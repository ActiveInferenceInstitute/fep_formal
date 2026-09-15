# H2.5d-R0: fixed Fin4 native conditioning repair gate

Status: **accepted; its append-only repair opened maintained H2.5d, which has
subsequently exited**.

Accepted evidence: warning-free Lean 4.34.0 compilation; 9 focused contracts;
an exact 2-abbreviation, 8-definition, 12-theorem public census; standard-only
axiom reports; and independent Lean/probability plus Gaussian graphical-model
review. The source-bound decision is recorded in
[`05d-gaussian-conditioning.json`](../readiness/repairs/05d-gaussian-conditioning.json).

## Outcome

Decide whether the accepted centered H2.5c stationary Gaussian law admits the
exact external--internal conditional factorization given sensory--active
coordinates. For `stationaryLaw (0 : StandardizedState)`, the native regular
conditional distribution of `(external, internal)` given `(sensory, active)`
must equal, almost everywhere under the actual sensory--active marginal, the
product of two scalar Gaussian kernels with variance `1 / 4` and common mean
`(sensory + active) / 4`.

Arbitrary-center translation is a maintained H2.5d obligation, not part of the
fatal pinned-API question tested by R0.

The decisive evidence is an exact native joint-measure reconstruction followed
by Mathlib conditional-kernel uniqueness. A pointwise PDF identity,
Schur-complement calculation, precision-zero field, or Boolean
conditional-independence certificate does not pass.

This gate creates no maintained formal resource. A `go` opens only H2.5d
implementation.

## Entry boundary

Required accepted inputs:

- maintained H2.5c;
- H2.0 `finite_dimensional_matrix_carrier = go`;
- H2.0 `positive_definite_inverse = go`;
- H2.0 `fin4_exact_precision_witness = go`;
- H2.0 `multivariate_gaussian_measure = go`;
- H2.0 `posterior_kernel = go`; and
- historical H2.0
  `gaussian_conditioning_precision = blocking_no_go`.

The historical blocking row is evidence being repaired, not a green
dependency. Do not mutate the accepted H2.0 matrix, receipt, or probe.

## Ownership and paths

- Spike: `../spikes/05d_gaussian_conditioning.lean`.
- Contract test:
  `../../../tests/test_horizon2_gaussian_conditioning_readiness.py`.
- Source-bound repair receipt:
  `../readiness/repairs/05d-gaussian-conditioning.json`.
- Spike namespace: `FEPProbe.H2_5dGaussianConditioning`.
- Maintained H2.5d owner, now eligible:
  `src/fep_lean/formal/gaussian_precision_conditioning.lean`, module
  `FepSketches.gaussian_precision_conditioning`, namespace
  `FEP.GaussianPrecisionConditioning`.

The spike is absent from `FORMAL_MODULES`, the workspace projection, and the
aggregate.

## Fixed carrier and coordinate order

Reuse, without redefining:

- `FEP.Fin4GaussianSemigroup.Axis` and `StandardizedState`;
- `K`, `Sigma`, and `stationaryLaw`;
- the centered law `stationaryLaw (0 : StandardizedState)`;
- coordinate order external, sensory, active, internal;
- `K_external_internal`; and
- `Sigma_external_internal_ne_zero`.

Define only the conditioning interface:

- `Blanket := ℝ × ℝ`, ordered `(sensory, active)`;
- `Endpoints := ℝ × ℝ`, ordered `(external, internal)`;
- `blanketCoordinates`;
- `endpointCoordinates`;
- `partitionCoordinates`;
- `blanketLaw`, as the actual stationary-law marginal;
- `conditionalOffset`;
- `externalConditionalKernel`;
- `internalConditionalKernel`; and
- `endpointConditionalKernel`, as the native product of the two scalar rows.

Private proof-only definitions may include the external and internal residuals
obtained by subtracting `conditionalOffset (blanketCoordinates x)`, their pair,
and the continuous-linear maps required by the Gaussian independence API.

No second axis, precision, covariance, stationary law, or Gaussian carrier is
permitted.

## Exact public spike roster

Public abbreviations:

- `Blanket`;
- `Endpoints`.

Public definitions:

- `blanketCoordinates`;
- `endpointCoordinates`;
- `partitionCoordinates`;
- `blanketLaw`;
- `conditionalOffset`;
- `externalConditionalKernel`;
- `internalConditionalKernel`;
- `endpointConditionalKernel`.

Public theorems:

- `measurable_blanketCoordinates`;
- `measurable_endpointCoordinates`;
- `measurable_partitionCoordinates`;
- `externalConditionalKernel_apply`;
- `internalConditionalKernel_apply`;
- `endpointConditionalKernel_apply`;
- `stationaryPartition_eq_compProd`;
- `endpointCondDistrib_ae_eq_product`;
- `externalCondDistrib_ae_eq`;
- `internalCondDistrib_ae_eq`;
- `external_condIndep_internal_given_blanket`;
- `fixed_precisionZero_covarianceNonzero_condIndep`.

Private helpers may prove Gaussian closure, means, covariances, and map
normalizations. They may not escape the exact namespace census.

The two decisive theorem shapes are:

```lean
theorem stationaryPartition_eq_compProd
    : (stationaryLaw (0 : StandardizedState)).map partitionCoordinates =
        blanketLaw ⊗ₘ endpointConditionalKernel
```

```lean
theorem endpointCondDistrib_ae_eq_product
    : condDistrib endpointCoordinates blanketCoordinates
        (stationaryLaw (0 : StandardizedState)) =ᵐ[blanketLaw]
      endpointConditionalKernel
```

`endpointConditionalKernel_apply` must expose each row as the product of the
two displayed `gaussianReal` laws. The scalar conditional-distribution
theorems must identify the two marginals, and
`external_condIndep_internal_given_blanket` must state Mathlib's native
`CondIndepFun` proposition. The combined boundary theorem must package the
accepted precision zero, actual stationary-law covariance `1 / 24`, and native
conditional independence without claiming a generic implication or converse.

## Expected source route

Freeze imports only after compilation. The bounded source audit expects the
successful tuple to draw directly from H2.5c plus Mathlib's Gaussian-law
independence, multivariate/scalar Gaussian, conditional-distribution, and
conditional-independence owners. `Matrix.SchurComplement`, `Kernel.Posterior`,
and H2.6a are not expected dependencies.

The intended proof ladder is:

1. Rewrite the centered stationary law as the accepted multivariate Gaussian
   and derive exact coordinate means and covariances from `Sigma`.
2. Prove both endpoint residuals have mean zero and variance `1 / 4`, are
   mutually covariance-zero, and have zero covariance with both blanket
   coordinates.
3. Use Mathlib's Gaussian-law covariance-zero independence theorems and native
   product-map equality to obtain the orthogonalized blanket/residual product
   law.
4. Affine-shift the residual product by `conditionalOffset` and prove the
   exact `compProd` reconstruction by measure extensionality.
5. Apply native `condDistrib` uniqueness for the endpoint pair and its scalar
   marginals, then the maintained conditional-independence equivalence.
6. Derive the actual marginal covariance `1 / 24` and combine it with the
   accepted precision zero and native conditional-independence theorem.

## Red-to-green contract

The initial focused test must fail on the absent spike and decisive native
factorization. It must reject:

1. a manifested or projected spike;
2. a new `Axis`, `K`, `Sigma`, `stationaryLaw`, or multivariate Gaussian
   owner;
3. generic arbitrary-axis, arbitrary-block-matrix, or arbitrary-partition
   conditioning;
4. conditioning an H2.5c transition row instead of its stationary law;
5. pointwise equality to `condDistrib` or arbitrary-center scope in R0;
6. a PDF or Schur-complement identity without
   `stationaryPartition_eq_compProd`;
7. a stored conditional kernel, independence flag, certificate, witness,
   `axiom`, `sorry`, `admit`, `opaque`, unsafe declaration, or `True` theorem;
8. a conditional endpoint row that is not the native product of the two
   scalar Gaussian laws;
9. swapped blanket or endpoint coordinate order;
10. an H2.6a mathematical dependency or second posterior owner; and
11. H2.7, H3, causal, dynamic, reversibility, thermodynamic, or continuous-
    path claims.

Green requires all of the following atomically:

1. exact imports frozen from the warning-free successful spike;
2. the exact public declaration census above;
3. measurable coordinate maps in the named order;
4. both conditional variances exactly `1 / 4`;
5. both conditional means exactly `(sensory + active) / 4`;
6. a Markov `endpointConditionalKernel` whose rows are the exact native
   product;
7. exact equality between the mapped stationary joint and
   `blanketLaw ⊗ₘ endpointConditionalKernel`;
8. pair and scalar almost-everywhere equality to Mathlib `condDistrib` under
   the actual `blanketLaw`;
9. the explicit native `CondIndepFun` proposition for external and internal
   coordinates given the blanket;
10. a typed consumer combining precision zero, actual stationary covariance
   `1 / 24`, and the native conditional-independence theorem;
11. warning-free exact-pin compilation;
12. nonempty axiom reports using only `propext`, `Classical.choice`, and
    `Quot.sound`, with no `sorryAx`; and
13. an append-only source-bound repair receipt plus independent review.

The test should separately pin spike-only ownership, exact H2.5c reuse,
coordinate order, Gaussian row parameters, native product construction, native
joint reconstruction, blanket-marginal almost-everywhere scope, native
conditional independence, the precision-zero/nonzero-covariance boundary,
exact public surface, warning-free compilation, standard axioms, and the repair
receipt.

## Receipt policy

Do not modify `readiness/matrix.yaml`, `readiness/acceptance.json`, or
`readiness/probes/08_gaussian_conditioning.lean`. The addendum must record:

```json
{
  "schema_version": 1,
  "gate": "H2.5d-R0",
  "decision": "go | blocking_no_go",
  "decision_scope": "open_H2.5d_implementation_only",
  "historical_boundary": {
    "acceptance_mutated": false,
    "addendum_only": true,
    "matrix_mutated": false,
    "row_id": "gaussian_conditioning_precision",
    "row_status_at_decision": "blocking_no_go"
  }
}
```

The source hash roster binds exactly the three Lean/Lake pin files, frozen H2.0
acceptance/matrix/conditioning probe, accepted
`fin4_gaussian_semigroup.lean`, this slice, the spike, and the focused test.
The receipt separately records imports, declarations, coordinate order,
conditional formulas, joint-factorization orientation, `condDistrib` scope,
compiler output, warnings, axioms, review verdicts, downstream edges, and
reviewed no-go claims.

## Review

Required independent approvals:

- Lean/probability: map orientation, `compProd`, measurability,
  almost-everywhere scope, and conditional-kernel uniqueness;
- Gaussian graphical model: partition order, `1 / 4` variances, conditional
  means, and the precision-versus-covariance interpretation; and
- skeptical claim review: stationary-only scope, no converse, no causal or
  physical blanket promotion, and exact downstream gating.

These approvals do not substitute for H2.7's separate terminal quorum.

## Stop/go

- **Go:** open only maintained H2.5d implementation.
- **No-go:** keep H2.5d, H2.7, and continuous H3 closed while preserving
  accepted H2.5c and all scalar/filter/control/path predecessors.

Even after `go`, do not claim a generic arbitrary-precision equivalence,
pointwise regular conditional distribution, unconditional endpoint
independence, transition-row conditioning, converse, perturbed dependence,
singular conditioning, causal separation, intervention, physical Markov
blanket, reversibility, SDE, Itô, Fokker--Planck, Girsanov, continuous-path,
thermodynamic, empirical, universal-FEP, H2.7, or H3 result.
