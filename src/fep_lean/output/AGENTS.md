# Output package contract

This folder owns deterministic rendering and evidence serialization. Keep one
canonical model per artifact family and make every tracked projection support a
non-mutating drift check.

## Invariants

- The formalism atlas consumes the coverage join; it does not parse YAML or
  Lean independently and never derives scientific relations from imports.
- The formal-kernel dashboard evaluates deterministic finite formulas mirrored
  by named declarations, labels itself as non-proof evidence, and shares one
  immutable data model across its SVG and interactive HTML projections.
- SVG and HTML render from the same immutable atlas model, conserve every node
  and authored edge, remain offline, and expose full text through accessible
  titles/tables.
- Evidence writers preserve source/toolchain digests and write atomically.
- Catalogue, native, declaration-audit, and full-run evidence stay separate.
- Manuscript rendering fails on unknown variables and never edits source
  chapters.
- `release_bundle/` owns archive assembly, renderer provenance, numerical
  receipts, and bundle manifests through its existing owner modules. Release archives contain only normalized
  regular files, exclude provider-plane reports, and are accepted only when
  native, declaration, projection, browser, numerical, and manuscript inputs
  independently bind to the live checkout.

## Verification

The [root required-check inventory](../../../AGENTS.md#required-checks) owns
projection and publication commands. Focused artifact contracts live in
`tests/test_formalism_atlas.py`, `tests/test_formal_kernel_dashboard.py`,
`tests/test_manuscript_artifacts.py`, `tests/test_reporter.py` and the release
bundle tests. Drift-check modes inspect existing outputs; they do not create
missing figures, archives or acceptance evidence. A real render and its retained
source/provenance artifacts have their own acceptance gate.
