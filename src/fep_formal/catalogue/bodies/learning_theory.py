"""Lean bodies for learning, concentration, and model evidence."""

from __future__ import annotations

BODIES: dict[str, str] = {
    "fep-114": """import FepSketches.learning_theory

/-! # Sub-Gaussian Empirical-Mean Tail Bound -/
namespace FEP114

open MeasureTheory ProbabilityTheory
open scoped BigOperators ENNReal MeasureTheory NNReal ProbabilityTheory

/-- Independent sub-Gaussian observations obey the finite-sample upper-tail
bound for the empirical-mean event. -/
theorem fep114_subGaussian_empiricalMean_tail
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
          (2 * ∑ index, proxyVariance index)) :=
  FEP.LearningTheory.subGaussian_empiricalMean_tail
    μ observables independent proxyVariance subGaussian deviationNonnegative

/-- The theorem fixes the finite sample through `Fin sampleCount`; no
asymptotic limit or IID premise is inferred beyond the stated independence. -/
theorem fep114_empiricalMean_definition
    {Ω : Type*} {sampleCount : ℕ}
    (observables : Fin sampleCount → Ω → ℝ) (outcome : Ω) :
    FEP.LearningTheory.empiricalMean observables outcome =
      (∑ index, observables index outcome) / sampleCount :=
  rfl

end FEP114
""",
    "fep-115": """import FepSketches.learning_theory

/-! # Simultaneous Finite-Alphabet Frequency Bound -/
namespace FEP115

open MeasureTheory ProbabilityTheory
open scoped ENNReal MeasureTheory ProbabilityTheory

/-- A finite union bound lifts per-symbol empirical-frequency guarantees to a
simultaneous alphabet-wide guarantee. -/
theorem fep115_simultaneous_frequency_bound
    {Ω Alphabet : Type*} [MeasurableSpace Ω]
    [Fintype Alphabet] [DecidableEq Alphabet]
    (μ : Measure Ω) [IsProbabilityMeasure μ]
    {sampleCount : ℕ} [NeZero sampleCount]
    (sample : Ω → Fin sampleCount → Alphabet)
    (target : Alphabet → ℝ) (deviation perSymbolFailure : ℝ)
    (perSymbolBound : ∀ symbol,
      μ.real
          (FEP.LearningTheory.frequencyDeviationEvent
            sample target deviation symbol) ≤ perSymbolFailure) :
    μ.real (⋃ symbol,
        FEP.LearningTheory.frequencyDeviationEvent
          sample target deviation symbol) ≤
      Fintype.card Alphabet * perSymbolFailure :=
  FEP.LearningTheory.simultaneous_frequency_bound
    μ sample target deviation perSymbolFailure perSymbolBound

/-- The event is the actual two-sided deviation of a normalized finite count,
not an abstract placeholder event. -/
theorem fep115_frequencyDeviationEvent_membership
    {Ω Alphabet : Type*} [Fintype Alphabet] [DecidableEq Alphabet]
    {sampleCount : ℕ} [NeZero sampleCount]
    (sample : Ω → Fin sampleCount → Alphabet)
    (target : Alphabet → ℝ) (deviation : ℝ)
    (symbol : Alphabet) (outcome : Ω) :
    outcome ∈ FEP.LearningTheory.frequencyDeviationEvent
        sample target deviation symbol ↔
      deviation ≤
        |FEP.LearningTheory.empiricalFrequency
            (sample outcome) symbol - target symbol| :=
  Iff.rfl

end FEP115
""",
    "fep-116": """import FepSketches.learning_theory

/-! # Finite-Hypothesis PAC-Bayes Loss-Gap Bound -/
namespace FEP116

open FEP MeasureTheory ProbabilityTheory
open scoped ENNReal MeasureTheory ProbabilityTheory

/-- A finite posterior's population loss is controlled by its empirical loss,
finite KL complexity, and a certified log-MGF budget. The Gibbs potential is
explicitly the inverse-temperature-scaled loss gap. -/
theorem fep116_finitePACBayes_with_confidence
    {Hypothesis : Type*} [Fintype Hypothesis]
    (prior posterior : FiniteLaw Hypothesis)
    (certificate : FEP.VariationalDuality.GibbsCertificate Hypothesis)
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
    FEP.VariationalDuality.expectation posterior populationLoss ≤
      FEP.VariationalDuality.expectation posterior empiricalLoss +
        (FEP.FiniteInformation.finiteKL posterior prior +
          Real.log confidence⁻¹) / inverseTemperature :=
  (FEP.LearningTheory.finitePACBayes_changeOfMeasure_with_confidence
    prior posterior certificate referenceIsPrior empiricalLoss populationLoss
    inverseTemperature inverseTemperaturePositive potentialIsLossGap confidence
    confidencePositive confidenceBelowOne logMGFBound).1

/-- A full-support finite prior has no zero-mass atom, matching the support
boundary required by finite KL and Gibbs log-density terms. -/
theorem fep116_prior_support_nonzero
    {Hypothesis : Type*} [Fintype Hypothesis]
    (prior : FiniteLaw Hypothesis)
    (priorPositive : ∀ hypothesis, 0 < prior hypothesis)
    (hypothesis : Hypothesis) :
    prior hypothesis ≠ 0 :=
  ne_of_gt (priorPositive hypothesis)

end FEP116
""",
    "fep-117": """import FepSketches.learning_theory

/-! # Posterior-Odds Multiplicative Recursion -/
namespace FEP117

open FEP

/-- At positive evidence, posterior odds equal prior odds times the likelihood
ratio, provided the reference hypothesis has positive prior and likelihood. -/
theorem fep117_posteriorOdds_recursion
    {Hypothesis Evidence : Type*} [Fintype Hypothesis] [Fintype Evidence]
    (prior : FiniteLaw Hypothesis)
    (likelihood : FiniteKernel Hypothesis Evidence)
    (evidence : Evidence)
    (evidencePositive : 0 < likelihood.predictive prior evidence)
    (favored reference : Hypothesis)
    (referencePriorPositive : 0 < prior reference)
    (referenceLikelihoodPositive : 0 < likelihood reference evidence) :
    FEP.LearningTheory.posteriorOdds
        prior likelihood evidence evidencePositive favored reference =
      (prior favored / prior reference) *
        (likelihood favored evidence / likelihood reference evidence) :=
  FEP.LearningTheory.posteriorOdds_recursion
    prior likelihood evidence evidencePositive favored reference
    referencePriorPositive referenceLikelihoodPositive

/-- A zero-prior hypothesis cannot be recovered by conditioning on positive
evidence. -/
theorem fep117_zero_prior_boundary
    {Hypothesis Evidence : Type*} [Fintype Hypothesis] [Fintype Evidence]
    (prior : FiniteLaw Hypothesis)
    (likelihood : FiniteKernel Hypothesis Evidence)
    (evidence : Evidence)
    (evidencePositive : 0 < likelihood.predictive prior evidence)
    (hypothesis : Hypothesis) (priorZero : prior hypothesis = 0) :
    likelihood.posterior prior evidence evidencePositive hypothesis = 0 :=
  FEP.LearningTheory.posterior_zero_of_prior_zero
    prior likelihood evidence evidencePositive hypothesis priorZero

end FEP117
""",
    "fep-118": """import FepSketches.learning_theory

/-! # Exponential Posterior Concentration from a Likelihood Gap -/
namespace FEP118

/-- A nonnegative per-observation likelihood gap gives an explicit exponential
finite-sample bound on inferior posterior mass. -/
theorem fep118_posteriorGap_concentration
    (priorGood priorBad likelihoodGood likelihoodBad likelihoodGap : ℝ)
    (sampleCount : ℕ)
    (priorGoodPositive : 0 < priorGood)
    (priorBadNonnegative : 0 ≤ priorBad)
    (likelihoodGoodPositive : 0 < likelihoodGood)
    (likelihoodBadNonnegative : 0 ≤ likelihoodBad)
    (likelihoodGapNonnegative : 0 ≤ likelihoodGap)
    (gapBound :
      likelihoodBad ≤ Real.exp (-likelihoodGap) * likelihoodGood) :
    FEP.LearningTheory.twoHypothesisPosteriorBad
        priorGood priorBad likelihoodGood likelihoodBad sampleCount ≤
      (priorBad / priorGood) *
        Real.exp (-((sampleCount : ℝ) * likelihoodGap)) :=
  FEP.LearningTheory.posteriorGap_concentration
    priorGood priorBad likelihoodGood likelihoodBad likelihoodGap sampleCount
    priorGoodPositive priorBadNonnegative likelihoodGoodPositive
    likelihoodBadNonnegative likelihoodGapNonnegative gapBound

/-- Equal priors and a `3:1` likelihood ratio give exact nonzero posterior bad
mass `1/10` after two observations. -/
theorem fep118_twoHypothesis_witness :
    FEP.LearningTheory.twoHypothesisPosteriorBad
      (1 / 2) (1 / 2) (3 / 4) (1 / 4) 2 = 1 / 10 :=
  FEP.LearningTheory.twoHypothesis_posterior_witness

end FEP118
""",
    "fep-119": """import FepSketches.learning_theory

/-! # Bayesian-Mixture Log-Loss Regret Bound -/
namespace FEP119

open FEP

variable {Hypothesis : Type*} [Fintype Hypothesis]

/-- Mixture evidence dominates every nonnegative component contribution. -/
theorem fep119_mixtureEvidence_lower_bound
    (prior : FiniteLaw Hypothesis) (likelihood : Hypothesis → ℝ)
    (likelihoodNonnegative : ∀ hypothesis, 0 ≤ likelihood hypothesis)
    (selected : Hypothesis) :
    prior selected * likelihood selected ≤
      FEP.LearningTheory.mixtureEvidence prior likelihood :=
  FEP.LearningTheory.mixtureEvidence_lower_bound
    prior likelihood likelihoodNonnegative selected

/-- The selected model pays at most its own log loss plus the exact finite
prior penalty. -/
theorem fep119_mixtureLogLoss_regret
    (prior : FiniteLaw Hypothesis) (likelihood : Hypothesis → ℝ)
    (likelihoodNonnegative : ∀ hypothesis, 0 ≤ likelihood hypothesis)
    (selected : Hypothesis)
    (priorPositive : 0 < prior selected)
    (likelihoodPositive : 0 < likelihood selected) :
    -Real.log (FEP.LearningTheory.mixtureEvidence prior likelihood) ≤
      -Real.log (likelihood selected) - Real.log (prior selected) :=
  FEP.LearningTheory.mixtureLogLoss_regret
    prior likelihood likelihoodNonnegative selected
    priorPositive likelihoodPositive

end FEP119
""",
    "fep-120": """import FepSketches.learning_theory

/-! # Bayes-Factor Multiplicativity and Model-Evidence Update -/
namespace FEP120

/-- Explicitly factorized evidence terms multiply, and sequential
posterior-odds updates agree with one update using product evidence. -/
theorem fep120_bayesFactor_multiplicative_update
    (priorOdds firstFavored firstReference secondFavored secondReference : ℝ)
    (firstReferenceNonzero : firstReference ≠ 0)
    (secondReferenceNonzero : secondReference ≠ 0) :
    FEP.LearningTheory.bayesFactor
        (firstFavored * secondFavored) (firstReference * secondReference) =
        FEP.LearningTheory.bayesFactor firstFavored firstReference *
          FEP.LearningTheory.bayesFactor secondFavored secondReference ∧
      FEP.LearningTheory.updatedModelOdds priorOdds
          (firstFavored * secondFavored) (firstReference * secondReference) =
        FEP.LearningTheory.updatedModelOdds
          (FEP.LearningTheory.updatedModelOdds
            priorOdds firstFavored firstReference)
          secondFavored secondReference :=
  FEP.LearningTheory.bayesFactor_multiplicative
    priorOdds firstFavored firstReference secondFavored secondReference
    firstReferenceNonzero secondReferenceNonzero

/-- A concrete two-model evidence ratio updates unit prior odds to three. -/
theorem fep120_twoHypothesis_evidence_witness :
    FEP.LearningTheory.bayesFactor (3 / 4) (1 / 4) = 3 ∧
      FEP.LearningTheory.updatedModelOdds 1 (3 / 4) (1 / 4) = 3 :=
  FEP.LearningTheory.bayesFactor_twoHypothesis_witness

/-- At zero reference evidence, real division returns zero rather than an
extended infinite Bayes factor; supported comparisons require nonzero
reference evidence. -/
theorem fep120_zero_evidence_boundary (favored : ℝ) :
    FEP.LearningTheory.bayesFactor favored 0 = 0 :=
  FEP.LearningTheory.bayesFactor_zero_denominator_boundary favored

end FEP120
""",
}
