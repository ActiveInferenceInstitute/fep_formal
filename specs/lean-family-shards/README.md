# Lean family shards

[Issue 101](https://github.com/ActiveInferenceInstitute/fep_formal/issues/101)
changes generated module ownership and imports. It adds no scientific theorem
or semantic-dependency edge.

The body manifest owns 22 generated family modules. All 168 topic namespace
bodies and all 17 composition proof bodies are byte-preserved after removing
only their module/import headers. Public qualified names remain unchanged.
`FepSketches.fep_all` is an import-only compatibility aggregate; composition
leaves import the families they actually reference.

The canonical generator's `--check` covers every shard and the aggregate.
Controls reject missing, tampered, unexpected and symlinked outputs. Formalism
audit receipts name each declaration's real family module; source ownership and
required distribution resources include the same manifest-derived shard roster.

## Local incremental observation

The baseline is main `b3e21f6690a22a98cc68b609a818817247fd6868`.
Both measurements used Lean 4.35.0, the pinned Mathlib cache, and the default
`FepSketches` target with warning failures enabled. After a warm control, the
canonical generator temporarily received one extra public `True` witness in
`fep-001`. Existing declarations were unchanged. The generator restored every
candidate byte afterward and the restored build passed. The witness is absent
from the delivered source.

| Observation | Before shards | With shards |
| --- | ---: | ---: |
| Warm control, seconds | 6.200 | 6.289 |
| One-topic public witness, seconds | 26.765 | 18.858 |
| Rebuilt topic/composition modules | 19 | 10 |
| Restored build, seconds | 20.262 | 14.431 |

These are single local elapsed-time observations with build logs and source
hashes, not a repeated or cross-machine performance benchmark. A comment-only
probe does not change the public interface and is not used for this comparison.
The retained [evidence](evidence/) binds the exact measurement inputs and body
preservation. Later documentation changes do not replace that measured snapshot.

## Evidence boundary

Compilation and body preservation establish this software refactor only.
Historical H3, Q5/Q6/Q7, capture, GNN and scientific receipts retain their exact
source epochs. New current software receipts and hosted qualification are
required for publication; this change does not promote historical native or
production claims.
