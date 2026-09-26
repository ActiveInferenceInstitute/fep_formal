# H2.7: smooth reference-kernel terminal merge

Status: **terminal implementation present; acceptance is source-bound**.
H2.7-R0 is accepted. The maintained owner defines the scalar and Fin4 terminal
theorems. H2.7 acceptance requires a valid
`specs/horizon-2-smooth-stochastic/readiness/terminal-acceptance.json`, including
the native results, diagnostics and three independent reviews below.
An absent or stale receipt leaves H3 closed;
a valid receipt opens only read-only H3.G0 continuous eligibility.

From the repository root:

```bash
uv run python specs/horizon-2-smooth-stochastic/readiness/terminal_acceptance.py \
  validate --project-root .
```

## Outcome

Export one connected theorem on the same scalar Gaussian carrier and a separate
accepted four-coordinate export. The terminal theorem is not a record storing
predecessor conclusions and not a conjunction of unrelated endpoints.

## Dependencies and owner

Solid dependencies: H2.1b, H2.2a, H2.3b, H2.4b, H2.5a, H2.5c, H2.5d,
H2.6a, H2.6b, H2.6c, and accepted H2.7-R0. H2.2b is optional.

- Resource: `compositions/smooth_reference_kernel.lean`.
- Module: `FepSketches.compositions.smooth_reference_kernel`.
- Role: `COMPOSITION`.
- Namespace: `FEPComposed.SmoothReferenceKernel`.

The final direct imports must be exact owners of declarations named in the
terminal proof. A review-only requirement that the separate Fin4 export is
accepted does not justify an otherwise unused import.

## Scalar terminal theorem

One theorem must connect, by exact equalities on one selected model:

- normalized H2.5a transition and H2.6a observation kernels, each proved equal
  to its H2.1 Gaussian-location instance;
- H2.5a native semigroup and invariant law;
- H2.6a native posterior/filter and the H2.7-R0 density-relative
  exact-posterior VFE/KL orientation;
- H2.3 distinct parameter-posterior convergence and bounded-continuous risk;
- H2.1b/H2.2a coordinate-qualified Fisher/duality plus the derived H2.7-R0
  local natural-gradient descent theorem;
- H2.6b finite filter-consuming action, connected to the accepted H1.2/H1.4
  decision orientation without claiming EFE-optimal control;
- H2.6c finite-grid path law; and
- native KL nonincrease under the same transition and invariant reference.

Every bridge is a theorem equality. A field saying two carriers agree is not a
bridge.

## Separate four-coordinate export

The same merge must verify accepted H2.5c and accepted H2.5d declarations
for the exact preregistered `Fin 4` carrier. The separate export must name the
maintained H2.5d blanket-marginal almost-everywhere product-conditional theorem;
otherwise H2.5d remains a review-only prerequisite and must not be an unused
direct import. The scalar vertical theorem must not pretend to be the Fin4
carrier, and H3 must not complete missing H2 algebra, measurability,
conditioning, or invariance.

## Required exclusions

The module and durable handoff enumerate non-transfers: singular-covariance
results, global statistical geometry, nonparametric rates, SDE/Itô existence,
Fokker--Planck or Girsanov results, continuous-path density/entropy production,
unbounded-observable convergence, physical dissipation, empirical adequacy,
and universal FEP.

## Evidence and review

- red terminal and exact-carrier integration tests first;
- warning-free native compilation and explicit axiom audit;
- exact manifest/import/namespace/projection/aggregate closure;
- focused foundation/composition/coverage/relations/novelty/audit tests;
- source-bound predecessor digests;
- deterministic numerical diagnostics clearly separate from proof; and
- three independent approvals: Lean, scientific domain, and skeptical
  carrier/claim review.

## Acceptance contract

| Field | Required evidence |
| --- | --- |
| Entry | Every solid predecessor listed above, including H2.7-R0, is accepted; all H2.0 blocking/upstream rows have been repaired or the terminal claim has been explicitly revised through a reviewed no-go. |
| Red | `tests/test_horizon2_smooth_reference_kernel.py` rejects an absent bridge, a second carrier, stored predecessor conclusions, or a terminal conjunction with no shared values. |
| Green | Warning-free compile, standard-axiom audit, exact owner/import/manifest/projection closure, and one theorem sharing the scalar carrier plus a separately verified Fin4 export. |
| Review | Three independent approvals are mandatory: Lean proof, scientific domain, and skeptical carrier/claim review. |
| Must stay green | Every predecessor focused suite, H1/H2 embedding boundaries, formal coverage/relations/novelty/audit, and readiness validation. |
| Feedback edge | Success opens read-only H3.G0 continuous eligibility; reviewed terminal no-go may instead expose only the already-accepted finite H1.8 branch. |
| Nearest excluded claim | SDE/Fokker--Planck/Girsanov, physical dissipation, empirical adequacy, or universal FEP. |

## No-go

If any solid clause fails or uses a second carrier, ship no positive terminal
theorem. Preserve accepted predecessors and a public blocked-merge theorem or
spec decision naming the exact mismatch. H3 remains closed.
