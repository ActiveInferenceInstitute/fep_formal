import FepSketches.active_inference

/-!
# Controlled finite Markov models and planning as inference

This module keeps control, filtering, and planning on the normalized
`FiniteLaw`/`FiniteKernel` substrate.  A finite belief carrier is an index into
interpreted laws, not an enumeration of the probability simplex.  Bayesian
updates require positive evidence, finite-horizon value preservation is proved
by induction, and feedback is distinguished from an open-loop action by an
exact two-stage Boolean witness.
-/

namespace FEP.ControlledMarkov

open FEP FEP.ActiveInference Finset
open scoped BigOperators

variable {State Action Observation Belief : Type*}
  [Fintype State] [Fintype Action] [Fintype Observation] [Fintype Belief]

/-- An action-indexed family of normalized state-transition kernels. -/
abbrev ControlledKernel (State Action : Type*)
    [Fintype State] [Fintype Action] :=
  Action → FiniteKernel State State

/-- Every action and current state select a normalized next-state law. -/
theorem controlledKernel_sum_one
    (transition : ControlledKernel State Action)
    (action : Action) (state : State) :
    ∑ nextState, transition action state nextState = 1 :=
  (transition action).sum_one state

/-- Predict a state law through one selected controlled transition. -/
def actionPrediction (prior : FiniteLaw State)
    (transition : ControlledKernel State Action) (action : Action) :
    FiniteLaw State :=
  (transition action).predictive prior

/-- Predict the observation law after one selected controlled transition. -/
def actionObservationLaw (prior : FiniteLaw State)
    (transition : ControlledKernel State Action)
    (emission : FiniteKernel State Observation) (action : Action) :
    FiniteLaw Observation :=
  emission.predictive (actionPrediction prior transition action)

/-- Evidence mass of one observation under a selected action. -/
def actionEvidence (prior : FiniteLaw State)
    (transition : ControlledKernel State Action)
    (emission : FiniteKernel State Observation) (action : Action)
    (observation : Observation) : ℝ :=
  actionObservationLaw prior transition emission action observation

/-- Exact action-conditioned Bayesian update at positive evidence. -/
noncomputable def actionBeliefUpdate (prior : FiniteLaw State)
    (transition : ControlledKernel State Action)
    (emission : FiniteKernel State Observation) (action : Action)
    (observation : Observation)
    (hEvidence : 0 < actionEvidence prior transition emission action observation) :
    FiniteLaw State :=
  emission.posterior (actionPrediction prior transition action)
    observation hEvidence

/-- Action-conditioned posterior mass reconstructs the predicted joint mass. -/
theorem actionBeliefUpdate_reconstruction (prior : FiniteLaw State)
    (transition : ControlledKernel State Action)
    (emission : FiniteKernel State Observation) (action : Action)
    (observation : Observation)
    (hEvidence : 0 < actionEvidence prior transition emission action observation)
    (state : State) :
    actionBeliefUpdate prior transition emission action observation hEvidence state *
        actionEvidence prior transition emission action observation =
      actionPrediction prior transition action state * emission state observation := by
  exact FiniteKernel.posterior_mul_predictive
    (actionPrediction prior transition action) emission observation hEvidence state

/-- The action-conditioned Bayesian update is a normalized finite law. -/
theorem actionBeliefUpdate_sum_one (prior : FiniteLaw State)
    (transition : ControlledKernel State Action)
    (emission : FiniteKernel State Observation) (action : Action)
    (observation : Observation)
    (hEvidence : 0 < actionEvidence prior transition emission action observation) :
    ∑ state,
        actionBeliefUpdate prior transition emission action observation hEvidence state =
      1 :=
  (actionBeliefUpdate prior transition emission action observation hEvidence).sum_one

/-- A zero-evidence observation is explicitly outside the Bayesian update's
positive-denominator construction boundary. -/
theorem actionEvidence_zero_boundary (prior : FiniteLaw State)
    (transition : ControlledKernel State Action)
    (emission : FiniteKernel State Observation) (action : Action)
    (observation : Observation)
    (hZero : actionEvidence prior transition emission action observation = 0) :
    ¬0 < actionEvidence prior transition emission action observation := by
  rw [hZero]
  exact lt_irrefl 0

/-- A finite reachable-belief POMDP indexes only selected belief laws.  The
update-soundness field states the exact positive-evidence Bayes boundary; no
claim is made that the full probability simplex is finite. -/
structure ReachableBeliefPOMDP
    (Belief State Action Observation : Type*)
    [Fintype Belief] [Fintype State] [Fintype Action] [Fintype Observation] where
  initial : Belief
  reachable : Finset Belief
  initial_mem : initial ∈ reachable
  interpret : Belief → FiniteLaw State
  transition : ControlledKernel State Action
  emission : FiniteKernel State Observation
  update : Belief → Action → Observation → Belief
  update_mem : ∀ belief ∈ reachable, ∀ action observation,
    0 < actionEvidence (interpret belief) transition emission action observation →
      update belief action observation ∈ reachable
  update_sound : ∀ belief action observation
      (hEvidence :
        0 < actionEvidence (interpret belief) transition emission action observation),
    interpret (update belief action observation) =
      actionBeliefUpdate (interpret belief) transition emission action observation
        hEvidence

/-- The observation pushforward and deterministic update induce a normalized
controlled kernel on finite belief indexes. -/
def reachableBeliefKernel [DecidableEq Belief]
    (model : ReachableBeliefPOMDP Belief State Action Observation)
    (action : Action) : FiniteKernel Belief Belief where
  mass belief nextBelief :=
    (actionObservationLaw (model.interpret belief) model.transition
      model.emission action).map (model.update belief action) nextBelief
  nonneg belief nextBelief :=
    ((actionObservationLaw (model.interpret belief) model.transition
      model.emission action).map (model.update belief action)).nonneg nextBelief
  sum_one belief :=
    ((actionObservationLaw (model.interpret belief) model.transition
      model.emission action).map (model.update belief action)).sum_one

/-- Expected latent stage cost represented at one belief index. -/
noncomputable def interpretedStageCost
    (model : ReachableBeliefPOMDP Belief State Action Observation)
    (stateCost : State → Action → ℝ) (belief : Belief) (action : Action) : ℝ :=
  ∑ state, model.interpret belief state * stateCost state action

/-- Finite-horizon policy value on the reachable belief-index reduction. -/
noncomputable def reducedPolicyValue [DecidableEq Belief]
    (model : ReachableBeliefPOMDP Belief State Action Observation)
    (stateCost : State → Action → ℝ) (policy : ℕ → Belief → Action) :
    ℕ → Belief → ℝ
  | 0, _ => 0
  | horizon + 1, belief =>
      interpretedStageCost model stateCost belief (policy horizon belief) +
        ∑ nextBelief,
          reachableBeliefKernel model (policy horizon belief) belief nextBelief *
            reducedPolicyValue model stateCost policy horizon nextBelief

/-- The same finite-horizon value with the belief interpretation expanded into
its latent-state expectation. -/
noncomputable def interpretedPolicyValue [DecidableEq Belief]
    (model : ReachableBeliefPOMDP Belief State Action Observation)
    (stateCost : State → Action → ℝ) (policy : ℕ → Belief → Action) :
    ℕ → Belief → ℝ
  | 0, _ => 0
  | horizon + 1, belief =>
      (∑ state,
        model.interpret belief state * stateCost state (policy horizon belief)) +
        ∑ nextBelief,
          reachableBeliefKernel model (policy horizon belief) belief nextBelief *
            interpretedPolicyValue model stateCost policy horizon nextBelief

/-- Interpreting each finite belief index preserves every finite-horizon
feedback-policy value exactly. -/
theorem reachableBelief_policyValue_eq [DecidableEq Belief]
    (model : ReachableBeliefPOMDP Belief State Action Observation)
    (stateCost : State → Action → ℝ) (policy : ℕ → Belief → Action)
    (horizon : ℕ) (belief : Belief) :
    reducedPolicyValue model stateCost policy horizon belief =
      interpretedPolicyValue model stateCost policy horizon belief := by
  induction horizon generalizing belief with
  | zero => rfl
  | succ horizon inductionHypothesis =>
      simp only [reducedPolicyValue, interpretedPolicyValue,
        interpretedStageCost]
      have hContinuation :
          (∑ nextBelief,
            reachableBeliefKernel model (policy horizon belief) belief nextBelief *
              reducedPolicyValue model stateCost policy horizon nextBelief) =
            ∑ nextBelief,
              reachableBeliefKernel model (policy horizon belief) belief nextBelief *
                interpretedPolicyValue model stateCost policy horizon nextBelief := by
        apply Finset.sum_congr rfl
        intro nextBelief _
        rw [inductionHypothesis nextBelief]
      rw [hContinuation]

/-! ## Prior-weighted Boltzmann control and soft recursion -/

/-- Unnormalized exponential tilt of a normalized finite prior. -/
noncomputable def boltzmannWeight (prior : FiniteLaw Action)
    (energy : Action → ℝ) (action : Action) : ℝ :=
  prior action * Real.exp (-energy action)

/-- Partition function of a prior-weighted finite exponential tilt. -/
noncomputable def boltzmannPartition (prior : FiniteLaw Action)
    (energy : Action → ℝ) : ℝ :=
  ∑ action, boltzmannWeight prior energy action

/-- Normalization of the prior guarantees a strictly positive exponential
partition even when the prior has zero-mass actions. -/
theorem boltzmannPartition_pos (prior : FiniteLaw Action)
    (energy : Action → ℝ) :
    0 < boltzmannPartition prior energy := by
  have hPrior : 0 < ∑ action, prior action := by
    rw [prior.sum_one]
    norm_num
  obtain ⟨action, _, hAction⟩ :=
    (Finset.sum_pos_iff_of_nonneg
      (fun candidate _ => prior.nonneg candidate)).mp hPrior
  apply (Finset.sum_pos_iff_of_nonneg (fun candidate _ =>
    mul_nonneg (prior.nonneg candidate) (Real.exp_nonneg _))).mpr
  exact ⟨action, Finset.mem_univ action,
    mul_pos hAction (Real.exp_pos _)⟩

/-- Normalized posterior induced by a finite prior and energy. -/
noncomputable def boltzmannPosterior (prior : FiniteLaw Action)
    (energy : Action → ℝ) : FiniteLaw Action where
  mass action := boltzmannWeight prior energy action /
    boltzmannPartition prior energy
  nonneg action := div_nonneg
    (mul_nonneg (prior.nonneg action) (Real.exp_nonneg _))
    (boltzmannPartition_pos prior energy).le
  sum_one := by
    rw [← Finset.sum_div]
    exact div_self (ne_of_gt (boltzmannPartition_pos prior energy))

/-- Posterior mass reconstructs its unnormalized exponential weight. -/
theorem boltzmannPosterior_mul_partition (prior : FiniteLaw Action)
    (energy : Action → ℝ) (action : Action) :
    boltzmannPosterior prior energy action * boltzmannPartition prior energy =
      boltzmannWeight prior energy action := by
  exact div_mul_cancel₀ _ (ne_of_gt (boltzmannPartition_pos prior energy))

/-- A zero energy leaves every normalized prior unchanged. -/
theorem boltzmannPosterior_zero_energy (prior : FiniteLaw Action) :
    boltzmannPosterior prior (fun _ => 0) = prior := by
  apply FiniteLaw.ext_mass
  funext action
  simp [boltzmannPosterior, boltzmannPartition, boltzmannWeight, prior.sum_one]

/-- One normalized control-as-inference posterior
`Q(a) ∝ P(a) exp(-precision * cost(a))`. -/
noncomputable def controlPosterior (prior : FiniteLaw Action)
    (precision : ℝ) (cost : Action → ℝ) : FiniteLaw Action :=
  boltzmannPosterior prior (fun action => precision * cost action)

/-- Control-as-inference action probabilities sum exactly to one. -/
theorem controlPosterior_sum_one (prior : FiniteLaw Action)
    (precision : ℝ) (cost : Action → ℝ) :
    ∑ action, controlPosterior prior precision cost action = 1 :=
  (controlPosterior prior precision cost).sum_one

/-- Zero control cost leaves the action prior unchanged at every precision. -/
theorem controlPosterior_zero_cost (prior : FiniteLaw Action)
    (precision : ℝ) :
    controlPosterior prior precision (fun _ => 0) = prior := by
  simpa [controlPosterior] using boltzmannPosterior_zero_energy prior

/-- Positive partition appearing in one soft Bellman step. -/
noncomputable def softBellmanPartition (temperature : ℝ)
    (stageCost : State → Action → ℝ) (continuation : Action → ℝ)
    (state : State) : ℝ :=
  ∑ action,
    Real.exp (-(stageCost state action + continuation action) / temperature)

omit [Fintype State] in
/-- A nonempty finite action set gives a positive soft partition. -/
theorem softBellmanPartition_pos [Nonempty Action] (temperature : ℝ)
    (stageCost : State → Action → ℝ) (continuation : Action → ℝ)
    (state : State) :
    0 < softBellmanPartition temperature stageCost continuation state := by
  let action : Action := Classical.choice (inferInstance : Nonempty Action)
  apply (Finset.sum_pos_iff_of_nonneg
    (fun candidate _ => (Real.exp_pos _).le)).mpr
  exact ⟨action, Finset.mem_univ action, Real.exp_pos _⟩

/-- Finite-horizon entropy-regularized Bellman recursion.  Positive-temperature
results are stated separately because real division is totalized in Lean. -/
noncomputable def softBellmanValue (temperature : ℝ)
    (stageCost : State → Action → ℝ)
    (transition : ControlledKernel State Action) : ℕ → State → ℝ
  | 0, _ => 0
  | horizon + 1, state =>
      -temperature * Real.log
        (∑ action,
          Real.exp (-((stageCost state action +
            ∑ nextState, transition action state nextState *
              softBellmanValue temperature stageCost transition horizon nextState) /
                temperature)))

/-- Action energy entering one finite-horizon soft Bellman backup. -/
noncomputable def softBellmanActionEnergy (temperature : ℝ)
    (stageCost : State → Action → ℝ)
    (transition : ControlledKernel State Action)
    (horizon : ℕ) (state : State) (action : Action) : ℝ :=
  stageCost state action +
    ∑ nextState, transition action state nextState *
      softBellmanValue temperature stageCost transition horizon nextState

/-- Exact successor equation for the finite-horizon soft Bellman value. -/
theorem softBellmanValue_succ (temperature : ℝ)
    (stageCost : State → Action → ℝ)
    (transition : ControlledKernel State Action)
    (horizon : ℕ) (state : State) :
    softBellmanValue temperature stageCost transition (horizon + 1) state =
      -temperature * Real.log
        (∑ action,
          Real.exp (-((softBellmanActionEnergy temperature stageCost transition
            horizon state action) / temperature))) := by
  rfl

/-- A nonempty action carrier makes the partition in every soft Bellman backup
strictly positive, so the logarithm is evaluated on its intended domain. -/
theorem softBellmanValue_partition_pos [Nonempty Action]
    (temperature : ℝ) (stageCost : State → Action → ℝ)
    (transition : ControlledKernel State Action)
    (horizon : ℕ) (state : State) :
    0 < ∑ action,
      Real.exp (-((softBellmanActionEnergy temperature stageCost transition
        horizon state action) / temperature)) := by
  let action : Action := Classical.choice (inferInstance : Nonempty Action)
  apply (Finset.sum_pos_iff_of_nonneg
    (fun candidate _ ↦ (Real.exp_pos _).le)).mpr
  exact ⟨action, Finset.mem_univ action, Real.exp_pos _⟩

/-- At positive temperature, the soft minimum is no larger than the energy of
any selected action.  This is the nonvacuous hard/soft comparison behind the
finite soft Bellman recursion. -/
theorem softBellmanValue_le_actionEnergy [Nonempty Action]
    (temperature : ℝ) (hTemperature : 0 < temperature)
    (stageCost : State → Action → ℝ)
    (transition : ControlledKernel State Action)
    (horizon : ℕ) (state : State) (action : Action) :
    softBellmanValue temperature stageCost transition (horizon + 1) state ≤
      softBellmanActionEnergy temperature stageCost transition
        horizon state action := by
  classical
  let energy := softBellmanActionEnergy temperature stageCost transition
    horizon state action
  let partition := ∑ candidate,
    Real.exp (-((softBellmanActionEnergy temperature stageCost transition
      horizon state candidate) / temperature))
  have hTerm : Real.exp (-(energy / temperature)) ≤ partition := by
    exact Finset.single_le_sum
      (fun candidate _ ↦ Real.exp_nonneg
        (-((softBellmanActionEnergy temperature stageCost transition
          horizon state candidate) / temperature)))
      (Finset.mem_univ action)
  have hLog : -(energy / temperature) ≤ Real.log partition := by
    rw [← Real.log_exp (-(energy / temperature))]
    exact Real.log_le_log (Real.exp_pos _) hTerm
  rw [softBellmanValue_succ]
  change -temperature * Real.log partition ≤ energy
  calc
    -temperature * Real.log partition ≤
        -temperature * (-(energy / temperature)) :=
      mul_le_mul_of_nonpos_left hLog (neg_nonpos.mpr hTemperature.le)
    _ = energy := by
      field_simp [ne_of_gt hTemperature]

/-- One linearly-solvable-control desirability backup. -/
noncomputable def desirabilityStep (passive : FiniteKernel State State)
    (stateCost desirability : State → ℝ) (state : State) : ℝ :=
  Real.exp (-stateCost state) *
    ∑ nextState, passive state nextState * desirability nextState

/-- Nonnegative desirability is preserved by a normalized passive kernel. -/
theorem desirabilityStep_nonneg (passive : FiniteKernel State State)
    (stateCost desirability : State → ℝ)
    (hDesirability : ∀ state, 0 ≤ desirability state) (state : State) :
    0 ≤ desirabilityStep passive stateCost desirability state := by
  exact mul_nonneg (Real.exp_nonneg _)
    (Finset.sum_nonneg fun nextState _ =>
      mul_nonneg (passive.nonneg state nextState)
        (hDesirability nextState))

/-- Zero state cost and unit terminal desirability are a fixed point of the
one-step KL-control recursion. -/
theorem desirabilityStep_zero_cost_one (passive : FiniteKernel State State)
    (state : State) :
    desirabilityStep passive (fun _ => 0) (fun _ => 1) state = 1 := by
  simp [desirabilityStep, passive.sum_one state]

/-! ## Observation-dependent sophisticated planning -/

/-- A finite minimizer exists for every real objective on a nonempty finite
carrier. -/
theorem exists_finite_minimizer {ι : Type*} [Fintype ι] [Nonempty ι]
    (objective : ι → ℝ) :
    ∃ minimizer, ∀ alternative, objective minimizer ≤ objective alternative := by
  let witness : ι := Classical.choice (inferInstance : Nonempty ι)
  have hNonempty : (Finset.univ : Finset ι).Nonempty :=
    ⟨witness, Finset.mem_univ witness⟩
  obtain ⟨minimizer, _, hMinimum⟩ :=
    Finset.exists_min_image Finset.univ objective hNonempty
  exact ⟨minimizer, fun alternative =>
    hMinimum alternative (Finset.mem_univ alternative)⟩

/-- A fixed choice of finite minimizer. -/
noncomputable def finiteArgmin {ι : Type*} [Fintype ι] [Nonempty ι]
    (objective : ι → ℝ) : ι :=
  Classical.choose (exists_finite_minimizer objective)

/-- The selected finite minimizer is no worse than any alternative. -/
theorem finiteArgmin_le {ι : Type*} [Fintype ι] [Nonempty ι]
    (objective : ι → ℝ) (alternative : ι) :
    objective (finiteArgmin objective) ≤ objective alternative :=
  Classical.choose_spec (exists_finite_minimizer objective) alternative

/-- Belief-dependent observation and update model for sophisticated planning. -/
structure SophisticatedEFEModel
    (Belief Action Observation : Type*)
    [Fintype Belief] [Fintype Action] [Fintype Observation] where
  observationLaw : Belief → Action → FiniteLaw Observation
  update : Belief → Action → Observation → Belief
  stageEFE : ℕ → Belief → Action → ℝ

/-- Backward-inducted expected free energy with a fresh finite action minimum
after every possible observation. -/
noncomputable def sophisticatedEFEValue [Nonempty Action]
    (model : SophisticatedEFEModel Belief Action Observation) :
    ℕ → Belief → ℝ
  | 0, _ => 0
  | horizon + 1, belief =>
      let objective := fun action =>
        model.stageEFE horizon belief action +
          ∑ observation, model.observationLaw belief action observation *
            sophisticatedEFEValue model horizon
              (model.update belief action observation)
      objective (finiteArgmin objective)

/-- One sophisticated action selected at a backward-induction node. -/
noncomputable def sophisticatedEFEAction [Nonempty Action]
    (model : SophisticatedEFEModel Belief Action Observation)
    (horizon : ℕ) (belief : Belief) : Action :=
  finiteArgmin fun action =>
    model.stageEFE horizon belief action +
      ∑ observation, model.observationLaw belief action observation *
        sophisticatedEFEValue model horizon (model.update belief action observation)

/-- Exact sophisticated expected-free-energy successor equation. -/
theorem sophisticatedEFEValue_succ [Nonempty Action]
    (model : SophisticatedEFEModel Belief Action Observation)
    (horizon : ℕ) (belief : Belief) :
    sophisticatedEFEValue model (horizon + 1) belief =
      model.stageEFE horizon belief (sophisticatedEFEAction model horizon belief) +
        ∑ observation,
          model.observationLaw belief (sophisticatedEFEAction model horizon belief)
              observation *
            sophisticatedEFEValue model horizon
              (model.update belief (sophisticatedEFEAction model horizon belief)
                observation) := by
  rfl

/-- The sophisticated action minimizes its observation-dependent continuation
objective at the current backward-induction node. -/
theorem sophisticatedEFEAction_le [Nonempty Action]
    (model : SophisticatedEFEModel Belief Action Observation)
    (horizon : ℕ) (belief : Belief) (alternative : Action) :
    model.stageEFE horizon belief (sophisticatedEFEAction model horizon belief) +
        ∑ observation,
          model.observationLaw belief (sophisticatedEFEAction model horizon belief)
              observation *
            sophisticatedEFEValue model horizon
              (model.update belief (sophisticatedEFEAction model horizon belief)
                observation) ≤
      model.stageEFE horizon belief alternative +
        ∑ observation, model.observationLaw belief alternative observation *
          sophisticatedEFEValue model horizon
            (model.update belief alternative observation) := by
  let objective : Action → ℝ := fun action =>
    model.stageEFE horizon belief action +
      ∑ observation, model.observationLaw belief action observation *
        sophisticatedEFEValue model horizon
          (model.update belief action observation)
  change objective (finiteArgmin objective) ≤ objective alternative
  exact finiteArgmin_le objective alternative

/-! ## Exact Boolean boundary witnesses -/

/-- Boolean belief indexes denote the two Boolean point-mass laws. -/
def boolBeliefInterpret (belief : Bool) : FiniteLaw Bool :=
  FiniteLaw.pointMass belief

/-- A Boolean action deterministically sets the next Boolean state. -/
def boolActionTransition (action : Bool) : FiniteKernel Bool Bool :=
  FiniteKernel.deterministic fun _ => action

/-- The Boolean observation reveals the resulting state exactly. -/
def boolObservationKernel : FiniteKernel Bool Bool :=
  FiniteKernel.identity

/-- The observed Boolean value is the next reachable belief index. -/
def boolBeliefUpdate (_belief action observation : Bool) : Bool :=
  if observation = action then observation else action

/-- The deterministic action prediction is the corresponding point mass. -/
theorem bool_actionPrediction_eq (belief action : Bool) :
    actionPrediction (boolBeliefInterpret belief) boolActionTransition action =
      FiniteLaw.pointMass action := by
  apply FiniteLaw.ext_mass
  funext nextState
  cases belief <;> cases action <;> cases nextState <;>
    norm_num [actionPrediction, FiniteKernel.predictive_mass,
      boolBeliefInterpret, boolActionTransition, FiniteLaw.pointMass,
      FiniteKernel.deterministic, Fintype.sum_bool]

/-- Exactly the action-consistent Boolean observation has unit evidence. -/
theorem bool_actionEvidence_eq (belief action observation : Bool) :
    actionEvidence (boolBeliefInterpret belief) boolActionTransition
        boolObservationKernel action observation =
      if observation = action then 1 else 0 := by
  rw [actionEvidence, actionObservationLaw, bool_actionPrediction_eq]
  rw [show boolObservationKernel = FiniteKernel.identity from rfl,
    FiniteKernel.predictive_identity]
  rfl

/-- Every positive-evidence Boolean observation agrees with the selected
action. -/
theorem bool_positiveEvidence_observation_eq_action
    (belief action observation : Bool)
    (hEvidence : 0 < actionEvidence (boolBeliefInterpret belief)
      boolActionTransition boolObservationKernel action observation) :
    observation = action := by
  by_contra hDifferent
  rw [bool_actionEvidence_eq, ite_eq_right hDifferent] at hEvidence
  exact (lt_irrefl 0) hEvidence

/-- The positive-evidence Boolean Bayesian update is exactly its reachable
point-mass belief interpretation. -/
theorem bool_actionBeliefUpdate_eq (belief action observation : Bool)
    (hEvidence : 0 < actionEvidence (boolBeliefInterpret belief)
      boolActionTransition boolObservationKernel action observation) :
    actionBeliefUpdate (boolBeliefInterpret belief) boolActionTransition
        boolObservationKernel action observation hEvidence =
      boolBeliefInterpret (boolBeliefUpdate belief action observation) := by
  have hObservation := bool_positiveEvidence_observation_eq_action
    belief action observation hEvidence
  subst observation
  apply FiniteLaw.ext_mass
  funext state
  have hReconstruction := actionBeliefUpdate_reconstruction
    (boolBeliefInterpret belief) boolActionTransition boolObservationKernel
    action action hEvidence state
  rw [bool_actionEvidence_eq, ite_eq_left rfl, mul_one,
    bool_actionPrediction_eq] at hReconstruction
  by_cases hState : state = action
  · subst state
    simpa [boolBeliefInterpret, boolBeliefUpdate, boolObservationKernel,
      FiniteKernel.identity, FiniteKernel.deterministic, FiniteLaw.pointMass]
      using hReconstruction
  · have hReverse : action ≠ state := fun h => hState h.symm
    simpa [boolBeliefInterpret, boolBeliefUpdate, boolObservationKernel,
      FiniteKernel.identity, FiniteKernel.deterministic, FiniteLaw.pointMass,
      hState, hReverse] using hReconstruction

/-- An exact reachable finite-belief POMDP on two belief indexes. -/
noncomputable def boolReachablePOMDP :
    ReachableBeliefPOMDP Bool Bool Bool Bool where
  initial := false
  reachable := Finset.univ
  initial_mem := Finset.mem_univ false
  interpret := boolBeliefInterpret
  transition := boolActionTransition
  emission := boolObservationKernel
  update := boolBeliefUpdate
  update_mem := by
    intro belief _ action observation _
    exact Finset.mem_univ (boolBeliefUpdate belief action observation)
  update_sound := by
    intro belief action observation hEvidence
    exact (bool_actionBeliefUpdate_eq belief action observation hEvidence).symm

/-- The exact Boolean instance satisfies its positive-evidence update contract. -/
theorem boolReachablePOMDP_update_sound (belief action observation : Bool)
    (hEvidence : 0 < actionEvidence
      (boolReachablePOMDP.interpret belief) boolReachablePOMDP.transition
      boolReachablePOMDP.emission action observation) :
    boolReachablePOMDP.interpret
        (boolReachablePOMDP.update belief action observation) =
      actionBeliefUpdate (boolReachablePOMDP.interpret belief)
        boolReachablePOMDP.transition boolReachablePOMDP.emission action observation
        hEvidence :=
  boolReachablePOMDP.update_sound belief action observation hEvidence

/-- Unit mismatch loss used by the two-stage feedback witness. -/
def boolMismatchCost (belief action : Bool) : ℝ :=
  if action = belief then 0 else 1

/-- After the first observation, the second-stage controller minimizes the
mismatch loss over the finite Boolean action space. -/
noncomputable def twoStageFeedback (observation : Bool) : Bool :=
  finiteArgmin (boolMismatchCost observation)

/-- The unique second-stage minimizer is the observed Boolean state. -/
theorem twoStageFeedback_eq_observation (observation : Bool) :
    twoStageFeedback observation = observation := by
  change finiteArgmin (boolMismatchCost observation) = observation
  by_contra hDifferent
  have hMinimum := finiteArgmin_le
    (boolMismatchCost observation) observation
  simp [boolMismatchCost, hDifferent] at hMinimum
  norm_num at hMinimum

/-- The two possible first observations select different second-stage actions. -/
theorem twoStageFeedback_changes_action :
    twoStageFeedback false ≠ twoStageFeedback true := by
  rw [twoStageFeedback_eq_observation, twoStageFeedback_eq_observation]
  decide

/-- Expected second-stage loss of the observation-dependent feedback policy
under a fair first observation. -/
noncomputable def twoStageFeedbackExpectedCost : ℝ :=
  ∑ observation : Bool,
    fairBoolLaw observation *
      boolMismatchCost observation (twoStageFeedback observation)

/-- Expected second-stage loss of any fixed open-loop Boolean action. -/
noncomputable def twoStageOpenLoopExpectedCost (action : Bool) : ℝ :=
  ∑ observation : Bool,
    fairBoolLaw observation * boolMismatchCost observation action

/-- Observation-dependent feedback has zero expected mismatch. -/
theorem twoStageFeedbackExpectedCost_zero :
    twoStageFeedbackExpectedCost = 0 := by
  rw [twoStageFeedbackExpectedCost, Fintype.sum_bool]
  simp [twoStageFeedback_eq_observation, boolMismatchCost]

/-- Every fixed open-loop second action has expected mismatch `1/2`. -/
theorem twoStageOpenLoopExpectedCost_eq_half (action : Bool) :
    twoStageOpenLoopExpectedCost action = 1 / 2 := by
  cases action <;>
    rw [twoStageOpenLoopExpectedCost, Fintype.sum_bool] <;>
    norm_num [fairBoolLaw, boolMismatchCost]

/-- The exact two-stage feedback policy strictly improves on every fixed
open-loop second action. -/
theorem twoStageFeedback_beats_openLoop (action : Bool) :
    twoStageFeedbackExpectedCost < twoStageOpenLoopExpectedCost action := by
  rw [twoStageFeedbackExpectedCost_zero,
    twoStageOpenLoopExpectedCost_eq_half]
  norm_num

end FEP.ControlledMarkov
