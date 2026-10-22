"""Typed, authored relations between catalogue topics and retained capabilities.

Shared imports are generated implementation data; they are deliberately not
treated as scientific or proof dependencies.  This module validates the
separate, maintained relation graph used by the coverage report.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

from .semantics import SemanticValidationError

_CAPABILITY_ID_RE = re.compile(r"^cap-[a-z0-9]+(?:-[a-z0-9]+)*$")
_DECLARATION_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)+$")
_CAPABILITY_BASE_FIELDS = frozenset({"id", "title", "description", "status"})
_EDGE_BASE_FIELDS = frozenset({"source", "target", "kind", "rationale"})


class CapabilityStatus(str, Enum):
    """Review state of a retained formal capability."""

    OPEN = "open"
    PARTIAL = "partial"
    SATISFIED = "satisfied"


class EdgeKind(str, Enum):
    """Meaning of one maintained formalism relation."""

    FORMAL = "formal"
    FORMAL_PAIRING = "formal_pairing"
    CONCEPTUAL = "conceptual"
    BLOCKED_BY = "blocked_by"

    @property
    def is_theorem_witnessed(self) -> bool:
        """Whether this relation is backed by a checked Lean declaration."""
        return self in {EdgeKind.FORMAL, EdgeKind.FORMAL_PAIRING}


@dataclass(frozen=True)
class CapabilityNode:
    """One tracked formal capability, including retained resolution evidence."""

    id: str
    title: str
    description: str
    status: CapabilityStatus
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class FormalismEdge:
    """One reviewed directed relation with an explicit rationale."""

    source: str
    target: str
    kind: EdgeKind
    rationale: str
    witness: str | None = None
    blocked_by: str | None = None


@dataclass(frozen=True)
class FormalismGraph:
    """Validated capability nodes and directed formalism edges."""

    capabilities: tuple[CapabilityNode, ...]
    edges: tuple[FormalismEdge, ...]

    @property
    def capability_ids(self) -> frozenset[str]:
        return frozenset(node.id for node in self.capabilities)

    @property
    def unresolved_capability_ids(self) -> frozenset[str]:
        return frozenset(
            node.id
            for node in self.capabilities
            if node.status is not CapabilityStatus.SATISFIED
        )


def _text(row: dict[str, Any], field: str, owner: str) -> str:
    value = row.get(field)
    if not isinstance(value, str) or not value.strip():
        raise SemanticValidationError(f"{owner}: {field} must be a non-empty string")
    return value.strip()


def _require_exact_fields(
    row: dict[str, Any], expected: frozenset[str], owner: str
) -> None:
    missing = expected - set(row)
    unknown = set(row) - expected
    if not missing and not unknown:
        return
    details = []
    if missing:
        details.append(f"missing {', '.join(sorted(missing))}")
    if unknown:
        details.append(f"unknown {', '.join(sorted(unknown))}")
    raise SemanticValidationError(f"{owner}: {'; '.join(details)}")


def _reject_formal_cycles(edges: tuple[FormalismEdge, ...]) -> None:
    adjacency: dict[str, list[str]] = {}
    for edge in edges:
        if edge.kind is EdgeKind.FORMAL:
            adjacency.setdefault(edge.source, []).append(edge.target)

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str, trail: tuple[str, ...]) -> None:
        if node in visiting:
            cycle = " -> ".join((*trail, node))
            raise SemanticValidationError(f"formal relation cycle: {cycle}")
        if node in visited:
            return
        visiting.add(node)
        for target in adjacency.get(node, []):
            visit(target, (*trail, node))
        visiting.remove(node)
        visited.add(node)

    for source in sorted(adjacency):
        visit(source, ())


def _obligation_token(raw_edge: dict[str, Any], owner: str) -> str:
    obligation = _text(raw_edge, "blocked_by", owner)
    if raw_edge["blocked_by"] != obligation:
        raise SemanticValidationError(f"{owner}: blocked_by must use canonical spacing")
    if not (
        re.fullmatch(r"issue:[1-9][0-9]*", obligation)
        or (
            obligation.startswith("lemma:")
            and _DECLARATION_RE.fullmatch(obligation[6:])
        )
    ):
        raise SemanticValidationError(
            f"{owner}: blocked_by must be a canonical issue or missing-lemma token"
        )
    return obligation


def load_formalism_graph(
    path: Path, *, roster_ids: Sequence[str] | None = None
) -> FormalismGraph:
    """Load and strictly validate the maintained relation graph."""
    try:
        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise SemanticValidationError(
            f"cannot read formalism graph {path}: {exc}"
        ) from exc
    if (
        not isinstance(raw, dict)
        or type(raw.get("schema_version")) is not int
        or raw["schema_version"] not in {2, 3}
    ):
        raise SemanticValidationError("formalism graph schema_version must be 2 or 3")
    schema_version = raw["schema_version"]
    unknown_top = set(raw) - {"schema_version", "capabilities", "edges"}
    if unknown_top:
        raise SemanticValidationError(
            f"formalism graph has unknown fields: {', '.join(sorted(unknown_top))}"
        )

    raw_capabilities = raw.get("capabilities")
    raw_edges = raw.get("edges")
    if not isinstance(raw_capabilities, list) or not isinstance(raw_edges, list):
        raise SemanticValidationError(
            "formalism graph capabilities and edges must be lists"
        )

    capabilities: list[CapabilityNode] = []
    for index, raw_node in enumerate(raw_capabilities, 1):
        owner = f"capability row {index}"
        if not isinstance(raw_node, dict):
            raise SemanticValidationError(f"{owner} must be an object")
        status_raw = raw_node.get("status")
        try:
            status = CapabilityStatus(status_raw)
        except (TypeError, ValueError) as exc:
            raise SemanticValidationError(
                f"{owner}: unsupported capability status"
            ) from exc
        expected_fields = (
            _CAPABILITY_BASE_FIELDS
            if status is CapabilityStatus.OPEN
            else _CAPABILITY_BASE_FIELDS | {"evidence"}
        )
        _require_exact_fields(raw_node, frozenset(expected_fields), owner)
        node_id = _text(raw_node, "id", owner)
        if not _CAPABILITY_ID_RE.fullmatch(node_id):
            raise SemanticValidationError(f"{owner}: invalid capability ID {node_id!r}")
        raw_evidence = raw_node.get("evidence", [])
        if not isinstance(raw_evidence, list) or not all(
            isinstance(item, str) and _DECLARATION_RE.fullmatch(item)
            for item in raw_evidence
        ):
            raise SemanticValidationError(
                f"{node_id}: evidence must be a list of qualified declarations"
            )
        evidence = tuple(raw_evidence)
        if status is CapabilityStatus.OPEN and evidence:
            raise SemanticValidationError(f"{node_id}: open capability has evidence")
        if status is not CapabilityStatus.OPEN and not evidence:
            raise SemanticValidationError(
                f"{node_id}: {status.value} capability requires evidence"
            )
        if len(set(evidence)) != len(evidence) or evidence != tuple(sorted(evidence)):
            raise SemanticValidationError(
                f"{node_id}: evidence declarations must be unique and sorted"
            )
        capabilities.append(
            CapabilityNode(
                id=node_id,
                title=_text(raw_node, "title", node_id),
                description=_text(raw_node, "description", node_id),
                status=status,
                evidence=evidence,
            )
        )
    capability_ids = [node.id for node in capabilities]
    if len(set(capability_ids)) != len(capability_ids):
        raise SemanticValidationError("formalism graph capability IDs must be unique")
    if capability_ids != sorted(capability_ids):
        raise SemanticValidationError("formalism graph capabilities must be ID-sorted")

    if roster_ids is None:
        from .schema import load_catalogue_metadata

        roster_ids = load_catalogue_metadata(
            Path(path).with_name("catalogue_metadata.yaml")
        ).topic_ids
    topic_ids = frozenset(roster_ids)
    capability_id_set = frozenset(capability_ids)
    edges: list[FormalismEdge] = []
    edge_keys: set[tuple[str, str, EdgeKind]] = set()
    for index, raw_edge in enumerate(raw_edges, 1):
        owner = f"edge row {index}"
        if not isinstance(raw_edge, dict):
            raise SemanticValidationError(f"{owner} must be an object")
        raw_kind = raw_edge.get("kind")
        try:
            kind = EdgeKind(raw_kind)
        except (TypeError, ValueError) as exc:
            raise SemanticValidationError(f"{owner}: unsupported edge kind") from exc
        expected_edge_fields = (
            _EDGE_BASE_FIELDS | {"witness"}
            if kind.is_theorem_witnessed
            else _EDGE_BASE_FIELDS
        )
        if schema_version == 3 and kind is EdgeKind.CONCEPTUAL:
            expected_edge_fields = expected_edge_fields | {"blocked_by"}
        _require_exact_fields(raw_edge, frozenset(expected_edge_fields), owner)
        source = _text(raw_edge, "source", owner)
        target = _text(raw_edge, "target", owner)
        if source not in topic_ids:
            raise SemanticValidationError(f"{owner}: unknown source {source!r}")
        if source == target:
            raise SemanticValidationError(f"{owner}: self-edge {source!r} is forbidden")
        if kind is EdgeKind.BLOCKED_BY:
            if target not in capability_id_set:
                raise SemanticValidationError(
                    f"{owner}: blocked_by target must be a known capability"
                )
        elif target not in topic_ids:
            raise SemanticValidationError(
                f"{owner}: {kind.value} target must be a known topic"
            )
        key = (source, target, kind)
        if key in edge_keys:
            raise SemanticValidationError(
                f"{owner}: duplicate {kind.value} edge {source} -> {target}"
            )
        edge_keys.add(key)
        witness: str | None = None
        if kind.is_theorem_witnessed:
            witness = _text(raw_edge, "witness", owner)
            if not _DECLARATION_RE.fullmatch(witness):
                raise SemanticValidationError(
                    f"{owner}: witness must be a qualified declaration"
                )
        obligation: str | None = None
        if schema_version == 3 and kind is EdgeKind.CONCEPTUAL:
            obligation = _obligation_token(raw_edge, owner)
        edges.append(
            FormalismEdge(
                source=source,
                target=target,
                kind=kind,
                rationale=_text(raw_edge, "rationale", owner),
                witness=witness,
                blocked_by=obligation,
            )
        )

    edge_tuple = tuple(edges)
    if tuple((e.source, e.kind.value, e.target) for e in edge_tuple) != tuple(
        sorted((e.source, e.kind.value, e.target) for e in edge_tuple)
    ):
        raise SemanticValidationError(
            "formalism graph edges must be sorted by source, kind, and target"
        )
    referenced_capabilities = {
        edge.target for edge in edge_tuple if edge.kind is EdgeKind.BLOCKED_BY
    }
    unresolved_capabilities = {
        node.id
        for node in capabilities
        if node.status is not CapabilityStatus.SATISFIED
    }
    unused_capabilities = unresolved_capabilities - referenced_capabilities
    if unused_capabilities:
        raise SemanticValidationError(
            "unreferenced unresolved capability nodes: "
            + ", ".join(sorted(unused_capabilities))
        )
    resolved_but_blocking = referenced_capabilities - unresolved_capabilities
    if resolved_but_blocking:
        raise SemanticValidationError(
            "satisfied capability nodes cannot be blockers: "
            + ", ".join(sorted(resolved_but_blocking))
        )
    _reject_formal_cycles(edge_tuple)
    return FormalismGraph(tuple(capabilities), edge_tuple)
