"""Capability validation contract."""

from pathlib import Path

import pytest

from fep_formal.verification.environment import (
    CATALOGUE_VALIDATION_CHECK_NAMES,
    FULL_VALIDATION_CHECK_NAMES,
    run_validation_checks,
)

PROJ = Path(__file__).resolve().parent.parent


def test_catalogue_validation_is_read_only_capability_check() -> None:
    result = run_validation_checks(PROJ, mode="catalogue")
    assert result["status"] == "ok"
    assert result["mode"] == "catalogue"
    assert result["failed_count"] == 0
    assert all(check["ok"] for check in result["checks"])
    assert [check["name"] for check in result["checks"]] == list(
        CATALOGUE_VALIDATION_CHECK_NAMES
    )


def test_full_validation_reports_missing_capabilities_without_building(
    monkeypatch,
) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    result = run_validation_checks(PROJ, mode="full")
    assert result["status"] == "error"
    assert any(
        check["name"] == "hermes_credentials" and not check["ok"]
        for check in result["checks"]
    )
    assert any(check["name"] == "mathlib_built" for check in result["checks"])
    assert [check["name"] for check in result["checks"]] == list(
        FULL_VALIDATION_CHECK_NAMES
    )


def test_validation_reports_the_selected_output_target(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = tmp_path / "selected"
    selected.mkdir()
    monkeypatch.setattr(
        "fep_formal.verification.environment.os.access",
        lambda path, _mode: Path(path) != selected,
    )
    result = run_validation_checks(PROJ, mode="catalogue", output_root=selected)
    output = next(
        check for check in result["checks"] if check["name"] == "output_writable"
    )
    assert output["ok"] is False
    assert str(selected) in output["message"]
    assert result["status"] == "error"

    monkeypatch.setenv("FEP_FORMAL_OUTPUT_ROOT", str(selected))
    implicit = run_validation_checks(PROJ, mode="catalogue")
    implicit_output = next(
        check for check in implicit["checks"] if check["name"] == "output_writable"
    )
    assert implicit_output["ok"] is False
    assert str(selected) in implicit_output["message"]


@pytest.mark.parametrize(
    ("banner", "toolchain", "expected"),
    [
        (
            "Lake version 5.0.0-src+eb6cafb (Lean version 4.35.0)",
            "leanprover/lean4:v4.35.0",
            True,
        ),
        (
            "Lake version 5.0.0-src+eb6cafb (Lean version 4.35.0)",
            "leanprover--lean4---v4.35.0",
            True,
        ),
        (
            "Lake version 5.0.0 (Lean version 4.35.0)\n",
            "leanprover/lean4:v4.35.0",
            True,
        ),
        (
            "Lean (version 4.35.0, arm64-apple-darwin, Release)",
            "leanprover/lean4:v4.35.0",
            False,
        ),
        (
            "Lake version 4.35.0 (Lean version 4.34.0)",
            "leanprover/lean4:v4.35.0",
            False,
        ),
        (
            "Lake version 5.0.0 (Lean version 4.350.0)",
            "leanprover--lean4---v4.35.0",
            False,
        ),
        (
            "Lake version 5.0.0 (Lean version 4.35.0-rc1)",
            "leanprover/lean4:v4.35.0",
            False,
        ),
        (
            "not Lake version 5.0.0 (Lean version 4.35.0)",
            "leanprover/lean4:v4.35.0",
            False,
        ),
        (
            "noise\nLake version 5.0.0 (Lean version 4.35.0)",
            "leanprover/lean4:v4.35.0",
            False,
        ),
        ("", "leanprover/lean4:v4.35.0", False),
        ("Lake version 5.0.0 (Lean version 4.35.0)", "other/lean4:v4.35.0", False),
        (
            "Lake version 5.0.0 (Lean version 4.35.0)",
            "leanprover--lean4---v4.35.0-extra",
            False,
        ),
        ("Lake version 5.0.0 (Lean version 4.35.0)", "v4.35.0", False),
    ],
)
def test_lake_banner_requires_the_pinned_embedded_lean_version(
    banner: str, toolchain: str, expected: bool
) -> None:
    from fep_formal.verification._toolchain import lake_version_matches_pin

    assert lake_version_matches_pin(banner, toolchain) is expected
