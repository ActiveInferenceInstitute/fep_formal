import Mathlib.Probability.BrownianMotion.Basic
import Mathlib.Probability.BrownianMotion.GaussianProjectiveFamily

open MeasureTheory ProbabilityTheory
open scoped NNReal

noncomputable def brownianReadinessTimes : Finset ℝ≥0 := {1, 2}

noncomputable def brownianReadinessTimeOne : brownianReadinessTimes :=
  ⟨1, by simp [brownianReadinessTimes]⟩

noncomputable def brownianReadinessTimeTwo : brownianReadinessTimes :=
  ⟨2, by simp [brownianReadinessTimes]⟩

-- H2-READINESS-OPTIONAL: brownian_finite_dimensional
example :
    cov[fun path => path brownianReadinessTimeOne,
      fun path => path brownianReadinessTimeTwo;
      BrownianReal.projectiveFamily brownianReadinessTimes] = 1 ∧
      MeasurePreserving
        (fun path => path brownianReadinessTimeTwo)
        (BrownianReal.projectiveFamily brownianReadinessTimes)
        (gaussianReal 0 2) ∧
      IsProjectiveMeasureFamily
        (α := fun _ : ℝ≥0 => ℝ) BrownianReal.projectiveFamily := by
  constructor
  · rw [BrownianReal.covariance_eval_projectiveFamily]
    norm_num [brownianReadinessTimeOne, brownianReadinessTimeTwo]
  constructor
  · exact BrownianReal.measurePreserving_eval_projectiveFamily
        brownianReadinessTimeTwo
  · exact BrownianReal.isProjectiveMeasureFamily_projectiveFamily
