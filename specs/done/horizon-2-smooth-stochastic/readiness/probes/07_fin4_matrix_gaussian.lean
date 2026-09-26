import Mathlib.Analysis.InnerProductSpace.PiL2
import Mathlib.Analysis.Normed.Algebra.MatrixExponential
import Mathlib.LinearAlgebra.Matrix.NonsingularInverse
import Mathlib.LinearAlgebra.Matrix.PosDef
import Mathlib.Probability.Distributions.Gaussian.Multivariate
import Mathlib.Probability.Kernel.Composition.CompProd
import Mathlib.Probability.Kernel.Composition.MapComap

open MeasureTheory Matrix NormedSpace ProbabilityTheory
open scoped MatrixOrder ProbabilityTheory RealInnerProductSpace

inductive Fin4Axis
  | external
  | sensory
  | active
  | internal
  deriving DecidableEq

open Fin4Axis

def Fin4Axis.toFin : Fin4Axis -> Fin 4
  | external => 0
  | sensory => 1
  | active => 2
  | internal => 3

def Fin4Axis.ofFin : Fin 4 -> Fin4Axis :=
  Fin.cases external (Fin.cases sensory (Fin.cases active (fun _ => internal)))

def fin4AxisEquivFin : Fin4Axis ≃ Fin 4 where
  toFun := Fin4Axis.toFin
  invFun := Fin4Axis.ofFin
  left_inv axis := by cases axis <;> rfl
  right_inv index := by fin_cases index <;> rfl

noncomputable instance : Fintype Fin4Axis :=
  Fintype.ofEquiv (Fin 4) fin4AxisEquivFin.symm

private lemma sum_fin4Axis {M : Type*} [AddCommMonoid M] (f : Fin4Axis -> M) :
    ∑ axis, f axis =
      f external + f sensory + f active + f internal := by
  classical
  change Finset.univ.sum f = _
  rw [show (Finset.univ : Finset Fin4Axis) =
      {external, sensory, active, internal} by
    ext axis
    cases axis <;> simp]
  simp [add_left_comm, add_comm]

abbrev Fin4State := EuclideanSpace ℝ Fin4Axis

def fin4Precision : Matrix Fin4Axis Fin4Axis ℝ
  | external, external => 4
  | external, sensory => -1
  | external, active => -1
  | external, internal => 0
  | sensory, external => -1
  | sensory, sensory => 4
  | sensory, active => 0
  | sensory, internal => -1
  | active, external => -1
  | active, sensory => 0
  | active, active => 4
  | active, internal => -1
  | internal, external => 0
  | internal, sensory => -1
  | internal, active => -1
  | internal, internal => 4

noncomputable def fin4Covariance : Matrix Fin4Axis Fin4Axis ℝ
  | external, external => 7 / 24
  | external, sensory => 1 / 12
  | external, active => 1 / 12
  | external, internal => 1 / 24
  | sensory, external => 1 / 12
  | sensory, sensory => 7 / 24
  | sensory, active => 1 / 24
  | sensory, internal => 1 / 12
  | active, external => 1 / 12
  | active, sensory => 1 / 24
  | active, active => 7 / 24
  | active, internal => 1 / 12
  | internal, external => 1 / 24
  | internal, sensory => 1 / 12
  | internal, active => 1 / 12
  | internal, internal => 7 / 24

lemma fin4Precision_mul_covariance : fin4Precision * fin4Covariance = 1 := by
  ext i j
  cases i <;> cases j <;>
    simp [Matrix.mul_apply, sum_fin4Axis, fin4Precision, fin4Covariance] <;>
      norm_num

lemma fin4Covariance_mul_precision : fin4Covariance * fin4Precision = 1 := by
  ext i j
  cases i <;> cases j <;>
    simp [Matrix.mul_apply, sum_fin4Axis, fin4Precision, fin4Covariance] <;>
      norm_num

lemma fin4Precision_isHermitian : fin4Precision.IsHermitian := by
  rw [Matrix.isHermitian_iff_isSymm]
  ext i j
  cases i <;> cases j <;> rfl

lemma fin4Precision_posDef : fin4Precision.PosDef := by
  apply Matrix.PosDef.of_dotProduct_mulVec_pos fin4Precision_isHermitian
  intro x hx
  have hcoordinate : ∃ i, x i ≠ 0 := by
    by_contra h
    apply hx
    funext i
    by_contra hi
    exact h ⟨i, hi⟩
  obtain ⟨i, hi⟩ := hcoordinate
  have hquadratic :
      star x ⬝ᵥ (fin4Precision *ᵥ x) =
        2 * x external ^ 2 + 2 * x sensory ^ 2 +
          2 * x active ^ 2 + 2 * x internal ^ 2 +
          (x external - x sensory) ^ 2 +
          (x external - x active) ^ 2 +
          (x sensory - x internal) ^ 2 +
          (x active - x internal) ^ 2 := by
    simp [dotProduct, Matrix.mulVec, sum_fin4Axis, fin4Precision]
    ring
  rw [hquadratic]
  cases i <;>
    nlinarith [sq_pos_of_ne_zero hi,
      sq_nonneg (x external - x sensory),
      sq_nonneg (x external - x active),
      sq_nonneg (x sensory - x internal),
      sq_nonneg (x active - x internal)]

lemma fin4Covariance_eq_inverse : fin4Covariance = fin4Precision⁻¹ := by
  rw [Matrix.inv_eq_right_inv fin4Precision_mul_covariance]

lemma fin4Covariance_posDef : fin4Covariance.PosDef := by
  rw [fin4Covariance_eq_inverse]
  exact fin4Precision_posDef.inv

lemma fin4Precision_external_internal :
    fin4Precision external internal = 0 := rfl

lemma fin4Covariance_external_internal :
    fin4Covariance external internal = 1 / 24 := rfl

def eigenmodeTwo : Fin4Axis -> ℝ := fun _ => 1

def eigenmodeFourExternal : Fin4Axis -> ℝ
  | external => 1
  | sensory => 0
  | active => 0
  | internal => -1

def eigenmodeFourSensory : Fin4Axis -> ℝ
  | external => 0
  | sensory => 1
  | active => -1
  | internal => 0

def eigenmodeSix : Fin4Axis -> ℝ
  | external => 1
  | sensory => -1
  | active => -1
  | internal => 1

lemma fin4Precision_eigenvalue_two :
    fin4Precision *ᵥ eigenmodeTwo = 2 • eigenmodeTwo := by
  funext i
  cases i <;>
    norm_num [Matrix.mulVec, dotProduct, sum_fin4Axis, fin4Precision,
      eigenmodeTwo]

lemma fin4Precision_eigenvalue_four_external :
    fin4Precision *ᵥ eigenmodeFourExternal = 4 • eigenmodeFourExternal := by
  funext i
  cases i <;>
    norm_num [Matrix.mulVec, dotProduct, sum_fin4Axis, fin4Precision,
      eigenmodeFourExternal]

lemma fin4Precision_eigenvalue_four_sensory :
    fin4Precision *ᵥ eigenmodeFourSensory = 4 • eigenmodeFourSensory := by
  funext i
  cases i <;>
    norm_num [Matrix.mulVec, dotProduct, sum_fin4Axis, fin4Precision,
      eigenmodeFourSensory]

lemma fin4Precision_eigenvalue_six :
    fin4Precision *ᵥ eigenmodeSix = 6 • eigenmodeSix := by
  funext i
  cases i <;>
    norm_num [Matrix.mulVec, dotProduct, sum_fin4Axis, fin4Precision,
      eigenmodeSix]

noncomputable def fin4GaussianKernel : Kernel Fin4State Fin4State :=
  Kernel.map
    (Kernel.compProd (Kernel.id : Kernel Fin4State Fin4State)
      (Kernel.const (Fin4State × Fin4State) (stdGaussian Fin4State)))
    (fun stateNoise => stateNoise.1 + stateNoise.2)

noncomputable instance fin4GaussianKernel_isMarkov :
    IsMarkovKernel fin4GaussianKernel :=
  Kernel.IsMarkovKernel.map _ (by fun_prop)

lemma fin4GaussianKernel_apply (state : Fin4State) :
    fin4GaussianKernel state = multivariateGaussian state 1 := by
  rw [fin4GaussianKernel, Kernel.map_apply _ (by fun_prop)]
  ext set hset
  rw [Measure.map_apply (by fun_prop) hset]
  rw [Kernel.compProd_apply (hset.preimage (by fun_prop))]
  rw [Kernel.id_apply, lintegral_dirac]
  rw [Kernel.const_apply]
  rw [multivariateGaussian]
  rw [Measure.map_apply (by fun_prop) hset]
  congr 1
  ext noise
  simp

-- H2-READINESS-ROW: finite_dimensional_matrix_carrier
example : Nonempty Fin4State ∧ fin4AxisEquivFin external = 0 ∧
    Matrix.toEuclideanLin fin4Precision (0 : Fin4State) = 0 := by
  exact ⟨⟨0⟩, rfl, by simp⟩

-- H2-READINESS-ROW: positive_definite_inverse
example : fin4Precision.PosDef ∧ fin4Covariance.PosDef ∧
    fin4Covariance = fin4Precision⁻¹ :=
  ⟨fin4Precision_posDef, fin4Covariance_posDef, fin4Covariance_eq_inverse⟩

-- H2-READINESS-ROW: matrix_exponential_semigroup
example (A : Matrix Fin4Axis Fin4Axis ℝ) (s t : ℝ) :
    exp ((s + t) • A) = exp (s • A) * exp (t • A) := by
  rw [add_smul]
  apply Matrix.exp_add_of_commute
  change (s • A) * (t • A) = (t • A) * (s • A)
  ext i j
  simp only [Matrix.mul_apply, Matrix.smul_apply]
  apply Finset.sum_congr rfl
  intro axis _
  ring

-- H2-READINESS-ROW: fin4_exact_precision_witness
example :
    fin4Precision * fin4Covariance = 1 ∧
      fin4Covariance * fin4Precision = 1 ∧
      fin4Precision external internal = 0 ∧
      fin4Covariance external internal = 1 / 24 ∧
      fin4Precision *ᵥ eigenmodeTwo = 2 • eigenmodeTwo ∧
      fin4Precision *ᵥ eigenmodeFourExternal = 4 • eigenmodeFourExternal ∧
      fin4Precision *ᵥ eigenmodeFourSensory = 4 • eigenmodeFourSensory ∧
      fin4Precision *ᵥ eigenmodeSix = 6 • eigenmodeSix :=
  ⟨fin4Precision_mul_covariance, fin4Covariance_mul_precision,
    fin4Precision_external_internal, fin4Covariance_external_internal,
    fin4Precision_eigenvalue_two, fin4Precision_eigenvalue_four_external,
    fin4Precision_eigenvalue_four_sensory, fin4Precision_eigenvalue_six⟩

-- H2-READINESS-UPSTREAM: fin4_scalar_specialization
example : fin4Precision *ᵥ eigenmodeTwo = 2 • eigenmodeTwo ∧
    ((2 : ℝ) • (1 : Matrix Fin4Axis Fin4Axis ℝ)) *ᵥ eigenmodeTwo =
      2 • eigenmodeTwo := by
  constructor
  · exact fin4Precision_eigenvalue_two
  · funext i
    cases i <;>
      norm_num [Matrix.mulVec, dotProduct, sum_fin4Axis, eigenmodeTwo,
        Matrix.one_apply]

-- H2-READINESS-BLOCKING: transition_covariance_psd
example (variance : ℝ) (hvariance : 0 ≤ variance) :
    ((variance : ℝ) • (1 : Matrix Fin4Axis Fin4Axis ℝ)).PosSemidef := by
  have hdiagonal :
      (Matrix.diagonal (fun _ : Fin4Axis => variance)).PosSemidef :=
    Matrix.PosSemidef.diagonal (d := fun _ : Fin4Axis => variance)
      (fun _ => hvariance)
  simpa [Matrix.smul_one_eq_diagonal] using hdiagonal

-- H2-READINESS-ROW: multivariate_gaussian_measure
example :
    (∫ state, state ∂multivariateGaussian (0 : Fin4State) fin4Covariance) = 0 ∧
      cov[fun state => state external, fun state => state internal;
        multivariateGaussian (0 : Fin4State) fin4Covariance] = 1 / 24 := by
  constructor
  · exact integral_id_multivariateGaussian
  · rw [covariance_eval_multivariateGaussian fin4Covariance_posDef.posSemidef]
    exact fin4Covariance_external_internal

-- H2-READINESS-ROW: multivariate_gaussian_state_kernel
example : IsMarkovKernel fin4GaussianKernel ∧
    ∀ state, fin4GaussianKernel state = multivariateGaussian state 1 := by
  exact ⟨inferInstance, fin4GaussianKernel_apply⟩
