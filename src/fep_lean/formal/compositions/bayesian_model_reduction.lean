import FepSketches.fep_all
import FepSketches.bayesian_model_reduction

/-!
# Bayesian model reduction topic compositions

This bridge pairs the exact evidence-masking free-energy monotonicity with
the nearest finite Gibbs variational lower bound.  The conjunction keeps the
reduction carrier and the Gibbs-certificate carrier separate instead of
asserting an unproved identification.
-/

namespace FEPComposed

open FEP.BayesianModelReduction
open FEP FEP.FiniteInformation FEP.VariationalDuality Finset
open scoped BigOperators

/-- Evidence-masking free-energy monotonicity is paired with the original
finite Gibbs variational lower bound; the reduction carrier and the
Gibbs-certificate carrier remain separate. -/
theorem fep158_reductionFreeEnergy_extends_fep058_gibbsLowerBound
    {Parameter Evidence : Type*} [Fintype Parameter] [Fintype Evidence]
    (prior : FiniteLaw Parameter) (weight : Parameter → ℝ)
    (kernel : FiniteKernel Parameter Evidence) (data : Evidence)
    (hw1 : ∀ x, weight x ≤ 1)
    (hE : 0 < maskedEvidence prior weight kernel data)
    (certificate : GibbsCertificate Parameter)
    (candidate : FiniteLaw Parameter) :
    (evidenceFreeEnergy (kernel.predictive prior data) ≤
        evidenceFreeEnergy (maskedEvidence prior weight kernel data)) ∧
      (-certificate.logPartition ≤
        gibbsFreeEnergy certificate candidate) := by
  exact
    ⟨fep_fep158.FEP158.fep158_reduction_free_energy_monotone
        prior weight kernel data hw1 hE,
      fep_fep058.FEP058.fep058_gibbsVariational_lower_bound
        certificate candidate⟩

end FEPComposed
