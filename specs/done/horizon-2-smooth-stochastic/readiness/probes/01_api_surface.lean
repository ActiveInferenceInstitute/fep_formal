import Mathlib.Analysis.Normed.Algebra.MatrixExponential
import Mathlib.Geometry.Manifold.Riemannian.Basic
import Mathlib.Geometry.Manifold.VectorBundle.CovariantDerivative.Basic
import Mathlib.MeasureTheory.Measure.LevyConvergence
import Mathlib.Probability.Distributions.Gaussian.Multivariate
import Mathlib.Probability.Distributions.Gaussian.Real
import Mathlib.Probability.Kernel.IonescuTulcea.Traj
import Mathlib.Probability.Kernel.Posterior
import Mathlib.Probability.Martingale.Convergence

open Filter MeasureTheory ProbabilityTheory
open scoped Topology

example : gaussianReal 0 0 = Measure.dirac 0 := by
  exact gaussianReal_zero_var 0

example : IsProbabilityMeasure (gaussianReal 0 1) := by
  infer_instance

example :
    multivariateGaussian (ι := Fin 1) 0 1 =
      stdGaussian (EuclideanSpace ℝ (Fin 1)) := by
  exact multivariateGaussian_zero_one

example {μ : ℕ → ProbabilityMeasure ℝ} {μ₀ : ProbabilityMeasure ℝ} :
    Tendsto μ atTop (𝓝 μ₀) ↔
      ∀ t : ℝ,
        Tendsto (fun n ↦ charFun (μ n) t) atTop (𝓝 (charFun μ₀ t)) := by
  exact ProbabilityMeasure.tendsto_iff_tendsto_charFun
