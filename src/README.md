# FEP_Formal Python source

This directory contains the installable `fep_formal` package. The project is
FEP_Formal; Python imports remain `fep_formal.*` and the console remains
`fep-formal`. Public export definitions live in each package's `__init__.py`,
with selected high-level operations exposed lazily by the package root.

## Package navigation

| Package | Responsibility |
| --- | --- |
| [catalogue](fep_formal/catalogue/) | Maintained metadata, canonical family bodies, semantic review and deterministic catalogue projections. |
| [methods](fep_formal/methods/) | Portable mathematical queries, source-text analysis, numerical boundary diagnostics and offline visual projections. |
| [formal](fep_formal/formal/) | Canonical Lean foundations, composition leaves and the explicit resource manifest. |
| [data](fep_formal/data/) | Generated catalogue and methods inputs installed with the wheel. |
| [verification](fep_formal/verification/) | Environment probes, native Lean compilation, declaration/axiom audits and scoped receipt validation. |
| [llm](fep_formal/llm/) | Explicit Hermes configuration and bounded provider requests. |
| [gauss](fep_formal/gauss/) | SQLite session storage and strict per-topic orchestration. |
| [output](fep_formal/output/) | Evidence receipts, reports, figures, manuscript rendering and release bundles. |
| [pipeline](fep_formal/pipeline/) | Offline catalogue and credentialed full-mode orchestration. |
| [bridge](fep_formal/bridge/) | Explicit GNN source custody, interchange and numerical comparison. |
| [custody](fep_formal/custody/) | Evidence census, strict gates, staged refresh and committed-candidate resume. |
| [prove2me](fep_formal/prove2me/) | Separately authorized remote formalization queries and submissions. |

## Execution and evidence

The [root execution contract](../AGENTS.md#execution-contract) defines the CLI
modes. Catalogue mode generates offline artifacts with no verified-topic claim;
native verification compiles identified Lean sources; full mode additionally
requires provider, persistence and workflow completion. Numerical comparisons,
source-text analysis and visualizations keep their own explanatory boundaries.

`gauss/client.py` owns SQLite state. Provider clients do not compile Lean or
write sessions, and verification does not acquire dependencies during ordinary
validation. Explicit setup owns dependency acquisition. The package contracts
explain these seams and the ownership of generated outputs.

## Imports and installed use

Use a narrow public import:

```python
from fep_formal.catalogue import FEPTopicCatalogue

catalogue = FEPTopicCatalogue.default()
```

The wheel installs the Python namespace, generated catalogue/methods data and
formal Lean resources. Portable catalogue and methods APIs use those resources
without a checkout. Operator workflows also need checkout-owned configuration,
Lean and manuscript assets; the CLI validates those markers and accepts an
explicit `--project-root` or `FEP_FORMAL_PROJECT_ROOT` where applicable.

The [package guide](fep_formal/README.md) explains the interpreter and installed
resource boundaries. The [source contract](AGENTS.md) and
[root check inventory](../AGENTS.md#required-checks) govern changes; the
[pipeline guide](fep_formal/pipeline/README.md) explains its recorded stages.
