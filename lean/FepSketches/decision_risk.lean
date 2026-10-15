module
public import FepSketches.native_blanket
public import FepSketches.finite_information
public import Mathlib.InformationTheory.KullbackLeibler.DataProcessing
public import Mathlib.Probability.Decision.BayesEstimator
public import Mathlib.Probability.Decision.Risk.Basic

@[expose] public section

/-!
# Native information and Bayesian decision risk

This module connects the repository's normalized finite laws to Mathlib's
extended-real Kullback--Leibler divergence and decision-risk APIs.  Native KL
statements retain absolute-continuity and `ℝ≥0∞` boundaries.  Proper
logarithmic-score risk remains ordered by the truth and reported laws; it is
not identified with an oppositely ordered variational KL term.
-/

namespace FEP.DecisionRisk

open FEP FEP.FiniteInformation FEP.NativeBlanket
open MeasureTheory ProbabilityTheory
open scoped BigOperators ENNReal MeasureTheory ProbabilityTheory

noncomputable section

section FiniteKLBridge

variable {α : Type*} [Fintype α] [MeasurableSpace α]
  [DiscreteMeasurableSpace α]

/-- Relative support suffices for the density-ratio construction.  Shared
zero-mass atoms contribute zero; only mass placed outside reference support
is excluded. -/
theorem embeddedLaw_withDensity_ratio_of_relativeSupport (p q : FiniteLaw α)
    (hsupport : ∀ x, p x ≠ 0 → 0 < q x) :
    (embeddedLaw q).withDensity
        (fun x => ENNReal.ofReal (p x / q x)) = embeddedLaw p := by
  classical
  apply Measure.ext_of_singleton
  intro x
  rw [withDensity_apply _ MeasurableSet.of_discrete,
    lintegral_singleton, embeddedLaw_apply_singleton,
    embeddedLaw_apply_singleton, ← ENNReal.ofReal_mul
      (div_nonneg (p.nonneg x) (q.nonneg x))]
  by_cases hq : q x = 0
  · have hp : p x = 0 := by
      by_contra hp
      exact (ne_of_gt (hsupport x hp)) hq
    simp [hq, hp]
  · rw [div_mul_cancel₀ _ hq]

/-- Native and finite KL agree under relative support, including sparse laws.
This does not identify the totalized finite value with native infinity when
the actual law charges a zero-reference atom. -/
theorem weightedDirac_klDiv_eq_finiteKL_of_relativeSupport
    (p q : FiniteLaw α) (hsupport : ∀ x, p x ≠ 0 → 0 < q x) :
    InformationTheory.klDiv (embeddedLaw p) (embeddedLaw q) =
      ENNReal.ofReal (finiteKL p q) := by
  have hDensity := embeddedLaw_withDensity_ratio_of_relativeSupport p q hsupport
  have hAC : embeddedLaw p ≪ embeddedLaw q := by
    rw [← hDensity]
    exact withDensity_absolutelyContinuous _ _
  rw [InformationTheory.klDiv_eq_lintegral_klFun_of_ac hAC]
  have hRN :
      (embeddedLaw p).rnDeriv (embeddedLaw q) =ᵐ[embeddedLaw q]
        fun x => ENNReal.ofReal (p x / q x) := by
    rw [← hDensity]
    exact Measure.rnDeriv_withDensity _ (by fun_prop)
  have hIntegrand :
      (fun x => ENNReal.ofReal
        (InformationTheory.klFun
          ((embeddedLaw p).rnDeriv (embeddedLaw q) x).toReal)) =ᵐ[embeddedLaw q]
        fun x => ENNReal.ofReal (InformationTheory.klFun (p x / q x)) := by
    filter_upwards [hRN] with x hx
    rw [hx, ENNReal.toReal_ofReal
      (div_nonneg (p.nonneg x) (q.nonneg x))]
  rw [lintegral_congr_ae hIntegrand, lintegral_fintype, finiteKL,
    ENNReal.ofReal_sum_of_nonneg]
  · apply Finset.sum_congr rfl
    intro x _
    rw [embeddedLaw_apply_singleton,
      ENNReal.ofReal_mul (q.nonneg x), mul_comm]
  · intro x _
    exact mul_nonneg (q.nonneg x)
      (InformationTheory.klFun_nonneg
        (div_nonneg (p.nonneg x) (q.nonneg x)))

/-- Under full reference support, the embedded actual law is the reference
measure tilted by the pointwise finite-law likelihood ratio. -/
theorem embeddedLaw_withDensity_ratio (p q : FiniteLaw α)
    (hq : ∀ x, 0 < q x) :
    (embeddedLaw q).withDensity
        (fun x => ENNReal.ofReal (p x / q x)) = embeddedLaw p := by
  classical
  apply Measure.ext_of_singleton
  intro x
  rw [withDensity_apply _ MeasurableSet.of_discrete,
    lintegral_singleton, embeddedLaw_apply_singleton,
    embeddedLaw_apply_singleton, ← ENNReal.ofReal_mul
      (div_nonneg (p.nonneg x) (q.nonneg x)),
    div_mul_cancel₀ _ (ne_of_gt (hq x))]

/-- The native weighted-Dirac KL is the `ℝ≥0∞` embedding of the repository's
real finite KL whenever the reference law has full support. -/
theorem weightedDirac_klDiv_eq_finiteKL_of_fullSupport
    (p q : FiniteLaw α) (hq : ∀ x, 0 < q x) :
    InformationTheory.klDiv (embeddedLaw p) (embeddedLaw q) =
      ENNReal.ofReal (finiteKL p q) := by
  have hDensity := embeddedLaw_withDensity_ratio p q hq
  have hAC : embeddedLaw p ≪ embeddedLaw q := by
    rw [← hDensity]
    exact withDensity_absolutelyContinuous _ _
  rw [InformationTheory.klDiv_eq_lintegral_klFun_of_ac hAC]
  have hRN :
      (embeddedLaw p).rnDeriv (embeddedLaw q) =ᵐ[embeddedLaw q]
        fun x => ENNReal.ofReal (p x / q x) := by
    rw [← hDensity]
    exact Measure.rnDeriv_withDensity _ (by fun_prop)
  have hIntegrand :
      (fun x => ENNReal.ofReal
        (InformationTheory.klFun
          ((embeddedLaw p).rnDeriv (embeddedLaw q) x).toReal)) =ᵐ[embeddedLaw q]
        fun x => ENNReal.ofReal (InformationTheory.klFun (p x / q x)) := by
    filter_upwards [hRN] with x hx
    rw [hx, ENNReal.toReal_ofReal
      (div_nonneg (p.nonneg x) (q.nonneg x))]
  rw [lintegral_congr_ae hIntegrand, lintegral_fintype, finiteKL,
    ENNReal.ofReal_sum_of_nonneg]
  · apply Finset.sum_congr rfl
    intro x _
    rw [embeddedLaw_apply_singleton,
      ENNReal.ofReal_mul (q.nonneg x), mul_comm]
  · intro x _
    exact mul_nonneg (q.nonneg x)
      (InformationTheory.klFun_nonneg
        (div_nonneg (p.nonneg x) (q.nonneg x)))

omit [DiscreteMeasurableSpace α] in
/-- Native KL is infinite at every failure of absolute continuity. -/
theorem weightedDirac_klDiv_eq_top_of_not_absolutelyContinuous
    (p q : FiniteLaw α) (hNotAC : ¬ embeddedLaw p ≪ embeddedLaw q) :
    InformationTheory.klDiv (embeddedLaw p) (embeddedLaw q) = ∞ :=
  InformationTheory.klDiv_of_not_ac hNotAC

/-- Disjoint Boolean point masses exercise the singular native-KL boundary. -/
theorem boolPointMass_klDiv_eq_top :
    InformationTheory.klDiv
        (embeddedLaw (FiniteLaw.pointMass true))
        (embeddedLaw (FiniteLaw.pointMass false)) = ∞ := by
  apply weightedDirac_klDiv_eq_top_of_not_absolutelyContinuous
  intro hAC
  have hReferenceZero :
      embeddedLaw (FiniteLaw.pointMass false) ({true} : Set Bool) = 0 := by
    simp [embeddedLaw_apply_singleton, FiniteLaw.pointMass]
  have hActualZero := hAC hReferenceZero
  norm_num [embeddedLaw_apply_singleton, FiniteLaw.pointMass] at hActualZero

end FiniteKLBridge

section ProperLogScore

variable {α : Type*} [Fintype α]

/-- Expected logarithmic-score risk in excess of truthful self-reporting.  The
first law is the data-generating truth and the second is the report. -/
noncomputable def properLogScoreExcessRisk
    (truth report : FiniteLaw α) : ℝ :=
  crossEntropy truth report - crossEntropy truth truth

/-- Self cross-entropy agrees with entropy, including at zero-mass atoms under
Mathlib's continuous `negMulLog` convention. -/
private theorem crossEntropy_self_eq_entropy (p : FiniteLaw α) :
    crossEntropy p p = entropy p := by
  apply Finset.sum_congr rfl
  intro x _
  rw [Real.negMulLog_eq_neg]
  ring

/-- Proper logarithmic-score excess risk is KL from the truth law to the
reported law exactly when the report is positive on the truth's support. -/
theorem properLogScore_excessRisk_eq_finiteKL_truth_report
    (truth report : FiniteLaw α)
    (hreport : ∀ x, truth x ≠ 0 → 0 < report x) :
    properLogScoreExcessRisk truth report = finiteKL truth report := by
  have hpoint : ∀ x,
      report x * InformationTheory.klFun (truth x / report x) =
        (-truth x * Real.log (report x) - Real.negMulLog (truth x)) +
          (report x - truth x) := by
    intro x
    by_cases htruth : truth x = 0
    · simp [htruth, InformationTheory.klFun_zero]
    · exact weighted_klFun_eq_log_score (hreport x htruth)
  rw [properLogScoreExcessRisk, crossEntropy_self_eq_entropy]
  symm
  simp_rw [finiteKL, hpoint]
  rw [Finset.sum_add_distrib, Finset.sum_sub_distrib,
    Finset.sum_sub_distrib, report.sum_one, truth.sum_one, sub_self, add_zero]
  rfl

/-! ### Executable orientation guard -/

/-- Asymmetric full-support Boolean truth law: masses `(4/7, 3/7)` on
`(false, true)`. -/
def asymmetricBoolTruth : FiniteLaw Bool where
  mass outcome := if outcome then 3 / 7 else 4 / 7
  nonneg outcome := by cases outcome <;> norm_num
  sum_one := by rw [Fintype.sum_bool]; norm_num

/-- Asymmetric full-support Boolean report law: masses `(1/7, 6/7)` on
`(false, true)`. -/
def asymmetricBoolReport : FiniteLaw Bool where
  mass outcome := if outcome then 6 / 7 else 1 / 7
  nonneg outcome := by cases outcome <;> norm_num
  sum_one := by rw [Fintype.sum_bool]; norm_num

/-- The two argument orders of finite KL are genuinely unequal, so an API
consumer cannot silently swap truth and report. -/
theorem finiteKL_asymmetric_bool :
    finiteKL asymmetricBoolTruth asymmetricBoolReport ≠
      finiteKL asymmetricBoolReport asymmetricBoolTruth := by
  have hlogTwo : 0 < Real.log 2 := Real.log_pos (by norm_num)
  have hlogFour : Real.log 4 = 2 * Real.log 2 := by
    calc
      Real.log 4 = Real.log (2 * 2) := by norm_num
      _ = Real.log 2 + Real.log 2 :=
        Real.log_mul (by norm_num) (by norm_num)
      _ = 2 * Real.log 2 := by ring
  have hlogHalf : Real.log (1 / 2) = -Real.log 2 := by
    rw [show (1 / 2 : ℝ) = 2⁻¹ by norm_num, Real.log_inv]
  have hlogQuarter : Real.log (1 / 4) = -(2 * Real.log 2) := by
    rw [show (1 / 4 : ℝ) = 4⁻¹ by norm_num, Real.log_inv,
      hlogFour]
  simp only [finiteKL, Fintype.sum_bool, asymmetricBoolTruth,
    asymmetricBoolReport]
  norm_num [InformationTheory.klFun_apply]
  rw [hlogHalf, hlogFour, hlogQuarter]
  nlinarith

end ProperLogScore

section NativeMutualInformation

variable {Parameter Observation Garbled : Type*}
  {mParameter : MeasurableSpace Parameter}
  {mObservation : MeasurableSpace Observation}
  {mGarbled : MeasurableSpace Garbled}

/-- Native channel mutual information: KL from the prior--experiment joint
measure to the product of the prior and predictive measures. -/
noncomputable def nativeChannelMutualInformation
    (prior : Measure Parameter) [IsProbabilityMeasure prior]
    (experiment : Kernel Parameter Observation) [IsMarkovKernel experiment] : ℝ≥0∞ :=
  InformationTheory.klDiv (prior ⊗ₘ experiment)
    (prior.prod (experiment ∘ₘ prior))

/-- Postprocessing observations with a Markov kernel cannot increase native
channel mutual information.  The proof sends both the joint and its product
reference through the same product kernel before applying Mathlib's KL DPI. -/
theorem mutualInformation_mono_under_observationGarbling
    (prior : Measure Parameter) [IsProbabilityMeasure prior]
    (experiment : Kernel Parameter Observation) [IsMarkovKernel experiment]
    (garbling : Kernel Observation Garbled) [IsMarkovKernel garbling] :
    nativeChannelMutualInformation prior (garbling ∘ₖ experiment) ≤
      nativeChannelMutualInformation prior experiment := by
  rw [nativeChannelMutualInformation, ← Measure.parallelComp_comp_compProd,
    ← Measure.comp_assoc, Measure.prod_comp_right]
  exact InformationTheory.klDiv_comp_right_le _ _
    (Kernel.id ∥ₖ garbling)

end NativeMutualInformation

section FiniteMutualInformation

variable {α β γ : Type*} [Fintype α] [Fintype β] [Fintype γ]
  [MeasurableSpace α] [MeasurableSpace β] [MeasurableSpace γ]
  [DiscreteMeasurableSpace α] [DiscreteMeasurableSpace β]
  [DiscreteMeasurableSpace γ]

/-- Independent finite products embed as native product measures. -/
theorem embeddedLaw_product (p : FiniteLaw α) (q : FiniteLaw β) :
    embeddedLaw (p.product q) = (embeddedLaw p).prod (embeddedLaw q) := by
  classical
  apply Measure.ext_of_singleton
  rintro ⟨x, y⟩
  rw [embeddedLaw_apply_singleton]
  change ENNReal.ofReal (p x * q y) = _
  rw [show ({(x, y)} : Set (α × β)) = {x} ×ˢ {y} by ext; simp,
    Measure.prod_prod]
  simp [ENNReal.ofReal_mul (p.nonneg x)]

omit [MeasurableSpace α] [MeasurableSpace β]
  [DiscreteMeasurableSpace α] [DiscreteMeasurableSpace β] in
/-- A positive joint atom forces both corresponding marginal atoms positive.
Thus every finite joint is relatively supported by its product marginals,
even when either marginal has unused states. -/
theorem joint_relativeSupport_productMarginals (joint : FiniteLaw (α × β)) :
    ∀ xy, joint xy ≠ 0 →
      0 < (joint.fstMarginal.product joint.sndMarginal) xy := by
  classical
  rintro ⟨x, y⟩ hmass
  have hpos : 0 < joint (x, y) :=
    lt_of_le_of_ne (joint.nonneg (x, y)) (Ne.symm hmass)
  have hfst : 0 < joint.fstMarginal x := by
    change 0 < ∑ z : β, joint (x, z)
    exact lt_of_lt_of_le hpos
      (Finset.single_le_sum (fun z _ => joint.nonneg (x, z)) (Finset.mem_univ y))
  have hsnd : 0 < joint.sndMarginal y := by
    change 0 < ∑ z : α, joint (z, y)
    exact lt_of_lt_of_le hpos
      (Finset.single_le_sum (fun z _ => joint.nonneg (z, y)) (Finset.mem_univ x))
  exact mul_pos hfst hsnd

/-- Finite mutual information agrees with native KL of the embedded joint
and product marginals without full-support assumptions. -/
theorem embeddedJoint_klDiv_eq_mutualInformation
    (joint : FiniteLaw (α × β)) :
    InformationTheory.klDiv (embeddedLaw joint)
        ((embeddedLaw joint.fstMarginal).prod (embeddedLaw joint.sndMarginal)) =
      ENNReal.ofReal (mutualInformation joint) := by
  rw [← embeddedLaw_product]
  exact weightedDirac_klDiv_eq_finiteKL_of_relativeSupport _ _
    (joint_relativeSupport_productMarginals joint)

omit [MeasurableSpace α] [MeasurableSpace β]
  [DiscreteMeasurableSpace α] [DiscreteMeasurableSpace β] in
/-- The first marginal of a finite channel joint is its prior. -/
theorem channelJoint_fstMarginal (prior : FiniteLaw α)
    (experiment : FiniteKernel α β) :
    (experiment.joint prior).fstMarginal = prior := by
  classical
  apply FiniteLaw.ext_mass
  funext x
  change (∑ y : β, prior x * experiment x y) = prior x
  rw [← Finset.mul_sum, experiment.sum_one, mul_one]

/-- Native channel mutual information is exactly the finite information of
the same prior-kernel joint, including deterministic experiments. -/
theorem nativeChannelMutualInformation_eq_finite
    (prior : FiniteLaw α) (experiment : FiniteKernel α β) :
    nativeChannelMutualInformation (embeddedLaw prior) (embeddedKernel experiment) =
      ENNReal.ofReal (mutualInformation (experiment.joint prior)) := by
  rw [nativeChannelMutualInformation, ← embeddedLaw_joint_eq_compProd,
    ← embeddedPredictive_eq_comp]
  have h := embeddedJoint_klDiv_eq_mutualInformation (experiment.joint prior)
  rw [channelJoint_fstMarginal] at h
  exact h

omit [MeasurableSpace α] [MeasurableSpace β]
  [DiscreteMeasurableSpace α] [DiscreteMeasurableSpace β] in
/-- A normalized channel preserves support containment.  Positive predictive
mass has a positive input/channel summand, which also contributes positively
under the relatively supporting reference law. -/
theorem predictive_relativeSupport (actual reference : FiniteLaw α)
    (channel : FiniteKernel α β)
    (hsupport : ∀ x, actual x ≠ 0 → 0 < reference x) :
    ∀ y, channel.predictive actual y ≠ 0 →
      0 < channel.predictive reference y := by
  classical
  intro y hmass
  have hpos : 0 < ∑ x : α, actual x * channel x y :=
    lt_of_le_of_ne ((channel.predictive actual).nonneg y) (Ne.symm hmass)
  obtain ⟨x, _, hterm⟩ := (Finset.sum_pos_iff_of_nonneg
    (fun x _ => mul_nonneg (actual.nonneg x) (channel.nonneg x y))).mp hpos
  have hactual : actual x ≠ 0 := by
    intro hzero
    simp [hzero] at hterm
  have hchannel : 0 < channel x y := by
    have hne : channel x y ≠ 0 := by
      intro hzero
      simp [hzero] at hterm
    exact lt_of_le_of_ne (channel.nonneg x y) (Ne.symm hne)
  have hreference := mul_pos (hsupport x hactual) hchannel
  exact lt_of_lt_of_le hreference
    (Finset.single_le_sum
      (fun z _ => mul_nonneg (reference.nonneg z) (channel.nonneg z y))
      (Finset.mem_univ x))

/-- Finite KL data processing under relative input support and arbitrary
normalized channels, including deterministic and sparse rows. -/
theorem finiteKL_mono_under_channel_of_relativeSupport
    (actual reference : FiniteLaw α) (channel : FiniteKernel α β)
    (hsupport : ∀ x, actual x ≠ 0 → 0 < reference x) :
    finiteKL (channel.predictive actual) (channel.predictive reference) ≤
      finiteKL actual reference := by
  have h := InformationTheory.klDiv_comp_right_le
    (embeddedLaw actual) (embeddedLaw reference) (embeddedKernel channel)
  simp only [← embeddedPredictive_eq_comp] at h
  rw [weightedDirac_klDiv_eq_finiteKL_of_relativeSupport _ _
      (predictive_relativeSupport actual reference channel hsupport),
    weightedDirac_klDiv_eq_finiteKL_of_relativeSupport _ _ hsupport] at h
  exact (ENNReal.ofReal_le_ofReal_iff (finiteKL_nonneg actual reference)).mp h

/-- Observation garbling cannot increase finite channel information.  There
are no positivity assumptions on prior atoms, experiment rows, or garbling
rows: normalization and the proved finite/native bridge supply the seam. -/
theorem finiteMutualInformation_mono_under_observationGarbling
    (prior : FiniteLaw α) (experiment : FiniteKernel α β)
    (garbling : FiniteKernel β γ) :
    mutualInformation ((FiniteKernel.comp garbling experiment).joint prior) ≤
      mutualInformation (experiment.joint prior) := by
  have h := mutualInformation_mono_under_observationGarbling
    (embeddedLaw prior) (embeddedKernel experiment) (embeddedKernel garbling)
  simp only [← embeddedKernel_comp, nativeChannelMutualInformation_eq_finite,
    nativeChannelMutualInformation_eq_finite] at h
  exact (ENNReal.ofReal_le_ofReal_iff (mutualInformation_nonneg _)).mp h

end FiniteMutualInformation

section BayesRisk

variable {Θ Observation Garbled Decision : Type*}
  {mΘ : MeasurableSpace Θ} {mObservation : MeasurableSpace Observation}
  {mGarbled : MeasurableSpace Garbled} {mDecision : MeasurableSpace Decision}

/-- Garbling an experiment with a native Markov kernel cannot reduce its
Bayes risk. -/
theorem bayesRisk_mono_under_observationGarbling
    (loss : Θ → Decision → ℝ≥0∞) (experiment : Kernel Θ Observation)
    (prior : Measure Θ) (garbling : Kernel Observation Garbled)
    [IsMarkovKernel garbling] :
    ProbabilityTheory.bayesRisk loss experiment prior ≤
      ProbabilityTheory.bayesRisk loss (garbling ∘ₖ experiment) prior :=
  ProbabilityTheory.bayesRisk_le_bayesRisk_comp
    loss experiment prior garbling

/-! ### Boolean nonvacuity witness -/

/-- Fair Boolean law used by the decision-risk witness. -/
def boolFairLaw : FiniteLaw Bool where
  mass _ := 1 / 2
  nonneg _ := by norm_num
  sum_one := by rw [Fintype.sum_bool]; norm_num

/-- The fair finite law embedded as a native Mathlib prior. -/
noncomputable def boolPrior : Measure Bool := embeddedLaw boolFairLaw

noncomputable instance boolPrior_isProbabilityMeasure :
    IsProbabilityMeasure boolPrior := by
  unfold boolPrior
  infer_instance

/-- Zero-one loss on the Boolean parameter and decision spaces. -/
def boolZeroOneLoss (truth report : Bool) : ℝ≥0∞ :=
  if truth = report then 0 else 1

theorem boolZeroOneLoss_measurable :
    Measurable (Function.uncurry boolZeroOneLoss) := by
  fun_prop

/-- The revealing experiment returns the Boolean parameter unchanged. -/
noncomputable def revealingBoolExperiment : Kernel Bool Bool := Kernel.id

noncomputable instance revealingBoolExperiment_isMarkovKernel :
    IsMarkovKernel revealingBoolExperiment := by
  rw [revealingBoolExperiment]
  infer_instance

/-- An input-independent channel erases the revealing observation. -/
noncomputable def independentBoolGarbling : Kernel Bool Bool :=
  Kernel.const Bool boolPrior

/-- The revealing experiment after the input-independent garbling. -/
noncomputable def garbledBoolExperiment : Kernel Bool Bool :=
  independentBoolGarbling ∘ₖ revealingBoolExperiment

/-- Under the fair prior, either constant Boolean report has risk one half. -/
theorem boolPrior_zeroOneRisk (report : Bool) :
    ∫⁻ truth, boolZeroOneLoss truth report ∂boolPrior = 1 / 2 := by
  rw [lintegral_fintype]
  cases report <;>
    norm_num [boolPrior, boolFairLaw, boolZeroOneLoss,
      embeddedLaw_apply_singleton, ENNReal.ofReal_div_of_pos]

/-- Identity is a genuine posterior argmin estimator for the revealing
Boolean experiment. -/
theorem revealingBoolArgminEstimator :
    IsArgminEstimator boolZeroOneLoss revealingBoolExperiment boolPrior id := by
  refine ⟨measurable_id, ?_⟩
  simp only [revealingBoolExperiment, Measure.id_comp]
  filter_upwards [ProbabilityTheory.posterior_id boolPrior] with observation hPosterior
  rw [hPosterior]
  simp_rw [Kernel.lintegral_id]
  cases observation <;> simp [boolZeroOneLoss, iInf_bool_eq]

/-- The deterministic kernel induced by the Boolean argmin is a Mathlib Bayes
estimator. -/
theorem revealingBool_isBayesEstimator :
    IsBayesEstimator boolZeroOneLoss revealingBoolExperiment Kernel.id boolPrior := by
  simpa [revealingBoolExperiment, Kernel.id] using
    revealingBoolArgminEstimator.isBayesEstimator boolZeroOneLoss_measurable

/-- A fully revealing Boolean experiment has zero Bayes risk under zero-one
loss. -/
theorem revealingBool_bayesRisk_eq_zero :
    bayesRisk boolZeroOneLoss revealingBoolExperiment boolPrior = 0 := by
  rw [← revealingBool_isBayesEstimator]
  simp only [avgRisk, revealingBoolExperiment, Kernel.id_comp]
  simp_rw [Kernel.lintegral_id]
  simp [boolZeroOneLoss]

/-- Erasing the revealing observation raises the exact Bayes risk to one
half. -/
theorem garbledBool_bayesRisk_eq_half :
    bayesRisk boolZeroOneLoss garbledBoolExperiment boolPrior = 1 / 2 := by
  rw [show garbledBoolExperiment = Kernel.const Bool boolPrior by
    simp [garbledBoolExperiment, independentBoolGarbling,
      revealingBoolExperiment]]
  rw [ProbabilityTheory.bayesRisk_const boolZeroOneLoss_measurable]
  simp_rw [boolPrior_zeroOneRisk]
  simp

/-- The concrete garbling is nonvacuous: its Bayes risk is strictly larger. -/
theorem revealingBool_bayesRisk_lt_garbled :
    bayesRisk boolZeroOneLoss revealingBoolExperiment boolPrior <
      bayesRisk boolZeroOneLoss garbledBoolExperiment boolPrior := by
  rw [revealingBool_bayesRisk_eq_zero, garbledBool_bayesRisk_eq_half]
  norm_num

end BayesRisk

end

end FEP.DecisionRisk
