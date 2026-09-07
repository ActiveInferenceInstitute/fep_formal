# Cold start and recoverable cleanup

Use this page to distinguish maintained source from reproducible local state.
Inspect targets before deleting anything: this checkout contains a tracked Lean
aggregate beside ignored verifier scratch files.

## Maintained files: never clean as cache

These paths are source or tracked generated projections:

- `config/catalogue_metadata.yaml`
- `config/theorem_maturity.yaml`
- `config/formalism_novelty.yaml`
- `config/formalism_relations.yaml`
- `src/fep_lean/catalogue/bodies/*.py`, `registry.py`, and `latex.py`
- `config/topics.yaml` and `src/fep_lean/data/topics.yaml`
- `lean/lakefile.lean`, `lean/lean-toolchain`, and `lean/lake-manifest.json`
- `lean/FepSketches/fep_all.lean`
- canonical manifested `src/fep_lean/formal/**/*.lean` modules and their
  tracked `lean/FepSketches/` projections
- `docs/formalism-coverage.json` and `docs/formalism-coverage.md`
- `docs/formalism-atlas.svg`, `docs/formalism-atlas.html`,
  `docs/formal-kernel-dashboard.svg`, and
  `docs/formal-kernel-dashboard.html`
- authored `manuscript/*.md` files

In particular, do not remove `lean/FepSketches/`: it contains the tracked
aggregate. The verifier owns only files matching
`lean/FepSketches/_verify_*.lean`, which are ignored and removed after each
normal check.

Before cleanup, inspect the exact state:

```bash
git status --short --branch
git status --ignored --short
git ls-files lean/FepSketches config src/fep_lean/data
```

## Reproducible checkout-local state

The following ignored locations can be regenerated, but may contain useful
local evidence. Preserve or archive any receipt you intend to cite before
removal.

| Path | Contents | Reproducer |
| --- | --- | --- |
| `output/` | figures, rendered manuscript, native receipts, run reports | relevant CLI command below |
| `manuscript/manuscript_vars.yaml` | generated typed variable projection | `fep-lean catalogue` |
| `manuscript/09z_unified_formalism_catalogue.md` | generated Lean and equation appendix | `fep-lean catalogue` |
| `.pytest_cache/`, `.coverage`, `htmlcov/` | test metadata and coverage output | coverage gate |
| `build/`, `dist/`, `*.egg-info/` | Python build output | `uv build` or `uv sync` |
| `__pycache__/` | interpreter bytecode | Python import |
| `lean/.lake/` | pinned dependency checkout and compiled Lake cache | `fep-lean setup` |

`output/reports/` may contain the only copy of a full-run receipt. Deleting it
is recoverable only by repeating the provider-backed run, so it is not routine
cache cleanup.

## Rebuild the deterministic surfaces

From the standalone repository root:

```bash
uv sync --locked --extra dev
uv run python scripts/_maint_build_topics_catalogue.py --check
uv run python scripts/_maint_build_fep_all_lean.py --check
uv run python scripts/_maint_build_formal_modules.py --check
uv run python scripts/theorem_maturity_audit.py --check
uv run python scripts/build_formalism_coverage.py --check
uv run python scripts/_maint_build_lean_landscape.py --check
uv run fep-lean atlas --check
uv run fep-lean dashboard --check
uv run fep-lean catalogue
uv run python scripts/render_manuscript.py --check
uv run python scripts/render_manuscript.py --output-dir output/manuscript
```

The projection commands with `--check` are non-mutating freshness checks.
Remove `--check` only when a maintained owner was intentionally changed and
its projection must be regenerated.

For a genuinely cold Lean workspace, use the bounded setup owner instead of
manually manipulating `.lake` internals:

```bash
uv run fep-lean setup
(cd lean && lake build FepSketches)
uv run fep-lean verify --fail-on-warnings \
  --receipt output/native-verification.json
```

`lake exe cache get` restores the exact pinned Mathlib binary cache; a source
rebuild of all upstream Mathlib modules is normally unnecessary.

## External Gauss and Hermes state

Session and LLM cache state lives under `GAUSS_HOME` (default `~/.gauss`),
outside this checkout. It can contain credentials, sessions, and cached
provider responses. Project cleanup does not authorize modifying it.

If a full cold provider run is required, first obtain explicit operator
authority, identify the exact Gauss targets, and preserve any report receipts
that must remain auditable. Never copy a key or `.env` file into this
repository.

## Acceptance after cleanup

Run the local acceptance surface after regeneration:

```bash
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
uv run python scripts/build_formalism_coverage.py --check
uv run python scripts/_maint_build_lean_landscape.py --check
uv run python scripts/build_formalism_atlas.py --check
uv run python scripts/build_formal_kernel_dashboard.py --check
uv run fep-lean catalogue
uv run python scripts/render_manuscript.py --check
```

Finish by confirming that only intended generated projections changed with
`git status --short` and `git diff --check`.

## Navigation

- [Getting started](getting-started.md)
- [Troubleshooting](troubleshooting.md)
- [Pipeline](pipeline.md)
- [Documentation index](README.md)
