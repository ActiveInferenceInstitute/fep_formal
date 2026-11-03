# `tests/_support/` contract

Private helpers for the suite. They may depend on test-only assumptions; they
must not become package code.

## Rules

- Resolve `lake` through [`lake.py`](lake.py). Boundary probes pass
  `missing="skip"`; acceptance probes pass `missing="raise"` and fail closed.
- Run Lean compiles through [`lean_runner.py`](lean_runner.py). Never call
  `subprocess.run(..., timeout=...)` directly for a compile probe; the
  process-group runner kills the `lean` grandchild as well as `lake`.
- Keep helpers deterministic and isolated. Use `tmp_path`, temporary
  `GAUSS_HOME` paths and `output_root` overrides; do not write to the live
  checkout.
- `resources/` holds frozen captured bytes. Do not reformat or regenerate
  them; a changed byte invalidates the digest check that loads it.
- Do not import `fep_lean`, and do not add these helpers to a package
  `__init__.py`.

Follow the [test contract](../AGENTS.md) and the
[root required checks](../../AGENTS.md#required-checks).
