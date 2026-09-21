"""H1.2 native information and Bayesian decision-risk bridge tests."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from fep_lean.lean_source import lean_code_without_comments
from tests._support.lake import lake_executable
from tests._support.lean_runner import run_lean_compile_probe

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEAN_ROOT = PROJECT_ROOT / "lean"
FOUNDATION = PROJECT_ROOT / "src" / "fep_lean" / "formal" / "decision_risk.lean"

pytestmark = pytest.mark.serial_lean

EXACT_IMPORTS = (
    "FepSketches.native_blanket",
    "FepSketches.finite_information",
    "Mathlib.InformationTheory.KullbackLeibler.DataProcessing",
    "Mathlib.Probability.Decision.BayesEstimator",
    "Mathlib.Probability.Decision.Risk.Basic",
)




def _declaration(source: str, name: str) -> str:
    uncommented = lean_code_without_comments(source)
    match = re.search(
        rf"(?:theorem|lemma|def|noncomputable def)\s+{re.escape(name)}\b"
        rf"(?P<body>.*?)(?=\n(?:theorem|lemma|def|noncomputable def|end)\b|\Z)",
        uncommented,
        flags=re.DOTALL,
    )
    assert match is not None, f"missing declaration {name}"
    return match.group(0)


def test_decision_risk_foundation_owns_exact_import_and_namespace_contract() -> None:
    source = FOUNDATION.read_text(encoding="utf-8")

    assert tuple(re.findall(r"(?m)^import (\S+)$", source)) == EXACT_IMPORTS
    assert "namespace FEP.DecisionRisk\n" in source
    assert source.rstrip().endswith("end FEP.DecisionRisk")
    assert not re.search(
        r"\b(?:sorry|admit|axiom|opaque)\b|unsafe\s+(?:def|theorem)|:\s*True\b",
        source,
    )


def test_weighted_dirac_bridge_preserves_support_and_extended_real_boundaries() -> None:
    source = FOUNDATION.read_text(encoding="utf-8")
    supported = _declaration(source, "weightedDirac_klDiv_eq_finiteKL_of_fullSupport")
    singular = _declaration(
        source, "weightedDirac_klDiv_eq_top_of_not_absolutelyContinuous"
    )
    disjoint = _declaration(source, "boolPointMass_klDiv_eq_top")

    assert "(hq : ∀ x, 0 < q x)" in supported
    assert "InformationTheory.klDiv (embeddedLaw p) (embeddedLaw q)" in supported
    assert "ENNReal.ofReal (finiteKL p q)" in supported
    assert "¬ embeddedLaw p ≪ embeddedLaw q" in singular
    assert "InformationTheory.klDiv (embeddedLaw p) (embeddedLaw q) = ∞" in singular
    assert "FiniteLaw.pointMass true" in disjoint
    assert "FiniteLaw.pointMass false" in disjoint


def test_bool_experiment_has_distinct_native_bayes_risks_and_genuine_estimator() -> (
    None
):
    source = FOUNDATION.read_text(encoding="utf-8")
    monotonicity = _declaration(source, "bayesRisk_mono_under_observationGarbling")
    argmin = _declaration(source, "revealingBoolArgminEstimator")
    bayes = _declaration(source, "revealingBool_isBayesEstimator")
    revealing_risk = _declaration(source, "revealingBool_bayesRisk_eq_zero")
    garbled_risk = _declaration(source, "garbledBool_bayesRisk_eq_half")
    strict = _declaration(source, "revealingBool_bayesRisk_lt_garbled")

    assert "ProbabilityTheory.bayesRisk_le_bayesRisk_comp" in monotonicity
    assert "IsArgminEstimator" in argmin
    assert "boolZeroOneLoss" in argmin
    assert "revealingBoolExperiment" in argmin
    assert "IsBayesEstimator" in bayes
    assert ".isBayesEstimator" in bayes
    assert "bayesRisk boolZeroOneLoss revealingBoolExperiment boolPrior = 0" in (
        revealing_risk
    )
    assert "bayesRisk boolZeroOneLoss garbledBoolExperiment boolPrior = 1 / 2" in (
        garbled_risk
    )
    assert "bayesRisk boolZeroOneLoss revealingBoolExperiment boolPrior <" in strict
    assert "bayesRisk boolZeroOneLoss garbledBoolExperiment boolPrior" in strict


def test_proper_log_score_keeps_truth_report_order_and_exhibits_asymmetry() -> None:
    source = FOUNDATION.read_text(encoding="utf-8")
    excess = _declaration(source, "properLogScoreExcessRisk")
    identity = _declaration(
        source, "properLogScore_excessRisk_eq_finiteKL_truth_report"
    )
    asymmetric = _declaration(source, "finiteKL_asymmetric_bool")

    assert "crossEntropy truth report - crossEntropy truth truth" in excess
    assert "(hreport : ∀ x, truth x ≠ 0 → 0 < report x)" in identity
    assert "properLogScoreExcessRisk truth report = finiteKL truth report" in identity
    assert "finiteKL asymmetricBoolTruth asymmetricBoolReport ≠" in asymmetric
    assert "finiteKL asymmetricBoolReport asymmetricBoolTruth" in asymmetric
    assert "forwardKL" not in source
    assert "reverseKL" not in source
    assert "vfeGap" not in source
    assert "epistemicValue" not in source


def test_native_mutual_information_garbling_uses_product_pushforward_dpi() -> None:
    source = FOUNDATION.read_text(encoding="utf-8")
    native_information = _declaration(source, "nativeChannelMutualInformation")
    monotonicity = _declaration(
        source, "mutualInformation_mono_under_observationGarbling"
    )

    assert "[IsProbabilityMeasure prior]" in native_information
    assert "[IsMarkovKernel experiment]" in native_information
    assert "InformationTheory.klDiv (prior ⊗ₘ experiment)" in native_information
    assert "prior.prod (experiment ∘ₘ prior)" in native_information
    assert "[IsProbabilityMeasure prior]" in monotonicity
    assert "[IsMarkovKernel experiment]" in monotonicity
    assert "[IsMarkovKernel garbling]" in monotonicity
    assert "Measure.parallelComp_comp_compProd" in monotonicity
    assert "Measure.prod_comp_right" in monotonicity
    assert "InformationTheory.klDiv_comp_right_le" in monotonicity


def test_decision_risk_foundation_compiles_warning_free() -> None:
    result = run_lean_compile_probe(
        FOUNDATION,
        cwd=LEAN_ROOT,
        timeout_s=300,
        executable=lake_executable(),
    )

    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "warning:" not in output.lower()
