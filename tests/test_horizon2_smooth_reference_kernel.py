"""H2.7 connected scalar and separate Fin4 terminal contracts."""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
from pathlib import Path

import pytest

from fep_lean.formal.manifest import FORMAL_MODULES, FormalModuleRole
from fep_lean.lean_source import lean_code_without_comments
from tests._support.h2_r0_custody import validate_h2_r0_custody
from tests._support.lean_runner import run_lean_probe

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEAN_ROOT = PROJECT_ROOT / "lean"
SOURCE = (
    PROJECT_ROOT
    / "src"
    / "fep_lean"
    / "formal"
    / "compositions"
    / "smooth_reference_kernel.lean"
)
PROJECTION = LEAN_ROOT / "FepSketches" / "compositions" / SOURCE.name
AGGREGATE = PROJECT_ROOT / "src" / "fep_lean" / "formal" / "composed.lean"
WORKSPACE_AGGREGATE = LEAN_ROOT / "FepSketches" / "composed.lean"
R0_RECEIPT = (
    PROJECT_ROOT
    / "specs"
    / "horizon-2-smooth-stochastic"
    / "readiness"
    / "repairs"
    / "07-gaussian-vfe-natural-gradient.json"
)

pytestmark = pytest.mark.serial_lean

NAMESPACE = "FEPComposed.SmoothReferenceKernel"
EXACT_IMPORTS = (
    "FepSketches.gaussian_information_geometry",
    "FepSketches.smooth_information_geometry",
    "FepSketches.posterior_convergence",
    "FepSketches.markov_semigroup",
    "FepSketches.scalar_gaussian_semigroup",
    "FepSketches.fin4_gaussian_semigroup",
    "FepSketches.gaussian_precision_conditioning",
    "FepSketches.compositions.gaussian_filter",
    "FepSketches.compositions.gaussian_control",
    "FepSketches.compositions.gaussian_grid_path",
)
PUBLIC_DEFINITIONS = (
    "selectedDynamics",
    "alternativeDynamics",
    "selectedPrior",
    "selectedFilter",
    "selectedControl",
    "selectedUnitGrid",
    "evidenceSurprisal",
    "gaussianVariationalFreeEnergy",
    "meanNaturalGradient",
    "naturalGradientFlow",
)
PUBLIC_THEOREMS = (
    "selectedDynamics_stationaryVariance",
    "selectedStationaryLaw_eq_learningObservationFalse",
    "selectedTransition_eq_gaussianLocation",
    "selectedObservationKernel_eq_learningObservationLaw",
    "selectedPredictionBelief_eq_prior",
    "selectedPosterior_mean",
    "selectedPosterior_variance",
    "evidenceLaw_eq_volume_withDensity",
    "evidenceDensity_ne_top",
    "gaussianVariationalFreeEnergy_eq_meanSquare_add_surprisal",
    "gaussianVariationalFreeEnergy_sub_surprisal_eq_nativeKL",
    "gaussianVariationalFreeEnergy_eq_surprisal_iff",
    "gaussianVariationalFreeEnergy_hasDerivAt",
    "meanNaturalGradient_eq_displacement",
    "meanNaturalGradient_metric_dual",
    "naturalGradientFlow_zero",
    "gaussianVariationalFreeEnergy_naturalGradientFlow_hasDerivAt",
    "gaussianVariationalFreeEnergy_naturalGradientFlow_deriv_neg",
    "continuousGaussianVFE_naturalGradient",
    "selectedControl_false_dynamics",
    "selectedControl_false_risk",
    "selectedControl_true_risk",
    "selectedControl_false_strictlyBetter",
    "selectedControl_selectedAction",
    "selectedControl_actionTransition_eq_selectedTransition",
    "selectedControl_actionTransitions_ne",
    "selectedUnitGrid_stepDuration",
    "selectedUnitGrid_stepKernel",
    "smoothReferenceKernel_terminal",
    "fin4ReferenceKernel_terminal",
)
PUBLIC_ENVIRONMENT = frozenset((*PUBLIC_DEFINITIONS, *PUBLIC_THEOREMS))
ALLOWED_AXIOMS = frozenset({"propext", "Classical.choice", "Quot.sound"})


def _run_lean(source_text: str) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory(prefix="lean_probe_") as temp_dir:
        probe = Path(temp_dir) / "LeanProbe.lean"
        probe.write_text(source_text, encoding="utf-8")
        return run_lean_probe(
            probe,
            import_root=PROJECT_ROOT / "src" / "fep_lean" / "formal",
            cwd=LEAN_ROOT,
            timeout_s=1800,
        )


def _parse_axioms(block: str) -> frozenset[str]:
    return frozenset(
        token.strip().strip("'")
        for token in block.replace("\n", " ").split(",")
        if token.strip().strip("'")
    )


def _axiom_reports(output: str) -> dict[str, frozenset[str]]:
    reports: dict[str, frozenset[str]] = {}
    for name in sorted(PUBLIC_ENVIRONMENT):
        qualified = f"{NAMESPACE}.{name}"
        report = re.search(
            rf"'{re.escape(qualified)}' "
            r"(?:depends on axioms: \[(?P<axioms>.*?)\]"
            r"|does not depend on any axioms)",
            output,
            re.DOTALL,
        )
        assert report is not None, f"missing axiom report for {qualified}\n{output}"
        if report.group("axioms") is None:
            reports[name] = frozenset()
        else:
            parsed = _parse_axioms(report.group("axioms"))
            assert parsed, f"empty axiom report for {qualified}"
            reports[name] = parsed
    return reports


def _typed_terminal_consumers() -> str:
    """Pin both exported types independently of their source proof text."""
    return r"""
open Filter MeasureTheory ProbabilityTheory InformationTheory
open scoped BoundedContinuousFunction ENNReal MeasureTheory NNReal ProbabilityTheory Topology
open FEP.GaussianInformationGeometry FEP.SmoothInformationGeometry
open FEP.PosteriorConvergence FEP.MarkovSemigroup FEP.ScalarGaussianSemigroup
open FEP.Fin4GaussianSemigroup FEP.GaussianPrecisionConditioning
open FEPComposed.GaussianFilter FEPComposed.GaussianControl
open FEPComposed.GaussianGridPath FEPComposed.SmoothReferenceKernel

example (initial : Measure ℝ) [IsFiniteMeasure initial]
    (start elapsed : ℝ≥0) (lastIndex : ℕ)
    (candidate direction : ℝ) (away : candidate ≠ 0)
    (testFunction : BoundedContinuousFunction MeanHypothesis ℝ) :
    (∀ parameter,
      observationKernel selectedFilter (selectedMean parameter) =
        selectedObservationLaw parameter) ∧
    (∀ parameter,
      observationKernel selectedFilter (selectedMean parameter) Set.univ = 1) ∧
    (∀ x, selectedDynamics.ouTransition 1 x =
      (selectedDynamics.positiveTimeGaussian 1 (by norm_num)).law
        (selectedDynamics.transitionMean 1 x)) ∧
    (∀ x, selectedDynamics.ouTransition 1 x Set.univ = 1) ∧
    selectedDynamics.stationaryLaw = selectedObservationLaw false ∧
    InvariantLaw selectedDynamics.ouNativeSemigroup selectedDynamics.stationaryLaw ∧
    predictionBelief selectedFilter selectedPrior = selectedPrior ∧
    closedFormPosteriorKernel selectedFilter selectedPrior =ᵐ[
      evidenceLaw selectedFilter selectedPrior]
      ProbabilityTheory.posterior (observationKernel selectedFilter)
        (predictionBelief selectedFilter selectedPrior).law ∧
    evidenceLaw selectedFilter selectedPrior =
      volume.withDensity (evidenceDensity selectedFilter selectedPrior) ∧
    0 < evidenceDensity selectedFilter selectedPrior 0 ∧
    evidenceDensity selectedFilter selectedPrior 0 ≠ ⊤ ∧
    gaussianVariationalFreeEnergy selectedFilter selectedPrior 0 candidate -
      evidenceSurprisal selectedFilter selectedPrior 0 =
      (klDiv ((posteriorFamily selectedFilter selectedPrior).law candidate)
        (posteriorBelief selectedFilter selectedPrior 0).law).toReal ∧
    (gaussianVariationalFreeEnergy selectedFilter selectedPrior 0 candidate =
        evidenceSurprisal selectedFilter selectedPrior 0 ↔
      candidate = posteriorMean selectedFilter selectedPrior 0) ∧
    meanNaturalGradient selectedFilter selectedPrior 0 candidate =
      candidate - posteriorMean selectedFilter selectedPrior 0 ∧
    meanMetricPairing (posteriorFamily selectedFilter selectedPrior) candidate
      (meanNaturalGradient selectedFilter selectedPrior 0 candidate) direction =
      ((candidate - posteriorMean selectedFilter selectedPrior 0) /
        (posteriorVariance selectedFilter selectedPrior : ℝ)) * direction ∧
    HasDerivAt
      (fun t => gaussianVariationalFreeEnergy selectedFilter selectedPrior 0
        (naturalGradientFlow selectedFilter selectedPrior 0 candidate t))
      (-((candidate - posteriorMean selectedFilter selectedPrior 0) ^ 2 /
        (posteriorVariance selectedFilter selectedPrior : ℝ))) 0 ∧
    -((candidate - posteriorMean selectedFilter selectedPrior 0) ^ 2 /
      (posteriorVariance selectedFilter selectedPrior : ℝ)) < 0 ∧
    (∀ᵐ data ∂selectedJointLaw,
      Tendsto (fun k => posteriorProbability k data) atTop
        (𝓝 (selectedParameterIndicator data))) ∧
    (∀ᵐ data ∂selectedJointLaw,
      Tendsto
        (fun k => ∫ parameter, testFunction parameter
          ∂(parameterPosterior k data : ProbabilityMeasure MeanHypothesis))
        atTop (𝓝 (testFunction data.1))) ∧
    (∀ᵐ data ∂selectedJointLaw,
      Tendsto (fun k => posteriorDecisionRisk k data) atTop (𝓝 0)) ∧
    (∀ action : Bool,
      filteredQuadraticRisk selectedControl selectedFilter selectedPrior 0
        (selectedAction selectedControl selectedFilter selectedPrior 0) ≤
      filteredQuadraticRisk selectedControl selectedFilter selectedPrior 0 action) ∧
    (fun y => selectedAction selectedControl selectedFilter selectedPrior y)
      =ᵐ[evidenceLaw selectedFilter selectedPrior]
      (fun y => nativePosteriorSelectedAction selectedControl selectedFilter selectedPrior y) ∧
    selectedAction selectedControl selectedFilter selectedPrior 0 = false ∧
    actionTransition selectedControl
      (selectedAction selectedControl selectedFilter selectedPrior 0) =
      selectedDynamics.ouTransition 1 ∧
    actionTransition selectedControl false ≠ actionTransition selectedControl true ∧
    ouGridStep selectedDynamics selectedUnitGrid lastIndex =
      (selectedDynamics.ouTransition 1).comap
        (fun path => path ⟨lastIndex, Finset.mem_Iic.mpr le_rfl⟩) (by fun_prop) ∧
    forwardGridLaw selectedDynamics selectedUnitGrid lastIndex Set.univ = 1 ∧
    klDiv (selectedDynamics.ouTransition (start + elapsed) ∘ₘ initial)
        selectedDynamics.stationaryLaw ≤
      klDiv (selectedDynamics.ouTransition start ∘ₘ initial)
        selectedDynamics.stationaryLaw :=
  smoothReferenceKernel_terminal initial start elapsed lastIndex
    candidate direction away testFunction

example :
    Fintype.card Axis = 4 ∧
    K.PosDef ∧
    K * FEP.Fin4GaussianSemigroup.Sigma = 1 ∧
    FEP.Fin4GaussianSemigroup.Sigma * K = 1 ∧
    FEP.Fin4GaussianSemigroup.Sigma.PosDef ∧
    K Axis.external Axis.internal = 0 ∧
    FEP.Fin4GaussianSemigroup.Sigma Axis.external Axis.internal = 1 / 24 ∧
    FEP.Fin4GaussianSemigroup.Sigma Axis.external Axis.internal ≠ 0 ∧
    (∀ μ : StandardizedState,
      stationaryLaw μ = multivariateGaussian μ FEP.Fin4GaussianSemigroup.Sigma) ∧
    (∀ μ : StandardizedState,
      InvariantLaw (nativeSemigroup μ) (stationaryLaw μ)) ∧
    (∀ μ x : StandardizedState,
      Tendsto (fun t : ℝ≥0 => transitionProbability μ t x)
        atTop (𝓝 (stationaryProbability μ))) ∧
    (∀ μ : ℝ,
      (scalarParameters μ).rate = 2 ∧
      (scalarParameters μ).diffusionVarianceRate = 2) ∧
    (∀ (μ : ℝ) (t : ℝ≥0),
      projectedTransition μ t = (scalarParameters μ).ouTransition t) ∧
    (∀ μ : StandardizedState,
      condDistrib endpointCoordinates blanketCoordinates (stationaryLaw μ)
        =ᵐ[blanketLaw μ] endpointConditionalKernel μ) ∧
    (∀ μ : StandardizedState,
      K Axis.external Axis.internal = 0 ∧
      cov[fun x : StandardizedState => x Axis.external,
        fun x => x Axis.internal; stationaryLaw μ] = 1 / 24 ∧
      cov[fun x : StandardizedState => x Axis.external,
        fun x => x Axis.internal; stationaryLaw μ] ≠ 0 ∧
      ((fun x : StandardizedState => x Axis.external) ⟂ᵢ[
        blanketCoordinates, measurable_blanketCoordinates; stationaryLaw μ]
        (fun x => x Axis.internal))) ∧
    ¬ IndepFun perturbedExternal perturbedInternal perturbedEndpointLaw :=
  fin4ReferenceKernel_terminal
"""


def test_h2_7_owns_one_terminal_composition_leaf() -> None:
    assert SOURCE.is_file()
    source = SOURCE.read_text(encoding="utf-8")
    assert tuple(re.findall(r"(?m)^import (\S+)$", source)) == EXACT_IMPORTS
    assert f"namespace {NAMESPACE}\n" in source
    assert source.rstrip().endswith(f"end {NAMESPACE}")


def test_h2_7_public_surface_is_exact_and_has_no_stored_certificate() -> None:
    source = lean_code_without_comments(SOURCE.read_text(encoding="utf-8"))
    definitions = tuple(
        re.findall(r"(?m)^(?:noncomputable )?def ([A-Za-z_][A-Za-z0-9_']*)\b", source)
    )
    theorems = tuple(re.findall(r"(?m)^theorem ([A-Za-z_][A-Za-z0-9_']*)\b", source))
    assert definitions == PUBLIC_DEFINITIONS
    assert theorems == PUBLIC_THEOREMS
    assert not re.search(
        r"(?m)^(?:@\[[^\n]*\]\s*)*(?:private|protected|local)\s+"
        r"(?:noncomputable\s+)?(?:def|theorem|lemma|structure|class|abbrev|instance)\b",
        source,
    )
    assert not re.search(
        r"(?m)^(?:@\[[^\n]*\]\s*)*(?:structure|class|abbrev|lemma|instance)\b",
        source,
    )
    assert not re.search(
        r"\b(?:sorry|admit|axiom|opaque)\b|unsafe\s+(?:def|theorem)|:\s*True\b",
        source,
    )


def test_h2_7_scalar_carrier_bridges_are_source_visible_and_fail_closed() -> None:
    source = lean_code_without_comments(SOURCE.read_text(encoding="utf-8"))
    assert "rate := 1" in source
    assert "diffusionVarianceRate := 2" in source
    assert "dynamics := selectedDynamics" in source
    assert "observationNoise := selectedGaussianFamily" in source
    assert "if action then alternativeDynamics else selectedDynamics" in source
    assert re.search(
        r"klDiv\s+\(\(posteriorFamily model prior\)\.law recognitionMean\)\s+"
        r"\(\(posteriorBelief model prior observation\)\.law\)",
        source,
    )
    assert "selectedObservationKernel_eq_learningObservationLaw" in source
    assert "selectedControl_actionTransition_eq_selectedTransition" in source
    assert "selectedUnitGrid_stepKernel" in source
    assert "posteriorProbability_consistent_ae" in source
    assert "posteriorDecisionRisk_tendsto_zero_ae" in source
    assert "ouKL_to_stationary_nonincrease" in source
    assert "endpointCondDistrib_ae_eq_product" in source
    assert "precisionZero_covarianceNonzero_condIndep" in source
    assert "perturbedEndpoint_external_not_indep_internal" in source
    assert "FEPProbe" not in source
    assert not re.search(
        r"\b(?:FiniteLaw|GenerativeModel|expectedFreeEnergy|reward|"
        r"HamiltonJacobi|FokkerPlanck|Girsanov|SDE|Ito)\b",
        source,
    )


def test_h2_7_compiles_warning_free() -> None:
    result = run_lean_probe(
        SOURCE,
        import_root=PROJECT_ROOT / "src" / "fep_lean" / "formal",
        cwd=LEAN_ROOT,
        timeout_s=1800,
    )
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert output == ""


def test_h2_7_environment_and_all_theorems_use_only_standard_axioms() -> None:
    suffix = "\n" + _typed_terminal_consumers() + "\n"
    # Lean v4.34.0 core no longer accepts `#print prefix <namespace>`; the
    # roster check emits one `#print axioms` per PUBLIC_ENVIRONMENT member.
    # A missing declaration fails its own report, so the roster stays
    # fail-closed; the axiom-report format quotes fully qualified names
    # regardless of the consumers' `open` statements.
    suffix += (
        "\n"
        + "\n".join(
            f"#print axioms {NAMESPACE}.{name}" for name in sorted(PUBLIC_ENVIRONMENT)
        )
        + "\n"
    )
    result = _run_lean(SOURCE.read_text(encoding="utf-8") + suffix)
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "warning:" not in output
    assert "sorryAx" not in output
    reports = _axiom_reports(output)
    assert set(reports) == set(PUBLIC_ENVIRONMENT)
    assert all(axioms <= ALLOWED_AXIOMS for axioms in reports.values())


def test_h2_7_typed_terminal_rejects_a_different_transition_carrier() -> None:
    consumers = _typed_terminal_consumers()
    connected_transition = (
        "actionTransition selectedControl\n"
        "      (selectedAction selectedControl selectedFilter selectedPrior 0) =\n"
        "      selectedDynamics.ouTransition 1"
    )
    assert consumers.count(connected_transition) == 1
    mutated = consumers.replace(
        connected_transition,
        connected_transition.replace("selectedDynamics", "alternativeDynamics"),
        1,
    )
    result = _run_lean(SOURCE.read_text(encoding="utf-8") + "\n" + mutated)
    output = result.stdout + result.stderr
    assert result.returncode != 0, "a different OU carrier satisfied the terminal type"
    assert "expected to have type" in output or "type mismatch" in output.lower()
    assert "alternativeDynamics" in output
    assert "warning:" not in output
    assert "sorryAx" not in output


def test_h2_7_is_manifested_projected_and_aggregated_exactly_once() -> None:
    owners = [
        module
        for module in FORMAL_MODULES
        if module.resource == "compositions/smooth_reference_kernel.lean"
    ]
    assert len(owners) == 1
    owner = owners[0]
    assert owner.lean_module == "FepSketches.compositions.smooth_reference_kernel"
    assert owner.role is FormalModuleRole.COMPOSITION
    assert owner.declaration_namespace == NAMESPACE
    assert PROJECTION.read_bytes() == SOURCE.read_bytes()
    expected_import = "import FepSketches.compositions.smooth_reference_kernel"
    assert (
        AGGREGATE.read_text(encoding="utf-8").splitlines().count(expected_import) == 1
    )
    assert WORKSPACE_AGGREGATE.read_bytes() == AGGREGATE.read_bytes()


def test_h2_7_consumes_only_an_accepted_source_bound_r0_decision() -> None:
    successor = validate_h2_r0_custody(PROJECT_ROOT)
    assert successor["decision"] == "preserve_accepted_R0"
    receipt = json.loads(R0_RECEIPT.read_text(encoding="utf-8"))
    assert receipt["gate"] == "H2.7-R0"
    assert receipt["decision"] == "go"
    assert receipt["decision_scope"] == "open_H2.7_implementation_only"
    assert receipt["review"] == {
        **receipt["review"],
        "independent_lean_api": "approved_no_api_or_proof_blocker",
        "independent_information_geometry": "approved_no_scientific_blocker",
        "independent_skeptical_claim_scope": "approved_fail_closed_source_bound_contract",
    }
    assert receipt["downstream"]["opened"] == ["H2.7 maintained implementation"]
    assert receipt["downstream"]["remains_closed"] == [
        "H3.G0 pending accepted H2.7 terminal certificate",
        "all H3 implementation",
    ]
