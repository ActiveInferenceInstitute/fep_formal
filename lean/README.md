# FEP_Formal Lean workspace

This is the Lake workspace for the `FepSketches` library. Lean is pinned by
[lean-toolchain](lean-toolchain); the Mathlib requirement and exact dependency
revision are owned by [lakefile.lean](lakefile.lean) and
[lake-manifest.json](lake-manifest.json). Read those files for current pins.

The repository qualifies stable Lean/Mathlib pairs together. The
[root check inventory](../AGENTS.md#required-checks) includes the pin audit;
a pair upgrade requires a reviewed migration and refreshed evidence.

## Setup and maintenance

Run explicit dependency setup from the project root:

```bash
uv run fep-lean setup
```

Setup validates declared pins and the resolved Mathlib revision, acquires the
exact cache and builds under the `FEP_LEAN_SETUP_TIMEOUT_SEC` deadline. It
preserves dependency pins and never runs `lake update`. Ordinary validation
acquires nothing.

Topic bodies are authored in the
[body registry](../src/fep_lean/catalogue/AGENTS.md). Reusable Lean resources are
authored under the [formal package](../src/fep_lean/formal/AGENTS.md) and selected
by its typed manifest. `FepSketches/` contains generated projections of those
owners. Change an owner, regenerate its projection and inspect the diff;
never repair a workspace copy by hand.

The [required checks](../AGENTS.md#required-checks) distinguish aggregate build,
orphan compilation, serial probes, exact-roster native verification and the
declaration/axiom audit. A successful aggregate build alone is insufficient to
claim every current source or a full provider workflow was accepted.

## Executable and timeout configuration

`FEP_LEAN_LAKE_EXE` and `FEP_LEAN_LEAN_EXE` select explicit binaries.
`ELAN_HOME` is respected for toolchain discovery and child execution; when
unset, the compiler child's writable home is a per-user temporary directory.
[`_toolchain.py`](../src/fep_lean/verification/_toolchain.py) owns resolution and
the allowlisted child environment. `FEP_LEAN_VERIFY_TIMEOUT` configures the
per-topic compilation deadline; its default is owned by
[`lean_verifier.py`](../src/fep_lean/verification/lean_verifier.py).

See [AGENTS.md](AGENTS.md) for the workspace contract and
[Lean operations](../docs/lean4.md) for detailed usage.
