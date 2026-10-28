module
public import FepSketches.finite_probability
public import Mathlib.LinearAlgebra.Matrix.NonsingularInverse
public import Mathlib.Tactic.FieldSimp
public import Mathlib.Tactic.NormNum
public import Mathlib.Tactic.Ring

@[expose] public section

/-!
# Multidimensional finite Fisher geometry

The Fisher metric is the probability-weighted Gram form of a centered score
field.  Positive semidefiniteness is unconditional; positive definiteness is
derived only under full support and an explicit score-identifiability premise.
-/

namespace FEP.InformationGeometry

open FEP Finset
open scoped BigOperators Matrix

variable {Outcome : Type*} [Fintype Outcome]
variable {d k m : ℕ}

/-- A finite statistical score model with its zero-mean score law recorded. -/
structure ScoreModel (Outcome : Type*) [Fintype Outcome] (d : ℕ) where
  law : FiniteLaw Outcome
  score : Outcome → Fin d → ℝ
  centered : ∀ coordinate,
    ∑ outcome, law outcome * score outcome coordinate = 0

/-- Pair a score covector with one parameter-space tangent. -/
def scorePairing (model : ScoreModel Outcome d)
    (tangent : Fin d → ℝ) (outcome : Outcome) : ℝ :=
  ∑ coordinate, model.score outcome coordinate * tangent coordinate

/-- Fisher information matrix of a finite score model. -/
def fisherMatrix (model : ScoreModel Outcome d) : Matrix (Fin d) (Fin d) ℝ :=
  fun i j => ∑ outcome,
    model.law outcome * model.score outcome i * model.score outcome j

/-- Fisher metric as the expected product of directional scores. -/
def fisherMetric (model : ScoreModel Outcome d)
    (left right : Fin d → ℝ) : ℝ :=
  ∑ outcome, model.law outcome *
    scorePairing model left outcome * scorePairing model right outcome

/-- Expected score is zero in every coordinate. -/
theorem expectedScore_zero (model : ScoreModel Outcome d) (coordinate : Fin d) :
    ∑ outcome, model.law outcome * model.score outcome coordinate = 0 :=
  model.centered coordinate

/-- The finite Fisher information matrix is symmetric. -/
theorem fisherMatrix_symm (model : ScoreModel Outcome d) :
    (fisherMatrix model).IsSymm := by
  apply Matrix.IsSymm.ext
  intro i j
  apply Finset.sum_congr rfl
  intro outcome _
  ring

/-- The Fisher metric is symmetric. -/
theorem fisherMetric_symm (model : ScoreModel Outcome d)
    (left right : Fin d → ℝ) :
    fisherMetric model left right = fisherMetric model right left := by
  apply Finset.sum_congr rfl
  intro outcome _
  ring

/-- Every tangent has nonnegative Fisher self-pairing. -/
theorem fisherMetric_nonneg (model : ScoreModel Outcome d)
    (tangent : Fin d → ℝ) :
    0 ≤ fisherMetric model tangent tangent := by
  exact Finset.sum_nonneg fun outcome _ => by
    simpa [mul_assoc] using
      mul_nonneg (model.law.nonneg outcome)
        (mul_self_nonneg (scorePairing model tangent outcome))

/-- Under full support, a zero Fisher norm is exactly a tangent annihilated by
every score covector. -/
theorem fisherMetric_eq_zero_iff (model : ScoreModel Outcome d)
    (hsupport : ∀ outcome, 0 < model.law outcome)
    (tangent : Fin d → ℝ) :
    fisherMetric model tangent tangent = 0 ↔
      ∀ outcome, scorePairing model tangent outcome = 0 := by
  constructor
  · intro hzero outcome
    have hterm_nonneg : ∀ x ∈ (Finset.univ : Finset Outcome),
        0 ≤ model.law x * scorePairing model tangent x *
          scorePairing model tangent x := by
      intro x _
      simpa [mul_assoc] using
        mul_nonneg (model.law.nonneg x)
          (mul_self_nonneg (scorePairing model tangent x))
    have hterm := (Finset.sum_eq_zero_iff_of_nonneg hterm_nonneg).mp
      (by simpa [fisherMetric] using hzero)
      outcome (Finset.mem_univ outcome)
    have hterm' :
        model.law outcome *
          (scorePairing model tangent outcome *
            scorePairing model tangent outcome) = 0 := by
      simpa [mul_assoc] using hterm
    have hsquare :
        scorePairing model tangent outcome *
          scorePairing model tangent outcome = 0 :=
      (mul_eq_zero.mp hterm').resolve_left (ne_of_gt (hsupport outcome))
    exact mul_self_eq_zero.mp hsquare
  · intro hannihilates
    simp [fisherMetric, hannihilates]

/-- Identifiability means the score covectors separate tangent vectors. -/
def Identifiable (model : ScoreModel Outcome d) : Prop :=
  ∀ tangent : Fin d → ℝ,
    (∀ outcome, scorePairing model tangent outcome = 0) →
      tangent = 0

/-- Full support plus identifiability makes the Fisher metric positive
definite, rather than merely semidefinite. -/
theorem fisherMetric_pos (model : ScoreModel Outcome d)
    (hsupport : ∀ outcome, 0 < model.law outcome)
    (hidentifiable : Identifiable model) {tangent : Fin d → ℝ}
    (htangent : tangent ≠ 0) :
    0 < fisherMetric model tangent tangent := by
  have hnonneg := fisherMetric_nonneg model tangent
  have hne : fisherMetric model tangent tangent ≠ 0 := by
    intro hzero
    apply htangent
    exact hidentifiable tangent
      ((fisherMetric_eq_zero_iff model hsupport tangent).mp hzero)
  exact lt_of_le_of_ne hnonneg (Ne.symm hne)

/-- Pull back the Fisher metric along a Jacobian from `k` coordinates to the
model's `d` coordinates. -/
def pullbackMetric (model : ScoreModel Outcome d)
    (jacobian : Matrix (Fin d) (Fin k) ℝ)
    (left right : Fin k → ℝ) : ℝ :=
  fisherMetric model (jacobian.mulVec left) (jacobian.mulVec right)

/-- Pulling the Fisher metric back through a composite Jacobian agrees with
successive pullback. -/
theorem pullbackMetric_comp (model : ScoreModel Outcome d)
    (outer : Matrix (Fin d) (Fin k) ℝ)
    (inner : Matrix (Fin k) (Fin m) ℝ)
    (left right : Fin m → ℝ) :
    pullbackMetric model (outer * inner) left right =
      pullbackMetric model outer (inner.mulVec left) (inner.mulVec right) := by
  simp [pullbackMetric, Matrix.mulVec_mulVec]

/-- Every Fisher pullback remains positive semidefinite. -/
theorem pullbackMetric_nonneg (model : ScoreModel Outcome d)
    (jacobian : Matrix (Fin d) (Fin k) ℝ) (tangent : Fin k → ℝ) :
    0 ≤ pullbackMetric model jacobian tangent tangent :=
  fisherMetric_nonneg model (jacobian.mulVec tangent)

/-- An injective Jacobian preserves positive definiteness of an identifiable
full-support Fisher model. -/
theorem pullbackMetric_pos (model : ScoreModel Outcome d)
    (jacobian : Matrix (Fin d) (Fin k) ℝ)
    (hsupport : ∀ outcome, 0 < model.law outcome)
    (hidentifiable : Identifiable model)
    (hinjective : ∀ tangent : Fin k → ℝ,
      jacobian.mulVec tangent = 0 → tangent = 0)
    {tangent : Fin k → ℝ} (htangent : tangent ≠ 0) :
    0 < pullbackMetric model jacobian tangent tangent := by
  apply fisherMetric_pos model hsupport hidentifiable
  intro hzero
  exact htangent (hinjective tangent hzero)

/-- Fisher lowering of a tangent vector to a coordinate covector. -/
def lowerTangent (model : ScoreModel Outcome d)
    (tangent : Fin d → ℝ) : Fin d → ℝ :=
  fun coordinate => ∑ other,
    fisherMatrix model coordinate other * tangent other

/-- The expected-score definition of the Fisher metric agrees exactly with
pairing a tangent against the matrix-lowered second tangent. -/
theorem fisherMetric_eq_dot_lowerTangent (model : ScoreModel Outcome d)
    (left right : Fin d → ℝ) :
    fisherMetric model left right =
      ∑ coordinate, left coordinate * lowerTangent model right coordinate := by
  classical
  rw [fisherMetric_symm model left right]
  simp only [fisherMetric, scorePairing, lowerTangent, fisherMatrix]
  simp_rw [Finset.mul_sum, Finset.sum_mul]
  conv_lhs => rw [Finset.sum_comm]
  apply Finset.sum_congr rfl
  intro coordinate _
  conv_lhs => rw [Finset.sum_comm]
  apply Finset.sum_congr rfl
  intro other _
  conv_rhs => rw [Finset.mul_sum]
  apply Finset.sum_congr rfl
  intro outcome _
  ring

/-- The Fisher metric is additive in its first tangent argument. -/
theorem fisherMetric_add_left (model : ScoreModel Outcome d)
    (left extra right : Fin d → ℝ) :
    fisherMetric model (fun coordinate => left coordinate + extra coordinate)
        right =
      fisherMetric model left right + fisherMetric model extra right := by
  rw [fisherMetric_eq_dot_lowerTangent,
    fisherMetric_eq_dot_lowerTangent,
    fisherMetric_eq_dot_lowerTangent]
  simp only [add_mul, Finset.sum_add_distrib]

/-- The Fisher metric is homogeneous in its first tangent argument. -/
theorem fisherMetric_smul_left (model : ScoreModel Outcome d)
    (scale : ℝ) (left right : Fin d → ℝ) :
    fisherMetric model (fun coordinate => scale * left coordinate) right =
      scale * fisherMetric model left right := by
  rw [fisherMetric_eq_dot_lowerTangent,
    fisherMetric_eq_dot_lowerTangent, Finset.mul_sum]
  apply Finset.sum_congr rfl
  intro coordinate _
  ring

/-- The Fisher metric is additive in its second tangent argument. -/
theorem fisherMetric_add_right (model : ScoreModel Outcome d)
    (left right extra : Fin d → ℝ) :
    fisherMetric model left
        (fun coordinate => right coordinate + extra coordinate) =
      fisherMetric model left right + fisherMetric model left extra := by
  rw [fisherMetric_symm model left,
    fisherMetric_add_left,
    fisherMetric_symm model right left,
    fisherMetric_symm model extra left]

/-- The Fisher metric is homogeneous in its second tangent argument. -/
theorem fisherMetric_smul_right (model : ScoreModel Outcome d)
    (scale : ℝ) (left right : Fin d → ℝ) :
    fisherMetric model left (fun coordinate => scale * right coordinate) =
      scale * fisherMetric model left right := by
  rw [fisherMetric_symm model left,
    fisherMetric_smul_left,
    fisherMetric_symm model right left]

/-- A natural-gradient witness is precisely a tangent raised from the target
covector by the Fisher information matrix. -/
def IsNaturalGradient (model : ScoreModel Outcome d)
    (covector tangent : Fin d → ℝ) : Prop :=
  lowerTangent model tangent = covector

/-- Any declared natural-gradient witness recovers the target covector. -/
theorem naturalGradient_duality (model : ScoreModel Outcome d)
    (covector tangent : Fin d → ℝ)
    (h : IsNaturalGradient model covector tangent) :
    lowerTangent model tangent = covector := h

/-- Raise a covector with an invertible Fisher information matrix.  Unlike the
witness predicate above, this is an executable closed-form construction. -/
noncomputable def naturalGradient (model : ScoreModel Outcome d)
    [Invertible (fisherMatrix model)] (covector : Fin d → ℝ) : Fin d → ℝ :=
  (fisherMatrix model)⁻¹ *ᵥ covector

/-- Fisher inversion constructs a genuine natural-gradient solution. -/
theorem naturalGradient_isNaturalGradient (model : ScoreModel Outcome d)
    [Invertible (fisherMatrix model)] (covector : Fin d → ℝ) :
    IsNaturalGradient model covector (naturalGradient model covector) := by
  change
    fisherMatrix model *ᵥ ((fisherMatrix model)⁻¹ *ᵥ covector) = covector
  rw [Matrix.mulVec_mulVec, Matrix.mul_inv_of_invertible, Matrix.one_mulVec]

/-- The constructed natural gradient is metric-dual to its target covector. -/
theorem naturalGradient_metric_duality (model : ScoreModel Outcome d)
    [Invertible (fisherMatrix model)]
    (covector tangent : Fin d → ℝ) :
    fisherMetric model tangent (naturalGradient model covector) =
      ∑ coordinate, tangent coordinate * covector coordinate := by
  rw [fisherMetric_eq_dot_lowerTangent,
    naturalGradient_isNaturalGradient]

/-- The Fisher energy of the natural gradient equals its ordinary pairing
with the target covector. -/
theorem naturalGradient_energy_identity (model : ScoreModel Outcome d)
    [Invertible (fisherMatrix model)] (covector : Fin d → ℝ) :
    fisherMetric model (naturalGradient model covector)
        (naturalGradient model covector) =
      ∑ coordinate, naturalGradient model covector coordinate *
        covector coordinate :=
  naturalGradient_metric_duality model covector
    (naturalGradient model covector)

/-- When the Fisher matrix is invertible, the natural-gradient solution is
unique. -/
theorem naturalGradient_unique (model : ScoreModel Outcome d)
    [Invertible (fisherMatrix model)] (covector candidate : Fin d → ℝ)
    (h : IsNaturalGradient model covector candidate) :
    candidate = naturalGradient model covector := by
  change fisherMatrix model *ᵥ candidate = covector at h
  have hinverse := congrArg (fun value => (fisherMatrix model)⁻¹ *ᵥ value) h
  simpa only [naturalGradient, Matrix.mulVec_mulVec,
    Matrix.inv_mul_of_invertible, Matrix.one_mulVec] using hinverse

/-! ## Concrete Bernoulli specialization

The following construction realizes the abstract finite score carrier for the
one-parameter Bernoulli family.  It is intentionally restricted to an
interior parameter: the score and Fisher information are not asserted at the
singular boundary points `p = 0` or `p = 1`.
-/

/-- The normalized Bernoulli law at an interior parameter. -/
def bernoulliLaw (p : ℝ) (hp0 : 0 < p) (hp1 : p < 1) : FiniteLaw Bool where
  mass outcome := if outcome then p else 1 - p
  nonneg outcome := by
    cases outcome <;> simp [hp0.le, hp1.le]
  sum_one := by simp

/-- The centered one-coordinate Bernoulli score model. -/
noncomputable def bernoulliScoreModel (p : ℝ) (hp0 : 0 < p) (hp1 : p < 1) :
    ScoreModel Bool 1 where
  law := bernoulliLaw p hp0 hp1
  score outcome _ := if outcome then 1 / p else -(1 / (1 - p))
  centered coordinate := by
    have hp : p ≠ 0 := ne_of_gt hp0
    have h1p : 1 - p ≠ 0 := ne_of_gt (sub_pos.mpr hp1)
    simp [bernoulliLaw, hp, h1p]

/-- A fully concrete, nondegenerate score-model witness at `p = 1 / 2`. -/
noncomputable def fairBernoulliScoreModel : ScoreModel Bool 1 :=
  bernoulliScoreModel (1 / 2 : ℝ) (by norm_num) (by norm_num)

/-- The fair Bernoulli model has two nonzero, oppositely signed scores. -/
theorem fairBernoulliScoreModel_scores :
    fairBernoulliScoreModel.score false 0 = -2 ∧
      fairBernoulliScoreModel.score true 0 = 2 := by
  norm_num [fairBernoulliScoreModel, bernoulliScoreModel]

/-- Every Bernoulli outcome has positive mass at an interior parameter. -/
theorem bernoulliScoreModel_fullSupport (p : ℝ) (hp0 : 0 < p) (hp1 : p < 1)
    (outcome : Bool) :
    0 < (bernoulliScoreModel p hp0 hp1).law outcome := by
  cases outcome <;> simp [bernoulliScoreModel, bernoulliLaw, hp0, sub_pos.mpr hp1]

/-- The one-coordinate Bernoulli score separates tangent vectors in the
interior. -/
theorem bernoulliScoreModel_identifiable (p : ℝ) (hp0 : 0 < p)
    (hp1 : p < 1) :
    Identifiable (bernoulliScoreModel p hp0 hp1) := by
  intro tangent hannihilates
  have hp : p ≠ 0 := ne_of_gt hp0
  have htrue := hannihilates true
  have htangent : tangent 0 = 0 := by
    simpa [scorePairing, bernoulliScoreModel, hp] using htrue
  funext coordinate
  simpa [Fin.eq_zero coordinate] using htangent

/-- The abstract Fisher matrix contains the familiar Bernoulli information
`1 / (p * (1 - p))` as its unique entry. -/
theorem bernoulli_fisherMatrix_entry (p : ℝ) (hp0 : 0 < p) (hp1 : p < 1) :
    fisherMatrix (bernoulliScoreModel p hp0 hp1) 0 0 =
      1 / (p * (1 - p)) := by
  have hp : p ≠ 0 := ne_of_gt hp0
  have h1p : 1 - p ≠ 0 := ne_of_gt (sub_pos.mpr hp1)
  simp [fisherMatrix, bernoulliScoreModel, bernoulliLaw]
  field_simp [hp, h1p]
  ring

/-- At the explicit interior point `p = 1 / 2`, the Fisher matrix entry is
exactly `4`, matching the finite curve's minimum. -/
theorem fairBernoulli_fisherMatrix_entry :
    fisherMatrix fairBernoulliScoreModel 0 0 = 4 := by
  change fisherMatrix (bernoulliScoreModel (1 / 2 : ℝ) (by norm_num)
    (by norm_num)) 0 0 = 4
  rw [bernoulli_fisherMatrix_entry]
  norm_num

/-- The general finite-score metric specializes to the scalar Bernoulli
Fisher metric on one-coordinate tangents. -/
theorem bernoulli_fisherMetric_eq (p : ℝ) (hp0 : 0 < p) (hp1 : p < 1)
    (left right : Fin 1 → ℝ) :
    fisherMetric (bernoulliScoreModel p hp0 hp1) left right =
      (1 / (p * (1 - p))) * left 0 * right 0 := by
  rw [fisherMetric_eq_dot_lowerTangent]
  simp [lowerTangent, bernoulli_fisherMatrix_entry]
  ring

/-- The concrete Bernoulli Fisher metric is positive definite throughout the
open parameter interval. -/
theorem bernoulli_fisherMetric_pos (p : ℝ) (hp0 : 0 < p) (hp1 : p < 1)
    {tangent : Fin 1 → ℝ} (htangent : tangent ≠ 0) :
    0 < fisherMetric (bernoulliScoreModel p hp0 hp1) tangent tangent :=
  fisherMetric_pos (bernoulliScoreModel p hp0 hp1)
    (bernoulliScoreModel_fullSupport p hp0 hp1)
    (bernoulliScoreModel_identifiable p hp0 hp1) htangent

/-- The interior Bernoulli Fisher matrix is a unit. -/
theorem bernoulli_fisherMatrix_isUnit (p : ℝ) (hp0 : 0 < p) (hp1 : p < 1) :
    IsUnit (fisherMatrix (bernoulliScoreModel p hp0 hp1)) := by
  rw [Matrix.isUnit_iff_isUnit_det, Matrix.det_fin_one,
    bernoulli_fisherMatrix_entry]
  exact isUnit_iff_ne_zero.mpr (one_div_ne_zero (mul_ne_zero
    (ne_of_gt hp0) (ne_of_gt (sub_pos.mpr hp1))))

/-- Constructive invertibility for the interior Bernoulli Fisher matrix. -/
@[implicit_reducible]
noncomputable def bernoulliFisherInvertible (p : ℝ) (hp0 : 0 < p)
    (hp1 : p < 1) :
    Invertible (fisherMatrix (bernoulliScoreModel p hp0 hp1)) :=
  (bernoulli_fisherMatrix_isUnit p hp0 hp1).invertible

/-- In the multidimensional carrier, inverse-Fisher raising for the
one-coordinate Bernoulli family is multiplication by `p * (1 - p)`. -/
theorem bernoulli_naturalGradient_eq (p : ℝ) (hp0 : 0 < p) (hp1 : p < 1)
    (covector : Fin 1 → ℝ) :
    letI := bernoulliFisherInvertible p hp0 hp1
    naturalGradient (bernoulliScoreModel p hp0 hp1) covector =
      fun _ => p * (1 - p) * covector 0 := by
  let _ := bernoulliFisherInvertible p hp0 hp1
  symm
  apply naturalGradient_unique
  funext coordinate
  have hcoordinate : coordinate = 0 := Fin.eq_zero coordinate
  subst coordinate
  simp only [lowerTangent, Fin.sum_univ_one]
  rw [bernoulli_fisherMatrix_entry]
  have hp : p ≠ 0 := ne_of_gt hp0
  have h1p : 1 - p ≠ 0 := ne_of_gt (sub_pos.mpr hp1)
  field_simp [hp, h1p]

/-! ## Concrete rank-deficient specialization

Duplicating the same centered Bernoulli score in two parameter coordinates
produces a rank-one Fisher carrier.  This example makes the identifiability
hypothesis observable: the nonzero difference direction is invisible to every
score and has exactly zero Fisher norm.
-/

/-- Two-coordinate score model obtained by duplicating the fair-Bernoulli
score covector. -/
noncomputable def duplicatedFairBernoulliScoreModel : ScoreModel Bool 2 where
  law := fairBernoulliScoreModel.law
  score outcome _ := fairBernoulliScoreModel.score outcome 0
  centered _ := fairBernoulliScoreModel.centered 0

/-- Difference tangent between the two duplicated parameter coordinates. -/
def duplicatedScoreNullTangent : Fin 2 → ℝ :=
  fun coordinate => if coordinate = 0 then 1 else -1

/-- Every entry of the duplicated-score Fisher matrix is `4`, so its two
columns coincide. -/
theorem duplicatedFairBernoulli_fisherMatrix_entry (i j : Fin 2) :
    fisherMatrix duplicatedFairBernoulliScoreModel i j = 4 := by
  norm_num [fisherMatrix, duplicatedFairBernoulliScoreModel,
    fairBernoulliScoreModel, bernoulliScoreModel, bernoulliLaw]

/-- The duplicate-coordinate difference direction is genuinely nonzero. -/
theorem duplicatedScoreNullTangent_ne_zero :
    duplicatedScoreNullTangent ≠ 0 := by
  intro hzero
  have hatZero := congrFun hzero (0 : Fin 2)
  norm_num [duplicatedScoreNullTangent] at hatZero

/-- The duplicate-coordinate difference direction is annihilated by every
score covector. -/
theorem duplicatedScoreNullTangent_pairing_zero (outcome : Bool) :
    scorePairing duplicatedFairBernoulliScoreModel
      duplicatedScoreNullTangent outcome = 0 := by
  simp [scorePairing, duplicatedFairBernoulliScoreModel,
    duplicatedScoreNullTangent, Fin.sum_univ_two]

/-- A concrete nonzero tangent has zero Fisher norm in the rank-deficient
model. -/
theorem duplicatedScore_fisherMetric_eq_zero :
    fisherMetric duplicatedFairBernoulliScoreModel
      duplicatedScoreNullTangent duplicatedScoreNullTangent = 0 := by
  apply (fisherMetric_eq_zero_iff duplicatedFairBernoulliScoreModel
    (bernoulliScoreModel_fullSupport (1 / 2 : ℝ) (by norm_num) (by norm_num))
    duplicatedScoreNullTangent).2
  exact duplicatedScoreNullTangent_pairing_zero

/-- The duplicated score family fails the identifiability premise required for
positive-definite Fisher geometry. -/
theorem duplicatedFairBernoulli_not_identifiable :
    ¬Identifiable duplicatedFairBernoulliScoreModel := by
  intro hidentifiable
  exact duplicatedScoreNullTangent_ne_zero
    (hidentifiable duplicatedScoreNullTangent
      duplicatedScoreNullTangent_pairing_zero)

end FEP.InformationGeometry
