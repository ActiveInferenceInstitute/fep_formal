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
writes `docs/render-acceptance.json`; `--verify-receipt` re-reads it. CI runs
that verification with two different meanings: the Python job verifies the
committed receipt against the checkout's sources, while the separate render
job (FEP-CI-RENDER) renders end-to-end at the pinned template ref and verifies
the fresh receipt it wrote in the same run -- a receipt CI cannot commit back.
A render needs a checkout of the shared template, XeLaTeX, pandoc,
`rsvg-convert`, the mermaid CLI and the two faces the preamble selects, so
read [the local render runbook](#local-render-runbook) before paying for one:

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

## Local render runbook

A local `check_render_log.py --verify-receipt` failure has two causes with very
different costs: a generated input that this checkout has not built yet, or a
manuscript source that changed since the committed render was accepted. The
checker already tells them apart. Prepare the inputs, read its diagnosis, and
render only when the diagnosis requires it. Rendering stays source-bound and
fail-closed; nothing below writes a receipt without a real accepted render.

### 1. Prepare the generated inputs

```bash
uv sync --locked --extra dev
uv run fep-lean catalogue
uv run fep-lean atlas --check
uv run fep-lean dashboard --check
uv run python scripts/build_manuscript_figures.py
uv run python scripts/build_manuscript_figures.py --check
uv run python scripts/build_render_fonts.py --check
```

`fep-lean catalogue` writes the generated appendix
`manuscript/09z_unified_formalism_catalogue.md`, the typed-variable projection
`manuscript/manuscript_vars.yaml`, and the catalogue figures under
`output/figures/`. All three are gitignored local build products, so a new
worktree has none of them. The atlas and dashboard projections are committed,
so they only need `--check`; if that fails, the regeneration is a tracked
change that belongs in its own commit. The figure pass must write before it
checks because `output/` is gitignored, and the font check reads the generated
appendix, so it is only decidable after the catalogue. None of these steps is
Lean, native, or render evidence.

Only then check the committed receipt:

```bash
uv run python scripts/check_render_log.py --verify-receipt
```

`tests/test_render_publication.py::test_the_committed_receipt_covers_the_committed_manuscript`
calls the same checker directly and does not prepare inputs, so on an
unprepared checkout it fails for the same reason. Prepare the checkout; do not
skip or deselect the test.

### 2. Read the diagnosis

**Class (a): generated appendix missing or regenerated.** On a checkout where
the catalogue has not run, the checker prints both lines (paths shortened):

```text
FAIL: docs/render-acceptance.json: covers manuscript sources '<recorded>' but this checkout is '<live>'; the shipped render predates these sources -- regenerate the build product with `uv run fep-lean catalogue`; changed since that render: 09z_unified_formalism_catalogue.md (generated appendix)
FAIL: docs/render-acceptance.json: generated appendix 09z_unified_formalism_catalogue.md is missing under <checkout>/manuscript; the acceptance digest covers the generated appendix, so run `uv run fep-lean catalogue` first
```

Remedy: run `uv run fep-lean catalogue`, then `--verify-receipt` again. When the
catalogue inputs have not changed since the accepted render, the regenerated
appendix reproduces the accepted bytes and the check passes with no render.
Generation does not always clear it: if the first line persists, still naming
only `09z_unified_formalism_catalogue.md (generated appendix)`, the catalogue
itself changed since the accepted render, and only a real render (step 3)
re-accepts it.

**Class (b): authored source changed.** Any name without the
`(generated appendix)` label -- a chapter or `preamble.md` -- is maintained
manuscript text the committed render predates:

```text
FAIL: docs/render-acceptance.json: covers manuscript sources '<recorded>' but this checkout is '<live>'; the shipped render predates these sources -- re-run scripts/render_publication.py; changed since that render: 00_front_matter.md
```

When both classes are present, an extra line names the generated appendix and
asks for `uv run fep-lean catalogue`; run it, but the authored change still
needs a render. Regeneration never clears class (b): the receipt stays rejected
until `render_publication.py` completes a real, accepted render and rewrites
it. Do not edit the receipt's digests by hand; `render_publication.py
--accept-only` only re-accepts the artifacts already in `output/pdf/` and is
not a substitute for rendering the changed sources.

### 3. Render and accept

The source-bound publication configuration requires the combined manuscript PDF
and disables per-section slide derivatives through the pinned SDK's existing
`render.formats.pdf: true` and `render.formats.slides: false` settings. Slides
remain an optional separately requested deliverable; this mode makes no claim
that slide PDFs were rendered or accepted. Other format settings are unchanged.

The SDK's `ENABLE_PDF` and `ENABLE_SLIDES` environment variables override YAML.
CI clears both for the render subprocess. Local and installed-wheel trials must
also remove both from the child environment before invoking the unchanged
publication entry point, and pass an explicit absolute `--template` checkout
(or `FEP_LEAN_TEMPLATE_DIR`) at the pinned SDK revision. Do not rely on an
editable installation's sibling-template discovery or an unrelated shell
environment. A portable Python launcher can form the child environment with
`{k: v for k, v in os.environ.items() if k not in {"ENABLE_PDF", "ENABLE_SLIDES"}}`
and run the existing entry point with that environment.

Combined PDF/TeX/Markdown/log parity, exact-source native and render receipts,
font registration/cleanup, provenance and scoped PDF visual review remain
mandatory. Enabling slides later requires an explicit mode change and fresh
render qualification; no timing improvement is assumed from this configuration.

Prerequisites, all matching CI's render job in `.github/workflows/ci.yml`:

- A claim-ready native receipt for the current sources at
  `output/native-verification.json`
  (`uv run fep-lean verify --fail-on-warnings --receipt output/native-verification.json`).
  Without it the hydration step exits 1 with "native verification receipt is
  absent or not claim-ready". `render_manuscript.py
  --allow-unavailable-evidence` is for intentionally dry runs only;
  `render_publication.py` does not pass it.
- The pinned Mathlib checkout (`cd lean && lake exe cache get`): the hydration
  step's identifier audit fails closed with "the pinned Mathlib checkout is
  absent" otherwise.
- A checkout of `docxology/template` at the `ref:` pinned in the workflow's
  "Check out the shared rendering template at its pinned ref" step, with this
  checkout registered as its active project. Use an isolated template
  checkout; do not re-point the `projects/active/fep_lean` symlink of a shared
  template checkout that another checkout depends on.
- XeLaTeX, pandoc, `rsvg-convert`, the mermaid CLI and the two preamble faces
  at the versions the workflow installs; `build_render_fonts.py --probe`
  confirms the faces cover the manuscript.

The template path must name the directory that itself contains
`scripts/pipeline/stage_03_render.py`, not a parent of it. In a docxology
monorepo layout that is `repos/public/template`, not the docxology root.
Passing the parent fails immediately with `ERROR: no rendering template
holding scripts/pipeline/stage_03_render.py was found; tried <path>`, and the
project symlink belongs under the same directory:

```bash
template="$(mktemp -d)/template"
git clone https://github.com/docxology/template "$template"
git -C "$template" checkout <ref pinned in .github/workflows/ci.yml>
mkdir -p "$template/projects/active"
ln -s "$PWD" "$template/projects/active/fep_lean"
FEP_LEAN_TEMPLATE_DIR="$template" uv run python scripts/render_publication.py
uv run python scripts/build_render_fonts.py --check
uv run python scripts/check_render_log.py --verify-receipt
```

`render_publication.py` exits 0 only when the template's render stage and this
repository's acceptance both pass; the acceptance writes
`docs/render-acceptance.json` only when it finds nothing. Treat any nonzero
exit as a failed render, and commit the receipt only from a run that exited 0,
together with the source change that required it; the Python job's committed-receipt gate then passes. The receipt
is render evidence only: it says nothing about Lean compilation, native
verification, or full Hermes/OpenGauss execution.

## Custody evidence commands

The custody machinery adapter is `uv run fep-lean custody
<census|apply|refresh>`:

```bash
uv run fep-lean custody census
uv run fep-lean custody apply --output-dir <dir>
uv run fep-lean custody refresh [--plan | --fixpoint | --resume <journal-dir>] \
  --reason "<why>"
```

`census` is a read-only drift report. `apply` is staged-only and requires
`--output-dir`; it performs no repo-side writes. `refresh` composes the
guarded loop; journals land under
`output/custody-journal/<operation-id>/journal.json` (`--journal-dir`
overrides). Focused suites for in-lane work:
`tests/test_custody_refresh.py tests/test_custody_apply.py`.

Focused gates run in-lane; the coordinator owns commit/push/bridge-seal and
the full gate battery.

## Mathematical supplement figures

The 1.6.0 methods export owns thirteen mathematical SVG panels and a standalone
explorer in `docs/mathematical-positioning/`. Generate that model before
`build_manuscript_figures.py`; its existing figure roster now rasterizes every
cited panel and its check rejects missing or stale PNGs:

```bash
uv run fep-lean --project-root . methods export --output-root docs/mathematical-positioning
uv run fep-lean --project-root . methods check --output-root docs/mathematical-positioning
uv run python scripts/build_manuscript_figures.py
uv run python scripts/build_manuscript_figures.py --check
```

[Mathematical methods](../docs/mathematical-methods.md) documents the portable
API and evidence limits. The methods resource projection is maintained by the
slice-local `specs/openai-math-methods/generate_package_methods.py`; ordinary
package and CI checks reject byte drift rather than regenerating authored
metadata or scientific records.
