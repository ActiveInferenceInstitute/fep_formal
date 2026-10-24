module
public import FepSketches.compositions.control_temporal
public import FepSketches.compositions.collective_learning
public import Mathlib.Tactic
@[expose] public section
namespace FEP103TemporalConsensusControls
open FEP FEP.TemporalInference FEP.CollectiveInference
open scoped BigOperators
noncomputable section

theorem boolean_backward_positive :
    0 < backwardEvidence boolInitialLaw boolStickyTransition boolAccurateEmission true := by
  rw [boolBackwardEvidence_eq]
  norm_num

theorem boolean_imported_reconstruction :
    ∃ hForward : 0 < forwardEvidence boolInitialLaw boolStickyTransition boolAccurateEmission true,
      (∀ state, forwardFilter boolInitialLaw boolStickyTransition boolAccurateEmission true hForward state *
        backwardEvidence boolInitialLaw boolStickyTransition boolAccurateEmission true =
          forwardPrediction boolInitialLaw boolStickyTransition state * boolAccurateEmission state true) ∧
        forwardFilter boolInitialLaw boolStickyTransition boolAccurateEmission true hForward true = 20 / 23 := by
  obtain ⟨hForward, reconstruction⟩ :=
    FEPComposed.fep074_backwardEvidence_supplies_fep072_filter boolInitialLaw
      boolStickyTransition boolAccurateEmission true boolean_backward_positive
  refine ⟨hForward, reconstruction, ?_⟩
  have atom := reconstruction true
  rw [boolBackwardEvidence_eq, boolPrediction_true_mass] at atom
  change forwardFilter boolInitialLaw boolStickyTransition boolAccurateEmission true hForward true *
    (23 / 40) = (5 / 8 : ℝ) * (4 / 5) at atom
  linarith

theorem prior_not_filtered : boolInitialLaw true ≠ boolForwardFilter true := by
  rw [fep_fep072.FEP072.fep072_bool_forward_mass]
  norm_num [boolInitialLaw]

noncomputable def neverTrue : FiniteKernel Bool Bool where
  mass _ observation := if observation then 0 else 1
  nonneg _ observation := by cases observation <;> norm_num
  sum_one _ := by norm_num [Fintype.sum_bool]

theorem zero_evidence_refuses :
    backwardEvidence boolInitialLaw boolStickyTransition neverTrue true = 0 ∧
      ¬0 < backwardEvidence boolInitialLaw boolStickyTransition neverTrue true ∧
      ¬0 < forwardEvidence boolInitialLaw boolStickyTransition neverTrue true := by
  have zero : backwardEvidence boolInitialLaw boolStickyTransition neverTrue true = 0 := by
    rw [← fep_fep074.FEP074.fep074_forward_backward_evidence_agreement]
    simp [forwardEvidence, FiniteKernel.predictive_mass, neverTrue]
  refine ⟨zero, ?_, ?_⟩
  · rw [zero]; norm_num
  · rw [fep_fep074.FEP074.fep074_forward_backward_evidence_agreement, zero]
    norm_num

noncomputable def uneven : FiniteLaw Bool where
  mass b := if b then 2 / 3 else 1 / 3
  nonneg b := by cases b <;> norm_num
  sum_one := by norm_num [Fintype.sum_bool]

theorem equal_nonuniform_pair_fixed :
    consensusLeft uneven uneven = uneven ∧ consensusRight uneven uneven = uneven := by
  constructor <;> apply FiniteLaw.ext_mass <;> funext b <;> cases b <;>
    norm_num [consensusLeft, consensusRight, convexMixture, uneven]

theorem imported_equal_pair : uneven = uneven := by
  exact FEPComposed.fep112_consensus_fixed_pair_is_equal uneven uneven
    equal_nonuniform_pair_fixed.1 equal_nonuniform_pair_fixed.2

theorem opposite_nonzero_gap :
    beliefGap (FiniteLaw.pointMass true) (FiniteLaw.pointMass false) true = 1 ∧
      beliefGap (consensusLeft (FiniteLaw.pointMass true) (FiniteLaw.pointMass false))
        (consensusRight (FiniteLaw.pointMass true) (FiniteLaw.pointMass false)) true = 1 / 2 := by
  have witness := fep_fep112.FEP112.fep112_bool_nonzero_strict_witness
  exact ⟨witness.1, witness.2.1⟩

theorem opposite_pair_not_fixed :
    ¬(consensusLeft (FiniteLaw.pointMass true) (FiniteLaw.pointMass false) = FiniteLaw.pointMass true ∧
      consensusRight (FiniteLaw.pointMass true) (FiniteLaw.pointMass false) = FiniteLaw.pointMass false) := by
  intro fixed
  have equal := FEPComposed.fep112_consensus_fixed_pair_is_equal _ _ fixed.1 fixed.2
  have atom := congrArg (fun law : FiniteLaw Bool => law true) equal
  norm_num [FiniteLaw.pointMass] at atom

theorem identity_coupling_adverse :
    (id (FiniteLaw.pointMass true), id (FiniteLaw.pointMass false)) =
      (FiniteLaw.pointMass true, FiniteLaw.pointMass false) ∧
      (FiniteLaw.pointMass true : FiniteLaw Bool) ≠ FiniteLaw.pointMass false := by
  constructor
  · rfl
  · intro equal
    have atom := congrArg (fun law : FiniteLaw Bool => law true) equal
    norm_num [FiniteLaw.pointMass] at atom

theorem many_equal_fixed_pairs :
    consensusLeft (FiniteLaw.pointMass true) (FiniteLaw.pointMass true) = FiniteLaw.pointMass true ∧
      consensusRight (FiniteLaw.pointMass true) (FiniteLaw.pointMass true) = FiniteLaw.pointMass true := by
  constructor <;> apply FiniteLaw.ext_mass <;> funext b <;> cases b <;>
    norm_num [consensusLeft, consensusRight, convexMixture, FiniteLaw.pointMass]
end
end FEP103TemporalConsensusControls

#check FEPComposed.fep074_backwardEvidence_supplies_fep072_filter
#print axioms FEPComposed.fep074_backwardEvidence_supplies_fep072_filter
#check FEPComposed.fep112_consensus_fixed_pair_is_equal
#print axioms FEPComposed.fep112_consensus_fixed_pair_is_equal
#check FEP103TemporalConsensusControls.boolean_backward_positive
#print axioms FEP103TemporalConsensusControls.boolean_backward_positive
#check FEP103TemporalConsensusControls.boolean_imported_reconstruction
#print axioms FEP103TemporalConsensusControls.boolean_imported_reconstruction
#check FEP103TemporalConsensusControls.prior_not_filtered
#print axioms FEP103TemporalConsensusControls.prior_not_filtered
#check FEP103TemporalConsensusControls.zero_evidence_refuses
#print axioms FEP103TemporalConsensusControls.zero_evidence_refuses
#check FEP103TemporalConsensusControls.equal_nonuniform_pair_fixed
#print axioms FEP103TemporalConsensusControls.equal_nonuniform_pair_fixed
#check FEP103TemporalConsensusControls.imported_equal_pair
#print axioms FEP103TemporalConsensusControls.imported_equal_pair
#check FEP103TemporalConsensusControls.opposite_nonzero_gap
#print axioms FEP103TemporalConsensusControls.opposite_nonzero_gap
#check FEP103TemporalConsensusControls.opposite_pair_not_fixed
#print axioms FEP103TemporalConsensusControls.opposite_pair_not_fixed
#check FEP103TemporalConsensusControls.identity_coupling_adverse
#print axioms FEP103TemporalConsensusControls.identity_coupling_adverse
#check FEP103TemporalConsensusControls.many_equal_fixed_pairs
#print axioms FEP103TemporalConsensusControls.many_equal_fixed_pairs
