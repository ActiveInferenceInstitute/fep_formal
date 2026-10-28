"""Canonical Lean bodies for causal blankets and interventions."""

from __future__ import annotations

BODIES: dict[str, str] = {
    "fep-079": """import FepSketches.causal_dynamics

namespace FEP079

open FEP FEP.CausalDynamics FEP.FiniteInformation FEP.MarkovBlanket

variable {Blanket Internal External Sensory Active : Type*}
  [Fintype Blanket] [Fintype Internal] [Fintype External]
  [Fintype Sensory] [Fintype Active]

/-- Under full blanket support, vanishing finite conditional mutual information
is equivalent to pointwise internal-external conditional factorization. -/
theorem fep079_blanketFactorization_iff_conditionalMutualInformation_zero
    (model : ConditionalBlanketModel Blanket Internal External)
    (hBlanket : ∀ blanket, 0 < model.blanketLaw blanket) :
    conditionalMutualInformation model = 0 ↔ Factorizes model :=
  conditionalMutualInformation_eq_zero_iff_factorizes model hBlanket

/-- A constructed static Markov-blanket model has zero conditional mutual
information even if some blanket values have zero probability. -/
theorem fep079_staticBlanket_conditionalMutualInformation_zero
    (model : StaticModel Internal Sensory Active External) :
    conditionalMutualInformation (ofStaticModel model) = 0 :=
  ofStaticModel_conditionalMutualInformation_zero model

end FEP079
""",
    "fep-080": """import FepSketches.causal_dynamics

namespace FEP080

open FEP FEP.CausalDynamics

variable {Input Output : Type*} [Fintype Input] [Fintype Output]

/-- Convex mixing commutes with formation of a joint law whenever both
components share the same conditional kernel. -/
theorem fep080_sharedConditional_mixture_preservation
    (weight : ℝ) (hWeightNonneg : 0 ≤ weight)
    (hWeightLeOne : weight ≤ 1)
    (left right : FiniteLaw Input) (kernel : FiniteKernel Input Output) :
    kernel.joint (mixLaw weight hWeightNonneg hWeightLeOne left right) =
      mixLaw weight hWeightNonneg hWeightLeOne
        (kernel.joint left) (kernel.joint right) :=
  sharedConditional_mixture_preserves_joint
    weight hWeightNonneg hWeightLeOne left right kernel

/-- The half-mixture witness puts positive, unequal-component mass on both
Boolean atoms. -/
theorem fep080_boolHalfMixture_nonvacuity :
    boolHalfMixture false = 1 / 2 ∧ boolHalfMixture true = 1 / 2 :=
  ⟨boolHalfMixture_false, boolHalfMixture_true⟩

end FEP080
""",
    "fep-081": """import FepSketches.causal_dynamics

namespace FEP081

open FEP FEP.CausalDynamics FEP.FiniteInformation FEP.MarkovBlanket

variable {Blanket₁ Blanket₂ Internal₁ Internal₂ External₁ External₂ : Type*}
  [Fintype Blanket₁] [Fintype Blanket₂]
  [Fintype Internal₁] [Fintype Internal₂]
  [Fintype External₁] [Fintype External₂]

/-- Two subsystems may have an arbitrarily coupled joint blanket law while
their paired internal and external rows retain zero conditional mutual
information. -/
theorem fep081_coupledSubsystem_blanketComposition
    (blanketLaw : FiniteLaw (Blanket₁ × Blanket₂))
    (internal₁ : FiniteKernel Blanket₁ Internal₁)
    (internal₂ : FiniteKernel Blanket₂ Internal₂)
    (external₁ : FiniteKernel Blanket₁ External₁)
    (external₂ : FiniteKernel Blanket₂ External₂)
    (blanket : Blanket₁ × Blanket₂) :
    mutualInformation
        (conditionalJoint
          (coupledBlanketModel blanketLaw internal₁ internal₂ external₁ external₂)
          blanket) = 0 :=
  coupledBlanket_conditionalMutualInformation_zero
    blanketLaw internal₁ internal₂ external₁ external₂ blanket

/-- The coupled-blanket carrier admits a non-product-looking diagonal Boolean
witness with zero cross mass. -/
theorem fep081_correlatedBlanket_nonvacuity :
    correlatedBoolBlanket (false, false) = 1 / 2 ∧
      correlatedBoolBlanket (true, true) = 1 / 2 ∧
      0 < mutualInformation correlatedBoolBlanket :=
  ⟨correlatedBoolBlanket_diagonal.1,
    correlatedBoolBlanket_diagonal.2,
    correlatedBoolBlanket_mutualInformation_pos⟩

end FEP081
""",
    "fep-082": """import FepSketches.causal_dynamics

namespace FEP082

open FEP FEP.CausalDynamics Finset
open scoped BigOperators

variable {Context Value : Type*} [Fintype Context] [Fintype Value]
  [DecidableEq Value]

/-- Every hard finite intervention kernel is normalized in every context. -/
theorem fep082_interventionKernel_normalization
    (chosen : Value) (context : Context) :
    ∑ value, interventionKernel (Context := Context) chosen context value = 1 :=
  interventionKernel_sum_one chosen context

/-- The hard intervention gives its chosen value unit mass. -/
theorem fep082_interventionKernel_chosen_mass
    (chosen : Value) (context : Context) :
    interventionKernel (Context := Context) chosen context chosen = 1 :=
  interventionKernel_chosen chosen context

/-- Every distinct value receives zero intervention mass. -/
theorem fep082_interventionKernel_other_mass
    (chosen other : Value) (hOther : other ≠ chosen) (context : Context) :
    interventionKernel (Context := Context) chosen context other = 0 :=
  interventionKernel_other chosen other hOther context

end FEP082
""",
    "fep-083": """import FepSketches.causal_dynamics

namespace FEP083

open FEP FEP.CausalDynamics

variable {Root NonDescendant Mediator Outcome : Type*}
  [Fintype Root] [Fintype NonDescendant]
  [Fintype Mediator] [Fintype Outcome] [DecidableEq Root]

/-- Intervening on the ordered root preserves the marginal law of the named
non-descendant. -/
theorem fep083_nonDescendant_intervention_invariance
    (model : OrderedFourNodeModel Root NonDescendant Mediator Outcome)
    (root : Root) :
    nonDescendantMarginal (interventionalJoint model root) =
      model.nonDescendantLaw :=
  nonDescendant_intervention_invariant model root

/-- In the concrete four-node model the intervention changes the mediator
descendant from zero to unit true-mass while preserving the non-descendant. -/
theorem fep083_fourNode_descendantChange_nonDescendantPreservation :
    mediatorMarginal (interventionalJoint boolOrderedModel false) true = 0 ∧
      mediatorMarginal (interventionalJoint boolOrderedModel true) true = 1 ∧
      nonDescendantMarginal (interventionalJoint boolOrderedModel false) =
        nonDescendantMarginal (interventionalJoint boolOrderedModel true) :=
  ⟨boolIntervention_false_mediator_true_zero,
    boolIntervention_true_mediator_true_one,
    boolIntervention_preserves_named_nonDescendant⟩

end FEP083
""",
    "fep-084": """import FepSketches.causal_dynamics

namespace FEP084

open FEP FEP.CausalDynamics Finset
open scoped BigOperators

variable {Root NonDescendant Mediator Outcome : Type*}
  [Fintype Root] [Fintype NonDescendant]
  [Fintype Mediator] [Fintype Outcome]

/-- The four-node observational law is exactly the product of its two root
laws and its two ordered parent kernels. -/
theorem fep084_orderedFiniteCausal_factorization
    (model : OrderedFourNodeModel Root NonDescendant Mediator Outcome)
    (root : Root) (nonDescendant : NonDescendant)
    (mediator : Mediator) (outcome : Outcome) :
    orderedJoint model (((root, nonDescendant), mediator), outcome) =
      ((model.rootLaw root * model.nonDescendantLaw nonDescendant) *
          model.mediatorGivenRoot root mediator) *
        model.outcomeGivenParents (nonDescendant, mediator) outcome :=
  orderedJoint_factorization model root nonDescendant mediator outcome

/-- The ordered factorization is a normalized joint law. -/
theorem fep084_orderedFiniteCausal_normalization
    (model : OrderedFourNodeModel Root NonDescendant Mediator Outcome) :
    ∑ state, orderedJoint model state = 1 :=
  orderedJoint_sum_one model

end FEP084
""",
    "fep-085": """import FepSketches.causal_dynamics

namespace FEP085

open FEP FEP.CausalDynamics FEP.FiniteInformation

variable {Root NonDescendant Mediator Outcome : Type*}
  [Fintype Root] [Fintype NonDescendant]
  [Fintype Mediator] [Fintype Outcome]

/-- In the maintained ordered carrier, the outcome and non-parent predecessor
root factorize after fixing the outcome's non-descendant and mediator parents. -/
theorem fep085_localMarkov_factorization_from_ordered
    (model : OrderedFourNodeModel Root NonDescendant Mediator Outcome)
    (nonDescendant : NonDescendant) (mediator : Mediator)
    (hEvidence : 0 < mediatorEvidence model mediator) :
    localMarkovConditional model nonDescendant mediator hEvidence =
      (model.mediatorGivenRoot.posterior model.rootLaw mediator hEvidence).product
        (model.outcomeGivenParents.row (nonDescendant, mediator)) :=
  localMarkov_factorization_from_ordered
    model nonDescendant mediator hEvidence

/-- The exact local product law has zero finite mutual information.  This is a
local Markov statement for the four-node carrier, not general d-separation. -/
theorem fep085_localMarkov_mutualInformation_zero
    (model : OrderedFourNodeModel Root NonDescendant Mediator Outcome)
    (nonDescendant : NonDescendant) (mediator : Mediator)
    (hEvidence : 0 < mediatorEvidence model mediator) :
    mutualInformation
        (localMarkovConditional model nonDescendant mediator hEvidence) = 0 :=
  localMarkov_mutualInformation_zero model nonDescendant mediator hEvidence

/-- The Boolean local-Markov theorem conditions on a positive half-mass
mediator event, providing a concrete nonvacuity witness. -/
theorem fep085_bool_localMarkov_nonvacuity :
    mutualInformation
        (localMarkovConditional boolOrderedModel false true
          (by rw [boolMediatorEvidence_true]; norm_num)) = 0 :=
  localMarkov_mutualInformation_zero boolOrderedModel false true
    (by rw [boolMediatorEvidence_true]; norm_num)

/-- Zero mediator evidence is the explicit conditioning boundary. -/
theorem fep085_zeroEvidence_boundary
    (model : OrderedFourNodeModel Root NonDescendant Mediator Outcome)
    (mediator : Mediator) (hZero : mediatorEvidence model mediator = 0) :
    ¬0 < mediatorEvidence model mediator :=
  localMarkov_zeroEvidence_boundary model mediator hZero

end FEP085
""",
}
