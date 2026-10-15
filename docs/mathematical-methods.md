# Mathematical methods and the OpenAI mathematics context

Version 1.6.0 makes the catalogue's mathematical location inspectable.
The portable `fep_lean.methods` interface joins canonical topic contracts and
authored relations with an explicit interpretive taxonomy. The extended
[manuscript supplement](../manuscript/08b_mathematical_positioning_supplement.md)
develops the mathematics behind that join. The
[source review](../specs/openai-math-methods/REVIEW.md) records what was inspected
in the pinned [OpenAI mathematics corpus](https://github.com/openai/math/tree/adc7f1241b42e322a6451854ab7e4b4c146bf78a).

That upstream is a collection of research manuscripts and formalization work.
Its useful pattern here is the result family: carrier, hypotheses, principal
claim, companion results, and explicit formalization scope. Shared words such
as free energy, Gaussian, geometry or pressure do not establish a transfer.
The selected comparisons are research affinities with stated differences;
they import no research code or proof authority into this package.

## Locate a result through its contract

| Question | Inspect | Mathematical implication |
| --- | --- | --- |
| What object is the theorem about? | Carrier, codomain, normalization and support | A finite vector, native measure, parameter chart and path law require different transfer arguments. |
| What is actually proved? | Reviewed invariant and qualified declarations | The exact proposition determines scope; a title or import does not. |
| What conditions do the work? | Assumption review and non-vacuity | Positivity, absolute continuity, identifiability, regularity and coercivity cannot be silently removed. |
| How does this relate to another result? | Edge kind and qualified witnesses | Derivation, checked pairing, conceptual association and capability blocker express different relations. |
| What evidence is available? | Origin and evidence boundary | A model projection, numerical probe and native compilation receipt support different claims. |

The taxonomy overlaps: a Bayesian kernel can belong to probability, measure
theory and statistics; Fisher geometry connects probability, differential
geometry and optimization. The domain incidence is a family summary. Every
topic labels its domains as inherited family context and retains its exact
review contract. A union of family features does not certify every member as
a theorem in every listed domain.

## Portable API and CLI

The default reads generated YAML resources and canonical Lean resources in the
installed distribution. It does not require a checkout:

```python
from fep_lean.methods import (
    build_mathematical_positioning,
    inspect_topic,
    positioning_neighbors,
    evaluate_boundary_probes,
    analyze_topic,
    inspect_theorem,
    cross_corpus_embedding,
)

model = build_mathematical_positioning()
topic = inspect_topic(model, "fep-001")
neighbors = positioning_neighbors(model, "core-information-geometry", limit=5)
probes = evaluate_boundary_probes()
analysis = analyze_topic(model, "fep-001")
statement = inspect_theorem(model, topic["primary_theorem_qualified"])
embedding = cross_corpus_embedding(model)
```

```bash
fep-lean methods inspect --topic fep-001
fep-lean methods inspect --family core-information-geometry
fep-lean methods neighbors core-information-geometry --limit 5
fep-lean methods probe
fep-lean methods analyze fep-001
fep-lean methods theorem fep_fep001.FEP001.fep001_variationalUpperBound_eq_iff
fep-lean methods embedding
fep-lean methods export --output-root ./mathematical-methods
fep-lean methods check --output-root ./mathematical-methods
```

Select current canonical checkout inputs explicitly:

```bash
uv run fep-lean --project-root . methods inspect --topic fep-001
uv run fep-lean --project-root . methods export --output-root docs/mathematical-positioning
uv run fep-lean --project-root . methods check --output-root docs/mathematical-positioning
uv run python specs/openai-math-methods/generate_package_methods.py --check
```

`check` is a non-mutating exact-byte comparison. An installed model describes
its installed resource set; a checkout model describes the selected live
owners. Source hashes identify that projection's inputs and do not establish
continuous custody, native compilation or a current scientific study.
The resource generator copies the maintained metadata, semantic review,
relations and taxonomy byte-identically. It does not author those contracts.

Family neighbors use binary domain features and an explicit Jaccard
score. The representation is an editorial search aid with equal feature
weights. It is neither a learned embedding nor a proof dependency, metric on
the underlying stochastic models, categorical equivalence or scientific
similarity claim.

## Reusable finite variational methods

The development checkout's four public helpers evaluate arbitrary finite laws and potentials without
loading the positioning model or invoking a compiler:

```python
import math
from fep_lean.methods import (
    finite_expectation,
    log_partition,
    exponential_tilt,
    gibbs_duality_diagnostics,
)

reference = (0.5, 0.5, 0.0)
potential = (0.0, math.log(3.0), 7.0)
optimizer = exponential_tilt(reference, potential)  # approximately (0.25, 0.75, 0)
value = log_partition(reference, potential)  # approximately log(2)
expected = finite_expectation(reference, potential)
report = gibbs_duality_diagnostics(reference, reference, potential)
```

```bash
fep-lean methods gibbs \
  --candidate '[0.5, 0.5, 0.0]' \
  --reference '[0.5, 0.5, 0.0]' \
  --potential '[0.0, 1.0986122886681098, 7.0]'
```

The CLI returns the usual JSON envelope with `source_origin: numerical-input`.
It accepts no proof or scientific disposition flag. Candidate input is required;
malformed JSON and domain/range errors produce a JSON error and exit 1. Missing
required arguments retain argparse's exit 2.

| Helper | Meaning | Numerical contract |
| --- | --- | --- |
| `finite_expectation(law, potential)` | Sum of supplied mass times potential | Exact accumulation of binary rational products, followed by one float rounding; preserves subnormal sums and severe cancellation. |
| `log_partition(reference, potential)` | Log of the reference-weighted exponential sum | Center on positive reference support before adding log masses, then use a second log-sum-exp center. |
| `exponential_tilt(reference, potential)` | Normalized reference-weighted Gibbs law | Preserve true zero reference atoms; a very small positive output can round to zero. |
| `gibbs_duality_diagnostics(candidate, reference, potential)` | Compare log partition minus the DV objective with KL to the mathematical tilt | Explicitly normalize accepted input laws; use centered 700-digit arithmetic and analytic log weights for the KL comparison. |

Inputs must be equal-length, nonempty sequences of finite real numbers.
Laws must be nonnegative and sum to one within `1e-12`; booleans and numeric
strings are rejected. The scalar helpers use accepted masses literally.
Diagnostics instead normalize by the exact binary rational sums and expose
`input_mass_sums`, `input_mass_residuals` and `normalization_convention`. This
prevents a tolerated mass residual from becoming a large artificial gap under
a large constant potential shift. Existing `finite_kl_totalized` and
`extended_kl` retain their earlier conventions.
The displayed sums and residuals use float summation; the internal
normalization retains smaller exact mass tails even when that displayed sum
rounds to one.

`reference_zero_indices` records true support zeros.
`candidate_outside_reference_indices` identifies an extended-KL support failure;
the report uses `"infinity"` for KL and the duality gap, `"-infinity"` for the
DV objective, and `null` identity comparisons. `tilt_underflow_indices` instead
records positive reference atoms whose computed optimizer mass rounds to zero.
For example, reference and candidate `(0.5, 0.5)` with potential `(0, -1000)`
have a finite gap of approximately `500 - log(2)`, even though the returned
optimizer is `(1, 0)`. Computing KL against that rounded optimizer would lose
the distinction. The private 700-digit context also retains tiny mass tails
beside a mass of one, where 80-digit addition would erase representable log
partitions and KL values. It does not inherit the caller's Decimal settings.

The report includes the expected potential, centered quantities, DV objective,
both gap evaluations, identity residual and a float roundoff allowance. Finite
reported values outside binary64 range raise `BoundaryProbeError`; an
unrepresentable intermediate potential difference alone does not cause failure
when its weighted result is representable. A small residual checks arithmetic
consistency, not an interval-certified bound or Lean proof. Exact theorem
premises and signed-precision optimization are described in the
[formal extension guide](support-aware-variational-methods.md).

## Lean statements and natural-language analysis

`analyze` joins the exact Lean declaration with its maintained invariant,
assumption review, non-vacuity record and semantic disposition. `theorem`
selects a qualified declaration rather than matching its name loosely. The
analysis separates binders, explicit premises and conclusions, and distinguishes
primary witnesses from supporting declarations and authored relation witnesses.
Its prose comes from reviewed owners. This source-grounded analysis is not a
certified translation of Lean into natural language or a new semantic review.

The interpretation protocol in Supplement A first fixes the carrier and
codomain, then checks normalization, support, quantifier order and equality
conditions, and finally tests the proposed prose against the exact conclusion.
Totalized real expressions and extended nonnegative expressions need separate
readings; almost-everywhere kernel identities cannot become pointwise claims.
Dependency roles help the reader locate evidence but do not establish that an
import was used by a particular proof.

## Four different embeddings

| Map | What it preserves | What still needs proof |
| --- | --- | --- |
| Finite law to weighted Dirac measure | Finite integrals and events on the specified embedding | Native functional agreement needs support, measurability and codomain conditions. |
| Parameter to probability law | A chosen statistical family | Injectivity and full differential rank; redundant parameters can make Fisher singular. |
| Full state or path to an observation | A pushforward law | Identification of hidden states or constitutive quantities; process reduction also needs kernel compatibility. |
| Result contract to corpus features | Chosen textual and binary coordinates | Every mathematical or semantic association beyond those coordinates. |

The finite simplex is compact in its Euclidean topology. Smooth Fisher
geometry normally uses its positive interior and tangent vectors summing to
zero. Weak convergence of laws does not by itself give KL convergence, and
compact finite-channel optimization does not by itself give infinite-dimensional
existence or strong duality. The supplement derives these distinctions and
provides exact countermodels.

## Numerical panels and scope

The export retains the original seven logical explorer views and adds
cross-corpus coordinates, feature inspection and Lean contract analysis. It
has 17 files, including thirteen SVGs.
The combined relation overview supports interactive inspection; three separate
relation matrices give readable print layers. The manuscript cites twelve
figures and the renderer preserves the complete companion asset closure.

Support-loss examples compare convergence of finite laws with extended KL and
the repository's explicitly totalized finite functional. Fisher examples
contrast law-coordinate tangents with a redundant parameter null direction.
The OU panel has identical observed laws despite distinct full laws at every
finite time; both full laws approach the same stationary limit. A separate
scalar-descent probe retains different hidden coordinates and distinct limits.
A binary decision example shows how changing preference alignment
changes agreement with risk minimization. Every panel declares its formula,
carrier and boundary; accessible data tables preserve the underlying numbers.
The four fixed publication grids use exact rational indices and coefficients.
Pi-dependent angles and logarithmic epsilon values are evaluated in an
explicit 80-digit Decimal context with bounded trigonometric series. Half-even
display quantization uses 24 decimal places before JSON serialization. The shared model
records the series remainder criteria and reconstruction factors. Exhaustion
fails closed. This reproducible display producer leaves arbitrary-input probe
contracts and the arithmetic tolerance unchanged; freshness compares exact
bytes, and the method does not provide interval-certified numerical proof.

These probes make failed transfers intelligible. They do not estimate a
population parameter, validate a biological model, or replace a qualified
Lean theorem. A future proof or experiment must specify its own carrier,
assumptions, countermodels and acceptance protocol.

The cross-corpus panel places the 22 FEP family summaries and 12 selected
OpenAI result records in common, authored binary coordinates. Domain, carrier
and condition features are positive assignments; absence means unassigned.
The source records retain exact upstream paths, hashes and the immutable
commit. Family features describe the union of selected owned statement
contexts, so a plotted family is not a single theorem with their conjunction.

Classical multidimensional scaling projects Euclidean distances between those
vectors. The full feature table, distances, eigenvalues and projection stress
remain inspectable. A close point is a comparison prompt: no mathematical
embedding between the underlying state spaces, transfer theorem, learned
language representation or equivalence is established by its coordinates.
Repeated eigenvalues can make axes ambiguous even when distances are stable;
the method reports that limitation. The canonical computation uses a private
80-digit Decimal context, a fixed Jacobi pivot rule and an explicit residual
gate. Derived values use 24-place half-even rounding; binary vectors and integer
squared distances retain their exact values. This avoids platform-specific
LAPACK output in freshness checks. The plot uses equal pixel units on both axes.
Supplement A derives the method and works through the actual statements and
the additional assumptions each proposed transfer would need.

## Maintenance and release

The [integration contract](../specs/openai-math-methods/INTEGRATION.md) records
owners and acceptance cases. Package methods and renderer changes participate
in the versioned source-owner roster; adding owners requires a coordinated
refresh. Acquire native evidence after the final source edits and render the
manuscript from that accepted source. The separate
[release gate](release.md) establishes version publication on an exact hosted
commit, while the [open backlog](../TODO.md) retains scientific and operational
lanes that this mathematical integration does not close.

The [local validation record](../specs/openai-math-methods/VALIDATION.md)
separates package, native, publication and scientific evidence. Installed-wheel
methods checks passed locally on Python 3.10 through 3.14. The existing
15-cell distribution job also runs that supplemental check on its selected
interpreter. Release acceptance requires its successful results on the exact
release commit; consult the linked GitHub release and workflow evidence for
that commit. The validator itself remains Python 3.14.
