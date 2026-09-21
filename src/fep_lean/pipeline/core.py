"""Strict catalogue and verification pipeline."""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from fep_lean.catalogue.topics import FEPTopicCatalogue
from fep_lean.gauss.runner import GaussRunner
from fep_lean.output.figures import write_all_catalogue_figures
from fep_lean.output.manuscript import (
    write_manuscript_vars,
    write_unified_formalism_appendix_markdown,
)
from fep_lean.verification.environment import run_validation_checks

log = logging.getLogger(__name__)
PipelineMode = Literal["full", "catalogue"]


def _max_topics_from_env() -> int | None:
    raw = os.environ.get("FEP_LEAN_MAX_TOPICS", "").strip()
    if not raw:
        return None
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError("FEP_LEAN_MAX_TOPICS must be a positive integer") from exc
    if value < 1:
        raise ValueError("FEP_LEAN_MAX_TOPICS must be a positive integer")
    return value


@dataclass
class StepResult:
    name: str
    status: str
    message: str = ""
    duration_s: float = 0.0
    payload: Any = None
    error: str | None = None


@dataclass
class PipelineResult:
    status: str
    mode: PipelineMode = "full"
    complete: bool = False
    total_duration: float = 0.0
    run_dir: str = ""
    stages: list[StepResult] = field(default_factory=list)
    lean_stats: dict[str, Any] = field(default_factory=dict)
    catalogue_topics: int = 0
    verified_topics: int = 0
    capabilities: dict[str, bool] = field(default_factory=dict)
    failure_reason: str = ""
    _topic_results: list[Any] = field(default_factory=list)

    @property
    def topic_results(self) -> list[Any]:
        return self._topic_results

    @topic_results.setter
    def topic_results(self, value: list[Any]) -> None:
        self._topic_results = value

    @property
    def hermes_count(self) -> int:
        return sum(
            bool(getattr(item, "hermes_success", False)) for item in self._topic_results
        )

    @property
    def lean_verified_count(self) -> int:
        return sum(
            bool(getattr(item, "lean_compiles", False)) for item in self._topic_results
        )

    @property
    def lean_compile_ok(self) -> int:
        return sum(
            bool(getattr(item, "lean_compiles", False))
            and not bool(getattr(item, "lean_has_sorry", True))
            and not bool(getattr(item, "lean_warnings", []))
            for item in self._topic_results
        )

    @property
    def duration_s(self) -> float:
        return self.total_duration

    @property
    def stats(self) -> dict[str, Any]:
        gauss_stage = next(
            (stage for stage in self.stages if stage.name == "Gauss Sessions"), None
        )
        return {
            "topics_total": self.catalogue_topics,
            "topics_verified": self.verified_topics,
            "hermes_success": self.hermes_count,
            "lean_verified": self.lean_verified_count,
            "lean_compile_ok": self.lean_compile_ok,
            "stages_ok": sum(stage.status == "ok" for stage in self.stages),
            "gauss_ran": bool(gauss_stage and gauss_stage.status == "ok"),
            **self.lean_stats,
        }

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "mode": self.mode,
            "complete": self.complete,
            "total_duration": round(self.total_duration, 3),
            "run_dir": self.run_dir,
            "catalogue_topics": self.catalogue_topics,
            "verified_topics": self.verified_topics,
            "capabilities": self.capabilities,
            "failure_reason": self.failure_reason,
            "stages": [
                {
                    "name": stage.name,
                    "status": stage.status,
                    "message": stage.message,
                    "duration_s": round(stage.duration_s, 3),
                    "error": stage.error,
                }
                for stage in self.stages
            ],
            "lean_stats": self.lean_stats,
        }


def _resolve_output_root(project_root: Path, output_root: Path | None) -> Path:
    if output_root is not None:
        return Path(output_root)
    return Path(os.environ.get("FEP_LEAN_OUTPUT_ROOT", project_root / "output"))


class FEPPipeline:
    def __init__(self, project_root: Path, *, output_root: Path | None = None) -> None:
        self.project_root = Path(project_root)
        self.topics_file = self.project_root / "config" / "topics.yaml"
        configured_root: Path | None = None
        if output_root is None:
            settings_path = self.project_root / "config" / "settings.yaml"
            try:
                import yaml

                settings = (
                    yaml.safe_load(settings_path.read_text(encoding="utf-8")) or {}
                )
                configured = settings.get("output", {}).get("root")
                if configured:
                    configured_root = (self.project_root / str(configured)).resolve()
            except (OSError, yaml.YAMLError, AttributeError) as exc:
                log.warning(
                    "could not read output.root from %s (%s: %s); "
                    "falling back to ./output",
                    settings_path,
                    type(exc).__name__,
                    exc,
                )
                configured_root = None
        self.output_root = _resolve_output_root(
            self.project_root, output_root or configured_root
        )
        self._catalogue: FEPTopicCatalogue | None = None
        self._topics_to_run: tuple[Any, ...] = ()
        self._run_topic_results: list[dict[str, Any]] = []

    def run(
        self,
        *,
        mode: PipelineMode = "full",
        topic_filter: list[str] | None = None,
        area_filter: str | None = None,
        workflow: str = "verify",
    ) -> PipelineResult:
        if mode not in ("full", "catalogue"):
            raise ValueError(f"unsupported pipeline mode: {mode}")
        started = time.perf_counter()
        stages: list[StepResult] = []

        def stage(name: str, action: Any) -> tuple[StepResult, Any]:
            t0 = time.perf_counter()
            try:
                payload = action()
                result = StepResult(
                    name, "ok", duration_s=time.perf_counter() - t0, payload=payload
                )
            except Exception as exc:
                result = StepResult(
                    name,
                    "error",
                    duration_s=time.perf_counter() - t0,
                    error=f"{type(exc).__name__}: {exc}",
                )
                payload = None
                log.error("stage %s failed: %s", name, exc)
            stages.append(result)
            return result, payload

        catalogue_stage, _catalogue_payload = stage(
            "Load Catalogue", self._load_catalogue(topic_filter, area_filter)
        )
        if catalogue_stage.status != "ok":
            return PipelineResult(
                "error",
                mode=mode,
                total_duration=time.perf_counter() - started,
                stages=stages,
                failure_reason=catalogue_stage.error or "catalogue load failed",
            )

        validation_stage, validation = stage(
            "Environment Validation",
            lambda: run_validation_checks(self.project_root, mode=mode),
        )
        if validation_stage.status != "ok" or validation.get("status") != "ok":
            reason = (
                validation_stage.error
                or f"{validation.get('failed_count', 0)} required capability checks failed"
            )
            result = PipelineResult(
                "error",
                mode=mode,
                complete=False,
                total_duration=time.perf_counter() - started,
                stages=stages,
                catalogue_topics=len(self._topics_to_run),
                capabilities={
                    c["name"]: bool(c["ok"]) for c in validation.get("checks", [])
                }
                if isinstance(validation, dict)
                else {},
                failure_reason=reason,
            )
            return result

        raw_results: list[Any] = []
        if mode == "full":
            gauss_stage, gauss_payload = stage(
                "Gauss Sessions", lambda: self._run_gauss(workflow)
            )
            if gauss_stage.status != "ok":
                return PipelineResult(
                    "error",
                    mode=mode,
                    total_duration=time.perf_counter() - started,
                    stages=stages,
                    catalogue_topics=len(self._topics_to_run),
                    failure_reason=gauss_stage.error or "verification stage failed",
                )
            raw_results = gauss_payload.get("results", [])
        else:
            stages.append(
                StepResult(
                    "Gauss Sessions",
                    "not_run",
                    message="catalogue mode never performs verification",
                )
            )

        artifact_stage, _ = stage(
            "Manuscript Artifacts", lambda: self._write_artifacts()
        )
        if artifact_stage.status != "ok":
            return PipelineResult(
                "error",
                mode=mode,
                total_duration=time.perf_counter() - started,
                stages=stages,
                catalogue_topics=len(self._topics_to_run),
                failure_reason=artifact_stage.error or "artifact generation failed",
                _topic_results=raw_results,
            )

        self._run_topic_results = [item.as_dict() for item in raw_results]
        stats = self._compute_lean_stats()
        verified = sum(
            bool(getattr(item, "success", False))
            and bool(getattr(item, "lean_compiles", False))
            and not bool(getattr(item, "lean_has_sorry", True))
            and not bool(getattr(item, "lean_warnings", []))
            for item in raw_results
        )
        complete = mode == "catalogue" or (
            len(raw_results) == len(self._topics_to_run)
            and verified == len(self._topics_to_run)
        )
        status = "ok" if complete else "error"
        capability_rows = {
            str(check["name"]): bool(check["ok"])
            for check in validation.get("checks", [])
            if isinstance(check, dict) and "name" in check and "ok" in check
        }
        return PipelineResult(
            status,
            mode=mode,
            complete=complete,
            total_duration=time.perf_counter() - started,
            stages=stages,
            lean_stats=stats,
            catalogue_topics=len(self._topics_to_run),
            verified_topics=verified,
            capabilities={
                "catalogue": True,
                "verification": mode == "full",
                **capability_rows,
            },
            failure_reason=""
            if complete
            else "one or more topics failed strict verification",
            _topic_results=raw_results,
        )

    def _load_catalogue(
        self, topic_filter: list[str] | None, area_filter: str | None
    ) -> Any:
        def action() -> dict[str, Any]:
            self._catalogue = FEPTopicCatalogue.from_yaml(self.topics_file)
            topics = self._catalogue.topics
            if topic_filter:
                unknown = sorted(set(topic_filter) - {topic.id for topic in topics})
                if unknown:
                    raise ValueError(f"unknown topic ids: {', '.join(unknown)}")
                topics = tuple(topic for topic in topics if topic.id in topic_filter)
            if area_filter:
                topics = tuple(topic for topic in topics if topic.area == area_filter)
            maximum = _max_topics_from_env()
            self._topics_to_run = tuple(topics[:maximum] if maximum else topics)
            return {
                "topics": [topic.id for topic in self._topics_to_run],
                "total_catalogue_topics": len(self._catalogue.topics),
            }

        return action

    def _run_gauss(self, workflow: str) -> dict[str, Any]:
        runner = GaussRunner.create_default(self.project_root, require_cli=True)
        try:
            if not getattr(runner.hermes, "is_live", False):
                raise RuntimeError(
                    "Hermes is not live; full mode requires configured credentials"
                )
            runner.hermes.preflight()
            results = runner.run_topics_batch(
                list(self._topics_to_run), workflow=workflow
            )
            return {
                "results": results,
                "topics": [result.as_dict() for result in results],
            }
        finally:
            runner.close()

    def _write_artifacts(self) -> dict[str, str]:
        if self._catalogue is None:
            raise RuntimeError("catalogue is not loaded")
        vars_path = write_manuscript_vars(
            self.project_root,
            self._catalogue,
            output_root=self.output_root,
        )
        appendix_path = write_unified_formalism_appendix_markdown(
            self.project_root, self._catalogue
        )
        figures = write_all_catalogue_figures(
            self._catalogue, self.project_root, output_root=self.output_root
        )
        return {
            "vars_file": str(vars_path),
            "appendix": str(appendix_path),
            "figures": str(len(figures)),
        }

    def _compute_lean_stats(self) -> dict[str, Any]:
        rows = self._run_topic_results
        return {
            "total_processed": len(rows),
            "compiles_clean": sum(
                bool(row.get("lean_compiles"))
                and not bool(row.get("lean_has_sorry"))
                and not bool(row.get("lean_warnings"))
                for row in rows
            ),
            "compile_error": sum(not bool(row.get("lean_compiles")) for row in rows),
            "hermes_error": sum(not bool(row.get("hermes_success")) for row in rows),
            "warning_count": sum(
                len(row.get("lean_warnings", []))
                for row in rows
                if isinstance(row.get("lean_warnings", []), list)
            ),
            "warning_logs": [
                f"{row.get('topic_id')}: {warning}"
                for row in rows
                for warning in row.get("lean_warnings", [])
                if isinstance(warning, str)
            ],
            "error_logs": [
                f"{row.get('topic_id')}: {row.get('error', '')}"
                for row in rows
                if row.get("error")
            ],
            "clean_logs": [
                f"{row.get('topic_id')} successfully verified"
                for row in rows
                if row.get("lean_compiles")
                and not row.get("lean_has_sorry")
                and not row.get("lean_warnings")
            ],
        }
