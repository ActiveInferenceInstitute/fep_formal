import FepSketches.finite_markov_dynamics
import FepSketches.active_inference
import FepSketches.decision_risk
import FepSketches.markov_blanket
import Mathlib.Analysis.Normed.Algebra.MatrixExponential

/-!
# Certified finite continuous-time Markov dynamics

The original two-state construction remains as a closed-form regression
instance.  The general layer records a finite rate generator and a certified
Markov semigroup separately: the matrix exponential supplies the algebraic
candidate, while stochasticity remains an explicit proved certificate until
entrywise Metzler positivity is available at the pinned Mathlib revision.
-/

namespace FEP.ContinuousTimeMarkov

open FEP FEP.FiniteInformation Finset
open scoped BigOperators

/-- A finite continuous-time rate matrix: off-diagonal rates are nonnegative
and every row sums to zero.  This is the generator contract only; it does not
claim that its matrix exponential is already a normalized finite kernel. -/
structure FiniteRateGenerator (State : Type*) [Fintype State] where
  rate : State → State → ℝ
  offDiagonal_nonneg : ∀ source target, source ≠ target → 0 ≤ rate source target
  row_sum_zero : ∀ source, ∑ target, rate source target = 0

namespace FiniteRateGenerator

variable {State : Type*} [Fintype State]

instance : CoeFun (FiniteRateGenerator State) (fun _ => State → State → ℝ) :=
  ⟨FiniteRateGenerator.rate⟩

/-- Matrix view of the finite generator. -/
def matrix (generator : FiniteRateGenerator State) : Matrix State State ℝ :=
  generator.rate

/-- Algebraic matrix-exponential candidate for the transition at `time`.
Identity, additivity, and differentiation are available for this candidate;
entrywise stochasticity is not inferred from the pinned matrix API. -/
noncomputable def exponentialCandidate [DecidableEq State]
    (generator : FiniteRateGenerator State) (time : ℝ) : Matrix State State ℝ :=
  NormedSpace.exp (time • generator.matrix)

/-- A law is stationary for a generator when its row-vector master equation
vanishes. -/
def IsStationary (generator : FiniteRateGenerator State)
    (law : FiniteLaw State) : Prop :=
  ∀ target, ∑ source, law source * generator source target = 0

/-- Generator-level detailed balance. -/
def IsDetailedBalanced (generator : FiniteRateGenerator State)
    (law : FiniteLaw State) : Prop :=
  ∀ source target,
    law source * generator source target =
      law target * generator target source

/-- Oriented continuous-time probability current through one edge. -/
def probabilityCurrent (generator : FiniteRateGenerator State)
    (law : FiniteLaw State) (source target : State) : ℝ :=
  law source * generator source target -
    law target * generator target source

/-- Detailed balance cancels every generator-level probability current. -/
theorem probabilityCurrent_eq_zero_of_detailedBalanced
    (generator : FiniteRateGenerator State) (law : FiniteLaw State)
    (hBalanced : generator.IsDetailedBalanced law) (source target : State) :
    generator.probabilityCurrent law source target = 0 := by
  unfold probabilityCurrent
  rw [hBalanced source target, sub_self]

end FiniteRateGenerator

/-- A certified finite Markov semigroup.  The raw transition is defined for
all real times so its derivative is meaningful, while nonnegativity is claimed
only on the mathematically relevant nonnegative half-line. -/
structure FiniteMarkovSemigroup (State : Type*)
    [Fintype State] [DecidableEq State] where
  generator : FiniteRateGenerator State
  transition : ℝ → State → State → ℝ
  transition_nonneg : ∀ {time}, 0 ≤ time → ∀ source target,
    0 ≤ transition time source target
  transition_sum_one : ∀ time source, ∑ target, transition time source target = 1
  transition_zero : ∀ source target,
    transition 0 source target = if source = target then 1 else 0
  transition_add : ∀ left right source target,
    transition (left + right) source target =
      ∑ middle,
        transition left source middle * transition right middle target
  transition_hasDerivAt_left : ∀ time source target,
    HasDerivAt (fun candidate ↦ transition candidate source target)
      (∑ middle,
        generator source middle * transition time middle target) time
  transition_hasDerivAt_right : ∀ time source target,
    HasDerivAt (fun candidate ↦ transition candidate source target)
      (∑ middle,
        transition time source middle * generator middle target) time

namespace FiniteMarkovSemigroup

variable {State : Type*} [Fintype State] [DecidableEq State]

/-- Every certified nonnegative-time slice is the repository's normalized
`FiniteKernel`, not a parallel probability carrier. -/
noncomputable def kernel (semigroup : FiniteMarkovSemigroup State)
    (time : ℝ) (hTime : 0 ≤ time) : FiniteKernel State State where
  mass := semigroup.transition time
  nonneg := semigroup.transition_nonneg hTime
  sum_one := semigroup.transition_sum_one time

@[simp]
theorem kernel_zero (semigroup : FiniteMarkovSemigroup State) :
    semigroup.kernel 0 le_rfl = FiniteKernel.identity := by
  apply FiniteKernel.ext_mass
  funext source target
  simp [kernel, semigroup.transition_zero, FiniteKernel.identity,
    FiniteKernel.deterministic, eq_comm]

/-- Certified Chapman--Kolmogorov additivity on nonnegative times. -/
theorem kernel_add (semigroup : FiniteMarkovSemigroup State)
    (left right : ℝ) (hLeft : 0 ≤ left) (hRight : 0 ≤ right) :
    semigroup.kernel (left + right) (add_nonneg hLeft hRight) =
      FiniteKernel.comp (semigroup.kernel right hRight)
        (semigroup.kernel left hLeft) := by
  apply FiniteKernel.ext_mass
  funext source target
  exact semigroup.transition_add left right source target

/-- Native Mathlib KL cannot increase when both finite laws are pushed through
the same certified nonnegative-time slice. -/
theorem nativeKL_contraction [MeasurableSpace State]
    [DiscreteMeasurableSpace State]
    (semigroup : FiniteMarkovSemigroup State)
    (time : ℝ) (hTime : 0 ≤ time) (actual reference : FiniteLaw State) :
    InformationTheory.klDiv
        (FEP.NativeBlanket.embeddedLaw
          ((semigroup.kernel time hTime).predictive actual))
        (FEP.NativeBlanket.embeddedLaw
          ((semigroup.kernel time hTime).predictive reference)) ≤
      InformationTheory.klDiv
        (FEP.NativeBlanket.embeddedLaw actual)
        (FEP.NativeBlanket.embeddedLaw reference) := by
  rw [FEP.NativeBlanket.embeddedPredictive_eq_comp,
    FEP.NativeBlanket.embeddedPredictive_eq_comp]
  exact InformationTheory.klDiv_comp_right_le
    (FEP.NativeBlanket.embeddedLaw actual)
    (FEP.NativeBlanket.embeddedLaw reference)
    (FEP.NativeBlanket.embeddedKernel (semigroup.kernel time hTime))

/-- If the reference law is invariant under the selected slice, native KL to
that fixed reference cannot increase. -/
theorem nativeKL_contraction_to_invariant [MeasurableSpace State]
    [DiscreteMeasurableSpace State]
    (semigroup : FiniteMarkovSemigroup State)
    (time : ℝ) (hTime : 0 ≤ time) (actual invariant : FiniteLaw State)
    (hInvariant : FEP.FiniteMarkovDynamics.IsInvariant invariant
      (semigroup.kernel time hTime)) :
    InformationTheory.klDiv
        (FEP.NativeBlanket.embeddedLaw
          ((semigroup.kernel time hTime).predictive actual))
        (FEP.NativeBlanket.embeddedLaw invariant) ≤
      InformationTheory.klDiv
        (FEP.NativeBlanket.embeddedLaw actual)
        (FEP.NativeBlanket.embeddedLaw invariant) := by
  have hDPI := semigroup.nativeKL_contraction time hTime actual invariant
  unfold FEP.FiniteMarkovDynamics.IsInvariant at hInvariant
  rw [hInvariant] at hDPI
  exact hDPI

/-- A law is stationary for every nonnegative slice of the semigroup. -/
def IsStationary (semigroup : FiniteMarkovSemigroup State)
    (law : FiniteLaw State) : Prop :=
  ∀ time hTime,
    FEP.FiniteMarkovDynamics.IsInvariant law (semigroup.kernel time hTime)

/-- A law satisfies detailed balance for every nonnegative slice. -/
def IsDetailedBalanced (semigroup : FiniteMarkovSemigroup State)
    (law : FiniteLaw State) : Prop :=
  ∀ time hTime,
    FEP.FiniteMarkovDynamics.IsReversible law (semigroup.kernel time hTime)

end FiniteMarkovSemigroup

/-- A finite action selects both a certified Markov semigroup and the
nonnegative duration at which that semigroup is sampled. -/
structure ActionIndexedSemigroup (State Action : Type*)
    [Fintype State] [DecidableEq State] [Fintype Action] where
  semigroup : Action → FiniteMarkovSemigroup State
  sampleTime : Action → ℝ
  sampleTime_nonneg : ∀ action, 0 ≤ sampleTime action

namespace ActionIndexedSemigroup

variable {Policy State Outcome Action : Type*}
  [Fintype Policy] [Fintype State] [Fintype Outcome] [Fintype Action]
  [DecidableEq State]

/-- The exact normalized kernel obtained by sampling the semigroup selected by
an action at that action's certified nonnegative duration. -/
noncomputable def sampledKernel
    (indexed : ActionIndexedSemigroup State Action) (action : Action) :
    FiniteKernel State State :=
  (indexed.semigroup action).kernel (indexed.sampleTime action)
    (indexed.sampleTime_nonneg action)

/-- Build a generative model whose policy transition is definitionally the
kernel sampled by the action emitted from that policy. -/
noncomputable def toGenerativeModel
    (indexed : ActionIndexedSemigroup State Action)
    (policyToAction : Policy → Action)
    (initialState : FiniteLaw State)
    (likelihood : FiniteKernel State Outcome)
    (preferences : FiniteLaw Outcome) (policyPrior : FiniteLaw Policy) :
    FEP.ActiveInference.GenerativeModel Policy State Outcome where
  initialState := initialState
  transition policy := indexed.sampledKernel (policyToAction policy)
  likelihood := likelihood
  preferences := preferences
  policyPrior := policyPrior

/-- The generated model exposes the sampled action kernel without a second
transition declaration. -/
@[simp]
theorem toGenerativeModel_transition
    (indexed : ActionIndexedSemigroup State Action)
    (policyToAction : Policy → Action)
    (initialState : FiniteLaw State)
    (likelihood : FiniteKernel State Outcome)
    (preferences : FiniteLaw Outcome) (policyPrior : FiniteLaw Policy)
    (policy : Policy) :
    (indexed.toGenerativeModel policyToAction initialState likelihood
        preferences policyPrior).transition policy =
      indexed.sampledKernel (policyToAction policy) :=
  rfl

/-- Expose the sampled action family through the repository's canonical active
inference interface.  The caller supplies the single consistency proof tying
each policy transition to the action it emits. -/
noncomputable def toActionInterface
    (indexed : ActionIndexedSemigroup State Action)
    (model : FEP.ActiveInference.GenerativeModel Policy State Outcome)
    (policyToAction : Policy → Action)
    (transition_consistent : ∀ policy,
      indexed.sampledKernel (policyToAction policy) = model.transition policy) :
    FEP.ActiveInference.ActionInterface model Action where
  policyToAction := policyToAction
  actionTransition := indexed.sampledKernel
  transition_consistent := transition_consistent

/-- The model constructed from an indexed semigroup carries its canonical
action interface with transition consistency discharged definitionally. -/
noncomputable def toGenerativeModelActionInterface
    (indexed : ActionIndexedSemigroup State Action)
    (policyToAction : Policy → Action)
    (initialState : FiniteLaw State)
    (likelihood : FiniteKernel State Outcome)
    (preferences : FiniteLaw Outcome) (policyPrior : FiniteLaw Policy) :
    FEP.ActiveInference.ActionInterface
      (indexed.toGenerativeModel policyToAction initialState likelihood
        preferences policyPrior) Action :=
  indexed.toActionInterface
    (indexed.toGenerativeModel policyToAction initialState likelihood
      preferences policyPrior)
    policyToAction (fun _ => rfl)

/-- Selecting a policy action and executing it uses exactly the sampled
semigroup kernel; no second action-transition carrier is introduced. -/
theorem selectedActionTransition_eq_sampledSemigroup
    (indexed : ActionIndexedSemigroup State Action)
    (model : FEP.ActiveInference.GenerativeModel Policy State Outcome)
    (policyToAction : Policy → Action)
    (transition_consistent : ∀ policy,
      indexed.sampledKernel (policyToAction policy) = model.transition policy)
    (policy : Policy) :
    (indexed.toActionInterface model policyToAction
        transition_consistent).actionTransition
        ((indexed.toActionInterface model policyToAction
          transition_consistent).policyToAction policy) =
      indexed.sampledKernel (policyToAction policy) :=
  rfl

end ActionIndexedSemigroup

/-! ## A three-state nonequilibrium steady cycle -/

/-- Unit-rate directed cycle `0 → 1 → 2 → 0`.  Its rows sum to zero,
but every reverse edge rate vanishes. -/
def threeCycleGenerator : FiniteRateGenerator (Fin 3) where
  rate := ![![-1, 1, 0], ![0, -1, 1], ![1, 0, -1]]
  offDiagonal_nonneg := by
    intro source target hDistinct
    fin_cases source <;> fin_cases target <;> simp_all
  row_sum_zero := by
    intro source
    fin_cases source <;> norm_num [Fin.sum_univ_succ]

/-- The uniform law is stationary for the directed three-cycle. -/
noncomputable def threeCycleStationaryLaw : FiniteLaw (Fin 3) :=
  FiniteLaw.uniform

theorem threeCycle_stationary :
    threeCycleGenerator.IsStationary threeCycleStationaryLaw := by
  intro target
  fin_cases target <;>
    norm_num [FiniteRateGenerator.IsStationary, threeCycleGenerator,
      threeCycleStationaryLaw, FiniteLaw.uniform, Fin.sum_univ_succ]

theorem threeCycle_not_detailedBalanced :
    ¬threeCycleGenerator.IsDetailedBalanced threeCycleStationaryLaw := by
  intro hBalanced
  have hForward := hBalanced (0 : Fin 3) (1 : Fin 3)
  norm_num [FiniteRateGenerator.IsDetailedBalanced, threeCycleGenerator,
    threeCycleStationaryLaw, FiniteLaw.uniform] at hForward

theorem threeCycle_current_zero_one :
    threeCycleGenerator.probabilityCurrent threeCycleStationaryLaw
        (0 : Fin 3) (1 : Fin 3) = 1 / 3 := by
  norm_num [FiniteRateGenerator.probabilityCurrent, threeCycleGenerator,
    threeCycleStationaryLaw, FiniteLaw.uniform]

theorem threeCycle_current_zero_one_ne_zero :
    threeCycleGenerator.probabilityCurrent threeCycleStationaryLaw
        (0 : Fin 3) (1 : Fin 3) ≠ 0 := by
  rw [threeCycle_current_zero_one]
  norm_num

/-! ## Positive refresh semigroups on exact blanket state spaces -/

variable {State : Type*} [Fintype State] [Nonempty State] [DecidableEq State]

/-- Mass of one atom under the uniform finite law. -/
noncomputable def refreshUniformMass : ℝ :=
  (Fintype.card State : ℝ)⁻¹

/-- Kronecker delta written as a real-valued transition entry. -/
def refreshDelta (source target : State) : ℝ :=
  if source = target then 1 else 0

omit [Nonempty State] in
@[simp]
private theorem sum_refreshDelta (source : State) :
    ∑ target, refreshDelta source target = 1 := by
  classical
  simp [refreshDelta]

omit [DecidableEq State] in
@[simp]
private theorem sum_refreshUniformMass :
    ∑ _ : State, refreshUniformMass (State := State) = 1 := by
  simp [refreshUniformMass, Fintype.card_ne_zero]

omit [Nonempty State] in
@[simp]
private theorem sum_refreshDelta_right (target : State) :
    ∑ source, refreshDelta source target = 1 := by
  classical
  simp [refreshDelta]

omit [Nonempty State] in
@[simp]
private theorem sum_refreshDelta_mul_delta (source target : State) :
    ∑ middle,
      refreshDelta source middle * refreshDelta middle target =
        refreshDelta source target := by
  classical
  simp [refreshDelta]

omit [Nonempty State] in
@[simp]
private theorem sum_refreshDelta_mul_uniform (source : State) :
    ∑ middle,
      refreshDelta source middle * refreshUniformMass (State := State) =
        refreshUniformMass (State := State) := by
  rw [← Finset.sum_mul, sum_refreshDelta, one_mul]

omit [Nonempty State] in
@[simp]
private theorem sum_refreshUniform_mul_delta (target : State) :
    ∑ middle,
      refreshUniformMass (State := State) * refreshDelta middle target =
        refreshUniformMass (State := State) := by
  rw [← Finset.mul_sum, sum_refreshDelta_right, mul_one]

omit [DecidableEq State] in
@[simp]
private theorem sum_refreshUniform_mul_uniform :
    ∑ _ : State,
      refreshUniformMass (State := State) *
        refreshUniformMass (State := State) =
      refreshUniformMass (State := State) := by
  rw [← Finset.mul_sum, sum_refreshUniformMass, mul_one]

omit [DecidableEq State] in
private theorem refreshUniformMass_pos :
    0 < refreshUniformMass (State := State) := by
  unfold refreshUniformMass
  positivity

/-- Unit-rate generator `U - I`, where every row of `U` is uniform. -/
noncomputable def refreshRateGenerator : FiniteRateGenerator State where
  rate source target :=
    refreshUniformMass (State := State) - refreshDelta source target
  offDiagonal_nonneg := by
    intro source target hDistinct
    simp [refreshDelta, hDistinct,
      (refreshUniformMass_pos (State := State)).le]
  row_sum_zero := by
    intro source
    rw [Finset.sum_sub_distrib, sum_refreshUniformMass,
      sum_refreshDelta, sub_self]

/-- Exponential survival weight for unit-rate refresh. -/
noncomputable def refreshRho (time : ℝ) : ℝ :=
  Real.exp (-time)

private theorem refreshRho_pos (time : ℝ) : 0 < refreshRho time :=
  Real.exp_pos _

private theorem refreshRho_le_one {time : ℝ} (hTime : 0 ≤ time) :
    refreshRho time ≤ 1 := by
  rw [refreshRho, Real.exp_le_one_iff]
  linarith

@[simp]
private theorem refreshRho_zero : refreshRho 0 = 1 := by
  simp [refreshRho]

private theorem refreshRho_add (left right : ℝ) :
    refreshRho (left + right) = refreshRho left * refreshRho right := by
  rw [refreshRho, refreshRho, refreshRho, ← Real.exp_add]
  congr 1
  ring

/-- Refresh transition `exp(-t) I + (1-exp(-t)) U`. -/
noncomputable def refreshTransition (time : ℝ)
    (source target : State) : ℝ :=
  refreshRho time * refreshDelta source target +
    (1 - refreshRho time) * refreshUniformMass (State := State)

theorem refreshTransition_nonneg {time : ℝ} (hTime : 0 ≤ time)
    (source target : State) : 0 ≤ refreshTransition time source target := by
  have hRho : 0 ≤ refreshRho time := (refreshRho_pos time).le
  have hOneSub : 0 ≤ 1 - refreshRho time :=
    sub_nonneg.mpr (refreshRho_le_one hTime)
  have hUniform : 0 ≤ refreshUniformMass (State := State) :=
    (refreshUniformMass_pos (State := State)).le
  have hDelta : 0 ≤ refreshDelta source target := by
    unfold refreshDelta
    split <;> norm_num
  exact add_nonneg (mul_nonneg hRho hDelta) (mul_nonneg hOneSub hUniform)

/-- Every entry is strictly positive at every strictly positive time. -/
theorem refreshTransition_pos {time : ℝ} (hTime : 0 < time)
    (source target : State) : 0 < refreshTransition time source target := by
  have hRho : 0 < refreshRho time := refreshRho_pos time
  have hOneSub : 0 < 1 - refreshRho time := by
    rw [sub_pos, refreshRho, Real.exp_lt_one_iff]
    linarith
  have hUniform : 0 < refreshUniformMass (State := State) :=
    refreshUniformMass_pos (State := State)
  by_cases h : source = target
  · simp only [refreshTransition, refreshDelta, h, ite_true]
    positivity
  · simp only [refreshTransition, refreshDelta, h, ite_false, mul_zero,
      zero_add]
    positivity

theorem refreshTransition_sum_one (time : ℝ) (source : State) :
    ∑ target, refreshTransition time source target = 1 := by
  change ∑ target,
      (refreshRho time * refreshDelta source target +
      (1 - refreshRho time) * refreshUniformMass (State := State)) = 1
  rw [Finset.sum_add_distrib, ← Finset.mul_sum, ← Finset.mul_sum,
    sum_refreshDelta, sum_refreshUniformMass]
  ring

omit [Nonempty State] in
theorem refreshTransition_zero (source target : State) :
    refreshTransition 0 source target =
      if source = target then 1 else 0 := by
  simp [refreshTransition, refreshDelta]

/-- Chapman--Kolmogorov for the refresh transition. -/
theorem refreshTransition_add (left right : ℝ) (source target : State) :
    refreshTransition (left + right) source target =
      ∑ middle,
        refreshTransition left source middle *
          refreshTransition right middle target := by
  simp only [refreshTransition, refreshRho_add]
  symm
  calc
    (∑ middle,
        (refreshRho left * refreshDelta source middle +
            (1 - refreshRho left) * refreshUniformMass (State := State)) *
          (refreshRho right * refreshDelta middle target +
            (1 - refreshRho right) * refreshUniformMass (State := State))) =
        ∑ middle,
          ((refreshRho left * refreshRho right) *
              (refreshDelta source middle * refreshDelta middle target) +
            (refreshRho left * (1 - refreshRho right)) *
              (refreshDelta source middle *
                refreshUniformMass (State := State)) +
            ((1 - refreshRho left) * refreshRho right) *
              (refreshUniformMass (State := State) *
                refreshDelta middle target) +
            ((1 - refreshRho left) * (1 - refreshRho right)) *
              (refreshUniformMass (State := State) *
                refreshUniformMass (State := State))) := by
          apply Finset.sum_congr rfl
          intro middle _
          ring
    _ = (refreshRho left * refreshRho right) *
          refreshDelta source target +
        (refreshRho left * (1 - refreshRho right)) *
          refreshUniformMass (State := State) +
        ((1 - refreshRho left) * refreshRho right) *
          refreshUniformMass (State := State) +
        ((1 - refreshRho left) * (1 - refreshRho right)) *
          refreshUniformMass (State := State) := by
      simp only [Finset.sum_add_distrib, ← Finset.mul_sum,
        sum_refreshDelta_mul_delta, sum_refreshDelta_mul_uniform,
        sum_refreshDelta_right, sum_refreshUniformMass, mul_one]
    _ = refreshRho left * refreshRho right * refreshDelta source target +
        (1 - refreshRho left * refreshRho right) *
          refreshUniformMass (State := State) := by
      ring

/-- Entrywise derivative of the refresh transition. -/
noncomputable def refreshTransitionDerivative (time : ℝ)
    (source target : State) : ℝ :=
  refreshRho time *
    (refreshUniformMass (State := State) - refreshDelta source target)

private theorem refreshRho_hasDerivAt (time : ℝ) :
    HasDerivAt refreshRho (-refreshRho time) time := by
  change HasDerivAt (fun candidate ↦ Real.exp (-candidate))
    (-Real.exp (-time)) time
  simpa using ((hasDerivAt_id time).neg.exp)

omit [Nonempty State] in
theorem refreshTransition_hasDerivAt (time : ℝ)
    (source target : State) :
    HasDerivAt (fun candidate ↦ refreshTransition candidate source target)
      (refreshTransitionDerivative time source target) time := by
  have hRho := refreshRho_hasDerivAt time
  unfold refreshTransition
  apply ((hRho.mul_const (refreshDelta source target)).add
    (((hasDerivAt_const time 1).sub hRho).mul_const
      (refreshUniformMass (State := State)))).congr_deriv
  unfold refreshTransitionDerivative
  ring

theorem refreshGenerator_mul_transition (time : ℝ)
    (source target : State) :
    (∑ middle,
      refreshRateGenerator source middle *
        refreshTransition time middle target) =
      refreshTransitionDerivative time source target := by
  change (∑ middle,
      (refreshUniformMass (State := State) - refreshDelta source middle) *
        (refreshRho time * refreshDelta middle target +
          (1 - refreshRho time) * refreshUniformMass (State := State))) = _
  calc
    _ = ∑ middle,
        (refreshRho time *
            (refreshUniformMass (State := State) *
              refreshDelta middle target) +
          (1 - refreshRho time) *
            (refreshUniformMass (State := State) *
              refreshUniformMass (State := State)) -
          refreshRho time *
            (refreshDelta source middle * refreshDelta middle target) -
          (1 - refreshRho time) *
            (refreshDelta source middle *
              refreshUniformMass (State := State))) := by
        apply Finset.sum_congr rfl
        intro middle _
        ring
    _ = refreshRho time * refreshUniformMass (State := State) +
        (1 - refreshRho time) * refreshUniformMass (State := State) -
        refreshRho time * refreshDelta source target -
        (1 - refreshRho time) * refreshUniformMass (State := State) := by
      simp only [Finset.sum_sub_distrib, Finset.sum_add_distrib,
        ← Finset.mul_sum, sum_refreshDelta_right,
        sum_refreshUniformMass, sum_refreshDelta_mul_delta,
        sum_refreshDelta_mul_uniform, mul_one]
    _ = refreshTransitionDerivative time source target := by
      rw [refreshTransitionDerivative]
      ring

theorem refreshTransition_mul_generator (time : ℝ)
    (source target : State) :
    (∑ middle,
      refreshTransition time source middle *
        refreshRateGenerator middle target) =
      refreshTransitionDerivative time source target := by
  change (∑ middle,
      (refreshRho time * refreshDelta source middle +
        (1 - refreshRho time) * refreshUniformMass (State := State)) *
      (refreshUniformMass (State := State) - refreshDelta middle target)) = _
  calc
    _ = ∑ middle,
        (refreshRho time *
            (refreshDelta source middle *
              refreshUniformMass (State := State)) -
          refreshRho time *
            (refreshDelta source middle * refreshDelta middle target) +
          (1 - refreshRho time) *
            (refreshUniformMass (State := State) *
              refreshUniformMass (State := State)) -
          (1 - refreshRho time) *
            (refreshUniformMass (State := State) *
              refreshDelta middle target)) := by
        apply Finset.sum_congr rfl
        intro middle _
        ring
    _ = refreshRho time * refreshUniformMass (State := State) -
        refreshRho time * refreshDelta source target +
        (1 - refreshRho time) * refreshUniformMass (State := State) -
        (1 - refreshRho time) * refreshUniformMass (State := State) := by
      simp only [Finset.sum_sub_distrib, Finset.sum_add_distrib,
        ← Finset.mul_sum, sum_refreshDelta_mul_uniform,
        sum_refreshDelta_mul_delta, sum_refreshUniformMass,
        sum_refreshDelta_right, mul_one]
    _ = refreshTransitionDerivative time source target := by
      rw [refreshTransitionDerivative]
      ring

/-- Fully certified positive refresh semigroup on an arbitrary nonempty finite
state space. -/
noncomputable def refreshSemigroup : FiniteMarkovSemigroup State where
  generator := refreshRateGenerator
  transition := refreshTransition
  transition_nonneg := refreshTransition_nonneg
  transition_sum_one := refreshTransition_sum_one
  transition_zero := refreshTransition_zero
  transition_add := refreshTransition_add
  transition_hasDerivAt_left := fun time source target ↦
    (refreshTransition_hasDerivAt time source target).congr_deriv
      (refreshGenerator_mul_transition time source target).symm
  transition_hasDerivAt_right := fun time source target ↦
    (refreshTransition_hasDerivAt time source target).congr_deriv
      (refreshTransition_mul_generator time source target).symm

/-- Prediction through refresh is the exact convex mixture of the input law
and the uniform stationary law. -/
theorem refreshSemigroup_predictive_mass (law : FiniteLaw State)
    {time : ℝ} (hTime : 0 ≤ time) (target : State) :
    (refreshSemigroup.kernel time hTime).predictive law target =
      refreshRho time * law target +
        (1 - refreshRho time) *
          (FiniteLaw.uniform : FiniteLaw State) target := by
  rw [FiniteKernel.predictive_mass]
  change
    (∑ source, law source *
      (refreshRho time * refreshDelta source target +
        (1 - refreshRho time) * refreshUniformMass (State := State))) = _
  calc
    _ = ∑ source,
        (refreshRho time * (law source * refreshDelta source target) +
          ((1 - refreshRho time) * refreshUniformMass (State := State)) *
            law source) := by
      apply Finset.sum_congr rfl
      intro source _
      ring
    _ = refreshRho time *
          (∑ source, law source * refreshDelta source target) +
        ((1 - refreshRho time) * refreshUniformMass (State := State)) *
          ∑ source, law source := by
      rw [Finset.sum_add_distrib, Finset.mul_sum, Finset.mul_sum]
    _ = refreshRho time * law target +
        (1 - refreshRho time) *
          (FiniteLaw.uniform : FiniteLaw State) target := by
      classical
      simp [refreshDelta, law.sum_one, refreshUniformMass, FiniteLaw.uniform]

/-- Uniform mass is stationary for the refresh transition at every time. -/
private theorem refreshTransition_uniform_stationary
    (time : ℝ) (target : State) :
    (∑ source,
      (FiniteLaw.uniform : FiniteLaw State) source *
        refreshTransition time source target) =
      (FiniteLaw.uniform : FiniteLaw State) target := by
  change (∑ source,
      refreshUniformMass (State := State) *
        (refreshRho time * refreshDelta source target +
          (1 - refreshRho time) * refreshUniformMass (State := State))) =
    refreshUniformMass (State := State)
  calc
    _ = ∑ source,
        (refreshRho time *
          (refreshUniformMass (State := State) * refreshDelta source target) +
        (1 - refreshRho time) *
          (refreshUniformMass (State := State) *
            refreshUniformMass (State := State))) := by
          apply Finset.sum_congr rfl
          intro source _
          ring
    _ = refreshRho time *
          (∑ source,
            refreshUniformMass (State := State) * refreshDelta source target) +
        (1 - refreshRho time) *
          (∑ _ : State,
            refreshUniformMass (State := State) *
              refreshUniformMass (State := State)) := by
          rw [Finset.sum_add_distrib, Finset.mul_sum, Finset.mul_sum]
    _ = refreshUniformMass (State := State) := by
      rw [sum_refreshUniform_mul_delta, sum_refreshUniform_mul_uniform]
      ring

/-- The uniform law is invariant under every certified refresh slice. -/
theorem refreshSemigroup_uniform_stationary :
    refreshSemigroup.IsStationary (FiniteLaw.uniform : FiniteLaw State) := by
  intro time hTime
  unfold FEP.FiniteMarkovDynamics.IsInvariant
  apply FiniteLaw.ext_mass
  funext target
  change (∑ source,
      (FiniteLaw.uniform : FiniteLaw State) source *
        refreshTransition time source target) =
    (FiniteLaw.uniform : FiniteLaw State) target
  exact refreshTransition_uniform_stationary time target

omit [Nonempty State] in
/-- A point mass predicted through a finite kernel selects exactly the chosen
row. -/
private theorem predictive_pointMass_mass (kernel : FiniteKernel State State)
    (chosen target : State) :
    kernel.predictive (FiniteLaw.pointMass chosen) target =
      kernel chosen target := by
  classical
  simp [FiniteKernel.predictive_mass, FiniteLaw.pointMass]

omit [DecidableEq State] in
/-- Cross-entropy against a uniform finite reference is independent of the
actual normalized law. -/
private theorem crossEntropy_uniform (law : FiniteLaw State) :
    crossEntropy law (FiniteLaw.uniform : FiniteLaw State) =
      Real.log (Fintype.card State : ℝ) := by
  rw [crossEntropy]
  simp only [FiniteLaw.uniform]
  rw [Real.log_inv]
  calc
    (∑ state, -law state * -Real.log (Fintype.card State : ℝ)) =
        ∑ state, law state * Real.log (Fintype.card State : ℝ) := by
          apply Finset.sum_congr rfl
          intro state _
          ring
    _ = (∑ state, law state) *
        Real.log (Fintype.card State : ℝ) := by
          rw [Finset.sum_mul]
    _ = Real.log (Fintype.card State : ℝ) := by
      rw [law.sum_one, one_mul]

/-- Every strictly positive refresh slice strictly decreases finite KL to the
uniform stationary law unless the input law is already uniform. -/
theorem refreshSemigroup_finiteKL_strict_decrease_of_ne_uniform
    (law : FiniteLaw State) {time : ℝ} (hTime : 0 < time)
    (hLaw : law ≠ (FiniteLaw.uniform : FiniteLaw State)) :
    finiteKL
        ((refreshSemigroup.kernel time hTime.le).predictive law)
        (FiniteLaw.uniform : FiniteLaw State) <
      finiteKL law (FiniteLaw.uniform : FiniteLaw State) := by
  classical
  let uniformLaw : FiniteLaw State := FiniteLaw.uniform
  let evolved : FiniteLaw State :=
    (refreshSemigroup.kernel time hTime.le).predictive law
  change finiteKL evolved uniformLaw < finiteKL law uniformLaw
  have hUniformPos (state : State) : 0 < uniformLaw state := by
    simpa [uniformLaw, FiniteLaw.uniform, refreshUniformMass] using
      (refreshUniformMass_pos (State := State))
  have hLawUniform : law ≠ uniformLaw := by
    simpa [uniformLaw] using hLaw
  have hKLNe : finiteKL law uniformLaw ≠ 0 := by
    intro hZero
    apply hLawUniform
    exact (finiteKL_eq_zero_iff law uniformLaw).mp hZero
  have hKLPos : 0 < finiteKL law uniformLaw :=
    lt_of_le_of_ne (finiteKL_nonneg law uniformLaw) (Ne.symm hKLNe)
  have hUniformEntropy :
      entropy uniformLaw = Real.log (Fintype.card State : ℝ) := by
    have hSelf := finiteKL_self uniformLaw
    rw [finiteKL_eq_crossEntropy_sub_entropy uniformLaw uniformLaw hUniformPos,
      crossEntropy_uniform] at hSelf
    linarith
  have hEntropyLt : entropy law < entropy uniformLaw := by
    rw [finiteKL_eq_crossEntropy_sub_entropy law uniformLaw hUniformPos,
      crossEntropy_uniform] at hKLPos
    rw [hUniformEntropy]
    linarith
  have hRhoPos : 0 < refreshRho time := refreshRho_pos time
  have hRhoLt : refreshRho time < 1 := by
    rw [refreshRho, Real.exp_lt_one_iff]
    linarith
  have hComplementPos : 0 < 1 - refreshRho time := sub_pos.mpr hRhoLt
  have hEvolvedMass (state : State) :
      evolved state =
        refreshRho time * law state +
          (1 - refreshRho time) * uniformLaw state := by
    simpa [evolved, uniformLaw] using
      refreshSemigroup_predictive_mass law hTime.le state
  have hWitness : ∃ state, law state ≠ uniformLaw state := by
    by_contra hNoWitness
    apply hLawUniform
    apply FiniteLaw.ext_mass
    funext state
    by_contra hDifferent
    exact hNoWitness ⟨state, hDifferent⟩
  obtain ⟨witness, hWitness⟩ := hWitness
  have hTermLe (state : State) :
      refreshRho time * Real.negMulLog (law state) +
          (1 - refreshRho time) * Real.negMulLog (uniformLaw state) ≤
        Real.negMulLog (evolved state) := by
    rw [hEvolvedMass]
    simpa only [smul_eq_mul] using
      Real.concaveOn_negMulLog.2
        (law.nonneg state) (uniformLaw.nonneg state)
        hRhoPos.le hComplementPos.le (by ring)
  have hTermLt :
      refreshRho time * Real.negMulLog (law witness) +
          (1 - refreshRho time) * Real.negMulLog (uniformLaw witness) <
        Real.negMulLog (evolved witness) := by
    rw [hEvolvedMass]
    simpa only [smul_eq_mul] using
      Real.strictConcaveOn_negMulLog.2
        (law.nonneg witness) (uniformLaw.nonneg witness) hWitness
        hRhoPos hComplementPos (by ring)
  have hWeightedEntropyLt :
      refreshRho time * entropy law +
          (1 - refreshRho time) * entropy uniformLaw <
        entropy evolved := by
    simp only [entropy, Finset.mul_sum, ← Finset.sum_add_distrib]
    exact Finset.sum_lt_sum (fun state _ => hTermLe state)
      ⟨witness, Finset.mem_univ witness, hTermLt⟩
  have hWeightedEntropyAbove :
      entropy law <
        refreshRho time * entropy law +
          (1 - refreshRho time) * entropy uniformLaw := by
    have hGap : 0 < entropy uniformLaw - entropy law := sub_pos.mpr hEntropyLt
    have hWeightedGap :
        0 < (1 - refreshRho time) *
          (entropy uniformLaw - entropy law) :=
      mul_pos hComplementPos hGap
    nlinarith
  have hEntropyIncrease : entropy law < entropy evolved :=
    hWeightedEntropyAbove.trans hWeightedEntropyLt
  rw [finiteKL_eq_crossEntropy_sub_entropy evolved uniformLaw hUniformPos,
    finiteKL_eq_crossEntropy_sub_entropy law uniformLaw hUniformPos,
    crossEntropy_uniform, crossEntropy_uniform]
  linarith

/-- The same generic strict refresh decrease on Mathlib's native
extended-real KL surface. -/
theorem refreshSemigroup_nativeKL_strict_decrease_of_ne_uniform
    [MeasurableSpace State] [DiscreteMeasurableSpace State]
    (law : FiniteLaw State) {time : ℝ} (hTime : 0 < time)
    (hLaw : law ≠ (FiniteLaw.uniform : FiniteLaw State)) :
    InformationTheory.klDiv
        (FEP.NativeBlanket.embeddedLaw
          ((refreshSemigroup.kernel time hTime.le).predictive law))
        (FEP.NativeBlanket.embeddedLaw
          (FiniteLaw.uniform : FiniteLaw State)) <
      InformationTheory.klDiv
        (FEP.NativeBlanket.embeddedLaw law)
        (FEP.NativeBlanket.embeddedLaw
          (FiniteLaw.uniform : FiniteLaw State)) := by
  have hUniformPos : ∀ state,
      0 < (FiniteLaw.uniform : FiniteLaw State) state := by
    intro state
    simpa [FiniteLaw.uniform, refreshUniformMass] using
      (refreshUniformMass_pos (State := State))
  rw [FEP.DecisionRisk.weightedDirac_klDiv_eq_finiteKL_of_fullSupport
      ((refreshSemigroup.kernel time hTime.le).predictive law)
      (FiniteLaw.uniform : FiniteLaw State) hUniformPos,
    FEP.DecisionRisk.weightedDirac_klDiv_eq_finiteKL_of_fullSupport
      law (FiniteLaw.uniform : FiniteLaw State) hUniformPos]
  exact (ENNReal.ofReal_lt_ofReal_iff_of_nonneg
    (finiteKL_nonneg
      ((refreshSemigroup.kernel time hTime.le).predictive law)
      (FiniteLaw.uniform : FiniteLaw State))).2
        (refreshSemigroup_finiteKL_strict_decrease_of_ne_uniform
          law hTime hLaw)

omit [Nonempty State] in
/-- A finite point mass has zero Shannon entropy. -/
private theorem entropy_pointMass (chosen : State) :
    entropy (FiniteLaw.pointMass chosen) = 0 := by
  classical
  rw [entropy]
  apply Finset.sum_eq_zero
  intro state _
  by_cases hState : state = chosen <;>
    simp [FiniteLaw.pointMass, hState]

variable {Internal Sensory Active External : Type*}
  [Fintype Internal] [Fintype Sensory] [Fintype Active] [Fintype External]
  [DecidableEq Internal] [DecidableEq Sensory] [DecidableEq Active]
  [DecidableEq External]
  [Nontrivial Internal] [Nontrivial Sensory]
  [Nontrivial Active] [Nontrivial External]

/-- The generic refresh certificate instantiated on the repository's exact
right-associated dynamic Markov-blanket carrier. -/
noncomputable def blanketRefreshSemigroup :
    FiniteMarkovSemigroup
      (FEP.MarkovBlanket.DynamicState Internal Sensory Active External) :=
  refreshSemigroup

theorem blanketRefreshSemigroup_transition_pos
    {time : ℝ} (hTime : 0 < time)
    (source target :
      FEP.MarkovBlanket.DynamicState Internal Sensory Active External) :
    0 < blanketRefreshSemigroup.transition time source target :=
  refreshTransition_pos hTime source target

/-- A point mass on any exact blanket state differs from the uniform law;
nontriviality of every factor makes the product carrier nontrivial. -/
theorem blanketPointMass_ne_uniform
    (chosen : FEP.MarkovBlanket.DynamicState
      Internal Sensory Active External) :
    FiniteLaw.pointMass chosen ≠
      (FiniteLaw.uniform : FiniteLaw
        (FEP.MarkovBlanket.DynamicState Internal Sensory Active External)) := by
  obtain ⟨other, hOther⟩ := exists_ne chosen
  intro hEqual
  have hMass := congrArg
    (fun law : FiniteLaw
      (FEP.MarkovBlanket.DynamicState Internal Sensory Active External) ↦
        law other) hEqual
  have hUniformPos :
      0 < (Fintype.card
        (FEP.MarkovBlanket.DynamicState Internal Sensory Active External) : ℝ)⁻¹ := by
    positivity
  simp [FiniteLaw.pointMass, FiniteLaw.uniform, hOther] at hMass

/-- The exact right-associated Boolean blanket carrier has sixteen states. -/
abbrev BoolBlanketState :=
  FEP.MarkovBlanket.DynamicState Bool Bool Bool Bool

theorem boolBlanketState_card :
    Fintype.card BoolBlanketState = 16 := by
  norm_num [BoolBlanketState, FEP.MarkovBlanket.DynamicState]

/-- Embed an internal Boolean belief as the first blanket factor while leaving
the sensory-active-external complement uniform. -/
noncomputable def liftInternalLaw (internal : FiniteLaw Bool) :
    FiniteLaw BoolBlanketState :=
  internal.product
    (FiniteLaw.uniform : FiniteLaw (Bool × (Bool × Bool)))

/-- The embedding preserves the internal law as its exact first marginal. -/
theorem liftInternalLaw_fstMarginal (internal : FiniteLaw Bool) :
    (liftInternalLaw internal).fstMarginal = internal := by
  simpa [liftInternalLaw] using
    FiniteLaw.product_fstMarginal internal
      (FiniteLaw.uniform : FiniteLaw (Bool × (Bool × Bool)))

/-- A nonuniform internal belief remains nonuniform after embedding; this is
the side condition needed to apply generic strict refresh contraction on the
shared blanket carrier. -/
theorem liftInternalLaw_ne_uniform_of_ne_uniform
    (internal : FiniteLaw Bool)
    (hInternal : internal ≠ (FiniteLaw.uniform : FiniteLaw Bool)) :
    liftInternalLaw internal ≠
      (FiniteLaw.uniform : FiniteLaw BoolBlanketState) := by
  intro hLifted
  apply hInternal
  apply FiniteLaw.ext_mass
  funext hypothesis
  have hMass := congrArg
    (fun law : FiniteLaw BoolBlanketState =>
      law (hypothesis, (false, (false, false)))) hLifted
  norm_num [liftInternalLaw, FiniteLaw.product, FiniteLaw.uniform,
    BoolBlanketState, FEP.MarkovBlanket.DynamicState] at hMass ⊢
  linarith

/-- Lift an internal-state likelihood to the blanket carrier without making
the complement causally relevant to the observation. -/
def liftInternalLikelihood {Outcome : Type*} [Fintype Outcome]
    (likelihood : FiniteKernel Bool Outcome) :
    FiniteKernel BoolBlanketState Outcome where
  mass state observation := likelihood state.1 observation
  nonneg state observation := likelihood.nonneg state.1 observation
  sum_one state := likelihood.sum_one state.1

/-- Prediction through the lifted likelihood after lifting an internal law is
exactly prediction in the original internal model. -/
theorem liftInternalLikelihood_predictive_liftInternalLaw
    {Outcome : Type*} [Fintype Outcome]
    (internal : FiniteLaw Bool) (likelihood : FiniteKernel Bool Outcome) :
    (liftInternalLikelihood likelihood).predictive (liftInternalLaw internal) =
      likelihood.predictive internal := by
  apply FiniteLaw.ext_mass
  funext observation
  rw [FiniteKernel.predictive_mass, FiniteKernel.predictive_mass]
  change
    (∑ state : Bool × (Bool × (Bool × Bool)),
      (internal state.1 *
        (FiniteLaw.uniform : FiniteLaw (Bool × (Bool × Bool))) state.2) *
          likelihood state.1 observation) =
      ∑ hypothesis : Bool, internal hypothesis * likelihood hypothesis observation
  rw [Fintype.sum_prod_type]
  apply Finset.sum_congr rfl
  intro hypothesis _
  calc
    (∑ complement : Bool × (Bool × Bool),
        (internal hypothesis *
          (FiniteLaw.uniform : FiniteLaw (Bool × (Bool × Bool))) complement) *
            likelihood hypothesis observation) =
        (internal hypothesis * likelihood hypothesis observation) *
          ∑ complement : Bool × (Bool × Bool),
            (FiniteLaw.uniform : FiniteLaw (Bool × (Bool × Bool))) complement := by
      rw [Finset.mul_sum]
      apply Finset.sum_congr rfl
      intro complement _
      ring
    _ = internal hypothesis * likelihood hypothesis observation := by
      rw [(FiniteLaw.uniform :
        FiniteLaw (Bool × (Bool × Bool))).sum_one, mul_one]

/-- Updating the lifted blanket law by an internal-only likelihood updates
exactly its internal factor and leaves the uniform complement unchanged. -/
theorem liftInternalLikelihood_posterior_liftInternalLaw
    {Outcome : Type*} [Fintype Outcome]
    (internal : FiniteLaw Bool) (likelihood : FiniteKernel Bool Outcome)
    (observation : Outcome)
    (hEvidence : 0 < likelihood.predictive internal observation) :
    (liftInternalLikelihood likelihood).posterior (liftInternalLaw internal)
        observation
        (by
          rw [liftInternalLikelihood_predictive_liftInternalLaw]
          exact hEvidence) =
      liftInternalLaw
        (likelihood.posterior internal observation hEvidence) := by
  apply FiniteLaw.ext_mass
  funext state
  change
    (internal state.1 *
          (FiniteLaw.uniform : FiniteLaw (Bool × (Bool × Bool))) state.2) *
        likelihood state.1 observation /
      (liftInternalLikelihood likelihood).predictive
        (liftInternalLaw internal) observation =
      (internal state.1 * likelihood state.1 observation /
          likelihood.predictive internal observation) *
        (FiniteLaw.uniform : FiniteLaw (Bool × (Bool × Bool))) state.2
  rw [liftInternalLikelihood_predictive_liftInternalLaw]
  ring

/-- Executable Boolean origin on the exact blanket carrier. -/
def boolBlanketOrigin :
    FEP.MarkovBlanket.DynamicState Bool Bool Bool Bool :=
  (false, (false, (false, false)))

noncomputable def boolBlanketInitialLaw :
    FiniteLaw (FEP.MarkovBlanket.DynamicState Bool Bool Bool Bool) :=
  FiniteLaw.pointMass boolBlanketOrigin

theorem boolBlanketInitial_ne_uniform :
    boolBlanketInitialLaw ≠
      (FiniteLaw.uniform : FiniteLaw
        (FEP.MarkovBlanket.DynamicState Bool Bool Bool Bool)) := by
  exact blanketPointMass_ne_uniform boolBlanketOrigin

/-- A distinct executable Boolean blanket state used to witness positive
post-refresh entropy. -/
def boolBlanketAlternative :
    FEP.MarkovBlanket.DynamicState Bool Bool Bool Bool :=
  (true, (false, (false, false)))

/-- One positive unit of refresh time. -/
noncomputable def boolBlanketRefreshTime : ℝ := 1

private theorem boolBlanketRefreshTime_pos : 0 < boolBlanketRefreshTime := by
  norm_num [boolBlanketRefreshTime]

/-- Boolean `false` holds the blanket state at time zero, while `true` selects
the existing positive one-unit refresh. -/
noncomputable def boolBlanketActionSampleTime (action : Bool) : ℝ :=
  if action then boolBlanketRefreshTime else 0

theorem boolBlanketActionSampleTime_nonneg (action : Bool) :
    0 ≤ boolBlanketActionSampleTime action := by
  cases action <;>
    norm_num [boolBlanketActionSampleTime, boolBlanketRefreshTime]

noncomputable def boolBlanketRefreshKernel :
    FiniteKernel
      (FEP.MarkovBlanket.DynamicState Bool Bool Bool Bool)
      (FEP.MarkovBlanket.DynamicState Bool Bool Bool Bool) :=
  (blanketRefreshSemigroup
    (Internal := Bool) (Sensory := Bool) (Active := Bool) (External := Bool)).kernel
      boolBlanketRefreshTime boolBlanketRefreshTime_pos.le

/-- A concrete action-indexed semigroup on the exact sixteen-state Boolean
blanket carrier. -/
noncomputable def boolBlanketActionIndexedSemigroup :
    ActionIndexedSemigroup BoolBlanketState Bool where
  semigroup _ :=
    blanketRefreshSemigroup
      (Internal := Bool) (Sensory := Bool) (Active := Bool) (External := Bool)
  sampleTime := boolBlanketActionSampleTime
  sampleTime_nonneg := boolBlanketActionSampleTime_nonneg

/-- The false action samples the semigroup at zero and is exactly identity. -/
theorem boolBlanketActionIndexedSemigroup_false_kernel :
    boolBlanketActionIndexedSemigroup.sampledKernel false =
      (FiniteKernel.identity : FiniteKernel BoolBlanketState BoolBlanketState) := by
  change
    (blanketRefreshSemigroup
      (Internal := Bool) (Sensory := Bool) (Active := Bool)
      (External := Bool)).kernel 0 _ = FiniteKernel.identity
  exact FiniteMarkovSemigroup.kernel_zero _

/-- The true action samples the already certified positive refresh kernel. -/
theorem boolBlanketActionIndexedSemigroup_true_kernel :
    boolBlanketActionIndexedSemigroup.sampledKernel true =
      boolBlanketRefreshKernel := by
  apply FiniteKernel.ext_mass
  rfl

/-- Hold and refresh are genuinely different kernels on the Boolean blanket
carrier. -/
theorem boolBlanketActionIndexedSemigroup_kernels_ne :
    boolBlanketActionIndexedSemigroup.sampledKernel false ≠
      boolBlanketActionIndexedSemigroup.sampledKernel true := by
  rw [boolBlanketActionIndexedSemigroup_false_kernel,
    boolBlanketActionIndexedSemigroup_true_kernel]
  intro hEqual
  have hMass := congrArg
    (fun kernel : FiniteKernel BoolBlanketState BoolBlanketState =>
      kernel boolBlanketOrigin boolBlanketAlternative) hEqual
  have hPositive :
      0 < boolBlanketRefreshKernel boolBlanketOrigin boolBlanketAlternative := by
    simpa [boolBlanketRefreshKernel, FiniteMarkovSemigroup.kernel] using
      (blanketRefreshSemigroup_transition_pos
        (Internal := Bool) (Sensory := Bool) (Active := Bool)
        (External := Bool) boolBlanketRefreshTime_pos
        boolBlanketOrigin boolBlanketAlternative)
  norm_num [FiniteKernel.identity, FiniteKernel.deterministic,
    boolBlanketOrigin, boolBlanketAlternative] at hMass
  simp only [boolBlanketOrigin, boolBlanketAlternative] at hPositive
  rw [← hMass] at hPositive
  exact (lt_irrefl 0) hPositive

/-- A Boolean-policy generative model on the sixteen-state blanket carrier.
Its policy transition is owned by `boolBlanketActionIndexedSemigroup`. -/
noncomputable def boolBlanketGenerativeModel
    (initialState : FiniteLaw BoolBlanketState)
    (likelihood : FiniteKernel BoolBlanketState Bool)
    (preferences policyPrior : FiniteLaw Bool) :
    FEP.ActiveInference.GenerativeModel Bool BoolBlanketState Bool :=
  boolBlanketActionIndexedSemigroup.toGenerativeModel id initialState
    likelihood preferences policyPrior

/-- The Boolean blanket model's transition is exactly its sampled action
kernel. -/
@[simp]
theorem boolBlanketGenerativeModel_transition
    (initialState : FiniteLaw BoolBlanketState)
    (likelihood : FiniteKernel BoolBlanketState Bool)
    (preferences policyPrior : FiniteLaw Bool) (action : Bool) :
    (boolBlanketGenerativeModel initialState likelihood preferences
        policyPrior).transition action =
      boolBlanketActionIndexedSemigroup.sampledKernel action :=
  rfl

/-- The same model exposes the canonical identity policy-to-action map. -/
noncomputable def boolBlanketGenerativeModelActionInterface
    (initialState : FiniteLaw BoolBlanketState)
    (likelihood : FiniteKernel BoolBlanketState Bool)
    (preferences policyPrior : FiniteLaw Bool) :
    FEP.ActiveInference.ActionInterface
      (boolBlanketGenerativeModel initialState likelihood preferences
        policyPrior) Bool :=
  boolBlanketActionIndexedSemigroup.toGenerativeModelActionInterface id
    initialState likelihood preferences policyPrior

/-- Holding before observation leaves the lifted internal prior unchanged, so
the blanket model predicts exactly the original internal observation law. -/
theorem boolBlanketGenerativeModel_false_predictedOutcome
    (internal : FiniteLaw Bool) (likelihood : FiniteKernel Bool Bool)
    (preferences policyPrior : FiniteLaw Bool) :
    FEP.ActiveInference.predictedOutcome
        (boolBlanketGenerativeModel (liftInternalLaw internal)
          (liftInternalLikelihood likelihood) preferences policyPrior) false =
      likelihood.predictive internal := by
  change
    (liftInternalLikelihood likelihood).predictive
        ((boolBlanketActionIndexedSemigroup.sampledKernel false).predictive
          (liftInternalLaw internal)) =
      likelihood.predictive internal
  rw [boolBlanketActionIndexedSemigroup_false_kernel,
    FiniteKernel.predictive_identity,
    liftInternalLikelihood_predictive_liftInternalLaw]

/-- Under the hold policy, the model's actual posterior state is the lifted
internal Bayes posterior on the same sixteen-state carrier. -/
theorem boolBlanketGenerativeModel_false_posteriorState
    (internal : FiniteLaw Bool) (likelihood : FiniteKernel Bool Bool)
    (preferences policyPrior : FiniteLaw Bool) (observation : Bool)
    (hEvidence : 0 < likelihood.predictive internal observation) :
    FEP.ActiveInference.posteriorState
        (boolBlanketGenerativeModel (liftInternalLaw internal)
          (liftInternalLikelihood likelihood) preferences policyPrior)
        false observation
        (by
          rw [boolBlanketGenerativeModel_false_predictedOutcome]
          exact hEvidence) =
      liftInternalLaw
        (likelihood.posterior internal observation hEvidence) := by
  apply FiniteLaw.ext_mass
  funext state
  change
    ((boolBlanketActionIndexedSemigroup.sampledKernel false).predictive
          (liftInternalLaw internal) state *
        likelihood state.1 observation /
      (liftInternalLikelihood likelihood).predictive
        ((boolBlanketActionIndexedSemigroup.sampledKernel false).predictive
          (liftInternalLaw internal)) observation =
      (internal state.1 * likelihood state.1 observation /
          likelihood.predictive internal observation) *
        (FiniteLaw.uniform : FiniteLaw (Bool × (Bool × Bool))) state.2)
  rw [boolBlanketActionIndexedSemigroup_false_kernel,
    FiniteKernel.predictive_identity,
    liftInternalLikelihood_predictive_liftInternalLaw]
  simp only [liftInternalLaw, FiniteLaw.product]
  ring

/-- The nonstationary Boolean point mass after one unit of positive refresh. -/
noncomputable def boolBlanketEvolvedLaw :
    FiniteLaw (FEP.MarkovBlanket.DynamicState Bool Bool Bool Bool) :=
  boolBlanketRefreshKernel.predictive boolBlanketInitialLaw

/-- Uniform stationary reference on the exact Boolean blanket carrier. -/
noncomputable def boolBlanketStationaryLaw :
    FiniteLaw (FEP.MarkovBlanket.DynamicState Bool Bool Bool Bool) :=
  FiniteLaw.uniform

theorem boolBlanketStationaryLaw_isStationary :
    (blanketRefreshSemigroup
      (Internal := Bool) (Sensory := Bool) (Active := Bool)
      (External := Bool)).IsStationary boolBlanketStationaryLaw := by
  simpa [blanketRefreshSemigroup, boolBlanketStationaryLaw] using
    (refreshSemigroup_uniform_stationary
      (State := FEP.MarkovBlanket.DynamicState Bool Bool Bool Bool))

private theorem boolBlanketStationaryLaw_pos
    (state : FEP.MarkovBlanket.DynamicState Bool Bool Bool Bool) :
    0 < boolBlanketStationaryLaw state := by
  norm_num [boolBlanketStationaryLaw, FiniteLaw.uniform]

private theorem boolBlanketEvolvedLaw_mass
    (target : FEP.MarkovBlanket.DynamicState Bool Bool Bool Bool) :
    boolBlanketEvolvedLaw target =
      (blanketRefreshSemigroup
        (Internal := Bool) (Sensory := Bool) (Active := Bool)
        (External := Bool)).transition
          boolBlanketRefreshTime boolBlanketOrigin target := by
  rw [boolBlanketEvolvedLaw, boolBlanketInitialLaw,
    predictive_pointMass_mass]
  rfl

private theorem boolBlanketEvolvedAlternative_mass :
    boolBlanketEvolvedLaw boolBlanketAlternative =
      (1 - refreshRho boolBlanketRefreshTime) / 16 := by
  rw [boolBlanketEvolvedLaw_mass]
  norm_num [blanketRefreshSemigroup, refreshSemigroup, refreshTransition,
    refreshDelta, boolBlanketAlternative, boolBlanketOrigin,
    refreshUniformMass]
  ring

private theorem boolBlanketEvolvedAlternative_mass_mem_Ioo :
    boolBlanketEvolvedLaw boolBlanketAlternative ∈ Set.Ioo 0 1 := by
  rw [boolBlanketEvolvedAlternative_mass]
  have hRhoPos : 0 < refreshRho boolBlanketRefreshTime :=
    refreshRho_pos boolBlanketRefreshTime
  have hRhoLt : refreshRho boolBlanketRefreshTime < 1 := by
    rw [refreshRho, Real.exp_lt_one_iff]
    linarith [boolBlanketRefreshTime_pos]
  constructor <;> nlinarith

private theorem boolBlanketEvolved_entropy_pos :
    0 < entropy boolBlanketEvolvedLaw := by
  have hMass := boolBlanketEvolvedAlternative_mass_mem_Ioo
  have hTermPos :
      0 < Real.negMulLog
        (boolBlanketEvolvedLaw boolBlanketAlternative) := by
    rw [Real.negMulLog_eq_neg]
    linarith [Real.mul_log_neg hMass.1 hMass.2]
  apply lt_of_lt_of_le hTermPos
  rw [entropy]
  exact Finset.single_le_sum
    (fun state _ ↦ Real.negMulLog_nonneg
      (boolBlanketEvolvedLaw.nonneg state)
      (boolBlanketEvolvedLaw.mass_le_one state))
    (Finset.mem_univ boolBlanketAlternative)

/-- The explicit positive refresh strictly decreases repository-real KL from
the Boolean point mass to the uniform stationary law. -/
theorem boolBlanket_finiteKL_strict_decrease :
    finiteKL boolBlanketEvolvedLaw boolBlanketStationaryLaw <
      finiteKL boolBlanketInitialLaw boolBlanketStationaryLaw := by
  have hUniformPos : ∀ state,
      0 < (FiniteLaw.uniform : FiniteLaw
        (FEP.MarkovBlanket.DynamicState Bool Bool Bool Bool)) state := by
    intro state
    norm_num [FiniteLaw.uniform]
  rw [boolBlanketStationaryLaw,
    finiteKL_eq_crossEntropy_sub_entropy _ _ hUniformPos,
    finiteKL_eq_crossEntropy_sub_entropy _ _ hUniformPos,
    crossEntropy_uniform, crossEntropy_uniform]
  have hInitialEntropy : entropy boolBlanketInitialLaw = 0 := by
    simpa [boolBlanketInitialLaw] using entropy_pointMass boolBlanketOrigin
  rw [hInitialEntropy]
  linarith [boolBlanketEvolved_entropy_pos]

/-- The named Boolean initial law is genuinely non-invariant under the
positive-time refresh kernel.  Inequality from the uniform stationary law
alone would not establish this dynamical claim. -/
theorem boolBlanketInitial_not_invariant :
    ¬FEP.FiniteMarkovDynamics.IsInvariant
      boolBlanketInitialLaw boolBlanketRefreshKernel := by
  intro hInvariant
  unfold FEP.FiniteMarkovDynamics.IsInvariant at hInvariant
  have hEvolved : boolBlanketEvolvedLaw = boolBlanketInitialLaw := by
    simpa [boolBlanketEvolvedLaw] using hInvariant
  have hStrict := boolBlanket_finiteKL_strict_decrease
  rw [hEvolved] at hStrict
  exact (lt_irrefl _ hStrict)

/-- The same strict decrease on Mathlib's native extended-real KL surface. -/
theorem boolBlanket_nativeKL_strict_decrease :
    InformationTheory.klDiv
        (FEP.NativeBlanket.embeddedLaw boolBlanketEvolvedLaw)
        (FEP.NativeBlanket.embeddedLaw boolBlanketStationaryLaw) <
      InformationTheory.klDiv
        (FEP.NativeBlanket.embeddedLaw boolBlanketInitialLaw)
        (FEP.NativeBlanket.embeddedLaw boolBlanketStationaryLaw) := by
  rw [FEP.DecisionRisk.weightedDirac_klDiv_eq_finiteKL_of_fullSupport
      boolBlanketEvolvedLaw boolBlanketStationaryLaw
      boolBlanketStationaryLaw_pos,
    FEP.DecisionRisk.weightedDirac_klDiv_eq_finiteKL_of_fullSupport
      boolBlanketInitialLaw boolBlanketStationaryLaw
      boolBlanketStationaryLaw_pos]
  exact (ENNReal.ofReal_lt_ofReal_iff_of_nonneg
    (finiteKL_nonneg boolBlanketEvolvedLaw boolBlanketStationaryLaw)).2
      boolBlanket_finiteKL_strict_decrease

/-- Positive jump rates `false → true` and `true → false`. -/
structure TwoStateRates where
  forward : ℝ
  backward : ℝ
  forward_pos : 0 < forward
  backward_pos : 0 < backward

namespace TwoStateRates

def decayRate (rates : TwoStateRates) : ℝ :=
  rates.forward + rates.backward

theorem decayRate_pos (rates : TwoStateRates) : 0 < rates.decayRate :=
  add_pos rates.forward_pos rates.backward_pos

noncomputable def stationaryFalse (rates : TwoStateRates) : ℝ :=
  rates.backward / rates.decayRate

noncomputable def stationaryTrue (rates : TwoStateRates) : ℝ :=
  rates.forward / rates.decayRate

theorem stationaryFalse_pos (rates : TwoStateRates) :
    0 < rates.stationaryFalse :=
  div_pos rates.backward_pos rates.decayRate_pos

theorem stationaryTrue_pos (rates : TwoStateRates) :
    0 < rates.stationaryTrue :=
  div_pos rates.forward_pos rates.decayRate_pos

theorem stationary_sum_one (rates : TwoStateRates) :
    rates.stationaryFalse + rates.stationaryTrue = 1 := by
  unfold stationaryFalse stationaryTrue decayRate
  field_simp [ne_of_gt (add_pos rates.forward_pos rates.backward_pos)]
  ring

theorem stationaryTrue_mul_decayRate (rates : TwoStateRates) :
    rates.stationaryTrue * rates.decayRate = rates.forward := by
  unfold stationaryTrue
  exact div_mul_cancel₀ rates.forward (ne_of_gt rates.decayRate_pos)

theorem stationaryFalse_mul_decayRate (rates : TwoStateRates) :
    rates.stationaryFalse * rates.decayRate = rates.backward := by
  unfold stationaryFalse
  exact div_mul_cancel₀ rates.backward (ne_of_gt rates.decayRate_pos)

/-- Stationary law `(b/(a+b), a/(a+b))`. -/
noncomputable def stationaryLaw (rates : TwoStateRates) : FiniteLaw Bool where
  mass state := if state then rates.stationaryTrue else rates.stationaryFalse
  nonneg state := by
    cases state <;> simp [rates.stationaryFalse_pos.le,
      rates.stationaryTrue_pos.le]
  sum_one := by
    simpa [Fintype.sum_bool, add_comm] using rates.stationary_sum_one

/-- Exact exponential relaxation factor. -/
noncomputable def rho (rates : TwoStateRates) (time : ℝ) : ℝ :=
  Real.exp (-rates.decayRate * time)

theorem rho_pos (rates : TwoStateRates) (time : ℝ) : 0 < rates.rho time :=
  Real.exp_pos _

theorem rho_le_one (rates : TwoStateRates) {time : ℝ} (hTime : 0 ≤ time) :
    rates.rho time ≤ 1 := by
  rw [rho, Real.exp_le_one_iff]
  exact mul_nonpos_of_nonpos_of_nonneg (neg_nonpos.mpr rates.decayRate_pos.le)
    hTime

@[simp]
theorem rho_zero (rates : TwoStateRates) : rates.rho 0 = 1 := by
  simp [rho]

theorem rho_add (rates : TwoStateRates) (left right : ℝ) :
    rates.rho (left + right) = rates.rho left * rates.rho right := by
  rw [rho, rho, rho, ← Real.exp_add]
  congr 1
  ring

/-- Closed-form two-state transition probability. -/
noncomputable def transition (rates : TwoStateRates) (time : ℝ)
    (source target : Bool) : ℝ :=
  match source, target with
  | false, false => rates.stationaryFalse + rates.stationaryTrue * rates.rho time
  | false, true => rates.stationaryTrue * (1 - rates.rho time)
  | true, false => rates.stationaryFalse * (1 - rates.rho time)
  | true, true => rates.stationaryTrue + rates.stationaryFalse * rates.rho time

theorem transition_rowSum (rates : TwoStateRates) (time : ℝ)
    (source : Bool) :
    ∑ target, rates.transition time source target = 1 := by
  cases source <;> simp only [Fintype.sum_bool, transition]
  · calc
      rates.stationaryTrue * (1 - rates.rho time) +
          (rates.stationaryFalse + rates.stationaryTrue * rates.rho time) =
          rates.stationaryFalse + rates.stationaryTrue := by ring
      _ = 1 := rates.stationary_sum_one
  · calc
      rates.stationaryTrue + rates.stationaryFalse * rates.rho time +
          rates.stationaryFalse * (1 - rates.rho time) =
          rates.stationaryFalse + rates.stationaryTrue := by ring
      _ = 1 := rates.stationary_sum_one

theorem transition_nonneg (rates : TwoStateRates) {time : ℝ}
    (hTime : 0 ≤ time) (source target : Bool) :
    0 ≤ rates.transition time source target := by
  have hRho : 0 ≤ rates.rho time := (rates.rho_pos time).le
  have hOneSub : 0 ≤ 1 - rates.rho time := sub_nonneg.mpr (rates.rho_le_one hTime)
  cases source <;> cases target <;> simp only [transition]
  · exact add_nonneg rates.stationaryFalse_pos.le
      (mul_nonneg rates.stationaryTrue_pos.le hRho)
  · exact mul_nonneg rates.stationaryTrue_pos.le hOneSub
  · exact mul_nonneg rates.stationaryFalse_pos.le hOneSub
  · exact add_nonneg rates.stationaryTrue_pos.le
      (mul_nonneg rates.stationaryFalse_pos.le hRho)

/-- The normalized two-state finite kernel at nonnegative time. -/
noncomputable def kernel (rates : TwoStateRates) (time : ℝ)
    (hTime : 0 ≤ time) : FiniteKernel Bool Bool where
  mass := rates.transition time
  nonneg := rates.transition_nonneg hTime
  sum_one := rates.transition_rowSum time

theorem transition_zero (rates : TwoStateRates) (source target : Bool) :
    rates.transition 0 source target = if source = target then 1 else 0 := by
  cases source <;> cases target <;>
    simp [transition, rates.stationary_sum_one, add_comm]

/-- Chapman--Kolmogorov for the exact two-state transition function. -/
theorem transition_add (rates : TwoStateRates) (left right : ℝ)
    (source target : Bool) :
    rates.transition (left + right) source target =
      ∑ middle,
        rates.transition left source middle *
          rates.transition right middle target := by
  have hStationary := rates.stationary_sum_one
  have hTrue : rates.stationaryTrue = 1 - rates.stationaryFalse := by
    linarith
  cases source <;> cases target <;>
    simp only [Fintype.sum_bool, transition] <;>
    rw [rates.rho_add left right, hTrue] <;> ring

/-- Generator with rows `(-a,a)` and `(b,-b)`. -/
def generator (rates : TwoStateRates) (source target : Bool) : ℝ :=
  match source, target with
  | false, false => -rates.forward
  | false, true => rates.forward
  | true, false => rates.backward
  | true, true => -rates.backward

/-- Entrywise derivative of the closed-form transition matrix. -/
noncomputable def transitionDerivative (rates : TwoStateRates) (time : ℝ)
    (source target : Bool) : ℝ :=
  match source, target with
  | false, false => -rates.forward * rates.rho time
  | false, true => rates.forward * rates.rho time
  | true, false => rates.backward * rates.rho time
  | true, true => -rates.backward * rates.rho time

theorem rho_hasDerivAt (rates : TwoStateRates) (time : ℝ) :
    HasDerivAt rates.rho (-rates.decayRate * rates.rho time) time := by
  change HasDerivAt
    (fun candidate ↦ Real.exp (-rates.decayRate * candidate))
    (-rates.decayRate * Real.exp (-rates.decayRate * time)) time
  simpa only [Function.id_def, one_mul, mul_one, mul_comm] using
    ((hasDerivAt_id time).const_mul (-rates.decayRate)).exp

theorem transition_hasDerivAt (rates : TwoStateRates) (time : ℝ)
    (source target : Bool) :
    HasDerivAt (fun candidate ↦ rates.transition candidate source target)
      (rates.transitionDerivative time source target) time := by
  have hRho := rates.rho_hasDerivAt time
  cases source <;> cases target
  · change HasDerivAt
      (fun candidate ↦ rates.stationaryFalse +
        rates.stationaryTrue * rates.rho candidate)
      (-rates.forward * rates.rho time) time
    apply ((hasDerivAt_const time rates.stationaryFalse).add
      (hRho.const_mul rates.stationaryTrue)).congr_deriv
    rw [← rates.stationaryTrue_mul_decayRate]
    ring
  · change HasDerivAt
      (fun candidate ↦ rates.stationaryTrue * (1 - rates.rho candidate))
      (rates.forward * rates.rho time) time
    apply (((hasDerivAt_const time 1).sub hRho).const_mul
      rates.stationaryTrue).congr_deriv
    rw [← rates.stationaryTrue_mul_decayRate]
    ring
  · change HasDerivAt
      (fun candidate ↦ rates.stationaryFalse * (1 - rates.rho candidate))
      (rates.backward * rates.rho time) time
    apply (((hasDerivAt_const time 1).sub hRho).const_mul
      rates.stationaryFalse).congr_deriv
    rw [← rates.stationaryFalse_mul_decayRate]
    ring
  · change HasDerivAt
      (fun candidate ↦ rates.stationaryTrue +
        rates.stationaryFalse * rates.rho candidate)
      (-rates.backward * rates.rho time) time
    apply ((hasDerivAt_const time rates.stationaryTrue).add
      (hRho.const_mul rates.stationaryFalse)).congr_deriv
    rw [← rates.stationaryFalse_mul_decayRate]
    ring

theorem generator_mul_transition (rates : TwoStateRates) (time : ℝ)
    (source target : Bool) :
    (∑ middle,
        rates.generator source middle * rates.transition time middle target) =
      rates.transitionDerivative time source target := by
  have hStationary := rates.stationary_sum_one
  have hTrue : rates.stationaryTrue = 1 - rates.stationaryFalse := by
    linarith
  cases source <;> cases target <;>
    simp only [Fintype.sum_bool, generator, transition, transitionDerivative] <;>
    simp only [← rates.stationaryTrue_mul_decayRate,
      ← rates.stationaryFalse_mul_decayRate] <;>
    rw [hTrue] <;> ring

theorem transition_mul_generator (rates : TwoStateRates) (time : ℝ)
    (source target : Bool) :
    (∑ middle,
        rates.transition time source middle * rates.generator middle target) =
      rates.transitionDerivative time source target := by
  have hStationary := rates.stationary_sum_one
  have hTrue : rates.stationaryTrue = 1 - rates.stationaryFalse := by
    linarith
  cases source <;> cases target <;>
    simp only [Fintype.sum_bool, generator, transition, transitionDerivative] <;>
    simp only [← rates.stationaryTrue_mul_decayRate,
      ← rates.stationaryFalse_mul_decayRate] <;>
    rw [hTrue] <;> ring

/-- The derivative equals both generator products, entry by entry. -/
theorem transition_masterEquation (rates : TwoStateRates) (time : ℝ)
    (source target : Bool) :
    HasDerivAt (fun candidate ↦ rates.transition candidate source target)
        (∑ middle,
          rates.generator source middle * rates.transition time middle target)
        time ∧
      HasDerivAt (fun candidate ↦ rates.transition candidate source target)
        (∑ middle,
          rates.transition time source middle * rates.generator middle target)
        time := by
  constructor
  · rw [rates.generator_mul_transition time source target]
    exact rates.transition_hasDerivAt time source target
  · rw [rates.transition_mul_generator time source target]
    exact rates.transition_hasDerivAt time source target

theorem transition_stationary (rates : TwoStateRates) (time : ℝ)
    (target : Bool) :
    (∑ source,
        rates.stationaryLaw source * rates.transition time source target) =
      rates.stationaryLaw target := by
  have hStationary := rates.stationary_sum_one
  have hTrue : rates.stationaryTrue = 1 - rates.stationaryFalse := by
    linarith
  cases target <;>
    simp only [Fintype.sum_bool, stationaryLaw,
      transition, Bool.false_eq_true, ite_false, ite_true] <;>
    rw [hTrue] <;> ring

theorem transition_detailedBalance (rates : TwoStateRates) (time : ℝ)
    (source target : Bool) :
    rates.stationaryLaw source * rates.transition time source target =
      rates.stationaryLaw target * rates.transition time target source := by
  cases source <;> cases target <;>
    simp [stationaryLaw, transition] <;> ring

/-- The closed-form two-state generator satisfies the general finite rate
generator contract. -/
def rateGenerator (rates : TwoStateRates) : FiniteRateGenerator Bool where
  rate := rates.generator
  offDiagonal_nonneg := by
    intro source target hDistinct
    cases source <;> cases target <;>
      simp_all [generator, rates.forward_pos.le, rates.backward_pos.le]
  row_sum_zero := by
    intro source
    cases source <;> simp [generator]

/-- The original closed-form transition is a fully certified instance of the
general semigroup interface. -/
noncomputable def certifiedSemigroup (rates : TwoStateRates) :
    FiniteMarkovSemigroup Bool where
  generator := rates.rateGenerator
  transition := rates.transition
  transition_nonneg := rates.transition_nonneg
  transition_sum_one := rates.transition_rowSum
  transition_zero := rates.transition_zero
  transition_add := rates.transition_add
  transition_hasDerivAt_left := fun time source target ↦
    (rates.transition_masterEquation time source target).1
  transition_hasDerivAt_right := fun time source target ↦
    (rates.transition_masterEquation time source target).2

/-- Sampling the certified wrapper recovers the pre-existing normalized
two-state kernel exactly. -/
theorem certifiedSemigroup_kernel_eq_kernel (rates : TwoStateRates)
    (time : ℝ) (hTime : 0 ≤ time) :
    rates.certifiedSemigroup.kernel time hTime = rates.kernel time hTime := by
  apply FiniteKernel.ext_mass
  rfl

/-- The exact stationary law is invariant under every certified slice. -/
theorem certifiedSemigroup_stationary (rates : TwoStateRates) :
    rates.certifiedSemigroup.IsStationary rates.stationaryLaw := by
  intro time hTime
  unfold FEP.FiniteMarkovDynamics.IsInvariant
  apply FiniteLaw.ext_mass
  funext target
  change (∑ source,
    rates.stationaryLaw source * rates.transition time source target) =
      rates.stationaryLaw target
  exact rates.transition_stationary time target

/-- The exact stationary law satisfies detailed balance for every certified
slice. -/
theorem certifiedSemigroup_detailedBalanced (rates : TwoStateRates) :
    rates.certifiedSemigroup.IsDetailedBalanced rates.stationaryLaw := by
  intro time hTime source target
  change rates.stationaryLaw source * rates.transition time source target =
    rates.stationaryLaw target * rates.transition time target source
  exact rates.transition_detailedBalance time source target

/-- True-state mass after evolving an arbitrary initial law. -/
noncomputable def trueMass (rates : TwoStateRates)
    (initial : FiniteLaw Bool) (time : ℝ) : ℝ :=
  ∑ source, initial source * rates.transition time source true

/-- Exact exponential relaxation of the nonstationary coordinate. -/
theorem relaxation_exact (rates : TwoStateRates)
    (initial : FiniteLaw Bool) (time : ℝ) :
    rates.trueMass initial time - rates.stationaryTrue =
      rates.rho time * (initial true - rates.stationaryTrue) := by
  have hInitial : initial false + initial true = 1 := by
    simpa [Fintype.sum_bool, add_comm] using initial.sum_one
  have hStationary := rates.stationary_sum_one
  have hInitialFalse : initial false = 1 - initial true := by
    linarith
  have hStationaryFalse :
      rates.stationaryFalse = 1 - rates.stationaryTrue := by
    linarith
  simp only [trueMass, Fintype.sum_bool, transition]
  rw [hInitialFalse, hStationaryFalse]
  ring

/-- Quadratic distance of the true-state mass from stationarity. -/
noncomputable def lyapunov (rates : TwoStateRates)
    (initial : FiniteLaw Bool) (time : ℝ) : ℝ :=
  (rates.trueMass initial time - rates.stationaryTrue) ^ 2

theorem lyapunov_exact (rates : TwoStateRates)
    (initial : FiniteLaw Bool) (time : ℝ) :
    rates.lyapunov initial time =
      rates.rho time ^ 2 *
        (initial true - rates.stationaryTrue) ^ 2 := by
  rw [lyapunov, rates.relaxation_exact initial time]
  ring

theorem lyapunov_hasDerivAt (rates : TwoStateRates)
    (initial : FiniteLaw Bool) (time : ℝ) :
    HasDerivAt (rates.lyapunov initial)
      (-2 * rates.decayRate * rates.lyapunov initial time) time := by
  have hLyapunov : rates.lyapunov initial = fun candidate ↦
      rates.rho candidate ^ 2 *
        (initial true - rates.stationaryTrue) ^ 2 := by
    funext candidate
    exact rates.lyapunov_exact initial candidate
  rw [hLyapunov]
  apply (((rates.rho_hasDerivAt time).pow 2).mul_const
    ((initial true - rates.stationaryTrue) ^ 2)).congr_deriv
  ring

/-! ## Plot-ready rates and a strict nonstationary witness -/

noncomputable def benchmarkRates : TwoStateRates where
  forward := 7 / 10
  backward := 3 / 10
  forward_pos := by norm_num
  backward_pos := by norm_num

noncomputable def benchmarkInitial : FiniteLaw Bool :=
  FiniteLaw.pointMass false

theorem benchmarkRates_exact :
    benchmarkRates.forward = 0.7 ∧ benchmarkRates.backward = 0.3 := by
  norm_num [benchmarkRates, OfScientific.ofScientific]

theorem benchmarkInitial_nonstationary :
    benchmarkInitial true ≠ benchmarkRates.stationaryTrue := by
  norm_num [benchmarkInitial, benchmarkRates, stationaryTrue, decayRate,
    FiniteLaw.pointMass]

theorem benchmarkLyapunov_deriv_zero_neg :
    -2 * benchmarkRates.decayRate * benchmarkRates.lyapunov benchmarkInitial 0 < 0 := by
  norm_num [benchmarkRates, benchmarkInitial, decayRate, lyapunov, trueMass,
    transition, stationaryTrue, stationaryFalse, rho, FiniteLaw.pointMass,
    Fintype.sum_bool]

end TwoStateRates

end FEP.ContinuousTimeMarkov
