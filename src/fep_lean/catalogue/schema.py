"""Typed schema-2 roster seal and static catalogue metadata."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, overload

import yaml

from .semantics import SemanticValidationError

AREAS = frozenset(
    {"FEP", "ActiveInference", "BayesianMechanics", "InfoGeometry", "Thermodynamics"}
)
MATHLIB_STATUSES = frozenset({"real", "partial", "aspirational"})
_TOPIC_ID_RE = re.compile(r"^fep-(\d{3})$")
_FAMILY_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
_DOCUMENT_FIELDS = frozenset({"schema_version", "roster", "families", "topics"})
_ROSTER_FIELDS = frozenset({"first_id", "last_id"})
_TOPIC_FIELDS = frozenset(
    {"id", "title", "area", "family", "mathlib_modules", "mathlib_status"}
)

# The generated catalogue document (config/topics.yaml and the packaged copy)
# carries the metadata fields plus its generated projections; validation
# accepts exactly this set on that document.
GENERATED_TOPIC_FIELDS = _TOPIC_FIELDS | frozenset(
    {
        "primary_theorem",
        "supporting_theorems",
        "boundary_theorems",
        "semantic_disposition",
        "nl",
        "assumption_review",
        "non_vacuity",
        "acceptance_probe",
        "lean_sketch",
        "latex_equations",
    }
)


def topic_ids_sha256(topic_ids: Sequence[str]) -> str:
    """Hash an ordered roster with an unambiguous newline-delimited encoding."""
    return hashlib.sha256(("\n".join(topic_ids) + "\n").encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class RosterSeal:
    """Inclusive stable-ID interval from which the ordered roster is derived."""

    first_id: str
    last_id: str

    @property
    def topic_ids(self) -> tuple[str, ...]:
        first = _topic_number(self.first_id, "roster.first_id")
        last = _topic_number(self.last_id, "roster.last_id")
        if first < 1:
            raise SemanticValidationError("roster.first_id must start at fep-001")
        if first > last:
            raise SemanticValidationError(
                "roster.first_id must not follow roster.last_id"
            )
        return tuple(f"fep-{index:03d}" for index in range(first, last + 1))

    @property
    def sha256(self) -> str:
        """Return the digest of the exact ordered roster."""
        return topic_ids_sha256(self.topic_ids)


@dataclass(frozen=True)
class CatalogueMetadata:
    """Maintained non-semantic metadata for one stable topic identifier."""

    id: str
    title: str
    area: str
    family: str
    mathlib_modules: tuple[str, ...]
    mathlib_status: str


@dataclass(frozen=True)
class CatalogueMetadataManifest(Sequence[CatalogueMetadata]):
    """Complete schema-2 metadata document with its sole roster seal."""

    schema_version: int
    roster: RosterSeal
    families: tuple[str, ...]
    records: tuple[CatalogueMetadata, ...]

    @property
    def topic_ids(self) -> tuple[str, ...]:
        """Return the exact IDs derived only from the roster interval."""
        return self.roster.topic_ids

    @property
    def by_topic_id(self) -> dict[str, CatalogueMetadata]:
        """Return maintained rows indexed by stable topic ID."""
        return {record.id: record for record in self.records}

    def __len__(self) -> int:
        return len(self.records)

    def __iter__(self) -> Iterator[CatalogueMetadata]:
        return iter(self.records)

    @overload
    def __getitem__(self, index: int) -> CatalogueMetadata: ...

    @overload
    def __getitem__(self, index: slice) -> tuple[CatalogueMetadata, ...]: ...

    def __getitem__(
        self, index: int | slice
    ) -> CatalogueMetadata | tuple[CatalogueMetadata, ...]:
        return self.records[index]


def _required_text(row: Mapping[str, Any], field: str, owner: str) -> str:
    value = row.get(field)
    if not isinstance(value, str) or not value.strip():
        raise SemanticValidationError(f"{owner}: {field} must be a non-empty string")
    return value.strip()


def _topic_number(value: object, owner: str) -> int:
    if not isinstance(value, str) or (match := _TOPIC_ID_RE.fullmatch(value)) is None:
        raise SemanticValidationError(f"{owner} must be a canonical fep-NNN ID")
    return int(match.group(1))


def _reject_field_drift(
    row: Mapping[str, Any], expected: frozenset[str], owner: str
) -> None:
    unknown = set(row) - expected
    missing = expected - set(row)
    details = []
    if missing:
        details.append(f"missing {', '.join(sorted(missing))}")
    if unknown:
        details.append(f"unknown {', '.join(sorted(unknown))}")
    if details:
        raise SemanticValidationError(f"{owner}: {'; '.join(details)}")


def load_catalogue_metadata(
    path: Path, row_fields: frozenset[str] | None = None
) -> CatalogueMetadataManifest:
    """Load metadata and reject any schema, roster, vocabulary, or row drift.

    ``row_fields`` selects the accepted per-row field set: the maintained
    metadata document by default, the generated catalogue's superset when
    the caller passes ``GENERATED_TOPIC_FIELDS``.
    """
    accepted_topic_fields = (
        _TOPIC_FIELDS if row_fields is None else frozenset(row_fields)
    )
    try:
        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise SemanticValidationError(
            f"cannot read catalogue metadata {path}: {exc}"
        ) from exc
    if not isinstance(raw, dict):
        raise SemanticValidationError("catalogue metadata must be a YAML object")
    _reject_field_drift(raw, _DOCUMENT_FIELDS, "catalogue metadata")
    if raw.get("schema_version") != 2:
        raise SemanticValidationError("catalogue metadata schema_version must be 2")

    roster_raw = raw.get("roster")
    if not isinstance(roster_raw, dict):
        raise SemanticValidationError("catalogue metadata roster must be an object")
    _reject_field_drift(roster_raw, _ROSTER_FIELDS, "catalogue metadata roster")
    roster = RosterSeal(
        first_id=_required_text(roster_raw, "first_id", "roster"),
        last_id=_required_text(roster_raw, "last_id", "roster"),
    )
    topic_ids = roster.topic_ids

    raw_families = raw.get("families")
    if not isinstance(raw_families, list) or not raw_families:
        raise SemanticValidationError(
            "catalogue metadata families must be a non-empty list"
        )
    if not all(
        isinstance(family, str) and _FAMILY_RE.fullmatch(family)
        for family in raw_families
    ):
        raise SemanticValidationError(
            "catalogue metadata families must be canonical kebab-case strings"
        )
    families = tuple(raw_families)
    if len(families) != len(set(families)):
        raise SemanticValidationError("catalogue metadata families must be unique")

    rows = raw.get("topics")
    if not isinstance(rows, list):
        raise SemanticValidationError("catalogue metadata topics must be a list")
    ids = tuple(row.get("id") if isinstance(row, dict) else None for row in rows)
    if ids != topic_ids:
        raise SemanticValidationError(
            "catalogue metadata rows must exactly match the sealed roster in order"
        )

    records: list[CatalogueMetadata] = []
    for raw_row in rows:
        if not isinstance(raw_row, dict):
            raise SemanticValidationError(
                "every catalogue metadata row must be an object"
            )
        topic_id = _required_text(raw_row, "id", "topic")
        _reject_field_drift(raw_row, accepted_topic_fields, topic_id)
        area = _required_text(raw_row, "area", topic_id)
        if area not in AREAS:
            raise SemanticValidationError(f"{topic_id}: unsupported area {area!r}")
        family = _required_text(raw_row, "family", topic_id)
        if family not in families:
            raise SemanticValidationError(
                f"{topic_id}: family {family!r} is absent from the ordered vocabulary"
            )
        raw_modules = raw_row.get("mathlib_modules")
        if (
            not isinstance(raw_modules, list)
            or not raw_modules
            or not all(
                isinstance(module, str) and module.strip() for module in raw_modules
            )
        ):
            raise SemanticValidationError(
                f"{topic_id}: mathlib_modules must be a non-empty list of strings"
            )
        modules = tuple(module.strip() for module in raw_modules)
        if len(modules) != len(set(modules)):
            raise SemanticValidationError(
                f"{topic_id}: mathlib_modules must not contain duplicates"
            )
        status = _required_text(raw_row, "mathlib_status", topic_id).lower()
        if status not in MATHLIB_STATUSES:
            raise SemanticValidationError(
                f"{topic_id}: unsupported mathlib_status {status!r}"
            )
        records.append(
            CatalogueMetadata(
                id=topic_id,
                title=_required_text(raw_row, "title", topic_id),
                area=area,
                family=family,
                mathlib_modules=modules,
                mathlib_status=status,
            )
        )
    return CatalogueMetadataManifest(
        schema_version=2,
        roster=roster,
        families=families,
        records=tuple(records),
    )


__all__ = [
    "AREAS",
    "GENERATED_TOPIC_FIELDS",
    "MATHLIB_STATUSES",
    "CatalogueMetadata",
    "CatalogueMetadataManifest",
    "RosterSeal",
    "load_catalogue_metadata",
    "topic_ids_sha256",
]
