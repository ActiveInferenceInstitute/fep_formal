# Verification package contract

This folder owns four different surfaces:

1. `run_validation_checks` is a read-only capability probe. It must not fetch a
   toolchain, build Mathlib, create a database, or write a report.
2. `LeanVerifier` compiles an explicitly supplied sketch in the pinned Lake
   workspace and returns a structured result. It must preserve errors,
   warnings, `sorry`, skip reason, failure kind, toolchain identity, and timing
   as separate fields.
3. `run_formalism_audit` resolves every reviewed primary/evidence declaration
   through the topic aggregate and the manifest-selected Lean module imports.
   `composed.lean` aggregates the composition leaves; it is not the sole import
   owner for every foundation. The audit requires parsed axiom output for every
   declaration, records the actual Lean version and resolved Mathlib revision,
   and fails on missing evidence, stale projections, warnings, compiler errors,
   `sorryAx`, or any axiom outside the versioned trusted set (`propext`,
   `Classical.choice`, and `Quot.sound`).

4. `setup_workspace` explicitly acquires/builds the pinned workspace with a
   single total deadline, allowlisted compiler environment and exact pin
   preimages. It is separate from read-only capability inspection.

`preflight.py` is an adapter for `fep-lean preflight`; it is not a second public
console script. Installation and dependency acquisition belong to
`fep-lean setup`.

## Invariants

- Resolve `lean` and `lake` through `_toolchain.py`; do not create a parallel
  executable search path.
- Keep batch verification serial around the shared `.lake` tree.
- Delete only verifier-owned `_verify_*.lean` temporary files.
- A successful process exit with warnings or `sorry` is not a clean result.
- The formalism audit receipt is declaration/axiom evidence, not a replacement
  for an exact sealed-roster native receipt.
- `check_mathlib_built()` is a presence probe, not proof that the current
  catalog compiled.
- Full-mode validation requires every local capability and a permitted Hermes
  credential; catalog mode remains offline.

## Verification scope

Use the [root required-check inventory](../../../AGENTS.md#required-checks)
for the environment, native and declaration-audit commands. Focused contracts
live in the Lean-verifier, environment and preflight tests; the serial Lean
lane exercises compiler-dependent consumers separately from ordinary Python
acceptance. An unavailable dependency is not a passing native probe.

The credentialed full-mode probe is an external acceptance stage. Never add a
secret to tests, documentation, receipts, or the checkout.
