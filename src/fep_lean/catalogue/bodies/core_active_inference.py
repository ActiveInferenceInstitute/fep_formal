"""Canonical Lean bodies for one original catalogue family."""

from __future__ import annotations

BODIES: dict[str, str] = {
    "fep-003": """import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Basic.ENNReal.Inv

namespace FEP003

open scoped ENNReal

/-- Discounted pragmatic expected-cost input to the EFE convention. -/
noncomputable def fep003_pragmaticCost
    (discount : ENNReal) (stageCost : ℕ → ENNReal) (horizon : ℕ) : ENNReal :=
  ∑ t ∈ Finset.range horizon, discount ^ t * stageCost t

/-- A zero planning horizon has zero pragmatic cost. -/
theorem fep003_pragmaticCost_zero
    (discount : ENNReal) (stageCost : ℕ → ENNReal) :
    fep003_pragmaticCost discount stageCost 0 = 0 := by
  simp [fep003_pragmaticCost]

/-- Extending the horizon exposes the exact discounted terminal increment. -/
theorem fep003_pragmaticCost_succ
    (discount : ENNReal) (stageCost : ℕ → ENNReal) (horizon : ℕ) :
    fep003_pragmaticCost discount stageCost (horizon + 1) =
      fep003_pragmaticCost discount stageCost horizon +
        discount ^ horizon * stageCost horizon := by
  simp [fep003_pragmaticCost, Finset.sum_range_succ]

/-- Pointwise larger stage costs produce larger pragmatic cost. -/
theorem fep003_pragmaticCost_mono
    (discount : ENNReal) {cost₁ cost₂ : ℕ → ENNReal}
    (hcost : ∀ t, cost₁ t ≤ cost₂ t) (horizon : ℕ) :
    fep003_pragmaticCost discount cost₁ horizon ≤
      fep003_pragmaticCost discount cost₂ horizon := by
  exact Finset.sum_le_sum fun t _ => mul_le_mul_right (hcost t) _

/-- Every additional nonnegative stage weakly increases finite-horizon cost. -/
theorem fep003_pragmaticCost_horizon_succ
    (discount : ENNReal) (stageCost : ℕ → ENNReal) (horizon : ℕ) :
    fep003_pragmaticCost discount stageCost horizon ≤
      fep003_pragmaticCost discount stageCost (horizon + 1) := by
  rw [fep003_pragmaticCost_succ]
  exact le_add_right (le_refl _)

end FEP003
""",
    "fep-007": """import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Algebra.BigOperators.Field
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Basic.Real.Basic

namespace FEP007

open Finset

-- [proof strategy: mul_nonneg / Finset.sum_nonneg for positivity; Finset.sum_le_sum for monotone updates]

abbrev Node := Fin 8

/-- Belief propagation: local potential products stay nonnegative when factors are. -/
theorem fep007_factorProduct_nonneg (ψ : Node → Node → ℝ) (i j : Node)
    (hψ : 0 ≤ ψ i j) (hj : 0 ≤ ψ j i) : 0 ≤ ψ i j * ψ j i := by
  exact mul_nonneg hψ hj

/-- Message aggregation: sum of factor-weighted messages stays nonneg. -/
theorem fep007_message_agg_nonneg (ψ : Node → Node → ℝ) (msg : Node → ℝ)
    (N : Finset Node) (i : Node)
    (hψ : ∀ j, 0 ≤ ψ i j) (hm : ∀ j, 0 ≤ msg j) :
    0 ≤ ∑ j ∈ N, ψ i j * msg j :=
  Finset.sum_nonneg fun j _ => mul_nonneg (hψ j) (hm j)

/-- Monotonicity: stronger messages → stronger aggregate. -/
theorem fep007_message_agg_mono (ψ : Node → Node → ℝ) (m₁ m₂ : Node → ℝ)
    (N : Finset Node) (i : Node)
    (hψ : ∀ j, 0 ≤ ψ i j) (h : ∀ j ∈ N, m₁ j ≤ m₂ j) :
    ∑ j ∈ N, ψ i j * m₁ j ≤ ∑ j ∈ N, ψ i j * m₂ j :=
  Finset.sum_le_sum fun j hj => mul_le_mul_of_nonneg_left (h j hj) (hψ j)

/-- Zero messages yield zero aggregate (absorbing behavior). -/
theorem fep007_zero_msg (ψ : Node → Node → ℝ) (N : Finset Node) (i : Node) :
    ∑ j ∈ N, ψ i j * (0 : ℝ) = 0 := by simp

/-- Positive unnormalized sum-product weight sent from neighbor `j` to node
`i`. -/
def fep007_unnormalizedMessage
    (ψ : Node → Node → ℝ) (incoming : Node → ℝ)
    (i j : Node) : ℝ :=
  ψ i j * incoming j

/-- Normalizing constant over a selected finite neighbor support. -/
def fep007_messageNormalizer
    (ψ : Node → Node → ℝ) (incoming : Node → ℝ)
    (neighbors : Finset Node) (i : Node) : ℝ :=
  ∑ j ∈ neighbors, fep007_unnormalizedMessage ψ incoming i j

/-- A normalized finite belief-propagation message, extended by zero outside
the selected support. -/
noncomputable def fep007_normalizedMessage
    (ψ : Node → Node → ℝ) (incoming : Node → ℝ)
    (neighbors : Finset Node) (i j : Node) : ℝ :=
  if j ∈ neighbors then
    fep007_unnormalizedMessage ψ incoming i j /
      fep007_messageNormalizer ψ incoming neighbors i
  else 0

/-- Strictly positive factors and incoming messages give a positive
normalizer on every nonempty support. -/
theorem fep007_messageNormalizer_pos
    (ψ : Node → Node → ℝ) (incoming : Node → ℝ)
    (neighbors : Finset Node) (i : Node)
    (hne : neighbors.Nonempty)
    (hψ : ∀ j ∈ neighbors, 0 < ψ i j)
    (hincoming : ∀ j ∈ neighbors, 0 < incoming j) :
    0 < fep007_messageNormalizer ψ incoming neighbors i := by
  exact Finset.sum_pos
    (fun j hj => mul_pos (hψ j hj) (hincoming j hj)) hne

/-- Normalized messages are nonnegative everywhere. -/
theorem fep007_normalizedMessage_nonneg
    (ψ : Node → Node → ℝ) (incoming : Node → ℝ)
    (neighbors : Finset Node) (i j : Node)
    (hne : neighbors.Nonempty)
    (hψ : ∀ k ∈ neighbors, 0 < ψ i k)
    (hincoming : ∀ k ∈ neighbors, 0 < incoming k) :
    0 ≤ fep007_normalizedMessage ψ incoming neighbors i j := by
  classical
  by_cases hj : j ∈ neighbors
  · rw [fep007_normalizedMessage, ite_eq_left hj]
    exact div_nonneg
      (mul_nonneg (hψ j hj).le (hincoming j hj).le)
      (fep007_messageNormalizer_pos
        ψ incoming neighbors i hne hψ hincoming).le
  · simp [fep007_normalizedMessage, hj]

/-- A normalized message has total mass one on its selected support. -/
theorem fep007_normalizedMessage_sum_one
    (ψ : Node → Node → ℝ) (incoming : Node → ℝ)
    (neighbors : Finset Node) (i : Node)
    (hne : neighbors.Nonempty)
    (hψ : ∀ j ∈ neighbors, 0 < ψ i j)
    (hincoming : ∀ j ∈ neighbors, 0 < incoming j) :
    ∑ j ∈ neighbors,
      fep007_normalizedMessage ψ incoming neighbors i j = 1 := by
  classical
  have hden : fep007_messageNormalizer ψ incoming neighbors i ≠ 0 :=
    ne_of_gt (fep007_messageNormalizer_pos
      ψ incoming neighbors i hne hψ hincoming)
  calc
    ∑ j ∈ neighbors,
        fep007_normalizedMessage ψ incoming neighbors i j =
        ∑ j ∈ neighbors,
          fep007_unnormalizedMessage ψ incoming i j /
            fep007_messageNormalizer ψ incoming neighbors i := by
      apply Finset.sum_congr rfl
      intro j hj
      simp [fep007_normalizedMessage, hj]
    _ = fep007_messageNormalizer ψ incoming neighbors i /
        fep007_messageNormalizer ψ incoming neighbors i := by
      rw [← Finset.sum_div]
      rfl
    _ = 1 := div_self hden

end FEP007
""",
    "fep-008": """import Mathlib.Data.Finset.Basic
import Mathlib.Data.Finset.Max
import Mathlib.Basic.Real.Basic
import Mathlib.Order.Bounds.Basic

namespace FEP008

abbrev Policy := Fin 14

/-- Discrete active inference: some policy minimizes expected free energy on a finite set. -/
theorem fep008_exists_minG (policies : Finset Policy) (hne : policies.Nonempty) (G : Policy → ℝ) :
    ∃ p ∈ policies, ∀ p' ∈ policies, G p ≤ G p' :=
  Finset.exists_min_image policies G hne

/-- Any two policy minimizers attain the same value (uniqueness of the minimum). -/
theorem fep008_min_agrees_on_value (policies : Finset Policy) (_hne : policies.Nonempty) (G : Policy → ℝ)
    (p p' : Policy) (hp : p ∈ policies) (hp' : p' ∈ policies)
    (hmin : ∀ p'' ∈ policies, G p ≤ G p'') (hmin' : ∀ p'' ∈ policies, G p' ≤ G p'') :
    G p = G p' :=
  le_antisymm (hmin p' hp') (hmin' p hp)

/-- Dual: some policy maximizes expected value on a finite nonempty set. -/
theorem fep008_exists_maxG (policies : Finset Policy) (hne : policies.Nonempty) (G : Policy → ℝ) :
    ∃ p ∈ policies, ∀ p' ∈ policies, G p' ≤ G p :=
  Finset.exists_max_image policies G hne

/-- Minimum is ≤ any evaluation in the policy set. -/
theorem fep008_min_is_lb (policies : Finset Policy) (G : Policy → ℝ)
    (p : Policy) (_hp : p ∈ policies)
    (hmin : ∀ p' ∈ policies, G p ≤ G p') :
    ∀ p' ∈ policies, G p ≤ G p' := hmin

end FEP008
""",
    "fep-021": """import Mathlib.Basic.ENNReal.Inv

namespace FEP021

open scoped ENNReal

/-- Expected free energy convention: pragmatic expected cost minus epistemic
information value, truncated at zero in the extended nonnegative reals. -/
noncomputable def fep021_expectedFreeEnergy
    (pragmaticCost epistemicValue : ENNReal) : ENNReal :=
  pragmaticCost - epistemicValue

/-- Expected free energy is nonnegative in its native codomain. -/
theorem fep021_efe_nonneg (pragmaticCost epistemicValue : ENNReal) :
    0 ≤ fep021_expectedFreeEnergy pragmaticCost epistemicValue :=
  bot_le

/-- When information value does not exceed pragmatic cost, adding it back
exactly reconstructs that cost. This fixes the epistemic sign convention. -/
theorem fep021_efe_epistemic_balance
    {pragmaticCost epistemicValue : ENNReal}
    (hvalue : epistemicValue ≤ pragmaticCost) :
    fep021_expectedFreeEnergy pragmaticCost epistemicValue + epistemicValue =
      pragmaticCost := by
  exact tsub_add_cancel_of_le hvalue

/-- Higher pragmatic cost cannot reduce EFE at fixed information value. -/
theorem fep021_efe_mono_pragmatic
    {pragmatic₁ pragmatic₂ epistemicValue : ENNReal}
    (hpragmatic : pragmatic₁ ≤ pragmatic₂) :
    fep021_expectedFreeEnergy pragmatic₁ epistemicValue ≤
      fep021_expectedFreeEnergy pragmatic₂ epistemicValue :=
  tsub_le_tsub_right hpragmatic epistemicValue

/-- Higher epistemic value cannot increase EFE at fixed pragmatic cost. -/
theorem fep021_efe_antitone_epistemic
    {pragmaticCost epistemic₁ epistemic₂ : ENNReal}
    (hepistemic : epistemic₁ ≤ epistemic₂) :
    fep021_expectedFreeEnergy pragmaticCost epistemic₂ ≤
      fep021_expectedFreeEnergy pragmaticCost epistemic₁ :=
  tsub_le_tsub_left hepistemic pragmaticCost

/-- Truncated EFE is zero exactly when information value covers pragmatic cost. -/
theorem fep021_efe_eq_zero_iff
    (pragmaticCost epistemicValue : ENNReal) :
    fep021_expectedFreeEnergy pragmaticCost epistemicValue = 0 ↔
      pragmaticCost ≤ epistemicValue := by
  exact tsub_eq_zero_iff_le

end FEP021
""",
    "fep-023": """import Mathlib.MeasureTheory.Measure.Typeclasses.Probability

namespace FEP023

open MeasureTheory

variable {Policy Outcome : Type*} [MeasurableSpace Outcome]

/-- Distributional affordance set: outcome laws induced by available policies. -/
def fep023_reachableLaws
    (policies : Set Policy) (law : Policy → Measure Outcome) :
    Set (Measure Outcome) :=
  law '' policies

/-- Every available policy induces a reachable outcome law. -/
theorem fep023_policy_reachable
    (policies : Set Policy) (law : Policy → Measure Outcome)
    {policy : Policy} (hpolicy : policy ∈ policies) :
    law policy ∈ fep023_reachableLaws policies law :=
  ⟨policy, hpolicy, rfl⟩

/-- Expanding the policy set can only enlarge the reachable-law set. -/
theorem fep023_reachable_mono
    {policies₁ policies₂ : Set Policy} (law : Policy → Measure Outcome)
    (hpolicies : policies₁ ⊆ policies₂) :
    fep023_reachableLaws policies₁ law ⊆
      fep023_reachableLaws policies₂ law := by
  rintro _ ⟨policy, hpolicy, rfl⟩
  exact ⟨policy, hpolicies hpolicy, rfl⟩

/-- If each policy law is normalized, every reachable law is normalized. -/
theorem fep023_reachable_normalized
    (policies : Set Policy) (law : Policy → Measure Outcome)
    (hlaw : ∀ policy ∈ policies, law policy Set.univ = 1)
    {μ : Measure Outcome} (hμ : μ ∈ fep023_reachableLaws policies law) :
    μ Set.univ = 1 := by
  rcases hμ with ⟨policy, hpolicy, rfl⟩
  exact hlaw policy hpolicy

/-- No policy means no reachable law. -/
theorem fep023_reachable_empty (law : Policy → Measure Outcome) :
    fep023_reachableLaws (∅ : Set Policy) law = ∅ := by
  simp [fep023_reachableLaws]

end FEP023
""",
    "fep-028": """import Mathlib.Data.Finset.Basic
import Mathlib.Analysis.SpecialFunctions.Exp

namespace FEP028

open Real Finset

-- [proof strategy: Real.exp_pos + Finset.sum_pos + div identities for softmax normalization]

abbrev Policy := Fin 10

noncomputable def fep028_softmax (γ : ℝ) (G : Policy → ℝ) (policies : Finset Policy) (p : Policy) :
    ℝ :=
  if p ∈ policies then
    Real.exp (-γ * G p) / ∑ p' ∈ policies, Real.exp (-γ * G p')
  else 0

/-- Softmax probabilities are nonneg over nonempty policy sets. -/
theorem fep028_softmax_nonneg (γ : ℝ) (G : Policy → ℝ) (policies : Finset Policy) (p : Policy)
    (hne : policies.Nonempty) : 0 ≤ fep028_softmax γ G policies p := by
  classical
  have hsum : 0 < ∑ p' ∈ policies, Real.exp (-γ * G p') :=
    Finset.sum_pos (fun _ _ => Real.exp_pos _) hne
  by_cases hp : p ∈ policies
  · rw [fep028_softmax, ite_eq_left hp]
    exact div_nonneg (Real.exp_nonneg _) hsum.le
  · simp [fep028_softmax, hp]

/-- Every support-aware softmax weight is at most one. -/
theorem fep028_softmax_le_one
    (γ : ℝ) (G : Policy → ℝ) (policies : Finset Policy) (p : Policy)
    (hne : policies.Nonempty) :
    fep028_softmax γ G policies p ≤ 1 := by
  classical
  have hsum : 0 < ∑ p' ∈ policies, Real.exp (-γ * G p') :=
    Finset.sum_pos (fun _ _ => Real.exp_pos _) hne
  by_cases hp : p ∈ policies
  · rw [fep028_softmax, ite_eq_left hp]
    apply (div_le_one hsum).2
    exact Finset.single_le_sum
      (fun q _ => Real.exp_nonneg (-γ * G q)) hp
  · simp [fep028_softmax, hp]

/-- Softmax probabilities over a nonempty finite policy set sum to one. -/
theorem fep028_softmax_probs_sum_one (γ : ℝ) (G : Policy → ℝ) (policies : Finset Policy)
    (hne : policies.Nonempty) :
    ∑ p ∈ policies, fep028_softmax γ G policies p = 1 := by
  classical
  have hden :
      (∑ p' ∈ policies, Real.exp (-γ * G p')) ≠ 0 :=
    ne_of_gt (Finset.sum_pos (fun _ _ => Real.exp_pos _) hne)
  calc
    ∑ p ∈ policies, fep028_softmax γ G policies p =
        ∑ p ∈ policies,
          Real.exp (-γ * G p) /
            ∑ p' ∈ policies, Real.exp (-γ * G p') := by
      apply Finset.sum_congr rfl
      intro p hp
      simp [fep028_softmax, hp]
    _ = 1 := by
      simp_rw [div_eq_mul_inv]
      rw [← Finset.sum_mul, mul_inv_cancel₀ hden]

/-- Policies outside the declared support receive exactly zero probability. -/
theorem fep028_softmax_support
    (γ : ℝ) (G : Policy → ℝ) (policies : Finset Policy) {p : Policy}
    (hp : p ∉ policies) :
    fep028_softmax γ G policies p = 0 := by
  simp [fep028_softmax, hp]

/-- The support-aware softmax is a normalized weight vector on the complete
finite policy type. -/
theorem fep028_softmax_sum_univ
    (γ : ℝ) (G : Policy → ℝ) (policies : Finset Policy)
    (hne : policies.Nonempty) :
    ∑ p : Policy, fep028_softmax γ G policies p = 1 := by
  classical
  have hsubset :
      (∑ p ∈ policies, fep028_softmax γ G policies p) =
        ∑ p : Policy, fep028_softmax γ G policies p := by
    apply Finset.sum_subset (Finset.subset_univ policies)
    intro p _ hp
    exact fep028_softmax_support γ G policies hp
  rw [← hsubset]
  exact fep028_softmax_probs_sum_one γ G policies hne

/-- Softmax numerator is strictly positive. -/
theorem fep028_numerator_pos (γ : ℝ) (G : Policy → ℝ) (p : Policy) :
    0 < Real.exp (-γ * G p) :=
  Real.exp_pos _

/-- Softmax denominator is strictly positive over a nonempty set. -/
theorem fep028_denominator_pos (γ : ℝ) (G : Policy → ℝ) (policies : Finset Policy)
    (hne : policies.Nonempty) :
    0 < ∑ p' ∈ policies, Real.exp (-γ * G p') :=
  Finset.sum_pos (fun _ _ => Real.exp_pos _) hne

end FEP028
""",
    "fep-033": """import Mathlib.Basic.ENNReal.Inv

namespace FEP033

open scoped ENNReal

/-- Transition-aware finite-horizon value with stage cost, discount, and
terminal cost. -/
noncomputable def fep033_value {State : Type*}
    (discount : ENNReal) (stageCost : State → ENNReal)
    (step : State → State) (terminalCost : State → ENNReal) :
    ℕ → State → ENNReal
  | 0, state => terminalCost state
  | horizon + 1, state =>
      stageCost state +
        discount * fep033_value discount stageCost step terminalCost horizon (step state)

/-- Bellman recursion is the defining finite-horizon transition law. -/
theorem fep033_bellman {State : Type*}
    (discount : ENNReal) (stageCost : State → ENNReal)
    (step : State → State) (terminalCost : State → ENNReal)
    (horizon : ℕ) (state : State) :
    fep033_value discount stageCost step terminalCost (horizon + 1) state =
      stageCost state + discount *
        fep033_value discount stageCost step terminalCost horizon (step state) :=
  rfl

/-- Pointwise larger stage and terminal costs produce a larger value. -/
theorem fep033_value_mono {State : Type*}
    (discount : ENNReal) {stage₁ stage₂ terminal₁ terminal₂ : State → ENNReal}
    (step : State → State) (hstage : ∀ state, stage₁ state ≤ stage₂ state)
    (hterminal : ∀ state, terminal₁ state ≤ terminal₂ state)
    (horizon : ℕ) (state : State) :
    fep033_value discount stage₁ step terminal₁ horizon state ≤
      fep033_value discount stage₂ step terminal₂ horizon state := by
  induction horizon generalizing state with
  | zero => exact hterminal state
  | succ horizon ih =>
      exact add_le_add (hstage state)
        (mul_le_mul_right (ih (step state)) discount)

/-- Zero stage and terminal costs yield zero value at every horizon. -/
theorem fep033_zeroCost {State : Type*}
    (discount : ENNReal) (step : State → State) (horizon : ℕ) (state : State) :
    fep033_value discount (fun _ => 0) step (fun _ => 0) horizon state = 0 := by
  induction horizon generalizing state with
  | zero => rfl
  | succ horizon ih => simp [fep033_value, ih]

/-- At zero discount, every positive-horizon value is exactly immediate cost. -/
theorem fep033_zeroDiscount {State : Type*}
    (stageCost : State → ENNReal) (step : State → State)
    (terminalCost : State → ENNReal) (horizon : ℕ) (state : State) :
    fep033_value 0 stageCost step terminalCost (horizon + 1) state =
      stageCost state := by
  simp [fep033_value]

end FEP033
""",
    "fep-034": """import Mathlib.Probability.Kernel.Posterior

namespace FEP034

open MeasureTheory ProbabilityTheory
open scoped ENNReal ProbabilityTheory

variable {Ω 𝓧 : Type*} [MeasurableSpace Ω] [MeasurableSpace 𝓧]

/-- The one-step predictive prior obtained by composing a transition kernel
with the previous latent-state law. -/
noncomputable def fep034_predictivePrior
    (τ : Kernel Ω Ω) (μ : Measure Ω) : Measure Ω :=
  τ ∘ₘ μ

/-- A Markov transition preserves total prior mass. -/
theorem fep034_predictive_mass
    (τ : Kernel Ω Ω) (μ : Measure Ω) [IsMarkovKernel τ] :
    fep034_predictivePrior τ μ Set.univ = μ Set.univ := by
  exact Measure.comp_apply_univ

/-- The normalized filtering kernel is the posterior of the observation
kernel with respect to the transition-predicted prior. -/
noncomputable def fep034_filter
    (τ : Kernel Ω Ω) (κ : Kernel Ω 𝓧) (μ : Measure Ω)
    [StandardBorelSpace Ω] [Nonempty Ω]
    [IsFiniteMeasure μ] [IsFiniteKernel τ] [IsFiniteKernel κ] : Kernel 𝓧 Ω :=
  ProbabilityTheory.posterior κ (τ ∘ₘ μ)

/-- Every observation-indexed filtering posterior has total mass one. -/
theorem fep034_filter_mass_one
    (τ : Kernel Ω Ω) (κ : Kernel Ω 𝓧) (μ : Measure Ω)
    [StandardBorelSpace Ω] [Nonempty Ω]
    [IsFiniteMeasure μ] [IsFiniteKernel τ] [IsFiniteKernel κ] (x : 𝓧) :
    fep034_filter τ κ μ x Set.univ = 1 := by
  change (ProbabilityTheory.posterior κ (τ ∘ₘ μ) x) Set.univ = 1
  exact measure_univ

/-- The predictive observation law and filtering posterior reconstruct the
swapped predicted-state/observation joint law. -/
theorem fep034_filter_joint_reconstruction
    (τ : Kernel Ω Ω) (κ : Kernel Ω 𝓧) (μ : Measure Ω)
    [StandardBorelSpace Ω] [Nonempty Ω]
    [IsFiniteMeasure μ] [IsFiniteKernel τ] [IsFiniteKernel κ] :
    (κ ∘ₘ fep034_predictivePrior τ μ) ⊗ₘ fep034_filter τ κ μ =
      (fep034_predictivePrior τ μ ⊗ₘ κ).map Prod.swap := by
  change
    (κ ∘ₘ (τ ∘ₘ μ)) ⊗ₘ ProbabilityTheory.posterior κ (τ ∘ₘ μ) =
      ((τ ∘ₘ μ) ⊗ₘ κ).map Prod.swap
  exact ProbabilityTheory.compProd_posterior_eq_map_swap

/-- With a Markov observation kernel, conditioning after prediction recovers
the transition-predicted prior. -/
theorem fep034_filter_recovers_prediction
    (τ : Kernel Ω Ω) (κ : Kernel Ω 𝓧) (μ : Measure Ω)
    [StandardBorelSpace Ω] [Nonempty Ω]
    [IsFiniteMeasure μ] [IsFiniteKernel τ] [IsMarkovKernel κ] :
    fep034_filter τ κ μ ∘ₘ κ ∘ₘ fep034_predictivePrior τ μ =
      fep034_predictivePrior τ μ := by
  change
    ProbabilityTheory.posterior κ (τ ∘ₘ μ) ∘ₘ κ ∘ₘ (τ ∘ₘ μ) =
      τ ∘ₘ μ
  exact ProbabilityTheory.posterior_comp_self

end FEP034
""",
    "fep-041": """import Mathlib.InformationTheory.KullbackLeibler.Basic
import Mathlib.MeasureTheory.Integral.Lebesgue.Countable

namespace FEP041

open MeasureTheory
open scoped ENNReal

variable {Obs State : Type*}
variable [MeasurableSpace Obs] [MeasurableSpace State]

/-- Information gain is Mathlib's measure-valued Kullback--Leibler divergence
from a posterior law to its prior law. -/
noncomputable def fep041_informationGain
    (posterior prior : Measure State) : ℝ≥0∞ :=
  InformationTheory.klDiv posterior prior

/-- Information gain is nonnegative because KL divergence is extended
nonnegative-real valued. -/
theorem fep041_informationGain_nonneg (posterior prior : Measure State) :
    0 ≤ fep041_informationGain posterior prior :=
  bot_le

/-- For finite measures, zero information gain characterizes equality of the
posterior and prior laws. -/
theorem fep041_informationGain_eq_zero_iff
    (posterior prior : Measure State)
    [IsFiniteMeasure posterior] [IsFiniteMeasure prior] :
    fep041_informationGain posterior prior = 0 ↔ posterior = prior := by
  exact InformationTheory.klDiv_eq_zero_iff

/-- Expected information gain under a predictive observation law. -/
noncomputable def fep041_expectedInformationGain
    (predictive : Measure Obs)
    (posterior : Obs → Measure State)
    (prior : Measure State) : ℝ≥0∞ :=
  ∫⁻ observation,
    fep041_informationGain (posterior observation) prior ∂predictive

/-- If observations leave the posterior equal to the prior almost everywhere,
then expected information gain is exactly zero. -/
theorem fep041_expectedInformationGain_zero
    (predictive : Measure Obs)
    (posterior : Obs → Measure State)
    (prior : Measure State) [SigmaFinite prior]
    (hposterior : ∀ᵐ observation ∂predictive, posterior observation = prior) :
    fep041_expectedInformationGain predictive posterior prior = 0 := by
  rw [fep041_expectedInformationGain]
  calc
    (∫⁻ observation,
        fep041_informationGain (posterior observation) prior ∂predictive) =
        ∫⁻ _observation, 0 ∂predictive := by
          apply lintegral_congr_ae
          filter_upwards [hposterior] with observation hobservation
          simp [fep041_informationGain, hobservation,
            InformationTheory.klDiv_self]
    _ = 0 := lintegral_zero

end FEP041
""",
    "fep-047": """import Mathlib.Data.Matrix.Mul
import Mathlib.Basic.Real.Basic

namespace FEP047

open Finset

abbrev State := Fin 7
abbrev Factor := Matrix State State ℝ

/-- A full finite sum-product forward pass is matrix--vector multiplication. -/
def fep047_forward (factor : Factor) (incoming : State → ℝ) : State → ℝ :=
  Matrix.mulVec factor incoming

/-- Forward message is nonneg when factors and incoming messages are nonneg. -/
theorem fep047_forward_nonneg
    (factor : Factor) (incoming : State → ℝ)
    (hfactor : ∀ x y, 0 ≤ factor x y)
    (hincoming : ∀ y, 0 ≤ incoming y) (x : State) :
    0 ≤ fep047_forward factor incoming x := by
  simp only [fep047_forward, Matrix.mulVec, dotProduct]
  exact Finset.sum_nonneg fun y _ =>
    mul_nonneg (hfactor x y) (hincoming y)

/-- Message-passing monotonicity: larger incoming messages → larger output. -/
theorem fep047_forward_mono
    (factor : Factor) (incoming₁ incoming₂ : State → ℝ)
    (hfactor : ∀ x y, 0 ≤ factor x y)
    (hincoming : ∀ y, incoming₁ y ≤ incoming₂ y) (x : State) :
    fep047_forward factor incoming₁ x ≤
      fep047_forward factor incoming₂ x := by
  simp only [fep047_forward, Matrix.mulVec, dotProduct]
  exact Finset.sum_le_sum fun y _ =>
    mul_le_mul_of_nonneg_left (hincoming y) (hfactor x y)

/-- Zero incoming messages → zero forward output. -/
theorem fep047_zero_in (factor : Factor) :
    fep047_forward factor (fun _ => 0) = 0 := by
  ext x
  change (∑ y : State, factor x y * 0) = (0 : ℝ)
  simp

/-- Identity factor leaves every incoming message unchanged. -/
theorem fep047_identity (incoming : State → ℝ) :
    fep047_forward (1 : Factor) incoming = incoming := by
  exact Matrix.one_mulVec incoming

/-- Two consecutive sum-product passes are exactly one pass through the
matrix product of their factors. -/
theorem fep047_forward_compose
    (outer inner : Factor) (incoming : State → ℝ) :
    fep047_forward outer (fep047_forward inner incoming) =
      fep047_forward (outer * inner) incoming := by
  exact Matrix.mulVec_mulVec incoming outer inner

end FEP047
""",
}
