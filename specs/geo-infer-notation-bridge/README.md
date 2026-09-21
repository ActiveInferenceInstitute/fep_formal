# GEO-INFER notation bridge slice

Status: core subset landed and accepted (checker and `data/notation-map.yaml`
in); the slice remains open for row-by-row growth per fixed decision 5.
Charter context:
[GNN bridge design](../../docs/design/gnn-bridge/README.md).

## Goal

Record, as reviewable data, the notation-level correspondence between
fep_lean's maintained theorem proxies (the reviewed invariant rows of
`config/theorem_maturity.yaml`) and the implemented Active Inference surface
of GEO-INFER-ACT (`src/geo_infer_act/` in the sibling GEO-INFER checkout).
The mapping states correspondence of symbols and constructs between the two
repositories; it does not translate proofs, run code, or compare numbers.

## Fixed decisions (adapted from the GNN bridge charter)

1. **Documentation-only.** The map is a documentation artifact. NO row may
   claim that any GEO-INFER implementation is verified or proved by fep_lean,
   and no Lean proof claim is promoted by a notation row. Evidence planes
   stay distinct: Lean native compilation, semantic review, numerical
   witnesses, and Python execution remain separate evidence classes.
2. **Deterministic checker or nothing.** Every mapping row is validated by
   `specs/geo-infer-notation-bridge/check_geo_notation_bridge.py`: strict YAML
   schema, every topic id and symbol must exist in
   `config/theorem_maturity.yaml`, and every GEO-INFER anchor must match a
   strict grammar. No heuristic extraction.
3. **Cross-repo references are prose paths only.** GEO-INFER anchors are
   written as `GEO-INFER-<MOD>/<repo-relative path>::<Symbol>` inline code,
   never as markdown links, because each repository validates links
   independently.
4. **Slice lifecycle.** This directory is a bounded spec slice under
   `specs/`: the README states scope, `data/notation-map.yaml` is the
   artifact, the checker is the freshness gate, and implementation status
   lives in this README's status line.
5. **Artifact scope.** `data/notation-map.yaml` is the machine-checked
   core subset, not an exhaustive census: rows are added one at a time
   through this slice's lifecycle, and the partner page
   (`GEO-INFER-ACT/docs/fep_lean_notation_bridge.md`) may discuss
   constructs whose rows have not landed yet. A row, once added, is
   digest-gated by the checker; the page's prose is the broader record.

## Anchor grammar

```
GEO-INFER-<MOD>/<repo-relative path>::<Symbol>
```

- `<MOD>` is the sibling module directory name under the GEO-INFER checkout
  (for example `GEO-INFER-ACT`).
- `<repo-relative path>` is a POSIX path from the module directory root to a
  Python source file (`.py`), for example
  `src/geo_infer_act/core/free_energy.py`.
- `<Symbol>` is a top-level `class` or `def` name declared in that file.

Anchors are recorded as prose; the checker validates grammar and
self-consistency inside this repository only. It never opens the sibling
checkout, so it cannot and does not verify that the anchor still exists on
the GEO-INFER side; that review belongs to mapping review, not automation.

## Operations

```bash
uv run python specs/geo-infer-notation-bridge/check_geo_notation_bridge.py --check
```

Exit 0 when every entry passes; exit 1 with a diff-style drift report on any
schema, roster, symbol, or grammar drift. Without `--check` the same
validation runs and prints a summary line.
