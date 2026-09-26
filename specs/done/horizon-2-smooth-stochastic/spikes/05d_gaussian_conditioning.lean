import FepSketches.fin4_gaussian_semigroup
import Mathlib.Probability.Distributions.Gaussian.HasGaussianLaw.Independence
import Mathlib.Probability.Independence.Conditional

/-!
# H2.5d-R0 fixed Fin4 native Gaussian conditioning proof spike

This non-maintained spike reconstructs the centered H2.5c stationary joint as
the actual sensory--active marginal composed with the native product of the
two scalar endpoint conditional laws.  It then invokes Mathlib's regular-
conditional-distribution uniqueness and native conditional-independence
predicate.  The result is stationary and center-zero only.
-/

namespace FEPProbe.H2_5dGaussianConditioning

open FEP.Fin4GaussianSemigroup
open FEP.Fin4GaussianSemigroup.Axis
open MeasureTheory ProbabilityTheory
open scoped ENNReal MeasureTheory NNReal ProbabilityTheory

noncomputable section

/-- Sensory--active coordinates, in that order. -/
abbrev Blanket := ℝ × ℝ

/-- External--internal coordinates, in that order. -/
abbrev Endpoints := ℝ × ℝ

/-- The sensory--active projection in the preregistered coordinate order. -/
def blanketCoordinates (state : StandardizedState) : Blanket :=
  (state sensory, state active)

/-- The external--internal projection in the preregistered coordinate order. -/
def endpointCoordinates (state : StandardizedState) : Endpoints :=
  (state external, state internal)

/-- The blanket-first partition used by native `compProd` reconstruction. -/
def partitionCoordinates (state : StandardizedState) : Blanket × Endpoints :=
  (blanketCoordinates state, endpointCoordinates state)

/-- The actual sensory--active marginal of the accepted centered stationary law. -/
noncomputable def blanketLaw : Measure Blanket :=
  (stationaryLaw (0 : StandardizedState)).map blanketCoordinates

/-- Common conditional mean of both endpoints at a blanket value. -/
def conditionalOffset (blanket : Blanket) : ℝ :=
  (blanket.1 + blanket.2) / 4

/-- Native scalar Gaussian row for the external coordinate. -/
noncomputable def externalConditionalKernel : Kernel Blanket ℝ where
  toFun blanket := gaussianReal (conditionalOffset blanket) (1 / 4)
  measurable' := by
    change Measurable
      (Function.uncurry gaussianReal ∘
        fun blanket : Blanket => (conditionalOffset blanket, (1 / 4 : ℝ≥0)))
    exact measurable_gaussianReal.comp
      ((by
        unfold conditionalOffset
        fun_prop : Measurable conditionalOffset).prodMk measurable_const)

private noncomputable instance externalConditionalKernel_isMarkovKernel :
    IsMarkovKernel externalConditionalKernel :=
  ⟨fun blanket => by
    change IsProbabilityMeasure
      (gaussianReal (conditionalOffset blanket) (1 / 4))
    infer_instance⟩

/-- Native scalar Gaussian row for the internal coordinate. -/
noncomputable def internalConditionalKernel : Kernel Blanket ℝ where
  toFun blanket := gaussianReal (conditionalOffset blanket) (1 / 4)
  measurable' := by
    change Measurable
      (Function.uncurry gaussianReal ∘
        fun blanket : Blanket => (conditionalOffset blanket, (1 / 4 : ℝ≥0)))
    exact measurable_gaussianReal.comp
      ((by
        unfold conditionalOffset
        fun_prop : Measurable conditionalOffset).prodMk measurable_const)

private noncomputable instance internalConditionalKernel_isMarkovKernel :
    IsMarkovKernel internalConditionalKernel :=
  ⟨fun blanket => by
    change IsProbabilityMeasure
      (gaussianReal (conditionalOffset blanket) (1 / 4))
    infer_instance⟩

/-- Product of the two native scalar endpoint rows. -/
noncomputable def endpointConditionalKernel : Kernel Blanket Endpoints :=
  externalConditionalKernel ×ₖ internalConditionalKernel

private noncomputable instance endpointConditionalKernel_isMarkovKernel :
    IsMarkovKernel endpointConditionalKernel := by
  unfold endpointConditionalKernel
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

private noncomputable instance blanketLaw_isProbabilityMeasure :
    IsProbabilityMeasure blanketLaw := by
  unfold blanketLaw
  exact (Measure.isProbabilityMeasure_map_iff
    measurable_blanketCoordinates.aemeasurable).mpr (by infer_instance)

theorem externalConditionalKernel_apply (blanket : Blanket) :
    externalConditionalKernel blanket =
      gaussianReal ((blanket.1 + blanket.2) / 4) (1 / 4) :=
  rfl

theorem internalConditionalKernel_apply (blanket : Blanket) :
    internalConditionalKernel blanket =
      gaussianReal ((blanket.1 + blanket.2) / 4) (1 / 4) :=
  rfl

theorem endpointConditionalKernel_apply (blanket : Blanket) :
    endpointConditionalKernel blanket =
      (gaussianReal ((blanket.1 + blanket.2) / 4) (1 / 4)).prod
        (gaussianReal ((blanket.1 + blanket.2) / 4) (1 / 4)) := by
  rw [endpointConditionalKernel, Kernel.prod_apply,
    externalConditionalKernel_apply, internalConditionalKernel_apply]

private abbrev centeredStationary : Measure StandardizedState :=
  stationaryLaw (0 : StandardizedState)

private noncomputable instance centeredStationary_isGaussian :
    IsGaussian centeredStationary := by
  rw [show centeredStationary = multivariateGaussian 0 Sigma by
    exact stationaryLaw_eq_gaussian 0]
  infer_instance

private def externalResidual (state : StandardizedState) : ℝ :=
  state external - conditionalOffset (blanketCoordinates state)

private def internalResidual (state : StandardizedState) : ℝ :=
  state internal - conditionalOffset (blanketCoordinates state)

private def endpointResidual (state : StandardizedState) : Endpoints :=
  (externalResidual state, internalResidual state)

private theorem measurable_externalResidual : Measurable externalResidual := by
  unfold externalResidual conditionalOffset blanketCoordinates
  fun_prop

private theorem measurable_internalResidual : Measurable internalResidual := by
  unfold internalResidual conditionalOffset blanketCoordinates
  fun_prop

private theorem measurable_endpointResidual : Measurable endpointResidual := by
  unfold endpointResidual
  exact measurable_externalResidual.prodMk measurable_internalResidual

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

private noncomputable def blanketCLM : StandardizedState →L[ℝ] Blanket :=
  (coordinateCLM sensory).prod (coordinateCLM active)

private noncomputable def residualCLM : StandardizedState →L[ℝ] Endpoints :=
  externalResidualCLM.prod internalResidualCLM

private theorem blanketCLM_apply (state : StandardizedState) :
    blanketCLM state = blanketCoordinates state := by
  rfl

private theorem externalResidualCLM_apply (state : StandardizedState) :
    externalResidualCLM state = externalResidual state := by
  simp [externalResidualCLM, offsetCLM, coordinateCLM, externalResidual,
    conditionalOffset, blanketCoordinates]
  ring

private theorem internalResidualCLM_apply (state : StandardizedState) :
    internalResidualCLM state = internalResidual state := by
  simp [internalResidualCLM, offsetCLM, coordinateCLM, internalResidual,
    conditionalOffset, blanketCoordinates]
  ring

private theorem residualCLM_apply (state : StandardizedState) :
    residualCLM state = endpointResidual state := by
  simp [residualCLM, endpointResidual, externalResidualCLM_apply,
    internalResidualCLM_apply]

private theorem coordinate_memLp (axis : Axis) :
    MemLp (fun state : StandardizedState => state axis) 2 centeredStationary := by
  simpa [coordinateCLM, Function.comp_def] using
    ((IsGaussian.hasGaussianLaw_id (μ := centeredStationary)).map
      (coordinateCLM axis)).memLp_two

private theorem covariance_coordinate (left right : Axis) :
    cov[fun state : StandardizedState => state left,
      fun state => state right; centeredStationary] = Sigma left right := by
  change cov[fun state : StandardizedState => state left,
    fun state => state right; stationaryLaw 0] = Sigma left right
  rw [stationaryLaw_eq_gaussian]
  exact covariance_eval_multivariateGaussian Sigma_posDef.posSemidef left right

private theorem offset_memLp :
    MemLp (fun state : StandardizedState =>
      conditionalOffset (blanketCoordinates state)) 2 centeredStationary := by
  have hSensory := coordinate_memLp sensory
  have hActive := coordinate_memLp active
  simpa [conditionalOffset, blanketCoordinates, div_eq_mul_inv, mul_comm] using
    (hSensory.add hActive).const_mul (4 : ℝ)⁻¹

private theorem covariance_coordinate_offset (axis : Axis) :
    cov[fun state : StandardizedState => state axis,
      fun state => conditionalOffset (blanketCoordinates state);
        centeredStationary] = (Sigma axis sensory + Sigma axis active) / 4 := by
  rw [show (fun state : StandardizedState =>
      conditionalOffset (blanketCoordinates state)) =
        fun state => (state sensory + state active) / 4 by
      funext state
      rfl]
  rw [covariance_fun_div_right]
  change
    cov[fun state : StandardizedState => state axis,
      (fun state => state sensory) + (fun state => state active);
        centeredStationary] / 4 = _
  rw [covariance_add_right]
  · rw [covariance_coordinate, covariance_coordinate]
  · exact coordinate_memLp axis
  · exact coordinate_memLp sensory
  · exact coordinate_memLp active

private theorem covariance_offset_coordinate (axis : Axis) :
    cov[fun state : StandardizedState =>
      conditionalOffset (blanketCoordinates state),
      fun state => state axis; centeredStationary] =
        (Sigma sensory axis + Sigma active axis) / 4 := by
  rw [covariance_comm, covariance_coordinate_offset, Sigma_eq_entries]
  cases axis <;> norm_num

private theorem covariance_offset_self :
    cov[fun state : StandardizedState =>
      conditionalOffset (blanketCoordinates state),
      fun state => conditionalOffset (blanketCoordinates state);
        centeredStationary] = 1 / 24 := by
  rw [show (fun state : StandardizedState =>
      conditionalOffset (blanketCoordinates state)) =
        fun state => (state sensory + state active) / 4 by
      funext state
      rfl]
  rw [covariance_fun_div_left, covariance_fun_div_right]
  change
    cov[(fun state : StandardizedState => state sensory) +
        (fun state => state active),
      (fun state => state sensory) + (fun state => state active);
        centeredStationary] / 4 / 4 = _
  rw [covariance_add_left, covariance_add_right, covariance_add_right]
  all_goals try exact (coordinate_memLp sensory).add (coordinate_memLp active)
  all_goals try exact coordinate_memLp sensory
  all_goals try exact coordinate_memLp active
  rw [covariance_coordinate, covariance_coordinate,
    covariance_coordinate, covariance_coordinate, Sigma_eq_entries]
  norm_num

private def blanketAxis : Bool → Axis
  | false => sensory
  | true => active

private def residualAxis : Bool → Axis
  | false => external
  | true => internal

private def blanketComponent (index : Bool) (state : StandardizedState) : ℝ :=
  state (blanketAxis index)

private def residualComponent (index : Bool) (state : StandardizedState) : ℝ :=
  state (residualAxis index) - conditionalOffset (blanketCoordinates state)

private theorem blanket_residual_covariance_zero
    (blanketIndex residualIndex : Bool) :
    cov[blanketComponent blanketIndex, residualComponent residualIndex;
      centeredStationary] = 0 := by
  rw [show residualComponent residualIndex = fun state : StandardizedState =>
      state (residualAxis residualIndex) -
        conditionalOffset (blanketCoordinates state) by rfl,
    covariance_fun_sub_right]
  · change cov[fun state : StandardizedState => state (blanketAxis blanketIndex),
      fun state => state (residualAxis residualIndex); centeredStationary] -
        cov[fun state : StandardizedState => state (blanketAxis blanketIndex),
          fun state => conditionalOffset (blanketCoordinates state);
            centeredStationary] = 0
    rw [covariance_coordinate, covariance_coordinate_offset, Sigma_eq_entries]
    cases blanketIndex <;> cases residualIndex <;> norm_num [blanketAxis, residualAxis]
  · exact coordinate_memLp (blanketAxis blanketIndex)
  · exact coordinate_memLp (residualAxis residualIndex)
  · exact offset_memLp

private theorem external_internal_residual_covariance_zero :
    cov[externalResidual, internalResidual; centeredStationary] = 0 := by
  rw [show externalResidual = fun state : StandardizedState =>
      state external - conditionalOffset (blanketCoordinates state) by rfl,
    show internalResidual = fun state : StandardizedState =>
      state internal - conditionalOffset (blanketCoordinates state) by rfl,
    covariance_fun_sub_fun_sub]
  · rw [covariance_coordinate, covariance_coordinate_offset,
      covariance_offset_coordinate, covariance_offset_self, Sigma_eq_entries]
    norm_num
  · exact coordinate_memLp external
  · exact offset_memLp
  · exact coordinate_memLp internal
  · exact offset_memLp

private theorem externalResidual_mean :
    ∫ state, externalResidual state ∂centeredStationary = 0 := by
  rw [show centeredStationary = multivariateGaussian 0 Sigma by
    exact stationaryLaw_eq_gaussian 0]
  simp_rw [← externalResidualCLM_apply]
  rw [externalResidualCLM.integral_comp_id_comm IsGaussian.integrable_id,
    integral_id_multivariateGaussian]
  simp

private theorem internalResidual_mean :
    ∫ state, internalResidual state ∂centeredStationary = 0 := by
  rw [show centeredStationary = multivariateGaussian 0 Sigma by
    exact stationaryLaw_eq_gaussian 0]
  simp_rw [← internalResidualCLM_apply]
  rw [internalResidualCLM.integral_comp_id_comm IsGaussian.integrable_id,
    integral_id_multivariateGaussian]
  simp

private theorem externalResidual_variance :
    Var[externalResidual; centeredStationary] = 1 / 4 := by
  rw [← covariance_self measurable_externalResidual.aemeasurable,
    show externalResidual = fun state : StandardizedState =>
      state external - conditionalOffset (blanketCoordinates state) by rfl,
    covariance_fun_sub_fun_sub]
  · rw [covariance_coordinate, covariance_coordinate_offset,
      covariance_offset_coordinate, covariance_offset_self, Sigma_eq_entries]
    norm_num
  · exact coordinate_memLp external
  · exact offset_memLp
  · exact coordinate_memLp external
  · exact offset_memLp

private theorem internalResidual_variance :
    Var[internalResidual; centeredStationary] = 1 / 4 := by
  rw [← covariance_self measurable_internalResidual.aemeasurable,
    show internalResidual = fun state : StandardizedState =>
      state internal - conditionalOffset (blanketCoordinates state) by rfl,
    covariance_fun_sub_fun_sub]
  · rw [covariance_coordinate, covariance_coordinate_offset,
      covariance_offset_coordinate, covariance_offset_self, Sigma_eq_entries]
    norm_num
  · exact coordinate_memLp internal
  · exact offset_memLp
  · exact coordinate_memLp internal
  · exact offset_memLp

private theorem hasGaussianLaw_blanket_residual :
    HasGaussianLaw
      (fun state : StandardizedState =>
        (blanketCoordinates state, endpointResidual state))
      centeredStationary := by
  have h := (IsGaussian.hasGaussianLaw_id (μ := centeredStationary)).map
    (blanketCLM.prod residualCLM)
  refine h.congr ?_
  filter_upwards with state
  simp only [Function.comp_apply, id_eq, ContinuousLinearMap.prod_apply,
    blanketCLM_apply, residualCLM_apply]

private theorem blanket_indep_endpointResidual :
    IndepFun blanketCoordinates endpointResidual centeredStationary := by
  let blanketFamily : Bool → StandardizedState → ℝ := blanketComponent
  let residualFamily : Bool → StandardizedState → ℝ := residualComponent
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
          fun index => residualFamily index state)) centeredStationary := by
    have h := (IsGaussian.hasGaussianLaw_id (μ := centeredStationary)).map
      (blanketFamilyCLM.prod residualFamilyCLM)
    refine h.congr ?_
    filter_upwards with state
    ext index <;> cases index <;>
      simp only [Function.comp_apply, id_eq, ContinuousLinearMap.prod_apply,
        ContinuousLinearMap.pi_apply, blanketFamilyCLM, residualFamilyCLM,
        blanketFamily, residualFamily, blanketComponent, residualComponent,
        blanketAxis, residualAxis, coordinateCLM_apply,
        externalResidual, internalResidual,
        externalResidualCLM_apply,
        internalResidualCLM_apply]
  have hFamilies := hGaussian.indepFun_of_covariance_eval
    (fun i j => by
      have hCov := blanket_residual_covariance_zero i j
      simpa only [blanketFamily, residualFamily] using hCov)
  have hPairs := hFamilies.comp
    (φ := fun values : Bool → ℝ => (values false, values true))
    (ψ := fun values : Bool → ℝ => (values false, values true))
    (by fun_prop) (by fun_prop)
  refine hPairs.congr ?_ ?_
  · filter_upwards with state
    rfl
  · filter_upwards with state
    rfl

private theorem externalResidual_indep_internalResidual :
    IndepFun externalResidual internalResidual centeredStationary := by
  exact hasGaussianLaw_blanket_residual.snd.indepFun_of_covariance_eq_zero
    external_internal_residual_covariance_zero

private theorem externalResidual_map :
    centeredStationary.map externalResidual = gaussianReal 0 (1 / 4) := by
  have h := hasGaussianLaw_blanket_residual.snd.fst.map_eq_gaussianReal
  rw [externalResidual_mean, externalResidual_variance] at h
  have hVariance : (1 / 4 : ℝ).toNNReal = (1 / 4 : ℝ≥0) := by
    apply NNReal.eq
    norm_num [Real.coe_toNNReal]
  simpa only [hVariance] using h

private theorem internalResidual_map :
    centeredStationary.map internalResidual = gaussianReal 0 (1 / 4) := by
  have h := hasGaussianLaw_blanket_residual.snd.snd.map_eq_gaussianReal
  rw [internalResidual_mean, internalResidual_variance] at h
  have hVariance : (1 / 4 : ℝ).toNNReal = (1 / 4 : ℝ≥0) := by
    apply NNReal.eq
    norm_num [Real.coe_toNNReal]
  simpa only [hVariance] using h

private theorem endpointResidual_map :
    centeredStationary.map endpointResidual =
      (gaussianReal 0 (1 / 4)).prod (gaussianReal 0 (1 / 4)) := by
  rw [show endpointResidual = fun state =>
      (externalResidual state, internalResidual state) by rfl,
    externalResidual_indep_internalResidual.map_prod_eq_prod_map_map
      measurable_externalResidual.aemeasurable
      measurable_internalResidual.aemeasurable,
    externalResidual_map, internalResidual_map]

private theorem blanket_endpointResidual_map :
    centeredStationary.map
        (fun state => (blanketCoordinates state, endpointResidual state)) =
      blanketLaw.prod
        ((gaussianReal 0 (1 / 4)).prod (gaussianReal 0 (1 / 4))) := by
  rw [blanket_indep_endpointResidual.map_prod_eq_prod_map_map
      measurable_blanketCoordinates.aemeasurable
      measurable_endpointResidual.aemeasurable,
    endpointResidual_map]
  rfl

private def shiftEndpoints (blanket : Blanket) (residual : Endpoints) : Endpoints :=
  (residual.1 + conditionalOffset blanket,
    residual.2 + conditionalOffset blanket)

private def shiftPartition (value : Blanket × Endpoints) : Blanket × Endpoints :=
  (value.1, shiftEndpoints value.1 value.2)

private theorem measurable_shiftEndpoints (blanket : Blanket) :
    Measurable (shiftEndpoints blanket) := by
  unfold shiftEndpoints conditionalOffset
  fun_prop

private theorem measurable_shiftPartition : Measurable shiftPartition := by
  unfold shiftPartition shiftEndpoints conditionalOffset
  fun_prop

private theorem endpointConditionalKernel_eq_shift (blanket : Blanket) :
    endpointConditionalKernel blanket =
      ((gaussianReal 0 (1 / 4)).prod (gaussianReal 0 (1 / 4))).map
        (shiftEndpoints blanket) := by
  rw [endpointConditionalKernel_apply]
  symm
  calc
    ((gaussianReal 0 (1 / 4)).prod (gaussianReal 0 (1 / 4))).map
        (shiftEndpoints blanket) =
      ((gaussianReal 0 (1 / 4)).prod (gaussianReal 0 (1 / 4))).map
        (Prod.map (fun value => value + conditionalOffset blanket)
          (fun value => value + conditionalOffset blanket)) := by
            congr 1
    _ = ((gaussianReal 0 (1 / 4)).map
          (fun value => value + conditionalOffset blanket)).prod
        ((gaussianReal 0 (1 / 4)).map
          (fun value => value + conditionalOffset blanket)) :=
      (Measure.map_prod_map (gaussianReal 0 (1 / 4))
        (gaussianReal 0 (1 / 4)) (by fun_prop) (by fun_prop)).symm
    _ = _ := by
      rw [gaussianReal_map_add_const]
      simp [conditionalOffset]

private theorem compProd_endpointConditionalKernel_eq_shifted_product :
    blanketLaw ⊗ₘ endpointConditionalKernel =
      (blanketLaw.prod
        ((gaussianReal 0 (1 / 4)).prod (gaussianReal 0 (1 / 4)))).map
          shiftPartition := by
  ext set hset
  rw [Measure.compProd_apply hset, Measure.map_apply measurable_shiftPartition hset,
    Measure.prod_apply (measurable_shiftPartition hset)]
  apply lintegral_congr
  intro blanket
  rw [endpointConditionalKernel_eq_shift,
    Measure.map_apply (measurable_shiftEndpoints blanket)
      (measurable_prodMk_left hset)]
  rfl

theorem stationaryPartition_eq_compProd :
    (stationaryLaw (0 : StandardizedState)).map partitionCoordinates =
      blanketLaw ⊗ₘ endpointConditionalKernel := by
  calc
    centeredStationary.map partitionCoordinates =
        centeredStationary.map
          (fun state => shiftPartition
            (blanketCoordinates state, endpointResidual state)) := by
      apply Measure.map_congr
      filter_upwards with state
      simp [partitionCoordinates, shiftPartition, shiftEndpoints, endpointResidual,
        endpointCoordinates, externalResidual, internalResidual]
    _ = centeredStationary.map
          (shiftPartition ∘
            fun state => (blanketCoordinates state, endpointResidual state)) := by
      apply Measure.map_congr
      filter_upwards with state
      rfl
    _ = (centeredStationary.map
          (fun state => (blanketCoordinates state, endpointResidual state))).map
            shiftPartition :=
      (Measure.map_map measurable_shiftPartition
        (measurable_blanketCoordinates.prodMk measurable_endpointResidual)).symm
    _ = (blanketLaw.prod
          ((gaussianReal 0 (1 / 4)).prod (gaussianReal 0 (1 / 4)))).map
            shiftPartition := by
      rw [blanket_endpointResidual_map]
    _ = blanketLaw ⊗ₘ endpointConditionalKernel :=
      compProd_endpointConditionalKernel_eq_shifted_product.symm

theorem endpointCondDistrib_ae_eq_product :
    condDistrib endpointCoordinates blanketCoordinates
        (stationaryLaw (0 : StandardizedState)) =ᵐ[blanketLaw]
      endpointConditionalKernel := by
  apply condDistrib_ae_eq_of_measure_eq_compProd_of_measurable
    measurable_blanketCoordinates measurable_endpointCoordinates
  change (stationaryLaw (0 : StandardizedState)).map partitionCoordinates =
    blanketLaw ⊗ₘ endpointConditionalKernel
  exact stationaryPartition_eq_compProd

theorem externalCondDistrib_ae_eq :
    condDistrib (fun state : StandardizedState => state external)
        blanketCoordinates (stationaryLaw (0 : StandardizedState)) =ᵐ[blanketLaw]
      externalConditionalKernel := by
  have hMap :
      condDistrib (Prod.fst ∘ endpointCoordinates) blanketCoordinates
          (stationaryLaw (0 : StandardizedState)) =ᵐ[blanketLaw]
        (condDistrib endpointCoordinates blanketCoordinates
          (stationaryLaw (0 : StandardizedState))).map Prod.fst := by
    simpa only [blanketLaw] using
      (condDistrib_comp (μ := stationaryLaw (0 : StandardizedState))
        measurable_blanketCoordinates.aemeasurable
        measurable_endpointCoordinates.aemeasurable
        (f := Prod.fst) measurable_fst)
  have hMap' :
      condDistrib (fun state : StandardizedState => state external)
          blanketCoordinates (stationaryLaw (0 : StandardizedState)) =ᵐ[blanketLaw]
        (condDistrib endpointCoordinates blanketCoordinates
          (stationaryLaw (0 : StandardizedState))).map Prod.fst := by
    have hExternalFunction :
        Prod.fst ∘ endpointCoordinates =
          fun state : StandardizedState => state external := by
      rfl
    rw [hExternalFunction] at hMap
    exact hMap
  filter_upwards [hMap', endpointCondDistrib_ae_eq_product] with blanket hComp hPair
  rw [hComp, Kernel.map_apply _ measurable_fst, hPair,
    endpointConditionalKernel, Kernel.prod_apply, Measure.map_fst_prod,
    measure_univ, one_smul]

theorem internalCondDistrib_ae_eq :
    condDistrib (fun state : StandardizedState => state internal)
        blanketCoordinates (stationaryLaw (0 : StandardizedState)) =ᵐ[blanketLaw]
      internalConditionalKernel := by
  have hMap :
      condDistrib (Prod.snd ∘ endpointCoordinates) blanketCoordinates
          (stationaryLaw (0 : StandardizedState)) =ᵐ[blanketLaw]
        (condDistrib endpointCoordinates blanketCoordinates
          (stationaryLaw (0 : StandardizedState))).map Prod.snd := by
    simpa only [blanketLaw] using
      (condDistrib_comp (μ := stationaryLaw (0 : StandardizedState))
        measurable_blanketCoordinates.aemeasurable
        measurable_endpointCoordinates.aemeasurable
        (f := Prod.snd) measurable_snd)
  have hMap' :
      condDistrib (fun state : StandardizedState => state internal)
          blanketCoordinates (stationaryLaw (0 : StandardizedState)) =ᵐ[blanketLaw]
        (condDistrib endpointCoordinates blanketCoordinates
          (stationaryLaw (0 : StandardizedState))).map Prod.snd := by
    have hInternalFunction :
        Prod.snd ∘ endpointCoordinates =
          fun state : StandardizedState => state internal := by
      rfl
    rw [hInternalFunction] at hMap
    exact hMap
  filter_upwards [hMap', endpointCondDistrib_ae_eq_product] with blanket hComp hPair
  rw [hComp, Kernel.map_apply _ measurable_snd, hPair,
    endpointConditionalKernel, Kernel.prod_apply, Measure.map_snd_prod,
    measure_univ, one_smul]

theorem external_condIndep_internal_given_blanket :
    (fun state : StandardizedState => state external) ⟂ᵢ[
      blanketCoordinates, measurable_blanketCoordinates;
      stationaryLaw (0 : StandardizedState)]
      (fun state => state internal) := by
  rw [condIndepFun_iff_map_prod_eq_prod_condDistrib_prod_condDistrib
    (by fun_prop) (by fun_prop) measurable_blanketCoordinates]
  rw [← Measure.compProd_eq_comp_prod]
  have hRows :
      (condDistrib (fun state : StandardizedState => state external)
          blanketCoordinates (stationaryLaw (0 : StandardizedState)) ×ₖ
        condDistrib (fun state : StandardizedState => state internal)
          blanketCoordinates (stationaryLaw (0 : StandardizedState))) =ᵐ[blanketLaw]
        endpointConditionalKernel := by
    filter_upwards [externalCondDistrib_ae_eq, internalCondDistrib_ae_eq]
      with blanket hExternal hInternal
    rw [Kernel.prod_apply, endpointConditionalKernel, Kernel.prod_apply,
      hExternal, hInternal]
  calc
    (stationaryLaw (0 : StandardizedState)).map
        (fun state =>
          (blanketCoordinates state, state external, state internal)) =
        (stationaryLaw (0 : StandardizedState)).map partitionCoordinates := by
          rfl
    _ = blanketLaw ⊗ₘ endpointConditionalKernel :=
      stationaryPartition_eq_compProd
    _ = blanketLaw ⊗ₘ
        (condDistrib (fun state : StandardizedState => state external)
            blanketCoordinates (stationaryLaw (0 : StandardizedState)) ×ₖ
          condDistrib (fun state : StandardizedState => state internal)
            blanketCoordinates (stationaryLaw (0 : StandardizedState))) :=
      Measure.compProd_congr hRows.symm

theorem fixed_precisionZero_covarianceNonzero_condIndep :
    K external internal = 0 ∧
      cov[fun state : StandardizedState => state external,
        fun state => state internal; stationaryLaw (0 : StandardizedState)] =
          1 / 24 ∧
      cov[fun state : StandardizedState => state external,
        fun state => state internal; stationaryLaw (0 : StandardizedState)] ≠
          0 ∧
      ((fun state : StandardizedState => state external) ⟂ᵢ[
        blanketCoordinates, measurable_blanketCoordinates;
        stationaryLaw (0 : StandardizedState)]
        (fun state => state internal)) := by
  have hCovariance :
      cov[fun state : StandardizedState => state external,
        fun state => state internal; stationaryLaw (0 : StandardizedState)] =
          1 / 24 := by
    change cov[fun state : StandardizedState => state external,
      fun state => state internal; centeredStationary] = 1 / 24
    rw [covariance_coordinate]
    exact Sigma_external_internal
  have hCovarianceNonzero :
      cov[fun state : StandardizedState => state external,
        fun state => state internal; stationaryLaw (0 : StandardizedState)] ≠
          0 := by
    change cov[fun state : StandardizedState => state external,
      fun state => state internal; centeredStationary] ≠ 0
    rw [covariance_coordinate]
    exact Sigma_external_internal_ne_zero
  exact ⟨K_external_internal, hCovariance, hCovarianceNonzero,
    external_condIndep_internal_given_blanket⟩

end

end FEPProbe.H2_5dGaussianConditioning
