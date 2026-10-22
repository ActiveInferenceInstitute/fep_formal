module
public import FepSketches.decision_risk
public import FepSketches.families.variational_duality
@[expose] public section
namespace fep_fep063.FEP063
open FEP FEP.FiniteInformation


namespace RelativeSupportControls
open FEP.NativeBlanket FEP.DecisionRisk
open scoped ENNReal

noncomputable def sparseReference : FiniteLaw (Bool × Bool) :=
  (FiniteLaw.uniform : FiniteLaw Bool).map (fun b => (b, b))

theorem sparse_support :
    ∀ xy, (FiniteLaw.pointMass (true, true)) xy ≠ 0 → 0 < sparseReference xy := by
  intro xy hmass
  by_cases hxy : xy = (true, true)
  · subst xy
    norm_num [sparseReference, FiniteLaw.map, FiniteLaw.uniform]
  · simp [FiniteLaw.pointMass, hxy] at hmass

theorem sparse_deterministic_DPI :
    finiteKL
        ((FiniteKernel.deterministic Prod.fst).predictive (FiniteLaw.pointMass (true, true)))
        ((FiniteKernel.deterministic Prod.fst).predictive sparseReference) ≤
      finiteKL (FiniteLaw.pointMass (true, true)) sparseReference :=
  fep063_finiteChannel_klDataProcessing_of_relativeSupport _ _ _ sparse_support

theorem identity_boundary :
    finiteKL (FiniteKernel.identity.predictive (FiniteLaw.pointMass (true, true)))
        (FiniteKernel.identity.predictive sparseReference) =
      finiteKL (FiniteLaw.pointMass (true, true)) sparseReference :=
  fep063_identityChannel_preservesKL _ _

theorem singular_support_adverse :
    ¬ (∀ x, (FiniteLaw.pointMass true) x ≠ 0 → 0 < (FiniteLaw.pointMass false) x) := by
  intro h
  have bad := h true (by norm_num [FiniteLaw.pointMass])
  norm_num [FiniteLaw.pointMass] at bad

theorem singular_native_infinity :
    InformationTheory.klDiv (embeddedLaw (FiniteLaw.pointMass true))
      (embeddedLaw (FiniteLaw.pointMass false)) = ∞ :=
  boolPointMass_klDiv_eq_top

end RelativeSupportControls
end fep_fep063.FEP063

namespace FEP68PrimaryAlignmentControls
open FEP FEP.FiniteInformation FEP.VariationalDuality
open fep_fep063.FEP063
open scoped ENNReal

/-- Full-support inputs are an explicitly supported special case. -/
theorem full_support_specialization
    {Input Output : Type*} [Fintype Input] [Fintype Output]
    (actual reference : FiniteLaw Input) (channel : FiniteKernel Input Output)
    (hreference : ∀ x, 0 < reference x) :
    finiteKL (channel.predictive actual) (channel.predictive reference) ≤
      finiteKL actual reference :=
  fep063_finiteChannel_klDataProcessing_of_relativeSupport actual reference channel
    (fun x _ => hreference x)

/-- Sparse reference has genuine shared-zero atoms; positivity is not implicit. -/
theorem sparse_shared_zero :
    RelativeSupportControls.sparseReference (true, false) = 0 := by
  norm_num [RelativeSupportControls.sparseReference, FiniteLaw.map, FiniteLaw.uniform]

/-- Singular totalized real KL is1, while the native quantity remains infinite. -/
theorem singular_real_finite :
    finiteKL (FiniteLaw.pointMass true) (FiniteLaw.pointMass false) = 1 :=
  finiteKL_disjoint_pointMass_totalized

/-- The proposed064 selector already names this actual-infimum bound. -/
theorem actual_dual_bound
    {Source Code : Type*} [Fintype Source] [Fintype Code]
    (source : FiniteLaw Source) (distortion : Source → Code → ℝ)
    (budget multiplier : ℝ) (hdistortion : ∀ x y, 0 ≤ distortion x y)
    (hmultiplier : 0 ≤ multiplier) (joint : FiniteLaw (Source × Code))
    (hjoint : RateDistortionFeasible source distortion budget joint) :
    rateDistortionDualValue source distortion budget multiplier ≤ mutualInformation joint :=
  fep_fep064.FEP064.fep064_rateDistortion_dual_lower_bound
    source distortion budget multiplier hdistortion hmultiplier joint hjoint

/-- A feasible informative interior problem exercises positive multiplier1. -/
theorem positive_multiplier_interior :
    ∃ joint : FiniteLaw (Bool × Bool),
      RateDistortionFeasible FiniteLaw.uniform boolHammingDistortion (1 / 4) joint ∧
      0 < mutualInformation joint ∧
      rateDistortionDualValue FiniteLaw.uniform boolHammingDistortion (1 / 4) 1 ≤
        mutualInformation joint := by
  obtain ⟨joint, hfeasible, hpositive, _⟩ :=
    fep_fep064.FEP064.fep064_quarterBudget_informative_optimum
  exact ⟨joint, hfeasible, hpositive,
    actual_dual_bound _ _ _ _ boolHammingDistortion_nonneg (by norm_num) joint hfeasible⟩

/-- Zero multiplier is a separate boundary, not existence of a dual maximizer. -/
theorem zero_multiplier_boundary :
    rateDistortionDualValue (FiniteLaw.uniform : FiniteLaw Bool)
      boolHammingDistortion (-1) 0 = 0 :=
  fep_fep064.FEP064.fep064_dual_zeroMultiplier _ _ _

/-- Negative nonnegative-distortion budget is genuinely infeasible. -/
theorem negative_budget_adverse :
    ¬ ∃ joint, RateDistortionFeasible (FiniteLaw.uniform : FiniteLaw Bool)
      boolHammingDistortion (-1) joint :=
  fep_fep064.FEP064.fep064_negativeBudget_infeasible _ _ _
    boolHammingDistortion_nonneg (by norm_num)

end FEP68PrimaryAlignmentControls
#print axioms fep_fep063.FEP063.fep063_finiteChannel_klDataProcessing_of_relativeSupport
#print axioms fep_fep063.FEP063.RelativeSupportControls.sparse_support
#print axioms fep_fep063.FEP063.RelativeSupportControls.sparse_deterministic_DPI
#print axioms fep_fep063.FEP063.RelativeSupportControls.identity_boundary
#print axioms fep_fep063.FEP063.RelativeSupportControls.singular_support_adverse
#print axioms fep_fep063.FEP063.RelativeSupportControls.singular_native_infinity
#print axioms FEP68PrimaryAlignmentControls.full_support_specialization
#print axioms FEP68PrimaryAlignmentControls.sparse_shared_zero
#print axioms FEP68PrimaryAlignmentControls.singular_real_finite
#print axioms FEP68PrimaryAlignmentControls.actual_dual_bound
#print axioms FEP68PrimaryAlignmentControls.positive_multiplier_interior
#print axioms FEP68PrimaryAlignmentControls.zero_multiplier_boundary
#print axioms FEP68PrimaryAlignmentControls.negative_budget_adverse
