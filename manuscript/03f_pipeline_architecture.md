## Pipeline Architecture and Execution Profile {#sec:pipeline_architecture_and_execution_profile}

### The Central Execution and Orchestration DAG {#sec:execution_orchestration_dag}

The architecture is organized around evidence boundaries rather than one undifferentiated success flag:

```text
maintained metadata + semantic review + Lean bodies
                         |
                         v
             generated catalogue/package data
                 |                    |
                 v                    v
        native Lean receipt      optional full run
                 |                    |
                 +---------+----------+
                           v
                 checked manuscript build
```

Catalogue generation is offline. Native verification requires the pinned Lean workspace. Full mode additionally requires the declared Hermes and OpenGauss capabilities. Manuscript rendering consumes validated evidence but cannot create it.

### Expression Lifecycle: YAML → Manuscript → Lake {#sec:expression_lifecycle_yaml_to_lake}

The direction of ownership is fixed:

1. `config/catalogue_metadata.yaml`, `config/theorem_maturity.yaml`, `config/formalism_novelty.yaml`, and the family-owned `fep_lean.catalogue.bodies` modules are maintained inputs.
2. The catalogue generator joins metadata, semantic review, and bodies strictly by stable topic ID, validates every required novelty bridge against the maintained composition leaves, and writes checkout and wheel data from identical bytes.
3. Native verification reads the generated catalogue, invokes Lean, and may write a digest-bound receipt.
4. Manuscript variables are projected from the catalogue plus validated receipts.
5. The renderer validates all placeholders before writing numbered chapters to a separate build directory.

Generated YAML, aggregate Lean, coverage reports, manuscript variables, and appendices are projections; hand edits to them are not a valid repair.

### Sequence Diagram: Single Topic Execution {#sec:sequence_diagram_single_topic_execution}

For native verification, one selected topic follows catalogue load → isolated temporary source → `lake env lean` → structured result. In full mode, Hermes may propose or explain a sketch before native checking, but the kernel outcome remains decisive. A failed or unavailable provider cannot be converted into a native or full success through baseline substitution.

### Persistent State: Dual-Mode Storage {#sec:persistent_state_sqlite_schema}

Offline catalogue mode needs no external state. Native receipts are standalone JSON artifacts. Full mode may persist session and model interaction state through OpenGauss-compatible SQLite storage, while its publication contract is the independently validated report directory. The distinction lets readers verify compiler evidence without trusting a database or provider.

#### Per-topic audit trail {#sec:per_topic_audit_trail}

Canonical topic content lives in the generated package catalogue; semantic review lives in the maintained maturity source. Native receipt rows add compiler status, warnings, admissions, elapsed time, and toolchain identity. Full report rows add provider and orchestration provenance. The layers are linked by topic ID and digests, not by copied prose.

#### Run-level artifacts {#sec:run_level_artifacts}

The report validator, rather than this manuscript, owns the exact artifact roster. It rejects missing required files, unsafe paths, hash mismatches, disagreement among summary/run/verification manifests, incomplete topic rosters, and drift from the live source tree.

### SQLite Storage Boundaries {#sec:sqlite_schema_five_tables}

The optional persistence layer separates sessions, dialogue turns, artifacts, logs, and cached provider responses. This separation exists so a compiler result is not reconstructed from an LLM transcript and a cached provider response is not mistaken for a fresh run. The schema in `fep_lean.gauss.client` is canonical; duplicating its columns here would invite drift.

### Environment Variable Reference {#sec:environment_variable_reference}

Environment variables configure credentials, provider budgets, timeouts, and storage locations. The supported names and defaults belong to the configuration and CLI documentation. Two principles matter for reproducibility:

- credentials enable full mode but do not alter native theorem truth;
- changing a timeout or model invalidates any claim that a previous full receipt describes the new configuration.

The package now uses the unambiguous `fep_lean` namespace, so correctness no longer depends on placing collision-prone top-level modules such as `catalogue`, `pipeline`, or `output` first on `PYTHONPATH`.

### Representative Run Statistics {#sec:pipeline_run_statistics}

No unvalidated run is called representative. The renderer reports native evidence `{{verify.evidence_kind}}` with `{{verify.compiles_true}}/{{verify.topics_with_result}}` compiler successes, {{verify.warning_count}} warnings, and {{verify.sorry_occurrences}} admissions. It reports full readiness as `{{full.claim_ready}}`; Hermes fields remain unavailable unless that predicate is true.

### Execution Metrics: Representative Run {#sec:execution_metrics_the_definitive_run}

For receipt `{{verify.run_id}}`, recorded native compiler time is {{verify.duration_seconds}} seconds in total and {{verify.mean_topic_s}} seconds per result. Provider latency, if present in a claim-ready full receipt, is reported independently. These observations are machine-specific and are not extrapolated into general performance bounds.

### Reproducibility Checklist {#sec:reproducibility_checklist}

From the project root:

1. synchronize the locked Python environment with `uv sync --locked --extra dev`, whose test extras step 5 needs;
2. explicitly prepare the pinned Lean workspace with `uv run fep-lean setup` when its cache is absent;
3. regenerate and drift-check catalogue, aggregate Lean, semantic audit, and coverage projections;
4. run `uv run fep-lean verify --fail-on-warnings --receipt output/native-verification.json` for native evidence;
5. generate manuscript variables, run the placeholder and theorem-reference audits, and render to `output/manuscript/`;
6. run full mode only when its external capabilities and credentials are intentionally supplied, then validate its report before citing it.

Hermes wording may vary. A fixed Lean source under the pinned toolchain is reproducible; a native receipt additionally binds that result to the current catalogue bytes.
