module
public import FepSketches.learning_theory
public import FepSketches.statistical_convergence
public import FepSketches.native_blanket
public import FepSketches.decision_risk
public import Mathlib.Probability.Independence.InfinitePi

@[expose] public section

/-!
# Selected finite posterior learning

This module selects one Boolean two-hypothesis model for the Horizon 1
reference agent.  Its repeated observations live on a concrete infinite
product measure.  Finite-sample concentration and almost-sure convergence are
kept as separate results, and neither is presented as empirical calibration or
a nonparametric rate.
-/

namespace FEP.FinitePosteriorLearning

open FEP Filter MeasureTheory ProbabilityTheory
open scoped BigOperators MeasureTheory NNReal ProbabilityTheory

noncomputable section

/-! ## Selected Boolean sampling model -/

/-- The two hypotheses in the terminal finite reference-agent model. -/
abbrev Hypothesis := Bool

/-- The finite observation alphabet shared by both hypotheses. -/
abbrev Observation := Bool

/-- Infinite observation paths carrying the selected repeated-sample law. -/
abbrev Trajectory := ℕ → Observation

/-- `true` is the selected data-generating hypothesis. -/
def truthHypothesis : Hypothesis := true

/-- The selected model emits the matching Boolean with probability `3/4` and
the other Boolean with probability `1/4`. -/
def selectedLikelihood : FiniteKernel Hypothesis Observation where
  mass hypothesis observation :=
    if hypothesis = observation then 3 / 4 else 1 / 4
  nonneg hypothesis observation := by
    split_ifs <;> norm_num
  sum_one hypothesis := by
    cases hypothesis <;> rw [Fintype.sum_bool] <;> norm_num

/-- The H1.2 fair Boolean law is reused as the selected model prior. -/
def selectedPrior : FiniteLaw Hypothesis :=
  FEP.DecisionRisk.boolFairLaw

/-- The one-coordinate observation law under the selected truth. -/
def truthObservationLaw : FiniteLaw Observation :=
  selectedLikelihood.row truthHypothesis

/-- Native probability measure associated with the selected finite truth law. -/
noncomputable def truthObservationMeasure : Measure Observation :=
  FEP.NativeBlanket.embeddedLaw truthObservationLaw

private noncomputable instance truthObservationMeasure_isProbabilityMeasure :
    IsProbabilityMeasure truthObservationMeasure := by
  unfold truthObservationMeasure
  infer_instance

/-- The concrete i.i.d. Boolean path measure used by both learning theorems. -/
noncomputable def trajectoryLaw : Measure Trajectory :=
  Measure.infinitePi fun _ : ℕ => truthObservationMeasure

noncomputable instance trajectoryLaw_isProbabilityMeasure :
    IsProbabilityMeasure trajectoryLaw := by
  unfold trajectoryLaw
  infer_instance

/-- Coordinate observations are independent because their law is the concrete
infinite product, not because independence was supplied as a premise. -/
theorem trajectoryCoordinates_iIndep :
    iIndepFun (fun index : ℕ => fun path : Trajectory => path index)
      trajectoryLaw := by
  unfold trajectoryLaw
  exact iIndepFun_infinitePi
    (P := fun _ : ℕ => truthObservationMeasure)
    (X := fun _ observation => observation) (by fun_prop)

/-- Every coordinate of the selected trajectory has the authored truth law. -/
theorem trajectoryCoordinate_map (index : ℕ) :
    trajectoryLaw.map (fun path : Trajectory => path index) =
      truthObservationMeasure := by
  simpa [trajectoryLaw] using
    (Measure.infinitePi_map_eval
      (fun _ : ℕ => truthObservationMeasure) index)

/-- Has-law form of the coordinate marginal identity. -/
private theorem trajectoryCoordinate_hasLaw (index : ℕ) :
    HasLaw (fun path : Trajectory => path index)
      truthObservationMeasure trajectoryLaw where
  aemeasurable := (measurable_pi_apply index).aemeasurable
  map_eq := trajectoryCoordinate_map index

/-! ## Derived finite-sample likelihood-gap bound -/

/-- Per-observation log likelihood of the inferior hypothesis relative to the
selected truth. -/
noncomputable def logLikelihoodRatio (observation : Observation) : ℝ :=
  Real.log
    (selectedLikelihood false observation /
      selectedLikelihood truthHypothesis observation)

/-- Lower endpoint of the selected Boolean log-likelihood ratio. -/
noncomputable def logLikelihoodRatioLower : ℝ := -Real.log 3

/-- Upper endpoint of the selected Boolean log-likelihood ratio. -/
noncomputable def logLikelihoodRatioUpper : ℝ := Real.log 3

/-- Positive expected per-observation separation of truth from the inferior
hypothesis. -/
noncomputable def identificationGap : ℝ := Real.log 3 / 2

/-- Hoeffding proxy induced by the exact selected log-likelihood-ratio range. -/
noncomputable def logLikelihoodRatioProxy : ℝ≥0 :=
  (‖logLikelihoodRatioUpper - logLikelihoodRatioLower‖₊ / 2) ^ 2

/-- The centered inferior-to-truth log-likelihood ratio. -/
noncomputable def centeredLogLikelihoodRatio
    (observation : Observation) : ℝ :=
  logLikelihoodRatio observation + identificationGap

private theorem logLikelihoodRatio_false :
    logLikelihoodRatio false = Real.log 3 := by
  norm_num [logLikelihoodRatio, selectedLikelihood, truthHypothesis]

private theorem logLikelihoodRatio_true :
    logLikelihoodRatio true = -Real.log 3 := by
  rw [logLikelihoodRatio]
  norm_num [selectedLikelihood, truthHypothesis]
  rw [show (1 / 3 : ℝ) = (3 : ℝ)⁻¹ by norm_num, Real.log_inv]

/-- The selected log-likelihood ratio is bounded at both Boolean atoms. -/
private theorem logLikelihoodRatio_mem_Icc (observation : Observation) :
    logLikelihoodRatio observation ∈
      Set.Icc logLikelihoodRatioLower logLikelihoodRatioUpper := by
  cases observation
  · rw [logLikelihoodRatio_false]
    exact ⟨by
      rw [logLikelihoodRatioLower]
      linarith [Real.log_pos (by norm_num : (1 : ℝ) < 3)], by
      rfl⟩
  · rw [logLikelihoodRatio_true]
    exact ⟨by rfl, by
      rw [logLikelihoodRatioUpper]
      linarith [Real.log_pos (by norm_num : (1 : ℝ) < 3)]⟩

/-- Under the selected truth, the inferior-to-truth log-likelihood ratio has
expectation exactly the negative identification gap. -/
private theorem logLikelihoodRatio_integral :
    ∫ observation, logLikelihoodRatio observation ∂truthObservationMeasure =
      -identificationGap := by
  rw [truthObservationMeasure,
    FEP.NativeBlanket.embeddedLaw_integral_eq_sum, Fintype.sum_bool]
  rw [logLikelihoodRatio_false, logLikelihoodRatio_true]
  norm_num [truthObservationLaw, selectedLikelihood, truthHypothesis,
    identificationGap, FiniteKernel.row]
  ring

/-- Hoeffding's lemma derives the centered sub-Gaussian certificate from the
exact two-point range; it is not an assumed concentration premise. -/
theorem centeredLogLikelihoodRatio_hasSubgaussianMGF :
    HasSubgaussianMGF centeredLogLikelihoodRatio
      logLikelihoodRatioProxy truthObservationMeasure := by
  have hHoeffding :=
    hasSubgaussianMGF_of_mem_Icc
      (μ := truthObservationMeasure) (X := logLikelihoodRatio)
      (by fun_prop)
      (Filter.Eventually.of_forall logLikelihoodRatio_mem_Icc)
  rw [logLikelihoodRatio_integral] at hHoeffding
  change HasSubgaussianMGF
    (fun observation => logLikelihoodRatio observation + identificationGap)
      logLikelihoodRatioProxy truthObservationMeasure
  simpa only [sub_neg_eq_add, logLikelihoodRatioProxy] using hHoeffding

/-- Centered coordinate observables for the first `sampleCount` observations. -/
private noncomputable def centeredObservables {sampleCount : ℕ}
    (index : Fin sampleCount) (path : Trajectory) : ℝ :=
  centeredLogLikelihoodRatio (path index)

/-- The finite family of centered observables inherits independence from the
concrete infinite-product coordinates. -/
private theorem centeredObservables_iIndep {sampleCount : ℕ} :
    iIndepFun (centeredObservables (sampleCount := sampleCount))
      trajectoryLaw := by
  have hCoordinates :
      iIndepFun
        (fun index : Fin sampleCount =>
          fun path : Trajectory => path index)
        trajectoryLaw :=
    trajectoryCoordinates_iIndep.precomp Fin.val_injective
  change iIndepFun
    (fun index : Fin sampleCount =>
      centeredLogLikelihoodRatio ∘ fun path : Trajectory => path index)
    trajectoryLaw
  exact hCoordinates.comp
    (fun _ : Fin sampleCount => centeredLogLikelihoodRatio)
    (fun _ => Measurable.of_discrete)

/-- Every centered coordinate has the same derived sub-Gaussian certificate. -/
private theorem centeredObservable_hasSubgaussianMGF {sampleCount : ℕ}
    (index : Fin sampleCount) :
    HasSubgaussianMGF
      (centeredObservables index) logLikelihoodRatioProxy trajectoryLaw := by
  change HasSubgaussianMGF
    (centeredLogLikelihoodRatio ∘ fun path : Trajectory => path index)
      logLikelihoodRatioProxy trajectoryLaw
  have hMapped := centeredLogLikelihoodRatio_hasSubgaussianMGF
  rw [← trajectoryCoordinate_map index] at hMapped
  have hEvaluation :
      AEMeasurable (fun path : Trajectory => path (index : ℕ)) trajectoryLaw :=
    (measurable_pi_apply (index : ℕ)).aemeasurable
  exact hMapped.of_map hEvaluation

/-- Event that the finite empirical log-likelihood gap loses at least
`deviation` relative to its positive population gap. -/
def finiteSampleBadGap (sampleCount : ℕ) (deviation : ℝ) : Set Trajectory :=
  {path |
    (sampleCount : ℝ) * deviation ≤
      ∑ index ∈ Finset.range sampleCount,
        centeredLogLikelihoodRatio (path index)}

/-- Explicit finite-sample probability of a bad empirical likelihood gap,
derived by feeding the selected Hoeffding certificate to the maintained
empirical-mean tail theorem. -/
theorem finiteSampleBadGap_probability_le
    (sampleCount : ℕ) (deviation : ℝ)
    (sampleCountPositive : 0 < sampleCount)
    (deviationPositive : 0 < deviation) :
    trajectoryLaw.real (finiteSampleBadGap sampleCount deviation) ≤
      Real.exp
        (-((sampleCount : ℝ) * deviation) ^ 2 /
          (2 * ∑ _index : Fin sampleCount, logLikelihoodRatioProxy)) := by
  have _sampleCountNonzero : sampleCount ≠ 0 := Nat.ne_of_gt sampleCountPositive
  have hTail :=
    FEP.LearningTheory.subGaussian_empiricalMean_tail
      trajectoryLaw
      (centeredObservables (sampleCount := sampleCount))
      centeredObservables_iIndep
      (fun _index : Fin sampleCount => logLikelihoodRatioProxy)
      centeredObservable_hasSubgaussianMGF
      deviationPositive.le
  have hEvent :
      {path : Trajectory |
        (sampleCount : ℝ) * deviation ≤
          ∑ index : Fin sampleCount,
            centeredObservables index path} =
        finiteSampleBadGap sampleCount deviation := by
    ext path
    change
      ((sampleCount : ℝ) * deviation ≤
        ∑ index : Fin sampleCount,
          centeredLogLikelihoodRatio (path (index : ℕ))) ↔
      ((sampleCount : ℝ) * deviation ≤
        ∑ index ∈ Finset.range sampleCount,
          centeredLogLikelihoodRatio (path index))
    rw [Fin.sum_univ_eq_sum_range
      (fun index : ℕ => centeredLogLikelihoodRatio (path index))]
  rw [← hEvent]
  exact hTail

/-! ## Repeated posterior update and finite-sample contraction -/

/-- Every selected likelihood atom is strictly positive. -/
theorem selectedLikelihood_pos (hypothesis : Hypothesis)
    (observation : Observation) :
    0 < selectedLikelihood hypothesis observation := by
  simp [selectedLikelihood]
  split_ifs <;> norm_num

/-- The selected observation has positive predictive mass under every
normalized prior. -/
theorem selectedPredictive_pos (prior : FiniteLaw Hypothesis)
    (observation : Observation) :
    0 < selectedLikelihood.predictive prior observation := by
  have hsum : prior true + prior false = 1 := by
    simpa [Fintype.sum_bool] using prior.sum_one
  rw [FiniteKernel.predictive_mass, Fintype.sum_bool]
  cases observation <;>
    simp only [selectedLikelihood, Bool.false_eq_true, Bool.true_eq_false,
      ↓reduceIte, eq_self] <;>
    nlinarith [prior.nonneg false, prior.nonneg true]

/-- One exact normalized Bayes update in the maintained `FiniteLaw` carrier. -/
noncomputable def posteriorUpdate (prior : FiniteLaw Hypothesis)
    (observation : Observation) : FiniteLaw Hypothesis :=
  selectedLikelihood.posterior prior observation
    (selectedPredictive_pos prior observation)

/-- Recursive repeated-sample posterior on the same Boolean model and belief
carrier used by the terminal reference agent. -/
noncomputable def posteriorAfter (prior : FiniteLaw Hypothesis)
    (path : Trajectory) : ℕ → FiniteLaw Hypothesis
  | 0 => prior
  | sampleCount + 1 =>
      posteriorUpdate (posteriorAfter prior path sampleCount)
        (path sampleCount)

/-- Inferior-to-truth odds of a finite Boolean belief. -/
noncomputable def priorBadOdds (belief : FiniteLaw Hypothesis) : ℝ :=
  belief false / belief truthHypothesis

/-- A positive truth mass remains positive after one selected update. -/
private theorem posteriorUpdate_truth_pos (prior : FiniteLaw Hypothesis)
    (observation : Observation) (truthPriorPositive : 0 < prior truthHypothesis) :
    0 < posteriorUpdate prior observation truthHypothesis := by
  unfold posteriorUpdate FiniteKernel.posterior
  exact div_pos
    (mul_pos truthPriorPositive
      (selectedLikelihood_pos truthHypothesis observation))
    (selectedPredictive_pos prior observation)

/-- A positive truth mass remains positive through every repeated update. -/
private theorem posteriorAfter_truth_pos (prior : FiniteLaw Hypothesis)
    (path : Trajectory) (truthPriorPositive : 0 < prior truthHypothesis) :
    ∀ sampleCount, 0 < posteriorAfter prior path sampleCount truthHypothesis
  | 0 => truthPriorPositive
  | sampleCount + 1 =>
      posteriorUpdate_truth_pos
        (posteriorAfter prior path sampleCount) (path sampleCount)
        (posteriorAfter_truth_pos prior path truthPriorPositive sampleCount)

/-- One posterior update multiplies inferior-to-truth odds by the selected
likelihood ratio. -/
private theorem posteriorUpdate_badOdds (prior : FiniteLaw Hypothesis)
    (observation : Observation) (truthPriorPositive : 0 < prior truthHypothesis) :
    priorBadOdds (posteriorUpdate prior observation) =
      priorBadOdds prior * Real.exp (logLikelihoodRatio observation) := by
  have hRecursion :=
    FEP.LearningTheory.posteriorOdds_recursion
      prior selectedLikelihood observation
      (selectedPredictive_pos prior observation) false truthHypothesis
      truthPriorPositive
      (selectedLikelihood_pos truthHypothesis observation)
  rw [logLikelihoodRatio, Real.exp_log (div_pos
    (selectedLikelihood_pos false observation)
    (selectedLikelihood_pos truthHypothesis observation))]
  simpa [priorBadOdds, posteriorUpdate,
    FEP.LearningTheory.posteriorOdds, logLikelihoodRatio] using hRecursion

/-- Repeated posterior odds are the prior odds times the exponential summed
log-likelihood ratio. -/
private theorem posteriorAfter_badOdds (prior : FiniteLaw Hypothesis)
    (path : Trajectory) (truthPriorPositive : 0 < prior truthHypothesis) :
    ∀ sampleCount,
      priorBadOdds (posteriorAfter prior path sampleCount) =
        priorBadOdds prior *
          Real.exp
            (∑ index ∈ Finset.range sampleCount,
              logLikelihoodRatio (path index))
  | 0 => by simp [posteriorAfter]
  | sampleCount + 1 => by
      rw [posteriorAfter,
        posteriorUpdate_badOdds
          (posteriorAfter prior path sampleCount) (path sampleCount)
          (posteriorAfter_truth_pos
            prior path truthPriorPositive sampleCount),
        posteriorAfter_badOdds prior path truthPriorPositive sampleCount,
        Finset.sum_range_succ, Real.exp_add]
      ring

/-- Inferior posterior mass is bounded by inferior-to-truth odds whenever the
truth retains positive mass. -/
private theorem posteriorBadMass_le_badOdds (belief : FiniteLaw Hypothesis)
    (truthMassPositive : 0 < belief truthHypothesis) :
    belief false ≤ priorBadOdds belief := by
  rw [priorBadOdds]
  apply (le_div_iff₀ truthMassPositive).2
  nlinarith [belief.nonneg false, belief.mass_le_one truthHypothesis]

/-- Outside the derived bad-gap event, the actual repeated posterior's
inferior mass contracts exponentially. -/
theorem posteriorBadMass_contraction_of_not_badGap
    (prior : FiniteLaw Hypothesis) (path : Trajectory)
    (sampleCount : ℕ) (deviation : ℝ)
    (sampleCountPositive : 0 < sampleCount)
    (deviationPositive : 0 < deviation)
    (deviationBelowGap : deviation < identificationGap)
    (truthPriorPositive : 0 < prior truthHypothesis)
    (notBadGap : path ∉ finiteSampleBadGap sampleCount deviation) :
    0 < (sampleCount : ℝ) * (identificationGap - deviation) ∧
      posteriorAfter prior path sampleCount false ≤
        priorBadOdds prior *
          Real.exp
            (-((sampleCount : ℝ) * (identificationGap - deviation))) := by
  have _deviationNonnegative : 0 ≤ deviation := deviationPositive.le
  constructor
  · exact mul_pos (by exact_mod_cast sampleCountPositive)
      (sub_pos.mpr deviationBelowGap)
  · have hCentered :
        (∑ index ∈ Finset.range sampleCount,
            centeredLogLikelihoodRatio (path index)) =
          (∑ index ∈ Finset.range sampleCount,
            logLikelihoodRatio (path index)) +
            (sampleCount : ℝ) * identificationGap := by
      simp [centeredLogLikelihoodRatio, Finset.sum_add_distrib]
    have hBadGapFails :
        (∑ index ∈ Finset.range sampleCount,
            centeredLogLikelihoodRatio (path index)) <
          (sampleCount : ℝ) * deviation := by
      exact lt_of_not_ge (by simpa [finiteSampleBadGap] using notBadGap)
    have hLogRatio :
        (∑ index ∈ Finset.range sampleCount,
            logLikelihoodRatio (path index)) ≤
          -((sampleCount : ℝ) * (identificationGap - deviation)) := by
      rw [hCentered] at hBadGapFails
      linarith
    calc
      posteriorAfter prior path sampleCount false ≤
          priorBadOdds (posteriorAfter prior path sampleCount) :=
        posteriorBadMass_le_badOdds _
          (posteriorAfter_truth_pos
            prior path truthPriorPositive sampleCount)
      _ = priorBadOdds prior *
            Real.exp
              (∑ index ∈ Finset.range sampleCount,
                logLikelihoodRatio (path index)) :=
        posteriorAfter_badOdds prior path truthPriorPositive sampleCount
      _ ≤ priorBadOdds prior *
            Real.exp
              (-((sampleCount : ℝ) * (identificationGap - deviation))) :=
        mul_le_mul_of_nonneg_left (Real.exp_le_exp.mpr hLogRatio)
          (div_nonneg (prior.nonneg false) truthPriorPositive.le)

/-- Trajectories on which the posterior bad mass exceeds its explicit
exponential envelope. -/
def posteriorBadMassFailure (prior : FiniteLaw Hypothesis)
    (sampleCount : ℕ) (deviation : ℝ) : Set Trajectory :=
  {path |
    priorBadOdds prior *
        Real.exp
          (-((sampleCount : ℝ) * (identificationGap - deviation))) <
      posteriorAfter prior path sampleCount false}

/-- The posterior-contraction failure probability is bounded by the selected
model's derived likelihood-gap tail probability. -/
theorem posteriorBadMass_failure_probability_le
    (prior : FiniteLaw Hypothesis) (sampleCount : ℕ) (deviation : ℝ)
    (sampleCountPositive : 0 < sampleCount)
    (deviationPositive : 0 < deviation)
    (deviationBelowGap : deviation < identificationGap)
    (truthPriorPositive : 0 < prior truthHypothesis) :
    trajectoryLaw.real
        (posteriorBadMassFailure prior sampleCount deviation) ≤
      Real.exp
        (-((sampleCount : ℝ) * deviation) ^ 2 /
          (2 * ∑ _index : Fin sampleCount, logLikelihoodRatioProxy)) := by
  calc
    trajectoryLaw.real
        (posteriorBadMassFailure prior sampleCount deviation) ≤
        trajectoryLaw.real (finiteSampleBadGap sampleCount deviation) := by
      refine measureReal_mono ?_ (measure_ne_top trajectoryLaw _)
      intro path hFailure
      by_contra hNotBad
      exact (not_le_of_gt hFailure)
        (posteriorBadMass_contraction_of_not_badGap
          prior path sampleCount deviation sampleCountPositive
          deviationPositive deviationBelowGap truthPriorPositive hNotBad).2
    _ ≤ Real.exp
        (-((sampleCount : ℝ) * deviation) ^ 2 /
          (2 * ∑ _index : Fin sampleCount, logLikelihoodRatioProxy)) :=
      finiteSampleBadGap_probability_le
        sampleCount deviation sampleCountPositive deviationPositive

/-! ## Nonvacuity and identification boundaries -/

/-- Two truth-matching observations move the fair prior to exact masses
`(1/10, 9/10)`; the maintained repeated update is therefore nonconstant. -/
theorem posteriorAfter_two_true_witness :
    posteriorAfter selectedPrior (fun _ => true) 2 false = 1 / 10 ∧
      posteriorAfter selectedPrior (fun _ => true) 2 true = 9 / 10 ∧
      posteriorAfter selectedPrior (fun _ => true) 2 ≠ selectedPrior := by
  constructor
  · norm_num [posteriorAfter, posteriorUpdate, selectedPrior,
      FEP.DecisionRisk.boolFairLaw, selectedLikelihood,
      FiniteKernel.posterior, FiniteKernel.predictive_mass, Fintype.sum_bool]
  constructor
  · norm_num [posteriorAfter, posteriorUpdate, selectedPrior,
      FEP.DecisionRisk.boolFairLaw, selectedLikelihood,
      FiniteKernel.posterior, FiniteKernel.predictive_mass, Fintype.sum_bool]
  · intro hEqual
    have hFalse := congrArg (fun belief : FiniteLaw Hypothesis => belief false) hEqual
    norm_num [posteriorAfter, posteriorUpdate, selectedPrior,
      FEP.DecisionRisk.boolFairLaw, selectedLikelihood,
      FiniteKernel.posterior, FiniteKernel.predictive_mass,
      Fintype.sum_bool] at hFalse

/-- A hypothesis excluded by the initial prior remains excluded after every
selected observation. -/
theorem posteriorAfter_zeroPrior (prior : FiniteLaw Hypothesis)
    (path : Trajectory) (hypothesis : Hypothesis)
    (priorZero : prior hypothesis = 0) :
    ∀ sampleCount, posteriorAfter prior path sampleCount hypothesis = 0
  | 0 => priorZero
  | sampleCount + 1 => by
      rw [posteriorAfter]
      exact FEP.LearningTheory.posterior_zero_of_prior_zero
        (posteriorAfter prior path sampleCount) selectedLikelihood
        (path sampleCount)
        (selectedPredictive_pos
          (posteriorAfter prior path sampleCount) (path sampleCount))
        hypothesis
        (posteriorAfter_zeroPrior
          prior path hypothesis priorZero sampleCount)

/-- Observation law with identical rows, making the two hypotheses
observationally nonidentifiable. -/
def nonidentifiableLikelihood : FiniteKernel Hypothesis Observation where
  mass _hypothesis _observation := 1 / 2
  nonneg _hypothesis _observation := by norm_num
  sum_one _hypothesis := by rw [Fintype.sum_bool]; norm_num

private theorem nonidentifiablePredictive_eq_half (prior : FiniteLaw Hypothesis)
    (observation : Observation) :
    nonidentifiableLikelihood.predictive prior observation = 1 / 2 := by
  rw [FiniteKernel.predictive_mass]
  simp only [nonidentifiableLikelihood]
  rw [← Finset.sum_mul, prior.sum_one]
  norm_num

theorem nonidentifiablePredictive_pos (prior : FiniteLaw Hypothesis)
    (observation : Observation) :
    0 < nonidentifiableLikelihood.predictive prior observation := by
  rw [nonidentifiablePredictive_eq_half]
  norm_num

/-- One observation from identical likelihood rows leaves every prior fixed. -/
noncomputable def nonidentifiablePosteriorUpdate
    (prior : FiniteLaw Hypothesis) (observation : Observation) :
    FiniteLaw Hypothesis :=
  nonidentifiableLikelihood.posterior prior observation
    (nonidentifiablePredictive_pos prior observation)

private theorem nonidentifiablePosteriorUpdate_eq_prior
    (prior : FiniteLaw Hypothesis) (observation : Observation) :
    nonidentifiablePosteriorUpdate prior observation = prior := by
  apply FiniteLaw.ext_mass
  funext hypothesis
  change
    prior hypothesis * nonidentifiableLikelihood hypothesis observation /
        nonidentifiableLikelihood.predictive prior observation =
      prior hypothesis
  rw [nonidentifiablePredictive_eq_half]
  simp [nonidentifiableLikelihood]

/-- Repeated observations from identical rows never identify either
hypothesis. -/
noncomputable def nonidentifiablePosteriorAfter
    (prior : FiniteLaw Hypothesis) (path : Trajectory) :
    ℕ → FiniteLaw Hypothesis
  | 0 => prior
  | sampleCount + 1 =>
      nonidentifiablePosteriorUpdate
        (nonidentifiablePosteriorAfter prior path sampleCount)
        (path sampleCount)

theorem nonidentifiablePosteriorAfter_eq_prior
    (prior : FiniteLaw Hypothesis) (path : Trajectory) :
    ∀ sampleCount,
      nonidentifiablePosteriorAfter prior path sampleCount = prior
  | 0 => rfl
  | sampleCount + 1 => by
      rw [nonidentifiablePosteriorAfter,
        nonidentifiablePosteriorAfter_eq_prior prior path sampleCount,
        nonidentifiablePosteriorUpdate_eq_prior]

/-! ## Separate almost-sure contraction from the finite-alphabet strong law -/

/-- Coordinate process supplied to the maintained finite-alphabet strong law. -/
def trajectoryObservation (index : ℕ) (path : Trajectory) : Observation :=
  path index

private theorem trajectoryAtomIndicators_integrable (atom : Observation) :
    Integrable
      (FEP.StatisticalConvergence.atomIndicator
        trajectoryObservation atom 0) trajectoryLaw := by
  have hMeasurable : Measurable
      (FEP.StatisticalConvergence.atomIndicator
        trajectoryObservation atom 0) := by
    change Measurable
      (fun path : Trajectory =>
        if path 0 = atom then (1 : ℝ) else 0)
    have hAtom : Measurable
        (fun observation : Observation =>
          if observation = atom then (1 : ℝ) else 0) :=
      Measurable.of_discrete
    exact hAtom.comp (measurable_pi_apply 0)
  refine Integrable.of_bound hMeasurable.aestronglyMeasurable 1
    (Filter.Eventually.of_forall fun path => ?_)
  change |if path 0 = atom then (1 : ℝ) else 0| ≤ 1
  split_ifs <;> norm_num

/-- Indicator processes inherit pairwise independence from the constructed
product coordinates. -/
private theorem trajectoryAtomIndicators_pairwiseIndep (atom : Observation) :
    Pairwise fun left right =>
      FEP.StatisticalConvergence.atomIndicator
          trajectoryObservation atom left ⟂ᵢ[trajectoryLaw]
        FEP.StatisticalConvergence.atomIndicator
          trajectoryObservation atom right := by
  have hIndicators :
      iIndepFun
        (fun index : ℕ =>
          (fun observation : Observation =>
            if observation = atom then (1 : ℝ) else 0) ∘
              fun path : Trajectory => path index)
        trajectoryLaw :=
    trajectoryCoordinates_iIndep.comp
      (fun _index : ℕ =>
        fun observation : Observation =>
          if observation = atom then (1 : ℝ) else 0)
      (fun _ => Measurable.of_discrete)
  intro left right hne
  change
    (fun path : Trajectory =>
      if path left = atom then (1 : ℝ) else 0) ⟂ᵢ[trajectoryLaw]
    (fun path : Trajectory =>
      if path right = atom then (1 : ℝ) else 0)
  exact hIndicators.indepFun hne

/-- Indicator processes are identically distributed because every product
coordinate has the same proved marginal law. -/
private theorem trajectoryAtomIndicators_identDistrib (atom : Observation)
    (index : ℕ) :
    IdentDistrib
      (FEP.StatisticalConvergence.atomIndicator
        trajectoryObservation atom index)
      (FEP.StatisticalConvergence.atomIndicator
        trajectoryObservation atom 0)
      trajectoryLaw trajectoryLaw := by
  have hCoordinates :=
    (trajectoryCoordinate_hasLaw index).identDistrib
      (trajectoryCoordinate_hasLaw 0)
  change IdentDistrib
    ((fun observation : Observation =>
      if observation = atom then (1 : ℝ) else 0) ∘
        fun path : Trajectory => path index)
    ((fun observation : Observation =>
      if observation = atom then (1 : ℝ) else 0) ∘
        fun path : Trajectory => path 0)
    trajectoryLaw trajectoryLaw
  exact hCoordinates.comp Measurable.of_discrete

/-- Expected indicator mass of one coordinate agrees with the authored finite
truth law. -/
private theorem trajectoryAtomIndicator_integral (atom : Observation) :
    trajectoryLaw[
        FEP.StatisticalConvergence.atomIndicator
          trajectoryObservation atom 0] =
      truthObservationLaw atom := by
  change
    (∫ path : Trajectory,
      (if path 0 = atom then (1 : ℝ) else 0) ∂trajectoryLaw) =
      truthObservationLaw atom
  calc
    (∫ path : Trajectory,
      (if path 0 = atom then (1 : ℝ) else 0) ∂trajectoryLaw) =
        ∫ observation,
          (if observation = atom then (1 : ℝ) else 0)
          ∂truthObservationMeasure := by
      exact
        (trajectoryCoordinate_hasLaw 0).integral_comp
          (f := fun observation : Observation =>
            if observation = atom then (1 : ℝ) else 0)
          AEStronglyMeasurable.of_discrete
    _ = truthObservationLaw atom := by
      rw [truthObservationMeasure,
        FEP.NativeBlanket.embeddedLaw_integral_eq_sum]
      cases atom <;> simp

private theorem populationLogLikelihoodRatio_eq :
    FEP.StatisticalConvergence.populationExpectation
        trajectoryLaw trajectoryObservation logLikelihoodRatio =
      -identificationGap := by
  rw [FEP.StatisticalConvergence.populationExpectation, Fintype.sum_bool,
    trajectoryAtomIndicator_integral,
    trajectoryAtomIndicator_integral,
    logLikelihoodRatio_false, logLikelihoodRatio_true]
  norm_num [truthObservationLaw, selectedLikelihood, truthHypothesis,
    identificationGap, FiniteKernel.row]
  ring

/-- The maintained finite-alphabet strong law gives almost-sure convergence of
the selected empirical log-likelihood ratio to its exact negative gap. -/
theorem empiricalLogLikelihoodRatio_strongLaw :
    ∀ᵐ path ∂trajectoryLaw,
      Tendsto
        (fun sampleCount =>
          FEP.StatisticalConvergence.empiricalExpectation
            trajectoryObservation logLikelihoodRatio sampleCount path)
        atTop (nhds (-identificationGap)) := by
  have hStrongLaw :=
    FEP.StatisticalConvergence.empiricalExpectation_strongLaw
      trajectoryLaw trajectoryObservation logLikelihoodRatio
      trajectoryAtomIndicators_integrable
      trajectoryAtomIndicators_pairwiseIndep
      trajectoryAtomIndicators_identDistrib
  rw [populationLogLikelihoodRatio_eq] at hStrongLaw
  exact hStrongLaw

/-- On every finite prefix, the maintained finite-alphabet empirical
expectation equals the ordinary average of selected log-likelihood ratios. -/
private theorem empiricalLogLikelihoodRatio_eq_average
    (sampleCount : ℕ) (path : Trajectory) :
    FEP.StatisticalConvergence.empiricalExpectation
        trajectoryObservation logLikelihoodRatio sampleCount path =
      (∑ index ∈ Finset.range sampleCount,
        logLikelihoodRatio (path index)) / sampleCount := by
  rw [FEP.StatisticalConvergence.empiricalExpectation]
  simp only [FEP.StatisticalConvergence.empiricalMass,
    FEP.StatisticalConvergence.atomIndicator, trajectoryObservation]
  calc
    (∑ atom : Observation,
        ((∑ index ∈ Finset.range sampleCount,
          if path index = atom then (1 : ℝ) else 0) / sampleCount) *
            logLikelihoodRatio atom) =
        (∑ atom : Observation,
          (∑ index ∈ Finset.range sampleCount,
            if path index = atom then (1 : ℝ) else 0) *
              logLikelihoodRatio atom) / sampleCount := by
      rw [Finset.sum_div]
      apply Finset.sum_congr rfl
      intro atom _
      ring
    _ = (∑ index ∈ Finset.range sampleCount,
          logLikelihoodRatio (path index)) / sampleCount := by
      congr 1
      simp_rw [Finset.sum_mul]
      rw [Finset.sum_comm]
      apply Finset.sum_congr rfl
      intro index hindex
      cases path index <;> simp

/-- Almost surely, every positive margin below the identification gap yields
eventual exponential contraction of the actual repeated posterior bad mass.
This theorem consumes the strong law separately from the finite-sample tail. -/
theorem posteriorBadMass_eventually_contracts
    (prior : FiniteLaw Hypothesis)
    (truthPriorPositive : 0 < prior truthHypothesis)
    (margin : ℝ) (marginPositive : 0 < margin)
    (marginBelowGap : margin < identificationGap) :
    ∀ᵐ path ∂trajectoryLaw,
      ∀ᶠ sampleCount in atTop,
        posteriorAfter prior path sampleCount false ≤
          priorBadOdds prior *
            Real.exp
              (-((sampleCount : ℝ) * (identificationGap - margin))) := by
  filter_upwards [empiricalLogLikelihoodRatio_strongLaw] with path hConvergence
  rcases Metric.tendsto_atTop.1 hConvergence margin marginPositive with
    ⟨threshold, hThreshold⟩
  filter_upwards [eventually_ge_atTop threshold, eventually_gt_atTop 0]
    with sampleCount hAtLeast hPositive
  have hNear := hThreshold sampleCount hAtLeast
  rw [Real.dist_eq] at hNear
  have hMean :
      FEP.StatisticalConvergence.empiricalExpectation
          trajectoryObservation logLikelihoodRatio sampleCount path <
        -identificationGap + margin := by
    have hUpper := (abs_lt.mp hNear).2
    linarith
  rw [empiricalLogLikelihoodRatio_eq_average] at hMean
  have hCountPositive : (0 : ℝ) < sampleCount := by exact_mod_cast hPositive
  have hLogRatio :
      (∑ index ∈ Finset.range sampleCount,
          logLikelihoodRatio (path index)) <
        -((sampleCount : ℝ) * (identificationGap - margin)) := by
    have hScaled := (div_lt_iff₀ hCountPositive).mp hMean
    nlinarith
  have hCentered :
      (∑ index ∈ Finset.range sampleCount,
          centeredLogLikelihoodRatio (path index)) =
        (∑ index ∈ Finset.range sampleCount,
          logLikelihoodRatio (path index)) +
          (sampleCount : ℝ) * identificationGap := by
    simp [centeredLogLikelihoodRatio, Finset.sum_add_distrib]
  have hNotBad : path ∉ finiteSampleBadGap sampleCount margin := by
    intro hBad
    have hBadInequality :
        (sampleCount : ℝ) * margin ≤
          ∑ index ∈ Finset.range sampleCount,
            centeredLogLikelihoodRatio (path index) := by
      simpa [finiteSampleBadGap] using hBad
    rw [hCentered] at hBadInequality
    linarith
  exact (posteriorBadMass_contraction_of_not_badGap
    prior path sampleCount margin hPositive marginPositive marginBelowGap
    truthPriorPositive hNotBad).2

end

end FEP.FinitePosteriorLearning
