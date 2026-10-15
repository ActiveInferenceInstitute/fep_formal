module
public import FepSketches.fep_all
public import FepSketches.measure_bayes
public import FepSketches.variational_duality

@[expose] public section

/-!
# Measure and variational topic compositions

These theorems expose the precise seams between the measure-native Bayesian
topics, the finite variational topics, and the original catalogue.  A
conjunction is used where the old and new topics deliberately have different
carriers; it records both certified laws without claiming an unproved coercion
between `FiniteLaw`, real-valued finite KL, and Mathlib's measure-valued KL.
-/

namespace FEPComposed

open FEP FEP.FiniteInformation FEP.VariationalDuality
open Filter MeasureTheory ProbabilityTheory Finset
open scoped BigOperators ENNReal MeasureTheory ProbabilityTheory

/-- Radon--Nikodym reconstruction and posterior joint reconstruction are the
measure-level reconstruction laws on either side of Bayesian inversion. -/
theorem fep051_rn_reconstruction_refines_fep017
    {Parameter Observation : Type*}
    [MeasurableSpace Parameter] [MeasurableSpace Observation]
    [StandardBorelSpace Parameter] [Nonempty Parameter]
    (target reference : Measure Parameter)
    [target.HaveLebesgueDecomposition reference]
    (hAbsoluteContinuous : target ≪ reference)
    (likelihood : Kernel Parameter Observation)
    [IsFiniteMeasure target] [IsFiniteKernel likelihood] :
    reference.withDensity (target.rnDeriv reference) = target ∧
      (likelihood ∘ₘ target) ⊗ₘ
          fep_fep017.FEP017.fep017_posterior likelihood target =
        (target ⊗ₘ likelihood).map Prod.swap := by
  exact
    ⟨fep_fep051.FEP051.fep051_likelihoodRatio_reconstruction
        target reference hAbsoluteContinuous,
      fep_fep017.FEP017.fep017_posterior_joint_reconstruction
        likelihood target⟩

/-- On a countable latent carrier, both topic surfaces certify the same
predictive-almost-everywhere likelihood-ratio representation. -/
theorem fep052_posterior_tilt_is_fep017_posterior
    {Parameter Observation : Type*}
    [Countable Parameter]
    [MeasurableSpace Parameter] [MeasurableSpace Observation]
    [StandardBorelSpace Parameter] [Nonempty Parameter]
    [StandardBorelSpace Observation] [Nonempty Observation]
    [MeasurableSpace.CountableOrCountablyGenerated Parameter Observation]
    (prior : Measure Parameter) [IsFiniteMeasure prior]
    (likelihood : Kernel Parameter Observation) [IsFiniteKernel likelihood] :
    (∀ᵐ observation ∂likelihood ∘ₘ prior,
        (likelihood†prior) observation =
          prior.withDensity (fun parameter =>
            (likelihood parameter).rnDeriv
              (likelihood ∘ₘ prior) observation)) ∧
      (∀ᵐ observation ∂likelihood ∘ₘ prior,
        fep_fep017.FEP017.fep017_posterior likelihood prior observation =
          prior.withDensity (fun parameter =>
            (likelihood parameter).rnDeriv
              (likelihood ∘ₘ prior) observation)) := by
  exact
    ⟨fep_fep052.FEP052.fep052_countable_posterior_density_tilt
        prior likelihood,
      fep_fep017.FEP017.fep017_posterior_bayes_density likelihood prior⟩

/-- Kernel Bayes and fep-017 reconstruct the same swapped joint law, with the
new topic keeping the native posterior notation visible. -/
theorem fep053_joint_reconstruction_extends_fep017
    {Parameter Observation : Type*}
    [MeasurableSpace Parameter] [MeasurableSpace Observation]
    [StandardBorelSpace Parameter] [Nonempty Parameter]
    (prior : Measure Parameter) [IsFiniteMeasure prior]
    (likelihood : Kernel Parameter Observation) [IsFiniteKernel likelihood] :
    ((likelihood ∘ₘ prior) ⊗ₘ likelihood†prior =
        (prior ⊗ₘ likelihood).map Prod.swap) ∧
      ((likelihood ∘ₘ prior) ⊗ₘ
          fep_fep017.FEP017.fep017_posterior likelihood prior =
        (prior ⊗ₘ likelihood).map Prod.swap) := by
  exact
    ⟨fep_fep053.FEP053.fep053_kernelBayes_joint_reconstruction
        prior likelihood,
      fep_fep017.FEP017.fep017_posterior_joint_reconstruction
        likelihood prior⟩

/-- Native Bayes involution recovers the original likelihood
prior-almost-everywhere, while the fep-017 posterior recovers the prior as an
exact measure equality. -/
theorem fep054_involution_of_fep017_posterior
    {Parameter Observation : Type*}
    [MeasurableSpace Parameter] [MeasurableSpace Observation]
    [StandardBorelSpace Parameter] [Nonempty Parameter]
    [StandardBorelSpace Observation] [Nonempty Observation]
    (prior : Measure Parameter) [IsFiniteMeasure prior]
    (likelihood : Kernel Parameter Observation)
    [IsFiniteKernel likelihood] [IsMarkovKernel likelihood] :
    ((likelihood†prior)†(likelihood ∘ₘ prior) =ᵐ[prior] likelihood) ∧
      (fep_fep017.FEP017.fep017_posterior likelihood prior ∘ₘ
          likelihood ∘ₘ prior = prior) := by
  exact
    ⟨fep_fep054.FEP054.fep054_bayes_involution prior likelihood,
      fep_fep017.FEP017.fep017_posterior_recovers_prior likelihood prior⟩

/-- Composite Bayesian inversion uses exactly the chronological predictive
law identified by fep-019's measure--kernel associativity theorem. -/
theorem fep055_composite_inversion_uses_fep019
    {Parameter Intermediate Observation : Type*}
    [MeasurableSpace Parameter] [MeasurableSpace Intermediate]
    [MeasurableSpace Observation]
    [StandardBorelSpace Parameter] [Nonempty Parameter]
    [StandardBorelSpace Intermediate] [Nonempty Intermediate]
    (prior : Measure Parameter) [IsFiniteMeasure prior]
    (earlier : Kernel Parameter Intermediate) [IsFiniteKernel earlier]
    (later : Kernel Intermediate Observation) [IsFiniteKernel later] :
    ((later ∘ₖ earlier)†prior =ᵐ[later ∘ₘ earlier ∘ₘ prior]
        earlier†prior ∘ₖ later†(earlier ∘ₘ prior)) ∧
      (later ∘ₘ
          fep_fep019.FEP019.fep019_priorPredictive earlier prior =
        fep_fep019.FEP019.fep019_priorPredictive
          (later ∘ₖ earlier) prior) := by
  exact
    ⟨fep_fep055.FEP055.fep055_compositeKernel_bayesInversion
        prior earlier later,
      fep_fep019.FEP019.fep019_priorPredictive_assoc
        earlier later prior⟩

/-- Standard-Borel disintegration reconstructs its joint, while fep-017
certifies the corresponding posterior reconstruction for an arbitrary
finite likelihood model. -/
theorem fep056_disintegration_supplies_fep017
    {Conditioning Conditioned Parameter Observation : Type*}
    [MeasurableSpace Conditioning] [MeasurableSpace Conditioned]
    [StandardBorelSpace Conditioned] [Nonempty Conditioned]
    [MeasurableSpace Parameter] [MeasurableSpace Observation]
    [StandardBorelSpace Parameter] [Nonempty Parameter]
    (joint : Measure (Conditioning × Conditioned)) [IsFiniteMeasure joint]
    (prior : Measure Parameter) [IsFiniteMeasure prior]
    (likelihood : Kernel Parameter Observation) [IsFiniteKernel likelihood] :
    (joint.fst ⊗ₘ joint.condKernel = joint) ∧
      ((likelihood ∘ₘ prior) ⊗ₘ
          fep_fep017.FEP017.fep017_posterior likelihood prior =
        (prior ⊗ₘ likelihood).map Prod.swap) := by
  exact
    ⟨fep_fep056.FEP056.fep056_standardBorel_condKernel_reconstruction joint,
      fep_fep017.FEP017.fep017_posterior_joint_reconstruction
        likelihood prior⟩

/-- The conditional-expectation tower integrates any integrable observable;
fep-015 supplies measurability for its canonical variational integrand. -/
theorem fep057_tower_integrates_fep015
    {Conditioning Conditioned : Type*}
    [MeasurableSpace Conditioning] [MeasurableSpace Conditioned]
    [StandardBorelSpace Conditioned] [Nonempty Conditioned]
    (joint : Measure (Conditioning × Conditioned)) [IsFiniteMeasure joint]
    {observable energy logApproximation logGenerative :
      Conditioning × Conditioned → ℝ}
    (hIntegrable : Integrable observable joint)
    (hEnergy : Measurable energy)
    (hApproximation : Measurable logApproximation)
    (hGenerative : Measurable logGenerative) :
    ((∫ conditioning,
        ∫ conditioned, observable (conditioning, conditioned)
          ∂joint.condKernel conditioning ∂joint.fst) =
      ∫ pair, observable pair ∂joint) ∧
      Measurable
        (fep_fep015.FEP015.fep015_variationalIntegrand
          energy logApproximation logGenerative) := by
  exact
    ⟨fep_fep057.FEP057.fep057_conditionalExpectation_tower
        joint hIntegrable,
      fep_fep015.FEP015.fep015_variationalIntegrand_measurable
        hEnergy hApproximation hGenerative⟩

/-- The finite Gibbs lower bound and fep-001's native KL upper bound expose
the same nonnegative-gap architecture without equating their scalar carriers. -/
theorem fep058_gibbs_gap_is_fep001_kl
    {State Native : Type*} [Fintype State]
    [MeasurableSpace Native]
    (certificate : GibbsCertificate State) (candidate : FiniteLaw State)
    (approximation posterior : Measure Native) (surprisal : ENNReal) :
    -certificate.logPartition ≤ gibbsFreeEnergy certificate candidate ∧
      surprisal ≤
        fep_fep001.FEP001.fep001_variationalUpperBound
          approximation posterior surprisal := by
  exact
    ⟨fep_fep058.FEP058.fep058_gibbsVariational_lower_bound
        certificate candidate,
      fep_fep001.FEP001.fep001_variationalUpperBound_ge
        approximation posterior surprisal⟩

/-- Equality in the finite Donsker--Varadhan bound and zero native KL each
separate the relevant optimizer, with their distinct support regimes visible. -/
theorem fep059_dv_equality_is_fep001_exactness
    {State Native : Type*} [Fintype State]
    [MeasurableSpace Native]
    (certificate : GibbsCertificate State) (candidate : FiniteLaw State)
    (approximation posterior : Measure Native)
    [IsFiniteMeasure approximation] [IsFiniteMeasure posterior] :
    (dvObjective certificate candidate = certificate.logPartition ↔
        candidate = certificate.optimizer) ∧
      (fep_fep001.FEP001.fep001_variationalGap approximation posterior = 0 ↔
        approximation = posterior) := by
  exact
    ⟨fep_fep059.FEP059.fep059_donskerVaradhan_equality_iff
        certificate candidate,
      fep_fep001.FEP001.fep001_variationalGap_eq_zero_iff
        approximation posterior⟩

/-- The coordinate decomposition supplies the nonnegative remainder required
by fep-002 and therefore turns the finite joint ELBO into an actual bound. -/
theorem fep060_coordinate_elbo_refines_fep002
    {Latent Observation : Type*}
    [Fintype Latent] [Fintype Observation]
    (actualPrior referencePrior : FiniteLaw Latent)
    (actualKernel referenceKernel : FiniteKernel Latent Observation)
    (hPrior : ∀ latent, 0 < referencePrior latent)
    (hKernel : ∀ latent observation,
      0 < referenceKernel latent observation) :
    (jointELBO actualPrior referencePrior actualKernel referenceKernel =
        -finiteKL actualPrior referencePrior -
          conditionalKL actualPrior actualKernel referenceKernel) ∧
      jointELBO actualPrior referencePrior actualKernel referenceKernel ≤
        -finiteKL actualPrior referencePrior := by
  have hDecomposition :=
    fep_fep060.FEP060.fep060_coordinateELBO_decomposition
      actualPrior referencePrior actualKernel referenceKernel hPrior hKernel
  have hConditional :=
    fep_fep060.FEP060.fep060_coordinateKL_nonnegative
      actualPrior actualKernel referenceKernel
  refine ⟨hDecomposition, ?_⟩
  apply fep_fep002.FEP002.fep002_elbo_bound
    (-finiteKL actualPrior referencePrior)
    (jointELBO actualPrior referencePrior actualKernel referenceKernel)
    (conditionalKL actualPrior actualKernel referenceKernel)
  · linarith
  · exact hConditional

/-- Finite mean-field optimality and measure-native KL exactness are recorded
together while preserving their intentionally different zero-mass semantics. -/
theorem fep061_meanField_gap_is_fep014_kl
    {Fixed Coordinate Native : Type*}
    [Fintype Fixed] [Fintype Coordinate] [MeasurableSpace Native]
    (fixed : FiniteLaw Fixed) (candidate target : FiniteLaw Coordinate)
    (hFixed : ∀ value, 0 < fixed value)
    (hTarget : ∀ value, 0 < target value)
    (approximation posterior : Measure Native)
    [IsFiniteMeasure approximation] [IsFiniteMeasure posterior] :
    (meanFieldCoordinateFreeEnergy fixed candidate target = 0 ↔
        candidate = target) ∧
      (InformationTheory.klDiv approximation posterior = 0 ↔
        approximation = posterior) := by
  exact
    ⟨fep_fep061.FEP061.fep061_meanFieldCoordinate_optimum_iff
        fixed candidate target hFixed hTarget,
      fep_fep014.FEP014.fep014_kl_eq_zero_iff
        approximation posterior⟩

/-- The fixed-sample IWAE inequality and fep-035's strict two-point Jensen
law expose respectively the weak and strict finite logarithmic boundaries. -/
theorem fep062_iwae_jensen_uses_fep035
    {Sample : Type*} [Fintype Sample]
    (sampling : FiniteLaw Sample) (weight : Sample → ℝ)
    (hWeight : ∀ sample, 0 < weight sample)
    {x y a b : ℝ} (hx : 0 < x) (hy : 0 < y) (hxy : x ≠ y)
    (ha : 0 < a) (hb : 0 < b) (hab : a + b = 1) :
    (∑ sample, sampling sample * Real.log (weight sample) ≤
        Real.log (∑ sample, sampling sample * weight sample)) ∧
      (a * Real.log x + b * Real.log y <
        Real.log (a * x + b * y)) := by
  exact
    ⟨fep_fep062.FEP062.fep062_fixedSample_importanceJensen
        sampling weight hWeight,
      fep_fep035.FEP035.fep035_log_jensen_two_strict
        hx hy hxy ha hb hab⟩

/-- Finite-channel contraction is paired with the native nonnegativity of the
pre-channel KL quantity; no unsupported finite-to-measure identification is
introduced. -/
theorem fep063_channel_dpi_bounds_fep014
    {Input Output Native : Type*}
    [Fintype Input] [Fintype Output] [Nonempty Input]
    [MeasurableSpace Native]
    (actual reference : FiniteLaw Input)
    (channel : FiniteKernel Input Output)
    (hActual : ∀ input, 0 < actual input)
    (hReference : ∀ input, 0 < reference input)
    (hChannel : ∀ input output, 0 < channel input output)
    (nativeActual nativeReference : Measure Native) :
    finiteKL (channel.predictive actual) (channel.predictive reference) ≤
        finiteKL actual reference ∧
      0 ≤ InformationTheory.klDiv nativeActual nativeReference := by
  exact
    ⟨fep_fep063.FEP063.fep063_finiteChannel_klDataProcessing
        actual reference channel hActual hReference hChannel,
      fep_fep014.FEP014.fep014_kl_nonneg nativeActual nativeReference⟩

/-- Rate--distortion weak duality is accompanied by the measure-native
nonnegativity law for the mutual-information ingredient's KL semantics. -/
theorem fep064_rateDistortion_uses_fep041_mutualInformation
    {Source Code Native : Type*}
    [Fintype Source] [Fintype Code] [MeasurableSpace Native]
    (joint : FiniteLaw (Source × Code))
    (distortion : Source → Code → ℝ)
    (multiplier rateLower distortionLower : ℝ)
    (hMultiplier : 0 ≤ multiplier)
    (hRate : rateLower ≤ mutualInformation joint)
    (hDistortion : distortionLower ≤ expectedDistortion joint distortion)
    (posterior prior : Measure Native) :
    rateLower + multiplier * distortionLower ≤
        rateDistortionLagrangian joint distortion multiplier ∧
      0 ≤ fep_fep041.FEP041.fep041_informationGain posterior prior := by
  exact
    ⟨fep_fep064.FEP064.fep064_rateDistortion_weakDuality
        joint distortion multiplier rateLower distortionLower
        hMultiplier hRate hDistortion,
      fep_fep041.FEP041.fep041_informationGain_nonneg posterior prior⟩

end FEPComposed
