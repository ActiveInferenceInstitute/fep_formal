module
public import FepSketches.families.closed_loop_policy_trees
public import FepSketches.families.controlled_markov
public import FepSketches.families.core_active_inference
public import FepSketches.policy_tree

@[expose] public section

/-!
# Closed-loop policy-tree topic compositions

These witnesses place depth-indexed observation-contingent trees beside the
earlier finite minimization, Bellman, EFE, and sophisticated-planning topics.
The conjunctions preserve the distinct real and `ENNReal` value carriers and
do not assert infinite-horizon POMDP optimality.
-/

namespace FEPComposed

open FEP FEP.ActiveInference FEP.ControlledMarkov FEP.PolicyTrees Finset
open scoped BigOperators ENNReal

/-- The explicit policy-tree node recursion is paired with the earlier
sophisticated-EFE observation-contingent backward step. -/
theorem fep128_policyTreeRecursion_extends_fep071
    {Belief Action Observation : Type*}
    [Fintype Belief] [Fintype Action] [Fintype Observation] [Nonempty Action]
    (treeModel : PolicyTreeModel Belief Action Observation)
    {depth : ℕ} (action : Action)
    (continuation : Observation → PolicyTree Action Observation depth)
    (belief : Belief)
    (sophisticatedModel : SophisticatedEFEModel Belief Action Observation)
    (sophisticatedDepth : ℕ) (sophisticatedBelief : Belief) :
    (policyTreeValue (depth := depth + 1) treeModel (action, continuation) belief =
      treeModel.stageCost depth belief action +
        ∑ observation,
          treeModel.observationLaw belief action observation *
            policyTreeValue treeModel (continuation observation)
              (treeModel.update belief action observation)) ∧
      (sophisticatedEFEValue sophisticatedModel
          (sophisticatedDepth + 1) sophisticatedBelief =
        sophisticatedModel.stageEFE sophisticatedDepth sophisticatedBelief
            (sophisticatedEFEAction sophisticatedModel sophisticatedDepth
              sophisticatedBelief) +
          ∑ observation,
            sophisticatedModel.observationLaw sophisticatedBelief
                (sophisticatedEFEAction sophisticatedModel sophisticatedDepth
                  sophisticatedBelief) observation *
              sophisticatedEFEValue sophisticatedModel sophisticatedDepth
                (sophisticatedModel.update sophisticatedBelief
                  (sophisticatedEFEAction sophisticatedModel sophisticatedDepth
                    sophisticatedBelief) observation)) := by
  exact
    ⟨fep_fep128.FEP128.fep128_policyTreeValue_node
        treeModel action continuation belief,
      fep_fep071.FEP071.fep071_sophisticatedEFE_backward_step
        sophisticatedModel sophisticatedDepth sophisticatedBelief⟩

/-- The finite action minimum in a tree node is paired with both the original
transition Bellman recursion and the earlier observation-contingent EFE step. -/
theorem fep129_policyTreeBellman_extends_fep033
    {Belief Action Observation OldState : Type*}
    [Fintype Belief] [Fintype Action] [Fintype Observation] [Nonempty Action]
    (treeModel : PolicyTreeModel Belief Action Observation)
    (depth : ℕ) (belief : Belief)
    (discount : ENNReal) (oldStageCost : OldState → ENNReal)
    (step : OldState → OldState) (terminalCost : OldState → ENNReal)
    (oldDepth : ℕ) (oldState : OldState)
    (sophisticatedModel : SophisticatedEFEModel Belief Action Observation)
    (sophisticatedDepth : ℕ) (sophisticatedBelief : Belief) :
    (optimalTreeValue treeModel (depth + 1) belief =
      treeModel.stageCost depth belief (optimalTreeAction treeModel depth belief) +
        ∑ observation,
          treeModel.observationLaw belief
              (optimalTreeAction treeModel depth belief) observation *
            optimalTreeValue treeModel depth
              (treeModel.update belief
                (optimalTreeAction treeModel depth belief) observation)) ∧
      ((fep_fep033.FEP033.fep033_value
          discount oldStageCost step terminalCost (oldDepth + 1) oldState =
        oldStageCost oldState + discount *
          fep_fep033.FEP033.fep033_value
            discount oldStageCost step terminalCost oldDepth (step oldState)) ∧
        sophisticatedEFEValue sophisticatedModel
            (sophisticatedDepth + 1) sophisticatedBelief =
          sophisticatedModel.stageEFE sophisticatedDepth sophisticatedBelief
              (sophisticatedEFEAction sophisticatedModel sophisticatedDepth
                sophisticatedBelief) +
            ∑ observation,
              sophisticatedModel.observationLaw sophisticatedBelief
                  (sophisticatedEFEAction sophisticatedModel sophisticatedDepth
                    sophisticatedBelief) observation *
                sophisticatedEFEValue sophisticatedModel sophisticatedDepth
                  (sophisticatedModel.update sophisticatedBelief
                    (sophisticatedEFEAction sophisticatedModel
                      sophisticatedDepth sophisticatedBelief) observation)) := by
  exact
    ⟨fep_fep129.FEP129.fep129_optimalTreeValue_eq_min treeModel depth belief,
      ⟨fep_fep033.FEP033.fep033_bellman
          discount oldStageCost step terminalCost oldDepth oldState,
        fep_fep071.FEP071.fep071_sophisticatedEFE_backward_step
          sophisticatedModel sophisticatedDepth sophisticatedBelief⟩⟩

/-- Backward induction on the depth-indexed tree is paired with the original
finite-policy minimizer and sophisticated-EFE recursion. -/
theorem fep130_optimalPolicyTree_extends_fep008
    {Belief Action Observation : Type*}
    [Fintype Belief] [Fintype Action] [Fintype Observation] [Nonempty Action]
    (treeModel : PolicyTreeModel Belief Action Observation)
    (depth : ℕ) (belief : Belief)
    (policies : Finset fep_fep008.FEP008.Policy)
    (policiesNonempty : policies.Nonempty)
    (objective : fep_fep008.FEP008.Policy → ℝ)
    (sophisticatedModel : SophisticatedEFEModel Belief Action Observation)
    (sophisticatedDepth : ℕ) (sophisticatedBelief : Belief) :
    (∃ tree : PolicyTree Action Observation depth,
      policyTreeValue treeModel tree belief =
          optimalTreeValue treeModel depth belief ∧
        ∀ alternative : PolicyTree Action Observation depth,
          policyTreeValue treeModel tree belief ≤
            policyTreeValue treeModel alternative belief) ∧
      ((∃ policy ∈ policies, ∀ alternative ∈ policies,
        objective policy ≤ objective alternative) ∧
        sophisticatedEFEValue sophisticatedModel
            (sophisticatedDepth + 1) sophisticatedBelief =
          sophisticatedModel.stageEFE sophisticatedDepth sophisticatedBelief
              (sophisticatedEFEAction sophisticatedModel sophisticatedDepth
                sophisticatedBelief) +
            ∑ observation,
              sophisticatedModel.observationLaw sophisticatedBelief
                  (sophisticatedEFEAction sophisticatedModel sophisticatedDepth
                    sophisticatedBelief) observation *
                sophisticatedEFEValue sophisticatedModel sophisticatedDepth
                  (sophisticatedModel.update sophisticatedBelief
                    (sophisticatedEFEAction sophisticatedModel
                      sophisticatedDepth sophisticatedBelief) observation)) := by
  exact
    ⟨fep_fep130.FEP130.fep130_exists_optimalPolicyTree
        treeModel depth belief,
      ⟨fep_fep008.FEP008.fep008_exists_minG
          policies policiesNonempty objective,
        fep_fep071.FEP071.fep071_sophisticatedEFE_backward_step
          sophisticatedModel sophisticatedDepth sophisticatedBelief⟩⟩

/-- Value preservation for the observation-ignoring embedding is paired with
the original Bellman recursion and sophisticated-EFE backward step. -/
theorem fep131_openLoopEmbedding_extends_fep033
    {Belief Action Observation OldState : Type*}
    [Fintype Belief] [Fintype Action] [Fintype Observation] [Nonempty Action]
    (treeModel : PolicyTreeModel Belief Action Observation)
    {depth : ℕ} (plan : OpenLoopPlan Action depth) (belief : Belief)
    (discount : ENNReal) (oldStageCost : OldState → ENNReal)
    (step : OldState → OldState) (terminalCost : OldState → ENNReal)
    (oldDepth : ℕ) (oldState : OldState)
    (sophisticatedModel : SophisticatedEFEModel Belief Action Observation)
    (sophisticatedDepth : ℕ) (sophisticatedBelief : Belief) :
    (policyTreeValue treeModel
        (openLoopEmbedding (Observation := Observation) plan) belief =
      openLoopValue treeModel plan belief) ∧
      ((fep_fep033.FEP033.fep033_value
          discount oldStageCost step terminalCost (oldDepth + 1) oldState =
        oldStageCost oldState + discount *
          fep_fep033.FEP033.fep033_value
            discount oldStageCost step terminalCost oldDepth (step oldState)) ∧
        sophisticatedEFEValue sophisticatedModel
            (sophisticatedDepth + 1) sophisticatedBelief =
          sophisticatedModel.stageEFE sophisticatedDepth sophisticatedBelief
              (sophisticatedEFEAction sophisticatedModel sophisticatedDepth
                sophisticatedBelief) +
            ∑ observation,
              sophisticatedModel.observationLaw sophisticatedBelief
                  (sophisticatedEFEAction sophisticatedModel sophisticatedDepth
                    sophisticatedBelief) observation *
                sophisticatedEFEValue sophisticatedModel sophisticatedDepth
                  (sophisticatedModel.update sophisticatedBelief
                    (sophisticatedEFEAction sophisticatedModel
                      sophisticatedDepth sophisticatedBelief) observation)) := by
  exact
    ⟨fep_fep131.FEP131.fep131_openLoopEmbedding_value
        treeModel plan belief,
      ⟨fep_fep033.FEP033.fep033_bellman
          discount oldStageCost step terminalCost oldDepth oldState,
        fep_fep071.FEP071.fep071_sophisticatedEFE_backward_step
          sophisticatedModel sophisticatedDepth sophisticatedBelief⟩⟩

/-- Closed-loop dominance over an embedded open-loop plan is paired with the
earlier strict two-stage Boolean feedback advantage. -/
theorem fep132_closedLoopDominance_extends_fep071
    {Belief Action Observation : Type*}
    [Fintype Belief] [Fintype Action] [Fintype Observation] [Nonempty Action]
    (treeModel : PolicyTreeModel Belief Action Observation)
    {depth : ℕ} (plan : OpenLoopPlan Action depth) (belief : Belief)
    (fixedBooleanAction : Bool) :
    (optimalTreeValue treeModel depth belief ≤
      openLoopValue treeModel plan belief) ∧
      (twoStageFeedbackExpectedCost <
        twoStageOpenLoopExpectedCost fixedBooleanAction) := by
  exact
    ⟨fep_fep132.FEP132.fep132_optimalTree_le_openLoop
        treeModel plan belief,
      fep_fep071.FEP071.fep071_twoStage_feedback_strictly_better
        fixedBooleanAction⟩

/-- Treewise real-valued EFE decomposition is paired with the original
truncated-`ENNReal` epistemic balance and sophisticated-EFE recursion. -/
theorem fep133_treewiseEFE_extends_fep021
    {Belief State Action Observation : Type*}
    [Fintype Belief] [Fintype State] [Fintype Action]
    [Fintype Observation] [Nonempty Action]
    (treeModel : EFEPolicyTreeModel Belief State Action Observation)
    {depth : ℕ} (tree : PolicyTree Action Observation depth)
    (belief : Belief)
    {pragmaticCost epistemicValue : ENNReal}
    (epistemicAtMostPragmatic : epistemicValue ≤ pragmaticCost)
    (sophisticatedModel : SophisticatedEFEModel Belief Action Observation)
    (sophisticatedDepth : ℕ) (sophisticatedBelief : Belief) :
    (policyTreeValue (efePolicyTreeModel treeModel) tree belief =
      policyTreeValue (riskAmbiguityPolicyTreeModel treeModel) tree belief) ∧
      ((fep_fep021.FEP021.fep021_expectedFreeEnergy
          pragmaticCost epistemicValue + epistemicValue = pragmaticCost) ∧
        sophisticatedEFEValue sophisticatedModel
            (sophisticatedDepth + 1) sophisticatedBelief =
          sophisticatedModel.stageEFE sophisticatedDepth sophisticatedBelief
              (sophisticatedEFEAction sophisticatedModel sophisticatedDepth
                sophisticatedBelief) +
            ∑ observation,
              sophisticatedModel.observationLaw sophisticatedBelief
                  (sophisticatedEFEAction sophisticatedModel sophisticatedDepth
                    sophisticatedBelief) observation *
                sophisticatedEFEValue sophisticatedModel sophisticatedDepth
                  (sophisticatedModel.update sophisticatedBelief
                    (sophisticatedEFEAction sophisticatedModel
                      sophisticatedDepth sophisticatedBelief) observation)) := by
  exact
    ⟨fep_fep133.FEP133.fep133_policyTree_efe_eq_risk_add_ambiguity
        treeModel tree belief,
      ⟨fep_fep021.FEP021.fep021_efe_epistemic_balance
          epistemicAtMostPragmatic,
        fep_fep071.FEP071.fep071_sophisticatedEFE_backward_step
          sophisticatedModel sophisticatedDepth sophisticatedBelief⟩⟩

/-- The new exact zero-versus-one-half Boolean policy-tree witness is paired
with the earlier strict two-stage feedback result. -/
theorem fep134_feedbackWitness_extends_fep071 (action : Bool) :
    (policyTreeValue boolFeedbackModel boolFeedbackTree false = 0 ∧
      openLoopValue boolFeedbackModel (boolOpenLoopPlan action) false = 1 / 2 ∧
      policyTreeValue boolFeedbackModel boolFeedbackTree false <
        openLoopValue boolFeedbackModel (boolOpenLoopPlan action) false) ∧
      (twoStageFeedbackExpectedCost < twoStageOpenLoopExpectedCost action) := by
  exact
    ⟨fep_fep134.FEP134.fep134_boolFeedback_strictlyBetter action,
      fep_fep071.FEP071.fep071_twoStage_feedback_strictly_better action⟩

/-- An actual attaining tree dominates every embedded open-loop plan at the same depth. -/
theorem fep130_attaining_tree_dominates_fep131_embedded_plans
    {Belief Action Observation : Type*}
    [Fintype Belief] [Fintype Action] [Fintype Observation] [Nonempty Action]
    (model : PolicyTreeModel Belief Action Observation) (depth : ℕ) (belief : Belief) :
    ∃ tree : PolicyTree Action Observation depth,
      policyTreeValue model tree belief = optimalTreeValue model depth belief ∧
      ∀ plan : OpenLoopPlan Action depth,
        policyTreeValue model tree belief ≤ openLoopValue model plan belief := by
  obtain ⟨tree, attained, dominates⟩ :=
    fep_fep130.FEP130.fep130_exists_optimalPolicyTree model depth belief
  refine ⟨tree, attained, ?_⟩
  intro plan
  have comparison := dominates (openLoopEmbedding (Observation := Observation) plan)
  rw [fep_fep131.FEP131.fep131_openLoopEmbedding_value model plan belief] at comparison
  exact comparison

end FEPComposed
