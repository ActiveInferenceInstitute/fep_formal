module
public import FepSketches.finite_probability
public import Mathlib.CategoryTheory.Functor.Basic
public import Mathlib.CategoryTheory.Types.Basic

@[expose] public section

/-!
# Finite-kernel category feasibility spike

The bundled finite objects, category instance and three category-law witnesses
are adapted from GitHub contributor `jhashemi`'s PR #44, exact source head
`df4bc773e0c0ddb4e4f80920903e711ed287beb4`:
https://github.com/ActiveInferenceInstitute/fep_formal/pull/44

This prospective Lean 4.35 port keeps the existing normalized real-valued
`FEP.FiniteKernel` carrier. The predictive-law functor below uses Mathlib's
standard `Functor` and the existing predictive identity/composition proofs;
it replaces the proposal's unrestricted, duplicate `FiniteKernelFunctor`
wrapper. Boolean consumers make its action on actual finite laws explicit.

This file is slice-local feasibility source. It is neither a manifested package
resource nor evidence of package integration, current native acceptance,
scientific promotion or CUR-13 closure. The 71-module manifest and historical
custody records are unchanged. An accepted port still needs an explicitly
reviewed successor source epoch and the required native, axiom, projection and
independent formal/domain acceptance.
-/

namespace FEPComposed.FiniteKernelCategory

open CategoryTheory FEP

/-- A finite object with the instances required by the existing kernel carrier. -/
structure FinKernCat : Type 1 where
  α : Type
  [instFintype : Fintype α]
  [instDecEq : DecidableEq α]

attribute [instance] FinKernCat.instFintype FinKernCat.instDecEq

/-- The existing kernel algebra in categorical composition order. -/
instance finiteKernelCategory : Category FinKernCat where
  Hom X Y := FiniteKernel X.α Y.α
  id X := FiniteKernel.identity (α := X.α)
  comp f g := FiniteKernel.comp g f
  id_comp f := FiniteKernel.comp_identity_right f
  comp_id f := FiniteKernel.comp_identity_left f
  assoc f g h := FiniteKernel.comp_assoc h g f

/-- A categorical identity before a kernel leaves it unchanged. -/
theorem finKernCat_id_comp (X Y : FinKernCat) (f : X ⟶ Y) :
    𝟙 X ≫ f = f :=
  FiniteKernel.comp_identity_right f

/-- A categorical identity after a kernel leaves it unchanged. -/
theorem finKernCat_comp_id (X Y : FinKernCat) (f : X ⟶ Y) :
    f ≫ 𝟙 Y = f :=
  FiniteKernel.comp_identity_left f

/-- The existing associativity theorem has exactly the categorical orientation. -/
theorem finKernCat_assoc (W X Y Z : FinKernCat)
    (f : W ⟶ X) (g : X ⟶ Y) (h : Y ⟶ Z) :
    (f ≫ g) ≫ h = f ≫ (g ≫ h) :=
  FiniteKernel.comp_assoc h g f

/-- Predictive propagation is a standard Mathlib functor into the category of types. -/
def predictiveFunctor : FinKernCat ⥤ Type where
  obj X := FiniteLaw X.α
  map kernel := TypeCat.ofHom fun prior => FiniteKernel.predictive prior kernel
  map_id X := by
    apply TypeCat.homEquiv.injective
    funext prior
    exact FiniteKernel.predictive_identity prior
  map_comp earlier later := by
    apply TypeCat.homEquiv.injective
    funext prior
    exact FiniteKernel.predictive_comp prior later earlier

/-- The Boolean state space is a concrete inhabited object. -/
def boolObject : FinKernCat where
  α := Bool
  instFintype := inferInstance
  instDecEq := inferInstance

/-- A nonidentity deterministic kernel on the Boolean object. -/
def boolFlip : boolObject ⟶ boolObject :=
  FiniteKernel.deterministic Bool.not

/-- The functor's identity law acts on an actual normalized point mass. -/
theorem bool_predictive_identity :
    predictiveFunctor.map (𝟙 boolObject) (FiniteLaw.pointMass true) =
      FiniteLaw.pointMass true :=
  FiniteKernel.predictive_identity (FiniteLaw.pointMass true)

/-- Flipping a point mass at `true` produces a point mass at `false`. -/
theorem bool_flip_true :
    predictiveFunctor.map boolFlip (FiniteLaw.pointMass true) =
      FiniteLaw.pointMass false := by
  apply FiniteLaw.ext_mass
  funext value
  change FiniteKernel.predictive (FiniteLaw.pointMass true)
      (FiniteKernel.deterministic Bool.not) value = FiniteLaw.pointMass false value
  cases value <;>
    simp [FiniteKernel.predictive_mass, FiniteKernel.deterministic,
      FiniteLaw.pointMass]

/-- Flipping a point mass at `false` produces a point mass at `true`. -/
theorem bool_flip_false :
    predictiveFunctor.map boolFlip (FiniteLaw.pointMass false) =
      FiniteLaw.pointMass true := by
  apply FiniteLaw.ext_mass
  funext value
  change FiniteKernel.predictive (FiniteLaw.pointMass false)
      (FiniteKernel.deterministic Bool.not) value = FiniteLaw.pointMass true value
  cases value <;>
    simp [FiniteKernel.predictive_mass, FiniteKernel.deterministic,
      FiniteLaw.pointMass]

/-- Categorical composition agrees with two predictive applications on this law. -/
theorem bool_predictive_composition :
    predictiveFunctor.map (boolFlip ≫ boolFlip) (FiniteLaw.pointMass true) =
      predictiveFunctor.map boolFlip
        (predictiveFunctor.map boolFlip (FiniteLaw.pointMass true)) :=
  FiniteKernel.predictive_comp (FiniteLaw.pointMass true) boolFlip boolFlip

/-- Two actual Boolean flips recover the starting normalized law. -/
theorem bool_predictive_flip_twice :
    predictiveFunctor.map (boolFlip ≫ boolFlip) (FiniteLaw.pointMass true) =
      FiniteLaw.pointMass true := by
  change FiniteKernel.predictive (FiniteLaw.pointMass true)
      (FiniteKernel.comp boolFlip boolFlip) = FiniteLaw.pointMass true
  exact (FiniteKernel.predictive_comp (FiniteLaw.pointMass true)
      boolFlip boolFlip).trans
    ((congrArg (fun prior : FiniteLaw Bool =>
      FiniteKernel.predictive prior boolFlip) bool_flip_true).trans bool_flip_false)

#print axioms finiteKernelCategory
#print axioms finKernCat_id_comp
#print axioms finKernCat_comp_id
#print axioms finKernCat_assoc
#print axioms predictiveFunctor
#print axioms bool_predictive_identity
#print axioms bool_flip_true
#print axioms bool_flip_false
#print axioms bool_predictive_composition
#print axioms bool_predictive_flip_twice

end FEPComposed.FiniteKernelCategory
