module
public import FepSketches.compositions.risk_calibration
public import FepSketches.compositions.exponential_family
public import Mathlib.Tactic
@[expose] public section
namespace FEP103RiskExpControls
open FEP FEP.EmpiricalRisk FEP.VariationalDuality FEP.ExponentialFamily
open scoped BigOperators
noncomputable section

def sampling : FiniteLaw Bool where
  mass b := if b then 2 / 3 else 1 / 3
  nonneg b := by cases b <;> norm_num
  sum_one := by norm_num [Fintype.sum_bool]

def successes (b : Bool) : ℕ := if b then 2 else 0

theorem risk_nonuniform_exact :
    brierExcessRisk sampling (fun o => laplaceEstimate (successes o) 2) (1 / 3) =
      17 / 144 := by
  norm_num [brierExcessRisk, expectation, Fintype.sum_bool, sampling,
    successes, laplaceEstimate, bernoulliBrierScore]

theorem risk_imported_bound :
    brierExcessRisk sampling (fun o => laplaceEstimate (successes o) 2) (1 / 3) ≤
      2 * shrinkage 2 ^ 2 * expectation sampling
        (fun o => (empiricalRate (successes o) 2 - 1 / 3) ^ 2) +
        2 * (1 / ((2 : ℝ) + 2)) ^ 2 := by
  apply FEPComposed.fep125_brier_identity_transfers_fep124_risk_bound
  · norm_num
  · intro o; cases o <;> norm_num [successes]
  · norm_num

theorem raw_score_not_excess :
    expectation sampling (fun o => bernoulliBrierScore (1 / 3)
      (laplaceEstimate (successes o) 2)) ≠
      brierExcessRisk sampling (fun o => laplaceEstimate (successes o) 2) (1 / 3) := by
  norm_num [brierExcessRisk, expectation, Fintype.sum_bool, sampling,
    successes, laplaceEstimate, bernoulliBrierScore]

theorem invalid_sample_and_target :
    ¬0 < (0 : ℕ) ∧ ¬(3 : ℕ) ≤ 2 ∧ ¬(2 : ℝ) ∈ Set.Icc (0 : ℝ) 1 := by
  norm_num

theorem threeState_variance_positive_all (parameter : ℝ) :
    0 < ScalarExponentialFamily.threeStateFamily.variance parameter := by
  let family := ScalarExponentialFamily.threeStateFamily
  have nonzero : family.score parameter 0 ≠ 0 ∨ family.score parameter 1 ≠ 0 := by
    by_contra h
    push Not at h
    have h0 := h.1
    have h1 := h.2
    simp only [ScalarExponentialFamily.score] at h0 h1
    norm_num [family, ScalarExponentialFamily.threeStateFamily,
      ScalarExponentialFamily.threeStateStatistic] at h0 h1
    linarith
  unfold ScalarExponentialFamily.variance
  apply Finset.sum_pos'
  · intro o _
    exact mul_nonneg ((family.law parameter).nonneg o) (sq_nonneg _)
  · rcases nonzero with h | h
    · exact ⟨0, Finset.mem_univ _, mul_pos (family.law_pos parameter 0) (sq_pos_of_ne_zero h)⟩
    · exact ⟨1, Finset.mem_univ _, mul_pos (family.law_pos parameter 1) (sq_pos_of_ne_zero h)⟩

theorem threeState_interval_strict_injective :
    StrictMonoOn ScalarExponentialFamily.threeStateFamily.mean (Set.Icc (-1 : ℝ) 1) ∧
      Set.InjOn ScalarExponentialFamily.threeStateFamily.mean (Set.Icc (-1 : ℝ) 1) := by
  apply FEPComposed.fep146_positive_fisher_supplies_fep148_mean_injectivity
  intro parameter _
  rw [fep_fep146.FEP146.fep146_fisher_eq_variance]
  exact threeState_variance_positive_all parameter

theorem interval_is_nondegenerate : (-1 : ℝ) ∈ Set.Icc (-1 : ℝ) 1 ∧
    (1 : ℝ) ∈ Set.Icc (-1 : ℝ) 1 ∧ (-1 : ℝ) ≠ 1 := by norm_num

noncomputable def constantFamily : ScalarExponentialFamily Bool :=
  ScalarExponentialFamily.constantStatisticFamily (fun _ => 1) (fun _ => by norm_num) 7

theorem constant_fisher_refuses :
    ¬(∀ parameter ∈ Set.Icc (-1 : ℝ) 1, 0 < constantFamily.fisher parameter) := by
  intro h
  have hp := h 0 (by norm_num)
  rw [show constantFamily.fisher 0 = 0 from
    fep_fep146.FEP146.fep146_constantStatistic_zero_boundary
      (fun _ : Bool => 1) (fun _ => by norm_num) 7 0] at hp
  exact (lt_irrefl 0) hp

theorem constant_mean (parameter : ℝ) : constantFamily.mean parameter = 7 := by
  rw [ScalarExponentialFamily.mean_eq_expectation]
  change (∑ o : Bool, constantFamily.law parameter o * 7) = 7
  rw [← Finset.sum_mul, (constantFamily.law parameter).sum_one]
  norm_num

theorem constant_interval_not_injective :
    ¬Set.InjOn constantFamily.mean (Set.Icc (-1 : ℝ) 1) := by
  intro h
  have bad := h (by norm_num : (-1 : ℝ) ∈ Set.Icc (-1 : ℝ) 1)
    (by norm_num : (1 : ℝ) ∈ Set.Icc (-1 : ℝ) 1)
    (by rw [constant_mean, constant_mean])
  norm_num at bad
end
end FEP103RiskExpControls

#check FEPComposed.fep125_brier_identity_transfers_fep124_risk_bound
#print axioms FEPComposed.fep125_brier_identity_transfers_fep124_risk_bound
#check FEPComposed.fep146_positive_fisher_supplies_fep148_mean_injectivity
#print axioms FEPComposed.fep146_positive_fisher_supplies_fep148_mean_injectivity
#check FEP103RiskExpControls.risk_nonuniform_exact
#print axioms FEP103RiskExpControls.risk_nonuniform_exact
#check FEP103RiskExpControls.risk_imported_bound
#print axioms FEP103RiskExpControls.risk_imported_bound
#check FEP103RiskExpControls.raw_score_not_excess
#print axioms FEP103RiskExpControls.raw_score_not_excess
#check FEP103RiskExpControls.invalid_sample_and_target
#print axioms FEP103RiskExpControls.invalid_sample_and_target
#check FEP103RiskExpControls.threeState_variance_positive_all
#print axioms FEP103RiskExpControls.threeState_variance_positive_all
#check FEP103RiskExpControls.threeState_interval_strict_injective
#print axioms FEP103RiskExpControls.threeState_interval_strict_injective
#check FEP103RiskExpControls.interval_is_nondegenerate
#print axioms FEP103RiskExpControls.interval_is_nondegenerate
#check FEP103RiskExpControls.constant_fisher_refuses
#print axioms FEP103RiskExpControls.constant_fisher_refuses
#check FEP103RiskExpControls.constant_mean
#print axioms FEP103RiskExpControls.constant_mean
#check FEP103RiskExpControls.constant_interval_not_injective
#print axioms FEP103RiskExpControls.constant_interval_not_injective
