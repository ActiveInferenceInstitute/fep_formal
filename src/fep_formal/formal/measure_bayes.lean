module
public import FepSketches.finite_probability
public import Mathlib.Probability.Kernel.Disintegration.Integral
public import Mathlib.Probability.Kernel.Posterior

@[expose] public section

/-!
# Measure-theoretic and finite Bayesian inversion

This module keeps the two proof scales distinct.  Native measure and kernel
results expose absolute-continuity, almost-everywhere, finiteness, and
standard-Borel assumptions.  The finite bridge reuses `FiniteLaw` and
`FiniteKernel`, where positive predictive mass is the exact support boundary.
-/

namespace FEP.MeasureBayes

open FEP Filter MeasureTheory ProbabilityTheory
open scoped ENNReal MeasureTheory ProbabilityTheory

/-! ## Likelihood-ratio reconstruction -/

variable {Ω Observation Intermediate : Type*}
  {mΩ : MeasurableSpace Ω} {mObservation : MeasurableSpace Observation}
  {mIntermediate : MeasurableSpace Intermediate}

/-- A Radon--Nikodym likelihood ratio reconstructs the dominated measure.
Absolute continuity is an explicit premise; a singular component would make
the conclusion false. -/
theorem likelihoodRatio_reconstruction (target reference : Measure Ω)
    [target.HaveLebesgueDecomposition reference]
    (h_ac : target ≪ reference) :
    reference.withDensity (target.rnDeriv reference) = target :=
  Measure.withDensity_rnDeriv_eq target reference h_ac

/-- Reconstruction by the Radon--Nikodym derivative is equivalent to absolute
continuity whenever the Lebesgue decomposition exists. -/
theorem likelihoodRatio_reconstruction_iff (target reference : Measure Ω)
    [target.HaveLebesgueDecomposition reference] :
    target ≪ reference ↔
      reference.withDensity (target.rnDeriv reference) = target :=
  Measure.absolutelyContinuous_iff_withDensity_rnDeriv_eq

/-! ## Native posterior kernels -/

variable [StandardBorelSpace Ω] [Nonempty Ω]
  {prior : Measure Ω} [IsFiniteMeasure prior]
  {likelihood : Kernel Ω Observation} [IsFiniteKernel likelihood]

/-- The posterior is a likelihood-ratio tilt of the prior almost everywhere.
The conclusion is deliberately not pointwise in the observation. -/
theorem posterior_density_as_likelihood_tilt
    [MeasurableSpace.CountableOrCountablyGenerated Ω Observation]
    (h_ac : ∀ᵐ parameter ∂prior,
      likelihood parameter ≪ likelihood ∘ₘ prior) :
    ∀ᵐ observation ∂likelihood ∘ₘ prior,
      (likelihood†prior) observation =
        prior.withDensity (fun parameter =>
          likelihood.rnDeriv
            (Kernel.const Ω (likelihood ∘ₘ prior)) parameter observation) :=
  posterior_eq_withDensity h_ac

/-- Bayesian inversion reconstructs the swapped prior--likelihood joint law. -/
theorem posterior_joint_reconstruction :
    (likelihood ∘ₘ prior) ⊗ₘ likelihood†prior =
      (prior ⊗ₘ likelihood).map Prod.swap :=
  compProd_posterior_eq_map_swap

/-- A Markov likelihood followed by its posterior reconstructs the prior. -/
theorem posterior_reconstructs_prior [IsMarkovKernel likelihood] :
    likelihood†prior ∘ₘ likelihood ∘ₘ prior = prior :=
  posterior_comp_self

/-- Bayesian inversion is involutive up to prior-almost-everywhere equality.
Both parameter and observation spaces are standard Borel. -/
theorem posterior_involution
    [StandardBorelSpace Observation] [Nonempty Observation]
    [IsMarkovKernel likelihood] :
    (likelihood†prior)†(likelihood ∘ₘ prior) =ᵐ[prior] likelihood :=
  posterior_posterior

/-- Posterior inversion reverses a composite finite kernel, almost everywhere
under the composite predictive law. -/
theorem posterior_composite
    [StandardBorelSpace Observation] [Nonempty Observation]
    (later : Kernel Observation Intermediate) [IsFiniteKernel later] :
    (later ∘ₖ likelihood)†prior =ᵐ[later ∘ₘ likelihood ∘ₘ prior]
      likelihood†prior ∘ₖ later†(likelihood ∘ₘ prior) :=
  posterior_comp

/-! ## Standard-Borel disintegration and its tower law -/

variable {Conditioned : Type*} {mConditioned : MeasurableSpace Conditioned}
  [StandardBorelSpace Conditioned] [Nonempty Conditioned]

/-- The canonical conditional kernel disintegrates a finite joint measure.
This is the maintained standard-Borel existence boundary. -/
theorem conditionalKernel_reconstruction
    (joint : Measure (Observation × Conditioned)) [IsFiniteMeasure joint] :
    joint.fst ⊗ₘ joint.condKernel = joint :=
  joint.disintegrate joint.condKernel

/-- Integrating a conditional expectation against the first marginal recovers
the joint expectation. -/
theorem conditionalExpectation_tower
    (joint : Measure (Observation × Conditioned)) [IsFiniteMeasure joint]
    {f : Observation × Conditioned → ℝ} (hf : Integrable f joint) :
    (∫ observation,
        ∫ conditioned, f (observation, conditioned) ∂joint.condKernel observation
      ∂joint.fst) = ∫ pair, f pair ∂joint :=
  joint.integral_condKernel hf

/-! ## Exact finite bridge -/

variable {Parameter Evidence : Type*}
  [Fintype Parameter] [Fintype Evidence]

/-- The finite posterior uses the same reconstruction law at every positive
evidence atom. -/
theorem finite_posterior_reconstruction
    (finitePrior : FiniteLaw Parameter)
    (finiteLikelihood : FiniteKernel Parameter Evidence)
    (evidence : Evidence)
    (hEvidence : 0 < finiteLikelihood.predictive finitePrior evidence)
    (parameter : Parameter) :
    finiteLikelihood.posterior finitePrior evidence hEvidence parameter *
        finiteLikelihood.predictive finitePrior evidence =
      finitePrior parameter * finiteLikelihood parameter evidence :=
  FiniteKernel.posterior_mul_predictive
    finitePrior finiteLikelihood evidence hEvidence parameter

/-- The positive-evidence finite posterior remains normalized. -/
theorem finite_posterior_normalized
    (finitePrior : FiniteLaw Parameter)
    (finiteLikelihood : FiniteKernel Parameter Evidence)
    (evidence : Evidence)
    (hEvidence : 0 < finiteLikelihood.predictive finitePrior evidence) :
    ∑ parameter, finiteLikelihood.posterior finitePrior evidence hEvidence parameter = 1 :=
  (finiteLikelihood.posterior finitePrior evidence hEvidence).sum_one

/-- Zero predictive mass is the exact obstruction to constructing this finite
posterior, rather than an implicit use of totalized division. -/
theorem finite_zero_evidence_boundary
    (finitePrior : FiniteLaw Parameter)
    (finiteLikelihood : FiniteKernel Parameter Evidence)
    (evidence : Evidence)
    (hzero : finiteLikelihood.predictive finitePrior evidence = 0) :
    ¬0 < finiteLikelihood.predictive finitePrior evidence := by
  rw [hzero]
  exact lt_irrefl 0

end FEP.MeasureBayes
