"""Immutable presentation join for structural and numerical formalism views.

The catalogue coverage join remains the sole structural source, and the typed
numerical-witness evaluator remains the sole numerical source.  This module
normalizes those two sources once so every HTML and SVG projection conserves
the same topics, relations, capabilities, modules, and witness tables.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Final, cast

from fep_lean.catalogue.coverage import build_formalism_coverage
from fep_lean.verification.numerical_witnesses import (
    NON_PROOF_EVIDENCE,
    NumericalWitness,
    evaluate_numerical_witnesses,
)

NUMERICAL_EVIDENCE_BOUNDARY = (
    "Deterministic numerical witnesses are explanatory non-proof evidence. "
    "They can expose finite sign, normalization, support, rank, identity, and "
    "contraction errors; they are neither Lean proof receipts nor empirical "
    "validation of the Free Energy Principle."
)

# The versioned release seal: the catalogue shape a release claims, not a live
# count. Bump it deliberately with each catalogue release; every receipt
# validator derives its expectations from this one definition.
RELEASE_FIRST_ID: Final = "fep-001"
RELEASE_LAST_ID: Final = "fep-159"
RELEASE_TOPICS: Final = 159
RELEASE_FAMILIES: Final = 21
RELEASE_AREAS: Final = 5
RELEASE_WITNESSES: Final = 16
RELEASE_RELATIONS: Final = 133
RELEASE_CAPABILITIES: Final = 48

RELEASE_SEAL: Final[Mapping[str, int | str]] = MappingProxyType(
    {
        "first_id": RELEASE_FIRST_ID,
        "last_id": RELEASE_LAST_ID,
        "topics": RELEASE_TOPICS,
        "families": RELEASE_FAMILIES,
        "areas": RELEASE_AREAS,
        "witnesses": RELEASE_WITNESSES,
        "relations": RELEASE_RELATIONS,
        "capabilities": RELEASE_CAPABILITIES,
    }
)

_FORMALISM_ACRONYMS = {
    "cmi": "CMI",
    "efe": "EFE",
    "elbo": "ELBO",
    "fep": "FEP",
    "iwae": "IWAE",
    "kl": "KL",
    "pac": "PAC",
    "pomdp": "POMDP",
    "slln": "SLLN",
    "vfe": "VFE",
}


def humanize_formalism_identifier(value: str) -> str:
    """Render one machine identifier without damaging scientific acronyms."""
    spaced = re.sub(
        r"(?<=[a-z])(?=[A-Z])", " ", value.replace("-", " ").replace("_", " ")
    )
    return " ".join(
        _FORMALISM_ACRONYMS.get(
            part.lower(), part if part.isupper() else part.capitalize()
        )
        for part in spaced.split()
    )


@dataclass(frozen=True)
class PresentationTopic:
    """One canonical catalogue topic represented without presentation geometry."""

    id: str
    title: str
    area: str
    family: str
    primary_theorem: str
    semantic_disposition: str
    invariant: str
    assumption_review: str
    non_vacuity: str
    acceptance_probe: str
    theorem_count: int
    definition_count: int
    abbreviation_count: int
    imports: tuple[str, ...]
    mathlib_hints: tuple[str, ...]


@dataclass(frozen=True)
class PresentationRelation:
    """One authored scientific relation copied exactly from the graph registry."""

    source: str
    target: str
    kind: str
    rationale: str
    witness: str | None


@dataclass(frozen=True)
class PresentationCapability:
    """One retained capability node and its exact declaration evidence."""

    id: str
    title: str
    description: str
    status: str
    evidence: tuple[str, ...]
    blocked_topics: tuple[str, ...]


@dataclass(frozen=True)
class PresentationFormalModule:
    """One maintained formal module and its code-dependency surface."""

    id: str
    resource: str
    lean_module: str
    role: str
    theorem_count: int
    theorems: tuple[str, ...]
    definition_count: int
    abbreviation_count: int
    structure_count: int
    imports: tuple[str, ...]
    formal_dependencies: tuple[str, ...]


@dataclass(frozen=True)
class PresentationFamily:
    """A family derived from topic rows and, when present, numerical witnesses."""

    id: str
    area: str | None
    topic_ids: tuple[str, ...]
    witness_ids: tuple[str, ...]
    formal_alignment_counts: Mapping[str, int]
    disposition_counts: Mapping[str, int]


@dataclass(frozen=True)
class PresentationArea:
    """One of the five broad areas, grouped entirely from canonical topic rows."""

    id: str
    family_ids: tuple[str, ...]
    topic_ids: tuple[str, ...]
    disposition_counts: Mapping[str, int]


@dataclass(frozen=True)
class FormalismPresentation:
    """Single immutable input model shared by every formalism presentation."""

    schema_version: int
    review_date: str
    structural_evidence_boundary: str
    numerical_evidence_boundary: str
    metrics: Mapping[str, int]
    topics: tuple[PresentationTopic, ...]
    relations: tuple[PresentationRelation, ...]
    capabilities: tuple[PresentationCapability, ...]
    formal_modules: tuple[PresentationFormalModule, ...]
    witnesses: tuple[NumericalWitness, ...]
    areas: tuple[PresentationArea, ...]
    families: tuple[PresentationFamily, ...]
    unmatched_witness_families: tuple[str, ...]


def _mapping(value: object, *, context: str) -> Mapping[str, object]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise ValueError(f"{context} must be a string-keyed mapping")
    return cast(dict[str, object], value)


def _rows(value: object, *, context: str) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, list):
        raise TypeError(f"{context} must be a list")
    rows: list[Mapping[str, object]] = []
    for index, item in enumerate(value):
        rows.append(_mapping(item, context=f"{context}[{index}]"))
    return tuple(rows)


def _required_str(row: Mapping[str, object], key: str, *, context: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{context}.{key} must be a nonempty string")
    return value


def _optional_str(row: Mapping[str, object], key: str, *, context: str) -> str | None:
    value = row.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise ValueError(f"{context}.{key} must be null or a nonempty string")
    return value


def _required_int(row: Mapping[str, object], key: str, *, context: str) -> int:
    value = row.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{context}.{key} must be a nonnegative integer")
    return value


def _strings(row: Mapping[str, object], key: str, *, context: str) -> tuple[str, ...]:
    value = row.get(key)
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(f"{context}.{key} must be a list of strings")
    return tuple(cast(list[str], value))


def _counts(value: object, *, context: str) -> Mapping[str, int]:
    raw = _mapping(value, context=context)
    counts: dict[str, int] = {}
    for key, item in raw.items():
        if not isinstance(item, int) or isinstance(item, bool) or item < 0:
            raise ValueError(f"{context}.{key} must be a nonnegative integer")
        counts[key] = item
    return MappingProxyType(counts)


def _topic(row: Mapping[str, object], index: int) -> PresentationTopic:
    context = f"coverage.topics[{index}]"
    return PresentationTopic(
        id=_required_str(row, "id", context=context),
        title=_required_str(row, "title", context=context),
        area=_required_str(row, "area", context=context),
        family=_required_str(row, "family", context=context),
        primary_theorem=_required_str(row, "primary_theorem", context=context),
        semantic_disposition=_required_str(
            row, "semantic_disposition", context=context
        ),
        invariant=_required_str(row, "invariant", context=context),
        assumption_review=_required_str(row, "assumption_review", context=context),
        non_vacuity=_required_str(row, "non_vacuity", context=context),
        acceptance_probe=_required_str(row, "acceptance_probe", context=context),
        theorem_count=_required_int(row, "theorem_count", context=context),
        definition_count=_required_int(row, "definition_count", context=context),
        abbreviation_count=_required_int(row, "abbreviation_count", context=context),
        imports=_strings(row, "imports", context=context),
        mathlib_hints=_strings(row, "mathlib_hints", context=context),
    )


def _relation(row: Mapping[str, object], index: int) -> PresentationRelation:
    context = f"coverage.relations[{index}]"
    return PresentationRelation(
        source=_required_str(row, "source", context=context),
        target=_required_str(row, "target", context=context),
        kind=_required_str(row, "kind", context=context),
        rationale=_required_str(row, "rationale", context=context),
        witness=_optional_str(row, "witness", context=context),
    )


def _capability(row: Mapping[str, object], index: int) -> PresentationCapability:
    context = f"coverage.capabilities[{index}]"
    return PresentationCapability(
        id=_required_str(row, "id", context=context),
        title=_required_str(row, "title", context=context),
        description=_required_str(row, "description", context=context),
        status=_required_str(row, "status", context=context),
        evidence=_strings(row, "evidence", context=context),
        blocked_topics=_strings(row, "blocked_topics", context=context),
    )


def _formal_module(row: Mapping[str, object], index: int) -> PresentationFormalModule:
    context = f"coverage.formal_modules[{index}]"
    return PresentationFormalModule(
        id=_required_str(row, "id", context=context),
        resource=_required_str(row, "resource", context=context),
        lean_module=_required_str(row, "lean_module", context=context),
        role=_required_str(row, "role", context=context),
        theorem_count=_required_int(row, "theorem_count", context=context),
        theorems=_strings(row, "theorems", context=context),
        definition_count=_required_int(row, "definition_count", context=context),
        abbreviation_count=_required_int(row, "abbreviation_count", context=context),
        structure_count=_required_int(row, "structure_count", context=context),
        imports=_strings(row, "imports", context=context),
        formal_dependencies=_strings(row, "formal_dependencies", context=context),
    )


def _summaries(
    topics: tuple[PresentationTopic, ...],
    witnesses: tuple[NumericalWitness, ...],
    area_order: tuple[str, ...],
) -> tuple[
    tuple[PresentationArea, ...],
    tuple[PresentationFamily, ...],
    tuple[str, ...],
]:
    family_topics: dict[str, list[PresentationTopic]] = defaultdict(list)
    family_witnesses: dict[str, list[NumericalWitness]] = defaultdict(list)
    family_areas: dict[str, str] = {}
    for topic in topics:
        previous = family_areas.setdefault(topic.family, topic.area)
        if previous != topic.area:
            raise ValueError(
                f"family {topic.family!r} spans multiple broad areas: "
                f"{previous!r} and {topic.area!r}"
            )
        family_topics[topic.family].append(topic)
    for witness in witnesses:
        family_witnesses[witness.family].append(witness)

    area_index = {area: index for index, area in enumerate(area_order)}
    family_ids = sorted(
        set(family_topics) | set(family_witnesses),
        key=lambda family: (
            area_index.get(family_areas.get(family, ""), len(area_order)),
            family,
        ),
    )
    families = tuple(
        PresentationFamily(
            id=family,
            area=family_areas.get(family),
            topic_ids=tuple(topic.id for topic in family_topics[family]),
            witness_ids=tuple(witness.id for witness in family_witnesses[family]),
            formal_alignment_counts=MappingProxyType(
                dict(
                    sorted(
                        Counter(
                            witness.formal_alignment
                            for witness in family_witnesses[family]
                        ).items()
                    )
                )
            ),
            disposition_counts=MappingProxyType(
                dict(
                    sorted(
                        Counter(
                            topic.semantic_disposition
                            for topic in family_topics[family]
                        ).items()
                    )
                )
            ),
        )
        for family in family_ids
    )

    areas = tuple(
        PresentationArea(
            id=area,
            family_ids=tuple(family.id for family in families if family.area == area),
            topic_ids=tuple(topic.id for topic in topics if topic.area == area),
            disposition_counts=MappingProxyType(
                dict(
                    sorted(
                        Counter(
                            topic.semantic_disposition
                            for topic in topics
                            if topic.area == area
                        ).items()
                    )
                )
            ),
        )
        for area in area_order
    )
    unmatched = tuple(
        family.id for family in families if family.area is None and family.witness_ids
    )
    return areas, families, unmatched


def build_formalism_presentation(project_root: Path) -> FormalismPresentation:
    """Build the sole immutable join consumed by atlas and dashboard views."""
    coverage = build_formalism_coverage(Path(project_root))
    witnesses = evaluate_numerical_witnesses(Path(project_root), scope="catalogue")

    topics = tuple(
        _topic(row, index)
        for index, row in enumerate(
            _rows(coverage.get("topics"), context="coverage.topics")
        )
    )
    relations = tuple(
        _relation(row, index)
        for index, row in enumerate(
            _rows(coverage.get("relations"), context="coverage.relations")
        )
    )
    capabilities = tuple(
        _capability(row, index)
        for index, row in enumerate(
            _rows(coverage.get("capabilities"), context="coverage.capabilities")
        )
    )
    formal_modules = tuple(
        _formal_module(row, index)
        for index, row in enumerate(
            _rows(coverage.get("formal_modules"), context="coverage.formal_modules")
        )
    )

    topic_ids = [topic.id for topic in topics]
    capability_ids = [capability.id for capability in capabilities]
    module_names = {module.lean_module for module in formal_modules}
    if len(topic_ids) != len(set(topic_ids)):
        raise ValueError("presentation join received duplicate topic IDs")
    if len(capability_ids) != len(set(capability_ids)):
        raise ValueError("presentation join received duplicate capability IDs")
    if len(witnesses) != len({witness.id for witness in witnesses}):
        raise ValueError("presentation join received duplicate numerical witness IDs")

    relation_endpoints = set(topic_ids) | set(capability_ids)
    unresolved_relations = tuple(
        f"{relation.source} -> {relation.target}"
        for relation in relations
        if relation.source not in relation_endpoints
        or relation.target not in relation_endpoints
    )
    if unresolved_relations:
        raise ValueError(
            "presentation relations have unresolved endpoints: "
            + ", ".join(unresolved_relations)
        )
    unresolved_dependencies = tuple(
        f"{module.lean_module} -> {dependency}"
        for module in formal_modules
        for dependency in module.formal_dependencies
        if dependency not in module_names
    )
    if unresolved_dependencies:
        raise ValueError(
            "presentation module dependencies have unresolved targets: "
            + ", ".join(unresolved_dependencies)
        )

    area_counts = _counts(coverage.get("area_counts"), context="coverage.area_counts")
    area_order = tuple(area_counts)
    if len(area_order) != 5:
        raise ValueError(
            "formalism presentation requires exactly five canonical broad areas; "
            f"received {len(area_order)}"
        )
    actual_area_counts = Counter(topic.area for topic in topics)
    if dict(area_counts) != dict(sorted(actual_area_counts.items())):
        raise ValueError("coverage area counts do not conserve canonical topic rows")

    areas, families, unmatched = _summaries(topics, witnesses, area_order)
    metrics = _counts(coverage.get("metrics"), context="coverage.metrics")
    if metrics.get("topics") != len(topics):
        raise ValueError("coverage topic metric does not conserve canonical topic rows")
    if metrics.get("authored_relation_edges") != len(relations):
        raise ValueError(
            "coverage relation metric does not conserve authored relation rows"
        )

    schema_version = coverage.get("schema_version")
    if not isinstance(schema_version, int) or isinstance(schema_version, bool):
        raise TypeError("coverage.schema_version must be an integer")
    review_date = coverage.get("review_date")
    if not isinstance(review_date, str) or not review_date:
        raise ValueError("coverage.review_date must be a nonempty string")
    evidence_boundary = coverage.get("evidence_boundary")
    if not isinstance(evidence_boundary, str) or not evidence_boundary:
        raise ValueError("coverage.evidence_boundary must be a nonempty string")
    if any(witness.evidence_kind != NON_PROOF_EVIDENCE for witness in witnesses):
        raise ValueError("numerical witness evidence boundary was weakened")

    return FormalismPresentation(
        schema_version=schema_version,
        review_date=review_date,
        structural_evidence_boundary=evidence_boundary,
        numerical_evidence_boundary=NUMERICAL_EVIDENCE_BOUNDARY,
        metrics=metrics,
        topics=topics,
        relations=relations,
        capabilities=capabilities,
        formal_modules=formal_modules,
        witnesses=witnesses,
        areas=areas,
        families=families,
        unmatched_witness_families=unmatched,
    )


__all__ = [
    "NUMERICAL_EVIDENCE_BOUNDARY",
    "RELEASE_AREAS",
    "RELEASE_CAPABILITIES",
    "RELEASE_FAMILIES",
    "RELEASE_FIRST_ID",
    "RELEASE_LAST_ID",
    "RELEASE_RELATIONS",
    "RELEASE_SEAL",
    "RELEASE_TOPICS",
    "RELEASE_WITNESSES",
    "FormalismPresentation",
    "PresentationArea",
    "PresentationCapability",
    "PresentationFamily",
    "PresentationFormalModule",
    "PresentationRelation",
    "PresentationTopic",
    "build_formalism_presentation",
    "humanize_formalism_identifier",
]
