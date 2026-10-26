module
public import FepSketches.compositions.h3_case_study_model_control
import all FepSketches.compositions.h3_case_study_model_control
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

open FEP.GaussianInformationGeometry FEPComposed.GaussianFilter
open FEPComposed.GaussianControl FEP.ScalarGaussianSemigroup

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



end

end FEPComposed.H3CaseStudy
