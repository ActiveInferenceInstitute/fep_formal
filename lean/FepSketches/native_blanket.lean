import FepSketches.markov_blanket
import Mathlib.MeasureTheory.Integral.Bochner.SumMeasure
import Mathlib.Probability.Independence.Conditional
import Mathlib.Probability.Kernel.Composition.Comp

/-!
# Finite laws as native measures and native Markov blankets

This module embeds the repository's normalized finite laws as weighted sums of
Dirac measures.  It then transports the authored static blanket
factorization to Mathlib's measure-theoretic `CondIndepFun` predicate.  The
conditional-independence result is not inferred from finite mutual
information: it is obtained by identifying the two finite conditional
kernels with Mathlib conditional distributions and applying Mathlib's native
joint-measure characterization.
-/

namespace FEP.NativeBlanket

open FEP FEP.MarkovBlanket Filter Finset MeasureTheory ProbabilityTheory
open scoped BigOperators ENNReal MeasureTheory ProbabilityTheory

noncomputable section

section FiniteEmbedding

variable {α β : Type*} [Fintype α] [Fintype β]
  [MeasurableSpace α] [MeasurableSpace β]
  [DiscreteMeasurableSpace α] [DiscreteMeasurableSpace β]

/-- A normalized finite law represented as a native Mathlib measure by
weighted Dirac masses. -/
noncomputable def embeddedLaw (law : FiniteLaw α) : Measure α :=
  Measure.sum fun state => ENNReal.ofReal (law state) • Measure.dirac state

/-- The native measure assigns each singleton exactly the authored finite
mass, embedded in `ℝ≥0∞`. -/
@[simp]
theorem embeddedLaw_apply_singleton (law : FiniteLaw α) (state : α) :
    embeddedLaw law {state} = ENNReal.ofReal (law state) := by
  simpa [embeddedLaw] using
    (Measure.sum_smul_dirac_singleton
      (f := fun state : α => ENNReal.ofReal (law state)) (a := state))

/-- A normalized finite law embeds as a probability measure. -/
@[simp]
theorem embeddedLaw_apply_univ (law : FiniteLaw α) :
    embeddedLaw law Set.univ = 1 := by
  rw [embeddedLaw, Measure.sum_apply_of_countable, tsum_fintype]
  simp only [Measure.smul_apply, Measure.dirac_apply]
  simp only [Set.indicator_of_mem (Set.mem_univ _), Pi.one_apply, smul_eq_mul, mul_one]
  rw [← ENNReal.ofReal_sum_of_nonneg (fun state _ => law.nonneg state), law.sum_one]
  simp

noncomputable instance embeddedLaw_isProbabilityMeasure (law : FiniteLaw α) :
    IsProbabilityMeasure (embeddedLaw law) where
  measure_univ := embeddedLaw_apply_univ law

/-- The real-valued singleton mass is definitionally faithful to the finite
carrier. -/
@[simp]
theorem embeddedLaw_real_singleton (law : FiniteLaw α) (state : α) :
    (embeddedLaw law).real {state} = law state := by
  rw [Measure.real_def, embeddedLaw_apply_singleton]
  exact ENNReal.toReal_ofReal (law.nonneg state)

/-- No two finite laws collapse to the same native measure. -/
theorem embeddedLaw_injective :
    Function.Injective (embeddedLaw : FiniteLaw α → Measure α) := by
  intro left right equalMeasures
  apply FiniteLaw.ext_mass
  funext state
  have singletonEquality :=
    congrArg (fun measure : Measure α => measure.real {state}) equalMeasures
  simpa using singletonEquality

/-- Native integration agrees exactly with the finite weighted sum. -/
theorem embeddedLaw_integral_eq_sum (law : FiniteLaw α) (observable : α → ℝ) :
    ∫ state, observable state ∂embeddedLaw law =
      ∑ state, law state * observable state := by
  have integrableObservable : Integrable observable (embeddedLaw law) :=
    Integrable.of_finite
  rw [integral_countable integrableObservable, tsum_fintype]
  simp [embeddedLaw_real_singleton, smul_eq_mul, mul_comm]

/-- Pushforward commutes with the finite-law embedding on discrete carriers. -/
theorem embeddedLaw_map [DecidableEq β]
    (law : FiniteLaw α) (mapState : α → β) :
    (embeddedLaw law).map mapState = embeddedLaw (law.map mapState) := by
  classical
  apply Measure.ext_of_singleton
  intro target
  rw [Measure.map_apply Measurable.of_discrete MeasurableSet.of_discrete,
    embeddedLaw, Measure.sum_apply_of_countable, tsum_fintype,
    embeddedLaw_apply_singleton, FiniteLaw.map_mass]
  simp only [Measure.smul_apply, Measure.dirac_apply, Set.indicator_apply,
    Pi.one_apply, smul_eq_mul, mul_ite, mul_one, mul_zero]
  rw [ENNReal.ofReal_sum_of_nonneg]
  · apply Finset.sum_congr rfl
    intro state _
    by_cases hstate : mapState state = target <;> simp [hstate]
  · intro state _
    split_ifs
    · exact law.nonneg state
    · exact le_rfl

/-- A finite kernel represented by its embedded probability-measure rows. -/
noncomputable def embeddedKernel (kernel : FiniteKernel α β) : Kernel α β :=
  Kernel.ofFunOfCountable fun state => embeddedLaw (kernel.row state)

omit [DiscreteMeasurableSpace β] in
@[simp]
theorem embeddedKernel_apply (kernel : FiniteKernel α β) (state : α) :
    embeddedKernel kernel state = embeddedLaw (kernel.row state) := rfl

@[simp]
theorem embeddedKernel_apply_singleton
    (kernel : FiniteKernel α β) (state : α) (target : β) :
    embeddedKernel kernel state {target} = ENNReal.ofReal (kernel state target) := by
  rw [embeddedKernel_apply, embeddedLaw_apply_singleton]
  rfl

noncomputable instance embeddedKernel_isMarkovKernel
    (kernel : FiniteKernel α β) : IsMarkovKernel (embeddedKernel kernel) where
  isProbabilityMeasure state := embeddedLaw_isProbabilityMeasure (kernel.row state)

/-- The authored finite identity kernel embeds as Mathlib's native identity
kernel, not merely as a distributionally equivalent transition. -/
@[simp]
theorem embeddedKernel_identity [DecidableEq α] :
    embeddedKernel (FiniteKernel.identity : FiniteKernel α α) = Kernel.id := by
  classical
  apply Kernel.ext
  intro state
  apply Measure.ext_of_singleton
  intro target
  rw [embeddedKernel_apply_singleton,
    Kernel.id_apply, Measure.dirac_apply' _ (MeasurableSet.singleton target)]
  by_cases htarget : target = state
  · subst target
    simp [FiniteKernel.identity, FiniteKernel.deterministic]
  · simp [FiniteKernel.identity, FiniteKernel.deterministic,
      htarget, Ne.symm htarget]

/-- Embedding a finite prior-kernel joint is exactly Mathlib's native
composition-product measure. -/
theorem embeddedLaw_joint_eq_compProd
    (prior : FiniteLaw α) (kernel : FiniteKernel α β) :
    embeddedLaw (kernel.joint prior) =
      embeddedLaw prior ⊗ₘ embeddedKernel kernel := by
  classical
  apply Measure.ext_of_singleton
  rintro ⟨state, target⟩
  rw [embeddedLaw_apply_singleton]
  change ENNReal.ofReal (prior state * kernel state target) = _
  rw [show ({(state, target)} : Set (α × β)) = {state} ×ˢ {target} by ext; simp,
    Measure.compProd_apply_prod MeasurableSet.of_discrete MeasurableSet.of_discrete,
    lintegral_singleton]
  simp [embeddedLaw_apply_singleton, FiniteKernel.row,
    ENNReal.ofReal_mul (prior.nonneg state), mul_comm]

/-- Native kernel composition gives the embedded finite predictive law. -/
theorem embeddedPredictive_eq_comp
    (prior : FiniteLaw α) (kernel : FiniteKernel α β) :
    embeddedLaw (kernel.predictive prior) =
      embeddedKernel kernel ∘ₘ embeddedLaw prior := by
  classical
  apply Measure.ext_of_singleton
  intro target
  rw [embeddedLaw_apply_singleton,
    Measure.bind_apply MeasurableSet.of_discrete (Kernel.aemeasurable _),
    lintegral_fintype, FiniteKernel.predictive_mass]
  rw [ENNReal.ofReal_sum_of_nonneg]
  · apply Finset.sum_congr rfl
    intro state _
    simp [embeddedLaw_apply_singleton, FiniteKernel.row,
      ENNReal.ofReal_mul (prior.nonneg state), mul_comm]
  · intro state _
    exact mul_nonneg (prior.nonneg state) (kernel.nonneg state target)

/-- Embedding preserves chronological finite-kernel composition exactly:
`earlier` acts first and `later` acts second on both sides. -/
@[simp]
theorem embeddedKernel_comp {γ : Type*} [Fintype γ]
    [MeasurableSpace γ] [DiscreteMeasurableSpace γ]
    (later : FiniteKernel β γ) (earlier : FiniteKernel α β) :
    embeddedKernel (FiniteKernel.comp later earlier) =
      embeddedKernel later ∘ₖ embeddedKernel earlier := by
  apply Kernel.ext
  intro state
  rw [Kernel.comp_apply, embeddedKernel_apply, embeddedKernel_apply]
  have hrow :
      (FiniteKernel.comp later earlier).row state =
        later.predictive (earlier.row state) := by
    apply FiniteLaw.ext_mass
    rfl
  rw [hrow]
  exact embeddedPredictive_eq_comp (earlier.row state) later

end FiniteEmbedding

section StaticBlanket

variable {Internal Sensory Active External : Type*}
  [Fintype Internal] [Fintype Sensory] [Fintype Active] [Fintype External]
  [MeasurableSpace Internal] [MeasurableSpace Sensory]
  [MeasurableSpace Active] [MeasurableSpace External]
  [DiscreteMeasurableSpace Internal] [DiscreteMeasurableSpace Sensory]
  [DiscreteMeasurableSpace Active] [DiscreteMeasurableSpace External]

local instance : DecidableEq Internal := Classical.decEq Internal
local instance : DecidableEq Sensory := Classical.decEq Sensory
local instance : DecidableEq Active := Classical.decEq Active
local instance : DecidableEq External := Classical.decEq External

/-- Blanket coordinate on the existing finite static-state carrier. -/
def blanketCoordinate
    (state : StaticState Internal Sensory Active External) :
    Blanket Sensory Active := state.1.1

/-- Internal coordinate on the existing finite static-state carrier. -/
def internalCoordinate
    (state : StaticState Internal Sensory Active External) : Internal :=
  state.1.2

/-- External coordinate on the existing finite static-state carrier. -/
def externalCoordinate
    (state : StaticState Internal Sensory Active External) : External :=
  state.2

/-- The association map used by Mathlib's `(blanket, internal, external)`
conditional-distribution characterization. -/
def blanketTripleCoordinate
    (state : StaticState Internal Sensory Active External) :
    Blanket Sensory Active × (Internal × External) :=
  (blanketCoordinate state, internalCoordinate state, externalCoordinate state)

theorem blanketCoordinate_measurable :
    Measurable
      (blanketCoordinate :
        StaticState Internal Sensory Active External → Blanket Sensory Active) :=
  Measurable.of_discrete

theorem internalCoordinate_measurable :
    Measurable
      (internalCoordinate :
        StaticState Internal Sensory Active External → Internal) :=
  Measurable.of_discrete

theorem externalCoordinate_measurable :
    Measurable
      (externalCoordinate :
        StaticState Internal Sensory Active External → External) :=
  Measurable.of_discrete

theorem blanketTripleCoordinate_measurable :
    Measurable
      (blanketTripleCoordinate :
        StaticState Internal Sensory Active External →
          Blanket Sensory Active × (Internal × External)) :=
  Measurable.of_discrete

/-- The finite product row containing the internal and external conditionals
at a fixed blanket value. -/
def conditionalPairKernel
    (model : StaticModel Internal Sensory Active External) :
    FiniteKernel (Blanket Sensory Active) (Internal × External) where
  mass blanket pair :=
    model.internalGiven blanket pair.1 * model.externalGiven blanket pair.2
  nonneg blanket pair :=
    mul_nonneg (model.internalGiven.nonneg blanket pair.1)
      (model.externalGiven.nonneg blanket pair.2)
  sum_one blanket := by
    rw [Fintype.sum_prod_type]
    simp_rw [← Finset.mul_sum, model.externalGiven.sum_one, mul_one]
    exact model.internalGiven.sum_one blanket

/-- The embedded finite product row is Mathlib's native product kernel. -/
theorem embeddedConditionalPairKernel_eq_prod
    (model : StaticModel Internal Sensory Active External) :
    embeddedKernel (conditionalPairKernel model) =
      embeddedKernel model.internalGiven ×ₖ embeddedKernel model.externalGiven := by
  classical
  apply Kernel.ext
  intro blanket
  apply Measure.ext_of_singleton
  rintro ⟨internal, external⟩
  rw [embeddedKernel_apply_singleton]
  change ENNReal.ofReal
      (model.internalGiven blanket internal *
        model.externalGiven blanket external) = _
  rw [show ({(internal, external)} : Set (Internal × External)) =
      {internal} ×ˢ {external} by ext; simp,
    Kernel.prod_apply_prod]
  simp [FiniteKernel.row,
    ENNReal.ofReal_mul (model.internalGiven.nonneg blanket internal)]

omit [MeasurableSpace Internal] [MeasurableSpace Sensory]
    [MeasurableSpace Active] [MeasurableSpace External]
    [DiscreteMeasurableSpace Internal] [DiscreteMeasurableSpace Sensory]
    [DiscreteMeasurableSpace Active] [DiscreteMeasurableSpace External] in
private theorem staticJoint_map_triple_finite
    (model : StaticModel Internal Sensory Active External) :
    (staticJoint model).map blanketTripleCoordinate =
      (conditionalPairKernel model).joint model.blanketLaw := by
  classical
  apply FiniteLaw.ext_mass
  funext state
  rcases state with ⟨blanket, internal, external⟩
  have coordinate_eq
      (source : StaticState Internal Sensory Active External) :
      blanketTripleCoordinate source = (blanket, internal, external) ↔
        source = ((blanket, internal), external) := by
    rcases source with ⟨⟨sourceBlanket, sourceInternal⟩, sourceExternal⟩
    simp [blanketTripleCoordinate, blanketCoordinate, internalCoordinate,
      externalCoordinate, and_assoc]
  rw [FiniteLaw.map_mass]
  simp_rw [coordinate_eq]
  simp only [Finset.sum_ite_eq', Finset.mem_univ, ite_eq_left]
  change staticJoint model ((blanket, internal), external) =
    model.blanketLaw blanket *
      (model.internalGiven blanket internal *
        model.externalGiven blanket external)
  rw [staticJoint_factorization]
  ring

omit [MeasurableSpace Internal] [MeasurableSpace Sensory]
    [MeasurableSpace Active] [MeasurableSpace External]
    [DiscreteMeasurableSpace Internal] [DiscreteMeasurableSpace Sensory]
    [DiscreteMeasurableSpace Active] [DiscreteMeasurableSpace External] in
private theorem staticJoint_map_blanketExternal_finite
    (model : StaticModel Internal Sensory Active External) :
    (staticJoint model).map
        (fun state => (blanketCoordinate state, externalCoordinate state)) =
      model.externalGiven.joint model.blanketLaw := by
  classical
  apply FiniteLaw.ext_mass
  funext state
  rcases state with ⟨blanket, external⟩
  rw [FiniteLaw.map_mass, Fintype.sum_prod_type]
  change (∑ blanketInternal : Blanket Sensory Active × Internal,
      ∑ sourceExternal : External,
        if (blanketInternal.1, sourceExternal) = (blanket, external) then
          staticJoint model (blanketInternal, sourceExternal)
        else 0) = _
  calc
    (∑ blanketInternal : Blanket Sensory Active × Internal,
        ∑ sourceExternal : External,
          if (blanketInternal.1, sourceExternal) = (blanket, external) then
            staticJoint model (blanketInternal, sourceExternal)
          else 0) =
        ∑ blanketInternal : Blanket Sensory Active × Internal,
          if blanketInternal.1 = blanket then
            staticJoint model (blanketInternal, external)
          else 0 := by
            apply Finset.sum_congr rfl
            intro blanketInternal _
            by_cases hblanket : blanketInternal.1 = blanket <;>
              simp [hblanket]
    _ = ∑ sourceBlanket : Blanket Sensory Active,
          if sourceBlanket = blanket then
            ∑ internal : Internal,
              staticJoint model ((sourceBlanket, internal), external)
          else 0 := by
            rw [Fintype.sum_prod_type]
            apply Finset.sum_congr rfl
            intro sourceBlanket _
            by_cases hblanket : sourceBlanket = blanket <;> simp [hblanket]
    _ = ∑ internal : Internal,
          staticJoint model ((blanket, internal), external) := by simp
    _ = model.blanketLaw blanket * model.externalGiven blanket external := by
          simp_rw [staticJoint_factorization]
          rw [← Finset.sum_mul, ← Finset.mul_sum,
            model.internalGiven.sum_one, mul_one]

private theorem staticJoint_map_blanketInternal_embedded
    (model : StaticModel Internal Sensory Active External) :
    (embeddedLaw (staticJoint model)).map
        (fun state => (blanketCoordinate state, internalCoordinate state)) =
      embeddedLaw model.blanketLaw ⊗ₘ embeddedKernel model.internalGiven := by
  change (embeddedLaw (staticJoint model)).fst = _
  rw [staticJoint, embeddedLaw_joint_eq_compProd, Measure.fst_compProd,
    embeddedLaw_joint_eq_compProd]

/-- The native blanket marginal is exactly the embedded authored blanket
law. -/
theorem staticJoint_map_blanket
    (model : StaticModel Internal Sensory Active External) :
    (embeddedLaw (staticJoint model)).map blanketCoordinate =
      embeddedLaw model.blanketLaw := by
  calc
    (embeddedLaw (staticJoint model)).map blanketCoordinate =
        ((embeddedLaw (staticJoint model)).map
          (fun state => (blanketCoordinate state, internalCoordinate state))).fst := by
            rw [Measure.fst, Measure.map_map Measurable.of_discrete Measurable.of_discrete]
            rfl
    _ = (embeddedLaw model.blanketLaw ⊗ₘ
          embeddedKernel model.internalGiven).fst := by
            rw [staticJoint_map_blanketInternal_embedded]
    _ = embeddedLaw model.blanketLaw := Measure.fst_compProd _ _

/-- The blanket-internal marginal is the authored internal conditional kernel
composed with the native blanket marginal. -/
theorem staticJoint_map_blanket_internal
    (model : StaticModel Internal Sensory Active External) :
    (embeddedLaw (staticJoint model)).map
        (fun state => (blanketCoordinate state, internalCoordinate state)) =
      (embeddedLaw (staticJoint model)).map blanketCoordinate ⊗ₘ
        embeddedKernel model.internalGiven := by
  rw [staticJoint_map_blanket, staticJoint_map_blanketInternal_embedded]

/-- The blanket-external marginal is the authored external conditional kernel
composed with the native blanket marginal. -/
theorem staticJoint_map_blanket_external
    (model : StaticModel Internal Sensory Active External) :
    (embeddedLaw (staticJoint model)).map
        (fun state => (blanketCoordinate state, externalCoordinate state)) =
      (embeddedLaw (staticJoint model)).map blanketCoordinate ⊗ₘ
        embeddedKernel model.externalGiven := by
  calc
    (embeddedLaw (staticJoint model)).map
        (fun state => (blanketCoordinate state, externalCoordinate state)) =
      embeddedLaw ((staticJoint model).map
        (fun state => (blanketCoordinate state, externalCoordinate state))) :=
          embeddedLaw_map
            (α := StaticState Internal Sensory Active External)
            (β := Blanket Sensory Active × External)
            (staticJoint model)
            (fun state => (blanketCoordinate state, externalCoordinate state))
    _ = embeddedLaw (model.externalGiven.joint model.blanketLaw) := by
          rw [staticJoint_map_blanketExternal_finite (model := model)]
    _ = embeddedLaw model.blanketLaw ⊗ₘ embeddedKernel model.externalGiven :=
          embeddedLaw_joint_eq_compProd _ _
    _ = (embeddedLaw (staticJoint model)).map blanketCoordinate ⊗ₘ
          embeddedKernel model.externalGiven := by
          rw [staticJoint_map_blanket]

/-- The complete native joint is the blanket marginal followed by the product
of the authored internal and external conditional kernels. -/
theorem staticJoint_map_triple_factorization
    (model : StaticModel Internal Sensory Active External) :
    (embeddedLaw (staticJoint model)).map blanketTripleCoordinate =
      (embeddedLaw (staticJoint model)).map blanketCoordinate ⊗ₘ
        (embeddedKernel model.internalGiven ×ₖ
          embeddedKernel model.externalGiven) := by
  calc
    (embeddedLaw (staticJoint model)).map blanketTripleCoordinate =
      embeddedLaw ((staticJoint model).map blanketTripleCoordinate) :=
        embeddedLaw_map
          (α := StaticState Internal Sensory Active External)
          (β := Blanket Sensory Active × (Internal × External))
          (staticJoint model) blanketTripleCoordinate
    _ = embeddedLaw
        ((conditionalPairKernel model).joint model.blanketLaw) := by
          rw [staticJoint_map_triple_finite (model := model)]
    _ = embeddedLaw model.blanketLaw ⊗ₘ
        embeddedKernel (conditionalPairKernel model) :=
          embeddedLaw_joint_eq_compProd _ _
    _ = embeddedLaw model.blanketLaw ⊗ₘ
        (embeddedKernel model.internalGiven ×ₖ
          embeddedKernel model.externalGiven) := by
          rw [embeddedConditionalPairKernel_eq_prod]
    _ = (embeddedLaw (staticJoint model)).map blanketCoordinate ⊗ₘ
        (embeddedKernel model.internalGiven ×ₖ
          embeddedKernel model.externalGiven) := by
          rw [staticJoint_map_blanket]

/-- The exact atomic rectangle factorization inherited from the finite static
joint.  On the discrete carrier these singleton rectangles generate the full
measurable space. -/
theorem staticJoint_rectangle_factorization
    (model : StaticModel Internal Sensory Active External)
    (blanket : Blanket Sensory Active) (internal : Internal)
    (external : External) :
    embeddedLaw (staticJoint model)
        (blanketCoordinate ⁻¹' {blanket} ∩
          internalCoordinate ⁻¹' {internal} ∩
          externalCoordinate ⁻¹' {external}) =
      ENNReal.ofReal (model.blanketLaw blanket) *
        ENNReal.ofReal (model.internalGiven blanket internal) *
          ENNReal.ofReal (model.externalGiven blanket external) := by
  have event_eq :
      blanketCoordinate ⁻¹' {blanket} ∩
          internalCoordinate ⁻¹' {internal} ∩
          externalCoordinate ⁻¹' {external} =
        ({((blanket, internal), external)} :
          Set (StaticState Internal Sensory Active External)) := by
    ext ⟨⟨stateBlanket, stateInternal⟩, stateExternal⟩
    simp [blanketCoordinate, internalCoordinate, externalCoordinate]
  rw [event_eq, embeddedLaw_apply_singleton, staticJoint_factorization]
  rw [ENNReal.ofReal_mul
      (mul_nonneg (model.blanketLaw.nonneg blanket)
        (model.internalGiven.nonneg blanket internal)),
    ENNReal.ofReal_mul (model.blanketLaw.nonneg blanket)]

private theorem internal_condDistrib_ae_eq
    [Nonempty Internal]
    (model : StaticModel Internal Sensory Active External) :
    condDistrib internalCoordinate blanketCoordinate
        (embeddedLaw (staticJoint model)) =ᵐ[
          (embeddedLaw (staticJoint model)).map blanketCoordinate]
      embeddedKernel model.internalGiven :=
  condDistrib_ae_eq_of_measure_eq_compProd_of_measurable
    blanketCoordinate_measurable internalCoordinate_measurable
    (staticJoint_map_blanket_internal model)

private theorem external_condDistrib_ae_eq
    [Nonempty External]
    (model : StaticModel Internal Sensory Active External) :
    condDistrib externalCoordinate blanketCoordinate
        (embeddedLaw (staticJoint model)) =ᵐ[
          (embeddedLaw (staticJoint model)).map blanketCoordinate]
      embeddedKernel model.externalGiven :=
  condDistrib_ae_eq_of_measure_eq_compProd_of_measurable
    blanketCoordinate_measurable externalCoordinate_measurable
    (staticJoint_map_blanket_external model)

/-- The finite blanket factorization induces Mathlib's native conditional
independence predicate for internal and external coordinates given the
blanket coordinate. -/
theorem staticJoint_condIndepFun
    [Nonempty Internal] [Nonempty External]
    (model : StaticModel Internal Sensory Active External) :
    CondIndepFun
      (MeasurableSpace.comap blanketCoordinate inferInstance)
      blanketCoordinate_measurable.comap_le
      internalCoordinate externalCoordinate
      (embeddedLaw (staticJoint model)) := by
  rw [condIndepFun_iff_map_prod_eq_prod_condDistrib_prod_condDistrib
    internalCoordinate_measurable externalCoordinate_measurable
    blanketCoordinate_measurable]
  have conditionalProduct :
      condDistrib internalCoordinate blanketCoordinate
          (embeddedLaw (staticJoint model)) ×ₖ
        condDistrib externalCoordinate blanketCoordinate
          (embeddedLaw (staticJoint model)) =ᵐ[
            (embeddedLaw (staticJoint model)).map blanketCoordinate]
        embeddedKernel model.internalGiven ×ₖ
          embeddedKernel model.externalGiven := by
    filter_upwards [internal_condDistrib_ae_eq model,
      external_condDistrib_ae_eq model] with blanket internal_eq external_eq
    simp only [Kernel.prod_apply]
    rw [internal_eq, external_eq]
  calc
    (embeddedLaw (staticJoint model)).map
        (fun state =>
          (blanketCoordinate state, internalCoordinate state,
            externalCoordinate state)) =
      (embeddedLaw (staticJoint model)).map blanketTripleCoordinate := rfl
    _ = (embeddedLaw (staticJoint model)).map blanketCoordinate ⊗ₘ
        (embeddedKernel model.internalGiven ×ₖ
          embeddedKernel model.externalGiven) :=
          staticJoint_map_triple_factorization model
    _ = (embeddedLaw (staticJoint model)).map blanketCoordinate ⊗ₘ
        (condDistrib internalCoordinate blanketCoordinate
            (embeddedLaw (staticJoint model)) ×ₖ
          condDistrib externalCoordinate blanketCoordinate
            (embeddedLaw (staticJoint model))) :=
          Measure.compProd_congr conditionalProduct.symm
    _ = (Kernel.id ×ₖ
          (condDistrib internalCoordinate blanketCoordinate
              (embeddedLaw (staticJoint model)) ×ₖ
            condDistrib externalCoordinate blanketCoordinate
              (embeddedLaw (staticJoint model)))) ∘ₘ
        (embeddedLaw (staticJoint model)).map blanketCoordinate :=
          Measure.compProd_eq_comp_prod _ _

/-- Conditional independence is preserved by measurable images of the
internal and external coordinates. -/
theorem condIndepFun_measurableImages
    [Nonempty Internal] [Nonempty External]
    {InternalImage ExternalImage : Type*}
    [MeasurableSpace InternalImage] [MeasurableSpace ExternalImage]
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
      (embeddedLaw (staticJoint model)) :=
  (staticJoint_condIndepFun model).comp internalMeasurable externalMeasurable

/-- Every authored factorized transition row induces a predicted native law
whose next internal and external coordinates are conditionally independent
given the next sensory-active blanket.  This is rowwise; arbitrary mixtures
over current states require additional hypotheses. -/
theorem prediction_preserves_nativeBlanket
    [Nonempty Internal] [Nonempty External]
    (dynamics : Dynamics Internal Sensory Active External)
    (current : DynamicState Internal Sensory Active External) :
    CondIndepFun
      (MeasurableSpace.comap blanketCoordinate inferInstance)
      blanketCoordinate_measurable.comap_le
      internalCoordinate externalCoordinate
      (embeddedLaw (staticJoint (nextStaticModel dynamics current))) :=
  staticJoint_condIndepFun (nextStaticModel dynamics current)

end StaticBlanket

section Nonvacuity

/-- A Boolean blanket with two positively weighted, perfectly correlated
sensory-active regimes.  Internal and external states both copy the sensory
coordinate, so their unconditional association is nontrivial while their
conditional law at each blanket value is a product of point masses. -/
noncomputable def correlatedBlanketModel : StaticModel Bool Bool Bool Bool where
  blanketLaw :=
    { mass := fun blanket => if blanket.1 = blanket.2 then (1 / 2 : ℝ) else 0
      nonneg := fun blanket => by split_ifs <;> positivity
      sum_one := by
        norm_num [Fintype.sum_prod_type] }
  internalGiven := FiniteKernel.deterministic fun blanket => blanket.1
  externalGiven := FiniteKernel.deterministic fun blanket => blanket.1

/-- The native theorem is nonvacuous: the Boolean model has two distinct
positive correlated blanket atoms and two distinct positive joint atoms. -/
theorem correlatedBlanket_nonvacuous :
    letI : MeasurableSpace Bool := ⊤
    CondIndepFun
        (MeasurableSpace.comap blanketCoordinate inferInstance)
        blanketCoordinate_measurable.comap_le
        internalCoordinate externalCoordinate
        (embeddedLaw (staticJoint correlatedBlanketModel)) ∧
      staticJoint correlatedBlanketModel (((false, false), false), false) = 1 / 2 ∧
      staticJoint correlatedBlanketModel (((true, true), true), true) = 1 / 2 ∧
      staticJoint correlatedBlanketModel (((false, true), false), false) ≠ 1 / 2 := by
  let _ : MeasurableSpace Bool := ⊤
  refine ⟨staticJoint_condIndepFun correlatedBlanketModel, ?_⟩
  norm_num [correlatedBlanketModel, staticJoint_factorization,
    FiniteKernel.deterministic]

end Nonvacuity

end

end FEP.NativeBlanket
