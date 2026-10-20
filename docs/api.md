# Public Python API

**Version:** 1.6.0
**Last reviewed:** 2026-10-19

FEP_Formal's installed distribution exposes one root namespace, `fep_lean`.
Generic top-level names such as `catalogue`, `pipeline`, and `output` are not packages
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
assert catalogue.topics[-1].id == "fep-168"
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

The metadata, semantic review and relation sources remain authored in the
checkout. The methods module packages byte-identical generated copies for
portable mathematical inspection; novelty remains a checkout authoring input.
These low-level loaders still take explicit paths. The portable default is the
validated `fep_lean.methods` join documented below.

## Mathematical methods

```python
from fep_lean.methods import (
    build_mathematical_positioning,
    inspect_topic,
    analyze_topic,
    inspect_theorem,
    cross_corpus_embedding,
)

model = build_mathematical_positioning()
contract = inspect_topic(model, "fep-001")
analysis = analyze_topic(model, "fep-001")
statement = inspect_theorem(model, contract["primary_theorem_qualified"])
embedding = cross_corpus_embedding(model)
```

`build_mathematical_positioning()` validates the installed metadata, semantic
contracts, authored relations, family positioning policy and packaged Lean
resources. Pass an explicit checkout path to inspect its canonical owners.
The model labels its origin; source resolution supplies no native receipt.
Family features are inherited context. Neighbor queries use explicit binary
features, and bounded probes make failed transfers visible. Export/check
interfaces produce/read exactly the same JSON, Markdown, HTML and SVG model;
checks do not repair drift. See [mathematical methods](mathematical-methods.md)
for all public commands, mathematical scope and maintenance ownership.

For an installed wheel with an independent file-integrity check, use the same
immutable query type through the narrower entry point:

```python
from fep_lean.methods import load_packaged_formalism_query, inspect_topic

query = load_packaged_formalism_query()
contract = inspect_topic(query, "fep-001")
```

This entry point checks every consumed owner/resource and package Python file
against the installed distribution's standard `RECORD` hashes and sizes, builds
the existing canonical join, and checks the binding again. Missing, ambiguous,
foreign or unverifiable installation metadata raises `PositioningError`.
Editable checkouts use `build_mathematical_positioning(project_root)` instead.
The query retains schema version 1, exact assumptions, qualified declarations,
relation kinds, capability states, owner digests and its installed origin.
`as_dict()` returns a detached view; no additional mathematical registry or
materialized query snapshot is shipped.

The integrity boundary is the trusted installed wheel metadata. Replacing the
whole distribution and its `RECORD` is outside that boundary. The operation
reads files without launching Lean, a provider, a subprocess or a network call.
Its source-text model contains no live proof receipt; native and full-run
acceptance retain their separate validators.

The development checkout adds four reusable finite numerical methods:

```python
from fep_lean.methods import (
    finite_expectation,
    log_partition,
    exponential_tilt,
    gibbs_duality_diagnostics,
)

q, potential = (0.5, 0.5), (0.0, -1000.0)
mean = finite_expectation(q, potential)
log_z = log_partition(q, potential)
optimizer = exponential_tilt(q, potential)
diagnostic = gibbs_duality_diagnostics(q, q, potential)
```

These functions operate on numerical inputs without building a positioning
model. The [numerical contract](mathematical-methods.md#reusable-finite-variational-methods)
defines literal versus normalized masses, exact weighted accumulation,
supported log-domain scaling, true support failure and optimizer underflow.

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

Unknown areas, explicit empty topic lists and filters whose intersection is
empty fail during catalogue loading, before capability checks, provider calls
or artifact writes. Omitting both filters selects the full catalogue.

The explicit `output_root` argument takes precedence over a nonblank
`FEP_LEAN_OUTPUT_ROOT`, then `output.root` settings, then `project_root/output`.
The [configuration guide](configuration.md) defines relative-path semantics.
Validation, figures, reports and run-bound manuscript evidence use that same
selected root; the paired authored projections remain under `manuscript/`.

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
full_checks = run_validation_checks(
    project_root, mode="full", output_root=chosen_output
)
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
coverage and evaluates one deterministic witness for each of the seventeen
expansion families: Bayesian reconstruction, variational duality, control,
temporal inference, causal intervention, generalized predictive coding, path
thermodynamics, categorical Fisher geometry, consensus, concentration,
Laplace/Brier risk, policy-tree feedback, native blanket transfer,
exponential-family duality, the two-state master equation, the standalone
expected-free-energy floor, and geometric-mechanics skew cancellation. Every witness
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

## Readiness snapshots

The root and `fep_lean.output` export the same frozen `SectionReport`,
`PublicationReadinessReport` and `StatusReport` types, owned by
`fep_lean.output.evidence`. The public builder composes existing validators:

```python
from pathlib import Path
from fep_lean import build_status_report, report_to_json

root = Path("/path/to/fep_formal")
snapshot = build_status_report(root, gnn_root=None)
print(report_to_json(snapshot))
```

Snapshot inspection starts no process and writes no consumed input. Findings,
source bindings and named evidence planes retain their individual states.
Omitting the sibling checkout leaves that comparison unverified. The immutable
nested publication report distinguishes static currency from runtime execution
and two-archive parity; static all-green results remain unverified. The CLI
serializes this same snapshot. Its legacy imports remain the same objects.
New input-stability records name the public
`fep_lean.output.release_bundle.publication_input_snapshot` owner; historical
receipts keep their original provenance.

The release owner also exposes `inspect_stored_publication_evidence(root, plane)`
for exactly `publication_inputs`, `python_acceptance_receipt` and
`browser_acceptance_receipt`; unknown planes reject before inspection. These
are stored-evidence checks. The separate
`validate_render_acceptance_barrier(root)` performs the existing strict source
and reproduction checks, including bounded child processes and temporary
render work; it preserves publication files.

## Explicit caller roots and native operations

```python
from fep_lean import project_root_context
from fep_lean.verification import setup_workspace, verify_catalogue

with project_root_context(root):
    snapshot = build_status_report(root)

# Explicit acquisition/build, with the existing total deadline and pin checks:
setup_exit = setup_workspace(root)
# Explicit native execution, independent of CLI parsing or provider calls:
outcome = verify_catalogue(
    root,
    ["fep-001"],
    None,
    receipt_path=root / "output/native-verification.json",
    fail_on_warnings=True,
)
print(outcome.to_json())
verify_exit = outcome.exit_code
```

Project-root precedence is explicit CLI `--project-root`, then caller context,
then `FEP_LEAN_PROJECT_ROOT`, then the package checkout fallback. The context
resets on exit or error and does not mutate the process environment. It applies
to the current execution context; pass roots explicitly to new threads and
OS processes. The capture owner explicitly projects the caller root into a
copied child environment. Compiler children retain their separate allowlist.
`CatalogueVerification` carries a result mapping, canonical JSON indentation
and exit status; its mapping is an ordinary result value. Receipt validation,
warning/admission counts and failure exits match the CLI. Read-only preflight
remains separate from setup acquisition and native compilation.

## Command-line API

The installed console script is `fep-lean`. The
[CLI reference](cli-reference.md) owns the command inventory and command-specific
write, exit-status and evidence boundaries, including bridge, custody, methods
and publication capture. Use `fep-lean --help` for the installed parser surface.

The wheel provides imports, packaged catalogue and manifested formal resources,
and CLI help independently. The portable `methods` commands use installed
resources or numerical inputs; other substantive operator commands require a
complete source checkout because configuration, the Lean workspace, manuscript inputs, and output
ownership are intentionally not duplicated into the wheel. Invoke
`fep-lean --project-root /path/to/fep_formal COMMAND` outside that checkout.
`review` is a two-turn workflow: refinement, compilation, then prose-only
review of the exact compiled source; either provider turn can fail the result.

There is no separate `fep-lean-preflight` entry point. Use `fep-lean preflight`
so every operator command shares the same project-root and logging contract.
`fep-lean status` is read-only: it composes the existing fail-closed checks
into one evidence-currency report and exits 0 whenever the report composes.
See the status section in [CLI reference](cli-reference.md) for each
section's capability boundary.
The [operator support table](cli-reference.md#operator-support-and-exit-contracts)
separates required inputs, persistent writes, subprocesses, platform support and
exit interpretation for the inspection and execution paths.

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
