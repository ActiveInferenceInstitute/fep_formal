## Unreleased

Formal-resource strengthening on the existing 168-topic roster. No semantic
disposition changes: each new statement awaits independent review against its
theorem proxy, and compilation establishes only the exact Lean statements.
Every addition builds warning-free at the pin (Lean v4.34.1) and depends only on
`propext`, `Classical.choice` and `Quot.sound`. Lexical Lean declarations grow
from 1,946 to 2,185.

- Path thermodynamics: the Jarzynski normalisation follows from a pathwise
  Crooks relation and is strictly weaker than it ([#87](https://github.com/ActiveInferenceInstitute/fep_formal/issues/87)); Markov-chain path
  laws for general horizons, the Schnakenberg entropy-production form and
  reversed-kernel duality ([#89](https://github.com/ActiveInferenceInstitute/fep_formal/issues/89)).
- Landauer: a generalized bound for erasure of a biased bit follows from local
  detailed balance and path-space entropy production, with no second-law
  hypothesis; reset, fair-bit and reversible-attainment cases are witnessed
  ([#88](https://github.com/ActiveInferenceInstitute/fep_formal/issues/88)).
- Continuous-time Markov chains: a finite generator's exponential is
  stochastic, via uniformisation ([#90](https://github.com/ActiveInferenceInstitute/fep_formal/issues/90)).
- Temporal inference: sum-product messages give exact marginals on finite
  trees, with a numeric star witness and a cycle countermodel for the naive
  message product ([#93](https://github.com/ActiveInferenceInstitute/fep_formal/issues/93)).
- NESS flow: the Helmholtz-decomposed stationary current is divergence-free,
  so the Fokker–Planck rate vanishes; non-skew and rotation countermodels mark
  the hypotheses ([#98](https://github.com/ActiveInferenceInstitute/fep_formal/issues/98)).
- Variational free energy from a joint model: surprisal is derived as the
  negative log evidence of a prior and likelihood kernel, so VFE equals KL to
  the exact posterior plus surprisal, with a strict-gap witness and a
  zero-evidence boundary ([#84](https://github.com/ActiveInferenceInstitute/fep_formal/issues/84)).
- Sophisticated inference with Bayesian updates: one generative model and its
  filter instantiate both planners, which agree with the reachable-belief
  POMDP optimum; the fep-134 witness is re-derived through the filter and an
  observation-ignoring update is a countermodel ([#94](https://github.com/ActiveInferenceInstitute/fep_formal/issues/94)).
- Dirichlet–categorical learning (stage 1): Pólya predictive, rising-factorial
  sequence law, exchangeability and normalised row-wise A/B learning; `K = 2`
  recovers the Bernoulli update and `α = 1` Laplace smoothing ([#95](https://github.com/ActiveInferenceInstitute/fep_formal/issues/95)).
- Gaussian Markov blankets in any dimension: for positive-definite block
  precision, the conditional external–internal covariance vanishes exactly
  when `K_ei = 0`; the `Fin 4` theorem is an instance and a non-sparse precision
  is a countermodel. Measure-level Gaussian conditioning is a recorded Mathlib
  gap ([#97](https://github.com/ActiveInferenceInstitute/fep_formal/issues/97), [#112](https://github.com/ActiveInferenceInstitute/fep_formal/issues/112)).
- Variational free energy: general finite maximum entropy and the constrained
  Gibbs maximiser ([#85](https://github.com/ActiveInferenceInstitute/fep_formal/issues/85)); Helmholtz free energy as the unique variational
  minimum with `dF/dT = −H` derived ([#86](https://github.com/ActiveInferenceInstitute/fep_formal/issues/86)).
- Predictive coding: generalized-coordinate jets are iterated derivatives
  ([#91](https://github.com/ActiveInferenceInstitute/fep_formal/issues/91)); precision is inferred with unique optimum `1/ε²`, and the
  linear-Gaussian chain energy is a negative log joint density ([#92](https://github.com/ActiveInferenceInstitute/fep_formal/issues/92)).
- Collective inference: KL-optimal linear and product-of-experts pooling and
  Dobrushin consensus contraction for any finite mixing matrix ([#96](https://github.com/ActiveInferenceInstitute/fep_formal/issues/96)).
- Relations: four derivational edges give every previously isolated topic a
  witness, raising `formal` edges from 20 to 24 ([#106](https://github.com/ActiveInferenceInstitute/fep_formal/issues/106)); the
  specializes/refines pairing review keeps all seven as pairings ([#104](https://github.com/ActiveInferenceInstitute/fep_formal/issues/104)).
  Released relation rows stay digest-sealed; reviewed additions are listed
  explicitly in the seal test.
- One shared finite-matrix kit replaces a duplicated one ([#99](https://github.com/ActiveInferenceInstitute/fep_formal/issues/99)).

Package and tooling: CLI cold start falls about sixfold through lazy imports
([#117](https://github.com/ActiveInferenceInstitute/fep_formal/issues/117)); custody and acceptance subprocesses run in contained process groups
([#114](https://github.com/ActiveInferenceInstitute/fep_formal/issues/114)); typed pipeline results ([#121](https://github.com/ActiveInferenceInstitute/fep_formal/issues/121)); a common `FepLeanError` base and
one CLI failure emitter for unpinned modules ([#119](https://github.com/ActiveInferenceInstitute/fep_formal/issues/119)); `py.typed` ships in the
wheel ([#116](https://github.com/ActiveInferenceInstitute/fep_formal/issues/116)). CI runs static checks in a parallel job ([#128](https://github.com/ActiveInferenceInstitute/fep_formal/issues/128)), pins uv with
grouped Dependabot action updates ([#135](https://github.com/ActiveInferenceInstitute/fep_formal/issues/135)) and adds a non-gating weekly compile
against the newest Lean/Mathlib pair ([#108](https://github.com/ActiveInferenceInstitute/fep_formal/issues/108)). The hosted release gate requires
every promised job, not only the run conclusion. `release_check.py --bump`
rewrites every version-bearing source ([#131](https://github.com/ActiveInferenceInstitute/fep_formal/issues/131)), and `AGENTS.md` is the single,
test-enforced owner of the required-check list ([#129](https://github.com/ActiveInferenceInstitute/fep_formal/issues/129), [#139](https://github.com/ActiveInferenceInstitute/fep_formal/issues/139)). Link and
hygiene checks cover every maintained Markdown file ([#141](https://github.com/ActiveInferenceInstitute/fep_formal/issues/141)).

## 1.6.0 — 2026-10-07 — mathematical methods, positioning and manuscript supplement

Mathematical integration with the pinned
[OpenAI mathematics corpus](https://github.com/openai/math/tree/adc7f1241b42e322a6451854ab7e4b4c146bf78a).
The corpus supplies research-result organization and selected comparisons;
it is not added as a runtime dependency or an imported proof authority.
The 168-topic roster, semantic dispositions, Lean bodies, and declared
Lean/Mathlib pin retain their existing scientific scope.

The new mathematical methods surface preserves each topic's carrier,
invariant, assumptions, non-vacuity, acceptance requirement and qualified
witnesses. Portable package resources support installed-wheel use without a
checkout. The supplementary manuscript develops topology, law and parameter
embeddings, information geometry, statistics, control and thermodynamics
through worked result contracts, commuting-transfer requirements,
countermodels and precise future proof obligations. Offline interactive
and publication figures expose those associations and their boundaries.

Source-grounded analysis retains 1,946 lexical Lean declarations with exact
statements, binder syntax, namespace context, conclusions and mention roles;
it does not certify translations or kernel dependencies. Twelve selected
upstream statements retain reviewed source passports against 82 locked file
identities. A shared binary representation places 22 FEP family context
unions and those twelve result units in 30 authored coordinates. Its
deterministic Decimal MDS reports distances, spectrum, stress and axis
ambiguity without creating theorem relations.

The scholarly manuscript version has reserved DOI
`10.5281/zenodo.23220027` under concept `10.5281/zenodo.19699233`. The automatic
GitHub software archive belongs to the separate concept
`10.5281/zenodo.23196891`. Release identity checks distinguish these three
roles while retaining the established package concept URL and historical
custody validator. Hosted Python acceptance retains per-case JUnit evidence
and coverage for review of actual passes, failures and skips. The four
explanatory numerical grids use explicit Decimal arithmetic and bounded
series with disclosed display serialization, so macOS/Linux elementary
function differences cannot change generated artifacts. Generic diagnostic
inputs, arithmetic thresholds and exact-byte freshness remain unchanged.

Hosted Chrome startup (CUR-01) passed all eight required cases, including
both real Chrome tests without skips, in the independently reviewed
[exact-source PR run](https://github.com/ActiveInferenceInstitute/fep_formal/actions/runs/37682721329)
for head `996ca58bb3ea128b8bdb77b13df329896852c482`. The actual tested checkout
`73eaf8bffddc4a35040d647003a775a239ebdc41` and that head share the complete tree
`8595c6070ad54c7eb662a8f38831dd720ecd87fb`. Python recorded 2,791 passed,
20 optional skips, zero failures/errors and 91.56% combined coverage across
all 2,811 selected cases. The parallel component passed the unchanged 89%
coverage floor at 91.01%; the isolated two-case Chrome component ran once
and appended coverage. Existing absent/present xdist controls and
failure-time diagnostic controls passed. Startup deadlines, test bodies and
retry policy remain unchanged. Earlier failures and their unresolved causes
remain historical. This PR acceptance is separate from the exact-main
release gate, fresh production capture, CUR-15 and other governed lanes.

Publication CI now acquires the pinned render template under the existing
ignored `output/` directory and checks unfiltered Git status before catalogue
projection and manuscript hydration. A real Git fixture demonstrated that
the former untracked root-level template made the otherwise unchanged source
stamp dirty; relocating the dependency preserves a clean stamp. The actual
PR render retained its dirty cover and remains historical. Source stamping,
template custody and all nine render checks retain their original contracts.

The original local candidate, before integration with newer GitHub main,
completed a coordinated source-owner refresh from version 24 to 25: five methods modules, four generated package YAML
resources and the authored positioning policy join the explicit owner roster.
Fresh native verification passed all 168 canonical bodies without warnings,
errors or `sorry`; the original receipt independently validates against its reviewed source. Current methods exports contain 17 products and thirteen
SVGs, including three additional panels for theorem contracts and cross-corpus
coordinates. The focused mathematical tests passed 112 cases. Isolated
installed-wheel API and CLI checks passed on local macOS Python 3.10.20,
3.11.15, 3.12.13, 3.13.16 and 3.14.4; all five produced the same MDS projection
hash. That candidate publication render accepted a 385-page PDF with a version-2
receipt, 1,315 numbered equation environments and independent page review.
Supplement A has twelve cited figures, six captioned tables and 55 numbered
equations. The complete non-serial Python suite passed 2,707 tests with nine
skips in 777.82 seconds and 91.50% coverage. The first full Python run failed with 78
failures, 2,626 passes and nine skips; obsolete fixture schemas, metadata and
import expectations were repaired and passed focused controls. The original
80-case distribution matrix and security assertions remain, with shared
render fixtures migrated to receipt version 2. The final wheel's 193 package
resources match the checkout, and the source archive's 338 regular members
passed exact source and metadata checks. Installation of that specific wheel
on local Python 3.14.4 passed all 17 API/CLI exports, nonmutating checks and the
reference MDS digest. Prior accepted artifacts remain historical. Hosted
matrix results remain separate.
[The validation record](specs/openai-math-methods/VALIDATION.md)
retains exact evidence boundaries and superseded attempts.
Further source-owner changes require a new coordinated evidence refresh.
Historical receipts keep their original bytes and scope. The frozen H2.7-R0
validator remains unchanged; its test-only release-lineage adapter explicitly
recognizes the 1.6.0 metadata token and still checks every other bound byte.
H3 primary seeds, empirical acceptance, Q7 generated-runner execution and
Hermes/OpenGauss execution remain separate research lanes. Publication requires fresh integrated-source validation and the exact-commit
hosted release gate. The scholarly and software Zenodo concept DOI histories
are maintained separately in citation metadata and release guidance.

## 1.5.0 — 2026-10-06 — 168-topic catalogue, finite information program and streamlined release gate

First published release since `v1.3.0` (the `1.4.0` candidate prepared on
2026-10-02 was never tagged; its content ships here). The catalogue grows from
159 to 168 canonical topics across 22 families (waves 3 and 4), with finite
information identity/coarsening, relative-support information and genuine
finite rate–distortion results, the Q7 source-pair acceptance, publication
capture with seven deadline-bounded evidence stages, render custody, and
cooperative process supervision. Citation metadata describes 168 canonical
topic bodies and separates compiled statements from semantic adequacy and
empirical validity. Lean/Mathlib stays at the v4.34.1 pair.

### Streamlined release gate (2026-10-06)

A versioned release now requires exactly: one version and date across every
version-bearing file, a dated `CHANGELOG.md` section, a clean `main` equal to
`origin/main`, and a successful hosted `ci.yml` run on that exact commit
(Python, distribution matrix, Lean and render jobs). `docs/release_check.py`
checks all of it and extracts these notes; [docs/release.md](docs/release.md)
is the procedure. Research and evidence lanes — the frozen H3 study, full
seven-stage capture and archive parity, the installed-wheel runtime matrix,
Q7 runner execution, provider (Hermes/OpenGauss) runs and the nine-criterion
audit — are tracked in `TODO.md` and reported in release notes, but no longer
block a release. No scientific or acceptance claim is upgraded by this change:
H3 primary seeds remain unopened and generated-runner execution unverified.

The hash-bound H2.7-R0 custody record pins the root release token to its
recorded `1.3.0 → 1.4.0` transition. Its validator and readiness tests stay
byte-identical; a test fixture validates a copy of the custody inputs with the
approved `1.5.0` token mapped back to `1.4.0`, so every other bound byte must
still match and any other version or duplicate root still fails.

The CI render job fetches the pinned GNU FreeSerif archive from
`ftp.gnu.org` or two identical mirrors and accepts only its SHA-256, after an
unreachable `ftp.gnu.org` failed the render job.

### Package, browser and process-supervision repairs (2026-10-06)

Browser interaction validation now uses the canonical 118 theorem pairings.
The mobile dashboard fits the unchanged two-viewport height limit on Linux as
well as macOS: tighter summary padding, a smaller mobile title and side-by-side
family/status filters take the 390×844 document from 1,705 px to 1,538 px on
macOS. Hosted Linux Chrome had measured 1,727 px against the 1,688 px limit, so
the earlier padding-only fix failed there. Summary touch targets stay at
63 px. Worker-level controls protect Chrome and Lean grouping under
pytest-xdist. Historical browser artifacts are retained until fresh capture.

Synthetic custody fixtures execute byte-checked historical validator source in
an isolated module. The current validator continues to reject fabricated
historical evidence. Nine supplemental controls passed, including concurrent
real PDF and provenance reproducibility; the installed 80-case matrix remains
unchanged. These local results establish neither native nor release acceptance.

Cooperative process supervision now holds a leased caller's result until owned
descendant cleanup settles within the original shared cleanup deadline. A
child's handled timeout no longer fails its ancestor, guard-wait faults still
publish final cleanup state, and only a command whose guard had not reported is
treated as cleanly cancelled by its ancestor, so an undelivered terminal
response remains an obligation regardless of release order. Remote requests
skip an empty frame remainder that raised EPIPE against a rejecting peer.

CUR-02 and CUR-04 leave the open-only backlog after their bounded acceptance:
the original matrix still collects 80 cases, exactly nine separate additions
pass, formatted source has fresh independent review, and reconciled guidance
passes strict links, Markdown hygiene and cross-reference audits. Historical
receipts and substantive PR44/45 remain preserved. The backlog retains 30 open
items; package, current native, hosted and scientific gates remain separate.

Publication capture now refreshes the paired manuscript projections and test
census only after strict native acceptance, renders those final values, then
runs Python acceptance against the accepted render. The seven evidence stages
retain their deadlines and independent validators. Generated cache ownership
and the citation, configured image, manuscript and font/receipt input guards
are explicit; missing projection preparation fails before tools start.

CI render custody binds the checkout to the declared template revision and
records its exact uninitialized submodule entry separately from tracked blobs.
Only the pinned path and commit in a canonical empty directory are accepted;
unknown entries, initialization, aliases, population and metadata drift are
rejected before evidence can be retained. Git does not enter submodule stores.

The canonical backlog contains open work only. The
[upcoming scope](docs/design/fep-research-program/next-improvements.md) defines
minor, medium and major improvements for package and formal work with explicit
dependency, acceptance and failure boundaries.

### Retained Q7 source-pair acceptance (2026-10-05)

The independently reviewed [current Q7 observation](specs/comprehensive-science-improvement/evidence/public-q7-current-source-20261005-r1/summary.json)
records all twelve stages and four closing checks passing under the original
limits. The actual root terminal closed exit 0 in 1,199.3769 seconds, and its
separate native receipt was claim-ready for its then-current 291-input roster,
selected isolated source pair and twelve static coefficient theorem reports.
All 124 pure cases, including twelve inventory controls, passed without skips.
Five fresh CPython parser/serializer probes returned the same 56,968-byte
canonical digest with all semantic/schema controls passing. These probes are
separate from native proof and generated-runner execution. Runner execution remains
unverified; Q5/Q6 observations and all failed/historical receipts keep their
original scope and bytes. Active GNN work remains untouched. Subsequent
browser-capture and dashboard owner changes make this observation historical;
a reviewed successor must establish currency for the new source pair.

After current-guidance read-only closure, `FEP-Q7-CURRENT` leaves the open-only
backlog. The seven-stage package capture, two identical independently validated
archives, local installed-wheel matrix, final-SHA hosted acceptance and complete
frozen H3 chain remain open. The 1.4.0 candidate remains unreleased.

### Render deadlines, process ownership and current guidance (2026-10-05)

Renderer preparation, execution, normalization, artifact capture and cleanup
now share one monotonic deadline. Finite timeout validation and bounded regular
file capture reject malformed budgets, aliases and nonregular producer output.
Cooperative subprocess leases use distinct capabilities and explicit ownership
trees; closing a nested lease revokes and terminates its descendants while
preserving its caller and sibling groups. CI custody checks bind the physical
executable mode and descriptor-relative empty gitlink entry to the Git record.
Fresh independent infrastructure review approved these existing-owner changes.

Actual supervised local validation passed all 413 cases across the release
bundle, subprocess watchdog and distribution modules without skips on CPython
3.14.4. Mypy passed. The earlier two nested-ownership failures and subsequent
lint findings remain retained as failed attempts; the tests were preserved and
the ownership defect was repaired. Ruff lint/format, strict links, Markdown
hygiene, cross-references, lock and dependency compatibility checks passed.
These focused results do not establish
whole-suite, native, provider, package-bundle or scientific acceptance.

Maintained navigation now identifies current source and historical evidence
separately, removes obsolete planning references and completed checklists, and
uses the canonical open-only backlog. The active-guidance cleanup leaves that
backlog after strict link, Markdown and cross-reference checks. Minor, medium
and major follow-on scopes retain their dependencies and measurable probes.
The successful hosted checkpoint at `c99e933` remains evidence for that source
epoch; later source changes require fresh same-SHA hosted acceptance.

The local wheel matrix retains its 15 GiB prerequisite before launch and every
cell. Current Q7/native capture, production capture, two independently accepted
identical archives and the frozen H3 export/review/outcome/reproduction chain
remain open. The later incomplete Q7 capture supplies no accepted prefix.
Licensed empirical data remain governed by the recorded no-go. Candidate
`1.4.0` remains unreleased and retains its 2026-10-02 authored snapshot date.

### Output/configuration repairs and reopened currency (2026-10-05)

The published `main` checkpoint
[fa3c88e](https://github.com/ActiveInferenceInstitute/fep_formal/commit/fa3c88e)
has a successful
[same-SHA hosted run](https://github.com/ActiveInferenceInstitute/fep_formal/actions/runs/37150440750):
all 15 distribution cells and the Python, Lean and render jobs passed.
Nonserial Python passed 2,371 tests with 15 policy skips in 829.74 seconds and
91.28% coverage on Linux CPython 3.14.8. Local validation uses the separate
CPython 3.14.4 environment.

Four existing owners now resolve selected output-root precedence,
checks of that output location, empty validation filters, read-only canonical
Hermes credential validation, and removal of a duplicate appendix writer.
The local CPython 3.14.4 focused run passed 298 cases with one explicit
live-provider skip. After correcting the valid-area intersection test,
the whole pipeline module passed all 37 cases without skips. Mypy, Ruff lint
and formatting, strict links/hygiene/xrefs, lock and environment checks passed.
Fresh independent infrastructure review approved the final source. Failed
attempts remain retained; these focused results are not full-suite, native,
provider or release acceptance.
Native-owner changes reopen the 291-input native and Q7 source-pair gates;
`FEP-Q7-CURRENT` returns to the open-only backlog. The old accepted Q7 captures,
failed attempts and `fa3c88e` CI results retain their source epochs without
receipt rewriting.

The local installed-wheel 15 GiB prerequisite remains unmet. Production capture,
two independently accepted identical package archives, once-only frozen H3
primary execution, claim review and study reproduction remain open. The empirical
branch remains governed no-go without licensed data. Candidate `v1.4.0` is
unreleased and retains its canonical authored date of 2026-10-02.

### Candidate publication and custody fixture repair (2026-10-03)

Published the reviewed candidate source to `main` at
[9aaa30e](https://github.com/ActiveInferenceInstitute/fep_formal/commit/9aaa30e94d9e31082665746dfb8715177ec84c8b)
with exact remote parity. All 15 hosted distribution cells passed. The wider
Python job's failed custody/date checks remain recorded at that source epoch.

Disposable census fixtures now rebind all predecessor maps before testing
deliberate drift. Refresh composition tests use a fixture-root-scoped adapter
that validates rebased bindings and reports native execution as `not_executed`;
the real H2/H3 validators and historical receipts retain their exact bytes.
Malformed, missing, misbound and incorrectly typed inputs still reject.
All 224 cases across the four affected modules pass without skips; the release
metadata regression passes separately. Citation and sidecar dates agree with
the canonical authored candidate date. Full production and H3 acceptance and
the v1.4.0 release remain open.

### Fresh Q7 source-pair closure (2026-10-02)

The [fresh Q7 capture](specs/comprehensive-science-improvement/evidence/public-q7-final-source-20261002-r1/summary.json)
passes all 12 newly executed stages and four closing checks in 1,249.5858
seconds under the unchanged 7,200-second acceptance bound. All 124 pure controls
pass without skips; five actual CPython runtimes produce the same 56,968
canonical scaffold bytes. The new native receipt has SHA-256
`5630eef0b58185dfd359f627453e386174d25157ddcf935c928930c2d8eef7f0`
and is independently validated as native-claim-ready for its exact checked
statements and source pair. Runner execution remains unverified. No historical
accepted prefix or native receipt is promoted, and active GNN work is preserved.

`FEP-Q7-CURRENT` leaves the open-only backlog. The former Q7 README heading is
explicitly historical; its exact capture-time preimage remains retained. These
postcapture guidance changes do not alter the 191 FEP or 291 native inputs.
Catalogue-native, full package/hosted acceptance, H3 outcomes, provider evidence
and the v1.4.0 release remain separate pending gates.

### Main publication and hosted follow-up (2026-10-02)

Published reviewed improvements to `main` at
[409ee71](https://github.com/ActiveInferenceInstitute/fep_formal/commit/409ee71f82b3353303e6306e87c1b1fedc949088),
with exact local/direct-remote parity. Complete guarded Python acceptance
passed 2,308 tests and 90.65% coverage at that source epoch; all 25 declared
static checks and strict real-template render preparation passed separately.

The [exact-SHA hosted run](https://github.com/ActiveInferenceInstitute/fep_formal/actions/runs/37035715408)
finished with five Windows matrix failures, one Python runtime-fixture failure
and two H2 custody failures. All ten Ubuntu/macOS matrix cells passed. The
failed Lean job produced no native or accepted-render artifact. Follow-up
repairs and active guidance changes reopen dependent source-currency gates;
prior accepted observations retain their recorded epochs. Historical receipts,
failed attempts, frozen scientific protocol and active GNN work are preserved.
The open-only [remaining acceptance](specs/comprehensive-science-improvement/NEXT.md)
records the full original scope and execution order.

### Q7 portability acceptance (2026-10-02)

The [post-guidance observation](specs/comprehensive-science-improvement/evidence/public-q7-current-doc-20261002-r1/summary.json)
passes live bridge status, static generation and the exact new native receipt's
read-only validation after independent document review, with stable custody.
This closes `FEP-SCAFFOLD-PORTABILITY`. The accepted native JSON stays unchanged;
Q5/Q6 remain historical, and static parity does not imply runner execution.


### Isolated Q7 evidence and active guidance refresh (2026-10-02)

The [public Q7 observation](specs/comprehensive-science-improvement/evidence/public-q7-closure-20261002-r1/summary.json)
records isolated recapture r3 accepted in 644.5096 seconds at actual receipt
SHA-256
`8c7c8d89023eb9784405143c1750b4b7ddd4ff1453dbbd089e9d660633b912ad`.
Seven actual accepted r2 substages were freshly revalidated; their parent
attempt remains failed. R3 actually executes stages 8–12 and passes all 124 pure
controls without skips. The independently isolated GNN Git checkout binds all
703 owners to `536d949829f6aed11dc540e5c5dec77578b25016`, with a private copied
runtime and read-only shared dependency base. Active GNN work/output is preserved.

Five actual CPython 3.10.20, 3.11.15, 3.12.13, 3.13.15 and 3.14.4 runtimes
produce 56,968 identical scaffold bytes at SHA-256
`b34a350a0c66bd611c19cd87e2343592c6ee7d15ed2fd6e422b1f891597febec`,
with all 11 controls per runtime. Evidence validation remains CPython 3.14.
The exact [new native receipt copy](specs/comprehensive-science-improvement/evidence/q7-accepted-native-retention-20261002-r1/native-receipt.json)
has SHA-256 `b0ecf640fffa06f019d67c74a2d02e22715120165a98d218d61f49f98366bc3b`,
is native-claim-ready and leaves runtime execution unverified.
Postcapture closure r2 accepts seven actual stages in 1,648.1618 seconds at
actual receipt SHA-256
`df7787a925bf1011a9bd09a8bcc5ae20240792ea0b4ca9bc435eb5204225ba59`.
All three real positive-axiom/wrong-F/wrong-Q native controls pass; the actual
outer process exits 0 with transport accepted. Failed attempts and the original
Q5/Q6/Q7 JSON receipts remain unchanged. Q5/Q6 observations remain historical
after W2 re-pinning; this Q7 result does not refresh them. Full operator-custody
records remain local; the public summary records observations, while the
separately validated official native receipt supplies the native claim.

Fourteen maintained Markdown files now distinguish baseline hosted evidence,
current native checkpoints and remaining acceptance. Their exact prior bytes,
second-read verification and manifest are retained in
`specs/comprehensive-science-improvement/evidence/active-guidance-history-20261002-r3/`.
Only README and REPORT change within the Q7 artifact-document map; this is not
a claim that the repository has only two changed files. Independent review and
three fresh read-only Q7 checks after this edit remain pending, so the
portability row stays open.

Wheel r7 remains historical after two guarded Q7 inputs changed and before this
guidance refresh. Its five cells each contain one actual installed target-runtime
case and 32 CPython 3.14 harness cases, 165 passes total. Wheel r8, hosted 15-cell
acceptance, canonical Python r2, render preparation r3, production capture r2,
two accepted identical archives and frozen H3 primary execution remain unrun.
The prior 2,303-pass, 12-skip, 90.66% Python run still fails its wider guard;
the private orchestrator repair has 11 focused passes. A projected 2,318-test
total is arithmetic only. Provider, release and H3/FORM-4 gates remain open.

### Programmatic test isolation and current evidence (2026-10-01)

Programmatic catalogue tests now use the same private canonical project fixture
as direct pipeline tests. Redirecting output alone still allowed generated
manuscript source files to be replaced in the live checkout. The default-root
contract remains explicit, private projections are checked, and every test
brackets the live manuscript's bytes and metadata. All 11 focused controls pass.
The preceding canonical run's 2,303 passes and 90.66% coverage remain a rejected
wider-guard attempt; identical bytes do not erase observed file replacement.

Native r3 verifies all 168 topics without warnings or `sorry`; strict real
template render preparation r2 and five local installed-wheel runtime probes
pass at their recorded source scopes. H3 export r2 and three independent
proof-role reviews pass, with no scientific draws executed. Production capture,
complete guarded Python acceptance, hosted evidence and H3 outcomes remain open.
Completed historical delivery checklists were removed from the active ISA;
their exact prior text, scientific records and repository history are retained.
Active GNN registry work is preserved; isolated Q7 capture requires separate
runtime and root custody.

### Render metadata ownership (2026-10-01)

The actual template render produced legitimate `config.yaml`, `preamble.md`
and `references.bib` copies that strict publication incorrectly rejected as
unexpected. Hydration now stages the exact raw metadata roster, capture declares
those outputs, and release archives require all three payloads with their own
evidence class. Missing, altered and linked copies still reject; chapter counts,
variable substitution and unknown-member rejection retain their contracts.
The [focused acceptance](specs/comprehensive-science-improvement/evidence/render-metadata-repair-20261001-r1/receipt.json)
records 247 passing nonserial rendering/release tests, whole-tree type/style
checks and an unchanged 293-file source/test bracket. The original production
validation failure is retained. Native, installed-wheel and production evidence
must bind the resulting source epoch before current acceptance is claimed.

### Finite information and rate–distortion acceptance (2026-10-01)

FORM-1, FORM-2 and FORM-3 close with fresh independent
[semantic review](specs/comprehensive-science-improvement/evidence/form-1-3-semantic-review-20261001-r2.json),
38 passing current native consumer/source tests, a warning-free whole aggregate
build and a live-validating 1,596-declaration axiom audit. The
[native controls](specs/comprehensive-science-improvement/evidence/form-1-3-native-controls-20261001-r1/receipt.json)
and [aggregate/audit packet](specs/comprehensive-science-improvement/evidence/form-1-3-aggregate-audit-20261001-r1/receipt.json)
retain commands, compiler output and unchanged source brackets. The failed
review/control attempts remain history.

Deterministic identity and complete coarsening now have actual finite KL
witnesses. Relative-support finite/native KL and mutual information identities
retain shared-zero atoms, sparse observation garbling and the singular native
infinity boundary. The asymmetric informative joint has positive information;
the independent asymmetric product has exactly zero information.
Finite fixed-source rate–distortion feasibility supplies a compact attained
minimum and an infimum-derived dual lower bound, with zero multiplier, negative
budget, informative quarter-budget, nonunique half-budget and unique zero-budget
controls. The original primary theorem and structural-proxy disposition remain
unchanged; general strong duality, dual attainment, an interior closed form and
general optimizer uniqueness are excluded.

The historical released-120 body and maturity digests remain unchanged. The
[reviewed-delta regression](specs/comprehensive-science-improvement/evidence/catalogue-155-regression-20261001-r1/summary.json)
reverses only the exact approved additions before checking both old digests;
11 tests pass, including seven mutation refusals. Whole Python, package/H3
synthetic, hosted and publication acceptance remain open.

### Scientific improvement checkpoints (2026-09-30)

PKG-1 closes: static status/readiness now rejects unavailable or changed inputs,
captures no checkout stamp through Git, and never promotes missing runtime
evidence. The independently reviewed status module passes all 26 focused cases
in the current checkout, including reachable comparisons, input mutation and
process/write sentinels. Strict publication validators remain separate.

Fresh H2 acceptance binds 329 passing mandatory cases, unchanged native inputs
and three actual source-bound reviews at terminal SHA-256
`2d72e6b7205b92a625106e2830c2a01200682ffb3af036dd48118eb88f9067be`.
The prior terminal bytes remain immutable history. Continuous G0 passed and
H3.0 was frozen before implementation at protocol SHA-256
`50b3575316fb272dc7bf209f50a21330fc5ea0764da9399e20aedeb0b2302c93`,
with two independent AI reviews. New proof, synthetic and publication acceptance
remain open; the empirical branch is governed no-go without licensed data.

The automatic Gauss capability check now uses an isolated local version probe
with dotenv and updates disabled, preserving required/advisory semantics.
Independent process/account-home/real-dotenv controls pass, and the isolated
upstream CLI reports v0.2.2. The requested free OpenRouter model returned HTTP
404; the attempted full 168-topic path rejected all topics and produced no
successful report. No paid fallback was enabled.

`FEP-LEGACY-TRANSPORT` closes after 155 current transport/status controls pass,
with one explicitly opt-in live Gauss test skipped. The earlier failing run is
preserved. A stdlib-only isolated guard and bounded startup fixtures retain
call-relative product deadlines, real descendant readiness, raw timeout bytes
and cleanup boundaries; fresh independent review covers the final helper.
The [local acceptance observation](specs/comprehensive-science-improvement/evidence/transport-acceptance-20260930.json)
retains the exact transcript and post-run source map. This establishes local
transport behavior; provider, native and publication evidence remain separate.

### Main status and open-backlog reconciliation (2026-09-30)

The [dated review](SCOPE-2026-09-30.md) checks `main`/remote parity at
`cd4a84c`, reconciles the 168-topic/22-family source with the tagged 1.3.0
cut and latest published GitHub release 1.2.0, and scopes minor, medium,
and major package/formalization improvements. Current overview documents
now distinguish the recorded H3 continuous selection and feasibility spike
from independent acceptance and H3.0 protocol freezing.

Removed `FEP-H27-RESEAL` from the open-only backlog: live
`validate_terminal_acceptance(Path('.'))` passes at receipt SHA-256
`8e20abbd4f5d63e09398014a0c64bee46ee6b42697eb24d16a488ede74e65c87`
(328 mandatory cases, 208 source hashes, three reviews). The 40 focused
H2/H3 custody/preregistration tests pass. Completed-history prose and dated
clearing logs were removed from `TODO.md`; four genuine residual rows remain,
with `FEP-FULL-CURRENT` replacing the stale 155-topic task name.

Same-commit CI native and axiom-audit artifacts were independently validated
against the live source (168/168 topics at v4.34.1, zero warnings or `sorry`,
1,411 audited declarations). Older ignored local receipts were preserved.
Local cache incompatibility and manuscript/render/bridge freshness remain
explicit residuals; no new full native sweep, provider run, or publication
is claimed by this review.

### Wave-4 catalogue wiring: 168 topics / 22 families (2026-09-28)

The catalogue grows 165 → 168 topics (families unchanged at 22) with the
wave-4 formalizations. fep-166 (Uniqueness of the Law-Weighted
Reversible/Circulation Split, area ActiveInference) joins the
`standalone-efe-formalizations` family through a new canonical
`FEP.LawWeightedSplit` module whose 7 public theorems are aliased into the
body: competing-pair uniqueness of the Helmholtz–Ao split, the reversible
boundary in uniqueness form, and the t-0060 two-state oracle datum with
nonzero forward circulation 1/2 and strictly negative reverse entry -1/4.
fep-167 (Frobenius Least-Squares Projection of the Symmetrizer) and fep-168
(Quantitative Control of the Uncancelled Divergence Remainder) extend
`geometric-mechanics-notation` (area Thermodynamics); the
`FEP.GeometricMechanics` module grows to 37 qualified declarations with the
exact Frobenius Pythagoras/minimality/uniqueness layer and the squared
Cauchy–Schwarz remainder budget with its equality witness on aligned data.
Three new FEPComposed bridges pair the new topics with their nearest
endpoints (fep-166→fep-160, fep-167→fep-162, fep-168→fep-163; seven bridges
total in the two geometric-mechanics composition files), and both extended
numerical witnesses grow typed checks and theorem mirrors
(`boltzmann-efe-affinity-gap` 18 mirrors / 14 checks,
`geometric-solenoidal-drop` 17 mirrors / 16 checks; 17 witnesses total).
The release seal moves to 168 topics / 22 families / 5 areas / 17 witnesses /
146 relations / 50 capabilities, and the third-expansion manuscript shape is
sealed at {standalone-efe-formalizations: 6, geometric-mechanics-notation: 7}
with the per-family size pin replacing the uniform-size singleton assertion.
Native capture and render re-acceptance ride the coordinator's remaining
phases and are pending, not part of this wiring.

### Wave-3 catalogue wiring: 165 topics / 22 families (2026-09-27)

The catalogue grows 159 → 165 topics and 21 → 22 families with the wave-3
formalizations. fep-160 (Helmholtz–Ao Decomposition of Nonequilibrium Steady
Currents, area ActiveInference) joins the `standalone-efe-formalizations`
family; a new `geometric-mechanics-notation` family (area Thermodynamics)
carries fep-161..165: skew trace/quadratic cancellation, the discrete-Hessian
symmetrization (finite Clairaut), the three-term solenoidal expansion with its
conditional drops, the graph-plane divergence decomposition, and the necessity
witness refuting the unconditional solenoidal drop. The `FEP.HelmholtzAoNess`
module contributes 25 public declarations (13 main theorems aliased into the
body); the `FEP.GeometricMechanics` module contributes 22 declarations of
which 19 public theorems are aliased (including the symmetrize/Clairaut
family — the pushed module commit message under-counted and is not the
inventory). Two new FEPComposed composition files carry 6 novelty bridges
(fep-160→fep-025, fep-161→fep-160, fep-162→fep-161, fep-163/164/165→fep-025),
a `cap-geometric-mechanics-solenoidal` capability node lands with 8 evidence
entries, and the `geometric-solenoidal-drop` numerical witness gives the new
family its typed non-proof evidence (17 witnesses total). The release seal
moves to 165 topics / 22 families / 5 areas / 17 witnesses / 143 relations /
50 capabilities. The 143/50 relation and capability planes correct a
pre-existing seal drift: a0f4ed3 added `cap-standalone-efe-theorems` and four
formal_pairing edges without bumping `RELEASE_SEAL` (live counts were 49/137
against a 48/133 seal at a64ca6c). Manuscript 04d's NESS disclaimers are
retired against the now-compiled statements (ansatz-universality, trace
quadratic and Hessian cancellations, conditional solenoidal drop, and the
2-node failing witness), keeping the state-dependent-diffusion and PDE/SDE
boundaries. The roster-v23 source-owner coordinated refresh, native capture,
render re-acceptance, and pin-cycle #32 re-seal ride the coordinator's
remaining phases and are pending, not part of this wiring.

### Coordinated evidence refresh: SOURCE_OWNER_ROSTER v24 (2026-09-28)

`OWNER_MANIFEST_VERSION` 23 → 24 covering the wave-4 fold chore's custody
cascade: the new `law_weighted_split` canonical formal module
(`FEP.LawWeightedSplit`, 7 public theorems) joins the native roster through
the formal-modules plane with its byte-identical `lean/FepSketches/` mirror,
the wave-4 wiring delta touches the reviewed owner files it reuses (the two
family body modules, the numerical-witness extensions, the release-seal and
third-expansion surfaces), and the H2.7 evidence-custody chain
(acceptance → matrix → R0 prior/successor custody receipts → 05d/05b/06a →
terminal packet → H3 spike lockstep) is re-bound over that delta with the
strip model in `tests/_support/h2_r0_custody.py` gaining this wave's
added-module group so the reconstruction still hashes to the sealed R0
manifest digest. Prerequisite for `fep-lean verify` claim-readiness at any
tip containing the wave-4 catalogue (the native capture fails the roster
pre-gate otherwise); the native capture, render re-acceptance, and pin-cycle #33
re-seal follow.

### GEO-INFER notation slice growth to 17 rows (2026-09-28)

- Grew `specs/geo-infer-notation-bridge/data/notation-map.yaml` from 13 to 17
  notation-level rows: fep-004 (Fisher metric quadratic form,
  `information_metric`), fep-018 (Fisher-Rao distance between parameter
  points, `geodesic_distance`), fep-038 (Fisher information as log-likelihood
  curvature, `fisher_information_matrix`), and fep-158 (Bayes-odds evidence
  weight between models, `ModelSelection`), each anchored on a lane-verified
  GEO-INFER-MATH anchor — the first cross-module anchors, ratified this
  session — and validated by `check_geo_notation_bridge.py --check`; no proof
  or verification claim is added.

### GEO-INFER notation slice growth (2026-09-28)

- Grew `specs/geo-infer-notation-bridge/data/notation-map.yaml` from 10 to 13
  notation-level rows: fep-025 (row-normalized transition kernel,
  `MarkovDecisionProcess`), fep-156 (Boltzmann control posterior,
  `PolicySelector`), and fep-157 (perception update as forward filter,
  `MarkovDecisionProcess`), each anchored on an already-verified GEO-INFER-ACT
  anchor and validated by `check_geo_notation_bridge.py --check`; no proof or
  verification claim is added.

### Coordinated evidence refresh: SOURCE_OWNER_ROSTER v23 (2026-09-27)

`OWNER_MANIFEST_VERSION` 22 → 23 covering the wave-3 fold chore's custody
cascade: the new `geometric_mechanics` catalogue body joins the roster via
`body_source_relative_paths()` and the H2.7 evidence-custody chain
(acceptance → matrix → R0 prior/successor custody receipts → 05d/05b/06a →
terminal packet → H3 spike lockstep) was re-bound over the wave-3 wiring
delta (two foundation modules + two bridge compositions in
`FORMAL_MODULES`, their byte-identical `lean/FepSketches/` mirrors, and the
expanded release seal). The strip model in `tests/_support/h2_r0_custody.py`
gains the wave-4 group constants so the reconstruction still hashes to the
sealed R0 manifest digest. Prerequisite for `fep-lean verify`
claim-readiness at any tip containing the wave-3 catalogue (the native
capture fails the roster pre-gate otherwise); the native capture and the
render re-acceptance follow before the pin-cycle #32 re-seal.

## 1.3.0 — 2026-09-26 — toolchain co-bump and wave-2 delivery

### Joint Mathlib/Lean v4.34.1 co-bump and release promotion (2026-09-26)

User-approved G20 co-bump: `lean/lean-toolchain` and `lean/lakefile.lean`
moved to v4.34.1, `lean/lake-manifest.json` re-resolved at Mathlib
`d13f23b7`; `lake build FepSketches` green (8990 jobs, zero errors and
warnings) with the catalogue-compile spot-check, mypy, ruff, and
pin-audit gates green. Wave-2 delivery (lean-5 archive under `done/`,
owner roster v22, 159-topic wave-3 catalogue, cycles #27-#29 custody
seals) ships with this release; the coordinated native capture and the
pin cycle #31 re-seal follow before the `v1.3.0` tag.

### Coordinated evidence refresh: SOURCE_OWNER_ROSTER v21 (2026-09-24)

`OWNER_MANIFEST_VERSION` 20 → 21 and six `src/fep_lean/custody/*` modules
(`__init__`, `apply`, `census`, `cli`, `model`, `verify`) added to
`SOURCE_OWNER_ROSTER`, landing the W19 custody layer as a coordinated
evidence refresh per AGENTS.md. Prerequisite for `fep-lean verify`
claim-readiness at any tip containing the custody package (the native
capture fails post-compile otherwise); the next bridge pin cycle re-seals
the roster-drifted source binding.


### Comprehensive improvement wave (2026-09-20/21) — SCOPE-2026-09-20

A 7-lane read-only scoping swarm (Ledger, CI, SRC, DOCS, TESTS, ARTIFACTS,
LEAN) over `1c3c627` produced `SCOPE-2026-09-20.md` (37 items). Execution ran
as ten parallel project threads (t-0009..t-0018), after the parallel t-0005/6/7
waves (docs+ledger hygiene, CI hardening, tests suite quality — landed
earlier the same day) were restored onto the synced tip when a reset-to-origin
dropped their merges (re-merged as `8e67751`, `ba1c582`, `2037b40`). Landed
item groups:

- **CI** (t-0009, rebased onto the restored `de62368` hardening): a
  `lean/.lake/build` cache keyed on toolchain + lakefile + manifest +
  `fep_all.lean`, and `pull_request` paths-ignore so doc-only PRs skip the
  lean/render chain.
- **Render receipt classification** (t-0010): `receipt_defects`/`_moved_sources`
  now classify generated appendices — a moved `09z` remediates with
  `fep-lean catalogue`, authored moves keep the render remediation; a missing
  generated source fails closed via a receipt defect (the digest function
  stays byte-stable, so committed custody receipts remain valid); the false
  boundary docstring corrected; `check_render_log.py` prints a degraded-mode
  WARN when `manuscript_vars.yaml` is absent; the contents-overflow scan
  covers an absent combined log when a sibling log exists; nine regressions
  in `tests/test_render_log.py`; the status-verb fixture stages the generated
  appendix; the `scripts/AGENTS.md` receipt-boundary claim corrected.
- **Render publication** (t-0011): `--require-release-stamp` pass-through
  (default off); render-lock holder-pid file, dead-holder stale-lock warning,
  and a guarded release that never masks the render exit code; tests.
- **fsutil consolidation** (t-0012): the deprecated `_sha256`/`_atomic_text`/
  `_atomic_bytes` shims removed across `browser_capture`/`evidence`/
  `release_bundle`/`rendering`/`reporter` (callsites point at `fsutil`);
  `reporter`'s inline digest → `sha256_bytes`; `release_bundle`'s
  coverage-line parse fails closed on malformed records; the divergent
  `gnn_artifact_proof.sha256_file` renamed `sha256_file_strict` (the Q5
  probe, the star-copy pin, the contract-edge attribute, and the
  regenerated `artifact_proof_manifest.json` aligned — 206 tests green on
  the proof trio).
- **Manuscript projections** (t-0013): `manuscript.py` atomic writes folded
  into `fsutil`; hand-typed structural counts tokenized — areas via the
  existing `{{total_areas}}`, expansion-family counts via new
  `manuscript_vars` projections (`expansion_families`, `expansion_family_topics`,
  second-wave boundary at `fep-121`); nine chapters updated; token-parity
  tests added.
- **check_or_write** (t-0014): one shared `--check`/write shell in
  `catalogue/generation`; six script callers plus the `cli` `_atlas`/
  `_dashboard` twins thinned; STALE wording unified (stdout); `cli`'s broad
  except narrowed.
- **Lean test adoption** (t-0015): raw `subprocess.run` lean compiles adopted
  onto the process-group-safe probes (`tests/_support/lean_runner.py` +
  the two-stance `tests/_support/lake.py`); 21 `_without_lean_comments`
  copies deduped onto `fep_lean.lean_source.lean_code_without_comments`;
  the bridge verify-document well-formedness test marked `serial_lean`; the
  conftest two-stance missing-tool policy documented.
- **Docs/config truth** (t-0016): `pin_audit` regex hardened for
  backtick-quoted Mathlib tags; the `coverage-branch.md`/`pyproject.toml`
  ProcessPoolExecutor claim corrected; the quickref bridge line gains the
  required `--gnn-root`; dead settings keys removed (`gauss.source`,
  `gauss.log_level`, `gauss.verify_lean`, `output.report_dir`) with
  README/configuration rows corrected (`gauss.default_model` kept —
  `pin_audit` cross-checks it against `hermes.model`).
- **Lean/specs** (t-0017): `lean/build.sh` runs lake from its own directory
  (root invocations previously failed); lean README/AGENTS version and
  `ELAN_HOME` refs refreshed; three bridge spec READMEs moved from "active"
  to accepted wording; the 2026-09-05 review spec moved under `specs/done/`
  (the getting-started link updated); the geo-bridge and h3-reference
  READMEs corrected.
- **Test behavior** (t-0018): the renderer-layering test made behavioral
  (monkeypatched probes replace source-text assertions); the font-coverage
  CI-conditional skip replaced with a stub-aware expectation.

Run-artifact provenance paths (GNN pipeline logs, summaries, dashboards,
archived acceptance assets, bridge receipts) and doc mentions were redacted
to neutral placeholders so committed evidence carries no authoring-machine
paths or organization names; digest evidence is unchanged and validated.

Ledger truth pass (LED-1/LED-2/LED-3): `FEP-RELEASE-NEXT` re-anchored —
v1.2.0 shipped and the native receipt already records the v4.34.0 pin
(owner_manifest_version 18, 155 topics, 0 sorry); `FEP-H27-RESEAL` was
re-recorded live — `validate_terminal_acceptance` was red at the recording
time on the native source capture (exactly the four tests-wave files:
horizon1 decision_risk / finite_reference_agent / policy_action,
native_blanket; receipt digest `d324e3d0` intact). The terminal roster was
subsequently re-captured, the W2 source roster re-sealed, the sealed H2_5d
readiness spike migrated to the then-pinned Mathlib API
(`Measure.isProbabilityMeasure_map_iff`), and the committed
render-acceptance receipt regenerated by a fresh publication render. The
serial-inclusive suite's remaining 7 failures are the R0 predecessor
chain's re-record remainder: the R0 acceptance's toolchain bindings one
bump stale at v4.33.1, the immutable R0 prior detecting the tests-wave
source drift, and the fin4 census probe's `Axis.toCtorIdx` — a second
Mathlib v4.34 rename victim after the 05d spike — owned by the same
re-issue procedure.

Repository note: the GitHub repository is now
`ActiveInferenceInstitute/fep_formal` (the former name redirects); local
URL references — README, CITATION, pyproject project URLs, the release
bundle's embedded identity, and sidecar config — were updated to the new
name. The Python package name is unchanged.

## 1.2.0 — 2026-09-17 — connected Horizon research program

### Post-release custody program and Wave 2026-09-20 landing fold (2026-09-16/21)

Commits (in order): `fde5dca1` pin cycle #11 sealing the wave-3 trees (GNN
doctor module joined the sealed roster; emit refresh + both models check
green) and `4f08f013` pin cycle #12 after the GNN doctor format commit;
manuscript commits `a0a507e`/`2d7d64b`/`17d626b`/`6b9dfab` (display-equation
numbering, extarticle 9pt typesetting, the pfr2023lean author field, and the
v4.34.0 evidence-tree acceptance-receipt refresh); release `7886e3f4`
(v1.2.0); post-release custody re-seals `e48371b0` at GNN `v3.4.0`
/ `90f40bfd2` and `1c3c627a` re-recording the Horizon-2/H3 acceptance chain
for the release bump; merge `48b8d22` completes the H2.7 terminal-packet
diagnostics re-pin (`0c22c76`: `1c3c627` regenerated `diagnostics.json`
wholesale but left its artifact ref at the pre-regeneration digest
`ad7d8b0c`; re-pinned to the live `e6ce5d7f` with a lockstep H3 spike
re-pin; immutable history preserved); `c31c5243` re-seals the source roster
at GNN `083ddaf948c9` after the post-batch GNN wave landing (#117-#125).
The Wave 2026-09-20 improvement wave ran seven read-only scout lanes and
four implementation threads (docs, CI, tests, src/custody) plus this
landing fold; method, constraints, assignments, and deferrals are recorded
in the [historical September 20 scope](https://github.com/ActiveInferenceInstitute/fep_formal/blob/cd4a84cd91d884d6952b2b2f1b0289b2bdfd36ed/SCOPE-2026-09-20.md).

### Lean/Mathlib v4.34.0 toolchain program and pin cycle #7 (2026-09-15)

Commits (in order): `ff5c712` bridge re-pin to GNN
`e983de5e5c997d413a24c8af212d0d4a2ecf61a6` sealing the post-`fa931c8`
owner content; `88ffd01` toolchain bump of Lean/Mathlib to v4.34.0 (the
newest-stable gate demanded it: `lean/lean-toolchain` v4.33.1 → v4.34.0,
lakefile + lake-manifest re-resolved at mathlib `5ed29652`) with the
155-topic FepSketches workspace migrated to the 4.34 Mathlib API, canonical
surfaces migrated and projections regenerated byte-identical,
`lake build FepSketches` at zero warnings, `fep-lean verify` at 155/155
verified with `native_claim_ready=true`, and the coordinated evidence-custody
refresh bound to the new pin; `98c6324` formalism-coverage projections
regenerated after the 4.34 migration (the CI catalogue-check step);
`1534610` ruff-format of the fixture constants in
`tests/test_reporter.py`/`tests/test_native_evidence.py` — all three merged
as PR #19 (`63aac26`); `430b725` pin cycle #7 re-seal to GNN
`e983de5e5c997d413a24c8af212d0d4a2ecf61a6` (the #19 merge's owner-content
changes invalidated the pre-bump seal; emit refresh-digests plus both-models
`emit --check` green with `--fail-on-warnings`); `24f570a` bump-proof
fixture normalization — the formalism-audit fixture now derives the Lean
version from the pinned toolchain, the same form the reporter and
native-evidence fixtures already used.

Post-entry bridge re-pins recorded here for the same program: `2b51c3d` pin
cycle #8 (GNN wave changed the sealed owner roster — framework_common.py
fold, context deletion, intelligent_analysis repoint); `1e4d634` pin cycle #9
(GNN wave-2 landed bnlearn executor + B-orientation diagnostics on the
sealed rosters; syntax-pin rebound for gnn_syntax.md); `26955f3` pin cycle #10
(ruff-format reflowed two sealed owner files: bnlearn_runner.py,
orientation.py). Each re-pin ran emit refresh + both-models
`emit --check` green with `--fail-on-warnings`.

### Docs pinning sweep and bridge re-pins #13/#14 (2026-09-14/15)

Commits (in order): `d8ca59b` canonical bridge re-pin runbook
(`docs/design/gnn-bridge/README.md` — status → pin both → emit
`--refresh-digests` → emit `--check` → PR/merge → GNN pair-pin bump LAST,
with the owner-file warning and mirror rule), the quickref bridge row, the
AGENTS.md status/topic/report verbs, the 3.14-only validator note, and
`uv sync --locked` quickstart alignment with CI; `942f836` docs pinning —
`uv sync --locked` in quickref/getting-started/development (matching CI,
README, and ISA-03) plus the two CI-enforced render acceptance gates
(`build_render_fonts.py --check`, `check_render_log.py --verify-receipt`)
added to the testing.md release-gate list; `1e398ee` (merged `8d8ef28`,
PR #13) bridge re-pin after the GNN quality/render sweep (mypy
`strict_equality` + `warn_unreachable` at 0, structural render specs, the
logging single-entry contract, SC-22 re-render + re-record), sealed at GNN
`b0865d32`; `33bc7da` (merged `dec6dce`, PR #14) bridge re-pin at the GNN
final content state (ruff-format of the two issue-#111 render files +
figures/SC-22 re-render), sealed at GNN `c2332212`. Both re-pins pass
`bridge emit --check` finite + continuous with `--fail-on-warnings`. The
GNN-side counterpart pin bump is `a4e73837a` (fep_lean source pin raised to
the PR #14 merge head).

### scope-wave2: FEP-CI-RENDER lane and evidence-currency close-out (2026-09-12)

Commits (in order): `8ffbe2a` hermetic acceptance carries exactly git + fc-list
and the real user font inventory; `2951557` Q7 scaffold records the CPython 3.14
interpreter contract with a pinned-digest test; `f942ec9`/`dc29ecf`-chained
custody re-pins bind the Q5/Q6 manifests and the bridge source pin to the
current extractor bytes; `bb35bad` collection evidence carries the canonical
marker filter and svg_raster coverage; `237fe02` bridge custody re-pin at
`bb35bad`; `ffccdc0` collection-cache schema pins reconciled to 5 (the
`bb35bad` cache-format bump intentionally invalidated old caches; the two
hermetic tests pin the schema so a bump forces a conscious test update);
`d818efb` the renderer carries the full manuscript asset roster; `f8cd645`
bridge custody re-pin at `d818efb`.

- Renderer contract (owner-visible decision): `render_manuscript` now copies
  every `MANUSCRIPT_ASSETS` destination unconditionally (roster-driven),
  failing closed when any roster source is absent. Rationale: the release
  assembler requires the full roster, chapters hyperlink the interactive
  companions through published-ref URLs by design (`d1c0530` replaced the
  404ing relative links), and the appendix promises the offline HTML
  "without requiring a network connection" — so a reference-only filter
  silently dropped the SVG/HTML companions from the release bundle. The
  referenced-only filter was the stale side of the contract.
- Hermetic acceptance (granted final run on the converged tree): 0 failed /
  0 errors; junit roster equals `manuscript_vars.tests.collected` at 1617
  (1604 passed + 13 skipped); line coverage 0.891 against the 0.89 floor;
  receipts retained under `output/` (pytest.xml, coverage.xml,
  python-acceptance.json).
- Deterministic release bundle: two `SOURCE_DATE_EPOCH=0` builds are
  byte-identical, sha256 `ceb08c1811a7aa832245cba8cb7bd56adaaa6bdff8e8e8e8ecaeab7abfb8bb38`
  (308 members), and `--check` validates the same bundle claim-ready against
  the live roster.
  (run 6 against the 32258cf tree; superseded by the later reconciliations —
  the final restoration chain's bundle is `f6ecc47136f895f01e502edd1b05e1c4c0859be8158b0e71d2759e9621ee61c2`,
  also byte-identical ×2 and `--check` claim-ready, recorded in the
  restoration-record section below)
- Evidence currency: native verification receipt regenerated on the final
  tree — 155/155 topics compile warning- and sorry-free; the formal two-arg
  `validate_native_lean_receipt(receipt, project_root=...)` reports `valid`,
  `source_bound`, and `native_claim_ready`. Bridge custody re-pinned
  (`specs/gnn-bridge-w2-source-custody/source-pin.json` at `d818efb`; both
  Q5 and Q6 freshness gates green). Formalism-audit receipt refreshed
  (complete, zero errors, no sorry-axiom). Publication plane current
  (catalogue, render-fonts, and the strict-default `render_manuscript
  --check` all green) and the browser interaction receipt re-captured with
  zero receipt errors against the live Chrome replay.
- Evidence boundary: the report receipt validates in catalogue mode
  (`valid`, `source_bound`; `claim_ready` is full-mode-only by definition —
  a catalogue-mode report must never be read as provider evidence); native
  compilation is claim-ready at 155/155 for the exact recorded digests; the
  Hermes/OpenGauss provider plane remains historical (FEP-FULL-155 owns the
  next full-mode run under its own credential and spend boundary).
- Process lesson, recorded for the ledger: acceptance runs bind their input
  snapshot, so the dependency chain is native → manuscript vars → render →
  acceptance → bundle. An acceptance run launched concurrently with the
  native re-seal completed before the native receipt landed and correctly
  failed the bundle's input-snapshot gate; the binding run is the one
  executed after the evidence plane converges. Manuscript vars were never
  reverted to satisfy a gate — the claim-ready state is the published state.
- Merge record (2026-09-12): `origin/main` (`0da46d7`) merged over merge-base
  `4bb32ec`; its delta touches the custody/spec plane only (two `gnn-input/`
  topic documents, the w1 `syntax-pin.json`, and the w2 `source-pin.json`
  re-seal) with zero `src/`/`scripts/` files, so the rostered source digest is
  unchanged and the native receipt needed no re-run. The `source-pin.json`
  conflict resolved to the wave side (`f8cd645` re-seal binds the current
  roster bytes; origin's re-seal pinned pre-wave bytes), re-verified by the
  Q5/Q6/geo freshness gates and bridge status after the merge. The owner's
  newer pending re-seal branch `origin/repin6` is intentionally not merged
  and remains on its own PR flow.
- Merge record (2026-09-12, second reconciliation): `origin/main` (`03f7cd4`,
  the owner's merged `repin6` re-seal) merged over the prior merge head. Its
  delta again touches only the custody/spec plane (the two `gnn-input/`
  projections, the w2 `source-pin.json`) with zero rostered source bytes, so
  the native receipt needed no re-run. The `source-pin.json` conflict again
  resolved to the wave re-seal: repin6 re-sealed against the origin lineage
  whose owner bytes pre-date the wave commits and is stale for this tree. The
  two `gnn-input/` documents are projections of the pinned sources, so the
  owner's hand-edited copies were superseded by re-emitting both models from
  the wave sources (`fep-lean bridge emit`, finite + continuous); bridge
  status reports every check fresh and the Q5/Q6/geo gates stay green.
- CI restoration record (2026-09-12): CI ruff round 2 formatted
  `rendering.py` (`b399d45`, byte-level formatting only — the d818efb
  contract is unchanged) and the render lane was restored to verify
  identifiers against the pinned template checkout; CI rounds 3–5 are
  workflow-only. The rostered byte shift invalidated the standing custody
  and evidence bindings, so the chain was re-run and re-bound at the
  formatted bytes: native verification recompiled 155/155 warning- and
  sorry-free (two-arg gate triple-True), bridge custody re-sealed, the
  publication plane re-rendered, and the hermetic acceptance plus the
  deterministic release bundle were re-validated under the new receipts.

- CI render lane accepted (2026-09-12): the `render` job passed end-to-end on
  GitHub CI twice (runs 34680452819 and 34681926826 — lean, python, and render
  all green; the render leg writes and validates fresh `docs/render-acceptance.json`
  plus `docs/render-fonts.json` in the same run over the pinned template ref),
  closing the FEP-CI-RENDER backlog row per its own probe.

### Wave-2 coordinated refactor and partial evidence refresh (2026-09-10)

Code (all receipt-digest-shifting by design; one coordinated refresh):

- Catalogue spine: `FEPTopicCatalogue` gained the sole validating
  construction path (roster/order/vocabulary asserted in `__init__`,
  `topics` frozen to a tuple); `from_yaml` delegates document/roster/family
  metadata validation to `schema.load_catalogue_metadata` (new
  `GENERATED_TOPIC_FIELDS` row-field set) and keeps only the
  generated-projection checks; one canonical Lean theorem-header regex
  (`LEAN_THEOREM_RE`) replaces five divergent copies.
- Verification layer: bridge custody `read_object` rejects duplicate JSON
  keys and non-finite constants; one strict-JSON loader
  (`verification/_jsonutil.load_strict_json`) replaces five hand-rolled
  parsers; `LeanVerifier` threads `lean_dir` into every subprocess
  environment and now delegates tool resolution to the shared
  `_toolchain` layer; Hermes preflight no longer mutates shared config
  budgets (per-call probe budgets instead); the theorem-witness endpoint
  dry-run found 89/125 edges failing a reviewed-primary-qualified rule —
  recorded as a relations-ledger review, not a code loosening.
- Output plane: shared `output/fsutil` primitives (atomic writes, digests);
  manuscript's pytest-collection evidence functions promoted to public
  names; a shared SVG presentation kernel serves atlas and dashboard; a
  versioned `RELEASE_SEAL` (plus individual constants) is the single
  definition site for the 155-topic release shape; the theorem-maturity
  projection is importable (`catalogue/theorem_maturity_projection.py`),
  removing the receipt validator's `runpy` execution of a script;
  release-bundle prerequisite passes one built presentation through both
  drift helpers; `render_manuscript` fails closed by default when the
  native receipt is not claim-ready (`--allow-unavailable-evidence` opts
  out); `summary.json` is written once (no hash-less crash window); the
  CDP WebSocket handshake closes the socket when `sendall` fails.
- Hygiene: `02_run_single_topic.py` requires an explicit topic id; the
  interpreter contract (packaging floor vs accepted 3.14 runtime) is
  documented in `src/fep_lean/README.md` and `docs/development.md`;
  per-user ELAN tempdir; `settings.yaml` `api_key` rejected; `.aii` test
  task runs under uv; the bare `index.md` gitignore is scoped to the root;
  Hermes API responses are bounded (8 MiB cap) and the wall-clock deadline
  now force-shuts the abandoned socket; `verify_batch` runs as a plain
  sequential loop; references.bib duplicate detection uses `Counter`;
  dead environment aliases removed; the status-pie palette asserts its
  arity.

Evidence refresh state (final chain, 2026-09-11 against 3ee3007): bridge custody re-pinned; native verification receipt valid/source-bound/claim-ready (155/155, formal two-arg call); formalism audit zero errors; publication plane current including the strict-default render check; browser acceptance clean; `fep-lean status` reads all four sections current with the top-level `native_claim_ready` flag derived from the section state (VI-7 fix). At this stamp the Python-acceptance plane was the remaining blocker (the hermetic environment could not run the tool-dependent lanes; see then-open TODO `FEP-EVIDENCE-CURRENT`) — superseded 2026-09-12: the owner authorized the hermetic-policy change (git + fc-list allowlist), and the close-out section above records the granted final acceptance run. Owner roster bumped
15 → 17 for the new rostered modules.

### Evidence-currency status verb and GEO-INFER notation slice (2026-09-08)

- Added the read-only `fep-lean status` verb: it composes existing
  fail-closed checks (catalogue projection drift, render-receipt defects,
  bridge source-pin binding, native-receipt validation) into one
  evidence-currency report whose every section carries its capability
  boundary; exit 0 means the report composed, never that evidence is
  current. The implementation lives in the rostered `cli.py` owner: report
  and native receipts bind a versioned source-owner roster, so a new
  `src/fep_lean/**` module would fail source-binding until a coordinated
  `OWNER_MANIFEST_VERSION` refresh.
- Added the `specs/geo-infer-notation-bridge/` slice: charter, the
  `data/notation-map.yaml` correspondence artifact (reviewed rows between
  fep_lean theorem proxies and the GEO-INFER-ACT implemented surface), and a
  slice-local deterministic checker; registered in the AGENTS required-check
  list and `docs/development.md`, which now also document the source-owner
  roster rule.
- Corrected five stale `scripts/check_geo_notation_bridge.py` references to
  the slice path after the checker moved under `specs/` (AGENTS required
  checks, development guide, slice README and checker docstring,
  notation-map header), and completed `docs/cli-reference.md`: the `status`
  verb, its exit-status boundary, `verify --receipt/--fail-on-warnings`, and
  the `emit --check/--refresh-digests` flags.

### Publication render remediation

- Made the published reproduction recipes reproduce. The conclusion's
  Reproducibility Statement, the `AGENTS.md` required-check list, `README.md`,
  `scripts/README.md`, `docs/SPEC.md`, `docs/testing.md`,
  `docs/development.md`, `docs/authorship-guide.md` and one block in
  `docs/cold-start-and-cleanup.md` ran
  `scripts/render_manuscript.py --check` with no generator ahead of it.
  `manuscript/manuscript_vars.yaml` and the generated appendix are
  `.gitignore`d build products, so on a fresh checkout the check exits 1 with
  "test collection cache is missing" before validating anything. Each block
  now runs `uv run fep-lean catalogue` first, and
  `unreproducible_command_blocks` fails the render path on any published shell
  block that reintroduces the gap -- it found five sites beyond the two that
  were reported. The generating form of `render_manuscript.py` does not
  qualify: with the projection absent it exits 1 the same way `--check` does.
- Restored the test extras the Reproducibility Statement's own first line
  removed. It opened `uv sync --locked`, which prunes the `dev` group, and the
  check it ends with counts the collected suite: running the published
  sequence verbatim gave "required pytest collection distribution is missing:
  pytest" and exit 1 from both `fep-lean catalogue` and
  `render_manuscript.py --check`. The statement and 3.6.6's checklist now say
  `uv sync --locked --extra dev`, and the same audit rejects a block whose
  sync starves the check that follows it.

- Replaced the primer's hand-typed "about 1-2 seconds" per verification with
  the receipt's own distribution. Nothing supported the range: the same PDF
  prints 14.952 s per result in the compilation chapter, and the cited receipt
  records a per-topic minimum of 2.381 s, a median of 8.982 s and a maximum of
  183.318 s, with 0 of 155 topics at or under 2 s. `verify.min_topic_s`,
  `verify.median_topic_s` and `verify.max_topic_s` now project that spread
  beside the existing mean, so the sentence is regenerated rather than typed.
- Published a verification command that runs. The primer printed `lake env
  lean lean/FepSketches/FepCheck_fep001.lean`, which exits 1 from every
  directory because no file of that name is ever created: `LeanVerifier` uses
  `tempfile.mkstemp(prefix=f"_verify_{topic_id}_")` and unlinks the result.
  The chapter now names the real argv, run with `lean/` as the working
  directory, and publishes `uv run fep-lean verify --topic fep-001` as the
  reproducible entry point. The same paragraph claimed `_wrap_lean_code`
  prepends imports, adds area-specific opens and wraps the body in a
  namespace; all 155 catalogue bodies already begin with `import` and declare
  their own `namespace FEP<NNN>`, so the wrapper returns every one of them
  unchanged. It also credited native mode with writing `VerifyResult` to
  SQLite; the session store belongs to full OpenGauss mode.

- Stopped printing catalogue row counts as theorem counts. Two sentences in
  the sophisticated-dynamics synthesis read "The {{areas.InfoGeometry.count}}
  Information Geometry theorems" and "The {{areas.BayesianMechanics.count}}
  Bayesian Mechanics theorems"; those tokens carry row counts, three lines
  below a heading that already said "Rows" and a sentence that already said
  "rows", so the rendered PDF contradicted itself on one page and understated
  its own proof totals, which `docs/formalism-coverage.json` sums per area
  from each row's `theorem_count`. Both sentences now say "rows", and
  `miscounted_area_labels` fails the render path on any `{{areas.*.count}}`
  token whose following noun names theorems, lemmas, declarations, proofs, or
  definitions, so the class cannot return through a third sentence.

- Typeset Lean's Unicode operator suffixes: the code face is JuliaMono, not
  FreeMono, which covers none of U+2098 U+2096 U+1D50 U+209A U+1D62 U+1D9C and
  had XeTeX drop all 162 occurrences silently -- printing the complement lemma
  `μ sᶜ = 1 - μ s` as the false `μ s = 1 - μ s`.
- Made the LaTeX pass fail closed. `scripts/check_render_log.py` rejects a
  render whose log records any `! ` error or `Missing character`, a mermaid
  diagram that shipped as verbatim source, a combined build older than its own
  manuscript sources, an uncaptioned table, or a contents number that overflows
  its number box. The shared template's own success test looks for four fatal
  markers and passes all of these.
- Gave every line break a cue. `\seqinsert` now emits a discretionary carrying
  a grey continuation arrow, so a table cell can no longer print
  `FEP.FiniteKernel.comp_assoc` as `FEP.Fini` / `teKernel.comp_assoc`; fvextra
  gains `breaknonspaceingroup`, without which `breaklines` was inert for every
  Lean listing because pandoc wraps each token in a macro.
- Widened the contents number columns. `article`'s default
  `\@dottedtocline` widths are too narrow for numbering that reaches
  `15.100.1`, so 224 contents lines printed as `15.100fep-100`.
- Captioned all 36 tables and the pipeline diagram. The combined build had 36
  `longtable`s and six captions, all six on figures, so no table carried a
  number any prose could cite; the one Mermaid diagram shipped as
  "Figure 3: Mermaid diagram", the template's placeholder.
- Carried `manuscript/config.yaml`'s subtitle and fifteen keywords into the PDF
  `/Info` dictionary, and made `scripts/render_manuscript.py` fail closed when
  the preamble copy drifts from the config (`pdf_metadata_drift`).
- Replaced the hand-maintained "Mathlib navigation hint" column with each
  row's own imports. Forty-two of its 71 cells named a module the row never
  imports -- `fep-023` advertised
  `MeasureTheory.Measure.Typeclasses.Probability` against a body that imports
  `Mathlib.MeasureTheory.Measure.MeasureSpace` -- because nothing recomputed a
  cell when a body moved an import. Every cell is now
  `{{topics.fep-NNN.imported_modules}}`, produced from the same regex and
  source as the coverage report's incidence table;
  `hand_maintained_module_cells` fails the render path on a literal typed back
  in, and `unknown_topic_import_modules` checks the relation itself against the
  pinned Mathlib.
- Stopped a catalogue theorem reading as Mathlib prior art, and made the
  allowlist that hid it self-checking. `manuscript/04b_framework_active_inference.md`
  said fep-008's proof used "`min_agrees_on_value` plus `le_antisymm`", between
  two real Mathlib names; `grep -rl min_agrees_on_value
  lean/.lake/packages/mathlib/Mathlib` matches nothing, because the name is
  this catalogue's own `fep008_min_agrees_on_value`
  (`src/fep_lean/catalogue/bodies/core_active_inference.py`) printed without its
  prefix. It evaded the reference audit only by sitting in
  `NON_CATALOGUE_IDENTIFIERS` under the comment "Mathlib declarations cited as
  prior art", which made that set's own header claim -- "Every entry is a
  reviewed exception" -- false. The prose now attributes each step to its
  owner, the entry is gone, and the set is split into three provenance groups
  that `unverified_non_catalogue_identifiers` checks against their sources: a
  Mathlib citation against the names the pinned checkout introduces (a
  declaration header, or a quoted token -- no `theorem`/`def` header carries
  `norm_num`; the tactic's name reaches the reader as the literal in
  `elab (name := normNum) "norm_num" ... : tactic`), a local citation
  against `src/fep_lean/formal`, and a record field against `TopicEntry`.
  `scripts/render_manuscript.py` fails on an unverifiable entry and prints an
  explicit "unchecked" line when the pinned library is absent rather than
  passing the group in silence.

- Gave the acceptance somewhere to bite. `scripts/check_render_log.py` was a
  real, tested check that nothing ran: `grep -rn check_render_log
  --include="*.yml" .github/` matched nothing, so every defect it catches could
  reach `main` unopposed. CI cannot re-run it, because CI does not render this
  manuscript: that needs a checkout of the shared template, XeLaTeX, pandoc,
  `rsvg-convert`, the mermaid CLI and the two faces the preamble selects. So a
  clean acceptance now writes `docs/render-acceptance.json` and CI runs
  `--verify-receipt` against it. The
  receipt is bound to a digest over every typeset manuscript source plus
  `manuscript/preamble.md`, so a chapter or a font selection changed without a
  fresh render fails CI; it is not bound to the values a `{{token}}` resolves
  to, which `manuscript_projection_drift` and `stale_render_defects` own on the
  render path. A rejected render writes no receipt and withdraws the standing
  one: sources can drift out of a render without changing, so the digest alone
  would let a superseded receipt keep vouching. The digests are recorded per
  file, so a stale receipt names what moved instead of printing two hashes.
- Made the publication entry point fail closed. `scripts/render_publication.py`
  runs the shared template's render stage and this repository's acceptance and
  exits on the conjunction, so a render the template calls successful over a
  dirty log is rejected here. The template compiles with
  `-interaction=nonstopmode` and tests four fatal markers; it is a separate
  repository, and `_pdf_latex_pipeline._check_fatal_error` still fails open
  upstream (as does `_pdf_mermaid.py`'s `render_disabled_reason` branch, which
  warns where the missing-`mmdc` branch raises).
- Recorded and probed the font requirement the render depends on. The R1 fix
  was a font installed on one machine and nothing in the checkout said which
  glyphs the document needs, so a render elsewhere would regress identically
  and silently. `docs/render-fonts.json` is derived from the sources and
  `--check`ed in CI; `scripts/build_render_fonts.py --probe` asks the host's
  fontconfig whether the selected faces cover the set, and
  `render_publication.py` runs it as a preflight.
- Judged render staleness by content instead of modification time, over every
  authored source rather than the ones a clock singles out. The first guard
  failed the delivered artifact because regenerating two files to
  byte-identical content moved their mtimes, and it could not have caught the
  opposite case at all: the template renders from `output/manuscript` when that
  directory exists and its hydration hook does not fire for this project, so a
  render made after two chapters were fixed reproduced their drift exactly
  while being newer than every source. The verdict is now whether each source's
  own lines, substituted the way the renderer substitutes them, are lines of
  the combined document -- and `render_publication.py` renders the authored
  sources itself before handing off to the template. Lines carrying a
  `{{source.*}}` stamp are exempt: they name the commit and date of one render,
  so no committed projection can agree with them, and a line whose markup the
  renderer consumes (the italic caption under a diagram fence becomes that
  figure's `\caption`) counts as rendered when its text is in the document.
- Linked into the repository through a ref that resolves. Five source links
  were pinned to a commit that existed only locally, so all five 404ed in the
  published PDF; they now resolve through the commit once it is on the remote
  and through the default branch until then, and the front matter prints which
  (`{{source.published_note}}`).
- Made an undisclosed release-stamp mismatch fatal. Between releases the
  checkout is always ahead of the stamped tag, so the mismatch cannot be the
  failure -- saying nothing about it can be, and the audited PDF stamped v1.1.0
  over a tree 15,033 Lean lines newer with nothing on the page to say so.
- Restored the green `ruff check` / `ruff format --check` gate that the render
  and audit fixes had broken (6 findings, 8 unformatted files).

- Hardened every production Lean/Lake probe against orphaned-grandchild
  timeouts: new `src/fep_lean/verification/_subprocess.py` runs each external
  probe in its own process group with a watchdog `SIGKILL` of the whole group
  on deadline (mirroring the test-suite's `run_lean_probe`), wired into the
  verifier compile probe, the declaration/axiom audit probes, and the `setup`
  bootstrap/lake commands. A wedged `lean`/`elan` grandchild can no longer
  hold the pipes and the `.olean` lock region past the advertised deadline.
- Made the theorem LaTeX projection fail closed: an unextractable statement
  raises instead of silently emitting a `\mathsf{?}` placeholder into the
  generated appendix.
- Extended generated-catalogue parity: `from_yaml` now also asserts
  `latex_equations` against `registry.LATEX_EQUATIONS`, matching the existing
  `lean_sketch` contract, wherever the catalogue is loaded (including wheels).
- Extended the coverage join to fail closed when a `theorem_maturity.yaml`
  primary/supporting/boundary reference is not a resolvable formal
  declaration (qualified namespace form).
- Preserved line numbers when the manuscript reference audit strips fenced
  blocks, so reported locations match the real file.
- Unified OpenGauss state-directory resolution (`resolve_gauss_home`:
  `GAUSS_HOME` → `config/settings.yaml` `gauss.home` → `~/.gauss`) across the
  SQLite client, `GaussRunner.create_default`, preflight validation, and the
  Hermes dotenv loader's home, so validation always checks the directory the
  run writes.
- Guarded CITATION.cff publication metadata: `docs/citation_audit.py` now
  fails when the CFF `version` drifts from the pyproject package version
  (same drift class as the toolchain pin audit).
- Output layer: atlas/dashboard/figure writers now render through atomic
  temp-file + `os.replace` semantics like every other projection writer; the
  dashboard y-axis label derives from the actual plotted floor instead of a
  hardcoded `0`; `latest_claim_ready_full_report` orders candidate reports by
  the deterministic run-id directory name instead of filesystem mtime; the
  reporter run-id helper drops the inline `__import__` and uses a tz-aware
  timestamp; and the stale `_write_sorry_distribution` figure helper is
  renamed to `_write_status_distribution`.
- Catalogue loaders fail closed: `FEPTopicCatalogue.summary()` raises on an
  unknown `mathlib_status` instead of silently counting it as `partial`, and
  the roster seal rejects `first_id` below `fep-001` (the canonical interval
  definition shared with novelty loading).
- Tests: the `serial_lean` marker now pins Lean-probe tests to a single xdist
  group via `pytest_collection_modifyitems`; live OpenRouter tests are
  strictly opt-in (`FEP_LEAN_LIVE_TESTS=1` required, never inferred from key
  presence); the Hermes deadline-abort ceiling allows scheduler slack; the
  future-mtime manuscript test stamps both times from one clock; and new
  `tests/test_core_body_modules.py` pins the five core_* body modules'
  exact rosters.
- Docs: scoped `formal/README.md`'s audit-inclusion claim to public theorems
  (private helpers are covered transitively), refreshed the stale
  `.ruff_baseline.txt` narrative, and removed six dead no-op LaTeX rewrite
  rules whose inputs were consumed by earlier loops.
- CI: added the `docs/lean-landscape.md` drift gate
  (`scripts/_maint_build_lean_landscape.py --check`) to the projection-check
  step and a least-privilege `permissions: contents: read` block.
- Tests: replaced the nip.io DNS dependency in the OpenRouter fallback test
  with a loopback httpserver plus an explicit `_build_model_chain` patch.

- Accepted H1.0--H1.8 of the dependency-gated Horizon research program, with
  optional H1.5 accepted separately. The archived
  [Horizon 1 record](specs/done/horizon-1-finite-synthesis/README.md) preserves
  the first H1.8 carrier-merge no-go and the repaired terminal theorem: one
  finite, synthetic, one-step posterior--decision--action certificate on a
  shared 16-state Boolean carrier, with a genuine sensory--active blanket and
  same-kernel strict real/native KL decrease.
- Kept the Horizon 1 exit claim narrow. It is not transition-aware planning,
  EFE-optimal control, physical thermodynamics, causal identification,
  empirical validation, or a universal FEP theorem.
- Advanced Horizon 2 through accepted H2.0--H2.3b, H2.4a/b,
  H2.5a/b/c/d (including H2.5b-R0 and H2.5d-R0), H2.6a/b/c, and H2.6a-R0:
  fixed-variance scalar Gaussian KL and coordinate geometry, local smooth
  duality, native kernel/action semigroups with the exact H1 lift, a scalar OU
  transition semigroup, a same-joint native posterior martingale with its
  limiting-observation conditional-expectation endpoint, selected-model
  identification, joint-law and fixed-truth posterior consistency, weak
  convergence to the sampled-parameter Dirac law, bounded-continuous transfer,
  bounded zero-one risk convergence, and monotone
  finite-grid path laws with support-aware
  forward-to-coordinate-reversed KL boundaries. Dynamic `Fin 4` transition
  covariance is derived generically by the accepted H2.5b-R0 spectral repair;
  the maintained H2.5b owner now constructs the native finite-axis Markov
  semigroup, invariant Gaussian, moments, full-time weak limit, and exact
  `Fin 1` H2.5a specialization while preserving the historical H2.0 no-go.
  The accepted H2.6a-R0 repair proves the selected scalar Gaussian
  density factorization, joint-law and evidence-marginal identities, and
  evidence-a.e. equality to Mathlib's native posterior; the maintained H2.6a
  owner adds exact posterior parameters, normalization, and chronological
  finite observation recursion. H2.5c now instantiates the preregistered
  external--sensory--active--internal carrier, derives its covariance, exact
  transition laws, invariant Gaussian, weak limit, and scalar specialization.
  The accepted H2.5d-R0 repair orthogonalizes the centered stationary law.
  Maintained H2.5d reconstructs the arbitrary-center blanket/endpoints
  `compProd`, identifies native pair and scalar conditionals blanket-marginal
  almost everywhere, proves endpoint `CondIndepFun` while retaining actual
  marginal covariance `1 / 24`, and derives a fixed bivariate precision
  perturbation with actual covariance `-1 / 15` and native non-independence.
  It claims no generic precision equivalence, transition-row conditioning,
  causal blanket, reversibility, H2.7 theorem, or H3 result.
  H2.6b now derives one-step posterior-predictive quadratic risk from the actual
  selected transition, proves finite attainment and evidence-a.e. native
  selector agreement, and supplies strict and tie witnesses without claiming
  policy-tree, reward--EFE, global Bayes-estimator, or infinite-horizon control.
  The H2.3b same-law countermodel keeps the native posterior equal to the prior
  only almost everywhere under the predictive law, and no entropy, logarithmic,
  unbounded-observable, rate, arbitrary-prior, continuous-parameter, or tail-field
  claim was introduced.
  No SDE, Fokker--Planck, Girsanov, continuous-path, reverse-OU, or physical
  entropy-production claim was introduced.
- Resliced and accepted the H2 terminal proof gate. H2.7-R0 proves actual
  Lebesgue-density evidence surprisal, recognition-to-exact-posterior native
  KL, the mean-coordinate Fisher-metric-dual natural-gradient tangent, and
  strict local descent. Its append-only source-bound decision opens H2.7 only;
  H3 remains closed pending the connected terminal merge and review.
- Added a deterministic manuscript author block and graphical abstract under a
  strict metadata, digest, dimension, and rendering contract. These changes,
  together with the accepted post-release H1/H2 source wave, deliberately
  invalidate the v1.1.0 evidence receipts for the live checkout until
  `FEP-EVIDENCE-CURRENT` is completed.
- No post-v1.1.0 theorem, manuscript, or generated artifact is part of the
  immutable v1.1.0 release. A later release must choose its own version and DOI
  only after the connected theorem and source-bound evidence gates settle.
- Refreshed the deterministic offline evidence surface after the post-v1.1.0
  source wave (`fep-evidence` lane): catalogue stage exit 0, formalism coverage
  regenerated (52 maintained formal modules, 33 foundation modules, 1480 total
  theorem declarations, 226 composed theorem declarations, including the new
  `FepSketches.ness_flow` and `FepSketches.compositions.smooth_reference_kernel`
  owners), atlas and formal-kernel dashboard projections regenerated and
  byte-current, theorem-maturity projection current, manuscript render check
  passing with every authored placeholder resolved. Native Lean compile sweep
  and Hermes/OpenGauss receipts remain deferred to the coordinator.

### CI integrity and maintenance accuracy (2026-09-07)

- Fixed the red `main` CI. The projection-check step ran
  `scripts/build_render_fonts.py --check` before `uv run fep-lean catalogue`
  had materialized the gitignored generated appendix
  (`manuscript/09z_unified_formalism_catalogue.md`), so every fresh checkout
  derived a smaller glyph set than the committed `docs/render-fonts.json` and
  the workflow reported a false STALE. The check now runs after the catalogue
  step, and requirement derivation fails closed on its own: without the
  generated appendix, `render_font_projection` and `font_coverage_defects`
  raise `FontProbeError` naming the remedy instead of silently deriving an
  understated requirement that every later check would accept.
- Closed `FEP-H2-SMOOTH` per the backlog closure rule: H2.7 and its R0 proof
  gate are accepted with terminal evidence in the Horizon 2 spec (328
  mandatory cases, the enabled Fin4 supplement, three source-bound reviews).
  Remaining H3 work stays under `FEP-H3-SCIENCE`. The backlog gains three
  cold-startable major rows: `FEP-CI-RENDER`, `FEP-LEAN-UPGRADE`, and
  `FEP-RELEASE-NEXT`; `FEP-EVIDENCE-CURRENT` now names the settled owner
  roster (bridge contract v0.6, GNN 3.3.0 route rename re-pin).
- CI hygiene: `concurrency` groups with PR cancellation, `timeout-minutes` on
  every job, a coverage-report artifact, a pinned `elan-init` commit plus an
  elan-toolchain cache, and a deduplicated failure issue from the weekly
  pin-audit schedule, whose result previously went to nobody. Actions moved
  to current majors: checkout@v7, upload-artifact@v7, setup-uv@v10.0.1 (no
  rolling v10 major tag exists), cache@v6, github-script@v9.
- Moved `scripts/render_manuscript.py --check` to the lean CI job, after the
  Mathlib cache fetch: its Mathlib-citation allowlist verification fails
  closed when `lean/.lake/packages/mathlib` is absent, which made the check
  unpassable in the Python job on every fresh checkout (masked behind the
  font-check STALE, which died first). The job also runs
  `uv run fep-lean catalogue` first, because the generated manuscript inputs
  do not survive across jobs.
- Made the Python CI suite finish at all: the post-v1.1.0 wave had never
  reached a green CI run, so three latent host dependencies surfaced once
  the earlier steps stopped dying. `.python-version` pins CPython 3.14 —
  the Q7 runner-scaffold digest freezes `ast.dump` output, which is
  interpreter-sensitive, and the reviewed digest was pinned under 3.14 (a
  3.12 interpreter computes a different digest and fails all 22 scaffold
  tests). The two manuscript-rendering tests that drive the real render
  path against the real tree (pinned Mathlib checkout, generated figure
  rasters) are `serial_lean` workspace tests now, and the host-font
  coverage probe skips CI runners, whose fontconfig resolves a glyphless
  JuliaMono stub; the render-host preflight
  (`scripts/build_render_fonts.py --probe`) remains the font acceptance.
- Documentation accuracy: `--gnn-root` documented as required for every
  `bridge` verb; the README/AGENTS/SPEC check lists now match what CI runs
  (`docs/pin_audit.py --check-latest`, `uv lock --check`, the
  `build_render_fonts.py --check` gate, and the `-m "not serial_lean"` pytest
  filter); HANDOFF's H2.7 status paragraph and its bridge-contract version
  (v0.4 → v0.6) refreshed against the tree. Dependency bumps were attempted
  and reverted: the Horizon predecessor receipts bind `uv.lock` bytes, so a
  lock refresh without the coordinated evidence re-pin fails the acceptance
  chain fail-closed (see `FEP-EVIDENCE-CURRENT`).
- Follow-up parity sweep after an adversarial doc review: the README, AGENTS,
  SPEC, HANDOFF, testing, development, and cold-start check lists now name the
  exact CI invocations for the atlas and formal-kernel dashboard projections
  (the generator `--check` scripts, not the CLI freshness forms), and carry the
  render-acceptance receipt verification, the lock check, the
  `--check-latest` pin audit, and the `-m "not serial_lean"` pytest filter
  wherever the corresponding recipe appears. The `FEP-SCAFFOLD-PORTABILITY`
  backlog row now scopes only the Q7 scaffold digest (Q5's runner custody is
  whole-file sha256 and already interpreter-independent).

## 1.1.0 — 2026-08-23

### 155-topic formalism expansion and release acceptance

- Extended the maintained schema-2 roster beyond `fep-120` through `fep-155`,
  yielding 155 stable topics in 20 families across the five established areas.
  The five new families cover finite-sample Laplace/Brier risk, closed-loop
  policy trees and treewise EFE, finite-to-native blanket transfer, finite
  exponential-family dual geometry, and exact two-state continuous-time
  thermodynamics.
- Added one reusable foundation and one seven-theorem composition leaf for each
  family. The new rows name explicit assumptions and non-vacuity boundaries:
  nonzero Laplace bias, a strict Boolean feedback advantage, a correlated
  nondegenerate blanket model satisfying native `CondIndepFun`, positive and
  zero Fisher-information witnesses, and a strictly decreasing nonstationary
  Lyapunov example.
- Expanded the typed numerical dashboard from ten to fifteen family witnesses.
  Each witness now owns multiple typed checks with independent tolerances;
  acceptance is their conjunction plus a named boundary observation.
- Added the authored 155-topic manuscript chapter with theorem names,
  assumptions, composition bridges, evidence-plane boundaries, and primary
  sources for Brier risk, sophisticated inference, information geometry, and
  the pinned Lean/Mathlib releases.
- The release-snapshot schema-4 formalism audit independently validates all 823 required
  formal-resource declarations, including 699 evidence declarations, under
  Lean 4.33.1 and the locked Mathlib revision with zero warnings, no `sorryAx`,
  and no untrusted axiom. The release-snapshot native receipt validates the exact 155
  topic roster with zero failures, warnings, or `sorry`; the schema-3 Python
  receipt binds the complete canonical collected-node roster, records zero
  failures or errors, and enforces the maintained 89% line-coverage floor;
  and the schema-4 browser receipt replays six accepted
  screenshots against all 20 families and 15 typed numerical witnesses. The
  retained 50-topic provider report remains historical and was not promoted to
  full-mode evidence for that release snapshot. Later source waves must
  regenerate every receipt before making a current-source claim.

### Prior 120-topic expansion and family-owned formal sources

- Advanced the schema-2 roster seal from `fep-050` through `fep-120`, yielding
  120 reviewed topics in 15 families across the five established areas. The
  expansion adds measure-theoretic Bayesian inversion, variational duality and
  information bounds, controlled and temporal inference, causal interventions,
  generalized predictive coding, path thermodynamics, geometric optimization,
  collective inference, and learning/model-evidence families.
- Replaced the monolithic body owner with family modules under
  `src/fep_lean/catalogue/bodies/`. One explicit registry validates namespace,
  declaration, ordering, uniqueness, and roster parity; theorem signatures are
  projected separately from the canonical bodies.
- Added a maintained novelty ledger for every expansion row. Each record names
  earlier nearest topics, its invariant and carrier delta, and a required
  `FEPComposed` bridge. Cross-topic witnesses now live in manifested leaf
  composition modules, with `composed.lean` reduced to an import-only aggregate.
- Added explicit finite path-law, fluctuation, Jarzynski, reversible-dissipation,
  categorical Fisher, Cramér--Rao, natural-gradient, mirror-descent,
  Bregman-projection, replicator, collective-agent, consensus, concentration,
  PAC-Bayes, posterior-concentration, regret, and Bayes-factor surfaces with
  named support and non-vacuity boundaries.
- The generated coverage, maturity audit, atlas, dashboard, and manuscript
  projections own all live counts. The 50-topic native, declaration, and full
  reports below are retained as historical evidence for their exact source
  snapshot and do not bind the expanded roster.

### Prior 120-topic acceptance evidence (historical source snapshot)

- Migrated the exact reproducibility pins to the newest stable pair, Lean
  4.33.1 and Mathlib `v4.33.1`, with resolved Mathlib revision
  `0df444a360eaa60ab8c11dca51a86af692955474`. Added a fail-closed networked
  latest-compatible-pair audit to pull-request CI and a scheduled weekly check;
  newer Lean-only patches remain visibly pending until a matching Mathlib tag
  exists, and release candidates or nightlies never replace the stable compiler.
- Updated the canonical calculus bodies for Lean 4.33's stricter elaboration,
  replaced deprecated square-root imports, migrated fep-036 from the retired
  PMF binomial API to Mathlib's measure-valued binomial distribution, and made
  every affected topic compile independently rather than borrowing aggregate
  imports. The complete `FepSketches` closure builds warning-free in 8,732 jobs.
- The source-bound native schema-4 receipt independently validates 120/120
  topics with zero warnings, zero `sorry`, and a 334.632-second duration under
  Lean 4.33.1 and the resolved pinned Mathlib revision.
- The schema-4 declaration audit independently resolves 647/647 audited
  declarations, including 558 structured evidence declarations, with zero
  warnings, no `sorryAx`, and trusted axiom policy version 1.
- The complete Python suite passes with 744 tests passed, 22 skipped, and
  90.62% coverage. Strict MyPy, Ruff, formatting, lock/install compatibility,
  projection freshness, manuscript rendering, links, pins, cross-references,
  theorem references, and 73-entry citation coverage were green for that
  snapshot.
- Six retained standalone, desktop, and mobile atlas/dashboard captures passed
  fresh unprimed visual review. The browser receipt verifies all five areas,
  15 families, 120 topics, 98 scientific relations, 43 satisfied capabilities,
  ten numerical witnesses, search/filter/keyboard behavior, zero external
  assets, and no body overflow.
- No new provider run was made for the expanded source. The retained 50-topic
  full report and two earlier one-topic smokes remain historical evidence only.

### Prior 50-topic semantic milestone (historical source snapshot)

- Deepened all 50 catalogue rows to directly formalized, deliberately bounded
  topic scopes. The final fep-036 promotion adds Mathlib's finite binomial PMF,
  an outcome-indexed Laplace prior, exact shrinkage, consistency transfer from
  convergent empirical frequencies, and posterior closure while explicitly
  excluding an unproved LLN, finite-sample risk, or marginal-likelihood claim.
- Added exact theorem families for native posterior inversion, normalized
  filtering and hierarchy; Bernoulli Fisher information, natural gradient,
  Fisher--Rao distance, and Hellinger divergence; measurable semigroups,
  quadratic convergence, finite stationary currents, Gaussian entropy and
  Helmholtz calculus, finite stick conservation, and matrix message passing.
- Expanded the canonical composed module to 22 declaration-witnessed seams
  spanning inference, information geometry, policy choice, dynamics,
  thermodynamics, and partition-energy conservation. The generated capability
  ledger now resolves all 33 retained nodes without erasing broader scientific
  limitations that remain outside those bounded capabilities.
- Expanded the joined formal surface to 412 theorems, 175 definitions, 10
  abbreviations, and 8 structures: 257 topic theorems plus 155 theorems in six
  foundation modules and the composed module. The authored graph now contains
  20 theorem-witnessed formal relations and 8 conceptual relations, with all
  33 retained capabilities satisfied at their deliberately bounded scopes.

### Prior publication and validation surfaces

- Added a semantic-closure manuscript chapter that embeds the generated SVG
  atlas, links its offline interactive counterpart, and presents the six
  executable theorem strands plus the seven-layer validation contract.
- Made manuscript rendering copy and rewrite declared atlas assets into the
  build tree and fail closed before writing when a referenced visual is
  missing. Zero-valued relation and capability buckets are now retained in the
  manuscript variable schema so placeholders cannot disappear at closure.
- Reconciled the manuscript and background documentation with the live native
  posterior, Bernoulli geometry, finite NESS, response, entropy-production,
  Gaussian, and Landauer theorems while preserving the continuous,
  multidimensional, empirical, and microscopic boundaries.
- Removed copied fallback-table counts from the atlas renderer. The accessible
  node and relation summaries now derive from the live graph, and regression
  tests pin their parity.
- Applied an independent desktop/mobile visual critique: the evidence inspector
  now precedes a bounded pan viewport, canonical totals remain visible outside
  the scroll plane, graph typography renders at a readable scale, panning is
  explicitly signposted, and every thin edge has a wide transparent pointer
  target. Exact 1440x900 and 390x844 acceptance captures are retained with the
  closed rationale.

### Prior independent failure-seam hardening

- Repaired `review` as an ordered two-turn workflow: the first provider turn
  must emit refinable Lean, the exact compiled result is supplied to a
  contradiction-free prose-only review prompt, both turns are persisted and
  separately cached, and review failure now fails the requested workflow.
- Propagated native Lean warning lists through `TopicRunResult`, pipeline
  completion/statistics, summary/run/verification manifests, Markdown reports,
  and independent receipt reconciliation. A warning-bearing full row can no
  longer be counted as verified.
- Made declaration evidence fail closed when Lean exits zero but omits one or
  more `#print axioms` results. The multiline parser now handles Lean's hard
  wrapping, normalizes the complete canonical declaration closure, and the
  validator independently checks return code, counts, resolution, axiom parity,
  warnings, `sorryAx`, toolchain, digest, and failure state.
- Made the installed console boundary explicit: imports/resources and help are
  wheel-native, while substantive commands require and validate a source
  checkout. The isolated-wheel smoke now proves both the fail-closed no-root
  path and a real explicit-root `atlas --check` command.
- Bound the repository report-receipt adapter to a live source root by default
  and exposed `--project-root` for explicit independent validation.

### Historical 50-topic evidence state

The following receipts and counts describe the earlier source snapshot that
they hash. They are not current acceptance evidence for the 155-topic cut.

- The historical coverage and theorem-maturity projections for that source
  snapshot recorded all 50 bounded semantic dispositions as
  `formalized`, 48 distinct Mathlib imports, 104 topic-import edges, 28 authored
  relations, and 33/33 satisfied retained capabilities.
- The source-bound native schema-3 receipt independently validates 50/50 topics
  with zero warnings, zero `sorry`, and a 100.446-second duration. The
  schema-4 formalism receipt independently resolves 262/262 declarations,
  including 243 evidence declarations, with zero warnings, no `sorryAx`, and
  trusted axiom policy version 1. The aggregate Lake target completes 8,257
  jobs cleanly.
- The owner-manifest-2 full report
  `output/reports/run_20260820_183143_709998` independently validates as
  schema 3, source-bound, complete, and claim-ready. Gemini 3.7 Flash completed
  all 50 selected topics: 50 Hermes successes, 50 preserved semantic
  declaration contracts, and 50 direct provider Lean compiles, with zero
  warnings, zero `sorry`, and zero network retries.
- The full run used 133,519 tokens and completed in 496.386 seconds, including
  418.745 seconds of Gauss sessions and 75.37 seconds of manuscript artifacts.
  Independent receipt validation checked all 56 hashed artifacts without an
  error.
- Two bounded one-topic OpenRouter/Hermes full-mode smokes completed against
  earlier source snapshots: `fep-001` with Kimi K2.6 and `fep-002` with Gemini
  3.7 Flash. Each selected topic passed its then-current provider, Gauss, and
  Lean path. The present validator rejects both report directories because
  they predate the current report-receipt schema and their source/configuration
  digests no longer match the live tree. They are not claim-ready evidence for
  the final source or the complete 50-topic catalogue.
- `FEP-FULL-002` and `FEP-PROV-003` were complete for that snapshot. The
  historical run stored no provider secret and granted no authority for a
  later release.

## Development snapshot — 2026-08-19

### Package and canonical ownership

- Replaced collision-prone loose top-level modules with one installable
  `fep_lean` namespace, package-relative imports, packaged catalogue data, and
  an isolated wheel/import/console-script contract.
- Split maintained catalogue metadata, semantic review, canonical Lean bodies,
  and generated projections into typed single-owner seams. Regeneration now
  preserves the checkout and wheel catalogue bytes deterministically.
- Added a strictly validated authored formalism graph with explicit
  `conceptual`, `formal`, and `blocked_by` edge kinds. Formal edges require
  qualified Lean witnesses, and capability nodes retain open/partial/satisfied
  resolution history with declaration evidence. Its generated coverage report
  records 50 topics, 227 topic theorems, 18 definitions, 15 abbreviations, 37
  distinct Mathlib imports, 98 topic-import edges, 31 authored relations, 3
  composed theorems, and 14 capability nodes.

### Formal kernel and semantic depth

- Replaced scalar KL stand-ins in fep-002 and fep-014 with pinned Mathlib
  `InformationTheory.klDiv` facts, including native nonnegativity,
  self/zero characterization, VFE bounds, and the composition-product chain
  rule. The absent-at-pin data-processing theorem remains an explicit gap.
- Replaced fep-048's implication-shaped premise with Mathlib's native
  `ContractingWith` fixed-point API, a satisfiable real-line halving witness,
  unique-zero theorem, and convergence of every halving iterate.
- Added direct quadratic Bregman identity/nonnegativity/zero characterization
  to fep-029 and normalized finite Boltzmann–Gibbs weights to fep-031.
- Added native conditional-independence symmetry/non-vacuity (fep-009),
  reversible-Markov-kernel invariance (fep-010), binary entropy
  maximum/equality (fep-030), and strict two-point Jensen for logarithm
  (fep-035).
- Added the canonical packaged `FEPComposed` module. Its witnessed theorems
  compose fep-002 with fep-014's KL chain rule and fep-031's two-state
  zero-inverse-temperature Gibbs law with fep-030's binary entropy maximum.
- Removed all project-owned Lean warnings without suppression and made warning
  rejection part of the native verifier and CI contract.
- Reclassified only the exact narrowed results supported by source. The current
  semantic census is 9 `formalized`, 13 `conditional_proxy`, 6
  `structural_proxy`, 5 `proxy`, and 17 explicit `scope_gap` rows.

### Evidence, manuscript, and audit integrity

- Added atomic, source-digest-bound native Lean receipts and kept their
  `native_claim_ready` predicate distinct from catalogue completion and
  claim-ready full Hermes/OpenGauss reports.
- Replaced in-place manuscript substitution with fail-closed source-to-build
  rendering. Missing, stale, partial, or tampered evidence renders explicit
  unavailability rather than zero-valued success prose.
- Added deterministic formalism coverage, theorem-reference, citation, and
  placeholder audits to CI. All 59 bibliography entries are both indexed and
  cited, and every canonical `fepNNN_*` manuscript reference resolves.
- Added a deterministic, offline formalism atlas rendered from the same
  coverage join: a publication-safe SVG plus searchable, filterable,
  keyboard-accessible HTML with complete node/edge tables. The evidence-first
  view defaults to theorem-witnessed edges, exposes non-color status labels and
  line-style semantics, wraps topic titles, labels proved compositions, and
  expands its inspector only on demand.
- Added a native formalism audit that resolves every primary and graph-evidence
  declaration, records `#print axioms` results, and fails on stale projection,
  compiler errors, warnings, timeouts, or `sorryAx`.
- Reconciled the manuscript and background documentation with the exact Lean
  statements, semantic dispositions, evidence classes, and primary sources;
  removed completed-Hermes, universal-FEP, KL-availability, thermodynamic,
  NESS, information-geometric, and dependency overclaims.

### Local acceptance

- Full Python/coverage gate: 409 collected, 406 passed, 3 intentionally
  skipped, 90.77% coverage against the 89% floor.
- Mypy passed for 39 source files; Ruff and format checks passed for all 157
  checked files; lock and installed-dependency checks passed.
- Wheel and source distributions built successfully with the packaged
  catalogue and canonical composed Lean source.
- Aggregate Lean build completed 8,251 jobs with no project warning.
- The independently validated native receipt records 50/50 clean topics, zero
  warnings, zero `sorry`, Lean/Mathlib v4.29.0, and 106.732 seconds.
- The declaration audit resolves 56/56 primary/composed declarations and all
  12 evidence declarations, with no warnings or `sorryAx`.
- All generator, link, Markdown, pin, cross-reference, theorem, citation, and
  manuscript-placeholder gates passed. Catalogue mode remained honest at zero
  verified topics.

### Still externally gated

- Full preflight passes every local capability and fails only because neither
  `OPENROUTER_API_KEY` nor `ANTHROPIC_API_KEY` is configured. The live
  Hermes/OpenGauss smoke, complete run, and final full-report receipt remain
  open; no credential, provider call, commit, push, or publication occurred.

## Development snapshot — 2026-07-31

### Verified in the local audit

- Repaired bounded Lean setup so it resolves the declared Lean 4.29.0
  toolchain directly, acquires Mathlib v4.29.0, and fails rather than masking
  installer or build errors.
- Built `FepSketches` successfully and passed the native 50-topic compile
  sweep with no compile errors or `sorry` results.
- Repaired the documented `scripts/03_lean_verify_only.py` path by adding the
  first-class `fep-lean verify` command, which performs the same 50-topic
  native sweep without Hermes or OpenGauss.
- Hardened full-mode fail-closed behavior, Hermes preflight budget restoration,
  SQLite session cleanup, selected-topic report denominators, nested artifact
  hashes, and custom manuscript output-root isolation.
- Added the strict `mypy` development gate and reconciled the test census at
  342 collected tests across 30 modules.
- Reconciled repository documentation and operator metadata with the 1.0.0
  checkout.
- Added `HANDOFF.md` with the next-reviewer protocol, evidence receipt, and
  remaining extension scope.
- Added a maintained semantic review for all 50 theorem proxies in
  `config/theorem_maturity.yaml`, with generated Markdown, theorem-name parity
  validation, explicit non-vacuity and assumption reviews, and native Lean
  acceptance probes. The audit records scope gaps honestly and changes no
  `mathlib_status` claim.
- Added the read-only `validate_report_receipt` API and
  `scripts/verify_report_receipt.py`. It recomputes every listed artifact hash,
  rejects report-directory escapes, and reconciles summary, run, and
  verification manifests. A real complete full-mode receipt is still required
  before FEP-PROV-003 can close.
- Re-ran `uv run fep-lean verify`: `complete: true`, 50/50 clean native Lean
  results, no `sorry` results. The catalogue CLI receipt also passed the new
  independent checker with `mode: catalogue` and `verified_topics: 0`.
- The complete Python gate passed with `339 passed, 3 skipped`, 90.24% line
  coverage, and 342 collected tests; strict receipt failure paths, including
  malformed boolean flags, are covered without lowering the 89% threshold.
- Recorded the Ruff policy decision in `docs/quality.md`: the current 216
  findings (down from the prior 222-finding baseline) are explicitly
  non-gating until Ruff is pinned, debt is reduced in staged batches, and the
  exact check and format commands run in CI.

### Still externally gated

- A permitted `OPENROUTER_API_KEY` or `ANTHROPIC_API_KEY` is still required to
  exercise the live Hermes/OpenGauss/Lean full-mode smoke and complete-catalogue
  runs. No credential is stored in this repository.

## Development snapshot — 2026-07-31 (revision 2)

### Improvements from Mahakala adversarial review

- **AGENTS.md**: Added Terminology section defining "sketch" (Lean code body)
  vs "proxy" (theorem statement). Documented `complete: true` semantics for
  `FEP_LEAN_MAX_TOPICS` subset runs. Added `preflight` JSON stability note.
- **README.md**: Added "why 50" provenance sentence, `verify` mode in Contract,
  inline "strict" definition (`Missing capability → complete: false, no report
  directory`), explicit releaseable-local statement, and Notation section with
  Lean↔FEP convention bridge.
- **ISA.md**: Added ISA-10 — non-vacuity/assumption-strength gate on every
  theorem proxy in `config/theorem_maturity.yaml`.
- **docs/quality.md**: Ruff pinned to `>=0.15.0` in dev dependencies, baseline
  captured at `.ruff_baseline.txt`, CI runs `ruff check` and `ruff format
  --check` in informational mode. Staged debt plan has deadlines.
- **CI**: Added `mypy src`, `ruff check`, and `ruff format --check` steps.
- **src/fep_lean/gauss/runner.py**: Removed misleading `FEP_LEAN_GAUSS_WORKFLOWS=1`
  docstring claims (gate was documented but never implemented in code).
- **lean/.lake/packages/**: Removed stale corrupt Mathlib cache directory
  `mathlib.corrupt-20260730`.
- Added `docs/test-suite-review.md` (31 files, 342 tests, 0 mocks, 0
  `except:pass`, parallel-safe, 90.25% cov, no blocking issues).
- Added `docs/mahakala-review.md` (multi-wave adversarial review with 6 persona
  proxies, 15 findings, GO with 3 pre-conditions, 9/10 overall score).

### Ruff cleanup (216 → 0)

- Applied 125 auto-fixed + 18 unsafe-fixed findings across 49 files
- Manually fixed 25 E741 ambiguous-variable-name violations (l→line)
- Fixed 3 B023 loop-variable-in-closure (captured via default arg)
- Fixed 7 E402 import-ordering violations (moved imports to top)
- Fixed 6 PYI036 `__exit__` type annotations, 1 PLW1510 `check=False`,
  1 TRY004 `TypeError` vs `ValueError`
- Suppressed RUF001/RUF003 (intentional math Unicode), BLE001 (fail-closed
  design), EXE001 (scripts imported not execed) via pyproject.toml
- `.ruff_baseline.txt`: baseline reduced to 0
- `docs/quality.md`: revision 3 — Ruff is clean, staged debt plan complete

### Gate verification

All gates re-run and passing after improvements:
- 339 passed, 3 skipped, 90.49% coverage (was 90.25%)
- mypy: 23 source files, no issues
- **ruff: 0 findings** (was 216 — 100% reduction)
- Lean verify: 50/50 clean, `complete: true`
- All 6 doc audits pass (links, md_hygiene, pin_audit, xref, catalogue, receipt)
Owner roster bumped
15 → 17 for the new rostered modules.
