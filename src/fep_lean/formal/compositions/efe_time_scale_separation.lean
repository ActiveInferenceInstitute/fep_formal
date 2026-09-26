import FepSketches.fep_all
import FepSketches.efe_time_scale_separation

/-!
# EFE time-scale-separation topic compositions

This bridge pairs the exact epistemic-gain affinity bound with the stationary
invariance of the nearest two-state continuous-time catalogue law.  The
conjunction keeps the information-gap functional and the semigroup stationary
carrier visible on both sides instead of asserting an unproved reduction.
-/

namespace FEPComposed

open FEP.TimeScaleEFE
open FEP FEP.FiniteInformation FEP.ContinuousTimeMarkov FEP.PathThermodynamics
  FEP.ActiveInference FEP.VariationalDuality Finset
open scoped BigOperators

/-- The policy-relevant information-gap bound is paired with the original
two-state stationary-law invariance of the same semigroup carrier; the
finite KL functional and the transition invariance remain distinct laws. -/
theorem fep159_epistemicGain_extends_fep153_stationary
    (rates : TwoStateRates) (belief : FiniteLaw Bool)
    (hSupport : ∀ i, 0 < belief i) (time : ℝ) (target : Bool) :
    (finiteKL belief rates.stationaryLaw ≤
        productionRate rates belief / rates.decayRate) ∧
      ((∑ source,
          rates.stationaryLaw source * rates.transition time source target) =
        rates.stationaryLaw target) := by
  exact
    ⟨fep_fep159.FEP159.fep159_epistemic_gain_bounded_by_affinity
        rates belief hSupport,
      fep_fep153.FEP153.fep153_twoStateSemigroup_stationary
        rates time target⟩

end FEPComposed
