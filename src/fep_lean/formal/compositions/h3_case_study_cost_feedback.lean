module
public import FepSketches.compositions.h3_case_study_model_control
import all FepSketches.compositions.h3_case_study_model_control
public import FepSketches.compositions.h3_case_study_path_information
import all FepSketches.compositions.h3_case_study_path_information
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
