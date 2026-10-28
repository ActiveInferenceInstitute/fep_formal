"""Lean bodies for finite-sample risk and Laplace calibration."""

from __future__ import annotations

BODIES: dict[str, str] = {
    "fep-121": """import FepSketches.empirical_risk

/-! # Laplace-Smoothing Error Identity -/
namespace FEP121

open FEP.EmpiricalRisk

/-- For a positive finite sample, add-one error is contracted empirical error
plus the exact target-dependent offset. -/
theorem fep121_laplaceError_identity
    (successes sampleCount : ℕ) (target : ℝ)
    (sampleCountPositive : 0 < sampleCount)
    (successesAtMost : successes ≤ sampleCount)
    (targetBounds : target ∈ Set.Icc (0 : ℝ) 1) :
    laplaceEstimate successes sampleCount - target =
      shrinkage sampleCount * (empiricalRate successes sampleCount - target) +
        laplaceBias sampleCount target := by
  have _ := successesAtMost
  have _ := targetBounds
  exact laplaceError_identity successes sampleCount target sampleCountPositive

/-- The contraction coefficient remains in the closed unit interval. -/
theorem fep121_shrinkage_mem_unitInterval (sampleCount : ℕ) :
    shrinkage sampleCount ∈ Set.Icc (0 : ℝ) 1 :=
  ⟨shrinkage_nonneg sampleCount, shrinkage_le_one sampleCount⟩

end FEP121
""",
    "fep-122": """import FepSketches.empirical_risk

/-! # Laplace-Smoothing Bias Bound -/
namespace FEP122

open FEP.EmpiricalRisk

/-- The target-dependent Laplace offset is bounded by one pseudo-count over
the smoothed sample size. -/
theorem fep122_laplaceBias_abs_le (sampleCount : ℕ) (target : ℝ)
    (targetBounds : target ∈ Set.Icc (0 : ℝ) 1) :
    |laplaceBias sampleCount target| ≤
      1 / ((sampleCount : ℝ) + 2) :=
  laplaceBias_abs_le sampleCount target targetBounds

/-- The bias is genuinely nonzero at a boundary target. -/
theorem fep122_nonzero_boundary_witness :
    laplaceBias 2 0 = 1 / 4 ∧ laplaceBias 2 0 ≠ 0 :=
  laplaceBias_nonzero_witness

end FEP122
""",
    "fep-123": """import FepSketches.empirical_risk

/-! # Absolute-Error Transfer -/
namespace FEP123

open FEP.EmpiricalRisk

/-- An empirical absolute-error certificate transfers through add-one
smoothing with exact shrinkage and offset terms. -/
theorem fep123_laplaceAbsoluteError_le
    (successes sampleCount : ℕ) (target error : ℝ)
    (sampleCountPositive : 0 < sampleCount)
    (successesAtMost : successes ≤ sampleCount)
    (targetBounds : target ∈ Set.Icc (0 : ℝ) 1)
    (empiricalErrorBound :
      |empiricalRate successes sampleCount - target| ≤ error) :
    |laplaceEstimate successes sampleCount - target| ≤
      shrinkage sampleCount * error + 1 / ((sampleCount : ℝ) + 2) := by
  have _ := successesAtMost
  exact laplaceAbsoluteError_le successes sampleCount target error
    sampleCountPositive targetBounds empiricalErrorBound

/-- The transferred threshold cannot hide a negative empirical tolerance. -/
theorem fep123_error_nonnegative
    (successes sampleCount : ℕ) (target error : ℝ)
    (empiricalErrorBound :
      |empiricalRate successes sampleCount - target| ≤ error) :
    0 ≤ error :=
  (abs_nonneg _).trans empiricalErrorBound

end FEP123
""",
    "fep-124": """import FepSketches.empirical_risk

/-! # Squared-Risk Transfer -/
namespace FEP124

open FEP FEP.EmpiricalRisk

/-- Pointwise squared Laplace error is controlled by contracted empirical
squared error and the squared pseudo-count offset. -/
theorem fep124_laplaceSquaredError_le
    (successes sampleCount : ℕ) (target : ℝ)
    (sampleCountPositive : 0 < sampleCount)
    (successesAtMost : successes ≤ sampleCount)
    (targetBounds : target ∈ Set.Icc (0 : ℝ) 1) :
    (laplaceEstimate successes sampleCount - target) ^ 2 ≤
      2 * shrinkage sampleCount ^ 2 *
          (empiricalRate successes sampleCount - target) ^ 2 +
        2 * (1 / ((sampleCount : ℝ) + 2)) ^ 2 := by
  have _ := successesAtMost
  exact laplaceSquaredError_le successes sampleCount target
    sampleCountPositive targetBounds

/-- The same pointwise inequality integrates under every normalized finite
sampling law. -/
theorem fep124_laplaceSquaredRisk_le
    {Ω : Type*} [Fintype Ω] (sampling : FiniteLaw Ω)
    (successes : Ω → ℕ) (sampleCount : ℕ) (target : ℝ)
    (sampleCountPositive : 0 < sampleCount)
    (successesAtMost : ∀ outcome, successes outcome ≤ sampleCount)
    (targetBounds : target ∈ Set.Icc (0 : ℝ) 1) :
    FEP.VariationalDuality.expectation sampling (fun outcome =>
      (laplaceEstimate (successes outcome) sampleCount - target) ^ 2) ≤
      2 * shrinkage sampleCount ^ 2 *
          FEP.VariationalDuality.expectation sampling (fun outcome =>
            (empiricalRate (successes outcome) sampleCount - target) ^ 2) +
        2 * (1 / ((sampleCount : ℝ) + 2)) ^ 2 :=
  laplaceSquaredRisk_le sampling successes sampleCount target
    sampleCountPositive successesAtMost targetBounds

end FEP124
""",
    "fep-125": """import FepSketches.empirical_risk

/-! # Bernoulli Brier Excess-Risk Identity -/
namespace FEP125

open FEP.EmpiricalRisk

/-- Bernoulli Brier excess risk is exactly squared probability error. -/
theorem fep125_brierExcess_eq_sqError (target forecast : ℝ) :
    bernoulliBrierScore target forecast - bernoulliBrierScore target target =
      (forecast - target) ^ 2 :=
  brierExcess_eq_sqError target forecast

/-- Forecasting the target itself has zero excess Brier risk. -/
theorem fep125_brierExcess_self (target : ℝ) :
    bernoulliBrierScore target target - bernoulliBrierScore target target = 0 := by
  ring

end FEP125
""",
    "fep-126": """import FepSketches.empirical_risk

/-! # Laplace Brier-Risk Bound -/
namespace FEP126

open FEP FEP.EmpiricalRisk

/-- The Brier excess risk of the add-one forecast inherits the finite-law
squared-error transfer bound. -/
theorem fep126_laplaceBrierRisk_le
    {Ω : Type*} [Fintype Ω] (sampling : FiniteLaw Ω)
    (successes : Ω → ℕ) (sampleCount : ℕ) (target : ℝ)
    (sampleCountPositive : 0 < sampleCount)
    (successesAtMost : ∀ outcome, successes outcome ≤ sampleCount)
    (targetBounds : target ∈ Set.Icc (0 : ℝ) 1) :
    brierExcessRisk sampling
        (fun outcome => laplaceEstimate (successes outcome) sampleCount) target ≤
      2 * shrinkage sampleCount ^ 2 *
          FEP.VariationalDuality.expectation sampling (fun outcome =>
            (empiricalRate (successes outcome) sampleCount - target) ^ 2) +
        2 * (1 / ((sampleCount : ℝ) + 2)) ^ 2 :=
  laplaceBrierRisk_le sampling successes sampleCount target
    sampleCountPositive successesAtMost targetBounds

/-- The risk theorem is finite-law weighted; it does not require a continuous
sampling carrier. -/
theorem fep126_sampling_mass_one
    {Ω : Type*} [Fintype Ω] (sampling : FiniteLaw Ω) :
    ∑ outcome, sampling outcome = 1 :=
  sampling.sum_one

end FEP126
""",
    "fep-127": """import FepSketches.empirical_risk

/-! # Concentration-Event Transfer Through Smoothing -/
namespace FEP127

open FEP FEP.EmpiricalRisk

/-- A smoothed deviation beyond the transferred threshold is contained in the
corresponding raw empirical-deviation event. -/
theorem fep127_laplaceBadEvent_subset
    {Ω : Type*} [Fintype Ω] (successes : Ω → ℕ)
    (sampleCount : ℕ) (target error : ℝ)
    (sampleCountPositive : 0 < sampleCount)
    (successesAtMost : ∀ outcome, successes outcome ≤ sampleCount)
    (targetBounds : target ∈ Set.Icc (0 : ℝ) 1) :
    laplaceBadEvent successes sampleCount target error ⊆
      empiricalBadEvent successes sampleCount target error :=
  laplaceBadEvent_subset successes sampleCount target error
    sampleCountPositive successesAtMost targetBounds

/-- Any finite-law bound on the raw event transfers to the contained smoothed
event without asserting a general posterior-contraction theorem. -/
theorem fep127_laplaceBadEvent_probability_le
    {Ω : Type*} [Fintype Ω] (sampling : FiniteLaw Ω)
    (successes : Ω → ℕ) (sampleCount : ℕ)
    (target error failure : ℝ)
    (sampleCountPositive : 0 < sampleCount)
    (successesAtMost : ∀ outcome, successes outcome ≤ sampleCount)
    (targetBounds : target ∈ Set.Icc (0 : ℝ) 1)
    (rawProbabilityBound :
      finiteEventProbability sampling
        (empiricalBadEvent successes sampleCount target error) ≤ failure) :
    finiteEventProbability sampling
        (laplaceBadEvent successes sampleCount target error) ≤ failure :=
  laplaceBadEvent_probability_le sampling successes sampleCount target error
    failure sampleCountPositive successesAtMost targetBounds rawProbabilityBound

end FEP127
""",
}
