# Introduction {#sec:introduction}

## The Verification Gap in Mathematical Physics {#sec:the_verification_gap_in_mathematical_physics}

The Free Energy Principle (FEP) offers a proposed unifying account of perception, action, and learning [@friston2010free]. Strong readings associate the persistence of self-organizing systems with minimization of a variational free-energy functional; narrower readings concern explicitly specified generative models and particular dynamics. Over the past two decades, the FEP has generated a rich theoretical ecosystem spanning Active Inference [@parr2022active], Information Geometry [@amari2016information], and Bayesian Mechanics [@dacosta2024bayesian]. Yet the mathematical foundations of this ecosystem—drawing simultaneously on measure theory, stochastic differential equations, differential geometry, and category theory—remain difficult to parse, verify, and extend. A working researcher reconstructing a derivation from a flagship paper must typically cross-reference textbooks in four distinct subfields, reconcile inconsistent notation, and silently patch over assumptions the author judged too obvious to state.

This difficulty is not merely pedagogical. Recent critiques [@biehl2021critique; @aguilera2022particular; @andrews2021math] raise substantive concerns about the mathematical status of key FEP claims: the uniqueness of Markov blanket decompositions, the conditions under which steady-state densities exist, and the extent to which variational bounds apply beyond specific model classes. Such debates expose a **verification gap** in mathematical physics: informal review does not provide a mechanically replayable check of every inference. In a literature where results are repeatedly reused, an unstated hypothesis can propagate into later derivations. Formal verification provides a precise checksum: an accepted theorem is derivable from the stated definitions, hypotheses, imported lemmas, and Lean's trusted kernel. That certificate does not establish that the definitions model the world correctly, that the hypotheses hold empirically, or that a narrowed theorem captures the motivating scientific claim. A catalogue of theorem statements, semantic audits, and reproducible compiler evidence lets later work inspect those three questions separately. When the free energy $F$ is claimed to upper-bound surprise, the argument hinges on a chain of measure-theoretic manipulations:

$$
F[q, p] = \KL[q(\psi \mid m) \,\|\, p(\psi \mid s, m)] - \log p(s \mid m) \geq -\log p(s \mid m),
$$ {#eq:intro_vfe_bound}

The inequality in [@eq:intro_vfe_bound] holds because Kullback–Leibler divergence is non-negative by Gibbs' inequality. Each of those symbols—$q$, $p$, $\KL$, $\log p(s \mid m)$—carries type-theoretic weight: $q$ is a probability measure absolutely continuous with respect to $p$, $\KL$ is the Radon–Nikodym-derivative integral $\int \log \frac{dq}{dp}\, dq$, and $\log p(s \mid m)$ is a real-valued random variable. In a journal proof these conditions are implicit; in a theorem prover they must be declared, and the compiler rejects the proof if they are not.

## Why Formal Verification of FEP Matters for Cognitive Science {#sec:why_formal_verification_matters}

The stakes are concrete. Active Inference is now used to model cortical processing, motor control, psychiatric conditions, and the behavior of multi-agent biological systems. When a clinical claim rests on the "free energy minimization" rationale, the underlying inequality should be correct by construction rather than by editorial consensus. Three specific benefits follow from machine-checked FEP mathematics:

1. **Unambiguous statements.** Each theorem forces explicit declaration of the measurable space, the dominating measure, and the policy type, eliminating the category errors that [@andrews2021math] identify as pervasive in the literature.
2. **Compositional reasoning at scale.** Once a lemma (for example, KL non-negativity) is kernel-checked, downstream proofs may reuse its statement without replaying its implementation, while still inheriting its exact hypotheses. A community library of FEP theorems would give each new manuscript a springboard rather than a restart.
3. **Automated differentiation of hype from theorem.** When Lean refuses to close a goal, the author sees precisely which hypothesis is missing. This provides a principled interface between informal intuition and formally defensible claim.

## Interactive Theorem Provers as Resolution Mechanism {#sec:interactive_theorem_provers_as_resolution_mechanism}

Interactive Theorem Provers (ITPs) such as Lean 4 [@moura2021lean] address this challenge directly. Lean 4's dependent type system implements the Calculus of Inductive Constructions, so accepted theorems are checked against the kernel. A theorem proven in Lean produces a *proof object*—a certificate that an independent verifier can re-check. Its community library, Mathlib4 [@mathlib2020], covers topology, measure theory, algebra, geometry, and many other areas. Notable successes include the Lean 4 formalization of the polynomial Freiman–Ruzsa proof [@pfr2023lean] and the Liquid Tensor Experiment [@scholze2022liquid]. Stochastic process foundations—critical for FEP path integrals—remain uneven in Mathlib4 at large; the shipped catalogue rows are nonetheless `sorry`-free under this project's maturity policy, while broader SDE and continuous-time stochastic infrastructure remains aspirational where the pinned revision does not supply a reviewed interface (see [@sec:gap_analysis]).

Lean 4 was selected for project-specific, reproducible reasons rather than a mutable cross-prover ranking:

| Requirement | Evidence at the pinned Lean/Mathlib revision | Project consequence |
|-------------|----------------------------------------------|---------------------|
| Measure-valued probability | `Measure`, Radon--Nikodym derivatives, finite measures, and Markov kernels | State probability claims at their native measure-theoretic level |
| Information theory | `InformationTheory.klDiv` plus self, zero-characterization, Gibbs, and kernel chain-rule lemmas | Reuse native KL results in fep-002 and fep-014 |
| Executable proof tooling | Lean elaborator, kernel, and tactics available through the pinned Lake workspace | Produce replayable per-topic and aggregate compiler evidence |
| Research-tool integration | Lean source is text, compiler results are structured, and local tooling can isolate invocations | Keep optional LLM commentary outside the acceptance boundary |
: Prover-selection requirements, the evidence each one is checked against at the pinned Lean/Mathlib revision, and the consequence for this project.

This is a fitness claim for the present catalogue, not a claim that Lean dominates Coq, Isabelle/HOL, Agda, or another prover for every physical theory.

## Origins and Context: FEP and Lean 4 / Mathlib4 Maturity {#sec:context_fep_lean_mathlib}

The FEP was introduced by Karl Friston in a sequence of papers between 2005 and 2010 [@friston2005theory; @friston2006free; @friston2010free], extending Helmholtz-machine and predictive-coding ideas. Active-Inference accounts subsequently developed perception–action formulations [@friston2017active], while recent Bayesian-mechanics work developed path-integral and non-equilibrium-statistical-mechanics connections under explicit modeling assumptions [@dacosta2024bayesian; @friston2024path]. The core variational objective is often written as

$$
F = \mathbb{E}_{q}[\log q(s) - \log p(o, s)]
$$ {#eq:intro_vfe_expected}

[@eq:intro_vfe_expected] is the negative evidence lower bound under the usual variational-Bayes construction. Connections to Helmholtz free energy require a specified energy map, normalization, and units; [@sec:thermo_helmholtz_bridge_derivation] states one such bridge and separates it from the current Lean result.

Lean 4 reached a comparable inflection point in parallel. Lean 4.0.0 was released in 2023, Mathlib4 completed its migration from Lean 3 in the same year, and the pinned toolchain used in this work (**`{{lean_toolchain}}`**, Mathlib4 **`{{mathlib_tag}}`**) includes mature measure theory and a native Kullback--Leibler divergence API. The catalogue imports `Mathlib.InformationTheory.KullbackLeibler.Basic` and `.ChainRule` directly. This matters methodologically: library availability is established from the pinned source and compiled declarations, not inferred from secondary roadmap commentary.

## LLM-ITP Integration: Beyond Problem Solving {#sec:llm_itp_integration_beyond_problem_solving}

The integration of Large Language Models with ITPs has produced strong results in parallel. Systems such as LeanDojo and ReProver [@yang2024leandojo], LEGO-Prover [@xin2024lego], DeepSeek-Prover [@deepseek2024prover], and the more recent DeepSeek-Prover-V2 [@deepseek2025proverv2] demonstrate that LLMs can effectively navigate proof search spaces, while AlphaProof [@alphaproof2024] solved International Mathematical Olympiad problems at a silver-medal level. Lean Copilot [@song2025copilot] brings LLM-assisted tactic suggestion directly into the developer workflow. The pinned Lean 4 **`{{lean_version}}`** toolchain (`lean/lean-toolchain`) and Mathlib4 **`{{mathlib_tag}}`** supply automation including `grind` (SMT-style), `positivity`, and related tactics, expanding the proof capabilities available to our pipeline.

Our work targets the **axiomatization of a physical theory** in a proof assistant: turning informal FEP statements into well-typed Lean specifications. Related formalization efforts exist nearby (e.g., categorical ontology definitions or classical simulation boundaries; see [@namjoshi2026fundamentals]); this catalogue is a systematic, template-integrated slice focused on FEP-facing rows. The task demands domain knowledge spanning neuroscience, statistical mechanics, and measure theory—material that must be *translated* from informal mathematical physics into formal specifications, not merely retrieved from Mathlib4.

## The FEP Lean Pipeline {#sec:the_fep_lean_pipeline}

The package has three intentionally separate evidence modes. Catalogue mode produces deterministic offline projections—including the coverage report and formalism atlas—and carries no verification claim. Native mode compiles selected canonical topic bodies with the pinned Lean/Mathlib workspace, can write a digest-bound topic receipt, and has a separate declaration/axiom audit for reviewed formal witnesses. Full mode additionally requires Hermes and OpenGauss capabilities and produces a report bundle whose hashes, source digests, topic roster, and verification provenance are independently checked. A success bit from one mode is never reused as evidence for another.

This separation is central to the research design. The Lean kernel, not an LLM, decides whether a topic body type-checks. The semantic audit then asks a different question: whether the proved statement reaches the topic-facing scientific claim. Finally, receipt validation asks whether a reported run corresponds to the current source. The manuscript renderer consumes only those typed projections and refuses unresolved variables. The current rendered native compilation rate is **`{{compile_rate.total}}`**; the evidence kind is **`{{verify.evidence_kind}}`**, and full-run claim readiness is **`{{full.claim_ready}}`**.

## Research Contributions {#sec:contributions}

This manuscript makes five principal contributions:

- **(C1) A distributable formalism catalogue.** The `fep_lean` package exposes {{total_topics}} stable topics through one import namespace. Static metadata, semantic review, Lean bodies, YAML, and the appendix follow an explicit generation graph rather than competing as sources of truth.
- **(C2) A semantic maturity audit.** Each topic records a primary theorem, assumption review, non-vacuity argument, and acceptance probe. The audit distinguishes direct formalization from conditional, structural, and scope-limited proxies; `mathlib_status: real` means a body is intended to compile, not that the motivating scientific claim is complete.
- **(C3) Deeper and compositional formal statements.** The variational and KL rows use Mathlib's native KL definition, identity law, zero characterization, and Markov-kernel chain rule. The manifested foundations now span measure and finite Bayesian inversion, variational duality, controlled and temporal inference, causal interventions, generalized predictive coding, finite path thermodynamics, categorical and optimization geometry, collective inference, concentration, and model evidence in addition to the original finite active-inference kernel. Manifested composition leaves prove **{{formalism.metrics.theorem_witnessed_relations}}** cross-topic witnesses rather than inferring them from shared imports; the graph distinguishes **{{formalism.metrics.formal_relation_witnesses}}** derivations or identifications from **{{formalism.metrics.formal_pairing_witnesses}}** checked pairings, and `composed.lean` is only their import aggregate.
- **(C4) Evidence-separated verification.** Native Lean and full Hermes/OpenGauss evidence have different receipt schemas and claim predicates. Both bind evidence to the current source, while catalogue-only output is ineligible by construction.
- **(C5) Publication contract audits and visualization.** Generated breadth/depth coverage, an offline accessible formalism atlas, declaration/axiom checking, theorem-reference checking, placeholder validation, and source-to-build rendering make drift visible before publication.

The machine-facing evidence for C1--C3 is the generated catalogue and appendix ([@sec:formalisms_and_results]; [@sec:appendix_b_full_topic_lean_catalogue]). The methodological evidence for C4--C5 is described in [@sec:native_lean_4_compilation_and_zero_direct_verification] and [@sec:pipeline_architecture_and_execution_profile]. At this rendered snapshot, native evidence is **`{{verify.evidence_kind}}`** with rate **`{{compile_rate.total}}`**; full-run claim readiness is **`{{full.claim_ready}}`**.

**What this contribution is, and is not.** This is not a proof that the FEP is empirically true or that its many formulations are mutually equivalent. Lean establishes exactly the propositions stated under exactly their hypotheses. The high direct-formalization count reflects disciplined narrowing to exact local contracts, not an end-to-end theorem of self-organization. The contribution is therefore a formal review instrument upstream of empirical and dynamical validation, not a substitute for either.

## Paper Organization {#sec:paper_organization}

The remainder of this paper is organized as follows.

**[@sec:background_and_related_work]** reviews FEP and Active Inference background, the relevant Lean 4 / Mathlib4 capabilities, and adjacent ITP efforts.

**[@sec:methodology_and_system_architecture]** details the Lean 4 / Mathlib4 methodology and pipeline architecture. Six deep-dive subsections ([@sec:lean_4_a_primer_for_active_inference_researchers]–[@sec:pipeline_architecture_and_execution_profile]) cover Lean 4 fundamentals, Mathlib4 coverage, the `sorry` maturity taxonomy, the Hermes AI agent, native `lake env lean` compilation, and the orchestration DAG.

**[@sec:formalisms_and_results]** presents results for the {{total_topics}}-topic catalogue across the {{total_areas}} theoretical areas—FEP foundations, Active Inference, Information Geometry, Bayesian Mechanics, and Thermodynamics—and then isolates the reusable finite kernel in [@sec:finite_active_inference_kernel]. The first {{expansion_first_families}} expansion families of {{expansion_family_size}} topics each are synthesized in [@sec:expanded_formalism_program]; [@sec:formalism_catalogue_155] adds finite-sample risk, finite policy trees, native blanket transfer, exponential-family dual geometry, and exact two-state continuous time. The injected `compile_rate` metrics (from `manuscript_vars.yaml`) are reported alongside Hermes and native verification statistics in [@sec:quantitative_execution_metrics].

**[@sec:discussion]** examines Mathlib4 coverage gaps, the execution-integrity standard, and implications for the FEP debate. **[@sec:conclusion_and_future_work]** concludes with an engineering-outcomes analysis and future directions.

**[@sec:appendix_comprehensive_formalisms_overview]** orients readers to the catalogue, anchors, and injection path. **[@sec:appendix_b_full_topic_lean_catalogue]** is the unified per-topic catalogue: each stable topic juxtaposes the full Lean body with typeset statement signatures and deterministic section/equation anchors for cross-references.

## Notation {#sec:notation}

The following notation is used throughout this paper:

| Symbol | Definition | First use |
|--------|-----------|-----------|
| $\FE[q,p]$ | Variational free energy functional | [@sec:formal_definition_variational_free_energy], [@eq:eq_1] |
| $\EFE(\pi)$ | Expected free energy under policy $\pi$ | [@sec:the_theoretical_landscape], [@eq:eq_4] |
| $\KL[q \| p]$ | Kullback-Leibler divergence from $q$ to $p$ | [@sec:formal_definition_variational_free_energy], [@eq:eq_1] |
| $\Ent[q]$ | Shannon entropy of distribution $q$ | [@sec:the_theoretical_landscape] |
| $\E_q[\cdot]$ | Expectation under distribution $q$ | [@sec:formal_definition_variational_free_energy], [@eq:eq_1] |
| $\Omega, \mathcal{F}, P$ | Sample space, sigma-algebra, and probability measure | [@sec:lean_4_a_primer_for_active_inference_researchers] |
| $q \ll p$ | Absolute continuity ($q$ is abs. continuous w.r.t. $p$) | [@sec:lean_4_a_primer_for_active_inference_researchers] |
| $\frac{dq}{dp}$ | Radon-Nikodym derivative | [@sec:mathlib4_and_measure_theoretic_probability] |
| `sorry` | Lean 4 tactic admitting a goal without proof | [@sec:the_sorry_mechanism_and_formalization_maturity] |
| $\nabla$ | Gradient operator (on statistical manifold or $\R^n$) | [@sec:the_theoretical_landscape] |
| $\Gamma$ | Solenoidal flow operator | [@sec:the_theoretical_landscape] |
| $Q = -Q^\top$ | Skew-symmetric (solenoidal) matrix | [@sec:the_theoretical_landscape], [@eq:eq_25] |
| $F, U, T, S$ | Helmholtz free energy, internal energy, temperature, entropy | [@sec:thermodynamics_results] |
: Notation used throughout the paper, with the section in which each symbol is first used.
