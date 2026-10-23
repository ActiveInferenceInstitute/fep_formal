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
end FEP.EmpiricalRisk


set_option autoImplicit false
open MeasureTheory
open scoped BigOperators
namespace FEP.EmpiricalRisk.ConditioningRowProductProposal
open StickFamily StickFamilyPosterior TailCountTransfer
noncomputable section
def rowPriors : Fin 2 → Fin 3 → ℝ := ![Fin3PosteriorControls.prior, ![3/2,1/2,2/3]]
def rowCounts : Fin 2 → Fin 3 → ℕ := ![Fin3PosteriorControls.counts, ![0,2,1]]

theorem actual_two_distinct_rows :
    (matrixZ 2 2 rowPriors rowCounts)⁻¹ •
      (Measure.pi (fun r => family 2 (rowPriors r))).withDensity
        (fun A => ∏ r, categoricalLikelihood 2 (rowCounts r) (A r)) =
      Measure.pi (fun r => family 2 (fun j => rowPriors r j+(rowCounts r j:ℝ))) := by
  exact normalized_rows 2 2 rowPriors (by intro r j; fin_cases r <;> fin_cases j <;> norm_num [rowPriors, Fin3PosteriorControls.prior]) rowCounts

theorem zero_rows_normalizer (α : Fin 0 → Fin 3 → ℝ) (c : Fin 0 → Fin 3 → ℕ) :
    matrixZ 0 2 α c = 1 := by simp [matrixZ]

-- Imported genuine measure inequalities for row0, not just different shape vectors.
theorem row0_swapped_refused : family 2 Fin3PosteriorControls.updated ≠
    family 2 Fin3PosteriorControls.swapped := Fin3PosteriorControls.actual_swapped_family_refused

theorem row0_wrong_tail_refused : family 2 Fin3PosteriorControls.updated ≠
    family 2 Fin3PosteriorControls.wrongTail := Fin3PosteriorControls.actual_wrong_tail_family_refused

end
end FEP.EmpiricalRisk.ConditioningRowProductProposal

namespace FEP.EmpiricalRisk.ConditioningRowProductProposal
open StickFamily StickFamilyPosterior Fin3PosteriorControls
noncomputable section

/-- Row projection derived from the finite product measure. -/
theorem row_projection (m k : ℕ) (α : Fin m → Fin (k+1) → ℝ)
    (hα : ∀ r j, 0<α r j) (r : Fin m) :
    (Measure.pi (fun r => family k (α r))).map (Function.eval r) = family k (α r) := by
  let : ∀ r, IsProbabilityMeasure (family k (α r)) := fun r => family_probability k (α r) (hα r)
  exact (measurePreserving_eval (μ := fun r => family k (α r)) r).map_eq

def matrixCounts : Fin 2 → Fin 3 → ℕ := ![counts, ![2,0,1]]
def matrixUpdated : Fin 2 → Fin 3 → ℝ := ![updated, ![7/2,1/2,5/3]]
def wrongRowUpdated : Fin 2 → Fin 3 → ℝ := ![swapped, ![5/2,1/2,8/3]]

theorem actual_matrix_posterior :
    (matrixZ 2 2 rowPriors matrixCounts)⁻¹ •
      (Measure.pi (fun r => family 2 (rowPriors r))).withDensity
        (fun A => ∏ r, TailCountTransfer.categoricalLikelihood 2 (matrixCounts r) (A r)) =
      Measure.pi (fun r => family 2 (matrixUpdated r)) := by
  have hp : ∀ r j, 0<rowPriors r j := by intro r j; fin_cases r <;> fin_cases j <;> norm_num [rowPriors, prior]
  have hu : (fun r j => rowPriors r j+(matrixCounts r j:ℝ)) = matrixUpdated := by
    funext r j; fin_cases r <;> fin_cases j <;> norm_num [rowPriors, prior, matrixCounts, counts, matrixUpdated, updated]
  exact (normalized_rows 2 2 rowPriors hp matrixCounts).trans
    (congrArg (fun (α : Fin 2 → Fin 3 → ℝ) =>
      Measure.pi (fun r => family 2 (α r))) hu)

/-- The incorrect update actually interchanges the two observed count rows. -/
theorem wrong_rows_are_swapped_counts :
    (fun r j => rowPriors r j+(matrixCounts (1-r) j:ℝ)) = wrongRowUpdated := by
  funext r j
  fin_cases r <;> fin_cases j <;> norm_num [rowPriors, prior, matrixCounts, counts, wrongRowUpdated, swapped]

/-- Genuine joint measure inequality; not merely different shape vectors. -/
theorem actual_joint_wrong_row_refused :
    Measure.pi (fun r => family 2 (matrixUpdated r)) ≠
      Measure.pi (fun r => family 2 (wrongRowUpdated r)) := by
  intro h
  have hm := congrArg (fun μ : Measure (Fin 2 → (Fin 3 → ℝ)) => μ.map (Function.eval 0)) h
  rw [row_projection 2 2 matrixUpdated (by intro r j; fin_cases r <;> fin_cases j <;> norm_num [matrixUpdated, updated]) 0,
    row_projection 2 2 wrongRowUpdated (by intro r j; fin_cases r <;> fin_cases j <;> norm_num [wrongRowUpdated, swapped]) 0] at hm
  exact actual_swapped_family_refused (by simpa [matrixUpdated, wrongRowUpdated] using hm)

/-- Missing-tail joint measure is refused via its actual first-row projection. -/
theorem actual_joint_wrong_tail_refused :
    Measure.pi (fun r => family 2 (matrixUpdated r)) ≠
      Measure.pi (fun r : Fin 2 => family 2 ((![wrongTail, matrixUpdated 1]) r)) := by
  intro h
  have hm := congrArg (fun μ : Measure (Fin 2 → (Fin 3 → ℝ)) => μ.map (Function.eval 0)) h
  rw [row_projection 2 2 matrixUpdated (by intro r j; fin_cases r <;> fin_cases j <;> norm_num [matrixUpdated, updated]) 0,
    row_projection 2 2 (![wrongTail, matrixUpdated 1]) (by intro r j; fin_cases r <;> fin_cases j <;> norm_num [wrongTail, matrixUpdated]) 0] at hm
  exact actual_wrong_tail_family_refused (by simpa [matrixUpdated] using hm)

/-- Row1 has a distinct prior and counts, and its genuine projection moment is 21/34. -/
theorem actual_second_row_moment :
    ((((Measure.pi (fun r => family 2 (matrixUpdated r))).map (Function.eval 1)).map
      (Function.eval 0)).withDensity (BetaDensity.likelihood 1 0)) Set.univ =
      ENNReal.ofReal (21/34:ℝ) := by
  rw [row_projection 2 2 matrixUpdated (by intro r j; fin_cases r <;> fin_cases j <;> norm_num [matrixUpdated, updated]) 1]
  rw [first_marginal (matrixUpdated 1) (by intro j; fin_cases j <;> norm_num [matrixUpdated])]
  rw [show matrixUpdated 1 0 = (7/2:ℝ) by norm_num [matrixUpdated],
    show matrixUpdated 1 1 + matrixUpdated 1 2 = (13/6:ℝ) by norm_num [matrixUpdated]]
  rw [BetaDensity.weighted_mass (by norm_num) (by norm_num) 1 0,
    NonintegerMomentControls.success_normalizer_ratio _ _ (by norm_num) (by norm_num)]
  norm_num

/-- Full zero-count row-product posterior identity, including empty row products. -/
theorem zero_count_row_product (m k : ℕ) (α : Fin m → Fin (k+1) → ℝ)
    (hα : ∀ r j, 0<α r j) :
    (matrixZ m k α (fun _ _ => 0))⁻¹ •
      (Measure.pi (fun r => family k (α r))).withDensity
        (fun A => ∏ r, TailCountTransfer.categoricalLikelihood k (fun _ => 0) (A r)) =
      Measure.pi (fun r => family k (α r)) := by
  simpa only [Nat.cast_zero, add_zero] using normalized_rows m k α hα (fun _ _ => 0)

end
end FEP.EmpiricalRisk.ConditioningRowProductProposal

#print axioms FEP.EmpiricalRisk.ConditioningRowProductProposal.vector_pi_withDensity
#print axioms FEP.EmpiricalRisk.ConditioningRowProductProposal.vector_pi_scale_factors
#print axioms FEP.EmpiricalRisk.ConditioningRowProductProposal.weighted_rows
#print axioms FEP.EmpiricalRisk.ConditioningRowProductProposal.matrixZ_pos_finite
#print axioms FEP.EmpiricalRisk.ConditioningRowProductProposal.normalized_rows
#print axioms FEP.EmpiricalRisk.ConditioningRowProductProposal.actual_two_distinct_rows
#print axioms FEP.EmpiricalRisk.ConditioningRowProductProposal.zero_rows_normalizer
#print axioms FEP.EmpiricalRisk.ConditioningRowProductProposal.row0_swapped_refused
#print axioms FEP.EmpiricalRisk.ConditioningRowProductProposal.row0_wrong_tail_refused
#print axioms FEP.EmpiricalRisk.ConditioningRowProductProposal.row_projection
#print axioms FEP.EmpiricalRisk.ConditioningRowProductProposal.actual_matrix_posterior
#print axioms FEP.EmpiricalRisk.ConditioningRowProductProposal.wrong_rows_are_swapped_counts
#print axioms FEP.EmpiricalRisk.ConditioningRowProductProposal.actual_joint_wrong_row_refused
#print axioms FEP.EmpiricalRisk.ConditioningRowProductProposal.actual_second_row_moment
#print axioms FEP.EmpiricalRisk.ConditioningRowProductProposal.zero_count_row_product
#print axioms FEP.EmpiricalRisk.ConditioningRowProductProposal.actual_joint_wrong_tail_refused
