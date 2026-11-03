# Test fixtures

Pinned inputs for catalogue, semantic, composition, custody and migration
tests. These are retained source records, not generated outputs, and not a
scratch directory.

## What is here

| Group | Examples | Consumed by |
| --- | --- | --- |
| Dated review records | `theorem_proxy_review_20261019.json`, `exact_information_review_20261020.json`, `conceptual_obligations_review_20261022.json` | Catalogue, semantic and formalism tests |
| Lean control modules | `fep103_*_controls.lean`, `fep95_*_controls.lean`, `ness_forward_difference_controls.lean` | Formal, composition and depth-upgrade tests |
| Historical custody records | `custody_toolchain_4_34_1.json`, `historical_h3_custody_*.json` | Custody and Lean 4.35 migration helpers |
| Exact historical text | `historical_*_Y.txt` | Custody and Gaussian readiness tests |
| Migration and release records | `lean435_catalogue_proof_migration.json`, `post219_composition_compatibility.json`, `landauer_epoch_20261026.json` | Catalogue, composition and epoch tests |

Filenames carrying a date are dated reviews; their values describe that source
epoch. They do not become current merely because the test suite still reads
them.

## Use

Read a fixture from its exact path. Do not rewrite, reformat or regenerate a
fixture to make a test pass. When a fixture needs to change, change its
consuming test and the evidence rationale in the same review. See the
[test contract](../AGENTS.md) and the [fixture contract](AGENTS.md).
