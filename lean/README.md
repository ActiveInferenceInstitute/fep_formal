# Lean workspace — FEP Sketches

**Version**: v1.6.0 | **Status**: Active | **Last Updated**: October 2026

Lake package with full **Mathlib4 v4.35.0** dependency (see `lakefile.lean` / `lake-manifest.json`).

The exact Lean and Mathlib tags track the newest stable compatible release pair.
The repository does not float to release candidates or nightlies;
`docs/pin_audit.py --check-latest` detects when a newer compatible pair is
available and reports newer Lean-only patches as pending Mathlib support. A
pair upgrade then requires the full migration and evidence cascade.

## One-Time Setup

Run from the project root:

```bash
# From the project root (directory containing pyproject.toml)
uv run fep-lean setup
```

The guarded setup validates the declared toolchain and resolved Mathlib revision,
acquires their exact cache and builds under one bounded process-group deadline.
It preserves the dependency pins and never runs `lake update`. Set
`FEP_LEAN_SETUP_TIMEOUT_SEC` to bound acquisition; read-only validation acquires
nothing. A deliberate pin upgrade requires its own migration and evidence refresh.

## Manual Verification

```bash
cd lean
lake build FepSketches
```

The tracked `FepSketches/fep_all.lean` aggregate is regenerated from the
family-owned canonical topic bodies. Every foundation, leaf-composition, and
import-aggregate resource declared by `src/fep_lean/formal/manifest.py` has an
exact workspace projection. From the project root, check both projection
families:

```bash
uv run python scripts/_maint_build_fep_all_lean.py --check
uv run python scripts/_maint_build_formal_modules.py --check
```

After `lake build FepSketches`, resolve every reviewed primary/evidence
declaration and inspect evidence axioms with:

```bash
uv run python scripts/audit_formalisms.py \
  --receipt output/formalism-audit.json
```

## Environment Variables

| Variable | Purpose |
|---|---|
| `FEP_LEAN_LAKE_EXE` | Override path to `lake` binary |
| `FEP_LEAN_LEAN_EXE` | Override path to `lean` binary |
| `ELAN_HOME` | Override elan home (default: `<tmpdir>/fep_lean_elan_<uid>`, e.g. `/tmp/fep_lean_elan_501` on Linux, `$TMPDIR/fep_lean_elan_501` on macOS) |
| `FEP_LEAN_VERIFY_TIMEOUT` | Compilation timeout in seconds (default: 300) |
