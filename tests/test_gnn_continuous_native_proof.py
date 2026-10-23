"""Serial native proof checks for the Q7 concrete coefficient bounds."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from fep_lean.verification.formalism_audit import parse_axiom_output
from fep_lean.verification.gnn_continuous_artifact_proof import NAMESPACE, THEOREMS
from tests._support.lean_runner import run_lean_probe

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "specs/gnn-bridge-q7-continuous-ou-proof/generated/probe.lean"
pytestmark = pytest.mark.serial_lean


def test_native_ou_bounds_have_complete_standard_axiom_census(tmp_path: Path) -> None:
    names = tuple(f"{NAMESPACE}.{name}" for name in THEOREMS)
    source = (
        PROBE.read_text()
        + "\n"
        + "\n".join(f"#print axioms {name}" for name in names)
        + "\n"
    )
    probe = tmp_path / "q7_positive.lean"
    probe.write_text(source)
    result = run_lean_probe(
        probe,
        import_root=ROOT / "src/fep_lean/formal",
        cwd=ROOT / "lean",
        timeout_s=1800,
    )
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert not re.search(r"\b(?:warning|sorry|sorryAx)\b", output)
    axioms, errors = parse_axiom_output(output, expected=names)
    assert not errors, errors
    assert set(axioms) == set(names)
    assert all(
        set(values) <= {"propext", "Classical.choice", "Quot.sound"}
        for values in axioms.values()
    )


@pytest.mark.parametrize("coefficient", ["artifactF", "artifactQ"])
def test_native_wrong_coefficient_cannot_prove_rounding_bound(
    tmp_path: Path, coefficient: str
) -> None:
    source, count = re.subn(
        rf"^def {coefficient} : ℝ := .*$",
        f"def {coefficient} : ℝ := (1 / 2 : ℝ)",
        PROBE.read_text(),
        flags=re.MULTILINE,
    )
    assert count == 1
    probe = tmp_path / f"q7_wrong_{coefficient}.lean"
    probe.write_text(source)
    result = run_lean_probe(
        probe,
        import_root=ROOT / "src/fep_lean/formal",
        cwd=ROOT / "lean",
        timeout_s=1800,
    )
    output = result.stdout + result.stderr
    assert result.returncode != 0
    assert "unsolved goals" in output or "type mismatch" in output.lower(), output
