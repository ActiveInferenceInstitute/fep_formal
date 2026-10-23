"""pipeline — Formalization DAG orchestrator and entry APIs.

Coordinates the 4-stage pipeline (Load Catalog, Environment Validation,
Gauss Sessions, Manuscript Artifacts) connecting Catalog -> LLM ->
verification -> output, executing the topological dependencies in order.
Run reporting (``Reporter.generate``) is invoked from
``fep_lean.pipeline.orchestrator.run_pipeline`` after ``FEPPipeline.run()`` returns and
is not a fifth entry in ``PipelineResult.stages``.

Public API
----------
    FEPPipeline       — core DAG executor class
    PipelineResult    — final state output of a DAG run
    StepResult        — individual stage outcome
    run_pipeline      — programmatic entry point for scripts (runs everything)
    run_single_topic  — programmatic entry point for verifying one target
    project_root      — returns the current standalone checkout root
"""

from fep_lean.pipeline.core import FEPPipeline, PipelineResult, StepResult
from fep_lean.pipeline.orchestrator import project_root, run_pipeline, run_single_topic

__all__ = [
    "FEPPipeline",
    "PipelineResult",
    "StepResult",
    "project_root",
    "run_pipeline",
    "run_single_topic",
]
