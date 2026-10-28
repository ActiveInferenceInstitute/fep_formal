"""Lean bodies for finite closed-loop policy trees and EFE."""

from __future__ import annotations

BODIES: dict[str, str] = {
    "fep-128": """import FepSketches.policy_tree

/-! # Observation-Contingent Policy-Tree Recursion -/
namespace FEP128

open FEP.PolicyTrees

/-- A node chooses one action and then follows the continuation indexed by the
realized observation. -/
theorem fep128_policyTreeValue_node
    {Belief Action Observation : Type*}
    [Fintype Belief] [Fintype Action] [Fintype Observation]
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
  policyTreeValue_node model action continuation belief

/-- The depth-zero carrier has no action node and therefore zero value. -/
theorem fep128_policyTreeValue_leaf
    {Belief Action Observation : Type*}
    [Fintype Belief] [Fintype Action] [Fintype Observation]
    (model : PolicyTreeModel Belief Action Observation) (belief : Belief) :
    policyTreeValue (depth := 0) model
        (PUnit.unit : PolicyTree Action Observation 0) belief = 0 :=
  rfl

end FEP128
""",
    "fep-129": """import FepSketches.policy_tree

/-! # Finite Policy-Tree Bellman Minimum -/
namespace FEP129

open FEP.PolicyTrees

/-- The finite Bellman value is the selected action minimum of stage cost plus
the observation-weighted optimal continuation. -/
theorem fep129_optimalTreeValue_eq_min
    {Belief Action Observation : Type*}
    [Fintype Belief] [Fintype Action] [Fintype Observation] [Nonempty Action]
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
  optimalTreeValue_eq_min model depth belief

/-- The selected node action is no worse than any finite alternative. -/
theorem fep129_optimalTreeAction_le
    {Belief Action Observation : Type*}
    [Fintype Belief] [Fintype Action] [Fintype Observation] [Nonempty Action]
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
              (model.update belief alternative observation) :=
  optimalTreeAction_le model depth belief alternative

end FEP129
""",
    "fep-130": """import FepSketches.policy_tree

/-! # Optimal Finite Policy-Tree Existence -/
namespace FEP130

open FEP.PolicyTrees

/-- Backward induction supplies an attaining optimum on the exact finite
depth-indexed tree carrier. -/
theorem fep130_exists_optimalPolicyTree
    {Belief Action Observation : Type*}
    [Fintype Belief] [Fintype Action] [Fintype Observation] [Nonempty Action]
    (model : PolicyTreeModel Belief Action Observation)
    (depth : ℕ) (belief : Belief) :
    ∃ tree : PolicyTree Action Observation depth,
      policyTreeValue model tree belief = optimalTreeValue model depth belief ∧
        ∀ alternative : PolicyTree Action Observation depth,
          policyTreeValue model tree belief ≤
            policyTreeValue model alternative belief :=
  exists_optimalPolicyTree model depth belief

/-- The authored carrier is finite at every finite depth. -/
theorem fep130_policyTree_carrier_finite
    {Action Observation : Type*}
    [Fintype Action] [Fintype Observation] (depth : ℕ) :
    Finite (PolicyTree Action Observation depth) := by
  infer_instance

end FEP130
""",
    "fep-131": """import FepSketches.policy_tree

/-! # Open-Loop Plan Embedding -/
namespace FEP131

open FEP.PolicyTrees

/-- Reusing the same continuation after every observation embeds an open-loop
plan without changing its recursive value. -/
theorem fep131_openLoopEmbedding_value
    {Belief Action Observation : Type*}
    [Fintype Belief] [Fintype Action] [Fintype Observation]
    (model : PolicyTreeModel Belief Action Observation)
    {depth : ℕ} (plan : OpenLoopPlan Action depth) (belief : Belief) :
    policyTreeValue model
        (openLoopEmbedding (Observation := Observation) plan) belief =
      openLoopValue model plan belief :=
  openLoopEmbedding_value model plan belief

/-- At depth zero, the embedding maps the unique empty plan to the unique
policy-tree leaf. -/
theorem fep131_openLoopEmbedding_leaf
    {Action Observation : Type*} :
    openLoopEmbedding (depth := 0) (Action := Action) (Observation := Observation)
        (PUnit.unit : OpenLoopPlan Action 0) =
      (PUnit.unit : PolicyTree Action Observation 0) :=
  rfl

end FEP131
""",
    "fep-132": """import FepSketches.policy_tree

/-! # Closed-Loop Dominance over Open Loop -/
namespace FEP132

open FEP.PolicyTrees

/-- The finite closed-loop optimum is no worse than any observation-ignoring
open-loop plan embedded at the same depth. -/
theorem fep132_optimalTree_le_openLoop
    {Belief Action Observation : Type*}
    [Fintype Belief] [Fintype Action] [Fintype Observation] [Nonempty Action]
    (model : PolicyTreeModel Belief Action Observation)
    {depth : ℕ} (plan : OpenLoopPlan Action depth) (belief : Belief) :
    optimalTreeValue model depth belief ≤ openLoopValue model plan belief :=
  optimalTree_le_openLoop model plan belief

/-- Dominance compares equal finite horizons; it does not assert an
infinite-horizon POMDP optimum. -/
theorem fep132_finite_horizon_depth (depth : ℕ) : depth < depth + 1 :=
  Nat.lt_succ_self depth

end FEP132
""",
    "fep-133": """import FepSketches.policy_tree

/-! # Treewise EFE Decomposition -/
namespace FEP133

open FEP.PolicyTrees

/-- The one-step full-support EFE identity lifts through every branch of a
finite observation-contingent tree. -/
theorem fep133_policyTree_efe_eq_risk_add_ambiguity
    {Belief State Action Observation : Type*}
    [Fintype Belief] [Fintype State] [Fintype Action] [Fintype Observation]
    (model : EFEPolicyTreeModel Belief State Action Observation)
    {depth : ℕ} (tree : PolicyTree Action Observation depth)
    (belief : Belief) :
    policyTreeValue (efePolicyTreeModel model) tree belief =
      policyTreeValue (riskAmbiguityPolicyTreeModel model) tree belief :=
  policyTree_efe_eq_risk_add_ambiguity model tree belief

/-- Consequently, the finite optimal EFE and optimal risk-plus-ambiguity
values agree. -/
theorem fep133_optimalValues_agree
    {Belief State Action Observation : Type*}
    [Fintype Belief] [Fintype State] [Fintype Action] [Fintype Observation]
    [Nonempty Action]
    (model : EFEPolicyTreeModel Belief State Action Observation)
    (depth : ℕ) (belief : Belief) :
    optimalTreeValue (efePolicyTreeModel model) depth belief =
      optimalTreeValue (riskAmbiguityPolicyTreeModel model) depth belief :=
  optimalEFEValue_eq_riskAmbiguity model depth belief

end FEP133
""",
    "fep-134": """import FepSketches.policy_tree

/-! # Strict Boolean Feedback Advantage -/
namespace FEP134

open FEP.PolicyTrees

/-- Observation-contingent Boolean feedback has value zero, every fixed
open-loop continuation has value one half, and the comparison is strict. -/
theorem fep134_boolFeedback_strictlyBetter (action : Bool) :
    policyTreeValue boolFeedbackModel boolFeedbackTree false = 0 ∧
      openLoopValue boolFeedbackModel (boolOpenLoopPlan action) false = 1 / 2 ∧
      policyTreeValue boolFeedbackModel boolFeedbackTree false <
        openLoopValue boolFeedbackModel (boolOpenLoopPlan action) false :=
  ⟨boolFeedbackTree_value_zero, boolOpenLoop_value_half action,
    boolFeedbackTree_strictlyBetter action⟩

/-- The witness is genuinely closed loop: its second action changes with the
first observation. -/
theorem fep134_feedback_continuation_changes :
    (boolFeedbackTree.2 false).1 ≠ (boolFeedbackTree.2 true).1 := by
  decide

end FEP134
""",
}
