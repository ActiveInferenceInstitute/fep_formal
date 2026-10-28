module
public import FepSketches.finite_probability
public import Mathlib.InformationTheory.KullbackLeibler.Basic
public import Mathlib.MeasureTheory.Integral.Bochner.SumMeasure

@[expose] public section

/-!
# Finite information theory

Entropy uses Mathlib's continuous extension `Real.negMulLog`, so zero-mass
atoms contribute exactly zero.  Finite KL is represented by the nonnegative
`klFun` integrand.  Normalization recovers separation even when the reference
law has zero-mass atoms; strict reference support is required only for the
logarithmic cross-entropy identity.
-/

namespace FEP.FiniteInformation

/-! Generic finite-weight Dirac helpers. These are measures of arbitrary nonnegative
finite mass, not a second normalized probability carrier. Mathlib native KL
retains its mass correction; the probability boundary requires normalization.
The separately retained standalone upstream draft uses only Mathlib imports. -/

open MeasureTheory ProbabilityTheory
open scoped BigOperators ENNReal MeasureTheory ProbabilityTheory


noncomputable def finiteWeightMeasure {α : Type*} [Fintype α] [MeasurableSpace α]
    (p : α → ℝ) : Measure α :=
  Measure.sum fun x => ENNReal.ofReal (p x) • Measure.dirac x

instance {α : Type*} [Fintype α] [MeasurableSpace α] (p : α → ℝ) :
    IsFiniteMeasure (finiteWeightMeasure p) where
  measure_univ_lt_top := by
    simp only [finiteWeightMeasure, Measure.sum_apply_of_countable, tsum_fintype,
      Measure.smul_apply, Measure.dirac_apply_of_mem (Set.mem_univ _), smul_eq_mul,
      mul_one]
    exact ENNReal.sum_lt_top.mpr fun _ _ => ENNReal.ofReal_lt_top

@[simp] theorem finiteWeightMeasure_singleton {α : Type*} [Fintype α]
    [MeasurableSpace α] [DiscreteMeasurableSpace α] (p : α → ℝ) (x : α) :
    finiteWeightMeasure p {x} = ENNReal.ofReal (p x) := by
  simpa [finiteWeightMeasure] using
    (Measure.sum_smul_dirac_singleton (f := fun a : α => ENNReal.ofReal (p a)) (a := x))

theorem finiteWeightMeasure_withDensity_ratio {α : Type*} [Fintype α]
    [MeasurableSpace α] [DiscreteMeasurableSpace α] (p q : α → ℝ)
    (hp : ∀ x, 0 ≤ p x) (hq : ∀ x, 0 ≤ q x)
    (hsupport : ∀ x, p x ≠ 0 → 0 < q x) :
    (finiteWeightMeasure q).withDensity (fun x => ENNReal.ofReal (p x / q x)) =
      finiteWeightMeasure p := by
  classical
  apply Measure.ext_of_singleton
  intro x
  rw [withDensity_apply _ MeasurableSet.of_discrete, lintegral_singleton,
    finiteWeightMeasure_singleton, finiteWeightMeasure_singleton,
    ← ENNReal.ofReal_mul (div_nonneg (hp x) (hq x))]
  by_cases hzero : q x = 0
  · have hpzero : p x = 0 := by
      by_contra hne
      exact (ne_of_gt (hsupport x hne)) hzero
    simp [hzero, hpzero]
  · rw [div_mul_cancel₀ _ hzero]

theorem klDiv_finiteWeightMeasure {α : Type*} [Fintype α]
    [MeasurableSpace α] [DiscreteMeasurableSpace α] (p q : α → ℝ)
    (hp : ∀ x, 0 ≤ p x) (hq : ∀ x, 0 ≤ q x)
    (hsupport : ∀ x, p x ≠ 0 → 0 < q x) :
    InformationTheory.klDiv (finiteWeightMeasure p) (finiteWeightMeasure q) =
      ENNReal.ofReal (∑ x, q x * InformationTheory.klFun (p x / q x)) := by
  have hDensity := finiteWeightMeasure_withDensity_ratio p q hp hq hsupport
  have hAC : finiteWeightMeasure p ≪ finiteWeightMeasure q := by
    rw [← hDensity]
    exact withDensity_absolutelyContinuous _ _
  rw [InformationTheory.klDiv_eq_lintegral_klFun_of_ac hAC]
  have hRN :
      (finiteWeightMeasure p).rnDeriv (finiteWeightMeasure q) =ᵐ[finiteWeightMeasure q]
        fun x => ENNReal.ofReal (p x / q x) := by
    rw [← hDensity]
    exact Measure.rnDeriv_withDensity _ (by fun_prop)
  have hIntegrand :
      (fun x => ENNReal.ofReal
        (InformationTheory.klFun ((finiteWeightMeasure p).rnDeriv (finiteWeightMeasure q) x).toReal))
          =ᵐ[finiteWeightMeasure q]
        fun x => ENNReal.ofReal (InformationTheory.klFun (p x / q x)) := by
    filter_upwards [hRN] with x hx
    rw [hx, ENNReal.toReal_ofReal (div_nonneg (hp x) (hq x))]
  rw [lintegral_congr_ae hIntegrand, lintegral_fintype,
    ENNReal.ofReal_sum_of_nonneg]
  · apply Finset.sum_congr rfl
    intro x _
    rw [finiteWeightMeasure_singleton, ENNReal.ofReal_mul (hq x), mul_comm]
  · intro x _
    exact mul_nonneg (hq x) (InformationTheory.klFun_nonneg (div_nonneg (hp x) (hq x)))

theorem finiteWeightMeasure_probability {α : Type*} [Fintype α]
    [MeasurableSpace α] (p : α → ℝ) (hp : ∀ x, 0 ≤ p x)
    (hnormalized : ∑ x, p x = 1) : IsProbabilityMeasure (finiteWeightMeasure p) where
  measure_univ := by
    simp only [finiteWeightMeasure, Measure.sum_apply_of_countable, tsum_fintype,
      Measure.smul_apply, Measure.dirac_apply_of_mem (Set.mem_univ _), smul_eq_mul,
      mul_one]
    rw [← ENNReal.ofReal_sum_of_nonneg (fun x _ => hp x), hnormalized]
    simp


open FEP Finset InformationTheory
open scoped BigOperators

variable {α β : Type*} [Fintype α] [Fintype β]

/-- Shannon entropy in nats, with the convention `0 log 0 = 0`. -/
noncomputable def entropy (p : FiniteLaw α) : ℝ :=
  ∑ x, Real.negMulLog (p x)

/-- Expected negative log score of `q` under `p`. -/
noncomputable def crossEntropy (p q : FiniteLaw α) : ℝ :=
  ∑ x, -(p x) * Real.log (q x)

/-- Finite KL divergence as a weighted sum of Mathlib's nonnegative `klFun`. -/
noncomputable def finiteKL (p q : FiniteLaw α) : ℝ :=
  ∑ x, q x * klFun (p x / q x)

/-- Finite Shannon entropy is nonnegative. -/
theorem entropy_nonneg (p : FiniteLaw α) : 0 ≤ entropy p := by
  exact Finset.sum_nonneg fun x _ =>
    Real.negMulLog_nonneg (p.nonneg x) (p.mass_le_one x)

/-- Finite KL is nonnegative, including at zero reference atoms under the
totalized real-division convention. -/
theorem finiteKL_nonneg (p q : FiniteLaw α) : 0 ≤ finiteKL p q := by
  exact Finset.sum_nonneg fun x _ =>
    mul_nonneg (q.nonneg x)
      (klFun_nonneg (div_nonneg (p.nonneg x) (q.nonneg x)))

/-- A finite law has zero divergence from itself, including at zero atoms. -/
theorem finiteKL_self (p : FiniteLaw α) : finiteKL p p = 0 := by
  apply Finset.sum_eq_zero
  intro x _
  by_cases hx : p x = 0
  · simp [hx]
  · rw [div_self hx, klFun_one, mul_zero]

/-- Explicit boundary witness for the totalized real-valued convention:
cross-entropy between disjoint Boolean point masses evaluates to zero because
`Real.log 0 = 0`.  This is not the extended-real cross-entropy, which would be
infinite. -/
theorem crossEntropy_disjoint_pointMass_totalized :
    crossEntropy (FiniteLaw.pointMass true) (FiniteLaw.pointMass false) = 0 := by
  rw [crossEntropy, Fintype.sum_bool]
  norm_num [FiniteLaw.pointMass]

/-- The same disjoint Boolean point masses have finite totalized KL value `1`,
not the extended-real value `∞`.  Support hypotheses on logarithmic identities
are therefore semantically essential, while normalization still makes zero
divergence separating below. -/
theorem finiteKL_disjoint_pointMass_totalized :
    finiteKL (FiniteLaw.pointMass true) (FiniteLaw.pointMass false) = 1 := by
  rw [finiteKL, Fintype.sum_bool]
  norm_num [FiniteLaw.pointMass, klFun_zero]

/-- For normalized finite laws, totalized finite KL vanishes exactly at
equality, without any support assumption.  A zero divergence first forces
equality wherever the reference has positive mass.  Normalization then forces
the actual law to put zero mass on every zero-reference atom. -/
theorem finiteKL_eq_zero_iff (p q : FiniteLaw α) :
    finiteKL p q = 0 ↔ p = q := by
  classical
  constructor
  · intro hzero
    have hterms := (Finset.sum_eq_zero_iff_of_nonneg
      (fun y _ =>
        mul_nonneg (q.nonneg y)
          (klFun_nonneg (div_nonneg (p.nonneg y) (q.nonneg y))))).mp hzero
    have heq_of_reference_ne_zero : ∀ x, q x ≠ 0 → p x = q x := by
      intro x hx
      have hterm := hterms x (Finset.mem_univ x)
      have hfun : klFun (p x / q x) = 0 :=
        (mul_eq_zero.mp hterm).resolve_left hx
      have hratio : p x / q x = 1 :=
        (klFun_eq_zero_iff (div_nonneg (p.nonneg x) (q.nonneg x))).mp hfun
      exact (div_eq_one_iff_eq hx).mp hratio
    have hsplit :
        (∑ x : α, p x) =
          (∑ x : α, if q x = 0 then p x else 0) +
            ∑ x : α, if q x ≠ 0 then p x else 0 := by
      rw [← Finset.sum_add_distrib]
      apply Finset.sum_congr rfl
      intro x _
      by_cases hx : q x = 0 <;> simp [hx]
    have hpositiveMass :
        (∑ x : α, if q x ≠ 0 then p x else 0) = 1 := by
      calc
        (∑ x : α, if q x ≠ 0 then p x else 0) =
            ∑ x : α, if q x ≠ 0 then q x else 0 := by
              apply Finset.sum_congr rfl
              intro x _
              by_cases hx : q x = 0
              · simp [hx]
              · simp [hx, heq_of_reference_ne_zero x hx]
        _ = ∑ x : α, q x := by
          apply Finset.sum_congr rfl
          intro x _
          by_cases hx : q x = 0 <;> simp [hx]
        _ = 1 := q.sum_one
    have hzeroReferenceMass :
        (∑ x : α, if q x = 0 then p x else 0) = 0 := by
      linarith [p.sum_one, hsplit, hpositiveMass]
    apply FiniteLaw.ext_mass
    funext x
    by_cases hx : q x = 0
    · have hzeroTerms := (Finset.sum_eq_zero_iff_of_nonneg
        (fun y _ => by
          by_cases hy : q y = 0
          · simpa [hy] using p.nonneg y
          · simp [hy])).mp hzeroReferenceMass
      simpa [hx] using hzeroTerms x (Finset.mem_univ x)
    · exact heq_of_reference_ne_zero x hx
  · intro hpq
    subst p
    exact finiteKL_self q

/-- Pointwise conversion from the `klFun` integrand to logarithmic scoring. -/
theorem weighted_klFun_eq_log_score {a b : ℝ} (hb : 0 < b) :
    b * klFun (a / b) =
      (-a * Real.log b - Real.negMulLog a) + (b - a) := by
  by_cases ha : a = 0
  · simp [ha, klFun_zero]
  · rw [klFun_apply, Real.negMulLog_eq_neg, Real.log_div ha (ne_of_gt hb)]
    field_simp [ne_of_gt hb]
    ring

/-- Under full reference support, finite KL is cross-entropy minus entropy. -/
theorem finiteKL_eq_crossEntropy_sub_entropy (p q : FiniteLaw α)
    (hq : ∀ x, 0 < q x) :
    finiteKL p q = crossEntropy p q - entropy p := by
  simp_rw [finiteKL, weighted_klFun_eq_log_score (hq _)]
  rw [Finset.sum_add_distrib, Finset.sum_sub_distrib]
  have hnorm : (∑ i : α, (q.mass i - p.mass i)) = 0 := by
    rw [Finset.sum_sub_distrib, q.sum_one, p.sum_one, sub_self]
  rw [hnorm, add_zero]
  rfl

/-- Conditional entropy of a normalized finite kernel under an input law. -/
noncomputable def conditionalEntropy
    (prior : FiniteLaw α) (kernel : FiniteKernel α β) : ℝ :=
  ∑ x, prior x * entropy (kernel.row x)

/-- Expected cross-entropy between two finite kernels under one input law. -/
noncomputable def conditionalCrossEntropy
    (prior : FiniteLaw α) (actual reference : FiniteKernel α β) : ℝ :=
  ∑ x, prior x * crossEntropy (actual.row x) (reference.row x)

/-- Expected row-wise KL divergence between two finite kernels. -/
noncomputable def conditionalKL
    (prior : FiniteLaw α) (actual reference : FiniteKernel α β) : ℝ :=
  ∑ x, prior x * finiteKL (actual.row x) (reference.row x)

/-- Conditional entropy is nonnegative for every normalized finite kernel. -/
theorem conditionalEntropy_nonneg
    (prior : FiniteLaw α) (kernel : FiniteKernel α β) :
    0 ≤ conditionalEntropy prior kernel := by
  exact Finset.sum_nonneg fun x _ =>
    mul_nonneg (prior.nonneg x) (entropy_nonneg (kernel.row x))

/-- Expected conditional KL is nonnegative without a support assumption. -/
theorem conditionalKL_nonneg
    (prior : FiniteLaw α) (actual reference : FiniteKernel α β) :
    0 ≤ conditionalKL prior actual reference := by
  exact Finset.sum_nonneg fun x _ =>
    mul_nonneg (prior.nonneg x)
      (finiteKL_nonneg (actual.row x) (reference.row x))

/-- Positive input support makes zero conditional KL equivalent to equality of
the two finite kernels; no reference-row support is needed. -/
theorem conditionalKL_eq_zero_iff
    (prior : FiniteLaw α) (actual reference : FiniteKernel α β)
    (hprior : ∀ x, 0 < prior x) :
    conditionalKL prior actual reference = 0 ↔ actual = reference := by
  constructor
  · intro hzero
    simp only [conditionalKL] at hzero
    have hterms := (Finset.sum_eq_zero_iff_of_nonneg
      (fun x _ =>
        mul_nonneg (prior.nonneg x)
          (finiteKL_nonneg (actual.row x) (reference.row x)))).mp hzero
    apply FiniteKernel.ext_mass
    funext x y
    have hterm := hterms x (Finset.mem_univ x)
    have hrowZero : finiteKL (actual.row x) (reference.row x) = 0 :=
      (mul_eq_zero.mp hterm).resolve_left (ne_of_gt (hprior x))
    have hrowEq : actual.row x = reference.row x :=
      (finiteKL_eq_zero_iff (actual.row x) (reference.row x)).mp hrowZero
    exact congrFun (congrArg FiniteLaw.mass hrowEq) y
  · rintro rfl
    apply Finset.sum_eq_zero
    intro x _
    rw [finiteKL_self, mul_zero]

/-- Entropy chain rule for the joint law generated by a finite kernel. -/
theorem entropy_joint_eq_add_conditional
    (prior : FiniteLaw α) (kernel : FiniteKernel α β) :
    entropy (kernel.joint prior) =
      entropy prior + conditionalEntropy prior kernel := by
  classical
  simp only [entropy, FiniteKernel.joint, Fintype.sum_prod_type,
    Real.negMulLog_mul, conditionalEntropy, FiniteKernel.row]
  simp_rw [Finset.sum_add_distrib]
  congr 1
  · apply Finset.sum_congr rfl
    intro x _
    rw [← Finset.sum_mul, kernel.sum_one, one_mul]
  · simp_rw [Finset.mul_sum]

/-- Cross-entropy of two prior-kernel joint laws obeys a finite chain rule. -/
theorem crossEntropy_joint
    (actualPrior referencePrior : FiniteLaw α)
    (actualKernel referenceKernel : FiniteKernel α β)
    (hprior : ∀ x, 0 < referencePrior x)
    (hkernel : ∀ x y, 0 < referenceKernel x y) :
    crossEntropy (actualKernel.joint actualPrior)
        (referenceKernel.joint referencePrior) =
      crossEntropy actualPrior referencePrior +
        conditionalCrossEntropy actualPrior actualKernel referenceKernel := by
  classical
  simp only [crossEntropy, FiniteKernel.joint, Fintype.sum_prod_type,
    conditionalCrossEntropy, FiniteKernel.row]
  simp_rw [Real.log_mul (ne_of_gt (hprior _)) (ne_of_gt (hkernel _ _))]
  simp only [mul_add]
  rw [← Finset.sum_add_distrib]
  apply Finset.sum_congr rfl
  intro x _
  rw [Finset.sum_add_distrib]
  congr 1
  · rw [← Finset.sum_mul]
    simp [← Finset.mul_sum, actualKernel.sum_one]
  · rw [Finset.mul_sum]
    apply Finset.sum_congr rfl
    intro y _
    ring

/-- Under row-wise reference support, conditional KL is conditional
cross-entropy minus conditional entropy. -/
theorem conditionalKL_eq_crossEntropy_sub_entropy
    (prior : FiniteLaw α) (actual reference : FiniteKernel α β)
    (hreference : ∀ x y, 0 < reference x y) :
    conditionalKL prior actual reference =
      conditionalCrossEntropy prior actual reference -
        conditionalEntropy prior actual := by
  simp only [conditionalKL, conditionalCrossEntropy, conditionalEntropy]
  rw [← Finset.sum_sub_distrib]
  apply Finset.sum_congr rfl
  intro x _
  rw [finiteKL_eq_crossEntropy_sub_entropy (actual.row x) (reference.row x)
    (hreference x)]
  ring

/-- KL between two finite prior-kernel joint laws decomposes into prior KL and
expected conditional KL.  Strict positivity is imposed only on the reference
law and reference kernel, exactly where logarithmic separation requires it. -/
theorem finiteKL_joint_chain_rule
    (actualPrior referencePrior : FiniteLaw α)
    (actualKernel referenceKernel : FiniteKernel α β)
    (hprior : ∀ x, 0 < referencePrior x)
    (hkernel : ∀ x y, 0 < referenceKernel x y) :
    finiteKL (actualKernel.joint actualPrior)
        (referenceKernel.joint referencePrior) =
      finiteKL actualPrior referencePrior +
        conditionalKL actualPrior actualKernel referenceKernel := by
  rw [finiteKL_eq_crossEntropy_sub_entropy _ _
      (fun xy => mul_pos (hprior xy.1) (hkernel xy.1 xy.2)),
    crossEntropy_joint actualPrior referencePrior actualKernel referenceKernel
      hprior hkernel,
    entropy_joint_eq_add_conditional,
    finiteKL_eq_crossEntropy_sub_entropy actualPrior referencePrior hprior,
    conditionalKL_eq_crossEntropy_sub_entropy actualPrior actualKernel
      referenceKernel hkernel]
  ring

/-- Marginalizing away the kernel output cannot increase KL divergence: the
joint divergence dominates the divergence between its input priors. -/
theorem finiteKL_prior_le_joint
    (actualPrior referencePrior : FiniteLaw α)
    (actualKernel referenceKernel : FiniteKernel α β)
    (hprior : ∀ x, 0 < referencePrior x)
    (hkernel : ∀ x y, 0 < referenceKernel x y) :
    finiteKL actualPrior referencePrior ≤
      finiteKL (actualKernel.joint actualPrior)
        (referenceKernel.joint referencePrior) := by
  rw [finiteKL_joint_chain_rule actualPrior referencePrior actualKernel
    referenceKernel hprior hkernel]
  exact le_add_of_nonneg_right
    (conditionalKL_nonneg actualPrior actualKernel referenceKernel)

/-- Shannon entropy is additive on independent finite products. -/
theorem entropy_product (p : FiniteLaw α) (q : FiniteLaw β) :
    entropy (p.product q) = entropy p + entropy q := by
  classical
  simp only [entropy, Fintype.sum_prod_type, FiniteLaw.product,
    Real.negMulLog_mul]
  simp_rw [Finset.sum_add_distrib]
  congr 1
  · apply Finset.sum_congr rfl
    intro x _
    rw [← Finset.sum_mul, q.sum_one, one_mul]
  · rw [Finset.sum_comm]
    apply Finset.sum_congr rfl
    intro y _
    rw [← Finset.sum_mul, p.sum_one, one_mul]

/-- KL divergence is additive across independent finite products when both
reference factors have full support. -/
theorem finiteKL_product
    (p q : FiniteLaw α) (r s : FiniteLaw β)
    (hq : ∀ x, 0 < q x) (hs : ∀ y, 0 < s y) :
    finiteKL (p.product r) (q.product s) =
      finiteKL p q + finiteKL r s := by
  let actualKernel : FiniteKernel α β :=
    { mass := fun _ y => r y
      nonneg := fun _ y => r.nonneg y
      sum_one := fun _ => r.sum_one }
  let referenceKernel : FiniteKernel α β :=
    { mass := fun _ y => s y
      nonneg := fun _ y => s.nonneg y
      sum_one := fun _ => s.sum_one }
  have hchain := finiteKL_joint_chain_rule p q actualKernel referenceKernel hq
    (fun _ y => hs y)
  have hactualJoint : actualKernel.joint p = p.product r := by
    apply FiniteLaw.ext_mass
    rfl
  have hreferenceJoint : referenceKernel.joint q = q.product s := by
    apply FiniteLaw.ext_mass
    rfl
  have hactualRow : ∀ x, actualKernel.row x = r := by
    intro x
    apply FiniteLaw.ext_mass
    rfl
  have hreferenceRow : ∀ x, referenceKernel.row x = s := by
    intro x
    apply FiniteLaw.ext_mass
    rfl
  have hconditional : conditionalKL p actualKernel referenceKernel =
      finiteKL r s := by
    simp only [conditionalKL]
    simp_rw [hactualRow, hreferenceRow]
    rw [← Finset.sum_mul, p.sum_one, one_mul]
  rw [hactualJoint, hreferenceJoint, hconditional] at hchain
  exact hchain

/-- Mutual information as KL from a joint law to the product of its marginals. -/
noncomputable def mutualInformation (joint : FiniteLaw (α × β)) : ℝ :=
  finiteKL joint (joint.fstMarginal.product joint.sndMarginal)

/-- Mutual information is nonnegative. -/
theorem mutualInformation_nonneg (joint : FiniteLaw (α × β)) :
    0 ≤ mutualInformation joint :=
  finiteKL_nonneg _ _

/-- Independent product laws have exactly zero mutual information. -/
theorem mutualInformation_product_eq_zero (p : FiniteLaw α) (q : FiniteLaw β) :
    mutualInformation (p.product q) = 0 := by
  rw [mutualInformation, FiniteLaw.product_fstMarginal,
    FiniteLaw.product_sndMarginal]
  exact finiteKL_self (p.product q)

/-- Cross-entropy against the product of positive marginals separates into
the two marginal entropies. -/
theorem crossEntropy_product_marginals (joint : FiniteLaw (α × β))
    (hfst : ∀ x, 0 < joint.fstMarginal x)
    (hsnd : ∀ y, 0 < joint.sndMarginal y) :
    crossEntropy joint (joint.fstMarginal.product joint.sndMarginal) =
      entropy joint.fstMarginal + entropy joint.sndMarginal := by
  classical
  simp only [crossEntropy, entropy, Fintype.sum_prod_type, FiniteLaw.product]
  simp_rw [Real.log_mul (ne_of_gt (hfst _)) (ne_of_gt (hsnd _))]
  simp only [mul_add, neg_mul]
  simp_rw [Finset.sum_add_distrib]
  congr 1
  · apply Finset.sum_congr rfl
    intro x _
    simp only [FiniteLaw.fstMarginal, Real.negMulLog_eq_neg]
    rw [Finset.sum_neg_distrib, Finset.sum_mul]
  · rw [Finset.sum_comm]
    apply Finset.sum_congr rfl
    intro y _
    simp only [FiniteLaw.sndMarginal, Real.negMulLog_eq_neg]
    rw [Finset.sum_neg_distrib, Finset.sum_mul]

/-- Mutual information equals the entropy sum of the marginals minus joint
entropy whenever both marginals have full support. -/
theorem mutualInformation_eq_entropy_marginals (joint : FiniteLaw (α × β))
    (hfst : ∀ x, 0 < joint.fstMarginal x)
    (hsnd : ∀ y, 0 < joint.sndMarginal y) :
    mutualInformation joint =
      entropy joint.fstMarginal + entropy joint.sndMarginal - entropy joint := by
  rw [mutualInformation,
    finiteKL_eq_crossEntropy_sub_entropy _ _
      (fun xy => mul_pos (hfst xy.1) (hsnd xy.2)),
    crossEntropy_product_marginals joint hfst hsnd]

/-- Zero mutual information characterizes factorization of the joint into the
product of its marginals, without marginal-support assumptions. -/
theorem mutualInformation_eq_zero_iff (joint : FiniteLaw (α × β)) :
    mutualInformation joint = 0 ↔
      joint = joint.fstMarginal.product joint.sndMarginal := by
  exact finiteKL_eq_zero_iff joint
    (joint.fstMarginal.product joint.sndMarginal)

/-- Information gain through a finite kernel is predictive entropy minus the
kernel's conditional entropy. -/
theorem mutualInformation_eq_predictive_entropy_sub_conditional
    (prior : FiniteLaw α) (kernel : FiniteKernel α β)
    (hprior : ∀ x, 0 < prior x)
    (hpredictive : ∀ y, 0 < kernel.predictive prior y) :
    mutualInformation (kernel.joint prior) =
      entropy (kernel.predictive prior) - conditionalEntropy prior kernel := by
  have hfst : (kernel.joint prior).fstMarginal = prior := by
    apply FiniteLaw.ext_mass
    funext x
    exact FiniteKernel.joint_fstMarginal_mass prior kernel x
  calc
    mutualInformation (kernel.joint prior) =
        entropy (kernel.joint prior).fstMarginal +
            entropy (kernel.joint prior).sndMarginal -
          entropy (kernel.joint prior) :=
      mutualInformation_eq_entropy_marginals (kernel.joint prior)
        (fun x => by simpa [hfst] using hprior x) hpredictive
    _ = entropy prior + entropy (kernel.predictive prior) -
          (entropy prior + conditionalEntropy prior kernel) := by
      rw [hfst]
      change entropy prior + entropy (kernel.predictive prior) -
          entropy (kernel.joint prior) = _
      rw [entropy_joint_eq_add_conditional]
    _ = entropy (kernel.predictive prior) -
          conditionalEntropy prior kernel := by ring

/-- Information gain cannot exceed predictive entropy under the same support
conditions needed for the entropy representation. -/
theorem mutualInformation_le_predictive_entropy
    (prior : FiniteLaw α) (kernel : FiniteKernel α β)
    (hprior : ∀ x, 0 < prior x)
    (hpredictive : ∀ y, 0 < kernel.predictive prior y) :
    mutualInformation (kernel.joint prior) ≤
      entropy (kernel.predictive prior) := by
  rw [mutualInformation_eq_predictive_entropy_sub_conditional prior kernel
    hprior hpredictive]
  linarith [conditionalEntropy_nonneg prior kernel]

/-! ## Maximum entropy on the uniform carrier -/

/-- Every atom of the uniform law on a nonempty finite type is positive. -/
theorem uniform_mass_pos [Nonempty α] (x : α) :
    0 < (FiniteLaw.uniform : FiniteLaw α) x := by
  change 0 < ((Fintype.card α : ℝ)⁻¹)
  exact inv_pos.mpr (Nat.cast_pos.mpr Fintype.card_pos)

/-- Cross-entropy against the uniform law is the constant `log n`. -/
theorem crossEntropy_uniform [Nonempty α] (p : FiniteLaw α) :
    crossEntropy p FiniteLaw.uniform = Real.log (Fintype.card α) := by
  unfold crossEntropy
  have h : ∀ x : α, -(p x) * Real.log ((FiniteLaw.uniform : FiniteLaw α) x) =
      p x * Real.log (Fintype.card α) := by
    intro x
    change -(p x) * Real.log ((Fintype.card α : ℝ)⁻¹) = _
    rw [Real.log_inv]
    ring
  rw [Finset.sum_congr rfl fun x _ => h x, ← Finset.sum_mul, p.sum_one, one_mul]

/-- Maximum entropy on a finite carrier: `H(p) ≤ log n`. -/
theorem entropy_le_log_card [Nonempty α] (p : FiniteLaw α) :
    entropy p ≤ Real.log (Fintype.card α) := by
  have h := finiteKL_eq_crossEntropy_sub_entropy p FiniteLaw.uniform
    uniform_mass_pos
  rw [crossEntropy_uniform] at h
  linarith [finiteKL_nonneg p (FiniteLaw.uniform : FiniteLaw α)]

/-- The bound `H(p) = log n` is attained exactly by the uniform law. -/
theorem entropy_eq_log_card_iff [Nonempty α] (p : FiniteLaw α) :
    entropy p = Real.log (Fintype.card α) ↔ p = FiniteLaw.uniform := by
  have h := finiteKL_eq_crossEntropy_sub_entropy p FiniteLaw.uniform
    uniform_mass_pos
  rw [crossEntropy_uniform] at h
  rw [← finiteKL_eq_zero_iff]
  constructor <;> intro h' <;> linarith

/-- Strict form: any non-uniform law has entropy strictly below `log n`. -/
theorem entropy_lt_log_card_of_ne_uniform [Nonempty α] (p : FiniteLaw α)
    (hp : p ≠ FiniteLaw.uniform) :
    entropy p < Real.log (Fintype.card α) :=
  lt_of_le_of_ne (entropy_le_log_card p)
    fun h => hp ((entropy_eq_log_card_iff p).mp h)

/-- A biased Bool law with masses `3/4` and `1/4`. -/
noncomputable def boolBiased : FiniteLaw Bool where
  mass b := if b then 3 / 4 else 1 / 4
  nonneg b := by cases b <;> norm_num
  sum_one := by simp; norm_num

/-- Strict witness: the biased Bool law has entropy strictly below `log 2`. -/
theorem boolBiased_entropy_lt_log_two :
    entropy boolBiased < Real.log 2 := by
  have hne : boolBiased ≠ (FiniteLaw.uniform : FiniteLaw Bool) := by
    intro h
    have := congrArg (fun r : FiniteLaw Bool => r.mass true) h
    simp [boolBiased, FiniteLaw.uniform] at this
    norm_num at this
  simpa using entropy_lt_log_card_of_ne_uniform boolBiased hne

end FEP.FiniteInformation
