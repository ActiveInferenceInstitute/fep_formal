"""Entry-point failure tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from fep_formal.pipeline.orchestrator import run_pipeline, run_single_topic


def test_unknown_topic_returns_structured_error() -> None:
    result = run_single_topic("fep-unknown-888", mode="catalogue")
    assert result.status == "error"
    assert result.failure_reason


def test_missing_catalogue_returns_structured_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("FEP_FORMAL_PROJECT_ROOT", str(tmp_path))
    (tmp_path / "config").mkdir()
    result = run_pipeline(mode="catalogue")
    assert result.status == "error"
    assert result.complete is False


def test_invalid_catalogue_is_rejected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("FEP_FORMAL_PROJECT_ROOT", str(tmp_path))
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "topics.yaml").write_text(
        "topics:\n  - id: fep-001\n", encoding="utf-8"
    )
    result = run_pipeline(mode="catalogue")
    assert result.status == "error"
    assert "catalogue" in result.failure_reason.lower()
