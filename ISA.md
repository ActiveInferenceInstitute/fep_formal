---
title: fep_lean Ideal State Assessment
status: active
phase: verifying
updated: 2026-09-07
---

# fep_lean Ideal State Assessment

## Problem

`fep_lean` combines a 155-row catalogue, generated Lean source, a pinned
Lean/Mathlib workspace, Hermes model calls, OpenGauss persistence, manuscript
projections, and strict run reports. The repository must distinguish a
deterministic offline catalogue from real theorem verification. A green local
command is only meaningful when its capability boundary and evidence are
explicit.

## Vision

A fresh checkout can reproduce the catalogue, acquire the exact declared Lean
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
- Exact Lean/Mathlib `v4.34.0` acquisition and compilation, plus a
  fail-closed audit against the newest stable release pair.
- Hermes, OpenGauss, SQLite session lifecycle, report provenance, and generated
  manuscript artifacts.
- Documentation links, cross-references, pinned dependency claims, and this
  repository's operator contracts.

## Out of scope

- Publishing, pushing, or merging changes to GitHub.
- Changing the parent HumOS repository or any sibling repository.
- Treating catalogue mode, a cached response, or a generated manuscript value
  as proof that a theorem was verified.
- Printing, inventing, or storing provider credentials.
- Making mathematical claims stronger than the source theorem statements and
  the compiler evidence support.

## Ideal-state criteria

| ID | Criterion | Required evidence |
| --- | --- | --- |
| ISA-01 | The sealed topic roster and family registry are complete and parity-safe. | Registry/SSOT tests pass; the aggregate generator is deterministic and leaves no diff. |
| ISA-02 | Offline mode is deterministic and honest. | `uv run fep-lean catalogue` completes, emits reproducible artifacts, and reports `verified_topics: 0`. |
| ISA-03 | The local Python boundary is reproducible. | `uv sync --locked --extra dev`, `uv pip check`, the coverage gate, and `uv run mypy src` pass. |
| ISA-04 | The pinned Lean workspace is real, not merely configured. | Direct pinned Lean/Lake version probes, Mathlib cache/build, `lake build FepSketches`, an exact sealed-roster native compile sweep, and the declaration/axiom audit pass. |
| ISA-05 | Full mode is fail-closed. | Preflight requires Gauss, writable state, exact Lean/Lake/Mathlib, and Hermes credentials; any failure returns an error without a successful report. |
| ISA-06 | The live full path is end-to-end. | A permitted Hermes provider answers a bounded smoke run, OpenGauss persists and closes sessions, Lean verifies each selected topic, and the report/manifest agree. |
| ISA-07 | Reports are provenance-safe. | Selected-topic identities and denominators, source/config and compiled-source digests, the preserved Lean declaration contract, toolchain revision, nested artifact hashes, verification source, and completion state are internally consistent. |
| ISA-08 | Generated manuscript projections use the requested output root. | A custom output-root run cannot consume a stale report from the default `output/reports` tree. |
| ISA-09 | Operator documentation matches behavior. | Link, Markdown hygiene, pin, and cross-reference audits pass after catalogue generation; counts and setup commands are current. |
| ISA-10 | Every primary theorem proxy has a non-vacuity and assumption-strength review on record. | `config/theorem_maturity.yaml` has a `non_vacuity` field for every topic, and the generated `docs/theorem-maturity-audit.md` renders it. The `non_vacuity` entry documents whether the statement has a real witness or is structural/vacuous; topics with `non_vacuity: structural` or `non_vacuity: witnessed` are accepted; topics missing the field are flagged. |
| ISA-11 | Scientific relations and capability history are explicit. | The typed loader validates every authored edge, every gap row has a `blocked_by` edge, derivational `formal` edges are acyclic, both theorem-backed kinds resolve leaf-owned declarations that use both endpoints, `formal_pairing` does not imply dependence, capability evidence resolves, and shared imports are reported separately. |
| ISA-12 | Manuscript claims fail closed. | Theorem-reference, bibliography/citation, placeholder, receipt, and source-to-build rendering audits pass; authored Markdown is never modified by rendering. |
| ISA-13 | Formal breadth and depth are inspectable without a second semantic source. | Coverage JSON/Markdown and the offline SVG/HTML atlas are deterministic projections of the same canonical join, conserve every node/edge, and pass drift/accessibility tests; the numerical dashboard independently renders every typed family witness and preserves its non-proof evidence label. |

## Anti-criteria

The repository is not in the ideal state if any of these occurs:

- catalogue mode reports a verified topic or full mode reports success after a
  failed capability check;
- a generated aggregate, report, or manuscript projection is treated as an
  authoring source of truth;
- setup silently accepts the wrong Lean version, a partial Mathlib checkout, or
  a failed build;
- a report calls failed Hermes rows `hermes_refined`, uses the full catalogue
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
uv run fep-lean atlas --check
uv run fep-lean dashboard --check
uv run python docs/pin_audit.py --check-latest
uv run mypy src
uv run fep-lean setup
cd lean
lake build FepSketches
cd ..
uv run fep-lean verify --fail-on-warnings --receipt output/native-verification.json
uv run python scripts/audit_formalisms.py --receipt output/formalism-audit.json
uv run fep-lean catalogue
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
  --output "$release_dir/fep-lean-1.1.0-155.tar.gz"
SOURCE_DATE_EPOCH=0 uv run python scripts/build_release_bundle.py \
  --check --output "$release_dir/fep-lean-1.1.0-155.tar.gz"
uv run fep-lean preflight
```

`preflight` reports the external full-mode capability boundary. A complete
local assessment must also run the direct Lean gate and the bounded full
workflow after credentials are supplied through the operator's existing secret
mechanism:

```bash
FEP_LEAN_CATALOGUE_COMPILE_TEST=1 uv run pytest tests/test_catalogue_bodies_compile.py -q --no-cov
uv run fep-lean run --topic fep-001
uv run fep-lean run
```

The smoke run is accepted only when its result is `complete: true`; the full
run is accepted only when all selected topics are cleanly verified and the
report's verification manifest agrees with the result. If credentials are not
available, record the exact preflight failure and leave the full-run criterion
open in [TODO.md](TODO.md).

## Current assessment

The maintained schema-2 roster now spans `fep-001` through `fep-155` in 20
families. Canonical bodies are family-owned and merged by one validated
registry; formal resources are split into manifested foundations and leaf
composition modules behind an import-only aggregate. The generated coverage
and theorem-maturity projections own the live declaration, relation,
capability, import, and semantic-disposition totals. The maturity ledger
contains direct formalizations as well as conditional and structural proxies;
compilation cannot erase those reviewed boundaries.

ISA-04 was closed for the frozen v1.1.0 155-topic release snapshot. Its exact
sealed-roster native, schema-4 declaration/axiom, schema-3 Python, and schema-4
Chrome receipts remain historical evidence for those bytes. The accepted
post-v1.1.0 Horizon 1/Horizon 2 and publication source wave changes formal
resources, tests, manuscript inputs, and the source-owner roster, so none of
those retained receipts currently binds the live checkout.
The coordinated refresh completed deterministically on 2026-09-12 after the
source wave settled (recorded in [CHANGELOG.md](CHANGELOG.md)); neither a
stale nor a refreshed receipt changes a maturity disposition.

The three provider reports created on 2026-08-20, including
`output/reports/run_20260820_183143_709998`, remain historical evidence for
their recorded 50-topic source snapshots. They cannot close ISA-06 or the
provider-backed portion of ISA-07 for the current 155-topic source. A new full
Hermes/OpenGauss receipt must pass independent live-source validation before
its results are described as current. No provider secret is stored in the
repository. Neither compilation nor provider execution establishes the FEP as
a physical theory or authorizes publication.

## Release boundary

The current source owns the 155-topic roster and the formal resources described
above, but the retained native, formal-declaration, trusted-axiom, Python, and
browser receipts do not validate these live bytes. Those current-source
evidence claims were re-bound by the coordinated refresh completed
deterministically on 2026-09-12 (recorded in [CHANGELOG.md](CHANGELOG.md)).
The repository also
does not support a current 155-topic provider claim until ISA-06 and the
provider-backed parts of ISA-07 have fresh evidence for these exact bytes.
Historical receipts remain useful provenance but do not cross that boundary.
The final worktree must be inspected, its release receipts must validate, and
published artifact bytes must match their recorded hashes before any release
is accepted.

## Coordinated reliability and artifact-proof delivery (2026-09-04)

### Goal

Deliver reliable model/run outcomes, read-only content-bound bridge checks,
and concrete PyMDP artifact proofs, preserving existing fleet changes.

### Criteria

- [x] BRIDGE-OPS: new bridge operations regression suite passes.
- [x] GNN-VALIDITY: current invalidity propagates across validation entry points.
- [x] GNN-ROUNDTRIP: annotated connections survive JSON/Markdown round trips.
- [x] GNN-RECEIPTS: retries and changed inputs do not inflate current outcomes.
- [x] GNN-API: both APIs agree on warning exits and reject active deletion.
- [x] GNN-MCP: transport behavior has functional PR tests.
- [x] PROOF-PAYLOAD: a current rendered PyMDP artifact and an independent
  asymmetric control have checked concrete payloads.
- [x] PROOF-NEGATIVE: literal/axis/artifact/custody mutations reject acceptance.
- [x] H2-AUDIT: existing H2.7 source is audited against its review gates.
- [x] Anti-CURRENT: no stale numerical artifact is promoted to native proof or
  current execution evidence.
- [x] Anti-WORKTREE: baseline unrelated changes remain intact.

### Verification strategy

Use repository-native focused tests followed by full applicable gates. Source
snapshots were captured before edits under `/tmp/gnn-fep-implementation-20260904`.
Full baselines were attempted and interrupted in native dependency checks amid
pre-existing fleets; logs retained under `/tmp/gnn-fep-*-baseline.log`.
Focused fep_lean baseline: 65 passed (CLI/formal composition/native evidence).
GNN focused baseline and subsequent regression results must be reported with
exact scope. No baseline aggregate pass is inferred from partial progress.

### Ownership

Codex validation lane: parsers/validation/CLI. Codex receipt lane: API/MCP/render/
execute. Omp: concrete artifact-proof slice. Parent: bridge operations, contract,
source pins, ISA and integration. Generated owners settle before receipt refresh.
No publication, paid provider runs, or H3 execution is authorized by this slice.

### Verified delivery

The coordinated delivery criteria above are complete. Evidence:

- GNN applicable suite: 2,102 passed, one unavailable-PyTorch skip, 277 slow/
  pipeline deselections. Twelve additional actual HTTP/auth socket tests passed.
  Full source Ruff and strict documentation audit pass.
- FEP full nonserial baseline: 1,159 passed, seven skipped, 523 native-marked
  deselections in 760.17 seconds. That run initially missed coverage at 88.34%.
  All 82 added failure-contract tests then passed in 4.02 seconds with
  `--cov=src --cov-append --cov-fail-under=89`, bringing combined coverage to
  **89.19%**. All 77 production Python files stayed byte-identical across those
  runs. This records a full baseline plus the additional tests, not a claimed
  second full-suite run. Logs: `/tmp/gnn-fep-fep-python-final.log` and
  `/tmp/gnn-fep-contract-coverage-final.log`.
- Q5: current actual canonical render, two concrete native probes, six standard-
  axiom theorem checks, and three passing native regression tests including a
  normalization-preserving wrong-axis rejection. The asymmetric control is
  handcrafted; only the symmetric fixture has current render provenance.
- H2 terminal audit: seven direct terminal tests, sixteen R0 tests including
  three native probes, and two final prerequisite/custody checks passed.
  Overall H2 acceptance remains open; this audit does not open H3.
- Ten actual read-only bridge/Q5 checks preserved all fifteen watched artifacts'
  bytes and mtimes. Numerical comparisons keep current-execution verification
  and native-claim readiness false. The separate native Q5 receipt validates.
- Eight source projections, manuscript projection/placeholder checks, Markdown
  hygiene and manuscript references pass. Strict typing passes for ten bridge
  and verification files. Both repository diffs pass whitespace checks.

At the wave-1 checkpoint, the source-bound native receipt and source pin were
current. Baseline files were preserved, the pre-existing FEP W1 REPORT is byte-identical to its initial
snapshot, and neither repository HEAD changed. Later backend proofs, continuous
semantics, wider H2 acceptance, H3, current-release/provider evidence, and
publication retain their independent acceptance boundaries.

Detailed evidence: [W2 operations](specs/gnn-bridge-w2-source-custody/REPORT.md), [Q5 proof](specs/gnn-bridge-q5-artifact-proof/REPORT.md), and [H2 audit](specs/horizon-2-smooth-stochastic/readiness/07-terminal-audit-20260904.md). The broader release criteria elsewhere in this ISA remain open.

## Comprehensive continuation (2026-09-04, wave 2)

User-authorized wave-2 implementation and verification are complete. Prior evidence above describes the
wave-1 bytes; subsequent changes require fresh source-bound checks. Worktree
snapshots and baseline logs are retained under
`/tmp/gnn-fep-comprehensive-wave2-20260904`. Existing work remains preserved.

### Acceptance criteria

- [x] W2-GNN-QUALITY: declared GNN test scope, full typing, lint and format pass.
- [x] W2-GNN-RUNS: source/config/artifact identity governs hashing, resume and reproduction.
- [x] W2-GNN-CONTAINERS: reviewed container settings survive composition and paths reject unsafe aliases.
- [x] W2-CONTINUOUS-ROUTE: public continuous dispatch and JAX output routing pass actual regressions.
- [x] W2-Q6: actual Julia embedded input tables have positive and wrong-axis native evidence.
- [x] W2-Q7: actual OU coefficients have source-bound exact-real error-bound evidence.
- [x] W2-RECEIPTS: shared immutable contract verification preserves tamper and checked-byte safeguards.
- [x] W2-H2-DIAGNOSTICS: scalar and Fin4 diagnostics use the existing typed witness registry.
- [x] W2-H2-EXIT: mandatory predecessor/native results, diagnostics and three fresh reviews validate together.
- [x] W2-H3-G0: eligibility checks the accepted H2 carrier and preserves prospective study boundaries.
- [x] W2-FEP-QUALITY: relevant full Python gates and native additions pass with exact exclusions reported.
- [x] W2-DOCS: current architecture/status and reviewable evidence match final code.
- [x] Anti-W2-CLAIMS: static proofs do not imply runtime, empirical or whole-program equivalence.
- [x] Anti-W2-CUSTODY: receipt regeneration is explicit; stale or edited evidence fails closed.
- [x] Anti-W2-WORKTREE: unrelated baseline files and repository HEADs remain preserved.

Native Lean/Lake commands are serialized. New FEP implementations are drafted
outside the source trees until the frozen-source baseline settles. GNN's full
applicable baseline completed with 4,028 passes, 11 skips, 557 deselections and
two failures; those failures and the full typing findings are implementation
inputs. Publication and paid provider execution are outside this continuation.

### Wave 2 GNN verification checkpoint

The integrated GNN run (`-m 'not pipeline and not mcp'`) completed with
4,157 passes, 18 skips, 557 deselections and one UV environment-check failure.
All 2,870 captured source/workspace files were unchanged during the run. The
failure was an exact-sync check rejecting the concurrent GEO lane's optional
`h3` package. Its documented non-pruning contract now uses `--inexact`; all
35 tests in that environment file pass, with required dependencies still
checked. This is the full run plus a scoped repair/recheck, not a second full
run. Full typing (986 files), Ruff, formatting and four strict documentation
audits pass; the changed environment test also passes typing and lint.

Additional evidence includes 128 independent durable-run/pipeline tests,
13 OpenAI synchronous-call tests, and 102 tests with optional scikit-learn
present. Deserialization rejects cached pickle extension opcodes and trailing
payloads at the shared GNN loader and the restricted classifier loader.

The following final checkpoint supersedes the preceding in-progress status.

### Final wave-2 checkpoint

All wave-2 criteria above are verified. FEP's clean integrated Python run passed
1,460 tests with seven skips, 529 native deselections, and 89.83% coverage.
The frozen full native baseline and enabled Fin4 supplement passed. Q5/Q6/Q7
schema-2 receipts validate 23 standard-axiom theorem reports. H2.7 acceptance
binds 328 mandatory cases, 180 source hashes, independent diagnostics, and three
fresh reviews. All 15 retained checks preserve 559 files' bytes and mtimes.

H3.G0 machinery is implemented and tested; actual prospective study metadata
remains unselected. No G0 study acceptance or H3.0--H3.7 execution is claimed.
Broader release/provider criteria elsewhere in this ISA remain independent.

Detailed changes, exact test scopes, repairs, and evidence: [wave-2 report](specs/gnn-bridge-w2-source-custody/WAVE2-REPORT.md).
