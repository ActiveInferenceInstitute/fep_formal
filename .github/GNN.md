# GNN conformance

`gnn conformance (pinned)` is the display name of the `gnn-conformance` job in
`.github/workflows/ci.yml`. This repository has no `.github/gnn-pin.json`; its
custody record is `specs/gnn-bridge-w2-source-custody/source-pin.json`
(schema_version 1), whose `gnn` entry names the descriptive commit
`2778e65c2228148417b2cf71832eb86a019785fb` and the SHA-256 of six GNN owner
files (`pyproject.toml`, `uv.lock`, `src/gnn/main.py`,
`src/gnn/pipeline/step_registry.py`, `docs/gnn/gnn_syntax.md` and
`docs/other/fep_lean/bridge-contract.md`) rather than a release tag.

The job uses the pinned `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1`
(v7.0.1), `astral-sh/setup-uv@68559e99cc807c1eb7e9238fd43a15bba460eec2`
(v10.3.3) and `actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9`
(v7.0.2), and calls `bash scripts/gate.sh gnn`. It does not use
`ActiveInferenceInstitute/.github/.github/actions/setup-python-uv@7159e67315330aac8e414aebae0ad1e999a41448`.

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

## GNN–FEP reader migration: blocked

The [GNN–FEP workflow contract](https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation/blob/main/docs/workflows/gnn-fep.md)
requires the shared `gnn.importers` reader from the pinned GNN environment,
with `--pin specs/gnn-bridge-w2-source-custody/source-pin.json --pin-party gnn`,
`--require-pointer --workflow .github/workflows/ci.yml --job gnn-conformance`.
The custody-pinned revision named above does not contain
`src/gnn/importers.py`. The existing `gnn` arm validates retained artifacts;
it does not materialize a GNN checkout or install a GNN parser environment.

The contract identifies `src/fep_formal/bridge/operations.py:pin_sources` as
the local copy to remove, but that function produces both parties' owner-digest
custody records. It does not parse an upstream pin. The bridge's strict JSON
reader also serves custody receipts, rejecting duplicate keys and non-finite
constants; it is not just a release-pin shape validator.

No reader cutover is claimed. Completing it needs a qualified source-pair
update that includes the shared reader and a materialized pinned environment,
or a clarified upstream instruction compatible with the retained custody pin.
Neither a newer-parser substitution nor deletion of owner-digest checks is
part of this migration. A checker run against a newer GNN checkout is only
diagnostic; it cannot establish conformance under the recorded revision.
