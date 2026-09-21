"""H1.4 finite policy/action composition contracts."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from fep_lean.lean_source import lean_code_without_comments
from tests._support.lake import lake_executable
from tests._support.lean_runner import run_lean_compile_probe

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEAN_ROOT = PROJECT_ROOT / "lean"
COMPOSITION = (
    PROJECT_ROOT
    / "src"
    / "fep_lean"
    / "formal"
    / "compositions"
    / "finite_policy_action.lean"
)

pytestmark = pytest.mark.serial_lean

EXACT_IMPORTS = (
    "FepSketches.policy_tree",
    "FepSketches.active_inference",
    "FepSketches.controlled_markov",
    "FepSketches.decision_risk",
    "FepSketches.finite_posterior_learning",
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


def test_policy_action_leaf_owns_exact_import_and_namespace_contract() -> None:
    source = COMPOSITION.read_text(encoding="utf-8")

    assert tuple(re.findall(r"(?m)^import (\S+)$", source)) == EXACT_IMPORTS
    assert "namespace FEPComposed.FinitePolicyAction\n" in source
    assert source.rstrip().endswith("end FEPComposed.FinitePolicyAction")
    assert not re.search(
        r"\b(?:sorry|admit|axiom|opaque)\b|unsafe\s+(?:def|theorem)|:\s*True\b",
        source,
    )


def test_vfe_gap_preserves_recognition_posterior_order_and_native_support() -> None:
    source = COMPOSITION.read_text(encoding="utf-8")
    gap = _declaration(source, "vfeGap_eq_finiteKL_recognition_posterior")

    assert "(hPosteriorSupport : ∀ state," in gap
    assert "0 < posteriorState model policy outcome hEvidence state" in gap
    assert "finiteKL recognition" in gap
    assert "posteriorState model policy outcome hEvidence" in gap
    assert "InformationTheory.klDiv" in gap
    assert "(embeddedLaw recognition)" in gap
    assert "ENNReal.ofReal" in gap
    assert "weightedDirac_klDiv_eq_finiteKL_of_fullSupport" in gap
    assert "properLogScore" not in gap


def test_selected_belief_index_is_the_exact_h13_posterior_and_updates_once() -> None:
    source = COMPOSITION.read_text(encoding="utf-8")
    interpret = _declaration(source, "selectedBeliefInterpret")
    update = _declaration(source, "selectedBeliefUpdate")
    exact = _declaration(source, "selectedBeliefInterpret_learned_exact")
    non_dirac = _declaration(source, "selectedBeliefInterpret_learned_nonDirac")
    commutation = _declaration(source, "selectedBeliefUpdate_commutes_posteriorUpdate")

    assert re.search(
        r"inductive SelectedBeliefIndex\b.*?\| learned\b.*?"
        r"\| afterObservation \(observation : Bool\).*?deriving DecidableEq, Fintype",
        lean_code_without_comments(source),
        flags=re.DOTALL,
    )
    assert "posteriorAfter selectedPrior (fun _ => true) 2" in interpret
    assert "posteriorUpdate" in interpret
    assert "SelectedBeliefIndex.afterObservation observation" in interpret
    assert "SelectedBeliefIndex.learned" in update
    assert "SelectedBeliefIndex.afterObservation observation" in update
    assert "selectedBeliefInterpret SelectedBeliefIndex.learned false = 1 / 10" in exact
    assert "selectedBeliefInterpret SelectedBeliefIndex.learned true = 9 / 10" in exact
    assert "FiniteLaw.pointMass false" in non_dirac
    assert "FiniteLaw.pointMass true" in non_dirac
    assert (
        "selectedBeliefInterpret\n        (selectedBeliefUpdate "
        "SelectedBeliefIndex.learned action observation)" in commutation
    )
    assert (
        "posteriorUpdate\n        (selectedBeliefInterpret "
        "SelectedBeliefIndex.learned) observation" in commutation
    )
    assert not re.search(r"instance\b[^\n]*Fintype\s*\([^\n]*FiniteLaw", source)


def test_selected_feedback_uses_asymmetric_bayes_risk_and_strictly_wins() -> None:
    source = COMPOSITION.read_text(encoding="utf-8")
    loss = _declaration(source, "selectedAsymmetricDecisionLoss")
    risk = _declaration(source, "selectedPosteriorDecisionRisk")
    model = _declaration(source, "selectedPosteriorFeedbackModel")
    tree = _declaration(source, "selectedPosteriorFeedbackTree")
    changes_action = _declaration(source, "selectedPosteriorFeedback_changes_action")
    optimal = _declaration(source, "selectedPosteriorDecisionRisk_prefers_observation")
    feedback_value = _declaration(source, "selectedPosteriorFeedback_value")
    open_loop_value = _declaration(source, "selectedPosteriorOpenLoop_value")
    strict = _declaration(source, "selectedPosteriorFeedback_strictlyBetter")

    assert "if action = hypothesis then 0" in loss
    assert "if action then 4 else 1" in loss
    assert "selectedBeliefInterpret belief hypothesis" in risk
    assert "selectedAsymmetricDecisionLoss hypothesis action" in risk
    assert "PolicyTreeModel SelectedBeliefIndex Bool Bool" in model
    assert "selectedLikelihood.predictive (selectedBeliefInterpret belief)" in model
    assert "update := selectedBeliefUpdate" in model
    assert "selectedPosteriorDecisionRisk belief action" in model
    assert "fun observation =>" in tree
    assert "(observation, fun _ => PUnit.unit)" in tree
    assert "selectedPosteriorFeedbackTree.2 false" in changes_action
    assert "selectedPosteriorFeedbackTree.2 true" in changes_action
    assert "alternative ≠ observation" in optimal
    assert "selectedPosteriorDecisionRisk" in optimal
    assert "SelectedBeliefIndex.afterObservation observation" in optimal
    assert "= 13 / 40" in feedback_value
    assert "if action then 2 / 5 else 9 / 10" in open_loop_value
    assert "∀ fixedAction" in strict
    assert "policyTreeValue selectedPosteriorFeedbackModel" in strict
    assert "openLoopValue selectedPosteriorFeedbackModel" in strict
    assert "false-positive report costs four times" in source


def test_selected_feedback_action_attains_the_recursive_selector() -> None:
    source = COMPOSITION.read_text(encoding="utf-8")
    optimal = _declaration(source, "selectedPosteriorFeedback_continuation_optimal")

    assert "(observation : Bool)" in optimal
    assert "optimalTreeAction selectedPosteriorFeedbackModel 0" in optimal
    assert "SelectedBeliefIndex.afterObservation observation" in optimal
    assert "selectedPosteriorFeedbackTree.2 observation" in optimal


def test_boolean_feedback_emits_nonconstant_action_through_model_transition() -> None:
    source = COMPOSITION.read_text(encoding="utf-8")
    model = _declaration(source, "boolFeedbackActionModel")
    interface = _declaration(source, "boolFeedbackActionInterface")
    witness = _declaration(source, "boolFeedback_observation_changes_emittedAction")

    assert "GenerativeModel (PolicyTree Bool Bool 1) Bool Bool" in model
    assert "transition tree := boolActionTransition tree.1" in model
    assert "policyPrior := FiniteLaw.uniform" in model
    assert "ActionInterface boolFeedbackActionModel Bool" in interface
    assert "policyToAction tree := tree.1" in interface
    assert "actionTransition := boolActionTransition" in interface
    assert "transition_consistent := by" in interface
    assert "boolFeedbackTree.2 false" in witness
    assert "boolFeedbackTree.2 true" in witness
    assert "≠" in witness
    assert "∀ observation" in witness
    assert "boolFeedbackTree.2 observation" in witness
    assert "boolFeedbackActionInterface.actionTransition" in witness
    assert "boolFeedbackActionModel.transition" in witness
    assert "boolFeedbackActionInterface.transition_consistent" in witness
    assert "policyTreeValue boolFeedbackModel boolFeedbackTree false = 0" in witness
    assert "boolFeedbackTree_strictlyBetter" in witness
    assert "boolMismatchCost" in witness
    assert "boolFeedbackModel.update false false observation" in witness
    assert "boolBeliefInterpret" in witness
    assert (
        "actionPrediction (boolBeliefInterpret false) boolActionTransition" in witness
    )
    assert "optimalTreeAction boolFeedbackModel 0" in witness
    assert "twoStageFeedback_eq_observation" in witness


def test_same_depth_tree_gibbs_law_reuses_normalized_control_posterior() -> None:
    source = COMPOSITION.read_text(encoding="utf-8")
    law = _declaration(source, "finiteTreeGibbsPosterior")
    normalization = _declaration(source, "finiteTreeGibbsPosterior_sum_one")

    assert "prior : FiniteLaw (PolicyTree Action Observation depth)" in law
    assert "controlPosterior prior precision" in law
    assert "policyTreeValue model tree belief" in law
    assert "∑ tree, finiteTreeGibbsPosterior" in normalization
    assert "= 1" in normalization
    assert "controlPosterior_sum_one" in normalization


def test_leaf_keeps_epistemic_and_total_efe_garbling_out_of_scope() -> None:
    source = COMPOSITION.read_text(encoding="utf-8")
    uncommented = lean_code_without_comments(source)
    prose = re.sub(r"\s+", " ", source)

    assert "No finite-to-native mutual-information bridge is maintained" in prose
    assert "The H1.3 posterior enters tree recursion through a finite index" in prose
    assert "Absorbing successors expose the one-step bound" in prose
    assert "No shared reward carrier relates Bellman reward to EFE" in prose
    assert "`PolicyTreeModel` has no generic transition field" in prose
    assert "The retained Boolean compatibility trace separately proves" in prose
    assert "The tree-learning clause remains blocked" not in prose
    assert "the H1.8 transition/value merge remains blocked" not in prose
    assert "epistemicValue_mono_under_observationGarbling" not in uncommented
    assert "nativeChannelMutualInformation" not in uncommented
    assert "properLogScoreExcessRisk" not in uncommented
    assert "reward" not in uncommented.lower()
    assert "infiniteHorizon" not in uncommented
    assert not re.search(r"\b(?:structure|def)\s+PolicyTree\b", uncommented)
    assert not re.search(r"\bstructure\s+ActionInterface\b", uncommented)
    assert tuple(re.findall(r"(?m)^theorem ([A-Za-z0-9_']+)", uncommented)) == (
        "vfeGap_eq_finiteKL_recognition_posterior",
        "finiteTreeGibbsPosterior_sum_one",
        "selectedBeliefInterpret_learned_exact",
        "selectedBeliefInterpret_learned_nonDirac",
        "selectedBeliefUpdate_commutes_posteriorUpdate",
        "selectedPosteriorDecisionRisk_prefers_observation",
        "selectedPosteriorFeedback_continuation_optimal",
        "selectedPosteriorFeedback_changes_action",
        "selectedPosteriorFeedback_value",
        "selectedPosteriorOpenLoop_value",
        "selectedPosteriorFeedback_strictlyBetter",
        "boolFeedback_observation_changes_emittedAction",
    )


def test_finite_policy_action_leaf_compiles_warning_free() -> None:
    result = run_lean_compile_probe(
        COMPOSITION,
        cwd=LEAN_ROOT,
        timeout_s=300,
        executable=lake_executable(),
    )

    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "warning:" not in output.lower()
