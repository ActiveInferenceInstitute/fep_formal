## Comparative Analysis with Existing LLM-ITP Systems {#sec:comparative_analysis_with_existing_llm_itp_systems}

FEP Lean is best understood as a domain catalogue and evidence pipeline, not as a new automated prover. Its canonical Lean bodies are researcher-curated; the optional model reviews those bodies; the kernel checks the resulting term; and a semantic audit separately asks whether the compiled statement captures the advertised concept. Comparing only “proof success” would therefore misstate the system's task.

| System family | Primary task | Starting point | Typical success evidence | Relation to FEP Lean |
|---|---|---|---|---|
| LeanDojo / LEGO-Prover [@yang2024leandojo; @xin2024lego] | tactic/proof search | formal theorem | closed proof and benchmark result | possible downstream proof-search layer |
| DeepSeek-Prover [@deepseek2024prover; @deepseek2025proverv2] | formal proof generation | formal or translated problems | benchmark proof acceptance | complementary to statement curation |
| Draft, Sketch, Prove [@jiang2023draft] | autoformalization plus proof | informal proof/problem | formal statement and discharged obligations | related translation workflow at theorem scale |
| PhysLean [@toobysmith2024] | human-led physics library | domain mathematics | reviewed definitions/theorems in Lean | closest library-building analogue |
| FEP Lean | catalogue curation, semantic audit, and evidence separation | contested domain claims | source parity + native receipt + semantic disposition | formalization-surface map for FEP |
: LLM-ITP system families compared with FEP Lean by primary task, starting point and the evidence each typically reports.

The distinctive contribution is the coupling of breadth with claim calibration: every row has an exact source, declaration inventory, primary theorem, assumption review, non-vacuity note, and disposition. This is not evidence that the approach outperforms proof-search systems on their benchmarks.

### Manual vs Hermes-Assisted Formalization {#sec:manual_vs_hermes_assisted}

No controlled human-time experiment is included, so the manuscript does not report speedups, first-pass error rates, or “weeks versus hours” estimates. The defensible comparison is functional:

| Activity | Researcher-owned path | Optional Hermes contribution | Acceptance owner |
|---|---|---|---|
| Select domain claim and scope | author/reviewer | may summarize | semantic review |
| Write canonical theorem and imports | author/reviewer | may suggest a revision in a full run | canonical source review |
| Establish type/proof correctness | invoke Lean | none | Lean kernel + native receipt |
| Explain proof strategy | write prose | may draft commentary | author/reviewer |
| Assert model/time/cost results | inspect full run | generates observed fields | validated full receipt |
: Division of work between the researcher-owned path and the optional Hermes contribution, with the acceptance owner for each activity.

This allocation is intentionally conservative. Uniform model commentary can reduce blank-page effort, but it also creates new review work: semantic drift, invented library names, missing code fences, and provider-dependent output must be checked. A future comparison should randomize topics, preregister editing-time and semantic-fidelity metrics, and distinguish initial draft, compile repair, and expert review.

### Comparison to Similar Projects {#sec:comparison_similar_projects}

PhysLean demonstrates the value of a human-reviewed, domain-specific Lean library. FEP Lean shares the commitment to a pinned formal substrate but pursues a different shape: {{total_topics}} deliberately bounded domain instances, {{formalism.metrics.theorem_witnessed_relations}} checked cross-topic witnesses with derivational and non-implicational pairing kinds kept distinct, a reusable formal kernel, and a machine-readable capability/blocker graph rather than a single mature mathematical hierarchy. Its deepest strands include native Bayesian kernels; posterior VFE and EFE on shared finite carriers; finite-dimensional Fisher geometry; concrete blanket factorization and dynamics; path-space thermodynamics; collective inference; and asymptotic and finite-sample learning laws. Its breadth still contains intentionally small topic-scoped results. LeanDojo, LEGO-Prover, DeepSeek-Prover, Lean Copilot [@song2025copilot], and Draft, Sketch, Prove address premise selection, tactic generation, proof completion, or autoformalization. Those capabilities could assist further strengthening, but they do not decide which formal statement resolves a contested FEP interpretation.

The repository makes no priority claim about being the first FEP formalization or the largest thermodynamics corpus. Such claims require a systematic, dated literature review and can become stale. Its inspectable claim is narrower: this release contains the exact catalogue and formalism coverage recorded by its generated reports and bound native receipt.

### State-Space Models, Domain-Specific Languages, and Generalized Notation {#sec:gnn_dsl_complementarity}

Executable Active-Inference tools and notations such as pymdp [@heins2022pymdp] or GNN [@smekal2023gnn] occupy a different layer. They specify and run model instances; Lean states and proves invariants. This package implements one such bridge from GNN. Four maintained modules carry it. `FEP.GnnDocument` (`lean/FepSketches/gnn_document.lean`) fixes the GNN abstract syntax and a `WellFormed` predicate that is decidable, so document validity is discharged by `decide` rather than asserted. `FEP.GnnDenotation` supplies `denoteDiscrete`, which sends a discrete-family document together with a conforming numeric payload to a `GenerativeModel` of `active_inference.lean` -- the same carrier the catalogue's finite active-inference rows use -- and `symBoolDoc_denotation` proves that the exemplar document's denotation is definitionally the hand-written `symmetricBoolModel trueBiasedPolicyPrior`, which is exactly the executable-refines-formal statement the next paragraph names as a requirement. `FEP.GnnContinuous` does the same for a linear-Gaussian family. `FEP.GnnRenderStatements` states, and proves for the exemplar, that the pymdp, ActiveInference.jl and JAX renderings of a document agree with its denotation, and that a policy rollout equals the corresponding kernel power. Provenance runs through `fep-lean bridge`, whose certificates are pinned to source digests in `specs/gnn-bridge-w2-source-custody/source-pin.json`.

The obligations the bridge discharges are the normalization ones: `DiscreteConforms` requires every row of the payload to be a probability vector, and the denotation cannot be formed without those proofs. Conditional-independence obligations are not generated -- no module in the bridge states one -- and the denotation is defined for the discrete and linear-Gaussian families rather than for arbitrary GNN documents. The specification slices are `specs/gnn-bridge-*`.

This distinction matters for validation. A numerical implementation can be tested on data while a theorem can be checked for deductive correctness; neither subsumes the other. End-to-end assurance needs both, plus a proof that the executable representation refines the formal one.

### Our Approach vs GPT-4-Class Direct Lean Generation {#sec:gpt4_direct_comparison}

The project has not run a controlled direct-generation baseline, so it does not claim a higher compile rate than a named frontier model. Its architecture embodies a testable hypothesis: separating deterministic theorem ownership from stochastic review should reduce run-to-run drift and make provenance easier to audit.

A valid future baseline would hold the topic statement, toolchain, Mathlib pin, prompt budget, number of repair attempts, and human-review budget fixed. It would report at least:

- syntactic extraction rate;
- warning-free and `sorry`-free compile rate;
- theorem-statement preservation;
- semantic disposition under blinded expert review;
- time and token cost; and
- reproducibility across multiple model seeds or provider runs.

Without those controls, comparing a curated catalogue's native compile rate to one-shot generated code would conflate authorship with verification.

### Quality Metrics {#sec:comparative_quality_metrics}

The publication metrics are deliberately split:

| Metric family | Current source |
|---|---|
| roster, areas, maturity tags | generated `topics.yaml` |
| semantic breadth/depth | `docs/formalism-coverage.md` |
| declaration/import counts | parsed canonical Lean source |
| native compile/warning/`sorry` outcomes | validated `output/native-verification.json` |
| Hermes success, model, retries, tokens, latency | validated full report only |
: Publication metric families and the source each is currently drawn from.

The native compile rate rendered for this source state is `{{compile_rate.total}}`; its evidence kind is `{{verify.evidence_kind}}`, warning count `{{verify.warning_count}}`, and claim-ready predicate `{{verify.claim_ready}}`. Full Hermes/OpenGauss claim readiness is separately `{{full.claim_ready}}`. These values are not interchangeable, and a false predicate is a result rather than a placeholder for a preferred headline.

### Time Comparison {#sec:time_comparison}

Native duration is measured by the receipt (`{{verify.duration_seconds}}` seconds for its exact roster and environment). No cross-person manual baseline is available. Full-model duration is reported only when a current full receipt is claim-ready. This avoids turning hardware-, cache-, network-, and provider-specific observations into general productivity claims.

### Implications for Active Inference Practitioners {#sec:implications_for_active_inference_practitioners}

The catalogue and finite kernel already provide invariants that executable systems can use as specifications: support-aware policy normalization, exact transition--observation posterior reconstruction, Bellman recursion, matrix--vector message propagation, finite policy minimizers, chronological rollout, action-law pushforward, and both EFE decompositions. They do not prove that pymdp, SPM, or another implementation satisfies those statements, because no refinement mapping from implementation state to Lean objects has been supplied.

The practical next step is therefore not to label the implementation “verified,” but to define that mapping and prove focused conformance lemmas. This would connect formal breadth to software behavior while preserving the manuscript's central distinction among a compiling theorem, a semantically adequate model, and an empirically validated system.
