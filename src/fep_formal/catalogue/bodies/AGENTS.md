# `catalogue/bodies/` contract

Canonical, hand-written Lean bodies for the catalog. This is an authoring
surface; `lean/FepSketches/families/` is its generated projection.

## Body module rules

- One module per reviewed family. Export `BODIES: dict[str, str]` and nothing
  else that a caller could mistake for catalog data.
- Add the module to `BODY_MODULE_MANIFEST` in [`../registry.py`](../registry.py)
  in the reviewed manifest order in the same change. An unregistered module is
  not validated.
- Keys are `fep-NNN` IDs. Each ID appears in exactly one module.
- Each body declares exactly one namespace, `FEPNNN`, with one named
  `end FEPNNN`. It declares at least one theorem, and every theorem name starts
  with `fepNNN_`. Declarations are unique inside the body.
- The body must compile as part of its generated family module, with no
  `sorry`, no new axioms and no warnings at the pinned toolchain.
- The primary theorem recorded in `config/theorem_maturity.yaml` must resolve
  in the body.

## Regeneration and checks

Change the body, then regenerate and inspect the diff:

```bash
uv run python scripts/_maint_build_fep_all_lean.py
uv run python scripts/_maint_build_topics_catalogue.py
(cd lean && lake build FepSketches)
uv run pytest tests/test_catalogue_bodies_compile.py -q --no-cov
```

Never hand-edit `lean/FepSketches/families/*.lean`, `config/topics.yaml` or
`src/fep_formal/data/topics.yaml`. A shared import never creates a scientific
relation; author those in `config/formalism_relations.yaml`. Follow the
[catalogue contract](../AGENTS.md) and the
[root required checks](../../../../AGENTS.md#required-checks).
