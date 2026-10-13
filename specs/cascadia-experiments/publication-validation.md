# Cascadia cross-repository validation, 2026-10-13

This record accompanies the source updates requested for the four main
branches. It records observed checks and their limits; it is not a release
qualification or a certificate for the numerical simulations.

## Source identities

| Repository | Reviewed implementation commit |
| --- | --- |
| fep_formal | `98e260a85124c40496da9d26bd2ff24083518096` |
| GEO_INFER | `0c54908e40323f65e433400e7c917bff1ac0f591` |
| Generalized_Notation_Notation | `eeb0d9c7b5a0f1886b8358b8313402f3622b77f6` |
| LectureCreate | `05e5d3e40375278c4bed2a8748a896292460ad91` |

The FEP commit includes the upstream publication-documentation merge.
The LectureCreate review checkout has the same tree at cherry-picked commit
`8b496b65deab19e3233bb724b16653f67b122d1c`. All 55 changed GEO paths were
compared byte-for-byte with the reviewed checkout. This documentation record
is a subsequent change; these identifiers name the implementation it describes.

Source, environments, outputs, caches and temporary projects were kept on
the mounted GitVault volume. Both resolved Python prefixes were checked:
FEP 3.14.7, GEO 3.12.11, GNN 3.11.15, and the clean LectureCreate animation
profile 3.12.11 with Manim 0.18.1. Original environments and unrelated work
were preserved.

## Checks that passed

| Check | Observed result |
| --- | --- |
| GEO numerical and adjacent regressions | 51 passed; four selected numerical modules 95.35% coverage, floor 90% |
| ACT subsequent full owned runner | 771 passed, zero failures/errors/skips; separate [final recheck receipt](evidence/20261013-act-full-recheck.md) |
| GNN export qualification and consumer compatibility | 20 passed; strict documentation audit passed |
| FEP experiment slice and CI check inventory | 16 passed |
| FEP process watchdog after teardown correction | 121 passed, two platform skips |
| LectureCreate companion and interpreter regressions | 28 focused cases passed |
| LectureCreate release documentation and audit after correction | 19 release-document cases, then 26 clean combined audit/release-document selections passed |
| GEO integration fleet | 45 of 45 selections passed |
| GEO H3 contract migration | Three static checks passed; these are not numerical tests |
| GEO clean-checkout contracts | 45 imports with zero errors/warnings; documentation, test and logging checks passed; 1615 generated signposts current |
| ACT installed wheel | Built with the selected external interpreter; installed template rendered real retained records |
| Committed-file secret scan | Gitleaks 8.30.1 scanned the exact changed files and extracted pair archive: no findings |

The secret scanner first rejected a newly generated high-entropy token.
The broad GEO checkout scan separately reported eight existing SHA-256
values in two October 12 source manifests. Their keys, 64-digit hexadecimal
form and unchanged baseline bytes were checked; no scanner rule was weakened.

The numerical comparison uses actual pymdp inference from GNN-produced agent
and process artifacts. Four pair editions retain seeds 0 and 7 and 48
observations each. The portable archive contains each closed manifest and
its inputs, trajectories, policy terms and observation-time scores.
Reproduce the archive using GEO's `run_model_pair.py --check EDITION --replay`;
use `plot_model_pairs.py --html --check` for separate display freshness.

The actual HTML was inspected at desktop width 1280 and mobile width 390.
Seed 7, Brier, step 26 showed elapsed time 156 hours and scores
0.9513, 0.8876, 0.8876 and 1.2613 in the declared edition order. Seed 0,
entropy, step 47 showed 282 hours and 0.0007, 0.0607, 0.0607 and 1.6613
nats. All four curves and input identities were present, with no horizontal
overflow. These are recorded simulation values, not population estimates.

## Failures retained and their follow-up

| Broad attempt | Result and disposition |
| --- | --- |
| FEP nonserial full suite | 2856 passed, one failed, 13 skipped, 563 deselected; coverage 91.48%. The held-guard teardown waited before closing its broker channel. The isolated failure reproduced; reversing that order preserved assertions and deadlines and passed both cases and the full watchdog module. The original full attempt remains failed. |
| ACT full owned runner | 763 passed and eight CLI startup timeouts under unchanged 60-second bounds, out of 771 selected. The subsequent full design module passed all 19 cases. This focused recheck does not promote the failed full receipt. |
| LectureCreate clean full suite | 1632 passed, one failed, one skipped; coverage 94.21%. The release-document assertion excluded only internal `.venv` paths and rejected the selected external interpreter. Documentation and the exact portable-command assertion were corrected together; the clean 26-case follow-up passed. The original full attempt remains failed. |
| GEO unit fleet | 40 of 45 selections passed. ACT/AGENT failed process-census inspection, DATA had missing DuckDB spatial-extension and header-deadline failures, PLACE exceeded an optional-import child deadline, and TEST exceeded a Hypothesis deadline. These failures are retained separately from the green integration fleet. |
| GEO performance fleet | Four of six selections passed; two process-census inspection failures remain. |
| FEP newest-stable pin audit | Maintained Lean/Mathlib 4.34.1 differs from upstream 4.35.0; no local pin drift was found across 601 audited files. No pin upgrade or gate exception was made. |

Local command transcripts are retained under GitVault's
`Local/task-tmp/cascadia-real-gnn-20261013`; the manual QA and independent
review records are in `.omo/evidence/cascadia-main-publication` in the FEP
checkout. Failed receipts, earlier native evidence, environments and review
checkouts are preserved. A full-suite pass is not asserted from narrower fixes.

The subsequent ACT run used the earlier full attempt's explicit 1800-second
budget and passed all 771 cases in 340.15 seconds. Its earlier failures remain
historical failures. The runner reports `custody_complete: false`; the green
test selection does not establish complete-workspace custody or promote the
other broad gates to green. The final recheck record binds the source commit,
run/attempt identifiers and retained result hashes.

## Mathematical and presentation scope

The retained diagnostic native receipt establishes exactly its six generic
Lean statements and requires two false-statement controls to fail. Its
current input check passed. It does not prove a floating-point implementation
refines those statements or certify any mismatched model instance. See
[the diagnostic bounds](README.md#recorded-state-score-bounds) and
[agent/process proof obligations](model-mismatch.md).

No result establishes ecological validity, population effects or held-out
calibration. The existing reference lecture remains unchanged; no new
production video was rendered in this publication increment.
