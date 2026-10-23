module
public import FepSketches.gaussian_precision_conditioning
public import Mathlib.Tactic
set_option autoImplicit false
@[expose] public section
namespace FEP.GaussianPrecisionResidualControls
noncomputable section
open Matrix FEP.GaussianPrecisionConditioning.FinitePrecision
abbrev A := Fin 1 ⊕ (Fin 1 ⊕ Fin 1)
def table (a b c d e f g h i : ℝ) : Matrix A A ℝ := fun x y ↦
  match x, y with
  | .inl _, .inl _ => a
  | .inl _, .inr (.inl _) => b
  | .inl _, .inr (.inr _) => c
  | .inr (.inl _), .inl _ => d
  | .inr (.inl _), .inr (.inl _) => e
  | .inr (.inl _), .inr (.inr _) => f
  | .inr (.inr _), .inl _ => g
  | .inr (.inr _), .inr (.inl _) => h
  | .inr (.inr _), .inr (.inr _) => i

def K : Matrix A A ℝ := table 2 0 1 0 2 1 1 1 2
def S : Matrix A A ℝ := table (3/4) (1/4) (-1/2) (1/4) (3/4) (-1/2) (-1/2) (-1/2) 1
def KB : Matrix A A ℝ := table 2 1 0 1 2 0 0 0 1
def SB : Matrix A A ℝ := table (2/3) (-1/3) 0 (-1/3) (2/3) 0 0 0 1
def KS : Matrix A A ℝ := table 0 0 1 0 1 0 1 0 0

def residual (k sigma : Matrix A A ℝ) (r : ℝ) : Matrix (Fin 1) (Fin 1) ℝ :=
  (ei sigma + (ee k)⁻¹ * eb k * bi sigma) +
    (eb sigma + (ee k)⁻¹ * eb k * bb sigma) * Matrix.transpose (fun (_ : Fin 1) (_ : Fin 1) ↦ r)

theorem positive_model : K * S = 1 ∧
    (∀ e i, K (Sum.inl e) (Sum.inr (Sum.inl i)) = 0) ∧ ei S 0 0 = 1/4 := by
  constructor
  · ext x y
    fin_cases x <;> fin_cases y <;>
      norm_num [Matrix.mul_apply, Matrix.one_apply, Fintype.sum_sum_type, Fin.sum_univ_succ, K, S, table]
  · constructor
    · intro e i; rfl
    · rfl

theorem positive_residual : residual K S 1 = 0 := by
  have hdet : IsUnit (Matrix.det (ee K)) := by
    norm_num [Matrix.det_unique, ee, K, table]
  let : Invertible (ee K) := Matrix.invertibleOfIsUnitDet (ee K) hdet
  exact residual_cross_block K S positive_model.1 positive_model.2.1 (fun _ _ ↦ 1)

theorem nonsparse_model : KB * SB = 1 ∧ KB (.inl 0) (.inr (.inl 0)) = 1 := by
  constructor
  · ext x y
    fin_cases x <;> fin_cases y <;>
      norm_num [Matrix.mul_apply, Matrix.one_apply, Fintype.sum_sum_type, Fin.sum_univ_succ, KB, SB, table]
  · rfl

theorem nonsparse_cross : residual KB SB 0 0 0 = -(1/3 : ℝ) := by
  norm_num [residual, Matrix.transpose_apply, Matrix.inv_subsingleton, Matrix.mul_apply, Fin.sum_univ_succ,
    ee, eb, ei, bi, bb, KB, SB, table]

theorem singular_principal_model : KS * KS = 1 ∧
    (∀ e i, KS (Sum.inl e) (Sum.inr (Sum.inl i)) = 0) ∧ ee KS = 0 := by
  constructor
  · ext x y
    fin_cases x <;> fin_cases y <;>
      norm_num [Matrix.mul_apply, Matrix.one_apply, Fintype.sum_sum_type, Fin.sum_univ_succ, KS, table]
  · constructor
    · intro e i; rfl
    · rfl

theorem singular_principal_cross : residual KS KS 1 0 0 = 1 := by
  norm_num [residual, Matrix.transpose_apply, Matrix.inv_subsingleton, Matrix.mul_apply, Fin.sum_univ_succ,
    ee, eb, ei, bi, bb, KS, table]
  rfl
end
end FEP.GaussianPrecisionResidualControls
#print axioms FEP.GaussianPrecisionResidualControls.positive_model
#print axioms FEP.GaussianPrecisionResidualControls.positive_residual
#print axioms FEP.GaussianPrecisionResidualControls.nonsparse_model
#print axioms FEP.GaussianPrecisionResidualControls.nonsparse_cross
#print axioms FEP.GaussianPrecisionResidualControls.singular_principal_model
#print axioms FEP.GaussianPrecisionResidualControls.singular_principal_cross

#print axioms FEP.GaussianPrecisionConditioning.FinitePrecision.inverse_rows
#print axioms FEP.GaussianPrecisionConditioning.FinitePrecision.residual_cross_block
#print axioms FEP.GaussianPrecisionConditioning.FiniteCovariance.covariance_weighted_add_left
#print axioms FEP.GaussianPrecisionConditioning.FiniteCovariance.covariance_weighted_add_right
#print axioms FEP.GaussianPrecisionConditioning.FiniteCovariance.covariance_residual_block
#print axioms FEP.GaussianPrecisionConditioning.FiniteCovariance.actual_residual_covariance_zero
