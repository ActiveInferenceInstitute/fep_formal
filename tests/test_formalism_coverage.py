"""Generated formalism coverage is complete and conserves source counts."""

from __future__ import annotations

import shutil
from collections import Counter
from pathlib import Path

import pytest
import yaml

from fep_lean.catalogue.coverage import (
    build_formalism_coverage,
    formalism_coverage_drift,
    render_formalism_coverage_json,
    render_formalism_coverage_markdown,
    write_formalism_coverage,
)
from fep_lean.catalogue.registry import BODIES
from fep_lean.catalogue.relations import (
    CapabilityStatus,
    EdgeKind,
    load_formalism_graph,
)
from fep_lean.catalogue.schema import load_catalogue_metadata
from fep_lean.formal.declarations import (
    composed_theorem_declarations,
    formal_theorem_modules,
)
from fep_lean.formal.manifest import FORMAL_MODULES, FormalModuleRole

PROJ = Path(__file__).resolve().parent.parent


def _copy_coverage_sources(destination: Path) -> None:
    config_dir = destination / "config"
    config_dir.mkdir()
    for name in (
        "catalogue_metadata.yaml",
        "theorem_maturity.yaml",
        "formalism_relations.yaml",
    ):
        shutil.copyfile(PROJ / "config" / name, config_dir / name)
    shutil.copytree(
        PROJ / "src" / "fep_lean" / "formal",
        destination / "src" / "fep_lean" / "formal",
    )


def test_formalism_coverage_counts_canonical_breadth_and_depth() -> None:
    coverage = build_formalism_coverage(PROJ)
    metrics = coverage["metrics"]
    metadata = load_catalogue_metadata(PROJ / "config" / "catalogue_metadata.yaml")
    graph = load_formalism_graph(
        PROJ / "config" / "formalism_relations.yaml",
        roster_ids=metadata.topic_ids,
    )
    topic_rows = coverage["topics"]
    formal_module_rows = coverage["formal_modules"]
    relation_counts = Counter(edge.kind.value for edge in graph.edges)
    capability_status_counts = Counter(node.status.value for node in graph.capabilities)

    assert metrics["topics"] == len(metadata.records) == len(BODIES)
    assert metrics["formal_modules"] == len(FORMAL_MODULES) == len(formal_module_rows)
    assert metrics["foundation_modules"] == sum(
        module.role is FormalModuleRole.FOUNDATION for module in FORMAL_MODULES
    )
    assert metrics["topic_theorems"] == sum(row["theorem_count"] for row in topic_rows)
    assert metrics["formal_resource_theorems"] == sum(
        row["theorem_count"] for row in formal_module_rows
    )
    assert metrics["foundation_theorems"] == sum(
        row["theorem_count"]
        for row in formal_module_rows
        if row["role"] == FormalModuleRole.FOUNDATION.value
    )
    assert metrics["theorems"] == (
        metrics["topic_theorems"] + metrics["formal_resource_theorems"]
    )
    assert metrics["topic_definitions"] == sum(
        row["definition_count"] for row in topic_rows
    )
    assert metrics["formal_resource_definitions"] == sum(
        row["definition_count"] for row in formal_module_rows
    )
    assert metrics["definitions"] == (
        metrics["topic_definitions"] + metrics["formal_resource_definitions"]
    )
    assert metrics["topic_abbreviations"] == sum(
        row["abbreviation_count"] for row in topic_rows
    )
    assert metrics["formal_resource_abbreviations"] == sum(
        row["abbreviation_count"] for row in formal_module_rows
    )
    assert metrics["abbreviations"] == (
        metrics["topic_abbreviations"] + metrics["formal_resource_abbreviations"]
    )
    assert metrics["formal_resource_structures"] == sum(
        row["structure_count"] for row in formal_module_rows
    )
    assert metrics["distinct_mathlib_imports"] == len(
        {module for row in topic_rows for module in row["imports"]}
    )
    assert metrics["topic_import_edges"] == sum(
        len(row["imports"]) for row in topic_rows
    )
    assert metrics["formal_module_import_edges"] == sum(
        len(row["imports"]) for row in formal_module_rows
    )
    assert metrics["formal_module_dependency_edges"] == sum(
        len(row["formal_dependencies"]) for row in formal_module_rows
    )
    assert metrics["authored_relation_edges"] == len(graph.edges)
    assert metrics["formal_relation_witnesses"] == relation_counts["formal"]
    assert metrics["formal_pairing_witnesses"] == relation_counts["formal_pairing"]
    assert metrics["theorem_witnessed_relations"] == sum(
        relation_counts[kind.value] for kind in EdgeKind if kind.is_theorem_witnessed
    )
    assert metrics["composed_theorems"] == len(composed_theorem_declarations(PROJ))
    assert metrics["capability_nodes"] == len(graph.capabilities)
    assert metrics["open_capabilities"] == sum(
        node.status is not CapabilityStatus.SATISFIED for node in graph.capabilities
    )
    assert metrics["satisfied_capabilities"] == capability_status_counts["satisfied"]

    assert coverage["disposition_counts"] == dict(
        sorted(Counter(row["semantic_disposition"] for row in topic_rows).items())
    )
    assert sum(coverage["disposition_counts"].values()) == metrics["topics"]
    assert len(topic_rows) == metrics["topics"]
    assert all(row["primary_theorem"] for row in coverage["topics"])
    assert all(row["assumption_review"] for row in coverage["topics"])
    assert coverage["relation_counts"] == dict(sorted(relation_counts.items()))
    assert coverage["capability_status_counts"] == dict(
        sorted(capability_status_counts.items())
    )
    assert len(coverage["capabilities"]) == metrics["capability_nodes"]
    assert all(
        node["blocked_topics"] or node["status"] == "satisfied"
        for node in coverage["capabilities"]
    )

    markdown = render_formalism_coverage_markdown(coverage)
    assert "## Authored formalism relations" in markdown
    assert "## Maintained formal kernel" in markdown
    assert "## Capability roster" in markdown
    assert "Shared imports never create these edges" in markdown
    assert "Checked formal pairings" in markdown
    formal_witness = next(
        edge.witness for edge in graph.edges if edge.kind is EdgeKind.FORMAL
    )
    assert f"`{formal_witness}`" in markdown
    assert (
        f'"authored_relation_edges": {len(graph.edges)}'
        in render_formalism_coverage_json(coverage)
    )


def test_coverage_writer_and_drift_check_are_deterministic(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    _copy_coverage_sources(tmp_path)

    assert len(formalism_coverage_drift(tmp_path)) == 2
    json_path, markdown_path = write_formalism_coverage(tmp_path)
    assert json_path.is_file()
    assert markdown_path.is_file()
    assert formalism_coverage_drift(tmp_path) == ()

    markdown_path.write_text("stale\n", encoding="utf-8")
    assert formalism_coverage_drift(tmp_path) == (markdown_path,)


def test_formal_import_inventory_retains_meta_dependencies(tmp_path: Path) -> None:
    _copy_coverage_sources(tmp_path)
    before = build_formalism_coverage(tmp_path)
    resource = tmp_path / "src" / "fep_lean" / "formal" / "finite_probability.lean"
    source = resource.read_text(encoding="utf-8")
    resource.write_text(
        source.replace(
            "module\n",
            "module\n"
            "public meta import Lean.Elab.Tactic.Omega\n"
            "meta import Lean.Meta.Tactic.NormCast\n"
            "/- public meta import Fake.CommentOnly -/\n",
            1,
        ),
        encoding="utf-8",
    )
    after = build_formalism_coverage(tmp_path)
    before_row = next(
        row
        for row in before["formal_modules"]
        if row["resource"] == "finite_probability.lean"
    )
    after_row = next(
        row
        for row in after["formal_modules"]
        if row["resource"] == "finite_probability.lean"
    )

    assert after_row["imports"] == [
        "Lean.Elab.Tactic.Omega",
        "Lean.Meta.Tactic.NormCast",
        *before_row["imports"],
    ]
    assert after["metrics"]["formal_module_import_edges"] == (
        before["metrics"]["formal_module_import_edges"] + 2
    )
    assert after_row["formal_dependencies"] == before_row["formal_dependencies"]


def test_formal_inventory_and_counts_ignore_comment_only_lean_commands(
    tmp_path: Path,
) -> None:
    _copy_coverage_sources(tmp_path)
    before = build_formalism_coverage(tmp_path)
    resource = tmp_path / "src" / "fep_lean" / "formal" / "finite_probability.lean"
    resource.write_text(
        resource.read_text(encoding="utf-8")
        + "\n/-\n"
        + "namespace FEP.CommentOnly\n"
        + "import Fake.CommentOnly\n"
        + "def fakeDefinition := 1\n"
        + "lemma fakeLemma : True := by trivial\n"
        + "end FEP.CommentOnly\n"
        + "-/\n",
        encoding="utf-8",
    )

    after = build_formalism_coverage(tmp_path)

    assert "FEP.CommentOnly.fakeLemma" not in formal_theorem_modules(tmp_path)
    assert after["metrics"] == before["metrics"]


def test_coverage_rejects_gap_without_explicit_blocker(tmp_path: Path) -> None:
    _copy_coverage_sources(tmp_path)
    config_dir = tmp_path / "config"
    relation_path = config_dir / "formalism_relations.yaml"
    maturity_path = config_dir / "theorem_maturity.yaml"
    maturity_data = yaml.safe_load(maturity_path.read_text(encoding="utf-8"))
    row = next(item for item in maturity_data["topics"] if item["id"] == "fep-036")
    row["disposition"] = "scope_gap"
    maturity_path.write_text(
        yaml.safe_dump(maturity_data, sort_keys=False), encoding="utf-8"
    )
    relation_data = yaml.safe_load(relation_path.read_text(encoding="utf-8"))
    relation_data["edges"] = [
        edge
        for edge in relation_data["edges"]
        if not (edge["source"] == "fep-036" and edge["kind"] == "blocked_by")
    ]
    relation_data["capabilities"] = [
        node
        for node in relation_data["capabilities"]
        if node["id"] != "cap-empirical-bayes-model"
    ]
    relation_path.write_text(
        yaml.safe_dump(relation_data, sort_keys=False), encoding="utf-8"
    )

    with pytest.raises(ValueError, match="gap rows without blocked_by edges: fep-036"):
        build_formalism_coverage(tmp_path)


def test_coverage_allows_proxy_rows_to_retain_stronger_capability_blockers(
    tmp_path: Path,
) -> None:
    _copy_coverage_sources(tmp_path)
    config_dir = tmp_path / "config"
    maturity_path = config_dir / "theorem_maturity.yaml"
    maturity_data = yaml.safe_load(maturity_path.read_text(encoding="utf-8"))
    row = next(item for item in maturity_data["topics"] if item["id"] == "fep-036")
    row["disposition"] = "conditional_proxy"
    maturity_path.write_text(
        yaml.safe_dump(maturity_data, sort_keys=False), encoding="utf-8"
    )

    relation_path = config_dir / "formalism_relations.yaml"
    relation_data = yaml.safe_load(relation_path.read_text(encoding="utf-8"))
    capability = next(
        item
        for item in relation_data["capabilities"]
        if item["id"] == "cap-empirical-bayes-model"
    )
    capability["status"] = "partial"
    relation_data["edges"].append(
        {
            "source": "fep-036",
            "target": "cap-empirical-bayes-model",
            "kind": "blocked_by",
            "rationale": "A stronger empirical-risk theorem is intentionally absent.",
        }
    )
    relation_data["edges"].sort(
        key=lambda edge: (edge["source"], edge["kind"], edge["target"])
    )
    relation_path.write_text(
        yaml.safe_dump(relation_data, sort_keys=False), encoding="utf-8"
    )

    coverage = build_formalism_coverage(tmp_path)

    topic = next(item for item in coverage["topics"] if item["id"] == "fep-036")
    assert topic["semantic_disposition"] == "conditional_proxy"
    capability = next(
        item
        for item in coverage["capabilities"]
        if item["id"] == "cap-empirical-bayes-model"
    )
    assert "fep-036" in capability["blocked_topics"]


def test_coverage_rejects_formalized_rows_with_capability_blockers(
    tmp_path: Path,
) -> None:
    _copy_coverage_sources(tmp_path)
    config_dir = tmp_path / "config"
    relation_path = config_dir / "formalism_relations.yaml"
    relation_data = yaml.safe_load(relation_path.read_text(encoding="utf-8"))
    capability = next(
        item
        for item in relation_data["capabilities"]
        if item["id"] == "cap-empirical-bayes-model"
    )
    capability["status"] = "partial"
    relation_data["edges"].append(
        {
            "source": "fep-036",
            "target": "cap-empirical-bayes-model",
            "kind": "blocked_by",
            "rationale": "A synthetic blocker used to exercise the firewall.",
        }
    )
    relation_data["edges"].sort(
        key=lambda edge: (edge["source"], edge["kind"], edge["target"])
    )
    relation_path.write_text(
        yaml.safe_dump(relation_data, sort_keys=False), encoding="utf-8"
    )

    with pytest.raises(
        ValueError, match="formalized rows with blocked_by edges: fep-036"
    ):
        build_formalism_coverage(tmp_path)


def test_coverage_rejects_unresolved_formal_witness(tmp_path: Path) -> None:
    _copy_coverage_sources(tmp_path)
    config_dir = tmp_path / "config"
    relation_path = config_dir / "formalism_relations.yaml"
    relation_data = yaml.safe_load(relation_path.read_text(encoding="utf-8"))
    formal_edge = next(
        edge for edge in relation_data["edges"] if edge["kind"] == "formal"
    )
    formal_edge["witness"] = "FEPComposed.not_a_declaration"
    relation_path.write_text(
        yaml.safe_dump(relation_data, sort_keys=False), encoding="utf-8"
    )

    with pytest.raises(ValueError, match="unresolved formal evidence declarations"):
        build_formalism_coverage(tmp_path)


def test_coverage_rejects_resolved_witness_that_omits_an_endpoint(
    tmp_path: Path,
) -> None:
    _copy_coverage_sources(tmp_path)
    relation_path = tmp_path / "config" / "formalism_relations.yaml"
    relation_data = yaml.safe_load(relation_path.read_text(encoding="utf-8"))
    formal_edge = next(
        edge
        for edge in relation_data["edges"]
        if edge["source"] == "fep-002" and edge["target"] == "fep-014"
    )
    formal_edge["witness"] = "FEPComposed.fep041_informationGain_is_fep014_kl"
    relation_path.write_text(
        yaml.safe_dump(relation_data, sort_keys=False), encoding="utf-8"
    )

    with pytest.raises(ValueError, match="missing endpoint references: fep-002"):
        build_formalism_coverage(tmp_path)


def test_coverage_does_not_count_comment_only_endpoint_mentions(
    tmp_path: Path,
) -> None:
    _copy_coverage_sources(tmp_path)
    core = tmp_path / "src" / "fep_lean" / "formal" / "compositions" / "core.lean"
    source = core.read_text(encoding="utf-8")
    source = source.replace("fep_fep002.", "fep_fep999.")
    source = source.replace(
        "theorem fep002_vfe_compProd_chain_rule",
        "theorem fep002_vfe_compProd_chain_rule\n"
        "-- fep_fep002. appears only in this comment",
    )
    core.write_text(source, encoding="utf-8")

    with pytest.raises(ValueError, match="missing endpoint references: fep-002"):
        build_formalism_coverage(tmp_path)


def test_coverage_requires_formal_pairings_to_state_a_conjunction(
    tmp_path: Path,
) -> None:
    _copy_coverage_sources(tmp_path)
    leaf = (
        tmp_path
        / "src"
        / "fep_lean"
        / "formal"
        / "compositions"
        / "collective_learning.lean"
    )
    source = leaf.read_text(encoding="utf-8")
    theorem_start = source.index(
        "theorem fep107_product_agent_extends_fep027_hierarchy"
    )
    theorem_end = source.index(
        "theorem fep108_collective_vfe_extends_fep039_additivity"
    )
    block = source[theorem_start:theorem_end]
    result_conjunction = block.index("∧")
    weakened = (
        block[:result_conjunction] + "→" + block[result_conjunction + 1 :]
    ).replace(
        "    {NativeParent NativeChild : Type*}",
        "    (syntheticHypothesis : True ∧ True)\n"
        "    {NativeParent NativeChild : Type*}",
        1,
    )
    assert weakened != block
    leaf.write_text(
        source[:theorem_start] + weakened + source[theorem_end:], encoding="utf-8"
    )

    with pytest.raises(
        ValueError, match="formal_pairing witnesses must expose a checked conjunction"
    ):
        build_formalism_coverage(tmp_path)
