"""Canonical Chrome/CDP browser acceptance owns its emitted evidence."""

from __future__ import annotations

import hashlib
import json
import os
import struct
import zlib
from dataclasses import replace
from pathlib import Path

import pytest

from fep_lean.output import browser_capture as capture_module


def _png_bytes(width: int, height: int, fill: int) -> bytes:
    def chunk(kind: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload))
            + kind
            + payload
            + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
        )

    rows = b"".join(b"\0" + bytes((fill,)) * width for _ in range(height))
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(rows, level=9))
        + chunk(b"IEND", b"")
    )


def test_canonical_render_configuration_names_every_normalized_pixel_input() -> None:
    assert capture_module.canonical_browser_render_configuration() == {
        "browser_locale": "en-US",
        "color_profile": "srgb",
        "device_scale_factor": "1",
        "font_render_hinting": "none",
        "gpu": "disabled",
        "process_locale": "C.UTF-8",
        "timezone": "UTC",
    }


def _stubbed_capture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> capture_module.BrowserReplay:
    source_root = Path(__file__).resolve().parents[1]
    for relative in (
        "src/fep_lean/output/browser_capture.py",
        "scripts/capture_browser_acceptance.py",
    ):
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((source_root / relative).read_bytes())
    counts = {
        "topics": 155,
        "families": 20,
        "witnesses": 15,
        "relations": 133,
        "capabilities": 48,
    }
    for key, relative in capture_module.CANONICAL_BROWSER_PROJECTIONS.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"{key}\n", encoding="utf-8")
    screenshots = {
        role: _png_bytes(
            390 if role.endswith("_mobile") else 1440,
            844 if role.endswith("_mobile") else 900,
            index + 1,
        )
        for index, role in enumerate(capture_module.CANONICAL_BROWSER_SCREENSHOTS)
    }
    browser_executable = tmp_path / "fixture-chrome"
    browser_executable.write_bytes(b"fixture Chrome binary\n")
    replay = capture_module.BrowserReplay(
        browser={
            "name": "Google Chrome",
            "version": "151.0.7922.169",
            "executable_path": str(browser_executable.resolve()),
            "executable_sha256": hashlib.sha256(
                browser_executable.read_bytes()
            ).hexdigest(),
        },
        render_configuration=capture_module.canonical_browser_render_configuration(),
        render_environment={
            "browser_locale": "en-US",
            "device_pixel_ratio": "1",
            "platform": "Linux x86_64",
            "timezone": "UTC",
            "webgl_renderer": "WebKit WebGL",
            "webgl_vendor": "WebKit",
        },
        observations=capture_module.canonical_browser_observations(counts),
        interactions={
            key: True for key in capture_module.REQUIRED_BROWSER_INTERACTIONS
        },
        screenshot_bytes=screenshots,
    )
    monkeypatch.setattr(capture_module, "_project_counts", lambda _root: counts)
    monkeypatch.setattr(
        capture_module,
        "replay_browser_acceptance",
        lambda *_args, **_kwargs: replay,
    )
    return replay


def test_capture_command_emits_source_bound_receipt_and_exact_screenshot_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    replay = _stubbed_capture(tmp_path, monkeypatch)

    receipt_path = capture_module.capture_browser_acceptance(tmp_path)
    payload = json.loads(receipt_path.read_text(encoding="utf-8"))

    owner = tmp_path / "src/fep_lean/output/browser_capture.py"
    wrapper = tmp_path / "scripts/capture_browser_acceptance.py"
    assert payload["capture"] == {
        "command": "uv run python scripts/capture_browser_acceptance.py",
        "owner": owner.relative_to(tmp_path).as_posix(),
        "owner_sha256": hashlib.sha256(owner.read_bytes()).hexdigest(),
        "protocol": "Chrome DevTools Protocol",
        "wrapper": wrapper.relative_to(tmp_path).as_posix(),
        "wrapper_sha256": hashlib.sha256(wrapper.read_bytes()).hexdigest(),
    }
    assert payload["schema_version"] == 4
    assert payload["browser"]["executable_path"] == str(
        (tmp_path / "fixture-chrome").resolve()
    )
    assert payload["render_configuration"] == (
        capture_module.canonical_browser_render_configuration()
    )
    assert payload["render_environment"] == replay.render_environment
    for role, relative in capture_module.CANONICAL_BROWSER_SCREENSHOTS.items():
        assert (tmp_path / relative).read_bytes() == replay.screenshot_bytes[role]


@pytest.mark.parametrize(
    "interruption",
    [
        OSError("injected browser install failure"),
        KeyboardInterrupt("injected browser install interruption"),
    ],
)
def test_capture_install_rolls_back_existing_and_absent_destinations(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    interruption: BaseException,
) -> None:
    _stubbed_capture(tmp_path, monkeypatch)
    destinations = [
        *(
            tmp_path / relative
            for relative in capture_module.CANONICAL_BROWSER_SCREENSHOTS.values()
        ),
        tmp_path / capture_module.BROWSER_RECEIPT,
    ]
    before: dict[Path, bytes | None] = {}
    for index, destination in enumerate(destinations):
        if index % 2 == 0:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(f"old-{index}".encode())
            before[destination] = destination.read_bytes()
        else:
            before[destination] = None
    real_replace = os.replace
    call_count = 0
    fail_at = sum(value is not None for value in before.values()) + 3

    def fail_once(source: Path, destination: Path) -> None:
        nonlocal call_count
        call_count += 1
        if call_count == fail_at:
            raise interruption
        real_replace(source, destination)

    monkeypatch.setattr(capture_module.os, "replace", fail_once)

    with pytest.raises(type(interruption), match="injected browser install"):
        capture_module.capture_browser_acceptance(tmp_path)

    for destination, expected in before.items():
        if expected is None:
            assert not destination.exists()
        else:
            assert destination.read_bytes() == expected


def test_capture_preserves_and_reports_backups_after_incomplete_rollback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stubbed_capture(tmp_path, monkeypatch)
    destinations = [
        *(
            tmp_path / relative
            for relative in capture_module.CANONICAL_BROWSER_SCREENSHOTS.values()
        ),
        tmp_path / capture_module.BROWSER_RECEIPT,
    ]
    for index, destination in enumerate(destinations):
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(f"old-{index}".encode())
    real_replace = capture_module.os.replace

    def fail_install_and_restore(source: Path, destination: Path) -> None:
        source_path = Path(source)
        if (
            source_path.name == "atlas-155-mobile.png"
            and source_path.parent.name.startswith(".browser-capture-")
        ):
            raise OSError("injected browser install failure")
        if source_path.parent.name == "backups" and source_path.name.startswith("01-"):
            raise OSError("injected browser restore failure")
        real_replace(source, destination)

    monkeypatch.setattr(os, "replace", fail_install_and_restore)

    with pytest.raises(
        capture_module.BrowserCaptureError,
        match="recovery files retained at",
    ) as captured:
        capture_module.capture_browser_acceptance(tmp_path)

    recovery = Path(str(captured.value).rsplit("recovery files retained at ", 1)[1])
    assert recovery.is_dir()
    assert (recovery / "backups" / "01-atlas-155-mobile.png").read_bytes() == b"old-1"


def test_replay_rejects_a_symlinked_projection_parent_before_browser_launch(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    project = tmp_path_factory.mktemp("browser-project")
    external_docs = tmp_path_factory.mktemp("external-docs")
    (external_docs / "formalism-atlas.html").write_text("external\n", encoding="utf-8")
    (project / "docs").symlink_to(external_docs, target_is_directory=True)

    with pytest.raises(
        capture_module.BrowserCaptureError,
        match="projection path traverses a symlink",
    ):
        capture_module.replay_browser_acceptance(project)


def test_replay_rejects_a_projection_path_that_lexically_escapes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        capture_module,
        "CANONICAL_BROWSER_PROJECTIONS",
        {"atlas_html": "../external/formalism-atlas.html"},
    )

    with pytest.raises(
        capture_module.BrowserCaptureError,
        match="projection path escapes the project root",
    ):
        capture_module.replay_browser_acceptance(tmp_path)


def test_capture_rejects_a_symlinked_specs_ancestor_without_external_writes(
    tmp_path_factory: pytest.TempPathFactory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = tmp_path_factory.mktemp("capture-project")
    external_specs = tmp_path_factory.mktemp("external-specs")
    _stubbed_capture(project, monkeypatch)
    (project / "specs").mkdir()
    (project / "specs/done").symlink_to(external_specs, target_is_directory=True)

    with pytest.raises(
        capture_module.BrowserCaptureError,
        match="asset path traverses a symlink",
    ):
        capture_module.capture_browser_acceptance(project)

    assert list(external_specs.iterdir()) == []


@pytest.mark.parametrize(
    "relative",
    (capture_module.CAPTURE_OWNER, capture_module.CAPTURE_WRAPPER),
)
def test_capture_rejects_symlinked_capture_provenance_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    relative: str,
) -> None:
    _stubbed_capture(tmp_path, monkeypatch)
    external = tmp_path / "external-capture-owner.py"
    external.write_text("external owner\n", encoding="utf-8")
    path = tmp_path / relative
    path.unlink()
    path.symlink_to(external)

    with pytest.raises(
        capture_module.BrowserCaptureError,
        match="capture provenance path traverses a symlink",
    ):
        capture_module.capture_browser_acceptance(tmp_path)


def test_receipt_rejects_a_long_delay_network_api_even_with_a_stubbed_replay(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _stubbed_capture(tmp_path, monkeypatch)
    (tmp_path / "docs/formalism-atlas.html").write_text(
        "<script>setTimeout(() => fetch('https://example.invalid'), 60000)</script>",
        encoding="utf-8",
    )

    with pytest.raises(
        capture_module.BrowserCaptureError,
        match="network-capable browser API",
    ):
        capture_module.capture_browser_acceptance(tmp_path)


def test_receipt_rejects_a_noncanonical_declared_render_configuration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    replay = _stubbed_capture(tmp_path, monkeypatch)
    tampered = replace(
        replay,
        render_configuration={**replay.render_configuration, "gpu": "enabled"},
    )

    with pytest.raises(
        capture_module.BrowserCaptureError,
        match="render configuration is not canonical",
    ):
        capture_module.build_browser_receipt(tmp_path, tampered)


def test_receipt_rejects_an_incomplete_observed_render_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    replay = _stubbed_capture(tmp_path, monkeypatch)
    tampered = replace(
        replay,
        render_environment={
            key: value
            for key, value in replay.render_environment.items()
            if key != "platform"
        },
    )

    with pytest.raises(
        capture_module.BrowserCaptureError,
        match="render environment is incomplete",
    ):
        capture_module.build_browser_receipt(tmp_path, tampered)


@pytest.mark.parametrize(
    "version_output",
    ("Brave Browser 123.4.5.6", "Chromium 123.4.5.6 Brave"),
)
def test_browser_resolution_rejects_an_unsupported_product(
    tmp_path: Path, version_output: str
) -> None:
    executable = tmp_path / "brave-like"
    executable.write_text(
        f'#!/bin/sh\nprintf "{version_output}\\n"\n',
        encoding="utf-8",
    )
    executable.chmod(0o755)

    with pytest.raises(
        capture_module.BrowserCaptureError,
        match="supported Chrome or Chromium product",
    ):
        capture_module.resolve_browser_executable(executable=executable)


def test_cdp_product_must_corroborate_the_resolved_browser_version() -> None:
    class FakeClient:
        def call(self, method: str) -> dict[str, str]:
            assert method == "Browser.getVersion"
            return {"product": "Chrome/124.0.0.1"}

    with pytest.raises(
        capture_module.BrowserCaptureError,
        match="CDP product version differs",
    ):
        capture_module._validate_cdp_browser_identity(
            FakeClient(),
            browser_name="Google Chrome",
            version="123.0.0.1",
        )


def _resolvable_browser() -> bool:
    """True when the capture module resolves a supported browser itself."""
    try:
        capture_module.resolve_browser_executable()
    except capture_module.BrowserCaptureError:
        return False
    return True


_BROWSER_RESOLVABLE = _resolvable_browser()


@pytest.mark.skipif(
    not _BROWSER_RESOLVABLE,
    reason=(
        "capture_module.resolve_browser_executable() cannot resolve a "
        "supported Chrome/Chromium executable on this host"
    ),
)
def test_live_chrome_blocks_and_records_a_delayed_outbound_request(
    tmp_path: Path,
) -> None:
    page = tmp_path / "delayed-network.html"
    page.write_text(
        "<script>setTimeout(() => fetch("
        "'https://example.invalid/delayed-resource'), 1000)</script>",
        encoding="utf-8",
    )
    executable = capture_module.resolve_browser_executable()[1]

    with (
        capture_module._chrome_client(executable) as (client, session_id),
        pytest.raises(
            capture_module.BrowserCaptureError,
            match="network-capable browser API",
        ),
    ):
        capture_module._navigate(client, session_id, page)


@pytest.mark.skipif(
    not _BROWSER_RESOLVABLE,
    reason=(
        "capture_module.resolve_browser_executable() cannot resolve a "
        "supported Chrome/Chromium executable on this host"
    ),
)
def test_live_chrome_replay_terminates_every_profile_writer() -> None:
    project_root = Path(__file__).resolve().parents[1]

    first = capture_module.replay_browser_acceptance(project_root)
    second = capture_module.replay_browser_acceptance(project_root)

    browser_path = Path(first.browser["executable_path"])
    assert browser_path.is_absolute()
    assert browser_path.is_file()
    assert (
        hashlib.sha256(browser_path.read_bytes()).hexdigest()
        == first.browser["executable_sha256"]
    )
    assert first.render_configuration == (
        capture_module.canonical_browser_render_configuration()
    )
    assert first.render_environment == second.render_environment
    assert first.render_environment["browser_locale"] == "en-US"
    assert first.render_environment["timezone"] == "UTC"
    assert first.render_environment["device_pixel_ratio"] == "1"
    assert first.render_environment["platform"]
    assert first.render_environment["webgl_renderer"]
    assert first.render_environment["webgl_vendor"]
    assert first.observations == second.observations
    assert (
        first.observations["dashboard_mobile"]["mobileOverviewInitiallyOpen"] is False
    )
    assert (
        first.observations["dashboard_mobile"]["mobileOverviewDisclosureVisible"]
        is True
    )
    assert first.screenshot_bytes == second.screenshot_bytes
