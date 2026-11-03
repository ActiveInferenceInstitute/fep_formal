# Canonical topic bodies

One Python module per reviewed catalog family. Each module exports
`BODIES: dict[str, str]`, mapping a topic ID such as `fep-001` to that topic's
canonical Lean source. This directory is the authoring surface for topic bodies.

## How a body is used

1. [`registry.py`](../registry.py) imports each family module explicitly,
   validates family membership and roster order, then merges the bodies into
   one immutable, roster-ordered map.
2. [`latex.py`](../latex.py) projects theorem signatures from the same bodies.
3. The runtime catalogue validates each topic's primary, supporting and
   boundary theorems against the body's declarations.
4. Generators project the merged catalog into
   `lean/FepSketches/families/*.lean`, `config/topics.yaml`,
   `src/fep_formal/data/topics.yaml`, coverage and the atlas.

A body is a fragment of Lean source, not a standalone module. The generated
`lean/FepSketches/families/<family>.lean` file is the compilable projection.

## Changing a body

```bash
uv run python scripts/_maint_build_fep_all_lean.py
uv run python scripts/_maint_build_topics_catalogue.py
uv run python scripts/build_formalism_coverage.py
uv run python scripts/build_formalism_atlas.py
```

Every generator has a non-mutating `--check` mode. Run the catalogue tests and
the Lean build after a body change. See the
[catalogue contract](../AGENTS.md), the [catalogue guide](../README.md) and the
[root required checks](../../../../AGENTS.md#required-checks).

## Related owners

- `config/catalogue_metadata.yaml` — roster seal and family membership.
- `config/theorem_maturity.yaml` — semantic review and primary theorem.
- `config/formalism_novelty.yaml` — expansion ledger and required bridges.
