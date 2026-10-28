"""Browser release/publication boundary contracts."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from fep_formal.output import release_bundle as bundle_module
from tests._support.release_bundle import (
    _png_bytes,
)

PROJ = Path(__file__).resolve().parents[1]


def _assert_stale_pairing_count_rejected(
    project_root: Path,
    receipt_path: Path,
    receipt: dict[str, Any],
    observations: dict[str, Any],
) -> None:
    # A self-consistent old-count receipt and replay still violate the current
    # reviewed contract; matching those two objects must not rebind the seal.
    for stale_count in [119, 120]:
        observations["atlas"]["pairingVisible"] = stale_count
        receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
        assert "browser receipt detailed DOM observations are not canonical" in (
            bundle_module._browser_receipt_errors(project_root, check_runtime=False)
        )
    observations["atlas"]["pairingVisible"] = 118
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    assert (
        bundle_module._browser_receipt_errors(project_root, check_runtime=False) == ()
    )


def test_browser_receipt_is_bound_to_canonical_projections_and_screenshots(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    chrome = tmp_path / "google-chrome"
    chrome.write_bytes(b"canonical Chrome fixture\n")
    chrome_digest = hashlib.sha256(chrome.read_bytes()).hexdigest()
    decoy = tmp_path / "google-chrome-decoy"
    decoy.write_bytes(b"different Chrome fixture\n")
    monkeypatch.setattr(
        bundle_module.shutil,
        "which",
        lambda name: str(decoy) if name == "google-chrome" else None,
    )
    monkeypatch.setattr(
        bundle_module.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(
            returncode=0,
            stdout="Google Chrome 151.0.7922.169\n",
            stderr="",
        ),
    )
    projection_records: dict[str, dict[str, str]] = {}
    for key, relative in bundle_module._CANONICAL_BROWSER_PROJECTIONS.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"{key}\n", encoding="utf-8")
        projection_records[key] = {
            "path": relative,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
    screenshot_records: list[dict[str, object]] = []
    for (
        role,
        screenshot_relative,
    ) in bundle_module._CANONICAL_BROWSER_SCREENSHOTS.items():
        if role.endswith("_mobile"):
            width, height = 390, 844
        elif role.endswith("_desktop"):
            width, height = 1440, 900
        else:
            width, height = 1600, 1000
        screenshot = tmp_path / screenshot_relative
        screenshot.parent.mkdir(parents=True, exist_ok=True)
        screenshot.write_bytes(_png_bytes(width, height))
        screenshot_records.append(
            {
                "role": role,
                "path": screenshot_relative,
                "sha256": hashlib.sha256(screenshot.read_bytes()).hexdigest(),
                "width": width,
                "height": height,
            }
        )
    expected = {
        "topics": 168,
        "families": 22,
        "witnesses": 22,
        "relations": 156,
        "capabilities": 50,
        "external_requests": [],
        "atlas": {
            "areas": 5,
            "bodyFitsViewport": True,
            "detailSections": 4,
            "detailsInitiallyOpen": 0,
            "escapeCleared": True,
            "escapePreservedFilters": True,
            "outsideEscapePreservedFilters": True,
            "clearAllResetFilters": True,
            "families": 22,
            "fepVisible": 41,
            "pairingVisible": 118,
            "relationCards": 156,
            "relations": 156,
            "searchVisible": 1,
            "slashFocused": True,
            "topics": 168,
        },
        "atlas_mobile": {
            "areas": 5,
            "bodyFitsViewport": True,
            "desktopSummaryHidden": True,
            "detailSections": 4,
            "detailsInitiallyOpen": 0,
            "families": 22,
            "mobileSummaryVisible": True,
            "relationCards": 156,
            "topics": 168,
        },
        "dashboard": {
            "acceptedVisible": 22,
            "accessibleTables": 22,
            "bodyFitsViewport": True,
            "detailJumps": 22,
            "detailRecords": 22,
            "detailsInitiallyOpen": 0,
            "escapeCleared": True,
            "escapePreservedFilters": True,
            "outsideEscapePreservedFilters": True,
            "clearAllResetFilters": True,
            "exactScrollRegions": 66,
            "familyVisible": 1,
            "filterOpened": 1,
            "jumpFocused": True,
            "jumpOpened": True,
            "overviewHiddenByFilter": True,
            "searchVisible": 1,
            "slashFocused": True,
            "structuralAnalogues": 1,
            "theoremInstances": 21,
            "witnesses": 22,
        },
        "dashboard_mobile": {
            "escapeCleared": True,
            "escapePreservedFilters": True,
            "outsideEscapePreservedFilters": True,
            "clearAllResetFilters": True,
            "bodyFitsViewport": True,
            "compactDefaultHeight": True,
            "desktopOverviewHidden": True,
            "detailJumps": 22,
            "detailRecords": 22,
            "detailsInitiallyOpen": 0,
            "exactScrollRegions": 66,
            "filterOpened": 1,
            "jumpFocused": True,
            "jumpOpened": True,
            "mobileOverviewInitiallyOpen": False,
            "mobileOverviewDisclosureVisible": True,
            "overviewHiddenByFilter": True,
            "plotSummaries": 22,
            "recordCollectionInitiallyOpen": False,
            "witnesses": 22,
        },
    }
    capture_provenance = {
        "command": "uv run python scripts/capture_browser_acceptance.py",
        "owner": "src/fep_formal/output/browser_capture.py",
        "owner_sha256": "b" * 64,
        "protocol": "Chrome DevTools Protocol",
        "wrapper": "scripts/capture_browser_acceptance.py",
        "wrapper_sha256": "c" * 64,
    }
    render_configuration = bundle_module.canonical_browser_render_configuration()
    render_environment = {
        "browser_locale": "en-US",
        "device_pixel_ratio": "1",
        "platform": "Linux x86_64",
        "timezone": "UTC",
        "webgl_renderer": "SwiftShader fixture",
        "webgl_vendor": "Google Inc. fixture",
    }
    receipt = {
        "schema_version": 4,
        "kind": "browser-interaction",
        "accepted": True,
        "browser": {
            "name": "Google Chrome",
            "version": "151.0.7922.169",
            "executable_path": str(chrome.resolve()),
            "executable_sha256": chrome_digest,
        },
        "render_configuration": dict(render_configuration),
        "render_environment": dict(render_environment),
        "capture": dict(capture_provenance),
        "projections": projection_records,
        "screenshots": screenshot_records,
        "interactions": {
            key: True for key in bundle_module._REQUIRED_BROWSER_INTERACTIONS
        },
        "observed": expected,
        "expected": expected,
    }
    receipt_path = tmp_path / bundle_module.BROWSER_RECEIPT
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    monkeypatch.setattr(
        bundle_module,
        "build_formalism_presentation",
        lambda _root: SimpleNamespace(
            topics=(None,) * 168,
            families=(None,) * 22,
            witnesses=(None,) * 22,
            relations=(None,) * 156,
            capabilities=(None,) * 50,
        ),
    )
    captured_screenshots = {
        record["role"]: (tmp_path / str(record["path"])).read_bytes()
        for record in screenshot_records
    }
    replay = SimpleNamespace(
        browser=receipt["browser"],
        render_configuration=render_configuration,
        render_environment=render_environment,
        observations=expected,
        interactions=receipt["interactions"],
        screenshot_bytes=captured_screenshots,
    )
    replay_calls: list[tuple[Path, str | None, Path | None]] = []

    def replay_exact_browser(
        project_root: Path,
        *,
        browser_name: str | None = None,
        executable: Path | None = None,
    ) -> SimpleNamespace:
        replay_calls.append((project_root, browser_name, executable))
        return replay

    monkeypatch.setattr(
        bundle_module, "replay_browser_acceptance", replay_exact_browser
    )
    monkeypatch.setattr(
        bundle_module,
        "canonical_browser_capture_provenance",
        lambda _root: capture_provenance,
    )

    static_snapshot = {
        path: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in tmp_path.rglob("*")
        if path.is_file()
    }

    def forbidden_browser_execution(*_args: object, **_kwargs: object) -> None:
        pytest.fail("static browser validation started a browser process")

    with monkeypatch.context() as static_patch:
        static_patch.setattr(subprocess, "run", forbidden_browser_execution)
        static_patch.setattr(
            bundle_module, "replay_browser_acceptance", forbidden_browser_execution
        )
        assert (
            bundle_module._browser_receipt_errors(tmp_path, check_runtime=False) == ()
        )
    assert replay_calls == []
    assert static_snapshot == {
        path: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in tmp_path.rglob("*")
        if path.is_file()
    }

    assert bundle_module._browser_receipt_errors(tmp_path) == ()
    assert replay_calls[-1] == (tmp_path.resolve(), "Google Chrome", chrome.resolve())

    receipt["browser"]["executable_path"] = str(decoy.resolve())
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    assert "browser executable hash differs from the live browser binary" in (
        bundle_module._browser_receipt_errors(tmp_path)
    )
    receipt["browser"]["executable_path"] = str(chrome.resolve())
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

    replay.render_configuration = {
        **render_configuration,
        "gpu": "enabled",
    }
    assert "browser render configuration differs from live Chrome replay" in (
        bundle_module._browser_receipt_errors(tmp_path)
    )
    replay.render_configuration = render_configuration

    receipt["capture"]["owner_sha256"] = "0" * 64
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    assert "browser capture provenance is not canonical" in (
        bundle_module._browser_receipt_errors(tmp_path)
    )
    receipt["capture"]["owner_sha256"] = "b" * 64
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

    replay.browser = {**receipt["browser"], "version": "151.0.7922.170"}
    assert "browser receipt identity differs from live Chrome replay" in (
        bundle_module._browser_receipt_errors(tmp_path)
    )
    replay.browser = receipt["browser"]

    receipt["render_environment"]["timezone"] = "America/Los_Angeles"
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    assert "browser render environment is not canonical" in (
        bundle_module._browser_receipt_errors(tmp_path)
    )
    receipt["render_environment"] = dict(render_environment)
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

    replay.render_environment = {**render_environment, "gpu": "enabled"}
    assert "browser render environment differs from live Chrome replay" in (
        bundle_module._browser_receipt_errors(tmp_path)
    )
    replay.render_environment = render_environment

    replay.observations = {
        **expected,
        "external_requests": ["https://unexpected.invalid/asset.css"],
    }
    assert "browser receipt observations differ from live Chrome replay" in (
        bundle_module._browser_receipt_errors(tmp_path)
    )
    replay.observations = expected

    replay.screenshot_bytes = {
        **captured_screenshots,
        "atlas_desktop": b"different live Chrome pixels",
    }
    assert (
        "browser screenshot differs from live Chrome capture: "
        "specs/done/formalism-catalogue-155/assets/atlas-155-desktop.png"
        in bundle_module._browser_receipt_errors(tmp_path)
    )
    replay.screenshot_bytes = captured_screenshots

    _assert_stale_pairing_count_rejected(tmp_path, receipt_path, receipt, expected)

    del expected["atlas"]["slashFocused"]
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    assert "browser receipt detailed DOM observations are not canonical" in (
        bundle_module._browser_receipt_errors(tmp_path)
    )
    expected["atlas"]["slashFocused"] = True
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

    receipt["browser"]["executable_sha256"] = "0" * 64
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    assert "browser executable hash cannot be the all-zero sentinel" in (
        bundle_module._browser_receipt_errors(tmp_path)
    )
    receipt["browser"]["executable_sha256"] = chrome_digest
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

    first = receipt["screenshots"][0]
    invalid_png = tmp_path / str(first["path"])
    invalid_png.write_bytes(b"not a png")
    first["sha256"] = hashlib.sha256(invalid_png.read_bytes()).hexdigest()
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    assert "browser screenshot is not a PNG stream" in (
        bundle_module._browser_receipt_errors(tmp_path)
    )

    (tmp_path / "docs/formalism-atlas.html").write_text("tampered\n", encoding="utf-8")
    assert (
        "browser receipt projection hash is stale: atlas_html"
        in bundle_module._browser_receipt_errors(tmp_path)
    )


def test_release_rejects_an_unsupported_receipt_browser_product(tmp_path: Path) -> None:
    executable = tmp_path / "brave-like"
    executable.write_text(
        '#!/bin/sh\nprintf "Brave Browser 123.4.5.6\\n"\n',
        encoding="utf-8",
    )
    executable.chmod(0o755)

    with pytest.raises(
        bundle_module.ReleaseBundleError,
        match="supported Chrome or Chromium product",
    ):
        bundle_module._live_browser_identity("Chromium", executable)
