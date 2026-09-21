# Tests

```bash
uv run pytest tests/ -q --cov=src --cov-fail-under=89 -m "not serial_lean"
```

The live collection is the authority for test counts:

```bash
uv run pytest tests/ --collect-only -q
```

Catalogue tests treat the maintained roster seal, family-owned body registry,
semantic review, novelty ledger, relation graph, and manifested composition
resources as separate owners. Generated YAML, Lean aggregates, and publication
surfaces are checked for parity rather than repaired in fixtures.

The default suite is credential-free. Tests that make provider calls require
explicit live-test selection plus `OPENROUTER_API_KEY` or
`ANTHROPIC_API_KEY`; set `FEP_LEAN_LIVE_TESTS=0` to suppress them when a key is
present. Native Lean acceptance and full external acceptance are separate from
the ordinary coverage run. See [AGENTS.md](AGENTS.md).
