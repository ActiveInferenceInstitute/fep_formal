"""Static source contracts for the H2.6a-R0 native posterior proof spike."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest

from fep_lean.formal.manifest import FORMAL_MODULES
from fep_lean.lean_source import lean_code_without_comments
from tests._support.lean_runner import run_lean_probe

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEAN_ROOT = PROJECT_ROOT / "lean"
SPIKE = (
    PROJECT_ROOT
    / "specs"
    / "horizon-2-smooth-stochastic"
    / "spikes"
    / "06a_native_filter_posterior.lean"
)
REPAIR = (
    PROJECT_ROOT
    / "specs"
    / "horizon-2-smooth-stochastic"
    / "readiness"
    / "repairs"
    / "06a-native-filter-posterior.json"
)
SOURCE_BOUND_PATHS = (
    "lean/lean-toolchain",
    "lean/lakefile.lean",
    "lean/lake-manifest.json",
    "specs/horizon-2-smooth-stochastic/readiness/acceptance.json",
    "specs/horizon-2-smooth-stochastic/readiness/matrix.yaml",
    "specs/horizon-2-smooth-stochastic/readiness/probes/08_gaussian_conditioning.lean",
    "src/fep_lean/formal/gaussian_information_geometry.lean",
    "src/fep_lean/formal/scalar_gaussian_semigroup.lean",
    "specs/horizon-2-smooth-stochastic/slices/06a-r0-native-posterior.md",
    "specs/horizon-2-smooth-stochastic/spikes/06a_native_filter_posterior.lean",
    "tests/test_horizon2_native_filter_posterior_readiness.py",
)

EXACT_IMPORTS = (
    "FepSketches.gaussian_information_geometry",
    "FepSketches.scalar_gaussian_semigroup",
    "Mathlib.Probability.Distributions.Gaussian.Real",
    "Mathlib.Probability.Kernel.Posterior",
)
PUBLIC_DEFINITIONS = (
    "law",
    "predictionVariance",
    "predictionBelief",
    "observationKernel",
    "innovationVariance",
    "gain",
    "posteriorMean",
    "posteriorVariance",
    "posteriorFamily",
    "posteriorBelief",
    "closedFormPosteriorKernel",
    "evidenceFamily",
    "evidenceLaw",
    "evidenceDensity",
)
PUBLIC_THEOREMS = (
    "predictionVariance_pos",
    "predictionBelief_law_eq_ouTransition",
    "observationKernel_apply",
    "innovationVariance_pos",
    "posteriorVariance_pos",
    "gaussianPDF_factorization",
    "gaussianEvidence_compProd_closedForm_eq_map_swap",
    "evidenceLaw_eq_gaussian",
    "closedFormPosterior_compProd_eq_map_swap",
    "closedFormPosterior_ae_eq_native",
    "evidenceDensity_pos",
    "evidenceDensity_ne_zero",
    "evidenceLaw_singleton_eq_zero",
    "closedFormPosterior_univ",
)

pytestmark = pytest.mark.serial_lean




def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()




def test_h2_6a_r0_is_a_spike_without_a_maintained_owner() -> None:
    assert SPIKE.is_file()
    assert all(module.resource != SPIKE.name for module in FORMAL_MODULES)


def test_h2_6a_r0_reuses_exact_scalar_owners_and_stores_only_raw_inputs() -> None:
    source = SPIKE.read_text(encoding="utf-8")
    uncommented = lean_code_without_comments(source)

    assert tuple(re.findall(r"(?m)^import (\S+)$", source)) == EXACT_IMPORTS
    assert "namespace FEPProbe.H2_6aNativePosterior\n" in source
    assert source.rstrip().endswith("end FEPProbe.H2_6aNativePosterior")
    assert re.search(
        r"structure ScalarGaussianBelief where\s+"
        r"mean : ℝ\s+"
        r"family : FixedVarianceGaussian",
        uncommented,
    )
    model = re.search(
        r"structure ScalarGaussianFilterModel where\n(?P<body>.*?)(?=\n\n)",
        uncommented,
        re.DOTALL,
    )
    assert model is not None
    assert tuple(re.findall(r"(?m)^  (\w+)\s*:", model["body"])) == (
        "dynamics",
        "stepDuration",
        "observationNoise",
    )


def test_h2_6a_r0_derives_the_exact_update_surface_fail_closed() -> None:
    source = lean_code_without_comments(SPIKE.read_text(encoding="utf-8"))

    assert (
        tuple(re.findall(r"(?m)^(?:noncomputable )?def (\w+)\b", source))
        == PUBLIC_DEFINITIONS
    )
    assert "NNReal.mk (model.dynamics.decay model.stepDuration ^ 2)" in source
    assert "model.dynamics.transitionVariance model.stepDuration" in source
    assert "predicted.family.variance + model.observationNoise.variance" in source
    assert "(predicted.family.variance : ℝ) /" in source
    assert (
        "predicted.mean + gain model prior * (observation - predicted.mean)" in source
    )
    assert (
        "predicted.family.variance * model.observationNoise.variance /\n"
        "    innovationVariance model prior"
    ) in source
    assert not re.search(
        r"(?m)^  (?:posterior|gain|evidence|processVariance|transitionKernel|"
        r"observationKernel)\s*:",
        source,
    )
    assert not re.search(
        r"\b(?:sorry|admit|axiom|opaque)\b|unsafe\s+(?:def|theorem)|:\s*True\b",
        source,
    )


def test_h2_6a_r0_public_theorems_encode_the_native_proof_ladder() -> None:
    source = lean_code_without_comments(SPIKE.read_text(encoding="utf-8"))

    assert tuple(re.findall(r"(?m)^theorem (\w+)\b", source)) == PUBLIC_THEOREMS
    assert "ouTransition_comp_gaussian" in source
    assert re.search(
        r"gaussianPDF predicted\.mean predicted\.family\.variance state \*\s*"
        r"gaussianPDF state model\.observationNoise\.variance observation =\s*"
        r"evidenceDensity model prior observation \*",
        source,
    )
    assert re.search(
        r"\(evidenceFamily model prior\)\.law predicted\.mean ⊗ₘ\s*"
        r"closedFormPosteriorKernel model prior =\s*"
        r"\(\(predictionBelief model prior\)\.law ⊗ₘ observationKernel model\)\.map\s*"
        r"Prod\.swap",
        source,
    )
    assert re.search(
        r"evidenceLaw model prior ⊗ₘ closedFormPosteriorKernel model prior =\s*"
        r"\(\(predictionBelief model prior\)\.law ⊗ₘ observationKernel model\)\.map\s*"
        r"Prod\.swap",
        source,
    )
    assert "ProbabilityTheory.ae_eq_posterior_of_compProd_eq" in source
    assert re.search(
        r"closedFormPosteriorKernel model prior\s*=ᵐ\[evidenceLaw model prior\]\s*"
        r"ProbabilityTheory\.posterior",
        source,
    )
    assert not re.search(
        r"closedFormPosteriorKernel model prior\s*=\s*"
        r"ProbabilityTheory\.posterior",
        source,
    )
    assert "0 < evidenceDensity model prior observation" in source
    assert "evidenceLaw model prior {observation} = 0" in source


def test_h2_6a_r0_excludes_out_of_scope_and_atomic_evidence_claims() -> None:
    raw_source = SPIKE.read_text(encoding="utf-8")
    source = lean_code_without_comments(raw_source)

    assert "Source-only freeze:" in raw_source
    assert not re.search(
        r"0\s*<\s*evidenceLaw\b.*\{(?:observation|datum)\}",
        source,
        re.DOTALL,
    )
    assert not re.search(
        r"\b(?:KalmanBucy|Kalman--Bucy|nonlinearFilter|SDE|Ito|Itô|"
        r"parameterConsistency)\b",
        source,
    )
    assert not re.search(
        r"model\.observationNoise\.variance\s*=\s*0|"
        r"if\s+innovationVariance\b.*=\s*0",
        source,
        re.DOTALL,
    )


def test_h2_6a_r0_spike_compiles_warning_free(tmp_path: Path) -> None:
    probe = tmp_path / "H2_6aNativePosteriorSpike.lean"
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


def test_h2_6a_r0_public_theorems_use_only_standard_axioms(tmp_path: Path) -> None:
    probe = tmp_path / "H2_6aNativePosteriorAxioms.lean"
    source = SPIKE.read_text(encoding="utf-8")
    prints = "\n".join(
        f"#print axioms FEPProbe.H2_6aNativePosterior.{name}"
        for name in PUBLIC_THEOREMS
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
        axioms = set(re.findall(r"'([^']+)'", block))
        assert axioms <= {"propext", "Classical.choice", "Quot.sound"}


def test_h2_6a_r0_repair_is_source_bound_append_only_go() -> None:
    assert REPAIR.is_file()
    repair = json.loads(REPAIR.read_text(encoding="utf-8"))

    assert repair["schema_version"] == 1
    assert repair["gate"] == "H2.6a-R0"
    assert repair["decision"] == "go"
    assert repair["decision_scope"] == "open_H2.6a_implementation_only"
    assert repair["historical_boundary"] == {
        "acceptance_mutated": False,
        "addendum_only": True,
        "matrix_mutated": False,
        "row_id": "native_filter_posterior",
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
    assert repair["proof_route"]["scope_substitution_used"] is False
    assert repair["proof_route"]["posterior_equality_scope"] == (
        "evidence_almost_everywhere"
    )
    assert repair["proof_route"]["positive_evidence_claim"] == (
        "strictly_positive_density_everywhere"
    )
    assert repair["proof_route"]["singleton_evidence_mass"] == "zero"
    assert repair["evidence"]["compiler_exit_code"] == 0
    assert repair["evidence"]["warning_count"] == 0
    assert repair["evidence"]["warning_sha256"] == hashlib.sha256(b"").hexdigest()
    assert repair["evidence"]["standard_axiom_audit"] is True
    assert repair["evidence"]["public_theorem_count"] == len(PUBLIC_THEOREMS)
    assert repair["evidence"]["allowed_axioms"] == [
        "propext",
        "Classical.choice",
        "Quot.sound",
    ]
    assert repair["evidence"]["sorry_axiom_present"] is False
    assert repair["review"]["independent_probability"] == (
        "approved_no_mathematical_blocker"
    )
    assert repair["downstream"]["opened"] == ["H2.6a implementation"]
    assert repair["downstream"]["remains_closed"] == [
        "H2.6b pending maintained H2.6a acceptance",
        "H2.7 terminal filter/control clauses",
    ]
    assert repair["source_sha256"] == {
        relative: _sha256(PROJECT_ROOT / relative) for relative in SOURCE_BOUND_PATHS
    }
