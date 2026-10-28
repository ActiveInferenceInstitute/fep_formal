module
public import FepSketches.gaussian_information_geometry
public import FepSketches.smooth_information_geometry
public import FepSketches.posterior_convergence
public import FepSketches.markov_semigroup
public import FepSketches.scalar_gaussian_semigroup
public import FepSketches.fin4_gaussian_semigroup
public import FepSketches.gaussian_precision_conditioning
public import FepSketches.compositions.gaussian_filter
public import FepSketches.compositions.gaussian_control
public import FepSketches.compositions.gaussian_grid_path

@[expose] public section

/-!
# Horizon 2 smooth reference kernel

This terminal leaf connects one selected scalar Gaussian carrier across
location-family geometry, static-parameter observations, OU prediction,
native filtering, one-step finite control, and finite-grid paths.  A separate
export verifies the accepted `Fin 4` carrier and native blanket conditioning.

The scalar theorem does not identify static-parameter learning with latent-
state filtering: it proves that both use the same named Gaussian observation
rows and keeps their posterior carriers distinct.  It makes no EFE/reward,
SDE/Itô, Fokker--Planck, Girsanov, physical-dissipation, causal-blanket,
empirical, or universal-FEP claim.  It does not extend to singular covariance,
arbitrary recognition families, global statistical geometry, nonparametric
learning rates, continuous-path densities or entropy production, or convergence
of unbounded observables.  Natural-gradient descent is a time-zero directional
derivative with fixed posterior variance, not a global flow or ODE result.
Native posterior agreement is evidence-almost-everywhere, not a claim about the
native posterior at the singleton datum zero.  Fin4 remains a separate carrier.
-/

open Filter MeasureTheory ProbabilityTheory InformationTheory
open scoped BoundedContinuousFunction ENNReal MeasureTheory NNReal ProbabilityTheory Topology

namespace FEPComposed.SmoothReferenceKernel

open FEP.GaussianInformationGeometry
open FEP.GaussianPrecisionConditioning
open FEP.MarkovSemigroup
open FEP.PosteriorConvergence
open FEP.ScalarGaussianSemigroup
open FEP.SmoothInformationGeometry
open FEP.Fin4GaussianSemigroup
open FEPComposed.GaussianControl
open FEPComposed.GaussianFilter
open FEPComposed.GaussianGridPath

noncomputable section

/-! ## One selected scalar carrier -/

/-- The base mean-reverting dynamics.  Its invariant variance is exactly one,
matching the H2.3 selected Gaussian observation family. -/
noncomputable def selectedDynamics : ScalarOUParameters where
  rate := 1
  rate_pos := by norm_num
  center := 0
  diffusionVarianceRate := 2
  diffusionVarianceRate_pos := by norm_num

/-- A higher-diffusion alternative used only for the finite one-step action
comparison on the same real state carrier. -/
noncomputable def alternativeDynamics : ScalarOUParameters where
  rate := 1
  rate_pos := by norm_num
  center := 0
  diffusionVarianceRate := 4
  diffusionVarianceRate_pos := by norm_num

/-- The invariant unit-variance base Gaussian, reused as the filter prior. -/
noncomputable def selectedPrior : ScalarGaussianBelief where
  mean := 0
  family := selectedGaussianFamily

/-- One unit-duration filter whose observation noise is exactly H2.3's
selected unit-variance Gaussian family. -/
noncomputable def selectedFilter : ScalarGaussianFilterModel where
  dynamics := selectedDynamics
  stepDuration := 1
  observationNoise := selectedGaussianFamily

/-- Boolean control on the same real state: `false` retains the base OU and
`true` selects only the higher diffusion rate. -/
noncomputable def selectedControl : FiniteGaussianControlModel Bool where
  dynamics := fun action =>
    if action then alternativeDynamics else selectedDynamics
  duration := 1
  duration_pos := by norm_num
  target := 0
  actionPenalty := fun _ => 0

/-- Unit-spaced nondecreasing grid for the accepted finite path constructor. -/
noncomputable def selectedUnitGrid : TimeGrid where
  time := fun n => n
  monotone_time := by
    intro left right h
    change (left : ℝ) ≤ (right : ℝ)
    exact_mod_cast h

/-- The base OU has invariant variance one. -/
theorem selectedDynamics_stationaryVariance :
    selectedDynamics.stationaryVariance = 1 := by
  apply NNReal.eq
  rw [selectedDynamics.stationaryVariance_eq]
  norm_num [selectedDynamics]

/-- The base invariant law is exactly the false-row H2.3 observation law. -/
theorem selectedStationaryLaw_eq_learningObservationFalse :
    selectedDynamics.stationaryLaw = selectedObservationLaw false := by
  change gaussianReal selectedDynamics.center selectedDynamics.stationaryVariance =
    gaussianReal (selectedMean false) selectedGaussianFamily.variance
  rw [selectedDynamics_stationaryVariance]
  norm_num [selectedDynamics, selectedMean, selectedGaussianFamily]

/-- Every positive unit-time transition row is the accepted H2.1 Gaussian
location family owned by the selected dynamics. -/
theorem selectedTransition_eq_gaussianLocation (state : ℝ) :
    selectedDynamics.ouTransition 1 state =
      (selectedDynamics.positiveTimeGaussian 1 (by norm_num)).law
        (selectedDynamics.transitionMean 1 state) := by
  exact selectedDynamics.ouTransition_eq_gaussianLocation 1 (by norm_num) state

/-- At each selected H2.3 mean, the filter observation row is exactly the
static-parameter learning observation law. -/
theorem selectedObservationKernel_eq_learningObservationLaw
    (hypothesis : MeanHypothesis) :
    observationKernel selectedFilter (selectedMean hypothesis) =
      selectedObservationLaw hypothesis := by
  change selectedGaussianFamily.law (selectedMean hypothesis) =
    selectedGaussianFamily.law (selectedMean hypothesis)
  rfl

/-- One base prediction preserves the exact selected prior parameters. -/
theorem selectedPredictionBelief_eq_prior :
    predictionBelief selectedFilter selectedPrior = selectedPrior := by
  unfold predictionBelief selectedPrior
  congr 1
  · norm_num [predictionBelief, selectedFilter, selectedPrior,
      selectedDynamics, ScalarOUParameters.transitionMean,
      ScalarOUParameters.decay]
  · congr 1
    apply NNReal.eq
    unfold predictionVariance ScalarOUParameters.transitionVariance
    change
      selectedDynamics.decay 1 ^ 2 * 1 +
          (selectedDynamics.stationaryVariance : ℝ) *
            (1 - selectedDynamics.decay 1 ^ 2) = 1
    rw [selectedDynamics.stationaryVariance_eq]
    norm_num [selectedDynamics, ScalarOUParameters.decay]

/-- The selected zero datum leaves the exact posterior centered. -/
theorem selectedPosterior_mean :
    posteriorMean selectedFilter selectedPrior 0 = 0 := by
  change
    (predictionBelief selectedFilter selectedPrior).mean +
        gain selectedFilter selectedPrior *
          (0 - (predictionBelief selectedFilter selectedPrior).mean) = 0
  rw [selectedPredictionBelief_eq_prior]
  norm_num [selectedPrior]

/-- The selected zero-datum posterior variance is exactly one half. -/
theorem selectedPosterior_variance :
    posteriorVariance selectedFilter selectedPrior = 1 / 2 := by
  change
    (predictionBelief selectedFilter selectedPrior).family.variance *
          selectedFilter.observationNoise.variance /
        ((predictionBelief selectedFilter selectedPrior).family.variance +
          selectedFilter.observationNoise.variance) = 1 / 2
  rw [selectedPredictionBelief_eq_prior]
  norm_num [selectedPrior, selectedFilter, selectedGaussianFamily]

/-! ## Maintained continuous Gaussian VFE and local natural gradient -/

/-- Evidence surprisal relative to the actual evidence law's Lebesgue density. -/
noncomputable def evidenceSurprisal
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation : ℝ) : ℝ :=
  -Real.log (evidenceDensity model prior observation).toReal

/-- Continuous VFE on fixed-posterior-variance recognition laws.  Native KL
is oriented recognition-to-posterior. -/
noncomputable def gaussianVariationalFreeEnergy
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation recognitionMean : ℝ) : ℝ :=
  (klDiv
      ((posteriorFamily model prior).law recognitionMean)
      ((posteriorBelief model prior observation).law)).toReal +
    evidenceSurprisal model prior observation

/-- Fisher-inverse image of the VFE mean differential. -/
noncomputable def meanNaturalGradient
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation recognitionMean : ℝ) : ℝ :=
  ((posteriorFamily model prior).meanFisher recognitionMean)⁻¹ *
    ((recognitionMean - posteriorMean model prior observation) /
      (posteriorVariance model prior : ℝ))

/-- The local negative-natural-gradient line through one recognition mean. -/
noncomputable def naturalGradientFlow
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation recognitionMean time : ℝ) : ℝ :=
  recognitionMean - time *
    meanNaturalGradient model prior observation recognitionMean

/-- The actual evidence law is Lebesgue measure weighted by its named density. -/
theorem evidenceLaw_eq_volume_withDensity
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief) :
    evidenceLaw model prior = volume.withDensity (evidenceDensity model prior) := by
  rw [evidenceLaw_eq_gaussian]
  exact
    (evidenceFamily model prior).law_eq_withDensity
      (predictionBelief model prior).mean

/-- The selected Gaussian evidence density is finite at every datum. -/
theorem evidenceDensity_ne_top
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation : ℝ) :
    evidenceDensity model prior observation ≠ ⊤ := by
  exact gaussianPDF_ne_top

/-- VFE is the exact Gaussian KL gap plus density-relative surprisal. -/
theorem gaussianVariationalFreeEnergy_eq_meanSquare_add_surprisal
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation recognitionMean : ℝ) :
    gaussianVariationalFreeEnergy model prior observation recognitionMean =
      (recognitionMean - posteriorMean model prior observation) ^ 2 /
          (2 * (posteriorVariance model prior : ℝ)) +
        evidenceSurprisal model prior observation := by
  unfold gaussianVariationalFreeEnergy
  change
    (klDiv
      ((posteriorFamily model prior).law recognitionMean)
      ((posteriorFamily model prior).law
        (posteriorMean model prior observation))).toReal + _ = _
  have hvariance : 0 < (posteriorVariance model prior : ℝ) := by
    exact_mod_cast posteriorVariance_pos model prior
  have hnonneg :
      0 ≤ (recognitionMean - posteriorMean model prior observation) ^ 2 /
        (2 * (posteriorVariance model prior : ℝ)) := by
    exact div_nonneg (sq_nonneg _) (mul_nonneg (by norm_num) hvariance.le)
  rw [(posteriorFamily model prior).klDiv_law_eq_meanSquare]
  change
    (ENNReal.ofReal
      ((recognitionMean - posteriorMean model prior observation) ^ 2 /
        (2 * (posteriorVariance model prior : ℝ)))).toReal + _ = _
  rw [ENNReal.toReal_ofReal hnonneg]

/-- Subtracting evidence surprisal leaves the oriented native KL. -/
theorem gaussianVariationalFreeEnergy_sub_surprisal_eq_nativeKL
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation recognitionMean : ℝ) :
    gaussianVariationalFreeEnergy model prior observation recognitionMean -
        evidenceSurprisal model prior observation =
      (klDiv
        ((posteriorFamily model prior).law recognitionMean)
        ((posteriorBelief model prior observation).law)).toReal := by
  unfold gaussianVariationalFreeEnergy
  ring

/-- The exact posterior is the unique optimum in the fixed-variance
recognition family. -/
theorem gaussianVariationalFreeEnergy_eq_surprisal_iff
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation recognitionMean : ℝ) :
    gaussianVariationalFreeEnergy model prior observation recognitionMean =
        evidenceSurprisal model prior observation ↔
      recognitionMean = posteriorMean model prior observation := by
  rw [gaussianVariationalFreeEnergy_eq_meanSquare_add_surprisal]
  have hvariance : 0 < (posteriorVariance model prior : ℝ) := by
    exact_mod_cast posteriorVariance_pos model prior
  constructor
  · intro h
    have hgap :
        (recognitionMean - posteriorMean model prior observation) ^ 2 /
            (2 * (posteriorVariance model prior : ℝ)) = 0 := by
      linarith
    field_simp [hvariance.ne'] at hgap
    nlinarith
  · intro h
    simp [h]

/-- The VFE differential is the posterior-precision-weighted mean error. -/
theorem gaussianVariationalFreeEnergy_hasDerivAt
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation recognitionMean : ℝ) :
    HasDerivAt
      (gaussianVariationalFreeEnergy model prior observation)
      ((recognitionMean - posteriorMean model prior observation) /
        (posteriorVariance model prior : ℝ))
      recognitionMean := by
  have hfun :
      gaussianVariationalFreeEnergy model prior observation =
        fun candidate =>
          (candidate - posteriorMean model prior observation) ^ 2 /
              (2 * (posteriorVariance model prior : ℝ)) +
            evidenceSurprisal model prior observation := by
    funext candidate
    exact
      gaussianVariationalFreeEnergy_eq_meanSquare_add_surprisal
        model prior observation candidate
  rw [hfun]
  have hraw :=
    ((((hasDerivAt_id recognitionMean).sub_const
          (posteriorMean model prior observation)).pow 2).div_const
        (2 * (posteriorVariance model prior : ℝ))).add_const
      (evidenceSurprisal model prior observation)
  have hvariance : (posteriorVariance model prior : ℝ) ≠ 0 := by
    exact_mod_cast (posteriorVariance_pos model prior).ne'
  have hderiv :
      (2 : ℝ) *
            (recognitionMean - posteriorMean model prior observation) /
          (2 * (posteriorVariance model prior : ℝ)) =
        (recognitionMean - posteriorMean model prior observation) /
          (posteriorVariance model prior : ℝ) := by
    rw [mul_div_mul_left _ _ (by norm_num : (2 : ℝ) ≠ 0)]
  simpa only [Pi.pow_apply, id_eq, Nat.cast_ofNat, Nat.reduceSub, pow_one,
    mul_one, hderiv] using hraw

/-- Fisher inversion reduces the natural gradient to posterior displacement. -/
theorem meanNaturalGradient_eq_displacement
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation recognitionMean : ℝ) :
    meanNaturalGradient model prior observation recognitionMean =
      recognitionMean - posteriorMean model prior observation := by
  rw [meanNaturalGradient,
    (posteriorFamily model prior).meanFisher_eq_inv_variance]
  change
    ((posteriorVariance model prior : ℝ)⁻¹)⁻¹ *
        ((recognitionMean - posteriorMean model prior observation) /
          (posteriorVariance model prior : ℝ)) = _
  have hvariance : (posteriorVariance model prior : ℝ) ≠ 0 := by
    exact_mod_cast (posteriorVariance_pos model prior).ne'
  field_simp [hvariance]

/-- The derived tangent is metric-dual to the VFE differential. -/
theorem meanNaturalGradient_metric_dual
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation recognitionMean tangent : ℝ) :
    meanMetricPairing (posteriorFamily model prior) recognitionMean
        (meanNaturalGradient model prior observation recognitionMean) tangent =
      ((recognitionMean - posteriorMean model prior observation) /
          (posteriorVariance model prior : ℝ)) * tangent := by
  rw [meanMetricPairing_eq_invVariance,
    meanNaturalGradient_eq_displacement]
  change
    (posteriorVariance model prior : ℝ)⁻¹ *
          (recognitionMean - posteriorMean model prior observation) * tangent =
      ((recognitionMean - posteriorMean model prior observation) /
          (posteriorVariance model prior : ℝ)) * tangent
  ring

/-- The local line starts at the supplied recognition mean. -/
theorem naturalGradientFlow_zero
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation recognitionMean : ℝ) :
    naturalGradientFlow model prior observation recognitionMean 0 =
      recognitionMean := by
  simp [naturalGradientFlow]

/-- The time-zero VFE derivative along the local negative-natural-gradient
line is minus squared mean error over posterior variance. -/
theorem gaussianVariationalFreeEnergy_naturalGradientFlow_hasDerivAt
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation recognitionMean : ℝ) :
    HasDerivAt
      (fun time =>
        gaussianVariationalFreeEnergy model prior observation
          (naturalGradientFlow model prior observation recognitionMean time))
      (-((recognitionMean - posteriorMean model prior observation) ^ 2 /
        (posteriorVariance model prior : ℝ)))
      0 := by
  have hfun :
      (fun time =>
        gaussianVariationalFreeEnergy model prior observation
          (naturalGradientFlow model prior observation recognitionMean time)) =
        fun time =>
          (recognitionMean -
                time * (recognitionMean - posteriorMean model prior observation) -
              posteriorMean model prior observation) ^ 2 /
              (2 * (posteriorVariance model prior : ℝ)) +
            evidenceSurprisal model prior observation := by
    funext time
    rw [gaussianVariationalFreeEnergy_eq_meanSquare_add_surprisal]
    rw [naturalGradientFlow, meanNaturalGradient_eq_displacement]
  rw [hfun]
  have hinner :
      HasDerivAt
        (fun time : ℝ =>
          recognitionMean -
              time * (recognitionMean - posteriorMean model prior observation) -
            posteriorMean model prior observation)
        (-(recognitionMean - posteriorMean model prior observation)) 0 := by
    simpa only [Pi.sub_apply, Pi.mul_apply, id_eq, one_mul, zero_sub] using
      ((hasDerivAt_const (x := (0 : ℝ)) recognitionMean).sub
        ((hasDerivAt_id (0 : ℝ)).mul_const
          (recognitionMean - posteriorMean model prior observation))).sub_const
            (posteriorMean model prior observation)
  have hraw :=
    ((hinner.pow 2).div_const
      (2 * (posteriorVariance model prior : ℝ))).add_const
        (evidenceSurprisal model prior observation)
  have hvariance : (posteriorVariance model prior : ℝ) ≠ 0 := by
    exact_mod_cast (posteriorVariance_pos model prior).ne'
  have hderiv :
      (2 : ℝ) *
            (recognitionMean -
                0 * (recognitionMean - posteriorMean model prior observation) -
              posteriorMean model prior observation) ^ (2 - 1) *
            (-(recognitionMean - posteriorMean model prior observation)) /
          (2 * (posteriorVariance model prior : ℝ)) =
        -((recognitionMean - posteriorMean model prior observation) ^ 2 /
          (posteriorVariance model prior : ℝ)) := by
    field_simp [hvariance]
    ring
  simpa only [Pi.pow_apply, Nat.cast_ofNat, hderiv] using hraw

/-- Away from the exact posterior mean, local VFE descent is strict. -/
theorem gaussianVariationalFreeEnergy_naturalGradientFlow_deriv_neg
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation recognitionMean : ℝ)
    (hRecognition :
      recognitionMean ≠ posteriorMean model prior observation) :
    -((recognitionMean - posteriorMean model prior observation) ^ 2 /
        (posteriorVariance model prior : ℝ)) < 0 := by
  have hvariance : 0 < (posteriorVariance model prior : ℝ) := by
    exact_mod_cast posteriorVariance_pos model prior
  exact neg_neg_of_pos
    (div_pos (sq_pos_of_ne_zero (sub_ne_zero.mpr hRecognition)) hvariance)

/-- Complete maintained continuous-Gaussian bridge, without EFE, physical
energy, or global-flow claims. -/
theorem continuousGaussianVFE_naturalGradient
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation recognitionMean tangent : ℝ)
    (hRecognition :
      recognitionMean ≠ posteriorMean model prior observation) :
    evidenceLaw model prior = volume.withDensity (evidenceDensity model prior) ∧
      0 < evidenceDensity model prior observation ∧
      evidenceDensity model prior observation ≠ ⊤ ∧
      gaussianVariationalFreeEnergy model prior observation recognitionMean -
          evidenceSurprisal model prior observation =
        (klDiv
          ((posteriorFamily model prior).law recognitionMean)
          ((posteriorBelief model prior observation).law)).toReal ∧
      (gaussianVariationalFreeEnergy model prior observation recognitionMean =
          evidenceSurprisal model prior observation ↔
        recognitionMean = posteriorMean model prior observation) ∧
      meanNaturalGradient model prior observation recognitionMean =
        recognitionMean - posteriorMean model prior observation ∧
      meanMetricPairing (posteriorFamily model prior) recognitionMean
          (meanNaturalGradient model prior observation recognitionMean) tangent =
        ((recognitionMean - posteriorMean model prior observation) /
            (posteriorVariance model prior : ℝ)) * tangent ∧
      HasDerivAt
        (fun time =>
          gaussianVariationalFreeEnergy model prior observation
            (naturalGradientFlow model prior observation recognitionMean time))
        (-((recognitionMean - posteriorMean model prior observation) ^ 2 /
          (posteriorVariance model prior : ℝ)))
        0 ∧
      -((recognitionMean - posteriorMean model prior observation) ^ 2 /
          (posteriorVariance model prior : ℝ)) < 0 := by
  exact ⟨
    evidenceLaw_eq_volume_withDensity model prior,
    evidenceDensity_pos model prior observation,
    evidenceDensity_ne_top model prior observation,
    gaussianVariationalFreeEnergy_sub_surprisal_eq_nativeKL
      model prior observation recognitionMean,
    gaussianVariationalFreeEnergy_eq_surprisal_iff
      model prior observation recognitionMean,
    meanNaturalGradient_eq_displacement model prior observation recognitionMean,
    meanNaturalGradient_metric_dual
      model prior observation recognitionMean tangent,
    gaussianVariationalFreeEnergy_naturalGradientFlow_hasDerivAt
      model prior observation recognitionMean,
    gaussianVariationalFreeEnergy_naturalGradientFlow_deriv_neg
      model prior observation recognitionMean hRecognition⟩

/-! ## One filter-consuming finite action on the selected dynamics -/

/-- The `false` branch is definitionally the same base dynamics used by the
filter, semigroup, invariant law, and grid path. -/
theorem selectedControl_false_dynamics :
    selectedControl.dynamics false = selectedDynamics := by
  rfl

/-- Exact one-step risk of retaining the base diffusion. -/
theorem selectedControl_false_risk :
    filteredQuadraticRisk selectedControl selectedFilter selectedPrior 0 false =
      1 - (1 / 2 : ℝ) * Real.exp (-1) ^ 2 := by
  have hMean :
      controlledMean selectedControl
          (posteriorBelief selectedFilter selectedPrior 0) false = 0 := by
    change
      selectedDynamics.transitionMean 1
        (posteriorMean selectedFilter selectedPrior 0) = 0
    rw [selectedPosterior_mean]
    norm_num [selectedDynamics, ScalarOUParameters.transitionMean,
      ScalarOUParameters.decay]
  have hVariance :
      (controlledVariance selectedControl
          (posteriorBelief selectedFilter selectedPrior 0) false : ℝ) =
        1 - (1 / 2 : ℝ) * Real.exp (-1) ^ 2 := by
    unfold controlledVariance
    rw [show
      (posteriorBelief selectedFilter selectedPrior 0).family.variance =
          1 / 2 by
        change posteriorVariance selectedFilter selectedPrior = 1 / 2
        exact selectedPosterior_variance]
    simp only [NNReal.coe_add, NNReal.coe_mul, NNReal.coe_mk]
    change
      selectedDynamics.decay 1 ^ 2 * (1 / 2 : ℝ) +
          (selectedDynamics.transitionVariance 1 : ℝ) =
        1 - (1 / 2 : ℝ) * Real.exp (-1) ^ 2
    unfold ScalarOUParameters.transitionVariance
    change
      selectedDynamics.decay 1 ^ 2 * (1 / 2 : ℝ) +
          (selectedDynamics.stationaryVariance : ℝ) *
            (1 - selectedDynamics.decay 1 ^ 2) =
        1 - (1 / 2 : ℝ) * Real.exp (-1) ^ 2
    rw [selectedDynamics.stationaryVariance_eq]
    norm_num [selectedDynamics, ScalarOUParameters.decay]
    ring
  rw [filteredQuadraticRisk, quadraticActionRisk_eq_closedForm]
  rw [hVariance, hMean]
  norm_num [selectedControl]

/-- Exact one-step risk of the higher-diffusion alternative. -/
theorem selectedControl_true_risk :
    filteredQuadraticRisk selectedControl selectedFilter selectedPrior 0 true =
      2 - (3 / 2 : ℝ) * Real.exp (-1) ^ 2 := by
  have hMean :
      controlledMean selectedControl
          (posteriorBelief selectedFilter selectedPrior 0) true = 0 := by
    change
      alternativeDynamics.transitionMean 1
        (posteriorMean selectedFilter selectedPrior 0) = 0
    rw [selectedPosterior_mean]
    norm_num [alternativeDynamics, ScalarOUParameters.transitionMean,
      ScalarOUParameters.decay]
  have hVariance :
      (controlledVariance selectedControl
          (posteriorBelief selectedFilter selectedPrior 0) true : ℝ) =
        2 - (3 / 2 : ℝ) * Real.exp (-1) ^ 2 := by
    unfold controlledVariance
    rw [show
      (posteriorBelief selectedFilter selectedPrior 0).family.variance =
          1 / 2 by
        change posteriorVariance selectedFilter selectedPrior = 1 / 2
        exact selectedPosterior_variance]
    simp only [NNReal.coe_add, NNReal.coe_mul, NNReal.coe_mk]
    change
      alternativeDynamics.decay 1 ^ 2 * (1 / 2 : ℝ) +
          (alternativeDynamics.transitionVariance 1 : ℝ) =
        2 - (3 / 2 : ℝ) * Real.exp (-1) ^ 2
    unfold ScalarOUParameters.transitionVariance
    change
      alternativeDynamics.decay 1 ^ 2 * (1 / 2 : ℝ) +
          (alternativeDynamics.stationaryVariance : ℝ) *
            (1 - alternativeDynamics.decay 1 ^ 2) =
        2 - (3 / 2 : ℝ) * Real.exp (-1) ^ 2
    rw [alternativeDynamics.stationaryVariance_eq]
    norm_num [alternativeDynamics, ScalarOUParameters.decay]
    ring
  rw [filteredQuadraticRisk, quadraticActionRisk_eq_closedForm]
  rw [hVariance, hMean]
  norm_num [selectedControl]

/-- The actual transition-derived base risk is strictly smaller. -/
theorem selectedControl_false_strictlyBetter :
    filteredQuadraticRisk selectedControl selectedFilter selectedPrior 0 false <
      filteredQuadraticRisk selectedControl selectedFilter selectedPrior 0 true := by
  rw [selectedControl_false_risk, selectedControl_true_risk]
  have hExpPos : 0 < Real.exp (-1) := Real.exp_pos _
  have hExpLtOne : Real.exp (-1) < 1 :=
    Real.exp_lt_one_iff.mpr (by norm_num)
  nlinarith [sq_nonneg (Real.exp (-1))]

/-- The finite minimizer selects the base action. -/
theorem selectedControl_selectedAction :
    selectedAction selectedControl selectedFilter selectedPrior 0 = false := by
  apply selectedAction_eq_of_strict
  intro alternative hAlternative
  have hTrue : alternative = true :=
    Bool.eq_true_of_not_eq_false hAlternative
  subst alternative
  exact selectedControl_false_strictlyBetter

/-- The selected action samples exactly the same unit-time base OU transition. -/
theorem selectedControl_actionTransition_eq_selectedTransition :
    actionTransition selectedControl
        (selectedAction selectedControl selectedFilter selectedPrior 0) =
      selectedDynamics.ouTransition 1 := by
  rw [selectedControl_selectedAction, actionTransition_eq_ouTransition]
  rfl

/-- Strict risk separation forces the two native action transitions to differ. -/
theorem selectedControl_actionTransitions_ne :
    actionTransition selectedControl false ≠
      actionTransition selectedControl true := by
  intro hTransitions
  have hRisks :
      filteredQuadraticRisk selectedControl selectedFilter selectedPrior 0 false =
        filteredQuadraticRisk selectedControl selectedFilter selectedPrior 0 true := by
    unfold filteredQuadraticRisk quadraticActionRisk
    rw [hTransitions]
    norm_num [selectedControl]
  exact (ne_of_lt selectedControl_false_strictlyBetter) hRisks

/-! ## The same base dynamics on a finite unit grid -/

/-- Consecutive selected grid times differ by one. -/
theorem selectedUnitGrid_stepDuration (n : ℕ) :
    selectedUnitGrid.time (n + 1) - selectedUnitGrid.time n = 1 := by
  apply NNReal.eq
  norm_num [selectedUnitGrid]

/-- Every grid step is the same selected unit-time OU kernel, read from the
last coordinate of the current finite path. -/
theorem selectedUnitGrid_stepKernel (n : ℕ) :
    ouGridStep selectedDynamics selectedUnitGrid n =
      (selectedDynamics.ouTransition 1).comap
        (fun path => path ⟨n, Finset.mem_Iic.mpr le_rfl⟩) (by fun_prop) := by
  unfold ouGridStep
  rw [selectedUnitGrid_stepDuration]

/-! ## Terminal exports -/

/-- The connected scalar H2 terminal result.  Every clause uses the named
selected real-valued model above: the learning and filtering lanes share exact
observation rows, the filter, controller, grid, invariant law, and KL theorem
share the same base OU transition, and the continuous VFE is evaluated at the
same selected filter posterior.  Static-parameter and latent-state posteriors
remain distinct carriers. -/
theorem smoothReferenceKernel_terminal
    (actual : Measure ℝ) [IsFiniteMeasure actual]
    (earlier increment : ℝ≥0) (n : ℕ)
    (recognitionMean tangent : ℝ) (hRecognition : recognitionMean ≠ 0)
    (observable : BoundedContinuousFunction MeanHypothesis ℝ) :
    (∀ hypothesis,
      observationKernel selectedFilter (selectedMean hypothesis) =
        selectedObservationLaw hypothesis) ∧
      (∀ hypothesis,
        observationKernel selectedFilter (selectedMean hypothesis) Set.univ = 1) ∧
      (∀ state,
        selectedDynamics.ouTransition 1 state =
          (selectedDynamics.positiveTimeGaussian 1 (by norm_num)).law
            (selectedDynamics.transitionMean 1 state)) ∧
      (∀ state, selectedDynamics.ouTransition 1 state Set.univ = 1) ∧
      selectedDynamics.stationaryLaw = selectedObservationLaw false ∧
      InvariantLaw selectedDynamics.ouNativeSemigroup
        selectedDynamics.stationaryLaw ∧
      predictionBelief selectedFilter selectedPrior = selectedPrior ∧
      closedFormPosteriorKernel selectedFilter selectedPrior =ᵐ[
          evidenceLaw selectedFilter selectedPrior]
        ProbabilityTheory.posterior (observationKernel selectedFilter)
          (predictionBelief selectedFilter selectedPrior).law ∧
      evidenceLaw selectedFilter selectedPrior =
        volume.withDensity (evidenceDensity selectedFilter selectedPrior) ∧
      0 < evidenceDensity selectedFilter selectedPrior 0 ∧
      evidenceDensity selectedFilter selectedPrior 0 ≠ ⊤ ∧
      gaussianVariationalFreeEnergy selectedFilter selectedPrior 0 recognitionMean -
          evidenceSurprisal selectedFilter selectedPrior 0 =
        (klDiv
          ((posteriorFamily selectedFilter selectedPrior).law recognitionMean)
          ((posteriorBelief selectedFilter selectedPrior 0).law)).toReal ∧
      (gaussianVariationalFreeEnergy selectedFilter selectedPrior 0
            recognitionMean = evidenceSurprisal selectedFilter selectedPrior 0 ↔
        recognitionMean = posteriorMean selectedFilter selectedPrior 0) ∧
      meanNaturalGradient selectedFilter selectedPrior 0 recognitionMean =
        recognitionMean - posteriorMean selectedFilter selectedPrior 0 ∧
      meanMetricPairing (posteriorFamily selectedFilter selectedPrior)
          recognitionMean
          (meanNaturalGradient selectedFilter selectedPrior 0 recognitionMean)
          tangent =
        ((recognitionMean - posteriorMean selectedFilter selectedPrior 0) /
            (posteriorVariance selectedFilter selectedPrior : ℝ)) * tangent ∧
      HasDerivAt
        (fun time =>
          gaussianVariationalFreeEnergy selectedFilter selectedPrior 0
            (naturalGradientFlow selectedFilter selectedPrior 0
              recognitionMean time))
        (-((recognitionMean - posteriorMean selectedFilter selectedPrior 0) ^ 2 /
          (posteriorVariance selectedFilter selectedPrior : ℝ))) 0 ∧
      -((recognitionMean - posteriorMean selectedFilter selectedPrior 0) ^ 2 /
          (posteriorVariance selectedFilter selectedPrior : ℝ)) < 0 ∧
      (∀ᵐ sample ∂selectedJointLaw,
        Tendsto (fun k => posteriorProbability k sample) atTop
          (𝓝 (selectedParameterIndicator sample))) ∧
      (∀ᵐ sample ∂selectedJointLaw,
        Tendsto
          (fun k =>
            ∫ hypothesis, observable hypothesis
              ∂(parameterPosterior k sample : ProbabilityMeasure MeanHypothesis))
          atTop (𝓝 (observable sample.1))) ∧
      (∀ᵐ sample ∂selectedJointLaw,
        Tendsto (fun k => posteriorDecisionRisk k sample) atTop (𝓝 0)) ∧
      (∀ alternative : Bool,
        filteredQuadraticRisk selectedControl selectedFilter selectedPrior 0
            (selectedAction selectedControl selectedFilter selectedPrior 0) ≤
          filteredQuadraticRisk selectedControl selectedFilter selectedPrior 0
            alternative) ∧
      (fun observation =>
          selectedAction selectedControl selectedFilter selectedPrior observation)
        =ᵐ[evidenceLaw selectedFilter selectedPrior]
          (fun observation =>
            nativePosteriorSelectedAction selectedControl selectedFilter
              selectedPrior observation) ∧
      selectedAction selectedControl selectedFilter selectedPrior 0 = false ∧
      actionTransition selectedControl
          (selectedAction selectedControl selectedFilter selectedPrior 0) =
        selectedDynamics.ouTransition 1 ∧
      actionTransition selectedControl false ≠
        actionTransition selectedControl true ∧
      ouGridStep selectedDynamics selectedUnitGrid n =
        (selectedDynamics.ouTransition 1).comap
          (fun path => path ⟨n, Finset.mem_Iic.mpr le_rfl⟩) (by fun_prop) ∧
      forwardGridLaw selectedDynamics selectedUnitGrid n Set.univ = 1 ∧
      klDiv
          (selectedDynamics.ouTransition (earlier + increment) ∘ₘ actual)
          selectedDynamics.stationaryLaw ≤
        klDiv (selectedDynamics.ouTransition earlier ∘ₘ actual)
          selectedDynamics.stationaryLaw := by
  have hRecognition' :
      recognitionMean ≠ posteriorMean selectedFilter selectedPrior 0 := by
    simpa only [selectedPosterior_mean] using hRecognition
  rcases continuousGaussianVFE_naturalGradient selectedFilter selectedPrior 0
      recognitionMean tangent hRecognition' with
    ⟨hEvidence, hDensityPos, hDensityFinite, hGap, hOptimal,
      hNaturalGradient, hMetricDual, hFlowDeriv, hFlowStrict⟩
  exact ⟨
    selectedObservationKernel_eq_learningObservationLaw,
    fun _ => measure_univ,
    selectedTransition_eq_gaussianLocation,
    fun state => selectedDynamics.ouTransition_univ 1 state,
    selectedStationaryLaw_eq_learningObservationFalse,
    selectedDynamics.stationaryLaw_invariant,
    selectedPredictionBelief_eq_prior,
    closedFormPosterior_ae_eq_native selectedFilter selectedPrior,
    hEvidence,
    hDensityPos,
    hDensityFinite,
    hGap,
    hOptimal,
    hNaturalGradient,
    hMetricDual,
    hFlowDeriv,
    hFlowStrict,
    posteriorProbability_consistent_ae,
    boundedContinuousPosteriorExpectation_tendsto_ae observable,
    posteriorDecisionRisk_tendsto_zero_ae,
    selectedAction_le selectedControl selectedFilter selectedPrior 0,
    selectedAction_ae_eq_nativePosteriorSelectedAction
      selectedControl selectedFilter selectedPrior,
    selectedControl_selectedAction,
    selectedControl_actionTransition_eq_selectedTransition,
    selectedControl_actionTransitions_ne,
    selectedUnitGrid_stepKernel n,
    forwardGridLaw_normalized selectedDynamics selectedUnitGrid n,
    selectedDynamics.ouKL_to_stationary_nonincrease earlier increment actual⟩

/-- Separate Fin4 terminal export.  It retains the exact preregistered carrier,
the maintained sensory--active conditional product law, the native conditional
independence theorem despite nonzero marginal covariance, and the fixed
Fin2 precision perturbation that refutes unconditional endpoint independence
in that separate two-coordinate diagnostic model. -/
theorem fin4ReferenceKernel_terminal :
    Fintype.card Axis = 4 ∧
      K.PosDef ∧
      K * FEP.Fin4GaussianSemigroup.Sigma = 1 ∧
      FEP.Fin4GaussianSemigroup.Sigma * K = 1 ∧
      FEP.Fin4GaussianSemigroup.Sigma.PosDef ∧
      K Axis.external Axis.internal = 0 ∧
      FEP.Fin4GaussianSemigroup.Sigma Axis.external Axis.internal = 1 / 24 ∧
      FEP.Fin4GaussianSemigroup.Sigma Axis.external Axis.internal ≠ 0 ∧
      (∀ center : StandardizedState,
        stationaryLaw center =
          multivariateGaussian center FEP.Fin4GaussianSemigroup.Sigma) ∧
      (∀ center : StandardizedState,
        InvariantLaw (nativeSemigroup center) (stationaryLaw center)) ∧
      (∀ center state : StandardizedState,
        Tendsto (fun time : ℝ≥0 => transitionProbability center time state)
          atTop (𝓝 (stationaryProbability center))) ∧
      (∀ center : ℝ,
        (scalarParameters center).rate = 2 ∧
          (scalarParameters center).diffusionVarianceRate = 2) ∧
      (∀ (center : ℝ) (time : ℝ≥0),
        projectedTransition center time =
          (scalarParameters center).ouTransition time) ∧
      (∀ center : StandardizedState,
        condDistrib endpointCoordinates blanketCoordinates (stationaryLaw center)
          =ᵐ[blanketLaw center] endpointConditionalKernel center) ∧
      (∀ center : StandardizedState,
        K Axis.external Axis.internal = 0 ∧
          cov[fun state : StandardizedState => state Axis.external,
            fun state => state Axis.internal; stationaryLaw center] = 1 / 24 ∧
          cov[fun state : StandardizedState => state Axis.external,
            fun state => state Axis.internal; stationaryLaw center] ≠ 0 ∧
          ((fun state : StandardizedState => state Axis.external) ⟂ᵢ[
            blanketCoordinates, measurable_blanketCoordinates;
            stationaryLaw center]
            (fun state => state Axis.internal))) ∧
      ¬ IndepFun perturbedExternal perturbedInternal perturbedEndpointLaw := by
  have hExact := exactFin4Carrier
  exact ⟨hExact.1, K_posDef, K_mul_Sigma, Sigma_mul_K, Sigma_posDef,
    K_external_internal, Sigma_external_internal,
    Sigma_external_internal_ne_zero, stationaryLaw_eq_gaussian,
    stationaryLaw_invariant, transitionProbability_tendsto_invariant,
    scalarParameters_exact, projectedTransition_eq_scalarOU,
    endpointCondDistrib_ae_eq_product,
    precisionZero_covarianceNonzero_condIndep,
    perturbedEndpoint_external_not_indep_internal⟩

end

end FEPComposed.SmoothReferenceKernel
