"""Load and summarize the generated FEP topic catalogue.

This is the canonical module for the catalogue data model.
Importable as ``from fep_lean.catalogue.topics import FEPTopicCatalogue``.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any

import yaml

from .schema import (
    AREAS,
    GENERATED_TOPIC_FIELDS,
    MATHLIB_STATUSES,
    RosterSeal,
    load_catalogue_metadata,
)
from .semantics import (
    SemanticDisposition,
    SemanticValidationError,
    theorem_names,
)

_MATURITY_ORDER = ("real", "partial", "aspirational")


class CatalogueValidationError(ValueError):
    """Raised when the catalogue cannot be trusted as a verification input."""


@dataclass(frozen=True)
class TopicEntry:
    """One catalogue row."""

    id: str
    title: str
    area: str
    family: str
    mathlib_modules: tuple[str, ...]
    mathlib_status: str
    primary_theorem: str
    supporting_theorems: tuple[str, ...]
    boundary_theorems: tuple[str, ...]
    semantic_disposition: str
    nl: str
    assumption_review: str
    non_vacuity: str
    acceptance_probe: str
    lean_sketch: str
    latex_equations: tuple[str, ...] = ()

    @property
    def lean_chars(self) -> int:
        """Character count of the Lean sketch (for catalogue metrics)."""
        return len(self.lean_sketch)


class FEPTopicCatalogue:
    """Validated in-memory view of generated checkout or package catalogue data."""

    def __init__(
        self,
        topics: Sequence[TopicEntry],
        source_path: Path,
        roster: RosterSeal,
        families: tuple[str, ...],
    ) -> None:
        """Initialize the sole validating construction path.

        Roster, order, and consistency are asserted here so no unvalidated
        catalogue can exist: every constructor (including ``from_yaml`` and
        ``default``) passes through these checks.
        """
        if not isinstance(roster, RosterSeal):
            raise CatalogueValidationError("catalogue roster must be a RosterSeal")
        if not isinstance(source_path, Path):
            raise CatalogueValidationError("catalogue source_path must be a Path")
        if (
            not isinstance(families, tuple)
            or not families
            or not all(isinstance(family, str) and family for family in families)
            or len(families) != len(set(families))
        ):
            raise CatalogueValidationError(
                "catalogue families must be a non-empty unique tuple of strings"
            )
        entries = tuple(topics)
        if not entries or not all(isinstance(entry, TopicEntry) for entry in entries):
            raise CatalogueValidationError(
                "catalogue topics must be a non-empty sequence of TopicEntry"
            )
        if tuple(entry.id for entry in entries) != roster.topic_ids:
            raise CatalogueValidationError(
                "catalogue rows must exactly match the sealed roster in order"
            )
        for entry in entries:
            if entry.area not in AREAS:
                raise CatalogueValidationError(
                    f"{entry.id}: unsupported area {entry.area!r}"
                )
            if entry.family not in families:
                raise CatalogueValidationError(
                    f"{entry.id}: family is absent from the vocabulary"
                )
            if entry.mathlib_status not in MATHLIB_STATUSES:
                raise CatalogueValidationError(
                    f"{entry.id}: unsupported mathlib_status {entry.mathlib_status!r}"
                )
        self._topics: tuple[TopicEntry, ...] = entries
        self.source_path = source_path
        self.roster = roster
        self.families = families

    @classmethod
    def default(cls) -> FEPTopicCatalogue:
        """Load the generated catalogue bundled with the installed package."""
        return cls.from_yaml(_default_topics_path())

    @classmethod
    def from_yaml(cls, path: Path | None = None) -> FEPTopicCatalogue:
        """Load and validate the complete catalogue from YAML.

        Document, roster, family, and per-row metadata validation is
        delegated to ``schema.load_catalogue_metadata`` with the generated
        topic row-field set, so a rule tightened there can no longer stay
        loose here. Only the generated-projection-specific checks (the Lean
        sketch, its theorem count against the typeset equations, and
        theorem-role closure) remain.
        """
        resolved = path if path is not None else _default_topics_path()
        try:
            manifest = load_catalogue_metadata(
                resolved, row_fields=GENERATED_TOPIC_FIELDS
            )
        except (OSError, SemanticValidationError) as exc:
            raise CatalogueValidationError(str(exc)) from exc
        try:
            data = yaml.safe_load(resolved.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            raise CatalogueValidationError(
                f"cannot read catalogue {resolved}: {exc}"
            ) from exc
        assert isinstance(data, dict)  # load_catalogue_metadata validated shape
        roster = manifest.roster
        families = manifest.families
        expected_ids = roster.topic_ids
        raw = data["topics"]
        if not isinstance(raw, list):
            raise CatalogueValidationError("catalogue topics must be a list")
        raw_ids = tuple(row.get("id") if isinstance(row, dict) else None for row in raw)
        if raw_ids != expected_ids:
            raise CatalogueValidationError(
                "catalogue rows must exactly match the sealed roster in order"
            )
        topics: list[TopicEntry] = []
        records_by_id = {record.id: record for record in manifest.records}
        for index, row in enumerate(raw, 1):
            if not isinstance(row, dict):
                raise CatalogueValidationError(f"topic row {index} must be a mapping")
            expected_id = expected_ids[index - 1]
            if row["id"] != expected_id:
                raise CatalogueValidationError(
                    f"topic row {index} must have id {expected_id!r}"
                )
            record = records_by_id[expected_id]
            if not all(
                isinstance(row[key], str) and row[key].strip()
                for key in (
                    "primary_theorem",
                    "semantic_disposition",
                    "nl",
                    "assumption_review",
                    "non_vacuity",
                    "acceptance_probe",
                    "lean_sketch",
                )
            ):
                raise CatalogueValidationError(
                    f"{expected_id}: catalogue text fields must be non-empty strings"
                )
            try:
                semantic_disposition = SemanticDisposition(
                    str(row["semantic_disposition"]).strip()
                ).value
            except ValueError as exc:
                raise CatalogueValidationError(
                    f"{expected_id}: unsupported semantic_disposition"
                ) from exc
            raw_latex = row.get("latex_equations")
            if (
                not isinstance(raw_latex, list)
                or not raw_latex
                or not all(isinstance(x, str) and x.strip() for x in raw_latex)
            ):
                raise CatalogueValidationError(
                    f"{expected_id}: latex_equations must be a non-empty list of strings"
                )
            latex_eqs = tuple(raw_latex)
            canonical_theorems = theorem_names(str(row["lean_sketch"]))
            theorem_count = len(canonical_theorems)
            if theorem_count != len(latex_eqs):
                raise CatalogueValidationError(
                    f"{expected_id}: {theorem_count} theorem declarations but {len(latex_eqs)} equations"
                )
            role_lists: list[tuple[str, ...]] = []
            for field in ("supporting_theorems", "boundary_theorems"):
                value = row.get(field)
                if not isinstance(value, list) or not all(
                    isinstance(name, str) and name.strip() for name in value
                ):
                    raise CatalogueValidationError(
                        f"{expected_id}: {field} must be a list of theorem names"
                    )
                names = tuple(name.strip() for name in value)
                if len(names) != len(set(names)):
                    raise CatalogueValidationError(
                        f"{expected_id}: {field} contains duplicates"
                    )
                role_lists.append(names)
            reviewed = (
                str(row["primary_theorem"]),
                *role_lists[0],
                *role_lists[1],
            )
            if (
                len(reviewed) != len(set(reviewed))
                or set(reviewed) != canonical_theorems
            ):
                raise CatalogueValidationError(
                    f"{expected_id}: theorem-role closure differs from the Lean body"
                )
            topics.append(
                TopicEntry(
                    id=row["id"],
                    title=record.title,
                    area=record.area,
                    family=record.family,
                    mathlib_modules=record.mathlib_modules,
                    mathlib_status=record.mathlib_status,
                    primary_theorem=row["primary_theorem"],
                    supporting_theorems=role_lists[0],
                    boundary_theorems=role_lists[1],
                    semantic_disposition=semantic_disposition,
                    nl=row["nl"],
                    assumption_review=row["assumption_review"],
                    non_vacuity=row["non_vacuity"],
                    acceptance_probe=row["acceptance_probe"],
                    lean_sketch=row["lean_sketch"],
                    latex_equations=latex_eqs,
                )
            )
        _validate_body_source_parity(topics, expected_ids)
        return cls(topics, resolved, roster, families)

    @property
    def topics(self) -> tuple[TopicEntry, ...]:
        return self._topics

    def summary(self) -> dict[str, Any]:
        """Counts by area and global maturity tallies."""
        areas: dict[str, int] = {}
        maturity_totals = {k: 0 for k in _MATURITY_ORDER}
        area_maturity: dict[str, dict[str, int]] = {}
        semantic_dispositions: dict[str, int] = {}
        area_semantic_dispositions: dict[str, dict[str, int]] = {}
        family_counts: dict[str, int] = {}

        for t in self._topics:
            areas[t.area] = areas.get(t.area, 0) + 1
            family_counts[t.family] = family_counts.get(t.family, 0) + 1
            st = t.mathlib_status
            maturity_totals[st] = maturity_totals.get(st, 0) + 1
            if t.area not in area_maturity:
                area_maturity[t.area] = {k: 0 for k in _MATURITY_ORDER}
            area_maturity[t.area][st] = area_maturity[t.area].get(st, 0) + 1
            semantic_dispositions[t.semantic_disposition] = (
                semantic_dispositions.get(t.semantic_disposition, 0) + 1
            )
            area_counts = area_semantic_dispositions.setdefault(t.area, {})
            area_counts[t.semantic_disposition] = (
                area_counts.get(t.semantic_disposition, 0) + 1
            )

        return {
            "total_topics": len(self._topics),
            "areas": dict(sorted(areas.items(), key=lambda x: x[0])),
            "families": dict(sorted(family_counts.items())),
            "maturity": maturity_totals,
            "area_maturity": area_maturity,
            "semantic_dispositions": dict(sorted(semantic_dispositions.items())),
            "area_semantic_dispositions": {
                area: dict(sorted(counts.items()))
                for area, counts in sorted(area_semantic_dispositions.items())
            },
        }


def _default_topics_path() -> Path:
    """Resolve the generated package-data catalogue for checkout or wheel use."""
    return Path(str(files("fep_lean.data").joinpath("topics.yaml")))


def _validate_body_source_parity(
    topics: list[TopicEntry], expected_ids: tuple[str, ...]
) -> None:
    """Ensure generated YAML bodies exactly match the packaged authoring registry."""
    from .registry import BODIES, LATEX_EQUATIONS, assert_roster

    assert_roster(expected_ids)
    for topic in topics:
        source = BODIES.get(topic.id)
        if source is None:
            raise CatalogueValidationError(
                f"{topic.id}: body is absent from fep_lean.catalogue.registry"
            )
        if source != topic.lean_sketch:
            raise CatalogueValidationError(
                f"{topic.id}: YAML lean_sketch differs from fep_lean.catalogue.registry"
            )
        if tuple(LATEX_EQUATIONS.get(topic.id, ())) != topic.latex_equations:
            raise CatalogueValidationError(
                f"{topic.id}: YAML latex_equations differ from "
                "fep_lean.catalogue.registry"
            )
