"""Native H3 composition seams and deterministic finite-experiment controls."""

from __future__ import annotations

import re
from fractions import Fraction
from pathlib import Path

import pytest
import yaml

from fep_formal.lean_source import lean_code_without_comments
from tests._support.lake import lake_executable
from tests._support.lean_runner import run_lean_compile_probe

ROOT = Path(__file__).resolve().parents[1]
COMPOSITION = ROOT / "src/fep_formal/formal/compositions/h3_case_study.lean"
PROJECTION = ROOT / "lean/FepSketches/compositions/h3_case_study.lean"
ALLOWED_AXIOMS = {"propext", "Classical.choice", "Quot.sound"}


def test_h3_composition_import_ownership_and_exact_projection() -> None:
    code = lean_code_without_comments(COMPOSITION.read_text())
    assert code.startswith("module\n")
    assert "\n@[expose] public section\n" in code
    imports = re.findall(r"(?m)^public import (FepSketches\.\S+)$", code)
    assert imports == [
        "FepSketches.h3_reference_model",
        "FepSketches.markov_blanket",
        "FepSketches.native_blanket",
        "FepSketches.causal_dynamics",
        "FepSketches.compositions.finite_scientific_implications",
        "FepSketches.compositions.smooth_reference_kernel",
        "FepSketches.compositions.gaussian_filter",
        "FepSketches.compositions.gaussian_control",
        "FepSketches.compositions.gaussian_grid_path",
        "FepSketches.compositions.finite_policy_action",
        "FepSketches.path_thermodynamics",
    ]
    assert "namespace FEPComposed.H3CaseStudy\n" in code
    assert code.rstrip().endswith("end FEPComposed.H3CaseStudy")
    assert not re.search(r"\b(?:sorry|admit|axiom|opaque)\b|unsafe\s+", code)
    assert COMPOSITION.read_bytes() == PROJECTION.read_bytes()


@pytest.mark.serial_lean
def test_native_h3_finite_observation_seams_and_failure_controls(
    tmp_path: Path,
) -> None:
    source = COMPOSITION.read_text()
    code = lean_code_without_comments(source)
    names = re.findall(r"(?<!private )\btheorem\s+([A-Za-z_][A-Za-z0-9_]*)", code)
    assert len(names) == len(set(names))
    prints = "\n".join(
        f"#print axioms FEPComposed.H3CaseStudy.{name}" for name in names
    )
    consumers = r"""
open MeasureTheory ProbabilityTheory
open scoped ENNReal ProbabilityTheory
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
