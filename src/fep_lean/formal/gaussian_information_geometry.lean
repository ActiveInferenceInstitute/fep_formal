module
public import Mathlib.Analysis.Calculus.Deriv.Mul
public import Mathlib.InformationTheory.KullbackLeibler.Basic
public import Mathlib.Probability.Distributions.Gaussian.Real

@[expose] public section

/-!
# Fixed-variance scalar Gaussian information geometry

This module owns the nondegenerate scalar Gaussian measure family used by the
smooth Horizon 2 lane. Native Kullback--Leibler divergence remains oriented
from the source law to the reference law and valued in `ℝ≥0∞`. Natural and
mean coordinates are kept distinct through their scores and Fisher values.
Zero variance, multivariate laws, and manifold geometry remain outside this
owner.
-/

namespace FEP.GaussianInformationGeometry

open MeasureTheory ProbabilityTheory
open scoped ENNReal MeasureTheory NNReal ProbabilityTheory

noncomputable section

/-- A scalar Gaussian location family with one fixed, strictly positive
variance. The location remains an explicit argument of `law`; normalization,
density, support, and information identities are derived theorems. -/
structure FixedVarianceGaussian where
  variance : ℝ≥0
  variance_pos : 0 < variance

namespace FixedVarianceGaussian

/-- The native Mathlib density of the family member at `mean`. -/
noncomputable def density (family : FixedVarianceGaussian) (mean : ℝ) : ℝ → ℝ≥0∞ :=
  gaussianPDF mean family.variance

/-- The native probability law of the family member at `mean`. -/
noncomputable def law (family : FixedVarianceGaussian) (mean : ℝ) : Measure ℝ :=
  gaussianReal mean family.variance

/-- The family law is definitionally the pinned Mathlib real Gaussian. -/
theorem law_eq_gaussianReal (family : FixedVarianceGaussian) (mean : ℝ) :
    family.law mean = gaussianReal mean family.variance := rfl

/-- Positive variance gives full density support. -/
theorem density_support (family : FixedVarianceGaussian) (mean : ℝ) :
    Function.support (family.density mean) = Set.univ := by
  exact support_gaussianPDF family.variance_pos.ne'

/-- Every family member is volume weighted by its canonical density. -/
theorem law_eq_withDensity (family : FixedVarianceGaussian) (mean : ℝ) :
    family.law mean = volume.withDensity (family.density mean) := by
  exact gaussianReal_of_var_ne_zero mean family.variance_pos.ne'

/-- The canonical density is normalized. -/
theorem density_lintegral_eq_one (family : FixedVarianceGaussian) (mean : ℝ) :
    ∫⁻ x, family.density mean x = 1 := by
  exact lintegral_gaussianPDF_eq_one mean family.variance_pos.ne'

/-- The native family law has unit mass. -/
theorem law_univ (family : FixedVarianceGaussian) (mean : ℝ) :
    family.law mean Set.univ = 1 := by
  simp [law]

/-- The Radon--Nikodym derivative against volume is the canonical density. -/
theorem law_rnDeriv_volume (family : FixedVarianceGaussian) (mean : ℝ) :
    (family.law mean).rnDeriv volume =ᵐ[volume] family.density mean := by
  exact rnDeriv_gaussianReal mean family.variance

/-- Equal positive variance makes every pair of family members mutually
absolutely continuous. -/
theorem law_mutuallyAbsolutelyContinuous
    (family : FixedVarianceGaussian) (sourceMean referenceMean : ℝ) :
    family.law sourceMean ≪ family.law referenceMean ∧
      family.law referenceMean ≪ family.law sourceMean := by
  constructor
  · exact
      (gaussianReal_absolutelyContinuous sourceMean family.variance_pos.ne').trans
        (gaussianReal_absolutelyContinuous' referenceMean family.variance_pos.ne')
  · exact
      (gaussianReal_absolutelyContinuous referenceMean family.variance_pos.ne').trans
        (gaussianReal_absolutelyContinuous' sourceMean family.variance_pos.ne')

private theorem densityReal_ratio
    (family : FixedVarianceGaussian) (sourceMean referenceMean x : ℝ) :
    gaussianPDFReal sourceMean family.variance x /
        gaussianPDFReal referenceMean family.variance x =
      Real.exp
        (((sourceMean - referenceMean) / (family.variance : ℝ)) * x +
          (referenceMean ^ 2 - sourceMean ^ 2) /
            (2 * (family.variance : ℝ))) := by
  rw [gaussianPDFReal_def, gaussianPDFReal_def]
  have hvarianceReal : 0 < (family.variance : ℝ) := by
    exact_mod_cast family.variance_pos
  have hnormalizer :
      (Real.sqrt (2 * Real.pi * (family.variance : ℝ)))⁻¹ ≠ 0 := by
    exact inv_ne_zero (ne_of_gt (Real.sqrt_pos.2 (by positivity)))
  rw [mul_div_mul_left _ _ hnormalizer, ← Real.exp_sub]
  congr 1
  field_simp [family.variance_pos.ne']
  ring

private theorem law_llr
    (family : FixedVarianceGaussian) (sourceMean referenceMean : ℝ) :
    llr (family.law sourceMean) (family.law referenceMean) =ᵐ[family.law sourceMean]
      fun x =>
        ((sourceMean - referenceMean) / (family.variance : ℝ)) * x +
          (referenceMean ^ 2 - sourceMean ^ 2) /
            (2 * (family.variance : ℝ)) := by
  change
    llr (gaussianReal sourceMean family.variance)
        (gaussianReal referenceMean family.variance) =ᵐ[
          gaussianReal sourceMean family.variance]
      fun x =>
        ((sourceMean - referenceMean) / (family.variance : ℝ)) * x +
          (referenceMean ^ 2 - sourceMean ^ 2) /
            (2 * (family.variance : ℝ))
  have hsourceVolume : gaussianReal sourceMean family.variance ≪ volume := by
    exact gaussianReal_absolutelyContinuous sourceMean family.variance_pos.ne'
  have hreferenceVolume : gaussianReal referenceMean family.variance ≪ volume := by
    exact gaussianReal_absolutelyContinuous referenceMean family.variance_pos.ne'
  have hsourceReference :
      gaussianReal sourceMean family.variance ≪
        gaussianReal referenceMean family.variance := by
    simpa [law] using
      (family.law_mutuallyAbsolutelyContinuous sourceMean referenceMean).1
  filter_upwards
    [hsourceReference
      (Measure.rnDeriv_eq_div hsourceVolume hreferenceVolume),
    hsourceVolume (rnDeriv_gaussianReal sourceMean family.variance),
    hsourceVolume (rnDeriv_gaussianReal referenceMean family.variance)] with
      x hratio hsource hreference
  rw [llr, hratio, hsource, hreference, ENNReal.toReal_div,
    toReal_gaussianPDF, toReal_gaussianPDF,
    family.densityReal_ratio sourceMean referenceMean, Real.log_exp]

private theorem law_llr_integrable
    (family : FixedVarianceGaussian) (sourceMean referenceMean : ℝ) :
    Integrable
      (llr (family.law sourceMean) (family.law referenceMean))
      (family.law sourceMean) := by
  change
    Integrable
      (llr (gaussianReal sourceMean family.variance)
        (gaussianReal referenceMean family.variance))
      (gaussianReal sourceMean family.variance)
  have hllr :
      llr (gaussianReal sourceMean family.variance)
          (gaussianReal referenceMean family.variance) =ᵐ[
            gaussianReal sourceMean family.variance]
        fun x =>
          ((sourceMean - referenceMean) / (family.variance : ℝ)) * x +
            (referenceMean ^ 2 - sourceMean ^ 2) /
              (2 * (family.variance : ℝ)) := by
    simpa [law] using family.law_llr sourceMean referenceMean
  rw [integrable_congr hllr]
  have hid : Integrable id (gaussianReal sourceMean family.variance) := by
    exact
      (memLp_id_gaussianReal
        (μ := sourceMean) (v := family.variance) 1).integrable le_rfl
  exact
    (Integrable.const_mul hid
      ((sourceMean - referenceMean) / (family.variance : ℝ))).add
      (integrable_const
        ((referenceMean ^ 2 - sourceMean ^ 2) /
          (2 * (family.variance : ℝ))))

/-- Native KL from the source location to the reference location is the
extended-real embedding of their squared mean displacement divided by twice
the fixed variance. -/
theorem klDiv_law_eq_meanSquare
    (family : FixedVarianceGaussian) (sourceMean referenceMean : ℝ) :
    InformationTheory.klDiv
        (family.law sourceMean)
        (family.law referenceMean) =
      ENNReal.ofReal
        ((sourceMean - referenceMean) ^ 2 /
          (2 * (family.variance : ℝ))) := by
  change
    InformationTheory.klDiv
        (gaussianReal sourceMean family.variance)
        (gaussianReal referenceMean family.variance) =
      ENNReal.ofReal
        ((sourceMean - referenceMean) ^ 2 /
          (2 * (family.variance : ℝ)))
  have hac :
      gaussianReal sourceMean family.variance ≪
        gaussianReal referenceMean family.variance := by
    simpa [law] using
      (family.law_mutuallyAbsolutelyContinuous sourceMean referenceMean).1
  have hintegrable :
      Integrable
        (llr (gaussianReal sourceMean family.variance)
          (gaussianReal referenceMean family.variance))
        (gaussianReal sourceMean family.variance) := by
    simpa [law] using family.law_llr_integrable sourceMean referenceMean
  rw [InformationTheory.klDiv_of_ac_of_integrable hac hintegrable]
  congr 1
  have hllr :
      llr (gaussianReal sourceMean family.variance)
          (gaussianReal referenceMean family.variance) =ᵐ[
            gaussianReal sourceMean family.variance]
        fun x =>
          ((sourceMean - referenceMean) / (family.variance : ℝ)) * x +
            (referenceMean ^ 2 - sourceMean ^ 2) /
              (2 * (family.variance : ℝ)) := by
    simpa [law] using family.law_llr sourceMean referenceMean
  rw [integral_congr_ae hllr]
  have hid : Integrable id (gaussianReal sourceMean family.variance) := by
    exact
      (memLp_id_gaussianReal
        (μ := sourceMean) (v := family.variance) 1).integrable le_rfl
  have hscaled :
      Integrable
        (fun x =>
          ((sourceMean - referenceMean) / (family.variance : ℝ)) * x)
        (gaussianReal sourceMean family.variance) := by
    simpa only [id_eq] using
      Integrable.const_mul hid
        ((sourceMean - referenceMean) / (family.variance : ℝ))
  rw [integral_add hscaled
    (integrable_const
      ((referenceMean ^ 2 - sourceMean ^ 2) /
        (2 * (family.variance : ℝ)))), integral_const_mul]
  simp only [integral_id_gaussianReal]
  simp
  field_simp [family.variance_pos.ne']
  ring

/-- Equal source and reference locations have zero native KL. -/
theorem klDiv_law_self (family : FixedVarianceGaussian) (mean : ℝ) :
    InformationTheory.klDiv (family.law mean) (family.law mean) = 0 := by
  simp [family.klDiv_law_eq_meanSquare]

/-- Distinct source and reference locations have strictly positive native KL. -/
theorem klDiv_law_pos_of_ne
    (family : FixedVarianceGaussian) (sourceMean referenceMean : ℝ)
    (hMeans : sourceMean ≠ referenceMean) :
    0 < InformationTheory.klDiv
      (family.law sourceMean) (family.law referenceMean) := by
  rw [family.klDiv_law_eq_meanSquare, ENNReal.ofReal_pos]
  exact
    div_pos (sq_pos_of_ne_zero (sub_ne_zero.mpr hMeans))
      (mul_pos (by norm_num) family.variance_pos)

/-- The family cannot silently include Mathlib's singular zero-variance branch. -/
theorem zero_variance_excluded :
    ¬ ∃ family : FixedVarianceGaussian, family.variance = 0 := by
  rintro ⟨family, hzero⟩
  exact family.variance_pos.ne' hzero

/-! ## Natural and mean coordinates -/

/-- Convert a mean coordinate to the natural coordinate of the fixed-variance
location family. -/
noncomputable def meanToNatural (family : FixedVarianceGaussian) (mean : ℝ) : ℝ :=
  mean / (family.variance : ℝ)

/-- Convert a natural coordinate to the mean coordinate of the
fixed-variance location family. -/
noncomputable def naturalToMean (family : FixedVarianceGaussian) (natural : ℝ) : ℝ :=
  (family.variance : ℝ) * natural

/-- The natural-coordinate log partition, relative to the zero-mean Gaussian
base law with the same variance. -/
noncomputable def naturalLogPartition
    (family : FixedVarianceGaussian) (natural : ℝ) : ℝ :=
  (family.variance : ℝ) * natural ^ 2 / 2

/-- The natural-coordinate score. -/
noncomputable def naturalScore
    (family : FixedVarianceGaussian) (natural x : ℝ) : ℝ :=
  x - family.naturalToMean natural

/-- The mean-coordinate score. -/
noncomputable def meanScore
    (family : FixedVarianceGaussian) (mean x : ℝ) : ℝ :=
  (x - mean) / (family.variance : ℝ)

/-- Fisher information computed from the natural-coordinate score. -/
noncomputable def naturalFisher
    (family : FixedVarianceGaussian) (natural : ℝ) : ℝ :=
  ∫ x, family.naturalScore natural x ^ 2 ∂family.law (family.naturalToMean natural)

/-- Fisher information computed from the mean-coordinate score. -/
noncomputable def meanFisher
    (family : FixedVarianceGaussian) (mean : ℝ) : ℝ :=
  ∫ x, family.meanScore mean x ^ 2 ∂family.law mean

/-- Natural-coordinate Bregman divergence, oriented to agree with
`klDiv (law source) (law reference)`. -/
noncomputable def naturalBregman
    (family : FixedVarianceGaussian) (sourceNatural referenceNatural : ℝ) : ℝ :=
  family.naturalLogPartition referenceNatural -
    family.naturalLogPartition sourceNatural -
      family.naturalToMean sourceNatural * (referenceNatural - sourceNatural)

/-- Mean-to-natural followed by natural-to-mean is the identity. -/
theorem meanToNatural_naturalToMean
    (family : FixedVarianceGaussian) (mean : ℝ) :
    family.naturalToMean (family.meanToNatural mean) = mean := by
  simp only [naturalToMean, meanToNatural]
  field_simp [family.variance_pos.ne']

/-- Natural-to-mean followed by mean-to-natural is the identity. -/
theorem naturalToMean_meanToNatural
    (family : FixedVarianceGaussian) (natural : ℝ) :
    family.meanToNatural (family.naturalToMean natural) = natural := by
  simp only [meanToNatural, naturalToMean]
  field_simp [family.variance_pos.ne']

/-- The mean-to-natural Jacobian is reciprocal variance. -/
theorem meanToNatural_hasDerivAt
    (family : FixedVarianceGaussian) (mean : ℝ) :
    HasDerivAt family.meanToNatural ((family.variance : ℝ)⁻¹) mean := by
  change
    HasDerivAt (fun candidate => candidate / (family.variance : ℝ))
      ((family.variance : ℝ)⁻¹) mean
  simpa only [Function.id_def, one_div] using
    (hasDerivAt_id mean).div_const (family.variance : ℝ)

/-- The natural log-partition gradient is the mean coordinate. -/
theorem naturalLogPartition_hasDerivAt
    (family : FixedVarianceGaussian) (natural : ℝ) :
    HasDerivAt family.naturalLogPartition
      (family.naturalToMean natural) natural := by
  have hderiv :=
    (((hasDerivAt_id natural).pow 2).const_mul
      (family.variance : ℝ)).div_const 2
  have hderiv' :
      HasDerivAt
        (fun candidate =>
          (family.variance : ℝ) * (id candidate) ^ 2 / 2)
        ((family.variance : ℝ) * natural) natural :=
    hderiv.congr_deriv (by
      norm_num [Function.id_def]
      ring)
  change
    HasDerivAt
      (fun candidate => (family.variance : ℝ) * candidate ^ 2 / 2)
      ((family.variance : ℝ) * natural) natural
  simpa only [Function.id_def] using hderiv'

/-- The derivative of the natural log-partition gradient, hence its second
derivative, is the fixed variance. -/
theorem naturalLogPartitionGradient_hasDerivAt
    (family : FixedVarianceGaussian) (natural : ℝ) :
    HasDerivAt family.naturalToMean (family.variance : ℝ) natural := by
  change
    HasDerivAt (fun candidate => (family.variance : ℝ) * candidate)
      (family.variance : ℝ) natural
  simpa using
    (hasDerivAt_id natural).const_mul (family.variance : ℝ)

/-- The actual Gaussian log-density ratio against the zero-mean base law has
the natural exponential-family form. -/
theorem naturalLogDensityRatio_eq
    (family : FixedVarianceGaussian) (natural x : ℝ) :
    Real.log
        (gaussianPDFReal (family.naturalToMean natural) family.variance x /
          gaussianPDFReal 0 family.variance x) =
      natural * x - family.naturalLogPartition natural := by
  rw [family.densityReal_ratio (family.naturalToMean natural) 0 x,
    Real.log_exp]
  dsimp only [naturalToMean, naturalLogPartition]
  field_simp [family.variance_pos.ne']
  ring

/-- The natural score is the derivative of the actual Gaussian log-density
ratio against the fixed zero-mean base law. -/
theorem naturalScore_is_logDensityRatio_derivative
    (family : FixedVarianceGaussian) (natural x : ℝ) :
    HasDerivAt
      (fun candidate =>
        Real.log
          (gaussianPDFReal (family.naturalToMean candidate) family.variance x /
            gaussianPDFReal 0 family.variance x))
      (family.naturalScore natural x) natural := by
  have hfunction :
      (fun candidate =>
          Real.log
            (gaussianPDFReal (family.naturalToMean candidate) family.variance x /
              gaussianPDFReal 0 family.variance x)) =
        fun candidate => candidate * x - family.naturalLogPartition candidate := by
    funext candidate
    exact family.naturalLogDensityRatio_eq candidate x
  rw [hfunction]
  have hderiv :=
    ((hasDerivAt_id natural).mul_const x).sub
      (family.naturalLogPartition_hasDerivAt natural)
  have hderiv' :
      HasDerivAt
        ((fun candidate => id candidate * x) - family.naturalLogPartition)
        (family.naturalScore natural x) natural :=
    hderiv.congr_deriv (by simp only [naturalScore, one_mul])
  change
    HasDerivAt
      ((fun candidate => candidate * x) - family.naturalLogPartition)
      (family.naturalScore natural x) natural
  simpa only [Function.id_def] using hderiv'

/-- The same actual log-density ratio in the mean coordinate. -/
theorem meanLogDensityRatio_eq
    (family : FixedVarianceGaussian) (mean x : ℝ) :
    Real.log
        (gaussianPDFReal mean family.variance x /
          gaussianPDFReal 0 family.variance x) =
      mean / (family.variance : ℝ) * x -
        mean ^ 2 / (2 * (family.variance : ℝ)) := by
  rw [family.densityReal_ratio mean 0 x, Real.log_exp]
  ring

/-- The mean score is the derivative of the actual Gaussian log-density ratio
against the fixed zero-mean base law. -/
theorem meanScore_is_logDensityRatio_derivative
    (family : FixedVarianceGaussian) (mean x : ℝ) :
    HasDerivAt
      (fun candidate =>
        Real.log
          (gaussianPDFReal candidate family.variance x /
            gaussianPDFReal 0 family.variance x))
      (family.meanScore mean x) mean := by
  have hfunction :
      (fun candidate =>
          Real.log
            (gaussianPDFReal candidate family.variance x /
              gaussianPDFReal 0 family.variance x)) =
        fun candidate =>
          candidate / (family.variance : ℝ) * x -
            candidate ^ 2 / (2 * (family.variance : ℝ)) := by
    funext candidate
    exact family.meanLogDensityRatio_eq candidate x
  rw [hfunction]
  have hlinear :=
    ((hasDerivAt_id mean).div_const (family.variance : ℝ)).mul_const x
  have hquadratic :=
    ((hasDerivAt_id mean).pow 2).div_const
      (2 * (family.variance : ℝ))
  have hderiv := hlinear.sub hquadratic
  have hderiv' :
      HasDerivAt
        ((fun candidate => id candidate / (family.variance : ℝ) * x) -
          fun candidate => (id candidate) ^ 2 / (2 * (family.variance : ℝ)))
        (family.meanScore mean x) mean :=
    hderiv.congr_deriv (by
      norm_num [Function.id_def, meanScore]
      field_simp [family.variance_pos.ne'])
  change
    HasDerivAt
      ((fun candidate => candidate / (family.variance : ℝ) * x) -
        fun candidate => candidate ^ 2 / (2 * (family.variance : ℝ)))
      (family.meanScore mean x) mean
  simpa only [Function.id_def] using hderiv'

/-- The natural-coordinate score is centered under the same Gaussian law. -/
theorem naturalScore_centered
    (family : FixedVarianceGaussian) (natural : ℝ) :
    ∫ x, family.naturalScore natural x ∂family.law (family.naturalToMean natural) = 0 := by
  change
    ∫ x, (x - (family.variance : ℝ) * natural) ∂
      gaussianReal ((family.variance : ℝ) * natural) family.variance = 0
  have hid :
      Integrable id
        (gaussianReal ((family.variance : ℝ) * natural) family.variance) :=
    (memLp_id_gaussianReal
      (μ := (family.variance : ℝ) * natural)
      (v := family.variance) 1).integrable le_rfl
  have hidentity :
      Integrable (fun x : ℝ => x)
        (gaussianReal ((family.variance : ℝ) * natural) family.variance) := by
    simpa only [Function.id_def] using hid
  rw [integral_sub hidentity (integrable_const _), integral_id_gaussianReal]
  simp

/-- The mean-coordinate score is centered under the same Gaussian law. -/
theorem meanScore_centered
    (family : FixedVarianceGaussian) (mean : ℝ) :
    ∫ x, family.meanScore mean x ∂family.law mean = 0 := by
  have hid : Integrable id (gaussianReal mean family.variance) :=
    (memLp_id_gaussianReal
      (μ := mean) (v := family.variance) 1).integrable le_rfl
  change
    ∫ x, (x - mean) / (family.variance : ℝ) ∂
      gaussianReal mean family.variance = 0
  have hidentity :
      Integrable (fun x : ℝ => x) (gaussianReal mean family.variance) := by
    simpa only [Function.id_def] using hid
  rw [integral_div, integral_sub hidentity (integrable_const _),
    integral_id_gaussianReal]
  simp

/-- The law covariance of the identity statistic is the fixed variance. -/
theorem law_variance_eq_fixed
    (family : FixedVarianceGaussian) (mean : ℝ) :
    Var[(fun x : ℝ => x); family.law mean] = (family.variance : ℝ) := by
  simpa only [law] using
    (variance_fun_id_gaussianReal (μ := mean) (v := family.variance))

/-- Natural-coordinate Fisher information is the fixed variance. -/
theorem naturalFisher_eq_variance
    (family : FixedVarianceGaussian) (natural : ℝ) :
    family.naturalFisher natural = (family.variance : ℝ) := by
  have hvariance :=
    variance_fun_id_gaussianReal
      (μ := family.naturalToMean natural) (v := family.variance)
  rw [variance_eq_integral measurable_id'.aemeasurable] at hvariance
  simpa only [naturalFisher, naturalScore, law, integral_id_gaussianReal] using
    hvariance

/-- Natural-coordinate Fisher information equals covariance for the identity
statistic under the same law. -/
theorem naturalFisher_eq_covariance
    (family : FixedVarianceGaussian) (natural : ℝ) :
    family.naturalFisher natural =
      cov[(fun x : ℝ => x), (fun x : ℝ => x);
        family.law (family.naturalToMean natural)] := by
  rw [covariance_self measurable_id'.aemeasurable,
    family.naturalFisher_eq_variance,
    family.law_variance_eq_fixed]

/-- Mean-coordinate Fisher information is reciprocal variance. -/
theorem meanFisher_eq_inv_variance
    (family : FixedVarianceGaussian) (mean : ℝ) :
    family.meanFisher mean = ((family.variance : ℝ)⁻¹) := by
  have hvariance :=
    variance_fun_id_gaussianReal (μ := mean) (v := family.variance)
  rw [variance_eq_integral measurable_id'.aemeasurable] at hvariance
  simp only [integral_id_gaussianReal] at hvariance
  have hfunction :
      (fun x : ℝ => family.meanScore mean x ^ 2) =
        fun x => (1 / (family.variance : ℝ) ^ 2) * (x - mean) ^ 2 := by
    funext x
    simp only [meanScore]
    field_simp [family.variance_pos.ne']
  rw [meanFisher, hfunction, integral_const_mul]
  change
    1 / (family.variance : ℝ) ^ 2 *
        ∫ a, (a - mean) ^ 2 ∂gaussianReal mean family.variance =
      (family.variance : ℝ)⁻¹
  rw [hvariance]
  field_simp [family.variance_pos.ne']

/-- Mean-coordinate Fisher is the pullback of natural-coordinate Fisher by
the reciprocal-variance Jacobian. -/
theorem meanFisher_eq_naturalFisher_pullback
    (family : FixedVarianceGaussian) (mean : ℝ) :
    family.meanFisher mean =
      family.naturalFisher (family.meanToNatural mean) *
        ((family.variance : ℝ)⁻¹) ^ 2 := by
  rw [family.meanFisher_eq_inv_variance,
    family.naturalFisher_eq_variance]
  field_simp [family.variance_pos.ne']

/-- The natural Bregman divergence is the same squared mean displacement used
by the native KL theorem. -/
theorem naturalBregman_eq_meanSquare
    (family : FixedVarianceGaussian) (sourceNatural referenceNatural : ℝ) :
    family.naturalBregman sourceNatural referenceNatural =
      (family.naturalToMean sourceNatural -
          family.naturalToMean referenceNatural) ^ 2 /
        (2 * (family.variance : ℝ)) := by
  simp only [naturalBregman, naturalLogPartition, naturalToMean]
  field_simp [family.variance_pos.ne']
  ring

/-- Native source-to-reference KL equals the oriented natural-coordinate
Bregman divergence. -/
theorem klDiv_law_eq_naturalBregman
    (family : FixedVarianceGaussian) (sourceNatural referenceNatural : ℝ) :
    InformationTheory.klDiv
        (family.law (family.naturalToMean sourceNatural))
        (family.law (family.naturalToMean referenceNatural)) =
      ENNReal.ofReal
        (family.naturalBregman sourceNatural referenceNatural) := by
  rw [family.klDiv_law_eq_meanSquare,
    family.naturalBregman_eq_meanSquare]

/-- Positive fixed variance makes the natural-to-mean map injective. -/
theorem naturalToMean_injective
    (family : FixedVarianceGaussian) : Function.Injective family.naturalToMean := by
  intro left right hequal
  simp only [naturalToMean] at hequal
  exact mul_left_cancel₀ (by exact_mod_cast family.variance_pos.ne') hequal

/-- The fixed-variance Gaussian law is injective in its mean parameter. -/
theorem law_injective
    (family : FixedVarianceGaussian) : Function.Injective family.law := by
  intro sourceMean referenceMean hequal
  change
    gaussianReal sourceMean family.variance =
      gaussianReal referenceMean family.variance at hequal
  exact (gaussianReal_ext_iff.mp hequal).1

end FixedVarianceGaussian

end

end FEP.GaussianInformationGeometry
