"""Additional error-path and contract tests (no mocks, real objects).

Covers gaps found in the fep-tests coverage audit (2026-08-28):
- ``_has_sorry`` comment-blindness contract (Lean comments must not trigger sorry detection)
- ``VerifyResult.status`` timeout variant
- ``_get_timeout`` call-time env override
- ``OpenGaussClient.close_open_session`` idempotence and artifact registration integrity
- ``GaussRunner.run_topic`` hermes_error finalization
- ``run_validation_checks`` unsupported-mode rejection and full-mode failure accumulation
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from fep_lean.catalogue.topics import FEPTopicCatalogue, TopicEntry
from fep_lean.gauss.client import OpenGaussClient
from fep_lean.gauss.runner import GaussRunner
from fep_lean.llm.hermes import HermesConfig, HermesExplainer, HermesResult
from fep_lean.verification import lean_verifier as verifier_module
from fep_lean.verification.environment import run_validation_checks
from fep_lean.verification.lean_verifier import LeanVerifier, VerifyResult

PROJ = Path(__file__).resolve().parent.parent
LEAN_DIR = PROJ / "lean"


# ── _has_sorry comment handling ──────────────────────────────────────────────


def test_has_sorry_ignores_line_comments() -> None:
    assert (
        verifier_module._has_sorry("-- sorry in a comment\ntheorem t : True := trivial")
        is False
    )


def test_has_sorry_ignores_block_comments() -> None:
    assert (
        verifier_module._has_sorry(
            "/- sorry inside block -/\ntheorem t : True := trivial"
        )
        is False
    )


def test_has_sorry_detects_real_sorry() -> None:
    assert verifier_module._has_sorry("theorem t : True := by sorry") is True


def test_has_sorry_detects_sorry_after_comment() -> None:
    assert verifier_module._has_sorry("-- note\ntheorem t : True := by sorry") is True


# ── VerifyResult.status timeout variant ──────────────────────────────────────


def test_verify_result_timeout_status_reports_skip_reason() -> None:
    r = VerifyResult(
        topic_id="fep-005",
        compiles=False,
        has_sorry=False,
        skip_reason="timeout after 900s",
        failure_kind="timeout",
    )
    assert r.status == "skipped (timeout after 900s)"
    d = r.as_dict()
    assert d["failure_kind"] == "timeout"


# ── _get_timeout call-time env override ─────────────────────────────────────


def test_get_timeout_reads_env_at_call_time(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FEP_LEAN_VERIFY_TIMEOUT", "1234")
    assert verifier_module._get_timeout() == 1234


def test_get_timeout_default_matches_module_constant(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("FEP_LEAN_VERIFY_TIMEOUT", raising=False)
    assert verifier_module._get_timeout() == verifier_module._VERIFICATION_TIMEOUT


# ── OpenGaussClient session finalization ─────────────────────────────────────


def test_close_open_session_is_idempotent(tmp_path: Path) -> None:
    client = OpenGaussClient(gauss_home=tmp_path / "g")
    sid = client.create_session("fep-020", "FEP")
    client.close_session(sid, status="success", hermes_success=True)
    client.close_open_session(sid, error="late cleanup attempt")
    rec = client.export_session(sid)
    # Already-closed session must keep its success status
    assert rec["status"] == "success"
    client.close() if hasattr(client, "close") else None


def test_close_open_session_fails_open_session(tmp_path: Path) -> None:
    client = OpenGaussClient(gauss_home=tmp_path / "g")
    sid = client.create_session("fep-021", "FEP")
    client.close_open_session(sid, error="boom")
    rec = client.export_session(sid)
    assert rec["status"] == "error"
    ops_log = tmp_path / "g" / "fep_logs" / "operations.jsonl"
    events = [json.loads(line) for line in ops_log.read_text().splitlines() if line]
    assert any(
        event["event"] == "session_cleanup_error" and event["session_id"] == sid
        for event in events
    )
    client.close() if hasattr(client, "close") else None


def test_write_artifact_registers_sha256_and_size(tmp_path: Path) -> None:
    import hashlib

    client = OpenGaussClient(gauss_home=tmp_path / "g")
    sid = client.create_session("fep-022", "FEP")
    payload = {"topic_id": "fep-022", "compiles": True}
    path = client.write_artifact(sid, payload)
    content = path.read_text(encoding="utf-8")
    row = client._conn.execute(
        "SELECT sha256, size_bytes FROM artifacts WHERE session_id=?", (sid,)
    ).fetchone()
    assert row is not None
    assert row["sha256"] == hashlib.sha256(content.encode()).hexdigest()
    assert row["size_bytes"] == len(content.encode())
    client.close() if hasattr(client, "close") else None


# ── GaussRunner hermes_error path ────────────────────────────────────────────


class _FailingHermes(HermesExplainer):
    """Hermes fixture that reports an error result without HTTP."""

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
            success=False,
            model_used="fixture",
            error="upstream unavailable",
            topic_id=topic.id,
        )


def _topic() -> TopicEntry:
    c = FEPTopicCatalogue.from_yaml(PROJ / "config" / "topics.yaml")
    return c.topics[0]


def test_run_topic_hermes_error_finalizes_session(tmp_path: Path) -> None:
    lean = LeanVerifier(LEAN_DIR, PROJ)
    hermes = _FailingHermes()
    client = OpenGaussClient(gauss_home=tmp_path / "g")
    runner = GaussRunner(lean, hermes, client, PROJ)
    result = runner.run_topic(_topic())
    assert result.status == "hermes_error"
    assert result.success is False
    assert result.error == "upstream unavailable"
    assert hermes.call_count == 1
    rec = client.export_session(result.session_id)
    assert rec["status"] == "error"
    assert rec["hermes_success"] == 0


def test_run_topic_hermes_error_does_not_write_cache(tmp_path: Path) -> None:
    lean = LeanVerifier(LEAN_DIR, PROJ)
    client = OpenGaussClient(gauss_home=tmp_path / "g")
    runner = GaussRunner(lean, _FailingHermes(), client, PROJ)
    runner.run_topic(_topic())
    rows = client._conn.execute("SELECT COUNT(*) AS n FROM hermes_cache").fetchone()
    assert rows["n"] == 0


# ── run_validation_checks mode contract ─────────────────────────────────────


def test_run_validation_checks_rejects_unknown_mode(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unsupported validation mode"):
        run_validation_checks(tmp_path, mode="bogus")


def test_run_validation_checks_catalogue_mode_on_skeleton_reports_failures(
    tmp_path: Path,
) -> None:
    result = run_validation_checks(tmp_path, mode="catalogue")
    assert result["status"] == "error"
    assert result["failed_count"] > 0
    names = {check["name"] for check in result["checks"]}
    assert "topics_yaml" in names
    assert "gauss_cli" not in names  # full-only checks stay out of catalogue mode
    for check in result["checks"]:
        assert check["duration_s"] >= 0.0
        assert isinstance(check["ok"], bool)
