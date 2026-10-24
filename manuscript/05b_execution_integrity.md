# Execution integrity {#sec:execution_integrity}

Every success claim in this project is tied to a concrete artifact or an
observable computation. Catalog mode validates and renders the {{total_topics}} source
entries, but it makes no Lean or Hermes claim. Full mode first validates every
required capability and then records the Hermes response, refined Lean source,
compiler result, SQLite session, and report manifest for each selected topic.

## Evidence boundaries

The evidence boundary is deliberately explicit:

1. YAML is loaded by the strict catalog schema and checked against the
   sealed family-body registry and generated aggregate.
2. Lean evidence comes only from `lake env lean` using the pinned workspace.
3. Hermes evidence comes from an HTTP response accepted by the configured
   response parser; a missing credential or invalid response is an error.
4. SQLite evidence is written transactionally and exported files are checked
   against their recorded hashes.
5. Report manifests bind the run to source and configuration digests, the
   Lean/Mathlib pins, capabilities, topic counts, and artifact hashes.

An unavailable capability therefore ends a full run before a success report is
created. The result is diagnostic JSON with `complete: false` and a structured
`failure_reason`. Offline work is available only through the explicitly named
`catalogue` mode, whose result always reports zero verified topics.

## Lean verification

`LeanVerifier` writes a temporary source file, invokes the real Lake command,
captures diagnostics, removes the temporary file, and records the result. In
full mode, a topic succeeds only when the Hermes-refined source compiles
without warnings or a proof placeholder; in native mode, the same compiler
boundary checks the canonical source directly. A prose-only review cannot
replace the candidate that actually compiled. The original catalog body
and any refined source are retained as separate fields; the original is never
presented as the refined result.

The committed `lean/FepSketches/fep_all.lean` is generated from the canonical
catalog source, while manifested foundations, leaf compositions, and their
import-only aggregate are projected from `src/fep_lean/formal/`. Regeneration
checks fail when either projection differs, and the Lean build compiles the
library against the exact pinned toolchain. The formalism audit then resolves
reviewed declarations and checks their reported axioms; aggregate success alone
does not supply that semantic evidence roster.

## Source-bound GNN numerical audits {#sec:gnn_semantic_audits}

The GNN semantic audit is a separate numerical evidence path. It reads retained
authored source for a restricted stationary finite model or passive
linear-Gaussian filtering model, then compares GNN's path-enumeration or joint
Gaussian reference with an independent forward-filter or Kalman/Joseph replay.
Admission checks the authored axes, ordered inputs, parameters, conditioning
horizons, declared float64 precision and distribution validity. Per-quantity
differences and explicit refusal reasons remain visible; a stored passing flag
does not establish agreement.

The audit retains source/result/program artifacts and live owner identities,
but supplied bytes do not authenticate an observed execution of the current
runner. Slice-local finite-weight normalization and scalar arbitrary-slope
prior-measurement laws have separate compiler and axiom controls, including
expected rejection of false claims. Their scope excludes GNN parsing/execution,
matrix Gaussian conditional-kernel theorems and universal translation
equivalence. Current pair custody, numerical replay, native algebraic evidence
and full-provider execution therefore remain distinct claims.

## HTTP and persistence

Hermes tests use a real loopback HTTP server and exercise response parsing,
timeouts, retries, model-chain advancement, and review calls over sockets.
SQLite tests use temporary on-disk databases, concurrent writers, atomic file
publication, restart recovery, and SHA-256 consistency checks. These boundaries
make provider, compiler, and filesystem drift visible in test results.

## Reproducibility

Use `uv.lock`, `fep-lean setup`, and the documented `fep-lean preflight` command
to reproduce the pinned environment. A complete run produces
`run_manifest.json`, `verification_manifest.json`, `summary.json`, Markdown
reports, deterministic figures, and manuscript projections. These artifacts
become evidence only when the independent receipt validator reconciles their
rosters, digests, and hashes against the live source; no stored `complete` flag
is authoritative by itself.
