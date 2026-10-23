module
public import FepSketches.learning_theory
public import Mathlib.Probability.Distributions.Beta
public import Mathlib.Tactic
public import Mathlib.MeasureTheory.Measure.WithDensity
public import Mathlib.MeasureTheory.Integral.Lebesgue.Map
public import Mathlib.MeasureTheory.Constructions.Pi
public import Mathlib.MeasureTheory.Measure.Dirac.Basic
public import Mathlib.Algebra.BigOperators.Ring.Finset
public import Mathlib.Algebra.BigOperators.Group.Finset.Basic
public import Mathlib.Basic.ENNReal.Real

@[expose] public section

/-!
# Finite empirical risk and Laplace calibration

This module keeps sample counts finite and evaluates pointwise losses under the
shared normalized `FiniteLaw` carrier.  Laplace smoothing is treated as an
explicit affine transformation of the empirical rate; concentration transfer
therefore follows from deterministic event containment rather than an
unrestricted posterior-contraction claim.
-/

namespace FEP.EmpiricalRisk

open FEP Finset
open FEP.VariationalDuality
open scoped BigOperators

variable {Ω : Type*} [Fintype Ω]

/-! ## Empirical and Laplace rates -/

/-- Empirical success rate for a positive finite sample count. -/
noncomputable def empiricalRate (successes sampleCount : ℕ) : ℝ :=
  (successes : ℝ) / sampleCount

/-- Add-one (Laplace) estimate of a Bernoulli success probability. -/
noncomputable def laplaceEstimate (successes sampleCount : ℕ) : ℝ :=
  ((successes : ℝ) + 1) / ((sampleCount : ℝ) + 2)

/-- Multiplicative shrinkage applied to empirical error by Laplace smoothing. -/
noncomputable def shrinkage (sampleCount : ℕ) : ℝ :=
  (sampleCount : ℝ) / ((sampleCount : ℝ) + 2)

/-- Target-dependent affine offset in the Laplace error identity. -/
noncomputable def laplaceBias (sampleCount : ℕ) (target : ℝ) : ℝ :=
  (1 - 2 * target) / ((sampleCount : ℝ) + 2)

theorem shrinkage_nonneg (sampleCount : ℕ) :
    0 ≤ shrinkage sampleCount := by
  unfold shrinkage
  positivity

theorem shrinkage_le_one (sampleCount : ℕ) :
    shrinkage sampleCount ≤ 1 := by
  unfold shrinkage
  apply (div_le_one (by positivity : (0 : ℝ) < (sampleCount : ℝ) + 2)).2
  norm_num

/-- Laplace error is a contracted empirical error plus an explicit bias. -/
theorem laplaceError_identity (successes sampleCount : ℕ) (target : ℝ)
    (sampleCountPositive : 0 < sampleCount) :
    laplaceEstimate successes sampleCount - target =
      shrinkage sampleCount * (empiricalRate successes sampleCount - target) +
        laplaceBias sampleCount target := by
  have sampleCountNonzero : (sampleCount : ℝ) ≠ 0 := by
    exact_mod_cast Nat.ne_of_gt sampleCountPositive
  have denominatorNonzero : (sampleCount : ℝ) + 2 ≠ 0 := by
    positivity
  unfold laplaceEstimate shrinkage empiricalRate laplaceBias
  field_simp [sampleCountNonzero, denominatorNonzero]
  ring

/-- The affine Laplace offset is uniformly at most one pseudo-count over the
smoothed denominator for targets in the unit interval. -/
theorem laplaceBias_abs_le (sampleCount : ℕ) (target : ℝ)
    (targetBounds : target ∈ Set.Icc (0 : ℝ) 1) :
    |laplaceBias sampleCount target| ≤
      1 / ((sampleCount : ℝ) + 2) := by
  have denominatorPositive : (0 : ℝ) < (sampleCount : ℝ) + 2 := by
    positivity
  rw [laplaceBias, abs_div, abs_of_pos denominatorPositive]
  apply (div_le_div_iff_of_pos_right denominatorPositive).2
  exact abs_le.2 ⟨by linarith [targetBounds.2], by linarith [targetBounds.1]⟩

/-- Absolute empirical error transfers through Laplace smoothing with the
exact shrinkage coefficient and one-pseudo-count offset. -/
theorem laplaceAbsoluteError_le (successes sampleCount : ℕ) (target error : ℝ)
    (sampleCountPositive : 0 < sampleCount)
    (targetBounds : target ∈ Set.Icc (0 : ℝ) 1)
    (empiricalErrorBound :
      |empiricalRate successes sampleCount - target| ≤ error) :
    |laplaceEstimate successes sampleCount - target| ≤
      shrinkage sampleCount * error + 1 / ((sampleCount : ℝ) + 2) := by
  rw [laplaceError_identity successes sampleCount target sampleCountPositive]
  calc
    |shrinkage sampleCount *
          (empiricalRate successes sampleCount - target) +
        laplaceBias sampleCount target| ≤
        |shrinkage sampleCount *
          (empiricalRate successes sampleCount - target)| +
          |laplaceBias sampleCount target| := abs_add_le _ _
    _ = shrinkage sampleCount *
          |empiricalRate successes sampleCount - target| +
          |laplaceBias sampleCount target| := by
      rw [abs_mul, abs_of_nonneg (shrinkage_nonneg sampleCount)]
    _ ≤ shrinkage sampleCount * error +
          1 / ((sampleCount : ℝ) + 2) :=
      add_le_add
        (mul_le_mul_of_nonneg_left empiricalErrorBound
          (shrinkage_nonneg sampleCount))
        (laplaceBias_abs_le sampleCount target targetBounds)

/-- Squared Laplace error is bounded pointwise by twice the contracted
empirical squared error plus twice the squared pseudo-count offset. -/
theorem laplaceSquaredError_le (successes sampleCount : ℕ) (target : ℝ)
    (sampleCountPositive : 0 < sampleCount)
    (targetBounds : target ∈ Set.Icc (0 : ℝ) 1) :
    (laplaceEstimate successes sampleCount - target) ^ 2 ≤
      2 * shrinkage sampleCount ^ 2 *
          (empiricalRate successes sampleCount - target) ^ 2 +
        2 * (1 / ((sampleCount : ℝ) + 2)) ^ 2 := by
  have biasSquareBound :
      laplaceBias sampleCount target ^ 2 ≤
        (1 / ((sampleCount : ℝ) + 2)) ^ 2 := by
    rw [sq_le_sq, abs_of_pos (by positivity : (0 : ℝ) <
      1 / ((sampleCount : ℝ) + 2))]
    exact laplaceBias_abs_le sampleCount target targetBounds
  have sumSquareBound :
      (shrinkage sampleCount *
          (empiricalRate successes sampleCount - target) +
        laplaceBias sampleCount target) ^ 2 ≤
        2 * (shrinkage sampleCount *
          (empiricalRate successes sampleCount - target)) ^ 2 +
        2 * laplaceBias sampleCount target ^ 2 := by
    nlinarith [sq_nonneg
      (shrinkage sampleCount *
        (empiricalRate successes sampleCount - target) -
          laplaceBias sampleCount target)]
  rw [laplaceError_identity successes sampleCount target sampleCountPositive]
  calc
    (shrinkage sampleCount *
          (empiricalRate successes sampleCount - target) +
        laplaceBias sampleCount target) ^ 2 ≤
        2 * (shrinkage sampleCount *
          (empiricalRate successes sampleCount - target)) ^ 2 +
        2 * laplaceBias sampleCount target ^ 2 := sumSquareBound
    _ ≤ 2 * (shrinkage sampleCount *
          (empiricalRate successes sampleCount - target)) ^ 2 +
        2 * (1 / ((sampleCount : ℝ) + 2)) ^ 2 := by
      nlinarith
    _ = 2 * shrinkage sampleCount ^ 2 *
          (empiricalRate successes sampleCount - target) ^ 2 +
        2 * (1 / ((sampleCount : ℝ) + 2)) ^ 2 := by ring

/-! ## Finite-law risks -/

theorem expectation_mono (sampling : FiniteLaw Ω) (left right : Ω → ℝ)
    (pointwise : ∀ outcome, left outcome ≤ right outcome) :
    VariationalDuality.expectation sampling left ≤
      VariationalDuality.expectation sampling right := by
  unfold VariationalDuality.expectation
  exact Finset.sum_le_sum fun outcome _ =>
    mul_le_mul_of_nonneg_left (pointwise outcome) (sampling.nonneg outcome)

theorem expectation_add (sampling : FiniteLaw Ω) (left right : Ω → ℝ) :
    VariationalDuality.expectation sampling (fun outcome =>
      left outcome + right outcome) =
      VariationalDuality.expectation sampling left +
        VariationalDuality.expectation sampling right := by
  simp [VariationalDuality.expectation, mul_add, Finset.sum_add_distrib]

theorem expectation_const_mul (sampling : FiniteLaw Ω) (constant : ℝ)
    (value : Ω → ℝ) :
    VariationalDuality.expectation sampling (fun outcome =>
      constant * value outcome) =
      constant * VariationalDuality.expectation sampling value := by
  unfold VariationalDuality.expectation
  rw [Finset.mul_sum]
  apply Finset.sum_congr rfl
  intro outcome _
  ring

theorem expectation_const (sampling : FiniteLaw Ω) (constant : ℝ) :
    VariationalDuality.expectation sampling (fun _ => constant) = constant := by
  unfold VariationalDuality.expectation
  rw [← Finset.sum_mul, sampling.sum_one, one_mul]

/-- The pointwise squared-error transfer integrates under any normalized
finite sampling law. -/
theorem laplaceSquaredRisk_le (sampling : FiniteLaw Ω)
    (successes : Ω → ℕ) (sampleCount : ℕ) (target : ℝ)
    (sampleCountPositive : 0 < sampleCount)
    (successesAtMost : ∀ outcome, successes outcome ≤ sampleCount)
    (targetBounds : target ∈ Set.Icc (0 : ℝ) 1) :
    VariationalDuality.expectation sampling (fun outcome =>
      (laplaceEstimate (successes outcome) sampleCount - target) ^ 2) ≤
      2 * shrinkage sampleCount ^ 2 *
          VariationalDuality.expectation sampling (fun outcome =>
            (empiricalRate (successes outcome) sampleCount - target) ^ 2) +
        2 * (1 / ((sampleCount : ℝ) + 2)) ^ 2 := by
  have pointwise : ∀ outcome,
      (laplaceEstimate (successes outcome) sampleCount - target) ^ 2 ≤
        2 * shrinkage sampleCount ^ 2 *
            (empiricalRate (successes outcome) sampleCount - target) ^ 2 +
          2 * (1 / ((sampleCount : ℝ) + 2)) ^ 2 := by
    intro outcome
    have _ := successesAtMost outcome
    exact laplaceSquaredError_le (successes outcome) sampleCount target
      sampleCountPositive targetBounds
  calc
    VariationalDuality.expectation sampling (fun outcome =>
        (laplaceEstimate (successes outcome) sampleCount - target) ^ 2) ≤
        VariationalDuality.expectation sampling (fun outcome =>
          2 * shrinkage sampleCount ^ 2 *
              (empiricalRate (successes outcome) sampleCount - target) ^ 2 +
            2 * (1 / ((sampleCount : ℝ) + 2)) ^ 2) :=
      expectation_mono sampling _ _ pointwise
    _ = VariationalDuality.expectation sampling (fun outcome =>
          2 * shrinkage sampleCount ^ 2 *
            (empiricalRate (successes outcome) sampleCount - target) ^ 2) +
        VariationalDuality.expectation sampling (fun _ =>
          2 * (1 / ((sampleCount : ℝ) + 2)) ^ 2) :=
      expectation_add sampling _ _
    _ = 2 * shrinkage sampleCount ^ 2 *
          VariationalDuality.expectation sampling (fun outcome =>
            (empiricalRate (successes outcome) sampleCount - target) ^ 2) +
        2 * (1 / ((sampleCount : ℝ) + 2)) ^ 2 := by
      rw [expectation_const_mul, expectation_const]

/-! ## Bernoulli Brier risk -/

/-- Expected squared error of the Bernoulli probability forecast. -/
noncomputable def bernoulliBrierScore (target forecast : ℝ) : ℝ :=
  target * (1 - forecast) ^ 2 + (1 - target) * forecast ^ 2

/-- Bernoulli Brier excess risk is exactly squared probability error. -/
theorem brierExcess_eq_sqError (target forecast : ℝ) :
    bernoulliBrierScore target forecast - bernoulliBrierScore target target =
      (forecast - target) ^ 2 := by
  unfold bernoulliBrierScore
  ring

/-- Finite-law Brier excess risk of an arbitrary forecast. -/
noncomputable def brierExcessRisk (sampling : FiniteLaw Ω)
    (forecast : Ω → ℝ) (target : ℝ) : ℝ :=
  VariationalDuality.expectation sampling (fun outcome =>
    bernoulliBrierScore target (forecast outcome) -
      bernoulliBrierScore target target)

/-- The Laplace Brier excess risk inherits the finite-law squared-error bound. -/
theorem laplaceBrierRisk_le (sampling : FiniteLaw Ω)
    (successes : Ω → ℕ) (sampleCount : ℕ) (target : ℝ)
    (sampleCountPositive : 0 < sampleCount)
    (successesAtMost : ∀ outcome, successes outcome ≤ sampleCount)
    (targetBounds : target ∈ Set.Icc (0 : ℝ) 1) :
    brierExcessRisk sampling
        (fun outcome => laplaceEstimate (successes outcome) sampleCount) target ≤
      2 * shrinkage sampleCount ^ 2 *
          VariationalDuality.expectation sampling (fun outcome =>
            (empiricalRate (successes outcome) sampleCount - target) ^ 2) +
        2 * (1 / ((sampleCount : ℝ) + 2)) ^ 2 := by
  unfold brierExcessRisk
  simp_rw [brierExcess_eq_sqError]
  exact laplaceSquaredRisk_le sampling successes sampleCount target
    sampleCountPositive successesAtMost targetBounds

/-! ## Concentration-event transfer -/

/-- Probability of an event under a normalized finite law. -/
noncomputable def finiteEventProbability (sampling : FiniteLaw Ω)
    (event : Set Ω) : ℝ := by
  classical
  exact ∑ outcome, if outcome ∈ event then sampling outcome else 0

theorem finiteEventProbability_mono (sampling : FiniteLaw Ω)
    {left right : Set Ω} (subset : left ⊆ right) :
    finiteEventProbability sampling left ≤
      finiteEventProbability sampling right := by
  classical
  unfold finiteEventProbability
  apply Finset.sum_le_sum
  intro outcome _
  by_cases leftMembership : outcome ∈ left
  · have rightMembership := subset leftMembership
    simp [leftMembership, rightMembership]
  · by_cases rightMembership : outcome ∈ right
    · simp [leftMembership, rightMembership, sampling.nonneg outcome]
    · simp [leftMembership, rightMembership]

/-- Raw empirical deviation event at tolerance `error`. -/
def empiricalBadEvent (successes : Ω → ℕ) (sampleCount : ℕ)
    (target error : ℝ) : Set Ω :=
  {outcome |
    error < |empiricalRate (successes outcome) sampleCount - target|}

/-- Smoothed deviation event above the transferred tolerance. -/
def laplaceBadEvent (successes : Ω → ℕ) (sampleCount : ℕ)
    (target error : ℝ) : Set Ω :=
  {outcome |
    shrinkage sampleCount * error + 1 / ((sampleCount : ℝ) + 2) <
      |laplaceEstimate (successes outcome) sampleCount - target|}

omit [Fintype Ω] in
/-- Every Laplace deviation beyond the transferred threshold implies a raw
empirical deviation beyond the original threshold. -/
theorem laplaceBadEvent_subset (successes : Ω → ℕ) (sampleCount : ℕ)
    (target error : ℝ) (sampleCountPositive : 0 < sampleCount)
    (successesAtMost : ∀ outcome, successes outcome ≤ sampleCount)
    (targetBounds : target ∈ Set.Icc (0 : ℝ) 1) :
    laplaceBadEvent successes sampleCount target error ⊆
      empiricalBadEvent successes sampleCount target error := by
  intro outcome smoothedBad
  have _ := successesAtMost outcome
  by_contra rawNotBad
  have rawBound :
      |empiricalRate (successes outcome) sampleCount - target| ≤ error :=
    le_of_not_gt rawNotBad
  have transferred := laplaceAbsoluteError_le
    (successes outcome) sampleCount target error sampleCountPositive
    targetBounds rawBound
  exact (not_le_of_gt smoothedBad) transferred

/-- Event containment transfers any finite-law raw concentration bound to the
Laplace-smoothed event. -/
theorem laplaceBadEvent_probability_le (sampling : FiniteLaw Ω)
    (successes : Ω → ℕ) (sampleCount : ℕ) (target error failure : ℝ)
    (sampleCountPositive : 0 < sampleCount)
    (successesAtMost : ∀ outcome, successes outcome ≤ sampleCount)
    (targetBounds : target ∈ Set.Icc (0 : ℝ) 1)
    (rawProbabilityBound :
      finiteEventProbability sampling
        (empiricalBadEvent successes sampleCount target error) ≤ failure) :
    finiteEventProbability sampling
        (laplaceBadEvent successes sampleCount target error) ≤ failure :=
  (finiteEventProbability_mono sampling
    (laplaceBadEvent_subset successes sampleCount target error
      sampleCountPositive successesAtMost targetBounds)).trans rawProbabilityBound

/-! ## Boundary witness -/

/-- Laplace smoothing has a genuine nonzero offset at a boundary target. -/
theorem laplaceBias_nonzero_witness :
    laplaceBias 2 0 = 1 / 4 ∧ laplaceBias 2 0 ≠ 0 := by
  norm_num [laplaceBias]

/-! ## Dirichlet--categorical conjugacy on a finite alphabet

Count-level conjugacy only: pseudo-counts `α : K → ℝ`, natural-number counts
`n : K → ℕ`, and the resulting Pólya predictive.  No Dirichlet density, digamma
function, or measure on the simplex appears; that is a separate, later stage. -/

section DirichletCategorical

variable {K : Type*} [Fintype K] [DecidableEq K]

/-- Rising factorial `a (a+1) ⋯ (a+m-1)` as an explicit finite product. -/
noncomputable def risingFactorial (a : ℝ) (m : ℕ) : ℝ :=
  ∏ i ∈ Finset.range m, (a + (i : ℝ))

theorem risingFactorial_zero (a : ℝ) : risingFactorial a 0 = 1 := by
  simp [risingFactorial]

theorem risingFactorial_succ_left (a : ℝ) (m : ℕ) :
    risingFactorial a (m + 1) = a * risingFactorial (a + 1) m := by
  unfold risingFactorial
  rw [Finset.prod_range_succ']
  simp only [Nat.cast_add, Nat.cast_one, Nat.cast_zero, add_zero]
  rw [mul_comm]
  congr 1
  apply Finset.prod_congr rfl
  intro i _
  ring

theorem risingFactorial_succ_right (a : ℝ) (m : ℕ) :
    risingFactorial a (m + 1) = risingFactorial a m * (a + m) := by
  unfold risingFactorial
  rw [Finset.prod_range_succ]

/-- Posterior pseudo-counts: prior pseudo-counts plus observed counts. -/
def dirichletPosterior (α : K → ℝ) (n : K → ℕ) : K → ℝ :=
  fun k => α k + (n k : ℝ)

/-- Total of the pseudo-counts plus the total number of observations. -/
noncomputable def dirichletTotal (α : K → ℝ) (n : K → ℕ) : ℝ :=
  ∑ k, α k + ∑ k, (n k : ℝ)

/-- Pólya predictive `P(next = k | counts) = (α_k + n_k) / (Σα + N)`. -/
noncomputable def polyaPredictive (α : K → ℝ) (n : K → ℕ) (k : K) : ℝ :=
  (α k + (n k : ℝ)) / (∑ j, α j + ∑ j, (n j : ℝ))

omit [DecidableEq K] in
theorem dirichletPosterior_total (α : K → ℝ) (n : K → ℕ) :
    ∑ k, dirichletPosterior α n k = dirichletTotal α n := by
  simp [dirichletPosterior, dirichletTotal, Finset.sum_add_distrib]

omit [DecidableEq K] in
/-- The Pólya predictive is the normalized posterior pseudo-count vector. -/
theorem polyaPredictive_eq_posterior_normalised (α : K → ℝ) (n : K → ℕ) (k : K) :
    polyaPredictive α n k =
      dirichletPosterior α n k / ∑ j, dirichletPosterior α n j := by
  rw [dirichletPosterior_total]
  rfl

omit [DecidableEq K] in
theorem polyaPredictive_nonneg (α : K → ℝ) (n : K → ℕ)
    (alphaNonneg : ∀ k, 0 ≤ α k) (k : K) :
    0 ≤ polyaPredictive α n k := by
  unfold polyaPredictive
  have : 0 ≤ ∑ j, α j + ∑ j, (n j : ℝ) :=
    add_nonneg (Finset.sum_nonneg fun j _ => alphaNonneg j)
      (Finset.sum_nonneg fun j _ => Nat.cast_nonneg _)
  exact div_nonneg (add_nonneg (alphaNonneg k) (Nat.cast_nonneg _)) this

omit [DecidableEq K] in
theorem polyaPredictive_sum_one (α : K → ℝ) (n : K → ℕ)
    (totalPositive : 0 < ∑ j, α j + ∑ j, (n j : ℝ)) :
    ∑ k, polyaPredictive α n k = 1 := by
  unfold polyaPredictive
  rw [← Finset.sum_div, Finset.sum_add_distrib]
  exact div_self totalPositive.ne'

omit [DecidableEq K] in
theorem polyaPredictive_pos (α : K → ℝ) (n : K → ℕ)
    (alphaPositive : ∀ k, 0 < α k) [Nonempty K] (k : K) :
    0 < polyaPredictive α n k := by
  unfold polyaPredictive
  have : 0 < ∑ j, α j + ∑ j, (n j : ℝ) :=
    add_pos_of_pos_of_nonneg (Finset.sum_pos (fun j _ => alphaPositive j)
      Finset.univ_nonempty) (Finset.sum_nonneg fun j _ => Nat.cast_nonneg _)
  exact div_pos (add_pos_of_pos_of_nonneg (alphaPositive k) (Nat.cast_nonneg _)) this

/-- Count-level probability of any sequence with counts `n`: a product of
rising factorials over a rising factorial of the total. -/
noncomputable def polyaCountProbability (α : K → ℝ) (n : K → ℕ) : ℝ :=
  (∏ k, risingFactorial (α k) (n k)) /
    risingFactorial (∑ k, α k) (∑ k, n k)

/-- Chain rule: observing one more `x` multiplies by the Pólya predictive. -/
theorem polyaCountProbability_succ (α : K → ℝ) (n : K → ℕ) (x : K) :
    polyaCountProbability α (n + (Pi.single x 1 : K → ℕ)) =
      polyaPredictive α n x * polyaCountProbability α n := by
  have totalCount : ∑ k, (n + (Pi.single x 1 : K → ℕ)) k = ∑ k, n k + 1 := by
    simp [Finset.sum_add_distrib]
  have numerator : ∏ k, risingFactorial (α k) ((n + (Pi.single x 1 : K → ℕ)) k) =
      (α x + (n x : ℝ)) * ∏ k, risingFactorial (α k) (n k) := by
    rw [← Finset.mul_prod_erase Finset.univ _ (Finset.mem_univ x),
      ← Finset.mul_prod_erase Finset.univ (fun k => risingFactorial (α k) (n k))
        (Finset.mem_univ x)]
    have rest : ∏ k ∈ Finset.univ.erase x,
        risingFactorial (α k) ((n + (Pi.single x 1 : K → ℕ)) k) =
        ∏ k ∈ Finset.univ.erase x, risingFactorial (α k) (n k) := by
      apply Finset.prod_congr rfl
      intro k hk
      have : k ≠ x := Finset.ne_of_mem_erase hk
      simp [Pi.single_eq_of_ne this]
    rw [rest]
    simp only [Pi.add_apply, Pi.single_eq_same]
    rw [risingFactorial_succ_right]
    ring
  unfold polyaCountProbability polyaPredictive
  rw [totalCount, numerator, risingFactorial_succ_right]
  have natCast : ((∑ k, n k : ℕ) : ℝ) = ∑ k, (n k : ℝ) := by simp
  rw [natCast]
  rw [div_mul_div_comm]
  congr 1
  ring

/-- Sequence probability under a Dirichlet prior, built one observation at a
time from the Pólya predictive (the pseudo-counts absorb each observation). -/
noncomputable def dirichletSequenceProbability :
    (K → ℝ) → List K → ℝ
  | _, [] => 1
  | α, x :: xs =>
      α x / (∑ k, α k) * dirichletSequenceProbability (α + (Pi.single x 1 : K → ℝ)) xs

/-- Closed form: a product of rising factorials of the symbol counts over the
rising factorial of the sequence length. -/
theorem dirichletSequenceProbability_eq_counts (xs : List K) :
    ∀ α : K → ℝ, dirichletSequenceProbability α xs =
      (∏ k, risingFactorial (α k) (xs.count k)) /
        risingFactorial (∑ k, α k) xs.length := by
  induction xs with
  | nil => intro α; simp [dirichletSequenceProbability, risingFactorial_zero]
  | cons x xs ih =>
    intro α
    rw [dirichletSequenceProbability, ih]
    have sumUpdate : ∑ k, (α + (Pi.single x 1 : K → ℝ)) k = ∑ k, α k + 1 := by
      simp [Finset.sum_add_distrib]
    have numerator :
        ∏ k, risingFactorial (α k) ((x :: xs).count k) =
          α x * ∏ k, risingFactorial ((α + (Pi.single x 1 : K → ℝ)) k) (xs.count k) := by
      rw [← Finset.mul_prod_erase Finset.univ _ (Finset.mem_univ x),
        ← Finset.mul_prod_erase Finset.univ
          (fun k => risingFactorial ((α + (Pi.single x 1 : K → ℝ)) k) (xs.count k))
          (Finset.mem_univ x)]
      have rest : ∏ k ∈ Finset.univ.erase x,
          risingFactorial (α k) ((x :: xs).count k) =
          ∏ k ∈ Finset.univ.erase x,
            risingFactorial ((α + (Pi.single x 1 : K → ℝ)) k) (xs.count k) := by
        apply Finset.prod_congr rfl
        intro k hk
        have hne : k ≠ x := Finset.ne_of_mem_erase hk
        have hne' : x ≠ k := fun h => hne h.symm
        simp [hne']
      rw [rest]
      simp only [List.count_cons_self, Pi.add_apply, Pi.single_eq_same]
      rw [risingFactorial_succ_left, mul_assoc]
    rw [sumUpdate, List.length_cons, risingFactorial_succ_left, numerator]
    rw [div_mul_div_comm]

theorem listCountSum (xs : List K) : ∑ k, xs.count k = xs.length := by
  induction xs with
  | nil => simp
  | cons x xs ih =>
    simp only [List.count_cons, List.length_cons, Finset.sum_add_distrib, ih]
    simp [beq_iff_eq]

/-- Sequence probability depends only on the symbol counts. -/
theorem dirichletSequenceProbability_eq_countProbability (α : K → ℝ)
    (xs : List K) :
    dirichletSequenceProbability α xs =
      polyaCountProbability α (fun k => xs.count k) := by
  rw [dirichletSequenceProbability_eq_counts]
  unfold polyaCountProbability
  rw [listCountSum]

/-- Exchangeability: any reordering of a sequence has the same probability. -/
theorem dirichletSequenceProbability_exchangeable (α : K → ℝ)
    {xs ys : List K} (permutation : xs.Perm ys) :
    dirichletSequenceProbability α xs = dirichletSequenceProbability α ys := by
  rw [dirichletSequenceProbability_eq_countProbability,
    dirichletSequenceProbability_eq_countProbability]
  congr 2
  funext k
  exact permutation.count_eq k

/-! ### Binary alphabet: bridge to the finite Bernoulli update and Laplace -/

/-- Binary pseudo-counts `(success, failure)`. -/
def binaryPseudoCounts (success failure : ℝ) : Bool → ℝ
  | true => success
  | false => failure

/-- With `K = Bool`, the Pólya predictive of `true` is the Beta--Bernoulli
posterior mean `(a + successes) / (a + b + trials)`. -/
theorem polyaPredictive_binary (success failure : ℝ) (n : Bool → ℕ) :
    polyaPredictive (binaryPseudoCounts success failure) n true =
      (success + (n true : ℝ)) /
        (success + failure + ((n true : ℝ) + (n false : ℝ))) := by
  simp [polyaPredictive, binaryPseudoCounts]

/-- `K = 2` reproduces the finite Bernoulli Bayes update (the `fep-045`
expression `p l₁ / (p l₁ + (1 - p) l₀)`): with prior `p` the zero-count
predictive of `true` and the two likelihoods the one-step predictives of `true`
after one `true` / one `false`, the Bayes-updated parameter equals the Pólya
predictive after observing a single `true`. -/
theorem dirichletBinary_bernoulliBayes_bridge (success failure : ℝ)
    (successPositive : 0 < success) (failurePositive : 0 < failure) :
    let α := binaryPseudoCounts success failure
    let p := polyaPredictive α (fun _ => 0) true
    let l₁ := polyaPredictive α (Pi.single true 1 : Bool → ℕ) true
    let l₀ := polyaPredictive α (Pi.single false 1 : Bool → ℕ) true
    p * l₁ / (p * l₁ + (1 - p) * l₀) =
      polyaPredictive α (Pi.single true 1 : Bool → ℕ) true := by
  intro α p l₁ l₀
  have hs := successPositive
  have hf := failurePositive
  simp only [p, l₁, l₀, α, polyaPredictive, binaryPseudoCounts,
    Fintype.sum_bool, Pi.single_apply, Bool.true_eq_false, Bool.false_eq_true,
    Nat.cast_zero]
  have hden : (1 + success + failure) ≠ 0 := by positivity
  have key : (1 + success + failure) * (1 + success + failure)⁻¹ = 1 :=
    mul_inv_cancel₀ hden
  simp
  field_simp
  linear_combination key

/-- `α = 1` on `K = 2` is add-one (Laplace) smoothing, exactly the
`laplaceEstimate` of the empirical-risk module. -/
theorem polyaPredictive_binary_laplace (n : Bool → ℕ) :
    polyaPredictive (binaryPseudoCounts 1 1) n true =
      laplaceEstimate (n true) (n true + n false) := by
  rw [polyaPredictive_binary]
  unfold laplaceEstimate
  push_cast
  ring_nf

omit [DecidableEq K] in
/-- `α = 1` on any alphabet is add-one smoothing with denominator `N + |K|`. -/
theorem polyaPredictive_ones (n : K → ℕ) (k : K) :
    polyaPredictive (fun _ => (1 : ℝ)) n k =
      ((n k : ℝ) + 1) / ((∑ j, (n j : ℝ)) + Fintype.card K) := by
  unfold polyaPredictive
  simp [add_comm]

/-! ### Row-wise learning of likelihood (A) and transition (B) kernels -/

/-- Row-wise Dirichlet learning: row `r` has its own pseudo-counts and counts. -/
noncomputable def learnedKernel {R : Type*} (α : R → K → ℝ) (n : R → K → ℕ)
    (r : R) (k : K) : ℝ :=
  polyaPredictive (α r) (n r) k

omit [DecidableEq K] in
theorem learnedKernel_nonneg {R : Type*} (α : R → K → ℝ) (n : R → K → ℕ)
    (alphaNonneg : ∀ r k, 0 ≤ α r k) (r : R) (k : K) :
    0 ≤ learnedKernel α n r k :=
  polyaPredictive_nonneg (α r) (n r) (alphaNonneg r) k

omit [DecidableEq K] in
theorem learnedKernel_row_sum_one {R : Type*} (α : R → K → ℝ) (n : R → K → ℕ)
    (rowPositive : ∀ r, 0 < ∑ k, α r k + ∑ k, (n r k : ℝ)) (r : R) :
    ∑ k, learnedKernel α n r k = 1 :=
  polyaPredictive_sum_one (α r) (n r) (rowPositive r)

/-- Learned likelihood `A(o | s)`: rows indexed by hidden state, counts over
observations. Rows are nonnegative and sum to one. -/
noncomputable def learnedLikelihood {S : Type*} (α : S → K → ℝ)
    (n : S → K → ℕ) (s : S) (o : K) : ℝ :=
  learnedKernel α n s o

/-- Learned transition `B(s' | s, u)`: rows indexed by (state, action). -/
noncomputable def learnedTransition {S U : Type*} (α : S × U → K → ℝ)
    (n : S × U → K → ℕ) (s : S) (u : U) (s' : K) : ℝ :=
  learnedKernel α n (s, u) s'

omit [DecidableEq K] in
theorem learnedLikelihood_normalised {S : Type*} (α : S → K → ℝ)
    (n : S → K → ℕ) (alphaPositive : ∀ s k, 0 < α s k) [Nonempty K] (s : S) :
    (∀ o, 0 ≤ learnedLikelihood α n s o) ∧
      ∑ o, learnedLikelihood α n s o = 1 := by
  refine ⟨fun o => learnedKernel_nonneg α n (fun r k => (alphaPositive r k).le) s o,
    learnedKernel_row_sum_one α n (fun r => ?_) s⟩
  exact add_pos_of_pos_of_nonneg
    (Finset.sum_pos (fun k _ => alphaPositive r k) Finset.univ_nonempty)
    (Finset.sum_nonneg fun k _ => Nat.cast_nonneg _)

omit [DecidableEq K] in
theorem learnedTransition_normalised {S U : Type*} (α : S × U → K → ℝ)
    (n : S × U → K → ℕ) (alphaPositive : ∀ r k, 0 < α r k) [Nonempty K]
    (s : S) (u : U) :
    (∀ s', 0 ≤ learnedTransition α n s u s') ∧
      ∑ s', learnedTransition α n s u s' = 1 := by
  refine ⟨fun s' => learnedKernel_nonneg α n (fun r k => (alphaPositive r k).le)
    (s, u) s', learnedKernel_row_sum_one α n (fun r => ?_) (s, u)⟩
  exact add_pos_of_pos_of_nonneg
    (Finset.sum_pos (fun k _ => alphaPositive r k) Finset.univ_nonempty)
    (Finset.sum_nonneg fun k _ => Nat.cast_nonneg _)

end DirichletCategorical

end FEP.EmpiricalRisk

namespace FEP.EmpiricalRisk

/- Source lineage 17fbc43aa3cec3edc6a1dac231a0b6ccf1ec0e6ef238fbdaf1c8e59e9250af32.
Current composed integration requires its own maintained qualification. -/
section
/- Positive real-shape Beta likelihood weighting and normalized posterior identities. -/

open MeasureTheory
open scoped ENNReal

namespace BetaDensity

noncomputable def likelihood (s f : ℕ) (x : ℝ) : ENNReal :=
  ENNReal.ofReal x ^ s * ENNReal.ofReal (1 - x) ^ f

noncomputable def normalizer (a b : ℝ) (s f : ℕ) : ℝ :=
  ProbabilityTheory.beta (a + (s : ℝ)) (b + (f : ℝ)) / ProbabilityTheory.beta a b

theorem normalizer_pos {a b : ℝ} (ha : 0 < a) (hb : 0 < b) (s f : ℕ) :
    0 < normalizer a b s f := by
  exact div_pos (ProbabilityTheory.beta_pos (by positivity) (by positivity))
    (ProbabilityTheory.beta_pos ha hb)

theorem normalizer_finite (a b : ℝ) (s f : ℕ) :
    ENNReal.ofReal (normalizer a b s f) ≠ ⊤ := ENNReal.ofReal_ne_top

theorem likelihood_measurable (s f : ℕ) : Measurable (likelihood s f) := by
  unfold likelihood
  fun_prop

theorem real_pdf_product {a b : ℝ} (ha : 0 < a) (hb : 0 < b)
    (s f : ℕ) (x : ℝ) :
    ProbabilityTheory.betaPDFReal a b x * (x ^ s * (1 - x) ^ f) =
      normalizer a b s f * ProbabilityTheory.betaPDFReal (a + (s : ℝ)) (b + (f : ℝ)) x := by
  by_cases hx : 0 < x ∧ x < 1
  · have hx1 : 0 < 1 - x := sub_pos.mpr hx.2
    have hbase : ProbabilityTheory.beta a b ≠ 0 := ne_of_gt (ProbabilityTheory.beta_pos ha hb)
    have hpost : ProbabilityTheory.beta (a + (s : ℝ)) (b + (f : ℝ)) ≠ 0 :=
      ne_of_gt (ProbabilityTheory.beta_pos (by positivity) (by positivity))
    simp only [ProbabilityTheory.betaPDFReal, ite_eq_left hx, normalizer]
    rw [show a + (s : ℝ) - 1 = (a - 1) + (s : ℝ) by ring,
      show b + (f : ℝ) - 1 = (b - 1) + (f : ℝ) by ring,
      Real.rpow_add_natCast (ne_of_gt hx.1), Real.rpow_add_natCast (ne_of_gt hx1)]
    field_simp
  · simp [ProbabilityTheory.betaPDFReal, hx]

theorem pdf_product {a b : ℝ} (ha : 0 < a) (hb : 0 < b)
    (s f : ℕ) (x : ℝ) :
    ProbabilityTheory.betaPDF a b x * likelihood s f x =
      ENNReal.ofReal (normalizer a b s f) *
        ProbabilityTheory.betaPDF (a + (s : ℝ)) (b + (f : ℝ)) x := by
  by_cases hx : 0 < x ∧ x < 1
  · have hp : 0 ≤ ProbabilityTheory.betaPDFReal a b x :=
      (ProbabilityTheory.betaPDFReal_pos hx.1 hx.2 ha hb).le
    have hx0 : 0 ≤ x := hx.1.le
    have hx1 : 0 ≤ 1 - x := (sub_pos.mpr hx.2).le
    calc
      ProbabilityTheory.betaPDF a b x * likelihood s f x =
          ENNReal.ofReal (ProbabilityTheory.betaPDFReal a b x * (x ^ s * (1 - x) ^ f)) := by
        rw [ENNReal.ofReal_mul hp, ENNReal.ofReal_mul (pow_nonneg hx0 s),
          ENNReal.ofReal_pow hx0, ENNReal.ofReal_pow hx1]
        rfl
      _ = ENNReal.ofReal (normalizer a b s f *
          ProbabilityTheory.betaPDFReal (a + (s : ℝ)) (b + (f : ℝ)) x) :=
        congrArg ENNReal.ofReal (real_pdf_product ha hb s f x)
      _ = _ := by
        rw [ENNReal.ofReal_mul (normalizer_pos ha hb s f).le]
        rfl
  · simp [ProbabilityTheory.betaPDF, ProbabilityTheory.betaPDFReal, hx]

theorem weighted_measure {a b : ℝ} (ha : 0 < a) (hb : 0 < b) (s f : ℕ) :
    (ProbabilityTheory.betaMeasure a b).withDensity (likelihood s f) =
      ENNReal.ofReal (normalizer a b s f) •
        ProbabilityTheory.betaMeasure (a + (s : ℝ)) (b + (f : ℝ)) := by
  have hprior : Measurable (ProbabilityTheory.betaPDF a b) := by
    unfold ProbabilityTheory.betaPDF
    fun_prop
  have hpost : Measurable (ProbabilityTheory.betaPDF (a + (s : ℝ)) (b + (f : ℝ))) := by
    unfold ProbabilityTheory.betaPDF
    fun_prop
  unfold ProbabilityTheory.betaMeasure
  rw [← MeasureTheory.withDensity_mul volume hprior (likelihood_measurable s f),
    ← MeasureTheory.withDensity_smul _ hpost]
  apply MeasureTheory.withDensity_congr_ae
  exact Filter.Eventually.of_forall fun x => pdf_product ha hb s f x

theorem weighted_mass {a b : ℝ} (ha : 0 < a) (hb : 0 < b) (s f : ℕ) :
    ((ProbabilityTheory.betaMeasure a b).withDensity (likelihood s f)) Set.univ =
      ENNReal.ofReal (normalizer a b s f) := by
  let := ProbabilityTheory.isProbabilityMeasureBeta
    (show 0 < a + (s : ℝ) by positivity) (show 0 < b + (f : ℝ) by positivity)
  rw [weighted_measure ha hb s f]
  simp

theorem normalized_posterior {a b : ℝ} (ha : 0 < a) (hb : 0 < b) (s f : ℕ) :
    (ENNReal.ofReal (normalizer a b s f))⁻¹ •
      (ProbabilityTheory.betaMeasure a b).withDensity (likelihood s f) =
        ProbabilityTheory.betaMeasure (a + (s : ℝ)) (b + (f : ℝ)) := by
  rw [weighted_measure ha hb s f, smul_smul,
    ENNReal.inv_mul_cancel (ne_of_gt (ENNReal.ofReal_pos.mpr (normalizer_pos ha hb s f)))
      (normalizer_finite a b s f), one_smul]

theorem normalized_probability {a b : ℝ} (ha : 0 < a) (hb : 0 < b) (s f : ℕ) :
    IsProbabilityMeasure ((ENNReal.ofReal (normalizer a b s f))⁻¹ •
      (ProbabilityTheory.betaMeasure a b).withDensity (likelihood s f)) := by
  rw [normalized_posterior ha hb s f]
  exact ProbabilityTheory.isProbabilityMeasureBeta (by positivity) (by positivity)

theorem zero_counts {a b : ℝ} (ha : 0 < a) (hb : 0 < b) :
    normalizer a b 0 0 = 1 := by
  simp [normalizer, ne_of_gt (ProbabilityTheory.beta_pos ha hb)]

theorem noninteger_prior_recovery : normalizer (1 / 2) (3 / 2) 0 0 = 1 :=
  zero_counts (by norm_num) (by norm_num)

theorem noninteger_measure_recovery :
    (ProbabilityTheory.betaMeasure (1 / 2) (3 / 2)).withDensity (likelihood 0 0) =
      ProbabilityTheory.betaMeasure (1 / 2) (3 / 2) := by
  have ha : (0 : ℝ) < 1 / 2 := by norm_num
  have hb : (0 : ℝ) < 3 / 2 := by norm_num
  have h := weighted_measure ha hb 0 0
  rw [zero_counts ha hb, ENNReal.ofReal_one, one_smul] at h
  simpa using h

private theorem gamma_two : Real.Gamma 2 = 1 := by
  norm_num

private theorem gamma_three : Real.Gamma 3 = 2 := by
  norm_num

private theorem gamma_four : Real.Gamma 4 = 6 := by
  norm_num

theorem uniform_success_normalizer : normalizer 1 1 1 0 = 1 / 2 := by
  norm_num [normalizer, ProbabilityTheory.beta, Real.Gamma_one, gamma_two, gamma_three]

theorem uniform_failure_normalizer : normalizer 1 1 0 1 = 1 / 2 := by
  norm_num [normalizer, ProbabilityTheory.beta, Real.Gamma_one, gamma_two, gamma_three]

theorem uniform_success_posterior :
    (ENNReal.ofReal (1 / 2 : ℝ))⁻¹ •
      (ProbabilityTheory.betaMeasure 1 1).withDensity (likelihood 1 0) =
        ProbabilityTheory.betaMeasure 2 1 := by
  simpa only [Nat.cast_one, Nat.cast_zero, add_zero, show (1 : ℝ) + 1 = 2 by norm_num, uniform_success_normalizer] using
    normalized_posterior (by norm_num : (0 : ℝ) < 1) (by norm_num : (0 : ℝ) < 1) 1 0

theorem uniform_failure_posterior :
    (ENNReal.ofReal (1 / 2 : ℝ))⁻¹ •
      (ProbabilityTheory.betaMeasure 1 1).withDensity (likelihood 0 1) =
        ProbabilityTheory.betaMeasure 1 2 := by
  simpa only [Nat.cast_one, Nat.cast_zero, add_zero, show (1 : ℝ) + 1 = 2 by norm_num, uniform_failure_normalizer] using
    normalized_posterior (by norm_num : (0 : ℝ) < 1) (by norm_num : (0 : ℝ) < 1) 0 1

theorem distinct_posteriors : ProbabilityTheory.betaMeasure 2 1 ≠ ProbabilityTheory.betaMeasure 1 2 := by
  intro h
  have hm := congrArg (fun μ : Measure ℝ => (μ.withDensity (likelihood 1 0)) Set.univ) h
  rw [weighted_mass (by norm_num : (0 : ℝ) < 2) (by norm_num : (0 : ℝ) < 1) 1 0,
    weighted_mass (by norm_num : (0 : ℝ) < 1) (by norm_num : (0 : ℝ) < 2) 1 0] at hm
  have hr := congrArg ENNReal.toReal hm
  norm_num [normalizer, ProbabilityTheory.beta, Real.Gamma_one, gamma_two, gamma_three,
    gamma_four] at hr

theorem wrong_inverse_ratio : ENNReal.ofReal (normalizer 1 1 1 0) ≠ ENNReal.ofReal (2 : ℝ) := by
  rw [uniform_success_normalizer]
  norm_num

theorem wrong_scaled_measure_refused :
    (ProbabilityTheory.betaMeasure 1 1).withDensity (likelihood 1 0) ≠
      ENNReal.ofReal (2 : ℝ) • ProbabilityTheory.betaMeasure 2 1 := by
  intro h
  let := ProbabilityTheory.isProbabilityMeasureBeta (by norm_num : (0 : ℝ) < 2)
    (by norm_num : (0 : ℝ) < 1)
  have hm := congrArg (fun μ : Measure ℝ => μ Set.univ) h
  rw [weighted_mass (by norm_num : (0 : ℝ) < 1) (by norm_num : (0 : ℝ) < 1) 1 0] at hm
  have hr := congrArg ENNReal.toReal hm
  norm_num [uniform_success_normalizer] at hr

theorem nonpositive_shape_refused : ¬ (0 < (0 : ℝ)) ∧ ¬ (0 < (-1 : ℝ)) := by norm_num

theorem outside_pdf_zero (a b x : ℝ) (hx : x ≤ 0 ∨ 1 ≤ x) :
    ProbabilityTheory.betaPDF a b x = 0 := by
  rcases hx with h | h
  · exact ProbabilityTheory.betaPDF_eq_zero_of_nonpos h
  · exact ProbabilityTheory.betaPDF_eq_zero_of_one_le h

end BetaDensity

end

/- Source lineage c46ab183c943feea671ed259ca696f255f906e3668a663a094975714904a7a93.
Current composed integration requires its own maintained qualification. -/
section
/- Measurable likelihood-weight transport; not a generic Dirichlet conjugacy theorem. -/

set_option autoImplicit false
open MeasureTheory
namespace MeasureTransport
variable {X Y : Type*} [MeasurableSpace X] [MeasurableSpace Y]

/-- A likelihood on the observed simplex may be pulled back to stick coordinates
before weighting, with no injectivity requirement on the stick map. -/
theorem map_likelihood_weight (μ : Measure X) (T : X → Y)
    (L : Y → ENNReal) (hT : Measurable T) (hL : Measurable L) :
    (μ.withDensity (fun x => L (T x))).map T =
      (μ.map T).withDensity L := by
  ext s hs
  rw [Measure.map_apply hT hs, withDensity_apply _ (hT hs), withDensity_apply _ hs]
  exact (setLIntegral_map hs hL hT).symm

/-- The genuine two-factor product-measure density identity, ready for induction.
There is no assumed conjugacy or assumed posterior equality. -/
theorem product_likelihood_weight (μ : Measure X) (ν : Measure Y)
    [SFinite μ] [SFinite ν] (f : X → ENNReal) (g : Y → ENNReal)
    (hf : Measurable f) (hg : Measurable g) :
    (μ.prod ν).withDensity (fun z => f z.1 * g z.2) =
      (μ.withDensity f).prod (ν.withDensity g) := by
  exact (prod_withDensity hf hg).symm
end MeasureTransport

end

/- Source lineage 0e89bd49a61e0669cc66e1ac200d53b1e71047caba9ee7ced02d7588f8cb00ca.
Current composed integration requires its own maintained qualification. -/
section
/- Normalized stick-defined family; no Dirichlet density identification. -/

set_option autoImplicit false
open MeasureTheory
open scoped BigOperators
namespace StickFamily
noncomputable section

def tailShape (n : ℕ) (α : Fin (n + 1) → ℝ) (i : Fin n) : ℝ :=
  α (Fin.last n) + ∑ j ∈ Finset.univ.filter (fun j : Fin n => i < j), α j.castSucc

theorem tailShape_pos (n : ℕ) (α : Fin (n + 1) → ℝ)
    (hα : ∀ i, 0 < α i) (i : Fin n) : 0 < tailShape n α i := by
  unfold tailShape
  apply add_pos_of_pos_of_nonneg (hα _)
  exact Finset.sum_nonneg fun j _ => (hα j.castSucc).le

def stickMap (n : ℕ) (v : Fin n → ℝ) (i : Fin (n + 1)) : ℝ :=
  if h : i.val < n then
    v ⟨i.val, h⟩ * ∏ j ∈ Finset.univ.filter (fun j : Fin n => j.val < i.val), (1 - v j)
  else ∏ j : Fin n, (1 - v j)

theorem measurable_stickMap (n : ℕ) : Measurable (stickMap n) := by
  apply measurable_pi_iff.mpr
  intro i
  unfold stickMap
  split_ifs <;> fun_prop

def stickLaw (n : ℕ) (α : Fin (n + 1) → ℝ) : Measure (Fin n → ℝ) :=
  Measure.pi (fun i => ProbabilityTheory.betaMeasure (α i.castSucc) (tailShape n α i))

def family (n : ℕ) (α : Fin (n + 1) → ℝ) : Measure (Fin (n + 1) → ℝ) :=
  (stickLaw n α).map (stickMap n)

theorem stickLaw_probability (n : ℕ) (α : Fin (n + 1) → ℝ)
    (hα : ∀ i, 0 < α i) : IsProbabilityMeasure (stickLaw n α) := by
  let : ∀ i : Fin n, IsProbabilityMeasure
      (ProbabilityTheory.betaMeasure (α i.castSucc) (tailShape n α i)) :=
    fun i => ProbabilityTheory.isProbabilityMeasureBeta (hα _) (tailShape_pos n α hα i)
  unfold stickLaw
  infer_instance

theorem family_probability (n : ℕ) (α : Fin (n + 1) → ℝ)
    (hα : ∀ i, 0 < α i) : IsProbabilityMeasure (family n α) := by
  let := stickLaw_probability n α hα
  constructor
  unfold family
  rw [Measure.map_apply (measurable_stickMap n) MeasurableSet.univ, Set.preimage_univ]
  exact measure_univ

theorem stickMap_nonneg (n : ℕ) (v : Fin n → ℝ)
    (hv : ∀ j, 0 ≤ v j ∧ v j ≤ 1) (i : Fin (n + 1)) : 0 ≤ stickMap n v i := by
  unfold stickMap
  split_ifs
  · apply mul_nonneg (hv _).1
    exact Finset.prod_nonneg fun j _ => sub_nonneg.mpr (hv j).2
  · exact Finset.prod_nonneg fun j _ => sub_nonneg.mpr (hv j).2

theorem stickMap_zero (v : Fin 0 → ℝ) : stickMap 0 v = fun _ => 1 := by
  funext i
  simp [stickMap]

theorem family_zero (α : Fin 1 → ℝ) (hα : ∀ i, 0 < α i) :
    family 0 α = Measure.dirac (fun _ : Fin 1 => (1 : ℝ)) := by
  let := stickLaw_probability 0 α hα
  have hmap : stickMap 0 = fun _ : Fin 0 → ℝ => fun _ : Fin 1 => (1 : ℝ) := by
    funext v
    exact stickMap_zero v
  unfold family
  rw [hmap, Measure.map_const]
  simp

/-- The finite ordered-product identity gives exact total mass of stick coordinates. -/
theorem stickMap_sum_one (n : ℕ) (v : Fin n → ℝ) :
    ∑ i : Fin (n + 1), stickMap n v i = 1 := by
  have hfirst : (∑ i : Fin n, stickMap n v i.castSucc) =
      ∑ i : Fin n, v i * ∏ j ∈ Finset.univ.filter (fun j : Fin n => j < i), (1 - v j) := by
    apply Finset.sum_congr rfl
    intro i _
    have hfilter : Finset.univ.filter (fun j : Fin n => j.val < i.val) =
        Finset.univ.filter (fun j : Fin n => j < i) := by
      ext j
      simp only [Finset.mem_filter, Finset.mem_univ, true_and, Fin.val_fin_lt]
    simp only [stickMap, Fin.val_castSucc, dite_eq_left i.isLt]
    rw [hfilter]
  have hlast : stickMap n v (Fin.last n) = ∏ j : Fin n, (1 - v j) := by
    simp [stickMap]
  rw [Fin.sum_univ_castSucc, hfirst, hlast]
  have hprod := Finset.prod_one_sub_ordered (Finset.univ : Finset (Fin n)) v
  linarith

/-- Actual Beta density is zero outside the open unit interval; no positive-shape
assumption is needed for this support implication alone. -/
theorem beta_ae_Ioo (a b : ℝ) :
    ∀ᵐ x ∂ProbabilityTheory.betaMeasure a b, 0 < x ∧ x < 1 := by
  unfold ProbabilityTheory.betaMeasure
  apply (ae_withDensity_iff (show Measurable (ProbabilityTheory.betaPDF a b) by
    exact (ProbabilityTheory.measurable_betaPDFReal a b).ennreal_ofReal)).mpr
  exact Filter.Eventually.of_forall fun x hx => by
    by_contra hout
    apply hx
    simp [ProbabilityTheory.betaPDF, ProbabilityTheory.betaPDFReal, hout]

/-- All independent sticks lie in their genuine Beta support almost everywhere. -/
theorem stickLaw_ae_unit (n : ℕ) (α : Fin (n + 1) → ℝ)
    (hα : ∀ i, 0 < α i) :
    ∀ᵐ v ∂stickLaw n α, ∀ i, 0 ≤ v i ∧ v i ≤ 1 := by
  let : ∀ i : Fin n, IsProbabilityMeasure
      (ProbabilityTheory.betaMeasure (α i.castSucc) (tailShape n α i)) :=
    fun i => ProbabilityTheory.isProbabilityMeasureBeta (hα _) (tailShape_pos n α hα i)
  apply Filter.eventually_all.mpr
  intro i
  have hi := (MeasureTheory.Measure.tendsto_eval_ae_ae
      (μ := fun j : Fin n => ProbabilityTheory.betaMeasure (α j.castSucc) (tailShape n α j))
      (i := i)).eventually (beta_ae_Ioo (α i.castSucc) (tailShape n α i))
  exact hi.mono fun _ hx => ⟨hx.1.le, hx.2.le⟩

/-- Actual ambient pushforward is concentrated on the closed probability simplex. -/
theorem family_ae_simplex (n : ℕ) (α : Fin (n + 1) → ℝ)
    (hα : ∀ i, 0 < α i) :
    ∀ᵐ p ∂family n α, (∀ i, 0 ≤ p i) ∧ ∑ i, p i = 1 := by
  unfold family
  apply (ae_map_iff (measurable_stickMap n).aemeasurable (by measurability)).mpr
  filter_upwards [stickLaw_ae_unit n α hα] with v hv
  exact ⟨fun i => stickMap_nonneg n v hv i, stickMap_sum_one n v⟩

end
end StickFamily


end

/- Source lineage f41e9f30380595fec26ac8694726ebeb1a12de7a8d6a36e40fb8e4f8f017a0e4.
Current composed integration requires its own maintained qualification. -/
section
/- Categorical-likelihood algebraic factorization; no measure-conjugacy claim. -/
set_option autoImplicit false
open scoped BigOperators
namespace CategoricalLikelihood
/-- Rearrangement of a finite incidence likelihood, before any probabilistic identification.
An incidence column records the residual sticks used by one simplex coordinate. -/
theorem incidence_factorization {I J : Type*} [Fintype I] [Fintype J]
    (a : J → ℝ) (b : I → ℝ) (counts : J → ℕ) (uses : I → J → Prop)
    [∀ i j, Decidable (uses i j)] :
    (∏ j, (a j * ∏ i, if uses i j then b i else 1) ^ counts j) =
      (∏ j, a j ^ counts j) *
        ∏ i, b i ^ (∑ j, if uses i j then counts j else 0) := by
  simp_rw [mul_pow, ← Finset.prod_pow]
  rw [Finset.prod_mul_distrib, Finset.prod_comm]
  congr 1
  apply Finset.prod_congr rfl
  intro i _
  rw [← Finset.prod_pow_eq_pow_sum]
  apply Finset.prod_congr rfl
  intro j _
  split_ifs <;> simp_all

/-- Explicit three-category likelihood: the final stick residual contributes both
later counts. This is not a posterior-measure statement. -/
theorem three_category_pullback (u v : ℝ) (c0 c1 c2 : ℕ) :
    u ^ c0 * ((1-u)*v) ^ c1 * ((1-u)*(1-v)) ^ c2 =
      (u ^ c0 * (1-u) ^ (c1+c2)) * (v ^ c1 * (1-v) ^ c2) := by
  simp only [mul_pow, pow_add]
  ring

/-- Zero counts give the genuine unit likelihood, including boundary coordinates. -/
theorem three_category_zero_counts (u v : ℝ) :
    u ^ (0:ℕ) * ((1-u)*v) ^ (0:ℕ) * ((1-u)*(1-v)) ^ (0:ℕ) = 1 := by simp

/-- An actual wrong-tail-count control, not just a syntactic inequality. -/
theorem wrong_tail_count_refused :
    ((1-(1/2:ℝ))*(1-(1/3:ℝ))) ^ (1:ℕ) ≠
      (1-(1/3:ℝ)) ^ (1:ℕ) := by norm_num
end CategoricalLikelihood

end

/- Source lineage c3ee31e3e275df3b905c6bf8dd127bd78310ac9ac6484f74c68916557811b440.
Current composed integration requires its own maintained qualification. -/
section
/- Stick-map likelihood specialization using the shared StickFamily and
CategoricalLikelihood definitions. -/
set_option autoImplicit false
open scoped BigOperators
namespace StickMapLikelihood
open StickFamily CategoricalLikelihood
noncomputable section

def headFactor (n : ℕ) (v : Fin n → ℝ) (j : Fin (n+1)) : ℝ :=
  if h : j.val < n then v ⟨j.val,h⟩ else 1

def tailCount (n : ℕ) (c : Fin (n+1) → ℕ) (i : Fin n) : ℕ :=
  c (Fin.last n) + ∑ j ∈ Finset.univ.filter (fun j : Fin n => i < j), c j.castSucc

/-- Exact pointwise identity for the actual ordered stick map, not a newly defined proxy. -/
theorem stickMap_incidence (n : ℕ) (v : Fin n → ℝ) (j : Fin (n+1)) :
    stickMap n v j = headFactor n v j *
      ∏ i : Fin n, if i.val < j.val then (1-v i) else 1 := by
  unfold stickMap headFactor
  split_ifs with h
  · simp only [Finset.prod_filter]
  · have hj : j = Fin.last n := Fin.eq_last_of_not_lt h
    subst j
    simp

/-- Actual generic likelihood pullback in real coordinates, before ENNReal/measure lifting. -/
theorem stickMap_likelihood_incidence (n : ℕ) (v : Fin n → ℝ)
    (c : Fin (n+1) → ℕ) :
    (∏ j, stickMap n v j ^ c j) =
      (∏ j, headFactor n v j ^ c j) *
        ∏ i : Fin n, (1-v i) ^ (∑ j : Fin (n+1), if i.val < j.val then c j else 0) := by
  simp_rw [stickMap_incidence]
  exact incidence_factorization (headFactor n v) (fun i => 1-v i) c
    (fun i j => i.val < j.val)

/-- The terminal coordinate has no head stick factor; earlier heads are exactly v_i. -/
theorem headFactor_likelihood (n : ℕ) (v : Fin n → ℝ) (c : Fin (n+1) → ℕ) :
    (∏ j, headFactor n v j ^ c j) = ∏ i : Fin n, v i ^ c i.castSucc := by
  rw [Fin.prod_univ_castSucc]
  simp [headFactor]

/-- Actual ordered Beta tail shapes shift by the sum of all later categorical counts. -/
theorem tailShape_update (n : ℕ) (α : Fin (n+1) → ℝ)
    (c : Fin (n+1) → ℕ) (i : Fin n) :
    tailShape n (fun j => α j + (c j : ℝ)) i =
      tailShape n α i + (tailCount n c i : ℝ) := by
  unfold tailShape tailCount
  push_cast
  rw [Finset.sum_add_distrib]
  ring

/-- Empty-stick boundary retains a unit categorical likelihood at the sole simplex point. -/
theorem zero_stick_likelihood (v : Fin 0 → ℝ) (c : Fin 1 → ℕ) :
    (∏ j, stickMap 0 v j ^ c j) = 1 := by
  simp [stickMap_zero]
end
end StickMapLikelihood

end

/- Source lineage 561cec459fba313559a48ed377fefd67e1b7f6cf3f0cc36fd420efdd23906a9c.
Current composed integration requires its own maintained qualification. -/
section
/- Tail-count and almost-everywhere likelihood transfer; no posterior-measure claim. -/
set_option autoImplicit false
open MeasureTheory
open scoped BigOperators
namespace TailCountTransfer
open StickFamily StickMapLikelihood
noncomputable section

theorem tail_exponent_eq (n : ℕ) (c : Fin (n+1) → ℕ) (i : Fin n) :
    (∑ j : Fin (n+1), if i.val < j.val then c j else 0) = tailCount n c i := by
  rw [Fin.sum_univ_castSucc]
  simp [tailCount, Finset.sum_filter, Fin.val_fin_lt, Nat.add_comm]

theorem real_likelihood_pullback (n : ℕ) (v : Fin n → ℝ) (c : Fin (n+1) → ℕ) :
    (∏ j, stickMap n v j ^ c j) =
      ∏ i : Fin n, (v i ^ c i.castSucc * (1-v i) ^ tailCount n c i) := by
  rw [stickMap_likelihood_incidence, headFactor_likelihood]
  simp_rw [tail_exponent_eq]
  exact (Finset.prod_mul_distrib).symm

theorem ofReal_product {K : Type*} [Fintype K] (f : K → ℝ) (hf : ∀ k, 0 ≤ f k) :
    ENNReal.ofReal (∏ k, f k) = ∏ k, ENNReal.ofReal (f k) := by
  exact ENNReal.ofReal_prod_of_nonneg (fun k _ => hf k)

def categoricalLikelihood (n : ℕ) (c : Fin (n+1) → ℕ) (p : Fin (n+1) → ℝ) : ENNReal :=
  ∏ j, ENNReal.ofReal (p j) ^ c j

def stickLikelihood (n : ℕ) (c : Fin (n+1) → ℕ) (v : Fin n → ℝ) : ENNReal :=
  ∏ i, ENNReal.ofReal (v i) ^ c i.castSucc * ENNReal.ofReal (1-v i) ^ tailCount n c i

theorem ennreal_likelihood_pullback (n : ℕ) (v : Fin n → ℝ) (c : Fin (n+1) → ℕ)
    (hv : ∀ i, 0 ≤ v i ∧ v i ≤ 1) :
    categoricalLikelihood n c (stickMap n v) = stickLikelihood n c v := by
  have left : ENNReal.ofReal (∏ j, stickMap n v j ^ c j) =
      categoricalLikelihood n c (stickMap n v) := by
    rw [ofReal_product _ (fun j => pow_nonneg (stickMap_nonneg n v hv j) _)]
    apply Finset.prod_congr rfl
    intro j _
    exact ENNReal.ofReal_pow (stickMap_nonneg n v hv j) _
  have right : ENNReal.ofReal (∏ i : Fin n, v i ^ c i.castSucc * (1-v i) ^ tailCount n c i) =
      stickLikelihood n c v := by
    rw [ofReal_product _ (fun i => mul_nonneg (pow_nonneg (hv i).1 _) (pow_nonneg (sub_nonneg.mpr (hv i).2) _))]
    apply Finset.prod_congr rfl
    intro i _
    rw [ENNReal.ofReal_mul (pow_nonneg (hv i).1 _), ENNReal.ofReal_pow (hv i).1,
      ENNReal.ofReal_pow (sub_nonneg.mpr (hv i).2)]
  rw [← left, real_likelihood_pullback, right]

theorem ae_likelihood_pullback (n : ℕ) (α : Fin (n+1) → ℝ)
    (hα : ∀ j, 0 < α j) (c : Fin (n+1) → ℕ) :
    ∀ᵐ v ∂stickLaw n α, categoricalLikelihood n c (stickMap n v) = stickLikelihood n c v := by
  filter_upwards [stickLaw_ae_unit n α hα] with v hv
  exact ennreal_likelihood_pullback n v c hv
end
end TailCountTransfer

end

/- Source lineage a69e44fa9874fc7374ca30955956f8b2d196f761887fa38a6b5fbabf0b40c84a.
Current composed integration requires its own maintained qualification. -/
section
/- Finite-product likelihood-weighting induction; no new measure definition. -/
set_option autoImplicit false
open MeasureTheory
open scoped BigOperators
namespace FinitePiWeighting
open MeasureTransport
noncomputable section

/-- The weighted finite product is the product of actual coordinate-weighted measures.
Sigma-finiteness of weighted coordinates is explicit and is satisfied by the
positive-shape Beta weighted identities; it is not the target conjugacy equality. -/
theorem fin_pi_withDensity (n : ℕ) (μ : Fin n → Measure ℝ)
    (f : Fin n → ℝ → ENNReal) [∀ i, SigmaFinite (μ i)]
    [∀ i, SigmaFinite ((μ i).withDensity (f i))] (hf : ∀ i, Measurable (f i)) :
    (Measure.pi μ).withDensity (fun x => ∏ i, f i (x i)) =
      Measure.pi (fun i => (μ i).withDensity (f i)) := by
  induction n with
  | zero =>
      have hempty : (fun i : Fin 0 => (μ i).withDensity (f i)) = μ := by
        funext i
        exact Fin.elim0 i
      rw [hempty]
      simp only [Finset.univ_eq_empty, Finset.prod_empty, withDensity_const, one_smul]
  | succ n ih =>
      let e := (MeasurableEquiv.piFinSuccAbove (fun _ : Fin (n+1) => ℝ) 0).symm
      let μtail := Measure.pi (fun i : Fin n => μ i.succ)
      let νtail := Measure.pi (fun i : Fin n => (μ i.succ).withDensity (f i.succ))
      have hprior : ((μ 0).prod μtail).map e = Measure.pi μ :=
        (measurePreserving_piFinSuccAbove μ 0).symm.map_eq
      have hpost : (((μ 0).withDensity (f 0)).prod νtail).map e =
          Measure.pi (fun i => (μ i).withDensity (f i)) :=
        (measurePreserving_piFinSuccAbove (fun i => (μ i).withDensity (f i)) 0).symm.map_eq
      have hweight : (fun z : ℝ × (Fin n → ℝ) => ∏ i : Fin (n+1), f i (e z i)) =
          fun z => f 0 z.1 * ∏ i : Fin n, f i.succ (z.2 i) := by
        funext z
        simp [e, MeasurableEquiv.piFinSuccAbove_symm_apply, Fin.insertNthEquiv,
          Fin.prod_univ_succ, Fin.zero_succAbove]
      have hL : Measurable (fun x : Fin (n+1) → ℝ => ∏ i, f i (x i)) := by fun_prop
      calc
        _ = (((μ 0).prod μtail).withDensity
              (fun z => f 0 z.1 * ∏ i : Fin n, f i.succ (z.2 i))).map e := by
          rw [← hweight, map_likelihood_weight _ _ _ e.measurable hL, hprior]
        _ = (((μ 0).withDensity (f 0)).prod νtail).map e := by
          let g : (Fin n → ℝ) → ENNReal := fun x => ∏ i, f i.succ (x i)
          have hg : Measurable g := by fun_prop
          have hsplit := (prod_withDensity (μ := μ 0) (ν := μtail)
            (f := f 0) (g := g) (hf 0) hg).symm
          have htail : μtail.withDensity g = νtail :=
            ih (fun i => μ i.succ) (fun i => f i.succ) (fun i => hf i.succ)
          exact congrArg (fun ν : Measure (ℝ × (Fin n → ℝ)) => ν.map e)
            (hsplit.trans (congrArg (fun ν => ((μ 0).withDensity (f 0)).prod ν) htail))
        _ = _ := hpost

/-- Coordinate scale factors collect into their genuine finite product. -/
theorem pi_scale_factors {K : Type*} [Fintype K] (μ : K → Measure ℝ)
    (c : K → ENNReal) [∀ i, SigmaFinite (μ i)]
    [∀ i, SigmaFinite (c i • μ i)] :
    Measure.pi (fun i => c i • μ i) = (∏ i, c i) • Measure.pi μ := by
  apply Measure.pi_eq
  intro s hs
  rw [Measure.smul_apply, Measure.pi_pi]
  simp_rw [Measure.smul_apply]
  exact (Finset.prod_mul_distrib).symm
end
end FinitePiWeighting

end

/- Source lineage bd1b617cde71d9d8a67313835f21fb1d324db3ff40a99d6c061aa30cff5ab676.
Current composed integration requires its own maintained qualification. -/
section
/- Independent Beta-coordinate likelihood weighting and normalized posterior. -/
set_option autoImplicit false
open MeasureTheory
open scoped BigOperators
namespace BetaProductPosterior
open BetaDensity FinitePiWeighting
noncomputable section

def betaPiZ (n : ℕ) (a b : Fin n → ℝ) (s t : Fin n → ℕ) : ENNReal :=
  ∏ i, ENNReal.ofReal (normalizer (a i) (b i) (s i) (t i))

theorem betaPiZ_pos_finite (n : ℕ) (a b : Fin n → ℝ) (s t : Fin n → ℕ)
    (ha : ∀ i, 0<a i) (hb : ∀ i, 0<b i) :
    betaPiZ n a b s t ≠ 0 ∧ betaPiZ n a b s t ≠ ⊤ := by
  constructor
  · exact Finset.prod_ne_zero_iff.mpr fun i _ =>
      ne_of_gt (ENNReal.ofReal_pos.mpr (normalizer_pos (ha i) (hb i) (s i) (t i)))
  · exact ENNReal.prod_ne_top fun i _ => normalizer_finite (a i) (b i) (s i) (t i)

theorem weighted_beta_pi (n : ℕ) (a b : Fin n → ℝ) (s t : Fin n → ℕ)
    (ha : ∀ i, 0<a i) (hb : ∀ i, 0<b i) :
    (Measure.pi (fun i => ProbabilityTheory.betaMeasure (a i) (b i))).withDensity
      (fun x => ∏ i, likelihood (s i) (t i) (x i)) =
    betaPiZ n a b s t • Measure.pi (fun i =>
      ProbabilityTheory.betaMeasure (a i+(s i:ℝ)) (b i+(t i:ℝ))) := by
  let : ∀ i, IsProbabilityMeasure (ProbabilityTheory.betaMeasure (a i) (b i)) :=
    fun i => ProbabilityTheory.isProbabilityMeasureBeta (ha i) (hb i)
  let : ∀ i, IsProbabilityMeasure
      (ProbabilityTheory.betaMeasure (a i+(s i:ℝ)) (b i+(t i:ℝ))) :=
    fun i => ProbabilityTheory.isProbabilityMeasureBeta
      (add_pos_of_pos_of_nonneg (ha i) (Nat.cast_nonneg (s i)))
      (add_pos_of_pos_of_nonneg (hb i) (Nat.cast_nonneg (t i)))
  let : ∀ i, IsFiniteMeasure ((ProbabilityTheory.betaMeasure (a i) (b i)).withDensity
      (likelihood (s i) (t i))) := fun i => ⟨by
    rw [weighted_mass (ha i) (hb i) (s i) (t i)]
    exact ENNReal.ofReal_lt_top⟩
  have hcoord : (fun i => (ProbabilityTheory.betaMeasure (a i) (b i)).withDensity
      (likelihood (s i) (t i))) = fun i =>
      ENNReal.ofReal (normalizer (a i) (b i) (s i) (t i)) •
      ProbabilityTheory.betaMeasure (a i+(s i:ℝ)) (b i+(t i:ℝ)) := by
    funext i
    exact weighted_measure (ha i) (hb i) (s i) (t i)
  let : ∀ i, SigmaFinite (ENNReal.ofReal (normalizer (a i) (b i) (s i) (t i)) •
      ProbabilityTheory.betaMeasure (a i+(s i:ℝ)) (b i+(t i:ℝ))) := fun i => by
    rw [← weighted_measure (ha i) (hb i) (s i) (t i)]
    infer_instance
  rw [fin_pi_withDensity n _ _ (fun i => likelihood_measurable (s i) (t i)), hcoord]
  exact pi_scale_factors _ _

theorem normalized_beta_pi (n : ℕ) (a b : Fin n → ℝ) (s t : Fin n → ℕ)
    (ha : ∀ i, 0<a i) (hb : ∀ i, 0<b i) :
    (betaPiZ n a b s t)⁻¹ •
      (Measure.pi (fun i => ProbabilityTheory.betaMeasure (a i) (b i))).withDensity
        (fun x => ∏ i, likelihood (s i) (t i) (x i)) =
      Measure.pi (fun i => ProbabilityTheory.betaMeasure (a i+(s i:ℝ)) (b i+(t i:ℝ))) := by
  rw [weighted_beta_pi n a b s t ha hb, smul_smul,
    ENNReal.inv_mul_cancel (betaPiZ_pos_finite n a b s t ha hb).1
      (betaPiZ_pos_finite n a b s t ha hb).2, one_smul]

theorem betaPiZ_empty (a b : Fin 0 → ℝ) (s t : Fin 0 → ℕ) :
    betaPiZ 0 a b s t = 1 := by simp [betaPiZ]
end
end BetaProductPosterior

end

/- Source lineage 894d96a1303301d8b19c3167dd1ba61fcdf0648d57e7e9df0628b558553f890d.
Current composed integration requires its own maintained qualification. -/
section
/- Categorical posterior of the constructed stick family.
This is not a simplex Lebesgue/Jacobian identification. -/
set_option autoImplicit false
open MeasureTheory
open scoped BigOperators
namespace StickFamilyPosterior
open BetaDensity BetaProductPosterior StickFamily
open StickMapLikelihood TailCountTransfer
open MeasureTransport
noncomputable section

def stickZ (n : ℕ) (α : Fin (n+1) → ℝ) (c : Fin (n+1) → ℕ) : ENNReal :=
  betaPiZ n (fun i => α i.castSucc) (tailShape n α)
    (fun i => c i.castSucc) (tailCount n c)

theorem stickZ_pos_finite (n : ℕ) (α : Fin (n+1) → ℝ)
    (hα : ∀ j, 0<α j) (c : Fin (n+1) → ℕ) :
    stickZ n α c ≠ 0 ∧ stickZ n α c ≠ ⊤ :=
  betaPiZ_pos_finite n _ _ _ _ (fun i => hα i.castSucc) (tailShape_pos n α hα)

theorem weighted_stickLaw (n : ℕ) (α : Fin (n+1) → ℝ)
    (hα : ∀ j, 0<α j) (c : Fin (n+1) → ℕ) :
    (stickLaw n α).withDensity (stickLikelihood n c) =
      stickZ n α c • stickLaw n (fun j => α j+(c j:ℝ)) := by
  have h := weighted_beta_pi n (fun i => α i.castSucc) (tailShape n α)
    (fun i => c i.castSucc) (tailCount n c)
    (fun i => hα i.castSucc) (tailShape_pos n α hα)
  have hlik : stickLikelihood n c =
      fun x => ∏ i : Fin n, likelihood (c i.castSucc) (tailCount n c i) (x i) := by
    funext x
    rfl
  rw [hlik]
  simpa only [stickLaw, stickZ, tailShape_update] using h

theorem weighted_family (n : ℕ) (α : Fin (n+1) → ℝ)
    (hα : ∀ j, 0<α j) (c : Fin (n+1) → ℕ) :
    (family n α).withDensity (categoricalLikelihood n c) =
      stickZ n α c • family n (fun j => α j+(c j:ℝ)) := by
  unfold family
  rw [← map_likelihood_weight _ _ _ (measurable_stickMap n) (by
    unfold categoricalLikelihood
    fun_prop)]
  rw [withDensity_congr_ae (ae_likelihood_pullback n α hα c),
    weighted_stickLaw n α hα c, Measure.map_smul _ (measurable_stickMap n).aemeasurable]

theorem weighted_family_mass (n : ℕ) (α : Fin (n+1) → ℝ)
    (hα : ∀ j, 0<α j) (c : Fin (n+1) → ℕ) :
    ((family n α).withDensity (categoricalLikelihood n c)) Set.univ = stickZ n α c := by
  let := family_probability n (fun j => α j+(c j:ℝ))
    (fun j => add_pos_of_pos_of_nonneg (hα j) (Nat.cast_nonneg (c j)))
  rw [weighted_family n α hα c]
  simp

theorem normalized_family (n : ℕ) (α : Fin (n+1) → ℝ)
    (hα : ∀ j, 0<α j) (c : Fin (n+1) → ℕ) :
    (stickZ n α c)⁻¹ • (family n α).withDensity (categoricalLikelihood n c) =
      family n (fun j => α j+(c j:ℝ)) := by
  rw [weighted_family n α hα c, smul_smul,
    ENNReal.inv_mul_cancel (stickZ_pos_finite n α hα c).1
      (stickZ_pos_finite n α hα c).2, one_smul]
end
end StickFamilyPosterior

end

end FEP.EmpiricalRisk

/-! Independent natural-count row posterior over the existing stick-family carrier. -/
set_option autoImplicit false
open MeasureTheory
open scoped BigOperators
namespace FEP.EmpiricalRisk
namespace ConditioningRowProductProposal
open FEP.EmpiricalRisk.MeasureTransport
noncomputable section
variable {E : Type*} [MeasurableSpace E]
theorem vector_pi_withDensity (n : ℕ) (μ : Fin n → Measure E)
    (f : Fin n → E → ENNReal) [∀ i, SigmaFinite (μ i)]
    [∀ i, SigmaFinite ((μ i).withDensity (f i))] (hf : ∀ i, Measurable (f i)) :
    (Measure.pi μ).withDensity (fun x => ∏ i, f i (x i)) =
      Measure.pi (fun i => (μ i).withDensity (f i)) := by
  induction n with
  | zero =>
      have hempty : (fun i : Fin 0 => (μ i).withDensity (f i)) = μ := by
        funext i
        exact Fin.elim0 i
      rw [hempty]
      simp only [Finset.univ_eq_empty, Finset.prod_empty, withDensity_const, one_smul]
  | succ n ih =>
      let e := (MeasurableEquiv.piFinSuccAbove (fun _ : Fin (n+1) => E) 0).symm
      let μtail := Measure.pi (fun i : Fin n => μ i.succ)
      let νtail := Measure.pi (fun i : Fin n => (μ i.succ).withDensity (f i.succ))
      have hprior : ((μ 0).prod μtail).map e = Measure.pi μ :=
        (measurePreserving_piFinSuccAbove μ 0).symm.map_eq
      have hpost : (((μ 0).withDensity (f 0)).prod νtail).map e =
          Measure.pi (fun i => (μ i).withDensity (f i)) :=
        (measurePreserving_piFinSuccAbove (fun i => (μ i).withDensity (f i)) 0).symm.map_eq
      have hweight : (fun z : E × (Fin n → E) => ∏ i : Fin (n+1), f i (e z i)) =
          fun z => f 0 z.1 * ∏ i : Fin n, f i.succ (z.2 i) := by
        funext z
        simp [e, MeasurableEquiv.piFinSuccAbove_symm_apply, Fin.insertNthEquiv,
          Fin.prod_univ_succ, Fin.zero_succAbove]
      have hL : Measurable (fun x : Fin (n+1) → E => ∏ i, f i (x i)) := by fun_prop
      calc
        _ = (((μ 0).prod μtail).withDensity
              (fun z => f 0 z.1 * ∏ i : Fin n, f i.succ (z.2 i))).map e := by
          rw [← hweight, map_likelihood_weight _ _ _ e.measurable hL, hprior]
        _ = (((μ 0).withDensity (f 0)).prod νtail).map e := by
          let g : (Fin n → E) → ENNReal := fun x => ∏ i, f i.succ (x i)
          have hg : Measurable g := by fun_prop
          have hsplit := (prod_withDensity (μ := μ 0) (ν := μtail)
            (f := f 0) (g := g) (hf 0) hg).symm
          have htail : μtail.withDensity g = νtail :=
            ih (fun i => μ i.succ) (fun i => f i.succ) (fun i => hf i.succ)
          exact congrArg (fun ν : Measure (E × (Fin n → E)) => ν.map e)
            (hsplit.trans (congrArg (fun ν => ((μ 0).withDensity (f 0)).prod ν) htail))
        _ = _ := hpost

/-- Coordinate scale factors collect into their genuine finite product. -/
theorem vector_pi_scale_factors {K : Type*} [Fintype K] (μ : K → Measure E)
    (c : K → ENNReal) [∀ i, SigmaFinite (μ i)]
    [∀ i, SigmaFinite (c i • μ i)] :
    Measure.pi (fun i => c i • μ i) = (∏ i, c i) • Measure.pi μ := by
  apply Measure.pi_eq
  intro s hs
  rw [Measure.smul_apply, Measure.pi_pi]
  simp_rw [Measure.smul_apply]
  exact (Finset.prod_mul_distrib).symm
end
end ConditioningRowProductProposal
end FEP.EmpiricalRisk

namespace FEP.EmpiricalRisk
namespace ConditioningRowProductProposal
open StickFamily StickFamilyPosterior TailCountTransfer
noncomputable section

def matrixZ (m k : ℕ) (α : Fin m → Fin (k+1) → ℝ)
    (c : Fin m → Fin (k+1) → ℕ) : ENNReal := ∏ r, stickZ k (α r) (c r)

theorem weighted_rows (m k : ℕ) (α : Fin m → Fin (k+1) → ℝ)
    (hα : ∀ r j, 0<α r j) (c : Fin m → Fin (k+1) → ℕ) :
    (Measure.pi (fun r => family k (α r))).withDensity
      (fun A => ∏ r, categoricalLikelihood k (c r) (A r)) =
      matrixZ m k α c • Measure.pi (fun r => family k (fun j => α r j+(c r j:ℝ))) := by
  let : ∀ r, IsProbabilityMeasure (family k (α r)) := fun r => family_probability k (α r) (hα r)
  let : ∀ r, IsProbabilityMeasure (family k (fun j => α r j+(c r j:ℝ))) :=
    fun r => family_probability k (fun j => α r j+(c r j:ℝ)) (fun j => add_pos_of_pos_of_nonneg (hα r j) (Nat.cast_nonneg _))
  let : ∀ r, IsFiniteMeasure ((family k (α r)).withDensity (categoricalLikelihood k (c r))) :=
    fun r => ⟨by rw [weighted_family_mass k (α r) (hα r) (c r)]; exact lt_top_iff_ne_top.mpr (stickZ_pos_finite k (α r) (hα r) (c r)).2⟩
  have hrow : (fun r => (family k (α r)).withDensity (categoricalLikelihood k (c r))) =
      fun r => stickZ k (α r) (c r) • family k (fun j => α r j+(c r j:ℝ)) := by
    funext r; exact weighted_family k (α r) (hα r) (c r)
  let : ∀ r, SigmaFinite (stickZ k (α r) (c r) • family k (fun j => α r j+(c r j:ℝ))) :=
    fun r => by rw [← weighted_family k (α r) (hα r) (c r)]; infer_instance
  rw [vector_pi_withDensity m _ _ (by intro r; unfold categoricalLikelihood; fun_prop), hrow]
  exact vector_pi_scale_factors _ _

theorem matrixZ_pos_finite (m k : ℕ) (α : Fin m → Fin (k+1) → ℝ)
    (hα : ∀ r j, 0<α r j) (c : Fin m → Fin (k+1) → ℕ) :
    matrixZ m k α c ≠ 0 ∧ matrixZ m k α c ≠ ⊤ := by
  constructor
  · exact Finset.prod_ne_zero_iff.mpr fun r _ => (stickZ_pos_finite k (α r) (hα r) (c r)).1
  · exact ENNReal.prod_ne_top fun r _ => (stickZ_pos_finite k (α r) (hα r) (c r)).2

theorem normalized_rows (m k : ℕ) (α : Fin m → Fin (k+1) → ℝ)
    (hα : ∀ r j, 0<α r j) (c : Fin m → Fin (k+1) → ℕ) :
    (matrixZ m k α c)⁻¹ • (Measure.pi (fun r => family k (α r))).withDensity
      (fun A => ∏ r, categoricalLikelihood k (c r) (A r)) =
      Measure.pi (fun r => family k (fun j => α r j+(c r j:ℝ))) := by
  rw [weighted_rows m k α hα c, smul_smul,
    ENNReal.inv_mul_cancel (matrixZ_pos_finite m k α hα c).1 (matrixZ_pos_finite m k α hα c).2, one_smul]

end
end ConditioningRowProductProposal
end FEP.EmpiricalRisk
