module
public import FepSketches.continuous_time_markov
public import FepSketches.geometric_mechanics
public import Mathlib.Tactic

@[expose] public section

/-!
# Helmholtz–Ao nonequilibrium steady-state decomposition

Finite-state incarnation of the Helmholtz–Ao potential-and-solenoidal split
of a nonequilibrium steady state (the manuscript section
`04d_framework_thermodynamics.md`, `sec:thermo_ness_fokker_planck`): the
drift ansatz `f = -(D + Q) ∇F` with `F = -log p*` and `Qᵀ = -Q` becomes, on
a finite state space with full-support stationary law `p*`, a decomposition
of a rate field into a reversible (detailed-balance) part plus a circulation
part relative to `p*`, together with the explicit divergence check
`∑ j, current j i = 0` that the manuscript demands of the ansatz.

## Main results

| theorem | meaning |
|---------|---------|
| `skewQuadratic_eq_zero` | a skew-symmetric matrix annihilates its quadratic form `gᵀ Q g = 0` (the quadratic-term cancellation) |
| `skewTrace_eq_zero` | `tr(Q H) = 0` for skew `Q` and symmetric `H`; `H` plays the Hessian role (the trace-term cancellation) |
| `aoDecomposition` | every rate field splits, relative to a full-support law, into `symmetricPart + circulationPart` (the finite `D + Q` ansatz) |
| `circulationPart_skew` | the circulation part is skew in the `p*`-weighted sense `p*_i Q_ij = -p*_j Q_ji` (the `Qᵀ = -Q` clause) |
| `symmetricPart_reversible` | the symmetric part is reversible: `p*_i D_ij = p*_j D_ji` |
| `forceSplit` | the log-affinity splits into potential drop plus skew force: `log(p*_i W_ij / p*_j W_ji) = (F_j - F_i) + log(W_ij / W_ji)` |
| `current_eq_twice_circulation` | the stationary edge current is carried entirely by the circulation part: `J_ij = 2 p*_i Q_ij` |
| `symmetricPart_current_eq_zero` | the reversible part carries no current at all |
| `detailedBalanced_iff_circulation_eq_zero` | removing the circulation part is exactly detailed balance |
| `stationaryCurrent_divergence_zero` | under the generator contract (row sums zero) and stationarity, the node divergence of the stationary current vanishes: `∑ j, J_ji = 0` |
| `cycle_*` | the directed three-cycle witness: stationary and divergence-free with `circulationPart = 1/2 ≠ 0` and current `1/3 ≠ 0` — a genuine NESS whose entire current is circulation |

## Scope discipline

* Finite carrier only: states form a `Fintype`, the potential is the
  pointwise `F = -log p*` on masses, and every derivative of the manuscript
  section is replaced by an explicit finite algebraic hypothesis.  The
  continuum Fokker–Planck equation, the diffusion matrix field, and the SDE
  noise are not formalized here.
* The Ao potential `aoPotential` is deliberately distinct from the
  thermodynamic `U - T S` Helmholtz free energy of the `fep013` topic; the
  manuscript keeps the two objects separate.
* The skew-algebra section is parameterized by an arbitrary dimension
  `Fin n`.  The steady-state sections reuse the repository's
  `FEP.ContinuousTimeMarkov` generator contract, so stationarity, detailed
  balance, and the probability current keep their established meanings.
* Carriers stay finite and every hypothesis is explicit.  No new axioms,
  no proof placeholders, no `native_decide`.
* This file is standalone: it is not wired into the generated
  `fep_all.lean`; the catalogue wire-up (topic row, formal-resource roster
  entry, aggregate hoist) is a post-acceptance coordinator chore.
-/

namespace FEP.HelmholtzAoNess

open FEP FEP.ContinuousTimeMarkov Finset
open scoped BigOperators

/-! ## Skew bilinear algebra (shared matrix kit)

The plain-matrix kit and its cancellation lemmas are defined once in
`FEP.GeometricMechanics`; the names are re-exported here so that
`FEP.HelmholtzAoNess.<name>` keeps resolving to the same declarations. -/

export FEP.GeometricMechanics
  (dot mulVec mulOf traceOf SkewSymmetric SymmetricOf sum_swapPairs
   sum_negPairs skewTrace_eq_zero skewQuadratic_eq_zero)

/-! ## The Helmholtz–Ao decomposition of a rate field -/

section AoDecomposition

variable {State : Type*} [Fintype State]

/-- The Ao potential of a full-support law: `F = -log p*`. -/
noncomputable def aoPotential (law : FiniteLaw State) (i : State) : ℝ :=
  -Real.log (law i)

/-- Raw reversible numerator: `p*_i W_ij + p*_j W_ji`. -/
def symmetricNum (rate : State → State → ℝ) (law : FiniteLaw State)
    (i j : State) : ℝ := law i * rate i j + law j * rate j i

/-- Raw circulation numerator: `p*_i W_ij - p*_j W_ji`. -/
def circulationNum (rate : State → State → ℝ) (law : FiniteLaw State)
    (i j : State) : ℝ := law i * rate i j - law j * rate j i

/-- Reversible (dissipative) part of a rate field relative to `law`. -/
noncomputable def symmetricPart (rate : State → State → ℝ)
    (law : FiniteLaw State) (i j : State) : ℝ :=
  symmetricNum rate law i j / (2 * law i)

/-- Solenoidal (circulation) part of a rate field relative to `law`. -/
noncomputable def circulationPart (rate : State → State → ℝ)
    (law : FiniteLaw State) (i j : State) : ℝ :=
  circulationNum rate law i j / (2 * law i)

/-- The two numerators rebuild the rate entry. -/
theorem symmetricNum_add_circulationNum {rate : State → State → ℝ}
    {law : FiniteLaw State} (i j : State) :
    symmetricNum rate law i j + circulationNum rate law i j =
      2 * law i * rate i j := by
  simp only [symmetricNum, circulationNum]
  ring

/-- The circulation numerator is skew under the edge swap. -/
theorem circulationNum_skew {rate : State → State → ℝ}
    {law : FiniteLaw State} (i j : State) :
    circulationNum rate law i j = -circulationNum rate law j i := by
  simp only [circulationNum]
  ring

/-- The reversible numerator is edge-swap symmetric. -/
theorem symmetricNum_comm {rate : State → State → ℝ}
    {law : FiniteLaw State} (i j : State) :
    symmetricNum rate law i j = symmetricNum rate law j i := by
  simp only [symmetricNum]
  ring

/-- Core cancellation: scaling by the mass cancels its own denominator. -/
theorem mass_div_two {law : FiniteLaw State} (hSupport : ∀ i, 0 < law i)
    (X : ℝ) (i : State) : law i * X / (2 * law i) = X / 2 := by
  have hi : law i ≠ 0 := by
    have := hSupport i
    positivity
  rw [mul_comm (2 : ℝ) (law i)]
  exact mul_div_mul_left X (2 : ℝ) hi

/-- The Helmholtz–Ao split: the rate field is the sum of its reversible and
circulation parts relative to the stationary law. -/
theorem aoDecomposition {rate : State → State → ℝ} {law : FiniteLaw State}
    (hSupport : ∀ i, 0 < law i) (i j : State) :
    rate i j = symmetricPart rate law i j + circulationPart rate law i j := by
  have hi : (2 : ℝ) * law i ≠ 0 := by
    have := hSupport i
    positivity
  rw [symmetricPart, circulationPart, ← add_div,
    symmetricNum_add_circulationNum, mul_div_cancel_left₀ (rate i j) hi]

/-- The circulation part is skew in the `p*`-weighted sense. -/
theorem circulationPart_skew {rate : State → State → ℝ} {law : FiniteLaw State}
    (hSupport : ∀ i, 0 < law i) (i j : State) :
    law i * circulationPart rate law i j =
      -(law j * circulationPart rate law j i) := by
  rw [circulationPart, circulationPart, mul_div_assoc' (law i),
    mul_div_assoc' (law j), mass_div_two hSupport, mass_div_two hSupport,
    circulationNum_skew j i, neg_div, neg_neg]

/-- The symmetric part is reversible: detailed balance of the dissipative
term. -/
theorem symmetricPart_reversible {rate : State → State → ℝ}
    {law : FiniteLaw State} (hSupport : ∀ i, 0 < law i) (i j : State) :
    law i * symmetricPart rate law i j =
      law j * symmetricPart rate law j i := by
  rw [symmetricPart, symmetricPart, mul_div_assoc' (law i),
    mul_div_assoc' (law j), mass_div_two hSupport, mass_div_two hSupport,
    symmetricNum_comm]

/-- The stationary edge current equals twice the `p*`-weighted circulation
part: the current is carried entirely by the solenoidal term. -/
theorem current_eq_twice_circulation {rate : State → State → ℝ}
    {law : FiniteLaw State} (hSupport : ∀ i, 0 < law i) (i j : State) :
    circulationNum rate law i j =
      2 * law i * circulationPart rate law i j := by
  have hi : (2 : ℝ) * law i ≠ 0 := by
    have := hSupport i
    positivity
  rw [circulationPart, mul_div_assoc',
    mul_div_cancel_left₀ (circulationNum rate law i j) hi]

/-- The reversible part carries no current. -/
theorem symmetricPart_current_eq_zero {rate : State → State → ℝ}
    {law : FiniteLaw State} (hSupport : ∀ i, 0 < law i) (i j : State) :
    law i * symmetricPart rate law i j -
      law j * symmetricPart rate law j i = 0 := by
  rw [symmetricPart, symmetricPart, mul_div_assoc' (law i),
    mul_div_assoc' (law j), mass_div_two hSupport, mass_div_two hSupport,
    symmetricNum_comm, sub_self]

/-- Generator-level current identity against the repository's probability
current. -/
theorem probabilityCurrent_eq_twice_circulation
    (generator : FiniteRateGenerator State) (law : FiniteLaw State)
    (hSupport : ∀ i, 0 < law i) (i j : State) :
    generator.probabilityCurrent law i j =
      2 * law i * circulationPart generator.rate law i j := by
  simp only [FiniteRateGenerator.probabilityCurrent]
  exact current_eq_twice_circulation hSupport i j

/-- Removing the circulation part is exactly detailed balance: the finite
constructive counterpart of the manuscript's disclaimer about the
solenoidal term. -/
theorem detailedBalanced_iff_circulation_eq_zero {rate : State → State → ℝ}
    {law : FiniteLaw State} (hSupport : ∀ i, 0 < law i) :
    (∀ i j, law i * rate i j = law j * rate j i) ↔
      ∀ i j, circulationPart rate law i j = 0 := by
  constructor
  · intro hBalanced i j
    have hz := hBalanced i j
    show circulationPart rate law i j = 0
    rw [circulationPart, circulationNum, hz, sub_self, zero_div]
  · intro hCirc i j
    have hi : (2 : ℝ) * law i ≠ 0 := by
      have := hSupport i
      positivity
    have hz := hCirc i j
    rw [circulationPart, circulationNum] at hz
    have hz' := div_eq_zero_iff.mp hz
    rcases hz' with h | hne
    · linarith
    · exact absurd hne hi

/-- The log-affinity splits into the potential drop plus the skew force. -/
theorem forceSplit {rate : State → State → ℝ} {law : FiniteLaw State}
    (hSupport : ∀ i, 0 < law i) {i j : State}
    (hij : 0 < rate i j) (hji : 0 < rate j i) :
    Real.log (law i * rate i j / (law j * rate j i)) =
      aoPotential law j - aoPotential law i +
        Real.log (rate i j / rate j i) := by
  have hi := hSupport i
  have hj := hSupport j
  have hnei : law i ≠ 0 := ne_of_gt hi
  have hnej : law j ≠ 0 := ne_of_gt hj
  have hne1 : law i * rate i j ≠ 0 := by positivity
  have hne2 : law j * rate j i ≠ 0 := by positivity
  rw [Real.log_div hne1 hne2, Real.log_mul hnei (ne_of_gt hij),
    Real.log_mul hnej (ne_of_gt hji),
    Real.log_div (ne_of_gt hij) (ne_of_gt hji)]
  unfold aoPotential
  ring

end AoDecomposition

/-! ## Steady-state consequence: the explicit divergence check -/

section SteadyState

variable {State : Type*} [Fintype State]

/-- Under the generator contract and stationarity, the node divergence of
the stationary current vanishes — the finite form of the manuscript's
stationarity constraint. -/
theorem stationaryCurrent_divergence_zero
    (generator : FiniteRateGenerator State) (law : FiniteLaw State)
    (hStat : generator.IsStationary law) (i : State) :
    ∑ j, generator.probabilityCurrent law j i = 0 := by
  simp only [FiniteRateGenerator.probabilityCurrent, Finset.sum_sub_distrib]
  rw [hStat i, ← Finset.mul_sum, generator.row_sum_zero i, mul_zero, sub_zero]

/-- Restated over the circulation part: the divergence check constrains
exactly the solenoidal contribution. -/
theorem circulation_divergence_zero
    (generator : FiniteRateGenerator State) (law : FiniteLaw State)
    (hStat : generator.IsStationary law) (hSupport : ∀ i, 0 < law i)
    (i : State) :
    ∑ j, 2 * law j * circulationPart generator.rate law j i = 0 := by
  have hDiv := stationaryCurrent_divergence_zero generator law hStat i
  simp_rw [probabilityCurrent_eq_twice_circulation generator law hSupport] at hDiv
  exact hDiv

end SteadyState

/-! ## Witness: the directed three-cycle NESS -/

section ThreeCycleWitness

/-- Full support of the uniform stationary law of the three-cycle. -/
theorem cycle_support (i : Fin 3) : 0 < threeCycleStationaryLaw i := by
  norm_num [threeCycleStationaryLaw, FiniteLaw.uniform]

theorem cycle_symmetricPart_zero_one :
    symmetricPart threeCycleGenerator.rate threeCycleStationaryLaw
        (0 : Fin 3) (1 : Fin 3) = 1 / 2 := by
  norm_num [symmetricPart, symmetricNum, threeCycleGenerator,
    threeCycleStationaryLaw, FiniteLaw.uniform]

theorem cycle_circulationPart_zero_one :
    circulationPart threeCycleGenerator.rate threeCycleStationaryLaw
        (0 : Fin 3) (1 : Fin 3) = 1 / 2 := by
  norm_num [circulationPart, circulationNum, threeCycleGenerator,
    threeCycleStationaryLaw, FiniteLaw.uniform]

/-- Skew display: the reverse edge carries the opposite circulation. -/
theorem cycle_circulationPart_one_zero :
    circulationPart threeCycleGenerator.rate threeCycleStationaryLaw
        (1 : Fin 3) (0 : Fin 3) = -1 / 2 := by
  norm_num [circulationPart, circulationNum, threeCycleGenerator,
    threeCycleStationaryLaw, FiniteLaw.uniform]

/-- The ansatz instance on the cycle's forward edge. -/
theorem cycle_decomposition_zero_one :
    threeCycleGenerator.rate (0 : Fin 3) (1 : Fin 3) =
      symmetricPart threeCycleGenerator.rate threeCycleStationaryLaw
          (0 : Fin 3) (1 : Fin 3) +
        circulationPart threeCycleGenerator.rate threeCycleStationaryLaw
          (0 : Fin 3) (1 : Fin 3) := by
  rw [cycle_symmetricPart_zero_one, cycle_circulationPart_zero_one]
  norm_num [threeCycleGenerator]

/-- The divergence check holds on the cycle for every node. -/
theorem cycle_current_divergence_zero (i : Fin 3) :
    ∑ j, threeCycleGenerator.probabilityCurrent threeCycleStationaryLaw j i =
      0 :=
  stationaryCurrent_divergence_zero threeCycleGenerator
    threeCycleStationaryLaw threeCycle_stationary i

/-- The cycle's circulation part is nonzero: a genuine NESS whose current is
entirely solenoidal. -/
theorem cycle_circulationPart_ne_zero :
    circulationPart threeCycleGenerator.rate threeCycleStationaryLaw
        (0 : Fin 3) (1 : Fin 3) ≠ 0 := by
  rw [cycle_circulationPart_zero_one]
  norm_num

/-- The full three-cycle NESS package: stationary, divergence-free, and
circulating. -/
theorem cycle_ao_ness :
    threeCycleGenerator.IsStationary threeCycleStationaryLaw ∧
      (∀ i : Fin 3,
        ∑ j, threeCycleGenerator.probabilityCurrent
            threeCycleStationaryLaw j i = 0) ∧
      circulationPart threeCycleGenerator.rate threeCycleStationaryLaw
          (0 : Fin 3) (1 : Fin 3) ≠ 0 :=
  ⟨threeCycle_stationary, cycle_current_divergence_zero,
    cycle_circulationPart_ne_zero⟩

end ThreeCycleWitness

end FEP.HelmholtzAoNess
