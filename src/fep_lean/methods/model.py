"""Portable canonical mathematical positioning model and source validation."""

from __future__ import annotations

import ast
import hashlib
import json
import re
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from importlib.resources import files
from pathlib import Path, PurePosixPath
from typing import Any, cast

import yaml

from fep_lean import _SOURCE_RUNTIME_SHA256, __version__
from fep_lean._paths import FepLeanError
from fep_lean.catalogue import registry as _registry
from fep_lean.catalogue.registry import (
    BODY_MODULE_MANIFEST,
    validate_body_family_ownership,
    validate_body_roster,
)
from fep_lean.catalogue.relations import EdgeKind, FormalismGraph, load_formalism_graph
from fep_lean.catalogue.schema import CatalogueMetadataManifest, load_catalogue_metadata
from fep_lean.catalogue.semantics import (
    TheoremMaturityAudit,
    load_theorem_maturity,
    render_proxy_statement,
)
from fep_lean.catalogue.topics import FEPTopicCatalogue
from fep_lean.formal.declarations import (
    all_formal_theorem_declarations,
    composed_theorem_sources,
    formal_theorem_modules,
)
from fep_lean.formal.manifest import FORMAL_MODULES, formal_resource_paths
from fep_lean.lean_source import (
    LEAN_THEOREM_RE,
    iter_lean_namespace_scopes,
    lean_code_without_comments,
    lean_declaration_conclusion,
)

from .probes import classical_mds, evaluate_boundary_probes

POLICY_FIELDS = {
    "family",
    "domains",
    "carriers",
    "scale",
    "topology",
    "embedding",
    "statistics",
    "limits",
}
SCOPE_FIELDS = {"resource", "domains", "carrier", "scope"}
RESOURCE_OWNERS = {
    "catalogue_metadata.yaml": "config/catalogue_metadata.yaml",
    "theorem_maturity.yaml": "config/theorem_maturity.yaml",
    "formalism_relations.yaml": "config/formalism_relations.yaml",
    "positioning.yaml": "specs/openai-math-methods/positioning.yaml",
}
_VALIDATOR_OWNERS = (
    "__init__.py",
    "catalogue/registry.py",
    "catalogue/schema.py",
    "catalogue/semantics.py",
    "catalogue/relations.py",
    "catalogue/latex.py",
    "catalogue/topics.py",
    "formal/manifest.py",
    "formal/declarations.py",
    "lean_source.py",
)
_METHODS_OWNERS = (
    "methods/__init__.py",
    "methods/model.py",
    "methods/probes.py",
    "methods/projection.py",
    "methods/visualization.py",
)
EVIDENCE_BOUNDARY = (
    "Offline canonical source analysis and authored mathematical context. "
    "Declaration resolution is source-text validation, never native compilation. "
    "No Hermes, OpenGauss, upstream execution, live service, H3/Q7 gate, or scientific promotion occurs. "
    "Family context, numerical probes and distances are non-proof information."
)


class PositioningError(ValueError, FepLeanError):
    """An input or projection failed the slice's bounded contract."""


ANALYSIS_BOUNDARY = (
    "Source-grounded semantic analysis: exact Lean source slices and lexical roles, "
    "joined to maintained review prose. This is neither a certified translation, "
    "Lean elaboration, a minimal kernel dependency graph, nor LLM execution. "
    "A proposition-looking binder is not classified as a proved hypothesis by this parser."
)
_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_']*(?:\.[A-Za-z_][A-Za-z0-9_']*)*")
_COMMAND = re.compile(
    r"(?m)^[ \t]*(?:@\[[^\]\r\n]*\][ \t]*(?:\n[ \t]*)?)*"
    r"(?:(?:private|protected|noncomputable|unsafe|partial)[ \t]+)*"
    r"(namespace|section|end|variable|include|omit|theorem|lemma|def|abbrev|structure|instance|opaque|inductive|class|axiom|constant|example)\b"
)


def _header_delimiters(code: str, start: int) -> tuple[int, int]:
    """Find the goal colon and proof delimiter without entering nested binders."""
    stack: list[str] = []
    colon: int | None = None
    pairs = {")": "(", "}": "{", "]": "["}
    for index in range(start, len(code)):
        char = code[index]
        if not stack and code[index : index + 2] == ":=":
            if colon is None:
                raise PositioningError("Lean theorem header has no goal colon")
            return colon, index
        if char in "({[":
            stack.append(char)
        elif char in ")}]":
            if not stack or stack.pop() != pairs[char]:
                raise PositioningError("unbalanced Lean theorem header")
        elif char == ":" and not stack and colon is None:
            colon = index
    raise PositioningError("Lean theorem header has no proof delimiter")


def _binder_groups(text: str) -> list[dict[str, Any]]:
    """Preserve complete top-level binder groups; make only syntactic assertions."""
    code = lean_code_without_comments(text)
    result: list[dict[str, Any]] = []
    index = 0
    pairs = {")": "(", "}": "{", "]": "["}
    while index < len(code):
        if code[index].isspace():
            index += 1
            continue
        if code[index] not in "({[":
            raise PositioningError("unsupported non-group Lean theorem binder")
        start = index
        stack = [code[index]]
        index += 1
        binder_colon: int | None = None
        while index < len(code) and stack:
            char = code[index]
            if char in "({[":
                stack.append(char)
            elif char in ")}]":
                if stack.pop() != pairs[char]:
                    raise PositioningError("unbalanced Lean binder")
            elif char == ":" and len(stack) == 1 and binder_colon is None:
                binder_colon = index
            index += 1
        if stack:
            raise PositioningError("unclosed Lean binder")
        raw = text[start:index]
        names = (
            code[start + 1 : binder_colon].strip().split()
            if binder_colon is not None
            else []
        )
        result.append(
            {
                "source": raw,
                "visibility": {"(": "explicit", "{": "implicit", "[": "instance"}[
                    code[start]
                ],
                "names": names,
                "type_source": text[binder_colon + 1 : index - 1].strip()
                if binder_colon is not None
                else text[start + 1 : index - 1].strip(),
                "role": "instance_requirement"
                if code[start] == "["
                else "typed_binder",
                "hypothesis_status": "source syntax; proposition elaboration not performed",
            }
        )
    return result


def _variable_context(source: str, before: int) -> list[str]:
    """Retain active namespace/section variable commands, including multiline groups."""
    code = lean_code_without_comments(source)
    scopes: list[tuple[str | None, list[str]]] = [(None, [])]
    commands = list(_COMMAND.finditer(code, 0, before))
    for index, match in enumerate(commands):
        kind = match.group(1)
        line_end = code.find("\n", match.end())
        if line_end < 0:
            line_end = len(code)
        name = code[match.end() : line_end].strip()
        if kind in {"namespace", "section"}:
            scopes.append((name or None, []))
        elif kind == "end" and len(scopes) > 1:
            if not name:
                scopes.pop()
            else:
                for scope_index in range(len(scopes) - 1, 0, -1):
                    scope_name = scopes[scope_index][0]
                    if scope_name and (
                        scope_name == name or scope_name.endswith("." + name)
                    ):
                        del scopes[scope_index:]
                        break
        elif kind == "variable":
            end = commands[index + 1].start() if index + 1 < len(commands) else before
            # Only complete groups are part of a variable command; trailing
            # open/include/omit commands are retained separately in source context.
            tail = source[match.end() : end].strip()
            cleaned = lean_code_without_comments(tail)
            depth = 0
            last_end = 0
            for position, char in enumerate(cleaned):
                if char in "({[":
                    depth += 1
                elif char in ")}]":
                    depth -= 1
                    if depth == 0:
                        last_end = position + 1
                elif depth == 0 and not char.isspace():
                    break
            if last_end:
                scopes[-1][1].append(tail[:last_end])
    return [item for _name, variables in scopes for item in variables]


def _theorem_sources(
    source: str, source_owner: str, prefix: str = ""
) -> dict[str, dict[str, Any]]:
    """Extract exact statements with namespace context from reviewed Lean resources."""
    code = lean_code_without_comments(source)
    offset = 0
    namespaces: dict[int, tuple[str, ...]] = {}
    for line, scope, _opened in iter_lean_namespace_scopes(source):
        namespaces[offset] = scope
        offset += len(line) + 1
    matches = list(LEAN_THEOREM_RE.finditer(code))
    commands = list(_COMMAND.finditer(code))
    result: dict[str, dict[str, Any]] = {}
    for match in matches:
        name_start = match.start(1)
        line_start = code.rfind("\n", 0, name_start) + 1
        namespace = ".".join(namespaces.get(line_start, ()))
        qualified = ".".join(
            part for part in (prefix, namespace, match.group(1)) if part
        )
        if qualified in result:
            raise PositioningError(f"ambiguous Lean theorem source: {qualified}")
        colon, proof_start = _header_delimiters(code, match.end())
        keyword = re.search(
            r"\b(?:theorem|lemma)\s*$", code[match.start() : name_start]
        )
        if keyword is None:
            raise PositioningError("Lean theorem declaration keyword is unresolved")
        declaration_start = match.start() + keyword.start()
        end = next(
            (item.start() for item in commands if item.start() > proof_start),
            len(source),
        )
        variables = _variable_context(source, declaration_start)
        statement = source[declaration_start:proof_start].strip()
        result[qualified] = {
            "qualified_name": qualified,
            "source_owner": source_owner,
            "source_line": source.count("\n", 0, declaration_start) + 1,
            "line_coordinate_kind": "canonical_topic_body_literal"
            if source_owner.endswith(".py")
            else "formal_resource_file",
            "statement": statement,
            "statement_sha256": hashlib.sha256(statement.encode()).hexdigest(),
            "namespace": ".".join(part for part in (prefix, namespace) if part),
            "namespace_variable_context": variables,
            "context_binders": [
                group for text in variables for group in _binder_groups(text)
            ],
            "binders": _binder_groups(source[match.end() : colon].strip()),
            "conclusion": source[colon + 1 : proof_start].strip(),
            "proof_source": source[proof_start + 2 : end].strip(),
            "source_context": source[:declaration_start],
            "analysis_boundary": ANALYSIS_BOUNDARY,
        }
    return result


def _theorem_analysis_index(paths: Mapping[str, Path]) -> dict[str, dict[str, Any]]:
    formal_sources = tuple(
        (key, path.read_text(encoding="utf-8"))
        for key, path in paths.items()
        if key.startswith("formal/")
    )
    return cast(
        dict[str, dict[str, Any]],
        json.loads(
            _cached_theorem_analysis(tuple(_registry.BODIES.items()), formal_sources)
        ),
    )


@lru_cache(maxsize=2)
def _cached_theorem_analysis(
    topic_sources: tuple[tuple[str, str], ...],
    formal_sources: tuple[tuple[str, str], ...],
) -> str:
    """Cache immutable source-content analysis, never a mutable source/path assertion."""
    index: dict[str, dict[str, Any]] = {}
    for topic_id, body in topic_sources:
        owner = next(
            entry.source_relative_path
            for entry in BODY_MODULE_MANIFEST
            if topic_id in entry.bodies
        )
        rows = _theorem_sources(body, owner, "fep_fep" + topic_id.removeprefix("fep-"))
        if index.keys() & rows.keys():
            raise PositioningError("ambiguous canonical theorem identity")
        index.update(rows)
    for key, source in formal_sources:
        rows = _theorem_sources(source, "src/fep_lean/" + key)
        if index.keys() & rows.keys():
            raise PositioningError("ambiguous formal theorem identity")
        index.update(rows)
    short_names: dict[str, list[str]] = {}
    for name in index:
        short_names.setdefault(name.rsplit(".", 1)[-1], []).append(name)
    for name, record in index.items():
        dependencies = []
        for role, text in (
            ("statement_reference", record["statement"]),
            ("proof_reference", record.pop("proof_source")),
        ):
            tokens = sorted(set(_IDENTIFIER.findall(lean_code_without_comments(text))))
            for token in tokens:
                resolved = (
                    token if token in index else record["namespace"] + "." + token
                )
                if resolved in index and resolved != name:
                    dependencies.append(
                        {
                            "identifier": token,
                            "qualified_name": resolved,
                            "role": role,
                            "resolution": "exact or same-namespace source identifier",
                        }
                    )
                elif token in short_names and token != name.rsplit(".", 1)[-1]:
                    dependencies.append(
                        {
                            "identifier": token,
                            "role": role,
                            "resolution": "unresolved lexical scope",
                            "candidates": sorted(short_names[token]),
                        }
                    )
        record["declaration_mentions"] = dependencies
        context = record.pop("source_context")
        record["import_context"] = re.findall(
            r"(?m)^\s*(?:public\s+)?import\s+([^\n]+)",
            lean_code_without_comments(context),
        )
        record["preceding_scope_directives"] = [
            {
                "directive": match.group(1),
                "source": context[match.start() : match.end()].strip(),
                "interpretation": "Preceding source directive; active scopes and elaborated binder inclusion are not inferred.",
            }
            for match in re.finditer(
                r"(?m)^[ \t]*(include|omit)[ \t]+[^\n]+",
                lean_code_without_comments(context),
            )
        ]
        record["dependency_boundary"] = (
            "Lexical declaration mentions and import context, not elaborated or minimal proof dependencies. Unresolved names remain unresolved."
        )
    return json.dumps(dict(sorted(index.items())), ensure_ascii=False, sort_keys=True)


class StrictLoader(yaml.SafeLoader):
    """Reject duplicate YAML keys instead of silently overwriting them."""


def _mapping(loader: StrictLoader, node: yaml.MappingNode) -> dict[Any, Any]:
    result: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=True)
        if not isinstance(key, str):
            raise PositioningError("YAML mappings require text keys")
        if key in result:
            raise PositioningError(f"duplicate YAML key: {key!r}")
        result[key] = loader.construct_object(value_node, deep=True)
    return result


def load_yaml(path: Path) -> dict[str, Any]:
    """Read a mapping while preserving its semantic values and rejecting key loss."""
    try:
        result = yaml.load(path.read_text(encoding="utf-8"), Loader=StrictLoader)
    except yaml.YAMLError as exc:
        raise PositioningError(f"{path.name}: invalid YAML") from exc
    if not isinstance(result, dict):
        raise PositioningError(f"{path.name}: expected a YAML mapping")
    return result


def _unique_texts(value: Any, owner: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise PositioningError(f"{owner}: expected a nonempty list")
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise PositioningError(f"{owner}: expected nonempty text items")
    if len(value) != len(set(value)):
        raise PositioningError(f"{owner}: duplicate item")
    return value


def _text_fields(row: Mapping[str, Any], fields: Sequence[str], owner: str) -> None:
    if any(
        not isinstance(row.get(field), str) or not row[field].strip()
        for field in fields
    ):
        raise PositioningError(f"{owner}: expected nonempty text fields")


def _validate_cross_corpus(table: Any, policy: Mapping[str, Any]) -> None:
    """Validate a closed positive-assignment vocabulary and exact pinned passports."""
    fields = {
        "schema_version",
        "coordinates",
        "fep_family_features",
        "upstream_pin",
        "upstream_results",
    }
    if (
        not isinstance(table, dict)
        or set(table) != fields
        or type(table["schema_version"]) is not int
        or table["schema_version"] != 1
    ):
        raise PositioningError("cross_corpus: invalid schema or fields")
    coordinates = table["coordinates"]
    if not isinstance(coordinates, list) or not coordinates:
        raise PositioningError("cross_corpus: nonempty coordinates required")
    ids = []
    for row in coordinates:
        if not isinstance(row, dict) or set(row) != {"id", "axis_kind", "definition"}:
            raise PositioningError("cross_corpus coordinate: invalid fields")
        _text_fields(row, ("id", "axis_kind", "definition"), "cross_corpus coordinate")
        if row["axis_kind"] not in {
            "domain",
            "carrier",
            "hypothesis",
        } or not re.fullmatch(row["axis_kind"] + r":[a-z0-9-]+", row["id"]):
            raise PositioningError("cross_corpus coordinate: invalid identity or kind")
        ids.append(row["id"])
    if len(ids) != len(set(ids)):
        raise PositioningError("cross_corpus: duplicate coordinate")
    if {row["id"] for row in coordinates if row["axis_kind"] == "domain"} != {
        "domain:" + name for name in policy["domains"]
    }:
        raise PositioningError(
            "cross_corpus: domain vocabulary disagrees with family context"
        )
    families = table["fep_family_features"]
    if not isinstance(families, list):
        raise PositioningError("cross_corpus: family feature rows required")
    names = []
    by_family = {row["family"]: row for row in policy["families"]}
    for row in families:
        if not isinstance(row, dict) or set(row) != {
            "family",
            "features",
            "scope",
            "rationale",
        }:
            raise PositioningError("cross_corpus family: invalid fields")
        _text_fields(row, ("family", "scope", "rationale"), "cross_corpus family")
        names.append(row["family"])
        features = _unique_texts(row["features"], "cross_corpus family features")
        if set(features) - set(ids) or row["family"] not in by_family:
            raise PositioningError("cross_corpus: unknown family or feature")
        if {feature for feature in features if feature.startswith("domain:")} != {
            "domain:" + name for name in by_family[row["family"]]["domains"]
        }:
            raise PositioningError("cross_corpus: family domain incidence drift")
    if len(names) != len(set(names)) or set(names) != set(by_family):
        raise PositioningError(
            "cross_corpus: duplicate or incomplete family feature roster"
        )
    pin = table["upstream_pin"]
    if not isinstance(pin, dict) or set(pin) != {
        "repository_url",
        "commit",
        "license",
        "review_status",
    }:
        raise PositioningError("cross_corpus: invalid upstream pin")
    _text_fields(pin, tuple(pin), "cross_corpus pin")
    if (
        pin["repository_url"] != "https://github.com/openai/math"
        or not re.fullmatch(r"[0-9a-f]{40}", pin["commit"])
        or pin["license"] != "Apache-2.0"
    ):
        raise PositioningError(
            "cross_corpus: unsupported repository, commit, or license"
        )
    results = table["upstream_results"]
    if not isinstance(results, list) or not results:
        raise PositioningError("cross_corpus: nonempty upstream result rows required")
    names = []
    expected = {
        "id",
        "title",
        "source_url",
        "source_path",
        "source_sha256",
        "status",
        "statement",
        "carriers",
        "hypotheses",
        "features",
        "scope",
        "rationale",
    }
    for row in results:
        if not isinstance(row, dict) or set(row) != expected:
            raise PositioningError("cross_corpus upstream result: invalid fields")
        _text_fields(
            row,
            tuple(expected - {"carriers", "hypotheses", "features"}),
            "cross_corpus upstream result",
        )
        names.append(row["id"])
        if not re.fullmatch(r"[a-z][a-z0-9-]*", row["id"]) or not re.fullmatch(
            r"[0-9a-f]{64}", row["source_sha256"]
        ):
            raise PositioningError(
                "cross_corpus upstream result: invalid identity or source hash"
            )
        path = PurePosixPath(row["source_path"])
        if (
            path.is_absolute()
            or "\\" in row["source_path"]
            or re.match(r"^[A-Za-z]:", row["source_path"])
            or ".." in path.parts
            or str(path) != row["source_path"]
            or row["source_url"]
            != pin["repository_url"]
            + "/blob/"
            + pin["commit"]
            + "/"
            + row["source_path"]
        ):
            raise PositioningError(
                "cross_corpus upstream result: source URL/path does not bind the configured pin"
            )
        if row["status"] not in {
            "reviewed_source_statement_uncompiled",
            "reviewed_source_statement_compiled_upstream_only",
        }:
            raise PositioningError(
                "cross_corpus upstream result: unreviewed evidence status"
            )
        for field in ("carriers", "hypotheses", "features"):
            _unique_texts(row[field], "cross_corpus upstream " + field)
        if set(row["features"]) - set(ids):
            raise PositioningError("cross_corpus: unknown upstream feature")
    if len(names) != len(set(names)):
        raise PositioningError("cross_corpus: duplicate upstream result")


def _cross_corpus_model(
    policy: Mapping[str, Any], source_hashes: Mapping[str, str]
) -> dict[str, Any] | None:
    if "cross_corpus" not in policy:
        return None
    table = policy["cross_corpus"]
    _validate_cross_corpus(table, policy)
    coordinates = table["coordinates"]
    ids = [row["id"] for row in coordinates]
    positions = {row["family"]: row for row in policy["families"]}
    rows = [
        {
            **row,
            "id": "fep-family:" + row["family"],
            "title": row["family"],
            "kind": "fep_family_context",
            "carriers": positions[row["family"]]["carriers"],
            "evidence_status": "authored_family_union_not_per_topic_proof",
        }
        for row in table["fep_family_features"]
    ] + [
        {**row, "kind": "upstream_result", "evidence_status": row["status"]}
        for row in table["upstream_results"]
    ]
    vectors = [[int(feature in row["features"]) for feature in ids] for row in rows]
    return {
        "schema_version": 1,
        "assignment_boundary": "Positive authored feature assignments. Absence means not assigned, not logical negation. FEP rows are family unions; upstream rows are individually named result units. Hypothesis axes include stated premises and regimes, not a common proposition.",
        "upstream_pin": table["upstream_pin"],
        "input_sha256": {"positioning.yaml": source_hashes["inputs/positioning.yaml"]},
        "coordinates": coordinates,
        "rows": rows,
        "row_order": [row["id"] for row in rows],
        "vectors": vectors,
        "coordinate_weight": "Each authored coordinate has unit weight. Domain/carrier/premise groups with more coordinates contribute more potential mismatches; no hidden group normalization.",
        "projection": classical_mds(vectors),
        "relation_boundary": "Feature proximity creates no relation edge, equivalence witness, imported theorem, native evidence, or scientific promotion.",
    }


def validate_policy(
    policy: Mapping[str, Any], families: Sequence[str], resources: set[str]
) -> None:
    """Require explicit, complete family coordinates with a closed domain vocabulary."""
    if set(policy) - {
        "schema_version",
        "domains",
        "families",
        "continuous_scope",
        "cross_corpus",
    } or not {"schema_version", "domains", "families", "continuous_scope"} <= set(
        policy
    ):
        raise PositioningError("policy: unknown or missing field")
    if type(policy["schema_version"]) is not int or policy["schema_version"] != 1:
        raise PositioningError("policy: schema_version must be 1")
    domains = policy["domains"]
    if not isinstance(domains, dict) or not domains:
        raise PositioningError("policy: domains must be a nonempty mapping")
    if not all(
        isinstance(key, str)
        and key.strip()
        and isinstance(value, str)
        and value.strip()
        for key, value in domains.items()
    ):
        raise PositioningError("policy: domains need names and definitions")
    rows = policy["families"]
    if not isinstance(rows, list):
        raise PositioningError("policy: families must be a list")
    names = []
    for row in rows:
        if not isinstance(row, dict) or set(row) != POLICY_FIELDS:
            raise PositioningError("family classification: unknown or missing field")
        name = row["family"]
        if not isinstance(name, str):
            raise PositioningError("family classification: family must be text")
        names.append(name)
        for key in ("domains", "carriers", "scale"):
            _unique_texts(row[key], f"{name}.{key}")
        unknown = set(row["domains"]) - set(domains)
        if unknown:
            raise PositioningError(f"{name}: unknown domain {sorted(unknown)}")
        for key in ("topology", "embedding", "statistics", "limits"):
            if not isinstance(row[key], str) or not row[key].strip():
                raise PositioningError(f"{name}: missing {key} analysis")
    if len(names) != len(set(names)):
        raise PositioningError("policy: duplicate family")
    if set(names) != set(families):
        raise PositioningError(
            f"policy family mismatch: missing={sorted(set(families) - set(names))}; "
            f"unknown={sorted(set(names) - set(families))}"
        )
    scopes = policy["continuous_scope"]
    if not isinstance(scopes, list):
        raise PositioningError("policy: continuous_scope must be a list")
    scope_resources = []
    for row in scopes:
        if not isinstance(row, dict) or set(row) != SCOPE_FIELDS:
            raise PositioningError("continuous scope: unknown or missing field")
        for key in ("resource", "carrier", "scope"):
            if not isinstance(row[key], str) or not row[key].strip():
                raise PositioningError(f"continuous scope: {key} must be text")
        scope_resources.append(row["resource"])
        if row["resource"] not in resources:
            raise PositioningError(
                f"unmanifested continuous resource: {row['resource']}"
            )
        _unique_texts(row["domains"], row["resource"])
        if set(row["domains"]) - set(domains):
            raise PositioningError(f"{row['resource']}: unknown domain")
    if len(scope_resources) != len(set(scope_resources)):
        raise PositioningError("continuous scope: duplicate resource")
    if "cross_corpus" in policy:
        _validate_cross_corpus(policy["cross_corpus"], policy)


def qualify_theorem(topic_id: str, name: str) -> str:
    """Preserve existing qualified references, otherwise use aggregate topic scope."""
    digits = topic_id.removeprefix("fep-")
    return name if "." in name else f"fep_fep{digits}.FEP{digits}.{name}"


def validate_references(
    reviews: Sequence[Mapping[str, Any]],
    relations: Mapping[str, Any],
    known: set[str] | frozenset[str],
) -> None:
    """Reject dangling semantic, relation-witness, and capability theorem references."""
    required = set()
    for review in reviews:
        for name in (
            review["primary_theorem"],
            *review["supporting_theorems"],
            *review["boundary_theorems"],
        ):
            required.add(qualify_theorem(review["id"], name))
    for node in relations["capabilities"]:
        required.update(node.get("evidence", []))
    for edge in relations["edges"]:
        if edge["kind"] in {"formal", "formal_pairing"}:
            if not edge.get("witness"):
                raise PositioningError("theorem-backed edge missing witness")
            required.add(edge["witness"])
    missing = required - known
    if missing:
        raise PositioningError(
            f"dangling theorem references: {', '.join(sorted(missing))}"
        )


def feature_embedding(
    families: Sequence[Mapping[str, Any]], domains: Sequence[str]
) -> dict[str, Any]:
    """Return an explicit binary incidence representation, independent of Lean edges."""
    return {
        "coordinates": list(domains),
        "row_order": [row["family"] for row in families],
        "representation": "binary authored family-domain incidence",
        "distance": "1 - Jaccard similarity; every domain has equal weight",
        "interpretation": (
            "Candidates for reading and comparison only. Family unions may hide "
            "topic differences. This is not a learned text embedding, theorem "
            "implication, geometric isometry, or proof graph."
        ),
        "vectors": {
            row["family"]: [int(domain in row["domains"]) for domain in domains]
            for row in families
        },
    }


def neighbors(
    embedding: Mapping[str, Any], family: str, limit: int = 3
) -> list[dict[str, Any]]:
    """Rank incidence candidates; retain exact intersection and union cardinalities."""
    vectors = embedding["vectors"]
    if family not in vectors or limit < 1:
        raise PositioningError(
            "neighbor request needs a known family and positive limit"
        )
    origin = {i for i, value in enumerate(vectors[family]) if value}
    results = []
    for target, values in vectors.items():
        if target == family:
            continue
        candidate = {i for i, value in enumerate(values) if value}
        shared = len(origin & candidate)
        union = len(origin | candidate)
        results.append(
            {
                "family": target,
                "shared_domains": shared,
                "union_domains": union,
                "jaccard": shared / union,
            }
        )
    return sorted(results, key=lambda row: (-row["jaccard"], row["family"]))[:limit]


StrictLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping)


class SourceOrigin(str, Enum):
    """Which actual owner bytes were read for this analysis."""

    INSTALLED_PACKAGE = "installed_package"
    CHECKOUT = "checkout"


@dataclass(frozen=True)
class MathematicalPositioning:
    """Immutable analysis with validated typed contracts and detached JSON views."""

    origin: SourceOrigin
    metadata: CatalogueMetadataManifest
    theorem_maturity: TheoremMaturityAudit
    graph: FormalismGraph
    _json: str

    def as_dict(self) -> dict[str, Any]:
        """Return a fresh mutable view; changes cannot alter the retained model."""
        result: dict[str, Any] = json.loads(self._json)
        return result


def _input_paths(project_root: Path | None) -> dict[str, Path]:
    if project_root is None:
        package_data = Path(str(files("fep_lean.data")))
        return {name: package_data / name for name in RESOURCE_OWNERS}
    return {name: Path(project_root) / owner for name, owner in RESOURCE_OWNERS.items()}


def package_resource_drift(project_root: Path) -> tuple[Path, ...]:
    """Read-only byte parity between every canonical owner and its generated copy."""
    root = Path(project_root)
    return tuple(
        root / "src/fep_lean/data" / name
        for name, owner in RESOURCE_OWNERS.items()
        if not (root / "src/fep_lean/data" / name).is_file()
        or (root / "src/fep_lean/data" / name).read_bytes()
        != (root / owner).read_bytes()
    )


def _source_paths(
    project_root: Path | None, inputs: Mapping[str, Path]
) -> dict[str, Path]:
    base = (
        Path(project_root) / "src/fep_lean"
        if project_root is not None
        else Path(str(files("fep_lean")))
    )
    paths = {"inputs/" + name: path for name, path in inputs.items()}
    if project_root is None:
        # Installed mode additionally validates this generated public catalogue.
        # Source mode reads the canonical owners instead of consuming its copy.
        paths["data/topics.yaml"] = base / "data/topics.yaml"
    paths.update(
        {
            entry.source_relative_path.removeprefix("src/fep_lean/"): base
            / entry.source_relative_path.removeprefix("src/fep_lean/")
            for entry in BODY_MODULE_MANIFEST
        }
    )
    paths.update(
        {
            "formal/" + module.resource: path
            for module, path in zip(
                FORMAL_MODULES,
                formal_resource_paths(project_root=project_root),
                strict=True,
            )
        }
    )
    paths.update({name: base / name for name in (*_VALIDATOR_OWNERS, *_METHODS_OWNERS)})
    return dict(sorted(paths.items()))


def __getattr__(name: str) -> object:
    """Expose ``BODIES`` lazily so importing this module skips registry build."""
    if name == "BODIES":
        return _registry.BODIES
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def _hashes(paths: Mapping[str, Path]) -> dict[str, str]:
    return {
        name: hashlib.sha256(path.read_bytes()).hexdigest()
        for name, path in paths.items()
    }


_RUNTIME_OWNER_HASHES = {
    name: _SOURCE_RUNTIME_SHA256[name]
    for name in (
        *_VALIDATOR_OWNERS,
        *_METHODS_OWNERS,
        *(
            entry.source_relative_path.removeprefix("src/fep_lean/")
            for entry in BODY_MODULE_MANIFEST
        ),
    )
}


def _validate_runtime_owners(source_hashes: Mapping[str, str]) -> None:
    """Refuse to describe foreign or changed Python using already imported code.

    The root package snapshots owner bytes before any subpackage imports.
    Selected owners are only read, never imported or executed. Exact parity
    prevents cached validators or manifests being labeled with different owner
    bytes. This is bounded model consistency, not continuous custody, a native
    receipt, or execution attestation.
    """
    differences = [
        name
        for name, digest in _RUNTIME_OWNER_HASHES.items()
        if source_hashes.get(name) != digest
    ]
    if differences:
        raise PositioningError(
            "selected Python owners disagree with imported runtime: "
            + ", ".join(differences)
        )


def _validate_body_literals(paths: Mapping[str, Path]) -> None:
    for entry in BODY_MODULE_MANIFEST:
        key = entry.source_relative_path.removeprefix("src/fep_lean/")
        tree = ast.parse(paths[key].read_text(encoding="utf-8"))
        assignments = [
            node
            for node in tree.body
            if isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "BODIES"
        ]
        if len(assignments) != 1 or not isinstance(assignments[0].value, ast.Dict):
            raise PositioningError(f"{key}: expected one literal BODIES mapping")
        literal = assignments[0].value
        if any(item is None for item in literal.keys):
            raise PositioningError(f"{key}: unpacked body mappings are forbidden")
        keys = [ast.literal_eval(item) for item in literal.keys if item is not None]
        if len(keys) != len(set(keys)) or ast.literal_eval(literal) != entry.bodies:
            raise PositioningError(f"{key}: duplicate or drifted body literal")


def _validate_graph_contracts(graph: FormalismGraph, project_root: Path | None) -> None:
    declarations = all_formal_theorem_declarations(project_root)
    required = {ref for node in graph.capabilities for ref in node.evidence}
    required.update(edge.witness for edge in graph.edges if edge.witness is not None)
    if required - declarations:
        raise PositioningError("unresolved capability or edge-witness theorem")
    sources = composed_theorem_sources(project_root)
    for edge in graph.edges:
        if not edge.kind.is_theorem_witnessed:
            continue
        raw = sources.get(edge.witness or "")
        if raw is None:
            raise PositioningError(
                "edge witness must resolve in a manifested composition"
            )
        code = lean_code_without_comments(raw)
        if not all(
            f"fep_fep{topic.removeprefix('fep-')}." in code
            for topic in (edge.source, edge.target)
        ):
            raise PositioningError("theorem-witnessed edge lacks endpoint references")
        if (
            edge.kind is EdgeKind.FORMAL_PAIRING
            and "∧" not in lean_declaration_conclusion(raw)
        ):
            raise PositioningError("formal_pairing must expose a conjunction")


def _validate_packaged_catalogue(
    metadata: CatalogueMetadataManifest, audit: TheoremMaturityAudit
) -> None:
    catalogue = FEPTopicCatalogue.default()
    if catalogue.roster != metadata.roster or catalogue.families != metadata.families:
        raise PositioningError(
            "packaged metadata differs from packaged topic projection"
        )
    for topic, meta, review in zip(
        catalogue.topics, metadata.records, audit.records, strict=True
    ):
        expected = {
            "id": meta.id,
            "title": meta.title,
            "area": meta.area,
            "family": meta.family,
            "mathlib_modules": meta.mathlib_modules,
            "mathlib_status": meta.mathlib_status,
            "primary_theorem": review.primary_theorem,
            "supporting_theorems": review.supporting_theorems,
            "boundary_theorems": review.boundary_theorems,
            "semantic_disposition": review.disposition.value,
            "nl": render_proxy_statement(review),
            "assumption_review": review.assumption_review,
            "non_vacuity": review.non_vacuity,
            "acceptance_probe": review.acceptance_probe,
        }
        if any(getattr(topic, key) != value for key, value in expected.items()):
            raise PositioningError(
                f"{topic.id}: methods resources drift from packaged catalogue"
            )


def build_mathematical_positioning(
    project_root: Path | None = None,
) -> MathematicalPositioning:
    """Validate actual installed resources or an explicitly selected canonical checkout."""
    inputs = _input_paths(project_root)
    paths = _source_paths(project_root, inputs)
    before = _hashes(paths)
    _validate_runtime_owners(before)
    raw = {name: load_yaml(path) for name, path in inputs.items()}
    _validate_body_literals(paths)
    metadata = load_catalogue_metadata(inputs["catalogue_metadata.yaml"])
    validate_body_roster(_registry.BODIES, metadata.topic_ids)
    validate_body_family_ownership({row.id: row.family for row in metadata.records})
    audit = load_theorem_maturity(
        inputs["theorem_maturity.yaml"],
        bodies=_registry.BODIES,
        roster_ids=metadata.topic_ids,
    )
    graph = load_formalism_graph(
        inputs["formalism_relations.yaml"], roster_ids=metadata.topic_ids
    )
    policy = raw["positioning.yaml"]
    validate_policy(
        policy, metadata.families, {module.resource for module in FORMAL_MODULES}
    )
    _validate_graph_contracts(graph, project_root)
    validate_references(
        raw["theorem_maturity.yaml"]["topics"],
        raw["formalism_relations.yaml"],
        all_formal_theorem_declarations(project_root),
    )
    if project_root is None:
        _validate_packaged_catalogue(metadata, audit)
    gap_ids = {
        row.id
        for row in audit.records
        if row.disposition.value in {"scope_gap", "assumption_gap"}
    }
    blocked = {edge.source for edge in graph.edges if edge.kind is EdgeKind.BLOCKED_BY}
    formalized = {
        row.id for row in audit.records if row.disposition.value == "formalized"
    }
    if gap_ids - blocked or formalized & blocked:
        raise PositioningError("semantic gap and blocked_by graph disagree")
    reviews = {row["id"]: row for row in raw["theorem_maturity.yaml"]["topics"]}
    contexts = {row["family"]: row for row in policy["families"]}
    theorem_analysis = _theorem_analysis_index(paths)
    if set(theorem_analysis) != all_formal_theorem_declarations(project_root):
        raise PositioningError(
            "theorem-analysis declaration roster disagrees with canonical resolution"
        )
    ownership = {
        topic_id: entry.source_relative_path
        for entry in BODY_MODULE_MANIFEST
        for topic_id in entry.bodies
    }
    topics = []
    for row in raw["catalogue_metadata.yaml"]["topics"]:
        topic_id, review = row["id"], reviews[row["id"]]
        digits = topic_id.removeprefix("fep-")
        topics.append(
            {
                **row,
                "semantic_review": review,
                "canonical_namespace": f"FEP{digits}",
                "aggregate_namespace": f"fep_fep{digits}.FEP{digits}",
                "primary_theorem_qualified": qualify_theorem(
                    topic_id, review["primary_theorem"]
                ),
                "reviewed_theorems_qualified": {
                    key: [qualify_theorem(topic_id, name) for name in review[key]]
                    for key in ("supporting_theorems", "boundary_theorems")
                },
                "mathematical_context": {
                    "classification_scope": "inherited_family_context",
                    "domains": contexts[row["family"]]["domains"],
                    "interpretation": "Editorial family union; exact topic claims remain in the semantic contract.",
                },
                "body_source": ownership[topic_id],
                "canonical_body_sha256": hashlib.sha256(
                    _registry.BODIES[topic_id].encode()
                ).hexdigest(),
                "body_theorem_count": len(
                    LEAN_THEOREM_RE.findall(
                        lean_code_without_comments(_registry.BODIES[topic_id])
                    )
                ),
            }
        )
    modules = formal_theorem_modules(project_root)
    inventory = [
        {
            "resource": module.resource,
            "lean_module": module.lean_module,
            "role": module.role.value,
            "declaration_namespace": module.declaration_namespace,
            "theorem_count": sum(
                value == module.lean_module for value in modules.values()
            ),
        }
        for module in FORMAL_MODULES
    ]
    embedding = feature_embedding(policy["families"], list(policy["domains"]))
    cross_corpus = _cross_corpus_model(policy, before)
    origin = (
        SourceOrigin.CHECKOUT
        if project_root is not None
        else SourceOrigin.INSTALLED_PACKAGE
    )
    if before != _hashes(paths):
        raise PositioningError("source changed during methods analysis")
    document = {
        "schema_version": 1,
        "package_version": __version__,
        "source_origin": origin.value,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "counts": {
            "topics": len(topics),
            "families": len(policy["families"]),
            "domains": len(policy["domains"]),
            "authored_edges": len(graph.edges),
            "capabilities": len(graph.capabilities),
            "formal_modules": len(inventory),
            "relation_kinds": dict(
                sorted(Counter(edge.kind.value for edge in graph.edges).items())
            ),
            "semantic_dispositions": audit.disposition_counts,
        },
        "source_sha256": before,
        "domains": policy["domains"],
        "family_positions": policy["families"],
        "continuous_scope": policy["continuous_scope"],
        "formal_inventory": inventory,
        "semantic_policy": {
            key: value
            for key, value in raw["theorem_maturity.yaml"].items()
            if key != "topics"
        },
        "topics": topics,
        "theorem_analysis": {
            "analysis_boundary": ANALYSIS_BOUNDARY,
            "declarations": theorem_analysis,
            "reviewed_topic_count": len(topics),
        },
        "authored_relations": raw["formalism_relations.yaml"],
        "feature_embedding": embedding,
        "cross_corpus_embedding": cross_corpus,
        "retrieval_candidates": {
            row["family"]: neighbors(embedding, row["family"])
            for row in policy["families"]
        },
        "numerical_probes": evaluate_boundary_probes(),
    }
    return MathematicalPositioning(
        origin,
        metadata,
        audit,
        graph,
        json.dumps(document, ensure_ascii=False, sort_keys=True, allow_nan=False),
    )


def inspect_topic(model: MathematicalPositioning, topic_id: str) -> dict[str, Any]:
    """Read one exact contract; reject unknown identities."""
    for row in model.as_dict()["topics"]:
        if row["id"] == topic_id:
            return cast(dict[str, Any], row)
    raise PositioningError(f"unknown topic: {topic_id}")


def inspect_theorem(
    model: MathematicalPositioning, qualified_name: str
) -> dict[str, Any]:
    """Read one unambiguous exact source declaration; never guess short-name scope."""
    declarations = model.as_dict()["theorem_analysis"]["declarations"]
    if qualified_name not in declarations:
        raise PositioningError(f"unknown fully qualified theorem: {qualified_name}")
    return cast(dict[str, Any], declarations[qualified_name])


def analyze_topic(model: MathematicalPositioning, topic_id: str) -> dict[str, Any]:
    """Join exact source syntax and maintained prose without promoting either."""
    topic = inspect_topic(model, topic_id)
    review = topic["semantic_review"]
    return {
        "topic_id": topic_id,
        "analysis_boundary": ANALYSIS_BOUNDARY,
        "primary": inspect_theorem(model, topic["primary_theorem_qualified"]),
        "supporting": [
            inspect_theorem(model, name)
            for name in topic["reviewed_theorems_qualified"]["supporting_theorems"]
        ],
        "boundary": [
            inspect_theorem(model, name)
            for name in topic["reviewed_theorems_qualified"]["boundary_theorems"]
        ],
        "maintained_semantic_analysis": {
            "source_owner": "config/theorem_maturity.yaml",
            "disposition": review["disposition"],
            "invariant": review["invariant"],
            "assumption_review": review["assumption_review"],
            "non_vacuity": review["non_vacuity"],
            "acceptance_probe": review["acceptance_probe"],
            "rendered_prose": f"{review['invariant']} Assumption scope: {review['assumption_review']} Semantic disposition: `{review['disposition']}`.",
            "interpretation": "Maintained source-grounded prose; no certified natural-language equivalence or new scientific review is inferred.",
        },
    }


def cross_corpus_embedding(model: MathematicalPositioning) -> dict[str, Any]:
    """Read the common authored mathematical coordinates and their diagnostic MDS."""
    result = model.as_dict()["cross_corpus_embedding"]
    if result is None:
        raise PositioningError("cross-corpus coordinate table is not configured")
    return cast(dict[str, Any], result)


def inspect_family(model: MathematicalPositioning, family: str) -> dict[str, Any]:
    """Read authored family context together with its exact topic IDs."""
    data = model.as_dict()
    for row in data["family_positions"]:
        if row["family"] == family:
            return {
                **row,
                "topic_ids": [
                    topic["id"] for topic in data["topics"] if topic["family"] == family
                ],
            }
    raise PositioningError(f"unknown family: {family}")


def positioning_neighbors(
    model: MathematicalPositioning, family: str, limit: int = 3
) -> list[dict[str, Any]]:
    """Read feature-space comparison candidates, independent of authored edges."""
    return neighbors(model.as_dict()["feature_embedding"], family, limit)
