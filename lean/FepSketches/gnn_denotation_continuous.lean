import FepSketches.gnn_document
import FepSketches.linear_gaussian_semigroup
import Mathlib.Data.Fintype.Basic
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.LinearAlgebra.Matrix.Notation

/-!
# GNN continuous-family denotation over the linear-Gaussian carrier

Direction-2 Q3 slice of the fep_lean/GNN bridge
(`specs/gnn-bridge-q3-continuous-denotation`). This module realizes alignment
statement 3 of the bridge program: a well-formed continuous-family GNN document,
read under the frozen conventions fixed in the slice README, denotes an instance
of the `linear_gaussian_semigroup.lean` `LinearGaussianParameters` (`F`/`H`/`Q`/`R`
with `prior_mean`/`prior_cov` payload surface).

The AST and its decidable well-formedness are the accepted Q1 module
`FepSketches.gnn_document` (`FEP.GnnDocument`); this module reuses its
cross-section extractors and the `WellFormed` predicate without modifying them.
The document-lookup helpers mirror the accepted Q2 module (`FEP.GnnDenotation`)
and are re-declared here so the continuous slice does not couple to the
discrete carriers.

Conventions frozen by the slice README (not resolvable from syntax):
  - axis reading: the state variable `x[2, 1]` is read column-convention, first
    dimension `n` = state dimension, carrier axis `Fin n`, slot `i` ↔ `Fin i`;
  - field surface `F`, `H`, `Q`, `R`, `prior_mean`, `prior_cov`, each declared
    with literal dimensions, parameterized, and ontology-bound;
  - denotation (prior gauge): `center := prior_mean`,
    `precision := prior_cov⁻¹` (mechanical inversion of the declared prior
    covariance), so the carrier's derived `covariance` is exactly the declared
    prior covariance;
  - the `F`/`H`/`Q`/`R` values are recorded but not consumed: the carrier has
    no observation fields, and identifying one-step decimal dynamics with the
    carrier's `exp(-t·precision)` law is the P4 no-go (transcendental entries);
  - numeric payload domain `ℝ`, exact rational values (P1 rounding policy);
    `type=float` claims no exactness (rounding boundary explicit);
  - closed-loop `goal_mean`/`control_gain` fields are out of scope.

The payload-string → typed-table interpretation is applied here, not parsed;
the boundary is recorded in the slice README as a finding for the GNN side.

Compilation of this module establishes only the exemplar denotation and its
corollaries on the fixed axis. It establishes nothing about GNN pipeline
behavior (bridge-contract evidence firewall, section 7).
-/

namespace FEP.GnnContinuous

open FEP FEP.LinearGaussianSemigroup FEP.GnnDocument

/-! ## Document lookups (mirroring the Q2 helpers, over the Q1 extractors) -/

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

/-! ## The continuous-family field surface -/

/-- The six continuous-family field variables. -/
def continuousFieldVars : List String :=
  ["F", "H", "Q", "R", "prior_mean", "prior_cov"]

/-- The frozen ontology bindings for the six continuous-family fields. -/
def continuousFieldBindings : List (String × String) :=
  [ ("F", "StateTransitionMatrix"), ("H", "ObservationMatrix"),
    ("Q", "ProcessNoiseCovariance"), ("R", "ObservationNoiseCovariance"),
    ("prior_mean", "PriorMean"), ("prior_cov", "PriorCovariance") ]

/-! ## Continuous payload and conformance -/

/-- Numeric payload tables for the continuous family's six matrix/vector
variables over a finite axis, in the frozen dimension order. The
`fTransition`/`hObservation`/`qProcess`/`rObservation` tables record the
document's one-step dynamics/observation surface; only `priorMean` and
`priorCov` are consumed by the denotation (frozen convention 4). -/
structure ContinuousPayload (Axis : Type*) where
  fTransition : Matrix Axis Axis ℝ
  hObservation : Matrix Axis Axis ℝ
  qProcess : Matrix Axis Axis ℝ
  rObservation : Matrix Axis Axis ℝ
  priorMean : Axis → ℝ
  priorCov : Matrix Axis Axis ℝ

/-- Conformance of a continuous-family document and payload to the frozen
conventions: the document is well-formed; the state variable is declared
`[n, 1]` and the six field variables with literal dimensions over the carrier
axis; each field is parameterized; the six ontology field bindings are
present; and the declared prior covariance is positive definite (the
denotation inverts it). -/
structure ContinuousConforms {Axis : Type*} [Fintype Axis] [DecidableEq Axis]
    (doc : GnnDocument) (nums : ContinuousPayload Axis) : Prop where
  docWellFormed : WellFormed doc
  declX : declDims doc "x" = some [Fintype.card Axis, 1]
  declF : declDims doc "F" = some [Fintype.card Axis, Fintype.card Axis]
  declH : declDims doc "H" = some [Fintype.card Axis, Fintype.card Axis]
  declQ : declDims doc "Q" = some [Fintype.card Axis, Fintype.card Axis]
  declR : declDims doc "R" = some [Fintype.card Axis, Fintype.card Axis]
  declPriorMean : declDims doc "prior_mean" = some [Fintype.card Axis]
  declPriorCov :
    declDims doc "prior_cov" = some [Fintype.card Axis, Fintype.card Axis]
  paramFields : ∀ v, v ∈ continuousFieldVars → parameterizes doc v = true
  ontologyFields :
    ∀ v t, (v, t) ∈ continuousFieldBindings → bindsTerm doc v t = true
  priorCovPosDef : nums.priorCov.PosDef

/-! ## The continuous-family denotation (alignment statement 3) -/

/-- The linear-Gaussian parameters denoted by a conforming continuous-family
document and payload, under the frozen prior gauge: the carrier center is the
document's declared prior mean and the carrier precision is the inverse of the
document's declared prior covariance, so the carrier's derived stationary
`covariance` is exactly the declared prior covariance. -/
noncomputable def denoteContinuous {Axis : Type*} [Fintype Axis] [DecidableEq Axis]
    (doc : GnnDocument) (nums : ContinuousPayload Axis)
    (h : ContinuousConforms doc nums) : LinearGaussianParameters Axis where
  precision := nums.priorCov⁻¹
  precision_posDef := h.priorCovPosDef.inv
  center := WithLp.toLp 2 nums.priorMean

/-- Fieldwise extensionality for `LinearGaussianParameters` (the carrier
declares no `ext` lemma; this local lemma assembles a parameter equality from
its precision and center equalities without unfolding the payload). -/
theorem linearGaussianParameters_ext {Axis : Type*} [Fintype Axis] [DecidableEq Axis]
    (m n : LinearGaussianParameters Axis)
    (h1 : m.precision = n.precision) (h2 : m.center = n.center) : m = n := by
  obtain ⟨p, hp, c⟩ := m
  obtain ⟨p', hp', c'⟩ := n
  subst h1
  subst h2
  rfl

/-- The inverse of a diagonal real matrix with nonzero entries is the diagonal
of the pointwise inverses. This is the mechanical prior-gauge inversion step
the denotation performs on the declared prior covariance. -/
theorem diagonal_inv {n : Type*} [Fintype n] [DecidableEq n] (d : n → ℝ)
    (hd : ∀ i, d i ≠ 0) :
    (Matrix.diagonal d)⁻¹ = Matrix.diagonal fun i => (d i)⁻¹ := by
  apply Matrix.inv_eq_left_inv
  rw [Matrix.diagonal_mul_diagonal]
  ext i j
  simp only [Matrix.diagonal_apply, Matrix.one_apply]
  by_cases h : i = j
  · subst h
    simp [hd i]
  · rw [ite_eq_right h, ite_eq_right h]

/-! ## Fixed exemplar: the stochastic continuous dynamics document -/

/-- Transcription of the canonical exemplar
`GeneralizedNotationNotation/input/gnn_files/continuous/stochastic_dynamics.md`
into the Q1 `GnnDocument` AST: a passive linear-Gaussian LGSSM document with
all six field variables declared, parameterized, and ontology-bound. -/
def sdDoc : GnnDocument where
  sections :=
    [ .gnnSection "ActInfContinuous"
    , .gnnVersionAndFlags .v1 []
    , .modelName "Stochastic Continuous Dynamics Agent"
    , .modelAnnotation
        "A continuous-state Active Inference agent whose dynamics carry \
         explicit process and observation noise, rendered as a native \
         linear-Gaussian state-space model (LGSSM). The agent runs passively \
         — it has no control input: hidden state x = (position, velocity), \
         the Euler-discretized (dt = 0.1) SDE; observation y: two noisy \
         readouts, both reading the position; Q is the process-noise \
         covariance (inverse process precision); R is the observation-noise \
         covariance (inverse observation precision)."
    , .stateSpaceBlock
        [ ⟨"x", [.lit 2, .lit 1], .floatT, none⟩
        , ⟨"y", [.lit 2, .lit 1], .floatT, none⟩
        , ⟨"F", [.lit 2, .lit 2], .floatT, none⟩
        , ⟨"H", [.lit 2, .lit 2], .floatT, none⟩
        , ⟨"Q", [.lit 2, .lit 2], .floatT, none⟩
        , ⟨"R", [.lit 2, .lit 2], .floatT, none⟩
        , ⟨"prior_mean", [.lit 2], .floatT, none⟩
        , ⟨"prior_cov", [.lit 2, .lit 2], .floatT, none⟩
        , ⟨"t", [.lit 1], .intT, none⟩ ]
    , .connections
        [ ⟨"prior_mean", .directed, "x", none⟩
        , ⟨"F", .directed, "x", none⟩
        , ⟨"x", .directed, "y", none⟩
        , ⟨"H", .directed, "y", none⟩
        , ⟨"Q", .directed, "x", none⟩
        , ⟨"R", .directed, "y", none⟩ ]
    , .initialParameterization
        [ ⟨"F", "{(1.0, 0.1), (0.0, 0.9)}"⟩
        , ⟨"H", "{(1.0, 0.0), (1.0, 0.0)}"⟩
        , ⟨"Q", "{(0.1, 0.0), (0.0, 0.1)}"⟩
        , ⟨"R", "{(0.2, 0.0), (0.0, 0.2)}"⟩
        , ⟨"prior_mean", "{(0.0, 0.0)}"⟩
        , ⟨"prior_cov", "{(0.5, 0.0), (0.0, 1.0)}"⟩ ]
    , .equations
        "Generative model (linear-Gaussian state-space): \
         x_1 ~ N(prior_mean, prior_cov); \
         x_t = F x_{t-1} + N(0, Q)      (passive: no control input); \
         y_t = H x_t + N(0, R). \
         SDE reading: dx/dt = F x + eps_state, \
         eps_state ~ N(0, gamma_state^-1 I); \
         y = H x + eps_obs, eps_obs ~ N(0, gamma_obs^-1 I)."
    , .time
        [ ⟨"Time", some "t"⟩, ⟨"Dynamic", none⟩, ⟨"Discrete", none⟩
        , ⟨"ModelTimeHorizon", some "15"⟩ ]
    , .actInfOntologyAnnotation
        [ ⟨"F", "StateTransitionMatrix"⟩, ⟨"H", "ObservationMatrix"⟩
        , ⟨"Q", "ProcessNoiseCovariance"⟩, ⟨"R", "ObservationNoiseCovariance"⟩
        , ⟨"prior_mean", "PriorMean"⟩, ⟨"prior_cov", "PriorCovariance"⟩
        , ⟨"x", "ContinuousHiddenState"⟩, ⟨"y", "ContinuousObservation"⟩
        , ⟨"t", "Time"⟩ ]
    , .modelParameters
        [ ⟨"num_timesteps", "15"⟩, ⟨"dt", "0.1"⟩, ⟨"random_seed", "42"⟩
        , ⟨"num_states", "2"⟩, ⟨"num_observations", "2"⟩ ]
    , .footer
        "Stochastic Continuous Dynamics Agent v1.0 - native linear-Gaussian \
         (LGSSM) GNN model. Passive linear-Gaussian SDE with explicit process \
         and observation noise."
    , .signature "Cryptographic signature goes here" ]

/-- The exemplar's typed payload tables over the two-axis carrier, carrying the
exact transcribed literals (P1 rounding policy): `F = [[1, 1/10], [0, 9/10]]`,
`H = [[1, 0], [1, 0]]`, `Q = (1/10)·I`, `R = (1/5)·I`, `prior_mean = (0, 0)`,
`prior_cov = diag(1/2, 1)`. -/
noncomputable def sdPayload : ContinuousPayload (Fin 2) where
  fTransition := !![1, 1 / 10; 0, 9 / 10]
  hObservation := !![1, 0; 1, 0]
  qProcess := !![1 / 10, 0; 0, 1 / 10]
  rObservation := !![1 / 5, 0; 0, 1 / 5]
  priorMean := fun _ => 0
  priorCov := Matrix.diagonal fun i : Fin 2 => if i = 0 then (1 / 2 : ℝ) else 1

/-- The exemplar document is well-formed under the frozen Q1 surface. -/
theorem sdDoc_wellFormed : WellFormed sdDoc := by decide

theorem sdConforms : ContinuousConforms sdDoc sdPayload := by
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩
  · exact sdDoc_wellFormed
  · simp [declDims, findDecl, stateSpaceDecls, sdDoc, Fintype.card_fin, dimsNat, dimNat]
  · simp [declDims, findDecl, stateSpaceDecls, sdDoc, Fintype.card_fin, dimsNat, dimNat]
  · simp [declDims, findDecl, stateSpaceDecls, sdDoc, Fintype.card_fin, dimsNat, dimNat]
  · simp [declDims, findDecl, stateSpaceDecls, sdDoc, Fintype.card_fin, dimsNat, dimNat]
  · simp [declDims, findDecl, stateSpaceDecls, sdDoc, Fintype.card_fin, dimsNat, dimNat]
  · simp [declDims, findDecl, stateSpaceDecls, sdDoc, Fintype.card_fin, dimsNat, dimNat]
  · simp [declDims, findDecl, stateSpaceDecls, sdDoc, Fintype.card_fin, dimsNat, dimNat]
  · intro v hv
    simp only [continuousFieldVars, List.mem_cons, List.not_mem_nil, or_false] at hv
    rcases hv with rfl | rfl | rfl | rfl | rfl | rfl
    all_goals simp [parameterizes, parameterizationEntries, sdDoc]
  · intro v t hv
    simp only [continuousFieldBindings, List.mem_cons, List.not_mem_nil, or_false] at hv
    rcases hv with ⟨rfl, rfl⟩ | ⟨rfl, rfl⟩ | ⟨rfl, rfl⟩ | ⟨rfl, rfl⟩ | ⟨rfl, rfl⟩ | ⟨rfl, rfl⟩
    all_goals simp [bindsTerm, ontologyBindings, sdDoc]
  · exact Matrix.PosDef.diagonal fun i => by
      by_cases h : i = 0 <;> simp [h]

/-- Hand-stated reference carrier instance for the fixed exemplar: the
two-axis symmetric precision `diag(2, 1)` with zero center, i.e. stationary
covariance `diag(1/2, 1)` — exactly the exemplar document's declared prior.
The acceptance statement below says the frozen prior-gauge convention
mechanically recovers this instance from the document's exact literals. -/
noncomputable def stochasticDynamicsParameters : LinearGaussianParameters (Fin 2) where
  precision := Matrix.diagonal fun i : Fin 2 => if i = 0 then (2 : ℝ) else 1
  precision_posDef := Matrix.PosDef.diagonal fun i => by
    by_cases h : i = 0 <;> simp [h]
  center := WithLp.toLp 2 fun _ => (0 : ℝ)

/-! ## The exemplar isomorphism-class statement -/

/-- The denoted parameters equal the hand-stated reference instance up to the
exact literals: reading the exemplar document under the frozen continuous
conventions recovers `stochasticDynamicsParameters`. The axis enumeration
(slot `i` ↔ `Fin i`) is the isomorphism-class caveat; the swapped enumeration
transports the prior covariance to `diag(1, 1/2)` and the precision to
`diag(1, 2)`, a different instance. -/
theorem sdDoc_denotation :
    denoteContinuous sdDoc sdPayload sdConforms = stochasticDynamicsParameters := by
  apply linearGaussianParameters_ext
  · simp only [denoteContinuous, sdPayload, stochasticDynamicsParameters]
    have hnn : ∀ i : Fin 2, (if i = 0 then (1 / 2 : ℝ) else 1) ≠ 0 := fun i => by
      by_cases h : i = 0 <;> simp [h]
    rw [diagonal_inv _ hnn]
    congr 1
    funext i
    by_cases h : i = 0 <;> simp [h]
  · simp only [denoteContinuous, sdPayload, stochasticDynamicsParameters]

/-! ## Corollaries: the denoted parameters drop into the carrier's laws -/

/-- The denoted exemplar's stationary covariance is exactly the document's
declared prior covariance: the prior gauge makes the carrier's derived
`covariance` read back the document's `prior_cov`. -/
theorem sdDoc_covariance :
    (denoteContinuous sdDoc sdPayload sdConforms).covariance = sdPayload.priorCov := by
  show (sdPayload.priorCov⁻¹)⁻¹ = sdPayload.priorCov
  apply Matrix.inv_eq_right_inv
  exact Matrix.nonsing_inv_mul sdPayload.priorCov
    (sdPayload.priorCov.isUnit_iff_isUnit_det.mp sdConforms.priorCovPosDef.isUnit)

/-- The denoted exemplar's stationary covariance is positive definite: the
document's declared prior is a genuine Gaussian law, not merely a shape. -/
theorem sdDoc_covariance_posDef :
    (denoteContinuous sdDoc sdPayload sdConforms).covariance.PosDef := by
  rw [sdDoc_covariance]
  exact sdConforms.priorCovPosDef

/-- The denoted exemplar's transition mean starts at the input state (the
carrier's zero-time Dirac boundary, via the existing carrier theorem). -/
theorem sdDoc_transitionMean_zero (state : State (Fin 2)) :
    (denoteContinuous sdDoc sdPayload sdConforms).transitionMean 0 state = state := by
  rw [sdDoc_denotation]
  exact LinearGaussianParameters.transitionMean_zero _ state

/-- The denoted exemplar's transition covariance vanishes at time zero (the
carrier's zero-time Dirac boundary, via the existing carrier theorem). -/
theorem sdDoc_transitionCovariance_zero :
    (denoteContinuous sdDoc sdPayload sdConforms).transitionCovariance 0 = 0 := by
  rw [sdDoc_denotation]
  exact LinearGaussianParameters.transitionCovariance_zero _

end FEP.GnnContinuous
