## Native Lean 4 Compilation and Execution-Integrity Verification {#sec:native_lean_4_compilation_and_zero_direct_verification}

Native verification is a compiler operation, not a catalogue property. The rendered evidence kind is `{{verify.evidence_kind}}`; claim readiness is `{{verify.claim_ready}}`; the full-catalogue rate is `{{compile_rate.total}}`, with {{verify.warning_count}} warnings and {{verify.sorry_occurrences}} admitted proofs in the selected receipt. If no matching receipt exists, these fields render as unavailable rather than borrowing a `complete` flag from catalogue mode.

### Why Simulated Compilation Fails {#sec:why_simulated_compilation_fails}

A generated success value cannot establish that imports resolve, types unify, tactics close their goals, or the pinned Mathlib API contains a cited declaration. The package therefore sends the exact canonical topic body to the pinned Lean binary and records compiler output. Tests may isolate subprocess behavior, but publication evidence must come from an actual native receipt.

### The `lean_verifier.py` Architecture {#sec:the_leanverifierpy_architecture}

The compiler bridge lives in `fep_lean.verification.lean_verifier`. Its public contract is intentionally small: isolate a sketch, invoke Lean through Lake, and return a structured `VerifyResult`. The source remains authoritative for implementation details.

#### Stage 1: Sketch Isolation and Temporary File Construction {#sec:stage_1_temporary_file_construction}

Each topic is written to its own temporary file inside the Lake workspace. Isolation prevents declarations from one topic satisfying another topic accidentally and permits the temporary source to be removed after the result is captured.

#### Stage 2: Native Shell Invocation {#sec:stage_2_native_shell_invocation}

The verifier invokes the pinned workspace through:

```bash
lake env lean FepSketches/<temporary-file>.lean
```

Executable discovery respects explicit overrides and the toolchain named by `lean/lean-toolchain`; it does not silently download dependencies. Acquisition belongs to the explicit setup command.

#### Stage 3: Output Parsing and `VerifyResult` {#sec:stage_3_output_parsing_and_error_taxonomy}

`VerifyResult` separates process success, `sorry` detection, compiler warnings, compiler errors, elapsed time, and an advisory failure category. Native claim readiness is stricter than process exit zero: every requested row must compile, no source may contain `sorry`, and warnings must be absent.

| Result dimension | Why it remains separate |
| --- | --- |
| `compiles` | Lean accepted elaboration and checking |
| `has_sorry` | The source admitted an unproved goal |
| `warnings` | Lean accepted the file but reported a quality or migration issue |
| semantic disposition | Human-reviewed relationship between theorem and topic claim |

### Aggressive Mathlib4 Caching {#sec:aggressive_mathlib_caching}

The local `.lake` tree is an untracked build cache. Verification refuses a visibly incomplete Mathlib workspace and instructs the operator to run the explicit setup path. The cache changes latency, not theorem meaning, and it is never publication evidence.

### Measured Compilation Headline {#sec:measured_compilation_headline}

The only headline used here is receipt-derived: **`{{compile_rate.total}}`** for receipt `{{verify.run_id}}`. Its {{verify.topics_with_result}} results contain {{verify.compiles_true}} compiler successes, {{verify.compiles_false}} failures, {{verify.warning_count}} warnings, and {{verify.sorry_occurrences}} uses of `sorry` in {{verify.sorry_topics}} topics. `mathlib_status: real` is not substituted for any of these numbers.

### Preflight: `LeanVerifier.check_mathlib_built()` {#sec:leanverifier_preflight}

Preflight checks that the pinned Lake workspace and required Mathlib object files exist before a batch begins. It is intentionally read-only. A failed preflight stops verification rather than producing one misleading import failure per topic.

### Verbose Mode: `FEP_LEAN_VERIFY_VERBOSE=1` {#sec:fep_lean_verify_verbose}

Verbose mode increases diagnostic logging for local reproduction. The stable automation surface is the CLI JSON and optional native receipt; prose should not depend on incidental log formatting.

### Sequential Batching: `verify_batch(max_workers=1)` {#sec:verify_batch_sequential}

The shared Lake workspace is verified sequentially. This favors reproducibility over throughput because concurrent compiler processes can contend over the same build tree. Parallelism would require isolated workspaces and a separate evidence review.

### Cache Timing: Cold vs Warm vs Cached {#sec:cache_timing}

Compiler timing depends on hardware and cache state. This manuscript reports only the elapsed values present in the selected receipt: {{verify.duration_seconds}} seconds total and {{verify.mean_topic_s}} seconds per result. It does not promote local cold/warm observations into general performance claims.

### The Execution-Integrity Standard Applied {#sec:the_zero_direct_standard_applied}

Execution integrity means that evidence is collected at the boundary where the claim is decided:

- Lean claims come from the Lean process and source scan;
- source identity comes from content digests;
- full-run claims come from reconciled and hashed report artifacts;
- semantic adequacy comes from maintained review records;
- manuscript values come from validated projections.

No one boundary can certify another.

### Methodological Assumptions and Limits {#sec:methodological_assumptions_and_limits}

Lean checks derivability in the imported formal system. It does not choose the uniquely correct formalization of an informal FEP statement, validate an empirical model, establish physical realizability, or infer composition merely because separately namespaced bodies share imports. Composition is established only where the maintained foundations or named leaf-composition witnesses state it explicitly; every other bridge remains a semantic or scientific obligation.

#### Formal Definition of Execution Integrity {#sec:formal_definition_of_zero_direct}

A native claim is accepted exactly when a schema-valid receipt identifies the canonical ordered roster, reconciles every result row, reports complete warning-free and `sorry`-free compilation, and matches the current catalogue, family-body source manifest, Lean toolchain, and Mathlib pin. A full claim additionally requires a valid full-mode report with artifact hashes and current source/configuration digests.

#### Per-Stage Success Criteria {#sec:per_stage_success_criteria}

| Boundary | Acceptance criterion | Failure meaning |
| --- | --- | --- |
| Catalogue generation | Typed sources join and generated projections are current | Authoring or drift error |
| Native Lean | Selected compiler results satisfy the native receipt | Formal compilation evidence unavailable |
| Full pipeline | Required capabilities and every selected full-mode row succeed | No Hermes/OpenGauss publication claim |
| Manuscript rendering | Every placeholder and theorem identifier resolves | Publication build blocked |

#### Three Levels of Truth {#sec:three_levels_of_truth}

The project keeps three claims ordered but non-interchangeable:

1. **Syntactic and kernel evidence:** the stated Lean proposition compiles without warnings or admissions.
2. **Semantic adequacy:** the proposition matches the reviewed topic claim under explicit assumptions and has a non-vacuity argument where needed.
3. **Scientific adequacy:** the formal object captures the intended empirical or physical system.

The current work directly automates the first, maintains an explicit audit of the second, and does not claim the third.
