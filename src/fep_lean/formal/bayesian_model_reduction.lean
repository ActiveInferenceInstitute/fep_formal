import FepSketches.variational_duality
import FepSketches.gaussian_information_geometry

/-!
# Bayesian model reduction

Conjugate, evidence-weighted reduction of a normalized finite model to a
nested sub-model.  A reduction carrier is a pointwise `0 ≤ weight ≤ 1`
evidence weighting; the reduced model renormalizes the weighted joint
prior-kernel mass, the reduced posterior keeps the multiplicative Bayes
form, and the reduced free energy is the negative log of the masked
evidence.  This module proves, with no new axioms and no unproved placeholders:

* the masked evidence never exceeds the full evidence, so the reduced
  free energy is weakly monotone in the reduction;
* the reduced posterior obeys the multiplicative odds law, and the odds
  factor is exactly the evidence weighting applied to the prior odds;
* the reduced posterior reconstructs the full posterior through the
  evidence ratio, mirroring `FiniteKernel.posterior_mul_predictive`;
* the same free-energy monotonicity holds for any supplied
  `VariationalDuality.GibbsCertificate`, via the Donsker--Varadhan gap;
* the Gaussian log Bayes factor in the pinned natural chart is the
  natural coordinate times the datum minus the natural log partition.
-/

namespace FEP.BayesianModelReduction

open FEP FEP.FiniteInformation FEP.VariationalDuality Finset
open scoped BigOperators

variable {Parameter Evidence : Type*} [Fintype Parameter] [Fintype Evidence]

noncomputable section

/-! ## Conjugate masked evidence -/

/-- Masked evidence for a reduction carrier: the joint prior-kernel mass
reweighted by the evidence weighting and summed at the observed datum.  The
weighting `0 ≤ weight ≤ 1` restricts the full model to a nested sub-model. -/
def maskedEvidence (prior : FiniteLaw Parameter) (weight : Parameter → ℝ)
    (kernel : FiniteKernel Parameter Evidence) (data : Evidence) : ℝ :=
  ∑ x, weight x * prior x * kernel x data

/-- Free energy of an evidence mass: the negative logarithm of the
evidence.  Smaller evidence (a strictly nested model) carries strictly more
free energy. -/
def evidenceFreeEnergy (e : ℝ) : ℝ := -Real.log e

/-- The reduced prior renormalizes the evidence-weighted prior mass.  It is
the exact Bayesian reduction of `prior` to the evidence-weighted sub-model. -/
def maskedPrior (prior : FiniteLaw Parameter) (weight : Parameter → ℝ)
    (hw : ∀ x, 0 ≤ weight x) (hZ : 0 < ∑ x, weight x * prior x) :
    FiniteLaw Parameter where
  mass x := weight x * prior x / ∑ y, weight y * prior y
  nonneg x := div_nonneg (mul_nonneg (hw x) (prior.nonneg x)) hZ.le
  sum_one := by
    rw [← Finset.sum_div]
    exact div_self hZ.ne'

/-! ## Masked evidence against the full evidence -/

/-- Masked evidence never exceeds the full evidence: the discarded residual
mass `(1 - weight x) * prior x * kernel x data` is nonnegative. -/
theorem maskedEvidence_le_predictive (prior : FiniteLaw Parameter)
    (weight : Parameter → ℝ) (kernel : FiniteKernel Parameter Evidence)
    (data : Evidence) (hw1 : ∀ x, weight x ≤ 1) :
    maskedEvidence prior weight kernel data ≤ kernel.predictive prior data := by
  have hsplit : ∑ x, prior x * kernel x data =
      ∑ x, weight x * prior x * kernel x data +
        ∑ x, (1 - weight x) * prior x * kernel x data := by
    rw [← Finset.sum_add_distrib]
    exact Finset.sum_congr rfl fun x _ => by ring
  rw [maskedEvidence, FiniteKernel.predictive_mass]
  calc
    ∑ x, weight x * prior x * kernel x data
        ≤ ∑ x, weight x * prior x * kernel x data +
            ∑ x, (1 - weight x) * prior x * kernel x data :=
      le_add_of_nonneg_right
        (Finset.sum_nonneg fun x _ =>
          mul_nonneg (mul_nonneg (sub_nonneg.2 (hw1 x)) (prior.nonneg x))
            (kernel.nonneg x data))
    _ = ∑ x, prior x * kernel x data := by rw [hsplit]

/-- The reduced predictive mass is the masked evidence divided by the
weighted prior mass. -/
theorem maskedPrior_predictive_eq (prior : FiniteLaw Parameter)
    (weight : Parameter → ℝ) (kernel : FiniteKernel Parameter Evidence)
    (data : Evidence) (hw : ∀ x, 0 ≤ weight x)
    (hZ : 0 < ∑ x, weight x * prior x) :
    kernel.predictive (maskedPrior prior weight hw hZ) data =
      maskedEvidence prior weight kernel data / ∑ y, weight y * prior y := by
  rw [FiniteKernel.predictive_mass, maskedEvidence]
  simp only [maskedPrior]
  simp_rw [div_mul_eq_mul_div]
  rw [← Finset.sum_div]

/-! ## Multiplicative posterior odds -/

/-- The reduced posterior keeps the multiplicative Bayes form: posterior
mass times masked evidence equals the weighted joint mass. -/
theorem reduction_posterior_reconstruction (prior : FiniteLaw Parameter)
    (weight : Parameter → ℝ) (kernel : FiniteKernel Parameter Evidence)
    (data : Evidence) (hw : ∀ x, 0 ≤ weight x)
    (hZ : 0 < ∑ x, weight x * prior x)
    (hy : 0 < kernel.predictive (maskedPrior prior weight hw hZ) data)
    (x : Parameter) :
    FiniteKernel.posterior (maskedPrior prior weight hw hZ) kernel data hy x *
        maskedEvidence prior weight kernel data =
      weight x * prior x * kernel x data := by
  have hmul := FiniteKernel.posterior_mul_predictive
    (maskedPrior prior weight hw hZ) kernel data hy x
  rw [maskedPrior_predictive_eq prior weight kernel data hw hZ] at hmul
  simp only [maskedPrior] at hmul
  field_simp [hZ.ne'] at hmul
  exact hmul

/-- Reduction odds: the reduced posterior odds at two states are the
evidence-weighted prior odds, the exact multiplicative form of the Bayes
factor reduction. -/
theorem reduction_posterior_odds (prior : FiniteLaw Parameter)
    (weight : Parameter → ℝ) (kernel : FiniteKernel Parameter Evidence)
    (data : Evidence) (hw : ∀ x, 0 ≤ weight x)
    (hZ : 0 < ∑ x, weight x * prior x)
    (hy : 0 < kernel.predictive (maskedPrior prior weight hw hZ) data)
    (x y : Parameter) :
    FiniteKernel.posterior (maskedPrior prior weight hw hZ) kernel data hy x *
        (weight y * prior y * kernel y data) =
      FiniteKernel.posterior (maskedPrior prior weight hw hZ) kernel data hy y *
        (weight x * prior x * kernel x data) := by
  rw [← reduction_posterior_reconstruction prior weight kernel data hw hZ hy y,
    ← reduction_posterior_reconstruction prior weight kernel data hw hZ hy x]
  ring
/-- The reduced posterior reconstructs the full posterior through the
evidence ratio: reduced posterior mass equals full posterior mass times the
reduction weight times the ratio of full evidence to masked evidence.  This
is the multiplicative conditional form of the reduction pushforward. -/
theorem reduced_posterior_reconstructs (prior : FiniteLaw Parameter)
    (weight : Parameter → ℝ) (kernel : FiniteKernel Parameter Evidence)
    (data : Evidence) (hw : ∀ x, 0 ≤ weight x)
    (hZ : 0 < ∑ x, weight x * prior x)
    (hP : 0 < kernel.predictive prior data)
    (hE : 0 < maskedEvidence prior weight kernel data)
    (hy : 0 < kernel.predictive (maskedPrior prior weight hw hZ) data)
    (x : Parameter) :
    FiniteKernel.posterior (maskedPrior prior weight hw hZ) kernel data hy x =
      FiniteKernel.posterior prior kernel data hP x * weight x *
        (kernel.predictive prior data /
          maskedEvidence prior weight kernel data) := by
  have hred := reduction_posterior_reconstruction prior weight kernel data hw
    hZ hy x
  have hfull := FiniteKernel.posterior_mul_predictive prior kernel data hP x
  field_simp [hE.ne']
  rw [hred, mul_assoc (weight x), ← hfull]
  ring

/-! ## Free energy monotonicity under reduction -/

/-- Reduction weakly raises the evidence free energy: the full model's
evidence free energy is at most the reduced model's, because masked evidence
never exceeds full evidence and `-log` is decreasing in the evidence. -/
theorem reduction_free_energy_monotone (prior : FiniteLaw Parameter)
    (weight : Parameter → ℝ) (kernel : FiniteKernel Parameter Evidence)
    (data : Evidence) (hw1 : ∀ x, weight x ≤ 1)
    (hE : 0 < maskedEvidence prior weight kernel data) :
    evidenceFreeEnergy (kernel.predictive prior data) ≤
      evidenceFreeEnergy (maskedEvidence prior weight kernel data) := by
  rw [evidenceFreeEnergy, evidenceFreeEnergy]
  apply neg_le_neg
  exact Real.log_le_log hE
    (maskedEvidence_le_predictive prior weight kernel data hw1)

/-! ## Gibbs-certificate form of the same monotonicity -/

/-- The Gibbs free energy is the negative Donsker--Varadhan objective. -/
theorem gibbsFreeEnergy_eq_neg_dvObjective (c : GibbsCertificate Parameter)
    (cand : FiniteLaw Parameter) :
    gibbsFreeEnergy c cand = -dvObjective c cand := by
  rw [gibbsFreeEnergy, dvObjective]
  ring

/-- The free-energy change against the Gibbs optimizer is exactly the KL
divergence to the optimizer: the Donsker--Varadhan duality gap. -/
theorem reduction_free_energy_change_eq_kl (c : GibbsCertificate Parameter)
    (cand : FiniteLaw Parameter) :
    gibbsFreeEnergy c cand - gibbsFreeEnergy c c.optimizer =
      finiteKL cand c.optimizer := by
  rw [gibbsFreeEnergy_eq_neg_dvObjective c cand,
    gibbsFreeEnergy_eq_neg_dvObjective c c.optimizer,
    dvObjective_eq_logPartition_sub_kl c cand, dvObjective_optimizer c]
  ring

/-- Reduction to the Gibbs optimizer never lowers the free energy: the
candidate's free energy is at least the optimizer's, with the excess exactly
the KL divergence to the optimizer. -/
theorem reduction_free_energy_monotone_gibbs
    (c : GibbsCertificate Parameter) (cand : FiniteLaw Parameter) :
    gibbsFreeEnergy c c.optimizer ≤ gibbsFreeEnergy c cand := by
  have h := reduction_free_energy_change_eq_kl c cand
  linarith [finiteKL_nonneg cand c.optimizer]

/-! ## Gaussian tilt clause -/

open MeasureTheory ProbabilityTheory FEP.GaussianInformationGeometry in
/-- For the pinned fixed-variance Gaussian family, the log Bayes factor of
the natural-coordinate tilt against the zero-mean base law is the natural
coordinate times the datum minus the natural log partition: the Bayes
factor reduces to the natural-log-partition difference in the pinned
charts. -/
theorem gaussianLogBayesFactor_eq (family : FixedVarianceGaussian)
    (natural x : ℝ) :
    Real.log
        (gaussianPDFReal (family.naturalToMean natural) family.variance x /
          gaussianPDFReal 0 family.variance x) =
      natural * x - family.naturalLogPartition natural :=
  family.naturalLogDensityRatio_eq natural x

end

end FEP.BayesianModelReduction
