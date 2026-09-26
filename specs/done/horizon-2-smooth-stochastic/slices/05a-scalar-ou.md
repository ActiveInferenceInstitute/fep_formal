# H2.5a: scalar Ornstein--Uhlenbeck transition law

Status: **accepted; H2.1a and H2.4b remain green**.

## Outcome

Construct a scalar mean-reverting Gaussian transition directly as a native
kernel and package it as the H2.4 semigroup. Prove normalization,
Chapman--Kolmogorov, invariant law, moments, and weak convergence. This is a
transition-law theorem, not an SDE solution.

## Dependencies and owner

- H2.1a; H2.4b; H2.0 rows `scalar_gaussian_parameter_measurability`,
  `scalar_gaussian_affine_convolution`, `scalar_gaussian_moments_ext`,
  `native_kernel_algebra`, `weak_characteristic_function`, and
  `weak_bounded_continuous`.
- Resource: `scalar_gaussian_semigroup.lean`.
- Module: `FepSketches.scalar_gaussian_semigroup`.
- Role: `FOUNDATION`.
- Namespace: `FEP.ScalarGaussianSemigroup`.

Direct imports are the H2.1 and H2.4 owners plus exact scalar Gaussian,
kernel-composition, and weak-convergence owners exercised in H2.0.

## Carrier and boundaries

Store raw parameters only: mean-reversion rate \(a>0\), center \(m\), and
diffusion variance rate \(q>0\). Define

\[
m_t(x)=m+e^{-at}(x-m),
\qquad v_t=\frac{q}{2a}\left(1-e^{-2at}\right).
\]

**Copyable LaTeX**
```latex
m_t(x)=m+e^{-at}(x-m),
\qquad v_t=\frac{q}{2a}\left(1-e^{-2at}\right).
```

At \(t=0\), the transition is a Dirac/identity kernel. At \(t>0\), it is a
nondegenerate Gaussian. These are separate theorem-visible branches.
Here \(q\) is the variance rate; in a diffusion-amplitude convention
\(q=\sigma^2\). The formal carrier stores \(q\), not both parameterizations.

## Required declarations

- transition mean/variance and their zero/positive-time boundaries;
- measurable state-dependent transition kernel and Markov instance;
- identity at zero and Chapman--Kolmogorov at addition;
- exact H2.4 semigroup packaging;
- stationary Gaussian law with derived variance \(q/(2a)\);
- invariance, transition mean, and transition variance;
- equality to the corresponding H2.1 Gaussian law at positive time; and
- weak convergence to the invariant law from each fixed state.

## Optional analytic branch

A generator or weak forward identity may be attempted only after H2.0 names an
explicit supported test-function class and actual integral/differentiation
lemmas. Failure is optional and must not introduce `FokkerPlanckSolution`,
`SDE`, or `ItoIntegral` declarations.

## Acceptance contract

| Field | Required evidence |
| --- | --- |
| Entry | H2.1a/H2.4b are accepted and all six named H2.0 rows remain green. |
| Red | `tests/test_horizon2_scalar_gaussian_semigroup.py` fails on the absent zero/positive-time kernel split, CK law, invariant law, and weak limit. |
| Green | Direct compile is warning-free; standard-axiom audit proves normalization, semigroup, invariance, moments, and bounded-continuous weak convergence. |
| Review | Probability review checks variance positivity and the (t=0) Dirac boundary; nomenclature review rejects SDE/Fokker--Planck language. |
| Must stay green | H2.1 Gaussian laws, H2.4 native semigroup, H2.0 scalar/weak probes, and H1 embedding tests. |
| Feedback edge | Success opens H2.5b, H2.6a, and H2.6c; failure leaves H2.4 intact. |
| Nearest excluded claim | Strong/weak SDE solution or continuous-path process construction. |

## Exit evidence

- `FEP.ScalarGaussianSemigroup` stores only positive mean-reversion and
  diffusion-variance-rate parameters plus the center. Its zero-time law is
  exactly Dirac/identity; every positive-time law is exactly the maintained
  H2.1 fixed-variance Gaussian.
- Chapman--Kolmogorov is proved in chronological order, then packaged through
  the accepted H2.4 native semigroup owner. Invariance, moments, full
  `NNReal`-time weak convergence, bounded-continuous expectation convergence,
  and invariant-reference native-KL monotonicity are derived theorems rather
  than certificate fields.
- The direct source compile is warning-free. All fourteen public theorems use
  only standard axioms, the nine slice tests pass, and the integrated
  H2/formal matrix passes 95 tests. The actual default `lake build` target,
  whose glob includes standalone foundations, completes all 8,752 jobs.
  Formal workspace,
  coverage, atlas, and dashboard projections are current at 43 maintained
  modules, 28 foundations, and 1,273 theorem declarations. The exported
  `ouTransition_comp_gaussian` theorem gives H2.6a the exact arbitrary-Gaussian
  prediction seam without duplicating the affine-bind proof.
- A fresh independent scientific review returned `APPROVE` with no critical,
  high, or medium finding. It specifically checked the variance convention,
  positive-time boundary, composition orientation, stationary-law proof,
  full-time weak limit, bounded-observable scope, and KL orientation.

## No-go

If the kernel, semigroup, or invariant-law construction fails, retain H2.4 and
block H2.5b--H2.7. Do not store Chapman--Kolmogorov, invariance, or covariance
as certificate fields.
