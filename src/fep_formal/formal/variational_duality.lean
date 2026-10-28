module
public import FepSketches.finite_information
public import Mathlib.Analysis.LocallyConvex.Separation
public import Mathlib.Analysis.Convex.SpecificFunctions.Basic
public import Mathlib.InformationTheory.KullbackLeibler.Basic
public import Mathlib.Probability.Moments.Basic
public import Mathlib.Topology.Order.Compact
public import Mathlib.Analysis.SpecialFunctions.BinaryEntropy

@[expose] public section

/-!
# Finite and measure-native variational information bounds

The results here use the normalized `FiniteLaw`/`FiniteKernel` substrate.  All
logarithmic identities expose full-support premises.  In particular, no result
identifies the existing totalized real-valued KL with an extended divergence at
zero reference mass.

The separate native entropy inequality uses probability measures, an
integrable potential under the candidate, and an integrable exponential under
the reference. Its `ℝ≥0∞` bound retains infinite native KL. Equality after
`ENNReal.ofReal` clipping is not an optimizer characterization; the finite real
tilt identity records the actual gap.
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

/- L06_MATHLIB_ONLY_BEGIN -/
section NativeEntropy

open MeasureTheory
open scoped ENNReal

variable {Ω : Type*} [MeasurableSpace Ω]

/-- Finite native KL has an exact real gap against the normalized exponential
tilt. Absolute continuity and likelihood-ratio integrability are explicit;
this identity never converts infinite KL into a real entropy bound. -/
theorem nativeKL_tilted_gap
    (μ ν : Measure Ω) [IsProbabilityMeasure μ] [IsProbabilityMeasure ν]
    {f : Ω → ℝ} (hμν : μ ≪ ν) (hf : Integrable f μ)
    (hexp : Integrable (fun x => Real.exp (f x)) ν)
    (hllr : Integrable (llr μ ν) μ) :
    (InformationTheory.klDiv μ (ν.tilted f)).toReal =
      (InformationTheory.klDiv μ ν).toReal - (∫ x, f x ∂μ) +
        Real.log (∫ x, Real.exp (f x) ∂ν) := by
  let : IsProbabilityMeasure (ν.tilted f) := isProbabilityMeasure_tilted hexp
  have hμtilt : μ ≪ ν.tilted f := hμν.trans (absolutelyContinuous_tilted hexp)
  have hllrtilt : Integrable (llr μ (ν.tilted f)) μ :=
    integrable_llr_tilted_right hμν hf hllr hexp
  rw [InformationTheory.toReal_klDiv hμtilt hllrtilt,
    InformationTheory.toReal_klDiv hμν hllr]
  simp only [probReal_univ, add_sub_cancel_right]
  exact integral_llr_tilted_right hμν hf hexp hllr

/-- Measure-level entropy inequality with native extended KL. Singular laws
and nonintegrable likelihood ratios keep the infinite right-hand side.
Exponential integrability is essential because the Bochner normalizer is
otherwise totalized to zero. The clipped left-hand side has no optimizer iff. -/
theorem nativeEntropy_le_klDiv
    (μ ν : Measure Ω) [IsProbabilityMeasure μ] [IsProbabilityMeasure ν]
    {f : Ω → ℝ} (hf : Integrable f μ)
    (hexp : Integrable (fun x => Real.exp (f x)) ν) :
    ENNReal.ofReal ((∫ x, f x ∂μ) - Real.log (∫ x, Real.exp (f x) ∂ν)) ≤
      InformationTheory.klDiv μ ν := by
  by_cases htop : InformationTheory.klDiv μ ν = ∞
  · simp [htop]
  obtain ⟨hμν, hllr⟩ := InformationTheory.klDiv_ne_top_iff.mp htop
  have hgap := nativeKL_tilted_gap μ ν hμν hf hexp hllr
  have hnonneg : 0 ≤ (InformationTheory.klDiv μ (ν.tilted f)).toReal :=
    ENNReal.toReal_nonneg
  have hle : (∫ x, f x ∂μ) - Real.log (∫ x, Real.exp (f x) ∂ν) ≤
      (InformationTheory.klDiv μ ν).toReal := by
    linarith
  calc
    ENNReal.ofReal ((∫ x, f x ∂μ) - Real.log (∫ x, Real.exp (f x) ∂ν)) ≤
        ENNReal.ofReal (InformationTheory.klDiv μ ν).toReal :=
      ENNReal.ofReal_le_ofReal hle
    _ = InformationTheory.klDiv μ ν := ENNReal.ofReal_toReal htop

/-- The entropy inequality for a cumulant-generating function. The parameter
may have either sign; the exponential moment must be integrable at that exact
parameter, and no finite-real interpretation of singular KL is asserted. -/
theorem nativeCgf_le_klDiv
    (μ ν : Measure Ω) [IsProbabilityMeasure μ] [IsProbabilityMeasure ν]
    {X : Ω → ℝ} (t : ℝ) (hX : Integrable X μ)
    (hexp : Integrable (fun x => Real.exp (t * X x)) ν) :
    ENNReal.ofReal (t * (∫ x, X x ∂μ) - ProbabilityTheory.cgf X ν t) ≤
      InformationTheory.klDiv μ ν := by
  simpa only [ProbabilityTheory.cgf, ProbabilityTheory.mgf, integral_const_mul] using
    nativeEntropy_le_klDiv μ ν (hX.const_mul t) hexp

end NativeEntropy
/- L06_MATHLIB_ONLY_END -/

/-! ## Exact fair-Boolean Hamming rate-distortion curve

Natural-log units and the fair Boolean source are fixed. The reverse-reference
proof permits zero reproduction atoms. Finite dual optimizers are asserted only
for strictly interior budgets; zero distortion has an unbounded limiting
multiplier despite the totalized logarithm's finite value at zero. This selected
source does not establish general finite- or continuous-alphabet strong duality.
-/
namespace FairBoolean

noncomputable def symmetricJoint (D : ℝ) (h0 : 0 ≤ D) (h1 : D ≤ 1) :
    FiniteLaw (Bool × Bool) where
  mass xy := if xy.1 = xy.2 then (1-D)/2 else D/2
  nonneg xy := by split <;> positivity
  sum_one := by simp [Fintype.sum_prod_type]; ring

theorem symmetricJoint_fst (D : ℝ) (h0 : 0 ≤ D) (h1 : D ≤ 1) :
    (symmetricJoint D h0 h1).fstMarginal = FiniteLaw.uniform := by
  apply FiniteLaw.ext_mass
  funext x
  cases x <;> simp [FiniteLaw.fstMarginal, symmetricJoint, FiniteLaw.uniform] <;> ring

theorem symmetricJoint_snd (D : ℝ) (h0 : 0 ≤ D) (h1 : D ≤ 1) :
    (symmetricJoint D h0 h1).sndMarginal = FiniteLaw.uniform := by
  apply FiniteLaw.ext_mass
  funext x
  cases x <;> simp [FiniteLaw.sndMarginal, symmetricJoint, FiniteLaw.uniform] <;> ring

theorem symmetricJoint_distortion (D : ℝ) (h0 : 0 ≤ D) (h1 : D ≤ 1) :
    expectedDistortion (symmetricJoint D h0 h1) boolHammingDistortion = D := by
  simp [expectedDistortion, symmetricJoint, boolHammingDistortion,
    Fintype.sum_prod_type]

theorem symmetricJoint_feasible (D : ℝ) (h0 : 0 ≤ D) (h1 : D ≤ 1) :
    RateDistortionFeasible FiniteLaw.uniform boolHammingDistortion D
      (symmetricJoint D h0 h1) :=
  ⟨symmetricJoint_fst D h0 h1, (symmetricJoint_distortion D h0 h1).le⟩

lemma entropy_fair_bool : entropy (FiniteLaw.uniform : FiniteLaw Bool) = Real.log 2 := by
  simp [entropy, FiniteLaw.uniform, Real.negMulLog_eq_neg]

lemma negMulLog_half (x : ℝ) :
    2 * Real.negMulLog (x/2) = Real.negMulLog x + x * Real.log 2 := by
  have hhalf : Real.negMulLog ((2 : ℝ)⁻¹) = (2 : ℝ)⁻¹ * Real.log 2 := by
    simp only [Real.negMulLog_eq_neg, Real.log_inv]
    ring
  have h := Real.negMulLog_mul x ((2 : ℝ)⁻¹)
  rw [hhalf] at h
  rw [div_eq_mul_inv]
  linear_combination 2 * h

theorem symmetricJoint_entropy (D : ℝ) (h0 : 0 ≤ D) (h1 : D ≤ 1) :
    entropy (symmetricJoint D h0 h1) = Real.log 2 + Real.binEntropy D := by
  have hD := negMulLog_half D
  have hC := negMulLog_half (1-D)
  rw [Real.binEntropy_eq_negMulLog_add_negMulLog_one_sub]
  simp [entropy, symmetricJoint, Fintype.sum_prod_type]
  linarith

theorem symmetricJoint_information (D : ℝ) (h0 : 0 ≤ D) (h1 : D ≤ 1) :
    mutualInformation (symmetricJoint D h0 h1) = Real.log 2 - Real.binEntropy D := by
  rw [mutualInformation_eq_entropy_marginals_without_support,
    symmetricJoint_fst, symmetricJoint_snd, entropy_fair_bool,
    symmetricJoint_entropy]
  ring

/-- Reverse-channel comparison law, using the actual reproduction marginal.
It is normalized even if the reproduction law has zero atoms. -/
noncomputable def reverseReference (code : FiniteLaw Bool)
    (D : ℝ) (h0 : 0 ≤ D) (h1 : D ≤ 1) : FiniteLaw (Bool × Bool) where
  mass xy := code xy.2 * (if xy.1 = xy.2 then 1-D else D)
  nonneg xy := mul_nonneg (code.nonneg _) (by split <;> positivity)
  sum_one := by
    have h := code.sum_one
    rw [Fintype.sum_bool] at h
    simp [Fintype.sum_prod_type]
    nlinarith

theorem reverseReference_support (J : FiniteLaw (Bool × Bool))
    (D : ℝ) (h0 : 0 < D) (h1 : D < 1) :
    ∀ xy, J xy ≠ 0 → 0 < reverseReference J.sndMarginal D h0.le h1.le xy := by
  rintro ⟨x,y⟩ hmass
  have hpos : 0 < J (x,y) := lt_of_le_of_ne (J.nonneg _) (Ne.symm hmass)
  have hmarg : 0 < J.sndMarginal y := by
    change 0 < ∑ z : Bool, J (z,y)
    rw [Fintype.sum_bool]
    cases x <;> linarith [J.nonneg (true,y), J.nonneg (false,y)]
  change 0 < J.sndMarginal y * (if x=y then 1-D else D)
  split <;> exact mul_pos hmarg (by linarith)

/-- This consumes the real existing relative-support theorem, not assumed KL
identification or full support of the reproduction marginal. -/
theorem reverseReference_KL_entropy (J : FiniteLaw (Bool × Bool))
    (D : ℝ) (h0 : 0 < D) (h1 : D < 1) :
    finiteKL J (reverseReference J.sndMarginal D h0.le h1.le) =
      crossEntropy J (reverseReference J.sndMarginal D h0.le h1.le) - entropy J := by
  exact finiteKL_eq_crossEntropy_sub_entropy_of_relativeSupport _ _
    (reverseReference_support J D h0 h1)

/-- Endpoint/large-budget value0: an actual independent minimizer. -/
theorem half_or_larger_exact (D : ℝ) (hD : (1:ℝ)/2 ≤ D) :
    ∃ J : FiniteLaw (Bool × Bool),
      RateDistortionFeasible FiniteLaw.uniform boolHammingDistortion D J ∧
      mutualInformation J = 0 ∧
      ∀ K, RateDistortionFeasible FiniteLaw.uniform boolHammingDistortion D K →
        mutualInformation J ≤ mutualInformation K := by
  let J := (FiniteLaw.uniform : FiniteLaw Bool).product (FiniteLaw.pointMass false)
  have h := boolIndependent_minimizer D hD (FiniteLaw.pointMass false)
  exact ⟨J,h.1,mutualInformation_product_eq_zero _ _,h.2⟩

noncomputable def interiorMultiplier (D : ℝ) := Real.log (1-D) - Real.log D

theorem interiorMultiplier_pos (D : ℝ) (h0 : 0 < D) (hhalf : D < (1:ℝ)/2) :
    0 < interiorMultiplier D := by
  unfold interiorMultiplier
  exact sub_pos.mpr (Real.log_lt_log h0 (show D < 1-D by linarith))

/-- The derivative is claimed only in the strict interior. -/
theorem interior_curve_derivative (D : ℝ) (h0 : 0 < D) (hhalf : D < (1:ℝ)/2) :
    HasDerivAt (fun d : ℝ => Real.log 2 - Real.binEntropy d)
      (-interiorMultiplier D) D := by
  simpa [interiorMultiplier] using
    (Real.hasDerivAt_binEntropy (ne_of_gt h0) (ne_of_lt (show D < 1 by linarith))).const_sub (Real.log 2)

lemma reverseReference_crossEntropy (J : FiniteLaw (Bool × Bool))
    (hfair : J.fstMarginal = FiniteLaw.uniform)
    (D : ℝ) (h0 : 0 < D) (h1 : D < 1) :
    crossEntropy J (reverseReference J.sndMarginal D h0.le h1.le) =
      crossEntropy J (J.fstMarginal.product J.sndMarginal) - Real.log 2 -
      ((1-expectedDistortion J boolHammingDistortion)*Real.log (1-D) +
        expectedDistortion J boolHammingDistortion*Real.log D) := by
  let c : Bool × Bool → ℝ := fun xy => if xy.1=xy.2 then 1-D else D
  have hc : ∀ xy, 0 < c xy := by intro xy; dsimp [c]; split <;> linarith
  have hp : ∀ xy, -J xy * Real.log
      (reverseReference J.sndMarginal D h0.le h1.le xy) =
      -J xy * Real.log ((J.fstMarginal.product J.sndMarginal) xy) -
        J xy * Real.log 2 - J xy * Real.log (c xy) := by
    intro xy
    by_cases hz : J xy=0
    · simp [hz]
    · have hprod := joint_supported_by_productMarginals J xy hz
      have heq : reverseReference J.sndMarginal D h0.le h1.le xy =
          (J.fstMarginal.product J.sndMarginal) xy * 2 * c xy := by
        simp [reverseReference, FiniteLaw.product, hfair, FiniteLaw.uniform, c]
        ring
      rw [heq, Real.log_mul (mul_ne_zero (ne_of_gt hprod) (by norm_num))
        (ne_of_gt (hc xy)), Real.log_mul (ne_of_gt hprod) (by norm_num)]
      ring
  have hchannel : (∑ xy, J xy * Real.log (c xy)) =
      (1-expectedDistortion J boolHammingDistortion)*Real.log (1-D) +
        expectedDistortion J boolHammingDistortion*Real.log D := by
    have hsum := J.sum_one
    simp only [Fintype.sum_prod_type, Fintype.sum_bool] at hsum
    have hslog := congrArg (fun z : ℝ => z * Real.log (1-D)) hsum
    simp [c, expectedDistortion, boolHammingDistortion, Fintype.sum_prod_type]
    nlinarith
  unfold crossEntropy
  simp_rw [hp]
  rw [Finset.sum_sub_distrib, Finset.sum_sub_distrib, ← Finset.sum_mul,
    J.sum_one, one_mul, hchannel]

lemma reverseReference_KL_exact (J : FiniteLaw (Bool × Bool))
    (hfair : J.fstMarginal = FiniteLaw.uniform)
    (D : ℝ) (h0 : 0 < D) (h1 : D < 1) :
    finiteKL J (reverseReference J.sndMarginal D h0.le h1.le) =
      mutualInformation J - Real.log 2 -
      ((1-expectedDistortion J boolHammingDistortion)*Real.log (1-D) +
        expectedDistortion J boolHammingDistortion*Real.log D) := by
  have hprod := finiteKL_eq_crossEntropy_sub_entropy_of_relativeSupport
    J (J.fstMarginal.product J.sndMarginal) (joint_supported_by_productMarginals J)
  have href := reverseReference_KL_entropy J D h0 h1
  have hcross := reverseReference_crossEntropy J hfair D h0 h1
  change mutualInformation J = _ at hprod
  linarith

/-- All source-fixed laws, not only distortion-feasible laws, obey this bound. -/
theorem boolean_lagrangian_lower (J : FiniteLaw (Bool × Bool))
    (hfair : J.fstMarginal = FiniteLaw.uniform)
    (D : ℝ) (h0 : 0 < D) (hhalf : D < (1:ℝ)/2) :
    Real.log 2 + Real.log (1-D) ≤
      mutualInformation J + interiorMultiplier D *
        expectedDistortion J boolHammingDistortion := by
  have h1 : D < 1 := by linarith
  have hn := finiteKL_nonneg J (reverseReference J.sndMarginal D h0.le h1.le)
  rw [reverseReference_KL_exact J hfair D h0 h1] at hn
  unfold interiorMultiplier
  nlinarith

lemma boolean_rate_algebra (D : ℝ) :
    Real.log 2 - Real.binEntropy D =
      Real.log 2 + Real.log (1-D) - interiorMultiplier D * D := by
  rw [Real.binEntropy_eq_negMulLog_add_negMulLog_one_sub]
  simp only [Real.negMulLog_eq_neg, interiorMultiplier]
  ring

theorem boolean_converse (D : ℝ) (h0 : 0 < D) (hhalf : D < (1:ℝ)/2)
    (J : FiniteLaw (Bool × Bool))
    (hJ : RateDistortionFeasible FiniteLaw.uniform boolHammingDistortion D J) :
    Real.log 2 - Real.binEntropy D ≤ mutualInformation J := by
  have hbound := boolean_lagrangian_lower J hJ.1 D h0 hhalf
  have hmult := interiorMultiplier_pos D h0 hhalf
  have hdist := mul_le_mul_of_nonneg_left hJ.2 hmult.le
  rw [boolean_rate_algebra]
  linarith

/-- Actual attained interior minimum, with no field assuming a converse. -/
theorem boolean_interior_exact_minimum
    (D : ℝ) (h0 : 0 < D) (hhalf : D < (1:ℝ)/2) :
    ∃ J : FiniteLaw (Bool × Bool),
      RateDistortionFeasible FiniteLaw.uniform boolHammingDistortion D J ∧
      mutualInformation J = Real.log 2 - Real.binEntropy D ∧
      ∀ K, RateDistortionFeasible FiniteLaw.uniform boolHammingDistortion D K →
        mutualInformation J ≤ mutualInformation K := by
  have h1 : D ≤ 1 := by linarith
  refine ⟨symmetricJoint D h0.le h1, symmetricJoint_feasible D h0.le h1,
    symmetricJoint_information D h0.le h1, ?_⟩
  intro K hK
  rw [symmetricJoint_information]
  exact boolean_converse D h0 hhalf K hK

theorem symmetric_zero_is_owned :
    symmetricJoint 0 (by norm_num) (by norm_num) = boolZeroDistortionJoint := by
  apply FiniteLaw.ext_mass
  funext xy
  simp [symmetricJoint, boolZeroDistortionJoint]

theorem boolean_zero_exact (J : FiniteLaw (Bool × Bool))
    (hJ : RateDistortionFeasible FiniteLaw.uniform boolHammingDistortion 0 J) :
    J = boolZeroDistortionJoint ∧ mutualInformation J = Real.log 2 := by
  have heq := boolZeroBudget_unique_feasible J hJ
  refine ⟨heq, ?_⟩
  rw [heq, ← symmetric_zero_is_owned, symmetricJoint_information]
  simp only [Real.binEntropy_zero, sub_zero]

/-- Closed interval value, assembled without endpoint multiplier/continuity. -/
theorem boolean_closed_exact_minimum
    (D : ℝ) (h0 : 0 ≤ D) (hhalf : D ≤ (1:ℝ)/2) :
    ∃ J : FiniteLaw (Bool × Bool),
      RateDistortionFeasible FiniteLaw.uniform boolHammingDistortion D J ∧
      mutualInformation J = Real.log 2 - Real.binEntropy D ∧
      ∀ K, RateDistortionFeasible FiniteLaw.uniform boolHammingDistortion D K →
        mutualInformation J ≤ mutualInformation K := by
  by_cases hz : D = 0
  · subst D
    refine ⟨boolZeroDistortionJoint, boolZeroDistortionJoint_feasible, ?_, ?_⟩
    · have h := (boolean_zero_exact _ boolZeroDistortionJoint_feasible).2
      simpa only [Real.binEntropy_zero, sub_zero] using h
    · intro K hK
      rw [(boolean_zero_exact _ hK).1]
  · by_cases hh : D = (1:ℝ)/2
    · subst D
      obtain ⟨J,hJ,hI,hmin⟩ := half_or_larger_exact ((1:ℝ)/2) le_rfl
      refine ⟨J,hJ,?_,hmin⟩
      have hEntropy : Real.binEntropy ((1:ℝ)/2) = Real.log 2 :=
        Real.binEntropy_eq_log_two.mpr (by norm_num)
      rw [hI,hEntropy,sub_self]
    · exact boolean_interior_exact_minimum D (lt_of_le_of_ne h0 (Ne.symm hz))
        (lt_of_le_of_ne hhalf hh)

/-- Exact dual value at the strict-interior finite multiplier. -/
theorem boolean_interior_dual_exact
    (D : ℝ) (h0 : 0 < D) (hhalf : D < (1:ℝ)/2) :
    rateDistortionDualValue (FiniteLaw.uniform : FiniteLaw Bool)
      boolHammingDistortion D (interiorMultiplier D) =
        Real.log 2 - Real.binEntropy D := by
  have h1 : D ≤ 1 := by linarith
  let J := symmetricJoint D h0.le h1
  have hJ := symmetricJoint_feasible D h0.le h1
  apply le_antisymm
  · have h := rateDistortionDual_le_feasible_information
      (FiniteLaw.uniform : FiniteLaw Bool) boolHammingDistortion D
      (interiorMultiplier D) boolHammingDistortion_nonneg
      (interiorMultiplier_pos D h0 hhalf).le J hJ
    simpa [J, symmetricJoint_information] using h
  · unfold rateDistortionDualValue
    refine le_csInf ?_ ?_
    · exact ⟨rateDistortionLagrangian J boolHammingDistortion
        (interiorMultiplier D) - interiorMultiplier D * D, J, hJ.1, rfl⟩
    · rintro value ⟨K,hfair,rfl⟩
      have h := boolean_lagrangian_lower K hfair D h0 hhalf
      rw [boolean_rate_algebra]
      unfold rateDistortionLagrangian
      linarith

/-- Quantitative one-sided divergence. No finite endpoint multiplier is inferred
from Lean's totalized real log at zero. -/
theorem interiorMultiplier_unbounded_near_zero :
    ∀ M : ℝ, ∃ δ : ℝ, 0 < δ ∧
      ∀ D : ℝ, 0 < D → D < δ → M < interiorMultiplier D := by
  intro M
  let δ : ℝ := min (1/4) (Real.exp (-M-Real.log 2))
  refine ⟨δ, lt_min (by norm_num) (Real.exp_pos _), ?_⟩
  intro D h0 hδ
  have hquarter : D < (1:ℝ)/4 := lt_of_lt_of_le hδ (min_le_left _ _)
  have hexp : D < Real.exp (-M-Real.log 2) :=
    lt_of_lt_of_le hδ (min_le_right _ _)
  have hlogD : Real.log D < -M-Real.log 2 := by
    simpa only [Real.log_exp] using Real.log_lt_log h0 hexp
  have hlogC : -Real.log 2 ≤ Real.log (1-D) := by
    have h := Real.log_le_log (by norm_num : (0:ℝ) < 1/2)
      (show (1:ℝ)/2 ≤ 1-D by linarith)
    simpa [Real.log_div] using h
  unfold interiorMultiplier
  linarith

/-- The totalized value differs from the right-hand limiting behavior. -/
theorem interiorMultiplier_zero_totalized : interiorMultiplier 0 = 0 := by
  simp [interiorMultiplier]

end FairBoolean

end FEP.VariationalDuality

/-! ### Finite rate-distortion strong duality under strict feasibility
The actual finite-law upper image supplies convexity and boundary geometry.
Nonnegative distortion and a strictly feasible law yield attained primal/dual
extrema and complementary slackness. No full-support or uniqueness claim.
-/
set_option autoImplicit false
open FEP FEP.VariationalDuality
open scoped BigOperators
namespace FEP.VariationalDuality
namespace RateDistortionGeometry
variable {ι : Type*} [Fintype ι]

/-- Homogeneous conditional-entropy contribution of one nonnegative column.
The algebraic definition is total on real vectors. -/
noncomputable def columnEntropy (x : ι → ℝ) : ℝ :=
  (∑ i, Real.negMulLog (x i)) - Real.negMulLog (∑ i, x i)

/-- This identity includes zero scaling and zero coordinates. -/
theorem columnEntropy_smul (c : ℝ) (x : ι → ℝ) :
    columnEntropy (c • x) = c * columnEntropy x := by
  unfold columnEntropy
  simp only [Pi.smul_apply, smul_eq_mul, ← Finset.mul_sum]
  simp_rw [Real.negMulLog_mul]
  rw [Finset.sum_add_distrib, ← Finset.sum_mul, ← Finset.mul_sum]
  ring

/-- Concavity on normalized nonnegative columns uses scalar entropy concavity;
no positivity or logarithm-of-zero premise is needed. -/
theorem normalized_columnEntropy_concave (x y : ι → ℝ)
    (hx : ∀ i, 0 ≤ x i) (hy : ∀ i, 0 ≤ y i)
    (hsx : ∑ i, x i = 1) (hsy : ∑ i, y i = 1)
    (a b : ℝ) (ha : 0 ≤ a) (hb : 0 ≤ b) (hab : a + b = 1) :
    a * columnEntropy x + b * columnEntropy y ≤ columnEntropy (a • x + b • y) := by
  have hsum : ∑ i, (a • x + b • y) i = 1 := by
    simp only [Pi.add_apply, Pi.smul_apply, smul_eq_mul, Finset.sum_add_distrib,
      ← Finset.mul_sum, hsx, hsy, mul_one, hab]
  have hpoint : ∀ i, a * Real.negMulLog (x i) + b * Real.negMulLog (y i) ≤
      Real.negMulLog ((a • x + b • y) i) := by
    intro i
    exact Real.concaveOn_negMulLog.2 (hx i) (hy i) ha hb hab
  have h := Finset.sum_le_sum (fun i (_ : i ∈ Finset.univ) => hpoint i)
  simpa only [columnEntropy, hsx, hsy, hsum, Real.negMulLog_one, sub_zero,
    Finset.sum_add_distrib, ← Finset.mul_sum] using h
/-- A nonnegative zero-mass column is exactly the zero vector. -/
theorem column_eq_zero_of_sum_zero (x : ι → ℝ) (hx : ∀ i, 0 ≤ x i)
    (hs : ∑ i, x i = 0) : x = 0 := by
  classical
  funext i
  have hi : x i ≤ ∑ j, x j := Finset.single_le_sum (fun j _ => hx j) (Finset.mem_univ i)
  exact le_antisymm (hi.trans (le_of_eq hs)) (hx i)

/-- Conditional column entropy is superadditive, including zero-mass columns. -/
theorem columnEntropy_superadd (x y : ι → ℝ)
    (hx : ∀ i, 0 ≤ x i) (hy : ∀ i, 0 ≤ y i) :
    columnEntropy x + columnEntropy y ≤ columnEntropy (x + y) := by
  by_cases hx0 : (∑ i, x i) = 0
  · have hxeq := column_eq_zero_of_sum_zero x hx hx0
    simp [hxeq, columnEntropy]
  by_cases hy0 : (∑ i, y i) = 0
  · have hyeq := column_eq_zero_of_sum_zero y hy hy0
    simp [hyeq, columnEntropy]
  let sx : ℝ := ∑ i, x i
  let sy : ℝ := ∑ i, y i
  let t : ℝ := sx + sy
  have hsx : 0 < sx := lt_of_le_of_ne (Finset.sum_nonneg (fun i _ => hx i)) (Ne.symm hx0)
  have hsy : 0 < sy := lt_of_le_of_ne (Finset.sum_nonneg (fun i _ => hy i)) (Ne.symm hy0)
  have ht : 0 < t := add_pos hsx hsy
  have hnx : ∀ i, 0 ≤ (sx⁻¹ • x) i := fun i =>
    mul_nonneg (inv_nonneg.mpr (le_of_lt hsx)) (hx i)
  have hny : ∀ i, 0 ≤ (sy⁻¹ • y) i := fun i =>
    mul_nonneg (inv_nonneg.mpr (le_of_lt hsy)) (hy i)
  have hsumx : ∑ i, (sx⁻¹ • x) i = 1 := by
    simp only [Pi.smul_apply, smul_eq_mul, ← Finset.mul_sum]
    exact inv_mul_cancel₀ (ne_of_gt hsx)
  have hsumy : ∑ i, (sy⁻¹ • y) i = 1 := by
    simp only [Pi.smul_apply, smul_eq_mul, ← Finset.mul_sum]
    exact inv_mul_cancel₀ (ne_of_gt hsy)
  have hab : sx / t + sy / t = 1 := by
    rw [← add_div]
    exact div_self (ne_of_gt ht)
  have hn := normalized_columnEntropy_concave (sx⁻¹ • x) (sy⁻¹ • y)
    hnx hny hsumx hsumy (sx / t) (sy / t)
    (div_nonneg (le_of_lt hsx) (le_of_lt ht))
    (div_nonneg (le_of_lt hsy) (le_of_lt ht)) hab
  have hm : (sx / t) • (sx⁻¹ • x) + (sy / t) • (sy⁻¹ • y) = t⁻¹ • (x + y) := by
    funext i
    simp only [Pi.add_apply, Pi.smul_apply, smul_eq_mul]
    field_simp [ne_of_gt hsx, ne_of_gt hsy, ne_of_gt ht]
  rw [hm] at hn
  simp only [columnEntropy_smul] at hn
  have hcx : (sx / t) * sx⁻¹ = t⁻¹ := by
    field_simp [ne_of_gt hsx, ne_of_gt ht]
  have hcy : (sy / t) * sy⁻¹ = t⁻¹ := by
    field_simp [ne_of_gt hsy, ne_of_gt ht]
  rw [← mul_assoc, hcx, ← mul_assoc, hcy, ← mul_add] at hn
  exact (mul_le_mul_iff_right₀ (inv_pos.mpr ht)).mp hn

/-- Homogeneity and superadditivity give concavity on the entire nonnegative cone. -/
theorem columnEntropy_concave_nonnegative :
    ConcaveOn ℝ {x : ι → ℝ | ∀ i, 0 ≤ x i} columnEntropy := by
  refine ⟨?_, ?_⟩
  · intro x hx y hy a b ha hb _hab i
    exact add_nonneg (mul_nonneg ha (hx i)) (mul_nonneg hb (hy i))
  · intro x hx y hy a b ha hb _hab
    have h := columnEntropy_superadd (a • x) (b • y)
      (fun i => mul_nonneg ha (hx i)) (fun i => mul_nonneg hb (hy i))
    simpa only [columnEntropy_smul, smul_eq_mul] using h

variable {α β : Type*} [Fintype α] [Fintype β]

/-- Exact finite entropy identity; it includes zero rows and columns. -/
theorem information_eq_rowEntropy_sub_columns (x : α × β → ℝ) :
    mutualInformationOfMasses x =
      (∑ u : α, Real.negMulLog (∑ v : β, x (u, v))) -
        ∑ v : β, columnEntropy (fun u : α => x (u, v)) := by
  have hswap : (∑ xy : α × β, Real.negMulLog (x xy)) =
      ∑ v : β, ∑ u : α, Real.negMulLog (x (u, v)) := by
    rw [Fintype.sum_prod_type, Finset.sum_comm]
  unfold mutualInformationOfMasses columnEntropy
  rw [Finset.sum_sub_distrib, ← hswap]
  ring

/-- Actual entropy-form mutual information is convex at fixed first marginal.
The domain is the maintained finite-law mass carrier, with zero distortion;
no full-support condition or supplied convexity certificate is assumed. -/
theorem convexOn_information_fixed_source (p : FiniteLaw α) :
    ConvexOn ℝ (rateDistortionFeasibleMasses (β := β) p (fun _ _ => 0) 0)
      (mutualInformationOfMasses : (α × β → ℝ) → ℝ) := by
  have hconv : Convex ℝ
      (rateDistortionFeasibleMasses (β := β) p (fun _ _ => 0) 0) := by
    intro x hx y hy a b ha hb hab
    refine ⟨?_, ?_, ?_⟩
    · intro xy
      exact add_nonneg (mul_nonneg ha (hx.1 xy)) (mul_nonneg hb (hy.1 xy))
    · intro u
      simp only [Pi.add_apply, Pi.smul_apply, smul_eq_mul, Finset.sum_add_distrib,
        ← Finset.mul_sum]
      rw [hx.2.1 u, hy.2.1 u, ← add_mul, hab, one_mul]
    · simp
  refine ⟨hconv, ?_⟩
  intro x hx y hy a b ha hb hab
  have hm := hconv hx hy ha hb hab
  have hc (v : β) :
      a * columnEntropy (fun u : α => x (u, v)) +
        b * columnEntropy (fun u : α => y (u, v)) ≤
      columnEntropy (fun u : α => (a • x + b • y) (u, v)) :=
    columnEntropy_concave_nonnegative.2 (fun u => hx.1 (u, v))
      (fun u => hy.1 (u, v)) ha hb hab
  have hsum := Finset.sum_le_sum (fun v (_ : v ∈ Finset.univ) => hc v)
  simp only [Finset.sum_add_distrib, ← Finset.mul_sum] at hsum
  have hMx := information_eq_rowEntropy_sub_columns x
  have hMy := information_eq_rowEntropy_sub_columns y
  have hMm := information_eq_rowEntropy_sub_columns (a • x + b • y)
  simp_rw [hx.2.1] at hMx
  simp_rw [hy.2.1] at hMy
  simp_rw [hm.2.1] at hMm
  rw [hMm, hMx, hMy]
  have hconst : (a + b) * (∑ u : α, Real.negMulLog (p u)) =
      ∑ u : α, Real.negMulLog (p u) := by rw [hab, one_mul]
  simp only [smul_eq_mul]
  nlinarith only [hsum, hconst]

end RateDistortionGeometry
end FEP.VariationalDuality



namespace FEP.VariationalDuality
namespace RateDistortionGeometry
variable {α β : Type*} [Fintype α] [Fintype β]

/-- Coordinate distortion is affine on the existing joint-mass carrier. -/
theorem distortion_affine (d : α → β → ℝ) (x y : α × β → ℝ) (a b : ℝ) :
    (∑ xy, (a • x + b • y) xy * d xy.1 xy.2) =
      a * (∑ xy, x xy * d xy.1 xy.2) +
      b * (∑ xy, y xy * d xy.1 xy.2) := by
  simp only [Pi.add_apply, Pi.smul_apply, smul_eq_mul, add_mul,
    Finset.sum_add_distrib, mul_assoc, ← Finset.mul_sum]

/-- Feasibility is convex without assuming an optimizer, information convexity,
or a duality equation. Zero source rows and output columns remain allowed. -/
theorem convex_feasible (p : FiniteLaw α) (d : α → β → ℝ) (D : ℝ) :
    Convex ℝ (rateDistortionFeasibleMasses p d D) := by
  intro x hx y hy a b ha hb hab
  refine ⟨?_, ?_, ?_⟩
  · intro xy
    exact add_nonneg (mul_nonneg ha (hx.1 xy)) (mul_nonneg hb (hy.1 xy))
  · intro u
    simp only [Pi.add_apply, Pi.smul_apply, smul_eq_mul,
      Finset.sum_add_distrib, ← Finset.mul_sum]
    rw [hx.2.1 u, hy.2.1 u, ← add_mul, hab, one_mul]
  · rw [distortion_affine]
    calc
      a * (∑ xy, x xy * d xy.1 xy.2) + b * (∑ xy, y xy * d xy.1 xy.2) ≤
          a * D + b * D := add_le_add
            (mul_le_mul_of_nonneg_left hx.2.2 ha)
            (mul_le_mul_of_nonneg_left hy.2.2 hb)
      _ = D := by rw [← add_mul, hab, one_mul]

/-- Fixed first marginal with no distortion restriction. -/
abbrev FixedSourceMasses (p : FiniteLaw α) : Set (α × β → ℝ) :=
  rateDistortionFeasibleMasses p (fun _ _ => 0) 0

/-- Actual finite information/distortion upper image; zero atoms remain allowed. -/
noncomputable def rateDistortionUpperImage (p : FiniteLaw α)
    (d : α → β → ℝ) : Set (ℝ × ℝ) :=
  {z | ∃ x ∈ FixedSourceMasses (β := β) p,
    (∑ xy, x xy * d xy.1 xy.2) ≤ z.1 ∧ mutualInformationOfMasses x ≤ z.2}

/-- This explicitly conditional theorem does not establish information convexity. -/
theorem convex_upperImage_of_information_convex
    (p : FiniteLaw α) (d : α → β → ℝ)
    (hMI : ConvexOn ℝ (FixedSourceMasses (β := β) p)
      (mutualInformationOfMasses : (α × β → ℝ) → ℝ)) :
    Convex ℝ (rateDistortionUpperImage p d) := by
  intro z hz v hv a b ha hb hab
  obtain ⟨x, hx, hxd, hxi⟩ := hz
  obtain ⟨y, hy, hyd, hyi⟩ := hv
  refine ⟨a • x + b • y, convex_feasible p (fun _ _ => 0) 0 hx hy ha hb hab, ?_, ?_⟩
  · rw [distortion_affine]
    exact add_le_add (mul_le_mul_of_nonneg_left hxd ha)
      (mul_le_mul_of_nonneg_left hyd hb)
  · exact (hMI.2 hx hy ha hb hab).trans
      (add_le_add (mul_le_mul_of_nonneg_left hxi ha)
        (mul_le_mul_of_nonneg_left hyi hb))

theorem upperImage_upward_distortion (p : FiniteLaw α) (d : α → β → ℝ)
    (z : ℝ × ℝ) (t : ℝ) (ht : 0 ≤ t)
    (hz : z ∈ rateDistortionUpperImage p d) :
    (z.1 + t, z.2) ∈ rateDistortionUpperImage p d := by
  obtain ⟨x, hx, hxd, hxi⟩ := hz
  exact ⟨x, hx, hxd.trans (le_add_of_nonneg_right ht), hxi⟩

theorem upperImage_upward_information (p : FiniteLaw α) (d : α → β → ℝ)
    (z : ℝ × ℝ) (t : ℝ) (ht : 0 ≤ t)
    (hz : z ∈ rateDistortionUpperImage p d) :
    (z.1, z.2 + t) ∈ rateDistortionUpperImage p d := by
  obtain ⟨x, hx, hxd, hxi⟩ := hz
  exact ⟨x, hx, hxd, hxi.trans (le_add_of_nonneg_right ht)⟩
/-- The coordinate upper image is exactly the existing finite-law image.
No information-convexity or optimizer assumption is needed for this equality. -/
theorem upperImage_iff_joint (p : FiniteLaw α) (d : α → β → ℝ) (z : ℝ × ℝ) :
    z ∈ rateDistortionUpperImage p d ↔
      ∃ J : FiniteLaw (α × β), J.fstMarginal = p ∧
        expectedDistortion J d ≤ z.1 ∧ FEP.FiniteInformation.mutualInformation J ≤ z.2 := by
  constructor
  · rintro ⟨x, hx, hxd, hxi⟩
    let J := rateDistortionLawOfMasses p (fun _ _ => 0) 0 x hx
    refine ⟨J, (rateDistortionLawOfMasses_feasible p (fun _ _ => 0) 0 x hx).1,
      hxd, ?_⟩
    rw [← mutualInformationOfMasses_eq J]
    exact hxi
  · rintro ⟨J, hJ, hD, hI⟩
    have hz : RateDistortionFeasible p (fun _ _ => 0) 0 J :=
      ⟨hJ, by simp [expectedDistortion]⟩
    refine ⟨J.mass, rateDistortionFeasible_mass_mem p (fun _ _ => 0) 0 J hz,
      hD, ?_⟩
    simpa only [mutualInformationOfMasses_eq] using hI

/-- Unconditional convexity of the actual finite-law upper image, including zero atoms. -/
theorem convex_actual_upperImage (p : FiniteLaw α) (d : α → β → ℝ) :
    Convex ℝ (rateDistortionUpperImage p d) :=
  convex_upperImage_of_information_convex p d
    (FEP.VariationalDuality.RateDistortionGeometry.convexOn_information_fixed_source p)

end RateDistortionGeometry
end FEP.VariationalDuality

namespace FEP.VariationalDuality
namespace RateDistortionGeometry
variable {α β : Type*} [Fintype α] [Fintype β]

/-- Any actual fixed-source joint supplies an open quadrant in the upper image. -/
theorem upperImage_nonempty_interior (p : FiniteLaw α) (d : α → β → ℝ)
    (J : FiniteLaw (α × β)) (hJ : J.fstMarginal = p) :
    (interior (rateDistortionUpperImage p d)).Nonempty := by
  let U : Set (ℝ × ℝ) := {z | expectedDistortion J d < z.1 ∧
    FEP.FiniteInformation.mutualInformation J < z.2}
  have hU : IsOpen U :=
    (isOpen_lt continuous_const continuous_fst).inter
      (isOpen_lt continuous_const continuous_snd)
  have hsub : U ⊆ rateDistortionUpperImage p d := by
    intro z hz
    exact (upperImage_iff_joint p d z).2 ⟨J, hJ, le_of_lt hz.1, le_of_lt hz.2⟩
  have hz : (expectedDistortion J d + 1,
      FEP.FiniteInformation.mutualInformation J + 1) ∈ U := by
    constructor <;> dsimp <;> linarith
  refine ⟨(expectedDistortion J d + 1, FEP.FiniteInformation.mutualInformation J + 1), ?_⟩
  exact interior_mono hsub (by rwa [hU.interior_eq])
end RateDistortionGeometry
end FEP.VariationalDuality

namespace FEP.VariationalDuality
namespace RateDistortionGeometry
variable {α β : Type*} [Fintype α] [Fintype β]

/-- An actual feasible information minimizer lies outside the upper-image interior. -/
theorem optimizer_not_interior (p : FiniteLaw α) (d : α → β → ℝ) (D : ℝ)
    (J : FiniteLaw (α × β))
    (hmin : ∀ K, RateDistortionFeasible p d D K →
      FEP.FiniteInformation.mutualInformation J ≤ FEP.FiniteInformation.mutualInformation K) :
    (D, FEP.FiniteInformation.mutualInformation J) ∉
      interior (rateDistortionUpperImage p d) := by
  intro hint
  obtain ⟨ε, hε, hball⟩ := Metric.mem_nhds_iff.mp (mem_interior_iff_mem_nhds.mp hint)
  have hnear : (D, FEP.FiniteInformation.mutualInformation J - ε / 2) ∈
      Metric.ball (D, FEP.FiniteInformation.mutualInformation J) ε := by
    rw [Metric.mem_ball, Prod.dist_eq]
    simp only [dist_self, Real.dist_eq]
    rw [max_lt_iff]
    constructor
    · exact hε
    · rw [show FEP.FiniteInformation.mutualInformation J - ε / 2 -
          FEP.FiniteInformation.mutualInformation J = -(ε / 2) by ring,
        abs_neg, abs_of_pos (by linarith : 0 < ε / 2)]
      linarith
  obtain ⟨K, hK, hD, hI⟩ := (upperImage_iff_joint p d _).mp (hball hnear)
  have h := hmin K ⟨hK, hD⟩
  linarith

/-- Compactness supplies the actual optimizer and its upper-image boundary point. -/
theorem exists_optimizer_boundary (p : FiniteLaw α) (d : α → β → ℝ) (D : ℝ)
    (hfeasible : ∃ J, RateDistortionFeasible p d D J) :
    ∃ J : FiniteLaw (α × β), RateDistortionFeasible p d D J ∧
      (D, FEP.FiniteInformation.mutualInformation J) ∈ rateDistortionUpperImage p d ∧
      (D, FEP.FiniteInformation.mutualInformation J) ∉
        interior (rateDistortionUpperImage p d) := by
  obtain ⟨J, hJ, hmin⟩ := rateDistortion_exists_minimizer p d D hfeasible
  exact ⟨J, hJ, (upperImage_iff_joint p d _).2 ⟨J, hJ.1, hJ.2, le_rfl⟩,
    optimizer_not_interior p d D J hmin⟩
end RateDistortionGeometry
end FEP.VariationalDuality

namespace FEP.VariationalDuality
namespace RateDistortionGeometry

/-- A lower-bounded full nonnegative ray cannot have negative slope. -/
theorem nonneg_of_bounded_below_ray (a c L : ℝ)
    (h : ∀ t : ℝ, 0 ≤ t → L ≤ c + t * a) : 0 ≤ a := by
  by_contra hn
  have ha : a < 0 := lt_of_not_ge hn
  have hc : L ≤ c := by simpa using h 0 (le_refl 0)
  have hden : 0 < -a := neg_pos.mpr ha
  have ht : 0 ≤ (c - L + 1) / (-a) := div_nonneg (by linarith) hden.le
  have heq := div_mul_cancel₀ (c - L + 1) (ne_of_gt hden)
  have hb := h ((c - L + 1) / (-a)) ht
  nlinarith

/-- Normalize an upward-closed lower support using strict feasibility only.
The support point need not belong to the set; no optimizer is assumed. -/
theorem normalize_lower_support_coefficients
    (C : Set (ℝ × ℝ)) (P : ℝ × ℝ) (a b : ℝ)
    (hupD : ∀ z ∈ C, ∀ t : ℝ, 0 ≤ t → (z.1 + t, z.2) ∈ C)
    (hupR : ∀ z ∈ C, ∀ t : ℝ, 0 ≤ t → (z.1, z.2 + t) ∈ C)
    (hsupport : ∀ z ∈ C, a * P.1 + b * P.2 ≤ a * z.1 + b * z.2)
    (hnonzero : a ≠ 0 ∨ b ≠ 0)
    (hslater : ∃ z ∈ C, z.1 < P.1) :
    0 ≤ a ∧ 0 < b ∧ 0 ≤ a / b ∧
      ∀ z ∈ C, P.2 ≤ z.2 + (a / b) * (z.1 - P.1) := by
  obtain ⟨z₀, hz₀, hstrict⟩ := hslater
  have ha : 0 ≤ a := nonneg_of_bounded_below_ray a
      (a * z₀.1 + b * z₀.2) (a * P.1 + b * P.2) (by
    intro t ht
    have hs := hsupport (z₀.1 + t, z₀.2) (hupD z₀ hz₀ t ht)
    dsimp at hs
    nlinarith)
  have hb : 0 ≤ b := nonneg_of_bounded_below_ray b
      (a * z₀.1 + b * z₀.2) (a * P.1 + b * P.2) (by
    intro t ht
    have hs := hsupport (z₀.1, z₀.2 + t) (hupR z₀ hz₀ t ht)
    dsimp at hs
    nlinarith)
  have hbpos : 0 < b := by
    by_contra hn
    have hbzero : b = 0 := le_antisymm (le_of_not_gt hn) hb
    have hane : a ≠ 0 := hnonzero.resolve_right (by simp [hbzero])
    have hapos : 0 < a := lt_of_le_of_ne ha (Ne.symm hane)
    have hs := hsupport z₀ hz₀
    have hm := mul_lt_mul_of_pos_left hstrict hapos
    simp only [hbzero, zero_mul, add_zero] at hs
    linarith
  refine ⟨ha, hbpos, div_nonneg ha hbpos.le, ?_⟩
  intro z hz
  have hs := hsupport z hz
  apply (mul_le_mul_iff_of_pos_right hbpos).mp
  have heq : (a / b) * b = a := div_mul_cancel₀ a (ne_of_gt hbpos)
  calc
    P.2 * b ≤ z.2 * b + a * (z.1 - P.1) := by nlinarith
    _ = (z.2 + (a / b) * (z.1 - P.1)) * b := by
      rw [add_mul]
      congr 1
      calc
        a * (z.1 - P.1) = ((a / b) * b) * (z.1 - P.1) := by rw [heq]
        _ = (a / b) * (z.1 - P.1) * b := by ring

def UpD (C : Set (ℝ × ℝ)) : Prop := ∀ z ∈ C, ∀ t : ℝ, 0 ≤ t → (z.1 + t, z.2) ∈ C
def UpR (C : Set (ℝ × ℝ)) : Prop := ∀ z ∈ C, ∀ t : ℝ, 0 ≤ t → (z.1, z.2 + t) ∈ C
def Lower (C : Set (ℝ × ℝ)) (P : ℝ × ℝ) (a b : ℝ) : Prop :=
  ∀ z ∈ C, a * P.1 + b * P.2 ≤ a * z.1 + b * z.2
def Slater (C : Set (ℝ × ℝ)) (P : ℝ × ℝ) : Prop := ∃ z ∈ C, z.1 < P.1
/-- The actual pinned separation API supplies a nonzero lower supporting normal.
The caller supplies its own convexity/interior proof. -/
theorem nonzero_lower_support (C : Set (ℝ × ℝ)) (P : ℝ × ℝ)
    (hC : Convex ℝ C) (hint : (interior C).Nonempty)
    (hboundary : P ∉ interior C) :
    ∃ f : StrongDual ℝ (ℝ × ℝ), f ≠ 0 ∧ ∀ z ∈ C, f P ≤ f z := by
  have hdis : Disjoint (interior C) ({P} : Set (ℝ × ℝ)) := by
    simpa only [Set.disjoint_singleton_right] using hboundary
  obtain ⟨f, u, hf, hCs, hp⟩ := geometric_hahn_banach_of_nonempty_interior
    hC (convex_singleton P) hdis hint (Set.singleton_nonempty P)
  refine ⟨-f, neg_ne_zero.mpr hf, ?_⟩
  intro z hz
  have hleft := hCs z hz
  have hright := hp P (by simp)
  change -f P ≤ -f z
  linarith

/-- Coordinate coefficients are derived from the real continuous linear map. -/
theorem coefficient_decomposition (f : StrongDual ℝ (ℝ × ℝ)) (d r : ℝ) :
    f (d, r) = d * f (1, 0) + r * f (0, 1) := by
  have h : (d, r) = d • ((1, 0) : ℝ × ℝ) + r • ((0, 1) : ℝ × ℝ) := by
    ext <;> simp
  rw [h, map_add, map_smul, map_smul]
  simp only [smul_eq_mul]

/-- Nonzero functional support normalizes without attainment or P-membership. -/
theorem normalize_lower_support_functional
    (C : Set (ℝ × ℝ)) (P : ℝ × ℝ) (f : StrongDual ℝ (ℝ × ℝ))
    (hupD : UpD C) (hupR : UpR C)
    (hsupport : ∀ z ∈ C, f P ≤ f z) (hf : f ≠ 0) (hslater : Slater C P) :
    0 ≤ f (1,0) ∧ 0 < f (0,1) ∧ 0 ≤ f (1,0) / f (0,1) ∧
      ∀ z ∈ C, P.2 ≤ z.2 + (f (1,0) / f (0,1)) * (z.1 - P.1) := by
  have expand (z : ℝ × ℝ) : f z = f (1,0) * z.1 + f (0,1) * z.2 := by
    simpa only [mul_comm] using coefficient_decomposition f z.1 z.2
  have hnonzero : f (1,0) ≠ 0 ∨ f (0,1) ≠ 0 := by
    by_contra hn
    have ha : f (1,0) = 0 := by tauto
    have hb : f (0,1) = 0 := by tauto
    apply hf
    apply ContinuousLinearMap.ext
    intro z
    change f z = 0
    rw [expand, ha, hb]
    ring
  apply normalize_lower_support_coefficients C P (f (1,0)) (f (0,1)) hupD hupR
  · intro z hz
    have hs := hsupport z hz
    rw [expand P, expand z] at hs
    exact hs
  · exact hnonzero
  · exact hslater

/-- Separation plus strict feasibility yields a nonnegative scalar support.
Actual rate-distortion geometry is deliberately a caller obligation. -/
theorem scalar_support_from_geometry
    (C : Set (ℝ × ℝ)) (P : ℝ × ℝ)
    (hC : Convex ℝ C) (hint : (interior C).Nonempty)
    (hboundary : P ∉ interior C) (hupD : UpD C) (hupR : UpR C)
    (hslater : Slater C P) :
    ∃ lam : ℝ, 0 ≤ lam ∧ ∀ z ∈ C, P.2 ≤ z.2 + lam * (z.1 - P.1) := by
  obtain ⟨f, hf, hs⟩ := nonzero_lower_support C P hC hint hboundary
  obtain ⟨_, _, hlam, hbound⟩ := normalize_lower_support_functional C P f hupD hupR hs hf hslater
  exact ⟨f (1,0) / f (0,1), hlam, hbound⟩
end RateDistortionGeometry
end FEP.VariationalDuality





namespace FEP.VariationalDuality
namespace RateDistortionGeometry
variable {α β : Type*} [Fintype α] [Fintype β]

/-- Strict actual feasibility produces a nonnegative Lagrange support multiplier. -/
theorem actual_slater_support (p : FiniteLaw α) (d : α → β → ℝ) (D : ℝ)
    (J : FiniteLaw (α × β))
    (hmin : ∀ K, RateDistortionFeasible p d D K →
      FEP.FiniteInformation.mutualInformation J ≤ FEP.FiniteInformation.mutualInformation K)
    (hslater : ∃ K : FiniteLaw (α × β), K.fstMarginal = p ∧ expectedDistortion K d < D) :
    ∃ lam : ℝ, 0 ≤ lam ∧ ∀ K : FiniteLaw (α × β), K.fstMarginal = p →
      FEP.FiniteInformation.mutualInformation J ≤
        FEP.FiniteInformation.mutualInformation K + lam * (expectedDistortion K d - D) := by
  obtain ⟨K₀, hK₀, hstrict⟩ := hslater
  obtain ⟨lam, hlam, hbound⟩ := FEP.VariationalDuality.RateDistortionGeometry.scalar_support_from_geometry
    (rateDistortionUpperImage p d) (D, FEP.FiniteInformation.mutualInformation J)
    (convex_actual_upperImage p d) (upperImage_nonempty_interior p d K₀ hK₀)
    (optimizer_not_interior p d D J hmin)
    (fun z hz t ht => upperImage_upward_distortion p d z t ht hz)
    (fun z hz t ht => upperImage_upward_information p d z t ht hz)
    ⟨(expectedDistortion K₀ d, FEP.FiniteInformation.mutualInformation K₀),
      (upperImage_iff_joint p d _).2 ⟨K₀, hK₀, le_rfl, le_rfl⟩, hstrict⟩
  refine ⟨lam, hlam, ?_⟩
  intro K hK
  exact hbound (expectedDistortion K d, FEP.FiniteInformation.mutualInformation K)
    ((upperImage_iff_joint p d _).2 ⟨K, hK, le_rfl, le_rfl⟩)

/-- Actual finite-law strong duality under strict feasibility; both extrema are
constructed from compactness and separation, with zero atoms allowed. -/
theorem exists_actual_strong_duality (p : FiniteLaw α) (d : α → β → ℝ) (D : ℝ)
    (hd : ∀ x y, 0 ≤ d x y)
    (hslater : ∃ K : FiniteLaw (α × β), K.fstMarginal = p ∧ expectedDistortion K d < D) :
    ∃ J : FiniteLaw (α × β), RateDistortionFeasible p d D J ∧
      (∀ K, RateDistortionFeasible p d D K →
        FEP.FiniteInformation.mutualInformation J ≤ FEP.FiniteInformation.mutualInformation K) ∧
      ∃ lam : ℝ, 0 ≤ lam ∧
        rateDistortionDualValue p d D lam = FEP.FiniteInformation.mutualInformation J := by
  have hfeasible : ∃ K, RateDistortionFeasible p d D K := by
    obtain ⟨K,hK,hD⟩ := hslater
    exact ⟨K,hK,le_of_lt hD⟩
  obtain ⟨J,hJ,hmin⟩ := rateDistortion_exists_minimizer p d D hfeasible
  obtain ⟨lam,hlam,hbound⟩ := actual_slater_support p d D J hmin hslater
  refine ⟨J,hJ,hmin,lam,hlam,le_antisymm
    (rateDistortionDual_le_feasible_information p d D lam hd hlam J hJ) ?_⟩
  unfold rateDistortionDualValue
  apply le_csInf
  · exact ⟨rateDistortionLagrangian J d lam - lam * D,J,hJ.1,rfl⟩
  · rintro value ⟨K,hK,rfl⟩
    have h := hbound K hK
    unfold rateDistortionLagrangian
    nlinarith only [h]
end RateDistortionGeometry
end FEP.VariationalDuality

namespace FEP.VariationalDuality
namespace RateDistortionGeometry
variable {α β : Type*} [Fintype α] [Fintype β]

/-- Strong duality also gives the primal infimum, dual supremum and slackness. -/
theorem actual_primal_dual_extrema (p : FiniteLaw α) (d : α → β → ℝ) (D : ℝ)
    (hd : ∀ x y, 0 ≤ d x y)
    (hslater : ∃ K : FiniteLaw (α × β), K.fstMarginal = p ∧ expectedDistortion K d < D) :
    ∃ J : FiniteLaw (α × β), RateDistortionFeasible p d D J ∧
      ∃ lam : ℝ, 0 ≤ lam ∧
        rateDistortionDualValue p d D lam = FEP.FiniteInformation.mutualInformation J ∧
        lam * (expectedDistortion J d - D) = 0 ∧
        sInf {v : ℝ | ∃ K, RateDistortionFeasible p d D K ∧
          v = FEP.FiniteInformation.mutualInformation K} =
            FEP.FiniteInformation.mutualInformation J ∧
        sSup {v : ℝ | ∃ t : ℝ, 0 ≤ t ∧ v = rateDistortionDualValue p d D t} =
          FEP.FiniteInformation.mutualInformation J := by
  obtain ⟨J,hJ,hmin,lam,hlam,heq⟩ := exists_actual_strong_duality p d D hd hslater
  have hbounded := rateDistortionDual_bddBelow p d D lam hd hlam
  have hdualJ : rateDistortionDualValue p d D lam ≤
      rateDistortionLagrangian J d lam - lam * D :=
    csInf_le hbounded ⟨J,hJ.1,rfl⟩
  have hslack : lam * (expectedDistortion J d - D) = 0 := by
    have hnonpos := mul_nonpos_of_nonneg_of_nonpos hlam (sub_nonpos.mpr hJ.2)
    unfold rateDistortionLagrangian at hdualJ
    rw [heq] at hdualJ
    nlinarith only [hdualJ,hnonpos]
  refine ⟨J,hJ,lam,hlam,heq,hslack,?_,?_⟩
  · apply le_antisymm
    · apply csInf_le
      · exact ⟨0,by rintro v ⟨K,_,rfl⟩; exact FEP.FiniteInformation.mutualInformation_nonneg K⟩
      · exact ⟨J,hJ,rfl⟩
    · apply le_csInf
      · exact ⟨FEP.FiniteInformation.mutualInformation J,J,hJ,rfl⟩
      · rintro v ⟨K,hK,rfl⟩
        exact hmin K hK
  · apply le_antisymm
    · apply csSup_le
      · exact ⟨rateDistortionDualValue p d D lam,lam,hlam,rfl⟩
      · rintro v ⟨t,ht,rfl⟩
        exact rateDistortionDual_le_feasible_information p d D t hd ht J hJ
    · rw [← heq]
      apply le_csSup
      · refine ⟨FEP.FiniteInformation.mutualInformation J,?_⟩
        rintro v ⟨t,ht,rfl⟩
        exact rateDistortionDual_le_feasible_information p d D t hd ht J hJ
      · exact ⟨lam,hlam,rfl⟩
end RateDistortionGeometry
end FEP.VariationalDuality

namespace FEP.VariationalDuality
namespace RateDistortionGeometry
/-- The existing informative fair Boolean quarter-budget problem satisfies
actual Slater and has a positive primal optimum attained by the dual. -/
theorem boolQuarterBudget_actual_dual_optimizer :
    ∃ J : FiniteLaw (Bool × Bool),
      RateDistortionFeasible FiniteLaw.uniform boolHammingDistortion (1 / 4) J ∧
      0 < FEP.FiniteInformation.mutualInformation J ∧
      ∃ lam : ℝ, 0 ≤ lam ∧
        rateDistortionDualValue FiniteLaw.uniform boolHammingDistortion (1 / 4) lam =
          FEP.FiniteInformation.mutualInformation J ∧
        lam * (expectedDistortion J boolHammingDistortion - 1 / 4) = 0 := by
  have hd : ∀ x y : Bool, 0 ≤ boolHammingDistortion x y := by
    intro x y
    simp only [boolHammingDistortion]
    split <;> norm_num
  have hs : ∃ K : FiniteLaw (Bool × Bool), K.fstMarginal = FiniteLaw.uniform ∧
      expectedDistortion K boolHammingDistortion < 1 / 4 := by
    refine ⟨boolZeroDistortionJoint,boolZeroDistortionJoint_feasible.1,?_⟩
    have h := boolZeroDistortionJoint_feasible.2
    linarith
  obtain ⟨J,hJ,lam,hlam,heq,hslack,_,_⟩ := actual_primal_dual_extrema
    (FiniteLaw.uniform : FiniteLaw Bool) boolHammingDistortion (1 / 4) hd hs
  exact ⟨J,hJ,boolFeasible_information_pos (1 / 4) (by norm_num) J hJ,
    lam,hlam,heq,hslack⟩
end RateDistortionGeometry
end FEP.VariationalDuality

namespace FEP.VariationalDuality
namespace RateDistortionGeometry
/-- Zero-distortion zero-budget is a real no-Slater boundary where the
independent law and zero multiplier still attain equal zero values. -/
theorem zeroBudget_zeroDistortion_control :
    let p : FiniteLaw Bool := FiniteLaw.uniform
    let J := p.product (FiniteLaw.pointMass false)
    RateDistortionFeasible p (fun _ _ : Bool => (0 : ℝ)) 0 J ∧
      FEP.FiniteInformation.mutualInformation J = 0 ∧
      rateDistortionDualValue p (fun _ _ : Bool => (0 : ℝ)) 0 0 =
        FEP.FiniteInformation.mutualInformation J ∧
      ¬ (∃ K : FiniteLaw (Bool × Bool), K.fstMarginal = p ∧
        expectedDistortion K (fun _ _ => 0) < 0) := by
  dsimp only
  refine ⟨⟨FiniteLaw.product_fstMarginal _ _,by simp [expectedDistortion]⟩,
    FEP.FiniteInformation.mutualInformation_product_eq_zero _ _,?_,?_⟩
  · rw [rateDistortionDual_zeroMultiplier,
      FEP.FiniteInformation.mutualInformation_product_eq_zero]
  · simp [expectedDistortion]

theorem negativeBudget_infeasible_control :
    ¬ ∃ J : FiniteLaw (Bool × Bool),
      RateDistortionFeasible FiniteLaw.uniform boolHammingDistortion (-1) J :=
  rateDistortion_infeasible_of_negativeBudget _ _ _
    boolHammingDistortion_nonneg (by norm_num)

theorem nonunique_minimizer_control :
    ∃ left right : FiniteLaw (Bool × Bool), left ≠ right ∧
      (RateDistortionFeasible FiniteLaw.uniform boolHammingDistortion (1 / 2) left ∧
        ∀ K, RateDistortionFeasible FiniteLaw.uniform boolHammingDistortion (1 / 2) K →
          FEP.FiniteInformation.mutualInformation left ≤ FEP.FiniteInformation.mutualInformation K) ∧
      (RateDistortionFeasible FiniteLaw.uniform boolHammingDistortion (1 / 2) right ∧
        ∀ K, RateDistortionFeasible FiniteLaw.uniform boolHammingDistortion (1 / 2) K →
          FEP.FiniteInformation.mutualInformation right ≤ FEP.FiniteInformation.mutualInformation K) :=
  boolHalfBudget_distinct_minimizers
end RateDistortionGeometry
end FEP.VariationalDuality

namespace FEP.VariationalDuality
variable {α β : Type*} [Fintype α] [Fintype β]
/-- Mutual information is convex over the actual fixed-source finite-law mass carrier. -/
theorem mutualInformationOfMasses_convexOn_fixedSource (p : FiniteLaw α) :
    ConvexOn ℝ (rateDistortionFeasibleMasses (β := β) p (fun _ _ => 0) 0)
      (mutualInformationOfMasses : (α × β → ℝ) → ℝ) :=
  RateDistortionGeometry.convexOn_information_fixed_source p
end FEP.VariationalDuality


namespace FEP.VariationalDuality
variable {α β : Type*} [Fintype α] [Fintype β]
theorem rateDistortion_exists_slater_dual_optimizer (p : FiniteLaw α) (d : α → β → ℝ) (D : ℝ)
    (hd : ∀ x y, 0 ≤ d x y)
    (hslater : ∃ K : FiniteLaw (α × β), K.fstMarginal = p ∧ expectedDistortion K d < D) :
    ∃ J : FiniteLaw (α × β), RateDistortionFeasible p d D J ∧
      (∀ K, RateDistortionFeasible p d D K →
        FEP.FiniteInformation.mutualInformation J ≤ FEP.FiniteInformation.mutualInformation K) ∧
      ∃ lam : ℝ, 0 ≤ lam ∧
        rateDistortionDualValue p d D lam = FEP.FiniteInformation.mutualInformation J :=
  RateDistortionGeometry.exists_actual_strong_duality p d D hd hslater

theorem rateDistortion_primal_dual_extrema (p : FiniteLaw α) (d : α → β → ℝ) (D : ℝ)
    (hd : ∀ x y, 0 ≤ d x y)
    (hslater : ∃ K : FiniteLaw (α × β), K.fstMarginal = p ∧ expectedDistortion K d < D) :
    ∃ J : FiniteLaw (α × β), RateDistortionFeasible p d D J ∧
      ∃ lam : ℝ, 0 ≤ lam ∧
        rateDistortionDualValue p d D lam = FEP.FiniteInformation.mutualInformation J ∧
        lam * (expectedDistortion J d - D) = 0 ∧
        sInf {v : ℝ | ∃ K, RateDistortionFeasible p d D K ∧
          v = FEP.FiniteInformation.mutualInformation K} =
            FEP.FiniteInformation.mutualInformation J ∧
        sSup {v : ℝ | ∃ t : ℝ, 0 ≤ t ∧ v = rateDistortionDualValue p d D t} =
          FEP.FiniteInformation.mutualInformation J :=
  RateDistortionGeometry.actual_primal_dual_extrema p d D hd hslater
end FEP.VariationalDuality

open scoped Pointwise
namespace FEP.VariationalDuality
namespace RateDistortionGeometry
variable {α β : Type*} [Fintype α] [Fintype β]
/-- Compact actual information/distortion image plus the closed nonnegative
quadrant makes the actual upper image closed, including feasible endpoints. -/
theorem upperImage_closed (p : FiniteLaw α) (d : α → β → ℝ) :
    IsClosed (rateDistortionUpperImage p d) := by
  let F : (α × β → ℝ) → ℝ × ℝ := fun x =>
    (∑ xy, x xy * d xy.1 xy.2, mutualInformationOfMasses x)
  let Q : Set (ℝ × ℝ) := {z | 0 ≤ z.1 ∧ 0 ≤ z.2}
  have hF : Continuous F := by
    apply Continuous.prodMk
    · apply continuous_finsetSum
      intro xy _
      exact (continuous_apply xy).mul continuous_const
    · exact continuous_mutualInformationOfMasses
  have hK := (isCompact_rateDistortionFeasibleMasses (β := β) p (fun _ _ => 0) 0).image hF
  have hQ : IsClosed Q :=
    (isClosed_le continuous_const continuous_fst).inter
      (isClosed_le continuous_const continuous_snd)
  have heq : rateDistortionUpperImage p d = F '' FixedSourceMasses (β := β) p + Q := by
    ext z
    constructor
    · rintro ⟨x,hx,hD,hI⟩
      refine ⟨F x,⟨x,hx,rfl⟩,z-F x,?_,?_⟩
      · exact ⟨sub_nonneg.mpr hD,sub_nonneg.mpr hI⟩
      · exact add_sub_cancel _ _
    · rintro ⟨u,⟨x,hx,rfl⟩,q,hq,rfl⟩
      refine ⟨x,hx,?_,?_⟩
      · exact le_add_of_nonneg_right hq.1
      · exact le_add_of_nonneg_right hq.2
  rw [heq]
  exact hQ.add_left_of_isCompact hK
end RateDistortionGeometry
end FEP.VariationalDuality

namespace FEP.VariationalDuality
namespace RateDistortionGeometry
variable {α β : Type*} [Fintype α] [Fintype β]
/-- Strict separation below the primal optimum normalizes without Slater:
a same-budget feasible point forces the objective coefficient positive. -/
theorem epsilon_dual_lower_bound (p : FiniteLaw α) (d : α → β → ℝ) (D : ℝ)
    (J : FiniteLaw (α × β)) (hJ : RateDistortionFeasible p d D J)
    (hmin : ∀ K, RateDistortionFeasible p d D K →
      FEP.FiniteInformation.mutualInformation J ≤ FEP.FiniteInformation.mutualInformation K)
    (ε : ℝ) (hε : 0 < ε) :
    ∃ lam : ℝ, 0 ≤ lam ∧
      FEP.FiniteInformation.mutualInformation J - ε ≤ rateDistortionDualValue p d D lam := by
  let R := FEP.FiniteInformation.mutualInformation J
  let P : ℝ × ℝ := (D,R-ε)
  have hnot : P ∉ rateDistortionUpperImage p d := by
    intro hP
    obtain ⟨K,hK,hD,hI⟩ := (upperImage_iff_joint p d P).mp hP
    have hm := hmin K ⟨hK,hD⟩
    dsimp [P,R] at hI
    linarith
  obtain ⟨f,u,hP,hC⟩ := geometric_hahn_banach_point_closed
    (convex_actual_upperImage p d) (upperImage_closed p d) hnot
  let a := f (1,0)
  let b := f (0,1)
  have expand (z : ℝ × ℝ) : f z = a*z.1+b*z.2 := by
    simpa only [a,b,mul_comm] using
      FEP.VariationalDuality.RateDistortionGeometry.coefficient_decomposition f z.1 z.2
  have hZ : (D,R) ∈ rateDistortionUpperImage p d :=
    (upperImage_iff_joint p d _).2 ⟨J,hJ.1,hJ.2,le_rfl⟩
  have hgap := hP.trans (hC (D,R) hZ)
  rw [expand P,expand (D,R)] at hgap
  have hbε : 0 < b*ε := by dsimp [P] at hgap; nlinarith only [hgap]
  have hb : 0 < b := (mul_pos_iff_of_pos_right hε).mp hbε
  have ha : 0 ≤ a := FEP.VariationalDuality.RateDistortionGeometry.nonneg_of_bounded_below_ray a
    (f (D,R)) (f P) (by
      intro t ht
      have hh := (hP.trans (hC (D+t,R)
        (upperImage_upward_distortion p d (D,R) t ht hZ))).le
      rw [expand P,expand (D+t,R)] at hh
      rw [expand (D,R),expand P]
      dsimp [P] at *
      nlinarith only [hh])
  let lam := a/b
  have hbound (K : FiniteLaw (α × β)) (hK : K.fstMarginal = p) :
      R-ε ≤ FEP.FiniteInformation.mutualInformation K + lam*(expectedDistortion K d-D) := by
    have hs := (hP.trans (hC (expectedDistortion K d,FEP.FiniteInformation.mutualInformation K)
      ((upperImage_iff_joint p d _).2 ⟨K,hK,le_rfl,le_rfl⟩))).le
    rw [expand P,expand _] at hs
    dsimp [P] at hs
    apply (mul_le_mul_iff_of_pos_right hb).mp
    rw [add_mul]
    have heq : lam*(expectedDistortion K d-D)*b = a*(expectedDistortion K d-D) := by
      calc
        lam*(expectedDistortion K d-D)*b = (a/b*b)*(expectedDistortion K d-D) := by dsimp [lam]; ring
        _ = a*(expectedDistortion K d-D) := by rw [div_mul_cancel₀ a (ne_of_gt hb)]
    rw [heq]
    nlinarith only [hs]
  refine ⟨lam,div_nonneg ha hb.le,?_⟩
  unfold rateDistortionDualValue
  apply le_csInf
  · exact ⟨rateDistortionLagrangian J d lam-lam*D,J,hJ.1,rfl⟩
  · rintro value ⟨K,hK,rfl⟩
    have hs := hbound K hK
    unfold rateDistortionLagrangian
    nlinarith only [hs]
end RateDistortionGeometry
end FEP.VariationalDuality

namespace FEP.VariationalDuality
namespace RateDistortionGeometry
variable {α β : Type*} [Fintype α] [Fintype β]
/-- Every nonempty finite nonnegative-distortion problem has equal attained
primal minimum and dual supremum. A finite maximizing multiplier is not asserted. -/
theorem exists_all_feasible_dual_supremum (p : FiniteLaw α) (d : α → β → ℝ) (D : ℝ)
    (hd : ∀ x y, 0 ≤ d x y)
    (hfeasible : ∃ K, RateDistortionFeasible p d D K) :
    ∃ J : FiniteLaw (α × β), RateDistortionFeasible p d D J ∧
      (∀ K, RateDistortionFeasible p d D K →
        FEP.FiniteInformation.mutualInformation J ≤ FEP.FiniteInformation.mutualInformation K) ∧
      sInf {v : ℝ | ∃ K, RateDistortionFeasible p d D K ∧
        v = FEP.FiniteInformation.mutualInformation K} =
          FEP.FiniteInformation.mutualInformation J ∧
      sSup {v : ℝ | ∃ t : ℝ, 0 ≤ t ∧ v = rateDistortionDualValue p d D t} =
        FEP.FiniteInformation.mutualInformation J := by
  obtain ⟨J,hJ,hmin⟩ := rateDistortion_exists_minimizer p d D hfeasible
  let V : Set ℝ := {v | ∃ t : ℝ, 0 ≤ t ∧ v = rateDistortionDualValue p d D t}
  have hV : V.Nonempty := ⟨rateDistortionDualValue p d D 0,0,le_rfl,rfl⟩
  have hb : BddAbove V := by
    refine ⟨FEP.FiniteInformation.mutualInformation J,?_⟩
    rintro v ⟨t,ht,rfl⟩
    exact rateDistortionDual_le_feasible_information p d D t hd ht J hJ
  refine ⟨J,hJ,hmin,?_,?_⟩
  · apply le_antisymm
    · apply csInf_le
      · exact ⟨0,by rintro v ⟨K,_,rfl⟩; exact FEP.FiniteInformation.mutualInformation_nonneg K⟩
      · exact ⟨J,hJ,rfl⟩
    · apply le_csInf
      · exact ⟨FEP.FiniteInformation.mutualInformation J,J,hJ,rfl⟩
      · rintro v ⟨K,hK,rfl⟩
        exact hmin K hK
  · change sSup V = FEP.FiniteInformation.mutualInformation J
    apply le_antisymm
    · apply csSup_le hV
      rintro v ⟨t,ht,rfl⟩
      exact rateDistortionDual_le_feasible_information p d D t hd ht J hJ
    · by_contra h
      have hlt : sSup V < FEP.FiniteInformation.mutualInformation J := lt_of_not_ge h
      let ε := (FEP.FiniteInformation.mutualInformation J-sSup V)/2
      have hε : 0 < ε := by dsimp [ε]; linarith
      obtain ⟨lam,hlam,hlo⟩ := epsilon_dual_lower_bound p d D J hJ hmin ε hε
      have hhi : rateDistortionDualValue p d D lam ≤ sSup V :=
        le_csSup hb ⟨lam,hlam,rfl⟩
      dsimp [ε] at hlo
      linarith

/-- The actual fair-Boolean zero-budget boundary has dual supremum log2;
no Slater condition or finite dual optimizer is introduced. -/
theorem boolZeroBudget_dual_supremum :
    sSup {v : ℝ | ∃ t : ℝ, 0 ≤ t ∧
      v = rateDistortionDualValue (FiniteLaw.uniform : FiniteLaw Bool)
        boolHammingDistortion 0 t} = Real.log 2 := by
  obtain ⟨J,hJ,_,_,hSup⟩ := exists_all_feasible_dual_supremum
    (FiniteLaw.uniform : FiniteLaw Bool) boolHammingDistortion 0
    boolHammingDistortion_nonneg ⟨boolZeroDistortionJoint,boolZeroDistortionJoint_feasible⟩
  exact hSup.trans (FairBoolean.boolean_zero_exact J hJ).2
end RateDistortionGeometry
end FEP.VariationalDuality

namespace FEP.VariationalDuality
namespace RateDistortionGeometry
/-- General finite dual-supremum equality recovers the complete maintained
fair-Boolean natural-log rate curve, including both closed endpoints. -/
theorem boolClosedBudget_dual_supremum (D : ℝ) (h0 : 0 ≤ D) (hhalf : D ≤ (1:ℝ)/2) :
    sSup {v : ℝ | ∃ t : ℝ, 0 ≤ t ∧
      v = rateDistortionDualValue (FiniteLaw.uniform : FiniteLaw Bool)
        boolHammingDistortion D t} = Real.log 2 - Real.binEntropy D := by
  obtain ⟨K,hK,hvalue,hKmin⟩ := FairBoolean.boolean_closed_exact_minimum D h0 hhalf
  obtain ⟨J,hJ,hJmin,_,hSup⟩ := exists_all_feasible_dual_supremum
    (FiniteLaw.uniform : FiniteLaw Bool) boolHammingDistortion D
    boolHammingDistortion_nonneg ⟨K,hK⟩
  have heq : FEP.FiniteInformation.mutualInformation J =
      FEP.FiniteInformation.mutualInformation K :=
    le_antisymm (hJmin K hK) (hKmin J hJ)
  exact hSup.trans (heq.trans hvalue)
end RateDistortionGeometry
end FEP.VariationalDuality

namespace FEP.VariationalDuality
variable {α β : Type*} [Fintype α] [Fintype β]
theorem rateDistortion_exists_minimizer_and_dual_supremum (p : FiniteLaw α) (d : α → β → ℝ) (D : ℝ)
    (hd : ∀ x y, 0 ≤ d x y)
    (hfeasible : ∃ K, RateDistortionFeasible p d D K) :
    ∃ J : FiniteLaw (α × β), RateDistortionFeasible p d D J ∧
      (∀ K, RateDistortionFeasible p d D K →
        FEP.FiniteInformation.mutualInformation J ≤ FEP.FiniteInformation.mutualInformation K) ∧
      sInf {v : ℝ | ∃ K, RateDistortionFeasible p d D K ∧
        v = FEP.FiniteInformation.mutualInformation K} =
          FEP.FiniteInformation.mutualInformation J ∧
      sSup {v : ℝ | ∃ t : ℝ, 0 ≤ t ∧ v = rateDistortionDualValue p d D t} =
        FEP.FiniteInformation.mutualInformation J :=
  RateDistortionGeometry.exists_all_feasible_dual_supremum p d D hd hfeasible
end FEP.VariationalDuality
