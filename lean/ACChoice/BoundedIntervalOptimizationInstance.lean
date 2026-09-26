import ACChoice.BoundedIntervalOptimization

/-! A concrete finite exact-score instance exercising the generic certificate. -/
namespace FEPComposed.ACChoice

inductive ToyPolicy
  | first
  | second
  deriving DecidableEq

def toyObjective (_policy : ToyPolicy) : Int := 7

def toyCell : CertifiedObjectiveCell ToyPolicy toyObjective where
  contains := fun _ => True
  lowerBound := 7
  upperBound := 7
  lowerSound := by intro policy _; rfl
  upperSound := by intro policy _; rfl

def toyCells : List (CertifiedObjectiveCell ToyPolicy toyObjective) := [toyCell]

theorem toyCellsCover : CellsCover toyCells := by
  intro policy
  exact ⟨toyCell, by simp [toyCells], trivial⟩

theorem toyGlobalLower :
    ∀ cell ∈ toyCells, (7 : Int) ≤ cell.lowerBound := by
  intro cell membership
  have equal : cell = toyCell := List.mem_singleton.mp membership
  subst cell
  rfl

theorem toyExactOptimizationInstance :
    ∀ policy, toyObjective ToyPolicy.first ≤ toyObjective policy + 0 := by
  apply bounded_global_approximation toyCells toyCellsCover 7 7 0 toyGlobalLower
    ToyPolicy.first
  · rfl
  · rfl

#print axioms toyExactOptimizationInstance
#print axioms toyCellsCover
#print axioms toyGlobalLower

end FEPComposed.ACChoice
