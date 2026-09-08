# AGENTS.md — fep_lean

## Purpose

Standalone 155-topic FEP / Active Inference / Bayesian Mechanics / Information
Geometry / Thermodynamics catalogue with Lean 4 source, Hermes integration,
OpenGauss SQLite persistence, deterministic manuscript artifacts, and strict
reports.

## Terminology

The Lean code for each catalogue row is a **canonical topic body**. Family-owned
modules under `src/fep_lean/catalogue/bodies/` export those bodies, and
`src/fep_lean/catalogue/registry.py` validates and merges them. The generated
runtime field remains named `lean_sketch` for API compatibility. The reviewed
invariant, formal Lean identifiers, and explicit assumptions define the row's
**theorem proxy** and scientific scope in `config/theorem_maturity.yaml`.
Compilation without `sorry` establishes that exact Lean body only; it does not
promote the semantic disposition or prove the full FEP concept.

## Source of truth

- `config/catalogue_metadata.yaml` — schema-2 roster seal, family membership,
  titles, areas, Mathlib hints, and compile-maturity metadata.
- `config/theorem_maturity.yaml` — maintained semantic review records for the
  catalogue theorem proxies; `docs/theorem-maturity-audit.md` is generated from
  this file.
- `config/formalism_novelty.yaml` — maintained expansion ledger with earlier
  nearest topics, invariants, carrier deltas, and required `FEPComposed`
  bridges.
- `config/formalism_relations.yaml` — maintained derivational-formal,
  theorem-pairing, conceptual, and blocker relations plus retained capability
  status/evidence. Never infer these from shared imports; both theorem-backed
  kinds require qualified Lean witnesses.
- `src/fep_lean/catalogue/bodies/*.py` — family-owned canonical Lean bodies.
- `src/fep_lean/catalogue/registry.py` and `latex.py` — validated body registry
  and deterministic theorem-signature projection.
- `config/topics.yaml` and `src/fep_lean/data/topics.yaml` — byte-identical,
  generated catalogue projections; never author either by hand.
- `scripts/_maint_build_topics_catalogue.py` — YAML regeneration.
- `scripts/_maint_build_fep_all_lean.py` — tracked aggregate regeneration.
- `src/fep_lean/formal/manifest.py` — explicit foundation, leaf-composition,
  and aggregate resource roster. Cross-topic proofs live in
  `formal/compositions/*.lean`; `formal/composed.lean` is the import-only
  aggregate. `scripts/_maint_build_formal_modules.py` projects the manifest
  into the workspace.
- `lean/FepSketches/fep_all.lean` — whole-catalogue Lean target.
- `ISA.md` — ideal-state criteria, anti-criteria, and evidence gates.
- `TODO.md` — canonical open-only backlog; completed work is not retained as
  struck-through rows.
- `HANDOFF.md` — next-reviewer protocol, evidence receipt, and remaining scope.
- `src/fep_lean/output/provenance.py` — versioned source-owner roster
  (`OWNER_MANIFEST_VERSION`, `SOURCE_OWNER_ROSTER`). New files under
  `src/fep_lean/**/*.py` or `scripts/*.py` fail report and native receipts
  fail-closed until reviewed into the roster; roster growth is a coordinated
  evidence refresh (`FEP-EVIDENCE-CURRENT`), not a per-PR append. Sanctioned
  per-PR alternatives: fold new code into an existing owner or keep tooling
  slice-local under `specs/`.

## Execution contract

- `uv run fep-lean catalogue` is explicit offline mode. It creates deterministic
  catalogue artifacts and reports zero verified topics.
- `uv run fep-lean verify` is the Lean-only native compile path. It requires
  the built pinned Mathlib cache but does not call Hermes, OpenGauss, or the
  full pipeline. Use `--receipt PATH --fail-on-warnings` for publication-grade
  native evidence.
- `uv run fep-lean atlas` projects the canonical coverage graph to offline SVG
  and accessible HTML; `--check` is a non-mutating freshness gate.
- `uv run fep-lean dashboard` evaluates the typed numerical witnesses and
  projects their shared model to offline SVG and accessible HTML; it is
  explanatory non-proof evidence, and `--check` is non-mutating.
- `uv run fep-lean run` is strict full mode. It requires configured Hermes,
  OpenGauss, Lean, Lake, and a complete pinned Mathlib build.
- Missing capabilities, failed topics, or artifact errors produce a failed
  result and no successful report.
- A full-mode report's `complete: true` means all *selected* topics passed (via
  `FEP_LEAN_MAX_TOPICS` or the default full catalogue). It is publication-ready
  only when `validate_report_receipt(...).claim_ready` independently validates
  the complete full-mode artifact set. Catalogue-mode completion is never
  Hermes or Lean evidence. A native receipt is separately claim-ready only for
  the live-source-bound sealed roster, actual compiler output matching the pin,
  the resolved Mathlib revision, and zero errors, warnings, or `sorry`.
- `run_validation_checks` is read-only. Dependency acquisition belongs only to
  `uv run fep-lean setup` and is bounded by `FEP_LEAN_SETUP_TIMEOUT_SEC`.
- `preflight` JSON output is advisory subject to additive field changes between
  releases. Stable referential queries use the CLI exit code and `status` field.

## Required checks

```bash
uv lock --check && uv pip check
uv run python scripts/_maint_build_topics_catalogue.py --check
uv run python scripts/_maint_build_fep_all_lean.py --check
uv run python scripts/_maint_build_formal_modules.py --check
uv run python scripts/theorem_maturity_audit.py --check
uv run python scripts/build_formalism_coverage.py --check
uv run python scripts/_maint_build_lean_landscape.py --check
uv run python scripts/build_formalism_atlas.py --check
uv run python scripts/build_formal_kernel_dashboard.py --check
uv run python scripts/audit_formalisms.py \
  --receipt output/formalism-audit.json
uv run python docs/theorem_ref_audit.py
uv run python docs/citation_audit.py
uv run fep-lean catalogue
uv run python scripts/render_manuscript.py --check
uv run python scripts/build_render_fonts.py --check
uv run python scripts/check_render_log.py --verify-receipt
uv run pytest tests/ -q --cov=src --cov-fail-under=89 -m "not serial_lean"
uv run mypy src
uv run ruff check src tests scripts docs
uv run ruff format --check src tests scripts docs
uv run python docs/check_links.py --strict --include-root
uv run python docs/md_hygiene.py --strict
uv run python docs/pin_audit.py --check-latest
uv run python docs/xref_audit.py
uv run python specs/gnn-bridge-q5-artifact-proof/generate_probe.py --check
uv run python specs/geo-infer-notation-bridge/check_geo_notation_bridge.py --check
```

Live bridge and native-receipt checks additionally require the explicitly
named GNN pair: `fep-lean bridge status --gnn-root PATH`, both emitters'
`--check`, and `verify_native.py --check --gnn-root PATH --receipt
specs/gnn-bridge-q5-artifact-proof/native_receipt.json`; the listed
`generate_probe.py --check` needs the same sibling checkout. They are not
unconditionally runnable, are not executed by CI, and never repair content
drift.

Do not claim Lean verification from catalogue mode or from generated manuscript
values. Native compilation and full Hermes/OpenGauss execution are distinct
evidence planes; state exactly which validated receipt supports a claim.

## GNN bridge operations

`uv run fep-lean bridge --help` exposes explicit source pinning, emission,
read-only status, and numerical comparison receipts. Pass `--gnn-root`; normal
standalone tests require no sibling checkout. Source pins bind owner bytes,
not a perpetually refreshed HEAD. Default checks never regenerate reports.
The package tests include `tests/test_gnn_bridge_operations.py`.
Numerical agreement is not native proof or proof of current execution.
