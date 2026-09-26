# H2.7 terminal acceptance record contract

The retained [terminal acceptance record](terminal-acceptance.json) validates
328 mandatory cases, the enabled Fin4 supplement, independently recomputed
diagnostics, and three fresh source-bound reviews. Its evidence is retained in
[evidence/20260904-wave2/](evidence/20260904-wave2/). Changes to the bound
sources invalidate acceptance until new evidence is reviewed and sealed.

The receipt has exactly `schema_version: 1`, `gate: H2.7`, `decision: accepted`,
`native_evidence`, `current_sources`, `predecessors`, `reviews`, `diagnostics`,
and `downstream`. The module exposes the fixed predecessor whitelist and
downstream scope; neither permits an arbitrary newest-receipt override.

`native_evidence` contains `collection` and `junit` artifact references (each
exactly `path` and `sha256`), `source_before`, `source_after`, and integer
`pytest_exit_code: 0`, and `heavy_probe_supplement` (normally `null`). Native source maps come from `native_source_paths(root)`
and must match the captured stable bytes. They exclude later diagnostic and
acceptance Python additions. Collection JSON has `schema_version: 1`, the
complete ordered `nodeids` list, and `markers` mapping every node ID to its
captured marker-name list. Its immutable SHA-256 is pinned by
`CAPTURED_COLLECTION_SHA256` to the actual 1771-node baseline capture, preventing
jointly rewritten collection/XML from dropping parameterized cases. Copy the
captured JSON byte-for-byte when placing it in the project evidence directory.
JUnit must contain exactly those nodes, no duplicate,
failure or error, consistent finite numeric counts/times, and no mandatory
skip/xfail. Every mandatory source test definition must appear in collection.
The single heavy H2.5b-R0 Fin4 consumer may have a visibly retained baseline
skip only when `heavy_probe_supplement` binds a separate JUnit containing exactly
that passing node. The supplement has `junit`, equal native `source_before` and
`source_after`, integer `pytest_exit_code: 0`, and exactly
`environment: {"FEP_HEAVY_LEAN_PROBES": "1"}`. It cannot cover another omission,
hide a failure, or substitute changed sources. A `skipif` marker alone is not a
failed outcome; unconditional `skip` and `xfail` markers remain ineligible.

`current_sources` is `source_snapshot(root, CURRENT_FILES)`. Each of exactly
three review artifact references resolves an object with `schema_version: 1`,
`role` (`lean`, `domain`, or `skeptical`), a distinct actual `reviewer_id`,
`decision: approve`, substantive `findings`, and `source_sha256` equal to the
union of native and current maps. Capture fresh reviews after source freeze;
old prose summaries cannot be relabeled as these approvals.

`diagnostics` references the exact output of `diagnostic_record(root)`. It
evaluates fixed IDs `h2-scalar-terminal` and `h2-fin4-blanket` through the existing
numerical registry, requires `horizon2` scope and the established non-proof
evidence kind, reconstructs every `NumericalCheck`, and tests its operands.
It compares the complete serialized witnesses to fresh evaluation rather than
trusting a claimed `passed` flag. Diagnostic before/after maps bind current
diagnostic/validator sources, including `_horizon_numerical_witnesses.py` and its
tests, the catalogue body registry and its Python owners, declaration parsing,
and the formal source plane. These are the consumed diagnostic inputs; YAML
catalogue projections are not read by this evaluator. The Fin4 stationarity
check compares the evolved covariance with independently integrated spectral
diffusion noise, so an incorrect transverse decay rate fails the diagnostic.

The six historical predecessor records and fixed current R0 custody successor
are immutable byte-pinned inputs. Their historical source bindings are checked;
only the named successor may supersede the two reviewed R0 source differences.
R0 native evidence must be verified and match its current source map.

`uv run python specs/horizon-2-smooth-stochastic/readiness/terminal_acceptance.py
validate --project-root .` is read-only. `diagnostics` evaluates the numerical
records. Either operation writes only when `--output` names a new explicit file;
no input is overwritten. Success permits read-only H3.G0, not H3 implementation,
empirical promotion, or publication.

Explicit outputs under the project must remain in the evidence output
directories and may not traverse a symlinked parent. An explicitly named
external destination remains allowed. Serialization completes before exclusive
creation, so an invalid payload does not leave an empty output file.
