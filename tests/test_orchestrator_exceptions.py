"""Artifact failures remain structured and never become successful reports."""

from pathlib import Path

from fep_formal.pipeline.core import FEPPipeline


def test_pipeline_reports_artifact_failure(monkeypatch, tmp_path: Path) -> None:
    project = Path(__file__).resolve().parent.parent
    pipeline = FEPPipeline(project, output_root=tmp_path / "output")
    monkeypatch.setattr(
        pipeline,
        "_write_artifacts",
        lambda: (_ for _ in ()).throw(PermissionError("read-only")),
    )
    result = pipeline.run(mode="catalogue")
    assert result.status == "error"
    assert result.complete is False
    assert result.failure_reason
