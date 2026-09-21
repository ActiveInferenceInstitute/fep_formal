# fep_lean/lean/

**Version**: v1.2.0 | **Status**: Active | **Last Updated**: September 2026

Full **Lake** workspace with **Mathlib4** dependency for FEP theorem verification.

## Toolchain

- **Lean**: `leanprover/lean4:v4.34.0` (see `lean-toolchain`)
- **Mathlib**: `v4.34.0` — see `lakefile.lean` and the exact revision in
  `lake-manifest.json`

## Layout

| File / Dir | Purpose |
|---|---|
| `lakefile.lean` | Lake package: declares `require mathlib` |
| `lean-toolchain` | Pins Lean 4 toolchain version |
| `lake-manifest.json` | Pins Mathlib4 git commit for reproducibility |
| `FepSketches/` | Library root containing generated `fep_all.lean` and `composed.lean`; verifier-owned temporary probes are removed |
| `.lake/packages/mathlib/` | Downloaded Mathlib4 source (after `lake exe cache get`) |

## One-Time Setup (non-sandboxed terminal)

```bash
# From the project root

# 1. Run the automated bootstrap script
bash scripts/_maint_bootstrap_lean_toolchain.sh
# (`fep-lean setup` wraps the same script.)

# Or manually:
cd lean
lake update           # fetch Mathlib4 @ v4.34.0 (see `lakefile.lean`)
lake exe cache get    # download ~3 GB prebuilt .olean cache
lake build            # build FepSketches against Mathlib
```

## Verification Workflow

After setup, `LeanVerifier` in `src/fep_lean/verification/lean_verifier.py` calls:

```bash
lake env lean FepSketches/_verify_{topic_id}_{random}.lean
```

This inherits the full Mathlib4 environment so every body in the sealed topic
roster resolves its declared `import Mathlib.*` dependencies.

## macOS Sandbox Bypass

The elan proxy may fail with `settings.toml: Operation not permitted`
in sandboxed AI agent shells.  `LeanVerifier` bypasses this by:

1. Setting `ELAN_HOME` to a per-user writable tempdir
   (`<tmpdir>/fep_lean_elan_<uid>`, e.g. `/tmp/fep_lean_elan_501` on Linux, `$TMPDIR/fep_lean_elan_501` on macOS)
2. Resolving `lake`/`lean` via direct toolchain path:
   `~/.elan/toolchains/leanprover--lean4---v4.34.0/bin/lake`
3. Respecting `FEP_LEAN_LAKE_EXE` / `FEP_LEAN_LEAN_EXE` env overrides

## Concurrency boundary

Run per-topic `lake env lean` checks serially. They share one Lake build tree,
and concurrent verifier subprocesses have produced toolchain/cache contention
and misleading missing-import failures in sandboxed environments. Parallelism
belongs outside one workspace, not inside `LeanVerifier.verify_batch`.

`FepSketches/composed.lean` and `FepSketches/compositions/*.lean` are byte-exact
projections of the manifested package resources; never edit the workspace
copies. The composition leaves own cross-topic proofs, while `composed.lean` is
their import-only aggregate. Formal relations may name only declarations that
resolve through that aggregate. Validate both projection and axioms from the
project root:

```bash
uv run python scripts/_maint_build_formal_modules.py --check
uv run python scripts/audit_formalisms.py \
  --receipt output/formalism-audit.json
```

## See also

- [../AGENTS.md](../AGENTS.md) — project-level documentation
- [../docs/lean4.md](../docs/lean4.md) — Lean4 + Mathlib4 context
- [../scripts/_maint_bootstrap_lean_toolchain.sh](../scripts/_maint_bootstrap_lean_toolchain.sh) — setup automation (`fep-lean setup` delegates here)
- [math-inc/OpenGauss](https://github.com/math-inc/OpenGauss) — optional CLI integration
