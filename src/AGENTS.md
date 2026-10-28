# FEP_Formal source contract

The installable namespace is `fep_formal`; `src/` is the packaging layout, not an
importable package. Keep the `fep-formal` console name and existing public Python
imports stable when changing project-facing documentation.

The [source guide](README.md) owns package navigation. Each subpackage's
`__init__.py` owns its public exports; the root
[`fep_formal/__init__.py`](fep_formal/__init__.py) lazily exposes selected high-level
operations. Use qualified `fep_formal.*` imports for package operations.

## Maintenance boundaries

- Follow the [package contract](fep_formal/AGENTS.md) and the affected module's
  local contract before editing an owner.
- Keep generated package data and Lake projections synchronized through their
  declared generators. Edit their canonical inputs rather than their copies.
- Preserve offline catalogue use, explicit provider operations and native
  verification as separate execution paths.
- Source/import consistency, native receipts, full-mode reports and scientific
  acceptance have different validators. A successful import supplies none of
  the latter claims.
- Public API or packaged-resource changes require import-surface and isolated
  wheel verification; project checks remain owned by the
  [root required-check inventory](../AGENTS.md#required-checks).

The [root source map](../AGENTS.md#source-of-truth) owns executable/formal source
rosters and their coordinated evidence-refresh policy. New source files must
follow that policy before a receipt can bind them.

The sibling `fep_lean` package is a deprecated import adapter. Never add
implementation or duplicate resources there; both names must resolve to the
same module and class objects.
