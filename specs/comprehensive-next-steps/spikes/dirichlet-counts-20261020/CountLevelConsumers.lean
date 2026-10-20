import FepSketches.empirical_risk
import FepSketches.families.core_bayesian_mechanics
import FepSketches.families.finite_sample_risk_calibration
open FEP.EmpiricalRisk
open scoped BigOperators
namespace CountLevelConsumers

theorem exact_fep045 (a b : ℝ) (ha : 0 < a) (hb : 0 < b) :
    let α := binaryPseudoCounts a b
    let p := polyaPredictive α (fun _ => 0) true
    let l₁ := polyaPredictive α (Pi.single true 1 : Bool → ℕ) true
    let l₀ := polyaPredictive α (Pi.single false 1 : Bool → ℕ) true
    fep_fep045.FEP045.fep045_posteriorParameter p l₀ l₁ =
      polyaPredictive α (Pi.single true 1 : Bool → ℕ) true := by
  simpa [fep_fep045.FEP045.fep045_posteriorParameter,
    fep_fep045.FEP045.fep045_evidence] using
    dirichletBinary_bernoulliBayes_bridge a b ha hb

theorem exact_fep121 (n : Bool → ℕ) (target : ℝ)
    (hn : 0 < n true + n false) (ht : target ∈ Set.Icc (0 : ℝ) 1) :
    polyaPredictive (binaryPseudoCounts 1 1) n true - target =
      shrinkage (n true + n false) *
        (empiricalRate (n true) (n true + n false) - target) +
      laplaceBias (n true + n false) target := by
  rw [polyaPredictive_binary_laplace]
  exact fep_fep121.FEP121.fep121_laplaceError_identity
    (n true) (n true + n false) target hn (Nat.le_add_right _ _) ht

theorem asymmetric_predictive :
    polyaPredictive (binaryPseudoCounts 2 3)
      (fun b : Bool => if b then 4 else 1) true = 3 / 5 := by
  norm_num [polyaPredictive, binaryPseudoCounts]

theorem nonconstant_exchangeability :
    dirichletSequenceProbability (binaryPseudoCounts 2 3) [true, false, true] =
      dirichletSequenceProbability (binaryPseudoCounts 2 3) [true, true, false] := by
  exact dirichletSequenceProbability_exchangeable _
    (List.Perm.cons true (List.Perm.swap true false []))

theorem A_rows (α : Bool → Bool → ℝ) (n : Bool → Bool → ℕ)
    (ha : ∀ s o, 0 < α s o) (s : Bool) :
    (∀ o, 0 ≤ learnedLikelihood α n s o) ∧
      ∑ o, learnedLikelihood α n s o = 1 :=
  learnedLikelihood_normalised α n ha s

theorem B_state_action_rows (α : Bool × Fin 3 → Bool → ℝ)
    (n : Bool × Fin 3 → Bool → ℕ) (ha : ∀ r k, 0 < α r k)
    (s : Bool) (u : Fin 3) :
    (∀ s', 0 ≤ learnedTransition α n s u s') ∧
      ∑ s', learnedTransition α n s u s' = 1 :=
  learnedTransition_normalised α n ha s u

/-- Totalized definitions at zero total are not normalized probability laws. -/
theorem zero_total_not_normalized :
    (∑ k : Bool, polyaPredictive (fun _ => 0) (fun _ => 0) k) = 0 := by
  simp [polyaPredictive]

/-- Dropping nonnegative pseudo-counts permits negative mass. -/
theorem negative_pseudocount_negative_mass :
    polyaPredictive (binaryPseudoCounts (-1) 2) (fun _ => 0) true = -1 := by
  norm_num [polyaPredictive, binaryPseudoCounts]

#print axioms exact_fep045
#print axioms exact_fep121
#print axioms asymmetric_predictive
#print axioms nonconstant_exchangeability
#print axioms A_rows
#print axioms B_state_action_rows
#print axioms zero_total_not_normalized
#print axioms negative_pseudocount_negative_mass
end CountLevelConsumers
