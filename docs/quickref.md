# Quick reference

```bash
uv sync --locked --extra dev
uv run fep-lean catalogue
uv run fep-lean setup
uv run fep-lean verify
uv run python scripts/audit_formalisms.py \
  --receipt output/formalism-audit.json
uv run python scripts/_maint_build_lean_landscape.py --check
uv run fep-lean atlas --check
uv run fep-lean dashboard --check
uv run fep-lean preflight
uv run fep-lean run --topic fep-001
uv run fep-lean status
uv run fep-lean topic fep-001
uv run fep-lean bridge status|pin|emit|certify|verify-certificate|verify-document
```
Bridge re-pinning follows the canonical order in the
[re-pin runbook](design/gnn-bridge/README.md#re-pin-runbook-canonical-order).

The full test and documentation gates are listed in
[`testing.md`](testing.md). Generated output lives under `output/`; manuscript
variables and the unified appendix live under `manuscript/`.
