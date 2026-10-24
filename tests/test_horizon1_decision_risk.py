"""H1.2 native information and Bayesian decision-risk bridge tests."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from fep_lean.lean_source import lean_code_without_comments
from tests._support.lake import lake_executable
from tests._support.lean_module_contract import assert_exposed_module_header
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

    assert_exposed_module_header(source, EXACT_IMPORTS)
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


def test_relative_support_bridge_and_sparse_information_consumer_compile(
    tmp_path: Path,
) -> None:
    """Sparse, asymmetric informative and independent native controls compile."""
    consumer = tmp_path / "relative_support_information.lean"
    consumer.write_text(
        FOUNDATION.read_text(encoding="utf-8")
        + """
namespace RelativeSupportConsumer
open FEP FEP.FiniteInformation FEP.NativeBlanket FEP.DecisionRisk
open MeasureTheory ProbabilityTheory
open scoped ENNReal

noncomputable def sparseReference : FiniteLaw (Bool × Bool) :=
  (FiniteLaw.uniform : FiniteLaw Bool).map (fun b => (b, b))

example : sparseReference (true, false) = 0 := by
  norm_num [sparseReference, FiniteLaw.map, FiniteLaw.uniform]

theorem actual_supported :
    ∀ xy, (FiniteLaw.pointMass (true, true)) xy ≠ 0 → 0 < sparseReference xy := by
  intro xy hmass
  by_cases hxy : xy = (true, true)
  · subst xy
    norm_num [sparseReference, FiniteLaw.map, FiniteLaw.uniform]
  · simp [FiniteLaw.pointMass, hxy] at hmass

example : InformationTheory.klDiv
    (embeddedLaw (FiniteLaw.pointMass (true, true))) (embeddedLaw sparseReference) =
      ENNReal.ofReal (finiteKL (FiniteLaw.pointMass (true, true)) sparseReference) :=
  weightedDirac_klDiv_eq_finiteKL_of_relativeSupport _ _ actual_supported

example : nativeChannelMutualInformation (embeddedLaw sparseReference)
    (embeddedKernel (FiniteKernel.deterministic Prod.fst)) =
      ENNReal.ofReal (mutualInformation
        ((FiniteKernel.deterministic Prod.fst).joint sparseReference)) :=
  nativeChannelMutualInformation_eq_finite _ _

example : mutualInformation
    ((FiniteKernel.comp (FiniteKernel.deterministic (fun _ : Bool => ()))
      (FiniteKernel.deterministic Prod.fst)).joint sparseReference) ≤
        mutualInformation ((FiniteKernel.deterministic Prod.fst).joint sparseReference) :=
  finiteMutualInformation_mono_under_observationGarbling _ _ _

example : finiteKL
    ((FiniteKernel.deterministic Prod.fst).predictive (FiniteLaw.pointMass (true, true)))
    ((FiniteKernel.deterministic Prod.fst).predictive sparseReference) ≤
      finiteKL (FiniteLaw.pointMass (true, true)) sparseReference :=
  finiteKL_mono_under_channel_of_relativeSupport _ _ _ actual_supported

noncomputable def informativePrior : FiniteLaw Bool where
  mass input := if input then 1 / 6 else 5 / 6
  nonneg input := by cases input <;> norm_num
  sum_one := by rw [Fintype.sum_bool]; norm_num

noncomputable def informativeExperiment : FiniteKernel Bool Bool where
  mass input output := if input then (if output then 0 else 1)
    else (if output then 2 / 5 else 3 / 5)
  nonneg input output := by cases input <;> cases output <;> norm_num
  sum_one input := by cases input <;> rw [Fintype.sum_bool] <;> norm_num

noncomputable def informativeJoint : FiniteLaw (Bool × Bool) :=
  informativeExperiment.joint informativePrior

-- These ordered atoms distinguish parameter/observation exchange.
example : informativeJoint (false, true) = 1 / 3 ∧
    informativeJoint (true, false) = 1 / 6 ∧
    informativeJoint (true, true) = 0 := by
  norm_num [informativeJoint, FiniteKernel.joint, informativePrior,
    informativeExperiment]

example : informativeJoint (false, true) ≠ informativeJoint (true, false) := by
  norm_num [informativeJoint, FiniteKernel.joint, informativePrior,
    informativeExperiment]

example : informativeJoint.fstMarginal false = 5 / 6 ∧
    informativeJoint.sndMarginal false = 2 / 3 := by
  norm_num [FiniteLaw.fstMarginal, FiniteLaw.sndMarginal, Fintype.sum_bool,
    informativeJoint, FiniteKernel.joint, informativePrior, informativeExperiment]

example : embeddedLaw informativeJoint =
    embeddedLaw informativePrior ⊗ₘ embeddedKernel informativeExperiment :=
  embeddedLaw_joint_eq_compProd _ _

example : embeddedLaw informativeJoint {(false, true)} = ENNReal.ofReal (1 / 3) ∧
    embeddedLaw informativeJoint {(true, false)} = ENNReal.ofReal (1 / 6) := by
  simp only [embeddedLaw_apply_singleton]
  norm_num [informativeJoint, FiniteKernel.joint, informativePrior,
    informativeExperiment]

example : InformationTheory.klDiv (embeddedLaw informativeJoint)
    ((embeddedLaw informativeJoint.fstMarginal).prod
      (embeddedLaw informativeJoint.sndMarginal)) =
        ENNReal.ofReal (mutualInformation informativeJoint) :=
  embeddedJoint_klDiv_eq_mutualInformation _

theorem informative_information_pos : 0 < mutualInformation informativeJoint := by
  have hne : mutualInformation informativeJoint ≠ 0 := by
    intro hzero
    have hproduct := (mutualInformation_eq_zero_iff informativeJoint).mp hzero
    have hatom := congrArg (fun p : FiniteLaw (Bool × Bool) => p (true, true)) hproduct
    norm_num [informativeJoint, FiniteKernel.joint, informativePrior,
      informativeExperiment, FiniteLaw.product, FiniteLaw.fstMarginal,
      FiniteLaw.sndMarginal, Fintype.sum_bool] at hatom
  exact lt_of_le_of_ne (mutualInformation_nonneg _) (Ne.symm hne)

theorem informative_native_information_pos :
    0 < nativeChannelMutualInformation (embeddedLaw informativePrior)
      (embeddedKernel informativeExperiment) := by
  rw [nativeChannelMutualInformation_eq_finite]
  exact ENNReal.ofReal_pos.mpr informative_information_pos

def erasure : FiniteKernel Bool Bool :=
  FiniteKernel.deterministic (fun _ => false)

noncomputable def independentJoint : FiniteLaw (Bool × Bool) :=
  erasure.joint informativePrior

theorem independent_joint_product :
    independentJoint = informativePrior.product (FiniteLaw.pointMass false) := by
  apply FiniteLaw.ext_mass
  rfl

-- Both the actual joint and the product reference have unused atoms.
example : independentJoint (true, true) = 0 ∧
    (independentJoint.fstMarginal.product independentJoint.sndMarginal)
      (true, true) = 0 := by
  simp only [independent_joint_product, FiniteLaw.product_fstMarginal,
    FiniteLaw.product_sndMarginal]
  norm_num [FiniteLaw.product, FiniteLaw.pointMass, informativePrior]

theorem independent_native_joint_zero :
    InformationTheory.klDiv (embeddedLaw independentJoint)
      ((embeddedLaw independentJoint.fstMarginal).prod
        (embeddedLaw independentJoint.sndMarginal)) = 0 := by
  rw [embeddedJoint_klDiv_eq_mutualInformation, independent_joint_product,
    mutualInformation_product_eq_zero]
  simp

theorem independent_native_channel_zero :
    nativeChannelMutualInformation (embeddedLaw informativePrior)
      (embeddedKernel erasure) = 0 := by
  rw [nativeChannelMutualInformation_eq_finite]
  change ENNReal.ofReal (mutualInformation independentJoint) = 0
  rw [independent_joint_product, mutualInformation_product_eq_zero]
  simp

example : nativeChannelMutualInformation (embeddedLaw informativePrior)
    (embeddedKernel erasure ∘ₖ embeddedKernel informativeExperiment) ≤
      nativeChannelMutualInformation (embeddedLaw informativePrior)
        (embeddedKernel informativeExperiment) :=
  mutualInformation_mono_under_observationGarbling _ _ _

example : mutualInformation
    ((FiniteKernel.comp erasure informativeExperiment).joint informativePrior) ≤
      mutualInformation informativeJoint :=
  finiteMutualInformation_mono_under_observationGarbling _ _ _

example : InformationTheory.klDiv
    (embeddedLaw (FiniteLaw.pointMass true)) (embeddedLaw (FiniteLaw.pointMass false)) = ∞ :=
  boolPointMass_klDiv_eq_top
example : finiteKL (FiniteLaw.pointMass true) (FiniteLaw.pointMass false) = 1 :=
  finiteKL_disjoint_pointMass_totalized
end RelativeSupportConsumer
#print axioms RelativeSupportConsumer.informative_information_pos
#print axioms RelativeSupportConsumer.informative_native_information_pos
#print axioms RelativeSupportConsumer.independent_native_joint_zero
#print axioms RelativeSupportConsumer.independent_native_channel_zero
""",
        encoding="utf-8",
    )
    result = run_lean_compile_probe(
        consumer,
        cwd=LEAN_ROOT,
        timeout_s=300,
        executable=lake_executable(),
    )
    consumer.with_suffix(".stdout.txt").write_text(result.stdout, encoding="utf-8")
    consumer.with_suffix(".stderr.txt").write_text(result.stderr, encoding="utf-8")
    consumer.with_suffix(".command.json").write_text(
        json.dumps(
            {
                "argv": result.args,
                "cwd": str(LEAN_ROOT),
                "timeout_sec": 300,
                "returncode": result.returncode,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "warning:" not in output.lower()
    assert "sorryAx" not in output


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


@pytest.mark.parametrize(
    ("source_name", "expected_axiom_targets"),
    [
        (
            "ConsumerControls.lean",
            (
                "FEP.FiniteInformation.finiteWeightMeasure_withDensity_ratio",
                "FEP.FiniteInformation.finiteWeightMeasure_probability",
                "FiniteWeightKLControls.sparse_shared_zero_control",
                "FiniteWeightKLControls.sparse_normalization_control",
                "FiniteWeightKLControls.singular_infinity_control",
                "FiniteWeightKLControls.singular_relative_support_rejected",
                "FiniteWeightKLControls.unnormalized_mass_correction_control",
                "FiniteWeightKLControls.unequal_mass_not_normalized_control",
                "FiniteWeightKLControls.mass_correction_not_uncorrected_score",
                "FiniteWeightKLControls.normalized_positive_nontrivial_control",
                "ExistingFiniteKLConsumer.embedding_defeq",
                "FEP.FiniteInformation.klDiv_finiteWeightMeasure",
                "FEP.DecisionRisk.embeddedLaw_withDensity_ratio_of_relativeSupport",
                "FEP.DecisionRisk.weightedDirac_klDiv_eq_finiteKL_of_relativeSupport",
                "FEP.DecisionRisk.embeddedLaw_withDensity_ratio",
                "FEP.DecisionRisk.weightedDirac_klDiv_eq_finiteKL_of_fullSupport",
            ),
        ),
        (
            "FiniteWeightKL.lean",
            (
                "InformationTheory.klDiv_finiteWeightMeasure",
                "InformationTheory.finiteWeightMeasure_probability",
                "FiniteWeightKLControls.sparse_shared_zero_control",
                "FiniteWeightKLControls.sparse_normalization_control",
                "FiniteWeightKLControls.singular_infinity_control",
                "FiniteWeightKLControls.singular_relative_support_rejected",
                "FiniteWeightKLControls.unnormalized_mass_correction_control",
                "FiniteWeightKLControls.unequal_mass_not_normalized_control",
                "FiniteWeightKLControls.mass_correction_not_uncorrected_score",
                "FiniteWeightKLControls.normalized_positive_nontrivial_control",
            ),
        ),
    ],
)
def test_finite_weight_kl_project_and_standalone_controls(
    source_name: str, expected_axiom_targets: tuple[str, ...], tmp_path: Path
) -> None:
    """Exercise support, mass correction, nonzero KL and existing API consumers."""
    source = PROJECT_ROOT / "specs" / "finite-kl-upstream" / source_name
    if source_name == "FiniteWeightKL.lean":
        code = lean_code_without_comments(source.read_text(encoding="utf-8"))
        imports = [
            name
            for payload in re.findall(
                r"(?m)^[ \t]*(?:public[ \t]+)?(?:meta[ \t]+)?import[ \t]+([^\n]+)", code
            )
            for name in payload.split()
        ]
        assert imports and all(name.startswith("Mathlib.") for name in imports)
        assert not re.search(r"\bFEP(?:\.|\b)", code)
    result = run_lean_compile_probe(
        source, cwd=LEAN_ROOT, timeout_s=300, executable=lake_executable()
    )
    (tmp_path / "stdout.txt").write_text(result.stdout, encoding="utf-8")
    (tmp_path / "stderr.txt").write_text(result.stderr, encoding="utf-8")
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "warning:" not in output.lower(), output
    records = re.findall(r"'([^']+)' depends on axioms: \[([^\]]*)\]", output)
    assert len(records) == len(expected_axiom_targets)
    assert {name for name, _ in records} == set(expected_axiom_targets)
    for _, values in records:
        assert {value.strip() for value in values.split(",") if value.strip()} <= {
            "propext",
            "Classical.choice",
            "Quot.sound",
        }
