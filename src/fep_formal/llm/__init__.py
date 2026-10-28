"""llm — LLM integration for FEP theorem explanation and Lean sketch refinement.

Uses the OpenRouter / Anthropic API (via stdlib ``urllib`` only) to drive structured
conversations that explain proof strategies and refine Lean 4 sketches.

HTTP **429** responses and **transient** transport failures (including chunked-body
``IncompleteRead``, ``URLError``, and low-level socket errors) are retried on the
current model with bounded exponential backoff before advancing the fallback chain;
see ``HERMES_429_MAX_RETRIES`` and ``HERMES_NETWORK_MAX_RETRIES`` in
``llm/hermes.py`` and ``docs/configuration.md``.

Public API
----------
    HermesConfig      — configuration dataclass (env vars + settings.yaml)
    HermesExplainer   — main explainer class
    HermesResult      — structured result dataclass
    HermesAPIError    — HTTP / network failure (optional ``.status_code``, ``.transient``)
"""

from fep_formal.llm.hermes import (
    HermesAPIError,
    HermesConfig,
    HermesExplainer,
    HermesResult,
)

__all__ = ["HermesAPIError", "HermesConfig", "HermesExplainer", "HermesResult"]
