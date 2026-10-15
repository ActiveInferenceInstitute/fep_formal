module
public import Mathlib.Tactic

@[expose] public section

/-!
# Geometric mechanics of the solenoidal term

Finite incarnations of the antisymmetry algebra behind the
Helmholtz–Ao solenoidal decomposition of the manuscript section
`04d_framework_thermodynamics.md` (`sec:thermo_ness_fokker_planck`,
`eq:thermo_solenoidal_divergence`, prose :101-108): the three-term
expansion of the divergence of the candidate current `J = Q ∇F p*` and
the exact boundary between what antisymmetry cancels and what needs an
explicit extra hypothesis.

## Main results

| theorem | meaning |
|---------|---------|
| `skewTrace_eq_zero` | `tr(Q H) = 0` for skew `Q`, symmetric `H`: the trace-term cancellation (04d:103-105) |
| `skewQuadratic_eq_zero` | `gᵀ Q g = 0` for skew `Q`: the quadratic-term cancellation (04d:105-106) |
| `symmetrize` / `symmetrize_symmetric` | the discrete Hessian: symmetrized mixed-difference data, symmetric by construction (finite Clairaut, 04d:107) |
| `skewTrace_symmetrize_eq_zero` | the trace cancellation against the constructed discrete Hessian, no hypothesis on the raw data |
| `weightedDivergence` | the finite `div(p* · Q g)/p*` from explicit directional derivative data |
| `weightedDivergence_eq` | the raw Leibniz expansion `tr(QH) + (∇·Q)ᵀg + (Qg)·∇log p*` |
| `solenoidal_expansion` | the manuscript's three-term identity `tr(QH) − gᵀQg + (∇·Q)ᵀg` under the coupling `∇log p* = −g` |
| `solenoidal_drop_of_orthogonal` | the drop holds when `g ⊥ (∇·Q)ᵀ` — the explicit extra hypothesis |
| `solenoidal_drop_of_constantQ` | the drop holds when every directional derivative of `Q` vanishes (spatially constant `Q`) |
| `expansion_remainder_witness` | concrete derivative data with `(∇·Q)ᵀ g = 1 ≠ 0` |
| `graphDecomposition` | the node divergence of the edge current `Q⊙g` = transport slot + discrete-divergence slot |
| `weightedNodeDiv_eq` | the exact finite Leibniz rule for `div(p ⊙ W)/p` |
| `weightedCurrent_div_eq` | the three-term graph expansion of `div(p ⊙ Q ⊙ g)/p` |
| `witness_current` | the 2-node candidate current `Q g = (0, −1)` |
| `witness_drop_fails` | the unconditional solenoidal drop is FALSE: node divergence `1 ≠ 0` at node `0` |
| `frobeniusInner` / `frobeniusSq` | the Frobenius quadratic form on plain real matrices |
| `frobeniusInner_skew_symmetric` | a skew matrix is Frobenius-orthogonal to a symmetric matrix |
| `fep167_frobenius_pythagoras` | exact Frobenius Pythagoras split across the symmetrization residual (fep-167) |
| `fep167_symmetrize_minimizes` | minimality of `symmetrize H` among symmetric matrices, equality exactly at the symmetrizer (fep-167) |
| `fep167_projection_unique` | uniqueness of the symmetric Frobenius least-squares minimizer (fep-167) |
| `fep167_residual_example` | concrete nonsymmetric datum with nonzero residual `1/2` (fep-167) |
| `dot_sq_le_sq_mul_sq` | squared Cauchy–Schwarz for the plain dot product |
| `fep168_weightedDivergence_eq_remainderDot` | under the cancellation hypotheses the weighted divergence is exactly `dot (divQ DQ) g` (fep-168) |
| `fep168_remainder_sq_budget` | squared Cauchy–Schwarz budget `(weightedDivergence …)² ≤ (∑ rᵢ²)(∑ gᵢ²)` (fep-168) |
| `fep168_absolute_budget` | the same budget over `abs` products (fep-168) |
| `fep168_equality_attained` | the budget is attained with equality on aligned nonzero data (fep-168) |

## Scope discipline

* Pointwise plane: the continuum identity is pointwise in `x`; the
  finite model replaces the directional derivatives of the gradient
  field and of the transport field by explicit data `H` (symmetric, the
  Hessian slot `∂ₖ gₗ`) and `DQ` (the `∂ₖ Qₖₗ` slot).  The weighted
  divergence is *defined* by the exact Leibniz decomposition
  `div(p·V)/p = ∇·V + V·∇log p`; the coupling `∇log p* = −∇F = −g`
  (from `p* ∝ e^{−F}`) is an explicit hypothesis.  The content of the
  expansion theorem is the data decomposition and the cancellation
  structure, not a discretization of the PDE.
* Graph plane: on a finite node set the divergence of an edge field
  `W` (`W i j` = flux `i → j`) is the node divergence
  `∑ j, (W i j − W j i)`.  Its weighted Leibniz rule carries the exact
  residual `∑ j, (1 − p j / p i) · W j i`; there is no finite graph
  identity making it vanish by skewness alone — the continuum step
  `V · ∇log p = −gᵀQg = 0` is first-order.
* The corrected theorem set: the *unconditional* three-term
  solenoidal drop is FALSE (the `witness_*` theorems reproduce the
  manuscript honesty guard's 2-node counterexample `Q = [[0,1],[-1,0]]`,
  `g = (1,0)`, whose candidate current is `(0, −1)` with node divergence
  `(1, −1)`).  The drop holds only under an explicit extra hypothesis.
* Carriers stay finite and every hypothesis is explicit.  No new
  axioms, no proof placeholders, no `native_decide`.
* Frobenius plane (fep-167): the metric/optimality layer over fep-162's
  algebraic symmetrization.  The projection is *constructed*
  (`symmetrize`), minimality is *proved* with the equality boundary, and
  uniqueness among symmetric candidates is *proved*.  No differentiability,
  no continuum Clairaut theorem, no Bregman-projection existence or
  uniqueness claim.  fep-105 (the affine Bregman law) is a different
  plane: vector carrier, generic Bregman divergence, *assumed*
  `AffineBregmanProjection` predicate whose row explicitly withholds
  projection uniqueness — nothing here aliases or generalizes it.
* Remainder-budget plane (fep-168): quantitative norm control of the
  uncancelled remainder on the fep-163 carrier.  The hypothesis
  `dot (mulVec Q g) dlogp = 0` is sufficient, not necessary
  (`weightedDivergence − dot (divQ DQ) g = dot (mulVec Q g) dlogp`
  identically; `dlogp = −g` is the canonical sufficient instance via the
  skew quadratic form).  The budget is stated squared (no square roots,
  no `noncomputable`).  The aligned equality witness introduces a new
  datum; the pinned `remainderG = (1, 1)` is deliberately not repinned
  (it is not aligned: bound `2`, value `1` — strict).
* This file is standalone: it is not wired into the generated
  `fep_all.lean`; the catalogue wire-up (topic rows, family, body file,
  formal-resource roster entry, aggregate hoist) is the coordinator's
  post-acceptance fold chore.
-/

namespace FEP.GeometricMechanics

open scoped BigOperators

/-! ## Skew bilinear algebra: the two cancellation terms -/

section SkewAlgebra

variable {n : ℕ}

/-- Dot product of plain real vectors indexed by `Fin n`. -/
def dot (v w : Fin n → ℝ) : ℝ := ∑ i, v i * w i

/-- Matrix–vector product for a plain real matrix indexed by `Fin n`. -/
def mulVec (M : Fin n → Fin n → ℝ) (v : Fin n → ℝ) : Fin n → ℝ :=
  fun i => ∑ k, M i k * v k

/-- Matrix product for plain real matrices indexed by `Fin n`. -/
def mulOf (A B : Fin n → Fin n → ℝ) : Fin n → Fin n → ℝ :=
  fun i j => ∑ k, A i k * B k j

/-- Plain trace of a plain real matrix indexed by `Fin n`. -/
def traceOf (M : Fin n → Fin n → ℝ) : ℝ := ∑ i, M i i

/-- Skew-symmetry `Mᵀ = -M` for a plain real matrix. -/
def SkewSymmetric (M : Fin n → Fin n → ℝ) : Prop := ∀ i j, M i j = -M j i

/-- Symmetry `Mᵀ = M` for a plain real matrix; the finite Hessian role. -/
def SymmetricOf (M : Fin n → Fin n → ℝ) : Prop := ∀ i j, M i j = M j i

/-- Double-index swap for sums over `Fin n × Fin n`: after
`Finset.sum_comm` the two binder orders are alpha-equivalent. -/
theorem sum_swapPairs {f : Fin n → Fin n → ℝ} :
    ∑ i, ∑ j, f i j = ∑ i, ∑ j, f j i := by
  rw [Finset.sum_comm]

/-- Negation commutes with a double sum over `Fin n × Fin n`. -/
theorem sum_negPairs {f : Fin n → Fin n → ℝ} :
    ∑ i, ∑ j, -f i j = -∑ i, ∑ j, f i j := by
  rw [Finset.sum_congr rfl fun i _ => Finset.sum_neg_distrib (f := fun j => f i j),
    Finset.sum_neg_distrib (f := fun i => ∑ j, f i j)]

/-- The trace-term cancellation: a skew matrix contracted against a
symmetric matrix has zero trace.  Finite form of the manuscript's
"the trace term vanishes ... because `Q` is antisymmetric and the
Hessian is symmetric" (04d:107). -/
theorem skewTrace_eq_zero (Q H : Fin n → Fin n → ℝ)
    (hQ : SkewSymmetric Q) (hH : SymmetricOf H) : traceOf (mulOf Q H) = 0 := by
  have key : traceOf (mulOf Q H) = ∑ i, ∑ j, Q i j * H j i := by
    simp only [traceOf, mulOf]
  have negated : traceOf (mulOf Q H) = -traceOf (mulOf Q H) := by
    calc traceOf (mulOf Q H)
        = ∑ i, ∑ j, Q i j * H j i := key
      _ = ∑ i, ∑ j, Q j i * H i j := sum_swapPairs
      _ = ∑ i, ∑ j, -(Q i j * H j i) := by
            refine Finset.sum_congr rfl fun i _ => ?_
            exact Finset.sum_congr rfl fun j _ => by rw [hQ j i, hH i j]; ring
      _ = -∑ i, ∑ j, Q i j * H j i := sum_negPairs
      _ = -traceOf (mulOf Q H) := by rw [key]
  linarith

/-- A skew-symmetric matrix annihilates its own quadratic form.  Finite
form of "the quadratic term also vanishes because an antisymmetric
bilinear form is zero on a repeated vector" (04d:107). -/
theorem skewQuadratic_eq_zero (Q : Fin n → Fin n → ℝ) (g : Fin n → ℝ)
    (hQ : SkewSymmetric Q) : dot g (mulVec Q g) = 0 := by
  have key : dot g (mulVec Q g) = ∑ i, ∑ j, Q i j * (g i * g j) := by
    simp only [dot, mulVec, Finset.mul_sum]
    exact Finset.sum_congr rfl fun i _ =>
      Finset.sum_congr rfl fun j _ => by ring
  have negated : dot g (mulVec Q g) = -dot g (mulVec Q g) := by
    calc dot g (mulVec Q g)
        = ∑ i, ∑ j, Q i j * (g i * g j) := key
      _ = ∑ i, ∑ j, Q j i * (g j * g i) := sum_swapPairs
      _ = ∑ i, ∑ j, -(Q i j * (g i * g j)) := by
            refine Finset.sum_congr rfl fun i _ => ?_
            exact Finset.sum_congr rfl fun j _ => by rw [hQ j i]; ring
      _ = -∑ i, ∑ j, Q i j * (g i * g j) := sum_negPairs
      _ = -dot g (mulVec Q g) := by rw [key]
  linarith

/-- Symmetrization of raw mixed-difference data: the finite
construction of the Hessian-role matrix.  The continuum Hessian `∇²F`
is symmetric by Clairaut's theorem; in the finite model the symmetric
Hessian-role object is the *construction* below, and the theorems that
follow prove the constructed matrix is symmetric and that the
manuscript's trace cancellation (04d:107) holds against it without any
hypothesis on the raw data. -/
noncomputable def symmetrize (H : Fin n → Fin n → ℝ) : Fin n → Fin n → ℝ :=
  fun i j => (H i j + H j i) / 2

/-- **Discrete-Hessian symmetry**: the symmetrized mixed-difference
data is symmetric — the finite Clairaut property ("the Hessian is
symmetric", 04d:107) as a construction rather than a hypothesis. -/
theorem symmetrize_symmetric (H : Fin n → Fin n → ℝ) :
    SymmetricOf (symmetrize H) := by
  intro i j
  simp only [symmetrize]
  ring

/-- The trace cancellation holds against the constructed discrete
Hessian for arbitrary raw mixed-difference data: the symmetry
hypothesis of `skewTrace_eq_zero` is discharged by the symmetrization
construction. -/
theorem skewTrace_symmetrize_eq_zero (Q H : Fin n → Fin n → ℝ)
    (hQ : SkewSymmetric Q) :
    traceOf (mulOf Q (symmetrize H)) = 0 :=
  skewTrace_eq_zero Q (symmetrize H) hQ (symmetrize_symmetric H)

/-- On data that is already symmetric (the sufficiently smooth case of
the manuscript), symmetrization is the identity: the constructed
discrete Hessian coincides with the given Hessian-role matrix. -/
theorem symmetrize_of_symmetric (H : Fin n → Fin n → ℝ) (hH : SymmetricOf H) :
    symmetrize H = H := by
  funext i j
  simp only [symmetrize, hH j i]
  ring

end SkewAlgebra

/-! ## The pointwise three-term expansion (explicit derivative data) -/

section PointwiseExpansion

variable {n : ℕ}

/-- The finite `∇·Q` field: component `l` is `∑ₖ DQ k l`, the sum of the
directional derivatives of the `k l` entries — the finite ` (∇·Q)ₗ `.
`DQ k l` plays the derivative data `∂ₖ Qₖₗ` at the evaluation point. -/
def divQ (DQ : Fin n → Fin n → ℝ) : Fin n → ℝ :=
  fun l => ∑ k, DQ k l

/-- The finite `∇·(Q g)` given the derivative data: `H l k` plays the
`∂ₖ gₗ` slot (symmetry is not needed here, only for the cancellation)
and `DQ k l` plays the `∂ₖ Qₖₗ` slot.  This is the exact Leibniz
decomposition of the directional derivatives of the flux
`∑ₗ Qₖₗ gₗ`. -/
def fluxDivergence (Q H DQ : Fin n → Fin n → ℝ) (g : Fin n → ℝ) : ℝ :=
  ∑ k, ∑ l, (Q k l * H l k + DQ k l * g l)

/-- The finite `div(p* · Q g)/p*`: the exact weighted Leibniz rule
`div(p·V)/p = ∇·V + V·∇log p` with `V = Q g`, `dlogp` the finite
`∇log p*` data. -/
def weightedDivergence (Q H DQ : Fin n → Fin n → ℝ) (g dlogp : Fin n → ℝ) : ℝ :=
  fluxDivergence Q H DQ g + dot (mulVec Q g) dlogp

/-- The data decomposition of the flux divergence: the Leibniz sum
splits into the trace slot `tr(Q H)` and the `∇·Q` slot. -/
theorem fluxDivergence_eq (Q H DQ : Fin n → Fin n → ℝ) (g : Fin n → ℝ) :
    fluxDivergence Q H DQ g = traceOf (mulOf Q H) + dot (divQ DQ) g := by
  have hsplit : ∀ k : Fin n, ∑ l, (Q k l * H l k + DQ k l * g l)
      = (∑ l, Q k l * H l k) + (∑ l, DQ k l * g l) :=
    fun k => Finset.sum_add_distrib
  have hswap : ∑ k, ∑ l, DQ k l * g l = ∑ l, (∑ k, DQ k l) * g l := by
    rw [Finset.sum_comm]
    exact Finset.sum_congr rfl fun l _ =>
      (Finset.sum_mul Finset.univ (fun k => DQ k l) (g l)).symm
  simp only [fluxDivergence, hsplit, Finset.sum_add_distrib, traceOf, mulOf, dot, divQ, hswap]

/-- The raw Leibniz expansion: the weighted divergence decomposes into
the trace slot, the `∇·Q` slot, and the `p*`-coupling slot — the exact
finite form of `div(p·V)/p = ∇·V + V·∇log p` with `V = Q g`. -/
theorem weightedDivergence_eq (Q H DQ : Fin n → Fin n → ℝ)
    (g dlogp : Fin n → ℝ) :
    weightedDivergence Q H DQ g dlogp
      = traceOf (mulOf Q H) + dot (divQ DQ) g + dot (mulVec Q g) dlogp := by
  rw [weightedDivergence, fluxDivergence_eq]

/-- The manuscript's three-term identity (`eq:thermo_solenoidal_divergence`,
04d:103-105) under the stationary-density coupling `∇log p* = −∇F = −g`
(from `p* ∝ e^{−F}`):

`div(p* · Q g)/p* = tr(Q H) − gᵀ Q g + (∇·Q)ᵀ g`.

Nothing vanishes by antisymmetry inside this statement — the identity
is exact as stated, and the cancellations are separate theorems. -/
theorem solenoidal_expansion (Q H DQ : Fin n → Fin n → ℝ)
    (g dlogp : Fin n → ℝ) (hcoup : ∀ i, dlogp i = -g i) :
    weightedDivergence Q H DQ g dlogp
      = traceOf (mulOf Q H) - dot g (mulVec Q g) + dot (divQ DQ) g := by
  rw [weightedDivergence_eq Q H DQ g dlogp]
  have hp : dot (mulVec Q g) dlogp = -dot g (mulVec Q g) := by
    simp only [dot]
    rw [← Finset.sum_neg_distrib (f := fun i => g i * mulVec Q g i)]
    exact Finset.sum_congr rfl fun i _ => by rw [hcoup i]; ring
  rw [hp]
  ring

/-- **The corrected solenoidal drop.**  Under the stationary coupling
and the explicit orthogonality hypothesis `g ⊥ (∇·Q)ᵀ`, the weighted
divergence of the candidate current vanishes: both antisymmetry-
cancellable terms die (`skewTrace_eq_zero`, `skewQuadratic_eq_zero`)
and the remainder is killed by the hypothesis.  Without the hypothesis
the drop fails — see `witness_drop_fails`. -/
theorem solenoidal_drop_of_orthogonal (Q H DQ : Fin n → Fin n → ℝ)
    (g dlogp : Fin n → ℝ) (hQ : SkewSymmetric Q) (hH : SymmetricOf H)
    (hcoup : ∀ i, dlogp i = -g i) (horth : dot (divQ DQ) g = 0) :
    weightedDivergence Q H DQ g dlogp = 0 := by
  rw [solenoidal_expansion Q H DQ g dlogp hcoup,
    skewTrace_eq_zero Q H hQ hH, skewQuadratic_eq_zero Q g hQ, horth]
  ring

/-- The drop under spatially constant `Q`: every directional derivative
of the transport field vanishes, hence so does its divergence — the
finite form of the manuscript's "it needs, for example, spatially
constant `Q`" (04d:107). -/
theorem solenoidal_drop_of_constantQ (Q H DQ : Fin n → Fin n → ℝ)
    (g dlogp : Fin n → ℝ) (hQ : SkewSymmetric Q) (hH : SymmetricOf H)
    (hcoup : ∀ i, dlogp i = -g i) (hconst : ∀ k l, DQ k l = 0) :
    weightedDivergence Q H DQ g dlogp = 0 := by
  have hdiv : divQ DQ = fun _ => 0 := by
    funext l
    simp only [divQ]
    exact Finset.sum_eq_zero fun k _ => hconst k l
  exact solenoidal_drop_of_orthogonal Q H DQ g dlogp hQ hH hcoup (by
    rw [hdiv]
    simp [dot])

/-- Concrete derivative data on two directions: `DQ 0 0 = 1`, all other
entries zero — a transport field whose `∇·Q` slot is `(1, 0)`. -/
def remainderDQ : Fin 2 → Fin 2 → ℝ :=
  fun k l => if k = 0 ∧ l = 0 then 1 else 0

/-- The constant unit gradient for the remainder witness. -/
def remainderG : Fin 2 → ℝ := fun _ => 1

/-- The expansion remainder `(∇·Q)ᵀ g` equals `1 ≠ 0` on the concrete
data: without the explicit extra hypothesis the solenoidal drop
genuinely fails already at the expansion level. -/
theorem expansion_remainder_witness : dot (divQ remainderDQ) remainderG = 1 := by
  have h0 : divQ remainderDQ 0 = 1 := by
    simp only [divQ, remainderDQ, Fin.sum_univ_two]
    norm_num
  have h1 : divQ remainderDQ 1 = 0 := by
    simp only [divQ, remainderDQ, Fin.sum_univ_two]
    norm_num
  simp only [dot, remainderG, Fin.sum_univ_two]
  rw [h0, h1]
  norm_num

end PointwiseExpansion

/-! ## The graph plane: node divergence of the edge current -/

section GraphDivergence

variable {n : ℕ}

/-- Row sum of a plain real matrix — the net outflow of the transport
field from node `i`. -/
def rowSum (M : Fin n → Fin n → ℝ) (i : Fin n) : ℝ := ∑ j, M i j

/-- Node divergence of an edge field `W` (`W i j` = flux `i → j`):
total outflow minus total inflow at node `i`. -/
def nodeDiv (W : Fin n → Fin n → ℝ) (i : Fin n) : ℝ := ∑ j, (W i j - W j i)

/-- The edge current of the candidate solenoidal flow: the flux
`i → j` carries `Q i j * g j` — the finite `Q ∇F` flux. -/
def currentOf (Q : Fin n → Fin n → ℝ) (g : Fin n → ℝ) :
    Fin n → Fin n → ℝ := fun i j => Q i j * g j

/-- For skew `Q` the node divergence of the transport field is twice
its row sum: the discrete divergence slot is generically nonzero. -/
theorem nodeDiv_skew {Q : Fin n → Fin n → ℝ} (hQ : SkewSymmetric Q)
    (i : Fin n) : nodeDiv Q i = 2 * rowSum Q i := by
  have hcol : ∑ j, Q j i = -∑ j, Q i j := by
    rw [← Finset.sum_neg_distrib]
    exact Finset.sum_congr rfl fun j _ => hQ j i
  simp only [nodeDiv, rowSum, Finset.sum_sub_distrib]
  rw [hcol]
  ring

/-- **Graph decomposition of the candidate current's divergence.**  For
skew `Q`, the node divergence of the edge current `Q⊙g` splits into the
transport slot `(Q g) i` plus the discrete-divergence slot
`g i · rowSum Q i` (the finite counterpart of the ` (∇·Q)ᵀ g ` term,
up to the skew factor of `nodeDiv_skew`). -/
theorem graphDecomposition (Q : Fin n → Fin n → ℝ) (g : Fin n → ℝ)
    (hQ : SkewSymmetric Q) (i : Fin n) :
    nodeDiv (currentOf Q g) i = mulVec Q g i + g i * rowSum Q i := by
  have hcol : ∑ j, Q j i = -∑ j, Q i j := by
    rw [← Finset.sum_neg_distrib]
    exact Finset.sum_congr rfl fun j _ => hQ j i
  simp only [nodeDiv, currentOf, mulVec, rowSum, Finset.sum_sub_distrib]
  rw [← Finset.sum_mul, hcol]
  ring

/-- Weighted node divergence: `div(p ⊙ W)/p` node-by-node, with `p` the
finite stationary density (full support assumed at use sites). -/
noncomputable def weightedNodeDiv (p : Fin n → ℝ) (W : Fin n → Fin n → ℝ)
    (i : Fin n) : ℝ :=
  (∑ j, (p i * W i j - p j * W j i)) / p i

/-- **Exact finite Leibniz rule** for the weighted node divergence:
`div(p ⊙ W)/p = div W + ∑ j, (1 − p j / p i) · W j i`.  On a finite
graph the `p`-residual does not vanish by skewness alone — the
continuum step `V · ∇log p = −gᵀQg = 0` is first-order and has no
exact finite graph analogue. -/
theorem weightedNodeDiv_eq (W : Fin n → Fin n → ℝ) {p : Fin n → ℝ}
    (hp : ∀ i, 0 < p i) (i : Fin n) :
    weightedNodeDiv p W i = nodeDiv W i + ∑ j, (1 - p j / p i) * W j i := by
  have hpi : p i ≠ 0 := ne_of_gt (hp i)
  have hsum : (∑ j, (p i * W i j - p j * W j i)) / p i
      = ∑ j, (W i j - (p j / p i) * W j i) := by
    rw [Finset.sum_div]
    refine Finset.sum_congr rfl fun j _ => ?_
    rw [sub_div, mul_div_cancel_left₀ _ hpi]
    ring
  rw [weightedNodeDiv, hsum, nodeDiv, ← Finset.sum_add_distrib]
  exact Finset.sum_congr rfl fun j _ => by ring

/-- The three-term graph expansion of the weighted candidate current:
transport slot + discrete-divergence slot + `p`-coupling slot — the
finite `div(p ⊙ Q ⊙ g)/p` with every slot explicit. -/
theorem weightedCurrent_div_eq (Q : Fin n → Fin n → ℝ) (g : Fin n → ℝ)
    {p : Fin n → ℝ}
    (hQ : SkewSymmetric Q) (hp : ∀ i, 0 < p i) (i : Fin n) :
    weightedNodeDiv p (currentOf Q g) i
      = mulVec Q g i + g i * rowSum Q i
        + g i * ∑ j, (1 - p j / p i) * Q j i := by
  have hslot : ∑ j, (1 - p j / p i) * (currentOf Q g) j i
      = g i * ∑ j, (1 - p j / p i) * Q j i := by
    simp only [currentOf]
    rw [Finset.mul_sum Finset.univ (fun j => (1 - p j / p i) * Q j i) (g i)]
    exact Finset.sum_congr rfl fun j _ => by ring
  rw [weightedNodeDiv_eq (currentOf Q g) hp i, graphDecomposition Q g hQ i, hslot]

end GraphDivergence

/-! ## The necessity witness: the unconditional drop is FALSE -/

section NecessityWitness

/-- The manuscript honesty guard's transport matrix
`[[0, 1], [-1, 0]]` on two nodes. -/
def witnessQ : Fin 2 → Fin 2 → ℝ :=
  fun i j => if i = 0 ∧ j = 1 then 1 else if i = 1 ∧ j = 0 then -1 else 0

/-- The manuscript honesty guard's gradient vector `(1, 0)`. -/
def witnessG : Fin 2 → ℝ := fun i => if i = 0 then 1 else 0

/-- The witness transport matrix is skew. -/
theorem witnessQ_skew : SkewSymmetric witnessQ := by
  intro i j
  fin_cases i <;> fin_cases j <;> simp [witnessQ]

/-- The candidate current of the honesty guard: `Q g = (0, −1)` — the
exact 2-node evaluation quoted in the manuscript's scope discussion. -/
theorem witness_current :
    mulVec witnessQ witnessG = fun i => if i = 0 then 0 else -1 := by
  funext i
  fin_cases i <;>
    simp only [mulVec, witnessQ, witnessG, Fin.sum_univ_two] <;> norm_num

/-- Why the drop fails here: the discrete divergence of the witness
transport field is `(2, −2) ≠ 0` — the finite counterpart of the
` (∇·Q)ᵀ g ` term, which no antisymmetry alone kills. -/
theorem witness_divQ :
    nodeDiv witnessQ = fun i => if i = 0 then 2 else -2 := by
  funext i
  fin_cases i <;>
    simp only [nodeDiv, witnessQ, Fin.sum_univ_two] <;> norm_num

/-- The node divergence of the witness current is `(1, −1) ≠ 0`: the
unconditional solenoidal drop fails on the exact 2-node counterexample. -/
theorem witness_divergence :
    nodeDiv (currentOf witnessQ witnessG) = fun i => if i = 0 then 1 else -1 := by
  funext i
  fin_cases i <;>
    simp only [nodeDiv, currentOf, witnessQ, witnessG, Fin.sum_univ_two] <;>
      norm_num

/-- **The unconditional solenoidal drop is false.**  For the exact
2-node transport `Q = [[0,1],[-1,0]]` and gradient `g = (1,0)` the node
divergence of the candidate current equals `1` at node `0`: neither
`solenoidal_drop_of_orthogonal`'s orthogonality (here
`g ⊥ (∇·Q)ᵀ` fails) nor a constant-`Q` condition (the discrete
divergence `nodeDiv witnessQ` is `2 ≠ 0` at node `0`) is available, and
the divergence genuinely does not vanish. -/
theorem witness_drop_fails : nodeDiv (currentOf witnessQ witnessG) 0 = 1 := by
  rw [witness_divergence]
  norm_num

end NecessityWitness

/-! ## The Frobenius least-squares projection (fep-167)

Metric/optimality extension of the fep-162 symmetrization: the carrier
is the plain-matrix type `Fin n → Fin n → ℝ` with the Frobenius
quadratic form `frobeniusSq X = ∑ i, ∑ j, X i j * X i j`.  For symmetric
`S`, `H − S = (H − symmetrize H) + (symmetrize H − S)` splits into the
skew residual and a symmetric residual, whose Frobenius cross term
vanishes — the exact Pythagoras split, minimality with the equality
boundary, and uniqueness of the minimizer follow. -/

section FrobeniusProjection

variable {n : ℕ}

/-- Frobenius inner product of plain real matrices indexed by `Fin n`. -/
def frobeniusInner (X Y : Fin n → Fin n → ℝ) : ℝ := ∑ i, ∑ j, X i j * Y i j

/-- Squared Frobenius form of a plain real matrix. -/
def frobeniusSq (X : Fin n → Fin n → ℝ) : ℝ := frobeniusInner X X

/-- A skew matrix is Frobenius-orthogonal to a symmetric matrix: the
finite form of the continuum fact that antisymmetric and symmetric
parts are orthogonal. -/
theorem frobeniusInner_skew_symmetric (A B : Fin n → Fin n → ℝ)
    (hA : SkewSymmetric A) (hB : SymmetricOf B) : frobeniusInner A B = 0 := by
  have key : frobeniusInner A B = ∑ i, ∑ j, A i j * B i j := rfl
  have negated : frobeniusInner A B = -frobeniusInner A B := by
    calc frobeniusInner A B
        = ∑ i, ∑ j, A i j * B i j := key
      _ = ∑ i, ∑ j, A j i * B j i := sum_swapPairs
      _ = ∑ i, ∑ j, -(A i j * B i j) := by
            refine Finset.sum_congr rfl fun i _ => ?_
            exact Finset.sum_congr rfl fun j _ => by rw [hA j i, hB i j]; ring
      _ = -∑ i, ∑ j, A i j * B i j := sum_negPairs
      _ = -frobeniusInner A B := by rw [key]
  linarith

/-- The raw-minus-symmetrized residual `H - symmetrize H` is
skew-symmetric: symmetrization removes exactly the symmetric part. -/
theorem sub_symmetrize_skew (H : Fin n → Fin n → ℝ) : SkewSymmetric (H - symmetrize H) := by
  intro i j
  show H i j - symmetrize H i j = -(H j i - symmetrize H j i)
  simp only [symmetrize]
  ring

/-- The difference of two symmetric matrices is symmetric. -/
theorem sub_symmetric {A B : Fin n → Fin n → ℝ}
    (hA : SymmetricOf A) (hB : SymmetricOf B) : SymmetricOf (A - B) := by
  intro i j
  show A i j - B i j = A j i - B j i
  rw [hA i j, hB i j]

/-- Expansion of the squared Frobenius form of a pointwise sum: the
cross term is exactly `2 * frobeniusInner A B`. -/
theorem frobeniusSq_add (A B : Fin n → Fin n → ℝ) :
    frobeniusSq (A + B) = frobeniusSq A + frobeniusSq B + 2 * frobeniusInner A B := by
  have point : ∀ i j : Fin n, (A i j + B i j) * (A i j + B i j)
      = A i j * A i j + B i j * B i j + 2 * (A i j * B i j) := fun i j => by ring
  simp only [frobeniusSq, frobeniusInner, Pi.add_apply]
  rw [Finset.sum_congr rfl fun i _ => Finset.sum_congr rfl fun j _ => point i j]
  simp only [Finset.sum_add_distrib, Finset.mul_sum]

/-- A matrix whose squared Frobenius form vanishes is the zero matrix:
the form is a sum of squares. -/
theorem frobeniusSq_eq_zero {X : Fin n → Fin n → ℝ} (h : frobeniusSq X = 0) : X = 0 := by
  funext i j
  have h0 : ∑ i, ∑ j, X i j * X i j = 0 := h
  have hout : ∀ k : Fin n, ∑ j, X k j * X k j = 0 := fun k =>
    (Finset.sum_eq_zero_iff_of_nonneg
      (fun k _ => Finset.sum_nonneg fun j _ => mul_self_nonneg (X k j))).mp h0 k
      (Finset.mem_univ k)
  exact mul_self_eq_zero.mp
    ((Finset.sum_eq_zero_iff_of_nonneg fun j (_ : j ∈ Finset.univ) =>
      mul_self_nonneg (X i j)).mp (hout i) j (Finset.mem_univ j))

/-- **fep-167 (exact Frobenius Pythagoras).**  For symmetric `S` the
squared Frobenius norm splits exactly across the symmetrization residual
and the projection residual:
`‖H − S‖²_F = ‖H − symmetrize H‖²_F + ‖symmetrize H − S‖²_F`. -/
theorem fep167_frobenius_pythagoras (H S : Fin n → Fin n → ℝ) (hS : SymmetricOf S) :
    frobeniusSq (H - S)
      = frobeniusSq (H - symmetrize H) + frobeniusSq (symmetrize H - S) := by
  have hsplit : H - S = (H - symmetrize H) + (symmetrize H - S) := by
    funext i j
    simp only [Pi.add_apply, Pi.sub_apply]
    ring
  rw [hsplit, frobeniusSq_add,
    frobeniusInner_skew_symmetric (H - symmetrize H) (symmetrize H - S)
      (sub_symmetrize_skew H) (sub_symmetric (symmetrize_symmetric H) hS)]
  ring

/-- **fep-167 (minimality with the equality boundary).**  `symmetrize H`
is the Frobenius least-squares approximation of `H` among symmetric
matrices: `‖H − symmetrize H‖²_F ≤ ‖H − S‖²_F` for every symmetric `S`,
with equality exactly at `S = symmetrize H`. -/
theorem fep167_symmetrize_minimizes (H S : Fin n → Fin n → ℝ) (hS : SymmetricOf S) :
    frobeniusSq (H - symmetrize H) ≤ frobeniusSq (H - S)
      ∧ (frobeniusSq (H - symmetrize H) = frobeniusSq (H - S) ↔ S = symmetrize H) := by
  have hp := fep167_frobenius_pythagoras H S hS
  have hnn : 0 ≤ frobeniusSq (symmetrize H - S) := by
    simp only [frobeniusSq, frobeniusInner]
    exact Finset.sum_nonneg fun i _ => Finset.sum_nonneg fun j _ => mul_self_nonneg _
  refine ⟨?_, ?_⟩
  · linarith
  · constructor
    · intro hEq
      have hsum : frobeniusSq (symmetrize H - S) = 0 := by linarith
      exact (sub_eq_zero.mp (frobeniusSq_eq_zero hsum)).symm
    · intro hS'
      rw [hS']

/-- **fep-167 (uniqueness).**  Among symmetric matrices the Frobenius
least-squares minimizer of `H` is unique: any symmetric `S` attaining
the minimal squared distance coincides with `symmetrize H`. -/
theorem fep167_projection_unique (H S : Fin n → Fin n → ℝ) (hS : SymmetricOf S)
    (hmin : ∀ T : Fin n → Fin n → ℝ, SymmetricOf T →
      frobeniusSq (H - S) ≤ frobeniusSq (H - T)) :
    S = symmetrize H := by
  have hle : frobeniusSq (H - S) ≤ frobeniusSq (H - symmetrize H) :=
    hmin (symmetrize H) (symmetrize_symmetric H)
  have hge : frobeniusSq (H - symmetrize H) ≤ frobeniusSq (H - S) :=
    (fep167_symmetrize_minimizes H S hS).1
  exact ((fep167_symmetrize_minimizes H S hS).2).mp (le_antisymm hge hle)

/-- The residual-example datum: the nonsymmetric two-direction matrix
`[[0, 1], [0, 0]]`. -/
def fep167ResidualH : Fin 2 → Fin 2 → ℝ :=
  fun i j => if i = 0 ∧ j = 1 then 1 else 0

/-- **fep-167 (residual example).**  The nonsymmetric datum
`fep167ResidualH = [[0, 1], [0, 0]]` has symmetrizer
`[[0, 1/2], [1/2, 0]]`, so the squared Frobenius residual of the
projection is `1/2 ≠ 0`: the residual genuinely does not vanish on
nonsymmetric data. -/
theorem fep167_residual_example :
    frobeniusSq (fep167ResidualH - symmetrize fep167ResidualH) = 1 / 2
      ∧ frobeniusSq (fep167ResidualH - symmetrize fep167ResidualH) ≠ 0 := by
  have hval : frobeniusSq (fep167ResidualH - symmetrize fep167ResidualH) = 1 / 2 := by
    simp only [frobeniusSq, frobeniusInner, Pi.sub_apply, fep167ResidualH, symmetrize,
      Fin.sum_univ_two]
    norm_num
  exact ⟨hval, by rw [hval]; norm_num⟩

end FrobeniusProjection

/-! ## Quantitative control of the uncancelled divergence remainder (fep-168)

**Hypothesis map** (t-0060 load-bearing refinement): on the fep-163
carrier `weightedDivergence − dot (divQ DQ) g = dot (mulVec Q g) dlogp`
holds identically, so the remainder identity needs exactly
{`Q` skew (else the trace slot survives against off-diagonal `H`),
`H` symmetric (else the trace slot survives), and
`dot (mulVec Q g) dlogp = 0` (the coupling slot)}.  `dlogp = −g` is the
canonical sufficient — not necessary — instance: the skew quadratic form
dies via `skewQuadratic_eq_zero`.

The budget is stated in squared form `(weightedDivergence …)² ≤
dot r r * dot g g` with `r = divQ DQ` (no square roots, stays
computable), with the `abs`-product corollary.  The equality witness
introduces the NEW aligned gradient datum `fep168AlignedG = (1, 0)`:
the pinned `remainderG = (1, 1)` is deliberately not repinned — it is
not aligned with `divQ remainderDQ = (1, 0)` (bound `2`, value `1`,
strict). -/

section RemainderBudget

variable {n : ℕ}

/-- Plain-dot Cauchy–Schwarz in squared form: `(r · g)² ≤ (r · r)(g · g)`
for plain real vectors — no square roots, no `noncomputable`. -/
theorem dot_sq_le_sq_mul_sq (r g : Fin n → ℝ) :
    (dot r g) ^ 2 ≤ dot r r * dot g g := by
  have hrr : dot r r = ∑ i, r i ^ 2 := by
    simp only [dot]
    exact Finset.sum_congr rfl fun i _ => (pow_two (r i)).symm
  have hgg : dot g g = ∑ i, g i ^ 2 := by
    simp only [dot]
    exact Finset.sum_congr rfl fun i _ => (pow_two (g i)).symm
  rw [hrr, hgg]
  exact Finset.sum_mul_sq_le_sq_mul_sq Finset.univ r g

/-- **fep-168 (remainder identity).**  Under `Q` skew, `H` symmetric,
and the stationary coupling `dlogp = −g`, the weighted divergence of the
candidate current is exactly the remainder dot product
`dot (divQ DQ) g`: the trace slot cancels (`skewTrace_eq_zero`), the
quadratic slot cancels (`skewQuadratic_eq_zero`), and nothing else
survives the expansion. -/
theorem fep168_weightedDivergence_eq_remainderDot (Q H DQ : Fin n → Fin n → ℝ)
    (g dlogp : Fin n → ℝ) (hQ : SkewSymmetric Q) (hH : SymmetricOf H)
    (hcoup : ∀ i, dlogp i = -g i) :
    weightedDivergence Q H DQ g dlogp = dot (divQ DQ) g := by
  rw [solenoidal_expansion Q H DQ g dlogp hcoup,
    skewTrace_eq_zero Q H hQ hH, skewQuadratic_eq_zero Q g hQ]
  ring

/-- **fep-168 (squared remainder budget).**  The uncancelled remainder
obeys the squared Cauchy–Schwarz budget
`(weightedDivergence …)² ≤ (∑ rᵢ²)(∑ gᵢ²)` with `r = divQ DQ`: the
remainder magnitude is bounded by the product of the transport-
divergence and gradient norms instead of being assumed to vanish
(fep-165's witness shows the unconditional drop is genuinely false). -/
theorem fep168_remainder_sq_budget (Q H DQ : Fin n → Fin n → ℝ)
    (g dlogp : Fin n → ℝ) (hQ : SkewSymmetric Q) (hH : SymmetricOf H)
    (hcoup : ∀ i, dlogp i = -g i) :
    (weightedDivergence Q H DQ g dlogp) ^ 2
      ≤ dot (divQ DQ) (divQ DQ) * dot g g := by
  rw [fep168_weightedDivergence_eq_remainderDot Q H DQ g dlogp hQ hH hcoup]
  exact dot_sq_le_sq_mul_sq (divQ DQ) g

/-- **fep-168 (absolute budget).**  The squared budget restated over
`abs` products: `|weightedDivergence …| · |weightedDivergence …| ≤
(∑ rᵢ²)(∑ gᵢ²)` — the same bound with no square roots. -/
theorem fep168_absolute_budget (Q H DQ : Fin n → Fin n → ℝ)
    (g dlogp : Fin n → ℝ) (hQ : SkewSymmetric Q) (hH : SymmetricOf H)
    (hcoup : ∀ i, dlogp i = -g i) :
    abs (weightedDivergence Q H DQ g dlogp) * abs (weightedDivergence Q H DQ g dlogp)
      ≤ dot (divQ DQ) (divQ DQ) * dot g g := by
  have habs : abs (weightedDivergence Q H DQ g dlogp)
      * abs (weightedDivergence Q H DQ g dlogp)
      = (weightedDivergence Q H DQ g dlogp) ^ 2 := by
    rw [← abs_mul, abs_of_nonneg (mul_self_nonneg _), pow_two]
  rw [habs]
  exact fep168_remainder_sq_budget Q H DQ g dlogp hQ hH hcoup

/-- The aligned gradient for the equality witness: `(1, 0)` — aligned
with `divQ remainderDQ = (1, 0)`.  New datum; the pinned
`remainderG = (1, 1)` is not repinned (it is not aligned). -/
def fep168AlignedG : Fin 2 → ℝ := fun i => if i = 0 then 1 else 0

/-- The symmetric Hessian-slot datum `diag(1, 2)` for the equality
witness. -/
def fep168AlignedH : Fin 2 → Fin 2 → ℝ :=
  fun i j => if i = 0 ∧ j = 0 then 1 else if i = 1 ∧ j = 1 then 2 else 0

/-- The equality-witness Hessian-slot datum is symmetric. -/
theorem fep168AlignedH_symmetric : SymmetricOf fep168AlignedH := by
  intro i j
  fin_cases i <;> fin_cases j <;> simp [fep168AlignedH]

/-- **fep-168 (equality attained).**  On the aligned datum —
`Q = witnessQ = [[0, 1], [-1, 0]]` (skew), `H = fep168AlignedH =
diag(1, 2)` (symmetric), `DQ = remainderDQ` (so `divQ DQ = (1, 0)`), and
the NEW aligned gradient `fep168AlignedG = (1, 0)` with the canonical
coupling `dlogp = −g` — the squared budget is attained with equality
and the data is nonzero: `(weightedDivergence …)² = dot r r * dot g g`
with `dot fep168AlignedG fep168AlignedG = 1 ≠ 0`.  Via
`fep168_weightedDivergence_eq_remainderDot` this is simultaneously the
Cauchy–Schwarz equality at the dot level, where `r = g = (1, 0)`. -/
theorem fep168_equality_attained :
    (weightedDivergence witnessQ fep168AlignedH remainderDQ fep168AlignedG
        (fun i => -fep168AlignedG i)) ^ 2
      = dot (divQ remainderDQ) (divQ remainderDQ) * dot fep168AlignedG fep168AlignedG
      ∧ dot fep168AlignedG fep168AlignedG ≠ 0 := by
  have hid : weightedDivergence witnessQ fep168AlignedH remainderDQ fep168AlignedG
      (fun i => -fep168AlignedG i) = dot (divQ remainderDQ) fep168AlignedG :=
    fep168_weightedDivergence_eq_remainderDot witnessQ fep168AlignedH remainderDQ
      fep168AlignedG (fun i => -fep168AlignedG i) witnessQ_skew fep168AlignedH_symmetric
      (fun i => rfl)
  have hr : divQ remainderDQ = fep168AlignedG := by
    funext l
    fin_cases l <;>
      simp only [divQ, remainderDQ, fep168AlignedG, Fin.sum_univ_two] <;> norm_num
  constructor
  · rw [hid, hr]
    ring
  · simp only [dot, fep168AlignedG, Fin.sum_univ_two]
    norm_num

end RemainderBudget

end FEP.GeometricMechanics
