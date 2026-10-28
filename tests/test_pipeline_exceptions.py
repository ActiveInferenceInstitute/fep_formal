"""Pipeline failure boundaries."""

from pathlib import Path

from fep_formal.pipeline.core import FEPPipeline

pytest_plugins = ["tests._support.catalogue_project"]


def test_pipeline_missing_catalogue(tmp_path: Path) -> None:
    result = FEPPipeline(tmp_path).run(mode="catalogue")
    assert result.status == "error"
    assert any(stage.status == "error" for stage in result.stages)


def test_pipeline_rejects_partial_catalogue(tmp_path: Path) -> None:
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "topics.yaml").write_text(
        "topics:\n  - id: fep-001\n", encoding="utf-8"
    )
    result = FEPPipeline(tmp_path).run(mode="catalogue")
    assert result.status == "error"
    assert not result.complete


def test_pipeline_catalogue_mode_never_runs_gauss(catalogue_project: Path) -> None:
    result = FEPPipeline(catalogue_project).run(mode="catalogue")
    assert result.status == "ok"
    assert result.complete is True
    gauss = next(stage for stage in result.stages if stage.name == "Gauss Sessions")
    assert gauss.status == "not_run"
