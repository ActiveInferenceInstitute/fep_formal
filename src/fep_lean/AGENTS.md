# `fep_lean` package contract

This directory is the sole import root installed by the distribution. Internal
imports must use `fep_lean.*`; do not recreate the removed collision-prone
top-level packages (`catalogue`, `pipeline`, `output`, `verification`, `gauss`,
or `llm`). FEP_Formal is the project name; `fep_lean`, `fep-lean` and
`FepSketches` retain their existing import, CLI and Lean-library identities.

## Boundaries

- `catalogue` owns typed metadata/semantic validation, the family-body registry,
  theorem-signature projection, and deterministic catalogue projections.
- `formal` owns the explicit foundation/composition manifest, canonical Lean
  resources, and exact workspace projection; its `composed.lean` resource is an
  import-only aggregate.
- `methods` owns portable source-text queries, numerical diagnostics and their
  offline projections; it does not compile the declarations it describes.
- `data` holds generated installable inputs with their own canonical owners.
- `verification` owns read-only environment checks and native Lean execution.
- `llm` owns Hermes/provider interaction; `gauss` owns SQLite sessions and
  per-topic orchestration.
- `pipeline` composes those layers. Catalogue mode must remain offline; full
  mode must fail closed when a required capability is unavailable.
- `output` owns receipts, reports, figures, variables, and source-preserving
  rendering. Catalogue, native, and full-run evidence must remain distinct.
- `bridge` owns explicit source custody and interchange with a named GNN
  checkout; numerical agreement does not establish current execution.
- `custody` owns read-only census/gating and explicit staged refresh. Rebinding
  a dependency does not create a new recorded observation.
- `prove2me` is an explicit remote-client surface, separate from the pipeline;
  local compilation and remote verdicts remain distinct.

Public exports belong in the narrow subpackage `__init__.py` and, only for
stable high-level operations, `fep_lean/__init__.py`. Add import-surface and
isolated-wheel tests whenever that contract changes.

The package root snapshots Python source hashes for import consistency and
loads high-level exports lazily. That snapshot is separate from the versioned
report/native owner roster and historical evidence custody.

Use the project-root [required checks](../../AGENTS.md#required-checks) and
[source ownership policy](../../AGENTS.md#source-of-truth).
