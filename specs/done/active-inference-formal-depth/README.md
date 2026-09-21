# Active Inference formal depth

Status: closed in the shared working tree; uncommitted and unpublished
Closed: 2026-08-20

## Purpose

This feature gives the stable fifty-topic catalogue a reusable, proof-bearing
finite kernel for Free Energy Principle and Active Inference research. Its
purpose is not to turn a compiling sketch into a universal physical theorem.
It makes a smaller claim more rigorously: normalized finite probability,
information, inference, action, blanket, information-geometry, and asymptotic
objects can inhabit one typed program whose assumptions, composition seams,
compiler evidence, and visualization are independently inspectable.

The same separation governs the execution plane. Canonical Lean, native topic
compilation, declaration-and-axiom auditing, provider-backed workflow execution,
and human-readable publication artifacts answer different questions. A green
result in one plane never promotes another.

## Why this shape

- **Depth stays below stable scholarly anchors.** The `fep-001` through
  `fep-050` roster remains fixed. Six topic-independent foundation modules and
  one composition module provide reusable depth without inflating the number
  of catalogue claims.
- **One finite carrier prevents semantic drift.** `FEP.FiniteLaw` and
  `FEP.FiniteKernel` own finite normalization, products, marginals,
  pushforwards, and composition. Entropy, KL, mutual information, generative
  models, blankets, and score geometry reuse those objects instead of growing
  incompatible local probability vectors.
- **Totalization is explicit.** The real-valued finite KL and cross-entropy
  definitions are useful algebraic objects, but at zero reference mass they
  are not the usual extended-real divergences. Separation is support-free;
  logarithmic identities that divide by reference mass retain visible support
  assumptions.
- **Selection and action form one normalized joint.** Policy prior, expected free
  energy, policy selection, emitted action, and action-indexed transition share
  one model and interface. Posterior-state inference and variational free energy
  reuse that generative model but are proved as adjacent contracts; they are not
  represented as feedback inputs to the infer-select-act-transition joint.
- **Blanket claims stop at the proved conditioning boundary.** The dynamics
  theorem identifies every fixed transition row with a static factorization and
  proves conditional internal-external factorization at positive blanket mass.
  Mixtures over current states and a general measurable-space transfer require
  additional hypotheses and are not inferred.
- **Geometry starts from a Gram construction.** Symmetry and positive
  semidefiniteness follow without regularity folklore. Positive definiteness
  requires full support and score identifiability; natural-gradient construction
  and uniqueness require an explicit inverse. Concrete Bernoulli and
  duplicated-score models demonstrate both the nondegenerate and rank-deficient
  cases.
- **Asymptotics stay in a foundation layer.** Finite-observable strong laws
  expose integrability, pairwise independence, and identical-distribution
  assumptions; the expected observable is their convergence target. The
  topic-specific Laplace-smoothing result lives in composition, so the
  foundation never imports catalogue namespaces.
- **Provider output cannot rewrite proof content.** The current canonical
  corpus is already `sorry`-free. Hermes may add explanation or formatting, but
  the non-comment Lean token stream must remain identical to canonical source.
  This conservative firewall is stronger and easier to audit than a partial
  source parser that could miss a weakened theorem or injected axiom.
- **Evidence is recomputed, not trusted.** Claim readiness derives from exact
  catalogue membership, an explicit owner manifest, source/config/toolchain
  digests, actual Lean and Mathlib identities, exact preflight stages, semantic
  source parity, compiler results, and complete artifact reconciliation. A
  producer-owned boolean is never sufficient.

## Mathematical invariants and boundaries

1. Foundation modules import Mathlib and earlier foundation modules only.
   `FepSketches.composed` alone owns bridges to topic declarations.
2. Every `FiniteLaw` and `FiniteKernel` is pointwise nonnegative and normalized;
   constructors and composition preserve those laws.
3. `FEP.FiniteInformation.finiteKL_eq_zero_iff` separates normalized finite
   laws without a full-support premise. Support remains necessary only where a
   theorem invokes a logarithmic ratio or identifies the totalized real
   expression with a standard extended divergence.
4. `FEP.ActiveInference.FullSupport` licenses logarithmic EFE decomposition and
   policy selection by excluding zero preference mass. The standalone
   `pragmaticCost` remains a totalized real function. Sensitivity to policy-prior
   changes is established by the exact symmetric Boolean witness, not asserted
   for every model.
5. Real expected free energy and the catalogue's truncated `ENNReal`
   convention are connected only through the explicit `ENNReal.ofReal` bridge;
   they are not definitionally identified.
6. `FEP.MarkovBlanket.transition_eq_staticJoint_nextStaticModel` is a row-wise
   result. It does not assert preservation of blanket factorization after
   mixing transition rows under an arbitrary prior.
7. Fisher positive definiteness is conditional on full support and score
   identifiability. `duplicatedScore_fisherMetric_eq_zero` exhibits a nonzero
   null direction, so positive semidefiniteness cannot be misread as
   unconditional invertibility.
8. The statistical results are almost-sure asymptotic theorems under their
   stated hypotheses. They are not finite-sample concentration, estimator-risk,
   marginal-likelihood optimality, or universal Bayesian-consistency results.
9. None of the finite models establishes that every persistent physical system
   performs Bayesian inference or possesses a Markov blanket.

## Evidence and publication invariants

1. `src/fep_lean/catalogue/sketches.py`, the formal resources, maintained YAML,
   and the explicit source-owner roster are authoritative. Workspace Lean,
   packaged YAML, coverage, atlas, dashboard, and manuscript files are checked
   projections.
2. Native verification, declaration/axiom audit, and full provider execution
   retain different schemas and readiness predicates. Each validator binds to
   the live complete owner tree and fails closed on stale or incomplete roots.
3. Formal audit accepts only the versioned trusted axiom set `propext`,
   `Classical.choice`, and `Quot.sound`; `sorryAx` and every unlisted axiom are
   rejected.
4. Full-report validation reconstructs catalogue rows, semantic contracts,
   preflight capabilities and stages, statistics, Markdown projections, and
   artifact hashes. Unknown topics, missing topic reports, weakened Lean,
   contradictory status fields, or recomputed attacker hashes remain invalid.
5. Manuscript rendering validates every placeholder and referenced asset before
   replacing the destination tree. Removed chapters/assets are pruned and an
   invalid source set leaves no partial publication.
6. A closure-time live-shaped-key scan found no provider credential in source,
   reports, screenshots, generated artifacts, or retained Gauss state; tests
   contain only explicit fake credential placeholders. The exact scan scope and
   its lack of a retained raw log are recorded in
   `acceptance-evidence.json`.

## Code and test pointers

- Finite probability and information:
  `src/fep_lean/formal/finite_probability.lean`,
  `src/fep_lean/formal/finite_information.lean`, and
  `tests/test_formal_foundations.py`.
- Shared generative model and exact examples:
  `src/fep_lean/formal/active_inference.lean`, especially
  `GenerativeModel`, `ActionInterface`,
  `inferSelectActActionMarginal_eq_actionLaw`, and the exact two-state policy
  witness; pinned by `tests/test_formal_foundations.py`. The policy witness does
  not instantiate `ActionInterface`; those are separate non-vacuity surfaces.
- Blanket factorization and dynamics:
  `src/fep_lean/formal/markov_blanket.lean`, especially
  `nextStaticModel`, `transition_eq_staticJoint_nextStaticModel`, and
  `transition_row_conditional_factorization`.
- Fisher geometry and concrete boundary witnesses:
  `src/fep_lean/formal/information_geometry.lean`, especially
  `naturalGradient_metric_duality`, `bernoulli_naturalGradient_eq`, and
  `duplicatedScore_fisherMetric_eq_zero`.
- Strong-law foundation and topic bridge:
  `src/fep_lean/formal/statistical_convergence.lean` and
  `FEPComposed.fep036_smoothedRate_strongLaw` in
  `src/fep_lean/formal/composed.lean`.
- Semantic graph and generated views:
  `fep_lean.catalogue.relations`, `fep_lean.catalogue.coverage`,
  `fep_lean.output.formalism_atlas`,
  `fep_lean.output.formal_kernel_dashboard`,
  `tests/test_formalism_relations.py`, `tests/test_formalism_coverage.py`,
  `tests/test_formalism_atlas.py`, and
  `tests/test_formal_kernel_dashboard.py`.
- Evidence and semantic firewall:
  `fep_lean.llm.hermes.lean_semantic_contract`,
  `fep_lean.output.provenance`, `fep_lean.output.evidence`,
  `fep_lean.output.reporter`, `fep_lean.verification.formalism_audit`,
  `tests/test_native_evidence.py`, `tests/test_reporter.py`, and
  `tests/test_formalism_audit.py`.
- Publication contract: `fep_lean.output.rendering`,
  `scripts/render_manuscript.py`, `tests/test_manuscript_rendering.py`, and
  `docs/formal-kernel-methods.md`.

## Rejected paths and consequential boundaries

- Support-gating finite-KL separation is rejected by the theorem's actual
  support-free signature and its disjoint-point-mass boundary witnesses.
  Support-sensitive logarithmic chain laws retain their explicit assumptions.
- A policy-to-action pushforward detached from transition is not an adequate
  action contract. `ActionInterface` and
  `inferSelectActActionMarginal_eq_actionLaw` connect the normalized selection
  joint to the advertised action law and one-step action-indexed transition.
- Blanket factorization after mixing arbitrary transition rows is outside the
  result. The module exposes a static model for each fixed row and explicitly
  documents that mixtures require additional hypotheses.
- No native measurable-space `CondIndepFun` bridge supports the blanket
  capability. The retained capability therefore says finite pointwise
  conditional factorization rather than borrowing an unrelated theorem.
- Topic imports are rejected from foundation modules. The generic strong law
  stays in `statistical_convergence.lean`; only
  `FEPComposed.fep036_smoothedRate_strongLaw` imports the topic-specific
  smoothing theorem, and the foundation-import test pins that boundary.
- General smooth statistical manifolds, exponential-family Hessian identities,
  and a continuous-time Markov example are outside the reviewed surface.
  Concrete full-rank and rank-deficient score families supply the required
  non-vacuity and limitation evidence.
- Name-level provider preservation is insufficient. Regression tests exhibit a
  same-name theorem weakened to `True` and an indented custom-axiom injection;
  exact non-comment token parity rejects both in the proof-complete corpus.
- Dynamic source globs cannot define completeness because deletion changes the
  discovered set. The versioned explicit owner roster defines completeness,
  while globs only detect unmanifested additions; deletion adversaries pin both
  native and full-report boundaries.
- The static atlas is intentionally a self-contained area matrix with the full
  relation inventory, not the detailed ninety-node HTML graph compressed onto
  one manuscript sheet. The interactive projection retains the graph, filters,
  inspector, and accessible tables. The decision trail and reviewed captures
  are recorded in [visual-review.md](visual-review.md).
- Dashboard numerical series come from one immutable model shared by SVG and
  HTML. Blanket topology and scientific labels remain renderer-owned literals
  with static regression assertions; a closure-time Chrome probe, rather than
  those string tests, activated the visible navigation controls.

## Visual provenance

No external artwork or screenshot was used as a style target. The visual
standard was internal and evidence-led: self-contained scientific notation,
complete relation accounting, color-independent line semantics, readable
static manuscript output, accessible data tables, and navigable offline HTML.

- [Atlas static acceptance capture](assets/atlas-static-1900.png) records the
  final standalone relation matrix and complete evidence inventory.
- [Atlas interactive acceptance capture](assets/atlas-interactive-1900.png)
  records the detailed ninety-node research map and its primary inspector.
- [Dashboard static acceptance capture](assets/dashboard-static-1800.png)
  records the five-panel finite-kernel narrative used in the manuscript.
- [Dashboard desktop acceptance capture](assets/dashboard-interactive-1920.png)
  and [mobile acceptance capture](assets/dashboard-mobile-390.png) record the
  responsive layout and visible navigation controls.

All five captures came from local Chrome renders of the generated SVG/HTML.
The independent verdicts, interaction boundary, and capture hashes are retained
in [visual-review.md](visual-review.md). The reproducible publication outputs are
`docs/formalism-atlas.svg`, `docs/formalism-atlas.html`,
`docs/formal-kernel-dashboard.svg`, and
`docs/formal-kernel-dashboard.html`; these captures preserve the visual bar
against which those outputs were closed.

## Acceptance record

The local working-tree source-bound evidence consists of:

- `output/native-verification.json`: exact fifty-topic native compilation,
  zero warnings, zero `sorry`, actual Lean 4.29.0, and the resolved pinned
  Mathlib revision;
- `output/formalism-audit.json`: the complete 262-declaration closure, 243
  evidence declarations, one parsed axiom result per declaration, and only the
  trusted axiom set;
- a historical full run, `run_20260820_183143_709998` (the gitignored
  `output/reports/` directory no longer exists; only its digest-only identity —
  summary, run-manifest, and verification-manifest SHA-256 digests in
  [acceptance-evidence.json](acceptance-evidence.json) — records it):
  independently validated full execution for all fifty topics, fifty Hermes
  successes, fifty preserved semantic contracts, fifty direct refined-source
  compilations, and 56 reconciled artifacts; and
- warning-free `lake build FepSketches` at 8,257 jobs, current deterministic
  projections, package-wheel isolation tests, documentation audits, and the
  repository's Python quality gates.

The raw receipts live under the gitignored `output/` tree and therefore do not
survive a normal clone. [acceptance-evidence.json](acceptance-evidence.json)
retains their schema versions, source/config/toolchain identities, SHA-256
digests, independently derived validation outcomes, and the final Python/Lake
gate results. It is a closure snapshot, not a substitute for rerunning the
validators against the raw receipts and live owner tree. The Lake result has no
retained raw log; the snapshot records the observed command, exit code, and job
count without calling it a compiler receipt.

The provider run records workflow execution, not new mathematical authority.
Canonical Lean and its native compiler/audit receipts remain the proof plane.
