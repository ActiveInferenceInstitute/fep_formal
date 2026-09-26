import FepSketches.gaussian_information_geometry
import FepSketches.smooth_information_geometry
import FepSketches.compositions.gaussian_filter

/-!
# H2.7-R0: continuous Gaussian VFE and natural-gradient gate

This source-bound spike uses the actual H2.6a evidence density and posterior
law. Its surprisal is a Lebesgue-density quantity, not a singleton-event mass.
Recognition is restricted to the maintained posterior variance family, and
the native KL orientation is recognition-to-posterior.
-/

open MeasureTheory ProbabilityTheory InformationTheory

namespace FEPProbe.H2_7GaussianVFE

open FEP.GaussianInformationGeometry
open FEP.GaussianInformationGeometry.FixedVarianceGaussian
open FEP.SmoothInformationGeometry
open FEPComposed.GaussianFilter

noncomputable section

/-- Evidence surprisal relative to Lebesgue density. -/
noncomputable def evidenceSurprisal
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation : ℝ) : ℝ :=
  -Real.log (evidenceDensity model prior observation).toReal

/-- Continuous Gaussian VFE on recognition means with posterior variance
held fixed. Native KL is oriented recognition-to-posterior. -/
noncomputable def gaussianVariationalFreeEnergy
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation recognitionMean : ℝ) : ℝ :=
  (klDiv
      ((posteriorFamily model prior).law recognitionMean)
      ((posteriorBelief model prior observation).law)).toReal +
    evidenceSurprisal model prior observation

/-- The Fisher-inverse image of the VFE differential in the posterior
mean-coordinate chart. -/
noncomputable def meanNaturalGradient
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation recognitionMean : ℝ) : ℝ :=
  ((posteriorFamily model prior).meanFisher recognitionMean)⁻¹ *
    ((recognitionMean - posteriorMean model prior observation) /
      (posteriorVariance model prior : ℝ))

/-- Local negative-natural-gradient line through a recognition mean. -/
noncomputable def naturalGradientFlow
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation recognitionMean time : ℝ) : ℝ :=
  recognitionMean - time *
    meanNaturalGradient model prior observation recognitionMean

/-- The actual evidence law is Lebesgue measure weighted by the named density. -/
theorem evidenceLaw_eq_volume_withDensity
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief) :
    evidenceLaw model prior = volume.withDensity (evidenceDensity model prior) := by
  rw [evidenceLaw_eq_gaussian]
  exact
    (evidenceFamily model prior).law_eq_withDensity
      (predictionBelief model prior).mean

/-- The selected Gaussian evidence density is finite at every datum. -/
theorem evidenceDensity_ne_top
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation : ℝ) :
    evidenceDensity model prior observation ≠ ⊤ := by
  exact gaussianPDF_ne_top

/-- VFE is the exact Gaussian KL gap plus density-relative surprisal. -/
theorem gaussianVariationalFreeEnergy_eq_meanSquare_add_surprisal
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation recognitionMean : ℝ) :
    gaussianVariationalFreeEnergy model prior observation recognitionMean =
      (recognitionMean - posteriorMean model prior observation) ^ 2 /
          (2 * (posteriorVariance model prior : ℝ)) +
        evidenceSurprisal model prior observation := by
  unfold gaussianVariationalFreeEnergy
  change
    (klDiv
      ((posteriorFamily model prior).law recognitionMean)
      ((posteriorFamily model prior).law
        (posteriorMean model prior observation))).toReal + _ = _
  have hvariance : 0 < (posteriorVariance model prior : ℝ) := by
    exact_mod_cast posteriorVariance_pos model prior
  have hnonneg :
      0 ≤ (recognitionMean - posteriorMean model prior observation) ^ 2 /
        (2 * (posteriorVariance model prior : ℝ)) := by
    exact div_nonneg (sq_nonneg _) (mul_nonneg (by norm_num) hvariance.le)
  rw [(posteriorFamily model prior).klDiv_law_eq_meanSquare]
  change
    (ENNReal.ofReal
      ((recognitionMean - posteriorMean model prior observation) ^ 2 /
        (2 * (posteriorVariance model prior : ℝ)))).toReal + _ = _
  rw [ENNReal.toReal_ofReal hnonneg]

/-- Subtracting evidence surprisal leaves the oriented native
recognition-to-posterior KL in real codomain. -/
theorem gaussianVariationalFreeEnergy_sub_surprisal_eq_nativeKL
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation recognitionMean : ℝ) :
    gaussianVariationalFreeEnergy model prior observation recognitionMean -
        evidenceSurprisal model prior observation =
      (klDiv
        ((posteriorFamily model prior).law recognitionMean)
        ((posteriorBelief model prior observation).law)).toReal := by
  unfold gaussianVariationalFreeEnergy
  ring

/-- Exact-posterior recognition is the unique VFE minimizer within the fixed
posterior-variance Gaussian recognition family. -/
theorem gaussianVariationalFreeEnergy_eq_surprisal_iff
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation recognitionMean : ℝ) :
    gaussianVariationalFreeEnergy model prior observation recognitionMean =
        evidenceSurprisal model prior observation ↔
      recognitionMean = posteriorMean model prior observation := by
  rw [gaussianVariationalFreeEnergy_eq_meanSquare_add_surprisal]
  have hvariance : 0 < (posteriorVariance model prior : ℝ) := by
    exact_mod_cast posteriorVariance_pos model prior
  constructor
  · intro h
    have hgap :
        (recognitionMean - posteriorMean model prior observation) ^ 2 /
            (2 * (posteriorVariance model prior : ℝ)) = 0 := by
      linarith
    field_simp [hvariance.ne'] at hgap
    nlinarith
  · intro h
    simp [h]

/-- The VFE differential is the posterior-precision-weighted mean error. -/
theorem gaussianVariationalFreeEnergy_hasDerivAt
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation recognitionMean : ℝ) :
    HasDerivAt
      (gaussianVariationalFreeEnergy model prior observation)
      ((recognitionMean - posteriorMean model prior observation) /
        (posteriorVariance model prior : ℝ))
      recognitionMean := by
  have hfun :
      gaussianVariationalFreeEnergy model prior observation =
        fun candidate =>
          (candidate - posteriorMean model prior observation) ^ 2 /
              (2 * (posteriorVariance model prior : ℝ)) +
            evidenceSurprisal model prior observation := by
    funext candidate
    exact
      gaussianVariationalFreeEnergy_eq_meanSquare_add_surprisal
        model prior observation candidate
  rw [hfun]
  have hraw :=
    ((((hasDerivAt_id recognitionMean).sub_const
          (posteriorMean model prior observation)).pow 2).div_const
        (2 * (posteriorVariance model prior : ℝ))).add_const
      (evidenceSurprisal model prior observation)
  have hvariance : (posteriorVariance model prior : ℝ) ≠ 0 := by
    exact_mod_cast (posteriorVariance_pos model prior).ne'
  have hderiv :
      (2 : ℝ) *
            (recognitionMean - posteriorMean model prior observation) /
          (2 * (posteriorVariance model prior : ℝ)) =
        (recognitionMean - posteriorMean model prior observation) /
          (posteriorVariance model prior : ℝ) := by
    rw [mul_div_mul_left _ _ (by norm_num : (2 : ℝ) ≠ 0)]
  simpa only [Pi.pow_apply, id_eq, Nat.cast_ofNat, Nat.reduceSub, pow_one,
    mul_one, hderiv] using hraw

/-- Fisher inversion reduces the natural-gradient tangent to the mean
displacement from the exact posterior. -/
theorem meanNaturalGradient_eq_displacement
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation recognitionMean : ℝ) :
    meanNaturalGradient model prior observation recognitionMean =
      recognitionMean - posteriorMean model prior observation := by
  rw [meanNaturalGradient,
    (posteriorFamily model prior).meanFisher_eq_inv_variance]
  change
    ((posteriorVariance model prior : ℝ)⁻¹)⁻¹ *
        ((recognitionMean - posteriorMean model prior observation) /
          (posteriorVariance model prior : ℝ)) = _
  have hvariance : (posteriorVariance model prior : ℝ) ≠ 0 := by
    exact_mod_cast (posteriorVariance_pos model prior).ne'
  field_simp [hvariance]

/-- The derived tangent is metric-dual to the VFE differential. -/
theorem meanNaturalGradient_metric_dual
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation recognitionMean tangent : ℝ) :
    meanMetricPairing (posteriorFamily model prior) recognitionMean
        (meanNaturalGradient model prior observation recognitionMean) tangent =
      ((recognitionMean - posteriorMean model prior observation) /
          (posteriorVariance model prior : ℝ)) * tangent := by
  rw [meanMetricPairing_eq_invVariance,
    meanNaturalGradient_eq_displacement]
  change
    (posteriorVariance model prior : ℝ)⁻¹ *
          (recognitionMean - posteriorMean model prior observation) * tangent =
      ((recognitionMean - posteriorMean model prior observation) /
          (posteriorVariance model prior : ℝ)) * tangent
  ring

/-- The local flow starts at the supplied recognition mean. -/
theorem naturalGradientFlow_zero
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation recognitionMean : ℝ) :
    naturalGradientFlow model prior observation recognitionMean 0 =
      recognitionMean := by
  simp [naturalGradientFlow]

/-- Along the negative natural-gradient line, the VFE time derivative at zero
is minus the squared mean error divided by posterior variance. -/
theorem gaussianVariationalFreeEnergy_naturalGradientFlow_hasDerivAt
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation recognitionMean : ℝ) :
    HasDerivAt
      (fun time =>
        gaussianVariationalFreeEnergy model prior observation
          (naturalGradientFlow model prior observation recognitionMean time))
      (-((recognitionMean - posteriorMean model prior observation) ^ 2 /
        (posteriorVariance model prior : ℝ)))
      0 := by
  have hfun :
      (fun time =>
        gaussianVariationalFreeEnergy model prior observation
          (naturalGradientFlow model prior observation recognitionMean time)) =
        fun time =>
          (recognitionMean -
                time * (recognitionMean - posteriorMean model prior observation) -
              posteriorMean model prior observation) ^ 2 /
              (2 * (posteriorVariance model prior : ℝ)) +
            evidenceSurprisal model prior observation := by
    funext time
    rw [gaussianVariationalFreeEnergy_eq_meanSquare_add_surprisal]
    rw [naturalGradientFlow, meanNaturalGradient_eq_displacement]
  rw [hfun]
  have hinner :
      HasDerivAt
        (fun time : ℝ =>
          recognitionMean -
              time * (recognitionMean - posteriorMean model prior observation) -
            posteriorMean model prior observation)
        (-(recognitionMean - posteriorMean model prior observation)) 0 := by
    simpa only [Pi.sub_apply, Pi.mul_apply, id_eq, one_mul, zero_sub] using
      ((hasDerivAt_const (x := (0 : ℝ)) recognitionMean).sub
        ((hasDerivAt_id (0 : ℝ)).mul_const
          (recognitionMean - posteriorMean model prior observation))).sub_const
            (posteriorMean model prior observation)
  have hraw :=
    ((hinner.pow 2).div_const
      (2 * (posteriorVariance model prior : ℝ))).add_const
        (evidenceSurprisal model prior observation)
  have hvariance : (posteriorVariance model prior : ℝ) ≠ 0 := by
    exact_mod_cast (posteriorVariance_pos model prior).ne'
  have hderiv :
      (2 : ℝ) *
            (recognitionMean -
                0 * (recognitionMean - posteriorMean model prior observation) -
              posteriorMean model prior observation) ^ (2 - 1) *
            (-(recognitionMean - posteriorMean model prior observation)) /
          (2 * (posteriorVariance model prior : ℝ)) =
        -((recognitionMean - posteriorMean model prior observation) ^ 2 /
          (posteriorVariance model prior : ℝ)) := by
    field_simp [hvariance]
    ring
  simpa only [Pi.pow_apply, Nat.cast_ofNat, hderiv] using hraw

/-- Away from the exact posterior mean, the derived negative natural-gradient
flow strictly decreases VFE locally. -/
theorem gaussianVariationalFreeEnergy_naturalGradientFlow_deriv_neg
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation recognitionMean : ℝ)
    (hRecognition :
      recognitionMean ≠ posteriorMean model prior observation) :
    -((recognitionMean - posteriorMean model prior observation) ^ 2 /
        (posteriorVariance model prior : ℝ)) < 0 := by
  have hvariance : 0 < (posteriorVariance model prior : ℝ) := by
    exact_mod_cast posteriorVariance_pos model prior
  exact neg_neg_of_pos
    (div_pos (sq_pos_of_ne_zero (sub_ne_zero.mpr hRecognition)) hvariance)

/-- Combined source-bound boundary: actual evidence density, exact posterior
VFE optimum, metric-dual natural gradient, and strict local descent all share
the maintained H2.6a posterior family. -/
theorem continuousGaussianVFE_naturalGradient
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation recognitionMean tangent : ℝ)
    (hRecognition :
      recognitionMean ≠ posteriorMean model prior observation) :
    evidenceLaw model prior = volume.withDensity (evidenceDensity model prior) ∧
      0 < evidenceDensity model prior observation ∧
      evidenceDensity model prior observation ≠ ⊤ ∧
      gaussianVariationalFreeEnergy model prior observation recognitionMean -
          evidenceSurprisal model prior observation =
        (klDiv
          ((posteriorFamily model prior).law recognitionMean)
          ((posteriorBelief model prior observation).law)).toReal ∧
      (gaussianVariationalFreeEnergy model prior observation recognitionMean =
          evidenceSurprisal model prior observation ↔
        recognitionMean = posteriorMean model prior observation) ∧
      meanNaturalGradient model prior observation recognitionMean =
        recognitionMean - posteriorMean model prior observation ∧
      meanMetricPairing (posteriorFamily model prior) recognitionMean
          (meanNaturalGradient model prior observation recognitionMean) tangent =
        ((recognitionMean - posteriorMean model prior observation) /
            (posteriorVariance model prior : ℝ)) * tangent ∧
      HasDerivAt
        (fun time =>
          gaussianVariationalFreeEnergy model prior observation
            (naturalGradientFlow model prior observation recognitionMean time))
        (-((recognitionMean - posteriorMean model prior observation) ^ 2 /
          (posteriorVariance model prior : ℝ)))
        0 ∧
      -((recognitionMean - posteriorMean model prior observation) ^ 2 /
          (posteriorVariance model prior : ℝ)) < 0 := by
  exact ⟨
    evidenceLaw_eq_volume_withDensity model prior,
    evidenceDensity_pos model prior observation,
    evidenceDensity_ne_top model prior observation,
    gaussianVariationalFreeEnergy_sub_surprisal_eq_nativeKL
      model prior observation recognitionMean,
    gaussianVariationalFreeEnergy_eq_surprisal_iff
      model prior observation recognitionMean,
    meanNaturalGradient_eq_displacement model prior observation recognitionMean,
    meanNaturalGradient_metric_dual
      model prior observation recognitionMean tangent,
    gaussianVariationalFreeEnergy_naturalGradientFlow_hasDerivAt
      model prior observation recognitionMean,
    gaussianVariationalFreeEnergy_naturalGradientFlow_deriv_neg
      model prior observation recognitionMean hRecognition⟩

end

end FEPProbe.H2_7GaussianVFE
