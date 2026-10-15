module
public import FepSketches.controlled_markov

@[expose] public section

/-!
# Finite temporal and hierarchical inference

This module develops normalized forward filtering, nonnegative backward
information messages, forward--backward smoothing, hierarchical prediction,
and Bayesian model averaging on the shared finite-law carrier.  Every
posterior or smoother exposes its positive-normalizer premise.  An asymmetric
Boolean HMM evaluates the filter, backward evidence, and smoother exactly.
-/

namespace FEP.TemporalInference

open FEP FEP.ControlledMarkov Finset
open scoped BigOperators

variable {State Observation Model Upper Middle : Type*}
  [Fintype State] [Fintype Observation] [Fintype Model]
  [Fintype Upper] [Fintype Middle]

/-- A time-homogeneous finite hidden Markov model. -/
structure FiniteHMM (State Observation : Type*)
    [Fintype State] [Fintype Observation] where
  initial : FiniteLaw State
  transition : FiniteKernel State State
  emission : FiniteKernel State Observation

/-- One hidden-state prediction step. -/
def forwardPrediction (prior : FiniteLaw State)
    (transition : FiniteKernel State State) : FiniteLaw State :=
  transition.predictive prior

/-- Evidence of one observation following a hidden-state transition. -/
def forwardEvidence (prior : FiniteLaw State)
    (transition : FiniteKernel State State)
    (emission : FiniteKernel State Observation) (observation : Observation) : ℝ :=
  emission.predictive (forwardPrediction prior transition) observation

/-- One normalized hidden-Markov forward-filtering update. -/
noncomputable def forwardFilter (prior : FiniteLaw State)
    (transition : FiniteKernel State State)
    (emission : FiniteKernel State Observation) (observation : Observation)
    (hEvidence : 0 < forwardEvidence prior transition emission observation) :
    FiniteLaw State :=
  emission.posterior (forwardPrediction prior transition) observation hEvidence

/-- The forward filter reconstructs the predicted state-observation joint. -/
theorem forwardFilter_reconstruction (prior : FiniteLaw State)
    (transition : FiniteKernel State State)
    (emission : FiniteKernel State Observation) (observation : Observation)
    (hEvidence : 0 < forwardEvidence prior transition emission observation)
    (state : State) :
    forwardFilter prior transition emission observation hEvidence state *
        forwardEvidence prior transition emission observation =
      forwardPrediction prior transition state * emission state observation := by
  exact FiniteKernel.posterior_mul_predictive
    (forwardPrediction prior transition) emission observation hEvidence state

/-- Every positive-evidence forward-filtering update is normalized. -/
theorem forwardFilter_sum_one (prior : FiniteLaw State)
    (transition : FiniteKernel State State)
    (emission : FiniteKernel State Observation) (observation : Observation)
    (hEvidence : 0 < forwardEvidence prior transition emission observation) :
    ∑ state, forwardFilter prior transition emission observation hEvidence state =
      1 :=
  (forwardFilter prior transition emission observation hEvidence).sum_one

/-- Zero observation evidence is explicitly outside the normalized forward
filter's positive-denominator construction boundary. -/
theorem forwardEvidence_zero_boundary (prior : FiniteLaw State)
    (transition : FiniteKernel State State)
    (emission : FiniteKernel State Observation) (observation : Observation)
    (hZero : forwardEvidence prior transition emission observation = 0) :
    ¬0 < forwardEvidence prior transition emission observation := by
  rw [hZero]
  exact lt_irrefl 0

/-- One backward information-message step. -/
noncomputable def backwardMessageStep (transition : FiniteKernel State State)
    (emission : FiniteKernel State Observation) (observation : Observation)
    (nextMessage : State → ℝ) (state : State) : ℝ :=
  ∑ nextState,
    transition state nextState * emission nextState observation *
      nextMessage nextState

/-- Backward recursion over a finite list of future observations. -/
noncomputable def backwardMessage (transition : FiniteKernel State State)
    (emission : FiniteKernel State Observation) :
    List Observation → State → ℝ
  | [], _ => 1
  | observation :: future, state =>
      backwardMessageStep transition emission observation
        (backwardMessage transition emission future) state

/-- Exact successor equation for the backward information recursion. -/
theorem backwardMessage_cons (transition : FiniteKernel State State)
    (emission : FiniteKernel State Observation) (observation : Observation)
    (future : List Observation) (state : State) :
    backwardMessage transition emission (observation :: future) state =
      backwardMessageStep transition emission observation
        (backwardMessage transition emission future) state :=
  rfl

/-- Nonnegative next messages produce a nonnegative backward message. -/
theorem backwardMessage_nonneg (transition : FiniteKernel State State)
    (emission : FiniteKernel State Observation) (observation : Observation)
    (nextMessage : State → ℝ) (hMessage : ∀ state, 0 ≤ nextMessage state)
    (state : State) :
    0 ≤ backwardMessageStep transition emission observation nextMessage state := by
  exact Finset.sum_nonneg fun nextState _ =>
    mul_nonneg
      (mul_nonneg (transition.nonneg state nextState)
        (emission.nonneg nextState observation))
      (hMessage nextState)

/-- Evidence evaluated from the initial law and one backward message. -/
noncomputable def backwardEvidence (prior : FiniteLaw State)
    (transition : FiniteKernel State State)
    (emission : FiniteKernel State Observation) (observation : Observation) : ℝ :=
  ∑ state, prior state *
    backwardMessageStep transition emission observation (fun _ => 1) state

/-- Forward marginalization and the one-step backward message compute the same
observation evidence. -/
theorem forward_backward_evidence_agree (prior : FiniteLaw State)
    (transition : FiniteKernel State State)
    (emission : FiniteKernel State Observation) (observation : Observation) :
    forwardEvidence prior transition emission observation =
      backwardEvidence prior transition emission observation := by
  simp only [forwardEvidence, forwardPrediction, backwardEvidence,
    backwardMessageStep, FiniteKernel.predictive_mass, mul_one]
  simp_rw [Finset.sum_mul, Finset.mul_sum]
  rw [Finset.sum_comm]
  apply Finset.sum_congr rfl
  intro state _
  apply Finset.sum_congr rfl
  intro nextState _
  ring

/-- Normalizer for a filtered law tilted by a backward information message. -/
noncomputable def smoothingNormalizer (filtered : FiniteLaw State)
    (backward : State → ℝ) : ℝ :=
  ∑ state, filtered state * backward state

/-- Normalized forward--backward smoothing marginal at positive normalizer. -/
noncomputable def forwardBackwardSmoothing (filtered : FiniteLaw State)
    (backward : State → ℝ) (hBackward : ∀ state, 0 ≤ backward state)
    (hNormalizer : 0 < smoothingNormalizer filtered backward) : FiniteLaw State where
  mass state := filtered state * backward state /
    smoothingNormalizer filtered backward
  nonneg state := div_nonneg
    (mul_nonneg (filtered.nonneg state) (hBackward state)) hNormalizer.le
  sum_one := by
    rw [← Finset.sum_div]
    exact div_self (ne_of_gt hNormalizer)

/-- Smoothing mass times its normalizer is the forward--backward product. -/
theorem forwardBackwardSmoothing_factorization (filtered : FiniteLaw State)
    (backward : State → ℝ) (hBackward : ∀ state, 0 ≤ backward state)
    (hNormalizer : 0 < smoothingNormalizer filtered backward) (state : State) :
    forwardBackwardSmoothing filtered backward hBackward hNormalizer state *
        smoothingNormalizer filtered backward =
      filtered state * backward state := by
  exact div_mul_cancel₀ _ (ne_of_gt hNormalizer)

/-- Every positive-normalizer smoothing marginal sums exactly to one. -/
theorem forwardBackwardSmoothing_sum_one (filtered : FiniteLaw State)
    (backward : State → ℝ) (hBackward : ∀ state, 0 ≤ backward state)
    (hNormalizer : 0 < smoothingNormalizer filtered backward) :
    ∑ state, forwardBackwardSmoothing filtered backward hBackward hNormalizer state =
      1 :=
  (forwardBackwardSmoothing filtered backward hBackward hNormalizer).sum_one

/-- A zero smoothing normalizer cannot satisfy the construction's required
positive-evidence boundary. -/
theorem smoothingNormalizer_zero_boundary (filtered : FiniteLaw State)
    (backward : State → ℝ)
    (hZero : smoothingNormalizer filtered backward = 0) :
    ¬0 < smoothingNormalizer filtered backward := by
  rw [hZero]
  exact lt_irrefl 0

/-- One normalized variational state update, expressed as a prior-weighted
Boltzmann tilt on the shared finite-law carrier. -/
noncomputable def variationalStateUpdate (prior : FiniteLaw State)
    (energy : State → ℝ) : FiniteLaw State :=
  boltzmannPosterior prior energy

/-- A one-step finite variational state update is normalized. -/
theorem variationalStateUpdate_sum_one (prior : FiniteLaw State)
    (energy : State → ℝ) :
    ∑ state, variationalStateUpdate prior energy state = 1 :=
  (variationalStateUpdate prior energy).sum_one

/-- A normalized variational state mass reconstructs its unnormalized tilt. -/
theorem variationalStateUpdate_reconstruction (prior : FiniteLaw State)
    (energy : State → ℝ) (state : State) :
    variationalStateUpdate prior energy state * boltzmannPartition prior energy =
      boltzmannWeight prior energy state :=
  boltzmannPosterior_mul_partition prior energy state

/-- Zero variational energy is the identity update on every finite prior. -/
theorem variationalStateUpdate_zero_energy (prior : FiniteLaw State) :
    variationalStateUpdate prior (fun _ => 0) = prior := by
  exact boltzmannPosterior_zero_energy prior

/-- Predict through a two-level finite hierarchy. -/
def hierarchicalPredictive (top : FiniteLaw Upper)
    (upperKernel : FiniteKernel Upper Middle)
    (lowerKernel : FiniteKernel Middle Observation) : FiniteLaw Observation :=
  lowerKernel.predictive (upperKernel.predictive top)

/-- Two-level hierarchical prediction is prediction through the composed
normalized kernel. -/
theorem hierarchicalPredictive_eq (top : FiniteLaw Upper)
    (upperKernel : FiniteKernel Upper Middle)
    (lowerKernel : FiniteKernel Middle Observation) :
    hierarchicalPredictive top upperKernel lowerKernel =
      (FiniteKernel.comp lowerKernel upperKernel).predictive top := by
  exact (FiniteKernel.predictive_comp top lowerKernel upperKernel).symm

/-- Pointwise two-level predictive factorization. -/
theorem hierarchicalPredictive_mass (top : FiniteLaw Upper)
    (upperKernel : FiniteKernel Upper Middle)
    (lowerKernel : FiniteKernel Middle Observation) (observation : Observation) :
    hierarchicalPredictive top upperKernel lowerKernel observation =
      ∑ middle,
        (∑ upper, top upper * upperKernel upper middle) *
          lowerKernel middle observation :=
  rfl

/-- Bayesian model-averaged predictive law. -/
def modelAverage (modelPrior : FiniteLaw Model)
    (modelPredictive : FiniteKernel Model Observation) : FiniteLaw Observation :=
  modelPredictive.predictive modelPrior

/-- Bayesian model averaging expands into its finite predictive mixture. -/
theorem modelAverage_mass (modelPrior : FiniteLaw Model)
    (modelPredictive : FiniteKernel Model Observation)
    (observation : Observation) :
    modelAverage modelPrior modelPredictive observation =
      ∑ model, modelPrior model * modelPredictive model observation :=
  rfl

/-- Every Bayesian model-averaged predictive law is normalized. -/
theorem modelAverage_sum_one (modelPrior : FiniteLaw Model)
    (modelPredictive : FiniteKernel Model Observation) :
    ∑ observation, modelAverage modelPrior modelPredictive observation = 1 :=
  (modelAverage modelPrior modelPredictive).sum_one

/-! ## Exact asymmetric Boolean HMM witness -/

/-- Boolean initial state with mass `3/4` on `true`. -/
noncomputable def boolInitialLaw : FiniteLaw Bool where
  mass state := if state then 3 / 4 else 1 / 4
  nonneg state := by cases state <;> norm_num
  sum_one := by rw [Fintype.sum_bool]; norm_num

/-- Sticky Boolean transition: stay with probability `3/4`. -/
noncomputable def boolStickyTransition : FiniteKernel Bool Bool where
  mass state nextState := if nextState = state then 3 / 4 else 1 / 4
  nonneg state nextState := by split <;> norm_num
  sum_one state := by cases state <;> rw [Fintype.sum_bool] <;> norm_num

/-- Accurate Boolean emission: report the state with probability `4/5`. -/
noncomputable def boolAccurateEmission : FiniteKernel Bool Bool where
  mass state observation := if observation = state then 4 / 5 else 1 / 5
  nonneg state observation := by split <;> norm_num
  sum_one state := by cases state <;> rw [Fintype.sum_bool] <;> norm_num

/-- Nontrivial asymmetric Boolean hidden Markov model. -/
noncomputable def boolHMM : FiniteHMM Bool Bool where
  initial := boolInitialLaw
  transition := boolStickyTransition
  emission := boolAccurateEmission

/-- The asymmetric Boolean model mixture predicts `true` with mass `13/20`. -/
theorem boolModelAverage_true_mass :
    modelAverage boolInitialLaw boolAccurateEmission true = 13 / 20 := by
  norm_num [modelAverage, FiniteKernel.predictive_mass, boolInitialLaw,
    boolAccurateEmission, Fintype.sum_bool]

/-- The asymmetric Boolean model mixture predicts `false` with mass `7/20`. -/
theorem boolModelAverage_false_mass :
    modelAverage boolInitialLaw boolAccurateEmission false = 7 / 20 := by
  norm_num [modelAverage, FiniteKernel.predictive_mass, boolInitialLaw,
    boolAccurateEmission, Fintype.sum_bool]

/-- After one sticky transition, predicted mass of `true` is `5/8`. -/
theorem boolPrediction_true_mass :
    forwardPrediction boolInitialLaw boolStickyTransition true = 5 / 8 := by
  norm_num [forwardPrediction, FiniteKernel.predictive_mass, boolInitialLaw,
    boolStickyTransition, Fintype.sum_bool]

/-- After one sticky transition, predicted mass of `false` is `3/8`. -/
theorem boolPrediction_false_mass :
    forwardPrediction boolInitialLaw boolStickyTransition false = 3 / 8 := by
  norm_num [forwardPrediction, FiniteKernel.predictive_mass, boolInitialLaw,
    boolStickyTransition, Fintype.sum_bool]

/-- Evidence of a `true` report is exactly `23/40`. -/
theorem boolForwardEvidence_true :
    forwardEvidence boolInitialLaw boolStickyTransition boolAccurateEmission true =
      23 / 40 := by
  norm_num [forwardEvidence, forwardPrediction, FiniteKernel.predictive_mass,
    boolInitialLaw, boolStickyTransition, boolAccurateEmission,
    Fintype.sum_bool]

/-- The Boolean witness's selected observation has positive evidence. -/
theorem boolForwardEvidence_true_pos :
    0 < forwardEvidence boolInitialLaw boolStickyTransition
      boolAccurateEmission true := by
  rw [boolForwardEvidence_true]
  norm_num

/-- Normalized forward filter after observing `true`. -/
noncomputable def boolForwardFilter : FiniteLaw Bool :=
  forwardFilter boolInitialLaw boolStickyTransition boolAccurateEmission true
    boolForwardEvidence_true_pos

/-- The filtered mass of `true` is exactly `20/23`. -/
theorem boolForwardFilter_true_mass :
    boolForwardFilter true = 20 / 23 := by
  have hReconstruction := forwardFilter_reconstruction boolInitialLaw
    boolStickyTransition boolAccurateEmission true
    boolForwardEvidence_true_pos true
  rw [boolForwardEvidence_true, boolPrediction_true_mass] at hReconstruction
  norm_num [boolForwardFilter, boolAccurateEmission] at hReconstruction ⊢
  linarith

/-- The filtered mass of `false` is exactly `3/23`. -/
theorem boolForwardFilter_false_mass :
    boolForwardFilter false = 3 / 23 := by
  have hReconstruction := forwardFilter_reconstruction boolInitialLaw
    boolStickyTransition boolAccurateEmission true
    boolForwardEvidence_true_pos false
  rw [boolForwardEvidence_true, boolPrediction_false_mass] at hReconstruction
  norm_num [boolForwardFilter, boolAccurateEmission] at hReconstruction ⊢
  linarith

/-- Exact Boolean forward-filter normalization. -/
theorem boolForwardFilter_sum_one :
    boolForwardFilter false + boolForwardFilter true = 1 := by
  rw [boolForwardFilter_false_mass, boolForwardFilter_true_mass]
  norm_num

/-- One-step Boolean backward information message for a `true` report. -/
noncomputable def boolBackwardMessage (state : Bool) : ℝ :=
  backwardMessageStep boolStickyTransition boolAccurateEmission true
    (fun _ => 1) state

/-- Backward message at `true` is exactly `13/20`. -/
theorem boolBackwardMessage_true_mass :
    boolBackwardMessage true = 13 / 20 := by
  norm_num [boolBackwardMessage, backwardMessageStep, boolStickyTransition,
    boolAccurateEmission, Fintype.sum_bool]

/-- Backward message at `false` is exactly `7/20`. -/
theorem boolBackwardMessage_false_mass :
    boolBackwardMessage false = 7 / 20 := by
  norm_num [boolBackwardMessage, backwardMessageStep, boolStickyTransition,
    boolAccurateEmission, Fintype.sum_bool]

/-- The Boolean backward message is nonnegative at every state. -/
theorem boolBackwardMessage_nonneg (state : Bool) :
    0 ≤ boolBackwardMessage state := by
  cases state <;>
    norm_num [boolBackwardMessage_false_mass, boolBackwardMessage_true_mass]

/-- The backward calculation agrees with forward evidence at `23/40`. -/
theorem boolBackwardEvidence_eq :
    backwardEvidence boolInitialLaw boolStickyTransition
        boolAccurateEmission true = 23 / 40 := by
  rw [← forward_backward_evidence_agree, boolForwardEvidence_true]

/-- The Boolean smoothing normalizer is the same `23/40` evidence. -/
theorem boolSmoothingNormalizer_eq :
    smoothingNormalizer boolInitialLaw boolBackwardMessage = 23 / 40 := by
  rw [smoothingNormalizer, Fintype.sum_bool,
    boolBackwardMessage_false_mass, boolBackwardMessage_true_mass]
  norm_num [boolInitialLaw]

/-- The Boolean smoothing normalizer is strictly positive. -/
theorem boolSmoothingNormalizer_pos :
    0 < smoothingNormalizer boolInitialLaw boolBackwardMessage := by
  rw [boolSmoothingNormalizer_eq]
  norm_num

/-- Smoothed initial-state law given the next `true` observation. -/
noncomputable def boolSmoothing : FiniteLaw Bool :=
  forwardBackwardSmoothing boolInitialLaw boolBackwardMessage
    boolBackwardMessage_nonneg boolSmoothingNormalizer_pos

/-- Smoothed mass of the initial `true` state is exactly `39/46`. -/
theorem boolSmoothing_true_mass :
    boolSmoothing true = 39 / 46 := by
  have hFactorization := forwardBackwardSmoothing_factorization
    boolInitialLaw boolBackwardMessage boolBackwardMessage_nonneg
    boolSmoothingNormalizer_pos true
  rw [boolSmoothingNormalizer_eq, boolBackwardMessage_true_mass]
    at hFactorization
  norm_num [boolSmoothing, boolInitialLaw] at hFactorization ⊢
  linarith

/-- Smoothed mass of the initial `false` state is exactly `7/46`. -/
theorem boolSmoothing_false_mass :
    boolSmoothing false = 7 / 46 := by
  have hFactorization := forwardBackwardSmoothing_factorization
    boolInitialLaw boolBackwardMessage boolBackwardMessage_nonneg
    boolSmoothingNormalizer_pos false
  rw [boolSmoothingNormalizer_eq, boolBackwardMessage_false_mass]
    at hFactorization
  norm_num [boolSmoothing, boolInitialLaw] at hFactorization ⊢
  linarith

/-- Exact Boolean forward--backward smoothing normalization. -/
theorem boolSmoothing_sum_one :
    boolSmoothing false + boolSmoothing true = 1 := by
  rw [boolSmoothing_false_mass, boolSmoothing_true_mass]
  norm_num

/-! ## Sum-product message passing on finite rooted trees

A `PTree S` is a finite rooted tree of variables over the finite state space
`S`.  Each node carries a nonnegative node potential and, for each of its
children, an edge potential indexed by (parent state, child state).  The
joint weight of a configuration is the product of all node and edge
potentials; the exact marginal is obtained by brute-force summation over every
configuration.  Sum-product messages are defined by structural recursion on the
tree, and `rootBelief_eq_exactMarginal` states that the normalised product of
incoming messages at the root is that exact marginal.  A three-cycle witness
shows that the same one-pass message product is not the marginal on a loopy
graph.  The theorems certify exact finite sum-product identities for these
potentials only; they are not a statement about convergence of loopy belief
propagation. -/

universe uS

/-- A finite rooted tree of variables over the state space `S`: a node
potential, a finite number of children, and an edge potential
(parent state, child state) for each child. -/
inductive PTree (S : Type uS) where
  | node (potential : S → ℝ) (arity : ℕ) (edge : Fin arity → S → S → ℝ)
      (child : Fin arity → PTree S) : PTree S

namespace PTree

variable {S : Type uS}

/-- A leaf: a node with no children. -/
def leaf (potential : S → ℝ) : PTree S :=
  node potential 0 (fun i => i.elim0) (fun i => i.elim0)

/-- All potentials of the tree are nonnegative. -/
def Nonneg : PTree S → Prop
  | node φ n ψ c =>
    (∀ s, 0 ≤ φ s) ∧ (∀ i s y, 0 ≤ ψ i s y) ∧ ∀ i : Fin n, Nonneg (c i)

/-- Joint configurations: one state per node of the tree. -/
def Conf : PTree S → Type uS
  | node _ n _ c => S × ∀ i : Fin n, Conf (c i)

/-- The state a configuration assigns to the root. -/
def Conf.root : (t : PTree S) → Conf t → S
  | node _ _ _ _, x => x.1

/-- Finiteness of the configuration space. -/
@[instance_reducible]
def fintypeConf [Fintype S] : (t : PTree S) → Fintype (Conf t)
  | node _ n _ c =>
    haveI : ∀ i : Fin n, Fintype (Conf (c i)) := fun i => fintypeConf (c i)
    inferInstanceAs (Fintype (S × ∀ i : Fin n, Conf (c i)))

attribute [instance] fintypeConf

/-- Unnormalised joint weight: the product of every node and edge potential. -/
noncomputable def weight : (t : PTree S) → Conf t → ℝ
  | node φ n ψ c, x =>
    φ x.1 * ∏ i : Fin n,
      ψ i x.1 (Conf.root (c i) (x.2 i)) * weight (c i) (x.2 i)

section Messages

variable [Fintype S]

/-- Brute-force unnormalised marginal: the total weight of all
configurations whose root is in state `s`. -/
noncomputable def bruteMass [DecidableEq S] (t : PTree S) (s : S) : ℝ :=
  ∑ x : Conf t, if Conf.root t x = s then weight t x else 0

/-- Total weight of all configurations. -/
noncomputable def totalWeight (t : PTree S) : ℝ := ∑ x : Conf t, weight t x

/-- Exact marginal at the root, computed by brute-force summation. -/
noncomputable def exactMarginal [DecidableEq S] (t : PTree S) (s : S) : ℝ :=
  bruteMass t s / totalWeight t

/-- Unnormalised sum-product belief at a node: its potential times the
product of the messages from its children. -/
noncomputable def msg : PTree S → S → ℝ
  | node φ n ψ c, s => φ s * ∏ i : Fin n, ∑ y, ψ i s y * msg (c i) y

/-- The message sent by child `i` of a node to that node, as a function of the
parent state. -/
noncomputable def childMessage (ψ : S → S → ℝ) (child : PTree S) (s : S) : ℝ :=
  ∑ y, ψ s y * msg child y

/-- Normaliser of the root belief. -/
noncomputable def beliefNormalizer (t : PTree S) : ℝ := ∑ y, msg t y

/-- Normalised product of incoming messages at the root. -/
noncomputable def rootBelief (t : PTree S) (s : S) : ℝ :=
  msg t s / beliefNormalizer t

/-- The root belief of a node is its potential times the product of the
incoming child messages, normalised. -/
theorem rootBelief_node (φ : S → ℝ) (n : ℕ) (ψ : Fin n → S → S → ℝ)
    (c : Fin n → PTree S) (s : S) :
    rootBelief (node φ n ψ c) s =
      (φ s * ∏ i : Fin n, childMessage (ψ i) (c i) s) /
        ∑ y, φ y * ∏ i : Fin n, childMessage (ψ i) (c i) y :=
  rfl

/-- Summing a root-dependent weight over configurations groups them by root
state. -/
theorem sum_root_weight [DecidableEq S] (t : PTree S) (F : S → ℝ) :
    ∑ x : Conf t, F (Conf.root t x) * weight t x =
      ∑ y, F y * bruteMass t y := by
  simp only [bruteMass, Finset.mul_sum]
  rw [Finset.sum_comm]
  refine Finset.sum_congr rfl fun x _ => ?_
  simp [mul_ite]

/-- Total weight is the sum of the brute-force root masses. -/
theorem totalWeight_eq_sum_bruteMass [DecidableEq S] (t : PTree S) :
    totalWeight t = ∑ y, bruteMass t y := by
  simpa [totalWeight] using sum_root_weight t (fun _ => 1)

/-- Sum-product messages compute the brute-force unnormalised marginal. -/
theorem msg_eq_bruteMass [DecidableEq S] (t : PTree S) (s : S) :
    msg t s = bruteMass t s := by
  induction t generalizing s with
  | node φ n ψ c ih =>
    have hsum : ∑ x : Conf (node φ n ψ c),
        (if Conf.root (node φ n ψ c) x = s then
          weight (node φ n ψ c) x else 0) =
        ∑ f : (∀ i : Fin n, Conf (c i)),
          φ s * ∏ i : Fin n,
            ψ i s (Conf.root (c i) (f i)) * weight (c i) (f i) := by
      change ∑ x : S × (∀ i : Fin n, Conf (c i)),
        (if x.1 = s then φ x.1 * ∏ i : Fin n,
          ψ i x.1 (Conf.root (c i) (x.2 i)) * weight (c i) (x.2 i) else 0) = _
      rw [Fintype.sum_prod_type]
      simp
    rw [bruteMass, hsum, ← Finset.mul_sum]
    have hprod := Finset.prod_univ_sum (fun i : Fin n => (Finset.univ : Finset (Conf (c i))))
      (fun i x => ψ i s (Conf.root (c i) x) * weight (c i) x)
    rw [Fintype.piFinset_univ] at hprod
    rw [← hprod, msg]
    congr 1
    refine Finset.prod_congr rfl fun i _ => ?_
    rw [sum_root_weight (c i) (fun y => ψ i s y)]
    exact Finset.sum_congr rfl fun y _ => by rw [ih i y]

/-- The normaliser of the root belief is the total configuration weight. -/
theorem beliefNormalizer_eq_totalWeight [DecidableEq S] (t : PTree S) :
    beliefNormalizer t = totalWeight t := by
  rw [totalWeight_eq_sum_bruteMass, beliefNormalizer]
  exact Finset.sum_congr rfl fun y _ => msg_eq_bruteMass t y

/-- Sum-product exactness on finite trees: the normalised product of incoming
messages at the root equals the exact marginal of the joint
`∝ ∏ node potentials · ∏ edge potentials` computed by brute-force summation
over all configurations. -/
theorem rootBelief_eq_exactMarginal [DecidableEq S] (t : PTree S) (s : S) :
    rootBelief t s = exactMarginal t s := by
  rw [rootBelief, exactMarginal, msg_eq_bruteMass, beliefNormalizer_eq_totalWeight]

/-- Messages are nonnegative when all potentials are. -/
theorem msg_nonneg : (t : PTree S) → t.Nonneg → ∀ s, 0 ≤ msg t s
  | node φ n ψ c, ⟨hφ, hψ, hc⟩, s => by
    rw [msg]
    exact mul_nonneg (hφ s) (Finset.prod_nonneg fun i _ =>
      Finset.sum_nonneg fun y _ => mul_nonneg (hψ i s y) (msg_nonneg (c i) (hc i) y))

/-- With nonnegative potentials and positive total weight, the root belief is
a probability law. -/
theorem rootBelief_sum_one [DecidableEq S] (t : PTree S) (hpos : 0 < totalWeight t) :
    ∑ s, rootBelief t s = 1 := by
  have h : beliefNormalizer t ≠ 0 := by
    rw [beliefNormalizer_eq_totalWeight]; exact hpos.ne'
  simp only [rootBelief]
  rw [← Finset.sum_div]
  exact div_self h

/-- Root beliefs are nonnegative for nonnegative potentials. -/
theorem rootBelief_nonneg (t : PTree S) (ht : t.Nonneg) (s : S) :
    0 ≤ rootBelief t s := by
  refine div_nonneg (msg_nonneg t ht s) ?_
  exact Finset.sum_nonneg fun y _ => msg_nonneg t ht y

end Messages

end PTree

/-! ### A three-node star witness and a three-cycle countermodel -/

open PTree

/-- Leaf potential on `Bool`: weight `3` on `true`, `1` on `false`. -/
def spLeafPotential (b : Bool) : ℝ := if b then 3 else 1

/-- Ferromagnetic edge potential: `2` for agreement, `1` for disagreement. -/
def spEdge (x y : Bool) : ℝ := if x = y then 2 else 1

/-- A three-node star: a root with unit potential and two leaves. -/
def spStar : PTree Bool :=
  PTree.node (fun _ => 1) 2 (fun _ => spEdge) (fun _ => PTree.leaf spLeafPotential)

/-- Explicit joint weight of the star on `(root, leaf₁, leaf₂)`. -/
def spStarJoint (x₀ x₁ x₂ : Bool) : ℝ :=
  spEdge x₀ x₁ * spEdge x₀ x₂ * spLeafPotential x₁ * spLeafPotential x₂

/-- Explicit joint weight of the three-cycle on `(x₀, x₁, x₂)`: the star
weight together with the closing edge between the two leaves. -/
def spCycleJoint (x₀ x₁ x₂ : Bool) : ℝ :=
  spStarJoint x₀ x₁ x₂ * spEdge x₁ x₂

/-- The star's sum-product message at root state `true`. -/
theorem spStar_msg_true : PTree.msg spStar true = 49 := by
  norm_num [spStar, PTree.leaf, PTree.msg, Fin.prod_univ_two, Fintype.sum_bool,
    spEdge, spLeafPotential]

/-- The star's sum-product message at root state `false`. -/
theorem spStar_msg_false : PTree.msg spStar false = 25 := by
  norm_num [spStar, PTree.leaf, PTree.msg, Fin.prod_univ_two, Fintype.sum_bool,
    spEdge, spLeafPotential]

/-- The star root belief at `true` is `49/74`. -/
theorem spStar_rootBelief_true : PTree.rootBelief spStar true = 49 / 74 := by
  rw [PTree.rootBelief, PTree.beliefNormalizer, Fintype.sum_bool,
    spStar_msg_true, spStar_msg_false]
  norm_num

/-- Brute-force enumeration of all eight configurations of the star gives the
root marginal `49/74` at `true`, independently of the message recursion. -/
theorem spStar_bruteForce_true :
    (∑ x₁ : Bool, ∑ x₂ : Bool, spStarJoint true x₁ x₂) /
        (∑ x₀ : Bool, ∑ x₁ : Bool, ∑ x₂ : Bool, spStarJoint x₀ x₁ x₂) =
      49 / 74 := by
  norm_num [Fintype.sum_bool, spStarJoint, spEdge, spLeafPotential]

/-- The tree-recursion exact marginal of the star agrees with the explicit
eight-configuration enumeration. -/
theorem spStar_exactMarginal_true : PTree.exactMarginal spStar true = 49 / 74 := by
  rw [← PTree.rootBelief_eq_exactMarginal, spStar_rootBelief_true]

/-- True marginal of node `0` on the three-cycle, by brute force over all
eight configurations: `43/62`. -/
theorem spCycle_marginal_true :
    (∑ x₁ : Bool, ∑ x₂ : Bool, spCycleJoint true x₁ x₂) /
        (∑ x₀ : Bool, ∑ x₁ : Bool, ∑ x₂ : Bool, spCycleJoint x₀ x₁ x₂) =
      43 / 62 := by
  norm_num [Fintype.sum_bool, spCycleJoint, spStarJoint, spEdge, spLeafPotential]

/-- Countermodel: on the loopy three-cycle the naive message product (the
star belief that ignores the closing edge) is not the true marginal. -/
theorem spCycle_naive_message_product_ne_marginal :
    PTree.rootBelief spStar true ≠
      (∑ x₁ : Bool, ∑ x₂ : Bool, spCycleJoint true x₁ x₂) /
        (∑ x₀ : Bool, ∑ x₁ : Bool, ∑ x₂ : Bool, spCycleJoint x₀ x₁ x₂) := by
  rw [spStar_rootBelief_true, spCycle_marginal_true]
  norm_num

/-! ### The fep-007 local update as a one-edge sum-product instance -/

/-- Normalised local sum-product update on an arbitrary finite carrier:
the edge potential times the incoming message, normalised over the selected
neighbour support and extended by zero outside it.  On `Fin 8` this is the
fep-007 normalised message. -/
noncomputable def localUpdate {S : Type uS} [DecidableEq S]
    (ψ : S → S → ℝ) (incoming : S → ℝ) (neighbors : Finset S) (i j : S) : ℝ :=
  if j ∈ neighbors then
    ψ i j * incoming j / ∑ k ∈ neighbors, ψ i k * incoming k
  else 0

/-- The one-edge tree: root `j` carries the incoming message restricted to the
neighbour support, and its single child carries the point mass at `i`. -/
noncomputable def oneEdgeTree {S : Type uS} [DecidableEq S]
    (ψ : S → S → ℝ) (incoming : S → ℝ) (neighbors : Finset S) (i : S) : PTree S :=
  PTree.node (fun s => if s ∈ neighbors then incoming s else 0) 1
    (fun _ s y => ψ y s) (fun _ => PTree.leaf (fun y => if y = i then 1 else 0))

/-- The fep-007 local update is the root belief of a one-edge tree, on any
finite carrier. -/
theorem localUpdate_eq_oneEdge_rootBelief {S : Type uS} [Fintype S] [DecidableEq S]
    (ψ : S → S → ℝ) (incoming : S → ℝ) (neighbors : Finset S) (i j : S) :
    localUpdate ψ incoming neighbors i j =
      PTree.rootBelief (oneEdgeTree ψ incoming neighbors i) j := by
  have hmsg : ∀ s, PTree.msg (oneEdgeTree ψ incoming neighbors i) s =
      if s ∈ neighbors then ψ i s * incoming s else 0 := by
    intro s
    by_cases hs : s ∈ neighbors <;>
      simp [oneEdgeTree, PTree.leaf, PTree.msg, hs, mul_comm]
  have hnorm : PTree.beliefNormalizer (oneEdgeTree ψ incoming neighbors i) =
      ∑ k ∈ neighbors, ψ i k * incoming k := by
    rw [PTree.beliefNormalizer]
    simp_rw [hmsg]
    rw [Finset.sum_ite_mem, Finset.univ_inter]
  rw [localUpdate, PTree.rootBelief, hmsg, hnorm]
  by_cases hj : j ∈ neighbors <;> simp [hj]

/-- The fep-007 local update equals the brute-force exact marginal of the
one-edge model, on any finite carrier. -/
theorem localUpdate_eq_oneEdge_exactMarginal {S : Type uS} [Fintype S] [DecidableEq S]
    (ψ : S → S → ℝ) (incoming : S → ℝ) (neighbors : Finset S) (i j : S) :
    localUpdate ψ incoming neighbors i j =
      PTree.exactMarginal (oneEdgeTree ψ incoming neighbors i) j := by
  rw [localUpdate_eq_oneEdge_rootBelief, PTree.rootBelief_eq_exactMarginal]


end FEP.TemporalInference
