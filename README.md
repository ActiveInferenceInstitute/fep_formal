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

```bash
uv sync --locked --extra dev
uv run fep-lean catalogue
```

`uv run fep-lean catalogue` is explicit offline mode. It creates deterministic
catalogue artifacts and reports zero verified topics. For native Lean
verification (`setup`, `verify`) and the strict full pipeline, follow
[`docs/getting-started.md`](docs/getting-started.md); the complete command list
is under [Quick start](#quick-start) below.

The development workspace pins Lean/Mathlib `v4.35.0`; retained receipts below
keep the versions they actually verified. See [the Lean upgrade procedure](docs/lean4.md#deliberate-toolchain-upgrades).

## Release

The **v1.6.0 release line** (2026-10-07) retains the 168-topic catalogue in
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

`full` execution is strict. It requires the pinned Lean/Lake/Mathlib workspace,
the `gauss` executable, configured Hermes credentials, and writable SQLite
state. Every selected row must compile without `sorry` or Lean warnings, and a
requested review workflow must complete its post-compile review turn.
**Missing capability or incomplete stage → `complete: false`, no report
directory.**

`catalogue` execution is deterministic and offline. It validates the complete
YAML source and writes figures, manuscript variables, the unified appendix, and
a report explicitly marked `catalogue`; it does not count topics as verified.

`verify` execution is Lean-only. It runs the sealed-roster native compile sweep
without Hermes or OpenGauss. Add `--receipt output/native-verification.json
--fail-on-warnings` to persist independently revalidatable native evidence.

`atlas` execution is deterministic and offline. It projects the canonical
coverage join into a standalone SVG and an interactive, keyboard-accessible
HTML graph; `--check` fails on missing or stale bytes. The graph distinguishes
derivational formal edges from checked formal pairings that place two endpoint
laws side by side without asserting implication. Both name qualified Lean
witnesses; conceptual and blocker edges remain visibly non-proof evidence.

`dashboard` execution is also deterministic and offline. It renders static
and interactive numerical witnesses for the expansion families. The
first ten cover Bayesian inversion, variational duality, control, temporal
inference, causal intervention, predictive coding, path thermodynamics,
categorical Fisher geometry, consensus, and finite concentration; the next
five cover Laplace/Brier risk transfer, policy-tree feedback, native blanket
conditional independence, exponential-family duality, and a two-state master
equation. Later witnesses cover standalone EFE and geometric mechanics.
These witnesses expose computational behavior and boundary cases but
never replace native Lean or axiom-audit evidence.

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

```bash
uv sync --locked --extra dev
uv run fep-lean catalogue
uv run fep-lean atlas
uv run fep-lean dashboard
uv run fep-lean setup
uv run fep-lean verify --fail-on-warnings \
  --receipt output/native-verification.json
uv run fep-lean preflight
uv run fep-lean run
```

Use `uv run fep-lean --help` for filters, workflow selection, and the explicit
checkout root. The equivalent maintained scripts are thin command wrappers in
[`scripts/`](scripts/).

The operator command quick reference lives at
[`docs/quickref.md`](docs/quickref.md).

## Source of truth

- [`config/catalogue_metadata.yaml`](config/catalogue_metadata.yaml) maintains
  the stable roster's descriptive and Mathlib metadata.
- [`config/theorem_maturity.yaml`](config/theorem_maturity.yaml) maintains the
  semantic review independently of syntactic compilation maturity.
- [`config/formalism_novelty.yaml`](config/formalism_novelty.yaml) records every
  post-baseline topic's nearest predecessors, invariant, carrier delta, and
  required composition theorem.
- [`config/formalism_relations.yaml`](config/formalism_relations.yaml) maintains
  reviewed formal, conceptual, and blocker relations plus retained open,
  partial, and satisfied capability history. Shared imports never create
  scientific-dependency edges.
- [`src/fep_lean/catalogue/bodies/`](src/fep_lean/catalogue/bodies/) contains
  the family-owned Lean bodies;
  [`registry.py`](src/fep_lean/catalogue/registry.py) validates their canonical
  order and [`latex.py`](src/fep_lean/catalogue/latex.py) derives theorem
  signatures.
- [`config/topics.yaml`](config/topics.yaml) and
  [`src/fep_lean/data/topics.yaml`](src/fep_lean/data/topics.yaml) are generated,
  byte-identical catalogue projections; regenerate them with
  [`scripts/_maint_build_topics_catalogue.py`](scripts/_maint_build_topics_catalogue.py).
- [`lean/FepSketches/fep_all.lean`](lean/FepSketches/fep_all.lean) is the tracked
  aggregate generated by
  [`scripts/_maint_build_fep_all_lean.py`](scripts/_maint_build_fep_all_lean.py).
- [`src/fep_lean/formal/manifest.py`](src/fep_lean/formal/manifest.py) owns the
  formal-resource roster. Canonical cross-topic proofs live in
  [`formal/compositions/`](src/fep_lean/formal/compositions/), while
  [`composed.lean`](src/fep_lean/formal/composed.lean) is the import-only
  aggregate; all tracked Lake projections are generated by
  [`scripts/_maint_build_formal_modules.py`](scripts/_maint_build_formal_modules.py).
- [`docs/formalism-coverage.md`](docs/formalism-coverage.md),
  [`docs/formalism-atlas.svg`](docs/formalism-atlas.svg), and
  [`docs/formalism-atlas.html`](docs/formalism-atlas.html) are generated views
  of the same canonical semantic graph.

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
- [`HANDOFF.md`](HANDOFF.md) gives the next reviewer the operating protocol,
  evidence pointers, and extension backlog.

## Development checks

Contributor setup, check tiers and repository rules are in
[`CONTRIBUTING.md`](CONTRIBUTING.md). The complete required-check list is
maintained once, in the "Required checks" block of
[`AGENTS.md`](AGENTS.md#required-checks); the quick local dev checks are:

```bash
uv run pytest tests/ -q --cov=src --cov-fail-under=89 -m "not serial_lean"
uv run mypy src
uv run ruff check src tests scripts docs
uv run python docs/pin_audit.py --check-latest  # networked: queries upstream for newer pins
```

The reproducible build and publication gates (release-bundle determinism,
browser acceptance capture, receipt validation) are documented in
[`HANDOFF.md`](HANDOFF.md); setup and pipeline gates live in
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
