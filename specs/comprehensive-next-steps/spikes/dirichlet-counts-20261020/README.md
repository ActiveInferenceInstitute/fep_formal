# Count-level Dirichlet learning and the Stage2 library boundary

This slice retains importing consumers of the existing
[count foundation](../../../../src/fep_formal/formal/empirical_risk.lean).
It adds no topic, manifested resource, probability carrier or maturity change.
Issue95 already permits Stage2 to stop at a recorded library no-go.

## Package contract

| Field | Selected contract |
| --- | --- |
| Outcome | Exercise exact current Stage1 endpoints and record the precise Stage2 continuation seam |
| Depends on | Issue95; the count-level domain/semantic subset of Issue75 only |
| Single owner | Existing empirical-risk foundation; current topic045 and topic121 family projections |
| Stop/go spike | Strict importing count consumers, available pinned-library APIs and zero-shape API refusal |
| Go condition | All count endpoint/row/exchangeability controls compile warning-free with standard trusted axioms |
| No-go action | Do not start or claim the Stage2 Dirichlet measure, logmoment or variational-update clause; retain its missing carrier/integration seam below. No terminal horizon dependency edge is removed |
| Theorem/API target | Positive finite pseudocounts and natural counts; K=2 posterior parameter, all-one Laplace smoothing, sequence exchangeability and normalized learned A/B rows |
| Positive witness | Asymmetric prior (2,3), counts (4,1), predictive 3/5; distinct state/action rows |
| Boundary result | Zero total gives total mass0; negative pseudocount gives negative mass; the normalized Beta API refuses a zero shape |
| Test surface | Three serial imported-consumer cases in test_formal_composition.py and the formal projection checks |
| Evidence plane | Formal/native component checks; source-text library search. No numerical/empirical/provider promotion |
| Human review | Semantic review of the count interpretation and the selected Issue75 prerequisite subset remains separate from compilation and final acceptance |
| Out of scope | General measure-level Dirichlet conjugacy, log-moment/digamma objective, variational posterior, identifiability, learning convergence or scientific acceptance |

## Stage1 endpoint consumers

[CountLevelConsumers.lean](CountLevelConsumers.lean) consumes the actual owned
K=2 Bernoulli posterior parameter and topic121 Laplace error/shrinkage identity.
It also exercises nonconstant exchangeability, positive A rows, state/action B
rows, and the zero-total/negative-pseudocount interpretation boundaries. Count
algebra with totalized division is distinguished from a probability law, which
needs the stated positivity premises. The foundation and its topic endpoints
already exist; this slice does not introduce a second implementation.

## Stage2: available APIs and bounded no-go

The pair is Lean4.35.0 / Mathlib v4.35.0 at
`56a005855ea17e0b0958f73ec801ae140b0a1679`.
[AvailableAPIs.lean](AvailableAPIs.lean) checks actual Complex digamma recurrence
with its pole exclusion, real Beta probability/density normalization for
positive shapes, finitely supported simplex weights, and a density endpoint.
These APIs exist. [RejectZeroShape.lean](RejectZeroShape.lean) intentionally
fails at the positive-shape premise; norm_num reduces that impossible premise
to `False`. It does not establish nonexistence of every zero-shape construction.

A general Dirichlet continuation still needs a measurable K-simplex carrier and
(K−1)-dimensional reference/chart, product-power density with face behavior,
multivariate Beta/Gamma normalizer and probability proof, positive real
log-moment/digamma identification, and an admissible posterior/variational
objective update. The inspected Beta/digamma/simplex APIs do not identify these
objects for us. This is a bounded stop at the named integration seam, not an
impossibility theorem or a claim that Mathlib lacks special functions or all
simplex infrastructure. Stick-breaking or Gamma normalization remains possible
future work with its own measurable-change-of-variables/integrability proofs.

The library probe is scoped to the pinned distribution, Gamma/Beta, digamma and
simplex sources. No unbounded global absence claim or solid horizon dependency
revision follows from those searches. The full Issue75 review remains open.

## Reproduction

After building the pinned workspace:

```bash
uv run pytest tests/test_formal_composition.py::test_dirichlet_count_component_and_library_boundary -q -n 1 --no-cov
```

The two positive consumers require exactly eight and five distinct standard
axiom reports. The adverse case must produce exactly its normalized `False`
shape-premise error, with no warning, admitted proof, missing import or unknown
identifier. The tests use the shared process-group-safe runner and fail closed
when the required toolchain is unavailable. Source-bound test execution,
semantic/prerequisite review, publication and issue closure remain separate.

## Recorded Stage2 continuation boundary

The [binary Beta evidence archive](stage2-binary-beta-external-r3/README.md)
records a partial go for continuous binary-measure feasibility. Its exact
external proof qualified on Lean 4.35.0 / Mathlib `56a005855ea17e0b0958f73ec801ae140b0a1679`
at source epoch `1cc327f4bf41a8ffda85e402bcb800baff1d0929`, with 21
standard-only axiom reports. It derives a likelihood-weighted Beta prior as a
positive finite scalar multiple of the shifted posterior and proves actual
normalized probability. This is historical external evidence, not a new
maintained theorem or current-source compiler receipt.

The broader continuation is a recorded no-go at three integration seams:

- a generic finite-simplex Dirichlet carrier/base measure, support and
  probability normalization;
- endpoint logarithm integrability and the real/complex digamma identification,
  with justified differentiation under integration if that route is used;
- an actual variational objective, admissible family and factorization with a
  proved coordinate optimum or monotone improvement.

The available Beta, Gamma, simplex, digamma and `withDensity` APIs do not supply
these identifications automatically. This is not a claim of library absence or
mathematical impossibility. Any general continuation needs a separate frozen
probe and independent review. The binary proof uses positive-shape Beta
normalization; it supplies no blanket #75/S01 dependency waiver or acceptance.
Accepted Stage1 and its current importing consumers remain unchanged. Issue95
stays open until this scoped record receives exact-source qualification,
independent review and accepted-main publication; its TODO row is retained.
