# fep_lean functional specification

**Version:** 1.1.0

## Scope

The project validates the schema-2 155-topic YAML catalogue against a pinned
Lean 4.34.0 and Mathlib 4.34.0 workspace. Exact pins track the newest stable
Lean/Mathlib release pair; release candidates and nightlies remain opt-in and
cannot silently replace the evidence compiler. It can also call the configured Hermes
service, persist each session in SQLite, and generate deterministic manuscript
and report artifacts.

## Execution modes

### `catalogue`

This mode performs strict YAML/schema/source-parity validation and generates
offline figures, manuscript variables, the unified appendix, and a report. It
records `verified_topics: 0` and `capabilities.verification: false`.

### `full`

This is the default for the programmatic API and requires every configured
capability: `gauss doctor`, the exact Lean/Lake pins, a complete Mathlib build,
writable GAUSS_HOME, and Hermes credentials. It executes one Hermes + Lean +
SQLite session per selected topic. A topic succeeds only when the Hermes-derived
sketch compiles without proof holes. Any failed capability or topic makes the
pipeline incomplete and prevents a successful report.

### `verify`

This command is a separate native Lean evidence path. It compiles canonical
topic bodies without Hermes or OpenGauss. With `--receipt` it writes a typed,
source-digest-bound receipt; full-catalogue claim readiness additionally
requires the exact ordered roster, zero failures, zero warnings, zero `sorry`,
and current toolchain/catalogue/source identities.

### `atlas`

This command is a deterministic offline projection of canonical coverage. It
writes a standalone SVG and self-contained interactive HTML view, or performs a
non-mutating drift check with `--check`. It carries no compilation or full-run
claim; derivational formal edges and non-implicational formal pairings display
the qualified Lean witnesses already maintained by the relation graph.

### `dashboard`

This command evaluates the typed deterministic numerical witness registry and
renders a shared immutable model as offline SVG and accessible HTML. Every
witness names theorem mirrors, parameters, typed exact checks with per-check
tolerances, and boundary behavior. The dashboard is explanatory non-proof
evidence; `--check` performs
a non-mutating freshness test.

## Public API

```python
from fep_lean.pipeline.core import FEPPipeline
from fep_lean.pipeline.orchestrator import run_pipeline, run_single_topic

result = run_pipeline(mode="catalogue")
result = run_pipeline(mode="full", topic_filter=["fep-001"])
result = run_single_topic("fep-001", mode="full")
```

`PipelineResult` exposes `mode`, `complete`, `catalogue_topics`,
`verified_topics`, `capabilities`, `failure_reason`, `stages`, and
`topic_results`. `TopicRunResult` records both the refined sketch and its
`verification_source`; no result is silently substituted or relabeled.

## Validation

`run_validation_checks(project_root, mode=...)` is read-only. It never downloads
Mathlib, invokes a build, creates a database, or writes a report. The explicit
`fep-lean setup` command performs dependency acquisition and `lake build` with a
bounded timeout.

The catalogue loader rejects missing fields, divergence from the maintained
roster seal, duplicate or out-of-order IDs, unsupported areas/statuses, empty
theorem bodies, mismatched equation counts, and divergence from the validated
family-body registry under `src/fep_lean/catalogue/`.
The formalism-graph loader separately rejects unknown or self targets,
unsupported edge kinds, duplicate edges, derivational-formal cycles,
unreferenced capabilities, and missing blocker edges for semantic gap rows.
Both `formal` and `formal_pairing` edges require resolvable qualified witnesses;
conceptual and blocker edges forbid witnesses. Partial/satisfied capability
nodes require resolvable declaration evidence.

`run_formalism_audit` imports the aggregate Lean library, whose manifested leaf
composition modules own the cross-topic witnesses. It resolves every primary
and semantic-evidence declaration, runs `#print axioms` for the evidence set,
and fails on stale projections, warnings, compiler errors, timeouts, or
`sorryAx`.

## Artifacts

Successful pipeline runs write a timestamped report containing Markdown, JSON,
a verification manifest, and SHA-256 hashes. Catalogue generation writes
`manuscript/manuscript_vars.yaml` and the unified appendix. Rendering writes
resolved chapters to `output/manuscript/` without changing authored Markdown.
Generated files are never evidence by themselves: native claims require a
validated native receipt, and Hermes/OpenGauss claims require an independently
validated, claim-ready full report.

The tracked coverage JSON/Markdown, formalism atlas SVG/HTML, and numerical
dashboard SVG/HTML are deterministic projections with non-mutating drift
checks. Every manifested workspace Lean module is an exact projection of its
packaged canonical resource.
