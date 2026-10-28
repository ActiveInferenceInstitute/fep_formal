"""Programmatic entry-point tests."""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest

from fep_formal.catalogue.schema import load_catalogue_metadata
from fep_formal.pipeline.core import PipelineResult
from fep_formal.pipeline.orchestrator import (
    project_root,
    run_pipeline,
    run_single_topic,
)
from tests._support.catalogue_project import manuscript_owner_state

PROJ = Path(__file__).resolve().parent.parent
pytest_plugins = ["tests._support.catalogue_project"]


@pytest.fixture(autouse=True)
def isolate(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, catalogue_project: Path
) -> Iterator[None]:
    live_before = manuscript_owner_state(PROJ)
    monkeypatch.setenv("FEP_FORMAL_PROJECT_ROOT", str(catalogue_project))
    monkeypatch.setenv("FEP_FORMAL_OUTPUT_ROOT", str(tmp_path / "output"))
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    yield
    assert manuscript_owner_state(PROJ) == live_before


def test_project_root_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FEP_FORMAL_PROJECT_ROOT", raising=False)
    assert project_root().resolve() == PROJ.resolve()


def test_project_root_uses_package_specific_override(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("FEP_FORMAL_PROJECT_ROOT", str(tmp_path))
    assert project_root().resolve() == tmp_path.resolve()


def test_run_single_topic_unknown() -> None:
    result = run_single_topic("fep-999", mode="catalogue")
    assert isinstance(result, PipelineResult)
    assert result.status == "error"
    assert "unknown topic" in result.failure_reason


def test_run_single_topic_catalogue_mode() -> None:
    result = run_single_topic("fep-001", mode="catalogue")
    assert result.complete is True
    assert result.catalogue_topics == 1
    assert result.run_dir


def test_run_pipeline_writes_catalogue_report(catalogue_project: Path) -> None:
    result = run_pipeline(mode="catalogue")
    assert result.complete is True
    assert result.mode == "catalogue"
    assert result.run_dir
    report = Path(result.run_dir)
    assert report.is_relative_to(Path(os.environ["FEP_FORMAL_OUTPUT_ROOT"]))
    assert not (catalogue_project / "output/reports").exists()
    assert (report / "summary.json").is_file()
    assert (report / "index.md").is_file()
    assert (catalogue_project / "manuscript/manuscript_vars.yaml").is_file()
    assert (
        catalogue_project / "manuscript/09z_unified_formalism_catalogue.md"
    ).is_file()


def test_run_pipeline_area_filter() -> None:
    result = run_pipeline(mode="catalogue", area_filter="FEP")
    expected_topics = sum(
        row.area == "FEP"
        for row in load_catalogue_metadata(PROJ / "config" / "catalogue_metadata.yaml")
    )
    assert result.complete is True
    assert result.catalogue_topics == expected_topics


def test_run_pipeline_full_fails_without_capabilities() -> None:
    result = run_pipeline(mode="full", topic_filter=["fep-001"])
    assert result.complete is False
    assert result.status == "error"
    assert result.run_dir == ""
