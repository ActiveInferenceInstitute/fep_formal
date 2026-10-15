# Upcoming package and formalization improvements

Future scopes were reviewed against maintained source on 2026-10-02; current
acceptance context was refreshed on 2026-10-05. This document scopes future
work; it is neither an acceptance receipt nor a second backlog, theorem registry,
or research protocol. [TODO.md](../../../TODO.md) owns open delivery work,
[remaining acceptance](../../../specs/comprehensive-science-improvement/NEXT.md)
owns the current execution sequence, and the
[locked program](../../../specs/comprehensive-science-improvement/PROTOCOL.md)
retains all nine original acceptance criteria. Future work cannot substitute
for an unfinished criterion.

The published [v1.6.0 release](https://github.com/ActiveInferenceInstitute/fep_formal/releases/tag/v1.6.0)
contains the [mathematical methods integration](../../mathematical-methods.md).
Subsequent Lean 4.35 and support-aware changes have their own
[accepted source checkpoint](../../../ISA.md#current-assessment).
The [active next-step campaign](../../../specs/comprehensive-next-steps/README.md)
reconciles this prospective roadmap against the delivered source and owns the
current pickup point. Later releases retain the [release procedure](../../release.md).
A version number, source publication or green CI run does not establish a
completed scientific study.

## Size, ownership and activation

Minor means an existing-owner refinement with a bounded compatibility surface.
Medium crosses one named API or mathematical seam. Major requires a staged
dependency chain, independent review and several evidence planes. These sizes
describe implementation scope, not a semantic-version promise or a calendar.

Before activating a proposal below, its bounded spec must instantiate the
[work-package contract](research-contract.md): exact owner, carrier/API,
predecessors, stop/go probe, positive witness, boundary result, tests and
reviewer. Proposed identifiers here are planning references only. They do not
reserve topic IDs or create catalogue, relation or capability claims.

Use existing owners where practical. New Python owners require the coordinated
versioned [source roster](../../../src/fep_lean/output/provenance.py) refresh;
new Lean resources require the six manifest/namespace facts in the research
contract. Generate projections from their canonical owners. Preserve the
four dependency pins unless a separately reviewed upgrade changes the program.

## Current implementation that still needs acceptance

The following code is present. Its existence must not be presented as a new
proposal or as proof that the final source epoch passed every gate.

| Original scope | Inspected implementation | Remaining obligation |
| --- | --- | --- |
| PKG-1: truthful static status | `SectionReport`, `PublicationReadinessReport` and `bridge_pin_section` in [cli.py](../../../src/fep_lean/cli.py); named/omitted GNN and source-race controls in [status tests](../../../tests/test_status_verb.py) | Final-source process-free, byte/mtime-preserving acceptance; unavailable comparisons remain unverified and drift remains stale on both status surfaces. Exit zero means composition succeeded. |
| PKG-2: distribution support | The declared Python floor in package metadata; isolated installed API/resource/help and parsed wheel-metadata controls in [distribution tests](../../../tests/test_distribution.py) | All 15 hosted cells passed at `c99e933`. Final-source runtime evidence remains required after later owner edits; the local five-cell matrix retains its 15 GiB prerequisite checked before launch and every cell. Validator runtime remains CPython 3.14; package import support does not imply native capture support. |
| PKG-3: documentation and render gates | Classification and source/template-link retention in [CI](../../../.github/workflows/ci.yml), with positive and adversarial distribution controls | Hosted Lean/render passed at `c99e933`; final-source PDF, render receipt, fonts, renderer and source manifest must still validate after owner edits. Preserve fresh independent infrastructure review; failed or skipped renders supply no accepted artifact. |
| PKG-4: capture and publication readiness | `PublicationCapturePlan`, `run_publication_capture` and `plan_publication_capture` in [release capture](../../../src/fep_lean/output/release_bundle/_core.py); strict [prerequisite aggregation](../../../src/fep_lean/output/release_bundle/_prerequisites.py) | Actual seven-stage capture, current native/audit/Python/render/numerical/browser acceptance, and two byte-identical archives independently accepted against final source. Static readiness and custom test plans cannot replace production capture. |
| FORM-1: deterministic information witnesses | `finiteChannel_identity_preservesKL` and `constantChannel_KL_strict` in [variational duality](../../../src/fep_lean/formal/variational_duality.lean) | Current warning-free focused/aggregate native and declaration/axiom evidence; retain the zero-reference convention and current reviewed theorem-proxy disposition. |
| FORM-2: relative-support information bridge | `weightedDirac_klDiv_eq_finiteKL_of_relativeSupport`, `nativeChannelMutualInformation_eq_finite` and the finite garbling theorems in [decision risk](../../../src/fep_lean/formal/decision_risk.lean) | Current source-bound native/audit and semantic review, including shared-zero, deterministic, asymmetric and singular boundaries. Native infinity is not the totalized finite convention. |
| FORM-3: actual finite rate-distortion optimization | Compactness-derived `rateDistortion_exists_minimizer`, infimum-derived weak duality and Boolean boundary witnesses in variational duality | Current source-bound acceptance for feasibility, attainment, informative interior, infeasible budget, zero multiplier and nonunique optimizer. The existing primary theorem still assumes component bounds; general strong duality is unproved. |
| FORM-4: frozen H3 chain | Manifested [reference model](../../../src/fep_lean/formal/h3_reference_model.lean), [composition](../../../src/fep_lean/formal/compositions/h3_case_study.lean), native export, synthetic executor and study bundler | Current native/export and three independent proof-role reviews, unchanged one-attempt synthetic execution and complete replay, outcome-bound claim reviews, and clean installed study reproduction. The licensed empirical branch remains governed no-go without data. |

The [2026-10-02 Q7 capture](../../../specs/comprehensive-science-improvement/evidence/public-q7-final-source-20261002-r1/summary.json)
closed the source-pair residual for its recorded native inputs. Preserve its
emitter checks, native receipt and postcapture guidance preimages as historical
evidence; the old isolated r3 acceptance is not rebound to changed source.
The separately reviewed
[2026-10-05 Q7 observation](../../../specs/comprehensive-science-improvement/evidence/public-q7-current-source-20261005-r1/summary.json)
records a complete 2026-10-05 capture with twelve stages and four closing checks,
closing the later Q7 requirement for its recorded 291 native inputs. The public
observation is not itself a native receipt or validation of this checkout;
later source-owner changes require fresh source-pair acceptance. Package,
export, hosted and scientific acceptance remain separate obligations. Active
GNN work, failed attempts and historical Q5/Q6/Q7 receipts remain preserved;
static coefficient proofs leave runner execution unverified. Current guidance
and all declared checks remain obligations under the ninth criterion.

The output/configuration repairs are minor existing-owner reliability work.
Their retained focused validation and independent infrastructure reviews apply
to the reviewed source epochs; later repairs require their own checks and review.
Final source-bound native, package and scientific acceptance remains open.
They do not activate the future medium API/information-theory scopes or the
major Windows capture, control and path-law scopes below. Those proposals retain
their named predecessors and reviews; none substitutes for current package or
once-only H3 acceptance, or changes the frozen scientific protocol.

## Core package: minor scopes

### CORE-M1 — precise operator contracts

**Owner and evidence:** existing CLI plus [API guide](../../api.md) and
[development guide](../../development.md). The CLI already distinguishes static
readiness, runtime capture and archive parity; the guide already documents the
POSIX-only execution boundary.

- **Outcome:** one concise command/support table states required inputs,
  mutation/process behavior, supported runtime and exit meaning for `status`,
  `preflight`, `verify`, bridge checks and `publication-capture`. Resolve wording
  that implies a pin-presence check compared an omitted GNN checkout.
- **Dependencies and go probe:** accepted PKG-1/PKG-2 behavior; compare the table
  with actual parser/API signatures and existing installed help output.
- **Acceptance and failure controls:** the documented examples use existing
  options; missing checkout, omitted sibling, stale receipt and unsupported
  capture platform remain distinguishable. Preserve additive preflight JSON
  policy and the exit-zero composition contract. Add behavioral tests only if
  behavior changes; documentation checks cover prose-only edits.
- **Review and boundary:** operator review decides that every state leads to a
  concrete next action. No status call acquires dependencies, starts providers,
  collects tests, repairs evidence or silently changes validator policy.

### CORE-M2 — maintain current guidance through dependency review

**Owner:** maintained Markdown and its inbound references; the canonical backlog
remains TODO.md. The current cleanup reconciles the [program overview](README.md),
horizon guides and [handoff](handoff.md) with accepted H2 history and the frozen
H3 guide. That cleanup belongs to the current program; this follow-on scope
keeps active reading paths synchronized as subsequent slices are accepted.

- **Outcome:** active reading paths contain only current instructions and open
  next steps. Move accepted delivery facts to changelog/release notes or linked
  history; replace duplicated live status tables with links to canonical owners.
- **Dependencies and go probe:** current acceptance decisions and a complete
  caller/link inventory for each retirement candidate. A historical count or
  an old filename alone is insufficient grounds for deletion.
- **Acceptance and failure controls:** strict links, hygiene and xrefs pass;
  no completed row remains in the open backlog. Immutable freezes, raw failed
  scientific results, countermodels and historical custody receipts remain
  accessible with their original source boundaries.
- **Boundary:** remove misleading active claims without rewriting scientific
  history or deleting unverified work as though it completed. An item leaves
  TODO only when its existing closure rule passes at the claimed source epoch.

## Core package: medium scopes

### CORE-D1 — expose one reusable typed readiness API

**Owner:** the existing CLI models and existing evidence/release owners. Current
readiness types live in cli.py, while strict archive prerequisites live in
`release_bundle/_prerequisites.py`; application callers currently have no
documented stable readiness type in the root API.

- **Outcome/API:** publish an immutable readiness snapshot API with named
  evidence planes, source bindings, findings and explicit runtime/parity flags.
  Make CLI serialization a projection of that API. Prefer an existing owner
  over a new package or a parallel validator. The proposed stable entry point
  is the existing `build_status_report(project_root, gnn_root=None) -> StatusReport`
  with its immutable nested `PublicationReadinessReport`; review any move into
  the existing evidence owner before changing imports.
- **Dependencies and go probe:** PKG-4 accepted first. Inventory current callers
  and demonstrate a non-CLI consumer of the same snapshot before extraction;
  stop if the move adds another validator or dependency cycle.
- **Acceptance:** old CLI output remains compatible except reviewed additive
  fields; installed-wheel callers produce the same states and bindings as CLI.
  Reuse existing strict validators and preserve source-race invalidation.
- **Controls:** absent/malformed/stale receipts, restored-mtime source changes,
  missing sibling comparisons and unknown planes fail closed. Existing process
  sentinels and real-file snapshots prove that inspection starts no child and
  changes no consumed file. A static all-green inventory remains unverified
  until actual runtime and two-archive parity evidence are validated.
- **Review/no-go:** independent infrastructure review approves ownership and
  compatibility. If API extraction changes receipt identity or schema, retain
  the old epoch and refresh dependent evidence explicitly; never relabel it.

### CORE-D2 — portable semantic and relation queries from one canonical join

**Owner:** catalogue generation/relations/semantics and the existing packaging
resource declarations. The API guide explicitly says the wheel's default
catalogue resource is topics.yaml; authoring metadata, maturity, novelty and
relations currently require explicit checkout paths.

- **Outcome/API:** offer an immutable installed query resource for reviewed
  assumptions, qualified theorem identifiers, authored relations and capability
  blockers. Generate it from the existing canonical join, with a schema version
  and owner digests; do not create another editable registry. The proposed
  resource is `data/formalism-query.json`, consumed through a reviewed
  `load_packaged_formalism_query()` API; packaging/generation/schema review must
  settle its exact type and closed field roster before implementation.
- **Dependencies and go probe:** PKG-2 and canonical projection acceptance.
  Demonstrate an outside-checkout topic-to-theorem/assumption/blocker query and
  a bounded resource-size proposal before adding package data.
- **Acceptance:** installed results conserve the canonical topic/node/edge
  roster and distinguish `formal`, `formal_pairing`, conceptual and blocker
  relations. Reordered, omitted, duplicated, unknown or coherently edited
  members reject. Deterministic regeneration and isolated wheel parity pass.
- **Controls and boundary:** no shared-import inference, automatic semantic
  promotion or bundled historical receipt masquerades as live proof. Optional
  receipt attachment requires explicit source-bound validation. Metadata
  inspection does not invoke Lean or an external model.
- **Review/no-go:** independent API/schema and semantic reviews approve the
  surface. Defer if the proposed snapshot cannot express unknown/current
  evidence separately or duplicates the maintained relation/maturity owners.

## Core package: major scopes

### CORE-J1 — equivalent Windows capture custody and process supervision

**Owner:** existing filesystem/capture and subprocess owners. Current Windows
package imports, resources, help and static readiness are supported; strict
capture deliberately rejects without POSIX descriptor custody. This is a new
execution capability, not a fix that removes the refusal.

- **Stages/dependencies:** first accept current cross-platform PKG-2 and POSIX
  PKG-4; then design Windows handle-relative no-follow custody and descendant
  supervision; independently review a bounded spike before implementation.
- **API target:** preserve the same capture plan, journal and validator contract.
  Use owned handles and an actual process containment mechanism for every
  child/descendant. An unsupported filesystem or missing containment facility
  keeps the pre-execution refusal.
- **Positive acceptance:** a real Windows final-source seven-stage capture and
  two independently accepted identical bundles, followed by installed/archive
  validation on the advertised matrix. Imports/help alone cannot close this.
- **Adversarial acceptance:** junction/reparse-point and ancestor swaps,
  alternate streams/path aliases, case collisions, sharing/permission failures,
  interrupted atomic writes, inherited child handles and timeout-spawned
  descendants all retain rejection evidence and leave no live owned process.
  Preserve source/output membership and raw failed streams.
- **Review/no-go:** fresh independent security/infrastructure review is mandatory.
  If equivalent guarantees cannot be demonstrated, retain the explicit Windows
  capture limitation; do not introduce skips, success sentinels or a relaxed
  archive validator to obtain green cells.

### CORE-J2 — measured incremental capture and bounded resource lifecycle

**Owner:** existing capture plan/journal, process supervisor and strict owner
validators. Selective stage resume and immutable attempts already exist. The
new scope is measured reuse across a documented lifecycle, not merely adding
another resume switch or trusting old zero exits.

- **Dependencies/go probe:** accepted PKG-4 and CORE-D1. Measure a full capture,
  an unchanged resume and one isolated input edit using the same fixed policies;
  identify actual redundant work or leaked owned resources before refactoring.
- **Outcome:** deduplicate only validated immutable inputs/outputs; expose the
  dependency reason for reuse/invalidation and explicit owned storage/process
  budgets. Preserve one decreasing deadline and exclusive attempts. Cleanup
  applies only to demonstrably closed owned resources, with a retained receipt.
- **Acceptance:** resumed and fresh captures independently validate equivalent
  final evidence and archive bytes; unaffected stages are reused only after
  their strict checks pass. Report actual elapsed time, stage executions and
  resource peaks rather than promising a speedup in advance.
- **Controls:** member additions/removals, source replacement with restored
  timestamps, changed templates/pins, killed parent/child, partial journal,
  low storage and concurrent writers reject or invalidate the exact affected
  descendants. A PID/path name alone cannot authorize cleanup. History and
  rejection bytes remain inspectable; no borrowed checkout or dependency cache
  is removed.
- **Review/no-go:** independent infrastructure review and real-child lifecycle
  tests precede rollout. Defer any optimization that weakens custody, hides a
  failure or changes the frozen current-cycle budgets.

## Formalizations: minor scope

### FORM-M1 — align primary theorem proxies with the proved information seams

**Owner:** existing variational-duality body/foundation, decision-risk bridge and
the [maturity records](../../../config/theorem_maturity.yaml). `fep-063` retains
a strict-positive-channel primary theorem despite a broader relative-support
bridge; `fep-064` retains an assumed-component primary theorem with genuine
attainment and dual-bound supporting theorems.

- **Outcome:** review whether a canonical primary statement can use the already
  proved narrower carrier directly. Preserve IDs and signature order, update
  explicit assumptions/non-vacuity and generate all projections from owners.
- **Dependencies/go probe:** current FORM-1–FORM-3 native/audit and independent
  semantic acceptance. Compare proposed primary types with the existing
  advertised scientific statements; no theorem body is changed merely to make
  a maturity label more favorable.
- **Acceptance:** focused and aggregate warning-free compilation, declaration
  ownership/axiom audit and deterministic signature/maturity projections;
  sparse supported, singular, zero-multiplier and nonunique boundaries remain
  visible. Reviewers decide the disposition from the exact statement.
- **Boundary/no-go:** supporting mathematics does not automatically promote an
  old proxy. If a primary swap obscures the distinction between totalized real
  finite KL and native extended KL, or implies general strong duality, retain
  the current primary and document the stronger supporting seam explicitly.

## Formalizations: medium scopes

### FORM-D1 — exact fair-Boolean Hamming rate-distortion curve

**Owner:** existing variational_duality.lean; any cross-topic bridge belongs in
an existing justified composition leaf. Current compactness/weak-duality
theorems prove attainment and a positive quarter-budget optimum, not a closed
rate curve or a general dual optimizer.

- **Target:** on the fair Boolean source and Boolean Hamming distortion, derive
  `R(D) = log 2 - H(Bernoulli D)` for `0 ≤ D ≤ 1/2`, and zero for larger
  feasible budgets. Construct a symmetric channel attaining the value, derive
  the converse, and derive a finite dual multiplier only on `0 < D < 1/2`.
- **Dependencies/go probe:** FORM-3 accepted; compile the exact entropy
  concavity/symmetrization and endpoint-continuity seams at the unchanged pin.
  Stop or split the claim if the selected APIs do not support the converse.
- **Positive/boundary witnesses:** informative interior channels, unique
  zero-budget joint, nonunique half-budget optimizers and infeasible negative
  budgets. Treat zero distortion's limiting multiplier separately; never assume
  that a finite interior dual optimizer exists at an endpoint.
- **Acceptance:** actual derived feasibility, lower bound and equality, focused
  plus aggregate warning-free native/audit receipts and independent information
  theory review. Numerical plots may explain the curve but cannot prove it.
- **Boundary:** this selected finite source does not establish general
  rate-distortion strong duality, continuous-alphabet attainment or a universal
  unique optimizer. Any disposition change applies only to the reviewed proxy.

### FORM-D2 — fixed-truth consistency for the continuous static-latent model

**Owner:** existing [posterior convergence](../../../src/fep_lean/formal/posterior_convergence.lean)
and a justified composition seam. That owner studies a selected Boolean mean
parameter; the current H3 continuous finite-latent result gives joint-law
convergence in probability and explicitly does not claim fixed-truth or
almost-sure consistency.

- **Target:** for each fixed scalar truth, one infinite conditionally i.i.d.
  Gaussian observation law with positive known noise, positive prior variance
  and the derived finite-prefix posterior. Prove posterior mean consistency and
  variance collapse; use an actual strong-law argument before claiming
  almost-sure convergence.
- **Dependencies/go probe:** complete current H3 acceptance first. Freeze a
  subsequent bounded spec; demonstrate that finite-prefix laws agree with the
  existing native posterior and that the infinite trajectory law uses the same
  units/orientation. Do not edit the current H3 protocol or rerun its seeds.
- **Positive/boundary witnesses:** two distinct fixed truths with valid prior
  support; retain a no-information observation and excluded/misspecified noise
  boundary. Name the exact premises lost in each counterexample. Positive
  misspecified variance may preserve point consistency while invalidating
  native-posterior equality/calibration; do not claim inconsistency from wrong
  noise alone.
- **Acceptance:** proved prefix/native equality, measurable convergence and
  explicit probability measure; source-bound native/axiom and domain/statistical
  review. A fresh synthetic protocol, if used, is separately preregistered and
  supports implementation recovery only.
- **Boundary:** static-latent learning is not sequential OU filtering, general
  hidden-state consistency or empirical parameter identification. Keep the
  frozen primary's original claim matrix unchanged.

## Formalizations: major scopes

### FORM-J1 — observation-dependent finite-horizon control on one carrier

**Owner:** existing Gaussian-control and justified composition owners. Current
H3 has an actual two-step terminal squared-coordinate objective, a posterior
threshold selector, a first-action tie and an explicit restricted-class
counterexample. These do not provide arbitrary-horizon control.

- **Stages/dependencies:** accept H3 first; spike measurable belief updates and
  finite-action minimization; define the selected finite-horizon policy class;
  derive Bellman recursion and native-policy cost equality; prove attainment
  and moment bounds before adding a scientific interpretation.
- **Target:** a fixed finite horizon on the same full-state controlled OU kernel,
  declared Gaussian observation law and scalar posterior sufficient statistic.
  Prove any sufficiency reduction; hidden modes are not reset at action changes.
  The stage/terminal cost and admissible observation-dependent policy class are
  explicit, with a measurable tie-breaking selector.
- **Positive/boundary acceptance:** recover the existing two-step result exactly;
  exhibit a longer nontrivial policy and a worse restricted class. Retain action
  ties, zero horizon, inaccessible observations and shifted-preference EFE/risk
  disagreement. Derive risk/moment bounds rather than placing them in fields.
- **Review/evidence:** actual focused/aggregate native and axiom acceptance,
  independent control/domain review and deterministic numerical regressions;
  new scientific measurements require a new pre-outcome protocol.
- **No-go/boundary:** an unavailable measurable-selection or integrability seam
  narrows the exact policy class in a reviewed subsequent spec. No infinite
  horizon, universal EFE/risk equivalence, pathwise stability or biological
  optimality follows from the finite-horizon theorem.

### FORM-J2 — generator-to-path lifting with an explicit library stop gate

**Owner:** existing linear-Gaussian/Fin4 semigroup and Gaussian path owners;
upstream Mathlib contributions only after a source-bound seam review. Current
finite-grid laws and KL results deliberately stop short of continuous-path
SDE, Itô and physical-entropy claims.

- **Stages/dependencies:** current H2/H3 source-bound acceptance; exact pinned
  generator/martingale-problem and stochastic-integration probes; selected OU
  generator derivation; actual path-law construction; only then a justified
  information or dissipation theorem on that path carrier.
- **Target:** the same symmetric positive precision, derived covariance and
  native transition semigroup. First prove a weak generator statement on a
  named test-function class and its semigroup compatibility. A subsequent path
  result must bind finite-dimensional distributions to that exact semigroup.
- **Positive/boundary acceptance:** nonconstant test function and positive-time
  covariance; zero-time and repeated-grid singular controls; observable versus
  hidden-mode distinction. Any change-of-measure result states support and
  integrability conditions and preserves native infinite KL where applicable.
- **Review/evidence:** exact compiling API spikes, independently reviewed carrier
  map, native/axiom receipts and countermodels. No numerically simulated path
  substitutes for construction or a diffusion-existence proof.
- **No-go/boundary:** missing pinned library APIs produce a bounded upstream
  proposal or a recorded no-go for the specific path clause. No local homonym,
  assumed SDE solution or structure field supplies the conclusion. Physical
  heat/entropy requires separately governed constitutive measurements; KL
  alone leaves the current nonidentification theorem intact.

## Sequence, release acceptance and closure

1. Complete the original nine-criterion current program, retain the Q7
   acceptance for its recorded source pair and finish the remaining source-bound
   native, package and scientific gates, including fresh Q7 validation after
   later source-owner changes. Reconcile open-only guidance and obtain final-source
   evidence in each distinct plane; preserve prior accepted epochs and failed
   attempts unchanged.
2. Cut versioned releases through the [release procedure](../../release.md):
   one version/date, a dated changelog section and green hosted CI on the exact
   commit. Package archives, the H3 study/reproduction chain and provider
   evidence are research lanes reported in release notes, not release gates.
   A governed empirical no-go is retained; no synthetic result supplies
   licensed data.
3. Release notes state proved, assumed, synthetic, empirical no-go and
   unverified runtime claims separately. An immutable release DOI comes from
   the Zenodo record for the actual release, never a guessed ID.
4. Close the research lanes above in their own order; each keeps its
   acceptance probe in TODO.md and its Issue.
5. Activate minor future scopes first, then CORE-D1/CORE-D2 and FORM-D1/FORM-D2
   as independent existing-owner lanes. CORE-J2 depends on CORE-D1; Windows
   capture and generator/path work retain their own prerequisite reviews.
   FORM-J1 and FORM-J2 follow current H3 acceptance, without altering its freeze.

The future empirical lane opens only for a named, licensed dataset with known
units, provenance, access and held-out split, followed by a new immutable
analysis protocol and independent review. Null and no-go outcomes remain valid
scientific results. This roadmap supplies no authorization to invent data,
adjust outcomes, spend outside the provider boundary or infer causal/physical
validity from a formal or synthetic pass.

Closure is requirement-specific: record the exact current source, command,
result and receipt; remove the completed row from TODO; retain the delivery
record in changelog/release notes or accepted history. Missing, indirect or
historical evidence keeps the requirement open. Prospective scopes remain here
until an active spec owns their implementation, and accepted scientific
counterexamples remain part of the package's meaning.
