# `fep_lean.catalogue` contract

This package owns the catalogue's semantic truth plane and all deterministic
projections from it.

## Files

- `schema.py`: strict static metadata records and roster validation.
- `relations.py`: typed conceptual/formal/formal-pairing/blocked-by graph,
  capability status, and declaration-evidence validation.
- `novelty.py`: expansion-row nearest-topic, carrier-delta, invariant, and
  required-bridge validation.
- `semantics.py`: `SemanticDisposition`, maturity records, primary-theorem
  validation, and claim-calibrated natural-language rendering.
- `bodies/*.py`: family-owned canonical Lean bodies.
- `registry.py`: explicit family manifest, body validation, and immutable
  roster-ordered merger.
- `latex.py`: deterministic theorem-signature projection from each body.
- `generation.py`: exact join and byte-identical checkout/package YAML output.
- `topics.py`: immutable runtime rows and catalogue summaries.
- `coverage.py`: declaration/import/topic coverage model and renderers.
- `references.py`: manuscript theorem-identifier inventory and audit.

## Invariants

- IDs match the schema-2 roster seal, in order, in every maintained source and
  projection; each body belongs to exactly one declared family.
- Every primary theorem resolves in its canonical Lean body.
- Compilation maturity and semantic disposition are separate; no consumer may
  promote a row solely because it compiles.
- Generated natural language is derived from maintained invariant and
  assumption review, never inferred from tactic syntax.
- Scientific relations come only from `config/formalism_relations.yaml`;
  shared imports never imply a conceptual or formal dependency.
- Derivational `formal` edges and non-implicational `formal_pairing` edges both
  require qualified leaf-composition witnesses that use both topic endpoints;
  partial/satisfied capability nodes require resolved declaration evidence,
  and satisfied nodes remain as auditable history.
- Expansion rows carry a nonempty novelty record whose unique `FEPComposed`
  bridge resolves from a manifested leaf and uses both the new topic and at
  least one declared nearest-topic endpoint outside comments.
- The packaged and checkout catalogues are byte-identical and all generators
  are idempotent.

Import from `fep_lean.catalogue`; do not add compatibility packages or dynamic
imports from `scripts/`.

When an import header changes, preserve module-system visibility and include
actual importing consumers in the review. The coverage parser retains public
and meta imports; source-text edges still supply no native or scientific
acceptance.

See [README.md](README.md), the [package contract](../AGENTS.md) and the
[root required checks](../../../AGENTS.md#required-checks).
