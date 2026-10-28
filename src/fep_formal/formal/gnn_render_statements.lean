module
public import FepSketches.gnn_document
public import FepSketches.gnn_denotation
public import FepSketches.active_inference
public import FepSketches.finite_probability
public import FepSketches.finite_markov_dynamics

@[expose] public section

/-!
# GNN renderer and execution statements

Direction-2 Q4 slice of the fep_lean/GNN bridge
(`specs/gnn-bridge-q4-renderer-execution-statements`). This module realizes
alignment statement 5 of the bridge program, per render target where a
formal semantics exists on the fep_lean side to state preservation against:

> For each render target, the rendered program's denotation equals the
> document's denotation (statement per target; proofs follow only where a
> target has a formal semantics to state against).

Scope discipline (bridge-contract evidence firewall, section 7; no-go
registry, section 9):

  - The four discrete-family matrix-emitting render targets (pymdp,
    activeinference_jl, jax, jax_pomdp) consume the five tables under one
    frozen layout — `A[observation, state]`, `B[next, previous, action]`,
    vectors over outcome / state / policy — which is exactly the Q2 payload
    order. For these targets the statable fragment is conditional: a
    target emission faithful to the payload under the frozen layout
    coincides with the carrier masses of the denoted model. The fragment
    is stated and proved here; the full program-denotation equality needs
    a formal semantics of the target-language program surface, which does
    not exist in fep_lean and is scheduled, not faked.
  - rxinfer, rxinfer_toml, discopy, discopy_combined, and bnlearn carry no
    statable semantics against the fep_lean carriers; they receive no Lean
    statement here and are documented as no-go rows in the slice README.
  - The execution semantics of the discrete family is composed from the
    kernel machinery: the policy-conditioned rollout of a denoted model is
    proved equal to the `kernelPower` of its transition kernel applied to
    the initial law, with the time-additivity corollary through
    `kernelPower_add` (the discrete Chapman–Kolmogorov composition). Any
    discrete-family simulation faithful to the per-step carrier update is
    proved to coincide with this rollout.

Compilation of this module establishes only that the stated fragments hold
as Lean propositions on the carriers. It establishes nothing about GNN
pipeline behavior (bridge-contract evidence firewall, section 7).
-/

namespace FEP.GnnRenderStatements

open FEP FEP.ActiveInference FEP.GnnDenotation FEP.GnnDocument
open FEP.FiniteMarkovDynamics Finset
open scoped BigOperators

/-! ## Frozen target layout (discrete family) -/

/-- The matrix tables a discrete-family render target consumes, under the
frozen target layout: `A[observation, hidden_state]`,
`B[next_state, previous_state, action]`, and vectors over outcome, state,
and policy. This is the Q2 payload order itself; the record exists so the
rendered artifact's consumed tables can be stated separately from the
document payload. -/
structure DiscreteTargetTables (State Outcome Policy : Type*) where
  aMat : Outcome → State → ℝ
  bMat : State → State → Policy → ℝ
  cVec : Outcome → ℝ
  dVec : State → ℝ
  eVec : Policy → ℝ

/-- The frozen target-layout contract: the target's consumed tables are the
document payload read under the frozen target layout. For the four
discrete-family matrix-emitting render targets the emitted layout is the Q2
payload order, so faithfulness is pointwise equality of the five tables. -/
def DiscreteTargetFaithful {State Outcome Policy : Type*}
    (tables : DiscreteTargetTables State Outcome Policy)
    (nums : DiscretePayload State Outcome Policy) : Prop :=
  (∀ outcome state, tables.aMat outcome state = nums.aLikelihood outcome state) ∧
    (∀ next previous policy, tables.bMat next previous policy =
      nums.bTransition next previous policy) ∧
    (∀ outcome, tables.cVec outcome = nums.cPreferences outcome) ∧
    (∀ state, tables.dVec state = nums.dInitialState state) ∧
    (∀ policy, tables.eVec policy = nums.eHabit policy)

/-! ## Alignment statement 5: discrete matrix fragment -/

/-- Alignment statement 5, matrix fragment, shared by the four
discrete-family render targets: an emission faithful to the payload under
the frozen target layout consumes exactly the carrier masses of the denoted
model (`denoteDiscrete`). The full program-denotation equality — the
rendered program's behavior — is not part of this fragment; it is
scheduled per target in the slice README's proof-schedule table and is not
stated here, because no formal semantics of the target-language program
surface exists in fep_lean to state it against. -/
def Statement5DiscreteMatrices {State Outcome Policy : Type*}
    [Fintype State] [Fintype Outcome] [Fintype Policy]
    (doc : GnnDocument) (nums : DiscretePayload State Outcome Policy)
    (h : DiscreteConforms doc nums)
    (tables : DiscreteTargetTables State Outcome Policy) : Prop :=
  DiscreteTargetFaithful tables nums →
    (∀ state outcome, tables.aMat outcome state =
        (denoteDiscrete doc nums h).likelihood.mass state outcome) ∧
      (∀ policy previous next, tables.bMat next previous policy =
        ((denoteDiscrete doc nums h).transition policy).mass previous next) ∧
      (∀ outcome, tables.cVec outcome =
        (denoteDiscrete doc nums h).preferences.mass outcome) ∧
      (∀ state, tables.dVec state =
        (denoteDiscrete doc nums h).initialState.mass state) ∧
      (∀ policy, tables.eVec policy =
        (denoteDiscrete doc nums h).policyPrior.mass policy)

/-- The matrix fragment holds whenever the emission is faithful: each
component reduces to the Q2 denotation's field construction. -/
theorem statement5DiscreteMatrices_holds {State Outcome Policy : Type*}
    [Fintype State] [Fintype Outcome] [Fintype Policy]
    (doc : GnnDocument) (nums : DiscretePayload State Outcome Policy)
    (h : DiscreteConforms doc nums)
    (tables : DiscreteTargetTables State Outcome Policy) :
    Statement5DiscreteMatrices doc nums h tables := by
  rintro ⟨ha, hb, hc, hd, he⟩
  exact ⟨fun _ _ => ha _ _, fun _ _ _ => hb _ _ _, fun _ => hc _,
    fun _ => hd _, fun _ => he _⟩

variable {State Outcome Policy : Type*}
  [Fintype State] [Fintype Outcome] [Fintype Policy]

/-- Alignment statement 5 for the `pymdp` render target (matrix fragment;
frozen layout evidenced by `GeneralizedNotationNotation/src/render/pymdp/
pymdp_renderer.py`, "pymdp 1.0.0 B[s',s,a]"). The full program-denotation
statement is scheduled, not stated. -/
def Statement5Pymdp (doc : GnnDocument) (nums : DiscretePayload State Outcome Policy)
    (h : DiscreteConforms doc nums)
    (tables : DiscreteTargetTables State Outcome Policy) : Prop :=
  Statement5DiscreteMatrices doc nums h tables

/-- Alignment statement 5 for the `activeinference_jl` render target (matrix
fragment; frozen layout evidenced by `GeneralizedNotationNotation/src/render/
activeinference_jl/activeinference_renderer.py`, the
`(NUM_OBSERVATIONS, NUM_STATES)` / `(NUM_STATES, NUM_STATES, NUM_ACTIONS)`
shape assertions and the `B[:, current_state, action]` next-state read).
The full program-denotation statement is scheduled, not stated. -/
def Statement5ActiveInferenceJl (doc : GnnDocument)
    (nums : DiscretePayload State Outcome Policy)
    (h : DiscreteConforms doc nums)
    (tables : DiscreteTargetTables State Outcome Policy) : Prop :=
  Statement5DiscreteMatrices doc nums h tables

/-- Alignment statement 5 for the `jax` render target, discrete fragment
(frozen layout evidenced by `GeneralizedNotationNotation/src/render/jax/
jax_renderer.py`, `self.models.B[:, :, action]` composed with
`self.models.A[observation, :]`). The continuous-family fragment is
scheduled against the Q3 continuous denotation and the full
program-denotation statement is scheduled; neither is stated here. -/
def Statement5Jax (doc : GnnDocument) (nums : DiscretePayload State Outcome Policy)
    (h : DiscreteConforms doc nums)
    (tables : DiscreteTargetTables State Outcome Policy) : Prop :=
  Statement5DiscreteMatrices doc nums h tables

/-- Alignment statement 5 for the `jax_pomdp` render target (matrix
fragment; same frozen layout and evidence as `jax`). The full
program-denotation statement is scheduled, not stated. -/
def Statement5JaxPomdp (doc : GnnDocument)
    (nums : DiscretePayload State Outcome Policy)
    (h : DiscreteConforms doc nums)
    (tables : DiscreteTargetTables State Outcome Policy) : Prop :=
  Statement5DiscreteMatrices doc nums h tables

/-! ## Execution semantics from the kernel machinery -/

/-- The policy-conditioned rollout of a denoted model: the state law after
`n` executed steps under a fixed policy, defined stepwise as the predictive
of the policy's transition kernel. This is the semantic target any
discrete-family execute target's state trajectory must realize. -/
def policyRollout [DecidableEq State]
    (m : GenerativeModel Policy State Outcome) (policy : Policy) :
    ℕ → FiniteLaw State
  | 0 => m.initialState
  | n + 1 => (m.transition policy).predictive (policyRollout m policy n)

/-- The execution semantics composed from the kernel machinery: the
stepwise rollout equals the `kernelPower` of the policy's transition kernel
applied to the initial law. -/
theorem policyRollout_kernelPower [DecidableEq State]
    (m : GenerativeModel Policy State Outcome) (policy : Policy) (n : ℕ) :
    policyRollout m policy n =
      (kernelPower (m.transition policy) n).predictive m.initialState := by
  induction n with
  | zero => simp [policyRollout, FiniteKernel.predictive_identity]
  | succ n ih =>
      simp only [policyRollout, ih, kernelPower_succ,
        FiniteKernel.predictive_comp]

/-- Time additivity of the executed rollout: a `(k + n)`-step execution is
the `n`-step rollout followed by the `k`-step kernel power — the discrete
Chapman–Kolmogorov composition, sibling of the
`FiniteMarkovSemigroup.transition_add` semigroup law. -/
theorem policyRollout_add [DecidableEq State]
    (m : GenerativeModel Policy State Outcome) (policy : Policy) (k n : ℕ) :
    policyRollout m policy (k + n) =
      (kernelPower (m.transition policy) k).predictive
        (policyRollout m policy n) := by
  rw [policyRollout_kernelPower, kernelPower_add,
    FiniteKernel.predictive_comp, ← policyRollout_kernelPower]

/-- The carrier's open-loop rollout kernel over the constant plan equals the
kernel power: repeating one policy `n` times composes to `kernelPower n` of
that policy's transition. This ties the execution semantics to the existing
open-loop machinery of `active_inference.lean` (`rolloutKernel`,
`plannedState`, `rolloutKernel_append`); the composition-order gap between
the head-first plan composition and the chronological kernel power closes by
`kernel_comp_power_comm`. -/
theorem rolloutKernel_replicate [DecidableEq State]
    (m : GenerativeModel Policy State Outcome) (policy : Policy) (n : ℕ) :
    rolloutKernel m (List.replicate n policy) =
      kernelPower (m.transition policy) n := by
  induction n with
  | zero => simp [rolloutKernel, List.replicate]
  | succ n ih =>
      simp only [List.replicate_succ, rolloutKernel, ih]
      rw [kernel_comp_power_comm, kernelPower_succ]

/-- The fixed-policy executed rollout is the carrier's open-loop planned
state over the constant plan: the Q4 execution semantics and the existing
`plannedState` machinery of `active_inference.lean` coincide. -/
theorem policyRollout_eq_plannedState [DecidableEq State]
    (m : GenerativeModel Policy State Outcome) (policy : Policy) (n : ℕ) :
    policyRollout m policy n =
      plannedState m (List.replicate n policy) := by
  rw [policyRollout_kernelPower, plannedState, rolloutKernel_replicate]

/-- Uniqueness of the executed state trajectory: any discrete-family
simulation that starts at the initial law and updates by the carrier's
predictive step coincides with the kernel-power rollout. This is the
conditional execution-preservation statement the discrete-family execute
targets (pymdp, activeinference_jl, jax, pytorch) must satisfy per step;
the per-program faithfulness antecedent is the GNN-side obligation. -/
def DiscreteExecutionSemantics [DecidableEq State]
    (m : GenerativeModel Policy State Outcome) (policy : Policy)
    (sim : ℕ → FiniteLaw State) : Prop :=
  sim 0 = m.initialState →
    (∀ n, sim (n + 1) = (m.transition policy).predictive (sim n)) →
      ∀ n, sim n = policyRollout m policy n

/-- The executed trajectory is unique: per-step faithfulness to the carrier
update pins the simulation to the kernel-power rollout. -/
theorem discreteExecutionSemantics_holds [DecidableEq State]
    (m : GenerativeModel Policy State Outcome) (policy : Policy)
    (sim : ℕ → FiniteLaw State) :
    DiscreteExecutionSemantics m policy sim := by
  intro h0 hstep n
  induction n with
  | zero => exact h0
  | succ n ih =>
      rw [hstep, ih, policyRollout]

/-! ## Exemplar corollaries: the P1 symmetric Boolean model -/

/-- The denoted exemplar model's executed rollout is the kernel-power
rollout of the original Lean definition (`symmetricBoolModel
trueBiasedPolicyPrior`). -/
theorem symBoolDoc_policyRollout_kernelPower (policy : Bool) (n : ℕ) :
    policyRollout (denoteDiscrete symBoolDoc symBoolPayload symBoolConforms)
        policy n =
      (kernelPower
          ((symmetricBoolModel trueBiasedPolicyPrior).transition policy) n).predictive
        (symmetricBoolModel trueBiasedPolicyPrior).initialState := by
  rw [symBoolDoc_denotation]
  exact policyRollout_kernelPower _ _ _

end FEP.GnnRenderStatements
