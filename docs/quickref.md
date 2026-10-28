# Quick reference

```bash
uv sync --locked --extra dev
uv run fep-formal catalogue
uv run fep-formal setup
uv run fep-formal verify
uv run python scripts/audit_formalisms.py \
  --receipt output/formalism-audit.json
uv run python scripts/_maint_build_lean_landscape.py --check
uv run fep-formal atlas --check
uv run fep-formal dashboard --check
uv run fep-formal preflight
uv run fep-formal run --topic fep-001
uv run fep-formal status
uv run fep-formal topic fep-001
uv run fep-formal bridge status --gnn-root /absolute/path/to/GNN
```
Replace the example GNN path with the explicitly named checkout. Other bridge
operations are listed by `uv run fep-formal bridge --help`; pinning and emission
write artifacts. Re-pinning follows the canonical order in the
[re-pin runbook](design/gnn-bridge/README.md#re-pin-runbook-canonical-order).

The full test and documentation gates are listed in
[`testing.md`](testing.md). Generated output lives under `output/`; manuscript
variables and the unified appendix live under `manuscript/`.
