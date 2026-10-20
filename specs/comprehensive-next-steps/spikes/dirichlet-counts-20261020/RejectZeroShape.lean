import Mathlib.Probability.Distributions.Beta
import Mathlib.Tactic

open MeasureTheory ProbabilityTheory

-- EXPECTED COMPILE FAILURE: the normalized-Beta API requires positive shapes.
-- This tests a missing hypothesis, not that betaMeasure 0 1 has some other property.
example : IsProbabilityMeasure (betaMeasure 0 1) := by
  apply isProbabilityMeasureBeta
  · norm_num
  · norm_num
