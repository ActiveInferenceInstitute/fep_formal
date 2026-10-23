module
public import FepSketches.ness_flow
public import Mathlib.Tactic
set_option autoImplicit false
@[expose] public section
namespace FEP.NessForwardDifferenceControls
open FEP.NessFlow FEP.NessFlow.ForwardDifference
open scoped BigOperators
noncomputable section

/-- The empty-coordinate sum is exactly zero, independently of step size. -/
theorem empty_dimension (V : (Fin 0 → ℝ) → Fin 0 → ℝ)
    (x : Fin 0 → ℝ) (h : ℝ) : forwardDiv V x h = 0 := by
  simp [forwardDiv]

/-- Totalized division at zero is not the punctured-neighborhood limit. -/
theorem zero_step (n : ℕ) (V : (Fin n → ℝ) → Fin n → ℝ)
    (x : Fin n → ℝ) : forwardDiv V x 0 = 0 := by
  simp [forwardDiv]

/-- Dense off-diagonal terms are present; the diagonal finite-difference trace is four. -/
theorem dense_field : forwardDiv
    (fun x : Fin 2 → ℝ => ![x 0 + x 1, 2 * x 0 + 3 * x 1])
    (fun _ => 0) 1 = 4 := by
  norm_num [forwardDiv, Fin.sum_univ_two, Pi.single_apply]

/-- At step one, D(x²)(0)=1 whereas x(0)D(x)(0)+x(0)D(x)(0)=0.
This is an actual forwardDiv instance, not an assumed product-rule failure. -/
theorem finite_step_leibniz_counterexample :
    forwardDiv (fun x : Fin 1 → ℝ => fun _ => x 0 * x 0) (fun _ => 0) 1 ≠
      (0 : ℝ) * forwardDiv (fun x : Fin 1 → ℝ => x) (fun _ => 0) 1 +
      (0 : ℝ) * forwardDiv (fun x : Fin 1 → ℝ => x) (fun _ => 0) 1 := by
  norm_num [forwardDiv, Fin.sum_univ_succ, Pi.single_apply]
end
end FEP.NessForwardDifferenceControls
#print axioms FEP.NessFlow.ForwardDifference.forwardDiv_tendsto
#print axioms FEP.NessFlow.ForwardDifference.stationary_current_differentiable
#print axioms FEP.NessFlow.ForwardDifference.stationary_forwardDiv_tendsto_zero
#print axioms FEP.NessFlow.ForwardDifference.actualCarrier_eq_negative_divergence
#print axioms FEP.NessFlow.ForwardDifference.negative_forwardDiv_tendsto_carrier
#print axioms FEP.NessFlow.ForwardDifference.nonSkew_gaussian_carrier_one
#print axioms FEP.NessFlow.ForwardDifference.skew_actualCarrier_zero
#print axioms FEP.NessForwardDifferenceControls.empty_dimension
#print axioms FEP.NessForwardDifferenceControls.zero_step
#print axioms FEP.NessForwardDifferenceControls.dense_field
#print axioms FEP.NessForwardDifferenceControls.finite_step_leibniz_counterexample
