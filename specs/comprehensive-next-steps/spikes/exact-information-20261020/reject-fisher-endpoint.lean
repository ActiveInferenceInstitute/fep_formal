/- Imported current-owner acceptance control. Actual results are recorded separately. -/
import FepSketches.compositions.core
example : 0 ≤ fep_fep038.FEP038.fep038_fisherMetric 1 1 1 := by
  exact FEPComposed.fep004_fep038_metric_nonneg (by norm_num) (by norm_num) 1
