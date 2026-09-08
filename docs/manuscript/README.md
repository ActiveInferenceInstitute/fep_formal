# Manuscript sources

The chapters are rendered from this directory with the local Pandoc/XeLaTeX
toolchain. Run `uv run fep-lean catalogue` first to generate
`manuscript_vars.yaml` and `09z_unified_formalism_catalogue.md`, then run
`uv run python scripts/render_manuscript.py --check` or render authored
chapters into `output/manuscript/` with the same command without `--check`.

`config.yaml` contains static metadata. Runtime values are emitted by
`src/fep_lean/output/manuscript.py`; rendering is source-preserving and any
unresolved `{{...}}` expression fails before output is written. The generated
appendix is derived from the validated catalogue and contains one Lean block
and one equation group for every topic.

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
roster from 120 to 155. Keep that last chapter source-grounded: the retained
native, declaration, Python, and browser receipts bind the frozen v1.1.0
release snapshot only — the accepted post-v1.1.0 Horizon 1/Horizon 2 source
wave invalidated their current-source binding, and
[`FEP-EVIDENCE-CURRENT`](../TODO.md) owns the coordinated refresh. The
retained 50-topic provider receipt remains historical.
