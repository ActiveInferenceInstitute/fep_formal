"""Deterministic breadth/depth coverage projections for the formalism catalogue."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from fep_lean.formal.declarations import (
    all_formal_theorem_declarations,
    composed_theorem_declarations,
    composed_theorem_sources,
    formal_theorem_modules,
)
from fep_lean.formal.manifest import (
    FORMAL_MODULES,
    FormalModuleRole,
    formal_resource_paths,
)
from fep_lean.lean_source import (
    LEAN_THEOREM_RE,
    lean_code_without_comments,
    lean_declaration_conclusion,
)

from .registry import BODIES, validate_body_family_ownership
from .relations import CapabilityStatus, EdgeKind, load_formalism_graph
from .schema import load_catalogue_metadata
from .semantics import SemanticDisposition, load_theorem_maturity

_THEOREM_RE = LEAN_THEOREM_RE
_DEFINITION_RE = re.compile(
    r"^\s*(?:noncomputable\s+)?def\s+([A-Za-z][A-Za-z0-9_]*)", re.MULTILINE
)
_ABBREV_RE = re.compile(r"^\s*abbrev\s+([A-Za-z][A-Za-z0-9_]*)", re.MULTILINE)
_STRUCTURE_RE = re.compile(r"^\s*structure\s+([A-Za-z][A-Za-z0-9_]*)", re.MULTILINE)
_IMPORT_RE = re.compile(r"^\s*import\s+(\S+)", re.MULTILINE)

COVERAGE_JSON = Path("docs/formalism-coverage.json")
COVERAGE_MARKDOWN = Path("docs/formalism-coverage.md")


def topic_import_modules(topic_id: str) -> tuple[str, ...]:
    """Return the modules a topic body imports, in body order, without repeats.

    This is one half of the topic-to-module incidence relation that
    :func:`build_formalism_coverage` aggregates into the coverage report's
    "Mathlib support surface" table -- same regex, same source, same comment
    stripping -- so a caller that needs one row's modules cannot disagree with
    the report that owns the relation.

    The framework chapters used to carry a hand-typed module per row instead.
    Forty-two of those seventy-one cells named a module their row never
    imported, because nothing recomputed them when a body narrowed or moved an
    import.
    """

    body = BODIES[topic_id]
    return tuple(dict.fromkeys(_IMPORT_RE.findall(lean_code_without_comments(body))))


def render_topic_import_modules(
    modules: Iterable[str], *, omit_prefix: str = "Mathlib."
) -> str:
    """Render a row's imports as one inline-code list for a manuscript cell.

    ``Mathlib.`` is dropped because every framework table sits under a heading
    that says so and the column would otherwise repeat it on every line; any
    other namespace (``FepSketches.``) keeps its prefix, so the two are never
    confusable. An empty import list renders as an em dash rather than an empty
    cell, which a reader cannot distinguish from a missing value.
    """

    names = [module.removeprefix(omit_prefix) for module in modules]
    if not names:
        return "---"
    return ", ".join(f"`{name}`" for name in names)


def build_formalism_coverage(project_root: Path) -> dict[str, Any]:
    """Join canonical sources into an auditable coverage data structure."""
    root = Path(project_root)
    metadata = load_catalogue_metadata(root / "config" / "catalogue_metadata.yaml")
    validate_body_family_ownership(
        {record.id: record.family for record in metadata.records}
    )
    audit = load_theorem_maturity(
        root / "config" / "theorem_maturity.yaml",
        roster_ids=metadata.topic_ids,
    )
    graph = load_formalism_graph(
        root / "config" / "formalism_relations.yaml",
        roster_ids=metadata.topic_ids,
    )
    known_declarations = all_formal_theorem_declarations(root)
    required_declarations = {
        declaration for node in graph.capabilities for declaration in node.evidence
    } | {
        edge.witness
        for edge in graph.edges
        if edge.kind.is_theorem_witnessed and edge.witness is not None
    }
    unresolved_declarations = sorted(required_declarations - known_declarations)
    if unresolved_declarations:
        raise ValueError(
            "unresolved formal evidence declarations: "
            + ", ".join(unresolved_declarations)
        )
    reviewed_declarations = sorted(
        {
            theorem
            for review in audit.records
            for theorem in (
                review.primary_theorem,
                *review.supporting_theorems,
                *review.boundary_theorems,
            )
            if "." in theorem
        }
        - known_declarations
    )
    if reviewed_declarations:
        raise ValueError(
            "theorem-maturity references not resolvable as formal declarations: "
            + ", ".join(reviewed_declarations)
        )
    composed_sources = composed_theorem_sources(root)
    endpoint_failures: list[str] = []
    pairing_shape_failures: list[str] = []
    for edge in graph.edges:
        if not edge.kind.is_theorem_witnessed or edge.witness is None:
            continue
        raw_witness_source = composed_sources.get(edge.witness)
        witness_source = (
            lean_code_without_comments(raw_witness_source)
            if raw_witness_source is not None
            else None
        )
        try:
            conclusion = (
                lean_declaration_conclusion(raw_witness_source)
                if raw_witness_source is not None
                else None
            )
        except ValueError:
            conclusion = None
        if edge.kind is EdgeKind.FORMAL_PAIRING and (
            conclusion is None or "∧" not in conclusion
        ):
            pairing_shape_failures.append(
                f"{edge.source} -> {edge.target} ({edge.witness})"
            )
        endpoint_fragments = tuple(
            f"fep_fep{topic_id.removeprefix('fep-')}."
            for topic_id in (edge.source, edge.target)
        )
        if witness_source is None or not all(
            fragment in witness_source for fragment in endpoint_fragments
        ):
            endpoint_failures.append(f"{edge.source} -> {edge.target} ({edge.witness})")
    if endpoint_failures:
        raise ValueError(
            "theorem-witnessed relations missing endpoint references: "
            + ", ".join(endpoint_failures)
        )
    if pairing_shape_failures:
        raise ValueError(
            "formal_pairing witnesses must expose a checked conjunction before "
            "their proof: " + ", ".join(pairing_shape_failures)
        )
    reviews = audit.by_topic_id
    module_topics: dict[str, list[str]] = defaultdict(list)
    rows: list[dict[str, Any]] = []
    total_theorems = 0
    total_definitions = 0
    total_abbreviations = 0
    total_import_edges = 0

    for meta in metadata.records:
        body = BODIES[meta.id]
        code = lean_code_without_comments(body)
        theorem_names = _THEOREM_RE.findall(code)
        definition_names = _DEFINITION_RE.findall(code)
        abbreviation_names = _ABBREV_RE.findall(code)
        imports = _IMPORT_RE.findall(code)
        total_theorems += len(theorem_names)
        total_definitions += len(definition_names)
        total_abbreviations += len(abbreviation_names)
        total_import_edges += len(imports)
        for module in imports:
            module_topics[module].append(meta.id)
        review = reviews[meta.id]
        rows.append(
            {
                "id": meta.id,
                "title": meta.title,
                "area": meta.area,
                "family": meta.family,
                "primary_theorem": review.primary_theorem,
                "semantic_disposition": review.disposition.value,
                "invariant": review.invariant,
                "assumption_review": review.assumption_review,
                "non_vacuity": review.non_vacuity,
                "acceptance_probe": review.acceptance_probe,
                "theorem_count": len(theorem_names),
                "definition_count": len(definition_names),
                "abbreviation_count": len(abbreviation_names),
                "imports": imports,
                "mathlib_hints": list(meta.mathlib_modules),
            }
        )

    disposition_counts = Counter(row["semantic_disposition"] for row in rows)
    area_counts = Counter(row["area"] for row in rows)
    family_counts = Counter(row["family"] for row in rows)
    area_dispositions: dict[str, dict[str, int]] = {}
    dispositions = [member.value for member in SemanticDisposition]
    for area in sorted(area_counts):
        area_dispositions[area] = {
            disposition: sum(
                row["area"] == area and row["semantic_disposition"] == disposition
                for row in rows
            )
            for disposition in dispositions
        }

    gap_ids = {
        row["id"]
        for row in rows
        if row["semantic_disposition"] in {"scope_gap", "assumption_gap"}
    }
    blocked_sources = {
        edge.source for edge in graph.edges if edge.kind is EdgeKind.BLOCKED_BY
    }
    formalized_ids = {
        row["id"]
        for row in rows
        if row["semantic_disposition"] == SemanticDisposition.FORMALIZED.value
    }
    missing = sorted(gap_ids - blocked_sources)
    blocked_formalized = sorted(formalized_ids & blocked_sources)
    if missing or blocked_formalized:
        details = []
        if missing:
            details.append("gap rows without blocked_by edges: " + ", ".join(missing))
        if blocked_formalized:
            details.append(
                "formalized rows with blocked_by edges: "
                + ", ".join(blocked_formalized)
            )
        raise ValueError("; ".join(details))

    relation_counts = Counter(edge.kind.value for edge in graph.edges)
    capability_status_counts = Counter(node.status.value for node in graph.capabilities)
    formal_declaration_modules = formal_theorem_modules(root)
    composed_declarations = composed_theorem_declarations(root)
    manifested_module_names = {module.lean_module for module in FORMAL_MODULES}
    formal_modules: list[dict[str, Any]] = []
    formal_definition_count = 0
    formal_abbreviation_count = 0
    formal_structure_count = 0
    formal_import_edges = 0
    internal_dependency_edges = 0
    for module, path in zip(
        FORMAL_MODULES,
        formal_resource_paths(project_root=root),
        strict=True,
    ):
        body = lean_code_without_comments(path.read_text(encoding="utf-8"))
        theorem_declarations = sorted(
            declaration
            for declaration, owner in formal_declaration_modules.items()
            if owner == module.lean_module
        )
        definitions = _DEFINITION_RE.findall(body)
        abbreviations = _ABBREV_RE.findall(body)
        structures = _STRUCTURE_RE.findall(body)
        imports = _IMPORT_RE.findall(body)
        dependencies = sorted(
            imported for imported in imports if imported in manifested_module_names
        )
        formal_definition_count += len(definitions)
        formal_abbreviation_count += len(abbreviations)
        formal_structure_count += len(structures)
        formal_import_edges += len(imports)
        internal_dependency_edges += len(dependencies)
        formal_modules.append(
            {
                "id": "formal-module-" + Path(module.resource).stem.replace("_", "-"),
                "resource": module.resource,
                "lean_module": module.lean_module,
                "role": module.role.value,
                "theorem_count": len(theorem_declarations),
                "theorems": theorem_declarations,
                "definition_count": len(definitions),
                "abbreviation_count": len(abbreviations),
                "structure_count": len(structures),
                "imports": imports,
                "formal_dependencies": dependencies,
            }
        )

    formal_theorem_count = len(formal_declaration_modules)
    foundation_theorem_count = sum(
        row["theorem_count"]
        for row in formal_modules
        if row["role"] == FormalModuleRole.FOUNDATION.value
    )

    return {
        "schema_version": 3,
        "review_date": audit.review_date,
        "evidence_boundary": (
            "Counts describe canonical source coverage. Compilation evidence and "
            "full external-run evidence are separate receipt contracts."
        ),
        "metrics": {
            "topics": len(rows),
            "formal_modules": len(formal_modules),
            "foundation_modules": sum(
                module.role is FormalModuleRole.FOUNDATION for module in FORMAL_MODULES
            ),
            "topic_theorems": total_theorems,
            "formal_resource_theorems": formal_theorem_count,
            "foundation_theorems": foundation_theorem_count,
            "theorems": total_theorems + formal_theorem_count,
            "topic_definitions": total_definitions,
            "formal_resource_definitions": formal_definition_count,
            "definitions": total_definitions + formal_definition_count,
            "topic_abbreviations": total_abbreviations,
            "formal_resource_abbreviations": formal_abbreviation_count,
            "abbreviations": total_abbreviations + formal_abbreviation_count,
            "formal_resource_structures": formal_structure_count,
            "distinct_mathlib_imports": len(module_topics),
            "topic_import_edges": total_import_edges,
            "formal_module_import_edges": formal_import_edges,
            "formal_module_dependency_edges": internal_dependency_edges,
            "authored_relation_edges": len(graph.edges),
            "formal_relation_witnesses": relation_counts[EdgeKind.FORMAL.value],
            "formal_pairing_witnesses": relation_counts[EdgeKind.FORMAL_PAIRING.value],
            "theorem_witnessed_relations": sum(
                relation_counts[kind.value]
                for kind in EdgeKind
                if kind.is_theorem_witnessed
            ),
            "composed_theorems": len(composed_declarations),
            "capability_nodes": len(graph.capabilities),
            "open_capabilities": sum(
                node.status is not CapabilityStatus.SATISFIED
                for node in graph.capabilities
            ),
            "satisfied_capabilities": capability_status_counts[
                CapabilityStatus.SATISFIED.value
            ],
        },
        "area_counts": dict(sorted(area_counts.items())),
        "family_counts": dict(sorted(family_counts.items())),
        "disposition_counts": dict(sorted(disposition_counts.items())),
        "area_dispositions": area_dispositions,
        "relation_counts": dict(sorted(relation_counts.items())),
        "capability_status_counts": dict(sorted(capability_status_counts.items())),
        "capabilities": [
            {
                "id": node.id,
                "title": node.title,
                "description": node.description,
                "status": node.status.value,
                "evidence": list(node.evidence),
                "blocked_topics": [
                    edge.source
                    for edge in graph.edges
                    if edge.kind is EdgeKind.BLOCKED_BY and edge.target == node.id
                ],
            }
            for node in graph.capabilities
        ],
        "relations": [
            {
                "source": edge.source,
                "target": edge.target,
                "kind": edge.kind.value,
                "rationale": edge.rationale,
                "witness": edge.witness,
            }
            for edge in graph.edges
        ],
        "formal_modules": formal_modules,
        "topics": rows,
        "mathlib_modules": [
            {
                "module": module,
                "topic_count": len(topic_ids),
                "topic_ids": topic_ids,
            }
            for module, topic_ids in sorted(module_topics.items())
        ],
    }


def render_formalism_coverage_markdown(coverage: dict[str, Any]) -> str:
    """Render the coverage join as a human-reviewable Markdown audit."""
    metrics = coverage["metrics"]
    dispositions = [member.value for member in SemanticDisposition]
    lines = [
        "<!-- AUTO-GENERATED by scripts/build_formalism_coverage.py; DO NOT EDIT -->",
        "",
        "# Formalism Coverage and Semantic Depth",
        "",
        f"Reviewed: `{coverage['review_date']}`.",
        "",
        str(coverage["evidence_boundary"]),
        "",
        "## Coverage totals",
        "",
        "| Metric | Count |",
        "| --- | ---: |",
        f"| Stable topics | {metrics['topics']} |",
        f"| Maintained formal modules | {metrics['formal_modules']} |",
        f"| Foundation modules | {metrics['foundation_modules']} |",
        f"| Topic theorem declarations | {metrics['topic_theorems']} |",
        f"| Formal-resource theorem declarations | {metrics['formal_resource_theorems']} |",
        f"| Foundation theorem declarations | {metrics['foundation_theorems']} |",
        f"| Total theorem declarations | {metrics['theorems']} |",
        f"| Topic definitions | {metrics['topic_definitions']} |",
        f"| Formal-resource definitions | {metrics['formal_resource_definitions']} |",
        f"| Total definitions | {metrics['definitions']} |",
        f"| Topic abbreviations | {metrics['topic_abbreviations']} |",
        f"| Formal-resource abbreviations | {metrics['formal_resource_abbreviations']} |",
        f"| Total abbreviations | {metrics['abbreviations']} |",
        f"| Formal-resource structures | {metrics['formal_resource_structures']} |",
        f"| Distinct Mathlib imports | {metrics['distinct_mathlib_imports']} |",
        f"| Topic-to-import edges | {metrics['topic_import_edges']} |",
        f"| Formal-resource import edges | {metrics['formal_module_import_edges']} |",
        f"| Internal formal-module dependencies | {metrics['formal_module_dependency_edges']} |",
        f"| Authored formalism relations | {metrics['authored_relation_edges']} |",
        f"| Derivational formal relations | {metrics['formal_relation_witnesses']} |",
        f"| Checked formal pairings | {metrics['formal_pairing_witnesses']} |",
        f"| All theorem-witnessed relations | {metrics['theorem_witnessed_relations']} |",
        f"| Composed theorem declarations | {metrics['composed_theorems']} |",
        f"| Capability nodes (retained history) | {metrics['capability_nodes']} |",
        f"| Unresolved capability nodes | {metrics['open_capabilities']} |",
        f"| Satisfied capability nodes | {metrics['satisfied_capabilities']} |",
        "",
        "## Semantic disposition matrix",
        "",
        (
            "Compilation and semantic adequacy are deliberately different axes. "
            "`formalized` means the primary theorem directly states the narrowed "
            "topic claim; proxy categories expose approximations or assumptions; "
            "gap categories identify work not yet represented by the theorem."
        ),
        "",
        "| Area | " + " | ".join(dispositions) + " | Total |",
        "| --- | " + " | ".join("---:" for _ in dispositions) + " | ---: |",
    ]
    for area, counts in coverage["area_dispositions"].items():
        total = sum(counts.values())
        lines.append(
            f"| {area} | "
            + " | ".join(str(counts[disposition]) for disposition in dispositions)
            + f" | {total} |"
        )
    totals = coverage["disposition_counts"]
    lines.append(
        "| **Total** | "
        + " | ".join(str(totals.get(disposition, 0)) for disposition in dispositions)
        + f" | **{metrics['topics']}** |"
    )
    lines.extend(
        [
            "",
            "## Per-topic coverage",
            "",
            "| Topic | Area | Primary theorem | Disposition | Theorems | Definitions | Imports |",
            "| --- | --- | --- | --- | ---: | ---: | ---: |",
        ]
    )
    for row in coverage["topics"]:
        lines.append(
            f"| {row['id']} | {row['area']} | `{row['primary_theorem']}` | "
            f"`{row['semantic_disposition']}` | {row['theorem_count']} | "
            f"{row['definition_count']} | {len(row['imports'])} |"
        )
    lines.extend(
        [
            "",
            "## Open semantic obligations",
            "",
            (
                "The following rows remain explicit scope or assumption gaps. Their "
                "Lean bodies may compile, but compilation is not evidence that the "
                "topic-level scientific claim has been formalized."
            ),
            "",
        ]
    )
    for row in coverage["topics"]:
        if row["semantic_disposition"] not in {"scope_gap", "assumption_gap"}:
            continue
        lines.extend(
            [
                f"### {row['id']} — {row['title']}",
                "",
                f"- Primary theorem: `{row['primary_theorem']}`",
                f"- Disposition: `{row['semantic_disposition']}`",
                f"- Assumption/scope review: {row['assumption_review']}",
                f"- Non-vacuity review: {row['non_vacuity']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Maintained formal kernel",
            "",
            (
                "These packaged modules are a distinct proof surface from the "
                "generated topic sketches. Internal module dependencies are "
                "displayed explicitly and never counted as authored scientific "
                "relations."
            ),
            "",
            "| Module | Role | Theorems | Definitions | Structures | Internal dependencies |",
            "| --- | --- | ---: | ---: | ---: | --- |",
        ]
    )
    for module in coverage["formal_modules"]:
        dependencies = (
            ", ".join(f"`{item}`" for item in module["formal_dependencies"]) or "—"
        )
        lines.append(
            f"| `{module['lean_module']}` | `{module['role']}` | "
            f"{module['theorem_count']} | {module['definition_count']} | "
            f"{module['structure_count']} | {dependencies} |"
        )
    lines.extend(
        [
            "",
            "## Authored formalism relations",
            "",
            (
                "These edges are maintained scientific review data. `conceptual` "
                "means explanatory adjacency, `formal` means a direct derivation or "
                "identification, `formal_pairing` means one checked theorem exposes "
                "both endpoint laws without implication, and `blocked_by` names a "
                "missing capability. Shared imports never create these edges."
            ),
            "",
            "| Source | Kind | Target | Witness | Rationale |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for edge in coverage["relations"]:
        witness = f"`{edge['witness']}`" if edge["witness"] else "—"
        lines.append(
            f"| {edge['source']} | `{edge['kind']}` | {edge['target']} | "
            f"{witness} | {edge['rationale']} |"
        )
    lines.extend(
        [
            "",
            "## Capability roster",
            "",
            "Satisfied nodes remain visible so resolved gaps retain auditable declaration evidence.",
            "",
            "| Capability | Status | Blocked topics | Evidence | Required formal surface |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for node in coverage["capabilities"]:
        lines.append(
            f"| `{node['id']}` — {node['title']} | `{node['status']}` | "
            f"{', '.join(node['blocked_topics']) or '—'} | "
            f"{', '.join(f'`{item}`' for item in node['evidence']) or '—'} | "
            f"{node['description']} |"
        )
    lines.extend(
        [
            "",
            "## Mathlib support surface",
            "",
            (
                "Shared imports indicate library reuse, not logical dependencies "
                "between catalogue topics."
            ),
            "",
            "| Mathlib module | Topics | Topic IDs |",
            "| --- | ---: | --- |",
        ]
    )
    for module in coverage["mathlib_modules"]:
        lines.append(
            f"| `{module['module']}` | {module['topic_count']} | "
            + ", ".join(module["topic_ids"])
            + " |"
        )
    return "\n".join(lines).rstrip() + "\n"


def render_formalism_coverage_json(coverage: dict[str, Any]) -> str:
    return json.dumps(coverage, indent=2, sort_keys=True) + "\n"


def coverage_projection_paths(project_root: Path) -> tuple[Path, Path]:
    root = Path(project_root)
    return root / COVERAGE_JSON, root / COVERAGE_MARKDOWN


def write_formalism_coverage(project_root: Path) -> tuple[Path, Path]:
    coverage = build_formalism_coverage(project_root)
    json_path, markdown_path = coverage_projection_paths(project_root)
    json_path.write_text(render_formalism_coverage_json(coverage), encoding="utf-8")
    markdown_path.write_text(
        render_formalism_coverage_markdown(coverage), encoding="utf-8"
    )
    return json_path, markdown_path


def formalism_coverage_drift(project_root: Path) -> tuple[Path, ...]:
    coverage = build_formalism_coverage(project_root)
    json_path, markdown_path = coverage_projection_paths(project_root)
    expected = {
        json_path: render_formalism_coverage_json(coverage),
        markdown_path: render_formalism_coverage_markdown(coverage),
    }
    return tuple(
        path
        for path, content in expected.items()
        if not path.is_file() or path.read_text(encoding="utf-8") != content
    )
