module
public import FepSketches.finite_probability

@[expose] public section

/-!
# Finite Markov dynamics

This module develops reusable dynamics for the normalized `FiniteLaw` and
`FiniteKernel` carriers.  It keeps three claims separate:

* algebraic kernel powers and Chapman--Kolmogorov composition;
* stationarity, detailed balance, and mass conservation; and
* total-variation contraction under an explicit Dobrushin bound.

The contraction coefficient is a proved contract supplied by a kernel, not an
implicitly inferred spectral quantity.  Downstream convergence theorems must
therefore expose the coefficient and its hypotheses.
-/

namespace FEP.FiniteMarkovDynamics

open FEP Finset
open scoped BigOperators

variable {State : Type*} [Fintype State]

/-! ## Kernel powers and Chapman--Kolmogorov -/

/-- Chronological `n`-step evolution of a homogeneous finite kernel. -/
def kernelPower [DecidableEq State]
    (kernel : FiniteKernel State State) : ℕ → FiniteKernel State State
  | 0 => FiniteKernel.identity
  | n + 1 => FiniteKernel.comp kernel (kernelPower kernel n)

@[simp]
theorem kernelPower_zero [DecidableEq State]
    (kernel : FiniteKernel State State) :
    kernelPower kernel 0 = FiniteKernel.identity := rfl

@[simp]
theorem kernelPower_succ [DecidableEq State]
    (kernel : FiniteKernel State State) (n : ℕ) :
    kernelPower kernel (n + 1) =
      FiniteKernel.comp kernel (kernelPower kernel n) := rfl

/-- A homogeneous kernel commutes with each of its finite powers. -/
theorem kernel_comp_power_comm [DecidableEq State]
    (kernel : FiniteKernel State State) (n : ℕ) :
    FiniteKernel.comp (kernelPower kernel n) kernel =
      FiniteKernel.comp kernel (kernelPower kernel n) := by
  induction n with
  | zero =>
      simp [kernelPower, FiniteKernel.comp_identity_left,
        FiniteKernel.comp_identity_right]
  | succ n ih =>
      simp only [kernelPower_succ]
      calc
        FiniteKernel.comp
            (FiniteKernel.comp kernel (kernelPower kernel n)) kernel =
            FiniteKernel.comp kernel
              (FiniteKernel.comp (kernelPower kernel n) kernel) :=
          (FiniteKernel.comp_assoc kernel (kernelPower kernel n) kernel).symm
        _ = FiniteKernel.comp kernel
              (FiniteKernel.comp kernel (kernelPower kernel n)) := by rw [ih]

/-- Finite Chapman--Kolmogorov: an `(m+n)`-step kernel is the composition of
the `n`-step evolution followed by the `m`-step evolution. -/
theorem kernelPower_add [DecidableEq State]
    (kernel : FiniteKernel State State) (m n : ℕ) :
    kernelPower kernel (m + n) =
      FiniteKernel.comp (kernelPower kernel m) (kernelPower kernel n) := by
  induction m with
  | zero =>
      simp [kernelPower, FiniteKernel.comp_identity_left]
  | succ m ih =>
      rw [Nat.succ_add]
      simp only [kernelPower_succ]
      rw [ih, FiniteKernel.comp_assoc]

/-! ## Invariance and reversibility -/

/-- A finite law is invariant when one predictive step leaves it unchanged. -/
def IsInvariant (law : FiniteLaw State)
    (kernel : FiniteKernel State State) : Prop :=
  kernel.predictive law = law

/-- Invariance is closed under chronological kernel composition. -/
theorem isInvariant_comp
    (law : FiniteLaw State)
    (later earlier : FiniteKernel State State)
    (hEarlier : IsInvariant law earlier)
    (hLater : IsInvariant law later) :
    IsInvariant law (FiniteKernel.comp later earlier) := by
  unfold IsInvariant at *
  rw [FiniteKernel.predictive_comp, hEarlier, hLater]

/-- An invariant law remains invariant under every finite kernel power. -/
theorem isInvariant_kernelPower [DecidableEq State]
    (law : FiniteLaw State) (kernel : FiniteKernel State State)
    (hInvariant : IsInvariant law kernel) (n : ℕ) :
    IsInvariant law (kernelPower kernel n) := by
  induction n with
  | zero =>
      simp [IsInvariant, kernelPower, FiniteKernel.predictive_identity]
  | succ n ih =>
      exact isInvariant_comp law kernel (kernelPower kernel n) ih hInvariant

/-- Finite detailed balance with respect to a reference law. -/
def IsReversible (law : FiniteLaw State)
    (kernel : FiniteKernel State State) : Prop :=
  ∀ source target,
    law source * kernel source target =
      law target * kernel target source

/-- The identity kernel is reversible with respect to every finite law. -/
theorem isReversible_identity [DecidableEq State]
    (law : FiniteLaw State) :
    IsReversible law (FiniteKernel.identity : FiniteKernel State State) := by
  intro source target
  by_cases h : source = target
  · subst target
    rfl
  · simp [FiniteKernel.identity, FiniteKernel.deterministic, h, Ne.symm h]

/-- Commuting reversible kernels have a reversible composition.  Commutativity
is essential here; arbitrary reversible kernels need not compose reversibly. -/
theorem isReversible_comp_of_commute
    (law : FiniteLaw State)
    (later earlier : FiniteKernel State State)
    (hEarlier : IsReversible law earlier)
    (hLater : IsReversible law later)
    (hCommute : FiniteKernel.comp later earlier =
      FiniteKernel.comp earlier later) :
    IsReversible law (FiniteKernel.comp later earlier) := by
  classical
  intro source target
  calc
    law source * FiniteKernel.comp later earlier source target =
        ∑ middle,
          law source *
            (earlier source middle * later middle target) := by
      simp [FiniteKernel.comp, Finset.mul_sum]
    _ = ∑ middle,
          law target *
            (later target middle * earlier middle source) := by
      apply Finset.sum_congr rfl
      intro middle _
      calc
        law source * (earlier source middle * later middle target) =
            (law source * earlier source middle) * later middle target := by
          ring
        _ = (law middle * earlier middle source) * later middle target := by
          rw [hEarlier source middle]
        _ = earlier middle source *
              (law middle * later middle target) := by ring
        _ = earlier middle source *
              (law target * later target middle) := by
          rw [hLater middle target]
        _ = law target *
              (later target middle * earlier middle source) := by ring
    _ = law target * FiniteKernel.comp earlier later target source := by
      simp [FiniteKernel.comp, Finset.mul_sum]
    _ = law target * FiniteKernel.comp later earlier target source := by
      rw [hCommute]

/-- Detailed balance is preserved by every finite homogeneous kernel power. -/
theorem isReversible_kernelPower [DecidableEq State]
    (law : FiniteLaw State) (kernel : FiniteKernel State State)
    (hReversible : IsReversible law kernel) (n : ℕ) :
    IsReversible law (kernelPower kernel n) := by
  induction n with
  | zero => exact isReversible_identity law
  | succ n ih =>
      exact isReversible_comp_of_commute law kernel (kernelPower kernel n)
        ih hReversible (kernel_comp_power_comm kernel n).symm

/-! ## Total variation and explicit Dobrushin contracts -/

/-- Total variation distance for normalized finite real laws. -/
noncomputable def totalVariation (left right : FiniteLaw State) : ℝ :=
  (1 / 2 : ℝ) * ∑ state, |left state - right state|

/-- Finite total variation is nonnegative. -/
theorem totalVariation_nonneg (left right : FiniteLaw State) :
    0 ≤ totalVariation left right := by
  unfold totalVariation
  positivity

/-- A law has zero total-variation distance from itself. -/
@[simp]
theorem totalVariation_self (law : FiniteLaw State) :
    totalVariation law law = 0 := by
  simp [totalVariation]

/-- `coefficient` is an explicit Dobrushin upper bound for the kernel's
total-variation Lipschitz constant. -/
def HasDobrushinBound (kernel : FiniteKernel State State)
    (coefficient : ℝ) : Prop :=
  0 ≤ coefficient ∧
    ∀ left right,
      totalVariation (kernel.predictive left) (kernel.predictive right) ≤
        coefficient * totalVariation left right

/-- Dobrushin bounds multiply under chronological kernel composition. -/
theorem hasDobrushinBound_comp
    (later earlier : FiniteKernel State State)
    {laterCoefficient earlierCoefficient : ℝ}
    (hLater : HasDobrushinBound later laterCoefficient)
    (hEarlier : HasDobrushinBound earlier earlierCoefficient) :
    HasDobrushinBound (FiniteKernel.comp later earlier)
      (laterCoefficient * earlierCoefficient) := by
  constructor
  · exact mul_nonneg hLater.1 hEarlier.1
  · intro left right
    calc
      totalVariation
          ((FiniteKernel.comp later earlier).predictive left)
          ((FiniteKernel.comp later earlier).predictive right) =
          totalVariation
            (later.predictive (earlier.predictive left))
            (later.predictive (earlier.predictive right)) := by
        rw [FiniteKernel.predictive_comp, FiniteKernel.predictive_comp]
      totalVariation
          (later.predictive (earlier.predictive left))
          (later.predictive (earlier.predictive right)) ≤
          laterCoefficient *
            totalVariation (earlier.predictive left) (earlier.predictive right) :=
        hLater.2 (earlier.predictive left) (earlier.predictive right)
      _ ≤ laterCoefficient *
            (earlierCoefficient * totalVariation left right) :=
        mul_le_mul_of_nonneg_left (hEarlier.2 left right) hLater.1
      _ = (laterCoefficient * earlierCoefficient) *
            totalVariation left right := by ring

/-- The identity kernel has Dobrushin bound one. -/
theorem hasDobrushinBound_identity [DecidableEq State] :
    HasDobrushinBound
      (FiniteKernel.identity : FiniteKernel State State) 1 := by
  constructor
  · norm_num
  · intro left right
    rw [FiniteKernel.predictive_identity, FiniteKernel.predictive_identity,
      one_mul]

/-- An explicit one-step Dobrushin bound yields its geometric `n`-step bound. -/
theorem hasDobrushinBound_kernelPower [DecidableEq State]
    (kernel : FiniteKernel State State) {coefficient : ℝ}
    (hBound : HasDobrushinBound kernel coefficient) (n : ℕ) :
    HasDobrushinBound (kernelPower kernel n) (coefficient ^ n) := by
  induction n with
  | zero =>
      simpa [kernelPower] using
        (hasDobrushinBound_identity (State := State))
  | succ n ih =>
      simpa [kernelPower, pow_succ, mul_comm] using
        hasDobrushinBound_comp kernel (kernelPower kernel n) hBound ih

/-- The corresponding geometric total-variation contraction inequality. -/
theorem totalVariation_kernelPower_le [DecidableEq State]
    (kernel : FiniteKernel State State) {coefficient : ℝ}
    (hBound : HasDobrushinBound kernel coefficient)
    (left right : FiniteLaw State) (n : ℕ) :
    totalVariation
        ((kernelPower kernel n).predictive left)
        ((kernelPower kernel n).predictive right) ≤
      coefficient ^ n * totalVariation left right :=
  (hasDobrushinBound_kernelPower kernel hBound n).2 left right

/-! ## Finite master equation -/

/-- One-step gain-minus-loss increment of a finite master equation. -/
def masterIncrement (law : FiniteLaw State)
    (kernel : FiniteKernel State State) (state : State) : ℝ :=
  kernel.predictive law state - law state

/-- Every normalized finite master-equation step conserves total mass. -/
theorem masterIncrement_sum_zero
    (law : FiniteLaw State) (kernel : FiniteKernel State State) :
    ∑ state, masterIncrement law kernel state = 0 := by
  classical
  unfold masterIncrement
  rw [Finset.sum_sub_distrib, (kernel.predictive law).sum_one, law.sum_one]
  exact sub_self 1

/-- The master increment reconstructs the exact next predictive mass. -/
theorem masterIncrement_add_current
    (law : FiniteLaw State) (kernel : FiniteKernel State State)
    (state : State) :
    masterIncrement law kernel state + law state =
      kernel.predictive law state := by
  simp [masterIncrement]

end FEP.FiniteMarkovDynamics
