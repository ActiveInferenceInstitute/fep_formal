# fep_lean

`fep_lean` is a standalone catalogue of 168 Free Energy Principle, Active
Inference, Bayesian Mechanics, Information Geometry, and Thermodynamics topics.
Each row contains a reviewed invariant, explicit assumptions, a Lean 4 theorem
body, and typeset signatures. The pinned Lean workspace is the compilation
authority; the semantic review separately records how far each theorem reaches
toward its topic label. The schema-2 roster spans 22 reviewed families in five
areas and is a versioned interface, not an exhaustive census of the FEP
literature. The families include five second-expansion families for
finite-sample risk, closed-loop policy trees, native blanket transfer, finite
exponential-family dual geometry, and exact two-state continuous time, plus
standalone EFE and geometric-mechanics families.

## First run

Python 3.14 is the only accepted validator environment (see `.python-version`);
[uv](https://docs.astral.sh/uv/) provisions it.
Project metadata and CI pin uv `0.13.0`; `uvx uv==0.13.0` can run the commands
below when the host's uv binary differs.

```bash
uv sync --locked --extra dev
uv run fep-lean catalogue
```

`uv run fep-lean catalogue` is explicit offline mode. It creates deterministic
catalogue artifacts and reports zero verified topics. For native Lean
verification (`setup`, `verify`) and the strict full pipeline, follow
[`docs/getting-started.md`](docs/getting-started.md) and the
[execution contract](AGENTS.md#execution-contract).

The development workspace pins Lean/Mathlib `v4.35.0`; retained receipts below
keep the versions they actually verified. See [the Lean upgrade procedure](docs/lean4.md#deliberate-toolchain-upgrades).

The [support-aware variational extension](docs/support-aware-variational-methods.md)
adds sparse-prior Gibbs optimization with explicit precision signs, actual
Markov-path marginal reductions and reversible endpoint KL-drop identities.
Four reusable [numerical methods](docs/mathematical-methods.md#reusable-finite-variational-methods)
expose stable expectations, log partitions, exponential tilts and diagnostic
gaps through Python and `fep-lean methods gibbs`.

## Release

The published **[v1.6.0 release](https://github.com/ActiveInferenceInstitute/fep_formal/releases/tag/v1.6.0)**
(release date 2026-10-07) retains the 168-topic catalogue in
22 families on the `v4.34.1` Lean/Mathlib pair and extends its mathematical methods and
manuscript. The previous published release is
[`v1.5.0`](https://github.com/ActiveInferenceInstitute/fep_formal/releases/tag/v1.5.0)
(2026-10-06). It superseded the
[`v1.3.0` tag](https://github.com/ActiveInferenceInstitute/fep_formal/tree/v1.3.0)
(159 topics); the untagged `1.4.0` candidate shipped within 1.5.0.
Releases follow the short [release procedure](docs/release.md): one version
and date everywhere, a dated changelog section and a green hosted CI run on
the exact `main` commit, checked by `docs/release_check.py`.
The package and manuscript metadata identify **1.6.0**, with portable
mathematical methods, source-grounded Lean statement analysis, shared FEP/OpenAI
feature coordinates, an offline explorer, publication panels and an extended
[Supplement A](manuscript/08b_mathematical_positioning_supplement.md).
[The integration guide](docs/mathematical-methods.md) records the interfaces and
mathematical transfer rules. Publication is bound to the release gate on the final integrated commit.

The Lean/Mathlib 4.35 migration and support-aware variational extension are
subsequent source changes, recorded under Unreleased. The
[accepted source checkpoint](ISA.md#current-assessment) binds their hosted
evidence to its exact commit. The [active next-step campaign](specs/comprehensive-next-steps/README.md)
owns subsequent implementation; the published tag retains its original bytes.

The evolving manuscript is identified by the
[scholarly concept DOI](https://doi.org/10.5281/zenodo.19699233). GitHub releases
are archived separately under the
[software concept DOI](https://doi.org/10.5281/zenodo.23196891); each history
has its own immutable version DOIs. See the [release procedure](docs/release.md)
for publication and file verification.
A release changes no evidence boundary below: unrun research lanes (the H3
study, full publication capture, installed-wheel matrix, provider runs) stay
described as unrun.

The [upcoming improvement scopes](docs/design/fep-research-program/next-improvements.md)
define minor, medium and major work for the core package and formalizations,
with named owners, dependencies, acceptance probes and failure boundaries.
The open-only [backlog](TODO.md) owns open research and evidence work.

The [mathematical positioning supplement](manuscript/08b_mathematical_positioning_supplement.md)
locates the formal methods within probability, topology, information geometry,
statistics, and control. The accompanying
[modular analysis slice](specs/openai-math-methods/README.md) joins canonical
contracts with authored family context and reviews the pinned `openai/math`
research corpus without adding a runtime dependency.

## Contract

The [execution contract](AGENTS.md#execution-contract) owns mode behavior,
capability requirements, failure handling, runtime policy, and evidence claims.
The [functional specification](SPEC.md#public-api) defines public result fields
and validation behavior; [pipeline usage](docs/pipeline.md) explains workflows.

## Formal depth

The live formalism is organized into theorem-connected strands rather than a
headline theorem count: normalized finite probability and information
algebras, including support-free separation for the explicitly totalized finite
KL; posterior-form variational free energy and a uniquely attained evidence
lower bound; both expected-free-energy decompositions; a transition-consistent
infer--select--act joint and prior-sensitive Boolean policy witness;
stage-dependent cumulative finite-horizon EFE; finite Bayesian inversion,
variational duality, controlled and temporal inference, causal interventions,
and generalized predictive coding; path-space fluctuation identities and
reversible KL dissipation; categorical Fisher geometry, Cramér--Rao,
natural-gradient, mirror-descent, and replicator laws; collective inference;
finite concentration and model-evidence results; finite Laplace/Brier risk
transfer; observation-contingent policy-tree recursion and dominance; native
`CondIndepFun` blanket transfer; scalar exponential-family KL/Bregman duality;
and an exact two-state continuous-time semigroup, master equation, detailed
balance, relaxation, and Lyapunov law. The generated
[coverage report](docs/formalism-coverage.md) owns all current counts, and the
[atlas](docs/formalism-atlas.html) shows exactly which relations have Lean
witnesses. The semantic firewall requires every non-formalized row to expose
an explicit scope or assumption boundary. The reusable kernel is an explicit
manifest of foundations and leaf composition modules; `composed.lean` is only
their import aggregate. The maturity audit, rather than compilation alone,
records which rows are direct formalizations and which remain conditional or
structural proxies.

**Current evidence boundary.** The maintained catalogue spans 168 topics.
H1.0--H1.8 have exited through their accepted gates, with optional H1.5
accepted separately; the archived
[Horizon 1 record](specs/done/horizon-1-finite-synthesis/README.md) owns the
detailed evidence. Its terminal theorem is one finite, synthetic, one-step
posterior--decision--action certificate on a shared 16-state Boolean carrier.
The learned posterior, emitted action, sampled kernel, genuine sensory--active
blanket factorization, and strict real/native KL decrease remain connected on
that same carrier and kernel. The record also preserves the first H1.8
carrier-merge no-go. It does not establish transition-aware planning,
EFE-optimal control, physical or causal adequacy, empirical validation, or a
universal FEP claim.

The archived [Horizon 2 spec](specs/done/horizon-2-smooth-stochastic/README.md) has
accepted H2.0--H2.3b, H2.4a/b, H2.5a/b/c/d, H2.5b-R0, H2.5d-R0,
H2.6a/b/c, and H2.6a-R0. The current smooth surface includes fixed-variance scalar Gaussian
KL/information geometry, local coordinate duality, a same-joint native
posterior martingale with its limiting-observation conditional-expectation
endpoint, selected-model identification, joint-law and fixed-truth posterior
consistency, weak convergence to the sampled-parameter Dirac law,
bounded-continuous transfer, bounded zero-one risk convergence, native
kernel/action semigroups, exact scalar and finite-axis linear-Gaussian
transition families, the exact four-axis symmetric-precision specialization,
an evidence-a.e. native Gaussian filter with chronological finite recursion,
one-step transition-consuming quadratic decision risk, and monotone finite-grid
path laws with explicit support and log-ratio boundaries. The accepted R0
repairs preserve the historical H2.0 no-go rows while their maintained owners
derive the replacement mathematics. H2.5d-R0 reconstructs the centered Fin4
stationary joint. Maintained H2.5d extends that native conditional product to
every stationary center, proves blanket-a.e. pair and scalar conditional laws
plus endpoint `CondIndepFun`, and derives a fixed bivariate precision
perturbation with actual covariance `-1 / 15` and native non-independence.
H2.7-R0 has accepted the continuous density-relative exact-posterior VFE and
derived local natural-gradient seam. The [H2.7 terminal record](specs/done/horizon-2-smooth-stochastic/readiness/terminal-acceptance.json)
validates the mandatory cases, enabled Fin4 supplement, source hashes,
independent diagnostics, and source-bound reviews. Fresh H2 custody and
continuous H3.G0 acceptance preceded the immutable
[H3.0 protocol freeze](specs/h3-reference-study/freeze.json). The selected
[reference study](specs/h3-reference-study/README.md) now has compiled native
model and cross-domain proofs, a retained native export and three independent
proof-role reviews. Package repairs require a fresh final-source export and
review before opening the frozen synthetic seeds. Final claim review and
bundle reproduction remain open; empirical execution is governed no-go without
a licensed named dataset.

The published output/configuration checkpoint at `c99e933` has a successful
[exact-SHA hosted run](https://github.com/ActiveInferenceInstitute/fep_formal/actions/runs/37334643019):
all 15 distribution cells and Python, Lean and render jobs passed. Nonserial
Python passed 2,404 tests with 15 skips and 91.31% coverage on Linux CPython
3.14.8. Local validation uses CPython 3.14.4. Later owner changes require fresh
source-bound acceptance; the [remaining acceptance](specs/comprehensive-science-improvement/NEXT.md)
owns the current sequence.

The expanded local catalogue-native checkpoint and
[Q7 capture](specs/comprehensive-science-improvement/evidence/public-q7-final-source-20261002-r1/summary.json)
retain their respective recorded source epochs. The 2026-10-02 Q7 capture
passed all 12
stages, four closing checks, five-runtime scaffold parity and 124 pure controls
without skips. Its native receipt proves the exact static coefficient
statements and leaves runner execution unverified. The separately reviewed
[2026-10-05 Q7 source-pair observation](specs/comprehensive-science-improvement/evidence/public-q7-current-source-20261005-r1/summary.json)
records a complete 2026-10-05 capture with all twelve stages and four closing
checks. Its native receipt binds the recorded 291-input roster at that source
epoch and leaves runner execution unverified. The public observation is not
itself a native receipt or verification of the current checkout. Later
source-owner changes require fresh source-pair acceptance. Earlier incomplete
captures promote no prefix or native output. Historical Q5/Q6/Q7 and provider
reports remain evidence for their own checked sources. Ignored provider reports
are not shipped in a release. Active GNN work remains preserved.

The H3 primary remains unopened pending current package and source-bound
proof/export review. Frozen execution and replay, claim review and clean study
reproduction are subsequent obligations. The scientific protocol, seeds,
counts and licensed-data no-go remain unchanged.

## Quick start

Run operator commands from a source checkout. Installed wheels support the
packaged `FEPTopicCatalogue.default()` API and `fep-lean --help`; substantive
commands deliberately require the checkout-owned configuration, Lean
workspace, and manuscript assets. From another directory, pass
`--project-root /path/to/fep_lean` before the subcommand.

Use `uv run fep-lean --help` for filters, workflow selection, and the explicit
checkout root. The equivalent maintained scripts are thin command wrappers in
[`scripts/`](scripts/).

Start with the offline example under [First run](#first-run), then use
[getting started](docs/getting-started.md) and the
[operator command quick reference](docs/quickref.md) for the intended workflow.

## Source of truth

The maintained [owner and projection map](AGENTS.md#source-of-truth) identifies
where to edit and which generator to use. Browse the generated
[coverage report](docs/formalism-coverage.md) and
[formalism atlas](docs/formalism-atlas.html) for the current graph.

## Review contracts

- [`ISA.md`](ISA.md) defines the ideal state, anti-criteria, and evidence gates.
- [`TODO.md`](TODO.md) is the canonical open-only backlog with behavior-based
  acceptance probes.
- [`CHANGELOG.md`](CHANGELOG.md) records release changes and their evidence
  boundary.
- [`manuscript/04i_formalism_catalogue_155.md`](manuscript/04i_formalism_catalogue_155.md)
  states the five second-expansion families (`fep-121` to `fep-155`), theorem
  assumptions, non-vacuity witnesses,
  and evidence boundaries in one authored chapter.
- [`HANDOFF.md`](HANDOFF.md) retains dated evidence and review observations;
  the [next-step campaign](specs/comprehensive-next-steps/README.md) owns the
  active implementation graph and pickup point.

## Development checks

Contributor setup, check tiers and repository rules are in
[`CONTRIBUTING.md`](CONTRIBUTING.md). The complete required-check list is
maintained once, in the "Required checks" block of
[`AGENTS.md`](AGENTS.md#required-checks).

The reproducible build and publication gates (release-bundle determinism,
browser acceptance capture, receipt validation) are maintained in the
[bounded publication capture runbook](docs/development.md#bounded-publication-capture);
the [local render runbook](scripts/README.md#local-render-runbook) owns render
preparation and stale-receipt diagnosis. Setup and pipeline usage live in
[`docs/getting-started.md`](docs/getting-started.md) and
[`docs/pipeline.md`](docs/pipeline.md).

## Layout

| Path | Purpose |
| --- | --- |
| `src/fep_lean/catalogue` | typed semantic model, family-owned canonical bodies, generation, and coverage projections |
| `src/fep_lean/formal` | packaged foundations, leaf compositions, import aggregate, and workspace projection |
| `src/fep_lean/verification` | read-only capability checks, Lean compiler bridge, declaration/axiom audit, and GNN artifact-proof extraction and manifest verification |
| `src/fep_lean/llm` | configured Hermes HTTP client |
| `src/fep_lean/gauss` | SQLite sessions and per-topic orchestration |
| `src/fep_lean/output` | evidence receipts, fail-closed rendering, figures, reports, the offline formalism atlas, and the typed numerical dashboard |
| `src/fep_lean/pipeline` | strict `full` and explicit offline `catalogue` modes |
| `lean` | pinned Lake workspace and tracked aggregate |
| `manuscript` | source chapters and generated publication inputs |

## Notation

Lean identifiers are deliberately topic-prefixed (`fepNNN_*`) and should be
read together with the corresponding invariant and `assumption_review` in
`config/theorem_maturity.yaml`. The generated appendix renders exact theorem
signatures; prose notation is never an alternative source for the Lean API.
