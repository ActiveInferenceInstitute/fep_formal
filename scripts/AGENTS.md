# Scripts contract

Public execution belongs to `src/fep_lean/cli.py` and the `fep-lean` console entry
point. Script files may only provide thin wrappers or deterministic maintenance
operations; they must not import packages outside this checkout.

Canonical authoring lives outside this wrapper directory: family-owned modules
under `src/fep_lean/catalogue/bodies/`, the validated catalogue registry,
`config/catalogue_metadata.yaml`, `config/theorem_maturity.yaml`,
`config/formalism_novelty.yaml`, and `config/formalism_relations.yaml`.
`_maint_build_topics_catalogue.py`,
`_maint_build_fep_all_lean.py`, `_maint_build_formal_modules.py`,
`build_formalism_coverage.py`, `build_formalism_atlas.py`, and
`build_formal_kernel_dashboard.py` are thin deterministic projection commands.
`audit_formalisms.py` is the native
declaration/axiom evidence adapter. The
`theorem_maturity_audit.py` maintenance command validates that review and
renders `docs/theorem-maturity-audit.md`.

`render_publication.py` is the publication entry point and owns the render
boundary: it renders the authored sources into `output/manuscript/` (the
directory the shared template actually typesets), runs the template's PDF
stage, and then runs `check_render_log.py`, exiting on the conjunction. The
template's own success test looks for four fatal markers under
`-interaction=nonstopmode`, so it reports success over a log recording TeX
errors and dropped glyphs; that template is a separate repository and this
wrapper does not accept its verdict. `build_render_fonts.py` owns the derived
font requirement (`docs/render-fonts.json`, `--check` in CI) and the host
probe. None of the three reconstructs a roster or a policy: the acceptance
predicates live in `fep_lean.output.render_log`, the requirement in
`fep_lean.output.render_fonts`.

A clean acceptance writes `docs/render-acceptance.json`, and CI runs
`check_render_log.py --verify-receipt` against it. That indirection is not
decoration: CI does not render this manuscript -- that needs a checkout of the
shared template, XeLaTeX, pandoc, `rsvg-convert`, the mermaid CLI and the two
faces `docs/manuscript/preamble.md` selects -- so it cannot re-run the acceptance
and would otherwise run nothing at all, which is exactly the audited state: a
tested acceptance no workflow invoked.

The receipt is bound to a digest over every typeset manuscript source plus
`docs/manuscript/preamble.md`, so a chapter or a font selection changed without a
fresh render fails CI. It is not bound to the values a `{{token}}` resolves
to; `manuscript_projection_drift` and `stale_render_defects` own that surface
and both run on the render path. A rejected render writes no receipt and
removes the standing one -- sources can drift out of a render without changing,
so the digest alone would let a superseded receipt keep vouching. The digests
are recorded per file, so a stale receipt names what moved.

`build_release_bundle.py` is a thin public wrapper over
`fep_lean.output.release_bundle`. It never reconstructs the archive roster,
renderer policy, manifest, checksum table, or evidence boundaries. `--check`
must remain non-mutating and bind an existing archive back to current sources.
Generated Lean output is tracked and must be regeneration-identical. The formal
resource manifest owns foundation, leaf-composition, and import-aggregate
projections; wrapper scripts must not reconstruct that roster independently.
