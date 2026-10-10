import FepSketches.active_inference
import FepSketches.controlled_markov
import FepSketches.finite_markov_dynamics
import FepSketches.policy_tree
import FepSketches.temporal_inference
import FepSketches.continuous_time_markov

/-!
# The perception-action loop as a closed-loop active-inference theorem

This module composes the repository's existing constructions into one
alternating perceive-update-select-predict loop on the normalized finite
carrier:

* the perception update is the exact likelihood posterior of the current
  belief, identified with the identity-transition forward filter and with an
  action-conditioned Bayesian update at any policy index;
* the selection stage chooses the finite expected-free-energy argmin evaluated
  at the updated root;
* the prediction stage pushes the updated belief through the rollout kernel of
  the selected one-policy plan.

The information theorems are:

* `perception_kl_decomposition` and `perception_step_kl_nonincrease`: the
  belief KL along the perception step splits exactly into a nonnegative
  outcome-marginal KL plus the posterior-averaged KL of the updated beliefs,
  so the posterior-averaged KL never exceeds the pre-update KL (finite data
  processing); native Mathlib KL enjoys the same data processing through the
  perception channel, and the act-predict stage is Dobrushin-contractive under
  an explicit certificate.
* `loop_invariant_surprisal_bound`: the stage outcome surprisal is bounded by
  the recognition's perception-stage variational free energy with the
  perception KL as the exact epistemic gap, while the selected policy's
  expected free energy at the updated root splits into the certified
  risk-plus-ambiguity budget.
* `policyPosterior_eq_controlPosterior` and `loop_fixed_point_is_boltzmann`:
  the loop's Boltzmann policy law is the house control posterior at the chosen
  precision, and at an expected-free-energy-flat fixed point it is exactly the
  policy prior.

No new axioms are introduced; every theorem reuses the pinned foundation.
-/

namespace FEP.PerceptionActionLoop

open FEP FEP.ActiveInference FEP.ControlledMarkov FEP.FiniteInformation
  FEP.TemporalInference FEP.PolicyTrees Finset
open scoped BigOperators

variable {Policy State Outcome : Type*}
  [Fintype Policy] [Fintype State] [Fintype Outcome]

/-! ## The perception-update-select-predict step -/

/-- The expected-free-energy-optimal policy at a belief root: the finite argmin
of the stage expected free energy evaluated with the belief as the model's
initial law. -/
noncomputable def selectedPolicy [Nonempty Policy]
    (model : GenerativeModel Policy State Outcome) (belief : FiniteLaw State) :
    Policy :=
  finiteArgmin fun policy =>
    expectedFreeEnergy (withInitialState model belief) policy

/-- The selected policy minimizes the stage expected free energy at its root. -/
theorem selectedPolicy_minimizes [Nonempty Policy]
    (model : GenerativeModel Policy State Outcome) (belief : FiniteLaw State)
    (alternative : Policy) :
    expectedFreeEnergy (withInitialState model belief)
        (selectedPolicy model belief) ≤
      expectedFreeEnergy (withInitialState model belief) alternative :=
  finiteArgmin_le _ alternative

/-- Perception stage: the exact Bayesian posterior of the current belief after
one positive-evidence observation through the model likelihood. -/
noncomputable def filteredBelief
    (model : GenerativeModel Policy State Outcome) (belief : FiniteLaw State)
    (outcome : Outcome)
    (hEvidence : 0 < model.likelihood.predictive belief outcome) :
    FiniteLaw State :=
  model.likelihood.posterior belief outcome hEvidence

/-- One perception-update-select-predict loop step at a belief root.  The
observation conditions the belief through the likelihood (posterior
reconstruction); the selected policy minimizes the stage expected free energy
at the updated belief; the prediction pushes the updated belief through the
rollout kernel of the one-policy plan built from the selection. -/
noncomputable def perceptionActionStep [Nonempty Policy] [DecidableEq State]
    (model : GenerativeModel Policy State Outcome) (belief : FiniteLaw State)
    (outcome : Outcome)
    (hEvidence : 0 < model.likelihood.predictive belief outcome) :
    FiniteLaw State :=
  (rolloutKernel model
      [selectedPolicy model (filteredBelief model belief outcome hEvidence)]).predictive
    (filteredBelief model belief outcome hEvidence)

/-- With the identity transition, the forward evidence is the model's
predictive evidence. -/
theorem forwardEvidence_eq_predictive_of_identity [DecidableEq State]
    (belief : FiniteLaw State) (outcome : Outcome)
    (transition : FiniteKernel State State)
    (hIdentity : transition = FiniteKernel.identity)
    (emission : FiniteKernel State Outcome) :
    forwardEvidence belief transition emission outcome =
      emission.predictive belief outcome := by
  rw [forwardEvidence, forwardPrediction, hIdentity,
    FiniteKernel.predictive_identity]

/-- The identity-transition forward evidence is positive at positive
predictive evidence. -/
theorem identity_forwardEvidence [DecidableEq State]
    (belief : FiniteLaw State) (outcome : Outcome)
    (transition : FiniteKernel State State)
    (hIdentity : transition = FiniteKernel.identity)
    (emission : FiniteKernel State Outcome)
    (hEvidence : 0 < emission.predictive belief outcome) :
    0 < forwardEvidence belief transition emission outcome := by
  rw [forwardEvidence_eq_predictive_of_identity belief outcome transition
    hIdentity emission]
  exact hEvidence

/-- The perception update is exactly the identity-transition forward filter of
the temporal-inference layer. -/
theorem filteredBelief_eq_forwardFilter [DecidableEq State]
    (model : GenerativeModel Policy State Outcome) (belief : FiniteLaw State)
    (outcome : Outcome)
    (hEvidence : 0 < model.likelihood.predictive belief outcome) :
    filteredBelief model belief outcome hEvidence =
      forwardFilter belief FiniteKernel.identity model.likelihood outcome
        (identity_forwardEvidence belief outcome FiniteKernel.identity rfl
          model.likelihood hEvidence) := by
  apply FiniteLaw.ext_mass
  funext state
  show
    belief state * model.likelihood state outcome /
        model.likelihood.predictive belief outcome =
      FiniteKernel.predictive belief FiniteKernel.identity state *
          model.likelihood state outcome /
        model.likelihood.predictive
          (FiniteKernel.predictive belief FiniteKernel.identity) outcome
  rw [FiniteKernel.predictive_identity]
  try rfl

/-- With the identity control kernel, the action-conditioned evidence is the
model's predictive evidence. -/
theorem actionEvidence_eq_predictive_of_identity [DecidableEq State]
    (belief : FiniteLaw State) (outcome : Outcome)
    (transition : ControlledKernel State Policy)
    (hIdentity : ∀ action, transition action = FiniteKernel.identity)
    (policy : Policy) (emission : FiniteKernel State Outcome) :
    actionEvidence belief transition emission policy outcome =
      emission.predictive belief outcome := by
  rw [actionEvidence, actionObservationLaw, actionPrediction, hIdentity policy,
    FiniteKernel.predictive_identity]

/-- The identity-control action evidence is positive at positive predictive
evidence. -/
theorem identity_actionEvidence [DecidableEq State]
    (belief : FiniteLaw State) (outcome : Outcome)
    (transition : ControlledKernel State Policy)
    (hIdentity : ∀ action, transition action = FiniteKernel.identity)
    (policy : Policy) (emission : FiniteKernel State Outcome)
    (hEvidence : 0 < emission.predictive belief outcome) :
    0 < actionEvidence belief transition emission policy outcome := by
  rw [actionEvidence_eq_predictive_of_identity belief outcome transition
    hIdentity policy emission]
  exact hEvidence

/-- The perception update is exactly an action-conditioned Bayesian update
whose control kernel is the identity transition, at any policy index. -/
theorem filteredBelief_eq_actionBeliefUpdate [DecidableEq State]
    (model : GenerativeModel Policy State Outcome) (belief : FiniteLaw State)
    (outcome : Outcome)
    (hEvidence : 0 < model.likelihood.predictive belief outcome)
    (transition : ControlledKernel State Policy)
    (hIdentity : ∀ action, transition action = FiniteKernel.identity)
    (policy : Policy) :
    filteredBelief model belief outcome hEvidence =
      actionBeliefUpdate belief transition model.likelihood policy outcome
        (identity_actionEvidence belief outcome transition hIdentity policy
          model.likelihood hEvidence) := by
  apply FiniteLaw.ext_mass
  funext state
  show
    belief state * model.likelihood state outcome /
        model.likelihood.predictive belief outcome =
      FiniteKernel.predictive belief (transition policy) state *
          model.likelihood state outcome /
        model.likelihood.predictive
          (FiniteKernel.predictive belief (transition policy)) outcome
  rw [hIdentity policy, FiniteKernel.predictive_identity]
  try rfl

/-- The one-policy rollout prediction of the loop step is exactly one
transition of the selected policy. -/
theorem perceptionActionStep_eq [Nonempty Policy] [DecidableEq State]
    (model : GenerativeModel Policy State Outcome) (belief : FiniteLaw State)
    (outcome : Outcome)
    (hEvidence : 0 < model.likelihood.predictive belief outcome) :
    perceptionActionStep model belief outcome hEvidence =
      (model.transition (selectedPolicy model
        (filteredBelief model belief outcome hEvidence))).predictive
        (filteredBelief model belief outcome hEvidence) := by
  rw [perceptionActionStep]
  simp only [rolloutKernel]
  rw [FiniteKernel.comp_identity_left]

/-- Kernel form of the loop step over the finite outcome carrier: every
positive-evidence observation indexes one full loop step. -/
noncomputable def perceptionActionKernel [Nonempty Policy] [DecidableEq State]
    (model : GenerativeModel Policy State Outcome) (belief : FiniteLaw State)
    (hEvidence : ∀ o : Outcome, 0 < model.likelihood.predictive belief o) :
    FiniteKernel Outcome State where
  mass outcome state :=
    perceptionActionStep model belief outcome (hEvidence outcome) state
  nonneg outcome state :=
    (perceptionActionStep model belief outcome (hEvidence outcome)).nonneg state
  sum_one outcome :=
    (perceptionActionStep model belief outcome (hEvidence outcome)).sum_one

/-- Each kernel row of the loop kernel is exactly one loop step. -/
theorem perceptionActionKernel_apply [Nonempty Policy] [DecidableEq State]
    (model : GenerativeModel Policy State Outcome) (belief : FiniteLaw State)
    (hEvidence : ∀ o : Outcome, 0 < model.likelihood.predictive belief o)
    (outcome : Outcome) (state : State) :
    perceptionActionKernel model belief hEvidence outcome state =
      perceptionActionStep model belief outcome (hEvidence outcome) state :=
  rfl

/-! ## Perception-step KL: finite data processing -/

/-- Full likelihood support forces strictly positive predictive evidence for
every observation and every input law. -/
theorem predictive_pos_of_fullLikelihood
    (model : GenerativeModel Policy State Outcome) (prior : FiniteLaw State)
    (hLikelihood : ∀ s o, 0 < model.likelihood s o) (o : Outcome) :
    0 < model.likelihood.predictive prior o := by
  have hsome : ∃ s : State, 0 < prior s := by
    have hpos : 0 < ∑ s : State, prior s := by
      rw [prior.sum_one]
      norm_num
    obtain ⟨s, _, hs⟩ :=
      (Finset.sum_pos_iff_of_nonneg (fun s _ => prior.nonneg s)).mp hpos
    exact ⟨s, hs⟩
  obtain ⟨s, hs⟩ := hsome
  simp only [FiniteKernel.predictive_mass]
  exact lt_of_lt_of_le (mul_pos hs (hLikelihood s o))
    (Finset.single_le_sum (fun s' _ =>
      mul_nonneg (prior.nonneg s') (model.likelihood.nonneg s' o))
      (Finset.mem_univ s))

/-- Full likelihood and reference support force strictly positive posterior
mass at every atom. -/
theorem posterior_pos_of_support
    (model : GenerativeModel Policy State Outcome) (reference : FiniteLaw State)
    (hReference : ∀ s, 0 < reference s)
    (hLikelihood : ∀ s o, 0 < model.likelihood s o) (o : Outcome) (s : State) :
    0 < model.likelihood.posterior reference o
      (predictive_pos_of_fullLikelihood model reference hLikelihood o) s := by
  show 0 < reference s * model.likelihood s o /
    model.likelihood.predictive reference o
  exact div_pos (mul_pos (hReference s) (hLikelihood s o))
    (predictive_pos_of_fullLikelihood model reference hLikelihood o)

/-- Finite KL between two joints generated by the same kernel from different
priors reduces to the prior KL: the shared likelihood contributes nothing.  No
support hypothesis is needed. -/
theorem finiteKL_joint_same_kernel {α β : Type*} [Fintype α] [Fintype β]
    (kernel : FiniteKernel α β) (actual reference : FiniteLaw α) :
    finiteKL (kernel.joint actual) (kernel.joint reference) =
      finiteKL actual reference := by
  have hrow : ∀ (s : α) (o : β), kernel s o *
      InformationTheory.klFun
          (actual s * kernel s o / (reference s * kernel s o)) =
      kernel s o * InformationTheory.klFun (actual s / reference s) := by
    intro s o
    by_cases hk : kernel s o = 0
    · simp [hk, InformationTheory.klFun_zero]
    · by_cases hr : reference s = 0
      · simp [hr, InformationTheory.klFun_zero]
      · have hd : actual s * kernel s o / (reference s * kernel s o) =
            actual s / reference s := by
          field_simp
        rw [hd]
  have hinner : ∀ s : α,
      ∑ o : β, reference s * kernel s o *
          InformationTheory.klFun
            (actual s * kernel s o / (reference s * kernel s o)) =
        reference s * InformationTheory.klFun (actual s / reference s) := by
    intro s
    have hasso : ∀ o : β, reference s * kernel s o *
        InformationTheory.klFun
          (actual s * kernel s o / (reference s * kernel s o)) =
        reference s * (kernel s o *
          InformationTheory.klFun
            (actual s * kernel s o / (reference s * kernel s o))) :=
      fun o => mul_assoc _ _ _
    simp only [hasso, hrow]
    rw [← Finset.mul_sum]
    have hcomm : ∑ o : β, kernel s o *
        InformationTheory.klFun (actual s / reference s) =
        InformationTheory.klFun (actual s / reference s) * ∑ o : β, kernel s o := by
      rw [Finset.mul_sum]
      simp only [mul_comm]
    rw [hcomm, kernel.sum_one s, mul_one]
  simp only [finiteKL, FiniteKernel.joint, Fintype.sum_prod_type, hinner]

/-- The perception posterior kernel: each positive-evidence outcome indexes the
exact Bayesian posterior of the input belief. -/
noncomputable def posteriorKernel
    (model : GenerativeModel Policy State Outcome) (prior : FiniteLaw State)
    (hEvidence : ∀ o : Outcome, 0 < model.likelihood.predictive prior o) :
    FiniteKernel Outcome State where
  mass outcome state :=
    model.likelihood.posterior prior outcome (hEvidence outcome) state
  nonneg outcome state :=
    (model.likelihood.posterior prior outcome (hEvidence outcome)).nonneg state
  sum_one outcome :=
    (model.likelihood.posterior prior outcome (hEvidence outcome)).sum_one

/-- Posterior reconstruction at the joint level: the posterior-kernel joint has
exactly the swapped masses of the likelihood joint. -/
theorem posteriorKernel_joint_eq_swap
    (model : GenerativeModel Policy State Outcome) (prior : FiniteLaw State)
    (hEvidence : ∀ o, 0 < model.likelihood.predictive prior o)
    (o : Outcome) (s : State) :
    (posteriorKernel model prior hEvidence).joint
        (model.likelihood.predictive prior) (o, s) =
      (model.likelihood.joint prior) (s, o) := by
  change
    model.likelihood.predictive prior o *
      posteriorKernel model prior hEvidence o s =
    prior s * model.likelihood s o
  have hmass : posteriorKernel model prior hEvidence o s =
      model.likelihood.posterior prior o (hEvidence o) s := rfl
  rw [hmass, mul_comm, FiniteKernel.posterior_mul_predictive]

/-- Finite KL is invariant under swapping the two coordinates of the
posterior-form joints. -/
theorem finiteKL_swappedJoint_eq
    (model : GenerativeModel Policy State Outcome)
    (actual reference : FiniteLaw State)
    (hEvidenceAct : ∀ o, 0 < model.likelihood.predictive actual o)
    (hEvidenceRef : ∀ o, 0 < model.likelihood.predictive reference o) :
    finiteKL
        ((posteriorKernel model actual hEvidenceAct).joint
          (model.likelihood.predictive actual))
        ((posteriorKernel model reference hEvidenceRef).joint
          (model.likelihood.predictive reference)) =
      finiteKL (model.likelihood.joint actual)
        (model.likelihood.joint reference) := by
  simp only [finiteKL, Fintype.sum_prod_type]
  rw [Finset.sum_comm]
  simp only [posteriorKernel_joint_eq_swap model actual hEvidenceAct,
    posteriorKernel_joint_eq_swap model reference hEvidenceRef]

/-- Perception chain-rule dual: the belief KL to a fully supported reference
splits exactly into the nonnegative outcome-marginal KL plus the
posterior-averaged KL of the updated beliefs. -/
theorem perception_kl_decomposition
    (model : GenerativeModel Policy State Outcome)
    (actual reference : FiniteLaw State)
    (hReference : ∀ s, 0 < reference s)
    (hLikelihood : ∀ s o, 0 < model.likelihood s o) :
    finiteKL actual reference =
      finiteKL (model.likelihood.predictive actual)
          (model.likelihood.predictive reference) +
        ∑ o : Outcome, model.likelihood.predictive actual o *
          finiteKL
            (filteredBelief model actual o
              (predictive_pos_of_fullLikelihood model actual hLikelihood o))
            (filteredBelief model reference o
              (predictive_pos_of_fullLikelihood model reference hLikelihood o)) := by
  have hAct : ∀ o, 0 < model.likelihood.predictive actual o :=
    fun o => predictive_pos_of_fullLikelihood model actual hLikelihood o
  have hRef : ∀ o, 0 < model.likelihood.predictive reference o :=
    fun o => predictive_pos_of_fullLikelihood model reference hLikelihood o
  have hPosteriorChain := finiteKL_joint_chain_rule
    (model.likelihood.predictive actual) (model.likelihood.predictive reference)
    (posteriorKernel model actual hAct) (posteriorKernel model reference hRef)
    hRef (fun o s => posterior_pos_of_support model reference hReference
      hLikelihood o s)
  have hSwap := finiteKL_swappedJoint_eq model actual reference hAct hRef
  have hSameKernel := finiteKL_joint_same_kernel model.likelihood actual reference
  have hConditional : conditionalKL (model.likelihood.predictive actual)
      (posteriorKernel model actual hAct)
      (posteriorKernel model reference hRef) =
      ∑ o : Outcome, model.likelihood.predictive actual o *
        finiteKL (filteredBelief model actual o (hAct o))
          (filteredBelief model reference o (hRef o)) := rfl
  rw [← hSameKernel, ← hSwap, hPosteriorChain, hConditional]

/-- Perception-step KL non-increase (finite data processing): the
posterior-averaged KL of the updated beliefs to the reference beliefs never
exceeds the pre-update belief KL.  The dropped summand is the nonnegative
outcome-marginal KL, which is the exact gap in
`perception_kl_decomposition`. -/
theorem perception_step_kl_nonincrease
    (model : GenerativeModel Policy State Outcome)
    (actual reference : FiniteLaw State)
    (hReference : ∀ s, 0 < reference s)
    (hLikelihood : ∀ s o, 0 < model.likelihood s o) :
    ∑ o : Outcome, model.likelihood.predictive actual o *
        finiteKL
          (filteredBelief model actual o
            (predictive_pos_of_fullLikelihood model actual hLikelihood o))
          (filteredBelief model reference o
            (predictive_pos_of_fullLikelihood model reference hLikelihood o)) ≤
      finiteKL actual reference := by
  rw [perception_kl_decomposition model actual reference hReference hLikelihood]
  linarith [finiteKL_nonneg (model.likelihood.predictive actual)
    (model.likelihood.predictive reference)]

/-- Native data processing along the perception channel: pushing both beliefs
through the model likelihood cannot increase their native Mathlib KL. -/
theorem perception_native_kl_nonincrease
    [MeasurableSpace State] [MeasurableSpace Outcome]
    [DiscreteMeasurableSpace State] [DiscreteMeasurableSpace Outcome]
    (model : GenerativeModel Policy State Outcome)
    (actual reference : FiniteLaw State) :
    InformationTheory.klDiv
        (FEP.NativeBlanket.embeddedLaw (model.likelihood.predictive actual))
        (FEP.NativeBlanket.embeddedLaw (model.likelihood.predictive reference)) ≤
      InformationTheory.klDiv (FEP.NativeBlanket.embeddedLaw actual)
        (FEP.NativeBlanket.embeddedLaw reference) := by
  rw [FEP.NativeBlanket.embeddedPredictive_eq_comp,
    FEP.NativeBlanket.embeddedPredictive_eq_comp]
  exact InformationTheory.klDiv_comp_right_le
    (FEP.NativeBlanket.embeddedLaw actual)
    (FEP.NativeBlanket.embeddedLaw reference)
    (FEP.NativeBlanket.embeddedKernel model.likelihood)

/-- The act-predict stage is Dobrushin-contractive in total variation whenever
the selected policy's transition kernel carries an explicit contraction
certificate. -/
theorem prediction_dobrushin_contraction [DecidableEq State]
    (model : GenerativeModel Policy State Outcome) (policy : Policy)
    {coefficient : ℝ}
    (hBound : FEP.FiniteMarkovDynamics.HasDobrushinBound
      (model.transition policy) coefficient)
    (left right : FiniteLaw State) :
    FEP.FiniteMarkovDynamics.totalVariation
        ((model.transition policy).predictive left)
        ((model.transition policy).predictive right) ≤
      coefficient * FEP.FiniteMarkovDynamics.totalVariation left right :=
  hBound.2 left right

/-! ## The loop invariant: surprisal bound with epistemic gap -/

/-- Perception-stage variational free energy: posterior-form VFE of any
recognition against the exact likelihood posterior of the current belief.  The
outcome surprisal enters through the model's predictive evidence. -/
noncomputable def perceptionVFE
    (model : GenerativeModel Policy State Outcome) (belief : FiniteLaw State)
    (outcome : Outcome)
    (hEvidence : 0 < model.likelihood.predictive belief outcome)
    (recognition : FiniteLaw State) : ℝ :=
  finiteKL recognition (filteredBelief model belief outcome hEvidence) +
    -Real.log (model.likelihood.predictive belief outcome)

/-- Perception VFE collapse: the pre-update recognition's perception VFE
decomposes exactly into the stage outcome surprisal plus the perception KL,
the exact epistemic gap closed by the Bayesian update. -/
theorem perceptionVFE_gap
    (model : GenerativeModel Policy State Outcome) (belief : FiniteLaw State)
    (outcome : Outcome)
    (hEvidence : 0 < model.likelihood.predictive belief outcome) :
    perceptionVFE model belief outcome hEvidence belief =
      -Real.log (model.likelihood.predictive belief outcome) +
        finiteKL belief (filteredBelief model belief outcome hEvidence) := by
  unfold perceptionVFE
  ring

/-- The loop invariant at one full perception-update-select-predict step: the
stage outcome surprisal is bounded by the recognition's perception VFE with
the perception KL as the exact epistemic gap, and the selected policy's
expected free energy at the updated root splits into the certified
risk-plus-ambiguity budget. -/
theorem loop_invariant_surprisal_bound [Nonempty Policy]
    (model : GenerativeModel Policy State Outcome) (belief : FiniteLaw State)
    (outcome : Outcome)
    (hEvidence : 0 < model.likelihood.predictive belief outcome)
    (support : FullSupport (withInitialState model
      (filteredBelief model belief outcome hEvidence))) :
    -Real.log (model.likelihood.predictive belief outcome) ≤
        perceptionVFE model belief outcome hEvidence belief ∧
      perceptionVFE model belief outcome hEvidence belief =
        -Real.log (model.likelihood.predictive belief outcome) +
          finiteKL belief (filteredBelief model belief outcome hEvidence) ∧
      expectedFreeEnergy
          (withInitialState model (filteredBelief model belief outcome hEvidence))
          (selectedPolicy model (filteredBelief model belief outcome hEvidence)) =
        risk (withInitialState model (filteredBelief model belief outcome hEvidence))
            (selectedPolicy model (filteredBelief model belief outcome hEvidence)) +
          ambiguity
            (withInitialState model (filteredBelief model belief outcome hEvidence))
            (selectedPolicy model (filteredBelief model belief outcome hEvidence)) := by
  constructor
  · have hgap := perceptionVFE_gap model belief outcome hEvidence
    linarith [hgap, finiteKL_nonneg belief
      (filteredBelief model belief outcome hEvidence)]
  · constructor
    · exact perceptionVFE_gap model belief outcome hEvidence
    · exact expectedFreeEnergy_eq_risk_add_ambiguity
        (withInitialState model (filteredBelief model belief outcome hEvidence))
        (selectedPolicy model (filteredBelief model belief outcome hEvidence))
        support

/-! ## The loop's Boltzmann policy law -/

/-- The loop's Boltzmann policy law coincides with the house control posterior:
energy equals precision times expected free energy. -/
theorem policyPosterior_eq_controlPosterior (precision : ℝ)
    (model : GenerativeModel Policy State Outcome)
    (support : FullSupport model) :
    policyPosterior precision model support =
      controlPosterior model.policyPrior precision (expectedFreeEnergy model) := by
  apply FiniteLaw.ext_mass
  funext candidate
  simp only [policyPosterior, policyWeight, policyPartition, controlPosterior,
    boltzmannPosterior, boltzmannWeight, boltzmannPartition, neg_mul]

/-- At a fixed point of the perception-action loop whose expected-free-energy
landscape is constant, the loop's Boltzmann policy law at the chosen precision
is exactly the policy prior. -/
theorem loop_fixed_point_is_boltzmann (precision : ℝ)
    (model : GenerativeModel Policy State Outcome)
    (support : FullSupport model) (energy : ℝ)
    (hflat : ∀ policy, expectedFreeEnergy model policy = energy) :
    policyPosterior precision model support = model.policyPrior := by
  apply FiniteLaw.ext_mass
  funext candidate
  simp only [policyPosterior]
  have hexp : Real.exp (-precision * energy) ≠ 0 :=
    ne_of_gt (Real.exp_pos _)
  have hweight : ∀ p : Policy, policyWeight precision model p =
      model.policyPrior p * Real.exp (-precision * energy) := fun p => by
    rw [policyWeight, hflat p]
  have hpart : policyPartition precision model = Real.exp (-precision * energy) := by
    have hsum : ∑ p : Policy, policyWeight precision model p =
        ∑ p : Policy, model.policyPrior p * Real.exp (-precision * energy) := by
      simp only [hweight]
    rw [policyPartition, hsum, ← Finset.sum_mul, model.policyPrior.sum_one, one_mul]
  rw [hweight candidate, hpart]
  field_simp

/-! ## Bayesian instantiation of sophisticated and policy-tree planning

`SophisticatedEFEModel` and `EFEPolicyTreeModel` accept an arbitrary
`update`, so their risk-ambiguity optimum is silent about whether beliefs are
actually filtered.  The carrier below fixes one generative model, indexes a
finite family of beliefs by `interpret`, and requires the belief update to be
the predict-then-`filteredBelief` posterior at every positive-evidence
observation.  Both planners are then instantiated from this single carrier
and proved to agree with each other and with the reachable-belief POMDP
optimum.  A non-Bayesian update is shown to break the agreement. -/

section BayesianPlanning

variable {Belief Action : Type*} [Fintype Belief] [Fintype Action]

/-- One generative model with a finite belief index family whose update is the
Bayesian filter: after the action's transition, the observation conditions the
predicted state law through the likelihood (`filteredBelief`). -/
structure BayesianBeliefModel
    (Belief State Action Outcome : Type*)
    [Fintype Belief] [Fintype State] [Fintype Action] [Fintype Outcome] where
  generative : GenerativeModel Action State Outcome
  interpret : Belief → FiniteLaw State
  update : Belief → Action → Outcome → Belief
  update_filtered : ∀ (belief : Belief) (action : Action) (outcome : Outcome)
      (hEvidence : 0 < generative.likelihood.predictive
        (predictedState (withInitialState generative (interpret belief)) action)
        outcome),
    interpret (update belief action outcome) =
      filteredBelief generative
        (predictedState (withInitialState generative (interpret belief)) action)
        outcome hEvidence

/-- The generative model rooted at the belief denoted by an index. -/
def bayesGenerative
    (model : BayesianBeliefModel Belief State Action Outcome)
    (belief : Belief) : GenerativeModel Action State Outcome :=
  withInitialState model.generative (model.interpret belief)

/-- The Bayesian update denotes the action-conditioned Bayesian posterior of
the control layer at every positive-evidence observation. -/
theorem bayesUpdate_eq_actionBeliefUpdate
    (model : BayesianBeliefModel Belief State Action Outcome)
    (belief : Belief) (action : Action) (outcome : Outcome)
    (hEvidence : 0 < actionEvidence (model.interpret belief)
      model.generative.transition model.generative.likelihood action outcome) :
    model.interpret (model.update belief action outcome) =
      actionBeliefUpdate (model.interpret belief) model.generative.transition
        model.generative.likelihood action outcome hEvidence :=
  model.update_filtered belief action outcome hEvidence

/-- Sophisticated planner instantiated from the Bayesian carrier: the
observation law is the generative model's predicted outcome, the stage cost is
its expected free energy, and the update is the carrier's filter. -/
noncomputable def bayesSophisticatedModel
    (model : BayesianBeliefModel Belief State Action Outcome) :
    SophisticatedEFEModel Belief Action Outcome where
  observationLaw belief action := predictedOutcome (bayesGenerative model belief) action
  update := model.update
  stageEFE _ belief action := expectedFreeEnergy (bayesGenerative model belief) action

/-- Policy-tree planner instantiated from the same Bayesian carrier, at full
support. -/
def bayesEFEPolicyTreeModel
    (model : BayesianBeliefModel Belief State Action Outcome)
    (support : ∀ belief, FullSupport (bayesGenerative model belief)) :
    EFEPolicyTreeModel Belief State Action Outcome where
  generative := bayesGenerative model
  update := model.update
  support := support

/-- The reachable-belief POMDP of the Bayesian carrier, rooted at an initial
index; its update soundness is the carrier's filter identity. -/
noncomputable def bayesReachablePOMDP
    (model : BayesianBeliefModel Belief State Action Outcome)
    (initial : Belief) :
    ReachableBeliefPOMDP Belief State Action Outcome where
  initial := initial
  reachable := Finset.univ
  initial_mem := Finset.mem_univ initial
  interpret := model.interpret
  transition := model.generative.transition
  emission := model.generative.likelihood
  update := model.update
  update_mem := fun belief _ action outcome _ =>
    Finset.mem_univ (model.update belief action outcome)
  update_sound := fun belief action outcome hEvidence =>
    bayesUpdate_eq_actionBeliefUpdate model belief action outcome hEvidence

/-- Policy-tree model of a reachable-belief POMDP with an arbitrary stage
cost: observations follow the POMDP's observation law and beliefs follow its
update. -/
noncomputable def pomdpPolicyTreeModel
    (pomdp : ReachableBeliefPOMDP Belief State Action Outcome)
    (cost : ℕ → Belief → Action → ℝ) :
    PolicyTreeModel Belief Action Outcome where
  observationLaw belief action :=
    actionObservationLaw (pomdp.interpret belief) pomdp.transition
      pomdp.emission action
  update := pomdp.update
  stageCost := cost

/-- The EFE tree model of the Bayesian carrier is the policy-tree model of its
reachable-belief POMDP under the expected-free-energy stage cost. -/
theorem bayesEFETree_eq_pomdpTree
    (model : BayesianBeliefModel Belief State Action Outcome)
    (support : ∀ belief, FullSupport (bayesGenerative model belief))
    (initial : Belief) :
    efePolicyTreeModel (bayesEFEPolicyTreeModel model support) =
      pomdpPolicyTreeModel (bayesReachablePOMDP model initial)
        (fun _ belief action =>
          expectedFreeEnergy (bayesGenerative model belief) action) :=
  rfl

/-- The sophisticated recursion and the EFE policy-tree optimum coincide when
both are instantiated from one Bayesian carrier. -/
theorem bayesSophisticatedValue_eq_optimalTree [Nonempty Action]
    (model : BayesianBeliefModel Belief State Action Outcome)
    (support : ∀ belief, FullSupport (bayesGenerative model belief))
    (depth : ℕ) (belief : Belief) :
    sophisticatedEFEValue (bayesSophisticatedModel model) depth belief =
      optimalTreeValue (efePolicyTreeModel (bayesEFEPolicyTreeModel model support))
        depth belief := by
  induction depth generalizing belief with
  | zero => rfl
  | succ depth inductionHypothesis =>
      have hObjective :
          (fun action =>
            (bayesSophisticatedModel model).stageEFE depth belief action +
              ∑ outcome,
                (bayesSophisticatedModel model).observationLaw belief action
                    outcome *
                  sophisticatedEFEValue (bayesSophisticatedModel model) depth
                    ((bayesSophisticatedModel model).update belief action
                      outcome)) =
            (fun action =>
              (efePolicyTreeModel (bayesEFEPolicyTreeModel model support)).stageCost
                  depth belief action +
                ∑ outcome,
                  (efePolicyTreeModel
                      (bayesEFEPolicyTreeModel model support)).observationLaw
                      belief action outcome *
                    optimalTreeValue
                      (efePolicyTreeModel (bayesEFEPolicyTreeModel model support))
                      depth
                      ((efePolicyTreeModel
                        (bayesEFEPolicyTreeModel model support)).update belief
                        action outcome)) := by
        funext action
        apply congrArg
        apply Finset.sum_congr rfl
        intro outcome _
        exact congrArg _ (inductionHypothesis _)
      change
        (fun action =>
            (bayesSophisticatedModel model).stageEFE depth belief action +
              ∑ outcome,
                (bayesSophisticatedModel model).observationLaw belief action
                    outcome *
                  sophisticatedEFEValue (bayesSophisticatedModel model) depth
                    ((bayesSophisticatedModel model).update belief action
                      outcome))
          (finiteArgmin _) = _
      rw [hObjective]
      rfl

/-- Pushforward expectation under a deterministic map. -/
theorem finiteLawMapSum {α β : Type*} [DecidableEq β] [Fintype α] [Fintype β]
    (f : α → β) (law : FiniteLaw α) (g : β → ℝ) :
    ∑ y, law.map f y * g y = ∑ x, law x * g (f x) := by
  simp only [FiniteLaw.map_mass, Finset.sum_mul]
  rw [Finset.sum_comm]
  apply Finset.sum_congr rfl
  intro x _
  simp [ite_mul]

/-- Finite-horizon value of a belief-feedback policy on a reachable-belief
POMDP, using its reachable-belief kernel and an arbitrary belief stage cost. -/
noncomputable def beliefFeedbackValue [DecidableEq Belief]
    (pomdp : ReachableBeliefPOMDP Belief State Action Outcome)
    (cost : ℕ → Belief → Action → ℝ) (policy : ℕ → Belief → Action) :
    ℕ → Belief → ℝ
  | 0, _ => 0
  | horizon + 1, belief =>
      cost horizon belief (policy horizon belief) +
        ∑ nextBelief,
          reachableBeliefKernel pomdp (policy horizon belief) belief nextBelief *
            beliefFeedbackValue pomdp cost policy horizon nextBelief

/-- The reachable-belief kernel expectation is the observation-law expectation
of the updated belief. -/
theorem reachableBeliefKernel_sum [DecidableEq Belief]
    (pomdp : ReachableBeliefPOMDP Belief State Action Outcome)
    (action : Action) (belief : Belief) (continuation : Belief → ℝ) :
    ∑ nextBelief,
        reachableBeliefKernel pomdp action belief nextBelief *
          continuation nextBelief =
      ∑ outcome,
        actionObservationLaw (pomdp.interpret belief) pomdp.transition
            pomdp.emission action outcome *
          continuation (pomdp.update belief action outcome) :=
  finiteLawMapSum (pomdp.update belief action)
    (actionObservationLaw (pomdp.interpret belief) pomdp.transition
      pomdp.emission action) continuation

/-- No belief-feedback policy beats the policy-tree optimum of the POMDP. -/
theorem optimalTreeValue_le_beliefFeedback [Nonempty Action] [DecidableEq Belief]
    (pomdp : ReachableBeliefPOMDP Belief State Action Outcome)
    (cost : ℕ → Belief → Action → ℝ) (policy : ℕ → Belief → Action) :
    ∀ (horizon : ℕ) (belief : Belief),
      optimalTreeValue (pomdpPolicyTreeModel pomdp cost) horizon belief ≤
        beliefFeedbackValue pomdp cost policy horizon belief
  | 0, _ => le_rfl
  | horizon + 1, belief => by
      have hAction := optimalTreeAction_le (pomdpPolicyTreeModel pomdp cost)
        horizon belief (policy horizon belief)
      rw [optimalTreeValue_eq_min]
      refine hAction.trans ?_
      change
        cost horizon belief (policy horizon belief) +
            ∑ outcome,
              actionObservationLaw (pomdp.interpret belief) pomdp.transition
                  pomdp.emission (policy horizon belief) outcome *
                optimalTreeValue (pomdpPolicyTreeModel pomdp cost) horizon
                  (pomdp.update belief (policy horizon belief) outcome) ≤
          cost horizon belief (policy horizon belief) +
            ∑ nextBelief,
              reachableBeliefKernel pomdp (policy horizon belief) belief
                  nextBelief *
                beliefFeedbackValue pomdp cost policy horizon nextBelief
      rw [reachableBeliefKernel_sum pomdp (policy horizon belief) belief
        (beliefFeedbackValue pomdp cost policy horizon)]
      apply add_le_add (le_refl _)
      apply Finset.sum_le_sum
      intro outcome _
      exact mul_le_mul_of_nonneg_left
        (optimalTreeValue_le_beliefFeedback pomdp cost policy horizon _)
        ((actionObservationLaw (pomdp.interpret belief) pomdp.transition
          pomdp.emission (policy horizon belief)).nonneg outcome)

/-- The Bellman-optimal action policy of the POMDP's tree model attains the
policy-tree optimum as a belief-feedback policy on the reachable-belief
kernel. -/
theorem optimalTreeValue_eq_beliefFeedback [Nonempty Action] [DecidableEq Belief]
    (pomdp : ReachableBeliefPOMDP Belief State Action Outcome)
    (cost : ℕ → Belief → Action → ℝ) :
    ∀ (horizon : ℕ) (belief : Belief),
      optimalTreeValue (pomdpPolicyTreeModel pomdp cost) horizon belief =
        beliefFeedbackValue pomdp cost
          (optimalTreeAction (pomdpPolicyTreeModel pomdp cost)) horizon belief
  | 0, _ => rfl
  | horizon + 1, belief => by
      rw [optimalTreeValue_eq_min]
      change
        cost horizon belief
              (optimalTreeAction (pomdpPolicyTreeModel pomdp cost) horizon belief) +
            ∑ outcome,
              actionObservationLaw (pomdp.interpret belief) pomdp.transition
                  pomdp.emission
                  (optimalTreeAction (pomdpPolicyTreeModel pomdp cost) horizon
                    belief) outcome *
                optimalTreeValue (pomdpPolicyTreeModel pomdp cost) horizon
                  (pomdp.update belief
                    (optimalTreeAction (pomdpPolicyTreeModel pomdp cost) horizon
                      belief) outcome) =
          cost horizon belief
              (optimalTreeAction (pomdpPolicyTreeModel pomdp cost) horizon belief) +
            ∑ nextBelief,
              reachableBeliefKernel pomdp
                  (optimalTreeAction (pomdpPolicyTreeModel pomdp cost) horizon
                    belief) belief nextBelief *
                beliefFeedbackValue pomdp cost
                  (optimalTreeAction (pomdpPolicyTreeModel pomdp cost)) horizon
                  nextBelief
      rw [reachableBeliefKernel_sum]
      apply congrArg
      apply Finset.sum_congr rfl
      intro outcome _
      rw [optimalTreeValue_eq_beliefFeedback pomdp cost horizon]

/-- The sophisticated Bayesian recursion is the reachable-belief POMDP optimum:
it never exceeds any belief-feedback policy's value and is attained by the
Bellman-optimal one. -/
theorem bayesSophisticatedValue_eq_pomdpOptimum [Nonempty Action] [DecidableEq Belief]
    (model : BayesianBeliefModel Belief State Action Outcome)
    (support : ∀ belief, FullSupport (bayesGenerative model belief))
    (initial : Belief) :
    (∀ (policy : ℕ → Belief → Action) (horizon : ℕ) (belief : Belief),
      sophisticatedEFEValue (bayesSophisticatedModel model) horizon belief ≤
        beliefFeedbackValue (bayesReachablePOMDP model initial)
          (fun _ belief action =>
            expectedFreeEnergy (bayesGenerative model belief) action)
          policy horizon belief) ∧
      ∃ policy : ℕ → Belief → Action, ∀ (horizon : ℕ) (belief : Belief),
        sophisticatedEFEValue (bayesSophisticatedModel model) horizon belief =
          beliefFeedbackValue (bayesReachablePOMDP model initial)
            (fun _ belief action =>
              expectedFreeEnergy (bayesGenerative model belief) action)
            policy horizon belief := by
  refine ⟨fun policy horizon belief => ?_,
    optimalTreeAction (pomdpPolicyTreeModel (bayesReachablePOMDP model initial)
      (fun _ belief action =>
        expectedFreeEnergy (bayesGenerative model belief) action)),
    fun horizon belief => ?_⟩
  · rw [bayesSophisticatedValue_eq_optimalTree model support,
      bayesEFETree_eq_pomdpTree model support initial]
    exact optimalTreeValue_le_beliefFeedback _ _ policy horizon belief
  · rw [bayesSophisticatedValue_eq_optimalTree model support,
      bayesEFETree_eq_pomdpTree model support initial]
    exact optimalTreeValue_eq_beliefFeedback _ _ horizon belief

/-- On the Bayesian carrier the risk-ambiguity optimum holds for the filtered
update, and equals the sophisticated recursion. -/
theorem bayesRiskAmbiguity_eq_sophisticated [Nonempty Action]
    (model : BayesianBeliefModel Belief State Action Outcome)
    (support : ∀ belief, FullSupport (bayesGenerative model belief))
    (depth : ℕ) (belief : Belief) :
    sophisticatedEFEValue (bayesSophisticatedModel model) depth belief =
      optimalTreeValue
        (riskAmbiguityPolicyTreeModel (bayesEFEPolicyTreeModel model support))
        depth belief := by
  rw [bayesSophisticatedValue_eq_optimalTree model support]
  exact optimalEFEValue_eq_riskAmbiguity _ depth belief

end BayesianPlanning

/-! ### The fep-134 Boolean feedback witness through the Bayesian filter -/

section BooleanBayesianWitness

/-- Fair latent Boolean state, identity transition, and identity likelihood. -/
noncomputable def boolBayesGenerative : GenerativeModel Bool Bool Bool where
  initialState := fairBoolLaw
  transition _ := FiniteKernel.identity
  likelihood := FiniteKernel.identity
  preferences := fairBoolLaw
  policyPrior := fairBoolLaw

/-- `none` is the fair prior belief and `some state` the point-mass belief. -/
noncomputable def boolBayesInterpret : Option Bool → FiniteLaw Bool
  | none => fairBoolLaw
  | some state => FiniteLaw.pointMass state

/-- The reachable index after observing `outcome`. -/
def boolBayesUpdate (_belief : Option Bool) (_action outcome : Bool) :
    Option Bool :=
  some outcome

/-- A non-Bayesian update that ignores the observation and keeps the belief. -/
def boolKeepPriorUpdate (belief : Option Bool) (_action _outcome : Bool) :
    Option Bool :=
  belief

/-- The identity transition leaves every denoted belief unchanged. -/
theorem boolBayes_predictedState (belief : Option Bool) (action : Bool) :
    predictedState
        (withInitialState boolBayesGenerative (boolBayesInterpret belief))
        action = boolBayesInterpret belief :=
  FiniteKernel.predictive_identity _

/-- The identity likelihood makes the predicted outcome law the belief. -/
theorem boolBayes_predictedOutcome (belief : Option Bool) (action : Bool) :
    predictedOutcome
        (withInitialState boolBayesGenerative (boolBayesInterpret belief))
        action = boolBayesInterpret belief := by
  change FiniteKernel.predictive
      (predictedState
        (withInitialState boolBayesGenerative (boolBayesInterpret belief))
        action) FiniteKernel.identity = _
  rw [boolBayes_predictedState]
  exact FiniteKernel.predictive_identity _

/-- Observing `outcome` through the Boolean filter yields the point mass. -/
theorem boolBayes_filtered (belief : Option Bool) (action outcome : Bool)
    (hEvidence : 0 < boolBayesGenerative.likelihood.predictive
      (predictedState
        (withInitialState boolBayesGenerative (boolBayesInterpret belief))
        action) outcome) :
    boolBayesInterpret (boolBayesUpdate belief action outcome) =
      filteredBelief boolBayesGenerative
        (predictedState
          (withInitialState boolBayesGenerative (boolBayesInterpret belief))
          action) outcome hEvidence := by
  apply FiniteLaw.ext_mass
  funext state
  have hState := boolBayes_predictedState belief action
  have hDen : boolBayesGenerative.likelihood.predictive
      (predictedState
        (withInitialState boolBayesGenerative (boolBayesInterpret belief))
        action) outcome = boolBayesInterpret belief outcome := by
    change FiniteKernel.predictive _ FiniteKernel.identity outcome = _
    rw [hState, FiniteKernel.predictive_identity]
  change FiniteLaw.pointMass outcome state =
    (predictedState
        (withInitialState boolBayesGenerative (boolBayesInterpret belief))
        action) state * FiniteKernel.identity state outcome /
      boolBayesGenerative.likelihood.predictive
        (predictedState
          (withInitialState boolBayesGenerative (boolBayesInterpret belief))
          action) outcome
  rw [hDen, hState]
  rw [hDen] at hEvidence
  cases belief with
  | none =>
      cases state <;> cases outcome <;>
        norm_num [boolBayesInterpret, FiniteLaw.pointMass, fairBoolLaw,
          FiniteKernel.identity, FiniteKernel.deterministic]
  | some chosen =>
      cases state <;> cases outcome <;> cases chosen <;>
        simp_all [boolBayesInterpret, FiniteLaw.pointMass,
          FiniteKernel.identity, FiniteKernel.deterministic]

/-- The Boolean Bayesian carrier. -/
noncomputable def boolBayesModel :
    BayesianBeliefModel (Option Bool) Bool Bool Bool where
  generative := boolBayesGenerative
  interpret := boolBayesInterpret
  update := boolBayesUpdate
  update_filtered := boolBayes_filtered

/-- Policy-tree model on the Boolean carrier with a terminal mismatch cost,
for a chosen belief update. -/
noncomputable def boolBeliefTreeModel
    (update : Option Bool → Bool → Bool → Option Bool) :
    PolicyTreeModel (Option Bool) Bool Bool where
  observationLaw belief action :=
    predictedOutcome (bayesGenerative boolBayesModel belief) action
  update := update
  stageCost depth belief action :=
    if depth = 0 then
      ∑ state, boolBayesInterpret belief state * boolMismatchCost state action
    else 0

/-- The root observation law is the fair law. -/
theorem boolBayes_rootObservation (action : Bool) :
    predictedOutcome (bayesGenerative boolBayesModel none) action =
      fairBoolLaw :=
  boolBayes_predictedOutcome none action

/-- fep-134 re-derived: the Bayesian-filtered feedback tree has value zero. -/
theorem boolBayesTree_value_zero :
    policyTreeValue (boolBeliefTreeModel boolBayesUpdate) boolFeedbackTree none
      = 0 := by
  simp only [policyTreeValue, boolBeliefTreeModel, boolFeedbackTree,
    boolBayes_rootObservation, Fintype.sum_bool]
  norm_num [boolBayesUpdate, boolBayesInterpret, FiniteLaw.pointMass,
    boolMismatchCost, fairBoolLaw]

/-- Every fixed open-loop second action has value one half under the filter. -/
theorem boolBayesOpenLoop_value_half (action : Bool) :
    openLoopValue (boolBeliefTreeModel boolBayesUpdate)
        (boolOpenLoopPlan action) none = 1 / 2 := by
  cases action <;>
    simp only [openLoopValue, boolBeliefTreeModel, boolOpenLoopPlan,
      boolBayes_rootObservation, Fintype.sum_bool] <;>
    norm_num [boolBayesUpdate, boolBayesInterpret, FiniteLaw.pointMass,
      boolMismatchCost, fairBoolLaw]

/-- The filtered Boolean witness re-derives fep-134: the filter's updates
denote the point-mass beliefs of `boolFeedbackModel`, and the values are the
same zero versus one half with strict feedback gain. -/
theorem boolBayes_rederives_feedbackWitness (action : Bool) :
    (∀ a o, boolBayesInterpret (boolBayesUpdate none a o) =
        boolBeliefInterpret (boolFeedbackModel.update false a o)) ∧
      policyTreeValue (boolBeliefTreeModel boolBayesUpdate) boolFeedbackTree
          none =
        policyTreeValue boolFeedbackModel boolFeedbackTree false ∧
      policyTreeValue (boolBeliefTreeModel boolBayesUpdate) boolFeedbackTree
          none <
        openLoopValue (boolBeliefTreeModel boolBayesUpdate)
          (boolOpenLoopPlan action) none := by
  refine ⟨fun _ _ => rfl, ?_, ?_⟩
  · rw [boolBayesTree_value_zero, boolFeedbackTree_value_zero]
  · rw [boolBayesTree_value_zero, boolBayesOpenLoop_value_half]
    norm_num

/-- A non-Bayesian update (ignore the observation) is not the filter: it
fails the Bayes-agreement identity at the first observation. -/
theorem boolKeepPrior_not_bayesian :
    ∃ (hEvidence : 0 < boolBayesGenerative.likelihood.predictive
        (predictedState
          (withInitialState boolBayesGenerative (boolBayesInterpret none))
          false) true),
      boolBayesInterpret (boolKeepPriorUpdate none false true) ≠
        filteredBelief boolBayesGenerative
          (predictedState
            (withInitialState boolBayesGenerative (boolBayesInterpret none))
            false) true hEvidence := by
  have hEvidence : 0 < boolBayesGenerative.likelihood.predictive
      (predictedState
        (withInitialState boolBayesGenerative (boolBayesInterpret none))
        false) true := by
    change 0 < FiniteKernel.predictive _ FiniteKernel.identity true
    rw [boolBayes_predictedState, FiniteKernel.predictive_identity]
    norm_num [boolBayesInterpret, fairBoolLaw]
  refine ⟨hEvidence, ?_⟩
  rw [← boolBayes_filtered none false true hEvidence]
  intro hEq
  have hMass := congrArg (fun law : FiniteLaw Bool => law true) hEq
  norm_num [boolKeepPriorUpdate, boolBayesUpdate, boolBayesInterpret,
    fairBoolLaw, FiniteLaw.pointMass] at hMass

/-- Under the non-Bayesian update the same feedback tree loses its gain: its
value is one half, and the Bayesian optimum is strictly lower than the
non-Bayesian optimum, so the claimed agreement fails. -/
theorem boolKeepPrior_agreement_fails :
    policyTreeValue (boolBeliefTreeModel boolKeepPriorUpdate)
        boolFeedbackTree none = 1 / 2 ∧
      optimalTreeValue (boolBeliefTreeModel boolBayesUpdate) 2 none <
        optimalTreeValue (boolBeliefTreeModel boolKeepPriorUpdate) 2 none := by
  have hLast : ∀ action, ∑ state,
      boolBayesInterpret none state * boolMismatchCost state action = 1 / 2 := by
    intro action
    cases action <;>
      norm_num [Fintype.sum_bool, boolBayesInterpret, fairBoolLaw,
        boolMismatchCost]
  have hOne : optimalTreeValue (boolBeliefTreeModel boolKeepPriorUpdate) 1
      none = 1 / 2 := by
    change (fun action =>
        (boolBeliefTreeModel boolKeepPriorUpdate).stageCost 0 none action +
          ∑ outcome,
            (boolBeliefTreeModel boolKeepPriorUpdate).observationLaw none action
                outcome *
              optimalTreeValue (boolBeliefTreeModel boolKeepPriorUpdate) 0
                ((boolBeliefTreeModel boolKeepPriorUpdate).update none action
                  outcome))
        (finiteArgmin _) = _
    simp only [boolBeliefTreeModel, optimalTreeValue, mul_zero,
      Finset.sum_const_zero, add_zero, ite_true]
    exact hLast _
  have hTwo : optimalTreeValue (boolBeliefTreeModel boolKeepPriorUpdate) 2
      none = 1 / 2 := by
    change (fun action =>
        (boolBeliefTreeModel boolKeepPriorUpdate).stageCost 1 none action +
          ∑ outcome,
            (boolBeliefTreeModel boolKeepPriorUpdate).observationLaw none action
                outcome *
              optimalTreeValue (boolBeliefTreeModel boolKeepPriorUpdate) 1
                ((boolBeliefTreeModel boolKeepPriorUpdate).update none action
                  outcome))
        (finiteArgmin _) = _
    have hConst : ∀ action,
        (boolBeliefTreeModel boolKeepPriorUpdate).stageCost 1 none action +
          ∑ outcome,
            (boolBeliefTreeModel boolKeepPriorUpdate).observationLaw none action
                outcome *
              optimalTreeValue (boolBeliefTreeModel boolKeepPriorUpdate) 1
                ((boolBeliefTreeModel boolKeepPriorUpdate).update none action
                  outcome) = 1 / 2 := by
      intro action
      have hStep : ∀ outcome,
          optimalTreeValue (boolBeliefTreeModel boolKeepPriorUpdate) 1
            ((boolBeliefTreeModel boolKeepPriorUpdate).update none action
              outcome) = 1 / 2 := fun _ => hOne
      simp only [hStep]
      simp only [boolBeliefTreeModel, boolBayes_rootObservation,
        Fintype.sum_bool]
      norm_num [fairBoolLaw]
    exact hConst _
  refine ⟨?_, ?_⟩
  · simp only [policyTreeValue, boolBeliefTreeModel, boolFeedbackTree,
      boolBayes_rootObservation, Fintype.sum_bool, boolKeepPriorUpdate]
    norm_num [boolBayesInterpret, boolMismatchCost, fairBoolLaw]
  · rw [hTwo]
    calc optimalTreeValue (boolBeliefTreeModel boolBayesUpdate) 2 none
        ≤ policyTreeValue (boolBeliefTreeModel boolBayesUpdate)
            boolFeedbackTree none := optimalTreeValue_le_tree _ _ _
      _ = 0 := boolBayesTree_value_zero
      _ < 1 / 2 := by norm_num

end BooleanBayesianWitness

end FEP.PerceptionActionLoop
