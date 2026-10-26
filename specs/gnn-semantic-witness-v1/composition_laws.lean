import Mathlib.Algebra.BigOperators.Field
import Mathlib.Tactic

/-!
Finite post-evidence weight products only. Factorization is an explicit
hypothesis about the joint weights, not a consequence of independent priors
or normalized marginals. These are real-arithmetic laws, not a Gaussian
conditional-kernel, covariance, parser, floating-point or execution proof.
-/
namespace FEPSemanticComposition

open scoped BigOperators

noncomputable section

theorem product_mass {S T : Type*} [Fintype S] [Fintype T]
    (u : S → ℝ) (v : T → ℝ) :
    (∑ s, ∑ t, u s * v t) = (∑ s, u s) * (∑ t, v t) := by
  simp only [Finset.sum_mul, Finset.mul_sum]
  exact Finset.sum_comm

theorem normalized_product {S T : Type*} [Fintype S] [Fintype T]
    (u : S → ℝ) (v : T → ℝ)
    (hU : (∑ s, u s) ≠ 0) (hV : (∑ t, v t) ≠ 0) (s : S) (t : T) :
    u s * v t / (∑ i, ∑ j, u i * v j) =
      (u s / ∑ i, u i) * (v t / ∑ j, v j) := by
  rw [product_mass]
  apply (div_eq_iff (mul_ne_zero hU hV)).2
  field_simp

theorem normalized_product_sum {S T : Type*} [Fintype S] [Fintype T]
    (u : S → ℝ) (v : T → ℝ)
    (hU : (∑ s, u s) ≠ 0) (hV : (∑ t, v t) ≠ 0) :
    (∑ s, ∑ t, u s * v t / (∑ i, ∑ j, u i * v j)) = 1 := by
  have hJoint : (∑ i, ∑ j, u i * v j) ≠ 0 := by
    rw [product_mass]
    exact mul_ne_zero hU hV
  simp_rw [← Finset.sum_div]
  exact div_self hJoint

theorem normalized_product_nonneg {S T : Type*} [Fintype S] [Fintype T]
    (u : S → ℝ) (v : T → ℝ)
    (hu : ∀ s, 0 ≤ u s) (hv : ∀ t, 0 ≤ v t)
    (hU : 0 < ∑ s, u s) (hV : 0 < ∑ t, v t) (s : S) (t : T) :
    0 ≤ u s * v t / (∑ i, ∑ j, u i * v j) := by
  rw [product_mass]
  exact div_nonneg (mul_nonneg (hu s) (hv t)) (mul_pos hU hV).le

/-- A normalized, correlated joint with normalized uniform marginals. -/
def correlatedJoint (s t : Bool) : ℝ := if s = t then 1 / 2 else 0

theorem correlated_joint_normalized :
    (∑ s, ∑ t, correlatedJoint s t) = 1 := by
  norm_num [correlatedJoint, Fintype.sum_bool]

theorem correlated_marginals_normalized :
    (∑ t, correlatedJoint false t) = 1 / 2 ∧
    (∑ s, correlatedJoint s false) = 1 / 2 := by
  norm_num [correlatedJoint, Fintype.sum_bool]

theorem normalized_marginals_do_not_imply_product :
    correlatedJoint false false ≠
      (∑ t, correlatedJoint false t) * (∑ s, correlatedJoint s false) := by
  norm_num [correlatedJoint, Fintype.sum_bool]

#print axioms product_mass
#print axioms normalized_product
#print axioms normalized_product_sum
#print axioms normalized_product_nonneg
#print axioms correlated_joint_normalized
#print axioms correlated_marginals_normalized
#print axioms normalized_marginals_do_not_imply_product

end
end FEPSemanticComposition
