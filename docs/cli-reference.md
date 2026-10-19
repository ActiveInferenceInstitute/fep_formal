# CLI reference

The only public command is `fep-lean`.

`methods` supports portable installed resources and numerical inputs without a checkout. The other
substantive commands are source-checkout-bound and reject a
`site-packages` ancestor or incomplete directory with a structured error. Use
`fep-lean --project-root /path/to/fep_formal COMMAND` when the current process is
outside the checkout.

```text
fep-lean setup       Acquire and build the pinned Lean workspace.
fep-lean preflight   Run read-only full-mode capability checks.
fep-lean verify      Compile canonical catalogue bodies with Lean only.
fep-lean catalogue   Generate deterministic offline artifacts.
fep-lean atlas       Generate or drift-check the offline formalism atlas.
fep-lean dashboard   Generate or drift-check finite numerical witnesses.
fep-lean run         Execute Hermes, Lean, and SQLite verification.
fep-lean topic ID    Execute one topic in full mode.
fep-lean report      Generate the offline catalogue report.
fep-lean bridge      Inspect, pin, emit, certify, or verify GNN bridge custody.
fep-lean status      Read-only evidence-currency report over existing checks.
fep-lean methods     Analyze portable mathematical contracts and visualizations.
fep-lean custody     Census, staged apply and guarded custody refresh.
fep-lean publication-capture  Plan or run bounded publication evidence capture.
```

`bridge` operates on an explicit sibling GNN checkout (`--gnn-root PATH` is
required for every verb). The current bridge surface is contract v0.6;
`verify-document` was added in contract v0.5. `status`,
`verify-certificate`, and `verify-document` are read-only; `pin` and `emit`
write receipts; `certify` writes one only with `--receipt PATH` and is
read-only without it. `certify` requires `--results PATH` -- the executed
results JSON under the FEP_Formal checkout -- and `verify-certificate`
requires `--receipt PATH`. `--model {finite,continuous}` (default
`finite`) selects the model family for `emit` and `verify-document`.
`verify-document --document PATH` checks one emitted GNN document against
the `FEP.GnnDocument` typed surface (syntax + `WellFormed`);
`--fail-on-warnings` treats verify-document warnings as failures. For
`emit` only, `--check` checks emitted bytes without writes and
`--refresh-digests` rewrites only permitted Signature custody fields.

`status` composes the existing fail-closed checks into one read-only
evidence-currency report: catalogue projection drift, render-receipt
defects, bridge source-pin binding, and native-receipt validation. It
accepts an optional `--gnn-root PATH` for the full two-sided pin comparison
and prints the report as JSON. Every section carries its capability
boundary; exit 0 means the report composed, not that the evidence is
current.

For a generated report bundle, the read-only receipt checker is:

```bash
uv run python scripts/verify_report_receipt.py output/reports/run_...
uv run python scripts/verify_report_receipt.py output/reports/run_... --require-complete
uv run python scripts/verify_report_receipt.py output/reports/run_... \
  --project-root /path/to/fep_formal --require-complete
```

It recomputes the listed artifact hashes, reconciles the summary, run, and
verification manifests, and always compares stored source/config digests with
a live checkout. The default live root is this repository; `--project-root`
selects another checkout. `--require-complete` additionally requires a
non-empty, zero-warning full-mode receipt; the adapter never runs Hermes,
OpenGauss, or Lean.

Global options are `--project-root PATH` and `--verbose`. `catalogue`, `verify`,
`run`, and `topic` accept topic/area filters where applicable. `run` and `topic` also
accept `verify`, `draft`, `prove`, or `review` workflows. `review` first asks
for a Lean refinement, compiles that exact result, then sends the compiled
source through a prose-only review prompt. Either turn failing makes the
requested workflow incomplete.

`atlas` writes `docs/formalism-atlas.svg` and
`docs/formalism-atlas.html`. `atlas --check` performs no writes and returns
non-zero if either projection is missing or stale. Both views contain the same
canonical node and edge set; the HTML view adds search, filters, an evidence
inspector, keyboard interaction, and complete fallback tables without external
assets.

`dashboard` writes `docs/formal-kernel-dashboard.svg` and
`docs/formal-kernel-dashboard.html`. `dashboard --check` performs no writes and
fails when either projection is missing or stale. The views contain
deterministic finite witnesses tied to named formal-kernel laws and
coverage-derived metrics. Each witness exposes typed equality, inequality, or
predicate checks with its own tolerance, and panel acceptance is their
conjunction plus a boundary observation. These are explanatory visualizations,
not Lean proof receipts or empirical validation.

`verify` never calls Hermes, OpenGauss, or the full pipeline. It requires the
already-built pinned Mathlib cache and returns one native `lake env lean` result
per selected topic. `--receipt PATH` atomically writes a typed native-Lean
verification receipt for the run; `--fail-on-warnings` treats any Lean warning
as a verification failure.

Exit status is zero only for a complete result. A full-mode capability failure,
topic warning, review failure, artifact failure, or unresolved report state
returns non-zero. `status` and `custody census` instead exit 0 when their report
composes, even when it reports stale or gated evidence. Inspect the structured
findings rather than treating those exit codes as acceptance.

## Operator support and exit contracts

Every row requires a complete source checkout selected by `--project-root` or
normal checkout discovery. A missing or incomplete checkout fails before the
operation runs. Installed help remains available outside a checkout.

| Operation | Required inputs | Mutation and processes | Supported runtime | Exit meaning and next action |
| --- | --- | --- | --- | --- |
| `status` | Checkout and existing evidence; optional `--gnn-root PATH` | Reads existing inputs; no dependency acquisition, test collection, compiler or provider process, or evidence repair | Static inspection on supported Python platforms | 0 means the report composed, including missing/stale/unverified sections. Inspect each finding and explicitly run its owning operation after reviewing the inputs. Omitting GNN leaves that side unverified; pin presence alone never compares an omitted checkout. |
| `preflight` | Checkout plus full-mode tool/settings configuration | Read-only capability inspection, including bounded executable availability/version probes; no build, database creation, report or provider request | Platforms supported by the configured tools | 0 means capability checks report `ok`; 1 means a capability failed. Inspect its reason; use explicit `setup` only when acquisition is intended. Preflight success is no topic verification. |
| `verify` | Checkout and built pinned Lean/Mathlib workspace; optional topic/area filters | Starts native Lean compilation with temporary probe files; `--receipt PATH` writes the requested receipt. No Hermes or OpenGauss | Platforms supported by the pinned Lean workspace | 0 means every selected body passed the requested policy. Use `--fail-on-warnings` for publication and independently validate the receipt; a filtered run does not establish the full sealed roster. |
| `bridge status`, `bridge emit --check`, `bridge verify-certificate` | Explicit `--gnn-root PATH`, current source bindings and the verb's identified document/result/receipt inputs | Read-only source/projection or certificate comparison; no model, compiler or emitting subprocess | Static inspection with the named checkout's Python dependencies | 0 means the named check passed; stale/malformed custody or failed comparison returns nonzero. Review changed owners before any explicit re-pin. Numerical certificate agreement does not prove generated-runner execution. |
| `bridge verify-document` | Explicit GNN checkout, `--document PATH` and built Lean workspace | Imports the named extraction route and starts a temporary native Lean probe; writes a receipt only when requested | Named GNN/Python and pinned Lean runtime | 0 means the requested syntax/well-formedness check passed. Use `--fail-on-warnings` for strict checking; this does not prove denotation, scientific validity or runner execution. |
| `publication-capture --plan` | Checkout and explicit `--template PATH` | Prints the fixed policy without journal creation or subprocess execution | Static planning on supported Python platforms | 0 means the plan composed. Review its inputs and budgets before choosing execution; a plan is no completed capture. |
| `publication-capture` execution or `--resume` | Reviewed plan inputs plus `--journal PATH`; exact declared template/toolchain/source inputs | Writes the owned journal and stage artifacts, and runs bounded local subprocesses. Resume revalidates custody before reuse | POSIX file custody and process supervision; Windows execution refuses before journal/process creation | 0 means the local capture completed. On failure inspect retained diagnostics and invalidation reasons. Completion supplies no hosted CI, publication, provider or scientific approval. |

Argparse usage errors return 2; operation refusals/failures return nonzero
rather than an accepted result. Read-only describes persistent artifact
mutation separately from subprocess activity: preflight probes and document
verification have the process behavior stated above. The
[capture runbook](development.md#bounded-publication-capture) owns execution
budgets and support boundaries; [evidence receipts](api.md#evidence-receipts)
owns claim readiness.

## Custody and publication orchestration

`custody census` inspects existing evidence; `custody apply` requires an
explicit staging `--output-dir`; `custody refresh` composes guarded refresh
steps. Its mutually exclusive `--plan`, `--fixpoint` and `--resume` modes have
different write and terminal-state boundaries. In particular, custody planning
writes a journal even though it launches no test/audit subprocesses. The
[custody runbook](development.md#custody-refresh-orchestration) owns the
authorized-owner, source-freeze and render-acceptance requirements.

`publication-capture --template PATH` orchestrates the fixed seven-stage
capture. `--plan` prints policy without creating a journal or running tools;
execution writes bounded evidence, and `--resume` revalidates an existing
journal. The [capture runbook](development.md#bounded-publication-capture)
owns dependency order, invalidation and receipt interpretation. These generic
capabilities do not override a governed production protocol's controller
limits or prohibition on resume.

## Portable mathematical methods

```bash
fep-lean methods inspect --topic fep-001
fep-lean methods inspect --family core-information-geometry
fep-lean methods neighbors core-information-geometry --limit 5
fep-lean methods probe
fep-lean methods analyze fep-001
fep-lean methods theorem fep_fep001.FEP001.fep001_variationalUpperBound_eq_iff
fep-lean methods embedding
fep-lean methods export --output-root ./mathematical-methods
fep-lean methods check --output-root ./mathematical-methods
```

These commands work from the installed wheel without checkout markers. An
explicit global `--project-root PATH` selects canonical checkout owners and
rejects an invalid checkout. The API defaults to installed resources; the CLI
also recognizes a valid current checkout. Inspect the reported origin before
interpreting input hashes. `check` compares existing export bytes without
repair; generation and probes establish neither native proof nor scientific
acceptance. [The guide](mathematical-methods.md) explains the interfaces and
mathematical transfer rules.

The development checkout also provides arbitrary-input Gibbs diagnostics:

```bash
fep-lean methods gibbs \
  --candidate '[0.5, 0.5]' \
  --reference '[0.5, 0.5]' \
  --potential '[0.0, -1000.0]'
```

All three JSON arrays are required. This operation reports the
`numerical-input` origin and uses the supplied vectors independently of
`--project-root`; it requires no valid checkout and writes no artifacts. Its support,
normalization and underflow fields follow the
[numerical API contract](mathematical-methods.md#reusable-finite-variational-methods).
