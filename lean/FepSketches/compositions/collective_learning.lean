module
public import FepSketches.families.collective_inference
public import FepSketches.families.core_active_inference
public import FepSketches.families.core_bayesian_mechanics
public import FepSketches.families.core_free_energy
public import FepSketches.families.core_thermodynamics
public import FepSketches.families.learning_theory
public import FepSketches.collective_inference
public import FepSketches.learning_theory

@[expose] public section

/-!
# Collective-inference and learning-theory topic compositions

These bridges keep product-agent independence, consensus coupling, finite
support, and confidence assumptions visible.  Finite-law inequalities are
paired with measure-native results where no proved carrier conversion exists;
no asymptotic or collective-agency interpretation is introduced.
-/

namespace FEPComposed

open FEP FEP.CollectiveInference FEP.FiniteInformation
open FEP.LearningTheory FEP.VariationalDuality
open Filter MeasureTheory ProbabilityTheory Finset
open scoped BigOperators ENNReal MeasureTheory NNReal ProbabilityTheory

/-- Independent product-agent generative mass factorizes pointwise, while the
original native hierarchical joint remains normalized under probability and
Markov assumptions. -/
theorem fep107_product_agent_extends_fep027_hierarchy
    {StateLeft StateRight ObservationLeft ObservationRight : Type*}
    [Fintype StateLeft] [Fintype StateRight]
    [Fintype ObservationLeft] [Fintype ObservationRight]
    (priorLeft : FiniteLaw StateLeft) (priorRight : FiniteLaw StateRight)
    (kernelLeft : FiniteKernel StateLeft ObservationLeft)
    (kernelRight : FiniteKernel StateRight ObservationRight)
    (stateLeft : StateLeft) (stateRight : StateRight)
    (observationLeft : ObservationLeft) (observationRight : ObservationRight)
    {NativeParent NativeChild : Type*}
    [MeasurableSpace NativeParent] [MeasurableSpace NativeChild]
    (nativePrior : Measure NativeParent) [IsProbabilityMeasure nativePrior]
    (nativeKernel : Kernel NativeParent NativeChild)
    [IsMarkovKernel nativeKernel] :
    ((productKernel kernelLeft kernelRight).joint
        (FiniteLaw.product priorLeft priorRight)
        ((stateLeft, stateRight), (observationLeft, observationRight)) =
      kernelLeft.joint priorLeft (stateLeft, observationLeft) *
        kernelRight.joint priorRight (stateRight, observationRight)) ∧
      (fep_fep027.FEP027.fep027_hierarchicalJoint
        nativePrior nativeKernel Set.univ = 1) := by
  exact
    ⟨fep_fep107.FEP107.fep107_productAgent_generative_mass
        priorLeft priorRight kernelLeft kernelRight
        stateLeft stateRight observationLeft observationRight,
      fep_fep027.FEP027.fep027_hierarchical_mass_one
        nativePrior nativeKernel⟩

/-- Product-law collective VFE additivity extends the original four-block
global free-energy additivity law without identifying their scalar models. -/
theorem fep108_collective_vfe_extends_fep039_additivity
    {StateLeft StateRight : Type*} [Fintype StateLeft] [Fintype StateRight]
    (actualLeft referenceLeft : FiniteLaw StateLeft)
    (actualRight referenceRight : FiniteLaw StateRight)
    (leftCost : StateLeft → ℝ) (rightCost : StateRight → ℝ)
    (hReferenceLeft : ∀ state, 0 < referenceLeft state)
    (hReferenceRight : ∀ state, 0 < referenceRight state)
    (oldLeft oldRight : Fin 4 → ℝ) :
    collectiveVFE
          actualLeft referenceLeft actualRight referenceRight leftCost rightCost =
        variationalFreeEnergy actualLeft referenceLeft leftCost +
          variationalFreeEnergy actualRight referenceRight rightCost ∧
      (fep_fep039.FEP039.fep039_global_fe
          (fun index => oldLeft index + oldRight index) =
        fep_fep039.FEP039.fep039_global_fe oldLeft +
          fep_fep039.FEP039.fep039_global_fe oldRight) := by
  exact
    ⟨fep_fep108.FEP108.fep108_collectiveVFE_additive
        actualLeft referenceLeft actualRight referenceRight leftCost rightCost
        hReferenceLeft hReferenceRight,
      fep_fep039.FEP039.fep039_global_add oldLeft oldRight⟩

/-- Independent-agent EFE additivity is paired with the original truncated
EFE sign convention and its exact epistemic-balance premise. -/
theorem fep109_independent_efe_extends_fep021
    {StateLeft StateRight : Type*} [Fintype StateLeft] [Fintype StateRight]
    (predictiveLeft preferenceLeft : FiniteLaw StateLeft)
    (predictiveRight preferenceRight : FiniteLaw StateRight)
    (ambiguityLeft : StateLeft → ℝ) (ambiguityRight : StateRight → ℝ)
    (hPreferenceLeft : ∀ state, 0 < preferenceLeft state)
    (hPreferenceRight : ∀ state, 0 < preferenceRight state)
    {pragmaticCost epistemicValue : ENNReal}
    (hEpistemicValue : epistemicValue ≤ pragmaticCost) :
    independentCollectiveEFE
          predictiveLeft preferenceLeft predictiveRight preferenceRight
          ambiguityLeft ambiguityRight =
        expectedFreeEnergy predictiveLeft preferenceLeft ambiguityLeft +
          expectedFreeEnergy predictiveRight preferenceRight ambiguityRight ∧
      (fep_fep021.FEP021.fep021_expectedFreeEnergy
          pragmaticCost epistemicValue + epistemicValue = pragmaticCost) := by
  exact
    ⟨fep_fep109.FEP109.fep109_independentEFE_additive
        predictiveLeft preferenceLeft predictiveRight preferenceRight
        ambiguityLeft ambiguityRight hPreferenceLeft hPreferenceRight,
      fep_fep021.FEP021.fep021_efe_epistemic_balance hEpistemicValue⟩

/-- A positive-normalizer unit-weight product-of-experts pool and a
nonempty-support softmax each expose exact finite normalization. -/
theorem fep110_product_of_experts_refines_fep028_normalization
    {State : Type*} [Fintype State]
    (left right : FiniteLaw State)
    (hNormalizer : 0 < productOfExpertsNormalizer left right)
    (gamma : ℝ) (cost : Fin 10 → ℝ) (policies : Finset (Fin 10))
    (hPolicies : policies.Nonempty) :
    (∑ state,
        unitWeightProductOfExpertsPool left right hNormalizer state = 1) ∧
      (∑ policy ∈ policies,
        fep_fep028.FEP028.fep028_softmax gamma cost policies policy = 1) := by
  exact
    ⟨fep_fep110.FEP110.fep110_unitWeightProductOfExpertsPool_normalized
        left right hNormalizer,
      fep_fep028.FEP028.fep028_softmax_probs_sum_one
        gamma cost policies hPolicies⟩

/-- The two-agent consensus step conserves pointwise mass; the original
antisymmetric-current theorem conserves total divergence. -/
theorem fep111_consensus_mass_extends_fep025_conservation
    {State : Type*} [Fintype State]
    (left right : FiniteLaw State) (state : State)
    {size : ℕ} (current : Matrix (Fin size) (Fin size) ℝ)
    (hCurrent : ∀ source target,
      current source target = -current target source) :
    consensusLeft left right state + consensusRight left right state =
        left state + right state ∧
      (∑ source,
        fep_fep025.FEP025.fep025_divergence current source = 0) := by
  exact
    ⟨fep_fep111.FEP111.fep111_consensus_pointwise_mass_conserved
        left right state,
      fep_fep025.FEP025.fep025_total_divergence_zero current hCurrent⟩

/-- Atomwise consensus disagreement converges to zero, extending the original
concrete halving-contraction convergence witness. -/
theorem fep112_consensus_convergence_extends_fep048_contraction
    {State : Type*} [Fintype State]
    (left right : FiniteLaw State) (state : State) (initial : ℝ) :
    Tendsto
          (fun iterations =>
            beliefGap
              (consensusIterate (left, right) iterations).1
              (consensusIterate (left, right) iterations).2 state)
          atTop (nhds 0) ∧
      Tendsto
        (fun iterations => fep_fep048.FEP048.fep048_halfUpdate^[iterations] initial)
        atTop (nhds 0) := by
  exact
    ⟨fep_fep112.FEP112.fep112_consensus_converges left right state,
      fep_fep048.FEP048.fep048_halfUpdate_iterates_converge initial⟩

/-- Nonzero consensus disagreement gives strict coupled-potential descent,
alongside the original stable-step quadratic-energy descent law. -/
theorem fep113_coupled_potential_refines_fep032_descent
    {State : Type*} [Fintype State]
    (left right : FiniteLaw State) (state : State)
    (hSeparated : left state ≠ right state)
    {step center estimate : ℝ} (hStepNonnegative : 0 ≤ step)
    (hStepAtMostTwo : step ≤ 2) :
    coupledPotential (consensusLeft left right)
          (consensusRight left right) state <
        coupledPotential left right state ∧
      (fep_fep032.FEP032.fep032_quadraticUpdate step center estimate - center) ^ 2 ≤
        (estimate - center) ^ 2 := by
  exact
    ⟨fep_fep113.FEP113.fep113_coupledPotential_strict_descent
        left right state hSeparated,
      fep_fep032.FEP032.fep032_quadraticEnergy_descent
        hStepNonnegative hStepAtMostTwo⟩

/-- The finite-sample sub-Gaussian tail certificate is paired with the original
strict positivity of a Laplace-smoothed empirical rate. -/
theorem fep114_subgaussian_tail_refines_fep036_empirical_rate
    {Omega : Type*} [MeasurableSpace Omega]
    (law : Measure Omega) {sampleCount : ℕ}
    (observables : Fin sampleCount → Omega → ℝ)
    (hIndependent : iIndepFun observables law)
    (proxyVariance : Fin sampleCount → ℝ≥0)
    (hSubGaussian : ∀ index,
      HasSubgaussianMGF (observables index) (proxyVariance index) law)
    {deviation : ℝ} (hDeviation : 0 ≤ deviation)
    (successes trials : ℕ) :
    law.real {outcome |
        (sampleCount : ℝ) * deviation ≤
          ∑ index, observables index outcome} ≤
        Real.exp
          (-((sampleCount : ℝ) * deviation) ^ 2 /
            (2 * ∑ index, proxyVariance index)) ∧
      0 < fep_fep036.FEP036.fep036_smoothedRate successes trials := by
  exact
    ⟨fep_fep114.FEP114.fep114_subGaussian_empiricalMean_tail
        law observables hIndependent proxyVariance hSubGaussian hDeviation,
      fep_fep036.FEP036.fep036_smoothedRate_pos successes trials⟩

/-- The simultaneous finite-alphabet frequency bound is paired with the
original exact Bernoulli likelihood factorization through finite counts. -/
theorem fep115_frequency_union_bound_extends_fep042_counts
    {Omega Alphabet : Type*} [MeasurableSpace Omega]
    [Fintype Alphabet] [DecidableEq Alphabet]
    (law : Measure Omega) [IsProbabilityMeasure law]
    {sampleCount : ℕ} [NeZero sampleCount]
    (sample : Omega → Fin sampleCount → Alphabet)
    (target : Alphabet → ℝ) (deviation perSymbolFailure : ℝ)
    (hPerSymbol : ∀ symbol,
      law.real (frequencyDeviationEvent sample target deviation symbol) ≤
        perSymbolFailure)
    (bernoulliParameter : ℝ) (data : List Bool) :
    law.real (⋃ symbol,
        frequencyDeviationEvent sample target deviation symbol) ≤
        Fintype.card Alphabet * perSymbolFailure ∧
      (fep_fep042.FEP042.fep042_bernoulliLikelihood bernoulliParameter data =
        bernoulliParameter ^ fep_fep042.FEP042.fep042_successCount data *
          (1 - bernoulliParameter) ^
            fep_fep042.FEP042.fep042_failureCount data) := by
  exact
    ⟨fep_fep115.FEP115.fep115_simultaneous_frequency_bound
        law sample target deviation perSymbolFailure hPerSymbol,
      fep_fep042.FEP042.fep042_likelihood_factorizes
        bernoulliParameter data⟩

/-- The finite posterior loss-gap bound conditioned on a certified log-MGF
budget is paired with fep-001's measure-native variational upper bound without
equating finite real KL and native extended KL. -/
theorem fep116_pac_bayes_refines_fep001_variational_bound
    {Hypothesis : Type*} [Fintype Hypothesis]
    (prior posterior : FiniteLaw Hypothesis)
    (certificate : GibbsCertificate Hypothesis)
    (hCertificate : certificate.reference = prior)
    (empiricalLoss populationLoss : Hypothesis → ℝ)
    (inverseTemperature : ℝ)
    (hInverseTemperature : 0 < inverseTemperature)
    (hPotential : ∀ hypothesis,
      certificate.potential hypothesis = inverseTemperature *
        (populationLoss hypothesis - empiricalLoss hypothesis))
    (confidence : ℝ)
    (hConfidencePositive : 0 < confidence)
    (hConfidenceBelowOne : confidence < 1)
    (hLogMGF : certificate.logPartition ≤ Real.log confidence⁻¹)
    {Native : Type*} [MeasurableSpace Native]
    (approximation exactPosterior : Measure Native) (surprisal : ENNReal) :
    expectation posterior populationLoss ≤
        expectation posterior empiricalLoss +
          (finiteKL posterior prior + Real.log confidence⁻¹) /
            inverseTemperature ∧
      surprisal ≤
        fep_fep001.FEP001.fep001_variationalUpperBound
          approximation exactPosterior surprisal := by
  exact
    ⟨fep_fep116.FEP116.fep116_finitePACBayes_with_confidence
        prior posterior certificate hCertificate empiricalLoss populationLoss
        inverseTemperature hInverseTemperature hPotential confidence
        hConfidencePositive hConfidenceBelowOne hLogMGF,
      fep_fep001.FEP001.fep001_variationalUpperBound_ge
        approximation exactPosterior surprisal⟩

/-- Finite posterior odds obey Bayes multiplication, while the measure-native
fep-017 posterior reconstructs its complete swapped joint law. -/
theorem fep117_posterior_odds_extends_fep017_bayes
    {Hypothesis Evidence : Type*} [Fintype Hypothesis] [Fintype Evidence]
    (prior : FiniteLaw Hypothesis)
    (likelihood : FiniteKernel Hypothesis Evidence)
    (evidence : Evidence)
    (hEvidence : 0 < likelihood.predictive prior evidence)
    (favored reference : Hypothesis)
    (hReferencePrior : 0 < prior reference)
    (hReferenceLikelihood : 0 < likelihood reference evidence)
    {NativeHypothesis NativeEvidence : Type*}
    [MeasurableSpace NativeHypothesis] [MeasurableSpace NativeEvidence]
    [StandardBorelSpace NativeHypothesis] [Nonempty NativeHypothesis]
    (nativePrior : Measure NativeHypothesis) [IsFiniteMeasure nativePrior]
    (nativeLikelihood : Kernel NativeHypothesis NativeEvidence)
    [IsFiniteKernel nativeLikelihood] :
    posteriorOdds prior likelihood evidence hEvidence favored reference =
        (prior favored / prior reference) *
          (likelihood favored evidence / likelihood reference evidence) ∧
      ((nativeLikelihood ∘ₘ nativePrior) ⊗ₘ
          fep_fep017.FEP017.fep017_posterior nativeLikelihood nativePrior =
        (nativePrior ⊗ₘ nativeLikelihood).map Prod.swap) := by
  exact
    ⟨fep_fep117.FEP117.fep117_posteriorOdds_recursion
        prior likelihood evidence hEvidence favored reference
        hReferencePrior hReferenceLikelihood,
      fep_fep017.FEP017.fep017_posterior_joint_reconstruction
        nativeLikelihood nativePrior⟩

/-- A finite likelihood gap bounds inferior posterior mass exponentially,
while the original Bernoulli update remains normalized for every parameter. -/
theorem fep118_posterior_concentration_extends_fep045_update
    (priorGood priorBad likelihoodGood likelihoodBad likelihoodGap : ℝ)
    (sampleCount : ℕ)
    (hPriorGood : 0 < priorGood) (hPriorBad : 0 ≤ priorBad)
    (hLikelihoodGood : 0 < likelihoodGood)
    (hLikelihoodBad : 0 ≤ likelihoodBad)
    (hGap : 0 ≤ likelihoodGap)
    (hGapBound : likelihoodBad ≤ Real.exp (-likelihoodGap) * likelihoodGood)
    (bernoulliPrior likelihoodFalse likelihoodTrue : ℝ) :
    twoHypothesisPosteriorBad
          priorGood priorBad likelihoodGood likelihoodBad sampleCount ≤
        (priorBad / priorGood) *
          Real.exp (-((sampleCount : ℝ) * likelihoodGap)) ∧
      (∑ value : Bool,
        fep_fep045.FEP045.fep045_bernoulliMass
          (fep_fep045.FEP045.fep045_posteriorParameter
            bernoulliPrior likelihoodFalse likelihoodTrue) value = 1) := by
  exact
    ⟨fep_fep118.FEP118.fep118_posteriorGap_concentration
        priorGood priorBad likelihoodGood likelihoodBad likelihoodGap sampleCount
        hPriorGood hPriorBad hLikelihoodGood hLikelihoodBad hGap hGapBound,
      fep_fep045.FEP045.fep045_posterior_mass_one
        bernoulliPrior likelihoodFalse likelihoodTrue⟩

/-- Mixture log-loss regret exposes the selected model's prior penalty, and
fep-026 proves that negative-log complexity is additive for the same positive
prior-likelihood product. -/
theorem fep119_mixture_log_loss_refines_fep026_complexity
    {Hypothesis : Type*} [Fintype Hypothesis]
    (prior : FiniteLaw Hypothesis) (likelihood : Hypothesis → ℝ)
    (hLikelihood : ∀ hypothesis, 0 ≤ likelihood hypothesis)
    (selected : Hypothesis) (hPrior : 0 < prior selected)
    (hSelectedLikelihood : 0 < likelihood selected) :
    -Real.log (mixtureEvidence prior likelihood) ≤
        -Real.log (likelihood selected) - Real.log (prior selected) ∧
      (fep_fep026.FEP026.fep026_priorComplexity
          (prior selected * likelihood selected) =
        fep_fep026.FEP026.fep026_priorComplexity (prior selected) +
          fep_fep026.FEP026.fep026_priorComplexity (likelihood selected)) := by
  exact
    ⟨fep_fep119.FEP119.fep119_mixtureLogLoss_regret
        prior likelihood hLikelihood selected hPrior hSelectedLikelihood,
      fep_fep026.FEP026.fep026_complexity_additive
        hPrior hSelectedLikelihood⟩

/-- Multiplicative Bayes factors agree with sequential odds updates, while
fep-019 records associativity for the corresponding native predictive chain. -/
theorem fep120_bayes_factor_update_extends_fep019_prediction
    (priorOdds firstFavored firstReference secondFavored secondReference : ℝ)
    (hFirstReference : firstReference ≠ 0)
    (hSecondReference : secondReference ≠ 0)
    {NativeState NativeMiddle NativeEvidence : Type*}
    [MeasurableSpace NativeState] [MeasurableSpace NativeMiddle]
    [MeasurableSpace NativeEvidence]
    (nativePrior : Measure NativeState)
    (firstKernel : Kernel NativeState NativeMiddle)
    (secondKernel : Kernel NativeMiddle NativeEvidence) :
    (bayesFactor (firstFavored * secondFavored)
          (firstReference * secondReference) =
        bayesFactor firstFavored firstReference *
          bayesFactor secondFavored secondReference ∧
      updatedModelOdds priorOdds (firstFavored * secondFavored)
          (firstReference * secondReference) =
        updatedModelOdds
          (updatedModelOdds priorOdds firstFavored firstReference)
          secondFavored secondReference) ∧
      (secondKernel ∘ₘ
          fep_fep019.FEP019.fep019_priorPredictive firstKernel nativePrior =
        fep_fep019.FEP019.fep019_priorPredictive
          (secondKernel ∘ₖ firstKernel) nativePrior) := by
  exact
    ⟨fep_fep120.FEP120.fep120_bayesFactor_multiplicative_update
        priorOdds firstFavored firstReference secondFavored secondReference
        hFirstReference hSecondReference,
      fep_fep019.FEP019.fep019_priorPredictive_assoc
        firstKernel secondKernel nativePrior⟩

end FEPComposed
