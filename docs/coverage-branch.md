# Branch coverage

Coverage is measured with `concurrency = ["multiprocessing"]` in `pyproject.toml`.
`src/fep_lean/output/figures.py` renders charts via matplotlib with the Agg
backend only; it spawns no worker processes.
The `multiprocessing` concurrency setting is incompatible with `--cov-branch`
(a known pytest-cov limitation: branch data is not collected from worker processes).

## Measuring branch coverage

To measure branch coverage, run a separate non-parallel invocation that excludes
figure-generation tests:

```bash
uv run pytest tests/ -q --cov=src --cov-branch --cov-report=term-missing \
  --ignore=tests/test_figure_generation.py
```

This gives branch coverage for all source files except `src/fep_lean/output/figures.py`
(which is excluded from the branch run). The figure module has 100% line coverage
and no branch-dependent logic, so the gap is negligible.

## Expected values

Current runs show approximately **89.6% branch coverage** across all non-figure
modules. Branch coverage is **not** independently gated — `fail_under` in
`pyproject.toml` applies to line coverage only. The line coverage threshold of
89% provides adequate protection since branch coverage tracks within ~1.5
percentage points of line coverage for this codebase's error-handling patterns.

## Related

- [`pyproject.toml`](../pyproject.toml) — coverage concurrency setting
