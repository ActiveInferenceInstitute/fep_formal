module
public import FepSketches.continuous_time_markov
public import FepSketches.native_blanket
public import Mathlib.InformationTheory.KullbackLeibler.DataProcessing
public import Mathlib.Probability.Kernel.Invariance

@[expose] public section

/-!
# Native Markov-semigroup bridge

This module gives the repository one narrow certificate for an already-lawful
family of native Mathlib Markov kernels.  It stores only the zero and
Chapman--Kolmogorov laws, defines stationary and reversible-law predicates,
derives invariance from reversibility, and proves native KL contraction.  The
finite H1 semigroups lift by exact kernel equality; no
generator-existence or parallel action-transition claim is introduced.
-/

open MeasureTheory ProbabilityTheory
open scoped ENNReal MeasureTheory NNReal ProbabilityTheory

namespace FEP.MarkovSemigroup

/-- Semigroup laws for an already-Markov family of native kernels. -/
structure NativeKernelSemigroup {State : Type*} [MeasurableSpace State]
    (kernel : ℝ≥0 → Kernel State State)
    [∀ time, IsMarkovKernel (kernel time)] : Type where
  kernel_zero : kernel 0 = Kernel.id
  kernel_add : ∀ left right,
    kernel (left + right) = kernel right ∘ₖ kernel left

namespace NativeKernelSemigroup

variable {State : Type*} [MeasurableSpace State]
  {kernel : ℝ≥0 → Kernel State State}
  [∀ time, IsMarkovKernel (kernel time)]

/-- Embed every nonnegative slice of an H1 finite semigroup into Mathlib's
native kernel carrier. -/
noncomputable def embeddedFiniteKernelFamily
    [Fintype State] [DecidableEq State] [DiscreteMeasurableSpace State]
    (semigroup : FEP.ContinuousTimeMarkov.FiniteMarkovSemigroup State)
    (time : ℝ≥0) : Kernel State State :=
  FEP.NativeBlanket.embeddedKernel
    (semigroup.kernel time.1 time.2)

noncomputable instance embeddedFiniteKernelFamily_isMarkovKernel
    [Fintype State] [DecidableEq State] [DiscreteMeasurableSpace State]
    (semigroup : FEP.ContinuousTimeMarkov.FiniteMarkovSemigroup State)
    (time : ℝ≥0) :
    IsMarkovKernel (embeddedFiniteKernelFamily semigroup time) :=
  FEP.NativeBlanket.embeddedKernel_isMarkovKernel
    (semigroup.kernel time.1 time.2)

/-- Exact H1-to-native lift.  The proof consumes H2.4a's preservation of
identity and ordered composition. -/
noncomputable def liftFiniteMarkovSemigroup
    [Fintype State] [DecidableEq State] [DiscreteMeasurableSpace State]
    (semigroup : FEP.ContinuousTimeMarkov.FiniteMarkovSemigroup State) :
    NativeKernelSemigroup (embeddedFiniteKernelFamily semigroup) where
  kernel_zero := by
    change
      FEP.NativeBlanket.embeddedKernel (semigroup.kernel 0 _) = Kernel.id
    rw [FEP.ContinuousTimeMarkov.FiniteMarkovSemigroup.kernel_zero]
    exact FEP.NativeBlanket.embeddedKernel_identity
  kernel_add left right := by
    change
      FEP.NativeBlanket.embeddedKernel
          (semigroup.kernel ((left : ℝ) + (right : ℝ)) _) =
        FEP.NativeBlanket.embeddedKernel (semigroup.kernel (right : ℝ) _) ∘ₖ
          FEP.NativeBlanket.embeddedKernel (semigroup.kernel (left : ℝ) _)
    rw [FEP.ContinuousTimeMarkov.FiniteMarkovSemigroup.kernel_add]
    exact FEP.NativeBlanket.embeddedKernel_comp _ _

/-- A measure is invariant under every slice of the certified family. -/
def InvariantLaw (_semigroup : NativeKernelSemigroup kernel)
    (law : Measure State) : Prop :=
  ∀ time, Kernel.Invariant (kernel time) law

/-- A measure satisfies detailed balance under every slice. -/
def ReversibleLaw (_semigroup : NativeKernelSemigroup kernel)
    (law : Measure State) : Prop :=
  ∀ time, Kernel.IsReversible (kernel time) law

/-- Native reversibility implies invariance at every time. -/
theorem reversibleLaw_invariantLaw
    (semigroup : NativeKernelSemigroup kernel) (law : Measure State)
    (hReversible : ReversibleLaw semigroup law) :
    InvariantLaw semigroup law := by
  intro time
  exact (hReversible time).invariant

/-- Native KL cannot increase when both measures are evolved by the same
certified time slice. -/
theorem nativeKL_nonincrease
    (semigroup : NativeKernelSemigroup kernel)
    (earlier increment : ℝ≥0)
    (actual reference : Measure State)
    [IsFiniteMeasure actual] [IsFiniteMeasure reference] :
    InformationTheory.klDiv (kernel (earlier + increment) ∘ₘ actual)
        (kernel (earlier + increment) ∘ₘ reference) ≤
      InformationTheory.klDiv (kernel earlier ∘ₘ actual)
        (kernel earlier ∘ₘ reference) := by
  rw [semigroup.kernel_add earlier increment,
    ← Measure.comp_assoc, ← Measure.comp_assoc]
  exact InformationTheory.klDiv_comp_right_le
    (kernel earlier ∘ₘ actual) (kernel earlier ∘ₘ reference)
    (kernel increment)

/-- KL to a semigroup-invariant reference measure cannot increase. -/
theorem nativeKL_to_invariant_nonincrease
    (semigroup : NativeKernelSemigroup kernel)
    (earlier increment : ℝ≥0)
    (actual invariant : Measure State)
    [IsFiniteMeasure actual] [IsFiniteMeasure invariant]
    (hInvariant : InvariantLaw semigroup invariant) :
    InformationTheory.klDiv
        (kernel (earlier + increment) ∘ₘ actual) invariant ≤
      InformationTheory.klDiv (kernel earlier ∘ₘ actual) invariant := by
  calc
    InformationTheory.klDiv
        (kernel (earlier + increment) ∘ₘ actual) invariant =
        InformationTheory.klDiv
          (kernel (earlier + increment) ∘ₘ actual)
          (kernel (earlier + increment) ∘ₘ invariant) := by
      rw [(hInvariant (earlier + increment)).def]
    _ ≤ InformationTheory.klDiv (kernel earlier ∘ₘ actual)
          (kernel earlier ∘ₘ invariant) :=
      nativeKL_nonincrease semigroup earlier increment actual invariant
    _ = InformationTheory.klDiv (kernel earlier ∘ₘ actual) invariant := by
      rw [(hInvariant earlier).def]

/-- The lift uses the exact H1 time slice, not an isomorphic replacement. -/
theorem liftFiniteMarkovSemigroup_kernel
    [Fintype State] [DecidableEq State] [DiscreteMeasurableSpace State]
    (semigroup : FEP.ContinuousTimeMarkov.FiniteMarkovSemigroup State)
    (time : ℝ≥0) :
    embeddedFiniteKernelFamily semigroup time =
      FEP.NativeBlanket.embeddedKernel
        (semigroup.kernel time.1 time.2) :=
  rfl

end NativeKernelSemigroup

/-- An action selects an already-lawful native semigroup and the nonnegative
time at which it is sampled. -/
structure NativeActionIndexedKernelSemigroup
    (State Action : Type*) [MeasurableSpace State]
    (kernel : Action → ℝ≥0 → Kernel State State)
    [∀ action time, IsMarkovKernel (kernel action time)] where
  semigroup : ∀ action, NativeKernelSemigroup (kernel action)
  sampleTime : Action → ℝ≥0

namespace NativeActionIndexedKernelSemigroup

variable {State Action : Type*} [MeasurableSpace State]
  {kernel : Action → ℝ≥0 → Kernel State State}
  [∀ action time, IsMarkovKernel (kernel action time)]

/-- The native family obtained by embedding each H1 action/time slice. -/
noncomputable def embeddedActionKernelFamily
    [Fintype State] [DecidableEq State] [DiscreteMeasurableSpace State]
    [Fintype Action]
    (indexed : FEP.ContinuousTimeMarkov.ActionIndexedSemigroup State Action)
    (action : Action) (time : ℝ≥0) : Kernel State State :=
  NativeKernelSemigroup.embeddedFiniteKernelFamily
    (indexed.semigroup action) time

noncomputable instance embeddedActionKernelFamily_isMarkovKernel
    [Fintype State] [DecidableEq State] [DiscreteMeasurableSpace State]
    [Fintype Action]
    (indexed : FEP.ContinuousTimeMarkov.ActionIndexedSemigroup State Action)
    (action : Action) (time : ℝ≥0) :
    IsMarkovKernel (embeddedActionKernelFamily indexed action time) :=
  NativeKernelSemigroup.embeddedFiniteKernelFamily_isMarkovKernel
    (indexed.semigroup action) time

/-- Exact action-indexed lift preserving the H1 action and sample time. -/
noncomputable def liftActionIndexedSemigroup
    [Fintype State] [DecidableEq State] [DiscreteMeasurableSpace State]
    [Fintype Action]
    (indexed : FEP.ContinuousTimeMarkov.ActionIndexedSemigroup State Action) :
    NativeActionIndexedKernelSemigroup State Action
      (embeddedActionKernelFamily indexed) where
  semigroup action :=
    NativeKernelSemigroup.liftFiniteMarkovSemigroup
      (indexed.semigroup action)
  sampleTime action :=
    ⟨indexed.sampleTime action, indexed.sampleTime_nonneg action⟩

/-- Sample the same native family at the time selected by the action. -/
noncomputable def sampledKernel
    (indexed : NativeActionIndexedKernelSemigroup State Action kernel)
    (action : Action) : Kernel State State :=
  kernel action (indexed.sampleTime action)

/-- Every lifted action/time slice is literally the embedded H1 slice. -/
theorem liftActionIndexedSemigroup_kernel
    [Fintype State] [DecidableEq State] [DiscreteMeasurableSpace State]
    [Fintype Action]
    (indexed : FEP.ContinuousTimeMarkov.ActionIndexedSemigroup State Action)
    (action : Action) (time : ℝ≥0) :
    embeddedActionKernelFamily indexed action time =
      FEP.NativeBlanket.embeddedKernel
        ((indexed.semigroup action).kernel time.1 time.2) :=
  rfl

/-- The lifted sample time has exactly the H1 real value and nonnegativity
certificate. -/
theorem liftActionIndexedSemigroup_sampleTime
    [Fintype State] [DecidableEq State] [DiscreteMeasurableSpace State]
    [Fintype Action]
    (indexed : FEP.ContinuousTimeMarkov.ActionIndexedSemigroup State Action)
    (action : Action) :
    (((liftActionIndexedSemigroup indexed).sampleTime action : ℝ)) =
      indexed.sampleTime action :=
  rfl

/-- Sampling the lift is exactly embedding the H1 sampled finite kernel. -/
theorem liftActionIndexedSemigroup_sampledKernel
    [Fintype State] [DecidableEq State] [DiscreteMeasurableSpace State]
    [Fintype Action]
    (indexed : FEP.ContinuousTimeMarkov.ActionIndexedSemigroup State Action)
    (action : Action) :
    sampledKernel (liftActionIndexedSemigroup indexed) action =
      FEP.NativeBlanket.embeddedKernel (indexed.sampledKernel action) :=
  rfl

/-- Native lift of H1.7's exact right-associated Boolean blanket action
semigroup. -/
noncomputable def boolBlanketNativeActionIndexedSemigroup :
    NativeActionIndexedKernelSemigroup
      FEP.ContinuousTimeMarkov.BoolBlanketState Bool
      (embeddedActionKernelFamily
        FEP.ContinuousTimeMarkov.boolBlanketActionIndexedSemigroup) :=
  liftActionIndexedSemigroup
    FEP.ContinuousTimeMarkov.boolBlanketActionIndexedSemigroup

/-- The lifted `false` action is the native identity kernel. -/
theorem boolBlanketNativeActionIndexedSemigroup_false_kernel :
    sampledKernel boolBlanketNativeActionIndexedSemigroup false =
      (Kernel.id : Kernel FEP.ContinuousTimeMarkov.BoolBlanketState
        FEP.ContinuousTimeMarkov.BoolBlanketState) := by
  calc
    sampledKernel boolBlanketNativeActionIndexedSemigroup false =
        FEP.NativeBlanket.embeddedKernel
          (FEP.ContinuousTimeMarkov.ActionIndexedSemigroup.sampledKernel
            FEP.ContinuousTimeMarkov.boolBlanketActionIndexedSemigroup false) := by
      simpa [boolBlanketNativeActionIndexedSemigroup] using
        (liftActionIndexedSemigroup_sampledKernel
          FEP.ContinuousTimeMarkov.boolBlanketActionIndexedSemigroup false)
    _ = FEP.NativeBlanket.embeddedKernel
        (FEP.FiniteKernel.identity : FEP.FiniteKernel
          FEP.ContinuousTimeMarkov.BoolBlanketState
          FEP.ContinuousTimeMarkov.BoolBlanketState) := by
      rw [FEP.ContinuousTimeMarkov.boolBlanketActionIndexedSemigroup_false_kernel]
    _ = Kernel.id := FEP.NativeBlanket.embeddedKernel_identity

/-- The lifted `true` action is the exact embedded positive refresh kernel. -/
theorem boolBlanketNativeActionIndexedSemigroup_true_kernel :
    sampledKernel boolBlanketNativeActionIndexedSemigroup true =
      FEP.NativeBlanket.embeddedKernel
        FEP.ContinuousTimeMarkov.boolBlanketRefreshKernel := by
  calc
    sampledKernel boolBlanketNativeActionIndexedSemigroup true =
        FEP.NativeBlanket.embeddedKernel
          (FEP.ContinuousTimeMarkov.ActionIndexedSemigroup.sampledKernel
            FEP.ContinuousTimeMarkov.boolBlanketActionIndexedSemigroup true) := by
      simpa [boolBlanketNativeActionIndexedSemigroup] using
        (liftActionIndexedSemigroup_sampledKernel
          FEP.ContinuousTimeMarkov.boolBlanketActionIndexedSemigroup true)
    _ = FEP.NativeBlanket.embeddedKernel
        FEP.ContinuousTimeMarkov.boolBlanketRefreshKernel := by
      rw [FEP.ContinuousTimeMarkov.boolBlanketActionIndexedSemigroup_true_kernel]

/-- Hold and refresh remain distinct after exact native embedding. -/
theorem boolBlanketNativeActionIndexedSemigroup_kernels_ne :
    sampledKernel boolBlanketNativeActionIndexedSemigroup false ≠
      sampledKernel boolBlanketNativeActionIndexedSemigroup true := by
  rw [boolBlanketNativeActionIndexedSemigroup_false_kernel,
    boolBlanketNativeActionIndexedSemigroup_true_kernel]
  intro hEqual
  have hMass := congrArg
    (fun selected : Kernel FEP.ContinuousTimeMarkov.BoolBlanketState
        FEP.ContinuousTimeMarkov.BoolBlanketState =>
      selected FEP.ContinuousTimeMarkov.boolBlanketOrigin
        {FEP.ContinuousTimeMarkov.boolBlanketAlternative}) hEqual
  rw [Kernel.id_apply,
    Measure.dirac_apply' _
      (MeasurableSet.singleton
        FEP.ContinuousTimeMarkov.boolBlanketAlternative),
    FEP.NativeBlanket.embeddedKernel_apply_singleton] at hMass
  have hDifferent :
      FEP.ContinuousTimeMarkov.boolBlanketAlternative ≠
        FEP.ContinuousTimeMarkov.boolBlanketOrigin := by
    simp [FEP.ContinuousTimeMarkov.boolBlanketAlternative,
      FEP.ContinuousTimeMarkov.boolBlanketOrigin]
  simp [Ne.symm hDifferent] at hMass
  have hPositive :
      0 < FEP.ContinuousTimeMarkov.boolBlanketRefreshKernel
        FEP.ContinuousTimeMarkov.boolBlanketOrigin
        FEP.ContinuousTimeMarkov.boolBlanketAlternative := by
    simpa [FEP.ContinuousTimeMarkov.boolBlanketRefreshKernel,
      FEP.ContinuousTimeMarkov.FiniteMarkovSemigroup.kernel] using
      (FEP.ContinuousTimeMarkov.blanketRefreshSemigroup_transition_pos
        (Internal := Bool) (Sensory := Bool) (Active := Bool)
        (External := Bool)
        (by norm_num [FEP.ContinuousTimeMarkov.boolBlanketRefreshTime])
        FEP.ContinuousTimeMarkov.boolBlanketOrigin
        FEP.ContinuousTimeMarkov.boolBlanketAlternative)
  exact (not_le_of_gt hPositive) hMass

end NativeActionIndexedKernelSemigroup

export NativeActionIndexedKernelSemigroup
  (boolBlanketNativeActionIndexedSemigroup
   boolBlanketNativeActionIndexedSemigroup_false_kernel
   boolBlanketNativeActionIndexedSemigroup_kernels_ne
   boolBlanketNativeActionIndexedSemigroup_true_kernel
   embeddedActionKernelFamily
   liftActionIndexedSemigroup
   liftActionIndexedSemigroup_kernel
   liftActionIndexedSemigroup_sampleTime
   liftActionIndexedSemigroup_sampledKernel
   sampledKernel)

export NativeKernelSemigroup
  (InvariantLaw
   ReversibleLaw
   embeddedFiniteKernelFamily
   liftFiniteMarkovSemigroup
   liftFiniteMarkovSemigroup_kernel
   nativeKL_nonincrease
   nativeKL_to_invariant_nonincrease
   reversibleLaw_invariantLaw)

end FEP.MarkovSemigroup
