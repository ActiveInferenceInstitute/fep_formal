"""H1.8 finite reference-agent shared-carrier terminal contracts."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

from tests._support.lake import lake_executable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FORMAL_ROOT = PROJECT_ROOT / "src" / "fep_lean" / "formal"
LEAN_ROOT = PROJECT_ROOT / "lean"
COMPOSITION = FORMAL_ROOT / "compositions" / "finite_reference_agent.lean"

pytestmark = pytest.mark.serial_lean

EXACT_IMPORTS = (
    "FepSketches.finite_posterior_learning",
    "FepSketches.compositions.finite_policy_action",
    "FepSketches.compositions.finite_scientific_implications",
    "FepSketches.native_blanket",
    "FepSketches.continuous_time_markov",
)

PUBLIC_THEOREMS = (
    "learnedPosterior_ne_boolBeliefInterpret",
    "boolPolicyState_not_equiv_boolBlanketState",
    "finiteReferenceCoherence_uninhabited",
    "retainedFiniteReference_predecessors",
    "finiteReferenceAgent_terminal",
)


def _without_lean_comments(source: str) -> str:
    """Remove nested block comments and line comments from Lean source."""
    result: list[str] = []
    index = 0
    depth = 0
    while index < len(source):
        if source.startswith("/-", index):
            depth += 1
            index += 2
        elif depth and source.startswith("-/", index):
            depth -= 1
            index += 2
        elif depth:
            index += 1
        elif source.startswith("--", index):
            newline = source.find("\n", index)
            index = len(source) if newline == -1 else newline
        else:
            result.append(source[index])
            index += 1
    return "".join(result)


def _declaration(source: str, kind: str, name: str) -> str:
    uncommented = _without_lean_comments(source)
    match = re.search(
        rf"(?m)^{kind}\s+{re.escape(name)}\b"
        rf"(?P<body>.*?)(?=\n(?:structure|theorem|lemma|def|noncomputable def|end)\b|\Z)",
        uncommented,
        flags=re.DOTALL,
    )
    assert match is not None, f"missing {kind} {name}"
    return match.group(0)


def test_finite_reference_agent_owns_exact_import_and_namespace_contract() -> None:
    source = COMPOSITION.read_text(encoding="utf-8")

    assert tuple(re.findall(r"(?m)^import (\S+)$", source)) == EXACT_IMPORTS
    assert "namespace FEPComposed.FiniteReferenceAgent\n" in source
    assert source.rstrip().endswith("end FEPComposed.FiniteReferenceAgent")
    assert not re.search(
        r"\b(?:sorry|admit|axiom|opaque)\b|unsafe\s+(?:def|theorem)|:\s*True\b",
        source,
    )


def test_one_coherence_record_is_explicitly_uninhabited_by_current_carriers() -> None:
    source = COMPOSITION.read_text(encoding="utf-8")
    uncommented = _without_lean_comments(source)
    coherence = _declaration(source, "structure", "FiniteReferenceCoherence")
    posterior_blocker = _declaration(
        source, "theorem", "learnedPosterior_ne_boolBeliefInterpret"
    )
    carrier_blocker = _declaration(
        source, "theorem", "boolPolicyState_not_equiv_boolBlanketState"
    )
    uninhabited = _declaration(
        source, "theorem", "finiteReferenceCoherence_uninhabited"
    )

    assert tuple(re.findall(r"(?m)^structure (\w+)", uncommented)) == (
        "FiniteReferenceCoherence",
    )
    assert "feedbackObservation : Bool" in coherence
    assert "posteriorAfter selectedPrior (fun _ => true) 2" in coherence
    assert "boolBeliefInterpret" in coherence
    assert "boolFeedbackModel.update false false feedbackObservation" in coherence
    assert "stateCarrierEquiv :" in coherence
    assert "Bool ≃" in coherence
    assert "FEP.MarkovBlanket.DynamicState Bool Bool Bool Bool" in coherence
    assert "posteriorAfter_two_true_witness" in posterior_blocker
    assert "Fintype.card_congr" in carrier_blocker
    assert "learnedPosterior_ne_boolBeliefInterpret" in uninhabited
    assert tuple(re.findall(r"(?m)^theorem (\w+)", uncommented)) == PUBLIC_THEOREMS
    assert not re.search(r"(?m)^(?:noncomputable )?def\s+\w+", uncommented)


def test_retained_predecessors_are_concrete_and_keep_failed_identities_separate() -> (
    None
):
    source = COMPOSITION.read_text(encoding="utf-8")
    retained = _declaration(source, "theorem", "retainedFiniteReference_predecessors")

    for predecessor in (
        "posteriorBadMass_failure_probability_le",
        "posteriorAfter_two_true_witness",
        "variationalFreeEnergy_eq_surprisal_iff",
        "vfeGap_eq_finiteKL_recognition_posterior",
        "boolFeedback_observation_changes_emittedAction",
        "factorizedProduct_invariant_under_pairedKernel",
        "boolBlanketStationaryLaw_isStationary",
        "nativeKL_contraction_to_invariant",
        "boolBlanket_finiteKL_strict_decrease",
        "boolBlanket_nativeKL_strict_decrease",
    ):
        assert predecessor in retained

    assert "(posteriorUpdate selectedPrior true).sum_one" in retained
    assert "posteriorAfter selectedPrior (fun _ => true) 2 false = 1 / 10" in retained
    assert "posteriorAfter selectedPrior (fun _ => true) 2 true = 9 / 10" in retained
    assert "boolFeedbackTree.2 false" in retained
    assert "boolFeedbackTree.2 true" in retained
    assert "boolBeliefInterpret" in retained
    assert "actionPrediction" in retained
    assert "boolBlanketRefreshKernel" in retained
    assert "boolBlanketStationaryLaw" in retained
    assert "boolBlanketOrigin ≠ boolBlanketAlternative" in retained
    assert "InformationTheory.klDiv" in retained
    assert "finiteKL" in retained
    assert "selectedActionTransition_eq_sampledSemigroup" not in retained
    assert not re.search(
        r"boolActionTransition[^\n=]*=\s*boolBlanketRefreshKernel", retained
    )


def test_terminal_theorem_connects_one_shared_learned_blanket_model() -> None:
    source = COMPOSITION.read_text(encoding="utf-8")
    terminal = _declaration(source, "theorem", "finiteReferenceAgent_terminal")
    statement = terminal.partition(":= by")[0]
    compact_statement = re.sub(r"\s+", " ", statement)

    for local_owner in (
        "let learned : FiniteLaw Bool :=",
        "let updatedInternal : FiniteLaw Bool :=",
        "let liftedLearned : FiniteLaw BoolBlanketState :=",
        "let liftedUpdated : FiniteLaw BoolBlanketState :=",
        "let model :=",
        "let actionInterface :=",
        "let emittedTrueAction : Bool :=",
        "let selectedKernel : FiniteKernel BoolBlanketState BoolBlanketState :=",
        "let stationary : FiniteLaw BoolBlanketState :=",
    ):
        assert local_owner in terminal

    for connected_claim in (
        "posteriorAfter selectedPrior (fun _ => true) 2",
        "learned false = 1 / 10",
        "learned true = 9 / 10",
        "liftedLearned.fstMarginal = learned",
        "∑ hypothesis, updatedInternal hypothesis = 1",
        "updatedInternal ≠ learned",
        "posteriorBadMassFailure selectedPrior 2 (identificationGap / 2)",
        "predictedOutcome model false = selectedLikelihood.predictive learned",
        "posteriorState model false true hEvidence = liftedUpdated",
        "recognition = liftedUpdated",
        "selectedPosteriorFeedback_continuation_optimal",
        "selectedPosteriorFeedback_strictlyBetter",
        "selectedActionTransition_eq_sampledSemigroup",
        "boolBlanketActionIndexedSemigroup_true_kernel",
        "liftInternalLaw_ne_uniform_of_ne_uniform",
        "refreshSemigroup_finiteKL_strict_decrease_of_ne_uniform",
        "refreshSemigroup_nativeKL_strict_decrease_of_ne_uniform",
    ):
        assert connected_claim in terminal

    assert re.search(
        r"posteriorState model false true hEvidence\)\.fstMarginal =\s*"
        r"selectedBeliefInterpret\s*\(selectedBeliefUpdate\s*"
        r"SelectedBeliefIndex\.learned false true\)",
        statement,
    )
    assert re.search(
        r"posteriorState model false true hEvidence\)\.fstMarginal =\s*"
        r"selectedBeliefInterpret\s*\(selectedPosteriorFeedbackModel\.update\s*"
        r"SelectedBeliefIndex\.learned false true\)",
        statement,
    )
    assert "Fintype.card BoolBlanketState = 16" in compact_statement
    assert "boolBlanketOrigin ≠ boolBlanketAlternative" in compact_statement
    assert "0 < stationary boolBlanketOrigin" in compact_statement
    assert "0 < stationary boolBlanketAlternative" in compact_statement
    assert "0 < liftedUpdated boolBlanketOrigin" in compact_statement
    assert "0 < liftedUpdated boolBlanketAlternative" in compact_statement
    assert "emittedTrueAction = true" in compact_statement
    assert (
        "selectedKernel = model.transition "
        "(selectedPosteriorFeedbackTree.2 true).1" in compact_statement
    )
    assert (
        "selectedKernel = boolBlanketActionIndexedSemigroup.sampledKernel true"
        in compact_statement
    )
    assert (
        "boolBlanketActionIndexedSemigroup.sampledKernel true = "
        "boolBlanketRefreshKernel" in compact_statement
    )
    assert (
        "ConditionalBlanketModel (FEP.MarkovBlanket.Blanket Bool Bool) Bool Bool"
        in compact_statement
    )
    assert "ConditionalBlanketModel Unit" not in compact_statement
    assert "∀ blanket, 0 < blanketModel.blanketLaw blanket" in compact_statement
    assert re.search(
        r"∃ blanketFirst blanketSecond, blanketFirst ≠ blanketSecond ∧ "
        r"0 < blanketModel\.blanketLaw blanketFirst ∧ "
        r"0 < blanketModel\.blanketLaw blanketSecond",
        compact_statement,
    )
    assert "Factorizes blanketModel" in compact_statement
    assert (
        "∀ internal sensory active external, stationary "
        "(internal, (sensory, (active, external))) = blanketModel.blanketLaw "
        "(sensory, active) * blanketModel.conditional (sensory, active) "
        "(internal, external)" in compact_statement
    )
    assert "IsInvariant stationary selectedKernel" in compact_statement
    assert compact_statement.count("selectedKernel.predictive liftedUpdated") == 3
    assert compact_statement.count("embeddedLaw liftedUpdated") == 2
    assert "finiteKL (selectedKernel.predictive liftedUpdated) stationary <" in (
        compact_statement
    )
    assert "finiteKL liftedUpdated stationary" in compact_statement

    for legacy_or_overclaim in (
        "boolBlanketInitialLaw",
        "boolBlanketEvolvedLaw",
        "boolBlanket_finiteKL_strict_decrease",
        "boolBlanket_nativeKL_strict_decrease",
        "boolBlanketActionIndexedSemigroup_kernels_ne",
        "rowwise",
        "observationalBlanket",
        "LocalFreeEnergyDescent",
        "probabilityCurrent",
        "IsDetailedBalanced",
    ):
        assert legacy_or_overclaim not in terminal


def test_finite_reference_agent_compiles_warning_free_with_explicit_output(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "finite_reference_agent.olean"
    result = subprocess.run(
        [
            lake_executable(),
            "env",
            "lean",
            "-R",
            str(FORMAL_ROOT),
            "-o",
            str(output_path),
            str(COMPOSITION),
        ],
        cwd=LEAN_ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=300,
    )

    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert output == ""
    assert output_path.is_file()
    assert output_path.stat().st_size > 0


def test_public_theorems_have_only_standard_axioms(tmp_path: Path) -> None:
    probe = tmp_path / "finite_reference_agent_axioms.lean"
    probe.write_text(
        COMPOSITION.read_text(encoding="utf-8")
        + "\n"
        + "\n".join(
            f"#print axioms FEPComposed.FiniteReferenceAgent.{theorem}"
            for theorem in PUBLIC_THEOREMS
        )
        + "\n",
        encoding="utf-8",
    )
    output_path = tmp_path / "finite_reference_agent_axioms.olean"
    result = subprocess.run(
        [
            lake_executable(),
            "env",
            "lean",
            "-R",
            str(tmp_path),
            "-o",
            str(output_path),
            str(probe),
        ],
        cwd=LEAN_ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=300,
    )

    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "warning:" not in output.lower()
    assert "sorryAx" not in output
    for theorem in PUBLIC_THEOREMS:
        assert f"FiniteReferenceAgent.{theorem}" in output
    axiom_lists = re.findall(r"depends on axioms: \[(.*?)\]", output, flags=re.DOTALL)
    assert len(axiom_lists) == len(PUBLIC_THEOREMS), output
    for axiom_list in axiom_lists:
        axioms = {item.strip() for item in axiom_list.split(",") if item.strip()}
        assert axioms <= {"propext", "Classical.choice", "Quot.sound"}
