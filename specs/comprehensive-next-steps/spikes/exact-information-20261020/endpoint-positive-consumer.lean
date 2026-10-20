/- Imported current-owner acceptance control. Actual results are recorded separately. -/
import FepSketches.compositions.core
open scoped BigOperators
example : 0 ≤ fep_fep038.FEP038.fep038_fisherMetric (1/2) 1 1 := by
  exact FEPComposed.fep004_fep038_metric_nonneg (by norm_num) (by norm_num) 1
example : 0 ≤ fep_fep026.FEP026.fep026_priorComplexity (1/2) := by
  exact FEPComposed.fep011_fep026_complexity_nonneg (by norm_num) (by norm_num)
example (center x : ℝ) : Filter.Tendsto
    (fun n : ℕ => ((fun y => y-(1/4)*fep_fep043.FEP043.fep043_quadraticGradient 1 center y)^[n]) x)
    Filter.atTop (nhds center) := by
  exact FEPComposed.fep032_fep043_gradient_iteration_tendsto
    (1/4) 1 center x (by norm_num) (by norm_num)
example : fep_fep039.FEP039.fep039_global_fe
    (FEPComposed.fep005_blockEnergy (fun _ => 0) (fun _ => 1)) =
      ∑ _ : Fin 20, (1 : ℝ) := by
  exact FEPComposed.fep039_fep005_partition_conservation_via_cover _ _
#print axioms FEPComposed.fep004_fep038_metric_nonneg
#print axioms FEPComposed.fep011_fep026_complexity_nonneg
#print axioms FEPComposed.fep032_fep043_gradient_iteration_tendsto
#print axioms FEPComposed.fep039_fep005_partition_conservation_via_cover
