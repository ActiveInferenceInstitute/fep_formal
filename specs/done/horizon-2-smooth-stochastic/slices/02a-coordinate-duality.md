# H2.2a: required local coordinate duality

Status: **accepted; H2.1 accepted**.

## Outcome

Own the minimum smooth-information-geometry result needed by the terminal
theorem: the H2.1 Fisher metric and one local exponential/mixture duality
identity on an explicit scalar chart. Coordinate tensor equations are the
required result; Mathlib manifold bundling is not a hidden prerequisite.

## Dependencies and owner

- H2.1b and H2.0 rows `coordinate_duality` and
  `matrix_valued_frechet_derivative`.
- Resource: `smooth_information_geometry.lean`.
- Module: `FepSketches.smooth_information_geometry`.
- Role: `FOUNDATION`.
- Namespace: `FEP.SmoothInformationGeometry`.
- Direct project import: `FepSketches.gaussian_information_geometry`.
- Exact Mathlib imports: `Mathlib.Analysis.Calculus.Deriv.Mul` and
  `Mathlib.Analysis.Calculus.FDeriv.Pi`.

## Required declarations

- natural- and mean-coordinate metric components derived from H2.1;
- coordinate pullback equality;
- one same-coordinate flat duality product rule with both metric pairings and
  all derivative premises visible;
- coordinate flatness for the explicit affine paths actually constructed;
- local KL/Bregman canonical-divergence equality; and
- a duplicated-coordinate rank-deficiency countermodel showing why positivity
  cannot be inferred for a noninjective parameterization.

The slice reuses Mathlib calculus. Its duplicated-coordinate map has a bundled
continuous-linear Fréchet derivative; the mapped mean appears in the pullback
metric itself. It defines no parallel manifold, tangent, connection, or
curvature hierarchy.

## TDD and evidence

Red first on exact declaration/import ownership, metric derivation, and the
rank-deficient boundary. Green requires warning-free compile and axiom audit,
plus a domain review of coordinate meaning.

## Acceptance contract

| Field | Required evidence |
| --- | --- |
| Entry | H2.1b and readiness rows `coordinate_duality` and `matrix_valued_frechet_derivative` are green. |
| Red | `tests/test_horizon2_smooth_information_geometry.py` fails on the absent owner, exact metric derivation, local duality, and rank-deficiency countermodel. |
| Green | Warning-free direct compile and standard-axiom audit prove only the explicit chart equations and local affine paths. |
| Review | Domain review checks coordinate meaning; refactor review confirms no parallel tangent/connection/manifold hierarchy. |
| Must stay green | H2.1 coordinate/KL tests, H2.0 local-calculus probes, manifest/projection/import parity. |
| Feedback edge | Success supplies the required geometry edge to H2.7; H2.2b remains optional. |
| Nearest excluded claim | Arbitrary statistical manifold or global dual-flat geometry. |

## Exit evidence

- The exact owner/import/declaration tracer first failed on the absent source;
  projection parity then failed until the new owner was generated.
- Direct Lean compilation exits zero with no output. All sixteen public theorem
  axiom probes report only `propext`, `Classical.choice`, and `Quot.sound`.
- The six slice tests pass. The integrated H2.1/H2.2, owner, foundation,
  presentation, atlas, and dashboard matrix passes 95 tests. `lake build`
  completes all 8,750 jobs.
- The accepted countermodel proves that the actual Fréchet derivative of
  `(theta0, theta1) -> theta0 + theta1` annihilates the nonzero tangent
  `(1, -1)`, so its Fisher pullback is not positive definite.
- Independent review accepted only the explicit constant-metric scalar
  identity. H2.2b remains optional and supplies no accepted theorem.

## No-go

If local coordinate duality cannot be proved without a second geometry
library, retain H2.1b, mark H2.2a `blocking_no_go`, and revise the H2.7 geometry
clause before proceeding. Do not relabel a definition as a duality theorem.

## Excluded claims

No global mixture chart, geodesic completeness, curvature classification,
arbitrary statistical manifold, or physical geometry.
