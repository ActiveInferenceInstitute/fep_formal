import FepSketches.fin4_gaussian_semigroup
import Mathlib.LinearAlgebra.Matrix.Notation
import Mathlib.Probability.Distributions.Gaussian.HasGaussianLaw.Independence
import Mathlib.Probability.Independence.Conditional

/-!
# H2.5d Gaussian conditioning and precision

This foundation reconstructs the arbitrary-center Fin4 stationary law from
its sensory--active marginal and native product conditional kernel.  It also
provides a fixed bivariate precision witness whose derived Gaussian law has
nonzero coordinate covariance and is therefore not independent.
-/

namespace FEP.GaussianPrecisionConditioning

open FEP.Fin4GaussianSemigroup
open FEP.Fin4GaussianSemigroup.Axis
open MeasureTheory ProbabilityTheory
open scoped ENNReal MeasureTheory NNReal ProbabilityTheory

noncomputable section

/-- Sensory--active coordinates, in that order. -/
abbrev Blanket := ℝ × ℝ

/-- External--internal coordinates, in that order. -/
abbrev Endpoints := ℝ × ℝ

/-- A diagnostic bivariate endpoint carrier, ordered external then internal. -/
abbrev PerturbedEndpoints := EuclideanSpace ℝ (Fin 2)

/-- The sensory--active projection. -/
def blanketCoordinates (state : StandardizedState) : Blanket :=
  (state sensory, state active)

/-- The external--internal projection. -/
def endpointCoordinates (state : StandardizedState) : Endpoints :=
  (state external, state internal)

/-- The blanket-first partition used by native `compProd` reconstruction. -/
def partitionCoordinates (state : StandardizedState) : Blanket × Endpoints :=
  (blanketCoordinates state, endpointCoordinates state)

/-- The actual sensory--active marginal at an arbitrary stationary center. -/
noncomputable def blanketLaw (center : StandardizedState) : Measure Blanket :=
  (stationaryLaw center).map blanketCoordinates

noncomputable instance blanketLaw_isProbabilityMeasure
    (center : StandardizedState) : IsProbabilityMeasure (blanketLaw center) := by
  unfold blanketLaw
  exact (Measure.isProbabilityMeasure_map_iff
    (by
      unfold blanketCoordinates
      fun_prop : Measurable blanketCoordinates).aemeasurable).mpr (by infer_instance)

/-- The blanket-dependent displacement from either endpoint center. -/
def conditionalOffset (center : StandardizedState) (blanket : Blanket) : ℝ :=
  ((blanket.1 - center sensory) + (blanket.2 - center active)) / 4

/-- Conditional external mean; its endpoint center is retained. -/
def externalConditionalMean (center : StandardizedState) (blanket : Blanket) : ℝ :=
  center external + conditionalOffset center blanket

/-- Conditional internal mean; its endpoint center is retained. -/
def internalConditionalMean (center : StandardizedState) (blanket : Blanket) : ℝ :=
  center internal + conditionalOffset center blanket

/-- Native scalar Gaussian row for the external coordinate. -/
noncomputable def externalConditionalKernel
    (center : StandardizedState) : Kernel Blanket ℝ where
  toFun blanket := gaussianReal (externalConditionalMean center blanket) (1 / 4)
  measurable' := by
    change Measurable
      (Function.uncurry gaussianReal ∘
        fun blanket : Blanket =>
          (externalConditionalMean center blanket, (1 / 4 : ℝ≥0)))
    exact measurable_gaussianReal.comp
      ((by
        unfold externalConditionalMean conditionalOffset
        fun_prop : Measurable (externalConditionalMean center)).prodMk
          measurable_const)

noncomputable instance externalConditionalKernel_isMarkovKernel
    (center : StandardizedState) :
    IsMarkovKernel (externalConditionalKernel center) :=
  ⟨fun blanket => by
    change IsProbabilityMeasure
      (gaussianReal (externalConditionalMean center blanket) (1 / 4))
    infer_instance⟩

/-- Native scalar Gaussian row for the internal coordinate. -/
noncomputable def internalConditionalKernel
    (center : StandardizedState) : Kernel Blanket ℝ where
  toFun blanket := gaussianReal (internalConditionalMean center blanket) (1 / 4)
  measurable' := by
    change Measurable
      (Function.uncurry gaussianReal ∘
        fun blanket : Blanket =>
          (internalConditionalMean center blanket, (1 / 4 : ℝ≥0)))
    exact measurable_gaussianReal.comp
      ((by
        unfold internalConditionalMean conditionalOffset
        fun_prop : Measurable (internalConditionalMean center)).prodMk
          measurable_const)

noncomputable instance internalConditionalKernel_isMarkovKernel
    (center : StandardizedState) :
    IsMarkovKernel (internalConditionalKernel center) :=
  ⟨fun blanket => by
    change IsProbabilityMeasure
      (gaussianReal (internalConditionalMean center blanket) (1 / 4))
    infer_instance⟩

/-- Product of the two native scalar endpoint rows. -/
noncomputable def endpointConditionalKernel
    (center : StandardizedState) : Kernel Blanket Endpoints :=
  externalConditionalKernel center ×ₖ internalConditionalKernel center

noncomputable instance endpointConditionalKernel_isMarkovKernel
    (center : StandardizedState) :
    IsMarkovKernel (endpointConditionalKernel center) := by
  unfold endpointConditionalKernel
  infer_instance

/-- External coordinate of the fixed bivariate diagnostic law. -/
def perturbedExternal (state : PerturbedEndpoints) : ℝ :=
  state 0

/-- Internal coordinate of the fixed bivariate diagnostic law. -/
def perturbedInternal (state : PerturbedEndpoints) : ℝ :=
  state 1

/-- Raw precision of the fixed bivariate diagnostic law. -/
def perturbedEndpointPrecision : Matrix (Fin 2) (Fin 2) ℝ :=
  !![4, 1; 1, 4]

/-- Covariance derived definitionally as the inverse precision. -/
noncomputable def perturbedEndpointCovariance : Matrix (Fin 2) (Fin 2) ℝ :=
  perturbedEndpointPrecision⁻¹

private theorem perturbedEndpointPrecision_posDef_private :
    perturbedEndpointPrecision.PosDef := by
  have hEntries :
      perturbedEndpointPrecision =
        (3 : ℝ) • (1 : Matrix (Fin 2) (Fin 2) ℝ) +
          Matrix.vecMulVec (fun _ : Fin 2 => (1 : ℝ))
            (fun _ : Fin 2 => (1 : ℝ)) := by
    ext row column
    fin_cases row <;> fin_cases column <;>
      norm_num [perturbedEndpointPrecision, Matrix.one_apply, Matrix.vecMulVec]
  rw [hEntries]
  exact (Matrix.PosDef.one.smul (by norm_num)).add_posSemidef
    (by
      simpa using Matrix.posSemidef_vecMulVec_self_star
        (fun _ : Fin 2 => (1 : ℝ)))

private theorem perturbedEndpointCovariance_posDef_private :
    perturbedEndpointCovariance.PosDef := by
  rw [perturbedEndpointCovariance]
  exact perturbedEndpointPrecision_posDef_private.inv

/-- Centered native Gaussian using the covariance derived from the precision. -/
noncomputable def perturbedEndpointLaw : Measure PerturbedEndpoints :=
  multivariateGaussian 0 perturbedEndpointCovariance

noncomputable instance perturbedEndpointLaw_isProbabilityMeasure :
    IsProbabilityMeasure perturbedEndpointLaw := by
  unfold perturbedEndpointLaw
  infer_instance

private noncomputable instance perturbedEndpointLaw_isGaussian_private :
    IsGaussian perturbedEndpointLaw := by
  unfold perturbedEndpointLaw
  infer_instance

theorem measurable_blanketCoordinates : Measurable blanketCoordinates := by
  unfold blanketCoordinates
  fun_prop

theorem measurable_endpointCoordinates : Measurable endpointCoordinates := by
  unfold endpointCoordinates
  fun_prop

theorem measurable_partitionCoordinates : Measurable partitionCoordinates := by
  unfold partitionCoordinates
  exact measurable_blanketCoordinates.prodMk measurable_endpointCoordinates

theorem externalConditionalKernel_apply
    (center : StandardizedState) (blanket : Blanket) :
    externalConditionalKernel center blanket =
      gaussianReal (externalConditionalMean center blanket) (1 / 4) :=
  rfl

theorem internalConditionalKernel_apply
    (center : StandardizedState) (blanket : Blanket) :
    internalConditionalKernel center blanket =
      gaussianReal (internalConditionalMean center blanket) (1 / 4) :=
  rfl

theorem endpointConditionalKernel_apply
    (center : StandardizedState) (blanket : Blanket) :
    endpointConditionalKernel center blanket =
      (gaussianReal (externalConditionalMean center blanket) (1 / 4)).prod
        (gaussianReal (internalConditionalMean center blanket) (1 / 4)) := by
  rw [endpointConditionalKernel, Kernel.prod_apply,
    externalConditionalKernel_apply, internalConditionalKernel_apply]

theorem externalConditionalKernel_mean
    (center : StandardizedState) (blanket : Blanket) :
    ∫ value, value ∂externalConditionalKernel center blanket =
      externalConditionalMean center blanket := by
  rw [externalConditionalKernel_apply, integral_id_gaussianReal]

theorem externalConditionalKernel_variance
    (center : StandardizedState) (blanket : Blanket) :
    Var[id; externalConditionalKernel center blanket] = 1 / 4 := by
  rw [externalConditionalKernel_apply, variance_id_gaussianReal]
  norm_num

theorem internalConditionalKernel_mean
    (center : StandardizedState) (blanket : Blanket) :
    ∫ value, value ∂internalConditionalKernel center blanket =
      internalConditionalMean center blanket := by
  rw [internalConditionalKernel_apply, integral_id_gaussianReal]

theorem internalConditionalKernel_variance
    (center : StandardizedState) (blanket : Blanket) :
    Var[id; internalConditionalKernel center blanket] = 1 / 4 := by
  rw [internalConditionalKernel_apply, variance_id_gaussianReal]
  norm_num

private noncomputable instance stationaryLaw_isGaussian_private
    (center : StandardizedState) : IsGaussian (stationaryLaw center) := by
  rw [stationaryLaw_eq_gaussian center]
  infer_instance

private theorem centeredState_hasGaussianLaw (center : StandardizedState) :
    HasGaussianLaw (fun state : StandardizedState => state - center)
      (stationaryLaw center) :=
  ⟨by fun_prop, by infer_instance⟩

private def centeredCoordinate
    (center : StandardizedState) (axis : Axis) (state : StandardizedState) : ℝ :=
  state axis - center axis

private noncomputable def coordinateCLM
    (axis : Axis) : StandardizedState →L[ℝ] ℝ :=
  EuclideanSpace.proj axis

private theorem coordinateCLM_apply (axis : Axis) (state : StandardizedState) :
    coordinateCLM axis state = state axis := by
  rfl

private noncomputable def offsetCLM : StandardizedState →L[ℝ] ℝ :=
  (1 / 4 : ℝ) • (coordinateCLM sensory + coordinateCLM active)

private noncomputable def externalResidualCLM : StandardizedState →L[ℝ] ℝ :=
  coordinateCLM external - offsetCLM

private noncomputable def internalResidualCLM : StandardizedState →L[ℝ] ℝ :=
  coordinateCLM internal - offsetCLM

private noncomputable def blanketDeviationCLM : StandardizedState →L[ℝ] Blanket :=
  (coordinateCLM sensory).prod (coordinateCLM active)

private noncomputable def residualCLM : StandardizedState →L[ℝ] Endpoints :=
  externalResidualCLM.prod internalResidualCLM

private def externalResidual
    (center : StandardizedState) (state : StandardizedState) : ℝ :=
  state external - externalConditionalMean center (blanketCoordinates state)

private def internalResidual
    (center : StandardizedState) (state : StandardizedState) : ℝ :=
  state internal - internalConditionalMean center (blanketCoordinates state)

private def endpointResidual
    (center : StandardizedState) (state : StandardizedState) : Endpoints :=
  (externalResidual center state, internalResidual center state)

private def blanketDeviation
    (center : StandardizedState) (state : StandardizedState) : Blanket :=
  (centeredCoordinate center sensory state,
    centeredCoordinate center active state)

private theorem measurable_externalResidual (center : StandardizedState) :
    Measurable (externalResidual center) := by
  unfold externalResidual externalConditionalMean conditionalOffset blanketCoordinates
  fun_prop

private theorem measurable_internalResidual (center : StandardizedState) :
    Measurable (internalResidual center) := by
  unfold internalResidual internalConditionalMean conditionalOffset blanketCoordinates
  fun_prop

private theorem measurable_endpointResidual (center : StandardizedState) :
    Measurable (endpointResidual center) := by
  unfold endpointResidual
  exact (measurable_externalResidual center).prodMk
    (measurable_internalResidual center)

private theorem measurable_blanketDeviation (center : StandardizedState) :
    Measurable (blanketDeviation center) := by
  unfold blanketDeviation centeredCoordinate
  fun_prop

private theorem blanketDeviationCLM_apply
    (center state : StandardizedState) :
    blanketDeviationCLM (state - center) = blanketDeviation center state := by
  rfl

private theorem externalResidualCLM_apply
    (center state : StandardizedState) :
    externalResidualCLM (state - center) = externalResidual center state := by
  simp [externalResidualCLM, offsetCLM, coordinateCLM, externalResidual,
    externalConditionalMean, conditionalOffset, blanketCoordinates]
  ring

private theorem internalResidualCLM_apply
    (center state : StandardizedState) :
    internalResidualCLM (state - center) = internalResidual center state := by
  simp [internalResidualCLM, offsetCLM, coordinateCLM, internalResidual,
    internalConditionalMean, conditionalOffset, blanketCoordinates]
  ring

private theorem residualCLM_apply (center state : StandardizedState) :
    residualCLM (state - center) = endpointResidual center state := by
  simp [residualCLM, endpointResidual, externalResidualCLM_apply,
    internalResidualCLM_apply]

private theorem coordinate_memLp (center : StandardizedState) (axis : Axis) :
    MemLp (fun state : StandardizedState => state axis) 2
      (stationaryLaw center) := by
  simpa [coordinateCLM, Function.comp_def] using
    ((IsGaussian.hasGaussianLaw_id (μ := stationaryLaw center)).map
      (coordinateCLM axis)).memLp_two

private theorem centeredCoordinate_memLp
    (center : StandardizedState) (axis : Axis) :
    MemLp (centeredCoordinate center axis) 2 (stationaryLaw center) := by
  change MemLp (fun state : StandardizedState => state axis - center axis) 2
    (stationaryLaw center)
  simpa [centeredCoordinate, coordinateCLM, Function.comp_def] using
    ((centeredState_hasGaussianLaw center).map (coordinateCLM axis)).memLp_two

private theorem covariance_coordinate
    (center : StandardizedState) (left right : Axis) :
    cov[fun state : StandardizedState => state left,
      fun state => state right; stationaryLaw center] = Sigma left right := by
  rw [stationaryLaw_eq_gaussian center]
  exact covariance_eval_multivariateGaussian Sigma_posDef.posSemidef left right

private theorem covariance_centeredCoordinate
    (center : StandardizedState) (left right : Axis) :
    cov[centeredCoordinate center left, centeredCoordinate center right;
      stationaryLaw center] = Sigma left right := by
  rw [show centeredCoordinate center left =
      fun state : StandardizedState => state left - center left by rfl,
    show centeredCoordinate center right =
      fun state : StandardizedState => state right - center right by rfl,
    covariance_sub_const_left
      ((coordinate_memLp center left).integrable (by norm_num)),
    covariance_sub_const_right
      ((coordinate_memLp center right).integrable (by norm_num)),
    covariance_coordinate]

private def centeredOffset
    (center : StandardizedState) (state : StandardizedState) : ℝ :=
  conditionalOffset center (blanketCoordinates state)

private theorem centeredOffset_eq
    (center : StandardizedState) :
    centeredOffset center = fun state : StandardizedState =>
      (centeredCoordinate center sensory state +
        centeredCoordinate center active state) / 4 := by
  funext state
  rfl

private theorem centeredOffset_memLp (center : StandardizedState) :
    MemLp (centeredOffset center) 2 (stationaryLaw center) := by
  rw [centeredOffset_eq]
  have hSensory := centeredCoordinate_memLp center sensory
  have hActive := centeredCoordinate_memLp center active
  simpa [div_eq_mul_inv, mul_comm] using
    (hSensory.add hActive).const_mul (4 : ℝ)⁻¹

private theorem covariance_centeredCoordinate_offset
    (center : StandardizedState) (axis : Axis) :
    cov[centeredCoordinate center axis, centeredOffset center;
      stationaryLaw center] =
        (Sigma axis sensory + Sigma axis active) / 4 := by
  rw [centeredOffset_eq, covariance_fun_div_right]
  change
    cov[centeredCoordinate center axis,
      (centeredCoordinate center sensory) +
        (centeredCoordinate center active); stationaryLaw center] / 4 = _
  rw [covariance_add_right]
  · rw [covariance_centeredCoordinate, covariance_centeredCoordinate]
  · exact centeredCoordinate_memLp center axis
  · exact centeredCoordinate_memLp center sensory
  · exact centeredCoordinate_memLp center active

private theorem covariance_offset_centeredCoordinate
    (center : StandardizedState) (axis : Axis) :
    cov[centeredOffset center, centeredCoordinate center axis;
      stationaryLaw center] =
        (Sigma sensory axis + Sigma active axis) / 4 := by
  rw [covariance_comm, covariance_centeredCoordinate_offset, Sigma_eq_entries]
  cases axis <;> norm_num

private theorem covariance_offset_self (center : StandardizedState) :
    cov[centeredOffset center, centeredOffset center; stationaryLaw center] =
      1 / 24 := by
  rw [centeredOffset_eq, covariance_fun_div_left, covariance_fun_div_right]
  change
    cov[(centeredCoordinate center sensory) +
        (centeredCoordinate center active),
      (centeredCoordinate center sensory) +
        (centeredCoordinate center active); stationaryLaw center] / 4 / 4 = _
  rw [covariance_add_left, covariance_add_right, covariance_add_right]
  all_goals try exact
    ((centeredCoordinate_memLp center sensory).add
      (centeredCoordinate_memLp center active))
  all_goals try exact centeredCoordinate_memLp center sensory
  all_goals try exact centeredCoordinate_memLp center active
  rw [covariance_centeredCoordinate, covariance_centeredCoordinate,
    covariance_centeredCoordinate, covariance_centeredCoordinate,
    Sigma_eq_entries]
  norm_num

private def blanketAxis : Bool → Axis
  | false => sensory
  | true => active

private def residualAxis : Bool → Axis
  | false => external
  | true => internal

private def blanketComponent
    (center : StandardizedState) (index : Bool) (state : StandardizedState) : ℝ :=
  centeredCoordinate center (blanketAxis index) state

private def residualComponent
    (center : StandardizedState) (index : Bool) (state : StandardizedState) : ℝ :=
  centeredCoordinate center (residualAxis index) state - centeredOffset center state

private theorem residualComponent_false
    (center : StandardizedState) (state : StandardizedState) :
    residualComponent center false state = externalResidual center state := by
  simp [residualComponent, residualAxis, centeredCoordinate, centeredOffset,
    externalResidual, externalConditionalMean]
  ring

private theorem residualComponent_true
    (center : StandardizedState) (state : StandardizedState) :
    residualComponent center true state = internalResidual center state := by
  simp [residualComponent, residualAxis, centeredCoordinate, centeredOffset,
    internalResidual, internalConditionalMean]
  ring

private theorem blanket_residual_covariance_zero
    (center : StandardizedState) (blanketIndex residualIndex : Bool) :
    cov[blanketComponent center blanketIndex,
      residualComponent center residualIndex; stationaryLaw center] = 0 := by
  rw [show residualComponent center residualIndex =
      fun state : StandardizedState =>
        centeredCoordinate center (residualAxis residualIndex) state -
          centeredOffset center state by rfl,
    covariance_fun_sub_right]
  · change
      cov[centeredCoordinate center (blanketAxis blanketIndex),
        centeredCoordinate center (residualAxis residualIndex);
          stationaryLaw center] -
        cov[centeredCoordinate center (blanketAxis blanketIndex),
          centeredOffset center; stationaryLaw center] = 0
    rw [covariance_centeredCoordinate, covariance_centeredCoordinate_offset,
      Sigma_eq_entries]
    cases blanketIndex <;> cases residualIndex <;>
      norm_num [blanketAxis, residualAxis]
  · exact centeredCoordinate_memLp center (blanketAxis blanketIndex)
  · exact centeredCoordinate_memLp center (residualAxis residualIndex)
  · exact centeredOffset_memLp center

private theorem external_internal_residual_covariance_zero
    (center : StandardizedState) :
    cov[externalResidual center, internalResidual center;
      stationaryLaw center] = 0 := by
  rw [show externalResidual center = fun state : StandardizedState =>
      centeredCoordinate center external state - centeredOffset center state by
        funext state
        simp [externalResidual, externalConditionalMean, centeredCoordinate,
          centeredOffset]
        ring,
    show internalResidual center = fun state : StandardizedState =>
      centeredCoordinate center internal state - centeredOffset center state by
        funext state
        simp [internalResidual, internalConditionalMean, centeredCoordinate,
          centeredOffset]
        ring,
    covariance_fun_sub_fun_sub]
  · rw [covariance_centeredCoordinate, covariance_centeredCoordinate_offset,
      covariance_offset_centeredCoordinate, covariance_offset_self,
      Sigma_eq_entries]
    norm_num
  · exact centeredCoordinate_memLp center external
  · exact centeredOffset_memLp center
  · exact centeredCoordinate_memLp center internal
  · exact centeredOffset_memLp center

private theorem centeredState_mean (center : StandardizedState) :
    ∫ state, state - center ∂stationaryLaw center = 0 := by
  rw [stationaryLaw_eq_gaussian center]
  rw [integral_sub]
  · simp
  · exact IsGaussian.integrable_id
  · fun_prop

private theorem externalResidual_mean (center : StandardizedState) :
    ∫ state, externalResidual center state ∂stationaryLaw center = 0 := by
  simp_rw [← externalResidualCLM_apply center]
  rw [externalResidualCLM.integral_comp_comm
      (centeredState_hasGaussianLaw center).integrable,
    centeredState_mean]
  simp

private theorem internalResidual_mean (center : StandardizedState) :
    ∫ state, internalResidual center state ∂stationaryLaw center = 0 := by
  simp_rw [← internalResidualCLM_apply center]
  rw [internalResidualCLM.integral_comp_comm
      (centeredState_hasGaussianLaw center).integrable,
    centeredState_mean]
  simp

private theorem externalResidual_variance (center : StandardizedState) :
    Var[externalResidual center; stationaryLaw center] = 1 / 4 := by
  rw [← covariance_self (measurable_externalResidual center).aemeasurable,
    show externalResidual center = fun state : StandardizedState =>
      centeredCoordinate center external state - centeredOffset center state by
        funext state
        simp [externalResidual, externalConditionalMean, centeredCoordinate,
          centeredOffset]
        ring,
    covariance_fun_sub_fun_sub]
  · rw [covariance_centeredCoordinate, covariance_centeredCoordinate_offset,
      covariance_offset_centeredCoordinate, covariance_offset_self,
      Sigma_eq_entries]
    norm_num
  · exact centeredCoordinate_memLp center external
  · exact centeredOffset_memLp center
  · exact centeredCoordinate_memLp center external
  · exact centeredOffset_memLp center

private theorem internalResidual_variance (center : StandardizedState) :
    Var[internalResidual center; stationaryLaw center] = 1 / 4 := by
  rw [← covariance_self (measurable_internalResidual center).aemeasurable,
    show internalResidual center = fun state : StandardizedState =>
      centeredCoordinate center internal state - centeredOffset center state by
        funext state
        simp [internalResidual, internalConditionalMean, centeredCoordinate,
          centeredOffset]
        ring,
    covariance_fun_sub_fun_sub]
  · rw [covariance_centeredCoordinate, covariance_centeredCoordinate_offset,
      covariance_offset_centeredCoordinate, covariance_offset_self,
      Sigma_eq_entries]
    norm_num
  · exact centeredCoordinate_memLp center internal
  · exact centeredOffset_memLp center
  · exact centeredCoordinate_memLp center internal
  · exact centeredOffset_memLp center

private theorem hasGaussianLaw_blanketDeviation_residual
    (center : StandardizedState) :
    HasGaussianLaw
      (fun state : StandardizedState =>
        (blanketDeviation center state, endpointResidual center state))
      (stationaryLaw center) := by
  have h := (centeredState_hasGaussianLaw center).map
    (blanketDeviationCLM.prod residualCLM)
  refine h.congr ?_
  filter_upwards with state
  simp only [Function.comp_apply, ContinuousLinearMap.prod_apply,
    blanketDeviationCLM_apply, residualCLM_apply]

private theorem blanketDeviation_indep_endpointResidual
    (center : StandardizedState) :
    IndepFun (blanketDeviation center) (endpointResidual center)
      (stationaryLaw center) := by
  let blanketFamily : Bool → StandardizedState → ℝ :=
    blanketComponent center
  let residualFamily : Bool → StandardizedState → ℝ :=
    residualComponent center
  let blanketFamilyCLM : StandardizedState →L[ℝ] (Bool → ℝ) :=
    ContinuousLinearMap.pi fun
      | false => coordinateCLM sensory
      | true => coordinateCLM active
  let residualFamilyCLM : StandardizedState →L[ℝ] (Bool → ℝ) :=
    ContinuousLinearMap.pi fun
      | false => externalResidualCLM
      | true => internalResidualCLM
  have hGaussian : HasGaussianLaw
      (fun state : StandardizedState =>
        (fun index => blanketFamily index state,
          fun index => residualFamily index state)) (stationaryLaw center) := by
    have h := (centeredState_hasGaussianLaw center).map
      (blanketFamilyCLM.prod residualFamilyCLM)
    refine h.congr ?_
    filter_upwards with state
    apply Prod.ext
    · funext index
      cases index <;>
        simp [Function.comp_apply, ContinuousLinearMap.prod_apply,
          blanketFamilyCLM, blanketFamily, blanketComponent, blanketAxis,
          centeredCoordinate, coordinateCLM]
    · funext index
      cases index
      · simpa only [Function.comp_apply, ContinuousLinearMap.prod_apply,
          ContinuousLinearMap.pi_apply, residualFamilyCLM, residualFamily,
          residualComponent_false] using externalResidualCLM_apply center state
      · simpa only [Function.comp_apply, ContinuousLinearMap.prod_apply,
          ContinuousLinearMap.pi_apply, residualFamilyCLM, residualFamily,
          residualComponent_true] using internalResidualCLM_apply center state
  have hFamilies := hGaussian.indepFun_of_covariance_eval
    (fun i j => by
      have hCov := blanket_residual_covariance_zero center i j
      simpa only [blanketFamily, residualFamily] using hCov)
  have hPairs := hFamilies.comp
    (φ := fun values : Bool → ℝ => (values false, values true))
    (ψ := fun values : Bool → ℝ => (values false, values true))
    (by fun_prop) (by fun_prop)
  refine hPairs.congr ?_ ?_
  · filter_upwards with state
    rfl
  · filter_upwards with state
    simp [residualFamily, endpointResidual,
      residualComponent_false, residualComponent_true]

private theorem blanket_indep_endpointResidual
    (center : StandardizedState) :
    IndepFun blanketCoordinates (endpointResidual center) (stationaryLaw center) := by
  have h := (blanketDeviation_indep_endpointResidual center).comp
    (φ := fun blanket : Blanket =>
      (blanket.1 + center sensory, blanket.2 + center active))
    (ψ := id) (by fun_prop) measurable_id
  refine h.congr ?_ ?_
  · filter_upwards with state
    simp [blanketDeviation, blanketCoordinates, centeredCoordinate]
  · filter_upwards with state
    rfl

private theorem externalResidual_indep_internalResidual
    (center : StandardizedState) :
    IndepFun (externalResidual center) (internalResidual center)
      (stationaryLaw center) := by
  exact (hasGaussianLaw_blanketDeviation_residual center).snd
    |>.indepFun_of_covariance_eq_zero
      (external_internal_residual_covariance_zero center)

private theorem externalResidual_map (center : StandardizedState) :
    (stationaryLaw center).map (externalResidual center) =
      gaussianReal 0 (1 / 4) := by
  have h := (hasGaussianLaw_blanketDeviation_residual center).snd.fst
    |>.map_eq_gaussianReal
  rw [externalResidual_mean, externalResidual_variance] at h
  have hVariance : (1 / 4 : ℝ).toNNReal = (1 / 4 : ℝ≥0) := by
    apply NNReal.eq
    norm_num [Real.coe_toNNReal]
  simpa only [hVariance] using h

private theorem internalResidual_map (center : StandardizedState) :
    (stationaryLaw center).map (internalResidual center) =
      gaussianReal 0 (1 / 4) := by
  have h := (hasGaussianLaw_blanketDeviation_residual center).snd.snd
    |>.map_eq_gaussianReal
  rw [internalResidual_mean, internalResidual_variance] at h
  have hVariance : (1 / 4 : ℝ).toNNReal = (1 / 4 : ℝ≥0) := by
    apply NNReal.eq
    norm_num [Real.coe_toNNReal]
  simpa only [hVariance] using h

private theorem endpointResidual_map (center : StandardizedState) :
    (stationaryLaw center).map (endpointResidual center) =
      (gaussianReal 0 (1 / 4)).prod (gaussianReal 0 (1 / 4)) := by
  rw [show endpointResidual center = fun state =>
      (externalResidual center state, internalResidual center state) by rfl,
    (externalResidual_indep_internalResidual center).map_prod_eq_prod_map_map
      (measurable_externalResidual center).aemeasurable
      (measurable_internalResidual center).aemeasurable,
    externalResidual_map, internalResidual_map]

private theorem blanket_endpointResidual_map (center : StandardizedState) :
    (stationaryLaw center).map
        (fun state => (blanketCoordinates state, endpointResidual center state)) =
      (blanketLaw center).prod
        ((gaussianReal 0 (1 / 4)).prod (gaussianReal 0 (1 / 4))) := by
  rw [(blanket_indep_endpointResidual center).map_prod_eq_prod_map_map
      measurable_blanketCoordinates.aemeasurable
      (measurable_endpointResidual center).aemeasurable,
    endpointResidual_map]
  rfl

private def shiftEndpoints
    (center : StandardizedState) (blanket : Blanket)
    (residual : Endpoints) : Endpoints :=
  (residual.1 + externalConditionalMean center blanket,
    residual.2 + internalConditionalMean center blanket)

private def shiftPartition
    (center : StandardizedState) (value : Blanket × Endpoints) :
    Blanket × Endpoints :=
  (value.1, shiftEndpoints center value.1 value.2)

private theorem measurable_shiftEndpoints
    (center : StandardizedState) (blanket : Blanket) :
    Measurable (shiftEndpoints center blanket) := by
  unfold shiftEndpoints externalConditionalMean internalConditionalMean
    conditionalOffset
  fun_prop

private theorem measurable_shiftPartition (center : StandardizedState) :
    Measurable (shiftPartition center) := by
  unfold shiftPartition shiftEndpoints externalConditionalMean
    internalConditionalMean conditionalOffset
  fun_prop

private theorem endpointConditionalKernel_eq_shift
    (center : StandardizedState) (blanket : Blanket) :
    endpointConditionalKernel center blanket =
      ((gaussianReal 0 (1 / 4)).prod (gaussianReal 0 (1 / 4))).map
        (shiftEndpoints center blanket) := by
  rw [endpointConditionalKernel_apply]
  symm
  calc
    ((gaussianReal 0 (1 / 4)).prod (gaussianReal 0 (1 / 4))).map
        (shiftEndpoints center blanket) =
      ((gaussianReal 0 (1 / 4)).prod (gaussianReal 0 (1 / 4))).map
        (Prod.map
          (fun value => value + externalConditionalMean center blanket)
          (fun value => value + internalConditionalMean center blanket)) := by
            congr 1
    _ = ((gaussianReal 0 (1 / 4)).map
          (fun value => value + externalConditionalMean center blanket)).prod
        ((gaussianReal 0 (1 / 4)).map
          (fun value => value + internalConditionalMean center blanket)) :=
      (Measure.map_prod_map (gaussianReal 0 (1 / 4))
        (gaussianReal 0 (1 / 4)) (by fun_prop) (by fun_prop)).symm
    _ = _ := by
      rw [gaussianReal_map_add_const, gaussianReal_map_add_const]
      simp

private theorem compProd_endpointConditionalKernel_eq_shifted_product
    (center : StandardizedState) :
    blanketLaw center ⊗ₘ endpointConditionalKernel center =
      ((blanketLaw center).prod
        ((gaussianReal 0 (1 / 4)).prod (gaussianReal 0 (1 / 4)))).map
          (shiftPartition center) := by
  ext set hset
  rw [Measure.compProd_apply hset,
    Measure.map_apply (measurable_shiftPartition center) hset,
    Measure.prod_apply ((measurable_shiftPartition center) hset)]
  apply lintegral_congr
  intro blanket
  rw [endpointConditionalKernel_eq_shift,
    Measure.map_apply (measurable_shiftEndpoints center blanket)
      (measurable_prodMk_left hset)]
  rfl

theorem stationaryPartition_eq_compProd (center : StandardizedState) :
    (stationaryLaw center).map partitionCoordinates =
      blanketLaw center ⊗ₘ endpointConditionalKernel center := by
  calc
    (stationaryLaw center).map partitionCoordinates =
        (stationaryLaw center).map
          (fun state => shiftPartition center
            (blanketCoordinates state, endpointResidual center state)) := by
      apply Measure.map_congr
      filter_upwards with state
      simp [partitionCoordinates, shiftPartition, shiftEndpoints, endpointResidual,
        endpointCoordinates, externalResidual, internalResidual]
    _ = (stationaryLaw center).map
          (shiftPartition center ∘
            fun state => (blanketCoordinates state, endpointResidual center state)) := by
      apply Measure.map_congr
      filter_upwards with state
      rfl
    _ = ((stationaryLaw center).map
          (fun state => (blanketCoordinates state,
            endpointResidual center state))).map (shiftPartition center) :=
      (Measure.map_map (measurable_shiftPartition center)
        (measurable_blanketCoordinates.prodMk
          (measurable_endpointResidual center))).symm
    _ = ((blanketLaw center).prod
          ((gaussianReal 0 (1 / 4)).prod (gaussianReal 0 (1 / 4)))).map
            (shiftPartition center) := by
      rw [blanket_endpointResidual_map]
    _ = blanketLaw center ⊗ₘ endpointConditionalKernel center :=
      (compProd_endpointConditionalKernel_eq_shifted_product center).symm

theorem endpointCondDistrib_ae_eq_product (center : StandardizedState) :
    condDistrib endpointCoordinates blanketCoordinates (stationaryLaw center)
      =ᵐ[blanketLaw center] endpointConditionalKernel center := by
  apply condDistrib_ae_eq_of_measure_eq_compProd_of_measurable
    measurable_blanketCoordinates measurable_endpointCoordinates
  change (stationaryLaw center).map partitionCoordinates =
    blanketLaw center ⊗ₘ endpointConditionalKernel center
  exact stationaryPartition_eq_compProd center

theorem externalCondDistrib_ae_eq (center : StandardizedState) :
    condDistrib (fun state : StandardizedState => state external)
        blanketCoordinates (stationaryLaw center) =ᵐ[blanketLaw center]
      externalConditionalKernel center := by
  have hMap :
      condDistrib (Prod.fst ∘ endpointCoordinates) blanketCoordinates
          (stationaryLaw center) =ᵐ[blanketLaw center]
        (condDistrib endpointCoordinates blanketCoordinates
          (stationaryLaw center)).map Prod.fst := by
    simpa only [blanketLaw] using
      (condDistrib_comp (μ := stationaryLaw center)
        measurable_blanketCoordinates.aemeasurable
        measurable_endpointCoordinates.aemeasurable
        (f := Prod.fst) measurable_fst)
  have hMap' :
      condDistrib (fun state : StandardizedState => state external)
          blanketCoordinates (stationaryLaw center) =ᵐ[blanketLaw center]
        (condDistrib endpointCoordinates blanketCoordinates
          (stationaryLaw center)).map Prod.fst := by
    have hExternalFunction :
        Prod.fst ∘ endpointCoordinates =
          fun state : StandardizedState => state external := by
      rfl
    rw [hExternalFunction] at hMap
    exact hMap
  filter_upwards [hMap', endpointCondDistrib_ae_eq_product center]
    with blanket hComp hPair
  rw [hComp, Kernel.map_apply _ measurable_fst, hPair,
    endpointConditionalKernel, Kernel.prod_apply, Measure.map_fst_prod,
    measure_univ, one_smul]

theorem internalCondDistrib_ae_eq (center : StandardizedState) :
    condDistrib (fun state : StandardizedState => state internal)
        blanketCoordinates (stationaryLaw center) =ᵐ[blanketLaw center]
      internalConditionalKernel center := by
  have hMap :
      condDistrib (Prod.snd ∘ endpointCoordinates) blanketCoordinates
          (stationaryLaw center) =ᵐ[blanketLaw center]
        (condDistrib endpointCoordinates blanketCoordinates
          (stationaryLaw center)).map Prod.snd := by
    simpa only [blanketLaw] using
      (condDistrib_comp (μ := stationaryLaw center)
        measurable_blanketCoordinates.aemeasurable
        measurable_endpointCoordinates.aemeasurable
        (f := Prod.snd) measurable_snd)
  have hMap' :
      condDistrib (fun state : StandardizedState => state internal)
          blanketCoordinates (stationaryLaw center) =ᵐ[blanketLaw center]
        (condDistrib endpointCoordinates blanketCoordinates
          (stationaryLaw center)).map Prod.snd := by
    have hInternalFunction :
        Prod.snd ∘ endpointCoordinates =
          fun state : StandardizedState => state internal := by
      rfl
    rw [hInternalFunction] at hMap
    exact hMap
  filter_upwards [hMap', endpointCondDistrib_ae_eq_product center]
    with blanket hComp hPair
  rw [hComp, Kernel.map_apply _ measurable_snd, hPair,
    endpointConditionalKernel, Kernel.prod_apply, Measure.map_snd_prod,
    measure_univ, one_smul]

theorem external_condIndep_internal_given_blanket
    (center : StandardizedState) :
    (fun state : StandardizedState => state external) ⟂ᵢ[
      blanketCoordinates, measurable_blanketCoordinates; stationaryLaw center]
      (fun state => state internal) := by
  rw [condIndepFun_iff_map_prod_eq_prod_condDistrib_prod_condDistrib
    (by fun_prop) (by fun_prop) measurable_blanketCoordinates]
  rw [← Measure.compProd_eq_comp_prod]
  have hRows :
      (condDistrib (fun state : StandardizedState => state external)
          blanketCoordinates (stationaryLaw center) ×ₖ
        condDistrib (fun state : StandardizedState => state internal)
          blanketCoordinates (stationaryLaw center)) =ᵐ[blanketLaw center]
        endpointConditionalKernel center := by
    filter_upwards [externalCondDistrib_ae_eq center,
      internalCondDistrib_ae_eq center] with blanket hExternal hInternal
    rw [Kernel.prod_apply, endpointConditionalKernel, Kernel.prod_apply,
      hExternal, hInternal]
  calc
    (stationaryLaw center).map
        (fun state =>
          (blanketCoordinates state, state external, state internal)) =
        (stationaryLaw center).map partitionCoordinates := by
          rfl
    _ = blanketLaw center ⊗ₘ endpointConditionalKernel center :=
      stationaryPartition_eq_compProd center
    _ = blanketLaw center ⊗ₘ
        (condDistrib (fun state : StandardizedState => state external)
            blanketCoordinates (stationaryLaw center) ×ₖ
          condDistrib (fun state : StandardizedState => state internal)
            blanketCoordinates (stationaryLaw center)) :=
      Measure.compProd_congr hRows.symm

theorem stationary_external_internal_covariance (center : StandardizedState) :
    cov[fun state : StandardizedState => state external,
      fun state => state internal; stationaryLaw center] = 1 / 24 := by
  rw [covariance_coordinate]
  exact Sigma_external_internal

theorem stationary_external_internal_covariance_ne_zero
    (center : StandardizedState) :
    cov[fun state : StandardizedState => state external,
      fun state => state internal; stationaryLaw center] ≠ 0 := by
  rw [stationary_external_internal_covariance]
  norm_num

theorem precisionZero_covarianceNonzero_condIndep
    (center : StandardizedState) :
    K external internal = 0 ∧
      cov[fun state : StandardizedState => state external,
        fun state => state internal; stationaryLaw center] = 1 / 24 ∧
      cov[fun state : StandardizedState => state external,
        fun state => state internal; stationaryLaw center] ≠ 0 ∧
      ((fun state : StandardizedState => state external) ⟂ᵢ[
        blanketCoordinates, measurable_blanketCoordinates; stationaryLaw center]
        (fun state => state internal)) := by
  exact ⟨K_external_internal, stationary_external_internal_covariance center,
    stationary_external_internal_covariance_ne_zero center,
    external_condIndep_internal_given_blanket center⟩

theorem perturbedEndpointPrecision_posDef :
    perturbedEndpointPrecision.PosDef :=
  perturbedEndpointPrecision_posDef_private

theorem perturbedEndpointCovariance_eq_entries :
    perturbedEndpointCovariance = !![4 / 15, -1 / 15; -1 / 15, 4 / 15] := by
  change perturbedEndpointPrecision⁻¹ =
    !![4 / 15, -1 / 15; -1 / 15, 4 / 15]
  apply Matrix.inv_eq_right_inv
  ext row column
  change (∑ index, perturbedEndpointPrecision row index *
      !![4 / 15, -1 / 15; -1 / 15, 4 / 15] index column) =
    (1 : Matrix (Fin 2) (Fin 2) ℝ) row column
  rw [Fin.sum_univ_two]
  fin_cases row <;> fin_cases column <;>
    norm_num [perturbedEndpointPrecision, Matrix.one_apply]

theorem perturbedEndpointCovariance_posDef :
    perturbedEndpointCovariance.PosDef :=
  perturbedEndpointCovariance_posDef_private

theorem perturbedEndpointPrecision_external_internal :
    perturbedEndpointPrecision 0 1 = 1 :=
  rfl

theorem perturbedEndpointCovariance_external_internal :
    perturbedEndpointCovariance 0 1 = -1 / 15 := by
  rw [perturbedEndpointCovariance_eq_entries]
  norm_num

theorem perturbedEndpoint_external_internal_covariance :
    cov[perturbedExternal, perturbedInternal; perturbedEndpointLaw] =
      -1 / 15 := by
  change cov[fun state : PerturbedEndpoints => state 0,
    fun state => state 1;
      multivariateGaussian 0 perturbedEndpointCovariance] = -1 / 15
  rw [covariance_eval_multivariateGaussian
    perturbedEndpointCovariance_posDef.posSemidef]
  exact perturbedEndpointCovariance_external_internal

private theorem perturbedExternal_memLp :
    MemLp perturbedExternal 2 perturbedEndpointLaw := by
  change MemLp (fun state : PerturbedEndpoints => state 0) 2
    perturbedEndpointLaw
  simpa [perturbedExternal, Function.comp_def] using
    ((IsGaussian.hasGaussianLaw_id (μ := perturbedEndpointLaw)).map
      (EuclideanSpace.proj (0 : Fin 2))).memLp_two

private theorem perturbedInternal_memLp :
    MemLp perturbedInternal 2 perturbedEndpointLaw := by
  change MemLp (fun state : PerturbedEndpoints => state 1) 2
    perturbedEndpointLaw
  simpa [perturbedInternal, Function.comp_def] using
    ((IsGaussian.hasGaussianLaw_id (μ := perturbedEndpointLaw)).map
      (EuclideanSpace.proj (1 : Fin 2))).memLp_two

theorem perturbedEndpoint_external_not_indep_internal :
    ¬ IndepFun perturbedExternal perturbedInternal perturbedEndpointLaw := by
  intro hIndep
  have hZero := hIndep.covariance_eq_zero
    perturbedExternal_memLp perturbedInternal_memLp
  rw [perturbedEndpoint_external_internal_covariance] at hZero
  norm_num at hZero

end

end FEP.GaussianPrecisionConditioning
