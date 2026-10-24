module
public import FepSketches.families.standalone_efe_formalizations
public import FepSketches.families.variational_duality
public import FepSketches.families.learning_theory
public import FepSketches.bayesian_model_reduction

@[expose] public section

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

/-- The endpoint predictive identity supplies the evidence premise of the endpoint odds recursion. -/
theorem fep158_masked_evidence_supplies_fep117_reduced_odds
    {Parameter Evidence : Type*} [Fintype Parameter] [Fintype Evidence]
    (prior : FiniteLaw Parameter) (weight : Parameter → ℝ)
    (kernel : FiniteKernel Parameter Evidence) (data : Evidence)
    (hw : ∀ x, 0 ≤ weight x) (hZ : 0 < ∑ x, weight x * prior x)
    (hE : 0 < maskedEvidence prior weight kernel data)
    (favored reference : Parameter) (hwref : 0 < weight reference)
    (hpref : 0 < prior reference) (hlref : 0 < kernel reference data) :
    ∃ hy : 0 < kernel.predictive (maskedPrior prior weight hw hZ) data,
      FEP.LearningTheory.posteriorOdds (maskedPrior prior weight hw hZ) kernel data hy favored reference =
        ((weight favored * prior favored) / (weight reference * prior reference)) *
          (kernel favored data / kernel reference data) := by
  have predictive := fep_fep158.FEP158.fep158_maskedPrior_predictive_eq prior weight kernel data hw hZ
  have hy : 0 < kernel.predictive (maskedPrior prior weight hw hZ) data := by
    rw [predictive]
    exact div_pos hE hZ
  have referencePositive : 0 < maskedPrior prior weight hw hZ reference :=
    div_pos (mul_pos hwref hpref) hZ
  refine ⟨hy, ?_⟩
  rw [fep_fep117.FEP117.fep117_posteriorOdds_recursion
    (maskedPrior prior weight hw hZ) kernel data hy favored reference referencePositive hlref]
  change (((weight favored * prior favored) / (∑ x, weight x * prior x)) /
    ((weight reference * prior reference) / (∑ x, weight x * prior x))) * _ = _
  rw [div_div_div_cancel_right₀ (ne_of_gt hZ)]

end FEPComposed
