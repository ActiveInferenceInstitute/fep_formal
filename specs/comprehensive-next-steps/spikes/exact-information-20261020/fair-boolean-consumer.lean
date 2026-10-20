/- Imported current-owner acceptance control. Actual results are recorded separately. -/
import FepSketches.variational_duality
open FEP FEP.FiniteInformation FEP.VariationalDuality
open FEP.VariationalDuality.FairBoolean
namespace Issue69Controls

theorem quarter_is_owned :
    symmetricJoint (1/4) (by norm_num) (by norm_num) = boolQuarterDistortionJoint := by
  apply FiniteLaw.ext_mass
  funext xy
  rcases xy with ⟨x,y⟩
  cases x <;> cases y <;> norm_num [symmetricJoint, boolQuarterDistortionJoint]

theorem quarter_information :
    mutualInformation boolQuarterDistortionJoint =
      Real.log 2 - Real.binEntropy (1/4) := by
  rw [← quarter_is_owned, symmetricJoint_information]

theorem quarter_is_optimal (K : FiniteLaw (Bool × Bool))
    (hK : RateDistortionFeasible FiniteLaw.uniform boolHammingDistortion (1/4) K) :
    mutualInformation boolQuarterDistortionJoint ≤ mutualInformation K := by
  rw [quarter_information]
  exact boolean_converse (1/4) (by norm_num) (by norm_num) K hK

theorem quarter_exact_dual :
    rateDistortionDualValue (FiniteLaw.uniform : FiniteLaw Bool)
      boolHammingDistortion (1/4) (interiorMultiplier (1/4)) =
        Real.log 2 - Real.binEntropy (1/4) :=
  boolean_interior_dual_exact (1/4) (by norm_num) (by norm_num)

theorem negative_budget_infeasible :
    ¬ ∃ J, RateDistortionFeasible (FiniteLaw.uniform : FiniteLaw Bool)
      boolHammingDistortion (-1) J :=
  rateDistortion_infeasible_of_negativeBudget _ _ _
    boolHammingDistortion_nonneg (by norm_num)

noncomputable def deterministicJoint : FiniteLaw (Bool × Bool) :=
  (FiniteLaw.pointMass false : FiniteLaw Bool).product (FiniteLaw.pointMass false)

theorem deterministic_feasible_zero :
    RateDistortionFeasible (FiniteLaw.pointMass false) boolHammingDistortion 0
      deterministicJoint := by
  refine ⟨FiniteLaw.product_fstMarginal _ _, ?_⟩
  norm_num [expectedDistortion, deterministicJoint, FiniteLaw.product,
    FiniteLaw.pointMass, boolHammingDistortion, Fintype.sum_prod_type, Fintype.sum_bool]

theorem deterministic_information_zero : mutualInformation deterministicJoint = 0 :=
  mutualInformation_product_eq_zero _ _

theorem deterministic_source_not_fair :
    (FiniteLaw.pointMass false : FiniteLaw Bool) ≠ FiniteLaw.uniform := by
  intro h
  have hatom := congrArg (fun law : FiniteLaw Bool => law true) h
  norm_num [FiniteLaw.pointMass, FiniteLaw.uniform] at hatom

theorem unfair_source_refutes_zero_budget_fair_curve :
    mutualInformation deterministicJoint < Real.log 2 - Real.binEntropy 0 := by
  rw [deterministic_information_zero]
  simp only [Real.binEntropy_zero, sub_zero]
  positivity

#print axioms quarter_information
#print axioms quarter_is_optimal
#print axioms quarter_exact_dual
#print axioms negative_budget_infeasible
#print axioms deterministic_feasible_zero
#print axioms deterministic_source_not_fair
#print axioms unfair_source_refutes_zero_budget_fair_curve
#print axioms boolHalfBudget_distinct_minimizers
#print axioms boolean_zero_exact
end Issue69Controls

#print axioms FEP.VariationalDuality.FairBoolean.interiorMultiplier_unbounded_near_zero
#print axioms FEP.VariationalDuality.FairBoolean.interiorMultiplier_zero_totalized
