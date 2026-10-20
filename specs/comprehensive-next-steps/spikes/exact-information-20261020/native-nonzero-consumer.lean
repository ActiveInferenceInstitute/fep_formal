/- Imported current-owner acceptance control. Actual results are recorded separately. -/
import FepSketches.compositions.core
open MeasureTheory ProbabilityTheory FEPComposed
namespace Issue104NativeControls
local instance : MeasurableSpace Bool := ⊤

noncomputable def trueKernel : Kernel Bool Bool := Kernel.const Bool (Measure.dirac true)
noncomputable def falseKernel : Kernel Bool Bool := Kernel.const Bool (Measure.dirac false)
instance : IsMarkovKernel trueKernel := by unfold trueKernel; infer_instance
instance : IsMarkovKernel falseKernel := by unfold falseKernel; infer_instance

theorem predictive_nonzero_Bool_consumer :
    (fep_fep027.FEP027.fep027_hierarchicalJoint (Measure.dirac false)
      (fep_fep022.FEP022.fep022_posteriorPredictive trueKernel falseKernel)).snd =
      falseKernel ∘ₘ (trueKernel ∘ₘ Measure.dirac false) := by
  exact fep022_fep027_predictive_child_marginal _ _ _

theorem predictive_law_nonzero :
    falseKernel ∘ₘ (trueKernel ∘ₘ Measure.dirac false) ≠ 0 := by
  have h : (falseKernel ∘ₘ (trueKernel ∘ₘ Measure.dirac false)) Set.univ = 1 :=
    measure_univ
  intro hz
  simp [hz] at h

theorem filter_nonzero_Bool_consumer :
    (falseKernel ∘ₘ (trueKernel ∘ₘ Measure.dirac false)) ⊗ₘ
      fep_fep034.FEP034.fep034_filter trueKernel falseKernel (Measure.dirac false) =
      ((trueKernel ∘ₘ Measure.dirac false) ⊗ₘ falseKernel).map Prod.swap := by
  exact fep034_fep017_filter_joint_reconstruction _ _ _

#print axioms predictive_nonzero_Bool_consumer
#print axioms predictive_law_nonzero
#print axioms filter_nonzero_Bool_consumer
end Issue104NativeControls
