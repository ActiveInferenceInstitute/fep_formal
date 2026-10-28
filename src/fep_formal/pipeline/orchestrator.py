"""Canonical programmatic pipeline entry points."""

from __future__ import annotations

import logging
from pathlib import Path

from fep_formal._paths import project_root
from fep_formal.catalogue.topics import FEPTopicCatalogue
from fep_formal.output.reporter import Reporter
from fep_formal.pipeline.core import FEPPipeline, PipelineMode, PipelineResult

log = logging.getLogger(__name__)

__all__ = ["project_root", "run_pipeline", "run_single_topic"]


def run_pipeline(
    *,
    mode: PipelineMode = "full",
    interactive: bool = False,
    area_filter: str | None = None,
    topic_filter: list[str] | None = None,
    workflow: str = "verify",
    output_root: Path | None = None,
) -> PipelineResult:
    """Run the strict pipeline and report only complete runs."""
    if interactive:
        logging.getLogger().setLevel(logging.DEBUG)
    root = project_root()
    pipeline = FEPPipeline(root, output_root=output_root)
    result = pipeline.run(
        mode=mode, area_filter=area_filter, topic_filter=topic_filter, workflow=workflow
    )
    if result.complete and pipeline._catalogue is not None:
        reporter = Reporter(root, output_root=pipeline.output_root)
        paths = reporter.generate(pipeline._catalogue, result)
        result.run_dir = str(paths.root)
    else:
        log.error(
            "pipeline did not complete: %s", result.failure_reason or result.status
        )
    return result


def run_single_topic(
    topic_id: str,
    *,
    mode: PipelineMode = "full",
    interactive: bool = False,
    workflow: str = "verify",
    output_root: Path | None = None,
) -> PipelineResult:
    """Run one exact catalog topic under the selected execution contract."""
    root = project_root()
    catalogue = FEPTopicCatalogue.from_yaml(root / "config" / "topics.yaml")
    if topic_id not in {topic.id for topic in catalogue.topics}:
        return PipelineResult(
            "error", mode=mode, failure_reason=f"unknown topic id: {topic_id}"
        )
    return run_pipeline(
        mode=mode,
        interactive=interactive,
        topic_filter=[topic_id],
        workflow=workflow,
        output_root=output_root,
    )
