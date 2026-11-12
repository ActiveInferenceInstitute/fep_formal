# W2: source custody and read-only bridge operations

Status: implemented and verified, 2026-09-04. See [delivery evidence](REPORT.md).
Design owner: [GNN bridge](../../docs/design/gnn-bridge/README.md).

## Goal

Make finite/continuous emission and certificate checks deterministic against an
explicit owner snapshot. End self-referential HEAD-refresh commits and reject
content drift, stale owners, malformed receipts, and invalid numeric policies.

## Criteria

- [x] W2-1: status and certificate evaluation leave bytes and mtimes unchanged.
- [x] W2-2: reordered/deleted/duplicated content cannot pass a custody refresh.
- [x] W2-3: relevant owner additions, deletions, and mutations invalidate pins.
- [x] W2-4: both finite and continuous documents regenerate from the same pin.
- [x] W2-5: certificate tampering and nonfinite numeric inputs fail closed.
- [x] W2-6: CLI and legacy entry points use the tested package operations.
- [x] Anti W2-7: comparisons never claim native proof or current execution.

Probe: `uv run pytest tests/test_gnn_bridge_operations.py -q --no-cov`.
Integration: explicit `fep-lean bridge status --gnn-root PATH`, followed by
both emitters' `--check` and independently validated comparison receipts.

## Decisions

- Source commits are descriptive custody references; owner hashes identify
  actual working-tree bytes. The pin and emitted documents are excluded from
  owner digests so a commit containing them does not invalidate itself.
- A pin operation is explicit. It does not accept syntax drift, prove source
  correctness, or establish that an old execution result used those sources.
- Native compilation, semantic review, concrete artifact proofs, and numerical
  comparison retain separate acceptance paths.
- Later expansion order: concrete PyMDP artifacts, then backend-specific
  ActiveInference.jl extraction, then reviewed continuous dynamics. H3 follows
  its independent accepted predecessor gates.

## Current source pin

The retained [source pin](source-pin.json) records GNN main commit
`2778e65c2228148417b2cf71832eb86a019785fb` (`v5.0.3-206-g2778e65c2`, 206
commits after the `v5.0.3` release tag) and FEP commit
`301c2d2405b260ef8b645b0c5a3914fbcdf5c49c`. The six recorded GNN owner digests
match that GNN commit. The GNN 5.0.1 release named in the repository's release
records is an earlier coordinated release, not the current bridge pin.

The pin records the revision under the `commit` key only; it has no `tag` or
`revision` key. A machine inventory that reads `tag`/`revision` therefore finds
no GNN pin for this repository (the real pin is present and checked). Treat
`gnn.commit` as the revision; add a `tag` field only if the pin schema itself is
being revised, which is a separate owner decision.

Open disagreement: the pin's GNN `pyproject.toml` and `uv.lock` digests are
`97277102f7bb...` and `6f60b3c0d755...`, while GNN's later main carries
`de0a22d2d36d...` and `dbee9eb5387b...`. GNN's `check_pair_pin_freshness.py`
exits 2 until the pair is re-pinned. This is an open owner decision (SCOPING
C-1, tracked as CUSTODY-GNN-1 in [TODO.md](../../TODO.md)): do not re-pin or
change the pair-pin machinery to resolve it here.

The retained P1/P2 and P3 artefacts are historical. Their `pipeline_commit`
stamps are `12a565b2f18db7f18c3a799568ad057834ba0358` (`v3.2.0-3-g12a565b2f`),
and the retained P1 pipeline log shows a pre-rename `src/3_gnn.py` run. The
current pin cannot regenerate those artefacts; do not re-label them as current.
