"""Native contracts for reusable finite Markov dynamics."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tests._support.lake import lake_executable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEAN_ROOT = PROJECT_ROOT / "lean"
FORMAL_SOURCE = (
    PROJECT_ROOT / "src" / "fep_lean" / "formal" / "finite_markov_dynamics.lean"
)

pytestmark = pytest.mark.serial_lean


def test_finite_markov_dynamics_compiles_warning_free() -> None:
    result = subprocess.run(
        [lake_executable(), "env", "lean", str(FORMAL_SOURCE)],
        cwd=LEAN_ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=300,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "warning:" not in (result.stdout + result.stderr).lower()


def test_finite_markov_dynamics_exposes_deep_contracts() -> None:
    source = FORMAL_SOURCE.read_text(encoding="utf-8")
    expected = {
        "kernelPower_add",
        "isInvariant_kernelPower",
        "isReversible_kernelPower",
        "hasDobrushinBound_comp",
        "totalVariation_kernelPower_le",
        "masterIncrement_sum_zero",
    }

    assert all(f"theorem {name}" in source for name in expected)
    assert "sorry" not in source
    assert "axiom " not in source
