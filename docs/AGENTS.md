# Documentation contract

All documentation is local to this checkout. Keep links relative to the file
that owns them, keep toolchain/model claims synchronized with the canonical
configuration, and mark generated values as generated data.

The [repository contract](../AGENTS.md#required-checks) owns the complete check
list; [testing.md](testing.md) explains the validation tiers. The release gate
is [release.md](release.md), checked by `release_check.py`. For documentation
changes, run the strict link, Markdown hygiene and cross-reference checks from
the canonical list at the project root.

`--include-root` widens `check_links.py` and `md_hygiene.py` from `docs/**` to
every root `*.md`, every `AGENTS.md` / `README.md` under `src/`, `tests/`,
`config/`, `scripts/`, `lean/`, and `manuscript/`, and the non-historical
documents under `specs/`. Historical trees are explicitly excluded because
they are retained receipts: `specs/done/**`, `specs/**/evidence/**`,
`specs/**/gnn_output*`, `specs/**/gnn-input`, and `specs/**/fixtures`. Repair a
broken link there by annotating the exclusion, never by rewriting the file.

Use `uv run fep-lean catalogue` to materialize manuscript variables and the
unified appendix before checking manuscript cross-references.

`formalism-coverage.*`, `formalism-atlas.*`, and
`formal-kernel-dashboard.*` are generated projections. Edit their canonical
catalogue, relation, formal-module, or renderer owners, never the generated
bytes. The dashboard is explanatory numerical evidence and never substitutes
for Lean compilation or the declaration/axiom audit.
