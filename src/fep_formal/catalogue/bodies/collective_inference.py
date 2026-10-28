"""Lean bodies for collective and multiagent active inference."""

from __future__ import annotations

BODIES: dict[str, str] = {
    "fep-107": """import FepSketches.collective_inference

/-! # Product-Agent Generative Law -/
namespace FEP107

open FEP Finset
open scoped BigOperators

variable {State₁ State₂ Observation₁ Observation₂ : Type*}
  [Fintype State₁] [Fintype State₂]
  [Fintype Observation₁] [Fintype Observation₂]

/-- Independent product kernels retain a normalized observation law at every
joint state. -/
theorem fep107_productKernel_normalized
    (left : FiniteKernel State₁ Observation₁)
    (right : FiniteKernel State₂ Observation₂)
    (state : State₁ × State₂) :
    ∑ observation,
      FEP.CollectiveInference.productKernel left right state observation = 1 :=
  FEP.CollectiveInference.productKernel_sum_one left right state

/-- With product priors and product kernels, the joint generative mass is the
product of the two agent-level generative masses. -/
theorem fep107_productAgent_generative_mass
    (priorLeft : FiniteLaw State₁) (priorRight : FiniteLaw State₂)
    (kernelLeft : FiniteKernel State₁ Observation₁)
    (kernelRight : FiniteKernel State₂ Observation₂)
    (stateLeft : State₁) (stateRight : State₂)
    (observationLeft : Observation₁) (observationRight : Observation₂) :
    (FEP.CollectiveInference.productKernel kernelLeft kernelRight).joint
        (FiniteLaw.product priorLeft priorRight)
        ((stateLeft, stateRight), (observationLeft, observationRight)) =
      kernelLeft.joint priorLeft (stateLeft, observationLeft) *
        kernelRight.joint priorRight (stateRight, observationRight) :=
  FEP.CollectiveInference.productAgent_joint_mass
    priorLeft priorRight kernelLeft kernelRight
    stateLeft stateRight observationLeft observationRight

end FEP107
""",
    "fep-108": """import FepSketches.collective_inference

/-! # Additive Collective Variational Free Energy -/
namespace FEP108

open FEP

variable {State₁ State₂ : Type*} [Fintype State₁] [Fintype State₂]

/-- Product-law VFE is additive under full-support reference factors and an
additive cost. -/
theorem fep108_collectiveVFE_additive
    (actualLeft referenceLeft : FiniteLaw State₁)
    (actualRight referenceRight : FiniteLaw State₂)
    (leftCost : State₁ → ℝ) (rightCost : State₂ → ℝ)
    (referenceLeftPositive : ∀ state, 0 < referenceLeft state)
    (referenceRightPositive : ∀ state, 0 < referenceRight state) :
    FEP.CollectiveInference.collectiveVFE
        actualLeft referenceLeft actualRight referenceRight leftCost rightCost =
      FEP.CollectiveInference.variationalFreeEnergy
          actualLeft referenceLeft leftCost +
        FEP.CollectiveInference.variationalFreeEnergy
          actualRight referenceRight rightCost :=
  FEP.CollectiveInference.collectiveVFE_additive
    actualLeft referenceLeft actualRight referenceRight leftCost rightCost
    referenceLeftPositive referenceRightPositive

/-- The expectation component has its own independent-product certificate. -/
theorem fep108_productCost_additive
    (left : FiniteLaw State₁) (right : FiniteLaw State₂)
    (leftCost : State₁ → ℝ) (rightCost : State₂ → ℝ) :
    FEP.CollectiveInference.expectedCost (FiniteLaw.product left right)
        (fun state => leftCost state.1 + rightCost state.2) =
      FEP.CollectiveInference.expectedCost left leftCost +
        FEP.CollectiveInference.expectedCost right rightCost :=
  FEP.CollectiveInference.productExpectedCost_additive
    left right leftCost rightCost

end FEP108
""",
    "fep-109": """import FepSketches.collective_inference

/-! # Independent-Agent Expected-Free-Energy Additivity -/
namespace FEP109

open FEP

variable {State₁ State₂ : Type*} [Fintype State₁] [Fintype State₂]

/-- EFE additivity follows from product predictive and preference laws,
additive ambiguity, and full-support preferences. -/
theorem fep109_independentEFE_additive
    (predictiveLeft preferenceLeft : FiniteLaw State₁)
    (predictiveRight preferenceRight : FiniteLaw State₂)
    (ambiguityLeft : State₁ → ℝ) (ambiguityRight : State₂ → ℝ)
    (preferenceLeftPositive : ∀ state, 0 < preferenceLeft state)
    (preferenceRightPositive : ∀ state, 0 < preferenceRight state) :
    FEP.CollectiveInference.independentCollectiveEFE
        predictiveLeft preferenceLeft predictiveRight preferenceRight
        ambiguityLeft ambiguityRight =
      FEP.CollectiveInference.expectedFreeEnergy
          predictiveLeft preferenceLeft ambiguityLeft +
        FEP.CollectiveInference.expectedFreeEnergy
          predictiveRight preferenceRight ambiguityRight :=
  FEP.CollectiveInference.independentEFE_additive
    predictiveLeft preferenceLeft predictiveRight preferenceRight
    ambiguityLeft ambiguityRight preferenceLeftPositive preferenceRightPositive

/-- Without the product construction, only the component expectation identity
is available; no dependence term is silently discarded. -/
theorem fep109_additiveAmbiguity_expectation
    (left : FiniteLaw State₁) (right : FiniteLaw State₂)
    (ambiguityLeft : State₁ → ℝ) (ambiguityRight : State₂ → ℝ) :
    FEP.CollectiveInference.expectedCost (FiniteLaw.product left right)
        (fun state => ambiguityLeft state.1 + ambiguityRight state.2) =
      FEP.CollectiveInference.expectedCost left ambiguityLeft +
        FEP.CollectiveInference.expectedCost right ambiguityRight :=
  FEP.CollectiveInference.productExpectedCost_additive
    left right ambiguityLeft ambiguityRight

end FEP109
""",
    "fep-110": """import FepSketches.collective_inference

/-! # Unit-Weight Product-of-Experts Pool Normalization -/
namespace FEP110

open FEP Finset
open scoped BigOperators

variable {State : Type*} [Fintype State]

/-- A positive pointwise-product normalizer yields a normalized unit-weight
product-of-experts pool. -/
theorem fep110_unitWeightProductOfExpertsPool_normalized
    (left right : FiniteLaw State)
    (normalizerPositive :
      0 < FEP.CollectiveInference.productOfExpertsNormalizer left right) :
    ∑ state,
        FEP.CollectiveInference.unitWeightProductOfExpertsPool
          left right normalizerPositive state = 1 :=
  FEP.CollectiveInference.unitWeightProductOfExpertsPool_sum_one
    left right normalizerPositive

/-- The pool mass is exactly the normalized pointwise product. It is a
unit-weight product of experts, not a half-exponent logarithmic pool. -/
theorem fep110_unitWeightProductOfExpertsPool_mass
    (left right : FiniteLaw State)
    (normalizerPositive :
      0 < FEP.CollectiveInference.productOfExpertsNormalizer left right)
    (state : State) :
    FEP.CollectiveInference.unitWeightProductOfExpertsPool
        left right normalizerPositive state =
      left state * right state /
        FEP.CollectiveInference.productOfExpertsNormalizer left right :=
  rfl

end FEP110
""",
    "fep-111": """import FepSketches.collective_inference

/-! # Consensus Mass Conservation -/
namespace FEP111

open FEP Finset
open scoped BigOperators

variable {State : Type*} [Fintype State]

/-- The doubly stochastic two-agent update conserves combined mass at every
state. -/
theorem fep111_consensus_pointwise_mass_conserved
    (left right : FiniteLaw State) (state : State) :
    FEP.CollectiveInference.consensusLeft left right state +
        FEP.CollectiveInference.consensusRight left right state =
      left state + right state :=
  FEP.CollectiveInference.consensusMass_conserved left right state

/-- Consequently, the two normalized post-update laws have total combined
mass two. -/
theorem fep111_consensus_total_mass_two
    (left right : FiniteLaw State) :
    (∑ state, FEP.CollectiveInference.consensusLeft left right state) +
        ∑ state, FEP.CollectiveInference.consensusRight left right state = 2 := by
  rw [(FEP.CollectiveInference.consensusLeft left right).sum_one,
    (FEP.CollectiveInference.consensusRight left right).sum_one]
  norm_num

end FEP111
""",
    "fep-112": """import FepSketches.collective_inference

/-! # Contractive Belief-Consensus Convergence -/
namespace FEP112

open FEP Filter

variable {State : Type*} [Fintype State]

/-- The strictly stochastic consensus matrix contracts every atomwise gap by
exactly one half. -/
theorem fep112_consensus_half_contraction
    (left right : FiniteLaw State) (state : State) :
    FEP.CollectiveInference.beliefGap
        (FEP.CollectiveInference.consensusLeft left right)
        (FEP.CollectiveInference.consensusRight left right) state =
      (1 / 2 : ℝ) *
        FEP.CollectiveInference.beliefGap left right state :=
  FEP.CollectiveInference.consensus_gap_contracts left right state

/-- Iterated consensus converges pointwise to zero disagreement. -/
theorem fep112_consensus_converges
    (left right : FiniteLaw State) (state : State) :
    Tendsto
      (fun iterations =>
        FEP.CollectiveInference.beliefGap
          (FEP.CollectiveInference.consensusIterate
            (left, right) iterations).1
          (FEP.CollectiveInference.consensusIterate
            (left, right) iterations).2 state)
      atTop (nhds 0) :=
  FEP.CollectiveInference.consensus_gap_tendsto_zero left right state

/-- The contraction is not a zero-gap tautology: opposite Boolean point masses
retain positive disagreement after one step and contract strictly. -/
theorem fep112_bool_nonzero_strict_witness :
    FEP.CollectiveInference.beliefGap
        (FiniteLaw.pointMass true) (FiniteLaw.pointMass false) true = 1 ∧
      FEP.CollectiveInference.beliefGap
          (FEP.CollectiveInference.consensusLeft
            (FiniteLaw.pointMass true) (FiniteLaw.pointMass false))
          (FEP.CollectiveInference.consensusRight
            (FiniteLaw.pointMass true) (FiniteLaw.pointMass false)) true = 1 / 2 ∧
      0 < FEP.CollectiveInference.beliefGap
          (FEP.CollectiveInference.consensusLeft
            (FiniteLaw.pointMass true) (FiniteLaw.pointMass false))
          (FEP.CollectiveInference.consensusRight
            (FiniteLaw.pointMass true) (FiniteLaw.pointMass false)) true ∧
      FEP.CollectiveInference.beliefGap
          (FEP.CollectiveInference.consensusLeft
            (FiniteLaw.pointMass true) (FiniteLaw.pointMass false))
          (FEP.CollectiveInference.consensusRight
            (FiniteLaw.pointMass true) (FiniteLaw.pointMass false)) true <
        FEP.CollectiveInference.beliefGap
          (FiniteLaw.pointMass true) (FiniteLaw.pointMass false) true :=
  FEP.CollectiveInference.boolConsensus_nonzero_strict_witness

end FEP112
""",
    "fep-113": """import FepSketches.collective_inference

/-! # Coupled-Agent Potential Descent -/
namespace FEP113

open FEP

variable {State : Type*} [Fintype State]

/-- The specified consensus coupling quarters the atomwise quadratic
disagreement potential. -/
theorem fep113_coupledPotential_contracts
    (left right : FiniteLaw State) (state : State) :
    FEP.CollectiveInference.coupledPotential
        (FEP.CollectiveInference.consensusLeft left right)
        (FEP.CollectiveInference.consensusRight left right) state =
      (1 / 4 : ℝ) *
        FEP.CollectiveInference.coupledPotential left right state :=
  FEP.CollectiveInference.coupledPotential_contracts left right state

/-- Nonzero disagreement makes the potential descent strict. -/
theorem fep113_coupledPotential_strict_descent
    (left right : FiniteLaw State) (state : State)
    (separated : left state ≠ right state) :
    FEP.CollectiveInference.coupledPotential
        (FEP.CollectiveInference.consensusLeft left right)
        (FEP.CollectiveInference.consensusRight left right) state <
      FEP.CollectiveInference.coupledPotential left right state :=
  FEP.CollectiveInference.coupledPotential_strict_descent
    left right state separated

end FEP113
""",
}
