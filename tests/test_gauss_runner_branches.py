"""Controlled Hermes/error branches and one serialized real-Lean review fixture."""

from __future__ import annotations

from pathlib import Path

import pytest

from fep_lean.catalogue.topics import FEPTopicCatalogue, TopicEntry
from fep_lean.gauss import runner as runner_module
from fep_lean.gauss.client import OpenGaussClient
from fep_lean.gauss.runner import GaussRunner
from fep_lean.llm.hermes import HermesConfig, HermesExplainer, HermesResult
from fep_lean.verification.lean_verifier import LeanVerifier, VerifyResult

PROJ = Path(__file__).resolve().parent.parent


class FixedHermes(HermesExplainer):
    """Returns a fixed result without HTTP (overrides ``explain_topic`` only)."""

    def __init__(self, result: HermesResult) -> None:
        super().__init__(HermesConfig(enabled=True, api_key="test-key-not-used"))
        self._fixed = result

    def explain_topic(
        self,
        topic: TopicEntry,
        *,
        preamble: str = "",
        request_lean: bool = True,
    ) -> HermesResult:
        return self._fixed


class BoomClient(OpenGaussClient):
    def create_session(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        raise RuntimeError("simulated session failure")


def _topic() -> TopicEntry:
    c = FEPTopicCatalogue.from_yaml(PROJ / "config" / "topics.yaml")
    return c.topics[0]


def test_run_topic_no_refined_sketch(tmp_path: Path) -> None:
    lean = LeanVerifier(PROJ / "lean", PROJ)
    hermes = FixedHermes(
        HermesResult(
            success=True,
            model_used="fixture",
            explanation="ok",
            refined_lean_sketch="",
            topic_id="x",
        )
    )
    client = OpenGaussClient(gauss_home=tmp_path / "g")
    runner = GaussRunner(lean, hermes, client, PROJ)
    r = runner.run_topic(_topic())
    assert r.status == "no_lean_sketch"
    assert r.success is False


@pytest.mark.serial_lean
def test_run_topic_with_reasoning_turn(tmp_path: Path) -> None:
    lean = LeanVerifier(PROJ / "lean", PROJ)
    sketch = "theorem fixtureReason : True := True.intro\n"
    hermes = FixedHermes(
        HermesResult(
            success=True,
            model_used="fixture",
            explanation="e",
            refined_lean_sketch=sketch,
            reasoning="internal chain",
            tokens_used=3,
            topic_id="x",
        )
    )
    client = OpenGaussClient(gauss_home=tmp_path / "g")
    runner = GaussRunner(lean, hermes, client, PROJ)
    r = runner.run_topic(_topic())
    assert r.topic_id == _topic().id
    assert r.hermes_success is True


def test_run_topics_batch_catches_runner_exception(tmp_path: Path) -> None:
    lean = LeanVerifier(PROJ / "lean", PROJ)
    hermes = HermesExplainer(HermesConfig(enabled=False))
    client = BoomClient(gauss_home=tmp_path / "g")
    runner = GaussRunner(lean, hermes, client, PROJ)
    t = _topic()
    out = runner.run_topics_batch([t])
    assert len(out) == 1
    assert out[0].success is False
    assert "Unhandled runner exception" in out[0].error


def test_run_topic_closes_session_after_unexpected_error(tmp_path: Path) -> None:
    lean = LeanVerifier(PROJ / "lean", PROJ)
    hermes = HermesExplainer(HermesConfig(enabled=False))
    client = OpenGaussClient(gauss_home=tmp_path / "g")
    runner = GaussRunner(lean, hermes, client, PROJ)

    def explode(*_args, **_kwargs):
        raise RuntimeError("injected failure after session creation")

    runner._record_hermes_turns = explode  # type: ignore[method-assign]
    with pytest.raises(RuntimeError, match="injected failure"):
        runner.run_topic(_topic())
    rows = client._conn.execute("SELECT status FROM sessions").fetchall()
    assert [row["status"] for row in rows] == ["error"]


# ── Explicit workflow selection tests ────────────────────────────────────────


def test_workflow_draft_preserves_requested_stage(tmp_path: Path) -> None:
    lean = LeanVerifier(PROJ / "lean", PROJ)
    hermes = FixedHermes(
        HermesResult(success=False, model_used="fixture", topic_id="fep-001")
    )
    client = OpenGaussClient(gauss_home=tmp_path / "g")
    runner = GaussRunner(lean, hermes, client, PROJ)
    result = runner.run_topic(_topic(), workflow="draft")
    assert result.workflow == "draft"


def test_workflow_prove_preserves_requested_stage(tmp_path: Path) -> None:
    lean = LeanVerifier(PROJ / "lean", PROJ)
    hermes = FixedHermes(
        HermesResult(success=False, model_used="fixture", topic_id="fep-001")
    )
    client = OpenGaussClient(gauss_home=tmp_path / "g")
    runner = GaussRunner(lean, hermes, client, PROJ)
    result = runner.run_topic(_topic(), workflow="prove")
    assert result.workflow == "prove"


# ── Hermes caching tests ──────────────────────────────────────────────────────


class _CountingHermes(HermesExplainer):
    """Hermes fixture that counts calls and returns a compile-clean sketch."""

    def __init__(self) -> None:
        self._cfg = HermesConfig(enabled=False, api_key="")
        self.call_count = 0

    def explain_topic(
        self,
        topic: TopicEntry,
        *,
        preamble: str = "",
        request_lean: bool = True,
    ) -> HermesResult:
        self.call_count += 1
        return HermesResult(
            success=True,
            model_used="fixture",
            explanation="fixture explanation",
            refined_lean_sketch=topic.lean_sketch if request_lean else "",
            topic_id=topic.id,
        )


class _PreambleAwareHermes(HermesExplainer):
    """Obey the stage directive exactly, exposing contradictory prompt order."""

    def __init__(self) -> None:
        super().__init__(HermesConfig(enabled=True, api_key="test-key-not-used"))
        self.preambles: list[str] = []
        self.requests_lean: list[bool] = []
        self.sketches: list[str] = []

    def explain_topic(
        self,
        topic: TopicEntry,
        *,
        preamble: str = "",
        request_lean: bool = True,
    ) -> HermesResult:
        self.preambles.append(preamble)
        self.requests_lean.append(request_lean)
        self.sketches.append(topic.lean_sketch)
        if not request_lean:
            return HermesResult(
                success=True,
                model_used="fixture",
                explanation="The already-compiled theorem is clear.",
                refined_lean_sketch="",
                topic_id=topic.id,
            )
        return HermesResult(
            success=True,
            model_used="fixture",
            explanation="Refined theorem.",
            refined_lean_sketch=topic.lean_sketch,
            topic_id=topic.id,
        )


@pytest.mark.serial_lean
def test_run_topic_uses_cache_on_second_call(tmp_path: Path) -> None:
    """Second identical run returns from SQLite cache; explain_topic called only once."""
    lean = LeanVerifier(PROJ / "lean", PROJ)
    hermes = _CountingHermes()
    client = OpenGaussClient(gauss_home=tmp_path / "g")
    runner = GaussRunner(lean, hermes, client, PROJ)
    topic = _topic()

    runner.run_topic(topic)
    runner.run_topic(topic)

    assert hermes.call_count == 1


def test_prompt_change_invalidates_the_hermes_cache(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    lean = LeanVerifier(PROJ / "lean", PROJ)
    monkeypatch.setattr(lean, "check_lake_available", lambda: True)
    monkeypatch.setattr(
        lean,
        "verify_sketch",
        lambda topic_id, _sketch: VerifyResult(
            topic_id=topic_id,
            compiles=True,
            has_sorry=False,
        ),
    )
    hermes = _CountingHermes()
    runner = GaussRunner(
        lean,
        hermes,
        OpenGaussClient(gauss_home=tmp_path / "g"),
        PROJ,
    )
    topic = _topic()

    runner.run_topic(topic)
    monkeypatch.setitem(
        runner_module._WORKFLOW_PREAMBLES,
        "verify",
        "TASK: Return the same Lean contract with this changed prompt.",
    )
    runner.run_topic(topic)

    assert hermes.call_count == 2


def test_stage_results_empty_for_verify(tmp_path: Path) -> None:
    """verify workflow always produces an empty stage_results list."""
    lean = LeanVerifier(PROJ / "lean", PROJ)
    hermes = FixedHermes(
        HermesResult(success=False, model_used="fixture", topic_id="fep-001")
    )
    client = OpenGaussClient(gauss_home=tmp_path / "g")
    runner = GaussRunner(lean, hermes, client, PROJ)
    result = runner.run_topic(_topic(), workflow="verify")
    assert result.stage_results == []


# ── Review workflow stage_results test ───────────────────────────────────────


@pytest.mark.serial_lean
def test_run_topic_review_workflow_populates_stage_results(tmp_path: Path) -> None:
    """workflow='review' appends a 'review_commentary' entry to stage_results
    when the refined sketch compiles successfully."""
    lean = LeanVerifier(PROJ / "lean", PROJ)
    # A sketch that will compile so verify_res.compiles is True (triggers review pass)
    hermes = _CountingHermes()

    client = OpenGaussClient(gauss_home=tmp_path / "g")
    runner = GaussRunner(lean, hermes, client, PROJ)
    if not runner.lean.check_lake_available():
        pytest.skip("pinned Lake is unavailable")
    result = runner.run_topic(_topic(), workflow="review")

    assert result.workflow == "review"
    assert len(result.stage_results) == 1
    assert result.stage_results[0]["stage"] == "review_commentary"
    assert "success" in result.stage_results[0]
    # Review Hermes call is also cached — first call was verify, second is review_commentary
    assert hermes.call_count == 2


def test_review_refines_before_requesting_commentary(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The first review turn must still request Lean; commentary comes second."""
    lean = LeanVerifier(PROJ / "lean", PROJ)
    monkeypatch.setattr(lean, "check_lake_available", lambda: True)
    monkeypatch.setattr(
        lean,
        "verify_sketch",
        lambda topic_id, _sketch: VerifyResult(
            topic_id=topic_id,
            compiles=True,
            has_sorry=False,
        ),
    )
    hermes = _PreambleAwareHermes()
    client = OpenGaussClient(gauss_home=tmp_path / "g")
    runner = GaussRunner(lean, hermes, client, PROJ)

    result = runner.run_topic(_topic(), workflow="review")

    assert result.success is True
    assert len(hermes.preambles) == 2
    assert "Do NOT produce a new ```lean block" not in hermes.preambles[0]
    assert "Do NOT produce a new ```lean block" in hermes.preambles[1]
    assert hermes.requests_lean == [True, False]
    assert hermes.sketches[1] == result.refined_lean_sketch
    turns = client.export_session(result.session_id)["turns"]
    assert [turn["turn_index"] for turn in turns] == list(range(len(turns)))
    assert [turn["role"] for turn in turns].count("system") == 2
    review_turns = turns[-2:]
    assert [turn["role"] for turn in review_turns] == ["user", "assistant"]
    assert result.refined_lean_sketch in review_turns[0]["content"]
    assert "without rewriting" in review_turns[0]["content"]


def test_run_topic_fails_closed_when_provider_weakens_canonical_lean(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    lean = LeanVerifier(PROJ / "lean", PROJ)
    monkeypatch.setattr(lean, "check_lake_available", lambda: True)
    monkeypatch.setattr(
        lean,
        "verify_sketch",
        lambda topic_id, _sketch: VerifyResult(
            topic_id=topic_id,
            compiles=True,
            has_sorry=False,
        ),
    )
    hermes = FixedHermes(
        HermesResult(
            success=True,
            model_used="fixture",
            explanation="I weakened the theorem.",
            refined_lean_sketch=(
                "namespace FEP001\n"
                "theorem fep001_variationalUpperBound_eq_iff : True := True.intro\n"
                "end FEP001\n"
            ),
            topic_id="fep-001",
        )
    )
    runner = GaussRunner(
        lean,
        hermes,
        OpenGaussClient(gauss_home=tmp_path / "g"),
        PROJ,
    )

    result = runner.run_topic(_topic(), workflow="verify")

    assert result.success is False
    assert result.semantic_contract_preserved is False
    assert result.hermes_lean_compiles is False
    assert result.verification_source == "canonical_semantic_fallback"
    assert "non-comment Lean token contract" in result.error


def test_review_commentary_failure_fails_requested_workflow(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    class ReviewFailureHermes(_PreambleAwareHermes):
        def explain_topic(
            self,
            topic: TopicEntry,
            *,
            preamble: str = "",
            request_lean: bool = True,
        ) -> HermesResult:
            if not request_lean or "Do NOT produce" in preamble:
                self.preambles.append(preamble)
                self.requests_lean.append(request_lean)
                self.sketches.append(topic.lean_sketch)
                return HermesResult(
                    success=False,
                    model_used="fixture",
                    error="review transport failed",
                    topic_id=topic.id,
                )
            return super().explain_topic(
                topic, preamble=preamble, request_lean=request_lean
            )

    lean = LeanVerifier(PROJ / "lean", PROJ)
    monkeypatch.setattr(lean, "check_lake_available", lambda: True)
    monkeypatch.setattr(
        lean,
        "verify_sketch",
        lambda topic_id, _sketch: VerifyResult(
            topic_id=topic_id,
            compiles=True,
            has_sorry=False,
        ),
    )
    runner = GaussRunner(
        lean,
        ReviewFailureHermes(),
        OpenGaussClient(gauss_home=tmp_path / "g"),
        PROJ,
    )

    result = runner.run_topic(_topic(), workflow="review")

    assert result.success is False
    assert result.stage_results[0]["error"] == "review transport failed"
    assert result.error == "review transport failed"


def test_review_commentary_rejects_a_prose_stage_lean_rewrite(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    class RewritingReviewHermes(_PreambleAwareHermes):
        def explain_topic(
            self,
            topic: TopicEntry,
            *,
            preamble: str = "",
            request_lean: bool = True,
        ) -> HermesResult:
            result = super().explain_topic(
                topic,
                preamble=preamble,
                request_lean=request_lean,
            )
            if not request_lean:
                result.refined_lean_sketch = (
                    "theorem forbiddenReviewRewrite : True := True.intro\n"
                )
            return result

    lean = LeanVerifier(PROJ / "lean", PROJ)
    monkeypatch.setattr(lean, "check_lake_available", lambda: True)
    monkeypatch.setattr(
        lean,
        "verify_sketch",
        lambda topic_id, _sketch: VerifyResult(
            topic_id=topic_id,
            compiles=True,
            has_sorry=False,
        ),
    )
    runner = GaussRunner(
        lean,
        RewritingReviewHermes(),
        OpenGaussClient(gauss_home=tmp_path / "g"),
        PROJ,
    )

    result = runner.run_topic(_topic(), workflow="review")

    assert result.success is False
    assert "prose-only" in result.stage_results[0]["error"]
    assert "forbiddenReviewRewrite" not in result.final_lean_sketch


def test_compiler_warning_is_a_strict_topic_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    lean = LeanVerifier(PROJ / "lean", PROJ)
    monkeypatch.setattr(lean, "check_lake_available", lambda: True)
    monkeypatch.setattr(
        lean,
        "verify_sketch",
        lambda topic_id, _sketch: VerifyResult(
            topic_id=topic_id,
            compiles=True,
            has_sorry=False,
            warnings=["fixture.lean:1:0: warning: declaration uses 'sorry'"],
        ),
    )
    client = OpenGaussClient(gauss_home=tmp_path / "g")
    runner = GaussRunner(lean, _CountingHermes(), client, PROJ)

    result = runner.run_topic(_topic())

    assert result.success is False
    assert result.status == "failed"
    assert result.lean_warnings == [
        "fixture.lean:1:0: warning: declaration uses 'sorry'"
    ]
    assert "warning" in result.error


def test_review_commentary_is_not_requested_for_warning_bearing_lean(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    lean = LeanVerifier(PROJ / "lean", PROJ)
    monkeypatch.setattr(lean, "check_lake_available", lambda: True)
    monkeypatch.setattr(
        lean,
        "verify_sketch",
        lambda topic_id, _sketch: VerifyResult(
            topic_id=topic_id,
            compiles=True,
            has_sorry=False,
            warnings=["fixture.lean:1:0: warning: declaration uses 'sorry'"],
        ),
    )
    hermes = _PreambleAwareHermes()
    runner = GaussRunner(
        lean,
        hermes,
        OpenGaussClient(gauss_home=tmp_path / "g"),
        PROJ,
    )

    result = runner.run_topic(_topic(), workflow="review")

    assert result.success is False
    assert result.stage_results == []
    assert hermes.requests_lean == [True]


# ── Error capture tests ──────────────────────────────────────────────────────


@pytest.mark.serial_lean
def test_topic_run_result_error_uses_skip_reason_when_errors_empty(
    tmp_path: Path,
) -> None:
    """When verify_res.errors is empty but compilation fails (timeout/no-lake),
    the runner must populate error from skip_reason or stdout rather than empty string."""
    lean = LeanVerifier(PROJ / "lean", PROJ)
    hermes = _CountingHermes()
    client = OpenGaussClient(gauss_home=tmp_path / "g")
    runner = GaussRunner(lean, hermes, client, PROJ)

    topic = _topic()
    result = runner.run_topic(topic)

    # The result should have a non-empty error string when lean_compiles is False
    if not result.lean_compiles:
        assert result.error != "", (
            "TopicRunResult.error must be non-empty when lean compilation fails; "
            "got empty string — check runner.py error fallback chain"
        )
