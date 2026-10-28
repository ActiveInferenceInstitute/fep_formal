module
public import FepSketches.gaussian_information_geometry
public import Mathlib.Analysis.Calculus.Deriv.Mul
public import Mathlib.Analysis.Calculus.FDeriv.Pi

@[expose] public section

/-!
# Scalar smooth information geometry

This module derives the local scalar-chart geometry of the accepted
fixed-variance Gaussian family. It owns coordinate metric pairings, one
explicit flat natural/mean duality identity, affine-coordinate paths, and a
rank-deficient duplicated-coordinate countermodel. It introduces no manifold,
connection, tangent-bundle, or curvature hierarchy.
-/

namespace FEP.SmoothInformationGeometry

open FEP.GaussianInformationGeometry
open MeasureTheory ProbabilityTheory
open scoped ENNReal MeasureTheory NNReal ProbabilityTheory

noncomputable section

/-- Scalar Fisher pairing in the natural coordinate. -/
noncomputable def naturalMetricPairing
    (family : FixedVarianceGaussian) (natural left right : ℝ) : ℝ :=
  family.naturalFisher natural * left * right

/-- Scalar Fisher pairing in the mean coordinate. -/
noncomputable def meanMetricPairing
    (family : FixedVarianceGaussian) (mean left right : ℝ) : ℝ :=
  family.meanFisher mean * left * right

/-- An affine path in the natural coordinate. -/
noncomputable def naturalAffinePath (start velocity time : ℝ) : ℝ :=
  start + time * velocity

/-- The Jacobian action of the duplicated mean parameterization. -/
noncomputable def duplicatedMeanJacobian : (Fin 2 → ℝ) →L[ℝ] ℝ :=
  (ContinuousLinearMap.proj 0 : (Fin 2 → ℝ) →L[ℝ] ℝ) +
    (ContinuousLinearMap.proj 1 : (Fin 2 → ℝ) →L[ℝ] ℝ)

/-- A deliberately redundant two-coordinate parameterization of one mean. -/
noncomputable def duplicatedMeanMap (parameter : Fin 2 → ℝ) : ℝ :=
  duplicatedMeanJacobian parameter

/-- Pull back the mean-coordinate Fisher pairing along the duplicated mean
map. -/
noncomputable def duplicatedMeanPullbackMetric
    (family : FixedVarianceGaussian) (parameter : Fin 2 → ℝ)
    (left right : Fin 2 → ℝ) : ℝ :=
  meanMetricPairing family (duplicatedMeanMap parameter)
    (duplicatedMeanJacobian left) (duplicatedMeanJacobian right)

/-- A nonzero tangent annihilated by the duplicated-mean Jacobian. -/
noncomputable def duplicatedNullTangent : Fin 2 → ℝ :=
  fun coordinate => if coordinate = 0 then 1 else -1

/-- The bundled map called the duplicated-mean Jacobian is the actual
Fréchet derivative of the duplicated-coordinate parameterization. -/
theorem duplicatedMeanMap_hasFDerivAt (parameter : Fin 2 → ℝ) :
    HasFDerivAt duplicatedMeanMap duplicatedMeanJacobian parameter := by
  change
    HasFDerivAt (fun candidate => duplicatedMeanJacobian candidate)
      duplicatedMeanJacobian parameter
  exact duplicatedMeanJacobian.hasFDerivAt

/-- The natural-coordinate pairing has variance as its metric component. -/
theorem naturalMetricPairing_eq_variance
    (family : FixedVarianceGaussian) (natural left right : ℝ) :
    naturalMetricPairing family natural left right =
      (family.variance : ℝ) * left * right := by
  rw [naturalMetricPairing, family.naturalFisher_eq_variance]

/-- The mean-coordinate pairing has reciprocal variance as its metric
component. -/
theorem meanMetricPairing_eq_invVariance
    (family : FixedVarianceGaussian) (mean left right : ℝ) :
    meanMetricPairing family mean left right =
      (family.variance : ℝ)⁻¹ * left * right := by
  rw [meanMetricPairing, family.meanFisher_eq_inv_variance]

/-- The mean-coordinate pairing is the natural-coordinate pairing pulled back
by one reciprocal-variance Jacobian factor for each tangent. -/
theorem meanMetricPairing_eq_naturalPullback
    (family : FixedVarianceGaussian) (mean left right : ℝ) :
    meanMetricPairing family mean left right =
      naturalMetricPairing family (family.meanToNatural mean)
        ((family.variance : ℝ)⁻¹ * left)
        ((family.variance : ℝ)⁻¹ * right) := by
  rw [meanMetricPairing_eq_invVariance,
    naturalMetricPairing_eq_variance]
  field_simp [family.variance_pos.ne']

/-- The natural basis and the mean-coordinate basis expressed in natural
coordinates pair to one. -/
theorem naturalMean_coordinateBasis_dual
    (family : FixedVarianceGaussian) (natural : ℝ) :
    naturalMetricPairing family natural 1 (family.variance : ℝ)⁻¹ = 1 := by
  rw [naturalMetricPairing_eq_variance]
  field_simp [family.variance_pos.ne']

/-- On this constant-metric chart, the derivative of the natural/mean dual
pairing is the sum of the pairings with the two flat coordinate derivatives.
This is a coordinate identity, not a bundled connection claim. -/
theorem flatNaturalMean_duality_hasDerivAt
    (family : FixedVarianceGaussian) (time : ℝ)
    (exponentialField mixtureField : ℝ → ℝ)
    (exponentialDerivative mixtureDerivative : ℝ)
    (hExponential : HasDerivAt exponentialField exponentialDerivative time)
    (hMixture : HasDerivAt mixtureField mixtureDerivative time) :
    HasDerivAt
      (fun candidate =>
        naturalMetricPairing family candidate
          (exponentialField candidate)
          ((family.variance : ℝ)⁻¹ * mixtureField candidate))
      (naturalMetricPairing family time exponentialDerivative
          ((family.variance : ℝ)⁻¹ * mixtureField time) +
        naturalMetricPairing family time (exponentialField time)
          ((family.variance : ℝ)⁻¹ * mixtureDerivative)) time := by
  have hpairing :
      (fun candidate =>
          naturalMetricPairing family candidate
            (exponentialField candidate)
            ((family.variance : ℝ)⁻¹ * mixtureField candidate)) =
        fun candidate => exponentialField candidate * mixtureField candidate := by
    funext candidate
    rw [naturalMetricPairing_eq_variance]
    field_simp [family.variance_pos.ne']
  have hderivative :
      naturalMetricPairing family time exponentialDerivative
          ((family.variance : ℝ)⁻¹ * mixtureField time) +
        naturalMetricPairing family time (exponentialField time)
          ((family.variance : ℝ)⁻¹ * mixtureDerivative) =
        exponentialDerivative * mixtureField time +
          exponentialField time * mixtureDerivative := by
    rw [naturalMetricPairing_eq_variance, naturalMetricPairing_eq_variance]
    field_simp [family.variance_pos.ne']
  rw [hpairing]
  rw [hderivative]
  exact hExponential.mul hMixture

/-- The natural-coordinate metric component is constant along its chart. -/
theorem naturalMetricComponent_hasDerivAt_zero
    (family : FixedVarianceGaussian) (natural : ℝ) :
    HasDerivAt family.naturalFisher 0 natural := by
  have hconstant :
      family.naturalFisher = fun _ => (family.variance : ℝ) := by
    funext candidate
    exact family.naturalFisher_eq_variance candidate
  rw [hconstant]
  exact hasDerivAt_const natural (family.variance : ℝ)

/-- The mean-coordinate metric component is constant along its chart. -/
theorem meanMetricComponent_hasDerivAt_zero
    (family : FixedVarianceGaussian) (mean : ℝ) :
    HasDerivAt family.meanFisher 0 mean := by
  have hconstant :
      family.meanFisher = fun _ => (family.variance : ℝ)⁻¹ := by
    funext candidate
    exact family.meanFisher_eq_inv_variance candidate
  rw [hconstant]
  exact hasDerivAt_const mean (family.variance : ℝ)⁻¹

/-- Every explicitly constructed affine natural-coordinate path has constant
velocity. -/
theorem naturalAffinePath_hasDerivAt
    (start velocity time : ℝ) :
    HasDerivAt (naturalAffinePath start velocity) velocity time := by
  change HasDerivAt (fun candidate => start + candidate * velocity) velocity time
  simpa only [Function.id_def, one_mul] using
    ((hasDerivAt_id time).mul_const velocity).const_add start

/-- The velocity field of an affine natural-coordinate path has zero
derivative. -/
theorem naturalAffinePathVelocity_hasDerivAt_zero
    (start velocity time : ℝ) :
    HasDerivAt
      (fun candidate => deriv (naturalAffinePath start velocity) candidate)
      0 time := by
  have hvelocity :
      (fun candidate => deriv (naturalAffinePath start velocity) candidate) =
        fun _ => velocity := by
    funext candidate
    exact (naturalAffinePath_hasDerivAt start velocity candidate).deriv
  rw [hvelocity]
  exact hasDerivAt_const time velocity

/-- Mapping an affine natural-coordinate path into the mean chart preserves
affineness and rescales its velocity by the fixed variance. -/
theorem naturalToMean_naturalAffinePath
    (family : FixedVarianceGaussian) (start velocity time : ℝ) :
    family.naturalToMean (naturalAffinePath start velocity time) =
      naturalAffinePath (family.naturalToMean start)
        ((family.variance : ℝ) * velocity) time := by
  change
    (family.variance : ℝ) * (start + time * velocity) =
      (family.variance : ℝ) * start +
        time * ((family.variance : ℝ) * velocity)
  ring

/-- The H2.1 native KL/Bregman identity is invariant under changing from mean
coordinates to their natural-coordinate images. -/
theorem klDiv_meanCoordinates_eq_naturalBregman
    (family : FixedVarianceGaussian) (sourceMean referenceMean : ℝ) :
    InformationTheory.klDiv
        (family.law sourceMean) (family.law referenceMean) =
      ENNReal.ofReal
        (family.naturalBregman
          (family.meanToNatural sourceMean)
          (family.meanToNatural referenceMean)) := by
  simpa only [family.meanToNatural_naturalToMean] using
    family.klDiv_law_eq_naturalBregman
      (family.meanToNatural sourceMean)
      (family.meanToNatural referenceMean)

/-- The duplicated-mean Jacobian annihilates the selected null tangent. -/
theorem duplicatedMeanJacobian_nullTangent :
    duplicatedMeanJacobian duplicatedNullTangent = 0 := by
  norm_num [duplicatedMeanJacobian, duplicatedNullTangent]

/-- The selected duplicated-coordinate null tangent is nonzero. -/
theorem duplicatedNullTangent_ne_zero : duplicatedNullTangent ≠ 0 := by
  intro hzero
  have hatZero := congrFun hzero (0 : Fin 2)
  norm_num [duplicatedNullTangent] at hatZero

/-- The duplicated-coordinate pullback metric vanishes on a nonzero tangent. -/
theorem duplicatedMeanPullbackMetric_null
    (family : FixedVarianceGaussian) (parameter : Fin 2 → ℝ) :
    duplicatedMeanPullbackMetric family parameter
      duplicatedNullTangent duplicatedNullTangent = 0 := by
  simp only [duplicatedMeanPullbackMetric, meanMetricPairing,
    duplicatedMeanJacobian_nullTangent, mul_zero]

/-- Therefore the duplicated-coordinate pullback is not positive definite,
despite the positive scalar Gaussian Fisher component. -/
theorem duplicatedMeanPullback_not_positiveDefinite
    (family : FixedVarianceGaussian) (parameter : Fin 2 → ℝ) :
    ¬ ∀ tangent : Fin 2 → ℝ, tangent ≠ 0 →
      0 < duplicatedMeanPullbackMetric family parameter tangent tangent := by
  intro hpositive
  have hnull := hpositive duplicatedNullTangent duplicatedNullTangent_ne_zero
  rw [duplicatedMeanPullbackMetric_null family parameter] at hnull
  exact (lt_irrefl 0) hnull

end

end FEP.SmoothInformationGeometry
