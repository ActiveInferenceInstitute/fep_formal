"""Validated novelty ledger for catalog rows beyond the original baseline."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from fep_lean._paths import FepLeanError
from fep_lean.lean_source import lean_code_without_comments

_TOPIC_ID_RE = re.compile(r"^fep-(\d{3})$")
_BRIDGE_RE = re.compile(
    r"^FEPComposed\.[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)*$"
)
_DOCUMENT_FIELDS = frozenset({"schema_version", "baseline_last_id", "topics"})
_RECORD_FIELDS = frozenset(
    {
        "id",
        "nearest_topics",
        "new_invariant",
        "carrier_delta",
        "required_bridge",
    }
)


class NoveltyValidationError(ValueError, FepLeanError):
    """Raised when an expansion row lacks a reviewable mathematical delta."""


@dataclass(frozen=True)
class FormalismNoveltyRecord:
    """One new topic's nearest neighbors, delta, and compiled bridge obligation."""

    id: str
    nearest_topics: tuple[str, ...]
    new_invariant: str
    carrier_delta: str
    required_bridge: str


@dataclass(frozen=True)
class FormalismNoveltyLedger:
    """Complete ordered novelty review for the post-baseline roster tail."""

    schema_version: int
    baseline_last_id: str
    records: tuple[FormalismNoveltyRecord, ...]

    @property
    def by_topic_id(self) -> dict[str, FormalismNoveltyRecord]:
        """Return records indexed by stable topic ID."""
        return {record.id: record for record in self.records}


def _topic_number(value: object, owner: str) -> int:
    if not isinstance(value, str) or (match := _TOPIC_ID_RE.fullmatch(value)) is None:
        raise NoveltyValidationError(f"{owner} must be a canonical fep-NNN ID")
    return int(match.group(1))


def _exact_fields(row: Mapping[str, Any], expected: frozenset[str], owner: str) -> None:
    missing = expected - set(row)
    unknown = set(row) - expected
    if missing or unknown:
        details: list[str] = []
        if missing:
            details.append("missing " + ", ".join(sorted(missing)))
        if unknown:
            details.append("unknown " + ", ".join(sorted(unknown)))
        raise NoveltyValidationError(f"{owner}: {'; '.join(details)}")


def _required_text(row: Mapping[str, Any], field: str, owner: str) -> str:
    value = row.get(field)
    if not isinstance(value, str) or not value.strip():
        raise NoveltyValidationError(f"{owner}: {field} must be a non-empty string")
    return value.strip()


def load_formalism_novelty(
    path: Path,
    roster_ids: Sequence[str],
    *,
    composed_sources: Mapping[str, str],
) -> FormalismNoveltyLedger:
    """Load the expansion tail and require unique endpoint-using bridges."""
    try:
        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise NoveltyValidationError(
            f"cannot read novelty ledger {path}: {exc}"
        ) from exc
    if not isinstance(raw, dict):
        raise NoveltyValidationError("formalism novelty ledger must be a YAML object")
    _exact_fields(raw, _DOCUMENT_FIELDS, "formalism novelty ledger")
    if raw.get("schema_version") != 1:
        raise NoveltyValidationError("formalism novelty schema_version must be 1")

    roster = tuple(roster_ids)
    if not roster or len(roster) != len(set(roster)):
        raise NoveltyValidationError("catalog roster must be non-empty and unique")
    for index, topic_id in enumerate(roster, 1):
        if _topic_number(topic_id, "catalog roster ID") != index:
            raise NoveltyValidationError(
                "catalog roster must be the ordered fep-001 interval"
            )

    baseline_last_id = _required_text(
        raw, "baseline_last_id", "formalism novelty ledger"
    )
    baseline_number = _topic_number(baseline_last_id, "baseline_last_id")
    if baseline_last_id not in roster:
        raise NoveltyValidationError("baseline_last_id must occur in the live roster")
    expected_ids = roster[baseline_number:]

    raw_topics = raw.get("topics")
    if not isinstance(raw_topics, list):
        raise NoveltyValidationError("formalism novelty topics must be a list")
    actual_ids = tuple(
        row.get("id") if isinstance(row, dict) else None for row in raw_topics
    )
    if actual_ids != expected_ids:
        raise NoveltyValidationError(
            "formalism novelty rows must exactly match the ordered expansion tail"
        )

    records: list[FormalismNoveltyRecord] = []
    used_bridges: set[str] = set()
    for raw_row in raw_topics:
        if not isinstance(raw_row, dict):
            raise NoveltyValidationError(
                "every formalism novelty row must be an object"
            )
        topic_id = _required_text(raw_row, "id", "formalism novelty row")
        _exact_fields(raw_row, _RECORD_FIELDS, topic_id)
        topic_number = _topic_number(topic_id, f"{topic_id}.id")

        raw_nearest = raw_row.get("nearest_topics")
        if (
            not isinstance(raw_nearest, list)
            or not raw_nearest
            or not all(isinstance(value, str) for value in raw_nearest)
        ):
            raise NoveltyValidationError(
                f"{topic_id}: nearest_topics must be a non-empty list of topic IDs"
            )
        nearest_topics = tuple(raw_nearest)
        if len(nearest_topics) != len(set(nearest_topics)):
            raise NoveltyValidationError(
                f"{topic_id}: nearest_topics contains duplicates"
            )
        for nearest in nearest_topics:
            nearest_number = _topic_number(nearest, f"{topic_id}.nearest_topics")
            if nearest not in roster:
                raise NoveltyValidationError(
                    f"{topic_id}: nearest topic {nearest} is absent from the roster"
                )
            if nearest_number >= topic_number:
                raise NoveltyValidationError(
                    f"{topic_id}: every nearest topic must precede the new topic"
                )

        new_invariant = _required_text(raw_row, "new_invariant", topic_id)
        carrier_delta = _required_text(raw_row, "carrier_delta", topic_id)
        required_bridge = _required_text(raw_row, "required_bridge", topic_id)
        if _BRIDGE_RE.fullmatch(required_bridge) is None:
            raise NoveltyValidationError(
                f"{topic_id}: required_bridge must be a qualified FEPComposed declaration"
            )
        raw_source = composed_sources.get(required_bridge)
        if raw_source is None:
            raise NoveltyValidationError(
                f"{topic_id}: required bridge {required_bridge} does not resolve"
            )
        source = lean_code_without_comments(raw_source)
        if required_bridge in used_bridges:
            raise NoveltyValidationError(
                f"{topic_id}: every novelty row must have a unique required_bridge"
            )
        topic_fragment = f"fep_fep{topic_id.removeprefix('fep-')}."
        if topic_fragment not in source:
            raise NoveltyValidationError(
                f"{topic_id}: required bridge does not use the new-topic endpoint"
            )
        nearest_fragments = tuple(
            f"fep_fep{nearest.removeprefix('fep-')}." for nearest in nearest_topics
        )
        if not any(fragment in source for fragment in nearest_fragments):
            raise NoveltyValidationError(
                f"{topic_id}: required bridge does not use a declared nearest-topic endpoint"
            )
        used_bridges.add(required_bridge)
        records.append(
            FormalismNoveltyRecord(
                id=topic_id,
                nearest_topics=nearest_topics,
                new_invariant=new_invariant,
                carrier_delta=carrier_delta,
                required_bridge=required_bridge,
            )
        )
    return FormalismNoveltyLedger(
        schema_version=1,
        baseline_last_id=baseline_last_id,
        records=tuple(records),
    )


__all__ = [
    "FormalismNoveltyLedger",
    "FormalismNoveltyRecord",
    "NoveltyValidationError",
    "load_formalism_novelty",
]
