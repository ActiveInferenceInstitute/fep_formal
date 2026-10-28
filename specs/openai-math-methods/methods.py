"""Offline mathematical positioning of canonical FEP Formal sources.

This projection is interpretive analysis, never a native compilation receipt.
The upstream OpenAI math corpus is intentionally not executed or imported.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import io
import json
import math
import sys
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

# A direct projection/check invocation must not update checkout-local bytecode.
if __name__ == "__main__":
    sys.dont_write_bytecode = True

import yaml

from fep_formal.catalogue.coverage import build_formalism_coverage
from fep_formal.catalogue.registry import BODIES, BODY_MODULE_MANIFEST
from fep_formal.catalogue.schema import load_catalogue_metadata
from fep_formal.catalogue.semantics import load_theorem_maturity
from fep_formal.formal.declarations import (
    all_formal_theorem_declarations,
    formal_theorem_modules,
)
from fep_formal.formal.manifest import FORMAL_MODULES, formal_resource_paths
from fep_formal.lean_source import LEAN_THEOREM_RE, lean_code_without_comments

ROOT = Path(__file__).resolve().parents[2]
SLICE = Path("specs/openai-math-methods")
OUTPUTS = (
    SLICE / "positioning.json",
    SLICE / "positioning.md",
    SLICE / "family-domains.svg",
)
EVIDENCE_BOUNDARY = (
    "Offline source-text projection and authored interpretive taxonomy. "
    "Theorem addresses resolve to declarations; no compiler, Hermes, OpenGauss, "
    "live account, H3/Q7 gate, or upstream research proof is executed. "
    "Counts, numeric probes, and feature distances are informational. "
    "Existing semantic dispositions are copied, never promoted."
)
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


class PositioningError(ValueError):
    """An input or projection failed the slice's bounded contract."""


class StrictLoader(yaml.SafeLoader):
    """Reject duplicate YAML keys instead of silently overwriting them."""


def _mapping(loader: StrictLoader, node: yaml.MappingNode) -> dict[Any, Any]:
    result: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=True)
        if key in result:
            raise PositioningError(f"duplicate YAML key: {key!r}")
        result[key] = loader.construct_object(value_node, deep=True)
    return result


StrictLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping)


def load_yaml(path: Path) -> dict[str, Any]:
    """Read a mapping while preserving its semantic values and rejecting key loss."""
    result = yaml.load(path.read_text(encoding="utf-8"), Loader=StrictLoader)
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
    if policy["schema_version"] != 1:
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


def feature_embedding(families: Sequence[Mapping[str, Any]], domains: Sequence[str]):
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


def neighbors(embedding: Mapping[str, Any], family: str, limit: int = 3):
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


def bernoulli_fisher(parameter: float) -> float:
    """Evaluate the regular interior Bernoulli Fisher weight; reject singular endpoints."""
    if not math.isfinite(parameter) or not 0 < parameter < 1:
        raise PositioningError("Bernoulli Fisher needs 0 < p < 1")
    information = 1 / (parameter * (1 - parameter))
    if not math.isfinite(information):
        raise PositioningError(
            "interior Bernoulli Fisher exceeds the representable float range"
        )
    return information


def _law_pair(p: Sequence[float], q: Sequence[float]) -> None:
    if not p or len(p) != len(q):
        raise PositioningError("law comparison needs equal nonempty supports")
    for law in (p, q):
        if any(not math.isfinite(x) or x < 0 for x in law) or not math.isclose(
            math.fsum(law), 1, rel_tol=0, abs_tol=1e-12
        ):
            raise PositioningError("numeric law must be normalized and nonnegative")


def finite_kl_totalized(p: Sequence[float], q: Sequence[float]) -> float:
    """Mirror q*klFun(p/q), with totalized division, for an explanatory probe."""
    _law_pair(p, q)
    terms = []
    for source, reference in zip(p, q, strict=True):
        if reference == 0:
            terms.append(0.0)
        elif source == 0:
            terms.append(reference)
        else:
            # Algebraically the same supported integrand without ratio overflow.
            log_ratio = math.log(source) - math.log(reference)
            terms.append(math.fsum((source * log_ratio, -source, reference)))
    return math.fsum(terms)


def extended_kl(p: Sequence[float], q: Sequence[float]) -> float:
    """Conventional extended-real discrete KL with its support-failure boundary."""
    _law_pair(p, q)
    if any(
        source > 0 and reference == 0 for source, reference in zip(p, q, strict=True)
    ):
        return math.inf
    return math.fsum(
        source * (math.log(source) - math.log(reference))
        for source, reference in zip(p, q, strict=True)
        if source > 0
    )


def numerical_probes() -> list[dict[str, Any]]:
    """Expose four finite diagnostic examples without claiming native verification."""
    extended_boundary = extended_kl((1.0, 0.0), (0.0, 1.0))
    law = [1 / 3, 1 / 3, 1 / 3]
    tangent = [1, -1, 0]
    return [
        {
            "id": "bernoulli-interior",
            "parameters": [0.5, 0.25, 0.01],
            "fisher": [bernoulli_fisher(p) for p in (0.5, 0.25, 0.01)],
            "boundary": "p=0 and p=1 rejected; no regular Fisher endpoint is inferred",
            "reading_anchor": "fep_fep038.FEP038.fep038_fisherMetric",
        },
        {
            "id": "kl-support-boundary",
            "source": [1.0, 0.0],
            "reference": [0.0, 1.0],
            "totalized_finite_kl": finite_kl_totalized((1.0, 0.0), (0.0, 1.0)),
            "extended_discrete_kl": "infinity"
            if math.isinf(extended_boundary)
            else extended_boundary,
            "interpretation": "Finite totalized KL cannot be substituted for native KL at disjoint support.",
            "reading_anchor": "FEP.FiniteInformation.finiteKL_disjoint_pointMass_totalized",
        },
        {
            "id": "fisher-chart-degeneracy",
            "law": law,
            "redundant_logit_information": [
                [2 / 9 if i == j else -1 / 9 for j in range(3)] for i in range(3)
            ],
            "logit_null_direction": [1, 1, 1],
            "simplex_tangent": tangent,
            "law_coordinate_tangent_norm_squared": sum(
                v * v / p for v, p in zip(tangent, law, strict=True)
            ),
            "interpretation": (
                "The redundant common-logit offset is null; the law-coordinate "
                "metric sum(v_i^2/p_i) is positive on this nonzero mass-zero tangent. "
                "These are different coordinate representations of the same family."
            ),
            "reading_anchor": "src/fep_formal/formal/geometric_optimization.lean",
        },
        {
            "id": "descent-does-not-identify",
            "objective": "f(x,y)=x^2",
            "update": "(x,y) -> (x/2,y)",
            "initial_states": [[1, 0], [1, 9]],
            "energy_sequence": [4.0 ** (-step) for step in range(6)],
            "distinct_limit_states": [[0, 0], [0, 9]],
            "interpretation": (
                "Both trajectories decrease the same objective but retain distinct "
                "unobserved coordinates. Descent alone does not establish "
                "identifiability or a unique state."
            ),
            "reading_anchor": "fep-032 exact scalar convergence versus additional latent coordinates",
        },
    ]


def source_paths(root: Path) -> tuple[Path, ...]:
    """Bind data, canonical owners, validators, and all manifested formal resources."""
    relative = [
        "config/catalogue_metadata.yaml",
        "config/theorem_maturity.yaml",
        "config/formalism_relations.yaml",
        str(SLICE / "positioning.yaml"),
        str(SLICE / "methods.py"),
        "src/fep_formal/catalogue/registry.py",
        "src/fep_formal/catalogue/schema.py",
        "src/fep_formal/catalogue/semantics.py",
        "src/fep_formal/catalogue/relations.py",
        "src/fep_formal/catalogue/coverage.py",
        "src/fep_formal/formal/declarations.py",
        "src/fep_formal/formal/manifest.py",
        "src/fep_formal/lean_source.py",
        *(entry.source_relative_path for entry in BODY_MODULE_MANIFEST),
    ]
    return tuple(
        sorted(
            {
                *(root / name for name in relative),
                *formal_resource_paths(project_root=root),
            }
        )
    )


def source_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in source_paths(root)
    }


def validate_body_sources(root: Path, manifest=BODY_MODULE_MANIFEST) -> None:
    """Ensure literal owner bytes match imported bodies; never execute an owner file."""
    for entry in manifest:
        path = root / entry.source_relative_path
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        assignments = [
            node
            for node in tree.body
            if isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "BODIES"
        ]
        if len(assignments) != 1 or not isinstance(assignments[0].value, ast.Dict):
            raise PositioningError(
                f"{entry.source_relative_path}: expected one literal BODIES mapping"
            )
        literal = assignments[0].value
        keys = [ast.literal_eval(key) for key in literal.keys]
        if len(keys) != len(set(keys)):
            raise PositioningError(
                f"{entry.source_relative_path}: duplicate literal body key"
            )
        if ast.literal_eval(literal) != entry.bodies:
            raise PositioningError(
                f"{entry.source_relative_path}: owner bytes and imported bodies differ"
            )


def build_model(root: Path = ROOT) -> dict[str, Any]:
    """Validate canonical sources, then join their unchanged statements to the taxonomy."""
    before = source_hashes(root)
    validate_body_sources(root)
    metadata = load_catalogue_metadata(root / "config/catalogue_metadata.yaml")
    policy = load_yaml(root / SLICE / "positioning.yaml")
    semantics = load_yaml(root / "config/theorem_maturity.yaml")
    relations = load_yaml(root / "config/formalism_relations.yaml")
    load_yaml(root / "config/catalogue_metadata.yaml")
    load_theorem_maturity(
        root / "config/theorem_maturity.yaml",
        bodies=BODIES,
        roster_ids=metadata.topic_ids,
    )
    validate_policy(
        policy, metadata.families, {module.resource for module in FORMAL_MODULES}
    )
    # Reuse the maintained graph's endpoint, conjunction, gap, and ownership checks.
    build_formalism_coverage(root)
    validate_references(
        semantics["topics"], relations, all_formal_theorem_declarations(root)
    )
    reviews = {row["id"]: row for row in semantics["topics"]}
    contexts = {row["family"]: row for row in policy["families"]}
    ownership = {
        topic_id: entry.source_relative_path
        for entry in BODY_MODULE_MANIFEST
        for topic_id in entry.bodies
    }
    rows = []
    for metadata_row in load_yaml(root / "config/catalogue_metadata.yaml")["topics"]:
        topic_id = metadata_row["id"]
        review = reviews[topic_id]
        digits = topic_id.removeprefix("fep-")
        rows.append(
            {
                **metadata_row,
                "semantic_review": review,
                "mathematical_context": {
                    "classification_scope": "inherited_family_context",
                    "domains": contexts[metadata_row["family"]]["domains"],
                    "interpretation": "Editorial family union; exact topic claims are the semantic review and qualified theorem contracts.",
                },
                "canonical_namespace": f"FEP{digits}",
                "aggregate_namespace": f"fep_fep{digits}.FEP{digits}",
                "primary_theorem_qualified": qualify_theorem(
                    topic_id, review["primary_theorem"]
                ),
                "reviewed_theorems_qualified": {
                    key: [qualify_theorem(topic_id, name) for name in review[key]]
                    for key in ("supporting_theorems", "boundary_theorems")
                },
                "body_source": ownership[topic_id],
                "canonical_body_sha256": hashlib.sha256(
                    BODIES[topic_id].encode()
                ).hexdigest(),
                "body_theorem_count": len(
                    LEAN_THEOREM_RE.findall(
                        lean_code_without_comments(BODIES[topic_id])
                    )
                ),
            }
        )
    modules = formal_theorem_modules(root)
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
    after = source_hashes(root)
    if before != after:
        raise PositioningError(
            "source changed during projection; rerun after edits finish"
        )
    return {
        "schema_version": 1,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "counts": {
            "topics": len(rows),
            "families": len(policy["families"]),
            "domains": len(policy["domains"]),
            "authored_edges": len(relations["edges"]),
            "relation_kinds": dict(
                sorted(Counter(edge["kind"] for edge in relations["edges"]).items())
            ),
            "semantic_dispositions": dict(
                sorted(
                    Counter(
                        review["disposition"] for review in reviews.values()
                    ).items()
                )
            ),
            "formal_modules": len(inventory),
            "capabilities": len(relations["capabilities"]),
        },
        "source_sha256": before,
        "domains": policy["domains"],
        "family_positions": policy["families"],
        "continuous_scope": policy["continuous_scope"],
        "formal_inventory": inventory,
        "semantic_policy": {
            key: value for key, value in semantics.items() if key != "topics"
        },
        "topics": rows,
        "authored_relations": relations,
        "feature_embedding": embedding,
        "retrieval_candidates": {
            row["family"]: neighbors(embedding, row["family"])
            for row in policy["families"]
        },
        "numerical_probes": numerical_probes(),
    }


def _cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_markdown(model: Mapping[str, Any]) -> str:
    """Project all family axes and every canonical review without truncating assumptions."""
    counts = model["counts"]
    lines = [
        "# Mathematical positioning of FEP Formal",
        "",
        "Generated by `methods.py` from canonical sources and `positioning.yaml`.",
        "",
        model["evidence_boundary"],
        "",
        (
            f"The projection contains {counts['topics']} topics, {counts['families']} families, "
            f"{counts['domains']} overlapping domains, and {counts['authored_edges']} authored relations."
        ),
        "",
        "## Family coordinates",
        "",
        (
            "The classifications summarize reviewed invariants and carrier assumptions. "
            "A family domain is a union of its rows' concerns; each topic's exact scope follows below. "
            "Topic domain lists explicitly carry `inherited_family_context`, an editorial label rather than a semantic certification."
        ),
        "",
        "| Family | Topics | Mathematical domains |",
        "| --- | ---: | --- |",
    ]
    for family in model["family_positions"]:
        number = sum(topic["family"] == family["family"] for topic in model["topics"])
        lines.append(
            f"| {_cell(family['family'])} | {number} | {_cell(', '.join(family['domains']))} |"
        )
    for family in model["family_positions"]:
        lines.extend(
            [
                "",
                f"### {family['family']}",
                "",
                f"Carriers: {'; '.join(family['carriers'])}.",
                "",
                f"Scale: {'; '.join(family['scale'])}.",
            ]
        )
        for field, label in (
            ("topology", "Topology"),
            ("embedding", "Embedding"),
            ("statistics", "Statistics"),
            ("limits", "Boundary"),
        ):
            lines.extend(["", f"{label}: {family[field]}"])
    lines.extend(
        [
            "",
            "## Continuous native scope beyond catalogue families",
            "",
            (
                "These selected authored scope notes concern manifested source modules. "
                "The complete inventory is in the JSON projection. Listing a declaration "
                "here does not validate a native receipt or close its scientific acceptance gates."
            ),
        ]
    )
    for scope in model["continuous_scope"]:
        lines.extend(
            ["", f"### `{scope['resource']}`", "", scope["carrier"], "", scope["scope"]]
        )
    lines.extend(
        [
            "",
            "## Explicit feature space",
            "",
            model["feature_embedding"]["interpretation"],
            "",
            (
                "Each family is a binary vector in the ordered domain vocabulary. "
                "Similarity is shared domains divided by union domains, with equal weights. "
                "The candidates below are separate from all authored theorem relations."
            ),
            "",
            "| Family | First comparison candidate | Shared / union |",
            "| --- | --- | --- |",
        ]
    )
    for family in model["feature_embedding"]["row_order"]:
        candidates = model["retrieval_candidates"][family]
        first = candidates[0]
        lines.append(
            f"| {family} | {first['family']} | {first['shared_domains']} / {first['union_domains']} |"
        )
    lines.extend(["", "## Numerical boundary probes", ""])
    for probe in model["numerical_probes"]:
        lines.extend(
            [
                f"### {probe['id']}",
                "",
                "```json",
                json.dumps(
                    probe, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False
                ),
                "```",
                "",
            ]
        )
    lines.extend(
        [
            "## Exact topic review projection",
            "",
            (
                "Invariants, assumptions, non-vacuity, acceptance probes, and dispositions "
                "are copied from the maintained semantic review. The acceptance-probe text "
                "describes its canonical requirement; this module does not run it."
            ),
        ]
    )
    for topic in model["topics"]:
        review = topic["semantic_review"]
        lines.extend(
            [
                "",
                f"### {topic['id']}: {topic['title']}",
                "",
                f"Family: `{topic['family']}`. Disposition: `{review['disposition']}`.",
                "",
                f"Primary theorem: `{topic['primary_theorem_qualified']}`.",
                "",
                f"Body owner: `{topic['body_source']}`; canonical namespace `{topic['canonical_namespace']}`.",
            ]
        )
        for field, label in (
            ("invariant", "Invariant"),
            ("assumption_review", "Assumptions"),
            ("non_vacuity", "Non-vacuity"),
            ("acceptance_probe", "Canonical acceptance probe"),
        ):
            lines.extend(["", f"{label}: {review[field]}"])
        for field, label in (
            ("supporting_theorems", "Supporting"),
            ("boundary_theorems", "Boundary"),
        ):
            refs = topic["reviewed_theorems_qualified"][field]
            lines.extend(
                [
                    "",
                    f"{label} theorems: "
                    + (
                        ", ".join(f"`{ref}`" for ref in refs)
                        if refs
                        else "none recorded"
                    )
                    + ".",
                ]
            )
    lines.extend(
        [
            "",
            "## Authored relations",
            "",
            (
                "Every edge is retained in authored order and with its original kind, rationale, "
                "and witness. `formal` and `formal_pairing` remain distinct; a conceptual edge "
                "does not gain a witness through this taxonomy. Capabilities and evidence "
                "lists are preserved completely in JSON."
            ),
            "",
        ]
    )
    for edge in model["authored_relations"]["edges"]:
        lines.extend(
            [
                f"- `{edge['source']}` → `{edge['target']}` ({edge['kind']}): {edge['rationale']}"
                + (f" Witness: `{edge['witness']}`." if "witness" in edge else ""),
                "",
            ]
        )
    lines.extend(
        [
            "## Source snapshots",
            "",
            (
                "SHA-256 values bind the bytes read for this informational projection. "
                "They are not a native receipt or continuous consumption-custody assertion."
            ),
            "",
            "| Source | SHA-256 |",
            "| --- | --- |",
        ]
    )
    lines.extend(
        f"| `{path}` | `{digest}` |" for path, digest in model["source_sha256"].items()
    )
    return "\n".join(lines) + "\n"


def projection_bytes(model: Mapping[str, Any]) -> dict[Path, bytes]:
    return {
        OUTPUTS[0]: (
            json.dumps(
                model, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False
            )
            + "\n"
        ).encode(),
        OUTPUTS[1]: render_markdown(model).encode(),
        OUTPUTS[2]: render_family_domains(model),
    }


def render_family_domains(model: Mapping[str, Any]) -> bytes:
    """Render the same editorial binary incidence model with deterministic SVG metadata."""
    from matplotlib import rc_context
    from matplotlib.colors import ListedColormap
    from matplotlib.figure import Figure
    from matplotlib.patches import Patch

    embedding = model["feature_embedding"]
    domains = embedding["coordinates"]
    families = embedding["row_order"]
    values = [embedding["vectors"][family] for family in families]
    title = "FEP Formal family–domain incidence"
    description = (
        "Editorial family context, not per-topic proof classification. "
        "The 22 rows are canonical families and the columns are authored mathematical "
        "domains. Teal marks a family-domain association; white marks no label. "
        "All values and precise topic contracts are available in positioning.md and positioning.json."
    )
    with rc_context(
        {
            "svg.hashsalt": "fep-formal-editorial-family-domain-v1",
            "font.family": "DejaVu Sans",
            "svg.fonttype": "none",
        }
    ):
        figure = Figure(figsize=(15, 10), layout="constrained")
        axis = figure.subplots()
        axis.pcolormesh(
            values,
            cmap=ListedColormap(["#ffffff", "#087e8b"]),
            vmin=0,
            vmax=1,
            shading="flat",
            edgecolors="#d8dfe3",
            linewidth=0.65,
        )
        axis.invert_yaxis()
        axis.set_xticks(
            [index + 0.5 for index in range(len(domains))],
            labels=domains,
            rotation=45,
            ha="right",
            rotation_mode="anchor",
            fontsize=9,
        )
        axis.set_yticks(
            [index + 0.5 for index in range(len(families))], labels=families, fontsize=9
        )
        axis.set_title(
            title
            + "\nEditorial family context • binary labels • no per-topic proof certification",
            fontsize=15,
            pad=18,
        )
        axis.legend(
            handles=[
                Patch(
                    facecolor="#087e8b",
                    edgecolor="#d8dfe3",
                    label="Authored family association",
                ),
                Patch(
                    facecolor="#ffffff", edgecolor="#d8dfe3", label="No family label"
                ),
            ],
            loc="upper center",
            bbox_to_anchor=(0.5, -0.22),
            ncol=2,
            frameon=False,
        )
        buffer = io.BytesIO()
        figure.savefig(
            buffer,
            format="svg",
            metadata={"Date": None, "Title": title, "Description": description},
        )
    svg = buffer.getvalue().decode()
    svg = svg.replace(
        "<svg ",
        '<svg role="img" aria-labelledby="family-domains-title family-domains-desc" ',
        1,
    )
    header_end = svg.index(">", svg.index("<svg ")) + 1
    accessible = f'\n <title id="family-domains-title">{title}</title>\n <desc id="family-domains-desc">{description}</desc>'
    return (svg[:header_end] + accessible + svg[header_end:]).encode()


def check_projections(root: Path, expected: Mapping[Path, bytes]) -> list[str]:
    """Compare retained artifacts without writing, repairing, or creating directories."""
    return [
        str(path)
        for path, content in expected.items()
        if not (root / path).is_file() or (root / path).read_bytes() != content
    ]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="read-only artifact freshness check"
    )
    parser.add_argument(
        "--neighbors", metavar="FAMILY", help="print incidence comparison candidates"
    )
    parser.add_argument("--limit", type=int, default=3)
    args = parser.parse_args(argv)
    if sys.version_info[:2] != (3, 14):
        parser.error("the repository validator contract requires Python 3.14")
    if args.check and args.neighbors:
        parser.error("choose --check or --neighbors")
    try:
        model = build_model()
        if args.neighbors:
            print(
                json.dumps(
                    neighbors(model["feature_embedding"], args.neighbors, args.limit),
                    indent=2,
                )
            )
            return 0
        projections = projection_bytes(model)
        if args.check:
            drift = check_projections(ROOT, projections)
            if drift:
                raise PositioningError("projection drift: " + ", ".join(drift))
            print(
                "mathematical positioning projections are current (offline analysis only)"
            )
        else:
            for path, content in projections.items():
                (ROOT / path).write_bytes(content)
            print("wrote mathematical positioning projections (offline analysis only)")
        return 0
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"positioning failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
