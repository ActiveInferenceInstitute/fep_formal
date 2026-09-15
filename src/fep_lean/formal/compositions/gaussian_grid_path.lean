import FepSketches.scalar_gaussian_semigroup
import Mathlib.InformationTheory.KullbackLeibler.Basic
import Mathlib.MeasureTheory.Integral.Bochner.Basic
import Mathlib.MeasureTheory.Measure.Decomposition.RadonNikodym
import Mathlib.Probability.Kernel.IonescuTulcea.PartialTraj

/-!
# Native finite-grid paths for the scalar Gaussian semigroup

This composition builds only a finite discrete grid from the accepted scalar
OU transition.  Its comparison law is the forward law mapped through a
coordinate-reversal involution; it is not asserted to be an independently
constructed reverse dynamics.  Native KL statements retain absolute-
continuity and log-ratio integrability boundaries explicitly.
-/

open Finset MeasureTheory ProbabilityTheory
open scoped BoundedContinuousFunction ENNReal MeasureTheory NNReal ProbabilityTheory

namespace FEPComposed.GaussianGridPath

noncomputable section

open FEP.ScalarGaussianSemigroup

/-- A nondecreasing sequence of finite-grid observation times.

Repeated times are permitted and produce the zero-duration identity transition.
Descending schedules cannot be constructed, so `NNReal` subtraction never
silently repairs a backward step.
-/
structure TimeGrid where
  time : ℕ → ℝ≥0
  monotone_time : Monotone time

/-- The state at every finite grid coordinate is real-valued. -/
abbrev GaussianGridState : ℕ → Type := fun _ => ℝ

/-- A real-valued path through grid coordinate `n`, inclusive. -/
abbrev GridPath (n : ℕ) := Π i : Iic n, GaussianGridState i

/-- The next-state OU kernel, read from the final coordinate of the input path. -/
noncomputable def ouGridStep
    (model : ScalarOUParameters) (grid : TimeGrid) (n : ℕ) :
    Kernel (GridPath n) (GaussianGridState (n + 1)) :=
  (model.ouTransition (grid.time (n + 1) - grid.time n)).comap
    (fun path => path ⟨n, mem_Iic.mpr le_rfl⟩) (by fun_prop)

noncomputable instance ouGridStep_isMarkovKernel
    (model : ScalarOUParameters) (grid : TimeGrid) (n : ℕ) :
    IsMarkovKernel (ouGridStep model grid n) := by
  unfold ouGridStep
  infer_instance

/-- Exact Mathlib finite-grid trajectory kernel for the OU step family. -/
noncomputable def ouPartialTraj
    (model : ScalarOUParameters) (grid : TimeGrid) (a b : ℕ) :
    Kernel (GridPath a) (GridPath b) :=
  Kernel.partialTraj (ouGridStep model grid) a b

noncomputable instance ouPartialTraj_isMarkovKernel
    (model : ScalarOUParameters) (grid : TimeGrid) (a b : ℕ) :
    IsMarkovKernel (ouPartialTraj model grid a b) := by
  unfold ouPartialTraj
  infer_instance

/-- Later grid segments compose on the left of earlier segments. -/
theorem ouPartialTraj_comp
    (model : ScalarOUParameters) (grid : TimeGrid)
    {a b c : ℕ} (hab : a ≤ b) (hbc : b ≤ c) :
    ouPartialTraj model grid b c ∘ₖ ouPartialTraj model grid a b =
      ouPartialTraj model grid a c := by
  exact Kernel.partialTraj_comp_partialTraj hab hbc

/-- Stationary initialization, embedded into the singleton grid coordinate. -/
noncomputable def initialGridLaw
    (model : ScalarOUParameters) : Measure (GridPath 0) :=
  model.stationaryLaw.map (fun state _ => state)

noncomputable instance initialGridLaw_isProbabilityMeasure
    (model : ScalarOUParameters) : IsProbabilityMeasure (initialGridLaw model) := by
  unfold initialGridLaw
  exact (Measure.isProbabilityMeasure_map_iff (by fun_prop)).mpr (by infer_instance)

/-- Forward path law from the stationary singleton coordinate through the grid. -/
noncomputable def forwardGridLaw
    (model : ScalarOUParameters) (grid : TimeGrid) (n : ℕ) :
    Measure (GridPath n) :=
  ouPartialTraj model grid 0 n ∘ₘ initialGridLaw model

noncomputable instance forwardGridLaw_isProbabilityMeasure
    (model : ScalarOUParameters) (grid : TimeGrid) (n : ℕ) :
    IsProbabilityMeasure (forwardGridLaw model grid n) := by
  unfold forwardGridLaw
  infer_instance

/-- The forward finite-grid path law is normalized. -/
theorem forwardGridLaw_normalized
    (model : ScalarOUParameters) (grid : TimeGrid) (n : ℕ) :
    forwardGridLaw model grid n Set.univ = 1 :=
  measure_univ

/-- Reverse only the coordinate order of a finite path. -/
def reverseGridPath (n : ℕ) (path : GridPath n) : GridPath n :=
  fun i => path ⟨n - i.1, mem_Iic.mpr (Nat.sub_le n i.1)⟩

/-- Coordinate reversal is measurable on the finite real product. -/
theorem reverseGridPath_measurable (n : ℕ) : Measurable (reverseGridPath n) := by
  refine Measurable.of_eval fun i => ?_
  change Measurable
    (fun path : GridPath n =>
      path ⟨n - i.1, mem_Iic.mpr (Nat.sub_le n i.1)⟩)
  exact measurable_pi_apply _

/-- Reversing finite-grid coordinates twice recovers the original path. -/
theorem reverseGridPath_involutive (n : ℕ) :
    Function.Involutive (reverseGridPath n) := by
  intro path
  funext i
  simp only [reverseGridPath]
  congr 1
  apply Subtype.ext
  exact Nat.sub_sub_self (mem_Iic.mp i.2)

/-- Forward law aligned to reversed coordinates; no reverse dynamics is asserted. -/
noncomputable def reverseAlignedGridLaw
    (model : ScalarOUParameters) (grid : TimeGrid) (n : ℕ) :
    Measure (GridPath n) :=
  Measure.map (reverseGridPath n) (forwardGridLaw model grid n)

noncomputable instance reverseAlignedGridLaw_isProbabilityMeasure
    (model : ScalarOUParameters) (grid : TimeGrid) (n : ℕ) :
    IsProbabilityMeasure (reverseAlignedGridLaw model grid n) := by
  unfold reverseAlignedGridLaw
  exact (Measure.isProbabilityMeasure_map_iff
    (reverseGridPath_measurable n).aemeasurable).mpr (by infer_instance)

/-- The coordinate-reversed comparison law is normalized. -/
theorem reverseAlignedGridLaw_normalized
    (model : ScalarOUParameters) (grid : TimeGrid) (n : ℕ) :
    reverseAlignedGridLaw model grid n Set.univ = 1 :=
  measure_univ

/-- Integrating after coordinate reversal is exactly integration of the reversed observable. -/
theorem integral_reverseAlignedGridLaw
    (model : ScalarOUParameters) (grid : TimeGrid) (n : ℕ)
    (f : GridPath n →ᵇ ℝ) :
    (∫ path, f path ∂reverseAlignedGridLaw model grid n) =
      ∫ path, f (reverseGridPath n path) ∂forwardGridLaw model grid n := by
  rw [reverseAlignedGridLaw,
    integral_map_of_stronglyMeasurable (reverseGridPath_measurable n)
      f.continuous.stronglyMeasurable]

/-- Native forward-to-coordinate-reversed path divergence. -/
noncomputable def gridPathKL
    (model : ScalarOUParameters) (grid : TimeGrid) (n : ℕ) : ℝ≥0∞ :=
  InformationTheory.klDiv
    (forwardGridLaw model grid n) (reverseAlignedGridLaw model grid n)

/-- RN derivative as a ratio through any common sigma-finite dominating measure. -/
theorem rnDeriv_forward_reverseAligned_eq_ratio
    (model : ScalarOUParameters) (grid : TimeGrid) (n : ℕ)
    (dominating : Measure (GridPath n)) [SigmaFinite dominating]
    (hForward : forwardGridLaw model grid n ≪ dominating)
    (hReverse : reverseAlignedGridLaw model grid n ≪ dominating) :
    (forwardGridLaw model grid n).rnDeriv
        (reverseAlignedGridLaw model grid n) =ᵐ[reverseAlignedGridLaw model grid n]
      fun path =>
        (forwardGridLaw model grid n).rnDeriv dominating path /
          (reverseAlignedGridLaw model grid n).rnDeriv dominating path := by
  exact Measure.rnDeriv_eq_div hForward hReverse

/-- Under support and integrability, native grid KL is the expected real log ratio. -/
theorem gridPathKL_eq_expectedLogRatio
    (model : ScalarOUParameters) (grid : TimeGrid) (n : ℕ)
    (hAC : forwardGridLaw model grid n ≪ reverseAlignedGridLaw model grid n)
    (hIntegrable : Integrable
      (MeasureTheory.llr (forwardGridLaw model grid n)
        (reverseAlignedGridLaw model grid n))
      (forwardGridLaw model grid n)) :
    gridPathKL model grid n = ENNReal.ofReal
      (∫ path, MeasureTheory.llr (forwardGridLaw model grid n)
          (reverseAlignedGridLaw model grid n) path
        ∂forwardGridLaw model grid n) := by
  rw [gridPathKL,
    InformationTheory.klDiv_of_ac_of_integrable hAC hIntegrable]
  simp [measureReal_def]

/-- Gibbs' inequality for the real expected forward log ratio. -/
theorem expectedLogRatio_nonneg
    (model : ScalarOUParameters) (grid : TimeGrid) (n : ℕ)
    (hAC : forwardGridLaw model grid n ≪ reverseAlignedGridLaw model grid n)
    (hIntegrable : Integrable
      (MeasureTheory.llr (forwardGridLaw model grid n)
        (reverseAlignedGridLaw model grid n))
      (forwardGridLaw model grid n)) :
    0 ≤ ∫ path, MeasureTheory.llr (forwardGridLaw model grid n)
        (reverseAlignedGridLaw model grid n) path
      ∂forwardGridLaw model grid n := by
  simpa [measureReal_def] using
    InformationTheory.integral_llr_add_sub_measure_univ_nonneg hAC hIntegrable

/-- Support failure makes native path divergence infinite. -/
theorem gridPathKL_eq_top_of_not_ac
    (model : ScalarOUParameters) (grid : TimeGrid) (n : ℕ)
    (hNotAC : ¬ forwardGridLaw model grid n ≪
      reverseAlignedGridLaw model grid n) :
    gridPathKL model grid n = ∞ := by
  exact InformationTheory.klDiv_of_not_ac hNotAC

/-- A nonintegrable forward log ratio also makes native path divergence infinite. -/
theorem gridPathKL_eq_top_of_not_integrable
    (model : ScalarOUParameters) (grid : TimeGrid) (n : ℕ)
    (hNotIntegrable : ¬ Integrable
      (MeasureTheory.llr (forwardGridLaw model grid n)
        (reverseAlignedGridLaw model grid n))
      (forwardGridLaw model grid n)) :
    gridPathKL model grid n = ∞ := by
  exact InformationTheory.klDiv_of_not_integrable hNotIntegrable

end

end FEPComposed.GaussianGridPath
