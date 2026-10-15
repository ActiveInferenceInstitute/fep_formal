module
public import FepSketches.finite_markov_dynamics
public import FepSketches.variational_duality
public import Mathlib.Analysis.SpecialFunctions.BinaryEntropy

@[expose] public section

/-!
# Finite path-space stochastic thermodynamics

This module keeps every thermodynamic statement on normalized finite laws.
The reverse law is stored in the same path coordinate as the forward law;
`reversal` records the involution used to align the physical reverse path.
Log-ratio identities require strict support.  At a zero reverse rate Lean's
totalized real logarithm is exposed as a boundary value, not interpreted as
an extended-real entropy production.
-/

namespace FEP.PathThermodynamics

open FEP FEP.FiniteInformation FEP.FiniteMarkovDynamics
  FEP.VariationalDuality Finset
open scoped BigOperators

variable {Path State : Type*} [Fintype Path] [Fintype State]

/-! ## Normalized forward and reverse path laws -/

/-- A pair of normalized finite path laws together with an involutive path
reversal.  `reverseAligned` is already expressed in forward-path coordinates,
so it can serve directly as the denominator of a likelihood ratio. -/
structure FinitePathProtocol (Path : Type*) [Fintype Path] where
  forward : FiniteLaw Path
  reverseAligned : FiniteLaw Path
  reversal : Path → Path
  reversal_involutive : Function.Involutive reversal

/-- Applying the protocol reversal twice recovers the original path. -/
theorem reverse_reverse (protocol : FinitePathProtocol Path) (path : Path) :
    protocol.reversal (protocol.reversal path) = path :=
  protocol.reversal_involutive path

/-- Both path laws carry unit mass by construction. -/
theorem pathLaw_normalization (protocol : FinitePathProtocol Path) :
    (∑ path, protocol.forward path = 1) ∧
      ∑ path, protocol.reverseAligned path = 1 :=
  ⟨protocol.forward.sum_one, protocol.reverseAligned.sum_one⟩

/-- Forward-to-reverse path likelihood ratio.  Its logarithmic use below is
restricted to full support. -/
noncomputable def pathRatio
    (protocol : FinitePathProtocol Path) (path : Path) : ℝ :=
  protocol.forward path / protocol.reverseAligned path

/-- Under reverse support, multiplying the ratio by its denominator
reconstructs the forward path mass. -/
theorem pathRatio_mul_reverse
    (protocol : FinitePathProtocol Path)
    (hReverse : ∀ path, 0 < protocol.reverseAligned path) (path : Path) :
    pathRatio protocol path * protocol.reverseAligned path =
      protocol.forward path := by
  exact div_mul_cancel₀ _ (ne_of_gt (hReverse path))

/-- The totalized ratio is zero at a zero reverse atom.  Downstream theorems
must not read this boundary as an infinite extended-real log ratio. -/
theorem pathRatio_zero_reverse_boundary
    (protocol : FinitePathProtocol Path) (path : Path)
    (hZero : protocol.reverseAligned path = 0) :
    pathRatio protocol path = 0 := by
  simp [pathRatio, hZero]

/-! ## Entropy production and fluctuation identities -/

/-- Pathwise stochastic entropy production as a supported log ratio. -/
noncomputable def pathwiseEntropyProduction
    (protocol : FinitePathProtocol Path) (path : Path) : ℝ :=
  Real.log (pathRatio protocol path)

/-- Mean path entropy production is the finite KL divergence between the
forward and aligned reverse laws. -/
noncomputable def entropyProduction
    (protocol : FinitePathProtocol Path) : ℝ :=
  finiteKL protocol.forward protocol.reverseAligned

/-- Entropy production is nonnegative on the normalized finite carrier. -/
theorem entropyProduction_nonneg (protocol : FinitePathProtocol Path) :
    0 ≤ entropyProduction protocol :=
  finiteKL_nonneg protocol.forward protocol.reverseAligned

/-- With full support, expected pathwise log ratio is exactly path KL. -/
theorem entropyProduction_eq_expected_logRatio
    (protocol : FinitePathProtocol Path)
    (hForward : ∀ path, 0 < protocol.forward path)
    (hReverse : ∀ path, 0 < protocol.reverseAligned path) :
    entropyProduction protocol =
      ∑ path, protocol.forward path * pathwiseEntropyProduction protocol path := by
  rw [entropyProduction,
    finiteKL_eq_crossEntropy_sub_entropy protocol.forward
      protocol.reverseAligned hReverse]
  simp only [crossEntropy, entropy, pathwiseEntropyProduction, pathRatio]
  simp_rw [Real.negMulLog_eq_neg,
    Real.log_div (ne_of_gt (hForward _)) (ne_of_gt (hReverse _))]
  rw [← Finset.sum_sub_distrib]
  apply Finset.sum_congr rfl
  intro path _
  ring

/-- Detailed pathwise fluctuation identity: reverse mass multiplied by the
exponential entropy production is the forward mass. -/
theorem detailedFluctuation_identity
    (protocol : FinitePathProtocol Path)
    (hForward : ∀ path, 0 < protocol.forward path)
    (hReverse : ∀ path, 0 < protocol.reverseAligned path) (path : Path) :
    protocol.reverseAligned path *
        Real.exp (pathwiseEntropyProduction protocol path) =
      protocol.forward path := by
  have hRatio : 0 < pathRatio protocol path :=
    div_pos (hForward path) (hReverse path)
  rw [pathwiseEntropyProduction, Real.exp_log hRatio]
  unfold pathRatio
  field_simp [ne_of_gt (hReverse path)]

/-- Integral fluctuation theorem on a supported finite path space. -/
theorem integralFluctuation_eq_one
    (protocol : FinitePathProtocol Path)
    (hForward : ∀ path, 0 < protocol.forward path)
    (hReverse : ∀ path, 0 < protocol.reverseAligned path) :
    ∑ path, protocol.forward path *
        Real.exp (-pathwiseEntropyProduction protocol path) = 1 := by
  calc
    (∑ path, protocol.forward path *
        Real.exp (-pathwiseEntropyProduction protocol path)) =
        ∑ path, protocol.reverseAligned path := by
      apply Finset.sum_congr rfl
      intro path _
      have hRatio : 0 < pathRatio protocol path :=
        div_pos (hForward path) (hReverse path)
      rw [pathwiseEntropyProduction, Real.exp_neg, Real.exp_log hRatio]
      unfold pathRatio
      field_simp [ne_of_gt (hForward path), ne_of_gt (hReverse path)]
    _ = 1 := protocol.reverseAligned.sum_one

/-- Under the usual reversal exchange law, entropy production changes sign
when the path is reversed. -/
theorem pathwiseEntropyProduction_reverse
    (protocol : FinitePathProtocol Path)
    (hForward : ∀ path, 0 < protocol.forward path)
    (hReverse : ∀ path, 0 < protocol.reverseAligned path)
    (hExchangeForward : ∀ path,
      protocol.forward (protocol.reversal path) =
        protocol.reverseAligned path)
    (hExchangeReverse : ∀ path,
      protocol.reverseAligned (protocol.reversal path) =
        protocol.forward path)
    (path : Path) :
    pathwiseEntropyProduction protocol (protocol.reversal path) =
      -pathwiseEntropyProduction protocol path := by
  simp only [pathwiseEntropyProduction, pathRatio, hExchangeForward,
    hExchangeReverse]
  rw [Real.log_div (ne_of_gt (hReverse path)) (ne_of_gt (hForward path)),
    Real.log_div (ne_of_gt (hForward path)) (ne_of_gt (hReverse path))]
  ring

/-! ## Finite Jarzynski equality -/

/-- Exponential work average for a finite protocol. -/
noncomputable def exponentialWorkAverage
    (law : FiniteLaw Path) (beta : ℝ) (work : Path → ℝ) : ℝ :=
  ∑ path, law path * Real.exp (-beta * work path)

/-- Explicit normalization premise for a finite Jarzynski protocol.  It is
the finite expectation of `exp (-β (W - ΔF))`, with positive inverse
temperature recorded separately. -/
def HasJarzynskiNormalization
    (law : FiniteLaw Path) (beta deltaFreeEnergy : ℝ)
    (work : Path → ℝ) : Prop :=
  0 < beta ∧
    ∑ path, law path *
      Real.exp (-beta * (work path - deltaFreeEnergy)) = 1

/-- Finite Jarzynski equality derived from the explicit exponential-work
normalization premise. -/
theorem finiteJarzynski_eq
    (law : FiniteLaw Path) (beta deltaFreeEnergy : ℝ)
    (work : Path → ℝ)
    (hNormalization :
      HasJarzynskiNormalization law beta deltaFreeEnergy work) :
    exponentialWorkAverage law beta work =
      Real.exp (-beta * deltaFreeEnergy) := by
  have hFactor :
      Real.exp (beta * deltaFreeEnergy) *
          exponentialWorkAverage law beta work = 1 := by
    calc
      Real.exp (beta * deltaFreeEnergy) *
          exponentialWorkAverage law beta work =
          ∑ path, law path *
            Real.exp (-beta * (work path - deltaFreeEnergy)) := by
        rw [exponentialWorkAverage, Finset.mul_sum]
        apply Finset.sum_congr rfl
        intro path _
        calc
          Real.exp (beta * deltaFreeEnergy) *
              (law path * Real.exp (-beta * work path)) =
              law path *
                (Real.exp (beta * deltaFreeEnergy) *
                  Real.exp (-beta * work path)) := by ring
          _ = law path *
                Real.exp (beta * deltaFreeEnergy + -beta * work path) := by
              rw [← Real.exp_add]
          _ = law path *
                Real.exp (-beta * (work path - deltaFreeEnergy)) := by
              congr 2
              ring
      _ = 1 := hNormalization.2
  calc
    exponentialWorkAverage law beta work =
        Real.exp (-beta * deltaFreeEnergy) *
          (Real.exp (beta * deltaFreeEnergy) *
            exponentialWorkAverage law beta work) := by
      rw [← mul_assoc, ← Real.exp_add]
      simp
    _ = Real.exp (-beta * deltaFreeEnergy) := by rw [hFactor, mul_one]

/-! ## Crooks relation as the source of the Jarzynski premise -/

/-- Pathwise Crooks relation in forward-path coordinates: the aligned reverse
path mass, reweighted by the exponential dissipated work `β (W - ΔF)`, is the
forward path mass.  Unlike `HasJarzynskiNormalization`, it is a per-path
microscopic statement rather than the averaged conclusion. -/
def HasCrooksRelation
    (protocol : FinitePathProtocol Path) (beta deltaFreeEnergy : ℝ)
    (work : Path → ℝ) : Prop :=
  0 < beta ∧ ∀ path,
    protocol.reverseAligned path *
        Real.exp (beta * (work path - deltaFreeEnergy)) =
      protocol.forward path

/-- The pathwise Crooks relation implies the Jarzynski normalization premise:
weighting it by `exp (-β (W - ΔF))` returns the reverse law's unit mass.  No
support hypothesis is needed. -/
theorem hasJarzynskiNormalization_of_crooks
    (protocol : FinitePathProtocol Path) (beta deltaFreeEnergy : ℝ)
    (work : Path → ℝ)
    (hCrooks : HasCrooksRelation protocol beta deltaFreeEnergy work) :
    HasJarzynskiNormalization protocol.forward beta deltaFreeEnergy work := by
  refine ⟨hCrooks.1, ?_⟩
  calc
    (∑ path, protocol.forward path *
        Real.exp (-beta * (work path - deltaFreeEnergy))) =
        ∑ path, protocol.reverseAligned path := by
      apply Finset.sum_congr rfl
      intro path _
      rw [← hCrooks.2 path, mul_assoc, ← Real.exp_add]
      have hCancel : beta * (work path - deltaFreeEnergy) +
          -beta * (work path - deltaFreeEnergy) = 0 := by ring
      rw [hCancel, Real.exp_zero, mul_one]
    _ = 1 := protocol.reverseAligned.sum_one

/-- Finite Jarzynski equality derived from the pathwise Crooks relation rather
than from an assumed exponential-work normalization. -/
theorem finiteJarzynski_of_crooks
    (protocol : FinitePathProtocol Path) (beta deltaFreeEnergy : ℝ)
    (work : Path → ℝ)
    (hCrooks : HasCrooksRelation protocol beta deltaFreeEnergy work) :
    exponentialWorkAverage protocol.forward beta work =
      Real.exp (-beta * deltaFreeEnergy) :=
  finiteJarzynski_eq protocol.forward beta deltaFreeEnergy work
    (hasJarzynskiNormalization_of_crooks protocol beta deltaFreeEnergy work
      hCrooks)

/-- On a supported protocol the work `ΔF + σ / β`, with `σ` the pathwise
entropy production, satisfies the Crooks relation: the detailed fluctuation
identity is the Crooks relation with dissipated work `β (W - ΔF) = σ`. -/
theorem crooks_of_entropyProduction
    (protocol : FinitePathProtocol Path) (beta deltaFreeEnergy : ℝ)
    (hBeta : 0 < beta)
    (hForward : ∀ path, 0 < protocol.forward path)
    (hReverse : ∀ path, 0 < protocol.reverseAligned path) :
    HasCrooksRelation protocol beta deltaFreeEnergy
      (fun path =>
        deltaFreeEnergy + pathwiseEntropyProduction protocol path / beta) := by
  refine ⟨hBeta, fun path => ?_⟩
  have hDissipated :
      beta * (deltaFreeEnergy + pathwiseEntropyProduction protocol path / beta -
          deltaFreeEnergy) =
        pathwiseEntropyProduction protocol path := by
    field_simp
    ring
  rw [hDissipated]
  exact detailedFluctuation_identity protocol hForward hReverse path

/-! ## Local detailed balance and finite currents -/

/-- Oriented one-step probability current. -/
def probabilityCurrent (law : FiniteLaw State)
    (kernel : FiniteKernel State State) (source target : State) : ℝ :=
  law source * kernel source target - law target * kernel target source

/-- Probability current is antisymmetric under edge reversal. -/
theorem probabilityCurrent_antisymm
    (law : FiniteLaw State) (kernel : FiniteKernel State State)
    (source target : State) :
    probabilityCurrent law kernel source target =
      -probabilityCurrent law kernel target source := by
  simp [probabilityCurrent]

/-- Detailed balance cancels every local stationary current. -/
theorem localDetailedBalance_current_zero
    (law : FiniteLaw State) (kernel : FiniteKernel State State)
    (hReversible : IsReversible law kernel) (source target : State) :
    probabilityCurrent law kernel source target = 0 := by
  unfold probabilityCurrent
  rw [hReversible source target, sub_self]

/-- Supported local log affinity, kept separate from any physical heat
interpretation. -/
noncomputable def localAffinity (law : FiniteLaw State)
    (kernel : FiniteKernel State State) (source target : State) : ℝ :=
  Real.log ((law source * kernel source target) /
    (law target * kernel target source))

/-- A zero reverse edge rate is an explicit totalized-log boundary. -/
theorem localAffinity_zero_reverseRate_boundary
    (law : FiniteLaw State) (kernel : FiniteKernel State State)
    (source target : State) (hZero : kernel target source = 0) :
    localAffinity law kernel source target = 0 := by
  simp [localAffinity, hZero]

/-! ## Reversible one-step KL dissipation -/

/-- Detailed balance implies stationarity for a normalized finite kernel. -/
theorem isInvariant_of_isReversible
    (law : FiniteLaw State) (kernel : FiniteKernel State State)
    (hReversible : IsReversible law kernel) :
    FEP.FiniteMarkovDynamics.IsInvariant law kernel := by
  unfold FEP.FiniteMarkovDynamics.IsInvariant
  apply FiniteLaw.ext_mass
  funext target
  simp only [FiniteKernel.predictive_mass]
  calc
    (∑ source, law source * kernel source target) =
        ∑ source, law target * kernel target source := by
      apply Finset.sum_congr rfl
      intro source _
      exact hReversible source target
    _ = law target * ∑ source, kernel target source := by
      rw [Finset.mul_sum]
    _ = law target := by rw [kernel.sum_one, mul_one]

/-- One reversible Markov step cannot increase KL to its stationary law.
Strict support is explicit because this theorem reuses the finite logarithmic
data-processing proof rather than an extended-real divergence. -/
theorem reversibleKL_oneStep_dissipation [Nonempty State]
    (actual stationary : FiniteLaw State)
    (kernel : FiniteKernel State State)
    (hActual : ∀ state, 0 < actual state)
    (hStationary : ∀ state, 0 < stationary state)
    (hKernel : ∀ source target, 0 < kernel source target)
    (hReversible : IsReversible stationary kernel) :
    finiteKL (kernel.predictive actual) stationary ≤
      finiteKL actual stationary := by
  have hData := finiteChannel_dataProcessing actual stationary kernel
    hActual hStationary hKernel
  have hInvariant := isInvariant_of_isReversible stationary kernel hReversible
  change kernel.predictive stationary = stationary at hInvariant
  rw [hInvariant] at hData
  exact hData

/-- The identity kernel gives an exact reversible equality boundary. -/
theorem identityKernel_KL_equality [DecidableEq State]
    (actual stationary : FiniteLaw State) :
    finiteKL
        ((FiniteKernel.identity : FiniteKernel State State).predictive actual)
        stationary = finiteKL actual stationary := by
  rw [FiniteKernel.predictive_identity]

/-! ## Concrete irreversible positive-production witness -/

/-- Full-support Boolean forward path law with masses `3/4` and `1/4`. -/
noncomputable def irreversibleForward : FiniteLaw Bool where
  mass path := if path then 3 / 4 else 1 / 4
  nonneg path := by cases path <;> norm_num
  sum_one := by norm_num [Fintype.sum_bool]

/-- Full-support Boolean aligned reverse law with the masses exchanged. -/
noncomputable def irreversibleReverse : FiniteLaw Bool where
  mass path := if path then 1 / 4 else 3 / 4
  nonneg path := by cases path <;> norm_num
  sum_one := by norm_num [Fintype.sum_bool]

/-- Concrete two-path protocol with identity path reversal and unequal laws. -/
noncomputable def irreversibleBoolProtocol : FinitePathProtocol Bool where
  forward := irreversibleForward
  reverseAligned := irreversibleReverse
  reversal := id
  reversal_involutive := by intro path; rfl

/-- The forward and reverse Boolean path laws are genuinely distinct. -/
theorem irreversibleForward_ne_reverse :
    irreversibleForward ≠ irreversibleReverse := by
  intro hEqual
  have hTrue := congrFun (congrArg FiniteLaw.mass hEqual) true
  norm_num [irreversibleForward, irreversibleReverse] at hTrue

/-- The explicit irreversible Boolean witness has strictly positive mean
entropy production. -/
theorem irreversibleBool_entropyProduction_pos :
    0 < entropyProduction irreversibleBoolProtocol := by
  have hNonneg := finiteKL_nonneg irreversibleForward irreversibleReverse
  have hNe : finiteKL irreversibleForward irreversibleReverse ≠ 0 := by
    intro hZero
    exact irreversibleForward_ne_reverse
      ((finiteKL_eq_zero_iff irreversibleForward irreversibleReverse).mp hZero)
  exact lt_of_le_of_ne hNonneg (Ne.symm hNe)

/-! ## Crooks witness and the strictness of the Jarzynski premise -/

/-- Nonconstant Boolean work `± log 3` for the irreversible protocol. -/
noncomputable def irreversibleCrooksWork (path : Bool) : ℝ :=
  if path then Real.log 3 else -Real.log 3

/-- The irreversible Boolean protocol satisfies the Crooks relation at `β = 1`,
`ΔF = 0` with the nonconstant work `± log 3`. -/
theorem irreversibleBool_crooks :
    HasCrooksRelation irreversibleBoolProtocol 1 0 irreversibleCrooksWork := by
  have hLog : Real.exp (Real.log 3) = 3 := Real.exp_log (by norm_num)
  refine ⟨one_pos, fun path => ?_⟩
  cases path <;>
    norm_num [irreversibleBoolProtocol, irreversibleCrooksWork,
      irreversibleForward, irreversibleReverse, Real.exp_neg, hLog]

/-- The Crooks witness work genuinely varies across paths. -/
theorem irreversibleCrooksWork_nonconstant :
    irreversibleCrooksWork true ≠ irreversibleCrooksWork false := by
  have hPos : 0 < Real.log 3 := Real.log_pos (by norm_num)
  simp only [irreversibleCrooksWork, ↓reduceIte, Bool.false_eq_true]
  intro hEqual
  linarith

/-- The Jarzynski normalization is strictly weaker than Crooks: zero work
normalizes the irreversible forward law yet violates the pathwise relation. -/
theorem jarzynski_without_crooks :
    HasJarzynskiNormalization irreversibleBoolProtocol.forward 1 0
        (fun _ => 0) ∧
      ¬ HasCrooksRelation irreversibleBoolProtocol 1 0 (fun _ => 0) := by
  refine ⟨⟨one_pos, ?_⟩, ?_⟩
  · simp only [sub_self, mul_zero, Real.exp_zero, mul_one]
    exact irreversibleBoolProtocol.forward.sum_one
  · rintro ⟨_, hCrooks⟩
    have hTrue := hCrooks true
    simp only [irreversibleBoolProtocol, irreversibleForward,
      irreversibleReverse, ↓reduceIte, sub_self, mul_zero, Real.exp_zero,
      mul_one] at hTrue
    norm_num at hTrue

/-- The Jarzynski premise is substantive: constant unit work at `β = 1`,
`ΔF = 0` violates it on the irreversible forward law. -/
theorem irreversibleForward_unitWork_not_jarzynski :
    ¬ HasJarzynskiNormalization irreversibleBoolProtocol.forward 1 0
        (fun _ => 1) := by
  rintro ⟨_, hNormalization⟩
  have hSum : (∑ path, irreversibleBoolProtocol.forward path *
      Real.exp (-1 * ((1 : ℝ) - 0))) = Real.exp (-1) := by
    rw [← Finset.sum_mul, irreversibleBoolProtocol.forward.sum_one]
    norm_num
  have hLt : Real.exp (-1) < 1 := Real.exp_lt_one_iff.2 (by norm_num)
  rw [hSum] at hNormalization
  linarith

/-! ## Markov path laws -/

section MarkovPaths

variable {S : Type*} [Fintype S]

/-- Mass of a length-`n+1` trajectory under a homogeneous Markov chain:
initial mass times the product of stage transition masses. -/
def markovPathMass (kernel : FiniteKernel S S) (initial : FiniteLaw S) (n : ℕ)
    (path : Fin (n + 1) → S) : ℝ :=
  initial (path 0) * ∏ t : Fin n, kernel (path t.castSucc) (path t.succ)

/-- Mass of the same trajectory read backwards, in forward coordinates, under a
chain driven by `reverse` and started from `final` at the last time. -/
def markovReverseMass (reverse : FiniteKernel S S) (final : FiniteLaw S) (n : ℕ)
    (path : Fin (n + 1) → S) : ℝ :=
  final (path (Fin.last n)) * ∏ t : Fin n, reverse (path t.succ) (path t.castSucc)

/-- Appending one step multiplies the path mass by one transition mass. -/
theorem markovPathMass_snoc (kernel : FiniteKernel S S) (initial : FiniteLaw S)
    (n : ℕ) (path : Fin (n + 1) → S) (next : S) :
    markovPathMass kernel initial (n + 1)
        (Fin.snoc (α := fun _ => S) path next) =
      markovPathMass kernel initial n path * kernel (path (Fin.last n)) next := by
  unfold markovPathMass
  rw [Fin.prod_univ_castSucc]
  have hStage : ∀ t : Fin n,
      kernel ((Fin.snoc (α := fun _ => S) path next) t.castSucc.castSucc)
          ((Fin.snoc (α := fun _ => S) path next) t.castSucc.succ) =
        kernel (path t.castSucc) (path t.succ) := by
    intro t
    rw [Fin.succ_castSucc, Fin.snoc_castSucc, Fin.snoc_castSucc]
  have hZero : (Fin.snoc (α := fun _ => S) path next) (0 : Fin (n + 2)) =
      path 0 := by
    rw [← Fin.castSucc_zero, Fin.snoc_castSucc]
  have hLast : (Fin.snoc (α := fun _ => S) path next)
      (Fin.last n).castSucc = path (Fin.last n) := Fin.snoc_castSucc _ _ _
  have hNext : (Fin.snoc (α := fun _ => S) path next)
      (Fin.last n).succ = next := by
    rw [Fin.succ_last]
    exact Fin.snoc_last _ _
  rw [Finset.prod_congr rfl (fun t _ => hStage t), hZero, hLast, hNext]
  ring

/-- Every Markov path mass is nonnegative. -/
theorem markovPathMass_nonneg (kernel : FiniteKernel S S)
    (initial : FiniteLaw S) (n : ℕ) (path : Fin (n + 1) → S) :
    0 ≤ markovPathMass kernel initial n path :=
  mul_nonneg (initial.nonneg _)
    (Finset.prod_nonneg fun _ _ => kernel.nonneg _ _)

/-- Total Markov path mass is one, by induction on the horizon. -/
theorem markovPathMass_sum_one (kernel : FiniteKernel S S)
    (initial : FiniteLaw S) (n : ℕ) :
    ∑ path : Fin (n + 1) → S, markovPathMass kernel initial n path = 1 := by
  induction n with
  | zero =>
      have hBase : ∀ path : Fin 1 → S,
          markovPathMass kernel initial 0 path = initial (path 0) := by
        intro path
        simp [markovPathMass]
      simp_rw [hBase]
      rw [Fintype.sum_equiv (Equiv.funUnique (Fin 1) S) _ (fun s => initial s)
        (fun path => by simp)]
      exact initial.sum_one
  | succ n ih =>
      rw [← (Fin.snocEquiv fun _ : Fin (n + 2) => S).sum_comp, Fintype.sum_prod_type]
      have hSnoc : ∀ (next : S) (path : Fin (n + 1) → S),
          markovPathMass kernel initial (n + 1)
              ((Fin.snocEquiv fun _ : Fin (n + 2) => S) (next, path)) =
            markovPathMass kernel initial n path *
              kernel (path (Fin.last n)) next := by
        intro next path
        exact markovPathMass_snoc kernel initial n path next
      simp_rw [hSnoc]
      rw [Finset.sum_comm]
      calc
        (∑ path : Fin (n + 1) → S, ∑ next : S,
            markovPathMass kernel initial n path *
              kernel (path (Fin.last n)) next) =
            ∑ path : Fin (n + 1) → S, markovPathMass kernel initial n path := by
          apply Finset.sum_congr rfl
          intro path _
          rw [← Finset.mul_sum, (kernel.sum_one _), mul_one]
        _ = 1 := ih

/-- Forward Markov path law on `Fin (n+1) → S`, normalized by
`markovPathMass_sum_one`. -/
def markovPathLaw (kernel : FiniteKernel S S) (initial : FiniteLaw S) (n : ℕ) :
    FiniteLaw (Fin (n + 1) → S) where
  mass := markovPathMass kernel initial n
  nonneg := markovPathMass_nonneg kernel initial n
  sum_one := markovPathMass_sum_one kernel initial n

/-- Reversal of a trajectory: read it backwards. -/
def pathReverse (n : ℕ) (path : Fin (n + 1) → S) : Fin (n + 1) → S :=
  path ∘ Fin.rev

omit [Fintype S] in
/-- Trajectory reversal is an involution. -/
theorem pathReverse_involutive (n : ℕ) :
    Function.Involutive (pathReverse (S := S) n) := by
  intro path
  funext i
  simp [pathReverse]

/-- The aligned reverse mass is the reverse chain's forward mass at the
reversed trajectory. -/
theorem markovReverseMass_eq (reverse : FiniteKernel S S) (final : FiniteLaw S)
    (n : ℕ) (path : Fin (n + 1) → S) :
    markovReverseMass reverse final n path =
      markovPathMass reverse final n (pathReverse n path) := by
  unfold markovReverseMass markovPathMass pathReverse
  simp only [Function.comp_apply, Fin.rev_zero, Fin.rev_castSucc, Fin.rev_succ]
  congr 1
  exact (Equiv.prod_comp Fin.revPerm
    fun t => reverse (path t.succ) (path t.castSucc)).symm

/-- Reverse-driven path law, expressed in forward-path coordinates. -/
def markovReversePathLaw (reverse : FiniteKernel S S) (final : FiniteLaw S)
    (n : ℕ) : FiniteLaw (Fin (n + 1) → S) where
  mass := markovReverseMass reverse final n
  nonneg path := by
    rw [markovReverseMass_eq]
    exact markovPathMass_nonneg reverse final n _
  sum_one := by
    simp_rw [markovReverseMass_eq]
    exact (Equiv.sum_comp (pathReverse_involutive (S := S) n).toPerm
      (markovPathMass reverse final n)).trans
      (markovPathMass_sum_one reverse final n)

/-- The forward Markov path law paired with a reverse-driven chain, with
trajectory reversal as the involution. -/
noncomputable def markovPathProtocol
    (kernel : FiniteKernel S S) (initial : FiniteLaw S)
    (reverse : FiniteKernel S S) (final : FiniteLaw S) (n : ℕ) :
    FinitePathProtocol (Fin (n + 1) → S) where
  forward := markovPathLaw kernel initial n
  reverseAligned := markovReversePathLaw reverse final n
  reversal := pathReverse n
  reversal_involutive := pathReverse_involutive n

/-- Supported trajectories have positive forward mass. -/
theorem markovPathMass_pos (kernel : FiniteKernel S S) (initial : FiniteLaw S)
    (hInitial : ∀ s, 0 < initial s) (hKernel : ∀ a b, 0 < kernel a b)
    (n : ℕ) (path : Fin (n + 1) → S) :
    0 < markovPathMass kernel initial n path :=
  mul_pos (hInitial _) (Finset.prod_pos fun _ _ => hKernel _ _)

/-- Supported trajectories have positive aligned reverse mass. -/
theorem markovReverseMass_pos (reverse : FiniteKernel S S) (final : FiniteLaw S)
    (hFinal : ∀ s, 0 < final s) (hReverse : ∀ a b, 0 < reverse a b)
    (n : ℕ) (path : Fin (n + 1) → S) :
    0 < markovReverseMass reverse final n path :=
  mul_pos (hFinal _) (Finset.prod_pos fun _ _ => hReverse _ _)

/-- Pathwise entropy production of a Markov path protocol is a boundary log
ratio plus the sum of stage log ratios `log (K_{x_t x_{t+1}} / R_{x_{t+1} x_t})`. -/
theorem pathwiseEntropyProduction_markov
    (kernel reverse : FiniteKernel S S) (initial final : FiniteLaw S)
    (hInitial : ∀ s, 0 < initial s) (hFinal : ∀ s, 0 < final s)
    (hKernel : ∀ a b, 0 < kernel a b) (hReverse : ∀ a b, 0 < reverse a b)
    (n : ℕ) (path : Fin (n + 1) → S) :
    pathwiseEntropyProduction
        (markovPathProtocol kernel initial reverse final n) path =
      Real.log (initial (path 0) / final (path (Fin.last n))) +
        ∑ t : Fin n, Real.log
          (kernel (path t.castSucc) (path t.succ) /
            reverse (path t.succ) (path t.castSucc)) := by
  have hRatio : pathRatio (markovPathProtocol kernel initial reverse final n)
      path = (initial (path 0) / final (path (Fin.last n))) *
        ∏ t : Fin n, (kernel (path t.castSucc) (path t.succ) /
          reverse (path t.succ) (path t.castSucc)) := by
    change markovPathMass kernel initial n path /
      markovReverseMass reverse final n path = _
    unfold markovPathMass markovReverseMass
    rw [Finset.prod_div_distrib, mul_div_mul_comm]
  unfold pathwiseEntropyProduction
  rw [hRatio, Real.log_mul (div_pos (hInitial _) (hFinal _)).ne'
    (Finset.prod_pos fun _ _ => div_pos (hKernel _ _) (hReverse _ _)).ne',
    Real.log_prod fun _ _ => (div_pos (hKernel _ _) (hReverse _ _)).ne']

/-- Path KL splits into the boundary term plus the sum of expected stage log
ratios, for every horizon `n`. -/
theorem entropyProduction_markov_decomposition
    (kernel reverse : FiniteKernel S S) (initial final : FiniteLaw S)
    (hInitial : ∀ s, 0 < initial s) (hFinal : ∀ s, 0 < final s)
    (hKernel : ∀ a b, 0 < kernel a b) (hReverse : ∀ a b, 0 < reverse a b)
    (n : ℕ) :
    entropyProduction (markovPathProtocol kernel initial reverse final n) =
      (∑ path : Fin (n + 1) → S, markovPathLaw kernel initial n path *
          Real.log (initial (path 0) / final (path (Fin.last n)))) +
        ∑ t : Fin n, ∑ path : Fin (n + 1) → S,
          markovPathLaw kernel initial n path *
            Real.log (kernel (path t.castSucc) (path t.succ) /
              reverse (path t.succ) (path t.castSucc)) := by
  rw [entropyProduction_eq_expected_logRatio _
    (fun path => markovPathMass_pos kernel initial hInitial hKernel n path)
    (fun path => by
      change 0 < markovReverseMass reverse final n path
      exact markovReverseMass_pos reverse final hFinal hReverse n path)]
  have hPath : ∀ path : Fin (n + 1) → S,
      (markovPathProtocol kernel initial reverse final n).forward path =
        markovPathLaw kernel initial n path := fun _ => rfl
  simp_rw [hPath, pathwiseEntropyProduction_markov kernel reverse initial final
    hInitial hFinal hKernel hReverse, mul_add, Finset.mul_sum]
  rw [Finset.sum_add_distrib, Finset.sum_comm (s := Finset.univ)]

/-! ### One-step paths -/

/-- A two-point trajectory sums as a double sum over its endpoints. -/
theorem sum_pathTwo (g : (Fin 2 → S) → ℝ) :
    ∑ path : Fin 2 → S, g path = ∑ i : S, ∑ j : S, g ![i, j] := by
  rw [← (finTwoArrowEquiv S).symm.sum_comp, Fintype.sum_prod_type]
  rfl

/-- One-step forward path mass is the joint mass `π₀ i K_{ij}`. -/
theorem markovPathMass_one (kernel : FiniteKernel S S) (initial : FiniteLaw S)
    (path : Fin 2 → S) :
    markovPathMass kernel initial 1 path = initial (path 0) * kernel (path 0) (path 1) := by
  simp [markovPathMass]

/-- One-step aligned reverse mass is `ρ_j R_{ji}`. -/
theorem markovReverseMass_one (reverse : FiniteKernel S S) (final : FiniteLaw S)
    (path : Fin 2 → S) :
    markovReverseMass reverse final 1 path = final (path 1) * reverse (path 1) (path 0) := by
  simp [markovReverseMass]

/-- One-step path KL as a double sum of joint-weighted log ratios. -/
theorem entropyProduction_markov_oneStep
    (kernel reverse : FiniteKernel S S) (initial final : FiniteLaw S)
    (hInitial : ∀ s, 0 < initial s) (hFinal : ∀ s, 0 < final s)
    (hKernel : ∀ a b, 0 < kernel a b) (hReverse : ∀ a b, 0 < reverse a b) :
    entropyProduction (markovPathProtocol kernel initial reverse final 1) =
      ∑ i : S, ∑ j : S, initial i * kernel i j *
        Real.log (initial i * kernel i j / (final j * reverse j i)) := by
  rw [entropyProduction_eq_expected_logRatio _
    (fun path => markovPathMass_pos kernel initial hInitial hKernel 1 path)
    (fun path => by
      change 0 < markovReverseMass reverse final 1 path
      exact markovReverseMass_pos reverse final hFinal hReverse 1 path),
    sum_pathTwo]
  apply Finset.sum_congr rfl
  intro i _
  apply Finset.sum_congr rfl
  intro j _
  change markovPathMass kernel initial 1 ![i, j] *
    Real.log (markovPathMass kernel initial 1 ![i, j] /
      markovReverseMass reverse final 1 ![i, j]) = _
  rw [markovPathMass_one, markovReverseMass_one]
  simp

/-- One-step path KL as boundary entropy term plus the stage log-ratio sum. -/
theorem entropyProduction_markov_oneStep_split
    (kernel reverse : FiniteKernel S S) (initial final : FiniteLaw S)
    (hInitial : ∀ s, 0 < initial s) (hFinal : ∀ s, 0 < final s)
    (hKernel : ∀ a b, 0 < kernel a b) (hReverse : ∀ a b, 0 < reverse a b) :
    entropyProduction (markovPathProtocol kernel initial reverse final 1) =
      (∑ i : S, initial i * Real.log (initial i) -
          ∑ j : S, kernel.predictive initial j * Real.log (final j)) +
        ∑ i : S, ∑ j : S, initial i * kernel i j *
          Real.log (kernel i j / reverse j i) := by
  rw [entropyProduction_markov_oneStep kernel reverse initial final hInitial
    hFinal hKernel hReverse]
  have hTerm : ∀ i j : S, initial i * kernel i j *
      Real.log (initial i * kernel i j / (final j * reverse j i)) =
        (initial i * kernel i j * Real.log (initial i) -
          initial i * kernel i j * Real.log (final j)) +
        initial i * kernel i j * Real.log (kernel i j / reverse j i) := by
    intro i j
    have hI := (hInitial i).ne'
    have hF := (hFinal j).ne'
    have hK := (hKernel i j).ne'
    have hR := (hReverse j i).ne'
    rw [Real.log_div (mul_ne_zero hI hK) (mul_ne_zero hF hR),
      Real.log_div hK hR, Real.log_mul hI hK, Real.log_mul hF hR]
    ring
  have hBoundaryStart : ∑ i : S, ∑ j : S, initial i * kernel i j *
      Real.log (initial i) = ∑ i : S, initial i * Real.log (initial i) := by
    apply Finset.sum_congr rfl
    intro i _
    calc
      ∑ j : S, initial i * kernel i j * Real.log (initial i) =
          (initial i * ∑ j : S, kernel i j) * Real.log (initial i) := by
        rw [Finset.mul_sum, Finset.sum_mul]
      _ = initial i * Real.log (initial i) := by rw [kernel.sum_one, mul_one]
  have hBoundaryEnd : ∑ i : S, ∑ j : S, initial i * kernel i j *
      Real.log (final j) =
        ∑ j : S, kernel.predictive initial j * Real.log (final j) := by
    rw [Finset.sum_comm]
    apply Finset.sum_congr rfl
    intro j _
    rw [FiniteKernel.predictive_mass, Finset.sum_mul]
  simp_rw [hTerm, Finset.sum_add_distrib, Finset.sum_sub_distrib]
  rw [hBoundaryStart, hBoundaryEnd]

/-! ### Stationary one-step production and detailed balance -/

/-- Stationary Schnakenberg form: when both path endpoints carry the same
supported law `π`, one-step path KL against the same kernel run on the
reversed trajectory is `∑ π_i K_ij log (π_i K_ij / (π_j K_ji))`. -/
theorem entropyProduction_markov_schnakenberg
    (kernel : FiniteKernel S S) (law : FiniteLaw S)
    (hLaw : ∀ s, 0 < law s) (hKernel : ∀ a b, 0 < kernel a b) :
    entropyProduction (markovPathProtocol kernel law kernel law 1) =
      ∑ i : S, ∑ j : S, law i * kernel i j *
        Real.log (law i * kernel i j / (law j * kernel j i)) :=
  entropyProduction_markov_oneStep kernel kernel law law hLaw hLaw hKernel
    hKernel

/-- The Schnakenberg form is the `localAffinity`-weighted probability flux. -/
theorem entropyProduction_markov_eq_localAffinity
    (kernel : FiniteKernel S S) (law : FiniteLaw S)
    (hLaw : ∀ s, 0 < law s) (hKernel : ∀ a b, 0 < kernel a b) :
    entropyProduction (markovPathProtocol kernel law kernel law 1) =
      ∑ i : S, ∑ j : S, law i * kernel i j * localAffinity law kernel i j :=
  entropyProduction_markov_schnakenberg kernel law hLaw hKernel

/-- For an invariant supported law the boundary entropy term vanishes, leaving
only the stage log-ratio sum `∑ π_i K_ij log (K_ij / K_ji)`. -/
theorem entropyProduction_markov_stationary
    (kernel : FiniteKernel S S) (law : FiniteLaw S)
    (hLaw : ∀ s, 0 < law s) (hKernel : ∀ a b, 0 < kernel a b)
    (hInvariant : IsInvariant law kernel) :
    entropyProduction (markovPathProtocol kernel law kernel law 1) =
      ∑ i : S, ∑ j : S, law i * kernel i j *
        Real.log (kernel i j / kernel j i) := by
  rw [entropyProduction_markov_oneStep_split kernel kernel law law hLaw hLaw
    hKernel hKernel]
  have hInv : kernel.predictive law = law := hInvariant
  rw [hInv, sub_self, zero_add]

/-- Under detailed balance the forward and reversed one-step path laws agree. -/
theorem markovPathLaw_eq_reverse_of_reversible
    (kernel : FiniteKernel S S) (law : FiniteLaw S)
    (hReversible : IsReversible law kernel) :
    markovPathLaw kernel law 1 = markovReversePathLaw kernel law 1 := by
  apply FiniteLaw.ext_mass
  funext path
  change markovPathMass kernel law 1 path = markovReverseMass kernel law 1 path
  rw [markovPathMass_one, markovReverseMass_one]
  exact hReversible (path 0) (path 1)

/-- Detailed balance gives exactly zero one-step path entropy production, with
no support hypothesis. -/
theorem entropyProduction_markov_reversible_zero
    (kernel : FiniteKernel S S) (law : FiniteLaw S)
    (hReversible : IsReversible law kernel) :
    entropyProduction (markovPathProtocol kernel law kernel law 1) = 0 := by
  unfold entropyProduction
  change finiteKL (markovPathLaw kernel law 1)
    (markovReversePathLaw kernel law 1) = 0
  rw [markovPathLaw_eq_reverse_of_reversible kernel law hReversible]
  exact finiteKL_self _

/-- Detailed balance cancels every local affinity (zero numerator/denominator
ratio is `1`, or the totalized `0` at a zero edge). -/
theorem localAffinity_zero_of_reversible
    (kernel : FiniteKernel S S) (law : FiniteLaw S)
    (hReversible : IsReversible law kernel) (source target : S) :
    localAffinity law kernel source target = 0 := by
  unfold localAffinity
  rw [hReversible source target]
  by_cases h : law target * kernel target source = 0
  · simp [h]
  · rw [div_self h, Real.log_one]

/-! ### Bayesian time-reversed kernel -/

/-- Time-reversed kernel of a chain against a supported invariant law:
`K†_{ab} = π_b K_{ba} / π_a`. -/
noncomputable def reversedKernel (law : FiniteLaw S) (kernel : FiniteKernel S S)
    (hLaw : ∀ s, 0 < law s) (hInvariant : IsInvariant law kernel) :
    FiniteKernel S S where
  mass a b := law b * kernel b a / law a
  nonneg a b := div_nonneg (mul_nonneg (law.nonneg b) (kernel.nonneg b a)) (hLaw a).le
  sum_one a := by
    have hInv : kernel.predictive law a = law a := by
      rw [show kernel.predictive law = law from hInvariant]
    rw [FiniteKernel.predictive_mass] at hInv
    rw [← Finset.sum_div, hInv]
    exact div_self (hLaw a).ne'

/-- The reversed kernel satisfies detailed balance against the original. -/
theorem reversedKernel_detailedBalance (law : FiniteLaw S)
    (kernel : FiniteKernel S S) (hLaw : ∀ s, 0 < law s)
    (hInvariant : IsInvariant law kernel) (a b : S) :
    law a * reversedKernel law kernel hLaw hInvariant a b =
      law b * kernel b a := by
  change law a * (law b * kernel b a / law a) = _
  field_simp [(hLaw a).ne']

/-- Detailed balance makes the reversed kernel the kernel itself. -/
theorem reversedKernel_eq_of_reversible (law : FiniteLaw S)
    (kernel : FiniteKernel S S) (hLaw : ∀ s, 0 < law s)
    (hReversible : IsReversible law kernel) :
    reversedKernel law kernel hLaw (isInvariant_of_isReversible law kernel hReversible) =
      kernel := by
  apply FiniteKernel.ext_mass
  funext a b
  change law b * kernel b a / law a = kernel a b
  rw [div_eq_iff (hLaw a).ne', ← hReversible a b]
  ring

/-- Telescoping of stage ratios of a positive function along a trajectory. -/
theorem prod_stage_ratio_telescope (n : ℕ) (f : Fin (n + 1) → ℝ)
    (hf : ∀ i, f i ≠ 0) :
    ∏ t : Fin n, f t.castSucc / f t.succ = f 0 / f (Fin.last n) := by
  induction n with
  | zero => simp [div_self (hf 0)]
  | succ n ih =>
      rw [Fin.prod_univ_castSucc]
      have hIh := ih (fun i => f i.castSucc) (fun i => hf _)
      simp only [Fin.succ_castSucc] at hIh ⊢
      rw [hIh]
      simp only [Fin.castSucc_zero, Fin.succ_last]
      have h1 := hf (Fin.last n).castSucc
      have h2 := hf (Fin.last (n + 1))
      field_simp

/-- Stationary time-reversal duality for every horizon: the chain driven by the
reversed kernel and started from `π`, read backwards, has exactly the forward
path mass of the original chain started from `π`. -/
theorem markovReverseMass_reversedKernel (law : FiniteLaw S)
    (kernel : FiniteKernel S S) (hLaw : ∀ s, 0 < law s)
    (hInvariant : IsInvariant law kernel) (n : ℕ) (path : Fin (n + 1) → S) :
    markovReverseMass (reversedKernel law kernel hLaw hInvariant) law n path =
      markovPathMass kernel law n path := by
  have hStage : ∀ t : Fin n,
      reversedKernel law kernel hLaw hInvariant (path t.succ) (path t.castSucc) =
        (law (path t.castSucc) / law (path t.succ)) *
          kernel (path t.castSucc) (path t.succ) := by
    intro t
    change law (path t.castSucc) * kernel (path t.castSucc) (path t.succ) /
      law (path t.succ) = _
    ring
  unfold markovReverseMass markovPathMass
  rw [Finset.prod_congr rfl (fun t _ => hStage t), Finset.prod_mul_distrib,
    prod_stage_ratio_telescope n (fun i => law (path i)) (fun i => (hLaw _).ne')]
  have hLast := (hLaw (path (Fin.last n))).ne'
  field_simp

/-- Under invariance the reversed-kernel chain reproduces the forward path law. -/
theorem markovReversePathLaw_reversedKernel (law : FiniteLaw S)
    (kernel : FiniteKernel S S) (hLaw : ∀ s, 0 < law s)
    (hInvariant : IsInvariant law kernel) (n : ℕ) :
    markovReversePathLaw (reversedKernel law kernel hLaw hInvariant) law n =
      markovPathLaw kernel law n := by
  apply FiniteLaw.ext_mass
  funext path
  exact markovReverseMass_reversedKernel law kernel hLaw hInvariant n path

/-- The Bayesian time reversal of a stationary chain has zero path entropy
production against the chain itself: reversal by `K†` is the identity on laws. -/
theorem entropyProduction_markov_reversedKernel_zero (law : FiniteLaw S)
    (kernel : FiniteKernel S S) (hLaw : ∀ s, 0 < law s)
    (hInvariant : IsInvariant law kernel) (n : ℕ) :
    entropyProduction (markovPathProtocol kernel law
      (reversedKernel law kernel hLaw hInvariant) law n) = 0 := by
  unfold entropyProduction
  change finiteKL (markovPathLaw kernel law n)
    (markovReversePathLaw (reversedKernel law kernel hLaw hInvariant) law n) = 0
  rw [markovReversePathLaw_reversedKernel]
  exact finiteKL_self _

end MarkovPaths

/-! ## Irreversible three-state stationary chain -/

/-- Full-support biased three-cycle: stay or step back with mass `1/4`, step
forward with mass `1/2`. -/
noncomputable def biasedCycleKernel : FiniteKernel (Fin 3) (Fin 3) where
  mass := ![![1 / 4, 1 / 2, 1 / 4], ![1 / 4, 1 / 4, 1 / 2],
    ![1 / 2, 1 / 4, 1 / 4]]
  nonneg i j := by fin_cases i <;> fin_cases j <;> norm_num
  sum_one i := by
    fin_cases i <;> norm_num [Fin.sum_univ_succ]

/-- The biased cycle is strictly positive. -/
theorem biasedCycleKernel_pos (i j : Fin 3) : 0 < biasedCycleKernel i j := by
  fin_cases i <;> fin_cases j <;> norm_num [biasedCycleKernel]

/-- The uniform law is invariant for the doubly stochastic biased cycle. -/
theorem biasedCycle_invariant :
    IsInvariant (FiniteLaw.uniform : FiniteLaw (Fin 3)) biasedCycleKernel := by
  apply FiniteLaw.ext_mass
  funext j
  rw [FiniteKernel.predictive_mass]
  fin_cases j <;>
    norm_num [biasedCycleKernel, FiniteLaw.uniform, Fin.sum_univ_succ]

/-- The biased cycle violates detailed balance against its stationary law. -/
theorem biasedCycle_not_reversible :
    ¬ IsReversible (FiniteLaw.uniform : FiniteLaw (Fin 3)) biasedCycleKernel := by
  intro hReversible
  have h := hReversible 0 1
  norm_num [biasedCycleKernel, FiniteLaw.uniform] at h

/-- Exact stationary one-step entropy production of the biased cycle:
`(1/4) log 2`. -/
theorem biasedCycle_entropyProduction :
    entropyProduction (markovPathProtocol biasedCycleKernel
      FiniteLaw.uniform biasedCycleKernel FiniteLaw.uniform 1) =
      Real.log 2 / 4 := by
  rw [entropyProduction_markov_stationary biasedCycleKernel FiniteLaw.uniform
    (fun _ => by simp [FiniteLaw.uniform]) biasedCycleKernel_pos
    biasedCycle_invariant]
  norm_num [Fin.sum_univ_succ, biasedCycleKernel, FiniteLaw.uniform]
  have hHalf : Real.log (1 / 2 : ℝ) = -Real.log 2 := by
    rw [one_div, Real.log_inv]
  rw [hHalf]
  ring

/-- The biased cycle has strictly positive stationary entropy production. -/
theorem biasedCycle_entropyProduction_pos :
    0 < entropyProduction (markovPathProtocol biasedCycleKernel
      FiniteLaw.uniform biasedCycleKernel FiniteLaw.uniform 1) := by
  rw [biasedCycle_entropyProduction]
  have := Real.log_pos (by norm_num : (1 : ℝ) < 2)
  linarith

/-! ## Landauer erasure from path entropy production -/

section LandauerErasure

/-- Expectation of a function of one coordinate equals the fiber-mass weighted
sum over that coordinate's values. -/
theorem sum_mul_comp_eq_sum_fiber (law : FiniteLaw Path) (coordinate : Path → Bool)
    (g : Bool → ℝ) :
    ∑ path, law path * g (coordinate path) =
      ∑ b, (∑ path with coordinate path = b, law path) * g b := by
  rw [← Finset.sum_fiberwise Finset.univ coordinate
    (fun path => law path * g (coordinate path))]
  apply Finset.sum_congr rfl
  intro b _
  rw [Finset.sum_mul]
  apply Finset.sum_congr rfl
  intro path hPath
  rw [(Finset.mem_filter.mp hPath).2]

/-- A finite one-bit erasure model.  Every modelling assumption is a named
field:

* `initial_marginal` / `final_marginal`: the forward path law has initial-bit
  law `prior` and final-bit law `finalLaw`.
* `reverse_support`: the aligned reverse law charges every forward-supported
  path (absolute continuity, needed for a finite log ratio).
* `localDetailedBalance`: the standard stochastic-thermodynamics encoding of
  heat.  On forward-supported paths the pathwise entropy production
  `log (P_F / P_R)` equals `β Q` (entropy flow into the bath at inverse
  temperature `β`) plus the system surprisal change
  `log prior(x₀) - log finalLaw(x_T)`, i.e. `σ = β Q + Δ s_sys`.

Nothing here assumes the second law; nonnegativity of mean production comes
from `entropyProduction_nonneg`. -/
structure ErasureModel (Path : Type*) [Fintype Path] extends
    FinitePathProtocol Path where
  prior : FiniteLaw Bool
  finalLaw : FiniteLaw Bool
  initialBit : Path → Bool
  finalBit : Path → Bool
  beta : ℝ
  heat : Path → ℝ
  beta_pos : 0 < beta
  initial_marginal : ∀ b, ∑ path with initialBit path = b, forward path = prior b
  final_marginal : ∀ b, ∑ path with finalBit path = b, forward path = finalLaw b
  reverse_support : ∀ path, forward path ≠ 0 → 0 < reverseAligned path
  localDetailedBalance : ∀ path, forward path ≠ 0 →
    pathwiseEntropyProduction toFinitePathProtocol path =
      beta * heat path + Real.log (prior (initialBit path)) -
        Real.log (finalLaw (finalBit path))

/-- Mean heat `⟨Q⟩` released to the bath under the forward path law. -/
noncomputable def ErasureModel.meanHeat (model : ErasureModel Path) : ℝ :=
  ∑ path, model.forward path * model.heat path

/-- The model erases: the final bit is deterministically `false`. -/
def ErasureModel.IsReset (model : ErasureModel Path) : Prop :=
  model.finalLaw = FiniteLaw.pointMass false

/-- A reset (point-mass) final law has zero entropy. -/
theorem entropy_pointMass_bool (chosen : Bool) :
    entropy (FiniteLaw.pointMass chosen) = 0 := by
  cases chosen <;>
    simp [entropy, FiniteLaw.pointMass]

/-- Shannon entropy of a Boolean law is the binary entropy of its `true` mass. -/
theorem entropy_bool_eq_binEntropy (law : FiniteLaw Bool) :
    entropy law = Real.binEntropy (law true) := by
  have hFalse : law false = 1 - law true := by
    have := law.sum_one
    rw [Fintype.sum_bool] at this
    linarith
  rw [entropy, Fintype.sum_bool, Real.binEntropy_eq_negMulLog_add_negMulLog_one_sub,
    ← hFalse]

/-- Decomposition of mean path entropy production into mean heat and the
change of system Shannon entropy:
`σ = β ⟨Q⟩ - H(initial) + H(final)`. -/
theorem erasure_entropyProduction_decomposition (model : ErasureModel Path) :
    entropyProduction model.toFinitePathProtocol =
      model.beta * model.meanHeat - entropy model.prior +
        entropy model.finalLaw := by
  have hKL : entropyProduction model.toFinitePathProtocol =
      ∑ path, model.forward path *
        pathwiseEntropyProduction model.toFinitePathProtocol path := by
    unfold entropyProduction
    rw [finiteKL_eq_crossEntropy_sub_entropy_of_relativeSupport _ _
      model.reverse_support]
    simp only [crossEntropy, entropy, ← Finset.sum_sub_distrib]
    apply Finset.sum_congr rfl
    intro path _
    by_cases hZero : model.forward path = 0
    · simp [hZero]
    · have hF : 0 < model.forward path :=
        lt_of_le_of_ne (model.forward.nonneg path) (Ne.symm hZero)
      have hR := model.reverse_support path hZero
      change -model.forward path * Real.log (model.reverseAligned path) -
          Real.negMulLog (model.forward path) =
        model.forward path * Real.log (pathRatio model.toFinitePathProtocol path)
      rw [pathRatio, Real.log_div hF.ne' hR.ne', Real.negMulLog_eq_neg]
      ring
  have hSupport : ∀ path, model.forward path *
      pathwiseEntropyProduction model.toFinitePathProtocol path =
        model.forward path * (model.beta * model.heat path +
          Real.log (model.prior (model.initialBit path)) -
          Real.log (model.finalLaw (model.finalBit path))) := by
    intro path
    by_cases hZero : model.forward path = 0
    · simp [hZero]
    · rw [model.localDetailedBalance path hZero]
  have hInitial := sum_mul_comp_eq_sum_fiber model.forward model.initialBit
    (fun b => Real.log (model.prior b))
  have hFinal := sum_mul_comp_eq_sum_fiber model.forward model.finalBit
    (fun b => Real.log (model.finalLaw b))
  simp only [model.initial_marginal, model.final_marginal] at hInitial hFinal
  have hEntropy : ∀ law : FiniteLaw Bool,
      entropy law = -∑ b, law b * Real.log (law b) := by
    intro law
    simp only [entropy, Real.negMulLog_eq_neg, Finset.sum_neg_distrib]
  rw [hKL, Finset.sum_congr rfl (fun path _ => hSupport path), hEntropy,
    hEntropy, ← hInitial, ← hFinal, ErasureModel.meanHeat, Finset.mul_sum]
  simp only [mul_add, mul_sub, Finset.sum_add_distrib, Finset.sum_sub_distrib]
  have hHeat : ∑ path, model.forward path * (model.beta * model.heat path) =
      ∑ path, model.beta * (model.forward path * model.heat path) :=
    Finset.sum_congr rfl fun path _ => by ring
  rw [hHeat]
  ring

/-- Generalized Landauer bound, with no second-law hypothesis:
`β ⟨Q⟩ ≥ H(initial) - H(final)`. -/
theorem erasure_generalized_landauer (model : ErasureModel Path) :
    entropy model.prior - entropy model.finalLaw ≤
      model.beta * model.meanHeat := by
  have hDecomp := erasure_entropyProduction_decomposition model
  have hNonneg := entropyProduction_nonneg model.toFinitePathProtocol
  linarith

/-- Landauer bound for a reset: `⟨Q⟩ ≥ binEntropy(p) / β`, in nats. -/
theorem erasure_landauer_reset (model : ErasureModel Path)
    (hReset : model.IsReset) :
    Real.binEntropy (model.prior true) / model.beta ≤ model.meanHeat := by
  have hBound := erasure_generalized_landauer model
  rw [hReset, entropy_pointMass_bool, sub_zero,
    entropy_bool_eq_binEntropy] at hBound
  exact (div_le_iff₀ model.beta_pos).mpr (by linarith)

/-- Fair-bit case: erasing a uniformly random bit costs at least
`log 2 / β`. -/
theorem erasure_landauer_fair_bit (model : ErasureModel Path)
    (hReset : model.IsReset) (hFair : model.prior true = 1 / 2) :
    Real.log 2 / model.beta ≤ model.meanHeat := by
  have hBound := erasure_landauer_reset model hReset
  rwa [hFair, one_div, Real.binEntropy_two_inv] at hBound

/-- A biased prior has a strictly smaller Landauer threshold than a fair
bit. -/
theorem landauer_biased_threshold_lt_fair (p beta : ℝ) (hBeta : 0 < beta)
    (hBiased : p ≠ 1 / 2) :
    Real.binEntropy p / beta < Real.log 2 / beta := by
  apply div_lt_div_of_pos_right _ hBeta
  rw [Real.binEntropy_lt_log_two]
  simpa [one_div] using hBiased

/-- Equality case: if the aligned reverse law equals the forward law, mean
entropy production vanishes and the generalized Landauer bound is attained. -/
theorem erasure_reversible_attains_bound (model : ErasureModel Path)
    (hReversible : model.reverseAligned = model.forward) :
    entropyProduction model.toFinitePathProtocol = 0 ∧
      model.beta * model.meanHeat =
        entropy model.prior - entropy model.finalLaw := by
  have hZero : entropyProduction model.toFinitePathProtocol = 0 := by
    unfold entropyProduction
    rw [hReversible]
    exact finiteKL_self _
  refine ⟨hZero, ?_⟩
  have hDecomp := erasure_entropyProduction_decomposition model
  linarith

/-- Reversible reset witness on the one-bit path space: the path is the
initial bit, the final bit is `false`, the reverse law equals the forward law,
and heat is the surprisal `-log p(x) / β`. -/
noncomputable def reversibleErasureWitness (prior : FiniteLaw Bool) (beta : ℝ)
    (hBeta : 0 < beta) : ErasureModel Bool where
  forward := prior
  reverseAligned := prior
  reversal := id
  reversal_involutive := fun _ => rfl
  prior := prior
  finalLaw := FiniteLaw.pointMass false
  initialBit := id
  finalBit := fun _ => false
  beta := beta
  heat := fun x => -Real.log (prior x) / beta
  beta_pos := hBeta
  initial_marginal := by
    intro b
    rw [Finset.sum_filter]
    simp
  final_marginal := by
    intro b
    have hOne := prior.sum_one
    rw [Fintype.sum_bool] at hOne
    cases b
    · simp [FiniteLaw.pointMass]
      linarith
    · simp [FiniteLaw.pointMass]
  reverse_support := fun path h =>
    lt_of_le_of_ne (prior.nonneg path) (Ne.symm h)
  localDetailedBalance := by
    intro path hPath
    have hPos : 0 < prior path :=
      lt_of_le_of_ne (prior.nonneg path) (Ne.symm hPath)
    simp only [pathwiseEntropyProduction, pathRatio, div_self hPos.ne',
      Real.log_one, id]
    have hBeta' := hBeta.ne'
    simp [FiniteLaw.pointMass]
    field_simp
    ring

/-- The witness is a reset. -/
theorem reversibleErasureWitness_isReset (prior : FiniteLaw Bool) (beta : ℝ)
    (hBeta : 0 < beta) : (reversibleErasureWitness prior beta hBeta).IsReset :=
  rfl

/-- The reversible witness attains the Landauer bound exactly:
`⟨Q⟩ = binEntropy(p) / β`. -/
theorem reversibleErasureWitness_meanHeat (prior : FiniteLaw Bool) (beta : ℝ)
    (hBeta : 0 < beta) :
    (reversibleErasureWitness prior beta hBeta).meanHeat =
      Real.binEntropy (prior true) / beta := by
  have hAttain := (erasure_reversible_attains_bound
    (reversibleErasureWitness prior beta hBeta) rfl).2
  have hBeta' : (reversibleErasureWitness prior beta hBeta).beta = beta := rfl
  have hPrior : (reversibleErasureWitness prior beta hBeta).prior = prior := rfl
  have hFinal : (reversibleErasureWitness prior beta hBeta).finalLaw =
      FiniteLaw.pointMass false := rfl
  rw [hBeta', hPrior, hFinal, entropy_pointMass_bool, sub_zero,
    entropy_bool_eq_binEntropy] at hAttain
  rw [eq_div_iff hBeta.ne']
  linarith

/-- Biased-bit witness (`P(true) = 3/4`): the reversible erasure heat
`binEntropy(3/4) / β` is strictly below the fair-bit threshold `log 2 / β`. -/
theorem biasedBit_erasure_heat_lt_fair (beta : ℝ) (hBeta : 0 < beta) :
    (reversibleErasureWitness irreversibleForward beta hBeta).meanHeat <
      Real.log 2 / beta := by
  rw [reversibleErasureWitness_meanHeat]
  apply landauer_biased_threshold_lt_fair _ _ hBeta
  simp only [irreversibleForward, ↓reduceIte]
  norm_num

/-- Fair-bit witness: the reversible erasure heat is exactly `log 2 / β`. -/
theorem fairBit_erasure_heat_eq (beta : ℝ) (hBeta : 0 < beta) :
    (reversibleErasureWitness (FiniteLaw.uniform : FiniteLaw Bool) beta
        hBeta).meanHeat = Real.log 2 / beta := by
  rw [reversibleErasureWitness_meanHeat]
  have hHalf : (FiniteLaw.uniform : FiniteLaw Bool) true = 2⁻¹ := by
    simp [FiniteLaw.uniform]
  rw [hHalf, Real.binEntropy_two_inv]

end LandauerErasure

end FEP.PathThermodynamics
