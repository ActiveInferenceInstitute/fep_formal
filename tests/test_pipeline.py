"""Strict pipeline contract tests."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from fep_formal._paths import resolve_output_root
from fep_formal.catalogue.topics import CatalogueValidationError, FEPTopicCatalogue
from fep_formal.gauss.runner import TopicRunResult
from fep_formal.output import manuscript
from fep_formal.output.manuscript import _verify_block_from_manifest
from fep_formal.output.provenance import report_owner_errors, report_source_digest
from fep_formal.pipeline.core import (
    FEPPipeline,
    PipelineResult,
    StepResult,
    _max_topics_from_env,
)
from tests._support.catalogue_project import manuscript_owner_state

PROJ = Path(__file__).resolve().parent.parent
pytest_plugins = ["tests._support.catalogue_project"]


def test_pipeline_instantiates() -> None:
    assert FEPPipeline(PROJ) is not None


def test_catalogue_mode_is_complete_but_unverified(
    tmp_path: Path, catalogue_project: Path
) -> None:
    result = FEPPipeline(catalogue_project, output_root=tmp_path / "output").run(
        mode="catalogue", topic_filter=["fep-001", "fep-002"]
    )
    assert isinstance(result, PipelineResult)
    assert result.mode == "catalogue"
    assert result.complete is True
    assert result.catalogue_topics == 2
    assert result.verified_topics == 0
    assert result.capabilities["verification"] is False
    assert (
        next(stage for stage in result.stages if stage.name == "Gauss Sessions").status
        == "not_run"
    )


def test_real_catalogue_writes_only_the_private_project(
    tmp_path: Path, catalogue_project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    live_before = manuscript_owner_state(PROJ)
    assert report_owner_errors(catalogue_project) == ()
    assert report_source_digest(catalogue_project) == report_source_digest(PROJ)
    assert not (catalogue_project / ".git").exists()
    assert not (catalogue_project / "lean/.lake").exists()
    assert {
        path.relative_to(catalogue_project).as_posix()
        for path in (catalogue_project / "specs").rglob("*")
        if path.is_file()
    } == {
        "specs/geo-infer-notation-bridge/check_geo_notation_bridge.py",
        "specs/gnn-bridge-q6-activeinference-artifact/skeleton/canonical_bool_runner.jl.in",
        "specs/lean-workspace/test_workspace.py",
        "specs/lean-workspace/workspace.py",
        "specs/openai-math-methods/positioning.yaml",
    }
    variables = catalogue_project / "manuscript/manuscript_vars.yaml"
    appendix = catalogue_project / "manuscript/09z_unified_formalism_catalogue.md"
    assert not variables.exists()
    assert not appendix.exists()
    monkeypatch.setenv("FEP_FORMAL_OUTPUT_ROOT", str(tmp_path / "products"))
    original_atomic_write = manuscript.atomic_write_text

    def reject_separate_appendix_write(path: Path, text: str) -> None:
        assert path != appendix, "the paired appendix must not be written a second time"
        original_atomic_write(path, text)

    monkeypatch.setattr(manuscript, "atomic_write_text", reject_separate_appendix_write)
    pipeline = FEPPipeline(catalogue_project)
    assert pipeline.output_root == tmp_path / "products"

    result = pipeline.run(mode="catalogue")

    assert result.status == "ok"
    assert result.complete is True
    assert result.catalogue_topics == 168
    assert result.verified_topics == 0
    projected = yaml.safe_load(variables.read_bytes())
    assert projected["total_topics"] == 168
    assert projected["verify"]["manifest_present"] is False
    assert projected["verify"]["claim_ready"] is False
    assert "fep-168" in appendix.read_text()
    assert len(list((tmp_path / "products/figures").glob("*.png"))) == 9
    assert manuscript_owner_state(PROJ) == live_before

    # A genuine source error stays a failed catalogue attempt in that private
    # project and cannot rewrite either the prior projection or live inputs.
    private_before = manuscript_owner_state(catalogue_project)
    (catalogue_project / "config/topics.yaml").write_text("topics: []\n")
    failed = pipeline.run(mode="catalogue")
    assert failed.status == "error"
    assert failed.complete is False
    assert manuscript_owner_state(catalogue_project) == private_before
    assert manuscript_owner_state(PROJ) == live_before


@pytest.mark.parametrize(
    ("environment", "explicit", "expected"),
    [
        (None, None, "configured"),
        ("", None, "configured"),
        ("   ", None, "configured"),
        ("environment", None, "environment"),
        ("environment", "explicit", "explicit"),
        (None, "explicit", "explicit"),
    ],
)
def test_output_root_precedence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    environment: str | None,
    explicit: str | None,
    expected: str,
) -> None:
    root = tmp_path / "project"
    (root / "config").mkdir(parents=True)
    (root / "config/settings.yaml").write_text("output:\n  root: configured\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("FEP_FORMAL_OUTPUT_ROOT", raising=False)
    if environment is not None:
        monkeypatch.setenv("FEP_FORMAL_OUTPUT_ROOT", environment)
    chosen = Path(explicit) if explicit is not None else None
    expected_path = root / expected if expected == "configured" else tmp_path / expected
    assert resolve_output_root(root, chosen).resolve() == expected_path
    assert FEPPipeline(root, output_root=chosen).output_root.resolve() == expected_path
    assert not expected_path.exists()


@pytest.mark.parametrize(
    "settings",
    ["[", "[]", "output: []", "output: {root: 7}", "output: {root: '   '}"],
)
def test_output_root_rejects_selected_malformed_settings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    settings: str,
) -> None:
    (tmp_path / "config").mkdir()
    (tmp_path / "config/settings.yaml").write_text(settings)
    monkeypatch.delenv("FEP_FORMAL_OUTPUT_ROOT", raising=False)
    with pytest.raises(ValueError):
        FEPPipeline(tmp_path)
    monkeypatch.setenv("FEP_FORMAL_OUTPUT_ROOT", str(tmp_path / "environment"))
    assert FEPPipeline(tmp_path).output_root == tmp_path / "environment"
    assert (
        FEPPipeline(tmp_path, output_root=tmp_path / "explicit").output_root
        == tmp_path / "explicit"
    )


def test_output_root_without_settings_uses_project_default(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("FEP_FORMAL_OUTPUT_ROOT", raising=False)
    assert FEPPipeline(tmp_path).output_root == tmp_path / "output"
    assert not (tmp_path / "output").exists()


@pytest.mark.parametrize(
    "settings", ["", "output: null\n", "output: {root: null}\n", "output: {root: ''}\n"]
)
def test_empty_output_settings_use_default_without_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, settings: str
) -> None:
    """Absent output values are defaults, not permission to write configuration."""
    monkeypatch.delenv("FEP_FORMAL_OUTPUT_ROOT", raising=False)
    selected = tmp_path / "config/settings.yaml"
    selected.parent.mkdir()
    selected.write_text(settings)
    before = (selected.read_bytes(), selected.stat().st_mtime_ns)

    assert resolve_output_root(tmp_path) == tmp_path / "output"
    assert FEPPipeline(tmp_path).output_root == tmp_path / "output"
    assert (selected.read_bytes(), selected.stat().st_mtime_ns) == before
    assert set(tmp_path.rglob("*")) == {selected.parent, selected}


@pytest.mark.parametrize("mode", ["catalogue", "full"])
@pytest.mark.parametrize(
    "filters",
    [
        {"topic_filter": []},
        {"area_filter": ""},
        {"area_filter": "unknown"},
        {"topic_filter": ["fep-001"], "area_filter": "InfoGeometry"},
    ],
)
def test_empty_or_invalid_selection_fails_before_services_and_writes(
    tmp_path: Path,
    catalogue_project: Path,
    monkeypatch: pytest.MonkeyPatch,
    mode: str,
    filters: dict[str, object],
) -> None:
    pipeline = FEPPipeline(catalogue_project, output_root=tmp_path / "unused")
    before = manuscript_owner_state(catalogue_project)

    def forbidden(*_args: object, **_kwargs: object) -> None:
        pytest.fail("rejected selection must not reach capability, provider or writer")

    monkeypatch.setattr("fep_formal.pipeline.core.run_validation_checks", forbidden)
    monkeypatch.setattr(pipeline, "_run_gauss", forbidden)
    monkeypatch.setattr(pipeline, "_write_artifacts", forbidden)
    result = pipeline.run(mode=mode, **filters)  # type: ignore[arg-type]
    assert result.status == "error"
    assert result.complete is False
    assert result.catalogue_topics == result.verified_topics == 0
    assert [stage.name for stage in result.stages] == ["Load Catalogue"]
    assert pipeline._topics_to_run == ()
    assert manuscript_owner_state(catalogue_project) == before
    assert not pipeline.output_root.exists()


def test_pipeline_validates_selected_output_before_writing(
    tmp_path: Path,
    catalogue_project: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = tmp_path / "selected"
    selected.mkdir()
    pipeline = FEPPipeline(catalogue_project, output_root=selected)
    before = manuscript_owner_state(catalogue_project)
    monkeypatch.setattr(
        "fep_formal.verification.environment.os.access",
        lambda path, _mode: Path(path) != selected,
    )
    monkeypatch.setattr(
        pipeline,
        "_write_artifacts",
        lambda: pytest.fail("invalid output reached writer"),
    )
    result = pipeline.run(mode="catalogue", topic_filter=["fep-001"])
    assert result.status == "error"
    assert result.capabilities["output_writable"] is False
    assert manuscript_owner_state(catalogue_project) == before
    assert not list(selected.iterdir())


def test_full_mode_fails_without_capabilities(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, catalogue_project: Path
) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    # Actual absent capabilities, with no access to host tools or elan state.
    monkeypatch.setenv("PATH", "")
    monkeypatch.setenv("ELAN_HOME", str(tmp_path / "empty-elan"))
    monkeypatch.delenv("FEP_FORMAL_LEAN_EXE", raising=False)
    monkeypatch.delenv("FEP_FORMAL_LAKE_EXE", raising=False)
    result = FEPPipeline(catalogue_project, output_root=tmp_path / "output").run(
        mode="full", topic_filter=["fep-001"]
    )
    assert result.complete is False
    assert result.status == "error"
    assert result.run_dir == ""
    assert result.failure_reason
    assert not (tmp_path / "output" / "reports").exists()


def test_result_fields_are_explicit(tmp_path: Path, catalogue_project: Path) -> None:
    result = FEPPipeline(catalogue_project, output_root=tmp_path / "output").run(
        mode="catalogue"
    )
    assert result.duration_s > 0
    assert isinstance(result.topic_results, list)
    assert isinstance(result.capabilities, dict)
    assert "mode" in result.as_dict()
    assert "complete" in result.as_dict()
    assert "failure_reason" in result.as_dict()
    assert not hasattr(result, "steps")


def test_step_result_dataclass() -> None:
    step = StepResult("test_step", "ok", "all fine", 0.5)
    assert step.name == "test_step"
    assert step.status == "ok"
    assert step.message == "all fine"
    assert step.duration_s == 0.5
    assert step.error is None


def test_step_result_records_error() -> None:
    step = StepResult("test_step", "error", "boom", 0.0, error="boom")
    assert step.error == "boom"
    assert step.status == "error"


def test_filters_and_topic_cap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, catalogue_project: Path
) -> None:
    monkeypatch.setenv("FEP_FORMAL_MAX_TOPICS", "2")
    result = FEPPipeline(catalogue_project, output_root=tmp_path / "output").run(
        mode="catalogue", area_filter="FEP"
    )
    load = next(stage for stage in result.stages if stage.name == "Load Catalogue")
    assert len(load.payload["topics"]) == 2


def test_unknown_topic_is_an_error(tmp_path: Path, catalogue_project: Path) -> None:
    result = FEPPipeline(catalogue_project, output_root=tmp_path / "output").run(
        mode="catalogue", topic_filter=["fep-999"]
    )
    assert result.status == "error"
    assert "unknown topic" in result.failure_reason


def test_max_topics_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FEP_FORMAL_MAX_TOPICS", raising=False)
    assert _max_topics_from_env() is None
    monkeypatch.setenv("FEP_FORMAL_MAX_TOPICS", "3")
    assert _max_topics_from_env() == 3
    monkeypatch.setenv("FEP_FORMAL_MAX_TOPICS", "0")
    with pytest.raises(ValueError):
        _max_topics_from_env()


def test_stats_never_counts_catalogue_as_verified() -> None:
    result = PipelineResult(
        status="ok", mode="catalogue", complete=True, catalogue_topics=50
    )
    assert result.stats["topics_total"] == 50
    assert result.stats["topics_verified"] == 0
    assert result.stats["stages_ok"] == 0
    assert result.lean_compile_ok == 0


def test_topic_metrics_use_clean_compilation() -> None:
    result = PipelineResult(status="ok", mode="full", catalogue_topics=2)
    result.topic_results = [
        TopicRunResult(
            "fep-001",
            "s1",
            True,
            "ok",
            hermes_success=True,
            lean_compiles=True,
            lean_has_sorry=False,
        ),
        TopicRunResult(
            "fep-002",
            "s2",
            False,
            "ok",
            hermes_success=True,
            lean_compiles=True,
            lean_has_sorry=True,
        ),
    ]
    assert result.hermes_count == 2
    assert result.lean_verified_count == 2
    assert result.lean_compile_ok == 1


def test_full_pipeline_rejects_compiling_topic_with_warnings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, catalogue_project: Path
) -> None:
    pipeline = FEPPipeline(catalogue_project, output_root=tmp_path / "output")
    warning = SimpleNamespace(
        topic_id="fep-001",
        success=False,
        hermes_success=True,
        lean_compiles=True,
        lean_has_sorry=False,
        lean_warnings=["fixture warning"],
        error="fixture warning",
    )
    warning.as_dict = lambda: vars(warning).copy()
    monkeypatch.setattr(
        "fep_formal.pipeline.core.run_validation_checks",
        lambda *_args, **_kwargs: {
            "status": "ok",
            "failed_count": 0,
            "checks": [],
        },
    )
    monkeypatch.setattr(
        pipeline, "_run_gauss", lambda _workflow: {"results": [warning]}
    )
    monkeypatch.setattr(pipeline, "_write_artifacts", dict)

    result = pipeline.run(mode="full", topic_filter=["fep-001"])

    assert result.complete is False
    assert result.verified_topics == 0
    assert result.lean_stats["warning_count"] == 1
    assert result.lean_stats["warning_logs"] == ["fep-001: fixture warning"]


def test_invalid_mode_rejected() -> None:
    with pytest.raises(ValueError):
        FEPPipeline(PROJ).run(mode="invalid")  # type: ignore[arg-type]


def test_empty_catalogue_is_rejected(tmp_path: Path) -> None:
    yaml_path = tmp_path / "topics.yaml"
    yaml_path.write_text("topics: []\n", encoding="utf-8")
    with pytest.raises(CatalogueValidationError):
        FEPTopicCatalogue.from_yaml(yaml_path)


def test_verify_block_defaults_without_topics_keys(tmp_path: Path) -> None:
    p = tmp_path / "verification_manifest.json"
    p.write_text(json.dumps({"random_key": 42}), encoding="utf-8")
    b = _verify_block_from_manifest(p)
    assert b["manifest_present"] is True
    assert b["verify_lean_ran"] is False
    assert b["topics_with_result"] == 0


def test_verify_block_non_integer_topics_falls_back_to_results_count(
    tmp_path: Path,
) -> None:
    p = tmp_path / "verification_manifest.json"
    p.write_text(
        json.dumps({"topics_with_result": "fifty", "results": [{"compiles": True}]}),
        encoding="utf-8",
    )
    b = _verify_block_from_manifest(p)
    assert b["manifest_present"] is True
    assert b["topics_with_result"] == 1
