# Documentation map

Everything in `docs/` resolves within this repository. Files are grouped by
lifecycle: authored operating docs at this level, long-form background in
[`guides/`](guides/), dated review snapshots in [`reviews/`](reviews/),
regenerable projections in [`generated/`](generated/), committed render
receipts in [`evidence/`](evidence/), prospective programs in
[`design/`](design/README.md), and the publication sources one level up in
[`manuscript/`](manuscript/README.md).

## Start here

- [Getting started](getting-started.md) — install, catalogue mode, and strict mode.
- [Quick reference](quickref.md) — command surface at a glance.
- [Glossary](glossary.md) — terminology used across the catalogue and formal modules.
- [FEP background](guides/fep-background.md) — conceptual orientation with explicit formalization boundaries.
- [Formal-kernel methods](guides/formal-kernel-methods.md) — shared carriers, theorem scope, validation ladder, and visualization contract.
- [Lean 4](guides/lean4.md) — pinned workspace and aggregate generation.

## Operate

- [Pipeline](pipeline.md) — stages, modes, and result contract.
- [CLI reference](cli-reference.md) — canonical command surface.
- [Configuration](configuration.md) — settings and environment overrides.
- [API](api.md) — Python surface.
- [Architecture](architecture.md) — module layout and dependencies.
- [Topic reference](topics-reference.md) — canonical owners, inspection, and receipt semantics.
- [Hermes](hermes.md) — HTTP client, cache, retries, and response validation.
- [OpenGauss](opengauss.md) — SQLite state and artifact persistence.
- [Troubleshooting](troubleshooting.md) — common failures and fixes.
- [Cold start](cold-start-and-cleanup.md) — disposable output cleanup.

## Quality gates

- [Testing](testing.md) — local and CI validation.
- [Development](development.md) — documentation, rendered-artifact, and projection-freshness gates (release-bundle and receipt validation live in `../HANDOFF.md`).
- [Quality-gate decisions](quality.md) — Ruff baseline, ownership, and staged policy.
- [Authorship guide](authorship-guide.md) — writing and evidence rules for new pages.
- [Coverage branch policy](coverage-branch.md) — coverage-floor maintenance.

## Generated products

Regenerable projections — edit the canonical owners, never the generated
bytes. Each row names its producing command and freshness gate.

| Page | Producer | Freshness gate |
| --- | --- | --- |
| [Formalism coverage](formalism-coverage.md) (+ [.json](formalism-coverage.json)) | `uv run python scripts/build_formalism_coverage.py` | `--check` |
| [Theorem maturity audit](generated/theorem-maturity-audit.md) | `uv run python scripts/theorem_maturity_audit.py` | `--check` |
| [Lean landscape](generated/lean-landscape.md) | `uv run python scripts/_maint_build_lean_landscape.py` | `--check` |
| [Interactive formalism atlas](formalism-atlas.html) (+ [static](formalism-atlas.svg)) | `uv run fep-lean atlas` | `atlas --check` |
| [Interactive formal-kernel dashboard](formal-kernel-dashboard.html) (+ [static](formal-kernel-dashboard.svg)) | `uv run fep-lean dashboard` | `dashboard --check` |

## Evidence receipts

Committed render receipts in [`evidence/`](evidence/) — written by the
publication pipeline, verified by `scripts/check_render_log.py
--verify-receipt`; never hand-edited.

- [Render acceptance](evidence/render-acceptance.json) — the accepted publication render and its per-source digests.
- [Render font requirement](evidence/render-fonts.json) — the glyph coverage the render host must provide.

## Design programs

- [Design programs](design/README.md) — prospective architecture and research goals, kept separate from current catalogue and evidence claims.
- [GNN bridge](design/gnn-bridge/README.md) — cross-repo articulation with the GeneralizedNotationNotation pipeline (bridge CLI, Lean AST, source custody, v0.6).
- [FEP research horizons](design/fep-research-program/README.md) — dependency-ordered finite synthesis, smooth/stochastic lifting, and an end-to-end scientific case study.

## Reviews (immutable dated snapshots)

- [Test suite review](reviews/test-suite-review.md) — dated historical snapshot, retained as review provenance.
- [Mahakala adversarial review](reviews/mahakala-review.md) — dated historical adversarial-review snapshot.
- [Reporter notes](reviews/reporter.md) — retained reporter-provenance snapshot.

## Manuscript

The publication sources live in [`manuscript/`](manuscript/README.md);
the [155-topic expansion chapter](manuscript/04i_formalism_catalogue_155.md)
carries the finite risk, policy trees, native blankets, exponential-family
duality, continuous time, and evidence boundaries. Catalogue-derived
manuscript inputs (`09z_unified_formalism_catalogue.md`,
`manuscript_vars.yaml`) are created by `uv run fep-lean catalogue`, and the
manuscript-render check retains its own freshness gate in the Lean lane.
