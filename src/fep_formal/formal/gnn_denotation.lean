module
public import FepSketches.gnn_document
public import FepSketches.active_inference
public import Mathlib.Data.Fintype.Basic
public import Mathlib.Algebra.BigOperators.Group.Finset.Basic

@[expose] public section

/-!
# GNN discrete-family denotation over the finite active-inference carriers

Direction-2 Q2 slice of the fep_lean/GNN bridge
(`specs/gnn-bridge-q2-discrete-denotation`). This module realizes alignment
statement 1 of the bridge program: a well-formed discrete-family GNN document,
read under the frozen conventions fixed in the slice README, denotes an instance
of the `active_inference.lean` `GenerativeModel`:

  `A` ↔ likelihood, `B` ↔ policy-indexed transition ordered
  `(next_state, previous_state, action)`, `C` ↔ preferences,
  `D` ↔ initial prior, `E` ↔ habit prior.

The AST and its decidable well-formedness are the accepted Q1 module
`FepSketches.gnn_document` (`FEP.GnnDocument`); this module reuses its
cross-section extractors and the `WellFormed` predicate without modifying them.

Conventions frozen by the slice README (not resolvable from syntax):
  - field binding `A`→likelihood, `B`→transition, `C`→preferences,
    `D`→initialState, `E`→policyPrior, read off the document's ontology
    bindings;
  - `B` payload order `(next, previous, action)` (bridge contract), so the
    carrier kernel `mass prev next` reads `payload[next, prev, policy]`;
  - `A` layout `A[observation, state]` (pymdp convention, per the P1 exemplar),
    so the carrier kernel `mass state outcome` reads `payload[outcome, state]`;
  - index enumeration fixed by the exemplar (`Bool: false, true`);
  - numeric payload domain `ℝ`, exact rational values (P1 rounding policy).

The payload-string → typed-table interpretation is applied here, not parsed;
the boundary is recorded in the slice README as a finding for the GNN side.

Compilation of this module establishes only the exemplar denotation and its
corollaries on the fixed carrier. It establishes nothing about GNN pipeline
behavior (bridge-contract evidence firewall, section 7).
-/

namespace FEP.GnnDenotation

open FEP FEP.ActiveInference FEP.GnnDocument Finset
open scoped BigOperators

/-! ## Discrete payload and conformance helpers -/

/-- Numeric payload tables for the discrete family's five matrix variables,
indexed by carrier element in the frozen dimension order. -/
structure DiscretePayload (State Outcome Policy : Type*) where
  aLikelihood : Outcome → State → ℝ
  bTransition : State → State → Policy → ℝ
  cPreferences : Outcome → ℝ
  dInitialState : State → ℝ
  eHabit : Policy → ℝ

/-- Vector payload is a finite probability law (nonnegative, sums to one). -/
def VectorLaw {α : Type*} [Fintype α] (v : α → ℝ) : Prop :=
  (∀ x, 0 ≤ v x) ∧ ∑ x, v x = 1

/-- Kernel payload `b : next → previous → policy → ℝ` is a finite Markov
kernel for each policy: nonnegative, and for every `(policy, previous)` the
next-state row sums to one (the carrier `transition policy : FiniteKernel
State State` sums over the output `next`). -/
def KernelPayload {State Policy : Type*} [Fintype State]
    (b : State → State → Policy → ℝ) : Prop :=
  (∀ next previous policy, 0 ≤ b next previous policy) ∧
    (∀ policy previous, ∑ next, b next previous policy = 1)

/-- Likelihood payload `a : outcome → state → ℝ` is column-stochastic: for
every state, the observation column sums to one (the carrier `likelihood :
FiniteKernel State Outcome` sums over the output `outcome`). -/
def LikelihoodPayload {State Outcome : Type*} [Fintype Outcome]
    (a : Outcome → State → ℝ) : Prop :=
  (∀ outcome state, 0 ≤ a outcome state) ∧ (∀ state, ∑ outcome, a outcome state = 1)

/-! ## Document lookups (reuse Q1 extractors) -/

/-- The natural dimension of a `GnnDim`, if it is a positive literal;
`none` for a name reference. -/
def dimNat : GnnDim → Option Nat
  | .lit n => if 0 < n then some n else none
  | .ref _ => none

/-- The literal dimension list of a declaration, or `none` if any dimension is
a name reference. -/
def dimsNat (ds : List GnnDim) : Option (List Nat) :=
  match ds with
  | [] => some []
  | d :: rest => (dimNat d).bind fun n => (dimsNat rest).map fun ns => n :: ns

/-- The first declaration named `name`, if any. -/
def findDecl (doc : GnnDocument) (name : String) : Option GnnDecl :=
  (stateSpaceDecls doc).filter (fun d => d.name == name) |>.head?

/-- The literal dimension list of the declaration named `name`. -/
def declDims (doc : GnnDocument) (name : String) : Option (List Nat) :=
  (findDecl doc name).bind fun d => dimsNat d.dims

/-- Whether some `InitialParameterization` entry parameterizes `name`. -/
def parameterizes (doc : GnnDocument) (name : String) : Bool :=
  (parameterizationEntries doc).any fun e => e.varName == name

/-- Whether an `ActInfOntologyAnnotation` binding `var = term` is present. -/
def bindsTerm (doc : GnnDocument) (var term : String) : Bool :=
  (ontologyBindings doc).any fun b => b.varName == var && b.term == term

/-- The five discrete-family field variables. -/
def discreteStateVars : List String := ["A", "B", "C", "D", "E"]

/-- The frozen ontology bindings for the five discrete-family fields. -/
def discreteFieldBindings : List (String × String) :=
  [ ("A", "LikelihoodMatrix"), ("B", "TransitionMatrix"), ("C", "Preferences"),
    ("D", "PriorOverHiddenStates"), ("E", "Habit") ]

/-! ## Discrete conformance -/

/-- Conformance of a discrete-family document and payload to the frozen
conventions: the document is well-formed; the five field variables are declared
with literal dimensions matching the carrier cardinalities; each is
parameterized; the five ontology field bindings are present; and the payload
tables satisfy the carrier normalization conditions. -/
structure DiscreteConforms {State Outcome Policy : Type*}
    [Fintype State] [Fintype Outcome] [Fintype Policy]
    (doc : GnnDocument) (nums : DiscretePayload State Outcome Policy) : Prop where
  docWellFormed : WellFormed doc
  declA : declDims doc "A" = some [Fintype.card Outcome, Fintype.card State]
  declB : declDims doc "B" = some [Fintype.card State, Fintype.card State, Fintype.card Policy]
  declC : declDims doc "C" = some [Fintype.card Outcome]
  declD : declDims doc "D" = some [Fintype.card State]
  declE : declDims doc "E" = some [Fintype.card Policy]
  paramFields : ∀ v, v ∈ discreteStateVars → parameterizes doc v = true
  ontologyFields :
    ∀ v t, (v, t) ∈ discreteFieldBindings → bindsTerm doc v t = true
  aPayload : LikelihoodPayload nums.aLikelihood
  bPayload : KernelPayload nums.bTransition
  cPayload : VectorLaw nums.cPreferences
  dPayload : VectorLaw nums.dInitialState
  ePayload : VectorLaw nums.eHabit

/-! ## Carrier construction helpers -/

/-- Construct a `FiniteLaw` from a mass function and its proofs. -/
def lawOfMass {α : Type*} [Fintype α] (m : α → ℝ)
    (hnn : ∀ x, 0 ≤ m x) (hsum : ∑ x, m x = 1) : FiniteLaw α :=
  ⟨m, hnn, hsum⟩

/-- Construct a `FiniteKernel` from a mass function and its proofs. -/
def kernelOfMass {α β : Type*} [Fintype α] [Fintype β]
    (m : α → β → ℝ) (hnn : ∀ x y, 0 ≤ m x y) (hsum : ∀ x, ∑ y, m x y = 1) :
    FiniteKernel α β :=
  ⟨m, hnn, hsum⟩

/-! ## The discrete-family denotation (alignment statement 1) -/

/-- The `GenerativeModel` denoted by a conforming discrete-family document and
payload. The document's field/parameterization/ontology conformance fixes the
binding of the five payload tables to the `GenerativeModel` fields; the payload
supplies the masses under the frozen dimension conventions. -/
def denoteDiscrete {State Outcome Policy : Type*}
    [Fintype State] [Fintype Outcome] [Fintype Policy]
    (doc : GnnDocument) (nums : DiscretePayload State Outcome Policy)
    (h : DiscreteConforms doc nums) :
    GenerativeModel Policy State Outcome where
  initialState :=
    lawOfMass nums.dInitialState h.dPayload.1 h.dPayload.2
  transition := fun policy =>
    kernelOfMass (fun prev next => nums.bTransition next prev policy)
      (fun prev next => h.bPayload.1 next prev policy)
      (fun prev => h.bPayload.2 policy prev)
  likelihood :=
    kernelOfMass (fun state outcome => nums.aLikelihood outcome state)
      (fun state outcome => h.aPayload.1 outcome state)
      (fun state => h.aPayload.2 state)
  preferences :=
    lawOfMass nums.cPreferences h.cPayload.1 h.cPayload.2
  policyPrior :=
    lawOfMass nums.eHabit h.ePayload.1 h.ePayload.2

/-! ## Fixed exemplar: the P1 symmetric Boolean model -/

/-- Transcription of the P1 artifact
`specs/gnn-bridge-p1-finite-spike/gnn-input/FepLeanSymmetricBool.md` into the
Q1 `GnnDocument` AST: the deterministic projection of
`FEP.ActiveInference.symmetricBoolModel trueBiasedPolicyPrior` to `GNN v1`. -/
def symBoolDoc : GnnDocument where
  sections :=
    [ .gnnSection "FepLeanSymmetricBool"
    , .gnnVersionAndFlags .v1 []
    , .modelName "FepLean Symmetric Boolean Generative Model"
    , .modelAnnotation
        "Bridge P1 spike: the fep_lean active_inference.lean GenerativeModel \
         instance symmetricBoolModel trueBiasedPolicyPrior (two policies, two \
         hidden states, two observations, one step) projected deterministically \
         to GNN v1 syntax."
    , .stateSpaceBlock
        [ ⟨"A", [.lit 2, .lit 2], .floatT, none⟩
        , ⟨"B", [.lit 2, .lit 2, .lit 2], .floatT, none⟩
        , ⟨"C", [.lit 2], .floatT, none⟩
        , ⟨"D", [.lit 2], .floatT, none⟩
        , ⟨"E", [.lit 2], .floatT, none⟩
        , ⟨"s", [.lit 2, .lit 1], .floatT, none⟩
        , ⟨"s_prime", [.lit 2, .lit 1], .floatT, none⟩
        , ⟨"o", [.lit 2, .lit 1], .floatT, none⟩
        , ⟨"π", [.lit 2], .floatT, none⟩
        , ⟨"F", [.ref "π"], .floatT, none⟩
        , ⟨"G", [.ref "π"], .floatT, none⟩
        , ⟨"t", [.lit 1], .intT, none⟩ ]
    , .connections
        [ ⟨"D", .directed, "s", none⟩
        , ⟨"s", .undirected, "B", none⟩
        , ⟨"B", .directed, "s_prime", none⟩
        , ⟨"s_prime", .undirected, "A", none⟩
        , ⟨"A", .directed, "o", none⟩
        , ⟨"E", .directed, "π", none⟩
        , ⟨"π", .directed, "B", none⟩
        , ⟨"C", .directed, "G", none⟩
        , ⟨"G", .directed, "π", none⟩ ]
    , .initialParameterization
        [ ⟨"A", "{(0.5, 0.5), (0.5, 0.5)}"⟩
        , ⟨"B", "{((0.5, 0.5), (0.5, 0.5)), ((0.5, 0.5), (0.5, 0.5))}"⟩
        , ⟨"C", "{(0.5, 0.5)}"⟩
        , ⟨"D", "{(0.5, 0.5)}"⟩
        , ⟨"E", "{(0.25, 0.75)}"⟩ ]
    , .equations
        "predictedState q_π(s') = Σ_s B[s',s,π] D[s]; \
         predictedOutcome p_π(o) = Σ_s' A[o,s'] q_π(s'); \
         risk KL(p_π || C); ambiguity Σ_s' q_π(s') H(A[·,s']); \
         expectedFreeEnergy G(π) = risk(π) + ambiguity(π); \
         variationalFreeEnergy F = KL(q||posterior) + surprisal; \
         policyPosterior Q(π) ∝ E(π) exp(-γ G(π))."
    , .time
        [ ⟨"Time", some "t"⟩, ⟨"Dynamic", none⟩, ⟨"Discrete", none⟩
        , ⟨"ModelTimeHorizon", some "1"⟩ ]
    , .actInfOntologyAnnotation
        [ ⟨"A", "LikelihoodMatrix"⟩, ⟨"B", "TransitionMatrix"⟩
        , ⟨"C", "Preferences"⟩, ⟨"D", "PriorOverHiddenStates"⟩
        , ⟨"E", "Habit"⟩, ⟨"F", "VariationalFreeEnergy"⟩
        , ⟨"G", "ExpectedFreeEnergy"⟩, ⟨"s", "HiddenState"⟩
        , ⟨"s_prime", "NextHiddenState"⟩, ⟨"o", "Observation"⟩
        , ⟨"π", "PolicyVector"⟩, ⟨"t", "Time"⟩ ]
    , .modelParameters
        [ ⟨"num_hidden_states", "2"⟩, ⟨"num_obs", "2"⟩
        , ⟨"num_actions", "2"⟩, ⟨"num_timesteps", "1"⟩ ]
    , .footer "FepLean bridge P1 spike: symmetric Boolean generative model."
    , .signature
        "source_repository: fep_lean; lean_instance: FEP.ActiveInference.\
         symmetricBoolModel trueBiasedPolicyPrior; target_syntax: GNN v1." ]

/-- The exemplar's typed payload tables over the Boolean carriers, carrying the
exact transcribed literals. `A`, `B`, `C`, `D` are fair (`1/2`); `E` is the
true-biased policy prior (`E(false)=1/4`, `E(true)=3/4`), matching
`trueBiasedPolicyPrior`. -/
noncomputable def symBoolPayload : DiscretePayload Bool Bool Bool where
  aLikelihood _ _ := 1 / 2
  bTransition _ _ _ := 1 / 2
  cPreferences _ := 1 / 2
  dInitialState _ := 1 / 2
  eHabit policy := if policy then 3 / 4 else 1 / 4

/-- The exemplar document is well-formed under the frozen Q1 surface. -/
theorem symBoolDoc_wellFormed : WellFormed symBoolDoc := by decide

theorem symBoolConforms : DiscreteConforms symBoolDoc symBoolPayload := by
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩
  · exact symBoolDoc_wellFormed
  · simp [declDims, findDecl, stateSpaceDecls, symBoolDoc, Fintype.card_bool, dimsNat, dimNat]
  · simp [declDims, findDecl, stateSpaceDecls, symBoolDoc, Fintype.card_bool, dimsNat, dimNat]
  · simp [declDims, findDecl, stateSpaceDecls, symBoolDoc, Fintype.card_bool, dimsNat, dimNat]
  · simp [declDims, findDecl, stateSpaceDecls, symBoolDoc, Fintype.card_bool, dimsNat, dimNat]
  · simp [declDims, findDecl, stateSpaceDecls, symBoolDoc, Fintype.card_bool, dimsNat, dimNat]
  · intro v hv
    simp only [discreteStateVars, List.mem_cons, List.not_mem_nil, or_false] at hv
    rcases hv with rfl | rfl | rfl | rfl | rfl
    all_goals simp [parameterizes, parameterizationEntries, symBoolDoc]
  · intro v t hv
    simp only [discreteFieldBindings, List.mem_cons, List.not_mem_nil, or_false] at hv
    rcases hv with ⟨rfl, rfl⟩ | ⟨rfl, rfl⟩ | ⟨rfl, rfl⟩ | ⟨rfl, rfl⟩ | ⟨rfl, rfl⟩
    all_goals simp [bindsTerm, ontologyBindings, symBoolDoc]
  · refine ⟨?_, ?_⟩ <;> simp [symBoolPayload]
  · refine ⟨?_, ?_⟩ <;> simp [symBoolPayload]
  · refine ⟨?_, ?_⟩ <;> simp [symBoolPayload]
  · refine ⟨?_, ?_⟩ <;> simp [symBoolPayload]
  · refine ⟨fun policy => ?_, ?_⟩
    · cases policy
      · simp only [symBoolPayload]
        norm_num
      · simp only [symBoolPayload]
        norm_num
    · rw [Fintype.sum_bool]
      simp only [symBoolPayload]
      norm_num

/-- Fieldwise extensionality for `GenerativeModel` (the carrier declares no
`ext` lemma; this local lemma assembles a model equality from its five field
equalities without unfolding the payload construction helpers). -/
theorem generativeModel_ext {State Outcome Policy : Type*}
    [Fintype State] [Fintype Outcome] [Fintype Policy]
    (m n : GenerativeModel Policy State Outcome)
    (h1 : m.initialState = n.initialState)
    (h2 : m.transition = n.transition)
    (h3 : m.likelihood = n.likelihood)
    (h4 : m.preferences = n.preferences)
    (h5 : m.policyPrior = n.policyPrior) : m = n := by
  obtain ⟨a, b, c, d, e⟩ := m
  obtain ⟨a', b', c', d', e'⟩ := n
  subst h1; subst h2; subst h3; subst h4; subst h5
  rfl

/-! ## The exemplar isomorphism-class statement -/

/-- The denoted model equals the original Lean definition up to the exact
literals: reading the P1 exemplar document under the frozen discrete
conventions recovers `symmetricBoolModel trueBiasedPolicyPrior`. -/
theorem symBoolDoc_denotation :
    denoteDiscrete symBoolDoc symBoolPayload symBoolConforms =
      symmetricBoolModel trueBiasedPolicyPrior := by
  apply generativeModel_ext
  · apply FiniteLaw.ext_mass
    funext x
    simp [denoteDiscrete, lawOfMass, symBoolPayload, symmetricBoolModel, fairBoolLaw]
  · funext policy
    apply FiniteKernel.ext_mass
    funext prev next
    simp [denoteDiscrete, kernelOfMass, symBoolPayload, symmetricBoolModel, fairBoolKernel]
  · apply FiniteKernel.ext_mass
    funext state outcome
    simp [denoteDiscrete, kernelOfMass, symBoolPayload, symmetricBoolModel, fairBoolKernel]
  · apply FiniteLaw.ext_mass
    funext x
    simp [denoteDiscrete, lawOfMass, symBoolPayload, symmetricBoolModel, fairBoolLaw]
  · apply FiniteLaw.ext_mass
    funext x
    simp [denoteDiscrete, lawOfMass, symBoolPayload, symmetricBoolModel, trueBiasedPolicyPrior]

/-! ## Corollaries: the denoted model drops into the carrier's theorems -/

/-- Every policy predicts the fair state law in the denoted exemplar model. -/
theorem symBoolDoc_predictedState (policy : Bool) :
    predictedState (denoteDiscrete symBoolDoc symBoolPayload symBoolConforms)
      policy = fairBoolLaw := by
  rw [symBoolDoc_denotation]
  exact symmetricBoolModel_predictedState _ policy

/-- Every policy predicts the fair observation law in the denoted exemplar
model. -/
theorem symBoolDoc_predictedOutcome (policy : Bool) :
    predictedOutcome (denoteDiscrete symBoolDoc symBoolPayload symBoolConforms)
      policy = fairBoolLaw := by
  rw [symBoolDoc_denotation]
  exact symmetricBoolModel_predictedOutcome _ policy

/-- The denoted exemplar model satisfies the full-support contract. -/
theorem symBoolDoc_fullSupport :
    FullSupport (denoteDiscrete symBoolDoc symBoolPayload symBoolConforms) := by
  rw [symBoolDoc_denotation]
  exact symmetricBoolModel_fullSupport _

end FEP.GnnDenotation
