"""Canonical Lean bodies for control and planning as inference."""

from __future__ import annotations

BODIES: dict[str, str] = {
    "fep-065": """import FepSketches.controlled_markov

namespace FEP065

open FEP FEP.ControlledMarkov Finset
open scoped BigOperators

variable {State Action : Type*} [Fintype State] [Fintype Action]

/-- Every action-conditioned Markov row is a normalized finite law. -/
theorem fep065_controlledKernel_normalization
    (transition : ControlledKernel State Action)
    (action : Action) (state : State) :
    ∑ nextState, transition action state nextState = 1 :=
  controlledKernel_sum_one transition action state

end FEP065
""",
    "fep-066": """import FepSketches.controlled_markov

namespace FEP066

open FEP FEP.ControlledMarkov Finset
open scoped BigOperators

variable {State Action Observation : Type*}
  [Fintype State] [Fintype Action] [Fintype Observation]

/-- A positive-evidence action-conditioned Bayes update reconstructs its
predicted state-observation joint mass. -/
theorem fep066_actionConditioned_bayes_reconstruction
    (prior : FiniteLaw State) (transition : ControlledKernel State Action)
    (emission : FiniteKernel State Observation) (action : Action)
    (observation : Observation)
    (hEvidence : 0 < actionEvidence prior transition emission action observation)
    (state : State) :
    actionBeliefUpdate prior transition emission action observation hEvidence state *
        actionEvidence prior transition emission action observation =
      actionPrediction prior transition action state * emission state observation :=
  actionBeliefUpdate_reconstruction prior transition emission action observation
    hEvidence state

/-- The same positive-evidence update is normalized. -/
theorem fep066_actionConditioned_update_normalized
    (prior : FiniteLaw State) (transition : ControlledKernel State Action)
    (emission : FiniteKernel State Observation) (action : Action)
    (observation : Observation)
    (hEvidence : 0 < actionEvidence prior transition emission action observation) :
    ∑ state,
      actionBeliefUpdate prior transition emission action observation hEvidence state =
        1 :=
  actionBeliefUpdate_sum_one prior transition emission action observation hEvidence

/-- A zero-evidence observation cannot be passed to the normalized update. -/
theorem fep066_zero_evidence_boundary
    (prior : FiniteLaw State) (transition : ControlledKernel State Action)
    (emission : FiniteKernel State Observation) (action : Action)
    (observation : Observation)
    (hZero : actionEvidence prior transition emission action observation = 0) :
    ¬0 < actionEvidence prior transition emission action observation :=
  actionEvidence_zero_boundary prior transition emission action observation hZero

end FEP066
""",
    "fep-067": """import FepSketches.controlled_markov

namespace FEP067

open FEP FEP.ControlledMarkov

variable {Belief State Action Observation : Type*}
  [Fintype Belief] [Fintype State] [Fintype Action] [Fintype Observation]
  [DecidableEq Belief]

/-- A finite reachable belief index denotes a finite law; expanding that
interpretation preserves every finite-horizon feedback-policy value. -/
theorem fep067_reachableBelief_policyValue_equivalence
    (model : ReachableBeliefPOMDP Belief State Action Observation)
    (stateCost : State → Action → ℝ) (policy : ℕ → Belief → Action)
    (horizon : ℕ) (belief : Belief) :
    reducedPolicyValue model stateCost policy horizon belief =
      interpretedPolicyValue model stateCost policy horizon belief :=
  reachableBelief_policyValue_eq model stateCost policy horizon belief

/-- The concrete two-index Boolean model satisfies the exact positive-evidence
Bayesian update required by the reachable reduction. -/
theorem fep067_bool_reachable_update
    (belief action observation : Bool)
    (hEvidence : 0 < actionEvidence
      (boolReachablePOMDP.interpret belief) boolReachablePOMDP.transition
      boolReachablePOMDP.emission action observation) :
    boolReachablePOMDP.interpret
        (boolReachablePOMDP.update belief action observation) =
      actionBeliefUpdate (boolReachablePOMDP.interpret belief)
        boolReachablePOMDP.transition boolReachablePOMDP.emission action observation
        hEvidence :=
  boolReachablePOMDP_update_sound belief action observation hEvidence

end FEP067
""",
    "fep-068": """import FepSketches.controlled_markov

namespace FEP068

open FEP FEP.ControlledMarkov Finset
open scoped BigOperators

variable {State Action : Type*}
  [Fintype State] [Fintype Action] [Nonempty Action]

/-- At positive temperature, every finite soft Bellman backup has a positive
partition, satisfies its exact recursion, and lies below each hard action
energy. -/
theorem fep068_softBellman_recursion (temperature : ℝ)
    (hTemperature : 0 < temperature) (stageCost : State → Action → ℝ)
    (transition : ControlledKernel State Action)
    (horizon : ℕ) (state : State) :
    (0 < ∑ action,
      Real.exp (-((softBellmanActionEnergy temperature stageCost transition
        horizon state action) / temperature))) ∧
    (softBellmanValue temperature stageCost transition (horizon + 1) state =
      -temperature * Real.log
        (∑ action,
          Real.exp (-((softBellmanActionEnergy temperature stageCost transition
            horizon state action) / temperature)))) ∧
    ∀ action,
      softBellmanValue temperature stageCost transition (horizon + 1) state ≤
        softBellmanActionEnergy temperature stageCost transition
          horizon state action := by
  exact
    ⟨softBellmanValue_partition_pos temperature stageCost transition horizon state,
      softBellmanValue_succ temperature stageCost transition horizon state,
      fun action ↦ softBellmanValue_le_actionEnergy temperature hTemperature
        stageCost transition horizon state action⟩

end FEP068
""",
    "fep-069": """import FepSketches.controlled_markov

namespace FEP069

open FEP FEP.ControlledMarkov Finset
open scoped BigOperators

variable {State : Type*} [Fintype State]

/-- One KL-control desirability backup is an exponential state-cost tilt of
the passive-kernel prediction. -/
theorem fep069_desirability_recursion
    (passive : FiniteKernel State State) (stateCost desirability : State → ℝ)
    (state : State) :
    desirabilityStep passive stateCost desirability state =
      Real.exp (-stateCost state) *
        ∑ nextState, passive state nextState * desirability nextState :=
  rfl

/-- The desirability recursion preserves nonnegativity. -/
theorem fep069_desirability_nonnegative
    (passive : FiniteKernel State State) (stateCost desirability : State → ℝ)
    (hDesirability : ∀ state, 0 ≤ desirability state) (state : State) :
    0 ≤ desirabilityStep passive stateCost desirability state :=
  desirabilityStep_nonneg passive stateCost desirability hDesirability state

/-- Zero state cost and unit desirability give an exact normalized fixed point. -/
theorem fep069_zeroCost_unitDesirability
    (passive : FiniteKernel State State) (state : State) :
    desirabilityStep passive (fun _ => 0) (fun _ => 1) state = 1 :=
  desirabilityStep_zero_cost_one passive state

end FEP069
""",
    "fep-070": """import FepSketches.controlled_markov

namespace FEP070

open FEP FEP.ControlledMarkov Finset
open scoped BigOperators

variable {Action : Type*} [Fintype Action]

/-- The prior-weighted exponential control posterior is a normalized finite
action law. -/
theorem fep070_controlPosterior_normalized (prior : FiniteLaw Action)
    (precision : ℝ) (cost : Action → ℝ) :
    ∑ action, controlPosterior prior precision cost action = 1 :=
  controlPosterior_sum_one prior precision cost

/-- Posterior control mass reconstructs its prior-weighted exponential score. -/
theorem fep070_controlPosterior_reconstruction (prior : FiniteLaw Action)
    (precision : ℝ) (cost : Action → ℝ) (action : Action) :
    controlPosterior prior precision cost action *
        boltzmannPartition prior (fun candidate => precision * cost candidate) =
      boltzmannWeight prior (fun candidate => precision * cost candidate) action :=
  boltzmannPosterior_mul_partition prior
    (fun candidate => precision * cost candidate) action

/-- Zero control cost leaves the prior action law unchanged. -/
theorem fep070_zeroCost_posterior_eq_prior (prior : FiniteLaw Action)
    (precision : ℝ) :
    controlPosterior prior precision (fun _ => 0) = prior :=
  controlPosterior_zero_cost prior precision

end FEP070
""",
    "fep-071": """import FepSketches.controlled_markov

namespace FEP071

open FEP FEP.ControlledMarkov Finset
open scoped BigOperators

variable {Belief Action Observation : Type*}
  [Fintype Belief] [Fintype Action] [Fintype Observation] [Nonempty Action]

/-- Sophisticated expected free energy applies a new finite minimum after the
observation-dependent continuation at every backward-induction node. -/
theorem fep071_sophisticatedEFE_backward_step
    (model : SophisticatedEFEModel Belief Action Observation)
    (horizon : ℕ) (belief : Belief) :
    sophisticatedEFEValue model (horizon + 1) belief =
      model.stageEFE horizon belief (sophisticatedEFEAction model horizon belief) +
        ∑ observation,
          model.observationLaw belief (sophisticatedEFEAction model horizon belief)
              observation *
            sophisticatedEFEValue model horizon
              (model.update belief (sophisticatedEFEAction model horizon belief)
                observation) :=
  sophisticatedEFEValue_succ model horizon belief

/-- In the exact two-stage Boolean witness, different observations select
different second-stage actions. -/
theorem fep071_twoStage_feedback_changes_action :
    twoStageFeedback false ≠ twoStageFeedback true :=
  twoStageFeedback_changes_action

/-- The observation-dependent second action strictly improves on every fixed
open-loop Boolean action. -/
theorem fep071_twoStage_feedback_strictly_better (action : Bool) :
    twoStageFeedbackExpectedCost < twoStageOpenLoopExpectedCost action :=
  twoStageFeedback_beats_openLoop action

end FEP071
""",
}
