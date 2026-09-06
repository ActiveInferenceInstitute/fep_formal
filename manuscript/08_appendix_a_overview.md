# Appendix A: Formalisms Overview {#sec:appendix_comprehensive_formalisms_overview}

**Appendices B and C (material)** are one auto-generated file, `09z_unified_formalism_catalogue.md`, produced during Manuscript Artifacts. It juxtaposes, per `fep-NNN` topic, the fenced Lean body and the typeset display-math blocks (former appendices B and C). Stable descriptive metadata comes from `config/catalogue_metadata.yaml`, semantic review from `config/theorem_maturity.yaml`, canonical Lean bodies from family modules under `src/fep_lean/catalogue/bodies/`, and equation signatures from `src/fep_lean/catalogue/latex.py`; `scripts/_maint_build_topics_catalogue.py` joins them into the generated catalogue. Each topic has one display-math **block** per `theorem` (typically `aligned`), with a unique stable id `eq:fep-NNN-k`. Counts and validated evidence projections come from `manuscript_vars.yaml`.

## Complete Topic Catalogue {#sec:complete_topic_catalogue}

The **per-topic index** (id, human title, area, primary Mathlib path, and full `lean_sketch`) is not duplicated here: it appears in the **unified formalism appendix** ([@sec:appendix_b_full_topic_lean_catalogue]), with stable per-topic anchors `#sec:catalogue-fep-NNN` (Lean sketch) and `#sec:eqs-fep-NNN` (typeset LaTeX equations) for each `fep-NNN`. That file is regenerated from `config/topics.yaml` on every Manuscript Artifacts pass, so titles and bodies cannot drift from the committed catalogue.

Native compilation status for the full roster is **`{{compile_rate.total}}`** against Mathlib **`{{mathlib_tag}}`** / Lean **`{{lean_toolchain}}`**. `manuscript_vars.yaml` prefers an independently validated, live-source-bound native receipt and accepts a full-run verification manifest only through its separate claim-ready report contract. Diagnostics and verifier fields are summarized in [@sec:quantitative_execution_metrics].

**Summary**: All {{total_topics}} rows are `mathlib_status: real` in `topics.yaml`. Per-area rates are **`{{compile_rate.by_area.FEP}}`** (FEP core), **`{{compile_rate.by_area.ActiveInference}}`** (Active Inference), **`{{compile_rate.by_area.InfoGeometry}}`** (Information Geometry), **`{{compile_rate.by_area.BayesianMechanics}}`** (Bayesian Mechanics), and **`{{compile_rate.by_area.Thermodynamics}}`** (Thermodynamics); see [@sec:aggregate_metrics].

## Area Breakdown {#sec:area_breakdown_overview}

| Area (topics) | Native compile (verifier) | Mathlib domains |
|---------------|---------------------------|-----------------|
| FEP core ({{areas.FEP.count}}) | `{{compile_rate.by_area.FEP}}` | Measures, real logarithms |
| Active Inference ({{areas.ActiveInference.count}}) | `{{compile_rate.by_area.ActiveInference}}` | Finite sets, big operators, order |
| Information Geometry ({{areas.InfoGeometry.count}}) | `{{compile_rate.by_area.InfoGeometry}}` | Inner products, metric spaces |
| Bayesian Mechanics ({{areas.BayesianMechanics.count}}) | `{{compile_rate.by_area.BayesianMechanics}}` | Matrices, probability measures |
| Thermodynamics ({{areas.Thermodynamics.count}}) | `{{compile_rate.by_area.Thermodynamics}}` | Real logarithms and exponentials |
| **Total ({{total_topics}})** | **`{{compile_rate.total}}`** | — |
: Per-area topic counts, native compile status from the verifier, and the Mathlib domains each area reaches.

Rates come from the selected validated evidence projected into `manuscript_vars.yaml`:

- Receipt: `{{verify.run_id}}`.
- Native verifier ran: `{{verify.verify_lean_ran}}`.
- Clean / failed / recorded topics: `{{verify.compiles_true}}` / `{{verify.compiles_false}}` / `{{verify.topics_with_result}}`.

After any toolchain or sketch change, regenerate a source-bound receipt with:

```bash
uv run fep-lean verify \
  --fail-on-warnings \
  --receipt output/native-verification.json
```

Then refresh the catalogue and manuscript projections.

## Representative topics (pointers only) {#sec:representative_lean_sketches}

To avoid duplicating Lean that can drift from the SSOT, this appendix does **not** paste catalogue fences. The pointers below cover the variational-bound backbone (fep-001), Boltzmann--Gibbs weights (fep-031), and stick-breaking bookkeeping (fep-046).

| Topic | Appendix B (Lean) | Appendix C (display math) |
|-------|-------------------|---------------------------|
| fep-001 | [@sec:catalogue-fep-001] | [@sec:eqs-fep-001] |
| fep-031 | [@sec:catalogue-fep-031] | [@sec:eqs-fep-031] |
| fep-046 | [@sec:catalogue-fep-046] | [@sec:eqs-fep-046] |
: Representative topics, with pointers to the Lean body in Appendix B and the display math in Appendix C.

## Mathlib4 Imports Used Across the Catalogue {#sec:mathlib4_imports_catalogue}

Every shipped row in Appendix B declares its own Mathlib imports rather than relying on an implicit global prelude. The project uses measure/probability kernels and conditional independence, finite sums and sets, real logarithm/exponential and calculus, finite-dimensional matrices and metrics, information theory, contraction limits, and the real strong law. Pedagogical snippets may use broader imports for exposition only; they are not catalogue sources.

The generated [formalism coverage report]({{publication.repository_url}}/blob/{{source.commit}}/docs/formalism-coverage.md) is the exact import and declaration roster. It owns both the topic-to-Mathlib incidence table and the maintained formal-module dependency graph. The atlas renders those import dependencies separately from scientific edges, while formal relations require named declarations. This avoids a static appendix roster that would drift whenever a sketch narrows an import.

## Formalization Epistemology: Realism vs. Illusionism {#sec:formalization_epistemology}

The catalogue offers a structural way to inspect claims that appear in debates about FEP and consciousness (Solms, Dołęga, Wiese, 2023–2025) [@brainsblog2023]. Its typed measure-theoretic rows illustrate how candidate belief objects can receive explicit domains and assumptions, and its finite kernel composes one bounded generative-model instance through posterior, VFE, EFE, policy, and rollout layers. It does not formalize consciousness, establish that the finite model describes a living system, or adjudicate realist and illusionist positions.

For machine-checked native compilation, run:

```bash
uv run fep-lean verify \
  --fail-on-warnings \
  --receipt output/native-verification.json
uv run fep-lean catalogue
```

Validate the receipt against the live tree before using its result. Full-run manifests under `output/reports/run_*/` are a separate Hermes/OpenGauss evidence class and cannot substitute for the native receipt.
