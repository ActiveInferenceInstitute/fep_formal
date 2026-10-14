# Cascadia matrix validation, 2026-10-14

This increment adds a bounded, portable ACT model registry and case matrix,
strict companion orchestration in LectureCreate, and modular producer and
mathematical guides. The executable cases reuse real GNN artifacts and
`inferactively-pymdp` 1.0.4 state/policy inference. The new
[proof-obligation guide](matrix-proof-obligations.md) preserves the distinction
between generic Lean bounds and model-instance evidence.

## Observed checks

| Surface | Result |
| --- | --- |
| New ACT matrix tests | 27 passed; branch-inclusive coverage 97.78% across both new runner modules, floor 90% |
| Full ACT owned selection | 798 passed, zero failures/errors/skips; runner duration 326.95 seconds |
| Display regression after mobile correction | 12 passed; no inference-owner change |
| LectureCreate matrix, study, integrity and reference-lecture selections | 52 passed |
| Matrix execution and fresh replay | Four cases, process seeds 0/7, 48 observations per trajectory |
| Installed ACT wheel | Both new modules and packaged template loaded from an external install target; full matrix replay passed |
| Portable archive | 50 files restored byte-for-byte; closed matrix recheck passed |
| Companion with replay | Both model exports reproduced/rechecked by GNN; both FEP worksheets produced; final ACT and live named-tool checks passed |
| Companion without replay | Explicit `numeric_replay_checked: false`; successful integrity-only companion |
| Documentation and source checks | GEO strict repository/test/documentation checks; GNN strict documentation audit; FEP strict links/hygiene; scoped Ruff/mypy passed |

The first flag controls failed because Pydantic boolean literals admitted
numeric aliases. Strict booleans and semantic validation now reject them.
A companion with a removed exporter-recheck log initially passed after its
hashes were resealed. The checker now requires every declared file role.
These red logs remain preserved beside the green follow-ups. A package-name
coverage attempt failed during SciPy collection; the subsequent source-path
coverage command passed without changing the numerical library or threshold.

Desktop and mobile inspection exercised both seeds, both metrics and the
first/last step against actual retained values and elapsed hours. The first
360-pixel layout overflowed by ten pixels because a label margin extended its
scroll area. The corrected display constrains that label's width; final
inspection shows all four curves, finite SVG coordinates and no horizontal
overflow. Seed 7, Brier, step 47 displays 282 hours and the retained values
`4.89e-10`, `2.86e-5`, `2.86e-5`, `0.7788` in the declared case order. These
are display checks on descriptive trajectories, not new population findings.

## Retained ACT identity

The source candidates for this increment are GEO_INFER
`329b3421fc60a93db8553d670fbf706c2a2e0f14`, GNN
`b4a583a5851021612a9a5df94e428f78aa6f76a0` and LectureCreate
`28d5433bc19d192341170ab006fb4c283c907dea`. These identify the bounded source
changes; remote publication and independent acceptance are separate checks.
Gitleaks 8.30.1 found no leaks in the exact changed files and extracted archive.

The full run is `25357e52af914c05910668bd9d6d9457`, attempt
`561e466718ca4220a59f4805cc34c207`, under
`GEO-INFER-ACT/examples/outputs/cascadia_matrix_validation_20261014` in GEO_INFER.
Its base revision is `0c54908e40323f65e433400e7c917bff1ac0f591`; it records
the dirty-source hashes. Both new modules, their test and the final HTML
template match those recorded hashes. The receipt reports
`custody_complete: true` for its inventory capture. That flag is not a global
SSD-closure, immutable-whole-workspace or full-release approval.

| Artifact | SHA-256 |
| --- | --- |
| `summary.json` | `3e2d7c13699beb2a548202f7c6533e7826a0282c11dce5f49ce70a2f0d1eb774` |
| `junit.xml` | `b908daaa8a9c6de85890eb87919250cab00f01461d8965d4c7ce420e1fd96b46` |
| `selection.json` | `e82c3cfc1576a9448d6a9b2aebc16a18382aa4ad4c6645c0e68d585fd964e030` |
| Public `model_matrix_20261014.zip` | `3b0d78324574dbe528e1a50ab50f0928c8b6dc8cb3fc6152af3a3861b7e3dd1d` |

The archive and comparisons are in GEO_INFER's
`GEO-INFER-ACT/examples/cascadia/data/`. The private companion editions stay
in LectureCreate's ignored `output/`. Local transcripts are preserved under
GitVault `Local/task-tmp/cascadia-matrix-direct-20261014`; the independent
review and manual QA belong to `.omo/evidence/cascadia-matrix-publication` in
this checkout. The first matrix/companion editions remain preserved after the
mobile-template correction; the final edition has the `_v2` suffix.

The original GitVault UUID and external Python prefix/base-prefix bindings
were verified before resumed writes. Interrupted commands with missing
session handles were treated as inconclusive and rerun; no replacement
checkout, controller or preview server was created. Earlier failed gates,
native receipts, original environments and unrelated source edits remain
preserved. The [preceding validation record](publication-validation.md)
retains broad-suite failures and hosted-execution limitations separately.

No new Lean statement or native matrix certificate was added. The existing
reference lecture's authored sources and frozen bundle were unchanged.
This publication does not assert calibration, ecological validity, a
population effect or new production-video acceptance.
