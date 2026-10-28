---
title: FEP_Formal Ideal State Assessment
status: active
phase: verifying
updated: 2026-10-27
---

# FEP_Formal Ideal State Assessment

## Problem

FEP_Formal combines a 168-row catalog, generated Lean source, a pinned
Lean/Mathlib workspace, Hermes model calls, OpenGauss persistence, manuscript
projections, and strict run reports. The repository must distinguish a
deterministic offline catalog from real theorem verification. A green local
command is only meaningful when its capability boundary and evidence are
explicit.

## Vision

A fresh checkout can reproduce the catalog, acquire the exact declared Lean
toolchain, compile the canonical aggregate, and expose a bounded full-run
workflow whose report proves what was actually verified. Missing external
credentials or failed topics stop full mode without producing a misleading
success report.

## Scope

This assessment covers the standalone repository boundary:

- Typed authoring parity among the roster/family metadata, semantic and novelty
  review, authored relations, family-owned canonical bodies, and their
  generated YAML/Lean/documentation projections.
- Python dependency installation, tests, coverage, type checking, and local
  subprocess/file/database behavior.
- Exact Lean/Mathlib `v4.35.0` acquisition and compilation, plus a
  fail-closed audit against the newest stable release pair.
- Hermes, OpenGauss, SQLite session lifecycle, report provenance, and generated
  manuscript artifacts.
- Documentation links, cross-references, pinned dependency claims, and this
  repository's operator contracts.
- Versioned releases through the [release procedure](docs/release.md): one
  version/date, a dated changelog section and green hosted CI on the exact commit.

## Out of scope

- Changing the parent repository or any sibling repository.
- Treating catalog mode, a cached response, or a generated manuscript value
  as proof that a theorem was verified.
- Printing, inventing, or storing provider credentials.
- Making mathematical claims stronger than the source theorem statements and
  the compiler evidence support.

## Ideal-state criteria

| ID | Criterion | Required evidence |
| --- | --- | --- |
| ISA-01 | The sealed topic roster and family registry are complete and parity-safe. | Registry/SSOT tests pass; the aggregate generator is deterministic and leaves no diff. |
| ISA-02 | Offline mode is deterministic and honest. | `uv run fep-formal catalogue` completes, emits reproducible artifacts, and reports `verified_topics: 0`. |
| ISA-03 | The local Python boundary is reproducible. | `uv sync --locked --extra dev`, `uv pip check`, the coverage gate, and the [canonical strict typing gate](AGENTS.md#required-checks) pass. |
| ISA-04 | The pinned Lean workspace is real, not merely configured. | Direct pinned Lean/Lake version probes, Mathlib cache/build, `lake build FepSketches`, an exact sealed-roster native compile sweep, and the declaration/axiom audit pass. |
| ISA-05 | Full mode is fail-closed. | Preflight requires Gauss, writable state, exact Lean/Lake/Mathlib, and Hermes credentials; any failure returns an error without a successful report. |
| ISA-06 | The live full path is end-to-end. | A permitted Hermes provider answers a bounded smoke run, OpenGauss persists and closes sessions, Lean verifies each selected topic, and the report/manifest agree. |
| ISA-07 | Reports are provenance-safe. | Selected-topic identities and denominators, source/config and compiled-source digests, the preserved Lean declaration contract, toolchain revision, nested artifact hashes, verification source, and completion state are internally consistent. |
| ISA-08 | Generated manuscript projections use the requested output root. | A custom output-root run cannot consume a stale report from the default `output/reports` tree. |
| ISA-09 | Operator documentation matches behavior. | Link, Markdown hygiene, pin, and cross-reference audits pass after catalog generation; counts and setup commands are current. |
| ISA-10 | Every primary theorem proxy has a non-vacuity and assumption-strength review on record. | `config/theorem_maturity.yaml` has a `non_vacuity` field for every topic, and the generated `docs/theorem-maturity-audit.md` renders it. The `non_vacuity` entry documents whether the statement has a real witness or is structural/vacuous; topics with `non_vacuity: structural` or `non_vacuity: witnessed` are accepted; topics missing the field are flagged. |
| ISA-11 | Scientific relations and capability history are explicit. | The typed loader validates every authored edge, every gap row has a `blocked_by` edge, derivational `formal` edges are acyclic, both theorem-backed kinds resolve leaf-owned declarations that use both endpoints, `formal_pairing` does not imply dependence, capability evidence resolves, and shared imports are reported separately. |
| ISA-12 | Manuscript claims fail closed. | Theorem-reference, bibliography/citation, placeholder, receipt, and source-to-build rendering audits pass; authored Markdown is never modified by rendering. |
| ISA-13 | Formal breadth and depth are inspectable without a second semantic source. | Coverage JSON/Markdown and the offline SVG/HTML atlas are deterministic projections of the same canonical join, conserve every node/edge, and pass drift/accessibility tests; the numerical dashboard independently renders every typed family witness and preserves its non-proof evidence label. |

## Anti-criteria

The repository is not in the ideal state if any of these occurs:

- catalog mode reports a verified topic or full mode reports success after a
  failed capability check;
- a generated aggregate, report, or manuscript projection is treated as an
  authoring source of truth;
- setup silently accepts the wrong Lean version, a partial Mathlib checkout, or
  a failed build;
- a report calls failed Hermes rows `hermes_refined`, uses the full catalog
  as a filtered-run denominator, or records stale artifact hashes;
- an unexpected runner failure leaves an open SQLite session or a live worker;
- validation acquires dependencies, prints credentials, or makes unbounded
  network calls;
- external credentials are committed, copied into tracked files, or inferred
  from a successful local fixture;
- stale test counts, version claims, or links make the documented operator path
  disagree with the checked-out tree.

## Verification strategy

Run these probes from the repository root, in order when a full local audit is
needed:

```bash
uv sync --locked --extra dev
uv run python scripts/_maint_build_topics_catalogue.py --check
uv run python scripts/_maint_build_fep_all_lean.py --check
uv run python scripts/_maint_build_formal_modules.py --check
uv run python scripts/theorem_maturity_audit.py --check
uv run python scripts/build_formalism_coverage.py --check
uv run python scripts/_maint_build_lean_landscape.py --check
uv run fep-formal atlas --check
uv run fep-formal dashboard --check
uv run python docs/pin_audit.py --check-latest
uv run mypy src scripts docs
uv run fep-formal setup
cd lean
lake build FepSketches
cd ..
uv run fep-formal verify --fail-on-warnings --receipt output/native-verification.json
uv run python scripts/audit_formalisms.py --receipt output/formalism-audit.json
uv run fep-formal catalogue
uv run python docs/theorem_ref_audit.py
uv run python docs/citation_audit.py
uv run python scripts/render_manuscript.py --check
uv run python docs/check_links.py --strict --include-root
uv run python docs/md_hygiene.py --strict
uv run python docs/xref_audit.py
uv run python scripts/capture_browser_acceptance.py
uv run python scripts/build_release_bundle.py --run-python-acceptance
release_dir="$(mktemp -d)"
SOURCE_DATE_EPOCH=0 uv run python scripts/build_release_bundle.py \
  --output "$release_dir/fep-formal-candidate-168.tar.gz"
SOURCE_DATE_EPOCH=0 uv run python scripts/build_release_bundle.py \
  --check --output "$release_dir/fep-formal-candidate-168.tar.gz"
uv run fep-formal preflight
```

`preflight` reports the external full-mode capability boundary. A complete
local assessment must also run the direct Lean gate and the bounded full
workflow after credentials are supplied through the operator's existing secret
mechanism:

```bash
FEP_FORMAL_CATALOGUE_COMPILE_TEST=1 uv run pytest tests/test_catalogue_bodies_compile.py -q --no-cov
uv run fep-formal run --topic fep-001
uv run fep-formal run
```

The smoke run is accepted only when its result is `complete: true`; the full
run is accepted only when all selected topics are cleanly verified and the
report's verification manifest agrees with the result. If credentials are not
available, record the exact preflight failure and leave the full-run criterion
open in [TODO.md](TODO.md).

## Current assessment

The following accepted source checkpoint predates the unreleased identity
migration. It remains historical acceptance of that source, not of the
changed checkout. Current cutover work and outstanding gates are recorded
in the [migration status](docs/identity-migration-status.md).

The accepted software/proof-component source is
[`a46ed93473046293f6e5ef33ba4ced2ad3ffdc43`](https://github.com/ActiveInferenceInstitute/fep_formal/commit/a46ed93473046293f6e5ef33ba4ced2ad3ffdc43);
its exact-main evidence is [PR #216](https://github.com/ActiveInferenceInstitute/fep_formal/pull/216) and
[fresh main workflow 39772166859](https://github.com/ActiveInferenceInstitute/fep_formal/actions/runs/39772166859).
The full fifteen-cell installed-wheel profile, source/native/audit/render/font
artifacts and scoped 390-page PDF layout were independently accepted.
The delivered #105 scope adds typed missing-lemma or Issue obligations to the
six remaining conceptual relations, exposes them in the atlas, preserves
legacy schema-2 compatibility, and pairs the supporting fep-016 quadratic
nonnegativity law with fep-032 bounded-step descent on the same state and
center. This does not derive a precision update, Laplace approximation,
general optimizer or convergence theorem, or promote a primary theorem.
The [F07 accepted scope](specs/comprehensive-next-steps/finite-rate-distortion-duality-20261021.md)
and [delivery history](CHANGELOG.md) retain earlier bounded component deliveries.
The EMP-J1 governance disposition concerns missing empirical admission gates,
not a dataset result or execution. Scientific primary, capture/archive,
reproduction and optional provider lanes remain separately open in
[TODO.md](TODO.md).

### Previous accepted software checkpoint

The preceding accepted source [75cde030c34d331eefb4b95943ac2fe7fb1505cb](https://github.com/ActiveInferenceInstitute/fep_formal/commit/75cde030c34d331eefb4b95943ac2fe7fb1505cb)
was delivered through [PR #214](https://github.com/ActiveInferenceInstitute/fep_formal/pull/214) and
[exact-main workflow 39715953206](https://github.com/ActiveInferenceInstitute/fep_formal/actions/runs/39715953206).
Its finite duality, lexical theorem spans and separately bounded governance
history remain valid for that epoch; the newer software acceptance does not
expand their scientific scope.

### Earlier accepted software checkpoint

The earlier accepted software/proof-component source is
[maina534](https://github.com/ActiveInferenceInstitute/fep_formal/commit/a53456c0941443d698a5dd34ea61c78721e40282).
Its [exact-main workflow](https://github.com/ActiveInferenceInstitute/fep_formal/actions/runs/39687054068)
passed the full fifteen-cell installed-wheel profile and required software
jobs. Downloaded native/audit/render/source/font artifacts and scoped PDF
layout were independently accepted for that epoch. The
[changelog](CHANGELOG.md) records the bounded operator, readiness, canonical
query, historical named-pair runner, accessibility and finite-KL deliveries.
Current scientific primary execution, capture/archive, study reproduction and
optional provider lanes remain separate requirements in [TODO.md](TODO.md).
Later source edits require fresh evidence in the affected planes.


The earlier accepted PR201 software/proof-component checkpoint is
[`de9643f`](https://github.com/ActiveInferenceInstitute/fep_formal/commit/de9643f5249ad207219af51f6446327197a01247).
Its [exact-main run](https://github.com/ActiveInferenceInstitute/fep_formal/actions/runs/39449116181)
passed all 21 executed jobs and all 15 installed-wheel cells; the
documentation-only alternative was intentionally skipped. Independent artifact
checks accepted all 168 native topics, 1,928 declaration axiom reports within
the reviewed allowlist, and the 389-page manuscript. All seven changed pages
were directly reviewed; 382 others exactly matched accepted-head pixels/text.
The directory-alias repair and 498-line compatible CLI extraction are accepted;
At that checkpoint PKG-13 was closed and CORE-D2 still required independent
API/schema and semantic review; the later scoped acceptance is recorded above. Source-custody-only PR202 adds no theorem or algorithm claim.
Primary scientific and full-capture criteria remain separate.
The [publication handoff](WORK_STATUS.md) remains a dated snapshot.

The earlier accepted integrated checkpoint
[`bea6b9c5ed4dc5b978b314a69d041055be295e5e`](https://github.com/ActiveInferenceInstitute/fep_formal/commit/bea6b9c5ed4dc5b978b314a69d041055be295e5e).
Its exact-main [hosted run](https://github.com/ActiveInferenceInstitute/fep_formal/actions/runs/38825444108)
passed all 21 executed jobs, including all 15 installed-wheel cells; the
documentation-only alternative was intentionally skipped. Its tree is
identical to the independently reviewed `c1419e7` PR180 head and tested PR
merge. That [source-bound artifact set](https://github.com/ActiveInferenceInstitute/fep_formal/actions/runs/38819590194)
retains 2,952 Python passes, 20 skips, complete 2,972-case membership, all eight
browser/startup controls and 91.64% coverage. Serial Lean retained 588 passes
and five skips. The Lean/Mathlib 4.35.0 native receipt verified all 168 topics
without warnings or `sorry`; the audit resolved 1,875 declarations with 1,744
evidence entries and only the standard approved axioms. The actual accepted
388-page render passed all nine defect counters. These exact-source checks and
independent reviews retain the bounded G02/P02/T01/D02/D03 implementation
acceptance at `f5c39fe` and its documentation/Issue closure at `bea6b9c`, as
recorded in the [changelog](CHANGELOG.md). They do not close the broader G01/D04
scopes or qualify later source changes automatically.

This checkpoint establishes those source-specific hosted lanes. Production
seven-stage capture, local runtime/status acceptance and the frozen H3 study
retain their separate gates. The
[active implementation plan](specs/comprehensive-next-steps/README.md) reconciles
those gates and future work; it does not rebind historical receipts to later
source changes.

The maintained schema-2 roster spans `fep-001` through `fep-168` in 22
families. Canonical bodies are family-owned and formal resources are manifested
foundations/composition leaves behind an import-only aggregate. The generated
coverage and theorem-maturity projections own the live declaration, relation,
capability, import, and semantic-disposition totals. The current reviewed
maturity split is 149 formalized, 13 conditional proxies, and six structural
proxies. Satisfied capability nodes refer to their narrowed statements;
compilation cannot erase those boundaries.

The 2026-09-30 baseline at `cd4a84c` has independently validated hosted
native and declaration/axiom evidence at the v4.34.1 pin. Expanded local
native and H3 export checkpoints retain their exact source epochs. Receipt
currency must be checked against the live source; none of these observations
substitutes for final package or scientific acceptance.

The output/configuration checkpoint at `c99e933` has a successful
[exact-SHA hosted run](https://github.com/ActiveInferenceInstitute/fep_formal/actions/runs/37334643019):
all 15 distribution cells and Python, Lean and render jobs passed. Later owner
changes reopen dependent source-currency gates. The
[remaining acceptance](specs/comprehensive-science-improvement/NEXT.md)
owns current execution; failed probes and historical receipts retain their epochs.

The [Q7 source-pair capture](specs/comprehensive-science-improvement/evidence/public-q7-final-source-20261002-r1/summary.json)
passed all 12 stages and four closing checks, five-runtime scaffold parity and
124 pure controls at its recorded 2026-10-02 source epoch. Its exact native
receipt is separately validated for that epoch; runner execution remains
unverified. The separately reviewed
[2026-10-05 Q7 observation](specs/comprehensive-science-improvement/evidence/public-q7-current-source-20261005-r1/summary.json)
records a complete 2026-10-05 capture with twelve stages and four closing
checks against its recorded 291 native inputs. This closed the later Q7
source-pair requirement for that epoch without promoting any failed prefix or
historical native receipt. The observation is not itself a native receipt or
validation of this checkout; later source-owner changes require fresh source-pair
acceptance. Historical Q5/Q6/Q7 receipts and active GNN work remain preserved.
Catalog-native, package, hosted, provider and scientific acceptance remain
separate.

Fresh H2 custody and continuous G0 acceptance preceded the immutable H3.0
freeze. H3 model/composition proofs, exports and independent proof-role reviews
retain their recorded epochs. The frozen primary remains unopened until
current package and source-bound proof/export gates pass. Complete recovery,
negative controls, independent final claim review and clean-environment study
reproduction are mandatory; the empirical branch is governed no-go without
licensed data. The original nine program criteria remain binding.

The 2026-08-20 provider reports remain historical for their earlier source
snapshots. They cannot close ISA-06 or the provider-backed portion of ISA-07
for today's roster. A new full Hermes/OpenGauss receipt requires explicit
credential/spend authorization and independent live-source validation.

## Mathematical methods integration

The `1.6.0` release (2026-10-07) makes mathematical location operational: an
installed wheel can inspect every canonical topic contract, distinguish typed
relations from editorial affinities, query explicit family features, evaluate
bounded counterexamples, and export the same readable and visual model offline.
The manuscript must explain the carriers and transfer obligations behind those
associations, and publication figures must have deterministic producers and
build-local asset custody. Source-owner growth requires a coordinated roster
refresh; native/render receipts are acquired after the final source changes.
[The slice acceptance criteria](specs/openai-math-methods/INTEGRATION.md) own
concrete probes and failure cases. Topic count, semantic promotion, unchecked
upstream proofs and the unopened H3 study are outside this integration.
At release the model retained 1,946 lexical declarations (live totals belong to
the [generated coverage inventory](docs/formalism-coverage.md)), twelve upstream source
statements against 82 locked identities, and 34 comparison rows in 30 authored
coordinates. Its export has 17 products and thirteen SVGs. Confirmed local
evidence includes 112 focused mathematical tests, the final 168-topic native
receipt, and isolated installed-method checks on macOS Python 3.10.20,
3.11.15, 3.12.13, 3.13.16 and 3.14.4 with identical MDS projection hashes.
The final 385-page PDF passed version-2 receipt checks and independent
publication reviews. Supplement A has twelve cited figures, six captioned
tables and 55 numbered equations; all 1,315 manuscript display equations are
numbered. The complete non-serial Python suite passed 2,707 tests with nine
skips in 777.82 seconds and 91.50% coverage. The first full Python run
failed with 78 failures, 2,626 passes and nine skips. Focused fixture repairs
passed, retaining the original 80-case distribution matrix and security
assertions while migrating shared render fixtures to receipt version 2.
The final wheel's 193 package resources and the source archive's 338 regular
members passed source/metadata comparison. That exact wheel passed isolated
Python 3.14.4 installation, all 17 API/CLI exports, nonmutating checks and the
reference MDS digest. Prior acceptance retains its historical scope. The
[validation record](specs/openai-math-methods/VALIDATION.md) retains scope and
source identity; version publication still requires the separate hosted gate.

## Release boundary

`v1.6.0` (2026-10-07) is the current release of the 168-topic tree; later
formal-resource work is recorded under Unreleased in the changelog. Releases require only the
[release gate](docs/release.md): version/date agreement, a dated changelog
section and a green hosted CI run on the exact `main` commit. Research and
evidence lanes are reported, not claimed. Historical receipts do not cross this
boundary. Neither compilation nor provider execution establishes the FEP as a
physical theory.

Prior delivery checkpoints remain in the [W2 operations record](specs/gnn-bridge-w2-source-custody/REPORT.md), [wave-2 report](specs/gnn-bridge-w2-source-custody/WAVE2-REPORT.md), [Q5 proof record](specs/gnn-bridge-q5-artifact-proof/REPORT.md), [H2 audit](specs/done/horizon-2-smooth-stochastic/readiness/07-terminal-audit-20260904.md), and repository history. They retain their original source and verification boundaries. Completed delivery checklists do not belong in this active assessment.
