/- Imported current-owner acceptance control. Actual results are recorded separately. -/
import FepSketches.compositions.core
example : Filter.Tendsto
    (fun n : ℕ => ((fun y : ℝ => y-0*fep_fep043.FEP043.fep043_quadraticGradient 1 0 y)^[n]) 1)
    Filter.atTop (nhds 0) := by
  exact FEPComposed.fep032_fep043_gradient_iteration_tendsto 0 1 0 1 (by norm_num) (by norm_num)
