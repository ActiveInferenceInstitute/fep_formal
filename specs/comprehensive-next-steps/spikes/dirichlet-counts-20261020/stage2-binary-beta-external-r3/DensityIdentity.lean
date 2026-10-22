/- External candidate under frozen contract61ce. Uncompiled; no maintained acceptance. -/
import Mathlib.Probability.Distributions.Beta
import Mathlib.Tactic

open MeasureTheory
open scoped ENNReal

namespace FEP95BinaryBetaProbe

noncomputable def likelihood (s f : ℕ) (x : ℝ) : ENNReal :=
  ENNReal.ofReal x ^ s * ENNReal.ofReal (1 - x) ^ f

noncomputable def normalizer (a b : ℝ) (s f : ℕ) : ℝ :=
  ProbabilityTheory.beta (a + (s : ℝ)) (b + (f : ℝ)) / ProbabilityTheory.beta a b

theorem normalizer_pos {a b : ℝ} (ha : 0 < a) (hb : 0 < b) (s f : ℕ) :
    0 < normalizer a b s f := by
  exact div_pos (ProbabilityTheory.beta_pos (by positivity) (by positivity))
    (ProbabilityTheory.beta_pos ha hb)

theorem normalizer_finite (a b : ℝ) (s f : ℕ) :
    ENNReal.ofReal (normalizer a b s f) ≠ ⊤ := ENNReal.ofReal_ne_top

theorem likelihood_measurable (s f : ℕ) : Measurable (likelihood s f) := by
  unfold likelihood
  fun_prop

theorem real_pdf_product {a b : ℝ} (ha : 0 < a) (hb : 0 < b)
    (s f : ℕ) (x : ℝ) :
    ProbabilityTheory.betaPDFReal a b x * (x ^ s * (1 - x) ^ f) =
      normalizer a b s f * ProbabilityTheory.betaPDFReal (a + (s : ℝ)) (b + (f : ℝ)) x := by
  by_cases hx : 0 < x ∧ x < 1
  · have hx1 : 0 < 1 - x := sub_pos.mpr hx.2
    have hbase : ProbabilityTheory.beta a b ≠ 0 := ne_of_gt (ProbabilityTheory.beta_pos ha hb)
    have hpost : ProbabilityTheory.beta (a + (s : ℝ)) (b + (f : ℝ)) ≠ 0 :=
      ne_of_gt (ProbabilityTheory.beta_pos (by positivity) (by positivity))
    simp only [ProbabilityTheory.betaPDFReal, ite_eq_left hx, normalizer]
    rw [show a + (s : ℝ) - 1 = (a - 1) + (s : ℝ) by ring,
      show b + (f : ℝ) - 1 = (b - 1) + (f : ℝ) by ring,
      Real.rpow_add_natCast (ne_of_gt hx.1), Real.rpow_add_natCast (ne_of_gt hx1)]
    field_simp
  · simp [ProbabilityTheory.betaPDFReal, hx]

theorem pdf_product {a b : ℝ} (ha : 0 < a) (hb : 0 < b)
    (s f : ℕ) (x : ℝ) :
    ProbabilityTheory.betaPDF a b x * likelihood s f x =
      ENNReal.ofReal (normalizer a b s f) *
        ProbabilityTheory.betaPDF (a + (s : ℝ)) (b + (f : ℝ)) x := by
  by_cases hx : 0 < x ∧ x < 1
  · have hp : 0 ≤ ProbabilityTheory.betaPDFReal a b x :=
      (ProbabilityTheory.betaPDFReal_pos hx.1 hx.2 ha hb).le
    have hx0 : 0 ≤ x := hx.1.le
    have hx1 : 0 ≤ 1 - x := (sub_pos.mpr hx.2).le
    calc
      ProbabilityTheory.betaPDF a b x * likelihood s f x =
          ENNReal.ofReal (ProbabilityTheory.betaPDFReal a b x * (x ^ s * (1 - x) ^ f)) := by
        rw [ENNReal.ofReal_mul hp, ENNReal.ofReal_mul (pow_nonneg hx0 s),
          ENNReal.ofReal_pow hx0, ENNReal.ofReal_pow hx1]
        rfl
      _ = ENNReal.ofReal (normalizer a b s f *
          ProbabilityTheory.betaPDFReal (a + (s : ℝ)) (b + (f : ℝ)) x) :=
        congrArg ENNReal.ofReal (real_pdf_product ha hb s f x)
      _ = _ := by
        rw [ENNReal.ofReal_mul (normalizer_pos ha hb s f).le]
        rfl
  · simp [ProbabilityTheory.betaPDF, ProbabilityTheory.betaPDFReal, hx]

theorem weighted_measure {a b : ℝ} (ha : 0 < a) (hb : 0 < b) (s f : ℕ) :
    (ProbabilityTheory.betaMeasure a b).withDensity (likelihood s f) =
      ENNReal.ofReal (normalizer a b s f) •
        ProbabilityTheory.betaMeasure (a + (s : ℝ)) (b + (f : ℝ)) := by
  have hprior : Measurable (ProbabilityTheory.betaPDF a b) := by
    unfold ProbabilityTheory.betaPDF
    fun_prop
  have hpost : Measurable (ProbabilityTheory.betaPDF (a + (s : ℝ)) (b + (f : ℝ))) := by
    unfold ProbabilityTheory.betaPDF
    fun_prop
  unfold ProbabilityTheory.betaMeasure
  rw [← MeasureTheory.withDensity_mul volume hprior (likelihood_measurable s f),
    ← MeasureTheory.withDensity_smul _ hpost]
  apply MeasureTheory.withDensity_congr_ae
  exact Filter.Eventually.of_forall fun x => pdf_product ha hb s f x

theorem weighted_mass {a b : ℝ} (ha : 0 < a) (hb : 0 < b) (s f : ℕ) :
    ((ProbabilityTheory.betaMeasure a b).withDensity (likelihood s f)) Set.univ =
      ENNReal.ofReal (normalizer a b s f) := by
  let := ProbabilityTheory.isProbabilityMeasureBeta
    (show 0 < a + (s : ℝ) by positivity) (show 0 < b + (f : ℝ) by positivity)
  rw [weighted_measure ha hb s f]
  simp

theorem normalized_posterior {a b : ℝ} (ha : 0 < a) (hb : 0 < b) (s f : ℕ) :
    (ENNReal.ofReal (normalizer a b s f))⁻¹ •
      (ProbabilityTheory.betaMeasure a b).withDensity (likelihood s f) =
        ProbabilityTheory.betaMeasure (a + (s : ℝ)) (b + (f : ℝ)) := by
  rw [weighted_measure ha hb s f, smul_smul,
    ENNReal.inv_mul_cancel (ne_of_gt (ENNReal.ofReal_pos.mpr (normalizer_pos ha hb s f)))
      (normalizer_finite a b s f), one_smul]

theorem normalized_probability {a b : ℝ} (ha : 0 < a) (hb : 0 < b) (s f : ℕ) :
    IsProbabilityMeasure ((ENNReal.ofReal (normalizer a b s f))⁻¹ •
      (ProbabilityTheory.betaMeasure a b).withDensity (likelihood s f)) := by
  rw [normalized_posterior ha hb s f]
  exact ProbabilityTheory.isProbabilityMeasureBeta (by positivity) (by positivity)

theorem zero_counts {a b : ℝ} (ha : 0 < a) (hb : 0 < b) :
    normalizer a b 0 0 = 1 := by
  simp [normalizer, ne_of_gt (ProbabilityTheory.beta_pos ha hb)]

theorem noninteger_prior_recovery : normalizer (1 / 2) (3 / 2) 0 0 = 1 :=
  zero_counts (by norm_num) (by norm_num)

theorem noninteger_measure_recovery :
    (ProbabilityTheory.betaMeasure (1 / 2) (3 / 2)).withDensity (likelihood 0 0) =
      ProbabilityTheory.betaMeasure (1 / 2) (3 / 2) := by
  have ha : (0 : ℝ) < 1 / 2 := by norm_num
  have hb : (0 : ℝ) < 3 / 2 := by norm_num
  have h := weighted_measure ha hb 0 0
  rw [zero_counts ha hb, ENNReal.ofReal_one, one_smul] at h
  simpa using h

private theorem gamma_two : Real.Gamma 2 = 1 := by
  norm_num

private theorem gamma_three : Real.Gamma 3 = 2 := by
  norm_num

private theorem gamma_four : Real.Gamma 4 = 6 := by
  norm_num

theorem uniform_success_normalizer : normalizer 1 1 1 0 = 1 / 2 := by
  norm_num [normalizer, ProbabilityTheory.beta, Real.Gamma_one, gamma_two, gamma_three]

theorem uniform_failure_normalizer : normalizer 1 1 0 1 = 1 / 2 := by
  norm_num [normalizer, ProbabilityTheory.beta, Real.Gamma_one, gamma_two, gamma_three]

theorem uniform_success_posterior :
    (ENNReal.ofReal (1 / 2 : ℝ))⁻¹ •
      (ProbabilityTheory.betaMeasure 1 1).withDensity (likelihood 1 0) =
        ProbabilityTheory.betaMeasure 2 1 := by
  simpa only [Nat.cast_one, Nat.cast_zero, add_zero, show (1 : ℝ) + 1 = 2 by norm_num, uniform_success_normalizer] using
    normalized_posterior (by norm_num : (0 : ℝ) < 1) (by norm_num : (0 : ℝ) < 1) 1 0

theorem uniform_failure_posterior :
    (ENNReal.ofReal (1 / 2 : ℝ))⁻¹ •
      (ProbabilityTheory.betaMeasure 1 1).withDensity (likelihood 0 1) =
        ProbabilityTheory.betaMeasure 1 2 := by
  simpa only [Nat.cast_one, Nat.cast_zero, add_zero, show (1 : ℝ) + 1 = 2 by norm_num, uniform_failure_normalizer] using
    normalized_posterior (by norm_num : (0 : ℝ) < 1) (by norm_num : (0 : ℝ) < 1) 0 1

theorem distinct_posteriors : ProbabilityTheory.betaMeasure 2 1 ≠ ProbabilityTheory.betaMeasure 1 2 := by
  intro h
  have hm := congrArg (fun μ : Measure ℝ => (μ.withDensity (likelihood 1 0)) Set.univ) h
  rw [weighted_mass (by norm_num : (0 : ℝ) < 2) (by norm_num : (0 : ℝ) < 1) 1 0,
    weighted_mass (by norm_num : (0 : ℝ) < 1) (by norm_num : (0 : ℝ) < 2) 1 0] at hm
  have hr := congrArg ENNReal.toReal hm
  norm_num [normalizer, ProbabilityTheory.beta, Real.Gamma_one, gamma_two, gamma_three,
    gamma_four] at hr

theorem wrong_inverse_ratio : ENNReal.ofReal (normalizer 1 1 1 0) ≠ ENNReal.ofReal (2 : ℝ) := by
  rw [uniform_success_normalizer]
  norm_num

theorem wrong_scaled_measure_refused :
    (ProbabilityTheory.betaMeasure 1 1).withDensity (likelihood 1 0) ≠
      ENNReal.ofReal (2 : ℝ) • ProbabilityTheory.betaMeasure 2 1 := by
  intro h
  let := ProbabilityTheory.isProbabilityMeasureBeta (by norm_num : (0 : ℝ) < 2)
    (by norm_num : (0 : ℝ) < 1)
  have hm := congrArg (fun μ : Measure ℝ => μ Set.univ) h
  rw [weighted_mass (by norm_num : (0 : ℝ) < 1) (by norm_num : (0 : ℝ) < 1) 1 0] at hm
  have hr := congrArg ENNReal.toReal hm
  norm_num [uniform_success_normalizer] at hr

theorem nonpositive_shape_refused : ¬ (0 < (0 : ℝ)) ∧ ¬ (0 < (-1 : ℝ)) := by norm_num

theorem outside_pdf_zero (a b x : ℝ) (hx : x ≤ 0 ∨ 1 ≤ x) :
    ProbabilityTheory.betaPDF a b x = 0 := by
  rcases hx with h | h
  · exact ProbabilityTheory.betaPDF_eq_zero_of_nonpos h
  · exact ProbabilityTheory.betaPDF_eq_zero_of_one_le h

#print axioms normalizer_pos
#print axioms normalizer_finite
#print axioms likelihood_measurable
#print axioms real_pdf_product
#print axioms pdf_product
#print axioms weighted_measure
#print axioms weighted_mass
#print axioms normalized_posterior
#print axioms normalized_probability
#print axioms zero_counts
#print axioms noninteger_prior_recovery
#print axioms noninteger_measure_recovery
#print axioms uniform_success_normalizer
#print axioms uniform_failure_normalizer
#print axioms uniform_success_posterior
#print axioms uniform_failure_posterior
#print axioms distinct_posteriors
#print axioms wrong_inverse_ratio
#print axioms wrong_scaled_measure_refused
#print axioms nonpositive_shape_refused
#print axioms outside_pdf_zero
end FEP95BinaryBetaProbe
