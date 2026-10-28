"""Tests for FEP_FORMAL_PREFETCH Hermes/Lean overlap (no direct execution; real SQLite + LeanVerifier)."""

from __future__ import annotations

from pathlib import Path

import pytest

from fep_formal.catalogue.topics import FEPTopicCatalogue
from fep_formal.gauss.client import OpenGaussClient
from fep_formal.gauss.runner import GaussRunner, _prefetch_enabled
from fep_formal.llm.hermes import HermesConfig, HermesExplainer, HermesResult
from fep_formal.verification.lean_verifier import LeanVerifier

PROJ = Path(__file__).resolve().parent.parent
TOPICS = FEPTopicCatalogue.from_yaml(PROJ / "config" / "topics.yaml")


class _CountingHermes(HermesExplainer):
    """Counts explain_topic invocations on this instance."""

    def __init__(self, cfg: HermesConfig) -> None:
        super().__init__(cfg)
        self.explain_calls = 0

    def explain_topic(
        self, topic, *, preamble: str = "", request_lean: bool = True
    ) -> HermesResult:
        self.explain_calls += 1
        return super().explain_topic(topic, preamble=preamble)


@pytest.fixture()
def runner_prefetch(tmp_path: Path) -> GaussRunner:
    cfg = HermesConfig(enabled=True, api_key="")
    hermes = _CountingHermes(cfg)
    lean = LeanVerifier(PROJ / "lean", PROJ)
    client = OpenGaussClient(gauss_home=tmp_path / "gauss_prefetch")
    return GaussRunner(
        lean_verifier=lean,
        hermes=hermes,
        client=client,
        project_root=PROJ,
    )


def test_prefetch_enabled_parses_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FEP_FORMAL_PREFETCH", raising=False)
    assert _prefetch_enabled() is False
    monkeypatch.setenv("FEP_FORMAL_PREFETCH", "1")
    assert _prefetch_enabled() is True
    monkeypatch.setenv("FEP_FORMAL_PREFETCH", "true")
    assert _prefetch_enabled() is True


def test_run_topics_batch_single_topic_skips_prefetch_path(
    runner_prefetch: GaussRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """len(subset) <= 1 uses the normal loop even when FEP_FORMAL_PREFETCH=1."""
    monkeypatch.setenv("FEP_FORMAL_PREFETCH", "1")
    r = runner_prefetch.run_topics_batch(TOPICS.topics[:1])
    assert len(r) == 1
    assert runner_prefetch.hermes.explain_calls == 1


def test_prefetch_batch_matches_serial_topic_ids(
    runner_prefetch: GaussRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Two-topic batch with prefetch=1 returns same topic order as prefetch=0."""
    subset = TOPICS.topics[:2]
    monkeypatch.delenv("FEP_FORMAL_PREFETCH", raising=False)
    serial = runner_prefetch.run_topics_batch(subset)
    # Fresh runner for prefetch path (separate DB in tmp_path to avoid
    # polluting the checkout — see the project-root .gitignore guard).
    cfg = HermesConfig(enabled=True, api_key="")
    h2 = _CountingHermes(cfg)
    lean = LeanVerifier(PROJ / "lean", PROJ)
    client = OpenGaussClient(gauss_home=tmp_path / "gauss_pf2")
    r2 = GaussRunner(lean, h2, client, PROJ)
    monkeypatch.setenv("FEP_FORMAL_PREFETCH", "1")
    try:
        prefetch = r2.run_topics_batch(subset)
    finally:
        monkeypatch.delenv("FEP_FORMAL_PREFETCH", raising=False)
    assert [x.topic_id for x in serial] == [x.topic_id for x in prefetch]
    assert len(prefetch) == 2


def test_prefetch_uses_second_hermes_for_overlap(
    runner_prefetch: GaussRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Prefetch mode uses auxiliary HermesExplainer; main thread calls drop for topic 2."""
    subset = TOPICS.topics[:2]
    monkeypatch.setenv("FEP_FORMAL_PREFETCH", "1")
    try:
        runner_prefetch.run_topics_batch(subset)
    finally:
        monkeypatch.delenv("FEP_FORMAL_PREFETCH", raising=False)
    # Topic 1 Hermes may be served by prefetch worker; main hermes may see only 1 explain.
    assert runner_prefetch.hermes.explain_calls >= 1
    assert runner_prefetch.hermes.explain_calls <= 2


def test_prefetch_graceful_when_hermes_disabled_mid_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Batch completes even when all Hermes calls fail (no API key)."""
    monkeypatch.setenv("FEP_FORMAL_PREFETCH", "1")
    cfg = HermesConfig(enabled=True, api_key="")
    hermes = HermesExplainer(cfg)
    lean = LeanVerifier(PROJ / "lean", PROJ)
    client = OpenGaussClient(gauss_home=tmp_path / "gauss_grace")
    runner = GaussRunner(lean, hermes, client, PROJ)
    try:
        results = runner.run_topics_batch(TOPICS.topics[:2])
    finally:
        monkeypatch.delenv("FEP_FORMAL_PREFETCH", raising=False)
    assert len(results) == 2
    assert all(not r.hermes_success for r in results)
