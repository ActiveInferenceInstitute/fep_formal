"""Lean bodies for measure-theoretic and finite Bayesian inversion."""

from __future__ import annotations

BODIES: dict[str, str] = {
    "fep-051": """import FepSketches.measure_bayes

namespace FEP051

open MeasureTheory

variable {Ω : Type*} [MeasurableSpace Ω]

/-- Absolute continuity is sufficient for reconstruction by the native
Radon--Nikodym likelihood ratio. -/
theorem fep051_likelihoodRatio_reconstruction
    (target reference : Measure Ω)
    [target.HaveLebesgueDecomposition reference]
    (h_ac : target ≪ reference) :
    reference.withDensity (target.rnDeriv reference) = target :=
  FEP.MeasureBayes.likelihoodRatio_reconstruction target reference h_ac

/-- The same equality characterizes absolute continuity, exposing the exact
failure boundary when a singular component is present. -/
theorem fep051_reconstruction_iff_absoluteContinuous
    (target reference : Measure Ω)
    [target.HaveLebesgueDecomposition reference] :
    reference.withDensity (target.rnDeriv reference) = target ↔
      target ≪ reference :=
  (FEP.MeasureBayes.likelihoodRatio_reconstruction_iff
    target reference).symm

end FEP051
""",
    "fep-052": """import FepSketches.measure_bayes

namespace FEP052

open Filter MeasureTheory ProbabilityTheory
open scoped MeasureTheory ProbabilityTheory

variable {Parameter Observation : Type*}
  [MeasurableSpace Parameter] [MeasurableSpace Observation]
  [StandardBorelSpace Parameter] [Nonempty Parameter]
  [MeasurableSpace.CountableOrCountablyGenerated Parameter Observation]

/-- The posterior density is a likelihood-ratio tilt only almost everywhere
under the predictive observation law. -/
theorem fep052_posterior_density_tilt
    (prior : Measure Parameter) [IsFiniteMeasure prior]
    (likelihood : Kernel Parameter Observation) [IsFiniteKernel likelihood]
    (h_ac : ∀ᵐ parameter ∂prior,
      likelihood parameter ≪ likelihood ∘ₘ prior) :
    ∀ᵐ observation ∂likelihood ∘ₘ prior,
      (likelihood†prior) observation =
        prior.withDensity (fun parameter =>
          likelihood.rnDeriv
            (Kernel.const Parameter (likelihood ∘ₘ prior))
            parameter observation) :=
  FEP.MeasureBayes.posterior_density_as_likelihood_tilt h_ac

/-- For countable parameter spaces Mathlib supplies the required domination,
but the resulting density identity remains predictive-almost-everywhere. -/
theorem fep052_countable_posterior_density_tilt
    {Parameter : Type*} [Countable Parameter] [MeasurableSpace Parameter]
    [Nonempty Parameter] [StandardBorelSpace Parameter]
    (prior : Measure Parameter) [IsFiniteMeasure prior]
    (likelihood : Kernel Parameter Observation) [IsFiniteKernel likelihood] :
    ∀ᵐ observation ∂likelihood ∘ₘ prior,
      (likelihood†prior) observation =
        prior.withDensity (fun parameter =>
          (likelihood parameter).rnDeriv (likelihood ∘ₘ prior) observation) :=
  posterior_eq_withDensity_of_countable likelihood prior

end FEP052
""",
    "fep-053": """import FepSketches.measure_bayes

namespace FEP053

open FEP MeasureTheory ProbabilityTheory
open scoped MeasureTheory ProbabilityTheory

variable {Parameter Observation : Type*}
  [MeasurableSpace Parameter] [MeasurableSpace Observation]
  [StandardBorelSpace Parameter] [Nonempty Parameter]

/-- A posterior kernel reconstructs the complete swapped joint law, not only
one posterior density. -/
theorem fep053_kernelBayes_joint_reconstruction
    (prior : Measure Parameter) [IsFiniteMeasure prior]
    (likelihood : Kernel Parameter Observation) [IsFiniteKernel likelihood] :
    (likelihood ∘ₘ prior) ⊗ₘ likelihood†prior =
      (prior ⊗ₘ likelihood).map Prod.swap :=
  FEP.MeasureBayes.posterior_joint_reconstruction

/-- At a positive finite evidence atom, posterior times evidence reconstructs
the corresponding joint atom exactly. -/
theorem fep053_finiteBayes_atom_reconstruction
    {FiniteParameter FiniteEvidence : Type*}
    [Fintype FiniteParameter] [Fintype FiniteEvidence]
    (prior : FiniteLaw FiniteParameter)
    (likelihood : FiniteKernel FiniteParameter FiniteEvidence)
    (evidence : FiniteEvidence)
    (hEvidence : 0 < likelihood.predictive prior evidence)
    (parameter : FiniteParameter) :
    likelihood.posterior prior evidence hEvidence parameter *
        likelihood.predictive prior evidence =
      prior parameter * likelihood parameter evidence :=
  FEP.MeasureBayes.finite_posterior_reconstruction
    prior likelihood evidence hEvidence parameter

end FEP053
""",
    "fep-054": """import FepSketches.measure_bayes

namespace FEP054

open Filter MeasureTheory ProbabilityTheory
open scoped MeasureTheory ProbabilityTheory

variable {Parameter Observation : Type*}
  [MeasurableSpace Parameter] [MeasurableSpace Observation]
  [StandardBorelSpace Parameter] [Nonempty Parameter]

/-- Inverting a Markov likelihood twice recovers it prior-almost-everywhere,
which is the native Bayes involution law. -/
theorem fep054_bayes_involution
    (prior : Measure Parameter) [IsFiniteMeasure prior]
    (likelihood : Kernel Parameter Observation)
    [StandardBorelSpace Observation] [Nonempty Observation]
    [IsFiniteKernel likelihood] [IsMarkovKernel likelihood] :
    (likelihood†prior)†(likelihood ∘ₘ prior) =ᵐ[prior] likelihood :=
  FEP.MeasureBayes.posterior_involution

/-- The one-sided inversion law is exact as a measure equality. -/
theorem fep054_posterior_reconstructs_prior
    (prior : Measure Parameter) [IsFiniteMeasure prior]
    (likelihood : Kernel Parameter Observation)
    [IsFiniteKernel likelihood] [IsMarkovKernel likelihood] :
    likelihood†prior ∘ₘ likelihood ∘ₘ prior = prior :=
  FEP.MeasureBayes.posterior_reconstructs_prior

end FEP054
""",
    "fep-055": """import FepSketches.measure_bayes

namespace FEP055

open Filter MeasureTheory ProbabilityTheory
open scoped MeasureTheory ProbabilityTheory

variable {Parameter Intermediate Observation : Type*}
  [MeasurableSpace Parameter] [MeasurableSpace Intermediate]
  [MeasurableSpace Observation]

/-- Bayesian inversion reverses sequential kernel composition almost
everywhere under the final predictive law. -/
theorem fep055_compositeKernel_bayesInversion
    (prior : Measure Parameter) [IsFiniteMeasure prior]
    [StandardBorelSpace Parameter] [Nonempty Parameter]
    [StandardBorelSpace Intermediate] [Nonempty Intermediate]
    (earlier : Kernel Parameter Intermediate) [IsFiniteKernel earlier]
    (later : Kernel Intermediate Observation) [IsFiniteKernel later] :
    (later ∘ₖ earlier)†prior =ᵐ[later ∘ₘ earlier ∘ₘ prior]
      earlier†prior ∘ₖ later†(earlier ∘ₘ prior) :=
  FEP.MeasureBayes.posterior_composite later

/-- The predictive law of the composite is the chronological two-kernel
predictive law used as the almost-everywhere reference above. -/
theorem fep055_compositePredictive_associativity
    (prior : Measure Parameter) [IsFiniteMeasure prior]
    (earlier : Kernel Parameter Intermediate) [IsFiniteKernel earlier]
    (later : Kernel Intermediate Observation) [IsFiniteKernel later] :
    (later ∘ₖ earlier) ∘ₘ prior = later ∘ₘ earlier ∘ₘ prior := by
  rw [Measure.comp_assoc]

end FEP055
""",
    "fep-056": """import FepSketches.measure_bayes

namespace FEP056

open MeasureTheory ProbabilityTheory
open scoped ENNReal MeasureTheory

variable {Conditioning Conditioned : Type*}
  [MeasurableSpace Conditioning] [MeasurableSpace Conditioned]
  [StandardBorelSpace Conditioned] [Nonempty Conditioned]

/-- The canonical conditional kernel reconstructs every finite joint measure
whose conditioned space is standard Borel. -/
theorem fep056_standardBorel_condKernel_reconstruction
    (joint : Measure (Conditioning × Conditioned)) [IsFiniteMeasure joint] :
    joint.fst ⊗ₘ joint.condKernel = joint :=
  FEP.MeasureBayes.conditionalKernel_reconstruction joint

/-- The constructed conditional kernel is normalized at every conditioning
value, including values in a marginal null set. -/
theorem fep056_standardBorel_condKernel_mass_one
    (joint : Measure (Conditioning × Conditioned)) [IsFiniteMeasure joint]
    (conditioning : Conditioning) :
    joint.condKernel conditioning Set.univ = 1 :=
  measure_univ

end FEP056
""",
    "fep-057": """import FepSketches.measure_bayes

namespace FEP057

open MeasureTheory ProbabilityTheory
open scoped ENNReal MeasureTheory

variable {Conditioning Conditioned : Type*}
  [MeasurableSpace Conditioning] [MeasurableSpace Conditioned]
  [StandardBorelSpace Conditioned] [Nonempty Conditioned]

/-- Conditional expectation followed by marginal expectation equals the
joint expectation for every integrable real observable. -/
theorem fep057_conditionalExpectation_tower
    (joint : Measure (Conditioning × Conditioned)) [IsFiniteMeasure joint]
    {observable : Conditioning × Conditioned → ℝ}
    (hintegrable : Integrable observable joint) :
    (∫ conditioning,
        ∫ conditioned, observable (conditioning, conditioned)
          ∂joint.condKernel conditioning ∂joint.fst) =
      ∫ pair, observable pair ∂joint :=
  FEP.MeasureBayes.conditionalExpectation_tower joint hintegrable

/-- The nonnegative tower law holds without an integrability premise because
Lebesgue integration uses extended nonnegative values. -/
theorem fep057_conditionalLIntegral_tower
    (joint : Measure (Conditioning × Conditioned)) [IsFiniteMeasure joint]
    {observable : Conditioning × Conditioned → ℝ≥0∞}
    (hmeasurable : Measurable observable) :
    (∫⁻ conditioning,
        ∫⁻ conditioned, observable (conditioning, conditioned)
          ∂joint.condKernel conditioning ∂joint.fst) =
      ∫⁻ pair, observable pair ∂joint :=
  joint.lintegral_condKernel hmeasurable

end FEP057
""",
}
