# FEP_Formal tests

```bash
FEP_LEAN_LIVE_TESTS=0 uv run pytest tests/ -q --cov=src --cov-fail-under=89 -m "not serial_lean"
```

The live collection is the authority for test counts:

```bash
uv run pytest tests/ --collect-only -q
```

Catalogue tests treat the maintained roster seal, family-owned body registry,
semantic review, novelty ledger, relation graph, and manifested composition
resources as separate owners. Generated YAML, Lean aggregates, and publication
surfaces are checked for parity rather than repaired in fixtures.

Set `FEP_LEAN_LIVE_TESTS=0` explicitly for credential-free selection. Hermes
and end-to-end provider tests require explicit live-test selection plus
credentials; the Gauss runner live family can also select itself when
`OPENROUTER_API_KEY` or `ANTHROPIC_API_KEY` is present unless disabled with `0`.
Native Lean acceptance and full external acceptance are separate from
the ordinary coverage run. See [AGENTS.md](AGENTS.md).
