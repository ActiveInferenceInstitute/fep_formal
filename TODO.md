# fep_lean — canonical backlog

Only open work belongs here. Completed work is represented by passing evidence
in the repository history or an eventual changelog; do not add struck-through
rows or a completed-work archive here.

| ID | Open work | Acceptance probe |
| --- | --- | --- |
| FEP-FULL-155 | Refresh optional external full-mode evidence for the expanded source. Historical 50-topic and one-topic provider reports must remain historical. | Under a separately confirmed credential and spend boundary, a 155-topic Hermes/OpenGauss run completes and `validate_report_receipt(..., require_complete=True, project_root=...)` reports `valid`, `source_bound`, and `claim_ready`, with the exact live roster and no validation errors. |
| FEP-LEAN-UPGRADE | Upgrade the pinned Lean/Mathlib pair when the next stable release lands (`docs/pin_audit.py --check-latest` fails CI at that point). The pin bump itself is mechanical; the work is the native evidence refresh and any body adjustments the new toolchain demands. | After bumping `lean/lean-toolchain`, `lean/lakefile.lean`, and `lean/lake-manifest.json` to the new stable pair, `lake build FepSketches` is warning-free, `uv run fep-lean verify --fail-on-warnings --receipt output/native-verification.json` validates `native_claim_ready` against the live roster, `scripts/audit_formalisms.py` validates with zero errors, and `docs/pin_audit.py --check-latest` passes. |
| FEP-RELEASE-NEXT | Engineer the next release. The version number and DOI are open decisions; the deterministic-evidence refresh for the released bytes is green — the coordinated refresh completed deterministically on 2026-09-12 (recorded in CHANGELOG.md). | `pyproject.toml`, `CITATION.cff`, and `CHANGELOG.md` agree on the version; two `scripts/build_release_bundle.py` runs are byte-identical and `--check` validates claim-ready against the live roster; the release notes state the evidence boundary (catalogue vs native vs provider) and cross-reference the GitHub release and Zenodo version DOI as v1.1.0 did. |
| FEP-SCAFFOLD-PORTABILITY | Make the Q7 runner-scaffold digest interpreter-independent. The interpreter contract branch is recorded (2026-09-11): the Q7 spec README documents CPython 3.14 (the `.python-version` pin) as the only accepted validator of the frozen `runner_ast_sha256`, and the focused pinned-digest test fails loudly on a pin bump or an unaccepted validating interpreter. Q5's runner custody is whole-file sha256 and already interpreter-independent — unaffected. | The precise remainder is the fail-closed half of the contract: `scaffold_digest` must refuse to digest under any interpreter outside the accepted set (an in-module guard naming the accepted CPython 3.14 set), landing with its own coordinated evidence refresh. If multi-interpreter portability is still wanted afterwards, a version-stable canonical serialization lands as a new reviewed scaffold through a coordinated custody re-pin — never a unilateral `expected.json` regeneration. |
| FEP-H27-RESEAL | Re-seal the H2.7 terminal receipt against the post-v1.1.0 source wave. The claim review of the Horizon 3 record (2026-09-12) verified at the live tree that the f335724-sealed H2.7 receipt no longer revalidates: exactly five `current_sources` files drifted post-seal (`latex.py`, `registry.py`, `declarations.py`, `lean_source.py`, `horizon_acceptance.py`), `tests/conftest.py` drifted inside one R0 predecessor map, and `manifest.py` (changed at `0b5d01e`, pre-seal) plus `test_horizon2_gaussian_vfe_readiness.py` (changed at the seal commit itself) unbind the 07-gaussian-vfe-natural-gradient predecessor map. This is a coordinated evidence-custody refresh (per the coordinated-evidence-refresh convention in ISA.md, "Current assessment"; the 2026-09-12 coordinated refresh completed deterministically and is recorded in CHANGELOG.md), not a unilateral regeneration; it gates H3.0 freeze, which must re-adjudicate the Horizon 3 record's open item 1 first. | `uv run python specs/horizon-2-smooth-stochastic/verify_native.py --check` (and the H2.7 receipt's validator) passes at the live tree with `validate_terminal_acceptance` green and the receipt claim-ready against the current owner roster. |
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
