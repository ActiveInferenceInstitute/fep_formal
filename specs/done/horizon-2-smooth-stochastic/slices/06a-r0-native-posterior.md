# H2.6a-R0: native scalar Gaussian posterior gate

Status: **accepted `go`; maintained H2.6a and narrowed one-step H2.6b
subsequently exited**.

## Outcome

Prove that the selected closed-form scalar Gaussian update is an
evidence-almost-everywhere version of Mathlib's native posterior kernel. This
is the only missing mathematical edge before the exact finite-step H2.6a
filter may open. It is not parameter learning, multivariate precision
conditioning, or a continuous-time Kalman--Bucy result.

## Dependencies and historical boundary

- Accepted H2.1a and H2.5a, including
  `ouTransition_comp_gaussian` for exact prediction.
- Pinned native posterior and density owners.
- Historical H2.0 row `native_filter_posterior` remains unchanged and
  receipt-bound as `blocking_no_go`. This gate emits a versioned repair
  addendum rather than recapturing the historical empty-H2-resource receipt.

Accepted spike:
`spikes/06a_native_filter_posterior.lean`.
Source-bound contract test:
`tests/test_horizon2_native_filter_posterior_readiness.py`.
Append-only source-bound decision:
`readiness/repairs/06a-native-filter-posterior.json`.

## Selected model and exact target

Let the H2.5a OU slice evolve a nondegenerate scalar Gaussian prior. Observe
the evolved state through the H2.1 fixed-positive-variance Gaussian location
family. For predicted mean (m^-), predicted variance (P^->0), observation
noise (R>0), and observation (y), derive

\[
S=P^-+R,
\qquad K=\frac{P^-}{S},
\qquad m^+=m^-+K(y-m^-),
\qquad P^+=\frac{P^-R}{S}.
\]

**Copyable LaTeX**
```latex
S=P^-+R,
\qquad K=\frac{P^-}{S},
\qquad m^+=m^-+K(y-m^-),
\qquad P^+=\frac{P^-R}{S}.
```

The decisive theorem must be evidence-almost-everywhere, not pointwise:

```lean
closedFormPosteriorKernel model prior
  =ᵐ[evidenceLaw model prior]
    ProbabilityTheory.posterior
      (observationKernel model)
      (predictionBelief model prior).law
```

The proof ladder is fixed:

1. reuse H2.5a to identify the prediction law exactly;
2. prove the pointwise Gaussian density factorization with the displayed
   (m^+,P^+);
3. lift it to the exact swapped joint-law identity for the closed posterior;
4. apply `ae_eq_posterior_of_compProd_eq`; and
5. prove evidence-density positivity and nonvanishing from (P^->0) and
   (R>0).

Gaussian evidence positivity means positive density everywhere. It never means
positive singleton mass.

## Red-to-green contract

The red test must reject:

- pointwise equality to `ProbabilityTheory.posterior`;
- a stored posterior, gain, evidence, process variance, transition kernel, or
  observation kernel;
- a second OU or Gaussian-location owner;
- positive atomic evidence wording;
- zero observation noise or a totalized zero-denominator update; and
- Kalman--Bucy, nonlinear-filter, SDE, Itô, or parameter-consistency claims.

Green requires a warning-free exact-pin spike, only standard axioms, the
pointwise density identity, joint-measure equality, the evidence-a.e. posterior
theorem, positive evidence density, exact source/test/toolchain hashes, and an
independent probability review. The repair record stores one `go` or
`blocking_no_go` decision and never changes the H2.0 receipt.

## Exit evidence

- The exact-pin spike compiles warning-free and proves all fourteen public
  theorem obligations, including Gaussian density factorization, both
  joint-law identities, evidence marginal identification, evidence-a.e.
  equality to Mathlib's posterior, density positivity, zero singleton mass,
  and normalization.
- Axiom inspection reports only `propext`, `Classical.choice`, and
  `Quot.sound`; no `sorryAx` is present. The final source-bound focused suite
  passes 8 tests.
- Fresh independent probability review approved the scalar carrier, OU and
  posterior orientation, completion-of-square algebra, `withDensity` lift,
  coordinate swap, marginal identification, and density-versus-atom boundary.
- The versioned repair receipt records `go` for
  `open_H2.6a_implementation_only`. The historical H2.0 matrix, its
  `native_filter_posterior = blocking_no_go` row, and its acceptance receipt
  remain byte-preserved evidence of the earlier probe boundary.
- This gate creates no maintained formal owner. It opens only the separately
  reviewed H2.6a implementation and does not open H2.6b, H2.7, or H3.

## Stop/go

- **Go:** open [`06a-gaussian-filter.md`](06a-gaussian-filter.md). Its formal
  owner may then add finite recursion while reusing the gate's proof route.
- **No-go:** keep H2.6a/b and the filter clauses of H2.7 closed. H2.3,
  H2.5b-R0, and H2.6c remain independent.
