/- Imported current-owner acceptance control. Actual results are recorded separately. -/
import FepSketches.compositions.core
open FEP FEP.FiniteInformation FEP.VariationalDuality
example : HasDerivAt (helmholtzFreeEnergy helmholtzBoolEnergy)
    (-entropy (helmholtzGibbsLaw helmholtzBoolEnergy (-1))) (-1) := by
  exact FEPComposed.fep013_finite_equilibrium_derivative _ (by norm_num)
