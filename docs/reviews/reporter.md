# Report bundles and provenance

`fep_lean.output.reporter.Reporter` writes one timestamped report directory for
one pipeline result. It refuses to reuse an existing run directory, so an
explicit `run_id` cannot overwrite earlier evidence.

## Bundle layout

```text
output/reports/run_YYYYMMDD_HHMMSS_microseconds/
├── index.md
├── summary.json
├── hermes.md
├── lean.md
├── validation.md
├── verification_manifest.json
├── run_manifest.json
└── topics/
    └── fep-NNN.md
```

`summary.json` carries the serialized pipeline result, selected topic rows,
catalogue summary, source/config digests, receipt-schema version, configured
Lean and Mathlib pins, the actual compiler version, the resolved 40-character
Mathlib revision, and a hash map for every other artifact. It deliberately
excludes its own digest to avoid a self-referential value.

`run_manifest.json` is the compact run contract: mode, completion, catalogue
and verified counts, warning count, capabilities, verification source,
clean-Lean and zero-warning predicates, failure reason, source/config digests,
toolchain, and topic rows.

`verification_manifest.json` is a topic-result projection. Its presence does
not make a run claim-ready; validation reconciles the entire canonical topic
evidence row with both the run manifest and summary, including provider/session
identity, exact refined and compiled Lean, compiled-source digest, actual
compiler version, direct Hermes compile result, and every warning.

The Markdown files are human-readable projections:

- `index.md`: status, mode, selection counts, stage table, and metrics;
- `hermes.md`: model, cache, explanation, refined source, and direct-compile
  information per selected topic;
- `lean.md`: structured compilation statistics;
- `validation.md`: the mode-dependent named capability checks;
- `topics/fep-NNN.md`: one selected topic's Hermes and final verification
  provenance.

Catalogue mode normally has no topic verification rows. Its bundle can be
structurally valid while `verified_topics` remains zero.

## API

```python
from fep_lean.output import Reporter, ReportPaths, validate_report_receipt

reporter = Reporter(
    project_root,
    run_id=None,
    output_root=None,
)
paths: ReportPaths = reporter.generate(catalogue, pipeline_result)

validation = validate_report_receipt(
    paths.root,
    require_complete=False,
    project_root=project_root,
)
```

`ReportPaths` exposes `root`, the five primary Markdown/JSON paths, and both
manifest paths. `as_dict()` provides their string representation.

The default run ID includes microseconds. If a caller supplies a repeated ID,
`generate` raises `FileExistsError` before any artifact is written.

## Independent validation

Use the repository adapter or the Python API:

```bash
uv run python scripts/verify_report_receipt.py output/reports/run_...
uv run python scripts/verify_report_receipt.py \
  output/reports/run_... --require-complete
uv run python scripts/verify_report_receipt.py \
  output/reports/run_... --project-root /path/to/fep_lean --require-complete
```

The validator:

- requires the report directory, mandatory artifacts, and exactly one hashed
  `topics/fep-NNN.md` file for every full-mode row;
- rejects absolute paths, traversal, malformed SHA-256 values, hash drift,
  unlisted files, missing topic files, and unexpected topic files;
- validates summary, capability, selection, and topic-row types;
- reconciles run ID, mode, completion, catalogue count, verified count,
  complete topic evidence rows, source/config digests, and toolchain fields;
- always recomputes repository digests against the repository root selected by
  the adapter (or the explicit `project_root` supplied to the Python API);
- reconciles warning lists and counts and rejects warnings in a complete full
  claim;
- requires each claim row to bind a successful Hermes session and nonempty
  model identity, direct Hermes-refined compilation, byte-identical refined and
  final Lean, the SHA-256 digest of that final source, and actual Lean version
  output matching the configured pin;
- binds the exact Mathlib Git revision from `lean/lake-manifest.json`, not only
  the human-readable release tag;
- derives `claim_ready` independently of the producing process.

A bundle is claim-ready only when it is a non-empty complete `full` run whose
selected rows, clean Lean counts, Hermes provenance, manifests, and artifacts
all reconcile with zero warnings. `catalogue` completion and a native Lean
receipt are separate evidence classes.

## Failure boundary

Full-mode capability or topic failure prevents a successful report at the
pipeline boundary. If a partial bundle is explicitly generated for diagnosis,
its manifests preserve the incomplete state and validator errors rather than
promoting it to evidence.

Report directories may contain provider-derived text and session identifiers.
They never contain provider keys by design, but inspect a bundle before sharing
it outside the operator boundary.

## Navigation

- [Hermes](../hermes.md)
- [Pipeline](../pipeline.md)
- [Public API](../api.md)
- [Documentation index](../README.md)
