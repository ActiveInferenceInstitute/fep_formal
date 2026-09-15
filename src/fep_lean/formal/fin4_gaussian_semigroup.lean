import FepSketches.linear_gaussian_semigroup

/-!
# Exact named-axis four-coordinate Gaussian carrier

This module specializes the accepted symmetric-precision linear Gaussian
transition to the preregistered standardized coordinates `external`,
`sensory`, `active`, and `internal`.  The stationary covariance, transition
kernel, semigroup, invariant law, and limits are derived from the fixed raw
precision through `FEP.LinearGaussianSemigroup`.

This is a transition-law construction.  It does not assert a stochastic
process, an SDE or generator, a reversibility law, or a conditioning result.
-/

open Filter MeasureTheory Matrix NormedSpace ProbabilityTheory
open scoped BoundedContinuousFunction MatrixOrder MeasureTheory NNReal ProbabilityTheory
  RealInnerProductSpace Topology

namespace FEP.Fin4GaussianSemigroup

noncomputable section

/-- Scientific coordinate names in the preregistered order. -/
inductive Axis
  | external
  | sensory
  | active
  | internal
  deriving DecidableEq

open Axis

/-- The only bridge from named scientific coordinates to `Fin 4`. -/
def axisFin : Axis ≃ Fin 4 where
  toFun
    | external => 0
    | sensory => 1
    | active => 2
    | internal => 3
  invFun :=
    Fin.cases external (Fin.cases sensory (Fin.cases active (fun _ => internal)))
  left_inv axis := by cases axis <;> rfl
  right_inv index := by fin_cases index <;> rfl

noncomputable instance : Fintype Axis :=
  Fintype.ofEquiv (Fin 4) axisFin.symm

/-- Dimensionless Euclidean state over the named axis. -/
abbrev StandardizedState :=
  EuclideanSpace ℝ Axis

/-- The equivalence fixes all four coordinate labels, not merely the card. -/
theorem axisFin_order :
    axisFin external = 0 ∧
      axisFin sensory = 1 ∧
      axisFin active = 2 ∧
      axisFin internal = 3 :=
  ⟨rfl, rfl, rfl, rfl⟩

/-- The named carrier has exactly four axes. -/
theorem axis_cardinality : Fintype.card Axis = 4 := by
  rw [Fintype.card_congr axisFin]
  rfl

/-- All six pairwise distinctions between the four scientific axes are
explicitly nonvacuous. -/
theorem axis_pairwise_ne :
    external ≠ sensory ∧ external ≠ active ∧ external ≠ internal ∧
      sensory ≠ active ∧ sensory ≠ internal ∧ active ≠ internal := by
  decide

private lemma sum_axis {M : Type*} [AddCommMonoid M] (f : Axis → M) :
    ∑ axis, f axis =
      f external + f sensory + f active + f internal := by
  classical
  change Finset.univ.sum f = _
  rw [show (Finset.univ : Finset Axis) =
      {external, sensory, active, internal} by
    ext axis
    cases axis <;> simp]
  simp [add_left_comm, add_comm]

/-- Fixed raw precision in named scientific coordinates. -/
def K : Matrix Axis Axis ℝ
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

/-- Stationary covariance derived from the fixed precision. -/
noncomputable def Sigma : Matrix Axis Axis ℝ :=
  K⁻¹

/-- The fixed precision is symmetric. -/
theorem K_isSymm : K.IsSymm := by
  ext row column
  cases row <;> cases column <;> rfl

/-- The fixed real symmetric precision is Hermitian. -/
theorem K_isHermitian : K.IsHermitian := by
  exact Matrix.isHermitian_iff_isSymm.mpr K_isSymm

/-- The fixed precision is positive definite, witnessed without a stored
minor or positivity certificate. -/
theorem K_posDef : K.PosDef := by
  apply Matrix.PosDef.of_dotProduct_mulVec_pos K_isHermitian
  intro state hState
  have hCoordinate : ∃ axis, state axis ≠ 0 := by
    by_contra h
    apply hState
    funext axis
    by_contra hAxis
    exact h ⟨axis, hAxis⟩
  obtain ⟨axis, hAxis⟩ := hCoordinate
  have hQuadratic :
      star state ⬝ᵥ (K *ᵥ state) =
        2 * state external ^ 2 + 2 * state sensory ^ 2 +
          2 * state active ^ 2 + 2 * state internal ^ 2 +
          (state external - state sensory) ^ 2 +
          (state external - state active) ^ 2 +
          (state sensory - state internal) ^ 2 +
          (state active - state internal) ^ 2 := by
    simp [dotProduct, Matrix.mulVec, sum_axis, K]
    ring
  rw [hQuadratic]
  cases axis <;>
    nlinarith [sq_pos_of_ne_zero hAxis,
      sq_nonneg (state external - state sensory),
      sq_nonneg (state external - state active),
      sq_nonneg (state sensory - state internal),
      sq_nonneg (state active - state internal)]

/-- The normalized-rate-two eigendirection before normalization. -/
def eigenmodeTwo : Axis → ℝ :=
  fun _ => 1

/-- First named rate-four eigendirection. -/
def eigenmodeFourExternal : Axis → ℝ
  | external => 1
  | sensory => 0
  | active => 0
  | internal => -1

/-- Second named rate-four eigendirection. -/
def eigenmodeFourSensory : Axis → ℝ
  | external => 0
  | sensory => 1
  | active => -1
  | internal => 0

/-- Named rate-six eigendirection. -/
def eigenmodeSix : Axis → ℝ
  | external => 1
  | sensory => -1
  | active => -1
  | internal => 1

/-- The all-ones mode has exact precision rate two. -/
theorem K_eigenmode_two :
    K *ᵥ eigenmodeTwo = 2 • eigenmodeTwo := by
  funext axis
  cases axis <;>
    norm_num [Matrix.mulVec, dotProduct, sum_axis, K, eigenmodeTwo]

/-- The external--internal contrast has exact precision rate four. -/
theorem K_eigenmode_four_external :
    K *ᵥ eigenmodeFourExternal = 4 • eigenmodeFourExternal := by
  funext axis
  cases axis <;>
    norm_num [Matrix.mulVec, dotProduct, sum_axis, K,
      eigenmodeFourExternal]

/-- The sensory--active contrast has exact precision rate four. -/
theorem K_eigenmode_four_sensory :
    K *ᵥ eigenmodeFourSensory = 4 • eigenmodeFourSensory := by
  funext axis
  cases axis <;>
    norm_num [Matrix.mulVec, dotProduct, sum_axis, K,
      eigenmodeFourSensory]

/-- The alternating interface mode has exact precision rate six. -/
theorem K_eigenmode_six :
    K *ᵥ eigenmodeSix = 6 • eigenmodeSix := by
  funext axis
  cases axis <;>
    norm_num [Matrix.mulVec, dotProduct, sum_axis, K, eigenmodeSix]

/-- Every named eigenmode is nonzero. -/
theorem eigenmodes_nonzero :
    eigenmodeTwo ≠ 0 ∧
      eigenmodeFourExternal ≠ 0 ∧
      eigenmodeFourSensory ≠ 0 ∧
      eigenmodeSix ≠ 0 := by
  constructor
  · intro h
    have := congrFun h external
    norm_num [eigenmodeTwo] at this
  constructor
  · intro h
    have := congrFun h external
    norm_num [eigenmodeFourExternal] at this
  constructor
  · intro h
    have := congrFun h sensory
    norm_num [eigenmodeFourSensory] at this
  · intro h
    have := congrFun h external
    norm_num [eigenmodeSix] at this

/-- The four named modes are independent, so the repeated rate four has two
distinct directions and the four equations exhaust the four-coordinate
carrier. -/
theorem eigenmodes_independent
    (two fourExternal fourSensory six : ℝ)
    (h : ∀ axis,
      two * eigenmodeTwo axis +
          fourExternal * eigenmodeFourExternal axis +
          fourSensory * eigenmodeFourSensory axis +
          six * eigenmodeSix axis = 0) :
    two = 0 ∧ fourExternal = 0 ∧ fourSensory = 0 ∧ six = 0 := by
  have hExternal := h external
  have hSensory := h sensory
  have hActive := h active
  have hInternal := h internal
  norm_num [eigenmodeTwo, eigenmodeFourExternal, eigenmodeFourSensory,
    eigenmodeSix] at hExternal hSensory hActive hInternal
  constructor
  · linarith
  constructor
  · linarith
  constructor <;> linarith

/-- Precision times its derived covariance is the identity. -/
theorem K_mul_Sigma : K * Sigma = 1 := by
  exact Matrix.mul_nonsing_inv K
    (K.isUnit_iff_isUnit_det.mp K_posDef.isUnit)

/-- The derived covariance times precision is the identity. -/
theorem Sigma_mul_K : Sigma * K = 1 := by
  exact Matrix.nonsing_inv_mul K
    (K.isUnit_iff_isUnit_det.mp K_posDef.isUnit)

/-- The derived inverse has exactly the preregistered rational entries. -/
theorem Sigma_eq_entries :
    Sigma = fun
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
      | internal, internal => 7 / 24 := by
  let entries : Matrix Axis Axis ℝ := fun
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
  change K⁻¹ = entries
  apply Matrix.inv_eq_right_inv
  ext row column
  change (∑ axis, K row axis * entries axis column) =
    (1 : Matrix Axis Axis ℝ) row column
  rw [sum_axis]
  cases row <;> cases column <;>
    norm_num [K, entries, Matrix.one_apply]

/-- The exact derived covariance is symmetric. -/
theorem Sigma_isSymm : Sigma.IsSymm := by
  rw [Sigma_eq_entries]
  ext row column
  cases row <;> cases column <;> rfl

/-- The derived stationary covariance is positive definite. -/
theorem Sigma_posDef : Sigma.PosDef := by
  rw [Sigma]
  exact K_posDef.inv

/-- The external--internal precision entry is exactly zero. -/
theorem K_external_internal : K external internal = 0 :=
  rfl

/-- The external--internal covariance entry is the derived nonzero value. -/
theorem Sigma_external_internal : Sigma external internal = 1 / 24 := by
  rw [Sigma_eq_entries]

/-- The external--internal covariance entry is not zero. -/
theorem Sigma_external_internal_ne_zero : Sigma external internal ≠ 0 := by
  rw [Sigma_external_internal]
  norm_num

/-! ## Exact specialization of the accepted linear Gaussian owner -/

/-- The only raw model data are the fixed precision, its proved positivity,
and an arbitrary center.  Covariance and transition laws remain derived by
the generic owner. -/
noncomputable def parameters (center : StandardizedState) :
    FEP.LinearGaussianSemigroup.LinearGaussianParameters Axis where
  precision := K
  precision_posDef := K_posDef
  center := center

/-- The generic owner's derived covariance is exactly the named `Sigma`. -/
theorem parameters_covariance (center : StandardizedState) :
    (parameters center).covariance = Sigma :=
  rfl

/-- Exact finite-time transition kernel on the named state. -/
noncomputable def transition (center : StandardizedState) (time : ℝ≥0) :
    Kernel StandardizedState StandardizedState :=
  (parameters center).transition time

noncomputable instance transition_isMarkovKernel
    (center : StandardizedState) (time : ℝ≥0) :
    IsMarkovKernel (transition center time) := by
  unfold transition
  infer_instance

/-- Every nonnegative time has an exact positive-semidefinite transition
covariance. -/
theorem transitionCovariance_posSemidef (center : StandardizedState)
    (time : ℝ≥0) :
    (Sigma -
      NormedSpace.exp ((-(time : ℝ)) • K) * Sigma *
        (NormedSpace.exp ((-(time : ℝ)) • K))ᵀ).PosSemidef := by
  change ((parameters center).transitionCovariance time).PosSemidef
  exact (parameters center).transitionCovariance_posSemidef time

/-- Strictly positive time gives an exact positive-definite transition
covariance. -/
theorem transitionCovariance_posDef (center : StandardizedState)
    (time : ℝ≥0) (hTime : 0 < time) :
    (Sigma -
      NormedSpace.exp ((-(time : ℝ)) • K) * Sigma *
        (NormedSpace.exp ((-(time : ℝ)) • K))ᵀ).PosDef := by
  change ((parameters center).transitionCovariance time).PosDef
  exact (parameters center).transitionCovariance_posDef time hTime

/-- Every transition row is the exact Gaussian determined by the fixed
precision and its derived covariance. -/
theorem transition_apply (center : StandardizedState) (time : ℝ≥0)
    (state : StandardizedState) :
    transition center time state =
      multivariateGaussian
        (center + Matrix.toEuclideanCLM (𝕜 := ℝ)
          (NormedSpace.exp ((-(time : ℝ)) • K)) (state - center))
        (Sigma -
          NormedSpace.exp ((-(time : ℝ)) • K) * Sigma *
            (NormedSpace.exp ((-(time : ℝ)) • K))ᵀ) := by
  simpa [transition, parameters, Sigma,
    FEP.LinearGaussianSemigroup.LinearGaussianParameters.transitionMean,
    FEP.LinearGaussianSemigroup.LinearGaussianParameters.transitionCovariance,
    FEP.LinearGaussianSemigroup.LinearGaussianParameters.evolution,
    FEP.LinearGaussianSemigroup.LinearGaussianParameters.covariance] using
      (parameters center).transition_apply time state

/-- Every exact transition row is normalized. -/
theorem transition_univ (center : StandardizedState) (time : ℝ≥0)
    (state : StandardizedState) :
    transition center time state Set.univ = 1 := by
  simp [transition]

/-- The zero-time slice is the native identity kernel. -/
theorem transition_zero (center : StandardizedState) :
    transition center 0 = Kernel.id := by
  simpa [transition] using (parameters center).transition_zero

/-- Chapman--Kolmogorov in chronological order: the later/right slice is
composed on the left. -/
theorem transition_add (center : StandardizedState) (left right : ℝ≥0) :
    transition center (left + right) =
      transition center right ∘ₖ transition center left := by
  simpa [transition] using (parameters center).transition_add left right

/-- H2.4 native-semigroup packaging of the exact Fin4 transition family. -/
noncomputable def nativeSemigroup (center : StandardizedState) :
    FEP.MarkovSemigroup.NativeKernelSemigroup (transition center) where
  kernel_zero := transition_zero center
  kernel_add := transition_add center

/-- Exact invariant Gaussian with arbitrary center and derived covariance. -/
noncomputable def stationaryLaw (center : StandardizedState) :
    Measure StandardizedState :=
  (parameters center).stationaryLaw

noncomputable instance stationaryLaw_isProbabilityMeasure
    (center : StandardizedState) :
    IsProbabilityMeasure (stationaryLaw center) := by
  unfold stationaryLaw
  infer_instance

/-- The invariant law is exactly the Gaussian with the arbitrary center and
the fixed precision's derived covariance. -/
theorem stationaryLaw_eq_gaussian (center : StandardizedState) :
    stationaryLaw center = multivariateGaussian center Sigma :=
  rfl

/-- The derived stationary Gaussian is invariant under every exact slice. -/
theorem stationaryLaw_invariant (center : StandardizedState) :
    FEP.MarkovSemigroup.InvariantLaw
      (nativeSemigroup center) (stationaryLaw center) := by
  intro time
  simpa [nativeSemigroup, stationaryLaw, transition] using
    (parameters center).stationaryLaw_invariant time

/-- The exact Gaussian parameter is the row mean. -/
theorem transition_mean (center : StandardizedState) (time : ℝ≥0)
    (state : StandardizedState) :
    (∫ next, next ∂transition center time state) =
      center + Matrix.toEuclideanCLM (𝕜 := ℝ)
        (NormedSpace.exp ((-(time : ℝ)) • K)) (state - center) := by
  simpa [transition, parameters,
    FEP.LinearGaussianSemigroup.LinearGaussianParameters.transitionMean,
    FEP.LinearGaussianSemigroup.LinearGaussianParameters.evolution] using
      (parameters center).transition_mean time state

/-- Named coordinate covariances are exactly the entries of the derived
finite-time covariance. -/
theorem transition_covariance (center : StandardizedState) (time : ℝ≥0)
    (state : StandardizedState) (left right : Axis) :
    cov[fun next => next left, fun next => next right;
      transition center time state] =
        (Sigma -
          NormedSpace.exp ((-(time : ℝ)) • K) * Sigma *
            (NormedSpace.exp ((-(time : ℝ)) • K))ᵀ) left right := by
  simpa [transition, parameters, Sigma,
    FEP.LinearGaussianSemigroup.LinearGaussianParameters.transitionCovariance,
    FEP.LinearGaussianSemigroup.LinearGaussianParameters.evolution,
    FEP.LinearGaussianSemigroup.LinearGaussianParameters.covariance] using
      (parameters center).transition_covariance time state left right

/-- Probability-measure view of one exact transition row. -/
noncomputable def transitionProbability (center : StandardizedState)
    (time : ℝ≥0) (state : StandardizedState) :
    ProbabilityMeasure StandardizedState :=
  (parameters center).transitionProbability time state

/-- Probability-measure view of the exact invariant law. -/
noncomputable def stationaryProbability (center : StandardizedState) :
    ProbabilityMeasure StandardizedState :=
  (parameters center).stationaryProbability

/-- Every fixed-state exact transition law converges weakly to the invariant
Gaussian. -/
theorem transitionProbability_tendsto_invariant
    (center state : StandardizedState) :
    Tendsto (fun time : ℝ≥0 => transitionProbability center time state)
      atTop (nhds (stationaryProbability center)) := by
  simpa [transitionProbability, stationaryProbability] using
    (parameters center).transitionProbability_tendsto_invariant state

/-- Weak convergence tested by every bounded continuous real observable. -/
theorem integral_transition_tendsto_invariant
    (center state : StandardizedState)
    (f : StandardizedState →ᵇ ℝ) :
    Tendsto
      (fun time : ℝ≥0 =>
        ∫ next, f next ∂
          (transitionProbability center time state : Measure StandardizedState))
      atTop
      (nhds (∫ next, f next ∂
        (stationaryProbability center : Measure StandardizedState))) := by
  simpa [transitionProbability, stationaryProbability] using
    (parameters center).integral_transition_tendsto_invariant state f

/-! ## Exact normalized all-ones scalar specialization -/

/-- The unit all-ones mode in four-dimensional Euclidean coordinates. -/
noncomputable def normalizedAllOnes : StandardizedState :=
  WithLp.toLp 2 (fun _ => (1 / 2 : ℝ))

/-- Orthogonal scalar coordinate along the normalized all-ones mode. -/
noncomputable def allOnesProjection : StandardizedState →L[ℝ] ℝ :=
  innerSL ℝ normalizedAllOnes

/-- Isometric scalar embedding into the normalized all-ones mode. -/
noncomputable def allOnesEmbedding : ℝ →L[ℝ] StandardizedState :=
  ContinuousLinearMap.toSpanSingleton ℝ normalizedAllOnes

/-- The normalization is exact: four coordinates of magnitude one half have
unit squared norm. -/
theorem normalizedAllOnes_unit :
    ⟪normalizedAllOnes, normalizedAllOnes⟫ = 1 := by
  rw [normalizedAllOnes, EuclideanSpace.inner_toLp_toLp]
  change ∑ _ : Axis, (1 / 2 : ℝ) * (1 / 2 : ℝ) = 1
  rw [sum_axis]
  norm_num

/-- Projection is a left inverse of the normalized mode embedding. -/
theorem allOnesProjection_embedding (value : ℝ) :
    allOnesProjection (allOnesEmbedding value) = value := by
  rw [allOnesProjection, allOnesEmbedding,
    ContinuousLinearMap.toSpanSingleton_apply, innerSL_apply_apply,
    real_inner_smul_right, normalizedAllOnes_unit, mul_one]

/-- The scalar observation of the mode is nontrivial. -/
theorem allOnes_projection_nontrivial :
    allOnesProjection normalizedAllOnes = 1 := by
  simpa [allOnesProjection, innerSL_apply_apply] using normalizedAllOnes_unit

/-- The normalized mode retains the exact precision eigenvalue two. -/
theorem K_normalizedAllOnes :
    K *ᵥ normalizedAllOnes = 2 • normalizedAllOnes := by
  funext axis
  cases axis <;>
    norm_num [Matrix.mulVec, dotProduct, sum_axis, K, normalizedAllOnes]

/-- The derived covariance has reciprocal eigenvalue one half on the
normalized mode. -/
theorem Sigma_normalizedAllOnes :
    Sigma *ᵥ normalizedAllOnes = (1 / 2 : ℝ) • normalizedAllOnes := by
  rw [Sigma_eq_entries]
  funext axis
  cases axis <;>
    norm_num [Matrix.mulVec, dotProduct, sum_axis, normalizedAllOnes]

private def modeBasis : Matrix Axis Axis ℝ
  | external, external => 1
  | external, sensory => 1
  | external, active => 0
  | external, internal => 1
  | sensory, external => 1
  | sensory, sensory => 0
  | sensory, active => 1
  | sensory, internal => -1
  | active, external => 1
  | active, sensory => 0
  | active, active => -1
  | active, internal => -1
  | internal, external => 1
  | internal, sensory => -1
  | internal, active => 0
  | internal, internal => 1

private def modeBasisInverse : Matrix Axis Axis ℝ
  | external, external => 1 / 4
  | external, sensory => 1 / 4
  | external, active => 1 / 4
  | external, internal => 1 / 4
  | sensory, external => 1 / 2
  | sensory, sensory => 0
  | sensory, active => 0
  | sensory, internal => -1 / 2
  | active, external => 0
  | active, sensory => 1 / 2
  | active, active => -1 / 2
  | active, internal => 0
  | internal, external => 1 / 4
  | internal, sensory => -1 / 4
  | internal, active => -1 / 4
  | internal, internal => 1 / 4

private def modeBasisUnit : (Matrix Axis Axis ℝ)ˣ where
  val := modeBasis
  inv := modeBasisInverse
  val_inv := by
    ext row column
    cases row <;> cases column <;>
      simp [Matrix.mul_apply, sum_axis, modeBasis, modeBasisInverse] <;>
      norm_num
  inv_val := by
    ext row column
    cases row <;> cases column <;>
      simp [Matrix.mul_apply, sum_axis, modeBasis, modeBasisInverse] <;>
      norm_num

private def modeRate : Axis → ℝ
  | external => 2
  | sensory => 4
  | active => 4
  | internal => 6

private theorem K_mode_decomposition :
    K = (modeBasisUnit : Matrix Axis Axis ℝ) *
      Matrix.diagonal modeRate *
        ((modeBasisUnit⁻¹ : (Matrix Axis Axis ℝ)ˣ) :
          Matrix Axis Axis ℝ) := by
  ext row column
  cases row <;> cases column <;>
    simp [Matrix.mul_apply, sum_axis, K, modeBasisUnit, modeBasis,
      modeBasisInverse, modeRate] <;>
    norm_num

private theorem evolution_mode_decomposition (time : ℝ≥0) :
    NormedSpace.exp ((-(time : ℝ)) • K) =
      modeBasis *
        Matrix.diagonal
          (fun mode => Real.exp (-((time : ℝ) * modeRate mode))) *
        modeBasisInverse := by
  calc
    NormedSpace.exp ((-(time : ℝ)) • K) =
        NormedSpace.exp
          ((modeBasisUnit : Matrix Axis Axis ℝ) *
            ((-(time : ℝ)) • Matrix.diagonal modeRate) *
              ((modeBasisUnit⁻¹ : (Matrix Axis Axis ℝ)ˣ) :
                Matrix Axis Axis ℝ)) := by
      rw [K_mode_decomposition]
      congr 1
      simp
    _ =
        (modeBasisUnit : Matrix Axis Axis ℝ) *
          NormedSpace.exp
            ((-(time : ℝ)) • Matrix.diagonal modeRate) *
          ((modeBasisUnit⁻¹ : (Matrix Axis Axis ℝ)ˣ) :
            Matrix Axis Axis ℝ) := by
      exact Matrix.exp_units_conj modeBasisUnit
        ((-(time : ℝ)) • Matrix.diagonal modeRate)
    _ = _ := by
      rw [← Matrix.diagonal_smul, Matrix.exp_diagonal]
      rw [Pi.exp_def]
      congr 1
      funext mode
      rw [← Real.exp_eq_exp_ℝ]
      simp [modeBasisUnit]

/-- Matrix evolution acts on the normalized all-ones direction with exact
rate-two decay. -/
theorem evolution_normalizedAllOnes (time : ℝ≥0) :
    NormedSpace.exp ((-(time : ℝ)) • K) *ᵥ normalizedAllOnes =
      Real.exp (-2 * (time : ℝ)) • normalizedAllOnes := by
  rw [evolution_mode_decomposition]
  rw [← Matrix.mulVec_mulVec, ← Matrix.mulVec_mulVec]
  have hInverse :
      modeBasisInverse *ᵥ normalizedAllOnes = fun
        | external => 1 / 2
        | sensory => 0
        | active => 0
        | internal => 0 := by
    funext axis
    cases axis <;>
      norm_num [Matrix.mulVec, dotProduct, sum_axis, modeBasisInverse,
        normalizedAllOnes]
  rw [hInverse]
  funext axis
  cases axis <;>
    simp [Matrix.mulVec, dotProduct, sum_axis, modeBasis, modeRate,
      normalizedAllOnes] <;>
    ring

/-- The accepted H2.5a owner at rate two and diffusion variance rate two. -/
noncomputable def scalarParameters (center : ℝ) :
    FEP.ScalarGaussianSemigroup.ScalarOUParameters :=
  FEP.LinearGaussianSemigroup.LinearGaussianParameters.finOneScalarParameters 2
    (by norm_num) center

/-- Both scalar raw parameters are definitionally the preregistered value two. -/
theorem scalarParameters_exact (center : ℝ) :
    (scalarParameters center).rate = 2 ∧
      (scalarParameters center).diffusionVarianceRate = 2 :=
  ⟨rfl, rfl⟩

/-- Restrict the exact Fin4 kernel to the embedded all-ones line and observe
the normalized scalar coordinate. -/
noncomputable def projectedTransition (center : ℝ) (time : ℝ≥0) :
    Kernel ℝ ℝ :=
  Kernel.map
    (Kernel.comap (transition (allOnesEmbedding center) time)
      allOnesEmbedding (by fun_prop))
    allOnesProjection

private theorem allOnes_transitionMean (center : ℝ) (time : ℝ≥0)
    (state : ℝ) :
    (∫ next, allOnesProjection next ∂
      transition (allOnesEmbedding center) time
        (allOnesEmbedding state)) =
      (scalarParameters center).transitionMean time state := by
  rw [transition_apply]
  rw [allOnesProjection.integral_comp_id_comm IsGaussian.integrable_id,
    integral_id_multivariateGaussian]
  have hEvolution :
      Matrix.toEuclideanCLM (𝕜 := ℝ)
          (NormedSpace.exp ((-(time : ℝ)) • K))
          (allOnesEmbedding state - allOnesEmbedding center) =
        (Real.exp (-2 * (time : ℝ)) * (state - center)) •
          normalizedAllOnes := by
    rw [← map_sub allOnesEmbedding]
    change
      Matrix.toEuclideanCLM (𝕜 := ℝ)
          (NormedSpace.exp ((-(time : ℝ)) • K))
          ((state - center) • normalizedAllOnes) = _
    rw [map_smul]
    have hEvolutionState :
        Matrix.toEuclideanCLM (𝕜 := ℝ)
            (NormedSpace.exp ((-(time : ℝ)) • K)) normalizedAllOnes =
          Real.exp (-2 * (time : ℝ)) • normalizedAllOnes := by
      ext axis
      exact congrFun (evolution_normalizedAllOnes time) axis
    rw [hEvolutionState]
    simp only [smul_smul]
    congr 1
    ring
  rw [hEvolution, map_add, allOnesProjection_embedding]
  change
    center +
        allOnesProjection
          (allOnesEmbedding
            (Real.exp (-2 * (time : ℝ)) * (state - center))) = _
  rw [allOnesProjection_embedding]
  simp [scalarParameters,
    FEP.LinearGaussianSemigroup.LinearGaussianParameters.finOneScalarParameters,
    FEP.ScalarGaussianSemigroup.ScalarOUParameters.transitionMean,
    FEP.ScalarGaussianSemigroup.ScalarOUParameters.decay]

private theorem allOnes_transitionCovariance (center : ℝ) (time : ℝ≥0) :
    normalizedAllOnes ⬝ᵥ
        (parameters (allOnesEmbedding center)).transitionCovariance time *ᵥ
          normalizedAllOnes =
      (((scalarParameters center).transitionVariance time : ℝ≥0) : ℝ) := by
  rw [FEP.LinearGaussianSemigroup.LinearGaussianParameters.transitionCovariance]
  change
    normalizedAllOnes ⬝ᵥ
        (Sigma -
          NormedSpace.exp ((-(time : ℝ)) • K) * Sigma *
            (NormedSpace.exp ((-(time : ℝ)) • K))ᵀ) *ᵥ
          normalizedAllOnes = _
  have hTranspose :
      (NormedSpace.exp ((-(time : ℝ)) • K))ᵀ =
        NormedSpace.exp ((-(time : ℝ)) • K) := by
    exact (parameters (allOnesEmbedding center)).evolution_transpose time
  rw [hTranspose, sub_mulVec]
  have hTransport :
      (NormedSpace.exp ((-(time : ℝ)) • K) * Sigma *
          NormedSpace.exp ((-(time : ℝ)) • K)) *ᵥ normalizedAllOnes =
        ((1 / 2 : ℝ) * Real.exp (-2 * (time : ℝ)) ^ 2) •
          normalizedAllOnes := by
    calc
      _ = NormedSpace.exp ((-(time : ℝ)) • K) *ᵥ
          (Sigma *ᵥ
            (NormedSpace.exp ((-(time : ℝ)) • K) *ᵥ
              normalizedAllOnes)) := by
            rw [Matrix.mulVec_mulVec, Matrix.mulVec_mulVec]
      _ = NormedSpace.exp ((-(time : ℝ)) • K) *ᵥ
          (Sigma *ᵥ
            (Real.exp (-2 * (time : ℝ)) • normalizedAllOnes)) := by
            rw [evolution_normalizedAllOnes]
      _ = NormedSpace.exp ((-(time : ℝ)) • K) *ᵥ
          (Real.exp (-2 * (time : ℝ)) •
            (Sigma *ᵥ normalizedAllOnes)) := by
            rw [Matrix.mulVec_smul]
      _ = NormedSpace.exp ((-(time : ℝ)) • K) *ᵥ
          (Real.exp (-2 * (time : ℝ)) •
            ((1 / 2 : ℝ) • normalizedAllOnes)) := by
            rw [Sigma_normalizedAllOnes]
      _ = Real.exp (-2 * (time : ℝ)) •
          ((1 / 2 : ℝ) •
            (NormedSpace.exp ((-(time : ℝ)) • K) *ᵥ
              normalizedAllOnes)) := by
            simp only [Matrix.mulVec_smul, smul_smul]
      _ = _ := by
            rw [evolution_normalizedAllOnes]
            simp only [smul_smul]
            congr 1
            ring
  rw [hTransport, Sigma_normalizedAllOnes, dotProduct_sub,
    dotProduct_smul, dotProduct_smul]
  rw [show normalizedAllOnes ⬝ᵥ normalizedAllOnes = 1 by
    change ∑ _ : Axis, (1 / 2 : ℝ) * (1 / 2 : ℝ) = 1
    rw [sum_axis]
    norm_num]
  simp only [smul_eq_mul, mul_one]
  change
    (1 / 2 : ℝ) -
        (1 / 2 : ℝ) * Real.exp (-2 * (time : ℝ)) ^ 2 =
      (2 / (2 * 2) : ℝ) *
        (1 - Real.exp (-2 * (time : ℝ)) ^ 2)
  ring

private theorem allOnes_transitionVariance (center : ℝ) (time : ℝ≥0)
    (state : ℝ) :
    Var[allOnesProjection;
      transition (allOnesEmbedding center) time
        (allOnesEmbedding state)] =
      (((scalarParameters center).transitionVariance time : ℝ≥0) : ℝ) := by
  rw [transition_apply]
  let mean : StandardizedState :=
    allOnesEmbedding center +
      Matrix.toEuclideanCLM (𝕜 := ℝ)
        (NormedSpace.exp ((-(time : ℝ)) • K))
        (allOnesEmbedding state - allOnesEmbedding center)
  let covariance : Matrix Axis Axis ℝ :=
    Sigma - NormedSpace.exp ((-(time : ℝ)) • K) * Sigma *
      (NormedSpace.exp ((-(time : ℝ)) • K))ᵀ
  change Var[allOnesProjection; multivariateGaussian mean covariance] = _
  calc
    Var[allOnesProjection; multivariateGaussian mean covariance] =
        covarianceBilin (multivariateGaussian mean covariance)
          normalizedAllOnes normalizedAllOnes := by
      symm
      rw [show (allOnesProjection : StandardizedState → ℝ) =
          fun next => ⟪normalizedAllOnes, next⟫ by
        funext next
        rfl]
      exact covarianceBilin_self
        (μ := multivariateGaussian mean covariance)
        IsGaussian.memLp_two_id
        normalizedAllOnes
    _ = normalizedAllOnes ⬝ᵥ covariance *ᵥ normalizedAllOnes := by
      exact covarianceBilin_multivariateGaussian
        ((parameters (allOnesEmbedding center)).transitionCovariance_posSemidef time)
        normalizedAllOnes normalizedAllOnes
    _ = _ := allOnes_transitionCovariance center time

/-- The transported normalized all-ones transition is exactly the accepted
H2.5a scalar OU kernel, with no same-shape surrogate. -/
theorem projectedTransition_eq_scalarOU (center : ℝ) (time : ℝ≥0) :
    projectedTransition center time =
      (scalarParameters center).ouTransition time := by
  apply DFunLike.ext _ _
  intro state
  have hMean := allOnes_transitionMean center time state
  have hVariance := allOnes_transitionVariance center time state
  rw [transition_apply] at hMean hVariance
  rw [projectedTransition, Kernel.map_apply _ (by fun_prop),
    Kernel.comap_apply, transition_apply]
  rw [IsGaussian.map_eq_gaussianReal]
  change
    gaussianReal
        ((multivariateGaussian _ _)[allOnesProjection])
        Var[allOnesProjection; multivariateGaussian _ _].toNNReal =
      gaussianReal
        ((scalarParameters center).transitionMean time state)
        ((scalarParameters center).transitionVariance time)
  rw [hMean, hVariance]
  simp

/-! ## Complete H2.5c export -/

/-- One theorem collecting exactly the proved H2.5c carrier clauses.  It does
not add a certificate field or widen the transition-law claim boundary. -/
theorem exactFin4Carrier :
    Fintype.card Axis = 4 ∧
      (axisFin external = 0 ∧ axisFin sensory = 1 ∧
        axisFin active = 2 ∧ axisFin internal = 3) ∧
      (external ≠ sensory ∧ external ≠ active ∧ external ≠ internal ∧
        sensory ≠ active ∧ sensory ≠ internal ∧ active ≠ internal) ∧
      K.IsSymm ∧ K.PosDef ∧
      K * Sigma = 1 ∧ Sigma * K = 1 ∧ Sigma.IsSymm ∧ Sigma.PosDef ∧
      (Sigma = fun
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
        | internal, internal => 7 / 24) ∧
      K *ᵥ eigenmodeTwo = 2 • eigenmodeTwo ∧
      K *ᵥ eigenmodeFourExternal = 4 • eigenmodeFourExternal ∧
      K *ᵥ eigenmodeFourSensory = 4 • eigenmodeFourSensory ∧
      K *ᵥ eigenmodeSix = 6 • eigenmodeSix ∧
      (eigenmodeTwo ≠ 0 ∧ eigenmodeFourExternal ≠ 0 ∧
        eigenmodeFourSensory ≠ 0 ∧ eigenmodeSix ≠ 0) ∧
      (∀ two fourExternal fourSensory six : ℝ,
        (∀ axis,
          two * eigenmodeTwo axis +
              fourExternal * eigenmodeFourExternal axis +
              fourSensory * eigenmodeFourSensory axis +
              six * eigenmodeSix axis = 0) →
          two = 0 ∧ fourExternal = 0 ∧ fourSensory = 0 ∧ six = 0) ∧
      K external internal = 0 ∧
      Sigma external internal = 1 / 24 ∧ Sigma external internal ≠ 0 ∧
      (∀ (time : ℝ≥0),
        (Sigma -
          NormedSpace.exp ((-(time : ℝ)) • K) * Sigma *
            (NormedSpace.exp ((-(time : ℝ)) • K))ᵀ).PosSemidef) ∧
      (∀ (time : ℝ≥0), 0 < time →
        (Sigma -
          NormedSpace.exp ((-(time : ℝ)) • K) * Sigma *
            (NormedSpace.exp ((-(time : ℝ)) • K))ᵀ).PosDef) ∧
      (∀ center time state,
        transition center time state =
          multivariateGaussian
            (center + Matrix.toEuclideanCLM (𝕜 := ℝ)
              (NormedSpace.exp ((-(time : ℝ)) • K)) (state - center))
            (Sigma -
              NormedSpace.exp ((-(time : ℝ)) • K) * Sigma *
                (NormedSpace.exp ((-(time : ℝ)) • K))ᵀ)) ∧
      (∀ center left right,
        transition center (left + right) =
          transition center right ∘ₖ transition center left) ∧
      (∀ center,
        stationaryLaw center = multivariateGaussian center Sigma) ∧
      (∀ center,
        FEP.MarkovSemigroup.InvariantLaw
          (nativeSemigroup center) (stationaryLaw center)) ∧
      (∀ center state,
        Tendsto (fun time : ℝ≥0 => transitionProbability center time state)
          atTop (nhds (stationaryProbability center))) ∧
      ⟪normalizedAllOnes, normalizedAllOnes⟫ = 1 ∧
      K *ᵥ normalizedAllOnes = 2 • normalizedAllOnes ∧
      Sigma *ᵥ normalizedAllOnes = (1 / 2 : ℝ) • normalizedAllOnes ∧
      (∀ center, (scalarParameters center).rate = 2 ∧
        (scalarParameters center).diffusionVarianceRate = 2) ∧
      (∀ center time,
        projectedTransition center time =
          (scalarParameters center).ouTransition time) := by
  exact ⟨axis_cardinality, axisFin_order, axis_pairwise_ne,
    K_isSymm, K_posDef, K_mul_Sigma, Sigma_mul_K, Sigma_isSymm, Sigma_posDef,
    Sigma_eq_entries, K_eigenmode_two, K_eigenmode_four_external,
    K_eigenmode_four_sensory, K_eigenmode_six, eigenmodes_nonzero,
    eigenmodes_independent, K_external_internal, Sigma_external_internal,
    Sigma_external_internal_ne_zero,
    fun time => transitionCovariance_posSemidef 0 time,
    fun time hTime => transitionCovariance_posDef 0 time hTime,
    transition_apply, transition_add, stationaryLaw_eq_gaussian,
    stationaryLaw_invariant,
    transitionProbability_tendsto_invariant, normalizedAllOnes_unit,
    K_normalizedAllOnes, Sigma_normalizedAllOnes, scalarParameters_exact,
    projectedTransition_eq_scalarOU⟩

end

end FEP.Fin4GaussianSemigroup
