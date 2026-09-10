"""No-direct execution tests for Hermes error paths: preflight + fallback_models chain.

Uses ``pytest-httpserver`` to run a real local HTTP server speaking the
OpenAI-compatible ``/chat/completions`` contract.  The ``HermesExplainer``
makes real HTTP calls against ``http://127.0.0.1:<port>/`` — no direct execution, no
network dependencies.

Covers:
    * ``HermesExplainer.preflight()`` returning False and disabling the
      config on HTTP 403 (OpenRouter "Key limit exceeded" scenario).
    * ``HermesExplainer.preflight()`` returning True on HTTP 200.
    * ``_build_model_chain`` preferring ``HermesConfig.fallback_models``
      over the built-in ``_FREE_MODEL_CHAIN`` and actually using the
      fallback when the primary model returns 429.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest
from pytest_httpserver import HTTPServer

from fep_lean.catalogue.topics import FEPTopicCatalogue
from fep_lean.llm.hermes import (
    _FREE_MODEL_CHAIN,
    HermesConfig,
    HermesExplainer,
)

PROJ = Path(__file__).resolve().parent.parent
TOPICS = FEPTopicCatalogue.from_yaml(PROJ / "config" / "topics.yaml")
FIRST_TOPIC = TOPICS.topics[0]


def _openrouter_like_url(httpserver: HTTPServer) -> str:
    """Loopback httpserver base for the OpenRouter-shape 429/fallback test.

    OpenRouter treatment (multi-model fallback chain) is enabled per-test by
    monkeypatching ``_build_model_chain`` instead of embedding "openrouter.ai"
    in the host, so the suite never depends on external DNS (nip.io) or any
    external name resolution.
    """
    return httpserver.url_for("/api/v1").rstrip("/")


def _local_url(httpserver: HTTPServer) -> str:
    """Plain local URL (no openrouter.ai in host => single-model chain)."""
    return httpserver.url_for("/").rstrip("/")


# ── preflight ────────────────────────────────────────────────────────────────


def test_preflight_allows_run_on_200(httpserver: HTTPServer) -> None:
    """200 response => preflight returns True, cfg.enabled stays True."""
    httpserver.expect_request("/chat/completions", method="POST").respond_with_json(
        {
            "choices": [{"message": {"content": "pong"}}],
            "usage": {"total_tokens": 1},
        }
    )
    cfg = HermesConfig(
        model="test/model",
        base_url=_local_url(httpserver),
        api_key="sk-test-123",
        enabled=True,
    )
    exp = HermesExplainer(cfg)
    assert exp.preflight() is True
    assert cfg.enabled is True


def test_preflight_disables_hermes_on_403(
    httpserver: HTTPServer, caplog: pytest.LogCaptureFixture
) -> None:
    """403 => preflight returns False, cfg.enabled flipped, actionable log."""
    httpserver.expect_request("/chat/completions", method="POST").respond_with_data(
        json.dumps(
            {"error": {"message": "Key limit exceeded (total limit)", "code": 403}}
        ),
        status=403,
        content_type="application/json",
    )
    cfg = HermesConfig(
        model="test/model",
        base_url=_local_url(httpserver),
        api_key="sk-test-403",
        enabled=True,
    )
    exp = HermesExplainer(cfg)
    with caplog.at_level(logging.ERROR, logger="fep_lean.llm.hermes"):
        ok = exp.preflight()
    assert ok is False
    assert cfg.enabled is False
    joined = "\n".join(r.message for r in caplog.records)
    assert "openrouter.ai/settings/keys" in joined
    assert "HERMES_API_BASE" in joined
    assert "ANTHROPIC_API_KEY" in joined


def test_preflight_noop_when_disabled() -> None:
    """Already-disabled config must short-circuit (no HTTP call needed)."""
    cfg = HermesConfig(enabled=False, api_key="whatever")
    assert HermesExplainer(cfg).preflight() is True


def test_preflight_noop_when_keyless() -> None:
    """No API key => nothing to probe, return True."""
    cfg = HermesConfig(enabled=True, api_key="")
    assert HermesExplainer(cfg).preflight() is True


def test_preflight_tolerates_5xx(httpserver: HTTPServer) -> None:
    """5xx is not credential-fatal: return True and let per-topic retry handle it."""
    httpserver.expect_request("/chat/completions", method="POST").respond_with_data(
        "upstream error", status=503, content_type="text/plain"
    )
    cfg = HermesConfig(
        model="test/model",
        base_url=_local_url(httpserver),
        api_key="sk-test-5xx",
        enabled=True,
    )
    exp = HermesExplainer(cfg)
    assert exp.preflight() is True
    assert cfg.enabled is True


def test_preflight_bounds_reasoning_model_and_restores_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cfg = HermesConfig(
        model="moonshotai/kimi-k2.6",
        api_key="sk-test",
        max_tokens=100,
        timeout_s=60,
        reasoning_max_tokens=999,
        reasoning_timeout_s=90,
    )
    seen: list[tuple[int, int] | None] = []
    exp = HermesExplainer(cfg)

    def fake_call(_messages, _model, budgets=None):
        seen.append(budgets)
        return {"choices": []}

    monkeypatch.setattr(exp, "_call_api", fake_call)
    assert exp.preflight() is True
    # Probe budgets are passed per call: 1 token, capped at 30 s.
    assert seen == [(1, 30)]
    # The shared config budgets are never mutated.
    assert (
        cfg.max_tokens,
        cfg.reasoning_max_tokens,
        cfg.timeout_s,
        cfg.reasoning_timeout_s,
    ) == (100, 999, 60, 90)


# ── fallback_models ──────────────────────────────────────────────────────────


def test_build_model_chain_prefers_user_fallbacks() -> None:
    """When fallback_models is non-empty, the built-in chain is ignored."""
    cfg = HermesConfig(
        model="primary/model",
        base_url="https://openrouter.ai/api/v1",
        api_key="sk-or-test",
        fallback_models=["user/fb-a", "user/fb-b"],
    )
    chain = HermesExplainer(cfg)._build_model_chain()
    assert chain[0] == "primary/model"
    assert chain[1:] == ["user/fb-a", "user/fb-b"]
    assert not any(m in chain for m in _FREE_MODEL_CHAIN if m != "primary/model")


def test_build_model_chain_defaults_to_free_chain_when_unset() -> None:
    """Empty fallback_models => built-in _FREE_MODEL_CHAIN is appended."""
    cfg = HermesConfig(
        model="primary/model",
        base_url="https://openrouter.ai/api/v1",
        api_key="sk-or-test",
        fallback_models=[],
    )
    chain = HermesExplainer(cfg)._build_model_chain()
    assert chain[0] == "primary/model"
    for m in _FREE_MODEL_CHAIN:
        if m != "primary/model":
            assert m in chain


def test_build_model_chain_single_for_anthropic() -> None:
    """Anthropic-direct endpoint ignores fallback chain."""
    cfg = HermesConfig(
        model="claude-3-5-sonnet-20240620",
        base_url="https://api.anthropic.com/v1",
        api_key="sk-ant-test",
        fallback_models=["should/be-ignored"],
    )
    chain = HermesExplainer(cfg)._build_model_chain()
    assert chain == ["claude-3-5-sonnet-20240620"]


def test_fallback_models_used_when_primary_returns_429(
    httpserver: HTTPServer,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Primary model returns 429 (exhausted), fallback model returns 200.

    Uses a loopback httpserver; the OpenRouter fallback-chain shape is
    enabled by monkeypatching ``_build_model_chain`` instead of embedding
    "openrouter.ai" in the host, so the test never needs external DNS.
    Two ordered handlers match POST /api/v1/chat/completions:
    first with model=primary/model → 429, second with model=user/fb-a → 200.
    """

    def _match_model(want: str):
        def _matcher(request) -> bool:
            try:
                body = json.loads(request.get_data(as_text=True) or "{}")
            except json.JSONDecodeError:
                return False
            return body.get("model") == want

        return _matcher

    httpserver.expect_ordered_request(
        "/api/v1/chat/completions", method="POST"
    ).respond_with_data(
        json.dumps({"error": {"message": "Rate limit", "code": 429}}),
        status=429,
        content_type="application/json",
    )
    httpserver.expect_ordered_request(
        "/api/v1/chat/completions", method="POST"
    ).respond_with_json(
        {
            "choices": [
                {
                    "message": {
                        "content": "Explanation.\n\n```lean\ntheorem t : True := trivial\n```",
                    }
                }
            ],
            "usage": {"total_tokens": 42},
            "model": "user/fb-a",
        }
    )

    cfg = HermesConfig(
        model="primary/model",
        base_url=_openrouter_like_url(httpserver),
        api_key="sk-or-test",
        fallback_models=["user/fb-a"],
        timeout_s=5,
    )
    exp = HermesExplainer(cfg)
    # Enable the OpenRouter fallback-chain shape on a loopback base_url:
    # without "openrouter.ai" in the host the chain would be single-model.
    monkeypatch.setattr(
        HermesExplainer,
        "_build_model_chain",
        lambda self: ["primary/model", "user/fb-a"],
    )
    # Patch the 429 retry count to 0 so we advance to the fallback quickly.
    monkeypatch.setenv("HERMES_429_MAX_RETRIES", "0")
    result = exp.explain_topic(FIRST_TOPIC)
    assert result.success is True, result.error
    assert result.model_used == "user/fb-a"
    assert "theorem t" in (result.refined_lean_sketch or "")
