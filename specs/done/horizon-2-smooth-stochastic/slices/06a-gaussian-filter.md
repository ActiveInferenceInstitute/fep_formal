# H2.6a: exact scalar Gaussian filter

Status: **accepted; H2.6b subsequently exited. The historical H2.0
native-posterior row remains `blocking_no_go`; the accepted H2.6a-R0 repair
and this maintained owner provide the replacement evidence**.

## Outcome

Construct one discrete-time scalar prediction/update step whose transition is
exactly H2.5a's OU kernel and whose observation law is exactly H2.1a's Gaussian
law. Prove the native posterior and its closed-form mean/variance agree.

## Dependencies and owner

- Accepted H2.1a and H2.5a, plus the required
  [H2.6a-R0](06a-r0-native-posterior.md) repair.
- Resource: `compositions/gaussian_filter.lean`.
- Module: `FepSketches.compositions.gaussian_filter`.
- Role: `COMPOSITION`.
- Namespace: `FEPComposed.GaussianFilter`.

## Required declarations

- one scalar latent/observation model with distinct, dimensionally named
  process and observation variances;
- prediction law equal to H2.5a evolution via
  `ouTransition_comp_gaussian`;
- observation kernel equal to H2.1a law;
- positive evidence under nondegenerate parameters;
- an evidence-almost-everywhere equality between the closed Gaussian update
  and Mathlib's native posterior kernel;
- exact Gaussian posterior mean and variance;
- normalization and a finite recursion step; and
- an explicit degenerate/zero-evidence boundary rather than a totalized update.

No continuous-time Kalman--Bucy equation is claimed.

## Acceptance contract

| Field | Required evidence |
| --- | --- |
| Entry | H2.1a/H2.5a are accepted, H2.6a-R0 repairs blocking row `native_filter_posterior` on the selected model, and the maintained H2.6a owner has passed its exit evidence. |
| Red | `tests/test_horizon2_gaussian_filter.py` rejects a second transition/observation owner, a stored posterior, or closed-form algebra disconnected from the native posterior. |
| Green | Warning-free compile and standard-axiom audit prove positive evidence density, evidence-a.e. native posterior equality, exact Gaussian parameters, normalization, and one recursion step. |
| Review | Probability review checks source/reference orientation, evidence positivity, variance domains, and the degenerate boundary. |
| Must stay green | H2.1a/H2.5a, H2.0 native-posterior blocker regression, existing measure-Bayes tests. |
| Feedback edge | Success opens H2.6b and contributes the filtering clause to H2.7. |
| Nearest excluded claim | Kalman--Bucy filtering or arbitrary nonlinear filtering. |

## No-go

If the closed form is not proved evidence-almost-everywhere equal to the native
posterior, retain the native posterior construction but block the closed-form
and downstream control clauses. Pointwise posterior equality, positive
singleton evidence, or a locally defined second transition/observation law is
rejected.

## Exit evidence

- The maintained owner reuses the exact H2.5a OU prediction and H2.1a Gaussian
  observation law. Completion-square, joint-law, and marginal identities prove
  the closed update equals Mathlib's native posterior evidence almost
  everywhere.
- Evidence density is positive everywhere while singleton evidence mass is
  zero. The update normalizes; zero-noise and totalized zero-denominator cases
  remain excluded.
- `filterRecursion` consumes `List ℝ` chronologically under one fixed-duration
  model: the empty list returns the prior and the head update precedes the
  tail.
- Direct compile is warning-free, all 16 public theorems use only standard
  axioms, and manifest/projection/aggregate/declaration ratchets are current.
  Fresh independent probability review returned `APPROVE`.
