import FepSketches.learning_theory

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
/-- The Pólya predictive is the normalised posterior pseudo-count vector. -/
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
