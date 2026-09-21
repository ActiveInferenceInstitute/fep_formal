# fep_lean — canonical backlog

Only open work belongs here. Completed work is represented by passing evidence
in the repository history or an eventual changelog; do not add struck-through
rows or a completed-work archive here.

| ID | Open work | Acceptance probe |
| --- | --- | --- |
| FEP-FULL-155 | Refresh optional external full-mode evidence for the expanded source. Historical 50-topic and one-topic provider reports must remain historical. | Under a separately confirmed credential and spend boundary, a 155-topic Hermes/OpenGauss run completes and `validate_report_receipt(..., require_complete=True, project_root=...)` reports `valid`, `source_bound`, and `claim_ready`, with the exact live roster and no validation errors. |
| FEP-RELEASE-NEXT | Engineer the next release. The version number and DOI are open decisions. Done since the 2026-09-15 re-anchor (SCOPE-2026-09-15.md N-4): the native receipt now records the v4.34.0 tree (lean_toolchain v4.34.0, mathlib_tag v4.34.0, Mathlib rev `5ed29652`, 155/155 claim-ready — note output/ is gitignored, so release engineering still re-runs the sweep on release bytes), and the H2.7 terminal-receipt re-seal is complete (`69400a1` refreshed the validator-source + native/supplement/review/diagnostics bindings; the H2.7 completion landed as `0c22c76`/`48b8d22`). Remaining: the version/DOI decision, bundle determinism, and re-running the native sweep on the released bytes at the new pin. | `pyproject.toml`, `CITATION.cff`, and `CHANGELOG.md` agree on the version; two `scripts/build_release_bundle.py` runs are byte-identical and `--check` validates claim-ready against the live roster; the release notes state the evidence boundary (catalogue vs native vs provider) and cross-reference the GitHub release and Zenodo version DOI as v1.1.0 did. |
| FEP-SCAFFOLD-PORTABILITY | Make the Q7 runner-scaffold digest interpreter-independent. The fail-closed interpreter contract is recorded (2026-09-15): the Q7 spec README documents CPython 3.14 (the `.python-version` pin) as the only accepted validator of the frozen `runner_ast_sha256`, and an in-module guard refuses `scaffold_digest` before parsing under any interpreter outside the accepted set, raising a `ContinuousArtifactError` naming the accepted set and the running interpreter; the focused pinned-digest test pins the guard and the digest reproduction, and the pinned digest itself is unchanged (no receipt re-seal). Q5's runner custody is whole-file sha256 and already interpreter-independent — unaffected. | Remaining (optional): multi-interpreter portability, if still wanted, lands as a version-stable canonical serialization through a new reviewed scaffold and a coordinated custody re-pin — never a unilateral `expected.json` regeneration. Until then, `uv run pytest tests/ -q -k "scaffold" -x` proves the contract: a non-accepted interpreter is refused with the clear error before parsing, and the pinned `runner_ast_sha256` reproduces under CPython 3.14. |
| FEP-H27-RESEAL | H3.0-gated adjudication only (rebound 2026-09-15): the H2.7 terminal receipt was re-sealed against the live tree per the coordinated evidence-custody refresh convention (`167e57b`, `88ffd01`) — the receipt's `current_sources` entry for `src/fep_lean/verification/horizon_acceptance.py` (post-`88ffd01` validator edits at `5fc0246`/`49c99c7`), the `native_evidence` and heavy-probe-supplement source-map entries for `tests/test_formalism_audit.py` (fixture change at `24f570a`), all three review source maps, and the recomputed diagnostics artifact; predecessor receipts, the `07-gaussian-vfe-natural-gradient` R0 successor custody, and the `PREDECESSORS` constant verified live with no drift. `validate_terminal_acceptance` is green at the re-sealed receipt (digest `f4dbbdba56f81cc859a0fcca0196e63a7fdab5a1fa41a4bdd87c7f74ca5e6cfb`) and `tests/test_horizon_acceptance.py` passes 38/38. Known consequence, intentionally not rebound in this row: the H3 spike's terminal-acceptance pin (`specs/h3-case-study`) still records the pre-rebind receipt digest — that re-pin belongs to the H3.0 adjudication. The re-seal is a coordinated evidence-custody refresh (per the coordinated-evidence-refresh convention in ISA.md, "Current assessment"), never a unilateral regeneration; it gates H3.0 freeze, which must re-adjudicate the Horizon 3 record's open item 1 first. (The row's earlier probe cell cited `specs/horizon-2-smooth-stochastic/verify_native.py`, a script that does not exist; corrected to the real validator below.) | `uv run python -c "from pathlib import Path; from fep_lean.verification.horizon_acceptance import validate_terminal_acceptance; validate_terminal_acceptance(Path('.'))"` passes at the live tree (receipt claim-ready against the current owner roster and validator sources), and the 07-gaussian-vfe-natural-gradient R0 successor custody digests still match. |
| FEP-H3-SCIENCE | After H2 exits, execute the gated and preregistered [Horizon 3 scientific case study](docs/design/fep-research-program/horizon-3-scientific-case-study.md). | H3.G0 inspects already-accepted H1/H2 source-bound evidence read-only and selects exactly one continuous or finite branch without proving, patching, or hybridizing a carrier; the frozen typed chain, H3.6S synthetic recovery, optional governed H3.6E analysis or no-go/null result, and independent claim review satisfy the H3 exit gate. |

`FEP-FULL-002` and `FEP-PROV-003` remain completed for their exact 2026-08-20
source snapshot; their evidence is recorded in [CHANGELOG.md](CHANGELOG.md),
[HANDOFF.md](HANDOFF.md), and [ISA.md](ISA.md). They do not substitute for
`FEP-FULL-155`. The release-recorded native and declaration/axiom probes remain
evidence for their exact source snapshot. The accepted post-v1.1.0 source
wave invalidated their current-source binding; the deterministic refresh
completed on 2026-09-12 and is recorded in [CHANGELOG.md](CHANGELOG.md).
`FEP-H2-SMOOTH` left this backlog on 2026-09-07: H2.7
and its R0 proof gate are accepted with terminal evidence in the
[Horizon 2 spec](specs/horizon-2-smooth-stochastic/README.md), and the
remaining H3 work lives in `FEP-H3-SCIENCE`. Completed engineering tasks
belong to repository history, not this open-only backlog.

## Closure rule

An item leaves this backlog only when its acceptance probe passes in the current
checkout, the evidence is retained in a test/report/documentation change where
appropriate, and the result is recorded in the repository's changelog or
release notes. Until then, the row remains open even if a partial local probe
looks promising.

Cleared 0 completed items on 2026-09-09 — all 7 rows independently verified against the tree and left open (one rewritten to its precise remainder); per-item verification evidence in SCOPE-2026-09-09.md §Cleared-Item-Evidence.
Cleared 0 completed items on 2026-09-15 — all 6 open rows re-verified against
`24f570a`; FEP-LEAN-UPGRADE rewritten to its changelog residual (engineering
done, CHANGELOG entry missing), FEP-H27-RESEAL's stale-evidence claim corrected
to the single surviving validator-source drift with a real probe, and
FEP-RELEASE-NEXT re-anchored to the v4.34.0 pin; per-row evidence in
SCOPE-2026-09-15.md §Cleared-Item-Evidence.
Cleared 1 completed item on 2026-09-16 — FEP-LEAN-UPGRADE: the acceptance
probe passes in this checkout. The 2026-09-15 toolchain program is recorded
in [CHANGELOG.md](CHANGELOG.md)'s `## 1.2.0 — 2026-09-17` section (that
entry landed at `0f5394b`; the former Unreleased section was folded there
by release commit `7886e3f4`; this close extended it with post-entry
bridge re-pins #8–#10 `2b51c3d`/`1e4d634`/`26955f3`), and
`docs/pin_audit.py --check-latest` is
green live on 2026-09-16 (223 files, no drift; newest stable
Lean/Mathlib pair v4.34.0 at mathlib `5ed2965256430c3649e86755f9576b54eca72435`
— the script's first run hit a transient GitHub 403 rate limit and passed on
retry). 5 open rows remain.
