module
public import FepSketches.families.controlled_markov
public import FepSketches.families.core_active_inference
public import FepSketches.families.core_bayesian_mechanics
public import FepSketches.families.core_thermodynamics
public import FepSketches.families.temporal_inference
public import FepSketches.controlled_markov
public import FepSketches.temporal_inference

@[expose] public section

/-!
# Controlled and temporal topic compositions

The finite normalized control/filtering results are paired with their nearest
original catalog laws.  Where the older theorem is measure-native, both
claims remain explicit instead of introducing an unproved conversion from a
`FiniteLaw` to a Mathlib `Measure`.
-/

namespace FEPComposed

open FEP FEP.ControlledMarkov FEP.TemporalInference
open MeasureTheory ProbabilityTheory Finset
open scoped BigOperators ENNReal MeasureTheory ProbabilityTheory

/-- Controlled transition rows and every reachable policy law obey their
respective normalization contracts. -/
theorem fep065_controlledKernel_extends_fep023_normalization
    {State Action Policy Outcome : Type*}
    [Fintype State] [Fintype Action] [MeasurableSpace Outcome]
    (transition : ControlledKernel State Action)
    (action : Action) (state : State)
    (policies : Set Policy) (law : Policy → Measure Outcome)
    (hLaw : ∀ policy ∈ policies, law policy Set.univ = 1)
    {reachable : Measure Outcome}
    (hReachable : reachable ∈
      fep_fep023.FEP023.fep023_reachableLaws policies law) :
    (∑ nextState, transition action state nextState = 1) ∧
      reachable Set.univ = 1 := by
  exact
    ⟨fep_fep065.FEP065.fep065_controlledKernel_normalization
        transition action state,
      fep_fep023.FEP023.fep023_reachable_normalized
        policies law hLaw hReachable⟩

/-- A finite action-conditioned update reconstructs its predicted joint, while
the native fep-034 filter reconstructs the corresponding measure joint. -/
theorem fep066_action_update_refines_fep034_filter
    {State Action Observation NativeState NativeObservation : Type*}
    [Fintype State] [Fintype Action] [Fintype Observation]
    [MeasurableSpace NativeState] [MeasurableSpace NativeObservation]
    [StandardBorelSpace NativeState] [Nonempty NativeState]
    (prior : FiniteLaw State) (transition : ControlledKernel State Action)
    (emission : FiniteKernel State Observation) (action : Action)
    (observation : Observation)
    (hEvidence : 0 < actionEvidence prior transition emission action observation)
    (state : State)
    (nativePrior : Measure NativeState) [IsFiniteMeasure nativePrior]
    (nativeTransition : Kernel NativeState NativeState)
    (nativeEmission : Kernel NativeState NativeObservation)
    [IsFiniteKernel nativeTransition] [IsFiniteKernel nativeEmission] :
    (actionBeliefUpdate prior transition emission action observation hEvidence state *
        actionEvidence prior transition emission action observation =
      actionPrediction prior transition action state *
        emission state observation) ∧
      ((nativeEmission ∘ₘ
          fep_fep034.FEP034.fep034_predictivePrior
            nativeTransition nativePrior) ⊗ₘ
          fep_fep034.FEP034.fep034_filter
            nativeTransition nativeEmission nativePrior =
        (fep_fep034.FEP034.fep034_predictivePrior
          nativeTransition nativePrior ⊗ₘ nativeEmission).map Prod.swap) := by
  exact
    ⟨fep_fep066.FEP066.fep066_actionConditioned_bayes_reconstruction
        prior transition emission action observation hEvidence state,
      fep_fep034.FEP034.fep034_filter_joint_reconstruction
        nativeTransition nativeEmission nativePrior⟩

/-- Reachable-belief reduction preserves policy value, alongside the original
set-level witness that an available policy has a reachable law. -/
theorem fep067_reachableBelief_refines_fep023
    {Belief State Action Observation Policy Outcome : Type*}
    [Fintype Belief] [Fintype State] [Fintype Action] [Fintype Observation]
    [DecidableEq Belief] [MeasurableSpace Outcome]
    (model : ReachableBeliefPOMDP Belief State Action Observation)
    (stateCost : State → Action → ℝ) (policy : ℕ → Belief → Action)
    (horizon : ℕ) (belief : Belief)
    (policies : Set Policy) (law : Policy → Measure Outcome)
    {available : Policy} (hAvailable : available ∈ policies) :
    reducedPolicyValue model stateCost policy horizon belief =
        interpretedPolicyValue model stateCost policy horizon belief ∧
      law available ∈
        fep_fep023.FEP023.fep023_reachableLaws policies law := by
  exact
    ⟨fep_fep067.FEP067.fep067_reachableBelief_policyValue_equivalence
        model stateCost policy horizon belief,
      fep_fep023.FEP023.fep023_policy_reachable
        policies law hAvailable⟩

/-- The finite soft Bellman backup has a positive partition, its exact
successor recursion, and an actionwise hard/soft bound; the original
transition-aware Bellman equation remains visible beside it. -/
theorem fep068_softBellman_extends_fep033
    {State Action OldState : Type*}
    [Fintype State] [Fintype Action] [Nonempty Action]
    (temperature : ℝ) (hTemperature : 0 < temperature)
    (stageCost : State → Action → ℝ)
    (transition : ControlledKernel State Action)
    (horizon : ℕ) (state : State)
    (discount : ENNReal) (oldStageCost : OldState → ENNReal)
    (step : OldState → OldState) (terminalCost : OldState → ENNReal)
    (oldHorizon : ℕ) (oldState : OldState) :
    ((0 < ∑ action,
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
            horizon state action) ∧
      (fep_fep033.FEP033.fep033_value
          discount oldStageCost step terminalCost (oldHorizon + 1) oldState =
        oldStageCost oldState + discount *
          fep_fep033.FEP033.fep033_value
            discount oldStageCost step terminalCost oldHorizon (step oldState)) := by
  exact
    ⟨fep_fep068.FEP068.fep068_softBellman_recursion
        temperature hTemperature stageCost transition horizon state,
      fep_fep033.FEP033.fep033_bellman
        discount oldStageCost step terminalCost oldHorizon oldState⟩

/-- A desirability backup combines a normalized passive prediction with the
strictly positive Gibbs weight certified by fep-031. -/
theorem fep069_desirability_combines_fep031_weights
    {State : Type*} [Fintype State]
    (passive : FiniteKernel State State)
    (stateCost desirability : State → ℝ) (state : State) :
    desirabilityStep passive stateCost desirability state =
        Real.exp (-stateCost state) *
          ∑ nextState, passive state nextState * desirability nextState ∧
      0 < Real.exp (-(1 : ℝ) * stateCost state) := by
  exact
    ⟨fep_fep069.FEP069.fep069_desirability_recursion
        passive stateCost desirability state,
      fep_fep031.FEP031.fep031_gibbs_weight_pos 1 (stateCost state)⟩

/-- The prior-weighted control posterior and the original support-aware
softmax are both exactly normalized finite action selectors. -/
theorem fep070_controlPosterior_refines_fep028_softmax
    {Action : Type*} [Fintype Action]
    (prior : FiniteLaw Action) (precision : ℝ) (cost : Action → ℝ)
    (gamma : ℝ) (oldCost : Fin 10 → ℝ)
    (policies : Finset (Fin 10)) (hPolicies : policies.Nonempty) :
    (∑ action, controlPosterior prior precision cost action = 1) ∧
      (∑ policy ∈ policies,
        fep_fep028.FEP028.fep028_softmax gamma oldCost policies policy = 1) := by
  exact
    ⟨fep_fep070.FEP070.fep070_controlPosterior_normalized
        prior precision cost,
      fep_fep028.FEP028.fep028_softmax_probs_sum_one
        gamma oldCost policies hPolicies⟩

/-- Sophisticated EFE and the original Bellman value each recompute a
continuation at the successor horizon; only the former conditions on future
observations. -/
theorem fep071_sophisticatedEFE_extends_fep033
    {Belief Action Observation OldState : Type*}
    [Fintype Belief] [Fintype Action] [Fintype Observation] [Nonempty Action]
    (model : SophisticatedEFEModel Belief Action Observation)
    (horizon : ℕ) (belief : Belief)
    (discount : ENNReal) (stageCost : OldState → ENNReal)
    (step : OldState → OldState) (terminalCost : OldState → ENNReal)
    (oldHorizon : ℕ) (oldState : OldState) :
    (sophisticatedEFEValue model (horizon + 1) belief =
      model.stageEFE horizon belief (sophisticatedEFEAction model horizon belief) +
        ∑ observation,
          model.observationLaw belief
              (sophisticatedEFEAction model horizon belief) observation *
            sophisticatedEFEValue model horizon
              (model.update belief
                (sophisticatedEFEAction model horizon belief) observation)) ∧
      (fep_fep033.FEP033.fep033_value
          discount stageCost step terminalCost (oldHorizon + 1) oldState =
        stageCost oldState + discount *
          fep_fep033.FEP033.fep033_value
            discount stageCost step terminalCost oldHorizon (step oldState)) := by
  exact
    ⟨fep_fep071.FEP071.fep071_sophisticatedEFE_backward_step
        model horizon belief,
      fep_fep033.FEP033.fep033_bellman
        discount stageCost step terminalCost oldHorizon oldState⟩

/-- The finite forward-filter atom reconstruction and the native fep-034 joint
reconstruction record the same predict-then-condition architecture. -/
theorem fep072_forward_filter_refines_fep034
    {State Observation NativeState NativeObservation : Type*}
    [Fintype State] [Fintype Observation]
    [MeasurableSpace NativeState] [MeasurableSpace NativeObservation]
    [StandardBorelSpace NativeState] [Nonempty NativeState]
    (prior : FiniteLaw State) (transition : FiniteKernel State State)
    (emission : FiniteKernel State Observation) (observation : Observation)
    (hEvidence : 0 < forwardEvidence prior transition emission observation)
    (state : State)
    (nativePrior : Measure NativeState) [IsFiniteMeasure nativePrior]
    (nativeTransition : Kernel NativeState NativeState)
    (nativeEmission : Kernel NativeState NativeObservation)
    [IsFiniteKernel nativeTransition] [IsFiniteKernel nativeEmission] :
    (forwardFilter prior transition emission observation hEvidence state *
        forwardEvidence prior transition emission observation =
      forwardPrediction prior transition state * emission state observation) ∧
      ((nativeEmission ∘ₘ
          fep_fep034.FEP034.fep034_predictivePrior
            nativeTransition nativePrior) ⊗ₘ
          fep_fep034.FEP034.fep034_filter
            nativeTransition nativeEmission nativePrior =
        (fep_fep034.FEP034.fep034_predictivePrior
          nativeTransition nativePrior ⊗ₘ nativeEmission).map Prod.swap) := by
  exact
    ⟨fep_fep072.FEP072.fep072_forward_filtering_recursion
        prior transition emission observation hEvidence state,
      fep_fep034.FEP034.fep034_filter_joint_reconstruction
        nativeTransition nativeEmission nativePrior⟩

/-- Backward information recursion and the original sum-product composition
law jointly certify temporal message composition in their native carriers. -/
theorem fep073_backward_message_composes_fep047
    {State Observation : Type*} [Fintype State] [Fintype Observation]
    (transition : FiniteKernel State State)
    (emission : FiniteKernel State Observation) (observation : Observation)
    (future : List Observation) (state : State)
    (outer inner : fep_fep047.FEP047.Factor)
    (incoming : fep_fep047.FEP047.State → ℝ) :
    (backwardMessage transition emission (observation :: future) state =
      backwardMessageStep transition emission observation
        (backwardMessage transition emission future) state) ∧
      (fep_fep047.FEP047.fep047_forward outer
          (fep_fep047.FEP047.fep047_forward inner incoming) =
        fep_fep047.FEP047.fep047_forward (outer * inner) incoming) := by
  exact
    ⟨fep_fep073.FEP073.fep073_backward_message_recursion
        transition emission observation future state,
      fep_fep047.FEP047.fep047_forward_compose outer inner incoming⟩

/-- Finite forward--backward smoothing reconstructs its weighted atom while
the native fep-034 posterior reconstructs the predicted observation joint. -/
theorem fep074_smoothing_reconstructs_fep034_filter
    {State NativeState NativeObservation : Type*}
    [Fintype State]
    [MeasurableSpace NativeState] [MeasurableSpace NativeObservation]
    [StandardBorelSpace NativeState] [Nonempty NativeState]
    (filtered : FiniteLaw State) (backward : State → ℝ)
    (hBackward : ∀ state, 0 ≤ backward state)
    (hNormalizer : 0 < smoothingNormalizer filtered backward) (state : State)
    (nativePrior : Measure NativeState) [IsFiniteMeasure nativePrior]
    (nativeTransition : Kernel NativeState NativeState)
    (nativeEmission : Kernel NativeState NativeObservation)
    [IsFiniteKernel nativeTransition] [IsFiniteKernel nativeEmission] :
    (forwardBackwardSmoothing filtered backward hBackward hNormalizer state *
        smoothingNormalizer filtered backward =
      filtered state * backward state) ∧
      ((nativeEmission ∘ₘ
          fep_fep034.FEP034.fep034_predictivePrior
            nativeTransition nativePrior) ⊗ₘ
          fep_fep034.FEP034.fep034_filter
            nativeTransition nativeEmission nativePrior =
        (fep_fep034.FEP034.fep034_predictivePrior
          nativeTransition nativePrior ⊗ₘ nativeEmission).map Prod.swap) := by
  exact
    ⟨fep_fep074.FEP074.fep074_forwardBackward_smoothing_factorization
        filtered backward hBackward hNormalizer state,
      fep_fep034.FEP034.fep034_filter_joint_reconstruction
        nativeTransition nativeEmission nativePrior⟩

/-- Positive-normalizer finite smoothing and every native fep-034 posterior
fiber each carry exactly unit mass. -/
theorem fep075_smoothing_normalization_extends_fep034
    {State NativeState NativeObservation : Type*}
    [Fintype State]
    [MeasurableSpace NativeState] [MeasurableSpace NativeObservation]
    [StandardBorelSpace NativeState] [Nonempty NativeState]
    (filtered : FiniteLaw State) (backward : State → ℝ)
    (hBackward : ∀ state, 0 ≤ backward state)
    (hNormalizer : 0 < smoothingNormalizer filtered backward)
    (nativePrior : Measure NativeState) [IsFiniteMeasure nativePrior]
    (nativeTransition : Kernel NativeState NativeState)
    (nativeEmission : Kernel NativeState NativeObservation)
    [IsFiniteKernel nativeTransition] [IsFiniteKernel nativeEmission]
    (nativeObservation : NativeObservation) :
    (∑ state,
        forwardBackwardSmoothing filtered backward hBackward hNormalizer state =
      1) ∧
      (fep_fep034.FEP034.fep034_filter
        nativeTransition nativeEmission nativePrior nativeObservation Set.univ = 1) := by
  exact
    ⟨fep_fep075.FEP075.fep075_smoothing_marginal_normalization
        filtered backward hBackward hNormalizer,
      fep_fep034.FEP034.fep034_filter_mass_one
        nativeTransition nativeEmission nativePrior nativeObservation⟩

/-- A prior-weighted variational state update and the original finite softmax
both produce normalized exponential-tilt laws. -/
theorem fep076_variational_update_refines_fep028_softmax
    {State : Type*} [Fintype State]
    (prior : FiniteLaw State) (energy : State → ℝ)
    (gamma : ℝ) (oldCost : Fin 10 → ℝ)
    (policies : Finset (Fin 10)) (hPolicies : policies.Nonempty) :
    (∑ state, variationalStateUpdate prior energy state = 1) ∧
      (∑ policy ∈ policies,
        fep_fep028.FEP028.fep028_softmax gamma oldCost policies policy = 1) := by
  exact
    ⟨fep_fep076.FEP076.fep076_variational_state_update_normalized
        prior energy,
      fep_fep028.FEP028.fep028_softmax_probs_sum_one
        gamma oldCost policies hPolicies⟩

/-- Finite two-level predictive composition and native three-level composition
both expose the same associativity seam without conflating their carriers. -/
theorem fep077_hierarchical_predictive_extends_fep027
    {Upper Middle Observation NativeUpper NativeMiddle NativeObservation : Type*}
    [Fintype Upper] [Fintype Middle] [Fintype Observation]
    [MeasurableSpace NativeUpper] [MeasurableSpace NativeMiddle]
    [MeasurableSpace NativeObservation]
    (top : FiniteLaw Upper) (upperKernel : FiniteKernel Upper Middle)
    (lowerKernel : FiniteKernel Middle Observation)
    (nativeTop : Measure NativeUpper)
    (nativeUpperKernel : Kernel NativeUpper NativeMiddle)
    (nativeLowerKernel : Kernel (NativeUpper × NativeMiddle) NativeObservation) :
    (hierarchicalPredictive top upperKernel lowerKernel =
      (FiniteKernel.comp lowerKernel upperKernel).predictive top) ∧
      ((fep_fep027.FEP027.fep027_hierarchicalJoint
          nativeTop nativeUpperKernel ⊗ₘ nativeLowerKernel).map
          MeasurableEquiv.prodAssoc =
        fep_fep027.FEP027.fep027_hierarchicalJoint
          nativeTop (nativeUpperKernel ⊗ₖ nativeLowerKernel)) := by
  exact
    ⟨fep_fep077.FEP077.fep077_hierarchical_predictive_factorization
        top upperKernel lowerKernel,
      fep_fep027.FEP027.fep027_hierarchical_assoc
        nativeTop nativeUpperKernel nativeLowerKernel⟩

/-- Finite Bayesian model averaging and native sequential prediction each
make their mixture/composition law explicit. -/
theorem fep078_model_average_composes_fep019
    {Model Observation NativeState NativeMiddle NativeObservation : Type*}
    [Fintype Model] [Fintype Observation]
    [MeasurableSpace NativeState] [MeasurableSpace NativeMiddle]
    [MeasurableSpace NativeObservation]
    (modelPrior : FiniteLaw Model)
    (modelPredictive : FiniteKernel Model Observation)
    (observation : Observation)
    (nativePrior : Measure NativeState)
    (earlier : Kernel NativeState NativeMiddle)
    (later : Kernel NativeMiddle NativeObservation) :
    (modelAverage modelPrior modelPredictive observation =
      ∑ model, modelPrior model * modelPredictive model observation) ∧
      (later ∘ₘ fep_fep019.FEP019.fep019_priorPredictive
          earlier nativePrior =
        fep_fep019.FEP019.fep019_priorPredictive
          (later ∘ₖ earlier) nativePrior) := by
  exact
    ⟨fep_fep078.FEP078.fep078_modelAverage_predictive_law
        modelPrior modelPredictive observation,
      fep_fep019.FEP019.fep019_priorPredictive_assoc
        earlier later nativePrior⟩

end FEPComposed
