"""Canonical Lean bodies for one original catalogue family."""

from __future__ import annotations

BODIES: dict[str, str] = {
    "fep-013": """import Mathlib.Analysis.Calculus.Deriv.Add
import Mathlib.Analysis.Calculus.Deriv.Mul
import Mathlib.Tactic

namespace FEP013

-- [proof strategy: simp / ring for algebraic rewrites; linarith for entropy-monotone bounds]

/-- Helmholtz free energy: F = U - TS defines the thermodynamic potential. -/
noncomputable def fep013_helmholtz (U T S : ℝ) : ℝ := U - T * S

/-- At zero temperature, Helmholtz free energy equals internal energy. -/
theorem fep013_helmholtz_at_zero_temp (U S : ℝ) : fep013_helmholtz U 0 S = U := by
  simp [fep013_helmholtz]

/-- Helmholtz free energy is monotone decreasing in entropy at positive temperature. -/
theorem fep013_helmholtz_mono_entropy (U T : ℝ) (S₁ S₂ : ℝ) (hT : 0 < T) (h : S₁ ≤ S₂) :
    fep013_helmholtz U T S₂ ≤ fep013_helmholtz U T S₁ := by
  simp only [fep013_helmholtz]
  linarith [mul_le_mul_of_nonneg_left h (le_of_lt hT)]

/-- Helmholtz free energy is monotone increasing in internal energy. -/
theorem fep013_helmholtz_mono_U (U₁ U₂ T S : ℝ) (h : U₁ ≤ U₂) :
    fep013_helmholtz U₁ T S ≤ fep013_helmholtz U₂ T S := by
  simp only [fep013_helmholtz]; linarith

/-- Helmholtz difference: ΔF = ΔU - TΔS. -/
theorem fep013_delta_F (U₁ U₂ T S₁ S₂ : ℝ) :
    fep013_helmholtz U₂ T S₂ - fep013_helmholtz U₁ T S₁ = (U₂ - U₁) - T * (S₂ - S₁) := by
  simp only [fep013_helmholtz]; ring

/-- Exact temperature derivative of `F(T) = U(T) - T S(T)`. -/
theorem fep013_helmholtz_hasDerivAt
    {U S : ℝ → ℝ} {U' S' T : ℝ}
    (hU : HasDerivAt U U' T) (hS : HasDerivAt S S' T) :
    HasDerivAt (fun t => fep013_helmholtz (U t) t (S t))
      (U' - (S T + T * S')) T := by
  convert HasDerivAt.sub hU (HasDerivAt.mul (hasDerivAt_id T) hS) using 1
  all_goals
    first
    | exact AddCommGroup.ext rfl
    | exact Module.ext rfl
    | rfl
    | simp

/-- Under the equilibrium first-law identity `U'(T) = T S'(T)`, the
Helmholtz derivative is exactly minus entropy. -/
theorem fep013_helmholtz_derivative_eq_neg_entropy
    {U S : ℝ → ℝ} {U' S' T : ℝ}
    (hU : HasDerivAt U U' T) (hS : HasDerivAt S S' T)
    (hfirstLaw : U' = T * S') :
    HasDerivAt (fun t => fep013_helmholtz (U t) t (S t)) (-S T) T := by
  convert fep013_helmholtz_hasDerivAt hU hS using 1
  rw [hfirstLaw]
  ring

end FEP013
""",
    "fep-025": """import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.LinearAlgebra.Matrix.Notation
import Mathlib.Tactic

namespace FEP025

open Finset

/-- Net probability current is forward flow minus reverse flow. -/
def fep025_probabilityCurrent {n : ℕ}
    (flow : Matrix (Fin n) (Fin n) ℝ) : Matrix (Fin n) (Fin n) ℝ :=
  fun i j => flow i j - flow j i

/-- Probability current is antisymmetric under edge reversal. -/
theorem fep025_probabilityCurrent_antisymm {n : ℕ}
    (flow : Matrix (Fin n) (Fin n) ℝ) (i j : Fin n) :
    fep025_probabilityCurrent flow i j =
      -fep025_probabilityCurrent flow j i := by
  simp only [fep025_probabilityCurrent]
  ring

/-- A probability current has no diagonal self-current. -/
theorem fep025_probabilityCurrent_diag_zero {n : ℕ}
    (flow : Matrix (Fin n) (Fin n) ℝ) (i : Fin n) :
    fep025_probabilityCurrent flow i i = 0 := by
  simp [fep025_probabilityCurrent]

/-- Net current leaving a state. Stationarity is zero divergence at each state. -/
def fep025_divergence {n : ℕ}
    (current : Matrix (Fin n) (Fin n) ℝ) (i : Fin n) : ℝ :=
  ∑ j, current i j

/-- Antisymmetry conserves total probability: divergences sum to zero. -/
theorem fep025_total_divergence_zero {n : ℕ}
    (current : Matrix (Fin n) (Fin n) ℝ)
    (hcurrent : ∀ i j, current i j = -current j i) :
    ∑ i, fep025_divergence current i = 0 := by
  have hneg : (∑ i, ∑ j, current i j) = -(∑ i, ∑ j, current i j) := by
    calc
      (∑ i, ∑ j, current i j) = ∑ j, ∑ i, current i j :=
        Finset.sum_comm
      _ = ∑ j, ∑ i, -current j i := by
        apply Finset.sum_congr rfl
        intro j _
        apply Finset.sum_congr rfl
        intro i _
        exact hcurrent i j
      _ = -(∑ j, ∑ i, current j i) := by simp
      _ = -(∑ i, ∑ j, current i j) := rfl
  simp only [fep025_divergence]
  linarith

/-- Current induced by a distribution and transition matrix. -/
def fep025_transitionCurrent {n : ℕ}
    (stationary : Fin n → ℝ) (transition : Matrix (Fin n) (Fin n) ℝ) :
    Matrix (Fin n) (Fin n) ℝ :=
  fep025_probabilityCurrent (fun i j => stationary i * transition i j)

/-- Row normalization and distribution stationarity imply zero current
divergence at every state. -/
theorem fep025_transitionCurrent_stationary {n : ℕ}
    (stationary : Fin n → ℝ) (transition : Matrix (Fin n) (Fin n) ℝ)
    (hrow : ∀ i, ∑ j, transition i j = 1)
    (hstationary : ∀ j, ∑ i, stationary i * transition i j = stationary j)
    (i : Fin n) :
    fep025_divergence (fep025_transitionCurrent stationary transition) i = 0 := by
  simp only [fep025_divergence, fep025_transitionCurrent,
    fep025_probabilityCurrent, Finset.sum_sub_distrib, ← Finset.mul_sum]
  rw [hrow i, mul_one, hstationary i, sub_self]

/-- Uniform stationary law for a directed three-state cycle. -/
noncomputable def fep025_cycleStationary : Fin 3 → ℝ := ![1 / 3, 1 / 3, 1 / 3]

/-- Deterministic clockwise transition on three states. -/
def fep025_cycleTransition : Matrix (Fin 3) (Fin 3) ℝ :=
  !![0, 1, 0; 0, 0, 1; 1, 0, 0]

/-- The probability current generated by the stationary cycle model. -/
noncomputable def fep025_cycleCurrent : Matrix (Fin 3) (Fin 3) ℝ :=
  fep025_transitionCurrent fep025_cycleStationary fep025_cycleTransition

theorem fep025_cycleTransition_row (i : Fin 3) :
    ∑ j, fep025_cycleTransition i j = 1 := by
  fin_cases i <;> norm_num [fep025_cycleTransition, Fin.sum_univ_succ]

theorem fep025_cycleStationary_invariant (j : Fin 3) :
    ∑ i, fep025_cycleStationary i * fep025_cycleTransition i j =
      fep025_cycleStationary j := by
  fin_cases j <;> norm_num [fep025_cycleStationary, fep025_cycleTransition,
    Fin.sum_univ_succ]

/-- The three-cycle current is divergence-free at every state. -/
theorem fep025_cycleCurrent_stationary (i : Fin 3) :
    fep025_divergence fep025_cycleCurrent i = 0 := by
  exact fep025_transitionCurrent_stationary fep025_cycleStationary
    fep025_cycleTransition fep025_cycleTransition_row
    fep025_cycleStationary_invariant i

/-- Stationarity does not force detailed balance: the cycle current is nonzero. -/
theorem fep025_cycleCurrent_nonzero : fep025_cycleCurrent 0 1 ≠ 0 := by
  norm_num [fep025_cycleCurrent, fep025_transitionCurrent,
    fep025_probabilityCurrent, fep025_cycleStationary, fep025_cycleTransition]

end FEP025
""",
    "fep-030": """import Mathlib.Analysis.SpecialFunctions.BinaryEntropy
import Mathlib.Algebra.BigOperators.Ring.Finset
import Mathlib.Basic.Real.Basic
import Mathlib.Tactic

namespace FEP030

open Real Finset

-- [proof strategy: native binary-entropy maximum plus explicit finite-uniform calculation]

/-- Binary Shannon entropy (in nats) is globally bounded above by log 2. -/
theorem fep030_binaryEntropy_max (p : ℝ) :
    Real.binEntropy p ≤ Real.log 2 :=
  Real.binEntropy_le_log_two

/-- The binary entropy maximum is attained uniquely at probability one half. -/
theorem fep030_binaryEntropy_eq_max_iff (p : ℝ) :
    Real.binEntropy p = Real.log 2 ↔ p = (2 : ℝ)⁻¹ :=
  Real.binEntropy_eq_log_two

/-- A uniform scalar weight is nonnegative. -/
theorem fep030_uniform_nonneg (n : ℕ) (_hn : 0 < n) : 0 ≤ (1 : ℝ) / n :=
  div_nonneg zero_le_one (Nat.cast_nonneg' (n := n))

/-- Uniform weights on a positive finite range sum to one. -/
theorem fep030_uniform_sum_one (n : ℕ) (hn : 0 < n) :
    ∑ _ ∈ Finset.range n, (1 : ℝ) / n = 1 := by
  rw [Finset.sum_const, Finset.card_range, nsmul_eq_mul]
  have hn0 : (n : ℝ) ≠ 0 := Nat.cast_ne_zero.mpr (Nat.ne_of_gt hn)
  field_simp [hn0]

/-- The logarithm of a positive natural cardinality is nonnegative. -/
theorem fep030_log_card_nonneg (n : ℕ) (hn : 1 ≤ n) : 0 ≤ Real.log n := by
  apply Real.log_nonneg
  exact_mod_cast hn

/-- The explicit uniform-weight entropy expression equals log n; maximality is not proved. -/
theorem fep030_entropy_eq_log (n : ℕ) (hn : 0 < n) :
    -∑ _ ∈ Finset.range n, (1 : ℝ) / n * Real.log ((1 : ℝ) / n)
    = Real.log n := by
  have hnR : (n : ℝ) ≠ 0 := Nat.cast_ne_zero.mpr (Nat.ne_of_gt hn)
  have hlog : Real.log ((1 : ℝ) / n) = - Real.log n := by
    rw [Real.log_div (one_ne_zero' ℝ) hnR, Real.log_one, zero_sub]
  have hsum : ∑ _ ∈ Finset.range n, (1 : ℝ) / n * Real.log ((1 : ℝ) / n) = - Real.log n := by
    calc
      ∑ _ ∈ Finset.range n, (1 : ℝ) / n * Real.log ((1 : ℝ) / n)
          = ∑ _ ∈ Finset.range n, (1 : ℝ) / n * (- Real.log n) :=
            Finset.sum_congr rfl fun _ _ => by rw [hlog]
      _ = (∑ _ ∈ Finset.range n, (1 : ℝ) / n) * (- Real.log n) := by rw [← Finset.sum_mul]
      _ = 1 * (- Real.log n) := by rw [fep030_uniform_sum_one n hn]
      _ = - Real.log n := by ring
  rw [hsum, neg_neg]

end FEP030
""",
    "fep-031": """import Mathlib.Analysis.SpecialFunctions.Exp

namespace FEP031

/-- Boltzmann weight exp(-βE) is strictly positive. -/
theorem fep031_gibbs_weight_pos (β E : ℝ) : 0 < Real.exp (-β * E) :=
  Real.exp_pos _

/-- Gibbs weight monotonicity: lower energy → higher weight at positive temperature (β > 0). -/
theorem fep031_gibbs_mono (β E₁ E₂ : ℝ) (hβ : 0 < β) (hE : E₁ ≤ E₂) :
    Real.exp (-β * E₂) ≤ Real.exp (-β * E₁) :=
  Real.exp_le_exp.mpr (by nlinarith [mul_le_mul_of_nonneg_left hE (le_of_lt hβ)])

/-- Partition function is strictly positive over any nonempty finite state space. -/
theorem fep031_partition_pos (β : ℝ) (n : ℕ) (E : Fin n → ℝ)
    (S : Finset (Fin n)) (hS : S.Nonempty) :
    0 < ∑ i ∈ S, Real.exp (-β * E i) :=
  Finset.sum_pos (fun _ _ => Real.exp_pos _) hS

/-- Gibbs probability on a selected finite support, normalized by its partition sum. -/
noncomputable def fep031_gibbsProbability (β : ℝ) (n : ℕ) (E : Fin n → ℝ)
    (S : Finset (Fin n)) (i : Fin n) : ℝ :=
  Real.exp (-β * E i) / ∑ j ∈ S, Real.exp (-β * E j)

/-- Each normalized Gibbs probability is nonnegative on nonempty support. -/
theorem fep031_gibbsProbability_nonneg (β : ℝ) (n : ℕ) (E : Fin n → ℝ)
    (S : Finset (Fin n)) (hS : S.Nonempty) (i : Fin n) :
    0 ≤ fep031_gibbsProbability β n E S i :=
  div_nonneg (le_of_lt (Real.exp_pos _))
    (le_of_lt (fep031_partition_pos β n E S hS))

/-- Normalized Gibbs probabilities sum to one on their selected support. -/
theorem fep031_gibbsProbability_sum_one (β : ℝ) (n : ℕ) (E : Fin n → ℝ)
    (S : Finset (Fin n)) (hS : S.Nonempty) :
    ∑ i ∈ S, fep031_gibbsProbability β n E S i = 1 := by
  have hden : (∑ j ∈ S, Real.exp (-β * E j)) ≠ 0 :=
    ne_of_gt (fep031_partition_pos β n E S hS)
  simp_rw [fep031_gibbsProbability, div_eq_mul_inv]
  rw [← Finset.sum_mul, mul_inv_cancel₀ hden]

end FEP031
""",
    "fep-037": """import Mathlib.Analysis.SpecificLimits.Normed
import Mathlib.Tactic

namespace FEP037

/-- Relaxation eigenvalue of the symmetric two-state Markov transition. -/
def fep037_relaxation (α : ℝ) : ℝ := 1 - 2 * α

/-- Stationary autocorrelation at lag `n` with equilibrium variance `variance`. -/
def fep037_autocorrelation (α variance : ℝ) (n : ℕ) : ℝ :=
  variance * fep037_relaxation α ^ n

/-- The autocorrelation obeys the Markov relaxation recurrence. -/
theorem fep037_autocorrelation_recurrence (α variance : ℝ) (n : ℕ) :
    fep037_autocorrelation α variance (n + 1) =
      fep037_relaxation α * fep037_autocorrelation α variance n := by
  simp only [fep037_autocorrelation, pow_succ]
  ring

/-- For a strictly interior switching probability, equilibrium correlations
decay to zero. -/
theorem fep037_autocorrelation_tendsto_zero
    {α : ℝ} (hα0 : 0 < α) (hα1 : α < 1) (variance : ℝ) :
    Filter.Tendsto (fep037_autocorrelation α variance)
      Filter.atTop (nhds 0) := by
  have habs : |fep037_relaxation α| < 1 := by
    rw [fep037_relaxation, abs_lt]
    constructor <;> linarith
  have hpow : Filter.Tendsto (fun n : ℕ => fep037_relaxation α ^ n)
      Filter.atTop (nhds 0) :=
    tendsto_pow_atTop_nhds_zero_of_abs_lt_one habs
  change Filter.Tendsto (fun n : ℕ => variance * fep037_relaxation α ^ n)
    Filter.atTop (nhds 0)
  simpa only [mul_zero] using hpow.const_mul variance

/-- Discrete fluctuation--response law: inverse temperature times the
one-step loss of stationary autocorrelation. -/
def fep037_response (β α variance : ℝ) (n : ℕ) : ℝ :=
  β * (fep037_autocorrelation α variance n -
    fep037_autocorrelation α variance (n + 1))

/-- Closed form of the discrete response kernel. -/
theorem fep037_response_eq (β α variance : ℝ) (n : ℕ) :
    fep037_response β α variance n =
      2 * β * α * variance * fep037_relaxation α ^ n := by
  rw [fep037_response, fep037_autocorrelation_recurrence]
  simp only [fep037_autocorrelation, fep037_relaxation]
  ring

/-- For nonnegative inverse temperature and variance, and switching no faster
than one half, the response kernel is nonnegative. -/
theorem fep037_response_nonneg
    {β α variance : ℝ} (hβ : 0 ≤ β) (hα0 : 0 ≤ α) (hαhalf : α ≤ 1 / 2)
    (hvariance : 0 ≤ variance) (n : ℕ) :
    0 ≤ fep037_response β α variance n := by
  rw [fep037_response_eq]
  have hrelax : 0 ≤ fep037_relaxation α := by
    rw [fep037_relaxation]
    linarith
  positivity

/-- The discrete response also relaxes to zero. -/
theorem fep037_response_tendsto_zero
    {α : ℝ} (hα0 : 0 < α) (hα1 : α < 1) (β variance : ℝ) :
    Filter.Tendsto (fun n => fep037_response β α variance n)
      Filter.atTop (nhds 0) := by
  have habs : |fep037_relaxation α| < 1 := by
    rw [fep037_relaxation, abs_lt]
    constructor <;> linarith
  have hpow : Filter.Tendsto (fun n : ℕ => fep037_relaxation α ^ n)
      Filter.atTop (nhds 0) :=
    tendsto_pow_atTop_nhds_zero_of_abs_lt_one habs
  simpa only [fep037_response_eq, mul_zero] using
    hpow.const_mul (2 * β * α * variance)

end FEP037
""",
    "fep-049": """import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Analysis.SpecialFunctions.Log.Basic
import Mathlib.Tactic

namespace FEP049

open Finset

/-- Diagonal linear constitutive law `Jᵢ = Lᵢ Xᵢ`. -/
def fep049_linearFlux {ι : Type*}
    (conductance force : ι → ℝ) (i : ι) : ℝ :=
  conductance i * force i

/-- Entropy production generated by diagonal conductances and forces. -/
def fep049_entropyProduction {ι : Type*} [Fintype ι]
    (conductance force : ι → ℝ) : ℝ :=
  ∑ i, conductance i * force i ^ 2

/-- The flux--force pairing is exactly the entropy-production quadratic form. -/
theorem fep049_flux_force_identity {ι : Type*} [Fintype ι]
    (conductance force : ι → ℝ) :
    (∑ i, force i * fep049_linearFlux conductance force i) =
      fep049_entropyProduction conductance force := by
  apply Finset.sum_congr rfl
  intro i _
  simp only [fep049_linearFlux]
  ring

/-- Nonnegative conductances imply nonnegative entropy production. -/
theorem fep049_entropyProduction_nonneg {ι : Type*} [Fintype ι]
    (conductance force : ι → ℝ)
    (hconductance : ∀ i, 0 ≤ conductance i) :
    0 ≤ fep049_entropyProduction conductance force := by
  exact Finset.sum_nonneg fun i _ =>
    mul_nonneg (hconductance i) (sq_nonneg (force i))

/-- With strictly positive conductances, entropy production vanishes exactly
at thermodynamic equilibrium (all forces zero). -/
theorem fep049_entropyProduction_eq_zero_iff {ι : Type*} [Fintype ι]
    (conductance force : ι → ℝ)
    (hconductance : ∀ i, 0 < conductance i) :
    fep049_entropyProduction conductance force = 0 ↔
      ∀ i, force i = 0 := by
  constructor
  · intro hzero i
    have hterm : conductance i * force i ^ 2 = 0 :=
      (Finset.sum_eq_zero_iff_of_nonneg
        (fun j _ => mul_nonneg (hconductance j).le (sq_nonneg (force j)))).mp
        hzero i (Finset.mem_univ i)
    have hsquare : force i ^ 2 = 0 :=
      (mul_eq_zero.mp hterm).resolve_left (ne_of_gt (hconductance i))
    nlinarith
  · intro hforce
    simp [fep049_entropyProduction, hforce]

/-- Thermodynamic affinity of a directed edge from positive forward and
reverse stationary fluxes. -/
noncomputable def fep049_edgeAffinity (forward reverse : ℝ) : ℝ :=
  Real.log (forward / reverse)

/-- Edge entropy production is current times affinity. -/
noncomputable def fep049_edgeProduction (forward reverse : ℝ) : ℝ :=
  (forward - reverse) * fep049_edgeAffinity forward reverse

/-- Positive bidirectional fluxes produce nonnegative edge entropy. -/
theorem fep049_edgeProduction_nonneg
    {forward reverse : ℝ} (hforward : 0 < forward) (hreverse : 0 < reverse) :
    0 ≤ fep049_edgeProduction forward reverse := by
  rw [fep049_edgeProduction, fep049_edgeAffinity,
    Real.log_div hforward.ne' hreverse.ne']
  rcases le_total reverse forward with h | h
  · exact mul_nonneg (sub_nonneg.mpr h)
      (sub_nonneg.mpr (Real.log_le_log hreverse h))
  · exact mul_nonneg_of_nonpos_of_nonpos (sub_nonpos.mpr h)
      (sub_nonpos.mpr (Real.log_le_log hforward h))

/-- Under positive bidirectional fluxes, zero edge production is equivalent
to detailed balance on that edge. -/
theorem fep049_edgeProduction_eq_zero_iff
    {forward reverse : ℝ} (hforward : 0 < forward) (hreverse : 0 < reverse) :
    fep049_edgeProduction forward reverse = 0 ↔ forward = reverse := by
  constructor
  · intro hzero
    rcases mul_eq_zero.mp hzero with hcurrent | haffinity
    · exact sub_eq_zero.mp hcurrent
    · have hratio : forward / reverse = 1 :=
        Real.eq_one_of_pos_of_log_eq_zero (div_pos hforward hreverse) haffinity
      have hmul : forward = 1 * reverse :=
        (div_eq_iff hreverse.ne').mp hratio
      simpa using hmul
  · rintro rfl
    simp [fep049_edgeProduction]

end FEP049
""",
    "fep-050": """import Mathlib.Analysis.SpecialFunctions.BinaryEntropy
import Mathlib.Tactic

namespace FEP050

/-- Logical reset of a binary memory to `false`. -/
def fep050_erasure (_bit : Bool) : Bool := false

/-- Reset is logically irreversible because it is not injective. -/
theorem fep050_erasure_not_injective :
    ¬Function.Injective fep050_erasure := by
  intro hinjective
  have hfalse_true : false = true := hinjective (by rfl)
  simp at hfalse_true

/-- Thermodynamic bit entropy in nats with Boltzmann constant `kB`. -/
noncomputable def fep050_bitEntropy (kB p : ℝ) : ℝ :=
  kB * Real.binEntropy p

/-- Entropy lost when an unbiased bit is reset to a pure state. -/
noncomputable def fep050_erasureEntropyLoss (kB : ℝ) : ℝ :=
  fep050_bitEntropy kB (2 : ℝ)⁻¹ - fep050_bitEntropy kB 0

/-- Resetting an unbiased bit loses exactly `kB log 2` entropy. -/
theorem fep050_erasureEntropyLoss_eq (kB : ℝ) :
    fep050_erasureEntropyLoss kB = kB * Real.log 2 := by
  simp [fep050_erasureEntropyLoss, fep050_bitEntropy]

/-- Environmental entropy gain from heat `Q` delivered at temperature `T`. -/
noncomputable def fep050_environmentEntropyChange (Q T : ℝ) : ℝ := Q / T

/-- Total entropy change for one-bit erasure. -/
noncomputable def fep050_totalEntropyChange (Q T kB : ℝ) : ℝ :=
  fep050_environmentEntropyChange Q T - fep050_erasureEntropyLoss kB

/-- Landauer threshold `kB T log 2`. -/
noncomputable def fep050_landauerBound (kB T : ℝ) : ℝ :=
  kB * T * Real.log 2

/-- The second-law entropy balance derives the Landauer heat bound; the
threshold inequality is a conclusion rather than an input. -/
theorem fep050_landauer_heat_bound
    {Q T kB : ℝ} (hT : 0 < T)
    (hsecondLaw : 0 ≤ fep050_totalEntropyChange Q T kB) :
    fep050_landauerBound kB T ≤ Q := by
  have hratio : kB * Real.log 2 ≤ Q / T := by
    rw [fep050_totalEntropyChange, fep050_environmentEntropyChange,
      fep050_erasureEntropyLoss_eq] at hsecondLaw
    exact sub_nonneg.mp hsecondLaw
  have hheat : (kB * Real.log 2) * T ≤ Q :=
    (le_div_iff₀ hT).mp hratio
  rw [fep050_landauerBound]
  nlinarith

/-- If supplied work dominates dissipated heat, the heat bound yields the
Landauer work bound. -/
theorem fep050_landauer_work_bound
    {W Q T kB : ℝ} (hT : 0 < T)
    (hsecondLaw : 0 ≤ fep050_totalEntropyChange Q T kB)
    (hworkHeat : Q ≤ W) :
    fep050_landauerBound kB T ≤ W :=
  (fep050_landauer_heat_bound hT hsecondLaw).trans hworkHeat

/-- The Landauer threshold is positive for positive `kB` and temperature. -/
theorem fep050_landauerBound_pos
    {kB T : ℝ} (hkB : 0 < kB) (hT : 0 < T) :
    0 < fep050_landauerBound kB T := by
  exact mul_pos (mul_pos hkB hT)
    (Real.log_pos (by norm_num : (1 : ℝ) < 2))

end FEP050
""",
}
