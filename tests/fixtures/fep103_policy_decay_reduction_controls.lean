module
public import FepSketches.compositions.policy_trees
public import FepSketches.compositions.continuous_time
public import FepSketches.compositions.bayesian_model_reduction
public import Mathlib.Tactic
@[expose] public section
namespace FEP103Controls
open FEP FEP.PolicyTrees FEP.ContinuousTimeMarkov FEP.BayesianModelReduction
open scoped BigOperators
noncomputable section

theorem policy_attained_boolean : ∃ tree : PolicyTree Bool Bool 2,
    policyTreeValue boolFeedbackModel tree false = optimalTreeValue boolFeedbackModel 2 false ∧
    ∀ _action : Bool, policyTreeValue boolFeedbackModel tree false ≤ (1:ℝ)/2 := by
  obtain ⟨tree, attained, dominates⟩ :=
    FEPComposed.fep130_attaining_tree_dominates_fep131_embedded_plans boolFeedbackModel 2 false
  refine ⟨tree, attained, ?_⟩
  intro action
  simpa only [boolOpenLoop_value_half] using dominates (boolOpenLoopPlan action)

theorem policy_strict_witness (action : Bool) :
    policyTreeValue boolFeedbackModel boolFeedbackTree false <
      openLoopValue boolFeedbackModel (boolOpenLoopPlan action) false :=
  (fep_fep134.FEP134.fep134_boolFeedback_strictlyBetter action).2.2

theorem policy_depth_zero : ∃ tree : PolicyTree Bool Bool 0,
    policyTreeValue boolFeedbackModel tree false = 0 := by
  refine ⟨PUnit.unit, ?_⟩
  rfl

/-- Strict improvement is not universal: every depth-zero comparison is equality. -/
theorem policy_not_universal_strict : ¬ (policyTreeValue (depth := 0) boolFeedbackModel
    (PUnit.unit : PolicyTree Bool Bool 0) false <
    openLoopValue (depth := 0) boolFeedbackModel (PUnit.unit : OpenLoopPlan Bool 0) false) := by
  simp [policyTreeValue, openLoopValue]

theorem decay_benchmark (time : ℝ) :
    HasDerivAt (TwoStateRates.benchmarkRates.lyapunov TwoStateRates.benchmarkInitial)
      (-2 * TwoStateRates.benchmarkRates.decayRate *
        TwoStateRates.benchmarkRates.lyapunov TwoStateRates.benchmarkInitial time) time ∧
    -2 * TwoStateRates.benchmarkRates.decayRate *
        TwoStateRates.benchmarkRates.lyapunov TwoStateRates.benchmarkInitial time < 0 :=
  FEPComposed.fep154_nonstationary_relaxation_supplies_fep155_strict_decay
    _ _ TwoStateRates.benchmarkInitial_nonstationary time

/-- The required nonstationarity cannot be discarded: the stationary initial law gives zero. -/
theorem decay_stationary_boundary (rates : TwoStateRates) (time : ℝ) :
    -2 * rates.decayRate * rates.lyapunov rates.stationaryLaw time = 0 := by
  have exactRelax := fep_fep154.FEP154.fep154_twoStateRelaxation_exact rates rates.stationaryLaw time
  have mass : rates.stationaryLaw true = rates.stationaryTrue := by rfl
  rw [mass, sub_self, mul_zero] at exactRelax
  simp [TwoStateRates.lyapunov, exactRelax]

noncomputable def prior : FiniteLaw Bool where
  mass b := if b then 2/3 else 1/3
  nonneg b := by cases b <;> norm_num
  sum_one := by norm_num [Fintype.sum_bool]
noncomputable def weight (b : Bool) : ℝ := if b then 1/2 else 1
noncomputable def likelihood : FiniteKernel Bool Bool where
  mass b y := if y then (if b then 3/4 else 1/4) else (if b then 1/4 else 3/4)
  nonneg b y := by cases b <;> cases y <;> norm_num
  sum_one b := by cases b <;> norm_num [Fintype.sum_bool]
theorem weights_nonnegative (b : Bool) : 0 ≤ weight b := by cases b <;> norm_num [weight]
theorem normalizer_positive : 0 < ∑ b, weight b * prior b := by norm_num [Fintype.sum_bool, weight, prior]
theorem evidence_positive : 0 < maskedEvidence prior weight likelihood true := by
  norm_num [maskedEvidence, Fintype.sum_bool, weight, prior, likelihood]
theorem reduced_odds_three : ∃ hy : 0 < likelihood.predictive
    (maskedPrior prior weight weights_nonnegative normalizer_positive) true,
    FEP.LearningTheory.posteriorOdds
      (maskedPrior prior weight weights_nonnegative normalizer_positive) likelihood true hy true false = 3 := by
  obtain ⟨hy, odds⟩ := FEPComposed.fep158_masked_evidence_supplies_fep117_reduced_odds
    prior weight likelihood true weights_nonnegative normalizer_positive evidence_positive
    true false (by norm_num [weight]) (by norm_num [prior]) (by norm_num [likelihood])
  refine ⟨hy, ?_⟩
  norm_num [weight, prior, likelihood] at odds
  exact odds

theorem original_odds_six : ∃ hy : 0 < likelihood.predictive prior true,
    FEP.LearningTheory.posteriorOdds prior likelihood true hy true false = 6 := by
  have hy : 0 < likelihood.predictive prior true := by
    norm_num [FiniteKernel.predictive_mass, Fintype.sum_bool, prior, likelihood]
  refine ⟨hy, ?_⟩
  rw [fep_fep117.FEP117.fep117_posteriorOdds_recursion prior likelihood true hy true false
    (by norm_num [prior]) (by norm_num [likelihood])]
  norm_num [prior, likelihood]

theorem zero_weights_refuse : ¬ (0 < ∑ b : Bool, (0:ℝ) * prior b) := by simp

theorem zero_reference_weight : ¬ (0 < (fun b : Bool => if b then (1:ℝ) else 0) false) := by simp
theorem no_action_depth_one : ¬ Nonempty (PolicyTree (Fin 0) Bool 1) := by
  rintro ⟨tree⟩
  exact Fin.elim0 tree.1

noncomputable def zeroRefWeight (b : Bool) : ℝ := if b then 1 else 0
/-- With reference weight zero, the actual reduced posterior odds is totalized to zero. -/
theorem zero_reference_actual_odds :
    ∃ hw : ∀ b, 0 ≤ zeroRefWeight b,
    ∃ hZ : 0 < ∑ b, zeroRefWeight b * prior b,
    ∃ hy : 0 < likelihood.predictive (maskedPrior prior zeroRefWeight hw hZ) true,
      FEP.LearningTheory.posteriorOdds (maskedPrior prior zeroRefWeight hw hZ)
        likelihood true hy true false = 0 := by
  have hw : ∀ b, 0 ≤ zeroRefWeight b := by intro b; cases b <;> norm_num [zeroRefWeight]
  have hZ : 0 < ∑ b, zeroRefWeight b * prior b := by
    norm_num [Fintype.sum_bool, zeroRefWeight, prior]
  have hy : 0 < likelihood.predictive (maskedPrior prior zeroRefWeight hw hZ) true := by
    rw [fep_fep158.FEP158.fep158_maskedPrior_predictive_eq prior zeroRefWeight likelihood true hw hZ]
    norm_num [maskedEvidence, Fintype.sum_bool, zeroRefWeight, prior, likelihood]
  refine ⟨hw, hZ, hy, ?_⟩
  have refZero : maskedPrior prior zeroRefWeight hw hZ false = 0 := by
    simp [maskedPrior, zeroRefWeight]
  have posteriorZero := fep_fep117.FEP117.fep117_zero_prior_boundary
    (maskedPrior prior zeroRefWeight hw hZ) likelihood true hy false refZero
  unfold FEP.LearningTheory.posteriorOdds
  rw [posteriorZero, div_zero]

/-- An impossible observation has zero masked evidence, so cannot supply positive evidence. -/
theorem impossible_observation_refuses :
    ¬ (0 < maskedEvidence prior weight
      (FiniteKernel.deterministic (fun _ : Bool => false)) true) := by
  norm_num [maskedEvidence, FiniteKernel.deterministic, Fintype.sum_bool]

end
end FEP103Controls

#check FEPComposed.fep130_attaining_tree_dominates_fep131_embedded_plans
#print axioms FEPComposed.fep130_attaining_tree_dominates_fep131_embedded_plans
#check FEPComposed.fep154_nonstationary_relaxation_supplies_fep155_strict_decay
#print axioms FEPComposed.fep154_nonstationary_relaxation_supplies_fep155_strict_decay
#check FEPComposed.fep158_masked_evidence_supplies_fep117_reduced_odds
#print axioms FEPComposed.fep158_masked_evidence_supplies_fep117_reduced_odds
#check FEP103Controls.policy_attained_boolean
#print axioms FEP103Controls.policy_attained_boolean
#check FEP103Controls.policy_strict_witness
#print axioms FEP103Controls.policy_strict_witness
#check FEP103Controls.policy_depth_zero
#print axioms FEP103Controls.policy_depth_zero
#check FEP103Controls.policy_not_universal_strict
#print axioms FEP103Controls.policy_not_universal_strict
#check FEP103Controls.decay_benchmark
#print axioms FEP103Controls.decay_benchmark
#check FEP103Controls.decay_stationary_boundary
#print axioms FEP103Controls.decay_stationary_boundary
#check FEP103Controls.weights_nonnegative
#print axioms FEP103Controls.weights_nonnegative
#check FEP103Controls.normalizer_positive
#print axioms FEP103Controls.normalizer_positive
#check FEP103Controls.evidence_positive
#print axioms FEP103Controls.evidence_positive
#check FEP103Controls.reduced_odds_three
#print axioms FEP103Controls.reduced_odds_three
#check FEP103Controls.original_odds_six
#print axioms FEP103Controls.original_odds_six
#check FEP103Controls.zero_weights_refuse
#print axioms FEP103Controls.zero_weights_refuse
#check FEP103Controls.zero_reference_weight
#print axioms FEP103Controls.zero_reference_weight
#check FEP103Controls.zero_reference_actual_odds
#print axioms FEP103Controls.zero_reference_actual_odds
#check FEP103Controls.impossible_observation_refuses
#print axioms FEP103Controls.impossible_observation_refuses
#check FEP103Controls.no_action_depth_one
#print axioms FEP103Controls.no_action_depth_one
