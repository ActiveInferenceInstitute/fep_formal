# Public Python API

**Version:** 1.2.0
**Last reviewed:** 2026-09-10

The installed distribution exposes one root namespace, `fep_lean`. Generic
top-level names such as `catalogue`, `pipeline`, and `output` are not packages
and have no compatibility aliases. The root package re-exports the stable
operator-facing types and functions listed in `fep_lean.__all__`; direct
submodule imports make ownership clearest in application code.

This page documents contracts, not every private helper. Runtime annotations
and docstrings in `src/fep_lean/` are the executable signature source, and the
distribution tests pin the installed import and console-script boundary.

## Catalogue

```python
from fep_lean.catalogue import FEPTopicCatalogue, TopicEntry

catalogue = FEPTopicCatalogue.default()
assert catalogue.topics[0].id == "fep-001"
assert catalogue.topics[-1].id == "fep-155"
summary = catalogue.summary()
```

`FEPTopicCatalogue.default()` reads the generated `topics.yaml` bundled in the
wheel through `importlib.resources`; it does not require a repository checkout.
`from_yaml(path)` is the explicit-path variant. Both reject an incomplete or
reordered roster, malformed fields, unknown areas/dispositions, empty Lean or
equation data, and theorem/equation-count drift.

`TopicEntry` is an immutable projection with these fields:

| Field | Meaning |
| --- | --- |
| `id`, `title`, `area` | Stable identity and five-area classification |
| `mathlib`, `mathlib_status` | Declared library surface and syntactic maturity |
| `primary_theorem` | Audited principal declaration for the row |
| `semantic_disposition` | Claim-alignment class, independent of compilation |
| `nl`, `assumption_review`, `non_vacuity`, `acceptance_probe` | Reviewed semantic projection |
| `lean_sketch` | Canonical generated Lean body |
| `latex_equations` | Typeset signatures in declaration order |

`summary()` returns topic, area, Mathlib-maturity, semantic-disposition, and
area-by-disposition counts computed from the loaded rows. It does not report
verification success.

## Authoring and coverage loaders

The maintainer-facing catalogue API also exports:

```python
from fep_lean.catalogue import (
    load_catalogue_metadata,
    load_formalism_graph,
    load_formalism_novelty,
    load_theorem_maturity,
)
```

These functions accept explicit `Path` inputs and strictly validate the four
maintained checkout sources. The formalism graph distinguishes derivational
`formal`, non-implicational `formal_pairing`, `conceptual`, and `blocked_by`
edges and rejects unknown targets, self-edges, duplicates, unsorted data,
formal cycles, and unused capability nodes. Both theorem-witnessed edge kinds
require qualified composition-leaf declarations that use both endpoints;
capability nodes retain an
`open`/`partial`/`satisfied` status and declaration evidence when resolved.

Only the generated topic catalogue is a default wheel resource. Metadata,
semantic review, novelty, and relation YAML are publication-authoring inputs in a source
checkout; callers must pass their paths explicitly.

## Pipeline

```python
from fep_lean.pipeline import FEPPipeline, run_pipeline, run_single_topic

offline = run_pipeline(mode="catalogue")
native_candidate = FEPPipeline(project_root).run(
    mode="full",
    topic_filter=["fep-001"],
    workflow="verify",
)
single = run_single_topic("fep-001", mode="full")
```

The main signatures are:

```python
FEPPipeline.run(
    *,
    mode: Literal["catalogue", "full"] = "full",
    topic_filter: list[str] | None = None,
    area_filter: str | None = None,
    workflow: str = "verify",
) -> PipelineResult

run_pipeline(
    *,
    mode: Literal["catalogue", "full"] = "full",
    interactive: bool = False,
    area_filter: str | None = None,
    topic_filter: list[str] | None = None,
    workflow: str = "verify",
    output_root: Path | None = None,
) -> PipelineResult

run_single_topic(
    topic_id: str,
    *,
    mode: Literal["catalogue", "full"] = "full",
    interactive: bool = False,
    workflow: str = "verify",
    output_root: Path | None = None,
) -> PipelineResult
```

`PipelineResult` records `status`, `mode`, `complete`, selected and verified
counts, capability flags, failure reason, stages, topic rows, run directory,
and duration. Catalogue mode can be complete while `verified_topics` remains
zero. Full mode is incomplete if a required capability or selected topic
fails, emits a Lean warning, retains `sorry`, or does not complete a requested
review stage.

## Native Lean verification

```python
from fep_lean.verification import LeanVerifier, VerifyResult

verifier = LeanVerifier(project_root=project_root)
result = verifier.verify_sketch(topic.id, topic.lean_sketch)
batch = verifier.verify_batch([(topic.id, topic.lean_sketch)])
```

`VerifyResult` keeps compiler success, warning lines, `sorry` detection,
diagnostics, duration, Lean version, skip reason, and failure classification
separate. Batch verification is serial because topic checks share one Lake
workspace.

Environment validation is read-only:

```python
from fep_lean import run_validation_checks

catalogue_checks = run_validation_checks(project_root, mode="catalogue")
full_checks = run_validation_checks(project_root, mode="full")
```

Dependency acquisition belongs to the explicit `fep-lean setup` command, not
to validation or package import.

The declaration/axiom audit is a separate native evidence surface:

```python
from fep_lean.verification import (
    run_formalism_audit,
    write_formalism_audit_receipt,
)

audit = run_formalism_audit(project_root)
write_formalism_audit_receipt(Path("output/formalism-audit.json"), audit)
```

It resolves every reviewed primary and semantic-evidence declaration through
the generated topic aggregate and every foundation, leaf-composition, and
aggregate module in the formal resource manifest, requires one parsed
`#print axioms` result for every
declaration, normalizes Lean's hard-wrapped messages in the receipt, and fails
on missing declaration evidence, projection drift, warnings, compiler errors,
timeouts, or `sorryAx`.

## Evidence receipts

```python
from fep_lean.output import (
    validate_native_lean_receipt,
    validate_report_receipt,
)

native = validate_native_lean_receipt(
    Path("output/native-verification.json"),
    project_root=Path.cwd(),
)
full = validate_report_receipt(
    report_dir,
    require_complete=True,
    project_root=Path.cwd(),
)
```

`validate_native_lean_receipt` independently recomputes row totals and live
catalogue/body-source digests. `native_claim_ready` requires an explicitly
supplied live project root, the exact sealed roster, current sources, uniform actual
Lean output matching the pin, the resolved Mathlib revision, finite timing
records, complete clean compilation, zero errors, zero warnings, and zero
`sorry`.

`validate_report_receipt` verifies a report bundle's paths, artifact hashes,
source digests, selected-topic counts, exact per-topic artifact roster, complete
topic evidence rows, compiler/Mathlib identity, warning lists/counts, and
completion fields. Full claim readiness requires successful provider and
direct-compile evidence, nonempty session/model provenance, exact compiled
source digests, zero warnings, and live-source binding.
Catalogue reports may be structurally valid but are never claim-ready full-run
evidence. `latest_claim_ready_full_report` searches only independently accepted
full-mode bundles.

## Manuscript and reports

```python
from fep_lean.output import (
    Reporter,
    build_manuscript_vars,
    manuscript_projection_drift,
    render_manuscript,
)

variables = build_manuscript_vars(catalogue, project_root)
assert manuscript_projection_drift(project_root, catalogue) == ()
rendered = render_manuscript(source_dir, destination_dir, variables)
paths = Reporter(project_root).generate(catalogue, pipeline_result)
```

Manuscript variables contain semantic counts and complete evidence sentences;
they do not turn unavailable run metrics into zero-valued success. The drift
check pins canonical topic, formalism, toolchain, test-census, and appendix
bytes while comparing only the schema—not local values—of receipt/provider
blocks. Rendering validates the full placeholder inventory before writing,
rejects source and destination aliasing, and atomically writes a separate
build tree.

The unified formalism appendix is assembled from two pure component renderers:
the exact Lean catalogue and its typeset theorem signatures. There is one
writer for the unified appendix and one writer for manuscript variables; the
obsolete split appendix files are neither authored inputs nor outputs.

`Reporter.generate` writes a timestamped Markdown/JSON report bundle and its
verification manifest. Use `ReportPaths` for emitted locations and validate the
bundle before making evidence claims.

## Formalism atlas

```python
from fep_lean.output import (
    atlas_projection_drift,
    build_formalism_atlas,
    render_formalism_atlas_html,
    render_formalism_atlas_svg,
    write_formalism_atlas,
)

atlas = build_formalism_atlas(project_root)
svg = render_formalism_atlas_svg(atlas)
html = render_formalism_atlas_html(atlas)
paths = write_formalism_atlas(project_root)
```

Both renderers consume one positioned immutable model built from canonical
coverage. They conserve every topic, retained capability, and authored edge;
formal witnesses are displayed but never inferred. The outputs use no external
assets, and the HTML includes keyboard interaction and complete tables.

## Formal-kernel dashboard

```python
from fep_lean.output import (
    build_formal_kernel_dashboard,
    formal_kernel_dashboard_drift,
    render_formal_kernel_dashboard_html,
    render_formal_kernel_dashboard_svg,
    write_formal_kernel_dashboard,
)

dashboard = build_formal_kernel_dashboard(project_root)
svg = render_formal_kernel_dashboard_svg(dashboard)
html = render_formal_kernel_dashboard_html(dashboard)
paths = write_formal_kernel_dashboard(project_root)
assert formal_kernel_dashboard_drift(project_root) == ()
```

The immutable dashboard model binds summary metrics to canonical formalism
coverage and evaluates one deterministic witness for each of the fifteen
expansion families: Bayesian reconstruction, variational duality, control,
temporal inference, causal intervention, generalized predictive coding, path
thermodynamics, categorical Fisher geometry, consensus, concentration,
Laplace/Brier risk, policy-tree feedback, native blanket transfer,
exponential-family duality, and the two-state master equation. Every witness
owns typed equality, inequality, or predicate checks with per-check tolerances;
acceptance is their conjunction plus the boundary observation. The SVG and
HTML are offline projections of the same source data. They are explanatory
numerical checks, not theorem or empirical-evidence receipts.

## Hermes and OpenGauss

`fep_lean.llm` exports `HermesConfig`, `HermesExplainer`, `HermesResult`, and
`HermesAPIError`. Configuration is loaded from environment and the canonical
settings file; model names and fallbacks should be read from live configuration
rather than copied into API documentation.

`fep_lean.gauss` exports `OpenGaussClient`, `SessionRecord`, `GaussRunner`, and
`TopicRunResult`. The client owns SQLite sessions, turns, artifacts, structured
events, and Hermes-result caching. The runner owns one topic's Hermes, Lean,
and session lifecycle and always records whether the verified sketch was native
or Hermes-derived.

Provider-backed calls occur only in full mode with valid credentials. Imports,
catalogue mode, native verification, and receipt validation do not call a
provider.

## Command-line API

The installed console script is `fep-lean`:

```text
fep-lean setup
fep-lean preflight
fep-lean bridge {status,pin,emit,certify,verify-certificate,verify-document} --gnn-root PATH
fep-lean verify [--area AREA] [--topic ID] [--fail-on-warnings] [--receipt PATH]
fep-lean catalogue [--area AREA] [--topic ID]
fep-lean atlas [--check]
fep-lean dashboard [--check]
fep-lean run [--area AREA] [--topic ID] [--workflow verify|draft|prove|review]
fep-lean topic ID [--workflow verify|draft|prove|review]
fep-lean report
fep-lean status [--gnn-root PATH]
```

The wheel provides imports, packaged catalogue and manifested formal resources,
and CLI help independently. Operator subcommands require a complete source checkout
because configuration, the Lean workspace, manuscript inputs, and output
ownership are intentionally not duplicated into the wheel. Invoke
`fep-lean --project-root /path/to/fep_lean COMMAND` outside that checkout.
`review` is a two-turn workflow: refinement, compilation, then prose-only
review of the exact compiled source; either provider turn can fail the result.

There is no separate `fep-lean-preflight` entry point. Use `fep-lean preflight`
so every operator command shares the same project-root and logging contract.
`fep-lean status` is read-only: it composes the existing fail-closed checks
into one evidence-currency report and exits 0 whenever the report composes.
See the status section in [CLI reference](cli-reference.md) for each
section's capability boundary.

## GNN bridge

`fep_lean.bridge` exposes the cross-repo operations surface (contract v0.6):

- CLI: `fep-lean bridge {status,pin,emit,certify,verify-certificate,verify-document} --gnn-root PATH`.
- Python: `status`, `pin_sources`, `check_sources`, `emit`,
  `certificate_receipt`, `emit_certificate`, `validate_certificate`,
  `verify_document`.
- Custody constants: `PIN`, `EMITTERS`, `DOCUMENTS`, `CONTRACT`, `MIRROR`,
  `SYNTAX_PIN`, `SYNTAX_FILES`; primitives `fingerprint`, `binding_digest`,
  `validate_binding`.

The source-custody pin (`specs/gnn-bridge-w2-source-custody/source-pin.json`)
seals owner bytes on both sides. The GNN owner-roster glob is
`src/gnn/**/*.py` plus `src/gnn/main.py`; the pin JSON shape is
`{"schema_version": 1, "fep_lean": {"commit", "owners"}, "gnn": {"commit", "owners"}}`.
`verify-document --document PATH` extracts one emitted document through the
pinned render route (`gnn.extract.pomdp_extractor.extract_pomdp_from_file`,
strict validation) and decides `FEP.GnnDocument.documentWellFormed` in a
compile-once Lean probe. Receipt schema: `{"schema_version": 2, "document",
"model_family", "extracted_family", "toolchain", "status", "warnings"}`.

## Formal Lean modules

The `fep_lean.formal` namespace carries the bridge's typed surface:

- `FEP.GnnDocument` — `GnnSectionKind` (frozen 13-kind inventory in canonical
  rank order), `GnnDocument`, `documentWellFormed`, and `WellFormed`
  (decidable mechanical well-formedness).
- `FEP.GnnDenotation` — `DiscreteConforms` / `ContinuousConforms` for the two
  model families.
- `FEP.GnnRenderStatements` — renderer statement contracts.

Compile with the committed workspace: `lean/` (Lake + Mathlib4); see
`lean/README.md`.

## Stability boundary

- Stable: the `fep_lean` root namespace, documented exports, CLI command names,
  stable topic IDs, and receipt validators.
- Versioned data: generated catalogue rows, semantic dispositions, formalism
  relations, and receipt schemas.
- Internal: underscore-prefixed helpers, raw SQLite tables, temporary Lean file
  layout, and exact report-rendering helpers not re-exported at a package
  boundary.

For architecture and source ownership, continue with
[Architecture](architecture.md) and [Development](development.md).
