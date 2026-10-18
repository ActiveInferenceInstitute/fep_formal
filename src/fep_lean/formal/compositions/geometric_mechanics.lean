module
public import FepSketches.families.core_thermodynamics
public import FepSketches.families.geometric_mechanics
public import FepSketches.families.standalone_efe_formalizations
public import FepSketches.geometric_mechanics

@[expose] public section

/-!
# Geometric-mechanics topic compositions

Seven bridges pair the new geometric-mechanics theorems with their nearest
catalogue endpoints.  Each conjunction keeps both endpoint laws visible
instead of asserting an unproved reduction; the necessity witness is paired
with the divergence-free cycle carrier to bound exactly what stationarity
and antisymmetry imply.
-/

namespace FEPComposed

open FEP.GeometricMechanics
open FEP

/-- The plain-matrix trace and quadratic cancellations are paired with the
Helmholtz–Ao rate-field decomposition and its law-weighted skew clause; the
plain pointwise carrier and the law-weighted finite carrier stay distinct. -/
theorem fep161_skewCancellation_extends_fep160_aoNess
    {n : ℕ} (Q H : Fin n → Fin n → ℝ) (hQ : SkewSymmetric Q)
    (hH : SymmetricOf H) (g : Fin n → ℝ)
    {rate : Fin n → Fin n → ℝ} {law : FiniteLaw (Fin n)}
    (hSupport : ∀ i, 0 < law i) (i j : Fin n) :
    (traceOf (mulOf Q H) = 0 ∧ dot g (mulVec Q g) = 0) ∧
      (law i * fep_fep160.FEP160.fep160_circulationPart rate law i j =
        -(law j * fep_fep160.FEP160.fep160_circulationPart rate law j i)) := by
  exact
    ⟨⟨fep_fep161.FEP161.fep161_skewTrace_eq_zero Q H hQ hH,
        fep_fep161.FEP161.fep161_skewQuadratic_eq_zero Q g hQ⟩,
      fep_fep160.FEP160.fep160_circulationPart_skew hSupport i j⟩

/-- The symmetrization construction discharges exactly the symmetric-matrix
hypothesis of the trace cancellation it is paired with. -/
theorem fep162_clairautSymmetrize_extends_fep161_skewCancellation
    {n : ℕ} (Q H : Fin n → Fin n → ℝ) (hQ : SkewSymmetric Q) :
    (SymmetricOf (FEP.GeometricMechanics.symmetrize H) ∧
      traceOf (mulOf Q (FEP.GeometricMechanics.symmetrize H)) = 0) := by
  have hSym : SymmetricOf (FEP.GeometricMechanics.symmetrize H) :=
    fep_fep162.FEP162.fep162_symmetrize_symmetric H
  have hTrace : traceOf (mulOf Q (FEP.GeometricMechanics.symmetrize H)) = 0 :=
    fep_fep161.FEP161.fep161_skewTrace_eq_zero Q
      (FEP.GeometricMechanics.symmetrize H) hQ hSym
  exact ⟨hSym, hTrace⟩

/-- The exact three-term solenoidal expansion under the stationary coupling
is paired with fep-025's divergence-free current stationarity; the
derivative-data carrier and the transition-row carrier stay distinct. -/
theorem fep163_solenoidalExpansion_extends_fep025_current
    {n : ℕ} (Q H DQ : Fin n → Fin n → ℝ) (g dlogp : Fin n → ℝ)
    (hcoup : ∀ i, dlogp i = -g i)
    {stationary : Fin n → ℝ} {transition : Matrix (Fin n) (Fin n) ℝ}
    (hrow : ∀ i, ∑ j, transition i j = 1)
    (hstat : ∀ j, ∑ i, stationary i * transition i j = stationary j)
    (i : Fin n) :
    (FEP.GeometricMechanics.weightedDivergence Q H DQ g dlogp
        = FEP.GeometricMechanics.traceOf (FEP.GeometricMechanics.mulOf Q H)
            - FEP.GeometricMechanics.dot g (FEP.GeometricMechanics.mulVec Q g)
            + FEP.GeometricMechanics.dot (FEP.GeometricMechanics.divQ DQ) g) ∧
      (fep_fep025.FEP025.fep025_divergence
          (fep_fep025.FEP025.fep025_transitionCurrent stationary transition) i
        = 0) := by
  exact
    ⟨fep_fep163.FEP163.fep163_solenoidal_expansion Q H DQ g dlogp hcoup,
      fep_fep025.FEP025.fep025_transitionCurrent_stationary
        stationary transition hrow hstat i⟩

/-- The graph-plane decomposition of the candidate current's divergence is
paired with fep-025's node-divergence current carrier; the flux-matrix
carrier and the transition-row carrier stay distinct. -/
theorem fep164_graphCurrent_extends_fep025_current
    {n : ℕ} (Q : Fin n → Fin n → ℝ) (g : Fin n → ℝ) (hQ : SkewSymmetric Q)
    (flow : Matrix (Fin n) (Fin n) ℝ) (i : Fin n) :
    (FEP.GeometricMechanics.nodeDiv (FEP.GeometricMechanics.currentOf Q g) i
        = FEP.GeometricMechanics.mulVec Q g i
          + g i * FEP.GeometricMechanics.rowSum Q i) ∧
      (∀ a b : Fin n,
        fep_fep025.FEP025.fep025_probabilityCurrent flow a b =
          -fep_fep025.FEP025.fep025_probabilityCurrent flow b a) := by
  exact
    ⟨fep_fep164.FEP164.fep164_graphDecomposition Q g hQ i,
      fun a b => fep_fep025.FEP025.fep025_probabilityCurrent_antisymm flow a b⟩

/-- The compiled necessity witness is paired with fep-025's divergence-free
cycle witness: jointly they bound exactly what stationarity and antisymmetry
imply. -/
theorem fep165_necessityWitness_extends_fep025_current :
    (FEP.GeometricMechanics.nodeDiv
        (FEP.GeometricMechanics.currentOf FEP.GeometricMechanics.witnessQ
          FEP.GeometricMechanics.witnessG) 0
      = 1) ∧
      (fep_fep025.FEP025.fep025_divergence
          fep_fep025.FEP025.fep025_cycleCurrent 0 = 0) := by
  exact
    ⟨fep_fep165.FEP165.fep165_witness_drop_fails,
      fep_fep025.FEP025.fep025_cycleCurrent_stationary 0⟩

/-- The Frobenius least-squares projection layer is paired with fep-162's
algebraic symmetrization construction: the exact Pythagoras split and the
minimality boundary hold against the constructed symmetric matrix, and the
construction is symmetric; no continuum Clairaut theorem and no
Bregman-projection existence claim enter. -/
theorem fep167_frobeniusProjection_extends_fep162_clairautSymmetrize
    {n : ℕ} (H S : Fin n → Fin n → ℝ) (hS : SymmetricOf S) :
    (frobeniusSq (H - S)
        = frobeniusSq (H - symmetrize H) + frobeniusSq (symmetrize H - S)) ∧
      (frobeniusSq (H - symmetrize H) ≤ frobeniusSq (H - S)) ∧
      SymmetricOf (FEP.GeometricMechanics.symmetrize H) := by
  refine ⟨?_, ?_, ?_⟩
  · exact fep_fep167.FEP167.fep167_frobenius_pythagoras H S hS
  · exact (fep_fep167.FEP167.fep167_symmetrize_minimizes H S hS).1
  · exact fep_fep162.FEP162.fep162_symmetrize_symmetric H

/-- The quantitative remainder budget is paired with fep-163's exact
three-term expansion: under the cancellation hypotheses the weighted
divergence is the expansion remainder `dot (divQ DQ) g`, and the squared
Cauchy–Schwarz budget bounds it instead of assuming it vanishes. -/
theorem fep168_remainderBound_extends_fep163_solenoidalExpansion
    {n : ℕ} (Q H DQ : Fin n → Fin n → ℝ) (g dlogp : Fin n → ℝ)
    (hQ : SkewSymmetric Q) (hH : SymmetricOf H) (hcoup : ∀ i, dlogp i = -g i) :
    (weightedDivergence Q H DQ g dlogp
        = FEP.GeometricMechanics.traceOf (FEP.GeometricMechanics.mulOf Q H)
          - FEP.GeometricMechanics.dot g (FEP.GeometricMechanics.mulVec Q g)
          + FEP.GeometricMechanics.dot (FEP.GeometricMechanics.divQ DQ) g) ∧
      ((weightedDivergence Q H DQ g dlogp) ^ 2
        ≤ FEP.GeometricMechanics.dot (FEP.GeometricMechanics.divQ DQ)
            (FEP.GeometricMechanics.divQ DQ)
          * FEP.GeometricMechanics.dot g g) := by
  exact
    ⟨fep_fep163.FEP163.fep163_solenoidal_expansion Q H DQ g dlogp hcoup,
      fep_fep168.FEP168.fep168_remainder_sq_budget Q H DQ g dlogp hQ hH hcoup⟩

end FEPComposed
