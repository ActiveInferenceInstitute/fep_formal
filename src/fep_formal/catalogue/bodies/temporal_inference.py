"""Canonical Lean bodies for temporal and hierarchical inference."""

from __future__ import annotations

BODIES: dict[str, str] = {
    "fep-072": """import FepSketches.temporal_inference

namespace FEP072

open FEP FEP.TemporalInference Finset
open scoped BigOperators

variable {State Observation : Type*}
  [Fintype State] [Fintype Observation]

/-- One positive-evidence hidden-Markov forward update reconstructs the
predicted state-observation joint. -/
theorem fep072_forward_filtering_recursion (prior : FiniteLaw State)
    (transition : FiniteKernel State State)
    (emission : FiniteKernel State Observation) (observation : Observation)
    (hEvidence : 0 < forwardEvidence prior transition emission observation)
    (state : State) :
    forwardFilter prior transition emission observation hEvidence state *
        forwardEvidence prior transition emission observation =
      forwardPrediction prior transition state * emission state observation :=
  forwardFilter_reconstruction prior transition emission observation hEvidence state

/-- The exact asymmetric Boolean filter assigns mass `20/23` to `true`. -/
theorem fep072_bool_forward_mass : boolForwardFilter true = 20 / 23 :=
  boolForwardFilter_true_mass

/-- Zero evidence is outside the normalized forward-filter construction. -/
theorem fep072_zero_evidence_boundary (prior : FiniteLaw State)
    (transition : FiniteKernel State State)
    (emission : FiniteKernel State Observation) (observation : Observation)
    (hZero : forwardEvidence prior transition emission observation = 0) :
    ¬0 < forwardEvidence prior transition emission observation :=
  forwardEvidence_zero_boundary prior transition emission observation hZero

end FEP072
""",
    "fep-073": """import FepSketches.temporal_inference

namespace FEP073

open FEP FEP.TemporalInference

variable {State Observation : Type*}
  [Fintype State] [Fintype Observation]

/-- Backward information messages obey the exact finite future-observation
recursion. -/
theorem fep073_backward_message_recursion
    (transition : FiniteKernel State State)
    (emission : FiniteKernel State Observation) (observation : Observation)
    (future : List Observation) (state : State) :
    backwardMessage transition emission (observation :: future) state =
      backwardMessageStep transition emission observation
        (backwardMessage transition emission future) state :=
  backwardMessage_cons transition emission observation future state

/-- Nonnegative terminal information stays nonnegative under a backward step. -/
theorem fep073_backward_message_nonnegative
    (transition : FiniteKernel State State)
    (emission : FiniteKernel State Observation) (observation : Observation)
    (nextMessage : State → ℝ) (hMessage : ∀ state, 0 ≤ nextMessage state)
    (state : State) :
    0 ≤ backwardMessageStep transition emission observation nextMessage state :=
  backwardMessage_nonneg transition emission observation nextMessage hMessage state

end FEP073
""",
    "fep-074": """import FepSketches.temporal_inference

namespace FEP074

open FEP FEP.TemporalInference

variable {State : Type*} [Fintype State]

/-- At positive normalizer, a smoothing marginal factors exactly into its
forward law and backward information message. -/
theorem fep074_forwardBackward_smoothing_factorization
    (filtered : FiniteLaw State) (backward : State → ℝ)
    (hBackward : ∀ state, 0 ≤ backward state)
    (hNormalizer : 0 < smoothingNormalizer filtered backward) (state : State) :
    forwardBackwardSmoothing filtered backward hBackward hNormalizer state *
        smoothingNormalizer filtered backward =
      filtered state * backward state :=
  forwardBackwardSmoothing_factorization filtered backward hBackward hNormalizer state

/-- Forward and backward evaluation agree on one-step observation evidence. -/
theorem fep074_forward_backward_evidence_agreement
    {Observation : Type*} [Fintype Observation]
    (prior : FiniteLaw State) (transition : FiniteKernel State State)
    (emission : FiniteKernel State Observation) (observation : Observation) :
    forwardEvidence prior transition emission observation =
      backwardEvidence prior transition emission observation :=
  forward_backward_evidence_agree prior transition emission observation

end FEP074
""",
    "fep-075": """import FepSketches.temporal_inference

namespace FEP075

open FEP FEP.TemporalInference Finset
open scoped BigOperators

variable {State : Type*} [Fintype State]

/-- A positive-normalizer forward--backward smoothing marginal is normalized. -/
theorem fep075_smoothing_marginal_normalization
    (filtered : FiniteLaw State) (backward : State → ℝ)
    (hBackward : ∀ state, 0 ≤ backward state)
    (hNormalizer : 0 < smoothingNormalizer filtered backward) :
    ∑ state, forwardBackwardSmoothing filtered backward hBackward hNormalizer state =
      1 :=
  forwardBackwardSmoothing_sum_one filtered backward hBackward hNormalizer

/-- The nontrivial Boolean smoother normalizes with masses `7/46` and `39/46`. -/
theorem fep075_bool_smoothing_normalization :
    boolSmoothing false + boolSmoothing true = 1 :=
  boolSmoothing_sum_one

/-- A zero forward--backward normalizer is explicitly outside the smoother's
construction boundary. -/
theorem fep075_zero_normalizer_boundary (filtered : FiniteLaw State)
    (backward : State → ℝ) (hZero : smoothingNormalizer filtered backward = 0) :
    ¬0 < smoothingNormalizer filtered backward :=
  smoothingNormalizer_zero_boundary filtered backward hZero

end FEP075
""",
    "fep-076": """import FepSketches.temporal_inference

namespace FEP076

open FEP FEP.TemporalInference FEP.ControlledMarkov Finset
open scoped BigOperators

variable {State : Type*} [Fintype State]

/-- A prior-weighted one-step variational state update is a normalized finite
law. -/
theorem fep076_variational_state_update_normalized
    (prior : FiniteLaw State) (energy : State → ℝ) :
    ∑ state, variationalStateUpdate prior energy state = 1 :=
  variationalStateUpdate_sum_one prior energy

/-- Normalized state mass reconstructs the corresponding unnormalized
variational tilt. -/
theorem fep076_variational_state_update_reconstruction
    (prior : FiniteLaw State) (energy : State → ℝ) (state : State) :
    variationalStateUpdate prior energy state * boltzmannPartition prior energy =
      boltzmannWeight prior energy state :=
  variationalStateUpdate_reconstruction prior energy state

/-- Zero state energy is the identity variational update. -/
theorem fep076_zeroEnergy_update_eq_prior (prior : FiniteLaw State) :
    variationalStateUpdate prior (fun _ => 0) = prior :=
  variationalStateUpdate_zero_energy prior

end FEP076
""",
    "fep-077": """import FepSketches.temporal_inference

namespace FEP077

open FEP FEP.TemporalInference

variable {Upper Middle Observation : Type*}
  [Fintype Upper] [Fintype Middle] [Fintype Observation]

/-- Two-level hierarchical prediction equals prediction through the composed
normalized kernel. -/
theorem fep077_hierarchical_predictive_factorization
    (top : FiniteLaw Upper) (upperKernel : FiniteKernel Upper Middle)
    (lowerKernel : FiniteKernel Middle Observation) :
    hierarchicalPredictive top upperKernel lowerKernel =
      (FiniteKernel.comp lowerKernel upperKernel).predictive top :=
  hierarchicalPredictive_eq top upperKernel lowerKernel

end FEP077
""",
    "fep-078": """import FepSketches.temporal_inference

namespace FEP078

open FEP FEP.TemporalInference Finset
open scoped BigOperators

variable {Model Observation : Type*} [Fintype Model] [Fintype Observation]

/-- Bayesian model averaging is the finite prior-weighted predictive mixture. -/
theorem fep078_modelAverage_predictive_law (modelPrior : FiniteLaw Model)
    (modelPredictive : FiniteKernel Model Observation)
    (observation : Observation) :
    modelAverage modelPrior modelPredictive observation =
      ∑ model, modelPrior model * modelPredictive model observation :=
  modelAverage_mass modelPrior modelPredictive observation

/-- The Bayesian model-averaged predictive mixture remains normalized. -/
theorem fep078_modelAverage_normalized (modelPrior : FiniteLaw Model)
    (modelPredictive : FiniteKernel Model Observation) :
    ∑ observation, modelAverage modelPrior modelPredictive observation = 1 :=
  modelAverage_sum_one modelPrior modelPredictive

/-- A nonuniform Boolean model prior and informative predictive kernel yield
the exact nontrivial mixture mass `13/20` on `true`. -/
theorem fep078_bool_modelAverage_true_mass :
    modelAverage boolInitialLaw boolAccurateEmission true = 13 / 20 :=
  boolModelAverage_true_mass

end FEP078
""",
}
