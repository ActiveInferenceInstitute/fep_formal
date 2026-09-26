# H2.5b-R0: dynamic transition-covariance gate

Status: **accepted `go`; maintained H2.5b and H2.5c subsequently exited**.

## Outcome

Decide whether the actual symmetric-precision linear Gaussian transition can
derive its time-dependent covariance law from raw precision data. This gate is
not the H2.5b implementation and creates no maintained formal module. It either
opens H2.5b with a compiled proof route or records a reviewed no-go that leaves
the accepted scalar lanes intact.

## Dependencies and historical boundary

- Accepted H2.4b and H2.5a.
- Green H2.0 rows `finite_dimensional_matrix_carrier`,
  `positive_definite_inverse`, `matrix_exponential_semigroup`,
  `multivariate_gaussian_measure`, and
  `multivariate_gaussian_state_kernel`.
- Historical H2.0 row `transition_covariance_psd` remains unchanged and
  receipt-bound as `blocking_no_go`. This gate writes a versioned addendum; it
  never rewrites the H2.0 acceptance receipt or pretends its diagonal surrogate
  proved the dynamic result.

Prospective spike:
`spikes/05b_transition_covariance.lean`.
Prospective contract test:
`tests/test_horizon2_transition_covariance_readiness.py`.
Prospective source-bound decision:
`readiness/repairs/05b-transition-covariance.json`.

## Exact mathematical target

For a finite index `Axis`, raw symmetric positive-definite precision (P),
derived covariance (Sigma=P^{-1}), and
(E_t=\exp(-tP)), define only in the spike

\[
Q_t=\Sigma-E_t\Sigma E_t^{\mathsf T}.
\]

**Copyable LaTeX**
```latex
Q_t=\Sigma-E_t\Sigma E_t^{\mathsf T}.
```

The gate must prove from the raw assumptions:

- (Q_0=0);
- (Q_t\succeq0) for every (t\ge0);
- (Q_t\succ0) for every (t>0);
- covariance composition
  (Q_{s+t}=E_tQ_sE_t^{\mathsf T}+Q_t), in the same chronological order as
  H2.5a and H2.4b; and
- no proof step relies on a stored PSD/PD/covariance/Markov certificate.

The preferred route uses symmetry/positive definiteness of (P), commutation
of its exponential with (P^{-1}), and a positive functional-calculus or
explicit squared-norm representation. A new general spectral library is not a
goal.

## Red-to-green contract

The red test must reject:

- the existing arbitrary nonnegative diagonal PSD witness as a repair;
- a carrier field named `transitionCovariancePosSemidef`,
  `transitionCovariancePosDef`, or equivalent;
- a proof only for the preregistered `Fin 4` numeric witness;
- a numerical eigenvalue diagnostic in place of a theorem; and
- any SDE, Itô, Fokker--Planck, Brownian-path, or generator substitution.

Green requires a warning-free spike at the exact Lean/Mathlib pin, explicit
axiom output with only standard axioms, exact source/import/toolchain hashes,
the four target propositions above, and independent linear-algebra review.
The decision record stores `go` or `blocking_no_go`, the spike/test hashes,
compiler identity, declaration roster, warnings, axioms, and reviewed no-go
edges. It does not mutate `readiness/acceptance.json`.

## Stop/go

- **Go:** open [`05b-linear-gaussian.md`](05b-linear-gaussian.md), importing
  only the source-true owners used by the successful proof.
- **No-go:** keep H2.5b/c/d, H2.7, and continuous H3 closed. H2.3 and the
  accepted scalar H2.6 lanes remain eligible.

## Exit evidence

- The bounded spike is generic over an arbitrary finite `Axis`. It derives
  covariance as the inverse of a raw positive-definite precision matrix and
  defines the matrix-exponential evolution and transition covariance without a
  certificate-bearing structure.
- Pinned Mathlib spectral decomposition and unitary conjugation prove
  `Q_0 = 0`, positive semidefiniteness for every nonnegative time, positive
  definiteness for positive time, and chronological covariance addition with
  the later/right evolution transporting the earlier/left covariance.
- Direct Lean 4.34.0 compilation is warning-free. All four public theorems use
  only standard axioms; the exact `Fin 4` consumer instantiates the generic
  result without using its preregistered numeric eigenvalue proofs.
- The source-bound append-only repair receipt records `go` while leaving the
  historical H2.0 `transition_covariance_psd` row and acceptance receipt
  unchanged. The authoritative focused suite passes all six tests.
- Fresh independent linear-algebra review returned `APPROVE`; refactor-clean,
  code review, and choice audit found no blocker. This gate opens only H2.5b
  implementation, not H2.5c/d, H2.7, or continuous H3.
