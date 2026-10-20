/- Imported current-owner acceptance control. Actual results are recorded separately. -/
import FepSketches.compositions.core
open FEP FEP.FiniteInformation FEP.VariationalDuality
namespace Issue86Boundary

/-- Lean's totalized division at zero produces uniform mass, not a ground-state
Gibbs minimizer. This strict counterexample forbids extending the T>0 theorem. -/
theorem zero_temperature_totalized_Gibbs_not_minimum :
    helmholtzFreeEnergy helmholtzBoolEnergy 0 <
      expectation (helmholtzGibbsLaw helmholtzBoolEnergy 0) helmholtzBoolEnergy -
        0 * entropy (helmholtzGibbsLaw helmholtzBoolEnergy 0) := by
  norm_num [helmholtzFreeEnergy, helmholtzGibbsLaw, helmholtzPartition,
    helmholtzBoolEnergy, expectation, Fintype.sum_bool]

#print axioms zero_temperature_totalized_Gibbs_not_minimum
end Issue86Boundary
