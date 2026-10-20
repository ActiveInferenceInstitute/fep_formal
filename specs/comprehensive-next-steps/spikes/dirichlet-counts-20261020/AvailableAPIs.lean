import Mathlib.Analysis.SpecialFunctions.Gamma.Digamma
import Mathlib.Probability.Distributions.Beta
import Mathlib.Geometry.Convex.ConvexSpace.Defs

open MeasureTheory ProbabilityTheory Convexity
open scoped ENNReal

-- Available special function: retain the actual pole-exclusion hypothesis.
theorem available_digamma_recurrence (z : ℂ)
    (hz : ∀ n : ℕ, z ≠ -(n : ℂ)) :
    Complex.digamma (z + 1) = Complex.digamma z + z⁻¹ :=
  Complex.digamma_apply_add_one z hz

-- Available normalized two-shape real distribution, not general Dirichlet.
theorem available_beta_probability {a b : ℝ} (ha : 0 < a) (hb : 0 < b) :
    IsProbabilityMeasure (betaMeasure a b) :=
  isProbabilityMeasureBeta ha hb

theorem available_beta_density_normalizer {a b : ℝ} (ha : 0 < a) (hb : 0 < b) :
    (∫⁻ x, betaPDF a b x) = 1 :=
  lintegral_betaPDF_eq_one ha hb

-- Modern finitely supported simplex; no deprecated stdSimplex alias.
theorem available_simplex_total (w : StdSimplex ℝ (Fin 3)) :
    ∑ i, w.weights i = 1 :=
  StdSimplex.total_of_fintype w

-- Positive boundary control: the chosen Beta density is zero at the endpoint.
theorem beta_density_zero_at_zero (a b : ℝ) : betaPDF a b 0 = 0 :=
  betaPDF_eq_zero_of_nonpos (le_refl 0)

#print axioms available_digamma_recurrence
#print axioms available_beta_probability
#print axioms available_beta_density_normalizer
#print axioms available_simplex_total
#print axioms beta_density_zero_at_zero
