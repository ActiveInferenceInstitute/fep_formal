# fep_lean — canonical backlog

Only open work belongs here. Completed work is represented by passing evidence
in the repository history or an eventual changelog; do not add struck-through
rows or a completed-work archive here.

| ID | Open work | Acceptance probe |
| --- | --- | --- |
| FEP-FULL-155 | Refresh optional external full-mode evidence for the expanded source. Historical 50-topic and one-topic provider reports must remain historical. | Under a separately confirmed credential and spend boundary, a 155-topic Hermes/OpenGauss run completes and `validate_report_receipt(..., require_complete=True, project_root=...)` reports `valid`, `source_bound`, and `claim_ready`, with the exact live roster and no validation errors. |
| FEP-EVIDENCE-CURRENT | Refresh deterministic native, declaration/axiom, Python, browser, and publication evidence for the accepted post-v1.1.0 source wave against the settled current owner roster (bridge contract v0.6 with the GNN 3.3.0 route rename re-pin). The predecessor receipts bind `pyproject.toml` and `uv.lock` bytes, so a dependency refresh alone invalidates the recorded Horizon acceptance chain and must be re-pinned together with the evidence refresh. Retained receipts from an older owner manifest or source digest remain historical, never current evidence. | Native validation is `valid`, `source_bound`, and `native_claim_ready`; formal-audit, Python-acceptance, and browser-replay validators return no errors; manuscript/publication drift checks pass; and a deterministic release bundle validates as source-bound and claim-ready against the same final owner roster. |
| FEP-CI-RENDER | Run the publication render and its fail-closed acceptance in CI. CI currently verifies only the committed `docs/render-acceptance.json` receipt because rendering needs the shared-template checkout, XeLaTeX, pandoc, `rsvg-convert`, the mermaid CLI, and the two faces the preamble selects. | A CI job (or a scheduled render lane with the toolchain and fonts installed) runs `scripts/render_publication.py` end-to-end, `scripts/check_render_log.py` accepts the fresh render, and the freshly written `docs/render-acceptance.json` plus `docs/render-fonts.json` validate against the same sources in the same run, so manuscript drift cannot survive between local renders. |
| FEP-LEAN-UPGRADE | Upgrade the pinned Lean/Mathlib pair when the next stable release lands (`docs/pin_audit.py --check-latest` fails CI at that point). The pin bump itself is mechanical; the work is the native evidence refresh and any body adjustments the new toolchain demands. | After bumping `lean/lean-toolchain`, `lean/lakefile.lean`, and `lean/lake-manifest.json` to the new stable pair, `lake build FepSketches` is warning-free, `uv run fep-lean verify --fail-on-warnings --receipt output/native-verification.json` validates `native_claim_ready` against the live roster, `scripts/audit_formalisms.py` validates with zero errors, and `docs/pin_audit.py --check-latest` passes. |
| FEP-RELEASE-NEXT | Engineer the next release. The version number and DOI are open decisions; the deterministic-evidence refresh (`FEP-EVIDENCE-CURRENT`) must be green for the released bytes first. | `pyproject.toml`, `CITATION.cff`, and `CHANGELOG.md` agree on the version; two `scripts/build_release_bundle.py` runs are byte-identical and `--check` validates claim-ready against the live roster; the release notes state the evidence boundary (catalogue vs native vs provider) and cross-reference the GitHub release and Zenodo version DOI as v1.1.0 did. |
| FEP-SCAFFOLD-PORTABILITY | Make the Q7 runner-scaffold digest interpreter-independent. The scaffold freezes `ast.dump` output, which changed between CPython 3.12 and 3.14; the reviewed `expected.json` digest is pinned under 3.14 and the `.python-version` pin added on 2026-09-07 is the interim mitigation, not the fix. Q5's runner custody is whole-file sha256 and already interpreter-independent — unaffected. A version-stable canonical serialization (or an explicit interpreter contract recording the accepted set) requires a new reviewed scaffold and a coordinated custody re-pin — never a unilateral regeneration. | `scaffold_digest(source)` returns the pinned `runner_ast_sha256` under every CPython from 3.10 through 3.14 (or the contract records the accepted interpreter set and `scaffold_digest` rejects any other fail-closed); `tests/test_gnn_continuous_artifact_proof.py` passes under each accepted interpreter; the re-pinned `expected.json` revalidates through the Q7 custody chain. Rough order: canonicalization design → reviewed digest re-pin through the custody lane → CI verification under all accepted interpreters. |
| FEP-H3-SCIENCE | After H2 exits, execute the gated and preregistered [Horizon 3 scientific case study](docs/design/fep-research-program/horizon-3-scientific-case-study.md). | H3.G0 inspects already-accepted H1/H2 source-bound evidence read-only and selects exactly one continuous or finite branch without proving, patching, or hybridizing a carrier; the frozen typed chain, H3.6S synthetic recovery, optional governed H3.6E analysis or no-go/null result, and independent claim review satisfy the H3 exit gate. |

`FEP-FULL-002` and `FEP-PROV-003` remain completed for their exact 2026-08-20
source snapshot; their evidence is recorded in [CHANGELOG.md](CHANGELOG.md),
[HANDOFF.md](HANDOFF.md), and [ISA.md](ISA.md). They do not substitute for
`FEP-FULL-155`. The release-recorded native and declaration/axiom probes remain
evidence for their exact source snapshot. The accepted post-v1.1.0 source wave
invalidated their current-source binding; `FEP-EVIDENCE-CURRENT` owns the next
deterministic refresh. `FEP-H2-SMOOTH` left this backlog on 2026-09-07: H2.7
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
