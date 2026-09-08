# Horizon 1: finite synthesis and falsification

## Outcome

Horizon 1 ends with one finite, one-step reference-agent certificate whose
learning law, Bayes update, posterior-dependent decision, emitted action,
sampled transition, stationary blanket factorization, and KL quantities are
connected by explicit typed bridges. It also ends with compiled countermodels
showing which stronger blanket-to-inference, causal, KL, EFE, planning, and
thermodynamic readings fail. The policy result is an attained finite decision
rule, not transition-aware planning or EFE-optimal control.

The horizon does **not** end when more topic rows compile. Its terminal theorem
must be a derivation through shared carriers, not a conjunction of unrelated
endpoint facts.

## Implementation contract matrix

Names marked “new” are prospective and must be introduced by the active spec,
not by this design document. Each row is a complete scheduling contract; a
failed solid-lane spike blocks H1.8 until the terminal claim and dependency DAG
are explicitly revised.

| ID | Canonical resource, manifest role, namespace, and imports | Smallest spike and observable go condition | No-go effect | Test, evidence, review, and nearest out-of-scope claim |
| --- | --- | --- | --- | --- |
| H1.0 | `src/fep_lean/formal/manifest.py`; schema owner, not a Lean module | Add and validate `FormalModule.declaration_namespace`; compile every named Mathlib probe at the locked revision | Do not open mathematical slices; correct stale source claims or open a bounded architecture/upstream prerequisite | Extend `tests/test_formal_composition.py`; documentation plus native probe evidence; architecture and Lean review; no theorem or disposition promotion |
| H1.1 | new `formal/compositions/finite_scientific_implications.lean`; `COMPOSITION`; `FEPComposed.FiniteScientificImplications`; imports the exact owners `finite_probability`, `causal_dynamics`, `finite_markov_dynamics`, `active_inference`, and `information_geometry` | One rational countermodel proves every translated premise and the negated conclusion; a separate Bernoulli/Fisher witness proves strict local directional descent from explicit posterior, rank, and flow-alignment premises; domain reviewer approves both translations | Remove the disputed implication edge and retain it as literature analysis; H1.6/H1.8 may use only reviewed predicates | new `tests/test_horizon1_finite_reference.py`, `tests/test_formalism_relations.py`, and `tests/test_formalism_coverage.py`; native + declaration audit; domain and skeptical review; no universal blanket-to-inference claim |
| H1.2 | new `formal/decision_risk.lean`; `FOUNDATION`; `FEP.DecisionRisk`; imports `native_blanket`, `finite_information`, KL data processing, `Decision.BayesEstimator`, and `Decision.Risk.Basic` | Boolean weighted-Dirac supported/singular KL cases, a two-experiment Bayes-risk garbling example, and a proper-log-score orientation guard compile | Block H1.3, H1.4, and H1.8 if the native KL or Bayes-risk translation fails; if only the optional information-pushforward seam fails, retain the decision-risk core and keep the finite/native epistemic bridge closed | new `tests/test_horizon1_finite_reference.py` plus `tests/test_native_blanket_formalisms.py`; native + declaration audit; probability/decision review; no unconditional equality between real finite KL and native `klDiv`, and no identification of `finiteKL P Q` with `finiteKL Q P` |
| H1.3 | new `formal/finite_posterior_learning.lean`; `FOUNDATION`; `FEP.FinitePosteriorLearning`; imports `learning_theory`, `statistical_convergence`, `native_blanket`, H1.2, and Mathlib's infinite-product independence API | A two-hypothesis repeated-sample model constructs its i.i.d. Boolean trajectory law, derives a bounded log-likelihood-ratio concentration bound, converts it to posterior bad-mass decay, separately proves almost-sure eventual convergence, and retains zero-prior/non-identifiable boundaries | Remove the learning clause and block H1.8; broad calibration, empirical Bayes, and continuous conjugacy move to optional specs | new `tests/test_horizon1_finite_reference.py`, `tests/test_collective_learning_formalisms.py`, and `tests/test_risk_policy_tree_formalisms.py`; native + numerical witness; statistical review; no generic nonparametric rate or empirical calibration claim |
| H1.4 | new `formal/compositions/finite_policy_action.lean`; `COMPOSITION`; `FEPComposed.FinitePolicyAction`; imports `policy_tree`, `active_inference`, `controlled_markov`, H1.2, and H1.3 | Prove the support-qualified recognition-to-posterior KL VFE gap, then use the exact learned posterior in a finite observation-contingent policy law whose emitted action is optimal and transition-consistent | Retain the finite/native mutual-information carrier mismatch as an explicit no-go; remove EFE/reward equivalence clauses that fail and block H1.8 if the selected action is not tied to the model transition | new `tests/test_horizon1_finite_reference.py` plus `tests/test_horizon1_policy_action.py`; native + numerical witness; control/active-inference review; no total-EFE data-processing, tree-learning, reward--EFE, or infinite-horizon claim |
| H1.5 | existing `formal/variational_duality.lean`; `FOUNDATION`; `FEP.VariationalDuality`; no new terminal import unless selected | A `Fin 3` relative-interior moment problem has a checkable feasible multiplier and one boundary-support case | Keep only certificate/KKT results or stop this dashed optional lane; H1.4 must normalize its selected law without it | new `tests/test_horizon1_variational_duality.py`; native evidence; convex-analysis review; no automatic strong duality or full-support Gibbs optimizer at the boundary |
| H1.6 | intrinsic laws remain in `formal/native_blanket.lean` and `formal/causal_dynamics.lean`; every cross-domain theorem reuses H1.1's single composition leaf | Shared-conditional and coupled Boolean mixtures plus observationally equivalent/intervention-distinct models compile | Remove the failed blanket-preservation or identification clause and block the corresponding H1.8 clause; never create a second leaf | `tests/test_native_blanket_formalisms.py`, `tests/test_causal_predictive_formalisms.py`, and new `tests/test_horizon1_finite_reference.py`; native + declaration audit; causal/domain review; no causal identification from observational independence |
| H1.7 | existing `formal/continuous_time_markov.lean`; `FOUNDATION`; `FEP.ContinuousTimeMarkov`; depends on H1.2 and adds direct imports of the actual `active_inference` action-interface owner and `decision_risk` | A certified action-indexed semigroup samples to `ActionInterface`'s `FiniteKernel`; the two-state case, three-state nonreversible case, and strict positive refresh semigroup on a nondegenerate four-factor product carrier compile | Retain the certificate interface and exact witnesses; remove generic generator construction or strictness, and block the matching H1.8 clause | `tests/test_geometry_continuous_time_formalisms.py` plus new `tests/test_horizon1_finite_reference.py`; native + axiom audit; Markov-process review; no unproved matrix-exponential positivity or physical thermodynamics |
| H1.8 | new `formal/compositions/finite_reference_agent.lean`; `COMPOSITION`; `FEPComposed.FiniteReferenceAgent`; imports `finite_posterior_learning`, `compositions/finite_policy_action`, `compositions/finite_scientific_implications`, `native_blanket`, and `continuous_time_markov` | One shared lifted posterior proves repeated-sample learning, exact-posterior VFE, posterior-dependent optimal feedback, `selectedActionTransition_eq_sampledSemigroup`, blanket-law factorization, selected-kernel invariance, and same-law strict finite/native KL decrease | Preserve the first uninhabited-carrier record and predecessor conjunction; if the repaired shared-carrier theorem fails, publish only those boundaries and keep H2 closed | new `tests/test_horizon1_finite_reference_agent.py`, `tests/test_horizon1_finite_reference.py`, `tests/test_formal_composition.py`, and `tests/test_formal_foundations.py`; formal + numerical evidence; Lean, domain, and skeptical review; no rowwise/causal/physical-dissipation or universal FEP claim |

All new manifested resources must be added to the exact role roster asserted by
`tests/test_formal_composition.py`. Each new focused test named above is
prospective; the active spec must create it before implementation and must also
name the unchanged existing regression suites it composes. The manifest-driven
projection must project every new resource into the Lean workspace exactly
once. The generated `composed.lean` aggregate directly imports each
`COMPOSITION` leaf exactly once; foundations enter its transitive closure only
through the leaves' explicit imports. No hand-maintained second aggregate
roster is allowed.

### Exact H1 formal-resource ledger

The active spec may narrow an import only after its probe proves it unnecessary;
adding an unlisted direct import requires architecture review. Mathlib module
names below are part of the H1.0 compile matrix.

| Package | Manifest tuple and declaration namespace | Exact direct imports after the slice |
| --- | --- | --- |
| H1.1 | `resource="compositions/finite_scientific_implications.lean"`; `lean_module="FepSketches.compositions.finite_scientific_implications"`; `COMPOSITION`; `FEPComposed.FiniteScientificImplications` | `FepSketches.finite_probability`, `FepSketches.causal_dynamics`, `FepSketches.finite_markov_dynamics`, `FepSketches.active_inference`, `FepSketches.information_geometry` |
| H1.2 | `resource="decision_risk.lean"`; `lean_module="FepSketches.decision_risk"`; `FOUNDATION`; `FEP.DecisionRisk` | `FepSketches.native_blanket`, `FepSketches.finite_information`, `Mathlib.InformationTheory.KullbackLeibler.DataProcessing`, `Mathlib.Probability.Decision.BayesEstimator`, `Mathlib.Probability.Decision.Risk.Basic` |
| H1.3 | `resource="finite_posterior_learning.lean"`; `lean_module="FepSketches.finite_posterior_learning"`; `FOUNDATION`; `FEP.FinitePosteriorLearning` | `FepSketches.learning_theory`, `FepSketches.statistical_convergence`, `FepSketches.native_blanket`, `FepSketches.decision_risk`, `Mathlib.Probability.Independence.InfinitePi` |
| H1.4 | `resource="compositions/finite_policy_action.lean"`; `lean_module="FepSketches.compositions.finite_policy_action"`; `COMPOSITION`; `FEPComposed.FinitePolicyAction` | `FepSketches.policy_tree`, `FepSketches.active_inference`, `FepSketches.controlled_markov`, `FepSketches.decision_risk`, `FepSketches.finite_posterior_learning` |
| H1.5 | existing `resource="variational_duality.lean"`; `lean_module="FepSketches.variational_duality"`; `FOUNDATION`; `FEP.VariationalDuality` | existing `FepSketches.finite_information`, `Mathlib.Analysis.Convex.SpecificFunctions.Basic`; no import expansion planned |
| H1.6 blanket | existing `resource="native_blanket.lean"`; `lean_module="FepSketches.native_blanket"`; `FOUNDATION`; `FEP.NativeBlanket` | existing `FepSketches.markov_blanket`, `Mathlib.MeasureTheory.Integral.Bochner.SumMeasure`, `Mathlib.Probability.Independence.Conditional`; no import expansion planned |
| H1.6 causal | existing `resource="causal_dynamics.lean"`; `lean_module="FepSketches.causal_dynamics"`; `FOUNDATION`; `FEP.CausalDynamics` | existing `FepSketches.markov_blanket`; cross-domain results import this module from H1.1, never the reverse |
| H1.7 | existing `resource="continuous_time_markov.lean"`; `lean_module="FepSketches.continuous_time_markov"`; `FOUNDATION`; `FEP.ContinuousTimeMarkov` | `FepSketches.finite_markov_dynamics`, `FepSketches.active_inference`, `FepSketches.decision_risk`, `FepSketches.markov_blanket`, `Mathlib.Analysis.Normed.Algebra.MatrixExponential` |
| H1.8 | `resource="compositions/finite_reference_agent.lean"`; `lean_module="FepSketches.compositions.finite_reference_agent"`; `COMPOSITION`; `FEPComposed.FiniteReferenceAgent` | `FepSketches.finite_posterior_learning`, `FepSketches.compositions.finite_policy_action`, `FepSketches.compositions.finite_scientific_implications`, `FepSketches.native_blanket`, `FepSketches.continuous_time_markov` |

Every tuple is asserted in `tests/test_formal_composition.py`, projected to the
matching `lean/FepSketches/...` path, and included in declaration/axiom evidence
according to its role. Only `COMPOSITION` tuples are direct generated-aggregate
imports; the listed foundation imports determine their transitive closure.

## H1.0 — pin-surface and ownership audit

**Depends on:** released v1.1.0 only.

**Single owners:** pin facts remain in [`docs/lean4.md`](../../guides/lean4.md) and the
Lean lockfiles; module membership remains in
[`formal/manifest.py`](../../../src/fep_lean/formal/manifest.py).

### Stop/go spikes

Compile minimal examples for these exact pinned declarations before using them:

- `InformationTheory.klDiv_comp_right_le` from Mathlib's KL
  data-processing module;
- `ProbabilityTheory.bayesRisk_le_bayesRisk_comp`,
  `IsArgminEstimator`, and `IsBayesEstimator`;
- `ProbabilityTheory.betaMeasure` and the Bernoulli/Binomial distribution APIs;
- matrix exponential identity, addition under commutation, and derivative APIs;
- native posterior, conditional distribution, and `CondIndepFun` APIs;
- Riemannian-bundle and covariant-derivative APIs needed by H2; and
- Brownian finite-dimensional laws and trajectory-kernel construction.

The current pin contains `klDiv_comp_right_le`; current prose that says the pin
does not expose a generic KL data-processing theorem is stale. Correct the
canonical maturity/prose owners and regenerate their projections before using
that absence as motivation. Keep the finite fep-063 disposition unchanged
unless its own reviewed theorem becomes stronger; upstream availability alone
does not promote a project theorem.

Search the pinned source for Itô integration, stochastic integrals, SDE
solutions, and Fokker--Planck APIs. If an API is absent, record the source-search
and failed compile probe in the active spec. Absence from memory is not
evidence.

### Composition ownership gate

H1.0 added the required `declaration_namespace` field to `FormalModule`,
validates it against comment-stripped source, rejects duplicate new owners, and
covers it in `tests/test_formal_composition.py`. New leaves use leaf-specific
namespaces such as
`FEPComposed.FiniteReferenceAgent`. Existing released flat `FEPComposed.*`
names retain their exact manifest values and public names. A bulk rename is a
separate migration with a complete consumer inventory; aliases that recreate
two owners are rejected.

The active H1 spec must also measure whether a terminal leaf can import
family-level topic projections rather than the whole generated `fep_all`
module. If family projection is cheap and byte-stable, make endpoint imports a
hard coverage rule. If it is not, retain the current proof-reference rule and
record the dependency-opacity debt; do not block H1 mathematics on a broad
generator rewrite.

### Acceptance

- All positive API probes compile at the exact pin with zero warnings.
- Every claimed absence has a bounded source search and negative probe.
- The KL data-processing prose/maturity inconsistency is closed.
- Every planned new module has one manifest owner and one namespace owner.
- No topic, disposition, or scientific claim changes in this package.

## H1.1 — implication contracts and countermodels

**Depends on:** H1.0.

**Single owners:** invariance is used directly as
`FEP.FiniteMarkovDynamics.IsInvariant`; row factorization is the exact
`FiniteKernel.row` marginal-product equality; absent coupling is exact equality
to `FEP.CausalDynamics.pairedKernel`; and stationary conditional independence
is the existing `FEP.CausalDynamics.Factorizes` predicate on an explicit
`ConditionalBlanketModel`. The Boolean countermodels use `Unit` as a genuine
one-value blanket and prove both its mass and conditional-row identity, so bare
unconditional product equality is not relabeled as a blanket statement.
Observational and causal equivalence are exact equalities of
`FEP.CausalDynamics.mediatorMarginal` over `orderedJoint` and
`interventionalJoint`. Predicates 4--5 reuse
`FEP.ActiveInference.posteriorState` and
`variationalFreeEnergy_eq_surprisal_iff`; the local-descent result reuses native
`finiteKL`, `FEP.InformationGeometry.IsNaturalGradient`, `fisherMetric_pos`,
and `fisherMetric_eq_dot_lowerTangent`. The new leaf owns only the genuinely
cross-carrier predicates `RecognitionMatchesPosterior` and
`LocalFreeEnergyDescent`, plus the implications and countermodels. The earlier
`HasRecognitionMap` proposal was removed because finite-law normalization made
its witness vacuous. The leaf must
not introduce wrapper aliases for intrinsic foundation vocabulary or a
parallel scientific-claims YAML graph.

### Target implications

Translate primary-source statements into separate predicates for:

1. stationary-law conditional independence;
2. rowwise transition factorization;
3. sparse or absent dynamical coupling;
4. existence of a synchronization/recognition map;
5. equality of recognition and conditional laws;
6. free-energy or KL dissipation;
7. Fisher-natural-gradient alignment of internal flow; and
8. causal identification under interventions.

At least these target declarations must be proved:

- `rowwiseBlanket_doesNotImply_stationaryBlanket`;
- `sparseCoupling_doesNotImply_condIndep`;
- `stationaryBlanket_doesNotImply_freeEnergyDescent`;
- `blanketPosterior_and_flowAlignment_imply_localDescent`; and
- `observationalBlanket_doesNotIdentify_causalBlanket`.

Names are prospective but their premise/conclusion separation is fixed. The
positive theorem must derive descent from independently inspectable blanket,
recognition, differentiability, rank, and flow-alignment premises; it may not
store the desired derivative sign as a structure field. Concretely, its
flow-alignment premise is `IsNaturalGradient model covector tangent`; full
support, `Identifiable model`, and `tangent ≠ 0` make the Fisher self-pairing
strictly positive; and a separately proved derivative/covector identity turns
the negative aligned flow into a strictly negative **local directional
derivative**. This is not a discrete update, global convergence, or physical
dissipation theorem. The interior Bernoulli score model is the required
nonvacuity witness; no predictive-coding scalar is silently substituted for
the reference-agent carrier.

### Stop/go spike

Formalize the smallest rational Boolean or finite linear model that satisfies
all premises of one rejected implication and proves the conclusion false. A
domain reviewer must approve the translation against the critique literature
before generalization begins. Separately compile the interior Bernoulli
positive-descent witness so the recovery theorem is not vacuous.

### Acceptance

- Every countermodel proves its premises, non-degeneracy, and failed
  conclusion.
- Competing blanket meanings are distinct predicates.
- A positive recovery theorem exposes every additional hypothesis.
- No theorem says that a blanket or stationary law alone performs inference.

**No-go action:** if reviewers cannot agree on an exact source proposition,
retain the dispute as literature analysis. Do not formalize a convenient
caricature.

## H1.2 — native information and Bayesian decision bridge

**Depends on:** H1.0; opens H1.3, H1.4, and H1.6 and is consumed transitively
by H1.8.

**Single owner:** new foundation `formal/decision_risk.lean`, namespace
`FEP.DecisionRisk`, owns the weighted-Dirac/native-KL transfer, proper-log-score
excess risk, the generic information-garbling bridge, and the translation into
Mathlib's `avgRisk`, `bayesRisk`, `minimaxRisk`, and estimator vocabulary. It
imports existing finite-information and native-blanket
declarations; none of those foundations imports it back. Active-inference VFE
and epistemic-value corollaries are not owned here; they compose this foundation
with `active_inference` in H1.4.

### Target declarations

- `weightedDirac_klDiv_eq_finiteKL_of_fullSupport`;
- `weightedDirac_klDiv_eq_top_of_not_absolutelyContinuous`;
- `properLogScore_excessRisk_eq_finiteKL_truth_report`;
- `finiteKL_asymmetric_bool` on named asymmetric full-support Boolean laws;
- `bayesRisk_mono_under_observationGarbling`;
- `mutualInformation_mono_under_observationGarbling`, conditional on the
  product/pushforward stop/go seam; and
- one finite `IsArgminEstimator` whose kernel is a genuine Bayes estimator.

The first equality must state the support or absolute-continuity assumptions
that make it true. The singular theorem must preserve native infinity rather
than totalizing it to the project's real finite KL value. For posterior or
truth law `P` and reported or recognition law `Q`, proper logarithmic-score
excess risk is `finiteKL P Q`. The VFE gap used by the active-inference model
has the opposite argument order, `finiteKL Q P`. These are not interchangeable:
the Boolean `finiteKL_asymmetric_bool` witness must make their inequality
executable rather than relying only on a prose warning.

### Stop/go spikes

1. Prove the weighted-Dirac equality for two full-support Boolean laws and the
   singular boundary for disjoint point masses.
2. Instantiate Mathlib Bayes risk on a two-hypothesis, two-observation model
   with a revealing experiment, an input-independent Boolean garbling, and
   zero-one loss; prove the informative and garbled risks differ.
3. Prove the proper-log-score excess-risk identity at its exact support boundary
   and compile the asymmetric Boolean `finiteKL_asymmetric_bool` guard.
4. Construct the product/pushforward kernels needed to apply native KL data
   processing to mutual information.

Failure of steps 1--3 is a no-go for the H1.2 base bridge and blocks its solid
dependents. If step 4 is not tractable, ship the weighted-Dirac, proper-score,
and Bayes-risk results, but leave both the generic mutual-information theorem
and H1.4's epistemic-value corollary blocked. Do not restate native DPI as an
assumed finite inequality.

### Acceptance

- Both supported and singular KL cases compile.
- Bayes-risk orientation is tested on an informative channel and its garbling.
- Proper log-score excess risk has argument order `finiteKL P Q`, and an
  asymmetric full-support Boolean witness proves it cannot be replaced by
  `finiteKL Q P`.
- Codomains (`Real` versus `ENNReal`) remain visible in theorem signatures.
- The bridge reuses Mathlib definitions rather than project-local homonyms.
- No VFE-gap or epistemic-value declaration is introduced in H1.2.

## H1.3 — selected-model posterior learning

**Depends on:** H1.2 and the current learning, native finite-measure, and
strong-law foundations.

**Single owner:** new foundation `formal/finite_posterior_learning.lean` owns the
selected sampling-model theorems and imports the exact generic learning,
native finite-measure, and strong-law endpoints they consume. Existing
foundations retain their generic declarations; this package does not duplicate
them or fabricate an empirical-risk dependency for a result that does not use
calibration or Brier-risk transfer.

### Mainline target

Use the exact finite hypothesis carrier later consumed by H1.8 and a concrete
Boolean trajectory law built with `Measure.infinitePi`. Discharge coordinate
independence with `iIndepFun_infinitePi` and marginal-law identities with
`infinitePi_map_eval`; do not leave the selected-model witness as an abstract
independence assumption. On that carrier prove:

- a bounded centered log-likelihood-ratio observable for the selected Boolean
  observation law, its `HasSubgaussianMGF` certificate via the pinned
  Hoeffding lemma, and an explicit finite-sample bad-gap probability bound;
- exponential posterior-mass contraction on the complement of that bad-gap
  event;
- a repeated-sample posterior update on that same carrier;
- a separate almost-sure eventual contraction result obtained from the
  maintained finite-alphabet strong law; and
- a zero-prior and an observationally equivalent boundary theorem.

The almost-sure theorem is not a numerical finite-sample probability bound and
cannot substitute for it. Conversely, the finite-sample concentration theorem
does not by itself assert almost-sure convergence. Both consume the same named
truth law, hypothesis likelihoods, and posterior update.

General calibration, Brier-risk transfer, misspecification rates, and finite
empirical-Bayes optimization are optional capability tracks. They may reuse the
selected model after the terminal learning clause is green, but they do not
block H1.8 and must not inflate the critical path.

### Optional continuous conjugacy branch

Spike Beta/Binomial density algebra using Mathlib's normalized `betaMeasure`.
Go only if posterior closure can be expressed as an equality of genuine
measures or densities with all normalization and endpoint conditions visible.
Otherwise the finite model remains the H1 result; do not introduce an
unnormalized “posterior” definition to force conjugacy.

### Stop/go spike

Before the concentration proof, compile the exact Boolean infinite-product
measure, coordinate measurability, `iIndepFun_infinitePi`, and its one-coordinate
marginal identity at the locked pin. Failure blocks the selected-model theorem
and must not be papered over by adding independence as an uninhabited premise.
Once green, derive the bounded centered log-likelihood ratio with
`hasSubgaussianMGF_of_mem_Icc` and feed the maintained
`subGaussian_empiricalMean_tail`; the almost-sure branch separately consumes
the maintained finite-alphabet strong law.

### Acceptance

- The data-generating law, truth, prior support, and identifiability assumption
  are explicit.
- The selected i.i.d. trajectory law and its independence/marginal facts are
  constructed, not merely postulated.
- A derived Hoeffding/sub-Gaussian probability bound replaces the current
  supplied-tail premise on the selected model, and the almost-sure strong-law
  result remains a separately named theorem.
- The exported theorem returns the final posterior in the maintained belief
  carrier and proves a nonconstant repeated update; H1.8, not H1.3's exit gate,
  owns the downstream-consumption check.
- Calibration, contraction, consistency, and marginal-likelihood optimization
  remain distinct claims when optional tracks are opened.
- A zero-prior or observationally equivalent boundary remains executable.

## H1.4 — EFE semantics, policy learning, and emitted action

**Depends on:** H1.2, H1.3, and the current controlled-Markov and policy-tree
foundations. H1.5 is an optional strengthening, not a merge prerequisite.

**Single owner:** new composition leaf
`formal/compositions/finite_policy_action.lean`, namespace
`FEPComposed.FinitePolicyAction`, owns this package. Intrinsic `PolicyTree`
lemmas stay in `policy_tree.lean`; the leaf adds only laws that genuinely join
policy, EFE, belief, action, and controlled-transition endpoints.

### Target declarations

- `vfeGap_eq_finiteKL_recognition_posterior`, with the recognition law first and
  the posterior law second under explicit support assumptions;
- an explicit no-go boundary for an active-inference epistemic-value
  garbling corollary: the maintained real finite mutual information and H1.2's
  native `ENNReal` channel mutual information have no proved bridge;
- normalization of a prior-weighted Gibbs law over finite policy trees;
- a finite reachable-belief index that reuses H1.3's learned posterior and its
  one-step updates without claiming a law over all posterior histories;
- an exact relation between recursive EFE and Bellman reward under named
  preference, information, and support conditions;
- a counterexample outside those conditions;
- root-action optimality after an observation-dependent belief update; and
- coherence between the selected tree action, `ActionInterface`, and the
  transition used by the generative model.

### Stop/go spike

First compose `active_inference` with H1.2 to prove the support-qualified
recognition-to-posterior KL VFE-gap identity. H1.2's native pushforward theorem
does not by itself bridge to `ActiveInference.epistemicValue`; record that
corollary as blocked without restating data processing. Then reuse H1.3's exact
learned posterior through a finite reachable-belief index, normalize the
same-depth tree law, and prove that the observation changes the continuation
action. Tree learning, reward--EFE equivalence, and transition use inside the
generic value recursion remain explicit no-go seams rather than new carriers.

### Acceptance

- No second `PolicyTree`, belief, transition, or EFE carrier exists.
- The VFE-gap theorem preserves the recognition-to-posterior KL orientation and
  is not identified with H1.2's proper posterior log-score excess risk.
- No epistemic monotonicity theorem is exported until a reviewed finite/native
  mutual-information bridge exists; generic native data processing is not
  relabeled as an active-inference result.
- The emitted action consumes the generative model's exact transition through
  `ActionInterface`; the generic policy-tree value recursion has no transition
  field, so no transition-aware planning or action-for-future-kernel-consequence
  claim is made.
- Exact support and sign conventions appear in the statement.
- Finite horizon remains visible; no infinite-horizon optimality is inferred.

The selected finite law may be normalized directly by its positive finite
partition. It may cite H1.5 only when the active model genuinely needs a
constrained-entropy certificate.

## H1.5 — optional finite constrained maximum entropy

**Depends on:** H1.0. This is a dashed capability lane and is not required by
H1.8 or the Gaussian H2 mainline.

**Single owner:** extend `formal/variational_duality.lean`, namespace
`FEP.VariationalDuality`. A different foundation requires a later architecture
spec and is not an option inside H1.5.

### Target declarations

For a nonempty finite carrier, normalized law, and finite list of affine moment
constraints, prove one of these in descending order of strength:

1. existence and uniqueness of the entropy-maximizing law plus a Gibbs form;
2. existence plus uniqueness from a supplied feasible multiplier; or
3. a certificate theorem whose multiplier and feasibility premises are
   independently checkable.

The full-support Gibbs-form target additionally requires a visible
relative-interior/Slater feasibility premise. Boundary optimizers are treated
on their restricted support or through an explicit KKT/certificate theorem;
mere affine feasibility does not imply a finite-multiplier Gibbs form. The
target includes infeasible constraints, redundant constraints, zero
temperature, and boundary-support cases as separate results.

### Stop/go spike

Prove the two-moment `Fin 3` problem and one infeasible boundary. If general
compactness or dual attainment requires building substantial convex-analysis
infrastructure, retain the finite certificate theorem and route reusable
missing lemmas upstream. Do not label weak duality as strong duality.

## H1.6 — blanket mixture, invariance, and causal limits

**Depends on:** H1.1. H1.2 is consumed elsewhere in the terminal H1 merge but
none of H1.6's blanket-mixture, invariance, or causal-identification statements
uses its decision-risk API.

**Single owners:** `native_blanket.lean` owns native conditional-independence
transfer; `causal_dynamics.lean` owns finite intervention semantics; every
claim that needs both is added to H1.1's single
`finite_scientific_implications.lean` leaf. H1.6 must not create another
cross-domain composition owner.

### Target declarations

- a necessary-and-sufficient condition, or the strongest tractable sufficient
  condition, for a mixture of blanket-factorized rows to remain factorized;
- an explicit arbitrary-mixture counterexample;
- preservation of a stationary blanket law under a transition kernel with
  named component conditions;
- finite-DAG soundness for the maintained intervention semantics;
- observationally equivalent models with different causal effects; and
- an identification theorem only under explicit intervention, faithfulness, or
  structural assumptions.

### Stop/go spike

Use a Boolean blanket with two positive conditioning regimes. Construct one
shared-conditional mixture that preserves independence and one coupled mixture
that breaks it. Separately construct two observationally equivalent finite
models with different interventional descendants.

### Acceptance

- “Compatible with a blanket” and “identified causal blanket” are different
  types or predicates.
- Off-support conditioning regimes remain explicit.
- Rowwise transition factorization is not substituted for stationary-law
  conditional independence.

## H1.7 — action-indexed finite semigroups and nonreversible witness

**Depends on:** H1.0 and H1.2; supports H1.8 and H2.4. Backward-compatible
semigroup source work may be prepared beside H1.2, but H1.7 cannot close or
claim its native-KL contract before the `decision_risk` import is green.

**Single owner:** extend `continuous_time_markov.lean`. The current two-state
`TwoStateRates` remains the regression instance of the general interface.

### Carrier and targets

Define a finite rate generator with nonnegative off-diagonal entries and zero
row sums, plus an `ActionIndexedSemigroup` whose selected action samples to the
same `FiniteKernel` carrier used by `ActionInterface.actionTransition`. Target:

- a normalized nonnegative transition kernel for every nonnegative time;
- identity and additive semigroup laws;
- left and right master equations;
- stationary and detailed-balance predicates;
- native KL contraction toward an invariant law via kernel DPI; and
- a theorem exposing the sampled kernel for each action;
- a three-state nonreversible steady-state witness with nonzero current; and
- on the exact blanket carrier
  `FEP.MarkovBlanket.DynamicState Internal Sensory Active External`,
  definitionally `Internal × (Sensory × (Active × External))`, with every
  factor nontrivial, an explicit positive refresh semigroup and nonstationary
  law with **strict** KL decrease. No reassociated product is silently
  substituted. The all-`Bool` instance is the executable boundary witness.

### Constructor spike

Try the matrix-exponential route first. Row-sum preservation follows from the
generator annihilating the constant vector; entrywise positivity for a Metzler
generator is the high-risk obligation. If that proof is not clean at the pin,
use a uniformization series or retain a `FiniteMarkovSemigroup` certificate
interface and open the generic constructor as an upstream/blocker task.

The no-go fallback is still a useful theorem: every certified finite Markov
semigroup contracts native KL to an invariant law, and the existing two-state
model instantiates it. Do not package stochasticity as an unproved structure
field while claiming a generator construction.

If the generic strictness characterization fails, retain generic nonincrease
and prove strictness directly for the explicit product-carrier refresh
semigroup. The three-state nonreversible example remains a current witness, not
the terminal blanket carrier.

## H1.8 — finite reference-agent terminal theorem

**Depends on:** H1.3, H1.4, H1.6, and H1.7. H1.5 is consumed only if the selected
policy theorem explicitly chooses its optional constrained-entropy result.

**Single owner:** one manifested composition leaf
`compositions/finite_reference_agent.lean`, namespace
`FEPComposed.FiniteReferenceAgent`. It retains the first merge's uninhabited
coherence record and no-go theorems, then adds one positive theorem through
local names for existing carriers. It does not define a second generative
model, policy tree, blanket law, or CTMC.

### Terminal certificate

On one exact finite model, prove a connected theorem whose intermediate values
are shared:

1. a positive-evidence observation produces the normalized posterior;
2. repeated observations on the same carrier satisfy the H1.3 posterior
   learning bound, with the final posterior reused below;
3. that posterior uniquely attains the posterior-form VFE bound;
4. the same posterior belief initializes the observation-contingent policy tree;
5. the posterior-index feedback continuation attains the explicit asymmetric
   finite decision objective and strictly beats every fixed report;
6. the emitted action uses the same controlled transition as the generative
   model;
7. `selectedActionTransition_eq_sampledSemigroup` proves by construction that
   this controlled transition is the selected H1.7 sampled semigroup kernel;
8. H1.6 supplies factorization of that exact stationary law, while H1.7
   independently proves that the selected refresh kernel preserves it; no
   paired-dynamics or causal-blanket conclusion is imported;
9. native KL to the invariant law is nonincreasing; and
10. the named nondegenerate product-carrier witness makes the posterior update,
    feedback advantage, and both real/native KL inequalities strict on that
    same lifted posterior and selected refresh kernel.

The terminal theorem may expose an explicit flow-alignment or constitutive
hypothesis, but it may not describe that hypothesis as derived.

### Horizon 1 exit gate

- The terminal certificate compiles warning-free and uses every listed shared
  object in a genuine derivation.
- `External`, `Sensory`, `Active`, and `Internal` are each nontrivial in the
  terminal witness, and the stationary blanket law has at least two positive
  support points; no singleton factor can make the blanket clause vacuous.
- H1 countermodels compile in the same aggregate and remain theorem-referenced.
- Every new formal edge names a manifested composition theorem; pairings remain
  pairings.
- The declaration/axiom audit reports no `sorryAx` or unapproved project axiom.
- Maturity, novelty, relation, capability, coverage, atlas, dashboard, and
  manuscript projections are current if their owners changed.
- A human semantic review confirms that no proxy was promoted by compilation.

Horizon 2 remains closed until this gate passes.
