module
public import Mathlib.InformationTheory.KullbackLeibler.Basic
public import Mathlib.MeasureTheory.Integral.Bochner.SumMeasure
import Mathlib.Tactic

/-! Unaccepted standalone probe. Uses only Mathlib, no FEP carrier or namespace.
For general finite weights this is Mathlib's mass-corrected divergence; ordinary
probability KL is recovered only when both weights sum to one. -/

@[expose] public section

open MeasureTheory ProbabilityTheory
open scoped BigOperators ENNReal MeasureTheory ProbabilityTheory

namespace InformationTheory

noncomputable def finiteWeightMeasure {α : Type*} [Fintype α] [MeasurableSpace α]
    (p : α → ℝ) : Measure α :=
  Measure.sum fun x => ENNReal.ofReal (p x) • Measure.dirac x

instance {α : Type*} [Fintype α] [MeasurableSpace α] (p : α → ℝ) :
    IsFiniteMeasure (finiteWeightMeasure p) where
  measure_univ_lt_top := by
    simp only [finiteWeightMeasure, Measure.sum_apply_of_countable, tsum_fintype,
      Measure.smul_apply, Measure.dirac_apply_of_mem (Set.mem_univ _), smul_eq_mul,
      mul_one]
    exact ENNReal.sum_lt_top.mpr fun _ _ => ENNReal.ofReal_lt_top

@[simp] theorem finiteWeightMeasure_singleton {α : Type*} [Fintype α]
    [MeasurableSpace α] [DiscreteMeasurableSpace α] (p : α → ℝ) (x : α) :
    finiteWeightMeasure p {x} = ENNReal.ofReal (p x) := by
  simpa [finiteWeightMeasure] using
    (Measure.sum_smul_dirac_singleton (f := fun a : α => ENNReal.ofReal (p a)) (a := x))

theorem finiteWeightMeasure_withDensity_ratio {α : Type*} [Fintype α]
    [MeasurableSpace α] [DiscreteMeasurableSpace α] (p q : α → ℝ)
    (hp : ∀ x, 0 ≤ p x) (hq : ∀ x, 0 ≤ q x)
    (hsupport : ∀ x, p x ≠ 0 → 0 < q x) :
    (finiteWeightMeasure q).withDensity (fun x => ENNReal.ofReal (p x / q x)) =
      finiteWeightMeasure p := by
  classical
  apply Measure.ext_of_singleton
  intro x
  rw [withDensity_apply _ MeasurableSet.of_discrete, lintegral_singleton,
    finiteWeightMeasure_singleton, finiteWeightMeasure_singleton,
    ← ENNReal.ofReal_mul (div_nonneg (hp x) (hq x))]
  by_cases hzero : q x = 0
  · have hpzero : p x = 0 := by
      by_contra hne
      exact (ne_of_gt (hsupport x hne)) hzero
    simp [hzero, hpzero]
  · rw [div_mul_cancel₀ _ hzero]

theorem klDiv_finiteWeightMeasure {α : Type*} [Fintype α]
    [MeasurableSpace α] [DiscreteMeasurableSpace α] (p q : α → ℝ)
    (hp : ∀ x, 0 ≤ p x) (hq : ∀ x, 0 ≤ q x)
    (hsupport : ∀ x, p x ≠ 0 → 0 < q x) :
    klDiv (finiteWeightMeasure p) (finiteWeightMeasure q) =
      ENNReal.ofReal (∑ x, q x * klFun (p x / q x)) := by
  have hDensity := finiteWeightMeasure_withDensity_ratio p q hp hq hsupport
  have hAC : finiteWeightMeasure p ≪ finiteWeightMeasure q := by
    rw [← hDensity]
    exact withDensity_absolutelyContinuous _ _
  rw [klDiv_eq_lintegral_klFun_of_ac hAC]
  have hRN :
      (finiteWeightMeasure p).rnDeriv (finiteWeightMeasure q) =ᵐ[finiteWeightMeasure q]
        fun x => ENNReal.ofReal (p x / q x) := by
    rw [← hDensity]
    exact Measure.rnDeriv_withDensity _ (by fun_prop)
  have hIntegrand :
      (fun x => ENNReal.ofReal
        (klFun ((finiteWeightMeasure p).rnDeriv (finiteWeightMeasure q) x).toReal))
          =ᵐ[finiteWeightMeasure q]
        fun x => ENNReal.ofReal (klFun (p x / q x)) := by
    filter_upwards [hRN] with x hx
    rw [hx, ENNReal.toReal_ofReal (div_nonneg (hp x) (hq x))]
  rw [lintegral_congr_ae hIntegrand, lintegral_fintype,
    ENNReal.ofReal_sum_of_nonneg]
  · apply Finset.sum_congr rfl
    intro x _
    rw [finiteWeightMeasure_singleton, ENNReal.ofReal_mul (hq x), mul_comm]
  · intro x _
    exact mul_nonneg (hq x) (klFun_nonneg (div_nonneg (hp x) (hq x)))

theorem finiteWeightMeasure_probability {α : Type*} [Fintype α]
    [MeasurableSpace α] (p : α → ℝ) (hp : ∀ x, 0 ≤ p x)
    (hnormalized : ∑ x, p x = 1) : IsProbabilityMeasure (finiteWeightMeasure p) where
  measure_univ := by
    simp only [finiteWeightMeasure, Measure.sum_apply_of_countable, tsum_fintype,
      Measure.smul_apply, Measure.dirac_apply_of_mem (Set.mem_univ _), smul_eq_mul,
      mul_one]
    rw [← ENNReal.ofReal_sum_of_nonneg (fun x _ => hp x), hnormalized]
    simp

end InformationTheory

namespace FiniteWeightKLControls

open InformationTheory

def pointWeight (b x : Bool) : ℝ := if x = b then 1 else 0

theorem pointWeight_nonneg (b x : Bool) : 0 ≤ pointWeight b x := by
  cases b <;> cases x <;> norm_num [pointWeight]

/-- Shared zero atoms are permitted: normalized sparse laws have native KL zero. -/
theorem sparse_shared_zero_control :
    klDiv (finiteWeightMeasure (pointWeight true))
      (finiteWeightMeasure (pointWeight true)) = 0 := by
  rw [klDiv_finiteWeightMeasure _ _ (pointWeight_nonneg true)
    (pointWeight_nonneg true) (by intro x; cases x <;> simp [pointWeight])]
  norm_num [Fintype.sum_bool, pointWeight, klFun_one, klFun_zero]

theorem sparse_normalization_control :
    IsProbabilityMeasure (finiteWeightMeasure (pointWeight true)) := by
  exact finiteWeightMeasure_probability _ (pointWeight_nonneg true)
    (by norm_num [Fintype.sum_bool, pointWeight])

/-- Actual mass outside reference support retains native infinity. -/
theorem singular_infinity_control :
    klDiv (finiteWeightMeasure (pointWeight true))
      (finiteWeightMeasure (pointWeight false)) = ∞ := by
  apply klDiv_of_not_ac
  intro hAC
  have hReferenceZero :
      finiteWeightMeasure (pointWeight false) ({true} : Set Bool) = 0 := by
    simp [pointWeight]
  have hActualZero := hAC hReferenceZero
  norm_num [pointWeight] at hActualZero

theorem singular_relative_support_rejected :
    ¬ (∀ x, pointWeight true x ≠ 0 → 0 < pointWeight false x) := by
  intro h
  have impossible := h true (by norm_num [pointWeight])
  norm_num [pointWeight] at impossible

/-- Unequal unnormalized masses include the native mass correction. -/
theorem unnormalized_mass_correction_control :
    klDiv (finiteWeightMeasure (fun _ : Unit => (2 : ℝ)))
      (finiteWeightMeasure (fun _ : Unit => (1 : ℝ))) =
        ENNReal.ofReal (2 * Real.log 2 - 1) := by
  rw [klDiv_finiteWeightMeasure _ _ (by intro; norm_num)
    (by intro; norm_num) (by intro; norm_num)]
  congr 1
  simp [klFun_apply]
  ring

theorem unequal_mass_not_normalized_control :
    (∑ _ : Unit, (2 : ℝ)) ≠ 1 := by norm_num

theorem mass_correction_not_uncorrected_score :
    (2 : ℝ) * Real.log 2 - 1 ≠ 2 * Real.log 2 := by linarith

noncomputable def positiveActual (b : Bool) : ℝ := if b then 3 / 4 else 1 / 4
noncomputable def positiveReference (_ : Bool) : ℝ := 1 / 2

/-- Nonidentical normalized full-support laws exercise a finite nonzero native KL. -/
theorem normalized_positive_nontrivial_control :
    IsProbabilityMeasure (finiteWeightMeasure positiveActual) ∧
    IsProbabilityMeasure (finiteWeightMeasure positiveReference) ∧
    klDiv (finiteWeightMeasure positiveActual) (finiteWeightMeasure positiveReference) ≠ 0 ∧
    klDiv (finiteWeightMeasure positiveActual) (finiteWeightMeasure positiveReference) =
      ENNReal.ofReal (∑ x, positiveReference x * klFun (positiveActual x / positiveReference x)) := by
  have hp : ∀ b, 0 ≤ positiveActual b := by intro b; cases b <;> norm_num [positiveActual]
  have hq : ∀ b, 0 ≤ positiveReference b := by intro b; norm_num [positiveReference]
  have hsupport : ∀ b, positiveActual b ≠ 0 → 0 < positiveReference b := by
    intro b _; norm_num [positiveReference]
  have hne : finiteWeightMeasure positiveActual ≠ finiteWeightMeasure positiveReference := by
    intro heq
    have hsingle := congrArg (fun m : Measure Bool => m ({true} : Set Bool)) heq
    norm_num [positiveActual, positiveReference] at hsingle
  refine ⟨finiteWeightMeasure_probability _ hp ?_,
    finiteWeightMeasure_probability _ hq ?_, ?_,
    klDiv_finiteWeightMeasure _ _ hp hq hsupport⟩
  · norm_num [Fintype.sum_bool, positiveActual]
  · norm_num [Fintype.sum_bool, positiveReference]
  · intro hzero
    exact hne (klDiv_eq_zero_iff.mp hzero)

#print axioms InformationTheory.klDiv_finiteWeightMeasure
#print axioms InformationTheory.finiteWeightMeasure_probability
#print axioms sparse_shared_zero_control
#print axioms sparse_normalization_control
#print axioms singular_infinity_control
#print axioms singular_relative_support_rejected
#print axioms unnormalized_mass_correction_control
#print axioms unequal_mass_not_normalized_control
#print axioms mass_correction_not_uncorrected_score
#print axioms normalized_positive_nontrivial_control

end FiniteWeightKLControls
