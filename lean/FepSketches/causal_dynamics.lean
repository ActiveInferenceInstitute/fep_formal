module
public import FepSketches.markov_blanket

@[expose] public section

/-!
# Finite causal blankets and intervention semantics

This module separates three finite claims that are often conflated in prose:
conditional factorization at a blanket, preservation under mixtures that share
one conditional kernel, and intervention behavior in an explicitly ordered
four-node model.  The ordered carrier records only the parent sets used below;
it is not a general DAG or d-separation calculus.
-/

namespace FEP.CausalDynamics

open FEP FEP.FiniteInformation FEP.MarkovBlanket Finset
open scoped BigOperators

variable {Blanket Internal External : Type*}
  [Fintype Blanket] [Fintype Internal] [Fintype External]

/-! ## Conditional blanket families -/

/-- A finite blanket law together with the internal-external conditional law
at each blanket value.  No factorization is built into this carrier. -/
structure ConditionalBlanketModel
    (Blanket Internal External : Type*)
    [Fintype Blanket] [Fintype Internal] [Fintype External] where
  blanketLaw : FiniteLaw Blanket
  conditional : Blanket → FiniteLaw (Internal × External)

/-- Conditional mutual information averaged under the blanket law. -/
noncomputable def conditionalMutualInformation
    (model : ConditionalBlanketModel Blanket Internal External) : ℝ :=
  ∑ blanket, model.blanketLaw blanket *
    mutualInformation (model.conditional blanket)

/-- Pointwise conditional factorization of internal and external states. -/
def Factorizes
    (model : ConditionalBlanketModel Blanket Internal External) : Prop :=
  ∀ blanket,
    model.conditional blanket =
      (model.conditional blanket).fstMarginal.product
        (model.conditional blanket).sndMarginal

/-- Finite conditional mutual information is nonnegative. -/
theorem conditionalMutualInformation_nonneg
    (model : ConditionalBlanketModel Blanket Internal External) :
    0 ≤ conditionalMutualInformation model := by
  exact Finset.sum_nonneg fun blanket _ =>
    mul_nonneg (model.blanketLaw.nonneg blanket)
      (mutualInformation_nonneg (model.conditional blanket))

/-- With full blanket support, zero conditional mutual information is exactly
pointwise conditional factorization.  Full support is needed so a positive-
probability average cannot hide a nonfactorizing null blanket row. -/
theorem conditionalMutualInformation_eq_zero_iff_factorizes
    (model : ConditionalBlanketModel Blanket Internal External)
    (hBlanket : ∀ blanket, 0 < model.blanketLaw blanket) :
    conditionalMutualInformation model = 0 ↔ Factorizes model := by
  constructor
  · intro hzero blanket
    have hterms := (Finset.sum_eq_zero_iff_of_nonneg
      (fun value _ =>
        mul_nonneg (model.blanketLaw.nonneg value)
          (mutualInformation_nonneg (model.conditional value)))).mp hzero
    have hterm := hterms blanket (Finset.mem_univ blanket)
    have hmi : mutualInformation (model.conditional blanket) = 0 :=
      (mul_eq_zero.mp hterm).resolve_left
        (ne_of_gt (hBlanket blanket))
    exact (mutualInformation_eq_zero_iff (model.conditional blanket)).mp hmi
  · intro hfactor
    apply Finset.sum_eq_zero
    intro blanket _
    rw [(mutualInformation_eq_zero_iff (model.conditional blanket)).mpr
      (hfactor blanket), mul_zero]

/-- Forget the built-in factorization of a static Markov-blanket model and
view its conditional rows through the general conditional-family carrier. -/
def ofStaticModel
    {Sensory Active : Type*} [Fintype Sensory] [Fintype Active]
    (model : StaticModel Internal Sensory Active External) :
    ConditionalBlanketModel
      (MarkovBlanket.Blanket Sensory Active) Internal External where
  blanketLaw := model.blanketLaw
  conditional := conditionalJoint model

/-- Static Markov-blanket models inhabit the pointwise factorizing fragment. -/
theorem ofStaticModel_factorizes
    {Sensory Active : Type*} [Fintype Sensory] [Fintype Active]
    (model : StaticModel Internal Sensory Active External) :
    Factorizes (ofStaticModel model) := by
  intro blanket
  change
    (model.internalGiven.row blanket).product
        (model.externalGiven.row blanket) =
      ((model.internalGiven.row blanket).product
          (model.externalGiven.row blanket)).fstMarginal.product
        ((model.internalGiven.row blanket).product
          (model.externalGiven.row blanket)).sndMarginal
  rw [FiniteLaw.product_fstMarginal, FiniteLaw.product_sndMarginal]

/-- The conditional mutual information of every constructed static model is
zero even when its blanket law contains null rows. -/
theorem ofStaticModel_conditionalMutualInformation_zero
    {Sensory Active : Type*} [Fintype Sensory] [Fintype Active]
    (model : StaticModel Internal Sensory Active External) :
    conditionalMutualInformation (ofStaticModel model) = 0 := by
  change
    (∑ blanket, model.blanketLaw blanket *
      mutualInformation (conditionalJoint model blanket)) = 0
  apply Finset.sum_eq_zero
  intro blanket _
  rw [conditional_mutualInformation_zero model blanket, mul_zero]

/-! ## Mixtures with a shared conditional kernel -/

/-- Convex mixture of two normalized finite laws. -/
def mixLaw (weight : ℝ) (hWeightNonneg : 0 ≤ weight)
    (hWeightLeOne : weight ≤ 1) (left right : FiniteLaw Internal) :
    FiniteLaw Internal where
  mass value := weight * left value + (1 - weight) * right value
  nonneg value := add_nonneg
    (mul_nonneg hWeightNonneg (left.nonneg value))
    (mul_nonneg (sub_nonneg.mpr hWeightLeOne) (right.nonneg value))
  sum_one := by
    rw [Finset.sum_add_distrib, ← Finset.mul_sum, ← Finset.mul_sum,
      left.sum_one, right.sum_one]
    ring

/-- Mixing input laws before applying a shared conditional kernel is exactly
the same joint law as mixing the two induced joints. -/
theorem sharedConditional_mixture_preserves_joint
    {Input Output : Type*} [Fintype Input] [Fintype Output]
    (weight : ℝ) (hWeightNonneg : 0 ≤ weight)
    (hWeightLeOne : weight ≤ 1)
    (left right : FiniteLaw Input) (kernel : FiniteKernel Input Output) :
    kernel.joint (mixLaw weight hWeightNonneg hWeightLeOne left right) =
      mixLaw weight hWeightNonneg hWeightLeOne
        (kernel.joint left) (kernel.joint right) := by
  apply FiniteLaw.ext_mass
  funext value
  change
    (weight * left value.1 + (1 - weight) * right value.1) *
          kernel value.1 value.2 =
      weight * (left value.1 * kernel value.1 value.2) +
        (1 - weight) * (right value.1 * kernel value.1 value.2)
  ring

/-- A mixture of product laws remains a product law when the right marginal is
shared.  This is a sufficient condition, not a claim that arbitrary mixtures
of independent laws remain independent. -/
theorem mixture_product_shared_right
    {Left Right : Type*} [Fintype Left] [Fintype Right]
    (weight : ℝ) (hWeightNonneg : 0 ≤ weight)
    (hWeightLeOne : weight ≤ 1)
    (left right : FiniteLaw Left) (shared : FiniteLaw Right) :
    mixLaw weight hWeightNonneg hWeightLeOne
        (left.product shared) (right.product shared) =
      (mixLaw weight hWeightNonneg hWeightLeOne left right).product shared := by
  apply FiniteLaw.ext_mass
  funext value
  change
    weight * (left value.1 * shared value.2) +
          (1 - weight) * (right value.1 * shared value.2) =
      (weight * left value.1 + (1 - weight) * right value.1) * shared value.2
  ring

/-- The symmetric sufficient condition: sharing the left marginal also makes
the mixture of product laws factorize. -/
theorem mixture_product_shared_left
    {Left Right : Type*} [Fintype Left] [Fintype Right]
    (weight : ℝ) (hWeightNonneg : 0 ≤ weight)
    (hWeightLeOne : weight ≤ 1)
    (shared : FiniteLaw Left) (left right : FiniteLaw Right) :
    mixLaw weight hWeightNonneg hWeightLeOne
        (shared.product left) (shared.product right) =
      shared.product (mixLaw weight hWeightNonneg hWeightLeOne left right) := by
  apply FiniteLaw.ext_mass
  funext value
  change
    weight * (shared value.1 * left value.2) +
          (1 - weight) * (shared value.1 * right value.2) =
      shared value.1 *
        (weight * left value.2 + (1 - weight) * right value.2)
  ring

/-- Two factorized rows with the same named right marginal have a factorized
mixture.  The shared-marginal premise is the substantive compatibility
condition; factorization of the two rows alone is insufficient. -/
theorem mixture_factorizes_of_shared_right
    {Left Right : Type*} [Fintype Left] [Fintype Right]
    (weight : ℝ) (hWeightNonneg : 0 ≤ weight)
    (hWeightLeOne : weight ≤ 1)
    (left right : FiniteLaw (Left × Right))
    (leftInternal rightInternal : FiniteLaw Left)
    (shared : FiniteLaw Right)
    (hLeft : left = leftInternal.product shared)
    (hRight : right = rightInternal.product shared) :
    let mixture := mixLaw weight hWeightNonneg hWeightLeOne left right
    mixture = mixture.fstMarginal.product mixture.sndMarginal := by
  subst left
  subst right
  dsimp only
  rw [mixture_product_shared_right, FiniteLaw.product_fstMarginal,
    FiniteLaw.product_sndMarginal]

/-- A half-mixture of the two Boolean point masses is genuinely nondegenerate. -/
noncomputable def boolHalfMixture : FiniteLaw Bool :=
  mixLaw (1 / 2 : ℝ) (by norm_num) (by norm_num)
    (FiniteLaw.pointMass false) (FiniteLaw.pointMass true)

theorem boolHalfMixture_false : boolHalfMixture false = 1 / 2 := by
  norm_num [boolHalfMixture, mixLaw, FiniteLaw.pointMass]

theorem boolHalfMixture_true : boolHalfMixture true = 1 / 2 := by
  norm_num [boolHalfMixture, mixLaw, FiniteLaw.pointMass]

/-! ## Coupled blankets -/

/-- Pair two local conditional kernels while allowing their blanket inputs to
be coupled by an arbitrary joint blanket law. -/
def pairedKernel
    {Blanket₁ Blanket₂ Output₁ Output₂ : Type*}
    [Fintype Blanket₁] [Fintype Blanket₂]
    [Fintype Output₁] [Fintype Output₂]
    (left : FiniteKernel Blanket₁ Output₁)
    (right : FiniteKernel Blanket₂ Output₂) :
    FiniteKernel (Blanket₁ × Blanket₂) (Output₁ × Output₂) where
  mass blanket output := left blanket.1 output.1 * right blanket.2 output.2
  nonneg blanket output :=
    mul_nonneg (left.nonneg blanket.1 output.1)
      (right.nonneg blanket.2 output.2)
  sum_one blanket := by
    rw [Fintype.sum_prod_type]
    simp_rw [← Finset.mul_sum, right.sum_one, mul_one]
    exact left.sum_one blanket.1

/-- Prediction of a product law through a paired component kernel is the
product of the two component predictions. -/
theorem pairedKernel_predictive_product
    {Input₁ Input₂ Output₁ Output₂ : Type*}
    [Fintype Input₁] [Fintype Input₂]
    [Fintype Output₁] [Fintype Output₂]
    (leftLaw : FiniteLaw Input₁) (rightLaw : FiniteLaw Input₂)
    (leftKernel : FiniteKernel Input₁ Output₁)
    (rightKernel : FiniteKernel Input₂ Output₂) :
    (pairedKernel leftKernel rightKernel).predictive
        (leftLaw.product rightLaw) =
      (leftKernel.predictive leftLaw).product
        (rightKernel.predictive rightLaw) := by
  apply FiniteLaw.ext_mass
  funext output
  change
    (∑ input : Input₁ × Input₂,
        (leftLaw input.1 * rightLaw input.2) *
          (leftKernel input.1 output.1 * rightKernel input.2 output.2)) =
      (∑ input : Input₁, leftLaw input * leftKernel input output.1) *
        ∑ input : Input₂, rightLaw input * rightKernel input output.2
  rw [Fintype.sum_prod_type, Finset.sum_mul]
  apply Finset.sum_congr rfl
  intro leftInput _
  rw [Finset.mul_sum]
  apply Finset.sum_congr rfl
  intro rightInput _
  ring

/-- Compose two local blanket subsystems around one possibly correlated blanket
pair.  Dependence may pass through the blanket law, while the internal and
external conditional rows remain product-separated. -/
def coupledBlanketModel
    {Blanket₁ Blanket₂ Internal₁ Internal₂ External₁ External₂ : Type*}
    [Fintype Blanket₁] [Fintype Blanket₂]
    [Fintype Internal₁] [Fintype Internal₂]
    [Fintype External₁] [Fintype External₂]
    (blanketLaw : FiniteLaw (Blanket₁ × Blanket₂))
    (internal₁ : FiniteKernel Blanket₁ Internal₁)
    (internal₂ : FiniteKernel Blanket₂ Internal₂)
    (external₁ : FiniteKernel Blanket₁ External₁)
    (external₂ : FiniteKernel Blanket₂ External₂) :
    StaticModel (Internal₁ × Internal₂) Blanket₁ Blanket₂
      (External₁ × External₂) where
  blanketLaw := blanketLaw
  internalGiven := pairedKernel internal₁ internal₂
  externalGiven := pairedKernel external₁ external₂

/-- Coupled subsystem composition preserves blanket-conditioned independence. -/
theorem coupledBlanket_conditionalMutualInformation_zero
    {Blanket₁ Blanket₂ Internal₁ Internal₂ External₁ External₂ : Type*}
    [Fintype Blanket₁] [Fintype Blanket₂]
    [Fintype Internal₁] [Fintype Internal₂]
    [Fintype External₁] [Fintype External₂]
    (blanketLaw : FiniteLaw (Blanket₁ × Blanket₂))
    (internal₁ : FiniteKernel Blanket₁ Internal₁)
    (internal₂ : FiniteKernel Blanket₂ Internal₂)
    (external₁ : FiniteKernel Blanket₁ External₁)
    (external₂ : FiniteKernel Blanket₂ External₂) (blanket : Blanket₁ × Blanket₂) :
    mutualInformation
        (conditionalJoint
          (coupledBlanketModel blanketLaw internal₁ internal₂ external₁ external₂)
          blanket) = 0 :=
  conditional_mutualInformation_zero
    (coupledBlanketModel blanketLaw internal₁ internal₂ external₁ external₂)
    blanket

/-- A correlated Boolean blanket law used to show that coupled composition is
not restricted to product-distributed blankets. -/
noncomputable def correlatedBoolBlanket : FiniteLaw (Bool × Bool) where
  mass value := if value.1 = value.2 then 1 / 2 else 0
  nonneg value := by split <;> norm_num
  sum_one := by
    rw [Fintype.sum_prod_type, Fintype.sum_bool]
    norm_num

theorem correlatedBoolBlanket_diagonal :
    correlatedBoolBlanket (false, false) = 1 / 2 ∧
      correlatedBoolBlanket (true, true) = 1 / 2 := by
  norm_num [correlatedBoolBlanket]

theorem correlatedBoolBlanket_cross_zero :
    correlatedBoolBlanket (false, true) = 0 ∧
      correlatedBoolBlanket (true, false) = 0 := by
  norm_num [correlatedBoolBlanket]

/-- The diagonal Boolean blanket is genuinely coupled: it is not the product
of its one-coordinate marginals. -/
theorem correlatedBoolBlanket_not_factorized :
    correlatedBoolBlanket ≠
      correlatedBoolBlanket.fstMarginal.product
        correlatedBoolBlanket.sndMarginal := by
  intro hFactor
  have hAtom := congrArg (fun law : FiniteLaw (Bool × Bool) => law (false, false))
    hFactor
  norm_num [correlatedBoolBlanket, FiniteLaw.fstMarginal,
    FiniteLaw.sndMarginal, FiniteLaw.product, Fintype.sum_bool] at hAtom

/-- Its blanket-coordinate mutual information is therefore strictly positive. -/
theorem correlatedBoolBlanket_mutualInformation_pos :
    0 < mutualInformation correlatedBoolBlanket := by
  have hNonzero : mutualInformation correlatedBoolBlanket ≠ 0 := by
    intro hzero
    exact correlatedBoolBlanket_not_factorized
      ((mutualInformation_eq_zero_iff correlatedBoolBlanket).mp hzero)
  exact lt_of_le_of_ne (mutualInformation_nonneg correlatedBoolBlanket)
    (Ne.symm hNonzero)

/-- The diagonal Boolean blanket is an equal mixture of two laws that are each
individually products of point masses. -/
theorem boolFactorizedMixture_eq_correlatedBlanket :
    mixLaw (1 / 2 : ℝ) (by norm_num) (by norm_num)
        ((FiniteLaw.pointMass false).product (FiniteLaw.pointMass false))
        ((FiniteLaw.pointMass true).product (FiniteLaw.pointMass true)) =
      correlatedBoolBlanket := by
  apply FiniteLaw.ext_mass
  funext value
  rcases value with ⟨internal, external⟩
  cases internal <;> cases external <;>
    norm_num [mixLaw, FiniteLaw.product, FiniteLaw.pointMass,
      correlatedBoolBlanket]

/-- Arbitrary positive mixtures do not preserve factorization: mixing the two
deterministic product regimes produces the correlated diagonal law. -/
theorem boolFactorizedMixture_not_factorized :
    let mixture :=
      mixLaw (1 / 2 : ℝ) (by norm_num) (by norm_num)
        ((FiniteLaw.pointMass false).product (FiniteLaw.pointMass false))
        ((FiniteLaw.pointMass true).product (FiniteLaw.pointMass true))
    mixture ≠ mixture.fstMarginal.product mixture.sndMarginal := by
  dsimp only
  rw [boolFactorizedMixture_eq_correlatedBlanket]
  exact correlatedBoolBlanket_not_factorized

/-! ## Interventions and an ordered four-node carrier -/

/-- A hard intervention ignores its context and returns the chosen value with
probability one. -/
def interventionKernel
    {Context Value : Type*} [Fintype Context] [Fintype Value]
    [DecidableEq Value] (chosen : Value) : FiniteKernel Context Value :=
  FiniteKernel.deterministic (fun _ => chosen)

theorem interventionKernel_sum_one
    {Context Value : Type*} [Fintype Context] [Fintype Value]
    [DecidableEq Value] (chosen : Value) (context : Context) :
    ∑ value, interventionKernel (Context := Context) chosen context value = 1 :=
  (interventionKernel (Context := Context) chosen).sum_one context

theorem interventionKernel_chosen
    {Context Value : Type*} [Fintype Context] [Fintype Value]
    [DecidableEq Value] (chosen : Value) (context : Context) :
    interventionKernel (Context := Context) chosen context chosen = 1 := by
  simp [interventionKernel, FiniteKernel.deterministic]

theorem interventionKernel_other
    {Context Value : Type*} [Fintype Context] [Fintype Value]
    [DecidableEq Value] (chosen other : Value) (hOther : other ≠ chosen)
    (context : Context) :
    interventionKernel (Context := Context) chosen context other = 0 := by
  simp [interventionKernel, FiniteKernel.deterministic, hOther]

/-- State order is root, named non-descendant, mediator, outcome. -/
abbrev OrderedState
    (Root NonDescendant Mediator Outcome : Type*) :=
  ((Root × NonDescendant) × Mediator) × Outcome

/-- An explicitly ordered four-node causal factorization.

The parent sets are `parents(Mediator)={Root}` and
`parents(Outcome)={NonDescendant,Mediator}`.  The two root nodes have independent
exogenous laws. -/
structure OrderedFourNodeModel
    (Root NonDescendant Mediator Outcome : Type*)
    [Fintype Root] [Fintype NonDescendant]
    [Fintype Mediator] [Fintype Outcome] where
  rootLaw : FiniteLaw Root
  nonDescendantLaw : FiniteLaw NonDescendant
  mediatorGivenRoot : FiniteKernel Root Mediator
  outcomeGivenParents : FiniteKernel (NonDescendant × Mediator) Outcome

variable {Root NonDescendant Mediator Outcome : Type*}
  [Fintype Root] [Fintype NonDescendant]
  [Fintype Mediator] [Fintype Outcome]

/-- Lift the mediator kernel to the ordered pair of exogenous roots without
creating a dependency on the named non-descendant. -/
def mediatorLift
    (model : OrderedFourNodeModel Root NonDescendant Mediator Outcome) :
    FiniteKernel (Root × NonDescendant) Mediator where
  mass roots mediator := model.mediatorGivenRoot roots.1 mediator
  nonneg roots mediator := model.mediatorGivenRoot.nonneg roots.1 mediator
  sum_one roots := model.mediatorGivenRoot.sum_one roots.1

/-- Lift the outcome kernel to its exact parent projection. -/
def outcomeLift
    (model : OrderedFourNodeModel Root NonDescendant Mediator Outcome) :
    FiniteKernel ((Root × NonDescendant) × Mediator) Outcome where
  mass history outcome :=
    model.outcomeGivenParents (history.1.2, history.2) outcome
  nonneg history outcome :=
    model.outcomeGivenParents.nonneg (history.1.2, history.2) outcome
  sum_one history :=
    model.outcomeGivenParents.sum_one (history.1.2, history.2)

/-- Normalized observational law of the ordered four-node model. -/
def orderedJoint
    (model : OrderedFourNodeModel Root NonDescendant Mediator Outcome) :
    FiniteLaw (OrderedState Root NonDescendant Mediator Outcome) :=
  (outcomeLift model).joint
    ((mediatorLift model).joint
      (model.rootLaw.product model.nonDescendantLaw))

/-- The observational law exposes exactly the maintained ordered parent
factorization. -/
theorem orderedJoint_factorization
    (model : OrderedFourNodeModel Root NonDescendant Mediator Outcome)
    (root : Root) (nonDescendant : NonDescendant)
    (mediator : Mediator) (outcome : Outcome) :
    orderedJoint model (((root, nonDescendant), mediator), outcome) =
      ((model.rootLaw root * model.nonDescendantLaw nonDescendant) *
          model.mediatorGivenRoot root mediator) *
        model.outcomeGivenParents (nonDescendant, mediator) outcome := rfl

theorem orderedJoint_sum_one
    (model : OrderedFourNodeModel Root NonDescendant Mediator Outcome) :
    ∑ state, orderedJoint model state = 1 :=
  (orderedJoint model).sum_one

/-- Replace the root law by a hard intervention while preserving the remaining
ordered kernels. -/
def interventionalJoint [DecidableEq Root]
    (model : OrderedFourNodeModel Root NonDescendant Mediator Outcome)
    (root : Root) :
    FiniteLaw (OrderedState Root NonDescendant Mediator Outcome) :=
  (outcomeLift model).joint
    ((mediatorLift model).joint
      ((FiniteLaw.pointMass root).product model.nonDescendantLaw))

/-- Extract the named non-descendant marginal from an ordered state law. -/
def nonDescendantMarginal
    (law : FiniteLaw (OrderedState Root NonDescendant Mediator Outcome)) :
    FiniteLaw NonDescendant :=
  law.fstMarginal.fstMarginal.sndMarginal

/-- A root intervention cannot change the named non-descendant law because
that node has no intervened root among its parents. -/
theorem nonDescendant_intervention_invariant [DecidableEq Root]
    (model : OrderedFourNodeModel Root NonDescendant Mediator Outcome)
    (root : Root) :
    nonDescendantMarginal (interventionalJoint model root) =
      model.nonDescendantLaw := by
  have houtcome :
      (interventionalJoint model root).fstMarginal =
        (mediatorLift model).joint
          ((FiniteLaw.pointMass root).product model.nonDescendantLaw) := by
    apply FiniteLaw.ext_mass
    funext history
    exact FiniteKernel.joint_fstMarginal_mass _ _ history
  have hmediator :
      ((mediatorLift model).joint
        ((FiniteLaw.pointMass root).product model.nonDescendantLaw)).fstMarginal =
          (FiniteLaw.pointMass root).product model.nonDescendantLaw := by
    apply FiniteLaw.ext_mass
    funext roots
    exact FiniteKernel.joint_fstMarginal_mass _ _ roots
  rw [nonDescendantMarginal, houtcome, hmediator,
    FiniteLaw.product_sndMarginal]

/-- Extract the mediator marginal, used to witness descendant change. -/
def mediatorMarginal
    (law : FiniteLaw (OrderedState Root NonDescendant Mediator Outcome)) :
    FiniteLaw Mediator :=
  law.fstMarginal.sndMarginal

/-- Under a hard root intervention, the mediator marginal is exactly the named
structural mediator kernel row.  No observational-identification premise is
used or inferred. -/
theorem interventionalMediatorMarginal_mass [DecidableEq Root]
    (model : OrderedFourNodeModel Root NonDescendant Mediator Outcome)
    (root : Root) (mediator : Mediator) :
    mediatorMarginal (interventionalJoint model root) mediator =
      model.mediatorGivenRoot root mediator := by
  have houtcome :
      (interventionalJoint model root).fstMarginal =
        (mediatorLift model).joint
          ((FiniteLaw.pointMass root).product model.nonDescendantLaw) := by
    apply FiniteLaw.ext_mass
    funext history
    exact FiniteKernel.joint_fstMarginal_mass _ _ history
  rw [mediatorMarginal, houtcome]
  change
    (∑ roots : Root × NonDescendant,
      (((FiniteLaw.pointMass root).product model.nonDescendantLaw) roots) *
        model.mediatorGivenRoot roots.1 mediator) =
      model.mediatorGivenRoot root mediator
  rw [Fintype.sum_prod_type]
  simp [FiniteLaw.product, FiniteLaw.pointMass]
  rw [← Finset.sum_mul, model.nonDescendantLaw.sum_one, one_mul]

/-- Interventional mediator behavior is identified when the maintained
structural mediator kernels are equal.  Observational equality alone is not a
premise and is not sufficient, as the separate Boolean countermodel shows. -/
theorem interventionalMediator_eq_of_mediatorKernel_eq [DecidableEq Root]
    (left right : OrderedFourNodeModel Root NonDescendant Mediator Outcome)
    (hMediator : left.mediatorGivenRoot = right.mediatorGivenRoot)
    (root : Root) :
    mediatorMarginal (interventionalJoint left root) =
      mediatorMarginal (interventionalJoint right root) := by
  apply FiniteLaw.ext_mass
  funext mediator
  rw [interventionalMediatorMarginal_mass,
    interventionalMediatorMarginal_mass, hMediator]

/-- Boolean four-node model in which the mediator copies the intervened root
and the outcome is the XOR of the non-descendant and mediator. -/
noncomputable def boolOrderedModel :
    OrderedFourNodeModel Bool Bool Bool Bool where
  rootLaw := FiniteLaw.uniform
  nonDescendantLaw := FiniteLaw.uniform
  mediatorGivenRoot := FiniteKernel.deterministic id
  outcomeGivenParents :=
    FiniteKernel.deterministic fun parents => Bool.xor parents.1 parents.2

/-- In the Boolean model `do(root=false)` assigns zero mass to a true
mediator. -/
theorem boolIntervention_false_mediator_true_zero :
    mediatorMarginal (interventionalJoint boolOrderedModel false) true = 0 := by
  norm_num [mediatorMarginal, interventionalJoint, outcomeLift, mediatorLift,
    boolOrderedModel, FiniteKernel.joint, FiniteLaw.fstMarginal,
    FiniteLaw.sndMarginal, FiniteLaw.product, FiniteLaw.pointMass,
    FiniteLaw.uniform, FiniteKernel.deterministic, Fintype.sum_prod_type,
    Fintype.sum_bool]

/-- In the same model `do(root=true)` assigns unit mass to a true mediator. -/
theorem boolIntervention_true_mediator_true_one :
    mediatorMarginal (interventionalJoint boolOrderedModel true) true = 1 := by
  norm_num [mediatorMarginal, interventionalJoint, outcomeLift, mediatorLift,
    boolOrderedModel, FiniteKernel.joint, FiniteLaw.fstMarginal,
    FiniteLaw.sndMarginal, FiniteLaw.product, FiniteLaw.pointMass,
    FiniteLaw.uniform, FiniteKernel.deterministic, Fintype.sum_prod_type,
    Fintype.sum_bool]

theorem boolIntervention_preserves_named_nonDescendant :
    nonDescendantMarginal (interventionalJoint boolOrderedModel false) =
      nonDescendantMarginal (interventionalJoint boolOrderedModel true) := by
  rw [nonDescendant_intervention_invariant,
    nonDescendant_intervention_invariant]

/-! ## Ordered local Markov property -/

/-- Evidence for conditioning a root on one mediator value. -/
def mediatorEvidence
    (model : OrderedFourNodeModel Root NonDescendant Mediator Outcome)
    (mediator : Mediator) : ℝ :=
  model.mediatorGivenRoot.predictive model.rootLaw mediator

/-- The conditional predecessor-outcome law at fixed local parents.  The root
posterior accounts for the mediator evidence; the outcome row depends only on
its maintained parents, non-descendant and mediator. -/
noncomputable def localMarkovConditional
    (model : OrderedFourNodeModel Root NonDescendant Mediator Outcome)
    (nonDescendant : NonDescendant) (mediator : Mediator)
    (hEvidence : 0 < mediatorEvidence model mediator) :
    FiniteLaw (Root × Outcome) :=
  (model.mediatorGivenRoot.posterior model.rootLaw mediator hEvidence).product
    (model.outcomeGivenParents.row (nonDescendant, mediator))

/-- The maintained ordered factorization yields the exact local product law:
the outcome is independent of the non-parent predecessor root once its two
parents are fixed. -/
theorem localMarkov_factorization_from_ordered
    (model : OrderedFourNodeModel Root NonDescendant Mediator Outcome)
    (nonDescendant : NonDescendant) (mediator : Mediator)
    (hEvidence : 0 < mediatorEvidence model mediator) :
    localMarkovConditional model nonDescendant mediator hEvidence =
      (model.mediatorGivenRoot.posterior model.rootLaw mediator hEvidence).product
        (model.outcomeGivenParents.row (nonDescendant, mediator)) := rfl

/-- Consequently the finite mutual information between the non-parent
predecessor and the outcome vanishes at every positive-evidence parent row. -/
theorem localMarkov_mutualInformation_zero
    (model : OrderedFourNodeModel Root NonDescendant Mediator Outcome)
    (nonDescendant : NonDescendant) (mediator : Mediator)
    (hEvidence : 0 < mediatorEvidence model mediator) :
    mutualInformation
        (localMarkovConditional model nonDescendant mediator hEvidence) = 0 :=
  mutualInformation_product_eq_zero
    (model.mediatorGivenRoot.posterior model.rootLaw mediator hEvidence)
    (model.outcomeGivenParents.row (nonDescendant, mediator))

/-- The local product law is the actual ordered joint conditional: multiplying
one root-outcome atom by its non-descendant and mediator evidence reconstructs
the corresponding four-node joint atom. -/
theorem localMarkovConditional_reconstruction
    (model : OrderedFourNodeModel Root NonDescendant Mediator Outcome)
    (nonDescendant : NonDescendant) (mediator : Mediator)
    (hEvidence : 0 < mediatorEvidence model mediator)
    (root : Root) (outcome : Outcome) :
    localMarkovConditional model nonDescendant mediator hEvidence (root, outcome) *
        (model.nonDescendantLaw nonDescendant * mediatorEvidence model mediator) =
      orderedJoint model (((root, nonDescendant), mediator), outcome) := by
  have hBayes := FiniteKernel.posterior_mul_predictive
    model.rootLaw model.mediatorGivenRoot mediator hEvidence root
  change
    model.mediatorGivenRoot.posterior model.rootLaw mediator hEvidence root *
        mediatorEvidence model mediator =
      model.rootLaw root * model.mediatorGivenRoot root mediator at hBayes
  rw [orderedJoint_factorization]
  change
    (model.mediatorGivenRoot.posterior model.rootLaw mediator hEvidence root *
        model.outcomeGivenParents (nonDescendant, mediator) outcome) *
          (model.nonDescendantLaw nonDescendant * mediatorEvidence model mediator) = _
  calc
    _ =
        (model.mediatorGivenRoot.posterior model.rootLaw mediator hEvidence root *
            mediatorEvidence model mediator) *
          (model.nonDescendantLaw nonDescendant *
            model.outcomeGivenParents (nonDescendant, mediator) outcome) := by ring
    _ =
        (model.rootLaw root * model.mediatorGivenRoot root mediator) *
          (model.nonDescendantLaw nonDescendant *
            model.outcomeGivenParents (nonDescendant, mediator) outcome) := by
          rw [hBayes]
    _ = _ := by ring

/-- The zero-evidence boundary is explicit: no normalized posterior-based
local conditional may be constructed through this API. -/
theorem localMarkov_zeroEvidence_boundary
    (model : OrderedFourNodeModel Root NonDescendant Mediator Outcome)
    (mediator : Mediator) (hZero : mediatorEvidence model mediator = 0) :
    ¬0 < mediatorEvidence model mediator := by
  rw [hZero]
  exact lt_irrefl 0

/-- The Boolean local-Markov witness conditions on a genuinely positive
mediator-evidence atom. -/
theorem boolMediatorEvidence_true :
    mediatorEvidence boolOrderedModel true = 1 / 2 := by
  norm_num [mediatorEvidence, boolOrderedModel, FiniteKernel.predictive_mass,
    FiniteLaw.uniform, FiniteKernel.deterministic, Fintype.sum_bool]

end FEP.CausalDynamics
