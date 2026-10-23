module
public import FepSketches.families.continuous_time_thermodynamics
public import FepSketches.families.core_bayesian_mechanics
public import FepSketches.families.core_free_energy
public import FepSketches.continuous_time_markov

@[expose] public section

/-!
# Exact two-state continuous-time topic compositions

These bridges pair the exact two-state semigroup with the nearest discrete or
measure-native catalog law.  The conjunctions preserve the different time
domains and carriers instead of asserting an unsupported general equivalence.
-/

namespace FEPComposed

open FEP FEP.ContinuousTimeMarkov
open MeasureTheory ProbabilityTheory Finset
open scoped BigOperators ENNReal MeasureTheory ProbabilityTheory

/-- Exact continuous-time row normalization is paired with the original
symmetric two-state discrete transition normalization. -/
theorem fep149_continuousKernel_extends_fep020
    (rates : TwoStateRates) (time switching : ℝ)
    (source discreteSource : Bool) :
    (∑ target, rates.transition time source target = 1) ∧
      (∑ target : Bool,
        fep_fep020.FEP020.fep020_transition switching discreteSource target =
          1) := by
  exact
    ⟨fep_fep149.FEP149.fep149_twoStateSemigroup_rowSum rates time source,
      fep_fep020.FEP020.fep020_transition_sum_one
        switching discreteSource⟩

/-- The continuous semigroup and an arbitrary discrete iterate both reduce to
their respective identity maps at zero time. -/
theorem fep150_semigroupZero_extends_fep006
    {State : Type*} (rates : TwoStateRates) (source target : Bool)
    (step : State → State) :
    (rates.transition 0 source target = if source = target then 1 else 0) ∧
      fep_fep006.FEP006.fep006_iterateFlow step 0 = id := by
  exact
    ⟨fep_fep150.FEP150.fep150_twoStateSemigroup_zero rates source target,
      fep_fep006.FEP006.fep006_iterateFlow_zero step⟩

/-- Chapman--Kolmogorov addition and discrete iterate addition expose the
same semigroup law on their explicitly different time domains. -/
theorem fep151_semigroupAdd_extends_fep006
    {State : Type*} (rates : TwoStateRates) (left right : ℝ)
    (source target : Bool) (step : State → State) (m n : ℕ)
    (state : State) :
    (rates.transition (left + right) source target =
      ∑ middle,
        rates.transition left source middle *
          rates.transition right middle target) ∧
      (fep_fep006.FEP006.fep006_iterateFlow step (m + n) state =
        fep_fep006.FEP006.fep006_iterateFlow step m
          (fep_fep006.FEP006.fep006_iterateFlow step n state)) := by
  exact
    ⟨fep_fep151.FEP151.fep151_twoStateSemigroup_add
        rates left right source target,
      fep_fep006.FEP006.fep006_iterateFlow_add step m n state⟩

/-- The continuous generator equation is paired with the original affine
one-step two-state master equation, without conflating derivatives and steps. -/
theorem fep152_masterEquation_extends_fep020
    (rates : TwoStateRates) (time : ℝ) (source target : Bool)
    (switching probability : ℝ) :
    HasDerivAt (fun candidate ↦ rates.transition candidate source target)
        (∑ middle,
          rates.generator source middle * rates.transition time middle target)
        time ∧
      (fep_fep020.FEP020.fep020_evolve switching probability =
        switching + (1 - 2 * switching) * probability) := by
  exact
    ⟨(fep_fep152.FEP152.fep152_twoStateSemigroup_hasDerivAt
        rates time source target).1,
      fep_fep020.FEP020.fep020_evolve_affine switching probability⟩

/-- Exact finite detailed balance is paired with the original native identity
kernel's reversibility witness; their carriers remain separate. -/
theorem fep153_continuousDetailedBalance_extends_fep010
    {Native : Type*} [MeasurableSpace Native]
    (rates : TwoStateRates) (time : ℝ) (source target : Bool)
    (nativeLaw : Measure Native) :
    (rates.stationaryLaw source * rates.transition time source target =
      rates.stationaryLaw target * rates.transition time target source) ∧
      Kernel.IsReversible (Kernel.id : Kernel Native Native) nativeLaw := by
  exact
    ⟨fep_fep153.FEP153.fep153_twoStateSemigroup_detailedBalance
        rates time source target,
      fep_fep010.FEP010.fep010_identity_reversible nativeLaw⟩

/-- Exact exponential relaxation and the original discrete deviation update
are paired as distinct closed-form two-state contraction laws. -/
theorem fep154_continuousRelaxation_extends_fep020
    (rates : TwoStateRates) (initial : FiniteLaw Bool) (time : ℝ)
    (switching probability : ℝ) :
    (rates.trueMass initial time - rates.stationaryTrue =
      rates.rho time * (initial true - rates.stationaryTrue)) ∧
      (fep_fep020.FEP020.fep020_evolve switching probability - 1 / 2 =
        (1 - 2 * switching) * (probability - 1 / 2)) := by
  exact
    ⟨fep_fep154.FEP154.fep154_twoStateRelaxation_exact rates initial time,
      fep_fep020.FEP020.fep020_deviation_step switching probability⟩

/-- Exact continuous Lyapunov differentiation is paired with the original
nonincrease certificate for one stable quadratic-descent step. -/
theorem fep155_lyapunovDecay_extends_fep032
    (rates : TwoStateRates) (initial : FiniteLaw Bool) (time : ℝ)
    {step center state : ℝ} (hStepNonnegative : 0 ≤ step)
    (hStepAtMostTwo : step ≤ 2) :
    HasDerivAt (rates.lyapunov initial)
        (-2 * rates.decayRate * rates.lyapunov initial time) time ∧
      (fep_fep032.FEP032.fep032_quadraticUpdate step center state - center) ^ 2 ≤
        (state - center) ^ 2 := by
  exact
    ⟨fep_fep155.FEP155.fep155_twoStateLyapunov_hasDerivAt
        rates initial time,
      fep_fep032.FEP032.fep032_quadraticEnergy_descent
        hStepNonnegative hStepAtMostTwo⟩

end FEPComposed
