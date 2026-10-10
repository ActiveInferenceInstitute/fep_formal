import FepSketches.finite_information
import Mathlib.Analysis.Convex.SpecificFunctions.Basic
import Mathlib.Topology.Order.Compact

/-!
# Finite variational duality and information bounds

The results here use the normalized `FiniteLaw`/`FiniteKernel` substrate.  All
logarithmic identities expose full-support premises.  In particular, no result
identifies the existing totalized real-valued KL with an extended divergence at
zero reference mass.
-/

namespace FEP.VariationalDuality

open FEP FEP.FiniteInformation Finset InformationTheory
open scoped BigOperators

variable {α β γ : Type*} [Fintype α] [Fintype β] [Fintype γ]

/-- Expectation of a real potential under a finite law. -/
def expectation (law : FiniteLaw α) (potential : α → ℝ) : ℝ :=
  ∑ x, law x * potential x

/-- Data sufficient to certify a normalized finite Gibbs optimizer.  The
pointwise log-density identity is explicit, as are both support assumptions. -/
structure GibbsCertificate (α : Type*) [Fintype α] where
  reference : FiniteLaw α
  optimizer : FiniteLaw α
  potential : α → ℝ
  logPartition : ℝ
  reference_pos : ∀ x, 0 < reference x
  optimizer_pos : ∀ x, 0 < optimizer x
  log_optimizer : ∀ x,
    Real.log (optimizer x) =
      Real.log (reference x) + potential x - logPartition

/-- A closed non-vacuity witness: the uniform law is the Gibbs optimizer for a
zero potential, with log partition zero. -/
noncomputable def uniformZeroPotentialGibbs [Nonempty α] :
    GibbsCertificate α where
  reference := FiniteLaw.uniform
  optimizer := FiniteLaw.uniform
  potential _ := 0
  logPartition := 0
  reference_pos _ := by
    change 0 < ((Fintype.card α : ℝ)⁻¹)
    exact inv_pos.mpr (Nat.cast_pos.mpr Fintype.card_pos)
  optimizer_pos _ := by
    change 0 < ((Fintype.card α : ℝ)⁻¹)
    exact inv_pos.mpr (Nat.cast_pos.mpr Fintype.card_pos)
  log_optimizer _ := by simp

/-- Donsker--Varadhan objective for a finite potential and reference law. -/
noncomputable def dvObjective
    (certificate : GibbsCertificate α) (candidate : FiniteLaw α) : ℝ :=
  expectation candidate certificate.potential -
    finiteKL candidate certificate.reference

/-- Free-energy form of the same finite variational objective. -/
noncomputable def gibbsFreeEnergy
    (certificate : GibbsCertificate α) (candidate : FiniteLaw α) : ℝ :=
  finiteKL candidate certificate.reference -
    expectation candidate certificate.potential

/-- Exact finite Gibbs identity: the duality gap is KL to the certified Gibbs
optimizer. -/
theorem dvObjective_eq_logPartition_sub_kl
    (certificate : GibbsCertificate α) (candidate : FiniteLaw α) :
    dvObjective certificate candidate =
      certificate.logPartition -
        finiteKL candidate certificate.optimizer := by
  unfold dvObjective
  rw [finiteKL_eq_crossEntropy_sub_entropy candidate certificate.reference
      certificate.reference_pos,
    finiteKL_eq_crossEntropy_sub_entropy candidate certificate.optimizer
      certificate.optimizer_pos]
  simp only [expectation, crossEntropy, entropy]
  have hlog := certificate.log_optimizer
  simp_rw [hlog]
  simp_rw [mul_sub, mul_add]
  rw [Finset.sum_sub_distrib, Finset.sum_add_distrib]
  have hpartition :
      (∑ x, candidate x * certificate.logPartition) =
        certificate.logPartition := by
    rw [← Finset.sum_mul, candidate.sum_one, one_mul]
  have hneg (f : α → ℝ) :
      (∑ x, -candidate x * f x) = -(∑ x, candidate x * f x) := by
    simp_rw [neg_mul]
    rw [Finset.sum_neg_distrib]
  rw [hneg (fun x => Real.log (certificate.reference x)),
    hneg certificate.potential,
    hneg (fun _ => certificate.logPartition), hpartition]
  ring

/-- Finite Donsker--Varadhan upper bound. -/
theorem dvObjective_le_logPartition
    (certificate : GibbsCertificate α) (candidate : FiniteLaw α) :
    dvObjective certificate candidate ≤ certificate.logPartition := by
  rw [dvObjective_eq_logPartition_sub_kl]
  linarith [finiteKL_nonneg candidate certificate.optimizer]

/-- The explicit Gibbs optimizer attains the Donsker--Varadhan bound. -/
theorem dvObjective_optimizer (certificate : GibbsCertificate α) :
    dvObjective certificate certificate.optimizer =
      certificate.logPartition := by
  rw [dvObjective_eq_logPartition_sub_kl, finiteKL_self, sub_zero]

/-- The uniform zero-potential certificate attains objective value zero. -/
theorem uniformZeroPotentialGibbs_objective [Nonempty α] :
    dvObjective (uniformZeroPotentialGibbs (α := α))
        (uniformZeroPotentialGibbs (α := α)).optimizer = 0 := by
  exact dvObjective_optimizer (uniformZeroPotentialGibbs (α := α))

/-- Attainment uniquely identifies the normalized Gibbs optimizer. -/
theorem dvObjective_eq_logPartition_iff
    (certificate : GibbsCertificate α) (candidate : FiniteLaw α) :
    dvObjective certificate candidate = certificate.logPartition ↔
      candidate = certificate.optimizer := by
  rw [dvObjective_eq_logPartition_sub_kl]
  constructor
  · intro h
    have hzero : finiteKL candidate certificate.optimizer = 0 := by
      linarith
    exact (finiteKL_eq_zero_iff candidate certificate.optimizer).mp hzero
  · rintro rfl
    rw [finiteKL_self, sub_zero]

/-- Gibbs' variational principle in free-energy form. -/
theorem neg_logPartition_le_gibbsFreeEnergy
    (certificate : GibbsCertificate α) (candidate : FiniteLaw α) :
    -certificate.logPartition ≤ gibbsFreeEnergy certificate candidate := by
  have h := dvObjective_le_logPartition certificate candidate
  simpa [dvObjective, gibbsFreeEnergy] using neg_le_neg h

/-- The Gibbs optimizer exactly minimizes finite free energy. -/
theorem gibbsFreeEnergy_optimizer (certificate : GibbsCertificate α) :
    gibbsFreeEnergy certificate certificate.optimizer =
      -certificate.logPartition := by
  have h := dvObjective_optimizer certificate
  simpa [dvObjective, gibbsFreeEnergy] using congrArg Neg.neg h

/-! ## Coordinate and mean-field decompositions -/

/-- An ELBO-like score defined as negative divergence from a reference joint. -/
noncomputable def jointELBO
    (actualPrior referencePrior : FiniteLaw α)
    (actualKernel referenceKernel : FiniteKernel α β) : ℝ :=
  -finiteKL (actualKernel.joint actualPrior)
    (referenceKernel.joint referencePrior)

/-- Coordinate ELBO decomposition into a marginal score and expected
conditional divergence. -/
theorem jointELBO_coordinate_decomposition
    (actualPrior referencePrior : FiniteLaw α)
    (actualKernel referenceKernel : FiniteKernel α β)
    (hprior : ∀ x, 0 < referencePrior x)
    (hkernel : ∀ x y, 0 < referenceKernel x y) :
    jointELBO actualPrior referencePrior actualKernel referenceKernel =
      -finiteKL actualPrior referencePrior -
        conditionalKL actualPrior actualKernel referenceKernel := by
  rw [jointELBO,
    finiteKL_joint_chain_rule actualPrior referencePrior actualKernel
      referenceKernel hprior hkernel]
  ring

/-- Mean-field coordinate free energy with one factor held fixed. -/
noncomputable def meanFieldCoordinateFreeEnergy
    (fixed : FiniteLaw α) (candidate target : FiniteLaw β) : ℝ :=
  finiteKL (fixed.product candidate) (fixed.product target)

/-- With full support, the mean-field coordinate objective reduces exactly to
KL of the varying factor. -/
theorem meanFieldCoordinateFreeEnergy_eq
    (fixed : FiniteLaw α) (candidate target : FiniteLaw β)
    (hfixed : ∀ x, 0 < fixed x) (htarget : ∀ y, 0 < target y) :
    meanFieldCoordinateFreeEnergy fixed candidate target =
      finiteKL candidate target := by
  rw [meanFieldCoordinateFreeEnergy,
    finiteKL_product fixed fixed candidate target hfixed htarget,
    finiteKL_self, zero_add]

/-- The target factor is the unique optimum of the supported mean-field
coordinate objective. -/
theorem meanFieldCoordinate_optimum_iff
    (fixed : FiniteLaw α) (candidate target : FiniteLaw β)
    (hfixed : ∀ x, 0 < fixed x) (htarget : ∀ y, 0 < target y) :
    meanFieldCoordinateFreeEnergy fixed candidate target = 0 ↔
      candidate = target := by
  rw [meanFieldCoordinateFreeEnergy_eq fixed candidate target hfixed htarget,
    finiteKL_eq_zero_iff]

/-! ## Fixed-sample Jensen bound -/

/-- Finite weighted Jensen inequality for positive importance weights.  A
product-law IWAE construction can instantiate `sampling` with its fixed-size
sample law; positivity prevents use of `Real.log 0 = 0`. -/
theorem expected_log_weight_le_log_expected_weight
    (sampling : FiniteLaw α) (weight : α → ℝ)
    (hweight : ∀ x, 0 < weight x) :
    ∑ x, sampling x * Real.log (weight x) ≤
      Real.log (∑ x, sampling x * weight x) := by
  have h := strictConcaveOn_log_Ioi.concaveOn.le_map_sum
    (t := Finset.univ) (w := fun x => sampling x) (p := weight)
    (fun x _ => sampling.nonneg x) sampling.sum_one
    (fun x _ => hweight x)
  simpa [smul_eq_mul, Function.comp_def] using h

/-- Independent product law for a fixed number of finite samples. -/
def iidProductLaw (base : FiniteLaw α) (sampleCount : ℕ) :
    FiniteLaw (Fin sampleCount → α) where
  mass sample := ∏ index, base (sample index)
  nonneg sample := Finset.prod_nonneg fun index _ =>
    base.nonneg (sample index)
  sum_one := by
    rw [← Fintype.prod_sum]
    simp [base.sum_one]

@[simp]
theorem iidProductLaw_mass
    (base : FiniteLaw α) (sampleCount : ℕ)
    (sample : Fin sampleCount → α) :
    iidProductLaw base sampleCount sample =
      ∏ index, base (sample index) :=
  rfl

/-- Arithmetic mean of importance weights in one fixed-size sample tuple. -/
noncomputable def sampleMeanWeight (sampleCount : ℕ) (weight : α → ℝ)
    (sample : Fin sampleCount → α) : ℝ :=
  (∑ index, weight (sample index)) / sampleCount

omit [Fintype α] in
/-- A positive sample count and pointwise positive weights make every sample
mean positive. -/
theorem sampleMeanWeight_pos
    (sampleCount : ℕ) [NeZero sampleCount]
    (weight : α → ℝ) (hweight : ∀ x, 0 < weight x)
    (sample : Fin sampleCount → α) :
    0 < sampleMeanWeight sampleCount weight sample := by
  have hcountNat : 0 < sampleCount := Nat.pos_of_ne_zero (NeZero.ne sampleCount)
  have hcountReal : 0 < (sampleCount : ℝ) := by
    exact_mod_cast hcountNat
  exact div_pos
    (Finset.sum_pos (fun index _ => hweight (sample index))
      Finset.univ_nonempty)
    hcountReal

/-- Fixed-sample IWAE Jensen component under the explicit IID product law.
This proves only the finite Jensen bound; identifying the expected sample mean
with model evidence requires a separate importance-ratio theorem. -/
theorem fixedSampleImportanceJensen
    (base : FiniteLaw α) (sampleCount : ℕ) [NeZero sampleCount]
    (weight : α → ℝ) (hweight : ∀ x, 0 < weight x) :
    ∑ sample, iidProductLaw base sampleCount sample *
        Real.log (sampleMeanWeight sampleCount weight sample) ≤
      Real.log (∑ sample, iidProductLaw base sampleCount sample *
        sampleMeanWeight sampleCount weight sample) :=
  expected_log_weight_le_log_expected_weight
    (iidProductLaw base sampleCount)
    (sampleMeanWeight sampleCount weight)
    (sampleMeanWeight_pos sampleCount weight hweight)

/-! ## Finite-channel data processing -/

/-- Swap the coordinates of a finite joint law. -/
def swapLaw (joint : FiniteLaw (α × β)) : FiniteLaw (β × α) where
  mass pair := joint (pair.2, pair.1)
  nonneg pair := joint.nonneg (pair.2, pair.1)
  sum_one := by
    rw [Fintype.sum_prod_type, Finset.sum_comm]
    simpa [Fintype.sum_prod_type] using joint.sum_one

/-- Totalized finite KL is invariant under coordinate swap. -/
theorem finiteKL_swap (actual reference : FiniteLaw (α × β)) :
    finiteKL (swapLaw actual) (swapLaw reference) =
      finiteKL actual reference := by
  unfold finiteKL
  simp only [swapLaw]
  rw [Fintype.sum_prod_type, Fintype.sum_prod_type]
  rw [Finset.sum_comm]

/-- Reverse finite channel at positive predictive mass. -/
noncomputable def reverseKernel
    (prior : FiniteLaw α) (channel : FiniteKernel α β)
    (hpredictive : ∀ y, 0 < channel.predictive prior y) :
    FiniteKernel β α where
  mass y x := channel.posterior prior y (hpredictive y) x
  nonneg y x := (channel.posterior prior y (hpredictive y)).nonneg x
  sum_one y := (channel.posterior prior y (hpredictive y)).sum_one

/-- Prediction followed by the reverse channel is the swapped original joint. -/
theorem reverseKernel_joint
    (prior : FiniteLaw α) (channel : FiniteKernel α β)
    (hpredictive : ∀ y, 0 < channel.predictive prior y) :
    (reverseKernel prior channel hpredictive).joint
        (channel.predictive prior) = swapLaw (channel.joint prior) := by
  apply FiniteLaw.ext_mass
  funext pair
  change channel.predictive prior pair.1 *
      channel.posterior prior pair.1 (hpredictive pair.1) pair.2 =
    prior pair.2 * channel pair.2 pair.1
  rw [mul_comm]
  exact channel.posterior_mul_predictive prior pair.1
    (hpredictive pair.1) pair.2

/-- The conditional KL of a channel with itself is zero. -/
theorem conditionalKL_self
    (prior : FiniteLaw α) (channel : FiniteKernel α β) :
    conditionalKL prior channel channel = 0 := by
  apply Finset.sum_eq_zero
  intro x _
  rw [finiteKL_self, mul_zero]

/-- A shared full-support channel preserves prior KL in the corresponding
joint laws. -/
theorem finiteKL_joint_sameKernel
    (actual reference : FiniteLaw α) (channel : FiniteKernel α β)
    (hreference : ∀ x, 0 < reference x)
    (hchannel : ∀ x y, 0 < channel x y) :
    finiteKL (channel.joint actual) (channel.joint reference) =
      finiteKL actual reference := by
  rw [finiteKL_joint_chain_rule actual reference channel channel hreference
      hchannel,
    conditionalKL_self, add_zero]

/-- Finite-channel KL data-processing inequality under explicit full support.
The assumptions justify both reverse kernels and every logarithmic chain rule;
no claim is made for extended divergence at a zero reference atom. -/
theorem finiteChannel_dataProcessing
    (actual reference : FiniteLaw α) (channel : FiniteKernel α β)
    [Nonempty α]
    (hactual : ∀ x, 0 < actual x)
    (hreference : ∀ x, 0 < reference x)
    (hchannel : ∀ x y, 0 < channel x y) :
    finiteKL (channel.predictive actual) (channel.predictive reference) ≤
      finiteKL actual reference := by
  have hactualPredictive : ∀ y, 0 < channel.predictive actual y := by
    intro y
    simp only [FiniteKernel.predictive_mass]
    exact Finset.sum_pos (fun x _ =>
      mul_pos (hactual x) (hchannel x y)) Finset.univ_nonempty
  have hreferencePredictive : ∀ y, 0 < channel.predictive reference y := by
    intro y
    simp only [FiniteKernel.predictive_mass]
    exact Finset.sum_pos (fun x _ =>
      mul_pos (hreference x) (hchannel x y)) Finset.univ_nonempty
  have hreverseReference : ∀ y x,
      0 < reverseKernel reference channel hreferencePredictive y x := by
    intro y x
    change 0 < reference x * channel x y /
      channel.predictive reference y
    exact div_pos (mul_pos (hreference x) (hchannel x y))
      (hreferencePredictive y)
  have hle := finiteKL_prior_le_joint
    (channel.predictive actual) (channel.predictive reference)
    (reverseKernel actual channel hactualPredictive)
    (reverseKernel reference channel hreferencePredictive)
    hreferencePredictive hreverseReference
  rw [reverseKernel_joint actual channel hactualPredictive,
    reverseKernel_joint reference channel hreferencePredictive,
    finiteKL_swap,
    finiteKL_joint_sameKernel actual reference channel hreference hchannel] at hle
  exact hle

/-! ### Deterministic channel boundaries -/

/-- The deterministic identity channel preserves finite KL exactly.  Its
off-diagonal zero entries show why the positive-channel theorem above does
not cover every normalized finite channel. -/
theorem finiteChannel_identity_preservesKL [DecidableEq α]
    (actual reference : FiniteLaw α) :
    finiteKL (FiniteKernel.identity.predictive actual)
        (FiniteKernel.identity.predictive reference) =
      finiteKL actual reference := by
  rw [FiniteKernel.predictive_identity, FiniteKernel.predictive_identity]

/-- Forgetting every input state sends every law to the same unit point mass.
This is a deterministic coarsening, rather than a positive-noise channel. -/
theorem constantChannel_predictive (law : FiniteLaw α) :
    (FiniteKernel.deterministic (fun _ : α => ())).predictive law =
      FiniteLaw.pointMass () := by
  apply FiniteLaw.ext_mass
  funext x
  cases x
  simp [FiniteKernel.predictive_mass, FiniteKernel.deterministic,
    FiniteLaw.pointMass, law.sum_one]

/-- Complete deterministic coarsening removes all divergence between its
output laws, even when the input laws differ. -/
theorem constantChannel_KL_zero (actual reference : FiniteLaw α) :
    finiteKL
        ((FiniteKernel.deterministic (fun _ : α => ())).predictive actual)
        ((FiniteKernel.deterministic (fun _ : α => ())).predictive reference) = 0 := by
  rw [constantChannel_predictive, constantChannel_predictive, finiteKL_self]

/-- Unequal normalized input laws give a strict deterministic-coarsening
comparison.  No extended-divergence claim is made at singular reference
atoms; this theorem states the repository's totalized finite convention. -/
theorem constantChannel_KL_strict (actual reference : FiniteLaw α)
    (hne : actual ≠ reference) :
    finiteKL
        ((FiniteKernel.deterministic (fun _ : α => ())).predictive actual)
        ((FiniteKernel.deterministic (fun _ : α => ())).predictive reference) <
      finiteKL actual reference := by
  rw [constantChannel_KL_zero]
  exact lt_of_le_of_ne (finiteKL_nonneg actual reference)
    (Ne.symm ((finiteKL_eq_zero_iff actual reference).not.mpr hne))

/-! ## Finite constrained maximum entropy -/

/-- One affine equality constraint on a finite law.  Its statistic has the
prescribed expectation `target`; normalization remains owned by `FiniteLaw`. -/
structure AffineMomentConstraint (α : Type*) where
  statistic : α → ℝ
  target : ℝ

/-- Exact feasibility for a finite list of affine moment constraints. -/
def SatisfiesMomentConstraints
    (law : FiniteLaw α) (constraints : List (AffineMomentConstraint α)) : Prop :=
  ∀ constraint ∈ constraints,
    expectation law constraint.statistic = constraint.target

/-- The signed affine Lagrange potential associated with a finite constraint
list.  Positive temperature scales this potential in the certificate below. -/
noncomputable def constraintPotential
    (constraints : List (AffineMomentConstraint α))
    (multipliers : Fin constraints.length → ℝ) (x : α) : ℝ :=
  ∑ index : Fin constraints.length,
    multipliers index *
      ((constraints.get index).statistic x - (constraints.get index).target)

/-- Independently checkable data for a finite constrained-entropy optimum.
The Gibbs law has full support, the reference is exactly uniform, its signed
potential is a finite affine combination of the listed constraint residuals,
the temperature is strictly positive, and the optimizer is feasible.  This
structure supplies a multiplier; it does not assert automatic dual attainment
from affine feasibility or a Slater condition. -/
structure ConstrainedEntropyCertificate (α : Type*) [Fintype α] [Nonempty α]
    where
  constraints : List (AffineMomentConstraint α)
  multipliers : Fin constraints.length → ℝ
  temperature : ℝ
  temperature_pos : 0 < temperature
  gibbs : GibbsCertificate α
  reference_eq_uniform : gibbs.reference = FiniteLaw.uniform
  potential_eq : ∀ x,
    gibbs.potential x =
      constraintPotential constraints multipliers x / temperature
  optimizer_feasible :
    SatisfiesMomentConstraints gibbs.optimizer constraints

/-- Zero temperature is outside the supplied finite Gibbs-certificate regime.
No division-by-zero convention is used to manufacture a boundary optimizer. -/
theorem zeroTemperature_not_certified [Nonempty α]
    (certificate : ConstrainedEntropyCertificate α) :
    certificate.temperature ≠ 0 :=
  ne_of_gt certificate.temperature_pos

/-- A supplied full-support finite-multiplier certificate exhibits a feasible
entropy maximizer and proves that it is unique.  This is a KKT/certificate
result: neither multiplier existence nor strong duality is inferred from
feasibility. -/
theorem constrainedEntropy_existsUnique_of_certificate [Nonempty α]
    (certificate : ConstrainedEntropyCertificate α) :
    SatisfiesMomentConstraints certificate.gibbs.optimizer
        certificate.constraints ∧
      ∀ candidate : FiniteLaw α,
        SatisfiesMomentConstraints candidate certificate.constraints →
          entropy candidate ≤ entropy certificate.gibbs.optimizer ∧
            (entropy candidate = entropy certificate.gibbs.optimizer ↔
              candidate = certificate.gibbs.optimizer) := by
  have hUniformPos :
      ∀ x, 0 < (FiniteLaw.uniform : FiniteLaw α) x := by
    intro x
    change 0 < ((Fintype.card α : ℝ)⁻¹)
    exact inv_pos.mpr (Nat.cast_pos.mpr Fintype.card_pos)
  have hUniformCrossEntropy :
      ∀ law : FiniteLaw α,
        crossEntropy law (FiniteLaw.uniform : FiniteLaw α) =
          -Real.log ((Fintype.card α : ℝ)⁻¹) := by
    intro law
    unfold crossEntropy FiniteLaw.uniform
    simp_rw [neg_mul]
    rw [Finset.sum_neg_distrib, ← Finset.sum_mul, law.sum_one, one_mul]
  have hFeasiblePotentialZero :
      ∀ law : FiniteLaw α,
        SatisfiesMomentConstraints law certificate.constraints →
          expectation law certificate.gibbs.potential = 0 := by
    intro law hFeasible
    have hConstraintPotential :
        expectation law
            (constraintPotential certificate.constraints
              certificate.multipliers) = 0 := by
      unfold expectation constraintPotential
      simp_rw [Finset.mul_sum]
      rw [Finset.sum_comm]
      apply Finset.sum_eq_zero
      intro index _
      have hMoment := hFeasible
        (certificate.constraints.get index)
        (List.get_mem certificate.constraints index)
      simp only [expectation] at hMoment
      have hCentered :
          (∑ x, law x *
            ((certificate.constraints.get index).statistic x -
              (certificate.constraints.get index).target)) = 0 := by
        simp_rw [mul_sub]
        rw [Finset.sum_sub_distrib, ← Finset.sum_mul, law.sum_one,
          one_mul, hMoment, sub_self]
      calc
        (∑ x, law x *
            (certificate.multipliers index *
              ((certificate.constraints.get index).statistic x -
                (certificate.constraints.get index).target))) =
            certificate.multipliers index *
              ∑ x, law x *
                ((certificate.constraints.get index).statistic x -
                  (certificate.constraints.get index).target) := by
              rw [Finset.mul_sum]
              apply Finset.sum_congr rfl
              intro x _
              ring
        _ = 0 := by rw [hCentered, mul_zero]
    unfold expectation at hConstraintPotential ⊢
    calc
      (∑ x, law x * certificate.gibbs.potential x) =
          ∑ x, (law x *
            constraintPotential certificate.constraints
              certificate.multipliers x) / certificate.temperature := by
            apply Finset.sum_congr rfl
            intro x _
            rw [certificate.potential_eq x]
            ring
      _ = (∑ x, law x *
          constraintPotential certificate.constraints
            certificate.multipliers x) / certificate.temperature := by
            rw [Finset.sum_div]
      _ = 0 := by rw [hConstraintPotential, zero_div]
  refine ⟨certificate.optimizer_feasible, ?_⟩
  intro candidate hCandidateFeasible
  have hCandidatePotential :=
    hFeasiblePotentialZero candidate hCandidateFeasible
  have hOptimizerPotential :=
    hFeasiblePotentialZero certificate.gibbs.optimizer
      certificate.optimizer_feasible
  have hCandidateBound :=
    dvObjective_le_logPartition certificate.gibbs candidate
  have hOptimizerValue := dvObjective_optimizer certificate.gibbs
  have hKLDominates :
      finiteKL certificate.gibbs.optimizer
          (FiniteLaw.uniform : FiniteLaw α) ≤
        finiteKL candidate (FiniteLaw.uniform : FiniteLaw α) := by
    rw [dvObjective, hCandidatePotential,
      certificate.reference_eq_uniform] at hCandidateBound
    rw [dvObjective, hOptimizerPotential,
      certificate.reference_eq_uniform] at hOptimizerValue
    linarith
  constructor
  · rw [finiteKL_eq_crossEntropy_sub_entropy candidate
        (FiniteLaw.uniform : FiniteLaw α) hUniformPos,
      finiteKL_eq_crossEntropy_sub_entropy certificate.gibbs.optimizer
        (FiniteLaw.uniform : FiniteLaw α) hUniformPos,
      hUniformCrossEntropy candidate,
      hUniformCrossEntropy certificate.gibbs.optimizer] at hKLDominates
    linarith
  · constructor
    · intro hEntropy
      have hKLEq :
          finiteKL candidate (FiniteLaw.uniform : FiniteLaw α) =
            finiteKL certificate.gibbs.optimizer
              (FiniteLaw.uniform : FiniteLaw α) := by
        rw [finiteKL_eq_crossEntropy_sub_entropy candidate
              (FiniteLaw.uniform : FiniteLaw α) hUniformPos,
          finiteKL_eq_crossEntropy_sub_entropy certificate.gibbs.optimizer
            (FiniteLaw.uniform : FiniteLaw α) hUniformPos,
          hUniformCrossEntropy candidate,
          hUniformCrossEntropy certificate.gibbs.optimizer,
          hEntropy]
      have hAttains :
          dvObjective certificate.gibbs candidate =
            certificate.gibbs.logPartition := by
        calc
          dvObjective certificate.gibbs candidate =
              -finiteKL candidate
                (FiniteLaw.uniform : FiniteLaw α) := by
                  simp [dvObjective, hCandidatePotential,
                    certificate.reference_eq_uniform]
          _ = -finiteKL certificate.gibbs.optimizer
                (FiniteLaw.uniform : FiniteLaw α) := by rw [hKLEq]
          _ = dvObjective certificate.gibbs
                certificate.gibbs.optimizer := by
                  simp [dvObjective, hOptimizerPotential,
                    certificate.reference_eq_uniform]
          _ = certificate.gibbs.logPartition :=
            dvObjective_optimizer certificate.gibbs
      exact (dvObjective_eq_logPartition_iff certificate.gibbs candidate).mp
        hAttains
    · rintro rfl
      rfl

/-! ### A checkable relative-interior `Fin 3` certificate -/

/-- First moment on the ordered three-state carrier. -/
def fin3FirstMoment : Fin 3 → ℝ := ![0, 1, 2]

/-- Second moment on the ordered three-state carrier. -/
def fin3SecondMoment : Fin 3 → ℝ := ![0, 1, 4]

/-- The uniform `Fin 3` law has first moment `1` and second moment `5 / 3`.
These two affine constraints give a concrete interior moment problem. -/
noncomputable def fin3InteriorMomentConstraints :
    List (AffineMomentConstraint (Fin 3)) :=
  [ { statistic := fin3FirstMoment, target := 1 },
    { statistic := fin3SecondMoment, target := 5 / 3 } ]

/-- Zero multipliers and unit positive temperature certify the full-support
uniform solution of the concrete two-moment `Fin 3` problem. -/
noncomputable def fin3InteriorMomentCertificate :
    ConstrainedEntropyCertificate (Fin 3) where
  constraints := fin3InteriorMomentConstraints
  multipliers _ := 0
  temperature := 1
  temperature_pos := by norm_num
  gibbs := uniformZeroPotentialGibbs
  reference_eq_uniform := rfl
  potential_eq x := by
    simp [uniformZeroPotentialGibbs, constraintPotential]
  optimizer_feasible := by
    intro constraint hConstraint
    simp only [fin3InteriorMomentConstraints, List.mem_cons,
      List.not_mem_nil, or_false] at hConstraint
    rcases hConstraint with rfl | rfl <;>
      norm_num [expectation, uniformZeroPotentialGibbs, FiniteLaw.uniform,
        fin3FirstMoment, fin3SecondMoment, Fin.sum_univ_succ]

/-- The explicit `Fin 3` optimizer is strictly positive, feasible, and the
unique maximum-entropy law among all laws satisfying both moments. -/
theorem fin3InteriorMoment_uniqueEntropyMaximizer :
    (∀ x, 0 < fin3InteriorMomentCertificate.gibbs.optimizer x) ∧
      SatisfiesMomentConstraints
        fin3InteriorMomentCertificate.gibbs.optimizer
        fin3InteriorMomentConstraints ∧
      ∀ candidate : FiniteLaw (Fin 3),
        SatisfiesMomentConstraints candidate fin3InteriorMomentConstraints →
          entropy candidate ≤
              entropy fin3InteriorMomentCertificate.gibbs.optimizer ∧
            (entropy candidate =
                entropy fin3InteriorMomentCertificate.gibbs.optimizer ↔
              candidate = fin3InteriorMomentCertificate.gibbs.optimizer) := by
  refine ⟨fin3InteriorMomentCertificate.gibbs.optimizer_pos, ?_⟩
  exact constrainedEntropy_existsUnique_of_certificate
    fin3InteriorMomentCertificate

/-! ### Boundary support without a full-support Gibbs form -/

/-- Requiring all mass at state zero is an affine boundary constraint. -/
def fin3BoundaryConstraint : AffineMomentConstraint (Fin 3) where
  statistic := ![1, 0, 0]
  target := 1

def fin3BoundaryConstraints : List (AffineMomentConstraint (Fin 3)) :=
  [fin3BoundaryConstraint]

/-- The boundary constraint forces the point mass at zero.  This theorem uses
the restricted feasible support directly and makes no finite-multiplier or
full-support Gibbs assertion. -/
theorem fin3Boundary_feasible_iff_pointMassZero (law : FiniteLaw (Fin 3)) :
    SatisfiesMomentConstraints law fin3BoundaryConstraints ↔
      law = FiniteLaw.pointMass (0 : Fin 3) := by
  constructor
  · intro hFeasible
    have hMoment := hFeasible fin3BoundaryConstraint (by
      simp [fin3BoundaryConstraints])
    norm_num [expectation, fin3BoundaryConstraint,
      Fin.sum_univ_succ] at hMoment
    have hSum := law.sum_one
    norm_num [Fin.sum_univ_succ] at hSum
    have hOne : law (1 : Fin 3) = 0 := by
      linarith [law.nonneg (1 : Fin 3), law.nonneg (2 : Fin 3)]
    have hTwo : law (2 : Fin 3) = 0 := by
      linarith [law.nonneg (1 : Fin 3), law.nonneg (2 : Fin 3)]
    apply FiniteLaw.ext_mass
    funext x
    fin_cases x
    · simp [FiniteLaw.pointMass, hMoment]
    · simp [FiniteLaw.pointMass, hOne]
    · simp [FiniteLaw.pointMass, hTwo]
  · rintro rfl
    intro constraint hConstraint
    simp only [fin3BoundaryConstraints, List.mem_singleton] at hConstraint
    subst constraint
    norm_num [expectation, fin3BoundaryConstraint, FiniteLaw.pointMass,
      Fin.sum_univ_succ]

/-- The support-forcing point mass is the unique feasible entropy maximizer.
This is the boundary result; it is intentionally separate from the positive-
temperature full-support certificate theorem. -/
theorem fin3Boundary_uniqueEntropyMaximizer :
    SatisfiesMomentConstraints (FiniteLaw.pointMass (0 : Fin 3))
        fin3BoundaryConstraints ∧
      ∀ candidate : FiniteLaw (Fin 3),
        SatisfiesMomentConstraints candidate fin3BoundaryConstraints →
          entropy candidate ≤ entropy (FiniteLaw.pointMass (0 : Fin 3)) ∧
            (entropy candidate = entropy (FiniteLaw.pointMass (0 : Fin 3)) ↔
              candidate = FiniteLaw.pointMass (0 : Fin 3)) := by
  constructor
  · exact (fin3Boundary_feasible_iff_pointMassZero
      (FiniteLaw.pointMass (0 : Fin 3))).2 rfl
  · intro candidate hFeasible
    have hCandidate :=
      (fin3Boundary_feasible_iff_pointMassZero candidate).1 hFeasible
    subst candidate
    exact ⟨le_rfl, ⟨fun _ => rfl, fun _ => rfl⟩⟩

/-! ### Infeasible and redundant constraints -/

/-- An impossible affine constraint: a probability law cannot place mass two
on one atom. -/
def fin3InfeasibleConstraint : AffineMomentConstraint (Fin 3) where
  statistic := ![1, 0, 0]
  target := 2

def fin3InfeasibleConstraints : List (AffineMomentConstraint (Fin 3)) :=
  [fin3InfeasibleConstraint]

/-- Infeasibility is discharged before any multiplier, entropy, or duality
claim is considered. -/
theorem fin3Infeasible_no_feasibleLaw :
    ¬ ∃ law : FiniteLaw (Fin 3),
      SatisfiesMomentConstraints law fin3InfeasibleConstraints := by
  rintro ⟨law, hFeasible⟩
  have hMoment := hFeasible fin3InfeasibleConstraint (by
    simp [fin3InfeasibleConstraints])
  norm_num [expectation, fin3InfeasibleConstraint,
    Fin.sum_univ_succ] at hMoment
  linarith [law.mass_le_one (0 : Fin 3)]

/-- The first-moment-equals-one constraint, named so duplication is visible. -/
def fin3MeanOneConstraint : AffineMomentConstraint (Fin 3) where
  statistic := fin3FirstMoment
  target := 1

/-- A finite list containing the same affine equality twice. -/
def fin3RedundantConstraints : List (AffineMomentConstraint (Fin 3)) :=
  [fin3MeanOneConstraint, fin3MeanOneConstraint]

/-- Duplicating an affine moment equality does not change the feasible set. -/
theorem fin3Redundant_feasible_iff (law : FiniteLaw (Fin 3)) :
    SatisfiesMomentConstraints law fin3RedundantConstraints ↔
      expectation law fin3FirstMoment = 1 := by
  simp [SatisfiesMomentConstraints, fin3RedundantConstraints,
    fin3MeanOneConstraint]

/-! ## Rate--distortion weak duality -/

/-- Expected distortion under a finite source--code joint law. -/
def expectedDistortion
    (joint : FiniteLaw (α × β)) (distortion : α → β → ℝ) : ℝ :=
  ∑ pair, joint pair * distortion pair.1 pair.2

/-- Finite rate--distortion Lagrangian. -/
noncomputable def rateDistortionLagrangian
    (joint : FiniteLaw (α × β)) (distortion : α → β → ℝ)
    (multiplier : ℝ) : ℝ :=
  mutualInformation joint + multiplier * expectedDistortion joint distortion

/-- Weak duality for any separately certified rate and distortion lower
bounds.  Optimizer existence is intentionally not asserted. -/
theorem rateDistortion_weak_duality
    (joint : FiniteLaw (α × β)) (distortion : α → β → ℝ)
    (multiplier rateLower distortionLower : ℝ)
    (hmultiplier : 0 ≤ multiplier)
    (hrate : rateLower ≤ mutualInformation joint)
    (hdistortion : distortionLower ≤ expectedDistortion joint distortion) :
    rateLower + multiplier * distortionLower ≤
      rateDistortionLagrangian joint distortion multiplier := by
  unfold rateDistortionLagrangian
  exact add_le_add hrate (mul_le_mul_of_nonneg_left hdistortion hmultiplier)

/-! ### Actual finite rate--distortion optimization -/

/-- Relative support, including shared zero atoms, suffices for the finite
logarithmic KL identity. -/
theorem finiteKL_eq_crossEntropy_sub_entropy_of_relativeSupport
    (p q : FiniteLaw α) (hsupport : ∀ x, p x ≠ 0 → 0 < q x) :
    finiteKL p q = crossEntropy p q - entropy p := by
  have hpoint : ∀ x,
      q x * klFun (p x / q x) =
        (-p x * Real.log (q x) - Real.negMulLog (p x)) + (q x - p x) := by
    intro x
    by_cases hp : p x = 0
    · simp [hp, klFun_zero]
    · exact weighted_klFun_eq_log_score (hsupport x hp)
  simp_rw [finiteKL, hpoint]
  rw [Finset.sum_add_distrib, Finset.sum_sub_distrib]
  have hnorm : (∑ x : α, (q x - p x)) = 0 := by
    rw [Finset.sum_sub_distrib, q.sum_one, p.sum_one, sub_self]
  rw [hnorm, add_zero]
  rfl

/-- Joint support is contained in the support of the product marginals. -/
theorem joint_supported_by_productMarginals (joint : FiniteLaw (α × β)) :
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

/-- The entropy expression for finite mutual information is valid even at
unused marginal states.  Zero joint atoms remove the corresponding log
terms before any logarithmic product identity is invoked. -/
theorem mutualInformation_eq_entropy_marginals_without_support
    (joint : FiniteLaw (α × β)) :
    mutualInformation joint =
      entropy joint.fstMarginal + entropy joint.sndMarginal - entropy joint := by
  have hlog : ∀ xy : α × β,
      -joint xy * Real.log ((joint.fstMarginal.product joint.sndMarginal) xy) =
        -joint xy * Real.log (joint.fstMarginal xy.1) +
          -joint xy * Real.log (joint.sndMarginal xy.2) := by
    intro xy
    by_cases hmass : joint xy = 0
    · simp [hmass]
    · have hproduct := joint_supported_by_productMarginals joint xy hmass
      have hfst : joint.fstMarginal xy.1 ≠ 0 := by
        intro hzero
        change 0 < joint.fstMarginal xy.1 * joint.sndMarginal xy.2 at hproduct
        simp [hzero] at hproduct
      have hsnd : joint.sndMarginal xy.2 ≠ 0 := by
        intro hzero
        change 0 < joint.fstMarginal xy.1 * joint.sndMarginal xy.2 at hproduct
        simp [hzero] at hproduct
      change -joint xy * Real.log
        (joint.fstMarginal xy.1 * joint.sndMarginal xy.2) = _
      rw [Real.log_mul hfst hsnd, mul_add]
  have hcross :
      crossEntropy joint (joint.fstMarginal.product joint.sndMarginal) =
        entropy joint.fstMarginal + entropy joint.sndMarginal := by
    simp only [crossEntropy, hlog, Finset.sum_add_distrib,
      entropy, Fintype.sum_prod_type]
    congr 1
    · simp [Real.negMulLog_eq_neg, FiniteLaw.fstMarginal,
        neg_mul, ← Finset.sum_mul, Finset.sum_neg_distrib]
    · rw [Finset.sum_comm]
      simp [Real.negMulLog_eq_neg, FiniteLaw.sndMarginal,
        neg_mul, ← Finset.sum_mul, Finset.sum_neg_distrib]
  rw [mutualInformation,
    finiteKL_eq_crossEntropy_sub_entropy_of_relativeSupport _ _
      (joint_supported_by_productMarginals joint), hcross]

/-- A fixed-source joint is feasible exactly when its distortion respects the
budget.  This predicate imposes constraints, not an optimizer certificate. -/
def RateDistortionFeasible (source : FiniteLaw α) (distortion : α → β → ℝ)
    (budget : ℝ) (joint : FiniteLaw (α × β)) : Prop :=
  joint.fstMarginal = source ∧ expectedDistortion joint distortion ≤ budget

/-- Coordinate realization of the same feasible set on the existing finite
law's mass function.  No second probability carrier is introduced. -/
def rateDistortionFeasibleMasses (source : FiniteLaw α)
    (distortion : α → β → ℝ) (budget : ℝ) : Set (α × β → ℝ) :=
  {weights | (∀ xy, 0 ≤ weights xy) ∧
    (∀ x, ∑ y : β, weights (x, y) = source x) ∧
    (∑ xy : α × β, weights xy * distortion xy.1 xy.2) ≤ budget}

/-- The entropy-form information objective is continuous on all mass
coordinates, including boundary atoms. -/
noncomputable def mutualInformationOfMasses (weights : α × β → ℝ) : ℝ :=
  (∑ x : α, Real.negMulLog (∑ y : β, weights (x, y))) +
    (∑ y : β, Real.negMulLog (∑ x : α, weights (x, y))) -
      ∑ xy : α × β, Real.negMulLog (weights xy)

theorem continuous_mutualInformationOfMasses :
    Continuous (mutualInformationOfMasses : (α × β → ℝ) → ℝ) := by
  unfold mutualInformationOfMasses
  fun_prop

theorem mutualInformationOfMasses_eq (joint : FiniteLaw (α × β)) :
    mutualInformationOfMasses joint.mass = mutualInformation joint := by
  rw [mutualInformation_eq_entropy_marginals_without_support]
  rfl

/-- The coordinate constraints form a closed set. -/
theorem isClosed_rateDistortionFeasibleMasses (source : FiniteLaw α)
    (distortion : α → β → ℝ) (budget : ℝ) :
    IsClosed (rateDistortionFeasibleMasses source distortion budget) := by
  unfold rateDistortionFeasibleMasses
  simp only [Set.ofPred_and, Set.ofPred_forall]
  refine (isClosed_iInter fun xy => ?_).inter
    ((isClosed_iInter fun x => ?_).inter ?_)
  · exact isClosed_le continuous_const (continuous_apply xy)
  · exact isClosed_eq (by fun_prop) continuous_const
  · exact isClosed_le (by fun_prop) continuous_const

/-- Every feasible coordinate is a normalized finite law. -/
def rateDistortionLawOfMasses (source : FiniteLaw α)
    (distortion : α → β → ℝ) (budget : ℝ) (weights : α × β → ℝ)
    (hweights : weights ∈ rateDistortionFeasibleMasses source distortion budget) :
    FiniteLaw (α × β) where
  mass := weights
  nonneg := hweights.1
  sum_one := by
    rw [Fintype.sum_prod_type]
    simp_rw [hweights.2.1]
    exact source.sum_one

theorem rateDistortionLawOfMasses_feasible (source : FiniteLaw α)
    (distortion : α → β → ℝ) (budget : ℝ) (weights : α × β → ℝ)
    (hweights : weights ∈ rateDistortionFeasibleMasses source distortion budget) :
    RateDistortionFeasible source distortion budget
      (rateDistortionLawOfMasses source distortion budget weights hweights) := by
  refine ⟨?_, hweights.2.2⟩
  apply FiniteLaw.ext_mass
  funext x
  exact hweights.2.1 x

theorem rateDistortionFeasible_mass_mem (source : FiniteLaw α)
    (distortion : α → β → ℝ) (budget : ℝ) (joint : FiniteLaw (α × β))
    (hjoint : RateDistortionFeasible source distortion budget joint) :
    joint.mass ∈ rateDistortionFeasibleMasses source distortion budget := by
  refine ⟨joint.nonneg, ?_, hjoint.2⟩
  intro x
  exact congrArg (fun law : FiniteLaw α => law x) hjoint.1

/-- Fixed source mass and nonnegativity bound each coordinate by one, so the
closed feasible set is compact even on faces with zero atoms. -/
theorem isCompact_rateDistortionFeasibleMasses (source : FiniteLaw α)
    (distortion : α → β → ℝ) (budget : ℝ) :
    IsCompact (rateDistortionFeasibleMasses source distortion budget) := by
  classical
  apply (isCompact_Icc : IsCompact
    (Set.Icc (fun _ : α × β => (0 : ℝ)) (fun _ => (1 : ℝ)))).of_isClosed_subset
    (isClosed_rateDistortionFeasibleMasses source distortion budget)
  intro weights hweights
  refine ⟨hweights.1, ?_⟩
  rintro ⟨x, y⟩
  calc
    weights (x, y) ≤ ∑ z : β, weights (x, z) :=
      Finset.single_le_sum (fun z _ => hweights.1 (x, z)) (Finset.mem_univ y)
    _ = source x := hweights.2.1 x
    _ ≤ 1 := source.mass_le_one x

/-- Every nonempty finite fixed-source distortion problem has an attained
information minimum.  Existence follows from compactness and continuity,
without a supplied optimizer, multiplier, or full-support certificate. -/
theorem rateDistortion_exists_minimizer (source : FiniteLaw α)
    (distortion : α → β → ℝ) (budget : ℝ)
    (hfeasible : ∃ joint, RateDistortionFeasible source distortion budget joint) :
    ∃ optimizer : FiniteLaw (α × β),
      RateDistortionFeasible source distortion budget optimizer ∧
        ∀ candidate : FiniteLaw (α × β),
          RateDistortionFeasible source distortion budget candidate →
            mutualInformation optimizer ≤ mutualInformation candidate := by
  rcases hfeasible with ⟨witness, hwitness⟩
  have hnonempty : (rateDistortionFeasibleMasses source distortion budget).Nonempty :=
    ⟨witness.mass, rateDistortionFeasible_mass_mem source distortion budget witness hwitness⟩
  obtain ⟨weights, hweights, hminimum⟩ :=
    (isCompact_rateDistortionFeasibleMasses source distortion budget).exists_isMinOn
      hnonempty continuous_mutualInformationOfMasses.continuousOn
  let optimizer := rateDistortionLawOfMasses source distortion budget weights hweights
  refine ⟨optimizer,
    rateDistortionLawOfMasses_feasible source distortion budget weights hweights, ?_⟩
  intro candidate hcandidate
  have h := hminimum (rateDistortionFeasible_mass_mem source distortion budget
    candidate hcandidate)
  change mutualInformationOfMasses optimizer.mass ≤
    mutualInformationOfMasses candidate.mass at h
  simpa only [mutualInformationOfMasses_eq] using h

/-- The Lagrangian dual value is an infimum over every joint with the fixed
source marginal.  The distortion constraint enters through its multiplier;
no component lower bound or minimizing law is assumed. -/
noncomputable def rateDistortionDualValue (source : FiniteLaw α)
    (distortion : α → β → ℝ) (budget multiplier : ℝ) : ℝ :=
  sInf {value | ∃ joint : FiniteLaw (α × β), joint.fstMarginal = source ∧
    value = rateDistortionLagrangian joint distortion multiplier - multiplier * budget}

theorem expectedDistortion_nonneg (joint : FiniteLaw (α × β))
    (distortion : α → β → ℝ) (hdistortion : ∀ x y, 0 ≤ distortion x y) :
    0 ≤ expectedDistortion joint distortion :=
  Finset.sum_nonneg fun xy _ => mul_nonneg (joint.nonneg xy)
    (hdistortion xy.1 xy.2)

theorem rateDistortionDual_bddBelow (source : FiniteLaw α)
    (distortion : α → β → ℝ) (budget multiplier : ℝ)
    (hdistortion : ∀ x y, 0 ≤ distortion x y) (hmultiplier : 0 ≤ multiplier) :
    BddBelow {value | ∃ joint : FiniteLaw (α × β), joint.fstMarginal = source ∧
      value = rateDistortionLagrangian joint distortion multiplier - multiplier * budget} := by
  refine ⟨-multiplier * budget, ?_⟩
  rintro value ⟨joint, _, rfl⟩
  unfold rateDistortionLagrangian
  have hMI := mutualInformation_nonneg joint
  have hdist := mul_nonneg hmultiplier (expectedDistortion_nonneg joint distortion hdistortion)
  linarith

/-- Genuine weak duality: the infimum-derived dual value is a lower bound on
the information of every distortion-feasible fixed-source joint. -/
theorem rateDistortionDual_le_feasible_information (source : FiniteLaw α)
    (distortion : α → β → ℝ) (budget multiplier : ℝ)
    (hdistortion : ∀ x y, 0 ≤ distortion x y) (hmultiplier : 0 ≤ multiplier)
    (joint : FiniteLaw (α × β))
    (hjoint : RateDistortionFeasible source distortion budget joint) :
    rateDistortionDualValue source distortion budget multiplier ≤ mutualInformation joint := by
  have hbound := rateDistortionDual_bddBelow source distortion budget multiplier
    hdistortion hmultiplier
  calc
    rateDistortionDualValue source distortion budget multiplier ≤
        rateDistortionLagrangian joint distortion multiplier - multiplier * budget :=
      csInf_le hbound ⟨joint, hjoint.1, rfl⟩
    _ ≤ mutualInformation joint := by
      unfold rateDistortionLagrangian
      have h := mul_le_mul_of_nonneg_left hjoint.2 hmultiplier
      linarith

/-- Zero multiplier gives dual value zero, witnessed by any independent
source--code law.  This remains a dual statement even at infeasible budgets. -/
theorem rateDistortionDual_zeroMultiplier [Nonempty β] (source : FiniteLaw α)
    (distortion : α → β → ℝ) (budget : ℝ) :
    rateDistortionDualValue source distortion budget 0 = 0 := by
  classical
  let witness := source.product (FiniteLaw.pointMass (Classical.arbitrary β))
  have hsource : witness.fstMarginal = source := FiniteLaw.product_fstMarginal _ _
  have hwitness : rateDistortionLagrangian witness distortion 0 - 0 * budget = 0 := by
    simp [witness, rateDistortionLagrangian, mutualInformation_product_eq_zero]
  have hbounded : BddBelow {value | ∃ joint : FiniteLaw (α × β),
      joint.fstMarginal = source ∧
        value = rateDistortionLagrangian joint distortion 0 - 0 * budget} := by
    refine ⟨0, ?_⟩
    rintro value ⟨joint, _, rfl⟩
    simpa [rateDistortionLagrangian] using mutualInformation_nonneg joint
  apply le_antisymm
  · change sInf _ ≤ 0
    apply csInf_le hbounded
    exact ⟨witness, hsource, hwitness.symm⟩
  · change 0 ≤ sInf _
    refine le_csInf ?_ ?_
    · exact ⟨0, witness, hsource, hwitness.symm⟩
    · rintro value ⟨joint, _, rfl⟩
      simpa [rateDistortionLagrangian] using mutualInformation_nonneg joint

/-- A negative budget cannot be met by a nonnegative distortion. -/
theorem rateDistortion_infeasible_of_negativeBudget (source : FiniteLaw α)
    (distortion : α → β → ℝ) (budget : ℝ)
    (hdistortion : ∀ x y, 0 ≤ distortion x y) (hbudget : budget < 0) :
    ¬ ∃ joint, RateDistortionFeasible source distortion budget joint := by
  rintro ⟨joint, hjoint⟩
  have hnonneg := expectedDistortion_nonneg joint distortion hdistortion
  linarith [hjoint.2]

/-! ### Boolean Hamming-distortion witnesses -/

/-- Unit Hamming distortion on a Boolean source and reproduction alphabet. -/
def boolHammingDistortion (source code : Bool) : ℝ := if source = code then 0 else 1

theorem boolHammingDistortion_nonneg (source code : Bool) :
    0 ≤ boolHammingDistortion source code := by
  unfold boolHammingDistortion
  split <;> norm_num

/-- Every independent reproduction of a fair Boolean source has distortion
one half, regardless of the reproduction law. -/
theorem boolIndependent_distortion (code : FiniteLaw Bool) :
    expectedDistortion ((FiniteLaw.uniform : FiniteLaw Bool).product code)
      boolHammingDistortion = 1 / 2 := by
  have hsum : code false + code true = 1 := by
    have h := code.sum_one
    rw [Fintype.sum_bool] at h
    linarith
  simp [expectedDistortion, FiniteLaw.product, boolHammingDistortion,
    FiniteLaw.uniform, Fintype.sum_prod_type]
  linarith

/-- Above the independent-reproduction threshold, every independent code law
is a genuine information minimizer. -/
theorem boolIndependent_minimizer (budget : ℝ) (hbudget : (1 : ℝ) / 2 ≤ budget)
    (code : FiniteLaw Bool) :
    RateDistortionFeasible FiniteLaw.uniform boolHammingDistortion budget
        (FiniteLaw.uniform.product code) ∧
      ∀ candidate : FiniteLaw (Bool × Bool),
        RateDistortionFeasible FiniteLaw.uniform boolHammingDistortion budget candidate →
          mutualInformation ((FiniteLaw.uniform : FiniteLaw Bool).product code) ≤
            mutualInformation candidate := by
  refine ⟨⟨FiniteLaw.product_fstMarginal _ _, ?_⟩, ?_⟩
  · rw [boolIndependent_distortion]
    exact hbudget
  · intro candidate _
    rw [mutualInformation_product_eq_zero]
    exact mutualInformation_nonneg candidate

/-- At budget one half the information minimizer is not unique: constant
false and constant true reproductions have distinct joint laws. -/
theorem boolHalfBudget_distinct_minimizers :
    ∃ left right : FiniteLaw (Bool × Bool), left ≠ right ∧
      (RateDistortionFeasible FiniteLaw.uniform boolHammingDistortion (1 / 2) left ∧
        ∀ candidate, RateDistortionFeasible FiniteLaw.uniform boolHammingDistortion
          (1 / 2) candidate → mutualInformation left ≤ mutualInformation candidate) ∧
      (RateDistortionFeasible FiniteLaw.uniform boolHammingDistortion (1 / 2) right ∧
        ∀ candidate, RateDistortionFeasible FiniteLaw.uniform boolHammingDistortion
          (1 / 2) candidate → mutualInformation right ≤ mutualInformation candidate) := by
  refine ⟨FiniteLaw.uniform.product (FiniteLaw.pointMass false),
    FiniteLaw.uniform.product (FiniteLaw.pointMass true), ?_,
    boolIndependent_minimizer _ le_rfl _, boolIndependent_minimizer _ le_rfl _⟩
  intro heq
  have hatom := congrArg (fun joint : FiniteLaw (Bool × Bool) => joint (false, false)) heq
  norm_num [FiniteLaw.product, FiniteLaw.uniform, FiniteLaw.pointMass] at hatom

/-- A nondegenerate binary-symmetric joint: fair source and code marginals,
with crossover probability one quarter. -/
noncomputable def boolQuarterDistortionJoint : FiniteLaw (Bool × Bool) where
  mass xy := if xy.1 = xy.2 then 3 / 8 else 1 / 8
  nonneg xy := by split <;> norm_num
  sum_one := by
    simp [Fintype.sum_prod_type]
    norm_num

theorem boolQuarterDistortionJoint_fstMarginal :
    boolQuarterDistortionJoint.fstMarginal = FiniteLaw.uniform := by
  apply FiniteLaw.ext_mass
  funext x
  cases x <;> norm_num [FiniteLaw.fstMarginal, boolQuarterDistortionJoint,
    FiniteLaw.uniform, Fintype.sum_bool]

theorem boolQuarterDistortionJoint_feasible :
    RateDistortionFeasible FiniteLaw.uniform boolHammingDistortion (1 / 4)
      boolQuarterDistortionJoint := by
  refine ⟨boolQuarterDistortionJoint_fstMarginal, ?_⟩
  norm_num [expectedDistortion, boolQuarterDistortionJoint, boolHammingDistortion,
    Fintype.sum_prod_type, Fintype.sum_bool]

/-- Below one-half distortion, every feasible fair-source joint has strictly
positive information.  A zero-information joint would be independent and
therefore have distortion one half. -/
theorem boolFeasible_information_pos (budget : ℝ) (hbudget : budget < (1 : ℝ) / 2)
    (joint : FiniteLaw (Bool × Bool))
    (hjoint : RateDistortionFeasible FiniteLaw.uniform boolHammingDistortion budget joint) :
    0 < mutualInformation joint := by
  by_contra hpositive
  have hzero : mutualInformation joint = 0 :=
    le_antisymm (le_of_not_gt hpositive) (mutualInformation_nonneg joint)
  have hindependent := (mutualInformation_eq_zero_iff joint).mp hzero
  have hdistortion : expectedDistortion joint boolHammingDistortion = 1 / 2 := by
    rw [hindependent, hjoint.1]
    exact boolIndependent_distortion joint.sndMarginal
  linarith [hjoint.2]

/-- An informative interior-budget problem has an attained, strictly
positive information optimum.  Its existence is the compactness theorem,
not a declaration that the explicit crossover witness is optimal. -/
theorem boolQuarterBudget_exists_positive_minimizer :
    ∃ optimizer : FiniteLaw (Bool × Bool),
      RateDistortionFeasible FiniteLaw.uniform boolHammingDistortion (1 / 4) optimizer ∧
        0 < mutualInformation optimizer ∧
          ∀ candidate, RateDistortionFeasible FiniteLaw.uniform boolHammingDistortion
            (1 / 4) candidate → mutualInformation optimizer ≤ mutualInformation candidate := by
  obtain ⟨optimizer, hfeasible, hminimum⟩ := rateDistortion_exists_minimizer
    (FiniteLaw.uniform : FiniteLaw Bool) boolHammingDistortion (1 / 4)
      ⟨boolQuarterDistortionJoint, boolQuarterDistortionJoint_feasible⟩
  exact ⟨optimizer, hfeasible,
    boolFeasible_information_pos _ (by norm_num) optimizer hfeasible, hminimum⟩

/-- Perfect reproduction of a fair Boolean source. -/
noncomputable def boolZeroDistortionJoint : FiniteLaw (Bool × Bool) where
  mass xy := if xy.1 = xy.2 then 1 / 2 else 0
  nonneg xy := by split <;> norm_num
  sum_one := by simp [Fintype.sum_prod_type]

theorem boolZeroDistortionJoint_feasible :
    RateDistortionFeasible FiniteLaw.uniform boolHammingDistortion 0
      boolZeroDistortionJoint := by
  refine ⟨?_, ?_⟩
  · apply FiniteLaw.ext_mass
    funext x
    cases x <;> norm_num [FiniteLaw.fstMarginal, boolZeroDistortionJoint,
      FiniteLaw.uniform, Fintype.sum_bool]
  · norm_num [expectedDistortion, boolZeroDistortionJoint, boolHammingDistortion,
      Fintype.sum_prod_type, Fintype.sum_bool]

/-- Zero budget forces zero mass on both mismatched atoms, so the fair-source
perfect-reproduction law is the unique feasible law and hence the unique
minimizer.  Uniqueness is derived from constraints rather than asserted. -/
theorem boolZeroBudget_unique_feasible (joint : FiniteLaw (Bool × Bool))
    (hjoint : RateDistortionFeasible FiniteLaw.uniform boolHammingDistortion 0 joint) :
    joint = boolZeroDistortionJoint := by
  have hoffdiag : joint (true, false) + joint (false, true) ≤ 0 := by
    simpa [expectedDistortion, boolHammingDistortion, Fintype.sum_prod_type]
      using hjoint.2
  have htf : joint (true, false) = 0 := by
    linarith [joint.nonneg (true, false), joint.nonneg (false, true)]
  have hft : joint (false, true) = 0 := by
    linarith [joint.nonneg (true, false), joint.nonneg (false, true)]
  have htrue := congrArg (fun law : FiniteLaw Bool => law true) hjoint.1
  have hfalse := congrArg (fun law : FiniteLaw Bool => law false) hjoint.1
  have htt : joint (true, true) = 1 / 2 := by
    simpa [FiniteLaw.fstMarginal, FiniteLaw.uniform, htf] using htrue
  have hff : joint (false, false) = 1 / 2 := by
    simpa [FiniteLaw.fstMarginal, FiniteLaw.uniform, hft] using hfalse
  apply FiniteLaw.ext_mass
  funext xy
  rcases xy with ⟨x, y⟩
  cases x <;> cases y <;> simp [boolZeroDistortionJoint, htf, hft, htt, hff]

/-! ## Gibbs maximum entropy under a mean-energy constraint -/

/-- Unnormalized partition function `Z(β) = ∑ exp(-β E)`. -/
noncomputable def energyPartition (E : α → ℝ) (β : ℝ) : ℝ :=
  ∑ x, Real.exp (-β * E x)

/-- The energy partition function is strictly positive. -/
theorem energyPartition_pos [Nonempty α] (E : α → ℝ) (β : ℝ) :
    0 < energyPartition E β :=
  Finset.sum_pos (fun _ _ => Real.exp_pos _) Finset.univ_nonempty

/-- The Gibbs law `p_β(x) = exp(-β E x) / Z(β)`. -/
noncomputable def energyGibbsLaw [Nonempty α] (E : α → ℝ) (β : ℝ) :
    FiniteLaw α where
  mass x := Real.exp (-β * E x) / energyPartition E β
  nonneg x := div_nonneg (Real.exp_pos _).le (energyPartition_pos E β).le
  sum_one := by
    rw [← Finset.sum_div]
    exact div_self (energyPartition_pos E β).ne'

/-- Every atom of the Gibbs law is positive. -/
theorem energyGibbsLaw_pos [Nonempty α] (E : α → ℝ) (β : ℝ) (x : α) :
    0 < energyGibbsLaw E β x :=
  div_pos (Real.exp_pos _) (energyPartition_pos E β)

/-- Entropy decomposition against the Gibbs law:
`H(q) = β⟨E⟩_q + log Z - KL(q ‖ p_β)`. -/
theorem entropy_eq_energy_add_logPartition_sub_kl [Nonempty α]
    (E : α → ℝ) (β : ℝ) (q : FiniteLaw α) :
    entropy q = β * expectation q E + Real.log (energyPartition E β) -
      finiteKL q (energyGibbsLaw E β) := by
  rw [finiteKL_eq_crossEntropy_sub_entropy q _ (energyGibbsLaw_pos E β)]
  have hlog : ∀ x, -(q x) * Real.log (energyGibbsLaw E β x) =
      q x * (β * E x) + q x * Real.log (energyPartition E β) := by
    intro x
    change -(q x) * Real.log (Real.exp (-β * E x) / energyPartition E β) = _
    rw [Real.log_div (Real.exp_pos _).ne' (energyPartition_pos E β).ne',
      Real.log_exp]
    ring
  have hce : crossEntropy q (energyGibbsLaw E β) =
      β * expectation q E + Real.log (energyPartition E β) := by
    unfold crossEntropy expectation
    rw [Finset.sum_congr rfl fun x _ => hlog x, Finset.sum_add_distrib,
      ← Finset.sum_mul, q.sum_one, one_mul, Finset.mul_sum]
    congr 1
    refine Finset.sum_congr rfl fun x _ => by ring
  rw [hce]
  ring

/-- Gibbs maximum entropy: among all finite laws with the same mean energy as
`p_β`, the Gibbs law has maximal entropy, and uniquely so. -/
theorem energyGibbs_maxEntropy [Nonempty α] (E : α → ℝ) (β : ℝ)
    (q : FiniteLaw α)
    (hq : expectation q E = expectation (energyGibbsLaw E β) E) :
    entropy q ≤ entropy (energyGibbsLaw E β) ∧
      (entropy q = entropy (energyGibbsLaw E β) ↔ q = energyGibbsLaw E β) := by
  have hq' := entropy_eq_energy_add_logPartition_sub_kl E β q
  have hg := entropy_eq_energy_add_logPartition_sub_kl E β
    (energyGibbsLaw E β)
  rw [finiteKL_self] at hg
  rw [hq] at hq'
  refine ⟨?_, ?_⟩
  · linarith [finiteKL_nonneg q (energyGibbsLaw E β)]
  · rw [← finiteKL_eq_zero_iff]
    constructor <;> intro h <;> linarith

/-- Strict form: a mean-energy-matched law different from `p_β` has strictly
smaller entropy. -/
theorem energyGibbs_entropy_lt_of_ne [Nonempty α] (E : α → ℝ) (β : ℝ)
    (q : FiniteLaw α)
    (hq : expectation q E = expectation (energyGibbsLaw E β) E)
    (hne : q ≠ energyGibbsLaw E β) :
    entropy q < entropy (energyGibbsLaw E β) :=
  lt_of_le_of_ne (energyGibbs_maxEntropy E β q hq).1
    fun h => hne ((energyGibbs_maxEntropy E β q hq).2.mp h)

/-- With the zero energy, the Gibbs law is uniform. -/
theorem energyGibbsLaw_zero_energy [Nonempty α] (β : ℝ) :
    energyGibbsLaw (fun _ : α => (0 : ℝ)) β = FiniteLaw.uniform := by
  apply FiniteLaw.ext_mass
  funext x
  simp [energyGibbsLaw, energyPartition, FiniteLaw.uniform]

/-- Strict constrained witness on `Bool`: with zero energy every law meets the
mean-energy constraint, and the biased law has entropy strictly below the
Gibbs (uniform) law. -/
theorem boolBiased_entropy_lt_zeroEnergyGibbs (β : ℝ) :
    entropy boolBiased <
      entropy (energyGibbsLaw (fun _ : Bool => (0 : ℝ)) β) := by
  have hne : boolBiased ≠ energyGibbsLaw (fun _ : Bool => (0 : ℝ)) β := by
    rw [energyGibbsLaw_zero_energy]
    intro h
    have := congrArg (fun r : FiniteLaw Bool => r.mass true) h
    simp [boolBiased, FiniteLaw.uniform] at this
    norm_num at this
  refine energyGibbs_entropy_lt_of_ne _ β boolBiased ?_ hne
  simp [expectation]

/-! ## Helmholtz free energy on finite laws

For energies `E` and temperature `T > 0`, the Gibbs law `exp (-E/T) / Z(T)`
satisfies the exact Helmholtz decomposition
`⟨E⟩_q - T H(q) = F(T) + T KL(q ‖ p_T)` with `F(T) = -T log Z(T)`.  This is a
finite-law identification of `F` with a variational free energy; it does not
alter the abstract `dF/dT = -S` statement for unspecified `U, S`. -/

/-- Partition function `Z(T) = ∑ exp (-E x / T)`. -/
noncomputable def helmholtzPartition (E : α → ℝ) (T : ℝ) : ℝ :=
  ∑ x, Real.exp (-E x / T)

/-- Helmholtz free energy `F(T) = -T log Z(T)`. -/
noncomputable def helmholtzFreeEnergy (E : α → ℝ) (T : ℝ) : ℝ :=
  -T * Real.log (helmholtzPartition E T)

theorem helmholtzPartition_pos [Nonempty α] (E : α → ℝ) (T : ℝ) :
    0 < helmholtzPartition E T :=
  Finset.sum_pos (fun _ _ => Real.exp_pos _) Finset.univ_nonempty

/-- Gibbs law with mass `exp (-E x / T) / Z(T)`. -/
noncomputable def helmholtzGibbsLaw [Nonempty α] (E : α → ℝ) (T : ℝ) :
    FiniteLaw α where
  mass x := Real.exp (-E x / T) / helmholtzPartition E T
  nonneg x := div_nonneg (Real.exp_pos _).le (helmholtzPartition_pos E T).le
  sum_one := by
    rw [← Finset.sum_div]
    exact div_self (helmholtzPartition_pos E T).ne'

theorem helmholtzGibbsLaw_pos [Nonempty α] (E : α → ℝ) (T : ℝ) (x : α) :
    0 < helmholtzGibbsLaw E T x :=
  div_pos (Real.exp_pos _) (helmholtzPartition_pos E T)

theorem log_helmholtzGibbsLaw [Nonempty α] (E : α → ℝ) (T : ℝ) (x : α) :
    Real.log (helmholtzGibbsLaw E T x) =
      -E x / T - Real.log (helmholtzPartition E T) := by
  change Real.log (Real.exp (-E x / T) / helmholtzPartition E T) = _
  rw [Real.log_div (Real.exp_pos _).ne' (helmholtzPartition_pos E T).ne',
    Real.log_exp]

/-- Helmholtz decomposition: mean energy minus `T` times entropy equals the
free energy plus `T` times the KL divergence to the Gibbs law. -/
theorem helmholtz_decomposition [Nonempty α] (E : α → ℝ) {T : ℝ} (hT : 0 < T)
    (q : FiniteLaw α) :
    expectation q E - T * entropy q =
      helmholtzFreeEnergy E T + T * finiteKL q (helmholtzGibbsLaw E T) := by
  rw [finiteKL_eq_crossEntropy_sub_entropy q _ (helmholtzGibbsLaw_pos E T)]
  have hcross : crossEntropy q (helmholtzGibbsLaw E T) =
      expectation q E / T + Real.log (helmholtzPartition E T) := by
    unfold crossEntropy expectation
    simp_rw [log_helmholtzGibbsLaw]
    have h : ∀ x, -q x * (-E x / T - Real.log (helmholtzPartition E T)) =
        q x * E x / T + q x * Real.log (helmholtzPartition E T) := by
      intro x; ring
    simp_rw [h]
    rw [Finset.sum_add_distrib, ← Finset.sum_div, ← Finset.sum_mul, q.sum_one,
      one_mul]
  rw [hcross]
  unfold helmholtzFreeEnergy
  field_simp
  ring

/-- Variational characterisation: the Gibbs free energy lower-bounds the
variational free energy of every law. -/
theorem helmholtzFreeEnergy_le [Nonempty α] (E : α → ℝ) {T : ℝ} (hT : 0 < T)
    (q : FiniteLaw α) :
    helmholtzFreeEnergy E T ≤ expectation q E - T * entropy q := by
  rw [helmholtz_decomposition E hT q]
  have := mul_nonneg hT.le (finiteKL_nonneg q (helmholtzGibbsLaw E T))
  linarith

/-- Equality holds exactly at the Gibbs law. -/
theorem helmholtzFreeEnergy_eq_iff [Nonempty α] (E : α → ℝ) {T : ℝ}
    (hT : 0 < T) (q : FiniteLaw α) :
    expectation q E - T * entropy q = helmholtzFreeEnergy E T ↔
      q = helmholtzGibbsLaw E T := by
  rw [helmholtz_decomposition E hT q, ← finiteKL_eq_zero_iff]
  constructor
  · intro h
    have : T * finiteKL q (helmholtzGibbsLaw E T) = 0 := by linarith
    exact (mul_eq_zero.mp this).resolve_left hT.ne'
  · intro h
    rw [h, mul_zero, add_zero]

/-- Strict inequality away from the Gibbs law. -/
theorem helmholtzFreeEnergy_lt [Nonempty α] (E : α → ℝ) {T : ℝ} (hT : 0 < T)
    (q : FiniteLaw α) (hq : q ≠ helmholtzGibbsLaw E T) :
    helmholtzFreeEnergy E T < expectation q E - T * entropy q := by
  refine lt_of_le_of_ne (helmholtzFreeEnergy_le E hT q) fun h => hq ?_
  exact (helmholtzFreeEnergy_eq_iff E hT q).mp h.symm

/-- Entropy of the Gibbs law in terms of the energy-weighted Boltzmann sum. -/
theorem entropy_helmholtzGibbsLaw [Nonempty α] (E : α → ℝ) {T : ℝ}
    (hT : 0 < T) :
    entropy (helmholtzGibbsLaw E T) =
      (∑ x, Real.exp (-E x / T) * E x) / (T * helmholtzPartition E T) +
        Real.log (helmholtzPartition E T) := by
  have hZ := (helmholtzPartition_pos E T).ne'
  have hterm : ∀ x, Real.negMulLog (helmholtzGibbsLaw E T x) =
      Real.exp (-E x / T) * E x / (T * helmholtzPartition E T) +
        Real.exp (-E x / T) / helmholtzPartition E T *
          Real.log (helmholtzPartition E T) := by
    intro x
    rw [Real.negMulLog, log_helmholtzGibbsLaw]
    change -(Real.exp (-E x / T) / helmholtzPartition E T) * _ = _
    field_simp
    ring
  unfold entropy
  simp_rw [hterm]
  rw [Finset.sum_add_distrib, ← Finset.sum_div, ← Finset.sum_mul,
    ← Finset.sum_div]
  have : (∑ x, Real.exp (-E x / T)) / helmholtzPartition E T = 1 :=
    div_self hZ
  rw [this, one_mul]

/-- Thermodynamic derivative: `dF/dT = -S(p_T)`. -/
theorem hasDerivAt_helmholtzFreeEnergy [Nonempty α] (E : α → ℝ) {T : ℝ}
    (hT : 0 < T) :
    HasDerivAt (helmholtzFreeEnergy E) (-entropy (helmholtzGibbsLaw E T)) T := by
  have hterm : ∀ x, HasDerivAt (fun t : ℝ => Real.exp (-E x / t))
      (Real.exp (-E x / T) * (E x / T ^ 2)) T := by
    intro x
    have h1 : HasDerivAt (fun t : ℝ => -E x / t) (E x / T ^ 2) T := by
      have := (hasDerivAt_inv hT.ne').const_mul (-E x)
      convert this using 1
      · funext t; simp [div_eq_mul_inv]
      · field_simp
    exact h1.exp
  have hZ : HasDerivAt (helmholtzPartition E)
      (∑ x, Real.exp (-E x / T) * (E x / T ^ 2)) T := by
    have := HasDerivAt.fun_sum (u := Finset.univ) (fun x _ => hterm x)
    convert this using 1
    funext t; simp [helmholtzPartition]
  have hlog := hZ.log (helmholtzPartition_pos E T).ne'
  have hF := (hasDerivAt_id T).neg.mul hlog
  have hfun : helmholtzFreeEnergy E =
      (-id) * fun y => Real.log (helmholtzPartition E y) := by
    funext t; simp [helmholtzFreeEnergy]
  rw [hfun]
  refine hF.congr_deriv ?_
  have hZpos := helmholtzPartition_pos E T
  rw [entropy_helmholtzGibbsLaw E hT]
  simp only [id, Pi.neg_apply]
  have : (∑ x, Real.exp (-E x / T) * (E x / T ^ 2)) =
      (∑ x, Real.exp (-E x / T) * E x) / T ^ 2 := by
    rw [Finset.sum_div]
    exact Finset.sum_congr rfl fun x _ => by ring
  rw [this]
  field_simp
  ring

/-- Two-level energy: `0` on `false`, `1` on `true`. -/
def helmholtzBoolEnergy : Bool → ℝ := fun b => if b then 1 else 0

theorem helmholtzPartition_bool (T : ℝ) :
    helmholtzPartition helmholtzBoolEnergy T = Real.exp (-1 / T) + 1 := by
  simp [helmholtzPartition, helmholtzBoolEnergy]

/-- Non-vacuity: at every positive temperature the uniform (non-Gibbs) law on
the two-level system has strictly larger variational free energy than `F(T)`. -/
theorem helmholtz_bool_uniform_gt {T : ℝ} (hT : 0 < T) :
    helmholtzFreeEnergy helmholtzBoolEnergy T <
      expectation (FiniteLaw.uniform : FiniteLaw Bool) helmholtzBoolEnergy -
        T * entropy (FiniteLaw.uniform : FiniteLaw Bool) := by
  apply helmholtzFreeEnergy_lt _ hT
  intro h
  have h0 := congrArg (fun p : FiniteLaw Bool => p.mass false) h
  have hZ : helmholtzPartition helmholtzBoolEnergy T = Real.exp (-1 / T) + 1 :=
    helmholtzPartition_bool T
  have hZpos := helmholtzPartition_pos helmholtzBoolEnergy T
  simp only [FiniteLaw.uniform, helmholtzGibbsLaw, helmholtzBoolEnergy,
    Fintype.card_bool] at h0
  rw [hZ] at h0
  simp only [Bool.false_eq_true, ↓reduceIte, neg_zero, zero_div,
    Real.exp_zero] at h0
  have hpos : 0 < Real.exp (-1 / T) := Real.exp_pos _
  have h1 : Real.exp (-1 / T) = 1 := by
    field_simp at h0
    push_cast at h0
    have e : -1 / T = -(1 / T) := by ring
    rw [e]
    linarith
  have h2 := Real.exp_eq_one_iff _ |>.mp h1
  have : (0 : ℝ) < 1 / T := by positivity
  have : -1 / T = -(1 / T) := by ring
  linarith

/-! ## Joint-slice variational free energy with derived surprisal -/

/-- Variational free energy of `q` against the unnormalised joint slice
`x ↦ prior x * kernel x y` at observation `y`.  Surprisal is not an argument:
it appears only after the slice is factored through the posterior. -/
noncomputable def jointSliceVFE (prior : FiniteLaw α)
    (kernel : FiniteKernel α β) (y : β) (q : FiniteLaw α) : ℝ :=
  ∑ x, q x * (Real.log (q x) - Real.log (prior x * kernel x y))

/-- Surprisal of `y`, derived as negative log predictive evidence. -/
noncomputable def evidenceSurprisal (prior : FiniteLaw α)
    (kernel : FiniteKernel α β) (y : β) : ℝ :=
  -Real.log (kernel.predictive prior y)

/-- Finite carrier, not the measure-theoretic route.  With a strictly positive
joint slice and positive evidence, KL to the unnormalised joint slice equals
KL to the exact Bayes posterior plus the derived surprisal. -/
theorem jointSliceVFE_eq_kl_add_surprisal (prior : FiniteLaw α)
    (kernel : FiniteKernel α β) (y : β)
    (hy : 0 < kernel.predictive prior y)
    (hjoint : ∀ x, 0 < prior x * kernel x y) (q : FiniteLaw α) :
    jointSliceVFE prior kernel y q =
      finiteKL q (kernel.posterior prior y hy) +
        evidenceSurprisal prior kernel y := by
  have hpost : ∀ x, 0 < kernel.posterior prior y hy x := fun x =>
    div_pos (hjoint x) hy
  rw [finiteKL_eq_crossEntropy_sub_entropy q _ hpost]
  have hlog : ∀ x, Real.log (kernel.posterior prior y hy x) =
      Real.log (prior x * kernel x y) -
        Real.log (kernel.predictive prior y) := fun x =>
    Real.log_div (hjoint x).ne' hy.ne'
  unfold jointSliceVFE crossEntropy entropy evidenceSurprisal
  simp_rw [hlog, Real.negMulLog_eq_neg]
  have h1 : ∑ x, -(q x) * (Real.log (prior x * kernel x y) -
        Real.log (kernel.predictive prior y)) =
      ∑ x, (-(q x * Real.log (prior x * kernel x y))) +
        (∑ x, q x) * Real.log (kernel.predictive prior y) := by
    rw [Finset.sum_mul, ← Finset.sum_add_distrib]
    exact Finset.sum_congr rfl fun x _ => by ring
  rw [h1, q.sum_one]
  have h2 : ∑ x, q x * (Real.log (q x) - Real.log (prior x * kernel x y)) =
      ∑ x, (q x * Real.log (q x)) +
        ∑ x, (-(q x * Real.log (prior x * kernel x y))) := by
    rw [← Finset.sum_add_distrib]
    exact Finset.sum_congr rfl fun x _ => by ring
  rw [h2, Finset.sum_neg_distrib]
  simp only [Finset.sum_neg_distrib]
  ring

/-- Joint-slice free energy bounds derived surprisal from above. -/
theorem jointSliceVFE_ge_surprisal (prior : FiniteLaw α)
    (kernel : FiniteKernel α β) (y : β)
    (hy : 0 < kernel.predictive prior y)
    (hjoint : ∀ x, 0 < prior x * kernel x y) (q : FiniteLaw α) :
    evidenceSurprisal prior kernel y ≤ jointSliceVFE prior kernel y q := by
  rw [jointSliceVFE_eq_kl_add_surprisal prior kernel y hy hjoint q]
  linarith [finiteKL_nonneg q (kernel.posterior prior y hy)]

/-- The bound is tight exactly at the Bayes posterior. -/
theorem jointSliceVFE_eq_surprisal_iff (prior : FiniteLaw α)
    (kernel : FiniteKernel α β) (y : β)
    (hy : 0 < kernel.predictive prior y)
    (hjoint : ∀ x, 0 < prior x * kernel x y) (q : FiniteLaw α) :
    jointSliceVFE prior kernel y q = evidenceSurprisal prior kernel y ↔
      q = kernel.posterior prior y hy := by
  rw [jointSliceVFE_eq_kl_add_surprisal prior kernel y hy hjoint q,
    ← finiteKL_eq_zero_iff]
  constructor <;> intro h <;> linarith

/-- A strictly positive joint slice forces positive evidence. -/
theorem predictive_pos_of_jointSlice_pos [Nonempty α] (prior : FiniteLaw α)
    (kernel : FiniteKernel α β) (y : β)
    (hjoint : ∀ x, 0 < prior x * kernel x y) :
    0 < kernel.predictive prior y := by
  rw [FiniteKernel.predictive_mass]
  exact Finset.sum_pos (fun x _ => hjoint x) Finset.univ_nonempty

/-- Boolean witness kernel: emits the matching Boolean with probability `3/4`. -/
noncomputable def vfeWitnessKernel : FiniteKernel Bool Bool where
  mass x y := if x = y then 3 / 4 else 1 / 4
  nonneg x y := by split_ifs <;> norm_num
  sum_one x := by
    cases x <;> rw [Fintype.sum_bool] <;> norm_num

/-- Witness evidence at `true` under a fair prior is `1/2`. -/
theorem vfeWitness_predictive_true :
    vfeWitnessKernel.predictive (FiniteLaw.uniform : FiniteLaw Bool) true =
      1 / 2 := by
  rw [FiniteKernel.predictive_mass, Fintype.sum_bool]
  simp [FiniteLaw.uniform, vfeWitnessKernel]
  norm_num

/-- Witness derived surprisal is `log 2`. -/
theorem vfeWitness_surprisal :
    evidenceSurprisal (FiniteLaw.uniform : FiniteLaw Bool) vfeWitnessKernel
      true = Real.log 2 := by
  rw [evidenceSurprisal, vfeWitness_predictive_true, one_div, Real.log_inv,
    neg_neg]

/-- Nonzero-gap witness: the fair prior against the Bayes posterior at `true`
is strictly above derived surprisal. -/
theorem vfeWitness_gap_pos :
    evidenceSurprisal (FiniteLaw.uniform : FiniteLaw Bool) vfeWitnessKernel
        true <
      jointSliceVFE (FiniteLaw.uniform : FiniteLaw Bool) vfeWitnessKernel true
        (FiniteLaw.uniform : FiniteLaw Bool) := by
  have hy : 0 < vfeWitnessKernel.predictive
      (FiniteLaw.uniform : FiniteLaw Bool) true := by
    rw [vfeWitness_predictive_true]; norm_num
  have hjoint : ∀ x : Bool,
      0 < (FiniteLaw.uniform : FiniteLaw Bool) x * vfeWitnessKernel x true := by
    intro x
    cases x <;> simp [FiniteLaw.uniform, vfeWitnessKernel]
  rw [jointSliceVFE_eq_kl_add_surprisal _ _ true hy hjoint]
  have hne : (FiniteLaw.uniform : FiniteLaw Bool) ≠
      vfeWitnessKernel.posterior (FiniteLaw.uniform : FiniteLaw Bool) true
        hy := by
    intro h
    have h0 := congrArg (fun p : FiniteLaw Bool => p.mass true) h
    simp only [FiniteKernel.posterior, FiniteLaw.uniform] at h0
    simp [vfeWitnessKernel] at h0
    norm_num at h0
  have hpos : 0 < finiteKL (FiniteLaw.uniform : FiniteLaw Bool)
      (vfeWitnessKernel.posterior (FiniteLaw.uniform : FiniteLaw Bool) true
        hy) :=
    lt_of_le_of_ne (finiteKL_nonneg _ _)
      (fun h => hne ((finiteKL_eq_zero_iff _ _).mp h.symm))
  linarith

/-- Degenerate boundary kernel: always emits `false`. -/
def vfeZeroEvidenceKernel : FiniteKernel Bool Bool :=
  FiniteKernel.deterministic fun _ => false

/-- Zero-evidence boundary: observing `true` has zero predictive mass, every
joint-slice atom vanishes, and so neither the Bayes posterior nor the positive
slice hypothesis of the identity is available. -/
theorem vfeZeroEvidence_boundary :
    vfeZeroEvidenceKernel.predictive (FiniteLaw.uniform : FiniteLaw Bool)
        true = 0 ∧
      (∀ x : Bool, (FiniteLaw.uniform : FiniteLaw Bool) x *
        vfeZeroEvidenceKernel x true = 0) ∧
      ¬ (0 < vfeZeroEvidenceKernel.predictive
        (FiniteLaw.uniform : FiniteLaw Bool) true) := by
  have hslice : ∀ x : Bool, (FiniteLaw.uniform : FiniteLaw Bool) x *
      vfeZeroEvidenceKernel x true = 0 := by
    intro x
    simp [vfeZeroEvidenceKernel, FiniteKernel.deterministic]
  have hzero : vfeZeroEvidenceKernel.predictive
      (FiniteLaw.uniform : FiniteLaw Bool) true = 0 := by
    rw [FiniteKernel.predictive_mass]
    exact Finset.sum_eq_zero fun x _ => hslice x
  exact ⟨hzero, hslice, by rw [hzero]; exact lt_irrefl _⟩

end FEP.VariationalDuality
