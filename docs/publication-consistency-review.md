# Publication consistency review

## Compile maturity and scientific scope

The archived fifty-topic manuscript used “aspirational” for broader stochastic
and geometric goals while describing every shipped row as `real`. That wording
mixed two axes: completion of an exact Lean body and the scope of the motivating
scientific concept. It must not be read as proof of unrestricted SDE,
Fokker–Planck, or Riemannian-manifold results.

The current source resolves this ambiguity through separate contracts:

- [Catalog metadata](../config/catalogue_metadata.yaml) owns the sealed roster
  and `mathlib_status` classification.
- [Theorem maturity](../config/theorem_maturity.yaml) owns each row's exact
  primary theorem, supporting statements, assumptions, non-vacuity review,
  acceptance probe, and semantic disposition.
- [The generated audit](theorem-maturity-audit.md) projects that review;
  compilation alone never changes a disposition.
- [The abstract](../manuscript/01_abstract.md),
  [maturity chapter](../manuscript/03c_sorry_maturity.md), and
  [conclusion](../manuscript/06_conclusion.md) distinguish exact theorem scope
  from broader continuous-state, geometric, biological, and empirical claims.
  Mutable totals are generated manuscript variables, not editorial constants.

All rows can consequently have a complete canonical body without all motivating
concepts being completely formalized. A `formalized` disposition also applies
only to the deliberately bounded invariant recorded for that row. Neither that
label nor a warning-free compile receipt proves a universal or empirical FEP.

## Verification and archival boundary

A current native claim requires an independently validated, live-source-bound
receipt from `fep-lean verify --fail-on-warnings`. Catalog generation and the
semantic audit provide source/projection evidence only. Full Hermes/OpenGauss
execution requires its separate validated report.

This review does not reclassify a theorem or assert a fresh native run. It also
does not replace an archived publication: that artifact retains its original
roster, wording, and source epoch. Any revised deposit should render the current
sources after the declared publication gates and identify the new revision.
