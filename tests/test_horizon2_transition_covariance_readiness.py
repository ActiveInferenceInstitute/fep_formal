"""H2.5b-R0 transition-covariance proof-spike contracts."""

import hashlib
import json
import os
import re
from pathlib import Path

import pytest

from tests._support.lean_runner import run_lean_probe

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEAN_ROOT = PROJECT_ROOT / "lean"
SPIKE = (
    PROJECT_ROOT
    / "specs"
    / "horizon-2-smooth-stochastic"
    / "spikes"
    / "05b_transition_covariance.lean"
)
FIN4_PROBE = (
    PROJECT_ROOT
    / "specs"
    / "horizon-2-smooth-stochastic"
    / "readiness"
    / "probes"
    / "07_fin4_matrix_gaussian.lean"
)
REPAIR = (
    PROJECT_ROOT
    / "specs"
    / "horizon-2-smooth-stochastic"
    / "readiness"
    / "repairs"
    / "05b-transition-covariance.json"
)
SOURCE_BOUND_PATHS = (
    "lean/lean-toolchain",
    "lean/lakefile.lean",
    "lean/lake-manifest.json",
    "specs/horizon-2-smooth-stochastic/readiness/acceptance.json",
    "specs/horizon-2-smooth-stochastic/readiness/matrix.yaml",
    "specs/horizon-2-smooth-stochastic/readiness/probes/07_fin4_matrix_gaussian.lean",
    "src/fep_lean/formal/markov_semigroup.lean",
    "src/fep_lean/formal/scalar_gaussian_semigroup.lean",
    "specs/horizon-2-smooth-stochastic/slices/05b-r0-transition-covariance.md",
    "specs/horizon-2-smooth-stochastic/spikes/05b_transition_covariance.lean",
    "tests/test_horizon2_transition_covariance_readiness.py",
)
PUBLIC_DEFINITIONS = ("covariance", "evolution", "transitionCovariance")
EXACT_IMPORTS = (
    "Mathlib.Analysis.Matrix.PosDef",
    "Mathlib.Analysis.Normed.Algebra.MatrixExponential",
    "Mathlib.Analysis.SpecialFunctions.Exponential",
    "Mathlib.Tactic.NoncommRing",
    "Mathlib.Topology.Instances.NNReal.Lemmas",
)
PUBLIC_THEOREMS = (
    "transitionCovariance_zero",
    "transitionCovariance_posSemidef",
    "transitionCovariance_posDef",
    "transitionCovariance_add",
)
ALLOWED_AXIOMS = frozenset({"propext", "Classical.choice", "Quot.sound"})

pytestmark = pytest.mark.serial_lean


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _parse_axiom_names(block: str) -> set[str]:
    return {
        token.strip().strip("'")
        for token in block.split(",")
        if token.strip().strip("'")
    }


def test_axiom_parser_accepts_lean_4_33_unquoted_names() -> None:
    assert _parse_axiom_names("propext, Classical.choice, Quot.sound") == {
        "propext",
        "Classical.choice",
        "Quot.sound",
    }
    assert _parse_axiom_names("'propext', 'Classical.choice'") == {
        "propext",
        "Classical.choice",
    }


def test_h2_5b_r0_spike_exists() -> None:
    assert SPIKE.is_file()


def test_h2_5b_r0_public_surface_is_exact_generic_and_fail_closed() -> None:
    source = SPIKE.read_text(encoding="utf-8")

    assert "namespace FEP.TransitionCovarianceR0\n" in source
    assert source.rstrip().endswith("end FEP.TransitionCovarianceR0")
    assert tuple(re.findall(r"(?m)^import (\S+)$", source)) == EXACT_IMPORTS
    assert (
        tuple(re.findall(r"(?m)^(?:noncomputable )?def (\w+)\b", source))
        == PUBLIC_DEFINITIONS
    )
    assert tuple(re.findall(r"(?m)^theorem (\w+)\b", source)) == PUBLIC_THEOREMS
    assert "{Axis : Type*} [Fintype Axis] [DecidableEq Axis]" in source
    assert not re.search(
        r"\b(?:sorry|admit|axiom|opaque)\b|unsafe\s+(?:def|theorem)|:\s*True\b",
        source,
    )
    assert "precision⁻¹" in source
    assert "NormedSpace.exp ((-(time : ℝ)) • precision)" in source
    assert "(transitionCovariance precision time).PosSemidef" in source
    assert "(transitionCovariance precision time).PosDef" in source
    assert "(hTime : 0 < time)" in source
    assert "transitionCovariance precision (left + right)" in source
    assert "evolution precision right * transitionCovariance precision left" in source
    assert not re.search(
        r"\b(?:Fin4Axis|eigenmodeTwo|eigenmodeFour|eigenmodeSix|"
        r"SDE|Ito|Itô|FokkerPlanck|Brownian|generator|Generator)\b",
        source,
    )
    assert not re.search(r"structure\s+\w+|transitionCovariancePosSemidef\s*:", source)


def test_h2_5b_r0_spike_compiles_warning_free(tmp_path: Path) -> None:
    probe = tmp_path / "TransitionCovarianceR0Spike.lean"
    probe.write_text(SPIKE.read_text(encoding="utf-8"), encoding="utf-8")
    result = run_lean_probe(
        probe,
        import_root=PROJECT_ROOT / "src" / "fep_lean" / "formal",
        cwd=LEAN_ROOT,
        timeout_s=1800,
    )

    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "warning:" not in output.lower()


def test_h2_5b_r0_public_theorems_use_only_standard_axioms(tmp_path: Path) -> None:
    probe = tmp_path / "TransitionCovarianceR0Axioms.lean"
    source = SPIKE.read_text(encoding="utf-8")
    prints = "\n".join(
        f"#print axioms FEP.TransitionCovarianceR0.{name}" for name in PUBLIC_THEOREMS
    )
    probe.write_text(f"{source}\n{prints}\n", encoding="utf-8")
    result = run_lean_probe(
        probe,
        import_root=PROJECT_ROOT / "src" / "fep_lean" / "formal",
        cwd=LEAN_ROOT,
        timeout_s=1800,
    )

    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "sorryAx" not in output
    assert "warning:" not in output.lower()
    axiom_blocks = re.findall(r"depends on axioms: \[(.*?)\]", output, re.DOTALL)
    assert len(axiom_blocks) == len(PUBLIC_THEOREMS), output
    for block in axiom_blocks:
        axioms = _parse_axiom_names(block)
        assert axioms, f"vacuous axiom block: {block!r}\n{output}"
        assert axioms <= ALLOWED_AXIOMS, axioms


@pytest.mark.skipif(
    os.environ.get("FEP_HEAVY_LEAN_PROBES") != "1",
    reason="fin4 consumer composes two full-root sources; runs only with FEP_HEAVY_LEAN_PROBES=1 "
    "(reliably exceeds compile timeouts when Mathlib imports run concurrently)",
)
def test_h2_5b_r0_generic_contract_has_exact_fin4_consumer(tmp_path: Path) -> None:
    probe = tmp_path / "TransitionCovarianceR0Fin4.lean"
    spike_source = SPIKE.read_text(encoding="utf-8")
    fin4_source = FIN4_PROBE.read_text(encoding="utf-8")
    imports = tuple(
        dict.fromkeys(re.findall(r"(?m)^import \S+$", f"{fin4_source}\n{spike_source}"))
    )
    bodies = re.sub(r"(?m)^import \S+\n", "", f"{fin4_source}\n{spike_source}")
    consumer = """
example :
    FEP.TransitionCovarianceR0.covariance fin4Precision = fin4Covariance :=
  fin4Covariance_eq_inverse.symm

example (time : ℝ≥0) :
    (FEP.TransitionCovarianceR0.transitionCovariance fin4Precision time).PosSemidef :=
  FEP.TransitionCovarianceR0.transitionCovariance_posSemidef
    fin4Precision fin4Precision_posDef time

example (time : ℝ≥0) (hTime : 0 < time) :
    (FEP.TransitionCovarianceR0.transitionCovariance fin4Precision time).PosDef :=
  FEP.TransitionCovarianceR0.transitionCovariance_posDef
    fin4Precision fin4Precision_posDef time hTime

example (left right : ℝ≥0) :
    FEP.TransitionCovarianceR0.transitionCovariance fin4Precision (left + right) =
      FEP.TransitionCovarianceR0.evolution fin4Precision right *
          FEP.TransitionCovarianceR0.transitionCovariance fin4Precision left *
            (FEP.TransitionCovarianceR0.evolution fin4Precision right)ᵀ +
        FEP.TransitionCovarianceR0.transitionCovariance fin4Precision right :=
  FEP.TransitionCovarianceR0.transitionCovariance_add
    fin4Precision fin4Precision_posDef left right
"""
    import_source = "\n".join(imports)
    probe.write_text(f"{import_source}\n{bodies}\n{consumer}\n", encoding="utf-8")
    result = run_lean_probe(
        probe,
        import_root=PROJECT_ROOT / "src" / "fep_lean" / "formal",
        cwd=LEAN_ROOT,
        timeout_s=1800,
    )

    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "warning:" not in output.lower()
    assert "eigenmodeTwo" not in consumer
    assert "eigenmodeFour" not in consumer
    assert "eigenmodeSix" not in consumer


def test_h2_5b_r0_repair_is_source_bound_append_only_go() -> None:
    assert REPAIR.is_file()
    repair = json.loads(REPAIR.read_text(encoding="utf-8"))

    assert repair["schema_version"] == 1
    assert repair["gate"] == "H2.5b-R0"
    assert repair["decision"] == "go"
    assert repair["decision_scope"] == "open_H2.5b_implementation_only"
    assert repair["historical_boundary"] == {
        "acceptance_mutated": False,
        "addendum_only": True,
        "matrix_mutated": False,
        "row_id": "transition_covariance_psd",
        "row_status_at_decision": "blocking_no_go",
    }
    assert repair["compiler"] == {
        "lean_commit": "819816b2e0a3bf405af45ae5c7af2491d8f5bee6",
        "lean_version": "4.33.1",
        "mathlib_revision": "0df444a360eaa60ab8c11dca51a86af692955474",
        "mathlib_tag": "v4.33.1",
    }
    assert repair["declarations"] == {
        "definitions": list(PUBLIC_DEFINITIONS),
        "theorems": list(PUBLIC_THEOREMS),
    }
    assert repair["evidence"]["compiler_exit_code"] == 0
    assert repair["evidence"]["warning_count"] == 0
    assert repair["evidence"]["warning_sha256"] == hashlib.sha256(b"").hexdigest()
    assert repair["evidence"]["standard_axiom_audit"] is True
    assert repair["evidence"]["allowed_axioms"] == [
        "propext",
        "Classical.choice",
        "Quot.sound",
    ]
    assert repair["evidence"]["exact_fin4_consumer"] is True
    assert repair["proof_route"]["generic_finite_axis"] is True
    assert repair["proof_route"]["exact_fin4_diagonalization_required"] is False
    assert repair["proof_route"]["stored_psd_or_pd_certificate"] is False
    assert repair["downstream"]["opened"] == ["H2.5b implementation"]
    assert repair["downstream"]["remains_closed"] == [
        "H2.5c pending maintained H2.5b acceptance",
        "H2.5d pending H2.5c and conditioning repair",
        "H2.7",
        "continuous H3",
    ]
    assert repair["source_sha256"] == {
        relative: _sha256(PROJECT_ROOT / relative) for relative in SOURCE_BOUND_PATHS
    }
