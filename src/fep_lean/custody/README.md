# `fep_lean.custody`

Evidence custody for the H2.7 terminal-acceptance chain: a read-only census of
which receipts and captured sources still match the live tree, a strict gate over
that census, and a staged, dependency-ordered refresh that re-binds stale
evidence without touching the live `specs/` tree.

```text
census → verify gate → apply (staged dependency order) → verify set → optional native capture
```

## Census

`census(specs_dir, repo_root)` classifies every custody surface with one of
three statuses and returns an ordered `Census` of `CensusRecord`s:

- `intact`: the recorded custody value equals the live value.
- `stale`: recorded evidence predates a live change, which a custody chore
  legitimately re-binds or re-captures (for example a native capture digest).
- `live-red`: a structural or semantic break, such as a missing or unparseable
  receipt, a drifted `PREDECESSORS` pin, or custody semantics the validator
  rejects. No re-bind of recorded values may paper over it.

The census only hashes bytes. `Census.is_gated()` is true when any surface is
non-intact. Both directories are injectable so tests can use isolated fixtures.

## Gate

`verify(census, expectations)` returns `(ok, problems)`. It does not read the
tree. Required surfaces must appear and be intact; a `stale` record passes only
when its path is in `allowed_stale`; a `live-red` record always fails.
`GATE_EXPECTATIONS` requires the terminal receipt, the validator constant, and
every pinned predecessor to be intact.

## Apply and refresh

Use `uv run fep-lean custody --help`. The `--project-root` option selects the
repository; `--specs-dir` defaults to `<project-root>/specs`.

- `census` prints a JSON drift report and writes nothing.
- `apply --output-dir DIR` gates, then walks the settled dependency order
  (`PHASE_ORDER`) and flushes a staged copy of the specs tree into `DIR`.
  `DIR` must be empty and must not be the live specs tree. Repo-side surfaces
  are never written; they come back as byte-replacement directives for the
  coordinator to apply.
- `refresh --reason TEXT` composes census, stop-gate, apply, the read-only
  verify set, the pre-capture owner gate, and, with `--native`, the native Lean
  capture. Capture needs a committed clean tip and fails closed.
  - `--plan` leaves the input tree unchanged and skips apply/test/audit
    subprocesses. It writes a plan journal in state `planned`, so it is not a
    filesystem-write-free inspection.
  - `--fixpoint --output-dir DIR` runs a bounded staged fixpoint
    (`--max-rounds`, default 4) and journals state `awaiting-commit`.
  - `--resume JOURNAL-DIR --output-dir DIR` completes a journal against the
    committed candidate, enforces the render-acceptance barrier, runs the verify
    set and optional capture, and ends in state `captured`.

Journals are schema-1 JSON under `output/custody-journal/<operation-id>/`
(`--journal-dir` overrides the parent). Exit code 0 means the requested report
composed or the operation landed; 1 means a gate or fail-closed check refused,
with a JSON error on stdout. A refresh never pins the GNN bridge; a stale bridge
binding after apply is reported as a warning for the coordinator's pin cycle.

```python
from fep_lean.custody import GATE_EXPECTATIONS, census, verify

ok, problems = verify(census(specs_dir, repo_root), GATE_EXPECTATIONS)
```

Tests (`tests/test_custody_*.py`) build synthetic, hermetic epochs under
`tmp_path`; they do not reaccept historical evidence or run the compiler.

Follow the [local contract](AGENTS.md) and the
[root required-check inventory](../../../AGENTS.md#required-checks).
