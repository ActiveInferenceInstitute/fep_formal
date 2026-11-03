# Cross-topic composition leaves

Hand-written Lean modules that prove relations across catalog families. Each
file imports the family modules whose declarations it uses and states the
cross-topic theorems under its own namespace. This directory is the authoring
surface; [`lean/FepSketches/compositions/`](../../../../lean/FepSketches/compositions/)
is the generated projection.

## How a leaf is used

[`../manifest.py`](../manifest.py) registers each leaf with role `composition`
and an explicit declaration namespace. It selects the leaf;
`scripts/_maint_build_formal_modules.py` projects it byte-exactly into the Lake
workspace and the manifest also selects it for the aggregate/audit closure.
[`../composed.lean`](../composed.lean) is the import-only aggregate, not a
proof owner.

## Current leaves

Every `.lean` file here is one composition. Names follow the cross-topic area
they join, for example `core.lean`, `perception_action_loop.lean`,
`gaussian_filter.lean` and `thermo_geometry.lean`. The manifest is the
authoritative roster; read it rather than inferring coverage from filenames.

## Changing a leaf

Edit the leaf and its manifest entry together, preserve the module-system
header and public declaration visibility, then regenerate:

```bash
uv run python scripts/_maint_build_formal_modules.py
(cd lean && lake build FepSketches)
uv run python scripts/audit_formalisms.py --receipt output/formalism-audit.json
```

Inspect the generated workspace diff. A successful import or build does not
create a scientific edge; relations stay authored in
`config/formalism_relations.yaml`. See the [formal package contract](../AGENTS.md)
and the [root required checks](../../../../AGENTS.md#required-checks).
