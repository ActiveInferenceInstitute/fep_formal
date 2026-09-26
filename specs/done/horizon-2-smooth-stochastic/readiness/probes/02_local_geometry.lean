import Mathlib.Analysis.Calculus.Deriv.Mul
import Mathlib.Geometry.Manifold.Riemannian.Basic
import Mathlib.Geometry.Manifold.VectorBundle.CovariantDerivative.Basic
import Mathlib.Geometry.Manifold.VectorBundle.CovariantDerivative.Metric
import Mathlib.Geometry.Manifold.VectorBundle.CovariantDerivative.Torsion

-- H2-READINESS-ROW: coordinate_duality
example (variance mean : ℝ) (hvariance : 0 < variance) :
    let naturalToMean : ℝ -> ℝ := fun natural => variance * natural
    let meanToNatural : ℝ -> ℝ := fun location => location / variance
    HasDerivAt naturalToMean variance (mean / variance) ∧
      HasDerivAt meanToNatural (1 / variance) mean ∧
      variance * (mean / variance) = mean := by
  dsimp only
  constructor
  · simpa using (hasDerivAt_id (mean / variance)).const_mul variance
  constructor
  · exact (hasDerivAt_id mean).div_const variance
  · field_simp [ne_of_gt hvariance]

-- H2-READINESS-OPTIONAL: riemannian_vector_space
#check IsRiemannianManifold
#check riemannianMetricVectorSpace

-- H2-READINESS-OPTIONAL: covariant_derivative_api
#check IsCovariantDerivativeOn
#check CovariantDerivative

-- H2-READINESS-OPTIONAL: torsion_api
#check IsCovariantDerivativeOn.torsion
#check IsCovariantDerivativeOn.torsion_self

-- H2-READINESS-OPTIONAL: metric_compatibility_api
#check CovariantDerivative.IsMetricCompatible
#check CovariantDerivative.isMetricCompatible_iff

-- H2-READINESS-OPTIONAL: manifold_bundle_packaging
#check IsRiemannianManifold
