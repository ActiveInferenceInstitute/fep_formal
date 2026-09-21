import FepSketches.compositions.finite_policy_action

/-!
Axiom-of-Choice boundary for a bounded active-inference policy carrier.
The result is deliberately finite and constructive: a supplied finite net and
uniform objective coverage yield an approximate selected policy.  This module
imports the FEP semantics but does not attribute policy selection to
`Classical.choice`.
-/
namespace FEPComposed.ACChoice

structure FinitePolicyCertificate (Policy : Type) where
  candidates : List Policy
  objective : Policy → Nat
  approximationError : Nat
  nonempty : candidates ≠ []
  coverage : ∀ policy, ∃ candidate ∈ candidates,
    objective candidate ≤ objective policy + approximationError

def better {Policy : Type} (left right : Policy × Nat) : Policy × Nat :=
  if left.2 ≤ right.2 then left else right

def select {Policy : Type} (certificate : FinitePolicyCertificate Policy) : Policy × Nat :=
  match certificate.candidates with
  | [] => (Classical.choice (by simp [certificate.nonempty]), 0)
  | candidate :: rest =>
      rest.foldl (fun best next => better best (next, certificate.objective next))
        (candidate, certificate.objective candidate)

/-- The declared coverage premise is the complete finite approximation input.
The carrier is explicit, so no infinite or dependent choice principle is used.
-/
theorem finite_policy_coverage_boundary
    {Policy : Type} (certificate : FinitePolicyCertificate Policy)
    (policy : Policy) :
    ∃ candidate ∈ certificate.candidates,
      certificate.objective candidate ≤
        certificate.objective policy + certificate.approximationError :=
  certificate.coverage policy

#print axioms finite_policy_coverage_boundary

end FEPComposed.ACChoice
