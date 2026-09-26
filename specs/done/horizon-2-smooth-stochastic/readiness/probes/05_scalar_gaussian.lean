import Mathlib.InformationTheory.KullbackLeibler.Basic
import Mathlib.Probability.Distributions.Gaussian.Real
import Mathlib.Probability.Kernel.Basic

open MeasureTheory ProbabilityTheory
open scoped ENNReal MeasureTheory ProbabilityTheory

private lemma gaussianPDFReal_unitShift_ratio (x : Real) :
    gaussianPDFReal 1 1 x / gaussianPDFReal 0 1 x =
      Real.exp (x - (1 : Real) / 2) := by
  rw [gaussianPDFReal_def, gaussianPDFReal_def]
  norm_num
  have hnormalizer :
      (Real.sqrt Real.pi)⁻¹ * (Real.sqrt 2)⁻¹ ≠ 0 := by
    positivity
  rw [mul_div_mul_left _ _ hnormalizer]
  rw [← Real.exp_sub]
  congr 1
  ring

private lemma gaussianReal_unitShift_llr :
    llr (gaussianReal 1 1) (gaussianReal 0 1) =ᵐ[gaussianReal 1 1]
      fun x => x - (1 : Real) / 2 := by
  have hsourceVolume : gaussianReal 1 1 ≪ volume := by
    exact gaussianReal_absolutelyContinuous 1 (by norm_num)
  have hreferenceVolume : gaussianReal 0 1 ≪ volume := by
    exact gaussianReal_absolutelyContinuous 0 (by norm_num)
  have hsourceReference : gaussianReal 1 1 ≪ gaussianReal 0 1 := by
    exact hsourceVolume.trans (gaussianReal_absolutelyContinuous' 0 (by norm_num))
  filter_upwards
    [hsourceReference
      (Measure.rnDeriv_eq_div hsourceVolume hreferenceVolume),
    hsourceVolume (rnDeriv_gaussianReal 1 1),
    hsourceVolume (rnDeriv_gaussianReal 0 1)] with x hratio hsource hreference
  rw [llr, hratio, hsource, hreference, ENNReal.toReal_div,
    toReal_gaussianPDF, toReal_gaussianPDF,
    gaussianPDFReal_unitShift_ratio, Real.log_exp]

private lemma gaussianReal_unitShift_llr_integrable :
    Integrable
      (llr (gaussianReal 1 1) (gaussianReal 0 1))
      (gaussianReal 1 1) := by
  rw [integrable_congr gaussianReal_unitShift_llr]
  have hid : Integrable id (gaussianReal 1 1) :=
    (memLp_id_gaussianReal (μ := 1) (v := 1) 1).integrable le_rfl
  exact
    (hid.sub (integrable_const ((1 : Real) / 2))).congr
      (ae_of_all _ fun _ => rfl)

-- H2-READINESS-ROW: scalar_gaussian_density_ac
example (mean1 mean2 : Real) {variance1 variance2 : NNReal}
    (hvariance1 : variance1 ≠ 0) (hvariance2 : variance2 ≠ 0) :
    gaussianReal mean1 variance1 =
        volume.withDensity (gaussianPDF mean1 variance1) ∧
      (∫⁻ x, gaussianPDF mean1 variance1 x) = 1 ∧
      gaussianReal mean1 variance1 ≪ volume ∧
      volume ≪ gaussianReal mean1 variance1 ∧
      (gaussianReal mean1 variance1).rnDeriv volume =ᵐ[volume]
        gaussianPDF mean1 variance1 ∧
      gaussianReal mean1 variance1 ≪ gaussianReal mean2 variance2 := by
  exact
    ⟨gaussianReal_of_var_ne_zero mean1 hvariance1,
      lintegral_gaussianPDF_eq_one mean1 hvariance1,
      gaussianReal_absolutelyContinuous mean1 hvariance1,
      gaussianReal_absolutelyContinuous' mean1 hvariance1,
      rnDeriv_gaussianReal mean1 variance1,
      (gaussianReal_absolutelyContinuous mean1 hvariance1).trans
        (gaussianReal_absolutelyContinuous' mean2 hvariance2)⟩

-- H2-READINESS-ROW: scalar_gaussian_moments_ext
example (mean1 mean2 : Real) (variance1 variance2 : NNReal) :
    ((∫ x, x ∂gaussianReal mean1 variance1) = mean1) ∧
      (Var[id; gaussianReal mean1 variance1] = variance1) ∧
      (gaussianReal mean1 variance1 = gaussianReal mean2 variance2 ↔
        mean1 = mean2 ∧ variance1 = variance2) := by
  exact
    And.intro integral_id_gaussianReal
      (And.intro variance_id_gaussianReal gaussianReal_ext_iff)

-- H2-READINESS-ROW: scalar_gaussian_parameter_measurability
example (mean : Real -> Real) (variance : Real -> NNReal)
    (hmean : Measurable mean) (hvariance : Measurable variance) :
    ∃ kernel : Kernel Real Real,
      IsMarkovKernel kernel ∧
        ∀ state, kernel state = gaussianReal (mean state) (variance state) := by
  let kernel : Kernel Real Real :=
    { toFun := fun state => gaussianReal (mean state) (variance state)
      measurable' :=
        measurable_gaussianReal.comp (hmean.prodMk hvariance) }
  have hmarkov : IsMarkovKernel kernel :=
    ⟨fun state => by
      change IsProbabilityMeasure (gaussianReal (mean state) (variance state))
      infer_instance⟩
  exact ⟨kernel, hmarkov, fun _ => rfl⟩

-- H2-READINESS-ROW: scalar_gaussian_affine_convolution
example (mean1 mean2 c shift : Real) (variance1 variance2 : NNReal) :
    (gaussianReal mean1 variance1).map (fun x => c * x + shift) =
        gaussianReal
          (c * mean1 + shift)
          (NNReal.mk (c ^ 2) (sq_nonneg c) * variance1) ∧
      (gaussianReal mean1 variance1).map (fun x => c * x) =
        gaussianReal (c * mean1) (NNReal.mk (c ^ 2) (sq_nonneg c) * variance1) ∧
      (gaussianReal mean1 variance1).map (fun x => x + shift) =
        gaussianReal (mean1 + shift) variance1 ∧
      gaussianReal mean1 variance1 ∗ gaussianReal mean2 variance2 =
        gaussianReal (mean1 + mean2) (variance1 + variance2) := by
  have haffine :
      (gaussianReal mean1 variance1).map (fun x => c * x + shift) =
        gaussianReal
          (c * mean1 + shift)
          (NNReal.mk (c ^ 2) (sq_nonneg c) * variance1) := by
    rw [show (fun x : Real => c * x + shift) =
      (fun x => x + shift) ∘ (fun x => c * x) by rfl]
    rw [← Measure.map_map (by fun_prop) (by fun_prop),
      gaussianReal_map_const_mul, gaussianReal_map_add_const]
  exact
    ⟨haffine, gaussianReal_map_const_mul c,
      gaussianReal_map_add_const shift, gaussianReal_conv_gaussianReal⟩

-- H2-READINESS-ROW: scalar_gaussian_native_kl
example :
    InformationTheory.klDiv
        (gaussianReal 1 1) (gaussianReal 0 1) =
          ENNReal.ofReal ((1 : Real) / 2) ∧
      Integrable
        (llr (gaussianReal 1 1) (gaussianReal 0 1))
        (gaussianReal 1 1) ∧
      InformationTheory.klDiv
        (gaussianReal 1 1) (gaussianReal 0 1) ≠ ∞ := by
  have hac : gaussianReal 1 1 ≪ gaussianReal 0 1 :=
    (gaussianReal_absolutelyContinuous 1 (by norm_num)).trans
      (gaussianReal_absolutelyContinuous' 0 (by norm_num))
  have hintegrable := gaussianReal_unitShift_llr_integrable
  have hformula :
      InformationTheory.klDiv
          (gaussianReal 1 1) (gaussianReal 0 1) =
        ENNReal.ofReal ((1 : Real) / 2) := by
    rw [InformationTheory.klDiv_of_ac_of_integrable hac hintegrable]
    congr 1
    rw [integral_congr_ae gaussianReal_unitShift_llr]
    have hid : Integrable id (gaussianReal 1 1) :=
      (memLp_id_gaussianReal (μ := 1) (v := 1) 1).integrable le_rfl
    change
      (∫ x, id x - (1 : Real) / 2 ∂gaussianReal 1 1) +
          (gaussianReal 0 1).real Set.univ -
          (gaussianReal 1 1).real Set.univ =
        (1 : Real) / 2
    rw [integral_sub hid (integrable_const ((1 : Real) / 2))]
    simp [integral_id_gaussianReal]
    norm_num
  exact
    ⟨hformula, hintegrable,
      InformationTheory.klDiv_ne_top hac hintegrable⟩
