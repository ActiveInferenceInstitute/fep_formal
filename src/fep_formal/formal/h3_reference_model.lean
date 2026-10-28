module
public import FepSketches.fin4_gaussian_semigroup
public import FepSketches.markov_semigroup

@[expose] public section

/-!
# Frozen H3 continuous reference model

This foundation selects the exact accepted Fin4 carrier. Its named scientific
axis is an explicit alias of that carrier, not an equinumerous new type. Raw
readings have axis tags and enter the dimensionless state only through a
positive affine calibration. Covariance, transition normalization, semigroup
and invariance are derived; no result certificate is stored in the model.

The computable rational export is linked by equality theorems to native Real
parameters. Precision-block recognition algebra is intrinsic only: native
conditional laws, posterior/VFE, EFE/control and path information belong to the
H3 composition. This module constructs finite-time laws, not a stochastic
process, a causal graph, empirical validity or physical heat.
-/

open Filter MeasureTheory Matrix ProbabilityTheory
open scoped ENNReal MatrixOrder NNReal Topology

namespace FEP.H3ReferenceModel

noncomputable section

/-- The same named scientific axis as the exact H2 carrier. -/
abbrev Axis := FEP.Fin4GaussianSemigroup.Axis

namespace Axis

abbrev external : Axis := FEP.Fin4GaussianSemigroup.Axis.external
abbrev sensory : Axis := FEP.Fin4GaussianSemigroup.Axis.sensory
abbrev active : Axis := FEP.Fin4GaussianSemigroup.Axis.active
abbrev internal : Axis := FEP.Fin4GaussianSemigroup.Axis.internal

end Axis

open Axis

/-- The explicit scientific ordering, shared with the selected carrier. -/
def axisFin : Axis ≃ Fin 4 := FEP.Fin4GaussianSemigroup.axisFin

theorem axisFin_order :
    axisFin external = 0 ∧ axisFin sensory = 1 ∧
      axisFin active = 2 ∧ axisFin internal = 3 :=
  FEP.Fin4GaussianSemigroup.axisFin_order

theorem axis_cardinality : Fintype.card Axis = 4 :=
  FEP.Fin4GaussianSemigroup.axis_cardinality

/-- Dimensionless scientific coordinates, before the native Euclidean wrapper. -/
abbrev StandardState := Axis → ℝ

/-- The exact H2 Euclidean carrier, never an unnamed tuple coercion. -/
abbrev NativeState := FEP.Fin4GaussianSemigroup.StandardizedState

/-- Named reversible conversion between scientific functions and native states. -/
def nativeStateEquiv : StandardState ≃ NativeState where
  toFun := WithLp.toLp 2
  invFun := WithLp.ofLp
  left_inv _ := rfl
  right_inv _ := rfl

def toNativeState : StandardState → NativeState := nativeStateEquiv
def fromNativeState : NativeState → StandardState := nativeStateEquiv.symm

@[simp] theorem fromNative_toNative (state : StandardState) :
    fromNativeState (toNativeState state) = state := rfl

@[simp] theorem toNative_fromNative (state : NativeState) :
    toNativeState (fromNativeState state) = state := rfl

@[simp] theorem toNativeState_apply (state : StandardState) (axis : Axis) :
    toNativeState state axis = state axis := rfl

@[simp] theorem fromNativeState_apply (state : NativeState) (axis : Axis) :
    fromNativeState state axis = state axis := rfl

@[fun_prop] theorem continuous_toNativeState : Continuous toNativeState :=
  PiLp.continuous_toLp 2 (fun _ : Axis => ℝ)

@[fun_prop] theorem continuous_fromNativeState : Continuous fromNativeState :=
  PiLp.continuous_ofLp 2 (fun _ : Axis => ℝ)

@[fun_prop] theorem measurable_toNativeState : Measurable toNativeState :=
  continuous_toNativeState.measurable

@[fun_prop] theorem measurable_fromNativeState : Measurable fromNativeState :=
  continuous_fromNativeState.measurable

/-- Raw unit tags are synthetic calibration conventions, not energy units. -/
inductive RawUnit
  | externalUnit | sensoryUnit | activeUnit | internalUnit
  deriving DecidableEq, Repr

def rawUnit : Axis → RawUnit
  | .external => .externalUnit
  | .sensory => .sensoryUnit
  | .active => .activeUnit
  | .internal => .internalUnit

/-- Axis-indexed raw readings admit no implicit coercion to a dynamical state. -/
@[ext] structure RawReading (axis : Axis) where
  value : ℝ

abbrev RawState := (axis : Axis) → RawReading axis

/-- Only primitive calibration data and the admissible positive scale domain. -/
structure PositiveCalibration where
  offset : Axis → ℝ
  scale : Axis → ℝ
  scale_pos : ∀ axis, 0 < scale axis

def standardize (calibration : PositiveCalibration) (raw : RawState) : StandardState :=
  fun axis => ((raw axis).value - calibration.offset axis) / calibration.scale axis

def rawValue (calibration : PositiveCalibration) (axis : Axis) (value : ℝ) : ℝ :=
  calibration.offset axis + calibration.scale axis * value

def destandardize (calibration : PositiveCalibration) (state : StandardState) : RawState :=
  fun axis => ⟨rawValue calibration axis (state axis)⟩

theorem standardize_destandardize (calibration : PositiveCalibration)
    (state : StandardState) :
    standardize calibration (destandardize calibration state) = state := by
  funext axis
  simp [standardize, destandardize, rawValue, (calibration.scale_pos axis).ne']

theorem destandardize_standardize (calibration : PositiveCalibration)
    (raw : RawState) :
    destandardize calibration (standardize calibration raw) = raw := by
  funext axis
  apply RawReading.ext
  dsimp [destandardize, rawValue, standardize]
  field_simp [(calibration.scale_pos axis).ne']
  ring

theorem rawValue_strictMono (calibration : PositiveCalibration) (axis : Axis) :
    StrictMono (rawValue calibration axis) := by
  intro left right h
  simpa [rawValue, add_comm] using
    add_lt_add_left (mul_lt_mul_of_pos_left h (calibration.scale_pos axis))
      (calibration.offset axis)

theorem standardize_value_strictMono (calibration : PositiveCalibration) (axis : Axis) :
    StrictMono (fun value : ℝ =>
      (value - calibration.offset axis) / calibration.scale axis) := by
  intro left right h
  exact (div_lt_div_iff_of_pos_right (calibration.scale_pos axis)).2
    (sub_lt_sub_right h _)

def frozenCalibration : PositiveCalibration where
  offset
    | .external => 0
    | .sensory => 1
    | .active => -1
    | .internal => 2
  scale
    | .external => 1
    | .sensory => 2
    | .active => 3
    | .internal => 4
  scale_pos axis := by cases axis <;> norm_num

theorem nonpositive_scale_excluded (calibration : PositiveCalibration) (axis : Axis) :
    ¬ calibration.scale axis ≤ 0 := not_le.mpr (calibration.scale_pos axis)

/-- Precision is the exact carrier pullback through the named axis equivalence. -/
def K : Matrix Axis Axis ℝ := fun row column =>
  FEP.Fin4GaussianSemigroup.K
    (FEP.Fin4GaussianSemigroup.axisFin.symm (axisFin row))
    (FEP.Fin4GaussianSemigroup.axisFin.symm (axisFin column))

theorem K_eq_carrier : K = FEP.Fin4GaussianSemigroup.K := by
  ext row column
  simp [K, axisFin]

/-- Covariance is computed as the inverse, never a model field. -/
def Sigma : Matrix Axis Axis ℝ := K⁻¹

theorem Sigma_eq_carrier : Sigma = FEP.Fin4GaussianSemigroup.Sigma := by
  rw [Sigma, K_eq_carrier]
  rfl

theorem K_isSymm : K.IsSymm := by
  rw [K_eq_carrier]
  exact FEP.Fin4GaussianSemigroup.K_isSymm

theorem K_posDef : K.PosDef := by
  rw [K_eq_carrier]
  exact FEP.Fin4GaussianSemigroup.K_posDef

theorem K_mul_Sigma : K * Sigma = 1 := by
  rw [K_eq_carrier, Sigma_eq_carrier]
  exact FEP.Fin4GaussianSemigroup.K_mul_Sigma

theorem Sigma_mul_K : Sigma * K = 1 := by
  rw [K_eq_carrier, Sigma_eq_carrier]
  exact FEP.Fin4GaussianSemigroup.Sigma_mul_K

theorem Sigma_isSymm : Sigma.IsSymm := by
  rw [Sigma_eq_carrier]
  exact FEP.Fin4GaussianSemigroup.Sigma_isSymm

theorem Sigma_posDef : Sigma.PosDef := by
  rw [Sigma_eq_carrier]
  exact FEP.Fin4GaussianSemigroup.Sigma_posDef

def transitionCovariance (time : ℝ≥0) : Matrix Axis Axis ℝ :=
  Sigma - NormedSpace.exp ((-(time : ℝ)) • K) * Sigma *
    (NormedSpace.exp ((-(time : ℝ)) • K))ᵀ

theorem transitionCovariance_posSemidef (time : ℝ≥0) :
    (transitionCovariance time).PosSemidef := by
  simp only [transitionCovariance, K_eq_carrier, Sigma_eq_carrier]
  exact FEP.Fin4GaussianSemigroup.transitionCovariance_posSemidef 0 time

theorem transitionCovariance_posDef (time : ℝ≥0) (hTime : 0 < time) :
    (transitionCovariance time).PosDef := by
  simp only [transitionCovariance, K_eq_carrier, Sigma_eq_carrier]
  exact FEP.Fin4GaussianSemigroup.transitionCovariance_posDef 0 time hTime

def toNativeKernel : Kernel StandardState NativeState :=
  Kernel.deterministic toNativeState measurable_toNativeState

def fromNativeKernel : Kernel NativeState StandardState :=
  Kernel.deterministic fromNativeState measurable_fromNativeState

theorem toNativeKernel_fromNativeKernel :
    toNativeKernel ∘ₖ fromNativeKernel = Kernel.id := by
  rw [toNativeKernel, fromNativeKernel, Kernel.deterministic_comp_deterministic]
  simp only [Function.comp_def, toNative_fromNative]
  rfl

theorem fromNativeKernel_toNativeKernel :
    fromNativeKernel ∘ₖ toNativeKernel = Kernel.id := by
  rw [fromNativeKernel, toNativeKernel, Kernel.deterministic_comp_deterministic]
  simp only [Function.comp_def, fromNative_toNative]
  rfl

/-- Exact carrier transition transported by the named state equivalence. -/
def transition (center : StandardState) (time : ℝ≥0) :
    Kernel StandardState StandardState :=
  fromNativeKernel ∘ₖ
    FEP.Fin4GaussianSemigroup.transition (toNativeState center) time ∘ₖ toNativeKernel

instance transition_isMarkovKernel (center : StandardState) (time : ℝ≥0) :
    IsMarkovKernel (transition center time) := by
  unfold transition toNativeKernel fromNativeKernel
  infer_instance

/-- Actual row-law identification through both directions of the state seam. -/
theorem transition_apply (center state : StandardState) (time : ℝ≥0) :
    transition center time state =
      (FEP.Fin4GaussianSemigroup.transition (toNativeState center) time
        (toNativeState state)).map fromNativeState := by
  rw [transition, toNativeKernel, Kernel.comp_deterministic_eq_comap,
    Kernel.comap_apply, fromNativeKernel, Kernel.deterministic_comp_eq_map,
    Kernel.map_apply _ measurable_fromNativeState]

theorem transition_eq_gaussian_map (center state : StandardState) (time : ℝ≥0) :
    transition center time state =
      (multivariateGaussian
        (toNativeState center + Matrix.toEuclideanCLM (𝕜 := ℝ)
          (NormedSpace.exp ((-(time : ℝ)) • K))
          (toNativeState state - toNativeState center))
        (transitionCovariance time)).map fromNativeState := by
  rw [transition_apply, FEP.Fin4GaussianSemigroup.transition_apply]
  rw [transitionCovariance, K_eq_carrier, Sigma_eq_carrier]

theorem transition_univ (center : StandardState) (time : ℝ≥0) (state : StandardState) :
    transition center time state Set.univ = 1 := measure_univ

theorem transition_zero (center : StandardState) : transition center 0 = Kernel.id := by
  rw [transition, FEP.Fin4GaussianSemigroup.transition_zero, Kernel.comp_id]
  exact fromNativeKernel_toNativeKernel

theorem transition_add (center : StandardState) (left right : ℝ≥0) :
    transition center (left + right) = transition center right ∘ₖ transition center left := by
  simp only [transition, FEP.Fin4GaussianSemigroup.transition_add]
  simp only [Kernel.comp_assoc]
  rw [← Kernel.comp_assoc toNativeKernel fromNativeKernel,
    toNativeKernel_fromNativeKernel, Kernel.id_comp]

def nativeSemigroup (center : StandardState) :
    FEP.MarkovSemigroup.NativeKernelSemigroup (transition center) where
  kernel_zero := transition_zero center
  kernel_add := transition_add center

/-- The selected Gaussian law transported to the dimensionless scientific state. -/
def stationaryLaw (center : StandardState) : Measure StandardState :=
  fromNativeKernel ∘ₘ FEP.Fin4GaussianSemigroup.stationaryLaw (toNativeState center)

instance stationaryLaw_isProbabilityMeasure (center : StandardState) :
    IsProbabilityMeasure (stationaryLaw center) := by
  unfold stationaryLaw fromNativeKernel
  infer_instance

theorem stationaryLaw_eq_gaussian_map (center : StandardState) :
    stationaryLaw center =
      (multivariateGaussian (toNativeState center) Sigma).map fromNativeState := by
  rw [stationaryLaw, fromNativeKernel, Measure.deterministic_comp_eq_map,
    FEP.Fin4GaussianSemigroup.stationaryLaw_eq_gaussian, Sigma_eq_carrier]

theorem stationaryLaw_invariant (center : StandardState) :
    FEP.MarkovSemigroup.InvariantLaw (nativeSemigroup center) (stationaryLaw center) := by
  intro time
  change transition center time ∘ₘ stationaryLaw center = stationaryLaw center
  simp only [transition, stationaryLaw, Measure.comp_assoc, Kernel.comp_assoc]
  rw [toNativeKernel_fromNativeKernel, Kernel.comp_id]
  rw [← Measure.comp_assoc]
  rw [FEP.Fin4GaussianSemigroup.stationaryLaw_invariant (toNativeState center) time]

/-- Weak-convergence view, obtained by continuous transport of the exact law. -/
def transitionProbability (center state : StandardState) (time : ℝ≥0) :
    ProbabilityMeasure StandardState :=
  (FEP.Fin4GaussianSemigroup.transitionProbability (toNativeState center) time
    (toNativeState state)).map fromNativeState

def stationaryProbability (center : StandardState) : ProbabilityMeasure StandardState :=
  (FEP.Fin4GaussianSemigroup.stationaryProbability (toNativeState center)).map fromNativeState

theorem transitionProbability_eq (center state : StandardState) (time : ℝ≥0) :
    (transitionProbability center state time : Measure StandardState) =
      transition center time state := by
  rw [transition_apply]
  rfl

theorem stationaryProbability_eq (center : StandardState) :
    (stationaryProbability center : Measure StandardState) = stationaryLaw center := by
  rw [stationaryLaw, fromNativeKernel, Measure.deterministic_comp_eq_map]
  rfl

theorem transitionProbability_tendsto_invariant (center state : StandardState) :
    Tendsto (transitionProbability center state) atTop
      (nhds (stationaryProbability center)) := by
  exact ProbabilityMeasure.tendsto_map_of_tendsto_of_continuous _ _
    (FEP.Fin4GaussianSemigroup.transitionProbability_tendsto_invariant
      (toNativeState center) (toNativeState state)) continuous_fromNativeState

/-- Primitive Bool center selections on the same four-axis transition family. -/
def actionCenter (action : Bool) : StandardState :=
  fun _ => if action then (1 / 2 : ℝ) else -1 / 2

theorem toNative_actionCenter (action : Bool) :
    toNativeState (actionCenter action) =
      FEP.Fin4GaussianSemigroup.allOnesEmbedding (if action then 1 else -1) := by
  cases action <;> ext axis <;>
    norm_num [actionCenter, FEP.Fin4GaussianSemigroup.allOnesEmbedding,
      FEP.Fin4GaussianSemigroup.normalizedAllOnes]

def actionTransition (action : Bool) (time : ℝ≥0) : Kernel StandardState StandardState :=
  transition (actionCenter action) time

instance actionTransition_isMarkovKernel (action : Bool) (time : ℝ≥0) :
    IsMarkovKernel (actionTransition action time) := by
  unfold actionTransition
  infer_instance

/-- Native scalar parameters are selected, not reconstructed from fitted numbers. -/
def scalarParameters (center : ℝ) := FEP.Fin4GaussianSemigroup.scalarParameters center

theorem scalarParameters_exact (center : ℝ) :
    (scalarParameters center).rate = 2 ∧
      (scalarParameters center).diffusionVarianceRate = 2 :=
  FEP.Fin4GaussianSemigroup.scalarParameters_exact center

/-- Precision-block coefficient algebra; native conditioning is a composition claim. -/
def recognitionCoefficient (axis : Axis) : ℝ := -K external axis / K external external

def recognitionVariance : ℝ := (K external external)⁻¹

def recognitionMean (center state : StandardState) : ℝ :=
  center external + recognitionCoefficient sensory * (state sensory - center sensory) +
    recognitionCoefficient active * (state active - center active)

theorem recognition_precision_blocks :
    recognitionCoefficient sensory = 1 / 4 ∧
      recognitionCoefficient active = 1 / 4 ∧ recognitionVariance = 1 / 4 := by
  norm_num [recognitionCoefficient, recognitionVariance, K_eq_carrier,
    FEP.Fin4GaussianSemigroup.K, sensory, active, external]

theorem recognitionMean_eq (center state : StandardState) :
    recognitionMean center state = center external +
      ((state sensory - center sensory) + (state active - center active)) / 4 := by
  rcases recognition_precision_blocks with ⟨hSensory, hActive, _⟩
  rw [recognitionMean, hSensory, hActive]
  ring

/-- A fixed continuous model stores primitive data only, never inferred results. -/
structure ContinuousReferenceModel where
  center : StandardState
  initialMean : StandardState
  observationNoiseVariance : ℝ≥0
  observationNoiseVariance_pos : 0 < observationNoiseVariance
  sampleDuration : ℝ≥0
  sampleDuration_pos : 0 < sampleDuration
  calibration : PositiveCalibration

def frozenProtocolSha256 : String :=
  "50b3575316fb272dc7bf209f50a21330fc5ea0764da9399e20aedeb0b2302c93"

def settingA : ContinuousReferenceModel where
  center := fun _ => 0
  initialMean := fun _ => 0
  observationNoiseVariance := 1 / 8
  observationNoiseVariance_pos := by norm_num
  sampleDuration := 1 / 4
  sampleDuration_pos := by norm_num
  calibration := frozenCalibration

def settingB : ContinuousReferenceModel where
  center := fun _ => 3 / 8
  initialMean := fun _ => 3 / 8
  observationNoiseVariance := 1 / 4
  observationNoiseVariance_pos := by norm_num
  sampleDuration := 1 / 2
  sampleDuration_pos := by norm_num
  calibration := frozenCalibration

end

/-! ## Computable, theorem-bound finite parameter export -/

open Axis Lean

inductive Setting
  | A | B
  deriving DecidableEq, Repr

noncomputable def referenceSetting : Setting → ContinuousReferenceModel
  | .A => settingA
  | .B => settingB

def centerRat : Setting → ℚ
  | .A => 0
  | .B => 3 / 4

def observationNoiseRat : Setting → ℚ
  | .A => 1 / 8
  | .B => 1 / 4

def sampleDurationRat : Setting → ℚ
  | .A => 1 / 4
  | .B => 1 / 2

theorem settingRat_eq_native (setting : Setting) :
    (∀ axis, (centerRat setting : ℝ) / 2 = (referenceSetting setting).center axis) ∧
      (∀ axis, (centerRat setting : ℝ) / 2 = (referenceSetting setting).initialMean axis) ∧
      (observationNoiseRat setting : ℝ) =
        ((referenceSetting setting).observationNoiseVariance : ℝ) ∧
      (sampleDurationRat setting : ℝ) = ((referenceSetting setting).sampleDuration : ℝ) := by
  cases setting <;>
    norm_num [centerRat, observationNoiseRat, sampleDurationRat, referenceSetting, settingA, settingB]

def precisionRat (row column : Fin 4) : ℚ :=
  ![![4, -1, -1, 0], ![-1, 4, 0, -1], ![-1, 0, 4, -1], ![0, -1, -1, 4]] row column

def covarianceRat (row column : Fin 4) : ℚ :=
  ![![7/24, 1/12, 1/12, 1/24], ![1/12, 7/24, 1/24, 1/12],
    ![1/12, 1/24, 7/24, 1/12], ![1/24, 1/12, 1/12, 7/24]] row column

def scaleRat (axis : Fin 4) : ℚ := ![1, 2, 3, 4] axis
def offsetRat (axis : Fin 4) : ℚ := ![0, 1, -1, 2] axis
def scalarRateRat : ℚ := 2
def diffusionVarianceRateRat : ℚ := 2
def recognitionCoefficientRat : ℚ := 1 / 4
def recognitionVarianceRat : ℚ := 1 / 4

/-- Rows are scientific axes; columns are the four named, unnormalized H2 modes. -/
def modeRat (row column : Fin 4) : ℚ :=
  ![![1, 1, 0, 1], ![1, 0, 1, -1], ![1, 0, -1, -1], ![1, -1, 0, 1]] row column

def modeRateRat (mode : Fin 4) : ℚ := ![2, 4, 4, 6] mode

noncomputable def modeVector (mode : Fin 4) : StandardState :=
  ![FEP.Fin4GaussianSemigroup.eigenmodeTwo,
    FEP.Fin4GaussianSemigroup.eigenmodeFourExternal,
    FEP.Fin4GaussianSemigroup.eigenmodeFourSensory,
    FEP.Fin4GaussianSemigroup.eigenmodeSix] mode

theorem modeRat_eq_native (row column : Fin 4) :
    (modeRat row column : ℝ) = modeVector column (axisFin.symm row) := by
  obtain ⟨row, rfl⟩ := axisFin.surjective row
  simp only [Equiv.symm_apply_apply]
  cases row <;> fin_cases column <;>
    norm_num [modeRat, modeVector, axisFin, FEP.Fin4GaussianSemigroup.axisFin,
      FEP.Fin4GaussianSemigroup.eigenmodeTwo,
      FEP.Fin4GaussianSemigroup.eigenmodeFourExternal,
      FEP.Fin4GaussianSemigroup.eigenmodeFourSensory,
      FEP.Fin4GaussianSemigroup.eigenmodeSix]

theorem modeRateRat_eigenpair (mode : Fin 4) :
    K *ᵥ modeVector mode = (modeRateRat mode : ℝ) • modeVector mode := by
  rw [K_eq_carrier]
  fin_cases mode
  · funext axis
    convert congrFun FEP.Fin4GaussianSemigroup.K_eigenmode_two axis using 1 <;>
      norm_num [modeVector, modeRateRat, Pi.smul_apply, smul_eq_mul]
  · funext axis
    convert congrFun FEP.Fin4GaussianSemigroup.K_eigenmode_four_external axis using 1 <;>
      norm_num [modeVector, modeRateRat, Pi.smul_apply, smul_eq_mul]
  · funext axis
    convert congrFun FEP.Fin4GaussianSemigroup.K_eigenmode_four_sensory axis using 1 <;>
      norm_num [modeVector, modeRateRat, Pi.smul_apply, smul_eq_mul]
  · funext axis
    convert congrFun FEP.Fin4GaussianSemigroup.K_eigenmode_six axis using 1 <;>
      norm_num [modeVector, modeRateRat, Pi.smul_apply, smul_eq_mul]

theorem modeVector_nonzero (mode : Fin 4) : modeVector mode ≠ 0 := by
  fin_cases mode
  · exact FEP.Fin4GaussianSemigroup.eigenmodes_nonzero.1
  · exact FEP.Fin4GaussianSemigroup.eigenmodes_nonzero.2.1
  · exact FEP.Fin4GaussianSemigroup.eigenmodes_nonzero.2.2.1
  · exact FEP.Fin4GaussianSemigroup.eigenmodes_nonzero.2.2.2

def modeSquaredNormRat (mode : Fin 4) : ℚ := ![4, 2, 2, 4] mode

private theorem sum_axis (f : Axis → ℝ) :
    ∑ axis, f axis = f external + f sensory + f active + f internal := by
  classical
  change Finset.univ.sum f = _
  rw [show (Finset.univ : Finset Axis) = {external, sensory, active, internal} by
    ext axis
    cases axis <;> simp]
  simp [add_comm, add_left_comm]

/-- The actual H2 modes are orthogonal with strictly positive declared squared norms. -/
theorem modeVector_gram (left right : Fin 4) :
    modeVector left ⬝ᵥ modeVector right =
      if left = right then (modeSquaredNormRat left : ℝ) else 0 := by
  fin_cases left <;> fin_cases right <;>
    norm_num [modeVector, modeSquaredNormRat, dotProduct, sum_axis, axis_cardinality,
      FEP.Fin4GaussianSemigroup.eigenmodeTwo,
      FEP.Fin4GaussianSemigroup.eigenmodeFourExternal,
      FEP.Fin4GaussianSemigroup.eigenmodeFourSensory,
      FEP.Fin4GaussianSemigroup.eigenmodeSix, external, sensory, active, internal]

theorem precisionRat_eq_native (row column : Fin 4) :
    (precisionRat row column : ℝ) = K (axisFin.symm row) (axisFin.symm column) := by
  obtain ⟨row, rfl⟩ := axisFin.surjective row
  obtain ⟨column, rfl⟩ := axisFin.surjective column
  simp only [Equiv.symm_apply_apply]
  cases row <;> cases column <;>
    norm_num [precisionRat, K_eq_carrier, axisFin, FEP.Fin4GaussianSemigroup.axisFin,
      FEP.Fin4GaussianSemigroup.K]

theorem covarianceRat_eq_native (row column : Fin 4) :
    (covarianceRat row column : ℝ) = Sigma (axisFin.symm row) (axisFin.symm column) := by
  obtain ⟨row, rfl⟩ := axisFin.surjective row
  obtain ⟨column, rfl⟩ := axisFin.surjective column
  simp only [Equiv.symm_apply_apply]
  rw [Sigma_eq_carrier, FEP.Fin4GaussianSemigroup.Sigma_eq_entries]
  cases row <;> cases column <;>
    norm_num [covarianceRat, axisFin, FEP.Fin4GaussianSemigroup.axisFin]

theorem scaleRat_eq_native (axis : Fin 4) :
    (scaleRat axis : ℝ) = frozenCalibration.scale (axisFin.symm axis) := by
  obtain ⟨axis, rfl⟩ := axisFin.surjective axis
  simp only [Equiv.symm_apply_apply]
  cases axis <;> norm_num [scaleRat, frozenCalibration, axisFin,
    FEP.Fin4GaussianSemigroup.axisFin]

theorem offsetRat_eq_native (axis : Fin 4) :
    (offsetRat axis : ℝ) = frozenCalibration.offset (axisFin.symm axis) := by
  obtain ⟨axis, rfl⟩ := axisFin.surjective axis
  simp only [Equiv.symm_apply_apply]
  cases axis <;> norm_num [offsetRat, frozenCalibration, axisFin,
    FEP.Fin4GaussianSemigroup.axisFin]

theorem scalarRateRat_eq_native (center : ℝ) :
    (scalarRateRat : ℝ) = (scalarParameters center).rate := by
  rw [(scalarParameters_exact center).1]
  norm_num [scalarRateRat]

theorem diffusionVarianceRateRat_eq_native (center : ℝ) :
    (diffusionVarianceRateRat : ℝ) = (scalarParameters center).diffusionVarianceRate := by
  rw [(scalarParameters_exact center).2]
  norm_num [diffusionVarianceRateRat]

theorem recognitionRat_eq_precision :
    (recognitionCoefficientRat : ℝ) = recognitionCoefficient sensory ∧
      (recognitionCoefficientRat : ℝ) = recognitionCoefficient active ∧
      (recognitionVarianceRat : ℝ) = recognitionVariance := by
  rcases recognition_precision_blocks with ⟨hs, ha, hv⟩
  simp [recognitionCoefficientRat, recognitionVarianceRat, hs, ha, hv]

def ratJson (value : ℚ) : Lean.Json := Lean.Json.mkObj
  [("numerator", toJson value.num), ("denominator", toJson value.den)]

def parameterWitnesses : List String :=
  ["FEP.H3ReferenceModel.precisionRat_eq_native", "FEP.H3ReferenceModel.covarianceRat_eq_native",
   "FEP.H3ReferenceModel.scaleRat_eq_native", "FEP.H3ReferenceModel.offsetRat_eq_native",
   "FEP.H3ReferenceModel.scalarRateRat_eq_native",
   "FEP.H3ReferenceModel.diffusionVarianceRateRat_eq_native",
   "FEP.H3ReferenceModel.recognitionRat_eq_precision",
   "FEP.H3ReferenceModel.settingRat_eq_native",
   "FEP.H3ReferenceModel.modeRat_eq_native",
   "FEP.H3ReferenceModel.modeRateRat_eigenpair",
   "FEP.H3ReferenceModel.modeVector_nonzero",
   "FEP.H3ReferenceModel.modeVector_gram"]

def settingJson (setting : Setting) : Lean.Json := Lean.Json.mkObj
  [("id", toJson (match setting with | .A => "A" | .B => "B")),
   ("center", ratJson (centerRat setting)),
   ("observation_noise_variance", ratJson (observationNoiseRat setting)),
   ("delta", ratJson (sampleDurationRat setting))]

/-- Exact rational JSON, executable by Lean; witness names are validated separately. -/
def parameterExport : Lean.Json := Lean.Json.mkObj
  [("schema_version", toJson (1 : Nat)),
   ("protocol_sha256", toJson frozenProtocolSha256),
   ("axes", toJson (["external", "sensory", "active", "internal"] : List String)),
   ("axis_fin_order", toJson ([0, 1, 2, 3] : List Nat)),
   ("raw_units", toJson (["synthetic_external_unit", "synthetic_sensory_unit",
     "synthetic_active_unit", "synthetic_internal_unit"] : List String)),
   ("settings", toJson ([settingJson .A, settingJson .B] : List Lean.Json)),
   ("precision", Lean.Json.arr ((List.finRange 4).map fun row =>
     Lean.Json.arr (((List.finRange 4).map fun col => ratJson (precisionRat row col)).toArray)).toArray),
   ("covariance", Lean.Json.arr ((List.finRange 4).map fun row =>
     Lean.Json.arr (((List.finRange 4).map fun col => ratJson (covarianceRat row col)).toArray)).toArray),
   ("mode_columns", Lean.Json.arr ((List.finRange 4).map fun row =>
     Lean.Json.arr (((List.finRange 4).map fun col => ratJson (modeRat row col)).toArray)).toArray),
   ("rates", Lean.Json.arr (((List.finRange 4).map fun mode => ratJson (modeRateRat mode)).toArray)),
   ("mode_squared_norms", Lean.Json.arr
     (((List.finRange 4).map fun mode => ratJson (modeSquaredNormRat mode)).toArray)),
   ("scales", Lean.Json.arr (((List.finRange 4).map fun axis => ratJson (scaleRat axis)).toArray)),
   ("offsets", Lean.Json.arr (((List.finRange 4).map fun axis => ratJson (offsetRat axis)).toArray)),
   ("rate", ratJson scalarRateRat), ("diffusion_variance_rate", ratJson diffusionVarianceRateRat),
   ("recognition_coefficients", toJson ([ratJson recognitionCoefficientRat,
     ratJson recognitionCoefficientRat] : List Lean.Json)),
   ("recognition_variance", ratJson recognitionVarianceRat),
   ("recognition_boundary", toJson ("precision_block_algebra_only_native_conditioning_owned_by_composition" : String)),
   ("witnesses", toJson parameterWitnesses)]

end FEP.H3ReferenceModel
