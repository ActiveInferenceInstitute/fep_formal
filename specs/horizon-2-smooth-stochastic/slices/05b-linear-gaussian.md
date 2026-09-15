# H2.5b: symmetric-precision linear Gaussian semigroup

Status: **accepted; H2.5c subsequently exited. The historical H2.0 covariance
row remains `blocking_no_go`; the accepted H2.5b-R0 repair and this maintained
owner provide the replacement evidence**.

## Outcome

Generalize only the algebra and native kernel construction required by the
exact four-coordinate export. Use a finite index, symmetric positive-definite
precision, its derived inverse covariance, and a symmetric-precision linear Gaussian
transition family induced by that symmetric precision. Genericity is an
implementation tool, not an acceptance claim.

## Dependencies and owner

- Accepted H2.5a and H2.4b; green H2.0 rows `finite_dimensional_matrix_carrier`,
  `positive_definite_inverse`, `matrix_exponential_semigroup`,
  `multivariate_gaussian_measure`, and `multivariate_gaussian_state_kernel`;
  plus the required [H2.5b-R0](05b-r0-transition-covariance.md) repair of
  blocking row `transition_covariance_psd`.
- Resource: `linear_gaussian_semigroup.lean`.
- Module: `FepSketches.linear_gaussian_semigroup`.
- Role: `FOUNDATION`.
- Namespace: `FEP.LinearGaussianSemigroup`.

## Required declarations

- a raw symmetric positive-definite precision matrix on a named finite index;
- covariance defined from the inverse, not stored independently;
- left/right inverse identities and positive definiteness of covariance;
- matrix exponential composition and commutation facts actually needed by the
  transition;
- derived transition mean and covariance;
- zero-time and positive-time covariance boundaries;
- measurable native multivariate Gaussian transition and Markov instance;
- Chapman--Kolmogorov and H2.4 semigroup packaging;
- invariant multivariate Gaussian and weak convergence; and
- an exact `Fin 1` specialization equal to H2.5a after explicit parameter
  identification.

H2.5c separately proves that the normalized all-ones eigenmode of the fixed
four-coordinate precision has eigenvalue `2` and that the projected transition
equals the H2.5a scalar OU with center carried by that mode, rate `2`, and
diffusion variance rate `2`. No unnamed “same shape” specialization is
accepted.

Symmetry, covariance positivity, kernel measurability, invariance, and
convergence are theorem obligations. A structure containing those conclusions
as fields is rejected.

## TDD and evidence

Red first on derived-covariance ownership, measurable kernel, semigroup, and
scalar-specialization meaning. Green requires warning-free compile and axiom
audit plus deterministic algebra diagnostics explicitly labeled non-proof.

## Acceptance contract

| Field | Required evidence |
| --- | --- |
| Entry | H2.5a/H2.4b are accepted and `transition_covariance_psd` has a reviewed red-to-green repair on the actual time-dependent covariance. |
| Red | `tests/test_horizon2_linear_gaussian_semigroup.py` rejects a measure-valued function, stored PSD/Markov fields, and an unnamed scalar specialization. |
| Green | Warning-free compile derives covariance from precision, proves dynamic PSD, constructs a Markov kernel, CK/invariance, and exact `Fin 1` equality. |
| Review | Linear-algebra and probability reviewers inspect matrix orientation, covariance formula, measurability, and zero-time degeneracy. |
| Must stay green | H2.5a/H2.4b, all green Fin4 readiness probes, and the blocking-row regression. |
| Feedback edge | Success opens H2.5c; failure keeps H2.5c/d, H2.7, and continuous H3 closed. |
| Nearest excluded claim | Arbitrary Hurwitz/Lyapunov or general multivariate OU theory. |

## No-go

Failure blocks H2.5c/d, H2.7, and continuous H3 eligibility. Do not replace an
unproved multivariate kernel with a measure-valued function or a stored Markov
certificate. Invariance is proved; detailed balance and a native reversibility
theorem are not part of H2.5b and must not be inferred from symmetric
precision alone at this acceptance boundary.

## Exit evidence

- The maintained owner stores only raw precision, its positive-definiteness
  proof, and the center; covariance, dynamic PSD/positive-time PD, kernel
  normalization, Chapman--Kolmogorov, invariance, moments, and weak limits are
  derived.
- Direct Lean 4.34.0 compilation is warning-free. All 25 public theorem axiom
  reports are parsed non-vacuously and contain only `propext`,
  `Classical.choice`, and `Quot.sound`.
- The exact `Fin 1` transported kernel equals H2.5a with diffusion variance
  rate two. The source, manifest, workspace projection, and declaration roster
  have one byte-current owner.
- The R0 audit was hardened for Lean's unquoted axiom output without changing
  the historical H2.0 matrix or acceptance receipt.
- Fresh independent linear-algebra/probability review returned `APPROVE` with
  no critical, high, or medium finding.
