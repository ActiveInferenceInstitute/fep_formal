module
public import FepSketches.families.causal_blankets_interventions
public import FepSketches.families.core_active_inference
public import FepSketches.families.core_bayesian_mechanics
public import FepSketches.families.core_free_energy
public import FepSketches.families.predictive_coding_generalized
public import FepSketches.causal_dynamics
public import FepSketches.predictive_coding

@[expose] public section

/-!
# Causal and predictive-coding topic compositions

The causal bridges preserve the distinction between finite conditional mutual
information and Mathlib's measure-theoretic conditional independence.  The
predictive-coding bridges specialize older quadratic, derivative, flow, and
convergence laws on shared scalar or finite-jet variables.
-/

namespace FEPComposed

open FEP FEP.CausalDynamics FEP.FiniteInformation FEP.MarkovBlanket
open FEP.PredictiveCoding
open Filter MeasureTheory ProbabilityTheory Finset Topology
open scoped BigOperators ENNReal MeasureTheory ProbabilityTheory

/-- Finite blanket factorization is characterized by zero conditional mutual
information, while fep-009 supplies the nonnegative product-mass primitive. -/
theorem fep079_blanket_cmi_refines_fep009
    {Blanket Internal External NativeLeft NativeRight : Type*}
    [Fintype Blanket] [Fintype Internal] [Fintype External]
    [MeasurableSpace NativeLeft] [MeasurableSpace NativeRight]
    (model : ConditionalBlanketModel Blanket Internal External)
    (hBlanket : ∀ blanket, 0 < model.blanketLaw blanket)
    (left : Measure NativeLeft) (right : Measure NativeRight)
    (leftEvent : Set NativeLeft) (rightEvent : Set NativeRight) :
    (conditionalMutualInformation model = 0 ↔ Factorizes model) ∧
      0 ≤ left leftEvent * right rightEvent := by
  exact
    ⟨fep_fep079.FEP079.fep079_blanketFactorization_iff_conditionalMutualInformation_zero
        model hBlanket,
      fep_fep009.FEP009.fep009_joint_product_nonneg
        left right leftEvent rightEvent⟩

/-- Mixing a shared finite conditional law commutes with joint formation,
alongside fep-019's native sequential-prediction associativity. -/
theorem fep080_shared_mixture_preserves_fep019_prediction
    {Input Output NativeInput NativeMiddle NativeOutput : Type*}
    [Fintype Input] [Fintype Output]
    [MeasurableSpace NativeInput] [MeasurableSpace NativeMiddle]
    [MeasurableSpace NativeOutput]
    (weight : ℝ) (hWeightNonnegative : 0 ≤ weight)
    (hWeightAtMostOne : weight ≤ 1)
    (left right : FiniteLaw Input) (kernel : FiniteKernel Input Output)
    (prior : Measure NativeInput)
    (earlier : Kernel NativeInput NativeMiddle)
    (later : Kernel NativeMiddle NativeOutput) :
    (kernel.joint
        (mixLaw weight hWeightNonnegative hWeightAtMostOne left right) =
      mixLaw weight hWeightNonnegative hWeightAtMostOne
        (kernel.joint left) (kernel.joint right)) ∧
      (later ∘ₘ fep_fep019.FEP019.fep019_priorPredictive earlier prior =
        fep_fep019.FEP019.fep019_priorPredictive
          (later ∘ₖ earlier) prior) := by
  exact
    ⟨fep_fep080.FEP080.fep080_sharedConditional_mixture_preservation
        weight hWeightNonnegative hWeightAtMostOne left right kernel,
      fep_fep019.FEP019.fep019_priorPredictive_assoc earlier later prior⟩

/-- Coupled blankets retain zero conditional mutual information within each
conditional row, together with fep-009's product-mass nonnegativity. -/
theorem fep081_coupled_blanket_composes_fep009
    {BlanketOne BlanketTwo InternalOne InternalTwo ExternalOne ExternalTwo : Type*}
    [Fintype BlanketOne] [Fintype BlanketTwo]
    [Fintype InternalOne] [Fintype InternalTwo]
    [Fintype ExternalOne] [Fintype ExternalTwo]
    [MeasurableSpace InternalOne] [MeasurableSpace ExternalOne]
    (blanketLaw : FiniteLaw (BlanketOne × BlanketTwo))
    (internalOne : FiniteKernel BlanketOne InternalOne)
    (internalTwo : FiniteKernel BlanketTwo InternalTwo)
    (externalOne : FiniteKernel BlanketOne ExternalOne)
    (externalTwo : FiniteKernel BlanketTwo ExternalTwo)
    (blanket : BlanketOne × BlanketTwo)
    (left : Measure InternalOne) (right : Measure ExternalOne)
    (leftEvent : Set InternalOne) (rightEvent : Set ExternalOne) :
    mutualInformation
          (conditionalJoint
            (coupledBlanketModel blanketLaw internalOne internalTwo
              externalOne externalTwo) blanket) = 0 ∧
      0 ≤ left leftEvent * right rightEvent := by
  exact
    ⟨fep_fep081.FEP081.fep081_coupledSubsystem_blanketComposition
        blanketLaw internalOne internalTwo externalOne externalTwo blanket,
      fep_fep009.FEP009.fep009_joint_product_nonneg
        left right leftEvent rightEvent⟩

/-- Every hard intervention row is normalized, as is every reachable law under
the original fep-023 normalization premise. -/
theorem fep082_intervention_normalization_extends_fep023
    {Context Value Policy Outcome : Type*}
    [Fintype Context] [Fintype Value] [DecidableEq Value]
    [MeasurableSpace Outcome]
    (chosen : Value) (context : Context)
    (policies : Set Policy) (law : Policy → Measure Outcome)
    (hLaw : ∀ policy ∈ policies, law policy Set.univ = 1)
    {reachable : Measure Outcome}
    (hReachable : reachable ∈
      fep_fep023.FEP023.fep023_reachableLaws policies law) :
    (∑ value, interventionKernel (Context := Context) chosen context value = 1) ∧
      reachable Set.univ = 1 := by
  exact
    ⟨fep_fep082.FEP082.fep082_interventionKernel_normalization chosen context,
      fep_fep023.FEP023.fep023_reachable_normalized
        policies law hLaw hReachable⟩

/-- Ordered intervention preserves the named non-descendant marginal; fep-009
simultaneously records monotonicity for any nested measurable events. -/
theorem fep083_intervention_invariance_refines_fep009
    {Root NonDescendant Mediator Outcome Native : Type*}
    [Fintype Root] [Fintype NonDescendant]
    [Fintype Mediator] [Fintype Outcome] [DecidableEq Root]
    [MeasurableSpace Native]
    (model : OrderedFourNodeModel Root NonDescendant Mediator Outcome)
    (root : Root) (nativeLaw : Measure Native)
    {smaller larger : Set Native} (hSubset : smaller ⊆ larger) :
    nonDescendantMarginal (interventionalJoint model root) =
        model.nonDescendantLaw ∧
      nativeLaw smaller ≤ nativeLaw larger := by
  exact
    ⟨fep_fep083.FEP083.fep083_nonDescendant_intervention_invariance model root,
      fep_fep009.FEP009.fep009_likelihood_mono hSubset⟩

/-- The finite ordered four-node density and the native three-level hierarchy
both expose their complete product factorization. -/
theorem fep084_ordered_factorization_extends_fep027
    {Root NonDescendant Mediator Outcome NativeRoot NativeMiddle NativeOutcome :
      Type*}
    [Fintype Root] [Fintype NonDescendant]
    [Fintype Mediator] [Fintype Outcome]
    [MeasurableSpace NativeRoot] [MeasurableSpace NativeMiddle]
    [MeasurableSpace NativeOutcome]
    (model : OrderedFourNodeModel Root NonDescendant Mediator Outcome)
    (root : Root) (nonDescendant : NonDescendant)
    (mediator : Mediator) (outcome : Outcome)
    (nativePrior : Measure NativeRoot)
    (nativeFirst : Kernel NativeRoot NativeMiddle)
    (nativeSecond : Kernel (NativeRoot × NativeMiddle) NativeOutcome) :
    (orderedJoint model (((root, nonDescendant), mediator), outcome) =
      ((model.rootLaw root * model.nonDescendantLaw nonDescendant) *
          model.mediatorGivenRoot root mediator) *
        model.outcomeGivenParents (nonDescendant, mediator) outcome) ∧
      ((fep_fep027.FEP027.fep027_hierarchicalJoint
          nativePrior nativeFirst ⊗ₘ nativeSecond).map
          MeasurableEquiv.prodAssoc =
        fep_fep027.FEP027.fep027_hierarchicalJoint
          nativePrior (nativeFirst ⊗ₖ nativeSecond)) := by
  exact
    ⟨fep_fep084.FEP084.fep084_orderedFiniteCausal_factorization
        model root nonDescendant mediator outcome,
      fep_fep027.FEP027.fep027_hierarchical_assoc
        nativePrior nativeFirst nativeSecond⟩

/-- The ordered finite carrier yields zero local mutual information at positive
evidence, while fep-009 supplies an inhabited native conditional-independence
boundary against the trivial sigma algebra. -/
theorem fep085_local_markov_refines_fep009
    {Root NonDescendant Mediator Outcome Native : Type*}
    [Fintype Root] [Fintype NonDescendant]
    [Fintype Mediator] [Fintype Outcome]
    [mNative : MeasurableSpace Native] [StandardBorelSpace Native]
    (model : OrderedFourNodeModel Root NonDescendant Mediator Outcome)
    (nonDescendant : NonDescendant) (mediator : Mediator)
    (hEvidence : 0 < mediatorEvidence model mediator)
    (conditioning observed : MeasurableSpace Native)
    (hConditioning : conditioning ≤ mNative)
    (nativeLaw : @Measure Native mNative) [IsFiniteMeasure nativeLaw] :
    mutualInformation
          (localMarkovConditional model nonDescendant mediator hEvidence) = 0 ∧
      CondIndep conditioning observed ⊥ hConditioning nativeLaw := by
  exact
    ⟨fep_fep085.FEP085.fep085_localMarkov_mutualInformation_zero
        model nonDescendant mediator hEvidence,
      fep_fep009.FEP009.fep009_condIndep_bot_right
        (mΩ := mNative) conditioning observed hConditioning nativeLaw⟩

/-- Precision energy is nonnegative both in the predictive-coding definition
and in fep-016's unhalved weighted-quadratic primitive. -/
theorem fep086_precision_energy_refines_fep016
    {precision : ℝ} (hPrecision : 0 ≤ precision)
    (observation estimate : ℝ) :
    0 ≤ precisionEnergy precision observation estimate ∧
      0 ≤ (precision / 2) * (observation - estimate) ^ 2 := by
  exact
    ⟨fep_fep086.FEP086.fep086_precisionWeighted_predictionError_nonnegative
        hPrecision observation estimate,
      fep_fep016.FEP016.fep016_precision_weighted
        (precision / 2) observation estimate
        (div_nonneg hPrecision (by norm_num))⟩

/-- A hierarchical prediction-error sum decomposes by level, while fep-039
certifies additivity of a four-block global free energy. -/
theorem fep087_hierarchical_energy_extends_fep039
    {depth : ℕ} (precision error : Fin (depth + 1) → ℝ)
    (left right : Fin 4 → ℝ) :
    (hierarchicalEnergy precision error =
      precision 0 / 2 * error 0 ^ 2 +
        ∑ level : Fin depth,
          precision level.succ / 2 * error level.succ ^ 2) ∧
      (fep_fep039.FEP039.fep039_global_fe
          (fun index => left index + right index) =
        fep_fep039.FEP039.fep039_global_fe left +
          fep_fep039.FEP039.fep039_global_fe right) := by
  exact
    ⟨fep_fep087.FEP087.fep087_hierarchicalPredictiveCoding_decomposition
        precision error,
      fep_fep039.FEP039.fep039_global_add left right⟩

/-- The predictive-error derivative and fep-043's quadratic derivative are
the same scalar geometry at curvature `precision / 2`. -/
theorem fep088_prediction_gradient_extends_fep043
    (precision observation estimate : ℝ) :
    HasDerivAt
          (fun candidate => precisionEnergy precision observation candidate)
          (-precision * predictionError observation estimate) estimate ∧
      HasDerivAt
        (fep_fep043.FEP043.fep043_quadraticFreeEnergy
          (precision / 2) observation 0)
        (fep_fep043.FEP043.fep043_quadraticGradient
          (precision / 2) observation estimate) estimate := by
  exact
    ⟨fep_fep088.FEP088.fep088_predictionError_gradient_identity
        precision observation estimate,
      fep_fep043.FEP043.fep043_quadratic_hasDerivAt
        (precision / 2) observation 0 estimate⟩

/-- Finite-jet shifts satisfy their native additive law and instantiate
fep-006's generic discrete-flow semigroup under one-degree shifting. -/
theorem fep089_finite_jet_shift_specializes_fep006
    {order : ℕ} (first second : ℕ) (jet : FiniteJet order) :
    shift (first + second) jet = shift first (shift second jet) ∧
      fep_fep006.FEP006.fep006_iterateFlow
          (shift 1 : FiniteJet order → FiniteJet order)
          (first + second) jet =
        fep_fep006.FEP006.fep006_iterateFlow
          (shift 1 : FiniteJet order → FiniteJet order) first
          (fep_fep006.FEP006.fep006_iterateFlow
            (shift 1 : FiniteJet order → FiniteJet order) second jet) := by
  exact
    ⟨fep_fep089.FEP089.fep089_finiteJet_shift_semigroup first second jet,
      fep_fep006.FEP006.fep006_iterateFlow_add
        (shift 1 : FiniteJet order → FiniteJet order) first second jet⟩

/-- A generalized-filter correction exposes its shift-minus-gradient equation;
the same coordinate gradient is backed by fep-043's exact quadratic derivative. -/
theorem fep090_generalized_correction_combines_fep043
    {order : ℕ} (stepSize : ℝ) (precision : ℕ → ℝ)
    (target estimate : FiniteJet order) (degree : ℕ) :
    ((generalizedFilteringStep stepSize precision target estimate).coefficient
        degree =
      estimate.coefficient degree + stepSize *
        ((shift 1 estimate).coefficient degree -
          precisionEnergyGradient (precision degree)
            (target.coefficient degree) (estimate.coefficient degree))) ∧
      HasDerivAt
        (fep_fep043.FEP043.fep043_quadraticFreeEnergy
          (precision degree / 2) (target.coefficient degree) 0)
        (fep_fep043.FEP043.fep043_quadraticGradient
          (precision degree / 2) (target.coefficient degree)
            (estimate.coefficient degree))
        (estimate.coefficient degree) := by
  exact
    ⟨fep_fep090.FEP090.fep090_finiteJet_generalizedFiltering_correctionEquation
        stepSize precision target estimate degree,
      fep_fep043.FEP043.fep043_quadratic_hasDerivAt
        (precision degree / 2) (target.coefficient degree) 0
        (estimate.coefficient degree)⟩

/-- Precision modulation is monotone in the predictive energy and specializes
fep-016's nonnegative weighted quadratic at the lower precision. -/
theorem fep091_precision_modulation_refines_fep016
    {lower upper : ℝ} (hLowerNonnegative : 0 ≤ lower)
    (hPrecision : lower ≤ upper) (observation estimate : ℝ) :
    (0 ≤ precisionEnergy lower observation estimate ∧
      precisionEnergy lower observation estimate ≤
        precisionEnergy upper observation estimate) ∧
      0 ≤ (lower / 2) * (observation - estimate) ^ 2 := by
  exact
    ⟨fep_fep091.FEP091.fep091_precisionModulation_energy_mono
        hLowerNonnegative hPrecision observation estimate,
      fep_fep016.FEP016.fep016_precision_weighted
        (lower / 2) observation estimate
        (div_nonneg hLowerNonnegative (by norm_num))⟩

/-- On the shared stability interval, predictive error tends to zero and the
equivalent centered quadratic iteration from fep-032 tends to its target. -/
theorem fep092_quadratic_convergence_specializes_fep032
    {stepSize : ℝ} (hStepPositive : 0 < stepSize)
    (hStepBelowTwo : stepSize < 2) (target estimate : ℝ) :
    Tendsto
          (fun iterations => predictionError target
            (iteratePredictionUpdate stepSize target iterations estimate))
          atTop (nhds 0) ∧
      Tendsto
        (fun iterations =>
          ((fep_fep032.FEP032.fep032_quadraticUpdate stepSize target)^[iterations])
            estimate)
        atTop (nhds target) := by
  exact
    ⟨fep_fep092.FEP092.fep092_quadraticPredictiveCoding_error_tendsto_zero
        hStepPositive hStepBelowTwo target estimate,
      fep_fep032.FEP032.fep032_quadraticUpdate_tendsto
        hStepPositive hStepBelowTwo target estimate⟩

end FEPComposed
