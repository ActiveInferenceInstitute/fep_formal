module
public import FepSketches.families.core_thermodynamics
public import FepSketches.families.standalone_efe_formalizations
public import FepSketches.helmholtz_ao_ness

@[expose] public section

/-!
# Helmholtz–Ao NESS topic composition

This bridge pairs the Helmholtz–Ao generator-level current identity with the
original fep-025 edge-current divergence law.  The conjunction keeps the
law-weighted circulation carrier and the finite edge-current carrier separate
instead of asserting an identification between the rate-field ansatz and the
transition-row model.
-/

namespace FEPComposed

open FEP.HelmholtzAoNess
open FEP FEP.ContinuousTimeMarkov Finset
open scoped BigOperators

/-- The stationary probability current is carried entirely by the
circulation part and the node divergence of the stationary current vanishes
under stationarity, paired with fep-025's probability-current antisymmetry
and its divergence-free directed-cycle witness; the finite rate-field
decomposition and the transition-row current stay distinct laws. -/
theorem fep160_aoNess_extends_fep025_current
    (generator : FiniteRateGenerator (Fin 3)) (law : FiniteLaw (Fin 3))
    (hSupport : ∀ i, 0 < law i) (hStat : generator.IsStationary law) :
    (∀ i j : Fin 3,
        generator.probabilityCurrent law i j =
          2 * law i * circulationPart generator.rate law i j) ∧
      (∀ i : Fin 3,
        ∑ j, generator.probabilityCurrent law j i = 0) ∧
      (fep_fep025.FEP025.fep025_cycleCurrent 0 1 ≠ 0) := by
  exact
    ⟨fep_fep160.FEP160.fep160_probabilityCurrent_eq_twice_circulation
        generator law hSupport,
      fep_fep160.FEP160.fep160_stationaryCurrent_divergence_zero
        generator law hStat,
      fep_fep025.FEP025.fep025_cycleCurrent_nonzero⟩

/-- The competing-pair uniqueness of the law-weighted split is paired with
fep-160's unconditional decomposition: on the same finite rate-field carrier
the canonical split exists (`rate i j = symmetricPart + circulationPart`)
and any constraint-satisfying competitor coincides with it; no stationarity
hypothesis and no nonnegativity claim for the circulation part enter. -/
theorem fep166_splitUnique_extends_fep160_aoNess
    {State : Type*} [Fintype State] {rate S A : State → State → ℝ}
    {law : FiniteLaw State}
    (hSupport : ∀ i, 0 < law i)
    (hS : ∀ i j, law i * S i j = law j * S j i)
    (hA : ∀ i j, law i * A i j = -(law j * A j i))
    (hSum : ∀ i j, rate i j = S i j + A i j) (i j : State) :
    (S = symmetricPart rate law ∧ A = circulationPart rate law) ∧
      (rate i j = symmetricPart rate law i j + circulationPart rate law i j) := by
  exact
    ⟨fep_fep166.FEP166.fep166_split_unique hSupport hS hA hSum,
      fep_fep160.FEP160.fep160_aoDecomposition hSupport i j⟩

end FEPComposed
