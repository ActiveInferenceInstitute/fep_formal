import FepSketches.fep_all
import FepSketches.efe_policy_selection

/-!
# EFE policy-selection topic compositions

This bridge pairs the exact Boltzmann control-posterior minimization with the
nearest catalogue EFE-convention endpoint.  The conjunction keeps the finite
policy-law carrier and the extended-nonnegative EFE convention separate
instead of asserting an unsupported identification.
-/

namespace FEPComposed

open FEP.EFEPolicy
open FEP ActiveInference ControlledMarkov FiniteInformation PolicyTrees
  VariationalDuality Finset
open scoped BigOperators ENNReal

/-- The exact Boltzmann control-posterior minimization and uniqueness are
paired with the original truncated EFE sign convention; the finite
policy-law carrier and the extended-nonnegative convention stay separate. -/
theorem fep156_boltzmannControlPosterior_extends_fep021_efeBalance
    {Action : Type*} [Fintype Action]
    (prior : FiniteLaw Action) (prior_pos : ∀ policy, 0 < prior policy)
    (γ : ℝ) (hγ : 0 < γ) (cost : Action → ℝ) (Q : FiniteLaw Action)
    {pragmaticCost epistemicValue : ENNReal}
    (hBalance : epistemicValue ≤ pragmaticCost) :
    (efeControlObjective prior γ cost (controlPosterior prior γ cost) ≤
        efeControlObjective prior γ cost Q ∧
      (efeControlObjective prior γ cost Q =
          efeControlObjective prior γ cost (controlPosterior prior γ cost) ↔
        Q = controlPosterior prior γ cost)) ∧
      (fep_fep021.FEP021.fep021_expectedFreeEnergy pragmaticCost epistemicValue +
          epistemicValue =
        pragmaticCost) := by
  exact
    ⟨fep_fep156.FEP156.fep156_boltzmann_control_posterior_minimizes_efe
        prior prior_pos γ hγ cost Q,
      fep_fep021.FEP021.fep021_efe_epistemic_balance hBalance⟩

end FEPComposed
