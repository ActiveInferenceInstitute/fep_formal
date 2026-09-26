# H2.4b: native action-indexed Markov semigroup

Status: **accepted; H2.4a and all three named readiness rows are green**.

## Outcome

Own one narrow native measure-kernel semigroup interface, native KL
nonincrease, and the exact lift of the accepted H1 action-indexed finite
semigroup. The interface adds no generator-existence promise and no parallel
action transition.

## Dependencies and owner

- H2.4a and H2.0 rows `native_kernel_algebra`,
  `native_invariance_kl_dpi`, and `exact_h1_embedded_lift`.
- Resource: `markov_semigroup.lean`.
- Module: `FepSketches.markov_semigroup`.
- Role: `FOUNDATION`.
- Namespace: `FEP.MarkovSemigroup`.
- Direct imports: exact H1.7 and embedding owners plus native kernel
  composition, invariance, and KL data-processing owners found by H2.0.

## Required declarations

- `NativeKernelSemigroup`, parameterized by an already-lawful native kernel
  family, storing only zero and addition/Chapman--Kolmogorov laws;
- `NativeActionIndexedKernelSemigroup` with action-indexed semigroup and sample
  time;
- sampled kernel, invariant-law and reversible predicates;
- native KL nonincrease and invariant-reference corollary;
- exact lift of an H1 certified semigroup; and
- exact lift of H1.7's Boolean hold/refresh action semigroup on
  `FEP.MarkovBlanket.DynamicState Bool Bool Bool Bool`.

The required bridge equations preserve the same action and time and are
literally equal to `FEP.NativeBlanket.embeddedKernel` of the H1 kernel. A
reassociated or merely equinumerous state is rejected.

Zero/addition laws are the narrow algebraic interface fields. Stochasticity,
invariance, reversibility, strictness, and generator existence are theorems or
remain absent.

## TDD and evidence

Red first on the exact owner/import/namespace/roster and both H1 bridge
equalities. Green requires warning-free compile and axiom audit, H1 two-state,
nonreversible three-state/nonzero-current, and exact 16-state action regressions,
composition-orientation tests, and projection parity.

## Acceptance contract

| Field | Required evidence |
| --- | --- |
| Entry | H2.4a and all three named native-kernel readiness rows are green. |
| Red | The H2.4 test fails on the absent owner, exact interface fields, H1 hold/refresh lift, and sampled-kernel equality. |
| Green | Warning-free compile and standard-axiom audit prove invariant-reference KL nonincrease and exact action/time/carrier preservation. |
| Review | Carrier review confirms one native kernel owner and the exact right-associated H1 blanket state; no generator promise appears. |
| Must stay green | H1.7 semigroup/current/strict-KL tests, native embedding tests, formal manifest/projection parity. |
| Feedback edge | Success opens H2.5a and H2.6c; failure blocks H2.5--H2.7. |
| Nearest excluded claim | Generic Markov-generator or SDE semigroup construction. |

## No-go

Failure blocks H2.5--H2.7. Retain the finite H1 interface; do not add an assumed
embedding field, alternate action carrier, or name-only upstream-semigroup
facade.

## Exit evidence

- The required owner is `FepSketches.markov_semigroup`, a foundation under
  `FEP.MarkovSemigroup`, with the exact four direct imports named by H2.0.
- `NativeKernelSemigroup` is parameterized by an already-Markov kernel family
  and stores only zero and ordered addition laws. The action-indexed interface
  stores the certified per-action semigroup and nonnegative sample time.
- Native KL is monotone from an earlier time to an added increment by the
  semigroup addition law, `Measure.comp_assoc`, and kernel DPI. The
  invariant-reference corollary rewrites both reference slices by the proved
  invariant law.
- The finite and action-indexed lifts preserve the exact real time, action,
  right-associated 16-state blanket carrier, and `embeddedKernel` bytes. The
  Boolean endpoints are native identity and the embedded positive refresh;
  they are provably distinct.
- The H1 two-state certified semigroup and Boolean action model instantiate the
  lift. The directed three-state H1 object remains a generator/current witness
  and a must-stay-green regression, not a falsely certified semigroup.
- TDD recorded the absent-owner/interface red. The completed H2.4 test file is
  12/12 green; the focused integration matrix is 119 passed with 16 expected
  opt-in skips; the 55-test presentation sweep passes. Direct compilation is
  warning-free, all 10 public theorems use only standard axioms, and the full
  Lean workspace builds 8,751 jobs.
- Formal projection, coverage, atlas, and dashboard checks are current. The
  maintained corpus now reports 42 modules, 27 foundations, and 1,259 total
  theorem declarations.
- Independent source-only review returned `APPROVE` after time monotonicity,
  three-state scope, comment accuracy, and projection parity were repaired.
