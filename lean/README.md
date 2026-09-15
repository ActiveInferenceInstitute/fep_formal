# Lean workspace — FEP Sketches

**Version**: v1.1.0 | **Status**: Active | **Last Updated**: August 2026

Lake package with full **Mathlib4 v4.34.0** dependency (see `lakefile.lean` / `lake-manifest.json`).

The exact Lean and Mathlib tags track the newest stable compatible release pair.
The repository does not float to release candidates or nightlies;
`docs/pin_audit.py --check-latest` detects when a newer compatible pair is
available and reports newer Lean-only patches as pending Mathlib support. A
pair upgrade then requires the full migration and evidence cascade.

## One-Time Setup

Run from a regular (non-sandboxed) terminal:

```bash
# From the project root (directory containing pyproject.toml)
bash scripts/_maint_bootstrap_lean_toolchain.sh
# (``fep-lean setup`` is a thin wrapper to the same bootstrap.)
```

Or manually:

```bash
cd lean
lake update        # fetch Mathlib4
lake exe cache get # download ~3 GB prebuilt .olean cache
lake build         # build FepSketches
```

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
| `ELAN_HOME` | Override elan home (default: `/tmp/fep_lean_elan`) |
| `FEP_LEAN_VERIFY_TIMEOUT` | Compilation timeout in seconds (default: 300) |
