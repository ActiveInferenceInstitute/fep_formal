import Mathlib.MeasureTheory.Measure.LevyConvergence
import Mathlib.MeasureTheory.Measure.ProbabilityMeasure

open Filter MeasureTheory
open scoped BoundedContinuousFunction Topology

-- H2-READINESS-ROW: weak_bounded_continuous
example {μ : ℕ → ProbabilityMeasure ℝ} {μ₀ : ProbabilityMeasure ℝ} :
    Tendsto μ atTop (𝓝 μ₀) ↔
      ∀ f : ℝ →ᵇ ℝ,
        Tendsto (fun n ↦ ∫ x, f x ∂(μ n : Measure ℝ)) atTop
          (𝓝 (∫ x, f x ∂(μ₀ : Measure ℝ))) := by
  exact ProbabilityMeasure.tendsto_iff_forall_integral_tendsto

-- H2-READINESS-ROW: weak_characteristic_function
example {μ : ℕ → ProbabilityMeasure ℝ} {μ₀ : ProbabilityMeasure ℝ} :
    Tendsto μ atTop (𝓝 μ₀) ↔
      ∀ t : ℝ,
        Tendsto (fun n ↦ charFun (μ n) t) atTop
          (𝓝 (charFun μ₀ t)) := by
  exact ProbabilityMeasure.tendsto_iff_tendsto_charFun
