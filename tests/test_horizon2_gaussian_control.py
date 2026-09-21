"""H2.6b filter-consuming finite Gaussian control source contracts."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from fep_lean.formal import formal_projection_pairs, render_formal_aggregate
from fep_lean.formal.manifest import FORMAL_MODULES, FormalModuleRole
from fep_lean.lean_source import lean_code_without_comments
from tests._support.lake import lake_executable
from tests._support.lean_runner import run_lean_compile_probe

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEAN_ROOT = PROJECT_ROOT / "lean"
SOURCE = (
    PROJECT_ROOT
    / "src"
    / "fep_lean"
    / "formal"
    / "compositions"
    / "gaussian_control.lean"
)

EXACT_IMPORTS = (
    "FepSketches.compositions.gaussian_filter",
    "FepSketches.controlled_markov",
    "FepSketches.gaussian_information_geometry",
    "FepSketches.markov_semigroup",
    "FepSketches.scalar_gaussian_semigroup",
    "Mathlib.Probability.Distributions.Gaussian.Real",
    "Mathlib.Probability.Kernel.Posterior",
)
PUBLIC_DEFINITIONS = (
    "actionKernelFamily",
    "actionIndexedSemigroup",
    "actionTransition",
    "controlledMean",
    "controlledVariance",
    "controlledBelief",
    "quadraticTerminalLoss",
    "quadraticActionRisk",
    "filteredQuadraticRisk",
    "nativePosteriorQuadraticRisk",
    "selectedAction",
    "nativePosteriorSelectedAction",
    "boolWitnessPrior",
    "boolWitnessFilter",
    "boolWitnessControl",
    "boolWitnessAction",
    "boolTieControl",
)
PUBLIC_THEOREMS = (
    "controlledVariance_pos",
    "actionTransition_eq_ouTransition",
    "actionTransition_comp_belief",
    "quadraticTerminalLoss_unbounded",
    "quadraticActionRisk_eq_closedForm",
    "quadraticActionRisk_nonneg",
    "filteredQuadraticRisk_ae_eq_nativePosterior",
    "selectedAction_le",
    "nativePosteriorSelectedAction_le",
    "selectedAction_ae_eq_nativePosteriorSelectedAction",
    "selectedAction_eq_of_strict",
    "boolWitness_posterior_mean",
    "boolWitness_posterior_variance",
    "boolWitness_true_risk",
    "boolWitness_false_risk",
    "boolWitness_true_strictlyBetter",
    "boolWitness_selectedAction",
    "boolWitness_actionTransitions_ne",
    "boolTie_false_true_risk_eq",
)

pytestmark = pytest.mark.serial_lean


def test_h2_6b_has_one_exact_composition_source_owner() -> None:
    assert SOURCE.is_file()
    source = SOURCE.read_text(encoding="utf-8")

    assert tuple(re.findall(r"(?m)^import (\S+)$", source)) == EXACT_IMPORTS
    assert "namespace FEPComposed.GaussianControl\n" in source
    assert source.rstrip().endswith("end FEPComposed.GaussianControl")
    assert "namespace FEPProbe" not in source


def test_h2_6b_is_manifested_projected_and_aggregated_once() -> None:
    modules = tuple(
        module
        for module in FORMAL_MODULES
        if module.resource == "compositions/gaussian_control.lean"
    )

    assert len(modules) == 1
    assert modules[0].lean_module == "FepSketches.compositions.gaussian_control"
    assert modules[0].role is FormalModuleRole.COMPOSITION
    assert modules[0].declaration_namespace == "FEPComposed.GaussianControl"

    projection_pairs = dict(formal_projection_pairs(PROJECT_ROOT))
    projection = PROJECT_ROOT / "lean" / "FepSketches" / modules[0].resource
    assert projection_pairs[SOURCE] == projection
    assert projection.read_bytes() == SOURCE.read_bytes()

    aggregate = render_formal_aggregate()
    assert aggregate.count("import FepSketches.compositions.gaussian_control\n") == 1


def test_h2_6b_stores_only_raw_control_inputs() -> None:
    source = lean_code_without_comments(SOURCE.read_text(encoding="utf-8"))
    model = re.search(
        r"structure FiniteGaussianControlModel \(Action : Type\*\) where\n"
        r"(?P<body>.*?)(?=\n\n)",
        source,
        re.DOTALL,
    )

    assert tuple(re.findall(r"(?m)^structure (\w+)", source)) == (
        "FiniteGaussianControlModel",
    )
    assert model is not None
    assert tuple(re.findall(r"(?m)^  (\w+)\s*:", model["body"])) == (
        "dynamics",
        "duration",
        "duration_pos",
        "target",
        "actionPenalty",
    )
    assert "dynamics : Action → ScalarOUParameters" in model["body"]
    assert "duration : ℝ≥0" in model["body"]
    assert "duration_pos : 0 < duration" in model["body"]
    assert "target : ℝ" in model["body"]
    assert "actionPenalty : Action → ℝ≥0" in model["body"]
    assert not re.search(
        r"(?i)posterior|transition|objective|optimizer|argmin", model["body"]
    )


def test_h2_6b_public_surface_is_exact_and_fail_closed() -> None:
    source = lean_code_without_comments(SOURCE.read_text(encoding="utf-8"))

    assert (
        tuple(re.findall(r"(?m)^(?:noncomputable )?def (\w+)\b", source))
        == PUBLIC_DEFINITIONS
    )
    assert tuple(re.findall(r"(?m)^theorem (\w+)\b", source)) == PUBLIC_THEOREMS
    assert not re.search(
        r"\b(?:sorry|admit|axiom|opaque)\b|unsafe\s+(?:def|theorem)|:\s*True\b",
        source,
    )
    assert not re.search(
        r"\b(?:bayesRisk|IsBayesEstimator|PolicyTree|EFE|reward|"
        r"HamiltonJacobiBellman|HJB|InfiniteHorizon)\b",
        source,
    )


def test_h2_6b_reuses_native_filter_transition_and_minimizer_owners() -> None:
    source = lean_code_without_comments(SOURCE.read_text(encoding="utf-8"))

    assert "(control.dynamics action).ouTransition time" in source
    assert "NativeActionIndexedKernelSemigroup ℝ Action" in source
    assert "semigroup action := (control.dynamics action).ouNativeSemigroup" in source
    assert "sampleTime _ := control.duration" in source
    assert "NativeActionIndexedKernelSemigroup.sampledKernel" in source
    assert re.search(
        r"actionTransition control action =\s*"
        r"\(control\.dynamics action\)\.ouTransition control\.duration",
        source,
    )
    assert "model.dynamics" not in source
    assert "posteriorBelief filter prior observation" in source
    assert "closedFormPosterior_ae_eq_native filter prior" in source
    assert re.search(
        r"def selectedAction\b.*?finiteArgmin\s*"
        r"\(filteredQuadraticRisk control filter prior observation\)",
        source,
        re.DOTALL,
    )
    assert re.search(
        r"def nativePosteriorSelectedAction\b.*?finiteArgmin\s*"
        r"\(nativePosteriorQuadraticRisk control filter prior observation\)",
        source,
        re.DOTALL,
    )
    assert source.count("finiteArgmin_le") == 2
    assert "structure ScalarOUParameters" not in source
    assert "structure ScalarGaussianBelief" not in source
    assert "structure ScalarGaussianFilterModel" not in source


def test_h2_6b_objective_is_the_actual_composed_gaussian_integral() -> None:
    source = lean_code_without_comments(SOURCE.read_text(encoding="utf-8"))
    risk = re.search(
        r"def quadraticActionRisk\b(?P<body>.*?)"
        r"(?=\n\n(?:noncomputable )?def filteredQuadraticRisk)",
        source,
        re.DOTALL,
    )

    assert risk is not None
    assert "(state - target) ^ 2" in source
    assert "∫ nextState, quadraticTerminalLoss control.target nextState" in risk["body"]
    assert "∂(actionTransition control action ∘ₘ belief.law)" in risk["body"]
    assert "+\n    (control.actionPenalty action : ℝ)" in risk["body"]
    assert "NNReal.mk" in source
    assert "(control.dynamics action).transitionVariance control.duration" in source
    assert "ouTransition_comp_gaussian" in source
    assert "MemLp id 2 (gaussianReal mean variance)" in source
    assert "integral_quadratic_gaussianReal" in source
    assert re.search(
        r"quadraticActionRisk control belief action =\s*"
        r"\(controlledVariance control belief action : ℝ\) \+\s*"
        r"\(controlledMean control belief action - control\.target\) \^ 2 \+\s*"
        r"\(control\.actionPenalty action : ℝ\)",
        source,
    )
    assert "∃ state : ℝ, bound < quadraticTerminalLoss target state" in source
    assert "FiniteLaw" not in source


def test_h2_6b_native_posterior_and_selector_claims_are_evidence_ae() -> None:
    source = lean_code_without_comments(SOURCE.read_text(encoding="utf-8"))

    assert re.search(
        r"actionTransition control action ∘ₘ\s*"
        r"\(ProbabilityTheory\.posterior \(observationKernel filter\)\s*"
        r"\(predictionBelief filter prior\)\.law\) observation",
        source,
    )
    assert re.search(
        r"filteredQuadraticRisk control filter prior observation action\) =ᵐ\[\s*"
        r"evidenceLaw filter prior\]\s*"
        r"fun observation =>\s*nativePosteriorQuadraticRisk",
        source,
    )
    assert re.search(
        r"selectedAction control filter prior observation\) =ᵐ\[\s*"
        r"evidenceLaw filter prior\]\s*fun observation =>\s*"
        r"nativePosteriorSelectedAction",
        source,
    )
    assert "Filter.eventually_all.2" in source
    assert "∀ᵐ observation ∂evidenceLaw filter prior, ∀ action : Action" in source
    assert "alternative ≠ candidate →" in source
    assert "selectedAction_le control filter prior observation candidate" in source


def test_h2_6b_boolean_witness_is_transition_derived_and_has_a_tie_boundary() -> None:
    source = lean_code_without_comments(SOURCE.read_text(encoding="utf-8"))

    assert re.search(
        r"def boolWitnessPrior\b.*?mean := 0.*?variance := 1 / 2",
        source,
        re.DOTALL,
    )
    assert re.search(
        r"def boolWitnessFilter\b.*?dynamics := boolDynamics 1.*?"
        r"stepDuration := 1.*?variance := 1 / 2",
        source,
        re.DOTALL,
    )
    assert re.search(
        r"def boolWitnessControl\b.*?if action then "
        r"boolDynamics \(1 / 2\).*?else boolDynamics 1.*?"
        r"duration := 1.*?target := 0.*?actionPenalty := fun _ => 0",
        source,
        re.DOTALL,
    )
    assert "posteriorMean boolWitnessFilter boolWitnessPrior 0 = 0" in source
    assert "posteriorVariance boolWitnessFilter boolWitnessPrior = 1 / 4" in source
    assert re.search(r"boolWitnessPrior 0 true =\s*\(1 / 4 : ℝ\)", source)
    assert re.search(
        r"boolWitnessPrior 0 false =\s*"
        r"\(1 / 2 : ℝ\) - \(1 / 4 : ℝ\) \* \(Real\.exp \(-1\)\) \^ 2",
        source,
    )
    assert "boolWitness_true_strictlyBetter" in source
    assert "boolWitnessAction = true" in source
    assert re.search(
        r"actionTransition boolWitnessControl true ≠\s*"
        r"actionTransition boolWitnessControl false",
        source,
    )
    assert "rw [hTransitions]" in source
    assert re.search(
        r"def boolTieControl\b.*?dynamics := fun _ => boolDynamics 1.*?"
        r"actionPenalty := fun _ => 0",
        source,
        re.DOTALL,
    )
    assert re.search(
        r"filteredQuadraticRisk boolTieControl boolWitnessFilter\s*"
        r"boolWitnessPrior 0 false =\s*"
        r"filteredQuadraticRisk boolTieControl boolWitnessFilter\s*"
        r"boolWitnessPrior 0 true",
        source,
    )


def test_h2_6b_compiles_warning_free(tmp_path: Path) -> None:
    output_path = tmp_path / "gaussian_control.olean"
    result = run_lean_compile_probe(
        SOURCE,
        cwd=LEAN_ROOT,
        import_root=PROJECT_ROOT / "src" / "fep_lean" / "formal",
        output_path=output_path,
        timeout_s=300,
        executable=lake_executable(
            missing="raise",
            context="H2.6b native acceptance",
        ),
    )

    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert output_path.is_file(), output
    assert "warning:" not in output.lower()


def test_h2_6b_public_theorems_use_only_standard_axioms(tmp_path: Path) -> None:
    probe = tmp_path / "GaussianControlAxioms.lean"
    source = SOURCE.read_text(encoding="utf-8")
    prints = "\n".join(
        f"#print axioms FEPComposed.GaussianControl.{name}" for name in PUBLIC_THEOREMS
    )
    probe.write_text(f"{source}\n{prints}\n", encoding="utf-8")
    result = run_lean_compile_probe(
        probe,
        cwd=LEAN_ROOT,
        import_root=PROJECT_ROOT / "src" / "fep_lean" / "formal",
        timeout_s=300,
        executable=lake_executable(
            missing="raise",
            context="H2.6b native acceptance",
        ),
    )

    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "sorryAx" not in output
    assert "warning:" not in output.lower()
    for name in PUBLIC_THEOREMS:
        qualified = f"FEPComposed.GaussianControl.{name}"
        name_pattern = rf"(?:'{re.escape(qualified)}'|{re.escape(qualified)})"
        axiom_blocks = re.findall(
            rf"{name_pattern} depends on axioms: \[(.*?)\]",
            output,
            re.DOTALL,
        )
        no_axiom_lines = re.findall(
            rf"{name_pattern} does not depend on any axioms", output
        )
        assert len(axiom_blocks) + len(no_axiom_lines) == 1, qualified
        if no_axiom_lines:
            continue
        axioms = {
            axiom.strip().strip("'")
            for axiom in axiom_blocks[0].replace("\n", " ").split(",")
            if axiom.strip()
        }
        assert axioms
        assert axioms <= {"propext", "Classical.choice", "Quot.sound"}
