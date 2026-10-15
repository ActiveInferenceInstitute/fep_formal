# Retained pytest evidence inventory

This inventory implements the documentation portion of
[G02 / LEAN-15](https://github.com/ActiveInferenceInstitute/fep_formal/issues/113).
All eight files below are retained. Each has an individual SHA-256 entry in the
historical receipt, so none is eligible for deduplication under the
[specification custody contract](../AGENTS.md). The `pytest-tmp` directory name
does not make a captured, receipt-bound artifact disposable.

This is a custody inventory checked on 2026-10-15. Its bounded documentation and
validator acceptance is recorded below; the historical compiler results retain
their original source epoch.

## Receipt and review consumers

The common evidence root is
`specs/comprehensive-science-improvement/evidence/form2-controls-20261001-r1/`.
Its [author receipt](../comprehensive-science-improvement/evidence/form2-controls-20261001-r1/receipt.json)
has SHA-256
`76bb96549d853ad233a545ab486ef98b64617593461d6f44f84a61a226109352`.
Every table entry is keyed in that receipt's `artifact_sha256` map by
`attempt-01/pytest-tmp/test_relative_support_bridge_a0/` or
`attempt-02/pytest-tmp/test_relative_support_bridge_a0/`, followed by the linked
filename. The attempt command, summary and test-source records also remain
retained in their original directories.

The separate
[FORM-1/2/3 semantic review](../comprehensive-science-improvement/evidence/form-1-3-semantic-review-20261001-r2.json),
SHA-256
`44ac9dd63a76203e8c75194eaf81d68df4479216fd1ee5122a8c3754619080e6`,
binds the author receipt in `form2_control_review.author_receipt`, records all
25 artifact hashes rechecked, and explicitly preserves the failed first
attempt before the successful second attempt. Deleting an artifact would
break that historical receipt's retained evidence set; changing the receipt
would break the independent review's binding.

## Eight retained exceptions

The sizes and digests below were read from the existing files and agree with
the author receipt. Each row is a separate retention decision.

| Attempt and artifact | Bytes | SHA-256 | Retention reason |
| --- | ---: | --- | --- |
| 01 [relative_support_information.command.json](../comprehensive-science-improvement/evidence/form2-controls-20261001-r1/attempt-01/pytest-tmp/test_relative_support_bridge_a0/relative_support_information.command.json) | 442 | `bde68385bf17dcce57c2e6fc28d4b2ca29685d096249cb2f19bd1d97972c7fa7` | Exact invocation record for the failed consumer attempt. |
| 01 [relative_support_information.lean](../comprehensive-science-improvement/evidence/form2-controls-20261001-r1/attempt-01/pytest-tmp/test_relative_support_bridge_a0/relative_support_information.lean) | 29971 | `3eb511e7d99f32c824debf023dad706a182c7488c6540390bc74652e14518951` | Actual failed consumer source; it differs from attempt 02. |
| 01 [relative_support_information.stderr.txt](../comprehensive-science-improvement/evidence/form2-controls-20261001-r1/attempt-01/pytest-tmp/test_relative_support_bridge_a0/relative_support_information.stderr.txt) | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | Recorded empty stderr is part of this attempt's receipt. |
| 01 [relative_support_information.stdout.txt](../comprehensive-science-improvement/evidence/form2-controls-20261001-r1/attempt-01/pytest-tmp/test_relative_support_bridge_a0/relative_support_information.stdout.txt) | 2742 | `9c201b56fbf8f13c6f38952fefd90a8844282641a7a6eea2c496e130868c2468` | Actual compiler diagnostics preserve the failure. |
| 02 [relative_support_information.command.json](../comprehensive-science-improvement/evidence/form2-controls-20261001-r1/attempt-02/pytest-tmp/test_relative_support_bridge_a0/relative_support_information.command.json) | 442 | `d48840bd5a6903c977350407fa2bf711fdedd41440e060e44e2a5c86c5d2eee6` | Distinct invocation record for the corrected consumer. |
| 02 [relative_support_information.lean](../comprehensive-science-improvement/evidence/form2-controls-20261001-r1/attempt-02/pytest-tmp/test_relative_support_bridge_a0/relative_support_information.lean) | 30036 | `0e4ab40d3137decf55494240546a70f458392b4b19aafaf4a7f8c96c538b5af3` | Exact consumer source supporting the successful attempt. |
| 02 [relative_support_information.stderr.txt](../comprehensive-science-improvement/evidence/form2-controls-20261001-r1/attempt-02/pytest-tmp/test_relative_support_bridge_a0/relative_support_information.stderr.txt) | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | Independently receipt-bound empty stream; equal bytes do not authorize removing its path. |
| 02 [relative_support_information.stdout.txt](../comprehensive-science-improvement/evidence/form2-controls-20261001-r1/attempt-02/pytest-tmp/test_relative_support_bridge_a0/relative_support_information.stdout.txt) | 465 | `66193a0b85996ed4b24e8e75607d63f562156502107ec2a710c7da39e4d6f8c0` | Retains the four successful consumer axiom printouts. |

## Preserve failure and success at their original epoch

[Attempt 01's summary](../comprehensive-science-improvement/evidence/form2-controls-20261001-r1/attempt-01/summary.json)
records return code 1. Its
[pytest output](../comprehensive-science-improvement/evidence/form2-controls-20261001-r1/attempt-01/pytest.stdout.txt)
records two passed tests and one failure: the generated consumer lacked
`noncomputable` annotations and had an unsolved goal. Axiom printouts in that
failed output do not establish a successful consumer compilation.

[Attempt 02's summary](../comprehensive-science-improvement/evidence/form2-controls-20261001-r1/attempt-02/summary.json)
records return code 0. The author receipt records seven tests passed in 7.54
seconds and four consumer axiom printouts containing only `propext`,
`Classical.choice` and `Quot.sound`. The Lean files are near copies, with
different bytes and digests: the second adds the required annotations and
repairs the marginal simplification. Both remain necessary to reconstruct the
recorded failure and repair.

These results were recorded on 2026-10-01. Their Lean compiler version is
`4.34.1`, and their Mathlib revision is
`d13f23b723b8a846827a245b89c10fc7d3f11612`. They are not fresh evidence for the
current Lean 4.35.0 source. This inventory preserves both attempts, all receipt
bytes and the separate semantic review unchanged.

## Bounded acceptance and prospective Issue closure

The original issue permits documenting every retained copy. The table supplies
that eight-file mapping, and independent custody review rechecked all 25 author
receipt artifact hashes. The [choices ledger](choices.md#retain-all-eight-receipt-bound-pytest-captures)
records the retention decision. All eight captures, historical receipts and
the separate semantic review retain their original bytes.

Fresh authenticated Python evidence from head `d1d5403` in
[workflow 38799938016](https://github.com/ActiveInferenceInstitute/fep_formal/actions/runs/38799938016)
records all 14 `test_terminal_*` cases in
[test_horizon_acceptance.py](../../tests/test_horizon_acceptance.py) passing.
They include the read-only positive control, actual roster growth, source and
review tampering, input-mtime changes, and jointly rewritten collection/JUnit
records. The positive control uses an explicitly synthetic source/evidence
fixture. These passes establish validator behavior while historical terminal
receipts retain their original acceptance epoch. Historical R0/H3 static-custody
replay remains a separate plane.

The tested PR merge and accepted main
[`f5c39fe`](https://github.com/ActiveInferenceInstitute/fep_formal/commit/f5c39fe6768b4e36296cbf2cd4d8a08ae25bbef2)
have the same reviewed source tree. Its
[exact-main workflow 38807878071](https://github.com/ActiveInferenceInstitute/fep_formal/actions/runs/38807878071)
passed all 21 executed checks, including all 15 distribution cells. The
[accepted checkpoint](../../ISA.md#current-assessment) and package matrix retain
the source-bound evidence. This documentation publication records G02's bounded
acceptance and prospectively closes Issue113 when its PR merges; the historical
scientific results and execution boundaries remain unchanged.

A correct live-source refusal must remain a refusal. This documentation
supplies no permission to weaken a validator, rewrite a frozen receipt or
claim a new native execution.
