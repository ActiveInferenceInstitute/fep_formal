import FepSketches.finite_information

/-!
# A shared finite active-inference model

One policy-conditioned carrier owns prediction, observation, posterior state,
preferences, expected free energy, policy selection, and action pushforward.
The epistemic sign is fixed by definition, while a theorem derives the
risk-plus-ambiguity decomposition under explicit full-support hypotheses.
-/

namespace FEP.ActiveInference

open FEP FEP.FiniteInformation Finset
open scoped BigOperators

variable {Policy State Outcome Action : Type*}
  [Fintype Policy] [Fintype State] [Fintype Outcome]

/-- Finite policy-conditioned generative model for active inference. -/
structure GenerativeModel (Policy State Outcome : Type*)
    [Fintype Policy] [Fintype State] [Fintype Outcome] where
  initialState : FiniteLaw State
  transition : Policy → FiniteKernel State State
  likelihood : FiniteKernel State Outcome
  preferences : FiniteLaw Outcome
  policyPrior : FiniteLaw Policy

/-- State prediction under a candidate policy. -/
def predictedState (model : GenerativeModel Policy State Outcome)
    (policy : Policy) : FiniteLaw State :=
  (model.transition policy).predictive model.initialState

/-- Predicted state-outcome joint under a policy. -/
def predictedJoint (model : GenerativeModel Policy State Outcome)
    (policy : Policy) : FiniteLaw (State × Outcome) :=
  model.likelihood.joint (predictedState model policy)

/-- Predicted outcome marginal under a policy. -/
def predictedOutcome (model : GenerativeModel Policy State Outcome)
    (policy : Policy) : FiniteLaw Outcome :=
  model.likelihood.predictive (predictedState model policy)

/-- Chronological open-loop rollout of a finite policy list.  The empty plan
is the identity transition; a head policy acts before the remaining plan. -/
def rolloutKernel [DecidableEq State]
    (model : GenerativeModel Policy State Outcome) :
    List Policy → FiniteKernel State State
  | [] => FiniteKernel.identity
  | policy :: remainder =>
      FiniteKernel.comp (rolloutKernel model remainder)
        (model.transition policy)

/-- State prediction after executing an open-loop policy list. -/
def plannedState [DecidableEq State]
    (model : GenerativeModel Policy State Outcome)
    (plan : List Policy) : FiniteLaw State :=
  (rolloutKernel model plan).predictive model.initialState

/-- Outcome prediction after an open-loop policy list. -/
def plannedOutcome [DecidableEq State]
    (model : GenerativeModel Policy State Outcome)
    (plan : List Policy) : FiniteLaw Outcome :=
  model.likelihood.predictive (plannedState model plan)

/-- Concatenating plans composes their normalized rollout kernels in
chronological order. -/
theorem rolloutKernel_append [DecidableEq State]
    (model : GenerativeModel Policy State Outcome)
    (headPlan tailPlan : List Policy) :
    rolloutKernel model (headPlan ++ tailPlan) =
      FiniteKernel.comp (rolloutKernel model tailPlan)
        (rolloutKernel model headPlan) := by
  induction headPlan with
  | nil =>
      simpa [rolloutKernel] using
        (FiniteKernel.comp_identity_right (rolloutKernel model tailPlan)).symm
  | cons policy remainder inductionHypothesis =>
      simp only [List.cons_append, rolloutKernel]
      rw [inductionHypothesis]
      exact (FiniteKernel.comp_assoc
        (rolloutKernel model tailPlan) (rolloutKernel model remainder)
        (model.transition policy)).symm

/-- The empty plan preserves the model's initial state law. -/
theorem plannedState_nil [DecidableEq State]
    (model : GenerativeModel Policy State Outcome) :
    plannedState model [] = model.initialState := by
  exact FiniteKernel.predictive_identity model.initialState

/-- Prediction after a concatenated plan is prediction of the suffix from the
prefix-predicted state. -/
theorem plannedState_append [DecidableEq State]
    (model : GenerativeModel Policy State Outcome)
    (headPlan tailPlan : List Policy) :
    plannedState model (headPlan ++ tailPlan) =
      (rolloutKernel model tailPlan).predictive
        (plannedState model headPlan) := by
  rw [plannedState, rolloutKernel_append, FiniteKernel.predictive_comp]
  rfl

/-- Exact posterior state law after a positive-mass outcome following a plan. -/
noncomputable def plannedPosteriorState [DecidableEq State]
    (model : GenerativeModel Policy State Outcome) (plan : List Policy)
    (outcome : Outcome) (h : 0 < plannedOutcome model plan outcome) :
    FiniteLaw State :=
  model.likelihood.posterior (plannedState model plan) outcome h

/-- Planned posterior mass times planned evidence reconstructs the
state-outcome joint mass. -/
theorem plannedPosteriorState_mul_evidence [DecidableEq State]
    (model : GenerativeModel Policy State Outcome) (plan : List Policy)
    (outcome : Outcome) (h : 0 < plannedOutcome model plan outcome)
    (state : State) :
    plannedPosteriorState model plan outcome h state *
        plannedOutcome model plan outcome =
      plannedState model plan state * model.likelihood state outcome := by
  exact FiniteKernel.posterior_mul_predictive _ _ _ h _

/-- Exact posterior state law after a positive-mass outcome. -/
noncomputable def posteriorState
    (model : GenerativeModel Policy State Outcome) (policy : Policy)
    (outcome : Outcome) (h : 0 < predictedOutcome model policy outcome) :
    FiniteLaw State :=
  model.likelihood.posterior (predictedState model policy) outcome h

/-- Preference risk: divergence of predicted outcomes from preferred outcomes. -/
noncomputable def risk (model : GenerativeModel Policy State Outcome)
    (policy : Policy) : ℝ :=
  finiteKL (predictedOutcome model policy) model.preferences

/-- Likelihood ambiguity averaged under policy-conditioned predicted states. -/
noncomputable def ambiguity (model : GenerativeModel Policy State Outcome)
    (policy : Policy) : ℝ :=
  conditionalEntropy (predictedState model policy) model.likelihood

/-- Epistemic value: mutual information between latent state and outcome. -/
noncomputable def epistemicValue
    (model : GenerativeModel Policy State Outcome) (policy : Policy) : ℝ :=
  mutualInformation (predictedJoint model policy)

/-- Pragmatic preference cost as expected negative log preference. -/
noncomputable def pragmaticCost
    (model : GenerativeModel Policy State Outcome) (policy : Policy) : ℝ :=
  crossEntropy (predictedOutcome model policy) model.preferences

/-- Expected free energy with the epistemic-value sign made explicit. -/
noncomputable def expectedFreeEnergy
    (model : GenerativeModel Policy State Outcome) (policy : Policy) : ℝ :=
  pragmaticCost model policy - epistemicValue model policy

/-- Epistemic value is nonnegative because it is a finite KL divergence. -/
theorem epistemicValue_nonneg
    (model : GenerativeModel Policy State Outcome) (policy : Policy) :
    0 ≤ epistemicValue model policy :=
  mutualInformation_nonneg _

/-- Support assumptions required for logarithmic decompositions and exact
posterior laws.  They are not hidden in the model carrier. -/
structure FullSupport (model : GenerativeModel Policy State Outcome) : Prop where
  state_pos : ∀ policy state, 0 < predictedState model policy state
  outcome_pos : ∀ policy outcome, 0 < predictedOutcome model policy outcome
  preference_pos : ∀ outcome, 0 < model.preferences outcome

/-- A zero-mass preferred outcome rules out the support contract needed by
logarithmic EFE decomposition and policy selection.  This exposes the boundary
instead of inheriting Lean's totalized value `Real.log 0 = 0`. -/
theorem not_fullSupport_of_preference_eq_zero
    (model : GenerativeModel Policy State Outcome) (outcome : Outcome)
    (hzero : model.preferences outcome = 0) : ¬FullSupport model := by
  intro support
  have hpositive := support.preference_pos outcome
  rw [hzero] at hpositive
  exact (lt_irrefl 0) hpositive

/-- The predicted joint reconstructs the predicted state marginal. -/
theorem predictedJoint_fstMarginal_mass
    (model : GenerativeModel Policy State Outcome) (policy : Policy)
    (state : State) :
    (predictedJoint model policy).fstMarginal state =
      predictedState model policy state :=
  FiniteKernel.joint_fstMarginal_mass _ _ _

/-- The predicted joint's second marginal is the predicted outcome law. -/
theorem predictedJoint_sndMarginal
    (model : GenerativeModel Policy State Outcome) (policy : Policy) :
    (predictedJoint model policy).sndMarginal =
      predictedOutcome model policy := rfl

/-- Finite Bayes reconstruction for the model's posterior state. -/
theorem posteriorState_mul_evidence
    (model : GenerativeModel Policy State Outcome) (policy : Policy)
    (outcome : Outcome) (h : 0 < predictedOutcome model policy outcome)
    (state : State) :
    posteriorState model policy outcome h state *
        predictedOutcome model policy outcome =
      predictedState model policy state * model.likelihood state outcome :=
  FiniteKernel.posterior_mul_predictive _ _ _ h _

/-- Surprisal of one outcome under a policy.  Positivity is required by the
downstream posterior/VFE theorems rather than hidden in this total function. -/
noncomputable def outcomeSurprisal
    (model : GenerativeModel Policy State Outcome) (policy : Policy)
    (outcome : Outcome) : ℝ :=
  -Real.log (predictedOutcome model policy outcome)

/-- Posterior-form variational free energy:
`F[Q,o,π] = KL(Q || P(s|o,π)) - log P(o|π)`. -/
noncomputable def variationalFreeEnergy
    (model : GenerativeModel Policy State Outcome) (policy : Policy)
    (outcome : Outcome) (h : 0 < predictedOutcome model policy outcome)
    (recognition : FiniteLaw State) : ℝ :=
  finiteKL recognition (posteriorState model policy outcome h) +
    outcomeSurprisal model policy outcome

/-- Variational free energy upper-bounds outcome surprisal. -/
theorem outcomeSurprisal_le_variationalFreeEnergy
    (model : GenerativeModel Policy State Outcome) (policy : Policy)
    (outcome : Outcome) (h : 0 < predictedOutcome model policy outcome)
    (recognition : FiniteLaw State) :
    outcomeSurprisal model policy outcome ≤
      variationalFreeEnergy model policy outcome h recognition := by
  unfold variationalFreeEnergy
  linarith [finiteKL_nonneg recognition
    (posteriorState model policy outcome h)]

/-- The exact Bayesian posterior attains the surprisal bound. -/
theorem variationalFreeEnergy_posterior
    (model : GenerativeModel Policy State Outcome) (policy : Policy)
    (outcome : Outcome) (h : 0 < predictedOutcome model policy outcome) :
    variationalFreeEnergy model policy outcome h
        (posteriorState model policy outcome h) =
      outcomeSurprisal model policy outcome := by
  simp [variationalFreeEnergy, finiteKL_self]

/-- Attaining the variational bound uniquely characterizes exact Bayesian
recognition, including posteriors with zero-mass states. -/
theorem variationalFreeEnergy_eq_surprisal_iff
    (model : GenerativeModel Policy State Outcome) (policy : Policy)
    (outcome : Outcome) (h : 0 < predictedOutcome model policy outcome)
    (recognition : FiniteLaw State) :
    variationalFreeEnergy model policy outcome h recognition =
        outcomeSurprisal model policy outcome ↔
      recognition = posteriorState model policy outcome h := by
  unfold variationalFreeEnergy
  rw [add_eq_right]
  exact finiteKL_eq_zero_iff recognition
    (posteriorState model policy outcome h)

/-- The negative variational free energy is an evidence lower bound. -/
theorem negative_variationalFreeEnergy_le_logEvidence
    (model : GenerativeModel Policy State Outcome) (policy : Policy)
    (outcome : Outcome) (h : 0 < predictedOutcome model policy outcome)
    (recognition : FiniteLaw State) :
    -variationalFreeEnergy model policy outcome h recognition ≤
      Real.log (predictedOutcome model policy outcome) := by
  simpa [outcomeSurprisal] using neg_le_neg
    (outcomeSurprisal_le_variationalFreeEnergy
      model policy outcome h recognition)

/-- Preference risk is cross-entropy minus predicted-outcome entropy. -/
theorem risk_eq_crossEntropy_sub_entropy
    (model : GenerativeModel Policy State Outcome) (policy : Policy)
    (support : FullSupport model) :
    risk model policy =
      pragmaticCost model policy - entropy (predictedOutcome model policy) := by
  exact finiteKL_eq_crossEntropy_sub_entropy _ _ support.preference_pos

/-- Epistemic value is predictive outcome entropy minus likelihood ambiguity. -/
theorem epistemicValue_eq_entropy_sub_ambiguity
    (model : GenerativeModel Policy State Outcome) (policy : Policy)
    (support : FullSupport model) :
    epistemicValue model policy =
      entropy (predictedOutcome model policy) - ambiguity model policy := by
  let joint := predictedJoint model policy
  have hfst : ∀ state, 0 < joint.fstMarginal state := by
    intro state
    rw [predictedJoint_fstMarginal_mass]
    exact support.state_pos policy state
  have hsnd : ∀ outcome, 0 < joint.sndMarginal outcome := by
    intro outcome
    rw [predictedJoint_sndMarginal]
    exact support.outcome_pos policy outcome
  have hfstLaw : joint.fstMarginal = predictedState model policy := by
    apply FiniteLaw.ext_mass
    funext state
    exact predictedJoint_fstMarginal_mass model policy state
  have hchain :
      entropy joint =
        entropy (predictedState model policy) + ambiguity model policy := by
    simpa [joint, predictedJoint, ambiguity] using
      entropy_joint_eq_add_conditional
        (predictedState model policy) model.likelihood
  rw [epistemicValue,
    mutualInformation_eq_entropy_marginals joint hfst hsnd,
    hfstLaw, predictedJoint_sndMarginal, hchain]
  ring

/-- Expected free energy admits the risk-plus-ambiguity decomposition. -/
theorem expectedFreeEnergy_eq_risk_add_ambiguity
    (model : GenerativeModel Policy State Outcome) (policy : Policy)
    (support : FullSupport model) :
    expectedFreeEnergy model policy =
      risk model policy + ambiguity model policy := by
  rw [expectedFreeEnergy,
    epistemicValue_eq_entropy_sub_ambiguity model policy support,
    risk_eq_crossEntropy_sub_entropy model policy support]
  unfold pragmaticCost
  ring

/-- Nonnegativity of EFE follows from its risk-plus-ambiguity decomposition
when conditional entropy is itself nonnegative. -/
theorem expectedFreeEnergy_nonneg
    (model : GenerativeModel Policy State Outcome) (policy : Policy)
    (support : FullSupport model) :
    0 ≤ expectedFreeEnergy model policy := by
  rw [expectedFreeEnergy_eq_risk_add_ambiguity model policy support]
  exact add_nonneg (finiteKL_nonneg _ _)
    (Finset.sum_nonneg fun state _ =>
      mul_nonneg ((predictedState model policy).nonneg state)
        (entropy_nonneg (model.likelihood.row state)))

/-- Replace only the current state law while preserving the transition,
likelihood, preferences, and policy prior of a generative model. -/
def withInitialState (model : GenerativeModel Policy State Outcome)
    (current : FiniteLaw State) : GenerativeModel Policy State Outcome where
  initialState := current
  transition := model.transition
  likelihood := model.likelihood
  preferences := model.preferences
  policyPrior := model.policyPrior

/-- Advance an arbitrary current state law through one policy-conditioned
transition. -/
def advanceState (model : GenerativeModel Policy State Outcome)
    (current : FiniteLaw State) (policy : Policy) : FiniteLaw State :=
  (model.transition policy).predictive current

/-- State reached by chronologically advancing an arbitrary starting law
through a finite open-loop plan. -/
def planStateFrom (model : GenerativeModel Policy State Outcome) :
    FiniteLaw State → List Policy → FiniteLaw State
  | current, [] => current
  | current, policy :: remainder =>
      planStateFrom model (advanceState model current policy) remainder

/-- Recursive, stage-dependent EFE accumulated along predicted state laws.
Each stage evaluates the same generative mechanisms after replacing the
initial law by the state prediction produced by the preceding stage. -/
noncomputable def cumulativeExpectedFreeEnergyFrom
    (model : GenerativeModel Policy State Outcome) :
    FiniteLaw State → List Policy → ℝ
  | _, [] => 0
  | current, policy :: remainder =>
      expectedFreeEnergy (withInitialState model current) policy +
        cumulativeExpectedFreeEnergyFrom model
          (advanceState model current policy) remainder

/-- Recursive support contract for every stage of an open-loop plan. -/
def PlanFullSupportFrom (model : GenerativeModel Policy State Outcome) :
    FiniteLaw State → List Policy → Prop
  | _, [] => True
  | current, policy :: remainder =>
      FullSupport (withInitialState model current) ∧
        PlanFullSupportFrom model
          (advanceState model current policy) remainder

/-- A plan advanced from an arbitrary law agrees with prediction through the
composed rollout kernel. -/
theorem planStateFrom_eq_rolloutPredictive [DecidableEq State]
    (model : GenerativeModel Policy State Outcome)
    (current : FiniteLaw State) (plan : List Policy) :
    planStateFrom model current plan =
      (rolloutKernel model plan).predictive current := by
  induction plan generalizing current with
  | nil =>
      simpa [planStateFrom, rolloutKernel] using
        (FiniteKernel.predictive_identity current).symm
  | cons policy remainder inductionHypothesis =>
      rw [planStateFrom, rolloutKernel, FiniteKernel.predictive_comp]
      exact inductionHypothesis (advanceState model current policy)

/-- Sequential state advancement respects list concatenation. -/
theorem planStateFrom_append
    (model : GenerativeModel Policy State Outcome)
    (current : FiniteLaw State) (headPlan tailPlan : List Policy) :
    planStateFrom model current (headPlan ++ tailPlan) =
      planStateFrom model (planStateFrom model current headPlan) tailPlan := by
  induction headPlan generalizing current with
  | nil => rfl
  | cons policy remainder inductionHypothesis =>
      simpa [planStateFrom] using
        inductionHypothesis (advanceState model current policy)

/-- Cumulative EFE decomposes exactly at every prefix--suffix boundary. -/
theorem cumulativeExpectedFreeEnergyFrom_append
    (model : GenerativeModel Policy State Outcome)
    (current : FiniteLaw State) (headPlan tailPlan : List Policy) :
    cumulativeExpectedFreeEnergyFrom model current (headPlan ++ tailPlan) =
      cumulativeExpectedFreeEnergyFrom model current headPlan +
        cumulativeExpectedFreeEnergyFrom model
          (planStateFrom model current headPlan) tailPlan := by
  induction headPlan generalizing current with
  | nil => simp [cumulativeExpectedFreeEnergyFrom, planStateFrom]
  | cons policy remainder inductionHypothesis =>
      simp only [List.cons_append, cumulativeExpectedFreeEnergyFrom,
        planStateFrom]
      rw [inductionHypothesis]
      ring

/-- Stagewise full support makes cumulative expected free energy nonnegative. -/
theorem cumulativeExpectedFreeEnergyFrom_nonneg
    (model : GenerativeModel Policy State Outcome)
    (current : FiniteLaw State) (plan : List Policy)
    (support : PlanFullSupportFrom model current plan) :
    0 ≤ cumulativeExpectedFreeEnergyFrom model current plan := by
  induction plan generalizing current with
  | nil => simp [cumulativeExpectedFreeEnergyFrom]
  | cons policy remainder inductionHypothesis =>
      rcases support with ⟨stageSupport, remainderSupport⟩
      exact add_nonneg
        (expectedFreeEnergy_nonneg
          (withInitialState model current) policy stageSupport)
        (inductionHypothesis
          (advanceState model current policy) remainderSupport)

/-- Model-rooted cumulative EFE for a finite open-loop plan. -/
noncomputable def cumulativeExpectedFreeEnergy
    (model : GenerativeModel Policy State Outcome)
    (plan : List Policy) : ℝ :=
  cumulativeExpectedFreeEnergyFrom model model.initialState plan

/-- Model-rooted stagewise support contract for a finite plan. -/
def PlanFullSupport (model : GenerativeModel Policy State Outcome)
    (plan : List Policy) : Prop :=
  PlanFullSupportFrom model model.initialState plan

/-- Model-rooted cumulative EFE is nonnegative under stagewise support. -/
theorem cumulativeExpectedFreeEnergy_nonneg
    (model : GenerativeModel Policy State Outcome) (plan : List Policy)
    (support : PlanFullSupport model plan) :
    0 ≤ cumulativeExpectedFreeEnergy model plan :=
  cumulativeExpectedFreeEnergyFrom_nonneg
    model model.initialState plan support

/-- Unnormalized prior-weighted Boltzmann policy mass. -/
noncomputable def policyWeight (precision : ℝ)
    (model : GenerativeModel Policy State Outcome) (policy : Policy) : ℝ :=
  model.policyPrior policy *
    Real.exp (-precision * expectedFreeEnergy model policy)

/-- Policy partition function. -/
noncomputable def policyPartition (precision : ℝ)
    (model : GenerativeModel Policy State Outcome) : ℝ :=
  ∑ policy, policyWeight precision model policy

/-- The prior-weighted Boltzmann policy partition is strictly positive. -/
theorem policyPartition_pos (precision : ℝ)
    (model : GenerativeModel Policy State Outcome) :
    0 < policyPartition precision model := by
  have hpriorSum : 0 < ∑ policy, model.policyPrior policy := by
    rw [model.policyPrior.sum_one]
    norm_num
  obtain ⟨policy, _, hpolicy⟩ :=
    (Finset.sum_pos_iff_of_nonneg
      (fun p _ => model.policyPrior.nonneg p)).mp hpriorSum
  apply (Finset.sum_pos_iff_of_nonneg (fun p _ =>
    mul_nonneg (model.policyPrior.nonneg p) (Real.exp_nonneg _))).mpr
  exact ⟨policy, Finset.mem_univ policy,
    mul_pos hpolicy (Real.exp_pos _)⟩

/-- Normalized posterior policy law `Q(π) ∝ P(π) exp(-γ G(π))`.
Full support is part of the interface because the real-valued logarithmic EFE
is only given its risk-plus-ambiguity interpretation under that contract. -/
noncomputable def policyPosterior (precision : ℝ)
    (model : GenerativeModel Policy State Outcome)
    (_support : FullSupport model) : FiniteLaw Policy where
  mass policy := policyWeight precision model policy /
    policyPartition precision model
  nonneg policy := div_nonneg
    (mul_nonneg (model.policyPrior.nonneg policy) (Real.exp_nonneg _))
    (policyPartition_pos precision model).le
  sum_one := by
    rw [← Finset.sum_div]
    exact div_self (ne_of_gt (policyPartition_pos precision model))

/-- The normalized posterior reconstructs its unnormalized policy weight. -/
theorem policyPosterior_mul_partition (precision : ℝ)
    (model : GenerativeModel Policy State Outcome)
    (support : FullSupport model) (policy : Policy) :
    policyPosterior precision model support policy *
        policyPartition precision model =
      policyWeight precision model policy := by
  exact div_mul_cancel₀ _ (ne_of_gt (policyPartition_pos precision model))

/-- Equal-prior lower-EFE policies receive at least as much posterior mass. -/
theorem policyPosterior_antitone_expectedFreeEnergy
    {precision : ℝ} (hprecision : 0 ≤ precision)
    (model : GenerativeModel Policy State Outcome) (support : FullSupport model)
    {policy₁ policy₂ : Policy}
    (hprior : model.policyPrior policy₁ = model.policyPrior policy₂)
    (hG : expectedFreeEnergy model policy₁ ≤
      expectedFreeEnergy model policy₂) :
    policyPosterior precision model support policy₂ ≤
      policyPosterior precision model support policy₁ := by
  have hexponent :
      -precision * expectedFreeEnergy model policy₂ ≤
        -precision * expectedFreeEnergy model policy₁ :=
    mul_le_mul_of_nonpos_left hG (neg_nonpos.mpr hprecision)
  have hexp := Real.exp_le_exp.mpr hexponent
  have hweight :
      policyWeight precision model policy₂ ≤
        policyWeight precision model policy₁ := by
    unfold policyWeight
    rw [hprior]
    exact mul_le_mul_of_nonneg_left hexp (model.policyPrior.nonneg policy₂)
  exact div_le_div_of_nonneg_right hweight
    (policyPartition_pos precision model).le

/-- A maximum-a-posteriori policy exists on the finite posterior carrier. -/
theorem exists_policyMAP (precision : ℝ)
    (model : GenerativeModel Policy State Outcome)
    (support : FullSupport model) :
    ∃ policy : Policy, ∀ alternative : Policy,
      policyPosterior precision model support alternative ≤
        policyPosterior precision model support policy := by
  have hne : (Finset.univ : Finset Policy).Nonempty := by
    have hpositive := policyPartition_pos precision model
    exact Finset.nonempty_iff_ne_empty.mpr fun hempty => by
      simp [policyPartition, hempty] at hpositive
  obtain ⟨policy, _, hmax⟩ :=
    Finset.exists_max_image Finset.univ
      (policyPosterior precision model support) hne
  exact ⟨policy, fun alternative => hmax alternative (Finset.mem_univ _)⟩

/-- Expected free energy attains a minimum on the model's finite policy type. -/
theorem exists_expectedFreeEnergy_minimizer
    (model : GenerativeModel Policy State Outcome) :
    ∃ policy : Policy, ∀ alternative : Policy,
      expectedFreeEnergy model policy ≤ expectedFreeEnergy model alternative := by
  have hpriorSum : 0 < ∑ policy, model.policyPrior policy := by
    rw [model.policyPrior.sum_one]
    norm_num
  obtain ⟨policy, _, _⟩ :=
    (Finset.sum_pos_iff_of_nonneg
      (fun p _ => model.policyPrior.nonneg p)).mp hpriorSum
  have hne : (Finset.univ : Finset Policy).Nonempty :=
    ⟨policy, Finset.mem_univ policy⟩
  obtain ⟨minimizer, _, hmin⟩ :=
    Finset.exists_min_image Finset.univ (expectedFreeEnergy model) hne
  exact ⟨minimizer, fun alternative => hmin alternative (Finset.mem_univ _)⟩

/-- Interface connecting policy selection to an emitted action and an
action-indexed state transition.  Consistency prevents two disconnected
notions of action: executing the action emitted by a policy must recover that
policy's transition kernel. -/
structure ActionInterface (model : GenerativeModel Policy State Outcome)
    (Action : Type*) [Fintype Action] where
  policyToAction : Policy → Action
  actionTransition : Action → FiniteKernel State State
  transition_consistent : ∀ policy,
    actionTransition (policyToAction policy) = model.transition policy

/-- Executing the action emitted by a policy produces the same predicted state
law as the policy-indexed generative transition. -/
theorem actionPredictedState_eq_predictedState
    [Fintype Action]
    (model : GenerativeModel Policy State Outcome)
    (interface : ActionInterface model Action) (policy : Policy) :
    (interface.actionTransition (interface.policyToAction policy)).predictive
        model.initialState =
      predictedState model policy := by
  rw [interface.transition_consistent]
  rfl

/-- Policy-indexed kernel for one exact act-transition step.  Its row emits
the policy's action deterministically and then predicts the next state through
the action-indexed transition. -/
def inferSelectActKernel
    [Fintype Action] [DecidableEq Action]
    (model : GenerativeModel Policy State Outcome)
    (interface : ActionInterface model Action) :
    FiniteKernel Policy (Action × State) where
  mass policy result :=
    (FiniteLaw.pointMass (interface.policyToAction policy)).product
      ((interface.actionTransition
        (interface.policyToAction policy)).predictive model.initialState) result
  nonneg policy result :=
    ((FiniteLaw.pointMass (interface.policyToAction policy)).product
      ((interface.actionTransition
        (interface.policyToAction policy)).predictive model.initialState)).nonneg
          result
  sum_one policy :=
    ((FiniteLaw.pointMass (interface.policyToAction policy)).product
      ((interface.actionTransition
        (interface.policyToAction policy)).predictive model.initialState)).sum_one

/-- The act-transition kernel exposes the emitted action and the model's
policy-conditioned predicted state exactly. -/
theorem inferSelectActKernel_mass
    [Fintype Action] [DecidableEq Action]
    (model : GenerativeModel Policy State Outcome)
    (interface : ActionInterface model Action)
    (policy : Policy) (action : Action) (state : State) :
    inferSelectActKernel model interface policy (action, state) =
      if action = interface.policyToAction policy then
        predictedState model policy state else 0 := by
  rw [inferSelectActKernel]
  simp only [FiniteLaw.product, FiniteLaw.pointMass]
  rw [actionPredictedState_eq_predictedState model interface policy]
  split <;> simp_all

/-- Push the posterior policy law through the policy-to-action map. -/
noncomputable def actionLaw [Fintype Action] [DecidableEq Action]
    (policyToAction : Policy → Action) (precision : ℝ)
    (model : GenerativeModel Policy State Outcome)
    (support : FullSupport model) : FiniteLaw Action :=
  (policyPosterior precision model support).map policyToAction

/-- Action probability is the sum of posterior policy mass in its fiber. -/
theorem actionLaw_mass [Fintype Action] [DecidableEq Action]
    (policyToAction : Policy → Action) (precision : ℝ)
    (model : GenerativeModel Policy State Outcome)
    (support : FullSupport model) (action : Action) :
    actionLaw policyToAction precision model support action =
      ∑ policy, if policyToAction policy = action then
        policyPosterior precision model support policy else 0 := rfl

/-- One normalized infer-select-act-transition joint.  The policy marginal is
the support-licensed Boltzmann posterior; conditional on a selected policy,
the action is deterministic and the next state follows the consistent action
transition. -/
noncomputable def inferSelectActJoint
    [Fintype Action] [DecidableEq Action]
    (precision : ℝ) (model : GenerativeModel Policy State Outcome)
    (support : FullSupport model)
    (interface : ActionInterface model Action) :
    FiniteLaw (Policy × (Action × State)) :=
  (inferSelectActKernel model interface).joint
    (policyPosterior precision model support)

/-- The exact cycle preserves the selected-policy posterior as its first
marginal. -/
theorem inferSelectActJoint_policyMarginal
    [Fintype Action] [DecidableEq Action]
    (precision : ℝ) (model : GenerativeModel Policy State Outcome)
    (support : FullSupport model)
    (interface : ActionInterface model Action) (policy : Policy) :
    (inferSelectActJoint precision model support interface).fstMarginal policy =
      policyPosterior precision model support policy :=
  FiniteKernel.joint_fstMarginal_mass
    (policyPosterior precision model support)
    (inferSelectActKernel model interface) policy

/-- Pointwise cycle factorization into selection mass, deterministic action,
and the policy-conditioned next-state prediction. -/
theorem inferSelectActJoint_factorization
    [Fintype Action] [DecidableEq Action]
    (precision : ℝ) (model : GenerativeModel Policy State Outcome)
    (support : FullSupport model)
    (interface : ActionInterface model Action)
    (policy : Policy) (action : Action) (state : State) :
    inferSelectActJoint precision model support interface
        (policy, (action, state)) =
      policyPosterior precision model support policy *
        (if action = interface.policyToAction policy then
          predictedState model policy state else 0) := by
  change
    policyPosterior precision model support policy *
        inferSelectActKernel model interface policy (action, state) = _
  rw [inferSelectActKernel_mass]

/-- Action marginal obtained from the exact infer-select-act-transition joint
by first dropping policy and then dropping next state. -/
noncomputable def inferSelectActActionMarginal
    [Fintype Action] [DecidableEq Action]
    (precision : ℝ) (model : GenerativeModel Policy State Outcome)
    (support : FullSupport model)
    (interface : ActionInterface model Action) : FiniteLaw Action :=
  (inferSelectActJoint precision model support interface).sndMarginal.fstMarginal

/-- The action law used by the public selection API is exactly the action
marginal of the normalized infer-select-act-transition cycle. -/
theorem inferSelectActActionMarginal_eq_actionLaw
    [Fintype Action] [DecidableEq Action]
    (precision : ℝ) (model : GenerativeModel Policy State Outcome)
    (support : FullSupport model)
    (interface : ActionInterface model Action) :
    inferSelectActActionMarginal precision model support interface =
      actionLaw interface.policyToAction precision model support := by
  apply FiniteLaw.ext_mass
  funext action
  rw [actionLaw_mass]
  change
    (∑ state : State, ∑ policy : Policy,
      inferSelectActJoint precision model support interface
        (policy, (action, state))) = _
  simp_rw [inferSelectActJoint_factorization]
  rw [Finset.sum_comm]
  apply Finset.sum_congr rfl
  intro policy _
  by_cases haction : action = interface.policyToAction policy
  · simp only [ite_eq_left haction, ite_eq_left haction.symm]
    rw [← Finset.mul_sum, (predictedState model policy).sum_one, mul_one]
  · have hreverse : interface.policyToAction policy ≠ action :=
      fun h => haction h.symm
    simp [haction, hreverse]

/-! ## Exact two-state, two-observation witness

The following symmetric carrier makes the support, sign, and prior-sensitivity
contracts concrete.  Both policies share a fully supported transition and
likelihood, so their EFE values agree; changing only the normalized policy prior
therefore changes the posterior policy mass exactly rather than being erased by
the Boltzmann normalization.
-/

/-- Fair law on the two-element Boolean carrier. -/
noncomputable def fairBoolLaw : FiniteLaw Bool where
  mass _ := 1 / 2
  nonneg _ := by norm_num
  sum_one := by rw [Fintype.sum_bool]; norm_num

/-- Fully supported state/observation kernel with fair rows. -/
noncomputable def fairBoolKernel : FiniteKernel Bool Bool where
  mass _ _ := 1 / 2
  nonneg _ _ := by norm_num
  sum_one _ := by rw [Fintype.sum_bool]; norm_num

/-- Policy prior assigning mass `3/4` to `true`. -/
noncomputable def trueBiasedPolicyPrior : FiniteLaw Bool where
  mass policy := if policy then 3 / 4 else 1 / 4
  nonneg policy := by cases policy <;> norm_num
  sum_one := by rw [Fintype.sum_bool]; norm_num

/-- Policy prior assigning mass `1/4` to `true`. -/
noncomputable def falseBiasedPolicyPrior : FiniteLaw Bool where
  mass policy := if policy then 1 / 4 else 3 / 4
  nonneg policy := by cases policy <;> norm_num
  sum_one := by rw [Fintype.sum_bool]; norm_num

/-- Symmetric two-policy, two-state, two-observation generative model. -/
noncomputable def symmetricBoolModel (prior : FiniteLaw Bool) :
    GenerativeModel Bool Bool Bool where
  initialState := fairBoolLaw
  transition _ := fairBoolKernel
  likelihood := fairBoolKernel
  preferences := fairBoolLaw
  policyPrior := prior

/-- Every policy predicts the fair state law in the symmetric witness. -/
theorem symmetricBoolModel_predictedState
    (prior : FiniteLaw Bool) (policy : Bool) :
    predictedState (symmetricBoolModel prior) policy = fairBoolLaw := by
  apply FiniteLaw.ext_mass
  funext state
  change (∑ current : Bool, fairBoolLaw current * (1 / 2 : ℝ)) = 1 / 2
  rw [← Finset.sum_mul, fairBoolLaw.sum_one]
  norm_num

/-- Every policy predicts the fair observation law in the symmetric witness. -/
theorem symmetricBoolModel_predictedOutcome
    (prior : FiniteLaw Bool) (policy : Bool) :
    predictedOutcome (symmetricBoolModel prior) policy = fairBoolLaw := by
  apply FiniteLaw.ext_mass
  funext outcome
  change
    (∑ state : Bool,
      predictedState (symmetricBoolModel prior) policy state * (1 / 2 : ℝ)) =
        1 / 2
  rw [← Finset.sum_mul, (predictedState
    (symmetricBoolModel prior) policy).sum_one]
  norm_num

/-- The concrete symmetric model satisfies the full-support contract. -/
theorem symmetricBoolModel_fullSupport (prior : FiniteLaw Bool) :
    FullSupport (symmetricBoolModel prior) where
  state_pos policy state := by
    rw [symmetricBoolModel_predictedState]
    norm_num [fairBoolLaw]
  outcome_pos policy outcome := by
    rw [symmetricBoolModel_predictedOutcome]
    norm_num [fairBoolLaw]
  preference_pos outcome := by
    norm_num [symmetricBoolModel, fairBoolLaw]

/-- Risk is exactly zero because prediction and preference are the same fair
law. -/
theorem symmetricBoolModel_risk_zero
    (prior : FiniteLaw Bool) (policy : Bool) :
    risk (symmetricBoolModel prior) policy = 0 := by
  rw [risk, symmetricBoolModel_predictedOutcome]
  exact finiteKL_self fairBoolLaw

/-- Likelihood ambiguity is exactly the entropy of one fair Boolean row. -/
theorem symmetricBoolModel_ambiguity
    (prior : FiniteLaw Bool) (policy : Bool) :
    ambiguity (symmetricBoolModel prior) policy = entropy fairBoolLaw := by
  rw [ambiguity, symmetricBoolModel_predictedState]
  simp only [conditionalEntropy, symmetricBoolModel, fairBoolKernel,
    FiniteKernel.row, fairBoolLaw]
  rw [Fintype.sum_bool]
  ring

/-- The EFE decomposition evaluates exactly to fair-row entropy: zero risk
plus one fair likelihood-row ambiguity. -/
theorem symmetricBoolModel_expectedFreeEnergy
    (prior : FiniteLaw Bool) (policy : Bool) :
    expectedFreeEnergy (symmetricBoolModel prior) policy = entropy fairBoolLaw := by
  rw [expectedFreeEnergy_eq_risk_add_ambiguity
    (symmetricBoolModel prior) policy (symmetricBoolModel_fullSupport prior),
    symmetricBoolModel_risk_zero, symmetricBoolModel_ambiguity, zero_add]

/-- With equal EFE values, the supported policy posterior recovers the supplied
policy prior exactly. -/
theorem symmetricBoolModel_policyPosterior_eq_prior
    (precision : ℝ) (prior : FiniteLaw Bool) (policy : Bool) :
    policyPosterior precision (symmetricBoolModel prior)
        (symmetricBoolModel_fullSupport prior) policy = prior policy := by
  simp only [policyPosterior, policyWeight, policyPartition]
  simp_rw [symmetricBoolModel_expectedFreeEnergy]
  simp only [symmetricBoolModel]
  rw [show (∑ candidate : Bool,
      prior candidate * Real.exp (-precision * entropy fairBoolLaw)) =
        Real.exp (-precision * entropy fairBoolLaw) by
    rw [← Finset.sum_mul, prior.sum_one, one_mul]]
  field_simp [ne_of_gt (Real.exp_pos _)]

/-- Changing only the policy prior changes the posterior mass of `true` from
`3/4` to `1/4`, for every precision. -/
theorem symmetricBoolModel_policyPrior_changes_posterior (precision : ℝ) :
    policyPosterior precision (symmetricBoolModel trueBiasedPolicyPrior)
          (symmetricBoolModel_fullSupport trueBiasedPolicyPrior) true = 3 / 4 ∧
      policyPosterior precision (symmetricBoolModel falseBiasedPolicyPrior)
          (symmetricBoolModel_fullSupport falseBiasedPolicyPrior) true = 1 / 4 := by
  constructor <;>
    rw [symmetricBoolModel_policyPosterior_eq_prior] <;>
    norm_num [trueBiasedPolicyPrior, falseBiasedPolicyPrior]

/-! ## Bridge: pragmatic-epistemic decomposition matching the Python demonstration

The ActiveInferenceSynthetic Python code (``src/expected_free_energy.py`` and
``src/policy_planning.py``) defines the expected free energy of one action as

``G(a) = -(E[ln P(o|a)] + I(s; o|a))``.

The theorems below prove that the library's ``expectedFreeEnergy`` agrees with
this sign convention and that the decomposition ties directly to the finite-KL
nonnegativity and mutual-information identity already established.
-/

/-- Pragmatic value of a policy: the expected log-preference of the predicted
outcome.  This is the ``pragmatic`` term used in the ActiveInferenceSynthetic
Python code (positive when the predicted outcome aligns with preferences). -/
noncomputable def pragmaticValue
    (model : GenerativeModel Policy State Outcome) (policy : Policy) : ℝ :=
  ∑ outcome : Outcome,
    predictedOutcome model policy outcome *
      Real.log (model.preferences outcome)

/-- Pragmatic value = -pragmaticCost because cross-entropy is -E[ln P(o)]. -/
theorem pragmaticValue_eq_negPragmaticCost
    (model : GenerativeModel Policy State Outcome) (policy : Policy) :
    pragmaticValue model policy = -pragmaticCost model policy := by
  unfold pragmaticValue pragmaticCost crossEntropy
  simp [mul_comm]

/-- **Expected free energy in ActiveInferenceSynthetic sign convention.**
``G(a) = -(pragmaticValue + epistemicValue)`` where the pragmatic term is
the expected log-preference ``E[ln P(o)]`` and the epistemic term is the
mutual information ``I(s; o)``. -/
theorem expectedFreeEnergy_eq_negPragmaticValuePlusEpistemicValue
    (model : GenerativeModel Policy State Outcome) (policy : Policy) :
    expectedFreeEnergy model policy =
      -(pragmaticValue model policy + epistemicValue model policy) := by
  rw [pragmaticValue_eq_negPragmaticCost]
  unfold expectedFreeEnergy
  ring

/-- **Static-state EFE decomposition.**  When the state transition is the
identity (the hidden state does not change over the planning horizon, as in
ActiveInferenceSynthetic's ``policy_planning.py``), the cumulative EFE over a
plan ``(a_1, ..., a_T)`` starting from the initial belief equals the sum of
per-step EFEs.  This is the exact finite-probability form of the
``evaluate_policy`` function in ``src/policy_planning.py``. -/
theorem staticState_cumulativeEFE_decomposition
    [DecidableEq State] [DecidableEq Policy]
    (model : GenerativeModel Policy State Outcome)
    (plan : List Policy)
    (hidentity : ∀ policy, model.transition policy = FiniteKernel.identity) :
    cumulativeExpectedFreeEnergy model plan =
      (plan.map (expectedFreeEnergy model)).sum := by
  rw [cumulativeExpectedFreeEnergy]
  have h_advance_id (current : FiniteLaw State) (policy : Policy) :
      advanceState model current policy = current := by
    have hide : model.transition policy = FiniteKernel.identity := hidentity policy
    simp [advanceState, hide, FiniteKernel.predictive_identity]
  induction plan with
  | nil => simp [cumulativeExpectedFreeEnergyFrom]
  | cons policy remainder ih =>
      have h_adv : advanceState model model.initialState policy = model.initialState :=
        h_advance_id model.initialState policy
      rw [cumulativeExpectedFreeEnergyFrom, h_adv]
      -- withInitialState model model.initialState is definitionally model
      -- so EFE at this state equals EFE at the original model
      have h_efe : expectedFreeEnergy (withInitialState model model.initialState) policy =
          expectedFreeEnergy model policy := rfl
      rw [h_efe, ih]
      simp [List.sum_cons]

end FEP.ActiveInference
