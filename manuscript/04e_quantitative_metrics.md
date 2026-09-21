## Quantitative Execution Metrics {#sec:quantitative_execution_metrics}

This section reports three surfaces separately: catalogue coverage, native Lean evidence, and optional full-pipeline evidence. A count from one surface is never substituted for another. The generated formalism coverage audit is authoritative for source structure; native and full receipts are authoritative for execution claims.

![Topic distribution across the five catalogue areas. The figure visualizes catalogue breadth only.](../output/figures/topics_by_area.png){#fig:topics_by_area width=80%}

The area-distribution figure above visualizes catalogue breadth only. It does not measure scientific maturity or compilation success.

### Aggregate Catalogue Metrics {#sec:aggregate_metrics}

The catalogue contains {{total_topics}} topics across {{total_areas}} areas. `mathlib_status` records whether a row is intended to use available pinned-library infrastructure; semantic disposition records whether the primary theorem reaches the topic-facing claim. The two fields answer different questions. Maintained foundation/composition declarations are counted separately from topic declarations before the package total is formed:

| Source layer | Modules | Theorem declarations |
| --- | ---: | ---: |
| Topic catalogue | {{formalism.metrics.topics}} topic modules | {{formalism.metrics.topic_theorems}} |
| Maintained foundations | {{formalism.metrics.foundation_modules}} | {{formalism.metrics.foundation_theorems}} |
| All maintained formal resources, including composition | {{formalism.metrics.formal_modules}} | {{formalism.metrics.formal_resource_theorems}} |
| Package total, without double-counting resources | — | {{formalism.metrics.theorems}} |
: Module and theorem-declaration counts by source layer, computed at render time from the formalism audit.

| Area | Topics | Native receipt rate |
| --- | ---: | ---: |
| FEP | {{areas.FEP.count}} | `{{compile_rate.by_area.FEP}}` |
| Active Inference | {{areas.ActiveInference.count}} | `{{compile_rate.by_area.ActiveInference}}` |
| Bayesian Mechanics | {{areas.BayesianMechanics.count}} | `{{compile_rate.by_area.BayesianMechanics}}` |
| Information Geometry | {{areas.InfoGeometry.count}} | `{{compile_rate.by_area.InfoGeometry}}` |
| Thermodynamics | {{areas.Thermodynamics.count}} | `{{compile_rate.by_area.Thermodynamics}}` |
| **Total** | **{{total_topics}}** | **`{{compile_rate.total}}`** |
: Topic count and native receipt rate for each catalogue area.

The runtime projection reports the following receipt-derived values:

| Field | Value |
| --- | --- |
| Evidence kind | `{{verify.evidence_kind}}` |
| Claim-ready native/full Lean evidence | `{{verify.claim_ready}}` |
| Receipt identifier | `{{verify.run_id}}` |
| Topics with compiler results | {{verify.topics_with_result}} |
| Compiled | {{verify.compiles_true}} |
| Failed compilation | {{verify.compiles_false}} |
| Warnings | {{verify.warning_count}} |
| Admitted proofs (`sorry` occurrences) | {{verify.sorry_occurrences}} |
| Topics containing `sorry` | {{verify.sorry_topics}} |
| Topic IDs that failed to compile | {{verify.failed_compile_topic_ids}} |
| Topic IDs not clean (failed, warned, or admitted) | {{verify.not_clean_topic_ids}} |
| Measured compiler time | {{verify.duration_seconds}} s |
| Mean measured time per result | {{verify.mean_topic_s}} s |
| Lean / Mathlib pin | `{{lean_toolchain}}` / `{{mathlib_tag}}` |
: Receipt-derived fields of the runtime verification projection.

A native receipt becomes claim-ready only for the exact ordered roster of {{total_topics}} topics with every result compiling, zero errors, zero warnings, zero `sorry`, actual Lean output matching the configured pin, the resolved Mathlib commit, finite timing evidence, and source/toolchain digests matching an explicitly supplied live tree. A valid subset or structurally validated unbound receipt remains useful diagnostic evidence but cannot populate the full-catalogue headline.

### Maturity Distribution by Area {#sec:maturity_distribution}

All rows currently carry `mathlib_status: real`, but that is a compile-intent classification, not a semantic result. The separate semantic audit reports {{semantic_dispositions.formalized}} directly formalized, {{semantic_dispositions.conditional_proxy}} conditional, and {{semantic_dispositions.structural_proxy}} structural rows at their stated scopes. The generated area-by-disposition matrix and per-topic assumptions live in `docs/formalism-coverage.md`; reproducing that matrix here would create a second owner.

### Formalism Composition and Capability Ledger {#sec:formalism_composition_metrics}

The authored semantic graph contains **{{formalism.metrics.authored_relation_edges}}** reviewed edges. Of these, **{{formalism.metrics.formal_relation_witnesses}}** are derivational formal edges and **{{formalism.metrics.formal_pairing_witnesses}}** are checked pairings whose theorem certifies both endpoint laws without claiming that one follows from the other. Together they form **{{formalism.metrics.theorem_witnessed_relations}}** qualified Lean declaration witnesses. The remaining edges are explicitly conceptual or blockers and therefore carry no proof claim. The retained capability ledger contains {{formalism.metrics.capability_nodes}} nodes: {{formalism.capability_status_counts.open}} open, {{formalism.capability_status_counts.partial}} partial, and {{formalism.capability_status_counts.satisfied}} satisfied. “Unresolved” includes both open and partial nodes, so its generated count is {{formalism.metrics.open_capabilities}}.

`docs/formalism-atlas.svg` and `docs/formalism-atlas.html` visualize this exact join. The atlas renders formal-module import dependencies separately from authored scientific relations, so code reuse cannot masquerade as a theorem witness. `docs/formal-kernel-dashboard.svg` and its interactive HTML companion evaluate one deterministic numerical witness for each of the {{expansion_families}} expansion families, including support, normalization, contraction, rank, risk-transfer, feedback, conditional-independence, duality, master-equation, and tail-bound boundaries. Every witness exposes typed checks with individual tolerances rather than one undifferentiated residual. Those values are validation diagnostics, not proof evidence. The declaration/axiom audit must still resolve formal witnesses, while the native receipt covers the exact {{total_topics}} topic bodies and the maintained modules compile through their manifested projection.

### Hermes LLM Performance {#sec:hermes_performance}

Hermes commentary is optional and has no bearing on native Lean acceptance. Manuscript Hermes metrics are exposed only from an independently validated, claim-ready full report. At render time, full-run claim readiness is `{{full.claim_ready}}`.

| Full-run field | Value |
| --- | --- |
| Report run ID | `{{hermes.run_id}}` |
| Processed topics | {{hermes.processed}} |
| Successful Hermes calls | {{hermes.success_count}} |
| Primary model | `{{hermes.primary_model}}` |
| Models used | {{hermes.models_used}} |
| Model-chain advances | {{hermes.model_fallback_count}} |
| Same-model network retries | {{hermes.network_retry_count}} |
| Hermes-refined sketches compiling | {{hermes.hermes_lean_compiles_count}} |
| Mean measured topic time | {{hermes.mean_topic_s}} s |
| Token total | {{hermes.tokens_total}} |
: Hermes full-run fields, exposed only from an independently validated, claim-ready report.

When `full.claim_ready` is false, zero or empty cells above mean *unavailable evidence*, not an observed zero-event experiment. Catalogue mode cannot populate this table.

### Lean 4 Verification Timing {#sec:lean_timing_distribution}

Only receipt-recorded elapsed time is reported: {{verify.duration_seconds}} seconds in total and {{verify.mean_topic_s}} seconds per result for `{{verify.run_id}}`. We do not generalize these machine- and cache-dependent observations into universal cold/warm timing ranges.

### Error Category Distribution {#sec:error_category_distribution}

`LeanVerifier` retains compiler errors, warnings, and an advisory failure category for each topic. The current receipt summary reports {{verify.compiles_false}} compile failures, {{verify.warning_count}} warnings, and {{verify.sorry_occurrences}} admitted proofs across {{verify.sorry_topics}} topics. Per-topic rows in the receipt, rather than a manually maintained chart, are authoritative.

### Live Verification Error Taxonomy: Hermes-Assisted Run {#sec:live_verification_error_taxonomy}

No Hermes-assisted result is described as live unless `full.claim_ready` is true. Full receipts must bind every selected row to a successful provider session and model, direct `hermes_refined` compilation, byte-identical refined/final Lean and its digest, actual compiler output, the resolved Mathlib commit, complete per-topic artifacts, redundant manifest parity, and current source/configuration digests. The renderer currently reports full claim readiness as `{{full.claim_ready}}`.

Historic LLM failures are useful engineering anecdotes but are not current mathematical evidence. The canonical failure rows remain in validated report bundles rather than being copied into a static taxonomy.

### Baseline Comparison: Hermes-Assisted vs Manual Drafting {#sec:baseline_comparison}

This project has not run a controlled human-versus-Hermes authoring study. It therefore makes no comparative claim about proof length, first-pass success, or authoring speed. A defensible comparison would require preregistered tasks, identical library context, blinded adjudication of semantic adequacy, and separate compiler and wall-clock outcomes.

## Maturity Migration Pathways {#sec:maturity_migration_pathways}

Rows migrate only through evidence, not elapsed calendar time. A proxy becomes `formalized` when its primary theorem states the reviewed invariant at the advertised scope, its assumptions are explicit, a non-vacuous witness exists where appropriate, and native acceptance remains clean. Mathlib pin changes, new definitions, or more permissive prose do not automatically promote a row.

## Error Taxonomy: LLM Failure Modes {#sec:error_taxonomy_llm_failure_modes}

The useful distinction is contractual:

- transport and provider failures prevent full-mode completion;
- malformed or invented Lean fails compiler verification;
- `sorry` fails native claim readiness even if elaboration succeeds;
- a compiling theorem with the wrong scope is a semantic-audit failure;
- a stale or tampered artifact is a receipt-validation failure.

These failure classes are independently observable and should not be collapsed into one success rate.

## Cross-Area Mathlib Dependency Analysis {#sec:cross_area_mathlib_dependency_analysis}

The generated coverage audit derives the exact Mathlib module-to-topic incidence relation from canonical imports. Shared imports indicate library reuse, not logical dependence between catalogue topics. Conceptual relationships must be reviewed separately, and both derivational relations and formal pairings must name checked declarations that consume both endpoint namespaces; the project does not infer any relation from common tokens such as `State`, `Policy`, or `Measure`.
