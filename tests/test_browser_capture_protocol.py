"""Fail-closed tests for Chrome/CDP protocol and evidence boundaries."""

from __future__ import annotations

import base64
import hashlib
import json
import struct
import subprocess
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

import pytest

from fep_formal.output import browser_capture as capture


class _ScriptedSocket:
    def __init__(
        self,
        chunks: Iterable[bytes] = (),
        *,
        fail_send: bool = False,
    ) -> None:
        self.chunks = list(chunks)
        self.fail_send = fail_send
        self.sent: list[bytes] = []
        self.closed = False

    def recv(self, size: int) -> bytes:
        if not self.chunks:
            return b""
        chunk = self.chunks.pop(0)
        if len(chunk) > size:
            self.chunks.insert(0, chunk[size:])
            return chunk[:size]
        return chunk

    def sendall(self, data: bytes) -> None:
        if self.fail_send:
            raise OSError("injected send failure")
        self.sent.append(data)

    def close(self) -> None:
        self.closed = True


def _server_frame(
    opcode: int,
    payload: bytes,
    *,
    final: bool = True,
    masked: bool = False,
) -> bytes:
    first = (0x80 if final else 0) | opcode
    length = len(payload)
    if length < 126:
        header = bytes((first, (0x80 if masked else 0) | length))
    elif length < 2**16:
        header = bytes((first, (0x80 if masked else 0) | 126)) + struct.pack(
            ">H", length
        )
    else:
        header = bytes((first, (0x80 if masked else 0) | 127)) + struct.pack(
            ">Q", length
        )
    if not masked:
        return header + payload
    mask = b"mask"
    encoded = bytes(value ^ mask[index % 4] for index, value in enumerate(payload))
    return header + mask + encoded


def _canonical_environment() -> dict[str, str]:
    return {
        "browser_locale": "en-US",
        "device_pixel_ratio": "1",
        "platform": "Linux x86_64",
        "timezone": "UTC",
        "webgl_renderer": "WebKit WebGL",
        "webgl_vendor": "WebKit",
    }


def test_websocket_reassembles_masked_fragments_around_control_frames() -> None:
    wire = b"".join(
        (
            _server_frame(0x9, b"probe"),
            _server_frame(0xA, b"ignored"),
            _server_frame(0x1, b'{"accepted":', final=False, masked=True),
            _server_frame(0x0, b"true}"),
        )
    )
    connection = _ScriptedSocket((wire[:3], wire[3:11], wire[11:]))
    websocket = capture._WebSocket(connection)

    assert websocket.receive_json() == {"accepted": True}
    assert connection.sent and connection.sent[0][0] == 0x8A


@pytest.mark.parametrize(
    ("wire", "message"),
    (
        (_server_frame(0x8, b""), "closed the CDP WebSocket"),
        (_server_frame(0x2, b"binary"), "unsupported CDP frame"),
        (_server_frame(0x1, b"not-json"), "invalid CDP JSON"),
        (_server_frame(0x1, json.dumps([1, 2]).encode()), "non-object CDP message"),
    ),
)
def test_websocket_rejects_non_json_protocol_messages(
    wire: bytes,
    message: str,
) -> None:
    websocket = capture._WebSocket(_ScriptedSocket((wire,)))

    with pytest.raises(capture.BrowserCaptureError, match=message):
        websocket.receive_json()


def test_websocket_send_encodes_all_length_classes_and_close_survives_io_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(capture.os, "urandom", lambda size: b"\0" * size)
    connection = _ScriptedSocket()
    websocket = capture._WebSocket(connection)

    websocket._send_frame(0x1, b"x")
    websocket._send_frame(0x1, b"x" * 126)
    websocket._send_frame(0x1, b"x" * (2**16))

    assert connection.sent[0][:2] == b"\x81\x81"
    assert connection.sent[1][:4] == b"\x81\xfe\x00\x7e"
    assert connection.sent[2][:10] == b"\x81\xff" + struct.pack(">Q", 2**16)

    failing = _ScriptedSocket(fail_send=True)
    capture._WebSocket(failing).close()
    assert failing.closed is True


def test_websocket_reports_connection_loss_while_reading_a_frame() -> None:
    websocket = capture._WebSocket(_ScriptedSocket())

    with pytest.raises(capture.BrowserCaptureError, match="closed the CDP connection"):
        websocket.receive_json()


@pytest.mark.parametrize(
    ("response", "message"),
    (
        (b"", "closed the CDP WebSocket handshake"),
        (b"x" * (64 * 1024 + 1), "oversized CDP headers"),
        (b"HTTP/1.1 403 Forbidden\r\n\r\n", "rejected the CDP WebSocket"),
        (
            b"HTTP/1.1 101 Switching Protocols\r\n"
            + b"Sec-WebSocket-Accept: invalid\r\n\r\n",
            "invalid CDP WebSocket accept key",
        ),
    ),
)
def test_websocket_handshake_failures_close_the_connection(
    monkeypatch: pytest.MonkeyPatch,
    response: bytes,
    message: str,
) -> None:
    connection = _ScriptedSocket((response,) if response else ())
    monkeypatch.setattr(
        capture.socket, "create_connection", lambda *_a, **_k: connection
    )
    monkeypatch.setattr(capture.os, "urandom", lambda size: b"a" * size)

    with pytest.raises(capture.BrowserCaptureError, match=message):
        capture._WebSocket.connect("127.0.0.1", 9222, "/devtools/browser/test")

    assert connection.closed is True


class _JsonWebSocket:
    def __init__(self, messages: Iterable[Mapping[str, Any]]) -> None:
        self.messages = [dict(message) for message in messages]
        self.sent: list[dict[str, Any]] = []
        self.closed = False

    def send_json(self, payload: Mapping[str, Any]) -> None:
        self.sent.append(dict(payload))

    def receive_json(self) -> dict[str, Any]:
        return self.messages.pop(0)

    def close(self) -> None:
        self.closed = True


def test_cdp_client_preserves_events_while_returning_the_matching_result() -> None:
    websocket = _JsonWebSocket(
        (
            {"method": "Page.loadEventFired", "sessionId": "session-1"},
            {"id": 1, "result": {"targetId": "target-1"}},
        )
    )
    client = capture._CdpClient(websocket)

    assert client.call(
        "Target.createTarget", {"url": "about:blank"}, session_id="session-1"
    ) == {"targetId": "target-1"}
    assert websocket.sent == [
        {
            "id": 1,
            "method": "Target.createTarget",
            "params": {"url": "about:blank"},
            "sessionId": "session-1",
        }
    ]
    assert client.events("Page.loadEventFired", session_id="session-1") == (
        {"method": "Page.loadEventFired", "sessionId": "session-1"},
    )
    client.clear_events()
    assert client.events("Page.loadEventFired", session_id="session-1") == ()
    client.close()
    assert websocket.closed is True


@pytest.mark.parametrize(
    ("message", "expected"),
    (
        ({"id": 1, "error": {"message": "denied"}}, "CDP Runtime.evaluate failed"),
        ({"id": 1, "result": []}, "returned an invalid result"),
    ),
)
def test_cdp_client_rejects_error_and_non_object_results(
    message: Mapping[str, Any],
    expected: str,
) -> None:
    client = capture._CdpClient(_JsonWebSocket((message,)))

    with pytest.raises(capture.BrowserCaptureError, match=expected):
        client.call("Runtime.evaluate")


def test_cdp_event_wait_times_out_without_consuming_external_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ticks = iter((10.0, 131.0))
    monkeypatch.setattr(capture.time, "monotonic", lambda: next(ticks))
    client = capture._CdpClient(_JsonWebSocket(()))

    with pytest.raises(capture.BrowserCaptureError, match="timed out waiting"):
        client.wait_event("Page.loadEventFired", session_id="session-1")


@pytest.mark.parametrize(
    ("product", "browser_name", "message"),
    (
        ("Firefox/151.0", "Google Chrome", "not a supported Chrome"),
        (
            "Chromium/151.0.7922.169",
            "Google Chrome",
            "differs from the resolved Google Chrome",
        ),
    ),
)
def test_cdp_identity_must_match_the_resolved_product_family(
    product: str,
    browser_name: str,
    message: str,
) -> None:
    class Client:
        def call(self, method: str) -> dict[str, str]:
            assert method == "Browser.getVersion"
            return {"product": product}

    with pytest.raises(capture.BrowserCaptureError, match=message):
        capture._validate_cdp_browser_identity(
            Client(),
            browser_name=browser_name,
            version="151.0.7922.169",
        )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        ("browser_locale", "fr-FR", "locale is not canonical"),
        ("timezone", "America/Los_Angeles", "timezone is not canonical"),
        ("device_pixel_ratio", "2", "pixel ratio is not canonical"),
    ),
)
def test_render_environment_rejects_noncanonical_live_values(
    field: str,
    value: str,
    message: str,
) -> None:
    environment = _canonical_environment()
    environment[field] = value

    with pytest.raises(capture.BrowserCaptureError, match=message):
        capture._validate_render_environment(environment)


@pytest.mark.parametrize(
    ("identity", "message"),
    (
        ({}, "identity is incomplete"),
        (
            {
                "name": "Brave",
                "version": "151.0.7922.169",
                "executable_path": "/missing",
                "executable_sha256": "0" * 64,
            },
            "browser name is invalid",
        ),
        (
            {
                "name": "Chromium",
                "version": "151",
                "executable_path": "/missing",
                "executable_sha256": "0" * 64,
            },
            "browser version is invalid",
        ),
        (
            {
                "name": "Chromium",
                "version": "151.0.7922.169",
                "executable_path": "relative-browser",
                "executable_sha256": "0" * 64,
            },
            "path is not replayable",
        ),
    ),
)
def test_browser_identity_rejects_incomplete_or_unreplayable_records(
    identity: Mapping[str, str],
    message: str,
) -> None:
    with pytest.raises(capture.BrowserCaptureError, match=message):
        capture._validate_browser_identity(identity)


def test_browser_identity_rejects_stale_executable_digest(tmp_path: Path) -> None:
    executable = tmp_path / "chromium"
    executable.write_bytes(b"browser bytes")

    with pytest.raises(capture.BrowserCaptureError, match="hash is stale"):
        capture._validate_browser_identity(
            {
                "name": "Chromium",
                "version": "151.0.7922.169",
                "executable_path": str(executable.resolve()),
                "executable_sha256": hashlib.sha256(b"other bytes").hexdigest(),
            }
        )


def test_projection_boundaries_reject_file_parents_and_unreadable_sources(
    tmp_path: Path,
) -> None:
    (tmp_path / "docs").write_text("not a directory", encoding="utf-8")
    with pytest.raises(capture.BrowserCaptureError, match="parent is not a directory"):
        capture._safe_descendant(tmp_path, "docs/atlas.html", label="projection")

    with pytest.raises(capture.BrowserCaptureError, match="source is unreadable"):
        capture._assert_offline_projection_source(tmp_path)


def test_projection_and_provenance_require_regular_files(tmp_path: Path) -> None:
    with pytest.raises(capture.BrowserCaptureError, match="projection is missing"):
        capture._canonical_projection_path(tmp_path, "docs/missing.html")

    with pytest.raises(
        capture.BrowserCaptureError, match="owner source is unavailable"
    ):
        capture.canonical_browser_capture_provenance(tmp_path)


def test_browser_resolution_rejects_missing_and_mismatched_executables(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(capture.shutil, "which", lambda _name: None)
    with pytest.raises(capture.BrowserCaptureError, match="identify a local Chrome"):
        capture.resolve_browser_executable()
    with pytest.raises(capture.BrowserCaptureError, match="must identify"):
        capture.resolve_browser_executable(browser_name="Brave")

    directory = tmp_path / "not-an-executable"
    directory.mkdir()
    with pytest.raises(capture.BrowserCaptureError, match="not a regular file"):
        capture.resolve_browser_executable(executable=directory)


def test_browser_resolution_wraps_process_errors_and_rejects_identity_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    executable = tmp_path / "chromium"
    executable.write_bytes(b"browser bytes")

    def fail_run(*_args: Any, **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        raise OSError("cannot execute")

    monkeypatch.setattr(capture.subprocess, "run", fail_run)
    with pytest.raises(capture.BrowserCaptureError, match="cannot identify"):
        capture.resolve_browser_executable(executable=executable)

    monkeypatch.setattr(
        capture.subprocess,
        "run",
        lambda *_a, **_k: subprocess.CompletedProcess(
            args=[], returncode=0, stdout="Chromium 151.0.7922.169\n", stderr=""
        ),
    )
    with pytest.raises(capture.BrowserCaptureError, match="differs from requested"):
        capture.resolve_browser_executable(
            browser_name="Google Chrome", executable=executable
        )


def test_browser_resolution_rejects_ambiguous_version_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    executable = tmp_path / "chromium"
    executable.write_bytes(b"browser bytes")
    monkeypatch.setattr(
        capture.subprocess,
        "run",
        lambda *_a, **_k: subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="Chromium 151.0.7922.169\n",
            stderr="Chromium 151.0.7922.169\n",
        ),
    )

    with pytest.raises(capture.BrowserCaptureError, match="cannot identify"):
        capture.resolve_browser_executable(executable=executable)


class _ResultClient:
    def __init__(self, responses: Mapping[str, Mapping[str, Any]]) -> None:
        self.responses = responses
        self.cleared = False

    def call(
        self,
        method: str,
        _params: Mapping[str, Any] | None = None,
        *,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        del session_id
        return dict(self.responses.get(method, {}))

    def clear_events(self) -> None:
        self.cleared = True

    def wait_event(self, _method: str, *, session_id: str) -> dict[str, Any]:
        return {"sessionId": session_id}


@pytest.mark.parametrize(
    ("response", "message"),
    (
        ({"exceptionDetails": {}}, "raised an exception"),
        ({"result": {}}, "returned no value"),
    ),
)
def test_browser_evaluation_requires_a_value_without_exceptions(
    response: Mapping[str, Any],
    message: str,
) -> None:
    client = _ResultClient({"Runtime.evaluate": response})

    with pytest.raises(capture.BrowserCaptureError, match=message):
        capture._evaluate(client, "session-1", "true")


def test_navigation_rejects_cdp_error_before_waiting_for_load(tmp_path: Path) -> None:
    page = tmp_path / "page.html"
    page.write_text("<p>offline</p>", encoding="utf-8")
    client = _ResultClient({"Page.navigate": {"errorText": "blocked"}})

    with pytest.raises(capture.BrowserCaptureError, match="navigation failed: blocked"):
        capture._navigate(client, "session-1", page)
    assert client.cleared is True


@pytest.mark.parametrize(
    ("metrics", "screenshot", "message"),
    (
        ({}, {}, "no CSS content size"),
        ({"cssContentSize": {"width": "bad", "height": 10}}, {}, "invalid CSS"),
        ({"cssContentSize": {"width": 0, "height": 10}}, {}, "empty CSS"),
        (
            {"cssContentSize": {"width": 10, "height": 10}},
            {},
            "no screenshot bytes",
        ),
        (
            {"cssContentSize": {"width": 10, "height": 10}},
            {"data": "not-base64!"},
            "invalid screenshot bytes",
        ),
    ),
)
def test_screenshot_capture_rejects_malformed_cdp_payloads(
    monkeypatch: pytest.MonkeyPatch,
    metrics: Mapping[str, Any],
    screenshot: Mapping[str, Any],
    message: str,
) -> None:
    monkeypatch.setattr(capture, "_evaluate", lambda *_a, **_k: True)
    client = _ResultClient(
        {"Page.getLayoutMetrics": metrics, "Page.captureScreenshot": screenshot}
    )

    with pytest.raises(capture.BrowserCaptureError, match=message):
        capture._capture_screenshot(client, "session-1")


def test_screenshot_png_parser_rejects_non_png_streams() -> None:
    with pytest.raises(capture.BrowserCaptureError, match="not a PNG stream"):
        capture._png_dimensions(base64.b64decode("aW52YWxpZA=="))


@pytest.mark.parametrize(
    ("mobile", "values", "message"),
    (
        (True, ([],), "atlas mobile observations are invalid"),
        (False, ([],), "atlas observations are invalid"),
        (False, ({}, True, True, []), "atlas action observations are invalid"),
    ),
)
def test_atlas_observations_reject_non_object_javascript_results(
    monkeypatch: pytest.MonkeyPatch,
    mobile: bool,
    values: tuple[Any, ...],
    message: str,
) -> None:
    results = iter(values)
    monkeypatch.setattr(capture, "_evaluate", lambda *_a, **_k: next(results))
    monkeypatch.setattr(capture, "_press_key", lambda *_a, **_k: None)

    with pytest.raises(capture.BrowserCaptureError, match=message):
        capture._atlas_observations(object(), "session-1", mobile=mobile)


@pytest.mark.parametrize(
    ("mobile", "values", "message"),
    (
        (False, ([],), "dashboard observations are invalid"),
        (True, ({}, []), "dashboard action observations are invalid"),
        (True, ({}, {}, []), "dashboard jump observations are invalid"),
    ),
)
def test_dashboard_observations_reject_non_object_javascript_results(
    monkeypatch: pytest.MonkeyPatch,
    mobile: bool,
    values: tuple[Any, ...],
    message: str,
) -> None:
    results = iter(values)
    monkeypatch.setattr(capture, "_evaluate", lambda *_a, **_k: next(results))
    monkeypatch.setattr(capture, "_press_key", lambda *_a, **_k: None)
    # This test isolates the action/jump result shape; reset policy has direct controls.
    monkeypatch.setattr(
        capture, "_explorer_keyboard_reset_observations", lambda *_a, **_k: {}
    )

    with pytest.raises(capture.BrowserCaptureError, match=message):
        capture._dashboard_observations(object(), "session-1", mobile=mobile)


def test_capture_rejects_non_directory_asset_root_before_replay(
    tmp_path: Path,
) -> None:
    asset_root = tmp_path / capture.BROWSER_ASSET_ROOT
    asset_root.parent.mkdir(parents=True)
    asset_root.write_text("not a directory", encoding="utf-8")

    with pytest.raises(capture.BrowserCaptureError, match="not a real directory"):
        capture.capture_browser_acceptance(tmp_path)


@pytest.mark.parametrize("staged_kind", ("directory", "symlink"))
def test_capture_install_rejects_non_regular_staged_evidence(
    tmp_path: Path,
    staged_kind: str,
) -> None:
    staging = tmp_path / "stage"
    staging.mkdir()
    staged = staging / "evidence.png"
    if staged_kind == "directory":
        staged.mkdir()
    else:
        target = tmp_path / "target.png"
        target.write_bytes(b"png")
        staged.symlink_to(target)

    with pytest.raises(capture.BrowserCaptureError, match="not a regular file"):
        capture._install_capture_transaction(
            [(staged, tmp_path / "destination.png")], staging
        )


def test_capture_install_rejects_non_regular_destination(tmp_path: Path) -> None:
    staging = tmp_path / "stage"
    staging.mkdir()
    staged = staging / "evidence.png"
    staged.write_bytes(b"png")
    destination = tmp_path / "destination.png"
    destination.mkdir()

    with pytest.raises(capture.BrowserCaptureError, match="destination is not"):
        capture._install_capture_transaction([(staged, destination)], staging)
