import Mathlib.Algebra.BigOperators.Field
import Mathlib.Tactic

/-!
Bounded algebraic seams for source-bound numerical witnesses. These laws do
not formalize a GNN parser, floating-point runner, matrix-valued Gaussian
conditioning, or an execution receipt. The scalar update uses its supplied
prior directly; prediction/dynamics are deliberately separate.
-/

namespace FEPSemanticWitness

open scoped BigOperators

noncomputable section

theorem normalized_sum {S : Type*} [Fintype S] (weights : S → ℝ)
    (hMass : (∑ state, weights state) ≠ 0) :
    ∑ state, weights state / (∑ item, weights item) = 1 := by
  rw [← Finset.sum_div]
  exact div_self hMass

theorem normalized_reconstruction {S : Type*} [Fintype S]
    (weights : S → ℝ) (hMass : (∑ state, weights state) ≠ 0) (state : S) :
    weights state / (∑ item, weights item) * (∑ item, weights item) =
      weights state := by
  exact div_mul_cancel₀ _ hMass

theorem normalized_nonneg {S : Type*} [Fintype S] (weights : S → ℝ)
    (hWeights : ∀ state, 0 ≤ weights state)
    (hMass : 0 < ∑ state, weights state) (state : S) :
    0 ≤ weights state / (∑ item, weights item) :=
  div_nonneg (hWeights state) hMass.le

def innovation (priorVariance observationSlope observationVariance : ℝ) : ℝ :=
  observationSlope ^ 2 * priorVariance + observationVariance

def gain (priorVariance observationSlope observationVariance : ℝ) : ℝ :=
  priorVariance * observationSlope /
    innovation priorVariance observationSlope observationVariance

def measurementMean (priorMean priorVariance observationSlope
    observationVariance observation : ℝ) : ℝ :=
  priorMean + gain priorVariance observationSlope observationVariance *
    (observation - observationSlope * priorMean)

def schurVariance (priorVariance observationSlope observationVariance : ℝ) : ℝ :=
  priorVariance - gain priorVariance observationSlope observationVariance *
    observationSlope * priorVariance

def josephVariance (priorVariance observationSlope observationVariance : ℝ) : ℝ :=
  (1 - gain priorVariance observationSlope observationVariance * observationSlope) ^ 2 *
      priorVariance +
    gain priorVariance observationSlope observationVariance ^ 2 * observationVariance

theorem innovation_pos (P H R : ℝ) (hP : 0 < P) (hR : 0 < R) :
    0 < innovation P H R := by
  exact add_pos_of_nonneg_of_pos (mul_nonneg (sq_nonneg H) hP.le) hR

theorem joseph_eq_schur (P H R : ℝ) (hS : innovation P H R ≠ 0) :
    josephVariance P H R = schurVariance P H R := by
  unfold josephVariance schurVariance gain innovation at *
  have hS' : P * H ^ 2 + R ≠ 0 := by simpa only [mul_comm] using hS
  field_simp [hS']
  ; ring

theorem schur_eq_product (P H R : ℝ) (hS : innovation P H R ≠ 0) :
    schurVariance P H R = P * R / innovation P H R := by
  unfold schurVariance gain innovation at *
  have hS' : P * H ^ 2 + R ≠ 0 := by simpa only [mul_comm] using hS
  field_simp [hS']
  ; ring

theorem posterior_variance_pos (P H R : ℝ) (hP : 0 < P) (hR : 0 < R) :
    0 < schurVariance P H R := by
  rw [schur_eq_product P H R (ne_of_gt (innovation_pos P H R hP hR))]
  exact div_pos (mul_pos hP hR) (innovation_pos P H R hP hR)

theorem measurement_prior_identity (m P H R y : ℝ)
    (hS : innovation P H R ≠ 0) :
    measurementMean m P H R y = (m * R + P * H * y) / innovation P H R := by
  unfold measurementMean gain innovation at *
  have hS' : P * H ^ 2 + R ≠ 0 := by simpa only [mul_comm] using hS
  field_simp [hS']
  ; ring

example : measurementMean 2 3 2 5 7 = 52 / 17 := by
  norm_num [measurementMean, gain, innovation]

example : josephVariance 3 2 5 = 15 / 17 := by
  norm_num [josephVariance, gain, innovation]

#print axioms normalized_sum
#print axioms normalized_reconstruction
#print axioms normalized_nonneg
#print axioms joseph_eq_schur
#print axioms schur_eq_product
#print axioms posterior_variance_pos
#print axioms measurement_prior_identity

end

end FEPSemanticWitness
