# GNN conformance

`gnn conformance (pinned)` is the display name of the `gnn-conformance` job in
`.github/workflows/ci.yml`. This repository has no `.github/gnn-pin.json`; its
custody record is `specs/gnn-bridge-w2-source-custody/source-pin.json`
(schema_version 1), whose `gnn` entry names the descriptive commit
`2778e65c2228148417b2cf71832eb86a019785fb` and the SHA-256 of six GNN owner
files (`pyproject.toml`, `uv.lock`, `src/gnn/main.py`,
`src/gnn/pipeline/step_registry.py`, `docs/gnn/gnn_syntax.md` and
`docs/other/fep_lean/bridge-contract.md`) rather than a release tag.

The job still reports for documentation-only pull requests, skipping its
heavier steps, and runs `generate_probe.py --check` under
`specs/gnn-bridge-q5-artifact-proof` and `specs/cascadia-geo-act-proof`,
`check_geo_notation_bridge.py --check` over
`specs/geo-infer-notation-bridge/data/notation-map.yaml` against
`config/theorem_maturity.yaml`, `validate_retained.py` with
`test_validate_retained.py`, and `pytest` on
`specs/gnn-semantic-witness-v1/test_composition.py`. The Cascadia gate
regenerates its instance in memory from
`specs/cascadia-geo-act-proof/fixtures/smith_river_homing.gnn.md` and the
sibling fixtures, failing on any byte difference; that fixture is the only
`*.gnn.md` the job reads, and the job neither re-reads the source pin against a
GNN checkout nor scans the rest of the repository for `*.gnn.md`.
