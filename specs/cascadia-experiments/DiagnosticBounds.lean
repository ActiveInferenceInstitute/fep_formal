import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Fin
import Mathlib.Basic.Real.Basic
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.Ring
import Mathlib.Tactic.NormNum

namespace CascadiaDiagnostics

noncomputable section

def brier {n : ℕ} (p : Fin n → ℝ) (truth : Fin n) : ℝ :=
  ∑ i, (p i - if i = truth then 1 else 0) ^ 2

theorem brier_nonneg {n : ℕ} (p : Fin n → ℝ) (truth : Fin n) :
    0 ≤ brier p truth := by
  exact Finset.sum_nonneg fun i _ => sq_nonneg _

theorem probability_le_one {n : ℕ} (p : Fin n → ℝ)
    (nonneg : ∀ i, 0 ≤ p i) (normalized : ∑ i, p i = 1) (i : Fin n) :
    p i ≤ 1 := by
  calc
    p i ≤ ∑ j, p j := Finset.single_le_sum (fun j _ => nonneg j) (Finset.mem_univ i)
    _ = 1 := normalized

theorem sum_squares_le_one {n : ℕ} (p : Fin n → ℝ)
    (nonneg : ∀ i, 0 ≤ p i) (normalized : ∑ i, p i = 1) :
    ∑ i, p i ^ 2 ≤ 1 := by
  calc
    ∑ i, p i ^ 2 ≤ ∑ i, p i := by
      apply Finset.sum_le_sum
      intro i _
      rw [pow_two]
      exact mul_le_of_le_one_right (nonneg i) (probability_le_one p nonneg normalized i)
    _ = 1 := normalized

theorem brier_identity {n : ℕ} (p : Fin n → ℝ) (truth : Fin n) :
    brier p truth = (∑ i, p i ^ 2) - 2 * p truth + 1 := by
  unfold brier
  have term (i : Fin n) :
      (p i - if i = truth then 1 else 0) ^ 2 =
        p i ^ 2 + if i = truth then 1 - 2 * p truth else 0 := by
    split_ifs with h
    · subst i
      ring
    · ring
  simp_rw [term]
  rw [Finset.sum_add_distrib]
  simp
  ring

theorem brier_le_two {n : ℕ} (p : Fin n → ℝ) (truth : Fin n)
    (nonneg : ∀ i, 0 ≤ p i) (normalized : ∑ i, p i = 1) :
    brier p truth ≤ 2 := by
  rw [brier_identity]
  have hs := sum_squares_le_one p nonneg normalized
  have ht := nonneg truth
  linarith

theorem wrong_point_mass_score : brier (fun i : Fin 2 => if i = 0 then 0 else 1) 0 = 2 := by
  norm_num [brier, Fin.sum_univ_succ]

#print axioms brier_nonneg
#print axioms probability_le_one
#print axioms sum_squares_le_one
#print axioms brier_identity
#print axioms brier_le_two
#print axioms wrong_point_mass_score

end

end CascadiaDiagnostics
