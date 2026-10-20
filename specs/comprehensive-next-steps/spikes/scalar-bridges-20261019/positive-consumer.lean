module
public import FepSketches.compositions.core

@[expose] public section


example : HasDerivAt fep_fep018.FEP018.fep018_fisherCoordinate 2 (1 / 2) := by
  convert FEPComposed.fep018_coordinate_derivative_is_fep038
    (p := 1 / 2) (by norm_num) (by norm_num) using 1
  norm_num [fep_fep038.FEP038.fep038_coordinateJacobian]
  have hsqrt : Real.sqrt (4 : ℝ) = 2 :=
    (Real.sqrt_eq_iff_eq_sq (by norm_num) (by norm_num)).2 (by norm_num)
  exact hsqrt.symm
open scoped BigOperators
namespace MaxEntSupportBoundary
/-- A singleton denominator does not make the ambient two-state expression a law. -/
theorem singleton_support_ambient_mass :
    (∑ i : Fin 2, fep_fep031.FEP031.fep031_gibbsProbability
      0 2 (fun _ => 0) {0} i) = 2 := by
  norm_num [fep_fep031.FEP031.fep031_gibbsProbability, Fin.sum_univ_two]

theorem singleton_support_not_ambient_normalized :
    (∑ i : Fin 2, fep_fep031.FEP031.fep031_gibbsProbability
      0 2 (fun _ => 0) {0} i) ≠ 1 := by
  rw [singleton_support_ambient_mass]
  norm_num
#print axioms singleton_support_ambient_mass
#print axioms singleton_support_not_ambient_normalized
end MaxEntSupportBoundary
#print axioms FEPComposed.fep031_energyGibbs_is_topicProbability
#print axioms FEPComposed.fep030_fep031_finite_maxEntropy
#print axioms FEPComposed.fep030_fin2_entropy_eq_binEntropy
#print axioms FEPComposed.fep030_finite_binary_entropy_bound
#print axioms FEPComposed.fep030_fep031_binary_maxEntropy
#print axioms FEPComposed.fep018_coordinate_derivative_is_fep038
#print axioms FEPComposed.fep018_fep038_actual_metric_pullback
