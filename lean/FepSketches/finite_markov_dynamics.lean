module
public import FepSketches.finite_probability
public import Mathlib.Tactic.Ring

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

/-! ## Event-weighted coarse-graining across all preparations -/

section WeightedCoarseGraining

variable {Target CoarseState CoarseTarget : Type*}
  [Fintype Target] [DecidableEq CoarseTarget]

/-- Unnormalized event-weighted mass in a coarse target block of a fine row. -/
noncomputable def weightedBlockRow (fine : FiniteKernel State Target)
    (weight : Target → ℝ) (targetLabel : Target → CoarseTarget)
    (x : State) (b : CoarseTarget) : ℝ :=
  ∑ y, if targetLabel y = b then fine x y * weight y else 0

/-- Preparation-averaged unnormalized weighted block mass. -/
noncomputable def weightedBlockMass (law : FiniteLaw State)
    (fine : FiniteKernel State Target) (weight : Target → ℝ)
    (targetLabel : Target → CoarseTarget) (b : CoarseTarget) : ℝ :=
  ∑ x, law x * weightedBlockRow fine weight targetLabel x b

/-- Reduced weighted rows averaged over the same fine preparation. -/
noncomputable def reducedWeightedBlockMass (law : FiniteLaw State)
    (sourceLabel : State → CoarseState) (reduced : CoarseState → CoarseTarget → ℝ)
    (b : CoarseTarget) : ℝ :=
  ∑ x, law x * reduced (sourceLabel x) b

/-- The row-average definition is exactly weighted predictive pushforward. -/
theorem weightedBlockMass_eq_pushforward (law : FiniteLaw State)
    (fine : FiniteKernel State Target) (weight : Target → ℝ)
    (targetLabel : Target → CoarseTarget) (b : CoarseTarget) :
    weightedBlockMass law fine weight targetLabel b =
      ∑ y, if targetLabel y = b then (fine.predictive law) y * weight y else 0 := by
  unfold weightedBlockMass weightedBlockRow
  simp_rw [Finset.mul_sum]
  rw [Finset.sum_comm]
  apply Finset.sum_congr rfl
  intro y _
  by_cases h : targetLabel y = b
  · simp only [h, ite_true, FiniteKernel.predictive_mass, Finset.sum_mul]
    apply Finset.sum_congr rfl
    intro x _
    ring
  · simp [h]

/-- Nonnegative event weights give nonnegative unnormalized coarse masses. -/
theorem weightedBlockMass_nonneg (law : FiniteLaw State)
    (fine : FiniteKernel State Target) (weight : Target → ℝ)
    (hWeight : ∀ y, 0 ≤ weight y) (targetLabel : Target → CoarseTarget)
    (b : CoarseTarget) : 0 ≤ weightedBlockMass law fine weight targetLabel b := by
  apply Finset.sum_nonneg
  intro x _
  apply mul_nonneg (law.nonneg x)
  apply Finset.sum_nonneg
  intro y _
  split
  · exact mul_nonneg (fine.nonneg x y) (hWeight y)
  · exact le_rfl

/-- Equality across every finite preparation is equivalent to rowwise equality.
Necessity uses point masses; sufficiency is finite-sum linearity. -/
theorem weightedBlockMass_forall_laws_iff_rowwise
    (fine : FiniteKernel State Target) (weight : Target → ℝ)
    (targetLabel : Target → CoarseTarget) (sourceLabel : State → CoarseState)
    (reduced : CoarseState → CoarseTarget → ℝ) :
    (∀ law : FiniteLaw State, ∀ b,
      weightedBlockMass law fine weight targetLabel b =
        reducedWeightedBlockMass law sourceLabel reduced b) ↔
    (∀ x b, weightedBlockRow fine weight targetLabel x b = reduced (sourceLabel x) b) := by
  classical
  constructor
  · intro h x b
    simpa [weightedBlockMass, reducedWeightedBlockMass, FiniteLaw.pointMass] using
      h (FiniteLaw.pointMass x) b
  · intro h law b
    unfold weightedBlockMass reducedWeightedBlockMass
    apply Finset.sum_congr rfl
    intro x _
    rw [h x b]

/-- Fibre-constant weights and lumpable movement give exact reduced weighted rows. -/
theorem weightedBlockRow_eq_of_lumpable [Fintype CoarseState] [Fintype CoarseTarget]
    (fine : FiniteKernel State Target) (coarseKernel : FiniteKernel CoarseState CoarseTarget)
    (sourceLabel : State → CoarseState) (targetLabel : Target → CoarseTarget)
    (weight : Target → ℝ) (coarseWeight : CoarseTarget → ℝ)
    (hFibre : ∀ y, weight y = coarseWeight (targetLabel y))
    (hLump : ∀ x b, (∑ y, if targetLabel y = b then fine x y else 0) =
      coarseKernel (sourceLabel x) b) (x : State) (b : CoarseTarget) :
    weightedBlockRow fine weight targetLabel x b =
      coarseKernel (sourceLabel x) b * coarseWeight b := by
  calc
    _ = (∑ y, if targetLabel y = b then fine x y else 0) * coarseWeight b := by
      rw [Finset.sum_mul]
      apply Finset.sum_congr rfl
      intro y _
      by_cases h : targetLabel y = b
      · simp [h, hFibre]
      · simp [h]
    _ = _ := by rw [hLump]

variable [Fintype CoarseTarget]

/-- Total unnormalized event evidence of a coarse block mass function. -/
noncomputable def weightedBlockEvidence (mass : CoarseTarget → ℝ) : ℝ := ∑ b, mass b

/-- Conditional coarse readout; claims use an explicit positive-evidence premise. -/
noncomputable def conditionalCoarseReadout (mass : CoarseTarget → ℝ) (b : CoarseTarget) : ℝ :=
  mass b / weightedBlockEvidence mass

/-- Rowwise equality preserves both evidence and positive-evidence readouts. -/
theorem weightedBlockMass_evidence_and_conditional
    (law : FiniteLaw State) (fine : FiniteKernel State Target) (weight : Target → ℝ)
    (targetLabel : Target → CoarseTarget) (sourceLabel : State → CoarseState)
    (reduced : CoarseState → CoarseTarget → ℝ)
    (hRows : ∀ x b, weightedBlockRow fine weight targetLabel x b = reduced (sourceLabel x) b) :
    weightedBlockEvidence (weightedBlockMass law fine weight targetLabel) =
      weightedBlockEvidence (reducedWeightedBlockMass law sourceLabel reduced) ∧
    (0 < weightedBlockEvidence (weightedBlockMass law fine weight targetLabel) →
      ∀ b, conditionalCoarseReadout (weightedBlockMass law fine weight targetLabel) b =
        conditionalCoarseReadout (reducedWeightedBlockMass law sourceLabel reduced) b) := by
  have hMass : weightedBlockMass law fine weight targetLabel =
      reducedWeightedBlockMass law sourceLabel reduced :=
    funext ((weightedBlockMass_forall_laws_iff_rowwise fine weight targetLabel sourceLabel reduced).mpr hRows law)
  rw [hMass]
  exact ⟨rfl, fun _ _ => rfl⟩

/-- Lumpable movement and fibre-constant nonnegative weights preserve evidence
and conditional readouts for every preparation at positive evidence. -/
theorem weightedBlockMass_lumpable_evidence_and_conditional [Fintype CoarseState]
    (law : FiniteLaw State) (fine : FiniteKernel State Target)
    (coarseKernel : FiniteKernel CoarseState CoarseTarget)
    (sourceLabel : State → CoarseState) (targetLabel : Target → CoarseTarget)
    (weight : Target → ℝ) (coarseWeight : CoarseTarget → ℝ)
    (hWeight : ∀ y, 0 ≤ weight y)
    (hFibre : ∀ y, weight y = coarseWeight (targetLabel y))
    (hLump : ∀ x b, (∑ y, if targetLabel y = b then fine x y else 0) =
      coarseKernel (sourceLabel x) b) :
    (∀ b, 0 ≤ weightedBlockMass law fine weight targetLabel b) ∧
    weightedBlockEvidence (weightedBlockMass law fine weight targetLabel) =
      weightedBlockEvidence (reducedWeightedBlockMass law sourceLabel
        (fun a b => coarseKernel a b * coarseWeight b)) ∧
    (0 < weightedBlockEvidence (weightedBlockMass law fine weight targetLabel) →
      ∀ b, conditionalCoarseReadout (weightedBlockMass law fine weight targetLabel) b =
        conditionalCoarseReadout (reducedWeightedBlockMass law sourceLabel
          (fun a b => coarseKernel a b * coarseWeight b)) b) :=
  ⟨weightedBlockMass_nonneg law fine weight hWeight targetLabel,
    weightedBlockMass_evidence_and_conditional law fine weight targetLabel sourceLabel _
      (weightedBlockRow_eq_of_lumpable fine coarseKernel sourceLabel targetLabel
        weight coarseWeight hFibre hLump)⟩

end WeightedCoarseGraining

/-- Hidden substates can have equal conditional coarse readout despite unequal
positive event evidence (survival multipliers 4/5 and 2/5). -/
theorem bool_conditional_equal_evidence_differs :
    let mass₁ := weightedBlockMass (FiniteLaw.pointMass true)
      (FiniteKernel.identity : FiniteKernel Bool Bool)
      (fun y => if y then (4 / 5 : ℝ) else 2 / 5) (fun _ => ())
    let mass₂ := weightedBlockMass (FiniteLaw.pointMass false)
      (FiniteKernel.identity : FiniteKernel Bool Bool)
      (fun y => if y then (4 / 5 : ℝ) else 2 / 5) (fun _ => ())
    weightedBlockEvidence mass₁ = 4 / 5 ∧ weightedBlockEvidence mass₂ = 2 / 5 ∧
    0 < weightedBlockEvidence mass₁ ∧ 0 < weightedBlockEvidence mass₂ ∧
    weightedBlockEvidence mass₁ ≠ weightedBlockEvidence mass₂ ∧
    (∀ b, conditionalCoarseReadout mass₁ b = conditionalCoarseReadout mass₂ b) := by
  norm_num [weightedBlockMass, weightedBlockRow, weightedBlockEvidence,
    conditionalCoarseReadout, FiniteLaw.pointMass, FiniteKernel.identity,
    FiniteKernel.deterministic, Fintype.sum_bool]

end FEP.FiniteMarkovDynamics
