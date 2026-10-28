module
public import FepSketches.helmholtz_ao_ness
public import Mathlib.Algebra.BigOperators.Fin
public import Mathlib.Data.Fin.VecNotation
public import Mathlib.Tactic.FinCases
public import Mathlib.Tactic.LinearCombination
public import Mathlib.Tactic.NormNum
public import Mathlib.Tactic.Positivity

@[expose] public section

/-!
# Uniqueness of the law-weighted reversible/circulation split (fep-166)

`FEP.HelmholtzAoNess` (fep-160) establishes that every rate field admits, relative
to a full-support law, the canonical split into a reversible part and a circulation
part (`aoDecomposition`).  This module adds the competing-pair uniqueness
characterization: any other decomposition obeying the same two constraint clauses
coincides with the canonical one.  This is the new boundary content — fep-160's
`detailedBalanced_iff_circulation_eq_zero` already characterizes zero circulation,
and is cited (not restated) for the reversible boundary.

## Main results

| theorem | meaning |
|---------|---------|
| `fep166_split_unique` | for positive finite `p` and `W = S + A` with `p_i S_ij = p_j S_ji`, `p_i A_ij = -p_j A_ji`, necessarily `S = symmetricPart W p` and `A = circulationPart W p` |
| `fep166_reversible_split_unique` | `p`-reversible `W` has the unique split `(W, 0)`: the canonical pair collapses onto the reversible field |
| `fep166_twoByTwo_*` | the t-0060 oracle datum `W = [[1, 5/2], [3/4, -1]]`, `p = (1/3, 2/3)` satisfies all constraints, its constraint-satisfying split is the canonical one, and the circulation is genuinely nonzero (`1/2`, with the reverse entry `-1/4 < 0`) |

## Scope discipline

* Positivity of `p` is the only analytic input: it licenses the divisions
  (the `mass_div_two` pattern of fep-160).  No stationarity hypothesis and no
  generator contract enter the algebraic uniqueness statements.
* `A` is never asserted to be a nonnegative rate field; the witness datum has
  `A_10 = -1/4 < 0`, so no such boundary holds.
* Carriers stay finite (`Fintype`); every hypothesis is explicit.  No new
  axioms, no proof placeholders, no `native_decide`.
* This file is wired into the generated `fep_all.lean` (wave-4 catalog
  wire-up: topic row, formal-resource roster entry, aggregate hoist).
-/

namespace FEP.LawWeightedSplit

open FEP FEP.HelmholtzAoNess Finset
open scoped BigOperators

/-! ## Competing-pair uniqueness of the law-weighted split -/

section Uniqueness

variable {State : Type*} [Fintype State] {rate S A : State → State → ℝ}
  {law : FiniteLaw State}

/-- Competing-pair uniqueness of the Helmholtz–Ao split: a positive finite law
`p` and a rate field `rate` written as `rate = S + A` where `S` is
`p`-reversible (`p_i S_ij = p_j S_ji`) and `A` is `p`-skew
(`p_i A_ij = -p_j A_ji`) force `S` and `A` to be exactly the canonical
`symmetricPart` and `circulationPart` of fep-160.  Positivity of `p` licenses
the divisions; no stationarity input is used. -/
theorem fep166_split_unique
    (hSupport : ∀ i, 0 < law i)
    (hS : ∀ i j, law i * S i j = law j * S j i)
    (hA : ∀ i j, law i * A i j = -(law j * A j i))
    (hSum : ∀ i j, rate i j = S i j + A i j) :
    S = symmetricPart rate law ∧ A = circulationPart rate law := by
  have h2 : ∀ i : State, (2 : ℝ) * law i ≠ 0 := by
    intro i
    have := hSupport i
    positivity
  constructor
  · funext i j
    rw [symmetricPart, symmetricNum, eq_div_iff (h2 i), hSum i j, hSum j i]
    linear_combination (hS i j) - (hA i j)
  · funext i j
    rw [circulationPart, circulationNum, eq_div_iff (h2 i), hSum i j, hSum j i]
    linear_combination (hA i j) - (hS i j)

/-- The reversible boundary, in uniqueness form: a `p`-reversible rate field
has the canonical split `(W, 0)` — the symmetric part is the field itself and
the circulation part vanishes.  Rests on fep-160's
`detailedBalanced_iff_circulation_eq_zero` and `aoDecomposition`, which this
boundary refines rather than restates. -/
theorem fep166_reversible_split_unique
    (hSupport : ∀ i, 0 < law i)
    (hRev : ∀ i j, law i * rate i j = law j * rate j i) :
    rate = symmetricPart rate law ∧ (∀ i j, circulationPart rate law i j = 0) := by
  have hz := (detailedBalanced_iff_circulation_eq_zero hSupport).mp hRev
  refine ⟨?_, hz⟩
  funext i j
  have h := aoDecomposition (rate := rate) (law := law) hSupport i j
  rw [hz i j, add_zero] at h
  exact h

end Uniqueness

/-! ## Witness: the t-0060 oracle datum on `Fin 2`

The datum is non-stationary and carries no generator contract: the split is
unconditional finite algebra.  All entries are proven, not computed through an
escape hatch. -/

section TwoByTwoWitness

/-- Witness weight vector `p = (1/3, 2/3)` as a plain mass function. -/
noncomputable def twoByTwoMass : Fin 2 → ℝ := ![1 / 3, 2 / 3]

/-- The witness weight vector packaged as a `FiniteLaw`. -/
noncomputable def twoByTwoLaw : FiniteLaw (Fin 2) where
  mass := twoByTwoMass
  nonneg := by
    intro x
    fin_cases x <;> norm_num [twoByTwoMass]
  sum_one := by
    norm_num [Fin.sum_univ_two, twoByTwoMass]

/-- The witness rate field `W = [[1, 5/2], [3/4, -1]]` (t-0060 oracle datum). -/
noncomputable def twoByTwoW : Fin 2 → Fin 2 → ℝ := ![![1, 5 / 2], ![3 / 4, -1]]

/-- The canonical reversible part `S = [[1, 2], [1, -1]]`. -/
noncomputable def twoByTwoS : Fin 2 → Fin 2 → ℝ := ![![1, 2], ![1, -1]]

/-- The canonical circulation part `A = [[0, 1/2], [-1/4, 0]]`. -/
noncomputable def twoByTwoA : Fin 2 → Fin 2 → ℝ := ![![0, 1 / 2], ![-1 / 4, 0]]

/-- Full support of the witness law. -/
theorem fep166_twoByTwo_support (i : Fin 2) : 0 < twoByTwoLaw i := by
  fin_cases i <;> norm_num [twoByTwoLaw, twoByTwoMass]

/-- The t-0060 datum satisfies every constraint clause of the law-weighted
split: `S` is `p`-reversible, `A` is `p`-skew, and `W = S + A` entrywise. -/
theorem fep166_twoByTwo_predicates :
    (∀ i j : Fin 2, twoByTwoLaw i * twoByTwoS i j = twoByTwoLaw j * twoByTwoS j i) ∧
      (∀ i j : Fin 2,
        twoByTwoLaw i * twoByTwoA i j = -(twoByTwoLaw j * twoByTwoA j i)) ∧
      (∀ i j : Fin 2, twoByTwoW i j = twoByTwoS i j + twoByTwoA i j) := by
  refine ⟨?_, ?_, ?_⟩ <;>
    · intro i j
      fin_cases i <;> fin_cases j <;>
        norm_num [twoByTwoLaw, twoByTwoMass, twoByTwoW, twoByTwoS, twoByTwoA]

/-- The datum's constraint-satisfying split is exactly the canonical
`symmetricPart`/`circulationPart` pair — the uniqueness theorem applied. -/
theorem fep166_twoByTwo_split_canonical :
    twoByTwoS = symmetricPart twoByTwoW twoByTwoLaw ∧
      twoByTwoA = circulationPart twoByTwoW twoByTwoLaw :=
  fep166_split_unique (rate := twoByTwoW) (S := twoByTwoS) (A := twoByTwoA)
    (law := twoByTwoLaw)
    fep166_twoByTwo_support
    fep166_twoByTwo_predicates.1
    fep166_twoByTwo_predicates.2.1
    fep166_twoByTwo_predicates.2.2

/-- The datum exhibits a genuinely nonzero circulation on the forward edge. -/
theorem fep166_twoByTwo_circulation_nonzero :
    circulationPart twoByTwoW twoByTwoLaw (0 : Fin 2) (1 : Fin 2) = 1 / 2 := by
  rw [circulationPart, circulationNum]
  norm_num [twoByTwoLaw, twoByTwoMass, twoByTwoW]

/-- The reverse edge carries the opposite, strictly negative circulation
`-1/4`: the circulation part is not a nonnegative rate field. -/
theorem fep166_twoByTwo_circulation_negative :
    circulationPart twoByTwoW twoByTwoLaw (1 : Fin 2) (0 : Fin 2) = -1 / 4 := by
  rw [circulationPart, circulationNum]
  norm_num [twoByTwoLaw, twoByTwoMass, twoByTwoW]

end TwoByTwoWitness

end FEP.LawWeightedSplit
