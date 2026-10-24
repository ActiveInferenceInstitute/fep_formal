module
public import FepSketches.compositions.geometric_mechanics
public import Mathlib.Tactic

@[expose] public section
namespace FEP103GeometricBridgeControls
open FEP.GeometricMechanics
open scoped BigOperators
noncomputable section

def rawH : Fin 2 → Fin 2 → ℝ :=
  fun i j => if i = 0 then (if j = 0 then 1 else 2) else (if j = 0 then 4 else 3)

def identityQ : Fin 2 → Fin 2 → ℝ := fun i j => if i = j then 1 else 0

theorem raw_not_symmetric : ¬ SymmetricOf rawH := by
  intro h
  have entry := h (0 : Fin 2) (1 : Fin 2)
  norm_num [rawH] at entry

theorem raw_trace_two : traceOf (mulOf witnessQ rawH) = 2 := by
  norm_num [traceOf, mulOf, Fin.sum_univ_two, witnessQ, rawH]

theorem constructed_symmetric : SymmetricOf (symmetrize rawH) := by
  exact (FEPComposed.fep162_clairautSymmetrize_extends_fep161_skewCancellation
    witnessQ rawH witnessQ_skew).1

theorem constructed_trace_zero : traceOf (mulOf witnessQ (symmetrize rawH)) = 0 := by
  exact (FEPComposed.fep162_clairautSymmetrize_extends_fep161_skewCancellation
    witnessQ rawH witnessQ_skew).2

theorem raw_trace_differs_from_constructed :
    traceOf (mulOf witnessQ rawH) ≠ traceOf (mulOf witnessQ (symmetrize rawH)) := by
  rw [raw_trace_two, constructed_trace_zero]
  norm_num

theorem identity_not_skew : ¬ SkewSymmetric identityQ := by
  intro h
  have diagonal := h (0 : Fin 2) (0 : Fin 2)
  norm_num [identityQ] at diagonal

theorem identity_trace_four : traceOf (mulOf identityQ (symmetrize rawH)) = 4 := by
  norm_num [traceOf, mulOf, Fin.sum_univ_two, identityQ, symmetrize, rawH]

theorem empty_imported_boundary (Q H : Fin 0 → Fin 0 → ℝ) :
    SymmetricOf (symmetrize H) ∧ traceOf (mulOf Q (symmetrize H)) = 0 := by
  exact FEPComposed.fep162_clairautSymmetrize_extends_fep161_skewCancellation Q H
    (by intro i; exact Fin.elim0 i)

end
end FEP103GeometricBridgeControls

#check fep_fep162.FEP162.fep162_symmetrize_symmetric
#print axioms fep_fep162.FEP162.fep162_symmetrize_symmetric
#check fep_fep161.FEP161.fep161_skewTrace_eq_zero
#print axioms fep_fep161.FEP161.fep161_skewTrace_eq_zero
#check FEPComposed.fep162_clairautSymmetrize_extends_fep161_skewCancellation
#print axioms FEPComposed.fep162_clairautSymmetrize_extends_fep161_skewCancellation
#check FEP103GeometricBridgeControls.raw_not_symmetric
#print axioms FEP103GeometricBridgeControls.raw_not_symmetric
#check FEP103GeometricBridgeControls.raw_trace_two
#print axioms FEP103GeometricBridgeControls.raw_trace_two
#check FEP103GeometricBridgeControls.constructed_symmetric
#print axioms FEP103GeometricBridgeControls.constructed_symmetric
#check FEP103GeometricBridgeControls.constructed_trace_zero
#print axioms FEP103GeometricBridgeControls.constructed_trace_zero
#check FEP103GeometricBridgeControls.raw_trace_differs_from_constructed
#print axioms FEP103GeometricBridgeControls.raw_trace_differs_from_constructed
#check FEP103GeometricBridgeControls.identity_not_skew
#print axioms FEP103GeometricBridgeControls.identity_not_skew
#check FEP103GeometricBridgeControls.identity_trace_four
#print axioms FEP103GeometricBridgeControls.identity_trace_four
#check FEP103GeometricBridgeControls.empty_imported_boundary
#print axioms FEP103GeometricBridgeControls.empty_imported_boundary
