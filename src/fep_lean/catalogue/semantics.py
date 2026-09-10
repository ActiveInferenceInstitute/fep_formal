"""Typed semantic-maturity records for the formalism catalogue.

``config/theorem_maturity.yaml`` is the maintained authoring source.  This
module owns validation and exposes immutable records to generators, reports,
and manuscript projections so those consumers cannot silently reinterpret the
same fields.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

from fep_lean.lean_source import (
    LEAN_THEOREM_RE,
    lean_code_without_comments,
)


class SemanticValidationError(ValueError):
    """Raised when semantic review data cannot be trusted as a projection input."""


class SemanticDisposition(str, Enum):
    """How closely a compiled statement matches its topic-facing claim."""

    FORMALIZED = "formalized"
    PROXY = "proxy"
    CONDITIONAL_PROXY = "conditional_proxy"
    STRUCTURAL_PROXY = "structural_proxy"
    SCOPE_GAP = "scope_gap"
    ASSUMPTION_GAP = "assumption_gap"


@dataclass(frozen=True)
class TheoremMaturityRecord:
    """Maintained semantic review for one catalogue topic."""

    id: str
    primary_theorem: str
    supporting_theorems: tuple[str, ...]
    boundary_theorems: tuple[str, ...]
    invariant: str
    assumption_review: str
    non_vacuity: str
    acceptance_probe: str
    disposition: SemanticDisposition


@dataclass(frozen=True)
class TheoremMaturityAudit:
    """Validated complete semantic review and its global policy metadata."""

    schema_version: int
    review_date: str
    native_evidence: str
    status_policy: str
    records: tuple[TheoremMaturityRecord, ...]

    @property
    def by_topic_id(self) -> dict[str, TheoremMaturityRecord]:
        """Return the review indexed by its stable topic identifier."""
        return {record.id: record for record in self.records}

    @property
    def disposition_counts(self) -> dict[str, int]:
        """Return deterministic nonzero semantic-disposition totals."""
        counts = Counter(record.disposition.value for record in self.records)
        return dict(sorted(counts.items()))


NATIVE_COMPILE_PHRASE = "native Lean compile"


_REQUIRED_RECORD_FIELDS = (
    "id",
    "primary_theorem",
    "supporting_theorems",
    "boundary_theorems",
    "invariant",
    "assumption_review",
    "non_vacuity",
    "acceptance_probe",
    "disposition",
)
_THEOREM_RE = LEAN_THEOREM_RE


def theorem_names(body: str) -> set[str]:
    """Extract theorem declaration names from one canonical Lean body."""
    return set(_THEOREM_RE.findall(lean_code_without_comments(body)))


def _nonempty_string(row: Mapping[str, Any], field: str, topic_id: str) -> str:
    value = row.get(field)
    if not isinstance(value, str) or not value.strip():
        raise SemanticValidationError(f"{topic_id}: {field} must be a non-empty string")
    return value.strip()


def _theorem_list(row: Mapping[str, Any], field: str, topic_id: str) -> tuple[str, ...]:
    value = row.get(field)
    if not isinstance(value, list) or not all(
        isinstance(name, str) and name.strip() for name in value
    ):
        raise SemanticValidationError(
            f"{topic_id}: {field} must be a list of non-empty theorem names"
        )
    names = tuple(name.strip() for name in value)
    if len(names) != len(set(names)):
        raise SemanticValidationError(f"{topic_id}: {field} contains duplicates")
    return names


def load_theorem_maturity(
    path: Path,
    *,
    bodies: Mapping[str, str] | None = None,
    roster_ids: Sequence[str] | None = None,
) -> TheoremMaturityAudit:
    """Load and strictly validate the complete semantic review."""
    try:
        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise SemanticValidationError(
            f"cannot read theorem maturity audit {path}: {exc}"
        ) from exc
    if not isinstance(raw, dict):
        raise SemanticValidationError("theorem maturity audit must be a YAML object")
    if raw.get("schema_version") != 2:
        raise SemanticValidationError("theorem maturity schema_version must be 2")

    review_date = _nonempty_string(raw, "review_date", "audit")
    native_evidence = _nonempty_string(raw, "native_evidence", "audit")
    status_policy = _nonempty_string(raw, "status_policy", "audit")
    rows = raw.get("topics")
    if not isinstance(rows, list):
        raise SemanticValidationError("topics must be a list")

    if roster_ids is None:
        from .schema import load_catalogue_metadata

        roster_ids = load_catalogue_metadata(
            Path(path).with_name("catalogue_metadata.yaml")
        ).topic_ids
    expected_ids = tuple(roster_ids)
    ids = tuple(row.get("id") if isinstance(row, dict) else None for row in rows)
    if ids != expected_ids:
        raise SemanticValidationError(
            "theorem maturity rows must exactly match the sealed roster in order"
        )

    canonical_bodies = bodies
    if canonical_bodies is None:
        from .registry import BODIES

        canonical_bodies = BODIES

    records: list[TheoremMaturityRecord] = []
    for raw_row in rows:
        if not isinstance(raw_row, dict):
            raise SemanticValidationError("every audit topic must be an object")
        topic_id = _nonempty_string(raw_row, "id", "topic")
        unknown_fields = set(raw_row) - set(_REQUIRED_RECORD_FIELDS)
        missing_fields = set(_REQUIRED_RECORD_FIELDS) - set(raw_row)
        if unknown_fields or missing_fields:
            details = []
            if missing_fields:
                details.append("missing " + ", ".join(sorted(missing_fields)))
            if unknown_fields:
                details.append("unknown " + ", ".join(sorted(unknown_fields)))
            raise SemanticValidationError(f"{topic_id}: {'; '.join(details)}")
        try:
            disposition = SemanticDisposition(
                _nonempty_string(raw_row, "disposition", topic_id)
            )
        except ValueError as exc:
            raise SemanticValidationError(
                f"{topic_id}: unsupported disposition {raw_row.get('disposition')!r}"
            ) from exc
        primary_theorem = _nonempty_string(raw_row, "primary_theorem", topic_id)
        supporting_theorems = _theorem_list(raw_row, "supporting_theorems", topic_id)
        boundary_theorems = _theorem_list(raw_row, "boundary_theorems", topic_id)
        reviewed_declarations = (
            primary_theorem,
            *supporting_theorems,
            *boundary_theorems,
        )
        if len(reviewed_declarations) != len(set(reviewed_declarations)):
            raise SemanticValidationError(
                f"{topic_id}: primary, supporting, and boundary theorem roles overlap"
            )
        body = canonical_bodies.get(topic_id, "")
        if not body:
            raise SemanticValidationError(f"{topic_id}: missing canonical Lean body")
        canonical_theorems = theorem_names(body)
        missing_theorems = sorted(set(reviewed_declarations) - canonical_theorems)
        unreviewed_theorems = sorted(canonical_theorems - set(reviewed_declarations))
        if missing_theorems or unreviewed_theorems:
            raise SemanticValidationError(
                f"{topic_id}: theorem-role closure differs from the canonical body: "
                f"missing={missing_theorems!r} unreviewed={unreviewed_theorems!r}"
            )
        acceptance_probe = _nonempty_string(raw_row, "acceptance_probe", topic_id)
        if NATIVE_COMPILE_PHRASE not in acceptance_probe:
            raise SemanticValidationError(
                f"{topic_id}: acceptance_probe must name a native Lean compile"
            )
        records.append(
            TheoremMaturityRecord(
                id=topic_id,
                primary_theorem=primary_theorem,
                supporting_theorems=supporting_theorems,
                boundary_theorems=boundary_theorems,
                invariant=_nonempty_string(raw_row, "invariant", topic_id),
                assumption_review=_nonempty_string(
                    raw_row, "assumption_review", topic_id
                ),
                non_vacuity=_nonempty_string(raw_row, "non_vacuity", topic_id),
                acceptance_probe=acceptance_probe,
                disposition=disposition,
            )
        )

    return TheoremMaturityAudit(
        schema_version=2,
        review_date=review_date,
        native_evidence=native_evidence,
        status_policy=status_policy,
        records=tuple(records),
    )


def render_proxy_statement(record: TheoremMaturityRecord) -> str:
    """Render claim-calibrated natural language from the maintained review."""
    return (
        f"{record.invariant} Assumption scope: {record.assumption_review} "
        f"Semantic disposition: `{record.disposition.value}`.\n"
    )
