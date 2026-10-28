# `fep_formal.pipeline`

Strict four-stage orchestration for offline catalog generation and
credentialed full execution.

1. Load and filter the validated catalog.
2. Validate the capabilities required by the selected mode.
3. In `full` mode, run Hermes, native Lean verification, and SQLite capture;
   in `catalogue` mode, record this stage as `not_run`.
4. Generate manuscript variables, the unified formalism appendix, and figures.

Reporting runs only after the four stages complete. Catalog-mode reports are
artifact manifests, not verification receipts. Full-mode results fail closed
when credentials, Gauss, the pinned toolchain, or any selected topic fails.

```python
from fep_formal.pipeline import run_pipeline, run_single_topic

offline = run_pipeline(mode="catalogue")
one_full_topic = run_single_topic("fep-008", mode="full")
```

`FEP_FORMAL_MAX_TOPICS` is an explicit subset filter. A subset's `complete` flag
does not establish full-catalog evidence; publication consumers must validate
the appropriate receipt independently.
