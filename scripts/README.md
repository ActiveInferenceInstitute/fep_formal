# Scripts

The public command is `uv run fep-lean`. The numbered files remain thin local
wrappers for environments that discover Python scripts automatically:

- `01_fep_catalogue_and_figures.py` → `fep-lean catalogue`
- `02_run_single_topic.py` → `fep-lean topic ID`
- `03_lean_verify_only.py` → `fep-lean verify` (Lean only; no Hermes/Gauss)
- `04_generate_reports.py` → `fep-lean report`

Maintenance adapters are prefixed with `_maint_`. Canonical topic bodies live
in family modules under `src/fep_lean/catalogue/bodies/` and are merged by the
validated registry; metadata, semantic review, novelty, and relation review
live in their corresponding `config/*.yaml` owners. Regenerate all tracked
projections after editing those sources:

```bash
uv run python scripts/_maint_build_topics_catalogue.py
uv run python scripts/_maint_build_lean_landscape.py
uv run python scripts/_maint_build_fep_all_lean.py
uv run python scripts/_maint_build_formal_modules.py
uv run python scripts/theorem_maturity_audit.py --write
uv run python scripts/build_formalism_coverage.py
uv run python scripts/build_formalism_atlas.py
uv run python scripts/build_formal_kernel_dashboard.py
```

Every generator supports `--check`, which performs a non-mutating freshness
test suitable for CI.

The atlas is the authored topic/capability/module relation projection. The
formal-kernel dashboard is a separate deterministic numerical-witness
projection. Neither generator creates proof evidence; native compilation and
the declaration/axiom audit remain separate gates.

`audit_formalisms.py` is not a generator. It compiles a declaration-resolution
probe against the pinned Lake workspace, checks every semantic/formal witness
with `#print axioms`, requires one parsed result per canonical declaration,
normalizes Lean's hard-wrapped output, rejects warnings and `sorryAx`, and can
write an atomic receipt:

```bash
uv run python scripts/audit_formalisms.py \
  --receipt output/formalism-audit.json
```

`render_manuscript.py` is the fail-closed source-to-build renderer. Its check
mode validates the stable typed-variable projection, the exact generated
appendix, and every authored placeholder without writing output. Run-local
receipt/provider values are rebuilt from independently validated evidence; the
default mode writes the resolved files under `output/manuscript/`:

```bash
uv run python scripts/render_manuscript.py --check
uv run python scripts/render_manuscript.py
```

`render_publication.py` is the publication entry point: it renders the authored
sources into `output/manuscript/`, runs the shared rendering template's PDF
stage, and then runs this repository's own acceptance; its exit code is the
conjunction. The first step is load-bearing: the template renders from
`output/manuscript/` whenever it exists and its hydration hook looks for a
generator script this project does not have, so a render invoked without it
typesets whatever that directory last held. The template compiles with
`-interaction=nonstopmode` and tests its log for four fatal markers, so a `!`
error and every `Missing character:` note exit zero with a PDF written -- the
mechanism that shipped 162 dropped glyphs and one false printed theorem. The
template is a separate repository, so this repository cannot fix that test; it
declines to accept its verdict instead. A preflight probes the host's installed
fonts first, because the dropped-glyph failure is silent by construction:

```bash
FEP_LEAN_TEMPLATE_DIR=<template checkout> \
  uv run python scripts/render_publication.py
uv run python scripts/render_publication.py --accept-only
```

`check_render_log.py` is that acceptance on its own. A run that finds nothing
writes `docs/render-acceptance.json`; `--verify-receipt` re-reads it and is
what CI runs, because CI does not render this document -- that needs a checkout
of the shared template, XeLaTeX, pandoc, `rsvg-convert`, the mermaid CLI and
the two faces the preamble selects:

```bash
uv run python scripts/check_render_log.py --receipt docs/render-acceptance.json
uv run python scripts/check_render_log.py --verify-receipt
```

`build_render_fonts.py` owns the font requirement: `--check` fails when the
manuscript starts typesetting a glyph the committed record does not list, and
`--probe` asks the host's fontconfig whether the selected faces cover the set:

```bash
uv run python scripts/build_render_fonts.py --check
uv run python scripts/build_render_fonts.py --probe
```

Do not invoke repository-root modules or set a monorepo-specific `PYTHONPATH`;
each wrapper resolves this checkout's `src/` directory directly.
