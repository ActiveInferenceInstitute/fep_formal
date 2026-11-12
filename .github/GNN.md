# GNN conformance

`gnn conformance (pinned)` is the display name of the `gnn-conformance` job in
`.github/workflows/ci.yml`. This repository has no `.github/gnn-pin.json`; its
custody record is `specs/gnn-bridge-w2-source-custody/source-pin.json`
(schema_version 1), whose `gnn` entry names release `v5.1.0` at commit
`75c834bd8519dc7b5adc4d24f16bf393cfd1ecdf` and the SHA-256 of six GNN owner
files (`pyproject.toml`, `uv.lock`, `src/gnn/main.py`,
`src/gnn/pipeline/step_registry.py`, `docs/gnn/gnn_syntax.md` and
`docs/other/fep_lean/bridge-contract.md`). The `fep_lean` entry seals this
repository's own owner bytes separately.

The job uses the pinned `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1`
(v7.0.1), `astral-sh/setup-uv@68559e99cc807c1eb7e9238fd43a15bba460eec2`
(v10.3.3) and `actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9`
(v7.0.2), and calls `bash scripts/gate.sh gnn`. It does not use
`ActiveInferenceInstitute/.github/.github/actions/setup-python-uv@7159e67315330aac8e414aebae0ad1e999a41448`.

The job still reports for documentation-only pull requests, skipping its
heavier steps, and runs the GNN–FEP reader described below, then
`generate_probe.py --check` under `specs/gnn-bridge-q5-artifact-proof` and
`specs/cascadia-geo-act-proof`,
`check_geo_notation_bridge.py --check` over
`specs/geo-infer-notation-bridge/data/notation-map.yaml` against
`config/theorem_maturity.yaml`, `validate_retained.py` with
`test_validate_retained.py`, and `pytest` on
`specs/gnn-semantic-witness-v1/test_composition.py`. The Cascadia gate
regenerates its instance in memory from
`specs/cascadia-geo-act-proof/fixtures/smith_river_homing.gnn.md`, failing on
any byte difference; the reader's own scan finds that one `*.gnn.md` and no
other. The job installs the pinned GNN revision but does not check out a GNN
working tree, so the pin's owner digests are re-verified against a checkout by
`fep-formal bridge status --gnn-root PATH`, not here.

## GNN–FEP reader: adopted

The [GNN–FEP workflow contract](https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation/blob/main/docs/workflows/gnn-fep.md)
gives pin parsing, pin and pointer validation, and `*.gnn.md` validation one
home: `gnn.importers` in the pinned GNN revision. This repository adopts that
reader and keeps no copy of it.

The revision recorded here before this change was
`2778e65c2228148417b2cf71832eb86a019785fb`, with no release tag. That tree
predates `src/gnn/importers.py` (`e6a9d3917`), so neither the module nor
`python -m gnn.importers` existed in the environment the pin named:
`git show 2778e65c:src/gnn/importers.py` fails, and a checker run against a
newer checkout was diagnostic only. The pin now names `v5.1.0` at
`75c834bd8519dc7b5adc4d24f16bf393cfd1ecdf`, which carries the reader, so
`bash scripts/gate.sh gnn` installs that revision and runs it:

```bash
python -m gnn.importers check --repo . \
  --pin specs/gnn-bridge-w2-source-custody/source-pin.json --pin-party gnn \
  --require-pointer --workflow .github/workflows/ci.yml --job gnn-conformance
```

The arm installs the package from the pinned commit rather than from a checkout
(`uv run --with "generalized-notation-notation @ git+https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation@<pinned commit>"`,
where the commit is read from the pin), so the pin reader, the pointer rules and
the specification parser are the ones `75c834bd` ships.

The reader reports one warning, `pin-schema-unversioned`: a two-party custody
pin keeps `schema_version: 1` plus per-file owner digests, so it does not
declare the flat `gnn-importer-pin/v1` shape. That is the expected state for
this artifact, not a field this repository should invent.

The cutover deleted no local reader, because this repository never added one:
the blocked state was a documented pointer with no GNN reader at all. The
duplicate the contract names, `bridge/operations.py:pin_sources`, produces both
parties' owner-digest records and is not a pin parser; the contract's own
member note keeps `fep_formal`'s owner-digest and paired-revision gates, so it
stays.
