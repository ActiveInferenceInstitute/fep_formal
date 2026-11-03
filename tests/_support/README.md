# Shared test support

Private helpers for the test suite. This directory is not part of the
installable package and must not be imported by `src/`.

## Modules

| Module | Purpose |
| --- | --- |
| `catalogue_project.py` | Build isolated checkout copies for real catalogue and reporting pipeline tests. |
| `custody_fixture_knobs.py` | Load the digest-checked historical validator for synthetic custody fixtures. |
| `fast_relaxation_review.py` | Exact inverse for the reviewed finite two-state limit extension. |
| `h2_r0_custody.py` | Validate the reviewed successor of the immutable H2.7-R0 gate. |
| `lake.py` | Resolve `lake` from `PATH` or `~/.elan/bin`, with deliberate skip/raise missing-tool stances. |
| `landauer_epoch.py` | Exact finite-path source successor views for immutable historical unit seals. |
| `lean435_migration.py` | Compare frozen H3 carrier bytes across the enumerated Lean 4.35 migration. |
| `lean_module_contract.py` | Exact current Lean module headers and source-only closure extraction. |
| `lean_runner.py` | Process-group-safe runner for Lake/Lean compile probes. |
| `native_catalogue_gate.py` | One explicit strict producer inside the serial catalogue test. |
| `native_catalogue_shadow.py` | Independent comparison of two actual strict native executions. |
| `release_bundle.py` | Shared release fixtures; assertions stay in the owner test modules. |
| `release_lineage.py` | Present the live tree to the frozen H2.7-R0 custody validator. |
| `resources/` | Frozen captured bytes, including the digest-pinned historical validator. |

## Use

Resolve shared executables through `lake.lake_executable` and run Lean
compiles through `lean_runner.run_lake_lean_probe` or
`run_lean_compile_probe`. Do not call `subprocess.run(..., timeout=...)`
directly for a compile probe: it kills only `lake` and leaves the `lean`
grandchild holding the `.olean` lock region.

The [test contract](../AGENTS.md) owns missing-tool stances and suite strata.
