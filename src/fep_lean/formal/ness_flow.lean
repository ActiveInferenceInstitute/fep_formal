module
public import Mathlib.Algebra.Order.Ring.Unbundled.Basic
public import Mathlib.Basic.Real.Basic
public import Mathlib.Analysis.Calculus.FDeriv.Symmetric
public import Mathlib.Analysis.Calculus.FDeriv.Pow
public import Mathlib.Analysis.SpecialFunctions.ExpDeriv
public import FepSketches.geometric_mechanics
public import Mathlib.Tactic

@[expose] public section

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

/-! ## Fokker–Planck stationarity of `p = exp (-F)` (Euclidean calculus)

Smooth-density counterpart of the `Fin 2` scalar carrier above, on `Fin n → ℝ`
with Fréchet derivatives and no stochastic process.  For a `C²` potential `F`,
constant `Γ`, `Q`, density `p = exp (-F)`, drift `f = -(Γ + Q) ∇F` and
probability current `J = p f - Γ ∇p`, the dissipative part cancels
pointwise, `J = -p · Q ∇F`, and `div J = 0` exactly when `Q` is
skew-symmetric (the Hessian of a `C²` function is symmetric).  Hence
`∂ₜ p = -div J = 0`: `p` is stationary for the Fokker–Planck equation.
-/

section FokkerPlanck

variable {n : ℕ}

/-- Gradient components `∇F x i = DF(x) eᵢ`. -/
noncomputable def gradF (F : (Fin n → ℝ) → ℝ) (x : Fin n → ℝ) : Fin n → ℝ :=
  fun i => fderiv ℝ F x (Pi.single i 1)

/-- Hessian components `∂ᵢ∂ₖ F x = D²F(x) eᵢ eₖ`. -/
noncomputable def hessF (F : (Fin n → ℝ) → ℝ) (x : Fin n → ℝ) (i k : Fin n) : ℝ :=
  fderiv ℝ (fderiv ℝ F) x (Pi.single i 1) (Pi.single k 1)

/-- The stationary density `p x = exp (-F x)`. -/
noncomputable def density (F : (Fin n → ℝ) → ℝ) (x : Fin n → ℝ) : ℝ :=
  Real.exp (-F x)

/-- Entrywise sum of two plain real matrices. -/
def addMat (Γ Q : Fin n → Fin n → ℝ) : Fin n → Fin n → ℝ := fun i j => Γ i j + Q i j

/-- The Helmholtz drift `f x = -(Γ + Q) ∇F x`. -/
noncomputable def drift (F : (Fin n → ℝ) → ℝ) (Γ Q : Fin n → Fin n → ℝ)
    (x : Fin n → ℝ) : Fin n → ℝ :=
  fun i => -GeometricMechanics.mulVec (addMat Γ Q) (gradF F x) i

/-- The probability current `J x = p x • f x - Γ ∇p x`. -/
noncomputable def probCurrent (F : (Fin n → ℝ) → ℝ) (Γ Q : Fin n → Fin n → ℝ)
    (x : Fin n → ℝ) : Fin n → ℝ :=
  fun i => density F x * drift F Γ Q x i
    - GeometricMechanics.mulVec Γ (gradF (density F) x) i

/-- Euclidean divergence `div V x = ∑ᵢ ∂ᵢ Vᵢ x`. -/
noncomputable def divergence (V : (Fin n → ℝ) → Fin n → ℝ) (x : Fin n → ℝ) : ℝ :=
  ∑ i, fderiv ℝ (fun y => V y i) x (Pi.single i 1)

/-- The Fokker–Planck right-hand side `∂ₜ p = -div J` (the diffusion and drift
terms are already folded into `J`). -/
noncomputable def fpRate (F : (Fin n → ℝ) → ℝ) (Γ Q : Fin n → Fin n → ℝ)
    (x : Fin n → ℝ) : ℝ :=
  -divergence (probCurrent F Γ Q) x

/-- `∇p = -p ∇F` for `p = exp (-F)`. -/
theorem gradF_density (F : (Fin n → ℝ) → ℝ) (x : Fin n → ℝ)
    (hF : DifferentiableAt ℝ F x) :
    gradF (density F) x = fun i => -(density F x) * gradF F x i := by
  have h : HasFDerivAt (density F) (density F x • (-(fderiv ℝ F x))) x :=
    hF.hasFDerivAt.neg.exp
  funext i
  simp [gradF, h.fderiv]

/-- **(1) Pointwise current identity.** `J x = -p x • (Q ∇F x)`: the
dissipative `Γ` terms cancel identically (no symmetry of `Γ`, `Q` needed). -/
theorem probCurrent_eq (F : (Fin n → ℝ) → ℝ) (Γ Q : Fin n → Fin n → ℝ)
    (x : Fin n → ℝ) (hF : DifferentiableAt ℝ F x) :
    probCurrent F Γ Q x
      = fun i => -(density F x) * GeometricMechanics.mulVec Q (gradF F x) i := by
  funext i
  have hΓ : ∑ k, Γ i k * (-density F x * gradF F x k)
      = -(density F x * ∑ k, Γ i k * gradF F x k) := by
    rw [Finset.mul_sum, ← Finset.sum_neg_distrib]
    exact Finset.sum_congr rfl fun k _ => by ring
  simp only [probCurrent, drift, gradF_density F x hF, GeometricMechanics.mulVec, addMat,
    add_mul, Finset.sum_add_distrib, hΓ]
  ring

/-- **(2) The `Q` term does no work**: `(Q ∇F) · ∇F = 0` for skew `Q`. -/
theorem qGradient_orthogonal (F : (Fin n → ℝ) → ℝ) (Q : Fin n → Fin n → ℝ)
    (hQ : GeometricMechanics.SkewSymmetric Q) (x : Fin n → ℝ) :
    GeometricMechanics.dot (GeometricMechanics.mulVec Q (gradF F x)) (gradF F x) = 0 := by
  have h := GeometricMechanics.skewQuadratic_eq_zero Q (gradF F x) hQ
  simpa [GeometricMechanics.dot, mul_comm] using h

/-- Derivative of a gradient component of a `C²` function. -/
theorem hasFDerivAt_gradF (F : (Fin n → ℝ) → ℝ) (hF : ContDiff ℝ 2 F)
    (x : Fin n → ℝ) (k : Fin n) :
    HasFDerivAt (fun y => gradF F y k)
      ((fderiv ℝ (fderiv ℝ F) x).flip (Pi.single k 1)) x := by
  have hd : DifferentiableAt ℝ (fderiv ℝ F) x :=
    ((hF.fderiv_right (m := 1) (by norm_num)).differentiable (by norm_num)) x
  have := hd.hasFDerivAt.clm_apply (hasFDerivAt_const (Pi.single k (1 : ℝ) : Fin n → ℝ) x)
  simpa [gradF] using this

/-- Mixed second derivatives as directional derivatives of gradient components. -/
theorem hessF_eq_fderiv_gradF (F : (Fin n → ℝ) → ℝ) (hF : ContDiff ℝ 2 F)
    (x : Fin n → ℝ) (i k : Fin n) :
    hessF F x i k = fderiv ℝ (fun y => gradF F y k) x (Pi.single i 1) := by
  rw [(hasFDerivAt_gradF F hF x k).fderiv]
  rfl

/-- The Hessian components of a `C²` function are symmetric (Schwarz). -/
theorem hessF_symmetric (F : (Fin n → ℝ) → ℝ) (hF : ContDiff ℝ 2 F)
    (x : Fin n → ℝ) : GeometricMechanics.SymmetricOf (hessF F x) := by
  intro i k
  have h := hF.contDiffAt.isSymmSndFDerivAt (x := x) (by simp)
  exact h _ _

/-- The skew contraction against a symmetric matrix vanishes entrywise-summed. -/
theorem skew_contract_symm (Q H : Fin n → Fin n → ℝ)
    (hQ : GeometricMechanics.SkewSymmetric Q) (hH : GeometricMechanics.SymmetricOf H) :
    ∑ i, ∑ k, Q i k * H i k = 0 := by
  have h := GeometricMechanics.skewTrace_eq_zero Q H hQ hH
  simp only [GeometricMechanics.traceOf, GeometricMechanics.mulOf] at h
  rw [← h]
  refine Finset.sum_congr rfl fun i _ => Finset.sum_congr rfl fun k _ => ?_
  rw [hH i k]

/-- The `Q`-part of the current, `i`-th component: `p · (Q ∇F)ᵢ`. -/
noncomputable def qCurrent (F : (Fin n → ℝ) → ℝ) (Q : Fin n → Fin n → ℝ)
    (y : Fin n → ℝ) (i : Fin n) : ℝ :=
  density F y * GeometricMechanics.mulVec Q (gradF F y) i

/-- Product-rule expansion of `∂ᵢ (p (Q∇F)ᵢ)`. -/
theorem fderiv_qCurrent (F : (Fin n → ℝ) → ℝ) (hF : ContDiff ℝ 2 F)
    (Q : Fin n → Fin n → ℝ) (x : Fin n → ℝ) (i : Fin n) :
    fderiv ℝ (fun y => qCurrent F Q y i) x (Pi.single i 1)
      = -(density F x * gradF F x i * GeometricMechanics.mulVec Q (gradF F x) i)
        + density F x * ∑ k, Q i k * hessF F x i k := by
  have hdiff : DifferentiableAt ℝ F x := (hF.differentiable (by norm_num)) x
  have hp : HasFDerivAt (density F) (density F x • (-(fderiv ℝ F x))) x :=
    hdiff.hasFDerivAt.neg.exp
  have hs : HasFDerivAt (fun y => GeometricMechanics.mulVec Q (gradF F y) i)
      (∑ k, Q i k • (fderiv ℝ (fderiv ℝ F) x).flip (Pi.single k 1)) x := by
    unfold GeometricMechanics.mulVec
    exact HasFDerivAt.fun_sum fun k _ => (hasFDerivAt_gradF F hF x k).const_mul (Q i k)
  have := (hp.mul hs).fderiv
  unfold qCurrent
  rw [show (fun y => density F y * GeometricMechanics.mulVec Q (gradF F y) i)
      = density F * (fun y => GeometricMechanics.mulVec Q (gradF F y) i) from rfl, this]
  simp [hessF, gradF, GeometricMechanics.mulVec]
  ring

/-- Divergence of the current for arbitrary constant `Γ`, `Q`:
`div J = p (∇F · Q∇F) - p ∑ᵢₖ Qᵢₖ ∂ᵢ∂ₖF`. -/
theorem divergence_probCurrent_eq (F : (Fin n → ℝ) → ℝ) (hF : ContDiff ℝ 2 F)
    (Γ Q : Fin n → Fin n → ℝ) (x : Fin n → ℝ) :
    divergence (probCurrent F Γ Q) x
      = density F x * GeometricMechanics.dot (gradF F x) (GeometricMechanics.mulVec Q (gradF F x))
        - density F x * ∑ i, ∑ k, Q i k * hessF F x i k := by
  have hfun : ∀ i, (fun y => probCurrent F Γ Q y i) = fun y => -(qCurrent F Q y i) := by
    intro i; funext y
    rw [probCurrent_eq F Γ Q y ((hF.differentiable (by norm_num)) y)]
    simp [qCurrent]
  have hterm : ∀ i, fderiv ℝ (fun y => probCurrent F Γ Q y i) x (Pi.single i 1)
      = density F x * (gradF F x i * GeometricMechanics.mulVec Q (gradF F x) i)
        - density F x * ∑ k, Q i k * hessF F x i k := by
    intro i
    rw [hfun i, fderiv_fun_neg, neg_apply, fderiv_qCurrent F hF Q x i]
    ring
  unfold divergence
  simp only [hterm, Finset.sum_sub_distrib, ← Finset.mul_sum]
  rfl

/-- **(3) The current is divergence-free** for skew `Q` and `C²` `F`. -/
theorem divergence_probCurrent_eq_zero (F : (Fin n → ℝ) → ℝ) (hF : ContDiff ℝ 2 F)
    (Γ Q : Fin n → Fin n → ℝ) (hQ : GeometricMechanics.SkewSymmetric Q)
    (x : Fin n → ℝ) : divergence (probCurrent F Γ Q) x = 0 := by
  rw [divergence_probCurrent_eq F hF Γ Q x,
    skew_contract_symm Q _ hQ (hessF_symmetric F hF x),
    GeometricMechanics.skewQuadratic_eq_zero Q _ hQ]
  ring

/-- **Fokker–Planck stationarity**: `∂ₜ p = -div J = 0`. -/
theorem fpRate_eq_zero (F : (Fin n → ℝ) → ℝ) (hF : ContDiff ℝ 2 F)
    (Γ Q : Fin n → Fin n → ℝ) (hQ : GeometricMechanics.SkewSymmetric Q)
    (x : Fin n → ℝ) : fpRate F Γ Q x = 0 := by
  simp [fpRate, divergence_probCurrent_eq_zero F hF Γ Q hQ x]

/-! ### Concrete `n = 2` witnesses -/

/-- The Gaussian potential `F x = (x₀² + x₁²) / 2`. -/
noncomputable def gaussF : (Fin 2 → ℝ) → ℝ := fun x => (x 0 ^ 2 + x 1 ^ 2) / 2

/-- Unit dissipation matrix. -/
def gammaId : Fin 2 → Fin 2 → ℝ := fun i j => if i = j then 1 else 0

/-- The skew rotation `Q = [[0,1],[-1,0]]`. -/
def qRot : Fin 2 → Fin 2 → ℝ := fun i j =>
  if i = 0 ∧ j = 1 then 1 else if i = 1 ∧ j = 0 then -1 else 0

/-- The non-skew matrix `Q = [[1,0],[0,0]]`. -/
def qNonSkew : Fin 2 → Fin 2 → ℝ := fun i j => if i = 0 ∧ j = 0 then 1 else 0

theorem gaussF_contDiff : ContDiff ℝ 2 gaussF := by
  unfold gaussF; fun_prop

theorem gradF_gaussF (y : Fin 2 → ℝ) : gradF gaussF y = y := by
  funext i
  have h : HasFDerivAt gaussF
      ((y 0 : ℝ) • (ContinuousLinearMap.proj 0 : (Fin 2 → ℝ) →L[ℝ] ℝ)
        + (y 1 : ℝ) • (ContinuousLinearMap.proj 1 : (Fin 2 → ℝ) →L[ℝ] ℝ)) y := by
    have h0 := ((hasFDerivAt_apply (𝕜 := ℝ) (0 : Fin 2) y).pow 2)
    have h1 := ((hasFDerivAt_apply (𝕜 := ℝ) (1 : Fin 2) y).pow 2)
    have h := (h0.add h1).const_mul (1 / 2 : ℝ)
    have e : gaussF = fun y => (1 / 2 : ℝ) * (y 0 ^ 2 + y 1 ^ 2) := by
      funext y; simp [gaussF]; ring
    rw [e]
    refine h.congr_fderiv (ContinuousLinearMap.ext fun z => ?_)
    simp
    ring
  unfold gradF
  rw [h.fderiv]
  fin_cases i <;> simp

theorem hessF_gaussF (x : Fin 2 → ℝ) (i k : Fin 2) :
    hessF gaussF x i k = if i = k then 1 else 0 := by
  rw [hessF_eq_fderiv_gradF gaussF gaussF_contDiff x i k]
  have : (fun y => gradF gaussF y k) = fun y => y k := funext fun y => by rw [gradF_gaussF]
  rw [this, (hasFDerivAt_apply k x).fderiv]
  simp [Pi.single_apply, eq_comm]

/-- **(4a) Non-skew countermodel.** With `Q = [[1,0],[0,0]]` (not skew), the
Gaussian potential and `Γ = I`, the divergence at the origin is `-1 ≠ 0`:
skew-symmetry of `Q` cannot be dropped. -/
theorem nonSkew_divergence_ne_zero :
    divergence (probCurrent gaussF gammaId qNonSkew) (fun _ => 0) ≠ 0 := by
  rw [divergence_probCurrent_eq gaussF gaussF_contDiff]
  simp [gradF_gaussF, hessF_gaussF, GeometricMechanics.dot, qNonSkew, density, gaussF]

/-- **(4b) Gaussian witness with nonzero circulation.** With the skew rotation
`Q = [[0,1],[-1,0]] ≠ 0`, the current at `(0,1)` is nonzero, yet it is
divergence-free there. -/
theorem rotation_current_ne_zero_divergence_zero :
    probCurrent gaussF gammaId qRot ![0, 1] ≠ 0 ∧
      divergence (probCurrent gaussF gammaId qRot) ![0, 1] = 0 := by
  refine ⟨?_, divergence_probCurrent_eq_zero gaussF gaussF_contDiff _ _ ?_ _⟩
  · intro h
    have h0 := congrFun h 0
    rw [probCurrent_eq gaussF gammaId qRot _ (gaussF_contDiff.differentiable (by norm_num) _)] at h0
    simp [gradF_gaussF, GeometricMechanics.mulVec, qRot, density, gaussF] at h0
  · intro i j
    fin_cases i <;> fin_cases j <;> simp [qRot]

end FokkerPlanck

end FEP.NessFlow
