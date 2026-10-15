module
public import FepSketches.markov_semigroup
public import FepSketches.scalar_gaussian_semigroup
public import Mathlib.Analysis.Matrix.PosDef
public import Mathlib.Analysis.Normed.Algebra.MatrixExponential
public import Mathlib.Analysis.SpecialFunctions.Exponential
public import Mathlib.MeasureTheory.Measure.LevyConvergence
public import Mathlib.MeasureTheory.Measure.ProbabilityMeasure
public import Mathlib.Order.Filter.AtTopBot.CountablyGenerated
public import Mathlib.Probability.Distributions.Gaussian.Multivariate
public import Mathlib.Probability.Kernel.Composition.Comp
public import Mathlib.Probability.Kernel.Composition.CompProd
public import Mathlib.Probability.Kernel.Composition.MapComap
public import Mathlib.Tactic.NoncommRing
public import Mathlib.Topology.Instances.NNReal.Lemmas

@[expose] public section

/-!
# Symmetric-precision linear Gaussian transition semigroup

This module generalizes only the finite-dimensional algebra and native kernel
construction needed by the exact four-coordinate export.  A raw symmetric
positive-definite precision and a center determine the inverse stationary
covariance, matrix-exponential evolution, finite-time covariance, and native
Gaussian transition.  The zero-time Dirac boundary, chronological semigroup,
invariant law, and weak limit are all derived.

The construction is a transition-law result.  It does not construct a
stochastic process, a general drift theory, or a forward equation.
-/

open Filter MeasureTheory Matrix NormedSpace ProbabilityTheory
open scoped BoundedContinuousFunction ComplexOrder ENNReal MatrixOrder MeasureTheory NNReal
  ProbabilityTheory RealInnerProductSpace Topology

namespace FEP.LinearGaussianSemigroup

noncomputable section

/-- The finite-dimensional state owned by a named finite axis. -/
abbrev State (Axis : Type*) := EuclideanSpace ℝ Axis

/-- Raw data for a symmetric-precision linear Gaussian transition. Covariance
and all kernel laws are deliberately absent: they are derived below. -/
structure LinearGaussianParameters (Axis : Type*) where
  precision : Matrix Axis Axis ℝ
  precision_posDef : precision.PosDef
  center : State Axis

namespace LinearGaussianParameters

variable {Axis : Type*} [Fintype Axis] [DecidableEq Axis]

/-- Stationary covariance derived from the raw precision. -/
noncomputable def covariance (model : LinearGaussianParameters Axis) :
    Matrix Axis Axis ℝ :=
  model.precision⁻¹

/-- Matrix-exponential contraction at nonnegative time. -/
noncomputable def evolution
    (model : LinearGaussianParameters Axis) (time : ℝ≥0) :
    Matrix Axis Axis ℝ :=
  NormedSpace.exp ((-(time : ℝ)) • model.precision)

/-- Conditional mean from a starting state. -/
noncomputable def transitionMean
    (model : LinearGaussianParameters Axis) (time : ℝ≥0)
    (state : State Axis) : State Axis :=
  model.center +
    Matrix.toEuclideanCLM (𝕜 := ℝ) (model.evolution time)
      (state - model.center)

/-- Finite-time covariance of the symmetric-precision linear Gaussian transition. -/
noncomputable def transitionCovariance
    (model : LinearGaussianParameters Axis) (time : ℝ≥0) :
    Matrix Axis Axis ℝ :=
  model.covariance -
    model.evolution time * model.covariance * (model.evolution time)ᵀ

/-- Precision times its derived covariance is the identity. -/
theorem precision_mul_covariance (model : LinearGaussianParameters Axis) :
    model.precision * model.covariance = 1 := by
  exact Matrix.mul_nonsing_inv model.precision
    (model.precision.isUnit_iff_isUnit_det.mp
      model.precision_posDef.isUnit)

/-- The derived covariance times precision is the identity. -/
theorem covariance_mul_precision (model : LinearGaussianParameters Axis) :
    model.covariance * model.precision = 1 := by
  exact Matrix.nonsing_inv_mul model.precision
    (model.precision.isUnit_iff_isUnit_det.mp
      model.precision_posDef.isUnit)

/-- Inverting the raw positive-definite precision produces a positive-definite
stationary covariance. -/
theorem covariance_posDef (model : LinearGaussianParameters Axis) :
    model.covariance.PosDef := by
  exact model.precision_posDef.inv

private lemma unitary_inverse_eq_transpose (U : unitary (Matrix Axis Axis ℝ)) :
    ((U : Matrix Axis Axis ℝ)⁻¹) = (U : Matrix Axis Axis ℝ)ᵀ := by
  apply Matrix.inv_eq_left_inv
  simpa only [Matrix.star_eq_conjTranspose,
    Matrix.conjTranspose_eq_transpose_of_trivial] using
      Unitary.coe_star_mul_self U

private lemma precision_spectral_form (model : LinearGaussianParameters Axis) :
    model.precision =
      (model.precision_posDef.isHermitian.eigenvectorUnitary :
          Matrix Axis Axis ℝ) *
        Matrix.diagonal model.precision_posDef.isHermitian.eigenvalues *
          (model.precision_posDef.isHermitian.eigenvectorUnitary :
            Matrix Axis Axis ℝ)ᵀ := by
  simpa only [Unitary.conjStarAlgAut_apply, RCLike.ofReal_real_eq_id,
    Function.id_comp, Matrix.star_eq_conjTranspose,
    Matrix.conjTranspose_eq_transpose_of_trivial] using
      model.precision_posDef.isHermitian.spectral_theorem

private lemma covariance_spectral_form (model : LinearGaussianParameters Axis) :
    model.covariance =
      (model.precision_posDef.isHermitian.eigenvectorUnitary :
          Matrix Axis Axis ℝ) *
        Matrix.diagonal
          (fun i =>
            (model.precision_posDef.isHermitian.eigenvalues i)⁻¹) *
          (model.precision_posDef.isHermitian.eigenvectorUnitary :
            Matrix Axis Axis ℝ)ᵀ := by
  rw [covariance]
  apply Matrix.inv_eq_right_inv
  calc
    model.precision *
          ((model.precision_posDef.isHermitian.eigenvectorUnitary :
              Matrix Axis Axis ℝ) *
            Matrix.diagonal
              (fun i =>
                (model.precision_posDef.isHermitian.eigenvalues i)⁻¹) *
              (model.precision_posDef.isHermitian.eigenvectorUnitary :
                Matrix Axis Axis ℝ)ᵀ) =
        ((model.precision_posDef.isHermitian.eigenvectorUnitary :
              Matrix Axis Axis ℝ) *
            Matrix.diagonal
              model.precision_posDef.isHermitian.eigenvalues *
              (model.precision_posDef.isHermitian.eigenvectorUnitary :
                Matrix Axis Axis ℝ)ᵀ) *
          ((model.precision_posDef.isHermitian.eigenvectorUnitary :
              Matrix Axis Axis ℝ) *
            Matrix.diagonal
              (fun i =>
                (model.precision_posDef.isHermitian.eigenvalues i)⁻¹) *
              (model.precision_posDef.isHermitian.eigenvectorUnitary :
                Matrix Axis Axis ℝ)ᵀ) := by
      rw [← precision_spectral_form model]
    _ = 1 := by
      have hUnit :
          (model.precision_posDef.isHermitian.eigenvectorUnitary :
              Matrix Axis Axis ℝ)ᵀ *
            (model.precision_posDef.isHermitian.eigenvectorUnitary :
              Matrix Axis Axis ℝ) = 1 := by
        simpa only [Matrix.star_eq_conjTranspose,
          Matrix.conjTranspose_eq_transpose_of_trivial] using
            Unitary.coe_star_mul_self
              model.precision_posDef.isHermitian.eigenvectorUnitary
      have hUnitRight :
          (model.precision_posDef.isHermitian.eigenvectorUnitary :
              Matrix Axis Axis ℝ) *
            (model.precision_posDef.isHermitian.eigenvectorUnitary :
              Matrix Axis Axis ℝ)ᵀ = 1 := by
        simpa only [Matrix.star_eq_conjTranspose,
          Matrix.conjTranspose_eq_transpose_of_trivial,
          Unitary.coe_star] using
            Unitary.coe_mul_star_self
              model.precision_posDef.isHermitian.eigenvectorUnitary
      have hDiagonalInverse :
          Matrix.diagonal model.precision_posDef.isHermitian.eigenvalues *
              Matrix.diagonal
                (fun i =>
                  (model.precision_posDef.isHermitian.eigenvalues i)⁻¹) =
            1 := by
        rw [Matrix.diagonal_mul_diagonal]
        ext i j
        by_cases hij : i = j
        · subst j
          simp [model.precision_posDef.eigenvalues_pos i |>.ne']
        · simp [hij]
      calc
        _ =
            (model.precision_posDef.isHermitian.eigenvectorUnitary :
                Matrix Axis Axis ℝ) *
              Matrix.diagonal
                model.precision_posDef.isHermitian.eigenvalues *
                ((model.precision_posDef.isHermitian.eigenvectorUnitary :
                    Matrix Axis Axis ℝ)ᵀ *
                  (model.precision_posDef.isHermitian.eigenvectorUnitary :
                    Matrix Axis Axis ℝ)) *
                  Matrix.diagonal
                    (fun i =>
                      (model.precision_posDef.isHermitian.eigenvalues i)⁻¹) *
                    (model.precision_posDef.isHermitian.eigenvectorUnitary :
                      Matrix Axis Axis ℝ)ᵀ := by
            noncomm_ring
        _ = 1 := by
          rw [hUnit]
          calc
            _ =
                (model.precision_posDef.isHermitian.eigenvectorUnitary :
                    Matrix Axis Axis ℝ) *
                  (Matrix.diagonal
                      model.precision_posDef.isHermitian.eigenvalues *
                    Matrix.diagonal
                      (fun i =>
                        (model.precision_posDef.isHermitian.eigenvalues i)⁻¹)) *
                    (model.precision_posDef.isHermitian.eigenvectorUnitary :
                      Matrix Axis Axis ℝ)ᵀ := by
              noncomm_ring
            _ = 1 := by
              rw [hDiagonalInverse]
              simpa using hUnitRight

private lemma evolution_spectral_form
    (model : LinearGaussianParameters Axis) (time : ℝ≥0) :
    model.evolution time =
      (model.precision_posDef.isHermitian.eigenvectorUnitary :
          Matrix Axis Axis ℝ) *
        Matrix.diagonal
          (fun i =>
            Real.exp
              (-((time : ℝ) *
                model.precision_posDef.isHermitian.eigenvalues i))) *
          (model.precision_posDef.isHermitian.eigenvectorUnitary :
            Matrix Axis Axis ℝ)ᵀ := by
  rw [evolution]
  calc
    NormedSpace.exp ((-(time : ℝ)) • model.precision) =
        NormedSpace.exp
          ((-(time : ℝ)) •
            ((model.precision_posDef.isHermitian.eigenvectorUnitary :
                Matrix Axis Axis ℝ) *
              Matrix.diagonal
                model.precision_posDef.isHermitian.eigenvalues *
                (model.precision_posDef.isHermitian.eigenvectorUnitary :
                  Matrix Axis Axis ℝ)ᵀ)) := by
      exact congrArg
        (fun matrix : Matrix Axis Axis ℝ =>
          NormedSpace.exp ((-(time : ℝ)) • matrix))
        (precision_spectral_form model)
    _ = NormedSpace.exp
        ((model.precision_posDef.isHermitian.eigenvectorUnitary :
            Matrix Axis Axis ℝ) *
          ((-(time : ℝ)) •
            Matrix.diagonal
              model.precision_posDef.isHermitian.eigenvalues) *
            (model.precision_posDef.isHermitian.eigenvectorUnitary :
              Matrix Axis Axis ℝ)ᵀ) := by
      congr 1
      simp
    _ =
        (model.precision_posDef.isHermitian.eigenvectorUnitary :
            Matrix Axis Axis ℝ) *
          Matrix.diagonal
            (fun i =>
              Real.exp
                (-((time : ℝ) *
                  model.precision_posDef.isHermitian.eigenvalues i))) *
            (model.precision_posDef.isHermitian.eigenvectorUnitary :
              Matrix Axis Axis ℝ)ᵀ := by
      rw [← unitary_inverse_eq_transpose
        model.precision_posDef.isHermitian.eigenvectorUnitary]
      rw [Matrix.exp_conj
        (model.precision_posDef.isHermitian.eigenvectorUnitary :
          Matrix Axis Axis ℝ)
        ((-(time : ℝ)) •
          Matrix.diagonal
            model.precision_posDef.isHermitian.eigenvalues)
        Unitary.isUnit_coe]
      rw [← Matrix.diagonal_smul, Matrix.exp_diagonal]
      rw [Pi.exp_def]
      congr 1
      funext i
      rw [← Real.exp_eq_exp_ℝ]
      simp

private lemma conjugate_mul (U : Matrix Axis Axis ℝ)
    (hUnit : Uᵀ * U = 1) (A B : Matrix Axis Axis ℝ) :
    (U * A * Uᵀ) * (U * B * Uᵀ) = U * (A * B) * Uᵀ := by
  calc
    _ = U * A * (Uᵀ * U) * B * Uᵀ := by noncomm_ring
    _ = U * (A * B) * Uᵀ := by rw [hUnit]; noncomm_ring

private lemma transitionCovariance_spectral_form
    (model : LinearGaussianParameters Axis) (time : ℝ≥0) :
    model.transitionCovariance time =
      (model.precision_posDef.isHermitian.eigenvectorUnitary :
          Matrix Axis Axis ℝ) *
        Matrix.diagonal (fun i =>
          (model.precision_posDef.isHermitian.eigenvalues i)⁻¹ -
            Real.exp
                (-((time : ℝ) *
                  model.precision_posDef.isHermitian.eigenvalues i)) *
              (model.precision_posDef.isHermitian.eigenvalues i)⁻¹ *
                Real.exp
                  (-((time : ℝ) *
                    model.precision_posDef.isHermitian.eigenvalues i))) *
          (model.precision_posDef.isHermitian.eigenvectorUnitary :
            Matrix Axis Axis ℝ)ᵀ := by
  rw [transitionCovariance, covariance_spectral_form model,
    evolution_spectral_form model]
  have hUnit :
      (model.precision_posDef.isHermitian.eigenvectorUnitary :
          Matrix Axis Axis ℝ)ᵀ *
        (model.precision_posDef.isHermitian.eigenvectorUnitary :
          Matrix Axis Axis ℝ) = 1 := by
    simpa only [Matrix.star_eq_conjTranspose,
      Matrix.conjTranspose_eq_transpose_of_trivial] using
        Unitary.coe_star_mul_self
          model.precision_posDef.isHermitian.eigenvectorUnitary
  have hEvolutionTranspose :
      ((model.precision_posDef.isHermitian.eigenvectorUnitary :
            Matrix Axis Axis ℝ) *
          Matrix.diagonal
            (fun i =>
              Real.exp
                (-((time : ℝ) *
                  model.precision_posDef.isHermitian.eigenvalues i))) *
          (model.precision_posDef.isHermitian.eigenvectorUnitary :
            Matrix Axis Axis ℝ)ᵀ)ᵀ =
        (model.precision_posDef.isHermitian.eigenvectorUnitary :
            Matrix Axis Axis ℝ) *
          Matrix.diagonal
            (fun i =>
              Real.exp
                (-((time : ℝ) *
                  model.precision_posDef.isHermitian.eigenvalues i))) *
          (model.precision_posDef.isHermitian.eigenvectorUnitary :
            Matrix Axis Axis ℝ)ᵀ := by
    rw [Matrix.transpose_mul, Matrix.transpose_mul]
    simp [Matrix.mul_assoc]
  rw [hEvolutionTranspose]
  rw [conjugate_mul _ hUnit]
  rw [conjugate_mul _ hUnit]
  have hDiagonalProduct :
      Matrix.diagonal
          (fun i =>
            (model.precision_posDef.isHermitian.eigenvalues i)⁻¹) -
        Matrix.diagonal
            (fun i =>
              Real.exp
                (-((time : ℝ) *
                  model.precision_posDef.isHermitian.eigenvalues i))) *
          Matrix.diagonal
              (fun i =>
                (model.precision_posDef.isHermitian.eigenvalues i)⁻¹) *
            Matrix.diagonal
              (fun i =>
                Real.exp
                  (-((time : ℝ) *
                    model.precision_posDef.isHermitian.eigenvalues i))) =
        Matrix.diagonal (fun i =>
          (model.precision_posDef.isHermitian.eigenvalues i)⁻¹ -
            Real.exp
                (-((time : ℝ) *
                  model.precision_posDef.isHermitian.eigenvalues i)) *
              (model.precision_posDef.isHermitian.eigenvalues i)⁻¹ *
                Real.exp
                  (-((time : ℝ) *
                    model.precision_posDef.isHermitian.eigenvalues i))) := by
    ext i j
    by_cases hij : i = j
    · subst j
      simp
    · simp [hij]
  calc
    _ =
        (model.precision_posDef.isHermitian.eigenvectorUnitary :
            Matrix Axis Axis ℝ) *
          (Matrix.diagonal
              (fun i =>
                (model.precision_posDef.isHermitian.eigenvalues i)⁻¹) -
            Matrix.diagonal
                (fun i =>
                  Real.exp
                    (-((time : ℝ) *
                      model.precision_posDef.isHermitian.eigenvalues i))) *
              Matrix.diagonal
                (fun i =>
                  (model.precision_posDef.isHermitian.eigenvalues i)⁻¹) *
                Matrix.diagonal
                  (fun i =>
                    Real.exp
                      (-((time : ℝ) *
                        model.precision_posDef.isHermitian.eigenvalues i)))) *
            (model.precision_posDef.isHermitian.eigenvectorUnitary :
              Matrix Axis Axis ℝ)ᵀ := by
      noncomm_ring
    _ = _ := by rw [hDiagonalProduct]

/-- Evolution is the identity at time zero. -/
theorem evolution_zero (model : LinearGaussianParameters Axis) :
    model.evolution 0 = 1 := by
  simp [evolution]

/-- Matrix exponentials compose in the same later-on-left chronology as the
native kernel interface. -/
theorem evolution_add (model : LinearGaussianParameters Axis)
    (left right : ℝ≥0) :
    model.evolution (left + right) =
      model.evolution right * model.evolution left := by
  rw [evolution, evolution, evolution]
  rw [NNReal.coe_add, neg_add, add_smul]
  have hCommute :
      Commute ((-(left : ℝ)) • model.precision)
        ((-(right : ℝ)) • model.precision) :=
    (((Commute.refl model.precision).smul_left (-((left : ℝ)))).smul_right
      (-((right : ℝ))))
  rw [Matrix.exp_add_of_commute _ _ hCommute, hCommute.exp.eq]

/-- Symmetric precision gives a symmetric evolution at every time. -/
theorem evolution_transpose (model : LinearGaussianParameters Axis)
    (time : ℝ≥0) :
    (model.evolution time)ᵀ = model.evolution time := by
  rw [evolution]
  apply Matrix.IsSymm.exp
  have hPrecisionSymm : model.precision.IsSymm :=
    Matrix.isHermitian_iff_isSymm.mp model.precision_posDef.isHermitian
  exact hPrecisionSymm.smul (-((time : ℝ)))

/-- The transition mean starts at the input state. -/
theorem transitionMean_zero (model : LinearGaussianParameters Axis)
    (state : State Axis) :
    model.transitionMean 0 state = state := by
  simp [transitionMean, model.evolution_zero]

private theorem transitionMean_affine
    (model : LinearGaussianParameters Axis) (time : ℝ≥0)
    (state : State Axis) :
    model.transitionMean time state =
      (model.center -
          Matrix.toEuclideanCLM (𝕜 := ℝ) (model.evolution time)
            model.center) +
        Matrix.toEuclideanCLM (𝕜 := ℝ) (model.evolution time) state := by
  rw [transitionMean]
  simp only [map_sub]
  abel

/-- Conditional means compose in chronological order. -/
theorem transitionMean_add (model : LinearGaussianParameters Axis)
    (left right : ℝ≥0) (state : State Axis) :
    model.transitionMean (left + right) state =
      model.transitionMean right (model.transitionMean left state) := by
  rw [transitionMean, transitionMean, transitionMean, model.evolution_add]
  simp only [map_sub, map_add, map_mul, mul_apply_eq_comp]
  abel

/-- The transition covariance vanishes at time zero. -/
theorem transitionCovariance_zero (model : LinearGaussianParameters Axis) :
    model.transitionCovariance 0 = 0 := by
  simp [transitionCovariance, model.evolution_zero]

/-- Every nonnegative time has a positive-semidefinite transition covariance. -/
theorem transitionCovariance_posSemidef
    (model : LinearGaussianParameters Axis) (time : ℝ≥0) :
    (model.transitionCovariance time).PosSemidef := by
  rw [transitionCovariance_spectral_form model time]
  suffices hDiagonal :
      (Matrix.diagonal (fun i =>
        (model.precision_posDef.isHermitian.eigenvalues i)⁻¹ -
          Real.exp
              (-((time : ℝ) *
                model.precision_posDef.isHermitian.eigenvalues i)) *
            (model.precision_posDef.isHermitian.eigenvalues i)⁻¹ *
              Real.exp
                (-((time : ℝ) *
                  model.precision_posDef.isHermitian.eigenvalues i)))).PosSemidef by
    simpa only [Matrix.star_eq_conjTranspose,
      Matrix.conjTranspose_eq_transpose_of_trivial] using
        (Unitary.isUnit_coe.posSemidef_star_right_conjugate_iff.mpr
          hDiagonal)
  rw [Matrix.posSemidef_diagonal_iff]
  intro i
  have hEigenvalue := model.precision_posDef.eigenvalues_pos i
  have hExponent :
      -((time : ℝ) *
        model.precision_posDef.isHermitian.eigenvalues i) ≤ 0 := by
    exact neg_nonpos.mpr (mul_nonneg time.coe_nonneg hEigenvalue.le)
  have hExpLe :
      Real.exp
          (-((time : ℝ) *
            model.precision_posDef.isHermitian.eigenvalues i)) ≤ 1 :=
    Real.exp_le_one_iff.mpr hExponent
  have hExpPos :
      0 < Real.exp
        (-((time : ℝ) *
          model.precision_posDef.isHermitian.eigenvalues i)) :=
    Real.exp_pos _
  have hInvPos :
      0 < (model.precision_posDef.isHermitian.eigenvalues i)⁻¹ :=
    inv_pos.mpr hEigenvalue
  calc
    _ = (model.precision_posDef.isHermitian.eigenvalues i)⁻¹ *
        ((1 - Real.exp
            (-((time : ℝ) *
              model.precision_posDef.isHermitian.eigenvalues i))) *
          (1 + Real.exp
            (-((time : ℝ) *
              model.precision_posDef.isHermitian.eigenvalues i)))) := by
      ring
    _ ≥ 0 := mul_nonneg hInvPos.le <|
      mul_nonneg (sub_nonneg.mpr hExpLe) (by positivity)

/-- Strictly positive time has a positive-definite transition covariance. -/
theorem transitionCovariance_posDef
    (model : LinearGaussianParameters Axis) (time : ℝ≥0)
    (hTime : 0 < time) :
    (model.transitionCovariance time).PosDef := by
  rw [transitionCovariance_spectral_form model time]
  suffices hDiagonal :
      (Matrix.diagonal (fun i =>
        (model.precision_posDef.isHermitian.eigenvalues i)⁻¹ -
          Real.exp
              (-((time : ℝ) *
                model.precision_posDef.isHermitian.eigenvalues i)) *
            (model.precision_posDef.isHermitian.eigenvalues i)⁻¹ *
              Real.exp
                (-((time : ℝ) *
                  model.precision_posDef.isHermitian.eigenvalues i)))).PosDef by
    simpa only [Matrix.star_eq_conjTranspose,
      Matrix.conjTranspose_eq_transpose_of_trivial] using
        (Unitary.isUnit_coe.posDef_star_right_conjugate_iff.mpr hDiagonal)
  rw [Matrix.posDef_diagonal_iff]
  intro i
  have hEigenvalue := model.precision_posDef.eigenvalues_pos i
  have hProduct :
      0 < (time : ℝ) *
        model.precision_posDef.isHermitian.eigenvalues i :=
    mul_pos (NNReal.coe_pos.mpr hTime) hEigenvalue
  have hExpLt :
      Real.exp
          (-((time : ℝ) *
            model.precision_posDef.isHermitian.eigenvalues i)) < 1 :=
    Real.exp_lt_one_iff.mpr (neg_neg_of_pos hProduct)
  have hExpPos :
      0 < Real.exp
        (-((time : ℝ) *
          model.precision_posDef.isHermitian.eigenvalues i)) :=
    Real.exp_pos _
  have hInvPos :
      0 < (model.precision_posDef.isHermitian.eigenvalues i)⁻¹ :=
    inv_pos.mpr hEigenvalue
  calc
    _ = (model.precision_posDef.isHermitian.eigenvalues i)⁻¹ *
        ((1 - Real.exp
            (-((time : ℝ) *
              model.precision_posDef.isHermitian.eigenvalues i))) *
          (1 + Real.exp
            (-((time : ℝ) *
              model.precision_posDef.isHermitian.eigenvalues i)))) := by
      ring
    _ > 0 := mul_pos hInvPos <|
      mul_pos (sub_pos.mpr hExpLt) (by positivity)

/-- Transition covariances compose with the later/right evolution transporting
the earlier/left covariance. -/
theorem transitionCovariance_add
    (model : LinearGaussianParameters Axis) (left right : ℝ≥0) :
    model.transitionCovariance (left + right) =
      model.evolution right * model.transitionCovariance left *
          (model.evolution right)ᵀ +
        model.transitionCovariance right := by
  rw [transitionCovariance, transitionCovariance, transitionCovariance,
    model.evolution_add]
  rw [Matrix.transpose_mul, model.evolution_transpose left,
    model.evolution_transpose right]
  noncomm_ring

private theorem transition_output_measurable
    (model : LinearGaussianParameters Axis) (time : ℝ≥0) :
    Measurable (fun stateNoise : State Axis × State Axis =>
      model.transitionMean time stateNoise.1 + stateNoise.2) := by
  unfold transitionMean
  fun_prop

/-- Native measurable transition built from the identity state kernel and an
independent centered multivariate Gaussian noise law. -/
noncomputable def transition
    (model : LinearGaussianParameters Axis) (time : ℝ≥0) :
    Kernel (State Axis) (State Axis) :=
  Kernel.map
    (Kernel.compProd (Kernel.id : Kernel (State Axis) (State Axis))
      (Kernel.const (State Axis × State Axis)
        (multivariateGaussian 0 (model.transitionCovariance time))))
    (fun stateNoise =>
      model.transitionMean time stateNoise.1 + stateNoise.2)

noncomputable instance transition_isMarkovKernel
    (model : LinearGaussianParameters Axis) (time : ℝ≥0) :
    IsMarkovKernel (model.transition time) :=
  Kernel.IsMarkovKernel.map _ (model.transition_output_measurable time)

private theorem multivariateGaussian_zero_map_const_add
    (mean : State Axis) (covariance : Matrix Axis Axis ℝ) :
    (multivariateGaussian 0 covariance).map (fun noise => mean + noise) =
      multivariateGaussian mean covariance := by
  rw [multivariateGaussian, multivariateGaussian,
    Measure.map_map (by fun_prop) (by fun_prop)]
  congr 1
  funext noise
  simp

/-- Each transition row is the multivariate Gaussian with the derived mean
and covariance. -/
theorem transition_apply (model : LinearGaussianParameters Axis)
    (time : ℝ≥0) (state : State Axis) :
    model.transition time state =
      multivariateGaussian (model.transitionMean time state)
        (model.transitionCovariance time) := by
  rw [transition,
    Kernel.map_apply _ (model.transition_output_measurable time)]
  ext set hSet
  rw [Measure.map_apply (model.transition_output_measurable time) hSet]
  rw [Kernel.compProd_apply
    (hSet.preimage (model.transition_output_measurable time))]
  rw [Kernel.id_apply, lintegral_dirac]
  rw [Kernel.const_apply]
  change
    multivariateGaussian 0 (model.transitionCovariance time)
        ((fun noise => model.transitionMean time state + noise) ⁻¹' set) =
      multivariateGaussian (model.transitionMean time state)
        (model.transitionCovariance time) set
  rw [← Measure.map_apply (by fun_prop) hSet,
    multivariateGaussian_zero_map_const_add]

/-- Every row of every time slice is normalized. -/
theorem transition_univ (model : LinearGaussianParameters Axis)
    (time : ℝ≥0) (state : State Axis) :
    model.transition time state Set.univ = 1 := by
  rw [model.transition_apply]
  simp

/-- The zero-time slice is the native identity kernel. -/
theorem transition_zero (model : LinearGaussianParameters Axis) :
    model.transition 0 = Kernel.id := by
  apply DFunLike.ext _ _
  intro state
  rw [model.transition_apply, model.transitionMean_zero,
    model.transitionCovariance_zero]
  simp [multivariateGaussian, Kernel.id_apply]

private theorem charFun_map_matrix
    (law : Measure (State Axis)) [IsFiniteMeasure law]
    (matrix : Matrix Axis Axis ℝ) (frequency : State Axis) :
    charFun
        (law.map (Matrix.toEuclideanCLM (𝕜 := ℝ) matrix)) frequency =
      charFun law
        (Matrix.toEuclideanCLM (𝕜 := ℝ) matrixᵀ frequency) := by
  rw [charFun_apply, charFun_apply,
    integral_map (by fun_prop) (by fun_prop)]
  congr with state
  have hAdjoint :
      (Matrix.toEuclideanCLM (𝕜 := ℝ) matrix).adjoint =
        Matrix.toEuclideanCLM (𝕜 := ℝ) matrixᵀ := by
    simpa only [ContinuousLinearMap.star_eq_adjoint,
      Matrix.star_eq_conjTranspose,
      Matrix.conjTranspose_eq_transpose_of_trivial] using
        (map_star (Matrix.toEuclideanCLM (n := Axis) (𝕜 := ℝ)) matrix).symm
  rw [← (Matrix.toEuclideanCLM (𝕜 := ℝ) matrix).adjoint_inner_right,
    hAdjoint]

private theorem charFun_map_affine
    (law : Measure (State Axis)) [IsFiniteMeasure law]
    (matrix : Matrix Axis Axis ℝ) (shift frequency : State Axis) :
    charFun
        (law.map (fun state =>
          shift + Matrix.toEuclideanCLM (𝕜 := ℝ) matrix state)) frequency =
      charFun law
          (Matrix.toEuclideanCLM (𝕜 := ℝ) matrixᵀ frequency) *
        Complex.exp (⟪shift, frequency⟫ * Complex.I) := by
  rw [show law.map (fun state =>
      shift + Matrix.toEuclideanCLM (𝕜 := ℝ) matrix state) =
      (law.map (Matrix.toEuclideanCLM (𝕜 := ℝ) matrix)).map
        (fun state => shift + state) by
    rw [Measure.map_map (by fun_prop) (by fun_prop)]
    rfl]
  rw [charFun_map_const_add, charFun_map_matrix]

private theorem inner_transpose_mulVec
    (matrix : Matrix Axis Axis ℝ) (left right : State Axis) :
    ⟪Matrix.toEuclideanCLM (𝕜 := ℝ) matrixᵀ left, right⟫ =
      ⟪left, Matrix.toEuclideanCLM (𝕜 := ℝ) matrix right⟫ := by
  calc
    _ = ⟪right,
        Matrix.toEuclideanCLM (𝕜 := ℝ) matrixᵀ left⟫ :=
      real_inner_comm _ _
    _ = right ⬝ᵥ matrixᵀ *ᵥ left :=
      Matrix.inner_toEuclideanCLM matrixᵀ right left
    _ = left ⬝ᵥ matrix *ᵥ right :=
      Matrix.dotProduct_transpose_mulVec matrix right left
    _ = _ := (Matrix.inner_toEuclideanCLM matrix left right).symm

private theorem quadratic_conjugate
    (matrix covariance : Matrix Axis Axis ℝ) (frequency : State Axis) :
    Matrix.toEuclideanCLM (𝕜 := ℝ) matrixᵀ frequency ⬝ᵥ
        covariance *ᵥ
          Matrix.toEuclideanCLM (𝕜 := ℝ) matrixᵀ frequency =
      frequency ⬝ᵥ
        (matrix * covariance * matrixᵀ) *ᵥ frequency := by
  change
    (matrixᵀ *ᵥ frequency) ⬝ᵥ
        covariance *ᵥ (matrixᵀ *ᵥ frequency) =
      frequency ⬝ᵥ (matrix * covariance * matrixᵀ) *ᵥ frequency
  calc
    _ = (covariance *ᵥ (matrixᵀ *ᵥ frequency)) ⬝ᵥ
        matrixᵀ *ᵥ frequency := dotProduct_comm _ _
    _ = frequency ⬝ᵥ
        matrix *ᵥ (covariance *ᵥ (matrixᵀ *ᵥ frequency)) :=
      Matrix.dotProduct_transpose_mulVec matrix _ _
    _ = _ := by simp only [Matrix.mulVec_mulVec, Matrix.mul_assoc]

private theorem multivariateGaussian_affine_conv
    (sourceMean shift : State Axis)
    (sourceCovariance noiseCovariance : Matrix Axis Axis ℝ)
    (hSourceCovariance : sourceCovariance.PosSemidef)
    (hNoiseCovariance : noiseCovariance.PosSemidef)
    (coefficient : Matrix Axis Axis ℝ) :
    (multivariateGaussian sourceMean sourceCovariance).map
          (fun state =>
            shift +
              Matrix.toEuclideanCLM (𝕜 := ℝ) coefficient state) ∗
        multivariateGaussian 0 noiseCovariance =
      multivariateGaussian
        (shift +
          Matrix.toEuclideanCLM (𝕜 := ℝ) coefficient sourceMean)
        (coefficient * sourceCovariance * coefficientᵀ + noiseCovariance) := by
  have hTransported :
      (coefficient * sourceCovariance * coefficientᵀ).PosSemidef := by
    simpa only [Matrix.conjTranspose_eq_transpose_of_trivial] using
      hSourceCovariance.mul_mul_conjTranspose_same coefficient
  have hCombined :
      (coefficient * sourceCovariance * coefficientᵀ +
        noiseCovariance).PosSemidef :=
    hTransported.add hNoiseCovariance
  apply Measure.ext_of_charFun
  funext frequency
  rw [charFun_conv, charFun_map_affine,
    charFun_multivariateGaussian hSourceCovariance,
    charFun_multivariateGaussian hNoiseCovariance,
    charFun_multivariateGaussian hCombined]
  simp only [← Complex.exp_add]
  congr 1
  rw [inner_transpose_mulVec coefficient frequency sourceMean,
    quadratic_conjugate coefficient sourceCovariance frequency,
    inner_add_right, Matrix.add_mulVec, dotProduct_add,
    real_inner_comm shift frequency]
  simp only [inner_zero_right, Complex.ofReal_zero, Complex.ofReal_add,
    zero_mul]
  ring

private theorem multivariateGaussian_bind_affine
    (sourceMean shift : State Axis)
    (sourceCovariance noiseCovariance : Matrix Axis Axis ℝ)
    (hSourceCovariance : sourceCovariance.PosSemidef)
    (hNoiseCovariance : noiseCovariance.PosSemidef)
    (coefficient : Matrix Axis Axis ℝ)
    (hMeasurable : Measurable (fun state =>
      multivariateGaussian
        (shift + Matrix.toEuclideanCLM (𝕜 := ℝ) coefficient state)
        noiseCovariance)) :
    (multivariateGaussian sourceMean sourceCovariance).bind
        (fun state =>
          multivariateGaussian
            (shift +
              Matrix.toEuclideanCLM (𝕜 := ℝ) coefficient state)
            noiseCovariance) =
      multivariateGaussian
        (shift +
          Matrix.toEuclideanCLM (𝕜 := ℝ) coefficient sourceMean)
        (coefficient * sourceCovariance * coefficientᵀ +
          noiseCovariance) := by
  calc
    (multivariateGaussian sourceMean sourceCovariance).bind
        (fun state =>
          multivariateGaussian
            (shift +
              Matrix.toEuclideanCLM (𝕜 := ℝ) coefficient state)
            noiseCovariance) =
        (multivariateGaussian sourceMean sourceCovariance).map
            (fun state =>
              shift +
                Matrix.toEuclideanCLM (𝕜 := ℝ) coefficient state) ∗
          multivariateGaussian 0 noiseCovariance := by
      refine Measure.ext_of_lintegral _ fun f hfMeasurable => ?_
      rw [Measure.lintegral_bind hMeasurable.aemeasurable (by fun_prop),
        Measure.lintegral_conv (by fun_prop),
        lintegral_map (by fun_prop) (by fun_prop)]
      congr with state
      have hTranslated :
          (multivariateGaussian 0 noiseCovariance).map
              (fun noise =>
                shift +
                  Matrix.toEuclideanCLM (𝕜 := ℝ) coefficient state +
                    noise) =
            multivariateGaussian
              (shift +
                Matrix.toEuclideanCLM (𝕜 := ℝ) coefficient state)
              noiseCovariance := by
        exact multivariateGaussian_zero_map_const_add _ _
      rw [← hTranslated, lintegral_map hfMeasurable (by fun_prop)]
    _ = _ := multivariateGaussian_affine_conv sourceMean shift
      sourceCovariance noiseCovariance hSourceCovariance
      hNoiseCovariance coefficient

/-- Evolving a multivariate Gaussian through one slice remains a multivariate
Gaussian with the derived affine mean and transported-plus-noise covariance. -/
theorem transition_comp_multivariateGaussian
    (model : LinearGaussianParameters Axis) (time : ℝ≥0)
    (sourceMean : State Axis)
    (sourceCovariance : Matrix Axis Axis ℝ)
    (hSourceCovariance : sourceCovariance.PosSemidef) :
    model.transition time ∘ₘ
        multivariateGaussian sourceMean sourceCovariance =
      multivariateGaussian
        (model.transitionMean time sourceMean)
        (model.evolution time * sourceCovariance *
            (model.evolution time)ᵀ +
          model.transitionCovariance time) := by
  have hRowsMeasurable :
      Measurable (fun state =>
        multivariateGaussian (model.transitionMean time state)
          (model.transitionCovariance time)) := by
    rw [show (fun state =>
        multivariateGaussian (model.transitionMean time state)
          (model.transitionCovariance time)) = model.transition time by
      funext state
      exact (model.transition_apply time state).symm]
    exact (model.transition time).measurable
  calc
    model.transition time ∘ₘ
          multivariateGaussian sourceMean sourceCovariance =
        (multivariateGaussian sourceMean sourceCovariance).bind
          (fun state =>
            multivariateGaussian (model.transitionMean time state)
              (model.transitionCovariance time)) := by
      apply Measure.bind_congr_right
      filter_upwards with state
      exact model.transition_apply time state
    _ = _ := by
      simp_rw [model.transitionMean_affine time]
      exact multivariateGaussian_bind_affine sourceMean
        (model.center -
          Matrix.toEuclideanCLM (𝕜 := ℝ) (model.evolution time)
            model.center)
        sourceCovariance (model.transitionCovariance time)
        hSourceCovariance (model.transitionCovariance_posSemidef time)
        (model.evolution time) (by
          simpa only [model.transitionMean_affine time] using hRowsMeasurable)

/-- Chapman--Kolmogorov with the later slice composed on the left. -/
theorem transition_add (model : LinearGaussianParameters Axis)
    (left right : ℝ≥0) :
    model.transition (left + right) =
      model.transition right ∘ₖ model.transition left := by
  apply DFunLike.ext _ _
  intro state
  rw [Kernel.comp_apply]
  calc
    model.transition (left + right) state =
        multivariateGaussian (model.transitionMean (left + right) state)
          (model.transitionCovariance (left + right)) :=
      model.transition_apply (left + right) state
    _ = multivariateGaussian
        (model.transitionMean right (model.transitionMean left state))
        (model.evolution right * model.transitionCovariance left *
            (model.evolution right)ᵀ + model.transitionCovariance right) := by
      rw [← model.transitionMean_add left right state,
        ← model.transitionCovariance_add left right]
    _ = model.transition right ∘ₘ model.transition left state := by
      rw [model.transition_apply]
      exact
        (model.transition_comp_multivariateGaussian right
          (model.transitionMean left state) (model.transitionCovariance left)
          (model.transitionCovariance_posSemidef left)).symm

/-- H2.4 packaging of the exact native transition family. -/
noncomputable def nativeSemigroup (model : LinearGaussianParameters Axis) :
    FEP.MarkovSemigroup.NativeKernelSemigroup model.transition where
  kernel_zero := model.transition_zero
  kernel_add := model.transition_add

/-- Invariant multivariate Gaussian law derived from center and precision. -/
noncomputable def stationaryLaw (model : LinearGaussianParameters Axis) :
    Measure (State Axis) :=
  multivariateGaussian model.center model.covariance

noncomputable instance stationaryLaw_isProbabilityMeasure
    (model : LinearGaussianParameters Axis) :
    IsProbabilityMeasure model.stationaryLaw := by
  unfold stationaryLaw
  infer_instance

/-- The stationary Gaussian is invariant under every transition slice. -/
theorem stationaryLaw_invariant (model : LinearGaussianParameters Axis) :
    FEP.MarkovSemigroup.InvariantLaw
      model.nativeSemigroup model.stationaryLaw := by
  intro time
  rw [Kernel.Invariant]
  rw [stationaryLaw,
    model.transition_comp_multivariateGaussian time model.center
      model.covariance model.covariance_posDef.posSemidef]
  rw [transitionMean, transitionCovariance]
  simp

/-- The transition mean is its multivariate Gaussian mean parameter. -/
theorem transition_mean (model : LinearGaussianParameters Axis)
    (time : ℝ≥0) (state : State Axis) :
    (∫ next, next ∂model.transition time state) =
      model.transitionMean time state := by
  rw [model.transition_apply]
  exact integral_id_multivariateGaussian

/-- Coordinate covariances of a transition row equal the corresponding
entries of the derived transition covariance. -/
theorem transition_covariance (model : LinearGaussianParameters Axis)
    (time : ℝ≥0) (state : State Axis) (left right : Axis) :
    cov[fun next => next left, fun next => next right;
      model.transition time state] =
        model.transitionCovariance time left right := by
  rw [model.transition_apply]
  exact covariance_eval_multivariateGaussian
    (model.transitionCovariance_posSemidef time) left right

/-- Probability-measure view of one transition row. -/
noncomputable def transitionProbability
    (model : LinearGaussianParameters Axis) (time : ℝ≥0)
    (state : State Axis) : ProbabilityMeasure (State Axis) :=
  ⟨model.transition time state, inferInstance⟩

/-- Probability-measure view of the invariant law. -/
noncomputable def stationaryProbability
    (model : LinearGaussianParameters Axis) :
    ProbabilityMeasure (State Axis) :=
  ⟨model.stationaryLaw, inferInstance⟩

private theorem evolution_tendsto_zero
    (model : LinearGaussianParameters Axis) :
    Tendsto model.evolution atTop (𝓝 0) := by
  have hScalar (eigen : Axis) :
      Tendsto
        (fun time : ℝ≥0 =>
          Real.exp (-((time : ℝ) *
            model.precision_posDef.isHermitian.eigenvalues eigen)))
        atTop (𝓝 0) := by
    have hTime :
        Tendsto (fun time : ℝ≥0 => (time : ℝ)) atTop atTop :=
      NNReal.tendsto_coe_atTop.mpr tendsto_id
    have hEigenvalue := model.precision_posDef.eigenvalues_pos eigen
    have hExponent :
        Tendsto
          (fun time : ℝ≥0 =>
            -(model.precision_posDef.isHermitian.eigenvalues eigen) *
              (time : ℝ))
          atTop atBot :=
      (tendsto_const_mul_atBot_of_neg
        (neg_lt_zero.mpr hEigenvalue)).mpr hTime
    convert Real.tendsto_exp_atBot.comp hExponent using 1
    funext time
    simp only [Function.comp_apply]
    congr 1
    ring
  have hDiagonal :
      Tendsto
        (fun time : ℝ≥0 => Matrix.diagonal (fun eigen =>
          Real.exp (-((time : ℝ) *
            model.precision_posDef.isHermitian.eigenvalues eigen))))
        atTop (𝓝 0) := by
    apply tendsto_pi_nhds.2
    intro row
    apply tendsto_pi_nhds.2
    intro column
    by_cases h : row = column
    · subst column
      simpa using hScalar row
    · simp [h]
  have hUnitary :
      Tendsto
        (fun _ : ℝ≥0 =>
          (model.precision_posDef.isHermitian.eigenvectorUnitary :
            Matrix Axis Axis ℝ))
        atTop
        (𝓝 (model.precision_posDef.isHermitian.eigenvectorUnitary :
          Matrix Axis Axis ℝ)) := tendsto_const_nhds
  have hConjugated :=
    (hUnitary.mul hDiagonal).mul_const
      (model.precision_posDef.isHermitian.eigenvectorUnitary :
        Matrix Axis Axis ℝ)ᵀ
  rw [show model.evolution = fun (time : ℝ≥0) =>
      (model.precision_posDef.isHermitian.eigenvectorUnitary :
          Matrix Axis Axis ℝ) *
        Matrix.diagonal (fun eigen =>
          Real.exp (-((time : ℝ) *
            model.precision_posDef.isHermitian.eigenvalues eigen))) *
        (model.precision_posDef.isHermitian.eigenvectorUnitary :
          Matrix Axis Axis ℝ)ᵀ by
    funext time
    exact evolution_spectral_form model time]
  simpa using hConjugated

private theorem transitionMean_tendsto_center
    (model : LinearGaussianParameters Axis) (state : State Axis) :
    Tendsto (fun time : ℝ≥0 => model.transitionMean time state)
      atTop (𝓝 model.center) := by
  have hEvolution := model.evolution_tendsto_zero
  have hApply :
      Tendsto
        (fun time : ℝ≥0 =>
          Matrix.toEuclideanCLM (𝕜 := ℝ) (model.evolution time)
            (state - model.center))
        atTop (𝓝 0) := by
    have hContinuous :
        Continuous
          (fun matrix : Matrix Axis Axis ℝ =>
            Matrix.toEuclideanCLM (𝕜 := ℝ) matrix
              (state - model.center)) := by
      change Continuous (fun matrix : Matrix Axis Axis ℝ =>
        WithLp.toLp 2
          (matrix *ᵥ WithLp.ofLp (state - model.center)))
      exact (PiLp.continuous_toLp 2 (fun _ : Axis => ℝ)).comp
        (continuous_id.matrix_mulVec continuous_const)
    have hComposed := hContinuous.continuousAt.tendsto.comp hEvolution
    change
      Tendsto
        (fun time : ℝ≥0 =>
          Matrix.toEuclideanCLM (𝕜 := ℝ) (model.evolution time)
            (state - model.center))
        atTop
        (𝓝 (Matrix.toEuclideanCLM (𝕜 := ℝ) 0
          (state - model.center))) at hComposed
    simpa using hComposed
  simpa only [transitionMean, add_zero] using
    tendsto_const_nhds.add hApply

private theorem transitionCovariance_tendsto_covariance
    (model : LinearGaussianParameters Axis) :
    Tendsto model.transitionCovariance atTop (𝓝 model.covariance) := by
  have hEvolution := model.evolution_tendsto_zero
  have hTranspose :
      Tendsto (fun time : ℝ≥0 => (model.evolution time)ᵀ)
        atTop (𝓝 0) := by
    have hComposed :=
      continuous_id.matrix_transpose.continuousAt.tendsto.comp hEvolution
    change
      Tendsto (fun time : ℝ≥0 => (model.evolution time)ᵀ)
        atTop (𝓝 (0 : Matrix Axis Axis ℝ)ᵀ) at hComposed
    simpa using hComposed
  change
    Tendsto
      (fun time : ℝ≥0 => model.covariance -
        model.evolution time * model.covariance *
          (model.evolution time)ᵀ)
      atTop (𝓝 model.covariance)
  have hCovariance :
      Tendsto (fun _ : ℝ≥0 => model.covariance) atTop
        (𝓝 model.covariance) := tendsto_const_nhds
  simpa only [zero_mul, mul_zero, sub_zero] using
    hCovariance.sub
      ((hEvolution.mul_const model.covariance).mul hTranspose)

omit [DecidableEq Axis] in
private theorem quadratic_tendsto
    {covariances : ℕ → Matrix Axis Axis ℝ}
    {limitCovariance : Matrix Axis Axis ℝ}
    (hCovariance : Tendsto covariances atTop (𝓝 limitCovariance))
    (frequency : State Axis) :
    Tendsto
      (fun index =>
        frequency ⬝ᵥ covariances index *ᵥ frequency)
      atTop
      (𝓝 (frequency ⬝ᵥ limitCovariance *ᵥ frequency)) := by
  simp only [dotProduct, mulVec]
  apply tendsto_finsetSum Finset.univ
  intro column _
  exact tendsto_const_nhds.mul
    (tendsto_finsetSum Finset.univ fun row _ =>
      (tendsto_pi_nhds.1
        (tendsto_pi_nhds.1 hCovariance column) row).mul_const _)

private theorem multivariateGaussian_charFun_tendsto
    {means : ℕ → State Axis}
    {covariances : ℕ → Matrix Axis Axis ℝ}
    {limitMean : State Axis}
    {limitCovariance : Matrix Axis Axis ℝ}
    (hMean : Tendsto means atTop (𝓝 limitMean))
    (hCovariance : Tendsto covariances atTop (𝓝 limitCovariance))
    (hCovariances : ∀ index, (covariances index).PosSemidef)
    (hLimitCovariance : limitCovariance.PosSemidef)
    (frequency : State Axis) :
    Tendsto
      (fun index =>
        charFun (multivariateGaussian (means index) (covariances index))
          frequency)
      atTop
      (𝓝 (charFun
        (multivariateGaussian limitMean limitCovariance) frequency)) := by
  simp_rw [charFun_multivariateGaussian (hCovariances _)]
  rw [charFun_multivariateGaussian hLimitCovariance]
  have hMeanReal :
      Tendsto (fun index => ⟪frequency, means index⟫)
        atTop (𝓝 ⟪frequency, limitMean⟫) :=
    Filter.Tendsto.inner tendsto_const_nhds hMean
  have hMeanComplex :
      Tendsto (fun index => (⟪frequency, means index⟫ : ℂ))
        atTop (𝓝 (⟪frequency, limitMean⟫ : ℂ)) :=
    Filter.tendsto_ofReal_iff.mpr hMeanReal
  have hQuadraticReal := quadratic_tendsto hCovariance frequency
  have hQuadraticComplex :
      Tendsto
        (fun index =>
          ((frequency ⬝ᵥ covariances index *ᵥ frequency : ℝ) : ℂ))
        atTop
        (𝓝 (((frequency ⬝ᵥ limitCovariance *ᵥ frequency : ℝ) : ℂ))) :=
    Filter.tendsto_ofReal_iff.mpr hQuadraticReal
  exact
    ((hMeanComplex.mul_const Complex.I).sub
      (hQuadraticComplex.div_const 2)).cexp

/-- The full nonnegative-time transition law converges weakly from every fixed
state to the invariant multivariate Gaussian. -/
theorem transitionProbability_tendsto_invariant
    (model : LinearGaussianParameters Axis) (state : State Axis) :
    Tendsto
      (fun time : ℝ≥0 => model.transitionProbability time state)
      atTop (𝓝 model.stationaryProbability) := by
  apply Filter.tendsto_of_seq_tendsto
  intro times hTimes
  rw [ProbabilityMeasure.tendsto_iff_tendsto_charFun]
  intro frequency
  simp only [Function.comp_apply]
  change
    Tendsto
      (fun index => charFun (model.transition (times index) state) frequency)
      atTop (𝓝 (charFun model.stationaryLaw frequency))
  simp_rw [model.transition_apply]
  change
    Tendsto
      (fun index => charFun
        (multivariateGaussian (model.transitionMean (times index) state)
          (model.transitionCovariance (times index))) frequency)
      atTop
      (𝓝 (charFun (multivariateGaussian model.center model.covariance)
        frequency))
  exact multivariateGaussian_charFun_tendsto
    ((model.transitionMean_tendsto_center state).comp hTimes)
    (model.transitionCovariance_tendsto_covariance.comp hTimes)
    (fun index => model.transitionCovariance_posSemidef (times index))
    model.covariance_posDef.posSemidef frequency

/-- Weak convergence transfers to bounded continuous real observables. -/
theorem integral_transition_tendsto_invariant
    (model : LinearGaussianParameters Axis) (state : State Axis)
    (f : State Axis →ᵇ ℝ) :
    Tendsto
      (fun time : ℝ≥0 =>
        ∫ next, f next ∂
          (model.transitionProbability time state : Measure (State Axis)))
      atTop
      (𝓝 (∫ next, f next ∂
        (model.stationaryProbability : Measure (State Axis)))) := by
  exact
    (ProbabilityMeasure.tendsto_iff_forall_integral_tendsto.mp
      (model.transitionProbability_tendsto_invariant state)) f

/-- Embed a scalar as the sole coordinate of `EuclideanSpace ℝ (Fin 1)`. -/
noncomputable def finOneState (value : ℝ) : State (Fin 1) :=
  WithLp.toLp 2 (fun _ => value)

theorem finOneState_measurable : Measurable finOneState := by
  unfold finOneState
  fun_prop

/-- One-axis precision model with drift rate `rate`. -/
noncomputable def finOneParameters
    (rate : ℝ) (hRate : 0 < rate) (center : ℝ) :
    LinearGaussianParameters (Fin 1) where
  precision := rate • (1 : Matrix (Fin 1) (Fin 1) ℝ)
  precision_posDef := Matrix.PosDef.one.smul hRate
  center := finOneState center

/-- H2.5a parameter identification for the one-axis model.  The generic
precision construction corresponds exactly to diffusion variance rate `2`. -/
noncomputable def finOneScalarParameters
    (rate : ℝ) (hRate : 0 < rate) (center : ℝ) :
    FEP.ScalarGaussianSemigroup.ScalarOUParameters where
  rate := rate
  rate_pos := hRate
  center := center
  diffusionVarianceRate := 2
  diffusionVarianceRate_pos := by norm_num

/-- Transport a one-axis transition kernel to the scalar carrier by the
explicit embedding/evaluation pair. -/
noncomputable def finOneTransition
    (model : LinearGaussianParameters (Fin 1)) (time : ℝ≥0) :
    Kernel ℝ ℝ :=
  Kernel.map
    (Kernel.comap (model.transition time) finOneState finOneState_measurable)
    (fun state : State (Fin 1) => state 0)

private theorem finOne_covariance_entry
    (rate : ℝ) (hRate : 0 < rate) (center : ℝ) :
    (finOneParameters rate hRate center).covariance 0 0 = rate⁻¹ := by
  have hIdentity :=
    (finOneParameters rate hRate center).precision_mul_covariance
  have hEntry := congrArg (fun matrix : Matrix (Fin 1) (Fin 1) ℝ => matrix 0 0)
    hIdentity
  have hEntry' :
      rate * (finOneParameters rate hRate center).covariance 0 0 = 1 := by
    simpa [finOneParameters, Matrix.mul_apply] using hEntry
  rw [← one_div]
  apply (eq_div_iff hRate.ne').2
  simpa [div_eq_mul_inv, mul_comm] using hEntry'

private theorem finOne_evolution_entry
    (rate : ℝ) (hRate : 0 < rate) (center : ℝ) (time : ℝ≥0) :
    (finOneParameters rate hRate center).evolution time 0 0 =
      (finOneScalarParameters rate hRate center).decay time := by
  rw [evolution]
  simp only [finOneParameters, smul_smul]
  rw [Matrix.smul_one_eq_diagonal, Matrix.exp_diagonal, Pi.exp_def]
  rw [← Real.exp_eq_exp_ℝ]
  simp [FEP.ScalarGaussianSemigroup.ScalarOUParameters.decay,
    finOneScalarParameters, mul_comm]

private theorem finOne_stationaryVariance
    (rate : ℝ) (hRate : 0 < rate) (center : ℝ) :
    (((finOneScalarParameters rate hRate center).stationaryVariance : ℝ)) =
      rate⁻¹ := by
  change (2 : ℝ) / (2 * rate) = rate⁻¹
  field_simp [hRate.ne']

/-- Under the explicit state and parameter identification, the sole
transition-mean coordinate is exactly H2.5a's scalar transition mean. -/
theorem finOne_transitionMean
    (rate : ℝ) (hRate : 0 < rate) (center : ℝ)
    (time : ℝ≥0) (state : ℝ) :
    (finOneParameters rate hRate center).transitionMean time
        (finOneState state) 0 =
      (finOneScalarParameters rate hRate center).transitionMean time state := by
  simp only [transitionMean, finOneParameters, finOneState]
  change center +
      (∑ column : Fin 1,
        (finOneParameters rate hRate center).evolution time 0 column *
          (state - center)) = _
  rw [Fin.sum_univ_one]
  rw [finOne_evolution_entry]
  rfl

/-- The sole transition-covariance entry is exactly H2.5a's scalar transition
variance after identifying the diffusion variance rate with `2`. -/
theorem finOne_transitionCovariance
    (rate : ℝ) (hRate : 0 < rate) (center : ℝ)
    (time : ℝ≥0) :
    (finOneParameters rate hRate center).transitionCovariance time 0 0 =
      (((finOneScalarParameters rate hRate center).transitionVariance time :
        ℝ≥0) : ℝ) := by
  simp only [transitionCovariance, Matrix.sub_apply, Matrix.mul_apply,
    Matrix.transpose_apply, Fin.sum_univ_one]
  rw [finOne_covariance_entry, finOne_evolution_entry]
  change
    rate⁻¹ -
        (finOneScalarParameters rate hRate center).decay time * rate⁻¹ *
          (finOneScalarParameters rate hRate center).decay time =
      ((finOneScalarParameters rate hRate center).stationaryVariance : ℝ) *
        (1 -
          (finOneScalarParameters rate hRate center).decay time ^ 2)
  rw [finOne_stationaryVariance]
  ring

/-- The explicitly transported `Fin 1` kernel is exactly the accepted H2.5a
scalar OU kernel, not merely a same-shape Gaussian. -/
theorem finOneTransition_eq_scalarOU
    (rate : ℝ) (hRate : 0 < rate) (center : ℝ) (time : ℝ≥0) :
    (finOneParameters rate hRate center).finOneTransition time =
      (finOneScalarParameters rate hRate center).ouTransition time := by
  apply DFunLike.ext _ _
  intro state
  rw [finOneTransition, Kernel.map_apply _ (by fun_prop), Kernel.comap_apply]
  rw [(finOneParameters rate hRate center).transition_apply]
  calc
    (multivariateGaussian
        ((finOneParameters rate hRate center).transitionMean time
          (finOneState state))
        ((finOneParameters rate hRate center).transitionCovariance time)).map
          (fun next : State (Fin 1) => next 0) =
        gaussianReal
          ((finOneParameters rate hRate center).transitionMean time
            (finOneState state) 0)
          (((finOneParameters rate hRate center).transitionCovariance time 0 0).toNNReal) := by
      exact
        (measurePreserving_eval_multivariateGaussian
          ((finOneParameters rate hRate center).transitionCovariance_posSemidef time)
          (i := (0 : Fin 1))).map_eq
    _ = gaussianReal
        ((finOneScalarParameters rate hRate center).transitionMean time state)
        ((finOneScalarParameters rate hRate center).transitionVariance time) := by
      rw [finOne_transitionMean, finOne_transitionCovariance]
      simp
    _ = (finOneScalarParameters rate hRate center).ouTransition time state :=
      rfl

end LinearGaussianParameters

end

end FEP.LinearGaussianSemigroup
