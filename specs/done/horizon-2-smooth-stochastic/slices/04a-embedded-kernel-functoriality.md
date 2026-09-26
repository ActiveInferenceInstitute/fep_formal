# H2.4a: embedded-kernel functoriality

Status: **accepted after H2.0**.

## Outcome

Extend the existing `FEP.NativeBlanket` embedding owner with the smallest
identity and composition preservation theorems needed to lift H1 semigroups.
This slice creates no new formal resource or manifest entry.

## Dependencies and owner

- H2.0 rows `exact_h1_embedded_lift` and `native_kernel_algebra`.
- Existing owner: `formal/native_blanket.lean`.
- Existing finite-kernel and native-kernel carriers are unchanged.

## Required declarations

- `embeddedKernel` of the finite identity kernel equals native `Kernel.id`;
- `embeddedKernel` preserves the exact finite composition orientation used by
  H1.7; and
- predictive/evolved embedded-law equality if H2.4b needs it and no existing
  theorem already owns it.

All state types and finite `Fintype`/measurability instances remain explicit.
The proof must use the live `embeddedKernel`; no adapter or second embedding is
accepted.

## TDD and evidence

Red first on exact public theorem names and composition direction. Green
requires warning-free native compile, identity/noncommutative composition
regressions, axiom audit, and all existing native-blanket tests.

## Acceptance contract

| Field | Required evidence |
| --- | --- |
| Entry | H2.0 `exact_h1_embedded_lift` and `native_kernel_algebra` remain green. |
| Red | `tests/test_horizon2_markov_semigroup.py` first rejects missing identity/composition laws and the wrong composition orientation. |
| Green | The existing `native_blanket.lean` owner compiles warning-free; exact theorems use the live embedding and pass standard-axiom audit. |
| Review | Owner/refactor review rejects a second embedding or a proof stored as a structure field. |
| Must stay green | All native-blanket, H1.7 action-semigroup, projection, and readiness tests. |
| Feedback edge | Success opens H2.4b; failure blocks H2.4b through H2.7. |
| Nearest excluded claim | An assumed or merely distributionally equivalent embedding. |

## No-go

If exact preservation cannot be proved, block H2.4b through H2.7. Do not make
the desired equality a field of the native semigroup.

## Exit evidence

- Exact TDD first failed on the absent direct composition import and the two
  missing laws. The final owner imports `Kernel.Composition.Comp` directly and
  adds only `embeddedKernel_identity` and `embeddedKernel_comp`.
- The identity theorem is extensional on native singleton masses. Composition
  reuses `embeddedPredictive_eq_comp`, fixing `earlier` then `later` on both
  finite and native sides. A Boolean `not`/constant-true regression proves the
  reverse order has a different mass.
- Direct compile is warning-free and both axiom probes report only `propext`,
  `Classical.choice`, and `Quot.sound`. Six slice tests, 52 focused embedding/
  readiness tests, 113 wider formal tests with 16 expected skips, and all
  8,750 Lake jobs pass.
- No new resource or manifest row exists. Canonical/workspace bytes, coverage,
  atlas, and dashboard projections are current. Independent preflight found no
  mathematical or architectural blocker.
