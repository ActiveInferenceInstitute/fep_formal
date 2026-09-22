import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Algebra.BigOperators.Ring.Finset
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Data.Fintype.BigOperators
import Mathlib.Data.Fintype.Card
import Mathlib.Basic.Real.Basic
import Mathlib.Tactic

/-!
# Finite probability laws and kernels

This module supplies one normalized real-valued carrier for the finite-state
parts of the FEP and active-inference development.  Nonnegativity and total
mass one are construction fields, so downstream definitions cannot silently
accept arbitrary weight vectors as probability laws.
-/

namespace FEP

open Finset
open scoped BigOperators

/-- A probability law on a finite type, represented by normalized real mass. -/
structure FiniteLaw (α : Type*) [Fintype α] where
  mass : α → ℝ
  nonneg : ∀ x, 0 ≤ mass x
  sum_one : ∑ x, mass x = 1

namespace FiniteLaw

variable {α β γ : Type*} [Fintype α] [Fintype β] [Fintype γ]

instance : CoeFun (FiniteLaw α) (fun _ => α → ℝ) := ⟨FiniteLaw.mass⟩

@[simp]
theorem coe_mass (p : FiniteLaw α) (x : α) : p x = p.mass x := rfl

/-- Finite laws are equal when their mass functions are equal. -/
@[ext]
theorem ext_mass {p q : FiniteLaw α} (h : p.mass = q.mass) : p = q := by
  cases p
  cases q
  cases h
  rfl

/-- Every atom of a finite law lies in the unit interval. -/
theorem mass_le_one (p : FiniteLaw α) (x : α) : p x ≤ 1 := by
  classical
  calc
    p x ≤ ∑ y : α, p y :=
      Finset.single_le_sum (fun y _ => p.nonneg y) (Finset.mem_univ x)
    _ = 1 := p.sum_one

/-- Every atom of a finite law lies in `[0,1]`. -/
theorem mass_mem_Icc (p : FiniteLaw α) (x : α) : p x ∈ Set.Icc (0 : ℝ) 1 :=
  ⟨p.nonneg x, p.mass_le_one x⟩

/-- The point mass at one finite state. -/
def pointMass [DecidableEq α] (chosen : α) : FiniteLaw α where
  mass x := if x = chosen then 1 else 0
  nonneg x := by split <;> positivity
  sum_one := by simp

/-- The uniform law on a nonempty finite type. -/
noncomputable def uniform [Nonempty α] : FiniteLaw α where
  mass _ := (Fintype.card α : ℝ)⁻¹
  nonneg _ := by positivity
  sum_one := by
    simp [Fintype.card_ne_zero]

/-- Independent product of two finite laws. -/
def product (p : FiniteLaw α) (q : FiniteLaw β) : FiniteLaw (α × β) where
  mass xy := p xy.1 * q xy.2
  nonneg xy := mul_nonneg (p.nonneg xy.1) (q.nonneg xy.2)
  sum_one := by
    classical
    rw [Fintype.sum_prod_type]
    simp_rw [← Finset.mul_sum, q.sum_one, mul_one]
    exact p.sum_one

/-- First marginal of a finite joint law. -/
def fstMarginal (p : FiniteLaw (α × β)) : FiniteLaw α where
  mass x := ∑ y : β, p (x, y)
  nonneg x := Finset.sum_nonneg fun y _ => p.nonneg (x, y)
  sum_one := by
    simpa [Fintype.sum_prod_type] using p.sum_one

/-- Second marginal of a finite joint law. -/
def sndMarginal (p : FiniteLaw (α × β)) : FiniteLaw β where
  mass y := ∑ x : α, p (x, y)
  nonneg y := Finset.sum_nonneg fun x _ => p.nonneg (x, y)
  sum_one := by
    rw [Finset.sum_comm]
    simpa [Fintype.sum_prod_type] using p.sum_one

/-- The first marginal of an independent product is its first factor. -/
theorem product_fstMarginal_mass (p : FiniteLaw α) (q : FiniteLaw β)
    (x : α) :
    (p.product q).fstMarginal x = p x := by
  simp [fstMarginal, product, ← Finset.mul_sum, q.sum_one]

/-- The second marginal of an independent product is its second factor. -/
theorem product_sndMarginal_mass (p : FiniteLaw α) (q : FiniteLaw β)
    (y : β) :
    (p.product q).sndMarginal y = q y := by
  simp [sndMarginal, product, ← Finset.sum_mul, p.sum_one]

/-- Independent products reconstruct their first factor as a law. -/
theorem product_fstMarginal (p : FiniteLaw α) (q : FiniteLaw β) :
    (p.product q).fstMarginal = p := by
  apply ext_mass
  funext x
  exact product_fstMarginal_mass p q x

/-- Independent products reconstruct their second factor as a law. -/
theorem product_sndMarginal (p : FiniteLaw α) (q : FiniteLaw β) :
    (p.product q).sndMarginal = q := by
  apply ext_mass
  funext y
  exact product_sndMarginal_mass p q y

/-- Push a finite law through a deterministic function. -/
def map [DecidableEq β] (f : α → β) (p : FiniteLaw α) : FiniteLaw β := by
  exact
    { mass := fun y => ∑ x : α, if f x = y then p x else 0
      nonneg := fun y => Finset.sum_nonneg fun x _ => by
        by_cases h : f x = y
        · simpa [h] using p.nonneg x
        · simp [h]
      sum_one := by
        rw [Finset.sum_comm]
        simpa using p.sum_one }

@[simp]
theorem map_mass [DecidableEq β] (f : α → β) (p : FiniteLaw α) (y : β) :
    p.map f y = ∑ x : α, if f x = y then p x else 0 := rfl

/-- Mapping by the identity function preserves a finite law pointwise. -/
theorem map_id_mass [DecidableEq α] (p : FiniteLaw α) (x : α) :
    p.map id x = p x := by
  change (∑ x' : α, if x' = x then p x' else 0) = p x
  rw [Finset.sum_ite_eq']
  simp

end FiniteLaw

/-- A normalized finite Markov kernel. -/
structure FiniteKernel (α β : Type*) [Fintype α] [Fintype β] where
  mass : α → β → ℝ
  nonneg : ∀ x y, 0 ≤ mass x y
  sum_one : ∀ x, ∑ y, mass x y = 1

namespace FiniteKernel

variable {α β γ : Type*} [Fintype α] [Fintype β] [Fintype γ]

instance : CoeFun (FiniteKernel α β) (fun _ => α → β → ℝ) :=
  ⟨FiniteKernel.mass⟩

/-- Finite kernels are equal when their mass functions are equal. -/
@[ext]
theorem ext_mass {kernel₁ kernel₂ : FiniteKernel α β}
    (h : kernel₁.mass = kernel₂.mass) : kernel₁ = kernel₂ := by
  cases kernel₁
  cases kernel₂
  cases h
  rfl

/-- Each input of a normalized kernel indexes a finite output law. -/
def row (kernel : FiniteKernel α β) (x : α) : FiniteLaw β where
  mass y := kernel x y
  nonneg y := kernel.nonneg x y
  sum_one := kernel.sum_one x

/-- Deterministic transition kernel induced by a function. -/
def deterministic [DecidableEq β] (f : α → β) : FiniteKernel α β where
  mass x y := if y = f x then 1 else 0
  nonneg x y := by split <;> positivity
  sum_one x := by simp

/-- Identity transition on a finite state space. -/
def identity [DecidableEq α] : FiniteKernel α α := deterministic id

/-- Sequential composition of normalized finite kernels. -/
def comp (later : FiniteKernel β γ) (earlier : FiniteKernel α β) :
    FiniteKernel α γ where
  mass x z := ∑ y : β, earlier x y * later y z
  nonneg x z := Finset.sum_nonneg fun y _ =>
    mul_nonneg (earlier.nonneg x y) (later.nonneg y z)
  sum_one x := by
    rw [Finset.sum_comm]
    simp [← Finset.mul_sum, later.sum_one, earlier.sum_one]

/-- Composition of normalized finite kernels is associative. -/
theorem comp_assoc {δ : Type*} [Fintype δ]
    (latest : FiniteKernel γ δ) (middle : FiniteKernel β γ)
    (earliest : FiniteKernel α β) :
    comp latest (comp middle earliest) =
      comp (comp latest middle) earliest := by
  apply ext_mass
  funext x z
  simp only [comp]
  simp_rw [Finset.sum_mul, Finset.mul_sum, mul_assoc]
  rw [Finset.sum_comm]

/-- An identity transition before a kernel leaves that kernel unchanged. -/
theorem comp_identity_right [DecidableEq α] (kernel : FiniteKernel α β) :
    comp kernel identity = kernel := by
  apply ext_mass
  funext x y
  simp [comp, identity, deterministic]

/-- An identity transition after a kernel leaves that kernel unchanged. -/
theorem comp_identity_left [DecidableEq β] (kernel : FiniteKernel α β) :
    comp identity kernel = kernel := by
  apply ext_mass
  funext x y
  simp [comp, identity, deterministic]

/-- Joint law generated by a prior and a normalized finite kernel. -/
def joint (prior : FiniteLaw α) (kernel : FiniteKernel α β) :
    FiniteLaw (α × β) where
  mass xy := prior xy.1 * kernel xy.1 xy.2
  nonneg xy := mul_nonneg (prior.nonneg xy.1) (kernel.nonneg xy.1 xy.2)
  sum_one := by
    classical
    rw [Fintype.sum_prod_type]
    simp_rw [← Finset.mul_sum, kernel.sum_one, mul_one]
    exact prior.sum_one

/-- Predictive output law obtained by marginalizing a prior-kernel joint. -/
def predictive (prior : FiniteLaw α) (kernel : FiniteKernel α β) : FiniteLaw β :=
  (joint prior kernel).sndMarginal

@[simp]
theorem predictive_mass (prior : FiniteLaw α) (kernel : FiniteKernel α β)
    (y : β) :
    predictive prior kernel y = ∑ x : α, prior x * kernel x y := rfl

/-- Prediction commutes with sequential kernel composition. -/
theorem predictive_comp (prior : FiniteLaw α)
    (later : FiniteKernel β γ) (earlier : FiniteKernel α β) :
    (comp later earlier).predictive prior =
      later.predictive (earlier.predictive prior) := by
  apply FiniteLaw.ext_mass
  funext z
  simp only [predictive_mass, comp]
  simp_rw [Finset.sum_mul, Finset.mul_sum, mul_assoc]
  rw [Finset.sum_comm]

/-- Prediction through the identity transition preserves the prior law. -/
theorem predictive_identity [DecidableEq α] (prior : FiniteLaw α) :
    identity.predictive prior = prior := by
  apply FiniteLaw.ext_mass
  funext x
  simp [predictive_mass, identity, deterministic]

/-- Exact finite Bayes posterior at evidence with positive predictive mass. -/
noncomputable def posterior (prior : FiniteLaw α) (kernel : FiniteKernel α β)
    (y : β) (hy : 0 < predictive prior kernel y) : FiniteLaw α where
  mass x := prior x * kernel x y / predictive prior kernel y
  nonneg x := div_nonneg (mul_nonneg (prior.nonneg x) (kernel.nonneg x y)) hy.le
  sum_one := by
    rw [← Finset.sum_div]
    exact div_self (ne_of_gt hy)

/-- Bayes reconstruction: posterior mass times evidence equals joint mass. -/
theorem posterior_mul_predictive (prior : FiniteLaw α)
    (kernel : FiniteKernel α β) (y : β)
    (hy : 0 < predictive prior kernel y) (x : α) :
    posterior prior kernel y hy x * predictive prior kernel y =
      prior x * kernel x y := by
  change
    (prior x * kernel x y / predictive prior kernel y) *
        predictive prior kernel y = _
  exact div_mul_cancel₀ _ (ne_of_gt hy)

/-- The generated joint's first marginal reconstructs its prior. -/
theorem joint_fstMarginal_mass (prior : FiniteLaw α)
    (kernel : FiniteKernel α β) (x : α) :
    (joint prior kernel).fstMarginal x = prior x := by
  simp [FiniteLaw.fstMarginal, joint, ← Finset.mul_sum, kernel.sum_one]

end FiniteKernel

end FEP
