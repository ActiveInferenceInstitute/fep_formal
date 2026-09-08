# CLI reference

The only public command is `fep-lean`.

Every substantive command is source-checkout-bound. The wheel exposes package
resources and help without a checkout, but the console command rejects a
`site-packages` ancestor or incomplete directory with a structured error. Use
`fep-lean --project-root /path/to/fep_lean COMMAND` when the current process is
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
```

`bridge` operates on an explicit sibling GNN checkout (`--gnn-root PATH` is
required for every verb): `status`, `verify-certificate`, and
`verify-document` are read-only; `pin` and `emit` write receipts; `certify`
writes one only with `--receipt PATH` and is read-only without it.
`verify-document --document PATH` checks one emitted GNN document against
the `FEP.GnnDocument` typed surface (syntax + `WellFormed`, contract v0.6);
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
  --project-root /path/to/fep_lean --require-complete
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
returns non-zero. The exception is `status`, whose documented boundary is the
report itself: it exits 0 whenever the report composes, even when sections
report stale evidence.
