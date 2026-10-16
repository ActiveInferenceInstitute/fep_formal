# FEP_Formal functional specification

## Scope

The project validates the schema-2 168-topic catalogue sealed in
[`config/catalogue_metadata.yaml`](config/catalogue_metadata.yaml) against its
pinned Lean and Mathlib workspace. The evidence compiler and dependency revision
are defined by [`lean/lean-toolchain`](lean/lean-toolchain),
[`lean/lakefile.lean`](lean/lakefile.lean), and
[`lean/lake-manifest.json`](lean/lake-manifest.json). Pin and lock changes require
an explicit reviewed upgrade; a newer upstream release never replaces the
evidence compiler automatically. Package version metadata lives in
[`pyproject.toml`](pyproject.toml). [ISA.md](ISA.md) records accepted source
checkpoints; the [next-step campaign](specs/comprehensive-next-steps/README.md)
owns active implementation, [TODO.md](TODO.md) the open backlog, and
[HANDOFF.md](HANDOFF.md) dated evidence snapshots.

The pipeline can call configured Hermes, persist each session in SQLite, and
generate deterministic manuscript and report artifacts. Its operating contract
and required checks are maintained in [`AGENTS.md`](AGENTS.md).

## Execution modes

Mode definitions, capability and failure requirements, runtime policy, and
receipt interpretation are maintained in the
[execution contract](AGENTS.md#execution-contract). The
[source-owner map](AGENTS.md#source-of-truth) identifies maintained inputs and
generated projections.

## Public API

FEP_Formal is the project name; `fep_lean` remains the Python distribution and
import namespace, and `fep-lean` remains the installed command.

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

The [execution contract](AGENTS.md#execution-contract) defines read-only
validation and explicit setup boundaries; the
[required-check inventory](AGENTS.md#required-checks) owns validation commands.

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
