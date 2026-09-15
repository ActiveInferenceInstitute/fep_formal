"""Fail-closed evidence contracts for native Lean and full pipeline claims."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from fep_lean.catalogue.topics import FEPTopicCatalogue
from fep_lean.output.evidence import (
    build_native_lean_receipt,
    latest_claim_ready_full_report,
    validate_native_lean_receipt,
    write_native_lean_receipt,
)
from fep_lean.output.provenance import (
    OWNER_MANIFEST_VERSION,
    catalogue_sources_digest,
    config_owner_paths,
    report_config_digest,
    report_source_digest,
    source_owner_paths,
)
from fep_lean.verification.lean_verifier import VerifyResult

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


def _topic_ids(project_root: Path = PROJ) -> list[str]:
    catalogue = FEPTopicCatalogue.from_yaml(project_root / "config" / "topics.yaml")
    return [topic.id for topic in catalogue.topics]


def _copy_complete_owner_tree(destination: Path) -> None:
    """Copy the maintained receipt-owner closure without the large Lake cache."""
    owners = set(source_owner_paths(PROJ)) | set(config_owner_paths(PROJ))
    for source in sorted(owners):
        relative = source.relative_to(PROJ)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def test_latest_full_report_skips_historical_digests_before_full_validation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from fep_lean.output import reporter

    reports = tmp_path / "reports"
    stale = reports / "stale" / "summary.json"
    current = reports / "current" / "summary.json"
    stale.parent.mkdir(parents=True)
    current.parent.mkdir(parents=True)
    live = {
        "owner_manifest_version": OWNER_MANIFEST_VERSION,
        "source_digest": report_source_digest(PROJ),
        "config_digest": report_config_digest(PROJ),
        "catalogue_sources_sha256": catalogue_sources_digest(PROJ),
    }
    stale.write_text(
        json.dumps({**live, "source_digest": "0" * 64}),
        encoding="utf-8",
    )
    current.write_text(json.dumps(live), encoding="utf-8")
    stale.touch()
    current.touch()
    calls: list[Path] = []

    def validate(report_root: Path, *, project_root: Path) -> dict[str, bool]:
        assert project_root == PROJ
        calls.append(report_root)
        return {"claim_ready": report_root.name == "current"}

    monkeypatch.setattr(reporter, "validate_report_receipt", validate)

    assert latest_claim_ready_full_report(PROJ, output_root=tmp_path) == current.parent
    assert calls == [current.parent]


def test_latest_full_report_rejects_malformed_stale_and_unready_candidates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from fep_lean.output import reporter

    reports = tmp_path / "reports"
    malformed = reports / "malformed" / "summary.json"
    nonobject = reports / "nonobject" / "summary.json"
    stale = reports / "stale" / "summary.json"
    current = reports / "current" / "summary.json"
    for path in (malformed, nonobject, stale, current):
        path.parent.mkdir(parents=True, exist_ok=True)
    live = {
        "owner_manifest_version": OWNER_MANIFEST_VERSION,
        "source_digest": report_source_digest(PROJ),
        "config_digest": report_config_digest(PROJ),
        "catalogue_sources_sha256": catalogue_sources_digest(PROJ),
    }
    malformed.write_text("{not-json", encoding="utf-8")
    nonobject.write_text("[]", encoding="utf-8")
    stale.write_text(json.dumps({**live, "config_digest": "0" * 64}), encoding="utf-8")
    current.write_text(json.dumps(live), encoding="utf-8")
    calls: list[Path] = []

    def validate(report_root: Path, *, project_root: Path) -> dict[str, bool]:
        assert project_root == PROJ
        calls.append(report_root)
        return {"claim_ready": False}

    monkeypatch.setattr(reporter, "validate_report_receipt", validate)

    assert latest_claim_ready_full_report(PROJ, output_root=tmp_path) is None
    assert calls == [current.parent]


def test_clean_full_catalogue_native_receipt_is_claim_ready(tmp_path: Path) -> None:
    checkout = tmp_path / "checkout"
    _copy_complete_owner_tree(checkout)
    topic_ids = _topic_ids(checkout)
    results = [
        VerifyResult(
            topic_id=topic_id,
            compiles=True,
            has_sorry=False,
            lean_version=LEAN_VERSION,
        )
        for topic_id in topic_ids
    ]
    payload = build_native_lean_receipt(checkout, topic_ids, results)
    receipt = write_native_lean_receipt(tmp_path / "native.json", payload)

    validation = validate_native_lean_receipt(receipt, project_root=checkout)

    assert validation["valid"] is True
    assert validation["native_claim_ready"] is True
    assert validation["live_catalogue_topics"] == len(topic_ids)
    assert validation["selected_topics"] == len(topic_ids)
    assert validation["verified_topics"] == len(topic_ids)
    assert validation["warning_count"] == 0
    assert validation["sorry_count"] == 0
    assert validation["lean_version"] == LEAN_VERSION
    assert validation["source_bound"] is True
    assert len(validation["mathlib_revision"]) == 40


def test_self_consistent_minimal_root_cannot_claim_native_source_binding(
    tmp_path: Path,
) -> None:
    """A receipt cannot define its own incomplete source universe."""
    minimal_root = tmp_path / "minimal"
    for relative in (
        "config/topics.yaml",
        "src/fep_lean/catalogue/registry.py",
        "lean/lean-toolchain",
        "lean/lakefile.lean",
        "lean/lake-manifest.json",
    ):
        target = minimal_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(PROJ / relative, target)
    topic_ids = _topic_ids()
    results = [
        VerifyResult(
            topic_id=topic_id,
            compiles=True,
            has_sorry=False,
            lean_version=LEAN_VERSION,
        )
        for topic_id in topic_ids
    ]
    receipt = write_native_lean_receipt(
        tmp_path / "minimal-native.json",
        build_native_lean_receipt(minimal_root, topic_ids, results),
    )

    validation = validate_native_lean_receipt(receipt, project_root=minimal_root)

    assert validation["valid"] is False
    assert validation["source_bound"] is False
    assert validation["native_claim_ready"] is False
    assert any(
        "canonical report owner is missing" in error for error in validation["errors"]
    )


def test_deleted_python_owner_cannot_disappear_from_native_source_universe(
    tmp_path: Path,
) -> None:
    checkout = tmp_path / "checkout"
    _copy_complete_owner_tree(checkout)
    deleted_owner = checkout / "src" / "fep_lean" / "gauss" / "client.py"
    deleted_owner.unlink()
    topic_ids = _topic_ids()
    results = [
        VerifyResult(
            topic_id=topic_id,
            compiles=True,
            has_sorry=False,
            lean_version=LEAN_VERSION,
        )
        for topic_id in topic_ids
    ]
    receipt = write_native_lean_receipt(
        tmp_path / "deleted-owner-native.json",
        build_native_lean_receipt(checkout, topic_ids, results),
    )

    validation = validate_native_lean_receipt(receipt, project_root=checkout)

    assert validation["valid"] is False
    assert validation["source_bound"] is False
    assert validation["native_claim_ready"] is False
    assert any(
        "canonical report owner is missing: src/fep_lean/gauss/client.py" in error
        for error in validation["errors"]
    )


def test_native_source_binding_rejects_owner_bytes_changed_after_receipt(
    tmp_path: Path,
) -> None:
    checkout = tmp_path / "checkout"
    _copy_complete_owner_tree(checkout)
    topic_ids = _topic_ids()
    results = [
        VerifyResult(
            topic_id=topic_id,
            compiles=True,
            has_sorry=False,
            lean_version=LEAN_VERSION,
        )
        for topic_id in topic_ids
    ]
    receipt = write_native_lean_receipt(
        tmp_path / "stale-owner-native.json",
        build_native_lean_receipt(checkout, topic_ids, results),
    )
    owner = checkout / "src" / "fep_lean" / "gauss" / "client.py"
    owner.write_text(
        owner.read_text(encoding="utf-8") + "\n# post-receipt change\n",
        encoding="utf-8",
    )

    validation = validate_native_lean_receipt(receipt, project_root=checkout)

    assert validation["valid"] is False
    assert validation["source_bound"] is False
    assert validation["native_claim_ready"] is False
    assert "source_digest does not match the live source tree" in validation["errors"]


def test_native_receipt_without_live_root_is_structural_only(tmp_path: Path) -> None:
    topic_ids = _topic_ids()
    results = [
        VerifyResult(
            topic_id=topic_id,
            compiles=True,
            has_sorry=False,
            lean_version=LEAN_VERSION,
        )
        for topic_id in topic_ids
    ]
    receipt = write_native_lean_receipt(
        tmp_path / "native-unbound.json",
        build_native_lean_receipt(PROJ, topic_ids, results),
    )

    validation = validate_native_lean_receipt(receipt)

    assert validation["valid"] is True
    assert validation["source_bound"] is False
    assert validation["native_claim_ready"] is False


def test_native_receipt_builder_rejects_truthy_non_boolean_result_flags() -> None:
    topic_id = _topic_ids()[0]
    result = {
        "topic_id": topic_id,
        "compiles": "false",
        "has_sorry": False,
        "warnings": [],
        "errors": [],
        "duration_s": 0.0,
        "lean_version": LEAN_VERSION,
    }

    with pytest.raises(TypeError, match="compiles and has_sorry must be booleans"):
        build_native_lean_receipt(PROJ, [topic_id], [result])


@pytest.mark.parametrize(
    ("requested", "expected_error"),
    [
        (["fep-001", "fep-001"], "must be unique"),
        (["fep-002", "fep-001"], "preserve live catalogue order"),
        (["fep-999"], "must be known"),
    ],
)
def test_native_receipt_builder_rejects_invalid_requested_rosters(
    requested: list[str], expected_error: str
) -> None:
    with pytest.raises(ValueError, match=expected_error):
        build_native_lean_receipt(PROJ, requested, [])


def test_native_receipt_writer_removes_staging_file_after_replace_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from fep_lean.output import evidence

    destination = tmp_path / "native.json"
    staged_paths: list[Path] = []

    def fail_replace(source: str, target: Path) -> None:
        assert target == destination
        staged_paths.append(Path(source))
        assert staged_paths[-1].is_file()
        raise OSError("replace failed")

    monkeypatch.setattr(evidence.os, "replace", fail_replace)

    with pytest.raises(OSError, match="replace failed"):
        write_native_lean_receipt(destination, {"complete": False})

    assert len(staged_paths) == 1
    assert not staged_paths[0].exists()
    assert not destination.exists()


@pytest.mark.parametrize(
    "content",
    [None, "{not-json", "[]"],
)
def test_native_receipt_validator_rejects_unreadable_or_nonobject_payloads(
    tmp_path: Path, content: str | None
) -> None:
    receipt = tmp_path / "native.json"
    if content is not None:
        receipt.write_text(content, encoding="utf-8")

    validation = validate_native_lean_receipt(receipt)

    assert validation["valid"] is False
    assert validation["native_claim_ready"] is False
    assert validation["source_bound"] is False
    if content == "[]":
        assert "native receipt must contain a JSON object" in validation["errors"]
    else:
        assert any(
            "cannot read native receipt" in error for error in validation["errors"]
        )


def test_native_receipt_validator_rejects_malformed_rows_and_summary_fields(
    tmp_path: Path,
) -> None:
    topic_id = _topic_ids()[0]
    payload = build_native_lean_receipt(
        PROJ,
        [topic_id],
        [
            VerifyResult(
                topic_id=topic_id,
                compiles=True,
                has_sorry=False,
                lean_version=LEAN_VERSION,
            )
        ],
    )
    payload.update(
        {
            "schema_version": 0,
            "kind": "full-provider",
            "mode": "full",
            "requested_topic_ids": [topic_id, 1],
            "results": ["not-a-row"],
            "selected_topics": 9,
            "verified_topics": 9,
            "warning_count": 9,
            "sorry_count": 9,
            "complete": "yes",
            "duration_s": -1,
            "lean_version": "forged",
            "lean_toolchain": "nightly",
            "mathlib_tag": "latest",
            "mathlib_revision": "not-a-revision",
            "owner_manifest_version": -1,
            "source_digest": "bad",
            "config_digest": "bad",
            "catalogue_sha256": "bad",
            "catalogue_sources_sha256": "bad",
            "roster_sha256": "bad",
            "live_catalogue_topics": True,
        }
    )
    receipt = write_native_lean_receipt(tmp_path / "malformed.json", payload)

    validation = validate_native_lean_receipt(receipt)

    assert validation["valid"] is False
    assert validation["native_claim_ready"] is False
    errors = "\n".join(validation["errors"])
    for expected in (
        "schema_version",
        "kind/mode contract",
        "requested_topic_ids must be a list of strings",
        "results must be a list of objects",
        "lean_toolchain",
        "mathlib_tag",
        "mathlib_revision",
        "owner_manifest_version",
        "source_digest",
        "live_catalogue_topics must be a positive integer",
    ):
        assert expected in errors


def test_native_receipt_validator_rejects_invalid_row_types_and_totals(
    tmp_path: Path,
) -> None:
    topic_id = _topic_ids()[0]
    payload = build_native_lean_receipt(
        PROJ,
        [topic_id],
        [
            VerifyResult(
                topic_id=topic_id,
                compiles=True,
                has_sorry=False,
                lean_version=LEAN_VERSION,
            )
        ],
    )
    row = payload["results"][0]
    row.update(
        {
            "warnings": [""],
            "errors": "compiler failure",
            "duration_s": float("nan"),
            "compiles": 1,
            "has_sorry": "no",
        }
    )
    payload["duration_s"] = 0.125
    receipt = write_native_lean_receipt(tmp_path / "invalid-row.json", payload)

    validation = validate_native_lean_receipt(receipt)

    assert validation["valid"] is False
    errors = "\n".join(validation["errors"])
    assert "warnings must be a list of non-empty strings" in errors
    assert "errors must be a list of non-empty strings" in errors
    assert "duration_s must be a finite non-negative number" in errors
    assert "compiles and has_sorry must be booleans" in errors
    assert "duration_s disagrees with receipt rows" in errors


def test_clean_partial_receipt_cannot_claim_the_live_roster(tmp_path: Path) -> None:
    checkout = tmp_path / "checkout"
    _copy_complete_owner_tree(checkout)
    live_topic_ids = _topic_ids(checkout)
    selected_topic_ids = live_topic_ids[:-1]
    results = [
        VerifyResult(
            topic_id=topic_id,
            compiles=True,
            has_sorry=False,
            lean_version=LEAN_VERSION,
        )
        for topic_id in selected_topic_ids
    ]
    receipt = write_native_lean_receipt(
        tmp_path / "native-partial.json",
        build_native_lean_receipt(checkout, selected_topic_ids, results),
    )

    validation = validate_native_lean_receipt(receipt, project_root=checkout)

    assert validation["valid"] is True
    assert validation["source_bound"] is True
    assert validation["native_claim_ready"] is False
    assert validation["live_catalogue_topics"] == len(live_topic_ids)
    assert validation["selected_topics"] == len(selected_topic_ids)
    assert validation["verified_topics"] == len(selected_topic_ids)


def test_native_receipt_with_warning_is_valid_but_not_claim_ready(
    tmp_path: Path,
) -> None:
    checkout = tmp_path / "checkout"
    _copy_complete_owner_tree(checkout)
    topic_ids = _topic_ids(checkout)
    results = [
        VerifyResult(
            topic_id=topic_id,
            compiles=True,
            has_sorry=False,
            lean_version=LEAN_VERSION,
        )
        for topic_id in topic_ids
    ]
    results[13].warnings.append("fixture warning")
    receipt = write_native_lean_receipt(
        tmp_path / "native-warning.json",
        build_native_lean_receipt(checkout, topic_ids, results),
    )

    validation = validate_native_lean_receipt(receipt, project_root=checkout)

    assert validation["valid"] is True
    assert validation["native_claim_ready"] is False
    assert validation["warning_count"] == 1
    assert validation["verified_topics"] == len(topic_ids) - 1


@pytest.mark.parametrize(
    "recorded_version",
    ["", "unknown", "Lean (version 4.28.0, fixture, Release)"],
)
def test_native_receipt_rejects_missing_or_mismatched_actual_lean_version(
    tmp_path: Path,
    recorded_version: str,
) -> None:
    topic_ids = _topic_ids()
    results = [
        VerifyResult(
            topic_id=topic_id,
            compiles=True,
            has_sorry=False,
            lean_version=recorded_version,
        )
        for topic_id in topic_ids
    ]
    receipt = write_native_lean_receipt(
        tmp_path / "native-version.json",
        build_native_lean_receipt(PROJ, topic_ids, results),
    )

    validation = validate_native_lean_receipt(receipt, project_root=PROJ)

    assert validation["valid"] is False
    assert validation["native_claim_ready"] is False
    assert any("lean_version" in error for error in validation["errors"])


def test_native_receipt_rejects_nonuniform_actual_lean_versions(
    tmp_path: Path,
) -> None:
    topic_ids = _topic_ids()
    results = [
        VerifyResult(
            topic_id=topic_id,
            compiles=True,
            has_sorry=False,
            lean_version=LEAN_VERSION,
        )
        for topic_id in topic_ids
    ]
    results[-1].lean_version = "Lean (version 4.29.0, different binary, Release)"
    receipt = write_native_lean_receipt(
        tmp_path / "native-mixed-version.json",
        build_native_lean_receipt(PROJ, topic_ids, results),
    )

    validation = validate_native_lean_receipt(receipt, project_root=PROJ)

    assert validation["valid"] is False
    assert validation["native_claim_ready"] is False
    assert "result lean_version values must be uniform" in validation["errors"]


def test_native_receipt_compile_errors_prevent_claim_readiness(tmp_path: Path) -> None:
    checkout = tmp_path / "checkout"
    _copy_complete_owner_tree(checkout)
    topic_ids = _topic_ids(checkout)
    results = [
        VerifyResult(
            topic_id=topic_id,
            compiles=True,
            has_sorry=False,
            lean_version=LEAN_VERSION,
        )
        for topic_id in topic_ids
    ]
    results[0].errors.append("compiler error despite success flag")
    receipt = write_native_lean_receipt(
        tmp_path / "native-row-errors.json",
        build_native_lean_receipt(checkout, topic_ids, results),
    )

    validation = validate_native_lean_receipt(receipt, project_root=checkout)

    assert validation["valid"] is True
    assert validation["native_claim_ready"] is False
    assert validation["verified_topics"] == len(topic_ids) - 1


@pytest.mark.parametrize(
    ("field", "value", "expected_error"),
    [
        ("duration_s", "not-a-number", "duration_s must be a finite"),
        ("duration_s", float("inf"), "duration_s must be a finite"),
    ],
)
def test_native_receipt_rejects_invalid_total_duration_without_raising(
    tmp_path: Path,
    field: str,
    value: object,
    expected_error: str,
) -> None:
    topic_ids = _topic_ids()
    results = [
        VerifyResult(
            topic_id=topic_id,
            compiles=True,
            has_sorry=False,
            lean_version=LEAN_VERSION,
        )
        for topic_id in topic_ids
    ]
    payload = build_native_lean_receipt(PROJ, topic_ids, results)
    payload[field] = value
    receipt = write_native_lean_receipt(tmp_path / "native-duration.json", payload)

    validation = validate_native_lean_receipt(receipt, project_root=PROJ)

    assert validation["valid"] is False
    assert validation["native_claim_ready"] is False
    assert any(expected_error in error for error in validation["errors"])
