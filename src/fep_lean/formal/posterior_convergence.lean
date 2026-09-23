import FepSketches.gaussian_information_geometry
import FepSketches.finite_posterior_learning
import FepSketches.measure_bayes
import Mathlib.MeasureTheory.Function.ConditionalExpectation.Basic
import Mathlib.Probability.Independence.InfinitePi
import Mathlib.MeasureTheory.Measure.ProbabilityMeasure
import Mathlib.Probability.Distributions.Gaussian.Fernique
import Mathlib.Probability.Kernel.Composition.Lemmas
import Mathlib.Probability.Kernel.CondDistrib
import Mathlib.Probability.Martingale.Convergence
import Mathlib.Probability.Process.Adapted
import Mathlib.Probability.StrongLaw

namespace FEP.PosteriorConvergence

open FEP.GaussianInformationGeometry
open Filter MeasureTheory ProbabilityTheory
open scoped ENNReal MeasureTheory NNReal ProbabilityTheory Topology

noncomputable section

/-!
This module formalizes parameter learning, not latent-state filtering.  The
single Boolean mean parameter is sampled once, then held fixed while the
conditionally i.i.d. Gaussian trajectory is observed.
-/

/-! ## Selected static-parameter Gaussian model -/

abbrev MeanHypothesis := Bool

abbrev GaussianObservation := ℝ

abbrev GaussianTrajectory := ℕ → GaussianObservation

abbrev GaussianSample := MeanHypothesis × GaussianTrajectory

abbrev GaussianPrefix (n : ℕ) := Set.Iic n → GaussianObservation

noncomputable def selectedGaussianFamily : FixedVarianceGaussian where
  variance := 1
  variance_pos := by norm_num

def selectedMean : MeanHypothesis → ℝ
  | false => 0
  | true => 1

noncomputable def selectedObservationLaw
    (hypothesis : MeanHypothesis) : Measure GaussianObservation :=
  selectedGaussianFamily.law (selectedMean hypothesis)

noncomputable instance selectedObservationLaw_isProbabilityMeasure
    (hypothesis : MeanHypothesis) :
    IsProbabilityMeasure (selectedObservationLaw hypothesis) := by
  unfold selectedObservationLaw FixedVarianceGaussian.law
  infer_instance

noncomputable def selectedObservationKernel :
    Kernel MeanHypothesis GaussianObservation :=
  Kernel.boolKernel (selectedObservationLaw false) (selectedObservationLaw true)

noncomputable instance selectedObservationKernel_isMarkovKernel :
    IsMarkovKernel selectedObservationKernel := by
  unfold selectedObservationKernel
  infer_instance

noncomputable def selectedMeanPrior : Measure MeanHypothesis :=
  FEP.NativeBlanket.embeddedLaw FEP.FinitePosteriorLearning.selectedPrior

noncomputable instance selectedMeanPrior_isProbabilityMeasure :
    IsProbabilityMeasure selectedMeanPrior := by
  unfold selectedMeanPrior
  infer_instance

noncomputable def selectedTrajectoryLaw
    (hypothesis : MeanHypothesis) : Measure GaussianTrajectory :=
  Measure.infinitePi fun _ : ℕ => selectedObservationLaw hypothesis

noncomputable instance selectedTrajectoryLaw_isProbabilityMeasure
    (hypothesis : MeanHypothesis) :
    IsProbabilityMeasure (selectedTrajectoryLaw hypothesis) := by
  unfold selectedTrajectoryLaw
  infer_instance

noncomputable def selectedTrajectoryKernel :
    Kernel MeanHypothesis GaussianTrajectory :=
  Kernel.boolKernel (selectedTrajectoryLaw false) (selectedTrajectoryLaw true)

noncomputable instance selectedTrajectoryKernel_isMarkovKernel :
    IsMarkovKernel selectedTrajectoryKernel := by
  unfold selectedTrajectoryKernel
  infer_instance

noncomputable def selectedJointLaw : Measure GaussianSample :=
  selectedMeanPrior ⊗ₘ selectedTrajectoryKernel

noncomputable instance selectedJointLaw_isProbabilityMeasure :
    IsProbabilityMeasure selectedJointLaw := by
  unfold selectedJointLaw
  infer_instance

def observation (index : ℕ) (sample : GaussianSample) : GaussianObservation :=
  sample.2 index

def observationPrefix (n : ℕ) (path : GaussianTrajectory) : GaussianPrefix n :=
  fun index => path index

private theorem observation_stronglyMeasurable (index : ℕ) :
    StronglyMeasurable (observation index) := by
  unfold observation
  fun_prop

private theorem observationPrefix_measurable (n : ℕ) :
    Measurable (observationPrefix n) := by
  unfold observationPrefix
  fun_prop

noncomputable def finiteObservationLaw
    (n : ℕ) (hypothesis : MeanHypothesis) : Measure (GaussianPrefix n) :=
  (selectedTrajectoryLaw hypothesis).map (observationPrefix n)

noncomputable instance finiteObservationLaw_isProbabilityMeasure
    (n : ℕ) (hypothesis : MeanHypothesis) :
    IsProbabilityMeasure (finiteObservationLaw n hypothesis) := by
  unfold finiteObservationLaw
  exact (Measure.isProbabilityMeasure_map_iff
    (observationPrefix_measurable n).aemeasurable).mpr (by infer_instance)

noncomputable def finiteObservationKernel (n : ℕ) :
    Kernel MeanHypothesis (GaussianPrefix n) :=
  selectedTrajectoryKernel.map (observationPrefix n)

noncomputable instance finiteObservationKernel_isMarkovKernel (n : ℕ) :
    IsMarkovKernel (finiteObservationKernel n) := by
  refine ⟨fun hypothesis => ?_⟩
  unfold finiteObservationKernel
  rw [Kernel.map_apply _ (observationPrefix_measurable n)]
  exact (Measure.isProbabilityMeasure_map_iff
    (observationPrefix_measurable n).aemeasurable).mpr (by infer_instance)

noncomputable def finitePosteriorKernel (n : ℕ) :
    Kernel (GaussianPrefix n) MeanHypothesis :=
  (finiteObservationKernel n)†selectedMeanPrior

noncomputable instance finitePosteriorKernel_isMarkovKernel (n : ℕ) :
    IsMarkovKernel (finitePosteriorKernel n) := by
  unfold finitePosteriorKernel
  infer_instance

noncomputable def observationFiltration :
    Filtration ℕ (inferInstance : MeasurableSpace GaussianSample) :=
  Filtration.natural observation observation_stronglyMeasurable

def selectedParameterIndicator (sample : GaussianSample) : ℝ :=
  if sample.1 = true then 1 else 0

private theorem selectedParameterIndicator_eq_indicator :
    selectedParameterIndicator =
      ((fun sample : GaussianSample => sample.1) ⁻¹' {true}).indicator
        (fun _ => (1 : ℝ)) := by
  funext sample
  by_cases h : sample.1 = true <;> simp [selectedParameterIndicator, h]

noncomputable def posteriorProbability (n : ℕ) (sample : GaussianSample) : ℝ :=
  ((finitePosteriorKernel n) (observationPrefix n sample.2)).real {true}

noncomputable def posteriorLimit (sample : GaussianSample) : ℝ :=
  selectedJointLaw[
    selectedParameterIndicator | ⨆ n, observationFiltration n] sample

/-! ## Finite-dimensional laws and the native posterior bridge -/

theorem selectedMeans_ne : selectedMean false ≠ selectedMean true := by
  norm_num [selectedMean]

theorem selectedObservationKernel_apply (hypothesis : MeanHypothesis) :
    selectedObservationKernel hypothesis = selectedObservationLaw hypothesis := by
  cases hypothesis <;> rfl

theorem selectedTrajectoryCoordinate_map
    (hypothesis : MeanHypothesis) (index : ℕ) :
    (selectedTrajectoryLaw hypothesis).map (fun path => path index) =
      selectedObservationLaw hypothesis := by
  simpa [selectedTrajectoryLaw] using
    (Measure.infinitePi_map_eval
      (fun _ : ℕ => selectedObservationLaw hypothesis) index)

theorem finiteObservationLaw_eq_pi
    (n : ℕ) (hypothesis : MeanHypothesis) :
    finiteObservationLaw n hypothesis =
      Measure.pi (fun _ : Set.Iic n => selectedObservationLaw hypothesis) := by
  unfold finiteObservationLaw selectedTrajectoryLaw
  calc
    (Measure.infinitePi fun _ : ℕ => selectedObservationLaw hypothesis).map
          (observationPrefix n) =
        Measure.infinitePi
          (fun _ : Set.Iic n => selectedObservationLaw hypothesis) := by
      rw [← Measure.infinitePi_map_restrict'
        (μ := fun _ : ℕ => selectedObservationLaw hypothesis)
        (I := Set.Iic n)]
      apply Measure.map_congr
      exact Filter.Eventually.of_forall fun path => by
        funext index
        rfl
    _ = Measure.pi
        (fun _ : Set.Iic n => selectedObservationLaw hypothesis) :=
      Measure.infinitePi_eq_pi
        (fun _ : Set.Iic n => selectedObservationLaw hypothesis)

theorem finiteObservationKernel_apply
    (n : ℕ) (hypothesis : MeanHypothesis) :
    finiteObservationKernel n hypothesis = finiteObservationLaw n hypothesis := by
  unfold finiteObservationKernel finiteObservationLaw
  rw [Kernel.map_apply _ (observationPrefix_measurable n)]
  cases hypothesis <;> rfl

theorem selectedJointLaw_map_parameterPrefix (n : ℕ) :
    selectedJointLaw.map
        (fun sample => (sample.1, observationPrefix n sample.2)) =
      selectedMeanPrior ⊗ₘ finiteObservationKernel n := by
  unfold selectedJointLaw finiteObservationKernel
  rw [Measure.compProd_map (observationPrefix_measurable n)]
  apply Measure.map_congr
  exact Filter.Eventually.of_forall fun _ => rfl

theorem observationFiltration_eq_comapPrefix (n : ℕ) :
    observationFiltration n =
      MeasurableSpace.comap
        (fun sample => observationPrefix n sample.2) inferInstance := by
  unfold observationFiltration
  rw [Filtration.natural_eq_comap]
  congr

private theorem selectedJointLaw_map_observationPrefix (n : ℕ) :
    selectedJointLaw.map (fun sample => observationPrefix n sample.2) =
      finiteObservationKernel n ∘ₘ selectedMeanPrior := by
  calc
    selectedJointLaw.map (fun sample => observationPrefix n sample.2) =
        (selectedJointLaw.map
          (fun sample => (sample.1, observationPrefix n sample.2))).snd := by
      symm
      exact Measure.snd_map_prodMk measurable_fst
        ((observationPrefix_measurable n).comp measurable_snd)
    _ = (selectedMeanPrior ⊗ₘ finiteObservationKernel n).snd := by
      rw [selectedJointLaw_map_parameterPrefix]
    _ = finiteObservationKernel n ∘ₘ selectedMeanPrior :=
      Measure.snd_compProd _ _

private theorem selectedJointLaw_map_prefixParameter (n : ℕ) :
    selectedJointLaw.map
        (fun sample => (observationPrefix n sample.2, sample.1)) =
      selectedJointLaw.map (fun sample => observationPrefix n sample.2) ⊗ₘ
        finitePosteriorKernel n := by
  calc
    selectedJointLaw.map
        (fun sample => (observationPrefix n sample.2, sample.1)) =
        (selectedJointLaw.map
          (fun sample => (sample.1, observationPrefix n sample.2))).map
            Prod.swap := by
      have hPair : Measurable
          (fun sample : GaussianSample =>
            (sample.1, observationPrefix n sample.2)) :=
        measurable_fst.prodMk
          ((observationPrefix_measurable n).comp measurable_snd)
      rw [Measure.map_map (by fun_prop) hPair]
      apply Measure.map_congr
      exact Filter.Eventually.of_forall fun _ => rfl
    _ = (selectedMeanPrior ⊗ₘ finiteObservationKernel n).map Prod.swap := by
      rw [selectedJointLaw_map_parameterPrefix]
    _ = (finiteObservationKernel n ∘ₘ selectedMeanPrior) ⊗ₘ
        finitePosteriorKernel n := by
      exact (FEP.MeasureBayes.posterior_joint_reconstruction
        (prior := selectedMeanPrior)
        (likelihood := finiteObservationKernel n)).symm
    _ = selectedJointLaw.map (fun sample => observationPrefix n sample.2) ⊗ₘ
        finitePosteriorKernel n := by
      rw [selectedJointLaw_map_observationPrefix]

private theorem finitePosteriorKernel_ae_eq_condDistrib (n : ℕ) :
    condDistrib (fun sample : GaussianSample => sample.1)
        (fun sample => observationPrefix n sample.2) selectedJointLaw =ᵐ[
          selectedJointLaw.map (fun sample => observationPrefix n sample.2)]
      finitePosteriorKernel n :=
  condDistrib_ae_eq_of_measure_eq_compProd_of_measurable
    ((observationPrefix_measurable n).comp measurable_snd) measurable_fst
      (selectedJointLaw_map_prefixParameter n)

/-- The native Bayesian posterior mass is a version of the conditional
expectation of the selected static-parameter indicator.  The equality is
necessarily prior-predictive-joint almost everywhere. -/
theorem posteriorProbability_ae_eq_condExp (n : ℕ) :
    posteriorProbability n =ᵐ[selectedJointLaw]
      selectedJointLaw[
        selectedParameterIndicator | observationFiltration n] := by
  have hPosterior := ae_of_ae_map
    (μ := selectedJointLaw)
    ((observationPrefix_measurable n).comp measurable_snd).aemeasurable
    (finitePosteriorKernel_ae_eq_condDistrib n)
  have hCondExp := condDistrib_ae_eq_condExp
    (μ := selectedJointLaw)
    (X := fun sample : GaussianSample => observationPrefix n sample.2)
    (Y := fun sample : GaussianSample => sample.1)
    (s := {true}) ((observationPrefix_measurable n).comp measurable_snd)
      measurable_fst (by measurability)
  filter_upwards [hPosterior, hCondExp] with sample hPosterior hCondExp
  calc
    posteriorProbability n sample =
        (condDistrib (fun state : GaussianSample => state.1)
          (fun state => observationPrefix n state.2) selectedJointLaw
            (observationPrefix n sample.2)).real {true} := by
      unfold posteriorProbability
      exact congrArg (fun measure : Measure MeanHypothesis => measure.real {true})
        (by simpa only [Function.comp_apply] using hPosterior.symm)
    _ = (selectedJointLaw⟦
          (fun state : GaussianSample => state.1) ⁻¹' {true} |
          MeasurableSpace.comap
            (fun state => observationPrefix n state.2) inferInstance⟧) sample :=
      hCondExp
    _ = selectedJointLaw[
          selectedParameterIndicator | observationFiltration n] sample := by
      rw [observationFiltration_eq_comapPrefix,
        selectedParameterIndicator_eq_indicator]

/-! ## Posterior martingale and Lévy upward limit -/

theorem posteriorProbability_stronglyAdapted :
    StronglyAdapted observationFiltration posteriorProbability := by
  intro n
  rw [observationFiltration_eq_comapPrefix]
  exact
    (((finitePosteriorKernel n).measurable_coe
      (measurableSet_singleton true)).ennreal_toReal.comp
        (Measurable.of_comap_le le_rfl)).stronglyMeasurable

theorem posteriorProbability_integrable (n : ℕ) :
    Integrable (posteriorProbability n) selectedJointLaw :=
  integrable_condExp.congr (posteriorProbability_ae_eq_condExp n).symm

theorem posteriorProbability_mem_Icc (n : ℕ) (sample : GaussianSample) :
    posteriorProbability n sample ∈ Set.Icc (0 : ℝ) 1 := by
  exact ⟨measureReal_nonneg, measureReal_le_one⟩

theorem posteriorProbability_martingale :
    Martingale posteriorProbability observationFiltration selectedJointLaw := by
  exact
    (martingale_condExp selectedParameterIndicator observationFiltration
      selectedJointLaw).congr posteriorProbability_stronglyAdapted
        (fun n => (posteriorProbability_ae_eq_condExp n).symm)

theorem posteriorProbability_tendsto_ae :
    ∀ᵐ sample ∂selectedJointLaw,
      Tendsto (fun n => posteriorProbability n sample) atTop
        (𝓝 (posteriorLimit sample)) := by
  filter_upwards
    [ae_all_iff.2 (fun n => posteriorProbability_ae_eq_condExp n),
      MeasureTheory.tendsto_ae_condExp
        (μ := selectedJointLaw) (ℱ := observationFiltration)
        selectedParameterIndicator]
    with sample hPosterior hCondExp
  exact hCondExp.congr'
    (Filter.Eventually.of_forall fun n => (hPosterior n).symm)

/-! ## Horizon-1 regression boundary -/

theorem finitePosterior_eventualContraction_regression
    (prior : FEP.FiniteLaw FEP.FinitePosteriorLearning.Hypothesis)
    (truthPriorPositive :
      0 < prior FEP.FinitePosteriorLearning.truthHypothesis)
    (margin : ℝ) (marginPositive : 0 < margin)
    (marginBelowGap :
      margin < FEP.FinitePosteriorLearning.identificationGap) :
    ∀ᵐ path ∂FEP.FinitePosteriorLearning.trajectoryLaw,
      ∀ᶠ sampleCount in atTop,
        FEP.FinitePosteriorLearning.posteriorAfter
            prior path sampleCount false ≤
          FEP.FinitePosteriorLearning.priorBadOdds prior *
            Real.exp
              (-((sampleCount : ℝ) *
                (FEP.FinitePosteriorLearning.identificationGap - margin))) :=
  FEP.FinitePosteriorLearning.posteriorBadMass_eventually_contracts
    prior truthPriorPositive margin marginPositive marginBelowGap

/-! ## Identification and posterior consistency -/

/-- The two selected Gaussian observation laws are separated by their
distinct means. -/
theorem selectedObservationLaws_ne :
    selectedObservationLaw false ≠ selectedObservationLaw true := by
  intro hLaws
  exact selectedMeans_ne (selectedGaussianFamily.law_injective hLaws)

/-- Both selected hypotheses have positive mass under the fixed fair prior. -/
theorem selectedMeanPrior_positive (hypothesis : MeanHypothesis) :
    0 < selectedMeanPrior.real {hypothesis} := by
  cases hypothesis <;>
    simp [selectedMeanPrior, FEP.FinitePosteriorLearning.selectedPrior,
      FEP.DecisionRisk.boolFairLaw]

/-- The fixed fair prior gives the selected `true` hypothesis positive mass. -/
theorem selectedMeanPrior_true_pos :
    0 < selectedMeanPrior.real {true} := by
  exact selectedMeanPrior_positive true

private def prefixEmpiricalMean
    (n : ℕ) (observedPrefix : GaussianPrefix n) : ℝ :=
  (n : ℝ)⁻¹ * ∑ index : Fin n, observedPrefix ⟨index, index.isLt.le⟩

private def trajectoryEmpiricalMean
    (n : ℕ) (path : GaussianTrajectory) : ℝ :=
  prefixEmpiricalMean n (observationPrefix n path)

private def sampleEmpiricalMean (n : ℕ) (sample : GaussianSample) : ℝ :=
  trajectoryEmpiricalMean n sample.2

private theorem trajectoryEmpiricalMean_measurable (n : ℕ) :
    Measurable (trajectoryEmpiricalMean n) := by
  unfold trajectoryEmpiricalMean prefixEmpiricalMean observationPrefix
  fun_prop

private theorem prefixEmpiricalMean_measurable (n : ℕ) :
    Measurable (prefixEmpiricalMean n) := by
  unfold prefixEmpiricalMean
  fun_prop

private theorem trajectoryEmpiricalMean_tendsto
    (hypothesis : MeanHypothesis) :
    ∀ᵐ path ∂selectedTrajectoryLaw hypothesis,
      Tendsto (fun n => trajectoryEmpiricalMean n path) atTop
        (𝓝 (selectedMean hypothesis)) := by
  let coordinates : ℕ → GaussianTrajectory → ℝ := fun index path => path index
  have hIndependent :
      Pairwise (Function.onFun
        (fun left right => left ⟂ᵢ[selectedTrajectoryLaw hypothesis] right)
        coordinates) := by
    intro left right hne
    exact (iIndepFun_infinitePi
      (P := fun _ : ℕ => selectedObservationLaw hypothesis)
      (X := fun _ observation => observation) (by fun_prop)).indepFun hne
  have hIdenticallyDistributed : ∀ index,
      IdentDistrib (coordinates index) (coordinates 0)
        (selectedTrajectoryLaw hypothesis)
        (selectedTrajectoryLaw hypothesis) := by
    intro index
    refine ⟨(by fun_prop), (by fun_prop), ?_⟩
    rw [selectedTrajectoryCoordinate_map, selectedTrajectoryCoordinate_map]
  have hCoordinateIntegrable :
      Integrable (coordinates 0) (selectedTrajectoryLaw hypothesis) := by
    have hIdentity : Integrable id (selectedObservationLaw hypothesis) := by
      unfold selectedObservationLaw FixedVarianceGaussian.law
      exact IsGaussian.integrable_id
    have hMapped :
        Integrable id
          ((selectedTrajectoryLaw hypothesis).map (coordinates 0)) := by
      rwa [selectedTrajectoryCoordinate_map]
    simpa [coordinates, Function.comp_def] using
      hMapped.comp_aemeasurable (by fun_prop)
  have hMean :
      ∫ path, coordinates 0 path ∂selectedTrajectoryLaw hypothesis =
        selectedMean hypothesis := by
    calc
      ∫ path, coordinates 0 path ∂selectedTrajectoryLaw hypothesis =
          ∫ observation, observation ∂
            (selectedTrajectoryLaw hypothesis).map (fun path => path 0) := by
        exact (integral_map
          ((by fun_prop : Measurable
            (fun path : GaussianTrajectory => path 0)).aemeasurable)
          stronglyMeasurable_id.aestronglyMeasurable).symm
      _ = ∫ observation, observation ∂selectedObservationLaw hypothesis := by
        rw [selectedTrajectoryCoordinate_map]
      _ = selectedMean hypothesis := by
        unfold selectedObservationLaw FixedVarianceGaussian.law
        exact integral_id_gaussianReal
  filter_upwards
    [strong_law_ae coordinates hCoordinateIntegrable hIndependent
      hIdenticallyDistributed]
    with path hPath
  rw [hMean] at hPath
  simpa [trajectoryEmpiricalMean, prefixEmpiricalMean, observationPrefix,
    coordinates, Fin.sum_univ_eq_sum_range, smul_eq_mul] using hPath

private theorem sampleEmpiricalMean_tendsto_set_measurable :
    MeasurableSet {sample : GaussianSample |
      Tendsto (fun n => sampleEmpiricalMean n sample) atTop
        (𝓝 (selectedMean sample.1))} := by
  have hFalse : MeasurableSet {path : GaussianTrajectory |
      Tendsto (fun n => trajectoryEmpiricalMean n path) atTop (𝓝 0)} :=
    measurableSet_tendsto (𝓝 0) trajectoryEmpiricalMean_measurable
  have hTrue : MeasurableSet {path : GaussianTrajectory |
      Tendsto (fun n => trajectoryEmpiricalMean n path) atTop (𝓝 1)} :=
    measurableSet_tendsto (𝓝 1) trajectoryEmpiricalMean_measurable
  convert (measurableSet_singleton false).prod hFalse |>.union
    ((measurableSet_singleton true).prod hTrue) using 1
  ext sample
  rcases sample with ⟨hypothesis, path⟩
  cases hypothesis <;> simp [sampleEmpiricalMean, selectedMean]

private theorem sampleEmpiricalMean_tendsto_ae :
    ∀ᵐ sample ∂selectedJointLaw,
      Tendsto (fun n => sampleEmpiricalMean n sample) atTop
        (𝓝 (selectedMean sample.1)) := by
  refine Measure.ae_compProd_of_ae_ae
    sampleEmpiricalMean_tendsto_set_measurable ?_
  exact Filter.Eventually.of_forall fun hypothesis => by
    change ∀ᵐ path ∂selectedTrajectoryKernel hypothesis,
      Tendsto (fun n => trajectoryEmpiricalMean n path) atTop
        (𝓝 (selectedMean hypothesis))
    have hKernel :
        selectedTrajectoryKernel hypothesis = selectedTrajectoryLaw hypothesis := by
      cases hypothesis <;> rfl
    rw [hKernel]
    exact trajectoryEmpiricalMean_tendsto hypothesis

private def empiricalParameterIndicator
    (n : ℕ) (sample : GaussianSample) : ℝ :=
  if (1 / 2 : ℝ) < sampleEmpiricalMean n sample then 1 else 0

private theorem empiricalParameterIndicator_stronglyMeasurable
    (n : ℕ) :
    @StronglyMeasurable GaussianSample ℝ
      _ (⨆ n, observationFiltration n) (empiricalParameterIndicator n) := by
  have hPrefix : @Measurable GaussianSample (GaussianPrefix n)
      (⨆ n, observationFiltration n) _
      (fun sample => observationPrefix n sample.2) := by
    apply Measurable.of_comap_le
    rw [← observationFiltration_eq_comapPrefix n]
    exact le_iSup observationFiltration n
  have hMean : @Measurable GaussianSample ℝ
      (⨆ n, observationFiltration n) _ (sampleEmpiricalMean n) := by
    change @Measurable GaussianSample ℝ
      (⨆ n, observationFiltration n) _
      (fun sample => prefixEmpiricalMean n (observationPrefix n sample.2))
    exact (prefixEmpiricalMean_measurable n).comp hPrefix
  exact Measurable.ite (measurableSet_lt measurable_const hMean)
    measurable_const measurable_const
    |>.stronglyMeasurable

private theorem empiricalParameterIndicator_tendsto_ae :
    ∀ᵐ sample ∂selectedJointLaw,
      Tendsto (fun n => empiricalParameterIndicator n sample) atTop
        (𝓝 (selectedParameterIndicator sample)) := by
  filter_upwards [sampleEmpiricalMean_tendsto_ae] with sample hMean
  rcases sample with ⟨hypothesis, path⟩
  cases hypothesis
  · simp only [selectedMean] at hMean
    apply tendsto_const_nhds.congr'
    filter_upwards [hMean.eventually_lt_const (by norm_num : (0 : ℝ) < 1 / 2)]
      with n hn
    have hnot : ¬(1 / 2 : ℝ) < trajectoryEmpiricalMean n path :=
      not_lt_of_ge hn.le
    change (0 : ℝ) = if (1 / 2 : ℝ) < trajectoryEmpiricalMean n path then 1 else 0
    rw [ite_eq_right hnot]
  · simp only [selectedMean] at hMean
    apply tendsto_const_nhds.congr'
    filter_upwards [hMean.eventually_const_lt (by norm_num : (1 / 2 : ℝ) < 1)]
      with n hn
    have hpos : (1 / 2 : ℝ) < trajectoryEmpiricalMean n path := by
      simpa [sampleEmpiricalMean] using hn
    change (1 : ℝ) = if (1 / 2 : ℝ) < trajectoryEmpiricalMean n path then 1 else 0
    rw [ite_eq_left hpos]

private noncomputable def limitingObservationIndicator
    (sample : GaussianSample) : ℝ :=
  limUnder atTop (fun n => empiricalParameterIndicator n sample)

private theorem limitingObservationIndicator_stronglyMeasurable :
    @StronglyMeasurable GaussianSample ℝ _
      (⨆ n, observationFiltration n) limitingObservationIndicator := by
  let _ : MeasurableSpace GaussianSample := ⨆ n, observationFiltration n
  exact StronglyMeasurable.limUnder
    empiricalParameterIndicator_stronglyMeasurable

private theorem limitingObservationIndicator_ae_eq_parameter :
    limitingObservationIndicator =ᵐ[selectedJointLaw]
      selectedParameterIndicator := by
  filter_upwards [empiricalParameterIndicator_tendsto_ae] with sample hSample
  exact hSample.limUnder_eq

private theorem selectedParameterIndicator_integrable :
    Integrable selectedParameterIndicator selectedJointLaw := by
  rw [selectedParameterIndicator_eq_indicator]
  exact (integrable_const (1 : ℝ)).indicator
    ((measurableSet_singleton true).preimage measurable_fst)

/-- The H2.3a limiting-observation conditional expectation is the hidden
parameter indicator almost everywhere.  This is the identification step;
martingale convergence alone did not establish it. -/
theorem limitingObservation_identifies_parameter :
    posteriorLimit =ᵐ[selectedJointLaw] selectedParameterIndicator := by
  unfold posteriorLimit
  have hMeasurableSpace :
      (⨆ n, observationFiltration n) ≤
        (inferInstance : MeasurableSpace GaussianSample) :=
    iSup_le fun n => observationFiltration.le n
  have hLimitIntegrable :
      Integrable limitingObservationIndicator selectedJointLaw :=
    selectedParameterIndicator_integrable.congr
      limitingObservationIndicator_ae_eq_parameter.symm
  calc
    selectedJointLaw[
        selectedParameterIndicator | ⨆ n, observationFiltration n] =ᵐ[
          selectedJointLaw]
        selectedJointLaw[
          limitingObservationIndicator | ⨆ n, observationFiltration n] :=
      condExp_congr_ae limitingObservationIndicator_ae_eq_parameter.symm
    _ =ᵐ[selectedJointLaw] limitingObservationIndicator :=
      Filter.Eventually.of_forall fun sample => congrFun
        (condExp_of_stronglyMeasurable hMeasurableSpace
          limitingObservationIndicator_stronglyMeasurable hLimitIntegrable) sample
    _ =ᵐ[selectedJointLaw] selectedParameterIndicator :=
      limitingObservationIndicator_ae_eq_parameter

/-- Under the selected positive prior and distinct Gaussian means, posterior
mass on `true` converges to one exactly when `true` was sampled. -/
theorem posteriorProbability_consistent_ae :
    ∀ᵐ sample ∂selectedJointLaw,
      Tendsto (fun n => posteriorProbability n sample) atTop
        (𝓝 (selectedParameterIndicator sample)) := by
  filter_upwards [posteriorProbability_tendsto_ae,
    limitingObservation_identifies_parameter] with sample hPosterior hIdentify
  simpa [hIdentify] using hPosterior

/-- Positive mass on each selected hypothesis extracts joint-law consistency
to each fixed truth-conditional Gaussian trajectory law. -/
theorem posteriorProbability_consistent_under_selectedTrajectoryLaw
    (hypothesis : MeanHypothesis) :
    ∀ᵐ path ∂selectedTrajectoryLaw hypothesis,
      Tendsto (fun n => posteriorProbability n (hypothesis, path)) atTop
        (𝓝 (if hypothesis then 1 else 0)) := by
  have hRows := Measure.ae_ae_of_ae_compProd posteriorProbability_consistent_ae
  have hAtom : selectedMeanPrior {hypothesis} ≠ 0 := by
    intro hZero
    have hPositive := selectedMeanPrior_positive hypothesis
    rw [Measure.real_def, hZero] at hPositive
    simp at hPositive
  have hRow := (ae_iff_of_countable.mp hRows) hypothesis hAtom
  have hKernel :
      selectedTrajectoryKernel hypothesis = selectedTrajectoryLaw hypothesis := by
    cases hypothesis <;> rfl
  rw [hKernel] at hRow
  filter_upwards [hRow] with path hPath
  simpa [selectedParameterIndicator] using hPath

/-! ## Weak convergence and bounded decision risk -/

/-- Probability-measure view of the native finite-prefix parameter posterior. -/
noncomputable def parameterPosterior
    (n : ℕ) (sample : GaussianSample) : ProbabilityMeasure MeanHypothesis :=
  ⟨finitePosteriorKernel n (observationPrefix n sample.2), inferInstance⟩

/-- Dirac probability measure at the parameter sampled in the joint model. -/
noncomputable def trueParameterLaw
    (sample : GaussianSample) : ProbabilityMeasure MeanHypothesis :=
  ⟨Measure.dirac sample.1, inferInstance⟩

private theorem parameterPosterior_true_mass
    (n : ℕ) (sample : GaussianSample) :
    (parameterPosterior n sample : Measure MeanHypothesis).real {true} =
      posteriorProbability n sample := by
  rfl

private theorem parameterPosterior_false_mass
    (n : ℕ) (sample : GaussianSample) :
    (parameterPosterior n sample : Measure MeanHypothesis).real {false} =
      1 - posteriorProbability n sample := by
  have hComplement := measureReal_compl
    (μ := (parameterPosterior n sample : Measure MeanHypothesis))
    (measurableSet_singleton true)
  have hSets : ({true} : Set MeanHypothesis)ᶜ = {false} := by
    ext hypothesis
    cases hypothesis <;> simp
  have hUniv :
      (parameterPosterior n sample : Measure MeanHypothesis).real Set.univ = 1 := by
    rw [Measure.real_def, measure_univ]
    simp
  rw [hSets, hUniv, parameterPosterior_true_mass] at hComplement
  exact hComplement

private theorem integral_parameterPosterior_eq
    (n : ℕ) (sample : GaussianSample)
    (f : BoundedContinuousFunction MeanHypothesis ℝ) :
    ∫ hypothesis, f hypothesis ∂(parameterPosterior n sample :
        ProbabilityMeasure MeanHypothesis) =
      posteriorProbability n sample * f true +
        (1 - posteriorProbability n sample) * f false := by
  rw [integral_fintype (f.integrable _), Fintype.sum_bool,
    parameterPosterior_true_mass, parameterPosterior_false_mass]
  simp [smul_eq_mul]

/-- The native parameter posterior converges weakly to the Dirac law at the
sampled Gaussian mean hypothesis. -/
theorem parameterPosterior_tendsto_dirac_ae :
    ∀ᵐ sample ∂selectedJointLaw,
      Tendsto (fun n => parameterPosterior n sample) atTop
        (𝓝 (trueParameterLaw sample)) := by
  filter_upwards [posteriorProbability_consistent_ae] with sample hPosterior
  apply ProbabilityMeasure.tendsto_iff_forall_integral_tendsto.mpr
  intro f
  rw [show (∫ hypothesis, f hypothesis ∂(trueParameterLaw sample :
      ProbabilityMeasure MeanHypothesis)) = f sample.1 by
    simp [trueParameterLaw]]
  rcases sample with ⟨hypothesis, path⟩
  cases hypothesis
  · simp [selectedParameterIndicator] at hPosterior
    have hComplement :=
      (tendsto_const_nhds : Tendsto (fun _ : ℕ => (1 : ℝ)) atTop (𝓝 1)).sub
        hPosterior
    simpa only [integral_parameterPosterior_eq, zero_mul, zero_add, sub_zero,
      one_mul] using
      (hPosterior.mul_const (f true)).add
        (hComplement.mul_const (f false))
  · simp [selectedParameterIndicator] at hPosterior
    have hComplement :=
      (tendsto_const_nhds : Tendsto (fun _ : ℕ => (1 : ℝ)) atTop (𝓝 1)).sub
        hPosterior
    simpa only [integral_parameterPosterior_eq, one_mul, sub_self, zero_mul,
      add_zero] using
      (hPosterior.mul_const (f true)).add
        (hComplement.mul_const (f false))

/-- Weak convergence transfers to every bounded continuous real observable
of the Boolean parameter.  This makes no claim about unbounded observables. -/
theorem boundedContinuousPosteriorExpectation_tendsto_ae
    (f : BoundedContinuousFunction MeanHypothesis ℝ) :
    ∀ᵐ sample ∂selectedJointLaw,
      Tendsto
        (fun n => ∫ hypothesis, f hypothesis ∂(parameterPosterior n sample :
          ProbabilityMeasure MeanHypothesis)) atTop
        (𝓝 (f sample.1)) := by
  filter_upwards [parameterPosterior_tendsto_dirac_ae] with sample hPosterior
  have hIntegral :=
    (ProbabilityMeasure.tendsto_iff_forall_integral_tendsto.mp hPosterior) f
  simpa [trueParameterLaw] using hIntegral

/-- Optimal zero-one Bayes risk for the Boolean parameter posterior. -/
noncomputable def posteriorDecisionRisk
    (n : ℕ) (sample : GaussianSample) : ℝ :=
  min (posteriorProbability n sample) (1 - posteriorProbability n sample)

/-- The selected zero-one posterior Bayes risk is genuinely bounded. -/
theorem posteriorDecisionRisk_mem_Icc
    (n : ℕ) (sample : GaussianSample) :
    posteriorDecisionRisk n sample ∈ Set.Icc (0 : ℝ) (1 / 2) := by
  have hPosterior := posteriorProbability_mem_Icc n sample
  constructor
  · exact le_min hPosterior.1 (sub_nonneg.mpr hPosterior.2)
  · rcases le_total (posteriorProbability n sample) (1 / 2 : ℝ) with h | h
    · exact (min_le_left _ _).trans h
    · exact (min_le_right _ _).trans (by linarith)

/-- Identification and consistency drive the bounded zero-one Bayes risk to
zero almost everywhere. -/
theorem posteriorDecisionRisk_tendsto_zero_ae :
    ∀ᵐ sample ∂selectedJointLaw,
      Tendsto (fun n => posteriorDecisionRisk n sample) atTop (𝓝 0) := by
  filter_upwards [posteriorProbability_consistent_ae] with sample hPosterior
  have hComplement :=
    (tendsto_const_nhds : Tendsto (fun _ : ℕ => (1 : ℝ)) atTop (𝓝 1)).sub
      hPosterior
  have hRisk := hPosterior.min hComplement
  rcases sample with ⟨hypothesis, path⟩
  cases hypothesis <;>
    simpa [posteriorDecisionRisk, selectedParameterIndicator] using hRisk

/-! ## Same-law nonidentifiable boundary -/

/-- Countermodel in which both hypotheses emit the same selected Gaussian
law, making the observation executable but nonidentifying. -/
noncomputable def nonidentifiableObservationKernel :
    Kernel MeanHypothesis GaussianObservation :=
  Kernel.const MeanHypothesis (selectedObservationLaw false)

noncomputable instance nonidentifiableObservationKernel_isMarkovKernel :
    IsMarkovKernel nonidentifiableObservationKernel := by
  unfold nonidentifiableObservationKernel
  infer_instance

/-- Native posterior for the same-law countermodel. -/
noncomputable def nonidentifiablePosteriorKernel :
    Kernel GaussianObservation MeanHypothesis :=
  nonidentifiableObservationKernel†selectedMeanPrior

noncomputable instance nonidentifiablePosteriorKernel_isMarkovKernel :
    IsMarkovKernel nonidentifiablePosteriorKernel := by
  unfold nonidentifiablePosteriorKernel
  infer_instance

theorem nonidentifiableObservationKernel_apply
    (hypothesis : MeanHypothesis) :
    nonidentifiableObservationKernel hypothesis =
      selectedObservationLaw false := by
  rfl

/-- With identical Gaussian rows, Mathlib's native posterior remains the
prior for evidence-almost every executable observation. -/
theorem nonidentifiablePosterior_eq_prior_ae :
    ∀ᵐ observation ∂selectedObservationLaw false,
      nonidentifiablePosteriorKernel observation = selectedMeanPrior := by
  have hPosterior := ProbabilityTheory.ae_eq_posterior_of_compProd_eq
    (κ := nonidentifiableObservationKernel) (μ := selectedMeanPrior)
    (η := Kernel.const GaussianObservation selectedMeanPrior) (by
      unfold nonidentifiableObservationKernel
      rw [Measure.const_comp, measure_univ, one_smul,
        Measure.compProd_const, Measure.compProd_const, Measure.prod_swap])
  have hEvidence :
      nonidentifiableObservationKernel ∘ₘ selectedMeanPrior =
        selectedObservationLaw false := by
    unfold nonidentifiableObservationKernel
    rw [Measure.const_comp, measure_univ, one_smul]
  rw [hEvidence] at hPosterior
  filter_upwards [hPosterior.symm] with observation hObservation
  simpa [nonidentifiableObservationKernel, nonidentifiablePosteriorKernel]
    using hObservation

end

end FEP.PosteriorConvergence
