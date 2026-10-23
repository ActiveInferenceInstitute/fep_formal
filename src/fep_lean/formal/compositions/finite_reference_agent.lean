module
public import FepSketches.finite_posterior_learning
public import FepSketches.compositions.finite_policy_action
public import FepSketches.compositions.finite_scientific_implications
public import FepSketches.native_blanket
public import FepSketches.continuous_time_markov

@[expose] public section

/-!
# Finite reference-agent coherence boundary

This leaf retains the original executable carrier no-go and predecessor
conjunction, then proves the repaired shared-carrier terminal result by reusing
the posterior-law policy and action-indexed blanket owners directly.
-/

namespace FEPComposed.FiniteReferenceAgent

open FEP FEP.ActiveInference FEP.CausalDynamics FEP.ContinuousTimeMarkov
  FEP.ControlledMarkov FEP.FiniteMarkovDynamics
  FEP.FiniteInformation FEP.FinitePosteriorLearning FEP.NativeBlanket
  FEP.PolicyTrees FEPComposed.FinitePolicyAction
open scoped BigOperators

/-! ## Exact blocked-merge obligations -/

/-- A terminal witness would have to reuse the learned posterior as the policy
tree's interpreted belief and identify the policy state carrier with the exact
four-factor blanket carrier.  The record stores obligations, not evidence: the
theorems below prove that the current concrete predecessors cannot inhabit it. -/
structure FiniteReferenceCoherence where
  feedbackObservation : Bool
  posterior_coherent :
    posteriorAfter selectedPrior (fun _ => true) 2 =
      boolBeliefInterpret
        (boolFeedbackModel.update false false feedbackObservation)
  stateCarrierEquiv :
    Bool ≃ FEP.MarkovBlanket.DynamicState Bool Bool Bool Bool

/-- The exact non-Dirac learned posterior is not either point-mass belief used
by the maintained Boolean policy-tree model. -/
theorem learnedPosterior_ne_boolBeliefInterpret (belief : Bool) :
    posteriorAfter selectedPrior (fun _ => true) 2 ≠
      boolBeliefInterpret belief := by
  intro hEqual
  cases belief
  · have hMass := congrArg (fun law : FiniteLaw Bool => law true) hEqual
    rw [posteriorAfter_two_true_witness.2.1] at hMass
    norm_num [boolBeliefInterpret, FiniteLaw.pointMass] at hMass
  · have hMass := congrArg (fun law : FiniteLaw Bool => law false) hEqual
    rw [posteriorAfter_two_true_witness.1] at hMass
    norm_num [boolBeliefInterpret, FiniteLaw.pointMass] at hMass

/-- The two-state policy carrier cannot be identified with the exact
right-associated sixteen-state Boolean blanket carrier used by H1.7. -/
theorem boolPolicyState_not_equiv_boolBlanketState :
    ¬Nonempty
      (Bool ≃ FEP.MarkovBlanket.DynamicState Bool Bool Bool Bool) := by
  rintro ⟨equiv⟩
  have hCard := Fintype.card_congr equiv
  norm_num [FEP.MarkovBlanket.DynamicState] at hCard

/-- No current concrete predecessor bundle discharges the terminal coherence
record.  This is an explicit blocked merge, not a terminal certificate. -/
theorem finiteReferenceCoherence_uninhabited :
    ¬Nonempty FiniteReferenceCoherence := by
  rintro ⟨coherence⟩
  exact
    learnedPosterior_ne_boolBeliefInterpret
      (boolFeedbackModel.update false false coherence.feedbackObservation)
      coherence.posterior_coherent

/-! ## Strongest retained predecessor conjunction -/

/-- All currently connected positive results are retained in one theorem while
their incompatible intermediate values remain visibly separate.  In
particular, the H1.3 posterior is not substituted for the policy-tree belief,
the paired H1.6 kernel is not substituted for the H1.7 refresh kernel, and no
selected-action/sampled-semigroup equality is claimed. -/
theorem retainedFiniteReference_predecessors :
    0 < selectedLikelihood.predictive selectedPrior true ∧
      (∑ hypothesis, posteriorUpdate selectedPrior true hypothesis = 1) ∧
      (posteriorAfter selectedPrior (fun _ => true) 2 false = 1 / 10 ∧
        posteriorAfter selectedPrior (fun _ => true) 2 true = 9 / 10 ∧
        posteriorAfter selectedPrior (fun _ => true) 2 ≠ selectedPrior) ∧
      trajectoryLaw.real
          (posteriorBadMassFailure selectedPrior 2 (identificationGap / 2)) ≤
        Real.exp
          (-((2 : ℝ) * (identificationGap / 2)) ^ 2 /
            (2 * ∑ _index : Fin 2, logLikelihoodRatioProxy)) ∧
      (∃ hEvidence :
          0 < predictedOutcome
            (symmetricBoolModel selectedPrior) false true,
        (∀ recognition : FiniteLaw Bool,
          variationalFreeEnergy (symmetricBoolModel selectedPrior) false true
                hEvidence recognition =
              outcomeSurprisal (symmetricBoolModel selectedPrior) false true ↔
            recognition = posteriorState
              (symmetricBoolModel selectedPrior) false true hEvidence) ∧
          ((variationalFreeEnergy
                (symmetricBoolModel selectedPrior) false true hEvidence
                selectedPrior -
              variationalFreeEnergy
                (symmetricBoolModel selectedPrior) false true hEvidence
                (posteriorState
                  (symmetricBoolModel selectedPrior) false true hEvidence) =
              finiteKL selectedPrior
                (posteriorState
                  (symmetricBoolModel selectedPrior) false true hEvidence)) ∧
            InformationTheory.klDiv
                (embeddedLaw selectedPrior)
                (embeddedLaw
                  (posteriorState
                    (symmetricBoolModel selectedPrior) false true hEvidence)) =
              ENNReal.ofReal
                (variationalFreeEnergy
                    (symmetricBoolModel selectedPrior) false true hEvidence
                    selectedPrior -
                  variationalFreeEnergy
                    (symmetricBoolModel selectedPrior) false true hEvidence
                    (posteriorState
                      (symmetricBoolModel selectedPrior) false true
                        hEvidence)))) ∧
      (policyTreeValue boolFeedbackModel boolFeedbackTree false = 0 ∧
        (∀ fixedAction,
          policyTreeValue boolFeedbackModel boolFeedbackTree false <
            openLoopValue boolFeedbackModel
              (boolOpenLoopPlan fixedAction) false) ∧
        FEPComposed.FinitePolicyAction.boolFeedbackActionInterface.policyToAction
              (boolFeedbackTree.2 false) ≠
          FEPComposed.FinitePolicyAction.boolFeedbackActionInterface.policyToAction
              (boolFeedbackTree.2 true) ∧
        ∀ observation,
          FEPComposed.FinitePolicyAction.boolFeedbackActionInterface.policyToAction
                (boolFeedbackTree.2 observation) = observation ∧
            boolMismatchCost
                (boolFeedbackModel.update false false observation)
                (FEPComposed.FinitePolicyAction.boolFeedbackActionInterface.policyToAction
                  (boolFeedbackTree.2 observation)) = 0 ∧
            optimalTreeAction boolFeedbackModel 0
                (boolFeedbackModel.update false false observation) =
              FEPComposed.FinitePolicyAction.boolFeedbackActionInterface.policyToAction
                (boolFeedbackTree.2 observation) ∧
            boolBeliefInterpret
                (boolFeedbackModel.update false false observation) =
              actionPrediction (boolBeliefInterpret false) boolActionTransition
                (FEPComposed.FinitePolicyAction.boolFeedbackActionInterface.policyToAction
                  (boolFeedbackTree.2 observation)) ∧
            FEPComposed.FinitePolicyAction.boolFeedbackActionInterface.actionTransition
                (FEPComposed.FinitePolicyAction.boolFeedbackActionInterface.policyToAction
                  (boolFeedbackTree.2 observation)) =
              FEPComposed.FinitePolicyAction.boolFeedbackActionModel.transition
                (boolFeedbackTree.2 observation)) ∧
      (((FiniteLaw.uniform : FiniteLaw Bool).product
            (FiniteLaw.uniform : FiniteLaw (Bool × (Bool × Bool))) =
          boolBlanketStationaryLaw) ∧
        IsInvariant
          ((FiniteLaw.uniform : FiniteLaw Bool).product
            (FiniteLaw.uniform : FiniteLaw (Bool × (Bool × Bool))))
          (pairedKernel
            (FiniteKernel.identity : FiniteKernel Bool Bool)
            (FiniteKernel.identity :
              FiniteKernel (Bool × (Bool × Bool)) (Bool × (Bool × Bool)))) ∧
        ∃ blanketModel :
            ConditionalBlanketModel Unit Bool (Bool × (Bool × Bool)),
          blanketModel.conditional () =
              (FiniteLaw.uniform : FiniteLaw Bool).product
                (FiniteLaw.uniform : FiniteLaw (Bool × (Bool × Bool))) ∧
            Factorizes blanketModel ∧ blanketModel.blanketLaw () = 1) ∧
      IsInvariant boolBlanketStationaryLaw boolBlanketRefreshKernel ∧
      (∀ source target, 0 < boolBlanketRefreshKernel source target) ∧
      boolBlanketOrigin ≠ boolBlanketAlternative ∧
      0 < boolBlanketStationaryLaw boolBlanketOrigin ∧
      0 < boolBlanketStationaryLaw boolBlanketAlternative ∧
      InformationTheory.klDiv
          (embeddedLaw boolBlanketEvolvedLaw)
          (embeddedLaw boolBlanketStationaryLaw) ≤
        InformationTheory.klDiv
          (embeddedLaw boolBlanketInitialLaw)
          (embeddedLaw boolBlanketStationaryLaw) ∧
      finiteKL boolBlanketEvolvedLaw boolBlanketStationaryLaw <
        finiteKL boolBlanketInitialLaw boolBlanketStationaryLaw ∧
      InformationTheory.klDiv
          (embeddedLaw boolBlanketEvolvedLaw)
          (embeddedLaw boolBlanketStationaryLaw) <
        InformationTheory.klDiv
          (embeddedLaw boolBlanketInitialLaw)
          (embeddedLaw boolBlanketStationaryLaw) := by
  have hEvidence :
      0 < selectedLikelihood.predictive selectedPrior true :=
    selectedPredictive_pos selectedPrior true
  have hNormalized :
      ∑ hypothesis, posteriorUpdate selectedPrior true hypothesis = 1 := by
    exact (posteriorUpdate selectedPrior true).sum_one
  have hLearned := posteriorAfter_two_true_witness
  have hIdentificationGapPositive : 0 < identificationGap := by
    rw [identificationGap]
    positivity
  have hFailureBound :=
    posteriorBadMass_failure_probability_le
      selectedPrior 2 (identificationGap / 2) (by norm_num)
      (div_pos hIdentificationGapPositive (by norm_num))
      (half_lt_self hIdentificationGapPositive)
      (by norm_num [selectedPrior, FEP.DecisionRisk.boolFairLaw,
        truthHypothesis])
  have hVfeEvidence :
      0 < predictedOutcome (symmetricBoolModel selectedPrior) false true := by
    rw [symmetricBoolModel_predictedOutcome]
    norm_num [fairBoolLaw]
  have hVfePosteriorSupport :
      ∀ state,
        0 < posteriorState
          (symmetricBoolModel selectedPrior) false true hVfeEvidence state := by
    intro state
    cases state <;>
      norm_num [posteriorState, predictedState, predictedOutcome,
        symmetricBoolModel, fairBoolLaw, fairBoolKernel,
        FiniteKernel.posterior, FiniteKernel.predictive_mass,
        Fintype.sum_bool]
  have hVfeGap :=
    FEPComposed.FinitePolicyAction.vfeGap_eq_finiteKL_recognition_posterior
      (symmetricBoolModel selectedPrior) false true hVfeEvidence selectedPrior
      hVfePosteriorSupport
  have hVfe :
      ∃ hEvidence :
          0 < predictedOutcome
            (symmetricBoolModel selectedPrior) false true,
        (∀ recognition : FiniteLaw Bool,
          variationalFreeEnergy (symmetricBoolModel selectedPrior) false true
                hEvidence recognition =
              outcomeSurprisal (symmetricBoolModel selectedPrior) false true ↔
            recognition = posteriorState
              (symmetricBoolModel selectedPrior) false true hEvidence) ∧
          ((variationalFreeEnergy
                (symmetricBoolModel selectedPrior) false true hEvidence
                selectedPrior -
              variationalFreeEnergy
                (symmetricBoolModel selectedPrior) false true hEvidence
                (posteriorState
                  (symmetricBoolModel selectedPrior) false true hEvidence) =
              finiteKL selectedPrior
                (posteriorState
                  (symmetricBoolModel selectedPrior) false true hEvidence)) ∧
            InformationTheory.klDiv
                (embeddedLaw selectedPrior)
                (embeddedLaw
                  (posteriorState
                    (symmetricBoolModel selectedPrior) false true hEvidence)) =
              ENNReal.ofReal
                (variationalFreeEnergy
                    (symmetricBoolModel selectedPrior) false true hEvidence
                    selectedPrior -
                  variationalFreeEnergy
                    (symmetricBoolModel selectedPrior) false true hEvidence
                    (posteriorState
                      (symmetricBoolModel selectedPrior) false true
                        hEvidence))) := by
    refine ⟨hVfeEvidence, ?_, hVfeGap⟩
    intro recognition
    exact variationalFreeEnergy_eq_surprisal_iff
      (symmetricBoolModel selectedPrior) false true hVfeEvidence recognition
  have hFeedback :=
    FEPComposed.FinitePolicyAction.boolFeedback_observation_changes_emittedAction
  have hInternalInvariant :
      IsInvariant (FiniteLaw.uniform : FiniteLaw Bool)
        (FiniteKernel.identity : FiniteKernel Bool Bool) := by
    exact FiniteKernel.predictive_identity _
  have hExternalInvariant :
      IsInvariant
        (FiniteLaw.uniform : FiniteLaw (Bool × (Bool × Bool)))
        (FiniteKernel.identity :
          FiniteKernel (Bool × (Bool × Bool)) (Bool × (Bool × Bool))) := by
    exact FiniteKernel.predictive_identity _
  have hFactorizedPredecessor :=
    FEPComposed.FiniteScientificImplications.factorizedProduct_invariant_under_pairedKernel
      (FiniteLaw.uniform : FiniteLaw Bool)
      (FiniteLaw.uniform : FiniteLaw (Bool × (Bool × Bool)))
      (FiniteKernel.identity : FiniteKernel Bool Bool)
      (FiniteKernel.identity :
        FiniteKernel (Bool × (Bool × Bool)) (Bool × (Bool × Bool)))
      hInternalInvariant hExternalInvariant
  have hStationaryProduct :
      (FiniteLaw.uniform : FiniteLaw Bool).product
          (FiniteLaw.uniform : FiniteLaw (Bool × (Bool × Bool))) =
        boolBlanketStationaryLaw := by
    apply FiniteLaw.ext_mass
    funext state
    norm_num [FiniteLaw.product, FiniteLaw.uniform,
      boolBlanketStationaryLaw]
  have hFactorized :
      (((FiniteLaw.uniform : FiniteLaw Bool).product
            (FiniteLaw.uniform : FiniteLaw (Bool × (Bool × Bool))) =
          boolBlanketStationaryLaw) ∧
        IsInvariant
          ((FiniteLaw.uniform : FiniteLaw Bool).product
            (FiniteLaw.uniform : FiniteLaw (Bool × (Bool × Bool))))
          (pairedKernel
            (FiniteKernel.identity : FiniteKernel Bool Bool)
            (FiniteKernel.identity :
              FiniteKernel (Bool × (Bool × Bool)) (Bool × (Bool × Bool)))) ∧
        ∃ blanketModel :
            ConditionalBlanketModel Unit Bool (Bool × (Bool × Bool)),
          blanketModel.conditional () =
              (FiniteLaw.uniform : FiniteLaw Bool).product
                (FiniteLaw.uniform : FiniteLaw (Bool × (Bool × Bool))) ∧
            Factorizes blanketModel ∧ blanketModel.blanketLaw () = 1) :=
    ⟨hStationaryProduct, hFactorizedPredecessor.1,
      hFactorizedPredecessor.2⟩
  have hRefreshTimeNonnegative : 0 ≤ boolBlanketRefreshTime := by
    norm_num [boolBlanketRefreshTime]
  have hRefreshInvariant :
      IsInvariant boolBlanketStationaryLaw boolBlanketRefreshKernel := by
    simpa [boolBlanketRefreshKernel] using
      (boolBlanketStationaryLaw_isStationary
        boolBlanketRefreshTime hRefreshTimeNonnegative)
  have hRefreshPositive :
      ∀ source target, 0 < boolBlanketRefreshKernel source target := by
    intro source target
    simpa [boolBlanketRefreshKernel, FiniteMarkovSemigroup.kernel] using
      (blanketRefreshSemigroup_transition_pos
        (Internal := Bool) (Sensory := Bool) (Active := Bool)
        (External := Bool)
        (by norm_num [boolBlanketRefreshTime]) source target)
  have hBlanketStatesDistinct :
      boolBlanketOrigin ≠ boolBlanketAlternative := by
    norm_num [boolBlanketOrigin, boolBlanketAlternative]
  have hStationaryOriginPositive :
      0 < boolBlanketStationaryLaw boolBlanketOrigin := by
    norm_num [boolBlanketStationaryLaw, FiniteLaw.uniform]
  have hStationaryAlternativePositive :
      0 < boolBlanketStationaryLaw boolBlanketAlternative := by
    norm_num [boolBlanketStationaryLaw, FiniteLaw.uniform]
  have hNativeContraction :
      InformationTheory.klDiv
          (embeddedLaw boolBlanketEvolvedLaw)
          (embeddedLaw boolBlanketStationaryLaw) ≤
        InformationTheory.klDiv
          (embeddedLaw boolBlanketInitialLaw)
          (embeddedLaw boolBlanketStationaryLaw) := by
    simpa [boolBlanketEvolvedLaw, boolBlanketRefreshKernel] using
      (FiniteMarkovSemigroup.nativeKL_contraction_to_invariant
        (blanketRefreshSemigroup
          (Internal := Bool) (Sensory := Bool) (Active := Bool)
          (External := Bool))
        boolBlanketRefreshTime hRefreshTimeNonnegative
        boolBlanketInitialLaw boolBlanketStationaryLaw hRefreshInvariant)
  exact
    ⟨hEvidence, hNormalized, hLearned, hFailureBound, hVfe, hFeedback,
      hFactorized, hRefreshInvariant, hRefreshPositive,
      hBlanketStatesDistinct, hStationaryOriginPositive,
      hStationaryAlternativePositive, hNativeContraction,
      boolBlanket_finiteKL_strict_decrease,
      boolBlanket_nativeKL_strict_decrease⟩

/-! ## Repaired shared-carrier terminal theorem -/

/-- One exact learned posterior is lifted to the sixteen-state Boolean blanket,
updated by the hold-policy observation, consumed by the posterior-dependent
feedback tree, and evolved by the true action's certified refresh slice.  The
KL clauses use that same lifted updated posterior; the separate point-mass
strictness witnesses above are not substituted into this result. -/
theorem finiteReferenceAgent_terminal :
    let learned : FiniteLaw Bool :=
      posteriorAfter selectedPrior (fun _ => true) 2
    let updatedInternal : FiniteLaw Bool := posteriorUpdate learned true
    let liftedLearned : FiniteLaw BoolBlanketState := liftInternalLaw learned
    let liftedUpdated : FiniteLaw BoolBlanketState :=
      liftInternalLaw updatedInternal
    let model :=
      boolBlanketGenerativeModel liftedLearned
        (liftInternalLikelihood selectedLikelihood)
        (FiniteLaw.uniform : FiniteLaw Bool)
        (FiniteLaw.uniform : FiniteLaw Bool)
    let actionInterface :=
      boolBlanketGenerativeModelActionInterface liftedLearned
        (liftInternalLikelihood selectedLikelihood)
        (FiniteLaw.uniform : FiniteLaw Bool)
        (FiniteLaw.uniform : FiniteLaw Bool)
    let emittedTrueAction : Bool :=
      actionInterface.policyToAction
        (selectedPosteriorFeedbackTree.2 true).1
    let selectedKernel : FiniteKernel BoolBlanketState BoolBlanketState :=
      actionInterface.actionTransition emittedTrueAction
    let stationary : FiniteLaw BoolBlanketState := boolBlanketStationaryLaw
    ∃ hEvidence : 0 < predictedOutcome model false true,
      learned false = 1 / 10 ∧
      learned true = 9 / 10 ∧
      learned ≠ selectedPrior ∧
      liftedLearned.fstMarginal = learned ∧
      selectedBeliefInterpret SelectedBeliefIndex.learned = learned ∧
      (∑ hypothesis, updatedInternal hypothesis = 1) ∧
      updatedInternal ≠ learned ∧
      trajectoryLaw.real
          (posteriorBadMassFailure selectedPrior 2 (identificationGap / 2)) ≤
        Real.exp
          (-((2 : ℝ) * (identificationGap / 2)) ^ 2 /
            (2 * ∑ _index : Fin 2, logLikelihoodRatioProxy)) ∧
      predictedOutcome model false = selectedLikelihood.predictive learned ∧
      posteriorState model false true hEvidence = liftedUpdated ∧
      (posteriorState model false true hEvidence).fstMarginal =
        selectedBeliefInterpret
          (selectedBeliefUpdate SelectedBeliefIndex.learned false true) ∧
      (posteriorState model false true hEvidence).fstMarginal =
        selectedBeliefInterpret
          (selectedPosteriorFeedbackModel.update
            SelectedBeliefIndex.learned false true) ∧
      (∀ recognition : FiniteLaw BoolBlanketState,
        variationalFreeEnergy model false true hEvidence recognition =
            outcomeSurprisal model false true ↔
          recognition = liftedUpdated) ∧
      optimalTreeAction selectedPosteriorFeedbackModel 0
          (SelectedBeliefIndex.afterObservation true) =
        (selectedPosteriorFeedbackTree.2 true).1 ∧
      (∀ fixedAction,
        policyTreeValue selectedPosteriorFeedbackModel
            selectedPosteriorFeedbackTree SelectedBeliefIndex.learned <
          openLoopValue selectedPosteriorFeedbackModel
            (selectedPosteriorOpenLoopPlan fixedAction)
            SelectedBeliefIndex.learned) ∧
      emittedTrueAction = true ∧
      selectedKernel =
        model.transition (selectedPosteriorFeedbackTree.2 true).1 ∧
      selectedKernel =
        boolBlanketActionIndexedSemigroup.sampledKernel true ∧
      boolBlanketActionIndexedSemigroup.sampledKernel true =
        boolBlanketRefreshKernel ∧
      (FiniteLaw.uniform : FiniteLaw Bool).product
          (FiniteLaw.uniform : FiniteLaw (Bool × (Bool × Bool))) = stationary ∧
      (∃ blanketModel :
          ConditionalBlanketModel
            (FEP.MarkovBlanket.Blanket Bool Bool) Bool Bool,
        (∀ blanket, 0 < blanketModel.blanketLaw blanket) ∧
          (∃ blanketFirst blanketSecond,
            blanketFirst ≠ blanketSecond ∧
              0 < blanketModel.blanketLaw blanketFirst ∧
              0 < blanketModel.blanketLaw blanketSecond) ∧
          Factorizes blanketModel ∧
          ∀ internal sensory active external,
            stationary (internal, (sensory, (active, external))) =
              blanketModel.blanketLaw (sensory, active) *
                blanketModel.conditional (sensory, active)
                  (internal, external)) ∧
      IsInvariant stationary selectedKernel ∧
      Fintype.card BoolBlanketState = 16 ∧
      boolBlanketOrigin ≠ boolBlanketAlternative ∧
      0 < stationary boolBlanketOrigin ∧
      0 < stationary boolBlanketAlternative ∧
      0 < liftedUpdated boolBlanketOrigin ∧
      0 < liftedUpdated boolBlanketAlternative ∧
      InformationTheory.klDiv
          (embeddedLaw (selectedKernel.predictive liftedUpdated))
          (embeddedLaw stationary) ≤
        InformationTheory.klDiv
          (embeddedLaw liftedUpdated) (embeddedLaw stationary) ∧
      finiteKL (selectedKernel.predictive liftedUpdated) stationary <
        finiteKL liftedUpdated stationary ∧
      InformationTheory.klDiv
          (embeddedLaw (selectedKernel.predictive liftedUpdated))
          (embeddedLaw stationary) <
        InformationTheory.klDiv
          (embeddedLaw liftedUpdated) (embeddedLaw stationary) := by
  dsimp only
  let learned : FiniteLaw Bool :=
    posteriorAfter selectedPrior (fun _ => true) 2
  let updatedInternal : FiniteLaw Bool := posteriorUpdate learned true
  let liftedLearned : FiniteLaw BoolBlanketState := liftInternalLaw learned
  let liftedUpdated : FiniteLaw BoolBlanketState := liftInternalLaw updatedInternal
  let model :=
    boolBlanketGenerativeModel liftedLearned
      (liftInternalLikelihood selectedLikelihood)
      (FiniteLaw.uniform : FiniteLaw Bool)
      (FiniteLaw.uniform : FiniteLaw Bool)
  let actionInterface :=
    boolBlanketGenerativeModelActionInterface liftedLearned
      (liftInternalLikelihood selectedLikelihood)
      (FiniteLaw.uniform : FiniteLaw Bool)
      (FiniteLaw.uniform : FiniteLaw Bool)
  let emittedTrueAction : Bool :=
    actionInterface.policyToAction
      (selectedPosteriorFeedbackTree.2 true).1
  let selectedKernel : FiniteKernel BoolBlanketState BoolBlanketState :=
    actionInterface.actionTransition emittedTrueAction
  let stationary : FiniteLaw BoolBlanketState := boolBlanketStationaryLaw
  have hLearned := posteriorAfter_two_true_witness
  have hLearnedFalse : learned false = 1 / 10 := by
    simpa [learned] using hLearned.1
  have hLearnedTrue : learned true = 9 / 10 := by
    simpa [learned] using hLearned.2.1
  have hLearnedNonconstant : learned ≠ selectedPrior := by
    simpa [learned] using hLearned.2.2
  have hLiftedLearnedMarginal : liftedLearned.fstMarginal = learned := by
    simpa [liftedLearned] using liftInternalLaw_fstMarginal learned
  have hPolicyRoot :
      selectedBeliefInterpret SelectedBeliefIndex.learned = learned := by
    rfl
  have hUpdatedNormalized : ∑ hypothesis, updatedInternal hypothesis = 1 := by
    exact updatedInternal.sum_one
  have hUpdatedNonconstant : updatedInternal ≠ learned := by
    intro hEqual
    have hFalseMass :=
      congrArg (fun law : FiniteLaw Bool => law false) hEqual
    norm_num [updatedInternal, learned, posteriorUpdate, posteriorAfter,
      selectedPrior, FEP.DecisionRisk.boolFairLaw, selectedLikelihood,
      FiniteKernel.posterior, FiniteKernel.predictive_mass,
      Fintype.sum_bool] at hFalseMass
  have hIdentificationGapPositive : 0 < identificationGap := by
    rw [identificationGap]
    positivity
  have hFailureBound :=
    posteriorBadMass_failure_probability_le
      selectedPrior 2 (identificationGap / 2) (by norm_num)
      (div_pos hIdentificationGapPositive (by norm_num))
      (half_lt_self hIdentificationGapPositive)
      (by norm_num [selectedPrior, FEP.DecisionRisk.boolFairLaw,
        truthHypothesis])
  have hInternalEvidence :
      0 < selectedLikelihood.predictive learned true :=
    selectedPredictive_pos learned true
  have hPredicted :
      predictedOutcome model false = selectedLikelihood.predictive learned := by
    simpa [model, liftedLearned] using
      (boolBlanketGenerativeModel_false_predictedOutcome learned
        selectedLikelihood (FiniteLaw.uniform : FiniteLaw Bool)
        (FiniteLaw.uniform : FiniteLaw Bool))
  have hEvidence : 0 < predictedOutcome model false true := by
    rw [hPredicted]
    exact hInternalEvidence
  have hPosterior :
      posteriorState model false true hEvidence = liftedUpdated := by
    simpa [model, liftedLearned, liftedUpdated, updatedInternal,
      posteriorUpdate] using
      (boolBlanketGenerativeModel_false_posteriorState learned
        selectedLikelihood (FiniteLaw.uniform : FiniteLaw Bool)
        (FiniteLaw.uniform : FiniteLaw Bool) true hInternalEvidence)
  have hUpdatedMarginal :
      (posteriorState model false true hEvidence).fstMarginal =
        selectedBeliefInterpret
          (selectedBeliefUpdate SelectedBeliefIndex.learned false true) := by
    calc
      (posteriorState model false true hEvidence).fstMarginal =
          liftedUpdated.fstMarginal := congrArg FiniteLaw.fstMarginal hPosterior
      _ = updatedInternal := by
        simpa [liftedUpdated] using liftInternalLaw_fstMarginal updatedInternal
      _ = selectedBeliefInterpret
          (selectedBeliefUpdate SelectedBeliefIndex.learned false true) := by
        simpa [updatedInternal, learned, selectedBeliefInterpret] using
          (selectedBeliefUpdate_commutes_posteriorUpdate false true).symm
  have hFeedbackModelUpdatedMarginal :
      (posteriorState model false true hEvidence).fstMarginal =
        selectedBeliefInterpret
          (selectedPosteriorFeedbackModel.update
            SelectedBeliefIndex.learned false true) := by
    simpa [selectedPosteriorFeedbackModel] using hUpdatedMarginal
  have hVfe :
      ∀ recognition : FiniteLaw BoolBlanketState,
        variationalFreeEnergy model false true hEvidence recognition =
            outcomeSurprisal model false true ↔
          recognition = liftedUpdated := by
    intro recognition
    simpa only [hPosterior] using
      (variationalFreeEnergy_eq_surprisal_iff
        model false true hEvidence recognition)
  have hOptimal := selectedPosteriorFeedback_continuation_optimal true
  have hFeedback := selectedPosteriorFeedback_strictlyBetter
  have hEmittedTrue : emittedTrueAction = true := by
    rfl
  have hGenerativeTransition :
      selectedKernel =
        model.transition (selectedPosteriorFeedbackTree.2 true).1 := by
    rfl
  have hSelectedAction :
      selectedKernel =
        boolBlanketActionIndexedSemigroup.sampledKernel true := by
    simpa [selectedKernel, emittedTrueAction, actionInterface, model,
      boolBlanketGenerativeModelActionInterface,
      boolBlanketGenerativeModel,
      ActionIndexedSemigroup.toGenerativeModelActionInterface,
      selectedPosteriorFeedbackTree] using
      (FEP.ContinuousTimeMarkov.ActionIndexedSemigroup.selectedActionTransition_eq_sampledSemigroup
          boolBlanketActionIndexedSemigroup
          (boolBlanketGenerativeModel liftedLearned
            (liftInternalLikelihood selectedLikelihood)
            (FiniteLaw.uniform : FiniteLaw Bool)
            (FiniteLaw.uniform : FiniteLaw Bool)) id
          (fun policy => by
            exact
              (boolBlanketGenerativeModel_transition liftedLearned
                (liftInternalLikelihood selectedLikelihood)
                (FiniteLaw.uniform : FiniteLaw Bool)
                (FiniteLaw.uniform : FiniteLaw Bool) policy).symm)
          true)
  have hTrueKernel := boolBlanketActionIndexedSemigroup_true_kernel
  have hStationaryProduct :
      (FiniteLaw.uniform : FiniteLaw Bool).product
          (FiniteLaw.uniform : FiniteLaw (Bool × (Bool × Bool))) = stationary := by
    apply FiniteLaw.ext_mass
    funext state
    norm_num [stationary, boolBlanketStationaryLaw, FiniteLaw.product,
      FiniteLaw.uniform]
  let blanketModel :
      ConditionalBlanketModel
        (FEP.MarkovBlanket.Blanket Bool Bool) Bool Bool :=
    { blanketLaw :=
        (FiniteLaw.uniform :
          FiniteLaw (FEP.MarkovBlanket.Blanket Bool Bool))
      conditional := fun _ =>
        (FiniteLaw.uniform : FiniteLaw Bool).product
          (FiniteLaw.uniform : FiniteLaw Bool) }
  have hBlanketSupport :
      ∀ blanket, 0 < blanketModel.blanketLaw blanket := by
    intro blanket
    norm_num [blanketModel, FiniteLaw.uniform, FEP.MarkovBlanket.Blanket]
  have hBlanketPair :
      ∃ blanketFirst blanketSecond,
        blanketFirst ≠ blanketSecond ∧
          0 < blanketModel.blanketLaw blanketFirst ∧
          0 < blanketModel.blanketLaw blanketSecond := by
    exact
      ⟨(false, false), (true, true), by norm_num,
        hBlanketSupport (false, false), hBlanketSupport (true, true)⟩
  have hBlanketFactorizes : Factorizes blanketModel := by
    intro blanket
    change
      (FiniteLaw.uniform : FiniteLaw Bool).product
          (FiniteLaw.uniform : FiniteLaw Bool) =
        ((FiniteLaw.uniform : FiniteLaw Bool).product
            (FiniteLaw.uniform : FiniteLaw Bool)).fstMarginal.product
          ((FiniteLaw.uniform : FiniteLaw Bool).product
            (FiniteLaw.uniform : FiniteLaw Bool)).sndMarginal
    rw [FiniteLaw.product_fstMarginal, FiniteLaw.product_sndMarginal]
  have hStationaryFactorization :
      ∀ internal sensory active external,
        stationary (internal, (sensory, (active, external))) =
          blanketModel.blanketLaw (sensory, active) *
            blanketModel.conditional (sensory, active)
              (internal, external) := by
    intro internal sensory active external
    norm_num [stationary, blanketModel, boolBlanketStationaryLaw,
      FiniteLaw.uniform, FiniteLaw.product, FEP.MarkovBlanket.Blanket]
  have hFactorized :
      ∃ blanketModel :
          ConditionalBlanketModel
            (FEP.MarkovBlanket.Blanket Bool Bool) Bool Bool,
        (∀ blanket, 0 < blanketModel.blanketLaw blanket) ∧
          (∃ blanketFirst blanketSecond,
            blanketFirst ≠ blanketSecond ∧
              0 < blanketModel.blanketLaw blanketFirst ∧
              0 < blanketModel.blanketLaw blanketSecond) ∧
          Factorizes blanketModel ∧
          ∀ internal sensory active external,
            stationary (internal, (sensory, (active, external))) =
              blanketModel.blanketLaw (sensory, active) *
                blanketModel.conditional (sensory, active)
                  (internal, external) := by
    exact
      ⟨blanketModel, hBlanketSupport, hBlanketPair,
        hBlanketFactorizes, hStationaryFactorization⟩
  have hRefreshTimePositive : 0 < boolBlanketRefreshTime := by
    norm_num [boolBlanketRefreshTime]
  have hRefreshInvariant :
      IsInvariant stationary boolBlanketRefreshKernel := by
    simpa [stationary, boolBlanketRefreshKernel] using
      (boolBlanketStationaryLaw_isStationary
        boolBlanketRefreshTime hRefreshTimePositive.le)
  have hSelectedInvariant : IsInvariant stationary selectedKernel := by
    simpa only [hSelectedAction, hTrueKernel] using hRefreshInvariant
  have hCarrierCard : Fintype.card BoolBlanketState = 16 :=
    boolBlanketState_card
  have hStatesDistinct : boolBlanketOrigin ≠ boolBlanketAlternative := by
    norm_num [boolBlanketOrigin, boolBlanketAlternative]
  have hStationaryOrigin : 0 < stationary boolBlanketOrigin := by
    norm_num [stationary, boolBlanketStationaryLaw, FiniteLaw.uniform]
  have hStationaryAlternative : 0 < stationary boolBlanketAlternative := by
    norm_num [stationary, boolBlanketStationaryLaw, FiniteLaw.uniform]
  have hLiftedOrigin : 0 < liftedUpdated boolBlanketOrigin := by
    norm_num [liftedUpdated, updatedInternal, learned, liftInternalLaw,
      posteriorUpdate, posteriorAfter, selectedPrior,
      FEP.DecisionRisk.boolFairLaw, selectedLikelihood,
      FiniteLaw.product, FiniteLaw.uniform, FiniteKernel.posterior,
      FiniteKernel.predictive_mass, Fintype.sum_bool, boolBlanketOrigin]
  have hLiftedAlternative : 0 < liftedUpdated boolBlanketAlternative := by
    norm_num [liftedUpdated, updatedInternal, learned, liftInternalLaw,
      posteriorUpdate, posteriorAfter, selectedPrior,
      FEP.DecisionRisk.boolFairLaw, selectedLikelihood,
      FiniteLaw.product, FiniteLaw.uniform, FiniteKernel.posterior,
      FiniteKernel.predictive_mass, Fintype.sum_bool, boolBlanketAlternative]
  have hUpdatedNeUniform :
      updatedInternal ≠ (FiniteLaw.uniform : FiniteLaw Bool) := by
    intro hEqual
    have hFalseMass :=
      congrArg (fun law : FiniteLaw Bool => law false) hEqual
    norm_num [updatedInternal, learned, posteriorUpdate, posteriorAfter,
      selectedPrior, FEP.DecisionRisk.boolFairLaw, selectedLikelihood,
      FiniteLaw.uniform, FiniteKernel.posterior,
      FiniteKernel.predictive_mass, Fintype.sum_bool] at hFalseMass
  have hLiftedNeUniform :
      liftedUpdated ≠ (FiniteLaw.uniform : FiniteLaw BoolBlanketState) := by
    simpa [liftedUpdated] using
      liftInternalLaw_ne_uniform_of_ne_uniform updatedInternal hUpdatedNeUniform
  have hNativeNonincrease :
      InformationTheory.klDiv
          (embeddedLaw (selectedKernel.predictive liftedUpdated))
          (embeddedLaw stationary) ≤
        InformationTheory.klDiv
          (embeddedLaw liftedUpdated) (embeddedLaw stationary) := by
    rw [hSelectedAction, hTrueKernel]
    simpa [stationary, boolBlanketRefreshKernel] using
      (FiniteMarkovSemigroup.nativeKL_contraction_to_invariant
        (blanketRefreshSemigroup
          (Internal := Bool) (Sensory := Bool) (Active := Bool)
          (External := Bool))
        boolBlanketRefreshTime hRefreshTimePositive.le liftedUpdated stationary
        hRefreshInvariant)
  have hFiniteStrict :
      finiteKL (selectedKernel.predictive liftedUpdated) stationary <
        finiteKL liftedUpdated stationary := by
    rw [hSelectedAction, hTrueKernel]
    simpa [stationary, boolBlanketStationaryLaw, boolBlanketRefreshKernel,
      blanketRefreshSemigroup] using
      (refreshSemigroup_finiteKL_strict_decrease_of_ne_uniform
        (State := BoolBlanketState) liftedUpdated hRefreshTimePositive
        hLiftedNeUniform)
  have hNativeStrict :
      InformationTheory.klDiv
          (embeddedLaw (selectedKernel.predictive liftedUpdated))
          (embeddedLaw stationary) <
        InformationTheory.klDiv
          (embeddedLaw liftedUpdated) (embeddedLaw stationary) := by
    rw [hSelectedAction, hTrueKernel]
    simpa [stationary, boolBlanketStationaryLaw, boolBlanketRefreshKernel,
      blanketRefreshSemigroup] using
      (refreshSemigroup_nativeKL_strict_decrease_of_ne_uniform
        (State := BoolBlanketState) liftedUpdated hRefreshTimePositive
        hLiftedNeUniform)
  exact
    ⟨hEvidence, hLearnedFalse, hLearnedTrue, hLearnedNonconstant,
      hLiftedLearnedMarginal, hPolicyRoot, hUpdatedNormalized,
      hUpdatedNonconstant, hFailureBound, hPredicted, hPosterior,
      hUpdatedMarginal, hFeedbackModelUpdatedMarginal, hVfe, hOptimal,
      hFeedback, hEmittedTrue,
      hGenerativeTransition, hSelectedAction, hTrueKernel,
      hStationaryProduct, hFactorized, hSelectedInvariant, hCarrierCard,
      hStatesDistinct, hStationaryOrigin, hStationaryAlternative,
      hLiftedOrigin, hLiftedAlternative, hNativeNonincrease,
      hFiniteStrict, hNativeStrict⟩

end FEPComposed.FiniteReferenceAgent
