# FEP_Formal packaged data

These YAML resources let the installed package load the catalogue and portable
methods inputs without relying on a checkout.

- `topics.yaml` is the byte-identical generated projection of
  `config/topics.yaml`. Its canonical metadata, semantic review, novelty ledger
  and family-owned bodies are joined by
  [`_maint_build_topics_catalogue.py`](../../../scripts/_maint_build_topics_catalogue.py).
- The remaining portable methods inputs are exact copies of maintained
  configuration and positioning policy. Their complete owner mapping is
  `RESOURCES` in
  [`generate_package_methods.py`](../../../specs/openai-math-methods/generate_package_methods.py).

Use each generator's `--check` mode to inspect freshness. Never edit a package
copy to hide drift in its canonical input.

`FEPTopicCatalogue.default()` validates the packaged catalogue it reads; it does
not compare it with an external checkout. Generator checks establish that
checkout/package byte parity at a named source epoch. Methods analysis has its
own source/runtime consistency checks, described in the
[methods contract](../methods/AGENTS.md). Schema validity, projection freshness
and native evidence remain separate facts.
