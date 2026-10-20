module
public import FepSketches.decision_risk
import Mathlib.Tactic

@[expose] public section
open MeasureTheory ProbabilityTheory
open scoped BigOperators ENNReal MeasureTheory ProbabilityTheory
namespace FiniteWeightKLControls

open InformationTheory FEP.FiniteInformation

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

#print axioms FEP.FiniteInformation.finiteWeightMeasure_withDensity_ratio
#print axioms FEP.FiniteInformation.finiteWeightMeasure_probability
#print axioms sparse_shared_zero_control
#print axioms sparse_normalization_control
#print axioms singular_infinity_control
#print axioms singular_relative_support_rejected
#print axioms unnormalized_mass_correction_control
#print axioms unequal_mass_not_normalized_control
#print axioms mass_correction_not_uncorrected_score
#print axioms normalized_positive_nontrivial_control

end FiniteWeightKLControls

namespace ExistingFiniteKLConsumer
open FEP FEP.FiniteInformation FEP.NativeBlanket FEP.DecisionRisk
variable {α : Type*} [Fintype α] [MeasurableSpace α] [DiscreteMeasurableSpace α]
omit [DiscreteMeasurableSpace α] in
/-- Generic weighted measure is definitionally the existing finite-law embedding. -/
theorem embedding_defeq (p : FiniteLaw α) : finiteWeightMeasure p = embeddedLaw p := rfl
example (p q : FiniteLaw α) (h : ∀ x, p x ≠ 0 → 0 < q x) :
    (embeddedLaw q).withDensity (fun x => ENNReal.ofReal (p x / q x)) = embeddedLaw p :=
  embeddedLaw_withDensity_ratio_of_relativeSupport p q h
example (p q : FiniteLaw α) (h : ∀ x, p x ≠ 0 → 0 < q x) :
    InformationTheory.klDiv (embeddedLaw p) (embeddedLaw q) = ENNReal.ofReal (finiteKL p q) :=
  weightedDirac_klDiv_eq_finiteKL_of_relativeSupport p q h
example (p q : FiniteLaw α) (h : ∀ x, 0 < q x) :
    (embeddedLaw q).withDensity (fun x => ENNReal.ofReal (p x / q x)) = embeddedLaw p :=
  embeddedLaw_withDensity_ratio p q h
example (p q : FiniteLaw α) (h : ∀ x, 0 < q x) :
    InformationTheory.klDiv (embeddedLaw p) (embeddedLaw q) = ENNReal.ofReal (finiteKL p q) :=
  weightedDirac_klDiv_eq_finiteKL_of_fullSupport p q h
end ExistingFiniteKLConsumer
#print axioms ExistingFiniteKLConsumer.embedding_defeq
#print axioms FEP.FiniteInformation.klDiv_finiteWeightMeasure
#print axioms FEP.DecisionRisk.embeddedLaw_withDensity_ratio_of_relativeSupport
#print axioms FEP.DecisionRisk.weightedDirac_klDiv_eq_finiteKL_of_relativeSupport
#print axioms FEP.DecisionRisk.embeddedLaw_withDensity_ratio
#print axioms FEP.DecisionRisk.weightedDirac_klDiv_eq_finiteKL_of_fullSupport
