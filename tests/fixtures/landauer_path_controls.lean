import FepSketches.families.core_thermodynamics

namespace FEP050Controls
open FEP FEP.PathThermodynamics FEP.FiniteInformation

/-- Units control: bath heat equals kBT times production plus heat-equivalent
lost Shannon entropy. The latter is not entropy measured in J/K. -/
theorem heat_encoding {Path : Type*} [Fintype Path]
    (m : ErasureModel Path) {kB T : ℝ} (hkB : 0 < kB) (hT : 0 < T)
    (hb : m.beta = (kB * T)⁻¹) :
    m.meanHeat = (kB * T) * entropyProduction m.toFinitePathProtocol +
      (kB * T) * (entropy m.prior - entropy m.finalLaw) := by
  have hs : (kB * T) * m.beta = 1 := by
    rw [hb]
    exact mul_inv_cancel₀ (ne_of_gt (mul_pos hkB hT))
  have hh : (kB * T) * (m.beta * m.meanHeat) = m.meanHeat := by
    rw [← mul_assoc, hs, one_mul]
  have hd := congrArg (fun x : ℝ => (kB * T) * x)
    (erasure_entropyProduction_decomposition m)
  nlinarith

/-- A real constructed fair reset reaches the catalogue threshold at kB=2,T=3. -/
theorem fair_catalogue_bound :
    fep_fep050.FEP050.fep050_landauerBound 2 3 ≤
      (reversibleErasureWitness (FiniteLaw.uniform : FiniteLaw Bool)
        (6 : ℝ)⁻¹ (by norm_num)).meanHeat := by
  apply fep_fep050.FEP050.fep050_landauer_heat_bound _ (by norm_num) (by norm_num)
  · norm_num [reversibleErasureWitness]
  · exact reversibleErasureWitness_isReset _ _ _
  · simp [reversibleErasureWitness, FiniteLaw.uniform]

/-- Reversible attainment at the same physical scale, not a conclusion premise. -/
theorem fair_reversible_equality :
    (reversibleErasureWitness (FiniteLaw.uniform : FiniteLaw Bool)
      (6 : ℝ)⁻¹ (by norm_num)).meanHeat =
        fep_fep050.FEP050.fep050_landauerBound 2 3 := by
  rw [fairBit_erasure_heat_eq]
  norm_num [fep_fep050.FEP050.fep050_landauerBound, div_eq_mul_inv, mul_comm]

/-- The biased constructed reset satisfies the generalized catalogue bound. -/
theorem biased_catalogue_bound :
    (2 : ℝ) * 3 * Real.binEntropy (irreversibleForward true) ≤
      (reversibleErasureWitness irreversibleForward (6 : ℝ)⁻¹
        (by norm_num)).meanHeat := by
  exact fep_fep050.FEP050.fep050_generalized_landauer_heat_bound
    (reversibleErasureWitness irreversibleForward (6 : ℝ)⁻¹ (by norm_num))
    (kB := 2) (T := 3) (by norm_num [reversibleErasureWitness])
    (reversibleErasureWitness_isReset _ _ _)

/-- The biased reversible heat is strictly below the fair-bit threshold. -/
theorem biased_strict_control :
    (reversibleErasureWitness irreversibleForward (6 : ℝ)⁻¹
      (by norm_num)).meanHeat < fep_fep050.FEP050.fep050_landauerBound 2 3 := by
  have h := biasedBit_erasure_heat_lt_fair (6 : ℝ)⁻¹ (by norm_num)
  simpa only [div_inv_eq_mul, fep_fep050.FEP050.fep050_landauerBound,
    show (2 : ℝ) * 3 = 6 by norm_num, mul_comm (Real.log 2) 6] using h

/-- Missing reset/thermal identification cannot be replaced by mere imports.
This control fixes a genuine reset and checks the work endpoint separately. -/
theorem fair_work_control :
    fep_fep050.FEP050.fep050_landauerBound 2 3 ≤
      (reversibleErasureWitness (FiniteLaw.uniform : FiniteLaw Bool)
        (6 : ℝ)⁻¹ (by norm_num)).meanHeat := by
  exact fep_fep050.FEP050.fep050_landauer_work_bound
    (reversibleErasureWitness (FiniteLaw.uniform : FiniteLaw Bool)
      (6 : ℝ)⁻¹ (by norm_num))
    (kB := 2) (T := 3) (by norm_num) (by norm_num)
    (by norm_num [reversibleErasureWitness])
    (reversibleErasureWitness_isReset _ _ _)
    (by simp [reversibleErasureWitness, FiniteLaw.uniform]) le_rfl

#print axioms fep_fep050.FEP050.fep050_generalized_landauer_heat_bound
#print axioms fep_fep050.FEP050.fep050_landauer_heat_bound
#print axioms fep_fep050.FEP050.fep050_landauer_work_bound
#print axioms heat_encoding
#print axioms fair_catalogue_bound
#print axioms fair_reversible_equality
#print axioms biased_catalogue_bound
#print axioms biased_strict_control
#print axioms fair_work_control
end FEP050Controls
