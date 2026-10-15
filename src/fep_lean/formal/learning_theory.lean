module
public import FepSketches.variational_duality
public import Mathlib.Probability.Moments.SubGaussian

@[expose] public section

/-!
# Finite-sample learning, posterior concentration, and model evidence

The probability statements below retain their sample-size, independence,
confidence, prior-support, and likelihood-gap premises. The finite evidence
identities use the shared `FiniteLaw` substrate and real-valued totalization;
zero-denominator boundaries are therefore stated explicitly.
-/

namespace FEP.LearningTheory

open FEP Finset MeasureTheory ProbabilityTheory
open FEP.FiniteInformation FEP.VariationalDuality
open scoped BigOperators ENNReal MeasureTheory NNReal ProbabilityTheory

/-! ## Finite-sample concentration -/

/-- Arithmetic empirical mean of a fixed finite sample of real observables. -/
noncomputable def empiricalMean
    {Ω : Type*} {sampleCount : ℕ}
    (observables : Fin sampleCount → Ω → ℝ) (outcome : Ω) : ℝ :=
  (∑ index, observables index outcome) / sampleCount

/-- Hoeffding's sub-Gaussian bound in the multiplication form of the
empirical-mean event. The observables are centered by the
`HasSubgaussianMGF` premise, and independence is explicit. -/
theorem subGaussian_empiricalMean_tail
    {Ω : Type*} [MeasurableSpace Ω]
    (μ : Measure Ω) {sampleCount : ℕ}
    (observables : Fin sampleCount → Ω → ℝ)
    (independent : iIndepFun observables μ)
    (proxyVariance : Fin sampleCount → ℝ≥0)
    (subGaussian : ∀ index,
      HasSubgaussianMGF (observables index) (proxyVariance index) μ)
    {deviation : ℝ} (deviationNonnegative : 0 ≤ deviation) :
    μ.real {outcome |
        (sampleCount : ℝ) * deviation ≤
          ∑ index, observables index outcome} ≤
      Real.exp
        (-((sampleCount : ℝ) * deviation) ^ 2 /
          (2 * ∑ index, proxyVariance index)) := by
  simpa using
    (HasSubgaussianMGF.measure_sum_ge_le_of_iIndepFun independent
      (s := Finset.univ)
      (c := proxyVariance)
      (fun index _ => subGaussian index)
      (ε := (sampleCount : ℝ) * deviation)
      (mul_nonneg (Nat.cast_nonneg sampleCount) deviationNonnegative))

/-- Frequency of a symbol in a nonempty finite sample. -/
noncomputable def empiricalFrequency
    {Alphabet : Type*} [Fintype Alphabet] [DecidableEq Alphabet]
    {sampleCount : ℕ} [NeZero sampleCount]
    (sample : Fin sampleCount → Alphabet) (symbol : Alphabet) : ℝ :=
  ((Finset.univ.filter fun index => sample index = symbol).card : ℝ) /
    sampleCount

/-- Two-sided frequency-deviation event for one alphabet symbol. -/
def frequencyDeviationEvent
    {Ω Alphabet : Type*} [Fintype Alphabet] [DecidableEq Alphabet]
    {sampleCount : ℕ} [NeZero sampleCount]
    (sample : Ω → Fin sampleCount → Alphabet)
    (target : Alphabet → ℝ) (deviation : ℝ) (symbol : Alphabet) : Set Ω :=
  {outcome |
    deviation ≤
      |empiricalFrequency (sample outcome) symbol - target symbol|}

/-- A simultaneous finite-alphabet frequency guarantee obtained by a genuine
finite union bound from per-symbol finite-sample bounds. -/
theorem simultaneous_frequency_bound
    {Ω Alphabet : Type*} [MeasurableSpace Ω]
    [Fintype Alphabet] [DecidableEq Alphabet]
    (μ : Measure Ω) [IsProbabilityMeasure μ]
    {sampleCount : ℕ} [NeZero sampleCount]
    (sample : Ω → Fin sampleCount → Alphabet)
    (target : Alphabet → ℝ) (deviation perSymbolFailure : ℝ)
    (perSymbolBound : ∀ symbol,
      μ.real (frequencyDeviationEvent sample target deviation symbol) ≤
        perSymbolFailure) :
    μ.real (⋃ symbol,
        frequencyDeviationEvent sample target deviation symbol) ≤
      Fintype.card Alphabet * perSymbolFailure := by
  calc
    μ.real (⋃ symbol,
        frequencyDeviationEvent sample target deviation symbol) ≤
        ∑ symbol,
          μ.real (frequencyDeviationEvent sample target deviation symbol) :=
      measureReal_iUnion_fintype_le _
    _ ≤ ∑ _symbol : Alphabet, perSymbolFailure :=
      Finset.sum_le_sum fun symbol _ => perSymbolBound symbol
    _ = Fintype.card Alphabet * perSymbolFailure := by simp

/-! ## Finite PAC--Bayes loss-gap certificate -/

/-- A finite PAC--Bayes-style loss-gap bound in which the posterior, loss
functions, Gibbs potential, inverse temperature, and log-MGF budget are one
connected statement. The theorem is deterministic conditional on
`logMGFBound`; deriving that premise with high probability over sampled data is
a separate probabilistic step. Full prior support is carried by the referenced
`GibbsCertificate`. -/
theorem finitePACBayes_changeOfMeasure_with_confidence
    {Hypothesis : Type*} [Fintype Hypothesis]
    (prior posterior : FiniteLaw Hypothesis)
    (certificate : GibbsCertificate Hypothesis)
    (referenceIsPrior : certificate.reference = prior)
    (empiricalLoss populationLoss : Hypothesis → ℝ)
    (inverseTemperature : ℝ)
    (inverseTemperaturePositive : 0 < inverseTemperature)
    (potentialIsLossGap : ∀ hypothesis,
      certificate.potential hypothesis = inverseTemperature *
        (populationLoss hypothesis - empiricalLoss hypothesis))
    (confidence : ℝ)
    (confidencePositive : 0 < confidence)
    (confidenceBelowOne : confidence < 1)
    (logMGFBound : certificate.logPartition ≤ Real.log confidence⁻¹) :
    VariationalDuality.expectation posterior populationLoss ≤
        VariationalDuality.expectation posterior empiricalLoss +
          (FiniteInformation.finiteKL posterior prior + Real.log confidence⁻¹) /
            inverseTemperature ∧
        confidence ∈ Set.Ioo 0 1 := by
  have potentialExpectation :
      VariationalDuality.expectation posterior certificate.potential =
        inverseTemperature *
          (VariationalDuality.expectation posterior populationLoss -
            VariationalDuality.expectation posterior empiricalLoss) := by
    simp only [VariationalDuality.expectation]
    calc
      (∑ hypothesis, posterior hypothesis * certificate.potential hypothesis) =
          ∑ hypothesis,
            inverseTemperature *
              (posterior hypothesis * populationLoss hypothesis -
                posterior hypothesis * empiricalLoss hypothesis) := by
        apply Finset.sum_congr rfl
        intro hypothesis _
        rw [potentialIsLossGap hypothesis]
        ring
      _ = inverseTemperature *
          ∑ hypothesis,
            (posterior hypothesis * populationLoss hypothesis -
              posterior hypothesis * empiricalLoss hypothesis) := by
        rw [Finset.mul_sum]
      _ = inverseTemperature *
          ((∑ hypothesis, posterior hypothesis * populationLoss hypothesis) -
            ∑ hypothesis, posterior hypothesis * empiricalLoss hypothesis) := by
        rw [Finset.sum_sub_distrib]
  have dualBound :=
    VariationalDuality.dvObjective_le_logPartition certificate posterior
  rw [VariationalDuality.dvObjective, referenceIsPrior, potentialExpectation] at dualBound
  have scaledGap :
      inverseTemperature *
          (VariationalDuality.expectation posterior populationLoss -
            VariationalDuality.expectation posterior empiricalLoss) ≤
        FiniteInformation.finiteKL posterior prior + Real.log confidence⁻¹ := by
    linarith
  have gapBound :
      VariationalDuality.expectation posterior populationLoss -
          VariationalDuality.expectation posterior empiricalLoss ≤
        (FiniteInformation.finiteKL posterior prior + Real.log confidence⁻¹) /
          inverseTemperature :=
    (le_div_iff₀ inverseTemperaturePositive).2 (by
      simpa [mul_comm] using scaledGap)
  constructor
  · linarith
  · exact ⟨confidencePositive, confidenceBelowOne⟩

/-! ## Posterior odds and support boundaries -/

/-- Posterior odds between two finite hypotheses at positive evidence. -/
noncomputable def posteriorOdds
    {Hypothesis Evidence : Type*} [Fintype Hypothesis] [Fintype Evidence]
    (prior : FiniteLaw Hypothesis)
    (likelihood : FiniteKernel Hypothesis Evidence)
    (evidence : Evidence) (evidencePositive : 0 < likelihood.predictive prior evidence)
    (favored reference : Hypothesis) : ℝ :=
  likelihood.posterior prior evidence evidencePositive favored /
    likelihood.posterior prior evidence evidencePositive reference

/-- Bayes' rule updates posterior odds by multiplying prior odds and the
likelihood ratio. Positive reference prior and likelihood masses are the exact
division premises. -/
theorem posteriorOdds_recursion
    {Hypothesis Evidence : Type*} [Fintype Hypothesis] [Fintype Evidence]
    (prior : FiniteLaw Hypothesis)
    (likelihood : FiniteKernel Hypothesis Evidence)
    (evidence : Evidence) (evidencePositive : 0 < likelihood.predictive prior evidence)
    (favored reference : Hypothesis)
    (referencePriorPositive : 0 < prior reference)
    (referenceLikelihoodPositive : 0 < likelihood reference evidence) :
    posteriorOdds prior likelihood evidence evidencePositive favored reference =
      (prior favored / prior reference) *
        (likelihood favored evidence / likelihood reference evidence) := by
  unfold posteriorOdds FiniteKernel.posterior
  field_simp [ne_of_gt evidencePositive, ne_of_gt referencePriorPositive,
    ne_of_gt referenceLikelihoodPositive]

/-- A zero-prior hypothesis remains absent after conditioning on positive
evidence. This pins the prior-support boundary of the odds recursion. -/
theorem posterior_zero_of_prior_zero
    {Hypothesis Evidence : Type*} [Fintype Hypothesis] [Fintype Evidence]
    (prior : FiniteLaw Hypothesis)
    (likelihood : FiniteKernel Hypothesis Evidence)
    (evidence : Evidence) (evidencePositive : 0 < likelihood.predictive prior evidence)
    (hypothesis : Hypothesis) (priorZero : prior hypothesis = 0) :
    likelihood.posterior prior evidence evidencePositive hypothesis = 0 := by
  simp [FiniteKernel.posterior, priorZero]

/-! ## Likelihood-gap concentration for two hypotheses -/

/-- Posterior mass assigned to the inferior member of a two-hypothesis model
after `sampleCount` repeated likelihood factors. -/
noncomputable def twoHypothesisPosteriorBad
    (priorGood priorBad likelihoodGood likelihoodBad : ℝ)
    (sampleCount : ℕ) : ℝ :=
  (priorBad * likelihoodBad ^ sampleCount) /
    (priorGood * likelihoodGood ^ sampleCount +
      priorBad * likelihoodBad ^ sampleCount)

/-- A per-sample likelihood gap yields an exponential finite-sample upper
bound on the inferior posterior mass. -/
theorem posteriorGap_concentration
    (priorGood priorBad likelihoodGood likelihoodBad likelihoodGap : ℝ)
    (sampleCount : ℕ)
    (priorGoodPositive : 0 < priorGood)
    (priorBadNonnegative : 0 ≤ priorBad)
    (likelihoodGoodPositive : 0 < likelihoodGood)
    (likelihoodBadNonnegative : 0 ≤ likelihoodBad)
    (likelihoodGapNonnegative : 0 ≤ likelihoodGap)
    (gapBound :
      likelihoodBad ≤ Real.exp (-likelihoodGap) * likelihoodGood) :
    twoHypothesisPosteriorBad priorGood priorBad likelihoodGood likelihoodBad
        sampleCount ≤
      (priorBad / priorGood) *
        Real.exp (-((sampleCount : ℝ) * likelihoodGap)) := by
  have goodWeightPositive :
      0 < priorGood * likelihoodGood ^ sampleCount :=
    mul_pos priorGoodPositive (pow_pos likelihoodGoodPositive sampleCount)
  have badWeightNonnegative :
      0 ≤ priorBad * likelihoodBad ^ sampleCount :=
    mul_nonneg priorBadNonnegative
      (pow_nonneg likelihoodBadNonnegative sampleCount)
  have fractionBound :
      (priorBad * likelihoodBad ^ sampleCount) /
          (priorGood * likelihoodGood ^ sampleCount +
            priorBad * likelihoodBad ^ sampleCount) ≤
        (priorBad * likelihoodBad ^ sampleCount) /
          (priorGood * likelihoodGood ^ sampleCount) := by
    apply (div_le_div_iff₀
      (add_pos_of_pos_of_nonneg goodWeightPositive badWeightNonnegative)
      goodWeightPositive).2
    nlinarith [mul_self_nonneg
      (priorBad * likelihoodBad ^ sampleCount)]
  have oddsIdentity :
      (priorBad * likelihoodBad ^ sampleCount) /
          (priorGood * likelihoodGood ^ sampleCount) =
        (priorBad / priorGood) *
          (likelihoodBad / likelihoodGood) ^ sampleCount := by
    rw [div_pow]
    field_simp [ne_of_gt priorGoodPositive, ne_of_gt likelihoodGoodPositive]
  have likelihoodRatioNonnegative :
      0 ≤ likelihoodBad / likelihoodGood :=
    div_nonneg likelihoodBadNonnegative likelihoodGoodPositive.le
  have likelihoodRatioBoundRaw :
      likelihoodBad / likelihoodGood ≤ Real.exp (-likelihoodGap) :=
    (div_le_iff₀ likelihoodGoodPositive).2 gapBound
  have exponentialAtMostOne : Real.exp (-likelihoodGap) ≤ 1 := by
    rw [Real.exp_le_one_iff]
    linarith
  have likelihoodRatioCertified :
      likelihoodBad / likelihoodGood ≤ min (Real.exp (-likelihoodGap)) 1 :=
    le_min likelihoodRatioBoundRaw
      (likelihoodRatioBoundRaw.trans exponentialAtMostOne)
  have likelihoodRatioBound :
      likelihoodBad / likelihoodGood ≤ Real.exp (-likelihoodGap) :=
    likelihoodRatioCertified.trans (min_le_left _ _)
  have powerBound :
      (likelihoodBad / likelihoodGood) ^ sampleCount ≤
        Real.exp (-likelihoodGap) ^ sampleCount :=
    pow_le_pow_left₀ likelihoodRatioNonnegative likelihoodRatioBound sampleCount
  have exponentialIdentity :
      Real.exp (-likelihoodGap) ^ sampleCount =
        Real.exp (-((sampleCount : ℝ) * likelihoodGap)) := by
    rw [← Real.exp_nat_mul]
    congr 1
    ring
  calc
    twoHypothesisPosteriorBad priorGood priorBad likelihoodGood likelihoodBad
        sampleCount ≤
        (priorBad * likelihoodBad ^ sampleCount) /
          (priorGood * likelihoodGood ^ sampleCount) := fractionBound
    _ = (priorBad / priorGood) *
          (likelihoodBad / likelihoodGood) ^ sampleCount := oddsIdentity
    _ ≤ (priorBad / priorGood) *
          Real.exp (-likelihoodGap) ^ sampleCount :=
      mul_le_mul_of_nonneg_left powerBound
        (div_nonneg priorBadNonnegative priorGoodPositive.le)
    _ = (priorBad / priorGood) *
          Real.exp (-((sampleCount : ℝ) * likelihoodGap)) := by
      rw [exponentialIdentity]

/-- Closed two-hypothesis witness: equal prior mass, likelihoods `3/4` and
`1/4`, and two observations leave posterior bad mass exactly `1/10`. -/
theorem twoHypothesis_posterior_witness :
    twoHypothesisPosteriorBad (1 / 2) (1 / 2) (3 / 4) (1 / 4) 2 = 1 / 10 := by
  norm_num [twoHypothesisPosteriorBad]

/-! ## Bayesian mixtures and evidence factors -/

/-- Symmetric prior used to make the finite two-hypothesis carrier explicit. -/
noncomputable def balancedBoolPrior : FiniteLaw Bool :=
  FiniteLaw.uniform

/-- Evidence assigned by a finite Bayesian mixture. -/
noncomputable def mixtureEvidence
    {Hypothesis : Type*} [Fintype Hypothesis]
    (prior : FiniteLaw Hypothesis) (likelihood : Hypothesis → ℝ) : ℝ :=
  ∑ hypothesis, prior hypothesis * likelihood hypothesis

/-- Mixture evidence dominates the contribution of every component. -/
theorem mixtureEvidence_lower_bound
    {Hypothesis : Type*} [Fintype Hypothesis]
    (prior : FiniteLaw Hypothesis) (likelihood : Hypothesis → ℝ)
    (likelihoodNonnegative : ∀ hypothesis, 0 ≤ likelihood hypothesis)
    (selected : Hypothesis) :
    prior selected * likelihood selected ≤ mixtureEvidence prior likelihood := by
  classical
  simpa [mixtureEvidence] using
    (Finset.single_le_sum
      (fun hypothesis _ =>
        mul_nonneg (prior.nonneg hypothesis) (likelihoodNonnegative hypothesis))
      (Finset.mem_univ selected))

/-- The Bayesian-mixture log loss is at most a component log loss plus the
finite regret penalty `-log prior(selected)`. -/
theorem mixtureLogLoss_regret
    {Hypothesis : Type*} [Fintype Hypothesis]
    (prior : FiniteLaw Hypothesis) (likelihood : Hypothesis → ℝ)
    (likelihoodNonnegative : ∀ hypothesis, 0 ≤ likelihood hypothesis)
    (selected : Hypothesis)
    (priorPositive : 0 < prior selected)
    (likelihoodPositive : 0 < likelihood selected) :
    -Real.log (mixtureEvidence prior likelihood) ≤
      -Real.log (likelihood selected) - Real.log (prior selected) := by
  have lowerBound :=
    mixtureEvidence_lower_bound prior likelihood likelihoodNonnegative selected
  have componentPositive : 0 < prior selected * likelihood selected :=
    mul_pos priorPositive likelihoodPositive
  have logBound := Real.log_le_log componentPositive lowerBound
  rw [Real.log_mul (ne_of_gt priorPositive) (ne_of_gt likelihoodPositive)] at logBound
  linarith

/-- Likelihood ratio used as a finite Bayes factor. -/
noncomputable def bayesFactor (favored reference : ℝ) : ℝ :=
  favored / reference

/-- Posterior model odds after one evidence update. -/
noncomputable def updatedModelOdds
    (priorOdds favoredEvidence referenceEvidence : ℝ) : ℝ :=
  priorOdds * bayesFactor favoredEvidence referenceEvidence

/-- Explicitly factorized evidence terms multiply, and sequential model-odds
updates agree with a single update by the product evidence. A probabilistic
independence theorem is not inferred from this algebraic factorization. -/
theorem bayesFactor_multiplicative
    (priorOdds firstFavored firstReference secondFavored secondReference : ℝ)
    (firstReferenceNonzero : firstReference ≠ 0)
    (secondReferenceNonzero : secondReference ≠ 0) :
    bayesFactor (firstFavored * secondFavored)
        (firstReference * secondReference) =
        bayesFactor firstFavored firstReference *
          bayesFactor secondFavored secondReference ∧
      updatedModelOdds priorOdds (firstFavored * secondFavored)
          (firstReference * secondReference) =
        updatedModelOdds
          (updatedModelOdds priorOdds firstFavored firstReference)
          secondFavored secondReference := by
  constructor
  · unfold bayesFactor
    field_simp [firstReferenceNonzero, secondReferenceNonzero]
  · unfold updatedModelOdds bayesFactor
    field_simp [firstReferenceNonzero, secondReferenceNonzero]

/-- Closed two-model witness: evidence `3/4` versus `1/4` multiplies unit prior
odds to posterior odds three. -/
theorem bayesFactor_twoHypothesis_witness :
    bayesFactor (3 / 4) (1 / 4) = 3 ∧
      updatedModelOdds 1 (3 / 4) (1 / 4) = 3 := by
  norm_num [bayesFactor, updatedModelOdds]

/-- Real division is totalized at zero: a zero reference evidence produces
zero here, not an infinite Bayes factor. Supported model comparison must use a
nonzero denominator. -/
theorem bayesFactor_zero_denominator_boundary (favored : ℝ) :
    bayesFactor favored 0 = 0 := by
  simp [bayesFactor]

end FEP.LearningTheory
