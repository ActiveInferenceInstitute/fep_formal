# Troubleshooting

## Preflight fails

Run `uv run fep-formal preflight`. The JSON lists the exact missing capability.
Use `uv run fep-formal setup` only when the failure is a missing Lean/Mathlib
build. Install OpenGauss and configure Hermes credentials separately.

## Catalog artifacts are stale

Run `uv run fep-formal catalogue`. The command validates the YAML first and then
regenerates manuscript variables, the unified appendix, figures, and a report.

## A full run fails

Inspect the structured `failure_reason` and the failed capability checks. Full
mode does not create a successful report when any topic or integration fails.
Check `GAUSS_HOME`, `FEP_FORMAL_VERIFY_TIMEOUT`, `FEP_FORMAL_LAKE_EXE`,
`FEP_FORMAL_LEAN_EXE`, and the configured Hermes endpoint.

## Documentation checks fail

Run the documentation and generated-projection commands in the
[root required-check inventory](../AGENTS.md#required-checks) from the project
root. Materialize generated manuscript inputs before `xref_audit.py`; regenerate the atlas and dashboard
only from their canonical builders when their drift checks identify stale
outputs.
