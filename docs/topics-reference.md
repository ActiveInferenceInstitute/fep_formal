# Topic reference

The schema-2 catalogue currently seals 155 stable identifiers, `fep-001`
through `fep-155`, across 20 named families. This page explains how to inspect
them without copying a second, drift-prone roster.

## Authoritative views

Each view answers a different question:

| Question | Authoritative source |
| --- | --- |
| What is the title, area, and Mathlib navigation hint? | [`config/catalogue_metadata.yaml`](../config/catalogue_metadata.yaml) |
| What is the reviewed invariant, primary theorem, assumption boundary, non-vacuity argument, and disposition? | [`config/theorem_maturity.yaml`](../config/theorem_maturity.yaml) |
| What Lean code is compiled? | Family modules under [`fep_lean.catalogue.bodies`](../src/fep_lean/catalogue/bodies/) merged by [`registry.py`](../src/fep_lean/catalogue/registry.py) |
| How are expansion rows distinguished from earlier work? | [`config/formalism_novelty.yaml`](../config/formalism_novelty.yaml) |
| Which formal/conceptual/blocker links and capability states were explicitly reviewed? | [`config/formalism_relations.yaml`](../config/formalism_relations.yaml) |
| What is the joined, human-readable coverage view? | [Formalism coverage](formalism-coverage.md) |
| How do the reviewed nodes and edges look as a graph? | [Interactive formalism atlas](formalism-atlas.html) or [static SVG](formalism-atlas.svg) |
| How do selected finite laws behave numerically? | [Interactive formal-kernel dashboard](formal-kernel-dashboard.html) or [static SVG](formal-kernel-dashboard.svg) |
| Which proofs genuinely compose stable topic namespaces? | Manifested leaves under [`src/fep_lean/formal/compositions/`](../src/fep_lean/formal/compositions/); [`composed.lean`](../src/fep_lean/formal/composed.lean) imports them |
| Which shared finite carriers and laws support those proofs? | [Formal-kernel methods](guides/formal-kernel-methods.md) and [`src/fep_lean/formal/`](../src/fep_lean/formal/) |
| What exact theorem statements and proofs appear in the publication appendix? | Generated `manuscript/09z_unified_formalism_catalogue.md` |
| Did the current bytes compile? | A validated native receipt, normally `output/native-verification.json` |

`config/topics.yaml` and `src/fep_lean/data/topics.yaml` are byte-identical
generated joins for checkout and installed-wheel use. Do not edit either one
by hand.

## Inspect from Python

```python
from fep_lean.catalogue import FEPTopicCatalogue

catalogue = FEPTopicCatalogue.default()
topic = next(row for row in catalogue.topics if row.id == "fep-014")

print(topic.primary_theorem)
print(topic.semantic_disposition)
print(topic.assumption_review)
print(topic.lean_sketch)
```

`FEPTopicCatalogue.default()` reads packaged data through
`importlib.resources`, so this works from an isolated wheel rather than only
from a source checkout.

## Inspect from the command line

Generate deterministic offline projections:

```bash
uv run fep-lean catalogue
```

Compile one topic for development:

```bash
uv run fep-lean verify --topic fep-014 --fail-on-warnings
```

Create publication-eligible native evidence for the exact roster:

```bash
uv run fep-lean verify \
  --fail-on-warnings \
  --receipt output/native-verification.json
```

A filtered receipt is diagnostic only. Native claim readiness requires the
ordered sealed roster, clean compilation for every row, zero warnings, zero
`sorry`, current catalogue/source digests, and the pinned Lean/Mathlib
identity. It does not establish semantic adequacy or a Hermes/OpenGauss run.

## Read the maturity fields correctly

- `mathlib_status` says whether the body is intended to compile against the
  pinned library surface.
- `semantic_disposition` says how the primary theorem relates to the reviewed,
  deliberately narrowed invariant.
- A `formalized` row is direct only at the stated scope. It is not evidence for
  every scientific interpretation of its topic label.
- `conditional_proxy` and `structural_proxy` record useful, narrower facts.
- `scope_gap` and `assumption_gap` identify work that compilation cannot close.

The current semantic firewall contains direct formalizations alongside
explicit `conditional_proxy` and `structural_proxy` rows. These are deliberate
scope classifications, not failed compilation states. The learning expansion
adds finite-sample concentration, PAC-Bayes, posterior-odds, posterior-
concentration, mixture-regret, and Bayes-factor results with their stated
support and probability premises; it does not retroactively strengthen
fep-036 beyond its maintained empirical-frequency and smoothing contract.
The later finite-sample family does add finite-law Laplace squared-risk and
Brier-risk transfer plus concentration-event containment, while retaining
posterior contraction, empirical calibration, and marginal-likelihood
optimization as broader claims. Parallel seven-topic families add finite
policy trees, native blanket transfer, scalar exponential-family dual geometry,
and an exact two-state continuous-time semigroup. Their scope and non-vacuity
contracts are summarized in
[`manuscript/04i_formalism_catalogue_155.md`](../manuscript/04i_formalism_catalogue_155.md).
Historical proxy and gap values remain part of the schema so older receipts
and future regressions stay interpretable.

The current disposition totals are generated in
[formalism-coverage.md](formalism-coverage.md); this page intentionally does
not copy them.

## Relations are authored, imports are derived

The coverage report contains two separate graphs:

- Mathlib import incidence is derived mechanically from actual `import`
  commands and records library reuse only.
- `conceptual`, `formal`, `formal_pairing`, and `blocked_by` relations are
  maintained with a rationale in `config/formalism_relations.yaml`; both
  theorem-backed kinds also name a qualified Lean witness.

No conceptual or proof dependency is inferred from two rows importing the
same module. Manifested composition leaves contain direct cross-topic proofs,
and the authored graph exposes them only when a theorem-backed edge resolves
to a leaf-owned declaration. `formal` records an actual derivation or
identification; `formal_pairing` records two checked endpoint laws without an
implication claim. The import-only aggregate makes those leaves available
to workspace consumers but is not a second theorem owner. Reusable foundation
modules provide additional capability evidence. Their internal imports are
visualized as a separate purple dependency layer and never promoted to
scientific edges. The other authored edges remain explicitly conceptual or
blocked.

## Change a topic

1. Edit the appropriate maintained owner: metadata, semantic review, novelty
   ledger, relation graph, or family-owned canonical body.
2. Regenerate the catalogue, topic aggregate, and manifested formal-module
   projections.
3. Regenerate maturity and coverage projections.
4. Regenerate and drift-check the atlas and formal-kernel dashboard.
5. Run focused Lean verification for the changed row.
6. Run the warning-free aggregate, formalism declaration/axiom audit, and
   exact-roster native receipt before publication.

Commands and ownership are documented in
[`scripts/README.md`](../scripts/README.md) and
[`docs/development.md`](development.md).
