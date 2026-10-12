import FepSketches.active_inference
import FepSketches.controlled_markov

/-!
# Typed geospatial kernels: light cones, arrival bounds and the pymdp bridge

General finite results for spatially typed active-inference models. A cell
type carries a movement relation `R : Cell → Cell → Prop`; for an H3 model `R`
is a sub-relation of grid adjacency recorded as data by the instance. Nothing
in this file depends on H3 geometry.

* `IsLocal R k`: positive kernel mass either stays put or follows `R`.
* `Reach R n c c'`: `c'` is reachable from `c` in `n` stay-or-move steps.
* Light cone (`plannedState_support`): every open-loop plan of `R`-local
  transitions predicts zero mass outside the `Reach` cone of the prior support.
* Arrival bound (`plannedState_eq_zero_of_potential`): an `R`-1-Lipschitz
  potential turns the cone into a lower bound on arrival time for every plan.
* Achievability (`plannedState_pos_of_chain`): a chain of positive steps gives
  positive predicted mass.
* pymdp bridge (`risk_add_ambiguity_eq_logPartition_sub_pymdpNegEFE`): with
  preferences `softmax C`, risk plus ambiguity equals `log Σ exp C` minus the
  one-step negative expected free energy that pymdp 1.0.3 computes (expected
  utility plus state information gain). No support hypothesis on predicted
  states or outcomes is needed, unlike the full-support decomposition
  `expectedFreeEnergy_eq_risk_add_ambiguity`; spatial beliefs are sparse.
  Consequently pymdp's policy posterior equals the Boltzmann posterior of
  risk plus ambiguity (`controlPosterior_riskAmbiguity_eq_pymdp`).

The firewall of the GNN bridge contract applies: these are statements about
finite laws and kernels. They do not establish anything about H3 geometry,
float32 execution, or fish behavior.
-/

namespace CascadiaGeo

open FEP FEP.ActiveInference FEP.ControlledMarkov FEP.FiniteInformation Finset
open scoped BigOperators

/-! ## Stay-or-move reachability -/

section Reach

variable {Cell : Type*}

/-- `Reach R n c c'`: `c'` is reachable from `c` in `n` steps, each step
either staying put or following `R`. -/
def Reach (R : Cell → Cell → Prop) : ℕ → Cell → Cell → Prop
  | 0, c, c' => c' = c
  | n + 1, c, c'' => ∃ c', Reach R n c c' ∧ (c'' = c' ∨ R c' c'')

/-- Staying put is always reachable. -/
theorem reach_refl (R : Cell → Cell → Prop) : ∀ (n : ℕ) (c : Cell), Reach R n c c
  | 0, _ => rfl
  | n + 1, c => ⟨c, reach_refl R n c, Or.inl rfl⟩

/-- One more step never shrinks the cone. -/
theorem reach_succ_of_reach {R : Cell → Cell → Prop} (n : ℕ) {c c' : Cell}
    (h : Reach R n c c') : Reach R (n + 1) c c' :=
  ⟨c', h, Or.inl rfl⟩

/-- Reachability is monotone in the step budget. -/
theorem reach_mono {R : Cell → Cell → Prop} {n m : ℕ} (hnm : n ≤ m)
    {c c' : Cell} (h : Reach R n c c') : Reach R m c c' := by
  induction hnm with
  | refl => exact h
  | step _ ih => exact reach_succ_of_reach _ ih

/-- Prepending one stay-or-move step. -/
theorem reach_cons {R : Cell → Cell → Prop} {c y : Cell} (hstep : y = c ∨ R c y) :
    ∀ (n : ℕ) {c' : Cell}, Reach R n y c' → Reach R (n + 1) c c'
  | 0, c', h => by
      have hy : c' = y := h
      subst hy
      exact ⟨c, rfl, hstep⟩
  | n + 1, _, ⟨c', hreach, hlast⟩ => ⟨c', reach_cons hstep n hreach, hlast⟩

/-- A potential that changes by at most one per `R`-move bounds arrival time:
`φ c ≤ φ c' + n` whenever `c'` is reachable from `c` in `n` steps. -/
theorem reach_potential {R : Cell → Cell → Prop} (φ : Cell → ℕ)
    (hφ : ∀ c c', R c c' → φ c ≤ φ c' + 1) :
    ∀ (n : ℕ) {c c' : Cell}, Reach R n c c' → φ c ≤ φ c' + n
  | 0, c, c', h => by
      have hc : c' = c := h
      subst hc
      omega
  | n + 1, _, c'', ⟨c', hreach, hlast⟩ => by
      have ih := reach_potential φ hφ n hreach
      rcases hlast with hstay | hmove
      · subst hstay
        omega
      · have := hφ c' c'' hmove
        omega

end Reach

/-! ## Local kernels and the light cone of open-loop plans -/

section LightCone

variable {Policy Cell Outcome : Type*}
  [Fintype Policy] [Fintype Cell] [Fintype Outcome] [DecidableEq Cell]

/-- A kernel is `R`-local when positive mass only stays put or follows `R`. -/
def IsLocal (R : Cell → Cell → Prop) (k : FiniteKernel Cell Cell) : Prop :=
  ∀ c c', k c c' ≠ 0 → c' = c ∨ R c c'

/-- Light cone of a rollout: an open-loop plan of `R`-local transitions only
connects cells within `Reach R plan.length`. -/
theorem rolloutKernel_support (model : GenerativeModel Policy Cell Outcome)
    {R : Cell → Cell → Prop} (hlocal : ∀ π, IsLocal R (model.transition π)) :
    ∀ (plan : List Policy) (c c' : Cell),
      rolloutKernel model plan c c' ≠ 0 → Reach R plan.length c c'
  | [], c, c', h => by
      have h' : (if c' = c then (1 : ℝ) else 0) ≠ 0 := h
      show c' = c
      by_contra hne
      simp [hne] at h'
  | π :: rest, c, c'', h => by
      have h' : (∑ y, model.transition π c y * rolloutKernel model rest y c'') ≠ 0 := h
      obtain ⟨y, -, hy⟩ := Finset.exists_ne_zero_of_sum_ne_zero h'
      have hreach := rolloutKernel_support model hlocal rest y c'' (right_ne_zero_of_mul hy)
      have hstep := hlocal π c y (left_ne_zero_of_mul hy)
      simpa [List.length_cons] using reach_cons hstep rest.length hreach

/-- Light cone of a prediction: positive predicted mass after a plan lies in
the `Reach` cone of the initial-state support. -/
theorem plannedState_support (model : GenerativeModel Policy Cell Outcome)
    {R : Cell → Cell → Prop} (hlocal : ∀ π, IsLocal R (model.transition π))
    (plan : List Policy) (c' : Cell) (h : plannedState model plan c' ≠ 0) :
    ∃ c, model.initialState c ≠ 0 ∧ Reach R plan.length c c' := by
  have h' : (∑ c, model.initialState c * rolloutKernel model plan c c') ≠ 0 := h
  obtain ⟨c, -, hc⟩ := Finset.exists_ne_zero_of_sum_ne_zero h'
  exact ⟨c, left_ne_zero_of_mul hc,
    rolloutKernel_support model hlocal plan c c' (right_ne_zero_of_mul hc)⟩

/-- Arrival lower bound: if every cell of the initial support is farther from
`target` (under an `R`-1-Lipschitz potential) than the plan is long, every such
plan predicts exactly zero mass at `target`. -/
theorem plannedState_eq_zero_of_potential (model : GenerativeModel Policy Cell Outcome)
    {R : Cell → Cell → Prop} (hlocal : ∀ π, IsLocal R (model.transition π))
    (φ : Cell → ℕ) (hφ : ∀ c c', R c c' → φ c ≤ φ c' + 1)
    (target : Cell) (plan : List Policy)
    (hfar : ∀ c, model.initialState c ≠ 0 → φ target + plan.length < φ c) :
    plannedState model plan target = 0 := by
  by_contra h
  obtain ⟨c, hc, hreach⟩ := plannedState_support model hlocal plan target h
  have hbound := reach_potential φ hφ plan.length hreach
  have hgap := hfar c hc
  omega

/-- `Chain model plan c c'`: a cell path from `c` to `c'` whose every step has
positive transition mass under the corresponding policy. -/
def Chain (model : GenerativeModel Policy Cell Outcome) :
    List Policy → Cell → Cell → Prop
  | [], c, c' => c' = c
  | π :: rest, c, c'' => ∃ y, 0 < model.transition π c y ∧ Chain model rest y c''

/-- A positive chain gives positive rollout mass. -/
theorem rolloutKernel_pos_of_chain (model : GenerativeModel Policy Cell Outcome) :
    ∀ (plan : List Policy) (c c' : Cell),
      Chain model plan c c' → 0 < rolloutKernel model plan c c'
  | [], c, c', h => by
      have hc : c' = c := h
      subst hc
      show (0 : ℝ) < if c' = c' then 1 else 0
      simp
  | π :: rest, c, c'', ⟨y, hy, hchain⟩ => by
      have hrest := rolloutKernel_pos_of_chain model rest y c'' hchain
      show 0 < ∑ x, model.transition π c x * rolloutKernel model rest x c''
      exact lt_of_lt_of_le (mul_pos hy hrest)
        (Finset.single_le_sum
          (f := fun x => model.transition π c x * rolloutKernel model rest x c'')
          (fun x _ => mul_nonneg ((model.transition π).nonneg c x)
            ((rolloutKernel model rest).nonneg x c''))
          (Finset.mem_univ y))

/-- Achievability: a positive chain from a cell of the initial support gives
positive predicted mass at its endpoint. -/
theorem plannedState_pos_of_chain (model : GenerativeModel Policy Cell Outcome)
    (plan : List Policy) (c c' : Cell) (hc : 0 < model.initialState c)
    (h : Chain model plan c c') : 0 < plannedState model plan c' := by
  show 0 < ∑ x, model.initialState x * rolloutKernel model plan x c'
  exact lt_of_lt_of_le (mul_pos hc (rolloutKernel_pos_of_chain model plan c c' h))
    (Finset.single_le_sum
      (f := fun x => model.initialState x * rolloutKernel model plan x c')
      (fun x _ => mul_nonneg (model.initialState.nonneg x)
        ((rolloutKernel model plan).nonneg x c'))
      (Finset.mem_univ c))

end LightCone

/-! ## Log-preferences and the pymdp 1.0.3 expected-free-energy bridge -/

section Pymdp

variable {Policy State Outcome : Type*}
  [Fintype Policy] [Fintype State] [Fintype Outcome] [Nonempty Outcome]

/-- Partition function of log-preferences `C`. -/
noncomputable def logPartition (C : Outcome → ℝ) : ℝ :=
  Real.log (∑ o, Real.exp (C o))

theorem expSum_pos (C : Outcome → ℝ) : 0 < ∑ o, Real.exp (C o) :=
  Finset.sum_pos (fun _ _ => Real.exp_pos _) Finset.univ_nonempty

/-- The preference law of log-preferences `C`: `softmax C`. GNN and pymdp
carry `C` as log-preferences (`LogPreferenceVector`); the finite carrier
carries the normalized law. -/
noncomputable def softmaxLaw (C : Outcome → ℝ) : FiniteLaw Outcome where
  mass o := Real.exp (C o) / ∑ o', Real.exp (C o')
  nonneg o := div_nonneg (Real.exp_pos _).le (expSum_pos C).le
  sum_one := by
    rw [← Finset.sum_div]
    exact div_self (ne_of_gt (expSum_pos C))

theorem softmaxLaw_pos (C : Outcome → ℝ) (o : Outcome) : 0 < softmaxLaw C o :=
  div_pos (Real.exp_pos _) (expSum_pos C)

theorem log_softmaxLaw (C : Outcome → ℝ) (o : Outcome) :
    Real.log (softmaxLaw C o) = C o - logPartition C := by
  show Real.log (Real.exp (C o) / ∑ o', Real.exp (C o')) = C o - logPartition C
  rw [Real.log_div (Real.exp_pos _).ne' (expSum_pos C).ne', Real.log_exp]
  rfl

/-- pymdp 1.0.3 one-step score: expected utility `Σ q(o) C(o)` plus state
information gain `H[q(o)] − ambiguity`. -/
noncomputable def pymdpNegEFE (model : GenerativeModel Policy State Outcome)
    (C : Outcome → ℝ) (π : Policy) : ℝ :=
  (∑ o, predictedOutcome model π o * C o) +
    entropy (predictedOutcome model π) - ambiguity model π

/-- The bridge identity, valid for sparse beliefs: risk plus ambiguity equals
`log Σ exp C` minus pymdp's negative expected free energy. -/
theorem risk_add_ambiguity_eq_logPartition_sub_pymdpNegEFE
    (model : GenerativeModel Policy State Outcome) (C : Outcome → ℝ)
    (hpref : model.preferences = softmaxLaw C) (π : Policy) :
    risk model π + ambiguity model π = logPartition C - pymdpNegEFE model C π := by
  have hpos : ∀ o, 0 < model.preferences o := by
    intro o
    rw [hpref]
    exact softmaxLaw_pos C o
  have hrisk : risk model π =
      crossEntropy (predictedOutcome model π) model.preferences -
        entropy (predictedOutcome model π) :=
    finiteKL_eq_crossEntropy_sub_entropy _ _ hpos
  have hcross : crossEntropy (predictedOutcome model π) model.preferences =
      logPartition C - ∑ o, predictedOutcome model π o * C o := by
    rw [hpref]
    unfold crossEntropy
    simp_rw [log_softmaxLaw]
    have hterm : ∀ o, -(predictedOutcome model π o) * (C o - logPartition C) =
        logPartition C * predictedOutcome model π o -
          predictedOutcome model π o * C o := by
      intro o
      ring
    simp_rw [hterm, Finset.sum_sub_distrib, ← Finset.mul_sum,
      (predictedOutcome model π).sum_one, mul_one]
  rw [hrisk, hcross]
  unfold pymdpNegEFE
  ring

/-- Policy rankings agree: lower risk plus ambiguity is exactly higher pymdp
score, so the deterministic argmax of pymdp minimizes risk plus ambiguity. -/
theorem riskAmbiguity_le_iff_pymdpNegEFE_le
    (model : GenerativeModel Policy State Outcome) (C : Outcome → ℝ)
    (hpref : model.preferences = softmaxLaw C) (π π' : Policy) :
    risk model π + ambiguity model π ≤ risk model π' + ambiguity model π' ↔
      pymdpNegEFE model C π' ≤ pymdpNegEFE model C π := by
  rw [risk_add_ambiguity_eq_logPartition_sub_pymdpNegEFE model C hpref π,
    risk_add_ambiguity_eq_logPartition_sub_pymdpNegEFE model C hpref π']
  constructor <;> intro h <;> linarith

/-- Boltzmann posteriors are invariant under adding a constant energy. -/
theorem boltzmannPosterior_add_const {Action : Type*} [Fintype Action]
    (prior : FiniteLaw Action) (energy : Action → ℝ) (shift : ℝ) :
    boltzmannPosterior prior (fun a => energy a + shift) =
      boltzmannPosterior prior energy := by
  apply FiniteLaw.ext_mass
  funext a
  have hweight : ∀ b, boltzmannWeight prior (fun a => energy a + shift) b =
      Real.exp (-shift) * boltzmannWeight prior energy b := by
    intro b
    unfold boltzmannWeight
    rw [neg_add, Real.exp_add]
    ring
  have hpartition : boltzmannPartition prior (fun a => energy a + shift) =
      Real.exp (-shift) * boltzmannPartition prior energy := by
    unfold boltzmannPartition
    simp_rw [hweight, ← Finset.mul_sum]
  show boltzmannWeight prior (fun a => energy a + shift) a /
      boltzmannPartition prior (fun a => energy a + shift) =
    boltzmannWeight prior energy a / boltzmannPartition prior energy
  rw [hweight, hpartition, mul_div_mul_left _ _ (Real.exp_pos _).ne']

/-- pymdp's policy posterior `σ(γ · negEFE + ln E)` is the control posterior of
risk plus ambiguity at precision `γ` under the habit `E`. -/
theorem controlPosterior_riskAmbiguity_eq_pymdp
    (model : GenerativeModel Policy State Outcome) (C : Outcome → ℝ)
    (hpref : model.preferences = softmaxLaw C) (γ : ℝ) :
    controlPosterior model.policyPrior γ
        (fun π => risk model π + ambiguity model π) =
      controlPosterior model.policyPrior γ
        (fun π => -pymdpNegEFE model C π) := by
  unfold controlPosterior
  have hshift : (fun π => γ * (risk model π + ambiguity model π)) =
      fun π => γ * -pymdpNegEFE model C π + γ * logPartition C := by
    funext π
    rw [risk_add_ambiguity_eq_logPartition_sub_pymdpNegEFE model C hpref π]
    ring
  rw [hshift]
  exact boltzmannPosterior_add_const _ _ _

end Pymdp

end CascadiaGeo
