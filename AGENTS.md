# AGENTS.md — FEP_Formal

## Purpose

FEP_Formal is a standalone 168-topic FEP / Active Inference / Bayesian
Mechanics / Information Geometry / Thermodynamics catalogue with Lean 4 source,
Hermes integration, OpenGauss SQLite persistence, deterministic manuscript
artifacts and strict reports. The repository is `fep_formal`; the Python
distribution/import namespace is `fep_lean` and the executable is `fep-lean`.
Preserve those package, CLI, environment-variable and Lean namespace interfaces
when updating project-facing prose.

## Terminology

The Lean code for each catalogue row is a **canonical topic body**. Family-owned
modules under `src/fep_lean/catalogue/bodies/` export those bodies, and
`src/fep_lean/catalogue/registry.py` validates and merges them. The generated
runtime field remains named `lean_sketch` for API compatibility. The reviewed
invariant, formal Lean identifiers, and explicit assumptions define the row's
**theorem proxy** and scientific scope in `config/theorem_maturity.yaml`.
Compilation without `sorry` establishes that exact Lean body only; it does not
promote the semantic disposition or prove the full FEP concept.

## Which document is current

| Document | Role | Status |
| --- | --- | --- |
| [README.md](README.md) | Project overview, first run, release line, contracts | Authoritative |
| [.github/README.md](.github/README.md) | GitHub landing projection of the root README, with rebased local links | Generated; edit the root README |
| [AGENTS.md](AGENTS.md) | This agent contract; per-directory `AGENTS.md` files refine it | Authoritative |
| [CLAUDE.md](CLAUDE.md) | Claude Code entry point that imports this contract | Authoritative (pointer) |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Environment, check tiers, repository rules, PR conventions | Authoritative |
| [TODO.md](TODO.md) | Canonical open-only backlog, one linked Issue per row | Authoritative |
| [CHANGELOG.md](CHANGELOG.md) | Release changes and their evidence boundary | Authoritative |
| [docs/release.md](docs/release.md) | Release procedure and gate | Authoritative |
| [SPEC.md](SPEC.md) | Functional specification of the validated catalogue | Authoritative |
| [ISA.md](ISA.md) | Ideal state, anti-criteria, evidence gates and accepted source checkpoints | Authoritative; dated in its front matter |
| [Next-step campaign](specs/comprehensive-next-steps/README.md) | Active dependency graph, work-package contracts and current pickup point | Active implementation plan; acceptance remains package-specific |
| [PAI.md](PAI.md) | Agent command interface | Authoritative |
| [HANDOFF.md](HANDOFF.md) | Next-reviewer protocol and evidence receipt, dated 2026-10-11 | Dated snapshot |
| [SCOPE-2026-09-30.md](specs/comprehensive-science-improvement/SCOPE-2026-09-30.md) | Retained preimplementation baseline of that day's scope review | Dated snapshot |
| [SCOPE-2026-10-08.md](specs/comprehensive-science-improvement/SCOPE-2026-10-08.md) | Scope review of that day; every candidate is filed as an Issue and tracked in `TODO.md` | Dated snapshot |

When a snapshot and an authoritative document disagree, the authoritative
document wins.

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
  kinds require qualified Lean witnesses. Shared imports never create
  scientific-dependency edges.
- `src/fep_lean/catalogue/bodies/*.py` — family-owned canonical Lean bodies.
- `src/fep_lean/catalogue/registry.py` and `latex.py` — validated body registry
  and deterministic theorem-signature projection.
- `src/fep_lean/catalogue/generation.py` — catalogue join for checkout and
  package projections.
- `config/topics.yaml` and `src/fep_lean/data/topics.yaml` — byte-identical,
  generated catalogue projections; never author either by hand.
- `scripts/_maint_build_topics_catalogue.py` — YAML regeneration.
- `scripts/_maint_build_fep_all_lean.py` — tracked family-shard and compatibility
  aggregate regeneration. Its check covers every manifest-owned output.
- `src/fep_lean/formal/manifest.py` — explicit foundation, leaf-composition,
  and aggregate resource roster. Cross-topic proofs live in
  `formal/compositions/*.lean`; `formal/composed.lean` is the import-only
  aggregate. `scripts/_maint_build_formal_modules.py` projects the manifest
  into the workspace.
- `lean/FepSketches/families/*.lean` — generated family topic modules with
  unchanged public namespaces; composition leaves import their actual families.
- `lean/FepSketches/fep_all.lean` — import-only whole-catalogue compatibility target.
- `src/fep_lean/output/evidence.py` — frozen readiness/status models and their
  process-free snapshot builder; CLI JSON projects those same type/function
  objects. Native/full evidence policy and manuscript
  claim sentences.
- `src/fep_lean/verification/formalism_audit.py` — declaration and axiom audit
  with typed receipts.
- `src/fep_lean/output/formalism_atlas.py` — coverage-graph SVG/HTML renderer.
- `manuscript/*.md` — authored chapters, rendered into `output/manuscript/`.
- `ISA.md` — ideal-state criteria, anti-criteria, and evidence gates.
- `TODO.md` — canonical open-only backlog; completed work is not retained as
  struck-through rows.
- `HANDOFF.md` — dated next-reviewer protocol and evidence snapshots; the
  [next-step campaign](specs/comprehensive-next-steps/README.md) owns the active
  implementation graph and pickup point.
- `src/fep_lean/output/provenance.py` — versioned source-owner roster
  (`OWNER_MANIFEST_VERSION`, `SOURCE_OWNER_ROSTER`). New files under
  `src/fep_lean/**/*.py` or `scripts/*.py` fail report and native receipts
  fail-closed until reviewed into the roster; roster growth is a coordinated
  evidence refresh (the completed refresh is recorded in
  [CHANGELOG.md](CHANGELOG.md); a further roster change re-opens the
  requirement), not a per-PR append. Sanctioned
  per-PR alternatives: fold new code into an existing owner or keep tooling
  slice-local under `specs/`.

Never hand-edit `config/topics.yaml`, `src/fep_lean/data/topics.yaml`,
`lean/FepSketches/fep_all.lean`, any manifested `lean/FepSketches` formal resource,
`docs/formalism-coverage.*`, `docs/formalism-atlas.*`, or generated manuscript
output. Use the owner-provided generators and their `--check` modes.

## Maintaining documentation

Use **FEP_Formal** for the project and `fep_formal` for the checkout/repository.
Use `fep_lean` for the real Python distribution/import namespace and `fep-lean`
for the CLI. Historical titles, external integration paths, environment
variables, citation versions and accepted receipts retain their exact identities.

Root `README.md` is the canonical project overview and packaging long description.
`.github/README.md` is its generated GitHub presentation, with local links rebased
from the `.github` directory. After editing the root overview, regenerate it with
`uv run python docs/check_links.py --write-github-readme`; do not edit the mirror
by hand. The existing strict `--include-root` link check also refuses missing or
stale mirror bytes and scans maintained `.github` Markdown. See
[.github/AGENTS.md](.github/AGENTS.md) for repository presentation and workflow rules.

Directory READMEs explain responsibility and entry points; their AGENTS files
state local ownership and verification constraints. Keep the required-check list
below as its single owner, and link to canonical configuration or generated
inventories rather than copying changing rosters. Audit maintained prose against
actual source behavior. Mark dated reviews as dated, and preserve frozen specs,
receipt-bound captures and generated outputs under their existing contracts.

## Execution contract

- `uv run fep-lean catalogue` is explicit offline mode. It creates deterministic
  catalogue artifacts and reports zero verified topics. It performs strict
  YAML/schema/source-parity validation and generates offline figures, manuscript
  variables, the unified appendix, and a report. It records
  `verified_topics: 0` and `capabilities.verification: false`.
- `uv run fep-lean verify` is the Lean-only native compile path. It requires
  the built pinned Mathlib cache but does not call Hermes, OpenGauss, or the
  full pipeline. Use `--receipt PATH --fail-on-warnings` for publication-grade
  native evidence. With `--receipt` it writes a typed, source-digest-bound receipt.
- `uv run fep-lean atlas` projects the canonical coverage graph to offline SVG
  and accessible HTML; `--check` is a non-mutating freshness gate. The graph distinguishes
  derivational formal edges from checked formal pairings that place two endpoint
  laws side by side without asserting implication. Both name qualified Lean
  witnesses; conceptual and blocker edges remain visibly non-proof evidence.
  It carries no compilation or full-run claim.
- `uv run fep-lean dashboard` evaluates the typed numerical witnesses and
  projects their shared model to offline SVG and accessible HTML; it is
  explanatory non-proof evidence, and `--check` is non-mutating. It renders a
  shared immutable model; every witness names theorem mirrors, parameters,
  typed exact checks with per-check tolerances, and boundary behavior.
- `uv run fep-lean run` is strict full mode. It requires configured Hermes,
  OpenGauss, Lean, Lake, and a complete pinned Mathlib build. This is the default
  for the programmatic API. It also requires the isolated `gauss --version` availability probe,
  writable configured output and persistence destinations, and Hermes
  credentials as defined in [Configuration](docs/configuration.md). The
  [OpenGauss guide](docs/opengauss.md) owns the credential-safe probe behavior. It executes one Hermes + Lean +
  SQLite session per selected topic. Every selected row must compile without
  `sorry` or Lean warnings, and a requested review workflow must complete its
  post-compile review turn. A topic succeeds only when the Hermes-derived
  sketch compiles without proof holes. Any failed capability or topic makes the
  pipeline incomplete and prevents a successful report.
- Missing capabilities, failed topics, or artifact errors produce a failed
  result and no successful report. **Missing capability or incomplete stage →
  `complete: false`, no report directory.**
- A full-mode report's `complete: true` means all *selected* topics passed (via
  `FEP_LEAN_MAX_TOPICS` or the default full catalogue). It is publication-ready
  only when `validate_report_receipt(...).claim_ready` independently validates
  the complete full-mode artifact set. Catalogue-mode completion is never
  Hermes or Lean evidence. A native receipt is separately claim-ready only for
  the live-source-bound sealed roster, actual compiler output matching the pin,
  the resolved Mathlib revision, and zero errors, warnings, or `sorry`.
- `run_validation_checks` is read-only. Dependency acquisition belongs only to
  `uv run fep-lean setup` and is bounded by `FEP_LEAN_SETUP_TIMEOUT_SEC`.
  It never downloads Mathlib, invokes a build, creates a database, or writes a
  report. The explicit setup command performs dependency acquisition and
  `lake build` with a bounded timeout.
- `preflight` JSON output is advisory subject to additive field changes between
  releases. Stable referential queries use the CLI exit code and `status` field.
- `uv run fep-lean status` composes a read-only evidence-currency report from
  existing checks; exit 0 means the report composed, not that evidence is
  current.
- `uv run fep-lean topic <id>` verifies one exact topic with the same workflow
  choices as `run`.
- `uv run fep-lean report` runs catalogue mode and emits a complete report.
- Python 3.14 is the only accepted validator environment (see
  `.python-version`); `requires-python >=3.10` in `pyproject.toml` is the
  packaging floor, not the validator contract.

These witnesses expose computational behavior and boundary cases but
never replace native Lean or axiom-audit evidence. The declared test gate
requires at least 89% line coverage. Branch coverage, hosted wheel
compatibility, native compilation, and full-mode acceptance need their own
scoped evidence.

The same split Python/Chrome coverage XML must also pass the measured package
line floors in [docs/coverage-floors.json](docs/coverage-floors.json). The
[coverage guide](docs/coverage-branch.md) records their baseline and scope.
These floors do not measure branch arcs or supply native/scientific acceptance.

## Required checks

This block is the single owner of the required-check list. `docs/development.md`,
`docs/testing.md` and the root overview/specification/handoff link here instead
of re-listing it. Their source-owner and execution references also link to this
document. Setup examples remain examples rather than a second gate list, and
`tests/test_check_inventory.py` fails if a command below is neither executed in
`.github/workflows/ci.yml` nor on that test's commented hosted-only/local-only
allow-lists, if CI runs a gate that is missing here, or if those reference
sections duplicate the maintained definitions. Add a check to CI and to this
block in the same change.

Ruff checks all active Python tooling, including slice-local specs. The narrow
historical/generated/pinned-input exclusions in `pyproject.toml` follow
`specs/AGENTS.md`; their bytes remain unchanged. Strict mypy covers the package,
scripts and docs at the Python 3.14 validator target. Ruff retains Python 3.10
syntax compatibility, and the installed-wheel matrix checks the packaging floor
separately. Exceptions preserve declared error or compatibility contracts and
must be justified at the affected line.

For credential-free local test runs, set `FEP_LEAN_LIVE_TESTS=0` explicitly.
The [test contract](tests/AGENTS.md) explains the provider families whose
selection can otherwise depend on ambient credentials.

Hosted Python, isolated Chrome and serial Lean pytest components retain their
complete warning-inventory logs with CLI warning visibility enabled. This
measurement precedes any narrowing of the existing filters; it does not turn
warnings into errors or change Lean's zero-warning acceptance. The serial lane
also retains its per-case JUnit file so actual compiler-review outcomes and
skip reasons remain independently inspectable. Distribution,
supplemental specs and nested/consumed warnings retain separate measurement
boundaries. The production-capture executor is unchanged.

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
uv run python specs/openai-math-methods/generate_package_methods.py --check
uv run fep-lean --project-root . methods check --output-root docs/mathematical-positioning
uv run pytest specs/openai-math-methods/test_methods.py \
  specs/openai-math-methods/test_upstream.py \
  specs/openai-math-methods/test_visualization.py -q --no-cov
uv run ruff check specs/openai-math-methods
uv run ruff format --check specs/openai-math-methods
uv run pytest specs/cascadia-experiments/test_proof_impact.py -q --no-cov
uv run pytest specs/cascadia-experiments/test_diagnostic_bounds.py -q --no-cov
uv run ruff check specs/cascadia-experiments
uv run ruff format --check specs/cascadia-experiments
uv run python scripts/audit_formalisms.py \
  --receipt output/formalism-audit.json
uv run python docs/theorem_ref_audit.py
uv run python docs/citation_audit.py
uv run fep-lean catalogue
uv run python scripts/render_manuscript.py --check
uv run python scripts/build_render_fonts.py --check
uv run python scripts/check_render_log.py --verify-receipt
uv run python scripts/build_manuscript_figures.py
uv run python scripts/build_manuscript_figures.py --check
uv run python -B specs/gnn-runner-execution/validate_retained.py
uv run python -B specs/gnn-runner-execution/test_validate_retained.py
uv run ruff check specs/gnn-runner-execution
uv run ruff format --check specs/gnn-runner-execution
uv run pytest specs/publication-browser-acceptance/test_validate_acceptance.py -q --no-cov
uv run ruff check specs/publication-browser-acceptance
uv run ruff format --check specs/publication-browser-acceptance
uv run python specs/publication-browser-acceptance/validate_acceptance.py --collect output/python-acceptance-collection.json
uv run pytest tests/ -q --cov=src --cov-report=xml --cov-fail-under=89 -m "not serial_lean"
uv run python docs/check_coverage_floors.py --coverage coverage.xml
uv run mypy src scripts docs
uv run ruff check .
uv run ruff format --check src tests scripts docs
git diff --check
uv run python docs/check_links.py --strict --include-root
uv run python docs/md_hygiene.py --strict --include-root
uv run python docs/pin_audit.py --check-latest
uv run python docs/xref_audit.py
uv run python docs/check_orphan_compiles.py
uv run python specs/gnn-bridge-q5-artifact-proof/generate_probe.py --check
uv run python specs/cascadia-geo-act-proof/generate_probe.py --check
uv run python specs/geo-infer-notation-bridge/check_geo_notation_bridge.py --check
```

Native Lean checks need the built pinned Mathlib cache (`lake exe cache get`)
and run in the hosted `lean` job:

```bash
(cd lean && lake build FepSketches)
uv run pytest tests/ -q -m serial_lean -n 1 --no-cov
uv run fep-lean verify --fail-on-warnings --receipt output/native-verification.json
uv run python specs/cascadia-experiments/verify_diagnostic_bounds.py --compile output/cascadia-diagnostic-bounds
uv run python specs/cascadia-experiments/verify_diagnostic_bounds.py --check output/cascadia-diagnostic-bounds
```

Hosted CI also runs the `distribution` installed-wheel matrix, the isolated
live Chrome pair and the membership aggregate of
`validate_acceptance.py`; see `docs/testing.md` for those boundaries.

The listed Q5 `generate_probe.py --check` and GEO notation checks validate
retained static artifacts without a sibling checkout. CI runs both. Q5
generation establishes fixture/probe/manifest freshness, not current
GNN-renderer custody or native evidence.

Live source-custody and current native-receipt checks require the explicitly
named GNN pair: `fep-lean bridge status --gnn-root PATH`, both emitters'
`--check`, and the applicable `verify_native.py --check --gnn-root PATH
--receipt PATH`. These additional live checks are conditional, are not
executed by CI, and never repair content drift. Select the exact receipt for
the claimed artifact proof. Historical Q5/Q6 receipts remain historical after
a source re-pin; a fresh Q7 receipt establishes only its own checked native
statements and source pair.

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


### Strict serial native producer and optional dual shadow

CI always selects the existing serial catalogue node's strict, unfiltered
`verify_catalogue` operation and independently validates its fresh native receipt,
existing intent/API record and once-passing JUnit node. This is the reviewed CI
decomposition of the strict `fep-lean verify --fail-on-warnings` operation below;
local CLI and the default local catalogue test remain unchanged. Missing, failed
or stale producer evidence fails; the job never hides it with another compile.

The manual `native_producer_shadow` input defaults to false. When selected, the
ordinary CLI additionally executes and its receipt is compared with the retained
first receipt on every non-duration field. Both actual execution origins and
workflow run/attempt/checkout bindings remain independently validated. Standard
native artifacts retain the existing intent/API records, without a new schema.
Any rollout requires actual full automatic PR/default and explicit dual-shadow acceptance;
no measured release speedup follows from this source change alone.


### Full automatic PR and explicit dual-shadow acceptance profiles

Automatic code PRs, normal main pushes and manual full runs use the same full
15-cell installed-wheel matrix (three OS families, Python 3.10 through 3.14).
The default native lane consumes its strict serial producer once. A separate
explicit manual full dual-shadow run executes the ordinary CLI as a second
strict operation and preserves both receipts. Local default CLI behavior is
unchanged. No extra manual default full run is required by this proposed profile
once its actual rollout is independently accepted; the explicit dual-shadow and
fresh merged-main full runs remain mandatory. Until rollout acceptance, the
current accepted profile policy remains in force.

Full profile contexts are 22 total: 21 successful roles/cells plus the configured
documentation skip. Artifact validation must authenticate automatic PR synthetic
merge parents/tree and preserve actual checkout/source/render origin; it must
not relabel synthetic execution as candidate or merged-main execution. Original
producer checkout/receipt paths are observed in the same-job context marker.
No new receipt schema, production owner, sidecar, cache-trust substitution,
classifier change or measured speedup is implied. Exact test membership is
collected and reviewed on the final composed source before acceptance.
