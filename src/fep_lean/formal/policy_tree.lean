module
public import FepSketches.controlled_markov

@[expose] public section

/-!
# Finite closed-loop policy trees

The carrier is indexed by its finite remaining depth.  Every internal node
chooses an action and supplies one continuation for each possible observation.
Observation laws and belief updates stay on the shared `FiniteLaw` substrate;
the recursive optimum uses the existing finite argmin owner.
-/

namespace FEP.PolicyTrees

open FEP FEP.ActiveInference FEP.ControlledMarkov Finset
open scoped BigOperators

universe uBelief uState uAction uObservation

variable {Belief : Type uBelief} {State : Type uState}
  {Action : Type uAction} {Observation : Type uObservation}
  [Fintype Belief] [Fintype State] [Fintype Action] [Fintype Observation]

/-! ## Depth-indexed carrier and evaluation -/

/-- A finite policy tree: a leaf at depth zero, and otherwise an action paired
with an observation-indexed continuation of one smaller depth. -/
def PolicyTree (Action : Type uAction) (Observation : Type uObservation) :
    ℕ → Type (max uAction uObservation)
  | 0 => PUnit
  | depth + 1 => Action × (Observation → PolicyTree Action Observation depth)

noncomputable instance instFintypePolicyTree (depth : ℕ) :
    Fintype (PolicyTree Action Observation depth) := by
  induction depth with
  | zero =>
      exact inferInstanceAs (Fintype PUnit)
  | succ depth inductionHypothesis =>
      classical
      letI : Fintype (PolicyTree Action Observation depth) :=
        inductionHypothesis
      exact inferInstanceAs
        (Fintype (Action × (Observation → PolicyTree Action Observation depth)))

instance instNonemptyPolicyTree [Nonempty Action] (depth : ℕ) :
    Nonempty (PolicyTree Action Observation depth) := by
  induction depth with
  | zero => exact inferInstanceAs (Nonempty PUnit)
  | succ depth inductionHypothesis =>
      change Nonempty
        (Action × (Observation → PolicyTree Action Observation depth))
      exact ⟨(Classical.choice (inferInstance : Nonempty Action),
        fun _ => Classical.choice inductionHypothesis)⟩

/-- Belief-indexed observation law, deterministic belief update, and
stage-dependent finite-horizon cost. -/
structure PolicyTreeModel
    (Belief Action Observation : Type*)
    [Fintype Belief] [Fintype Action] [Fintype Observation] where
  observationLaw : Belief → Action → FiniteLaw Observation
  update : Belief → Action → Observation → Belief
  stageCost : ℕ → Belief → Action → ℝ

/-- Recursive value of one observation-contingent policy tree. -/
noncomputable def policyTreeValue
    (model : PolicyTreeModel Belief Action Observation) :
    {depth : ℕ} → PolicyTree Action Observation depth → Belief → ℝ
  | 0, _, _ => 0
  | depth + 1, tree, belief =>
      model.stageCost depth belief tree.1 +
        ∑ observation,
          model.observationLaw belief tree.1 observation *
            policyTreeValue model (tree.2 observation)
              (model.update belief tree.1 observation)

/-- Exact node recursion, including observation-weighted continuation. -/
theorem policyTreeValue_node
    (model : PolicyTreeModel Belief Action Observation)
    {depth : ℕ} (action : Action)
    (continuation : Observation → PolicyTree Action Observation depth)
    (belief : Belief) :
    policyTreeValue (depth := depth + 1) model (action, continuation) belief =
      model.stageCost depth belief action +
        ∑ observation,
          model.observationLaw belief action observation *
            policyTreeValue model (continuation observation)
              (model.update belief action observation) :=
  rfl

/-! ## Finite Bellman optimum -/

/-- Backward-inducted optimal value, selecting a finite action minimizer at
every reachable observation branch. -/
noncomputable def optimalTreeValue [Nonempty Action]
    (model : PolicyTreeModel Belief Action Observation) : ℕ → Belief → ℝ
  | 0, _ => 0
  | depth + 1, belief =>
      let objective := fun action =>
        model.stageCost depth belief action +
          ∑ observation,
            model.observationLaw belief action observation *
              optimalTreeValue model depth
                (model.update belief action observation)
      objective (finiteArgmin objective)

/-- Action attaining the finite Bellman minimum at one tree node. -/
noncomputable def optimalTreeAction [Nonempty Action]
    (model : PolicyTreeModel Belief Action Observation)
    (depth : ℕ) (belief : Belief) : Action :=
  finiteArgmin fun action =>
    model.stageCost depth belief action +
      ∑ observation,
        model.observationLaw belief action observation *
          optimalTreeValue model depth
            (model.update belief action observation)

/-- The optimal value exposes the exact action minimum and
observation-weighted continuation at every successor depth. -/
theorem optimalTreeValue_eq_min [Nonempty Action]
    (model : PolicyTreeModel Belief Action Observation)
    (depth : ℕ) (belief : Belief) :
    optimalTreeValue model (depth + 1) belief =
      model.stageCost depth belief (optimalTreeAction model depth belief) +
        ∑ observation,
          model.observationLaw belief (optimalTreeAction model depth belief)
              observation *
            optimalTreeValue model depth
              (model.update belief (optimalTreeAction model depth belief)
                observation) :=
  rfl

/-- The chosen Bellman action is no worse than any alternative action. -/
theorem optimalTreeAction_le [Nonempty Action]
    (model : PolicyTreeModel Belief Action Observation)
    (depth : ℕ) (belief : Belief) (alternative : Action) :
    model.stageCost depth belief (optimalTreeAction model depth belief) +
        ∑ observation,
          model.observationLaw belief (optimalTreeAction model depth belief)
              observation *
            optimalTreeValue model depth
              (model.update belief (optimalTreeAction model depth belief)
                observation) ≤
      model.stageCost depth belief alternative +
        ∑ observation,
          model.observationLaw belief alternative observation *
            optimalTreeValue model depth
              (model.update belief alternative observation) := by
  let objective : Action → ℝ := fun action =>
    model.stageCost depth belief action +
      ∑ observation,
        model.observationLaw belief action observation *
          optimalTreeValue model depth
            (model.update belief action observation)
  change objective (finiteArgmin objective) ≤ objective alternative
  exact finiteArgmin_le objective alternative

/-- A concrete optimal tree obtained by backward induction. -/
noncomputable def optimalPolicyTree [Nonempty Action]
    (model : PolicyTreeModel Belief Action Observation) :
    (depth : ℕ) → Belief → PolicyTree Action Observation depth
  | 0, _ => PUnit.unit
  | depth + 1, belief =>
      let action := optimalTreeAction model depth belief
      (action, fun observation =>
        optimalPolicyTree model depth (model.update belief action observation))

/-- The backward-inducted tree attains the recursively defined optimum. -/
theorem optimalPolicyTree_value [Nonempty Action]
    (model : PolicyTreeModel Belief Action Observation) :
    ∀ (depth : ℕ) (belief : Belief),
      policyTreeValue model (optimalPolicyTree model depth belief) belief =
        optimalTreeValue model depth belief
  | 0, _ => rfl
  | depth + 1, belief => by
      rw [optimalTreeValue_eq_min]
      change
        model.stageCost depth belief (optimalTreeAction model depth belief) +
            ∑ observation,
              model.observationLaw belief
                  (optimalTreeAction model depth belief) observation *
                policyTreeValue model
                  (optimalPolicyTree model depth
                    (model.update belief
                      (optimalTreeAction model depth belief) observation))
                  (model.update belief
                    (optimalTreeAction model depth belief) observation) = _
      apply congrArg
      apply Finset.sum_congr rfl
      intro observation _
      rw [optimalPolicyTree_value model depth]

/-- The recursive Bellman value is below the value of every tree on the same
finite depth carrier. -/
theorem optimalTreeValue_le_tree [Nonempty Action]
    (model : PolicyTreeModel Belief Action Observation) :
    ∀ {depth : ℕ} (tree : PolicyTree Action Observation depth)
      (belief : Belief),
      optimalTreeValue model depth belief ≤ policyTreeValue model tree belief
  | 0, _, _ => le_rfl
  | depth + 1, tree, belief => by
      let objective : Action → ℝ := fun action =>
        model.stageCost depth belief action +
          ∑ observation,
            model.observationLaw belief action observation *
              optimalTreeValue model depth
                (model.update belief action observation)
      change objective (finiteArgmin objective) ≤
        model.stageCost depth belief tree.1 +
          ∑ observation,
            model.observationLaw belief tree.1 observation *
              policyTreeValue model (tree.2 observation)
                (model.update belief tree.1 observation)
      calc
        objective (finiteArgmin objective) ≤ objective tree.1 :=
          finiteArgmin_le objective tree.1
        _ ≤ model.stageCost depth belief tree.1 +
            ∑ observation,
              model.observationLaw belief tree.1 observation *
                policyTreeValue model (tree.2 observation)
                  (model.update belief tree.1 observation) := by
          change
            model.stageCost depth belief tree.1 +
                ∑ observation,
                  model.observationLaw belief tree.1 observation *
                    optimalTreeValue model depth
                      (model.update belief tree.1 observation) ≤
              model.stageCost depth belief tree.1 +
                ∑ observation,
                  model.observationLaw belief tree.1 observation *
                    policyTreeValue model (tree.2 observation)
                      (model.update belief tree.1 observation)
          apply add_le_add (le_refl _)
          apply Finset.sum_le_sum
          intro observation _
          exact mul_le_mul_of_nonneg_left
            (optimalTreeValue_le_tree model (tree.2 observation)
              (model.update belief tree.1 observation))
            ((model.observationLaw belief tree.1).nonneg observation)

/-- An optimal finite policy tree exists and attains a value no larger than
every alternative tree at the same depth. -/
theorem exists_optimalPolicyTree [Nonempty Action]
    (model : PolicyTreeModel Belief Action Observation)
    (depth : ℕ) (belief : Belief) :
    ∃ tree : PolicyTree Action Observation depth,
      policyTreeValue model tree belief = optimalTreeValue model depth belief ∧
        ∀ alternative : PolicyTree Action Observation depth,
          policyTreeValue model tree belief ≤
            policyTreeValue model alternative belief := by
  refine ⟨optimalPolicyTree model depth belief,
    optimalPolicyTree_value model depth belief, ?_⟩
  intro alternative
  rw [optimalPolicyTree_value model depth belief]
  exact optimalTreeValue_le_tree model alternative belief

/-! ## Open-loop embedding and dominance -/

/-- A depth-indexed open-loop action plan. -/
def OpenLoopPlan (Action : Type uAction) : ℕ → Type uAction
  | 0 => PUnit
  | depth + 1 => Action × OpenLoopPlan Action depth

/-- Embed an open-loop plan by reusing the same continuation after every
possible observation. -/
def openLoopEmbedding :
    {depth : ℕ} → OpenLoopPlan Action depth → PolicyTree Action Observation depth
  | 0, _ => PUnit.unit
  | _depth + 1, plan =>
      (plan.1, fun _ => openLoopEmbedding plan.2)

/-- Recursive value of an observation-ignoring action plan. -/
noncomputable def openLoopValue
    (model : PolicyTreeModel Belief Action Observation) :
    {depth : ℕ} → OpenLoopPlan Action depth → Belief → ℝ
  | 0, _, _ => 0
  | depth + 1, plan, belief =>
      model.stageCost depth belief plan.1 +
        ∑ observation,
          model.observationLaw belief plan.1 observation *
            openLoopValue model plan.2
              (model.update belief plan.1 observation)

/-- Observation-ignoring tree continuations preserve the open-loop value. -/
theorem openLoopEmbedding_value
    (model : PolicyTreeModel Belief Action Observation) :
    ∀ {depth : ℕ} (plan : OpenLoopPlan Action depth) (belief : Belief),
      policyTreeValue model (openLoopEmbedding plan) belief =
        openLoopValue model plan belief
  | 0, _, _ => rfl
  | depth + 1, plan, belief => by
      change
        model.stageCost depth belief plan.1 +
            ∑ observation,
              model.observationLaw belief plan.1 observation *
                policyTreeValue model (openLoopEmbedding plan.2)
                  (model.update belief plan.1 observation) = _
      apply congrArg
      apply Finset.sum_congr rfl
      intro observation _
      rw [openLoopEmbedding_value model plan.2]

/-- The closed-loop optimum is no worse than every embedded open-loop plan. -/
theorem optimalTree_le_openLoop [Nonempty Action]
    (model : PolicyTreeModel Belief Action Observation)
    {depth : ℕ} (plan : OpenLoopPlan Action depth) (belief : Belief) :
    optimalTreeValue model depth belief ≤ openLoopValue model plan belief := by
  rw [← openLoopEmbedding_value model plan belief]
  exact optimalTreeValue_le_tree model (openLoopEmbedding plan) belief

/-! ## Treewise expected-free-energy decomposition -/

/-- A belief-indexed finite generative model and observation update used to
lift the one-step full-support EFE identity through a policy tree. -/
structure EFEPolicyTreeModel
    (Belief State Action Observation : Type*)
    [Fintype Belief] [Fintype State] [Fintype Action] [Fintype Observation] where
  generative : Belief → GenerativeModel Action State Observation
  update : Belief → Action → Observation → Belief
  support : ∀ belief, FullSupport (generative belief)

/-- Tree model whose stage cost is one-step expected free energy. -/
noncomputable def efePolicyTreeModel
    (model : EFEPolicyTreeModel Belief State Action Observation) :
    PolicyTreeModel Belief Action Observation where
  observationLaw belief action :=
    predictedOutcome (model.generative belief) action
  update := model.update
  stageCost _ belief action :=
    expectedFreeEnergy (model.generative belief) action

/-- Same observation dynamics with stage cost written as risk plus ambiguity. -/
noncomputable def riskAmbiguityPolicyTreeModel
    (model : EFEPolicyTreeModel Belief State Action Observation) :
    PolicyTreeModel Belief Action Observation where
  observationLaw belief action :=
    predictedOutcome (model.generative belief) action
  update := model.update
  stageCost _ belief action :=
    risk (model.generative belief) action +
      ambiguity (model.generative belief) action

/-- The one-step full-support EFE identity lifts through every branch of a
finite policy tree. -/
theorem policyTree_efe_eq_risk_add_ambiguity
    (model : EFEPolicyTreeModel Belief State Action Observation) :
    ∀ {depth : ℕ} (tree : PolicyTree Action Observation depth)
      (belief : Belief),
      policyTreeValue (efePolicyTreeModel model) tree belief =
        policyTreeValue (riskAmbiguityPolicyTreeModel model) tree belief
  | 0, _, _ => rfl
  | depth + 1, tree, belief => by
      change
        expectedFreeEnergy (model.generative belief) tree.1 +
            ∑ observation,
              predictedOutcome (model.generative belief) tree.1 observation *
                policyTreeValue (efePolicyTreeModel model) (tree.2 observation)
                  (model.update belief tree.1 observation) =
          (risk (model.generative belief) tree.1 +
              ambiguity (model.generative belief) tree.1) +
            ∑ observation,
              predictedOutcome (model.generative belief) tree.1 observation *
                policyTreeValue (riskAmbiguityPolicyTreeModel model)
                  (tree.2 observation)
                  (model.update belief tree.1 observation)
      rw [expectedFreeEnergy_eq_risk_add_ambiguity
        (model.generative belief) tree.1 (model.support belief)]
      apply congrArg
      apply Finset.sum_congr rfl
      intro observation _
      rw [policyTree_efe_eq_risk_add_ambiguity model
        (tree.2 observation)]

/-- Since every tree has equal EFE and risk-plus-ambiguity values, their finite
optimal values agree as well. -/
theorem optimalEFEValue_eq_riskAmbiguity [Nonempty Action]
    (model : EFEPolicyTreeModel Belief State Action Observation)
    (depth : ℕ) (belief : Belief) :
    optimalTreeValue (efePolicyTreeModel model) depth belief =
      optimalTreeValue (riskAmbiguityPolicyTreeModel model) depth belief := by
  apply le_antisymm
  · calc
      optimalTreeValue (efePolicyTreeModel model) depth belief ≤
          policyTreeValue (efePolicyTreeModel model)
            (optimalPolicyTree (riskAmbiguityPolicyTreeModel model)
              depth belief) belief :=
        optimalTreeValue_le_tree _ _ _
      _ = policyTreeValue (riskAmbiguityPolicyTreeModel model)
            (optimalPolicyTree (riskAmbiguityPolicyTreeModel model)
              depth belief) belief :=
        policyTree_efe_eq_risk_add_ambiguity model _ _
      _ = optimalTreeValue (riskAmbiguityPolicyTreeModel model)
            depth belief :=
        optimalPolicyTree_value _ _ _
  · calc
      optimalTreeValue (riskAmbiguityPolicyTreeModel model) depth belief ≤
          policyTreeValue (riskAmbiguityPolicyTreeModel model)
            (optimalPolicyTree (efePolicyTreeModel model) depth belief) belief :=
        optimalTreeValue_le_tree _ _ _
      _ = policyTreeValue (efePolicyTreeModel model)
            (optimalPolicyTree (efePolicyTreeModel model) depth belief) belief :=
        (policyTree_efe_eq_risk_add_ambiguity model _ _).symm
      _ = optimalTreeValue (efePolicyTreeModel model) depth belief :=
        optimalPolicyTree_value _ _ _

/-! ## Exact Boolean feedback witness -/

/-- A fair first observation followed by a terminal Boolean mismatch cost. -/
noncomputable def boolFeedbackModel : PolicyTreeModel Bool Bool Bool where
  observationLaw _ _ := fairBoolLaw
  update _ _ observation := observation
  stageCost depth belief action :=
    if depth = 0 then boolMismatchCost belief action else 0

/-- The feedback tree chooses its second action from the first observation. -/
noncomputable def boolFeedbackTree : PolicyTree Bool Bool 2 :=
  (false, fun observation =>
    (observation, fun _ => PUnit.unit))

/-- A two-step open-loop plan with an arbitrary fixed second action. -/
noncomputable def boolOpenLoopPlan (action : Bool) : OpenLoopPlan Bool 2 :=
  (false, (action, PUnit.unit))

/-- Observation-contingent feedback has exact value zero. -/
theorem boolFeedbackTree_value_zero :
    policyTreeValue boolFeedbackModel boolFeedbackTree false = 0 := by
  norm_num [policyTreeValue, boolFeedbackModel, boolFeedbackTree,
    fairBoolLaw, boolMismatchCost, Fintype.sum_bool]

/-- Every fixed open-loop second action has exact value one half. -/
theorem boolOpenLoop_value_half (action : Bool) :
    openLoopValue boolFeedbackModel (boolOpenLoopPlan action) false = 1 / 2 := by
  cases action <;>
    norm_num [openLoopValue, boolFeedbackModel, boolOpenLoopPlan,
      fairBoolLaw, boolMismatchCost, Fintype.sum_bool]

/-- The closed-loop Boolean tree strictly improves on every fixed open-loop
continuation. -/
theorem boolFeedbackTree_strictlyBetter (action : Bool) :
    policyTreeValue boolFeedbackModel boolFeedbackTree false <
      openLoopValue boolFeedbackModel (boolOpenLoopPlan action) false := by
  rw [boolFeedbackTree_value_zero, boolOpenLoop_value_half]
  norm_num

end FEP.PolicyTrees
