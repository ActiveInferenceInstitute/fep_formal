# Retained pytest evidence inventory

This inventory implements the documentation portion of
[G02 / LEAN-15](https://github.com/ActiveInferenceInstitute/fep_formal/issues/113).
All eight files below are retained. Each has an individual SHA-256 entry in the
historical receipt, so none is eligible for deduplication under the
[specification custody contract](../AGENTS.md). The `pytest-tmp` directory name
does not make a captured, receipt-bound artifact disposable.

This is a custody inventory checked on 2026-10-15. It adds no compiler run,
scientific acceptance or renewal of the historical source epoch. G02 acceptance
requires source-bound custody controls, independent review and published checks.

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

These are 2026-10-01 Lean 4.34.1 results at Mathlib revision
`d13f23b723b8a846827a245b89c10fc7d3f11612`. They are not fresh evidence for the
current Lean 4.35 source. This inventory preserves both attempts, all receipt
bytes and the separate semantic review unchanged.

## Acceptance still required

The original issue permits documenting every retained copy instead of deleting
one. The table supplies that eight-file mapping, and the linked receipt and
review explain each exception. Closure additionally requires the appropriate
positive and fail-closed controls for the H2 terminal validator, independent
custody review and accepted publication checks. The positive terminal control
in [test_horizon_acceptance.py](../../tests/test_horizon_acceptance.py) uses an
explicitly synthetic source/evidence fixture; passing it does not reaccept a
historical terminal receipt. Historical R0/H3 static-custody replay is a
separate test plane and cannot substitute for terminal-validator controls.

A correct live-source refusal must remain a refusal. This documentation
supplies no permission to weaken a validator, rewrite a frozen receipt or
claim a new native execution. The parent integration pass owns those distinct
controls and the final G02/Issue disposition.
