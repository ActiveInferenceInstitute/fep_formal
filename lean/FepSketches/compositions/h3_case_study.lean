module
public import FepSketches.h3_reference_model
public import FepSketches.markov_blanket
public import FepSketches.native_blanket
public import FepSketches.causal_dynamics
public import FepSketches.compositions.finite_scientific_implications
public import FepSketches.compositions.smooth_reference_kernel
public import FepSketches.compositions.gaussian_filter
public import FepSketches.compositions.gaussian_control
public import FepSketches.compositions.gaussian_grid_path
public import FepSketches.compositions.finite_policy_action
public import FepSketches.path_thermodynamics
public import Mathlib.Analysis.SpecificLimits.Basic
public import Mathlib.InformationTheory.KullbackLeibler.ChainRule
public import Mathlib.InformationTheory.KullbackLeibler.DataProcessing

@[expose] public section

/-!
# Frozen H3 cross-domain case study

This composition connects the exact finite-time Fin4 laws selected by the H3
foundation to native scalar observations, Gaussian conditioning, interventions,
filtering and control. Statements concern dimensionless finite-time laws.
Native posterior and conditional-distribution identities are almost-everywhere;
normalization, precision sparsity and good prediction do not imply causal
identification, empirical validity or measured heat.
-/

open Filter MeasureTheory ProbabilityTheory InformationTheory Matrix
open scoped ENNReal MatrixOrder MeasureTheory NNReal ProbabilityTheory RealInnerProductSpace Topology

namespace FEPComposed.H3CaseStudy

noncomputable section

section NativeProjection

open FEP.Fin4GaussianSemigroup
open FEP.Fin4GaussianSemigroup.Axis

private theorem sum_axis (f : Axis → ℝ) :
    ∑ axis, f axis = f external + f sensory + f active + f internal := by
  classical
  change Finset.univ.sum f = _
  rw [show (Finset.univ : Finset Axis) = {external, sensory, active, internal} by
    ext axis; cases axis <;> simp]
  simp [add_assoc]

/-- Project every full starting state. No embedded-line restriction or reset
of hidden coordinates is imposed. -/
def scalarCoordinate (state : FEP.H3ReferenceModel.StandardState) : ℝ :=
  allOnesProjection (FEP.H3ReferenceModel.toNativeState state)

@[fun_prop] theorem measurable_scalarCoordinate : Measurable scalarCoordinate := by
  unfold scalarCoordinate
  fun_prop

private theorem evolution_projected (time : ℝ≥0) (state : StandardizedState) :
    allOnesProjection
        (Matrix.toEuclideanCLM (𝕜 := ℝ)
          (NormedSpace.exp ((-(time : ℝ)) • K)) state) =
      Real.exp (-2 * (time : ℝ)) * allOnesProjection state := by
  change ⟪normalizedAllOnes,
      Matrix.toEuclideanCLM (𝕜 := ℝ)
        (NormedSpace.exp ((-(time : ℝ)) • K)) state⟫ =
    Real.exp (-2 * (time : ℝ)) * ⟪normalizedAllOnes, state⟫
  simp only [EuclideanSpace.inner_eq_star_dotProduct, star_trivial]
  have hSymm := (parameters (0 : StandardizedState)).evolution_transpose time
  have hSwap : (NormedSpace.exp ((-(time : ℝ)) • K)).IsSymm := hSymm
  change ((NormedSpace.exp ((-(time : ℝ)) • K)) *ᵥ state) ⬝ᵥ
      normalizedAllOnes = _
  rw [dotProduct_comm, hSwap.dotProduct_mulVec_comm,
    evolution_normalizedAllOnes, dotProduct_smul, smul_eq_mul]

private theorem projected_transitionMean (center : ℝ) (time : ℝ≥0)
    (state : StandardizedState) :
    (∫ next, allOnesProjection next ∂
      transition (allOnesEmbedding center) time state) =
      (scalarParameters center).transitionMean time (allOnesProjection state) := by
  rw [transition_apply]
  rw [allOnesProjection.integral_comp_id_comm IsGaussian.integrable_id,
    integral_id_multivariateGaussian, map_add,
    allOnesProjection_embedding, evolution_projected, map_sub,
    allOnesProjection_embedding]
  simp [scalarParameters,
    FEP.LinearGaussianSemigroup.LinearGaussianParameters.finOneScalarParameters,
    FEP.ScalarGaussianSemigroup.ScalarOUParameters.transitionMean,
    FEP.ScalarGaussianSemigroup.ScalarOUParameters.decay]

private theorem projected_transitionCovariance (center : ℝ) (time : ℝ≥0) :
    normalizedAllOnes ⬝ᵥ
        (parameters (allOnesEmbedding center)).transitionCovariance time *ᵥ
          normalizedAllOnes =
      (((scalarParameters center).transitionVariance time : ℝ≥0) : ℝ) := by
  rw [FEP.LinearGaussianSemigroup.LinearGaussianParameters.transitionCovariance]
  change
    normalizedAllOnes ⬝ᵥ
        (FEP.Fin4GaussianSemigroup.Sigma -
          NormedSpace.exp ((-(time : ℝ)) • K) * FEP.Fin4GaussianSemigroup.Sigma *
            (NormedSpace.exp ((-(time : ℝ)) • K))ᵀ) *ᵥ
          normalizedAllOnes = _
  have hTranspose :
      (NormedSpace.exp ((-(time : ℝ)) • K))ᵀ =
        NormedSpace.exp ((-(time : ℝ)) • K) := by
    exact (parameters (allOnesEmbedding center)).evolution_transpose time
  rw [hTranspose, sub_mulVec]
  have hTransport :
      (NormedSpace.exp ((-(time : ℝ)) • K) * FEP.Fin4GaussianSemigroup.Sigma *
          NormedSpace.exp ((-(time : ℝ)) • K)) *ᵥ normalizedAllOnes =
        ((1 / 2 : ℝ) * Real.exp (-2 * (time : ℝ)) ^ 2) •
          normalizedAllOnes := by
    calc
      _ = NormedSpace.exp ((-(time : ℝ)) • K) *ᵥ
          (FEP.Fin4GaussianSemigroup.Sigma *ᵥ
            (NormedSpace.exp ((-(time : ℝ)) • K) *ᵥ
              normalizedAllOnes)) := by
            rw [Matrix.mulVec_mulVec, Matrix.mulVec_mulVec]
      _ = NormedSpace.exp ((-(time : ℝ)) • K) *ᵥ
          (FEP.Fin4GaussianSemigroup.Sigma *ᵥ
            (Real.exp (-2 * (time : ℝ)) • normalizedAllOnes)) := by
            rw [evolution_normalizedAllOnes]
      _ = NormedSpace.exp ((-(time : ℝ)) • K) *ᵥ
          (Real.exp (-2 * (time : ℝ)) •
            (FEP.Fin4GaussianSemigroup.Sigma *ᵥ normalizedAllOnes)) := by
            rw [Matrix.mulVec_smul]
      _ = NormedSpace.exp ((-(time : ℝ)) • K) *ᵥ
          (Real.exp (-2 * (time : ℝ)) •
            ((1 / 2 : ℝ) • normalizedAllOnes)) := by
            rw [Sigma_normalizedAllOnes]
      _ = Real.exp (-2 * (time : ℝ)) •
          ((1 / 2 : ℝ) •
            (NormedSpace.exp ((-(time : ℝ)) • K) *ᵥ
              normalizedAllOnes)) := by
            simp only [Matrix.mulVec_smul, smul_smul]
      _ = _ := by
            rw [evolution_normalizedAllOnes]
            simp only [smul_smul]
            congr 1
            ring
  rw [hTransport, Sigma_normalizedAllOnes, dotProduct_sub,
    dotProduct_smul, dotProduct_smul]
  rw [show normalizedAllOnes ⬝ᵥ normalizedAllOnes = 1 by
    change ∑ _ : Axis, (1 / 2 : ℝ) * (1 / 2 : ℝ) = 1
    rw [sum_axis]
    norm_num]
  simp only [smul_eq_mul, mul_one]
  change
    (1 / 2 : ℝ) -
        (1 / 2 : ℝ) * Real.exp (-2 * (time : ℝ)) ^ 2 =
      (2 / (2 * 2) : ℝ) *
        (1 - Real.exp (-2 * (time : ℝ)) ^ 2)
  ring

private theorem projected_transitionVariance (center : ℝ) (time : ℝ≥0)
    (state : StandardizedState) :
    Var[allOnesProjection;
      transition (allOnesEmbedding center) time
        state] =
      (((scalarParameters center).transitionVariance time : ℝ≥0) : ℝ) := by
  rw [transition_apply]
  let mean : StandardizedState :=
    allOnesEmbedding center +
      Matrix.toEuclideanCLM (𝕜 := ℝ)
        (NormedSpace.exp ((-(time : ℝ)) • K))
        (state - allOnesEmbedding center)
  let covariance : Matrix Axis Axis ℝ :=
    FEP.Fin4GaussianSemigroup.Sigma - NormedSpace.exp ((-(time : ℝ)) • K) * FEP.Fin4GaussianSemigroup.Sigma *
      (NormedSpace.exp ((-(time : ℝ)) • K))ᵀ
  change Var[allOnesProjection; multivariateGaussian mean covariance] = _
  calc
    Var[allOnesProjection; multivariateGaussian mean covariance] =
        covarianceBilin (multivariateGaussian mean covariance)
          normalizedAllOnes normalizedAllOnes := by
      symm
      rw [show (allOnesProjection : StandardizedState → ℝ) =
          fun next => ⟪normalizedAllOnes, next⟫ by
        funext next
        rfl]
      exact covarianceBilin_self
        (μ := multivariateGaussian mean covariance)
        IsGaussian.memLp_two_id
        normalizedAllOnes
    _ = normalizedAllOnes ⬝ᵥ covariance *ᵥ normalizedAllOnes := by
      exact covarianceBilin_multivariateGaussian
        ((parameters (allOnesEmbedding center)).transitionCovariance_posSemidef time)
        normalizedAllOnes normalizedAllOnes
    _ = _ := projected_transitionCovariance center time

/-- Actual arbitrary-state native pushforward equals the scalar OU row. -/
theorem arbitrary_state_projection_native (center : ℝ) (time : ℝ≥0)
    (state : StandardizedState) :
    (transition (allOnesEmbedding center) time state).map allOnesProjection =
      (scalarParameters center).ouTransition time (allOnesProjection state) := by
  have hMean := projected_transitionMean center time state
  have hVariance := projected_transitionVariance center time state
  rw [transition_apply] at hMean hVariance
  rw [transition_apply, IsGaussian.map_eq_gaussianReal]
  change gaussianReal ((multivariateGaussian _ _)[allOnesProjection])
      Var[allOnesProjection; multivariateGaussian _ _].toNNReal =
    gaussianReal ((scalarParameters center).transitionMean time (allOnesProjection state))
      ((scalarParameters center).transitionVariance time)
  rw [hMean, hVariance]
  simp

/-- The scientific-state transport has the identical row law for every state. -/
theorem arbitrary_state_projection (center : ℝ) (time : ℝ≥0)
    (state : FEP.H3ReferenceModel.StandardState) :
    (FEP.H3ReferenceModel.transition
      (FEP.H3ReferenceModel.fromNativeState (allOnesEmbedding center)) time state).map
        scalarCoordinate =
      (FEP.H3ReferenceModel.scalarParameters center).ouTransition time
        (scalarCoordinate state) := by
  rw [FEP.H3ReferenceModel.transition_apply,
    FEP.H3ReferenceModel.toNative_fromNative,
    Measure.map_map measurable_scalarCoordinate
      FEP.H3ReferenceModel.measurable_fromNativeState]
  change (transition (allOnesEmbedding center) time
    (FEP.H3ReferenceModel.toNativeState state)).map allOnesProjection = _
  exact arbitrary_state_projection_native center time _

end NativeProjection

/-! ## Named finite tuple bridge and intrinsic Gaussian blanket -/

/-- Explicit right-associated H1 dynamical order: internal, sensory, active,
external. This is a type-level permutation, not an identification of finite
and continuous probability laws. -/
def h1TupleEquiv : FEP.H3ReferenceModel.StandardState ≃
    FEP.MarkovBlanket.DynamicState ℝ ℝ ℝ ℝ where
  toFun state := (state .internal, state .sensory, state .active, state .external)
  invFun tuple := fun axis => match axis with
    | .external => tuple.2.2.2
    | .sensory => tuple.2.1
    | .active => tuple.2.2.1
    | .internal => tuple.1
  left_inv state := by funext axis; cases axis <;> rfl
  right_inv tuple := by rcases tuple with ⟨i, s, a, e⟩; rfl

/-- The actual stationary Gaussian blanket factorization, transported only
through the explicit native-state conversion. -/
theorem native_blanket (center : FEP.H3ReferenceModel.StandardState) :
    FEP.H3ReferenceModel.K .external .internal = 0 ∧
    cov[fun state : FEP.H3ReferenceModel.NativeState => state .external,
      fun state => state .internal;
      FEP.Fin4GaussianSemigroup.stationaryLaw (FEP.H3ReferenceModel.toNativeState center)] =
        1 / 24 ∧
    ((fun state : FEP.H3ReferenceModel.NativeState => state .external) ⟂ᵢ[
      FEP.GaussianPrecisionConditioning.blanketCoordinates,
      FEP.GaussianPrecisionConditioning.measurable_blanketCoordinates;
      FEP.Fin4GaussianSemigroup.stationaryLaw (FEP.H3ReferenceModel.toNativeState center)]
      (fun state => state .internal)) := by
  rcases FEP.GaussianPrecisionConditioning.precisionZero_covarianceNonzero_condIndep
    (FEP.H3ReferenceModel.toNativeState center) with ⟨hK, hCov, _, hCI⟩
  exact ⟨by simpa only [FEP.H3ReferenceModel.K_eq_carrier] using hK, hCov, hCI⟩

/-- The precision-block recognition mean is the actual native Gaussian
conditional mean, not the internal sample or a covariance-zero condition. -/
theorem native_recognition (center state : FEP.H3ReferenceModel.StandardState) :
    FEP.H3ReferenceModel.recognitionMean center state =
      FEP.GaussianPrecisionConditioning.externalConditionalMean
        (FEP.H3ReferenceModel.toNativeState center)
        (FEP.GaussianPrecisionConditioning.blanketCoordinates
          (FEP.H3ReferenceModel.toNativeState state)) ∧
    condDistrib (fun next : FEP.H3ReferenceModel.NativeState => next .external)
        FEP.GaussianPrecisionConditioning.blanketCoordinates
        (FEP.Fin4GaussianSemigroup.stationaryLaw (FEP.H3ReferenceModel.toNativeState center))
      =ᵐ[FEP.GaussianPrecisionConditioning.blanketLaw
        (FEP.H3ReferenceModel.toNativeState center)]
      FEP.GaussianPrecisionConditioning.externalConditionalKernel
        (FEP.H3ReferenceModel.toNativeState center) := by
  refine ⟨?_, FEP.GaussianPrecisionConditioning.externalCondDistrib_ae_eq _⟩
  rw [FEP.H3ReferenceModel.recognitionMean_eq]
  rfl

/-- The chosen surgical clamp changes only the active coordinate. -/
def clampActive (value : ℝ) (state : FEP.H3ReferenceModel.StandardState) :
    FEP.H3ReferenceModel.StandardState :=
  fun axis => if axis = FEP.H3ReferenceModel.Axis.active then value else state axis

@[fun_prop] theorem measurable_clampActive (value : ℝ) :
    Measurable (clampActive value) := by
  apply Measurable.of_eval
  intro axis
  by_cases h : axis = FEP.H3ReferenceModel.Axis.active
  · simp [clampActive, h]
  · simpa [clampActive, h] using (measurable_pi_apply axis)

def clampKernel (value : ℝ) : Kernel FEP.H3ReferenceModel.StandardState
    FEP.H3ReferenceModel.StandardState :=
  Kernel.deterministic (clampActive value) (measurable_clampActive value)

instance clampKernel_isMarkovKernel (value : ℝ) : IsMarkovKernel (clampKernel value) := by
  unfold clampKernel
  infer_instance

theorem clamp_normalization (value : ℝ) (state : FEP.H3ReferenceModel.StandardState) :
    clampKernel value state Set.univ = 1 := measure_univ

/-- The full joint external/sensory/internal law is preserved. This is not an
observational-to-causal identification theorem. -/
theorem clamp_nondescendants (value : ℝ)
    (law : Measure FEP.H3ReferenceModel.StandardState) :
    (clampKernel value ∘ₘ law).map
        (fun state => (state FEP.H3ReferenceModel.Axis.external,
          state FEP.H3ReferenceModel.Axis.sensory,
          state FEP.H3ReferenceModel.Axis.internal)) =
      law.map (fun state => (state FEP.H3ReferenceModel.Axis.external,
        state FEP.H3ReferenceModel.Axis.sensory,
        state FEP.H3ReferenceModel.Axis.internal)) := by
  rw [clampKernel, Measure.deterministic_comp_eq_map,
    Measure.map_map (by fun_prop) (measurable_clampActive value)]
  apply Measure.map_congr
  filter_upwards with state
  simp [clampActive,
    FEP.H3ReferenceModel.Axis.external, FEP.H3ReferenceModel.Axis.sensory,
    FEP.H3ReferenceModel.Axis.internal, FEP.H3ReferenceModel.Axis.active]

/-! ## Frozen scalar observation and native posterior/VFE -/

open FEP.GaussianInformationGeometry FEPComposed.GaussianFilter

/-- Exact stationary projected prior selected by the protocol. -/
def prior (center : ℝ) : ScalarGaussianBelief where
  mean := center
  family := ⟨1 / 2, by norm_num⟩

/-- One noisy scalar observation after the same finite-time evolution. -/
def observationFilter (center : ℝ) (duration noise : ℝ≥0) (hNoise : 0 < noise) :
    ScalarGaussianFilterModel where
  dynamics := FEP.H3ReferenceModel.scalarParameters center
  stepDuration := duration
  observationNoise := ⟨noise, hNoise⟩

/-- Native posterior identity for the exact Gaussian observation law. The
statement remains evidence-almost-everywhere. -/
theorem native_posterior (center : ℝ) (duration noise : ℝ≥0) (hNoise : 0 < noise) :
    closedFormPosteriorKernel (observationFilter center duration noise hNoise) (prior center)
      =ᵐ[evidenceLaw (observationFilter center duration noise hNoise) (prior center)]
      ProbabilityTheory.posterior
        (observationKernel (observationFilter center duration noise hNoise))
        (predictionBelief (observationFilter center duration noise hNoise) (prior center)).law :=
  closedFormPosterior_ae_eq_native _ _

/-- The density-relative VFE is globally bounded below by evidence surprisal
in the positive fixed-posterior-variance recognition family and attains it
uniquely at the derived posterior mean. -/
theorem vfe_optimum (center : ℝ) (duration noise : ℝ≥0) (hNoise : 0 < noise)
    (observation recognition : ℝ) :
    FEPComposed.SmoothReferenceKernel.evidenceSurprisal
        (observationFilter center duration noise hNoise) (prior center) observation ≤
      FEPComposed.SmoothReferenceKernel.gaussianVariationalFreeEnergy
        (observationFilter center duration noise hNoise) (prior center) observation recognition ∧
    (FEPComposed.SmoothReferenceKernel.gaussianVariationalFreeEnergy
        (observationFilter center duration noise hNoise) (prior center) observation recognition =
      FEPComposed.SmoothReferenceKernel.evidenceSurprisal
        (observationFilter center duration noise hNoise) (prior center) observation ↔
      recognition = posteriorMean
        (observationFilter center duration noise hNoise) (prior center) observation) := by
  refine ⟨?_, FEPComposed.SmoothReferenceKernel.gaussianVariationalFreeEnergy_eq_surprisal_iff
    _ _ _ _⟩
  rw [FEPComposed.SmoothReferenceKernel.gaussianVariationalFreeEnergy_eq_meanSquare_add_surprisal]
  have hP := posteriorVariance_pos (observationFilter center duration noise hNoise) (prior center)
  have hPr : 0 < (posteriorVariance
      (observationFilter center duration noise hNoise) (prior center) : ℝ) := by
    exact_mod_cast hP
  exact le_add_of_nonneg_left (div_nonneg (sq_nonneg _) (by positivity))

/-- Positive fixed observation noise identifies the scalar mean from its
native observation law. No rate, diffusion, or hidden-mode identification is
claimed from this one scalar marginal. -/
theorem scalar_mean_identifiability (noise : ℝ≥0) (hNoise : 0 < noise) :
    Function.Injective (fun mean : ℝ => gaussianReal mean noise) := by
  exact (FixedVarianceGaussian.law_injective ⟨noise, hNoise⟩)

/-- The full covariance-selected scalar stationary prior is preserved by the
selected OU prediction at any nonnegative duration. -/
theorem prediction_stationary (center : ℝ) (duration noise : ℝ≥0) (hNoise : 0 < noise) :
    predictionBelief (observationFilter center duration noise hNoise) (prior center) =
      prior center := by
  unfold predictionBelief prior
  congr 1
  · simp [observationFilter, FEP.H3ReferenceModel.scalarParameters,
      FEP.Fin4GaussianSemigroup.scalarParameters,
      FEP.LinearGaussianSemigroup.LinearGaussianParameters.finOneScalarParameters,
      FEP.ScalarGaussianSemigroup.ScalarOUParameters.transitionMean]
  · congr 1
    apply NNReal.eq
    unfold predictionVariance FEP.ScalarGaussianSemigroup.ScalarOUParameters.transitionVariance
    change (FEP.H3ReferenceModel.scalarParameters center).decay duration ^ 2 * (1 / 2 : ℝ) +
      ((FEP.H3ReferenceModel.scalarParameters center).stationaryVariance : ℝ) *
        (1 - (FEP.H3ReferenceModel.scalarParameters center).decay duration ^ 2) = 1 / 2
    rw [FEP.ScalarGaussianSemigroup.ScalarOUParameters.stationaryVariance_eq]
    rcases FEP.H3ReferenceModel.scalarParameters_exact center with ⟨hRate, hD⟩
    rw [hRate, hD]
    norm_num
    ring

/-- The protocol's gain, mean and variance are the actual native-filter
parameters for both frozen settings; no plug-in law replaces prediction. -/
theorem posterior_parameters (center : ℝ) (duration noise : ℝ≥0) (hNoise : 0 < noise)
    (observation : ℝ) :
    gain (observationFilter center duration noise hNoise) (prior center) =
        (1 / 2 : ℝ) / (1 / 2 + noise) ∧
    posteriorMean (observationFilter center duration noise hNoise) (prior center) observation =
        center + ((1 / 2 : ℝ) / (1 / 2 + noise)) * (observation - center) ∧
    (posteriorVariance (observationFilter center duration noise hNoise) (prior center) : ℝ) =
        ((1 / 2 : ℝ) * noise) / (1 / 2 + noise) := by
  simp only [gain, posteriorMean, posteriorVariance, innovationVariance,
    prediction_stationary]
  norm_num [prior, observationFilter]

/-! ## Finite fixed-latent observation experiment and consistency

The native experiment draws one latent coordinate and finitely many independent
noise coordinates. There is no intervening OU transition and no infinite-path
assumption. Probabilities below belong to each finite known-prior experiment.
-/

abbrev BatchState (n : ℕ) := EuclideanSpace ℝ (Fin (n + 1))

def batchMean (n : ℕ) (center : ℝ) : BatchState n :=
  WithLp.toLp 2 (Fin.cases center (fun _ => 0))

def batchCovariance (n : ℕ) (noise : ℝ) : Matrix (Fin (n + 1)) (Fin (n + 1)) ℝ :=
  Matrix.diagonal (Fin.cases (1 / 2) (fun _ => noise))

theorem batchCovariance_posDef (n : ℕ) (noise : ℝ) (hNoise : 0 < noise) :
    (batchCovariance n noise).PosDef := by
  rw [batchCovariance, Matrix.posDef_diagonal_iff]
  intro index
  refine Fin.cases ?_ (fun _ => ?_) index
  · norm_num
  · exact hNoise

/-- Native joint source with latent prior N(center,1/2) and independent
N(0,noise) innovations; both positivity and independence are derived. -/
def batchSourceLaw (n : ℕ) (center noise : ℝ) : Measure (BatchState n) :=
  multivariateGaussian (batchMean n center) (batchCovariance n noise)

instance batchSourceLaw_isProbabilityMeasure (n : ℕ) (center noise : ℝ) :
    IsProbabilityMeasure (batchSourceLaw n center noise) := by
  unfold batchSourceLaw
  infer_instance

instance batchSourceLaw_isGaussian (n : ℕ) (center noise : ℝ) :
    IsGaussian (batchSourceLaw n center noise) := by
  unfold batchSourceLaw
  infer_instance

/-- Finite conditional-independent observation Y_j=Z+epsilon_j. -/
def batchObservations {n : ℕ} (state : BatchState n) : Fin n → ℝ :=
  fun index => state 0 + state index.succ

@[fun_prop] theorem measurable_batchObservations (n : ℕ) :
    Measurable (batchObservations (n := n)) := by
  unfold batchObservations
  fun_prop

/-- Closed posterior mean for the finite observation vector. -/
def batchPosteriorMean {n : ℕ} (center noise : ℝ) (observations : Fin n → ℝ) : ℝ :=
  (2 * noise * center + ∑ index, observations index) / (2 * noise + n)

def batchPosteriorVariance (n : ℕ) (noise : ℝ) : ℝ := noise / (2 * noise + n)

theorem batchDenominator_pos (n : ℕ) (noise : ℝ) (hNoise : 0 < noise) :
    0 < 2 * noise + n := by positivity

theorem batchPosteriorVariance_pos (n : ℕ) (noise : ℝ) (hNoise : 0 < noise) :
    0 < batchPosteriorVariance n noise :=
  div_pos hNoise (batchDenominator_pos n noise hNoise)

def batchErrorVector (n : ℕ) (noise : ℝ) : BatchState n :=
  WithLp.toLp 2
    (Fin.cases (-2 * noise / (2 * noise + n)) (fun _ => 1 / (2 * noise + n)))

/-- Signed posterior-mean error under the finite native joint experiment. -/
def batchError {n : ℕ} (center noise : ℝ) (state : BatchState n) : ℝ :=
  (innerSL ℝ (batchErrorVector n noise)) (state - batchMean n center)

@[fun_prop] theorem measurable_batchError (n : ℕ) (center noise : ℝ) :
    Measurable (batchError (n := n) center noise) := by
  unfold batchError
  fun_prop

/-- The random-variable expression is exactly the declared estimator minus
its latent target, including the n=0 prior-only experiment. -/
theorem batchError_eq (n : ℕ) (center noise : ℝ) (hNoise : 0 < noise)
    (state : BatchState n) :
    batchError center noise state =
      batchPosteriorMean center noise (batchObservations state) - state 0 := by
  have hD := (batchDenominator_pos n noise hNoise).ne'
  simp only [batchError, innerSL_apply_apply, EuclideanSpace.inner_eq_star_dotProduct,
    star_trivial, batchErrorVector, batchMean, dotProduct, Fin.sum_univ_succ,
    PiLp.sub_apply, Fin.cases_zero, Fin.cases_succ]
  simp only [sub_zero]
  rw [← Finset.sum_mul]
  simp only [batchPosteriorMean, batchObservations, Finset.sum_add_distrib,
    Finset.sum_const, Finset.card_univ, Fintype.card_fin, nsmul_eq_mul]
  field_simp
  ring

private theorem batchCentered_hasGaussianLaw (n : ℕ) (center noise : ℝ) :
    HasGaussianLaw (fun state : BatchState n => state - batchMean n center)
      (batchSourceLaw n center noise) := ⟨by fun_prop, by infer_instance⟩

theorem batchError_hasGaussianLaw (n : ℕ) (center noise : ℝ) :
    HasGaussianLaw (batchError (n := n) center noise) (batchSourceLaw n center noise) := by
  exact (batchCentered_hasGaussianLaw n center noise).map_fun
    (innerSL ℝ (batchErrorVector n noise))

theorem batchError_mean (n : ℕ) (center noise : ℝ) :
    ∫ state, batchError center noise state ∂batchSourceLaw n center noise = 0 := by
  change (∫ state, (innerSL ℝ (batchErrorVector n noise))
    (state - batchMean n center) ∂batchSourceLaw n center noise) = 0
  rw [(innerSL ℝ (batchErrorVector n noise)).integral_comp_comm
      (batchCentered_hasGaussianLaw n center noise).integrable,
    integral_sub IsGaussian.integrable_fun_id (integrable_const _)]
  simp [batchSourceLaw]

private theorem batchErrorVector_covariance (n : ℕ) (noise : ℝ) (hNoise : 0 < noise) :
    batchErrorVector n noise ⬝ᵥ
      (batchCovariance n noise) *ᵥ batchErrorVector n noise =
        batchPosteriorVariance n noise := by
  have hD := (batchDenominator_pos n noise hNoise).ne'
  simp only [dotProduct, batchCovariance, Matrix.mulVec_diagonal,
    batchErrorVector, PiLp.toLp_apply, Fin.sum_univ_succ,
    Fin.cases_zero, Fin.cases_succ]
  simp only [Finset.sum_const, Finset.card_univ, Fintype.card_fin, nsmul_eq_mul]
  unfold batchPosteriorVariance
  field_simp

/-- Native variance is derived from the diagonal finite Gaussian source,
never stored as a posterior-convergence assumption. -/
theorem batchError_variance (n : ℕ) (center noise : ℝ) (hNoise : 0 < noise) :
    Var[batchError center noise; batchSourceLaw n center noise] =
      batchPosteriorVariance n noise := by
  have hFun : batchError (n := n) center noise =
      fun state : BatchState n =>
        ⟪batchErrorVector n noise, state⟫ -
          ⟪batchErrorVector n noise, batchMean n center⟫ := by
    funext state
    simp only [batchError, innerSL_apply_apply, inner_sub_right]
  rw [hFun, variance_sub_const (by fun_prop), ← covarianceBilin_self
    (μ := batchSourceLaw n center noise) IsGaussian.memLp_two_id]
  rw [batchSourceLaw, covarianceBilin_multivariateGaussian
    (batchCovariance_posDef n noise hNoise).posSemidef]
  exact batchErrorVector_covariance n noise hNoise

/-- Actual joint MSE is P_n=R/(2R+n). This integrates over the known prior and
finite innovation coordinates, rather than making a pointwise claim at every
possible fixed truth. -/
theorem consistency_mse (n : ℕ) (center noise : ℝ) (hNoise : 0 < noise) :
    (∫ state, (batchPosteriorMean center noise (batchObservations state) - state 0) ^ 2
      ∂batchSourceLaw n center noise) = noise / (2 * noise + n) := by
  simp_rw [← batchError_eq n center noise hNoise]
  have hV := batchError_variance n center noise hNoise
  rw [variance_eq_integral (measurable_batchError n center noise).aemeasurable,
    batchError_mean] at hV
  simpa [batchPosteriorVariance] using hV

/-- The uncapped Markov/Chebyshev tail bound, valid also at n=0. -/
theorem consistency_tail (n : ℕ) (center noise epsilon : ℝ)
    (hNoise : 0 < noise) (hEpsilon : 0 < epsilon) :
    batchSourceLaw n center noise
      {state | epsilon ≤ |batchPosteriorMean center noise (batchObservations state) - state 0|} ≤
        ENNReal.ofReal (batchPosteriorVariance n noise / epsilon ^ 2) := by
  have h := meas_ge_le_variance_div_sq
    (batchError_hasGaussianLaw n center noise).memLp_two hEpsilon
  rw [batchError_mean, batchError_variance n center noise hNoise] at h
  simpa only [sub_zero, batchError_eq n center noise hNoise] using h

/-- The finite-experiment MSE and its tail upper bound tend to zero. -/
theorem consistency_bound_limit (noise epsilon : ℝ) :
    Tendsto (fun n : ℕ => batchPosteriorVariance n noise / epsilon ^ 2)
      atTop (nhds 0) := by
  have hDen : Tendsto (fun n : ℕ => 2 * noise + (n : ℝ)) atTop atTop :=
    tendsto_atTop_add_const_left atTop (2 * noise) tendsto_natCast_atTop_atTop
  have h := (tendsto_const_nhds (x := noise)).mul
    (tendsto_inv_atTop_zero.comp hDen)
  simpa only [batchPosteriorVariance, div_eq_mul_inv, zero_mul, mul_zero, Function.comp_def] using
    (h.div_const (epsilon ^ 2)).congr (fun _ => rfl)

/-- Posterior-mean consistency in probability for the finite known-prior
fixed-latent experiments. No almost-sure, changing-state or parameter-recovery
claim is made. -/
theorem consistency_limit (center noise epsilon : ℝ) (hNoise : 0 < noise)
    (hEpsilon : 0 < epsilon) :
    Tendsto (fun n : ℕ => (batchSourceLaw n center noise).real
      {state | epsilon ≤ |batchPosteriorMean center noise (batchObservations state) - state 0|})
      atTop (nhds 0) := by
  refine squeeze_zero (fun n => measureReal_nonneg) (fun n => ?_)
    (consistency_bound_limit noise epsilon)
  have h := consistency_tail n center noise epsilon hNoise hEpsilon
  have hNonneg : 0 ≤ batchPosteriorVariance n noise / epsilon ^ 2 :=
    div_nonneg (batchPosteriorVariance_pos n noise hNoise).le (sq_nonneg epsilon)
  simpa only [Measure.real_def, ENNReal.toReal_ofReal hNonneg] using
    ENNReal.toReal_mono (by simp) h

private def batchObservationVector (n : ℕ) (index : Fin n) : BatchState n :=
  EuclideanSpace.single 0 1 + EuclideanSpace.single index.succ 1

private def batchObservationCLM (n : ℕ) : BatchState n →L[ℝ] (Fin n → ℝ) :=
  ContinuousLinearMap.pi fun index => innerSL ℝ (batchObservationVector n index)

private theorem batchObservationCLM_apply (n : ℕ) (state : BatchState n) :
    batchObservationCLM n state = batchObservations state := by
  funext index
  simp [batchObservationCLM, batchObservationVector, innerSL_apply_apply,
    EuclideanSpace.inner_single_left, batchObservations]

/-- The finite innovation coordinates are jointly independent in the actual
native source; conditional independence is not a certificate input. -/
theorem batch_innovations_independent (n : ℕ) (center noise : ℝ) (hNoise : 0 < noise) :
    iIndepFun (fun index : Fin (n + 1) => fun state : BatchState n => state index)
      (batchSourceLaw n center noise) := by
  have hGaussian := (IsGaussian.hasGaussianLaw_id
    (μ := batchSourceLaw n center noise)).map
    (PiLp.continuousLinearEquiv 2 ℝ (fun _ : Fin (n + 1) => ℝ)).toContinuousLinearMap
  apply hGaussian.iIndepFun_of_covariance_eq_zero
  intro left right hDifferent
  change cov[fun state : BatchState n => state left,
    fun state => state right; multivariateGaussian (batchMean n center)
      (batchCovariance n noise)] = 0
  rw [covariance_eval_multivariateGaussian
    (batchCovariance_posDef n noise hNoise).posSemidef]
  simp [batchCovariance, Matrix.diagonal, hDifferent]

/-- The actual latent marginal is the frozen stationary projected prior. -/
theorem batch_latent_law (n : ℕ) (center noise : ℝ) (hNoise : 0 < noise) :
    (batchSourceLaw n center noise).map (fun state => state 0) =
      gaussianReal center (1 / 2) := by
  change (batchSourceLaw n center noise).map (EuclideanSpace.proj 0) = _
  rw [IsGaussian.map_eq_gaussianReal]
  have hMean : (∫ state : BatchState n, state 0 ∂batchSourceLaw n center noise) = center := by
    change (∫ state, (EuclideanSpace.proj 0) state ∂batchSourceLaw n center noise) = _
    rw [(EuclideanSpace.proj (0 : Fin (n + 1)) : BatchState n →L[ℝ] ℝ).integral_comp_id_comm IsGaussian.integrable_id]
    simp [batchSourceLaw, batchMean]
  have hVar : Var[fun state : BatchState n => state 0;
      batchSourceLaw n center noise] = 1 / 2 := by
    rw [batchSourceLaw, variance_eval_multivariateGaussian
      (batchCovariance_posDef n noise hNoise).posSemidef]
    simp [batchCovariance]
  change gaussianReal (∫ state : BatchState n, state 0 ∂batchSourceLaw n center noise)
    Var[fun state : BatchState n => state 0; batchSourceLaw n center noise].toNNReal = _
  rw [hMean, hVar]
  congr 1
  apply NNReal.eq
  norm_num [Real.coe_toNNReal]

private theorem batchObservation_error_covariance (n : ℕ) (center noise : ℝ)
    (hNoise : 0 < noise) (index : Fin n) :
    cov[fun state : BatchState n =>
      (innerSL ℝ (batchObservationVector n index)) (state - batchMean n center),
      batchError center noise; batchSourceLaw n center noise] = 0 := by
  change cov[fun state : BatchState n =>
      ⟪batchObservationVector n index, state - batchMean n center⟫,
    fun state => ⟪batchErrorVector n noise, state - batchMean n center⟫;
      batchSourceLaw n center noise] = 0
  simp only [inner_sub_right]
  have hObs : Integrable (fun state : BatchState n => ⟪batchObservationVector n index, state⟫)
      (batchSourceLaw n center noise) := by
    simpa only [Function.comp_def, id_eq, innerSL_apply_apply] using
      ((IsGaussian.hasGaussianLaw_id (μ := batchSourceLaw n center noise)).map
        (innerSL ℝ (batchObservationVector n index))).integrable
  have hError : Integrable (fun state : BatchState n => ⟪batchErrorVector n noise, state⟫)
      (batchSourceLaw n center noise) := by
    simpa only [Function.comp_def, id_eq, innerSL_apply_apply] using
      ((IsGaussian.hasGaussianLaw_id (μ := batchSourceLaw n center noise)).map
        (innerSL ℝ (batchErrorVector n noise))).integrable
  rw [covariance_sub_const_left hObs,
    covariance_sub_const_right hError,
    ← covarianceBilin_apply_eq_cov IsGaussian.memLp_two_id,
    batchSourceLaw, covarianceBilin_multivariateGaussian
      (batchCovariance_posDef n noise hNoise).posSemidef]
  change (batchObservationVector n index).ofLp ⬝ᵥ
    (batchCovariance n noise) *ᵥ (batchErrorVector n noise).ofLp = 0
  simp [batchObservationVector, add_dotProduct, single_dotProduct,
    Matrix.mulVec_diagonal, batchCovariance, batchErrorVector]
  ring

private theorem batchObservations_indep_error (n : ℕ) (center noise : ℝ)
    (hNoise : 0 < noise) :
    IndepFun (batchObservations (n := n)) (batchError center noise)
      (batchSourceLaw n center noise) := by
  let errorCLM : BatchState n →L[ℝ] (Fin 1 → ℝ) :=
    ContinuousLinearMap.pi fun _ => innerSL ℝ (batchErrorVector n noise)
  have hGaussian := (batchCentered_hasGaussianLaw n center noise).map
    ((batchObservationCLM n).prod errorCLM)
  have hIndep := hGaussian.indepFun_of_covariance_eval
    (fun index _ => batchObservation_error_covariance n center noise hNoise index)
  have hShift : Measurable (fun observations : Fin n → ℝ =>
      fun index => observations index + center) := by fun_prop
  have hEval : Measurable (fun errors : Fin 1 → ℝ => errors 0) := measurable_pi_apply 0
  have h := hIndep.comp
    (φ := fun observations : Fin n → ℝ => fun index => observations index + center)
    (ψ := fun errors : Fin 1 → ℝ => errors 0) hShift hEval
  refine h.congr ?_ ?_
  · filter_upwards with state
    funext index
    simp only [Function.comp_apply]
    have hPoint := congrFun (batchObservationCLM_apply n (state - batchMean n center)) index
    change (batchObservationCLM n (state - batchMean n center)) index + center = _
    rw [hPoint]
    simp [batchObservations, batchMean]
    ring
  · filter_upwards with state
    rfl

private theorem batchResidual_law (n : ℕ) (center noise : ℝ) (hNoise : 0 < noise) :
    (batchSourceLaw n center noise).map (fun state => -batchError center noise state) =
      gaussianReal 0 (batchPosteriorVariance n noise).toNNReal := by
  have h := (batchError_hasGaussianLaw n center noise).fun_neg.map_eq_gaussianReal
  rw [integral_neg, batchError_mean, neg_zero, variance_fun_neg,
    batchError_variance n center noise hNoise] at h
  exact h

/-- Positive native posterior kernel for the complete finite observation
vector, not just its plug-in sufficient statistic. -/
def batchPosteriorKernel (n : ℕ) (center noise : ℝ) : Kernel (Fin n → ℝ) ℝ where
  toFun observations := gaussianReal (batchPosteriorMean center noise observations)
    (batchPosteriorVariance n noise).toNNReal
  measurable' := by
    change Measurable (Function.uncurry gaussianReal ∘
      fun observations : Fin n → ℝ =>
        (batchPosteriorMean center noise observations,
          (batchPosteriorVariance n noise).toNNReal))
    apply measurable_gaussianReal.comp
    have hMean : Measurable (batchPosteriorMean (n := n) center noise) := by
      unfold batchPosteriorMean
      fun_prop
    exact hMean.prodMk measurable_const

instance batchPosteriorKernel_isMarkovKernel (n : ℕ) (center noise : ℝ) :
    IsMarkovKernel (batchPosteriorKernel n center noise) :=
  ⟨fun _ => by change IsProbabilityMeasure (gaussianReal _ _); infer_instance⟩

private def batchShift (n : ℕ) (center noise : ℝ)
    (pair : (Fin n → ℝ) × ℝ) : (Fin n → ℝ) × ℝ :=
  (pair.1, pair.2 + batchPosteriorMean center noise pair.1)

private theorem batchPosterior_compProd_eq_shift (n : ℕ) (center noise : ℝ)
    (law : Measure (Fin n → ℝ)) [SFinite law] :
    law ⊗ₘ batchPosteriorKernel n center noise =
      (law.prod (gaussianReal 0 (batchPosteriorVariance n noise).toNNReal)).map
        (batchShift n center noise) := by
  have hShift : Measurable (batchShift n center noise) := by
    unfold batchShift batchPosteriorMean
    fun_prop
  ext set hSet
  rw [Measure.compProd_apply hSet, Measure.map_apply hShift hSet,
    Measure.prod_apply (hShift hSet)]
  apply lintegral_congr
  intro observations
  change gaussianReal (batchPosteriorMean center noise observations)
      (batchPosteriorVariance n noise).toNNReal
        (Prod.mk observations ⁻¹' set) = _
  rw [← show (gaussianReal 0 (batchPosteriorVariance n noise).toNNReal).map
      (fun residual => residual + batchPosteriorMean center noise observations) =
        gaussianReal (batchPosteriorMean center noise observations)
          (batchPosteriorVariance n noise).toNNReal by
    rw [gaussianReal_map_add_const]; simp,
    Measure.map_apply (by fun_prop) (measurable_prodMk_left hSet)]
  rfl

/-- The native finite joint reconstructs from the observation-vector law and
its conjugate posterior. This equality, not an assumed conjugacy field,
justifies the finite Bayes update. -/
theorem finite_likelihood_conjugacy (n : ℕ) (center noise : ℝ) (hNoise : 0 < noise) :
    (batchSourceLaw n center noise).map (fun state => (batchObservations state, state 0)) =
      ((batchSourceLaw n center noise).map batchObservations) ⊗ₘ
        batchPosteriorKernel n center noise := by
  have hIndep := (batchObservations_indep_error n center noise hNoise).comp
    (φ := id) (ψ := fun error : ℝ => -error) measurable_id (by fun_prop)
  have hMap := hIndep.map_prod_eq_prod_map_map
    (measurable_batchObservations n).aemeasurable (by fun_prop)
  simp only [Function.comp_def] at hMap
  rw [batchResidual_law n center noise hNoise] at hMap
  rw [batchPosterior_compProd_eq_shift, ← hMap,
    Measure.map_map (by unfold batchShift batchPosteriorMean; fun_prop) (by fun_prop)]
  apply Measure.map_congr
  filter_upwards with state
  simp only [Function.comp_def, batchShift, batchError_eq n center noise hNoise]
  congr 1
  ring

/-- The finite native conditional distribution agrees with the derived
posterior almost everywhere under the complete observation-vector law. -/
theorem finite_native_posterior (n : ℕ) (center noise : ℝ) (hNoise : 0 < noise) :
    condDistrib (fun state : BatchState n => state 0) batchObservations
        (batchSourceLaw n center noise) =ᵐ[(batchSourceLaw n center noise).map batchObservations]
      batchPosteriorKernel n center noise :=
  condDistrib_ae_eq_of_measure_eq_compProd_of_measurable
    (measurable_batchObservations n) (by fun_prop)
    (finite_likelihood_conjugacy n center noise hNoise)

/-! ## Explicit hidden-mode nonidentifiability -/

section HiddenMode

open FEP.Fin4GaussianSemigroup
open FEP.Fin4GaussianSemigroup.Axis

/-- Projection of a genuine full native Gaussian law with covariance Sigma. -/
theorem gaussianSigma_scalar_marginal (mean : StandardizedState) :
    (multivariateGaussian mean FEP.Fin4GaussianSemigroup.Sigma).map allOnesProjection =
      gaussianReal (allOnesProjection mean) (1 / 2) := by
  rw [IsGaussian.map_eq_gaussianReal]
  have hMean :
      (∫ state, allOnesProjection state ∂multivariateGaussian mean
        FEP.Fin4GaussianSemigroup.Sigma) = allOnesProjection mean := by
    rw [allOnesProjection.integral_comp_id_comm IsGaussian.integrable_id,
      integral_id_multivariateGaussian]
  have hVariance : Var[allOnesProjection;
      multivariateGaussian mean FEP.Fin4GaussianSemigroup.Sigma] = 1 / 2 := by
    rw [show (allOnesProjection : StandardizedState → ℝ) =
      fun state => ⟪normalizedAllOnes, state⟫ by rfl,
      ← covarianceBilin_self IsGaussian.memLp_two_id,
      covarianceBilin_multivariateGaussian Sigma_posDef.posSemidef,
      Sigma_normalizedAllOnes, dotProduct_smul]
    have hUnit : normalizedAllOnes ⬝ᵥ normalizedAllOnes = 1 := by
      change ∑ _ : Axis, (1 / 2 : ℝ) * (1 / 2 : ℝ) = 1
      rw [sum_axis]
      norm_num
    rw [hUnit]
    simp
  change gaussianReal _ _ = _
  rw [hMean, hVariance]
  congr 1
  apply NNReal.eq
  norm_num [Real.coe_toNNReal]

/-- Raw external/internal rate-four mode from the native carrier. -/
def rawHiddenContrast : StandardizedState := WithLp.toLp 2 eigenmodeFourExternal

/-- The frozen normalized external/internal rate-four contrast. -/
def hiddenContrast : StandardizedState := (Real.sqrt 2)⁻¹ • rawHiddenContrast

theorem hiddenContrast_native_binding :
    hiddenContrast = (Real.sqrt 2)⁻¹ • WithLp.toLp 2 eigenmodeFourExternal ∧
      K *ᵥ hiddenContrast = 4 • hiddenContrast := by
  refine ⟨rfl, ?_⟩
  change K *ᵥ ((Real.sqrt 2)⁻¹ • eigenmodeFourExternal) =
    4 • ((Real.sqrt 2)⁻¹ • eigenmodeFourExternal)
  rw [Matrix.mulVec_smul, K_eigenmode_four_external]
  module

theorem hiddenContrast_norm : ‖hiddenContrast‖ = 1 := by
  have hRawInner : ⟪rawHiddenContrast, rawHiddenContrast⟫ = (2 : ℝ) := by
    rw [rawHiddenContrast, EuclideanSpace.inner_toLp_toLp]
    simp only [dotProduct, star_trivial]
    rw [sum_axis]
    norm_num [eigenmodeFourExternal]
  have hRawNorm : ‖rawHiddenContrast‖ = Real.sqrt 2 := by
    rw [norm_eq_sqrt_real_inner, hRawInner]
  rw [hiddenContrast, norm_smul, hRawNorm, Real.norm_eq_abs, abs_inv,
    abs_of_pos (Real.sqrt_pos.2 (by norm_num : (0 : ℝ) < 2)),
    inv_mul_cancel₀ (Real.sqrt_pos.2 (by norm_num : (0 : ℝ) < 2)).ne']

theorem hiddenContrast_ne_zero : hiddenContrast ≠ 0 := by
  intro h
  have := hiddenContrast_norm
  rw [h, norm_zero] at this
  norm_num at this

theorem hiddenContrast_projection : allOnesProjection hiddenContrast = 0 := by
  rw [hiddenContrast, map_smul]
  have hRaw : allOnesProjection rawHiddenContrast = 0 := by
    change ∑ axis : Axis, rawHiddenContrast axis * normalizedAllOnes axis = 0
    rw [sum_axis]
    norm_num [rawHiddenContrast, eigenmodeFourExternal, normalizedAllOnes]
  rw [hRaw, smul_zero]

def hiddenInitialLaw (center : ℝ) (shiftHidden : Bool) : Measure StandardizedState :=
  multivariateGaussian
    (allOnesEmbedding center + if shiftHidden then hiddenContrast else 0)
    FEP.Fin4GaussianSemigroup.Sigma

instance hiddenInitialLaw_isProbabilityMeasure (center : ℝ) (shiftHidden : Bool) :
    IsProbabilityMeasure (hiddenInitialLaw center shiftHidden) := by
  unfold hiddenInitialLaw
  infer_instance

theorem hiddenInitialLaw_projection (center : ℝ) (shiftHidden : Bool) :
    (hiddenInitialLaw center shiftHidden).map allOnesProjection =
      gaussianReal center (1 / 2) := by
  rw [hiddenInitialLaw, gaussianSigma_scalar_marginal, map_add,
    allOnesProjection_embedding]
  cases shiftHidden <;> simp [hiddenContrast_projection]

private theorem full_transition_projection (center : ℝ) (time : ℝ≥0)
    (law : Measure StandardizedState) :
    (transition (allOnesEmbedding center) time ∘ₘ law).map allOnesProjection =
      (scalarParameters center).ouTransition time ∘ₘ law.map allOnesProjection := by
  rw [Measure.map_comp _ _ (by fun_prop)]
  have hKernel : (transition (allOnesEmbedding center) time).map allOnesProjection =
      ((scalarParameters center).ouTransition time).comap
        allOnesProjection (by fun_prop) := by
    apply DFunLike.ext _ _
    intro state
    rw [Kernel.map_apply _ (by fun_prop), Kernel.comap_apply]
    exact arbitrary_state_projection_native center time state
  rw [hKernel, ← Kernel.comp_deterministic_eq_comap,
    ← Measure.comp_assoc, Measure.deterministic_comp_eq_map]

/-- Distinct full native initial laws remain indistinguishable by this
projected trajectory marginal at every nonnegative time. The hidden mode is
retained in the full carrier, rather than reset to an embedded scalar state. -/
theorem hidden_mode_marginal_nonidentifiability (center : ℝ) (time : ℝ≥0) :
    hiddenInitialLaw center false ≠ hiddenInitialLaw center true ∧
    (transition (allOnesEmbedding center) time ∘ₘ hiddenInitialLaw center false).map
        allOnesProjection =
      (transition (allOnesEmbedding center) time ∘ₘ hiddenInitialLaw center true).map
        allOnesProjection := by
  refine ⟨?_, ?_⟩
  · intro hLaws
    have hMeans := congrArg (fun law : Measure StandardizedState => ∫ state, state ∂law) hLaws
    simp only [hiddenInitialLaw, Bool.false_eq_true, ↓reduceIte,
      integral_id_multivariateGaussian, add_zero] at hMeans
    have hContrast : hiddenContrast = 0 := by
      apply add_left_cancel (a := allOnesEmbedding center)
      simpa only [add_zero] using hMeans.symm
    exact hiddenContrast_ne_zero hContrast
  · rw [full_transition_projection, full_transition_projection,
      hiddenInitialLaw_projection, hiddenInitialLaw_projection]

end HiddenMode

/-! ## Exact two-step Boolean controls and attained feedback risk -/

open FEPComposed.GaussianControl FEP.ScalarGaussianSemigroup

/-- Frozen control duration; the two decisions have the same time budget. -/
def controlDuration : ℝ≥0 := 1 / 4

def controlDecay : ℝ := Real.exp (-(1 / 2 : ℝ))

theorem controlDecay_bounds : 0 < controlDecay ∧ controlDecay < 1 := by
  exact ⟨Real.exp_pos _, by rw [controlDecay, Real.exp_lt_one_iff]; norm_num⟩

def actionCenter (action : Bool) : ℝ := if action then 1 else -1

/-- Both actions use the same accepted diffusion, rate, duration and loss.
Only the all-ones scalar center changes. -/
def controlModel : FiniteGaussianControlModel Bool where
  dynamics action := FEP.H3ReferenceModel.scalarParameters (actionCenter action)
  duration := controlDuration
  duration_pos := by norm_num [controlDuration]
  target := 0
  actionPenalty _ := 0

def firstFilter (action : Bool) (noise : ℝ≥0) (hNoise : 0 < noise) :
    ScalarGaussianFilterModel :=
  observationFilter (actionCenter action) controlDuration noise hNoise

private theorem control_decay (action : Bool) :
    (controlModel.dynamics action).decay controlModel.duration = controlDecay := by
  rcases FEP.H3ReferenceModel.scalarParameters_exact (actionCenter action) with ⟨hRate, _⟩
  change Real.exp (-((FEP.H3ReferenceModel.scalarParameters (actionCenter action)).rate : ℝ) *
    (controlDuration : ℝ)) = _
  rw [hRate]
  norm_num [controlDuration, controlDecay]

private theorem control_transitionVariance (action : Bool) :
    ((controlModel.dynamics action).transitionVariance controlModel.duration : ℝ) =
      (1 - controlDecay ^ 2) / 2 := by
  change ((controlModel.dynamics action).stationaryVariance : ℝ) *
    (1 - (controlModel.dynamics action).decay controlModel.duration ^ 2) = _
  rw [control_decay]
  rcases FEP.H3ReferenceModel.scalarParameters_exact (actionCenter action) with ⟨hRate, hD⟩
  change (FEP.H3ReferenceModel.scalarParameters (actionCenter action)).diffusionVarianceRate /
    (2 * ((FEP.H3ReferenceModel.scalarParameters (actionCenter action)).rate : ℝ)) *
      (1 - controlDecay ^ 2) = _
  rw [hRate, hD]
  norm_num
  ring

private theorem first_prediction (action : Bool) (noise : ℝ≥0) (hNoise : 0 < noise) :
    (predictionBelief (firstFilter action noise hNoise) (prior 0)).mean =
        (1 - controlDecay) * actionCenter action ∧
      (predictionBelief (firstFilter action noise hNoise) (prior 0)).family.variance = 1 / 2 := by
  constructor
  · change (controlModel.dynamics action).transitionMean controlModel.duration 0 = _
    change (controlModel.dynamics action).center +
      (controlModel.dynamics action).decay controlModel.duration *
        (0 - (controlModel.dynamics action).center) = _
    rw [control_decay]
    change actionCenter action + controlDecay * (0 - actionCenter action) = _
    ring
  · apply NNReal.eq
    change (controlModel.dynamics action).decay controlModel.duration ^ 2 * (1 / 2 : ℝ) +
      ((controlModel.dynamics action).transitionVariance controlModel.duration : ℝ) = _
    rw [control_decay, control_transitionVariance]
    norm_num
    ring

/-- Derived first-observation posterior mean, with no action-dependent reset. -/
def controlPosteriorMean (first : Bool) (noise : ℝ≥0) (observation : ℝ) : ℝ :=
  let predicted := (1 - controlDecay) * actionCenter first
  predicted + ((1 / 2 : ℝ) / (1 / 2 + noise)) * (observation - predicted)

def controlPosteriorVariance (noise : ℝ≥0) : ℝ≥0 :=
  (1 / 2) * noise / (1 / 2 + noise)

private theorem first_posterior (first : Bool) (noise : ℝ≥0) (hNoise : 0 < noise)
    (observation : ℝ) :
    posteriorMean (firstFilter first noise hNoise) (prior 0) observation =
        controlPosteriorMean first noise observation ∧
      posteriorVariance (firstFilter first noise hNoise) (prior 0) =
        controlPosteriorVariance noise := by
  rcases first_prediction first noise hNoise with ⟨hMean, hVariance⟩
  simp only [posteriorMean, gain, innovationVariance, hMean, hVariance,
    posteriorVariance]
  constructor <;> rfl

/-- Risk of the actual composed posterior-to-terminal law. -/
def secondRisk (first : Bool) (noise : ℝ≥0) (hNoise : 0 < noise)
    (observation : ℝ) (second : Bool) : ℝ :=
  filteredQuadraticRisk controlModel (firstFilter first noise hNoise) (prior 0)
    observation second

theorem secondRisk_closedForm (first second : Bool) (noise : ℝ≥0) (hNoise : 0 < noise)
    (observation : ℝ) :
    secondRisk first noise hNoise observation second =
      controlDecay ^ 2 * (controlPosteriorVariance noise : ℝ) +
        (1 - controlDecay ^ 2) / 2 +
        (controlDecay * controlPosteriorMean first noise observation +
          (1 - controlDecay) * actionCenter second) ^ 2 := by
  rw [secondRisk, filteredQuadraticRisk, quadraticActionRisk_eq_closedForm]
  simp only [controlledVariance, controlledMean, NNReal.coe_add, NNReal.coe_mul,
    NNReal.coe_mk, controlModel, sub_zero, NNReal.coe_zero, add_zero,
    posteriorBelief, posteriorFamily]
  rw [(first_posterior first noise hNoise observation).1,
    (first_posterior first noise hNoise observation).2]
  change (controlModel.dynamics second).decay controlModel.duration ^ 2 *
      (controlPosteriorVariance noise : ℝ) +
      ((controlModel.dynamics second).transitionVariance controlModel.duration : ℝ) +
      ((controlModel.dynamics second).transitionMean controlModel.duration
        (controlPosteriorMean first noise observation)) ^ 2 = _
  rw [control_decay, control_transitionVariance]
  rw [ScalarOUParameters.transitionMean, control_decay]
  change _ + _ + (actionCenter second + controlDecay *
      (controlPosteriorMean first noise observation - actionCenter second)) ^ 2 = _
  ring

private theorem measurable_secondRisk (first second : Bool) (noise : ℝ≥0)
    (hNoise : 0 < noise) : Measurable (fun observation =>
      secondRisk first noise hNoise observation second) := by
  simp_rw [secondRisk_closedForm]
  unfold controlPosteriorMean
  fun_prop

/-- Explicit measurable second decision; equality goes to `false`. -/
def optimalSecond (first : Bool) (noise : ℝ≥0) (hNoise : 0 < noise)
    (observation : ℝ) : Bool :=
  if secondRisk first noise hNoise observation false ≤
      secondRisk first noise hNoise observation true then false else true

theorem measurable_optimalSecond (first : Bool) (noise : ℝ≥0) (hNoise : 0 < noise) :
    Measurable (optimalSecond first noise hNoise) := by
  apply Measurable.ite
    (measurableSet_le (measurable_secondRisk first false noise hNoise)
      (measurable_secondRisk first true noise hNoise)) measurable_const measurable_const

theorem optimalSecond_le (first second : Bool) (noise : ℝ≥0) (hNoise : 0 < noise)
    (observation : ℝ) :
    secondRisk first noise hNoise observation (optimalSecond first noise hNoise observation) ≤
      secondRisk first noise hNoise observation second := by
  unfold optimalSecond
  split_ifs with h <;> cases second
  · exact le_rfl
  · exact h
  · exact le_of_lt (lt_of_not_ge h)
  · exact le_rfl

/-- Primitive two-step policy inputs. No minimum or risk theorem is a field. -/
structure TwoStepPolicy where
  first : Bool
  second : ℝ → Bool
  measurable_second : Measurable second

def policyRisk (noise : ℝ≥0) (hNoise : 0 < noise) (policy : TwoStepPolicy) : ℝ :=
  ∫ observation, secondRisk policy.first noise hNoise observation (policy.second observation)
    ∂evidenceLaw (firstFilter policy.first noise hNoise) (prior 0)

/-- Named Gaussian L2 leaf with explicit law, independent of filter unfolding. -/
private theorem gaussian_centeredAffine_memLp (mean : ℝ) (variance : ℝ≥0)
    (offset coefficient : ℝ) :
    MemLp (fun observation : ℝ => offset + coefficient * (observation - offset))
      2 (gaussianReal mean variance) := by
  have hIdentity : MemLp (fun observation : ℝ => observation) 2
      (gaussianReal mean variance) := memLp_id_gaussianReal 2
  have hConstant : MemLp (fun _ : ℝ => offset) 2
      (gaussianReal mean variance) := memLp_const offset
  exact hConstant.add ((hIdentity.sub hConstant).const_mul coefficient)

/-- Isolate the actual posterior affine formula from the terminal square. -/
private theorem controlPosteriorMean_memLp (first : Bool) (noise : ℝ≥0)
    (mean : ℝ) (variance : ℝ≥0) :
    MemLp (controlPosteriorMean first noise) 2 (gaussianReal mean variance) := by
  exact gaussian_centeredAffine_memLp mean variance
    ((1 - controlDecay) * actionCenter first) ((1 / 2 : ℝ) / (1 / 2 + noise))

private theorem secondRisk_integrable (first second : Bool) (noise : ℝ≥0)
    (hNoise : 0 < noise) : Integrable
      (fun observation => secondRisk first noise hNoise observation second)
      (evidenceLaw (firstFilter first noise hNoise) (prior 0)) := by
  rw [evidenceLaw_eq_gaussian]
  change Integrable (fun observation => secondRisk first noise hNoise observation second)
    (gaussianReal (predictionBelief (firstFilter first noise hNoise) (prior 0)).mean
      (innovationVariance (firstFilter first noise hNoise) (prior 0)))
  have hMean := controlPosteriorMean_memLp first noise
    (predictionBelief (firstFilter first noise hNoise) (prior 0)).mean
    (innovationVariance (firstFilter first noise hNoise) (prior 0))
  have hTerminalMean : MemLp (fun observation =>
      controlDecay * controlPosteriorMean first noise observation +
        (1 - controlDecay) * actionCenter second) 2
      (gaussianReal (predictionBelief (firstFilter first noise hNoise) (prior 0)).mean
        (innovationVariance (firstFilter first noise hNoise) (prior 0))) :=
    (hMean.const_mul controlDecay).add (memLp_const _)
  simp_rw [secondRisk_closedForm]
  exact (integrable_const (controlDecay ^ 2 * (controlPosteriorVariance noise : ℝ) +
    (1 - controlDecay ^ 2) / 2)).add hTerminalMean.integrable_sq

private theorem policy_secondRisk_integrable (noise : ℝ≥0) (hNoise : 0 < noise)
    (policy : TwoStepPolicy) : Integrable
      (fun observation => secondRisk policy.first noise hNoise observation (policy.second observation))
      (evidenceLaw (firstFilter policy.first noise hNoise) (prior 0)) := by
  have hs : MeasurableSet {observation | policy.second observation = false} :=
    (measurableSet_singleton false).preimage policy.measurable_second
  have hPiece := Integrable.piecewise hs.nullMeasurableSet
    (secondRisk_integrable policy.first false noise hNoise).integrableOn
    (secondRisk_integrable policy.first true noise hNoise).integrableOn
  apply hPiece.congr
  filter_upwards with observation
  cases h : policy.second observation <;> simp [Set.piecewise, h]

def feedbackPolicy (first : Bool) (noise : ℝ≥0) (hNoise : 0 < noise) : TwoStepPolicy :=
  ⟨first, optimalSecond first noise hNoise, measurable_optimalSecond first noise hNoise⟩

def optimalPolicy (noise : ℝ≥0) (hNoise : 0 < noise) : TwoStepPolicy :=
  feedbackPolicy (if policyRisk noise hNoise (feedbackPolicy false noise hNoise) ≤
    policyRisk noise hNoise (feedbackPolicy true noise hNoise) then false else true) noise hNoise

/-- The explicit measurable feedback policy attains the minimum over the full
primitive two-step class at the same native law, loss and time budget. -/
theorem policy_attainment (noise : ℝ≥0) (hNoise : 0 < noise) (policy : TwoStepPolicy) :
    policyRisk noise hNoise (optimalPolicy noise hNoise) ≤ policyRisk noise hNoise policy := by
  have hSecond : policyRisk noise hNoise (feedbackPolicy policy.first noise hNoise) ≤
      policyRisk noise hNoise policy := by
    exact integral_mono (policy_secondRisk_integrable noise hNoise _)
      (policy_secondRisk_integrable noise hNoise policy)
      (fun observation => optimalSecond_le policy.first (policy.second observation)
        noise hNoise observation)
  apply le_trans _ hSecond
  unfold optimalPolicy
  split_ifs with h <;> cases policy.first
  · exact le_rfl
  · exact h
  · exact le_of_lt (lt_of_not_ge h)
  · exact le_rfl

def openLoopPolicy (first second : Bool) : TwoStepPolicy :=
  ⟨first, fun _ => second, measurable_const⟩

/-- All four fixed action pairs are in the same attained policy class. -/
theorem policy_containment (noise : ℝ≥0) (hNoise : 0 < noise) (first second : Bool) :
    policyRisk noise hNoise (optimalPolicy noise hNoise) ≤
      policyRisk noise hNoise (openLoopPolicy first second) :=
  policy_attainment noise hNoise _

/-! ## Native Gaussian information prerequisites -/

private def gaussianLogNormalizer (variance referenceVariance : ℝ≥0) : ℝ :=
  Real.log (Real.sqrt (2 * Real.pi * (referenceVariance : ℝ))) -
    Real.log (Real.sqrt (2 * Real.pi * (variance : ℝ)))

private def gaussianLogRatio (mean referenceMean : ℝ)
    (variance referenceVariance : ℝ≥0) (value : ℝ) : ℝ :=
  gaussianLogNormalizer variance referenceVariance +
    (value - referenceMean) ^ 2 / (2 * (referenceVariance : ℝ)) -
    (value - mean) ^ 2 / (2 * (variance : ℝ))

private theorem gaussianLogRatio_density (mean referenceMean : ℝ)
    (variance referenceVariance : ℝ≥0) (hVariance : 0 < variance)
    (hReferenceVariance : 0 < referenceVariance) (value : ℝ) :
    Real.log (gaussianPDFReal mean variance value /
      gaussianPDFReal referenceMean referenceVariance value) =
        gaussianLogRatio mean referenceMean variance referenceVariance value := by
  rw [Real.log_div (gaussianPDFReal_pos mean variance value hVariance.ne').ne'
    (gaussianPDFReal_pos referenceMean referenceVariance value hReferenceVariance.ne').ne',
    gaussianPDFReal_def, gaussianPDFReal_def,
    Real.log_mul (by positivity) (Real.exp_ne_zero _),
    Real.log_mul (by positivity) (Real.exp_ne_zero _),
    Real.log_inv, Real.log_inv, Real.log_exp, Real.log_exp]
  unfold gaussianLogRatio gaussianLogNormalizer
  ring

private theorem gaussianLogRatio_ae (mean referenceMean : ℝ)
    (variance referenceVariance : ℝ≥0) (hVariance : 0 < variance)
    (hReferenceVariance : 0 < referenceVariance) :
    llr (gaussianReal mean variance) (gaussianReal referenceMean referenceVariance)
      =ᵐ[gaussianReal mean variance]
        gaussianLogRatio mean referenceMean variance referenceVariance := by
  have hSourceVolume := gaussianReal_absolutelyContinuous mean hVariance.ne'
  have hReferenceVolume := gaussianReal_absolutelyContinuous referenceMean hReferenceVariance.ne'
  have hSourceReference := hSourceVolume.trans
    (gaussianReal_absolutelyContinuous' referenceMean hReferenceVariance.ne')
  filter_upwards [hSourceReference (Measure.rnDeriv_eq_div hSourceVolume hReferenceVolume),
    hSourceVolume (rnDeriv_gaussianReal mean variance),
    hSourceVolume (rnDeriv_gaussianReal referenceMean referenceVariance)]
      with value hRatio hSource hReference
  rw [llr, hRatio, hSource, hReference, ENNReal.toReal_div,
    toReal_gaussianPDF, toReal_gaussianPDF]
  exact gaussianLogRatio_density mean referenceMean variance referenceVariance
    hVariance hReferenceVariance value

private theorem gaussianLogRatio_integrable (mean referenceMean : ℝ)
    (variance referenceVariance : ℝ≥0) :
    Integrable (gaussianLogRatio mean referenceMean variance referenceVariance)
      (gaussianReal mean variance) := by
  have hIdentity : MemLp (fun value : ℝ => value) 2 (gaussianReal mean variance) :=
    memLp_id_gaussianReal 2
  have hSource := (hIdentity.sub (memLp_const mean)).integrable_sq
  have hReference := (hIdentity.sub (memLp_const referenceMean)).integrable_sq
  exact ((integrable_const (gaussianLogNormalizer variance referenceVariance)).add
    (hReference.div_const (2 * (referenceVariance : ℝ)))).sub
      (hSource.div_const (2 * (variance : ℝ)))

private theorem gaussian_centered_square_integral (mean : ℝ) (variance : ℝ≥0) :
    (∫ value, (value - mean) ^ 2 ∂gaussianReal mean variance) = variance := by
  have h := variance_eq_integral
    (μ := gaussianReal mean variance) (X := id) measurable_id.aemeasurable
  simpa only [variance_id_gaussianReal, integral_id_gaussianReal, id_eq] using h.symm

private theorem gaussian_square_integral (mean referenceMean : ℝ) (variance : ℝ≥0) :
    (∫ value, (value - referenceMean) ^ 2 ∂gaussianReal mean variance) =
      (variance : ℝ) + (mean - referenceMean) ^ 2 := by
  have hIdentity : MemLp (fun value : ℝ => value) 2 (gaussianReal mean variance) :=
    memLp_id_gaussianReal 2
  have hCentered := hIdentity.sub (memLp_const mean)
  have hLinear : Integrable (fun value : ℝ =>
      (2 * (mean - referenceMean)) * (value - mean)) (gaussianReal mean variance) :=
    (hCentered.integrable one_le_two).const_mul (2 * (mean - referenceMean))
  have hCenteredMean : (∫ value, value - mean ∂gaussianReal mean variance) = 0 := by
    rw [integral_sub (hIdentity.integrable one_le_two) (integrable_const mean),
      integral_id_gaussianReal, integral_const]
    simp
  calc
    _ = ∫ value, ((value - mean) ^ 2 +
          (2 * (mean - referenceMean)) * (value - mean)) + (mean - referenceMean) ^ 2
            ∂gaussianReal mean variance := by
      apply integral_congr_ae
      filter_upwards with value
      ring
    _ = _ := by
      rw [integral_add
          (f := fun value : ℝ => (value - mean) ^ 2 +
            (2 * (mean - referenceMean)) * (value - mean))
          (g := fun _ : ℝ => (mean - referenceMean) ^ 2)
          (hCentered.integrable_sq.add hLinear)
          (integrable_const ((mean - referenceMean) ^ 2)),
        integral_add (f := fun value : ℝ => (value - mean) ^ 2)
          (g := fun value : ℝ => (2 * (mean - referenceMean)) * (value - mean))
          hCentered.integrable_sq hLinear,
        integral_const_mul, hCenteredMean, mul_zero,
        gaussian_centered_square_integral, integral_const]
      simp

private theorem gaussianLogNormalizer_eq (variance referenceVariance : ℝ≥0)
    (hVariance : 0 < variance) (hReferenceVariance : 0 < referenceVariance) :
    gaussianLogNormalizer variance referenceVariance =
      Real.log ((referenceVariance : ℝ) / variance) / 2 := by
  unfold gaussianLogNormalizer
  rw [Real.log_sqrt (by positivity), Real.log_sqrt (by positivity),
    Real.log_mul (by positivity : (2 * Real.pi) ≠ 0)
      (by positivity : (referenceVariance : ℝ) ≠ 0),
    Real.log_mul (by positivity : (2 * Real.pi) ≠ 0)
      (by positivity : (variance : ℝ) ≠ 0),
    Real.log_div (by positivity : (referenceVariance : ℝ) ≠ 0)
      (by positivity : (variance : ℝ) ≠ 0)]
  ring

/-- Native positive unequal-variance Gaussian KL, including the actual RN
binding and Gaussian quadratic integrability. Private prerequisite for the
case study's actual channel information; a log-determinant expression alone
is never used as native divergence evidence. -/
private theorem gaussian_klDiv (mean referenceMean : ℝ)
    (variance referenceVariance : ℝ≥0) (hVariance : 0 < variance)
    (hReferenceVariance : 0 < referenceVariance) :
    klDiv (gaussianReal mean variance) (gaussianReal referenceMean referenceVariance) =
      ENNReal.ofReal ((1 / 2 : ℝ) *
        (Real.log ((referenceVariance : ℝ) / variance) +
          ((variance : ℝ) + (mean - referenceMean) ^ 2) / referenceVariance - 1)) := by
  have hSourceReference := (gaussianReal_absolutelyContinuous mean hVariance.ne').trans
    (gaussianReal_absolutelyContinuous' referenceMean hReferenceVariance.ne')
  have hLLR := gaussianLogRatio_ae mean referenceMean variance referenceVariance
    hVariance hReferenceVariance
  have hIntegrable : Integrable
      (llr (gaussianReal mean variance) (gaussianReal referenceMean referenceVariance))
      (gaussianReal mean variance) :=
    (integrable_congr hLLR).mpr (gaussianLogRatio_integrable _ _ _ _)
  rw [klDiv_of_ac_of_integrable hSourceReference hIntegrable,
    integral_congr_ae hLLR]
  have hIdentity : MemLp (fun value : ℝ => value) 2 (gaussianReal mean variance) :=
    memLp_id_gaussianReal 2
  have hSource := (hIdentity.sub (memLp_const mean)).integrable_sq
  have hReference := (hIdentity.sub (memLp_const referenceMean)).integrable_sq
  simp only [gaussianLogRatio]
  rw [integral_sub
      (f := fun value : ℝ => gaussianLogNormalizer variance referenceVariance +
        (value - referenceMean) ^ 2 / (2 * (referenceVariance : ℝ)))
      (g := fun value : ℝ => (value - mean) ^ 2 / (2 * (variance : ℝ)))
      ((integrable_const (gaussianLogNormalizer variance referenceVariance)).add
      (hReference.div_const (2 * (referenceVariance : ℝ))))
      (hSource.div_const (2 * (variance : ℝ))),
    integral_add (f := fun _ : ℝ => gaussianLogNormalizer variance referenceVariance)
      (g := fun value : ℝ => (value - referenceMean) ^ 2 / (2 * (referenceVariance : ℝ)))
      (integrable_const (gaussianLogNormalizer variance referenceVariance))
      (hReference.div_const (2 * (referenceVariance : ℝ))),
    integral_const, integral_div, integral_div,
    gaussian_square_integral, gaussian_centered_square_integral,
    gaussianLogNormalizer_eq variance referenceVariance hVariance hReferenceVariance]
  simp only [probReal_univ, one_smul]
  congr 1
  have hv : (variance : ℝ) ≠ 0 := by exact_mod_cast hVariance.ne'
  have hw : (referenceVariance : ℝ) ≠ 0 := by exact_mod_cast hReferenceVariance.ne'
  field_simp
  ring

def informationJoint (model : ScalarGaussianFilterModel)
    (belief : ScalarGaussianBelief) : Measure (ℝ × ℝ) :=
  (predictionBelief model belief).law ⊗ₘ observationKernel model

def informationIndependent (model : ScalarGaussianFilterModel)
    (belief : ScalarGaussianBelief) : Measure (ℝ × ℝ) :=
  (predictionBelief model belief).law.prod (evidenceLaw model belief)

instance informationJoint_probability (model : ScalarGaussianFilterModel)
    (belief : ScalarGaussianBelief) : IsProbabilityMeasure (informationJoint model belief) := by
  unfold informationJoint
  infer_instance

instance informationIndependent_probability (model : ScalarGaussianFilterModel)
    (belief : ScalarGaussianBelief) : IsProbabilityMeasure (informationIndependent model belief) := by
  unfold informationIndependent evidenceLaw
  infer_instance

private theorem informationIndependent_eq_marginals
    (model : ScalarGaussianFilterModel) (belief : ScalarGaussianBelief) :
    informationIndependent model belief =
      (informationJoint model belief).fst.prod (informationJoint model belief).snd := by
  simp only [informationIndependent, informationJoint,
    Measure.fst_compProd, Measure.snd_compProd, evidenceLaw]

private theorem informationJoint_eq_withDensity
    (model : ScalarGaussianFilterModel) (belief : ScalarGaussianBelief) :
    informationJoint model belief =
      (volume.prod volume).withDensity (fun pair : ℝ × ℝ =>
        gaussianPDF (predictionBelief model belief).mean
            (predictionBelief model belief).family.variance pair.1 *
          gaussianPDF pair.1 model.observationNoise.variance pair.2) := by
  have hKernel : observationKernel model =
      (Kernel.const ℝ volume).withDensity
        (fun state observation => gaussianPDF state model.observationNoise.variance observation) := by
    ext state
    rw [observationKernel_apply, FixedVarianceGaussian.law_eq_withDensity,
      Kernel.withDensity_apply]
    · rfl
    · fun_prop
  unfold informationJoint
  rw [hKernel, ScalarGaussianBelief.law, FixedVarianceGaussian.law_eq_withDensity]
  let _ : IsSFiniteKernel
      ((Kernel.const ℝ volume).withDensity
        (fun state observation => gaussianPDF state model.observationNoise.variance observation)) :=
    Kernel.IsSFiniteKernel.withDensity _ (fun _ _ => gaussianPDF_ne_top)
  have hDensity : Measurable
      ((predictionBelief model belief).family.density (predictionBelief model belief).mean) := by
    unfold FixedVarianceGaussian.density
    fun_prop
  rw [Measure.compProd_withDensity (by fun_prop), Measure.compProd_const,
    prod_withDensity_left hDensity]
  simp only [FixedVarianceGaussian.density]
  rw [← withDensity_mul (volume.prod volume) (by fun_prop) (by fun_prop)]
  rfl

private theorem informationIndependent_eq_withDensity
    (model : ScalarGaussianFilterModel) (belief : ScalarGaussianBelief) :
    informationIndependent model belief =
      (volume.prod volume).withDensity (fun pair : ℝ × ℝ =>
        gaussianPDF (predictionBelief model belief).mean
            (predictionBelief model belief).family.variance pair.1 *
          gaussianPDF (predictionBelief model belief).mean
            (innovationVariance model belief) pair.2) := by
  rw [informationIndependent, evidenceLaw_eq_gaussian,
    ScalarGaussianBelief.law, FixedVarianceGaussian.law_eq_withDensity,
    FixedVarianceGaussian.law_eq_withDensity]
  simp only [FixedVarianceGaussian.density]
  rw [prod_withDensity (by fun_prop) (by fun_prop)]
  rfl

private theorem informationJoint_llr
    (model : ScalarGaussianFilterModel) (belief : ScalarGaussianBelief) :
    llr (informationJoint model belief) (informationIndependent model belief)
      =ᵐ[informationJoint model belief] fun pair : ℝ × ℝ =>
        gaussianLogRatio pair.1 (predictionBelief model belief).mean
          model.observationNoise.variance (innovationVariance model belief) pair.2 := by
  let dominating : Measure (ℝ × ℝ) := volume.prod volume
  have hSource : informationJoint model belief ≪ dominating := by
    rw [informationJoint_eq_withDensity]
    exact withDensity_absolutelyContinuous _ _
  have hReference : informationIndependent model belief ≪ dominating := by
    rw [informationIndependent_eq_withDensity]
    exact withDensity_absolutelyContinuous _ _
  have hDominatingReference : dominating ≪ informationIndependent model belief := by
    rw [informationIndependent_eq_withDensity]
    apply withDensity_absolutelyContinuous' (by fun_prop)
    apply ae_of_all
    intro pair
    exact mul_ne_zero
      (gaussianPDF_pos _ (predictionBelief model belief).family.variance_pos.ne' _).ne'
      (gaussianPDF_pos _ (innovationVariance_pos model belief).ne' _).ne'
  have hSourceReference := hSource.trans hDominatingReference
  have hSourceDerivative :
      (informationJoint model belief).rnDeriv dominating =ᵐ[dominating]
        fun pair : ℝ × ℝ =>
          gaussianPDF (predictionBelief model belief).mean
              (predictionBelief model belief).family.variance pair.1 *
            gaussianPDF pair.1 model.observationNoise.variance pair.2 := by
    rw [informationJoint_eq_withDensity]
    exact Measure.rnDeriv_withDensity dominating (by fun_prop)
  have hReferenceDerivative :
      (informationIndependent model belief).rnDeriv dominating =ᵐ[dominating]
        fun pair : ℝ × ℝ =>
          gaussianPDF (predictionBelief model belief).mean
              (predictionBelief model belief).family.variance pair.1 *
            gaussianPDF (predictionBelief model belief).mean
              (innovationVariance model belief) pair.2 := by
    rw [informationIndependent_eq_withDensity]
    exact Measure.rnDeriv_withDensity dominating (by fun_prop)
  filter_upwards [hSourceReference (Measure.rnDeriv_eq_div hSource hReference),
    hSource hSourceDerivative, hSource hReferenceDerivative]
      with pair hRatio hPriorChannel hPriorEvidence
  rw [llr, hRatio, hPriorChannel, hPriorEvidence,
    ENNReal.toReal_div, ENNReal.toReal_mul, ENNReal.toReal_mul,
    toReal_gaussianPDF, toReal_gaussianPDF, toReal_gaussianPDF]
  rw [mul_div_mul_left _ _
    (gaussianPDFReal_pos _ _ pair.1
      (predictionBelief model belief).family.variance_pos.ne').ne']
  exact gaussianLogRatio_density pair.1 (predictionBelief model belief).mean
    model.observationNoise.variance (innovationVariance model belief)
    model.observationNoise.variance_pos (innovationVariance_pos model belief) pair.2

private theorem informationNoiseSquare_integrable
    (model : ScalarGaussianFilterModel) (belief : ScalarGaussianBelief) :
    Integrable (fun pair : ℝ × ℝ => (pair.2 - pair.1) ^ 2)
      (informationJoint model belief) := by
  unfold informationJoint
  apply (Measure.integrable_compProd_iff (by fun_prop)).mpr
  constructor
  · apply ae_of_all
    intro state
    change Integrable (fun observation : ℝ => (observation - state) ^ 2)
      (gaussianReal state model.observationNoise.variance)
    have hIdentity : MemLp (fun observation : ℝ => observation) 2
        (gaussianReal state model.observationNoise.variance) := memLp_id_gaussianReal 2
    exact (hIdentity.sub (memLp_const state)).integrable_sq
  · have hOuter : (fun state : ℝ =>
        ∫ observation, ‖(observation - state) ^ 2‖ ∂observationKernel model state) =
        fun _ => (model.observationNoise.variance : ℝ) := by
      funext state
      change (∫ observation, ‖(observation - state) ^ 2‖
        ∂gaussianReal state model.observationNoise.variance) = _
      simp only [Real.norm_eq_abs, abs_sq]
      exact gaussian_centered_square_integral state model.observationNoise.variance
    rw [hOuter]
    exact integrable_const _

private theorem informationNoiseSquare_integral
    (model : ScalarGaussianFilterModel) (belief : ScalarGaussianBelief) :
    (∫ pair : ℝ × ℝ, (pair.2 - pair.1) ^ 2 ∂informationJoint model belief) =
      model.observationNoise.variance := by
  rw [informationJoint, Measure.integral_compProd
    (informationNoiseSquare_integrable model belief)]
  change (∫ state, (∫ observation, (observation - state) ^ 2
    ∂gaussianReal state model.observationNoise.variance)
      ∂(predictionBelief model belief).law) = _
  simp only [gaussian_centered_square_integral]
  simp

private theorem informationEvidence_marginal
    (model : ScalarGaussianFilterModel) (belief : ScalarGaussianBelief) :
    (informationJoint model belief).map Prod.snd =
      gaussianReal (predictionBelief model belief).mean (innovationVariance model belief) := by
  change (informationJoint model belief).snd = _
  rw [informationJoint, Measure.snd_compProd]
  exact evidenceLaw_eq_gaussian model belief

private theorem informationEvidenceSquare_integrable
    (model : ScalarGaussianFilterModel) (belief : ScalarGaussianBelief) :
    Integrable (fun pair : ℝ × ℝ => (pair.2 - (predictionBelief model belief).mean) ^ 2)
      (informationJoint model belief) := by
  have hIdentity : MemLp (fun observation : ℝ => observation) 2
      (gaussianReal (predictionBelief model belief).mean (innovationVariance model belief)) :=
    memLp_id_gaussianReal 2
  have hSquare :=
    (hIdentity.sub (memLp_const (predictionBelief model belief).mean)).integrable_sq
  rw [← informationEvidence_marginal model belief] at hSquare
  exact hSquare.comp_measurable measurable_snd

private theorem informationEvidenceSquare_integral
    (model : ScalarGaussianFilterModel) (belief : ScalarGaussianBelief) :
    (∫ pair : ℝ × ℝ, (pair.2 - (predictionBelief model belief).mean) ^ 2
      ∂informationJoint model belief) = innovationVariance model belief := by
  have hMap :
      (∫ observation : ℝ, (observation - (predictionBelief model belief).mean) ^ 2
        ∂(informationJoint model belief).map Prod.snd) =
      (∫ pair : ℝ × ℝ, (pair.2 - (predictionBelief model belief).mean) ^ 2
        ∂informationJoint model belief) :=
    integral_map (by fun_prop) (by fun_prop)
  rw [← hMap, informationEvidence_marginal]
  exact gaussian_centered_square_integral _ _

/-- Positive native Gaussian densities give absolute continuity of the
actual state-observation joint with respect to its independent marginals. -/
private theorem informationJoint_ac
    (model : ScalarGaussianFilterModel) (belief : ScalarGaussianBelief) :
    informationJoint model belief ≪ informationIndependent model belief := by
  have hSource : informationJoint model belief ≪ volume.prod volume := by
    rw [informationJoint_eq_withDensity]
    exact withDensity_absolutelyContinuous _ _
  apply hSource.trans
  rw [informationIndependent_eq_withDensity]
  apply withDensity_absolutelyContinuous' (by fun_prop)
  apply ae_of_all
  intro pair
  exact mul_ne_zero
    (gaussianPDF_pos _ (predictionBelief model belief).family.variance_pos.ne' _).ne'
    (gaussianPDF_pos _ (innovationVariance_pos model belief).ne' _).ne'

/-- Native KL between the actual scalar state-observation channel joint and
the product of its actual marginals, derived from its log ratio and moments. -/
theorem information_native_mutualInformation
    (model : ScalarGaussianFilterModel) (belief : ScalarGaussianBelief) :
    klDiv (informationJoint model belief)
        ((informationJoint model belief).fst.prod (informationJoint model belief).snd) =
      ENNReal.ofReal ((1 / 2 : ℝ) * Real.log
        (1 + ((predictionBelief model belief).family.variance : ℝ) /
          (model.observationNoise.variance : ℝ))) := by
  rw [← informationIndependent_eq_marginals]
  have hNoise := informationNoiseSquare_integrable model belief
  have hEvidence := informationEvidenceSquare_integrable model belief
  have hLLR := informationJoint_llr model belief
  have hExpression : Integrable
      (fun pair : ℝ × ℝ => gaussianLogRatio pair.1
        (predictionBelief model belief).mean model.observationNoise.variance
        (innovationVariance model belief) pair.2) (informationJoint model belief) := by
    unfold gaussianLogRatio
    exact ((integrable_const _).add
      (hEvidence.div_const (2 * (innovationVariance model belief : ℝ)))).sub
        (hNoise.div_const (2 * (model.observationNoise.variance : ℝ)))
  have hIntegrable : Integrable
      (llr (informationJoint model belief) (informationIndependent model belief))
      (informationJoint model belief) :=
    (integrable_congr hLLR).mpr hExpression
  have hR : (model.observationNoise.variance : ℝ) ≠ 0 := by
    exact_mod_cast model.observationNoise.variance_pos.ne'
  have hS : (innovationVariance model belief : ℝ) ≠ 0 := by
    exact_mod_cast (innovationVariance_pos model belief).ne'
  have hIntegral :
      (∫ pair : ℝ × ℝ, gaussianLogRatio pair.1
        (predictionBelief model belief).mean model.observationNoise.variance
        (innovationVariance model belief) pair.2 ∂informationJoint model belief) =
      gaussianLogNormalizer model.observationNoise.variance
        (innovationVariance model belief) := by
    unfold gaussianLogRatio
    rw [integral_sub
        (f := fun pair : ℝ × ℝ => gaussianLogNormalizer model.observationNoise.variance
          (innovationVariance model belief) +
            (pair.2 - (predictionBelief model belief).mean) ^ 2 /
              (2 * (innovationVariance model belief : ℝ)))
        (g := fun pair : ℝ × ℝ => (pair.2 - pair.1) ^ 2 /
          (2 * (model.observationNoise.variance : ℝ)))
        ((integrable_const (gaussianLogNormalizer model.observationNoise.variance
        (innovationVariance model belief))).add
        (hEvidence.div_const (2 * (innovationVariance model belief : ℝ))))
        (hNoise.div_const (2 * (model.observationNoise.variance : ℝ))),
      integral_add
        (f := fun _ : ℝ × ℝ => gaussianLogNormalizer model.observationNoise.variance
          (innovationVariance model belief))
        (g := fun pair : ℝ × ℝ => (pair.2 - (predictionBelief model belief).mean) ^ 2 /
          (2 * (innovationVariance model belief : ℝ)))
        (integrable_const (gaussianLogNormalizer model.observationNoise.variance
        (innovationVariance model belief)))
        (hEvidence.div_const (2 * (innovationVariance model belief : ℝ))),
      integral_const, integral_div, integral_div,
      informationEvidenceSquare_integral, informationNoiseSquare_integral]
    simp only [probReal_univ, one_smul]
    field_simp [hR, hS]
    ring
  rw [klDiv_of_ac_of_integrable (informationJoint_ac model belief) hIntegrable,
    integral_congr_ae hLLR, hIntegral]
  simp only [probReal_univ, add_sub_cancel_right]
  congr 1
  rw [gaussianLogNormalizer_eq model.observationNoise.variance
    (innovationVariance model belief) model.observationNoise.variance_pos
    (innovationVariance_pos model belief)]
  have hRatio : (innovationVariance model belief : ℝ) /
      (model.observationNoise.variance : ℝ) =
      1 + ((predictionBelief model belief).family.variance : ℝ) /
        (model.observationNoise.variance : ℝ) := by
    change (((predictionBelief model belief).family.variance : ℝ) +
        (model.observationNoise.variance : ℝ)) /
      (model.observationNoise.variance : ℝ) = _
    field_simp [hR]
    ring
  rw [hRatio]
  ring

section SensoryClampNative
open FEP.Fin4GaussianSemigroup FEP.Fin4GaussianSemigroup.Axis

instance sensoryStationary_isGaussian (center : StandardizedState) :
    IsGaussian (stationaryLaw center) := by
  rw [stationaryLaw_eq_gaussian]
  infer_instance

def sensoryEndpointAxis : Bool → Axis
  | false => external
  | true => internal

def sensoryVector : StandardizedState := EuclideanSpace.single sensory 1

def sensoryEndpointVector (index : Bool) : StandardizedState :=
  EuclideanSpace.single (sensoryEndpointAxis index) 1 -
    (2 / 7 : ℝ) • sensoryVector

def sensoryCentered (center state : StandardizedState) : ℝ :=
  ⟪sensoryVector, state - center⟫

def sensoryResidual (center : StandardizedState) (index : Bool)
    (state : StandardizedState) : ℝ :=
  ⟪sensoryEndpointVector index, state - center⟫

def sensoryResidualPair (center state : StandardizedState) : ℝ × ℝ :=
  (sensoryResidual center false state, sensoryResidual center true state)

def sensoryEndpoints (state : StandardizedState) : ℝ × ℝ :=
  (state external, state internal)

def sensoryConditionalMean (center : StandardizedState) (index : Bool)
    (datum : ℝ) : ℝ :=
  center (sensoryEndpointAxis index) + (2 / 7 : ℝ) * (datum - center sensory)

@[fun_prop] private theorem measurable_sensoryCentered (center : StandardizedState) :
    Measurable (sensoryCentered center) := by unfold sensoryCentered; fun_prop

@[fun_prop] private theorem measurable_sensoryResidual (center : StandardizedState) (index : Bool) :
    Measurable (sensoryResidual center index) := by unfold sensoryResidual; fun_prop

@[fun_prop] private theorem measurable_sensoryResidualPair (center : StandardizedState) :
    Measurable (sensoryResidualPair center) := by unfold sensoryResidualPair; fun_prop

@[fun_prop] private theorem measurable_sensoryEndpoints : Measurable sensoryEndpoints := by
  unfold sensoryEndpoints
  fun_prop

private theorem sensoryResidual_eq (center state : StandardizedState) (index : Bool) :
    sensoryResidual center index state =
      state (sensoryEndpointAxis index) - sensoryConditionalMean center index (state sensory) := by
  simp only [sensoryResidual, sensoryEndpointVector, sensoryVector,
    inner_sub_left, real_inner_smul_left, EuclideanSpace.inner_single_left,
    map_one, one_mul, PiLp.sub_apply, sensoryConditionalMean]
  ring

private theorem sensoryCentered_hasGaussianLaw (center : StandardizedState) :
    HasGaussianLaw (fun state : StandardizedState => state - center)
      (stationaryLaw center) := ⟨by fun_prop, by infer_instance⟩

private theorem sensoryLinear_mean (center vector : StandardizedState) :
    (∫ state : StandardizedState, ⟪vector, state - center⟫ ∂stationaryLaw center) = 0 := by
  change (∫ state, (innerSL ℝ vector) (state - center) ∂stationaryLaw center) = 0
  rw [(innerSL ℝ vector).integral_comp_comm
      (sensoryCentered_hasGaussianLaw center).integrable,
    integral_sub IsGaussian.integrable_fun_id (integrable_const _)]
  simp [stationaryLaw_eq_gaussian]

private theorem sensoryLinear_covariance (center left right : StandardizedState) :
    cov[fun state : StandardizedState => ⟪left, state - center⟫,
      fun state => ⟪right, state - center⟫; stationaryLaw center] =
        left.ofLp ⬝ᵥ Sigma *ᵥ right.ofLp := by
  simp only [inner_sub_right]
  have hLeft : Integrable (fun state : StandardizedState => ⟪left, state⟫)
      (stationaryLaw center) := by
    simpa only [Function.comp_def, id_eq, innerSL_apply_apply] using
      ((IsGaussian.hasGaussianLaw_id (μ := stationaryLaw center)).map
        (innerSL ℝ left)).integrable
  have hRight : Integrable (fun state : StandardizedState => ⟪right, state⟫)
      (stationaryLaw center) := by
    simpa only [Function.comp_def, id_eq, innerSL_apply_apply] using
      ((IsGaussian.hasGaussianLaw_id (μ := stationaryLaw center)).map
        (innerSL ℝ right)).integrable
  rw [covariance_sub_const_left hLeft, covariance_sub_const_right hRight,
    ← covarianceBilin_apply_eq_cov IsGaussian.memLp_two_id,
    stationaryLaw_eq_gaussian, covarianceBilin_multivariateGaussian Sigma_posDef.posSemidef]

private theorem sensory_residual_covariance_zero (center : StandardizedState) (index : Bool) :
    cov[sensoryCentered center, sensoryResidual center index; stationaryLaw center] = 0 := by
  change cov[(fun state : StandardizedState => ⟪sensoryVector, state - center⟫),
    (fun state => ⟪sensoryEndpointVector index, state - center⟫); stationaryLaw center] = 0
  rw [sensoryLinear_covariance]
  cases index <;>
    norm_num [sensoryEndpointVector, sensoryEndpointAxis, sensoryVector,
      dotProduct, Matrix.mulVec, sum_axis, Sigma_eq_entries, PiLp.single_apply]

/-- The actual native residual pair is correlated; its entries are derived
from Sigma and the 2/7 sensory regression, not stored in a certificate. -/
private theorem sensory_residual_covariance (center : StandardizedState) (left right : Bool) :
    cov[sensoryResidual center left, sensoryResidual center right; stationaryLaw center] =
      if left = right then (15 / 56 : ℝ) else (1 / 56 : ℝ) := by
  change cov[(fun state : StandardizedState => ⟪sensoryEndpointVector left, state - center⟫),
    (fun state => ⟪sensoryEndpointVector right, state - center⟫); stationaryLaw center] = _
  rw [sensoryLinear_covariance]
  cases left <;> cases right <;>
    norm_num [sensoryEndpointVector, sensoryEndpointAxis, sensoryVector,
      dotProduct, Matrix.mulVec, sum_axis, Sigma_eq_entries, PiLp.single_apply]

private theorem sensory_indep_residualPair (center : StandardizedState) :
    IndepFun (fun state : StandardizedState => state sensory)
      (sensoryResidualPair center) (stationaryLaw center) := by
  let sensoryCLM : StandardizedState →L[ℝ] (Unit → ℝ) :=
    ContinuousLinearMap.pi fun _ => innerSL ℝ sensoryVector
  let residualCLM : StandardizedState →L[ℝ] (Bool → ℝ) :=
    ContinuousLinearMap.pi fun index => innerSL ℝ (sensoryEndpointVector index)
  have hGaussian :=
    (sensoryCentered_hasGaussianLaw center).map (sensoryCLM.prod residualCLM)
  have hFamilies := hGaussian.indepFun_of_covariance_eval
    (fun _ index => by
      change cov[sensoryCentered center, sensoryResidual center index; stationaryLaw center] = 0
      exact sensory_residual_covariance_zero center index)
  have h := hFamilies.comp
    (φ := fun values : Unit → ℝ => values () + center sensory)
    (ψ := fun values : Bool → ℝ => (values false, values true))
    (by fun_prop) (by fun_prop)
  refine h.congr ?_ ?_
  · filter_upwards with state
    simp only [Function.comp_apply]
    change ⟪sensoryVector, state - center⟫ + center sensory = state sensory
    simp [sensoryVector, EuclideanSpace.inner_single_left]
  · filter_upwards with state
    rfl

private def sensoryResidualSumVector : StandardizedState :=
  sensoryEndpointVector false + sensoryEndpointVector true
private def sensoryResidualDifferenceVector : StandardizedState :=
  sensoryEndpointVector false - sensoryEndpointVector true
private def sensoryResidualU (center state : StandardizedState) : ℝ :=
  ⟪sensoryResidualSumVector, state - center⟫
private def sensoryResidualW (center state : StandardizedState) : ℝ :=
  ⟪sensoryResidualDifferenceVector, state - center⟫

@[fun_prop] private theorem measurable_sensoryResidualU (center : StandardizedState) :
    Measurable (sensoryResidualU center) := by unfold sensoryResidualU; fun_prop

@[fun_prop] private theorem measurable_sensoryResidualW (center : StandardizedState) :
    Measurable (sensoryResidualW center) := by unfold sensoryResidualW; fun_prop

private theorem sensoryResidualUW_hasGaussianLaw (center : StandardizedState) :
    HasGaussianLaw (fun state : StandardizedState =>
      (sensoryResidualU center state, sensoryResidualW center state)) (stationaryLaw center) := by
  simpa only [sensoryResidualU, sensoryResidualW, Function.comp_def,
    ContinuousLinearMap.prod_apply, innerSL_apply_apply] using
    (sensoryCentered_hasGaussianLaw center).map
      ((innerSL ℝ sensoryResidualSumVector).prod (innerSL ℝ sensoryResidualDifferenceVector))

private theorem sensoryResidualUW_covariance (center : StandardizedState) :
    cov[sensoryResidualU center, sensoryResidualW center; stationaryLaw center] = 0 := by
  change cov[(fun state : StandardizedState => ⟪sensoryResidualSumVector, state - center⟫),
    (fun state => ⟪sensoryResidualDifferenceVector, state - center⟫); stationaryLaw center] = 0
  rw [sensoryLinear_covariance]
  norm_num [sensoryResidualSumVector, sensoryResidualDifferenceVector,
    sensoryEndpointVector, sensoryEndpointAxis, sensoryVector,
    dotProduct, Matrix.mulVec, sum_axis, Sigma_eq_entries, PiLp.single_apply]

private theorem sensoryResidualU_variance (center : StandardizedState) :
    Var[sensoryResidualU center; stationaryLaw center] = 4 / 7 := by
  rw [← covariance_self (by fun_prop : Measurable (sensoryResidualU center)).aemeasurable]
  change cov[(fun state : StandardizedState => ⟪sensoryResidualSumVector, state - center⟫),
    (fun state => ⟪sensoryResidualSumVector, state - center⟫); stationaryLaw center] = _
  rw [sensoryLinear_covariance]
  norm_num [sensoryResidualSumVector, sensoryEndpointVector, sensoryEndpointAxis, sensoryVector,
    dotProduct, Matrix.mulVec, sum_axis, Sigma_eq_entries, PiLp.single_apply]

private theorem sensoryResidualW_variance (center : StandardizedState) :
    Var[sensoryResidualW center; stationaryLaw center] = 1 / 2 := by
  rw [← covariance_self (by fun_prop : Measurable (sensoryResidualW center)).aemeasurable]
  change cov[(fun state : StandardizedState => ⟪sensoryResidualDifferenceVector, state - center⟫),
    (fun state => ⟪sensoryResidualDifferenceVector, state - center⟫); stationaryLaw center] = _
  rw [sensoryLinear_covariance]
  norm_num [sensoryResidualDifferenceVector, sensoryEndpointVector, sensoryEndpointAxis, sensoryVector,
    dotProduct, Matrix.mulVec, sum_axis, Sigma_eq_entries, PiLp.single_apply]

private def sensoryDiagonalInverse (value : ℝ × ℝ) : ℝ × ℝ :=
  ((value.1 + value.2) / 2, (value.1 - value.2) / 2)

@[fun_prop] private theorem measurable_sensoryDiagonalInverse :
    Measurable sensoryDiagonalInverse := by unfold sensoryDiagonalInverse; fun_prop

def sensoryResidualLaw (center : StandardizedState) : Measure (ℝ × ℝ) :=
  (stationaryLaw center).map (sensoryResidualPair center)

instance sensoryResidualLaw_probability (center : StandardizedState) :
    IsProbabilityMeasure (sensoryResidualLaw center) := by
  unfold sensoryResidualLaw
  exact (Measure.isProbabilityMeasure_map_iff (by fun_prop)).mpr (by infer_instance)

/-- Explicit diagonal native representation of the correlated endpoint pair.
U and W, rather than E and I, are independent. -/
private theorem sensoryResidualLaw_eq_diagonal (center : StandardizedState) :
    sensoryResidualLaw center =
      ((gaussianReal 0 (4 / 7)).prod (gaussianReal 0 (1 / 2))).map sensoryDiagonalInverse := by
  have hU := (sensoryResidualUW_hasGaussianLaw center).fst.map_eq_gaussianReal
  have hW := (sensoryResidualUW_hasGaussianLaw center).snd.map_eq_gaussianReal
  have hUmean : (∫ state, sensoryResidualU center state ∂stationaryLaw center) = 0 :=
    sensoryLinear_mean center sensoryResidualSumVector
  have hWmean : (∫ state, sensoryResidualW center state ∂stationaryLaw center) = 0 :=
    sensoryLinear_mean center sensoryResidualDifferenceVector
  rw [hUmean, sensoryResidualU_variance] at hU
  rw [hWmean, sensoryResidualW_variance] at hW
  have hUp : (4 / 7 : ℝ).toNNReal = (4 / 7 : ℝ≥0) := by
    apply NNReal.eq; norm_num [Real.coe_toNNReal]
  have hWp : (1 / 2 : ℝ).toNNReal = (1 / 2 : ℝ≥0) := by
    apply NNReal.eq; norm_num [Real.coe_toNNReal]
  rw [hUp] at hU
  rw [hWp] at hW
  have hIndependent := (sensoryResidualUW_hasGaussianLaw center).indepFun_of_covariance_eq_zero
    (sensoryResidualUW_covariance center)
  have hPair := hIndependent.map_prod_eq_prod_map_map (by fun_prop) (by fun_prop)
  rw [hU, hW] at hPair
  rw [← hPair, Measure.map_map (by fun_prop) (by fun_prop)]
  unfold sensoryResidualLaw
  apply Measure.map_congr
  filter_upwards with state
  apply Prod.ext
  all_goals
    simp only [Function.comp_def, sensoryDiagonalInverse, sensoryResidualPair,
      sensoryResidualU, sensoryResidualW, sensoryResidualSumVector,
      sensoryResidualDifferenceVector, inner_add_left, inner_sub_left, sensoryResidual]
    ring

def sensoryShift (center : StandardizedState) (value : ℝ × (ℝ × ℝ)) : ℝ × ℝ :=
  (value.2.1 + sensoryConditionalMean center false value.1,
    value.2.2 + sensoryConditionalMean center true value.1)

/-- A constructed Markov kernel from the actual residual law. -/
def sensoryConditionalKernel (center : StandardizedState) : Kernel ℝ (ℝ × ℝ) :=
  (Kernel.id ×ₖ Kernel.const ℝ (sensoryResidualLaw center)).map (sensoryShift center)

instance sensoryConditionalKernel_markov (center : StandardizedState) :
    IsMarkovKernel (sensoryConditionalKernel center) :=
  Kernel.IsMarkovKernel.map _ (by unfold sensoryShift sensoryConditionalMean; fun_prop)

private theorem sensoryConditionalKernel_apply (center : StandardizedState) (datum : ℝ) :
    sensoryConditionalKernel center datum =
      (sensoryResidualLaw center).map (fun residual : ℝ × ℝ =>
        (residual.1 + sensoryConditionalMean center false datum,
          residual.2 + sensoryConditionalMean center true datum)) := by
  rw [sensoryConditionalKernel, Kernel.map_apply _ (by unfold sensoryShift sensoryConditionalMean; fun_prop),
    Kernel.prod_apply, Kernel.id_apply, Kernel.const_apply, Measure.dirac_prod,
    Measure.map_map (by unfold sensoryShift sensoryConditionalMean; fun_prop) (by fun_prop)]
  rfl

private def sensoryPartitionShift (center : StandardizedState)
    (value : ℝ × (ℝ × ℝ)) : ℝ × (ℝ × ℝ) :=
  (value.1, sensoryShift center value)

private theorem sensoryConditional_compProd (center : StandardizedState)
    (law : Measure ℝ) [SFinite law] :
    law ⊗ₘ sensoryConditionalKernel center =
      (law.prod (sensoryResidualLaw center)).map (sensoryPartitionShift center) := by
  have hShift : Measurable (sensoryPartitionShift center) := by
    unfold sensoryPartitionShift sensoryShift sensoryConditionalMean
    fun_prop
  ext set hSet
  rw [Measure.compProd_apply hSet, Measure.map_apply hShift hSet,
    Measure.prod_apply (hShift hSet)]
  apply lintegral_congr
  intro datum
  rw [sensoryConditionalKernel_apply,
    Measure.map_apply (by unfold sensoryConditionalMean; fun_prop) (measurable_prodMk_left hSet)]
  rfl

private theorem sensory_native_joint_reconstruction (center : StandardizedState) :
    (stationaryLaw center).map (fun state => (state sensory, sensoryEndpoints state)) =
      ((stationaryLaw center).map (fun state => state sensory)) ⊗ₘ
        sensoryConditionalKernel center := by
  have hIndependent := sensory_indep_residualPair center
  have hPair := hIndependent.map_prod_eq_prod_map_map (by fun_prop) (by fun_prop)
  rw [sensoryConditional_compProd, sensoryResidualLaw, ← hPair,
    Measure.map_map (by unfold sensoryPartitionShift sensoryShift sensoryConditionalMean; fun_prop)
      (by fun_prop)]
  apply Measure.map_congr
  filter_upwards with state
  apply Prod.ext
  · rfl
  · apply Prod.ext <;>
      simp only [Function.comp_def, sensoryPartitionShift, sensoryShift,
        sensoryResidualPair, sensoryEndpoints, sensoryResidual_eq, sensoryEndpointAxis]
    all_goals ring

private theorem sensory_native_condDistrib (center : StandardizedState) :
    condDistrib sensoryEndpoints (fun state : StandardizedState => state sensory)
      (stationaryLaw center)
        =ᵐ[(stationaryLaw center).map (fun state => state sensory)]
      sensoryConditionalKernel center :=
  condDistrib_ae_eq_of_measure_eq_compProd_of_measurable
    (by fun_prop) (by unfold sensoryEndpoints; fun_prop)
    (sensory_native_joint_reconstruction center)

/- Native covariance of every constructed conditional row, including its
nonzero E/I cross entry. This follows through the actual mapped residual law. -/
private theorem sensoryConditionalKernel_covariance (center : StandardizedState)
    (datum : ℝ) (left right : Bool) :
    cov[fun endpoints : ℝ × ℝ => if left then endpoints.2 else endpoints.1,
      fun endpoints => if right then endpoints.2 else endpoints.1;
        sensoryConditionalKernel center datum] =
      if left = right then (15 / 56 : ℝ) else (1 / 56 : ℝ) := by
  rw [sensoryConditionalKernel_apply, sensoryResidualLaw,
    Measure.map_map (by unfold sensoryConditionalMean; fun_prop) (by fun_prop),
    covariance_map (by cases left <;> simp only [Bool.false_eq_true, ↓reduceIte] <;> fun_prop)
      (by cases right <;> simp only [Bool.false_eq_true, ↓reduceIte] <;> fun_prop) (by fun_prop)]
  have hL : Integrable (sensoryResidual center left) (stationaryLaw center) :=
    ((sensoryCentered_hasGaussianLaw center).map_fun
      (innerSL ℝ (sensoryEndpointVector left))).integrable
  have hR : Integrable (sensoryResidual center right) (stationaryLaw center) :=
    ((sensoryCentered_hasGaussianLaw center).map_fun
      (innerSL ℝ (sensoryEndpointVector right))).integrable
  have hFunctions :
      (fun state : StandardizedState =>
        if left then (sensoryResidualPair center state).2 + sensoryConditionalMean center true datum
          else (sensoryResidualPair center state).1 + sensoryConditionalMean center false datum) =
      fun state => sensoryResidual center left state + sensoryConditionalMean center left datum := by
    cases left <;> rfl
  have hFunctionsR :
      (fun state : StandardizedState =>
        if right then (sensoryResidualPair center state).2 + sensoryConditionalMean center true datum
          else (sensoryResidualPair center state).1 + sensoryConditionalMean center false datum) =
      fun state => sensoryResidual center right state + sensoryConditionalMean center right datum := by
    cases right <;> rfl
  simp only [Function.comp_def]
  change cov[(fun state => if left then
      (sensoryResidualPair center state).2 + sensoryConditionalMean center true datum else
      (sensoryResidualPair center state).1 + sensoryConditionalMean center false datum),
    (fun state => if right then
      (sensoryResidualPair center state).2 + sensoryConditionalMean center true datum else
      (sensoryResidualPair center state).1 + sensoryConditionalMean center false datum);
      stationaryLaw center] = _
  rw [hFunctions, hFunctionsR, covariance_add_const_left hL,
    covariance_add_const_right hR, sensory_residual_covariance]

/- The surgery uses the explicit native/standard carrier equivalence. -/
def sensoryNativeClamp (state : StandardizedState) : StandardizedState :=
  FEP.H3ReferenceModel.toNativeState
    (clampActive 0 (FEP.H3ReferenceModel.fromNativeState state))

def sensoryClampedLaw (center : StandardizedState) : Measure StandardizedState :=
  (stationaryLaw center).map sensoryNativeClamp

instance sensoryClampedLaw_probability (center : StandardizedState) :
    IsProbabilityMeasure (sensoryClampedLaw center) := by
  unfold sensoryClampedLaw
  exact (Measure.isProbabilityMeasure_map_iff
    (by unfold sensoryNativeClamp; fun_prop)).mpr (by infer_instance)

private def sensoryEmbed (datum : ℝ) : ℝ × ℝ := (datum, 0)
def sensoryClampedBlanket (state : StandardizedState) : ℝ × ℝ :=
  (state sensory, state active)
def sensoryClampedConditionalKernel (center : StandardizedState) :
    Kernel (ℝ × ℝ) (ℝ × ℝ) :=
  (sensoryConditionalKernel center).comap Prod.fst measurable_fst

instance sensoryClampedConditionalKernel_markov (center : StandardizedState) :
    IsMarkovKernel (sensoryClampedConditionalKernel center) := by
  unfold sensoryClampedConditionalKernel
  infer_instance

private theorem sensory_embed_compProd (center : StandardizedState)
    (law : Measure ℝ) [SFinite law] :
    (law ⊗ₘ sensoryConditionalKernel center).map
        (fun value : ℝ × (ℝ × ℝ) => (sensoryEmbed value.1, value.2)) =
      (law.map sensoryEmbed) ⊗ₘ sensoryClampedConditionalKernel center := by
  have hLift : Measurable
      (fun value : ℝ × (ℝ × ℝ) => (sensoryEmbed value.1, value.2)) := by
    unfold sensoryEmbed
    fun_prop
  ext set hSet
  rw [Measure.map_apply hLift hSet, Measure.compProd_apply (hLift hSet),
    Measure.compProd_apply hSet,
    lintegral_map (Kernel.measurable_kernel_prodMk_left
      (κ := sensoryClampedConditionalKernel center) hSet) (by unfold sensoryEmbed; fun_prop)]
  apply lintegral_congr
  intro datum
  rfl

private theorem sensory_clamped_marginal (center : StandardizedState) :
    (sensoryClampedLaw center).map sensoryClampedBlanket =
      ((stationaryLaw center).map (fun state : StandardizedState => state sensory)).map sensoryEmbed := by
  rw [sensoryClampedLaw,
    Measure.map_map (by unfold sensoryClampedBlanket; fun_prop)
      (by unfold sensoryNativeClamp; fun_prop),
    Measure.map_map (by unfold sensoryEmbed; fun_prop) (by fun_prop)]
  apply Measure.map_congr
  filter_upwards with state
  simp [sensoryClampedBlanket, sensoryNativeClamp, sensoryEmbed, clampActive]

private theorem sensory_clamped_joint (center : StandardizedState) :
    (sensoryClampedLaw center).map (fun state =>
      (sensoryClampedBlanket state, sensoryEndpoints state)) =
      ((sensoryClampedLaw center).map sensoryClampedBlanket) ⊗ₘ
        sensoryClampedConditionalKernel center := by
  rw [sensory_clamped_marginal, ← sensory_embed_compProd,
    ← sensory_native_joint_reconstruction,
    Measure.map_map (by unfold sensoryEmbed; fun_prop) (by fun_prop),
    sensoryClampedLaw,
    Measure.map_map (by unfold sensoryClampedBlanket sensoryEndpoints; fun_prop)
      (by unfold sensoryNativeClamp; fun_prop)]
  apply Measure.map_congr
  filter_upwards with state
  simp [sensoryClampedBlanket, sensoryEndpoints,
    sensoryNativeClamp, sensoryEmbed, clampActive]

/-- Native supported-boundary conditional law after surgery, a.e. under the
actual clamped blanket law (supported at active=0), with correlated endpoints.
No off-support conditional version or original observational A=0 event is claimed. -/
theorem sensory_clamped_native_condDistrib (center : StandardizedState) :
    condDistrib sensoryEndpoints sensoryClampedBlanket (sensoryClampedLaw center)
      =ᵐ[(sensoryClampedLaw center).map sensoryClampedBlanket]
        sensoryClampedConditionalKernel center := by
  exact condDistrib_ae_eq_of_measure_eq_compProd_of_measurable
    (by unfold sensoryClampedBlanket; fun_prop) (by unfold sensoryEndpoints; fun_prop)
    (sensory_clamped_joint center)

/-- Actual cross covariance of the clamped conditional row is 1/56. -/
theorem sensory_clamped_conditional_covariance (center : StandardizedState) (datum : ℝ) :
    cov[Prod.fst, Prod.snd; sensoryClampedConditionalKernel center (datum, 0)] = 1 / 56 := by
  change cov[Prod.fst, Prod.snd; sensoryConditionalKernel center datum] = _
  simpa using sensoryConditionalKernel_covariance center datum false true

/-- Actual conditional endpoint variance is 15/56, not original full-blanket 1/4. -/
theorem sensory_clamped_conditional_variances (center : StandardizedState) (datum : ℝ) :
    Var[Prod.fst; sensoryClampedConditionalKernel center (datum, 0)] = 15 / 56 ∧
    Var[Prod.snd; sensoryClampedConditionalKernel center (datum, 0)] = 15 / 56 := by
  constructor
  · rw [← covariance_self measurable_fst.aemeasurable]
    change cov[Prod.fst, Prod.fst; sensoryConditionalKernel center datum] = _
    simpa using sensoryConditionalKernel_covariance center datum false false
  · rw [← covariance_self measurable_snd.aemeasurable]
    change cov[Prod.snd, Prod.snd; sensoryConditionalKernel center datum] = _
    simpa using sensoryConditionalKernel_covariance center datum true true

end SensoryClampNative

/-! ## Native full-state finite paths and their retained scalar projection -/

section NativeFinitePath

open FEP.Fin4GaussianSemigroup FEP.Fin4GaussianSemigroup.Axis
open FEPComposed.GaussianGridPath Finset

private theorem map_compProd_intertwining
    {A B C D : Type*} [MeasurableSpace A] [MeasurableSpace B]
    [MeasurableSpace C] [MeasurableSpace D]
    (law : Measure A) [SFinite law] (rows : Kernel A C) [IsSFiniteKernel rows]
    (projectedRows : Kernel B D) [IsSFiniteKernel projectedRows]
    (p : A → B) (q : C → D) (hp : Measurable p) (hq : Measurable q)
    (hRows : ∀ state, (rows state).map q = projectedRows (p state)) :
    (law ⊗ₘ rows).map (Prod.map p q) = law.map p ⊗ₘ projectedRows := by
  have hKernel : rows.map q = projectedRows.comap p hp := by
    apply DFunLike.ext _ _
    intro state
    rw [Kernel.map_apply _ hq, Kernel.comap_apply]
    exact hRows state
  rw [Measure.compProd_eq_comp_prod, Measure.map_comp _ _ (hp.prodMap hq),
    ← Kernel.map_prod_map _ _ hp hq, hKernel, Kernel.id_map hp,
    ← Kernel.id_comap hp, ← Kernel.comap_prod _ _ hp,
    ← Kernel.comp_deterministic_eq_comap, ← Measure.comp_assoc,
    Measure.deterministic_comp_eq_map, ← Measure.compProd_eq_comp_prod]

abbrev FullGridPath (n : ℕ) := Iic n → StandardizedState

def projectFullPath (n : ℕ) (path : FullGridPath n) : GridPath n :=
  fun index => allOnesProjection (path index)

@[fun_prop] theorem measurable_projectFullPath (n : ℕ) : Measurable (projectFullPath n) := by
  unfold projectFullPath
  fun_prop

private def projectNewPath (n : ℕ)
    (path : Ioc n (n + 1) → StandardizedState) : Ioc n (n + 1) → ℝ :=
  fun index => allOnesProjection (path index)

private theorem measurable_projectNewPath (n : ℕ) : Measurable (projectNewPath n) := by
  unfold projectNewPath
  fun_prop

def fullGridStep (center : ℝ) (grid : TimeGrid) (n : ℕ) :
    Kernel (FullGridPath n) StandardizedState :=
  (transition (allOnesEmbedding center) (grid.time (n + 1) - grid.time n)).comap
    (fun path => path ⟨n, mem_Iic.mpr le_rfl⟩) (by fun_prop)

instance fullGridStep_isMarkovKernel (center : ℝ) (grid : TimeGrid) (n : ℕ) :
    IsMarkovKernel (fullGridStep center grid n) := by
  unfold fullGridStep
  infer_instance

/-- Full native path from an arbitrary initial law. Hidden modes stay in every
transition and are projected only after the joint path is constructed. -/
def fullNativeGridLaw (center : ℝ) (grid : TimeGrid) (initial : Measure StandardizedState)
    (n : ℕ) : Measure (FullGridPath n) :=
  Kernel.partialTraj (X := fun _ : ℕ => StandardizedState) (fullGridStep center grid) 0 n ∘ₘ
    initial.map (fun state (_ : Iic 0) => state)

instance fullNativeGridLaw_isProbabilityMeasure (center : ℝ) (grid : TimeGrid)
    (initial : Measure StandardizedState) [IsProbabilityMeasure initial] (n : ℕ) :
    IsProbabilityMeasure (fullNativeGridLaw center grid initial n) := by
  unfold fullNativeGridLaw
  have : IsProbabilityMeasure (initial.map (fun state (_ : Iic 0) => state)) :=
    (Measure.isProbabilityMeasure_map_iff (by fun_prop)).mpr (by infer_instance)
  infer_instance

/-- Existing scalar OU finite-path kernel with an explicit initial law. -/
def scalarNativeGridLaw (center : ℝ) (grid : TimeGrid) (initial : Measure ℝ)
    (n : ℕ) : Measure (GridPath n) :=
  ouPartialTraj (scalarParameters center) grid 0 n ∘ₘ
    initial.map (fun state (_ : Iic 0) => state)

instance scalarNativeGridLaw_probability (center : ℝ) (grid : TimeGrid)
    (initial : Measure ℝ) [IsProbabilityMeasure initial] (n : ℕ) :
    IsProbabilityMeasure (scalarNativeGridLaw center grid initial n) := by
  unfold scalarNativeGridLaw
  infer_instance

private theorem fullNativeGridLaw_succ (center : ℝ) (grid : TimeGrid)
    (initial : Measure StandardizedState) [IsProbabilityMeasure initial] (n : ℕ) :
    fullNativeGridLaw center grid initial (n + 1) =
      ((fullNativeGridLaw center grid initial n) ⊗ₘ
        (fullGridStep center grid n).map
          (MeasurableEquiv.piSingleton (X := fun _ : ℕ => StandardizedState) n)).map
            (IicProdIoc n (n + 1) (X := fun _ : ℕ => StandardizedState)) := by
  unfold fullNativeGridLaw
  rw [Kernel.partialTraj_succ_of_le (Nat.zero_le n),
    ← Measure.map_comp _ _ (measurable_IicProdIoc
      (X := fun _ : ℕ => StandardizedState) (m := n) (n := n + 1)), ← Measure.comp_assoc,
    ← Measure.compProd_eq_comp_prod]

private theorem scalarNativeGridLaw_succ (center : ℝ) (grid : TimeGrid)
    (initial : Measure ℝ) [IsProbabilityMeasure initial] (n : ℕ) :
    scalarNativeGridLaw center grid initial (n + 1) =
      ((scalarNativeGridLaw center grid initial n) ⊗ₘ
        (ouGridStep (scalarParameters center) grid n).map (MeasurableEquiv.piSingleton n)).map
          (IicProdIoc n (n + 1)) := by
  unfold scalarNativeGridLaw ouPartialTraj
  rw [Kernel.partialTraj_succ_of_le (Nat.zero_le n),
    ← Measure.map_comp _ _ (measurable_IicProdIoc
      (X := fun _ : ℕ => ℝ) (m := n) (n := n + 1)), ← Measure.comp_assoc,
    ← Measure.compProd_eq_comp_prod]

private theorem fullGridStep_projected (center : ℝ) (grid : TimeGrid) (n : ℕ)
    (path : FullGridPath n) :
    (((fullGridStep center grid n).map (MeasurableEquiv.piSingleton (X := fun _ : ℕ => StandardizedState) n)) path).map
      (projectNewPath n) =
        ((ouGridStep (scalarParameters center) grid n).map
          (MeasurableEquiv.piSingleton (X := fun _ : ℕ => ℝ) n)) (projectFullPath n path) := by
  rw [Kernel.map_apply _ (MeasurableEquiv.piSingleton (X := fun _ : ℕ => StandardizedState) n).measurable,
    fullGridStep, Kernel.comap_apply,
    Measure.map_map (measurable_projectNewPath n) (MeasurableEquiv.piSingleton (X := fun _ : ℕ => StandardizedState) n).measurable]
  have hCommute : projectNewPath n ∘ (MeasurableEquiv.piSingleton (X := fun _ : ℕ => StandardizedState) n) =
      (MeasurableEquiv.piSingleton (X := fun _ : ℕ => ℝ) n) ∘ allOnesProjection := by
    funext state index
    cases Nat.mem_Ioc_succ' index
    rfl
  rw [hCommute, ← Measure.map_map (MeasurableEquiv.piSingleton (X := fun _ : ℕ => ℝ) n).measurable (by fun_prop),
    arbitrary_state_projection_native, Kernel.map_apply _ (MeasurableEquiv.piSingleton (X := fun _ : ℕ => ℝ) n).measurable,
    ouGridStep, Kernel.comap_apply]
  rfl

/-- Native finite JOINT-path intertwining, not an inference from equal
one-time marginals. It covers nonstationary initialization and repeated times. -/
theorem full_native_path_projection (center : ℝ) (grid : TimeGrid)
    (initial : Measure StandardizedState) [IsProbabilityMeasure initial] (n : ℕ) :
    (fullNativeGridLaw center grid initial n).map (projectFullPath n) =
      scalarNativeGridLaw center grid (initial.map allOnesProjection) n := by
  induction n with
  | zero =>
    unfold fullNativeGridLaw scalarNativeGridLaw ouPartialTraj
    rw [Kernel.partialTraj_self, Kernel.partialTraj_self, Measure.id_comp, Measure.id_comp,
      Measure.map_map (measurable_projectFullPath 0) (by fun_prop),
      Measure.map_map (by fun_prop) (by fun_prop)]
    rfl
  | succ n ih =>
    rw [fullNativeGridLaw_succ,
      Measure.map_map (measurable_projectFullPath (n + 1)) measurable_IicProdIoc]
    have hCommute : projectFullPath (n + 1) ∘
        (IicProdIoc n (n + 1) (X := fun _ => StandardizedState)) =
      (IicProdIoc n (n + 1) (X := fun _ => ℝ)) ∘
        Prod.map (projectFullPath n) (projectNewPath n) := by
      funext pair index
      simp only [Function.comp_apply, projectFullPath,
        IicProdIoc]
      split_ifs <;> rfl
    rw [hCommute, ← Measure.map_map measurable_IicProdIoc
      ((measurable_projectFullPath n).prodMap (measurable_projectNewPath n)),
      map_compProd_intertwining _ _ _ _ _ (measurable_projectFullPath n)
        (measurable_projectNewPath n) (fullGridStep_projected center grid n),
      ih, ← scalarNativeGridLaw_succ]

end NativeFinitePath

section HiddenNativePath

open FEP.Fin4GaussianSemigroup FEPComposed.GaussianGridPath
open Finset

/-- The frozen rank-one noisy scalar observation of one retained path time. -/
def pathObservationKernel (n : ℕ) (index : Iic n) (noise : ℝ≥0) (hNoise : 0 < noise) :
    Kernel (GridPath n) ℝ :=
  (observationKernel (observationFilter 0 0 noise hNoise)).comap
    (fun path => path index) (by fun_prop)

instance pathObservationKernel_markov (n : ℕ) (index : Iic n)
    (noise : ℝ≥0) (hNoise : 0 < noise) :
    IsMarkovKernel (pathObservationKernel n index noise hNoise) := by
  unfold pathObservationKernel
  infer_instance

/-- This full-state channel reads the same scalar projection without resetting
the other axes; its independent Gaussian noise is supplied by the native row. -/
def fullPathObservationKernel (n : ℕ) (index : Iic n) (noise : ℝ≥0) (hNoise : 0 < noise) :
    Kernel (FullGridPath n) ℝ :=
  (pathObservationKernel n index noise hNoise).comap (projectFullPath n)
    (measurable_projectFullPath n)

instance fullPathObservationKernel_markov (n : ℕ) (index : Iic n)
    (noise : ℝ≥0) (hNoise : 0 < noise) :
    IsMarkovKernel (fullPathObservationKernel n index noise hNoise) := by
  unfold fullPathObservationKernel
  infer_instance

theorem fullPathObservationKernel_native_row (n : ℕ) (index : Iic n)
    (noise : ℝ≥0) (hNoise : 0 < noise) (path : FullGridPath n) :
    fullPathObservationKernel n index noise hNoise path =
      gaussianReal (allOnesProjection (path index)) noise := by
  rfl

private theorem full_noisy_path_projection (center : ℝ) (grid : TimeGrid)
    (initial : Measure StandardizedState) [IsProbabilityMeasure initial]
    (n : ℕ) (index : Iic n) (noise : ℝ≥0) (hNoise : 0 < noise) :
    ((fullNativeGridLaw center grid initial n) ⊗ₘ
      fullPathObservationKernel n index noise hNoise).map (Prod.map (projectFullPath n) id) =
        (scalarNativeGridLaw center grid (initial.map allOnesProjection) n) ⊗ₘ
          pathObservationKernel n index noise hNoise := by
  rw [map_compProd_intertwining (fullNativeGridLaw center grid initial n)
    (fullPathObservationKernel n index noise hNoise) (pathObservationKernel n index noise hNoise)
    (projectFullPath n) id (measurable_projectFullPath n) measurable_id
    (by intro path; rw [Measure.map_id]; rfl), full_native_path_projection]

/-- Frozen hidden-mode negative control. Distinct native initial laws with
means zero and the normalized rate-four external/internal mode induce exactly
the same finite projected JOINT paths and path/noisy-observation JOINT laws.
The zero-centered full transition, Sigma and noise remain fixed. -/
theorem hidden_mode_nonidentifiability (grid : TimeGrid) (n : ℕ) (index : Iic n)
    (noise : ℝ≥0) (hNoise : 0 < noise) :
    hiddenInitialLaw 0 false ≠ hiddenInitialLaw 0 true ∧
    (fullNativeGridLaw 0 grid (hiddenInitialLaw 0 false) n).map (projectFullPath n) =
      (fullNativeGridLaw 0 grid (hiddenInitialLaw 0 true) n).map (projectFullPath n) ∧
    ((fullNativeGridLaw 0 grid (hiddenInitialLaw 0 false) n) ⊗ₘ
        fullPathObservationKernel n index noise hNoise).map (Prod.map (projectFullPath n) id) =
      ((fullNativeGridLaw 0 grid (hiddenInitialLaw 0 true) n) ⊗ₘ
        fullPathObservationKernel n index noise hNoise).map (Prod.map (projectFullPath n) id) := by
  refine ⟨(hidden_mode_marginal_nonidentifiability 0 0).1, ?_, ?_⟩
  · rw [full_native_path_projection, full_native_path_projection,
      hiddenInitialLaw_projection, hiddenInitialLaw_projection]
  · rw [full_noisy_path_projection, full_noisy_path_projection,
      hiddenInitialLaw_projection, hiddenInitialLaw_projection]

end HiddenNativePath

/-! ## Native prospective observation, preference EFE and its assumption boundary -/

def prospectiveObservationFilter (noise : ℝ≥0) (hNoise : 0 < noise) :
    ScalarGaussianFilterModel := observationFilter 0 0 noise hNoise

private theorem prediction_at_zero (noise : ℝ≥0) (hNoise : 0 < noise)
    (belief : ScalarGaussianBelief) :
    predictionBelief (prospectiveObservationFilter noise hNoise) belief = belief := by
  cases belief with
  | mk mean family =>
    cases family with
    | mk variance hVariance =>
      simp [predictionBelief, predictionVariance, prospectiveObservationFilter,
        observationFilter, ScalarOUParameters.transitionMean_zero,
        ScalarOUParameters.transitionVariance_zero, ScalarOUParameters.decay]

/-- Actual common terminal variance for both control centers. -/
def terminalVariance (belief : ScalarGaussianBelief) : ℝ :=
  controlDecay ^ 2 * (belief.family.variance : ℝ) + (1 - controlDecay ^ 2) / 2

theorem controlledVariance_exact (belief : ScalarGaussianBelief) (action : Bool) :
    (controlledVariance controlModel belief action : ℝ) = terminalVariance belief := by
  change (controlModel.dynamics action).decay controlModel.duration ^ 2 *
    (belief.family.variance : ℝ) +
      ((controlModel.dynamics action).transitionVariance controlModel.duration : ℝ) = _
  rw [control_decay, control_transitionVariance]
  rfl

theorem controlledMean_exact (belief : ScalarGaussianBelief) (action : Bool) :
    controlledMean controlModel belief action =
      controlDecay * belief.mean + (1 - controlDecay) * actionCenter action := by
  rw [controlledMean, ScalarOUParameters.transitionMean, control_decay]
  change actionCenter action + controlDecay * (belief.mean - actionCenter action) = _
  ring

theorem terminalVariance_pos (belief : ScalarGaussianBelief) : 0 < terminalVariance belief := by
  rw [← controlledVariance_exact belief false]
  exact_mod_cast controlledVariance_pos controlModel belief false

/-- Native terminal state/independent-noisy-observation joint, without an extra
prediction step or an assumed information field. -/
def terminalObservationJoint (belief : ScalarGaussianBelief) (action : Bool)
    (noise : ℝ≥0) (hNoise : 0 < noise) : Measure (ℝ × ℝ) :=
  (controlledBelief controlModel belief action).law ⊗ₘ
    observationKernel (prospectiveObservationFilter noise hNoise)

def terminalInformation (belief : ScalarGaussianBelief) (action : Bool)
    (noise : ℝ≥0) (hNoise : 0 < noise) : ℝ≥0∞ :=
  klDiv (terminalObservationJoint belief action noise hNoise)
    ((terminalObservationJoint belief action noise hNoise).fst.prod
      (terminalObservationJoint belief action noise hNoise).snd)

/-- Frozen EFE information is the actual native terminal-channel MI. The exact
formula derives action independence, finite support and integrability. -/
theorem efe_native_information (belief : ScalarGaussianBelief) (action : Bool)
    (noise : ℝ≥0) (hNoise : 0 < noise) :
    terminalInformation belief action noise hNoise =
      ENNReal.ofReal ((1 / 2 : ℝ) * Real.log (1 + terminalVariance belief / noise)) := by
  have h := information_native_mutualInformation (prospectiveObservationFilter noise hNoise)
    (controlledBelief controlModel belief action)
  unfold informationJoint at h
  rw [prediction_at_zero] at h
  change terminalInformation belief action noise hNoise =
    ENNReal.ofReal ((1 / 2 : ℝ) * Real.log
      (1 + (controlledVariance controlModel belief action : ℝ) / noise)) at h
  rw [controlledVariance_exact] at h
  exact h

private theorem terminalInformation_real (belief : ScalarGaussianBelief) (action : Bool)
    (noise : ℝ≥0) (hNoise : 0 < noise) :
    (terminalInformation belief action noise hNoise).toReal =
      (1 / 2 : ℝ) * Real.log (1 + terminalVariance belief / noise) := by
  rw [efe_native_information, ENNReal.toReal_ofReal]
  have hNoiseReal : (0 : ℝ) < noise := by exact_mod_cast hNoise
  exact mul_nonneg (by norm_num) (Real.log_nonneg
    (le_add_of_nonneg_right (div_nonneg (terminalVariance_pos belief).le hNoiseReal.le)))

/-- Negative log of the actual positive preference density N(preference,1/2). -/
def preferenceSurprisal (preference state : ℝ) : ℝ :=
  -Real.log (gaussianPDFReal preference (1 / 2) state)

private theorem preferenceSurprisal_eq (preference state : ℝ) :
    preferenceSurprisal preference state = (state - preference) ^ 2 +
      (1 / 2 : ℝ) * Real.log Real.pi := by
  unfold preferenceSurprisal
  rw [gaussianPDFReal_def]
  have hVariance : ((1 / 2 : ℝ≥0) : ℝ) = 1 / 2 := by norm_num
  rw [hVariance, show 2 * Real.pi * (1 / 2 : ℝ) = Real.pi by ring,
    show 2 * (1 / 2 : ℝ) = 1 by norm_num]
  dsimp only
  rw [div_one]
  rw [Real.log_mul (inv_ne_zero (Real.sqrt_pos.2 Real.pi_pos).ne') (Real.exp_ne_zero _),
    Real.log_inv, Real.log_exp, Real.log_sqrt Real.pi_pos.le]
  ring

/-- Density-defined EFE for the exact terminal law, not a renamed quadratic
risk: expected negative log preference minus actual native mutual information. -/
def expectedFreeEnergy (preference : ℝ) (belief : ScalarGaussianBelief) (action : Bool)
    (noise : ℝ≥0) (hNoise : 0 < noise) : ℝ :=
  (∫ state, preferenceSurprisal preference state ∂(controlledBelief controlModel belief action).law) -
    (terminalInformation belief action noise hNoise).toReal

theorem expectedFreeEnergy_closedForm (preference : ℝ) (belief : ScalarGaussianBelief)
    (action : Bool) (noise : ℝ≥0) (hNoise : 0 < noise) :
    expectedFreeEnergy preference belief action noise hNoise =
      terminalVariance belief +
        (controlledMean controlModel belief action - preference) ^ 2 +
        (1 / 2 : ℝ) * Real.log Real.pi -
        (1 / 2 : ℝ) * Real.log (1 + terminalVariance belief / noise) := by
  rw [expectedFreeEnergy, terminalInformation_real]
  change (∫ state, preferenceSurprisal preference state
      ∂gaussianReal (controlledMean controlModel belief action)
        (controlledVariance controlModel belief action)) - _ = _
  simp_rw [preferenceSurprisal_eq]
  have hSquare : Integrable (fun state : ℝ =>
      (state - preference) ^ 2) (gaussianReal (controlledMean controlModel belief action)
        (controlledVariance controlModel belief action)) :=
    ((memLp_id_gaussianReal 2).sub (memLp_const preference)).integrable_sq
  rw [integral_add hSquare (integrable_const ((1 / 2 : ℝ) * Real.log Real.pi)),
    gaussian_square_integral, integral_const, controlledVariance_exact]
  simp only [probReal_univ, one_smul]

/-- With the frozen centered preference, EFE is risk plus an action-common
constant, including the actual native information term. -/
theorem efe_risk_alignment (belief : ScalarGaussianBelief) (left right : Bool)
    (noise : ℝ≥0) (hNoise : 0 < noise) :
    expectedFreeEnergy 0 belief left noise hNoise -
        expectedFreeEnergy 0 belief right noise hNoise =
      quadraticActionRisk controlModel belief left - quadraticActionRisk controlModel belief right := by
  rw [expectedFreeEnergy_closedForm, expectedFreeEnergy_closedForm,
    quadraticActionRisk_eq_closedForm, quadraticActionRisk_eq_closedForm,
    controlledVariance_exact, controlledVariance_exact]
  simp only [controlModel, sub_zero, NNReal.coe_zero, add_zero]
  ring

theorem efe_risk_ordering (belief : ScalarGaussianBelief) (left right : Bool)
    (noise : ℝ≥0) (hNoise : 0 < noise) :
    (expectedFreeEnergy 0 belief left noise hNoise ≤ expectedFreeEnergy 0 belief right noise hNoise ↔
      quadraticActionRisk controlModel belief left ≤ quadraticActionRisk controlModel belief right) ∧
    (expectedFreeEnergy 0 belief left noise hNoise = expectedFreeEnergy 0 belief right noise hNoise ↔
      quadraticActionRisk controlModel belief left = quadraticActionRisk controlModel belief right) := by
  have h := efe_risk_alignment belief left right noise hNoise
  constructor <;> constructor <;> intro hOrder <;> linarith

def preferenceCounterBelief (noise : ℝ≥0) (hNoise : 0 < noise) : ScalarGaussianBelief where
  mean := 1
  family :=
    { variance := controlPosteriorVariance noise
      variance_pos := by
        rw [← (first_posterior false noise hNoise 0).2]
        exact posteriorVariance_pos _ _ }

/-- Keeping the native transition, noise and terminal-risk target fixed, the
declared preference shift at posterior mean one reverses the strict ordering.
This is an assumption countermodel, not a fitted second primary model. -/
theorem preference_counterexample (noise : ℝ≥0) (hNoise : 0 < noise) :
    quadraticActionRisk controlModel (preferenceCounterBelief noise hNoise) false <
      quadraticActionRisk controlModel (preferenceCounterBelief noise hNoise) true ∧
    expectedFreeEnergy 1 (preferenceCounterBelief noise hNoise) true noise hNoise <
      expectedFreeEnergy 1 (preferenceCounterBelief noise hNoise) false noise hNoise := by
  rcases controlDecay_bounds with ⟨hPositive, hLessOne⟩
  constructor
  · rw [quadraticActionRisk_eq_closedForm, quadraticActionRisk_eq_closedForm,
      controlledVariance_exact, controlledVariance_exact, controlledMean_exact, controlledMean_exact]
    simp only [controlModel, preferenceCounterBelief, actionCenter, ↓reduceIte,
      Bool.false_eq_true, sub_zero, NNReal.coe_zero, add_zero]
    have hProduct : controlDecay * (controlDecay - 1) < 0 :=
      mul_neg_of_pos_of_neg hPositive (sub_neg.mpr hLessOne)
    nlinarith
  · rw [expectedFreeEnergy_closedForm, expectedFreeEnergy_closedForm,
      controlledMean_exact, controlledMean_exact]
    simp only [preferenceCounterBelief, actionCenter, Bool.false_eq_true, ↓reduceIte]
    have hSquare : 0 < (2 * controlDecay - 2) ^ 2 := sq_pos_of_ne_zero (by linarith)
    nlinarith

/-- The attained primitive policy cost is exactly its native-posterior
conditional-law cost, evidence a.e.; the same measurement is used throughout. -/
theorem policyRisk_eq_nativePosterior (noise : ℝ≥0) (hNoise : 0 < noise) (policy : TwoStepPolicy) :
    policyRisk noise hNoise policy =
      ∫ observation, nativePosteriorQuadraticRisk controlModel
        (firstFilter policy.first noise hNoise) (prior 0) observation (policy.second observation)
        ∂evidenceLaw (firstFilter policy.first noise hNoise) (prior 0) := by
  apply integral_congr_ae
  have hActions : ∀ᵐ observation ∂evidenceLaw (firstFilter policy.first noise hNoise) (prior 0),
      ∀ action : Bool, secondRisk policy.first noise hNoise observation action =
        nativePosteriorQuadraticRisk controlModel (firstFilter policy.first noise hNoise)
          (prior 0) observation action :=
    Filter.eventually_all.2 fun action => filteredQuadraticRisk_ae_eq_nativePosterior
      controlModel (firstFilter policy.first noise hNoise) (prior 0) action
  filter_upwards [hActions] with observation hObservation
  exact hObservation (policy.second observation)

/-! ## Same-budget open-loop restriction counterexample -/

private theorem gaussian_affine_square_integrable (mean coefficient offset : ℝ)
    (variance : ℝ≥0) :
    Integrable (fun value : ℝ => (coefficient * value + offset) ^ 2)
      (gaussianReal mean variance) :=
  ((memLp_id_gaussianReal 2).const_mul coefficient |>.add (memLp_const offset)).integrable_sq

private theorem gaussian_affine_square_integral (mean coefficient offset : ℝ)
    (variance : ℝ≥0) :
    (∫ value : ℝ, (coefficient * value + offset) ^ 2 ∂gaussianReal mean variance) =
      coefficient ^ 2 * (variance : ℝ) + (coefficient * mean + offset) ^ 2 := by
  have hMap : (gaussianReal mean variance).map (fun value => coefficient * value + offset) =
      gaussianReal (coefficient * mean + offset)
        (NNReal.mk (coefficient ^ 2) (sq_nonneg coefficient) * variance) := by
    rw [← gaussianReal_map_add_const offset, ← gaussianReal_map_const_mul coefficient,
      Measure.map_map (by fun_prop) (by fun_prop)]
    rfl
  have hMoment := gaussian_square_integral (coefficient * mean + offset) 0
    (NNReal.mk (coefficient ^ 2) (sq_nonneg coefficient) * variance)
  rw [← hMap, integral_map (by fun_prop) (by fun_prop)] at hMoment
  simpa only [sub_zero, NNReal.coe_mul, NNReal.coe_mk] using hMoment

/-- Actual integrated native filtered risk for every fixed pair. Measurement
noise changes the posterior but cancels from this unconditional fixed-action
cost by native Gaussian integration. -/
theorem openLoopRisk_closedForm (noise : ℝ≥0) (hNoise : 0 < noise)
    (first second : Bool) :
    policyRisk noise hNoise (openLoopPolicy first second) =
      (1 / 2 : ℝ) +
        ((1 - controlDecay) * (controlDecay * actionCenter first + actionCenter second)) ^ 2 := by
  rw [policyRisk]
  change (∫ observation, secondRisk first noise hNoise observation second
    ∂evidenceLaw (firstFilter first noise hNoise) (prior 0)) = _
  rw [evidenceLaw_eq_gaussian, FixedVarianceGaussian.law_eq_gaussianReal]
  rcases first_prediction first noise hNoise with ⟨hMean, hVariance⟩
  simp only [evidenceFamily, innovationVariance, hMean, hVariance]
  let predicted : ℝ := (1 - controlDecay) * actionCenter first
  let gainValue : ℝ := (1 / 2 : ℝ) / (1 / 2 + noise)
  let coefficient : ℝ := controlDecay * gainValue
  let offset : ℝ := controlDecay * (1 - gainValue) * predicted +
    (1 - controlDecay) * actionCenter second
  let constant : ℝ := controlDecay ^ 2 * (controlPosteriorVariance noise : ℝ) +
    (1 - controlDecay ^ 2) / 2
  have hRewrite (observation : ℝ) : secondRisk first noise hNoise observation second =
      constant + (coefficient * observation + offset) ^ 2 := by
    rw [secondRisk_closedForm]
    dsimp [constant, coefficient, offset, gainValue, predicted, controlPosteriorMean]
    ring
  simp_rw [hRewrite]
  change (∫ observation : ℝ, constant + (coefficient * observation + offset) ^ 2
    ∂gaussianReal predicted (1 / 2 + noise)) = _
  rw [integral_add (integrable_const constant)
      (gaussian_affine_square_integrable predicted coefficient offset (1 / 2 + noise)),
    integral_const, gaussian_affine_square_integral]
  simp only [probReal_univ, one_smul]
  have hDen : (1 / 2 : ℝ) + noise ≠ 0 := by positivity
  dsimp [constant, coefficient, offset, gainValue, predicted, controlPosteriorVariance]
  norm_num
  field_simp [hDen]
  ring

/-- Fixing the same sign for both actions excludes a strictly better admitted
opposite pair. Every cost uses the same loss, duration and actual noisy law. -/
theorem restricted_class_counterexample (noise : ℝ≥0) (hNoise : 0 < noise) :
    policyRisk noise hNoise (openLoopPolicy true true) =
      (1 / 2 : ℝ) + (1 - controlDecay ^ 2) ^ 2 ∧
    policyRisk noise hNoise (openLoopPolicy false true) =
      (1 / 2 : ℝ) + (1 - controlDecay) ^ 4 ∧
    policyRisk noise hNoise (openLoopPolicy false true) <
      policyRisk noise hNoise (openLoopPolicy true true) := by
  have hSame := openLoopRisk_closedForm noise hNoise true true
  have hOpposite := openLoopRisk_closedForm noise hNoise false true
  simp only [actionCenter, Bool.false_eq_true, ↓reduceIte, mul_one, mul_neg_one] at hSame hOpposite
  have hFirst : policyRisk noise hNoise (openLoopPolicy true true) =
      (1 / 2 : ℝ) + (1 - controlDecay ^ 2) ^ 2 := by rw [hSame]; ring
  have hSecond : policyRisk noise hNoise (openLoopPolicy false true) =
      (1 / 2 : ℝ) + (1 - controlDecay) ^ 4 := by rw [hOpposite]; ring
  refine ⟨hFirst, hSecond, ?_⟩
  rw [hFirst, hSecond]
  rcases controlDecay_bounds with ⟨hPositive, hLess⟩
  have hGap : 0 < 4 * controlDecay * (1 - controlDecay) ^ 2 := by positivity
  nlinarith

/-- The native post-surgery conditional endpoint dependence is supported on
(S,0); this combines normalization and the actual a.e. conditional law. -/
theorem clamp_conditional_covariance (center : FEP.Fin4GaussianSemigroup.StandardizedState) :
    (condDistrib sensoryEndpoints sensoryClampedBlanket (sensoryClampedLaw center)
      =ᵐ[(sensoryClampedLaw center).map sensoryClampedBlanket]
        sensoryClampedConditionalKernel center) ∧
      ∀ datum : ℝ,
        cov[Prod.fst, Prod.snd; sensoryClampedConditionalKernel center (datum, 0)] = 1 / 56 :=
  ⟨sensory_clamped_native_condDistrib center, sensory_clamped_conditional_covariance center⟩

/-! ## Actual controlled full-state modal moments -/

section FullStateMoments
open FEP.Fin4GaussianSemigroup FEP.Fin4GaussianSemigroup.Axis

private def modeBasis : Matrix Axis Axis ℝ
  | external, external => 1
  | external, sensory => 1
  | external, active => 0
  | external, internal => 1
  | sensory, external => 1
  | sensory, sensory => 0
  | sensory, active => 1
  | sensory, internal => -1
  | active, external => 1
  | active, sensory => 0
  | active, active => -1
  | active, internal => -1
  | internal, external => 1
  | internal, sensory => -1
  | internal, active => 0
  | internal, internal => 1

private def modeBasisInverse : Matrix Axis Axis ℝ
  | external, external => 1 / 4
  | external, sensory => 1 / 4
  | external, active => 1 / 4
  | external, internal => 1 / 4
  | sensory, external => 1 / 2
  | sensory, sensory => 0
  | sensory, active => 0
  | sensory, internal => -1 / 2
  | active, external => 0
  | active, sensory => 1 / 2
  | active, active => -1 / 2
  | active, internal => 0
  | internal, external => 1 / 4
  | internal, sensory => -1 / 4
  | internal, active => -1 / 4
  | internal, internal => 1 / 4

private def modeBasisUnit : (Matrix Axis Axis ℝ)ˣ where
  val := modeBasis
  inv := modeBasisInverse
  val_inv := by
    ext row column
    cases row <;> cases column <;>
      simp [Matrix.mul_apply, sum_axis, modeBasis, modeBasisInverse] <;>
      norm_num
  inv_val := by
    ext row column
    cases row <;> cases column <;>
      simp [Matrix.mul_apply, sum_axis, modeBasis, modeBasisInverse] <;>
      norm_num

private def modeRate : Axis → ℝ
  | external => 2
  | sensory => 4
  | active => 4
  | internal => 6

private theorem K_mode_decomposition :
    K = (modeBasisUnit : Matrix Axis Axis ℝ) *
      Matrix.diagonal modeRate *
        ((modeBasisUnit⁻¹ : (Matrix Axis Axis ℝ)ˣ) :
          Matrix Axis Axis ℝ) := by
  ext row column
  cases row <;> cases column <;>
    simp [Matrix.mul_apply, sum_axis, K, modeBasisUnit, modeBasis,
      modeBasisInverse, modeRate] <;>
    norm_num

private theorem evolution_mode_decomposition (time : ℝ≥0) :
    NormedSpace.exp ((-(time : ℝ)) • K) =
      modeBasis *
        Matrix.diagonal
          (fun mode => Real.exp (-((time : ℝ) * modeRate mode))) *
        modeBasisInverse := by
  calc
    NormedSpace.exp ((-(time : ℝ)) • K) =
        NormedSpace.exp
          ((modeBasisUnit : Matrix Axis Axis ℝ) *
            ((-(time : ℝ)) • Matrix.diagonal modeRate) *
              ((modeBasisUnit⁻¹ : (Matrix Axis Axis ℝ)ˣ) :
                Matrix Axis Axis ℝ)) := by
      rw [K_mode_decomposition]
      congr 1
      simp
    _ =
        (modeBasisUnit : Matrix Axis Axis ℝ) *
          NormedSpace.exp
            ((-(time : ℝ)) • Matrix.diagonal modeRate) *
          ((modeBasisUnit⁻¹ : (Matrix Axis Axis ℝ)ˣ) :
            Matrix Axis Axis ℝ) := by
      exact Matrix.exp_units_conj modeBasisUnit
        ((-(time : ℝ)) • Matrix.diagonal modeRate)
    _ = _ := by
      rw [← Matrix.diagonal_smul, Matrix.exp_diagonal]
      rw [Pi.exp_def]
      congr 1
      funext mode
      rw [← Real.exp_eq_exp_ℝ]
      simp [modeBasisUnit]


private def rawModeVector : Axis → StandardizedState
  | external => WithLp.toLp 2 eigenmodeTwo
  | sensory => WithLp.toLp 2 eigenmodeFourExternal
  | active => WithLp.toLp 2 eigenmodeFourSensory
  | internal => WithLp.toLp 2 eigenmodeSix

private def rawModeNormSquared : Axis → ℝ
  | external => 4
  | sensory => 2
  | active => 2
  | internal => 4

private def modeProjection (mode : Axis) : StandardizedState →L[ℝ] ℝ :=
  innerSL ℝ (rawModeVector mode)

private def modeDecay (mode : Axis) (time : ℝ≥0) : ℝ :=
  Real.exp (-((time : ℝ) * modeRate mode))

private theorem rawMode_norm (mode : Axis) :
    rawModeVector mode ⬝ᵥ rawModeVector mode = rawModeNormSquared mode := by
  cases mode <;>
    norm_num [rawModeVector, rawModeNormSquared, dotProduct, sum_axis, axis_cardinality,
      eigenmodeTwo, eigenmodeFourExternal, eigenmodeFourSensory, eigenmodeSix]

private theorem rawMode_covariance (mode : Axis) :
    Sigma *ᵥ rawModeVector mode =
      (1 / modeRate mode) • rawModeVector mode := by
  rw [Sigma_eq_entries]
  funext axis
  cases mode <;> cases axis <;>
    norm_num [rawModeVector, modeRate, Matrix.mulVec, dotProduct, sum_axis,
      eigenmodeTwo, eigenmodeFourExternal, eigenmodeFourSensory, eigenmodeSix]

private theorem evolution_rawMode (mode : Axis) (time : ℝ≥0) :
    NormedSpace.exp ((-(time : ℝ)) • K) *ᵥ rawModeVector mode =
      modeDecay mode time • rawModeVector mode := by
  rw [evolution_mode_decomposition, ← Matrix.mulVec_mulVec, ← Matrix.mulVec_mulVec]
  have hInverse : modeBasisInverse *ᵥ rawModeVector mode = Pi.single mode 1 := by
    funext axis
    cases mode <;> cases axis <;>
      norm_num [Matrix.mulVec, dotProduct, sum_axis, modeBasisInverse, rawModeVector,
        eigenmodeTwo, eigenmodeFourExternal, eigenmodeFourSensory, eigenmodeSix, Pi.single_apply]
  rw [hInverse]
  funext axis
  cases mode <;> cases axis <;>
    simp [Matrix.mulVec, dotProduct, sum_axis, modeBasis, modeRate, modeDecay,
      rawModeVector, eigenmodeTwo, eigenmodeFourExternal, eigenmodeFourSensory, eigenmodeSix]

private theorem evolution_modeProjected (mode : Axis) (time : ℝ≥0)
    (state : StandardizedState) :
    modeProjection mode (Matrix.toEuclideanCLM (𝕜 := ℝ)
      (NormedSpace.exp ((-(time : ℝ)) • K)) state) =
      modeDecay mode time * modeProjection mode state := by
  change ⟪rawModeVector mode, Matrix.toEuclideanCLM (𝕜 := ℝ)
      (NormedSpace.exp ((-(time : ℝ)) • K)) state⟫ =
    modeDecay mode time * ⟪rawModeVector mode, state⟫
  simp only [EuclideanSpace.inner_eq_star_dotProduct, star_trivial]
  have hSwap : (NormedSpace.exp ((-(time : ℝ)) • K)).IsSymm :=
    (parameters (0 : StandardizedState)).evolution_transpose time
  change ((NormedSpace.exp ((-(time : ℝ)) • K)) *ᵥ state) ⬝ᵥ rawModeVector mode = _
  rw [dotProduct_comm, hSwap.dotProduct_mulVec_comm, evolution_rawMode,
    dotProduct_smul, smul_eq_mul]

private theorem modeProjection_embedding (mode : Axis) (center : ℝ) :
    modeProjection mode (allOnesEmbedding center) =
      if mode = external then 2 * center else 0 := by
  cases mode <;>
    norm_num [modeProjection, innerSL_apply_apply, EuclideanSpace.inner_eq_star_dotProduct,
      dotProduct, sum_axis, rawModeVector, eigenmodeTwo, eigenmodeFourExternal,
      eigenmodeFourSensory, eigenmodeSix, allOnesEmbedding, normalizedAllOnes, axis_cardinality, smul_eq_mul]
  ring

private theorem mode_transitionMean (mode : Axis) (center : ℝ) (time : ℝ≥0)
    (state : StandardizedState) :
    (∫ next, modeProjection mode next ∂transition (allOnesEmbedding center) time state) =
      modeDecay mode time * modeProjection mode state +
        (1 - modeDecay mode time) * (if mode = external then 2 * center else 0) := by
  rw [transition_apply, (modeProjection mode).integral_comp_id_comm IsGaussian.integrable_id,
    integral_id_multivariateGaussian, map_add, evolution_modeProjected, map_sub,
    modeProjection_embedding]
  ring

private theorem mode_transitionCovariance (mode : Axis) (center : ℝ) (time : ℝ≥0) :
    rawModeVector mode ⬝ᵥ
      (parameters (allOnesEmbedding center)).transitionCovariance time *ᵥ rawModeVector mode =
      rawModeNormSquared mode / modeRate mode * (1 - modeDecay mode time ^ 2) := by
  rw [FEP.LinearGaussianSemigroup.LinearGaussianParameters.transitionCovariance]
  change rawModeVector mode ⬝ᵥ
    (FEP.Fin4GaussianSemigroup.Sigma - NormedSpace.exp ((-(time : ℝ)) • K) * FEP.Fin4GaussianSemigroup.Sigma *
      (NormedSpace.exp ((-(time : ℝ)) • K))ᵀ) *ᵥ rawModeVector mode = _
  have hTranspose : (NormedSpace.exp ((-(time : ℝ)) • K))ᵀ =
      NormedSpace.exp ((-(time : ℝ)) • K) := by
    exact (parameters (allOnesEmbedding center)).evolution_transpose time
  rw [hTranspose, sub_mulVec]
  have hTransport :
      (NormedSpace.exp ((-(time : ℝ)) • K) * FEP.Fin4GaussianSemigroup.Sigma *
        NormedSpace.exp ((-(time : ℝ)) • K)) *ᵥ rawModeVector mode =
      ((1 / modeRate mode) * modeDecay mode time ^ 2) • rawModeVector mode := by
    rw [← Matrix.mulVec_mulVec, ← Matrix.mulVec_mulVec, evolution_rawMode,
      Matrix.mulVec_smul, rawMode_covariance, Matrix.mulVec_smul, Matrix.mulVec_smul,
      evolution_rawMode]
    simp only [smul_smul]
    congr 1
    ring
  rw [hTransport, rawMode_covariance, dotProduct_sub, dotProduct_smul, dotProduct_smul,
    rawMode_norm]
  ring

private theorem mode_transitionVariance (mode : Axis) (center : ℝ) (time : ℝ≥0)
    (state : StandardizedState) :
    Var[modeProjection mode; transition (allOnesEmbedding center) time state] =
      rawModeNormSquared mode / modeRate mode * (1 - modeDecay mode time ^ 2) := by
  rw [transition_apply]
  rw [show (modeProjection mode : StandardizedState → ℝ) =
    fun next => ⟪rawModeVector mode, next⟫ by rfl]
  rw [← covarianceBilin_self IsGaussian.memLp_two_id]
  calc
    _ = rawModeVector mode ⬝ᵥ
        (parameters (allOnesEmbedding center)).transitionCovariance time *ᵥ rawModeVector mode := by
      exact covarianceBilin_multivariateGaussian
        ((parameters (allOnesEmbedding center)).transitionCovariance_posSemidef time)
        (rawModeVector mode) (rawModeVector mode)
    _ = _ := mode_transitionCovariance mode center time

private theorem mode_transition_law (mode : Axis) (center : ℝ) (time : ℝ≥0)
    (state : StandardizedState) :
    (transition (allOnesEmbedding center) time state).map (modeProjection mode) =
      gaussianReal
        (modeDecay mode time * modeProjection mode state +
          (1 - modeDecay mode time) * (if mode = external then 2 * center else 0))
        (rawModeNormSquared mode / modeRate mode * (1 - modeDecay mode time ^ 2)).toNNReal := by
  have hMean := mode_transitionMean mode center time state
  have hVariance := mode_transitionVariance mode center time state
  rw [transition_apply] at hMean hVariance
  rw [transition_apply, IsGaussian.map_eq_gaussianReal, hMean, hVariance]

private theorem modal_parseval (state : StandardizedState) :
    ‖state‖ ^ 2 =
      (modeProjection external state) ^ 2 / 4 +
      (modeProjection sensory state) ^ 2 / 2 +
      (modeProjection active state) ^ 2 / 2 +
      (modeProjection internal state) ^ 2 / 4 := by
  rw [← real_inner_self_eq_norm_sq]
  simp only [EuclideanSpace.inner_eq_star_dotProduct, star_trivial]
  simp [modeProjection, innerSL_apply_apply, EuclideanSpace.inner_eq_star_dotProduct,
    dotProduct, sum_axis, rawModeVector, eigenmodeTwo, eigenmodeFourExternal,
    eigenmodeFourSensory, eigenmodeSix]
  ring

/-- The genuine native full-state row selected from the primitive Bool action;
only the center changes. Reading a history retains its current full state. -/
def selectedNativeTransition {H : Type*} [MeasurableSpace H]
    (read : H → StandardizedState) (hRead : Measurable read)
    (select : H → Bool) (hSelect : Measurable select) : Kernel H StandardizedState := by
  classical
  exact Kernel.piecewise ((measurableSet_singleton true).preimage hSelect)
    ((transition (allOnesEmbedding 1) controlDuration).comap read hRead)
    ((transition (allOnesEmbedding (-1)) controlDuration).comap read hRead)

instance selectedNativeTransition_markov {H : Type*} [MeasurableSpace H]
    (read : H → StandardizedState) (hRead : Measurable read)
    (select : H → Bool) (hSelect : Measurable select) :
    IsMarkovKernel (selectedNativeTransition read hRead select hSelect) := by
  unfold selectedNativeTransition
  infer_instance

private theorem selectedNativeTransition_apply {H : Type*} [MeasurableSpace H]
    (read : H → StandardizedState) (hRead : Measurable read)
    (select : H → Bool) (hSelect : Measurable select) (history : H) :
    selectedNativeTransition read hRead select hSelect history =
      transition (allOnesEmbedding (actionCenter (select history))) controlDuration (read history) := by
  classical
  cases h : select history <;> simp [selectedNativeTransition, Kernel.piecewise_apply,
    actionCenter, h, Bool.false_eq_true]

private theorem mode_row_integrable (mode : Axis) (center : ℝ) (state : StandardizedState) :
    Integrable (fun next => (modeProjection mode next) ^ 2)
      (transition (allOnesEmbedding center) controlDuration state) := by
  have h : Integrable (fun value : ℝ => value ^ 2)
      ((transition (allOnesEmbedding center) controlDuration state).map (modeProjection mode)) := by
    rw [mode_transition_law]
    exact (memLp_id_gaussianReal 2).integrable_sq
  exact (integrable_map_measure (by fun_prop) (by fun_prop)).1 h

private theorem mode_row_moment (mode : Axis) (center : ℝ) (state : StandardizedState) :
    (∫ next, (modeProjection mode next) ^ 2
      ∂transition (allOnesEmbedding center) controlDuration state) =
      rawModeNormSquared mode / modeRate mode * (1 - modeDecay mode controlDuration ^ 2) +
        (modeDecay mode controlDuration * modeProjection mode state +
          (1 - modeDecay mode controlDuration) * (if mode = external then 2 * center else 0)) ^ 2 := by
  have hVariance : 0 ≤ rawModeNormSquared mode / modeRate mode *
      (1 - modeDecay mode controlDuration ^ 2) := by
    rw [← mode_transitionVariance mode center controlDuration state]
    exact variance_nonneg _ _
  rw [← integral_map (f := fun value : ℝ => value ^ 2)
      (modeProjection mode).measurable.aemeasurable (by fun_prop),
    mode_transition_law]
  have hMoment := gaussian_square_integral
      (modeDecay mode controlDuration * modeProjection mode state +
        (1 - modeDecay mode controlDuration) * (if mode = external then 2 * center else 0))
      0 (rawModeNormSquared mode / modeRate mode *
        (1 - modeDecay mode controlDuration ^ 2)).toNNReal
  rw [sub_zero, Real.coe_toNNReal _ hVariance] at hMoment
  simpa only [sub_zero] using hMoment

private theorem selected_mode_integrable {H : Type*} [MeasurableSpace H]
    (law : Measure H) [IsProbabilityMeasure law]
    (read : H → StandardizedState) (hRead : Measurable read)
    (select : H → Bool) (hSelect : Measurable select) (mode : Axis)
    (hInput : MemLp (fun history => modeProjection mode (read history)) 2 law) :
    Integrable (fun pair : H × StandardizedState => (modeProjection mode pair.2) ^ 2)
      (law ⊗ₘ selectedNativeTransition read hRead select hSelect) := by
  classical
  apply (Measure.integrable_compProd_iff (by fun_prop)).mpr
  constructor
  · apply ae_of_all
    intro history
    rw [selectedNativeTransition_apply]
    exact mode_row_integrable mode _ _
  · have hRow (history : H) :
        (∫ next, ‖(modeProjection mode next) ^ 2‖
          ∂selectedNativeTransition read hRead select hSelect history) =
        rawModeNormSquared mode / modeRate mode * (1 - modeDecay mode controlDuration ^ 2) +
          (modeDecay mode controlDuration * modeProjection mode (read history) +
            (1 - modeDecay mode controlDuration) *
              (if mode = external then 2 * actionCenter (select history) else 0)) ^ 2 := by
      simp only [Real.norm_eq_abs, abs_sq]
      rw [selectedNativeTransition_apply, mode_row_moment]
    simp_rw [hRow]
    have hFixed (action : Bool) : Integrable (fun history =>
        rawModeNormSquared mode / modeRate mode * (1 - modeDecay mode controlDuration ^ 2) +
          (modeDecay mode controlDuration * modeProjection mode (read history) +
            (1 - modeDecay mode controlDuration) *
              (if mode = external then 2 * actionCenter action else 0)) ^ 2) law :=
      (integrable_const _).add
        ((hInput.const_mul _).add (memLp_const _)).integrable_sq
    have hPiece := Integrable.piecewise ((measurableSet_singleton true).preimage hSelect).nullMeasurableSet
      (hFixed true).integrableOn (hFixed false).integrableOn
    apply hPiece.congr
    filter_upwards with history
    cases h : select history <;> simp [Set.piecewise, h]

private theorem selected_mode_moment {H : Type*} [MeasurableSpace H]
    (law : Measure H) [IsProbabilityMeasure law]
    (read : H → StandardizedState) (hRead : Measurable read)
    (select : H → Bool) (hSelect : Measurable select) (mode : Axis)
    (hInput : MemLp (fun history => modeProjection mode (read history)) 2 law) :
    (∫ pair : H × StandardizedState, (modeProjection mode pair.2) ^ 2
      ∂law ⊗ₘ selectedNativeTransition read hRead select hSelect) =
      ∫ history, rawModeNormSquared mode / modeRate mode *
        (1 - modeDecay mode controlDuration ^ 2) +
        (modeDecay mode controlDuration * modeProjection mode (read history) +
          (1 - modeDecay mode controlDuration) *
            (if mode = external then 2 * actionCenter (select history) else 0)) ^ 2 ∂law := by
  rw [Measure.integral_compProd (selected_mode_integrable law read hRead select hSelect mode hInput)]
  apply integral_congr_ae
  filter_upwards with history
  rw [selectedNativeTransition_apply, mode_row_moment]

private theorem selected_mode_memLp {H : Type*} [MeasurableSpace H]
    (law : Measure H) [IsProbabilityMeasure law]
    (read : H → StandardizedState) (hRead : Measurable read)
    (select : H → Bool) (hSelect : Measurable select) (mode : Axis)
    (hInput : MemLp (fun history => modeProjection mode (read history)) 2 law) :
    MemLp (modeProjection mode) 2
      ((law ⊗ₘ selectedNativeTransition read hRead select hSelect).map Prod.snd) := by
  apply (memLp_two_iff_integrable_sq (by fun_prop)).2
  exact (integrable_map_measure (by fun_prop) (by fun_prop)).2
    (selected_mode_integrable law read hRead select hSelect mode hInput)

/-- Actual native full-state initial law and both retained state marginals. -/
def controlInitialLaw : Measure StandardizedState := stationaryLaw 0

instance controlInitialLaw_probability : IsProbabilityMeasure controlInitialLaw := by
  unfold controlInitialLaw
  infer_instance

def controlFirstLaw (policy : TwoStepPolicy) : Measure StandardizedState :=
  (controlInitialLaw ⊗ₘ selectedNativeTransition id measurable_id
    (fun _ => policy.first) measurable_const).map Prod.snd

instance controlFirstLaw_probability (policy : TwoStepPolicy) :
    IsProbabilityMeasure (controlFirstLaw policy) := by unfold controlFirstLaw; infer_instance

def controlObservationKernel (noise : ℝ≥0) (hNoise : 0 < noise) :
    Kernel StandardizedState ℝ :=
  (observationKernel (prospectiveObservationFilter noise hNoise)).comap allOnesProjection
    allOnesProjection.measurable

instance controlObservationKernel_markov (noise : ℝ≥0) (hNoise : 0 < noise) :
    IsMarkovKernel (controlObservationKernel noise hNoise) := by
  unfold controlObservationKernel
  infer_instance

def controlHistoryLaw (policy : TwoStepPolicy) (noise : ℝ≥0) (hNoise : 0 < noise) :
    Measure (StandardizedState × ℝ) :=
  controlFirstLaw policy ⊗ₘ controlObservationKernel noise hNoise

instance controlHistoryLaw_probability (policy : TwoStepPolicy) (noise : ℝ≥0)
    (hNoise : 0 < noise) : IsProbabilityMeasure (controlHistoryLaw policy noise hNoise) := by
  unfold controlHistoryLaw
  infer_instance

def controlSecondLaw (policy : TwoStepPolicy) (noise : ℝ≥0) (hNoise : 0 < noise) :
    Measure StandardizedState :=
  (controlHistoryLaw policy noise hNoise ⊗ₘ
    selectedNativeTransition Prod.fst measurable_fst
      (fun history => policy.second history.2) (policy.measurable_second.comp measurable_snd)).map
        Prod.snd

instance controlSecondLaw_probability (policy : TwoStepPolicy) (noise : ℝ≥0)
    (hNoise : 0 < noise) : IsProbabilityMeasure (controlSecondLaw policy noise hNoise) := by
  unfold controlSecondLaw
  infer_instance

private theorem initial_mode_memLp (mode : Axis) :
    MemLp (modeProjection mode) 2 controlInitialLaw := by
  change MemLp (modeProjection mode) 2 (multivariateGaussian 0 FEP.Fin4GaussianSemigroup.Sigma)
  exact IsGaussian.memLp_dual _ _ 2 (by norm_num)

private theorem initial_mode_moment (mode : Axis) :
    (∫ state, (modeProjection mode state) ^ 2 ∂controlInitialLaw) =
      rawModeNormSquared mode / modeRate mode := by
  have hLaw : controlInitialLaw.map (modeProjection mode) =
      gaussianReal 0 (rawModeNormSquared mode / modeRate mode).toNNReal := by
    change (multivariateGaussian 0 FEP.Fin4GaussianSemigroup.Sigma).map (modeProjection mode) = _
    rw [IsGaussian.map_eq_gaussianReal]
    have hMean : (multivariateGaussian 0 FEP.Fin4GaussianSemigroup.Sigma)[modeProjection mode] = 0 := by
      rw [(modeProjection mode).integral_comp_id_comm IsGaussian.integrable_id,
        integral_id_multivariateGaussian, map_zero]
    rw [hMean, show Var[modeProjection mode;
        multivariateGaussian 0 FEP.Fin4GaussianSemigroup.Sigma] =
          rawModeNormSquared mode / modeRate mode by
      change Var[fun state : StandardizedState => ⟪rawModeVector mode, state⟫;
        multivariateGaussian 0 FEP.Fin4GaussianSemigroup.Sigma] = _
      rw [← covarianceBilin_self IsGaussian.memLp_two_id,
        covarianceBilin_multivariateGaussian Sigma_posDef.posSemidef,
        rawMode_covariance, dotProduct_smul, rawMode_norm]
      ring]
  rw [← integral_map (f := fun value : ℝ => value ^ 2)
      (modeProjection mode).measurable.aemeasurable (by fun_prop), hLaw]
  have hNonneg : 0 ≤ rawModeNormSquared mode / modeRate mode := by
    cases mode <;> norm_num [rawModeNormSquared, modeRate]
  simpa only [sub_zero, zero_pow (by norm_num : 2 ≠ 0), add_zero,
    Real.toNNReal_of_nonneg hNonneg, NNReal.coe_mk] using
      gaussian_square_integral 0 0 (rawModeNormSquared mode / modeRate mode).toNNReal

private theorem first_mode_memLp (policy : TwoStepPolicy) (mode : Axis) :
    MemLp (modeProjection mode) 2 (controlFirstLaw policy) :=
  selected_mode_memLp controlInitialLaw id measurable_id (fun _ => policy.first)
    measurable_const mode (initial_mode_memLp mode)

private theorem history_mode_memLp (policy : TwoStepPolicy) (noise : ℝ≥0)
    (hNoise : 0 < noise) (mode : Axis) :
    MemLp (fun history : StandardizedState × ℝ => modeProjection mode history.1) 2
      (controlHistoryLaw policy noise hNoise) := by
  have hMap : (controlHistoryLaw policy noise hNoise).map Prod.fst = controlFirstLaw policy := by
    change (controlFirstLaw policy ⊗ₘ controlObservationKernel noise hNoise).fst = _
    exact Measure.fst_compProd _ _
  exact (first_mode_memLp policy mode).comp_measurePreserving
    ⟨measurable_fst, hMap⟩

private theorem second_mode_memLp (policy : TwoStepPolicy) (noise : ℝ≥0)
    (hNoise : 0 < noise) (mode : Axis) :
    MemLp (modeProjection mode) 2 (controlSecondLaw policy noise hNoise) :=
  selected_mode_memLp (controlHistoryLaw policy noise hNoise) Prod.fst measurable_fst
    (fun history => policy.second history.2) (policy.measurable_second.comp measurable_snd)
    mode (history_mode_memLp policy noise hNoise mode)

private theorem modeQuarter_decay_external : modeDecay external controlDuration = controlDecay := by
  norm_num [modeDecay, modeRate, controlDuration, controlDecay]

private theorem raw_external_projection (state : StandardizedState) :
    modeProjection external state = 2 * allOnesProjection state := by
  simp [modeProjection, innerSL_apply_apply, EuclideanSpace.inner_eq_star_dotProduct,
    dotProduct, sum_axis, rawModeVector, eigenmodeTwo, allOnesProjection, normalizedAllOnes]
  ring

private theorem history_mode_moment (policy : TwoStepPolicy) (noise : ℝ≥0)
    (hNoise : 0 < noise) (mode : Axis) :
    (∫ history : StandardizedState × ℝ, (modeProjection mode history.1) ^ 2
      ∂controlHistoryLaw policy noise hNoise) =
      ∫ state, (modeProjection mode state) ^ 2 ∂controlFirstLaw policy := by
  have hMap : (controlHistoryLaw policy noise hNoise).map Prod.fst = controlFirstLaw policy := by
    change (controlFirstLaw policy ⊗ₘ controlObservationKernel noise hNoise).fst = _
    exact Measure.fst_compProd _ _
  rw [← hMap, integral_map (by fun_prop) (by fun_prop)]

private theorem selected_hidden_stationary_moment {H : Type*} [MeasurableSpace H]
    (law : Measure H) [IsProbabilityMeasure law]
    (read : H → StandardizedState) (hRead : Measurable read)
    (select : H → Bool) (hSelect : Measurable select) (mode : Axis) (hMode : mode ≠ external)
    (hInput : MemLp (fun history => modeProjection mode (read history)) 2 law)
    (hMoment : (∫ history, (modeProjection mode (read history)) ^ 2 ∂law) =
      rawModeNormSquared mode / modeRate mode) :
    (∫ state, (modeProjection mode state) ^ 2
      ∂(law ⊗ₘ selectedNativeTransition read hRead select hSelect).map Prod.snd) =
      rawModeNormSquared mode / modeRate mode := by
  rw [integral_map (by fun_prop) (by fun_prop),
    selected_mode_moment law read hRead select hSelect mode hInput]
  simp only [hMode, ↓reduceIte, mul_zero, add_zero, mul_pow]
  rw [integral_add (integrable_const _)
      (hInput.integrable_sq.const_mul (modeDecay mode controlDuration ^ 2)),
    integral_const, integral_const_mul, hMoment]
  simp only [probReal_univ, one_smul]
  ring

/-- The frozen finite-horizon scalar certificate, derived from row moments. -/
def controlledBound : ℝ := 3 / 2 + controlDecay / 2

private theorem controlledBound_fixedpoint :
    controlDecay * (4 * controlledBound) + 4 * (1 - controlDecay) +
      2 * (1 - controlDecay ^ 2) = 4 * controlledBound := by
  unfold controlledBound
  ring

private theorem scalar_convex_square (value : ℝ) (action : Bool) :
    (controlDecay * value + (1 - controlDecay) * (2 * actionCenter action)) ^ 2 ≤
      controlDecay * value ^ 2 + 4 * (1 - controlDecay) := by
  rcases controlDecay_bounds with ⟨hPositive, hLess⟩
  have hGap : 0 ≤ controlDecay * (1 - controlDecay) *
      (value - 2 * actionCenter action) ^ 2 := by positivity
  cases action <;> simp only [actionCenter, Bool.false_eq_true, ↓reduceIte] at * <;> nlinarith

private theorem selected_scalar_bounded {H : Type*} [MeasurableSpace H]
    (law : Measure H) [IsProbabilityMeasure law]
    (read : H → StandardizedState) (hRead : Measurable read)
    (select : H → Bool) (hSelect : Measurable select)
    (hInput : MemLp (fun history => modeProjection external (read history)) 2 law)
    (hMoment : (∫ history, (modeProjection external (read history)) ^ 2 ∂law) ≤
      4 * controlledBound) :
    (∫ state, (modeProjection external state) ^ 2
      ∂(law ⊗ₘ selectedNativeTransition read hRead select hSelect).map Prod.snd) ≤
      4 * controlledBound := by
  rw [integral_map (by fun_prop) (by fun_prop),
    selected_mode_moment law read hRead select hSelect external hInput]
  simp only [modeQuarter_decay_external, rawModeNormSquared, modeRate, ↓reduceIte]
  norm_num only
  have hInputSquare := hInput.integrable_sq
  have hUpper : Integrable (fun history => 2 * (1 - controlDecay ^ 2) +
      (controlDecay * (modeProjection external (read history)) ^ 2 +
        4 * (1 - controlDecay))) law :=
    (integrable_const _).add ((hInputSquare.const_mul _).add (integrable_const _))
  have hLower : Integrable (fun history => 2 * (1 - controlDecay ^ 2) +
      (controlDecay * modeProjection external (read history) +
        (1 - controlDecay) * (2 * actionCenter (select history))) ^ 2) law := by
    have h := (selected_mode_integrable law read hRead select hSelect external hInput).integral_compProd
    have hRow (history : H) :
        (∫ next, (modeProjection external next) ^ 2
          ∂selectedNativeTransition read hRead select hSelect history) =
          2 * (1 - controlDecay ^ 2) +
            (controlDecay * modeProjection external (read history) +
              (1 - controlDecay) * (2 * actionCenter (select history))) ^ 2 := by
      rw [selectedNativeTransition_apply, mode_row_moment]
      norm_num [rawModeNormSquared, modeRate, modeQuarter_decay_external]
    change Integrable (fun history => ∫ next, (modeProjection external next) ^ 2
      ∂selectedNativeTransition read hRead select hSelect history) law at h
    simpa only [hRow] using h
  calc
    _ ≤ ∫ history, 2 * (1 - controlDecay ^ 2) +
        (controlDecay * (modeProjection external (read history)) ^ 2 +
          4 * (1 - controlDecay)) ∂law :=
      integral_mono hLower hUpper (fun history => by
        linarith [scalar_convex_square (modeProjection external (read history)) (select history)])
    _ = controlDecay * (∫ history, (modeProjection external (read history)) ^ 2 ∂law) +
        4 * (1 - controlDecay) + 2 * (1 - controlDecay ^ 2) := by
      rw [integral_add
          (f := fun _ : H => 2 * (1 - controlDecay ^ 2))
          (g := fun history => controlDecay * (modeProjection external (read history)) ^ 2 +
            4 * (1 - controlDecay))
          (integrable_const _) ((hInputSquare.const_mul _).add (integrable_const _)),
        integral_add
          (f := fun history => controlDecay * (modeProjection external (read history)) ^ 2)
          (g := fun _ : H => 4 * (1 - controlDecay))
          (hInputSquare.const_mul _) (integrable_const _),
        integral_const, integral_const]
      simp only [integral_const_mul, probReal_univ, one_smul]
      ring
    _ ≤ controlDecay * (4 * controlledBound) +
        4 * (1 - controlDecay) + 2 * (1 - controlDecay ^ 2) := by
      nlinarith [mul_le_mul_of_nonneg_left hMoment controlDecay_bounds.1.le]
    _ = _ := controlledBound_fixedpoint

private theorem first_hidden_moment (policy : TwoStepPolicy) (mode : Axis) (hMode : mode ≠ external) :
    (∫ state, (modeProjection mode state) ^ 2 ∂controlFirstLaw policy) =
      rawModeNormSquared mode / modeRate mode :=
  selected_hidden_stationary_moment controlInitialLaw id measurable_id
    (fun _ => policy.first) measurable_const mode hMode (initial_mode_memLp mode)
    (initial_mode_moment mode)

private theorem second_hidden_moment (policy : TwoStepPolicy) (noise : ℝ≥0)
    (hNoise : 0 < noise) (mode : Axis) (hMode : mode ≠ external) :
    (∫ state, (modeProjection mode state) ^ 2 ∂controlSecondLaw policy noise hNoise) =
      rawModeNormSquared mode / modeRate mode := by
  apply selected_hidden_stationary_moment (controlHistoryLaw policy noise hNoise)
    Prod.fst measurable_fst (fun history => policy.second history.2)
    (policy.measurable_second.comp measurable_snd) mode hMode
    (history_mode_memLp policy noise hNoise mode)
  rw [history_mode_moment, first_hidden_moment policy mode hMode]

private theorem first_scalar_bound (policy : TwoStepPolicy) :
    (∫ state, (modeProjection external state) ^ 2 ∂controlFirstLaw policy) ≤
      4 * controlledBound := by
  apply selected_scalar_bounded controlInitialLaw id measurable_id
    (fun _ => policy.first) measurable_const (initial_mode_memLp external)
  change (∫ state, (modeProjection external state) ^ 2 ∂controlInitialLaw) ≤ _
  rw [initial_mode_moment]
  simp only [rawModeNormSquared, modeRate]
  unfold controlledBound
  linarith [controlDecay_bounds.1]

private theorem second_scalar_bound (policy : TwoStepPolicy) (noise : ℝ≥0)
    (hNoise : 0 < noise) :
    (∫ state, (modeProjection external state) ^ 2 ∂controlSecondLaw policy noise hNoise) ≤
      4 * controlledBound := by
  apply selected_scalar_bounded (controlHistoryLaw policy noise hNoise)
    Prod.fst measurable_fst (fun history => policy.second history.2)
    (policy.measurable_second.comp measurable_snd) (history_mode_memLp policy noise hNoise external)
  rw [history_mode_moment]
  exact first_scalar_bound policy

private theorem fullnorm_moment {law : Measure StandardizedState} [IsProbabilityMeasure law]
    (hModes : ∀ mode, MemLp (modeProjection mode) 2 law) :
    (∫ state, ‖state‖ ^ 2 ∂law) =
      (∫ state, (modeProjection external state) ^ 2 ∂law) / 4 +
      (∫ state, (modeProjection sensory state) ^ 2 ∂law) / 2 +
      (∫ state, (modeProjection active state) ^ 2 ∂law) / 2 +
      (∫ state, (modeProjection internal state) ^ 2 ∂law) / 4 := by
  simp_rw [modal_parseval]
  rw [integral_add
      (f := fun state => (modeProjection external state) ^ 2 / 4 +
        (modeProjection sensory state) ^ 2 / 2 + (modeProjection active state) ^ 2 / 2)
      (g := fun state => (modeProjection internal state) ^ 2 / 4)
      (((hModes external).integrable_sq.div_const 4 |>.add
        ((hModes sensory).integrable_sq.div_const 2)).add
          ((hModes active).integrable_sq.div_const 2))
      ((hModes internal).integrable_sq.div_const 4),
    integral_add
      (f := fun state => (modeProjection external state) ^ 2 / 4 +
        (modeProjection sensory state) ^ 2 / 2)
      (g := fun state => (modeProjection active state) ^ 2 / 2)
      ((hModes external).integrable_sq.div_const 4 |>.add
        ((hModes sensory).integrable_sq.div_const 2))
      ((hModes active).integrable_sq.div_const 2),
    integral_add
      (f := fun state => (modeProjection external state) ^ 2 / 4)
      (g := fun state => (modeProjection sensory state) ^ 2 / 2)
      ((hModes external).integrable_sq.div_const 4)
      ((hModes sensory).integrable_sq.div_const 2),
    integral_div, integral_div, integral_div, integral_div]

/-- Both actual native full-state marginals satisfy the frozen scalar and
full-norm second-moment bounds for every admitted measurable feedback policy.
No Gaussian full-state feedback law or observed/hidden independence is assumed. -/
theorem controlled_moment_bound (policy : TwoStepPolicy) (noise : ℝ≥0) (hNoise : 0 < noise) :
    (∫ state, (allOnesProjection state) ^ 2 ∂controlFirstLaw policy) ≤ controlledBound ∧
    (∫ state, (allOnesProjection state) ^ 2 ∂controlSecondLaw policy noise hNoise) ≤ controlledBound ∧
    (∫ state, ‖state‖ ^ 2 ∂controlFirstLaw policy) ≤ controlledBound + 2 / 3 ∧
    (∫ state, ‖state‖ ^ 2 ∂controlSecondLaw policy noise hNoise) ≤ controlledBound + 2 / 3 := by
  have hFirst := first_scalar_bound policy
  have hSecond := second_scalar_bound policy noise hNoise
  have hScalar (law : Measure StandardizedState) [IsProbabilityMeasure law]
      (hBound : (∫ state, (modeProjection external state) ^ 2 ∂law) ≤ 4 * controlledBound) :
      (∫ state, (allOnesProjection state) ^ 2 ∂law) ≤ controlledBound := by
    simp_rw [raw_external_projection, mul_pow] at hBound
    rw [integral_const_mul] at hBound
    norm_num at hBound
    linarith
  refine ⟨hScalar _ hFirst,
    hScalar _ hSecond, ?_, ?_⟩
  · rw [fullnorm_moment (first_mode_memLp policy),
      first_hidden_moment policy sensory (by decide),
      first_hidden_moment policy active (by decide),
      first_hidden_moment policy internal (by decide)]
    simp only [rawModeNormSquared, modeRate]
    linarith
  · rw [fullnorm_moment (second_mode_memLp policy noise hNoise),
      second_hidden_moment policy noise hNoise sensory (by decide),
      second_hidden_moment policy noise hNoise active (by decide),
      second_hidden_moment policy noise hNoise internal (by decide)]
    simp only [rawModeNormSquared, modeRate]
    linarith

end FullStateMoments

section ThreeTimeNativeInformation
open FEP.Fin4GaussianSemigroup FEPComposed.GaussianGridPath
open Finset

/-- Two-way data processing proves exact native KL invariance under a
measurable equivalence, including non-AC/infinite branches. -/
private theorem nativeKL_map_equiv {A B : Type*} [MeasurableSpace A] [MeasurableSpace B]
    (law reference : Measure A) [IsFiniteMeasure law] [IsFiniteMeasure reference]
    (equiv : A ≃ᵐ B) :
    klDiv (law.map equiv) (reference.map equiv) = klDiv law reference := by
  apply le_antisymm (klDiv_map_le law reference equiv.measurable)
  have h := klDiv_map_le (law.map equiv) (reference.map equiv) equiv.symm.measurable
  rw [Measure.map_map equiv.symm.measurable equiv.measurable,
    Measure.map_map equiv.symm.measurable equiv.measurable] at h
  have hInverse : equiv.symm ∘ equiv = id := by
    funext value
    exact equiv.symm_apply_apply value
  rw [hInverse, Measure.map_id, Measure.map_id] at h
  exact h

/-- Product KL addition from the pinned native chain rule, with no new RN
or integrability hypothesis silently supplied by a model field. -/
private theorem nativeKL_prod {A B : Type*} [MeasurableSpace A] [MeasurableSpace B]
    (left referenceLeft : Measure A) (right referenceRight : Measure B)
    [IsProbabilityMeasure left] [IsProbabilityMeasure referenceLeft]
    [IsProbabilityMeasure right] [IsProbabilityMeasure referenceRight] :
    klDiv (left.prod right) (referenceLeft.prod referenceRight) =
      klDiv left referenceLeft + klDiv right referenceRight := by
  have hChain := klDiv_compProd_eq_add left referenceLeft
    (Kernel.const A right) (Kernel.const A referenceRight)
  simp only [Measure.compProd_const] at hChain
  rw [hChain]
  congr 1
  have hSwap := nativeKL_map_equiv (left.prod right) (left.prod referenceRight)
    (MeasurableEquiv.prodComm : A × B ≃ᵐ B × A)
  change klDiv ((left.prod right).map Prod.swap)
    ((left.prod referenceRight).map Prod.swap) = _ at hSwap
  rw [Measure.prod_swap, Measure.prod_swap] at hSwap
  rw [← hSwap]
  simpa only [Measure.compProd_const] using
    klDiv_compProd_left right referenceRight (Kernel.const B left)

abbrev InformationTriple := (ℝ × ℝ) × ℝ

private def tripleReverse (value : InformationTriple) : InformationTriple :=
  ((value.2, value.1.2), value.1.1)

private def tripleReverseEquiv : InformationTriple ≃ᵐ InformationTriple where
  toFun := tripleReverse
  invFun := tripleReverse
  left_inv value := by rcases value with ⟨⟨x, y⟩, z⟩; rfl
  right_inv value := by rcases value with ⟨⟨x, y⟩, z⟩; rfl
  measurable_toFun := by change Measurable tripleReverse; unfold tripleReverse; fun_prop
  measurable_invFun := by change Measurable tripleReverse; unfold tripleReverse; fun_prop

private def tripleInnovations (decay : ℝ) (value : InformationTriple) : InformationTriple :=
  ((value.1.1, value.1.2 - decay * value.1.1), value.2 - decay * value.1.2)

private def tripleFromInnovations (decay : ℝ) (value : InformationTriple) : InformationTriple :=
  ((value.1.1, decay * value.1.1 + value.1.2),
    decay * (decay * value.1.1 + value.1.2) + value.2)

private def tripleInnovationEquiv (decay : ℝ) : InformationTriple ≃ᵐ InformationTriple where
  toFun := tripleInnovations decay
  invFun := tripleFromInnovations decay
  left_inv value := by
    rcases value with ⟨⟨x, y⟩, z⟩
    apply Prod.ext
    · apply Prod.ext
      · rfl
      · dsimp [tripleInnovations, tripleFromInnovations]; ring
    · dsimp [tripleInnovations, tripleFromInnovations]; ring
  right_inv value := by
    rcases value with ⟨⟨x, y⟩, z⟩
    apply Prod.ext
    · apply Prod.ext
      · rfl
      · dsimp [tripleInnovations, tripleFromInnovations]; ring
    · dsimp [tripleInnovations, tripleFromInnovations]; ring
  measurable_toFun := by change Measurable (tripleInnovations decay); unfold tripleInnovations; fun_prop
  measurable_invFun := by change Measurable (tripleFromInnovations decay); unfold tripleFromInnovations; fun_prop

def gaussianARStep (decay : ℝ) (noise : ℝ≥0) : Kernel ℝ ℝ where
  toFun state := gaussianReal (decay * state) noise
  measurable' := by
    change Measurable (Function.uncurry gaussianReal ∘
      fun state : ℝ => (decay * state, noise))
    exact measurable_gaussianReal.comp (by fun_prop)

instance gaussianARStep_markov (decay : ℝ) (noise : ℝ≥0) :
    IsMarkovKernel (gaussianARStep decay noise) :=
  ⟨fun _ => by change IsProbabilityMeasure (gaussianReal _ _); infer_instance⟩

private theorem gaussianAR_compProd {A : Type*} [MeasurableSpace A]
    (law : Measure A) [SFinite law] (read : A → ℝ) (hRead : Measurable read)
    (decay : ℝ) (noise : ℝ≥0) :
    law ⊗ₘ (gaussianARStep decay noise).comap read hRead =
      (law.prod (gaussianReal 0 noise)).map
        (fun pair : A × ℝ => (pair.1, decay * read pair.1 + pair.2)) := by
  have hShift : Measurable
      (fun pair : A × ℝ => (pair.1, decay * read pair.1 + pair.2)) := by fun_prop
  ext set hSet
  rw [Measure.compProd_apply hSet, Measure.map_apply hShift hSet,
    Measure.prod_apply (hShift hSet)]
  apply lintegral_congr
  intro state
  change gaussianReal (decay * read state) noise (Prod.mk state ⁻¹' set) = _
  rw [← show (gaussianReal 0 noise).map
      (fun innovation : ℝ => decay * read state + innovation) =
        gaussianReal (decay * read state) noise by
    rw [gaussianReal_map_const_add]; simp,
    Measure.map_apply (by fun_prop) (measurable_prodMk_left hSet)]
  rfl

/-- A concrete native Markov joint, ready to be identified with the actual
partialTraj/Iic representation, rather than a three-moment surrogate. -/
def gaussianARTripleLaw (initialMean : ℝ) (initialVariance : ℝ≥0)
    (decay : ℝ) (noise : ℝ≥0) : Measure InformationTriple :=
  ((gaussianReal initialMean initialVariance) ⊗ₘ gaussianARStep decay noise) ⊗ₘ
    (gaussianARStep decay noise).comap Prod.snd measurable_snd

def gaussianARInnovationLaw (initialMean : ℝ) (initialVariance : ℝ≥0)
    (noise : ℝ≥0) : Measure InformationTriple :=
  ((gaussianReal initialMean initialVariance).prod (gaussianReal 0 noise)).prod
    (gaussianReal 0 noise)

private theorem gaussianARTripleLaw_eq_innovations (initialMean : ℝ)
    (initialVariance : ℝ≥0) (decay : ℝ) (noise : ℝ≥0) :
    gaussianARTripleLaw initialMean initialVariance decay noise =
      (gaussianARInnovationLaw initialMean initialVariance noise).map
        (tripleFromInnovations decay) := by
  let firstShift : ℝ × ℝ → ℝ × ℝ := fun pair => (pair.1, decay * pair.1 + pair.2)
  have hFirst :
      (gaussianReal initialMean initialVariance) ⊗ₘ gaussianARStep decay noise =
        ((gaussianReal initialMean initialVariance).prod (gaussianReal 0 noise)).map firstShift := by
    simpa only [Kernel.comap_id, firstShift, id_eq] using
      gaussianAR_compProd (gaussianReal initialMean initialVariance) id measurable_id decay noise
  have hIntertwining := map_compProd_intertwining
    ((gaussianReal initialMean initialVariance).prod (gaussianReal 0 noise))
    ((gaussianARStep decay noise).comap
      (fun pair : ℝ × ℝ => decay * pair.1 + pair.2) (by fun_prop))
    ((gaussianARStep decay noise).comap Prod.snd measurable_snd)
    firstShift id (by dsimp [firstShift]; fun_prop) measurable_id
    (by intro pair; rw [Measure.map_id]; rfl)
  rw [gaussianARTripleLaw, hFirst, ← hIntertwining,
    gaussianAR_compProd, Measure.map_map (by dsimp [firstShift]; fun_prop) (by fun_prop)]
  apply Measure.map_congr
  filter_upwards with value
  rfl

private theorem gaussianARTripleLaw_innovation_map (initialMean : ℝ)
    (initialVariance : ℝ≥0) (decay : ℝ) (noise : ℝ≥0) :
    (gaussianARTripleLaw initialMean initialVariance decay noise).map
      (tripleInnovationEquiv decay) =
        gaussianARInnovationLaw initialMean initialVariance noise := by
  rw [gaussianARTripleLaw_eq_innovations,
    Measure.map_map (tripleInnovationEquiv decay).measurable (by unfold tripleFromInnovations; fun_prop)]
  have hInverse : (tripleInnovationEquiv decay) ∘ tripleFromInnovations decay = id := by
    funext value
    exact (tripleInnovationEquiv decay).apply_symm_apply value
  rw [hInverse, Measure.map_id]

def frozenPathNoise : ℝ≥0 :=
  ⟨(1 - controlDecay ^ 2) / 2, by
    have h := controlDecay_bounds
    have hProduct : 0 < (1 - controlDecay) * (1 + controlDecay) :=
      mul_pos (sub_pos.mpr h.2) (by linarith [h.1])
    nlinarith [hProduct]⟩

private theorem frozenPathNoise_pos : 0 < frozenPathNoise := by
  change 0 < (1 - controlDecay ^ 2) / 2
  have h := controlDecay_bounds
  have hProduct : 0 < (1 - controlDecay) * (1 + controlDecay) :=
    mul_pos (sub_pos.mpr h.2) (by linarith [h.1])
  nlinarith [hProduct]

def frozenForwardInnovations : Measure InformationTriple :=
  gaussianARInnovationLaw 1 (1 / 2) frozenPathNoise

private def frozenReverseInnovations : Measure InformationTriple :=
  ((gaussianReal (controlDecay ^ 2) (1 / 2)).prod
    (gaussianReal (controlDecay * (1 - controlDecay ^ 2)) frozenPathNoise)).prod
      (gaussianReal (1 - controlDecay ^ 2) frozenPathNoise)

/-- Native product-KL calculation for the exact forward and reverse innovation laws. -/
private theorem frozen_innovation_native_KL :
    klDiv frozenForwardInnovations frozenReverseInnovations =
      ENNReal.ofReal (2 * (1 - controlDecay ^ 2)) := by
  rw [frozenForwardInnovations, frozenReverseInnovations, gaussianARInnovationLaw,
    nativeKL_prod, nativeKL_prod]
  let fixedHalf : FEP.GaussianInformationGeometry.FixedVarianceGaussian := ⟨1 / 2, by norm_num⟩
  let fixedNoise : FEP.GaussianInformationGeometry.FixedVarianceGaussian :=
    ⟨frozenPathNoise, frozenPathNoise_pos⟩
  change (klDiv (fixedHalf.law 1) (fixedHalf.law (controlDecay ^ 2)) +
      klDiv (fixedNoise.law 0) (fixedNoise.law (controlDecay * (1 - controlDecay ^ 2)))) +
      klDiv (fixedNoise.law 0) (fixedNoise.law (1 - controlDecay ^ 2)) = _
  rw [fixedHalf.klDiv_law_eq_meanSquare, fixedNoise.klDiv_law_eq_meanSquare,
    fixedNoise.klDiv_law_eq_meanSquare]
  rw [← ENNReal.ofReal_add (by positivity) (by positivity),
    ← ENNReal.ofReal_add (by positivity) (by positivity)]
  congr 1
  change ((1 - controlDecay ^ 2) ^ 2 / (2 * (1 / 2 : ℝ)) +
      (0 - controlDecay * (1 - controlDecay ^ 2)) ^ 2 /
        (2 * ((1 - controlDecay ^ 2) / 2))) +
      (0 - (1 - controlDecay ^ 2)) ^ 2 /
        (2 * ((1 - controlDecay ^ 2) / 2)) = _
  have hDenominator : 1 - controlDecay ^ 2 ≠ 0 := by
    have h := controlDecay_bounds
    have hProduct : 0 < (1 - controlDecay) * (1 + controlDecay) :=
      mul_pos (sub_pos.mpr h.2) (by linarith [h.1])
    nlinarith [hProduct]
  field_simp [hDenominator]
  ring

/-! Repeated-time native support argument, with the zero-duration coordinate
copied and positive-duration noise supplied by an actual Gaussian row. -/

private def repeatedTripleBuild (decay : ℝ) (value : ℝ × ℝ) : InformationTriple :=
  ((value.1, value.1), decay * value.1 + value.2)

private def repeatedTripleLaw (mean : ℝ) (variance : ℝ≥0) (decay : ℝ) (noise : ℝ≥0) :
    Measure InformationTriple :=
  ((gaussianReal mean variance).prod (gaussianReal 0 noise)).map (repeatedTripleBuild decay)

private def repeatedFirstEquality : Set InformationTriple :=
  {value | value.1.1 = value.1.2}

private theorem repeatedFirstEquality_measurable : MeasurableSet repeatedFirstEquality := by
  unfold repeatedFirstEquality
  exact isClosed_eq (by fun_prop) (by fun_prop) |>.measurableSet

private theorem repeated_forward_support (mean : ℝ) (variance : ℝ≥0)
    (decay : ℝ) (noise : ℝ≥0) :
    repeatedTripleLaw mean variance decay noise repeatedFirstEquality = 1 := by
  rw [repeatedTripleLaw, Measure.map_apply (by unfold repeatedTripleBuild; fun_prop)
    repeatedFirstEquality_measurable]
  have hPreimage : repeatedTripleBuild decay ⁻¹' repeatedFirstEquality = Set.univ := by
    ext value
    simp [repeatedTripleBuild, repeatedFirstEquality]
  rw [hPreimage]
  exact measure_univ

private theorem repeated_reverse_support_null (mean : ℝ) (variance : ℝ≥0)
    (decay : ℝ) (noise : ℝ≥0) (hNoise : 0 < noise) :
    ((repeatedTripleLaw mean variance decay noise).map tripleReverseEquiv)
      repeatedFirstEquality = 0 := by
  rw [repeatedTripleLaw,
    Measure.map_map tripleReverseEquiv.measurable (by unfold repeatedTripleBuild; fun_prop),
    Measure.map_apply (by unfold repeatedTripleBuild; fun_prop) repeatedFirstEquality_measurable,
    Measure.prod_apply (repeatedFirstEquality_measurable.preimage
      (tripleReverseEquiv.measurable.comp (by unfold repeatedTripleBuild; fun_prop)))]
  apply lintegral_eq_zero_of_ae_eq_zero
  apply ae_of_all
  intro value
  have hFiber : Prod.mk value ⁻¹'
      ((tripleReverseEquiv ∘ repeatedTripleBuild decay) ⁻¹' repeatedFirstEquality) =
        {(1 - decay) * value} := by
    ext innovation
    change decay * value + innovation = value ↔ innovation = (1 - decay) * value
    constructor <;> intro h <;> linarith
  change (gaussianReal 0 noise)
    (Prod.mk value ⁻¹' ((tripleReverseEquiv ∘ repeatedTripleBuild decay) ⁻¹' repeatedFirstEquality)) = 0
  rw [hFiber]
  exact (gaussianReal_absolutelyContinuous 0 hNoise.ne') (measure_singleton _)

private theorem repeated_native_KL_infinite (mean : ℝ) (variance : ℝ≥0)
    (decay : ℝ) (noise : ℝ≥0) (hNoise : 0 < noise) :
    klDiv (repeatedTripleLaw mean variance decay noise)
      ((repeatedTripleLaw mean variance decay noise).map tripleReverseEquiv) = ∞ := by
  apply klDiv_of_not_ac
  intro hAC
  have hZero := hAC (repeated_reverse_support_null mean variance decay noise hNoise)
  rw [repeated_forward_support] at hZero
  exact one_ne_zero hZero


end ThreeTimeNativeInformation

section ThreeTimeCarrierBinding
open FEP.Fin4GaussianSemigroup FEPComposed.GaussianGridPath Finset

private def informationZeroIndex : Iic 0 := ⟨0, by simp⟩
private def informationOneZero : Iic 1 := ⟨0, by simp⟩
private def informationOneOne : Iic 1 := ⟨1, by simp⟩
def informationTwoZero : Iic 2 := ⟨0, by simp⟩
def informationTwoOne : Iic 2 := ⟨1, by simp⟩
def informationTwoTwo : Iic 2 := ⟨2, by simp⟩

private def informationPath0 (path : GridPath 0) : ℝ := path informationZeroIndex
private def informationPath1 (path : GridPath 1) : ℝ × ℝ :=
  (path informationOneZero, path informationOneOne)

def informationPath2Equiv : GridPath 2 ≃ᵐ InformationTriple where
  toFun path := ((path informationTwoZero, path informationTwoOne), path informationTwoTwo)
  invFun value index := if index.1 = 0 then value.1.1 else
    if index.1 = 1 then value.1.2 else value.2
  left_inv path := by
    funext index
    rcases index with ⟨index, hIndex⟩
    have hBound : index ≤ 2 := mem_Iic.mp hIndex
    interval_cases index <;> rfl
  right_inv value := by rcases value with ⟨⟨x, y⟩, z⟩; rfl
  measurable_toFun := by
    change Measurable (fun path : GridPath 2 =>
      ((path informationTwoZero, path informationTwoOne), path informationTwoTwo))
    fun_prop
  measurable_invFun := by
    change Measurable (fun (value : InformationTriple) (index : Iic 2) =>
      if index.1 = 0 then value.1.1 else if index.1 = 1 then value.1.2 else value.2)
    apply Measurable.of_eval
    intro index
    split_ifs <;> fun_prop

private theorem informationPath2_reverse :
    informationPath2Equiv ∘ reverseGridPath 2 =
      tripleReverseEquiv ∘ informationPath2Equiv := by
  funext path
  rfl

def informationGrid : TimeGrid where
  time n := (n : ℝ≥0) / 4
  monotone_time := by
    intro left right hOrder
    exact div_le_div_of_nonneg_right (by exact_mod_cast hOrder) (by norm_num)

private theorem informationGrid_duration_zero :
    informationGrid.time 1 - informationGrid.time 0 = (1 / 4 : ℝ≥0) := by
  norm_num [informationGrid]

private theorem informationGrid_duration_one :
    informationGrid.time 2 - informationGrid.time 1 = (1 / 4 : ℝ≥0) := by
  apply NNReal.eq
  norm_num [informationGrid, NNReal.coe_sub_def]

private theorem informationNativeAR_step :
    (scalarParameters 0).ouTransition (1 / 4) =
      gaussianARStep controlDecay frozenPathNoise := by
  apply DFunLike.ext _ _
  intro state
  change gaussianReal ((scalarParameters 0).transitionMean (1 / 4) state)
      ((scalarParameters 0).transitionVariance (1 / 4)) =
    gaussianReal (controlDecay * state) frozenPathNoise
  congr 1
  · simp [ScalarOUParameters.transitionMean, ScalarOUParameters.decay,
      scalarParameters, FEP.LinearGaussianSemigroup.LinearGaussianParameters.finOneScalarParameters,
      controlDecay]
    norm_num
  · apply NNReal.eq
    change ((scalarParameters 0).stationaryVariance : ℝ) *
      (1 - (scalarParameters 0).decay (1 / 4) ^ 2) = (1 - controlDecay ^ 2) / 2
    rw [ScalarOUParameters.stationaryVariance_eq]
    norm_num [scalarParameters, FEP.LinearGaussianSemigroup.LinearGaussianParameters.finOneScalarParameters,
      ScalarOUParameters.decay, controlDecay]
    ring

private def informationNewCoordinate (n : ℕ)
    (path : Ioc n (n + 1) → ℝ) : ℝ :=
  path ⟨n + 1, by simp⟩

private theorem informationNewCoordinate_singleton (n : ℕ) :
    informationNewCoordinate n ∘ (MeasurableEquiv.piSingleton n (X := fun _ => ℝ)) = id := by
  funext value
  rfl

private theorem informationGrid_rows_zero (path : GridPath 0) :
    (((ouGridStep (scalarParameters 0) informationGrid 0).map
      (MeasurableEquiv.piSingleton 0 (X := fun _ => ℝ))) path).map (informationNewCoordinate 0) =
      gaussianARStep controlDecay frozenPathNoise (informationPath0 path) := by
  rw [Kernel.map_apply _ (MeasurableEquiv.piSingleton 0 (X := fun _ => ℝ)).measurable,
    ouGridStep, Kernel.comap_apply,
    Measure.map_map (by unfold informationNewCoordinate; fun_prop)
      (MeasurableEquiv.piSingleton 0 (X := fun _ => ℝ)).measurable,
    informationNewCoordinate_singleton, Measure.map_id,
    informationGrid_duration_zero, informationNativeAR_step]
  rfl

private theorem informationGrid_rows_one (path : GridPath 1) :
    (((ouGridStep (scalarParameters 0) informationGrid 1).map
      (MeasurableEquiv.piSingleton 1 (X := fun _ => ℝ))) path).map (informationNewCoordinate 1) =
      gaussianARStep controlDecay frozenPathNoise ((informationPath1 path).2) := by
  rw [Kernel.map_apply _ (MeasurableEquiv.piSingleton 1 (X := fun _ => ℝ)).measurable,
    ouGridStep, Kernel.comap_apply,
    Measure.map_map (by unfold informationNewCoordinate; fun_prop)
      (MeasurableEquiv.piSingleton 1 (X := fun _ => ℝ)).measurable,
    informationNewCoordinate_singleton, Measure.map_id,
    informationGrid_duration_one, informationNativeAR_step]
  rfl

private theorem information_scalar_zero :
    (scalarNativeGridLaw 0 informationGrid (gaussianReal 1 (1 / 2)) 0).map informationPath0 =
      gaussianReal 1 (1 / 2) := by
  unfold scalarNativeGridLaw ouPartialTraj
  rw [Kernel.partialTraj_self, Measure.id_comp,
    Measure.map_map (by unfold informationPath0; fun_prop) (by fun_prop)]
  have hIdentity : informationPath0 ∘ (fun state : ℝ => fun _ : Iic 0 => state) = id := by
    funext state
    rfl
  rw [hIdentity, Measure.map_id]

private theorem information_scalar_one :
    (scalarNativeGridLaw 0 informationGrid (gaussianReal 1 (1 / 2)) 1).map informationPath1 =
      (gaussianReal 1 (1 / 2)) ⊗ₘ gaussianARStep controlDecay frozenPathNoise := by
  rw [scalarNativeGridLaw_succ,
    Measure.map_map (by unfold informationPath1; fun_prop) (measurable_IicProdIoc (X := fun _ => ℝ) (m := 0) (n := 1))]
  have hConcat : informationPath1 ∘ (IicProdIoc 0 1 (X := fun _ => ℝ)) =
      Prod.map informationPath0 (informationNewCoordinate 0) := by
    funext value
    rfl
  rw [hConcat,
    map_compProd_intertwining _ _ _ _ _
      (by unfold informationPath0; fun_prop)
      (by unfold informationNewCoordinate; fun_prop) informationGrid_rows_zero,
    information_scalar_zero]

private theorem information_scalar_three_time_joint :
    (scalarNativeGridLaw 0 informationGrid (gaussianReal 1 (1 / 2)) 2).map
      informationPath2Equiv =
        gaussianARTripleLaw 1 (1 / 2) controlDecay frozenPathNoise := by
  rw [scalarNativeGridLaw_succ,
    Measure.map_map informationPath2Equiv.measurable (measurable_IicProdIoc (X := fun _ => ℝ) (m := 1) (n := 2))]
  have hConcat : informationPath2Equiv ∘ (IicProdIoc 1 2 (X := fun _ => ℝ)) =
      Prod.map informationPath1 (informationNewCoordinate 1) := by
    funext value
    rfl
  rw [hConcat,
    map_compProd_intertwining _ _
      (((gaussianARStep controlDecay frozenPathNoise).comap Prod.snd measurable_snd) : Kernel (ℝ × ℝ) ℝ)
      informationPath1 (informationNewCoordinate 1)
      (by unfold informationPath1; fun_prop)
      (by unfold informationNewCoordinate; fun_prop)
      (by intro path; exact informationGrid_rows_one path), information_scalar_one]
  rfl

def informationFullInitial : Measure StandardizedState :=
  multivariateGaussian normalizedAllOnes FEP.Fin4GaussianSemigroup.Sigma

private theorem information_full_initial_projection :
    informationFullInitial.map allOnesProjection = gaussianReal 1 (1 / 2) := by
  rw [informationFullInitial, gaussianSigma_scalar_marginal,
    allOnes_projection_nontrivial]

/-- Actual full-state JOINT binding; no initial hidden-mode reset is used. -/
private theorem information_full_three_time_joint :
    ((fullNativeGridLaw 0 informationGrid informationFullInitial 2).map
      (projectFullPath 2)).map informationPath2Equiv =
        gaussianARTripleLaw 1 (1 / 2) controlDecay frozenPathNoise := by
  have : IsProbabilityMeasure informationFullInitial := by
    unfold informationFullInitial
    infer_instance
  rw [full_native_path_projection, information_full_initial_projection,
    information_scalar_three_time_joint]

end ThreeTimeCarrierBinding

section NativeReverseInnovationFactorization

def originalInnovationCoordinate (index : Fin 3) (value : InformationTriple) : ℝ :=
  ![value.1.1, value.1.2, value.2] index

private def originalInnovationVariance (index : Fin 3) : ℝ≥0 :=
  ![(1 / 2 : ℝ≥0), frozenPathNoise, frozenPathNoise] index

private def originalInnovationMean (index : Fin 3) : ℝ := ![1, 0, 0] index

instance originalInnovation_isGaussian : IsGaussian frozenForwardInnovations := by
  unfold frozenForwardInnovations gaussianARInnovationLaw
  infer_instance

instance originalInnovation_probability : IsProbabilityMeasure frozenForwardInnovations := by
  unfold frozenForwardInnovations gaussianARInnovationLaw
  infer_instance

private theorem originalInnovation_marginal (index : Fin 3) :
    frozenForwardInnovations.map (originalInnovationCoordinate index) =
      gaussianReal (originalInnovationMean index) (originalInnovationVariance index) := by
  fin_cases index
  · have hFunction : originalInnovationCoordinate 0 = Prod.fst ∘ Prod.fst := rfl
    change frozenForwardInnovations.map (originalInnovationCoordinate 0) = gaussianReal 1 (1 / 2)
    rw [hFunction, ← Measure.map_map measurable_fst measurable_fst,
      frozenForwardInnovations, gaussianARInnovationLaw, Measure.map_fst_prod,
      measure_univ, one_smul, Measure.map_fst_prod, measure_univ, one_smul]
  · have hFunction : originalInnovationCoordinate 1 = Prod.snd ∘ Prod.fst := rfl
    change frozenForwardInnovations.map (originalInnovationCoordinate 1) = gaussianReal 0 frozenPathNoise
    rw [hFunction, ← Measure.map_map measurable_snd measurable_fst,
      frozenForwardInnovations, gaussianARInnovationLaw, Measure.map_fst_prod,
      measure_univ, one_smul, Measure.map_snd_prod, measure_univ, one_smul]
  · change (((gaussianReal 1 (1 / 2)).prod (gaussianReal 0 frozenPathNoise)).prod
      (gaussianReal 0 frozenPathNoise)).map Prod.snd = gaussianReal 0 frozenPathNoise
    rw [Measure.map_snd_prod, measure_univ, one_smul]

private theorem originalInnovation_memLp (index : Fin 3) :
    MemLp (originalInnovationCoordinate index) 2 frozenForwardInnovations := by
  have hGaussian : MemLp id 2
      (frozenForwardInnovations.map (originalInnovationCoordinate index)) := by
    rw [originalInnovation_marginal]
    exact memLp_id_gaussianReal 2
  simpa only [Function.comp_def, id_eq] using
    hGaussian.comp_measurePreserving
      (show MeasurePreserving (originalInnovationCoordinate index)
        frozenForwardInnovations (frozenForwardInnovations.map (originalInnovationCoordinate index))
        from ⟨by unfold originalInnovationCoordinate; fun_prop, rfl⟩)

private theorem originalInnovation_integral (index : Fin 3) :
    (∫ value, originalInnovationCoordinate index value ∂frozenForwardInnovations) =
      originalInnovationMean index := by
  have hMap : (∫ coordinate : ℝ, coordinate
      ∂frozenForwardInnovations.map (originalInnovationCoordinate index)) =
      (∫ value, originalInnovationCoordinate index value ∂frozenForwardInnovations) :=
    integral_map (by unfold originalInnovationCoordinate; fun_prop) (by fun_prop)
  rw [originalInnovation_marginal, integral_id_gaussianReal] at hMap
  exact hMap.symm

private theorem originalInnovation_variance (index : Fin 3) :
    Var[originalInnovationCoordinate index; frozenForwardInnovations] =
      originalInnovationVariance index := by
  have hMap := variance_map (μ := frozenForwardInnovations)
    (X := id) (Y := originalInnovationCoordinate index) (by fun_prop)
    (by unfold originalInnovationCoordinate; fun_prop)
  rw [originalInnovation_marginal, variance_id_gaussianReal] at hMap
  simpa only [Function.comp_def, id_eq] using hMap.symm

private theorem originalInnovation_cov01 :
    cov[originalInnovationCoordinate 0, originalInnovationCoordinate 1;
      frozenForwardInnovations] = 0 := by
  let pairLaw := (gaussianReal 1 (1 / 2)).prod (gaussianReal 0 frozenPathNoise)
  have hPairMap : frozenForwardInnovations.map Prod.fst = pairLaw := by
    rw [frozenForwardInnovations, gaussianARInnovationLaw, Measure.map_fst_prod,
      measure_univ, one_smul]
  have hBase : cov[Prod.fst, Prod.snd; pairLaw] = 0 :=
    covariance_fst_snd_prod (memLp_id_gaussianReal 2) (memLp_id_gaussianReal 2)
  have hMap := covariance_map (μ := frozenForwardInnovations)
    (X := Prod.fst) (Y := Prod.snd) (Z := Prod.fst) (by fun_prop) (by fun_prop) (by fun_prop)
  rw [hPairMap] at hMap
  exact hMap.symm.trans hBase

private theorem originalInnovation_cov02 :
    cov[originalInnovationCoordinate 0, originalInnovationCoordinate 2;
      frozenForwardInnovations] = 0 := by
  change cov[fun value : InformationTriple => value.1.1,
    fun value => value.2;
    ((gaussianReal 1 (1 / 2)).prod (gaussianReal 0 frozenPathNoise)).prod
      (gaussianReal 0 frozenPathNoise)] = 0
  exact covariance_fst_snd_prod
    ((memLp_id_gaussianReal (μ := 1) (v := (1 / 2 : ℝ≥0)) 2).comp_fst
      (gaussianReal 0 frozenPathNoise)) (memLp_id_gaussianReal 2)

private theorem originalInnovation_cov12 :
    cov[originalInnovationCoordinate 1, originalInnovationCoordinate 2;
      frozenForwardInnovations] = 0 := by
  change cov[fun value : InformationTriple => value.1.2,
    fun value => value.2;
    ((gaussianReal 1 (1 / 2)).prod (gaussianReal 0 frozenPathNoise)).prod
      (gaussianReal 0 frozenPathNoise)] = 0
  exact covariance_fst_snd_prod
    ((memLp_id_gaussianReal (μ := 0) (v := frozenPathNoise) 2).comp_snd
      (gaussianReal 1 (1 / 2))) (memLp_id_gaussianReal 2)

private theorem originalInnovation_covariance (left right : Fin 3) :
    cov[originalInnovationCoordinate left, originalInnovationCoordinate right;
      frozenForwardInnovations] =
      if left = right then (originalInnovationVariance left : ℝ) else 0 := by
  fin_cases left <;> fin_cases right
  · change cov[originalInnovationCoordinate 0, originalInnovationCoordinate 0; frozenForwardInnovations] = _
    rw [covariance_self (by unfold originalInnovationCoordinate; fun_prop), originalInnovation_variance]
    rfl
  · exact originalInnovation_cov01
  · exact originalInnovation_cov02
  · rw [covariance_comm]; exact originalInnovation_cov01
  · change cov[originalInnovationCoordinate 1, originalInnovationCoordinate 1; frozenForwardInnovations] = _
    rw [covariance_self (by unfold originalInnovationCoordinate; fun_prop), originalInnovation_variance]
    rfl
  · exact originalInnovation_cov12
  · rw [covariance_comm]; exact originalInnovation_cov02
  · rw [covariance_comm]; exact originalInnovation_cov12
  · change cov[originalInnovationCoordinate 2, originalInnovationCoordinate 2; frozenForwardInnovations] = _
    rw [covariance_self (by unfold originalInnovationCoordinate; fun_prop), originalInnovation_variance]
    rfl

private def tripleCoordinateCLM (index : Fin 3) : InformationTriple →L[ℝ] ℝ :=
  ![(ContinuousLinearMap.fst ℝ ℝ ℝ).comp (ContinuousLinearMap.fst ℝ (ℝ × ℝ) ℝ),
    (ContinuousLinearMap.snd ℝ ℝ ℝ).comp (ContinuousLinearMap.fst ℝ (ℝ × ℝ) ℝ),
    ContinuousLinearMap.snd ℝ (ℝ × ℝ) ℝ] index

private def tripleLinearCLM (coefficient : Fin 3 → ℝ) : InformationTriple →L[ℝ] ℝ :=
  ∑ index, coefficient index • tripleCoordinateCLM index

private def tripleLinear (coefficient : Fin 3 → ℝ) (value : InformationTriple) : ℝ :=
  ∑ index, coefficient index * originalInnovationCoordinate index value

private theorem tripleLinearCLM_apply (coefficient : Fin 3 → ℝ) (value : InformationTriple) :
    tripleLinearCLM coefficient value = tripleLinear coefficient value := by
  simp [tripleLinearCLM, tripleLinear, tripleCoordinateCLM,
    originalInnovationCoordinate, Fin.sum_univ_succ]

private theorem tripleLinear_integral (coefficient : Fin 3 → ℝ) :
    (∫ value, tripleLinear coefficient value ∂frozenForwardInnovations) = coefficient 0 := by
  unfold tripleLinear
  rw [integral_finsetSum]
  · simp only [integral_const_mul, originalInnovation_integral]
    simp [originalInnovationMean, Fin.sum_univ_succ]
  · intro index _
    exact ((originalInnovation_memLp index).integrable one_le_two).const_mul _

private theorem tripleLinear_covariance (left right : Fin 3 → ℝ) :
    cov[tripleLinear left, tripleLinear right; frozenForwardInnovations] =
      (1 / 2 : ℝ) * left 0 * right 0 +
        (frozenPathNoise : ℝ) * left 1 * right 1 +
        (frozenPathNoise : ℝ) * left 2 * right 2 := by
  unfold tripleLinear
  rw [covariance_fun_sum_fun_sum]
  · simp_rw [covariance_const_mul_left, covariance_const_mul_right,
      originalInnovation_covariance]
    simp [originalInnovationVariance, Fin.sum_univ_succ]
    ring
  · intro index
    exact (originalInnovation_memLp index).const_mul _
  · intro index
    exact (originalInnovation_memLp index).const_mul _

private def reverseInnovationCoefficient (index : Fin 3) : Fin 3 → ℝ :=
  ![![controlDecay ^ 2, controlDecay, 1],
    ![controlDecay * (1 - controlDecay ^ 2), 1 - controlDecay ^ 2, -controlDecay],
    ![1 - controlDecay ^ 2, -controlDecay, 0]] index

private def actualReverseInnovation (index : Fin 3) : InformationTriple → ℝ :=
  tripleLinear (reverseInnovationCoefficient index)

private theorem actualReverseInnovation_measurable (index : Fin 3) :
    Measurable (actualReverseInnovation index) := by
  have h : Measurable (fun value : InformationTriple =>
      tripleLinearCLM (reverseInnovationCoefficient index) value) :=
    (tripleLinearCLM (reverseInnovationCoefficient index)).continuous.measurable
  simpa only [tripleLinearCLM_apply, actualReverseInnovation] using h

private theorem actualReverseInnovation_mean (index : Fin 3) :
    (∫ value, actualReverseInnovation index value ∂frozenForwardInnovations) =
      ![controlDecay ^ 2, controlDecay * (1 - controlDecay ^ 2), 1 - controlDecay ^ 2] index := by
  rw [actualReverseInnovation, tripleLinear_integral]
  fin_cases index <;> rfl

private theorem actualReverseInnovation_covariance (left right : Fin 3) :
    cov[actualReverseInnovation left, actualReverseInnovation right;
      frozenForwardInnovations] =
      if left = right then (originalInnovationVariance left : ℝ) else 0 := by
  rw [actualReverseInnovation, actualReverseInnovation, tripleLinear_covariance]
  fin_cases left <;> fin_cases right <;>
    norm_num [reverseInnovationCoefficient, originalInnovationVariance]
  all_goals
    have hQ : (frozenPathNoise : ℝ) = (1 - controlDecay ^ 2) / 2 := rfl
    simp only [hQ]
    ring

private theorem actualReverseInnovation_gaussian (index : Fin 3) :
    HasGaussianLaw (actualReverseInnovation index) frozenForwardInnovations := by
  have h := (IsGaussian.hasGaussianLaw_id (μ := frozenForwardInnovations)).map_fun
    (tripleLinearCLM (reverseInnovationCoefficient index))
  simpa only [id_eq, tripleLinearCLM_apply, actualReverseInnovation] using h

private theorem actualReverseInnovation_marginal (index : Fin 3) :
    frozenForwardInnovations.map (actualReverseInnovation index) =
      gaussianReal
        (![controlDecay ^ 2, controlDecay * (1 - controlDecay ^ 2), 1 - controlDecay ^ 2] index)
        (originalInnovationVariance index) := by
  have h := (actualReverseInnovation_gaussian index).map_eq_gaussianReal
  rw [actualReverseInnovation_mean,
    ← covariance_self (actualReverseInnovation_gaussian index).aemeasurable,
    actualReverseInnovation_covariance] at h
  simp only [ite_true] at h
  simpa only [Real.toNNReal_coe] using h

private theorem actualReverseInnovation_pair_independent :
    IndepFun (fun value => (actualReverseInnovation 0 value, actualReverseInnovation 1 value))
      (actualReverseInnovation 2) frozenForwardInnovations := by
  let pairCLM : InformationTriple →L[ℝ] (Bool → ℝ) :=
    ContinuousLinearMap.pi fun index =>
      tripleLinearCLM (reverseInnovationCoefficient (if index then 1 else 0))
  let thirdCLM : InformationTriple →L[ℝ] (Unit → ℝ) :=
    ContinuousLinearMap.pi fun _ => tripleLinearCLM (reverseInnovationCoefficient 2)
  have hGaussian := (IsGaussian.hasGaussianLaw_id (μ := frozenForwardInnovations)).map_fun
    (pairCLM.prod thirdCLM)
  have hIndependent := hGaussian.indepFun_of_covariance_eval (fun index _ => by
    change cov[actualReverseInnovation (if index then 1 else 0), actualReverseInnovation 2;
      frozenForwardInnovations] = 0
    cases index <;> simp [actualReverseInnovation_covariance])
  have h : IndepFun
      (fun value => (pairCLM value false, pairCLM value true))
      (fun value => thirdCLM value ()) frozenForwardInnovations := hIndependent.comp
    (φ := fun values : Bool → ℝ => (values false, values true))
    (ψ := fun values : Unit → ℝ => values ())
    ((measurable_pi_apply false).prodMk (measurable_pi_apply true)) (measurable_pi_apply ())
  simpa [pairCLM, thirdCLM, tripleLinearCLM_apply, actualReverseInnovation] using h

private theorem actualReverseInnovation_first_two_independent :
    IndepFun (actualReverseInnovation 0) (actualReverseInnovation 1)
      frozenForwardInnovations := by
  have hGaussian : HasGaussianLaw
      (fun value : InformationTriple =>
        (actualReverseInnovation 0 value, actualReverseInnovation 1 value))
        frozenForwardInnovations := by
    have h := (IsGaussian.hasGaussianLaw_id (μ := frozenForwardInnovations)).map_fun
      ((tripleLinearCLM (reverseInnovationCoefficient 0)).prod
        (tripleLinearCLM (reverseInnovationCoefficient 1)))
    simpa only [id_eq, ContinuousLinearMap.prod_apply, tripleLinearCLM_apply,
      actualReverseInnovation] using h
  apply hGaussian.indepFun_of_covariance_eq_zero
  simp [actualReverseInnovation_covariance]

/-- Actual native Gaussian JOINT product derived from the linear transformed
Gaussian source, native covariance-zero independence, and native marginals. -/
private theorem actualReverseInnovation_joint_product :
    frozenForwardInnovations.map (fun value =>
      ((actualReverseInnovation 0 value, actualReverseInnovation 1 value),
        actualReverseInnovation 2 value)) = frozenReverseInnovations := by
  rw [actualReverseInnovation_pair_independent.map_prod_eq_prod_map_map
    ((actualReverseInnovation_measurable 0).prodMk
      (actualReverseInnovation_measurable 1)).aemeasurable
    (actualReverseInnovation_measurable 2).aemeasurable,
    actualReverseInnovation_first_two_independent.map_prod_eq_prod_map_map
      (actualReverseInnovation_measurable 0).aemeasurable
      (actualReverseInnovation_measurable 1).aemeasurable,
    actualReverseInnovation_marginal, actualReverseInnovation_marginal,
    actualReverseInnovation_marginal]
  rfl

/-- The compiled native AR joint's coordinate reversal and triangular
innovation map produce exactly the derived product joint, not just its means. -/
private theorem frozen_reverse_innovation_joint :
    (gaussianARTripleLaw 1 (1 / 2) controlDecay frozenPathNoise).map
      ((tripleInnovationEquiv controlDecay) ∘ tripleReverseEquiv) =
        frozenReverseInnovations := by
  rw [gaussianARTripleLaw_eq_innovations,
    Measure.map_map (by fun_prop) (by unfold tripleFromInnovations; fun_prop)]
  change frozenForwardInnovations.map
    (((tripleInnovationEquiv controlDecay) ∘ tripleReverseEquiv) ∘
      tripleFromInnovations controlDecay) = _
  have hFunction : (((tripleInnovationEquiv controlDecay) ∘ tripleReverseEquiv) ∘
      tripleFromInnovations controlDecay) =
      fun value => ((actualReverseInnovation 0 value, actualReverseInnovation 1 value),
        actualReverseInnovation 2 value) := by
    funext value
    rcases value with ⟨⟨x, e1⟩, e2⟩
    apply Prod.ext
    · apply Prod.ext
      all_goals simp [Function.comp_def, tripleInnovationEquiv, tripleReverseEquiv,
        tripleInnovations, tripleReverse, tripleFromInnovations, actualReverseInnovation,
        tripleLinear, reverseInnovationCoefficient, originalInnovationCoordinate,
        Fin.sum_univ_succ]; ring
    · simp [Function.comp_def, tripleInnovationEquiv, tripleReverseEquiv,
        tripleInnovations, tripleReverse, tripleFromInnovations, actualReverseInnovation,
        tripleLinear, reverseInnovationCoefficient, originalInnovationCoordinate,
        Fin.sum_univ_succ]
      ring
  rw [hFunction, actualReverseInnovation_joint_product]

end NativeReverseInnovationFactorization


section FrozenNativeGrid
open FEP.Fin4GaussianSemigroup FEPComposed.GaussianGridPath Finset

private theorem native_grid_zero (grid : TimeGrid) (initial : Measure ℝ)
    [IsProbabilityMeasure initial] :
    (scalarNativeGridLaw 0 grid initial 0).map informationPath0 = initial := by
  unfold scalarNativeGridLaw ouPartialTraj
  rw [Kernel.partialTraj_self, Measure.id_comp,
    Measure.map_map (by unfold informationPath0; fun_prop) (by fun_prop)]
  have hIdentity : informationPath0 ∘ (fun state : ℝ => fun _ : Iic 0 => state) = id := by
    funext state
    rfl
  rw [hIdentity, Measure.map_id]

private theorem native_grid_row (grid : TimeGrid) (n : ℕ) (path : GridPath n) :
    (((ouGridStep (scalarParameters 0) grid n).map
      (MeasurableEquiv.piSingleton n (X := fun _ => ℝ))) path).map (informationNewCoordinate n) =
      (scalarParameters 0).ouTransition (grid.time (n + 1) - grid.time n)
        (path ⟨n, mem_Iic.mpr le_rfl⟩) := by
  rw [Kernel.map_apply _ (MeasurableEquiv.piSingleton n (X := fun _ => ℝ)).measurable,
    ouGridStep, Kernel.comap_apply,
    Measure.map_map (by unfold informationNewCoordinate; fun_prop)
      (MeasurableEquiv.piSingleton n (X := fun _ => ℝ)).measurable,
    informationNewCoordinate_singleton, Measure.map_id]

private theorem native_grid_one (grid : TimeGrid) (initial : Measure ℝ)
    [IsProbabilityMeasure initial] :
    (scalarNativeGridLaw 0 grid initial 1).map informationPath1 =
      initial ⊗ₘ (scalarParameters 0).ouTransition (grid.time 1 - grid.time 0) := by
  rw [scalarNativeGridLaw_succ,
    Measure.map_map (by unfold informationPath1; fun_prop)
      (measurable_IicProdIoc (X := fun _ => ℝ) (m := 0) (n := 1))]
  have hConcat : informationPath1 ∘ (IicProdIoc 0 1 (X := fun _ => ℝ)) =
      Prod.map informationPath0 (informationNewCoordinate 0) := by funext value; rfl
  rw [hConcat,
    map_compProd_intertwining _ _ _ _ _
      (by unfold informationPath0; fun_prop)
      (by unfold informationNewCoordinate; fun_prop)
      (by intro path; exact native_grid_row grid 0 path), native_grid_zero]

private theorem native_grid_three (grid : TimeGrid) (initial : Measure ℝ)
    [IsProbabilityMeasure initial] :
    (scalarNativeGridLaw 0 grid initial 2).map informationPath2Equiv =
      (initial ⊗ₘ (scalarParameters 0).ouTransition (grid.time 1 - grid.time 0)) ⊗ₘ
        ((scalarParameters 0).ouTransition (grid.time 2 - grid.time 1)).comap
          (fun pair : ℝ × ℝ => pair.2) measurable_snd := by
  rw [scalarNativeGridLaw_succ,
    Measure.map_map informationPath2Equiv.measurable
      (measurable_IicProdIoc (X := fun _ => ℝ) (m := 1) (n := 2))]
  have hConcat : informationPath2Equiv ∘ (IicProdIoc 1 2 (X := fun _ => ℝ)) =
      Prod.map informationPath1 (informationNewCoordinate 1) := by funext value; rfl
  rw [hConcat,
    map_compProd_intertwining _ _
      ((((scalarParameters 0).ouTransition (grid.time 2 - grid.time 1)).comap
        Prod.snd measurable_snd) : Kernel (ℝ × ℝ) ℝ)
      informationPath1 (informationNewCoordinate 1)
      (by unfold informationPath1; fun_prop)
      (by unfold informationNewCoordinate; fun_prop)
      (by intro path; exact native_grid_row grid 1 path), native_grid_one]

/-- The actual full-state path projected to all three retained coordinates. -/
def studyProjectedLaw (grid : TimeGrid) : Measure (GridPath 2) :=
  (fullNativeGridLaw 0 grid informationFullInitial 2).map (projectFullPath 2)

instance studyProjectedLaw_probability (grid : TimeGrid) :
    IsProbabilityMeasure (studyProjectedLaw grid) := by
  have : IsProbabilityMeasure informationFullInitial := by unfold informationFullInitial; infer_instance
  unfold studyProjectedLaw
  infer_instance

/-- Coordinate reversal of the same finite law, with every coordinate retained. -/
def studyReverseLaw (grid : TimeGrid) : Measure (GridPath 2) :=
  (studyProjectedLaw grid).map (reverseGridPath 2)

instance studyReverseLaw_probability (grid : TimeGrid) :
    IsProbabilityMeasure (studyReverseLaw grid) := by
  unfold studyReverseLaw
  infer_instance

/-- Genuine full-state nonstationary path binding to the native chronological
AR joint at times 0,1/4,1/2, initialized at N(u,Sigma). -/
theorem nonstationary_native_grid :
    (studyProjectedLaw informationGrid).map informationPath2Equiv =
      gaussianARTripleLaw 1 (1 / 2) controlDecay frozenPathNoise := by
  exact information_full_three_time_joint

private theorem study_reverse_tuple (grid : TimeGrid) :
    (studyReverseLaw grid).map informationPath2Equiv =
      ((studyProjectedLaw grid).map informationPath2Equiv).map tripleReverseEquiv := by
  rw [studyReverseLaw, Measure.map_map informationPath2Equiv.measurable
    (reverseGridPath_measurable 2), informationPath2_reverse,
    Measure.map_map tripleReverseEquiv.measurable informationPath2Equiv.measurable]

/-- Actual native finite-path KL, obtained by invertible measurable coordinate
maps and native Gaussian product KL. It is not a supplied logdet certificate. -/
theorem finite_grid_kl :
    klDiv (studyProjectedLaw informationGrid) (studyReverseLaw informationGrid) =
      ENNReal.ofReal (2 * (1 - controlDecay ^ 2)) := by
  rw [← nativeKL_map_equiv (studyProjectedLaw informationGrid)
      (studyReverseLaw informationGrid) informationPath2Equiv,
    nonstationary_native_grid, study_reverse_tuple, nonstationary_native_grid]
  have : IsProbabilityMeasure (gaussianARTripleLaw 1 (1 / 2) controlDecay frozenPathNoise) := by
    unfold gaussianARTripleLaw
    infer_instance
  rw [← nativeKL_map_equiv _ _ (tripleInnovationEquiv controlDecay),
    gaussianARTripleLaw_innovation_map,
    Measure.map_map (tripleInnovationEquiv controlDecay).measurable tripleReverseEquiv.measurable,
    frozen_reverse_innovation_joint]
  exact frozen_innovation_native_KL

private theorem finite_grid_value_pos : 0 < 2 * (1 - controlDecay ^ 2) := by
  rcases controlDecay_bounds with ⟨hPositive, hLess⟩
  have hProduct : 0 < (1 - controlDecay) * (1 + controlDecay) := by positivity
  nlinarith

theorem finite_grid_kl_positive :
    0 < klDiv (studyProjectedLaw informationGrid) (studyReverseLaw informationGrid) := by
  rw [finite_grid_kl]
  exact ENNReal.ofReal_pos.mpr finite_grid_value_pos

/-- Native absolute continuity and log-ratio integrability follow from the
proved finite divergence of the actual forward and reverse-aligned path laws. -/
theorem finite_grid_support :
    studyProjectedLaw informationGrid ≪ studyReverseLaw informationGrid ∧
      Integrable (llr (studyProjectedLaw informationGrid) (studyReverseLaw informationGrid))
        (studyProjectedLaw informationGrid) := by
  apply klDiv_ne_top_iff.mp
  rw [finite_grid_kl]
  exact ENNReal.ofReal_ne_top

/-- Repeated-time control retains both zero-time coordinates. -/
def repeatedStudyGrid : TimeGrid where
  time n := ((n - 1 : ℕ) : ℝ≥0) / 4
  monotone_time := by
    intro left right hOrder
    apply div_le_div_of_nonneg_right _ (by norm_num)
    exact_mod_cast Nat.sub_le_sub_right hOrder 1

private theorem repeated_study_tuple :
    (studyProjectedLaw repeatedStudyGrid).map informationPath2Equiv =
      repeatedTripleLaw 1 (1 / 2) controlDecay frozenPathNoise := by
  have : IsProbabilityMeasure informationFullInitial := by unfold informationFullInitial; infer_instance
  rw [studyProjectedLaw, full_native_path_projection, information_full_initial_projection,
    native_grid_three]
  have hZero : repeatedStudyGrid.time 1 - repeatedStudyGrid.time 0 = 0 := by norm_num [repeatedStudyGrid]
  have hQuarter : repeatedStudyGrid.time 2 - repeatedStudyGrid.time 1 = (1 / 4 : ℝ≥0) := by
    apply NNReal.eq
    norm_num [repeatedStudyGrid, NNReal.coe_sub_def]
  rw [hZero, hQuarter, ScalarOUParameters.ouTransition_zero, informationNativeAR_step,
    Measure.compProd_id, gaussianAR_compProd]
  have hProduct : ((gaussianReal 1 (1 / 2)).map Function.diag).prod
      (gaussianReal 0 frozenPathNoise) =
      ((gaussianReal 1 (1 / 2)).prod (gaussianReal 0 frozenPathNoise)).map
        (Prod.map Function.diag id) := by
    simpa only [Measure.map_id] using
      Measure.map_prod_map (gaussianReal 1 (1 / 2)) (gaussianReal 0 frozenPathNoise)
        (by fun_prop : Measurable Function.diag) measurable_id
  rw [hProduct, Measure.map_map (by fun_prop) (by fun_prop)]
  rfl

/-- An explicit measurable support witness proves native non-AC and infinity
for the actual projected repeated grid (0,0,1/4). -/
theorem singular_grid_infinite_kl :
    klDiv (studyProjectedLaw repeatedStudyGrid) (studyReverseLaw repeatedStudyGrid) = ∞ := by
  rw [← nativeKL_map_equiv _ _ informationPath2Equiv,
    study_reverse_tuple, repeated_study_tuple]
  exact repeated_native_KL_infinite 1 (1 / 2) controlDecay frozenPathNoise frozenPathNoise_pos

/-- All-zero repeated grids are a supported zero-divergence control. -/
def allZeroStudyGrid : TimeGrid where
  time _ := 0
  monotone_time := monotone_const

private theorem allZero_study_tuple :
    (studyProjectedLaw allZeroStudyGrid).map informationPath2Equiv =
      (gaussianReal 1 (1 / 2)).map (fun value => ((value, value), value)) := by
  have : IsProbabilityMeasure informationFullInitial := by unfold informationFullInitial; infer_instance
  rw [studyProjectedLaw, full_native_path_projection, information_full_initial_projection,
    native_grid_three]
  simp only [allZeroStudyGrid, tsub_self, ScalarOUParameters.ouTransition_zero]
  rw [Measure.compProd_id, Kernel.id_comap measurable_snd, Measure.compProd_deterministic measurable_snd,
    Measure.map_map (by fun_prop) (by fun_prop)]
  rfl

theorem all_zero_grid_kl :
    klDiv (studyProjectedLaw allZeroStudyGrid) (studyReverseLaw allZeroStudyGrid) = 0 := by
  rw [← nativeKL_map_equiv _ _ informationPath2Equiv, study_reverse_tuple, allZero_study_tuple,
    Measure.map_map tripleReverseEquiv.measurable (by fun_prop)]
  have hSame : tripleReverseEquiv ∘ (fun value : ℝ => ((value, value), value)) =
      (fun value => ((value, value), value)) := by funext value; rfl
  rw [hSame, klDiv_self]

/-- Explicitly hypothetical assignments in one shared unmeasured energy unit.
The probability law contains no constitutive energy-per-nat parameter. -/
def hypotheticalEnergyLaw (_energyPerNat : ℝ) : Measure (GridPath 2) :=
  studyProjectedLaw informationGrid

def hypotheticalAssignedExpectedHeat (energyPerNat : ℝ) : ℝ :=
  energyPerNat * (klDiv (studyProjectedLaw informationGrid) (studyReverseLaw informationGrid)).toReal

/-- Identical probability and path-information laws permit unequal assigned
heat under the two frozen unmeasured hypotheses 1 and 2 energy units per nat. -/
theorem constitutive_nonidentification :
    hypotheticalEnergyLaw 1 = hypotheticalEnergyLaw 2 ∧
      klDiv (hypotheticalEnergyLaw 1) (studyReverseLaw informationGrid) =
        klDiv (hypotheticalEnergyLaw 2) (studyReverseLaw informationGrid) ∧
      hypotheticalAssignedExpectedHeat 1 < hypotheticalAssignedExpectedHeat 2 := by
  refine ⟨rfl, rfl, ?_⟩
  rw [hypotheticalAssignedExpectedHeat, hypotheticalAssignedExpectedHeat,
    finite_grid_kl, ENNReal.toReal_ofReal finite_grid_value_pos.le]
  linarith [finite_grid_value_pos]

end FrozenNativeGrid


section NativeControlledCost
open FEP.Fin4GaussianSemigroup FEP.Fin4GaussianSemigroup.Axis

private theorem control_first_native_law (policy : TwoStepPolicy) :
    controlFirstLaw policy =
      transition (allOnesEmbedding (actionCenter policy.first)) controlDuration ∘ₘ controlInitialLaw := by
  have hKernel : selectedNativeTransition id measurable_id (fun _ => policy.first) measurable_const =
      transition (allOnesEmbedding (actionCenter policy.first)) controlDuration := by
    apply DFunLike.ext _ _
    intro state
    rw [selectedNativeTransition_apply]
    rfl
  rw [controlFirstLaw, hKernel, ← Measure.snd_compProd]
  rfl

private theorem control_first_scalar_law (policy : TwoStepPolicy) (noise : ℝ≥0)
    (hNoise : 0 < noise) :
    (controlFirstLaw policy).map allOnesProjection =
      (predictionBelief (firstFilter policy.first noise hNoise) (prior 0)).law := by
  rw [control_first_native_law, full_transition_projection]
  have hInitial : controlInitialLaw.map allOnesProjection = (prior 0).law := by
    change (multivariateGaussian 0 FEP.Fin4GaussianSemigroup.Sigma).map allOnesProjection = _
    rw [gaussianSigma_scalar_marginal, map_zero]
    rfl
  rw [hInitial]
  exact predictionBelief_law_eq_ouTransition (firstFilter policy.first noise hNoise) (prior 0)

private theorem control_history_scalar_joint (policy : TwoStepPolicy) (noise : ℝ≥0)
    (hNoise : 0 < noise) :
    (controlHistoryLaw policy noise hNoise).map (Prod.map allOnesProjection id) =
      informationJoint (firstFilter policy.first noise hNoise) (prior 0) := by
  rw [controlHistoryLaw,
    map_compProd_intertwining _ _
      (observationKernel (firstFilter policy.first noise hNoise)) allOnesProjection id
      allOnesProjection.measurable measurable_id
      (by intro state; rw [Measure.map_id]; rfl), control_first_scalar_law policy noise hNoise]
  rfl

private theorem control_row_scalar_moment (state : StandardizedState) (action : Bool) :
    (∫ next, (allOnesProjection next) ^ 2
      ∂transition (allOnesEmbedding (actionCenter action)) controlDuration state) =
      (1 - controlDecay ^ 2) / 2 +
        (controlDecay * allOnesProjection state + (1 - controlDecay) * actionCenter action) ^ 2 := by
  have h := mode_row_moment external (actionCenter action) state
  simp_rw [raw_external_projection, mul_pow] at h
  rw [integral_const_mul] at h
  norm_num only [rawModeNormSquared, modeRate, modeQuarter_decay_external, ite_true] at h
  nlinarith [h]

private def controlConditionalLoss (policy : TwoStepPolicy) (state observation : ℝ) : ℝ :=
  (1 - controlDecay ^ 2) / 2 +
    (controlDecay * state + (1 - controlDecay) * actionCenter (policy.second observation)) ^ 2

private theorem controlConditionalLoss_history_integrable (policy : TwoStepPolicy)
    (noise : ℝ≥0) (hNoise : 0 < noise) :
    Integrable (fun history : StandardizedState × ℝ =>
      controlConditionalLoss policy (allOnesProjection history.1) history.2)
        (controlHistoryLaw policy noise hNoise) := by
  classical
  have hInput : MemLp (fun history : StandardizedState × ℝ => allOnesProjection history.1) 2
      (controlHistoryLaw policy noise hNoise) := by
    have h := (history_mode_memLp policy noise hNoise external).const_mul (1 / 2 : ℝ)
    apply MemLp.ae_eq _ h
    filter_upwards with history
    rw [raw_external_projection]
    ring
  have hFixed (action : Bool) : Integrable (fun history : StandardizedState × ℝ =>
      (1 - controlDecay ^ 2) / 2 +
        (controlDecay * allOnesProjection history.1 + (1 - controlDecay) * actionCenter action) ^ 2)
        (controlHistoryLaw policy noise hNoise) :=
    (integrable_const _).add ((hInput.const_mul _).add (memLp_const _)).integrable_sq
  have hPiece := Integrable.piecewise
    ((measurableSet_singleton true).preimage (policy.measurable_second.comp measurable_snd)).nullMeasurableSet
    (hFixed true).integrableOn (hFixed false).integrableOn
  apply hPiece.congr
  filter_upwards with history
  cases h : policy.second history.2 <;> simp [Set.piecewise, controlConditionalLoss, h]

private theorem control_terminal_cost_eq_history (policy : TwoStepPolicy) (noise : ℝ≥0)
    (hNoise : 0 < noise) :
    (∫ state, (allOnesProjection state) ^ 2 ∂controlSecondLaw policy noise hNoise) =
      ∫ history : StandardizedState × ℝ,
        controlConditionalLoss policy (allOnesProjection history.1) history.2
        ∂controlHistoryLaw policy noise hNoise := by
  have hInput : MemLp allOnesProjection 2 (controlSecondLaw policy noise hNoise) := by
    have h := (second_mode_memLp policy noise hNoise external).const_mul (1 / 2 : ℝ)
    apply MemLp.ae_eq _ h
    filter_upwards with state
    rw [raw_external_projection]
    ring
  have hJoint : Integrable
      (fun pair : (StandardizedState × ℝ) × StandardizedState => (allOnesProjection pair.2) ^ 2)
      (controlHistoryLaw policy noise hNoise ⊗ₘ
        selectedNativeTransition Prod.fst measurable_fst
          (fun history => policy.second history.2) (policy.measurable_second.comp measurable_snd)) :=
    (integrable_map_measure (by fun_prop) (by fun_prop)).1 hInput.integrable_sq
  rw [controlSecondLaw, integral_map (by fun_prop) (by fun_prop), Measure.integral_compProd hJoint]
  apply integral_congr_ae
  filter_upwards with history
  rw [selectedNativeTransition_apply, control_row_scalar_moment]
  rfl

private theorem posterior_control_loss (policy : TwoStepPolicy) (noise : ℝ≥0)
    (hNoise : 0 < noise) (observation : ℝ) :
    (∫ state, controlConditionalLoss policy state observation
      ∂closedFormPosteriorKernel (firstFilter policy.first noise hNoise) (prior 0) observation) =
        secondRisk policy.first noise hNoise observation (policy.second observation) := by
  change (∫ state, (1 - controlDecay ^ 2) / 2 +
    (controlDecay * state + (1 - controlDecay) * actionCenter (policy.second observation)) ^ 2
      ∂gaussianReal (posteriorMean (firstFilter policy.first noise hNoise) (prior 0) observation)
        (posteriorVariance (firstFilter policy.first noise hNoise) (prior 0))) = _
  rw [integral_add (integrable_const _)
      (gaussian_affine_square_integrable _ _ _ _), integral_const,
    gaussian_affine_square_integral, secondRisk_closedForm,
    (first_posterior policy.first noise hNoise observation).1,
    (first_posterior policy.first noise hNoise observation).2]
  simp
  ring

/-- The primitive policy's attained scalar cost is exactly the squared
all-ones coordinate under the same actual full-state controlled law. Hidden
coordinates are retained in both transitions and the observation history. -/
theorem controlled_native_cost (policy : TwoStepPolicy) (noise : ℝ≥0) (hNoise : 0 < noise) :
    (∫ state, (allOnesProjection state) ^ 2 ∂controlSecondLaw policy noise hNoise) =
      policyRisk noise hNoise policy := by
  rw [control_terminal_cost_eq_history]
  have hMeas : Measurable (fun pair : ℝ × ℝ => controlConditionalLoss policy pair.1 pair.2) := by
    have hAction : Measurable (fun pair : ℝ × ℝ => actionCenter (policy.second pair.2)) := by
      unfold actionCenter
      exact Measurable.ite
        ((measurableSet_singleton true).preimage (policy.measurable_second.comp measurable_snd))
        measurable_const measurable_const
    unfold controlConditionalLoss
    fun_prop
  have hProjection := control_history_scalar_joint policy noise hNoise
  have hScalar : Integrable (fun pair : ℝ × ℝ => controlConditionalLoss policy pair.1 pair.2)
      (informationJoint (firstFilter policy.first noise hNoise) (prior 0)) := by
    rw [← hProjection]
    exact (integrable_map_measure hMeas.aestronglyMeasurable (by fun_prop)).2
      (controlConditionalLoss_history_integrable policy noise hNoise)
  have hMap : (∫ pair : ℝ × ℝ, controlConditionalLoss policy pair.1 pair.2
      ∂informationJoint (firstFilter policy.first noise hNoise) (prior 0)) =
      (∫ history : StandardizedState × ℝ,
        controlConditionalLoss policy (allOnesProjection history.1) history.2
          ∂controlHistoryLaw policy noise hNoise) := by
    rw [← hProjection, integral_map (by fun_prop) hMeas.aestronglyMeasurable]
    rfl
  rw [← hMap]
  have hSwap := closedFormPosterior_compProd_eq_map_swap
    (firstFilter policy.first noise hNoise) (prior 0)
  change evidenceLaw (firstFilter policy.first noise hNoise) (prior 0) ⊗ₘ
    closedFormPosteriorKernel (firstFilter policy.first noise hNoise) (prior 0) =
      (informationJoint (firstFilter policy.first noise hNoise) (prior 0)).map Prod.swap at hSwap
  have hSwapped : Integrable (fun pair : ℝ × ℝ => controlConditionalLoss policy pair.2 pair.1)
      (evidenceLaw (firstFilter policy.first noise hNoise) (prior 0) ⊗ₘ
        closedFormPosteriorKernel (firstFilter policy.first noise hNoise) (prior 0)) := by
    rw [hSwap]
    exact (integrable_map_measure (hMeas.comp measurable_swap).aestronglyMeasurable
      measurable_swap.aemeasurable).2 hScalar
  have hSwappedIntegral := integral_map
    (μ := informationJoint (firstFilter policy.first noise hNoise) (prior 0))
    (φ := Prod.swap) (f := fun pair : ℝ × ℝ => controlConditionalLoss policy pair.2 pair.1)
    measurable_swap.aemeasurable (hMeas.comp measurable_swap).aestronglyMeasurable
  change (∫ pair : ℝ × ℝ, controlConditionalLoss policy pair.2 pair.1
      ∂(informationJoint (firstFilter policy.first noise hNoise) (prior 0)).map Prod.swap) =
    (∫ pair : ℝ × ℝ, controlConditionalLoss policy pair.1 pair.2
      ∂informationJoint (firstFilter policy.first noise hNoise) (prior 0)) at hSwappedIntegral
  rw [← hSwap] at hSwappedIntegral
  have : IsProbabilityMeasure (evidenceLaw (firstFilter policy.first noise hNoise) (prior 0)) := by
    rw [evidenceLaw_eq_gaussian, FEP.GaussianInformationGeometry.FixedVarianceGaussian.law_eq_gaussianReal]
    infer_instance
  rw [← hSwappedIntegral, Measure.integral_compProd hSwapped]
  simp_rw [posterior_control_loss]
  rfl

end NativeControlledCost

section NativeGridMoments
open FEPComposed.GaussianGridPath Finset Matrix

/-- The native projected path coordinates in chronological order. -/
def informationCoordinate (index : Fin 3) : GridPath 2 → ℝ :=
  originalInnovationCoordinate index ∘ informationPath2Equiv

/-- The mean vector is derived below from the native joint law. -/
def informationMean : Fin 3 → ℝ := ![1, controlDecay, controlDecay ^ 2]

/-- Frozen three-time covariance, subsequently bound to native covariance. -/
def informationCovariance : Matrix (Fin 3) (Fin 3) ℝ :=
  !![(1 / 2), controlDecay / 2, controlDecay ^ 2 / 2;
    controlDecay / 2, (1 / 2), controlDecay / 2;
    controlDecay ^ 2 / 2, controlDecay / 2, (1 / 2)]

private def forwardCoordinateCoefficient (index : Fin 3) : Fin 3 → ℝ :=
  ![![1, 0, 0], ![controlDecay, 1, 0], ![controlDecay ^ 2, controlDecay, 1]] index

private theorem forward_coordinate_binding (index : Fin 3) :
    originalInnovationCoordinate index ∘ tripleFromInnovations controlDecay =
      tripleLinear (forwardCoordinateCoefficient index) := by
  funext value
  fin_cases index <;>
    simp [originalInnovationCoordinate, tripleFromInnovations,
      tripleLinear, forwardCoordinateCoefficient, Fin.sum_univ_three]
  all_goals ring

private theorem informationCoordinate_measurable (index : Fin 3) :
    Measurable (informationCoordinate index) := by
  unfold informationCoordinate originalInnovationCoordinate
  fin_cases index <;> fun_prop

private theorem native_forward_coordinate_gaussian (index : Fin 3) :
    HasGaussianLaw (tripleLinear (forwardCoordinateCoefficient index))
      frozenForwardInnovations := by
  have h := (IsGaussian.hasGaussianLaw_id (μ := frozenForwardInnovations)).map_fun
    (tripleLinearCLM (forwardCoordinateCoefficient index))
  simpa only [id_eq, tripleLinearCLM_apply] using h

private theorem native_forward_coordinate_covariance (left right : Fin 3) :
    cov[tripleLinear (forwardCoordinateCoefficient left),
      tripleLinear (forwardCoordinateCoefficient right); frozenForwardInnovations] =
        informationCovariance left right := by
  rw [tripleLinear_covariance]
  fin_cases left <;> fin_cases right <;>
    norm_num [forwardCoordinateCoefficient, informationCovariance]
  all_goals
    have hQ : (frozenPathNoise : ℝ) = (1 - controlDecay ^ 2) / 2 := rfl
    try rw [hQ]
    ring

private theorem native_forward_coordinate_marginal (index : Fin 3) :
    frozenForwardInnovations.map (tripleLinear (forwardCoordinateCoefficient index)) =
      gaussianReal (informationMean index) (1 / 2) := by
  have h := (native_forward_coordinate_gaussian index).map_eq_gaussianReal
  rw [tripleLinear_integral,
    ← covariance_self (native_forward_coordinate_gaussian index).aemeasurable,
    native_forward_coordinate_covariance] at h
  have hDiagonal : informationCovariance index index = (1 / 2 : ℝ) := by
    fin_cases index <;> rfl
  have hVariance : Real.toNNReal (1 / 2 : ℝ) = (1 / 2 : ℝ≥0) := by
    apply NNReal.eq
    rw [Real.coe_toNNReal _ (by norm_num)]
    norm_num
  rw [hDiagonal, hVariance] at h
  fin_cases index <;> simpa [forwardCoordinateCoefficient, informationMean] using h

/-- Actual native one-coordinate Gaussian law; no fitted moment table is supplied. -/
theorem information_native_marginal (index : Fin 3) :
    (studyProjectedLaw informationGrid).map (informationCoordinate index) =
      gaussianReal (informationMean index) (1 / 2) := by
  rw [informationCoordinate, ← Measure.map_map
    (by unfold originalInnovationCoordinate; fin_cases index <;> fun_prop)
    informationPath2Equiv.measurable, nonstationary_native_grid,
    gaussianARTripleLaw_eq_innovations,
    Measure.map_map (by unfold originalInnovationCoordinate; fin_cases index <;> fun_prop)
      (by unfold tripleFromInnovations; fun_prop), forward_coordinate_binding]
  exact native_forward_coordinate_marginal index

/-- The actual chronological native joint has the declared mean vector. -/
theorem information_native_mean (index : Fin 3) :
    (∫ path, informationCoordinate index path ∂studyProjectedLaw informationGrid) =
      informationMean index := by
  have hMap := integral_map
    (μ := studyProjectedLaw informationGrid) (φ := informationCoordinate index)
    (f := fun value : ℝ => value)
    (informationCoordinate_measurable index).aemeasurable (by fun_prop)
  change (∫ value : ℝ, value ∂(studyProjectedLaw informationGrid).map (informationCoordinate index)) =
    (∫ path, informationCoordinate index path ∂studyProjectedLaw informationGrid) at hMap
  rw [← hMap, information_native_marginal, integral_id_gaussianReal]

/-- Every entry of the stated covariance is the covariance under the native full-state path pushforward. -/
theorem information_native_covariance (left right : Fin 3) :
    cov[informationCoordinate left, informationCoordinate right;
      studyProjectedLaw informationGrid] = informationCovariance left right := by
  rw [informationCoordinate, informationCoordinate,
    ← covariance_map_equiv (originalInnovationCoordinate left) (originalInnovationCoordinate right)
      informationPath2Equiv, nonstationary_native_grid, gaussianARTripleLaw_eq_innovations,
    covariance_map (by unfold originalInnovationCoordinate; fin_cases left <;> fun_prop)
      (by unfold originalInnovationCoordinate; fin_cases right <;> fun_prop)
      (by unfold tripleFromInnovations; fun_prop),
    forward_coordinate_binding, forward_coordinate_binding]
  exact native_forward_coordinate_covariance left right

/-- Positive definiteness is proved from independent positive-variance innovations. -/
theorem informationCovariance_posDef : informationCovariance.PosDef := by
  apply Matrix.PosDef.of_dotProduct_mulVec_pos
  · rw [Matrix.isHermitian_iff_isSymm]
    ext left right
    fin_cases left <;> fin_cases right <;> rfl
  · intro vector hNonzero
    have hQuadratic : star vector ⬝ᵥ (informationCovariance *ᵥ vector) =
        (1 / 2 : ℝ) * (vector 0 + controlDecay * vector 1 + controlDecay ^ 2 * vector 2) ^ 2 +
          (frozenPathNoise : ℝ) * (vector 1 + controlDecay * vector 2) ^ 2 +
          (frozenPathNoise : ℝ) * (vector 2) ^ 2 := by
      have hQ : (frozenPathNoise : ℝ) = (1 - controlDecay ^ 2) / 2 := rfl
      rw [hQ]
      simp [informationCovariance, Matrix.mulVec, dotProduct, Fin.sum_univ_three]
      ring
    rw [hQuadratic]
    have hQ : 0 < (frozenPathNoise : ℝ) := frozenPathNoise_pos
    by_cases hTwo : vector 2 = 0
    · by_cases hOne : vector 1 = 0
      · have hZero : vector 0 ≠ 0 := by
          intro hZero
          apply hNonzero
          funext index
          fin_cases index <;> simp [hZero, hOne, hTwo]
        simp only [hOne, hTwo, mul_zero, add_zero, zero_pow (by norm_num : 2 ≠ 0)]
        positivity
      · have hSquare : 0 < (vector 1) ^ 2 := sq_pos_of_ne_zero hOne
        simp only [hTwo, mul_zero, add_zero, zero_pow (by norm_num : 2 ≠ 0)]
        nlinarith [sq_nonneg (vector 0 + controlDecay * vector 1)]
    · have hSquare : 0 < (vector 2) ^ 2 := sq_pos_of_ne_zero hTwo
      nlinarith [sq_nonneg (vector 0 + controlDecay * vector 1 + controlDecay ^ 2 * vector 2),
        sq_nonneg (vector 1 + controlDecay * vector 2)]

def informationInverse : Matrix (Fin 3) (Fin 3) ℝ :=
  (frozenPathNoise : ℝ)⁻¹ •
    !![1, -controlDecay, 0;
      -controlDecay, 1 + controlDecay ^ 2, -controlDecay;
      0, -controlDecay, 1]

private theorem informationInverse_mul : informationInverse * informationCovariance = 1 := by
  ext left right
  fin_cases left <;> fin_cases right <;>
    norm_num [informationInverse, informationCovariance, Matrix.mul_apply, Fin.sum_univ_three]
  all_goals
    have hQ : (frozenPathNoise : ℝ) = (1 - controlDecay ^ 2) / 2 := rfl
    have hNonzero : (frozenPathNoise : ℝ) ≠ 0 := ne_of_gt frozenPathNoise_pos
    field_simp [hNonzero]
    rw [hQ]
    ring

/-- Exact inverse of the native covariance. -/
theorem informationCovariance_inverse : informationCovariance⁻¹ = informationInverse := by
  exact Matrix.inv_eq_left_inv informationInverse_mul

/-- The actual forward mean differs from the coordinate-reversed mean. -/
theorem information_mean_asymmetry : informationMean ≠ fun index => informationMean (2 - index) := by
  intro hEqual
  have h := congr_fun hEqual 0
  norm_num [informationMean] at h
  have hPositive := finite_grid_value_pos
  nlinarith

/-- Native path KL agrees with the covariance Mahalanobis expression. -/
theorem finite_grid_kl_mahalanobis :
    klDiv (studyProjectedLaw informationGrid) (studyReverseLaw informationGrid) =
      ENNReal.ofReal ((1 / 2 : ℝ) *
        ((informationMean - fun index => informationMean (2 - index)) ⬝ᵥ
          (informationCovariance⁻¹ *ᵥ (informationMean - fun index => informationMean (2 - index))))) := by
  rw [finite_grid_kl, informationCovariance_inverse]
  congr 1
  norm_num [informationMean, informationInverse, Matrix.mulVec, dotProduct, Fin.sum_univ_three]
  have hQ : (frozenPathNoise : ℝ) = (1 - controlDecay ^ 2) / 2 := rfl
  have hNonzero : (frozenPathNoise : ℝ) ≠ 0 := ne_of_gt frozenPathNoise_pos
  field_simp [hNonzero]
  rw [hQ]
  ring

/-- Native marginal KL to the fixed stationary scalar law. -/
theorem information_marginal_kl (index : Fin 3) :
    klDiv ((studyProjectedLaw informationGrid).map (informationCoordinate index))
      (gaussianReal 0 (1 / 2)) = ENNReal.ofReal ((informationMean index) ^ 2) := by
  rw [information_native_marginal]
  let fixedHalf : FEP.GaussianInformationGeometry.FixedVarianceGaussian := ⟨1 / 2, by norm_num⟩
  change klDiv (fixedHalf.law (informationMean index)) (fixedHalf.law 0) = _
  rw [fixedHalf.klDiv_law_eq_meanSquare]
  norm_num

/-- Frozen marginal Lyapunov values at 0,1/4,1/2, for the fixed uncontrolled center. -/
theorem information_marginal_kl_values :
    (∀ index : Fin 3, klDiv ((studyProjectedLaw informationGrid).map (informationCoordinate index))
      (gaussianReal 0 (1 / 2)) =
        ENNReal.ofReal (![1, Real.exp (-1), Real.exp (-2)] index)) := by
  intro index
  rw [information_marginal_kl]
  fin_cases index
  · norm_num [informationMean]
  · change ENNReal.ofReal (controlDecay ^ 2) = ENNReal.ofReal (Real.exp (-1))
    rw [controlDecay, ← Real.exp_nat_mul (-(1 / 2 : ℝ)) 2]
    norm_num
  · change ENNReal.ofReal ((controlDecay ^ 2) ^ 2) = ENNReal.ofReal (Real.exp (-2))
    rw [controlDecay, ← Real.exp_nat_mul (-(1 / 2 : ℝ)) 2]
    norm_num
    rw [← Real.exp_nat_mul (-1 : ℝ) 2]
    norm_num

private theorem frozen_reverse_innovation_native_KL :
    klDiv frozenReverseInnovations frozenForwardInnovations =
      ENNReal.ofReal (2 * (1 - controlDecay ^ 2)) := by
  have hSymmetric (variance : ℝ≥0) (hVariance : 0 < variance) (left right : ℝ) :
      klDiv (gaussianReal left variance) (gaussianReal right variance) =
        klDiv (gaussianReal right variance) (gaussianReal left variance) := by
    let model : FEP.GaussianInformationGeometry.FixedVarianceGaussian := ⟨variance, hVariance⟩
    change klDiv (model.law left) (model.law right) = klDiv (model.law right) (model.law left)
    rw [model.klDiv_law_eq_meanSquare, model.klDiv_law_eq_meanSquare]
    congr 1
    ring
  have hSame : klDiv frozenReverseInnovations frozenForwardInnovations =
      klDiv frozenForwardInnovations frozenReverseInnovations := by
    rw [frozenReverseInnovations, frozenForwardInnovations, gaussianARInnovationLaw,
      nativeKL_prod, nativeKL_prod, nativeKL_prod, nativeKL_prod]
    rw [hSymmetric (1 / 2) (by norm_num) (controlDecay ^ 2) 1,
      hSymmetric frozenPathNoise frozenPathNoise_pos (controlDecay * (1 - controlDecay ^ 2)) 0,
      hSymmetric frozenPathNoise frozenPathNoise_pos (1 - controlDecay ^ 2) 0]
  exact hSame.trans frozen_innovation_native_KL

/-- Native reverse divergence is also finite, from the actual inverse coordinate transports. -/
theorem finite_grid_reverse_kl :
    klDiv (studyReverseLaw informationGrid) (studyProjectedLaw informationGrid) =
      ENNReal.ofReal (2 * (1 - controlDecay ^ 2)) := by
  rw [← nativeKL_map_equiv (studyReverseLaw informationGrid)
      (studyProjectedLaw informationGrid) informationPath2Equiv,
    study_reverse_tuple, nonstationary_native_grid]
  have : IsProbabilityMeasure (gaussianARTripleLaw 1 (1 / 2) controlDecay frozenPathNoise) := by
    unfold gaussianARTripleLaw
    infer_instance
  rw [← nativeKL_map_equiv _ _ (tripleInnovationEquiv controlDecay),
    Measure.map_map (tripleInnovationEquiv controlDecay).measurable tripleReverseEquiv.measurable,
    frozen_reverse_innovation_joint, gaussianARTripleLaw_innovation_map]
  exact frozen_reverse_innovation_native_KL

/-- Both native directions have absolute continuity and integrable log ratios; the singular control has neither finite formula nor covariance inverse substituted. -/
theorem finite_grid_mutual_support :
    (studyProjectedLaw informationGrid ≪ studyReverseLaw informationGrid ∧
      Integrable (llr (studyProjectedLaw informationGrid) (studyReverseLaw informationGrid))
        (studyProjectedLaw informationGrid)) ∧
    (studyReverseLaw informationGrid ≪ studyProjectedLaw informationGrid ∧
      Integrable (llr (studyReverseLaw informationGrid) (studyProjectedLaw informationGrid))
        (studyReverseLaw informationGrid)) := by
  refine ⟨finite_grid_support, klDiv_ne_top_iff.mp ?_⟩
  rw [finite_grid_reverse_kl]
  exact ENNReal.ofReal_ne_top

end NativeGridMoments

section NativeLyapunov
open FEP.Fin4GaussianSemigroup FEPComposed.GaussianGridPath

/-- The same full Fin4 law evolved at zero center, with the hidden state retained. -/
def informationFullMarginal (time : ℝ≥0) : Measure StandardizedState :=
  transition 0 time ∘ₘ informationFullInitial

/-- Nonstationary mean relaxation with stationary covariance, derived from native evolution. -/
theorem information_full_marginal_projection (time : ℝ≥0) :
    (informationFullMarginal time).map allOnesProjection =
      gaussianReal (Real.exp (-2 * (time : ℝ))) (1 / 2) := by
  have hCenter : (0 : StandardizedState) = allOnesEmbedding 0 := by simp
  rw [informationFullMarginal, hCenter, full_transition_projection,
    information_full_initial_projection,
    (scalarParameters 0).ouTransition_comp_gaussian]
  apply gaussianReal_ext_iff.mpr
  constructor
  · simp [ScalarOUParameters.transitionMean, ScalarOUParameters.decay,
      scalarParameters, FEP.LinearGaussianSemigroup.LinearGaussianParameters.finOneScalarParameters]
  · apply NNReal.eq
    change (scalarParameters 0).decay time ^ 2 * (1 / 2 : ℝ) +
      ((scalarParameters 0).transitionVariance time : ℝ) = 1 / 2
    rw [ScalarOUParameters.transitionVariance]
    change (scalarParameters 0).decay time ^ 2 * (1 / 2 : ℝ) +
      ((scalarParameters 0).stationaryVariance : ℝ) *
        (1 - (scalarParameters 0).decay time ^ 2) = 1 / 2
    have hVariance : (scalarParameters 0).stationaryVariance = (1 / 2 : ℝ≥0) := by
      apply NNReal.eq
      change (2 : ℝ) / (2 * 2) = 1 / 2
      norm_num
    rw [hVariance]
    norm_num
    ring

/-- Native marginal Lyapunov value for every time in this fixed-center information leg. -/
theorem information_native_lyapunov (time : ℝ≥0) :
    klDiv ((informationFullMarginal time).map allOnesProjection) (gaussianReal 0 (1 / 2)) =
      ENNReal.ofReal (Real.exp (-4 * (time : ℝ))) := by
  rw [information_full_marginal_projection]
  let fixedHalf : FEP.GaussianInformationGeometry.FixedVarianceGaussian := ⟨1 / 2, by norm_num⟩
  change klDiv (fixedHalf.law (Real.exp (-2 * (time : ℝ)))) (fixedHalf.law 0) = _
  rw [fixedHalf.klDiv_law_eq_meanSquare]
  norm_num only [sub_zero, NNReal.coe_div, NNReal.coe_one, NNReal.coe_ofNat]
  rw [div_one, ← Real.exp_nat_mul (-2 * (time : ℝ)) 2]
  congr 2
  ring

/-- Mean and covariance entries are the frozen exponential time formulas. -/
theorem informationMean_time_entries (index : Fin 3) :
    informationMean index = Real.exp (-2 * (informationGrid.time index.val : ℝ)) := by
  fin_cases index
  · norm_num [informationMean, informationGrid]
  · norm_num [informationMean, informationGrid, controlDecay]
  · norm_num [informationMean, informationGrid, controlDecay]
    rw [← Real.exp_nat_mul (-(1 / 2 : ℝ)) 2]
    norm_num

theorem informationCovariance_time_entries (left right : Fin 3) :
    informationCovariance left right = (1 / 2 : ℝ) *
      Real.exp (-2 * |(informationGrid.time left.val : ℝ) - (informationGrid.time right.val : ℝ)|) := by
  fin_cases left <;> fin_cases right <;>
    norm_num [informationCovariance, informationGrid, controlDecay]
  all_goals
    try rw [← Real.exp_nat_mul (-(1 / 2 : ℝ)) 2]
    norm_num
    ring

/-- The frozen retained coordinates agree with the continuous fixed-center Lyapunov values. -/
theorem information_marginal_kl_at_time (index : Fin 3) :
    klDiv ((studyProjectedLaw informationGrid).map (informationCoordinate index))
      (gaussianReal 0 (1 / 2)) =
        ENNReal.ofReal (Real.exp (-4 * (informationGrid.time index.val : ℝ))) := by
  rw [information_marginal_kl_values]
  fin_cases index <;> norm_num [informationGrid]

/-- Pointwise exact selector and its tie rule expressed in the actual posterior mean. -/
theorem optimalSecond_threshold (first : Bool) (noise : ℝ≥0) (hNoise : 0 < noise)
    (observation : ℝ) :
    optimalSecond first noise hNoise observation =
      if 0 ≤ controlPosteriorMean first noise observation then false else true := by
  have hCompare : (secondRisk first noise hNoise observation false ≤
      secondRisk first noise hNoise observation true) ↔
        0 ≤ controlPosteriorMean first noise observation := by
    rw [secondRisk_closedForm, secondRisk_closedForm]
    simp only [actionCenter, Bool.false_eq_true, ↓reduceIte]
    have hCoefficient : 0 < 4 * controlDecay * (1 - controlDecay) := by
      rcases controlDecay_bounds with ⟨hPositive, hLess⟩
      positivity
    constructor <;> intro h
    · nlinarith
    · nlinarith
  simp only [optimalSecond, hCompare]

end NativeLyapunov

section NativeFeedbackSymmetry

private theorem optimalSecond_risk_min (first : Bool) (noise : ℝ≥0) (hNoise : 0 < noise)
    (observation : ℝ) :
    secondRisk first noise hNoise observation (optimalSecond first noise hNoise observation) =
      min (secondRisk first noise hNoise observation false)
        (secondRisk first noise hNoise observation true) := by
  unfold optimalSecond
  split_ifs with hOrder
  · rw [min_eq_left hOrder]
  · rw [min_eq_right (le_of_lt (lt_of_not_ge hOrder))]

private theorem first_evidence_gaussian (first : Bool) (noise : ℝ≥0) (hNoise : 0 < noise) :
    evidenceLaw (firstFilter first noise hNoise) (prior 0) =
      gaussianReal ((1 - controlDecay) * actionCenter first) ((1 / 2 : ℝ≥0) + noise) := by
  rw [evidenceLaw_eq_gaussian, FEP.GaussianInformationGeometry.FixedVarianceGaussian.law_eq_gaussianReal,
    (first_prediction first noise hNoise).1]
  congr 1
  change (predictionBelief (firstFilter first noise hNoise) (prior 0)).family.variance + noise =
    (1 / 2 : ℝ≥0) + noise
  rw [(first_prediction first noise hNoise).2]

private theorem first_evidence_reflection (noise : ℝ≥0) (hNoise : 0 < noise) :
    evidenceLaw (firstFilter false noise hNoise) (prior 0) =
      (evidenceLaw (firstFilter true noise hNoise) (prior 0)).map (fun value => -value) := by
  rw [first_evidence_gaussian, first_evidence_gaussian, gaussianReal_map_neg]
  simp [actionCenter]

private theorem secondRisk_reflection (noise : ℝ≥0) (hNoise : 0 < noise)
    (observation : ℝ) (second : Bool) :
    secondRisk false noise hNoise (-observation) second =
      secondRisk true noise hNoise observation (!second) := by
  have hMean : controlPosteriorMean false noise (-observation) =
      -controlPosteriorMean true noise observation := by
    unfold controlPosteriorMean actionCenter
    simp only [Bool.false_eq_true, ↓reduceIte]
    ring
  rw [secondRisk_closedForm, secondRisk_closedForm, hMean]
  cases second <;> simp [actionCenter] <;> ring

private theorem optimalSecond_risk_reflection (noise : ℝ≥0) (hNoise : 0 < noise)
    (observation : ℝ) :
    secondRisk false noise hNoise (-observation) (optimalSecond false noise hNoise (-observation)) =
      secondRisk true noise hNoise observation (optimalSecond true noise hNoise observation) := by
  rw [optimalSecond_risk_min, optimalSecond_risk_min, secondRisk_reflection, secondRisk_reflection]
  simp only [Bool.not_false, Bool.not_true, min_comm]

/-- The two first-action feedback risks tie under the actual reflected native
observation laws, with the same zero-target loss and positive observation noise. -/
theorem feedback_first_risk_symmetry (noise : ℝ≥0) (hNoise : 0 < noise) :
    policyRisk noise hNoise (feedbackPolicy false noise hNoise) =
      policyRisk noise hNoise (feedbackPolicy true noise hNoise) := by
  have hMeas : Measurable (fun observation =>
      secondRisk false noise hNoise observation (optimalSecond false noise hNoise observation)) := by
    simp_rw [optimalSecond_risk_min]
    exact (measurable_secondRisk false false noise hNoise).min
      (measurable_secondRisk false true noise hNoise)
  change (∫ observation, secondRisk false noise hNoise observation
    (optimalSecond false noise hNoise observation)
      ∂evidenceLaw (firstFilter false noise hNoise) (prior 0)) =
    ∫ observation, secondRisk true noise hNoise observation
      (optimalSecond true noise hNoise observation)
        ∂evidenceLaw (firstFilter true noise hNoise) (prior 0)
  rw [first_evidence_reflection, integral_map (by fun_prop) hMeas.aestronglyMeasurable]
  apply integral_congr_ae
  filter_upwards with observation
  exact optimalSecond_risk_reflection noise hNoise observation

/-- Actual native risk symmetry resolves the frozen first-action tie to false. -/
theorem optimalPolicy_eq_feedback_false (noise : ℝ≥0) (hNoise : 0 < noise) :
    optimalPolicy noise hNoise = feedbackPolicy false noise hNoise := by
  unfold optimalPolicy
  rw [feedback_first_risk_symmetry]
  simp

theorem optimalPolicy_first_false (noise : ℝ≥0) (hNoise : 0 < noise) :
    (optimalPolicy noise hNoise).first = false := by
  rw [optimalPolicy_eq_feedback_false]
  rfl

/-- Direct attainment by the exact false-first feedback policy used by the
frozen synthetic consumer, over every admitted measurable two-step policy. -/
theorem feedback_false_attainment (noise : ℝ≥0) (hNoise : 0 < noise) (policy : TwoStepPolicy) :
    policyRisk noise hNoise (feedbackPolicy false noise hNoise) ≤ policyRisk noise hNoise policy := by
  rw [← optimalPolicy_eq_feedback_false]
  exact policy_attainment noise hNoise policy

end NativeFeedbackSymmetry

end

end FEPComposed.H3CaseStudy
