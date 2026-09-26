# H2.5d: Gaussian conditioning and precision

Status: **accepted; historical H2.0 `gaussian_conditioning_precision` remains
blocking no-go and is repaired only by the source-bound R0 plus this maintained
owner**.

## Outcome

Promote the accepted centered native conditioning proof to every stationary
center of the exact H2.5c Fin4 Gaussian law. The external and internal
conditional rows have variance `1 / 4` and means

- `center external + ((sensory - center sensory) +
  (active - center active)) / 4`; and
- `center internal + ((sensory - center sensory) +
  (active - center active)) / 4`.

The means coincide only for the centered witness. The maintained theorem must
reconstruct the actual blanket/endpoints joint, identify Mathlib's native
conditional distribution blanket-marginal almost everywhere, and prove native
external--internal conditional independence given sensory--active.

Add one exact diagnostic endpoint law with precision `[[4, 1], [1, 4]]`,
derived covariance `[[4 / 15, -1 / 15], [-1 / 15, 4 / 15]]`, actual coordinate
covariance `-1 / 15`, and native coordinate non-independence. This is a fixed
bivariate nonvacuity witness, not a perturbed Fin4 stationary model or a
generic converse.

## Dependencies and owner

- Accepted H2.5c plus accepted
  [`H2.5d-R0`](05d-r0-gaussian-conditioning.md).
- Historical H2.0 `gaussian_conditioning_precision = blocking_no_go` remains
  immutable evidence repaired only by the R0 addendum; it is not a green
  dependency.
- Resource: `gaussian_precision_conditioning.lean`.
- Module: `FepSketches.gaussian_precision_conditioning`.
- Role: `FOUNDATION`.
- Namespace: `FEP.GaussianPrecisionConditioning`.
- Direct imports, exactly and in order:
  1. `FepSketches.fin4_gaussian_semigroup`;
  2. `Mathlib.LinearAlgebra.Matrix.Notation`;
  3. `Mathlib.Probability.Distributions.Gaussian.HasGaussianLaw.Independence`;
  4. `Mathlib.Probability.Independence.Conditional`.

Do not import the non-maintained spike, H2.6a, `Kernel.Posterior`,
`Matrix.SchurComplement`, an aggregate, or a future H2.7 owner.

## Fixed carriers and ownership

Reuse H2.5c's `Axis`, `StandardizedState`, `K`, `Sigma`, and `stationaryLaw`
without aliases or wrappers.

Public abbreviations, exactly:

- `Blanket := ℝ × ℝ`, ordered `(sensory, active)`;
- `Endpoints := ℝ × ℝ`, ordered `(external, internal)`; and
- `PerturbedEndpoints := EuclideanSpace ℝ (Fin 2)`, ordered
  `0 = external`, `1 = internal`.

Public definitions, exactly:

- `blanketCoordinates`;
- `endpointCoordinates`;
- `partitionCoordinates`;
- `blanketLaw`;
- `conditionalOffset`;
- `externalConditionalMean`;
- `internalConditionalMean`;
- `externalConditionalKernel`;
- `internalConditionalKernel`;
- `endpointConditionalKernel`;
- `perturbedExternal`;
- `perturbedInternal`;
- `perturbedEndpointPrecision`;
- `perturbedEndpointCovariance`; and
- `perturbedEndpointLaw`.

`perturbedEndpointCovariance` must be definitionally
`perturbedEndpointPrecision⁻¹`; the explicit covariance matrix is a theorem,
not a second stored parameter.

Public named instances, exactly:

- `blanketLaw_isProbabilityMeasure`;
- `externalConditionalKernel_isMarkovKernel`;
- `internalConditionalKernel_isMarkovKernel`;
- `endpointConditionalKernel_isMarkovKernel`; and
- `perturbedEndpointLaw_isProbabilityMeasure`.

Residuals, continuous-linear maps, Gaussian-family facts, `MemLp` facts,
covariance expansions, shifts, and matrix symmetry helpers remain private.

## Exact public theorem roster

1. `measurable_blanketCoordinates`;
2. `measurable_endpointCoordinates`;
3. `measurable_partitionCoordinates`;
4. `externalConditionalKernel_apply`;
5. `internalConditionalKernel_apply`;
6. `endpointConditionalKernel_apply`;
7. `externalConditionalKernel_mean`;
8. `externalConditionalKernel_variance`;
9. `internalConditionalKernel_mean`;
10. `internalConditionalKernel_variance`;
11. `stationaryPartition_eq_compProd`;
12. `endpointCondDistrib_ae_eq_product`;
13. `externalCondDistrib_ae_eq`;
14. `internalCondDistrib_ae_eq`;
15. `external_condIndep_internal_given_blanket`;
16. `stationary_external_internal_covariance`;
17. `stationary_external_internal_covariance_ne_zero`;
18. `precisionZero_covarianceNonzero_condIndep`;
19. `perturbedEndpointPrecision_posDef`;
20. `perturbedEndpointCovariance_eq_entries`;
21. `perturbedEndpointCovariance_posDef`;
22. `perturbedEndpointPrecision_external_internal`;
23. `perturbedEndpointCovariance_external_internal`;
24. `perturbedEndpoint_external_internal_covariance`; and
25. `perturbedEndpoint_external_not_indep_internal`.

The decisive arbitrary-center theorem shapes are:

```lean
theorem stationaryPartition_eq_compProd (center : StandardizedState) :
    (stationaryLaw center).map partitionCoordinates =
      blanketLaw center ⊗ₘ endpointConditionalKernel center
```

```lean
theorem endpointCondDistrib_ae_eq_product (center : StandardizedState) :
    condDistrib endpointCoordinates blanketCoordinates (stationaryLaw center)
      =ᵐ[blanketLaw center] endpointConditionalKernel center
```

The scalar conditional-distribution theorems use the same
`blanketLaw center` almost-everywhere scope. The conditional-independence
theorem is native `CondIndepFun`, not a stored flag. The combined theorem
packages, for every center, `K external internal = 0`, actual stationary-law
covariance `1 / 24`, its nonzero consequence, and native conditional
independence. It is not quantified over arbitrary matrices or partitions.

## Perturbation witness

Define only the raw precision

```lean
!![4, 1; 1, 4]
```

and derive its inverse. Prove positive definiteness, the exact inverse entries,
and covariance positive definiteness. Define the centered native
`multivariateGaussian` from that derived covariance. Then prove

```lean
cov[perturbedExternal, perturbedInternal; perturbedEndpointLaw] = -1 / 15
```

and refute native `IndepFun` by combining
`IndepFun.covariance_eq_zero` with the Gaussian coordinate `MemLp` facts. A
matrix-only contradiction or Boolean certificate does not pass; the public
`PerturbedEndpoints` order and coordinate maps are the exact bridge.

## TDD and integration contract

Create `tests/test_horizon2_gaussian_precision_conditioning.py`. It must first
fail on the absent owner, then pin:

1. exact source path, four imports, namespace, and no `FEPProbe` residue;
2. reuse of H2.5c with no local `Axis`, `StandardizedState`, `K`, `Sigma`,
   `stationaryLaw`, or second Fin4 owner;
3. the exact 3-abbreviation, 15-definition, 5-instance, 25-theorem public
   environment census, including mutation rejection for hidden declaration
   forms;
4. typed arbitrary-center consumers for both distinct means, both variances,
   joint reconstruction, pair/scalar `condDistrib`, and `CondIndepFun`;
5. a centered specialization recovering common mean `(sensory + active) / 4`;
6. actual stationary covariance `1 / 24` and the combined precision/covariance/
   conditional-independence theorem;
7. exact Fin-2 order, all precision/covariance entries, derived inverse,
   positive definiteness, actual covariance `-1 / 15`, and native negated
   `IndepFun`;
8. warning-free canonical-source compilation and one nonvacuous standard-axiom
   report for each public theorem; and
9. preservation of the accepted H2.5c and H2.5d-R0 source hashes and readiness
   validation.

After source review, add exactly one manifest row immediately after H2.5c:

```python
FormalModule(
    resource="gaussian_precision_conditioning.lean",
    lean_module="FepSketches.gaussian_precision_conditioning",
    role=FormalModuleRole.FOUNDATION,
    declaration_namespace="FEP.GaussianPrecisionConditioning",
)
```

Generate exactly one byte-identical projection at
`lean/FepSketches/gaussian_precision_conditioning.lean`, update the foundation
theorem-owner count to 25, and regenerate formal coverage projections. This
foundation must **not** enter the composition-only `composed.lean` aggregate.
Do not create H2.7 or mark H2.7/H3 open during H2.5d integration.

## Forbidden substitutions and claims

Reject:

- center-zero-only maintained results or one shared arbitrary-center endpoint
  mean;
- pointwise equality to a regular conditional distribution;
- PDF, density, Schur-complement, or matrix algebra replacing native
  `compProd` and conditional-kernel uniqueness;
- posterior/H2.6a ownership or transition-row conditioning;
- a stored Boolean, certificate, conclusion field, axiom, `sorry`, `admit`,
  `opaque`, unsafe declaration, or `True` theorem;
- independently reconstructed scalar joints instead of deriving marginals from
  the endpoint-pair owner;
- a second named Fin4 axis, precision, covariance, stationary law, or global
  perturbed Fin4 model;
- generic precision-zero equivalence, necessity, converse, arbitrary
  matrix/partition, singular conditioning, or unconditional independence of
  the actual stationary endpoints;
- causal separation, intervention, physical Markov blanket, reversibility,
  SDE/Itô, Fokker--Planck, Girsanov, thermodynamic, empirical, universal-FEP,
  H2.7, or H3 claims; and
- mutation of the historical matrix, acceptance receipt, conditioning probe,
  R0 spike, or R0 repair receipt. The sole historical exception is the exact
  test-lifecycle correction already recorded by
  `readiness/repairs/05d-gaussian-conditioning-lifecycle.json`: after R0 opened
  maintained H2.5d, its owner-absence guard became pre-receipt-only and the R0
  receipt's bound test digest followed that one non-scientific correction.
  The provenance record retains both test hashes and forbids another in-place
  repair mutation.

## Stop/go

- **Go:** accept H2.5d and open only the H2.7 terminal merge gate.
- **No-go:** preserve accepted H2.5c/R0 evidence and keep H2.7 plus continuous
  H3 closed.

Failure of either the arbitrary-center native `compProd`/conditional-
distribution/`CondIndepFun` chain or the actual perturbation-law covariance-to-
nonindependence chain is fatal. No narrower algebraic theorem substitutes.

## Exit evidence

- Canonical source and byte-identical projection hash:
  `be51dc0c06c28ee50331b561bd21df00b03215d2f397caf49a98100f83e8ec7b`.
- Exact maintained owner: one foundation module in
  `FEP.GaussianPrecisionConditioning`, excluded from the composition-only
  aggregate; 3 public abbreviations, 15 definitions, 5 named instances, and 25
  theorems.
- Warning-free canonical and projected-module compilation; exact namespace,
  typed boundary, native-instance, and standard-axiom consumers; focused
  maintained plus R0 contracts green.
- Two independent final reviews returned `APPROVE`. The append-only lifecycle
  provenance record binds the original and corrected R0 test hashes without
  changing the R0 spike, H2.0 matrix, acceptance receipt, conditioning probe,
  or scientific decision.
- Exit opens only H2.7. It does not establish a generic precision theorem,
  transition conditioning, causal/physical blanket, reversibility, H2.7
  terminal theorem, or H3 result.
