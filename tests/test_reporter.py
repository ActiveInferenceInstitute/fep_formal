"""Tests for reporter — Markdown + JSON report generation.

All tests use real PipelineResult objects and tmp_path file writes.
No direct execution.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

from fep_lean.catalogue.topics import FEPTopicCatalogue
from fep_lean.output.manuscript import _verify_block_from_manifest
from fep_lean.output.provenance import (
    OWNER_MANIFEST_VERSION,
    config_owner_paths,
    source_owner_paths,
)
from fep_lean.output.reporter import (
    Reporter,
    ReportPaths,
    _render_validation_markdown,
    validate_report_receipt,
)
from fep_lean.pipeline.core import FEPPipeline, PipelineResult, StepResult
from fep_lean.verification.environment import (
    CATALOGUE_VALIDATION_CHECK_NAMES,
    FULL_VALIDATION_CHECK_NAMES,
)
from scripts import verify_report_receipt as receipt_cli

PROJ = Path(__file__).resolve().parent.parent
LEAN_VERSION = (
    "Lean (version "
    + (PROJ / "lean" / "lean-toolchain")
    .read_text()
    .strip()
    .rsplit(":", 1)[-1]
    .lstrip("v")
    + ", x86_64-unknown-linux-gnu, commit fixture, Release)"
)


TOPICS = FEPTopicCatalogue.from_yaml(PROJ / "config" / "topics.yaml")


def _minimal_result(tmp_path: Path) -> PipelineResult:
    """Build a minimal PipelineResult without running the pipeline."""
    r = PipelineResult(status="ok")
    run_test_dir = tmp_path / "run_test"
    run_test_dir.mkdir()
    r.run_dir = str(run_test_dir)
    r.stages = [
        StepResult(
            name="Load Catalogue",
            status="ok",
            duration_s=0.01,
            payload={"topics": ["fep-001", "fep-002"]},
        ),
        StepResult(
            name="Environment Validation",
            status="ok",
            duration_s=0.5,
            payload={
                "status": "ok",
                "failed_count": 0,
                "checks": [
                    {"name": "lean_cli", "ok": True, "message": "ok", "duration_s": 0.1}
                ],
            },
        ),
        StepResult(name="Gauss Sessions", status="skipped", duration_s=0.001),
        StepResult(
            name="Manuscript Artifacts",
            status="ok",
            duration_s=0.05,
            payload={"vars_file": "manuscript_vars.yaml"},
        ),
    ]
    r.total_duration = 1.0
    r.lean_stats = {
        "total_processed": len(TOPICS.roster.topic_ids),
        "compiles_clean": 0,
        "compiles_with_sorry": 0,
        "compile_error": 0,
        "skipped": 0,
        "error_logs": [],
        "sorry_logs": [],
        "clean_logs": [],
    }
    return r


@pytest.fixture()
def reporter(tmp_path: Path) -> Reporter:
    return Reporter(tmp_path)


@pytest.fixture()
def report_paths(reporter: Reporter, tmp_path: Path) -> ReportPaths:
    result = _minimal_result(tmp_path)
    reporter.reports_dir = tmp_path / "run_test"
    return reporter.generate(TOPICS, result)


def test_reporter_rejects_existing_run_directory(tmp_path: Path) -> None:
    """A repeated explicit run ID must not overwrite provenance artifacts."""
    reporter = Reporter(tmp_path, run_id="run_collision")
    existing = tmp_path / "output" / "reports" / "run_collision"
    existing.mkdir(parents=True)
    sentinel = existing / "summary.json"
    sentinel.write_text("preserve me\n", encoding="utf-8")

    with pytest.raises(FileExistsError):
        reporter.generate(TOPICS, _minimal_result(tmp_path))

    assert sentinel.read_text(encoding="utf-8") == "preserve me\n"


def test_generate_returns_report_paths(report_paths: ReportPaths) -> None:
    assert isinstance(report_paths, ReportPaths)


def test_all_report_files_created(report_paths: ReportPaths) -> None:
    assert report_paths.index_md.is_file()
    assert report_paths.summary_json.is_file()
    assert (report_paths.summary_json.parent / "verification_manifest.json").is_file()
    assert (report_paths.summary_json.parent / "run_manifest.json").is_file()
    assert report_paths.hermes_md.is_file()
    assert report_paths.lean_md.is_file()
    assert report_paths.validation_md.is_file()


def test_index_md_contains_status(report_paths: ReportPaths) -> None:
    text = report_paths.index_md.read_text(encoding="utf-8")
    assert "ok" in text.lower() or "ok" in text
    assert "Load Catalogue" in text
    assert "Environment Validation" in text


def test_index_md_pipeline_stages_table(report_paths: ReportPaths) -> None:
    text = report_paths.index_md.read_text(encoding="utf-8")
    assert "Stages" in text
    assert "Gauss Sessions" in text


def test_summary_json_is_valid_json(report_paths: ReportPaths) -> None:
    data = json.loads(report_paths.summary_json.read_text(encoding="utf-8"))
    assert "status" in data
    assert data["status"] == "ok"
    assert "stages" in data
    assert data["source_digest"]
    assert data["config_digest"]
    assert "lean_toolchain" in data["toolchain"]
    assert data["warning_count"] == 0


def test_verification_manifest_json_matches_manuscript_schema(
    report_paths: ReportPaths,
) -> None:
    vm = report_paths.summary_json.parent / "verification_manifest.json"
    assert vm.is_file()
    raw = json.loads(vm.read_text(encoding="utf-8"))
    assert "verify_lean_ran" in raw
    assert "results" in raw and isinstance(raw["results"], list)
    block = _verify_block_from_manifest(vm)
    assert block["manifest_present"] is True


def test_hermes_report_md_structure(report_paths: ReportPaths) -> None:
    text = report_paths.hermes_md.read_text(encoding="utf-8")
    assert "Hermes" in text


def test_lean_report_md_structure(report_paths: ReportPaths) -> None:
    text = report_paths.lean_md.read_text(encoding="utf-8")
    assert "Lean" in text


def test_validation_md_has_checks(report_paths: ReportPaths) -> None:
    text = report_paths.validation_md.read_text(encoding="utf-8")
    assert "lean_cli" in text
    assert "ok" in text


def test_report_paths_as_dict(report_paths: ReportPaths) -> None:
    d = report_paths.as_dict()
    assert "index_md" in d
    assert "summary_json" in d
    assert "hermes_md" in d
    assert "lean_md" in d
    assert "validation_md" in d


def test_reporter_with_real_pipeline_result(tmp_path: Path) -> None:
    """Run the full catalogue-only pipeline and generate reports."""
    pl = FEPPipeline(PROJ)
    result = pl.run()
    reporter = Reporter(tmp_path)
    reporter.reports_dir = tmp_path / "full_run"
    paths = reporter.generate(TOPICS, result)
    assert paths.index_md.is_file()
    text = paths.index_md.read_text(encoding="utf-8")
    assert "Total Topics" in text
    # Should show the number of stages
    assert "Total Topics" in text


def test_reporter_rich_gauss_and_lean_logs(tmp_path: Path) -> None:
    """Exercise Hermes markdown, index stage details, and lean log sections."""
    r = PipelineResult(status="warning", total_duration=12.3)
    r.stages = [
        StepResult(
            name="Load Catalogue (Total Topics)",
            status="ok",
            duration_s=0.02,
            payload={"topics": [topic.id for topic in TOPICS.topics]},
        ),
        StepResult(
            name="Environment Validation",
            status="ok",
            duration_s=0.1,
            payload={
                "status": "ok",
                "failed_count": 0,
                "checks": [
                    {
                        "name": "fixture_check",
                        "ok": True,
                        "message": "fixture capability is available",
                        "duration_s": 0.01,
                    }
                ],
            },
        ),
        StepResult(
            name="Lean Verification",
            status="ok",
            duration_s=1.0,
            payload={"compiles_clean": 3},
        ),
        StepResult(
            name="Gauss Sessions",
            status="ok",
            duration_s=2.0,
            payload={
                "topics": [
                    {
                        "topic_id": "fep-001",
                        "success": False,
                        "hermes_success": False,
                        "error": "hermes offline",
                    },
                    {
                        "topic_id": "fep-002",
                        "success": True,
                        "hermes_success": True,
                        "lean_compiles": True,
                        "hermes_lean_compiles": True,
                        "cache_hit": False,
                        "tokens_used": 42,
                        "hermes_model": "z-ai/glm-5.1",
                        "explanation": "line1\nline2",
                        "refined_lean_sketch": "theorem x : True := True.intro",
                    },
                ]
            },
        ),
    ]
    r.lean_stats = {
        "total_processed": 2,
        "compiles_clean": 1,
        "compiles_with_sorry": 0,
        "compile_error": 1,
        "skipped": 0,
        "error_logs": ["e1"],
        "sorry_logs": ["s1"],
        "clean_logs": [],
    }
    rep = Reporter(tmp_path, run_id="test_rich")
    rep.reports_dir = tmp_path / "run_rich"
    paths = rep.generate(TOPICS, r)
    summary = json.loads(paths.summary_json.read_text(encoding="utf-8"))
    assert summary["status"] == "warning"
    hermes = paths.hermes_md.read_text(encoding="utf-8")
    assert "hermes offline" in hermes
    assert "theorem x" in hermes
    lean = paths.lean_md.read_text(encoding="utf-8")
    assert "fep-001: hermes offline" in lean
    assert '"compile_error": 1' in lean
    idx = paths.index_md.read_text(encoding="utf-8")
    assert "WARNING" in idx.upper() or "warning" in idx
    assert "3 compile clean" in idx or "Lean Verification" in idx


def _gauss_payload(rows: list[dict[str, object]]) -> dict[str, object]:
    return {"topics": rows}


def _result_with_gauss(rows: list[dict[str, object]]) -> PipelineResult:
    """Build a minimal PipelineResult with a Gauss Sessions stage payload."""
    normalized_rows: list[dict[str, object]] = []
    topics_by_id = {topic.id: topic for topic in TOPICS.topics}
    for raw in rows:
        row = dict(raw)
        if (
            row.get("success")
            and row.get("hermes_success")
            and row.get("lean_compiles")
        ):
            refined = str(
                row.get("refined_lean_sketch")
                or row.get("final_lean_sketch")
                or (
                    topics_by_id[str(row["topic_id"])].lean_sketch
                    if str(row["topic_id"]) in topics_by_id
                    else "theorem fixture : True := True.intro"
                )
            )
            row.setdefault("status", "success")
            row.setdefault("session_id", "fixture-session")
            row.setdefault("hermes_lean_compiles", True)
            row.setdefault("lean_has_sorry", False)
            row.setdefault("lean_warnings", [])
            row.setdefault("lean_version", LEAN_VERSION)
            row.setdefault("duration_s", 1.0)
            row.setdefault("error", "")
            row.setdefault("workflow", "verify")
            row.setdefault("stage_results", [])
            row.setdefault("explanation", "fixture")
            row.setdefault("refined_lean_sketch", refined)
            row.setdefault("final_lean_sketch", refined)
            row.setdefault("tokens_used", 1)
            row.setdefault("hermes_model", "fixture/provider-model")
            row.setdefault("cache_hit", False)
            row.setdefault("network_retries", 0)
            row.setdefault("chain_advance_reason", "")
        normalized_rows.append(row)
    r = PipelineResult(status="ok", total_duration=10.0)
    r.stages = [
        StepResult(
            name="Load Catalogue",
            status="ok",
            duration_s=0.01,
            payload={"topics": [row["topic_id"] for row in normalized_rows]},
        ),
        StepResult(
            name="Environment Validation",
            status="ok",
            duration_s=0.1,
            payload={
                "status": "ok",
                "failed_count": 0,
                "checks": [
                    {
                        "name": name,
                        "ok": True,
                        "message": f"{name} is available",
                        "duration_s": 0.01,
                    }
                    for name in FULL_VALIDATION_CHECK_NAMES
                ],
            },
        ),
        StepResult(
            name="Gauss Sessions",
            status="ok",
            duration_s=5.0,
            payload=_gauss_payload(normalized_rows),
        ),
        StepResult(
            name="Manuscript Artifacts",
            status="ok",
            duration_s=0.1,
            payload={"status": "ok"},
        ),
    ]
    lean_ok = sum(1 for r0 in normalized_rows if r0.get("lean_compiles"))
    lean_err = sum(1 for r0 in normalized_rows if r0.get("lean_compiles") is False)
    r.lean_stats = {
        "total_processed": len(normalized_rows),
        "compiles_clean": lean_ok,
        "compiles_with_sorry": 0,
        "compile_error": lean_err,
        "hermes_error": sum(
            1 for row in normalized_rows if not row.get("hermes_success")
        ),
        "warning_count": sum(
            len(row.get("lean_warnings", []))
            for row in normalized_rows
            if isinstance(row.get("lean_warnings", []), list)
        ),
        "skipped": 0,
        "error_logs": [],
        "sorry_logs": [],
        "clean_logs": [],
    }
    r.capabilities = {
        "catalogue": True,
        "verification": True,
        **{name: True for name in FULL_VALIDATION_CHECK_NAMES},
    }
    return r


def _write_toolchain_fixture(project_root: Path) -> None:
    """Copy the complete report-owner closure into a synthetic project root."""
    owners = set(source_owner_paths(PROJ)) | set(config_owner_paths(PROJ))
    for source in sorted(owners):
        relative = source.relative_to(PROJ)
        target = project_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def _complete_full_report(tmp_path: Path, run_id: str) -> ReportPaths:
    """Generate a live-roster claim-ready fixture against a complete owner tree."""
    _write_toolchain_fixture(tmp_path)
    rows = [
        {
            "topic_id": topic.id,
            "success": True,
            "hermes_success": True,
            "lean_compiles": True,
            "lean_has_sorry": False,
            "verification_source": "hermes_refined",
        }
        for topic in TOPICS.topics
    ]
    result = _result_with_gauss(rows)
    result.complete = True
    result.catalogue_topics = len(rows)
    result.verified_topics = len(rows)
    return Reporter(tmp_path, run_id=run_id).generate(TOPICS, result)


def _refresh_report_hashes(paths: ReportPaths, summary: dict[str, object]) -> None:
    """Refresh attacker-controlled hashes after an adversarial bundle rewrite."""
    summary["artifact_hashes"] = {
        path.relative_to(paths.root).as_posix(): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in sorted(paths.root.rglob("*"))
        if path.is_file() and path.name != "summary.json"
    }
    paths.summary_json.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def test_hermes_md_renders_aggregate_block(tmp_path: Path) -> None:
    """``_gen_hermes_md`` must surface the new aggregate header (cache hits,
    mean tokens, models used, Hermes-refined Lean compiled)."""
    rows = [
        {
            "topic_id": "fep-001",
            "success": True,
            "hermes_success": True,
            "lean_compiles": True,
            "hermes_lean_compiles": True,
            "cache_hit": True,
            "tokens_used": 1000,
            "hermes_model": "z-ai/glm-5.1",
            "explanation": "fixture",
            "refined_lean_sketch": "theorem t1 : True := True.intro",
        },
        {
            "topic_id": "fep-002",
            "success": True,
            "hermes_success": True,
            "lean_compiles": True,
            "hermes_lean_compiles": False,
            "cache_hit": False,
            "tokens_used": 2000,
            "hermes_model": "z-ai/glm-5.1",
            "explanation": "fixture",
            "refined_lean_sketch": "theorem t2 : True := True.intro",
        },
    ]
    rep = Reporter(tmp_path, run_id="test_aggregates")
    rep.reports_dir = tmp_path / "run_aggregates"
    paths = rep.generate(TOPICS, _result_with_gauss(rows))
    text = paths.hermes_md.read_text(encoding="utf-8")
    assert "Cache hits" in text
    assert "1/2" in text  # one cached out of two
    assert "Mean tokens/topic" in text
    assert "1500" in text  # (1000 + 2000) // 2
    assert "Models used" in text
    assert "z-ai/glm-5.1" in text
    assert "Hermes-refined Lean compiled" in text


def test_index_md_splits_lean_directly_vs_post_fallback(tmp_path: Path) -> None:
    """``_gen_index_md`` must report the directly-compiled and final-compiled
    Lean rates as separate bullets."""
    rows = [
        {
            "topic_id": "fep-001",
            "success": True,
            "hermes_success": True,
            "lean_compiles": True,
            "hermes_lean_compiles": True,
            "cache_hit": False,
            "tokens_used": 500,
            "hermes_model": "z-ai/glm-5.1",
        },
        {
            "topic_id": "fep-002",
            "success": True,
            "hermes_success": True,
            "lean_compiles": True,
            "hermes_lean_compiles": False,
            "cache_hit": False,
            "tokens_used": 500,
            "hermes_model": "z-ai/glm-5.1",
        },
    ]
    rep = Reporter(tmp_path, run_id="test_split")
    rep.reports_dir = tmp_path / "run_split"
    paths = rep.generate(TOPICS, _result_with_gauss(rows))
    text = paths.index_md.read_text(encoding="utf-8")
    assert "Hermes-refined Lean compiled directly" in text
    assert "Final Lean compiled" in text
    # 1 of 2 compiled directly; 2 of 2 finally compiled (1 via fallback)
    assert "1/2" in text
    assert "2/2" in text
    assert "Final Lean compiled" in text


def test_index_and_summary_use_selected_topics_and_hash_nested_artifacts(
    tmp_path: Path,
) -> None:
    rows = [
        {
            "topic_id": "fep-001",
            "success": False,
            "hermes_success": False,
            "lean_compiles": False,
        }
    ]
    result = _result_with_gauss(rows)
    result.catalogue_topics = 1
    rep = Reporter(tmp_path, run_id="test_selected_topics")
    paths = rep.generate(TOPICS, result)
    index = paths.index_md.read_text(encoding="utf-8")
    assert "**Total Topics:** 1" in index
    assert f"**Catalogue Topics:** {len(TOPICS.roster.topic_ids)}" in index
    summary = json.loads(paths.summary_json.read_text(encoding="utf-8"))
    hashes = summary["artifact_hashes"]
    assert "topics/fep-001.md" in hashes
    assert hashes["topics/fep-001.md"]
    root = paths.summary_json.parent.resolve()
    for relative, digest in hashes.items():
        artifact = (root / relative).resolve()
        assert root in artifact.parents
        assert artifact.is_file()
        assert hashlib.sha256(artifact.read_bytes()).hexdigest() == digest
    assert "summary.json" not in hashes
    run_manifest = json.loads((root / "run_manifest.json").read_text(encoding="utf-8"))
    assert run_manifest["live_catalogue_topics"] == len(TOPICS.topics)
    assert run_manifest["selected_topics"] == 1
    assert run_manifest["complete"] is False
    assert len(run_manifest["topics"]) == 1


def test_validate_report_receipt_accepts_catalogue_bundle(tmp_path: Path) -> None:
    result = PipelineResult(
        status="ok",
        mode="catalogue",
        complete=True,
        catalogue_topics=len(TOPICS.roster.topic_ids),
        verified_topics=0,
    )
    result.stages = [
        StepResult(
            name="Load Catalogue",
            status="ok",
            payload={"topics": [topic.id for topic in TOPICS.topics]},
        ),
        StepResult(
            name="Environment Validation",
            status="ok",
            payload={
                "status": "ok",
                "failed_count": 0,
                "checks": [
                    {
                        "name": name,
                        "ok": True,
                        "message": f"{name} is available",
                        "duration_s": 0.01,
                    }
                    for name in CATALOGUE_VALIDATION_CHECK_NAMES
                ],
            },
        ),
        StepResult(name="Gauss Sessions", status="not_run"),
        StepResult(name="Manuscript Artifacts", status="ok"),
    ]
    result.capabilities = {
        "catalogue": True,
        "verification": False,
        **{name: True for name in CATALOGUE_VALIDATION_CHECK_NAMES},
    }
    rep = Reporter(tmp_path, run_id="run_catalogue_receipt")
    paths = rep.generate(TOPICS, result)

    receipt = validate_report_receipt(paths.root)

    assert receipt["valid"] is True
    assert receipt["claim_ready"] is False
    assert receipt["mode"] == "catalogue"
    assert receipt["selected_topics"] == len(TOPICS.roster.topic_ids)
    assert receipt["checked_artifacts"] >= 6


def test_validate_report_receipt_accepts_partial_full_bundle_but_denies_claim(
    tmp_path: Path,
) -> None:
    _write_toolchain_fixture(tmp_path)
    rows = [
        {
            "topic_id": "fep-001",
            "success": True,
            "hermes_success": True,
            "lean_compiles": True,
            "lean_has_sorry": False,
            "verification_source": "hermes_refined",
        }
    ]
    result = _result_with_gauss(rows)
    result.complete = True
    result.catalogue_topics = 1
    result.verified_topics = 1
    rep = Reporter(tmp_path, run_id="run_full_receipt")
    paths = rep.generate(TOPICS, result)

    receipt = validate_report_receipt(
        paths.root,
        project_root=tmp_path,
    )

    assert receipt["valid"] is True
    assert receipt["claim_ready"] is False
    assert receipt["mode"] == "full"
    assert receipt["live_catalogue_topics"] == len(TOPICS.topics)
    assert receipt["selected_topics"] == receipt["verified_topics"] == 1
    assert receipt["errors"] == []
    summary = json.loads(paths.summary_json.read_text(encoding="utf-8"))
    assert summary["receipt_schema_version"] == 4
    assert "catalogue_topics" not in summary
    assert summary["roster_sha256"]
    assert summary["catalogue_sources_sha256"]
    assert summary["toolchain"]["lean_version"] == LEAN_VERSION
    assert len(summary["toolchain"]["mathlib_revision"]) == 40


def test_reporter_rejects_topic_absent_from_catalogue_before_writing(
    tmp_path: Path,
) -> None:
    result = _result_with_gauss(
        [
            {
                "topic_id": "fep-999",
                "success": False,
                "hermes_success": False,
                "lean_compiles": False,
            }
        ]
    )

    with pytest.raises(ValueError, match="absent from the catalogue"):
        Reporter(tmp_path, run_id="run_unknown_topic").generate(TOPICS, result)

    assert not (tmp_path / "output" / "reports" / "run_unknown_topic").exists()


def test_complete_receipt_rejects_internally_consistent_unknown_topic(
    tmp_path: Path,
) -> None:
    paths = _complete_full_report(tmp_path, "run_unknown_topic_receipt")
    summary = json.loads(paths.summary_json.read_text(encoding="utf-8"))
    run_manifest = json.loads(paths.run_manifest_json.read_text(encoding="utf-8"))
    verification = json.loads(paths.manifest_json.read_text(encoding="utf-8"))
    for payload, field in (
        (summary, "topics"),
        (run_manifest, "topics"),
        (verification, "results"),
    ):
        payload[field][0]["topic_id"] = "fep-999"
    summary["selected_topic_ids"] = ["fep-999"]
    summary["selection"]["topic_ids"] = ["fep-999"]
    run_manifest["selected_topic_ids"] = ["fep-999"]
    run_manifest["selection"]["topic_ids"] = ["fep-999"]
    paths.run_manifest_json.write_text(
        json.dumps(run_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    paths.manifest_json.write_text(
        json.dumps(verification, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    renderer = Reporter(tmp_path, run_id=paths.root.name)
    paths.hermes_md.write_text(renderer._hermes_md(summary["topics"]), encoding="utf-8")
    old_topic = paths.root / "topics" / "fep-001.md"
    old_topic.unlink()
    (paths.root / "topics" / "fep-999.md").write_text(
        renderer._topic_md(summary["topics"][0]), encoding="utf-8"
    )
    _refresh_report_hashes(paths, summary)

    receipt = validate_report_receipt(
        paths.root, require_complete=True, project_root=tmp_path
    )

    assert receipt["claim_ready"] is False
    assert any("absent from the live catalogue" in error for error in receipt["errors"])


def test_incomplete_synthetic_root_cannot_source_bind(tmp_path: Path) -> None:
    minimal_root = tmp_path / "minimal"
    lean_dir = minimal_root / "lean"
    lean_dir.mkdir(parents=True)
    for name in ("lean-toolchain", "lakefile.lean", "lake-manifest.json"):
        shutil.copy2(PROJ / "lean" / name, lean_dir / name)
    result = _result_with_gauss(
        [
            {
                "topic_id": "fep-001",
                "success": True,
                "hermes_success": True,
                "lean_compiles": True,
                "lean_has_sorry": False,
                "verification_source": "hermes_refined",
            }
        ]
    )
    result.complete = True
    result.catalogue_topics = result.verified_topics = 1
    paths = Reporter(minimal_root, run_id="run_incomplete_owner_root").generate(
        TOPICS, result
    )

    receipt = validate_report_receipt(paths.root, project_root=minimal_root)

    assert receipt["source_bound"] is False
    assert receipt["claim_ready"] is False
    assert any(
        "canonical report owner is missing" in error for error in receipt["errors"]
    )


@pytest.mark.parametrize("tamper", ["weakened_type", "indented_axiom"])
def test_complete_receipt_rejects_provider_source_semantic_tamper(
    tmp_path: Path,
    tamper: str,
) -> None:
    paths = _complete_full_report(tmp_path, f"run_semantic_tamper_{tamper}")
    summary = json.loads(paths.summary_json.read_text(encoding="utf-8"))
    run_manifest = json.loads(paths.run_manifest_json.read_text(encoding="utf-8"))
    verification = json.loads(paths.manifest_json.read_text(encoding="utf-8"))
    canonical = next(
        topic for topic in TOPICS.topics if topic.id == "fep-001"
    ).lean_sketch
    if tamper == "weakened_type":
        changed = (
            "import Mathlib.InformationTheory.KullbackLeibler.Basic\n\n"
            "namespace FEP001\n"
            "theorem fep001_variationalUpperBound_eq_iff : True := True.intro\n"
            "end FEP001\n"
        )
    else:
        changed = canonical.replace(
            "  exact le_add_right (le_refl _)",
            "  exact le_add_right (le_refl _)\n\n  axiom semanticEscape : False",
            1,
        ).replace(
            "  exact InformationTheory.klDiv_eq_zero_iff",
            "  exact False.elim semanticEscape",
            1,
        )
    compiled_digest = hashlib.sha256(changed.encode("utf-8")).hexdigest()
    for payload, field in (
        (summary, "topics"),
        (run_manifest, "topics"),
        (verification, "results"),
    ):
        payload[field][0].update(
            {
                "refined_lean_sketch": changed,
                "final_lean_sketch": changed,
                "compiled_source_sha256": compiled_digest,
                "semantic_contract_preserved": True,
            }
        )
    paths.run_manifest_json.write_text(
        json.dumps(run_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    paths.manifest_json.write_text(
        json.dumps(verification, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    renderer = Reporter(tmp_path, run_id=paths.root.name)
    paths.hermes_md.write_text(renderer._hermes_md(summary["topics"]), encoding="utf-8")
    (paths.root / "topics" / "fep-001.md").write_text(
        renderer._topic_md(summary["topics"][0]), encoding="utf-8"
    )
    _refresh_report_hashes(paths, summary)

    receipt = validate_report_receipt(
        paths.root, require_complete=True, project_root=tmp_path
    )

    assert receipt["claim_ready"] is False
    assert any(
        "changes the live canonical token contract" in error
        for error in receipt["errors"]
    )


@pytest.mark.parametrize("tamper", ["omit", "substitute"])
def test_complete_receipt_requires_exact_full_preflight_policy(
    tmp_path: Path,
    tamper: str,
) -> None:
    paths = _complete_full_report(tmp_path, f"run_preflight_{tamper}")
    summary = json.loads(paths.summary_json.read_text(encoding="utf-8"))
    run_manifest = json.loads(paths.run_manifest_json.read_text(encoding="utf-8"))
    if tamper == "omit":
        summary["validation"]["checks"] = summary["validation"]["checks"][:-1]
        summary["capabilities"].pop("hermes_credentials")
    else:
        summary["validation"]["checks"][-1]["name"] = "pretend_credentials"
        summary["capabilities"]["pretend_credentials"] = summary["capabilities"].pop(
            "hermes_credentials"
        )
    run_manifest["validation"] = summary["validation"]
    run_manifest["capabilities"] = summary["capabilities"]
    paths.validation_md.write_text(
        _render_validation_markdown(summary["validation"]), encoding="utf-8"
    )
    paths.run_manifest_json.write_text(
        json.dumps(run_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    _refresh_report_hashes(paths, summary)

    receipt = validate_report_receipt(
        paths.root, require_complete=True, project_root=tmp_path
    )

    assert receipt["claim_ready"] is False
    assert any("required policy" in error for error in receipt["errors"])


def test_complete_receipt_rejects_summary_run_id_tamper(tmp_path: Path) -> None:
    paths = _complete_full_report(tmp_path, "run_id_bound")
    summary = json.loads(paths.summary_json.read_text(encoding="utf-8"))
    summary["run_id"] = "run_other"
    paths.summary_json.write_text(json.dumps(summary), encoding="utf-8")

    receipt = validate_report_receipt(
        paths.root, require_complete=True, project_root=tmp_path
    )

    assert receipt["claim_ready"] is False
    assert any("summary run_id" in error for error in receipt["errors"])


def test_complete_receipt_rejects_rehashed_markdown_projection_tamper(
    tmp_path: Path,
) -> None:
    paths = _complete_full_report(tmp_path, "run_markdown_tamper")
    summary = json.loads(paths.summary_json.read_text(encoding="utf-8"))
    topic_path = paths.root / "topics" / "fep-001.md"
    topic_path.write_text("# Fabricated human projection\n", encoding="utf-8")
    _refresh_report_hashes(paths, summary)

    receipt = validate_report_receipt(
        paths.root, require_complete=True, project_root=tmp_path
    )

    assert receipt["claim_ready"] is False
    assert any(
        "topics/fep-001.md does not match its structured evidence" in error
        for error in receipt["errors"]
    )


def test_complete_full_receipt_rejects_missing_topic_artifact(
    tmp_path: Path,
) -> None:
    _write_toolchain_fixture(tmp_path)
    result = _result_with_gauss(
        [
            {
                "topic_id": "fep-001",
                "success": True,
                "hermes_success": True,
                "lean_compiles": True,
                "lean_has_sorry": False,
                "verification_source": "hermes_refined",
            }
        ]
    )
    result.complete = True
    result.catalogue_topics = 1
    result.verified_topics = 1
    paths = Reporter(tmp_path, run_id="run_missing_topic_artifact").generate(
        TOPICS, result
    )
    topic_path = paths.root / "topics" / "fep-001.md"
    topic_path.unlink()
    summary = json.loads(paths.summary_json.read_text(encoding="utf-8"))
    summary["artifact_hashes"].pop("topics/fep-001.md")
    paths.summary_json.write_text(json.dumps(summary), encoding="utf-8")

    receipt = validate_report_receipt(
        paths.root,
        require_complete=True,
        project_root=tmp_path,
    )

    assert receipt["valid"] is False
    assert receipt["claim_ready"] is False
    assert any(
        "per-topic artifacts are not hashed" in error for error in receipt["errors"]
    )


def test_complete_full_receipt_rejects_erased_provider_semantics(
    tmp_path: Path,
) -> None:
    """Redundant, consistently tampered rows cannot retain claim readiness."""
    _write_toolchain_fixture(tmp_path)
    result = _result_with_gauss(
        [
            {
                "topic_id": "fep-001",
                "success": True,
                "hermes_success": True,
                "lean_compiles": True,
                "lean_has_sorry": False,
                "verification_source": "hermes_refined",
            }
        ]
    )
    result.complete = True
    result.catalogue_topics = 1
    result.verified_topics = 1
    paths = Reporter(tmp_path, run_id="run_erased_provider_semantics").generate(
        TOPICS, result
    )
    summary = json.loads(paths.summary_json.read_text(encoding="utf-8"))
    run_manifest = json.loads(paths.run_manifest_json.read_text(encoding="utf-8"))
    verification = json.loads(paths.manifest_json.read_text(encoding="utf-8"))
    erased = {
        "hermes_success": False,
        "hermes_lean_compiles": False,
        "session_id": "",
        "hermes_model": "",
        "refined_lean_sketch": "",
        "final_lean_sketch": "",
        "compiled_source_sha256": "",
    }
    summary["topics"][0].update(erased)
    run_manifest["topics"][0].update(erased)
    verification["results"][0].update(erased)
    paths.run_manifest_json.write_text(json.dumps(run_manifest), encoding="utf-8")
    paths.manifest_json.write_text(json.dumps(verification), encoding="utf-8")
    summary["artifact_hashes"]["run_manifest.json"] = hashlib.sha256(
        paths.run_manifest_json.read_bytes()
    ).hexdigest()
    summary["artifact_hashes"]["verification_manifest.json"] = hashlib.sha256(
        paths.manifest_json.read_bytes()
    ).hexdigest()
    paths.summary_json.write_text(json.dumps(summary), encoding="utf-8")

    receipt = validate_report_receipt(
        paths.root,
        require_complete=True,
        project_root=tmp_path,
    )

    assert receipt["valid"] is False
    assert receipt["claim_ready"] is False
    assert any("hermes_success=true" in error for error in receipt["errors"])
    assert any("final compiled Lean source" in error for error in receipt["errors"])
    assert any("non-empty session_id" in error for error in receipt["errors"])


def test_complete_full_receipt_rejects_contradictory_pipeline_state(
    tmp_path: Path,
) -> None:
    """Clean rows cannot override failed capability and stage evidence."""
    _write_toolchain_fixture(tmp_path)
    result = _result_with_gauss(
        [
            {
                "topic_id": "fep-001",
                "success": True,
                "hermes_success": True,
                "lean_compiles": True,
                "lean_has_sorry": False,
                "verification_source": "hermes_refined",
            }
        ]
    )
    result.complete = True
    result.catalogue_topics = 1
    result.verified_topics = 1
    paths = Reporter(tmp_path, run_id="run_contradictory_pipeline").generate(
        TOPICS, result
    )
    summary = json.loads(paths.summary_json.read_text(encoding="utf-8"))
    run_manifest = json.loads(paths.run_manifest_json.read_text(encoding="utf-8"))
    failed_capabilities = {
        "catalogue": False,
        "verification": False,
        "fixture_check": False,
    }
    failed_validation = {
        "status": "error",
        "failed_count": 1,
        "checks": [
            {
                "name": "fixture_check",
                "ok": False,
                "message": "fixture capability failed",
                "duration_s": 0.01,
            }
        ],
    }
    summary["capabilities"] = failed_capabilities
    run_manifest["capabilities"] = failed_capabilities
    summary["validation"] = failed_validation
    run_manifest["validation"] = failed_validation
    summary["failure_reason"] = "required capability checks failed"
    run_manifest["failure_reason"] = "required capability checks failed"
    environment_stage = next(
        stage
        for stage in summary["stages"]
        if stage["name"] == "Environment Validation"
    )
    environment_stage["status"] = "error"
    environment_stage["error"] = "required capability checks failed"
    paths.validation_md.write_text(
        "# Environment validation\n\n"
        "Status: `error`\n\n"
        "- `fixture_check`: `False` — fixture capability failed\n",
        encoding="utf-8",
    )
    paths.run_manifest_json.write_text(json.dumps(run_manifest), encoding="utf-8")
    summary["artifact_hashes"]["run_manifest.json"] = hashlib.sha256(
        paths.run_manifest_json.read_bytes()
    ).hexdigest()
    summary["artifact_hashes"]["validation.md"] = hashlib.sha256(
        paths.validation_md.read_bytes()
    ).hexdigest()
    paths.summary_json.write_text(json.dumps(summary), encoding="utf-8")

    receipt = validate_report_receipt(
        paths.root,
        require_complete=True,
        project_root=tmp_path,
    )

    assert receipt["valid"] is False
    assert receipt["claim_ready"] is False
    assert any("failed capability" in error for error in receipt["errors"])
    assert any(
        "environment validation must be ok" in error for error in receipt["errors"]
    )
    assert any("stage 'Environment Validation'" in error for error in receipt["errors"])
    assert any("failure_reason must be empty" in error for error in receipt["errors"])


def test_complete_receipt_rejects_rehashed_derived_statistics_tamper(
    tmp_path: Path,
) -> None:
    """Rehashed projections cannot make fabricated derived evidence authoritative."""
    paths = _complete_full_report(tmp_path, "run_derived_statistics_tamper")
    summary = json.loads(paths.summary_json.read_text(encoding="utf-8"))
    run_manifest = json.loads(paths.run_manifest_json.read_text(encoding="utf-8"))

    fabricated_stats = {
        "fabricated_metric": 999,
        "topics_total": 999,
        "stages_ok": -20,
    }
    fabricated_lean_stats = {
        **summary["lean_stats"],
        "error_logs": ["fabricated compiler failure"],
    }
    for payload in (summary, run_manifest):
        payload["stats"] = fabricated_stats
        payload["lean_stats"] = fabricated_lean_stats
        payload["validation"]["failed_count"] = False

    renderer = Reporter(tmp_path, run_id=paths.root.name)
    proxy = SimpleNamespace(
        status=summary["status"],
        mode=summary["mode"],
        catalogue_topics=summary["selected_topics"],
        verified_topics=summary["verified_topics"],
        stages=[SimpleNamespace(**stage) for stage in summary["stages"]],
        stats=fabricated_stats,
    )
    paths.index_md.write_text(
        renderer._index_md(TOPICS, proxy, topics=summary["topics"]),
        encoding="utf-8",
    )
    paths.lean_md.write_text(renderer._lean_md(fabricated_lean_stats), encoding="utf-8")
    paths.validation_md.write_text(
        _render_validation_markdown(summary["validation"]), encoding="utf-8"
    )
    paths.run_manifest_json.write_text(
        json.dumps(run_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    _refresh_report_hashes(paths, summary)

    receipt = validate_report_receipt(
        paths.root, require_complete=True, project_root=tmp_path
    )

    assert receipt["claim_ready"] is False
    assert any(
        "failed_count must be a non-negative integer" in error
        for error in receipt["errors"]
    )
    assert "summary lean_stats disagree with canonical topic rows" in receipt["errors"]
    assert (
        "summary stats disagree with canonical topic rows and stages"
        in receipt["errors"]
    )


def test_complete_full_receipt_without_live_source_is_not_claim_ready(
    tmp_path: Path,
) -> None:
    _write_toolchain_fixture(tmp_path)
    rows = [
        {
            "topic_id": "fep-001",
            "success": True,
            "hermes_success": True,
            "lean_compiles": True,
            "lean_has_sorry": False,
            "lean_warnings": [],
            "verification_source": "hermes_refined",
        }
    ]
    result = _result_with_gauss(rows)
    result.complete = True
    result.catalogue_topics = 1
    result.verified_topics = 1
    paths = Reporter(tmp_path, run_id="run_unbound_full_receipt").generate(
        TOPICS,
        result,
    )

    receipt = validate_report_receipt(paths.root)

    assert receipt["valid"] is True
    assert receipt["source_bound"] is False
    assert receipt["claim_ready"] is False


def test_live_source_binding_ignores_python_cache_bytes(tmp_path: Path) -> None:
    paths = _complete_full_report(tmp_path, "run_cache_independent_receipt")
    cache = tmp_path / "src" / "fep_lean" / "__pycache__"
    cache.mkdir(parents=True, exist_ok=True)
    (cache / "ignored.cpython-314.pyc").write_bytes(b"not a source owner")

    receipt = validate_report_receipt(
        paths.root,
        require_complete=True,
        project_root=tmp_path,
    )

    assert receipt["valid"] is True
    assert receipt["source_bound"] is True
    assert receipt["claim_ready"] is True


def test_report_receipt_rejects_warning_bearing_full_claim(tmp_path: Path) -> None:
    _write_toolchain_fixture(tmp_path)
    rows = [
        {
            "topic_id": "fep-001",
            "success": True,
            "hermes_success": True,
            "lean_compiles": True,
            "lean_has_sorry": False,
            "lean_warnings": ["fixture warning"],
            "verification_source": "hermes_refined",
        }
    ]
    result = _result_with_gauss(rows)
    result.complete = True
    result.catalogue_topics = 1
    result.verified_topics = 1
    paths = Reporter(tmp_path, run_id="run_warning_receipt").generate(TOPICS, result)

    receipt = validate_report_receipt(paths.root, require_complete=True)

    assert receipt["valid"] is False
    assert receipt["claim_ready"] is False
    assert any("warnings" in error for error in receipt["errors"])


def test_report_receipt_preserves_exact_warning_across_evidence_surfaces(
    tmp_path: Path,
) -> None:
    warning = "FepSketches/fep_all.lean:17:2: declaration uses 'sorry'"
    rows = [
        {
            "topic_id": "fep-001",
            "success": False,
            "hermes_success": True,
            "lean_compiles": True,
            "lean_has_sorry": False,
            "lean_warnings": [warning],
            "verification_source": "hermes_refined",
        }
    ]
    result = _result_with_gauss(rows)
    result.complete = False
    result.catalogue_topics = 1
    result.verified_topics = 0
    paths = Reporter(tmp_path, run_id="run_warning_carrier").generate(TOPICS, result)

    summary = json.loads(paths.summary_json.read_text(encoding="utf-8"))
    run_manifest = json.loads(paths.run_manifest_json.read_text(encoding="utf-8"))
    verification = json.loads(paths.manifest_json.read_text(encoding="utf-8"))
    topic_markdown = (paths.root / "topics" / "fep-001.md").read_text(encoding="utf-8")

    assert summary["topics"][0]["lean_warnings"] == [warning]
    assert run_manifest["topics"][0]["lean_warnings"] == [warning]
    assert verification["results"][0]["warnings"] == [warning]
    assert summary["warning_count"] == run_manifest["warning_count"] == 1
    assert verification["warning_count"] == 1
    assert warning in topic_markdown
    receipt = validate_report_receipt(paths.root)
    assert receipt["valid"] is True
    assert receipt["claim_ready"] is False

    # Removing warning evidence from only one redundant surface must fail even
    # when the attacker updates the summary's artifact hash for that file.
    run_manifest["topics"][0]["lean_warnings"] = []
    paths.run_manifest_json.write_text(json.dumps(run_manifest), encoding="utf-8")
    summary["artifact_hashes"]["run_manifest.json"] = hashlib.sha256(
        paths.run_manifest_json.read_bytes()
    ).hexdigest()
    paths.summary_json.write_text(json.dumps(summary), encoding="utf-8")
    drifted = validate_report_receipt(paths.root)
    assert drifted["valid"] is False
    assert any("run manifest warnings disagree" in error for error in drifted["errors"])


def test_report_receipt_requires_matching_owner_manifest_version(
    tmp_path: Path,
) -> None:
    _write_toolchain_fixture(tmp_path)
    rows = [
        {
            "topic_id": "fep-001",
            "success": True,
            "hermes_success": True,
            "lean_compiles": True,
            "lean_has_sorry": False,
            "lean_warnings": [],
            "verification_source": "hermes_refined",
        }
    ]
    result = _result_with_gauss(rows)
    result.complete = True
    result.catalogue_topics = 1
    result.verified_topics = 1
    paths = Reporter(tmp_path, run_id="run_owner_manifest").generate(TOPICS, result)
    summary = json.loads(paths.summary_json.read_text(encoding="utf-8"))
    run_manifest = json.loads(paths.run_manifest_json.read_text(encoding="utf-8"))
    assert summary["owner_manifest_version"] == OWNER_MANIFEST_VERSION
    assert run_manifest["owner_manifest_version"] == OWNER_MANIFEST_VERSION

    run_manifest["owner_manifest_version"] = 999
    paths.run_manifest_json.write_text(json.dumps(run_manifest), encoding="utf-8")
    summary["artifact_hashes"]["run_manifest.json"] = hashlib.sha256(
        paths.run_manifest_json.read_bytes()
    ).hexdigest()
    paths.summary_json.write_text(json.dumps(summary), encoding="utf-8")
    receipt = validate_report_receipt(paths.root, project_root=tmp_path)
    assert receipt["valid"] is False
    assert any("owner manifest version" in error for error in receipt["errors"])


def test_report_receipt_cli_binds_validation_to_explicit_live_root(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    captured: dict[str, object] = {}

    def fake_validate(report_root: Path, **kwargs: object) -> dict[str, object]:
        captured.update(report_root=report_root, **kwargs)
        return {"valid": True}

    monkeypatch.setattr(receipt_cli, "validate_report_receipt", fake_validate)
    report_root = tmp_path / "report"
    live_root = tmp_path / "checkout"

    assert (
        receipt_cli.main(
            [str(report_root), "--project-root", str(live_root), "--require-complete"]
        )
        == 0
    )
    assert captured == {
        "report_root": report_root,
        "require_complete": True,
        "project_root": live_root.resolve(),
    }
    assert json.loads(capsys.readouterr().out)["valid"] is True


def test_report_receipt_cli_defaults_to_repository_live_root(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    captured: dict[str, object] = {}

    def fake_validate(report_root: Path, **kwargs: object) -> dict[str, object]:
        captured.update(report_root=report_root, **kwargs)
        return {"valid": True}

    monkeypatch.setattr(receipt_cli, "validate_report_receipt", fake_validate)
    assert receipt_cli.main([str(tmp_path / "report")]) == 0
    assert captured["project_root"] == PROJ.resolve()
    assert captured["require_complete"] is False
    assert json.loads(capsys.readouterr().out)["valid"] is True


def test_validate_report_receipt_rejects_string_verification_flags(
    tmp_path: Path,
) -> None:
    rows = [
        {
            "topic_id": "fep-001",
            "success": True,
            "hermes_success": True,
            "lean_compiles": True,
            "lean_has_sorry": False,
            "verification_source": "hermes_refined",
        }
    ]
    result = _result_with_gauss(rows)
    result.complete = True
    result.catalogue_topics = 1
    result.verified_topics = 1
    rep = Reporter(tmp_path, run_id="run_string_flags_receipt")
    paths = rep.generate(TOPICS, result)

    summary = json.loads(paths.summary_json.read_text(encoding="utf-8"))
    verification = json.loads(
        (paths.root / "verification_manifest.json").read_text(encoding="utf-8")
    )
    summary["topics"][0].update(
        {"success": "true", "lean_compiles": "true", "lean_has_sorry": "false"}
    )
    verification["results"][0].update({"compiles": "true", "lean_has_sorry": "false"})
    paths.summary_json.write_text(json.dumps(summary), encoding="utf-8")
    (paths.root / "verification_manifest.json").write_text(
        json.dumps(verification), encoding="utf-8"
    )

    receipt = validate_report_receipt(paths.root, require_complete=True)

    assert receipt["valid"] is False
    assert any(
        "summary topic fep-001 success must be a boolean" in error
        for error in receipt["errors"]
    )
    assert any(
        "summary topic fep-001 lean_compiles must be a boolean" in error
        for error in receipt["errors"]
    )
    assert any(
        "summary topic fep-001 lean_has_sorry must be a boolean" in error
        for error in receipt["errors"]
    )
    assert any(
        "verification topic fep-001 compiles must be a boolean" in error
        for error in receipt["errors"]
    )
    assert any(
        "verification topic fep-001 lean_has_sorry must be a boolean" in error
        for error in receipt["errors"]
    )
    assert "complete full-mode receipt is required" in receipt["errors"]


def test_validate_report_receipt_detects_tampering_and_path_escape(
    tmp_path: Path,
) -> None:
    rep = Reporter(tmp_path, run_id="run_tamper_receipt")
    paths = rep.generate(TOPICS, _minimal_result(tmp_path))
    root = paths.root

    paths.index_md.write_text(
        paths.index_md.read_text(encoding="utf-8") + "tampered\n", encoding="utf-8"
    )
    summary = json.loads(paths.summary_json.read_text(encoding="utf-8"))
    summary["artifact_hashes"]["../outside.txt"] = "0" * 64
    paths.summary_json.write_text(json.dumps(summary), encoding="utf-8")

    receipt = validate_report_receipt(root)

    assert receipt["valid"] is False
    assert any("hash mismatch" in error for error in receipt["errors"])
    assert any("escapes report directory" in error for error in receipt["errors"])


def test_validate_report_receipt_rejects_unlisted_artifact(tmp_path: Path) -> None:
    paths = Reporter(tmp_path, run_id="run_unlisted_artifact").generate(
        TOPICS, _minimal_result(tmp_path)
    )
    (paths.root / "unlisted.txt").write_text(
        "not in hash inventory\n", encoding="utf-8"
    )

    receipt = validate_report_receipt(paths.root)

    assert receipt["valid"] is False
    assert any(
        "report artifacts are not hashed: unlisted.txt" in error
        for error in receipt["errors"]
    )


def test_validate_report_receipt_rejects_missing_and_malformed_manifests(
    tmp_path: Path,
) -> None:
    missing = validate_report_receipt(tmp_path / "missing_receipt")
    assert missing["valid"] is False
    assert any("report directory is missing" in error for error in missing["errors"])

    root = tmp_path / "malformed_receipt"
    root.mkdir()
    (root / "summary.json").write_text("{", encoding="utf-8")
    (root / "run_manifest.json").write_text("[]", encoding="utf-8")

    receipt = validate_report_receipt(root)

    assert receipt["valid"] is False
    assert any("invalid summary.json" in error for error in receipt["errors"])
    assert any(
        "run_manifest.json must contain a JSON object" in error
        for error in receipt["errors"]
    )
    assert any(
        "missing verification_manifest.json" in error for error in receipt["errors"]
    )


def test_validate_report_receipt_checks_summary_types_and_required_hashes(
    tmp_path: Path,
) -> None:
    rep = Reporter(tmp_path, run_id="run_invalid_summary_receipt")
    paths = rep.generate(
        TOPICS,
        PipelineResult(
            status="ok", mode="catalogue", complete=True, catalogue_topics=50
        ),
    )
    summary = json.loads(paths.summary_json.read_text(encoding="utf-8"))
    summary.update(
        {
            "mode": "unsupported",
            "complete": "yes",
            "selected_topics": True,
            "verified_topics": -1,
            "topics": "not-a-list",
            "source_digest": "bad",
            "config_digest": None,
            "toolchain": [],
            "artifact_hashes": [],
        }
    )
    paths.summary_json.write_text(json.dumps(summary), encoding="utf-8")

    receipt = validate_report_receipt(paths.root)

    assert receipt["valid"] is False
    expected_errors = (
        "summary mode is unsupported",
        "summary complete must be a boolean",
        "summary selected_topics must be a non-negative integer",
        "summary verified_topics must be a non-negative integer",
        "summary topics must be a list of objects",
        "summary source_digest must be a lowercase SHA-256 digest",
        "summary config_digest must be a lowercase SHA-256 digest",
        "summary toolchain must be an object",
        "summary artifact_hashes must be an object",
        "required artifacts are not hashed",
    )
    assert all(
        any(expected in error for error in receipt["errors"])
        for expected in expected_errors
    ), receipt["errors"]


def test_validate_report_receipt_rejects_invalid_artifact_entries(
    tmp_path: Path,
) -> None:
    rep = Reporter(tmp_path, run_id="run_invalid_artifact_receipt")
    paths = rep.generate(TOPICS, _minimal_result(tmp_path))
    summary = json.loads(paths.summary_json.read_text(encoding="utf-8"))
    hashes = summary["artifact_hashes"]
    hashes[""] = "0" * 64
    hashes["/absolute.txt"] = "0" * 64
    hashes["."] = "0" * 64
    hashes["missing.txt"] = "0" * 64
    hashes["index.md"] = "not-a-digest"
    paths.summary_json.write_text(json.dumps(summary), encoding="utf-8")

    receipt = validate_report_receipt(paths.root)

    assert receipt["valid"] is False
    assert any("non-empty strings" in error for error in receipt["errors"])
    assert sum("escapes report directory" in error for error in receipt["errors"]) >= 2
    assert any(
        "hashed artifact is missing: missing.txt" in error
        for error in receipt["errors"]
    )
    assert any(
        "invalid SHA-256 digest for artifact: index.md" in error
        for error in receipt["errors"]
    )
    assert any(
        "required artifacts are not hashed" in error for error in receipt["errors"]
    )


def test_validate_report_receipt_reconciles_rows_and_verification_counters(
    tmp_path: Path,
) -> None:
    rows = [
        {
            "topic_id": "fep-001",
            "success": True,
            "hermes_success": True,
            "lean_compiles": True,
            "lean_has_sorry": False,
            "verification_source": "hermes_refined",
        }
    ]
    result = _result_with_gauss(rows)
    result.catalogue_topics = 1
    result.verified_topics = 1
    rep = Reporter(tmp_path, run_id="run_inconsistent_rows_receipt")
    paths = rep.generate(TOPICS, result)

    summary = json.loads(paths.summary_json.read_text(encoding="utf-8"))
    run_manifest = json.loads(
        (paths.root / "run_manifest.json").read_text(encoding="utf-8")
    )
    verification = json.loads(
        (paths.root / "verification_manifest.json").read_text(encoding="utf-8")
    )
    summary["topics"] = [{"topic_id": "fep-001"}, {}]
    run_manifest["topics"] = {"topic_id": "fep-001"}
    verification["results"] = [
        {"topic_id": "fep-001", "compiles": True, "lean_has_sorry": True}
    ]
    verification.update(
        {
            "verify_lean_ran": False,
            "topics_with_result": 0,
            "compiles_true": 0,
            "compiles_false": 1,
        }
    )
    paths.summary_json.write_text(json.dumps(summary), encoding="utf-8")
    (paths.root / "run_manifest.json").write_text(
        json.dumps(run_manifest), encoding="utf-8"
    )
    (paths.root / "verification_manifest.json").write_text(
        json.dumps(verification), encoding="utf-8"
    )

    receipt = validate_report_receipt(paths.root)

    assert receipt["valid"] is False
    expected_errors = (
        "run manifest topics must be a list of objects",
        "summary topics contains a row without a topic_id",
        "summary and run manifest topic rows disagree",
        "full-mode summary topic rows do not match selected-topic count",
        "run manifest topic rows do not match the mode contract",
        "verification manifest verify_lean_ran disagrees with its rows",
        "verification manifest topics_with_result disagrees with its rows",
        "verification manifest compiles_true disagrees with its rows",
        "verification manifest compiles_false disagrees with its rows",
        "verification compile flag disagrees for fep-001",
        "verification sorry flag disagrees for fep-001",
    )
    assert all(
        any(expected in error for error in receipt["errors"])
        for expected in expected_errors
    )


def test_validate_report_receipt_keeps_full_mode_claim_boundary_explicit(
    tmp_path: Path,
) -> None:
    rows = [
        {
            "topic_id": "fep-001",
            "success": True,
            "hermes_success": True,
            "lean_compiles": True,
            "lean_has_sorry": False,
            "verification_source": "hermes_refined",
        }
    ]
    result = _result_with_gauss(rows)
    result.complete = True
    result.catalogue_topics = 1
    result.verified_topics = 1
    rep = Reporter(tmp_path, run_id="run_incomplete_full_receipt")
    paths = rep.generate(TOPICS, result)

    summary = json.loads(paths.summary_json.read_text(encoding="utf-8"))
    run_manifest = json.loads(
        (paths.root / "run_manifest.json").read_text(encoding="utf-8")
    )
    summary["topics"] = []
    summary["selected_topics"] = 0
    summary["verified_topics"] = 0
    summary["status"] = "error"
    run_manifest["topics"] = []
    run_manifest["selected_topics"] = 0
    run_manifest["verified_topics"] = 0
    run_manifest["verification_source"] = "unexpected"
    run_manifest["lean_clean"] = False
    paths.summary_json.write_text(json.dumps(summary), encoding="utf-8")
    (paths.root / "run_manifest.json").write_text(
        json.dumps(run_manifest), encoding="utf-8"
    )

    receipt = validate_report_receipt(paths.root, require_complete=True)

    assert receipt["valid"] is False
    assert receipt["claim_ready"] is False
    assert any("must select at least one topic" in error for error in receipt["errors"])
    assert any("summary must have status ok" in error for error in receipt["errors"])
    assert any("wrong verification source" in error for error in receipt["errors"])
    assert any("must mark lean_clean true" in error for error in receipt["errors"])
    assert "complete full-mode receipt is required" in receipt["errors"]


def test_summary_json_includes_topics_payload(tmp_path: Path) -> None:
    """``Reporter._gen_summary_json`` must include the per-topic rows so
    ``fep_lean.output.manuscript.build_manuscript_vars`` can derive Hermes aggregates."""
    pl = FEPPipeline(PROJ)
    result = pl.run()
    rep = Reporter(tmp_path, run_id="test_topics")
    rep.reports_dir = tmp_path / "run_topics"
    paths = rep.generate(TOPICS, result)
    data = json.loads(paths.summary_json.read_text(encoding="utf-8"))
    assert "topics" in data
    assert isinstance(data["topics"], list)


def test_topic_md_renders_hermes_validation_panel(tmp_path: Path) -> None:
    """Per-topic markdown must include the Hermes Validation panel with cache
    hit + Hermes-refined compile status when ``hermes_success`` is True."""
    rows = [
        {
            "topic_id": TOPICS.topics[0].id,
            "success": True,
            "hermes_success": True,
            "lean_compiles": True,
            "hermes_lean_compiles": False,
            "cache_hit": True,
            "tokens_used": 1234,
            "hermes_model": "z-ai/glm-5.1",
            "explanation": "fixture explanation",
            "refined_lean_sketch": "theorem t : True := True.intro",
            "session_id": "sess-123",
        },
    ]
    rep = Reporter(tmp_path, run_id="test_panel")
    rep.reports_dir = tmp_path / "run_panel"
    paths = rep.generate(TOPICS, _result_with_gauss(rows))
    topic_md = paths.index_md.parent / "topics" / f"{rows[0]['topic_id']}.md"
    assert topic_md.is_file()
    text = topic_md.read_text(encoding="utf-8")
    assert "## Hermes Validation" in text
    assert "Cache hit" in text
    assert "Cache hit: `True`" in text
    assert "Hermes-refined Lean compiled" in text
    assert "Lean warnings: `0`" in text


def test_build_verification_manifest_helper_shape() -> None:
    """``Reporter.build_verification_manifest`` must produce the canonical shape
    required by ``_verify_block_from_manifest``."""

    class _fixture:
        def __init__(
            self,
            topic_id: str,
            compiles: bool,
            has_sorry: bool = False,
            warnings: list[str] | None = None,
        ) -> None:
            self.topic_id = topic_id
            self.compiles = compiles
            self.has_sorry = has_sorry
            self.warnings = warnings or []

    payload = Reporter.build_verification_manifest(
        [
            _fixture("fep-001", True),
            _fixture("fep-002", False, warnings=["fixture warning"]),
            _fixture("fep-003", True, True),
        ]
    )
    assert payload["verify_lean_ran"] is True
    assert payload["topics_with_result"] == 3
    assert payload["compiles_true"] == 2
    assert payload["compiles_false"] == 1
    assert payload["warning_count"] == 1
    assert payload["topics_with_warnings"] == 1
    assert {row["topic_id"] for row in payload["results"]} == {
        "fep-001",
        "fep-002",
        "fep-003",
    }
    sorry_rows = [row for row in payload["results"] if row["lean_has_sorry"]]
    assert len(sorry_rows) == 1
    assert sorry_rows[0]["topic_id"] == "fep-003"


def test_summary_json_carries_run_id(tmp_path: Path) -> None:
    """summary.json must carry the run_id so manuscripts can render it."""
    rep = Reporter(tmp_path, run_id="run_id_carrier")
    paths = rep.generate(TOPICS, _minimal_result(tmp_path))
    summary = json.loads(paths.summary_json.read_text(encoding="utf-8"))
    assert summary["run_id"] == "run_id_carrier"


def test_validate_receipt_detects_source_drift(tmp_path: Path) -> None:
    """Supplying project_root must flag a stored digest that no longer matches
    the live source tree."""
    paths = _complete_full_report(tmp_path, "run_drift_receipt")

    # Validation against the producing root is claim-ready before source drift.
    base = validate_report_receipt(
        paths.root,
        require_complete=True,
        project_root=tmp_path,
    )
    assert base["valid"] is True

    # Simulate a historical receipt after one already-rostered live source
    # owner evolves. The owner closure remains complete, so only its digest
    # binding changes.
    source_owner = tmp_path / "src" / "fep_lean" / "pipeline" / "core.py"
    source_owner.write_text(
        source_owner.read_text(encoding="utf-8") + "\n# historical drift\n",
        encoding="utf-8",
    )

    drifted = validate_report_receipt(
        paths.root, require_complete=True, project_root=tmp_path
    )
    assert drifted["valid"] is False
    assert drifted["source_bound"] is False
    assert any("source_digest" in error for error in drifted["errors"])


@pytest.mark.parametrize(
    ("binding", "expected_error"),
    [
        ("source_digest", "summary source_digest does not match"),
        ("config_digest", "summary config_digest does not match"),
        (
            "catalogue_sources_sha256",
            "summary catalogue_sources_sha256 does not match",
        ),
        ("roster_sha256", "summary roster_sha256 does not match"),
        ("toolchain", "summary toolchain does not match"),
        ("catalogue", "summary catalogue does not match"),
    ],
)
def test_source_bound_rejects_tampered_live_binding(
    tmp_path: Path,
    binding: str,
    expected_error: str,
) -> None:
    paths = _complete_full_report(tmp_path, f"run_tampered_{binding}")
    summary = json.loads(paths.summary_json.read_text(encoding="utf-8"))
    run_manifest = json.loads(paths.run_manifest_json.read_text(encoding="utf-8"))

    if binding == "toolchain":
        tampered = dict(summary["toolchain"])
        tampered["mathlib_revision"] = "0" * 40
        summary["toolchain"] = tampered
        run_manifest["toolchain"] = tampered
    elif binding == "catalogue":
        summary["catalogue"] = {}
    else:
        tampered = "0" * 64
        summary[binding] = tampered
        run_manifest[binding] = tampered

    paths.run_manifest_json.write_text(
        json.dumps(run_manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _refresh_report_hashes(paths, summary)

    receipt = validate_report_receipt(
        paths.root,
        require_complete=True,
        project_root=tmp_path,
    )

    assert receipt["valid"] is False
    assert receipt["source_bound"] is False
    assert any(expected_error in error for error in receipt["errors"])


def test_reporter_rejects_traversal_topic_before_writing(tmp_path: Path) -> None:
    """A crafted topic ID must fail before any report directory is written."""
    rows = [
        {
            "topic_id": "../../escape",
            "success": True,
            "hermes_success": True,
            "lean_compiles": True,
            "lean_has_sorry": False,
            "verification_source": "hermes_refined",
        }
    ]
    rep = Reporter(tmp_path, run_id="run_traversal")
    with pytest.raises(ValueError, match="canonical fep-NNN"):
        rep.generate(TOPICS, _result_with_gauss(rows))
    assert not (tmp_path / "output" / "reports" / "run_traversal").exists()
    assert not (tmp_path / "escape.md").exists()
