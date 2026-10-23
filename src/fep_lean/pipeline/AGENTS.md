# `fep_lean.pipeline` contract

`core.py` owns `FEPPipeline`, `PipelineResult`, and `StepResult`;
`orchestrator.py` owns the stable `run_pipeline` and `run_single_topic`
entrypoints plus report generation.

## Invariants

- Only `full` and `catalogue` modes are valid.
- Catalog mode is offline and never invokes Hermes, Gauss, or Lean.
- Full mode requires a live Hermes client and strict capability validation; no
  fallback may convert a missing capability into success.
- A report is generated only for a complete pipeline result.
- `catalogue_topics` is the selected roster size and `verified_topics` is
  derived from successful, no-`sorry`, zero-warning full-run rows. Do not
  conflate either with native-receipt evidence.
- Artifact generation may write only declared output/manuscript projections.

Use imports from `fep_lean.pipeline`. Tests must cover unknown IDs, empty or
invalid filters, missing capabilities, catalog non-execution, and valid
single-topic/full selection.

See [README.md](README.md) and [../../AGENTS.md](../../AGENTS.md).
