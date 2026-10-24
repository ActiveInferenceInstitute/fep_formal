<!-- Generated from ../README.md by ../docs/check_links.py; edit the root README.md and regenerate. -->

# FEP_Formal

**Formal methods for the Free Energy Principle and Active Inference.**

[![CI](https://github.com/ActiveInferenceInstitute/fep_formal/actions/workflows/ci.yml/badge.svg)](https://github.com/ActiveInferenceInstitute/fep_formal/actions/workflows/ci.yml)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC_BY_4.0-lightgrey.svg)](../LICENSE)

FEP_Formal is a standalone catalog of 168 Free Energy Principle, Active
Inference, Bayesian Mechanics, Information Geometry, and Thermodynamics topics.
Its reviewed roster spans 22 reviewed families in five
areas. Each topic connects an invariant, explicit assumptions, a canonical Lean
4 theorem body and typeset signatures. The catalog is a versioned research
interface, not an exhaustive census of the FEP literature.

The repository is **FEP_Formal** (`fep_formal` on GitHub). Its Python distribution
and import namespace remain **`fep_lean`**, and its command is **`fep-lean`**.
These names identify different interfaces; commands and imports below use their
actual installed names.

Lean checks exact statements under their stated assumptions. A successful
compile does not establish that a theorem captures an entire scientific
concept or that a model is empirically valid. Semantic review, numerical
witnesses and execution receipts make those boundaries inspectable.

## Explore the project

| Start here | What it provides |
| --- | --- |
| [Documentation index](../docs/README.md) | Guides for researchers, users, contributors and operators |
| [Formalism coverage](../docs/formalism-coverage.md) | Generated topic, declaration, maturity and relationship inventory |
| [Formalism atlas](../docs/formalism-atlas.html) | Offline interactive exploration of the same reviewed graph; download and open the HTML locally |
| [Mathematical methods](../docs/mathematical-methods.md) | Python methods, source-grounded theorem analysis and the positioning explorer |
| [Manuscript sources](../manuscript/README.md) | Authored chapters, generated inputs and reproducible publication workflow |
| [Accepted source checkpoints](../ISA.md#current-assessment) | Exact commits and the evidence supporting their scoped acceptance |
| [Open backlog](../TODO.md) | Linked Issues with dependencies and concrete closure probes |

## First run

Use a source checkout for operator commands. Python 3.14 is the accepted
validator environment; `.python-version` and `pyproject.toml` own the runtime
and dependency policy. The project pins [uv](https://docs.astral.sh/uv/)
`0.13.0`; use that version, including through `uvx uv==0.13.0` when necessary.

```bash
git clone https://github.com/ActiveInferenceInstitute/fep_formal.git
cd fep_formal
uv sync --locked --extra dev
uv run fep-lean catalogue
```

This offline command validates the catalog and creates deterministic figures,
manuscript inputs and a report. It records **zero verified topics** and does
not call Hermes or compile Lean. See [getting started](../docs/getting-started.md)
for expected outputs and the separate native and full-mode prerequisites.

The development workspace pins Lean/Mathlib **v4.35.0**. The
[Lean guide](../docs/lean4.md) explains setup, compilation, diagnostics and deliberate
toolchain upgrades. Retained release and research receipts keep the toolchains
they actually verified.

## Quick start

Choose the interface that matches the work:

- **Explore without a model provider:** begin with the offline catalog above,
  the [atlas](../docs/formalism-atlas.html) and the
  [numerical dashboard guide](../docs/formal-kernel-methods.md).
- **Use the Python API:** start with the [API guide](../docs/api.md). Installed
  wheels support packaged catalog resources and `fep-lean --help`; substantive
  operator commands require the checkout's configuration, Lean workspace and
  manuscript assets.
- **Compile the canonical Lean statements:** follow the native setup and
  `verify` workflow in [getting started](../docs/getting-started.md). A
  publication-grade claim requires its validated, source-bound native receipt.
- **Run configured model-assisted verification:** follow the
  [pipeline guide](../docs/pipeline.md) and [configuration reference](../docs/configuration.md).
  Full mode requires Hermes, OpenGauss, the pinned Lean environment and the
  required credentials. Failed capabilities or topics prevent a successful report.
- **Audit GNN numerical semantics:** follow the
  [source-bound semantic audit guide](../src/fep_lean/bridge/README.md#independent-semantic-audit).
  It checks a retained receipt against independent finite/Gaussian calculations;
  actual execution and native proof require separate evidence.
- **Inspect mathematical methods:** use the [methods guide](../docs/mathematical-methods.md),
  including stable finite expectations, log partitions, exponential tilts and
  Gibbs diagnostics. Numerical agreement is explanatory evidence.

From outside the checkout, place `--project-root /path/to/fep_formal` before the
subcommand. [The command quick reference](../docs/quickref.md) and
`uv run fep-lean --help` describe the available workflows.

## Formal depth

The maintained catalog spans 168 topics. Its reusable formal kernel connects
finite probability, Bayesian inversion, variational free energy,
expected-free-energy decompositions, controlled inference, finite Markov paths,
information geometry and thermodynamic identities. Continuous constructions
include explicit Gaussian, filtering and semigroup interfaces with stated
support, regularity and carrier assumptions. The
[support-aware variational guide](../docs/support-aware-variational-methods.md)
explains the sparse-prior and finite-path extensions.

The generated [coverage report](../docs/formalism-coverage.md) owns current counts
and the exact topic-to-declaration join. The [maturity audit](../docs/theorem-maturity-audit.md)
records direct, conditional and structural scope. In the
[atlas](../docs/formalism-atlas.html), theorem-backed implications and checked
pairings name Lean witnesses; conceptual relationships do not become proofs
through shared imports.

Historical [Horizon 1](../specs/done/horizon-1-finite-synthesis/README.md) and
[Horizon 2](../specs/done/horizon-2-smooth-stochastic/README.md) acceptances retain
their original source epochs and scientific limits. The
[H3 reference study](../specs/h3-reference-study/README.md) has a frozen protocol;
its primary study remains unopened pending its declared package, source and
review gates. Neither hosted CI nor an offline catalog run supplies
production-capture, provider, empirical or scientific acceptance.

## Contract

The [execution contract](../AGENTS.md#execution-contract) owns mode behavior,
capability requirements, failure handling, runtime policy and evidence claims.
The [functional specification](../SPEC.md#public-api) defines public results and
validation behavior. [Pipeline usage](../docs/pipeline.md) gives operator examples.

## Release

The **2.1.0 implementation** coordinates with GNN 5.0.1. It includes seven
bounded composition proofs, updated formal relations, and fail-fast Mathlib
prerequisites. The native supplement remains a separately unactivated proposal. Its
[semantic audit](../src/fep_lean/bridge/README.md#independent-semantic-audit)
compares source-bound finite and passive linear-Gaussian numerical witnesses
through independent reference algorithms. It retains identity, parameter,
quantity, refusal and provenance details. The separate
[finite/scalar algebraic laws](../specs/gnn-semantic-witness-v1/README.md) have
their own compiler controls; neither plane proves universal translation or
authenticates a supplied execution artifact. Current pair/native, manuscript,
hosted, distribution and publication gates must pass before it is
described as an accepted joint release.

The 2.1.0 manuscript has the reserved, unpublished version DOI
`10.5281/zenodo.23607007` under the scholarly concept. Final rendered bytes and
publication acceptance remain pending; the published 1.6.0 manuscript retains
its own DOI and files.

The published [v1.6.0 release](https://github.com/ActiveInferenceInstitute/fep_formal/releases/tag/v1.6.0)
contains mathematical methods and the manuscript's
[Supplement A](../manuscript/08b_mathematical_positioning_supplement.md). Its
recorded Lean/Mathlib pair is `v4.34.1`; its evidence describes that immutable
release. The v4.35.0 migration and subsequent source improvements are recorded in the dated 2.0.0 preparation section of
[CHANGELOG.md](../CHANGELOG.md); the [accepted checkpoint](../ISA.md#current-assessment)
and [active campaign](../specs/comprehensive-next-steps/README.md) distinguish
accepted scopes, proposals and remaining gates.

[The release procedure](../docs/release.md) owns version/date consistency,
exact-commit CI, bundle validation and publication. Manuscript and software
archives have distinct DOI histories:

- [Scholarly concept DOI](https://doi.org/10.5281/zenodo.19699233)
- [Software concept DOI](https://doi.org/10.5281/zenodo.23196891)

## Source of truth

The [owner and projection map](../AGENTS.md#source-of-truth) identifies where to
edit and which generator to use. Generated YAML, Lean aggregates, coverage,
visualizations and manuscript inputs are projections of those owners. Their
rendered bytes are not alternative authoring surfaces.

## Review contracts

- [AGENTS.md](../AGENTS.md) defines the repository contract and links directory-specific instructions.
- [ISA.md](../ISA.md) defines ideal-state criteria, anti-criteria and accepted evidence.
- [TODO.md](../TODO.md) is the open-only Issue backlog.
- [The active campaign](../specs/comprehensive-next-steps/README.md) owns the current dependency graph and pickup point.
- [HANDOFF.md](../HANDOFF.md) and closed specs retain dated observations; they do not override current owner contracts.
- [The GNN bridge design](../docs/design/gnn-bridge/README.md) distinguishes source custody, formal statements and actual renderer execution.

## Development checks

[CONTRIBUTING.md](../CONTRIBUTING.md) explains setup, check tiers and review
conventions. The complete required-check list is maintained once in
[AGENTS.md](../AGENTS.md#required-checks).

The [publication capture runbook](../docs/development.md#bounded-publication-capture)
and [local render runbook](../scripts/README.md#local-render-runbook) own their
prerequisites and acceptance boundaries. The
[documentation maintenance contract](../AGENTS.md#maintaining-documentation)
explains the canonical README and its generated GitHub presentation.

## Layout

Authoring lives in [config](../config/README.md), the
[Python package](../src/fep_lean/README.md), and the
[manuscript](../manuscript/README.md). The [Lean workspace](../lean/README.md)
compiles the projected formal sources. [Scripts](../scripts/README.md) provide
bounded entry points, [tests](../tests/README.md) enforce contracts, and
[specs](../specs/README.md) retain implementation plans and source-bound evidence.

## Notation

Topic-prefixed Lean identifiers such as `fepNNN_*` must be read with their
reviewed invariant and assumptions in `config/theorem_maturity.yaml`. The
manuscript appendix projects exact theorem signatures; prose notation does not
replace the Lean API.

## License and citation

FEP_Formal is maintained by the Active Inference Institute and distributed
under [CC BY 4.0](../LICENSE). Use [CITATION.cff](../CITATION.cff) for the software and
preferred scholarly citation, and cite the exact release or source revision
used in a reproducible result.
