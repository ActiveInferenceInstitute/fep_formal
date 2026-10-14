# Documentation map

- [Mathematical methods](mathematical-methods.md) — portable topic contracts, research context and mathematical transfer rules.
- [Mathematical positioning explorer](mathematical-positioning/mathematical-map.html) — offline searchable contracts, typed associations and numerical boundary panels.
- [Getting started](getting-started.md) — install, catalogue mode, and strict mode.
- [FEP background](fep-background.md) — conceptual orientation with explicit formalization boundaries.
- [Formal-kernel methods](formal-kernel-methods.md) — shared carriers, theorem scope, validation ladder, and visualization contract.
- [Design programs](design/README.md) — prospective architecture and research goals, kept separate from current catalogue and evidence claims.
- [GNN bridge](design/gnn-bridge/README.md) — cross-repo articulation with the GeneralizedNotationNotation pipeline (bridge CLI, Lean AST, and source custody).
- [FEP research horizons](design/fep-research-program/README.md) — dependency-ordered finite synthesis, smooth/stochastic lifting, and an end-to-end scientific case study.
- [Second-expansion chapter (`fep-121` to `fep-155`)](../manuscript/04i_formalism_catalogue_155.md) — finite risk, policy trees, native blankets, exponential-family duality, continuous time, and evidence boundaries.
- [Horizon-2 smooth/stochastic kernel chapter](../manuscript/04j_horizon2_smooth_stochastic_kernel.md) — posterior convergence, native semigroups, precision conditioning, and smooth information geometry.
- [Mathematical positioning supplement](../manuscript/08b_mathematical_positioning_supplement.md) — probability, topology, statistical geometry, embeddings, and result-family methods.
- [OpenAI mathematics review and modular analysis](../specs/openai-math-methods/README.md) — pinned reference corpus, canonical topic/assumption join, family context, and boundary diagnostics.
- [Topic reference](topics-reference.md) — canonical owners, inspection, and receipt semantics.
- [Pipeline](pipeline.md) — stages, modes, and result contract.
- [Quick reference](quickref.md) — copy-paste command quick start for operator and maintenance runs.
- [Glossary](glossary.md) — canonical vocabulary for modes, kernels, receipts, and evidence planes.
- [Report bundles](reporter.md) — run-directory layout, provenance files, and receipt validation.
- [CLI reference](cli-reference.md) — canonical command surface.
- [Configuration](configuration.md) — settings and environment overrides.
- [Lean 4](lean4.md) — pinned workspace and aggregate generation.
- [Lean landscape](lean-landscape.md) — generated dependency-ordered map of the formal modules.
- [Hermes](hermes.md) — HTTP client, cache, retries, and response validation.
- [Prove2me](prove2me.md) — Lean-formalization platform client: API-key auth, missions, proposals, and proof verification.
- [OpenGauss](opengauss.md) — SQLite state and artifact persistence.
- [Testing](testing.md) — local and CI validation.
- [Release procedure](release.md) — the versioned release gate and steps.
- [Cold start](cold-start-and-cleanup.md) — disposable output cleanup.
- [Theorem maturity audit](theorem-maturity-audit.md) — semantic scope review beyond compilation.
- [Formalism coverage](formalism-coverage.md) — generated breadth, declarations, imports, and semantic gaps.
- [Interactive formalism atlas](formalism-atlas.html) — offline searchable graph separating derivational formal edges, checked formal pairings, and conceptual relations, with accessible tables.
- [Static formalism atlas](formalism-atlas.svg) — deterministic publication-safe projection of the same graph.
- [Interactive formal-kernel dashboard](formal-kernel-dashboard.html) — deterministic numerical witnesses for selected checked laws.
- [Static formal-kernel dashboard](formal-kernel-dashboard.svg) — publication-safe projection of the numerical witness view.
- [Quality-gate decision](quality.md) — blocking Ruff lint and formatting policy.
- [Publication](development.md) — documentation, rendered-artifact, and projection-freshness gates (release-bundle and receipt validation live in `../HANDOFF.md`).

## Reference

- [Documentation specification](SPEC.md) — what the documentation set must cover and how it is kept self-contained.
- [Architecture](architecture.md) — package layout and the data flow between catalogue, Lean, Hermes, and OpenGauss.
- [Python API](api.md) — public package surface.
- [Formalism authorship guide](authorship-guide.md) — strengthening a reviewed topic and deciding when a new formalism is warranted.
- [Publication consistency review](publication-consistency-review.md) — reconciles archived publication wording with current theorem scope and evidence boundaries.
- [Branch coverage](coverage-branch.md) — the declared coverage configuration and what the gate measures.
- [Scaffold portability](scaffold-portability.md) — carrying the checkout kit and scaffold into another repository.
- [Troubleshooting](troubleshooting.md) — preflight, setup, and run failures with their remedies.

## Historical reviews

Dated snapshots and adjudications. Counts and verdicts reflect the date they
were written; current evidence lives in the generated reports above.

- [Mahakala adversarial review](mahakala-review.md) — 2026-07-31 external-style review of the repository.
- [Test suite review](test-suite-review.md) — 2026-07-31 snapshot of suite structure and gaps.
- [Relations endpoint adjudication](relations-endpoint-adjudication.md) — coverage-gate verdict on the reviewed-primary-qualified endpoint rule.

All paths in this directory resolve within this repository. Catalogue-derived
manuscript inputs are created by `uv run fep-lean catalogue`; coverage, atlas,
dashboard, and manuscript-render checks each retain a separate freshness gate.

The [repository execution contract](../AGENTS.md) owns the required checks.
[`.python-version`](../.python-version) selects Python 3.14 for validation;
[`pyproject.toml`](../pyproject.toml) defines the packaging floor and the 89%
line-coverage gate. The package floor does not expand validator acceptance.
Current open acceptance work is recorded in [`TODO.md`](../TODO.md).
