module
public import FepSketches.finite_information

@[expose] public section

/-!
# Finite Markov blankets and blanket-respecting dynamics

The static model makes internal and external states independent after
conditioning on the sensory-active blanket.  The dynamical model encodes the
permitted dependency graph in kernel source types, then builds a normalized
four-component transition law by products of normalized rows.
-/

namespace FEP.MarkovBlanket

open FEP FEP.FiniteInformation Finset
open scoped BigOperators

variable {Internal Sensory Active External : Type*}
  [Fintype Internal] [Fintype Sensory] [Fintype Active] [Fintype External]

/-- Sensory-active blanket state. -/
abbrev Blanket (Sensory Active : Type*) := Sensory × Active

/-- Static state arranged as blanket, internal, and external coordinates. -/
abbrev StaticState (Internal Sensory Active External : Type*) :=
  ((Blanket Sensory Active) × Internal) × External

/-- A static blanket factorization `P(b,i,e)=P(b)P(i|b)P(e|b)`. -/
structure StaticModel (Internal Sensory Active External : Type*)
    [Fintype Internal] [Fintype Sensory] [Fintype Active] [Fintype External] where
  blanketLaw : FiniteLaw (Blanket Sensory Active)
  internalGiven : FiniteKernel (Blanket Sensory Active) Internal
  externalGiven : FiniteKernel (Blanket Sensory Active) External

/-- Lift the external conditional so it can follow a sampled blanket-internal
pair without acquiring a dependency on the internal coordinate. -/
def externalLift (model : StaticModel Internal Sensory Active External) :
    FiniteKernel ((Blanket Sensory Active) × Internal) External where
  mass bi external := model.externalGiven bi.1 external
  nonneg bi external := model.externalGiven.nonneg bi.1 external
  sum_one bi := model.externalGiven.sum_one bi.1

/-- Normalized static joint law induced by a Markov-blanket factorization. -/
def staticJoint (model : StaticModel Internal Sensory Active External) :
    FiniteLaw (StaticState Internal Sensory Active External) :=
  (externalLift model).joint
    (model.internalGiven.joint model.blanketLaw)

/-- The generated joint has the exact Markov-blanket factorization. -/
theorem staticJoint_factorization
    (model : StaticModel Internal Sensory Active External)
    (blanket : Blanket Sensory Active) (internal : Internal)
    (external : External) :
    staticJoint model ((blanket, internal), external) =
      (model.blanketLaw blanket * model.internalGiven blanket internal) *
        model.externalGiven blanket external := rfl

/-- Conditional internal-external law at one blanket value. -/
def conditionalJoint
    (model : StaticModel Internal Sensory Active External)
    (blanket : Blanket Sensory Active) : FiniteLaw (Internal × External) :=
  (model.internalGiven.row blanket).product
    (model.externalGiven.row blanket)

/-- Every blanket-indexed conditional law has zero internal-external mutual
information because it is an exact independent product. -/
theorem conditional_mutualInformation_zero
    (model : StaticModel Internal Sensory Active External)
    (blanket : Blanket Sensory Active) :
    mutualInformation (conditionalJoint model blanket) = 0 := by
  exact mutualInformation_product_eq_zero
    (model.internalGiven.row blanket) (model.externalGiven.row blanket)

/-- Internal and external states factorize after conditioning on a
positive-mass blanket state. -/
theorem conditional_internal_external_factorization
    (model : StaticModel Internal Sensory Active External)
    (blanket : Blanket Sensory Active) (hblanket : 0 < model.blanketLaw blanket)
    (internal : Internal) (external : External) :
    staticJoint model ((blanket, internal), external) /
        model.blanketLaw blanket =
      conditionalJoint model blanket (internal, external) := by
  rw [staticJoint_factorization]
  change
    ((model.blanketLaw blanket * model.internalGiven blanket internal) *
          model.externalGiven blanket external) /
        model.blanketLaw blanket =
      model.internalGiven blanket internal *
        model.externalGiven blanket external
  field_simp [ne_of_gt hblanket]

/-- Summing the conditional joint over external states recovers the internal
conditional law. -/
theorem conditionalJoint_fstMarginal
    (model : StaticModel Internal Sensory Active External)
    (blanket : Blanket Sensory Active) (internal : Internal) :
    (conditionalJoint model blanket).fstMarginal internal =
      model.internalGiven blanket internal := by
  change
    (∑ external : External,
      model.internalGiven blanket internal *
        model.externalGiven blanket external) = _
  rw [← Finset.mul_sum, model.externalGiven.sum_one, mul_one]

/-- Dynamical state in internal-sensory-active-external order. -/
abbrev DynamicState (Internal Sensory Active External : Type*) :=
  Internal × (Sensory × (Active × External))

/-- Markov-blanket dependency graph for one transition step.

Internal and active updates can see only current internal-sensory state;
sensory and external updates can see only current external-active state.
-/
structure Dynamics (Internal Sensory Active External : Type*)
    [Fintype Internal] [Fintype Sensory] [Fintype Active] [Fintype External] where
  internalFlow : FiniteKernel (Internal × Sensory) Internal
  sensoryFlow : FiniteKernel (External × Active) Sensory
  activeFlow : FiniteKernel (Internal × Sensory) Active
  externalFlow : FiniteKernel (External × Active) External

/-- Static blanket model induced by one row of the dynamical transition.
The next sensory-active blanket has the product of its two local flow rows;
the next internal and external conditionals are constant in that new blanket
because the transition row fixes the current state. -/
def nextStaticModel
    (dynamics : Dynamics Internal Sensory Active External)
    (current : DynamicState Internal Sensory Active External) :
    StaticModel Internal Sensory Active External where
  blanketLaw :=
    (dynamics.sensoryFlow.row (current.2.2.2, current.2.2.1)).product
      (dynamics.activeFlow.row (current.1, current.2.1))
  internalGiven :=
    { mass := fun _ internal =>
        dynamics.internalFlow (current.1, current.2.1) internal
      nonneg := fun _ internal =>
        dynamics.internalFlow.nonneg (current.1, current.2.1) internal
      sum_one := fun _ =>
        dynamics.internalFlow.sum_one (current.1, current.2.1) }
  externalGiven :=
    { mass := fun _ external =>
        dynamics.externalFlow (current.2.2.2, current.2.2.1) external
      nonneg := fun _ external =>
        dynamics.externalFlow.nonneg (current.2.2.2, current.2.2.1) external
      sum_one := fun _ =>
        dynamics.externalFlow.sum_one (current.2.2.2, current.2.2.1) }

/-- Reassociate a dynamical state as blanket, internal, and external
coordinates without changing any component. -/
def staticCoordinates
    (state : DynamicState Internal Sensory Active External) :
    StaticState Internal Sensory Active External :=
  (((state.2.1, state.2.2.1), state.1), state.2.2.2)

/-- Product law for the next four-component state. -/
def nextLaw (dynamics : Dynamics Internal Sensory Active External)
    (current : DynamicState Internal Sensory Active External) :
    FiniteLaw (DynamicState Internal Sensory Active External) :=
  let internalSensory := (current.1, current.2.1)
  let externalActive := (current.2.2.2, current.2.2.1)
  (dynamics.internalFlow.row internalSensory).product
    ((dynamics.sensoryFlow.row externalActive).product
      ((dynamics.activeFlow.row internalSensory).product
        (dynamics.externalFlow.row externalActive)))

/-- Normalized transition kernel generated by blanket-respecting flows. -/
def transition (dynamics : Dynamics Internal Sensory Active External) :
    FiniteKernel
      (DynamicState Internal Sensory Active External)
      (DynamicState Internal Sensory Active External) where
  mass current next := nextLaw dynamics current next
  nonneg current next := (nextLaw dynamics current).nonneg next
  sum_one current := (nextLaw dynamics current).sum_one

/-- The dynamical transition exposes its four local factors exactly. -/
theorem transition_factorization
    (dynamics : Dynamics Internal Sensory Active External)
    (current next : DynamicState Internal Sensory Active External) :
    transition dynamics current next =
      dynamics.internalFlow (current.1, current.2.1) next.1 *
        (dynamics.sensoryFlow (current.2.2.2, current.2.2.1) next.2.1 *
          (dynamics.activeFlow (current.1, current.2.1) next.2.2.1 *
            dynamics.externalFlow
              (current.2.2.2, current.2.2.1) next.2.2.2)) := rfl

/-- Every dynamical transition row is exactly the static joint law of its
induced next-state blanket model after coordinate reassociation.  This is the
explicit seam between the dynamical dependency graph and the static blanket
factorization; it does not claim preservation after mixing different current
states under an arbitrary prior. -/
theorem transition_eq_staticJoint_nextStaticModel
    (dynamics : Dynamics Internal Sensory Active External)
    (current next : DynamicState Internal Sensory Active External) :
    transition dynamics current next =
      staticJoint (nextStaticModel dynamics current)
        (staticCoordinates next) := by
  change
    dynamics.internalFlow (current.1, current.2.1) next.1 *
          (dynamics.sensoryFlow
              (current.2.2.2, current.2.2.1) next.2.1 *
            (dynamics.activeFlow
                (current.1, current.2.1) next.2.2.1 *
              dynamics.externalFlow
                (current.2.2.2, current.2.2.1) next.2.2.2)) =
      ((dynamics.sensoryFlow
              (current.2.2.2, current.2.2.1) next.2.1 *
            dynamics.activeFlow
              (current.1, current.2.1) next.2.2.1) *
          dynamics.internalFlow (current.1, current.2.1) next.1) *
        dynamics.externalFlow
          (current.2.2.2, current.2.2.1) next.2.2.2
  ring

/-- At every positive-mass next blanket, a transition row makes next internal
and external states conditionally factorize.  The conditioning claim is about
one fixed transition row; mixtures over current states require additional
hypotheses. -/
theorem transition_row_conditional_factorization
    (dynamics : Dynamics Internal Sensory Active External)
    (current next : DynamicState Internal Sensory Active External)
    (hblanket :
      0 < (nextStaticModel dynamics current).blanketLaw
        (next.2.1, next.2.2.1)) :
    transition dynamics current next /
        (nextStaticModel dynamics current).blanketLaw
          (next.2.1, next.2.2.1) =
      conditionalJoint (nextStaticModel dynamics current)
        (next.2.1, next.2.2.1) (next.1, next.2.2.2) := by
  rw [transition_eq_staticJoint_nextStaticModel]
  simpa [staticCoordinates] using
    conditional_internal_external_factorization
      (nextStaticModel dynamics current)
      (next.2.1, next.2.2.1) hblanket next.1 next.2.2.2

/-- The induced conditional next-state law has zero internal-external mutual
information for every current state and next blanket value. -/
theorem transition_row_conditional_mutualInformation_zero
    (dynamics : Dynamics Internal Sensory Active External)
    (current : DynamicState Internal Sensory Active External)
    (blanket : Blanket Sensory Active) :
    mutualInformation
        (conditionalJoint (nextStaticModel dynamics current) blanket) = 0 :=
  conditional_mutualInformation_zero
    (nextStaticModel dynamics current) blanket

/-- A concrete Boolean blanket model: internal copies internal, active copies
sensory, sensory copies external, and external copies active.  It is normalized
and mediates change through the declared blanket graph. -/
def boolDynamics : Dynamics Bool Bool Bool Bool where
  internalFlow := FiniteKernel.deterministic fun current => current.1
  sensoryFlow := FiniteKernel.deterministic fun current => current.1
  activeFlow := FiniteKernel.deterministic fun current => current.2
  externalFlow := FiniteKernel.deterministic fun current => current.2

/-- The Boolean example is nontrivial: this state changes with probability one. -/
theorem boolDynamics_nontrivial :
    let current : DynamicState Bool Bool Bool Bool :=
      (false, (true, (false, true)))
    let next : DynamicState Bool Bool Bool Bool :=
      (false, (true, (true, false)))
    next ≠ current ∧ nextLaw boolDynamics current next = 1 := by
  norm_num [nextLaw, boolDynamics, FiniteLaw.product,
    FiniteKernel.row, FiniteKernel.deterministic]

end FEP.MarkovBlanket
