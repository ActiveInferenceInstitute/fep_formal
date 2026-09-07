# Testing

Run from the project root:

```bash
uv run pytest tests/ -q --cov=src --cov-fail-under=89 -m "not serial_lean"
```

The suite uses real temporary files, SQLite databases, subprocesses, and local
HTTP servers. Environment variables isolate secrets and expensive external
integration tests; they do not manufacture successful execution results.

Required release gates are:

```bash
uv run python scripts/_maint_build_topics_catalogue.py --check
uv run python scripts/_maint_build_fep_all_lean.py --check
uv run python scripts/_maint_build_formal_modules.py --check
uv run python scripts/theorem_maturity_audit.py --check
uv run python scripts/build_formalism_coverage.py --check
uv run python scripts/_maint_build_lean_landscape.py --check
uv run python scripts/build_formalism_atlas.py --check
uv run python scripts/build_formal_kernel_dashboard.py --check
uv run pytest tests/ -q --cov=src --cov-fail-under=89 -m "not serial_lean"
uv run mypy src
uv run ruff check src tests scripts docs
uv run ruff format --check src tests scripts docs
uv run python docs/check_links.py --strict --include-root
uv run python docs/md_hygiene.py --strict
uv run python docs/pin_audit.py --check-latest
uv run python docs/xref_audit.py
uv run python docs/theorem_ref_audit.py
uv run python docs/citation_audit.py
uv run fep-lean catalogue
uv run python scripts/render_manuscript.py --check
```

Native formal acceptance additionally requires the pinned toolchain and
Mathlib build:

```bash
cd lean && lake build FepSketches
cd .. && uv run python scripts/audit_formalisms.py \
  --receipt output/formalism-audit.json
uv run fep-lean verify --fail-on-warnings \
  --receipt output/native-verification.json
```

Hermes/OpenGauss full validation additionally requires external credentials;
`fep-lean preflight` reports each missing capability without modifying the
workspace.

The atlas and dashboard tests validate deterministic projection and
accessibility contracts. The atlas visualizes authored provenance; the
dashboard visualizes selected finite examples. Neither is deductive evidence.
See [formal-kernel methods](formal-kernel-methods.md) for the evidence matrix.
