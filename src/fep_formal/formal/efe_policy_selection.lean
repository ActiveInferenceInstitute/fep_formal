module
public import FepSketches.controlled_markov
public import FepSketches.policy_tree
public import FepSketches.variational_duality

@[expose] public section

/-!
# Planning as inference: the EFE policy-selection bridge

Three finite-carrier results connect expected-free-energy (EFE) policy
selection to the risk-plus-ambiguity decomposition and to
control-as-inference:

1. With fixed precision `γ > 0`, the Boltzmann control posterior
   `Q*(π) ∝ prior(π) · exp(-γ · G(π))` is the unique minimizer of the
   KL-regularized expected-cost objective `E_Q[G] + γ⁻¹ · KL(Q ‖ prior)`;
   the minimized value is `-γ⁻¹ · log Z` (Gibbs / Donsker-Varadhan algebra
   on the finite carrier). The candidate must be supported by the prior;
   the prior may contain zero-mass policies. Released full-support results
   remain special cases, including the constructive `GibbsCertificate`.
2. Under full support, minimizing expected free energy and minimizing risk
   plus ambiguity select the same policies; the finite argmin exists and is
   selected by the existing `finiteArgmin` owner.
3. On depth-indexed policy trees, the backward-inducted EFE-argmin tree
   attains exactly the optimal risk-plus-ambiguity value, and dually.

The scaled Gibbs gap holds for every real precision. The divided objective
has a unique maximum at negative precision, while zero precision removes its
KL penalty. Explicit countermodels show why candidate support and the sign of
precision matter under finite totalized real KL. All proofs reuse the shared
`FiniteLaw`/`FiniteKernel` substrate; the risk-plus-ambiguity bridge retains
the one-step full-support EFE identity. No new axioms are introduced.
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
    exact (boltzmannPosterior_pos_iff prior _ policy).mpr (prior_pos policy)
  log_optimizer := by
    intro policy
    have hlog := log_boltzmannPosterior prior (fun policy => γ * cost policy)
      policy (prior_pos policy)
    change Real.log (controlPosterior prior γ cost policy) =
      Real.log (prior policy) - γ * cost policy -
        Real.log (efeControlPartition prior γ cost) at hlog
    rw [hlog]
    ring

/-! ### Relative support and the sign of precision -/

/-- The control posterior is supported by its prior even when that prior is
sparse. Its exponential tilt cannot charge a forbidden policy. -/
theorem controlPosterior_relativeSupport (prior : FiniteLaw Action)
    (γ : ℝ) (cost : Action → ℝ) :
    ∀ policy, controlPosterior prior γ cost policy ≠ 0 → 0 < prior policy := by
  intro policy hmass
  apply (boltzmannPosterior_pos_iff prior _ policy).mp
  exact lt_of_le_of_ne ((controlPosterior prior γ cost).nonneg policy) hmass.symm

/-- Exact finite Gibbs gap for an arbitrary real precision and a candidate
supported by the prior. Unlike the divided objective, this scaled identity
also holds at zero precision. Shared zero atoms vanish before taking logs. -/
theorem efeControl_scaled_objective_eq_kl_sub_logPartition
    (prior : FiniteLaw Action) (γ : ℝ) (cost : Action → ℝ)
    (Q : FiniteLaw Action)
    (hsupport : ∀ policy, Q policy ≠ 0 → 0 < prior policy) :
    γ * expectation Q cost + finiteKL Q prior =
      finiteKL Q (controlPosterior prior γ cost) -
        Real.log (efeControlPartition prior γ cost) := by
  have hposterior : ∀ policy, Q policy ≠ 0 →
      0 < controlPosterior prior γ cost policy := by
    intro policy hmass
    exact (boltzmannPosterior_pos_iff prior _ policy).mpr (hsupport policy hmass)
  have hcross : crossEntropy Q (controlPosterior prior γ cost) =
      crossEntropy Q prior + γ * expectation Q cost +
        Real.log (efeControlPartition prior γ cost) := by
    have hterm : ∀ policy,
        -Q policy * Real.log (controlPosterior prior γ cost policy) =
          -Q policy * Real.log (prior policy) +
            γ * (Q policy * cost policy) +
              Q policy * Real.log (efeControlPartition prior γ cost) := by
      intro policy
      by_cases hmass : Q policy = 0
      · simp [hmass]
      · have hlog := log_boltzmannPosterior prior
          (fun policy => γ * cost policy) policy (hsupport policy hmass)
        change Real.log (controlPosterior prior γ cost policy) =
          Real.log (prior policy) - γ * cost policy -
            Real.log (efeControlPartition prior γ cost) at hlog
        rw [hlog]
        ring
    simp only [crossEntropy, expectation]
    simp_rw [hterm]
    rw [Finset.sum_add_distrib, Finset.sum_add_distrib, ← Finset.mul_sum,
      ← Finset.sum_mul, Q.sum_one, one_mul]
  rw [finiteKL_eq_crossEntropy_sub_entropy_of_relativeSupport Q prior hsupport,
    finiteKL_eq_crossEntropy_sub_entropy_of_relativeSupport Q _ hposterior, hcross]
  ring

/-- Relative support suffices for the divided objective at every nonzero
precision. Positivity is required for minimization, not for this identity. -/
theorem efeControlObjective_eq_kl_sub_logPartition_of_relativeSupport
    (prior : FiniteLaw Action) (γ : ℝ) (hγ : γ ≠ 0) (cost : Action → ℝ)
    (Q : FiniteLaw Action)
    (hsupport : ∀ policy, Q policy ≠ 0 → 0 < prior policy) :
    efeControlObjective prior γ cost Q =
      γ⁻¹ * (finiteKL Q (controlPosterior prior γ cost) -
        Real.log (efeControlPartition prior γ cost)) := by
  rw [← efeControl_scaled_objective_eq_kl_sub_logPartition prior γ cost Q hsupport]
  unfold efeControlObjective
  field_simp

/-- The exact optimizer value needs nonzero precision but no full prior
support. For negative precision it is a maximum rather than a minimum. -/
theorem efeControlObjective_optimizer_value (prior : FiniteLaw Action)
    (γ : ℝ) (hγ : γ ≠ 0) (cost : Action → ℝ) :
    efeControlObjective prior γ cost (controlPosterior prior γ cost) =
      -(γ⁻¹ * Real.log (efeControlPartition prior γ cost)) := by
  rw [efeControlObjective_eq_kl_sub_logPartition_of_relativeSupport prior γ hγ cost
    (controlPosterior prior γ cost) (controlPosterior_relativeSupport prior γ cost),
    finiteKL_self, zero_sub]
  ring

/-- For a supported candidate and nonzero precision, the signed objective gap
is exactly inverse precision times KL to the constructed posterior. -/
theorem efeControlObjective_sub_eq_kl_of_relativeSupport
    (prior : FiniteLaw Action) (γ : ℝ) (hγ : γ ≠ 0) (cost : Action → ℝ)
    (Q : FiniteLaw Action)
    (hsupport : ∀ policy, Q policy ≠ 0 → 0 < prior policy) :
    efeControlObjective prior γ cost Q -
        efeControlObjective prior γ cost (controlPosterior prior γ cost) =
      γ⁻¹ * finiteKL Q (controlPosterior prior γ cost) := by
  rw [efeControlObjective_eq_kl_sub_logPartition_of_relativeSupport prior γ hγ cost
    Q hsupport, efeControlObjective_optimizer_value prior γ hγ cost]
  ring

/-- At every nonzero precision, equality of the supported candidate's value
with the posterior's value characterizes that posterior exactly. -/
theorem efeControlObjective_eq_optimizer_iff_of_relativeSupport
    (prior : FiniteLaw Action) (γ : ℝ) (hγ : γ ≠ 0) (cost : Action → ℝ)
    (Q : FiniteLaw Action)
    (hsupport : ∀ policy, Q policy ≠ 0 → 0 < prior policy) :
    (efeControlObjective prior γ cost Q =
        efeControlObjective prior γ cost (controlPosterior prior γ cost)) ↔
      Q = controlPosterior prior γ cost := by
  rw [← sub_eq_zero,
    efeControlObjective_sub_eq_kl_of_relativeSupport prior γ hγ cost Q hsupport,
    mul_eq_zero, or_iff_right (inv_ne_zero hγ), finiteKL_eq_zero_iff]

/-- Positive precision gives a unique minimum on all laws supported by the
prior, including sparse priors. -/
theorem boltzmann_control_posterior_minimizes_efe_of_relativeSupport
    (prior : FiniteLaw Action) (γ : ℝ) (hγ : 0 < γ) (cost : Action → ℝ)
    (Q : FiniteLaw Action)
    (hsupport : ∀ policy, Q policy ≠ 0 → 0 < prior policy) :
    efeControlObjective prior γ cost (controlPosterior prior γ cost) ≤
        efeControlObjective prior γ cost Q ∧
      (efeControlObjective prior γ cost Q =
          efeControlObjective prior γ cost (controlPosterior prior γ cost) ↔
        Q = controlPosterior prior γ cost) := by
  refine ⟨?_, efeControlObjective_eq_optimizer_iff_of_relativeSupport
    prior γ hγ.ne' cost Q hsupport⟩
  have hgap := efeControlObjective_sub_eq_kl_of_relativeSupport
    prior γ hγ.ne' cost Q hsupport
  have hnonneg := mul_nonneg (inv_nonneg.mpr hγ.le)
    (finiteKL_nonneg Q (controlPosterior prior γ cost))
  linarith

/-- Every supported nonoptimizer has a strictly larger divided objective at
positive precision. -/
theorem efeControlObjective_optimizer_lt_of_relativeSupport
    (prior : FiniteLaw Action) (γ : ℝ) (hγ : 0 < γ) (cost : Action → ℝ)
    (Q : FiniteLaw Action)
    (hsupport : ∀ policy, Q policy ≠ 0 → 0 < prior policy)
    (hne : Q ≠ controlPosterior prior γ cost) :
    efeControlObjective prior γ cost (controlPosterior prior γ cost) <
      efeControlObjective prior γ cost Q := by
  have hmin := boltzmann_control_posterior_minimizes_efe_of_relativeSupport
    prior γ hγ cost Q hsupport
  exact lt_of_le_of_ne hmin.1 (fun heq => hne (hmin.2.mp heq.symm))

/-- Negative precision reverses the optimization direction: the constructed
posterior uniquely maximizes the divided objective on supported laws. -/
theorem boltzmann_control_posterior_maximizes_efe_of_negative_precision
    (prior : FiniteLaw Action) (γ : ℝ) (hγ : γ < 0) (cost : Action → ℝ)
    (Q : FiniteLaw Action)
    (hsupport : ∀ policy, Q policy ≠ 0 → 0 < prior policy) :
    efeControlObjective prior γ cost Q ≤
        efeControlObjective prior γ cost (controlPosterior prior γ cost) ∧
      (efeControlObjective prior γ cost Q =
          efeControlObjective prior γ cost (controlPosterior prior γ cost) ↔
        Q = controlPosterior prior γ cost) := by
  refine ⟨?_, efeControlObjective_eq_optimizer_iff_of_relativeSupport
    prior γ hγ.ne cost Q hsupport⟩
  have hgap := efeControlObjective_sub_eq_kl_of_relativeSupport
    prior γ hγ.ne cost Q hsupport
  have hnonpos := mul_nonpos_of_nonpos_of_nonneg (inv_lt_zero.mpr hγ).le
    (finiteKL_nonneg Q (controlPosterior prior γ cost))
  linarith

/-- A supported nonoptimizer has a strictly smaller divided objective at
negative precision, so a positive-precision minimizer reading would fail. -/
theorem efeControlObjective_lt_optimizer_of_negative_precision
    (prior : FiniteLaw Action) (γ : ℝ) (hγ : γ < 0) (cost : Action → ℝ)
    (Q : FiniteLaw Action)
    (hsupport : ∀ policy, Q policy ≠ 0 → 0 < prior policy)
    (hne : Q ≠ controlPosterior prior γ cost) :
    efeControlObjective prior γ cost Q <
      efeControlObjective prior γ cost (controlPosterior prior γ cost) := by
  have hmax := boltzmann_control_posterior_maximizes_efe_of_negative_precision
    prior γ hγ cost Q hsupport
  exact lt_of_le_of_ne hmax.1 (fun heq => hne (hmax.2.mp heq))

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
  exact efeControlObjective_eq_kl_sub_logPartition_of_relativeSupport
    prior γ hγ.ne' cost Q (fun policy _ => prior_pos policy)

/-- Objective gap: any candidate law exceeds the control posterior's value by
exactly `γ⁻¹ · KL(Q ‖ Q*)`. -/
theorem efeControlObjective_sub_eq_kl (prior : FiniteLaw Action)
    (prior_pos : ∀ policy, 0 < prior policy) (γ : ℝ) (hγ : 0 < γ)
    (cost : Action → ℝ) (Q : FiniteLaw Action) :
    efeControlObjective prior γ cost Q -
        efeControlObjective prior γ cost (controlPosterior prior γ cost) =
      γ⁻¹ * finiteKL Q (controlPosterior prior γ cost) := by
  exact efeControlObjective_sub_eq_kl_of_relativeSupport
    prior γ hγ.ne' cost Q (fun policy _ => prior_pos policy)

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
  exact boltzmann_control_posterior_minimizes_efe_of_relativeSupport
    prior γ hγ cost Q (fun policy _ => prior_pos policy)

/-- The minimized value is the negative expected log-partition
`-γ⁻¹ · log Z` of the EFE tilt. -/
theorem boltzmann_control_posterior_minimal_value (prior : FiniteLaw Action)
    (prior_pos : ∀ policy, 0 < prior policy) (γ : ℝ) (hγ : 0 < γ)
    (cost : Action → ℝ) :
    efeControlObjective prior γ cost (controlPosterior prior γ cost) =
      -(γ⁻¹ * Real.log (efeControlPartition prior γ cost)) := by
  rw [efeControlObjective_eq_kl_sub_logPartition_of_relativeSupport prior γ hγ.ne'
    cost (controlPosterior prior γ cost) (fun policy _ => prior_pos policy),
    finiteKL_self, zero_sub]
  ring

/-! ### Sparse and precision-boundary witnesses -/

/-- A nontrivial sparse prior: two equiprobable admissible policies and one
forbidden policy, on the existing normalized finite-law carrier. -/
noncomputable def sparseGibbsPrior : FiniteLaw (Fin 3) where
  mass := ![1 / 2, 1 / 2, 0]
  nonneg policy := by fin_cases policy <;> norm_num
  sum_one := by norm_num [Fin.sum_univ_succ]

/-- The negative potential `[0, log 3, 7]`. A large potential on the forbidden
third policy still cannot create posterior support. -/
noncomputable def sparseGibbsCost : Fin 3 → ℝ := ![0, -Real.log 3, -7]

/-- The sparse witness has an exact positive normalizer, without any
contribution from its forbidden third policy. -/
theorem sparseGibbs_partition :
    efeControlPartition sparseGibbsPrior 1 sparseGibbsCost = 2 := by
  norm_num [efeControlPartition, boltzmannPartition, boltzmannWeight,
    sparseGibbsPrior, sparseGibbsCost, Fin.sum_univ_succ,
    Real.exp_log (by norm_num : (0 : ℝ) < 3)]

/-- The constructed sparse optimizer has masses `[1/4, 3/4, 0]`. -/
theorem sparseGibbs_posterior_mass (policy : Fin 3) :
    controlPosterior sparseGibbsPrior 1 sparseGibbsCost policy =
      ![1 / 4, 3 / 4, 0] policy := by
  change sparseGibbsPrior policy * Real.exp (-(1 * sparseGibbsCost policy)) /
    efeControlPartition sparseGibbsPrior 1 sparseGibbsCost = _
  rw [sparseGibbs_partition]
  fin_cases policy <;>
    norm_num [sparseGibbsPrior, sparseGibbsCost,
      Real.exp_log (by norm_num : (0 : ℝ) < 3)]

/-- The sparse reference is a supported strict nonoptimizer, and the large
potential on its zero atom leaves that atom exactly zero. -/
theorem sparseGibbs_supported_strict_gap :
    efeControlObjective sparseGibbsPrior 1 sparseGibbsCost
        (controlPosterior sparseGibbsPrior 1 sparseGibbsCost) <
      efeControlObjective sparseGibbsPrior 1 sparseGibbsCost sparseGibbsPrior ∧
        controlPosterior sparseGibbsPrior 1 sparseGibbsCost 2 = 0 := by
  have hsupport : ∀ policy, sparseGibbsPrior policy ≠ 0 →
      0 < sparseGibbsPrior policy := by
    intro policy hmass
    exact lt_of_le_of_ne (sparseGibbsPrior.nonneg policy) hmass.symm
  have hne : sparseGibbsPrior ≠
      controlPosterior sparseGibbsPrior 1 sparseGibbsCost := by
    intro heq
    have hmass := congrArg (fun law : FiniteLaw (Fin 3) => law 0) heq
    rw [sparseGibbs_posterior_mass] at hmass
    norm_num [sparseGibbsPrior] at hmass
  refine ⟨efeControlObjective_optimizer_lt_of_relativeSupport
    sparseGibbsPrior 1 (by norm_num) sparseGibbsCost sparseGibbsPrior hsupport hne, ?_⟩
  simpa using sparseGibbs_posterior_mass 2

/-- The same sparse model exhibits a strict maximum at every negative
precision: a supported point mass has strictly smaller divided objective. -/
theorem sparseGibbs_negative_precision_strict_gap (γ : ℝ) (hγ : γ < 0) :
    efeControlObjective sparseGibbsPrior γ sparseGibbsCost
        (FiniteLaw.pointMass 0) <
      efeControlObjective sparseGibbsPrior γ sparseGibbsCost
        (controlPosterior sparseGibbsPrior γ sparseGibbsCost) := by
  have hsupport : ∀ policy, (FiniteLaw.pointMass (0 : Fin 3)) policy ≠ 0 →
      0 < sparseGibbsPrior policy := by
    intro policy hmass
    fin_cases policy <;> norm_num [FiniteLaw.pointMass, sparseGibbsPrior] at *
  have hne : FiniteLaw.pointMass (0 : Fin 3) ≠
      controlPosterior sparseGibbsPrior γ sparseGibbsCost := by
    intro heq
    have hpositive : 0 < controlPosterior sparseGibbsPrior γ sparseGibbsCost 1 :=
      (boltzmannPosterior_pos_iff sparseGibbsPrior _ 1).mpr (by
        norm_num [sparseGibbsPrior])
    rw [← heq] at hpositive
    norm_num [FiniteLaw.pointMass] at hpositive
  exact efeControlObjective_lt_optimizer_of_negative_precision
    sparseGibbsPrior γ hγ sparseGibbsCost _ hsupport hne

/-- Countermodel to dropping relative support: with positive precision, a
law charging a forbidden policy beats the constructed posterior under the
finite totalized KL convention. This is not extended-real KL minimization. -/
theorem zeroReference_unsupported_candidate_beats_posterior :
    let prior : FiniteLaw Bool := FiniteLaw.pointMass false
    let candidate : FiniteLaw Bool := FiniteLaw.pointMass true
    let cost : Bool → ℝ := fun policy => if policy then -2 else 0
    (prior true = 0 ∧ candidate true = 1) ∧
      efeControlObjective prior 1 cost candidate <
        efeControlObjective prior 1 cost (controlPosterior prior 1 cost) := by
  dsimp only
  have hposterior : controlPosterior (FiniteLaw.pointMass false) 1
      (fun policy : Bool => if policy then -2 else 0) = FiniteLaw.pointMass false := by
    apply FiniteLaw.ext_mass
    funext policy
    cases policy <;>
      norm_num [controlPosterior, boltzmannPosterior, boltzmannWeight,
        boltzmannPartition, FiniteLaw.pointMass, Fintype.sum_bool]
  rw [hposterior]
  simp only [efeControlObjective, finiteKL_self,
    finiteKL_disjoint_pointMass_totalized]
  norm_num [expectation, FiniteLaw.pointMass, Fintype.sum_bool]

/-- Zero precision leaves the prior unchanged but removes the divided KL
penalty. With nonconstant costs, that posterior need not minimize the
remaining expected cost, even though the prior has full support. -/
theorem zeroPrecision_prior_not_minimizer :
    let prior : FiniteLaw Bool := FiniteLaw.uniform
    let cost : Bool → ℝ := fun policy => if policy then 1 else 0
    (∀ policy, 0 < prior policy) ∧ controlPosterior prior 0 cost = prior ∧
      efeControlObjective prior 0 cost (FiniteLaw.pointMass false) <
        efeControlObjective prior 0 cost (controlPosterior prior 0 cost) := by
  dsimp only
  have hposterior : controlPosterior (FiniteLaw.uniform : FiniteLaw Bool) 0
      (fun policy : Bool => if policy then 1 else 0) = FiniteLaw.uniform := by
    simpa [controlPosterior] using
      boltzmannPosterior_zero_energy (FiniteLaw.uniform : FiniteLaw Bool)
  rw [hposterior]
  norm_num [efeControlObjective, expectation, FiniteLaw.pointMass,
    FiniteLaw.uniform, Fintype.sum_bool]

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
