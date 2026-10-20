/- Imported current-owner acceptance control. Actual results are recorded separately. -/
import FepSketches.compositions.core
open scoped BigOperators
namespace Issue104Boundary
open FEPComposed

theorem Fisher_parameter_two_is_negative :
    fep_fep038.FEP038.fep038_fisherMetric 2 1 1 < 0 := by
  norm_num [fep_fep038.FEP038.fep038_fisherMetric,
    fep_fep038.FEP038.fep038_fisherInformation,
    fep_fep038.FEP038.fep038_score,
    fep_fep038.FEP038.fep038_bernoulliMass,
    fep_fep038.FEP038.fep038_bernoulliMassDeriv]

theorem probability_mass_upper_bound_is_necessary :
    fep_fep026.FEP026.fep026_priorComplexity 2 < 0 := by
  change -Real.log 2 < 0
  linarith [Real.log_pos (by norm_num : (1:ℝ) < 2)]

theorem incomplete_partition_sum_loses_energy :
    fep005_blockEnergy (fun _ => 1) (fun _ => 1) 0 <
      ∑ _ : Fin 20, (1:ℝ) := by
  norm_num [fep005_blockEnergy, fep_fep005.FEP005.fep005_partitionCover]

theorem zero_step_does_not_converge_to_center :
    ¬ Filter.Tendsto
      (fun n : ℕ => ((fun y : ℝ => y-0*fep_fep043.FEP043.fep043_quadraticGradient 1 0 y)^[n]) 1)
      Filter.atTop (nhds 0) := by
  intro h
  have heq : (fun n : ℕ =>
      ((fun y : ℝ => y-0*fep_fep043.FEP043.fep043_quadraticGradient 1 0 y)^[n]) 1) =
      (fun _ : ℕ => (1:ℝ)) := by
    funext n
    simp only [zero_mul, sub_zero]
    exact congrArg (fun f : ℝ → ℝ => f 1) (Function.iterate_id n)
  rw [heq] at h
  have hfalse : (1:ℝ) = 0 := tendsto_nhds_unique tendsto_const_nhds h
  norm_num at hfalse

#print axioms Fisher_parameter_two_is_negative
#print axioms probability_mass_upper_bound_is_necessary
#print axioms incomplete_partition_sum_loses_energy
#print axioms zero_step_does_not_converge_to_center
end Issue104Boundary
