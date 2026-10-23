module
public import FepSketches.gaussian_information_geometry
public import FepSketches.markov_semigroup
public import Mathlib.Analysis.SpecialFunctions.Exp
public import Mathlib.MeasureTheory.Measure.LevyConvergence
public import Mathlib.MeasureTheory.Measure.ProbabilityMeasure
public import Mathlib.Order.Filter.AtTopBot.CountablyGenerated
public import Mathlib.Probability.Distributions.Gaussian.Real
public import Mathlib.Probability.Kernel.Composition.Comp
public import Mathlib.Topology.Instances.NNReal.Lemmas

@[expose] public section

/-!
# Scalar Gaussian Ornstein--Uhlenbeck transition semigroup

This module constructs the mean-reverting scalar Gaussian transition law
directly as a family of native Mathlib kernels.  It proves the Dirac boundary
at time zero, Chapman--Kolmogorov in chronological order, invariance of the
derived stationary Gaussian law, moment formulas, and weak convergence.  It
does not construct or claim an SDE solution, a stochastic process, or a
forward equation.
-/

open Filter MeasureTheory ProbabilityTheory
open scoped BoundedContinuousFunction ENNReal MeasureTheory NNReal ProbabilityTheory Topology

namespace FEP.ScalarGaussianSemigroup

noncomputable section

/-- Raw parameters of the scalar mean-reverting transition.  The diffusion
variance rate is the square of the diffusion-amplitude convention sometimes
written in scientific prose. -/
structure ScalarOUParameters where
  rate : ℝ
  rate_pos : 0 < rate
  center : ℝ
  diffusionVarianceRate : ℝ≥0
  diffusionVarianceRate_pos : 0 < diffusionVarianceRate

namespace ScalarOUParameters

/-- Exponential mean-reversion coefficient at nonnegative time. -/
noncomputable def decay (model : ScalarOUParameters) (time : ℝ≥0) : ℝ :=
  Real.exp (-model.rate * (time : ℝ))

noncomputable def rateDenominator (model : ScalarOUParameters) : ℝ≥0 :=
  ⟨2 * model.rate, mul_nonneg (by norm_num) model.rate_pos.le⟩

/-- Variance of the invariant Gaussian law, derived from the raw variance
rate and mean-reversion rate. -/
noncomputable def stationaryVariance (model : ScalarOUParameters) : ℝ≥0 :=
  model.diffusionVarianceRate / model.rateDenominator

/-- Closed real formula for the invariant variance derived from the raw
diffusion variance rate and positive mean-reversion rate. -/
theorem stationaryVariance_eq (model : ScalarOUParameters) :
    (model.stationaryVariance : ℝ) =
      (model.diffusionVarianceRate : ℝ) / (2 * model.rate) := by
  rw [stationaryVariance, NNReal.coe_div]
  rfl

/-- Conditional transition mean from `state` at `time`. -/
noncomputable def transitionMean
    (model : ScalarOUParameters) (time : ℝ≥0) (state : ℝ) : ℝ :=
  model.center + model.decay time * (state - model.center)

private theorem decay_pos (model : ScalarOUParameters) (time : ℝ≥0) :
    0 < model.decay time := by
  exact Real.exp_pos _

private theorem decay_le_one (model : ScalarOUParameters) (time : ℝ≥0) :
    model.decay time ≤ 1 := by
  rw [decay, Real.exp_le_one_iff]
  exact mul_nonpos_of_nonpos_of_nonneg
    (neg_nonpos.mpr model.rate_pos.le) time.2

private theorem decay_lt_one
    (model : ScalarOUParameters) (time : ℝ≥0) (hTime : 0 < time) :
    model.decay time < 1 := by
  rw [decay, Real.exp_lt_one_iff]
  have hTimeReal : 0 < (time : ℝ) := by exact_mod_cast hTime
  exact mul_neg_of_neg_of_pos (neg_lt_zero.mpr model.rate_pos) hTimeReal

theorem stationaryVariance_pos (model : ScalarOUParameters) :
    0 < model.stationaryVariance := by
  exact div_pos model.diffusionVarianceRate_pos (by
    change 0 < model.rateDenominator
    exact_mod_cast mul_pos (by norm_num : (0 : ℝ) < 2) model.rate_pos)

/-- Conditional transition variance. -/
noncomputable def transitionVariance
    (model : ScalarOUParameters) (time : ℝ≥0) : ℝ≥0 :=
  ⟨(model.stationaryVariance : ℝ) * (1 - model.decay time ^ 2),
    mul_nonneg model.stationaryVariance.2
      (sub_nonneg.mpr (by
        nlinarith [model.decay_pos time, model.decay_le_one time]))⟩

/-- The positive-time transition as an H2.1 fixed-variance Gaussian family. -/
noncomputable def positiveTimeGaussian
    (model : ScalarOUParameters) (time : ℝ≥0) (hTime : 0 < time) :
    FEP.GaussianInformationGeometry.FixedVarianceGaussian where
  variance := model.transitionVariance time
  variance_pos := by
    change 0 < (model.stationaryVariance : ℝ) * (1 - model.decay time ^ 2)
    have hDecaySquare : model.decay time ^ 2 < 1 := by
      nlinarith [model.decay_pos time, model.decay_lt_one time hTime]
    exact mul_pos (by exact_mod_cast model.stationaryVariance_pos) (sub_pos.mpr hDecaySquare)

/-- Native scalar Gaussian transition kernel.  At time zero Mathlib's
zero-variance Gaussian is definitionally the required Dirac branch. -/
noncomputable def ouTransition
    (model : ScalarOUParameters) (time : ℝ≥0) : Kernel ℝ ℝ where
  toFun state :=
    gaussianReal (model.transitionMean time state) (model.transitionVariance time)
  measurable' := by
    have hParameters : Measurable
        (fun state : ℝ =>
          (model.transitionMean time state, model.transitionVariance time)) := by
      apply Measurable.prodMk
      · unfold transitionMean
        fun_prop
      · exact measurable_const
    change Measurable
      (Function.uncurry gaussianReal ∘
        fun state : ℝ =>
          (model.transitionMean time state, model.transitionVariance time))
    exact measurable_gaussianReal.comp hParameters

noncomputable instance ouTransition_isMarkovKernel
    (model : ScalarOUParameters) (time : ℝ≥0) :
    IsMarkovKernel (model.ouTransition time) :=
  ⟨fun state => by
    simpa [ouTransition] using
      (inferInstance : IsProbabilityMeasure
        (gaussianReal (model.transitionMean time state)
          (model.transitionVariance time)))⟩

private theorem decay_zero (model : ScalarOUParameters) : model.decay 0 = 1 := by
  simp [decay]

private theorem decay_add (model : ScalarOUParameters) (left right : ℝ≥0) :
    model.decay (left + right) = model.decay left * model.decay right := by
  rw [decay, decay, decay, NNReal.coe_add, ← Real.exp_add]
  congr 1
  ring

/-- The transition mean at time zero is the input state. -/
theorem transitionMean_zero (model : ScalarOUParameters) (state : ℝ) :
    model.transitionMean 0 state = state := by
  simp [transitionMean, model.decay_zero]

/-- The time-zero transition variance is exactly zero. -/
theorem transitionVariance_zero (model : ScalarOUParameters) :
    model.transitionVariance 0 = 0 := by
  apply NNReal.eq
  change (model.stationaryVariance : ℝ) * (1 - model.decay 0 ^ 2) = 0
  rw [model.decay_zero]
  ring

/-- Every strictly positive time has a nondegenerate Gaussian variance. -/
theorem transitionVariance_pos
    (model : ScalarOUParameters) (time : ℝ≥0) (hTime : 0 < time) :
    0 < model.transitionVariance time := by
  exact (model.positiveTimeGaussian time hTime).variance_pos

/-- Every row of every time slice is normalized. -/
theorem ouTransition_univ
    (model : ScalarOUParameters) (time : ℝ≥0) (state : ℝ) :
    model.ouTransition time state Set.univ = 1 := by
  change
    gaussianReal (model.transitionMean time state)
        (model.transitionVariance time) Set.univ = 1
  simp

/-- The zero-time transition is the native identity kernel. -/
theorem ouTransition_zero (model : ScalarOUParameters) :
    model.ouTransition 0 = Kernel.id := by
  apply DFunLike.ext _ _
  intro state
  change
    gaussianReal (model.transitionMean 0 state)
        (model.transitionVariance 0) = Measure.dirac state
  rw [model.transitionMean_zero, model.transitionVariance_zero,
    gaussianReal_zero_var]

private theorem transitionMean_affine
    (model : ScalarOUParameters) (time : ℝ≥0) (state : ℝ) :
    model.transitionMean time state =
      model.decay time * state + model.center * (1 - model.decay time) := by
  rw [transitionMean]
  ring

private theorem transitionMean_add
    (model : ScalarOUParameters) (left right : ℝ≥0) (state : ℝ) :
    model.transitionMean (left + right) state =
      model.transitionMean right (model.transitionMean left state) := by
  rw [transitionMean, transitionMean, transitionMean, model.decay_add]
  ring

private theorem transitionVariance_add
    (model : ScalarOUParameters) (left right : ℝ≥0) :
    model.transitionVariance (left + right) =
      NNReal.mk (model.decay right ^ 2) (sq_nonneg _) *
          model.transitionVariance left +
        model.transitionVariance right := by
  apply NNReal.eq
  change
    (model.stationaryVariance : ℝ) *
        (1 - model.decay (left + right) ^ 2) =
      model.decay right ^ 2 *
          ((model.stationaryVariance : ℝ) *
            (1 - model.decay left ^ 2)) +
        (model.stationaryVariance : ℝ) * (1 - model.decay right ^ 2)
  rw [model.decay_add]
  ring

private theorem gaussian_bind_affine
    (sourceMean coefficient shift : ℝ)
    (sourceVariance noiseVariance : ℝ≥0) :
    (gaussianReal sourceMean sourceVariance).bind
        (fun state => gaussianReal (coefficient * state + shift) noiseVariance) =
      gaussianReal
        (coefficient * sourceMean + shift)
        (NNReal.mk (coefficient ^ 2) (sq_nonneg _) * sourceVariance +
          noiseVariance) := by
  calc
    (gaussianReal sourceMean sourceVariance).bind
        (fun state => gaussianReal (coefficient * state + shift) noiseVariance) =
        ((gaussianReal sourceMean sourceVariance).map
            (fun state => coefficient * state + shift)) ∗
          gaussianReal 0 noiseVariance := by
      refine Measure.ext_of_lintegral _ fun f hMeasurable => ?_
      rw [Measure.lintegral_bind (by fun_prop) (by fun_prop),
        Measure.lintegral_conv hMeasurable,
        lintegral_map (by fun_prop) (by fun_prop)]
      congr with state
      have hTranslated :
          (gaussianReal 0 noiseVariance).map
              (fun noise => coefficient * state + shift + noise) =
            gaussianReal (coefficient * state + shift) noiseVariance := by
        simpa using gaussianReal_map_const_add
          (μ := 0) (v := noiseVariance) (coefficient * state + shift)
      rw [← hTranslated, lintegral_map hMeasurable (by fun_prop)]
    _ = gaussianReal
        (coefficient * sourceMean + shift)
        (NNReal.mk (coefficient ^ 2) (sq_nonneg _) * sourceVariance +
          noiseVariance) := by
      rw [show (fun state : ℝ => coefficient * state + shift) =
          (fun state => state + shift) ∘ (fun state => coefficient * state) by rfl,
        ← Measure.map_map (by fun_prop) (by fun_prop),
        gaussianReal_map_const_mul, gaussianReal_map_add_const,
        gaussianReal_conv_gaussianReal]
      simp

/-- Chapman--Kolmogorov with the later slice composed on the left. -/
theorem ouTransition_add
    (model : ScalarOUParameters) (left right : ℝ≥0) :
    model.ouTransition (left + right) =
      model.ouTransition right ∘ₖ model.ouTransition left := by
  apply DFunLike.ext _ _
  intro state
  rw [Kernel.comp_apply]
  change
    gaussianReal
        (model.transitionMean (left + right) state)
        (model.transitionVariance (left + right)) =
      (gaussianReal
        (model.transitionMean left state)
        (model.transitionVariance left)).bind
        (fun next =>
          gaussianReal
            (model.transitionMean right next)
            (model.transitionVariance right))
  simp_rw [model.transitionMean_affine right]
  rw [gaussian_bind_affine]
  apply gaussianReal_ext_iff.mpr
  exact ⟨(model.transitionMean_add left right state).trans
      (model.transitionMean_affine right (model.transitionMean left state)),
    model.transitionVariance_add left right⟩

/-- Evolving an arbitrary scalar Gaussian through the OU slice stays Gaussian. -/
theorem ouTransition_comp_gaussian
    (model : ScalarOUParameters) (time : ℝ≥0)
    (sourceMean : ℝ) (sourceVariance : ℝ≥0) :
    model.ouTransition time ∘ₘ gaussianReal sourceMean sourceVariance =
      gaussianReal
        (model.transitionMean time sourceMean)
        (NNReal.mk (model.decay time ^ 2) (sq_nonneg _) * sourceVariance +
          model.transitionVariance time) := by
  change
    (gaussianReal sourceMean sourceVariance).bind
        (fun state =>
          gaussianReal (model.transitionMean time state)
            (model.transitionVariance time)) = _
  simp_rw [model.transitionMean_affine time]
  rw [gaussian_bind_affine]

/-- H2.4 native-semigroup packaging of the exact transition family. -/
noncomputable def ouNativeSemigroup (model : ScalarOUParameters) :
    FEP.MarkovSemigroup.NativeKernelSemigroup model.ouTransition where
  kernel_zero := model.ouTransition_zero
  kernel_add := model.ouTransition_add

/-- At positive time the transition is exactly an H2.1 Gaussian location law. -/
theorem ouTransition_eq_gaussianLocation
    (model : ScalarOUParameters) (time : ℝ≥0) (hTime : 0 < time)
    (state : ℝ) :
    model.ouTransition time state =
      (model.positiveTimeGaussian time hTime).law
        (model.transitionMean time state) := by
  change gaussianReal _ _ = gaussianReal _ _
  rfl

/-- H2.1 family owning the invariant scalar Gaussian law. -/
noncomputable def stationaryGaussian (model : ScalarOUParameters) :
    FEP.GaussianInformationGeometry.FixedVarianceGaussian where
  variance := model.stationaryVariance
  variance_pos := model.stationaryVariance_pos

/-- Invariant scalar Gaussian law. -/
noncomputable def stationaryLaw (model : ScalarOUParameters) : Measure ℝ :=
  (model.stationaryGaussian).law model.center

noncomputable instance stationaryLaw_isProbabilityMeasure
    (model : ScalarOUParameters) : IsProbabilityMeasure model.stationaryLaw := by
  change IsProbabilityMeasure
    (gaussianReal model.center model.stationaryVariance)
  infer_instance

private theorem stationaryVariance_decomposition
    (model : ScalarOUParameters) (time : ℝ≥0) :
    NNReal.mk (model.decay time ^ 2) (sq_nonneg _) *
          model.stationaryVariance +
        model.transitionVariance time =
      model.stationaryVariance := by
  apply NNReal.eq
  change
    model.decay time ^ 2 * (model.stationaryVariance : ℝ) +
        (model.stationaryVariance : ℝ) * (1 - model.decay time ^ 2) =
      model.stationaryVariance
  ring

/-- The stationary Gaussian is invariant under every time slice. -/
theorem stationaryLaw_invariant (model : ScalarOUParameters) :
    FEP.MarkovSemigroup.InvariantLaw
      model.ouNativeSemigroup model.stationaryLaw := by
  intro time
  rw [Kernel.Invariant]
  change model.ouTransition time ∘ₘ gaussianReal model.center model.stationaryVariance =
    gaussianReal model.center model.stationaryVariance
  rw [model.ouTransition_comp_gaussian, model.stationaryVariance_decomposition]
  simp [transitionMean]

/-- The transition mean is its declared Gaussian mean parameter. -/
theorem ouTransition_mean
    (model : ScalarOUParameters) (time : ℝ≥0) (state : ℝ) :
    (∫ next, next ∂model.ouTransition time state) =
      model.transitionMean time state := by
  change
    (∫ next, next ∂gaussianReal
      (model.transitionMean time state) (model.transitionVariance time)) =
      model.transitionMean time state
  exact integral_id_gaussianReal

/-- The transition variance is its declared Gaussian variance parameter. -/
theorem ouTransition_variance
    (model : ScalarOUParameters) (time : ℝ≥0) (state : ℝ) :
    Var[id; model.ouTransition time state] = model.transitionVariance time := by
  change
    Var[id; gaussianReal
      (model.transitionMean time state) (model.transitionVariance time)] =
      model.transitionVariance time
  exact variance_id_gaussianReal

/-- Probability-measure view of one transition row. -/
noncomputable def ouTransitionProbability
    (model : ScalarOUParameters) (time : ℝ≥0) (state : ℝ) :
    ProbabilityMeasure ℝ :=
  ⟨model.ouTransition time state, inferInstance⟩

/-- Probability-measure view of the invariant law. -/
noncomputable def stationaryProbability (model : ScalarOUParameters) :
    ProbabilityMeasure ℝ :=
  ⟨model.stationaryLaw, inferInstance⟩

private theorem decay_tendsto_zero (model : ScalarOUParameters) :
    Tendsto model.decay atTop (𝓝 0) := by
  have hTime : Tendsto (fun time : ℝ≥0 => (time : ℝ)) atTop atTop :=
    NNReal.tendsto_coe_atTop.mpr tendsto_id
  have hExponent :
      Tendsto (fun time : ℝ≥0 => -model.rate * (time : ℝ)) atTop atBot :=
    (tendsto_const_mul_atBot_of_neg
      (neg_lt_zero.mpr model.rate_pos)).mpr hTime
  change
    Tendsto (fun time : ℝ≥0 => Real.exp (-model.rate * (time : ℝ)))
      atTop (𝓝 0)
  exact Real.tendsto_exp_atBot.comp hExponent

private theorem transitionMean_tendsto_center
    (model : ScalarOUParameters) (state : ℝ) :
    Tendsto (fun time : ℝ≥0 => model.transitionMean time state)
      atTop (𝓝 model.center) := by
  simpa only [transitionMean, zero_mul, add_zero] using
    tendsto_const_nhds.add
      (model.decay_tendsto_zero.mul_const (state - model.center))

private theorem transitionVariance_tendsto_stationary
    (model : ScalarOUParameters) :
    Tendsto model.transitionVariance atTop (𝓝 model.stationaryVariance) := by
  apply NNReal.tendsto_coe.mp
  change
    Tendsto
      (fun time : ℝ≥0 =>
        (model.stationaryVariance : ℝ) * (1 - model.decay time ^ 2))
      atTop (𝓝 (model.stationaryVariance : ℝ))
  have hOne :
      Tendsto (fun _ : ℝ≥0 => (1 : ℝ)) atTop (𝓝 1) :=
    tendsto_const_nhds
  have hStationary :
      Tendsto (fun _ : ℝ≥0 => (model.stationaryVariance : ℝ))
        atTop (𝓝 (model.stationaryVariance : ℝ)) :=
    tendsto_const_nhds
  convert hStationary.mul
      (hOne.sub (model.decay_tendsto_zero.pow 2)) using 1
  all_goals norm_num

private theorem gaussianReal_charFun_tendsto
    {means : ℕ → ℝ} {variances : ℕ → ℝ≥0}
    {limitMean : ℝ} {limitVariance : ℝ≥0}
    (hMean : Tendsto means atTop (𝓝 limitMean))
    (hVariance : Tendsto variances atTop (𝓝 limitVariance))
    (frequency : ℝ) :
    Tendsto
      (fun index => charFun (gaussianReal (means index) (variances index)) frequency)
      atTop
      (𝓝 (charFun (gaussianReal limitMean limitVariance) frequency)) := by
  have hMeanComplex :
      Tendsto (fun index => (means index : ℂ)) atTop (𝓝 (limitMean : ℂ)) :=
    Filter.tendsto_ofReal_iff.mpr hMean
  have hVarianceReal :
      Tendsto (fun index => (variances index : ℝ))
        atTop (𝓝 (limitVariance : ℝ)) :=
    NNReal.tendsto_coe.mpr hVariance
  have hVarianceComplex :
      Tendsto (fun index => ((variances index : ℝ) : ℂ))
        atTop (𝓝 ((limitVariance : ℝ) : ℂ)) :=
    Filter.tendsto_ofReal_iff.mpr hVarianceReal
  have hMeanTerm :
      Tendsto
        (fun index => (frequency : ℂ) * means index * Complex.I)
        atTop (𝓝 ((frequency : ℂ) * limitMean * Complex.I)) :=
    (tendsto_const_nhds.mul hMeanComplex).mul_const Complex.I
  have hVarianceTerm :
      Tendsto
        (fun index =>
          ((variances index : ℝ) : ℂ) * (frequency : ℂ) ^ 2 / 2)
        atTop
        (𝓝 (((limitVariance : ℝ) : ℂ) * (frequency : ℂ) ^ 2 / 2)) :=
    (hVarianceComplex.mul_const ((frequency : ℂ) ^ 2)).div_const 2
  simpa only [charFun_gaussianReal] using
    (hMeanTerm.sub hVarianceTerm).cexp

/-- The full nonnegative-time transition law converges weakly from every
fixed state to the invariant Gaussian law. -/
theorem ouTransitionProbability_tendsto_invariant
    (model : ScalarOUParameters) (state : ℝ) :
    Tendsto
      (fun time : ℝ≥0 => model.ouTransitionProbability time state)
      atTop (𝓝 model.stationaryProbability) := by
  apply Filter.tendsto_of_seq_tendsto
  intro times hTimes
  rw [ProbabilityMeasure.tendsto_iff_tendsto_charFun]
  intro frequency
  change
    Tendsto
      (fun index =>
        charFun
          (gaussianReal
            (model.transitionMean (times index) state)
            (model.transitionVariance (times index))) frequency)
      atTop
      (𝓝 (charFun
        (gaussianReal model.center model.stationaryVariance) frequency))
  apply gaussianReal_charFun_tendsto
  · exact model.transitionMean_tendsto_center state |>.comp hTimes
  · exact model.transitionVariance_tendsto_stationary.comp hTimes

/-- Weak convergence transfers to exactly the bounded continuous real
observables supported by the topology on probability measures. -/
theorem integral_ouTransition_tendsto_invariant
    (model : ScalarOUParameters) (state : ℝ) (f : ℝ →ᵇ ℝ) :
    Tendsto
      (fun time : ℝ≥0 =>
        ∫ next, f next ∂(model.ouTransitionProbability time state : Measure ℝ))
      atTop
      (𝓝 (∫ next, f next ∂(model.stationaryProbability : Measure ℝ))) := by
  exact
    (ProbabilityMeasure.tendsto_iff_forall_integral_tendsto.mp
      (model.ouTransitionProbability_tendsto_invariant state)) f

/-- Native KL to the invariant Gaussian law is nonincreasing between any
earlier time and a later increment. -/
theorem ouKL_to_stationary_nonincrease
    (model : ScalarOUParameters) (earlier increment : ℝ≥0)
    (actual : Measure ℝ) [IsFiniteMeasure actual] :
    InformationTheory.klDiv
        (model.ouTransition (earlier + increment) ∘ₘ actual)
        model.stationaryLaw ≤
      InformationTheory.klDiv
        (model.ouTransition earlier ∘ₘ actual)
        model.stationaryLaw := by
  exact
    FEP.MarkovSemigroup.NativeKernelSemigroup.nativeKL_to_invariant_nonincrease
      model.ouNativeSemigroup earlier increment actual model.stationaryLaw
      model.stationaryLaw_invariant

end ScalarOUParameters

end

end FEP.ScalarGaussianSemigroup
