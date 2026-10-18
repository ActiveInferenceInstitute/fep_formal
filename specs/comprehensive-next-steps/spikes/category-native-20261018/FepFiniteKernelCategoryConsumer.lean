module
public import FepSketches.compositions.finite_kernel_category

@[expose] public section

open CategoryTheory FEP FEPComposed.FiniteKernelCategory

example (X Y : FinKernCat) (kernel : FiniteKernel X.α Y.α) : X ⟶ Y := kernel

example (X Y : FinKernCat) (kernel : X ⟶ Y) : 𝟙 X ≫ kernel = kernel :=
  finKernCat_id_comp X Y kernel

example (X Y : FinKernCat) (kernel : X ⟶ Y) : kernel ≫ 𝟙 Y = kernel :=
  finKernCat_comp_id X Y kernel

example (W X Y Z : FinKernCat) (f : W ⟶ X) (g : X ⟶ Y) (h : Y ⟶ Z) :
    (f ≫ g) ≫ h = f ≫ (g ≫ h) :=
  finKernCat_assoc W X Y Z f g h

example : predictiveFunctor.obj boolObject = FiniteLaw Bool := rfl

example (X Y : FinKernCat) (kernel : X ⟶ Y) (prior : FiniteLaw X.α) :
    predictiveFunctor.map kernel prior = FiniteKernel.predictive prior kernel := rfl

example : predictiveFunctor.map (𝟙 boolObject) (FiniteLaw.pointMass true) =
    FiniteLaw.pointMass true := bool_predictive_identity

example : predictiveFunctor.map boolFlip (FiniteLaw.pointMass true) =
    FiniteLaw.pointMass false := bool_flip_true

example : predictiveFunctor.map boolFlip (FiniteLaw.pointMass false) =
    FiniteLaw.pointMass true := bool_flip_false

example : predictiveFunctor.map (boolFlip ≫ boolFlip) (FiniteLaw.pointMass true) =
    predictiveFunctor.map boolFlip
      (predictiveFunctor.map boolFlip (FiniteLaw.pointMass true)) :=
  bool_predictive_composition

example : predictiveFunctor.map (boolFlip ≫ boolFlip) (FiniteLaw.pointMass true) =
    FiniteLaw.pointMass true := bool_predictive_flip_twice

#print axioms FEPComposed.FiniteKernelCategory.finiteKernelCategory
#print axioms FEPComposed.FiniteKernelCategory.finKernCat_id_comp
#print axioms FEPComposed.FiniteKernelCategory.finKernCat_comp_id
#print axioms FEPComposed.FiniteKernelCategory.finKernCat_assoc
#print axioms FEPComposed.FiniteKernelCategory.predictiveFunctor
#print axioms FEPComposed.FiniteKernelCategory.bool_predictive_identity
#print axioms FEPComposed.FiniteKernelCategory.bool_flip_true
#print axioms FEPComposed.FiniteKernelCategory.bool_flip_false
#print axioms FEPComposed.FiniteKernelCategory.bool_predictive_composition
#print axioms FEPComposed.FiniteKernelCategory.bool_predictive_flip_twice
