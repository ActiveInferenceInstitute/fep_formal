# Finite-path Landauer review

The fep-050 endpoints derive biased-prior heat bounds from the normalized finite
path erasure model, reverse support, local detailed balance, and a reset final
marginal. The fair-bit heat and work bounds are derived corners. The
constitutive-law bridge retains its explicit entropy-balance assumption and
conditional meaning. The reviewed maturity disposition is unchanged.

Canonical inputs:

- [Topic bodies](../../../../src/fep_formal/catalogue/bodies/core_thermodynamics.py)
- [Finite path model](../../../../src/fep_formal/formal/path_thermodynamics.lean)
- [Conditional composition](../../../../src/fep_formal/formal/compositions/core.lean)
- [Maintained native controls](../../../../tests/fixtures/landauer_path_controls.lean)
- [Maturity review](../../../../config/theorem_maturity.yaml)

These immutable records are retained verbatim at their observation checkpoints:

| Record | Scope | SHA-256 |
| --- | --- | --- |
| [Science](science.json) | Finite-path premises, heat units, biased and reversible controls, conditional bridge | `272f92230f9f9f21612869c8d804f6a89fa784345b736e3021642f2691e2aa7f` |
| [Software](software.json) | Current contracts, copied historical comparisons, unchanged sealed fixtures | `96cd72003805111d33cd1a85ca33e0b8ed260dcaf7a645dffa7ff8deece64ca0` |
| [Test partition](test-partition.json) | Exact marker-only movement of 182 cases; preserved 4,469 collected identities and compiler serialization | `a3b890e2d5b0a6d41066aa27566333185311d248053890a3bfaf5e323a017053` |
| [Native and publication data](native-publication.json) | Actual 168-topic native receipt, focused tests, and source-bound local PDF/HTML | `87b5f0b3b9e48a85968f8e320babca2cbf550cb205fe01e86f11fb8536c26ff5` |

Later edits clarify the partition wording and document packaging preparation
before strict collection. The source and test contracts reviewed above retain
their recorded bytes. Review records distinguish observations from executed
qualification; the final commit still requires normal pull-request and merged-main
CI. The local PDF discloses its dirty source snapshot and existing release label.
Release identities and historical receipts remain unchanged.
