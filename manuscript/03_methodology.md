# Methodology and System Architecture {#sec:methodology_and_system_architecture}

The project is organized around one methodological rule: a claim is no stronger than the evidence object that supports it. Catalogue generation, native Lean compilation, and a live Hermes/OpenGauss run are therefore separate modes with separate acceptance predicates. A deterministic catalogue build can establish source consistency; a native receipt can establish warning-free, `sorry`-free typechecking against a pinned toolchain; only a validated full-run receipt can support claims about model output, provider latency, or persisted sessions.

Readers new to Lean should begin with [@sec:lean_4_a_primer_for_active_inference_researchers]. The detailed components in [@sec:mathlib4_and_measure_theoretic_probability]--[@sec:pipeline_architecture_and_execution_profile] cover the library substrate, semantic maturity, optional LLM stage, native compiler bridge, and execution pipeline.

## System Architecture Overview {#sec:system_architecture_overview}

The architecture has three source layers and three evidence layers.

| Layer | Canonical input | Derived output | What it can establish |
|---|---|---|---|
| Authorship | roster/family metadata, maturity and novelty review, authored relations, family-owned topic bodies, and manifested formal resources | checkout/wheel `topics.yaml`; topic aggregate; foundation, composition-leaf, and import-aggregate Lean; coverage, atlas, and numerical dashboard | roster, source parity, declared semantic scope, maintained dependency structure, and witnessed composition |
| Native verification | exact topic roster plus generated catalogue/formal modules and pinned Lake workspace | native topic receipt plus formalism declaration/axiom receipt | compiler exit status, warnings, `sorry`/`sorryAx`, declaration resolution, toolchain and source digests |
| Full pipeline | live credentials, Hermes result, OpenGauss session state, native verification | hashed report bundle and independently validated full receipt | only the observed LLM/session/run claims |
: The three source layers and three evidence layers, with the canonical input, derived output and evidentiary reach of each.

`FEPPipeline` itself has four stages: Load Catalogue, Environment Validation, Gauss Sessions, and Manuscript Artifacts. In `catalogue` mode the Gauss stage is explicitly `not_run`. In `full` mode all selected topics must produce successful Hermes-backed results and clean Lean verification before the run is complete. `Reporter` executes only after a complete pipeline result; incomplete runs do not receive a successful report directory.

## The Command-Line Toolchain {#sec:the_command_line_toolchain}

The installed `fep-lean` command is the public interface:

```bash
uv run fep-lean catalogue
uv run fep-lean atlas --check
uv run fep-lean verify --fail-on-warnings --receipt output/native-verification.json
uv run python scripts/audit_formalisms.py --receipt output/formalism-audit.json
uv run fep-lean preflight
uv run fep-lean run
```

The first two commands are deterministic and offline: catalogue mode builds publication inputs, while the atlas command checks the coverage visualization. The native compiler command writes an atomic, source-bound topic receipt that records the actual compiler output and resolved Mathlib revision; the formalism audit separately resolves primary/evidence declarations, applies a versioned trusted-axiom policy, and inspects evidence axioms. `preflight` is a read-only capability check. `run` is the credentialed Hermes/OpenGauss path and fails closed when required capabilities are absent. Topic and area filters are useful during development, but a filtered native receipt is never publication-claim-ready for the full catalogue.

Maintenance scripts expose non-mutating drift checks:

```bash
uv run python scripts/_maint_build_topics_catalogue.py --check
uv run python scripts/_maint_build_fep_all_lean.py --check
uv run python scripts/_maint_build_formal_modules.py --check
uv run python scripts/build_formalism_coverage.py --check
uv run fep-lean atlas --check
uv run python scripts/build_formal_kernel_dashboard.py --check
uv run python scripts/theorem_maturity_audit.py
uv run python docs/theorem_ref_audit.py
```

## The Hermes Agent and LLM Integration {#sec:the_hermes_agent_and_llm_integration}

`fep_lean.llm.hermes.HermesExplainer` is an optional reviewer of a curated theorem body, not the owner of the formal kernel. It sends a system/user prompt pair to an OpenAI-compatible endpoint, parses the explanation and refined Lean block, and records retries and model-chain advances. The prompt requires preservation of imports, namespaces, tactic hints, and the absence of `sorry` in an already complete sketch.

Provider/model rosters are runtime configuration rather than scientific results. They are authoritative only in a validated report bundle. With no OpenRouter or Anthropic credential, full-mode preflight fails; an offline fixture result may exercise code paths in tests, but it is ineligible for publication claims.

See [@sec:the_hermes_ai_agent_and_llm_assisted_formalization] for the session protocol and the three distinct fallback mechanisms.

## The Native Lean Compilation Engine {#sec:the_native_lean_compilation_engine}

`fep_lean.verification.lean_verifier.LeanVerifier` writes each selected body to a temporary file in the pinned Lake workspace and invokes `lake env lean`. Leading imports are preserved; a shared preamble is used only for a sketch that has no explicit imports. Results retain compiler output, separated warnings and errors, `sorry` detection, duration, toolchain version, and an advisory failure class.

Native claim readiness is stricter than an exit code. The receipt must cover the exact ordered roster of {{total_topics}} topics, every row must compile, warning and `sorry` counts must both be zero, and the catalogue, canonical family-body sources, Lean toolchain, and Mathlib tag must match the live tree. Revalidation independently recomputes those conditions rather than trusting a stored `complete` flag.

The complementary formalism audit imports `FepSketches.composed`, checks every reviewed primary plus semantic/formal witness, and runs `#print axioms` over the evidence roster. Projection drift, unresolved names, warnings, timeouts, compiler failures, or `sorryAx` make that receipt incomplete. Standard logical axioms reported by Mathlib are retained rather than hidden.

## OpenGauss Workflow and State Integration {#sec:opengauss_database_integration}

OpenGauss here refers to the Math, Inc. Lean-workflow tool, not the similarly named database product. `GaussRunner` persists project sessions in SQLite, records the system/user/assistant turns, stores the refined sketch and structured compiler artifact, and closes each session with explicit Hermes and Lean outcomes. Raw compiler diagnostics remain in the artifact rather than being presented as model dialogue.

The state store improves auditability but does not confer correctness. Full-report validation checks the selected topic roster, verification source, summary/manifest agreement, current source and configuration digests, and hashes of required artifacts. A stale, partial, catalogue-only, or fixture-backed report cannot supply manuscript metrics.

## The Unified Execution Pipeline {#sec:the_unified_execution_pipeline}

The three supported execution contracts are intentionally non-interchangeable:

1. `catalogue`: validates sources and writes deterministic figures/manuscript data; it performs no verification.
2. `verify`: runs the native compiler without an LLM or session store and may emit a native receipt.
3. `run`: requires live credentials and state/toolchain capabilities, runs Hermes and native verification per topic, and emits a full report only on strict completion.

This separation removes the former ambiguity in which a catalogue-only `complete` flag could be read as empirical pipeline evidence. The manuscript renderer selects a current, independently validated native receipt for compile claims and a claim-ready full report for Hermes/OpenGauss claims; otherwise it emits explicit unavailable/false values.

## Standard Reproducibility Workflow {#sec:standard_reproducibility_workflow}

For native formal results:

```bash
uv sync --locked --extra dev
uv run python scripts/_maint_build_topics_catalogue.py --check
uv run python scripts/_maint_build_fep_all_lean.py --check
uv run python scripts/_maint_build_formal_modules.py --check
uv run python scripts/build_formalism_coverage.py --check
uv run fep-lean atlas --check
uv run python scripts/build_formal_kernel_dashboard.py --check
uv run python scripts/audit_formalisms.py --receipt output/formalism-audit.json
uv run fep-lean verify --fail-on-warnings --receipt output/native-verification.json
uv run fep-lean catalogue
uv run python scripts/render_manuscript.py --check
```

For a full live run, configure an accepted credential, run `uv run fep-lean preflight`, then `uv run fep-lean run`. The resulting report must pass the receipt validator before its Hermes or timing fields can enter manuscript variables. Neither path mutates authored manuscript Markdown: rendering writes to `output/manuscript/` only after validating every placeholder across the full source set.

## Area-Specific Methodological Constraints {#sec:area_specific_methodological_constraints}

The five areas are organizational lenses, not five independent foundations. Each row declares its actual imports, primary theorem, assumptions, non-vacuity argument, acceptance probe, and semantic disposition in generated coverage. The following summaries state the present boundary rather than an aspirational one.

### FEP Methodology ({{areas.FEP.count}} topics) {#sec:fep_methodology}

The FEP area combines measurable variational integrands, native extended-real KL divergence, exact scalar Laplace kernels, finite quadratic optimization dynamics, variational duality, generalized predictive-coding corrections, and finite learning/model-evidence bounds. fep-001 and fep-002 prove KL-remainder variational bounds; fep-015 supplies the measurable integrand contract; fep-016 exposes the exact Gaussian normalizer; and fep-032 compiles the closed-form gradient-descent iterate and its stable-step convergence. Later families add Gibbs duality, mean-field and importance-weighted bounds, precision-weighted prediction-error dynamics, PAC-Bayes, posterior-concentration, mixture-regret, Bayes-factor laws, and finite-law Laplace squared/Brier-risk transfer on explicit carriers. The reusable finite active-inference model additionally derives posterior-form VFE, its evidence lower bound, exact-posterior attainment, and uniqueness even for posteriors with zero-mass states. No theorem identifies all of these finite and measure-valued conventions without the bridges stated in their composition leaves.

### Active Inference Methodology ({{areas.ActiveInference.count}} topics) {#sec:active_inference_methodology}

Active-Inference rows combine discounted pragmatic cost, an explicit `ENNReal` EFE sign convention, policy-indexed reachable laws, finite-horizon Bellman and desirability recursions, native measure-KL information gain, normalized sum-product messages, support-aware softmax policies, and collective product-agent and consensus laws. The maintained kernel proves pragmatic-minus-epistemic and risk-plus-ambiguity decompositions under explicit support, normalized prior-weighted policy selection, action pushforward, chronological state rollout, recursively accumulated stage-dependent EFE, and a concrete two-stage Boolean witness in which feedback strictly improves on open-loop control. The later policy-tree foundation proves arbitrary finite-depth observation-contingent recursion on finite carriers, Bellman optimizer existence, open-loop embedding and dominance, treewise EFE decomposition, and the same strict Boolean witness. No result claims infinite-horizon or continuous-belief optimality, equivalence with every EFE formulation, or emergent agency for a collective.

### Information Geometry Methodology ({{areas.InfoGeometry.count}} topics) {#sec:information_geometry_methodology}

This area uses native `InformationTheory.klDiv`, including self-zero, finite-measure separation, and the composition-product chain rule. It contains a finite positive-definite weighted Fisher metric, the complete one-dimensional Bernoulli family, and a categorical score model with explicit full-rank and null-direction witnesses. The maintained geometry modules prove Fisher Gram PSD and conditional PD on simplex tangents, pullback laws, scalar Cramér--Rao under unbiasedness and score regularity, natural-gradient equivariance under an invertible chart, a mirror-descent three-point identity, an affine-projection Bregman Pythagorean law, and replicator--natural-gradient equivalence. The scalar exponential-family foundation adds normalization/full support, log-partition gradient and Hessian, centered score, Fisher--variance equality, KL--Bregman duality, and interval-local mean-coordinate injection. These sources do not define arbitrary smooth manifolds, affine connections, curvature, or general geodesic existence.

### Bayesian Mechanics Methodology ({{areas.BayesianMechanics.count}} topics) {#sec:bayesian_mechanics_methodology}

These rows include generic conditional-independence laws, reversible-kernel invariance, measure-theoretic and finite posterior reconstruction, transition--observation filtering and smoothing, hierarchical and posterior-predictive kernel composition, Bernoulli sufficient statistics and conjugate closure, finite causal interventions, and a nonzero stationary probability current. The maintained blanket and causal modules connect explicit finite carriers to exact conditional factorization, zero conditional mutual information, typed blanket-respecting dynamics, intervention normalization, descendant change, and named non-descendant invariance witnesses. The finite-to-native family further proves weighted-Dirac law/kernel embeddings, expectation and prediction transfer, native `CondIndepFun`, measurable endpoint coarsening, and rowwise factorized-transition closure. These sources do not prove blanket existence, mixture-level preservation, or causal identification for arbitrary systems, nor derive continuous Fokker--Planck dynamics.

### Thermodynamics Methodology ({{areas.Thermodynamics.count}} topics) {#sec:thermodynamics_methodology}

Thermodynamic rows cover the equilibrium Helmholtz derivative identity, finite conserved currents, binary entropy optimality, normalized Gibbs weights, Gaussian thermal entropy response and heat capacity, diagonal and edgewise entropy production, and a logical-erasure derivation of Landauer heat/work bounds from explicit second-law premises. The path-space family additionally normalizes forward and reverse finite path laws, proves reversal and fluctuation identities, states a finite Jarzynski equality with explicit work, inverse temperature, and normalization, and links reversible one-step dynamics to KL dissipation. The exact Boolean continuous-time family adds stochastic kernels, the Chapman--Kolmogorov semigroup, both master equations, stationarity, detailed balance, exponential relaxation, and quadratic Lyapunov decay for positive two-state rates. These finite laws do not constitute general constrained equilibrium statistical mechanics, SDE/PDE theory, or a microscopic thermodynamic derivation of the FEP.

## Catalogue Authorship Pipeline {#sec:catalogue_authorship_pipeline}

The source graph is explicit:

```text
config/catalogue_metadata.yaml             stable titles/areas/library hints
config/theorem_maturity.yaml               primary theorem + semantic review
config/formalism_novelty.yaml              expansion deltas + required bridges
config/formalism_relations.yaml            authored relations + capability history
src/fep_lean/catalogue/bodies/*.py          family-owned canonical Lean bodies
src/fep_lean/catalogue/registry.py          validated body manifest and merger
src/fep_lean/catalogue/latex.py             theorem-signature projection
src/fep_lean/formal/**/*.lean               manifested foundations + composition leaves
                    \ | /
                     v
src/fep_lean/catalogue/generation.py
        |                         |
        v                         v
config/topics.yaml       src/fep_lean/data/topics.yaml
        |
        +--> lean/FepSketches/fep_all.lean
        +--> lean/FepSketches/{foundations,compositions,aggregate}.lean
        +--> docs/formalism-coverage.{md,json}
        +--> docs/formalism-atlas.{svg,html}
        +--> docs/formal-kernel-dashboard.{svg,html}
```

The braces in this schematic mean the explicitly manifested formal-module set, not a literal filename or an inferred directory glob. `scripts/_maint_build_formal_modules.py` owns the exact source-to-workspace projection. The atlas displays authored scientific relations and module-import dependencies as separate edge classes; the dashboard evaluates deterministic numerical witnesses but supplies no proof evidence.

Both YAML copies are byte-identical generated projections: one supports checkout workflows and one ships in the wheel. Strict loaders reject missing/extra rows, order drift, unknown semantic values, theorem/signature count mismatches, and a primary theorem absent from the canonical body. The generator restores its own provenance header, so formatting churn cannot silently create a second authoring source.

## Verification Workflow and Cache Strategy {#sec:verification_workflow_cache_strategy}

The project pins `{{lean_toolchain}}` and Mathlib `{{mathlib_tag}}`. `lake exe cache get` may populate dependency `.olean` files; no validation command implicitly downloads or rebuilds them. Verification checks the existing workspace and returns a structured failure when the toolchain or cache is absent.

`verify_batch` is deliberately serialized (`max_workers=1`) to avoid races over temporary files and build artifacts. Warm-cache duration is environmental and is therefore reported only from a receipt, never as a fixed value in prose. The aggregate/composed targets provide complementary whole-library checks that catch namespace collisions, broken seams, and warning-producing declarations. The declaration/axiom probe then confirms that names cited as evidence resolve through those exact modules.

## execution-integrity Testing Policy {#sec:zero_direct_testing_policy}

Tests pin observable contracts rather than publication constants. Catalogue tests exercise strict schema and source parity; native tests invoke the real Lean subprocess where marked; SQLite tests use isolated real databases; HTTP behavior is tested through controlled local servers or is guarded by explicit live credentials. Distribution tests build a wheel, install it into an isolated environment, import `fep_lean`, execute CLI help, load packaged data, and confirm that obsolete top-level names such as `catalogue` are not exported.

External services remain external evidence. Offline fixture responses are useful for parser and failure-path tests, but cannot make a full report claim-ready.

## Namespace Convention and Topic Isolation {#sec:namespace_convention}

Python code lives under one `fep_lean` namespace. Lean declarations use an inner stable topic namespace (`FEP002`, `FEP014`, and so on); the generated aggregate adds an outer `fep_fepNNN` namespace so helper declarations from different self-contained sketches cannot collide. The coverage audit counts declarations and imports from canonical bodies, while theorem-reference auditing ensures that manuscript identifiers resolve to actual declarations.

## PYTHONPATH Isolation {#sec:pythonpath_isolation}

The installable package no longer relies on path precedence among generic top-level names such as `catalogue`, `pipeline`, `llm`, or `output`. Checkout commands run through `uv`, and installed commands import `fep_lean.*`. The wheel includes its generated catalogue as package data, so loading the default catalogue does not depend on locating the repository root.

## Parallelism Model {#sec:parallelism_model}

Formal compilation is serialized. In full mode, optional single-worker prefetch may overlap the next Hermes request with current Lean verification, but it does not reorder persisted topic results or permit multiple concurrent compiler processes. Receipt topic order remains the requested catalogue order, which makes completeness and digest validation deterministic.

## Detailed Methodology Sub-Sections {#sec:detailed_methodology_sub_sections}

The following sub-sections give the necessary depth without changing these contracts: the Lean primer ([@sec:lean_4_a_primer_for_active_inference_researchers]), pinned Mathlib surface ([@sec:mathlib4_and_measure_theoretic_probability]), proof/semantic maturity ([@sec:the_sorry_mechanism_and_formalization_maturity]), optional Hermes stage ([@sec:the_hermes_ai_agent_and_llm_assisted_formalization]), native receipt ([@sec:native_lean_4_compilation_and_zero_direct_verification]), and full pipeline ([@sec:pipeline_architecture_and_execution_profile]).
