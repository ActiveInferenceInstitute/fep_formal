# Compatibility distributions

Metadata-only packages that preserve the deprecated `fep_lean`/`fep-lean`
names for installers that still request them. New work uses the canonical
`fep_formal`/`fep-formal` distribution in [`../`](../README.md); see the
[identity migration guide](../docs/identity-migration.md) for the transition
and release ordering.

## Contents

| Path | What it is |
| --- | --- |
| [fep-lean/](fep-lean/README.md) | Deprecated `fep-lean` alias distribution: name and metadata only, with no modules or console commands. |

Each subdirectory is a standalone distribution with its own `pyproject.toml`.
They declare a dependency on the matching `fep-formal` version, so building or
publishing one follows the canonical release. They own no source; do not add
code or entry points here. The local contract is
[`fep-lean/AGENTS.md`](fep-lean/AGENTS.md).

## Build and publish

Build like any other distribution, after the matching `fep-formal` release:

```bash
python -m build compat/fep-lean
```

Never publish a compatibility distribution ahead of, or against a different
version of, the canonical release it depends on.
