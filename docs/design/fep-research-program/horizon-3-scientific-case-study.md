# Horizon 3: end-to-end scientific case study

## Outcome

Horizon 3 turns the H2 mathematical kernel into one falsifiable scientific
study. The primary candidate is the exact H2.5 symmetric-precision
linear-Gaussian stationary process, relabeled through an explicit
external/sensory/active/internal axis equivalence, with an observation model and
a finite set of interventions or actions. H3.G0 performs read-only acceptance
of the already-landed H2 carrier and selects exactly one continuous or finite
branch. H3.0 then freezes the protocol for that branch before H3.1 starts. H3
must not become a collection of unrelated demonstrations or a hybrid of the two
branches.

The target is not “validate the FEP.” The target is a claim matrix stating,
for this named model and data:

- what is proved;
- what is a supplied scientific assumption;
- what is numerically reproduced;
- what is identified from observations or interventions;
- what passes held-out empirical tests; and
- what is rejected or remains unknown.

## Primary and fallback carriers

| Candidate | Role | Go condition | Boundary |
| --- | --- | --- | --- |
| Controlled linear-Gaussian/Ornstein--Uhlenbeck blanket model | Continuous branch | H2.5 has already landed the exact symmetric-precision `Fin 4` constructor, H2.7 exits, H3.G0 accepts its source-bound evidence read-only, and relevant data expose interface and intervention variables | Linear, Gaussian, symmetric-positive precision, dimensionless-state, and stationarity premises remain explicit |
| Finite partially observed reference agent from H1 | Finite branch and negative control | The H1 carrier repair and H1.8 exit are green, and H3.G0 selects this branch before H3.0 freezes | Synthetic/finite result only; no covariance, diffusion, or continuous-time claim |
| Biochemical reaction or cellular network | Future alternative, not H3 mainline | Separate domain, data, and stochastic-process spec | Must not be approximated as OU without a reviewed error model |

H3.G0 records exactly one branch. A continuous model may not borrow a finite
blanket theorem through an unnamed coercion, and a finite model may not borrow
Gaussian covariance, diffusion, or raw-unit conclusions. Changing branches
invalidates H3.0 and requires a new preregistration before outcome inspection.

The fallback is a valid publishable negative result. It is not permission to
rename a synthetic finite study as empirical validation.

## Implementation contract matrix

H3 has one formal model owner, one cross-domain composition owner, one
executable owner, and one frozen protocol. Reusing a file across adjacent rows
does not create shared ownership: the declaration classes below are disjoint.

| ID | Canonical resource and ownership boundary | Smallest spike and observable go condition | No-go effect | Test, evidence, review, and nearest out-of-scope claim |
| --- | --- | --- | --- | --- |
| H3.G0 | prospective read-only carrier-acceptance and branch-decision record in the active H3 spec; no Lean resource, import, or H2 source mutation | Verify the accepted H2.5 declaration/axiom receipt, exact `K`/`Sigma` witness, scalar specialization, H2.7 exit, and conditioning/precision seam by source digest; also verify H1.8 if the finite branch is eligible, then record exactly one branch before H3.0 | Keep H3.0--H3.7 closed; repair the owning H1/H2 horizon or select the other already-green branch without changing either carrier | new `tests/test_h3_preregistration.py` validates the acceptance record and source hashes; read-only formal/provenance evidence; probability/dynamics review; no new Gaussian theorem, branch hybrid, or blanket conclusion from stability |
| H3.0 | prospective `specs/h3-reference-study/preregistration.yaml`; immutable protocol owner after freeze | Before outcome inspection, validate one candidate dataset's license, column/unit map, time resolution, intervention field, missingness, and immutable split hash | Remove the dashed H3.0--H3.6E real-data edge; continue through H3.6S and H3.7 with an empirical-unavailable claim row | new `tests/test_h3_preregistration.py`; data-governance evidence; data owner + statistician approval; no causal or empirical claim from unavailable variables |
| H3.1 | new `formal/h3_reference_model.lean`; `FOUNDATION`; `FEP.H3ReferenceModel`; directly imports exactly `fin4_gaussian_semigroup` and `markov_semigroup`, with the latter retained only for declarations named in public signatures; `gaussian_information_geometry`, `posterior_convergence`, `controlled_markov`, and the finite `markov_blanket` owner are excluded | After the hard H3.0 dependency passes, define `Axis`, its exact `Axis ≃ Fin 4` order, the standardized dimensionless state, positive affine raw-unit bridge, observation/intervention primitives, and data-column map without storing covariance, invariance, recognition, or identifiability conclusions | Keep H3.2--H3.7 closed or replace the selected branch through a new H3.G0/H3.0 cycle; do not invent unit coercions, a second action carrier, or certificate fields that assume downstream theorems | new `tests/test_h3_reference_model.py`; native + semantic validation; domain and Lean review; no biological identity, measured-energy interpretation, posterior theorem, finite blanket carrier, or generic control carrier |
| H3.2 | intrinsic derived transition/precision/covariance/invariance declarations in `h3_reference_model.lean`; the explicit H1 tuple permutation plus blanket, recognition, identifiability, preservation, intervention, and countermodel bridges in `compositions/h3_case_study.lean`; generic laws remain with H1/H2 owners | On the continuous branch, pull back H2.5's exact `K`/`Sigma` through `Axis ≃ Fin 4`, derive covariance and invariance, prove the precision-zero blanket equivalence, derive the Gaussian conditional-mean recognition map and its rank-based identifiability, and normalize one intervention; on the finite branch, first prove the named right-associated H1 tuple permutation and then prove only claims supplied by the repaired H1 terminal carrier | Remove blanket, recognition, identifiability, or causal clauses individually from the case-study DAG; retain the selected model as a negative/control process if its intrinsic dynamics remain valid | `tests/test_h3_reference_model.py`, `tests/test_h3_case_study.py`, `tests/test_native_blanket_formalisms.py`, and `tests/test_causal_predictive_formalisms.py`; native + numerical witness; dynamical-systems and causal review; no blanket from good prediction, covariance sparsity, or stored certificates |
| H3.3 | cross-domain declarations in new `formal/compositions/h3_case_study.lean`; `COMPOSITION`; `FEPComposed.H3CaseStudy`; imports H3 foundation and stable H2 posterior/filter endpoints | One exact synthetic observation reproduces the native Gaussian update and VFE optimum; a non-identifiable/noise-misspecified pair remains executable | Remove posterior-consistency/calibration clauses; block H3.4 and real-data inference until recovery is redesigned | new `tests/test_h3_case_study.py`; native + synthetic evidence; inference/statistics review; no observed-data calibration inferred from a theorem |
| H3.4 | action/control declaration block in `h3_case_study.lean`; generic control remains in H1/H2 owners | A two-step observation-contingent controller and matched open-loop baseline use the exact H3.3 belief and H3.2 transition | Remove action/EFE advantage and controlled-dissipation edges; permit an observational filtering case study only after claim-matrix revision | `tests/test_h3_case_study.py`, `tests/test_risk_policy_tree_formalisms.py`, and `tests/test_control_temporal_formalisms.py`; native + synthetic evidence; control review; no infinite-horizon, reinforcement-learning, or spontaneous-agency claim |
| H3.5 | information/constitutive declaration block in `h3_case_study.lean`; generic path laws remain in path-thermodynamics owners | One finite grid proves path-law KL and Lyapunov change; a second witness shows the same path KL does not determine heat without measured constitutive premises | Delete the physical-thermodynamic terminal clause and its H3.6S/E claim-matrix columns while retaining the information-asymmetry edge | `tests/test_h3_case_study.py` and `tests/test_thermo_geometry_formalisms.py`; native + numerical evidence; physics/domain review; no heat, work, or entropy-flow identification from KL alone |
| H3.6S | new `src/fep_lean/verification/h3_reference_study.py`; single executable consumer of exported typed parameters, never a model registry | One exact fixture round-trips and two identifiable synthetic settings recover model/parameters inside preregistered tolerances | Remove the dashed H3.6S--H3.6E unlock; keep real data sealed and publish recovery failure/null evidence rather than retuning thresholds | new `tests/test_h3_reference_study.py`; synthetic receipt; statistical + domain review; no empirical, calibration-on-observed-data, or post-hoc threshold claim |
| H3.6E | the same executable under the frozen H3.0 analysis plan; no new code/model owner | Only after H3.6S passes, run the immutable held-out split once with frozen baselines, exclusions, metrics, and multiplicity control | Retain null/negative output and mark the dashed H3.6E--H3.7 empirical branch unavailable or null; never alter the primary analysis | `tests/test_h3_reference_study.py` and `tests/test_release_bundle.py`; empirical evidence; statistician + data-owner review; no causal claim without H3.0 identification |
| H3.7 | prospective `specs/h3-reference-study/acceptance/` claim matrix, signatures, and clean-room reproduction record | A reviewer with no author context rebuilds one symbolic fixture and one preregistered synthetic run from the release bundle with matching hashes | No supportive publication or empirical promotion; return exact mismatch to its owning DAG row and retain the failed replication record | `tests/test_release_bundle.py`, `tests/test_native_evidence.py`, `tests/test_formalism_audit.py`, `tests/test_manuscript_artifacts.py`, `tests/test_browser_capture.py`, and `tests/test_browser_capture_protocol.py`; formal + synthetic + optional empirical + publication evidence; independent Lean/domain/statistical quorum; no universal FEP conclusion |

`h3_reference_model.lean` and `h3_case_study.lean` must be added to the exact
manifest and namespace roster introduced in H1.0. No topic row or separate
scientific-model YAML registry is created by these packages. Both resources
are projected into the Lean workspace exactly once. The generated
`composed.lean` aggregate directly imports only `h3_case_study`; the H3
foundation enters its transitive closure through that leaf's explicit import.
The executable remains outside the Lean aggregate.

### Exact H3 formal-resource ledger

| Package | Manifest tuple and declaration namespace | Exact direct imports after the slice |
| --- | --- | --- |
| H3.1--H3.2 intrinsic | `resource="h3_reference_model.lean"`; `lean_module="FepSketches.h3_reference_model"`; `FOUNDATION`; `FEP.H3ReferenceModel` | `FepSketches.fin4_gaussian_semigroup`, `FepSketches.markov_semigroup` |
| H3.2 bridges--H3.5 | `resource="compositions/h3_case_study.lean"`; `lean_module="FepSketches.compositions.h3_case_study"`; `COMPOSITION`; `FEPComposed.H3CaseStudy` | `FepSketches.h3_reference_model`, `FepSketches.markov_blanket`, `FepSketches.native_blanket`, `FepSketches.causal_dynamics`, `FepSketches.compositions.finite_scientific_implications`, `FepSketches.compositions.smooth_reference_kernel`, `FepSketches.compositions.gaussian_filter`, `FepSketches.compositions.gaussian_control`, `FepSketches.compositions.gaussian_grid_path`, `FepSketches.compositions.finite_policy_action`, `FepSketches.path_thermodynamics` |

Both tuples are asserted by the manifest roster/namespace tests, projected to
their exact workspace paths, and included in the declaration/axiom audit. The
composition tuple is the direct `composed.lean` import; its foundation import
supplies the transitive closure. H3.6S/E consume exported parameters but never
enter `FORMAL_MODULES`.

H3.G0 has no manifest tuple: it is an acceptance record over immutable H1/H2
evidence. H3.0 remains a hard scheduling dependency of H3.1 even though a
preregistration artifact is not a Lean import. Neither
`FepSketches.gaussian_information_geometry`,
`FepSketches.posterior_convergence`, `FepSketches.controlled_markov`, nor the
finite `FepSketches.markov_blanket` owner belongs in the H3 foundation.
Posterior/filter/control endpoints and the H1 tuple bridge enter only through
the H3 composition leaf's explicit owners.

## H3.G0 — read-only carrier acceptance and branch gate

**Depends on:** H2 exit.

**Single owner:** a source-bound acceptance record in the active H3 spec. It is
not a formal resource. H3.G0 reads H1/H2 declarations, receipts, source digests,
and pre-outcome data-capability metadata; it changes none of them.

For continuous eligibility, the record must resolve and source-bind H2.5's
scalar constructor, exact symmetric-positive `Fin 4` precision
`K`, derived `Sigma = K⁻¹`, transition semigroup, invariant Gaussian, weak
convergence, scalar-specialization theorem, and conditioning/precision seam,
plus the H2.7 exit acceptance. The exact displayed H2.5 matrices are the
carrier; an arbitrary Hurwitz matrix or a newly fitted covariance is not a
substitute.

For finite eligibility, the record must resolve a repaired and accepted H1.8
terminal carrier. The retained first-merge no-go is not eligibility by itself;
the accepted `finiteReferenceAgent_terminal` and its source-bound exit evidence
are the eligible H1 surface. H3.G0 must verify both so the repair cannot erase
the exact boundary it supersedes.

The gate then records exactly one branch:

- **continuous:** consume the accepted H2.5 `Fin 4` carrier; or
- **finite:** consume the repaired H1.8 carrier and mechanically exclude every
  covariance, diffusion, and continuous-time claim.

The selection may use licenses, variable/unit availability, sampling, and
intervention metadata, but not protected outcomes. A branch switch invalidates
the acceptance record and every H3.0 artifact derived from it. If neither
branch is eligible, H3.0--H3.7 remain closed. H3.G0 may not add imports, prove a
missing Gaussian theorem, repair H1, or rebuild either carrier in an H3
namespace.

## H3.0 — preregistration and model/data decision

**Depends on:** H3.G0 unconditionally. Its exactly-one branch decision is an
immutable protocol input. Candidate/data governance may be investigated during
late H2, but hypotheses remain frozen before outcome inspection. The finite
branch does not bypass H3.0, and a Lean file cannot satisfy this scheduling
dependency by import.

**Single owner:** prospective
`specs/h3-reference-study/preregistration.yaml`, versioned and immutable after
freeze. This design file is not the final protocol.

### Questions to freeze

1. On the continuous branch, under which precision and support conditions does
   the stationary Gaussian have the selected blanket conditional independence;
   on the finite branch, which repaired H1 theorem supplies the corresponding
   fact?
2. Does the recognition map recover the exact external conditional mean, and
   when does it fail to be identifiable?
3. Does the inference implementation recover parameters and latent states on
   synthetic data generated from the formal model?
4. Do observation-contingent actions improve the locked objective relative to
   capacity-matched filtering, control, and policy baselines?
5. Do held-out observations support the blanket, stationarity, and flow-
   alignment assumptions better than named alternatives?
6. Is any measured energetic quantity available that could support a physical
   thermodynamic bridge, or is the result limited to path-law information?

### Protocol contents

- H3.G0 acceptance-record hash and the exactly-one continuous/finite branch;
- exact data source, license, consent/governance, checksums, and immutable raw
  split;
- variable-to-`Axis` mapping, raw units, positive affine standardization,
  sampling times, missingness, exclusions, and preprocessing;
- synthetic generator and parameter ranges;
- model and parameter recovery thresholds;
- train/validation/test or time-block split fixed before fitting;
- baseline models with capacity and optimization budgets;
- primary and secondary metrics;
- calibration and posterior predictive checks;
- conditional-independence, stationarity, and intervention diagnostics;
- multiplicity control and minimum supportive effect;
- failure, null-result, and early-stop rules; and
- exact claims permitted for each outcome pattern.

### Go conditions

- Data expose enough internal, external, and interface variables to test the
  proposed blanket rather than infer it solely from latent labels.
- Sampling resolution and duration can assess stationarity and dynamics.
- At least one intervention or defensible causal assumption is available for a
  causal claim; otherwise the study is observational.
- Synthetic model and parameter recovery are identifiable in principle.
- The data license permits retention and reproducibility at the planned level.

**No-go action:** freeze the real-data branch, publish the mathematical and
synthetic case study as such, and record the missing data capability. Do not
change the research question after inspecting outcomes.

## H3.1 — typed scientific model and dimensional boundary

**Depends on:** H3.G0 and H3.0 for both branches. H3.0 is a hard dependency,
not a provenance note and not an optional real-data edge.

**Single owner:** new foundation `formal/h3_reference_model.lean`, namespace
`FEP.H3ReferenceModel`. On the continuous branch it selects, but does not copy,
H2.5's exact symmetric-precision carrier and H2.4's native action-indexed
interface. The finite branch remains owned by H1 and enters only through the H3
composition leaf's explicit bridge. H2 posterior/filter/control and H1 finite
blanket/policy/control theorems likewise remain composition dependencies of
`h3_case_study.lean`; the H3 foundation does not import
`gaussian_information_geometry`, `posterior_convergence`, `controlled_markov`,
`markov_blanket`, or any composition leaf.

### Exact coordinate seams

Define `Axis` with constructors in scientific order `external`, `sensory`,
`active`, `internal`, and one equivalence `axisFin : Axis ≃ Fin 4` fixed by

```text
external ↦ 0
sensory  ↦ 1
active   ↦ 2
internal ↦ 3
```

All pullbacks of H2.5 matrices and laws use `axisFin`; no declaration relies on
constructor ordinals or an unproved coordinate convention.

The finite H1 bridge is a separate H3.2 composition obligation, not an H3.1
foundation import or field. H1's blanket carrier is definitionally
`Internal × (Sensory × (Active × External))`; for scalar blocks the required
permutation is

```text
toH1 x = (x internal, (x sensory, (x active, x external)))
```

with inverse obtained by reading the tuple as internal, sensory, active,
external and writing those values back to the corresponding `Axis`. The H3.2
composition leaf directly imports the finite owner and proves both inverse
laws. This is a named permutation, not tuple reassociation and not an implicit
identification between `Axis → ℝ`, `Fin 4 → ℝ`, and the H1 tuple.

### Dimensionless state and raw-unit bridge

The formal dynamical state is `StandardState := Axis → ℝ`, interpreted as
dimensionless standardized coordinates. H3.0 supplies an axis-indexed raw unit,
offset `b`, and scale `s`. H3.1 admits raw data only through the positive affine
calibration

\[
x^{\mathrm{raw}}_a = b_a + s_a z_a,
\qquad 0 < s_a,
\qquad
z_a = \frac{x^{\mathrm{raw}}_a-b_a}{s_a}.
\]

The forward and inverse laws and strict monotonicity are theorems. Raw values
with different unit tags are never added or inserted directly into the OU
matrix. A raw-unit covariance or energy statement must be derived through the
calibration and retain its unit annotation; a dimensionless covariance is not
measured energy.

### Primitive model data

The H3.1 structure may store only the frozen branch/protocol reference,
standardized initial/mean and observation parameters, action/intervention
primitives, admissible parameter bounds, the positive raw calibration,
unit/data-column mapping, and, on the continuous branch, the exact imported H2
carrier reference. It must not contain fields asserting a stationary
covariance, invariant law, blanket, recognition map, or identifiability. On the
continuous branch, `Sigma` is derived from H2.5's precision `K`; on the finite
branch, the H3.2 composition derives every invariant or blanket fact from the
repaired H1 carrier without adding an H1 field to the H3 foundation.

Variational free energy, expected free energy, native relative entropy,
Helmholtz free energy, work, heat, and entropy production remain separate
definitions. Any equality between them is a theorem with dimensional and
constitutive premises.

### Acceptance

- Dimensionally incompatible identifications do not typecheck or fail a
  dedicated unit/semantic validator.
- The branch type prevents finite consumers from projecting continuous-only
  covariance or diffusion fields and prevents continuous consumers from
  importing an H1 theorem through an unnamed coercion.
- Every fitted parameter has an admissible domain; identifiability status is a
  derived theorem or an explicit unresolved result, never a Boolean field.
- Latent-state relabeling and equivalent parameterizations are recorded.
- A nonpositive raw scale and a degenerate precision/noise case are executable
  rejection boundaries.

## H3.2 — dynamics, stationarity, blanket, and intervention

**Depends on:** H3.1; reuses H1.1, H1.6, H2.4, and H2.5.

**Single owners:** on the continuous branch, the H3 model foundation derives
intrinsic transition, stability, covariance, and invariance from the imported
H2 carrier. On the finite branch those intrinsic facts remain with H1. The H3
composition leaf owns the explicit H1 tuple permutation and derives the
branch-appropriate blanket equivalence, recognition/synchronization,
identifiability, preservation, intervention, and countermodel bridges. Generic
blanket, causal, and semigroup laws remain in their existing foundations.

### Target chain

- on the continuous branch, the `Axis` pullback of H2.5's exact `K` and derived
  `Sigma`, the transition semigroup, and the invariant Gaussian law;
- on that branch, symmetry/positive-definiteness of `K`, both `K`/`Sigma`
  inverse identities, and covariance/invariance derived from those facts rather
  than stored;
- equivalence between the chosen Gaussian blanket statement and the relevant
  external--internal **precision** zeros, with covariance zeros retained as a
  rejected substitute;
- the synchronization/recognition map derived from the Gaussian conditional
  mean blocks and identifiability derived from the corresponding injectivity or
  rank theorem, with a rank-deficient countermodel;
- preservation of the blanket under the selected dynamics;
- intervention-kernel normalization and named non-descendant invariance; and
- on the finite branch, only the corresponding theorems that follow from the
  repaired H1 terminal carrier; and
- positive and negative models for sparse-coupling, blanket, recognition, and
  alignment implications.

### Stop/go slices

1. **H3.2a — intrinsic carrier derivation:** on the continuous branch, pull back
   the H2 carrier and derive its covariance/invariance facts; on the finite
   branch, prove the exact H1 tuple permutation and reuse only H1-owned
   intrinsic facts. A failure closes every later H3.2 clause; it is not repaired
   with certificate fields or an extra foundation import.
2. **H3.2b — blanket seam:** on the continuous branch, prove the exact
   precision-zero equivalence and a covariance/sparse-coupling countermodel; on
   the finite branch, consume only the corresponding H1 theorem and
   countermodel. Failure removes the blanket edge.
3. **H3.2c — recognition and identifiability:** on the continuous branch,
   derive the conditional-mean map and its injectivity/rank condition, then
   retain a nonidentifiable boundary; the finite branch claims only an H1-owned
   analogue if one exists. Failure removes recognition/identifiability claims
   without blocking plain filtering.
4. **H3.2d — intervention:** normalize the selected intervention kernel and
   prove only the named invariances its graph premises support. Failure removes
   causal edges and leaves an observational study.

### Falsification requirements

The empirical protocol must separately test:

- stationarity or controlled nonstationarity;
- conditional independence with uncertainty;
- residual coupling not explained by the blanket;
- synchronization-map stability across splits; and
- intervention predictions when interventions exist.

A good predictive fit does not establish a blanket. Observational conditional
independence does not establish the causal graph.

## H3.3 — inference, VFE, contraction, and calibration

**Depends on:** H3.2; reuses H1.2--H1.3, H2.3, and H2.6.

**Single owner:** the inference declaration block in
`formal/compositions/h3_case_study.lean`, namespace
`FEPComposed.H3CaseStudy`. The H3 model foundation supplies only intrinsic
instance laws.

### Formal targets

- the selected filter is the exact native posterior for the linear-Gaussian
  model;
- posterior-form VFE bounds surprisal and is uniquely attained at that
  posterior under stated conditions;
- posterior mean/covariance recursion uses the same observation model as H3.2;
- synthetic posterior or parameter consistency under identifiability; and
- a misspecified-noise or non-identifiable countermodel.

### Empirical targets

- coverage of posterior intervals or regions;
- held-out log predictive density and proper scoring rules;
- residual calibration and whiteness;
- parameter and latent-state recovery on synthetic data; and
- sensitivity to priors, initialization, preprocessing, and stationarity
  violations.

The theorem may establish consistency on the formal model. Only the empirical
study may report calibration on observed data.

## H3.4 — action, EFE, and control comparison

**Depends on:** H3.3; reuses H1.4 and H2.6.

**Single owner:** the action/control declaration block in
`formal/compositions/h3_case_study.lean`. Generic policy and controller laws
remain in their existing owners.

### Formal targets

- a finite-horizon action or policy law over the H3 belief state;
- exact conditions under which the selected EFE objective and a linear-
  quadratic or reward-control objective choose the same action;
- a counterexample when epistemic value, preferences, or support violate those
  conditions;
- closed-loop value no worse than the matched open-loop plan **only** for the
  identical objective and horizon, with the closed-loop policy class proved to
  contain the embedded open-loop plan and the optimizer exact (or with an
  explicit optimization-error bound);
- stability or boundedness of the selected controlled dynamics under an
  independently checkable controller certificate.

A restricted-controller countermodel must show that dominance can fail when
the closed-loop class does not contain the open-loop comparator. Sharing a
belief and transition alone is not a dominance proof.

### Empirical comparisons

Compare against capacity-matched, separately tuned:

- Bayesian/Kalman filtering without active selection;
- linear-quadratic or model-predictive control;
- a finite POMDP/policy-tree baseline where applicable;
- reward-based reinforcement learning only when the data and action protocol
  support it; and
- ablations removing epistemic value, preference terms, or belief updates.

Primary comparisons use held-out prediction, calibration, control cost, and
intervention response. In-sample free energy alone is not an outcome metric.

## H3.5 — thermodynamic and Lyapunov bridge

**Depends on:** H3.2 and H3.4; reuses H1.7, H2.4, and finite-grid path laws.

**Single owner:** the information/constitutive declaration block in
`formal/compositions/h3_case_study.lean`. The block must import the selected H3
model rather than reconstructing its transition or units.

### Layers

1. **Information layer:** native KL to the invariant law and finite-grid path
   KL, derived from the probability model.
2. **Dynamical layer:** a Lyapunov or dissipation theorem for the selected
   semigroup/controller.
3. **Physical layer:** work, heat, temperature, or entropy flow only when the
   model supplies measured units and a reviewed local-detailed-balance or
   constitutive law.

### Target declarations

- monotonic native KL or a named Lyapunov functional;
- forward/reverse finite-grid path-ratio theorem;
- strict non-equilibrium witness;
- a constitutive implication from measured physical premises to thermodynamic
  entropy production, if such premises are available; and
- a counterexample showing that path KL alone does not identify measured heat.

If the dataset has no energy/temperature measurements or defensible
constitutive model, H3 reports only information-theoretic path asymmetry. It
must not rename that quantity physical dissipation.

## H3.6S/H3.6E — executable oracle, synthetic recovery, and empirical analysis

**H3.6S depends on:** H3.3--H3.5 and the frozen H3.0 protocol.

**H3.6E depends on:** H3.6S and the licensed real-data branch opened by H3.0.

**Single owner:** prospective
`src/fep_lean/verification/h3_reference_study.py` consumes exported, typed model
parameters and theorem-owned equations. It does not become a second scientific
model registry. Exact test fixtures bind its formulas and parameter order to
the Lean declarations they mirror.

### Feasibility spike

Before implementing the full analysis, round-trip one theorem-owned exact
fixture and run model/parameter recovery on two identifiable synthetic settings
with frozen tolerances. The executable must reject reordered parameters,
missing units, and stale theorem/source digests. Failure closes the real-data
branch before any protected outcome is read.

### Execution order

1. Generate exact rational/symbolic fixtures from the formal model where
   feasible.
2. Verify implementation invariants and theorem-specialization examples.
3. Run simulation-based calibration.
4. Run model and parameter recovery on synthetic data.
5. Run negative controls and misspecified models.
6. Record H3.6S acceptance or rejection atomically.
7. Only after H3.6S passes, unlock the frozen H3.6E real-data split.
8. Run the preregistered analysis once; label every later analysis exploratory.

### Required artifacts

- environment and source digests;
- raw-data provenance and immutable split receipt;
- preprocessing and exclusion receipt;
- synthetic seeds and parameter draws;
- all fitted-model diagnostics and failed runs;
- exact metric definitions and confidence intervals;
- baseline tuning budgets;
- machine-readable claim matrix; and
- a report that retains null, negative, and sensitivity results.

### Stop rules

- Failed model recovery blocks real-data fitting.
- Failed parameter recovery blocks mechanistic parameter claims.
- Failed calibration blocks uncertainty claims.
- Failed stationarity/blanket diagnostics block the corresponding FEP reading.
- A baseline win or null result remains a result; it does not trigger outcome-
  aware metric replacement.

## H3.7 — independent review, replication, and publication

**Depends on:** H3.6S, plus H3.6E when the real-data branch was opened.

**Single owner:** the frozen claim matrix, reviewer decisions, and clean-room
reproduction record under prospective
`specs/h3-reference-study/acceptance/`. Publication output is a projection of
that record, not a second acceptance owner.

### Replication spike

Give a context-free reviewer only the release bundle and protocol. Go when the
reviewer reproduces one symbolic fixture and one preregistered synthetic run,
including hashes and claim classifications. Any mismatch is routed to the
owning H3 row; publication remains blocked until it is resolved or recorded as
a terminal negative result.

### Independent reviews

- Lean proof and axiom audit by a reviewer who did not author the terminal
  theorem;
- domain review of the model-to-system mapping;
- statistical review of preregistration adherence, recovery, calibration, and
  multiplicity;
- adversarial review centered on H1 countermodels and stronger readings; and
- replication from the retained release bundle in a clean environment.

### Publication boundary

The publication separates four result tables:

1. theorem-backed statements;
2. supplied modeling assumptions;
3. numerical/synthetic observations; and
4. real-data empirical results.

Each table names its evidence artifact and exact source version. Claims about
brains, organisms, cells, self-organization, sentience, or universal Bayesian
inference remain prohibited unless a later separately reviewed study directly
supports them.

### Horizon 3 exit gate

- The source-bound H3.G0 record, frozen H3.0 protocol, formal model, executable,
  and claim matrix name the same single branch; no finite/continuous hybrid
  claim survives.
- The full typed chain compiles and its countermodels remain in the audit.
- Synthetic model and parameter recovery meet the frozen thresholds.
- The preregistered real-data analysis either completes or records a governed
  no-go/null outcome without relabeling.
- Baseline, calibration, intervention, and sensitivity results are retained.
- Independent formal, domain, and statistical reviewers sign the exact claim
  matrix.
- Reproduction from the release artifact matches retained hashes and metrics.

Only this exit gate permits a narrowly worded empirical conclusion about the
selected model and dataset. It never establishes a universal Free Energy
Principle.

## DRAFT preregistration (2026-08-28; CONDITIONAL-ON-H2.7; not yet frozen)

This draft is a design-time preparation for H3.G0/H3.0, written while H2.7 is
still the sole legal implementation slice and H3 is closed. Nothing here is a
frozen protocol; H3.0 remains the only prospective owner of
`specs/h3-reference-study/preregistration.yaml`. Every statement that depends
on the H2.7 terminal merge landing is marked **CONDITIONAL-ON-H2.7**. The
preregistered branch is **continuous** (the H2.5 symmetric-precision
linear-Gaussian/OU carrier); the H1 partially observed reference agent remains
the finite branch and negative control, not selected here.

### Branch-selection criteria (H3.G0, continuous branch)

H3.G0 accepts the continuous branch only if all of the following resolve
read-only, source-bound, by digest, in the accepted H2 owners — none may be
rebuilt, repaired, or copied into an H3 namespace:

1. Exact `Fin 4` symmetric-positive carrier in
   `FEP.Fin4GaussianSemigroup` (`lean/FepSketches/fin4_gaussian_semigroup.lean`):
   stored precision `K` with `K_posDef`; covariance definitionally derived as
   `Sigma` with `K_mul_Sigma`, `Sigma_mul_K`, `Sigma_eq_entries`,
   `Sigma_isSymm`, `Sigma_posDef`; exact axis order `axisFin_order` with
   `external ↦ 0, sensory ↦ 1, active ↦ 2, internal ↦ 3`.
2. Transition and semigroup: `transition_apply`, `transition_zero`,
   `transition_add`, `transition_mean`, `transition_covariance`,
   `transitionCovariance_posSemidef`, `transitionCovariance_posDef`.
3. Stationarity and convergence: `stationaryLaw_eq_gaussian`,
   `stationaryLaw_invariant`, `transitionProbability_tendsto_invariant`,
   `integral_transition_tendsto_invariant`; terminal export `exactFin4Carrier`.
4. Scalar specialization, exactly and not by shape: `scalarParameters_exact`
   and `projectedTransition_eq_scalarOU` (normalized all-ones eigenmode, rate
   `2`, diffusion variance rate `2`) against the accepted
   `FepSketches.scalar_gaussian_semigroup` owner.
5. Conditioning/precision seam in `FEP.GaussianPrecisionConditioning`
   (`lean/FepSketches/gaussian_precision_conditioning.lean`): native
   `stationaryPartition_eq_compProd`, `endpointCondDistrib_ae_eq_product`,
   `externalConditionalKernel_mean`, `externalConditionalKernel_variance`,
   `external_condIndep_internal_given_blanket`,
   `stationary_external_internal_covariance` (= `1/24`),
   `precisionZero_covarianceNonzero_condIndep`; non-vacuity via the
   `perturbedEndpoint*` chain
   (`perturbedEndpoint_external_internal_covariance` = `-1/15`,
   `perturbedEndpoint_external_not_indep_internal`).
6. **CONDITIONAL-ON-H2.7:** the H2.7 exit acceptance. Until H2.7 lands, the
   only VFE/natural-gradient surface is the accepted but non-maintained
   source-bound spike `FEPProbe.H2_7GaussianVFE`
   (`spikes/07_gaussian_vfe_natural_gradient.lean`, decision
   `specs/done/horizon-2-smooth-stochastic/readiness/repairs/07-gaussian-vfe-natural-gradient.json`),
   which may not be cited as a maintained owner by H3.

No eligible acceptance record may substitute an arbitrary Hurwitz matrix, a
newly fitted covariance, a positional/equinumerous H1 coercion, or a symbolic
matrix receipt for these named theorems.

### Observation model and finite intervention set as they would bind

These bind only after H3.G0 records the branch and H3.0 freezes a protocol on a
licensed dataset; the following is the template of the binding, not a protocol.

- Observation model: at each sampling time `t`, one interface coordinate is
  observed through a Gaussian channel with the frozen mean/variance supplied by
  the filter owner (H2.6a posterior family; native closed-form posterior
  `closedFormPosterior_ae_eq_native` and evidence
  `evidenceLaw_eq_gaussian`, `evidenceDensity_pos` in
  `FEPComposed.GaussianFilter`). The observation index is restricted to
  `sensory` and/or `active` axes; `external` is latent by construction of the
  blanket partition in `partitionCoordinates`.
- Finite intervention set: a finite `Action` type (as in
  `FEPComposed.GaussianControl`), each action selecting one H2.4b
  action-indexed native transition over one common positive comparison
  duration, with objective the posterior-predictive quadratic terminal risk
  `quadraticActionRisk_eq_closedForm` (plus separately typed nonnegative
  action penalty). **CONDITIONAL-ON-H2.7:** any extension from one-step
  selection toward multi-step observation-contingent policies requires the H2.7
  terminal merge first; H3.4's dominance claims additionally require the
  closed-loop-contains-open-loop class condition, which no current H2 theorem
  establishes and which must be proved in `h3_case_study.lean`, not assumed.
- All bind through the H3.1 `Axis ≃ Fin 4` pullback and the positive affine
  raw-unit calibration; no raw covariance or energy claim without the unit
  annotation.

### Claim-matrix TEMPLATE (rows pre-filled from what the H2 theorems prove)

Statuses: `proved` (Lean, source-bound) / `assumed` (supplied scientific
premise) / `numerically-reproduced` / `identified` / `held-out` / `rejected-or-unknown`.

| # | Claim | Status at H3.G0 | Source |
| --- | --- | --- | --- |
| C1 | `K` is symmetric positive-definite; `Sigma = K⁻¹` with exact entries | proved | `K_posDef`, `Sigma_eq_entries`, `Sigma_posDef` |
| C2 | Exact transition is a measurable Markov kernel with Chapman–Kolmogorov | proved | `transition_apply/add/zero` (H2.5b/H2.5c) |
| C3 | Stationary Gaussian law exists and is invariant; transition converges weakly to it | proved | `stationaryLaw_eq_gaussian/invariant`, `transitionProbability_tendsto_invariant` |
| C4 | Scalar OU specialization exact (rate 2, diffusion variance rate 2) | proved | `scalarParameters_exact`, `projectedTransition_eq_scalarOU` |
| C5 | Native conditioning: blanket-partition law = blanket law ⊗ endpoint conditional kernel, for every center | proved | `stationaryPartition_eq_compProd`, `endpointCondDistrib_ae_eq_product` |
| C6 | External/internal conditional independence given (sensory, active); precision entry zero, covariance `1/24 ≠ 0` | proved | `external_condIndep_internal_given_blanket`, `precisionZero_covarianceNonzero_condIndep` |
| C7 | Precision-zero ⇒ CI is non-generic (perturbed witness: covariance `-1/15`, non-independence) | proved | `perturbedEndpoint_*` chain |
| C8 | One-step finite control: Gaussian closed-form risk, finite attainment, native-posterior selector agreement, strict/tie witness | proved | `quadraticActionRisk_eq_closedForm`, `selectedAction_le`, `nativePosteriorSelectedAction_le`, `boolWitness_*` (H2.6b) |
| C9 | Scalar OU KL-to-stationary non-increase | proved | `ouKL_to_stationary_nonincrease` |
| C10 | VFE = KL-to-posterior + density surprisal, with Fisher natural-gradient descent, on the scalar carrier | **CONDITIONAL-ON-H2.7** (R0 spike `FEPProbe.H2_7GaussianVFE`; not a maintained owner until H2.7 exits) | H2.7-R0 decision JSON |
| C11 | Data satisfy linear-Gaussian/OU dynamics on the selected axes | assumed (H3.0 diagnostic plan required) | — |
| C12 | Standardization maps raw units to the dimensionless carrier without distortion | assumed pending H3.0 unit map | — |
| C13 | Conditional variances/means recover from the actual dataset observations | identified / held-out (H3.3/H3.6E only) | — |
| C14 | Parameter recovery on synthetic data from the formal model | numerically-reproduced / held-out (H3.6S gate) | — |
| C15 | Observation-contingent action improves the locked objective over matched baselines on real data | held-out (H3.6E; never from C8) | — |
| C16 | Reversibility, detailed balance, physical work/heat/entropy from KL alone | rejected-or-unknown (explicitly excluded at H2.5b/H2.5d acceptance) | — |
| C17 | Blanket from good predictive fit; causal graph from observational CI | rejected-or-unknown (falsification requirements, H3.2) | — |
| C18 | Multi-step/EFE-optimal or infinite-horizon control | rejected-or-unknown (excluded by H2.6b no-go; needs new proof) | — |

### Explicit boundary list (each a standing premise of every proved row)

- **Linear** dynamics only (matrix-exponential semigroup; no SDE/Itô,
  Fokker–Planck, or Girsanov claim).
- **Gaussian** laws only (native multivariate Gaussian kernels; no non-Gaussian
  observation or recognition family).
- **Symmetric-positive precision** (the exact fixed `K`, not an arbitrary
  Hurwitz matrix; covariance derived as inverse, never stored).
- **Dimensionless standardized state** (`StandardizedState := Axis → ℝ`; raw
  units enter only through the positive affine calibration with unit
  annotation).
- **Stationarity** of the invariant law (invariance and weak convergence are
  proved; reversibility/detailed balance are not).
- Additional H2-bound exclusions: no transition-row conditioning beyond the
  stationary law, no generic precision-zero converse, no second Fin4 carrier,
  no biological identity or measured-energy interpretation.

### Collapse clause (what survives if H2.7 fails)

If H2.7 does not exit, all **CONDITIONAL-ON-H2.7** rows close and the draft
collapses as follows:

- Survives: C1–C9 (H2.5a/b/c/d and H2.6a/b are accepted maintained owners,
  independent of H2.7). The continuous carrier itself — algebra, transition,
  semigroup, stationarity, scalar specialization, and the conditioning/precision
  seam — is fully H2.7-independent.
- Does not survive: C10 (VFE/natural-gradient seam) and every H3.3
  surprisal-form clause that needs it; H3.4 multi-step/observation-contingent
  extensions; the continuous-branch H3.G0 acceptance as a whole, because the
  H3 spec requires the H2.7 exit acceptance as part of continuous eligibility.
  H3.0–H3.7 remain closed.
- Recovery path: freeze a synthetic-only study scoped to the surviving rows
  (a linear-Gaussian filtering/stationarity/conditional-independence case
  study without VFE, EFE, or any thermodynamic row), or select the finite H1
  branch under a fresh H3.G0 after H1.8 exits — with all covariance, diffusion,
  and continuous-time claims mechanically excluded.
