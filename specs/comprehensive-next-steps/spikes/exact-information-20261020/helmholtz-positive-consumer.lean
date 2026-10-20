import FepSketches.compositions.core
open FEP FEP.FiniteInformation FEP.VariationalDuality FEPComposed
namespace HelmholtzControls

/-- One actual two-level carrier has decomposition, attainment, uniqueness,
actual equilibrium derivative, and a strictly nonoptimal uniform law at T=1. -/
theorem two_level_positive_temperature :
    (∀ q : FiniteLaw Bool,
      fep_fep013.FEP013.fep013_helmholtz (expectation q helmholtzBoolEnergy) 1 (entropy q) =
        helmholtzFreeEnergy helmholtzBoolEnergy 1 +
          finiteKL q (helmholtzGibbsLaw helmholtzBoolEnergy 1)) ∧
    (∀ q : FiniteLaw Bool,
      helmholtzFreeEnergy helmholtzBoolEnergy 1 ≤
        fep_fep013.FEP013.fep013_helmholtz (expectation q helmholtzBoolEnergy) 1 (entropy q)) ∧
    (∀ q : FiniteLaw Bool,
      fep_fep013.FEP013.fep013_helmholtz (expectation q helmholtzBoolEnergy) 1 (entropy q) =
        helmholtzFreeEnergy helmholtzBoolEnergy 1 ↔ q = helmholtzGibbsLaw helmholtzBoolEnergy 1) ∧
    HasDerivAt (helmholtzFreeEnergy helmholtzBoolEnergy)
      (-entropy (helmholtzGibbsLaw helmholtzBoolEnergy 1)) 1 ∧
    helmholtzFreeEnergy helmholtzBoolEnergy 1 <
      fep_fep013.FEP013.fep013_helmholtz
        (expectation (FiniteLaw.uniform : FiniteLaw Bool) helmholtzBoolEnergy)
        1 (entropy (FiniteLaw.uniform : FiniteLaw Bool)) := by
  have hT : (0:ℝ) < 1 := by norm_num
  refine ⟨?_, (fep013_finite_helmholtz_unique_minimum helmholtzBoolEnergy hT).1,
    (fep013_finite_helmholtz_unique_minimum helmholtzBoolEnergy hT).2,
    fep013_finite_equilibrium_derivative helmholtzBoolEnergy hT,
    fep013_two_level_uniform_strict⟩
  intro q
  simpa using fep013_finite_helmholtz_decomposition helmholtzBoolEnergy hT q

#print axioms two_level_positive_temperature
#print axioms FEPComposed.fep013_finite_helmholtz_decomposition
#print axioms FEPComposed.fep013_finite_helmholtz_unique_minimum
#print axioms FEPComposed.fep013_finite_equilibrium_derivative
#print axioms FEPComposed.fep013_two_level_uniform_strict
end HelmholtzControls
