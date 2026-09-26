"""Canonical Lean bodies for the wave-3 standalone formalizations."""

from __future__ import annotations

BODIES: dict[str, str] = {
    "fep-156": """import FepSketches.efe_policy_selection

namespace FEP156

open FEP.EFEPolicy
open FEP ActiveInference ControlledMarkov FiniteInformation PolicyTrees
  VariationalDuality Finset
open scoped BigOperators
variable {Action State Outcome Policy Belief Observation : Type*}
  [Fintype Action] [Fintype State] [Fintype Outcome] [Fintype Policy]
  [Fintype Belief] [Fintype Observation]

/-- **Planning as inference, Boltzmann form.**  For fixed precision `γ > 0`
the Boltzmann control posterior `Q*(π) ∝ prior(π) · exp(-γ · G π)` induced by
the expected free energy minimizes the KL-regularized expected-cost objective
`E_Q[G] + γ⁻¹ · KL(Q ‖ prior)` over all normalized policy laws, and it is the
unique minimizer: attaining the optimum happens exactly at `Q*`. -/
theorem fep156_boltzmann_control_posterior_minimizes_efe (prior : FiniteLaw Action)
    (prior_pos : ∀ policy, 0 < prior policy) (γ : ℝ) (hγ : 0 < γ)
    (cost : Action → ℝ) (Q : FiniteLaw Action) :
    efeControlObjective prior γ cost (controlPosterior prior γ cost) ≤
      efeControlObjective prior γ cost Q ∧
    (efeControlObjective prior γ cost Q =
        efeControlObjective prior γ cost (controlPosterior prior γ cost) ↔
      Q = controlPosterior prior γ cost) :=
  FEP.EFEPolicy.boltzmann_control_posterior_minimizes_efe prior prior_pos γ hγ cost Q

/-- The minimized value is the negative expected log-partition
`-γ⁻¹ · log Z` of the EFE tilt. -/
theorem fep156_boltzmann_control_posterior_minimal_value (prior : FiniteLaw Action)
    (prior_pos : ∀ policy, 0 < prior policy) (γ : ℝ) (hγ : 0 < γ)
    (cost : Action → ℝ) :
    efeControlObjective prior γ cost (controlPosterior prior γ cost) =
      -(γ⁻¹ * Real.log (efeControlPartition prior γ cost)) :=
  FEP.EFEPolicy.boltzmann_control_posterior_minimal_value prior prior_pos γ hγ cost

/-- Gibbs free-energy bridge: the divided KL-regularized objective equals
`γ⁻¹` times the Gibbs free energy of the EFE certificate. -/
theorem fep156_efeControlObjective_eq_gibbsFreeEnergy (prior : FiniteLaw Action)
    (prior_pos : ∀ policy, 0 < prior policy) (γ : ℝ) (hγ : 0 < γ)
    (cost : Action → ℝ) (Q : FiniteLaw Action) :
    efeControlObjective prior γ cost Q =
      γ⁻¹ * gibbsFreeEnergy (efeGibbsCertificate prior prior_pos γ cost) Q :=
  FEP.EFEPolicy.efeControlObjective_eq_gibbsFreeEnergy prior prior_pos γ hγ cost Q

/-- Planning-as-inference core identity: the KL-regularized expected-cost
objective at any candidate `Q` decomposes as `γ⁻¹ · KL(Q ‖ Q*)` plus the
negative expected log-partition. -/
theorem fep156_efeControlObjective_eq_kl_sub_logPartition (prior : FiniteLaw Action)
    (prior_pos : ∀ policy, 0 < prior policy) (γ : ℝ) (hγ : 0 < γ)
    (cost : Action → ℝ) (Q : FiniteLaw Action) :
    efeControlObjective prior γ cost Q =
      γ⁻¹ * (finiteKL Q (controlPosterior prior γ cost) -
        Real.log (efeControlPartition prior γ cost)) :=
  FEP.EFEPolicy.efeControlObjective_eq_kl_sub_logPartition prior prior_pos γ hγ cost Q

/-- Objective gap: any candidate law exceeds the control posterior's value by
exactly `γ⁻¹ · KL(Q ‖ Q*)`. -/
theorem fep156_efeControlObjective_sub_eq_kl (prior : FiniteLaw Action)
    (prior_pos : ∀ policy, 0 < prior policy) (γ : ℝ) (hγ : 0 < γ)
    (cost : Action → ℝ) (Q : FiniteLaw Action) :
    efeControlObjective prior γ cost Q -
        efeControlObjective prior γ cost (controlPosterior prior γ cost) =
      γ⁻¹ * finiteKL Q (controlPosterior prior γ cost) :=
  FEP.EFEPolicy.efeControlObjective_sub_eq_kl prior prior_pos γ hγ cost Q

/-- On a full-support generative model the EFE-argmin selection rule and the
risk-plus-ambiguity selection rule select the same policies: a policy
minimizes expected free energy exactly when it minimizes risk plus
ambiguity. -/
theorem fep156_argminEFE_eq_risk_add_ambiguity
    (model : GenerativeModel Policy State Outcome) (support : FullSupport model)
    (policy : Policy) :
    (∀ alternative : Policy,
        expectedFreeEnergy model policy ≤ expectedFreeEnergy model alternative) ↔
    (∀ alternative : Policy,
        risk model policy + ambiguity model policy ≤
          risk model alternative + ambiguity model alternative) :=
  FEP.EFEPolicy.argminEFE_eq_risk_add_ambiguity model support policy

/-- The finite EFE-argmin policy — the `finiteArgmin` selection whose
existence content is the `fep008` `exists_minG` owner — minimizes risk plus
ambiguity under full support. -/
theorem fep156_finiteArgminEFE_minimizes_risk_add_ambiguity
    (model : GenerativeModel Policy State Outcome) (support : FullSupport model)
    [Nonempty Policy] (alternative : Policy) :
    risk model (finiteArgmin (expectedFreeEnergy model)) +
        ambiguity model (finiteArgmin (expectedFreeEnergy model)) ≤
      risk model alternative + ambiguity model alternative :=
  FEP.EFEPolicy.finiteArgminEFE_minimizes_risk_add_ambiguity model support alternative

/-- An EFE-minimizing policy exists on every nonempty finite policy carrier
(the `exists_minG` content of `fep008` on the generative-model carrier). -/
theorem fep156_exists_EFE_minimizing_policy
    (model : GenerativeModel Policy State Outcome) [Nonempty Policy] :
    ∃ policy : Policy, ∀ alternative : Policy,
      expectedFreeEnergy model policy ≤ expectedFreeEnergy model alternative :=
  FEP.EFEPolicy.exists_EFE_minimizing_policy model

/-- The backward-inducted EFE-argmin tree, evaluated under the
risk-plus-ambiguity tree model, attains exactly the optimal
risk-plus-ambiguity value; and dually, the risk-plus-ambiguity-optimal tree
attains exactly the optimal EFE value. -/
theorem fep156_policyTree_value_agreement [Nonempty Action]
    (model : EFEPolicyTreeModel Belief State Action Observation)
    (depth : ℕ) (belief : Belief) :
    policyTreeValue (riskAmbiguityPolicyTreeModel model)
        (optimalPolicyTree (efePolicyTreeModel model) depth belief) belief =
      optimalTreeValue (riskAmbiguityPolicyTreeModel model) depth belief ∧
    policyTreeValue (efePolicyTreeModel model)
        (optimalPolicyTree (riskAmbiguityPolicyTreeModel model) depth belief)
          belief =
      optimalTreeValue (efePolicyTreeModel model) depth belief :=
  FEP.EFEPolicy.policyTree_value_agreement model depth belief

end FEP156
""",
    "fep-157": """import FepSketches.perception_action_loop

namespace FEP157

open FEP.PerceptionActionLoop
open FEP FEP.ActiveInference FEP.ControlledMarkov FEP.FiniteInformation
  FEP.TemporalInference Finset
open scoped BigOperators
variable {Policy State Outcome : Type*}
  [Fintype Policy] [Fintype State] [Fintype Outcome]

/-- The loop invariant at one full perception-update-select-predict step: the
stage outcome surprisal is bounded by the recognition's perception VFE with
the perception KL as the exact epistemic gap, and the selected policy's
expected free energy at the updated root splits into the certified
risk-plus-ambiguity budget. -/
theorem fep157_loop_invariant_surprisal_bound [Nonempty Policy]
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
            (selectedPolicy model (filteredBelief model belief outcome hEvidence)) :=
  FEP.PerceptionActionLoop.loop_invariant_surprisal_bound model belief outcome hEvidence support

/-- Perception chain-rule dual: the belief KL to a fully supported reference
splits exactly into the nonnegative outcome-marginal KL plus the
posterior-averaged KL of the updated beliefs. -/
theorem fep157_perception_kl_decomposition
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
              (predictive_pos_of_fullLikelihood model reference hLikelihood o)) :=
  FEP.PerceptionActionLoop.perception_kl_decomposition model actual reference hReference hLikelihood

/-- Perception-step KL non-increase (finite data processing): the
posterior-averaged KL of the updated beliefs to the reference beliefs never
exceeds the pre-update belief KL.  The dropped summand is the nonnegative
outcome-marginal KL, which is the exact gap in
`perception_kl_decomposition`. -/
theorem fep157_perception_step_kl_nonincrease
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
      finiteKL actual reference :=
  FEP.PerceptionActionLoop.perception_step_kl_nonincrease model actual reference hReference hLikelihood

/-- Native data processing along the perception channel: pushing both beliefs
through the model likelihood cannot increase their native Mathlib KL. -/
theorem fep157_perception_native_kl_nonincrease
    [MeasurableSpace State] [MeasurableSpace Outcome]
    [DiscreteMeasurableSpace State] [DiscreteMeasurableSpace Outcome]
    (model : GenerativeModel Policy State Outcome)
    (actual reference : FiniteLaw State) :
    InformationTheory.klDiv
        (FEP.NativeBlanket.embeddedLaw (model.likelihood.predictive actual))
        (FEP.NativeBlanket.embeddedLaw (model.likelihood.predictive reference)) ≤
      InformationTheory.klDiv (FEP.NativeBlanket.embeddedLaw actual)
        (FEP.NativeBlanket.embeddedLaw reference) :=
  FEP.PerceptionActionLoop.perception_native_kl_nonincrease model actual reference

/-- The act-predict stage is Dobrushin-contractive in total variation whenever
the selected policy's transition kernel carries an explicit contraction
certificate. -/
theorem fep157_prediction_dobrushin_contraction [DecidableEq State]
    (model : GenerativeModel Policy State Outcome) (policy : Policy)
    {coefficient : ℝ}
    (hBound : FEP.FiniteMarkovDynamics.HasDobrushinBound
      (model.transition policy) coefficient)
    (left right : FiniteLaw State) :
    FEP.FiniteMarkovDynamics.totalVariation
        ((model.transition policy).predictive left)
        ((model.transition policy).predictive right) ≤
      coefficient * FEP.FiniteMarkovDynamics.totalVariation left right :=
  FEP.PerceptionActionLoop.prediction_dobrushin_contraction model policy hBound left right

/-- Perception VFE collapse: the pre-update recognition's perception VFE
decomposes exactly into the stage outcome surprisal plus the perception KL,
the exact epistemic gap closed by the Bayesian update. -/
theorem fep157_perceptionVFE_gap
    (model : GenerativeModel Policy State Outcome) (belief : FiniteLaw State)
    (outcome : Outcome)
    (hEvidence : 0 < model.likelihood.predictive belief outcome) :
    perceptionVFE model belief outcome hEvidence belief =
      -Real.log (model.likelihood.predictive belief outcome) +
        finiteKL belief (filteredBelief model belief outcome hEvidence) :=
  FEP.PerceptionActionLoop.perceptionVFE_gap model belief outcome hEvidence

/-- The loop's Boltzmann policy law coincides with the house control posterior:
energy equals precision times expected free energy. -/
theorem fep157_policyPosterior_eq_controlPosterior (precision : ℝ)
    (model : GenerativeModel Policy State Outcome)
    (support : FullSupport model) :
    policyPosterior precision model support =
      controlPosterior model.policyPrior precision (expectedFreeEnergy model) :=
  FEP.PerceptionActionLoop.policyPosterior_eq_controlPosterior precision model support

/-- At a fixed point of the perception-action loop whose expected-free-energy
landscape is constant, the loop's Boltzmann policy law at the chosen precision
is exactly the policy prior. -/
theorem fep157_loop_fixed_point_is_boltzmann (precision : ℝ)
    (model : GenerativeModel Policy State Outcome)
    (support : FullSupport model) (energy : ℝ)
    (hflat : ∀ policy, expectedFreeEnergy model policy = energy) :
    policyPosterior precision model support = model.policyPrior :=
  FEP.PerceptionActionLoop.loop_fixed_point_is_boltzmann precision model support energy hflat

/-- The selected policy minimizes the stage expected free energy at its root. -/
theorem fep157_selectedPolicy_minimizes [Nonempty Policy]
    (model : GenerativeModel Policy State Outcome) (belief : FiniteLaw State)
    (alternative : Policy) :
    expectedFreeEnergy (withInitialState model belief)
        (selectedPolicy model belief) ≤
      expectedFreeEnergy (withInitialState model belief) alternative :=
  FEP.PerceptionActionLoop.selectedPolicy_minimizes model belief alternative

/-- The perception update is exactly the identity-transition forward filter of
the temporal-inference layer. -/
theorem fep157_filteredBelief_eq_forwardFilter [DecidableEq State]
    (model : GenerativeModel Policy State Outcome) (belief : FiniteLaw State)
    (outcome : Outcome)
    (hEvidence : 0 < model.likelihood.predictive belief outcome) :
    filteredBelief model belief outcome hEvidence =
      forwardFilter belief FiniteKernel.identity model.likelihood outcome
        (identity_forwardEvidence belief outcome FiniteKernel.identity rfl
          model.likelihood hEvidence) :=
  FEP.PerceptionActionLoop.filteredBelief_eq_forwardFilter model belief outcome hEvidence

/-- The one-policy rollout prediction of the loop step is exactly one
transition of the selected policy. -/
theorem fep157_perceptionActionStep_eq [Nonempty Policy] [DecidableEq State]
    (model : GenerativeModel Policy State Outcome) (belief : FiniteLaw State)
    (outcome : Outcome)
    (hEvidence : 0 < model.likelihood.predictive belief outcome) :
    perceptionActionStep model belief outcome hEvidence =
      (model.transition (selectedPolicy model
        (filteredBelief model belief outcome hEvidence))).predictive
        (filteredBelief model belief outcome hEvidence) :=
  FEP.PerceptionActionLoop.perceptionActionStep_eq model belief outcome hEvidence

/-- Each kernel row of the loop kernel is exactly one loop step. -/
theorem fep157_perceptionActionKernel_apply [Nonempty Policy] [DecidableEq State]
    (model : GenerativeModel Policy State Outcome) (belief : FiniteLaw State)
    (hEvidence : ∀ o : Outcome, 0 < model.likelihood.predictive belief o)
    (outcome : Outcome) (state : State) :
    perceptionActionKernel model belief hEvidence outcome state =
      perceptionActionStep model belief outcome (hEvidence outcome) state :=
  FEP.PerceptionActionLoop.perceptionActionKernel_apply model belief hEvidence outcome state

/-- Posterior reconstruction at the joint level: the posterior-kernel joint has
exactly the swapped masses of the likelihood joint. -/
theorem fep157_posteriorKernel_joint_eq_swap
    (model : GenerativeModel Policy State Outcome) (prior : FiniteLaw State)
    (hEvidence : ∀ o, 0 < model.likelihood.predictive prior o)
    (o : Outcome) (s : State) :
    (posteriorKernel model prior hEvidence).joint
        (model.likelihood.predictive prior) (o, s) =
      (model.likelihood.joint prior) (s, o) :=
  FEP.PerceptionActionLoop.posteriorKernel_joint_eq_swap model prior hEvidence o s

end FEP157
""",
    "fep-158": """import FepSketches.bayesian_model_reduction

namespace FEP158

open FEP.BayesianModelReduction
open FEP FEP.FiniteInformation FEP.VariationalDuality Finset
open scoped BigOperators
variable {Parameter Evidence : Type*} [Fintype Parameter] [Fintype Evidence]
open MeasureTheory ProbabilityTheory FEP.GaussianInformationGeometry in

/-- Reduction weakly raises the evidence free energy: the full model's
evidence free energy is at most the reduced model's, because masked evidence
never exceeds full evidence and `-log` is decreasing in the evidence. -/
theorem fep158_reduction_free_energy_monotone (prior : FiniteLaw Parameter)
    (weight : Parameter → ℝ) (kernel : FiniteKernel Parameter Evidence)
    (data : Evidence) (hw1 : ∀ x, weight x ≤ 1)
    (hE : 0 < maskedEvidence prior weight kernel data) :
    evidenceFreeEnergy (kernel.predictive prior data) ≤
      evidenceFreeEnergy (maskedEvidence prior weight kernel data) :=
  FEP.BayesianModelReduction.reduction_free_energy_monotone prior weight kernel data hw1 hE

/-- Masked evidence never exceeds the full evidence: the discarded residual
mass `(1 - weight x) * prior x * kernel x data` is nonnegative. -/
theorem fep158_maskedEvidence_le_predictive (prior : FiniteLaw Parameter)
    (weight : Parameter → ℝ) (kernel : FiniteKernel Parameter Evidence)
    (data : Evidence) (hw1 : ∀ x, weight x ≤ 1) :
    maskedEvidence prior weight kernel data ≤ kernel.predictive prior data :=
  FEP.BayesianModelReduction.maskedEvidence_le_predictive prior weight kernel data hw1

/-- The reduced predictive mass is the masked evidence divided by the
weighted prior mass. -/
theorem fep158_maskedPrior_predictive_eq (prior : FiniteLaw Parameter)
    (weight : Parameter → ℝ) (kernel : FiniteKernel Parameter Evidence)
    (data : Evidence) (hw : ∀ x, 0 ≤ weight x)
    (hZ : 0 < ∑ x, weight x * prior x) :
    kernel.predictive (maskedPrior prior weight hw hZ) data =
      maskedEvidence prior weight kernel data / ∑ y, weight y * prior y :=
  FEP.BayesianModelReduction.maskedPrior_predictive_eq prior weight kernel data hw hZ

/-- The reduced posterior keeps the multiplicative Bayes form: posterior
mass times masked evidence equals the weighted joint mass. -/
theorem fep158_reduction_posterior_reconstruction (prior : FiniteLaw Parameter)
    (weight : Parameter → ℝ) (kernel : FiniteKernel Parameter Evidence)
    (data : Evidence) (hw : ∀ x, 0 ≤ weight x)
    (hZ : 0 < ∑ x, weight x * prior x)
    (hy : 0 < kernel.predictive (maskedPrior prior weight hw hZ) data)
    (x : Parameter) :
    FiniteKernel.posterior (maskedPrior prior weight hw hZ) kernel data hy x *
        maskedEvidence prior weight kernel data =
      weight x * prior x * kernel x data :=
  FEP.BayesianModelReduction.reduction_posterior_reconstruction prior weight kernel data hw hZ hy x

/-- Reduction odds: the reduced posterior odds at two states are the
evidence-weighted prior odds, the exact multiplicative form of the Bayes
factor reduction. -/
theorem fep158_reduction_posterior_odds (prior : FiniteLaw Parameter)
    (weight : Parameter → ℝ) (kernel : FiniteKernel Parameter Evidence)
    (data : Evidence) (hw : ∀ x, 0 ≤ weight x)
    (hZ : 0 < ∑ x, weight x * prior x)
    (hy : 0 < kernel.predictive (maskedPrior prior weight hw hZ) data)
    (x y : Parameter) :
    FiniteKernel.posterior (maskedPrior prior weight hw hZ) kernel data hy x *
        (weight y * prior y * kernel y data) =
      FiniteKernel.posterior (maskedPrior prior weight hw hZ) kernel data hy y *
        (weight x * prior x * kernel x data) :=
  FEP.BayesianModelReduction.reduction_posterior_odds prior weight kernel data hw hZ hy x y

/-- The reduced posterior reconstructs the full posterior through the
evidence ratio: reduced posterior mass equals full posterior mass times the
reduction weight times the ratio of full evidence to masked evidence.  This
is the multiplicative conditional form of the reduction pushforward. -/
theorem fep158_reduced_posterior_reconstructs (prior : FiniteLaw Parameter)
    (weight : Parameter → ℝ) (kernel : FiniteKernel Parameter Evidence)
    (data : Evidence) (hw : ∀ x, 0 ≤ weight x)
    (hZ : 0 < ∑ x, weight x * prior x)
    (hP : 0 < kernel.predictive prior data)
    (hE : 0 < maskedEvidence prior weight kernel data)
    (hy : 0 < kernel.predictive (maskedPrior prior weight hw hZ) data)
    (x : Parameter) :
    FiniteKernel.posterior (maskedPrior prior weight hw hZ) kernel data hy x =
      FiniteKernel.posterior prior kernel data hP x * weight x *
        (kernel.predictive prior data /
          maskedEvidence prior weight kernel data) :=
  FEP.BayesianModelReduction.reduced_posterior_reconstructs prior weight kernel data hw hZ hP hE hy x

/-- The Gibbs free energy is the negative Donsker--Varadhan objective. -/
theorem fep158_gibbsFreeEnergy_eq_neg_dvObjective (c : GibbsCertificate Parameter)
    (cand : FiniteLaw Parameter) :
    gibbsFreeEnergy c cand = -dvObjective c cand :=
  FEP.BayesianModelReduction.gibbsFreeEnergy_eq_neg_dvObjective c cand

/-- The free-energy change against the Gibbs optimizer is exactly the KL
divergence to the optimizer: the Donsker--Varadhan duality gap. -/
theorem fep158_reduction_free_energy_change_eq_kl (c : GibbsCertificate Parameter)
    (cand : FiniteLaw Parameter) :
    gibbsFreeEnergy c cand - gibbsFreeEnergy c c.optimizer =
      finiteKL cand c.optimizer :=
  FEP.BayesianModelReduction.reduction_free_energy_change_eq_kl c cand

/-- Reduction to the Gibbs optimizer never lowers the free energy: the
candidate's free energy is at least the optimizer's, with the excess exactly
the KL divergence to the optimizer. -/
theorem fep158_reduction_free_energy_monotone_gibbs
    (c : GibbsCertificate Parameter) (cand : FiniteLaw Parameter) :
    gibbsFreeEnergy c c.optimizer ≤ gibbsFreeEnergy c cand :=
  FEP.BayesianModelReduction.reduction_free_energy_monotone_gibbs c cand

open MeasureTheory ProbabilityTheory FEP.GaussianInformationGeometry in
/-- For the pinned fixed-variance Gaussian family, the log Bayes factor of
the natural-coordinate tilt against the zero-mean base law is the natural
coordinate times the datum minus the natural log partition: the Bayes
factor reduces to the natural-log-partition difference in the pinned
charts. -/
theorem fep158_gaussianLogBayesFactor_eq (family : FixedVarianceGaussian)
    (natural x : ℝ) :
    Real.log
        (gaussianPDFReal (family.naturalToMean natural) family.variance x /
          gaussianPDFReal 0 family.variance x) =
      natural * x - family.naturalLogPartition natural :=
  FEP.BayesianModelReduction.gaussianLogBayesFactor_eq family natural x

end FEP158
""",
    "fep-159": """import FepSketches.efe_time_scale_separation

namespace FEP159

open FEP.TimeScaleEFE
open FEP FEP.FiniteInformation FEP.ContinuousTimeMarkov FEP.PathThermodynamics
  FEP.ActiveInference FEP.VariationalDuality Finset
open scoped BigOperators

/-- **Theorem 1 (`epistemic_gain_bounded_by_affinity`).**  The policy-relevant
information gap of the belief is bounded by the entropy-production rate
`σ = J * A` scaled by the relaxation time `1 / decayRate`. -/
theorem fep159_epistemic_gain_bounded_by_affinity (rates : TwoStateRates)
    (belief : FiniteLaw Bool) (hSupport : ∀ i, 0 < belief i) :
    finiteKL belief rates.stationaryLaw ≤
      productionRate rates belief / rates.decayRate :=
  FEP.TimeScaleEFE.epistemic_gain_bounded_by_affinity rates belief hSupport

/-- **Theorem 1, EFE form.**  The expected free energy of the two-state
observing agent is bounded by the entropy-production rate scaled by the
relaxation time. -/
theorem fep159_expectedFreeEnergy_le_productionRate_div_decayRate (rates : TwoStateRates)
    (belief : FiniteLaw Bool) (hSupport : ∀ i, 0 < belief i)
    (time : ℝ) (hTime : 0 ≤ time) (policy : Bool) :
    expectedFreeEnergy (twoStateModel rates belief time hTime) policy ≤
      productionRate rates belief / rates.decayRate :=
  FEP.TimeScaleEFE.expectedFreeEnergy_le_productionRate_div_decayRate rates belief hSupport time hTime policy

/-- **Theorem 2 (`slow_fast_separation_statement`).**  The evolved
policy-relevant information gap is bounded by the squared relaxation factor
times the initial gap: information contracts to the invariant measure on the
relaxation timescale, so the information timescale is twice the mass
relaxation timescale. -/
theorem fep159_slow_fast_separation_statement (rates : TwoStateRates)
    (belief : FiniteLaw Bool) (time : ℝ) (hTime : 0 ≤ time) :
    epistemicGain rates belief time hTime ≤
      rates.rho time ^ 2 *
        ((belief true - rates.stationaryTrue) ^ 2 /
          (rates.stationaryTrue * rates.stationaryFalse)) :=
  FEP.TimeScaleEFE.slow_fast_separation_statement rates belief time hTime

/-- **Theorem 2, limit form.**  Under the `1 / eps` rate scaling the
policy-relevant gain after a fixed positive action time vanishes as
`eps → 0⁺`; on the tuned branch the explicit witness is
`eps = decayRate * time / (-log (delta / chi0))`. -/
theorem fep159_fastRelaxation_epistemic_vanishes (rates : TwoStateRates)
    (belief : FiniteLaw Bool) (time : ℝ) (hpos : 0 < time) :
    ∀ δ : ℝ, 0 < δ → ∃ eps : ℝ, 0 < eps ∧ ∀ (hTime : 0 ≤ time) (heps : 0 < eps),
      epistemicGain (scaledRates rates eps heps) belief time hTime ≤ δ :=
  FEP.TimeScaleEFE.fastRelaxation_epistemic_vanishes rates belief time hpos

/-- **Theorem 3 (`slicePath_entropyProduction_eq`).**  The one-slice path-space
entropy production of `FEP.PathThermodynamics` equals `(1 - rho time) * σ /
decayRate`: the generator entropy-production rate `σ = J * A` is exactly the
per-unit-relaxation path-space dissipation rate. -/
theorem fep159_slicePath_entropyProduction_eq (rates : TwoStateRates)
    (belief : FiniteLaw Bool) (hSupport : ∀ i, 0 < belief i)
    (time : ℝ) (hTime : 0 ≤ time) (hpos : 0 < time) :
    entropyProduction (slicePathProtocol rates belief time hTime)
      = (1 - rates.rho time) * productionRate rates belief / rates.decayRate :=
  FEP.TimeScaleEFE.slicePath_entropyProduction_eq rates belief hSupport time hTime hpos

/-- The generator affinity coincides with `FEP.PathThermodynamics.localAffinity`
of the semigroup slice at every positive sampling time. -/
theorem fep159_beliefAffinity_eq_localAffinity (rates : TwoStateRates)
    (belief : FiniteLaw Bool) (hSupport : ∀ i, 0 < belief i)
    (time : ℝ) (hTime : 0 < time) :
    beliefAffinity rates belief =
      localAffinity belief (rates.certifiedSemigroup.kernel time hTime.le) false true :=
  FEP.TimeScaleEFE.beliefAffinity_eq_localAffinity rates belief hSupport time hTime

/-- The entropy-production rate is nonnegative at a fully supported belief. -/
theorem fep159_productionRate_nonneg (rates : TwoStateRates) (belief : FiniteLaw Bool)
    (hSupport : ∀ i, 0 < belief i) : 0 ≤ productionRate rates belief :=
  FEP.TimeScaleEFE.productionRate_nonneg rates belief hSupport

/-- For the two-state observing agent the expected free energy of every
policy is exactly the belief information gap: `risk` is the gap and the
perfect-observation ambiguity vanishes. -/
theorem fep159_twoStateModel_expectedFreeEnergy (rates : TwoStateRates)
    (belief : FiniteLaw Bool) (hSupport : ∀ i, 0 < belief i)
    (time : ℝ) (hTime : 0 ≤ time) (policy : Bool) :
    expectedFreeEnergy (twoStateModel rates belief time hTime) policy =
      epistemicGain rates belief time hTime :=
  FEP.TimeScaleEFE.twoStateModel_expectedFreeEnergy rates belief hSupport time hTime policy

/-- Under the `1 / eps` rate scaling the evolved gain is bounded by the squared
scaled relaxation factor times the initial gap. -/
theorem fep159_epistemicGain_rateScaling (rates : TwoStateRates) (belief : FiniteLaw Bool)
    (time : ℝ) (hTime : 0 ≤ time) (eps : ℝ) (heps : 0 < eps) :
    epistemicGain (scaledRates rates eps heps) belief time hTime ≤
      Real.exp (-(rates.decayRate / eps) * time) ^ 2 *
        ((belief true - rates.stationaryTrue) ^ 2 /
          (rates.stationaryTrue * rates.stationaryFalse)) :=
  FEP.TimeScaleEFE.epistemicGain_rateScaling rates belief time hTime eps heps

end FEP159
""",
}
