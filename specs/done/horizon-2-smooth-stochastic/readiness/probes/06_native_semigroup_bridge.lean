import FepSketches.continuous_time_markov
import FepSketches.native_blanket
import Mathlib.InformationTheory.KullbackLeibler.DataProcessing
import Mathlib.Probability.Kernel.Invariance

open MeasureTheory ProbabilityTheory
open scoped ENNReal MeasureTheory ProbabilityTheory

private lemma lintegral_embeddedLaw_bool
    (law : FEP.FiniteLaw Bool) (observable : Bool -> ENNReal) :
    (∫⁻ state, observable state ∂FEP.NativeBlanket.embeddedLaw law) =
      ∑ state, ENNReal.ofReal (law state) * observable state := by
  rw [FEP.NativeBlanket.embeddedLaw]
  simp

-- H2-READINESS-ROW: native_kernel_algebra
example {A B C D : Type*}
    [MeasurableSpace A] [MeasurableSpace B]
    [MeasurableSpace C] [MeasurableSpace D]
    (latest : Kernel C D) (middle : Kernel B C) (earliest : Kernel A B)
    [IsMarkovKernel latest] [IsMarkovKernel middle]
    [IsMarkovKernel earliest] :
    latest ∘ₖ middle ∘ₖ earliest = latest ∘ₖ (middle ∘ₖ earliest) ∧
      IsMarkovKernel (latest ∘ₖ middle) := by
  exact ⟨Kernel.comp_assoc latest middle earliest,
    ProbabilityTheory.Kernel.IsMarkovKernel.comp latest middle⟩

-- H2-READINESS-ROW: native_invariance_kl_dpi
example {State : Type*} [MeasurableSpace State]
    (kernel : Kernel State State) [IsMarkovKernel kernel]
    (actual reference : Measure State)
    [IsFiniteMeasure actual] [IsFiniteMeasure reference]
    (hinvariant : Kernel.Invariant kernel reference) :
    InformationTheory.klDiv (kernel ∘ₘ actual) reference ≤
      InformationTheory.klDiv actual reference := by
  calc
    InformationTheory.klDiv (kernel ∘ₘ actual) reference =
        InformationTheory.klDiv
          (kernel ∘ₘ actual) (kernel ∘ₘ reference) := by
            rw [hinvariant.def]
    _ ≤ InformationTheory.klDiv actual reference :=
      InformationTheory.klDiv_comp_right_le actual reference kernel

-- H2-READINESS-ROW: exact_h1_embedded_lift
example (later earlier : FEP.FiniteKernel Bool Bool) :
    FEP.NativeBlanket.embeddedKernel
        (FEP.FiniteKernel.identity : FEP.FiniteKernel Bool Bool) =
        Kernel.id ∧
      FEP.NativeBlanket.embeddedKernel (FEP.FiniteKernel.comp later earlier) =
        FEP.NativeBlanket.embeddedKernel later ∘ₖ
          FEP.NativeBlanket.embeddedKernel earlier ∧
      ∀ action : Bool,
        FEP.NativeBlanket.embeddedKernel
            (FEP.ContinuousTimeMarkov.ActionIndexedSemigroup.sampledKernel
              FEP.ContinuousTimeMarkov.boolBlanketActionIndexedSemigroup action) =
          FEP.NativeBlanket.embeddedKernel
            ((FEP.ContinuousTimeMarkov.boolBlanketActionIndexedSemigroup.semigroup
              action).kernel
                (FEP.ContinuousTimeMarkov.boolBlanketActionIndexedSemigroup.sampleTime
                  action)
                (FEP.ContinuousTimeMarkov.boolBlanketActionIndexedSemigroup.sampleTime_nonneg
                  action)) := by
  constructor
  · apply Kernel.ext
    intro state
    apply Measure.ext_of_singleton
    intro target
    rw [FEP.NativeBlanket.embeddedKernel_apply_singleton,
      Kernel.id_apply, Measure.dirac_apply' _ (MeasurableSet.singleton target)]
    by_cases htarget : target = state
    · subst target
      simp [FEP.FiniteKernel.identity, FEP.FiniteKernel.deterministic]
    · simp [FEP.FiniteKernel.identity, FEP.FiniteKernel.deterministic,
        htarget, Ne.symm htarget]
  constructor
  · apply Kernel.ext
    intro state
    apply Measure.ext_of_singleton
    intro target
    rw [FEP.NativeBlanket.embeddedKernel_apply_singleton]
    rw [Kernel.comp_apply' _ _ _ (MeasurableSet.singleton target)]
    rw [FEP.NativeBlanket.embeddedKernel_apply,
      lintegral_embeddedLaw_bool]
    simp only [FEP.FiniteKernel.row,
      FEP.NativeBlanket.embeddedKernel_apply_singleton]
    change
      ENNReal.ofReal
          (∑ middle : Bool, earlier state middle * later middle target) =
        ∑ middle : Bool,
          ENNReal.ofReal (earlier state middle) *
            ENNReal.ofReal (later middle target)
    rw [ENNReal.ofReal_sum_of_nonneg]
    · apply Finset.sum_congr rfl
      intro middle _
      rw [ENNReal.ofReal_mul (earlier.nonneg state middle)]
    · intro middle _
      exact mul_nonneg (earlier.nonneg state middle)
        (later.nonneg middle target)
  · intro action
    rfl
