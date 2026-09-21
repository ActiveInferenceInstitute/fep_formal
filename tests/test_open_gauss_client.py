"""Tests for open_gauss_client — SQLite session store.

All tests use real SQLite (tmp_path) — no direct execution.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

import pytest

from fep_lean.gauss.client import OpenGaussClient


@pytest.fixture()
def client(tmp_path: Path) -> Iterator[OpenGaussClient]:
    with OpenGaussClient(gauss_home=tmp_path / "gauss_home") as store:
        yield store


def test_new_nested_home_can_be_reopened_without_losing_sessions(
    tmp_path: Path,
) -> None:
    home = tmp_path / "new" / "nested" / "gauss"
    with OpenGaussClient(gauss_home=home) as store:
        session_id = store.create_session("fep-001", "FEP")
    with OpenGaussClient(gauss_home=home) as store:
        assert store.export_session(session_id)["topic_id"] == "fep-001"
    assert (home / "fep_artifacts").is_dir()
    assert (home / "fep_logs").is_dir()


def test_create_session_returns_string(client: OpenGaussClient) -> None:
    sid = client.create_session("fep-001", "FEP", "theorem foo : True := by trivial")
    assert isinstance(sid, str)
    assert "fep-001" in sid


def test_create_session_rejects_empty_topic_id(client: OpenGaussClient) -> None:
    with pytest.raises(ValueError, match="topic_id cannot be empty"):
        client.create_session("", "FEP")


def test_create_session_rejects_whitespace_topic_id(
    client: OpenGaussClient,
) -> None:
    with pytest.raises(ValueError, match="topic_id cannot be empty"):
        client.create_session("   ", "FEP")


def test_update_session_stores_turns(client: OpenGaussClient) -> None:
    sid = client.create_session("fep-002", "ActiveInference", "sketch")
    client.update_session(sid, 0, "user", "Explain ELBO bound")
    client.update_session(sid, 1, "assistant", "F ≥ -log p(s|m)")
    exported = client.export_session(sid)
    assert len(exported["turns"]) == 2
    assert exported["turns"][0]["role"] == "user"
    assert exported["turns"][1]["role"] == "assistant"


def test_close_session_writes_status(client: OpenGaussClient) -> None:
    sid = client.create_session("fep-003", "FEP")
    client.close_session(sid, status="success", hermes_success=True, lean_compiles=1)
    rec = client.export_session(sid)
    assert rec["status"] == "success"
    assert rec["hermes_success"] == 1
    assert rec["lean_compiles"] == 1
    assert rec["closed_at"] is not None
    assert rec["duration_s"] is not None and rec["duration_s"] >= 0


def test_export_session_not_found_raises(client: OpenGaussClient) -> None:
    with pytest.raises(KeyError):
        client.export_session("nonexistent-id")


def test_set_refined_sketch(client: OpenGaussClient) -> None:
    sid = client.create_session("fep-004", "BayesianMechanics")
    refined = "theorem foo : True := by trivial"
    client.set_refined_sketch(sid, refined)
    rec = client.export_session(sid)
    assert rec["refined_sketch"] == refined


def test_export_all_sessions_source_filter(client: OpenGaussClient) -> None:
    sid1 = client.create_session("fep-001", "FEP", source="fep_lean")
    sid2 = client.create_session("fep-002", "FEP", source="other_project")
    client.close_session(sid1)
    client.close_session(sid2)
    all_fep = client.export_all_sessions("fep_lean")
    ids = [r["session_id"] for r in all_fep]
    assert sid1 in ids
    assert sid2 not in ids


def test_write_artifact_creates_file(client: OpenGaussClient) -> None:
    sid = client.create_session("fep-005", "InfoGeometry")
    payload = {"result": "ok", "topic_id": "fep-005", "score": 42}
    path = client.write_artifact(sid, payload)
    assert path.is_file()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["result"] == "ok"


def test_write_bulk_jsonl(client: OpenGaussClient, tmp_path: Path) -> None:
    sid1 = client.create_session("fep-010", "FEP")
    sid2 = client.create_session("fep-011", "FEP")
    client.close_session(sid1)
    client.close_session(sid2)
    sessions = client.export_all_sessions()
    out = tmp_path / "bulk.jsonl"
    result = client.write_bulk_jsonl(sessions, out)
    assert result.is_file()
    lines = [
        line for line in result.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    assert len(lines) == 2
    first = json.loads(lines[0])
    assert "session_id" in first


def test_log_event_writes_to_db_and_file(client: OpenGaussClient) -> None:
    sid = client.create_session("fep-006", "Thermodynamics")
    client.log_event("test_event", session_id=sid, extra="data")
    ops_file = client._logs_dir / "operations.jsonl"
    assert ops_file.is_file()
    lines = [
        line
        for line in ops_file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert any("test_event" in line for line in lines)


def test_get_stats(client: OpenGaussClient) -> None:
    for i in range(3):
        sid = client.create_session(f"fep-{i:03d}", "FEP")
        client.close_session(sid, hermes_success=(i % 2 == 0), lean_compiles=1)
    stats = client.get_stats()
    assert stats["total_sessions"] == 3
    assert stats["lean_compiles"] == 3
    assert "db_path" in stats


def test_context_manager(tmp_path: Path) -> None:
    home = tmp_path / "gauss_cm_test"
    with OpenGaussClient(gauss_home=home) as c:
        sid = c.create_session("fep-999", "FEP")
        assert isinstance(sid, str)


# ── Hermes cache tests ────────────────────────────────────────────────────────


def test_set_and_get_cached_hermes(client: OpenGaussClient) -> None:
    payload = json.dumps(
        {"success": True, "model_used": "fixture-model", "explanation": "test"}
    )
    client.set_cached_hermes(
        "key-abc", "fep-001", "verify", "fixture-model", payload, "hash123"
    )
    result = client.get_cached_hermes("key-abc")
    assert result is not None
    assert result["success"] is True
    assert result["model_used"] == "fixture-model"
    assert result["explanation"] == "test"


def test_get_cached_hermes_missing_returns_none(client: OpenGaussClient) -> None:
    assert client.get_cached_hermes("nonexistent-key-xyz") is None


def test_get_cached_hermes_ignores_malformed_payload(client: OpenGaussClient) -> None:
    client._conn.execute(
        "INSERT INTO hermes_cache (cache_key, topic_id, stage, model, hermes_result, lean_sketch_hash, created_at) VALUES (?,?,?,?,?,?,?)",
        ("bad-key", "fep-001", "verify", "fixture", "not-json", "hash", 0.0),
    )
    client._conn.commit()
    assert client.get_cached_hermes("bad-key") is None


def test_prune_hermes_cache_removes_old(client: OpenGaussClient) -> None:
    import time as _time

    payload = json.dumps({"success": True, "model_used": "fixture"})
    client.set_cached_hermes("old-key", "fep-002", "verify", "fixture", payload, "h1")
    # Manually backdate the entry beyond ttl
    client._conn.execute(
        "UPDATE hermes_cache SET created_at=? WHERE cache_key=?",
        (_time.time() - 100_000, "old-key"),
    )
    client._conn.commit()
    pruned = client.prune_hermes_cache(ttl_hours=1.0)
    assert pruned >= 1
    assert client.get_cached_hermes("old-key") is None


def test_prune_hermes_cache_keeps_fresh(client: OpenGaussClient) -> None:
    payload = json.dumps({"success": True, "model_used": "fixture"})
    client.set_cached_hermes("fresh-key", "fep-003", "verify", "fixture", payload, "h2")
    pruned = client.prune_hermes_cache(ttl_hours=24.0)
    assert pruned == 0
    assert client.get_cached_hermes("fresh-key") is not None
