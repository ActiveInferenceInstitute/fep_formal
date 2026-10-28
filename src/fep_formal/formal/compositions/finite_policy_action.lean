module
public import FepSketches.policy_tree
public import FepSketches.active_inference
public import FepSketches.controlled_markov
public import FepSketches.decision_risk
public import FepSketches.finite_posterior_learning

@[expose] public section

/-!
# Finite variational inference and observation-contingent action

This leaf joins the existing variational-free-energy, policy-tree, and
action-transition carriers.  Native KL is retained only at the full-support
boundary where the decision-risk bridge applies.  No finite-to-native
mutual-information bridge is maintained, so this leaf does not relabel the
native channel theorem as finite epistemic value or total expected free energy.
The H1.3 posterior enters tree recursion through a finite index: its root is the
exact selected two-sample law and its only reachable successors commute with
one further `posteriorUpdate`.  Absorbing successors expose the one-step bound
instead of pretending that all repeatedly updated laws form a finite type.  No
shared reward carrier relates Bellman reward to EFE, so no equivalence or
counterexample is asserted.  `PolicyTreeModel` has no generic transition field.
The retained Boolean compatibility trace separately proves that its updated
point-mass belief denotes prediction through the emitted action's controlled
transition; no generic model equivalence is inferred.
-/

namespace FEPComposed.FinitePolicyAction

open FEP FEP.ActiveInference FEP.ControlledMarkov FEP.DecisionRisk
  FEP.FiniteInformation FEP.FinitePosteriorLearning FEP.NativeBlanket
  FEP.PolicyTrees
open scoped BigOperators

universe uPolicy uState uOutcome

variable {Policy : Type uPolicy} {State : Type uState} {Outcome : Type uOutcome}
  [Fintype Policy] [Fintype State] [Fintype Outcome]

/-! ## Recognition-to-posterior variational gap -/

/-- The variational gap is finite KL from recognition to posterior.  Full
posterior support additionally identifies that real gap with Mathlib's native
extended KL; the truth-to-report log-score orientation is deliberately not
used here. -/
theorem vfeGap_eq_finiteKL_recognition_posterior
    [MeasurableSpace State] [DiscreteMeasurableSpace State]
    (model : GenerativeModel Policy State Outcome) (policy : Policy)
    (outcome : Outcome)
    (hEvidence : 0 < predictedOutcome model policy outcome)
    (recognition : FiniteLaw State)
    (hPosteriorSupport : ∀ state,
      0 < posteriorState model policy outcome hEvidence state) :
    (variationalFreeEnergy model policy outcome hEvidence recognition -
        variationalFreeEnergy model policy outcome hEvidence
          (posteriorState model policy outcome hEvidence) =
      finiteKL recognition
        (posteriorState model policy outcome hEvidence)) ∧
      InformationTheory.klDiv
          (embeddedLaw recognition)
          (embeddedLaw (posteriorState model policy outcome hEvidence)) =
        ENNReal.ofReal
          (variationalFreeEnergy model policy outcome hEvidence recognition -
            variationalFreeEnergy model policy outcome hEvidence
              (posteriorState model policy outcome hEvidence)) := by
  have hGap :
      variationalFreeEnergy model policy outcome hEvidence recognition -
          variationalFreeEnergy model policy outcome hEvidence
            (posteriorState model policy outcome hEvidence) =
        finiteKL recognition
          (posteriorState model policy outcome hEvidence) := by
    simp only [variationalFreeEnergy]
    rw [finiteKL_self]
    ring
  refine ⟨hGap, ?_⟩
  rw [hGap]
  exact weightedDirac_klDiv_eq_finiteKL_of_fullSupport recognition
    (posteriorState model policy outcome hEvidence) hPosteriorSupport

/-! ## Prior-weighted law on one finite tree depth -/

/-- Apply the maintained normalized control posterior to tree values on one
fixed finite-depth carrier. -/
noncomputable def finiteTreeGibbsPosterior
    {Belief Action Observation : Type*}
    [Fintype Belief] [Fintype Action] [Fintype Observation]
    {depth : ℕ}
    (prior : FiniteLaw (PolicyTree Action Observation depth))
    (precision : ℝ) (model : PolicyTreeModel Belief Action Observation)
    (belief : Belief) : FiniteLaw (PolicyTree Action Observation depth) :=
  controlPosterior prior precision
    (fun tree => policyTreeValue model tree belief)

/-- The prior-weighted finite tree law is normalized by the existing control
posterior owner. -/
theorem finiteTreeGibbsPosterior_sum_one
    {Belief Action Observation : Type*}
    [Fintype Belief] [Fintype Action] [Fintype Observation]
    {depth : ℕ}
    (prior : FiniteLaw (PolicyTree Action Observation depth))
    (precision : ℝ) (model : PolicyTreeModel Belief Action Observation)
    (belief : Belief) :
    ∑ tree, finiteTreeGibbsPosterior prior precision model belief tree = 1 := by
  simpa [finiteTreeGibbsPosterior] using
    controlPosterior_sum_one prior precision
      (fun tree => policyTreeValue model tree belief)

/-! ## Finite index for the selected learned posterior -/

/-- The smallest belief-index carrier needed to start at H1.3's selected
two-sample posterior and branch on one further Boolean observation.  Successor
indices are terminal for this depth-two decision problem; they do not claim to
enumerate the full space of repeatedly updated finite laws. -/
inductive SelectedBeliefIndex where
  | learned
  | afterObservation (observation : Bool)
  deriving DecidableEq, Fintype

/-- Interpret the root as H1.3's exact non-Dirac learned posterior and each
successor as one more update by H1.3's selected likelihood. -/
noncomputable def selectedBeliefInterpret :
    SelectedBeliefIndex → FiniteLaw Bool
  | SelectedBeliefIndex.learned =>
      posteriorAfter selectedPrior (fun _ => true) 2
  | SelectedBeliefIndex.afterObservation observation =>
      posteriorUpdate
        (posteriorAfter selectedPrior (fun _ => true) 2) observation

/-- The root interpretation is exactly the public H1.3 two-observation
posterior, including both authored masses. -/
theorem selectedBeliefInterpret_learned_exact :
    selectedBeliefInterpret SelectedBeliefIndex.learned false = 1 / 10 ∧
      selectedBeliefInterpret SelectedBeliefIndex.learned true = 9 / 10 := by
  have hLearned := posteriorAfter_two_true_witness
  exact ⟨by simpa [selectedBeliefInterpret] using hLearned.1,
    by simpa [selectedBeliefInterpret] using hLearned.2.1⟩

/-- H1.3's selected learned posterior is neither Boolean point mass. -/
theorem selectedBeliefInterpret_learned_nonDirac :
    selectedBeliefInterpret SelectedBeliefIndex.learned ≠
        FiniteLaw.pointMass false ∧
      selectedBeliefInterpret SelectedBeliefIndex.learned ≠
        FiniteLaw.pointMass true := by
  constructor
  · intro hPointMass
    have hTrueMass := congrArg (fun law : FiniteLaw Bool => law true) hPointMass
    rw [selectedBeliefInterpret_learned_exact.2] at hTrueMass
    norm_num [FiniteLaw.pointMass] at hTrueMass
  · intro hPointMass
    have hFalseMass := congrArg (fun law : FiniteLaw Bool => law false) hPointMass
    rw [selectedBeliefInterpret_learned_exact.1] at hFalseMass
    norm_num [FiniteLaw.pointMass] at hFalseMass

/-- Advance the learned root by one observation.  The successor is absorbing
because this finite carrier owns exactly one sound update, which is all the
depth-two feedback theorem consumes. -/
def selectedBeliefUpdate :
    SelectedBeliefIndex → Bool → Bool → SelectedBeliefIndex
  | SelectedBeliefIndex.learned, _, observation =>
      SelectedBeliefIndex.afterObservation observation
  | SelectedBeliefIndex.afterObservation previousObservation, _, _ =>
      SelectedBeliefIndex.afterObservation previousObservation

/-- Interpreting the one reachable update is exactly H1.3's
`posteriorUpdate`; the carrier does not postulate closure under later updates. -/
theorem selectedBeliefUpdate_commutes_posteriorUpdate
    (action observation : Bool) :
    selectedBeliefInterpret
        (selectedBeliefUpdate SelectedBeliefIndex.learned action observation) =
      posteriorUpdate
        (selectedBeliefInterpret SelectedBeliefIndex.learned) observation := by
  rfl

/-! ## Posterior-dependent finite feedback -/

/-- A false-positive report costs four times a false-negative report.  Its
Bayes threshold is `4/5`, which lies strictly between the truth masses `3/4`
and `27/28` produced by the two one-step H1.3 posterior branches. -/
def selectedAsymmetricDecisionLoss (hypothesis action : Bool) : ℝ :=
  if action = hypothesis then 0 else if action then 4 else 1

/-- Posterior expected loss of one Boolean report at a selected belief index. -/
noncomputable def selectedPosteriorDecisionRisk
    (belief : SelectedBeliefIndex) (action : Bool) : ℝ :=
  ∑ hypothesis,
    selectedBeliefInterpret belief hypothesis *
      selectedAsymmetricDecisionLoss hypothesis action

/-- A depth-two policy model whose first observation is the H1.3 posterior
predictive and whose terminal cost is the asymmetric posterior decision risk. -/
noncomputable def selectedPosteriorFeedbackModel :
    PolicyTreeModel SelectedBeliefIndex Bool Bool where
  observationLaw belief _ :=
    selectedLikelihood.predictive (selectedBeliefInterpret belief)
  update := selectedBeliefUpdate
  stageCost depth belief action :=
    if depth = 0 then selectedPosteriorDecisionRisk belief action else 0

/-- The second report follows the informative observation; the first action is
a decision-free placeholder before that observation arrives. -/
def selectedPosteriorFeedbackTree : PolicyTree Bool Bool 2 :=
  (false, fun observation =>
    (observation, fun _ => PUnit.unit))

/-- A comparison plan that must use one fixed second report on both branches. -/
def selectedPosteriorOpenLoopPlan
    (action : Bool) : OpenLoopPlan Bool 2 :=
  (false, (action, PUnit.unit))

/-- At either successor, the observation-matching report has strictly smaller
posterior risk than the only alternative report. -/
theorem selectedPosteriorDecisionRisk_prefers_observation
    (observation alternative : Bool) (hDifferent : alternative ≠ observation) :
    selectedPosteriorDecisionRisk
        (SelectedBeliefIndex.afterObservation observation) observation <
      selectedPosteriorDecisionRisk
        (SelectedBeliefIndex.afterObservation observation) alternative := by
  cases observation <;> cases alternative <;>
    norm_num [selectedPosteriorDecisionRisk, selectedBeliefInterpret,
      selectedAsymmetricDecisionLoss, posteriorAfter, posteriorUpdate,
      selectedPrior, FEP.DecisionRisk.boolFairLaw, selectedLikelihood,
      FiniteKernel.posterior, FiniteKernel.predictive_mass,
      Fintype.sum_bool] at *

/-- The observation-matching report is the action selected by the maintained
depth-zero Bellman objective, not merely an externally supplied better action. -/
theorem selectedPosteriorFeedback_continuation_optimal (observation : Bool) :
    optimalTreeAction selectedPosteriorFeedbackModel 0
        (SelectedBeliefIndex.afterObservation observation) =
      (selectedPosteriorFeedbackTree.2 observation).1 := by
  change
    optimalTreeAction selectedPosteriorFeedbackModel 0
        (SelectedBeliefIndex.afterObservation observation) = observation
  by_contra hDifferent
  have hMinimum :=
    optimalTreeAction_le selectedPosteriorFeedbackModel 0
      (SelectedBeliefIndex.afterObservation observation) observation
  have hMinimumRisk :
      selectedPosteriorDecisionRisk
          (SelectedBeliefIndex.afterObservation observation)
          (optimalTreeAction selectedPosteriorFeedbackModel 0
            (SelectedBeliefIndex.afterObservation observation)) ≤
        selectedPosteriorDecisionRisk
          (SelectedBeliefIndex.afterObservation observation) observation := by
    simpa [selectedPosteriorFeedbackModel, optimalTreeValue] using hMinimum
  have hStrict :=
    selectedPosteriorDecisionRisk_prefers_observation observation
      (optimalTreeAction selectedPosteriorFeedbackModel 0
        (SelectedBeliefIndex.afterObservation observation)) hDifferent
  exact (not_lt_of_ge hMinimumRisk) hStrict

/-- The two observation branches emit different second-stage reports. -/
theorem selectedPosteriorFeedback_changes_action :
    (selectedPosteriorFeedbackTree.2 false).1 ≠
      (selectedPosteriorFeedbackTree.2 true).1 := by
  norm_num [selectedPosteriorFeedbackTree]

/-- The observation-dependent tree has exact posterior decision risk `13/40`. -/
theorem selectedPosteriorFeedback_value :
    policyTreeValue selectedPosteriorFeedbackModel
        selectedPosteriorFeedbackTree SelectedBeliefIndex.learned = 13 / 40 := by
  norm_num [policyTreeValue, selectedPosteriorFeedbackModel,
    selectedPosteriorFeedbackTree, selectedPosteriorDecisionRisk,
    selectedAsymmetricDecisionLoss, selectedBeliefInterpret,
    selectedBeliefUpdate, posteriorAfter, posteriorUpdate, selectedPrior,
    FEP.DecisionRisk.boolFairLaw, selectedLikelihood,
    FiniteKernel.posterior, FiniteKernel.predictive_mass,
    Fintype.sum_bool]

/-- Fixed false and true reports have respective risks `9/10` and `2/5`. -/
theorem selectedPosteriorOpenLoop_value (action : Bool) :
    openLoopValue selectedPosteriorFeedbackModel
        (selectedPosteriorOpenLoopPlan action) SelectedBeliefIndex.learned =
      if action then 2 / 5 else 9 / 10 := by
  cases action <;>
    norm_num [openLoopValue, selectedPosteriorFeedbackModel,
      selectedPosteriorOpenLoopPlan, selectedPosteriorDecisionRisk,
      selectedAsymmetricDecisionLoss, selectedBeliefInterpret,
      selectedBeliefUpdate, posteriorAfter, posteriorUpdate, selectedPrior,
      FEP.DecisionRisk.boolFairLaw, selectedLikelihood,
      FiniteKernel.posterior, FiniteKernel.predictive_mass,
      Fintype.sum_bool]

/-- The posterior-dependent feedback tree strictly improves on every fixed
second-stage report under the same predictive law and asymmetric loss. -/
theorem selectedPosteriorFeedback_strictlyBetter :
    ∀ fixedAction,
      policyTreeValue selectedPosteriorFeedbackModel
          selectedPosteriorFeedbackTree SelectedBeliefIndex.learned <
        openLoopValue selectedPosteriorFeedbackModel
          (selectedPosteriorOpenLoopPlan fixedAction)
          SelectedBeliefIndex.learned := by
  intro fixedAction
  rw [selectedPosteriorFeedback_value,
    selectedPosteriorOpenLoop_value]
  cases fixedAction <;> norm_num

/-! ## Executable observation-contingent action -/

/-- The depth-one continuations of the existing Boolean feedback tree are the
policies of an active-inference model whose transition is the maintained
Boolean controlled transition. -/
noncomputable def boolFeedbackActionModel :
    GenerativeModel (PolicyTree Bool Bool 1) Bool Bool where
  initialState := fairBoolLaw
  transition tree := boolActionTransition tree.1
  likelihood := boolObservationKernel
  preferences := fairBoolLaw
  policyPrior := FiniteLaw.uniform

/-- Emit a continuation tree's root action through the canonical action
interface, using the exact transition stored by the generative model. -/
noncomputable def boolFeedbackActionInterface :
    ActionInterface boolFeedbackActionModel Bool where
  policyToAction tree := tree.1
  actionTransition := boolActionTransition
  transition_consistent := by
    intro tree
    rfl

/-- False and true observations select different continuation actions, and
executing either selected action uses exactly the corresponding generative
model transition. -/
theorem boolFeedback_observation_changes_emittedAction :
    policyTreeValue boolFeedbackModel boolFeedbackTree false = 0 ∧
    (∀ fixedAction,
      policyTreeValue boolFeedbackModel boolFeedbackTree false <
        openLoopValue boolFeedbackModel
          (boolOpenLoopPlan fixedAction) false) ∧
    boolFeedbackActionInterface.policyToAction
          (boolFeedbackTree.2 false) ≠
        boolFeedbackActionInterface.policyToAction
          (boolFeedbackTree.2 true) ∧
    ∀ observation,
      boolFeedbackActionInterface.policyToAction
          (boolFeedbackTree.2 observation) = observation ∧
        boolMismatchCost
            (boolFeedbackModel.update false false observation)
            (boolFeedbackActionInterface.policyToAction
              (boolFeedbackTree.2 observation)) = 0 ∧
        optimalTreeAction boolFeedbackModel 0
            (boolFeedbackModel.update false false observation) =
          boolFeedbackActionInterface.policyToAction
            (boolFeedbackTree.2 observation) ∧
        boolBeliefInterpret
            (boolFeedbackModel.update false false observation) =
          actionPrediction (boolBeliefInterpret false) boolActionTransition
            (boolFeedbackActionInterface.policyToAction
              (boolFeedbackTree.2 observation)) ∧
        boolFeedbackActionInterface.actionTransition
            (boolFeedbackActionInterface.policyToAction
              (boolFeedbackTree.2 observation)) =
          boolFeedbackActionModel.transition
            (boolFeedbackTree.2 observation) := by
  constructor
  · exact boolFeedbackTree_value_zero
  constructor
  · intro fixedAction
    exact boolFeedbackTree_strictlyBetter fixedAction
  constructor
  · norm_num [boolFeedbackActionInterface, boolFeedbackTree]
  intro observation
  constructor
  · rfl
  constructor
  · simp [boolFeedbackActionInterface, boolFeedbackTree, boolFeedbackModel,
      boolMismatchCost]
  constructor
  · simpa [optimalTreeAction, optimalTreeValue, boolFeedbackModel,
      boolFeedbackActionInterface, boolFeedbackTree,
      twoStageFeedback, Fintype.sum_bool] using
      twoStageFeedback_eq_observation observation
  constructor
  · rw [bool_actionPrediction_eq]
    apply FiniteLaw.ext_mass
    funext state
    simp [boolFeedbackModel, boolFeedbackActionInterface, boolFeedbackTree,
      boolBeliefInterpret, FiniteLaw.pointMass]
    rfl
  · exact boolFeedbackActionInterface.transition_consistent _

end FEPComposed.FinitePolicyAction
