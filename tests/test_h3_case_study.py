"""Native H3 composition seams and deterministic finite-experiment controls."""

from __future__ import annotations

import re
from fractions import Fraction
from pathlib import Path

import pytest
import yaml

from fep_lean.lean_source import lean_code_without_comments
from tests._support.lake import lake_executable
from tests._support.lean_runner import run_lean_compile_probe

ROOT = Path(__file__).resolve().parents[1]
COMPOSITION = ROOT / "src/fep_lean/formal/compositions/h3_case_study.lean"
PROJECTION = ROOT / "lean/FepSketches/compositions/h3_case_study.lean"
ALLOWED_AXIOMS = {"propext", "Classical.choice", "Quot.sound"}
LEAF_NAMES = (
    "h3_case_study_model_control",
    "h3_case_study_path_information",
    "h3_case_study_cost_feedback",
)
# Exact public theorem inventory preserved from the pre-split source.
PUBLIC_THEOREMS = (
    "measurable_scalarCoordinate",
    "arbitrary_state_projection_native",
    "arbitrary_state_projection",
    "native_blanket",
    "native_recognition",
    "measurable_clampActive",
    "clamp_normalization",
    "clamp_nondescendants",
    "native_posterior",
    "vfe_optimum",
    "scalar_mean_identifiability",
    "prediction_stationary",
    "posterior_parameters",
    "batchCovariance_posDef",
    "measurable_batchObservations",
    "batchDenominator_pos",
    "batchPosteriorVariance_pos",
    "measurable_batchError",
    "batchError_eq",
    "batchError_hasGaussianLaw",
    "batchError_mean",
    "batchError_variance",
    "consistency_mse",
    "consistency_tail",
    "consistency_bound_limit",
    "consistency_limit",
    "batch_innovations_independent",
    "batch_latent_law",
    "finite_likelihood_conjugacy",
    "finite_native_posterior",
    "gaussianSigma_scalar_marginal",
    "hiddenContrast_native_binding",
    "hiddenContrast_norm",
    "hiddenContrast_ne_zero",
    "hiddenContrast_projection",
    "hiddenInitialLaw_projection",
    "hidden_mode_marginal_nonidentifiability",
    "controlDecay_bounds",
    "secondRisk_closedForm",
    "measurable_optimalSecond",
    "optimalSecond_le",
    "policy_attainment",
    "policy_containment",
    "information_native_mutualInformation",
    "sensory_clamped_native_condDistrib",
    "sensory_clamped_conditional_covariance",
    "sensory_clamped_conditional_variances",
    "measurable_projectFullPath",
    "full_native_path_projection",
    "fullPathObservationKernel_native_row",
    "hidden_mode_nonidentifiability",
    "controlledVariance_exact",
    "controlledMean_exact",
    "terminalVariance_pos",
    "efe_native_information",
    "expectedFreeEnergy_closedForm",
    "efe_risk_alignment",
    "efe_risk_ordering",
    "preference_counterexample",
    "policyRisk_eq_nativePosterior",
    "openLoopRisk_closedForm",
    "restricted_class_counterexample",
    "clamp_conditional_covariance",
    "controlled_moment_bound",
    "nonstationary_native_grid",
    "finite_grid_kl",
    "finite_grid_kl_positive",
    "finite_grid_support",
    "singular_grid_infinite_kl",
    "all_zero_grid_kl",
    "constitutive_nonidentification",
    "controlled_native_cost",
    "information_native_marginal",
    "information_native_mean",
    "information_native_covariance",
    "informationCovariance_posDef",
    "informationCovariance_inverse",
    "information_mean_asymmetry",
    "finite_grid_kl_mahalanobis",
    "information_marginal_kl",
    "information_marginal_kl_values",
    "finite_grid_reverse_kl",
    "finite_grid_mutual_support",
    "information_full_marginal_projection",
    "information_native_lyapunov",
    "informationMean_time_entries",
    "informationCovariance_time_entries",
    "information_marginal_kl_at_time",
    "optimalSecond_threshold",
    "feedback_first_risk_symmetry",
    "optimalPolicy_eq_feedback_false",
    "optimalPolicy_first_false",
    "feedback_false_attainment",
)


def test_h3_composition_import_ownership_and_exact_projection() -> None:
    facade = lean_code_without_comments(COMPOSITION.read_text())
    assert re.findall(r"(?m)^public import (FepSketches\.\S+)$", facade) == [
        "FepSketches.compositions." + name for name in LEAF_NAMES
    ]
    assert not re.search(r"\b(?:namespace|def|theorem)\b", facade)
    assert COMPOSITION.read_bytes() == PROJECTION.read_bytes()
    names = []
    for name in LEAF_NAMES:
        path = COMPOSITION.with_name(name + ".lean")
        source = path.read_text()
        code = lean_code_without_comments(source)
        assert code.startswith("module\n")
        assert "\n@[expose] public section\n" in code
        assert "namespace FEPComposed.H3CaseStudy\n" in code
        assert code.rstrip().endswith("end FEPComposed.H3CaseStudy")
        assert not re.search(r"\b(?:sorry|admit|axiom|opaque)\b|unsafe\s+", code)
        assert "set_option maxHeartbeats" not in code
        assert path.read_bytes() == PROJECTION.with_name(path.name).read_bytes()
        names.extend(
            re.findall(r"(?<!private )\btheorem\s+([A-Za-z_][A-Za-z0-9_]*)", code)
        )
    assert tuple(names) == PUBLIC_THEOREMS


@pytest.mark.serial_lean
def test_native_h3_finite_observation_seams_and_failure_controls(
    tmp_path: Path,
) -> None:
    source = COMPOSITION.read_text()
    names = PUBLIC_THEOREMS
    prints = "\n".join(
        f"#print axioms FEPComposed.H3CaseStudy.{name}" for name in names
    )
    consumers = r"""
open MeasureTheory ProbabilityTheory
open scoped ENNReal NNReal ProbabilityTheory
open FEPComposed.H3CaseStudy

-- A full state with a rate-four hidden component remains in the projection theorem.
example (center : ℝ) (time : ℝ≥0) :
    (FEP.Fin4GaussianSemigroup.transition
      (FEP.Fin4GaussianSemigroup.allOnesEmbedding center) time
      (FEP.Fin4GaussianSemigroup.allOnesEmbedding center + hiddenContrast)).map
        FEP.Fin4GaussianSemigroup.allOnesProjection =
      (FEP.H3ReferenceModel.scalarParameters center).ouTransition time
        (FEP.Fin4GaussianSemigroup.allOnesProjection
          (FEP.Fin4GaussianSemigroup.allOnesEmbedding center + hiddenContrast)) :=
  arbitrary_state_projection_native center time _

example : FEP.H3ReferenceModel.K .external .internal = 0 ∧
    FEP.H3ReferenceModel.Sigma .external .internal ≠ 0 := by
  refine ⟨(native_blanket (fun _ => 0)).1, ?_⟩
  rw [FEP.H3ReferenceModel.Sigma_eq_carrier,
    FEP.Fin4GaussianSemigroup.Sigma_external_internal]
  norm_num

-- The prior-only bound is retained uncapped: P_0/(1/2)^2 = 2.
example : batchPosteriorVariance 0 (1/8) / (1/2 : ℝ)^2 = 2 := by
  norm_num [batchPosteriorVariance]

example (center : ℝ) :
    (∫ state, (batchPosteriorMean center (1/8) (batchObservations state) - state 0)^2
      ∂batchSourceLaw 0 center (1/8)) = 1/2 := by
  rw [consistency_mse 0 center (1/8) (by norm_num)]
  norm_num

example (center : ℝ) (epsilon : ℝ) (hEpsilon : 0 < epsilon) :
    Filter.Tendsto (fun n : ℕ => (batchSourceLaw n center (1/4)).real
      {state | epsilon ≤ |batchPosteriorMean center (1/4) (batchObservations state) - state 0|})
      Filter.atTop (nhds 0) := consistency_limit center (1/4) epsilon (by norm_num) hEpsilon

example (center : ℝ) :
    condDistrib (fun state : BatchState 16 => state 0) batchObservations
      (batchSourceLaw 16 center (1/8)) =ᵐ[(batchSourceLaw 16 center (1/8)).map batchObservations]
      batchPosteriorKernel 16 center (1/8) :=
  finite_native_posterior 16 center (1/8) (by norm_num)

-- Positive observation-noise APIs reject the singular R=0 request.
#check_failure (observationFilter 0 0 0 (by norm_num))
#check_failure (fun (model : FEP.H3ReferenceModel.ContinuousReferenceModel) => model.consistency)
#check_failure (fun (model : FEP.H3ReferenceModel.ContinuousReferenceModel) => model.nativePosterior)

-- The normalized hidden mode is nontrivial but completely unobserved.
example : ‖hiddenContrast‖ = 1 := hiddenContrast_norm
example : FEP.Fin4GaussianSemigroup.allOnesProjection hiddenContrast = 0 :=
  hiddenContrast_projection

-- The optimized risk is the actual same full-state controlled-law cost.
example (policy : TwoStepPolicy) : policyRisk (1/8) (by norm_num) policy ≤ controlledBound := by
  rw [← controlled_native_cost policy (1/8) (by norm_num)]
  exact (controlled_moment_bound policy (1/8) (by norm_num)).2.1

example (policy : TwoStepPolicy) :
    (∫ state, ‖state‖ ^ 2 ∂controlSecondLaw policy (1/4) (by norm_num)) ≤
      controlledBound + 2 / 3 :=
  (controlled_moment_bound policy (1/4) (by norm_num)).2.2.2

-- The four fixed action pairs remain inside the primitive measurable policy class.
example : policyRisk (1/8) (by norm_num) (optimalPolicy (1/8) (by norm_num)) ≤
    policyRisk (1/8) (by norm_num) (openLoopPolicy false true) :=
  policy_containment (1/8) (by norm_num) false true

example : policyRisk (1/4) (by norm_num) (openLoopPolicy false true) <
    policyRisk (1/4) (by norm_num) (openLoopPolicy true true) :=
  (restricted_class_counterexample (1/4) (by norm_num)).2.2

-- The frozen numerical first action is bound to native integrated feedback symmetry.
example : (optimalPolicy (1/8) (by norm_num)).first = false :=
  optimalPolicy_first_false (1/8) (by norm_num)

example (policy : TwoStepPolicy) :
    policyRisk (1/4) (by norm_num) (feedbackPolicy false (1/4) (by norm_num)) ≤
      policyRisk (1/4) (by norm_num) policy :=
  feedback_false_attainment (1/4) (by norm_num) policy

example : policyRisk (1/8) (by norm_num) (feedbackPolicy false (1/8) (by norm_num)) =
    policyRisk (1/8) (by norm_num) (feedbackPolicy true (1/8) (by norm_num)) :=
  feedback_first_risk_symmetry (1/8) (by norm_num)

-- Actual native finite-path divergence stays ENNReal across singular controls.
example : InformationTheory.klDiv (studyProjectedLaw repeatedStudyGrid)
    (studyReverseLaw repeatedStudyGrid) = ∞ := singular_grid_infinite_kl

example : InformationTheory.klDiv (studyProjectedLaw allZeroStudyGrid)
    (studyReverseLaw allZeroStudyGrid) = 0 := all_zero_grid_kl

example : 0 < InformationTheory.klDiv (studyProjectedLaw informationGrid)
    (studyReverseLaw informationGrid) := finite_grid_kl_positive

example : informationCovariance.PosDef := informationCovariance_posDef
example : (∫ path, informationCoordinate 0 path ∂studyProjectedLaw informationGrid) = 1 := by
  rw [information_native_mean]
  rfl

example : cov[informationCoordinate 0, informationCoordinate 0;
    studyProjectedLaw informationGrid] = 1/2 := by
  rw [information_native_covariance]
  rfl

-- Degenerate active support retains endpoint dependence after actual surgery.
example (center : FEP.Fin4GaussianSemigroup.StandardizedState) (datum : ℝ) :
    cov[Prod.fst, Prod.snd; sensoryClampedConditionalKernel center (datum, 0)] ≠ 0 := by
  rw [sensory_clamped_conditional_covariance]
  norm_num

#check_failure (show InformationTheory.klDiv (studyProjectedLaw repeatedStudyGrid)
  (studyReverseLaw repeatedStudyGrid) < ∞ from by rw [singular_grid_infinite_kl]; norm_num)
#check_failure (show hiddenContrast = 0 from hiddenContrast_ne_zero)
#check_failure (fun (policy : TwoStepPolicy) => policy.attainment)
"""
    protocol = yaml.safe_load(
        (ROOT / "specs/h3-reference-study/preregistration.yaml").read_text()
    )
    frozen = protocol["synthetic_acceptance"]["fixed_latent_posterior_consistency"][
        "deterministic_fixtures"
    ]
    epsilon = Fraction(frozen["epsilon"])
    fixtures: list[str] = []

    def lean_fraction(value: Fraction) -> str:
        return f"({value.numerator}/{value.denominator} : ℝ)"

    for setting in protocol["synthetic_acceptance"]["settings"]:
        center = Fraction(str(setting["center"]))
        noise = Fraction(str(setting["observation_noise_variance"]))
        for count in frozen["counts"]:
            values = frozen["observation_list"][:count]
            observation_vector = (
                "![" + ",".join(str(value) for value in values) + "]"
                if count
                else "(fun index : Fin 0 => Fin.elim0 index)"
            )
            mean = (2 * noise * center + sum(values)) / (2 * noise + count)
            variance = noise / (2 * noise + count)
            bound = variance / epsilon**2
            fixtures.append(
                f"example : batchPosteriorMean {lean_fraction(center)} {lean_fraction(noise)} "
                f"{observation_vector} = {lean_fraction(mean)} := by "
                "norm_num [batchPosteriorMean, Fin.sum_univ_succ]"
            )
            fixtures.append(
                f"example : batchPosteriorVariance {count} {lean_fraction(noise)} = "
                f"{lean_fraction(variance)} := by norm_num [batchPosteriorVariance]"
            )
            fixtures.append(
                f"example : batchPosteriorVariance {count} {lean_fraction(noise)} / "
                f"{lean_fraction(epsilon)}^2 = {lean_fraction(bound)} := by "
                "norm_num [batchPosteriorVariance]"
            )
    probe = tmp_path / "H3CaseStudyAcceptance.lean"
    probe.write_text(
        source + "\n" + consumers + "\n" + "\n".join(fixtures) + "\n" + prints
    )
    result = run_lean_compile_probe(
        probe,
        cwd=ROOT / "lean",
        import_root=tmp_path,
        output_path=tmp_path / "H3CaseStudyAcceptance.olean",
        timeout_s=1200,
        executable=lake_executable(
            missing="raise", context="H3 composition acceptance"
        ),
    )
    (tmp_path / "H3CaseStudyAcceptance.stdout.txt").write_text(result.stdout)
    (tmp_path / "H3CaseStudyAcceptance.stderr.txt").write_text(result.stderr)
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "warning:" not in output.lower(), output
    assert "sorryAx" not in output
    reports = dict(
        re.findall(
            r"'FEPComposed\.H3CaseStudy\.(\w+)' depends on axioms: \[([^\]]*)\]",
            output,
        )
    )
    no_axioms = set(
        re.findall(
            r"'FEPComposed\.H3CaseStudy\.(\w+)' does not depend on any axioms", output
        )
    )
    assert set(names) == reports.keys() | no_axioms, output
    for axioms in reports.values():
        assert {
            name.strip() for name in axioms.split(",") if name.strip()
        } <= ALLOWED_AXIOMS
