# Manuscript sources

The chapters are rendered from this directory with the local Pandoc/XeLaTeX
toolchain. Run `uv run fep-lean catalogue` first to generate
`manuscript_vars.yaml` and `09z_unified_formalism_catalogue.md`, then run
`uv run python scripts/render_manuscript.py --check` or render authored
chapters into `output/manuscript/` with the same command without `--check`.

`config.yaml` contains static metadata. Runtime values are emitted by
`src/fep_lean/output/manuscript.py`; rendering is source-preserving and any
unresolved `{{...}}` expression fails before output is written. The generated
appendix is derived from the validated catalog and contains one Lean block
and one equation group for every topic.

The cover's top-level `authors` record in `config.yaml` is validated against
`CITATION.cff`, including Daniel Ari Friedman's affiliation, email and ORCID.
The renderer prefixes the ORCID link, so this cover field stores the bare ID.
`autoEqnLabels: true` in the first chapter's metadata numbers every displayed
equation across the combined edition. Explicit equation labels remain usable
for cross-references; inline mathematics and code examples are unaffected.
Acceptance checks the actual LaTeX for unnumbered display environments and
records that gate in receipt version 2. The receipt also binds the cover
configuration and bibliography, as well as chapters and the preamble.

Authored chapters may reference the canonical formalism atlas and numerical
formal-kernel dashboard under `../docs/`. The renderer validates those
references before creating a build and rewrites them to build-local `assets/`
copies, so an exported manuscript never depends on the checkout-relative
preview path. The atlas visualizes authored relations and import dependencies;
the dashboard supplies deterministic numerical witnesses, not proof evidence.

The discussion chapters include `05b_execution_integrity.md`, which documents
the real compiler, HTTP, and SQLite execution contract.

The formal development is read in order: `04g_finite_active_inference_kernel.md`
introduces the reusable kernel, `04h_expanded_formalism_program.md` documents
the first ten seven-topic expansion families, and
`04i_formalism_catalogue_155.md` documents the five families that extend the
roster from 120 to 155 (`fep-121` to `fep-155`, the second expansion; the
third-expansion rows `fep-156` to `fep-168` bring the live catalog to 168
topics and are outside that chapter). Keep that last chapter source-grounded: the retained
native, declaration, Python, and browser receipts bind the frozen v1.1.0
release snapshot only — the accepted post-v1.1.0 Horizon 1/Horizon 2 source
wave invalidated their current-source binding; the coordinated refresh
completed deterministically on 2026-09-12 and is recorded in
[CHANGELOG.md](../CHANGELOG.md). The
retained 50-topic provider receipt remains historical.
`04j_horizon2_smooth_stochastic_kernel.md` completes the ordered sequence,
carrying the kernel onto the Horizon-2 smooth and stochastic foundations.

`08b_mathematical_positioning_supplement.md` places the catalog and maintained
foundations within probability, topology, statistical geometry, inference,
control, and stochastic mechanics. It compares selected result families from
the pinned OpenAI mathematics corpus and distinguishes editorial affinities
from checked relations. Its reproducible inventory, mathematical profiles,
and boundary diagnostics live in the
[modular methods slice](../specs/openai-math-methods/README.md).

Supplement A develops nine worked result passports, eight proposed
mathematical packets, Lean-to-language analysis, and twelve deterministic
publication figures, including a common FEP/OpenAI feature embedding. The
[portable guide](../docs/mathematical-methods.md) explains the installed API and
[offline explorer](../docs/mathematical-positioning/mathematical-map.html).
Prepare the visual source and cited PNGs before rendering:

```bash
uv run fep-lean --project-root . methods export --output-root docs/mathematical-positioning
uv run python scripts/build_manuscript_figures.py
uv run python scripts/build_manuscript_figures.py --check
```

The figure roster owns those PNGs. The seven logical explorer views retain a
combined relation overview; three separate relation panels provide legible
publication figures. The export contains 17 products, including thirteen SVGs.
The renderer stages every SVG companion and the explorer's JSON download into
build-local assets, preserving the standalone HTML's relative links.
Current-source native proof, publication
render acceptance and hosted version release still require their own checks.

Inline Mermaid figures require the installed Mermaid CLI and a browser that
the pinned template can resolve. Use the CLI version declared by that
template's `package-lock.json` and put its `node_modules/.bin` first on the
render invocation's `PATH`; a different CLI can reject the renderer's flags.
For a local macOS render, set
`CHROME_EXECUTABLE_PATH` to the installed browser executable for that
invocation when automatic resolution does not find the application bundle.
The publication acceptance gate rejects a diagram rendered as raw source.
