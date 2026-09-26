import FepSketches.controlled_markov
import FepSketches.policy_tree
import FepSketches.variational_duality

/-!
# Planning as inference: the EFE policy-selection bridge

Three finite-carrier results connect expected-free-energy (EFE) policy
selection to the risk-plus-ambiguity decomposition and to
control-as-inference:

1. With fixed precision `γ > 0`, the Boltzmann control posterior
   `Q*(π) ∝ prior(π) · exp(-γ · G(π))` is the unique minimizer of the
   KL-regularized expected-cost objective `E_Q[G] + γ⁻¹ · KL(Q ‖ prior)`;
   the minimized value is `-γ⁻¹ · log Z` (Gibbs / Donsker-Varadhan algebra
   on the finite carrier, reusing the `GibbsCertificate` duality).
2. Under full support, minimizing expected free energy and minimizing risk
   plus ambiguity select the same policies; the finite argmin exists and is
   selected by the existing `finiteArgmin` owner.
3. On depth-indexed policy trees, the backward-inducted EFE-argmin tree
   attains exactly the optimal risk-plus-ambiguity value, and dually.

All proofs reuse the shared `FiniteLaw`/`FiniteKernel` substrate and the
one-step full-support EFE identity.  No new axioms are introduced.
-/

namespace FEP.EFEPolicy

open FEP ActiveInference ControlledMarkov FiniteInformation PolicyTrees
  VariationalDuality Finset
open scoped BigOperators

variable {Action State Outcome Policy Belief Observation : Type*}
  [Fintype Action] [Fintype State] [Fintype Outcome] [Fintype Policy]
  [Fintype Belief] [Fintype Observation]

/-! ## Control as inference: the EFE Gibbs certificate -/

/-- Partition function of the EFE-induced exponential tilt:
`Z = ∑ π, prior π · exp(-γ · G π)`. -/
noncomputable def efeControlPartition (prior : FiniteLaw Action) (γ : ℝ)
    (cost : Action → ℝ) : ℝ :=
  boltzmannPartition prior (fun policy => γ * cost policy)

/-- KL-regularized expected-cost objective over candidate policy laws:
`E_Q[G] + γ⁻¹ · KL(Q ‖ prior)`. -/
noncomputable def efeControlObjective (prior : FiniteLaw Action) (γ : ℝ)
    (cost : Action → ℝ) (Q : FiniteLaw Action) : ℝ :=
  expectation Q cost + γ⁻¹ * finiteKL Q prior

/-- Gibbs certificate for the EFE tilt: reference `prior`, optimizer the
Boltzmann control posterior `Q*(π) ∝ prior(π) · exp(-γ · G π)`, potential
`-γ · G`, and log partition `log Z`. -/
noncomputable def efeGibbsCertificate (prior : FiniteLaw Action)
    (prior_pos : ∀ policy, 0 < prior policy) (γ : ℝ) (cost : Action → ℝ) :
    GibbsCertificate Action where
  reference := prior
  optimizer := controlPosterior prior γ cost
  potential := fun policy => -γ * cost policy
  logPartition := Real.log (efeControlPartition prior γ cost)
  reference_pos := prior_pos
  optimizer_pos := fun policy => by
    have hZ : 0 < efeControlPartition prior γ cost :=
      boltzmannPartition_pos prior _
    exact div_pos (mul_pos (prior_pos policy) (Real.exp_pos _)) hZ
  log_optimizer := by
    intro policy
    have hZ : 0 < efeControlPartition prior γ cost :=
      boltzmannPartition_pos prior _
    have hmass : controlPosterior prior γ cost policy =
        prior policy * Real.exp (-(γ * cost policy)) /
          efeControlPartition prior γ cost := rfl
    have hnum : 0 < prior policy * Real.exp (-(γ * cost policy)) :=
      mul_pos (prior_pos policy) (Real.exp_pos _)
    rw [hmass, Real.log_div (ne_of_gt hnum) (ne_of_gt hZ),
      Real.log_mul (ne_of_gt (prior_pos policy))
        (ne_of_gt (Real.exp_pos _)), Real.log_exp]
    ring

/-- Gibbs free-energy bridge: the divided KL-regularized objective equals
`γ⁻¹` times the Gibbs free energy of the EFE certificate. -/
theorem efeControlObjective_eq_gibbsFreeEnergy (prior : FiniteLaw Action)
    (prior_pos : ∀ policy, 0 < prior policy) (γ : ℝ) (hγ : 0 < γ)
    (cost : Action → ℝ) (Q : FiniteLaw Action) :
    efeControlObjective prior γ cost Q =
      γ⁻¹ * gibbsFreeEnergy (efeGibbsCertificate prior prior_pos γ cost) Q := by
  have hexp : ∑ policy, Q policy * (-γ * cost policy) =
      -(γ * ∑ policy, Q policy * cost policy) := by
    have hterm : ∀ policy : Action,
        Q policy * (-γ * cost policy) = -(γ * (Q policy * cost policy)) :=
      fun policy => by ring
    rw [Finset.sum_congr rfl (fun policy _ => hterm policy),
      Finset.sum_neg_distrib, Finset.mul_sum]
  unfold efeControlObjective gibbsFreeEnergy
  simp only [efeGibbsCertificate, expectation]
  rw [hexp]
  field_simp
  ring

/-- Planning-as-inference core identity: the KL-regularized expected-cost
objective at any candidate `Q` decomposes as `γ⁻¹ · KL(Q ‖ Q*)` plus the
negative expected log-partition. -/
theorem efeControlObjective_eq_kl_sub_logPartition (prior : FiniteLaw Action)
    (prior_pos : ∀ policy, 0 < prior policy) (γ : ℝ) (hγ : 0 < γ)
    (cost : Action → ℝ) (Q : FiniteLaw Action) :
    efeControlObjective prior γ cost Q =
      γ⁻¹ * (finiteKL Q (controlPosterior prior γ cost) -
        Real.log (efeControlPartition prior γ cost)) := by
  have hneg : gibbsFreeEnergy (efeGibbsCertificate prior prior_pos γ cost) Q =
      finiteKL Q (controlPosterior prior γ cost) -
        Real.log (efeControlPartition prior γ cost) := by
    have hdv := dvObjective_eq_logPartition_sub_kl
      (efeGibbsCertificate prior prior_pos γ cost) Q
    have hform : gibbsFreeEnergy (efeGibbsCertificate prior prior_pos γ cost) Q =
        -dvObjective (efeGibbsCertificate prior prior_pos γ cost) Q := by
      unfold gibbsFreeEnergy dvObjective
      ring
    rw [hform, hdv]
    simp only [efeGibbsCertificate]
    ring
  rw [efeControlObjective_eq_gibbsFreeEnergy prior prior_pos γ hγ cost Q, hneg]

/-- Objective gap: any candidate law exceeds the control posterior's value by
exactly `γ⁻¹ · KL(Q ‖ Q*)`. -/
theorem efeControlObjective_sub_eq_kl (prior : FiniteLaw Action)
    (prior_pos : ∀ policy, 0 < prior policy) (γ : ℝ) (hγ : 0 < γ)
    (cost : Action → ℝ) (Q : FiniteLaw Action) :
    efeControlObjective prior γ cost Q -
        efeControlObjective prior γ cost (controlPosterior prior γ cost) =
      γ⁻¹ * finiteKL Q (controlPosterior prior γ cost) := by
  rw [efeControlObjective_eq_kl_sub_logPartition prior prior_pos γ hγ cost Q,
    efeControlObjective_eq_kl_sub_logPartition prior prior_pos γ hγ cost
      (controlPosterior prior γ cost), finiteKL_self]
  field_simp
  ring

/-- **Planning as inference, Boltzmann form.**  For fixed precision `γ > 0`
the Boltzmann control posterior `Q*(π) ∝ prior(π) · exp(-γ · G π)` induced by
the expected free energy minimizes the KL-regularized expected-cost objective
`E_Q[G] + γ⁻¹ · KL(Q ‖ prior)` over all normalized policy laws, and it is the
unique minimizer: attaining the optimum happens exactly at `Q*`. -/
theorem boltzmann_control_posterior_minimizes_efe (prior : FiniteLaw Action)
    (prior_pos : ∀ policy, 0 < prior policy) (γ : ℝ) (hγ : 0 < γ)
    (cost : Action → ℝ) (Q : FiniteLaw Action) :
    efeControlObjective prior γ cost (controlPosterior prior γ cost) ≤
      efeControlObjective prior γ cost Q ∧
    (efeControlObjective prior γ cost Q =
        efeControlObjective prior γ cost (controlPosterior prior γ cost) ↔
      Q = controlPosterior prior γ cost) := by
  have hdiff := efeControlObjective_sub_eq_kl prior prior_pos γ hγ cost Q
  refine ⟨?_, ?_⟩
  · have hgap : 0 ≤ efeControlObjective prior γ cost Q -
        efeControlObjective prior γ cost (controlPosterior prior γ cost) := by
      rw [hdiff]
      exact mul_nonneg (inv_nonneg.mpr hγ.le) (finiteKL_nonneg _ _)
    linarith
  · constructor
    · intro heq
      have hzero : γ⁻¹ * finiteKL Q (controlPosterior prior γ cost) = 0 := by
        rw [← hdiff]
        linarith
      have hkl : finiteKL Q (controlPosterior prior γ cost) = 0 := by
        rcases mul_eq_zero.mp hzero with h | h
        · exact absurd h (inv_ne_zero (ne_of_gt hγ))
        · exact h
      exact (finiteKL_eq_zero_iff Q _).mp hkl
    · intro hQ
      rw [hQ]

/-- The minimized value is the negative expected log-partition
`-γ⁻¹ · log Z` of the EFE tilt. -/
theorem boltzmann_control_posterior_minimal_value (prior : FiniteLaw Action)
    (prior_pos : ∀ policy, 0 < prior policy) (γ : ℝ) (hγ : 0 < γ)
    (cost : Action → ℝ) :
    efeControlObjective prior γ cost (controlPosterior prior γ cost) =
      -(γ⁻¹ * Real.log (efeControlPartition prior γ cost)) := by
  rw [efeControlObjective_eq_kl_sub_logPartition prior prior_pos γ hγ cost
    (controlPosterior prior γ cost), finiteKL_self, zero_sub]
  ring

/-! ## The finite EFE-argmin policy minimizes risk plus ambiguity -/

/-- On a full-support generative model the EFE-argmin selection rule and the
risk-plus-ambiguity selection rule select the same policies: a policy
minimizes expected free energy exactly when it minimizes risk plus
ambiguity. -/
theorem argminEFE_eq_risk_add_ambiguity
    (model : GenerativeModel Policy State Outcome) (support : FullSupport model)
    (policy : Policy) :
    (∀ alternative : Policy,
        expectedFreeEnergy model policy ≤ expectedFreeEnergy model alternative) ↔
    (∀ alternative : Policy,
        risk model policy + ambiguity model policy ≤
          risk model alternative + ambiguity model alternative) := by
  constructor
  · intro hmin alternative
    rw [← expectedFreeEnergy_eq_risk_add_ambiguity model policy support,
      ← expectedFreeEnergy_eq_risk_add_ambiguity model alternative support]
    exact hmin alternative
  · intro hmin alternative
    rw [expectedFreeEnergy_eq_risk_add_ambiguity model policy support,
      expectedFreeEnergy_eq_risk_add_ambiguity model alternative support]
    exact hmin alternative

/-- The finite EFE-argmin policy — the `finiteArgmin` selection whose
existence content is the `fep008` `exists_minG` owner — minimizes risk plus
ambiguity under full support. -/
theorem finiteArgminEFE_minimizes_risk_add_ambiguity
    (model : GenerativeModel Policy State Outcome) (support : FullSupport model)
    [Nonempty Policy] (alternative : Policy) :
    risk model (finiteArgmin (expectedFreeEnergy model)) +
        ambiguity model (finiteArgmin (expectedFreeEnergy model)) ≤
      risk model alternative + ambiguity model alternative := by
  rw [← expectedFreeEnergy_eq_risk_add_ambiguity model alternative support,
    ← expectedFreeEnergy_eq_risk_add_ambiguity model
      (finiteArgmin (expectedFreeEnergy model)) support]
  exact finiteArgmin_le _ alternative

/-- An EFE-minimizing policy exists on every nonempty finite policy carrier
(the `exists_minG` content of `fep008` on the generative-model carrier). -/
theorem exists_EFE_minimizing_policy
    (model : GenerativeModel Policy State Outcome) [Nonempty Policy] :
    ∃ policy : Policy, ∀ alternative : Policy,
      expectedFreeEnergy model policy ≤ expectedFreeEnergy model alternative :=
  exists_finite_minimizer _

/-! ## Tree-level agreement of the EFE and risk-plus-ambiguity optima -/

/-- The backward-inducted EFE-argmin tree, evaluated under the
risk-plus-ambiguity tree model, attains exactly the optimal
risk-plus-ambiguity value; and dually, the risk-plus-ambiguity-optimal tree
attains exactly the optimal EFE value. -/
theorem policyTree_value_agreement [Nonempty Action]
    (model : EFEPolicyTreeModel Belief State Action Observation)
    (depth : ℕ) (belief : Belief) :
    policyTreeValue (riskAmbiguityPolicyTreeModel model)
        (optimalPolicyTree (efePolicyTreeModel model) depth belief) belief =
      optimalTreeValue (riskAmbiguityPolicyTreeModel model) depth belief ∧
    policyTreeValue (efePolicyTreeModel model)
        (optimalPolicyTree (riskAmbiguityPolicyTreeModel model) depth belief)
          belief =
      optimalTreeValue (efePolicyTreeModel model) depth belief := by
  constructor
  · calc
      policyTreeValue (riskAmbiguityPolicyTreeModel model)
          (optimalPolicyTree (efePolicyTreeModel model) depth belief) belief
        = policyTreeValue (efePolicyTreeModel model)
            (optimalPolicyTree (efePolicyTreeModel model) depth belief) belief :=
            (policyTree_efe_eq_risk_add_ambiguity model
              (optimalPolicyTree (efePolicyTreeModel model) depth belief)
              belief).symm
      _ = optimalTreeValue (efePolicyTreeModel model) depth belief :=
          optimalPolicyTree_value (efePolicyTreeModel model) depth belief
      _ = optimalTreeValue (riskAmbiguityPolicyTreeModel model) depth belief :=
          optimalEFEValue_eq_riskAmbiguity model depth belief
  · calc
      policyTreeValue (efePolicyTreeModel model)
          (optimalPolicyTree (riskAmbiguityPolicyTreeModel model) depth belief)
          belief
        = policyTreeValue (riskAmbiguityPolicyTreeModel model)
            (optimalPolicyTree (riskAmbiguityPolicyTreeModel model) depth belief)
            belief :=
            policyTree_efe_eq_risk_add_ambiguity model
              (optimalPolicyTree (riskAmbiguityPolicyTreeModel model)
                depth belief) belief
      _ = optimalTreeValue (riskAmbiguityPolicyTreeModel model) depth belief :=
          optimalPolicyTree_value (riskAmbiguityPolicyTreeModel model)
            depth belief
      _ = optimalTreeValue (efePolicyTreeModel model) depth belief :=
          (optimalEFEValue_eq_riskAmbiguity model depth belief).symm

end FEP.EFEPolicy
