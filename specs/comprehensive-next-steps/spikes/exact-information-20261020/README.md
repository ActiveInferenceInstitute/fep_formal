# Exact finite information and endpoint consequences

This slice exercises additions in the existing
[variational foundation](../../../../src/fep_lean/formal/variational_duality.lean)
and [core composition owner](../../../../src/fep_lean/formal/compositions/core.lean).
The 168-topic roster, 72 formal resources and semantic dispositions stay fixed.
Its authenticated [review fixture](../../../../tests/fixtures/exact_information_review_20261020.json)
reverses only the exact new owner blocks and seven relation/two capability
changes before the older historical seals run. Historical fixture bytes remain
unchanged. Source review, actual compilation, native/audit receipts and final
publication acceptance remain separate records.

## Fair Boolean Hamming rate-distortion

The existing normalized finite law owns the fair Boolean source. An actual
symmetric joint attains `log 2 - binEntropy D` for `0 ≤ D ≤ 1/2`, and the derived
converse bounds every joint with that source and distortion budget. Larger
budgets attain zero. Units are natural-log nats. The relative-support comparison
allows zero reproduction atoms.

The finite positive multiplier and exact dual-value theorem are restricted to
`0 < D < 1/2`. At zero budget the joint is unique; the one-sided multiplier grows
without bound even though Lean's totalized logarithm gives a finite value at
zero. Half-budget minimizers are nonunique, negative budgets are infeasible,
and an unfair deterministic source violates the fair-source formula. This does
not establish general finite- or continuous-alphabet strong duality.

- [Interior, negative-budget and unfair-source consumers](fair-boolean-consumer.lean).
- [Refusal of a zero-budget interior multiplier](reject-fair-boolean-zero-multiplier.lean).

## Finite Helmholtz characterization

On one finite probability carrier and positive temperature, the actual physical
functional is `F(T) + T * KL(q || p_T)`, where `F(T) = -T log Z(T)`. The Gibbs law
is the unique minimizer and the derivative of that log-partition free energy
is the negative Gibbs entropy. The two-level Boolean example combines the
identity, minimum, uniqueness, derivative and a strictly worse uniform law.

- [One-carrier positive consumer](helmholtz-positive-consumer.lean).
- [Actual totalized zero-temperature countermodel](helmholtz-zero-countermodel.lean).
- [Zero-temperature API refusal](reject-zero-temperature.lean) and
  [negative-temperature API refusal](reject-negative-temperature.lean).

The negative-temperature refusal tests the positive-temperature API premise;
it does not assert that every derivative formula is false at negative values.
The `013 → 002` relation remains conceptual: physical free energy has an energy
shift and temperature-scaled finite KL, while topic002 uses native extended VFE.

## Substantive endpoint consequences

Six existing formal edges now consume endpoint theorems instead of relying
only on unfolded definitions or a generic Mathlib identity:

| Edge | Derived consequence | Explicit boundary |
| --- | --- | --- |
| 004 → 038 | Bernoulli tangent self-metric nonnegativity | `0 < p < 1` |
| 011 → 026 | Nonnegative negative-log prior complexity | probability mass `0 < p ≤ 1` |
| 022 → 027 | Predictive child marginal | stated native measurable/kernel hypotheses |
| 032 → 043 | Actual quadratic-gradient iteration convergence | `0 < 2*a*eta < 2` |
| 034 → 017 | Filter joint reconstruction | stated native hypotheses; no pointwise posterior-version claim |
| 039 → 005 | Additive partition-energy conservation | actual finite disjoint cover; no dynamics claim |

[Endpoint consumers](endpoint-positive-consumer.lean),
[nonzero native Boolean kernels](native-nonzero-consumer.lean) and
[boundary countermodels](endpoint-countermodels.lean) exercise those hypotheses.
[An endpoint Fisher call](reject-fisher-endpoint.lean) and
[a zero-step convergence call](reject-zero-step.lean) must be rejected.
The graph retains 24 formal, 119 pairing and seven conceptual edges.

## Reproduction

After building the pinned Lean workspace, run the actual importing consumers:

```bash
uv run pytest tests/test_formal_composition.py::test_exact_information_imported_consumers_and_boundary_controls -q -n 1 --no-cov
```

Every positive result must compile without warnings or admitted proofs and
report only the standard trusted axioms. Each refusal must produce its one
intended `False` premise failure, with no missing/unknown module or declaration.
The [tests](../../../../tests/test_formal_composition.py) preserve those distinct
contracts. Compilation never promotes a semantic disposition or supplies a
production/Hermes scientific result.
