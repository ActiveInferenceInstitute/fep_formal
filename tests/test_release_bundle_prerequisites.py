"""Prerequisites release/publication boundary contracts."""

from __future__ import annotations

from pathlib import Path

import pytest

from fep_formal.output import release_bundle as bundle_module

PROJ = Path(__file__).resolve().parents[1]


def test_prerequisite_gate_reports_stale_projection_native_formal_and_browser_planes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        bundle_module,
        "report_owner_errors",
        lambda _root: ("canonical projection is stale",),
    )
    for name in (
        "formalism_coverage_drift",
        "atlas_projection_drift",
        "formal_kernel_dashboard_drift",
        "manuscript_projection_drift",
    ):
        monkeypatch.setattr(bundle_module, name, lambda _root: ())
    monkeypatch.setattr(
        bundle_module, "_theorem_maturity_projection_errors", lambda _root: ()
    )
    monkeypatch.setattr(bundle_module, "_rendered_manuscript_errors", lambda _root: ())
    monkeypatch.setattr(
        bundle_module,
        "validate_native_lean_receipt",
        lambda *_args, **_kwargs: {
            "valid": False,
            "source_bound": False,
            "native_claim_ready": False,
            "errors": ["source digest drifted"],
        },
    )
    monkeypatch.setattr(
        bundle_module,
        "validate_formalism_audit_receipt",
        lambda *_args: ("declaration closure drifted",),
    )
    monkeypatch.setattr(
        bundle_module,
        "_browser_receipt_errors",
        lambda _root, *, presentation=None: ("browser projection hash drifted",),
    )
    monkeypatch.setattr(bundle_module, "_pytest_receipt_errors", lambda _root: ())

    errors = bundle_module._base_prerequisite_errors(tmp_path)

    assert "canonical projection is stale" in errors
    assert (
        "native Lean receipt is not current and claim-ready: source digest drifted"
        in errors
    )
    assert "formalism audit receipt is stale: declaration closure drifted" in errors
    assert "browser projection hash drifted" in errors
