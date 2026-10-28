# FEP_Formal configuration authoring contract

Edit only the file that owns the intended concept:

- `settings.yaml` for non-secret runtime defaults;
- `catalogue_metadata.yaml` for the schema-2 roster seal, family membership,
  descriptive metadata, and Mathlib hints;
- `theorem_maturity.yaml` for semantic claim review;
- `formalism_novelty.yaml` for expansion-row nearest predecessors, carrier
  deltas, invariants, and required composition bridges;
- `formalism_relations.yaml` for reviewed relations and retained capability
  status/evidence;
- the appropriate `src/fep_formal/catalogue/bodies/*.py` module for canonical
  Lean bodies. `registry.py` validates the family registry and `latex.py`
  derives equation signatures.

`topics.yaml` is generated. Never repair a generated row by hand. Run the
topic generator, inspect both checkout and package-data projections, and use
`--check` to prove idempotence.

## Invariants

- Preserve the exact ordered schema-2 roster seal and the declared family
  partition.
- Keep syntactic maturity, semantic disposition, native verification, and
  full-run evidence as separate concepts.
- Do not promote a disposition merely because Lean compiles.
- Every relation edge needs an explicit rationale. Never infer topic
  dependencies from shared imports or similar theorem syntax.
- Every `formal` or `formal_pairing` edge names a qualified declaration that
  resolves from canonical topic or composed Lean resources. `formal` asserts a
  genuine derivation or identification across endpoints; `formal_pairing`
  certifies both endpoint laws without claiming implication. Conceptual and
  blocker edges never carry a witness.
- Keep satisfied capability nodes with their declaration evidence; do not
  erase the history of a resolved gap.
- Every `scope_gap` or `assumption_gap` row needs a `blocked_by` edge to a named
  capability.
- Every novelty row must identify an earlier nearest topic, a nonempty carrier
  delta and invariant, and a required `FEPComposed` bridge that resolves in a
  manifested leaf composition module.
- Do not copy live counts or model rosters into this file; use generated
  coverage and live configuration.
- Never store provider credentials in YAML.

## Maintenance checks

Use the [root required-check inventory](../AGENTS.md#required-checks) for
projection, semantic, coverage and Markdown gates. The focused source contracts
are exercised by `tests/test_fep_topics.py`, `tests/test_semantics.py`,
`tests/test_formalism_relations.py` and `tests/test_formalism_coverage.py`.
Portable methods inputs have a separate generated-package owner, described in
[the packaged-data guide](../src/fep_formal/data/README.md).

See [README.md](README.md) for the file schema and [SPEC.md](SPEC.md) for the
ownership model.
