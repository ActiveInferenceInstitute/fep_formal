import FepSketches.fep_all
import FepSketches.perception_action_loop

/-!
# Perception-action-loop topic compositions

This bridge pairs the exact closed-loop surprisal invariant with the
controlled-kernel normalization of the nearest catalogue endpoint.  The
conjunction keeps the generative-model loop carrier and the controlled-kernel
carrier separate instead of asserting an unproved identification.
-/

namespace FEPComposed

open FEP.PerceptionActionLoop
open FEP FEP.ActiveInference FEP.ControlledMarkov FEP.FiniteInformation
  FEP.TemporalInference Finset
open scoped BigOperators

/-- The closed-loop perception-action surprisal invariant is paired with the
original action-conditioned transition-row normalization; the generative-model
and controlled-kernel carriers remain separate. -/
theorem fep157_loopInvariant_extends_fep065_controlledKernel
    {Policy State Outcome Action : Type*}
    [Fintype Policy] [Fintype State] [Fintype Outcome] [Fintype Action]
    [Nonempty Policy]
    (model : GenerativeModel Policy State Outcome) (belief : FiniteLaw State)
    (outcome : Outcome)
    (hEvidence : 0 < model.likelihood.predictive belief outcome)
    (support : FullSupport (withInitialState model
      (filteredBelief model belief outcome hEvidence)))
    (controlledTransition : ControlledKernel State Action)
    (controlledAction : Action) (controlledState : State) :
    (-Real.log (model.likelihood.predictive belief outcome) ≤
        perceptionVFE model belief outcome hEvidence belief ∧
      perceptionVFE model belief outcome hEvidence belief =
        -Real.log (model.likelihood.predictive belief outcome) +
          finiteKL belief (filteredBelief model belief outcome hEvidence) ∧
      expectedFreeEnergy
          (withInitialState model (filteredBelief model belief outcome hEvidence))
          (selectedPolicy model (filteredBelief model belief outcome hEvidence)) =
        risk (withInitialState model (filteredBelief model belief outcome hEvidence))
            (selectedPolicy model (filteredBelief model belief outcome hEvidence)) +
          ambiguity
            (withInitialState model (filteredBelief model belief outcome hEvidence))
            (selectedPolicy model (filteredBelief model belief outcome hEvidence))) ∧
      (∑ nextState, controlledTransition controlledAction controlledState nextState =
        1) := by
  exact
    ⟨fep_fep157.FEP157.fep157_loop_invariant_surprisal_bound
        model belief outcome hEvidence support,
      fep_fep065.FEP065.fep065_controlledKernel_normalization
        controlledTransition controlledAction controlledState⟩

end FEPComposed
