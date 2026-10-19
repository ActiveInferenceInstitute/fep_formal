module
public import FepSketches.compositions.core

@[expose] public section


open FEP FEP.FiniteInformation FEP.VariationalDuality
example {n : ℕ} [NeZero n] (E : Fin n → ℝ) (β : ℝ) (q : FiniteLaw (Fin n)) :
    entropy q ≤ entropy (energyGibbsLaw E β) := by
  exact (FEPComposed.fep030_fep031_finite_maxEntropy E β q).2.1
