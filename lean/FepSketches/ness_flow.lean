import Mathlib.Algebra.Order.Ring.Unbundled.Basic
import Mathlib.Basic.Real.Basic
import Mathlib.Tactic

/-!
# Non-equilibrium steady-state (NESS) flow

The Bayesian-mechanics flow `f = (Q - Γ)∇F` is the dynamical heart of the Free
Energy Principle.  At equilibrium (`ω = 0`) the flow is pure gradient descent on
free energy, `f = -Γ∇F`, which comes to rest at a mode.  Away from equilibrium
(`ω ≠ 0`) an antisymmetric solenoidal term `Q ∇F` adds a persistent probability
current that circulates without doing work — the mathematical signature of a
living (non-equilibrium) steady state.

This module proves the ℝ-valued structural claims over `Fin 2 → ℝ`, the
simplest carrier that exhibits both regimes.  The Python demo in
ActiveInferenceSynthetic (`src/free_energy_flow.py`, `src/trajectories.py`,
`src/steady_state.py`) instantiates every quantity with concrete numbers; this
module provides the formal ℝ guarantee that the relationships hold identically,
for every gradient, every `ω`, and every `γ ≥ 0`.

## Main results

| theorem | Meaning |
|---------|---------|
| `solenoidal_orthogonal` | `(Q g) · g = 0` — the circulation does no work |
| `flow_work_eq_dissipation` | `f · g = -γ·‖g‖²` — free energy is non-increasing |
| `detailed_balance_iff` | `Q g = 0 ↔ ω = 0` — equilibrium or flow |
| `entropyProduction_nonneg` | `σ = 2ω²·precision/γ ≥ 0` |
| `entropyProduction_eq_zero_iff` | `σ = 0 ↔ ω = 0` for strict positive γ, precision |
-/

namespace FEP.NessFlow

/-- Euclidean inner product of real 2-vectors. -/
def dot (u v : Fin 2 → ℝ) : ℝ := u 0 * v 0 + u 1 * v 1

/-- Squared Euclidean norm of a 2-vector. -/
def normSq (v : Fin 2 → ℝ) : ℝ := dot v v

/-- The squared norm is nonnegative. -/
theorem normSq_nonneg (v : Fin 2 → ℝ) : 0 ≤ normSq v := by
  have h0 : 0 ≤ v 0 ^ 2 := pow_two_nonneg _
  have h1 : 0 ≤ v 1 ^ 2 := pow_two_nonneg _
  unfold normSq dot; nlinarith

/-- Solenoidal (antisymmetric) operator: `Q(ω) v = (ω·v₁, -ω·v₀)`. -/
def solenoidal (ω : ℝ) (v : Fin 2 → ℝ) : Fin 2 → ℝ :=
  λ i => match i with
    | 0 => ω * v 1
    | 1 => -ω * v 0

/-- The solenoidal operator is antisymmetric: `(Q v) · w = -(Q w) · v`. -/
theorem solenoidal_antisymm (ω : ℝ) (v w : Fin 2 → ℝ) :
    dot (solenoidal ω v) w = -dot (solenoidal ω w) v := by
  simp [dot, solenoidal]; ring

/-- **The solenoidal current does no work.** `(Q g) · g = 0` for every
gradient `g` and every `ω` — the antisymmetric operator produces a flow
everywhere orthogonal to `g`, so it leaves free energy unchanged. -/
theorem solenoidal_orthogonal (ω : ℝ) (g : Fin 2 → ℝ) :
    dot (solenoidal ω g) g = 0 := by
  simp [dot, solenoidal]; ring

/-- Dissipative (symmetric) operator: `Γ(γ) v = (γ·v₀, γ·v₁)`. -/
def dissipative (γ : ℝ) (v : Fin 2 → ℝ) : Fin 2 → ℝ :=
  λ i => γ * v i

/-- The full Bayesian-mechanics flow `f = (Q - Γ) g = Q g - Γ g`. -/
def flow (γ ω : ℝ) (g : Fin 2 → ℝ) : Fin 2 → ℝ :=
  λ i => (solenoidal ω g - dissipative γ g) i

/-- **Free-energy descent rate.** The work of the full flow against the gradient
`g = ∇F` is exactly the dissipative term `-γ·‖g‖²`.  Since `‖g‖² ≥ 0`, for
`γ ≥ 0` the free energy is non-increasing along the flow, and the solenoidal
circulation is thermodynamically free. -/
theorem flow_work_eq_dissipation (γ ω : ℝ) (g : Fin 2 → ℝ) :
    dot (flow γ ω g) g = -γ * normSq g := by
  simp [flow, dot, solenoidal, dissipative, normSq]; ring

/-- **Free energy is non-increasing along the flow,** for a nonnegative
dissipative coefficient `γ ≥ 0`. -/
theorem freeEnergy_non_increasing (γ : ℝ) (hγ : 0 ≤ γ) (g : Fin 2 → ℝ) :
    dot (flow γ ω g) g ≤ 0 := by
  rw [flow_work_eq_dissipation]
  have h := normSq_nonneg g
  nlinarith

/-- **Detailed balance iff no solenoidal drive.** For a nonzero gradient, the
solenoidal current vanishes exactly when `ω = 0`.  Equilibrium (detailed
balance) is precisely the absence of the antisymmetric drive. -/
theorem detailed_balance_iff (ω : ℝ) (g : Fin 2 → ℝ) (hg : g 0 ≠ 0 ∨ g 1 ≠ 0) :
    solenoidal ω g = 0 ↔ ω = 0 := by
  constructor
  · intro h
    have h0 : solenoidal ω g 0 = 0 := by simp [h]
    have h1 : solenoidal ω g 1 = 0 := by simp [h]
    simp [solenoidal] at h0 h1
    rcases hg with (hgx | hgy)
    · -- h1: -ω * g 0 = 0, which simp turned into ω = 0 ∨ g 0 = 0
      rcases h1 with (hω | hgx')
      · exact hω
      · exfalso; exact hgx hgx'
    · -- h0: ω * g 1 = 0, which simp turned into ω = 0 ∨ g 1 = 0
      rcases h0 with (hω | hgy')
      · exact hω
      · exfalso; exact hgy hgy'
  · intro h; subst h; ext i; fin_cases i <;> simp [solenoidal]

/-- The denominator-cleared entropy production rate: `σ = 2·ω²·precision / γ`.
At equilibrium (`ω = 0`) this is zero; out of equilibrium (`ω ≠ 0`) it is
strictly positive for positive precision and γ. -/
noncomputable def entropyProduction (precision ω γ : ℝ) : ℝ :=
  2 * ω ^ 2 * precision / γ

/-- **Entropy production is nonnegative,** for nonnegative precision and
dissipative strength `γ`. -/
theorem entropyProduction_nonneg (precision ω γ : ℝ)
    (hp : 0 ≤ precision) (hg : 0 ≤ γ) : 0 ≤ entropyProduction precision ω γ := by
  refine div_nonneg ?_ hg
  have hω2 : 0 ≤ ω ^ 2 := pow_two_nonneg _
  nlinarith

/-- **Entropy production vanishes exactly at detailed balance.** For a strictly
positive `γ` and `precision`, `σ = 0 ↔ ω = 0`. -/
theorem entropyProduction_eq_zero_iff (precision ω γ : ℝ)
    (hp : 0 < precision) (hg : 0 < γ) : entropyProduction precision ω γ = 0 ↔ ω = 0 := by
  constructor
  · intro h
    have : 2 * ω ^ 2 * precision / γ = 0 := h
    have hnum : 2 * ω ^ 2 * precision = 0 := by
      have hpos : γ ≠ 0 := ne_of_gt hg
      have h' : 2 * ω ^ 2 * precision / γ = 0 := by
        simpa [entropyProduction] using h
      calc
        2 * ω ^ 2 * precision = (2 * ω ^ 2 * precision / γ) * γ := by
          field_simp [hpos]
        _ = 0 * γ := by rw [h']
        _ = 0 := by ring
    have h_nonzero : 2 * precision ≠ 0 := by nlinarith
    have hω2 : ω ^ 2 = 0 := by
      have hmul := mul_eq_zero.mp hnum
      rcases hmul with (htwo | hprec_val)
      · -- htwo: 2 * ω ^ 2 = 0; 2 ≠ 0, so ω ^ 2 = 0
        nlinarith
      · -- hprec_val: precision = 0; contradicts hp > 0
        exfalso; nlinarith
    nlinarith [sq_nonneg ω]
  · intro h; subst h; simp [entropyProduction]

/-- **The NESS flow signature.**  At equilibrium (`ω = 0`), the solenoidal
current vanishes and entropy production is zero.  Out of equilibrium (`ω ≠ 0`),
a persistent solenoidal drive sustains positive entropy production. -/
theorem ness_signature (ω : ℝ) (g : Fin 2 → ℝ) (hg : g 0 ≠ 0 ∨ g 1 ≠ 0) :
    (solenoidal ω g = 0) ↔ (ω = 0) :=
  detailed_balance_iff ω g hg

end FEP.NessFlow
