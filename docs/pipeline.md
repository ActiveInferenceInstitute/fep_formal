# Pipeline

The pipeline has four recorded stages:

1. **Load Catalog** — strict YAML validation and optional filters.
2. **Environment Validation** — bounded, read-only capability checks.
3. **Gauss Sessions** — full mode only: Hermes, Lean, and SQLite per topic.
4. **Manuscript Artifacts** — deterministic figures, variables, and appendix.

`Reporter.generate` runs only after a complete pipeline result. Full mode never
turns an unavailable service into a successful-looking partial run. Catalog
mode records the Gauss stage as `not_run`, writes a report marked
`catalogue`, and reports zero verified topics.

A full row is verified only when Hermes completed the requested workflow and
the final Lean source compiled with neither `sorry` nor warnings. The `review`
workflow is ordered: Lean refinement, native compilation, then prose-only
review of that exact compiled source. Both provider turns are persisted in the
SQLite session, and a failed commentary turn fails the requested workflow.

## Programmatic use

```python
from fep_lean.pipeline import run_pipeline, run_single_topic

offline = run_pipeline(mode="catalogue")
strict = run_pipeline(mode="full", topic_filter=["fep-001"])
single = run_single_topic("fep-001", mode="full")
```

The report contains `summary.json`, stage Markdown, a verification manifest,
and SHA-256 artifact hashes. The in-memory result remains the source for the
report, so serialized topic fields must stay aligned with `TopicRunResult`.

After a report exists, run [`verify_report_receipt.py`](../scripts/verify_report_receipt.py)
to independently recompute its complete artifact inventory and reconcile the
manifests. A receipt is claim-ready only when `--require-complete` accepts a
non-empty full-mode run whose Hermes session/model, direct compile result,
exact compiled Lean digest, actual compiler version, resolved Mathlib revision,
and one-per-topic Markdown roster all agree with the live source tree.
Catalog receipts remain offline artifacts with zero verified topics.
