# Shared filesystem and JSON helper audit — 2026-10-18

This audit addresses P03 / Issue #118 against source checkpoint
`982bd478e367fc68ba2a4923262ecea1bfc96043`. It covers all authored package Python
modules, with an AST inventory of atomic replacement, temporary-file, SHA-256 and
JSON calls. The original inventory found relevant calls in 45 modules and 73
one-shot digest sites. No historical evidence or frozen scientific input is
rewritten by the consolidation.

## Consolidation

Twenty-five one-shot digest implementations in eight output/bridge modules
now delegate to `output.fsutil.sha256_bytes`. Their original byte-producing
expressions, path checks, canonicalization, ordering and public wrappers remain.
The PDF trailer-ID owner converts its existing mutable zeroed buffer to `bytes`
for the shared helper's declared type; the digest and PDF mutation sequence are
unchanged. Imports already reached the same output facade; fresh-process imports
qualify the resulting order separately.

Changed owners: `output/reporter.py`, `output/manuscript.py`,
`output/render_log.py`, `output/publication_metadata.py`,
`output/release_bundle/_manuscript.py`, `output/release_bundle/_core.py`,
`bridge/custody.py`, and `bridge/operations.py`.

## Retained atomic publication policies

| Owner | Reason for retaining its operation |
| --- | --- |
| `output/fsutil.atomic_write_bytes` | Canonical adjacent temporary file, binary write, fsync, atomic replace and final cleanup owner. |
| `output/evidence.write_native_lean_receipt` | Legacy streamed text JSON, nonfinite policy, platform text newline conversion, adjacent temporary-file mode and interruption cleanup are observable. Shared `write_json` rejects nonfinite values and serializes to binary UTF-8/LF. |
| `verification/formalism_audit.write_formalism_audit_receipt` | Same legacy text/stream/nonfinite distinctions, plus its existing Exception-only cleanup boundary. Changing these requires a separate compatibility decision. |
| `custody/refresh._persist_journal`, `_rewrite_journal` | Ordered journal serialization, PID staging, path/mode/fsync policy and recovery lifecycle. |
| `gauss/client.write_artifact` | Unicode/no-terminal-newline format and coupled database/filesystem publication with rollback. |
| `output/figures._save` | Matplotlib consumes a pathname and manages its own encoder lifecycle. |
| `output/manuscript._stage_bytes`, `_transactional_write_texts` | Named temporary files stage a coordinated multi-file transaction with rollback. |
| `output/browser_capture._install_capture_transaction` | Capture/receipt pair installation and rollback must remain coordinated. |
| `output/rendering._replace_render_tree` | Directory-tree installation and restoration, rather than a single-file write. |
| `output/release_bundle/_manuscript._replace_publication_set` | Coordinated publication-set replacement and rollback. |
| `output/release_bundle/_assemble._write_archive`, `build_release_bundle` | Streamed gzip/USTAR metadata, errors and final replacement only after validation and source guards. |
| `verification/lean_verifier.verify_sketch`, `verification/formalism_audit.run_formalism_audit` | Temporary Lean compiler inputs have a compiler-owned lifecycle; they are not final artifact writers. |

## Retained digest primitives and dependency boundaries

Streaming hash state, composite framing and archive/worker protocols retain their
existing owners. A different byte expression alone is not a reason to duplicate
a one-shot digest: the 25 substitutions preserve that expression explicitly.
The remaining one-shot sites are retained as the following bounded import-layer
or compatibility decisions, rather than claimed universally unsafe to migrate.

| Modules | Retained boundary |
| --- | --- |
| `__init__.py` | Runtime identity captured before importing subpackages; bootstrap independence. |
| `output/fsutil.py` | Canonical shared primitive. |
| `catalogue/schema.py`, `llm/hermes.py`, `gauss/client.py` | Lower-layer owners participate in eager output initialization; avoid introducing catalogue/Hermes/Gauss cycles. `gauss.client._sha256` also accepts text. |
| `gauss/runner.py`, `methods/model.py`, `methods/visualization.py` | Workflow/cache, source/model and renderer/font identities remain lower-layer owned. Moving the primitive is deliberately deferred pending package-initialization review; this is not evidence that every such move is unsafe. |
| `verification/_subprocess.py` | Worker/frame protocol and bootstrap isolation. |
| `verification/horizon_acceptance.py`, `verification/gnn_artifact_proof.py`, `verification/gnn_continuous_artifact_proof.py`, `verification/gnn_julia_artifact_proof.py`, `verification/gnn_artifact_receipt.py` | Typed public wrappers, source-bound extraction and low-level provenance engines retain their dependency boundaries. Source binding alone does not make a primitive permanently exempt. |
| `custody/census.py`, `custody/apply.py`, `custody/refresh.py` | Read-only classification, staged candidate buffers, operation IDs, journal/cache/receipt checks remain custody-layer owned. No eager output-facade dependency is added. |

`sha256_file` returns an empty string for an absent/non-file input. Strict-file
wrappers that raise, contained-file/symlink guards, absent-as-empty **bytes**,
captured-byte identity and ordered composite hashes therefore must not be
replaced by a pathname helper. Existing guards remain before byte hashing.

## JSON compatibility

`bridge.operations.read_object` is the remaining independent duplicate-key and
nonfinite parser. Its duplicate-key and constant messages, pathname-qualified
syntax/recursion errors and object-root `TypeError` are public tested behavior.
It is retained as an explicit compatibility exception to `_jsonutil`; a future
shared adapter must preserve those errors before delegation. Other strict
receipt/custody engines already delegate to `_jsonutil`. Permissive JSON readers,
canonical archive bytes, bounded subprocess/HTTP frame decoders and scaffold
parsers are different contracts, not equivalent strict-parser copies.

## Evidence boundary

Digest equality does not keep an old source-bound receipt current. Changed
owners require fresh source-bound software, native, formal/report/render and
bridge custody evidence where those owners participate. Prior failed runs and
historical receipts remain unchanged and retain their original source epochs.
This document records the implementation/audit boundary; acceptance requires
actual checks and a reviewed final source snapshot.

The [acceptance receipt](shared-helper-acceptance-20261018.json) binds the
reviewed runtime owners, actual software/native/declaration evidence and
Signature-only current-pair refresh. The
[static inventory](spikes/shared-helpers-20261018/source-inventory.json)
records all48 remaining one-shot sites and the retained atomic/JSON call sites.
Clean-head hosted serial, render and distribution qualification remains an
integration prerequisite. Historical bridge proof and production receipts are
not renewed by the source-pair refresh.
