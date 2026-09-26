import FepSketches.continuous_time_markov
import FepSketches.path_thermodynamics
import FepSketches.active_inference
import FepSketches.ness_flow

/-!
# EFE ↔ entropy-production time-scale separation

This module ties the policy-relevant epistemic (information) gain of the
expected-free-energy stack to the Markov semigroup's entropy-production
machinery on the two-state carrier.

## Main results

| theorem | meaning |
|---------|---------|
| `epistemic_gain_bounded_by_affinity` | the belief information gap `finiteKL belief stationaryLaw` is at most the entropy-production rate `σ = J * A` scaled by the relaxation time `1 / decayRate` |
| `expectedFreeEnergy_le_productionRate_div_decayRate` | the same bound for the actual `expectedFreeEnergy` of the two-state observing agent |
| `slow_fast_separation_statement` | the evolved gain is bounded by the squared relaxation factor `rho time ^ 2` and by the initial gap: policy-relevant information contracts to the invariant measure no slower than the relaxation timescale |
| `fastRelaxation_epistemic_vanishes` | under the `1 / eps` rate scaling the gain after a fixed positive action time vanishes as `eps → 0⁺` |
| `slicePath_entropyProduction_eq` | the one-slice path-space entropy production of `FEP.PathThermodynamics` equals `(1 - rho time) * σ / decayRate`, so `σ` is the generator production rate of the anchored path machinery |

## Scope discipline

* The bridge quantity is the **belief information gap** `finiteKL belief
  stationaryLaw` — exactly the information functional the semigroup
  contracts.  The mutual-information form `epistemicValue` of
  `FEP.ActiveInference` is a different functional: at a stationary belief the
  gap is zero while the MI form can reach `log 2` (a fully informative
  likelihood), so no universal `epistemicValue ≤ σ / decayRate` exists.  The
  bridge is therefore stated for the information gap; in the two-state
  observing model below the expected free energy coincides with it exactly.
* Entropy production is the classical two-state rate `σ = J * A` with `J` the
  generator current and `A` the log-affinity;
  `beliefAffinity_eq_localAffinity` grounds `A` in
  `FEP.PathThermodynamics.localAffinity`.
* Carriers stay decidable and finite (`Bool`); every rate or scaling
  hypothesis is explicit.  No new axioms, no proof placeholders, no
  `native_decide`.
* `FepSketches.ness_flow` is imported as its first consumer (orphan adoption
  marker); no mathematical dependence on it is used or claimed.
* This file is rostered in the formal resource manifest and is imported by the
  generated `fep_all.lean`; its catalogue topics are bridged from
  `formal/compositions/efe_time_scale_separation.lean`.
-/

namespace FEP.TimeScaleEFE

open FEP FEP.FiniteInformation FEP.ContinuousTimeMarkov FEP.PathThermodynamics
  FEP.ActiveInference FEP.VariationalDuality Finset
open scoped BigOperators

/-! ## Two-state helpers -/

/-- Stationary masses sum to one in `true`-first order. -/
theorem stationaryTrue_add_stationaryFalse (rates : TwoStateRates) :
    rates.stationaryTrue + rates.stationaryFalse = 1 := by
  have h := rates.stationary_sum_one
  linarith

/-- The invariant law assigns `stationaryTrue` to `true`. -/
theorem stationaryLaw_true (rates : TwoStateRates) :
    rates.stationaryLaw true = rates.stationaryTrue := rfl

/-- The invariant law assigns `stationaryFalse` to `false`. -/
theorem stationaryLaw_false (rates : TwoStateRates) :
    rates.stationaryLaw false = rates.stationaryFalse := rfl

/-- The invariant law has full support. -/
theorem stationaryLaw_pos (rates : TwoStateRates) (i : Bool) :
    0 < rates.stationaryLaw i := by
  cases i
  · rw [stationaryLaw_false]
    exact rates.stationaryFalse_pos
  · rw [stationaryLaw_true]
    exact rates.stationaryTrue_pos

/-- Boolean belief masses sum to one. -/
theorem belief_sum_one (belief : FiniteLaw Bool) :
    belief false + belief true = 1 := by
  simpa [Fintype.sum_bool, add_comm] using belief.sum_one

/-- The relaxation factor is strictly below one at a positive time. -/
theorem rho_lt_one (rates : TwoStateRates) {time : ℝ} (hpos : 0 < time) :
    rates.rho time < 1 := by
  rw [TwoStateRates.rho, Real.exp_lt_one_iff]
  have hdt : 0 < rates.decayRate * time := mul_pos rates.decayRate_pos hpos
  linarith

/-- Closed form of the `false → true` transition entry. -/
theorem transition_false_true (rates : TwoStateRates) (time : ℝ) :
    rates.transition time false true = rates.stationaryTrue * (1 - rates.rho time) := rfl

/-- Closed form of the `true → false` transition entry. -/
theorem transition_true_false (rates : TwoStateRates) (time : ℝ) :
    rates.transition time true false = rates.stationaryFalse * (1 - rates.rho time) := rfl

/-- Closed form of the `false → false` transition entry. -/
theorem transition_false_false (rates : TwoStateRates) (time : ℝ) :
    rates.transition time false false =
      rates.stationaryFalse + rates.stationaryTrue * rates.rho time := rfl

/-- Closed form of the `true → true` transition entry. -/
theorem transition_true_true (rates : TwoStateRates) (time : ℝ) :
    rates.transition time true true =
      rates.stationaryTrue + rates.stationaryFalse * rates.rho time := rfl

/-- Diagonal transition entries are strictly positive. -/
theorem transition_diagonal_pos (rates : TwoStateRates) (time : ℝ) (i : Bool) :
    0 < rates.transition time i i := by
  have hρ : 0 < rates.rho time := rates.rho_pos time
  cases i
  · rw [transition_false_false]
    exact add_pos rates.stationaryFalse_pos (mul_pos rates.stationaryTrue_pos hρ)
  · rw [transition_true_true]
    exact add_pos rates.stationaryTrue_pos (mul_pos rates.stationaryFalse_pos hρ)

/-- At a positive time every transition entry is strictly positive. -/
theorem transition_fullSupport_pos (rates : TwoStateRates) (time : ℝ)
    (_hTime : 0 ≤ time) (hpos : 0 < time) (s t : Bool) :
    0 < rates.transition time s t := by
  have hρ1 : rates.rho time < 1 := rho_lt_one rates hpos
  cases s <;> cases t
  · exact transition_diagonal_pos rates time false
  · rw [transition_false_true]
    exact mul_pos rates.stationaryTrue_pos (sub_pos.mpr hρ1)
  · rw [transition_true_false]
    exact mul_pos rates.stationaryFalse_pos (sub_pos.mpr hρ1)
  · exact transition_diagonal_pos rates time true

/-- Predictive mass keeps the support of a fully supported belief whenever
the kernel's diagonal is strictly positive. -/
theorem predictive_support_of (kernel : FiniteKernel Bool Bool)
    (belief : FiniteLaw Bool) (hSupport : ∀ i, 0 < belief i)
    (hDiag : ∀ i, 0 < kernel i i) (i : Bool) :
    0 < kernel.predictive belief i := by
  rw [FiniteKernel.predictive_mass]
  cases i
  · calc 0 < belief false * kernel false false := mul_pos (hSupport false) (hDiag false)
      _ ≤ belief false * kernel false false + belief true * kernel true false :=
          le_add_of_nonneg_right
            (mul_nonneg (belief.nonneg true) (kernel.nonneg true false))
      _ = ∑ x, belief x * kernel x false := by
          rw [Fintype.sum_bool, add_comm]
  · calc 0 < belief true * kernel true true := mul_pos (hSupport true) (hDiag true)
      _ ≤ belief true * kernel true true + belief false * kernel false true :=
          le_add_of_nonneg_right
            (mul_nonneg (belief.nonneg false) (kernel.nonneg false true))
      _ = ∑ x, belief x * kernel x true := by
          rw [Fintype.sum_bool]

/-! ## Generator current, affinity, and entropy-production rate -/

/-- Oriented probability current through the two-state generator at `belief`:
`J = belief false * forward - belief true * backward`. -/
def beliefCurrent (rates : TwoStateRates) (belief : FiniteLaw Bool) : ℝ :=
  belief false * rates.forward - belief true * rates.backward

/-- Log-affinity of the generator edge `false → true` at `belief`.  At a zero
mass Lean's totalized logarithm is exposed as a boundary value; the bridging
theorems below assume full belief support. -/
noncomputable def beliefAffinity (rates : TwoStateRates) (belief : FiniteLaw Bool) : ℝ :=
  Real.log (belief false * rates.forward / (belief true * rates.backward))

/-- Entropy-production rate at `belief`: the classical two-state Markov-jump
rate `σ = J * A`. -/
noncomputable def productionRate (rates : TwoStateRates) (belief : FiniteLaw Bool) : ℝ :=
  beliefCurrent rates belief * beliefAffinity rates belief

/-- The current is the relaxation rate times the signed distance of the true
mass from stationarity. -/
theorem beliefCurrent_eq (rates : TwoStateRates) (belief : FiniteLaw Bool) :
    beliefCurrent rates belief =
      rates.decayRate * (rates.stationaryTrue - belief true) := by
  have hEq : belief false = 1 - belief true := by
    linarith [belief_sum_one belief]
  rw [beliefCurrent, hEq, ← rates.stationaryTrue_mul_decayRate,
    ← rates.stationaryFalse_mul_decayRate]
  have hEq2 : belief true * (rates.stationaryFalse + rates.stationaryTrue) =
      belief true := by
    rw [rates.stationary_sum_one, mul_one]
  calc (1 - belief true) * (rates.stationaryTrue * rates.decayRate) -
        belief true * (rates.stationaryFalse * rates.decayRate)
      = rates.decayRate *
          (rates.stationaryTrue -
            belief true * (rates.stationaryFalse + rates.stationaryTrue)) := by
        ring
    _ = rates.decayRate * (rates.stationaryTrue - belief true) := by
        rw [hEq2]

/-- The generator affinity coincides with `FEP.PathThermodynamics.localAffinity`
of the semigroup slice at every positive sampling time. -/
theorem beliefAffinity_eq_localAffinity (rates : TwoStateRates)
    (belief : FiniteLaw Bool) (hSupport : ∀ i, 0 < belief i)
    (time : ℝ) (hTime : 0 < time) :
    beliefAffinity rates belief =
      localAffinity belief (rates.certifiedSemigroup.kernel time hTime.le) false true := by
  have hρ1 : rates.rho time < 1 := rho_lt_one rates hTime
  have hEq : belief false * rates.forward / (belief true * rates.backward) =
      belief false * (rates.stationaryTrue * (1 - rates.rho time)) /
        (belief true * (rates.stationaryFalse * (1 - rates.rho time))) := by
    rw [← rates.stationaryTrue_mul_decayRate, ← rates.stationaryFalse_mul_decayRate]
    field_simp [ne_of_gt (hSupport true), rates.stationaryFalse_pos.ne,
      ne_of_gt rates.decayRate_pos,
      ne_of_gt (show 0 < 1 - rates.rho time by linarith)]
  rw [beliefAffinity, localAffinity]
  change Real.log (belief false * rates.forward / (belief true * rates.backward)) =
    Real.log ((belief false * rates.transition time false true) /
      (belief true * rates.transition time true false))
  rw [transition_false_true, transition_true_false, hEq]

/-- The entropy-production rate is nonnegative at a fully supported belief. -/
theorem productionRate_nonneg (rates : TwoStateRates) (belief : FiniteLaw Bool)
    (hSupport : ∀ i, 0 < belief i) : 0 ≤ productionRate rates belief := by
  have hJ : belief false * rates.forward - belief true * rates.backward =
      rates.decayRate * (rates.stationaryTrue - belief true) :=
    beliefCurrent_eq rates belief
  rcases le_or_gt (belief true) rates.stationaryTrue with hle | hgt
  · have hJpos : 0 ≤ belief false * rates.forward - belief true * rates.backward := by
      rw [hJ]
      exact mul_nonneg rates.decayRate_pos.le (sub_nonneg.mpr hle)
    have hApos : 0 ≤ beliefAffinity rates belief := by
      have h1 : 1 ≤ belief false * rates.forward / (belief true * rates.backward) := by
        rw [one_le_div (mul_pos (hSupport true) rates.backward_pos)]
        linarith [hJpos]
      exact Real.log_nonneg h1
    exact mul_nonneg hJpos hApos
  · have hJneg : belief false * rates.forward - belief true * rates.backward ≤ 0 := by
      rw [hJ]
      exact mul_nonpos_of_nonneg_of_nonpos rates.decayRate_pos.le (sub_nonpos.mpr hgt.le)
    have hAneg : beliefAffinity rates belief ≤ 0 := by
      have h1 : belief false * rates.forward / (belief true * rates.backward) ≤ 1 := by
        rw [div_le_one (mul_pos (hSupport true) rates.backward_pos)]
        linarith [hJneg]
      exact Real.log_nonpos
        (div_nonneg (mul_pos (hSupport false) rates.forward_pos).le
          (mul_pos (hSupport true) rates.backward_pos).le) h1
    have hfact : productionRate rates belief =
        -(beliefCurrent rates belief) * -(beliefAffinity rates belief) := by
      rw [productionRate]; ring
    rw [hfact]
    exact mul_nonneg (neg_nonneg.mpr hJneg) (neg_nonneg.mpr hAneg)

/-! ## Policy-relevant epistemic gain and theorem 1 -/

/-- Policy-relevant epistemic gain of acting for `time`: the information gap
of the semigroup-evolved belief against the invariant law. -/
noncomputable def epistemicGain (rates : TwoStateRates) (belief : FiniteLaw Bool)
    (time : ℝ) (hTime : 0 ≤ time) : ℝ :=
  finiteKL ((rates.certifiedSemigroup.kernel time hTime).predictive belief)
    rates.stationaryLaw

/-- Expanded logarithmic form of the belief information gap. -/
theorem finiteKL_stationaryLaw_eq (rates : TwoStateRates) (belief : FiniteLaw Bool) :
    finiteKL belief rates.stationaryLaw =
      belief false * (Real.log (belief false) - Real.log (rates.stationaryFalse)) +
        belief true * (Real.log (belief true) - Real.log (rates.stationaryTrue)) := by
  have hT : rates.stationaryTrue *
      InformationTheory.klFun (belief true / rates.stationaryTrue) =
      belief true * (Real.log (belief true) - Real.log (rates.stationaryTrue)) +
        (rates.stationaryTrue - belief true) := by
    rw [weighted_klFun_eq_log_score rates.stationaryTrue_pos]
    simp only [Real.negMulLog]
    ring
  have hF : rates.stationaryFalse *
      InformationTheory.klFun (belief false / rates.stationaryFalse) =
      belief false * (Real.log (belief false) - Real.log (rates.stationaryFalse)) +
        (rates.stationaryFalse - belief false) := by
    rw [weighted_klFun_eq_log_score rates.stationaryFalse_pos]
    simp only [Real.negMulLog]
    ring
  rw [finiteKL, Fintype.sum_bool, stationaryLaw_true, stationaryLaw_false, hT, hF]
  ring_nf
  linarith [belief_sum_one belief, rates.stationary_sum_one]

/-- Core real-algebra identity behind theorem 1: the gap exceeds the
production-rate bound exactly by the signed log-split mass, which is
nonpositive. -/
private theorem efe_core (bf bt sf st Lf Lt : ℝ)
    (h1 : bf + bt = 1) (h2 : sf + st = 1)
    (hbound : sf * Lf + st * Lt ≤ 0) :
    bf * Lf + bt * Lt ≤ (st - bt) * (Lf - Lt) := by
  have h6 : bf + bt - (st + sf) = 0 := by linarith
  have hneg : (st - bt) * (Lf - Lt) - (bf * Lf + bt * Lt)
      = -(sf * Lf + st * Lt) - Lf * (bf + bt - (st + sf)) := by ring
  have h0 : 0 ≤ (st - bt) * (Lf - Lt) - (bf * Lf + bt * Lt) := by
    rw [hneg, h6, mul_zero, sub_zero]
    exact neg_nonneg.mpr hbound
  linarith

/-- **Theorem 1 (`epistemic_gain_bounded_by_affinity`).**  The policy-relevant
information gap of the belief is bounded by the entropy-production rate
`σ = J * A` scaled by the relaxation time `1 / decayRate`. -/
theorem epistemic_gain_bounded_by_affinity (rates : TwoStateRates)
    (belief : FiniteLaw Bool) (hSupport : ∀ i, 0 < belief i) :
    finiteKL belief rates.stationaryLaw ≤
      productionRate rates belief / rates.decayRate := by
  have hKL := finiteKL_stationaryLaw_eq rates belief
  have hAff : beliefAffinity rates belief =
      (Real.log (belief false) - Real.log (rates.stationaryFalse)) -
      (Real.log (belief true) - Real.log (rates.stationaryTrue)) := by
    have hab : rates.forward / rates.backward =
        rates.stationaryTrue / rates.stationaryFalse := by
      rw [← rates.stationaryTrue_mul_decayRate, ← rates.stationaryFalse_mul_decayRate]
      field_simp [rates.stationaryFalse_pos.ne, ne_of_gt rates.decayRate_pos]
    have hlogab : Real.log rates.forward - Real.log rates.backward =
        Real.log rates.stationaryTrue - Real.log rates.stationaryFalse := by
      rw [← Real.log_div (ne_of_gt rates.forward_pos) (ne_of_gt rates.backward_pos),
        ← Real.log_div (ne_of_gt rates.stationaryTrue_pos)
          (ne_of_gt rates.stationaryFalse_pos), hab]
    rw [beliefAffinity,
      Real.log_div (ne_of_gt (mul_pos (hSupport false) rates.forward_pos))
        (ne_of_gt (mul_pos (hSupport true) rates.backward_pos)),
      Real.log_mul (ne_of_gt (hSupport false)) (ne_of_gt rates.forward_pos),
      Real.log_mul (ne_of_gt (hSupport true)) (ne_of_gt rates.backward_pos)]
    linarith [hlogab]
  have hprod : productionRate rates belief / rates.decayRate =
      (rates.stationaryTrue - belief true) * beliefAffinity rates belief := by
    rw [productionRate, beliefCurrent_eq]
    field_simp [ne_of_gt rates.decayRate_pos]
  have hbound : rates.stationaryFalse *
        (Real.log (belief false) - Real.log (rates.stationaryFalse)) +
      rates.stationaryTrue *
        (Real.log (belief true) - Real.log (rates.stationaryTrue)) ≤ 0 := by
    have h1 : rates.stationaryFalse *
        (Real.log (belief false) - Real.log (rates.stationaryFalse))
        ≤ belief false - rates.stationaryFalse := by
      calc rates.stationaryFalse *
              (Real.log (belief false) - Real.log (rates.stationaryFalse))
          = rates.stationaryFalse *
              Real.log (belief false / rates.stationaryFalse) := by
                rw [Real.log_div (ne_of_gt (hSupport false))
                  (ne_of_gt rates.stationaryFalse_pos)]
        _ ≤ rates.stationaryFalse *
              (belief false / rates.stationaryFalse - 1) :=
              mul_le_mul_of_nonneg_left
                (Real.log_le_sub_one_of_pos
                  (div_pos (hSupport false) rates.stationaryFalse_pos))
                rates.stationaryFalse_pos.le
        _ = belief false - rates.stationaryFalse := by
              field_simp [ne_of_gt rates.stationaryFalse_pos]
    have h2 : rates.stationaryTrue *
        (Real.log (belief true) - Real.log (rates.stationaryTrue))
        ≤ belief true - rates.stationaryTrue := by
      calc rates.stationaryTrue *
              (Real.log (belief true) - Real.log (rates.stationaryTrue))
          = rates.stationaryTrue *
              Real.log (belief true / rates.stationaryTrue) := by
                rw [Real.log_div (ne_of_gt (hSupport true))
                  (ne_of_gt rates.stationaryTrue_pos)]
        _ ≤ rates.stationaryTrue *
              (belief true / rates.stationaryTrue - 1) :=
              mul_le_mul_of_nonneg_left
                (Real.log_le_sub_one_of_pos
                  (div_pos (hSupport true) rates.stationaryTrue_pos))
                rates.stationaryTrue_pos.le
        _ = belief true - rates.stationaryTrue := by
              field_simp [ne_of_gt rates.stationaryTrue_pos]
    linarith [h1, h2, belief_sum_one belief, rates.stationary_sum_one]
  rw [hKL, hprod, hAff]
  exact efe_core (belief false) (belief true) rates.stationaryFalse rates.stationaryTrue
    (Real.log (belief false) - Real.log (rates.stationaryFalse))
    (Real.log (belief true) - Real.log (rates.stationaryTrue))
    (belief_sum_one belief) rates.stationary_sum_one hbound

/-- Theorem 1 applied to the semigroup-evolved belief. -/
theorem residual_gain_bounded_by_affinity (rates : TwoStateRates)
    (belief : FiniteLaw Bool) (hSupport : ∀ i, 0 < belief i)
    (time : ℝ) (hTime : 0 ≤ time) :
    epistemicGain rates belief time hTime ≤
      productionRate rates
          ((rates.certifiedSemigroup.kernel time hTime).predictive belief) /
        rates.decayRate := by
  rw [epistemicGain]
  refine epistemic_gain_bounded_by_affinity rates _ fun i =>
    predictive_support_of _ belief hSupport (fun j => transition_diagonal_pos rates time j) i

/-! ## Two-state observing agent: EFE form of theorem 1 -/

/-- The two-state observing agent: every policy acts through the same
semigroup slice, observes the latent state perfectly (identity likelihood),
and prefers the invariant law. -/
noncomputable def twoStateModel (rates : TwoStateRates) (belief : FiniteLaw Bool)
    (time : ℝ) (hTime : 0 ≤ time) : GenerativeModel Bool Bool Bool where
  initialState := belief
  transition _ := rates.certifiedSemigroup.kernel time hTime
  likelihood := FiniteKernel.identity
  preferences := rates.stationaryLaw
  policyPrior := FiniteLaw.pointMass true

/-- Every policy of the observing agent predicts the semigroup-evolved
belief. -/
theorem twoStateModel_predictedState (rates : TwoStateRates) (belief : FiniteLaw Bool)
    (time : ℝ) (hTime : 0 ≤ time) (policy : Bool) :
    predictedState (twoStateModel rates belief time hTime) policy =
      (rates.certifiedSemigroup.kernel time hTime).predictive belief := rfl

/-- Perfect observation makes the predicted outcome law the evolved belief. -/
theorem twoStateModel_predictedOutcome (rates : TwoStateRates) (belief : FiniteLaw Bool)
    (time : ℝ) (hTime : 0 ≤ time) (policy : Bool) :
    predictedOutcome (twoStateModel rates belief time hTime) policy =
      (rates.certifiedSemigroup.kernel time hTime).predictive belief := by
  rw [predictedOutcome, twoStateModel_predictedState]
  simp only [twoStateModel]
  rw [FiniteKernel.predictive_identity]

/-- The observing agent satisfies the full-support contract whenever the
belief does. -/
theorem twoStateModel_fullSupport (rates : TwoStateRates) (belief : FiniteLaw Bool)
    (hSupport : ∀ i, 0 < belief i) (time : ℝ) (hTime : 0 ≤ time) :
    FullSupport (twoStateModel rates belief time hTime) where
  state_pos policy state := by
    rw [twoStateModel_predictedState]
    exact predictive_support_of _ belief hSupport
      (fun i => transition_diagonal_pos rates time i) state
  outcome_pos policy outcome := by
    rw [twoStateModel_predictedOutcome]
    exact predictive_support_of _ belief hSupport
      (fun i => transition_diagonal_pos rates time i) outcome
  preference_pos outcome := stationaryLaw_pos rates outcome

/-- Perfect observation removes all likelihood ambiguity. -/
theorem twoStateModel_ambiguity_eq_zero (rates : TwoStateRates) (belief : FiniteLaw Bool)
    (time : ℝ) (hTime : 0 ≤ time) (policy : Bool) :
    ambiguity (twoStateModel rates belief time hTime) policy = 0 := by
  rw [ambiguity, twoStateModel_predictedState, conditionalEntropy]
  simp only [twoStateModel]
  refine Finset.sum_eq_zero fun x _ => ?_
  have hrow : entropy ((FiniteKernel.identity : FiniteKernel Bool Bool).row x) = 0 := by
    simp only [entropy, FiniteKernel.row, FiniteKernel.identity,
      FiniteKernel.deterministic, Fintype.sum_bool]
    cases x <;> simp
  rw [hrow, mul_zero]

/-- For the two-state observing agent the expected free energy of every
policy is exactly the belief information gap: `risk` is the gap and the
perfect-observation ambiguity vanishes. -/
theorem twoStateModel_expectedFreeEnergy (rates : TwoStateRates)
    (belief : FiniteLaw Bool) (hSupport : ∀ i, 0 < belief i)
    (time : ℝ) (hTime : 0 ≤ time) (policy : Bool) :
    expectedFreeEnergy (twoStateModel rates belief time hTime) policy =
      epistemicGain rates belief time hTime := by
  rw [expectedFreeEnergy_eq_risk_add_ambiguity
    (twoStateModel rates belief time hTime) policy
    (twoStateModel_fullSupport rates belief hSupport time hTime),
    twoStateModel_ambiguity_eq_zero, add_zero, risk,
    twoStateModel_predictedOutcome]
  rfl

/-- The policy-relevant gain contracts to the initial gap: acting through the
certified slice cannot increase the information gap against the invariant
law. -/
theorem epistemicGain_initial_bound (rates : TwoStateRates)
    (belief : FiniteLaw Bool) (hSupport : ∀ i, 0 < belief i)
    (time : ℝ) (hTime : 0 ≤ time) :
    epistemicGain rates belief time hTime ≤
      finiteKL belief rates.stationaryLaw := by
  by_cases h0 : time = 0
  · subst h0
    have hzero : rates.certifiedSemigroup.kernel 0 hTime = FiniteKernel.identity :=
      rates.certifiedSemigroup.kernel_zero
    rw [epistemicGain, hzero, FiniteKernel.predictive_identity]
  · have hpos : 0 < time := lt_of_le_of_ne hTime (Ne.symm h0)
    have hdp := finiteChannel_dataProcessing belief rates.stationaryLaw
      (rates.certifiedSemigroup.kernel time hTime) hSupport
      (fun i => stationaryLaw_pos rates i)
      (fun x y => transition_fullSupport_pos rates time hTime hpos x y)
    have hstat := TwoStateRates.certifiedSemigroup_stationary rates time hTime
    unfold FEP.FiniteMarkovDynamics.IsInvariant at hstat
    rw [hstat] at hdp
    rw [epistemicGain]
    exact hdp

/-- **Theorem 1, EFE form.**  The expected free energy of the two-state
observing agent is bounded by the entropy-production rate scaled by the
relaxation time. -/
theorem expectedFreeEnergy_le_productionRate_div_decayRate (rates : TwoStateRates)
    (belief : FiniteLaw Bool) (hSupport : ∀ i, 0 < belief i)
    (time : ℝ) (hTime : 0 ≤ time) (policy : Bool) :
    expectedFreeEnergy (twoStateModel rates belief time hTime) policy ≤
      productionRate rates belief / rates.decayRate := by
  rw [twoStateModel_expectedFreeEnergy rates belief hSupport time hTime policy]
  exact le_trans (epistemicGain_initial_bound rates belief hSupport time hTime)
    (epistemic_gain_bounded_by_affinity rates belief hSupport)

/-! ## Theorem 2: slow–fast separation -/

/-- Pointwise domination of the KL integrand by the squared log-ratio. -/
private theorem klFun_le_sqDiff {r : ℝ} (hr : 0 ≤ r) :
    InformationTheory.klFun r ≤ (r - 1) ^ 2 := by
  by_cases h0 : r = 0
  · subst h0
    rw [InformationTheory.klFun_zero]
    norm_num
  · have hpos : 0 < r := lt_of_le_of_ne hr (Ne.symm h0)
    rw [InformationTheory.klFun_apply]
    have hlog := Real.log_le_sub_one_of_pos hpos
    have h1 : r * Real.log r ≤ r * r - r := by
      nlinarith [mul_le_mul_of_nonneg_left hlog hr]
    have h2 : (r - 1) ^ 2 = r * r - 2 * r + 1 := by ring
    rw [h2]
    linarith

/-- Combining the two per-coordinate χ² terms of a two-state law. -/
private theorem twoPoint_chi_combine (A πt πf : ℝ) (hsum : πf + πt = 1)
    (hπt : 0 < πt) (hπf : 0 < πf) :
    A / πt + A / πf = A / (πt * πf) := by
  rw [div_add_div A A hπt.ne' hπf.ne', mul_comm πt A, ← mul_add, hsum, mul_one]

/-- The information gap of the evolved belief is at most its χ²-style squared
distance to the invariant law. -/
theorem epistemicGain_le_sqDiff (rates : TwoStateRates) (belief : FiniteLaw Bool)
    (time : ℝ) (hTime : 0 ≤ time) :
    epistemicGain rates belief time hTime ≤
      ((rates.certifiedSemigroup.kernel time hTime).predictive belief true
          - rates.stationaryTrue) ^ 2 /
        (rates.stationaryTrue * rates.stationaryFalse) := by
  have hπt : 0 < rates.stationaryTrue := rates.stationaryTrue_pos
  have hπf : 0 < rates.stationaryFalse := rates.stationaryFalse_pos
  have hterm : ∀ (i : Bool) (π : ℝ), 0 < π →
      π * InformationTheory.klFun
        ((rates.certifiedSemigroup.kernel time hTime).predictive belief i / π) ≤
        ((rates.certifiedSemigroup.kernel time hTime).predictive belief i - π) ^ 2 / π := by
    intro i π hπi
    have hnonneg : 0 ≤
        (rates.certifiedSemigroup.kernel time hTime).predictive belief i / π :=
      div_nonneg (((rates.certifiedSemigroup.kernel time hTime).predictive belief).nonneg i)
        hπi.le
    calc π * InformationTheory.klFun
            ((rates.certifiedSemigroup.kernel time hTime).predictive belief i / π) ≤
        π * (((rates.certifiedSemigroup.kernel time hTime).predictive belief i / π) - 1) ^ 2 :=
          mul_le_mul_of_nonneg_left (klFun_le_sqDiff hnonneg) hπi.le
      _ = ((rates.certifiedSemigroup.kernel time hTime).predictive belief i - π) ^ 2 / π := by
          field_simp [ne_of_gt hπi]
  rw [epistemicGain, finiteKL, Fintype.sum_bool, stationaryLaw_true, stationaryLaw_false]
  refine le_trans (add_le_add
    (hterm true rates.stationaryTrue rates.stationaryTrue_pos)
    (hterm false rates.stationaryFalse rates.stationaryFalse_pos)) ?_
  have hsum : (rates.certifiedSemigroup.kernel time hTime).predictive belief false
      + (rates.certifiedSemigroup.kernel time hTime).predictive belief true = 1 :=
    belief_sum_one _
  have hΔf : (rates.certifiedSemigroup.kernel time hTime).predictive belief false -
      rates.stationaryFalse =
      -((rates.certifiedSemigroup.kernel time hTime).predictive belief true -
        rates.stationaryTrue) := by
    linarith [hsum, rates.stationary_sum_one]
  have hsqf : ((rates.certifiedSemigroup.kernel time hTime).predictive belief false -
      rates.stationaryFalse) ^ 2 =
      ((rates.certifiedSemigroup.kernel time hTime).predictive belief true -
        rates.stationaryTrue) ^ 2 := by
    rw [hΔf]
    ring
  rw [hsqf, twoPoint_chi_combine _ _ _ rates.stationary_sum_one hπt hπf]

/-- The evolved `true` mass is exactly the repo's closed-form relaxation
functional. -/
theorem evolved_true_eq_trueMass (rates : TwoStateRates)
    (belief : FiniteLaw Bool) (time : ℝ) (hTime : 0 ≤ time) :
    (rates.certifiedSemigroup.kernel time hTime).predictive belief true
      = rates.trueMass belief time := rfl

/-- **Theorem 2 (`slow_fast_separation_statement`).**  The evolved
policy-relevant information gap is bounded by the squared relaxation factor
times the initial gap: information contracts to the invariant measure on the
relaxation timescale, so the information timescale is twice the mass
relaxation timescale. -/
theorem slow_fast_separation_statement (rates : TwoStateRates)
    (belief : FiniteLaw Bool) (time : ℝ) (hTime : 0 ≤ time) :
    epistemicGain rates belief time hTime ≤
      rates.rho time ^ 2 *
        ((belief true - rates.stationaryTrue) ^ 2 /
          (rates.stationaryTrue * rates.stationaryFalse)) := by
  refine le_trans (epistemicGain_le_sqDiff rates belief time hTime) ?_
  rw [evolved_true_eq_trueMass, rates.relaxation_exact belief time]
  exact le_of_eq (by ring)

/-! ## Fast-relaxation scaling: the `eps → 0⁺` limit -/

/-- The fast-relaxation rescaling: rates grow by `1 / eps` while the invariant
law is untouched. -/
noncomputable def scaledRates (rates : TwoStateRates) (eps : ℝ) (heps : 0 < eps) :
    TwoStateRates where
  forward := rates.forward / eps
  backward := rates.backward / eps
  forward_pos := div_pos rates.forward_pos heps
  backward_pos := div_pos rates.backward_pos heps

theorem scaledRates_decayRate_eq (rates : TwoStateRates) (eps : ℝ) (heps : 0 < eps) :
    (scaledRates rates eps heps).decayRate = rates.decayRate / eps := by
  show rates.forward / eps + rates.backward / eps = rates.decayRate / eps
  rw [TwoStateRates.decayRate]
  field_simp [ne_of_gt heps]

theorem scaledRates_stationaryTrue_eq (rates : TwoStateRates) (eps : ℝ) (heps : 0 < eps) :
    (scaledRates rates eps heps).stationaryTrue = rates.stationaryTrue := by
  show (rates.forward / eps) / (rates.forward / eps + rates.backward / eps)
      = rates.forward / (rates.forward + rates.backward)
  field_simp [ne_of_gt heps, ne_of_gt rates.decayRate_pos,
    ne_of_gt (add_pos (div_pos rates.forward_pos heps)
      (div_pos rates.backward_pos heps))]

theorem scaledRates_stationaryFalse_eq (rates : TwoStateRates) (eps : ℝ) (heps : 0 < eps) :
    (scaledRates rates eps heps).stationaryFalse = rates.stationaryFalse := by
  show (rates.backward / eps) / (rates.forward / eps + rates.backward / eps)
      = rates.backward / (rates.forward + rates.backward)
  field_simp [ne_of_gt heps, ne_of_gt rates.decayRate_pos,
    ne_of_gt (add_pos (div_pos rates.forward_pos heps)
      (div_pos rates.backward_pos heps))]

theorem scaledRates_stationaryLaw_eq (rates : TwoStateRates) (eps : ℝ) (heps : 0 < eps) :
    (scaledRates rates eps heps).stationaryLaw = rates.stationaryLaw := by
  apply FiniteLaw.ext_mass
  funext i
  cases i
  · rw [stationaryLaw_false, stationaryLaw_false, scaledRates_stationaryFalse_eq]
  · rw [stationaryLaw_true, stationaryLaw_true, scaledRates_stationaryTrue_eq]

theorem scaledRates_rho_eq (rates : TwoStateRates) (eps : ℝ) (heps : 0 < eps) (time : ℝ) :
    (scaledRates rates eps heps).rho time
      = Real.exp (-(rates.decayRate / eps) * time) := by
  rw [TwoStateRates.rho, scaledRates_decayRate_eq]

/-- Under the `1 / eps` rate scaling the evolved gain is bounded by the squared
scaled relaxation factor times the initial gap. -/
theorem epistemicGain_rateScaling (rates : TwoStateRates) (belief : FiniteLaw Bool)
    (time : ℝ) (hTime : 0 ≤ time) (eps : ℝ) (heps : 0 < eps) :
    epistemicGain (scaledRates rates eps heps) belief time hTime ≤
      Real.exp (-(rates.decayRate / eps) * time) ^ 2 *
        ((belief true - rates.stationaryTrue) ^ 2 /
          (rates.stationaryTrue * rates.stationaryFalse)) := by
  refine le_trans (epistemicGain_le_sqDiff (scaledRates rates eps heps) belief time hTime) ?_
  rw [evolved_true_eq_trueMass,
    TwoStateRates.relaxation_exact (scaledRates rates eps heps) belief time,
    scaledRates_rho_eq, scaledRates_stationaryTrue_eq, scaledRates_stationaryFalse_eq]
  exact le_of_eq (by ring)

/-- **Theorem 2, limit form.**  Under the `1 / eps` rate scaling the
policy-relevant gain after a fixed positive action time vanishes as
`eps → 0⁺`; on the tuned branch the explicit witness is
`eps = decayRate * time / (-log (delta / chi0))`. -/
theorem fastRelaxation_epistemic_vanishes (rates : TwoStateRates)
    (belief : FiniteLaw Bool) (time : ℝ) (hpos : 0 < time) :
    ∀ δ : ℝ, 0 < δ → ∃ eps : ℝ, 0 < eps ∧ ∀ (hTime : 0 ≤ time) (heps : 0 < eps),
      epistemicGain (scaledRates rates eps heps) belief time hTime ≤ δ := by
  intro δ hδ
  have hχnonneg : 0 ≤ (belief true - rates.stationaryTrue) ^ 2 /
      (rates.stationaryTrue * rates.stationaryFalse) :=
    div_nonneg (sq_nonneg _)
      (mul_pos rates.stationaryTrue_pos rates.stationaryFalse_pos).le
  have hsq1 : Real.exp (-(rates.decayRate / 1) * time) ^ 2 ≤ 1 := by
    have hexp1 : Real.exp (-(rates.decayRate / 1) * time) ≤ 1 :=
      (Real.exp_le_one_iff).mpr (by
        rw [neg_mul, neg_nonpos]
        exact mul_nonneg (div_pos rates.decayRate_pos one_pos).le hpos.le)
    have h := mul_self_le_mul_self (Real.exp_nonneg _) hexp1
    rwa [one_mul, ← pow_two] at h
  by_cases hsmall : (belief true - rates.stationaryTrue) ^ 2 /
      (rates.stationaryTrue * rates.stationaryFalse) ≤ δ
  · refine ⟨1, one_pos, fun hTime heps => ?_⟩
    refine le_trans (epistemicGain_rateScaling rates belief time hTime 1 one_pos) ?_
    refine le_trans (mul_le_mul_of_nonneg_right hsq1 hχnonneg) ?_
    rw [one_mul]
    exact hsmall
  · have hχlt : δ < (belief true - rates.stationaryTrue) ^ 2 /
      (rates.stationaryTrue * rates.stationaryFalse) := lt_of_not_ge hsmall
    have hχpos : 0 < (belief true - rates.stationaryTrue) ^ 2 /
      (rates.stationaryTrue * rates.stationaryFalse) := lt_trans hδ hχlt
    have htargetlt : δ / ((belief true - rates.stationaryTrue) ^ 2 /
        (rates.stationaryTrue * rates.stationaryFalse)) < 1 :=
      div_lt_one hχpos |>.mpr hχlt
    have htargetpos : 0 < δ / ((belief true - rates.stationaryTrue) ^ 2 /
        (rates.stationaryTrue * rates.stationaryFalse)) := div_pos hδ hχpos
    have hMpos : 0 < -Real.log (δ / ((belief true - rates.stationaryTrue) ^ 2 /
        (rates.stationaryTrue * rates.stationaryFalse))) :=
      neg_pos.mpr ((Real.log_neg_iff htargetpos).mpr htargetlt)
    refine ⟨rates.decayRate * time /
      -Real.log (δ / ((belief true - rates.stationaryTrue) ^ 2 /
        (rates.stationaryTrue * rates.stationaryFalse))),
      div_pos (mul_pos rates.decayRate_pos hpos) hMpos, fun hTime heps => ?_⟩
    refine le_trans (epistemicGain_rateScaling rates belief time hTime _ heps) ?_
    have hkey : -(rates.decayRate / (rates.decayRate * time /
        -Real.log (δ / ((belief true - rates.stationaryTrue) ^ 2 /
          (rates.stationaryTrue * rates.stationaryFalse))))) * time
        = Real.log (δ / ((belief true - rates.stationaryTrue) ^ 2 /
          (rates.stationaryTrue * rates.stationaryFalse))) := by
      have hcore : (rates.decayRate / (rates.decayRate * time /
          -Real.log (δ / ((belief true - rates.stationaryTrue) ^ 2 /
            (rates.stationaryTrue * rates.stationaryFalse))))) * time
          = -Real.log (δ / ((belief true - rates.stationaryTrue) ^ 2 /
            (rates.stationaryTrue * rates.stationaryFalse))) := by
        field_simp [ne_of_gt (mul_pos rates.decayRate_pos hpos), ne_of_gt hMpos]
        rw [neg_inj, mul_div_cancel_left₀ _ (ne_of_gt rates.decayRate_pos)]
      rw [neg_mul, hcore, neg_neg]
    have htsq : (δ / ((belief true - rates.stationaryTrue) ^ 2 /
        (rates.stationaryTrue * rates.stationaryFalse))) ^ 2 ≤
      δ / ((belief true - rates.stationaryTrue) ^ 2 /
        (rates.stationaryTrue * rates.stationaryFalse)) := by
      rw [pow_two]
      exact le_trans (mul_le_mul_of_nonneg_right htargetlt.le htargetpos.le)
        (by rw [one_mul])
    rw [hkey, Real.exp_log htargetpos]
    refine le_trans (mul_le_mul_of_nonneg_right htsq hχnonneg) ?_
    exact le_of_eq (div_mul_cancel₀ δ (ne_of_gt hχpos))

/-! ## One-slice path-space entropy production -/

/-- The aligned reverse law of the one-slice path protocol: the joint law of
the slice with source and target coordinates swapped. -/
noncomputable def slicePathReverse (rates : TwoStateRates) (belief : FiniteLaw Bool)
    (time : ℝ) (hTime : 0 ≤ time) : FiniteLaw (Bool × Bool) where
  mass p := belief p.2 * rates.certifiedSemigroup.kernel time hTime p.2 p.1
  nonneg p := mul_nonneg (belief.nonneg p.2)
    ((rates.certifiedSemigroup.kernel time hTime).nonneg p.2 p.1)
  sum_one := by
    rw [Fintype.sum_prod_type, Finset.sum_comm]
    simp_rw [← Finset.mul_sum,
      (rates.certifiedSemigroup.kernel time hTime).sum_one, mul_one]
    exact belief.sum_one

/-- The one-slice path protocol for the certified two-state slice at
`belief`: forward paths are source–target pairs of the slice; the aligned
reverse law swaps the pair. -/
noncomputable def slicePathProtocol (rates : TwoStateRates)
    (belief : FiniteLaw Bool) (time : ℝ) (hTime : 0 ≤ time) :
    FinitePathProtocol (Bool × Bool) where
  forward := (rates.certifiedSemigroup.kernel time hTime).joint belief
  reverseAligned := slicePathReverse rates belief time hTime
  reversal := fun p => (p.2, p.1)
  reversal_involutive := fun _p => rfl

private theorem slicePath_forward_mass (rates : TwoStateRates) (belief : FiniteLaw Bool)
    (time : ℝ) (hTime : 0 ≤ time) (s t : Bool) :
    (slicePathProtocol rates belief time hTime).forward (s, t)
      = belief s * rates.certifiedSemigroup.kernel time hTime s t := rfl

private theorem slicePath_reverse_mass (rates : TwoStateRates) (belief : FiniteLaw Bool)
    (time : ℝ) (hTime : 0 ≤ time) (s t : Bool) :
    (slicePathProtocol rates belief time hTime).reverseAligned (s, t)
      = belief t * rates.certifiedSemigroup.kernel time hTime t s := rfl

/-- **Theorem 3 (`slicePath_entropyProduction_eq`).**  The one-slice path-space
entropy production of `FEP.PathThermodynamics` equals `(1 - rho time) * σ /
decayRate`: the generator entropy-production rate `σ = J * A` is exactly the
per-unit-relaxation path-space dissipation rate. -/
theorem slicePath_entropyProduction_eq (rates : TwoStateRates)
    (belief : FiniteLaw Bool) (hSupport : ∀ i, 0 < belief i)
    (time : ℝ) (hTime : 0 ≤ time) (hpos : 0 < time) :
    entropyProduction (slicePathProtocol rates belief time hTime)
      = (1 - rates.rho time) * productionRate rates belief / rates.decayRate := by
  have hForward : ∀ p : Bool × Bool,
      0 < (slicePathProtocol rates belief time hTime).forward p := by
    rintro ⟨s, t⟩
    rw [slicePath_forward_mass]
    exact mul_pos (hSupport s) (transition_fullSupport_pos rates time hTime hpos s t)
  have hReverse : ∀ p : Bool × Bool,
      0 < (slicePathProtocol rates belief time hTime).reverseAligned p := by
    rintro ⟨s, t⟩
    rw [slicePath_reverse_mass]
    exact mul_pos (hSupport t) (transition_fullSupport_pos rates time hTime hpos t s)
  have hdiag : ∀ s : Bool, (belief s * rates.transition time s s) *
      Real.log ((belief s * rates.transition time s s) /
        (belief s * rates.transition time s s)) = 0 := by
    intro s
    rw [div_self (ne_of_gt (mul_pos (hSupport s) (transition_diagonal_pos rates time s))),
      Real.log_one, mul_zero]
  have hA : Real.log ((belief false * rates.transition time false true) /
      (belief true * rates.transition time true false)) = beliefAffinity rates belief := by
    rw [transition_false_true, transition_true_false, beliefAffinity]
    refine congrArg Real.log ?_
    rw [← rates.stationaryTrue_mul_decayRate, ← rates.stationaryFalse_mul_decayRate]
    field_simp [ne_of_gt (hSupport true), rates.stationaryFalse_pos.ne,
      ne_of_gt rates.decayRate_pos,
      ne_of_gt (show 0 < 1 - rates.rho time by linarith [rho_lt_one rates hpos])]
  have hAinv : Real.log ((belief true * rates.transition time true false) /
      (belief false * rates.transition time false true))
      = -beliefAffinity rates belief := by
    have hxy : 0 < belief false * rates.transition time false true :=
      mul_pos (hSupport false) (transition_fullSupport_pos rates time hTime hpos false true)
    have hyx : 0 < belief true * rates.transition time true false :=
      mul_pos (hSupport true) (transition_fullSupport_pos rates time hTime hpos true false)
    rw [show ((belief true * rates.transition time true false) /
        (belief false * rates.transition time false true)) =
        ((belief false * rates.transition time false true) /
        (belief true * rates.transition time true false))⁻¹ from
        (inv_div _ _).symm,
      Real.log_inv, hA]
  have hker : ∀ s t : Bool, (rates.certifiedSemigroup.kernel time hTime) s t
      = rates.transition time s t := fun s t => rfl
  rw [entropyProduction_eq_expected_logRatio _ hForward hReverse]
  simp only [Fintype.sum_prod_type, Fintype.sum_bool, pathwiseEntropyProduction,
    pathRatio, slicePath_forward_mass, slicePath_reverse_mass, hker]
  rw [hdiag false, hdiag true, zero_add, add_zero]
  rw [hA, hAinv, transition_false_true, transition_true_false]
  rw [productionRate, beliefCurrent, ← rates.stationaryTrue_mul_decayRate,
    ← rates.stationaryFalse_mul_decayRate]
  field_simp [ne_of_gt rates.decayRate_pos]
  ring

end FEP.TimeScaleEFE
