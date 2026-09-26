# H2.2b: optional Mathlib manifold packaging

Status: **optional; closed pending a proof-compression usefulness test**.

## Outcome

Bundle the already-proved H2.2a scalar chart into selected Mathlib Riemannian
and covariant-derivative interfaces only if doing so eliminates duplicated
premises and shortens downstream proofs. It must not strengthen the accepted
scientific claim.

## Dependencies and owner

- H2.2a and the explicitly optional H2.0 rows
  `riemannian_vector_space`, `covariant_derivative_api`, `torsion_api`,
  `metric_compatibility_api`, and `manifold_bundle_packaging`.
- Same resource and namespace as H2.2a.
- Direct imports must be exact owners among Mathlib Riemannian and
  covariant-derivative modules actually named in public proofs.

## Acceptance

- the bundled metric is definitionally or theorem-equal to H2.1's coordinate
  metric;
- one selected covariant derivative is shown metric-compatible and
  torsion-free on the explicit chart;
- no project-local duplicate of Mathlib's bundle hierarchy appears;
- no new solid DAG edge depends exclusively on this optional bundle; and
- H2.2a remains usable without importing the bundle declarations.

## Acceptance contract

| Field | Required evidence |
| --- | --- |
| Entry | H2.2a is accepted and a new red usefulness test justifies reopening the five H2.0 optional rows. |
| Green | The same H2.2 owner compiles warning-free, removes downstream premises, and stays theorem-equal to the coordinate metric. |
| Review | Refactor review demonstrates a net reduction in owned structure; domain review confirms no stronger claim. |
| Must stay green | H2.2a compiles without optional imports; no solid DAG edge depends on this package. |
| Feedback edge | Success is optional polish only; no-go leaves the vertical spine unchanged. |
| Nearest excluded claim | Global Riemannian connection, curvature, or completeness. |

## No-go

If packaging creates more structure than it removes, record
`optional_no_go`, omit the declarations, and continue with H2.2a. Do not leave
an empty compatibility facade or aspirational import.
