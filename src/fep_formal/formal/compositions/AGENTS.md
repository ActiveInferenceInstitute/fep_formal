# Composition leaf contract

Hand-written cross-topic proofs. Every leaf is projected byte-exactly into
`lean/FepSketches/compositions/`; never edit that projection.

## Rules

- One leaf per cross-topic claim. Register it in [`../manifest.py`](../manifest.py)
  with role `composition` and an explicit qualified declaration namespace. The
  manifest derives the Lean module path from the resource path, so both must
  match.
- Import the actual `FepSketches.families.*` modules whose declarations the
  proof uses. Do not import `fep_all.lean` or `composed.lean`; the aggregate is
  not a proof dependency.
- Keep the established header shape, including `@[expose] public section`, and
  preserve public declaration visibility. An import or header change needs its
  real importing consumers reviewed.
- No `sorry`, no new axioms, no warnings at the pinned toolchain.
- A shared import is not a scientific relation. Author relations in
  `config/formalism_relations.yaml`; a compiled leaf becomes a witness for an
  authored edge, not the edge itself.

## Regeneration and checks

```bash
uv run python scripts/_maint_build_formal_modules.py
(cd lean && lake build FepSketches)
uv run python scripts/audit_formalisms.py --receipt output/formalism-audit.json
```

Follow the [formal package contract](../AGENTS.md) and the
[root required checks](../../../../AGENTS.md#required-checks).
