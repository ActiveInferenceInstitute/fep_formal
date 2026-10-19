module
public import FepSketches.families.core_active_inference
public import FepSketches.families.core_bayesian_mechanics
public import FepSketches.families.core_free_energy
public import FepSketches.families.core_information_geometry
public import FepSketches.families.core_thermodynamics
public import FepSketches.families.geometric_optimization
public import FepSketches.active_inference
public import FepSketches.information_geometry
public import FepSketches.markov_blanket
public import FepSketches.statistical_convergence
public import FepSketches.controlled_markov
public import FepSketches.temporal_inference
public import FepSketches.path_thermodynamics
public import FepSketches.geometric_optimization
public import Mathlib.Analysis.SpecialFunctions.BinaryEntropy

@[expose] public section

namespace FEPComposed

open FEP.StatisticalConvergence Filter MeasureTheory ProbabilityTheory
open scoped ENNReal

variable {Ω : Type*}

/-- Topic bridge: fep-036's Laplace smoothing preserves the almost-sure
Boolean strong-law limit supplied by the topic-independent foundation. -/
theorem fep036_smoothedRate_strongLaw
    [MeasurableSpace Ω] (μ : Measure Ω) (observations : ℕ → Ω → Bool)
    (hint : Integrable (indicator observations 0) μ)
    (hindep : Pairwise (fun i j =>
      indicator observations i ⟂ᵢ[μ] indicator observations j))
    (hident : ∀ index,
      IdentDistrib (indicator observations index)
        (indicator observations 0) μ μ) :
    ∀ᵐ ω ∂μ,
      Tendsto
        (fun n =>
          fep_fep036.FEP036.fep036_smoothedRate
            (successCount observations n ω) n)
        atTop (nhds μ[indicator observations 0]) := by
  filter_upwards [empiricalRate_strongLaw μ observations hint hindep hident]
    with ω hraw
  exact fep_fep036.FEP036.fep036_smoothedRate_tendsto_of_empiricalRate
    (fun n => successCount observations n ω)
    μ[indicator observations 0] hraw

/-- The real finite-model EFE convention maps exactly to fep-021's truncated
ENNReal convention under `ofReal`; negative real EFE values are therefore
explicitly truncated rather than silently identified with a real quantity. -/
theorem activeInference_expectedFreeEnergy_to_fep021
    {Policy State Outcome : Type*}
    [Fintype Policy] [Fintype State] [Fintype Outcome]
    (model : FEP.ActiveInference.GenerativeModel Policy State Outcome)
    (policy : Policy) :
    ENNReal.ofReal (FEP.ActiveInference.expectedFreeEnergy model policy) =
      fep_fep021.FEP021.fep021_expectedFreeEnergy
        (ENNReal.ofReal (FEP.ActiveInference.pragmaticCost model policy))
        (ENNReal.ofReal (FEP.ActiveInference.epistemicValue model policy)) := by
  simpa [FEP.ActiveInference.expectedFreeEnergy,
    fep_fep021.FEP021.fep021_expectedFreeEnergy] using
    ENNReal.ofReal_sub (FEP.ActiveInference.pragmaticCost model policy)
      (FEP.ActiveInference.epistemicValue_nonneg model policy)

/-- The fep-002 variational-free-energy definition composes with fep-014's
native KL chain rule on measure-kernel composition products. -/
theorem fep002_vfe_compProd_chain_rule
    {α β : Type*} [MeasurableSpace α] [MeasurableSpace β]
    (μ ν : Measure α) (κ η : Kernel α β)
    [IsFiniteMeasure μ] [IsFiniteMeasure ν]
    [IsMarkovKernel κ] [IsMarkovKernel η]
    (surprisal : ENNReal) :
    fep_fep002.FEP002.fep002_variationalFreeEnergy
        (μ ⊗ₘ κ) (ν ⊗ₘ η) surprisal =
      surprisal +
        (InformationTheory.klDiv μ ν +
          InformationTheory.klDiv (μ ⊗ₘ κ) (μ ⊗ₘ η)) := by
  rw [fep_fep002.FEP002.fep002_variationalFreeEnergy]
  rw [fep_fep014.FEP014.fep014_kl_chain_rule]

/-- The normalized fep-034 transition-observation filter is exactly fep-017's
native posterior kernel applied to the transition-predicted prior. -/
theorem fep034_filter_is_fep017_posterior
    {Ω 𝓧 : Type*} [MeasurableSpace Ω] [MeasurableSpace 𝓧]
    (τ : Kernel Ω Ω) (κ : Kernel Ω 𝓧) (μ : Measure Ω)
    [StandardBorelSpace Ω] [Nonempty Ω]
    [IsFiniteMeasure μ] [IsFiniteKernel τ] [IsFiniteKernel κ] :
    fep_fep034.FEP034.fep034_filter τ κ μ =
      fep_fep017.FEP017.fep017_posterior κ
        (τ ∘ₘ μ) := by
  rfl

/-- The child marginal of fep-027's hierarchical joint is exactly fep-019's
native prior-predictive law. -/
theorem fep027_priorPredictive_is_fep019
    {α β : Type*} [MeasurableSpace α] [MeasurableSpace β]
    (μ : Measure α) (κ : Kernel α β) [SFinite μ] [IsSFiniteKernel κ] :
    (fep_fep027.FEP027.fep027_hierarchicalJoint μ κ).snd =
      fep_fep019.FEP019.fep019_priorPredictive κ μ := by
  exact fep_fep027.FEP027.fep027_hierarchical_snd μ κ

/-- A posterior-predictive kernel is the child kernel of a hierarchical joint;
its child marginal equals sequential posterior-then-likelihood prediction. -/
theorem fep022_predictive_is_hierarchical_marginal
    {𝓒 Ω 𝓧 : Type*}
    [MeasurableSpace 𝓒] [MeasurableSpace Ω] [MeasurableSpace 𝓧]
    (ν : Measure 𝓒) (posterior : Kernel 𝓒 Ω) (likelihood : Kernel Ω 𝓧)
    [SFinite ν] [IsSFiniteKernel posterior] [IsSFiniteKernel likelihood] :
    (fep_fep027.FEP027.fep027_hierarchicalJoint ν
      (fep_fep022.FEP022.fep022_posteriorPredictive posterior likelihood)).snd =
        likelihood ∘ₘ (posterior ∘ₘ ν) := by
  change (ν ⊗ₘ (likelihood ∘ₖ posterior)).snd =
    likelihood ∘ₘ (posterior ∘ₘ ν)
  rw [Measure.snd_compProd]
  exact Measure.comp_assoc.symm

/-- Laplace-smoothed cohort counts from fep-036 define an interior Bernoulli
prior, and fep-045's normalized binary-evidence update remains in the same
Bernoulli family. -/
theorem fep036_empiricalPosterior_closed
    (data : List Bool) {l₀ l₁ : ℝ} (hl₀ : 0 < l₀) (hl₁ : 0 < l₁) (b : Bool) :
    fep_fep045.FEP045.fep045_bernoulliMass
        (fep_fep045.FEP045.fep045_posteriorParameter
          (fep_fep036.FEP036.fep036_smoothedRate
            (fep_fep042.FEP042.fep042_successCount data) data.length)
          l₀ l₁) b =
      fep_fep045.FEP045.fep045_bernoulliMass
          (fep_fep036.FEP036.fep036_smoothedRate
            (fep_fep042.FEP042.fep042_successCount data) data.length) b *
        fep_fep045.FEP045.fep045_binaryLikelihood l₀ l₁ b /
          fep_fep045.FEP045.fep045_evidence
            (fep_fep036.FEP036.fep036_smoothedRate
              (fep_fep042.FEP042.fep042_successCount data) data.length)
            l₀ l₁ := by
  have hcount :
      fep_fep042.FEP042.fep042_successCount data ≤ data.length := by
    simpa [fep_fep042.FEP042.fep042_successCount] using
      (List.count_le_length (l := data) (a := true))
  have hp₀ :
      0 < fep_fep036.FEP036.fep036_smoothedRate
        (fep_fep042.FEP042.fep042_successCount data) data.length :=
    fep_fep036.FEP036.fep036_smoothedRate_pos _ _
  have hp₁ :
      fep_fep036.FEP036.fep036_smoothedRate
        (fep_fep042.FEP042.fep042_successCount data) data.length < 1 :=
    fep_fep036.FEP036.fep036_smoothedRate_lt_one hcount
  apply fep_fep045.FEP045.fep045_bernoulli_posterior_closed
  exact ne_of_gt
    (fep_fep045.FEP045.fep045_evidence_pos hp₀ hp₁ hl₀ hl₁)

/-- The closed-form fep-018 Fisher--Rao distance and fep-038 Fisher metric
jointly supply separation of Bernoulli laws and positive tangent norm. -/
theorem fep038_fisherRao_separation
    {p q v : ℝ} (hp : p ∈ Set.Ioo (0 : ℝ) 1)
    (hq : q ∈ Set.Icc (0 : ℝ) 1) (hv : v ≠ 0) :
    (fep_fep018.FEP018.fep018_fisherRaoDistance p q = 0 ↔ p = q) ∧
      0 < fep_fep038.FEP038.fep038_fisherMetric p v v := by
  constructor
  · exact fep_fep018.FEP018.fep018_fisherRaoDistance_eq_zero_iff
      ⟨hp.1.le, hp.2.le⟩ hq
  · exact fep_fep038.FEP038.fep038_fisherMetric_pos hp.1 hp.2 hv

/-- fep-041's information gain is exactly the native KL quantity whose
finite-measure separation law is exposed by fep-014. -/
theorem fep041_informationGain_is_fep014_kl
    {State : Type*} [MeasurableSpace State]
    (posterior prior : Measure State)
    [IsFiniteMeasure posterior] [IsFiniteMeasure prior] :
    fep_fep041.FEP041.fep041_informationGain posterior prior =
        InformationTheory.klDiv posterior prior ∧
      (fep_fep041.FEP041.fep041_informationGain posterior prior = 0 ↔
        posterior = prior) := by
  constructor
  · rfl
  · exact fep_fep014.FEP014.fep014_kl_eq_zero_iff posterior prior

/-- Every finite probability-current field from fep-025 dissipates
nonnegative entropy under fep-049's nonnegative diagonal resistance law. -/
theorem fep025_current_dissipation_nonneg
    {n : ℕ} (flow : Matrix (Fin n) (Fin n) ℝ)
    (resistance : Fin n × Fin n → ℝ)
    (hresistance : ∀ edge, 0 ≤ resistance edge) :
    0 ≤ fep_fep049.FEP049.fep049_entropyProduction resistance
      (fun edge =>
        fep_fep025.FEP025.fep025_probabilityCurrent flow edge.1 edge.2) := by
  exact fep_fep049.FEP049.fep049_entropyProduction_nonneg _ _ hresistance

/-- fep-037's unit-variance autocorrelation is exactly twice the deviation
from the stationary mass in fep-020's two-state Markov evolution. -/
theorem fep037_autocorrelation_tracks_fep020 (α : ℝ) (n : ℕ) :
    2 * (((fep_fep020.FEP020.fep020_evolve α)^[n]) 1 - 1 / 2) =
      fep_fep037.FEP037.fep037_autocorrelation α 1 n := by
  rw [fep_fep020.FEP020.fep020_iterate_deviation]
  simp only [fep_fep037.FEP037.fep037_autocorrelation,
    fep_fep037.FEP037.fep037_relaxation]
  ring

/-- fep-021's EFE sign convention accepts fep-041's native KL information
gain without leaving the extended-nonnegative-real codomain. -/
theorem fep021_informationGain_balance
    {State : Type*} [MeasurableSpace State]
    (posterior prior : Measure State) (pragmaticCost : ENNReal)
    (hvalue :
      fep_fep041.FEP041.fep041_informationGain posterior prior ≤ pragmaticCost) :
    fep_fep021.FEP021.fep021_expectedFreeEnergy pragmaticCost
          (fep_fep041.FEP041.fep041_informationGain posterior prior) +
        fep_fep041.FEP041.fep041_informationGain posterior prior =
      pragmaticCost := by
  exact fep_fep021.FEP021.fep021_efe_epistemic_balance hvalue

/-- fep-003's discounted pragmatic cost is a direct input to fep-021's EFE
balance, with no scalar conversion or copied EFE convention. -/
theorem fep003_pragmaticCost_efe_balance
    (discount : ENNReal) (stageCost : ℕ → ENNReal) (horizon : ℕ)
    (epistemicValue : ENNReal)
    (hvalue : epistemicValue ≤
      fep_fep003.FEP003.fep003_pragmaticCost discount stageCost horizon) :
    fep_fep021.FEP021.fep021_expectedFreeEnergy
          (fep_fep003.FEP003.fep003_pragmaticCost discount stageCost horizon)
          epistemicValue + epistemicValue =
      fep_fep003.FEP003.fep003_pragmaticCost discount stageCost horizon := by
  exact fep_fep021.FEP021.fep021_efe_epistemic_balance hvalue

/-- fep-024's regularizer is exactly fep-014's native KL divergence scaled by
the declared nonnegative weight. -/
theorem fep024_regularizer_is_fep014_kl
    {α : Type*} [MeasurableSpace α]
    (base weight : ENNReal) (approximation prior : Measure α) :
    fep_fep024.FEP024.fep024_klRegularizedObjective
        base weight approximation prior =
      base + weight * InformationTheory.klDiv approximation prior ∧
    0 ≤ InformationTheory.klDiv approximation prior := by
  exact ⟨rfl, fep_fep014.FEP014.fep014_kl_nonneg approximation prior⟩

/-- At zero inverse temperature (`β = 0`), hence the infinite-temperature
limit, either state of a binary Gibbs law has probability one half. -/
theorem fep031_zeroBeta_binary_uniform (E : Fin 2 → ℝ) :
    fep_fep031.FEP031.fep031_gibbsProbability
        0 2 E Finset.univ 0 = (2 : ℝ)⁻¹ := by
  simp [fep_fep031.FEP031.fep031_gibbsProbability]

/-- The zero-inverse-temperature binary Gibbs law therefore attains the
fep-030 binary entropy maximum. -/
theorem fep031_zeroBeta_binary_maxEntropy (E : Fin 2 → ℝ) :
    Real.binEntropy
        (fep_fep031.FEP031.fep031_gibbsProbability
          0 2 E Finset.univ 0) = Real.log 2 := by
  rw [fep031_zeroBeta_binary_uniform]
  exact
    (fep_fep030.FEP030.fep030_binaryEntropy_eq_max_iff (2 : ℝ)⁻¹).2 rfl

/-- fep-004's finite weighted metric specializes exactly to fep-038's
one-dimensional Bernoulli Fisher metric. -/
theorem fep004_bernoulliMetric_specialization (p v w : ℝ) :
    fep_fep004.FEP004.fep004_fisherMetric
        (ι := Unit)
        (fun _ => fep_fep038.FEP038.fep038_fisherInformation p)
        (fun _ => v) (fun _ => w) =
      fep_fep038.FEP038.fep038_fisherMetric p v w := by
  simp [fep_fep004.FEP004.fep004_fisherMetric,
    fep_fep038.FEP038.fep038_fisherMetric]

/-- fep-026 prior complexity and fep-011 self-information are the same
negative-log functional, preventing two sign conventions from drifting. -/
theorem fep026_priorComplexity_is_fep011_surprise (p : ℝ) :
    fep_fep026.FEP026.fep026_priorComplexity p =
      fep_fep011.FEP011.fep011_surprise p := by
  rfl

/-- fep-028's normalized finite softmax supplies a unit-interval policy law
to fep-012's entropy-regularized objective. -/
theorem fep012_softmax_entropyRegularizedCost_le
    (γ : ℝ) (cost : Fin 10 → ℝ) (policies : Finset (Fin 10))
    (hne : policies.Nonempty) {temperature : ℝ} (htemperature : 0 ≤ temperature) :
    fep_fep012.FEP012.fep012_entropyRegularizedCost
        (fep_fep028.FEP028.fep028_softmax γ cost policies)
        cost temperature ≤
      fep_fep012.FEP012.fep012_expectedCost
        (fep_fep028.FEP028.fep028_softmax γ cost policies) cost := by
  apply fep_fep012.FEP012.fep012_entropyRegularizedCost_le_expectedCost
  · exact htemperature
  · intro policy
    exact ⟨
      fep_fep028.FEP028.fep028_softmax_nonneg
        γ cost policies policy hne,
      fep_fep028.FEP028.fep028_softmax_le_one
        γ cost policies policy hne⟩

/-- Choosing Gaussian thermal entropy from fep-040 and internal energy
`U(T)=T/2` satisfies fep-013's equilibrium first-law premise, so the
Helmholtz derivative is exactly minus entropy. -/
theorem fep013_gaussianHelmholtz_derivative
    {κ T : ℝ} (hκ : 0 < κ) (hT : 0 < T) :
    HasDerivAt
      (fun t => fep_fep013.FEP013.fep013_helmholtz
        (t / 2) t (fep_fep040.FEP040.fep040_thermalEntropy κ t))
      (-fep_fep040.FEP040.fep040_thermalEntropy κ T) T := by
  have hU : HasDerivAt (fun t : ℝ => t / 2) (1 / 2) T := by
    simpa using (hasDerivAt_id T).div_const 2
  have hS :=
    fep_fep040.FEP040.fep040_thermalEntropy_hasDerivAt hκ hT
  have hfirstLaw : (1 / 2 : ℝ) = T * (1 / (2 * T)) := by
    field_simp [ne_of_gt hT]
  exact fep_fep013.FEP013.fep013_helmholtz_derivative_eq_neg_entropy
    hU hS hfirstLaw

/-- A gradient step on fep-043's quadratic is exactly fep-032's centered
update with effective step size 2*a*eta. This identity has no curvature
or stable-step premise. -/
theorem fep032_update_is_fep043_gradientStep
    (η a center x : ℝ) :
    x - η * fep_fep043.FEP043.fep043_quadraticGradient a center x =
      fep_fep032.FEP032.fep032_quadraticUpdate (2 * a * η) center x := by
  simp [fep_fep043.FEP043.fep043_quadraticGradient,
    fep_fep032.FEP032.fep032_quadraticUpdate]
  ring

/-- Local energies of fep-005's four exact partition blocks sum to the total
state energy through fep-039's additive global free energy. -/
def fep005_blockEnergy
    (assign : Fin 20 → fep_fep005.FEP005.BlkPart)
    (stateEnergy : Fin 20 → ℝ)
    (block : fep_fep005.FEP005.BlkPart) : ℝ :=
  ∑ state ∈ fep_fep005.FEP005.fep005_partitionCover assign block,
    stateEnergy state

theorem fep039_partitionEnergy_conservation
    (assign : Fin 20 → fep_fep005.FEP005.BlkPart)
    (stateEnergy : Fin 20 → ℝ) :
    fep_fep039.FEP039.fep039_global_fe
        (fep005_blockEnergy assign stateEnergy) =
      ∑ state : Fin 20, stateEnergy state := by
  classical
  simpa [fep_fep039.FEP039.fep039_global_fe, fep005_blockEnergy,
    fep_fep005.FEP005.fep005_partitionCover] using
    (Finset.sum_fiberwise (s := Finset.univ) assign stateEnergy)

/-- One stick-breaking fraction is the Bernoulli law of fep-045: the allocated
weight and the residual are its `true` and `false` masses.  Applied to the
conjugate posterior parameter, fep-046's mass-conservation law derives the
normalization of fep-045's posterior mass function. -/
theorem fep046_single_break_is_fep045_bernoulli (p l₀ l₁ : ℝ) :
    fep_fep046.FEP046.fep046_stickWeights
          [fep_fep045.FEP045.fep045_posteriorParameter p l₀ l₁] =
        [fep_fep045.FEP045.fep045_bernoulliMass
          (fep_fep045.FEP045.fep045_posteriorParameter p l₀ l₁) true] ∧
      fep_fep046.FEP046.fep046_remainder
          [fep_fep045.FEP045.fep045_posteriorParameter p l₀ l₁] =
        fep_fep045.FEP045.fep045_bernoulliMass
          (fep_fep045.FEP045.fep045_posteriorParameter p l₀ l₁) false ∧
      ∑ b : Bool, fep_fep045.FEP045.fep045_bernoulliMass
          (fep_fep045.FEP045.fep045_posteriorParameter p l₀ l₁) b = 1 := by
  refine ⟨?_, ?_, ?_⟩
  · simp [fep_fep046.FEP046.fep046_stickWeights,
      fep_fep045.FEP045.fep045_bernoulliMass]
  · simp [fep_fep046.FEP046.fep046_remainder,
      fep_fep045.FEP045.fep045_bernoulliMass]
  · have hconserve := fep_fep046.FEP046.fep046_mass_conservation
      [fep_fep045.FEP045.fep045_posteriorParameter p l₀ l₁]
    simp [fep_fep046.FEP046.fep046_stickWeights,
      fep_fep046.FEP046.fep046_remainder,
      fep_fep045.FEP045.fep045_bernoulliMass] at hconserve ⊢

/-! ## Derivations from released core topics

Reviewed derivational edges for core topics that previously had no relation
(LEAN-8).  The five expansion leaves own exactly one bridge per expansion
topic, so these core-topic derivations live here. -/

section CoreTopicDerivations

open FEP FEP.ControlledMarkov FEP.TemporalInference FEP.FiniteInformation
  FEP.FiniteMarkovDynamics FEP.GeometricOptimization FEP.InformationGeometry
  FEP.PathThermodynamics Finset
open scoped BigOperators Matrix

/-- With unit incoming messages and factor `exp (-gamma * cost)`, fep-007's
normalized sum-product message is fep-028's support-aware softmax on the
support embedded from `Fin 8` into the ten-policy type.  Consequently fep-007's
message normalization derives the unit sum of that softmax. -/
theorem fep007_normalizedMessage_is_fep028_softmax
    (gamma : ℝ) (cost : Fin 10 → ℝ) (neighbors : Finset (Fin 8))
    (hNeighbors : neighbors.Nonempty) (node : Fin 8) :
    (∀ target : Fin 8,
      fep_fep007.FEP007.fep007_normalizedMessage
          (fun _ source =>
            Real.exp (-gamma * cost (Fin.castLE (by norm_num) source)))
          (fun _ => 1) neighbors node target =
        fep_fep028.FEP028.fep028_softmax gamma cost
          (neighbors.map ⟨Fin.castLE (by norm_num), Fin.castLE_injective _⟩)
          (Fin.castLE (by norm_num) target)) ∧
      (∑ policy ∈ neighbors.map
          ⟨Fin.castLE (by norm_num), Fin.castLE_injective _⟩,
        fep_fep028.FEP028.fep028_softmax gamma cost
          (neighbors.map ⟨Fin.castLE (by norm_num), Fin.castLE_injective _⟩)
          policy = 1) := by
  have hIdentify : ∀ target : Fin 8,
      fep_fep007.FEP007.fep007_normalizedMessage
          (fun _ source =>
            Real.exp (-gamma * cost (Fin.castLE (by norm_num) source)))
          (fun _ => 1) neighbors node target =
        fep_fep028.FEP028.fep028_softmax gamma cost
          (neighbors.map ⟨Fin.castLE (by norm_num), Fin.castLE_injective _⟩)
          (Fin.castLE (by norm_num) target) := by
    intro target
    classical
    simp only [fep_fep007.FEP007.fep007_normalizedMessage,
      fep_fep007.FEP007.fep007_unnormalizedMessage,
      fep_fep007.FEP007.fep007_messageNormalizer,
      fep_fep028.FEP028.fep028_softmax, mul_one, Finset.sum_map,
      Function.Embedding.coeFn_mk]
    simp
  refine ⟨hIdentify, ?_⟩
  rw [Finset.sum_map]
  simp only [Function.Embedding.coeFn_mk]
  calc
    _ = ∑ target ∈ neighbors,
        fep_fep007.FEP007.fep007_normalizedMessage
          (fun _ source =>
            Real.exp (-gamma * cost (Fin.castLE (by norm_num) source)))
          (fun _ => 1) neighbors node target :=
      Finset.sum_congr rfl fun target _ => (hIdentify target).symm
    _ = 1 :=
      fep_fep007.FEP007.fep007_normalizedMessage_sum_one _ _ neighbors node
        hNeighbors (fun _ _ => Real.exp_pos _) (fun _ _ => one_pos)

/-- fep-029's scalar quadratic Bregman divergence is the one-coordinate
instance of the generic Bregman divergence of fep-104 with potential `v 0 ^ 2`
and gradient `2 * v 0`; the fep-104 three-point identity therefore yields the
scalar three-point law for fep-029's divergence. -/
theorem fep029_quadraticBregman_is_fep104_scalar_instance (x y z : ℝ) :
    bregmanDivergence (d := 1) (fun v => v 0 ^ 2) (fun v _ => 2 * v 0)
        (fun _ => x) (fun _ => y) =
        fep_fep029.FEP029.fep029_quadraticBregman x y ∧
      fep_fep029.FEP029.fep029_quadraticBregman x z -
          fep_fep029.FEP029.fep029_quadraticBregman x y -
          fep_fep029.FEP029.fep029_quadraticBregman y z =
        2 * (y - z) * (x - y) := by
  have hIdentify : ∀ a b : ℝ,
      bregmanDivergence (d := 1) (fun v => v 0 ^ 2) (fun v _ => 2 * v 0)
          (fun _ => a) (fun _ => b) =
        fep_fep029.FEP029.fep029_quadraticBregman a b := by
    intro a b
    simp [bregmanDivergence, coordinatePairing,
      fep_fep029.FEP029.fep029_quadraticBregman]
  refine ⟨hIdentify x y, ?_⟩
  have hThree := fep_fep104.FEP104.fep104_mirrorDescent_threePoint_identity
    (d := 1) (fun v => v 0 ^ 2) (fun v _ => 2 * v 0)
    (fun _ => x) (fun _ => y) (fun _ => z)
  rw [hIdentify, hIdentify, hIdentify] at hThree
  simpa [coordinatePairing, mul_sub, sub_mul] using hThree

/-- Discharging fep-050's second-law premise with fep-049's nonnegative
quadratic entropy production derives the Landauer work bound.  The explicit
`hBalance` premise identifies the erasure's total entropy change with the
constitutive-law entropy production; it is a modelling assumption, not a
consequence of either topic. -/
theorem fep050_landauer_work_bound_from_fep049_entropy_production
    {Edge : Type*} [Fintype Edge] {W Q T kB : ℝ} (hT : 0 < T)
    (conductance force : Edge → ℝ)
    (hConductance : ∀ edge, 0 ≤ conductance edge)
    (hBalance : fep_fep050.FEP050.fep050_totalEntropyChange Q T kB =
      fep_fep049.FEP049.fep049_entropyProduction conductance force)
    (hWorkHeat : Q ≤ W) :
    fep_fep050.FEP050.fep050_landauerBound kB T ≤ W := by
  have hSecondLaw : 0 ≤ fep_fep050.FEP050.fep050_totalEntropyChange Q T kB := by
    rw [hBalance]
    exact fep_fep049.FEP049.fep049_entropyProduction_nonneg
      conductance force hConductance
  exact fep_fep050.FEP050.fep050_landauer_work_bound hT hSecondLaw hWorkHeat

end CoreTopicDerivations

end FEPComposed
