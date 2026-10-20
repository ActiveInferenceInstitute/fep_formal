/- Imported current-owner acceptance control. Actual results are recorded separately. -/
import FepSketches.variational_duality
open FEP.VariationalDuality.FairBoolean
example : 0 < interiorMultiplier 0 := by
  exact interiorMultiplier_pos 0 (by norm_num) (by norm_num)
