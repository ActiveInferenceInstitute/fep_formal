module
public import Mathlib.Algebra.BigOperators.Group.Finset.Basic
public import Mathlib.Algebra.Order.Ring.Basic
public import Mathlib.Analysis.Calculus.Deriv.Add
public import Mathlib.Analysis.Calculus.Deriv.Mul
public import Mathlib.Analysis.Calculus.Deriv.Pow
public import Mathlib.Analysis.Calculus.IteratedDeriv.Defs
public import Mathlib.Analysis.SpecialFunctions.ExpDeriv
public import Mathlib.Basic.Real.Basic
public import Mathlib.Analysis.Convex.SpecificFunctions.Basic
public import Mathlib.Analysis.SpecialFunctions.Log.Deriv
public import Mathlib.Order.Filter.Tendsto
public import Mathlib.Probability.Distributions.Gaussian.Real
public import Mathlib.Topology.Algebra.Monoid
public import Mathlib.Tactic.Convert
public import Mathlib.Tactic.FieldSimp
public import Mathlib.Tactic.Linarith
public import Mathlib.Tactic.NormNum
public import Mathlib.Tactic.Positivity
public import Mathlib.Tactic.Ring
public import Mathlib.Tactic.SimpRw
public meta import Lean.Elab.Tactic.Omega
public meta import Lean.Meta.Tactic.NormCast

@[expose] public section

/-!
# Predictive coding and finite generalized coordinates

The scalar layer proves exact precision-weighted prediction-error identities.
The generalized-coordinate layer uses finitely supported natural-number jets,
so the shift operator has a visible terminal boundary.  The update law is an
explicit Euler correction for a quadratic energy; it does not assert an
analytic infinite jet, a continuous neural flow, or convergence beyond the
stated scalar quadratic model.
-/

namespace FEP.PredictiveCoding

open Finset Filter Topology
open scoped BigOperators

/-! ## Precision-weighted prediction errors -/

/-- Signed sensory prediction error. -/
def predictionError (observation estimate : ℝ) : ℝ :=
  observation - estimate

/-- Half precision-weighted squared prediction error. -/
noncomputable def precisionEnergy (precision observation estimate : ℝ) : ℝ :=
  precision / 2 * predictionError observation estimate ^ 2

/-- Nonnegative precision gives a nonnegative prediction-error energy. -/
theorem precisionEnergy_nonneg {precision : ℝ} (hPrecision : 0 ≤ precision)
    (observation estimate : ℝ) :
    0 ≤ precisionEnergy precision observation estimate := by
  exact mul_nonneg (div_nonneg hPrecision (by norm_num)) (sq_nonneg _)

/-- Under positive precision, zero energy separates the observation from every
distinct estimate. -/
theorem precisionEnergy_eq_zero_iff {precision : ℝ}
    (hPrecision : 0 < precision) (observation estimate : ℝ) :
    precisionEnergy precision observation estimate = 0 ↔
      estimate = observation := by
  constructor
  · intro hzero
    have hsquare : predictionError observation estimate ^ 2 = 0 := by
      have hhalf : 0 < precision / 2 := by positivity
      exact (mul_eq_zero.mp hzero).resolve_left (ne_of_gt hhalf)
    have herr : predictionError observation estimate = 0 :=
      sq_eq_zero_iff.mp hsquare
    exact (sub_eq_zero.mp herr).symm
  · rintro rfl
    simp [precisionEnergy, predictionError]

/-- Positive precision and a nonzero error give strictly positive energy. -/
theorem precisionEnergy_pos {precision : ℝ} (hPrecision : 0 < precision)
    {observation estimate : ℝ} (hError : observation ≠ estimate) :
    0 < precisionEnergy precision observation estimate := by
  have hhalf : 0 < precision / 2 := by positivity
  have hdiff : predictionError observation estimate ≠ 0 := by
    intro hzero
    apply hError
    dsimp [predictionError] at hzero
    linarith
  exact mul_pos hhalf (sq_pos_of_ne_zero hdiff)

/-- The exact derivative with respect to the estimate is minus precision times
the signed prediction error. -/
theorem precisionEnergy_hasDerivAt (precision observation estimate : ℝ) :
    HasDerivAt (fun candidate => precisionEnergy precision observation candidate)
      (-precision * predictionError observation estimate) estimate := by
  convert
    (((hasDerivAt_const estimate observation).sub
      (hasDerivAt_id estimate)).pow 2).const_mul (precision / 2) using 1
  · funext candidate
    rfl
  · simp [predictionError]
    ring

/-- Named gradient of the scalar quadratic energy. -/
def precisionEnergyGradient
    (precision observation estimate : ℝ) : ℝ :=
  -precision * predictionError observation estimate

theorem precisionEnergy_derivative_eq_gradient
    (precision observation estimate : ℝ) :
    HasDerivAt (fun candidate => precisionEnergy precision observation candidate)
      (precisionEnergyGradient precision observation estimate) estimate :=
  precisionEnergy_hasDerivAt precision observation estimate

/-! ## Hierarchical energy -/

/-- Additive precision-weighted energy over a finite hierarchy. -/
noncomputable def hierarchicalEnergy {Level : Type*} [Fintype Level]
    (precision error : Level → ℝ) : ℝ :=
  ∑ level, precision level / 2 * error level ^ 2

theorem hierarchicalEnergy_nonneg
    {Level : Type*} [Fintype Level]
    (precision error : Level → ℝ)
    (hPrecision : ∀ level, 0 ≤ precision level) :
    0 ≤ hierarchicalEnergy precision error := by
  exact Finset.sum_nonneg fun level _ =>
    mul_nonneg (div_nonneg (hPrecision level) (by norm_num))
      (sq_nonneg (error level))

/-- A successor hierarchy decomposes into its zeroth-level energy and the
remaining shifted levels. -/
theorem hierarchicalEnergy_succ {depth : ℕ}
    (precision error : Fin (depth + 1) → ℝ) :
    hierarchicalEnergy precision error =
      precision 0 / 2 * error 0 ^ 2 +
        ∑ level : Fin depth,
          precision level.succ / 2 * error level.succ ^ 2 := by
  exact Fin.sum_univ_succ _

/-- Exact two-level nonvacuity witness with distinct precision and error at
both levels. -/
theorem twoLevelEnergy_witness :
    hierarchicalEnergy
      (fun level : Fin 2 => if level = 0 then 2 else 4)
      (fun level : Fin 2 => if level = 0 then 3 else 1) = 11 := by
  rw [hierarchicalEnergy, Fin.sum_univ_two]
  norm_num

/-! ## Finite generalized-coordinate jets -/

/-- A jet whose coefficients above `order` are definitionally constrained to
zero.  Natural-number indexing makes truncation and repeated shift explicit. -/
@[ext]
structure FiniteJet (order : ℕ) where
  coefficient : ℕ → ℝ
  truncated : ∀ degree, order < degree → coefficient degree = 0

/-- Shift a finite jet by a natural number of generalized-coordinate degrees. -/
def shift {order : ℕ} (steps : ℕ) (jet : FiniteJet order) : FiniteJet order where
  coefficient degree := jet.coefficient (degree + steps)
  truncated degree hDegree := jet.truncated (degree + steps) (by omega)

@[simp]
theorem shift_coefficient {order : ℕ} (steps degree : ℕ)
    (jet : FiniteJet order) :
    (shift steps jet).coefficient degree = jet.coefficient (degree + steps) := rfl

theorem shift_zero {order : ℕ} (jet : FiniteJet order) :
    shift 0 jet = jet := by
  apply FiniteJet.ext
  funext degree
  simp [shift]

/-- Finite shifts form a natural-number semigroup under composition. -/
theorem shift_add {order : ℕ} (first second : ℕ) (jet : FiniteJet order) :
    shift (first + second) jet = shift first (shift second jet) := by
  apply FiniteJet.ext
  funext degree
  simp [shift, Nat.add_assoc]

/-- The one-step shift is zero at the highest retained coordinate; this is the
explicit finite-jet boundary. -/
theorem shift_top_zero {order : ℕ} (jet : FiniteJet order) :
    (shift 1 jet).coefficient order = 0 := by
  change jet.coefficient (order + 1) = 0
  exact jet.truncated (order + 1) (by omega)

/-- The order-`order` jet of `f` at `t`: coordinate `k` is the `k`-th iterated
derivative `iteratedDeriv k f t` for `k ≤ order` and zero above the truncation. -/
noncomputable def functionJet (order : ℕ) (f : ℝ → ℝ) (t : ℝ) : FiniteJet order where
  coefficient k := if k ≤ order then iteratedDeriv k f t else 0
  truncated degree hDegree := by
    simp [show ¬ degree ≤ order by omega]

theorem functionJet_coefficient_of_le {order : ℕ} (f : ℝ → ℝ) (t : ℝ) {k : ℕ}
    (hk : k ≤ order) :
    (functionJet order f t).coefficient k = iteratedDeriv k f t := by
  simp [functionJet, hk]

/-- The one-step shift of the jet of `f` is the jet of `deriv f` on every
coordinate strictly below the truncation order: the shift realizes
differentiation. -/
theorem shift_one_functionJet {order : ℕ} (f : ℝ → ℝ) (t : ℝ) {k : ℕ}
    (hk : k < order) :
    (shift 1 (functionJet order f t)).coefficient k =
      (functionJet order (deriv f) t).coefficient k := by
  rw [shift_coefficient, functionJet_coefficient_of_le f t (by omega),
    functionJet_coefficient_of_le (deriv f) t (by omega), iteratedDeriv_succ']

/-- The `m`-fold shift of the jet of `f` is the jet of the `m`-th iterated
derivative on every coordinate `k` with `k + m ≤ order`. -/
theorem shift_functionJet {order : ℕ} (m : ℕ) (f : ℝ → ℝ) (t : ℝ) {k : ℕ}
    (hk : k + m ≤ order) :
    (shift m (functionJet order f t)).coefficient k =
      (functionJet order (iteratedDeriv m f) t).coefficient k := by
  rw [shift_coefficient, functionJet_coefficient_of_le f t hk,
    functionJet_coefficient_of_le (iteratedDeriv m f) t (by omega),
    iteratedDeriv_eq_iterate, iteratedDeriv_eq_iterate, iteratedDeriv_eq_iterate,
    Function.iterate_add_apply]

/-- The `(m + 1)`-fold shift is the one-step shift of the `m`-fold shift
(semigroup law via `shift_add`). -/
theorem shift_functionJet_succ {order : ℕ} (m : ℕ) (f : ℝ → ℝ) (t : ℝ) (k : ℕ) :
    (shift (m + 1) (functionJet order f t)).coefficient k =
      (shift 1 (shift m (functionJet order f t))).coefficient k := by
  rw [show m + 1 = 1 + m from Nat.add_comm m 1, shift_add]

/-- Truncation boundary: the top coordinate of the shifted jet is zero, while
the jet of `deriv f` keeps the genuine `(order + 1)`-th derivative there. -/
theorem shift_one_functionJet_top {order : ℕ} (f : ℝ → ℝ) (t : ℝ) :
    (shift 1 (functionJet order f t)).coefficient order = 0 ∧
      (functionJet order (deriv f) t).coefficient order =
        iteratedDeriv (order + 1) f t := by
  refine ⟨shift_top_zero _, ?_⟩
  rw [functionJet_coefficient_of_le (deriv f) t le_rfl, iteratedDeriv_succ']

theorem iteratedDeriv_exp_eq (k : ℕ) (t : ℝ) : iteratedDeriv k Real.exp t = Real.exp t := by
  induction k generalizing t with
  | zero => simp
  | succ k ih =>
    rw [iteratedDeriv_succ', Real.deriv_exp]
    exact ih t

/-- Nonvacuous witness: every retained coordinate of the exponential jet is
`exp t ≠ 0`, and the shift agrees with the jet of the derivative (again `exp`)
below the truncation order while the top coordinate of the shift is zero. -/
theorem exp_jet_shift_witness (order : ℕ) (t : ℝ) :
    (∀ k, k ≤ order → (functionJet order Real.exp t).coefficient k ≠ 0) ∧
      (∀ k, k < order →
        (shift 1 (functionJet order Real.exp t)).coefficient k =
          (functionJet order (deriv Real.exp) t).coefficient k) ∧
      (shift 1 (functionJet order Real.exp t)).coefficient order = 0 := by
  refine ⟨fun k hk => ?_, fun k hk => shift_one_functionJet _ t hk, shift_top_zero _⟩
  rw [functionJet_coefficient_of_le _ t hk, iteratedDeriv_exp_eq]
  exact (Real.exp_pos t).ne'

/-- A concrete first-order jet with value and velocity coefficients. -/
def firstOrderJet (value velocity : ℝ) : FiniteJet 1 where
  coefficient degree :=
    if degree = 0 then value else if degree = 1 then velocity else 0
  truncated degree hDegree := by
    simp [show degree ≠ 0 by omega, show degree ≠ 1 by omega]

@[simp]
theorem firstOrderJet_value (value velocity : ℝ) :
    (firstOrderJet value velocity).coefficient 0 = value := by
  simp [firstOrderJet]

@[simp]
theorem firstOrderJet_velocity (value velocity : ℝ) :
    (firstOrderJet value velocity).coefficient 1 = velocity := by
  simp [firstOrderJet]

theorem firstOrderJet_shift_boundary (value velocity : ℝ) :
    (shift 1 (firstOrderJet value velocity)).coefficient 0 = velocity ∧
      (shift 1 (firstOrderJet value velocity)).coefficient 1 = 0 := by
  constructor
  · simp [shift]
  · exact shift_top_zero (firstOrderJet value velocity)

/-! ## Finite-jet generalized filtering -/

/-- The generalized-coordinate flow is the truncated shift minus the exact
quadratic prediction-error gradient at each retained coordinate. -/
def generalizedFlow {order : ℕ} (precision : ℕ → ℝ)
    (target estimate : FiniteJet order) : FiniteJet order where
  coefficient degree :=
    (shift 1 estimate).coefficient degree -
      precisionEnergyGradient (precision degree)
        (target.coefficient degree) (estimate.coefficient degree)
  truncated degree hDegree := by
    rw [(shift 1 estimate).truncated degree hDegree,
      estimate.truncated degree hDegree, target.truncated degree hDegree]
    simp [precisionEnergyGradient, predictionError]

/-- Explicit Euler correction of a finite generalized-coordinate state. -/
def generalizedFilteringStep {order : ℕ} (stepSize : ℝ)
    (precision : ℕ → ℝ) (target estimate : FiniteJet order) :
    FiniteJet order where
  coefficient degree :=
    estimate.coefficient degree +
      stepSize * (generalizedFlow precision target estimate).coefficient degree
  truncated degree hDegree := by
    rw [estimate.truncated degree hDegree,
      (generalizedFlow precision target estimate).truncated degree hDegree]
    ring

/-- The one-step correction equation exposes both the finite shift and the
exact quadratic energy gradient. -/
theorem generalizedFilteringStep_equation {order : ℕ} (stepSize : ℝ)
    (precision : ℕ → ℝ) (target estimate : FiniteJet order)
    (degree : ℕ) :
    (generalizedFilteringStep stepSize precision target estimate).coefficient degree =
      estimate.coefficient degree + stepSize *
        ((shift 1 estimate).coefficient degree -
          precisionEnergyGradient (precision degree)
            (target.coefficient degree) (estimate.coefficient degree)) := rfl

/-- Each correction gradient is backed by an actual `HasDerivAt` theorem. -/
theorem generalizedCoordinateEnergy_hasDerivAt {order : ℕ}
    (precision : ℕ → ℝ) (target estimate : FiniteJet order) (degree : ℕ) :
    HasDerivAt
      (fun candidate =>
        precisionEnergy (precision degree) (target.coefficient degree) candidate)
      (precisionEnergyGradient (precision degree)
        (target.coefficient degree) (estimate.coefficient degree))
      (estimate.coefficient degree) :=
  precisionEnergy_derivative_eq_gradient _ _ _

/-- At the highest retained degree, the generalized shift is exactly zero, so
the terminal correction contains only the negative energy gradient. -/
theorem generalizedFlow_top_boundary {order : ℕ} (precision : ℕ → ℝ)
    (target estimate : FiniteJet order) :
    (generalizedFlow precision target estimate).coefficient order =
      -precisionEnergyGradient (precision order)
        (target.coefficient order) (estimate.coefficient order) := by
  change
    (shift 1 estimate).coefficient order -
        precisionEnergyGradient (precision order)
          (target.coefficient order) (estimate.coefficient order) = _
  rw [shift_top_zero]
  ring

/-- Nontrivial first-order correction: both retained coordinates move, while
the terminal shift contribution is still zero. -/
theorem firstOrderCorrection_witness :
    let corrected := generalizedFilteringStep (1 / 2 : ℝ) (fun _ => 1)
      (firstOrderJet 2 0) (firstOrderJet 0 1)
    corrected.coefficient 0 = 3 / 2 ∧ corrected.coefficient 1 = 1 / 2 := by
  norm_num [generalizedFilteringStep, generalizedFlow,
    precisionEnergyGradient, precisionEnergy, predictionError, shift,
    firstOrderJet]

/-! ## Precision modulation -/

/-- Increasing nonnegative precision cannot decrease the energy assigned to a
fixed prediction error. -/
theorem precisionEnergy_mono {lower upper : ℝ}
    (hLowerNonneg : 0 ≤ lower) (hPrecision : lower ≤ upper)
    (observation estimate : ℝ) :
    0 ≤ precisionEnergy lower observation estimate ∧
      precisionEnergy lower observation estimate ≤
        precisionEnergy upper observation estimate := by
  constructor
  · exact precisionEnergy_nonneg hLowerNonneg observation estimate
  · dsimp [precisionEnergy]
    nlinarith [sq_nonneg (predictionError observation estimate)]

/-- Precision rescaling acts linearly on the quadratic energy. -/
theorem precisionEnergy_scale (scale precision observation estimate : ℝ) :
    precisionEnergy (scale * precision) observation estimate =
      scale * precisionEnergy precision observation estimate := by
  simp [precisionEnergy]
  ring

/-- The exact energy gradient scales linearly with precision. -/
theorem precisionGradient_scale (scale precision observation estimate : ℝ) :
    precisionEnergyGradient (scale * precision) observation estimate =
      scale * precisionEnergyGradient precision observation estimate := by
  simp [precisionEnergyGradient]
  ring

theorem doubledPrecision_nontrivial_witness :
    precisionEnergy 2 1 0 = 2 * precisionEnergy 1 1 0 ∧
      precisionEnergy 1 1 0 < precisionEnergy 2 1 0 := by
  norm_num [precisionEnergy, predictionError]

/-! ## Quadratic predictive-coding convergence -/

/-- One scalar prediction update with learning rate `stepSize`. -/
def predictionUpdate (stepSize target estimate : ℝ) : ℝ :=
  estimate + stepSize * predictionError target estimate

theorem predictionError_update (stepSize target estimate : ℝ) :
    predictionError target (predictionUpdate stepSize target estimate) =
      (1 - stepSize) * predictionError target estimate := by
  simp [predictionError, predictionUpdate]
  ring

/-- One update contracts the quadratic energy by the exact squared factor. -/
theorem predictionEnergy_contraction
    (precision stepSize target estimate : ℝ) :
    precisionEnergy precision target
        (predictionUpdate stepSize target estimate) =
      (1 - stepSize) ^ 2 * precisionEnergy precision target estimate := by
  rw [precisionEnergy, predictionError_update, precisionEnergy]
  ring

/-- Positive precision, a nonzero error, and a step strictly between zero and
two produce strict one-step energy descent. -/
theorem predictionEnergy_strictDecrease {precision stepSize target estimate : ℝ}
    (hPrecision : 0 < precision) (hStepPositive : 0 < stepSize)
    (hStepBelowTwo : stepSize < 2) (hError : target ≠ estimate) :
    precisionEnergy precision target (predictionUpdate stepSize target estimate) <
      precisionEnergy precision target estimate := by
  rw [predictionEnergy_contraction]
  have hEnergy : 0 < precisionEnergy precision target estimate :=
    precisionEnergy_pos hPrecision hError
  have hFactor : (1 - stepSize) ^ 2 < 1 := by
    have hProduct : 0 < stepSize * (2 - stepSize) :=
      mul_pos hStepPositive (sub_pos.mpr hStepBelowTwo)
    nlinarith
  have hScaled := mul_lt_mul_of_pos_right hFactor hEnergy
  simpa using hScaled

/-- Repeated scalar prediction update. -/
def iteratePredictionUpdate (stepSize target : ℝ) : ℕ → ℝ → ℝ
  | 0, estimate => estimate
  | iterations + 1, estimate =>
      predictionUpdate stepSize target
        (iteratePredictionUpdate stepSize target iterations estimate)

/-- Closed-form error after a finite number of quadratic updates. -/
theorem iteratePredictionError
    (stepSize target estimate : ℝ) (iterations : ℕ) :
    predictionError target
        (iteratePredictionUpdate stepSize target iterations estimate) =
      (1 - stepSize) ^ iterations * predictionError target estimate := by
  induction iterations with
  | zero => simp [iteratePredictionUpdate]
  | succ iterations ih =>
      rw [iteratePredictionUpdate, predictionError_update, ih, pow_succ]
      ring

/-- For a learning rate in `(0,2)`, the exact prediction error converges to
zero under repeated quadratic updates. -/
theorem iteratePredictionError_tendsto_zero
    {stepSize : ℝ} (hStepPositive : 0 < stepSize)
    (hStepBelowTwo : stepSize < 2) (target estimate : ℝ) :
    Tendsto
      (fun iterations => predictionError target
        (iteratePredictionUpdate stepSize target iterations estimate))
      atTop (nhds 0) := by
  have hAbs : |1 - stepSize| < 1 :=
    abs_lt.mpr ⟨by linarith, by linarith⟩
  have hPower := tendsto_pow_atTop_nhds_zero_of_abs_lt_one hAbs
  have hScaled := hPower.mul_const (predictionError target estimate)
  have hScaledZero :
      Tendsto
        (fun iterations =>
          (1 - stepSize) ^ iterations * predictionError target estimate)
        atTop (nhds 0) := by
    simpa using hScaled
  exact hScaledZero.congr' (Filter.Eventually.of_forall fun iterations =>
    (iteratePredictionError stepSize target estimate iterations).symm)

/-- The corresponding precision-weighted quadratic energy converges to zero. -/
theorem iteratePredictionEnergy_tendsto_zero
    (precision : ℝ) {stepSize : ℝ} (hStepPositive : 0 < stepSize)
    (hStepBelowTwo : stepSize < 2) (target estimate : ℝ) :
    Tendsto
      (fun iterations => precisionEnergy precision target
        (iteratePredictionUpdate stepSize target iterations estimate))
      atTop (nhds 0) := by
  have hError := iteratePredictionError_tendsto_zero
    hStepPositive hStepBelowTwo target estimate
  simpa [precisionEnergy] using
    (tendsto_const_nhds.mul (hError.pow 2))

/-- Concrete decreasing quadratic witness: a half-step reduces unit energy to
one quarter. -/
theorem halfStep_energy_witness :
    precisionEnergy 2 1 0 = 1 ∧
      predictionUpdate (1 / 2) 1 0 = 1 / 2 ∧
      precisionEnergy 2 1 (predictionUpdate (1 / 2) 1 0) = 1 / 4 := by
  norm_num [precisionEnergy, predictionError, predictionUpdate]

/-! ## Precision as inference -/

/-- Scalar free energy of a precision `precision` given a fixed prediction
error `error`: `precision/2 * error² - log(precision)/2`.  The log term is the
Gaussian normalizer that makes precision an inferred quantity rather than a
free weight. -/
noncomputable def precisionFreeEnergy (error precision : ℝ) : ℝ :=
  precision * error ^ 2 / 2 - Real.log precision / 2

/-- Exact gap to the candidate optimum `1/error²`. -/
theorem precisionFreeEnergy_sub_opt {error : ℝ} (hError : error ≠ 0)
    {precision : ℝ} (hPrecision : 0 < precision) :
    precisionFreeEnergy error precision - precisionFreeEnergy error (1 / error ^ 2) =
      (error ^ 2 * precision - 1 - Real.log (error ^ 2 * precision)) / 2 := by
  have hE : 0 < error ^ 2 := by positivity
  have hLog : Real.log (error ^ 2 * precision) =
      Real.log (error ^ 2) + Real.log precision :=
    Real.log_mul hE.ne' hPrecision.ne'
  have hInv : Real.log (1 / error ^ 2) = -Real.log (error ^ 2) := by
    rw [one_div, Real.log_inv]
  rw [precisionFreeEnergy, precisionFreeEnergy, hInv, hLog]
  field_simp
  ring

/-- The free energy is minimized at `1/error²`. -/
theorem precisionFreeEnergy_min {error : ℝ} (hError : error ≠ 0)
    {precision : ℝ} (hPrecision : 0 < precision) :
    precisionFreeEnergy error (1 / error ^ 2) ≤
      precisionFreeEnergy error precision := by
  have hE : 0 < error ^ 2 := by positivity
  have hGap := precisionFreeEnergy_sub_opt hError hPrecision
  have hLe := Real.log_le_sub_one_of_pos (mul_pos hE hPrecision)
  linarith

/-- The minimizer `1/error²` is unique. -/
theorem precisionFreeEnergy_eq_iff {error : ℝ} (hError : error ≠ 0)
    {precision : ℝ} (hPrecision : 0 < precision) :
    precisionFreeEnergy error precision =
        precisionFreeEnergy error (1 / error ^ 2) ↔
      precision = 1 / error ^ 2 := by
  have hE : 0 < error ^ 2 := by positivity
  have hGap := precisionFreeEnergy_sub_opt hError hPrecision
  have hX : 0 < error ^ 2 * precision := mul_pos hE hPrecision
  constructor
  · intro hEq
    by_contra hNe
    have hX1 : error ^ 2 * precision ≠ 1 := by
      intro h
      apply hNe
      field_simp
      linarith
    have := Real.log_lt_sub_one_of_pos hX hX1
    linarith
  · intro h
    rw [h]

/-- Derivative of the precision free energy in the precision. -/
theorem precisionFreeEnergy_hasDerivAt (error : ℝ) {precision : ℝ}
    (hPrecision : 0 < precision) :
    HasDerivAt (precisionFreeEnergy error)
      (error ^ 2 / 2 - 1 / (2 * precision)) precision := by
  have h1 : HasDerivAt (fun p : ℝ => p * error ^ 2 / 2) (error ^ 2 / 2) precision := by
    simpa using ((hasDerivAt_id precision).mul_const (error ^ 2)).div_const 2
  have h2 := (Real.hasDerivAt_log hPrecision.ne').div_const 2
  have h3 := h1.sub h2
  have hF : precisionFreeEnergy error =
      (fun p : ℝ => p * error ^ 2 / 2) - fun x => Real.log x / 2 := by
    funext p
    simp [precisionFreeEnergy]
  rw [hF]
  convert h3 using 1
  field_simp

/-- The free energy is strictly convex on positive precisions. -/
theorem precisionFreeEnergy_strictConvexOn (error : ℝ) :
    StrictConvexOn ℝ (Set.Ioi 0) (precisionFreeEnergy error) := by
  refine ⟨convex_Ioi 0, fun x hx y hy hxy a b ha hb hab => ?_⟩
  have hLog := strictConcaveOn_log_Ioi.2 hx hy hxy ha hb hab
  simp only [smul_eq_mul, precisionFreeEnergy] at hLog ⊢
  nlinarith [hLog]

/-- Boundary case: with zero prediction error no precision is optimal; the
free energy is unbounded below as precision grows. -/
theorem precisionFreeEnergy_zero_error_unbounded (M : ℝ) :
    ∃ precision : ℝ, 0 < precision ∧ precisionFreeEnergy 0 precision < M := by
  refine ⟨Real.exp (-2 * M + 2), Real.exp_pos _, ?_⟩
  rw [precisionFreeEnergy, Real.log_exp]
  linarith

/-! ## Linear-Gaussian chain: energy equals negative log-density -/

/-- Chain energy: precision-weighted errors minus half the log-precisions. -/
noncomputable def gaussianChainEnergy {Level : Type*} [Fintype Level]
    (precision error : Level → ℝ) : ℝ :=
  hierarchicalEnergy precision error - (∑ level, Real.log (precision level)) / 2

/-- One Gaussian factor: `-log N(x; μ, v)` is the precision-form energy plus
`log(2π)/2`, with precision `1/v`. -/
theorem neg_log_gaussianPDFReal (mean x : ℝ) {variance : NNReal}
    (hVariance : variance ≠ 0) :
    -Real.log (ProbabilityTheory.gaussianPDFReal mean variance x) =
      (1 / (variance : ℝ)) / 2 * (x - mean) ^ 2
        - Real.log (1 / (variance : ℝ)) / 2 + Real.log (2 * Real.pi) / 2 := by
  have hV : 0 < (variance : ℝ) := by
    exact_mod_cast pos_iff_ne_zero.mpr hVariance
  have hPi := Real.pi_pos
  have hArg : 0 < 2 * Real.pi * (variance : ℝ) := by positivity
  have hSqrt : 0 < √(2 * Real.pi * (variance : ℝ)) := Real.sqrt_pos.mpr hArg
  rw [ProbabilityTheory.gaussianPDFReal, Real.log_mul (inv_ne_zero hSqrt.ne')
    (Real.exp_pos _).ne', Real.log_inv, Real.log_exp, Real.log_sqrt hArg.le,
    Real.log_mul (by positivity) hV.ne', one_div, Real.log_inv]
  field_simp
  ring

/-- A hierarchy of independent Gaussian conditionals (explicit means and
variances per level, observed values `x`): the chain energy equals the
negative log of the product of Gaussian densities up to `n/2 · log(2π)`. -/
theorem gaussianChainEnergy_eq_neg_log_prod
    {Level : Type*} [Fintype Level]
    (mean x : Level → ℝ) (variance : Level → NNReal)
    (hVariance : ∀ level, variance level ≠ 0) :
    -Real.log (∏ level, ProbabilityTheory.gaussianPDFReal
        (mean level) (variance level) (x level)) =
      gaussianChainEnergy (fun level => 1 / (variance level : ℝ))
          (fun level => x level - mean level) +
        (Fintype.card Level : ℝ) / 2 * Real.log (2 * Real.pi) := by
  have hNe : ∀ level ∈ (Finset.univ : Finset Level),
      ProbabilityTheory.gaussianPDFReal (mean level) (variance level) (x level) ≠ 0 :=
    fun level _ => (ProbabilityTheory.gaussianPDFReal_pos _ _ _ (hVariance level)).ne'
  rw [Real.log_prod hNe, ← Finset.sum_neg_distrib]
  simp_rw [neg_log_gaussianPDFReal _ _ (hVariance _)]
  rw [gaussianChainEnergy, hierarchicalEnergy, Finset.sum_add_distrib,
    Finset.sum_sub_distrib, ← Finset.sum_div, ← Finset.sum_div]
  simp [Finset.sum_const, Finset.card_univ]
  ring

/-- Two-level instance with explicit means and variances. -/
theorem gaussianChain_twoLevel
    (mean x : Fin 2 → ℝ) (variance : Fin 2 → NNReal)
    (hVariance : ∀ level, variance level ≠ 0) :
    -Real.log (ProbabilityTheory.gaussianPDFReal (mean 0) (variance 0) (x 0) *
        ProbabilityTheory.gaussianPDFReal (mean 1) (variance 1) (x 1)) =
      gaussianChainEnergy (fun level => 1 / (variance level : ℝ))
          (fun level => x level - mean level) + Real.log (2 * Real.pi) := by
  have := gaussianChainEnergy_eq_neg_log_prod mean x variance hVariance
  rw [Fin.prod_univ_two] at this
  rw [this]
  simp

/-- Numeric witness consistent with `twoLevel_energy_witness`: precisions
`2, 4` (variances `1/2, 1/4`) and errors `3, 1` give hierarchical energy `11`
and chain energy `11 - (3/2) log 2`. -/
theorem twoLevel_chain_energy_witness :
    gaussianChainEnergy
      (fun level : Fin 2 => if level = 0 then 2 else 4)
      (fun level : Fin 2 => if level = 0 then 3 else 1) =
        11 - 3 / 2 * Real.log 2 := by
  have h4 : Real.log 4 = 2 * Real.log 2 := by
    rw [show (4 : ℝ) = 2 ^ 2 by norm_num, Real.log_pow]; norm_num
  rw [gaussianChainEnergy, twoLevelEnergy_witness]
  simp [Fin.sum_univ_two, h4]
  ring


end FEP.PredictiveCoding
