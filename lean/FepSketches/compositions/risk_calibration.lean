module
public import FepSketches.families.core_bayesian_mechanics
public import FepSketches.families.finite_sample_risk_calibration
public import FepSketches.families.learning_theory
public import FepSketches.empirical_risk

@[expose] public section

/-!
# Finite risk and calibration topic compositions

These witnesses pair the new finite-law Laplace and Brier contracts with the
earlier empirical-prior and finite-concentration topics.  Conjunctions keep the
distinct carriers explicit; no posterior-contraction or carrier-conversion
claim is inferred from the pairing.
-/

namespace FEPComposed

open FEP FEP.EmpiricalRisk FEP.VariationalDuality Finset
open MeasureTheory ProbabilityTheory
open scoped BigOperators ENNReal MeasureTheory NNReal ProbabilityTheory

/-- The target-relative Laplace error identity is paired with the earlier
target-free shrinkage identity for the same finite count. -/
theorem fep121_laplaceError_extends_fep036
    (successes sampleCount : ℕ) (target : ℝ)
    (sampleCountPositive : 0 < sampleCount)
    (successesAtMost : successes ≤ sampleCount)
    (targetBounds : target ∈ Set.Icc (0 : ℝ) 1) :
    (laplaceEstimate successes sampleCount - target =
      shrinkage sampleCount * (empiricalRate successes sampleCount - target) +
        laplaceBias sampleCount target) ∧
      (fep_fep036.FEP036.fep036_smoothedRate successes sampleCount =
        ((successes : ℝ) / sampleCount) *
            ((sampleCount : ℝ) / (sampleCount + 2)) +
          1 / ((sampleCount : ℝ) + 2)) := by
  exact
    ⟨fep_fep121.FEP121.fep121_laplaceError_identity
        successes sampleCount target sampleCountPositive successesAtMost
        targetBounds,
      fep_fep036.FEP036.fep036_smoothedRate_eq_shrunkEmpirical
        sampleCountPositive⟩

/-- The explicit target-dependent bias bound is paired with the earlier
interior-probability boundary for an admissible success count. -/
theorem fep122_laplaceBias_extends_fep036
    (successes sampleCount : ℕ) (target : ℝ)
    (successesAtMost : successes ≤ sampleCount)
    (targetBounds : target ∈ Set.Icc (0 : ℝ) 1) :
    (|laplaceBias sampleCount target| ≤
      1 / ((sampleCount : ℝ) + 2)) ∧
      (fep_fep036.FEP036.fep036_smoothedRate successes sampleCount ∈
        Set.Ioo (0 : ℝ) 1) := by
  exact
    ⟨fep_fep122.FEP122.fep122_laplaceBias_abs_le
        sampleCount target targetBounds,
      fep_fep036.FEP036.fep036_smoothedRate_mem_Ioo successesAtMost⟩

/-- Absolute-error transfer and the earlier smoothed-rate affine identity are
checked side by side on the same count. -/
theorem fep123_laplaceAbsoluteError_extends_fep036
    (successes sampleCount : ℕ) (target error : ℝ)
    (sampleCountPositive : 0 < sampleCount)
    (successesAtMost : successes ≤ sampleCount)
    (targetBounds : target ∈ Set.Icc (0 : ℝ) 1)
    (empiricalErrorBound :
      |empiricalRate successes sampleCount - target| ≤ error) :
    (|laplaceEstimate successes sampleCount - target| ≤
      shrinkage sampleCount * error + 1 / ((sampleCount : ℝ) + 2)) ∧
      (fep_fep036.FEP036.fep036_smoothedRate successes sampleCount =
        ((successes : ℝ) / sampleCount) *
            ((sampleCount : ℝ) / (sampleCount + 2)) +
          1 / ((sampleCount : ℝ) + 2)) := by
  exact
    ⟨fep_fep123.FEP123.fep123_laplaceAbsoluteError_le
        successes sampleCount target error sampleCountPositive successesAtMost
        targetBounds empiricalErrorBound,
      fep_fep036.FEP036.fep036_smoothedRate_eq_shrunkEmpirical
        sampleCountPositive⟩

/-- Pointwise squared-error transfer is paired with both the earlier Laplace
affine law and its independent sub-Gaussian finite-sample tail certificate. -/
theorem fep124_laplaceSquaredRisk_combines_fep036_fep114
    {Ω : Type*} [MeasurableSpace Ω]
    (nativeLaw : Measure Ω) {nativeSampleCount : ℕ}
    (observables : Fin nativeSampleCount → Ω → ℝ)
    (independent : iIndepFun observables nativeLaw)
    (proxyVariance : Fin nativeSampleCount → ℝ≥0)
    (subGaussian : ∀ index,
      HasSubgaussianMGF (observables index) (proxyVariance index) nativeLaw)
    {deviation : ℝ} (deviationNonnegative : 0 ≤ deviation)
    (successes sampleCount : ℕ) (target : ℝ)
    (sampleCountPositive : 0 < sampleCount)
    (successesAtMost : successes ≤ sampleCount)
    (targetBounds : target ∈ Set.Icc (0 : ℝ) 1) :
    ((laplaceEstimate successes sampleCount - target) ^ 2 ≤
      2 * shrinkage sampleCount ^ 2 *
          (empiricalRate successes sampleCount - target) ^ 2 +
        2 * (1 / ((sampleCount : ℝ) + 2)) ^ 2) ∧
      ((fep_fep036.FEP036.fep036_smoothedRate successes sampleCount =
        ((successes : ℝ) / sampleCount) *
            ((sampleCount : ℝ) / (sampleCount + 2)) +
          1 / ((sampleCount : ℝ) + 2)) ∧
        nativeLaw.real {outcome |
            (nativeSampleCount : ℝ) * deviation ≤
              ∑ index, observables index outcome} ≤
          Real.exp
            (-((nativeSampleCount : ℝ) * deviation) ^ 2 /
              (2 * ∑ index, proxyVariance index))) := by
  exact
    ⟨fep_fep124.FEP124.fep124_laplaceSquaredError_le
        successes sampleCount target sampleCountPositive successesAtMost
        targetBounds,
      ⟨fep_fep036.FEP036.fep036_smoothedRate_eq_shrunkEmpirical
          sampleCountPositive,
        fep_fep114.FEP114.fep114_subGaussian_empiricalMean_tail
          nativeLaw observables independent proxyVariance subGaussian
          deviationNonnegative⟩⟩

/-- The new excess-risk identity and the earlier proper-score decomposition
are two exact presentations of Bernoulli squared forecast error. -/
theorem fep125_brierExcess_refines_fep022 (target forecast : ℝ) :
    (bernoulliBrierScore target forecast -
        bernoulliBrierScore target target = (forecast - target) ^ 2) ∧
      (fep_fep022.FEP022.fep022_brierScore target forecast =
        target * (1 - target) + (forecast - target) ^ 2) := by
  exact
    ⟨fep_fep125.FEP125.fep125_brierExcess_eq_sqError target forecast,
      fep_fep022.FEP022.fep022_brier_decomposition target forecast⟩

/-- Finite-law Laplace Brier risk is paired with the earlier pointwise Brier
decomposition and Laplace affine identity, without identifying their risk
carriers. -/
theorem fep126_laplaceBrierRisk_combines_fep022_fep036
    {Ω : Type*} [Fintype Ω] (sampling : FiniteLaw Ω)
    (successes : Ω → ℕ) (sampleCount : ℕ) (target : ℝ)
    (sampleCountPositive : 0 < sampleCount)
    (successesAtMost : ∀ outcome, successes outcome ≤ sampleCount)
    (targetBounds : target ∈ Set.Icc (0 : ℝ) 1)
    (selected : Ω) :
    (brierExcessRisk sampling
        (fun outcome => laplaceEstimate (successes outcome) sampleCount) target ≤
      2 * shrinkage sampleCount ^ 2 *
          expectation sampling (fun outcome =>
            (empiricalRate (successes outcome) sampleCount - target) ^ 2) +
        2 * (1 / ((sampleCount : ℝ) + 2)) ^ 2) ∧
      ((fep_fep022.FEP022.fep022_brierScore target
          (laplaceEstimate (successes selected) sampleCount) =
        target * (1 - target) +
          (laplaceEstimate (successes selected) sampleCount - target) ^ 2) ∧
        fep_fep036.FEP036.fep036_smoothedRate
            (successes selected) sampleCount =
          ((successes selected : ℝ) / sampleCount) *
              ((sampleCount : ℝ) / (sampleCount + 2)) +
            1 / ((sampleCount : ℝ) + 2)) := by
  exact
    ⟨fep_fep126.FEP126.fep126_laplaceBrierRisk_le
        sampling successes sampleCount target sampleCountPositive
        successesAtMost targetBounds,
      ⟨fep_fep022.FEP022.fep022_brier_decomposition target
          (laplaceEstimate (successes selected) sampleCount),
        fep_fep036.FEP036.fep036_smoothedRate_eq_shrunkEmpirical
          sampleCountPositive⟩⟩

/-- Smoothed-event containment is paired with the earlier affine Laplace law
and a separate sub-Gaussian tail statement; the conjunction does not promote
either sampling carrier into the other. -/
theorem fep127_laplaceConcentration_combines_fep036_fep114
    {Ω : Type*} [Fintype Ω] [MeasurableSpace Ω]
    (successes : Ω → ℕ) (sampleCount : ℕ)
    (target error : ℝ) (sampleCountPositive : 0 < sampleCount)
    (successesAtMost : ∀ outcome, successes outcome ≤ sampleCount)
    (targetBounds : target ∈ Set.Icc (0 : ℝ) 1) (selected : Ω)
    (nativeLaw : Measure Ω)
    (observables : Fin sampleCount → Ω → ℝ)
    (independent : iIndepFun observables nativeLaw)
    (proxyVariance : Fin sampleCount → ℝ≥0)
    (subGaussian : ∀ index,
      HasSubgaussianMGF (observables index) (proxyVariance index) nativeLaw)
    (deviation : ℝ) (deviationNonnegative : 0 ≤ deviation) :
    (laplaceBadEvent successes sampleCount target error ⊆
      empiricalBadEvent successes sampleCount target error) ∧
      ((fep_fep036.FEP036.fep036_smoothedRate
          (successes selected) sampleCount =
        ((successes selected : ℝ) / sampleCount) *
            ((sampleCount : ℝ) / (sampleCount + 2)) +
          1 / ((sampleCount : ℝ) + 2)) ∧
        nativeLaw.real {outcome |
            (sampleCount : ℝ) * deviation ≤
              ∑ index, observables index outcome} ≤
          Real.exp
            (-((sampleCount : ℝ) * deviation) ^ 2 /
              (2 * ∑ index, proxyVariance index))) := by
  exact
    ⟨fep_fep127.FEP127.fep127_laplaceBadEvent_subset
        successes sampleCount target error sampleCountPositive successesAtMost
        targetBounds,
      ⟨fep_fep036.FEP036.fep036_smoothedRate_eq_shrunkEmpirical
          sampleCountPositive,
        fep_fep114.FEP114.fep114_subGaussian_empiricalMean_tail
          nativeLaw observables independent proxyVariance subGaussian
          deviationNonnegative⟩⟩

end FEPComposed
