"""Typed, fail-closed evidence contracts for publication-facing claims.

Native Lean verification is deliberately separate from a full Hermes/OpenGauss
pipeline receipt.  A clean native receipt establishes only that the selected
canonical sketches compiled without warnings or ``sorry`` against the pinned
toolchain.  Full-run claim readiness remains owned by
``reporter.validate_report_receipt``.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import tempfile
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from fep_lean.catalogue.schema import topic_ids_sha256
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

NATIVE_RECEIPT_SCHEMA_VERSION = 4
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else ""


def _toolchain_snapshot(project_root: Path) -> dict[str, str]:
    root = Path(project_root)
    toolchain_path = root / "lean" / "lean-toolchain"
    lakefile = root / "lean" / "lakefile.lean"
    toolchain = (
        toolchain_path.read_text(encoding="utf-8").strip()
        if toolchain_path.is_file()
        else ""
    )
    mathlib_tag = ""
    if lakefile.is_file():
        match = re.search(r'@\s*"([^"]+)"', lakefile.read_text(encoding="utf-8"))
        if match:
            mathlib_tag = match.group(1)
    return {
        "lean_toolchain": toolchain,
        "mathlib_tag": mathlib_tag,
        "mathlib_revision": resolved_mathlib_revision(root / "lean"),
    }


def _live_topic_ids(project_root: Path) -> tuple[str, ...]:
    from fep_lean.catalogue.topics import FEPTopicCatalogue

    catalogue = FEPTopicCatalogue.from_yaml(
        Path(project_root) / "config" / "topics.yaml"
    )
    return tuple(topic.id for topic in catalogue.topics)


def _source_snapshot(
    project_root: Path, *, live_topic_ids: Sequence[str] | None = None
) -> dict[str, Any]:
    root = Path(project_root)
    roster = (
        tuple(live_topic_ids) if live_topic_ids is not None else _live_topic_ids(root)
    )
    return {
        "owner_manifest_version": OWNER_MANIFEST_VERSION,
        "source_digest": report_source_digest(root),
        "config_digest": report_config_digest(root),
        "catalogue_sha256": _sha256(root / "config" / "topics.yaml"),
        "catalogue_sources_sha256": catalogue_sources_digest(root),
        "roster_sha256": topic_ids_sha256(roster),
        "live_catalogue_topics": len(roster),
        **_toolchain_snapshot(root),
    }


def _result_row(result: Any) -> dict[str, Any]:
    raw = result.as_dict() if hasattr(result, "as_dict") else dict(result)
    warnings = raw.get("warnings", [])
    errors = raw.get("errors", [])
    compiles = raw.get("compiles", False)
    has_sorry = raw.get("has_sorry", raw.get("lean_has_sorry", False))
    if not isinstance(compiles, bool) or not isinstance(has_sorry, bool):
        raise TypeError("native result compiles and has_sorry must be booleans")
    # ``has_sorry`` is a per-topic boolean; ``sorry_occurrences`` is the count of
    # admitted proofs in that topic. Summing the boolean answers "how many
    # topics admit anything", never "how many uses of ``sorry``". A receipt
    # written before this field existed derives it from the boolean.
    raw_occurrences = raw.get("sorry_occurrences")
    sorry_occurrences = (
        int(raw_occurrences)
        if isinstance(raw_occurrences, int) and not isinstance(raw_occurrences, bool)
        else int(has_sorry)
    )
    row = {
        "topic_id": str(raw.get("topic_id", "")),
        "compiles": compiles,
        "has_sorry": has_sorry,
        "sorry_occurrences": sorry_occurrences,
        "warnings": list(warnings) if isinstance(warnings, list) else [],
        "errors": list(errors) if isinstance(errors, list) else [],
        "duration_s": float(raw.get("duration_s", 0.0) or 0.0),
        "lean_version": str(raw.get("lean_version", "")),
    }
    return row


def build_native_lean_receipt(
    project_root: Path,
    requested_topic_ids: Sequence[str],
    results: Iterable[Any],
) -> dict[str, Any]:
    """Build a serializable native verification receipt from compiler results."""
    selected = list(requested_topic_ids)
    live_topic_ids = _live_topic_ids(Path(project_root))
    if len(selected) != len(set(selected)):
        raise ValueError("requested native topic IDs must be unique")
    canonical_selection = [
        topic_id for topic_id in live_topic_ids if topic_id in selected
    ]
    if selected != canonical_selection:
        raise ValueError(
            "requested native topic IDs must be known and preserve live catalogue order"
        )
    rows = [_result_row(result) for result in results]
    source = _source_snapshot(Path(project_root), live_topic_ids=live_topic_ids)
    warning_count = sum(len(row["warnings"]) for row in rows)
    sorry_count = sum(bool(row["has_sorry"]) for row in rows)
    sorry_occurrences = sum(int(row["sorry_occurrences"]) for row in rows)
    verified_topics = sum(
        bool(row["compiles"])
        and not bool(row["has_sorry"])
        and not row["warnings"]
        and not row["errors"]
        for row in rows
    )
    row_versions = [row["lean_version"] for row in rows]
    version_evidence_valid = (
        bool(row_versions)
        and len(set(row_versions)) == 1
        and all(
            lean_version_matches_pin(version, source["lean_toolchain"])
            for version in row_versions
        )
    )
    complete = (
        bool(selected)
        and [row["topic_id"] for row in rows] == selected
        and verified_topics == len(selected)
        and version_evidence_valid
    )
    return {
        "schema_version": NATIVE_RECEIPT_SCHEMA_VERSION,
        "kind": "native-lean",
        "mode": "lean-only",
        "complete": complete,
        "requested_topic_ids": selected,
        "selected_topics": len(selected),
        "verified_topics": verified_topics,
        "warning_count": warning_count,
        "sorry_count": sorry_count,
        "sorry_occurrences": sorry_occurrences,
        "duration_s": round(sum(float(row["duration_s"]) for row in rows), 3),
        **source,
        "lean_version": row_versions[0] if version_evidence_valid else "",
        "results": rows,
    }


def write_native_lean_receipt(path: Path, payload: Mapping[str, Any]) -> Path:
    """Atomically persist a native receipt without leaving a partial JSON file."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, raw_path = tempfile.mkstemp(
        prefix=f".{destination.name}.", dir=destination.parent
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(dict(payload), handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(raw_path, destination)
    finally:
        if os.path.exists(raw_path):
            os.unlink(raw_path)
    return destination


def validate_native_lean_receipt(
    path: Path,
    *,
    project_root: Path | None = None,
) -> dict[str, Any]:
    """Validate a receipt and independently derive native claim readiness."""
    receipt = Path(path)
    errors: list[str] = []
    try:
        payload = json.loads(receipt.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return {
            "status": "error",
            "valid": False,
            "native_claim_ready": False,
            "source_bound": False,
            "receipt": str(receipt),
            "live_catalogue_topics": 0,
            "selected_topics": 0,
            "verified_topics": 0,
            "warning_count": 0,
            "sorry_count": 0,
            "sorry_occurrences": 0,
            "errors": [f"cannot read native receipt: {exc}"],
        }
    if not isinstance(payload, dict):
        errors.append("native receipt must contain a JSON object")
        payload = {}
    if payload.get("schema_version") != NATIVE_RECEIPT_SCHEMA_VERSION:
        errors.append(
            f"native receipt schema_version must be {NATIVE_RECEIPT_SCHEMA_VERSION}"
        )
    if payload.get("kind") != "native-lean" or payload.get("mode") != "lean-only":
        errors.append("native receipt kind/mode contract is invalid")

    selected_raw = payload.get("requested_topic_ids", [])
    selected = selected_raw if isinstance(selected_raw, list) else []
    if not all(isinstance(topic_id, str) for topic_id in selected):
        errors.append("requested_topic_ids must be a list of strings")
        selected = []
    if len(set(selected)) != len(selected):
        errors.append("requested_topic_ids contains duplicates")
    rows_raw = payload.get("results", [])
    rows = (
        rows_raw
        if isinstance(rows_raw, list) and all(isinstance(row, dict) for row in rows_raw)
        else []
    )
    if rows_raw != rows:
        errors.append("results must be a list of objects")
    result_ids = [str(row.get("topic_id", "")) for row in rows]
    if result_ids != selected:
        errors.append("result topic IDs do not exactly match the requested roster")

    warning_count = 0
    sorry_count = 0
    sorry_occurrences = 0
    verified_topics = 0
    row_versions: list[str] = []
    row_duration_total = 0.0
    for row in rows:
        warnings = row.get("warnings")
        if not isinstance(warnings, list) or not all(
            isinstance(warning, str) and warning for warning in warnings
        ):
            errors.append(
                f"{row.get('topic_id', '')}: warnings must be a list of non-empty strings"
            )
            warnings = []
        row_errors = row.get("errors")
        if not isinstance(row_errors, list) or not all(
            isinstance(error, str) and error for error in row_errors
        ):
            errors.append(
                f"{row.get('topic_id', '')}: errors must be a list of non-empty strings"
            )
            row_errors = []
        duration = row.get("duration_s")
        if (
            not isinstance(duration, (int, float))
            or isinstance(duration, bool)
            or not math.isfinite(float(duration))
            or float(duration) < 0
        ):
            errors.append(
                f"{row.get('topic_id', '')}: duration_s must be a finite non-negative number"
            )
        else:
            row_duration_total += float(duration)
        warning_count += len(warnings)
        has_sorry = row.get("has_sorry")
        compiles = row.get("compiles")
        if not isinstance(has_sorry, bool) or not isinstance(compiles, bool):
            errors.append(
                f"{row.get('topic_id', '')}: compiles and has_sorry must be booleans"
            )
            continue
        sorry_count += has_sorry
        raw_occurrences = row.get("sorry_occurrences")
        sorry_occurrences += (
            int(raw_occurrences)
            if isinstance(raw_occurrences, int)
            and not isinstance(raw_occurrences, bool)
            else int(has_sorry)
        )
        verified_topics += (
            compiles and not has_sorry and not warnings and not row_errors
        )
        lean_version = row.get("lean_version")
        if (
            not isinstance(lean_version, str)
            or actual_lean_semver(lean_version) is None
        ):
            errors.append(
                f"{row.get('topic_id', '')}: lean_version must be actual compiler version output"
            )
        else:
            row_versions.append(lean_version)

    toolchain = payload.get("lean_toolchain")
    if not isinstance(toolchain, str) or pinned_lean_semver(toolchain) is None:
        errors.append("lean_toolchain must identify a pinned Lean semantic version")
        toolchain = ""
    versions_uniform = len(row_versions) == len(rows) and len(set(row_versions)) == 1
    if row_versions and len(set(row_versions)) != 1:
        errors.append("result lean_version values must be uniform")
    versions_match_pin = versions_uniform and all(
        lean_version_matches_pin(version, toolchain) for version in row_versions
    )
    if row_versions and not versions_match_pin:
        errors.append("result lean_version values do not match lean_toolchain")
    recorded_lean_version = row_versions[0] if versions_uniform else ""
    if payload.get("lean_version") != recorded_lean_version:
        errors.append("lean_version disagrees with receipt rows")

    mathlib_tag = payload.get("mathlib_tag")
    if not isinstance(mathlib_tag, str) or not re.fullmatch(
        r"v\d+\.\d+\.\d+", mathlib_tag
    ):
        errors.append("mathlib_tag must identify a pinned semantic version")
    elif toolchain and mathlib_tag.removeprefix("v") != pinned_lean_semver(toolchain):
        errors.append("mathlib_tag does not match lean_toolchain")
    mathlib_revision = payload.get("mathlib_revision")
    if not isinstance(mathlib_revision, str) or not re.fullmatch(
        r"[0-9a-f]{40}", mathlib_revision
    ):
        errors.append("mathlib_revision must be a 40-character lowercase Git revision")

    for field, actual in (
        ("selected_topics", len(selected)),
        ("verified_topics", verified_topics),
        ("warning_count", warning_count),
        ("sorry_count", sorry_count),
    ):
        if payload.get(field) != actual:
            errors.append(f"{field} disagrees with receipt rows")
    declared_occurrences = payload.get("sorry_occurrences")
    if declared_occurrences is not None and declared_occurrences != sorry_occurrences:
        errors.append("sorry_occurrences disagrees with receipt rows")
    expected_complete = (
        bool(selected) and verified_topics == len(selected) and versions_match_pin
    )
    if payload.get("complete") is not expected_complete:
        errors.append("complete disagrees with receipt rows")

    total_duration = payload.get("duration_s")
    if (
        not isinstance(total_duration, (int, float))
        or isinstance(total_duration, bool)
        or not math.isfinite(float(total_duration))
        or float(total_duration) < 0
    ):
        errors.append("duration_s must be a finite non-negative number")
        validated_duration = 0.0
    else:
        validated_duration = float(total_duration)
        if validated_duration != round(row_duration_total, 3):
            errors.append("duration_s disagrees with receipt rows")

    if payload.get("owner_manifest_version") != OWNER_MANIFEST_VERSION:
        errors.append(
            "native receipt owner_manifest_version does not match the canonical "
            f"owner roster version {OWNER_MANIFEST_VERSION}"
        )
    for digest_field in (
        "source_digest",
        "config_digest",
        "catalogue_sha256",
        "catalogue_sources_sha256",
        "roster_sha256",
    ):
        if not isinstance(payload.get(digest_field), str) or not _SHA256_RE.fullmatch(
            str(payload.get(digest_field, ""))
        ):
            errors.append(f"{digest_field} must be a lowercase SHA-256 digest")

    live_catalogue_topics = payload.get("live_catalogue_topics")
    if type(live_catalogue_topics) is not int or live_catalogue_topics <= 0:
        errors.append("live_catalogue_topics must be a positive integer")
        live_catalogue_topics = 0

    source_bound = False
    live_topic_ids: tuple[str, ...] = ()
    if project_root is not None:
        live_root = Path(project_root).resolve()
        owner_errors = report_owner_errors(live_root)
        errors.extend(f"live source binding failed: {error}" for error in owner_errors)
        catalogue_bound = False
        try:
            from fep_lean.catalogue.topics import FEPTopicCatalogue

            catalogue = FEPTopicCatalogue.from_yaml(
                live_root / "config" / "topics.yaml"
            )
        except (OSError, TypeError, ValueError) as exc:
            errors.append(f"live catalogue cannot be loaded: {exc}")
        else:
            live_topic_ids = tuple(topic.id for topic in catalogue.topics)
            catalogue_bound = payload.get("live_catalogue_topics") == len(
                live_topic_ids
            ) and payload.get("roster_sha256") == topic_ids_sha256(live_topic_ids)
            if not catalogue_bound:
                errors.append(
                    "receipt live roster fields do not match the canonical catalogue"
                )

        live = _source_snapshot(live_root, live_topic_ids=live_topic_ids)
        snapshot_matches = True
        for field, value in live.items():
            if payload.get(field) != value:
                errors.append(f"{field} does not match the live source tree")
                snapshot_matches = False
        source_bound = not owner_errors and catalogue_bound and snapshot_matches

    full_catalogue = bool(live_topic_ids) and tuple(selected) == live_topic_ids
    native_claim_ready = (
        not errors
        and source_bound
        and full_catalogue
        and expected_complete
        and verified_topics == live_catalogue_topics
        and warning_count == 0
        and sorry_count == 0
    )
    return {
        "status": "ok" if not errors else "error",
        "valid": not errors,
        "native_claim_ready": native_claim_ready,
        "source_bound": source_bound,
        "receipt": str(receipt),
        "live_catalogue_topics": live_catalogue_topics,
        "selected_topics": len(selected),
        "verified_topics": verified_topics,
        "warning_count": warning_count,
        "sorry_count": sorry_count,
        "sorry_occurrences": sorry_occurrences,
        "duration_s": validated_duration,
        "lean_version": recorded_lean_version,
        "lean_toolchain": str(payload.get("lean_toolchain", "")),
        "mathlib_tag": str(payload.get("mathlib_tag", "")),
        "mathlib_revision": str(payload.get("mathlib_revision", "")),
        "errors": errors,
    }


def latest_claim_ready_full_report(
    project_root: Path,
    *,
    output_root: Path | None = None,
) -> Path | None:
    """Return the newest independently validated full-mode report, if any.

    Historical report trees can be large.  Reject summaries whose versioned
    owner or live source/configuration digests cannot possibly bind this
    checkout before invoking the full artifact validator.  A candidate that
    survives this cheap filter still passes the complete fail-closed receipt
    validation; the filter can only exclude reports, never promote one.
    """
    from fep_lean.output.reporter import validate_report_receipt

    root = Path(project_root)
    reports = (
        Path(output_root) if output_root is not None else root / "output"
    ) / "reports"
    live_identity = {
        "owner_manifest_version": OWNER_MANIFEST_VERSION,
        "source_digest": report_source_digest(root),
        "config_digest": report_config_digest(root),
        "catalogue_sources_sha256": catalogue_sources_digest(root),
    }
    # run_id directory names embed microsecond timestamps, so name order is
    # the deterministic recency order; mtime is environment-dependent.
    summary_paths = sorted(
        reports.glob("*/summary.json"),
        key=lambda path: path.parent.name,
        reverse=True,
    )
    for summary_path in summary_paths:
        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        if not isinstance(summary, dict) or any(
            summary.get(key) != value for key, value in live_identity.items()
        ):
            continue
        report_root = summary_path.parent
        validation = validate_report_receipt(report_root, project_root=root)
        if validation.get("claim_ready") is True:
            return report_root
    return None
