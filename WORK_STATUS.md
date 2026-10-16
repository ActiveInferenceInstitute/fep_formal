# Work status — 2026-10-16

This is a restart handoff, not a second backlog or acceptance registry. The
[open TODOs](TODO.md), [package matrix](specs/comprehensive-next-steps/work-packages.json)
and [campaign contracts](specs/comprehensive-next-steps/README.md) remain authoritative.

## Accepted main

Main checkpoint [`4208d589`](https://github.com/ActiveInferenceInstitute/fep_formal/commit/4208d589a00c5eeaed5a36d8760153bad8805ef1)
passed [exact-main run 38839512633](https://github.com/ActiveInferenceInstitute/fep_formal/actions/runs/38839512633):
21 executed checks succeeded, including 15 installed-wheel cells; the alternative
documentation-only lane was intentionally skipped. Later source needs its own acceptance.

## Pushed implementation awaiting complete acceptance

The current L01/L06/P09 implementation is pushed in
[PR182](https://github.com/ActiveInferenceInstitute/fep_formal/pull/182), branch
`improvements/topic-body-imports`, at
[`bedfcab912edcd5dc94e6a979ff1c547bf54ad2d`](https://github.com/ActiveInferenceInstitute/fep_formal/commit/bedfcab912edcd5dc94e6a979ff1c547bf54ad2d)
(tree `2809ecd51fc08feff6468d146f5dc9cbf083411c`).

- L01 / [Issue109](https://github.com/ActiveInferenceInstitute/fep_formal/issues/109): narrow 21 topic import blocks and preserve import meaning in shared projection.
- L06 / [Issue111](https://github.com/ActiveInferenceInstitute/fep_formal/issues/111): native measure entropy/CGF bounds, with explicit integrability, infinite KL and single-source Mathlib-only controls.
- P09 / [Issue125](https://github.com/ActiveInferenceInstitute/fep_formal/issues/125): measured package line floors and adversarial coverage/custody controls; no branch-arc enforcement.

[Run 38930339625](https://github.com/ActiveInferenceInstitute/fep_formal/actions/runs/38930339625)
has a passing [Lean job](https://github.com/ActiveInferenceInstitute/fep_formal/actions/runs/38930339625/job/117073361472):
597 serial passes, five skips and one Python pytest warning; 168 native topics
with zero Lean warnings or proof holes; audit 1,878 resolved declarations and
1,747 evidence entries. All three actual entropy axiom reports were retained
and contain only the standard axioms. This is native evidence, not an all-checks pass.

The real-render job was in progress at the last observation. Python stopped
before tests/Chrome/coverage because the committed shipped-render receipt predates
the regenerated appendix. The manuscript source digest changed (`eca36b81…` to
`4ad49a69…`); the receipt gate must remain intact. All three Issues stay open.

## Restart sequence

1. Read the live PR/run state and exact source identities; reuse the existing run's evidence before considering another execution.
2. Authenticate the fresh real-render artifact, its exact inputs and zero-defect acceptance. Refresh the committed receipt through its existing owner; do not replace receipt hashes by hand.
3. Qualify the successor's complete Python/Chrome membership, P09 coverage controls and all applicable CI checks. Native success alone does not supply these results.
4. Review and merge only the qualified exact PR head, verify the remote merge and exact-main result, then reconcile the three Issue/TODO contracts from actual acceptance.

## Work that remains held

[PR179](https://github.com/ActiveInferenceInstitute/fep_formal/pull/179) remains draft
at `4e5c041087260cbc105ca7852e2dc82c78c5d13d`. Its
[passing hosted run](https://github.com/ActiveInferenceInstitute/fep_formal/actions/runs/38840270358)
does not discharge R01 → C05 → C03 actual production capture and C04 local
installed-runtime/status acceptance. Preserve [PR44](https://github.com/ActiveInferenceInstitute/fep_formal/pull/44)
attribution and [Issue58](https://github.com/ActiveInferenceInstitute/fep_formal/issues/58).

The historical production streams and reviewed controller packet have not been
located. C01/C02 remain open; source-only review supplies no execution approval.

The snapshot has 57 open Issues matching 57 TODO rows and 58 unaccepted package
contracts. This handoff closes none. Preserve scientific/H3/provider boundaries, historical evidence and
the required primary/scratch resource reserves. A restart grants no production
approval and does not waive any capture, runtime, review or acceptance gate.
