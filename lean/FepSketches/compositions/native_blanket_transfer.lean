module
public import FepSketches.fep_all
public import FepSketches.native_blanket
public import FepSketches.gaussian_precision_conditioning
public import Mathlib.LinearAlgebra.Matrix.PosDef
public import Mathlib.LinearAlgebra.Matrix.SchurComplement

@[expose] public section

/-!
# Finite-to-native blanket-transfer compositions

These bridges keep the finite and Mathlib-native carriers visible in honest
conjunctions.  In particular, the native conditional-independence rows use
`CondIndepFun` directly; finite conditional mutual information is retained
only as earlier topic evidence and is never substituted for the native
predicate.
-/

namespace FEPComposed

open FEP FEP.CausalDynamics FEP.MarkovBlanket FEP.NativeBlanket
open MeasureTheory ProbabilityTheory
open scoped BigOperators ENNReal MeasureTheory ProbabilityTheory

/-- The embedded finite-law normalization is paired with fep-017's native
posterior-fibre normalization when the embedded law is used as the prior. -/
theorem fep135_embeddedLaw_extends_fep017
    {State Observation : Type*}
    [Fintype State] [Fintype Observation] [Nonempty State]
    [MeasurableSpace State] [MeasurableSpace Observation]
    [DiscreteMeasurableSpace State] [DiscreteMeasurableSpace Observation]
    (law : FiniteLaw State) (kernel : FiniteKernel State Observation)
    (observation : Observation) :
    embeddedLaw law Set.univ = 1 ∧
      fep_fep017.FEP017.fep017_posterior
          (embeddedKernel kernel) (embeddedLaw law) observation Set.univ = 1 := by
  exact
    ⟨fep_fep135.FEP135.fep135_embeddedLaw_normalized law,
      fep_fep017.FEP017.fep017_posterior_mass_one
        (embeddedKernel kernel) (embeddedLaw law) observation⟩

/-- The finite expectation transfer is instantiated at fep-015's measurable
variational integrand, keeping both integrability and measurability evidence. -/
theorem fep136_embeddedExpectation_extends_fep015
    {State : Type*} [Fintype State]
    [MeasurableSpace State] [DiscreteMeasurableSpace State]
    (law : FiniteLaw State)
    (energy logApproximation logGenerative : State → ℝ)
    (energyMeasurable : Measurable energy)
    (approximationMeasurable : Measurable logApproximation)
    (generativeMeasurable : Measurable logGenerative) :
    (∫ state,
        fep_fep015.FEP015.fep015_variationalIntegrand
          energy logApproximation logGenerative state ∂embeddedLaw law) =
          ∑ state, law state *
            fep_fep015.FEP015.fep015_variationalIntegrand
              energy logApproximation logGenerative state ∧
      Measurable
        (fep_fep015.FEP015.fep015_variationalIntegrand
          energy logApproximation logGenerative) := by
  exact
    ⟨fep_fep136.FEP136.fep136_embeddedLaw_expectation law
        (fep_fep015.FEP015.fep015_variationalIntegrand
          energy logApproximation logGenerative),
      fep_fep015.FEP015.fep015_variationalIntegrand_measurable
        energyMeasurable approximationMeasurable generativeMeasurable⟩

/-- Embedded finite prediction is native kernel composition, and fep-019's
native prior-predictive theorem certifies that this law remains normalized. -/
theorem fep137_embeddedPredictive_extends_fep019
    {Input Output : Type*} [Fintype Input] [Fintype Output]
    [MeasurableSpace Input] [MeasurableSpace Output]
    [DiscreteMeasurableSpace Input] [DiscreteMeasurableSpace Output]
    (prior : FiniteLaw Input) (kernel : FiniteKernel Input Output) :
    embeddedLaw (kernel.predictive prior) =
        embeddedKernel kernel ∘ₘ embeddedLaw prior ∧
      fep_fep019.FEP019.fep019_priorPredictive
          (embeddedKernel kernel) (embeddedLaw prior) Set.univ = 1 := by
  exact
    ⟨fep_fep137.FEP137.fep137_embeddedPredictive_eq_comp prior kernel,
      fep_fep019.FEP019.fep019_priorPredictive_mass_one
        (embeddedKernel kernel) (embeddedLaw prior)⟩

/-- The native singleton-rectangle factorization is paired with fep-079's
finite conditional-mutual-information certificate for the same static model. -/
theorem fep138_rectangleFactorization_extends_fep079
    {Internal Sensory Active External : Type*}
    [Fintype Internal] [Fintype Sensory] [Fintype Active] [Fintype External]
    [MeasurableSpace Internal] [MeasurableSpace Sensory]
    [MeasurableSpace Active] [MeasurableSpace External]
    [DiscreteMeasurableSpace Internal] [DiscreteMeasurableSpace Sensory]
    [DiscreteMeasurableSpace Active] [DiscreteMeasurableSpace External]
    (model : StaticModel Internal Sensory Active External)
    (blanket : Blanket Sensory Active) (internal : Internal)
    (external : External) :
    embeddedLaw (staticJoint model)
        (blanketCoordinate ⁻¹' {blanket} ∩
          internalCoordinate ⁻¹' {internal} ∩
          externalCoordinate ⁻¹' {external}) =
        ENNReal.ofReal (model.blanketLaw blanket) *
          ENNReal.ofReal (model.internalGiven blanket internal) *
            ENNReal.ofReal (model.externalGiven blanket external) ∧
      conditionalMutualInformation (ofStaticModel model) = 0 := by
  exact
    ⟨fep_fep138.FEP138.fep138_staticJoint_rectangle_factorization
        model blanket internal external,
      fep_fep079.FEP079.fep079_staticBlanket_conditionalMutualInformation_zero
        model⟩

/-- The fep-079 finite factorization is transferred by fep-139 to genuine
Mathlib `CondIndepFun`; alongside it, fep-009 supplies the corresponding
symmetry law for conditional independence of the coordinate sigma-algebras.
The conjunction does not identify finite conditional mutual information with
the native predicate. -/
theorem fep139_nativeCondIndep_connects_fep009_fep079
    {Internal Sensory Active External : Type*}
    [Fintype Internal] [Fintype Sensory] [Fintype Active] [Fintype External]
    [Nonempty Internal] [Nonempty External]
    [MeasurableSpace Internal] [MeasurableSpace Sensory]
    [MeasurableSpace Active] [MeasurableSpace External]
    [DiscreteMeasurableSpace Internal] [DiscreteMeasurableSpace Sensory]
    [DiscreteMeasurableSpace Active] [DiscreteMeasurableSpace External]
    (model : StaticModel Internal Sensory Active External) :
    CondIndepFun
        (MeasurableSpace.comap blanketCoordinate inferInstance)
        blanketCoordinate_measurable.comap_le
        internalCoordinate externalCoordinate
        (embeddedLaw (staticJoint model)) ∧
      (CondIndep
          (MeasurableSpace.comap blanketCoordinate inferInstance)
          (MeasurableSpace.comap internalCoordinate inferInstance)
          (MeasurableSpace.comap externalCoordinate inferInstance)
          blanketCoordinate_measurable.comap_le
          (embeddedLaw (staticJoint model)) →
        CondIndep
          (MeasurableSpace.comap blanketCoordinate inferInstance)
          (MeasurableSpace.comap externalCoordinate inferInstance)
          (MeasurableSpace.comap internalCoordinate inferInstance)
          blanketCoordinate_measurable.comap_le
          (embeddedLaw (staticJoint model))) := by
  refine
    ⟨fep_fep139.FEP139.fep139_staticJoint_condIndepFun model, ?_⟩
  intro sigmaIndependence
  exact
    fep_fep009.FEP009.fep009_condIndep_symm
      (Ω := StaticState Internal Sensory Active External)
      (MeasurableSpace.comap blanketCoordinate inferInstance)
      (MeasurableSpace.comap internalCoordinate inferInstance)
      (MeasurableSpace.comap externalCoordinate inferInstance)
      blanketCoordinate_measurable.comap_le
      (embeddedLaw (staticJoint model)) sigmaIndependence

/-- Native measurable coarsening is paired with fep-009's symmetry law at
the sigma-algebras generated by those same coarsened coordinates. -/
theorem fep140_measurableCoarsening_extends_fep009
    {Internal Sensory Active External InternalImage ExternalImage : Type*}
    [Fintype Internal] [Fintype Sensory] [Fintype Active] [Fintype External]
    [Nonempty Internal] [Nonempty External]
    [MeasurableSpace Internal] [MeasurableSpace Sensory]
    [MeasurableSpace Active] [MeasurableSpace External]
    [MeasurableSpace InternalImage] [MeasurableSpace ExternalImage]
    [DiscreteMeasurableSpace Internal] [DiscreteMeasurableSpace Sensory]
    [DiscreteMeasurableSpace Active] [DiscreteMeasurableSpace External]
    (model : StaticModel Internal Sensory Active External)
    (internalImage : Internal → InternalImage)
    (externalImage : External → ExternalImage)
    (internalMeasurable : Measurable internalImage)
    (externalMeasurable : Measurable externalImage) :
    CondIndepFun
        (MeasurableSpace.comap blanketCoordinate inferInstance)
        blanketCoordinate_measurable.comap_le
        (internalImage ∘ internalCoordinate)
        (externalImage ∘ externalCoordinate)
        (embeddedLaw (staticJoint model)) ∧
      (CondIndep
          (MeasurableSpace.comap blanketCoordinate inferInstance)
          (MeasurableSpace.comap (internalImage ∘ internalCoordinate) inferInstance)
          (MeasurableSpace.comap (externalImage ∘ externalCoordinate) inferInstance)
          blanketCoordinate_measurable.comap_le
          (embeddedLaw (staticJoint model)) →
        CondIndep
          (MeasurableSpace.comap blanketCoordinate inferInstance)
          (MeasurableSpace.comap (externalImage ∘ externalCoordinate) inferInstance)
          (MeasurableSpace.comap (internalImage ∘ internalCoordinate) inferInstance)
          blanketCoordinate_measurable.comap_le
          (embeddedLaw (staticJoint model))) := by
  refine
    ⟨fep_fep140.FEP140.fep140_condIndepFun_measurableImages
        model internalImage externalImage internalMeasurable externalMeasurable,
      ?_⟩
  intro sigmaIndependence
  exact
    fep_fep009.FEP009.fep009_condIndep_symm
      (Ω := StaticState Internal Sensory Active External)
      (MeasurableSpace.comap blanketCoordinate inferInstance)
      (MeasurableSpace.comap
        (internalImage ∘ internalCoordinate) inferInstance)
      (MeasurableSpace.comap
        (externalImage ∘ externalCoordinate) inferInstance)
      blanketCoordinate_measurable.comap_le
      (embeddedLaw (staticJoint model)) sigmaIndependence

/-- Rowwise native blanket closure is paired with fep-080's exact finite
mixture law for two blanket priors sharing that row's conditional pair kernel. -/
theorem fep141_blanketTransition_extends_fep080
    {Internal Sensory Active External : Type*}
    [Fintype Internal] [Fintype Sensory] [Fintype Active] [Fintype External]
    [Nonempty Internal] [Nonempty External]
    [MeasurableSpace Internal] [MeasurableSpace Sensory]
    [MeasurableSpace Active] [MeasurableSpace External]
    [DiscreteMeasurableSpace Internal] [DiscreteMeasurableSpace Sensory]
    [DiscreteMeasurableSpace Active] [DiscreteMeasurableSpace External]
    (dynamics : Dynamics Internal Sensory Active External)
    (current : DynamicState Internal Sensory Active External)
    (weight : ℝ) (weightNonnegative : 0 ≤ weight) (weightAtMostOne : weight ≤ 1)
    (left right : FiniteLaw (Blanket Sensory Active)) :
    CondIndepFun
        (MeasurableSpace.comap blanketCoordinate inferInstance)
        blanketCoordinate_measurable.comap_le
        internalCoordinate externalCoordinate
        (embeddedLaw (staticJoint (nextStaticModel dynamics current))) ∧
      (conditionalPairKernel (nextStaticModel dynamics current)).joint
          (mixLaw weight weightNonnegative weightAtMostOne left right) =
        mixLaw weight weightNonnegative weightAtMostOne
          ((conditionalPairKernel (nextStaticModel dynamics current)).joint left)
          ((conditionalPairKernel (nextStaticModel dynamics current)).joint right) := by
  exact
    ⟨fep_fep141.FEP141.fep141_prediction_preserves_nativeBlanket
        dynamics current,
      fep_fep080.FEP080.fep080_sharedConditional_mixture_preservation
        weight weightNonnegative weightAtMostOne left right
        (conditionalPairKernel (nextStaticModel dynamics current))⟩

end FEPComposed

namespace FEPComposed

namespace GaussianBlanket

open FEP.GaussianPrecisionConditioning
open FEP.Fin4GaussianSemigroup
open FEP.Fin4GaussianSemigroup.Axis
open MeasureTheory ProbabilityTheory
open scoped ENNReal MeasureTheory NNReal ProbabilityTheory

noncomputable section

/-! ## Dimension-generic Gaussian blankets (FORM-S14)

For a positive-definite precision partitioned as `((external ⊕ internal) ⊕
blanket)`, the conditional covariance of the interior given the blanket is the
inverse of the interior precision block (Schur complement), so its
external–internal cross block vanishes exactly when the precision has no
external–internal entries. The accepted `Fin 4` carrier is recovered as an
instance and a non-sparse precision is a countermodel. This is matrix algebra
on precisions; measure-level conditioning of a general Gaussian is a recorded
Mathlib gap (`docs/lean4.md`, Gaussian conditioning against Mathlib).
-/

section GenericBlanket

open Matrix

variable {E I B : Type*} [Fintype E] [Fintype I] [Fintype B]
  [DecidableEq E] [DecidableEq I] [DecidableEq B]

/-- Conditional precision of the interior block `(external, internal)` given
the blanket for a precision partitioned as `((E ⊕ I) ⊕ B)`: the interior
principal submatrix of the joint precision (a Gaussian conditional keeps the
joint precision restricted to the unobserved coordinates). -/
def blanketConditionalPrecision (K : Matrix ((E ⊕ I) ⊕ B) ((E ⊕ I) ⊕ B) ℝ) :
    Matrix (E ⊕ I) (E ⊕ I) ℝ :=
  K.toBlocks₁₁

/-- Conditional covariance of the interior block given the blanket, taken as the
Schur complement `Σ_xx - Σ_xb Σ_bb⁻¹ Σ_bx` of the covariance `Σ = K⁻¹`. -/
noncomputable def blanketConditionalCovariance
    (K : Matrix ((E ⊕ I) ⊕ B) ((E ⊕ I) ⊕ B) ℝ) : Matrix (E ⊕ I) (E ⊕ I) ℝ :=
  K⁻¹.toBlocks₁₁ - K⁻¹.toBlocks₁₂ * (K⁻¹.toBlocks₂₂)⁻¹ * K⁻¹.toBlocks₂₁

omit [Fintype E] [Fintype I] [Fintype B] [DecidableEq E] [DecidableEq I] [DecidableEq B] in
theorem blanketConditionalPrecision_posDef
    {K : Matrix ((E ⊕ I) ⊕ B) ((E ⊕ I) ⊕ B) ℝ} (hK : K.PosDef) :
    (blanketConditionalPrecision K).PosDef :=
  hK.submatrix Sum.inl_injective

/-- Schur-complement identity: the conditional covariance is the inverse of
the conditional precision, for every positive-definite partitioned precision. -/
theorem blanketConditionalCovariance_eq_inv
    {K : Matrix ((E ⊕ I) ⊕ B) ((E ⊕ I) ⊕ B) ℝ} (hK : K.PosDef) :
    blanketConditionalCovariance K = (blanketConditionalPrecision K)⁻¹ := by
  have hA : IsUnit (blanketConditionalPrecision K) :=
    (blanketConditionalPrecision_posDef hK).isUnit
  have hS22 : IsUnit (K⁻¹.toBlocks₂₂) :=
    (hK.inv.submatrix (e := Sum.inr) Sum.inr_injective).isUnit
  have hKS : K * K⁻¹ = 1 := Matrix.mul_nonsing_inv _ ((Matrix.isUnit_iff_isUnit_det _).mp hK.isUnit)
  have hFB : K = fromBlocks K.toBlocks₁₁ K.toBlocks₁₂ K.toBlocks₂₁ K.toBlocks₂₂ :=
    (fromBlocks_toBlocks K).symm
  have hFS : K⁻¹ = fromBlocks K⁻¹.toBlocks₁₁ K⁻¹.toBlocks₁₂ K⁻¹.toBlocks₂₁ K⁻¹.toBlocks₂₂ :=
    (fromBlocks_toBlocks _).symm
  set A := K.toBlocks₁₁ with hAdef
  set Bm := K.toBlocks₁₂
  set C := K.toBlocks₂₁
  set D := K.toBlocks₂₂
  set S11 := K⁻¹.toBlocks₁₁
  set S12 := K⁻¹.toBlocks₁₂
  set S21 := K⁻¹.toBlocks₂₁
  set S22 := K⁻¹.toBlocks₂₂
  have hmul : fromBlocks A Bm C D * fromBlocks S11 S12 S21 S22 = 1 := by
    rw [← hFB, ← hFS]; exact hKS
  rw [fromBlocks_multiply, ← fromBlocks_one, fromBlocks_inj] at hmul
  obtain ⟨h11, h12, -, -⟩ := hmul
  have hAinv : A * A⁻¹ = 1 := Matrix.mul_nonsing_inv _ ((Matrix.isUnit_iff_isUnit_det _).mp hA)
  have hAinv' : A⁻¹ * A = 1 := Matrix.nonsing_inv_mul _ ((Matrix.isUnit_iff_isUnit_det _).mp hA)
  have hS22inv : S22 * S22⁻¹ = 1 :=
    Matrix.mul_nonsing_inv _ ((Matrix.isUnit_iff_isUnit_det _).mp hS22)
  have e12 : S12 = -(A⁻¹ * Bm * S22) := by
    have : A⁻¹ * (A * S12 + Bm * S22) = 0 := by rw [h12]; simp
    rw [Matrix.mul_add, ← Matrix.mul_assoc, hAinv', Matrix.one_mul, ← Matrix.mul_assoc] at this
    exact eq_neg_of_add_eq_zero_left this
  have e11 : S11 = A⁻¹ - A⁻¹ * Bm * S21 := by
    have : A⁻¹ * (A * S11 + Bm * S21) = A⁻¹ := by rw [h11, Matrix.mul_one]
    rw [Matrix.mul_add, ← Matrix.mul_assoc, hAinv', Matrix.one_mul, ← Matrix.mul_assoc] at this
    exact eq_sub_of_add_eq this
  unfold blanketConditionalCovariance blanketConditionalPrecision
  change S11 - S12 * S22⁻¹ * S21 = A⁻¹
  have e22 : S12 * S22⁻¹ = -(A⁻¹ * Bm) := by
    rw [e12, Matrix.neg_mul, Matrix.mul_assoc _ S22, hS22inv, Matrix.mul_one]
  rw [e22, e11, Matrix.neg_mul]
  abel

/-- For a positive-definite matrix partitioned as `E ⊕ I`, the cross block
vanishes exactly when the cross block of its inverse vanishes. -/
theorem blanketPrecisionCrossZeroIff
    {P : Matrix (E ⊕ I) (E ⊕ I) ℝ} (hP : P.PosDef) :
    P.toBlocks₁₂ = 0 ↔ P⁻¹.toBlocks₁₂ = 0 := by
  have key : ∀ {Q : Matrix (E ⊕ I) (E ⊕ I) ℝ}, Q.PosDef → Q.toBlocks₁₂ = 0 →
      Q⁻¹.toBlocks₁₂ = 0 := by
    intro Q hQ h12
    have h21 : Q.toBlocks₂₁ = 0 := by
      ext i e
      have := hQ.1.apply (Sum.inl e) (Sum.inr i)
      have h : Q (Sum.inl e) (Sum.inr i) = 0 := congrFun (congrFun h12 e) i
      simpa [Matrix.toBlocks₂₁, h] using this
    have hA : IsUnit Q.toBlocks₁₁ := (hQ.submatrix Sum.inl_injective).isUnit
    have hD : IsUnit Q.toBlocks₂₂ := (hQ.submatrix Sum.inr_injective).isUnit
    have hFB : Q = fromBlocks Q.toBlocks₁₁ 0 0 Q.toBlocks₂₂ := by
      conv_lhs => rw [← fromBlocks_toBlocks Q, h12, h21]
    rw [hFB, inv_fromBlocks_zero₂₁_of_isUnit_iff _ _ _ (iff_of_true hA hD)]
    simp
  refine ⟨key hP, fun h => ?_⟩
  have := key hP.inv h
  rwa [Matrix.nonsing_inv_nonsing_inv _ ((Matrix.isUnit_iff_isUnit_det _).mp hP.isUnit)] at this

/-- Dimension-generic Gaussian blanket criterion at the precision/covariance
level: the external--internal cross block of the conditional covariance given
the blanket vanishes iff the joint precision has `K_{ei} = 0`.  The forward
direction is the sparsity theorem; the converse is the non-sparse
countermodel principle. -/
theorem blanketConditionalCovarianceCrossZeroIff
    {K : Matrix ((E ⊕ I) ⊕ B) ((E ⊕ I) ⊕ B) ℝ} (hK : K.PosDef) :
    (blanketConditionalCovariance K).toBlocks₁₂ = 0 ↔
      ∀ e i, K (Sum.inl (Sum.inl e)) (Sum.inl (Sum.inr i)) = 0 := by
  rw [blanketConditionalCovariance_eq_inv hK,
    ← blanketPrecisionCrossZeroIff (blanketConditionalPrecision_posDef hK)]
  constructor
  · intro h e i
    exact congrFun (congrFun h e) i
  · intro h
    ext e i
    exact h e i

/-- Sparse joint precision implies a block-diagonal conditional covariance
cross block, in any dimension. -/
theorem blanketSparsePrecisionConditionalCovarianceCrossZero
    {K : Matrix ((E ⊕ I) ⊕ B) ((E ⊕ I) ⊕ B) ℝ} (hK : K.PosDef)
    (hSparse : ∀ e i, K (Sum.inl (Sum.inl e)) (Sum.inl (Sum.inr i)) = 0) :
    (blanketConditionalCovariance K).toBlocks₁₂ = 0 :=
  (blanketConditionalCovarianceCrossZeroIff hK).mpr hSparse

/-- Non-sparse joint precision forces a nonzero conditional covariance cross
entry, in any dimension. -/
theorem blanketNonSparsePrecisionConditionalCovarianceCrossNeZero
    {K : Matrix ((E ⊕ I) ⊕ B) ((E ⊕ I) ⊕ B) ℝ} (hK : K.PosDef) {e : E} {i : I}
    (hNonSparse : K (Sum.inl (Sum.inl e)) (Sum.inl (Sum.inr i)) ≠ 0) :
    (blanketConditionalCovariance K).toBlocks₁₂ ≠ 0 := fun h =>
  hNonSparse (((blanketConditionalCovarianceCrossZeroIff hK).mp h) e i)

end GenericBlanket

/-- Fin4 coordinates in `((external ⊕ internal) ⊕ (sensory ⊕ active))` order. -/
def fin4BlanketIndex : ((Unit ⊕ Unit) ⊕ (Unit ⊕ Unit)) → Axis
  | Sum.inl (Sum.inl _) => external
  | Sum.inl (Sum.inr _) => internal
  | Sum.inr (Sum.inl _) => sensory
  | Sum.inr (Sum.inr _) => active

theorem fin4BlanketIndex_injective : Function.Injective fin4BlanketIndex := by
  rintro ((⟨⟩ | ⟨⟩) | (⟨⟩ | ⟨⟩)) ((⟨⟩ | ⟨⟩) | (⟨⟩ | ⟨⟩)) h <;>
    first | rfl | (exfalso; simp [fin4BlanketIndex] at h)

/-- The Fin4 precision in the generic `(e, i, b)` partition. -/
def fin4BlanketPrecision : Matrix ((Unit ⊕ Unit) ⊕ (Unit ⊕ Unit))
    ((Unit ⊕ Unit) ⊕ (Unit ⊕ Unit)) ℝ :=
  K.submatrix fin4BlanketIndex fin4BlanketIndex

theorem fin4BlanketPrecision_posDef : fin4BlanketPrecision.PosDef :=
  K_posDef.submatrix fin4BlanketIndex_injective

theorem fin4BlanketPrecision_sparse :
    ∀ e i : Unit, fin4BlanketPrecision (Sum.inl (Sum.inl e)) (Sum.inl (Sum.inr i)) = 0 :=
  fun _ _ => K_external_internal

/-- The Fin4 blanket is an instance of the dimension-generic criterion: the
algebraic conditional-covariance cross block vanishes, and the measure-level
conditional independence theorem holds at every stationary center. -/
theorem fin4_blanket_generic_instance (center : StandardizedState) :
    (blanketConditionalCovariance fin4BlanketPrecision).toBlocks₁₂ = 0 ∧
      ((fun state : StandardizedState => state external) ⟂ᵢ[
        blanketCoordinates, measurable_blanketCoordinates; stationaryLaw center]
        (fun state => state internal)) :=
  ⟨blanketSparsePrecisionConditionalCovarianceCrossZero
      fin4BlanketPrecision_posDef fin4BlanketPrecision_sparse,
    external_condIndep_internal_given_blanket center⟩

/-- Index map placing the diagnostic bivariate precision in the generic
partition with an empty blanket. -/
def perturbedBlanketIndex : ((Unit ⊕ Unit) ⊕ Empty) → Fin 2
  | Sum.inl (Sum.inl _) => 0
  | Sum.inl (Sum.inr _) => 1
  | Sum.inr e => e.elim

theorem perturbedBlanketIndex_injective : Function.Injective perturbedBlanketIndex := by
  rintro ((⟨⟩ | ⟨⟩) | e) ((⟨⟩ | ⟨⟩) | e') h <;>
    first | rfl | exact e.elim | exact e'.elim |
      (exfalso; simp [perturbedBlanketIndex] at h)

/-- Non-sparse countermodel precision in the generic partition. -/
def nonSparseBlanketPrecision : Matrix ((Unit ⊕ Unit) ⊕ Empty)
    ((Unit ⊕ Unit) ⊕ Empty) ℝ :=
  perturbedEndpointPrecision.submatrix perturbedBlanketIndex perturbedBlanketIndex

theorem nonSparseBlanketPrecision_posDef : nonSparseBlanketPrecision.PosDef :=
  perturbedEndpointPrecision_posDef.submatrix perturbedBlanketIndex_injective

/-- Countermodel: a positive-definite precision with `K_{ei} ≠ 0` has a
nonzero conditional covariance cross block. -/
theorem nonSparseBlanket_conditionalCovariance_cross_ne_zero :
    nonSparseBlanketPrecision (Sum.inl (Sum.inl ())) (Sum.inl (Sum.inr ())) ≠ 0 ∧
      (blanketConditionalCovariance nonSparseBlanketPrecision).toBlocks₁₂ ≠ 0 :=
  have hEntry : nonSparseBlanketPrecision (Sum.inl (Sum.inl ())) (Sum.inl (Sum.inr ())) ≠ 0 := by
    change perturbedEndpointPrecision 0 1 ≠ 0
    rw [perturbedEndpointPrecision_external_internal]
    exact one_ne_zero
  ⟨hEntry, blanketNonSparsePrecisionConditionalCovarianceCrossNeZero
    nonSparseBlanketPrecision_posDef hEntry⟩

end

end GaussianBlanket

end FEPComposed
