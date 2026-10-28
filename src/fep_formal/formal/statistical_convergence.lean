module
public import Mathlib.Probability.StrongLaw

@[expose] public section

/-!
# Statistical convergence for empirical finite laws

This module instantiates Mathlib's almost-sure real strong law for Boolean
and finite-valued observations. Pairwise independence, identical distribution,
and integrability are all explicit theorem premises. Topic-specific bridges,
including Laplace smoothing from fep-036, live in the composed module.
-/

namespace FEP.StatisticalConvergence

open Filter MeasureTheory ProbabilityTheory Finset
open scoped BigOperators MeasureTheory ProbabilityTheory

variable {Ω : Type*}

/-- Real indicator associated with a Boolean observation process. -/
def indicator (observations : ℕ → Ω → Bool) (index : ℕ) (ω : Ω) : ℝ :=
  if observations index ω then 1 else 0

/-- Number of successful Boolean observations before time `n`. -/
def successCount (observations : ℕ → Ω → Bool) (n : ℕ) (ω : Ω) : ℕ :=
  ∑ index ∈ Finset.range n, if observations index ω then 1 else 0

/-- Raw empirical success frequency, totalized to zero at `n=0`. -/
noncomputable def empiricalRate
    (observations : ℕ → Ω → Bool) (n : ℕ) (ω : Ω) : ℝ :=
  (successCount observations n ω : ℝ) / n

/-- The real indicator sum is the cast of the natural success count. -/
lemma sum_indicator_eq_successCount
    (observations : ℕ → Ω → Bool) (n : ℕ) (ω : Ω) :
    ∑ index ∈ Finset.range n, indicator observations index ω =
      (successCount observations n ω : ℝ) := by
  simp only [indicator, successCount, Nat.cast_sum]
  apply Finset.sum_congr rfl
  intro index _
  split <;> norm_num

/-- Almost-sure convergence of the empirical Boolean frequency under the
native strong-law hypotheses. -/
theorem empiricalRate_strongLaw
    [MeasurableSpace Ω] (μ : Measure Ω) (observations : ℕ → Ω → Bool)
    (hint : Integrable (indicator observations 0) μ)
    (hindep : Pairwise (fun i j =>
      indicator observations i ⟂ᵢ[μ] indicator observations j))
    (hident : ∀ index,
      IdentDistrib (indicator observations index)
        (indicator observations 0) μ μ) :
    ∀ᵐ ω ∂μ,
      Tendsto (fun n => empiricalRate observations n ω)
        atTop (nhds μ[indicator observations 0]) := by
  filter_upwards [strong_law_ae_real
    (indicator observations) hint hindep hident] with ω hω
  have hfunctions :
      (fun n => empiricalRate observations n ω) =
        (fun n =>
          (∑ index ∈ Finset.range n, indicator observations index ω) / n) := by
    funext n
    rw [empiricalRate, sum_indicator_eq_successCount]
  rw [hfunctions]
  exact hω

/-- Real indicator for one atom of a finite-valued process. -/
def atomIndicator {α : Type*} [DecidableEq α]
    (observations : ℕ → Ω → α) (atom : α) (index : ℕ) (ω : Ω) : ℝ :=
  if observations index ω = atom then 1 else 0

/-- Pointwise empirical mass for one atom of a finite-valued process. -/
noncomputable def empiricalMass {α : Type*} [DecidableEq α]
    (observations : ℕ → Ω → α) (atom : α) (n : ℕ) (ω : Ω) : ℝ :=
  (∑ index ∈ Finset.range n, atomIndicator observations atom index ω) / n

/-- Every finite atom frequency obeys the strong law when its indicator
process satisfies the explicit native hypotheses. -/
theorem empiricalMass_strongLaw {α : Type*} [DecidableEq α]
    [MeasurableSpace Ω] (μ : Measure Ω)
    (observations : ℕ → Ω → α) (atom : α)
    (hint : Integrable (atomIndicator observations atom 0) μ)
    (hindep : Pairwise (fun i j =>
      atomIndicator observations atom i ⟂ᵢ[μ]
        atomIndicator observations atom j))
    (hident : ∀ index,
      IdentDistrib (atomIndicator observations atom index)
        (atomIndicator observations atom 0) μ μ) :
    ∀ᵐ ω ∂μ,
      Tendsto (fun n => empiricalMass observations atom n ω)
        atTop (nhds μ[atomIndicator observations atom 0]) := by
  exact strong_law_ae_real
    (atomIndicator observations atom) hint hindep hident

/-- All atom frequencies of a finite-valued process converge simultaneously
outside one null set.  The theorem exposes the per-atom strong-law hypotheses
rather than silently assuming i.i.d. observations. -/
theorem empiricalLaw_strongLaw {α : Type*} [Fintype α] [DecidableEq α]
    [MeasurableSpace Ω] (μ : Measure Ω) (observations : ℕ → Ω → α)
    (hint : ∀ atom,
      Integrable (atomIndicator observations atom 0) μ)
    (hindep : ∀ atom, Pairwise (fun i j =>
      atomIndicator observations atom i ⟂ᵢ[μ]
        atomIndicator observations atom j))
    (hident : ∀ atom index,
      IdentDistrib (atomIndicator observations atom index)
        (atomIndicator observations atom 0) μ μ) :
    ∀ᵐ ω ∂μ, ∀ atom,
      Tendsto (fun n => empiricalMass observations atom n ω)
        atTop (nhds μ[atomIndicator observations atom 0]) := by
  exact Filter.eventually_all.2 fun atom =>
    empiricalMass_strongLaw μ observations atom
      (hint atom) (hindep atom) (hident atom)

/-- Pointwise `L¹` error of the empirical atom masses against their expected
indicator values. -/
noncomputable def empiricalL1Error {α : Type*} [Fintype α] [DecidableEq α]
    [MeasurableSpace Ω] (μ : Measure Ω) (observations : ℕ → Ω → α)
    (n : ℕ) (ω : Ω) : ℝ :=
  ∑ atom,
    |empiricalMass observations atom n ω -
      μ[atomIndicator observations atom 0]|

/-- Simultaneous atomwise strong laws imply almost-sure convergence of the
entire finite empirical law in `L¹`. -/
theorem empiricalL1Error_strongLaw
    {α : Type*} [Fintype α] [DecidableEq α]
    [MeasurableSpace Ω] (μ : Measure Ω) (observations : ℕ → Ω → α)
    (hint : ∀ atom,
      Integrable (atomIndicator observations atom 0) μ)
    (hindep : ∀ atom, Pairwise (fun i j =>
      atomIndicator observations atom i ⟂ᵢ[μ]
        atomIndicator observations atom j))
    (hident : ∀ atom index,
      IdentDistrib (atomIndicator observations atom index)
        (atomIndicator observations atom 0) μ μ) :
    ∀ᵐ ω ∂μ,
      Tendsto (fun n => empiricalL1Error μ observations n ω)
        atTop (nhds 0) := by
  filter_upwards [empiricalLaw_strongLaw μ observations hint hindep hident]
    with ω hω
  unfold empiricalL1Error
  have hsum :
      Tendsto
        (fun n => ∑ atom,
          |empiricalMass observations atom n ω -
            μ[atomIndicator observations atom 0]|)
        atTop (nhds (∑ _atom : α, (0 : ℝ))) := by
    apply tendsto_finsetSum Finset.univ
    intro atom _
    simpa using
      ((hω atom).sub_const μ[atomIndicator observations atom 0]).abs
  simpa using hsum

/-- Empirical expectation of an arbitrary real observable on a finite state
space. -/
noncomputable def empiricalExpectation
    {α : Type*} [Fintype α] [DecidableEq α]
    (observations : ℕ → Ω → α) (observable : α → ℝ)
    (n : ℕ) (ω : Ω) : ℝ :=
  ∑ atom, empiricalMass observations atom n ω * observable atom

/-- Population expectation represented by the expected atom indicators. -/
noncomputable def populationExpectation
    {α : Type*} [Fintype α] [DecidableEq α]
    [MeasurableSpace Ω] (μ : Measure Ω) (observations : ℕ → Ω → α)
    (observable : α → ℝ) : ℝ :=
  ∑ atom, μ[atomIndicator observations atom 0] * observable atom

/-- The finite empirical law integrates every real observable consistently on
the same almost-sure event as the simultaneous atomwise strong law. -/
theorem empiricalExpectation_strongLaw
    {α : Type*} [Fintype α] [DecidableEq α]
    [MeasurableSpace Ω] (μ : Measure Ω) (observations : ℕ → Ω → α)
    (observable : α → ℝ)
    (hint : ∀ atom,
      Integrable (atomIndicator observations atom 0) μ)
    (hindep : ∀ atom, Pairwise (fun i j =>
      atomIndicator observations atom i ⟂ᵢ[μ]
        atomIndicator observations atom j))
    (hident : ∀ atom index,
      IdentDistrib (atomIndicator observations atom index)
        (atomIndicator observations atom 0) μ μ) :
    ∀ᵐ ω ∂μ,
      Tendsto (fun n => empiricalExpectation observations observable n ω)
        atTop (nhds (populationExpectation μ observations observable)) := by
  filter_upwards [empiricalLaw_strongLaw μ observations hint hindep hident]
    with ω hω
  unfold empiricalExpectation populationExpectation
  apply tendsto_finsetSum Finset.univ
  intro atom _
  exact (hω atom).mul_const (observable atom)

/-- Consequently, the absolute empirical expectation error converges almost
surely to zero for every finite real observable. -/
theorem empiricalExpectationError_strongLaw
    {α : Type*} [Fintype α] [DecidableEq α]
    [MeasurableSpace Ω] (μ : Measure Ω) (observations : ℕ → Ω → α)
    (observable : α → ℝ)
    (hint : ∀ atom,
      Integrable (atomIndicator observations atom 0) μ)
    (hindep : ∀ atom, Pairwise (fun i j =>
      atomIndicator observations atom i ⟂ᵢ[μ]
        atomIndicator observations atom j))
    (hident : ∀ atom index,
      IdentDistrib (atomIndicator observations atom index)
        (atomIndicator observations atom 0) μ μ) :
    ∀ᵐ ω ∂μ,
      Tendsto
        (fun n =>
          |empiricalExpectation observations observable n ω -
            populationExpectation μ observations observable|)
        atTop (nhds 0) := by
  filter_upwards [empiricalExpectation_strongLaw
    μ observations observable hint hindep hident] with ω hω
  simpa using
    (hω.sub_const (populationExpectation μ observations observable)).abs

end FEP.StatisticalConvergence
