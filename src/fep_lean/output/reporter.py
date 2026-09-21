"""Transactional Markdown and JSON run reports."""

from __future__ import annotations

import datetime
import hashlib
import json
import logging
import math
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from fep_lean.catalogue.schema import topic_ids_sha256
from fep_lean.catalogue.topics import FEPTopicCatalogue
from fep_lean.llm.hermes import (
    lean_semantic_contract_sha256,
    preserves_lean_semantic_contract,
)
from fep_lean.output.fsutil import atomic_write_text, sha256_bytes
from fep_lean.output.provenance import (
    OWNER_MANIFEST_VERSION,
    catalogue_sources_digest,
    report_config_digest,
    report_owner_errors,
    report_source_digest,
)
from fep_lean.verification._toolchain import (
    actual_lean_semver,
    lean_version_matches_pin,
    pinned_lean_semver,
    resolved_mathlib_revision,
)
from fep_lean.verification.environment import (
    CATALOGUE_VALIDATION_CHECK_NAMES,
    FULL_VALIDATION_CHECK_NAMES,
)

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_TOPIC_ID_RE = re.compile(r"^fep-\d{3}$")
REPORT_RECEIPT_SCHEMA_VERSION = 4
_REQUIRED_REPORT_ARTIFACTS = frozenset(
    {
        "index.md",
        "hermes.md",
        "lean.md",
        "validation.md",
        "verification_manifest.json",
        "run_manifest.json",
    }
)

log = logging.getLogger(__name__)


def _default_run_id() -> str:
    """Timestamped run identifier; names report directories, never digests."""
    stamp = datetime.datetime.now(tz=datetime.timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    return f"run_{stamp}"


def _toolchain_snapshot(
    project_root: Path,
    *,
    lean_version: str = "",
) -> dict[str, str]:
    """Return the configured and resolved compiler dependency identity."""
    root = Path(project_root)
    lean_dir = root / "lean"
    toolchain_path = lean_dir / "lean-toolchain"
    toolchain = (
        toolchain_path.read_text(encoding="utf-8").strip()
        if toolchain_path.is_file()
        else ""
    )
    mathlib_tag = ""
    lakefile = lean_dir / "lakefile.lean"
    if lakefile.is_file():
        match = re.search(r'@\s*"([^"]+)"', lakefile.read_text(encoding="utf-8"))
        if match:
            mathlib_tag = match.group(1)
    return {
        "lean_toolchain": toolchain,
        "lean_version": lean_version,
        "mathlib_tag": mathlib_tag,
        "mathlib_revision": resolved_mathlib_revision(lean_dir),
    }


def _canonical_evidence_row(row: dict[str, Any]) -> dict[str, Any]:
    """Normalize aliases before comparing redundant evidence surfaces."""
    normalized = dict(row)
    if "lean_compiles" not in normalized and "compiles" in normalized:
        normalized["lean_compiles"] = normalized["compiles"]
    if "lean_has_sorry" not in normalized and "has_sorry" in normalized:
        normalized["lean_has_sorry"] = normalized["has_sorry"]
    if "lean_warnings" not in normalized and "warnings" in normalized:
        normalized["lean_warnings"] = normalized["warnings"]
    for alias in ("compiles", "has_sorry", "warnings"):
        normalized.pop(alias, None)
    return normalized


def _validation_evidence(result: Any) -> dict[str, Any]:
    """Project the environment stage into a JSON-stable evidence record."""
    payload: Any = next(
        (
            stage.payload
            for stage in getattr(result, "stages", [])
            if stage.name == "Environment Validation"
        ),
        {},
    )
    validation = payload if isinstance(payload, dict) else {}
    raw_checks = validation.get("checks", [])
    checks = raw_checks if isinstance(raw_checks, list) else []
    return {
        "status": validation.get("status", "not-run"),
        "failed_count": validation.get("failed_count", 0),
        "checks": [dict(check) for check in checks if isinstance(check, dict)],
    }


def _render_validation_markdown(validation: dict[str, Any]) -> str:
    """Render the human-readable projection of structured validation evidence."""
    lines = [
        "# Environment validation",
        "",
        f"Status: `{validation.get('status', 'not-run')}`",
        "",
    ]
    checks = validation.get("checks", [])
    for check in checks if isinstance(checks, list) else []:
        if isinstance(check, dict):
            lines.append(
                f"- `{check.get('name', '')}`: `{check.get('ok', False)}` — "
                f"{check.get('message', '')}"
            )
    return "\n".join(lines) + "\n"


def _selected_topic_ids(
    catalogue: FEPTopicCatalogue,
    result: Any,
    rows: list[dict[str, Any]],
) -> list[str]:
    """Resolve the exact ordered selection from the pipeline's catalogue stage."""
    catalogue_ids = [topic.id for topic in catalogue.topics]
    stage_ids: list[str] | None = None
    for stage in getattr(result, "stages", []):
        if stage.name != "Load Catalogue" or not isinstance(stage.payload, dict):
            continue
        raw = stage.payload.get("topics")
        if isinstance(raw, list) and all(isinstance(item, str) for item in raw):
            stage_ids = list(raw)
        break
    row_ids = [str(row.get("topic_id", "")) for row in rows]
    if stage_ids is not None:
        selected = stage_ids
    elif row_ids:
        selected = row_ids
    elif int(getattr(result, "catalogue_topics", 0) or 0) == len(catalogue_ids):
        selected = catalogue_ids
    else:
        selected = catalogue_ids[: int(getattr(result, "catalogue_topics", 0) or 0)]
    if len(selected) != len(set(selected)):
        raise ValueError("selected report topic IDs must be unique")
    unknown = sorted(set(selected) - set(catalogue_ids))
    if unknown:
        raise ValueError(
            "selected report topic IDs are absent from the catalogue: "
            + ", ".join(unknown)
        )
    canonical_order = [topic_id for topic_id in catalogue_ids if topic_id in selected]
    if selected != canonical_order:
        raise ValueError("selected report topic IDs must preserve catalogue order")
    if rows and row_ids != selected:
        raise ValueError("report topic rows must equal the selected catalogue topics")
    return selected


def _bind_canonical_topic_evidence(
    catalogue: FEPTopicCatalogue,
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Bind provider rows to canonical source and its complete token contract."""
    by_id = {topic.id: topic for topic in catalogue.topics}
    bound: list[dict[str, Any]] = []
    for raw in rows:
        row = dict(raw)
        topic_id = row.get("topic_id")
        if not isinstance(topic_id, str) or topic_id not in by_id:
            raise ValueError(f"report topic is absent from the catalogue: {topic_id!r}")
        canonical = by_id[topic_id].lean_sketch
        final = row.get("final_lean_sketch")
        final_source = final if isinstance(final, str) else ""
        computed_preserved = preserves_lean_semantic_contract(final_source, canonical)
        recorded_preserved = row.get("semantic_contract_preserved")
        row["canonical_source_sha256"] = hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()
        row["semantic_contract_sha256"] = lean_semantic_contract_sha256(canonical)
        row["semantic_contract_preserved"] = computed_preserved and (
            recorded_preserved is not False
        )
        bound.append(row)
    return bound


def _derived_lean_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Derive the complete Lean summary from canonical per-topic rows."""
    warning_logs = [
        f"{row.get('topic_id')}: {warning}"
        for row in rows
        for warning in (
            row.get("lean_warnings", [])
            if isinstance(row.get("lean_warnings", []), list)
            else []
        )
        if isinstance(warning, str)
    ]
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
        "warning_count": len(warning_logs),
        "warning_logs": warning_logs,
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


def _derived_report_stats(
    rows: list[dict[str, Any]],
    stages: list[dict[str, Any]],
    selected_topics: int,
) -> dict[str, Any]:
    """Derive aggregate report metrics without trusting caller-supplied stats."""
    lean_stats = _derived_lean_stats(rows)
    clean = [
        bool(row.get("lean_compiles"))
        and not bool(row.get("lean_has_sorry"))
        and not bool(row.get("lean_warnings"))
        for row in rows
    ]
    gauss_stage = next(
        (stage for stage in stages if stage.get("name") == "Gauss Sessions"), None
    )
    return {
        "topics_total": selected_topics,
        "topics_verified": sum(
            bool(row.get("success")) and is_clean
            for row, is_clean in zip(rows, clean, strict=True)
        ),
        "hermes_success": sum(bool(row.get("hermes_success")) for row in rows),
        "lean_verified": sum(bool(row.get("lean_compiles")) for row in rows),
        "lean_compile_ok": sum(clean),
        "stages_ok": sum(stage.get("status") == "ok" for stage in stages),
        "gauss_ran": bool(gauss_stage and gauss_stage.get("status") == "ok"),
        **lean_stats,
    }


def _report_projection_result(summary: dict[str, Any]) -> SimpleNamespace:
    """Create the minimal immutable-style view consumed by Markdown renderers."""
    return SimpleNamespace(
        status=summary.get("status", "unknown"),
        mode=summary.get("mode", "full"),
        catalogue_topics=summary.get("selected_topics", 0),
        verified_topics=summary.get("verified_topics", 0),
        stages=[
            SimpleNamespace(**stage)
            for stage in summary.get("stages", [])
            if isinstance(stage, dict)
        ],
        stats=summary.get("stats", {}),
    )


@dataclass
class _ReceiptFacts:
    """Mutable facts extracted from the summary and shared between validators."""

    mode: str = ""
    complete: bool = False
    selected_topics: int = 0
    live_catalogue_topics: int = 0
    selected_topic_ids: list[str] = field(default_factory=list)
    verified_topics: int = 0
    warning_count: int = 0
    summary_rows: list[dict[str, Any]] = field(default_factory=list)
    run_rows: list[dict[str, Any]] = field(default_factory=list)
    verification_rows: list[dict[str, Any]] = field(default_factory=list)
    summary_ids: list[str] = field(default_factory=list)
    run_ids: list[str] = field(default_factory=list)
    verification_ids: list[str] = field(default_factory=list)
    summary_flags: list[tuple[bool, bool, bool, list[str]]] = field(
        default_factory=list
    )
    run_flags: list[tuple[bool, bool, bool, list[str]]] = field(default_factory=list)
    verification_flags: list[tuple[bool, bool, list[str]]] = field(default_factory=list)
    seen_artifacts: set[str] = field(default_factory=set)
    checked_artifacts: int = 0
    expected_warning_count: int = 0
    source_bound: bool = False


def _validate_digests(summary: dict[str, Any]) -> tuple[str, ...]:
    """Require the four provenance digests to be lowercase SHA-256 strings."""
    errors: list[str] = []
    for digest_name in (
        "source_digest",
        "config_digest",
        "roster_sha256",
        "catalogue_sources_sha256",
    ):
        digest = summary.get(digest_name)
        if not isinstance(digest, str) or not _SHA256_RE.fullmatch(digest):
            errors.append(f"summary {digest_name} must be a lowercase SHA-256 digest")
    return tuple(errors)


def _validate_summary_header(
    summary: dict[str, Any],
    root: Path,
    facts: _ReceiptFacts,
) -> tuple[str, ...]:
    """Validate summary structure and record the parsed receipt facts."""
    errors: list[str] = []
    facts.mode = str(summary.get("mode", ""))
    facts.complete = bool(summary.get("complete", False))
    if "catalogue_topics" in summary:
        errors.append("summary uses removed catalogue_topics receipt field")
    if summary.get("receipt_schema_version") != REPORT_RECEIPT_SCHEMA_VERSION:
        errors.append(
            f"summary receipt_schema_version must be {REPORT_RECEIPT_SCHEMA_VERSION}"
        )
    if summary.get("run_id") != root.name:
        errors.append("summary run_id does not match the report directory")
    if facts.mode not in {"full", "catalogue"}:
        errors.append(f"summary mode is unsupported: {facts.mode!r}")
    if not isinstance(summary.get("complete"), bool):
        errors.append("summary complete must be a boolean")
    raw_selected = summary.get("selected_topics")
    if (
        not isinstance(raw_selected, int)
        or isinstance(raw_selected, bool)
        or raw_selected < 0
    ):
        errors.append("summary selected_topics must be a non-negative integer")
    else:
        facts.selected_topics = raw_selected
    raw_selected_ids = summary.get("selected_topic_ids")
    if not isinstance(raw_selected_ids, list) or not all(
        isinstance(topic_id, str) and _TOPIC_ID_RE.fullmatch(topic_id)
        for topic_id in (raw_selected_ids if isinstance(raw_selected_ids, list) else ())
    ):
        errors.append("summary selected_topic_ids must be canonical fep-NNN strings")
    else:
        facts.selected_topic_ids = list(raw_selected_ids)
        if len(facts.selected_topic_ids) != len(set(facts.selected_topic_ids)):
            errors.append("summary selected_topic_ids must be unique")
        if len(facts.selected_topic_ids) != facts.selected_topics:
            errors.append("summary selected_topic_ids disagree with selected_topics")
    raw_live = summary.get("live_catalogue_topics")
    if type(raw_live) is not int or raw_live <= 0:
        errors.append("summary live_catalogue_topics must be a positive integer")
    else:
        facts.live_catalogue_topics = raw_live
        if facts.live_catalogue_topics < facts.selected_topics:
            errors.append(
                "summary live_catalogue_topics cannot be smaller than selected_topics"
            )
    selection = summary.get("selection")
    if not isinstance(selection, dict):
        errors.append("summary selection must be an object")
    else:
        if selection.get("topic_ids") != facts.selected_topic_ids:
            errors.append("summary selection topic IDs disagree")
        total_catalogue = selection.get("total_catalogue_topics")
        if (
            type(total_catalogue) is not int
            or total_catalogue != facts.live_catalogue_topics
        ):
            errors.append("summary selection total_catalogue_topics is inconsistent")
    raw_verified = summary.get("verified_topics")
    if (
        not isinstance(raw_verified, int)
        or isinstance(raw_verified, bool)
        or raw_verified < 0
    ):
        errors.append("summary verified_topics must be a non-negative integer")
    else:
        facts.verified_topics = raw_verified
    raw_warning_count = summary.get("warning_count")
    if type(raw_warning_count) is not int or raw_warning_count < 0:
        errors.append("summary warning_count must be a non-negative integer")
    else:
        facts.warning_count = raw_warning_count
    raw_rows = summary.get("topics", [])
    if not isinstance(raw_rows, list) or not all(
        isinstance(row, dict) for row in raw_rows
    ):
        errors.append("summary topics must be a list of objects")
    else:
        facts.summary_rows = [row for row in raw_rows if isinstance(row, dict)]
    errors.extend(_validate_digests(summary))
    if not isinstance(summary.get("toolchain"), dict):
        errors.append("summary toolchain must be an object")
    capabilities = summary.get("capabilities")
    if not isinstance(capabilities, dict) or not all(
        isinstance(name, str) and name and isinstance(available, bool)
        for name, available in (
            capabilities.items() if isinstance(capabilities, dict) else ()
        )
    ):
        errors.append("summary capabilities must map names to booleans")
    if not isinstance(summary.get("failure_reason"), str):
        errors.append("summary failure_reason must be a string")
    if not isinstance(summary.get("stages"), list) or not all(
        isinstance(stage, dict) for stage in summary.get("stages", [])
    ):
        errors.append("summary stages must be a list of objects")
    if not isinstance(summary.get("lean_stats"), dict):
        errors.append("summary lean_stats must be an object")
    if not isinstance(summary.get("validation"), dict):
        errors.append("summary validation must be an object")
    else:
        failed_count = summary["validation"].get("failed_count")
        if type(failed_count) is not int or failed_count < 0:
            errors.append(
                "summary validation failed_count must be a non-negative integer"
            )
    if not isinstance(summary.get("catalogue"), dict):
        errors.append("summary catalogue must be an object")
    if not isinstance(summary.get("stats"), dict):
        errors.append("summary stats must be an object")
    if summary.get("owner_manifest_version") != OWNER_MANIFEST_VERSION:
        errors.append("summary owner manifest version does not match this validator")
    return tuple(errors)


def _validate_artifact_hashes(
    summary: dict[str, Any],
    root: Path,
    facts: _ReceiptFacts,
) -> tuple[str, ...]:
    """Recompute every listed artifact hash and reconcile the directory."""
    errors: list[str] = []
    raw_hashes = summary.get("artifact_hashes")
    if not isinstance(raw_hashes, dict):
        errors.append("summary artifact_hashes must be an object")
        raw_hashes = {}
    for raw_relative, expected in raw_hashes.items():
        if not isinstance(raw_relative, str) or not raw_relative:
            errors.append("artifact hash paths must be non-empty strings")
            continue
        relative = Path(raw_relative)
        if relative.is_absolute() or ".." in relative.parts:
            errors.append(f"artifact path escapes report directory: {raw_relative!r}")
            continue
        artifact = (root / relative).resolve()
        if artifact == root or root not in artifact.parents:
            errors.append(f"artifact path escapes report directory: {raw_relative!r}")
            continue
        if not artifact.is_file():
            errors.append(f"hashed artifact is missing: {raw_relative}")
            continue
        if not isinstance(expected, str) or not _SHA256_RE.fullmatch(expected):
            errors.append(f"invalid SHA-256 digest for artifact: {raw_relative}")
            continue
        actual = hashlib.sha256(artifact.read_bytes()).hexdigest()
        facts.checked_artifacts += 1
        facts.seen_artifacts.add(relative.as_posix())
        if actual != expected:
            errors.append(f"artifact hash mismatch: {raw_relative}")
    missing_required = sorted(_REQUIRED_REPORT_ARTIFACTS - facts.seen_artifacts)
    if missing_required:
        errors.append(
            "required artifacts are not hashed: " + ", ".join(missing_required)
        )

    actual_artifacts = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path.relative_to(root).as_posix() != "summary.json"
    }
    unlisted_artifacts = sorted(actual_artifacts - facts.seen_artifacts)
    if unlisted_artifacts:
        errors.append(
            "report artifacts are not hashed: " + ", ".join(unlisted_artifacts)
        )
    return tuple(errors)


def _validate_rendered_evidence(
    summary: dict[str, Any],
    root: Path,
    facts: _ReceiptFacts,
) -> tuple[str, ...]:
    """Check rendered markdown artifacts against their structured evidence."""
    errors: list[str] = []
    validation_path = root / "validation.md"
    if isinstance(summary.get("validation"), dict) and validation_path.is_file():
        try:
            rendered_validation = validation_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(f"cannot read validation.md: {exc}")
        else:
            if rendered_validation != _render_validation_markdown(
                summary["validation"]
            ):
                errors.append(
                    "validation.md does not match structured validation evidence"
                )
    projection_renderer = Reporter(root, run_id=root.name)
    expected_markdown = {
        "hermes.md": projection_renderer._hermes_md(facts.summary_rows),
        "lean.md": projection_renderer._lean_md(
            summary.get("lean_stats", {})
            if isinstance(summary.get("lean_stats"), dict)
            else {}
        ),
    }
    expected_markdown.update(
        {
            f"topics/{row.get('topic_id', '')}.md": projection_renderer._topic_md(row)
            for row in facts.summary_rows
            if isinstance(row.get("topic_id"), str)
        }
    )
    for markdown_relative, expected_text in expected_markdown.items():
        path = root / markdown_relative
        if not path.is_file():
            continue
        try:
            actual_text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(f"cannot read {markdown_relative}: {exc}")
        else:
            if actual_text != expected_text:
                errors.append(
                    f"{markdown_relative} does not match its structured evidence"
                )
    return tuple(errors)


def _validate_topic_rows(
    run_manifest: dict[str, Any] | None,
    verification_manifest: dict[str, Any] | None,
    facts: _ReceiptFacts,
) -> tuple[str, ...]:
    """Extract topic rows from both manifests and derive their flag tuples."""
    errors: list[str] = []

    def rows_from(
        payload: dict[str, Any] | None, field: str, label: str
    ) -> list[dict[str, Any]]:
        if payload is None:
            return []
        raw = payload.get(field, [])
        if not isinstance(raw, list) or not all(isinstance(row, dict) for row in raw):
            errors.append(f"{label} {field} must be a list of objects")
            return []
        return [row for row in raw if isinstance(row, dict)]

    facts.run_rows = rows_from(run_manifest, "topics", "run manifest")
    facts.verification_rows = rows_from(
        verification_manifest, "results", "verification manifest"
    )

    def row_ids(rows: list[dict[str, Any]], label: str) -> list[str]:
        ids: list[str] = []
        for row in rows:
            topic_id = row.get("topic_id")
            if not isinstance(topic_id, str) or not topic_id:
                errors.append(f"{label} contains a row without a topic_id")
                continue
            ids.append(topic_id)
        if len(set(ids)) != len(ids):
            errors.append(f"{label} contains duplicate topic_id values")
        return ids

    facts.summary_ids = row_ids(facts.summary_rows, "summary topics")
    facts.run_ids = row_ids(facts.run_rows, "run manifest topics")
    facts.verification_ids = row_ids(
        facts.verification_rows, "verification manifest results"
    )
    for topic_id in facts.summary_ids:
        if not _TOPIC_ID_RE.fullmatch(topic_id):
            errors.append(f"summary topic_id is malformed: {topic_id!r}")
    expected_topic_artifacts = {
        f"topics/{topic_id}.md"
        for topic_id in facts.summary_ids
        if facts.mode == "full"
    }
    missing_topic_artifacts = sorted(expected_topic_artifacts - facts.seen_artifacts)
    if missing_topic_artifacts:
        errors.append(
            "per-topic artifacts are not hashed: " + ", ".join(missing_topic_artifacts)
        )
    hashed_topic_artifacts = {
        relative
        for relative in facts.seen_artifacts
        if relative.startswith("topics/") and relative.endswith(".md")
    }
    unexpected_topic_artifacts = sorted(
        hashed_topic_artifacts - expected_topic_artifacts
    )
    if unexpected_topic_artifacts:
        errors.append(
            "unexpected per-topic artifacts are hashed: "
            + ", ".join(unexpected_topic_artifacts)
        )
    if facts.run_ids != facts.summary_ids:
        errors.append("summary and run manifest topic rows disagree")

    def row_bool(row: dict[str, Any], names: tuple[str, ...], label: str) -> bool:
        key = next((name for name in names if name in row), names[0])
        value = row.get(key)
        if not isinstance(value, bool):
            errors.append(f"{label} {key} must be a boolean")
            return False
        return value

    def row_warnings(
        row: dict[str, Any], names: tuple[str, ...], label: str
    ) -> list[str]:
        key = next((name for name in names if name in row), names[0])
        value = row.get(key)
        if not isinstance(value, list) or not all(
            isinstance(warning, str) and warning for warning in value
        ):
            errors.append(f"{label} {key} must be a list of non-empty strings")
            return []
        return value

    facts.summary_flags = [
        (
            row_bool(row, ("success",), f"summary topic {row.get('topic_id', '')}"),
            row_bool(
                row,
                ("lean_compiles", "compiles"),
                f"summary topic {row.get('topic_id', '')}",
            ),
            row_bool(
                row,
                ("lean_has_sorry", "has_sorry"),
                f"summary topic {row.get('topic_id', '')}",
            ),
            row_warnings(
                row,
                ("lean_warnings", "warnings"),
                f"summary topic {row.get('topic_id', '')}",
            ),
        )
        for row in facts.summary_rows
    ]
    facts.run_flags = [
        (
            row_bool(
                row,
                ("success",),
                f"run manifest topic {row.get('topic_id', '')}",
            ),
            row_bool(
                row,
                ("lean_compiles", "compiles"),
                f"run manifest topic {row.get('topic_id', '')}",
            ),
            row_bool(
                row,
                ("lean_has_sorry", "has_sorry"),
                f"run manifest topic {row.get('topic_id', '')}",
            ),
            row_warnings(
                row,
                ("lean_warnings", "warnings"),
                f"run manifest topic {row.get('topic_id', '')}",
            ),
        )
        for row in facts.run_rows
    ]
    facts.verification_flags = [
        (
            row_bool(
                row, ("compiles",), f"verification topic {row.get('topic_id', '')}"
            ),
            row_bool(
                row,
                ("lean_has_sorry",),
                f"verification topic {row.get('topic_id', '')}",
            ),
            row_warnings(
                row,
                ("warnings",),
                f"verification topic {row.get('topic_id', '')}",
            ),
        )
        for row in facts.verification_rows
    ]
    return tuple(errors)


def _validate_run_manifest(
    run_manifest: dict[str, Any],
    summary: dict[str, Any] | None,
    root: Path,
    facts: _ReceiptFacts,
) -> tuple[str, ...]:
    """Reconcile the run manifest against the summary's recorded facts."""
    errors: list[str] = []
    summary_payload = summary or {}
    if "catalogue_topics" in run_manifest:
        errors.append("run manifest uses removed catalogue_topics receipt field")
    if run_manifest.get("receipt_schema_version") != REPORT_RECEIPT_SCHEMA_VERSION:
        errors.append(
            "run manifest receipt_schema_version must be "
            f"{REPORT_RECEIPT_SCHEMA_VERSION}"
        )
    if run_manifest.get("run_id") != root.name:
        errors.append("run manifest run_id does not match the report directory")
    if run_manifest.get("run_id") != summary_payload.get("run_id"):
        errors.append("summary and run manifest run_id values disagree")
    if run_manifest.get("mode") != facts.mode:
        errors.append("summary and run manifest mode disagree")
    if run_manifest.get("complete") != facts.complete:
        errors.append("summary and run manifest complete flags disagree")
    if run_manifest.get("selected_topics") != facts.selected_topics:
        errors.append("summary and run manifest selected-topic counts disagree")
    if run_manifest.get("live_catalogue_topics") != facts.live_catalogue_topics:
        errors.append("summary and run manifest live-catalogue counts disagree")
    if run_manifest.get("selected_topic_ids") != facts.selected_topic_ids:
        errors.append("summary and run manifest selected-topic IDs disagree")
    if run_manifest.get("selection") != summary_payload.get("selection"):
        errors.append("summary and run manifest selection evidence disagrees")
    if run_manifest.get("verified_topics") != facts.verified_topics:
        errors.append("summary and run manifest verified-topic counts disagree")
    if run_manifest.get("warning_count") != facts.warning_count:
        errors.append("summary and run manifest warning counts disagree")
    if run_manifest.get("capabilities") != summary_payload.get("capabilities"):
        errors.append("summary and run manifest capabilities disagree")
    if run_manifest.get("validation") != summary_payload.get("validation"):
        errors.append("summary and run manifest validation evidence disagrees")
    if run_manifest.get("lean_stats") != summary_payload.get("lean_stats"):
        errors.append("summary and run manifest Lean statistics disagree")
    if run_manifest.get("stats") != summary_payload.get("stats"):
        errors.append("summary and run manifest aggregate statistics disagree")
    if run_manifest.get("failure_reason") != summary_payload.get("failure_reason"):
        errors.append("summary and run manifest failure reasons disagree")
    for digest_name in (
        "source_digest",
        "config_digest",
        "roster_sha256",
        "catalogue_sources_sha256",
    ):
        if run_manifest.get(digest_name) != summary_payload.get(digest_name):
            errors.append(f"summary and run manifest {digest_name} values disagree")
    if run_manifest.get("toolchain") != summary_payload.get("toolchain"):
        errors.append("summary and run manifest toolchain values disagree")
    if run_manifest.get("owner_manifest_version") != OWNER_MANIFEST_VERSION:
        errors.append(
            "run manifest owner manifest version does not match this validator"
        )
    if run_manifest.get("owner_manifest_version") != summary_payload.get(
        "owner_manifest_version"
    ):
        errors.append("summary and run manifest owner manifest versions disagree")
    return tuple(errors)


def _validate_topic_agreement(facts: _ReceiptFacts) -> tuple[str, ...]:
    """Cross-check per-topic flags, evidence rows, and the mode row contract."""
    errors: list[str] = []
    for summary_row, summary_flags_row, run_flags_row in zip(
        facts.summary_rows,
        facts.summary_flags,
        facts.run_flags,
        strict=False,
    ):
        if run_flags_row[0] != summary_flags_row[0]:
            errors.append(
                f"run manifest success flag disagrees for {summary_row.get('topic_id', '')}"
            )
        if run_flags_row[1] != summary_flags_row[1]:
            errors.append(
                f"run manifest compile flag disagrees for {summary_row.get('topic_id', '')}"
            )
        if run_flags_row[2] != summary_flags_row[2]:
            errors.append(
                f"run manifest sorry flag disagrees for {summary_row.get('topic_id', '')}"
            )
        if run_flags_row[3] != summary_flags_row[3]:
            errors.append(
                f"run manifest warnings disagree for {summary_row.get('topic_id', '')}"
            )

    for summary_row, run_row in zip(facts.summary_rows, facts.run_rows, strict=False):
        if _canonical_evidence_row(run_row) != _canonical_evidence_row(summary_row):
            errors.append(
                "summary and run manifest evidence rows disagree for "
                f"{summary_row.get('topic_id', '')}"
            )

    expected_row_count = len(facts.summary_rows) if facts.mode == "full" else 0
    if facts.mode == "full" and len(facts.summary_rows) != facts.selected_topics:
        errors.append("full-mode summary topic rows do not match selected-topic count")
    if facts.mode == "full" and facts.summary_ids != facts.selected_topic_ids:
        errors.append("full-mode summary topic rows do not match selected topic IDs")
    if facts.mode == "catalogue" and facts.summary_rows:
        errors.append("catalogue-mode summary must not contain verification topic rows")
    if len(facts.run_rows) != expected_row_count:
        errors.append("run manifest topic rows do not match the mode contract")
    if facts.verification_ids != facts.summary_ids[:expected_row_count]:
        errors.append("verification manifest topic rows do not match summary topics")
    return tuple(errors)


def _validate_verification_manifest(
    verification_manifest: dict[str, Any],
    facts: _ReceiptFacts,
) -> tuple[str, ...]:
    """Reconcile the verification manifest against the summary topic rows."""
    errors: list[str] = []
    if (
        verification_manifest.get("receipt_schema_version")
        != REPORT_RECEIPT_SCHEMA_VERSION
    ):
        errors.append(
            "verification manifest receipt_schema_version must be "
            f"{REPORT_RECEIPT_SCHEMA_VERSION}"
        )
    expected_true = sum(compiles for compiles, _, _ in facts.verification_flags)
    expected_false = len(facts.verification_rows) - expected_true
    expected_warning_count = sum(
        len(warnings) for _, _, warnings in facts.verification_flags
    )
    expected_warning_topics = sum(
        bool(warnings) for _, _, warnings in facts.verification_flags
    )
    if verification_manifest.get("verify_lean_ran") != bool(facts.verification_rows):
        errors.append("verification manifest verify_lean_ran disagrees with its rows")
    if verification_manifest.get("topics_with_result") != len(facts.verification_rows):
        errors.append(
            "verification manifest topics_with_result disagrees with its rows"
        )
    if verification_manifest.get("compiles_true") != expected_true:
        errors.append("verification manifest compiles_true disagrees with its rows")
    if verification_manifest.get("compiles_false") != expected_false:
        errors.append("verification manifest compiles_false disagrees with its rows")
    if verification_manifest.get("warning_count") != expected_warning_count:
        errors.append("verification manifest warning_count disagrees with its rows")
    if verification_manifest.get("topics_with_warnings") != expected_warning_topics:
        errors.append(
            "verification manifest topics_with_warnings disagrees with its rows"
        )
    for (
        summary_row,
        summary_flags_row,
        verification_flags_row,
        verification_row,
    ) in zip(
        facts.summary_rows,
        facts.summary_flags,
        facts.verification_flags,
        facts.verification_rows,
        strict=False,
    ):
        expected_compiles = summary_flags_row[1]
        expected_sorry = summary_flags_row[2]
        expected_warnings = summary_flags_row[3]
        verification_compiles, verification_sorry, verification_warnings = (
            verification_flags_row
        )
        if verification_compiles != expected_compiles:
            errors.append(
                f"verification compile flag disagrees for {summary_row.get('topic_id', '')}"
            )
        if verification_sorry != expected_sorry:
            errors.append(
                f"verification sorry flag disagrees for {summary_row.get('topic_id', '')}"
            )
        if verification_warnings != expected_warnings:
            errors.append(
                f"verification warnings disagree for {summary_row.get('topic_id', '')}"
            )
        if _canonical_evidence_row(verification_row) != _canonical_evidence_row(
            summary_row
        ):
            errors.append(
                "summary and verification manifest evidence rows disagree for "
                f"{summary_row.get('topic_id', '')}"
            )
    return tuple(errors)


def _validate_derived_summary(
    summary: dict[str, Any] | None,
    facts: _ReceiptFacts,
) -> tuple[str, ...]:
    """Recompute derived counts and statistics from canonical topic rows."""
    errors: list[str] = []
    expected_verified = sum(
        success and compiles and not has_sorry and not warnings
        for success, compiles, has_sorry, warnings in facts.summary_flags
    )
    facts.expected_warning_count = sum(
        len(warnings) for _, _, _, warnings in facts.summary_flags
    )
    if summary is not None and facts.warning_count != facts.expected_warning_count:
        errors.append("summary warning_count disagrees with its topic rows")
    if facts.verified_topics != expected_verified:
        errors.append("summary verified_topics disagrees with clean topic rows")
    if facts.mode == "catalogue" and facts.verified_topics != 0:
        errors.append("catalogue mode cannot report verified topics")

    summary_stages = (summary or {}).get("stages")
    summary_stages = summary_stages if isinstance(summary_stages, list) else []
    expected_lean_stats = _derived_lean_stats(facts.summary_rows)
    if (summary or {}).get("lean_stats") != expected_lean_stats:
        errors.append("summary lean_stats disagree with canonical topic rows")
    expected_stats = _derived_report_stats(
        facts.summary_rows,
        [stage for stage in summary_stages if isinstance(stage, dict)],
        facts.selected_topics,
    )
    if (summary or {}).get("stats") != expected_stats:
        errors.append("summary stats disagree with canonical topic rows and stages")
    return tuple(errors)


def _validate_catalogue_completion(
    summary: dict[str, Any] | None,
) -> tuple[str, ...]:
    """Enforce the completion policy for a complete catalogue-mode receipt."""
    errors: list[str] = []
    catalogue_validation = (summary or {}).get("validation")
    catalogue_validation = (
        catalogue_validation if isinstance(catalogue_validation, dict) else {}
    )
    catalogue_checks = catalogue_validation.get("checks")
    catalogue_checks = catalogue_checks if isinstance(catalogue_checks, list) else []
    catalogue_check_names = [
        check.get("name") for check in catalogue_checks if isinstance(check, dict)
    ]
    if catalogue_check_names != list(CATALOGUE_VALIDATION_CHECK_NAMES):
        errors.append(
            "complete catalogue-mode environment checks do not match the required policy"
        )
    if (
        catalogue_validation.get("status") != "ok"
        or type(catalogue_validation.get("failed_count")) is not int
        or catalogue_validation.get("failed_count") != 0
    ):
        errors.append("complete catalogue-mode environment validation must be clean")
    if any(
        not isinstance(check, dict)
        or check.get("ok") is not True
        or not isinstance(check.get("message"), str)
        for check in catalogue_checks
    ):
        errors.append("complete catalogue-mode environment checks must be true")
    catalogue_capabilities = (summary or {}).get("capabilities")
    catalogue_capabilities = (
        catalogue_capabilities if isinstance(catalogue_capabilities, dict) else {}
    )
    expected_catalogue_capabilities = {
        "catalogue",
        "verification",
        *CATALOGUE_VALIDATION_CHECK_NAMES,
    }
    if set(catalogue_capabilities) != expected_catalogue_capabilities:
        errors.append(
            "complete catalogue-mode capabilities do not match the required policy"
        )
    if catalogue_capabilities.get("catalogue") is not True or (
        catalogue_capabilities.get("verification") is not False
    ):
        errors.append("complete catalogue-mode capability values are inconsistent")
    if any(
        catalogue_capabilities.get(name) is not True
        for name in CATALOGUE_VALIDATION_CHECK_NAMES
    ):
        errors.append("complete catalogue-mode contains a failed capability")
    catalogue_stages = (summary or {}).get("stages")
    catalogue_stages = catalogue_stages if isinstance(catalogue_stages, list) else []
    expected_catalogue_stage_statuses = (
        ("Load Catalogue", "ok"),
        ("Environment Validation", "ok"),
        ("Gauss Sessions", "not_run"),
        ("Manuscript Artifacts", "ok"),
    )
    if [
        (stage.get("name"), stage.get("status"))
        for stage in catalogue_stages
        if isinstance(stage, dict)
    ] != list(expected_catalogue_stage_statuses):
        errors.append(
            "complete catalogue-mode receipt has inconsistent pipeline stages"
        )
    if (summary or {}).get("status") != "ok" or (summary or {}).get(
        "failure_reason"
    ) != "":
        errors.append("complete catalogue-mode summary state is inconsistent")
    return tuple(errors)


def _validate_full_completion(
    summary: dict[str, Any] | None,
    run_manifest: dict[str, Any] | None,
    facts: _ReceiptFacts,
) -> tuple[str, ...]:
    """Enforce the completion policy for a complete full-mode receipt."""
    errors: list[str] = []
    toolchain = (
        (summary or {}).get("toolchain", {})
        if isinstance((summary or {}).get("toolchain"), dict)
        else {}
    )
    lean_toolchain = toolchain.get("lean_toolchain")
    lean_version = toolchain.get("lean_version")
    mathlib_tag = toolchain.get("mathlib_tag")
    mathlib_revision = toolchain.get("mathlib_revision")
    if (
        not isinstance(lean_toolchain, str)
        or pinned_lean_semver(lean_toolchain) is None
    ):
        errors.append("complete full-mode receipt must pin a Lean semantic version")
        lean_toolchain = ""
    if not isinstance(lean_version, str) or actual_lean_semver(lean_version) is None:
        errors.append(
            "complete full-mode receipt must record actual Lean version output"
        )
        lean_version = ""
    elif not lean_version_matches_pin(lean_version, lean_toolchain):
        errors.append("complete full-mode actual Lean version does not match its pin")
    if not isinstance(mathlib_tag, str) or not re.fullmatch(
        r"v\d+\.\d+\.\d+", mathlib_tag
    ):
        errors.append("complete full-mode receipt must pin a Mathlib version")
    elif lean_toolchain and mathlib_tag.removeprefix("v") != pinned_lean_semver(
        lean_toolchain
    ):
        errors.append("complete full-mode Mathlib tag does not match Lean pin")
    if not isinstance(mathlib_revision, str) or not re.fullmatch(
        r"[0-9a-f]{40}", mathlib_revision
    ):
        errors.append(
            "complete full-mode receipt must bind the resolved Mathlib revision"
        )

    capabilities = (summary or {}).get("capabilities")
    if not isinstance(capabilities, dict):
        capabilities = {}
    if capabilities.get("catalogue") is not True:
        errors.append("complete full-mode receipt must record catalogue capability")
    if capabilities.get("verification") is not True:
        errors.append("complete full-mode receipt must record verification capability")
    if any(value is not True for value in capabilities.values()):
        errors.append("complete full-mode receipt contains a failed capability")
    expected_capability_names = {
        "catalogue",
        "verification",
        *FULL_VALIDATION_CHECK_NAMES,
    }
    if set(capabilities) != expected_capability_names:
        errors.append(
            "complete full-mode capabilities do not match the required policy"
        )

    validation = (summary or {}).get("validation")
    validation = validation if isinstance(validation, dict) else {}
    if validation.get("status") != "ok":
        errors.append("complete full-mode environment validation must be ok")
    if (
        type(validation.get("failed_count")) is not int
        or validation.get("failed_count") != 0
    ):
        errors.append(
            "complete full-mode environment validation must report zero failures"
        )
    checks = validation.get("checks")
    if not isinstance(checks, list) or not checks:
        errors.append(
            "complete full-mode environment validation must retain named checks"
        )
        checks = []
    check_names: list[str] = []
    for check in checks:
        if not isinstance(check, dict):
            errors.append("complete full-mode environment checks must be objects")
            continue
        name = check.get("name")
        if not isinstance(name, str) or not name:
            errors.append(
                "complete full-mode environment check names must be non-empty"
            )
        else:
            check_names.append(name)
            if capabilities.get(name) is not True:
                errors.append(
                    f"complete full-mode capability evidence is missing for {name}"
                )
        if check.get("ok") is not True:
            errors.append(f"complete full-mode environment check {name!r} must be true")
        if not isinstance(check.get("message"), str):
            errors.append(
                f"complete full-mode environment check {name!r} message must be a string"
            )
        check_duration = check.get("duration_s")
        if (
            not isinstance(check_duration, (int, float))
            or isinstance(check_duration, bool)
            or not math.isfinite(float(check_duration))
            or float(check_duration) < 0
        ):
            errors.append(
                f"complete full-mode environment check {name!r} duration must be finite and non-negative"
            )
    if len(check_names) != len(set(check_names)):
        errors.append("complete full-mode environment check names must be unique")
    if check_names != list(FULL_VALIDATION_CHECK_NAMES):
        errors.append(
            "complete full-mode environment checks do not match the required policy"
        )

    stages = (summary or {}).get("stages")
    stages = stages if isinstance(stages, list) else []
    expected_stage_names = [
        "Load Catalogue",
        "Environment Validation",
        "Gauss Sessions",
        "Manuscript Artifacts",
    ]
    if [stage.get("name") for stage in stages if isinstance(stage, dict)] != (
        expected_stage_names
    ):
        errors.append(
            "complete full-mode receipt must retain the four ordered pipeline stages"
        )
    for stage in stages:
        if not isinstance(stage, dict):
            continue
        stage_name = stage.get("name", "")
        if stage.get("status") != "ok":
            errors.append(
                f"complete full-mode stage {stage_name!r} must have status ok"
            )
        if stage.get("error") not in (None, ""):
            errors.append(
                f"complete full-mode stage {stage_name!r} cannot retain an error"
            )
        stage_duration = stage.get("duration_s")
        if (
            not isinstance(stage_duration, (int, float))
            or isinstance(stage_duration, bool)
            or not math.isfinite(float(stage_duration))
            or float(stage_duration) < 0
        ):
            errors.append(
                f"complete full-mode stage {stage_name!r} duration must be finite and non-negative"
            )

    if (summary or {}).get("failure_reason") != "":
        errors.append("complete full-mode summary failure_reason must be empty")
    total_duration = (summary or {}).get("total_duration")
    if (
        not isinstance(total_duration, (int, float))
        or isinstance(total_duration, bool)
        or not math.isfinite(float(total_duration))
        or float(total_duration) < 0
    ):
        errors.append(
            "complete full-mode total_duration must be finite and non-negative"
        )
    if summary is not None and summary.get("status") != "ok":
        errors.append("complete full-mode summary must have status ok")
    if not facts.summary_rows or facts.selected_topics == 0:
        errors.append("complete full-mode receipt must select at least one topic")
    if facts.verified_topics != facts.selected_topics:
        errors.append("complete full-mode receipt does not verify every selected topic")
    if facts.expected_warning_count:
        errors.append("complete full-mode receipt must contain zero Lean warnings")
    for row in facts.summary_rows:
        topic_id = str(row.get("topic_id", ""))
        for field_name in (
            "success",
            "hermes_success",
            "lean_compiles",
            "hermes_lean_compiles",
        ):
            if row.get(field_name) is not True:
                errors.append(
                    f"complete full-mode {topic_id} must record {field_name}=true"
                )
        if row.get("lean_has_sorry") is not False:
            errors.append(
                f"complete full-mode {topic_id} must record lean_has_sorry=false"
            )
        if row.get("lean_warnings") != []:
            errors.append(
                f"complete full-mode {topic_id} must record zero Lean warnings"
            )
        for field_name, expected in (
            ("status", "success"),
            ("workflow", "verify"),
            ("verification_source", "hermes_refined"),
        ):
            if row.get(field_name) != expected:
                errors.append(
                    f"complete full-mode {topic_id} must record "
                    f"{field_name}={expected!r}"
                )
        for field_name in ("session_id", "hermes_model"):
            value = row.get(field_name)
            if not isinstance(value, str) or not value.strip():
                errors.append(
                    f"complete full-mode {topic_id} must record non-empty {field_name}"
                )
        refined = row.get("refined_lean_sketch")
        final = row.get("final_lean_sketch")
        if not isinstance(refined, str) or not refined.strip():
            errors.append(
                f"complete full-mode {topic_id} must record refined Lean source"
            )
        if not isinstance(final, str) or not final.strip():
            errors.append(
                f"complete full-mode {topic_id} must record final compiled Lean source"
            )
            final = ""
        if refined != final:
            errors.append(
                f"complete full-mode {topic_id} refined and final Lean source disagree"
            )
        compiled_digest = row.get("compiled_source_sha256")
        if not isinstance(compiled_digest, str) or not _SHA256_RE.fullmatch(
            compiled_digest
        ):
            errors.append(
                f"complete full-mode {topic_id} must record compiled source digest"
            )
        elif (
            final
            and compiled_digest != hashlib.sha256(final.encode("utf-8")).hexdigest()
        ):
            errors.append(
                f"complete full-mode {topic_id} compiled source digest disagrees"
            )
        if row.get("semantic_contract_preserved") is not True:
            errors.append(
                f"complete full-mode {topic_id} must preserve the canonical Lean token contract"
            )
        for field_name in (
            "canonical_source_sha256",
            "semantic_contract_sha256",
        ):
            value = row.get(field_name)
            if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
                errors.append(f"complete full-mode {topic_id} must record {field_name}")
        if row.get("lean_version") != lean_version:
            errors.append(
                f"complete full-mode {topic_id} Lean version disagrees with toolchain evidence"
            )
        if row.get("error") not in ("", None):
            errors.append(
                f"complete full-mode {topic_id} cannot retain a verification error"
            )
        for field_name in ("tokens_used", "network_retries"):
            value = row.get(field_name)
            if type(value) is not int or value < 0:
                errors.append(
                    f"complete full-mode {topic_id} {field_name} must be a non-negative integer"
                )
        duration = row.get("duration_s")
        if (
            not isinstance(duration, (int, float))
            or isinstance(duration, bool)
            or not math.isfinite(float(duration))
            or float(duration) < 0
        ):
            errors.append(
                f"complete full-mode {topic_id} duration_s must be finite and non-negative"
            )
        if not isinstance(row.get("cache_hit"), bool):
            errors.append(f"complete full-mode {topic_id} cache_hit must be a boolean")
        if not isinstance(row.get("chain_advance_reason"), str):
            errors.append(
                f"complete full-mode {topic_id} chain_advance_reason must be a string"
            )
        if not isinstance(row.get("stage_results"), list):
            errors.append(f"complete full-mode {topic_id} stage_results must be a list")
    if (
        run_manifest is not None
        and run_manifest.get("verification_source") != "hermes_refined"
    ):
        errors.append(
            "complete full-mode run manifest has the wrong verification source"
        )
    if run_manifest is not None and run_manifest.get("lean_clean") is not True:
        errors.append("complete full-mode run manifest must mark lean_clean true")
    if run_manifest is not None and run_manifest.get("warnings_clean") is not True:
        errors.append("complete full-mode run manifest must mark warnings_clean true")
    return tuple(errors)


def _validate_live_binding(
    project_root: Path,
    summary: dict[str, Any],
    root: Path,
    facts: _ReceiptFacts,
) -> tuple[str, ...]:
    """Recompute digests and catalogue contracts against the live owner tree.

    A synthetic directory whose missing files merely hash as ``<missing>`` is
    structural evidence only and can never be claim-ready.
    """
    errors: list[str] = []
    live_root = Path(project_root).resolve()
    owner_errors = report_owner_errors(live_root)
    errors.extend(f"live source binding failed: {error}" for error in owner_errors)
    facts.source_bound = not owner_errors
    recomputed_source = report_source_digest(live_root)
    recomputed_config = report_config_digest(live_root)
    recomputed_catalogue_sources = catalogue_sources_digest(live_root)
    for name, stored, recomputed in (
        ("source_digest", summary.get("source_digest"), recomputed_source),
        ("config_digest", summary.get("config_digest"), recomputed_config),
        (
            "catalogue_sources_sha256",
            summary.get("catalogue_sources_sha256"),
            recomputed_catalogue_sources,
        ),
    ):
        if stored != recomputed:
            facts.source_bound = False
            errors.append(
                f"summary {name} does not match the live source tree "
                f"(stored {stored}, live {recomputed})"
            )
    stored_toolchain = summary.get("toolchain")
    if isinstance(stored_toolchain, dict):
        live_toolchain = _toolchain_snapshot(
            live_root,
            lean_version=str(stored_toolchain.get("lean_version", "")),
        )
        if stored_toolchain != live_toolchain:
            facts.source_bound = False
            errors.append("summary toolchain does not match the live source tree")
    else:
        facts.source_bound = False
    try:
        live_catalogue = FEPTopicCatalogue.from_yaml(
            live_root / "config" / "topics.yaml"
        )
    except (OSError, TypeError, ValueError) as exc:
        facts.source_bound = False
        errors.append(f"live catalogue cannot be loaded: {exc}")
    else:
        live_ids = [topic.id for topic in live_catalogue.topics]
        if summary.get("live_catalogue_topics") != len(live_ids):
            facts.source_bound = False
            errors.append(
                "summary live_catalogue_topics does not match the live catalogue"
            )
        if summary.get("roster_sha256") != topic_ids_sha256(live_ids):
            facts.source_bound = False
            errors.append("summary roster_sha256 does not match the live catalogue")
        if summary.get("catalogue") != live_catalogue.summary():
            facts.source_bound = False
            errors.append("summary catalogue does not match the live catalogue")
        live_selection = summary.get("selection")
        live_selection = live_selection if isinstance(live_selection, dict) else {}
        if live_selection.get("topic_ids") != facts.selected_topic_ids:
            facts.source_bound = False
        if live_selection.get("total_catalogue_topics") != len(live_ids):
            facts.source_bound = False
            errors.append("summary selection total does not match the live catalogue")
        if any(topic_id not in live_ids for topic_id in facts.selected_topic_ids):
            facts.source_bound = False
            errors.append("summary selects a topic absent from the live catalogue")
        live_selected_order = [
            topic_id for topic_id in live_ids if topic_id in facts.selected_topic_ids
        ]
        if facts.selected_topic_ids != live_selected_order:
            facts.source_bound = False
            errors.append("summary selection does not preserve live catalogue order")

        live_by_id = {topic.id: topic for topic in live_catalogue.topics}
        for row in facts.summary_rows:
            live_topic_id = row.get("topic_id")
            if not isinstance(live_topic_id, str) or live_topic_id not in live_by_id:
                facts.source_bound = False
                continue
            canonical = live_by_id[live_topic_id].lean_sketch
            expected_canonical_digest = hashlib.sha256(
                canonical.encode("utf-8")
            ).hexdigest()
            expected_contract_digest = lean_semantic_contract_sha256(canonical)
            if row.get("canonical_source_sha256") != expected_canonical_digest:
                facts.source_bound = False
                errors.append(
                    f"{live_topic_id} canonical source digest disagrees with the live catalogue"
                )
            if row.get("semantic_contract_sha256") != expected_contract_digest:
                facts.source_bound = False
                errors.append(
                    f"{live_topic_id} semantic contract digest disagrees with the live catalogue"
                )
            final_source = row.get("final_lean_sketch")
            if not isinstance(final_source, str) or not (
                preserves_lean_semantic_contract(final_source, canonical)
            ):
                facts.source_bound = False
                errors.append(
                    f"{live_topic_id} final Lean source changes the live canonical token contract"
                )

        result_proxy = _report_projection_result(summary)
        expected_index = Reporter(
            live_root,
            run_id=root.name,
        )._index_md(live_catalogue, result_proxy, topics=facts.summary_rows)
        index_path = root / "index.md"
        if index_path.is_file():
            try:
                actual_index = index_path.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                errors.append(f"cannot read index.md: {exc}")
            else:
                if actual_index != expected_index:
                    errors.append(
                        "index.md does not match its structured live evidence"
                    )
    return tuple(errors)


def validate_report_receipt(
    report_root: Path,
    *,
    require_complete: bool = False,
    project_root: Path | None = None,
) -> dict[str, Any]:
    """Independently validate a generated report bundle.

    The report's ``summary.json`` is intentionally excluded from its own hash
    map because the map lives inside that file.  This validator therefore
    recomputes every listed artifact hash, rejects path traversal, and
    reconciles the summary, run manifest, and verification manifest.  It does
    not execute Lean, Hermes, OpenGauss, or any other external process.

    When ``project_root`` is supplied, the stored ``source_digest`` /
    ``config_digest`` values are recomputed against the live source tree and
    drift is reported as an error, closing the provenance gap between a receipt
    and the tree it claims to represent.

    ``claim_ready`` is stricter than ``valid``: it is true only for a complete,
    non-empty full-mode receipt whose selected topics all have clean final Lean
    results *and* whose source/config digests were checked against a supplied
    live project root.  Omitting ``project_root`` permits structural validation
    only.  Callers can use ``require_complete=True`` as a policy input while
    still receiving the same structured diagnostics.
    """
    root = Path(report_root).resolve()
    errors: list[str] = []
    facts = _ReceiptFacts()

    def read_json(name: str) -> dict[str, Any] | None:
        path = root / name
        if not path.is_file():
            errors.append(f"missing {name}")
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            errors.append(f"invalid {name}: {exc}")
            return None
        if not isinstance(payload, dict):
            errors.append(f"{name} must contain a JSON object")
            return None
        return payload

    if not root.is_dir():
        return {
            "status": "error",
            "valid": False,
            "claim_ready": False,
            "source_bound": False,
            "require_complete": require_complete,
            "report_root": str(root),
            "checked_artifacts": 0,
            "errors": [f"report directory is missing: {root}"],
        }

    summary = read_json("summary.json")
    run_manifest = read_json("run_manifest.json")
    verification_manifest = read_json("verification_manifest.json")

    if summary is not None:
        errors.extend(_validate_summary_header(summary, root, facts))
        errors.extend(_validate_artifact_hashes(summary, root, facts))
        errors.extend(_validate_rendered_evidence(summary, root, facts))
    errors.extend(_validate_topic_rows(run_manifest, verification_manifest, facts))
    if run_manifest is not None:
        errors.extend(_validate_run_manifest(run_manifest, summary, root, facts))
    errors.extend(_validate_topic_agreement(facts))
    if verification_manifest is not None:
        errors.extend(_validate_verification_manifest(verification_manifest, facts))
    errors.extend(_validate_derived_summary(summary, facts))
    if facts.mode == "catalogue" and facts.complete:
        errors.extend(_validate_catalogue_completion(summary))
    if facts.mode == "full" and facts.complete:
        errors.extend(_validate_full_completion(summary, run_manifest, facts))
    elif (
        run_manifest is not None
        and run_manifest.get("verification_source") != "none"
        and not facts.summary_rows
    ):
        errors.append("run manifest reports a verification source without topic rows")
    if project_root is not None and summary is not None:
        errors.extend(_validate_live_binding(project_root, summary, root, facts))

    claim_ready = (
        not errors
        and facts.source_bound
        and facts.mode == "full"
        and facts.complete
        and facts.selected_topics > 0
        and facts.selected_topics == facts.live_catalogue_topics
        and facts.selected_topics
        == facts.verified_topics
        == len(facts.summary_rows)
        == len(facts.verification_rows)
    )
    if require_complete and not claim_ready:
        errors.append("complete full-mode receipt is required")

    return {
        "status": "ok" if not errors else "error",
        "valid": not errors,
        "claim_ready": claim_ready,
        "source_bound": facts.source_bound,
        "require_complete": require_complete,
        "report_root": str(root),
        "mode": facts.mode,
        "complete": facts.complete,
        "live_catalogue_topics": facts.live_catalogue_topics,
        "selected_topics": facts.selected_topics,
        "verified_topics": facts.verified_topics,
        "checked_artifacts": facts.checked_artifacts,
        "errors": errors,
    }


@dataclass(frozen=True)
class ReportPaths:
    root: Path
    index_md: Path
    summary_json: Path
    hermes_md: Path
    lean_md: Path
    validation_md: Path
    manifest_json: Path
    run_manifest_json: Path | None = None

    def as_dict(self) -> dict[str, str]:
        data = {
            "root": str(self.root),
            "index_md": str(self.index_md),
            "summary_json": str(self.summary_json),
            "hermes_md": str(self.hermes_md),
            "lean_md": str(self.lean_md),
            "validation_md": str(self.validation_md),
            "verification_manifest": str(self.manifest_json),
        }
        if self.run_manifest_json is not None:
            data["run_manifest"] = str(self.run_manifest_json)
        return data


class Reporter:
    def __init__(
        self,
        project_root: Path,
        *,
        run_id: str | None = None,
        output_root: Path | None = None,
    ) -> None:
        self.project_root = Path(project_root)
        self.output_root = (
            Path(output_root)
            if output_root is not None
            else self.project_root / "output"
        )
        self.reports_dir = self.output_root / "reports"
        self.run_id = run_id or _default_run_id()

    @staticmethod
    def build_verification_manifest(results: Iterable[Any]) -> dict[str, Any]:
        rows = []
        for result in results:
            row = (
                dict(result)
                if isinstance(result, dict)
                else {"topic_id": getattr(result, "topic_id", "")}
            )
            if "compiles" not in row:
                row["compiles"] = bool(
                    row.get("lean_compiles", getattr(result, "compiles", False))
                )
            if "lean_has_sorry" not in row:
                row["lean_has_sorry"] = bool(
                    row.get("has_sorry", getattr(result, "has_sorry", False))
                )
            warnings = row.get(
                "lean_warnings", row.get("warnings", getattr(result, "warnings", []))
            )
            row["warnings"] = (
                list(warnings) if isinstance(warnings, tuple) else warnings
            )
            rows.append(row)
        return {
            "receipt_schema_version": REPORT_RECEIPT_SCHEMA_VERSION,
            "verify_lean_ran": bool(rows),
            "topics_with_result": len(rows),
            "compiles_true": sum(bool(r.get("compiles")) for r in rows),
            "compiles_false": sum(not bool(r.get("compiles")) for r in rows),
            "warning_count": sum(
                len(r.get("warnings", []))
                for r in rows
                if isinstance(r.get("warnings", []), list)
            ),
            "topics_with_warnings": sum(bool(r.get("warnings")) for r in rows),
            "results": rows,
        }

    def generate(self, catalogue: FEPTopicCatalogue, result: Any) -> ReportPaths:
        topics = self._topic_rows(result)
        topic_ids = [row.get("topic_id") for row in topics]
        if any(
            not isinstance(topic_id, str) or not _TOPIC_ID_RE.fullmatch(topic_id)
            for topic_id in topic_ids
        ):
            raise ValueError("report topic IDs must use the canonical fep-NNN form")
        if len(set(topic_ids)) != len(topic_ids):
            raise ValueError("report topic IDs must be unique")
        topics = _bind_canonical_topic_evidence(catalogue, topics)
        selected_topic_ids = _selected_topic_ids(catalogue, result, topics)
        root = self.reports_dir / self.run_id
        root.mkdir(parents=True, exist_ok=False)
        summary = result.as_dict() if hasattr(result, "as_dict") else dict(result)
        summary["topics"] = topics
        summary["run_id"] = self.run_id
        summary["catalogue"] = catalogue.summary()
        summary.pop("catalogue_topics", None)
        summary["live_catalogue_topics"] = len(catalogue.topics)
        summary["selected_topics"] = len(selected_topic_ids)
        summary["selected_topic_ids"] = selected_topic_ids
        summary["selection"] = {
            "topic_ids": selected_topic_ids,
            "total_catalogue_topics": len(catalogue.topics),
        }
        summary_stages = summary.get("stages", [])
        summary_stages = summary_stages if isinstance(summary_stages, list) else []
        summary["lean_stats"] = _derived_lean_stats(topics)
        summary["stats"] = _derived_report_stats(
            topics,
            [stage for stage in summary_stages if isinstance(stage, dict)],
            len(selected_topic_ids),
        )
        summary["warning_count"] = sum(
            len(row.get("lean_warnings", []))
            for row in topics
            if isinstance(row.get("lean_warnings", []), list)
        )
        source_digest = report_source_digest(self.project_root)
        config_digest = report_config_digest(self.project_root)
        roster_sha256 = topic_ids_sha256(tuple(topic.id for topic in catalogue.topics))
        catalogue_sources_sha256 = catalogue_sources_digest(self.project_root)
        validation_evidence = _validation_evidence(result)
        summary["validation"] = validation_evidence
        row_versions = [
            row.get("lean_version")
            for row in topics
            if isinstance(row.get("lean_version"), str) and row.get("lean_version")
        ]
        recorded_lean_version = (
            str(row_versions[0])
            if len(row_versions) == len(topics) and len(set(row_versions)) == 1
            else ""
        )
        toolchain = _toolchain_snapshot(
            self.project_root,
            lean_version=recorded_lean_version,
        )
        run_manifest = {
            "receipt_schema_version": REPORT_RECEIPT_SCHEMA_VERSION,
            "run_id": self.run_id,
            "mode": summary.get("mode", ""),
            "complete": bool(summary.get("complete", False)),
            "live_catalogue_topics": len(catalogue.topics),
            "selected_topics": len(selected_topic_ids),
            "selected_topic_ids": selected_topic_ids,
            "selection": summary["selection"],
            "verified_topics": int(summary.get("verified_topics", 0)),
            "warning_count": int(summary["warning_count"]),
            "capabilities": summary.get("capabilities", {}),
            "validation": validation_evidence,
            "lean_stats": summary["lean_stats"],
            "stats": summary["stats"],
            "verification_source": "hermes_refined"
            if any(
                row.get("verification_source") == "hermes_refined"
                or row.get("hermes_success")
                for row in topics
            )
            else "none",
            "lean_clean": bool(summary.get("complete", False))
            and int(summary.get("verified_topics", 0)) == len(selected_topic_ids)
            and summary.get("mode") == "full"
            and summary["warning_count"] == 0,
            "warnings_clean": summary["warning_count"] == 0,
            "failure_reason": summary.get("failure_reason", ""),
            "source_digest": source_digest,
            "config_digest": config_digest,
            "roster_sha256": roster_sha256,
            "catalogue_sources_sha256": catalogue_sources_sha256,
            "owner_manifest_version": OWNER_MANIFEST_VERSION,
            "toolchain": toolchain,
            "topics": topics,
        }
        summary["source_digest"] = source_digest
        summary["config_digest"] = config_digest
        summary["roster_sha256"] = roster_sha256
        summary["catalogue_sources_sha256"] = catalogue_sources_sha256
        summary["receipt_schema_version"] = REPORT_RECEIPT_SCHEMA_VERSION
        summary["owner_manifest_version"] = OWNER_MANIFEST_VERSION
        summary["toolchain"] = toolchain
        summary["artifact_hashes"] = {}
        projection_result = _report_projection_result(summary)
        for name, content in (
            ("hermes.md", self._hermes_md(topics)),
            ("lean.md", self._lean_md(summary["lean_stats"])),
            ("validation.md", _render_validation_markdown(validation_evidence)),
            ("index.md", self._index_md(catalogue, projection_result, topics=topics)),
        ):
            atomic_write_text(root / name, content)
        for row in topics:
            topic_id = str(row["topic_id"])
            atomic_write_text(root / "topics" / f"{topic_id}.md", self._topic_md(row))
        manifest = self.build_verification_manifest(topics)
        atomic_write_text(
            root / "verification_manifest.json",
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        )
        atomic_write_text(
            root / "run_manifest.json",
            json.dumps(run_manifest, indent=2, sort_keys=True, default=str) + "\n",
        )
        # ``summary.json`` contains this map, so hashing it would create a
        # self-referential value.  Hash every other report artifact, including
        # nested per-topic files, and make the exclusion explicit in the key
        # name's surrounding schema rather than publishing a stale digest.
        hashes = {
            p.relative_to(root).as_posix(): sha256_bytes(p.read_bytes())
            for p in sorted(root.rglob("*"))
            if p.is_file() and p.name != "summary.json"
        }
        summary["artifact_hashes"] = hashes
        atomic_write_text(
            root / "summary.json",
            json.dumps(summary, indent=2, sort_keys=True, default=str) + "\n",
        )
        return ReportPaths(
            root,
            root / "index.md",
            root / "summary.json",
            root / "hermes.md",
            root / "lean.md",
            root / "validation.md",
            root / "verification_manifest.json",
            root / "run_manifest.json",
        )

    @staticmethod
    def _topic_rows(result: Any) -> list[dict[str, Any]]:
        def normalize(row: dict[str, Any]) -> dict[str, Any]:
            normalized = dict(row)
            if "lean_warnings" not in normalized:
                warnings = normalized.get("warnings", [])
                normalized["lean_warnings"] = (
                    list(warnings) if isinstance(warnings, tuple) else warnings
                )
            final_source = normalized.get("final_lean_sketch")
            if isinstance(final_source, str) and final_source:
                normalized["compiled_source_sha256"] = hashlib.sha256(
                    final_source.encode("utf-8")
                ).hexdigest()
            return normalized

        direct = getattr(result, "topic_results", [])
        rows = [
            normalize(row.as_dict() if hasattr(row, "as_dict") else dict(row))
            for row in direct
        ]
        if rows:
            return rows
        for stage in getattr(result, "stages", []):
            if stage.name != "Gauss Sessions" or not isinstance(stage.payload, dict):
                continue
            candidate = (
                stage.payload.get("topics") or stage.payload.get("results") or []
            )
            return [
                normalize(row.as_dict() if hasattr(row, "as_dict") else dict(row))
                for row in candidate
            ]
        return []

    def _index_md(
        self,
        catalogue: FEPTopicCatalogue,
        result: Any,
        *,
        topics: list[dict[str, Any]] | None = None,
    ) -> str:
        stats = getattr(result, "stats", {})
        rows = topics if topics is not None else self._topic_rows(result)
        direct = sum(bool(row.get("hermes_lean_compiles")) for row in rows)
        final = sum(
            bool(row.get("lean_compiles"))
            and not bool(row.get("lean_has_sorry"))
            and not bool(row.get("lean_warnings"))
            for row in rows
        )
        selected_topics = int(
            getattr(result, "catalogue_topics", 0) or len(rows) or len(catalogue.topics)
        )
        lines = [
            f"# fep_lean run `{self.run_id}`",
            "",
            f"**Status:** `{getattr(result, 'status', 'unknown')}`",
            f"**Mode:** `{getattr(result, 'mode', 'full')}`",
            f"**Total Topics:** {selected_topics}",
            f"**Catalogue Topics:** {len(catalogue.topics)}",
            f"**Verified topics:** {getattr(result, 'verified_topics', 0)}",
            f"**Hermes-refined Lean compiled directly:** {direct}/{len(rows) or 0}",
            f"**Final Lean compiled:** {final}/{len(rows) or 0}",
            "",
            "## Stages",
            "",
            "| Stage | Status | Duration |",
            "| --- | --- | ---: |",
        ]
        for stage in getattr(result, "stages", []):
            lines.append(f"| {stage.name} | {stage.status} | {stage.duration_s:.2f}s |")
        lines.extend(
            [
                "",
                "## Metrics",
                "",
                "```json",
                json.dumps(stats, indent=2, sort_keys=True, default=str),
                "```",
                "",
            ]
        )
        return "\n".join(lines)

    def _hermes_md(self, topics: list[dict[str, Any]]) -> str:
        tokens = [
            int(row.get("tokens_used", 0) or 0)
            for row in topics
            if int(row.get("tokens_used", 0) or 0) > 0
        ]
        models = sorted(
            {
                str(row.get("hermes_model", ""))
                for row in topics
                if row.get("hermes_model")
            }
        )
        direct = sum(bool(row.get("hermes_lean_compiles")) for row in topics)
        lines = [
            "# Hermes results",
            "",
            f"Processed: {len(topics)}",
            f"Successful: {sum(bool(t.get('hermes_success')) for t in topics)}",
            f"Cache hits: {sum(bool(t.get('cache_hit')) for t in topics)}/{len(topics) or 0}",
            f"Mean tokens/topic: {sum(tokens) // len(tokens) if tokens else 0}",
            f"Models used: {', '.join(models) or 'none'}",
            f"Hermes-refined Lean compiled: {direct}/{len(topics) or 0}",
            "",
        ]
        for row in topics:
            lines.extend(
                [
                    f"## {row.get('topic_id', '')}",
                    "",
                    f"- Hermes success: `{row.get('hermes_success', False)}`",
                    f"- Model: `{row.get('hermes_model', '')}`",
                    f"- Verification source: `{row.get('verification_source', 'none')}`",
                    f"- Error: {row.get('error', '') or 'none'}",
                    "",
                    "### Explanation",
                    "",
                    str(row.get("explanation", "") or "(none)"),
                    "",
                    "### Refined Lean source",
                    "",
                    "```lean",
                    str(row.get("refined_lean_sketch", "") or ""),
                    "```",
                    "",
                ]
            )
        return "\n".join(lines)

    def _topic_md(self, row: dict[str, Any]) -> str:
        warnings = row.get("lean_warnings", [])
        warning_lines = (
            [f"- {warning}" for warning in warnings]
            if isinstance(warnings, list) and warnings
            else ["- none"]
        )
        return "\n".join(
            [
                f"# Topic {row.get('topic_id', '')}",
                "",
                "## Hermes Validation",
                "",
                f"- Success: `{row.get('hermes_success', False)}`",
                f"- Cache hit: `{row.get('cache_hit', False)}`",
                f"- Model: `{row.get('hermes_model', '') or 'none'}`",
                f"- Hermes-refined Lean compiled: `{row.get('hermes_lean_compiles', False)}`",
                f"- Final verification source: `{row.get('verification_source', 'none')}`",
                f"- Final Lean compiled cleanly: `{bool(row.get('lean_compiles')) and not bool(row.get('lean_has_sorry')) and not bool(row.get('lean_warnings'))}`",
                f"- Lean warnings: `{len(row.get('lean_warnings', [])) if isinstance(row.get('lean_warnings', []), list) else 'invalid'}`",
                f"- Error: {row.get('error', '') or 'none'}",
                "",
                "### Lean warning evidence",
                "",
                *warning_lines,
                "",
                "## Explanation",
                "",
                str(row.get("explanation", "") or "(no explanation recorded)"),
                "",
                "## Refined Lean source",
                "",
                "```lean",
                str(row.get("refined_lean_sketch", "") or ""),
                "```",
                "",
            ]
        )

    def _lean_md(self, stats: dict[str, Any]) -> str:
        return (
            "# Lean results\n\n```json\n"
            + json.dumps(stats, indent=2, sort_keys=True, default=str)
            + "\n```\n"
        )

    def _validation_md(self, result: Any) -> str:
        return _render_validation_markdown(_validation_evidence(result))
