"""Canonical Chrome/CDP browser-acceptance capture and replay.

This module owns the browser selectors, actions, measurements, screenshots, and
schema-4 receipt emission for the 155-topic release.  It deliberately uses only
the Python standard library plus a locally installed Chrome/Chromium binary.
"""

from __future__ import annotations

import base64
import hashlib
import json
import math
import os
import re
import shutil
import signal
import socket
import struct
import subprocess
import tempfile
import time
from collections.abc import Iterator, Mapping
from contextlib import contextmanager, suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from fep_lean.output.formalism_presentation import build_formalism_presentation
from fep_lean.output.fsutil import sha256_bytes, sha256_file

BROWSER_ASSET_ROOT = Path("specs/done/formalism-catalogue-155/assets")
BROWSER_RECEIPT = BROWSER_ASSET_ROOT / "browser-interaction-receipt.json"
CANONICAL_BROWSER_PROJECTIONS: Mapping[str, str] = {
    "atlas_html": "docs/formalism-atlas.html",
    "atlas_svg": "docs/formalism-atlas.svg",
    "dashboard_html": "docs/formal-kernel-dashboard.html",
    "dashboard_svg": "docs/formal-kernel-dashboard.svg",
}
CANONICAL_BROWSER_SCREENSHOTS: Mapping[str, str] = {
    "atlas_desktop": (BROWSER_ASSET_ROOT / "atlas-155-desktop.png").as_posix(),
    "atlas_mobile": (BROWSER_ASSET_ROOT / "atlas-155-mobile.png").as_posix(),
    "atlas_standalone": (BROWSER_ASSET_ROOT / "atlas-155-standalone.png").as_posix(),
    "dashboard_desktop": (BROWSER_ASSET_ROOT / "dashboard-155-desktop.png").as_posix(),
    "dashboard_mobile": (BROWSER_ASSET_ROOT / "dashboard-155-mobile.png").as_posix(),
    "dashboard_standalone": (
        BROWSER_ASSET_ROOT / "dashboard-155-standalone.png"
    ).as_posix(),
}
REQUIRED_BROWSER_INTERACTIONS = frozenset(
    {
        "accessible_tables",
        "keyboard_shortcuts",
        "no_external_requests",
        "overflow_free",
        "responsive_layout",
        "search_and_filter",
    }
)
CAPTURE_OWNER = "src/fep_lean/output/browser_capture.py"
CAPTURE_WRAPPER = "scripts/capture_browser_acceptance.py"
CAPTURE_COMMAND = "uv run python scripts/capture_browser_acceptance.py"

_CHROME_CANDIDATES: Mapping[str, tuple[str, ...]] = {
    "Google Chrome": ("google-chrome", "google-chrome-stable"),
    "Chromium": ("chromium", "chromium-browser"),
}
_VERSION_RE = re.compile(r"(\d+\.\d+\.\d+\.\d+)")
_SUPPORTED_BROWSER_VERSION_RE = re.compile(
    r"^(Google Chrome(?: for Testing)?|Chromium) (\d+\.\d+\.\d+\.\d+)$"
)
_CDP_BROWSER_PRODUCT_RE = re.compile(
    r"^(Chrome|HeadlessChrome|Chromium)/(\d+\.\d+\.\d+\.\d+)$"
)
_CDP_START_TIMEOUT_SECONDS = 15.0
_CDP_COMMAND_TIMEOUT_SECONDS = 120.0
_NETWORK_QUIET_SECONDS = 0.25


class BrowserCaptureError(RuntimeError):
    """Raised when canonical browser evidence cannot be captured faithfully."""


@dataclass(frozen=True)
class BrowserReplay:
    """Live Chrome observations and exact screenshot bytes."""

    browser: Mapping[str, str]
    render_configuration: Mapping[str, str]
    render_environment: Mapping[str, str]
    observations: Mapping[str, Any]
    interactions: Mapping[str, bool]
    screenshot_bytes: Mapping[str, bytes]


@dataclass(frozen=True)
class _CaptureSpec:
    role: str
    projection: str
    width: int
    height: int
    mobile: bool


_CAPTURE_SPECS = (
    _CaptureSpec("atlas_desktop", "atlas_html", 1440, 900, False),
    _CaptureSpec("atlas_mobile", "atlas_html", 390, 844, True),
    _CaptureSpec("atlas_standalone", "atlas_svg", 1600, 1000, False),
    _CaptureSpec("dashboard_desktop", "dashboard_html", 1440, 900, False),
    _CaptureSpec("dashboard_mobile", "dashboard_html", 390, 844, True),
    _CaptureSpec("dashboard_standalone", "dashboard_svg", 1600, 1000, False),
)


def canonical_browser_render_configuration() -> dict[str, str]:
    """Return the normalized Chrome settings that influence captured pixels."""
    return {
        "browser_locale": "en-US",
        "color_profile": "srgb",
        "device_scale_factor": "1",
        "font_render_hinting": "none",
        "gpu": "disabled",
        "process_locale": "C.UTF-8",
        "timezone": "UTC",
    }


_RENDER_ENVIRONMENT_KEYS = frozenset(
    {
        "browser_locale",
        "device_pixel_ratio",
        "platform",
        "timezone",
        "webgl_renderer",
        "webgl_vendor",
    }
)
_NETWORK_CAPABLE_API_RE = re.compile(
    r"(?:\bfetch\s*\(|\bXMLHttpRequest\s*\(|"
    r"\b(?:WebSocket|EventSource|importScripts)\s*\(|"
    r"\bnavigator\s*\.\s*sendBeacon\s*\()",
    re.IGNORECASE,
)


def _safe_descendant(project_root: Path, relative: Path | str, *, label: str) -> Path:
    """Return one lexical descendant after rejecting symlinks and escapes."""
    root = Path(project_root).resolve()
    relative_path = Path(relative)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise BrowserCaptureError(f"browser {label} path escapes the project root")
    candidate = root
    for index, part in enumerate(relative_path.parts):
        candidate /= part
        if candidate.is_symlink():
            raise BrowserCaptureError(f"browser {label} path traverses a symlink")
        if (
            index < len(relative_path.parts) - 1
            and candidate.exists()
            and not candidate.is_dir()
        ):
            raise BrowserCaptureError(f"browser {label} parent is not a directory")
    try:
        candidate.resolve(strict=False).relative_to(root)
    except (OSError, ValueError) as exc:
        raise BrowserCaptureError(
            f"browser {label} path escapes the project root"
        ) from exc
    return candidate


def _canonical_projection_path(project_root: Path, relative: str) -> Path:
    path = _safe_descendant(project_root, relative, label="projection")
    if not path.is_file():
        raise BrowserCaptureError(f"browser projection is missing: {relative}")
    return path


def _assert_offline_projection_source(path: Path) -> None:
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise BrowserCaptureError("browser projection source is unreadable") from exc
    if _NETWORK_CAPABLE_API_RE.search(source):
        raise BrowserCaptureError(
            "browser projection contains a network-capable browser API"
        )


def _validate_render_environment(environment: Mapping[str, str]) -> None:
    if set(environment) != set(_RENDER_ENVIRONMENT_KEYS) or not all(
        isinstance(value, str) and value for value in environment.values()
    ):
        raise BrowserCaptureError("live Chrome render environment is incomplete")
    if environment["browser_locale"] != "en-US":
        raise BrowserCaptureError("live Chrome browser locale is not canonical")
    if environment["timezone"] != "UTC":
        raise BrowserCaptureError("live Chrome timezone is not canonical")
    if environment["device_pixel_ratio"] != "1":
        raise BrowserCaptureError("live Chrome device pixel ratio is not canonical")


def _validate_browser_identity(browser: Mapping[str, str]) -> None:
    if set(browser) != {
        "name",
        "version",
        "executable_path",
        "executable_sha256",
    }:
        raise BrowserCaptureError("live Chrome browser identity is incomplete")
    if browser["name"] not in _CHROME_CANDIDATES:
        raise BrowserCaptureError("live Chrome browser name is invalid")
    if _VERSION_RE.fullmatch(browser["version"]) is None:
        raise BrowserCaptureError("live Chrome browser version is invalid")
    executable = Path(browser["executable_path"])
    if (
        not executable.is_absolute()
        or executable.is_symlink()
        or not executable.is_file()
        or executable.resolve() != executable
    ):
        raise BrowserCaptureError("live Chrome executable path is not replayable")
    try:
        digest = sha256_file(executable)
    except OSError as exc:
        raise BrowserCaptureError("live Chrome executable is unreadable") from exc
    if browser["executable_sha256"] != digest:
        raise BrowserCaptureError("live Chrome executable hash is stale")


def canonical_browser_observations(
    counts: Mapping[str, int],
) -> dict[str, Any]:
    """Return the exact browser observation contract for the release seal."""
    return {
        **counts,
        "external_requests": [],
        "atlas": {
            "areas": 5,
            "bodyFitsViewport": True,
            "detailSections": 4,
            "detailsInitiallyOpen": 0,
            "escapeCleared": True,
            "families": counts["families"],
            "fepVisible": 41,
            "pairingVisible": 105,
            "relationCards": counts["relations"],
            "relations": counts["relations"],
            "searchVisible": 1,
            "slashFocused": True,
            "topics": counts["topics"],
        },
        "atlas_mobile": {
            "areas": 5,
            "bodyFitsViewport": True,
            "desktopSummaryHidden": True,
            "detailSections": 4,
            "detailsInitiallyOpen": 0,
            "families": counts["families"],
            "mobileSummaryVisible": True,
            "relationCards": counts["relations"],
            "topics": counts["topics"],
        },
        "dashboard": {
            "acceptedVisible": counts["witnesses"],
            "accessibleTables": counts["witnesses"],
            "bodyFitsViewport": True,
            "detailJumps": counts["witnesses"],
            "detailRecords": counts["witnesses"],
            "detailsInitiallyOpen": 0,
            "escapeCleared": True,
            "exactScrollRegions": 3 * counts["witnesses"],
            "familyVisible": 1,
            "filterOpened": 1,
            "overviewHiddenByFilter": True,
            "searchVisible": 1,
            "slashFocused": True,
            "structuralAnalogues": 1,
            "theoremInstances": 15,
            "jumpFocused": True,
            "jumpOpened": True,
            "witnesses": counts["witnesses"],
        },
        "dashboard_mobile": {
            "bodyFitsViewport": True,
            "compactDefaultHeight": True,
            "desktopOverviewHidden": True,
            "detailJumps": counts["witnesses"],
            "detailRecords": counts["witnesses"],
            "detailsInitiallyOpen": 0,
            "exactScrollRegions": 3 * counts["witnesses"],
            "filterOpened": 1,
            "jumpFocused": True,
            "jumpOpened": True,
            "mobileOverviewInitiallyOpen": False,
            "mobileOverviewDisclosureVisible": True,
            "overviewHiddenByFilter": True,
            "plotSummaries": counts["witnesses"],
            "recordCollectionInitiallyOpen": False,
            "witnesses": counts["witnesses"],
        },
    }


def _project_counts(project_root: Path) -> dict[str, int]:
    presentation = build_formalism_presentation(Path(project_root))
    return {
        "topics": len(presentation.topics),
        "families": len(presentation.families),
        "witnesses": len(presentation.witnesses),
        "relations": len(presentation.relations),
        "capabilities": len(presentation.capabilities),
    }


def canonical_browser_capture_provenance(project_root: Path) -> dict[str, str]:
    """Bind a browser receipt to its sole capture owner and public command."""
    root = Path(project_root).resolve()
    owner_path = _safe_descendant(root, CAPTURE_OWNER, label="capture provenance")
    wrapper_path = _safe_descendant(root, CAPTURE_WRAPPER, label="capture provenance")
    try:
        if not owner_path.is_file() or not wrapper_path.is_file():
            raise OSError("capture provenance owner is not a regular file")
        owner = owner_path.read_bytes()
        wrapper = wrapper_path.read_bytes()
    except OSError as exc:
        raise BrowserCaptureError(
            "browser capture owner source is unavailable"
        ) from exc
    return {
        "command": CAPTURE_COMMAND,
        "owner": CAPTURE_OWNER,
        "owner_sha256": sha256_bytes(owner),
        "protocol": "Chrome DevTools Protocol",
        "wrapper": CAPTURE_WRAPPER,
        "wrapper_sha256": sha256_bytes(wrapper),
    }


def resolve_browser_executable(
    *, browser_name: str | None = None, executable: Path | None = None
) -> tuple[str, Path, str, str]:
    candidates: tuple[Path, ...]
    if executable is not None:
        resolved = Path(executable).expanduser().resolve()
        candidates = (resolved,)
    else:
        names = (
            (browser_name,) if browser_name is not None else tuple(_CHROME_CANDIDATES)
        )
        if any(name not in _CHROME_CANDIDATES for name in names):
            raise BrowserCaptureError("browser must identify Google Chrome or Chromium")
        candidates = tuple(
            Path(found).resolve()
            for name in names
            for command in _CHROME_CANDIDATES[name]
            if (found := shutil.which(command)) is not None
        )
    if not candidates:
        raise BrowserCaptureError(
            "cannot identify a local Chrome or Chromium executable"
        )
    resolved = candidates[0]
    if not resolved.is_file():
        raise BrowserCaptureError("browser executable is not a regular file")
    try:
        completed = subprocess.run(
            [str(resolved), "--version"],
            capture_output=True,
            check=False,
            text=True,
            timeout=10,
        )
        output_lines = tuple(
            line
            for raw_line in (completed.stdout, completed.stderr)
            if (line := raw_line.strip())
        )
        digest = sha256_file(resolved)
    except (OSError, subprocess.SubprocessError) as exc:
        raise BrowserCaptureError(
            "cannot identify the local browser executable"
        ) from exc
    if completed.returncode != 0 or len(output_lines) != 1:
        raise BrowserCaptureError("cannot identify the local browser executable")
    match = _SUPPORTED_BROWSER_VERSION_RE.fullmatch(output_lines[0])
    if match is None:
        raise BrowserCaptureError(
            "local browser executable is not a supported Chrome or Chromium product"
        )
    detected_name = (
        "Google Chrome" if match.group(1).startswith("Google Chrome") else "Chromium"
    )
    if browser_name is not None and detected_name != browser_name:
        raise BrowserCaptureError(
            "resolved browser name differs from requested identity"
        )
    return detected_name, resolved, match.group(2), digest


class _WebSocket:
    def __init__(self, connection: socket.socket, initial: bytes = b"") -> None:
        self._connection = connection
        self._buffer = bytearray(initial)

    @classmethod
    def connect(cls, host: str, port: int, path: str) -> _WebSocket:
        connection = socket.create_connection(
            (host, port), timeout=_CDP_COMMAND_TIMEOUT_SECONDS
        )
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        request = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {host}:{port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
        ).encode("ascii")
        try:
            connection.sendall(request)
        except OSError as exc:
            connection.close()
            raise BrowserCaptureError(
                f"CDP WebSocket request could not be sent: {exc}"
            ) from exc
        response = bytearray()
        while b"\r\n\r\n" not in response:
            chunk = connection.recv(4096)
            if not chunk:
                connection.close()
                raise BrowserCaptureError("Chrome closed the CDP WebSocket handshake")
            response.extend(chunk)
            if len(response) > 64 * 1024:
                connection.close()
                raise BrowserCaptureError("Chrome returned oversized CDP headers")
        headers, initial = bytes(response).split(b"\r\n\r\n", 1)
        if not headers.startswith(b"HTTP/1.1 101 "):
            connection.close()
            raise BrowserCaptureError("Chrome rejected the CDP WebSocket handshake")
        expected = base64.b64encode(
            hashlib.sha1(
                key.encode("ascii") + b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11",
                usedforsecurity=False,
            ).digest()
        )
        if b"sec-websocket-accept: " + expected.lower() not in headers.lower():
            connection.close()
            raise BrowserCaptureError(
                "Chrome returned an invalid CDP WebSocket accept key"
            )
        return cls(connection, initial)

    def close(self) -> None:
        with suppress(OSError):
            self._send_frame(0x8, b"")
        self._connection.close()

    def send_json(self, payload: Mapping[str, Any]) -> None:
        self._send_frame(
            0x1,
            json.dumps(payload, separators=(",", ":")).encode("utf-8"),
        )

    def receive_json(self) -> dict[str, Any]:
        fragments = bytearray()
        started = False
        while True:
            first, second = self._recv_exact(2)
            final = bool(first & 0x80)
            opcode = first & 0x0F
            masked = bool(second & 0x80)
            length = second & 0x7F
            if length == 126:
                length = struct.unpack(">H", self._recv_exact(2))[0]
            elif length == 127:
                length = struct.unpack(">Q", self._recv_exact(8))[0]
            mask = self._recv_exact(4) if masked else b""
            data = self._recv_exact(length)
            if masked:
                data = bytes(
                    value ^ mask[index % 4] for index, value in enumerate(data)
                )
            if opcode == 0x8:
                raise BrowserCaptureError("Chrome closed the CDP WebSocket")
            if opcode == 0x9:
                self._send_frame(0xA, data)
                continue
            if opcode == 0xA:
                continue
            if opcode == 0x1:
                fragments = bytearray(data)
                started = True
            elif opcode == 0x0 and started:
                fragments.extend(data)
            else:
                raise BrowserCaptureError("Chrome returned an unsupported CDP frame")
            if final:
                try:
                    decoded = json.loads(fragments.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise BrowserCaptureError(
                        "Chrome returned invalid CDP JSON"
                    ) from exc
                if not isinstance(decoded, dict):
                    raise BrowserCaptureError(
                        "Chrome returned a non-object CDP message"
                    )
                return decoded

    def _send_frame(self, opcode: int, data: bytes) -> None:
        first = 0x80 | opcode
        length = len(data)
        if length < 126:
            header = bytes((first, 0x80 | length))
        elif length < 2**16:
            header = bytes((first, 0x80 | 126)) + struct.pack(">H", length)
        else:
            header = bytes((first, 0x80 | 127)) + struct.pack(">Q", length)
        mask = os.urandom(4)
        masked = bytes(value ^ mask[index % 4] for index, value in enumerate(data))
        self._connection.sendall(header + mask + masked)

    def _recv_exact(self, size: int) -> bytes:
        while len(self._buffer) < size:
            chunk = self._connection.recv(max(4096, size - len(self._buffer)))
            if not chunk:
                raise BrowserCaptureError("Chrome closed the CDP connection")
            self._buffer.extend(chunk)
        result = bytes(self._buffer[:size])
        del self._buffer[:size]
        return result


class _CdpClient:
    def __init__(self, websocket: _WebSocket) -> None:
        self._websocket = websocket
        self._next_id = 1
        self._events: list[dict[str, Any]] = []

    def close(self) -> None:
        self._websocket.close()

    def clear_events(self) -> None:
        self._events.clear()

    def events(self, method: str, *, session_id: str) -> tuple[dict[str, Any], ...]:
        """Return already observed events for one attached target."""
        return tuple(
            message
            for message in self._events
            if message.get("method") == method
            and message.get("sessionId") == session_id
        )

    def call(
        self,
        method: str,
        params: Mapping[str, Any] | None = None,
        *,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        message_id = self._next_id
        self._next_id += 1
        payload: dict[str, Any] = {"id": message_id, "method": method}
        if params is not None:
            payload["params"] = dict(params)
        if session_id is not None:
            payload["sessionId"] = session_id
        self._websocket.send_json(payload)
        while True:
            message = self._websocket.receive_json()
            if message.get("id") == message_id:
                if "error" in message:
                    raise BrowserCaptureError(
                        f"Chrome CDP {method} failed: {message['error']}"
                    )
                result = message.get("result", {})
                if not isinstance(result, dict):
                    raise BrowserCaptureError(
                        f"Chrome CDP {method} returned an invalid result"
                    )
                return result
            self._events.append(message)

    def wait_event(self, method: str, *, session_id: str) -> dict[str, Any]:
        deadline = time.monotonic() + _CDP_COMMAND_TIMEOUT_SECONDS
        while True:
            for index, message in enumerate(self._events):
                if (
                    message.get("method") == method
                    and message.get("sessionId") == session_id
                ):
                    return self._events.pop(index)
            if time.monotonic() >= deadline:
                raise BrowserCaptureError(f"timed out waiting for Chrome CDP {method}")
            self._events.append(self._websocket.receive_json())


class _BrowserVersionClient(Protocol):
    def call(self, method: str) -> dict[str, Any]: ...


def _validate_cdp_browser_identity(
    client: _BrowserVersionClient,
    *,
    browser_name: str,
    version: str,
) -> None:
    """Corroborate the executable identity with the launched CDP product."""
    response = client.call("Browser.getVersion")
    product = response.get("product")
    match = (
        _CDP_BROWSER_PRODUCT_RE.fullmatch(product) if isinstance(product, str) else None
    )
    if match is None:
        raise BrowserCaptureError(
            "live CDP product is not a supported Chrome or Chromium product"
        )
    if match.group(2) != version:
        raise BrowserCaptureError(
            "live CDP product version differs from the resolved browser executable"
        )
    if browser_name == "Google Chrome" and match.group(1) == "Chromium":
        raise BrowserCaptureError(
            "live CDP product differs from the resolved Google Chrome executable"
        )


@contextmanager
def _chrome_client(executable: Path) -> Iterator[tuple[_CdpClient, str]]:
    profile = Path(tempfile.mkdtemp(prefix="fep-lean-chrome-"))
    process: subprocess.Popen[bytes] | None = None
    try:
        command = [
            str(executable),
            "--headless=new",
            "--remote-debugging-port=0",
            f"--user-data-dir={profile}",
            "--allow-file-access-from-files",
            "--disable-background-networking",
            "--disable-component-update",
            "--disable-default-apps",
            "--disable-dev-shm-usage",
            "--disable-extensions",
            "--disable-features=Translate,MediaRouter",
            "--disable-gpu",
            "--disable-sync",
            "--font-render-hinting=none",
            "--force-color-profile=srgb",
            "--force-device-scale-factor=1",
            "--hide-scrollbars",
            "--lang=en-US",
            "--metrics-recording-only",
            "--no-default-browser-check",
            "--no-first-run",
            "about:blank",
        ]
        try:
            process = subprocess.Popen(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
                env={
                    **os.environ,
                    "LANG": "C.UTF-8",
                    "LC_ALL": "C.UTF-8",
                    "TZ": "UTC",
                },
            )
        except OSError as exc:
            raise BrowserCaptureError("cannot launch the local browser") from exc
        client: _CdpClient | None = None
        try:
            active_port = Path(profile) / "DevToolsActivePort"
            deadline = time.monotonic() + _CDP_START_TIMEOUT_SECONDS
            while not active_port.is_file() and time.monotonic() < deadline:
                if process.poll() is not None:
                    raise BrowserCaptureError(
                        "Chrome exited before CDP became available"
                    )
                time.sleep(0.05)
            # Chrome creates DevToolsActivePort before writing its contents;
            # a read in that window returns "" and int("") raises. Re-read
            # until the first line parses as an int (bounded by the same
            # start deadline), so the create-then-write race cannot surface
            # as a failed capture.
            port: int | None = None
            websocket_path: str | None = None
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise BrowserCaptureError(
                        "Chrome exited before CDP became available"
                    )
                try:
                    first_two = active_port.read_text(encoding="utf-8").splitlines()[:2]
                    port = int(first_two[0])
                    websocket_path = first_two[1]
                    break
                except (OSError, ValueError, IndexError):
                    time.sleep(0.05)
            if port is None or websocket_path is None:
                raise BrowserCaptureError("Chrome did not publish a usable CDP port")
            websocket = _WebSocket.connect("127.0.0.1", port, websocket_path)
            client = _CdpClient(websocket)
            target = client.call("Target.createTarget", {"url": "about:blank"})
            target_id = target.get("targetId")
            if not isinstance(target_id, str):
                raise BrowserCaptureError("Chrome did not create a CDP target")
            attached = client.call(
                "Target.attachToTarget", {"targetId": target_id, "flatten": True}
            )
            session_id = attached.get("sessionId")
            if not isinstance(session_id, str):
                raise BrowserCaptureError("Chrome did not attach a CDP target")
            client.call("Page.enable", session_id=session_id)
            client.call("Runtime.enable", session_id=session_id)
            client.call("Network.enable", session_id=session_id)
            client.call(
                "Network.setBlockedURLs",
                {"urls": ["http://*", "https://*"]},
                session_id=session_id,
            )
            client.call(
                "Emulation.setLocaleOverride",
                {"locale": "en-US"},
                session_id=session_id,
            )
            client.call(
                "Emulation.setTimezoneOverride",
                {"timezoneId": "UTC"},
                session_id=session_id,
            )
            yield client, session_id
        finally:
            if client is not None:
                client.close()
    finally:
        if process is not None and process.poll() is None:
            with suppress(ProcessLookupError):
                os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                with suppress(ProcessLookupError):
                    os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=5)
        cleanup_error: OSError | None = None
        for _attempt in range(20):
            try:
                shutil.rmtree(profile)
                cleanup_error = None
                break
            except FileNotFoundError:
                cleanup_error = None
                break
            except OSError as exc:
                cleanup_error = exc
                time.sleep(0.05)
        if cleanup_error is not None:
            raise BrowserCaptureError(
                "cannot remove the terminated browser profile"
            ) from cleanup_error


def _evaluate(client: _CdpClient, session_id: str, expression: str) -> Any:
    response = client.call(
        "Runtime.evaluate",
        {
            "expression": expression,
            "awaitPromise": True,
            "returnByValue": True,
        },
        session_id=session_id,
    )
    if "exceptionDetails" in response:
        raise BrowserCaptureError("browser observation JavaScript raised an exception")
    remote = response.get("result")
    if not isinstance(remote, dict) or "value" not in remote:
        raise BrowserCaptureError("browser observation JavaScript returned no value")
    return remote["value"]


_RENDER_ENVIRONMENT_JS = r"""
(() => {
  const canvas=document.createElement("canvas");
  const gl=canvas.getContext("webgl") || canvas.getContext("experimental-webgl");
  return {
    browser_locale:String(navigator.language),
    device_pixel_ratio:String(window.devicePixelRatio),
    platform:String(navigator.platform),
    timezone:String(Intl.DateTimeFormat().resolvedOptions().timeZone),
    webgl_renderer:gl ? String(gl.getParameter(gl.RENDERER)) : "unavailable",
    webgl_vendor:gl ? String(gl.getParameter(gl.VENDOR)) : "unavailable",
  };
})()
"""


def _observe_render_environment(client: _CdpClient, session_id: str) -> dict[str, str]:
    value = _evaluate(client, session_id, _RENDER_ENVIRONMENT_JS)
    if not isinstance(value, dict) or not all(
        isinstance(key, str) and isinstance(item, str) for key, item in value.items()
    ):
        raise BrowserCaptureError("live Chrome render environment is invalid")
    environment = dict(value)
    _validate_render_environment(environment)
    return environment


def _set_viewport(
    client: _CdpClient, session_id: str, *, width: int, height: int, mobile: bool
) -> None:
    client.call(
        "Emulation.setDeviceMetricsOverride",
        {
            "width": width,
            "height": height,
            "deviceScaleFactor": 1,
            "mobile": mobile,
            "screenWidth": width,
            "screenHeight": height,
        },
        session_id=session_id,
    )
    client.call(
        "Emulation.setEmulatedMedia",
        {
            "media": "screen",
            "features": [{"name": "prefers-reduced-motion", "value": "reduce"}],
        },
        session_id=session_id,
    )


def _navigate(client: _CdpClient, session_id: str, path: Path) -> None:
    _assert_offline_projection_source(path)
    client.clear_events()
    result = client.call(
        "Page.navigate", {"url": path.resolve().as_uri()}, session_id=session_id
    )
    if result.get("errorText"):
        raise BrowserCaptureError(f"Chrome navigation failed: {result['errorText']}")
    client.wait_event("Page.loadEventFired", session_id=session_id)
    _evaluate(
        client,
        session_id,
        "document.fonts ? document.fonts.ready.then(() => true) : true",
    )
    time.sleep(_NETWORK_QUIET_SECONDS)
    _evaluate(client, session_id, "true")


def _press_key(client: _CdpClient, session_id: str, key: str) -> None:
    code, virtual_key, text = {
        "/": ("Slash", 191, "/"),
        "Escape": ("Escape", 27, ""),
    }[key]
    common: dict[str, Any] = {
        "key": key,
        "code": code,
        "windowsVirtualKeyCode": virtual_key,
        "nativeVirtualKeyCode": virtual_key,
    }
    client.call(
        "Input.dispatchKeyEvent",
        {"type": "keyDown", "text": text, **common},
        session_id=session_id,
    )
    client.call(
        "Input.dispatchKeyEvent",
        {"type": "keyUp", **common},
        session_id=session_id,
    )


def _network_external_requests(client: _CdpClient, session_id: str) -> tuple[str, ...]:
    urls: set[str] = set()
    for event in client.events("Network.requestWillBeSent", session_id=session_id):
        params = event.get("params")
        if not isinstance(params, dict):
            continue
        request = params.get("request")
        if not isinstance(request, dict):
            continue
        url = request.get("url")
        if isinstance(url, str) and re.match(r"^https?://", url, re.IGNORECASE):
            urls.add(url)
    return tuple(sorted(urls))


_EXTERNAL_REQUESTS_JS = r"""
(() => [...new Set([
  ...performance.getEntriesByType("resource").map(entry => entry.name),
  ...[...document.querySelectorAll("[src],[href]")].map(node => node.src || node.href),
].filter(url => /^https?:\/\//i.test(url)))].sort())()
"""

_ATLAS_INITIAL_JS = r"""
(() => {
  const details=[...document.querySelectorAll("main > details[id]")];
  return {
    areas:document.querySelectorAll(".desktop-summary [data-area-summary]").length,
    bodyFitsViewport:document.documentElement.scrollWidth <= window.innerWidth + 1,
    detailSections:details.length,
    detailsInitiallyOpen:details.filter(detail => detail.open).length,
    families:document.querySelectorAll(".desktop-summary [data-family-summary]").length,
    relationCards:document.querySelectorAll("[data-relation-row]").length,
    relations:document.querySelectorAll("[data-relation-row]").length,
    topics:document.querySelectorAll("[data-topic-row]").length,
  };
})()
"""

_ATLAS_ACTIONS_JS = r"""
(() => {
  const search=document.getElementById("atlas-search");
  const rows=[...document.querySelectorAll("[data-topic-row]")];
  search.value=rows[0].dataset.topicRow;
  search.dispatchEvent(new Event("input", {bubbles:true}));
  const searchVisible=rows.filter(row => !row.hidden).length;
  search.value="";
  const area=document.getElementById("area-filter");
  area.value="FEP";area.dispatchEvent(new Event("input", {bubbles:true}));
  const fepVisible=rows.filter(row => !row.hidden).length;
  area.value="";area.dispatchEvent(new Event("input", {bubbles:true}));
  const relation=document.getElementById("relation-filter");
  relation.value="formal_pairing";
  relation.dispatchEvent(new Event("input", {bubbles:true}));
  const pairingVisible=[...document.querySelectorAll("[data-relation-row]")]
    .filter(row => !row.hidden).length;
  return {searchVisible,fepVisible,pairingVisible};
})()
"""

_ATLAS_ESCAPE_JS = r"""
(() => {
  const search=document.getElementById("atlas-search");
  return search.value === "" &&
    [...document.querySelectorAll("#area-filter,#family-filter,#status-filter,#relation-filter")]
      .every(control => control.value === "") && document.activeElement === search;
})()
"""

_ATLAS_MOBILE_JS = r"""
(() => {
  const details=[...document.querySelectorAll("main > details[id]")];
  return {
    areas:document.querySelectorAll(".mobile-summary [data-mobile-area-summary]").length,
    bodyFitsViewport:document.documentElement.scrollWidth <= window.innerWidth + 1,
    desktopSummaryHidden:getComputedStyle(document.querySelector(".desktop-summary")).display === "none",
    detailSections:details.length,
    detailsInitiallyOpen:details.filter(detail => detail.open).length,
    families:document.querySelectorAll(".mobile-summary [data-mobile-family-summary]").length,
    mobileSummaryVisible:getComputedStyle(document.querySelector(".mobile-summary")).display !== "none",
    relationCards:document.querySelectorAll("[data-relation-row]").length,
    topics:document.querySelectorAll("[data-topic-row]").length,
  };
})()
"""

_DASHBOARD_INITIAL_JS = r"""
(() => {
  const records=[...document.querySelectorAll(".witness-detail")];
  return {
    acceptedVisible:records.filter(record => record.querySelector(".witness-workbench").dataset.status === "accepted").length,
    accessibleTables:records.filter(record =>
      record.querySelectorAll('.exact-scroll[role="region"][tabindex="0"] .exact-table').length === 3
    ).length,
    bodyFitsViewport:document.documentElement.scrollWidth <= window.innerWidth + 1,
    detailJumps:document.querySelectorAll("[data-detail-jump]").length,
    detailRecords:records.length,
    detailsInitiallyOpen:records.filter(record => record.open).length,
    exactScrollRegions:document.querySelectorAll(".exact-scroll").length,
    structuralAnalogues:records.filter(record => record.querySelector(".witness-workbench").dataset.formalAlignment === "structural_analogue").length,
    theoremInstances:records.filter(record => record.querySelector(".witness-workbench").dataset.formalAlignment === "theorem_instance").length,
    witnesses:records.length,
  };
})()
"""

_DASHBOARD_ACTIONS_JS = r"""
(() => {
  const records=[...document.querySelectorAll(".witness-detail")];
  const search=document.getElementById("witness-search");
  const family=document.getElementById("witness-family-filter");
  search.value=records[0].querySelector(".witness-workbench").dataset.witnessId;
  search.dispatchEvent(new Event("input", {bubbles:true}));
  const searchVisible=records.filter(record => !record.hidden).length;
  search.value="";search.dispatchEvent(new Event("input", {bubbles:true}));
  family.value=[...family.options].find(option => option.value).value;
  family.dispatchEvent(new Event("input", {bubbles:true}));
  const familyVisible=records.filter(record => !record.hidden).length;
  const filterOpened=records.filter(record => !record.hidden && record.open).length;
  const overviewHiddenByFilter=document.getElementById("witness-overview").hidden;
  return {searchVisible,familyVisible,filterOpened,overviewHiddenByFilter};
})()
"""

_DASHBOARD_ESCAPE_JS = r"""
(() => {
  const search=document.getElementById("witness-search");
  return search.value === "" &&
    document.getElementById("witness-family-filter").value === "" &&
    document.getElementById("witness-status-filter").value === "" &&
    document.activeElement === search;
})()
"""

_DASHBOARD_JUMP_JS = r"""
(() => {
  const link=document.querySelector("[data-detail-jump]");
  const id=link.dataset.detailJump;link.click();
  const target=[...document.querySelectorAll(".witness-detail")]
    .find(record => record.querySelector(".witness-workbench").dataset.witnessId === id);
  return {
    jumpFocused:document.activeElement === target.querySelector("summary"),
    jumpOpened:target.open && document.getElementById("witnesses").open,
  };
})()
"""

_DASHBOARD_MOBILE_JS = r"""
(() => {
  const records=[...document.querySelectorAll(".witness-detail")];
  const mobile=document.querySelector(".mobile-overview");
  const collection=document.getElementById("witnesses");
  return {
    bodyFitsViewport:document.documentElement.scrollWidth <= window.innerWidth + 1,
    compactDefaultHeight:document.documentElement.scrollHeight <= window.innerHeight * 2,
    desktopOverviewHidden:getComputedStyle(document.querySelector(".desktop-overview")).display === "none",
    detailJumps:document.querySelectorAll("[data-detail-jump]").length,
    detailRecords:records.length,
    detailsInitiallyOpen:records.filter(record => record.open).length,
    exactScrollRegions:document.querySelectorAll(".exact-scroll").length,
    mobileOverviewInitiallyOpen:
      document.querySelectorAll(".mobile-plot-group[open]").length > 0,
    mobileOverviewDisclosureVisible:getComputedStyle(mobile).display !== "none",
    plotSummaries:document.querySelectorAll("[data-mobile-witness-summary]").length,
    recordCollectionInitiallyOpen:collection.open,
    witnesses:records.length,
  };
})()
"""

_DASHBOARD_MOBILE_ACTIONS_JS = r"""
(() => {
  const records=[...document.querySelectorAll(".witness-detail")];
  const family=document.getElementById("witness-family-filter");
  family.value=[...family.options].find(option => option.value).value;
  family.dispatchEvent(new Event("input", {bubbles:true}));
  return {
    filterOpened:records.filter(record => !record.hidden && record.open).length,
    overviewHiddenByFilter:document.getElementById("witness-overview").hidden,
  };
})()
"""


def _atlas_observations(
    client: _CdpClient, session_id: str, *, mobile: bool
) -> dict[str, Any]:
    if mobile:
        value = _evaluate(client, session_id, _ATLAS_MOBILE_JS)
        if not isinstance(value, dict):
            raise BrowserCaptureError("atlas mobile observations are invalid")
        return value
    value = _evaluate(client, session_id, _ATLAS_INITIAL_JS)
    if not isinstance(value, dict):
        raise BrowserCaptureError("atlas observations are invalid")
    _press_key(client, session_id, "/")
    value["slashFocused"] = _evaluate(
        client,
        session_id,
        'document.activeElement?.id === "atlas-search"',
    )
    actions = _evaluate(client, session_id, _ATLAS_ACTIONS_JS)
    if not isinstance(actions, dict):
        raise BrowserCaptureError("atlas action observations are invalid")
    value.update(actions)
    _press_key(client, session_id, "Escape")
    value["escapeCleared"] = _evaluate(client, session_id, _ATLAS_ESCAPE_JS)
    return value


def _dashboard_observations(
    client: _CdpClient, session_id: str, *, mobile: bool
) -> dict[str, Any]:
    initial_expression = _DASHBOARD_MOBILE_JS if mobile else _DASHBOARD_INITIAL_JS
    value = _evaluate(client, session_id, initial_expression)
    if not isinstance(value, dict):
        raise BrowserCaptureError("dashboard observations are invalid")
    if mobile:
        actions = _evaluate(client, session_id, _DASHBOARD_MOBILE_ACTIONS_JS)
    else:
        _press_key(client, session_id, "/")
        value["slashFocused"] = _evaluate(
            client,
            session_id,
            'document.activeElement?.id === "witness-search"',
        )
        actions = _evaluate(client, session_id, _DASHBOARD_ACTIONS_JS)
    if not isinstance(actions, dict):
        raise BrowserCaptureError("dashboard action observations are invalid")
    value.update(actions)
    _press_key(client, session_id, "Escape")
    if not mobile:
        value["escapeCleared"] = _evaluate(client, session_id, _DASHBOARD_ESCAPE_JS)
    jump = _evaluate(client, session_id, _DASHBOARD_JUMP_JS)
    if not isinstance(jump, dict):
        raise BrowserCaptureError("dashboard jump observations are invalid")
    value.update(jump)
    return value


def _capture_screenshot(client: _CdpClient, session_id: str) -> bytes:
    _evaluate(client, session_id, "scrollTo(0, 0); true")
    metrics = client.call("Page.getLayoutMetrics", session_id=session_id)
    content = metrics.get("cssContentSize")
    if not isinstance(content, dict):
        raise BrowserCaptureError("Chrome returned no CSS content size")
    try:
        width = math.ceil(float(content["width"]))
        height = math.ceil(float(content["height"]))
    except (KeyError, TypeError, ValueError) as exc:
        raise BrowserCaptureError(
            "Chrome returned an invalid CSS content size"
        ) from exc
    if width <= 0 or height <= 0:
        raise BrowserCaptureError("Chrome returned an empty CSS content size")
    response = client.call(
        "Page.captureScreenshot",
        {
            "format": "png",
            "fromSurface": True,
            "captureBeyondViewport": True,
            "clip": {"x": 0, "y": 0, "width": width, "height": height, "scale": 1},
        },
        session_id=session_id,
    )
    encoded = response.get("data")
    if not isinstance(encoded, str):
        raise BrowserCaptureError("Chrome returned no screenshot bytes")
    try:
        return base64.b64decode(encoded, validate=True)
    except ValueError as exc:
        raise BrowserCaptureError("Chrome returned invalid screenshot bytes") from exc


def _interactions(observations: Mapping[str, Any]) -> dict[str, bool]:
    atlas = observations["atlas"]
    atlas_mobile = observations["atlas_mobile"]
    dashboard = observations["dashboard"]
    dashboard_mobile = observations["dashboard_mobile"]
    return {
        "accessible_tables": dashboard["accessibleTables"] == observations["witnesses"],
        "keyboard_shortcuts": all(
            (
                atlas["slashFocused"],
                atlas["escapeCleared"],
                dashboard["slashFocused"],
                dashboard["escapeCleared"],
            )
        ),
        "no_external_requests": observations["external_requests"] == [],
        "overflow_free": all(
            section["bodyFitsViewport"]
            for section in (atlas, atlas_mobile, dashboard, dashboard_mobile)
        ),
        "responsive_layout": all(
            (
                atlas_mobile["desktopSummaryHidden"],
                atlas_mobile["mobileSummaryVisible"],
                dashboard_mobile["desktopOverviewHidden"],
                dashboard_mobile["mobileOverviewDisclosureVisible"],
                not dashboard_mobile["mobileOverviewInitiallyOpen"],
                not dashboard_mobile["recordCollectionInitiallyOpen"],
            )
        ),
        "search_and_filter": all(
            (
                atlas["searchVisible"] == 1,
                atlas["fepVisible"] == 41,
                atlas["pairingVisible"] == 105,
                dashboard["searchVisible"] == 1,
                dashboard["familyVisible"] == 1,
                dashboard["filterOpened"] == 1,
                dashboard["overviewHiddenByFilter"],
                dashboard["jumpOpened"],
                dashboard["jumpFocused"],
                dashboard_mobile["filterOpened"] == 1,
                dashboard_mobile["overviewHiddenByFilter"],
                dashboard_mobile["jumpOpened"],
                dashboard_mobile["jumpFocused"],
            )
        ),
    }


def replay_browser_acceptance(
    project_root: Path,
    *,
    browser_name: str | None = None,
    executable: Path | None = None,
) -> BrowserReplay:
    """Replay the canonical interactions and capture exact screenshots in memory."""
    root = Path(project_root).resolve()
    projection_paths = {
        key: _canonical_projection_path(root, relative)
        for key, relative in CANONICAL_BROWSER_PROJECTIONS.items()
    }
    name, browser_path, version, executable_sha256 = resolve_browser_executable(
        browser_name=browser_name,
        executable=executable,
    )
    counts = _project_counts(root)
    observations: dict[str, Any] = dict(counts)
    screenshots: dict[str, bytes] = {}
    external_requests: set[str] = set()
    with _chrome_client(browser_path) as (client, session_id):
        _validate_cdp_browser_identity(
            client,
            browser_name=name,
            version=version,
        )
        render_environment = _observe_render_environment(client, session_id)
        for spec in _CAPTURE_SPECS:
            _set_viewport(
                client,
                session_id,
                width=spec.width,
                height=spec.height,
                mobile=spec.mobile,
            )
            path = projection_paths[spec.projection]
            _navigate(client, session_id, path)
            if spec.role == "atlas_desktop":
                observations["atlas"] = _atlas_observations(
                    client, session_id, mobile=False
                )
            elif spec.role == "atlas_mobile":
                observations["atlas_mobile"] = _atlas_observations(
                    client, session_id, mobile=True
                )
            elif spec.role == "dashboard_desktop":
                observations["dashboard"] = _dashboard_observations(
                    client, session_id, mobile=False
                )
            elif spec.role == "dashboard_mobile":
                observations["dashboard_mobile"] = _dashboard_observations(
                    client, session_id, mobile=True
                )
            urls = _evaluate(client, session_id, _EXTERNAL_REQUESTS_JS)
            if not isinstance(urls, list) or not all(
                isinstance(url, str) for url in urls
            ):
                raise BrowserCaptureError(
                    "browser external-request observations are invalid"
                )
            external_requests.update(urls)
            external_requests.update(_network_external_requests(client, session_id))
            _navigate(client, session_id, path)
            screenshots[spec.role] = _capture_screenshot(client, session_id)
            external_requests.update(_network_external_requests(client, session_id))
    observations["external_requests"] = sorted(external_requests)
    return BrowserReplay(
        browser={
            "name": name,
            "version": version,
            "executable_path": str(browser_path),
            "executable_sha256": executable_sha256,
        },
        render_configuration=canonical_browser_render_configuration(),
        render_environment=render_environment,
        observations=observations,
        interactions=_interactions(observations),
        screenshot_bytes=screenshots,
    )


def _png_dimensions(data: bytes) -> tuple[int, int]:
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise BrowserCaptureError("Chrome screenshot is not a PNG stream")
    return struct.unpack(">II", data[16:24])


def build_browser_receipt(project_root: Path, replay: BrowserReplay) -> bytes:
    """Serialize a replay only when every live observation meets the contract."""
    root = Path(project_root).resolve()
    counts = _project_counts(root)
    expected = canonical_browser_observations(counts)
    _validate_browser_identity(replay.browser)
    if replay.observations != expected:
        raise BrowserCaptureError("live Chrome DOM observations are not canonical")
    if set(replay.interactions) != set(REQUIRED_BROWSER_INTERACTIONS) or not all(
        replay.interactions.values()
    ):
        raise BrowserCaptureError("live Chrome interaction checks are not all accepted")
    if set(replay.screenshot_bytes) != set(CANONICAL_BROWSER_SCREENSHOTS):
        raise BrowserCaptureError("live Chrome screenshot roster is not canonical")
    render_configuration = canonical_browser_render_configuration()
    if replay.render_configuration != render_configuration:
        raise BrowserCaptureError("live Chrome render configuration is not canonical")
    _validate_render_environment(replay.render_environment)
    projections: dict[str, dict[str, str]] = {}
    for key, relative in CANONICAL_BROWSER_PROJECTIONS.items():
        path = _canonical_projection_path(root, relative)
        _assert_offline_projection_source(path)
        projections[key] = {"path": relative, "sha256": sha256_file(path)}
    screenshots = []
    for role, relative in sorted(
        CANONICAL_BROWSER_SCREENSHOTS.items(), key=lambda item: item[1]
    ):
        data = replay.screenshot_bytes[role]
        width, height = _png_dimensions(data)
        screenshots.append(
            {
                "role": role,
                "path": relative,
                "sha256": sha256_bytes(data),
                "width": width,
                "height": height,
            }
        )
    payload = {
        "schema_version": 4,
        "kind": "browser-interaction",
        "accepted": True,
        "browser": dict(replay.browser),
        "render_configuration": render_configuration,
        "render_environment": dict(replay.render_environment),
        "capture": canonical_browser_capture_provenance(root),
        "projections": projections,
        "screenshots": screenshots,
        "interactions": dict(replay.interactions),
        "observed": dict(replay.observations),
        "expected": expected,
    }
    return (
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def _install_capture_transaction(
    staged_files: list[tuple[Path, Path]], staging: Path
) -> None:
    """Install all capture files or restore every destination exactly."""
    records: list[tuple[Path, Path, Path, bool]] = []
    backup_root = staging / "backups"
    backup_root.mkdir()
    for index, (staged, destination) in enumerate(staged_files):
        if not staged.is_file() or staged.is_symlink():
            raise BrowserCaptureError("staged browser evidence is not a regular file")
        if destination.is_symlink() or (
            destination.exists() and not destination.is_file()
        ):
            raise BrowserCaptureError(
                f"browser evidence destination is not a regular file: {destination}"
            )
        records.append(
            (
                staged,
                destination,
                backup_root / f"{index:02d}-{destination.name}",
                destination.is_file(),
            )
        )
    try:
        for _staged, destination, backup, had_original in records:
            if had_original:
                os.replace(destination, backup)
        for staged, destination, _backup, _had_original in records:
            os.replace(staged, destination)
    except BaseException as install_error:
        rollback_errors: list[OSError] = []
        for _staged, destination, backup, had_original in reversed(records):
            try:
                if backup.is_file():
                    if destination.is_symlink() or destination.exists():
                        destination.unlink()
                    os.replace(backup, destination)
                elif not had_original and (
                    destination.is_symlink() or destination.exists()
                ):
                    destination.unlink()
            except OSError as exc:
                rollback_errors.append(exc)
        if rollback_errors:
            raise BrowserCaptureError(
                "browser evidence install failed and rollback was incomplete"
            ) from install_error
        raise


def capture_browser_acceptance(
    project_root: Path,
    *,
    browser_name: str | None = None,
    executable: Path | None = None,
) -> Path:
    """Capture, validate, and install the canonical screenshots and receipt."""
    root = Path(project_root).resolve()
    asset_root = _safe_descendant(root, BROWSER_ASSET_ROOT, label="asset")
    if asset_root.exists() and not asset_root.is_dir():
        raise BrowserCaptureError("browser asset root is not a real directory")
    replay = replay_browser_acceptance(
        root,
        browser_name=browser_name,
        executable=executable,
    )
    receipt = build_browser_receipt(root, replay)
    staging = Path(tempfile.mkdtemp(prefix=".browser-capture-", dir=root))
    preserve_stage = False
    try:
        staged_screenshots: list[tuple[Path, Path]] = []
        for role, relative in CANONICAL_BROWSER_SCREENSHOTS.items():
            staged = staging / Path(relative).name
            staged.write_bytes(replay.screenshot_bytes[role])
            staged_screenshots.append((staged, root / relative))
        staged_receipt = staging / BROWSER_RECEIPT.name
        staged_receipt.write_bytes(receipt)
        asset_root = _safe_descendant(root, BROWSER_ASSET_ROOT, label="asset")
        asset_root.parent.mkdir(parents=True, exist_ok=True)
        asset_root.mkdir(parents=True, exist_ok=True)
        _install_capture_transaction(
            [*staged_screenshots, (staged_receipt, root / BROWSER_RECEIPT)],
            staging,
        )
    except BaseException as exc:
        backup_root = staging / "backups"
        recovery_exists = backup_root.is_dir() and any(backup_root.iterdir())
        preserve_stage = recovery_exists
        if recovery_exists:
            detail = f"recovery files retained at {staging}"
            if isinstance(exc, BrowserCaptureError):
                raise BrowserCaptureError(f"{exc}; {detail}") from exc
            exc.add_note(detail)
        raise
    finally:
        if staging.exists() and not preserve_stage:
            shutil.rmtree(staging)
    return root / BROWSER_RECEIPT


__all__ = [
    "BROWSER_ASSET_ROOT",
    "BROWSER_RECEIPT",
    "CANONICAL_BROWSER_PROJECTIONS",
    "CANONICAL_BROWSER_SCREENSHOTS",
    "CAPTURE_COMMAND",
    "CAPTURE_OWNER",
    "CAPTURE_WRAPPER",
    "REQUIRED_BROWSER_INTERACTIONS",
    "BrowserCaptureError",
    "BrowserReplay",
    "build_browser_receipt",
    "canonical_browser_capture_provenance",
    "canonical_browser_observations",
    "canonical_browser_render_configuration",
    "capture_browser_acceptance",
    "replay_browser_acceptance",
    "resolve_browser_executable",
]
