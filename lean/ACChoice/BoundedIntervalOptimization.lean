import FepSketches.compositions.finite_policy_action
import Mathlib.Data.Int.Order.Basic

/-!
Conditional global-approximation boundary for a finite cover of a represented
policy domain.  The theorem separates the mathematical obligations that a
runtime certificate must discharge: coverage, sound cell lower bounds, an
incumbent upper bound, and the requested additive tolerance.

This module does not prove that a floating-point EFE implementation supplies
those obligations.  It also does not use choice to construct a candidate: the
candidate is an explicit input with a checked upper-bound premise.
-/
namespace FEPComposed.ACChoice

/- All objective bounds are integer ticks under one declared dyadic scale. -/
structure CertifiedObjectiveCell (Policy : Type) (objective : Policy → Int) where
  contains : Policy → Prop
  lowerBound : Int
  upperBound : Int
  lowerSound : ∀ policy, contains policy → lowerBound ≤ objective policy
  upperSound : ∀ policy, contains policy → objective policy ≤ upperBound

/-- Every policy in the declared domain is covered by a listed terminal cell. -/
def CellsCover {Policy : Type} {objective : Policy → Int}
    (cells : List (CertifiedObjectiveCell Policy objective)) : Prop :=
  ∀ policy, ∃ cell, cell ∈ cells ∧ cell.contains policy

/-- A declared global lower bound follows from a finite terminal-cell cover. -/
theorem covered_cells_global_lower_bound
    {Policy : Type} {objective : Policy → Int}
    (cells : List (CertifiedObjectiveCell Policy objective))
    (covers : CellsCover cells)
    (globalLower : Int)
    (cellLower : ∀ cell ∈ cells, globalLower ≤ cell.lowerBound) :
    ∀ policy, globalLower ≤ objective policy := by
  intro policy
  obtain ⟨cell, hcell, hpolicy⟩ := covers policy
  exact le_trans (cellLower cell hcell) (cell.lowerSound policy hpolicy)

/--
If a finite cover supplies sound lower bounds and an explicit feasible
incumbent supplies an upper bound, the incumbent is within `tolerance` of
every represented policy.  The statement is additive and does not assert exact
attainment of an infimum.
-/
theorem bounded_global_approximation
    {Policy : Type} {objective : Policy → Int}
    (cells : List (CertifiedObjectiveCell Policy objective))
    (covers : CellsCover cells)
    (globalLower upperBound tolerance : Int)
    (cellLower : ∀ cell ∈ cells, globalLower ≤ cell.lowerBound)
    (incumbent : Policy)
    (incumbentUpper : objective incumbent ≤ upperBound)
    (gap : upperBound ≤ globalLower + tolerance) :
    ∀ policy, objective incumbent ≤ objective policy + tolerance := by
  have lower := covered_cells_global_lower_bound cells covers globalLower cellLower
  intro policy
  calc
    objective incumbent ≤ upperBound := incumbentUpper
    _ ≤ globalLower + tolerance := gap
    _ = tolerance + globalLower := Int.add_comm _ _
    _ ≤ tolerance + objective policy := add_le_add_right (lower policy) tolerance
    _ = objective policy + tolerance := Int.add_comm _ _

#print axioms covered_cells_global_lower_bound
#print axioms bounded_global_approximation

end FEPComposed.ACChoice
