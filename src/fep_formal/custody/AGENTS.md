# `fep_formal.custody` contract

- `model.py` owns the census seam types: the three-status vocabulary
  (`intact`, `stale`, `live-red`), `CensusRecord`, and `Census`. Construction
  fails closed on an unknown status, an empty path or detail, or a duplicate
  surface.
- `census.py` owns the read-only classification of the H2.7 custody surface
  (terminal receipt, native capture, `PREDECESSORS` pins, 07 R0 successor)
  against the live tree. It hashes bytes only: no writes, no validator or
  compiler invocation.
- `verify.py` owns the strict comparator `verify(census, expectations)` and the
  default `GATE_EXPECTATIONS`. It never reads the tree.
- `apply.py` owns the settled dependency-ordered walk
  (`PHASE_ORDER`), `byte_replace`, `PatchDirective`, and the buffered staged
  view. It is the only module that flushes a staged specs tree.
- `refresh.py` owns the composed command: `refresh`, `plan_refresh`,
  `fixpoint_refresh`, `resume_refresh`, the schema-1 journals, and the optional
  native capture.
- `cli.py` is a thin argparse adapter (`census`, `apply`, `refresh`) wired into
  `fep-formal custody`; it keeps imports lazy.

A `live-red` record is never authorized: only a `stale` record on a surface in
`allowed_stale` that is not also `required_intact` passes the gate. Census-green
is necessary, not sufficient, for `validate_terminal_acceptance`. Do not give
`census`/`verify` write or subprocess behavior, and do not add tree reads to
`verify`.

`apply` writes only into an explicit, empty `--output-dir` that is not the live
specs tree; a refusal leaves it untouched. Never write repo-side custody files
(`h2_r0_custody`, precision-test constants, `PREDECESSORS`) from this package:
emit count-validated `PatchDirective`s for the coordinator instead. Every byte
replacement goes through `byte_replace` (anchor must occur exactly once). Do not
change the phase order or the two insertion-order JSON exceptions
(`05d-gaussian-conditioning-lifecycle.json`, `diagnostics.json`).

`refresh` requires a non-empty `--reason` in every mode. `--plan` and
`--fixpoint` never run the verify-set subprocesses. Planning leaves the source
tree unchanged but writes its explicit journal; it must not be advertised as
performing no filesystem writes. The native capture is
fail-closed and needs a committed clean tip; never swallow a refusal. The
post-apply bridge cascade is a warning only; this package never pins the bridge.
Receipt re-issues are dependency re-binds, not new execution evidence.

```python
from fep_formal.custody import (
    AUTHORIZED_PRIOR_DRIFT,
    GATE_EXPECTATIONS,
    INTACT,
    LIVE_RED,
    STALE,
    STATUS_VOCABULARY,
    VALIDATOR_PATH,
    Census,
    CensusRecord,
    Expectations,
    census,
    verify,
)
```

`apply`, `refresh`, and `cli` are not re-exported; import them by module path.

Tests are `tests/test_custody_census.py`, `test_custody_apply.py`,
`test_custody_refresh.py`, and `test_custody_fixture_epoch.py`, with synthetic
epochs from `tests/_support/custody_fixture_knobs.py`. They run on `tmp_path`
fixture roots and injected `Census`/`Expectations`, never the live `specs/` tree
or a real native run. Use the
[root required-check inventory](../../../AGENTS.md#required-checks) for the
project gate; a focused custody selection retains those fixture boundaries.

See [README.md](README.md), [../verification/AGENTS.md](../verification/AGENTS.md),
[../output/AGENTS.md](../output/AGENTS.md), and
[../bridge/AGENTS.md](../bridge/AGENTS.md).
