# `fep_formal.llm`

This package owns FEP_Formal's provider-facing Hermes client. It uses the
standard-library HTTP stack and returns structured `HermesResult` values.
Importing it reads no credentials and makes no request; explicit client
operations perform bounded provider calls.

## Public API

```python
from fep_formal.llm import (
    HermesAPIError,
    HermesConfig,
    HermesExplainer,
    HermesResult,
)
```

`HermesConfig.from_settings(project_root)` resolves provider URL, model,
budgets, fallbacks, cache lifetime, and credentials. Environment variables
override checkout settings. The optional `GAUSS_HOME/.env` reader accepts only
an explicit allowlist and never overrides an existing environment value.
Its default hydration can fill missing process-environment values;
`hydrate_environment=False` uses a private effective mapping for read-only
configuration inspection. Neither configuration path sends a provider request.

`HermesExplainer.explain_topic(topic, preamble=...)` returns a result containing
the explanation, refined Lean block, reasoning text, model, token count,
duration, error, topic ID, and cache flag. A disabled or credential-free client
returns a structured failure without making a request.

## Failure policy

- Provider-key and base-URL affinity is checked before transmission.
- HTTP 429 and transient network failures use bounded same-model retries, then
  advance through the configured fallback chain.
- A wall-clock deadline bounds the whole response, not only individual socket
  operations.
- Non-retryable client errors disable the shared configuration for the
  remainder of the run and preserve an actionable error.
- Response parsing never treats an absent/empty completion as success.

The active primary model and fallback sequence are runtime configuration, not
documentation constants. Inspect `config/settings.yaml` and
`HermesConfig.from_settings()` when reviewing a live run.

## Evidence boundary

Hermes success alone is not theorem verification. `GaussRunner` records whether
the returned Lean source compiled cleanly and which source was finally
verified. Only an independently validated complete full-mode report can support
a live-provider manuscript claim.

See [AGENTS.md](AGENTS.md), [Hermes operations](../../../docs/hermes.md), and
[configuration](../../../docs/configuration.md).
