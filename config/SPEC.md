# FEP_Formal configuration specification

The `config/` directory contains runtime settings and maintained publication
inputs. It does not contain executable code.

## Ownership

| File | Contract |
| --- | --- |
| `settings.yaml` | Standalone project, Gauss, output, and Hermes defaults; environment overrides remain external |
| `catalogue_metadata.yaml` | Schema-2 roster seal, family, identity, title, area, Mathlib hints, and syntactic maturity |
| `theorem_maturity.yaml` | Semantic invariant, assumptions, non-vacuity, acceptance probe, primary theorem, and disposition |
| `formalism_novelty.yaml` | Expansion-row nearest topics, invariant, carrier delta, and required composition bridge |
| `formalism_relations.yaml` | Explicit reviewed topic relations and retained capability status/evidence |
| `topics.yaml` | Generated join; never an authoring source |

Canonical Lean bodies live in family modules under
`src/fep_lean/catalogue/bodies/`. The validated `registry.py` merger and
`latex.py` theorem-signature projection join them with the maintained topic
inputs and write both checkout and package-data YAML.

## Validation rules

- Topic IDs match the `catalogue_metadata.yaml` roster seal, are ordered and
  unique, and belong to exactly one declared family.
- Catalogue and semantic review schemas reject missing and unknown fields.
  Runtime settings use their named consumer contracts; they are not validated
  by the catalogue row schema.
- A primary theorem must resolve in its canonical Lean body.
- Semantic disposition is independent of `mathlib_status` and compilation.
- Relation edges require a rationale; `blocked_by` targets capabilities, while
  `formal`, `formal_pairing`, and `conceptual` target known topics. The two
  theorem-backed kinds require a qualified declaration witness. A `formal`
  edge records a derivation or identification; `formal_pairing` records a
  checked conjunction without implication. Conceptual and blocker edges
  forbid witnesses.
- Capability status is open, partial, or satisfied. Partial/satisfied nodes
  require sorted declaration evidence, and satisfied nodes cannot remain
  blocker targets.
- Every semantic gap has an explicit blocker, derivational-formal edges are
  acyclic, and shared imports never imply a scientific relation.
- Every novelty row points backward to an earlier topic and names a resolvable
  `FEPComposed` bridge in a manifested leaf composition module.
- Runtime settings never contain provider credentials.

## Projection maintenance

Follow the generator ownership in [README.md](README.md) and use the
[root required-check inventory](../AGENTS.md#required-checks). A generator write
pass is an explicit owner update; its `--check` mode inspects drift without
repairing it. Packaged methods resources have the separate owner mapping in
[the data guide](../src/fep_lean/data/README.md).
