# Mathematical positioning explorer

Generated, byte-exact projection of the mathematical positioning model. It
holds the offline explorer and the figures the manuscript cites. Nothing here
is authored in place.

## Contents

| Path | What it is |
| --- | --- |
| [mathematical-map.html](mathematical-map.html) | Standalone, offline searchable explorer for topic contracts, typed associations and numerical boundary panels. |
| [positioning.md](positioning.md) | Markdown projection of the same model. |
| [positioning.json](positioning.json) | Canonical data projection. |
| [visual-model.json](visual-model.json) | Renderer input for the SVG panels. |
| [panels/](panels/) | Thirteen generated SVG panels and relation views. |

## Regenerate and check

Owners are `config/` and `specs/openai-math-methods/positioning.yaml`; renderers
are `src/fep_formal/methods/projection.py` and `visualization.py`.

```bash
uv run fep-formal --project-root . methods export --output-root docs/mathematical-positioning
uv run fep-formal --project-root . methods check --output-root docs/mathematical-positioning
```

`export` writes the projection; `check` is read-only and runs in CI. Change the
owner or the renderer, then regenerate. Never patch an output file.

## Read next

- [Documentation map](../README.md)
- [Mathematical methods guide](../mathematical-methods.md)
- [Generated projection contract](AGENTS.md)
