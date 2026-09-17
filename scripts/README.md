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
appendix, and every authored placeholder without writing output. Neither mode
creates that projection -- `fep-lean catalogue` owns it, and both modes exit 1
with "stale manuscript projections" where it is absent, which on a fresh
checkout is always. Run-local receipt/provider values are rebuilt from
independently validated evidence; the default mode writes the resolved files
under `output/manuscript/`:

```bash
uv run fep-lean catalogue
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

`build_manuscript_figures.py` publishes the two atlas/dashboard PNGs the
manuscript cites (rasterized from the committed SVG projections via
`rsvg-convert`) and the graphical abstract under `output/figures/`; `--check`
fails when a cited PNG is missing or older than its SVG projection. The write
pass must precede the check on a fresh checkout because `output/` is
gitignored -- CI runs exactly that pair after `fep-lean catalogue`:

```bash
uv run python scripts/build_manuscript_figures.py
uv run python scripts/build_manuscript_figures.py --check
```

`build_graphical_abstract.py` is the graphical abstract's producer: it renders
`manuscript/assets/graphical-abstract.png` (the sha256-pinned canonical asset)
from `fep_lean.output.graphical_abstract` -- byte-deterministic, 8-bit RGB,
no external rasterizer. Run it when the art changes, then record the new
digest in `manuscript/config.yaml`; `--check` validates the committed asset
against that pin without writing. The copy pass above republishes the asset
under `output/figures/` for the combined render:

```bash
uv run python scripts/build_graphical_abstract.py
uv run python scripts/build_graphical_abstract.py --check
```

`verify_report_receipt.py` independently validates a generated report bundle
under `output/reports/run_...`: it recomputes the listed artifact hashes,
reconciles the summary, run, and verification manifests, and compares stored
source/config digests against a live checkout (`--project-root` to select
another one); `--require-complete` additionally demands a complete,
non-empty, zero-warning full-mode receipt:

```bash
uv run python scripts/verify_report_receipt.py output/reports/run_... --require-complete
```

`capture_browser_acceptance.py` records the canonical Chrome/CDP browser
acceptance: it drives a local Chrome/Chromium (or `--browser PATH`) through
the receipt surface and writes `output/browser-acceptance.json` with six
bound screenshots. It needs a real browser and is not part of CI:

```bash
uv run python scripts/capture_browser_acceptance.py
```

`build_release_bundle.py` builds or validates the deterministic evidence
bundle: without flags it renders the publication set and writes the
`--output PATH` archive; `--check` re-renders in temporary directories and
binds an existing archive back to current sources without mutating them;
`--run-python-acceptance` runs the exact full acceptance command and retains
its receipts:

```bash
uv run python scripts/build_release_bundle.py --output dist/fep-lean.tar.gz
uv run python scripts/build_release_bundle.py --check --output dist/fep-lean.tar.gz
```

Do not invoke repository-root modules or set a monorepo-specific `PYTHONPATH`;
each wrapper resolves this checkout's `src/` directory directly.
