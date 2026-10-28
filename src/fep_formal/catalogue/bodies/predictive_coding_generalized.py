"""Canonical Lean bodies for predictive coding and generalized coordinates."""

from __future__ import annotations

BODIES: dict[str, str] = {
    "fep-086": """import FepSketches.predictive_coding

namespace FEP086

open FEP.PredictiveCoding

/-- Nonnegative precision produces nonnegative squared prediction-error
energy. -/
theorem fep086_precisionWeighted_predictionError_nonnegative
    {precision : ℝ} (hPrecision : 0 ≤ precision)
    (observation estimate : ℝ) :
    0 ≤ precisionEnergy precision observation estimate :=
  precisionEnergy_nonneg hPrecision observation estimate

/-- At positive precision, zero energy occurs exactly at an exact prediction. -/
theorem fep086_precisionWeighted_zero_iff_exactPrediction
    {precision : ℝ} (hPrecision : 0 < precision)
    (observation estimate : ℝ) :
    precisionEnergy precision observation estimate = 0 ↔
      estimate = observation :=
  precisionEnergy_eq_zero_iff hPrecision observation estimate

/-- Unit prediction error at precision two has exactly unit energy. -/
theorem fep086_unitError_nonvacuity : precisionEnergy 2 1 0 = 1 := by
  norm_num [precisionEnergy, predictionError]

end FEP086
""",
    "fep-087": """import FepSketches.predictive_coding

namespace FEP087

open FEP.PredictiveCoding Finset
open scoped BigOperators

/-- A finite successor hierarchy splits into the zeroth prediction-error
energy and the sum over all higher levels. -/
theorem fep087_hierarchicalPredictiveCoding_decomposition {depth : ℕ}
    (precision error : Fin (depth + 1) → ℝ) :
    hierarchicalEnergy precision error =
      precision 0 / 2 * error 0 ^ 2 +
        ∑ level : Fin depth,
          precision level.succ / 2 * error level.succ ^ 2 :=
  hierarchicalEnergy_succ precision error

/-- Nonnegative precision at every hierarchy level makes the total energy
nonnegative. -/
theorem fep087_hierarchicalPredictiveCoding_nonnegative
    {Level : Type*} [Fintype Level]
    (precision error : Level → ℝ)
    (hPrecision : ∀ level, 0 ≤ precision level) :
    0 ≤ hierarchicalEnergy precision error :=
  hierarchicalEnergy_nonneg precision error hPrecision

/-- Both levels contribute in the concrete energy value eleven. -/
theorem fep087_twoLevel_decomposition_nonvacuity :
    hierarchicalEnergy
      (fun level : Fin 2 => if level = 0 then 2 else 4)
      (fun level : Fin 2 => if level = 0 then 3 else 1) = 11 :=
  twoLevelEnergy_witness

end FEP087
""",
    "fep-088": """import FepSketches.predictive_coding

namespace FEP088

open FEP.PredictiveCoding

/-- The estimate derivative of precision-weighted error energy is exactly
minus precision times signed prediction error. -/
theorem fep088_predictionError_gradient_identity
    (precision observation estimate : ℝ) :
    HasDerivAt (fun candidate => precisionEnergy precision observation candidate)
      (-precision * predictionError observation estimate) estimate :=
  precisionEnergy_hasDerivAt precision observation estimate

/-- The named prediction-error gradient is definitionally the derivative
certified above. -/
theorem fep088_namedGradient_hasDerivAt
    (precision observation estimate : ℝ) :
    HasDerivAt (fun candidate => precisionEnergy precision observation candidate)
      (precisionEnergyGradient precision observation estimate) estimate :=
  precisionEnergy_derivative_eq_gradient precision observation estimate

/-- The gradient is nonzero for a concrete imperfect prediction. -/
theorem fep088_gradient_nonvacuity :
    precisionEnergyGradient 2 1 0 = -2 := by
  norm_num [precisionEnergyGradient, predictionError]

end FEP088
""",
    "fep-089": """import FepSketches.predictive_coding

namespace FEP089

open FEP.PredictiveCoding

/-- Generalized-coordinate shifts form a natural-number semigroup. -/
theorem fep089_finiteJet_shift_semigroup {order : ℕ}
    (first second : ℕ) (jet : FiniteJet order) :
    shift (first + second) jet = shift first (shift second jet) :=
  shift_add first second jet

/-- The highest retained coordinate shifts into the explicitly truncated zero
coefficient. -/
theorem fep089_finiteJet_terminal_boundary {order : ℕ}
    (jet : FiniteJet order) :
    (shift 1 jet).coefficient order = 0 :=
  shift_top_zero jet

/-- A first-order jet shifts velocity into position and exposes zero at its
terminal coordinate. -/
theorem fep089_firstOrder_shift_nonvacuity (value velocity : ℝ) :
    (shift 1 (firstOrderJet value velocity)).coefficient 0 = velocity ∧
      (shift 1 (firstOrderJet value velocity)).coefficient 1 = 0 :=
  firstOrderJet_shift_boundary value velocity

end FEP089
""",
    "fep-090": """import FepSketches.predictive_coding

namespace FEP090

open FEP.PredictiveCoding

/-- One generalized-filtering Euler correction is the current jet plus step
size times truncated shift minus the certified quadratic energy gradient. -/
theorem fep090_finiteJet_generalizedFiltering_correctionEquation
    {order : ℕ} (stepSize : ℝ) (precision : ℕ → ℝ)
    (target estimate : FiniteJet order) (degree : ℕ) :
    (generalizedFilteringStep stepSize precision target estimate).coefficient degree =
      estimate.coefficient degree + stepSize *
        ((shift 1 estimate).coefficient degree -
          precisionEnergyGradient (precision degree)
            (target.coefficient degree) (estimate.coefficient degree)) :=
  generalizedFilteringStep_equation stepSize precision target estimate degree

/-- The correction's pointwise gradient is backed by an exact derivative
statement rather than a symbolic placeholder. -/
theorem fep090_finiteJet_coordinateGradient_hasDerivAt
    {order : ℕ} (precision : ℕ → ℝ)
    (target estimate : FiniteJet order) (degree : ℕ) :
    HasDerivAt
      (fun candidate =>
        precisionEnergy (precision degree) (target.coefficient degree) candidate)
      (precisionEnergyGradient (precision degree)
        (target.coefficient degree) (estimate.coefficient degree))
      (estimate.coefficient degree) :=
  generalizedCoordinateEnergy_hasDerivAt precision target estimate degree

/-- At the top finite coordinate the shift term is exactly absent. -/
theorem fep090_finiteJet_truncation_visible
    {order : ℕ} (precision : ℕ → ℝ)
    (target estimate : FiniteJet order) :
    (generalizedFlow precision target estimate).coefficient order =
      -precisionEnergyGradient (precision order)
        (target.coefficient order) (estimate.coefficient order) :=
  generalizedFlow_top_boundary precision target estimate

/-- Both coordinates of a concrete first-order jet receive nonzero, exact
corrections. -/
theorem fep090_firstOrder_correction_nonvacuity :
    let corrected := generalizedFilteringStep (1 / 2 : ℝ) (fun _ => 1)
      (firstOrderJet 2 0) (firstOrderJet 0 1)
    corrected.coefficient 0 = 3 / 2 ∧ corrected.coefficient 1 = 1 / 2 :=
  firstOrderCorrection_witness

end FEP090
""",
    "fep-091": """import FepSketches.predictive_coding

namespace FEP091

open FEP.PredictiveCoding

/-- Greater precision cannot lower the energy of a fixed prediction error. -/
theorem fep091_precisionModulation_energy_mono
    {lower upper : ℝ} (hLowerNonneg : 0 ≤ lower)
    (hPrecision : lower ≤ upper)
    (observation estimate : ℝ) :
    0 ≤ precisionEnergy lower observation estimate ∧
      precisionEnergy lower observation estimate ≤
        precisionEnergy upper observation estimate :=
  precisionEnergy_mono hLowerNonneg hPrecision observation estimate

/-- Scaling precision scales the exact prediction-error gradient by the same
factor. -/
theorem fep091_precisionModulation_gradient_scale
    (scale precision observation estimate : ℝ) :
    precisionEnergyGradient (scale * precision) observation estimate =
      scale * precisionEnergyGradient precision observation estimate :=
  precisionGradient_scale scale precision observation estimate

/-- Doubling precision strictly increases the energy of one concrete nonzero
error. -/
theorem fep091_doubledPrecision_nonvacuity :
    precisionEnergy 2 1 0 = 2 * precisionEnergy 1 1 0 ∧
      precisionEnergy 1 1 0 < precisionEnergy 2 1 0 :=
  doubledPrecision_nontrivial_witness

end FEP091
""",
    "fep-092": """import FepSketches.predictive_coding

namespace FEP092

open FEP.PredictiveCoding Filter Topology

/-- Each quadratic prediction update contracts energy by the exact squared
factor `(1-stepSize)^2`. -/
theorem fep092_quadraticPredictiveCoding_contraction
    (precision stepSize target estimate : ℝ) :
    precisionEnergy precision target
        (predictionUpdate stepSize target estimate) =
      (1 - stepSize) ^ 2 * precisionEnergy precision target estimate :=
  predictionEnergy_contraction precision stepSize target estimate

/-- Positive precision and a nonzero error give strict descent for every step
size strictly between zero and two. -/
theorem fep092_quadraticPredictiveCoding_strictDecrease
    {precision stepSize target estimate : ℝ}
    (hPrecision : 0 < precision) (hStepPositive : 0 < stepSize)
    (hStepBelowTwo : stepSize < 2) (hError : target ≠ estimate) :
    precisionEnergy precision target (predictionUpdate stepSize target estimate) <
      precisionEnergy precision target estimate :=
  predictionEnergy_strictDecrease hPrecision hStepPositive hStepBelowTwo hError

/-- Under the same step-size boundary, repeated exact prediction error
converges to zero. -/
theorem fep092_quadraticPredictiveCoding_error_tendsto_zero
    {stepSize : ℝ} (hStepPositive : 0 < stepSize)
    (hStepBelowTwo : stepSize < 2) (target estimate : ℝ) :
    Tendsto
      (fun iterations => predictionError target
        (iteratePredictionUpdate stepSize target iterations estimate))
      atTop (nhds 0) :=
  iteratePredictionError_tendsto_zero
    hStepPositive hStepBelowTwo target estimate

/-- A half-step reduces a concrete unit energy to one quarter. -/
theorem fep092_halfStep_decrease_nonvacuity :
    precisionEnergy 2 1 0 = 1 ∧
      predictionUpdate (1 / 2) 1 0 = 1 / 2 ∧
      precisionEnergy 2 1 (predictionUpdate (1 / 2) 1 0) = 1 / 4 :=
  halfStep_energy_witness

end FEP092
""",
}
