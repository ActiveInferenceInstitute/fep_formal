# `fep_lean.catalogue`

Typed catalogue ownership and deterministic projections for FEP_Formal's
schema-2 roster. The maintained roster seal is owned by
[`catalogue_metadata.yaml`](../../../config/catalogue_metadata.yaml).

## Authoring graph

```text
config/catalogue_metadata.yaml
config/theorem_maturity.yaml
config/formalism_novelty.yaml
src/fep_lean/catalogue/bodies/*.py
src/fep_lean/catalogue/registry.py + latex.py
                 │
                 ▼ strict roster-sealed join + novelty-bridge validation
config/topics.yaml == src/fep_lean/data/topics.yaml
                 │
                 ├─ lean/FepSketches/fep_all.lean
                 ├─ docs/theorem-maturity-audit.md
                 ├─ docs/formalism-coverage.{md,json}
                 ├─ docs/formalism-atlas.{svg,html}
                 └─ docs/formal-kernel-dashboard.{svg,html}

config/formalism_relations.yaml
                 │
                 └─ independent relation/capability validation and projections
```

`FEPTopicCatalogue.default()` loads packaged data with `importlib.resources`, so
the same API works in a checkout and an isolated wheel. `from_yaml(path)` is
available for explicit projections and test fixtures.

`TopicEntry` keeps compile maturity (`mathlib_status`) distinct from semantic
reach (`semantic_disposition`) and exposes the maintained primary theorem,
assumption review, non-vacuity note, and acceptance probe. `summary()` reports
both maturity and semantic totals, including area-level breakdowns.

```python
from fep_lean.catalogue import FEPTopicCatalogue, SemanticDisposition

catalogue = FEPTopicCatalogue.default()
assert catalogue.topics[0].id == "fep-001"
assert catalogue.topics[-1].id == "fep-168"
assert SemanticDisposition.FORMALIZED.value == "formalized"
```

The novelty ledger seals the post-baseline roster and resolves its required
cross-topic theorems before topic projection. The relations ledger is a
separate authored semantic graph: it distinguishes actual derivational
`formal` edges from checked, non-implicational `formal_pairing` edges and
resolves both kinds plus capability witnesses. Its rows are not copied into
`topics.yaml`.

Edit only the maintained inputs, then run the project-root generators and
their `--check` modes. Never hand-edit a generated YAML, aggregate Lean file,
audit table, coverage projection, or atlas.

The [root source map](../../../AGENTS.md#source-of-truth) owns the complete
projection chain and its [required checks](../../../AGENTS.md#required-checks).
Portable methods package copies have a separate generator; see the
[packaged-data contract](../data/AGENTS.md).
