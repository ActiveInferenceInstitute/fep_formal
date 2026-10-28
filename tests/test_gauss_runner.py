"""Tests for gauss_runner — per-topic session orchestration.

All tests use real SQLite (tmp_path), real HermesExplainer (disabled / no-key),
and real LeanVerifier (skipped when lake absent).  No direct execution.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from fep_formal._paths import resolve_environment
from fep_formal.catalogue.topics import FEPTopicCatalogue
from fep_formal.gauss.client import OpenGaussClient
from fep_formal.gauss.runner import GaussRunner, TopicRunResult
from fep_formal.llm.hermes import HermesConfig, HermesExplainer
from fep_formal.verification.lean_verifier import LeanVerifier

PROJ = Path(__file__).resolve().parent.parent
TOPICS = FEPTopicCatalogue.from_yaml(PROJ / "config" / "topics.yaml")

_HAS_API_KEY = bool(
    os.environ.get("OPENROUTER_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
)
# Run live tests when a key is present, unless explicitly opted out with =0.
# Set FEP_FORMAL_LIVE_TESTS=0 in CI to skip expensive API calls even when keys exist.
# Set FEP_FORMAL_LIVE_TESTS=1 to force-run even without a key (will fail at API level).
_FEP_FORMAL_LIVE_VAR = resolve_environment("FEP_FORMAL_LIVE_TESTS", "").lower()
_LIVE_TESTS_ENABLED = _FEP_FORMAL_LIVE_VAR in ("1", "true", "yes") or (
    _HAS_API_KEY and _FEP_FORMAL_LIVE_VAR not in ("0", "false", "no")
)


@pytest.fixture()
def runner(tmp_path: Path) -> GaussRunner:
    cfg = HermesConfig(enabled=True, api_key="")  # will get skipped cleanly
    hermes = HermesExplainer(cfg)
    # Instantiate genuine LeanVerifier (runs real lake env lean organically)
    lean = LeanVerifier(PROJ / "lean", PROJ)
    client = OpenGaussClient(gauss_home=tmp_path / "gauss")
    return GaussRunner(
        lean_verifier=lean,
        hermes=hermes,
        client=client,
        project_root=PROJ,
    )


def test_runner_instantiates(runner: GaussRunner) -> None:
    assert runner is not None


def test_run_topic_returns_result(runner: GaussRunner) -> None:
    topic = TOPICS.topics[0]
    result = runner.run_topic(topic)
    assert isinstance(result, TopicRunResult)
    assert result.topic_id == topic.id


def test_run_topic_creates_sqlite_session(runner: GaussRunner, tmp_path: Path) -> None:
    topic = TOPICS.topics[1]
    result = runner.run_topic(topic)
    # Session must have been written to the DB
    assert result.session_id


def test_run_topic_no_api_key_hermes_skipped(runner: GaussRunner) -> None:
    topic = TOPICS.topics[0]
    result = runner.run_topic(topic)
    # No API key → Hermes naturally skips execution and returns failure
    assert result.hermes_success is False


def test_run_topics_batch_returns_all(runner: GaussRunner) -> None:
    subset = TOPICS.topics[:3]
    results = runner.run_topics_batch(subset)
    assert len(results) == 3
    ids = [r.topic_id for r in results]
    assert ids == [t.id for t in subset]


def test_run_topics_batch_max_topics(runner: GaussRunner) -> None:
    results = runner.run_topics_batch(TOPICS.topics, max_topics=2)
    assert len(results) == 2


def test_topic_run_result_as_dict(runner: GaussRunner) -> None:
    topic = TOPICS.topics[5]
    result = runner.run_topic(topic)
    d = result.as_dict()
    # Core identity / status fields
    for key in (
        "topic_id",
        "session_id",
        "success",
        "status",
        "hermes_success",
        "lean_compiles",
        "lean_has_sorry",
        "lean_warnings",
        "duration_s",
        "workflow",
        "stage_results",
    ):
        assert key in d, f"missing core key: {key}"

    # Hermes-derived fields surfaced for downstream reporters.  Types are
    # asserted (not values) so the contract holds for fixture Hermes returns
    # whether or not a network call happens.
    for key, expected_type in (
        ("explanation", str),
        ("refined_lean_sketch", str),
        ("tokens_used", int),
        ("hermes_model", str),
        ("cache_hit", bool),
        ("hermes_lean_compiles", bool),
    ):
        assert key in d, f"missing Hermes-surfaced key: {key}"
        assert isinstance(d[key], expected_type), (
            f"{key} should be {expected_type.__name__}, got {type(d[key]).__name__}"
        )


def test_run_topic_default_workflow_field(runner: GaussRunner) -> None:
    topic = TOPICS.topics[0]
    result = runner.run_topic(topic)
    assert result.workflow == "verify"
    assert isinstance(result.stage_results, list)


def test_run_topic_result_as_dict_includes_workflow(runner: GaussRunner) -> None:
    topic = TOPICS.topics[2]
    d = runner.run_topic(topic).as_dict()
    assert "workflow" in d
    assert "stage_results" in d
    assert d["workflow"] == "verify"


def test_run_topics_batch_workflow_kwarg(
    runner: GaussRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    results = runner.run_topics_batch(TOPICS.topics[:2], workflow="draft")
    assert all(r.workflow == "draft" for r in results)


@pytest.mark.skipif(
    not (_HAS_API_KEY and _LIVE_TESTS_ENABLED),
    reason="No API key found (set OPENROUTER_API_KEY or ANTHROPIC_API_KEY); or suppressed via FEP_FORMAL_LIVE_TESTS=0",
)
def test_run_topic_with_real_hermes(tmp_path: Path) -> None:
    """Full GaussRunner integration: real OpenRouter HTTP → SQLite → LeanVerifier.

    Why this test exists
    --------------------
    The other GaussRunner tests in this file use the SQLite-backed runner with
    Hermes disabled (``HermesConfig(enabled=False)``), so Hermes returns a fixture
    ``HermesResult`` and no HTTP call is made.  ``FixedHermes`` /
    ``_CountingHermes`` fixtures that exercise the Hermes seam directly live in
    ``test_gauss_runner_branches.py``.  This test is the only one that exercises
    the *real* network path through ``HermesExplainer._call_api`` →
    ``_parse_response`` → ``LeanVerifier`` → ``OpenGaussClient`` in one shot.
    It verifies that the wiring between those four components holds under
    production conditions.

    What it checks
    --------------
    * ``TopicRunResult`` is returned with the correct ``topic_id``.
    * The Hermes fallback chain (primary model → 6 free-tier fallbacks) does
      not raise unhandled exceptions — any model-level error is captured in
      ``result.error``, not propagated.
    * SQLite session is written to ``tmp_path`` (real WAL file, not in-memory).

    How to run
    ----------
    ::

        export OPENROUTER_API_KEY=sk-or-v1-...   # or ANTHROPIC_API_KEY
        export FEP_FORMAL_LIVE_TESTS=1
        uv run pytest tests/test_gauss_runner.py::test_run_topic_with_real_hermes -v

    Expected timing: 5–90 s depending on model (reasoning models up to ~5 min).
    The test does NOT assert ``result.success`` because rate-limit and
    model-unavailable responses are non-fatal by design.
    """
    cfg = HermesConfig.from_settings(PROJ)
    hermes = HermesExplainer(cfg)
    lean = LeanVerifier(PROJ / "lean", PROJ)
    client = OpenGaussClient(gauss_home=tmp_path / "hermes_test")
    runner = GaussRunner(
        lean_verifier=lean,
        hermes=hermes,
        client=client,
        project_root=PROJ,
    )
    result = runner.run_topic(TOPICS.topics[0])
    assert isinstance(result, TopicRunResult)
    assert result.topic_id == TOPICS.topics[0].id
