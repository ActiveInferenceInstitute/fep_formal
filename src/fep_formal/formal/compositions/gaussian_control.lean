module
public import FepSketches.compositions.gaussian_filter
public import FepSketches.controlled_markov
public import FepSketches.gaussian_information_geometry
public import FepSketches.markov_semigroup
public import FepSketches.scalar_gaussian_semigroup
public import Mathlib.Probability.Distributions.Gaussian.Real
public import Mathlib.Probability.Kernel.Posterior

@[expose] public section

/-!
# Filter-consuming finite Gaussian control

This composition applies one finite action after the accepted scalar Gaussian
filter update.  Each action selects an accepted scalar OU transition at one
common positive duration.  The real objective is the integral of terminal
squared error under that composed transition law, plus a separately
nonnegative action penalty.  Native-posterior selector agreement is therefore
claimed only almost everywhere under the filter's evidence law.
-/

namespace FEPComposed.GaussianControl

open FEP.ControlledMarkov
open FEP.GaussianInformationGeometry
open FEP.MarkovSemigroup
open FEP.ScalarGaussianSemigroup
open FEPComposed.GaussianFilter
open MeasureTheory ProbabilityTheory
open scoped ENNReal MeasureTheory NNReal ProbabilityTheory

noncomputable section

/-- Raw inputs for a finite family of one-step scalar Gaussian controls. -/
structure FiniteGaussianControlModel (Action : Type*) where
  dynamics : Action → ScalarOUParameters
  duration : ℝ≥0
  duration_pos : 0 < duration
  target : ℝ
  actionPenalty : Action → ℝ≥0

/-- Each action reuses its accepted scalar OU transition family. -/
noncomputable def actionKernelFamily {Action : Type*}
    (control : FiniteGaussianControlModel Action)
    (action : Action) (time : ℝ≥0) : Kernel ℝ ℝ :=
  (control.dynamics action).ouTransition time

noncomputable instance actionKernelFamily_isMarkovKernel
    {Action : Type*} (control : FiniteGaussianControlModel Action)
    (action : Action) (time : ℝ≥0) :
    IsMarkovKernel (actionKernelFamily control action time) := by
  unfold actionKernelFamily
  infer_instance

/-- H2.4b packaging of the action-indexed OU families at one common time. -/
noncomputable def actionIndexedSemigroup {Action : Type*}
    (control : FiniteGaussianControlModel Action) :
    NativeActionIndexedKernelSemigroup ℝ Action
      (actionKernelFamily control) where
  semigroup action := (control.dynamics action).ouNativeSemigroup
  sampleTime _ := control.duration

/-- The native transition selected by one action at the common duration. -/
noncomputable def actionTransition {Action : Type*}
    (control : FiniteGaussianControlModel Action)
    (action : Action) : Kernel ℝ ℝ :=
  NativeActionIndexedKernelSemigroup.sampledKernel
    (actionIndexedSemigroup control) action

/-- Mean after applying the selected OU transition to a Gaussian belief. -/
noncomputable def controlledMean {Action : Type*}
    (control : FiniteGaussianControlModel Action)
    (belief : ScalarGaussianBelief) (action : Action) : ℝ :=
  (control.dynamics action).transitionMean control.duration belief.mean

/-- Variance after applying the selected OU transition to a Gaussian belief. -/
noncomputable def controlledVariance {Action : Type*}
    (control : FiniteGaussianControlModel Action)
    (belief : ScalarGaussianBelief) (action : Action) : ℝ≥0 :=
  NNReal.mk
      ((control.dynamics action).decay control.duration ^ 2)
      (sq_nonneg _) * belief.family.variance +
    (control.dynamics action).transitionVariance control.duration

/-- A nondegenerate input belief remains nondegenerate after every action. -/
theorem controlledVariance_pos {Action : Type*}
    (control : FiniteGaussianControlModel Action)
    (belief : ScalarGaussianBelief) (action : Action) :
    0 < controlledVariance control belief action := by
  have hDecay :
      0 < (control.dynamics action).decay control.duration := Real.exp_pos _
  have hCoefficient :
      0 < NNReal.mk
        ((control.dynamics action).decay control.duration ^ 2)
        (sq_nonneg _) := by
    exact_mod_cast sq_pos_of_pos hDecay
  exact add_pos_of_pos_of_nonneg
    (mul_pos hCoefficient belief.family.variance_pos)
    ((control.dynamics action).transitionVariance control.duration).2

/-- Exact Gaussian belief produced by the selected transition. -/
noncomputable def controlledBelief {Action : Type*}
    (control : FiniteGaussianControlModel Action)
    (belief : ScalarGaussianBelief) (action : Action) :
    ScalarGaussianBelief where
  mean := controlledMean control belief action
  family :=
    { variance := controlledVariance control belief action
      variance_pos := controlledVariance_pos control belief action }

/-- Sampling the packaged family is exactly the selected accepted OU slice. -/
theorem actionTransition_eq_ouTransition {Action : Type*}
    (control : FiniteGaussianControlModel Action) (action : Action) :
    actionTransition control action =
      (control.dynamics action).ouTransition control.duration := by
  rfl

/-- The actual selected transition composed with the input belief has the
derived Gaussian parameters. -/
theorem actionTransition_comp_belief {Action : Type*}
    (control : FiniteGaussianControlModel Action)
    (belief : ScalarGaussianBelief) (action : Action) :
    actionTransition control action ∘ₘ belief.law =
      (controlledBelief control belief action).law := by
  rw [actionTransition_eq_ouTransition]
  change
    (control.dynamics action).ouTransition control.duration ∘ₘ
        gaussianReal belief.mean belief.family.variance =
      gaussianReal (controlledMean control belief action)
        (controlledVariance control belief action)
  simpa only [controlledMean, controlledVariance] using
    (control.dynamics action).ouTransition_comp_gaussian
      control.duration belief.mean belief.family.variance

/-- Statewise terminal squared error.  It is intentionally not bounded. -/
def quadraticTerminalLoss (target state : ℝ) : ℝ :=
  (state - target) ^ 2

/-- The integral terminal risk under the actual composed law, plus the
separately typed nonnegative action penalty. -/
noncomputable def quadraticActionRisk {Action : Type*}
    (control : FiniteGaussianControlModel Action)
    (belief : ScalarGaussianBelief) (action : Action) : ℝ :=
  ∫ nextState, quadraticTerminalLoss control.target nextState
      ∂(actionTransition control action ∘ₘ belief.law) +
    (control.actionPenalty action : ℝ)

/-- The closed H2.6a posterior is the belief consumed by one-step control. -/
noncomputable def filteredQuadraticRisk {Action : Type*}
    (control : FiniteGaussianControlModel Action)
    (filter : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation : ℝ) (action : Action) : ℝ :=
  quadraticActionRisk control
    (posteriorBelief filter prior observation) action

/-- The corresponding risk computed from Mathlib's native posterior row. -/
noncomputable def nativePosteriorQuadraticRisk {Action : Type*}
    (control : FiniteGaussianControlModel Action)
    (filter : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation : ℝ) (action : Action) : ℝ :=
  ∫ nextState, quadraticTerminalLoss control.target nextState
      ∂(actionTransition control action ∘ₘ
        (ProbabilityTheory.posterior (observationKernel filter)
          (predictionBelief filter prior).law) observation) +
    (control.actionPenalty action : ℝ)

/-- Every real bound is exceeded by some statewise terminal loss. -/
theorem quadraticTerminalLoss_unbounded (target bound : ℝ) :
    ∃ state : ℝ, bound < quadraticTerminalLoss target state := by
  refine ⟨target + |bound| + 1, ?_⟩
  unfold quadraticTerminalLoss
  have hAbs : bound ≤ |bound| := le_trans (le_abs_self bound) le_rfl
  have hAbsNonneg : 0 ≤ |bound| := abs_nonneg bound
  nlinarith

private theorem integral_quadratic_gaussianReal
    (mean target : ℝ) (variance : ℝ≥0) :
    ∫ state, quadraticTerminalLoss target state
        ∂gaussianReal mean variance =
      (variance : ℝ) + (mean - target) ^ 2 := by
  have hLp : MemLp id 2 (gaussianReal mean variance) :=
    memLp_id_gaussianReal 2
  have hIdentity :
      Integrable (fun state : ℝ => state) (gaussianReal mean variance) := by
    simpa only [Function.id_def] using hLp.integrable one_le_two
  have hSquare :
      Integrable (fun state : ℝ => state ^ 2)
        (gaussianReal mean variance) := by
    simpa only [Function.id_def] using hLp.integrable_sq
  have hVariance :
      (variance : ℝ) =
        (∫ state, state ^ 2 ∂gaussianReal mean variance) - mean ^ 2 := by
    simpa only [variance_fun_id_gaussianReal, integral_id_gaussianReal,
      Pi.pow_apply, Function.id_def] using variance_eq_sub hLp
  have hLinear :
      Integrable (fun state : ℝ => (2 * target) * state)
        (gaussianReal mean variance) :=
    hIdentity.const_mul (2 * target)
  have hDifference :
      Integrable (fun state : ℝ => state ^ 2 - (2 * target) * state)
        (gaussianReal mean variance) :=
    hSquare.sub hLinear
  calc
    ∫ state, quadraticTerminalLoss target state
        ∂gaussianReal mean variance =
        ∫ state, (state ^ 2 - (2 * target) * state) + target ^ 2
          ∂gaussianReal mean variance := by
      apply integral_congr_ae
      filter_upwards [] with state
      unfold quadraticTerminalLoss
      ring
    _ =
        (∫ state, state ^ 2 - (2 * target) * state
          ∂gaussianReal mean variance) +
          ∫ _ : ℝ, target ^ 2 ∂gaussianReal mean variance :=
      integral_add hDifference (integrable_const (target ^ 2))
    _ =
        ((∫ state, state ^ 2 ∂gaussianReal mean variance) -
          ∫ state, (2 * target) * state
            ∂gaussianReal mean variance) +
          ∫ _ : ℝ, target ^ 2 ∂gaussianReal mean variance := by
      rw [integral_sub hSquare hLinear]
    _ = (variance : ℝ) + (mean - target) ^ 2 := by
      rw [integral_const_mul, integral_const, integral_id_gaussianReal]
      simp only [probReal_univ, one_smul]
      nlinarith [hVariance]

/-- Gaussian integrability turns the actual composed-law integral into its
exact mean-square closed form. -/
theorem quadraticActionRisk_eq_closedForm {Action : Type*}
    (control : FiniteGaussianControlModel Action)
    (belief : ScalarGaussianBelief) (action : Action) :
    quadraticActionRisk control belief action =
      (controlledVariance control belief action : ℝ) +
        (controlledMean control belief action - control.target) ^ 2 +
        (control.actionPenalty action : ℝ) := by
  rw [quadraticActionRisk, actionTransition_comp_belief]
  change
    (∫ nextState, quadraticTerminalLoss control.target nextState
        ∂gaussianReal (controlledMean control belief action)
          (controlledVariance control belief action)) +
      (control.actionPenalty action : ℝ) = _
  rw [integral_quadratic_gaussianReal]

/-- Every one-step action risk is nonnegative. -/
theorem quadraticActionRisk_nonneg {Action : Type*}
    (control : FiniteGaussianControlModel Action)
    (belief : ScalarGaussianBelief) (action : Action) :
    0 ≤ quadraticActionRisk control belief action := by
  rw [quadraticActionRisk_eq_closedForm]
  positivity

/-- Closed-form and native-posterior action risks agree only evidence almost
everywhere, matching the scope of the accepted filter theorem. -/
theorem filteredQuadraticRisk_ae_eq_nativePosterior {Action : Type*}
    (control : FiniteGaussianControlModel Action)
    (filter : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (action : Action) :
    (fun observation =>
      filteredQuadraticRisk control filter prior observation action) =ᵐ[
        evidenceLaw filter prior]
      fun observation =>
        nativePosteriorQuadraticRisk control filter prior observation action := by
  filter_upwards [closedFormPosterior_ae_eq_native filter prior] with
    observation hPosterior
  unfold filteredQuadraticRisk quadraticActionRisk
    nativePosteriorQuadraticRisk
  change
    (∫ nextState, quadraticTerminalLoss control.target nextState
        ∂(actionTransition control action ∘ₘ
          closedFormPosteriorKernel filter prior observation)) +
        (control.actionPenalty action : ℝ) = _
  rw [hPosterior]

/-- A fixed finite minimizer of the filtered one-step objective. -/
noncomputable def selectedAction {Action : Type*}
    [Fintype Action] [Nonempty Action]
    (control : FiniteGaussianControlModel Action)
    (filter : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation : ℝ) : Action :=
  finiteArgmin (filteredQuadraticRisk control filter prior observation)

/-- The corresponding finite minimizer of the native-posterior objective. -/
noncomputable def nativePosteriorSelectedAction {Action : Type*}
    [Fintype Action] [Nonempty Action]
    (control : FiniteGaussianControlModel Action)
    (filter : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation : ℝ) : Action :=
  finiteArgmin
    (nativePosteriorQuadraticRisk control filter prior observation)

/-- The selected filtered action is no worse than every alternative. -/
theorem selectedAction_le {Action : Type*}
    [Fintype Action] [Nonempty Action]
    (control : FiniteGaussianControlModel Action)
    (filter : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation : ℝ) (alternative : Action) :
    filteredQuadraticRisk control filter prior observation
        (selectedAction control filter prior observation) ≤
      filteredQuadraticRisk control filter prior observation alternative := by
  exact finiteArgmin_le
    (filteredQuadraticRisk control filter prior observation) alternative

/-- The selected native-posterior action is no worse than every alternative. -/
theorem nativePosteriorSelectedAction_le {Action : Type*}
    [Fintype Action] [Nonempty Action]
    (control : FiniteGaussianControlModel Action)
    (filter : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation : ℝ) (alternative : Action) :
    nativePosteriorQuadraticRisk control filter prior observation
        (nativePosteriorSelectedAction control filter prior observation) ≤
      nativePosteriorQuadraticRisk control filter prior observation
        alternative := by
  exact finiteArgmin_le
    (nativePosteriorQuadraticRisk control filter prior observation)
    alternative

/-- Finite choice lifts the risk equality to selector equality on the same
evidence-almost-everywhere set. -/
theorem selectedAction_ae_eq_nativePosteriorSelectedAction
    {Action : Type*} [Fintype Action] [Nonempty Action]
    (control : FiniteGaussianControlModel Action)
    (filter : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief) :
    (fun observation => selectedAction control filter prior observation) =ᵐ[
        evidenceLaw filter prior]
      fun observation =>
        nativePosteriorSelectedAction control filter prior observation := by
  have hRisks :
      ∀ᵐ observation ∂evidenceLaw filter prior, ∀ action : Action,
        filteredQuadraticRisk control filter prior observation action =
          nativePosteriorQuadraticRisk control filter prior observation
            action := by
    exact Filter.eventually_all.2 fun action =>
      filteredQuadraticRisk_ae_eq_nativePosterior
        control filter prior action
  filter_upwards [hRisks] with observation hObservation
  change
    finiteArgmin (filteredQuadraticRisk control filter prior observation) =
      finiteArgmin
        (nativePosteriorQuadraticRisk control filter prior observation)
  congr 1
  funext action
  exact hObservation action

/-- A pointwise strict minimizer is the action chosen by `finiteArgmin`. -/
theorem selectedAction_eq_of_strict {Action : Type*}
    [Fintype Action] [Nonempty Action]
    (control : FiniteGaussianControlModel Action)
    (filter : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation : ℝ) (candidate : Action)
    (hStrict : ∀ alternative, alternative ≠ candidate →
      filteredQuadraticRisk control filter prior observation candidate <
        filteredQuadraticRisk control filter prior observation alternative) :
    selectedAction control filter prior observation = candidate := by
  by_contra hSelected
  have hMinimum := selectedAction_le control filter prior observation candidate
  have hStrictSelected := hStrict
    (selectedAction control filter prior observation) hSelected
  exact (not_lt_of_ge hMinimum) hStrictSelected

noncomputable def boolDynamics
    (diffusionVarianceRate : ℝ≥0)
    (hDiffusionVarianceRate : 0 < diffusionVarianceRate) :
    ScalarOUParameters where
  rate := 1
  rate_pos := by norm_num
  center := 0
  diffusionVarianceRate := diffusionVarianceRate
  diffusionVarianceRate_pos := hDiffusionVarianceRate

private theorem boolDynamics_stationaryVariance
    (diffusionVarianceRate : ℝ≥0)
    (hDiffusionVarianceRate : 0 < diffusionVarianceRate) :
    (boolDynamics diffusionVarianceRate hDiffusionVarianceRate).stationaryVariance =
      diffusionVarianceRate / 2 := by
  apply NNReal.eq
  change
    (diffusionVarianceRate : ℝ) / (2 * (1 : ℝ)) =
      ((diffusionVarianceRate / 2 : ℝ≥0) : ℝ)
  norm_num

private theorem boolDynamics_decay_one
    (diffusionVarianceRate : ℝ≥0)
    (hDiffusionVarianceRate : 0 < diffusionVarianceRate) :
    (boolDynamics diffusionVarianceRate hDiffusionVarianceRate).decay 1 =
      Real.exp (-1) := by
  norm_num [ScalarOUParameters.decay, boolDynamics]

private theorem boolDynamics_transitionVariance_one_real
    (diffusionVarianceRate : ℝ≥0)
    (hDiffusionVarianceRate : 0 < diffusionVarianceRate) :
    ((boolDynamics diffusionVarianceRate hDiffusionVarianceRate).transitionVariance 1 : ℝ) =
      (diffusionVarianceRate : ℝ) / 2 * (1 - Real.exp (-1) ^ 2) := by
  change
    ((boolDynamics diffusionVarianceRate
          hDiffusionVarianceRate).stationaryVariance : ℝ) *
        (1 -
          (boolDynamics diffusionVarianceRate
              hDiffusionVarianceRate).decay 1 ^ 2) =
      (diffusionVarianceRate : ℝ) / 2 * (1 - Real.exp (-1) ^ 2)
  rw [boolDynamics_stationaryVariance, boolDynamics_decay_one]
  norm_num [NNReal.coe_div]

/-- Symmetric prior used by the strict Boolean witness. -/
noncomputable def boolWitnessPrior : ScalarGaussianBelief where
  mean := 0
  family :=
    { variance := 1 / 2
      variance_pos := by norm_num }

/-- Accepted filter instance whose zero observation gives posterior `N(0,1/4)`. -/
noncomputable def boolWitnessFilter : ScalarGaussianFilterModel where
  dynamics := boolDynamics 1 (by norm_num)
  stepDuration := 1
  observationNoise :=
    { variance := 1 / 2
      variance_pos := by norm_num }

/-- Boolean control with lower diffusion variance for `true`. -/
noncomputable def boolWitnessControl : FiniteGaussianControlModel Bool where
  dynamics := fun action =>
    if action then boolDynamics (1 / 2) (by norm_num)
    else boolDynamics 1 (by norm_num)
  duration := 1
  duration_pos := by norm_num
  target := 0
  actionPenalty := fun _ => 0

/-- The finite action actually selected by the strict Boolean witness. -/
noncomputable def boolWitnessAction : Bool :=
  selectedAction boolWitnessControl boolWitnessFilter boolWitnessPrior 0

/-- Equal dynamics and penalties expose the non-unique tie boundary. -/
noncomputable def boolTieControl : FiniteGaussianControlModel Bool where
  dynamics := fun _ => boolDynamics 1 (by norm_num)
  duration := 1
  duration_pos := by norm_num
  target := 0
  actionPenalty := fun _ => 0

private theorem boolWitness_prediction_mean :
    (predictionBelief boolWitnessFilter boolWitnessPrior).mean = 0 := by
  norm_num [predictionBelief, boolWitnessFilter, boolWitnessPrior,
    boolDynamics, ScalarOUParameters.transitionMean,
    ScalarOUParameters.decay]

private theorem boolWitness_prediction_variance :
    (predictionBelief boolWitnessFilter boolWitnessPrior).family.variance =
      1 / 2 := by
  change predictionVariance boolWitnessFilter boolWitnessPrior = 1 / 2
  apply NNReal.eq
  unfold predictionVariance
  simp only [NNReal.coe_add, NNReal.coe_mul, NNReal.coe_mk]
  rw [show
    boolWitnessFilter.dynamics.decay boolWitnessFilter.stepDuration =
        Real.exp (-1) by
      norm_num [boolWitnessFilter, boolDynamics_decay_one],
    show (boolWitnessPrior.family.variance : ℝ) = 1 / 2 by
      norm_num [boolWitnessPrior],
    show
      (boolWitnessFilter.dynamics.transitionVariance
          boolWitnessFilter.stepDuration : ℝ) =
        (1 / 2 : ℝ) * (1 - Real.exp (-1) ^ 2) by
      norm_num [boolWitnessFilter,
        boolDynamics_transitionVariance_one_real]]
  norm_num
  ring

/-- The witness update remains centered after observing zero. -/
theorem boolWitness_posterior_mean :
    posteriorMean boolWitnessFilter boolWitnessPrior 0 = 0 := by
  change
    (predictionBelief boolWitnessFilter boolWitnessPrior).mean +
        gain boolWitnessFilter boolWitnessPrior *
          (0 - (predictionBelief boolWitnessFilter boolWitnessPrior).mean) = 0
  rw [boolWitness_prediction_mean]
  ring

/-- The witness update has exact posterior variance one quarter. -/
theorem boolWitness_posterior_variance :
    posteriorVariance boolWitnessFilter boolWitnessPrior = 1 / 4 := by
  change
    (predictionBelief boolWitnessFilter boolWitnessPrior).family.variance *
          boolWitnessFilter.observationNoise.variance /
        ((predictionBelief boolWitnessFilter boolWitnessPrior).family.variance +
          boolWitnessFilter.observationNoise.variance) =
      1 / 4
  rw [boolWitness_prediction_variance]
  norm_num [boolWitnessFilter]

private theorem boolWitness_controlledMean (action : Bool) :
    controlledMean boolWitnessControl
        (posteriorBelief boolWitnessFilter boolWitnessPrior 0) action = 0 := by
  change
    (boolWitnessControl.dynamics action).transitionMean
        boolWitnessControl.duration
        (posteriorMean boolWitnessFilter boolWitnessPrior 0) = 0
  rw [boolWitness_posterior_mean]
  cases action <;>
    norm_num [boolWitnessControl, boolDynamics,
      ScalarOUParameters.transitionMean, ScalarOUParameters.decay]

private theorem boolWitness_true_controlledVariance :
    controlledVariance boolWitnessControl
        (posteriorBelief boolWitnessFilter boolWitnessPrior 0) true =
      1 / 4 := by
  apply NNReal.eq
  unfold controlledVariance
  rw [show
    (posteriorBelief boolWitnessFilter boolWitnessPrior 0).family.variance =
        1 / 4 by
      change posteriorVariance boolWitnessFilter boolWitnessPrior = 1 / 4
      exact boolWitness_posterior_variance]
  simp only [NNReal.coe_add, NNReal.coe_mul, NNReal.coe_mk]
  rw [show
    (boolWitnessControl.dynamics true).decay boolWitnessControl.duration =
        Real.exp (-1) by
      norm_num [boolWitnessControl, boolDynamics_decay_one],
    show
      ((boolWitnessControl.dynamics true).transitionVariance
          boolWitnessControl.duration : ℝ) =
        (1 / 4 : ℝ) * (1 - Real.exp (-1) ^ 2) by
      norm_num [boolWitnessControl,
        boolDynamics_transitionVariance_one_real]]
  norm_num
  ring

private theorem boolWitness_false_controlledVariance :
    (controlledVariance boolWitnessControl
        (posteriorBelief boolWitnessFilter boolWitnessPrior 0) false : ℝ) =
      (1 / 2 : ℝ) - (1 / 4 : ℝ) * (Real.exp (-1)) ^ 2 := by
  unfold controlledVariance
  rw [show
    (posteriorBelief boolWitnessFilter boolWitnessPrior 0).family.variance =
        1 / 4 by
      change posteriorVariance boolWitnessFilter boolWitnessPrior = 1 / 4
      exact boolWitness_posterior_variance]
  simp only [NNReal.coe_add, NNReal.coe_mul, NNReal.coe_mk]
  rw [show
    (boolWitnessControl.dynamics false).decay boolWitnessControl.duration =
        Real.exp (-1) by
      norm_num [boolWitnessControl, boolDynamics_decay_one],
    show
      ((boolWitnessControl.dynamics false).transitionVariance
          boolWitnessControl.duration : ℝ) =
        (1 / 2 : ℝ) * (1 - Real.exp (-1) ^ 2) by
      norm_num [boolWitnessControl,
        boolDynamics_transitionVariance_one_real]]
  norm_num
  ring

/-- The lower-diffusion action preserves posterior variance one quarter. -/
theorem boolWitness_true_risk :
    filteredQuadraticRisk boolWitnessControl boolWitnessFilter
        boolWitnessPrior 0 true =
      (1 / 4 : ℝ) := by
  rw [filteredQuadraticRisk, quadraticActionRisk_eq_closedForm]
  rw [boolWitness_true_controlledVariance,
    boolWitness_controlledMean]
  norm_num [boolWitnessControl]

/-- The higher-diffusion action has its exact transition-derived risk. -/
theorem boolWitness_false_risk :
    filteredQuadraticRisk boolWitnessControl boolWitnessFilter
        boolWitnessPrior 0 false =
      (1 / 2 : ℝ) - (1 / 4 : ℝ) * (Real.exp (-1)) ^ 2 := by
  rw [filteredQuadraticRisk, quadraticActionRisk_eq_closedForm]
  rw [boolWitness_false_controlledVariance,
    boolWitness_controlledMean]
  norm_num [boolWitnessControl]

/-- The transition-derived Boolean comparison is genuinely strict. -/
theorem boolWitness_true_strictlyBetter :
    filteredQuadraticRisk boolWitnessControl boolWitnessFilter
        boolWitnessPrior 0 true <
      filteredQuadraticRisk boolWitnessControl boolWitnessFilter
        boolWitnessPrior 0 false := by
  rw [boolWitness_true_risk, boolWitness_false_risk]
  have hExpPos : 0 < Real.exp (-1) := Real.exp_pos _
  have hExpLtOne : Real.exp (-1) < 1 :=
    Real.exp_lt_one_iff.mpr (by norm_num)
  nlinarith [sq_nonneg (Real.exp (-1))]

/-- The finite minimizer selects the strictly lower-risk action. -/
theorem boolWitness_selectedAction : boolWitnessAction = true := by
  unfold boolWitnessAction
  apply selectedAction_eq_of_strict
  intro alternative hAlternative
  have hFalse : alternative = false :=
    Bool.eq_false_of_not_eq_true hAlternative
  subst alternative
  exact boolWitness_true_strictlyBetter

/-- Strict risk separation forces the two selected native transitions to
differ. -/
theorem boolWitness_actionTransitions_ne :
    actionTransition boolWitnessControl true ≠
      actionTransition boolWitnessControl false := by
  intro hTransitions
  have hRisks :
      filteredQuadraticRisk boolWitnessControl boolWitnessFilter
          boolWitnessPrior 0 true =
        filteredQuadraticRisk boolWitnessControl boolWitnessFilter
          boolWitnessPrior 0 false := by
    unfold filteredQuadraticRisk quadraticActionRisk
    rw [hTransitions]
    norm_num [boolWitnessControl]
  exact (ne_of_lt boolWitness_true_strictlyBetter) hRisks

/-- Equal action dynamics and penalties give an explicit non-unique risk tie. -/
theorem boolTie_false_true_risk_eq :
    filteredQuadraticRisk boolTieControl boolWitnessFilter
        boolWitnessPrior 0 false =
      filteredQuadraticRisk boolTieControl boolWitnessFilter
        boolWitnessPrior 0 true := by
  rfl

end

end FEPComposed.GaussianControl
