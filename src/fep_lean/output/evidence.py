"""Typed, fail-closed evidence contracts for publication-facing claims.

Native Lean verification is deliberately separate from a full Hermes/OpenGauss
pipeline receipt.  A clean native receipt establishes only that the selected
canonical sketches compiled without warnings or ``sorry`` against the pinned
toolchain.  Full-run claim readiness remains owned by
``reporter.validate_report_receipt``.
"""

from __future__ import annotations

import json
import math
import os
import re
import tempfile
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from fep_lean.catalogue.schema import topic_ids_sha256
from fep_lean.output.fsutil import sha256_file
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
    toolchain_identity,
)

if TYPE_CHECKING:
    from fep_lean.catalogue.topics import FEPTopicCatalogue

NATIVE_RECEIPT_SCHEMA_VERSION = 4
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _toolchain_snapshot(project_root: Path) -> dict[str, str]:
    """Return the validated Lean/Mathlib identity of the Lean workspace."""
    return toolchain_identity(Path(project_root) / "lean")


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
        "catalogue_sha256": sha256_file(root / "config" / "topics.yaml"),
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


STATUS_BOUNDARY = (
    "status composes existing read-only checks; exit 0 means the report "
    "composed, never that the evidence is current. Each section's state and "
    "boundary are the authority. Nothing here compiles Lean, runs Hermes or "
    "OpenGauss, executes the test suite, writes bytes, or repairs drift."
)


@dataclass(frozen=True)
class SectionReport:
    """One evidence-currency section with its explicit capability boundary."""

    name: str
    state: str
    findings: tuple[str, ...]
    composes: tuple[str, ...]
    boundary: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "state": self.state,
            "findings": list(self.findings),
            "composes": list(self.composes),
            "boundary": self.boundary,
        }


_PUBLICATION_PLANES = (
    "catalogue_build_products",
    "render_receipt_freshness",
    "bridge_source_pin",
    "native_verification_receipt",
    "formalism_audit_receipt",
    "python_acceptance_receipt",
    "browser_acceptance_receipt",
    "publication_inputs",
    "publication_bundle",
    "input_stability",
)


@dataclass(frozen=True)
class PublicationReadinessReport:
    """Static readiness inventory; runtime and archive gates stay explicit."""

    sections: tuple[SectionReport, ...]
    runtime_checks_performed: bool = False
    bundle_parity_verified: bool = False

    @property
    def claim_ready(self) -> bool:
        return (
            tuple(section.name for section in self.sections) == _PUBLICATION_PLANES
            and all(
                section.state in {"current", "claim_ready"} for section in self.sections
            )
            and self.runtime_checks_performed
            and self.bundle_parity_verified
        )

    @property
    def state(self) -> str:
        if tuple(section.name for section in self.sections) != _PUBLICATION_PLANES:
            return "blocked"
        if any(
            section.state not in {"current", "claim_ready", "unverified"}
            for section in self.sections
        ):
            return "blocked"
        return "claim_ready" if self.claim_ready else "unverified"

    def as_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "claim_ready": self.claim_ready,
            "runtime_checks_performed": self.runtime_checks_performed,
            "bundle_parity_verified": self.bundle_parity_verified,
            "deferred_checks": [
                "fresh canonical Python test collection and executor validation",
                "live browser executable identification and capture replay",
                "deterministic publication rendering and renderer identity validation",
                "two byte-identical bundles and final live-source bundle validation",
            ],
            "boundary": (
                "Static source and receipt checks only. Missing or stale evidence "
                "blocks readiness; successful static checks do not replace fresh "
                "collection, browser replay, deterministic rendering, or bundle "
                "validation. No publication is performed or authorized here."
            ),
            "sections": [section.as_dict() for section in self.sections],
        }


@dataclass(frozen=True)
class StatusReport:
    """Typed ``fep-lean status`` payload: sections, never proof claims."""

    sections: tuple[SectionReport, ...]
    publication_readiness: PublicationReadinessReport | None = None

    @property
    def status(self) -> str:
        """``ok`` when the report composed; section states carry currency."""
        return "ok" if len(self.sections) == 4 else "error"

    def as_dict(self) -> dict[str, Any]:
        # The top-level native_claim_ready flag must agree with the
        # native_verification_receipt section's state: the sections are the
        # authority, and a hardcoded False contradicted a claim_ready section
        # (observed 2026-09-10 after the wave-2 evidence refresh).
        native_ready = any(
            section.name == "native_verification_receipt"
            and section.state == "claim_ready"
            for section in self.sections
        )
        payload = {
            "schema_version": 1,
            "status": self.status,
            "evidence_plane": "evidence currency and provenance",
            "boundary": STATUS_BOUNDARY,
            "native_claim_ready": native_ready,
            "sections": [section.as_dict() for section in self.sections],
        }
        if self.publication_readiness is not None:
            payload["publication_readiness"] = self.publication_readiness.as_dict()
        return payload


RENDER_RECEIPT = Path("docs") / "render-acceptance.json"
NATIVE_RECEIPT = Path("output") / "native-verification.json"


def _readiness_display(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def catalogue_products_section(
    root: Path, catalogue: FEPTopicCatalogue | None = None
) -> SectionReport:
    """Compare offline catalogue build products against their generators."""
    from fep_lean.catalogue.generation import (
        catalogue_projection_drift,
        fep_all_projection_drift,
    )
    from fep_lean.catalogue.topics import FEPTopicCatalogue
    from fep_lean.output.manuscript import (
        build_manuscript_vars,
        manuscript_projection_drift,
    )

    composes = (
        "fep_lean.catalogue.generation.catalogue_projection_drift",
        "fep_lean.catalogue.generation.fep_all_projection_drift",
        "fep_lean.output.manuscript.manuscript_projection_drift",
    )
    boundary = (
        "Compares generated projections byte-for-byte against their canonical "
        "generators. It does not compile Lean, run Hermes or OpenGauss, "
        "execute the test suite, or prove any theorem: current means every "
        "comparison completed and generators and products agree on bytes. "
        "An unavailable comparison is unverified, even if other products match. "
        "Run-local receipt/provider values and checkout stamp values are excluded; "
        "only their mapping shapes are compared. No checkout stamp is captured "
        "or treated as a current fact."
    )
    stale: list[Path] = []
    findings: list[str] = []
    try:
        stale.extend(catalogue_projection_drift(root))
    except (OSError, TypeError, ValueError) as exc:
        findings.append(f"topic catalogue projections unreadable: {exc}")
    try:
        stale.extend(fep_all_projection_drift(root))
    except (OSError, TypeError, ValueError) as exc:
        findings.append(f"aggregate Lean projection unreadable: {exc}")
    try:
        cat = catalogue or FEPTopicCatalogue.from_yaml(root / "config" / "topics.yaml")
        expected_vars = build_manuscript_vars(
            cat,
            root,
            output_root=root / "output",
            cache_test_count=False,
            capture_source_stamp=False,
        )
        stale.extend(
            manuscript_projection_drift(
                root,
                catalogue=cat,
                output_root=root / "output",
                expected_variables=expected_vars,
            )
        )
    except (OSError, TypeError, ValueError) as exc:
        # The test census refuses to run a collection here; a missing cache is
        # the census boundary, not a drift verdict on the manuscript.
        findings.append(f"manuscript projections not compared: {exc}")
    if stale:
        findings.extend(
            f"stale or missing: {_readiness_display(root, path)}" for path in stale
        )
    state = "stale" if stale else "unverified" if findings else "current"
    return SectionReport(
        name="catalogue_build_products",
        state=state,
        findings=tuple(findings),
        composes=composes,
        boundary=boundary,
    )


def render_receipt_section(
    root: Path,
    *,
    receipt_path: Path | None = None,
    manuscript_dir: Path | None = None,
) -> SectionReport:
    from fep_lean.output.render_log import receipt_defects

    receipt = receipt_path or root / RENDER_RECEIPT
    manuscript = manuscript_dir or root / "manuscript"
    composes = (
        "fep_lean.output.render_log.receipt_defects",
        "fep_lean.output.render_log.manuscript_source_digests",
    )
    boundary = (
        "The receipt binds an accepted render to the authored manuscript text "
        "and LaTeX preamble as of that render. It does not re-run the render, "
        "does not cover values a {{token}} resolves to (manuscript projection "
        "drift owns that surface), and says nothing about Lean, Hermes, or "
        "OpenGauss evidence."
    )
    try:
        defects = receipt_defects(receipt, manuscript)
    except (OSError, TypeError, ValueError) as exc:
        state = "error"
        defects = (f"render receipt cannot be compared with live sources: {exc}",)
    else:
        if not receipt.is_file():
            state = "missing"
        elif defects:
            state = "stale"
        else:
            state = "current"
    return SectionReport(
        name="render_receipt_freshness",
        state=state,
        findings=defects,
        composes=composes,
        boundary=boundary,
    )


def bridge_pin_section(root: Path, gnn_root: Path | None = None) -> SectionReport:
    """Report GNN bridge source-pin presence and, when possible, staleness."""
    from fep_lean.bridge import operations
    from fep_lean.bridge.custody import validate_binding

    composes = (
        "fep_lean.bridge.operations.check_sources",
        "fep_lean.bridge.custody.validate_binding",
    )
    pin = root / Path(operations.PIN)
    if not pin.is_file():
        return SectionReport(
            name="bridge_source_pin",
            state="not_pinned",
            findings=(
                "specs/gnn-bridge-w2-source-custody/source-pin.json: not pinned",
            ),
            composes=composes,
            boundary=(
                "No source pin exists, so no bridge evidence is bound to owner "
                "bytes. Pin presence alone establishes nothing about the "
                "current sibling tree: comparing working-tree bytes requires "
                "the explicitly named GNN checkout, and a fresh pin is not "
                "evidence of correctness or of native proof."
            ),
        )
    try:
        data = operations.read_object(pin)
        findings = [
            f"fep_lean commit recorded: {data['fep_lean'].get('commit', '?')}",
            f"gnn commit recorded: {data['gnn'].get('commit', '?')}",
        ]
        errors: list[str]
        if gnn_root is not None:
            errors = operations.check_sources(root, gnn_root, data)
        else:
            fep_entry = data.get("fep_lean")
            owners = fep_entry.get("owners") if isinstance(fep_entry, dict) else None
            if not isinstance(owners, dict):
                errors = ["malformed fep_lean source binding"]
            else:
                errors = validate_binding(
                    root, owners, operations.owner_roster(root, "fep_lean")
                )
                errors = [f"fep_lean: {error}" for error in errors]
            findings.append(
                "gnn owner bytes not compared: pass --gnn-root with the "
                "explicit GNN checkout to validate both sides"
            )
    except (OSError, KeyError, TypeError, ValueError) as exc:
        return SectionReport(
            name="bridge_source_pin",
            state="error",
            findings=(f"unreadable or malformed source pin: {exc}",),
            composes=composes,
            boundary=(
                "A malformed pin is a custody failure, not a stale-but-trusted "
                "reference; re-pin explicitly after reviewing owner changes."
            ),
        )
    findings.extend(errors)
    state = "stale" if errors else "current" if gnn_root is not None else "unverified"
    return SectionReport(
        name="bridge_source_pin",
        state=state,
        findings=tuple(findings),
        composes=composes,
        boundary=(
            "Custody binds owner bytes, not a perpetually refreshed HEAD. "
            "Currency requires comparing both explicitly named working trees. "
            "Without --gnn-root, the GNN comparison remains unverified. It is "
            "not native proof, not semantic review, and not proof that an "
            "older execution artifact was produced by these sources."
        ),
    )


def native_receipt_section(
    root: Path, *, receipt_path: Path | None = None
) -> SectionReport:
    """Read the native verification receipt with its claim boundary."""
    receipt = receipt_path or root / NATIVE_RECEIPT
    composes = ("fep_lean.output.evidence.validate_native_lean_receipt",)
    if not receipt.is_file():
        return SectionReport(
            name="native_verification_receipt",
            state="missing",
            findings=("output/native-verification.json: absent",),
            composes=composes,
            boundary=(
                "No native receipt exists, so no Lean compilation claim is "
                "bound to current sources. Catalogue-mode output must never "
                "be read as Lean evidence."
            ),
        )
    try:
        validation = validate_native_lean_receipt(receipt, project_root=root)
    except (OSError, TypeError, ValueError) as exc:
        return SectionReport(
            name="native_verification_receipt",
            state="error",
            findings=(f"native receipt cannot be compared with live sources: {exc}",),
            composes=composes,
            boundary=(
                "Native source/receipt comparison did not complete. No native "
                "claim readiness is established by an unavailable comparison."
            ),
        )
    findings = [
        f"valid: {validation.get('valid', False)}",
        f"native_claim_ready: {validation.get('native_claim_ready', False)}",
        f"selected topics: {validation.get('selected_topics', 0)}",
        f"verified topics: {validation.get('verified_topics', 0)}",
        f"warnings: {validation.get('warning_count', 0)}",
        f"sorry: {validation.get('sorry_count', 0)}",
    ]
    findings.extend(str(error) for error in validation.get("errors", []))
    state = "claim_ready" if validation.get("native_claim_ready") else "not_claim_ready"
    return SectionReport(
        name="native_verification_receipt",
        state=state,
        findings=tuple(findings),
        composes=composes,
        boundary=(
            "Claim readiness covers exact-source native compilation of the "
            "selected roster at the recorded digests, with zero errors, "
            "warnings, and sorry. It is not a Hermes/OpenGauss full run, not "
            "semantic review of a theorem proxy, and not a proof of the FEP; "
            "compilation of a Lean body never promotes its disposition."
        ),
    )


def _readiness_input_snapshot(
    root: Path, gnn_root: Path | None
) -> tuple[dict[str, str], tuple[str, ...]]:
    from fep_lean.output import release_bundle

    return release_bundle.publication_input_snapshot(root, gnn_root)


def _stored_readiness_section(
    root: Path,
    *,
    name: str,
    receipts: tuple[Path, ...],
    validator: Callable[[Path], tuple[str, ...]],
    owner: str,
    runtime_required: bool = False,
) -> SectionReport:
    """Project one existing validator's defects without relaxing its policy."""
    missing = tuple(
        f"missing: {relative.as_posix()}"
        for relative in receipts
        if not (root / relative).is_file()
    )
    state = "missing" if missing else "current"
    defects = missing
    if not missing:
        try:
            defects = validator(root)
        except (OSError, TypeError, ValueError) as exc:
            state = "error"
            defects = (f"stored evidence cannot be validated: {exc}",)
        else:
            state = (
                "stale" if defects else "unverified" if runtime_required else "current"
            )
    return SectionReport(
        name=name,
        state=state,
        findings=defects,
        composes=(owner,),
        boundary=(
            "Validates stored evidence against canonical source/schema policy "
            "without executing tools. "
            + (
                "Successful static validation remains unverified until its "
                "separate runtime validation completes."
                if runtime_required
                else "Current covers only this receipt's exact evidence plane."
            )
        ),
    )


def _publication_input_errors(root: Path) -> tuple[str, ...]:
    from fep_lean.output import release_bundle

    return release_bundle.inspect_stored_publication_evidence(
        root, "publication_inputs"
    )


def build_status_report(root: Path, gnn_root: Path | None = None) -> StatusReport:
    """Compose compatible currency sections plus static publication readiness."""
    from fep_lean.output import release_bundle

    before, snapshot_errors = _readiness_input_snapshot(root, gnn_root)
    sections = (
        catalogue_products_section(root),
        render_receipt_section(root),
        bridge_pin_section(root, gnn_root),
        native_receipt_section(root),
    )
    readiness = list(sections)
    readiness.extend(
        (
            _stored_readiness_section(
                root,
                name="formalism_audit_receipt",
                receipts=(Path("output/formalism-audit.json"),),
                validator=lambda project: (
                    release_bundle.validate_formalism_audit_receipt(
                        project / "output/formalism-audit.json", project
                    )
                ),
                owner="fep_lean.verification.formalism_audit.validate_formalism_audit_receipt",
            ),
            _stored_readiness_section(
                root,
                name="python_acceptance_receipt",
                receipts=(
                    release_bundle.PYTHON_ACCEPTANCE_RECEIPT,
                    release_bundle.PYTEST_RECEIPT,
                    release_bundle.PYTHON_COVERAGE_RECEIPT,
                ),
                validator=lambda project: (
                    release_bundle.inspect_stored_publication_evidence(
                        project, "python_acceptance_receipt"
                    )
                ),
                owner="fep_lean.output.release_bundle._python_acceptance_receipt_errors",
                runtime_required=True,
            ),
            _stored_readiness_section(
                root,
                name="browser_acceptance_receipt",
                receipts=(release_bundle.BROWSER_RECEIPT,),
                validator=lambda project: (
                    release_bundle.inspect_stored_publication_evidence(
                        project, "browser_acceptance_receipt"
                    )
                ),
                owner="fep_lean.output.release_bundle._browser_receipt_errors",
                runtime_required=True,
            ),
            _stored_readiness_section(
                root,
                name="publication_inputs",
                receipts=(Path("manuscript/manuscript_vars.yaml"),),
                validator=_publication_input_errors,
                owner="fep_lean.output.release_bundle._prerequisites",
                runtime_required=True,
            ),
            SectionReport(
                "publication_bundle",
                "unverified",
                (
                    "Deterministic rendering and archive parity validation are deferred.",
                ),
                ("fep_lean.output.release_bundle.validate_release_bundle",),
                "No archive is built, selected, or validated by status. Final "
                "publication requires two identical builds and live-source validation.",
            ),
        )
    )
    after, after_errors = _readiness_input_snapshot(root, gnn_root)
    stability_errors = (*snapshot_errors, *after_errors)
    if not stability_errors and before != after:
        stability_errors = (
            "Source or evidence inputs changed during status validation.",
        )
    readiness.append(
        SectionReport(
            "input_stability",
            "error" if stability_errors else "current",
            tuple(dict.fromkeys(stability_errors)),
            ("fep_lean.output.release_bundle.publication_input_snapshot",),
            "Compares observed owner/test/manuscript/receipt bytes before and "
            "after checks. This is input stability, never execution or proof evidence.",
        )
    )
    return StatusReport(
        sections=sections,
        publication_readiness=PublicationReadinessReport(tuple(readiness)),
    )


def report_to_json(report: StatusReport) -> str:
    """Serialize the report for the CLI's JSON output convention."""
    return json.dumps(report.as_dict(), indent=2, default=str)
