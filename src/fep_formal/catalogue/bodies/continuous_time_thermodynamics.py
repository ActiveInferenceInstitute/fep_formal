"""Canonical Lean bodies for exact two-state continuous-time thermodynamics."""

from __future__ import annotations

BODIES: dict[str, str] = {
    "fep-149": """import FepSketches.continuous_time_markov

namespace FEP149

open FEP FEP.ContinuousTimeMarkov Finset
open scoped BigOperators

/-- Every row of the exact two-state transition function has unit mass. -/
theorem fep149_twoStateSemigroup_rowSum
    (rates : TwoStateRates) (time : ℝ) (source : Bool) :
    ∑ target, rates.transition time source target = 1 :=
  rates.transition_rowSum time source

/-- Positive rates and nonnegative time make every entry nonnegative. -/
theorem fep149_twoStateSemigroup_nonnegative
    (rates : TwoStateRates) {time : ℝ} (hTime : 0 ≤ time)
    (source target : Bool) :
    0 ≤ rates.transition time source target :=
  rates.transition_nonneg hTime source target

/-- The plot-ready case uses exactly the requested rates. -/
theorem fep149_benchmarkRates_exact :
    TwoStateRates.benchmarkRates.forward = 0.7 ∧
      TwoStateRates.benchmarkRates.backward = 0.3 :=
  TwoStateRates.benchmarkRates_exact

end FEP149
""",
    "fep-150": """import FepSketches.continuous_time_markov

namespace FEP150

open FEP.ContinuousTimeMarkov

/-- At zero time the exact transition is the identity matrix. -/
theorem fep150_twoStateSemigroup_zero
    (rates : TwoStateRates) (source target : Bool) :
    rates.transition 0 source target = if source = target then 1 else 0 :=
  rates.transition_zero source target

end FEP150
""",
    "fep-151": """import FepSketches.continuous_time_markov

namespace FEP151

open FEP.ContinuousTimeMarkov Finset
open scoped BigOperators

/-- The exact transition function obeys Chapman--Kolmogorov at all real
times; its probability-kernel interpretation uses nonnegative times. -/
theorem fep151_twoStateSemigroup_add
    (rates : TwoStateRates) (left right : ℝ) (source target : Bool) :
    rates.transition (left + right) source target =
      ∑ middle,
        rates.transition left source middle *
          rates.transition right middle target :=
  rates.transition_add left right source target

end FEP151
""",
    "fep-152": """import FepSketches.continuous_time_markov

namespace FEP152

open FEP.ContinuousTimeMarkov Finset
open scoped BigOperators

/-- The exact two-state transition derivative equals both generator products
entrywise. -/
theorem fep152_twoStateSemigroup_hasDerivAt
    (rates : TwoStateRates) (time : ℝ) (source target : Bool) :
    HasDerivAt (fun candidate ↦ rates.transition candidate source target)
        (∑ middle,
          rates.generator source middle * rates.transition time middle target)
        time ∧
      HasDerivAt (fun candidate ↦ rates.transition candidate source target)
        (∑ middle,
          rates.transition time source middle * rates.generator middle target)
        time :=
  rates.transition_masterEquation time source target

end FEP152
""",
    "fep-153": """import FepSketches.continuous_time_markov

namespace FEP153

open FEP FEP.ContinuousTimeMarkov Finset
open scoped BigOperators

/-- The closed-form stationary law is invariant at every time. -/
theorem fep153_twoStateSemigroup_stationary
    (rates : TwoStateRates) (time : ℝ) (target : Bool) :
    (∑ source,
        rates.stationaryLaw source * rates.transition time source target) =
      rates.stationaryLaw target :=
  rates.transition_stationary time target

/-- The same law satisfies entrywise detailed balance. -/
theorem fep153_twoStateSemigroup_detailedBalance
    (rates : TwoStateRates) (time : ℝ) (source target : Bool) :
    rates.stationaryLaw source * rates.transition time source target =
      rates.stationaryLaw target * rates.transition time target source :=
  rates.transition_detailedBalance time source target

end FEP153
""",
    "fep-154": """import FepSketches.continuous_time_markov

namespace FEP154

open FEP FEP.ContinuousTimeMarkov

/-- Every initial two-state law relaxes exactly at rate `a+b`. -/
theorem fep154_twoStateRelaxation_exact
    (rates : TwoStateRates) (initial : FiniteLaw Bool) (time : ℝ) :
    rates.trueMass initial time - rates.stationaryTrue =
      rates.rho time * (initial true - rates.stationaryTrue) :=
  rates.relaxation_exact initial time

/-- The plot-ready initial point mass is genuinely nonstationary. -/
theorem fep154_benchmarkInitial_nonstationary :
    TwoStateRates.benchmarkInitial true ≠
      TwoStateRates.benchmarkRates.stationaryTrue :=
  TwoStateRates.benchmarkInitial_nonstationary

end FEP154
""",
    "fep-155": """import FepSketches.continuous_time_markov

namespace FEP155

open FEP FEP.ContinuousTimeMarkov

/-- Squared deviation from stationarity decays by the exact squared
semigroup factor. -/
theorem fep155_twoStateLyapunov_exact
    (rates : TwoStateRates) (initial : FiniteLaw Bool) (time : ℝ) :
    rates.lyapunov initial time =
      rates.rho time ^ 2 *
        (initial true - rates.stationaryTrue) ^ 2 :=
  rates.lyapunov_exact initial time

/-- Its derivative is exactly `-2(a+b)V(t)`. -/
theorem fep155_twoStateLyapunov_hasDerivAt
    (rates : TwoStateRates) (initial : FiniteLaw Bool) (time : ℝ) :
    HasDerivAt (rates.lyapunov initial)
      (-2 * rates.decayRate * rates.lyapunov initial time) time :=
  rates.lyapunov_hasDerivAt initial time

/-- For rates `(0.7,0.3)` and a nonstationary point mass, the Lyapunov
derivative is strictly negative at time zero. -/
theorem fep155_benchmarkLyapunov_strictlyDecreasing :
    -2 * TwoStateRates.benchmarkRates.decayRate *
        TwoStateRates.benchmarkRates.lyapunov
          TwoStateRates.benchmarkInitial 0 < 0 :=
  TwoStateRates.benchmarkLyapunov_deriv_zero_neg

end FEP155
""",
}
