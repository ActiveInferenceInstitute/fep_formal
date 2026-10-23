import FepSketches.empirical_risk

namespace FEP.EmpiricalRisk

section
/- Supporting Beta moment controls for the constructed Fin3 family projection. -/
set_option autoImplicit false
open MeasureTheory
namespace NonintegerMomentControls
open BetaDensity

theorem success_normalizer_ratio (a b : ℝ) (ha : 0<a) (hb : 0<b) :
    normalizer a b 1 0 = a/(a+b) := by
  have hGa := ne_of_gt (Real.Gamma_pos_of_pos ha)
  have hGb := ne_of_gt (Real.Gamma_pos_of_pos hb)
  have hGab := ne_of_gt (Real.Gamma_pos_of_pos (add_pos ha hb))
  have hab := ne_of_gt (add_pos ha hb)
  simp only [normalizer, Nat.cast_one, Nat.cast_zero, add_zero, ProbabilityTheory.beta]
  rw [show a+1+b=(a+b)+1 by ring, Real.Gamma_add_one (ne_of_gt ha),
    Real.Gamma_add_one hab]
  field_simp

theorem correct_noninteger_marginal_moment :
    ((ProbabilityTheory.betaMeasure (3/2:ℝ) (25/6:ℝ)).withDensity (likelihood 1 0)) Set.univ =
      ENNReal.ofReal (9/34:ℝ) := by
  rw [weighted_mass (by norm_num) (by norm_num) 1 0,
    success_normalizer_ratio _ _ (by norm_num) (by norm_num)]
  norm_num

theorem swapped_noninteger_marginal_refused :
    ProbabilityTheory.betaMeasure (3/2:ℝ) (25/6:ℝ) ≠
      ProbabilityTheory.betaMeasure (5/2:ℝ) (19/6:ℝ) := by
  intro h
  have hm := congrArg (fun μ : Measure ℝ => (μ.withDensity (likelihood 1 0)) Set.univ) h
  rw [weighted_mass (by norm_num) (by norm_num) 1 0,
    weighted_mass (by norm_num) (by norm_num) 1 0,
    success_normalizer_ratio _ _ (by norm_num) (by norm_num),
    success_normalizer_ratio _ _ (by norm_num) (by norm_num)] at hm
  have hr := congrArg ENNReal.toReal hm
  norm_num at hr
end NonintegerMomentControls

end

section
/- Controls of the constructed family; no Lebesgue/Jacobian identification
or log-moment theorem. -/
set_option autoImplicit false
open MeasureTheory
namespace Fin3PosteriorControls
open StickFamily StickFamilyPosterior
open NonintegerMomentControls
noncomputable section

def prior : Fin 3 → ℝ := ![1/2, 3/2, 2/3]
def counts : Fin 3 → ℕ := ![1, 0, 2]
def swappedCounts : Fin 3 → ℕ := ![2, 0, 1]
def updated : Fin 3 → ℝ := ![3/2, 3/2, 8/3]
def swapped : Fin 3 → ℝ := ![5/2, 3/2, 5/3]

theorem first_marginal (α : Fin 3 → ℝ) (hα : ∀ i, 0 < α i) :
    (family 2 α).map (Function.eval 0) =
      ProbabilityTheory.betaMeasure (α 0) (α 1 + α 2) := by
  have hm : (Function.eval 0) ∘ stickMap 2 = Function.eval (0 : Fin 2) := by
    funext v
    simp [Function.eval, stickMap]
  let : ∀ i : Fin 2, IsProbabilityMeasure
      (ProbabilityTheory.betaMeasure (α i.castSucc) (tailShape 2 α i)) :=
    fun i => ProbabilityTheory.isProbabilityMeasureBeta (hα _) (tailShape_pos 2 α hα i)
  unfold family
  rw [Measure.map_map (measurable_pi_apply 0) (measurable_stickMap 2), hm]
  unfold stickLaw
  rw [(measurePreserving_eval
    (μ := fun i : Fin 2 => ProbabilityTheory.betaMeasure (α i.castSucc) (tailShape 2 α i))
    (0 : Fin 2)).map_eq]
  congr 1
  simp only [tailShape, Finset.sum_filter, Fin.sum_univ_two]
  norm_num
  exact add_comm _ _

theorem actual_noninteger_posterior :
    (stickZ 2 prior counts)⁻¹ • (family 2 prior).withDensity
      (TailCountTransfer.categoricalLikelihood 2 counts) = family 2 updated := by
  have hα : ∀ i, 0 < prior i := by intro i; fin_cases i <;> norm_num [prior]
  have hu : (fun i => prior i + (counts i : ℝ)) = updated := by
    funext i; fin_cases i <;> norm_num [prior, counts, updated]
  simpa only [hu] using normalized_family 2 prior hα counts

theorem actual_posterior_first_marginal :
    (family 2 updated).map (Function.eval 0) =
      ProbabilityTheory.betaMeasure (3/2:ℝ) (25/6:ℝ) := by
  rw [first_marginal updated (by intro i; fin_cases i <;> norm_num [updated])]
  norm_num [updated]

theorem actual_posterior_first_moment_mass :
    (((family 2 updated).map (Function.eval 0)).withDensity
      (BetaDensity.likelihood 1 0)) Set.univ = ENNReal.ofReal (9/34:ℝ) := by
  rw [actual_posterior_first_marginal]
  exact correct_noninteger_marginal_moment

theorem actual_swapped_family_refused : family 2 updated ≠ family 2 swapped := by
  intro h
  have hm := congrArg (fun μ : Measure (Fin 3 → ℝ) => μ.map (Function.eval 0)) h
  rw [actual_posterior_first_marginal,
    first_marginal swapped (by intro i; fin_cases i <;> norm_num [swapped])] at hm
  have hs : swapped 0 = (5/2:ℝ) ∧ swapped 1 + swapped 2 = (19/6:ℝ) := by
    norm_num [swapped]
  rw [hs.1, hs.2] at hm
  exact swapped_noninteger_marginal_refused hm

def wrongTail : Fin 3 → ℝ := ![3/2, 3/2, 2/3]

theorem actual_swapped_posterior :
    (stickZ 2 prior swappedCounts)⁻¹ • (family 2 prior).withDensity
      (TailCountTransfer.categoricalLikelihood 2 swappedCounts) = family 2 swapped := by
  have hα : ∀ i, 0 < prior i := by intro i; fin_cases i <;> norm_num [prior]
  have hu : (fun i => prior i + (swappedCounts i : ℝ)) = swapped := by
    funext i; fin_cases i <;> norm_num [prior, swappedCounts, swapped]
  simpa only [hu] using normalized_family 2 prior hα swappedCounts

theorem actual_swapped_first_moment_mass :
    (((family 2 swapped).map (Function.eval 0)).withDensity
      (BetaDensity.likelihood 1 0)) Set.univ = ENNReal.ofReal (15/34:ℝ) := by
  rw [first_marginal swapped (by intro i; fin_cases i <;> norm_num [swapped])]
  rw [show swapped 0 = (5/2:ℝ) by norm_num [swapped],
    show swapped 1 + swapped 2 = (19/6:ℝ) by norm_num [swapped]]
  rw [BetaDensity.weighted_mass (by norm_num) (by norm_num) 1 0,
    success_normalizer_ratio _ _ (by norm_num) (by norm_num)]
  norm_num

theorem actual_wrong_tail_first_moment_mass :
    (((family 2 wrongTail).map (Function.eval 0)).withDensity
      (BetaDensity.likelihood 1 0)) Set.univ = ENNReal.ofReal (9/22:ℝ) := by
  rw [first_marginal wrongTail (by intro i; fin_cases i <;> norm_num [wrongTail])]
  rw [show wrongTail 0 = (3/2:ℝ) by norm_num [wrongTail],
    show wrongTail 1 + wrongTail 2 = (13/6:ℝ) by norm_num [wrongTail]]
  rw [BetaDensity.weighted_mass (by norm_num) (by norm_num) 1 0,
    success_normalizer_ratio _ _ (by norm_num) (by norm_num)]
  norm_num

theorem actual_wrong_tail_family_refused : family 2 updated ≠ family 2 wrongTail := by
  intro h
  have hm := congrArg (fun μ : Measure (Fin 3 → ℝ) =>
    ((μ.map (Function.eval 0)).withDensity (BetaDensity.likelihood 1 0)) Set.univ) h
  rw [actual_posterior_first_moment_mass, actual_wrong_tail_first_moment_mass] at hm
  have hr := congrArg ENNReal.toReal hm
  norm_num at hr

theorem zero_count_evidence : stickZ 2 prior (fun _ => 0) = 1 := by
  have hα : ∀ i, 0 < prior i := by intro i; fin_cases i <;> norm_num [prior]
  simp [stickZ, BetaProductPosterior.betaPiZ,
    StickMapLikelihood.tailCount, BetaDensity.zero_counts,
    hα, tailShape_pos 2 prior hα]

theorem zero_count_posterior :
    (stickZ 2 prior (fun _ => 0))⁻¹ • (family 2 prior).withDensity
      (TailCountTransfer.categoricalLikelihood 2 (fun _ => 0)) = family 2 prior := by
  simpa using normalized_family 2 prior
    (by intro i; fin_cases i <;> norm_num [prior]) (fun _ => 0)

theorem n0_evidence (α : Fin 1 → ℝ) (c : Fin 1 → ℕ) : stickZ 0 α c = 1 := by
  exact BetaProductPosterior.betaPiZ_empty _ _ _ _

theorem n0_family_dirac (α : Fin 1 → ℝ) (hα : ∀ i, 0 < α i) :
    family 0 α = Measure.dirac (fun _ : Fin 1 => (1 : ℝ)) := family_zero α hα

end
end Fin3PosteriorControls


end

#print axioms FEP.EmpiricalRisk.BetaDensity.normalizer_pos
#print axioms FEP.EmpiricalRisk.BetaDensity.normalizer_finite
#print axioms FEP.EmpiricalRisk.BetaDensity.likelihood_measurable
#print axioms FEP.EmpiricalRisk.BetaDensity.real_pdf_product
#print axioms FEP.EmpiricalRisk.BetaDensity.pdf_product
#print axioms FEP.EmpiricalRisk.BetaDensity.weighted_measure
#print axioms FEP.EmpiricalRisk.BetaDensity.weighted_mass
#print axioms FEP.EmpiricalRisk.BetaDensity.normalized_posterior
#print axioms FEP.EmpiricalRisk.BetaDensity.normalized_probability
#print axioms FEP.EmpiricalRisk.BetaDensity.zero_counts
#print axioms FEP.EmpiricalRisk.BetaDensity.noninteger_prior_recovery
#print axioms FEP.EmpiricalRisk.BetaDensity.noninteger_measure_recovery
#print axioms FEP.EmpiricalRisk.BetaDensity.uniform_success_normalizer
#print axioms FEP.EmpiricalRisk.BetaDensity.uniform_failure_normalizer
#print axioms FEP.EmpiricalRisk.BetaDensity.uniform_success_posterior
#print axioms FEP.EmpiricalRisk.BetaDensity.uniform_failure_posterior
#print axioms FEP.EmpiricalRisk.BetaDensity.distinct_posteriors
#print axioms FEP.EmpiricalRisk.BetaDensity.wrong_inverse_ratio
#print axioms FEP.EmpiricalRisk.BetaDensity.wrong_scaled_measure_refused
#print axioms FEP.EmpiricalRisk.BetaDensity.nonpositive_shape_refused
#print axioms FEP.EmpiricalRisk.BetaDensity.outside_pdf_zero
#print axioms FEP.EmpiricalRisk.MeasureTransport.map_likelihood_weight
#print axioms FEP.EmpiricalRisk.MeasureTransport.product_likelihood_weight
#print axioms FEP.EmpiricalRisk.StickFamily.tailShape_pos
#print axioms FEP.EmpiricalRisk.StickFamily.measurable_stickMap
#print axioms FEP.EmpiricalRisk.StickFamily.stickLaw_probability
#print axioms FEP.EmpiricalRisk.StickFamily.family_probability
#print axioms FEP.EmpiricalRisk.StickFamily.stickMap_nonneg
#print axioms FEP.EmpiricalRisk.StickFamily.stickMap_zero
#print axioms FEP.EmpiricalRisk.StickFamily.family_zero
#print axioms FEP.EmpiricalRisk.StickFamily.stickMap_sum_one
#print axioms FEP.EmpiricalRisk.StickFamily.beta_ae_Ioo
#print axioms FEP.EmpiricalRisk.StickFamily.stickLaw_ae_unit
#print axioms FEP.EmpiricalRisk.StickFamily.family_ae_simplex
#print axioms FEP.EmpiricalRisk.CategoricalLikelihood.incidence_factorization
#print axioms FEP.EmpiricalRisk.CategoricalLikelihood.three_category_pullback
#print axioms FEP.EmpiricalRisk.CategoricalLikelihood.three_category_zero_counts
#print axioms FEP.EmpiricalRisk.CategoricalLikelihood.wrong_tail_count_refused
#print axioms FEP.EmpiricalRisk.StickMapLikelihood.stickMap_incidence
#print axioms FEP.EmpiricalRisk.StickMapLikelihood.stickMap_likelihood_incidence
#print axioms FEP.EmpiricalRisk.StickMapLikelihood.headFactor_likelihood
#print axioms FEP.EmpiricalRisk.StickMapLikelihood.tailShape_update
#print axioms FEP.EmpiricalRisk.StickMapLikelihood.zero_stick_likelihood
#print axioms FEP.EmpiricalRisk.TailCountTransfer.tail_exponent_eq
#print axioms FEP.EmpiricalRisk.TailCountTransfer.real_likelihood_pullback
#print axioms FEP.EmpiricalRisk.TailCountTransfer.ofReal_product
#print axioms FEP.EmpiricalRisk.TailCountTransfer.ennreal_likelihood_pullback
#print axioms FEP.EmpiricalRisk.TailCountTransfer.ae_likelihood_pullback
#print axioms FEP.EmpiricalRisk.FinitePiWeighting.fin_pi_withDensity
#print axioms FEP.EmpiricalRisk.FinitePiWeighting.pi_scale_factors
#print axioms FEP.EmpiricalRisk.BetaProductPosterior.betaPiZ_pos_finite
#print axioms FEP.EmpiricalRisk.BetaProductPosterior.weighted_beta_pi
#print axioms FEP.EmpiricalRisk.BetaProductPosterior.normalized_beta_pi
#print axioms FEP.EmpiricalRisk.BetaProductPosterior.betaPiZ_empty
#print axioms FEP.EmpiricalRisk.StickFamilyPosterior.stickZ_pos_finite
#print axioms FEP.EmpiricalRisk.StickFamilyPosterior.weighted_stickLaw
#print axioms FEP.EmpiricalRisk.StickFamilyPosterior.weighted_family
#print axioms FEP.EmpiricalRisk.StickFamilyPosterior.weighted_family_mass
#print axioms FEP.EmpiricalRisk.StickFamilyPosterior.normalized_family
#print axioms FEP.EmpiricalRisk.NonintegerMomentControls.success_normalizer_ratio
#print axioms FEP.EmpiricalRisk.NonintegerMomentControls.correct_noninteger_marginal_moment
#print axioms FEP.EmpiricalRisk.NonintegerMomentControls.swapped_noninteger_marginal_refused
#print axioms FEP.EmpiricalRisk.Fin3PosteriorControls.first_marginal
#print axioms FEP.EmpiricalRisk.Fin3PosteriorControls.actual_noninteger_posterior
#print axioms FEP.EmpiricalRisk.Fin3PosteriorControls.actual_posterior_first_marginal
#print axioms FEP.EmpiricalRisk.Fin3PosteriorControls.actual_posterior_first_moment_mass
#print axioms FEP.EmpiricalRisk.Fin3PosteriorControls.actual_swapped_family_refused
#print axioms FEP.EmpiricalRisk.Fin3PosteriorControls.actual_swapped_posterior
#print axioms FEP.EmpiricalRisk.Fin3PosteriorControls.actual_swapped_first_moment_mass
#print axioms FEP.EmpiricalRisk.Fin3PosteriorControls.actual_wrong_tail_first_moment_mass
#print axioms FEP.EmpiricalRisk.Fin3PosteriorControls.actual_wrong_tail_family_refused
#print axioms FEP.EmpiricalRisk.Fin3PosteriorControls.zero_count_evidence
#print axioms FEP.EmpiricalRisk.Fin3PosteriorControls.zero_count_posterior
#print axioms FEP.EmpiricalRisk.Fin3PosteriorControls.n0_evidence
#print axioms FEP.EmpiricalRisk.Fin3PosteriorControls.n0_family_dirac

end FEP.EmpiricalRisk
