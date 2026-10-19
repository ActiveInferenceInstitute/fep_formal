# Development guide

## Setup

```bash
uv sync --locked --extra dev
uv run python -c "from fep_lean.catalogue import FEPTopicCatalogue; print(len(FEPTopicCatalogue.default().topics))"
```

The distribution uses a single `fep_lean` namespace under `src/fep_lean/`.
Do not add `PYTHONPATH` shims or import obsolete top-level modules such as
`catalogue` or `pipeline`; the isolated-wheel test enforces this boundary.

## Canonical authoring graph

- `config/catalogue_metadata.yaml`: stable topic metadata and Mathlib hints.
- `config/theorem_maturity.yaml`: semantic review and primary theorem.
- `config/formalism_novelty.yaml`: expansion-row nearest topics, carrier delta,
  invariant, and required composition bridge.
- `config/formalism_relations.yaml`: explicit derivational formal,
  non-implicational formal-pairing, conceptual, and blocker relations plus
  retained capability status/evidence.
- `src/fep_lean/catalogue/bodies/*.py`: family-owned canonical Lean bodies;
  `registry.py` validates their sole ordered union and `latex.py` derives
  theorem signatures.
- `src/fep_lean/formal/`: reusable finite and measure-theoretic foundations plus
  exact cross-topic proofs; `manifest.py` owns foundation, leaf-composition,
  and aggregate roles.
- `config/topics.yaml`, packaged `src/fep_lean/data/topics.yaml`, aggregate
  Lean, maturity audit, and coverage files: generated projections.

Every body keeps its `namespace FEPNNN ... end FEPNNN` wrapper and may declare
the narrow Mathlib imports it needs. Generated aggregate wrappers add a second
topic namespace to prevent helper collisions.

## Change loop

```bash
uv run python scripts/_maint_build_topics_catalogue.py
uv run python scripts/_maint_build_fep_all_lean.py
uv run python scripts/_maint_build_formal_modules.py
uv run python scripts/theorem_maturity_audit.py
uv run python scripts/build_formalism_coverage.py
uv run fep-lean atlas
uv run fep-lean dashboard
```

The required verification list (`--check` gates, audits, tests, lint, native
Lean) is owned by the "Required checks" block in
[`AGENTS.md`](../AGENTS.md#required-checks); it is not repeated here, and
`tests/test_check_inventory.py` keeps it in step with `.github/workflows/ci.yml`.

Native Lean acceptance (`lake build FepSketches`, `fep-lean verify`, the
formalism audit) is the expensive semantic compiler boundary; its commands are in the same
[required-checks block](../AGENTS.md#required-checks).

The native receipt establishes exact-source compilation for the stable topic
roster; the formalism audit separately covers the maintained formal modules
and reviewed declarations. A credentialed full run remains a distinct gate:

```bash
uv run fep-lean preflight
uv run fep-lean run --topic fep-001
uv run fep-lean run
```

Never inject credentials into source, tests, or generated evidence.

## Package boundaries

| Area | Path | Contract |
| --- | --- | --- |
| Catalogue | `src/fep_lean/catalogue/` | typed authoring, loading, audits, coverage |
| Formal kernel | `src/fep_lean/formal/` | reusable finite carriers, cross-topic proofs, and exact Lake projection |
| Bridge | `src/fep_lean/bridge/` | typed cross-repository interchange, AST analysis and custody validation |
| Custody | `src/fep_lean/custody/` | census, staged refresh and bounded orchestration |
| Methods | `src/fep_lean/methods/` | portable mathematical contracts, positioning and transfer diagnostics |
| Verification | `src/fep_lean/verification/` | read-only capability probes, Lean subprocesses, declaration/axiom audit |
| Hermes | `src/fep_lean/llm/` | provider request, retry, and response validation |
| Sessions | `src/fep_lean/gauss/` | SQLite ownership and per-topic runner |
| Pipeline | `src/fep_lean/pipeline/` | strict `catalogue`/`full` orchestration |
| Output | `src/fep_lean/output/` | receipts, reports, figures, rendering, atlas, and numerical witness dashboard |

Use type hints on public APIs, immutable dataclasses for source records,
structured results at subprocess/network boundaries, and temporary paths in
tests. Preserve catalogue, native, and full-run evidence as separate types and
claims.

For theorem ownership, support conventions, the validation ladder, and the
limits of numerical witnesses, see
[formal-kernel methods](formal-kernel-methods.md).

## Roster expansion

The current schema deliberately seals a reviewed, family-partitioned roster.
Adding another topic is a policy/schema change, not a YAML append. It requires
updating the roster seal and family metadata, semantic record, canonical body,
novelty record and composition bridge, generated projections, registry and
coverage tests, and manuscript review together. A new ID is not accepted until
that scientific review and its native acceptance plan are explicit.

## Source-owner roster expansion

The report and native receipts bind a versioned owner roster
(`SOURCE_OWNER_ROSTER` in `src/fep_lean/output/provenance.py`), not a
recursive checkout snapshot. Adding a file under `src/fep_lean/**/*.py` or
`scripts/*.py` fails receipt validation fail-closed until the file is
reviewed into the roster and `OWNER_MANIFEST_VERSION` is bumped. The bump
orphans every retained receipt that pins the previous version, so roster
growth is a coordinated evidence refresh (the completed refresh is recorded
in [CHANGELOG.md](../CHANGELOG.md); a further roster change re-opens the
requirement), not a per-PR append. Per-PR alternatives: fold the new code
into an existing
rostered owner (the status verb lives in `cli.py`), or keep tooling
slice-local under `specs/`, which is not rostered.

See [authorship-guide.md](authorship-guide.md), [testing.md](testing.md), and
[troubleshooting.md](troubleshooting.md).

## Interpreter contract

`requires-python = ">=3.10"` declares the packaging floor. CI tests fresh
installed wheels on CPython 3.10, 3.11, 3.12, 3.13, and 3.14 on Ubuntu, macOS,
and Windows. Each target environment resolves the wheel's declared runtime
dependencies, imports the public API and catalogue, verifies every packaged
Lean/YAML resource against the built sources, and exercises the console script
outside the checkout. It has no editable install, parent site-packages,
`PYTHONPATH`, or `PYTHONHOME`. This matrix is a package compatibility gate;
its hosted results, rather than the declared floor, supply platform evidence.
Future Python versions and alternate interpreters remain untested.

Build distributions with `uv build --out-dir dist`. Its default route builds
a source distribution first, then a wheel from that fresh source distribution.
A direct `--wheel` build can retain deleted modules or Lean resources in an
existing setuptools `build/lib` tree. Acceptance compares the exact Python,
Lean and YAML member roster and bytes in both the archive and installed
namespace; merely finding the expected resources is insufficient. The private
cache regression retains orphan files and checks both build routes.
See the [uv build contract](https://docs.astral.sh/uv/concepts/projects/build/).

The development and evidence harness remains pinned to CPython 3.14 by
`.python-version`; mypy also targets 3.14 in `pyproject.toml`.
Installed-package compatibility does not extend the validator contract.
Q7's `scaffold_digest` uses the reviewed canonical
AST serialization and accepts evidence validation only on CPython 3.14.
Unsupported validator interpreters refuse before parsing with a
`ContinuousArtifactError` naming the accepted set and running interpreter.
The wheel matrix exercises that
refusal on 3.10--3.13, alongside the canonical serializer's actual byte parity
across 3.10--3.14. See the
[serialization protocol](../specs/gnn-bridge-q7-continuous-ou-proof/scaffold-serialization.md).
That static parity does not extend validator acceptance or replace the new
source-bound native/custody capture required by a serializer change. The retained
2026-10-02 isolated Q7 capture established five-runtime parity for the
56,968-byte scaffold and native acceptance at that source epoch; see the
[Q7 report](../specs/gnn-bridge-q7-continuous-ou-proof/REPORT.md).
Its native receipt covers static coefficient statements and leaves runner
execution unverified. The separately reviewed
[2026-10-05 Q7 observation](../specs/comprehensive-science-improvement/evidence/public-q7-current-source-20261005-r1/summary.json)
records the complete 2026-10-05 source-pair capture, including five fresh
parser/serializer probes, all 124 pure controls and its separate native
receipt for its recorded 291 inputs. This closed the later Q7 requirement for
that epoch; later owner or serializer changes require their own acceptance.
The public observation is not itself a native receipt or validation of this
checkout. Historical Q7 JSON, Q5/Q6 observations and failed attempts retain their
original epochs. No parser/serializer control establishes generated-runner
execution.

To exercise a target runtime locally while keeping the harness pinned:

```bash
FEP_DISTRIBUTION_PYTHON=3.10 \
  uv run --locked python -m pytest tests/test_distribution.py -q -s --no-cov
```

The target interpreter must be available to uv; runtime dependencies may be
acquired from the package index. No Lean compile or provider call occurs.

Installed-wheel observations retain their exact guarded source epochs. Each
local cell reports an actual installed target-runtime case separately from the
CPython 3.14 harness cases. The hosted run at `c99e933` passed all 15
Ubuntu/macOS/Windows Python 3.10–3.14 cells. Later source changes require fresh
acceptance; POSIX controls alone do not establish Windows behavior. The
[remaining acceptance](../specs/comprehensive-science-improvement/NEXT.md)
owns current source freezes, actual collection, and package/render gates.

## Documentation PRs and retained renders

Documentation-only pull requests run the documentation lane before merge.
The allowlist covers root Markdown and prose under `docs/`; changes to the
canonical manuscript, receipts, fonts, generated scientific projections,
workflows, or any other owner take the full gates. A source deletion or rename
out of an owner path also takes the full gates. Main pushes retain the complete
integration workflow.

The documentation lane materializes the generated manuscript inputs, then
checks catalogue/formal projections, font requirements, the committed render
receipt, links, Markdown hygiene, theorem references, citations, and
cross-references. Font requirements are source projections; installed-font
coverage is checked by the real render lane. Prose checks run no native build
and neither manufacture nor overwrite an acceptance receipt.

A successful render retains an `accepted-render-<commit>-<attempt>` artifact
for 90 days. It contains the combined PDF, TeX, Markdown and compiler logs,
accepted render receipt, font projection, native/declaration receipts,
renderer/tool versions, template commit and tracked template input hashes,
selected-font file hashes, a source manifest, and an artifact hash manifest.
Staging freezes the accepted output bytes, brackets validation and tool/font
discovery with source, output, template and font comparisons, and verifies the
retained copies against that frozen snapshot. Authored manuscript membership
is rechecked after reading the last source. Missing outputs, source drift, a
different checkout SHA, a stale/rejecting receipt, or a changed retained copy
rejects staging and removes its partial directory. Failed renders produce no
accepted artifact.

The version-2 render receipt binds manuscript sources, cover configuration,
bibliography and acceptance findings;
it does not itself contain a PDF hash. The retained artifact manifest binds
the PDF bytes kept by this stable staging interval. Neither record establishes
an atomic filesystem snapshot or substitutes for a physical render.

Download retained evidence into a separate temporary directory. Verify its
commit against the intended workflow SHA, every file hash against
`artifact-manifest.json`, and every source hash against the live checkout and
its generated inputs. Re-run the native/audit/render receipt validators on
those exact files before treating them as current. A green workflow or matching
filename does not authorize replacing committed receipts or publishing; release
bundle validation and the explicit publication boundary still apply.

## Custody refresh orchestration

`uv run fep-lean custody <census|apply|refresh>` is the H2.7 custody machinery adapter.
`census` is a read-only drift report; `apply` performs one staged 14-phase run into
`--output-dir` (required, staged-only) with no repo-side writes; `refresh` composes
the guarded refresh loop.

`refresh` modes are mutually exclusive:

| Mode | Contract |
| --- | --- |
| default | census → strict verify gate (`GATE_EXPECTATIONS`) → one staged 14-phase `apply` into `--output-dir` (default fresh temp dir) → read-only verify set → pre-capture owner gate → optional `--native` capture. Zero repo-side writes; the staged tree and replacement directives are coordinator inputs. |
| `--plan` | Read-only planning pass. No test/audit subprocesses (no pytest, no formalism audit, no writers; read-only git probes only). Writes a plan journal and stops; state `planned`. |
| `--fixpoint` | Bounded staged fixpoint over the same 14-phase order (H3 lockstep last). Requires `--output-dir`. Terminal state `awaiting-commit`. |
| `--resume <journal-dir>` | Resumes only against a committed tip. Validates the commit is the agreed candidate, then completes evidence at that tip. Terminal state `captured` (or `awaiting-render-acceptance`). |

`--plan` refuses on: missing/empty `--reason`, dirty tree, unknown owners (`report_owner_errors`
non-empty), live-red census records, staleness outside `--authorized`, pin/toolchain mismatch,
and an authorized change path outside the reviewed source owners (no roster auto-growth).

`--fixpoint` rounds read the previous round's staged candidate (staged specs
tree plus projected directive bytes, carried into the next round). Default
bound 4 rounds (`--max-rounds`); a repeated non-terminal state hash stops as a
cycle; non-convergence at the bound stops. Convergence requires zero mutations
and zero directives in a round plus a byte-identical re-application into a
throwaway directory. The journal records per-round inputs, outputs, and state
hash, and classifies receipt re-issues as dependency re-binds, not new
execution evidence, preserving sealed historical observations. A denied census
is a stop requiring adjudication, never a rewrite.

`--resume` validates: clean tree, HEAD past the journal's pre-commit HEAD, committed bytes of
every changed path matching the journal's expected post-commit digests, clean owner snapshot,
census/gate green at the new tip, and one verification apply round with zero mutations and
zero directives (otherwise the commit is not the agreed candidate — stop). Journal paths
touching manuscript/render inputs (`manuscript/`, `src/fep_lean/output/rendering.py`,
`scripts/render_publication.py`, `scripts/render_manuscript.py`, `docs/`) stop at the
render-acceptance barrier with state `awaiting-render-acceptance` before any capture.
Otherwise the full verify set runs at the committed tip — the mode where the writer step
`scripts/audit_formalisms.py --receipt output/formalism-audit.json` legitimately runs —
then, with `--native`, exactly one sanctioned `fep-lean verify --fail-on-warnings` capture
to `output/native-verification.json`, independently validated by
`validate_native_lean_receipt` to `native_claim_ready`, with post-capture dirty/HEAD/owner
rechecks.

Journals live under `output/custody-journal/<operation-id>/journal.json` (`--journal-dir`
overrides); `--reason` is mandatory for every refresh mode. Bridge pin cycles, commits,
pushes, roster growth, and GNN-side writes are coordinator-owned, never performed here.
Native and bridge evidence is never claimed from focused tests alone; the coordinator
runs the full battery at the integrated tip.

Phase 0 correctness: a nonzero native capture exit, a missing, stale, or non-claim-ready
receipt, or post-capture drift refuses with exit 1 (the historical exit-0 `ok` behavior is
fixed). Exit codes: 0 = report composed / fixpoint converged / resume completed; 1 = any
gate or fail-closed check refused (JSON `{"status": "error", ...}`).

## Bounded publication capture

`fep-lean publication-capture` is an explicit local capture action. Planning
reads the checkout and an explicitly selected rendering template without
starting tools or writing a journal. Run `fep-lean catalogue` first so the
paired generated manuscript members exist; capture refreshes their values
after native acceptance:

```bash
uv run fep-lean publication-capture --template /path/to/template --plan
```

Capture runs native verification, formalism audit, render, Python, numerical,
browser and release-bundle owners. Accepted native verification refreshes the
paired manuscript variables and appendix plus the collection cache. Rendering
binds those projections; Python waits for the accepted render and binds the
final variable bytes. Browser waits for render/numerical acceptance,
and the final stage requires all six. It builds two independent archives,
strictly validates each against live inputs and requires byte equality.

The rendered tree owns exact raw copies of `manuscript/config.yaml`,
`manuscript/preamble.md` and `manuscript/references.bib`. These are metadata,
not counted or substituted chapter bodies. Hydration stages their bytes with
the chapters and assets; strict publication requires all three canonical
inputs and output copies, compares their exact bytes, and rejects unexpected
members. Capture declares each output and bundles require its recorded payload.

```bash
uv run fep-lean publication-capture --template /path/to/template \
  --journal /tmp/fep-publication-capture --source-date-epoch 0 --timeout 21600
uv run fep-lean publication-capture --template /path/to/template \
  --journal /tmp/fep-publication-capture --source-date-epoch 0 --timeout 21600 --resume
```

For the current governed production attempt, the
[execution sequence](../specs/comprehensive-science-improvement/NEXT.md) requires
the original caps and no-resume policy. These general CLI examples describe
available functionality; they do not change that reviewed attempt contract.

The journal must be a new directory outside the checkout. Existing producers
retain their declared project output paths; the manager preserves prior and
new artifact bytes in numbered immutable attempts, including partial outputs
and rejecting streams. Each attempt records exact inputs before and after,
process outcomes, output hashes and the policy hash. Resume checks all retained
history before starting a tool. Changed inputs or live outputs rerun the stage
and its descendants; independent unchanged stages still run their strict owner
checks before reuse. A rejected reuse check and its replacement capture share
one stage budget, within the overall deadline.

The policy seals the regular-file membership of consumed test, manuscript and
template trees. Template resources include style, class, bibliography, browser
and image assets. Only `.git`, `.venv`, `__pycache__`, `.pytest_cache`,
`.mypy_cache`, `.ruff_cache` and Python bytecode are excluded. Added or removed
members refuse an existing frozen plan; generate a new plan and journal after
reviewing the changed roster. Undeclared symlinked inputs, destinations and
journal history refuse capture. Template links are explicitly recorded with
their exact raw targets: internal targets must be direct canonical resources
outside excluded cache subtrees, with their consumed files sealed as inputs.
Relative targets allow only a bounded leading run of `..` within the owner,
then ordinary components. Empty, dot and later parent components refuse.
The single external registration `projects/active/fep_lean` must point exactly
to the selected project root. Descriptor-relative metadata checks compare the
actual link referent with its canonical target by device, inode and type, and
bind that identity into snapshots. Link identity and owned ancestor directories
are checked around execution; directory membership remains sealed. Content
edits with the same roster can resume selectively.

Capture execution requires POSIX descriptor-relative file custody and the
cooperative process supervisor. File-content reads, new journal files and
directory creation use no-follow descriptor traversal; declared link referents
are checked through metadata only. Timeout logs retain exact raw bytes; completed
process logs encode the runner's normalized text output as UTF-8.
Windows package imports, resources, help and static readiness remain supported.
Windows capture execution refuses before creating a journal or starting a
process. Equivalent Windows file custody and descendant supervision need a
separate implementation and runtime acceptance.

Exit 0 reports completed local capture. It performs no publication, hosted CI
or provider action. The [operator support table](cli-reference.md#operator-support-and-exit-contracts)
compares inspection, compiler and capture contracts. `status` remains a separate
process-free inspection. The
custom Python capture API records its declared checks and does not establish
the strict production evidence contract merely from zero process exits.
