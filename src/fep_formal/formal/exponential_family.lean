module
public import FepSketches.finite_information

@[expose] public section

/-!
# Finite scalar exponential families

This module develops the smooth one-parameter geometry of a finite
exponential family.  The carrier is finite and nonempty, base weights are
strictly positive, and all logarithmic identities retain that support
hypothesis through the family structure.
-/

namespace FEP.ExponentialFamily

open FEP FEP.FiniteInformation Finset
open scoped BigOperators

variable {Outcome : Type*} [Fintype Outcome] [Nonempty Outcome]

/-- Positive base weights and one real-valued sufficient statistic. -/
structure ScalarExponentialFamily (Outcome : Type*) [Fintype Outcome] where
  base : Outcome → ℝ
  base_pos : ∀ outcome, 0 < base outcome
  statistic : Outcome → ℝ

namespace ScalarExponentialFamily

/-- Unnormalized exponential-family mass. -/
noncomputable def weight (family : ScalarExponentialFamily Outcome)
    (parameter : ℝ) (outcome : Outcome) : ℝ :=
  family.base outcome * Real.exp (parameter * family.statistic outcome)

/-- The `order`-th unnormalized statistic moment. -/
noncomputable def weightedMoment (family : ScalarExponentialFamily Outcome)
    (order : ℕ) (parameter : ℝ) : ℝ :=
  ∑ outcome,
    family.weight parameter outcome * family.statistic outcome ^ order

/-- Finite partition function. -/
noncomputable def partition (family : ScalarExponentialFamily Outcome)
    (parameter : ℝ) : ℝ :=
  family.weightedMoment 0 parameter

/-- Log-partition potential. -/
noncomputable def logPartition (family : ScalarExponentialFamily Outcome)
    (parameter : ℝ) : ℝ :=
  Real.log (family.partition parameter)

omit [Nonempty Outcome] in
theorem weight_pos (family : ScalarExponentialFamily Outcome)
    (parameter : ℝ) (outcome : Outcome) :
    0 < family.weight parameter outcome :=
  mul_pos (family.base_pos outcome) (Real.exp_pos _)

theorem partition_pos (family : ScalarExponentialFamily Outcome)
    (parameter : ℝ) : 0 < family.partition parameter := by
  classical
  exact Finset.sum_pos (fun outcome _ ↦ by
    simpa [partition, weightedMoment, weight] using
      family.weight_pos parameter outcome) Finset.univ_nonempty

/-- The normalized finite exponential-family law. -/
noncomputable def law (family : ScalarExponentialFamily Outcome)
    (parameter : ℝ) : FiniteLaw Outcome where
  mass outcome := family.weight parameter outcome / family.partition parameter
  nonneg outcome := div_nonneg (family.weight_pos parameter outcome).le
    (family.partition_pos parameter).le
  sum_one := by
    rw [← Finset.sum_div]
    simpa [partition, weightedMoment] using
      div_self (ne_of_gt (family.partition_pos parameter))

theorem law_pos (family : ScalarExponentialFamily Outcome)
    (parameter : ℝ) (outcome : Outcome) :
    0 < family.law parameter outcome :=
  div_pos (family.weight_pos parameter outcome)
    (family.partition_pos parameter)

/-- Mean (expectation) coordinate of the sufficient statistic. -/
noncomputable def mean (family : ScalarExponentialFamily Outcome)
    (parameter : ℝ) : ℝ :=
  family.weightedMoment 1 parameter / family.partition parameter

theorem mean_eq_expectation (family : ScalarExponentialFamily Outcome)
    (parameter : ℝ) :
    family.mean parameter =
      ∑ outcome, family.law parameter outcome * family.statistic outcome := by
  classical
  calc
    family.mean parameter =
        (∑ outcome,
          family.weight parameter outcome * family.statistic outcome) /
            family.partition parameter := by
      simp [mean, weightedMoment]
    _ = ∑ outcome,
          (family.weight parameter outcome * family.statistic outcome) /
            family.partition parameter := by
      rw [Finset.sum_div]
    _ = ∑ outcome,
          family.law parameter outcome * family.statistic outcome := by
      apply Finset.sum_congr rfl
      intro outcome _
      simp only [law]
      ring

/-- Centered score of the scalar natural parameter. -/
noncomputable def score (family : ScalarExponentialFamily Outcome)
    (parameter : ℝ) (outcome : Outcome) : ℝ :=
  family.statistic outcome - family.mean parameter

/-- Variance of the sufficient statistic under the normalized family. -/
noncomputable def variance (family : ScalarExponentialFamily Outcome)
    (parameter : ℝ) : ℝ :=
  ∑ outcome,
    family.law parameter outcome * family.score parameter outcome ^ 2

/-- Scalar Fisher information as expected squared score. -/
noncomputable def fisher (family : ScalarExponentialFamily Outcome)
    (parameter : ℝ) : ℝ :=
  family.variance parameter

omit [Nonempty Outcome] in
theorem score_eq_statistic_sub_mean
    (family : ScalarExponentialFamily Outcome)
    (parameter : ℝ) (outcome : Outcome) :
    family.score parameter outcome =
      family.statistic outcome - family.mean parameter :=
  rfl

theorem mean_score_zero (family : ScalarExponentialFamily Outcome)
    (parameter : ℝ) :
    ∑ outcome,
      family.law parameter outcome * family.score parameter outcome = 0 := by
  classical
  calc
    (∑ outcome,
        family.law parameter outcome * family.score parameter outcome) =
        (∑ outcome,
          family.law parameter outcome * family.statistic outcome) -
          family.mean parameter *
            ∑ outcome, family.law parameter outcome := by
      rw [Finset.mul_sum, ← Finset.sum_sub_distrib]
      apply Finset.sum_congr rfl
      intro outcome _
      rw [score]
      ring
    _ = family.mean parameter - family.mean parameter * 1 := by
      rw [← family.mean_eq_expectation parameter,
        (family.law parameter).sum_one]
    _ = 0 := by ring

theorem fisher_eq_variance (family : ScalarExponentialFamily Outcome)
    (parameter : ℝ) :
    family.fisher parameter = family.variance parameter :=
  rfl

theorem variance_eq_rawMoment (family : ScalarExponentialFamily Outcome)
    (parameter : ℝ) :
    family.variance parameter =
      family.weightedMoment 2 parameter / family.partition parameter -
        family.mean parameter ^ 2 := by
  classical
  have hSecond :
      (∑ outcome,
          family.law parameter outcome * family.statistic outcome ^ 2) =
        family.weightedMoment 2 parameter / family.partition parameter := by
    calc
      (∑ outcome,
          family.law parameter outcome * family.statistic outcome ^ 2) =
          ∑ outcome,
            (family.weight parameter outcome *
              family.statistic outcome ^ 2) / family.partition parameter := by
        apply Finset.sum_congr rfl
        intro outcome _
        simp only [law]
        ring
      _ = family.weightedMoment 2 parameter / family.partition parameter := by
        rw [weightedMoment, Finset.sum_div]
  calc
    family.variance parameter = ∑ outcome,
        (family.law parameter outcome * family.statistic outcome ^ 2 -
          2 * family.mean parameter *
            (family.law parameter outcome * family.statistic outcome) +
          family.mean parameter ^ 2 * family.law parameter outcome) := by
      rw [variance]
      apply Finset.sum_congr rfl
      intro outcome _
      rw [score]
      ring
    _ =
        (∑ outcome,
          family.law parameter outcome * family.statistic outcome ^ 2) -
          2 * family.mean parameter *
            (∑ outcome,
              family.law parameter outcome * family.statistic outcome) +
          family.mean parameter ^ 2 *
            ∑ outcome, family.law parameter outcome := by
      rw [Finset.mul_sum, Finset.mul_sum,
        Finset.sum_add_distrib, Finset.sum_sub_distrib]
    _ = family.weightedMoment 2 parameter / family.partition parameter -
        2 * family.mean parameter * family.mean parameter +
          family.mean parameter ^ 2 * 1 := by
      rw [hSecond, ← family.mean_eq_expectation parameter,
        (family.law parameter).sum_one]
    _ = family.weightedMoment 2 parameter / family.partition parameter -
        family.mean parameter ^ 2 := by ring

omit [Nonempty Outcome] in
/-- Differentiating a finite weighted moment raises its statistic order. -/
theorem weightedMoment_hasDerivAt
    (family : ScalarExponentialFamily Outcome)
    (order : ℕ) (parameter : ℝ) :
    HasDerivAt (family.weightedMoment order)
      (family.weightedMoment (order + 1) parameter) parameter := by
  classical
  unfold weightedMoment weight
  apply HasDerivAt.fun_sum
  intro outcome _
  simpa only [Function.id_def, one_mul, pow_succ, mul_assoc, mul_comm,
    mul_left_comm] using
      (((hasDerivAt_id parameter).mul_const
        (family.statistic outcome)).exp.const_mul
          (family.base outcome)).mul_const
        (family.statistic outcome ^ order)

omit [Nonempty Outcome] in
theorem partition_hasDerivAt (family : ScalarExponentialFamily Outcome)
    (parameter : ℝ) :
    HasDerivAt family.partition (family.weightedMoment 1 parameter)
      parameter := by
  change HasDerivAt (family.weightedMoment 0)
    (family.weightedMoment 1 parameter) parameter
  simpa using family.weightedMoment_hasDerivAt 0 parameter

/-- The log-partition derivative is the mean sufficient statistic. -/
theorem logPartition_hasDerivAt
    (family : ScalarExponentialFamily Outcome) (parameter : ℝ) :
    HasDerivAt family.logPartition (family.mean parameter) parameter := by
  change HasDerivAt (fun candidate ↦ Real.log (family.partition candidate))
    (family.weightedMoment 1 parameter / family.partition parameter) parameter
  simpa only using
    (family.partition_hasDerivAt parameter).log
      (ne_of_gt (family.partition_pos parameter))

/-- The mean-coordinate derivative is the statistic variance. -/
theorem mean_hasDerivAt (family : ScalarExponentialFamily Outcome)
    (parameter : ℝ) :
    HasDerivAt family.mean (family.variance parameter) parameter := by
  have hMoment :
      HasDerivAt (family.weightedMoment 1)
        (family.weightedMoment 2 parameter) parameter := by
    simpa using family.weightedMoment_hasDerivAt 1 parameter
  have hPartition := family.partition_hasDerivAt parameter
  have hQuotient := hMoment.div hPartition
    (ne_of_gt (family.partition_pos parameter))
  change HasDerivAt (family.weightedMoment 1 / family.partition)
    (family.variance parameter) parameter
  apply hQuotient.congr_deriv
  rw [family.variance_eq_rawMoment parameter, mean]
  field_simp [ne_of_gt (family.partition_pos parameter)]

/-- Pointwise law derivative equals mass times centered score. -/
theorem law_hasDerivAt (family : ScalarExponentialFamily Outcome)
    (parameter : ℝ) (outcome : Outcome) :
    HasDerivAt (fun candidate ↦ family.law candidate outcome)
      (family.law parameter outcome * family.score parameter outcome)
      parameter := by
  have hWeight :
      HasDerivAt (fun candidate ↦ family.weight candidate outcome)
        (family.weight parameter outcome * family.statistic outcome)
        parameter := by
    simpa only [weight, Function.id_def, one_mul, mul_assoc] using
      ((hasDerivAt_id parameter).mul_const
        (family.statistic outcome)).exp.const_mul (family.base outcome)
  have hQuotient := hWeight.div (family.partition_hasDerivAt parameter)
    (ne_of_gt (family.partition_pos parameter))
  change HasDerivAt
    ((fun candidate ↦ family.weight candidate outcome) / family.partition)
    ((family.weight parameter outcome / family.partition parameter) *
      (family.statistic outcome -
        family.weightedMoment 1 parameter / family.partition parameter))
    parameter
  apply hQuotient.congr_deriv
  field_simp [ne_of_gt (family.partition_pos parameter)]

/-- Supported log density has the canonical affine form. -/
theorem log_law_eq (family : ScalarExponentialFamily Outcome)
    (parameter : ℝ) (outcome : Outcome) :
    Real.log (family.law parameter outcome) =
      Real.log (family.base outcome) +
        parameter * family.statistic outcome -
          family.logPartition parameter := by
  rw [law, FiniteLaw.coe_mass,
    Real.log_div (ne_of_gt (family.weight_pos parameter outcome))
      (ne_of_gt (family.partition_pos parameter)),
    weight,
    Real.log_mul (ne_of_gt (family.base_pos outcome))
      (Real.exp_ne_zero _), Real.log_exp]
  rfl

/-- The log-density ratio is affine in the sufficient statistic. -/
theorem logDensityRatio_eq (family : ScalarExponentialFamily Outcome)
    (left right : ℝ) (outcome : Outcome) :
    Real.log
        (family.law left outcome / family.law right outcome) =
      (left - right) * family.statistic outcome -
        (family.logPartition left - family.logPartition right) := by
  rw [Real.log_div (ne_of_gt (family.law_pos left outcome))
    (ne_of_gt (family.law_pos right outcome)),
    family.log_law_eq left outcome, family.log_law_eq right outcome]
  ring

/-- Supported finite KL written as an expected log-density ratio. -/
noncomputable def logRatioKL (family : ScalarExponentialFamily Outcome)
    (left right : ℝ) : ℝ :=
  ∑ outcome, family.law left outcome *
    Real.log (family.law left outcome / family.law right outcome)

/-- Bregman divergence of `logPartition`, oriented as `KL(p_left || p_right)`. -/
noncomputable def logPartitionBregman
    (family : ScalarExponentialFamily Outcome) (left right : ℝ) : ℝ :=
  family.logPartition right - family.logPartition left -
    family.mean left * (right - left)

theorem logRatioKL_eq_logPartitionBregman
    (family : ScalarExponentialFamily Outcome) (left right : ℝ) :
    family.logRatioKL left right =
      family.logPartitionBregman left right := by
  classical
  rw [logRatioKL]
  simp_rw [family.logDensityRatio_eq left right]
  calc
    (∑ outcome,
        family.law left outcome *
          ((left - right) * family.statistic outcome -
            (family.logPartition left - family.logPartition right))) =
        (left - right) *
            (∑ outcome,
              family.law left outcome * family.statistic outcome) -
          (family.logPartition left - family.logPartition right) *
            ∑ outcome, family.law left outcome := by
      rw [Finset.mul_sum, Finset.mul_sum, ← Finset.sum_sub_distrib]
      apply Finset.sum_congr rfl
      intro outcome _
      ring
    _ = (left - right) * family.mean left -
        (family.logPartition left - family.logPartition right) * 1 := by
      rw [← family.mean_eq_expectation left, (family.law left).sum_one]
    _ = family.logPartitionBregman left right := by
      unfold logPartitionBregman
      ring

theorem finiteKL_eq_logRatioKL
    (family : ScalarExponentialFamily Outcome) (left right : ℝ) :
    finiteKL (family.law left) (family.law right) =
      family.logRatioKL left right := by
  rw [finiteKL_eq_crossEntropy_sub_entropy _ _ (family.law_pos right)]
  simp only [crossEntropy, entropy, logRatioKL]
  simp_rw [Real.negMulLog_eq_neg,
    Real.log_div (ne_of_gt (family.law_pos left _))
      (ne_of_gt (family.law_pos right _))]
  rw [← Finset.sum_sub_distrib]
  apply Finset.sum_congr rfl
  intro outcome _
  ring

/-- Full-support finite KL equals the log-partition Bregman divergence. -/
theorem finiteKL_eq_logPartitionBregman
    (family : ScalarExponentialFamily Outcome) (left right : ℝ) :
    finiteKL (family.law left) (family.law right) =
      family.logPartitionBregman left right := by
  rw [family.finiteKL_eq_logRatioKL left right,
    family.logRatioKL_eq_logPartitionBregman left right]

/-- Positive variance on an interval makes the mean coordinate strictly
monotone on that interval. -/
theorem meanParameter_strictMono (family : ScalarExponentialFamily Outcome)
    {lower upper : ℝ}
    (hVariance : ∀ parameter ∈ Set.Icc lower upper,
      0 < family.variance parameter) :
    StrictMonoOn family.mean (Set.Icc lower upper) := by
  refine strictMonoOn_of_hasDerivWithinAt_pos (f' := family.variance)
    (convex_Icc lower upper) ?_ ?_ ?_
  · intro parameter _
    exact (family.mean_hasDerivAt parameter).continuousAt.continuousWithinAt
  · intro parameter _
    exact (family.mean_hasDerivAt parameter).hasDerivWithinAt
  · intro parameter hParameter
    exact hVariance parameter (interior_subset hParameter)

theorem meanParameter_injectiveOn (family : ScalarExponentialFamily Outcome)
    {lower upper : ℝ}
    (hVariance : ∀ parameter ∈ Set.Icc lower upper,
      0 < family.variance parameter) :
    Set.InjOn family.mean (Set.Icc lower upper) :=
  (family.meanParameter_strictMono hVariance).injOn

/-! ## Concrete three-state nondegeneracy and constant boundary -/

def threeStateStatistic : Fin 3 → ℝ := ![0, 1, 2]

noncomputable def threeStateFamily : ScalarExponentialFamily (Fin 3) where
  base _ := 1
  base_pos _ := by norm_num
  statistic := threeStateStatistic

theorem threeState_variance_zero : threeStateFamily.variance 0 = 2 / 3 := by
  norm_num [variance, score, mean, weightedMoment, partition, law, weight,
    threeStateFamily, threeStateStatistic, Fin.sum_univ_succ]

theorem threeState_variance_zero_pos : 0 < threeStateFamily.variance 0 := by
  rw [threeState_variance_zero]
  norm_num

noncomputable def constantStatisticFamily
    (base : Outcome → ℝ) (hBase : ∀ outcome, 0 < base outcome)
    (constant : ℝ) : ScalarExponentialFamily Outcome where
  base := base
  base_pos := hBase
  statistic _ := constant

theorem constantStatistic_variance_zero
    (base : Outcome → ℝ) (hBase : ∀ outcome, 0 < base outcome)
    (constant parameter : ℝ) :
    (constantStatisticFamily base hBase constant).variance parameter = 0 := by
  have hMean :
      (constantStatisticFamily base hBase constant).mean parameter = constant := by
    rw [mean_eq_expectation]
    calc
      (∑ outcome,
          (constantStatisticFamily base hBase constant).law parameter outcome *
            constant) =
          constant * ∑ outcome,
            (constantStatisticFamily base hBase constant).law parameter outcome := by
        rw [Finset.mul_sum]
        apply Finset.sum_congr rfl
        intro outcome _
        ring
      _ = constant := by
        rw [((constantStatisticFamily base hBase constant).law parameter).sum_one,
          mul_one]
  rw [variance]
  apply Finset.sum_eq_zero
  intro outcome _
  rw [score, hMean]
  simp [constantStatisticFamily]

end ScalarExponentialFamily

end FEP.ExponentialFamily
