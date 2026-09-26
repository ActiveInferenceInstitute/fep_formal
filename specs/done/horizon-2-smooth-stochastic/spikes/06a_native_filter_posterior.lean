import FepSketches.gaussian_information_geometry
import FepSketches.scalar_gaussian_semigroup
import Mathlib.Probability.Distributions.Gaussian.Real
import Mathlib.Probability.Kernel.Posterior

/-!
# H2.6a-R0 native scalar Gaussian posterior proof spike

This non-maintained spike tests the exact density-factorization and native
posterior-uniqueness route required before the scalar Gaussian filter owner may
open. It reuses the accepted H2.1a Gaussian family and H2.5a OU transition.

Source-only freeze: H2.6a remains closed until this spike passes the serialized
native compiler lane, axiom audit, and independent probability review.
-/

namespace FEPProbe.H2_6aNativePosterior

open FEP.GaussianInformationGeometry
open FEP.ScalarGaussianSemigroup
open MeasureTheory ProbabilityTheory
open scoped ENNReal MeasureTheory NNReal ProbabilityTheory

noncomputable section

/-- A nondegenerate scalar Gaussian belief reusing the accepted H2.1a family. -/
structure ScalarGaussianBelief where
  mean : ℝ
  family : FixedVarianceGaussian

namespace ScalarGaussianBelief

/-- The belief's native H2.1a Gaussian law. -/
noncomputable def law (belief : ScalarGaussianBelief) : Measure ℝ :=
  belief.family.law belief.mean

noncomputable instance law_isProbabilityMeasure
    (belief : ScalarGaussianBelief) : IsProbabilityMeasure belief.law := by
  change IsProbabilityMeasure (gaussianReal belief.mean belief.family.variance)
  infer_instance

end ScalarGaussianBelief

/-- Raw inputs for one fixed-duration scalar prediction/update model. -/
structure ScalarGaussianFilterModel where
  dynamics : ScalarOUParameters
  stepDuration : ℝ≥0
  observationNoise : FixedVarianceGaussian

noncomputable local instance fixedVarianceGaussian_law_isProbabilityMeasure
    (family : FixedVarianceGaussian) (mean : ℝ) :
    IsProbabilityMeasure (family.law mean) := by
  change IsProbabilityMeasure (gaussianReal mean family.variance)
  infer_instance

/-- Exact H2.5a variance after evolving the prior through one OU step. -/
noncomputable def predictionVariance
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief) : ℝ≥0 :=
  NNReal.mk (model.dynamics.decay model.stepDuration ^ 2) (sq_nonneg _) *
      prior.family.variance +
    model.dynamics.transitionVariance model.stepDuration

/-- A nondegenerate prior stays nondegenerate after every nonnegative OU step. -/
theorem predictionVariance_pos
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief) :
    0 < predictionVariance model prior := by
  have hDecay : 0 < model.dynamics.decay model.stepDuration := Real.exp_pos _
  have hCoefficient :
      0 < NNReal.mk (model.dynamics.decay model.stepDuration ^ 2) (sq_nonneg _) := by
    exact_mod_cast sq_pos_of_pos hDecay
  exact add_pos_of_pos_of_nonneg
    (mul_pos hCoefficient prior.family.variance_pos)
    (model.dynamics.transitionVariance model.stepDuration).2

/-- Exact predicted Gaussian belief, with no stored prediction certificate. -/
noncomputable def predictionBelief
    (model : ScalarGaussianFilterModel)
    (prior : ScalarGaussianBelief) : ScalarGaussianBelief where
  mean := model.dynamics.transitionMean model.stepDuration prior.mean
  family :=
    { variance := predictionVariance model prior
      variance_pos := predictionVariance_pos model prior }

/-- The prediction law is exactly the accepted H2.5a OU evolution. -/
theorem predictionBelief_law_eq_ouTransition
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief) :
    model.dynamics.ouTransition model.stepDuration ∘ₘ prior.law =
      (predictionBelief model prior).law := by
  change
    model.dynamics.ouTransition model.stepDuration ∘ₘ
        gaussianReal prior.mean prior.family.variance =
      gaussianReal (model.dynamics.transitionMean model.stepDuration prior.mean)
        (predictionVariance model prior)
  simpa only [predictionVariance] using
    model.dynamics.ouTransition_comp_gaussian model.stepDuration
      prior.mean prior.family.variance

/-- H2.1a Gaussian-location observation kernel with fixed positive noise. -/
noncomputable def observationKernel
    (model : ScalarGaussianFilterModel) : Kernel ℝ ℝ where
  toFun state := model.observationNoise.law state
  measurable' := by
    change Measurable
      (Function.uncurry gaussianReal ∘
        fun state : ℝ => (state, model.observationNoise.variance))
    exact measurable_gaussianReal.comp
      (measurable_id.prodMk measurable_const)

noncomputable instance observationKernel_isMarkovKernel
    (model : ScalarGaussianFilterModel) :
    IsMarkovKernel (observationKernel model) :=
  ⟨fun state => by
    change IsProbabilityMeasure
      (gaussianReal state model.observationNoise.variance)
    infer_instance⟩

/-- Every observation row is exactly the accepted H2.1a location law. -/
theorem observationKernel_apply
    (model : ScalarGaussianFilterModel) (state : ℝ) :
    observationKernel model state = model.observationNoise.law state := rfl

/-- Predictive variance of the scalar evidence law. -/
noncomputable def innovationVariance
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief) : ℝ≥0 :=
  let predicted := predictionBelief model prior
  predicted.family.variance + model.observationNoise.variance

/-- Closed scalar Gaussian gain, derived only after prediction. -/
noncomputable def gain
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief) : ℝ :=
  let predicted := predictionBelief model prior
  (predicted.family.variance : ℝ) / (innovationVariance model prior : ℝ)

/-- Closed posterior mean at one observation. -/
noncomputable def posteriorMean
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation : ℝ) : ℝ :=
  let predicted := predictionBelief model prior
  predicted.mean + gain model prior * (observation - predicted.mean)

/-- Closed posterior variance. -/
noncomputable def posteriorVariance
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief) : ℝ≥0 :=
  let predicted := predictionBelief model prior
  predicted.family.variance * model.observationNoise.variance /
    innovationVariance model prior

/-- The evidence and update denominators are strictly positive. -/
theorem innovationVariance_pos
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief) :
    0 < innovationVariance model prior := by
  exact add_pos
    (predictionBelief model prior).family.variance_pos
    model.observationNoise.variance_pos

/-- The closed posterior remains a nondegenerate H2.1a Gaussian. -/
theorem posteriorVariance_pos
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief) :
    0 < posteriorVariance model prior := by
  exact div_pos
    (mul_pos (predictionBelief model prior).family.variance_pos
      model.observationNoise.variance_pos)
    (innovationVariance_pos model prior)

/-- H2.1a family carrying the derived posterior variance. -/
noncomputable def posteriorFamily
    (model : ScalarGaussianFilterModel)
    (prior : ScalarGaussianBelief) : FixedVarianceGaussian where
  variance := posteriorVariance model prior
  variance_pos := posteriorVariance_pos model prior

/-- Closed-form updated belief at one observation. -/
noncomputable def posteriorBelief
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation : ℝ) : ScalarGaussianBelief where
  mean := posteriorMean model prior observation
  family := posteriorFamily model prior

@[fun_prop]
private theorem measurable_posteriorMean
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief) :
    Measurable (posteriorMean model prior) := by
  unfold posteriorMean gain
  fun_prop

/-- Pointwise closed Gaussian version of the posterior kernel. -/
noncomputable def closedFormPosteriorKernel
    (model : ScalarGaussianFilterModel)
    (prior : ScalarGaussianBelief) : Kernel ℝ ℝ where
  toFun observation := (posteriorBelief model prior observation).law
  measurable' := by
    change Measurable
      (Function.uncurry gaussianReal ∘ fun observation : ℝ =>
        (posteriorMean model prior observation, posteriorVariance model prior))
    exact measurable_gaussianReal.comp (by fun_prop)

noncomputable instance closedFormPosteriorKernel_isMarkovKernel
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief) :
    IsMarkovKernel (closedFormPosteriorKernel model prior) :=
  ⟨fun observation => by
    change IsProbabilityMeasure
      (gaussianReal (posteriorMean model prior observation)
        (posteriorVariance model prior))
    infer_instance⟩

/-- H2.1a family carrying the exact Gaussian evidence variance. -/
noncomputable def evidenceFamily
    (model : ScalarGaussianFilterModel)
    (prior : ScalarGaussianBelief) : FixedVarianceGaussian where
  variance := innovationVariance model prior
  variance_pos := innovationVariance_pos model prior

/-- Actual evidence law obtained by composing prediction and observation. -/
noncomputable def evidenceLaw
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief) : Measure ℝ :=
  observationKernel model ∘ₘ (predictionBelief model prior).law

/-- Candidate Gaussian evidence density, later identified with `evidenceLaw`. -/
noncomputable def evidenceDensity
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief) : ℝ → ℝ≥0∞ :=
  let predicted := predictionBelief model prior
  (evidenceFamily model prior).density predicted.mean

private theorem gaussianPDFReal_factorization_aux
    (mean : ℝ) (prediction observation : ℝ≥0)
    (hPrediction : 0 < prediction) (hObservation : 0 < observation)
    (state datum : ℝ) :
    gaussianPDFReal mean prediction state *
        gaussianPDFReal state observation datum =
      gaussianPDFReal mean (prediction + observation) datum *
        gaussianPDFReal
          (mean + (prediction : ℝ) / (prediction + observation : ℝ) *
            (datum - mean))
          (prediction * observation / (prediction + observation)) state := by
  have hPredictionReal : 0 < (prediction : ℝ) := by exact_mod_cast hPrediction
  have hObservationReal : 0 < (observation : ℝ) := by exact_mod_cast hObservation
  have hInnovationReal : 0 < (prediction + observation : ℝ) := by positivity
  have hPosteriorReal :
      0 < (prediction * observation / (prediction + observation) : ℝ) := by
    positivity
  have hNormalizer :
      (Real.sqrt (2 * Real.pi * (prediction : ℝ)))⁻¹ *
          (Real.sqrt (2 * Real.pi * (observation : ℝ)))⁻¹ =
        (Real.sqrt (2 * Real.pi * (prediction + observation : ℝ)))⁻¹ *
          (Real.sqrt
            (2 * Real.pi *
              (prediction * observation / (prediction + observation) : ℝ)))⁻¹ := by
    rw [← mul_inv, ← mul_inv]
    congr 1
    rw [← Real.sqrt_mul (by positivity), ← Real.sqrt_mul (by positivity)]
    congr 1
    field_simp [ne_of_gt hInnovationReal]
  have hExponent :
      -(state - mean) ^ 2 / (2 * (prediction : ℝ)) +
          -(datum - state) ^ 2 / (2 * (observation : ℝ)) =
        -(datum - mean) ^ 2 / (2 * (prediction + observation : ℝ)) +
          -(state -
              (mean + (prediction : ℝ) / (prediction + observation : ℝ) *
                (datum - mean))) ^ 2 /
            (2 * (prediction * observation / (prediction + observation) : ℝ)) := by
    field_simp
      [ne_of_gt hPredictionReal, ne_of_gt hObservationReal,
        ne_of_gt hInnovationReal]
    ring
  have hExponential :
      Real.exp (-(state - mean) ^ 2 / (2 * (prediction : ℝ))) *
          Real.exp (-(datum - state) ^ 2 / (2 * (observation : ℝ))) =
        Real.exp (-(datum - mean) ^ 2 /
            (2 * (prediction + observation : ℝ))) *
          Real.exp
            (-(state -
                (mean + (prediction : ℝ) /
                  (prediction + observation : ℝ) * (datum - mean))) ^ 2 /
              (2 *
                (prediction * observation /
                  (prediction + observation) : ℝ))) := by
    rw [← Real.exp_add, ← Real.exp_add, hExponent]
  simp only [gaussianPDFReal]
  calc
    (Real.sqrt (2 * Real.pi * (prediction : ℝ)))⁻¹ *
          Real.exp (-(state - mean) ^ 2 / (2 * (prediction : ℝ))) *
        ((Real.sqrt (2 * Real.pi * (observation : ℝ)))⁻¹ *
          Real.exp (-(datum - state) ^ 2 / (2 * (observation : ℝ)))) =
        ((Real.sqrt (2 * Real.pi * (prediction : ℝ)))⁻¹ *
          (Real.sqrt (2 * Real.pi * (observation : ℝ)))⁻¹) *
          (Real.exp (-(state - mean) ^ 2 / (2 * (prediction : ℝ))) *
            Real.exp (-(datum - state) ^ 2 / (2 * (observation : ℝ)))) := by ring
    _ =
        ((Real.sqrt (2 * Real.pi * (prediction + observation : ℝ)))⁻¹ *
          (Real.sqrt
            (2 * Real.pi *
              (prediction * observation / (prediction + observation) : ℝ)))⁻¹) *
          (Real.exp (-(datum - mean) ^ 2 /
              (2 * (prediction + observation : ℝ))) *
            Real.exp
              (-(state -
                  (mean + (prediction : ℝ) /
                    (prediction + observation : ℝ) * (datum - mean))) ^ 2 /
                (2 *
                  (prediction * observation /
                    (prediction + observation) : ℝ)))) := by
      rw [hNormalizer, hExponential]
    _ =
        (Real.sqrt (2 * Real.pi * (prediction + observation : ℝ)))⁻¹ *
            Real.exp (-(datum - mean) ^ 2 /
              (2 * (prediction + observation : ℝ))) *
          ((Real.sqrt
            (2 * Real.pi *
              (prediction * observation / (prediction + observation) : ℝ)))⁻¹ *
            Real.exp
              (-(state -
                  (mean + (prediction : ℝ) /
                    (prediction + observation : ℝ) * (datum - mean))) ^ 2 /
                (2 *
                  (prediction * observation /
                    (prediction + observation) : ℝ)))) := by ring

/-- The pointwise likelihood-times-prior density factors into evidence times
the closed Gaussian posterior density. This is density positivity, not a
claim that any singleton observation has positive measure. -/
theorem gaussianPDF_factorization
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (state observation : ℝ) :
    let predicted := predictionBelief model prior
    gaussianPDF predicted.mean predicted.family.variance state *
        gaussianPDF state model.observationNoise.variance observation =
      evidenceDensity model prior observation *
        gaussianPDF (posteriorMean model prior observation)
          (posteriorVariance model prior) state := by
  dsimp only
  simp only
      [evidenceDensity, evidenceFamily, FixedVarianceGaussian.density,
        innovationVariance, posteriorMean, posteriorVariance, gain, gaussianPDF]
  rw [← ENNReal.ofReal_mul (gaussianPDFReal_nonneg _ _ _),
    ← ENNReal.ofReal_mul (gaussianPDFReal_nonneg _ _ _)]
  exact congrArg ENNReal.ofReal
    (gaussianPDFReal_factorization_aux
      (predictionBelief model prior).mean
      (predictionBelief model prior).family.variance
      model.observationNoise.variance
      (predictionBelief model prior).family.variance_pos
      model.observationNoise.variance_pos state observation)

private theorem observationKernel_eq_withDensity
    (model : ScalarGaussianFilterModel) :
    observationKernel model =
      (Kernel.const ℝ volume).withDensity
        (fun state observation =>
          gaussianPDF state model.observationNoise.variance observation) := by
  ext state
  rw [observationKernel_apply, FixedVarianceGaussian.law_eq_withDensity,
    Kernel.withDensity_apply]
  · rfl
  · fun_prop

private theorem closedFormPosteriorKernel_eq_withDensity
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief) :
    closedFormPosteriorKernel model prior =
      (Kernel.const ℝ volume).withDensity
        (fun observation state =>
          gaussianPDF (posteriorMean model prior observation)
            (posteriorVariance model prior) state) := by
  ext observation : 1
  have hApply :
      ((Kernel.const ℝ volume).withDensity
          (fun observation state =>
            gaussianPDF (posteriorMean model prior observation)
              (posteriorVariance model prior) state)) observation =
        volume.withDensity
          (gaussianPDF (posteriorMean model prior observation)
            (posteriorVariance model prior)) :=
    ProbabilityTheory.Kernel.withDensity_apply _ (by fun_prop) observation
  rw [hApply]
  change
    (posteriorFamily model prior).law (posteriorMean model prior observation) =
      volume.withDensity
        (gaussianPDF (posteriorMean model prior observation)
          (posteriorVariance model prior))
  rw [FixedVarianceGaussian.law_eq_withDensity]
  rfl

private theorem predictionObservationJoint_eq_withDensity
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief) :
    let predicted := predictionBelief model prior
    predicted.law ⊗ₘ observationKernel model =
      (volume.prod volume).withDensity (fun pair : ℝ × ℝ =>
        gaussianPDF predicted.mean predicted.family.variance pair.1 *
          gaussianPDF pair.1 model.observationNoise.variance pair.2) := by
  dsimp only
  rw [observationKernel_eq_withDensity, ScalarGaussianBelief.law,
    FixedVarianceGaussian.law_eq_withDensity]
  let _ : IsSFiniteKernel
      ((Kernel.const ℝ volume).withDensity
        (fun state observation =>
          gaussianPDF state model.observationNoise.variance observation)) :=
    ProbabilityTheory.Kernel.IsSFiniteKernel.withDensity _
      fun _ _ => gaussianPDF_ne_top
  have hPredictionDensity : Measurable
      ((predictionBelief model prior).family.density
        (predictionBelief model prior).mean) := by
    unfold FixedVarianceGaussian.density
    fun_prop
  rw [Measure.compProd_withDensity (by fun_prop), Measure.compProd_const,
    MeasureTheory.prod_withDensity_left hPredictionDensity]
  simp only [FixedVarianceGaussian.density]
  rw [← MeasureTheory.withDensity_mul (volume.prod volume) (by fun_prop) (by fun_prop)]
  rfl

private theorem gaussianEvidenceClosedFormJoint_eq_withDensity
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief) :
    let predicted := predictionBelief model prior
    (evidenceFamily model prior).law predicted.mean ⊗ₘ
        closedFormPosteriorKernel model prior =
      (volume.prod volume).withDensity (fun pair : ℝ × ℝ =>
        evidenceDensity model prior pair.1 *
          gaussianPDF (posteriorMean model prior pair.1)
            (posteriorVariance model prior) pair.2) := by
  dsimp only
  rw [closedFormPosteriorKernel_eq_withDensity,
    FixedVarianceGaussian.law_eq_withDensity]
  let _ : IsSFiniteKernel
      ((Kernel.const ℝ volume).withDensity
        (fun observation state =>
          gaussianPDF (posteriorMean model prior observation)
            (posteriorVariance model prior) state)) :=
    ProbabilityTheory.Kernel.IsSFiniteKernel.withDensity _
      fun _ _ => gaussianPDF_ne_top
  have hEvidenceDensity : Measurable
      ((evidenceFamily model prior).density (predictionBelief model prior).mean) := by
    unfold FixedVarianceGaussian.density
    fun_prop
  rw [Measure.compProd_withDensity (by fun_prop), Measure.compProd_const,
    MeasureTheory.prod_withDensity_left hEvidenceDensity]
  simp only [FixedVarianceGaussian.density, evidenceDensity]
  rw [← MeasureTheory.withDensity_mul (volume.prod volume) (by fun_prop) (by fun_prop)]
  rfl

@[fun_prop]
private theorem measurable_evidenceDensity
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief) :
    Measurable (evidenceDensity model prior) := by
  unfold evidenceDensity FixedVarianceGaussian.density
  exact measurable_gaussianPDF _ _

/-- The candidate Gaussian evidence and closed posterior reconstruct the
state-observation joint with coordinates swapped. -/
theorem gaussianEvidence_compProd_closedForm_eq_map_swap
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief) :
    let predicted := predictionBelief model prior
    (evidenceFamily model prior).law predicted.mean ⊗ₘ
        closedFormPosteriorKernel model prior =
      ((predictionBelief model prior).law ⊗ₘ observationKernel model).map
        Prod.swap := by
  dsimp only
  rw [gaussianEvidenceClosedFormJoint_eq_withDensity,
    predictionObservationJoint_eq_withDensity]
  refine Measure.ext_of_lintegral _ fun test hTest => ?_
  rw [MeasureTheory.lintegral_map hTest measurable_swap,
    MeasureTheory.lintegral_withDensity_eq_lintegral_mul _ (by fun_prop) hTest]
  change
    ∫⁻ pair,
        (evidenceDensity model prior pair.1 *
            gaussianPDF (posteriorMean model prior pair.1)
              (posteriorVariance model prior) pair.2) * test pair ∂volume.prod volume =
      ∫⁻ pair, (fun pair => test pair.swap) pair ∂
        (volume.prod volume).withDensity (fun pair : ℝ × ℝ =>
          gaussianPDF (predictionBelief model prior).mean
              (predictionBelief model prior).family.variance pair.1 *
            gaussianPDF pair.1 model.observationNoise.variance pair.2)
  have hRight :
      (∫⁻ pair, (fun pair : ℝ × ℝ => test pair.swap) pair ∂
          (volume.prod volume).withDensity (fun pair : ℝ × ℝ =>
            gaussianPDF (predictionBelief model prior).mean
                (predictionBelief model prior).family.variance pair.1 *
              gaussianPDF pair.1 model.observationNoise.variance pair.2)) =
        ∫⁻ pair,
          (gaussianPDF (predictionBelief model prior).mean
                (predictionBelief model prior).family.variance pair.1 *
              gaussianPDF pair.1 model.observationNoise.variance pair.2) *
            test pair.swap ∂volume.prod volume := by
    exact MeasureTheory.lintegral_withDensity_eq_lintegral_mul _ (by fun_prop)
      (hTest.comp measurable_swap)
  rw [hRight]
  rw [← MeasureTheory.lintegral_prod_swap
    (fun pair : ℝ × ℝ =>
      (gaussianPDF (predictionBelief model prior).mean
          (predictionBelief model prior).family.variance pair.1 *
        gaussianPDF pair.1 model.observationNoise.variance pair.2) *
        test pair.swap)]
  refine MeasureTheory.lintegral_congr fun pair => ?_
  rcases pair with ⟨observation, state⟩
  simp only [Prod.swap_prod_mk]
  rw [gaussianPDF_factorization model prior state observation]

/-- The actual evidence composition is the Gaussian candidate marginal. -/
theorem evidenceLaw_eq_gaussian
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief) :
    let predicted := predictionBelief model prior
    evidenceLaw model prior = (evidenceFamily model prior).law predicted.mean := by
  dsimp only
  have hMarginal := congrArg Measure.fst
    (gaussianEvidence_compProd_closedForm_eq_map_swap model prior)
  simpa only [Measure.fst_compProd, Measure.fst_map_swap,
    Measure.snd_compProd, evidenceLaw] using hMarginal.symm

/-- The actual evidence and closed posterior satisfy Mathlib's native joint
identity. -/
theorem closedFormPosterior_compProd_eq_map_swap
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief) :
    evidenceLaw model prior ⊗ₘ closedFormPosteriorKernel model prior =
      ((predictionBelief model prior).law ⊗ₘ observationKernel model).map
        Prod.swap := by
  rw [evidenceLaw_eq_gaussian]
  exact gaussianEvidence_compProd_closedForm_eq_map_swap model prior

/-- The closed Gaussian update is a version of Mathlib's native posterior,
and therefore is claimed only evidence-almost everywhere. -/
theorem closedFormPosterior_ae_eq_native
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief) :
    closedFormPosteriorKernel model prior =ᵐ[evidenceLaw model prior]
      ProbabilityTheory.posterior (observationKernel model)
        (predictionBelief model prior).law := by
  exact ProbabilityTheory.ae_eq_posterior_of_compProd_eq
    (κ := observationKernel model)
    (μ := (predictionBelief model prior).law)
    (η := closedFormPosteriorKernel model prior)
    (closedFormPosterior_compProd_eq_map_swap model prior)

/-- The evidence has a strictly positive Lebesgue density at every datum. -/
theorem evidenceDensity_pos
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation : ℝ) :
    0 < evidenceDensity model prior observation := by
  simpa only
      [evidenceDensity, evidenceFamily, FixedVarianceGaussian.density] using
    gaussianPDF_pos (predictionBelief model prior).mean
      (innovationVariance_pos model prior).ne' observation

/-- Pointwise evidence-density positivity excludes a zero denominator. -/
theorem evidenceDensity_ne_zero
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation : ℝ) :
    evidenceDensity model prior observation ≠ 0 :=
  (evidenceDensity_pos model prior observation).ne'

/-- Despite its positive density, the nonatomic evidence law gives every
singleton zero mass. -/
theorem evidenceLaw_singleton_eq_zero
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation : ℝ) :
    evidenceLaw model prior {observation} = 0 := by
  rw [evidenceLaw_eq_gaussian]
  let _ : NullSingletonClass
      ((evidenceFamily model prior).law (predictionBelief model prior).mean) := by
    change NullSingletonClass
      (gaussianReal (predictionBelief model prior).mean
        (innovationVariance model prior))
    exact nullSingletonClass_gaussianReal (innovationVariance_pos model prior).ne'
  exact measure_singleton observation

/-- Every row of the closed posterior has unit mass. -/
theorem closedFormPosterior_univ
    (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation : ℝ) :
    closedFormPosteriorKernel model prior observation Set.univ = 1 := by
  exact measure_univ

end

end FEPProbe.H2_6aNativePosterior
