# Packaged catalogue data

`topics.yaml` is the wheel-readable, byte-identical projection of the checkout
`config/topics.yaml`. It is generated from metadata, theorem maturity, the
validated novelty ledger, and canonical family-owned Lean bodies; never edit it
by hand.

`FEPTopicCatalogue.default()` reads this resource through `importlib.resources`
so the installed package does not depend on the source checkout.

## Freshness boundary (SC-40)

Byte-identity between this packaged copy and `config/topics.yaml` is enforced
at write time by the generator and in CI (`_maint_build_topics_catalogue.py
--check`), but there is **no runtime drift probe**: `FEPTopicCatalogue.default()`
trusts the packaged bytes as loaded. Outside a checkout, a stale packaged copy
is invisible to the catalogue loader — checkout-as-truth remains the model,
and the CI check is the only freshness guarantee.
