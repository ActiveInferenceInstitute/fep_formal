"""Static H2.3 selected Gaussian posterior-convergence contracts."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from tests._support.lake import lake_executable
from tests._support.lean_runner import run_lean_compile_probe

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE = PROJECT_ROOT / "src" / "fep_lean" / "formal" / "posterior_convergence.lean"
FORMAL_ROOT = SOURCE.parent
LEAN_ROOT = PROJECT_ROOT / "lean"
EXACT_IMPORTS = (
    "FepSketches.gaussian_information_geometry",
    "FepSketches.finite_posterior_learning",
    "FepSketches.measure_bayes",
    "Mathlib.MeasureTheory.Function.ConditionalExpectation.Basic",
    "Mathlib.Probability.Independence.InfinitePi",
    "Mathlib.Probability.Kernel.Composition.Lemmas",
    "Mathlib.Probability.Kernel.CondDistrib",
    "Mathlib.Probability.Martingale.Convergence",
    "Mathlib.Probability.Process.Adapted",
    "Mathlib.Probability.StrongLaw",
)
PUBLIC_CARRIERS = (
    "MeanHypothesis",
    "GaussianObservation",
    "GaussianTrajectory",
    "GaussianSample",
    "GaussianPrefix",
)
H2_3A_PUBLIC_DEFINITIONS = (
    "selectedGaussianFamily",
    "selectedMean",
    "selectedObservationLaw",
    "selectedObservationKernel",
    "selectedMeanPrior",
    "selectedTrajectoryLaw",
    "selectedTrajectoryKernel",
    "selectedJointLaw",
    "observation",
    "observationPrefix",
    "finiteObservationLaw",
    "finiteObservationKernel",
    "finitePosteriorKernel",
    "observationFiltration",
    "selectedParameterIndicator",
    "posteriorProbability",
    "posteriorLimit",
)
H2_3B_PUBLIC_DEFINITIONS = (
    "parameterPosterior",
    "trueParameterLaw",
    "posteriorDecisionRisk",
    "nonidentifiableObservationKernel",
    "nonidentifiablePosteriorKernel",
)
PUBLIC_DEFINITIONS = H2_3A_PUBLIC_DEFINITIONS + H2_3B_PUBLIC_DEFINITIONS
H2_3A_PUBLIC_INSTANCES = (
    "selectedObservationLaw_isProbabilityMeasure",
    "selectedObservationKernel_isMarkovKernel",
    "selectedMeanPrior_isProbabilityMeasure",
    "selectedTrajectoryLaw_isProbabilityMeasure",
    "selectedTrajectoryKernel_isMarkovKernel",
    "selectedJointLaw_isProbabilityMeasure",
    "finiteObservationLaw_isProbabilityMeasure",
    "finiteObservationKernel_isMarkovKernel",
    "finitePosteriorKernel_isMarkovKernel",
)
H2_3B_PUBLIC_INSTANCES = (
    "nonidentifiableObservationKernel_isMarkovKernel",
    "nonidentifiablePosteriorKernel_isMarkovKernel",
)
PUBLIC_INSTANCES = H2_3A_PUBLIC_INSTANCES + H2_3B_PUBLIC_INSTANCES
H2_3A_PUBLIC_THEOREMS = (
    "selectedMeans_ne",
    "selectedObservationKernel_apply",
    "selectedTrajectoryCoordinate_map",
    "finiteObservationLaw_eq_pi",
    "finiteObservationKernel_apply",
    "selectedJointLaw_map_parameterPrefix",
    "observationFiltration_eq_comapPrefix",
    "posteriorProbability_ae_eq_condExp",
    "posteriorProbability_stronglyAdapted",
    "posteriorProbability_integrable",
    "posteriorProbability_mem_Icc",
    "posteriorProbability_martingale",
    "posteriorProbability_tendsto_ae",
    "finitePosterior_eventualContraction_regression",
)
H2_3B_PUBLIC_THEOREMS = (
    "selectedObservationLaws_ne",
    "selectedMeanPrior_positive",
    "selectedMeanPrior_true_pos",
    "limitingObservation_identifies_parameter",
    "posteriorProbability_consistent_ae",
    "posteriorProbability_consistent_under_selectedTrajectoryLaw",
    "parameterPosterior_tendsto_dirac_ae",
    "boundedContinuousPosteriorExpectation_tendsto_ae",
    "posteriorDecisionRisk_mem_Icc",
    "posteriorDecisionRisk_tendsto_zero_ae",
    "nonidentifiableObservationKernel_apply",
    "nonidentifiablePosterior_eq_prior_ae",
)
PUBLIC_THEOREMS = H2_3A_PUBLIC_THEOREMS + H2_3B_PUBLIC_THEOREMS
STANDARD_AXIOMS = {"propext", "Classical.choice", "Quot.sound"}
DECLARATION_NAMESPACE = "FEP.PosteriorConvergence"
PUBLIC_ENVIRONMENT_DECLARATIONS = frozenset(
    (*PUBLIC_CARRIERS, *PUBLIC_DEFINITIONS, *PUBLIC_INSTANCES, *PUBLIC_THEOREMS)
)


def _declaration(source: str, name: str) -> str:
    match = re.search(
        rf"(?m)^(?:private\s+)?(?:noncomputable\s+)?"
        rf"(?:theorem|lemma|abbrev|def|instance)\s+{re.escape(name)}\b"
        rf"(?P<body>.*?)(?=\n(?:private\s+)?(?:noncomputable\s+)?"
        rf"(?:theorem|lemma|abbrev|def|instance|end)\b|\Z)",
        source,
        flags=re.DOTALL,
    )
    assert match is not None, f"missing declaration {name}"
    return match.group(0)


def _parse_axiom_names(block: str) -> set[str]:
    axioms = {
        token.strip().strip("'")
        for token in block.split(",")
        if token.strip().strip("'")
    }
    assert axioms, "axiom dependency block must be nonempty"
    return axioms


def _assert_axiom_reports(output: str, qualified_names: tuple[str, ...]) -> None:
    for full_name in qualified_names:
        escaped_name = re.escape(full_name)
        dependency_reports = re.findall(
            rf"(?ms)^'{escaped_name}' depends on axioms: \[(?P<axioms>.*?)\]$",
            output,
        )
        no_axiom_reports = re.findall(
            rf"(?m)^'{escaped_name}' does not depend on any axioms$",
            output,
        )
        report_count = len(dependency_reports) + len(no_axiom_reports)
        assert report_count == 1, (
            f"{full_name}: expected one axiom report, saw {report_count}"
        )
        if dependency_reports:
            axioms = _parse_axiom_names(dependency_reports[0])
            forbidden = axioms - STANDARD_AXIOMS
            assert not forbidden, f"{full_name}: forbidden axioms={sorted(forbidden)}"


def _parse_namespace_declaration_names(output: str, namespace: str) -> frozenset[str]:
    qualified_prefix = re.escape(f"{namespace}.")
    return frozenset(
        re.findall(
            rf"(?m)^{qualified_prefix}"
            r"([A-Za-z_][A-Za-z0-9_']*(?:\.[A-Za-z_][A-Za-z0-9_']*)*)",
            output,
        )
    )


def _assert_exact_namespace_declarations(
    output: str, namespace: str, expected: frozenset[str]
) -> None:
    actual = _parse_namespace_declaration_names(output, namespace)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    assert not missing and not extra, f"missing={missing}; extra={extra}"


def _h2_3b_typed_consumers() -> str:
    return r"""
open FEP.PosteriorConvergence
open Filter MeasureTheory ProbabilityTheory
open scoped ENNReal MeasureTheory NNReal ProbabilityTheory Topology

example : selectedObservationLaw false ≠ selectedObservationLaw true :=
  selectedObservationLaws_ne

example (hypothesis : MeanHypothesis) :
    0 < selectedMeanPrior.real {hypothesis} :=
  selectedMeanPrior_positive hypothesis

example : 0 < selectedMeanPrior.real {true} :=
  selectedMeanPrior_true_pos

example : posteriorLimit =ᵐ[selectedJointLaw] selectedParameterIndicator :=
  limitingObservation_identifies_parameter

example :
    ∀ᵐ sample ∂selectedJointLaw,
      Tendsto (fun n => posteriorProbability n sample) atTop
        (𝓝 (selectedParameterIndicator sample)) :=
  posteriorProbability_consistent_ae

example (hypothesis : MeanHypothesis) :
    ∀ᵐ path ∂selectedTrajectoryLaw hypothesis,
      Tendsto (fun n => posteriorProbability n (hypothesis, path)) atTop
        (𝓝 (if hypothesis then 1 else 0)) :=
  posteriorProbability_consistent_under_selectedTrajectoryLaw hypothesis

example :
    ∀ᵐ sample ∂selectedJointLaw,
      Tendsto (fun n => parameterPosterior n sample) atTop
        (𝓝 (trueParameterLaw sample)) :=
  parameterPosterior_tendsto_dirac_ae

example (f : BoundedContinuousFunction MeanHypothesis ℝ) :
    ∀ᵐ sample ∂selectedJointLaw,
      Tendsto
        (fun n => ∫ hypothesis, f hypothesis ∂(parameterPosterior n sample :
          ProbabilityMeasure MeanHypothesis)) atTop
        (𝓝 (f sample.1)) :=
  boundedContinuousPosteriorExpectation_tendsto_ae f

example (n : ℕ) (sample : GaussianSample) :
    posteriorDecisionRisk n sample ∈ Set.Icc (0 : ℝ) (1 / 2) :=
  posteriorDecisionRisk_mem_Icc n sample

example :
    ∀ᵐ sample ∂selectedJointLaw,
      Tendsto (fun n => posteriorDecisionRisk n sample) atTop (𝓝 0) :=
  posteriorDecisionRisk_tendsto_zero_ae

example (hypothesis : MeanHypothesis) :
    nonidentifiableObservationKernel hypothesis =
      selectedObservationLaw false :=
  nonidentifiableObservationKernel_apply hypothesis

example :
    ∀ᵐ observation ∂selectedObservationLaw false,
      nonidentifiablePosteriorKernel observation = selectedMeanPrior :=
  nonidentifiablePosterior_eq_prior_ae
"""


def _has_exact_posterior_bridge_statement(declaration: str) -> bool:
    return (
        re.search(
            r"theorem posteriorProbability_ae_eq_condExp \(n : ℕ\) :\s*"
            r"posteriorProbability n =ᵐ\[selectedJointLaw\]\s*"
            r"selectedJointLaw\[\s*selectedParameterIndicator \| "
            r"observationFiltration n\] := by",
            declaration,
        )
        is not None
    )


def _has_exact_posterior_limit_statement(declaration: str) -> bool:
    return (
        re.search(
            r"theorem posteriorProbability_tendsto_ae :\s*"
            r"∀ᵐ sample ∂selectedJointLaw,\s*"
            r"Tendsto \(fun n => posteriorProbability n sample\) atTop\s*"
            r"\(𝓝 \(posteriorLimit sample\)\) := by",
            declaration,
        )
        is not None
    )


def test_axiom_parser_accepts_lean_4_33_quoted_and_unquoted_names() -> None:
    assert _parse_axiom_names("propext, Classical.choice, Quot.sound") == {
        "propext",
        "Classical.choice",
        "Quot.sound",
    }
    assert _parse_axiom_names("'propext', 'Classical.choice'") == {
        "propext",
        "Classical.choice",
    }
    theorem = "FEP.PosteriorConvergence.selectedObservationLaws_ne"
    _assert_axiom_reports(f"'{theorem}' does not depend on any axioms", (theorem,))


def test_axiom_audit_rejects_an_unquoted_forbidden_axiom() -> None:
    theorem = "FEP.PosteriorConvergence.selectedObservationLaws_ne"
    output = f"'{theorem}' depends on axioms: [propext, Unsafe.forbidden]"

    with pytest.raises(AssertionError, match="Unsafe.forbidden"):
        _assert_axiom_reports(output, (theorem,))
    with pytest.raises(AssertionError, match="must be nonempty"):
        _assert_axiom_reports(f"'{theorem}' depends on axioms: []", (theorem,))
    duplicate = "\n".join(
        (
            f"'{theorem}' does not depend on any axioms",
            f"'{theorem}' does not depend on any axioms",
        )
    )
    with pytest.raises(AssertionError, match="expected one axiom report, saw 2"):
        _assert_axiom_reports(duplicate, (theorem,))


def test_h2_3b_exact_type_consumer_payload_covers_every_required_theorem() -> None:
    consumers = _h2_3b_typed_consumers()

    for theorem in H2_3B_PUBLIC_THEOREMS:
        assert theorem in consumers


@pytest.mark.serial_lean
def test_h2_3_environment_census_rejects_every_public_declaration_form(
    tmp_path: Path,
) -> None:
    probe = tmp_path / "PosteriorConvergenceCensusMutations.lean"
    probe.write_text(
        """import Mathlib

namespace FEP.PosteriorConvergenceCensusMutation

lemma publicLemma : (0 : Nat) = 0 := rfl

protected theorem protectedTheorem : (1 : Nat) = 1 := rfl

@[simp]
theorem attributedTheorem (value : Nat) : value + 0 = value := by simp

@[simp] theorem sameLineTheorem (value : Nat) : 0 + value = value := by simp

end FEP.PosteriorConvergenceCensusMutation

#print prefix FEP.PosteriorConvergenceCensusMutation
""",
        encoding="utf-8",
    )
    result = run_lean_compile_probe(
        probe,
        cwd=LEAN_ROOT,
        import_root=FORMAL_ROOT,
        timeout_s=300,
        executable=lake_executable(
            missing="raise",
            context="H2.3 native validation",
        ),
    )
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    escaped_declarations = frozenset(
        {
            "publicLemma",
            "protectedTheorem",
            "attributedTheorem",
            "sameLineTheorem",
        }
    )
    assert (
        _parse_namespace_declaration_names(
            output, "FEP.PosteriorConvergenceCensusMutation"
        )
        == escaped_declarations
    )
    with pytest.raises(AssertionError) as rejected:
        _assert_exact_namespace_declarations(
            output, "FEP.PosteriorConvergenceCensusMutation", frozenset()
        )
    for name in escaped_declarations:
        assert name in str(rejected.value)


@pytest.mark.serial_lean
def test_h2_3b_typed_consumers_reject_an_extra_theorem_premise(
    tmp_path: Path,
) -> None:
    source = SOURCE.read_text(encoding="utf-8")
    mutated = source.replace(
        "theorem selectedObservationLaws_ne :",
        "theorem selectedObservationLaws_ne (_extra : True) :",
        1,
    )
    assert mutated != source
    probe = tmp_path / "PosteriorConvergenceExtraPremiseMutation.lean"
    probe.write_text(f"{mutated}\n{_h2_3b_typed_consumers()}\n", encoding="utf-8")
    result = run_lean_compile_probe(
        probe,
        cwd=LEAN_ROOT,
        import_root=FORMAL_ROOT,
        timeout_s=300,
        executable=lake_executable(
            missing="raise",
            context="H2.3 native validation",
        ),
    )
    output = result.stdout + result.stderr

    assert result.returncode != 0, output
    assert "selectedObservationLaws_ne" in output
    assert "but is expected to have type" in output


def test_h2_3_source_owner_exists() -> None:
    assert SOURCE.is_file()


def test_h2_3_exact_import_and_namespace_boundary() -> None:
    source = SOURCE.read_text(encoding="utf-8")

    assert tuple(re.findall(r"(?m)^import (\S+)$", source)) == EXACT_IMPORTS
    assert source.count("namespace FEP.PosteriorConvergence\n") == 1
    assert source.rstrip().endswith("end FEP.PosteriorConvergence")


def test_h2_3_exact_carrier_and_definition_surface_preserves_h2_3a_prefix() -> None:
    source = SOURCE.read_text(encoding="utf-8")

    assert tuple(re.findall(r"(?m)^abbrev (\w+)\b", source)) == PUBLIC_CARRIERS
    assert (
        tuple(re.findall(r"(?m)^(?:noncomputable )?def (\w+)\b", source))
        == PUBLIC_DEFINITIONS
    )
    assert PUBLIC_DEFINITIONS[: len(H2_3A_PUBLIC_DEFINITIONS)] == (
        H2_3A_PUBLIC_DEFINITIONS
    )


def test_h2_3_exact_instance_surface_preserves_h2_3a_prefix() -> None:
    source = SOURCE.read_text(encoding="utf-8")

    assert (
        tuple(re.findall(r"(?m)^(?:noncomputable )?instance (\w+)\b", source))
        == PUBLIC_INSTANCES
    )
    assert PUBLIC_INSTANCES[: len(H2_3A_PUBLIC_INSTANCES)] == H2_3A_PUBLIC_INSTANCES


def test_h2_3_exact_public_theorem_roster_preserves_h2_3a_prefix() -> None:
    source = SOURCE.read_text(encoding="utf-8")

    assert tuple(re.findall(r"(?m)^theorem (\w+)\b", source)) == PUBLIC_THEOREMS
    assert PUBLIC_THEOREMS[: len(H2_3A_PUBLIC_THEOREMS)] == H2_3A_PUBLIC_THEOREMS


def test_h2_3b_required_inference_steps_are_separately_named() -> None:
    source = SOURCE.read_text(encoding="utf-8")

    for name in (
        "selectedObservationLaws_ne",
        "selectedMeanPrior_true_pos",
        "limitingObservation_identifies_parameter",
        "posteriorProbability_consistent_ae",
        "parameterPosterior_tendsto_dirac_ae",
        "boundedContinuousPosteriorExpectation_tendsto_ae",
        "posteriorDecisionRisk_mem_Icc",
        "posteriorDecisionRisk_tendsto_zero_ae",
        "nonidentifiableObservationKernel_apply",
        "nonidentifiablePosterior_eq_prior_ae",
    ):
        _declaration(source, name)


def test_h2_3b_distinct_laws_identify_the_limiting_observation() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    distinct = _declaration(source, "selectedObservationLaws_ne")
    identification = _declaration(source, "limitingObservation_identifies_parameter")

    assert "selectedGaussianFamily.law_injective" in distinct
    assert "sampleEmpiricalMean_tendsto_ae" in source
    assert "StronglyMeasurable.limUnder" in source
    assert "posteriorLimit =ᵐ[selectedJointLaw] selectedParameterIndicator" in (
        identification
    )
    assert "condExp_congr_ae" in identification
    assert "condExp_of_stronglyMeasurable" in identification
    assert "Filter.tail" not in source


def test_h2_3b_consistency_includes_each_fixed_truth_law() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    joint = _declaration(source, "posteriorProbability_consistent_ae")
    fixed_truth = _declaration(
        source, "posteriorProbability_consistent_under_selectedTrajectoryLaw"
    )

    assert "posteriorProbability_tendsto_ae" in joint
    assert "limitingObservation_identifies_parameter" in joint
    assert "∀ᵐ path ∂selectedTrajectoryLaw hypothesis" in fixed_truth
    assert "ae_iff_of_countable" in fixed_truth
    assert "selectedMeanPrior_positive hypothesis" in fixed_truth


def test_h2_3b_weak_and_bounded_continuous_transfers_are_native() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    weak = _declaration(source, "parameterPosterior_tendsto_dirac_ae")
    bounded = _declaration(source, "boundedContinuousPosteriorExpectation_tendsto_ae")

    assert "ProbabilityMeasure MeanHypothesis" in _declaration(
        source, "parameterPosterior"
    )
    assert "Measure.dirac sample.1" in _declaration(source, "trueParameterLaw")
    assert "ProbabilityMeasure.tendsto_iff_forall_integral_tendsto.mpr" in weak
    assert "∀ᵐ sample ∂selectedJointLaw" in weak
    assert "BoundedContinuousFunction MeanHypothesis ℝ" in bounded
    assert "ProbabilityMeasure.tendsto_iff_forall_integral_tendsto.mp" in bounded


def test_h2_3b_decision_consequence_is_genuinely_bounded_zero_one_risk() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    risk = _declaration(source, "posteriorDecisionRisk")
    bounded = _declaration(source, "posteriorDecisionRisk_mem_Icc")
    convergence = _declaration(source, "posteriorDecisionRisk_tendsto_zero_ae")

    assert "min (posteriorProbability n sample)" in risk
    assert "(1 - posteriorProbability n sample)" in risk
    assert "Set.Icc (0 : ℝ) (1 / 2)" in bounded
    assert "posteriorProbability_consistent_ae" in convergence
    assert "atTop (𝓝 0)" in convergence


def test_h2_3b_same_law_countermodel_stays_prior_only_evidence_ae() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    kernel = _declaration(source, "nonidentifiableObservationKernel")
    posterior = _declaration(source, "nonidentifiablePosteriorKernel")
    equality = _declaration(source, "nonidentifiablePosterior_eq_prior_ae")

    assert "Kernel.const MeanHypothesis (selectedObservationLaw false)" in kernel
    assert "nonidentifiableObservationKernel†selectedMeanPrior" in posterior
    assert "∀ᵐ observation ∂selectedObservationLaw false" in equality
    assert "nonidentifiablePosteriorKernel observation = selectedMeanPrior" in equality
    assert "ae_eq_posterior_of_compProd_eq" in equality


def test_h2_3b_claim_boundary_excludes_unproved_stronger_modes() -> None:
    source = SOURCE.read_text(encoding="utf-8")

    for forbidden in (
        "InformationTheory",
        "Real.log",
        "Entropy",
        "klDiv",
        "TotalVariation",
        "LevyConvergence",
    ):
        assert forbidden not in source


def test_h2_3a_is_static_parameter_learning_not_latent_state_filtering() -> None:
    source = SOURCE.read_text(encoding="utf-8")

    assert (
        "This module formalizes parameter learning, not latent-state filtering."
        in source
    )
    assert "abbrev MeanHypothesis := Bool" in source
    assert "selectedMeanPrior ⊗ₘ selectedTrajectoryKernel" in _declaration(
        source, "selectedJointLaw"
    )
    assert "(finiteObservationKernel n)†selectedMeanPrior" in _declaration(
        source, "finitePosteriorKernel"
    )
    assert "Set.Iic n → GaussianObservation" in source


def test_h2_3a_native_posterior_bridge_is_joint_law_ae_only() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    bridge = _declaration(source, "posteriorProbability_ae_eq_condExp")
    posterior_joint = _declaration(source, "selectedJointLaw_map_prefixParameter")

    assert "FEP.MeasureBayes.posterior_joint_reconstruction" in posterior_joint
    assert "condDistrib_ae_eq_of_measure_eq_compProd_of_measurable" in source
    assert _has_exact_posterior_bridge_statement(bridge)
    assert "=ᵐ[selectedJointLaw]" in bridge
    assert "ae_of_ae_map" in bridge
    assert "condDistrib_ae_eq_condExp" in bridge
    assert "observationFiltration_eq_comapPrefix" in bridge
    assert "selectedParameterIndicator | observationFiltration n" in bridge


def test_h2_3a_martingale_and_limit_transport_native_results() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    martingale = _declaration(source, "posteriorProbability_martingale")
    convergence = _declaration(source, "posteriorProbability_tendsto_ae")
    limit = _declaration(source, "posteriorLimit")

    assert "martingale_condExp" in martingale
    assert ".congr posteriorProbability_stronglyAdapted" in martingale
    assert "posteriorProbability_ae_eq_condExp" in martingale
    assert _has_exact_posterior_limit_statement(convergence)
    assert "MeasureTheory.tendsto_ae_condExp" in convergence
    assert "Integrable.tendsto_ae_condExp" not in source
    assert "ae_all_iff.2" in convergence
    assert "⨆ n, observationFiltration n" in limit


def test_h2_3a_exact_limit_contract_rejects_hidden_identification_premises() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    bridge = _declaration(source, "posteriorProbability_ae_eq_condExp")
    convergence = _declaration(source, "posteriorProbability_tendsto_ae")

    widened_bridge = bridge.replace(
        "(n : ℕ) :",
        "(n : ℕ) (hIdentifiable : selectedParameterIndicator = 0) :",
        1,
    )
    widened_limit = convergence.replace(
        "posteriorProbability_tendsto_ae :",
        "posteriorProbability_tendsto_ae\n"
        "    (hTailMeasurable : StronglyMeasurable selectedParameterIndicator) :",
        1,
    )

    assert not _has_exact_posterior_bridge_statement(widened_bridge)
    assert not _has_exact_posterior_limit_statement(widened_limit)


def test_h2_3a_preserves_horizon1_contraction_as_regression_only() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    regression = _declaration(source, "finitePosterior_eventualContraction_regression")

    assert "(prior : FEP.FiniteLaw" in regression
    assert "∀ᵐ path ∂FEP.FinitePosteriorLearning.trajectoryLaw" in regression
    assert "∀ᶠ sampleCount in atTop" in regression
    assert (
        "FEP.FinitePosteriorLearning.posteriorBadMass_eventually_contracts"
        in regression
    )
    assert "posteriorProbability" not in regression


def test_h2_3_has_no_assumed_identification_or_convergence_fields() -> None:
    source = SOURCE.read_text(encoding="utf-8")

    assert re.search(r"(?m)^(?:structure|class|axiom|opaque)\b", source) is None
    assert re.search(r"(?m)\b(?:sorry|admit)\b", source) is None


@pytest.mark.serial_lean
def test_h2_3_source_compiles_warning_free(tmp_path: Path) -> None:
    output_path = tmp_path / "posterior_convergence.olean"
    result = run_lean_compile_probe(
        SOURCE,
        cwd=LEAN_ROOT,
        import_root=FORMAL_ROOT,
        output_path=output_path,
        timeout_s=300,
        executable=lake_executable(
            missing="raise",
            context="H2.3 native validation",
        ),
    )
    output = result.stdout + result.stderr

    assert result.returncode == 0, output
    assert output_path.is_file(), output
    assert "warning:" not in output.lower()


@pytest.mark.serial_lean
def test_h2_3_public_environment_axioms_and_h2_3b_exact_types(tmp_path: Path) -> None:
    probe = tmp_path / "PosteriorConvergenceAxioms.lean"
    prints = "\n".join(
        f"#print axioms FEP.PosteriorConvergence.{name}" for name in PUBLIC_THEOREMS
    )
    qualified_theorems = tuple(
        f"{DECLARATION_NAMESPACE}.{name}" for name in PUBLIC_THEOREMS
    )
    probe.write_text(
        f"{SOURCE.read_text(encoding='utf-8')}\n{prints}\n"
        f"#print prefix {DECLARATION_NAMESPACE}\n{_h2_3b_typed_consumers()}\n",
        encoding="utf-8",
    )
    result = run_lean_compile_probe(
        probe,
        cwd=LEAN_ROOT,
        import_root=FORMAL_ROOT,
        timeout_s=300,
        executable=lake_executable(
            missing="raise",
            context="H2.3 native validation",
        ),
    )
    output = result.stdout + result.stderr

    assert result.returncode == 0, output
    assert "sorryAx" not in output
    assert "warning:" not in output.lower()
    _assert_axiom_reports(output, qualified_theorems)
    _assert_exact_namespace_declarations(
        output, DECLARATION_NAMESPACE, PUBLIC_ENVIRONMENT_DECLARATIONS
    )
    assert len(PUBLIC_ENVIRONMENT_DECLARATIONS) == 64
