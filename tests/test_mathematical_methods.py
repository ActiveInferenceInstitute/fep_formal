"""Portable installed and canonical-checkout mathematical-method contracts."""

from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path, PureWindowsPath

import pytest
import yaml

from fep_lean import __version__, cli
from fep_lean.catalogue.relations import EdgeKind
from fep_lean.methods import (
    BoundaryProbeError,
    PositioningError,
    SourceOrigin,
    analyze_topic,
    bernoulli_fisher,
    build_mathematical_positioning,
    classical_mds,
    cross_corpus_embedding,
    export_mathematical_positioning,
    extended_kl,
    finite_kl_totalized,
    inspect_family,
    inspect_theorem,
    inspect_topic,
    mathematical_positioning_bytes,
    mathematical_positioning_drift,
    package_resource_drift,
    positioning_neighbors,
)
from fep_lean.methods import model as model_module

ROOT = Path(__file__).resolve().parents[1]


def test_exact_statement_analysis_preserves_all_reviewed_contracts(packaged):
    data = packaged.as_dict()
    declarations = data["theorem_analysis"]["declarations"]
    assert len(declarations) == 2185
    assert "not a certified" not in data["theorem_analysis"]["analysis_boundary"]
    assert (
        "neither a certified translation"
        in data["theorem_analysis"]["analysis_boundary"]
    )
    for topic in data["topics"]:
        result = analyze_topic(packaged, topic["id"])
        primary = result["primary"]
        assert primary["qualified_name"] == topic["primary_theorem_qualified"]
        assert primary["statement"] in model_module.BODIES[topic["id"]]
        assert (
            hashlib.sha256(primary["statement"].encode()).hexdigest()
            == primary["statement_sha256"]
        )
        assert ":= by" not in primary["statement"]
        for field in (
            "invariant",
            "assumption_review",
            "non_vacuity",
            "acceptance_probe",
            "disposition",
        ):
            assert (
                result["maintained_semantic_analysis"][field]
                == topic["semantic_review"][field]
            )
        assert [row["qualified_name"] for row in result["supporting"]] == topic[
            "reviewed_theorems_qualified"
        ]["supporting_theorems"]
        assert [row["qualified_name"] for row in result["boundary"]] == topic[
            "reviewed_theorems_qualified"
        ]["boundary_theorems"]
    fisher = analyze_topic(packaged, "fep-038")["primary"]
    assert [row["names"] for row in fisher["binders"]] == [["p"], ["hp0"], ["hp1"]]
    assert [row["type_source"] for row in fisher["binders"]] == ["ℝ", "0 < p", "p < 1"]
    assert fisher["binders"][0]["visibility"] == "implicit"
    assert fisher["conclusion"] == "fep038_fisherInformation p = 1 / (p * (1 - p))"
    unique = analyze_topic(packaged, "fep-005")["primary"]
    assert unique["conclusion"].startswith("∃! k : BlkPart,")
    with pytest.raises(PositioningError, match="fully qualified"):
        inspect_theorem(packaged, "fep038_fisherInformation_eq")
    with pytest.raises(PositioningError, match="unknown topic"):
        analyze_topic(packaged, "fep-999")


def test_lean_signature_parser_retains_scopes_nested_binders_and_comment_offsets():
    source = """namespace Outer
variable {α : Type*} [MeasurableSpace α]
section Local
variable (ambient : α)
theorem first (x : α) (h : ∀ y : α, y = x) :
  ∀ z : α, z = x := by
  -- Fake.second is only a comment.
  exact h
end Local
theorem second (x : α) : x = x := by rfl
end Outer
namespace Other
theorem second : True := by trivial
end Other
"""
    rows = model_module._theorem_sources(source, "specimen.lean")
    first, second = rows["Outer.first"], rows["Outer.second"]
    assert first["conclusion"] == "∀ z : α, z = x"
    assert first["binders"][1]["type_source"] == "∀ y : α, y = x"
    assert len(first["context_binders"]) == 3
    assert len(second["context_binders"]) == 2
    assert rows["Other.second"]["context_binders"] == []
    assert first["statement"] in source
    duplicate = (
        source + "namespace Outer\ntheorem first : True := by trivial\nend Outer\n"
    )
    with pytest.raises(PositioningError, match="ambiguous Lean theorem"):
        model_module._theorem_sources(duplicate, "duplicate.lean")
    with pytest.raises(PositioningError, match="proof delimiter"):
        model_module._theorem_sources(
            "theorem unfinished (x : ℝ) : x = x", "invalid.lean"
        )


def test_proof_mentions_stop_before_private_and_attribute_prefixed_declarations(
    packaged,
):
    source = """namespace Example
variable (h : True)
include h
theorem first : True := by trivial
@[simp]
private theorem hidden : True := by
  exact Other.later
@[simp] protected def hiddenDefinition : Bool := true
theorem last : True := by trivial
end Example
"""
    records = model_module._theorem_sources(source, "fixture.lean")
    assert set(records) == {"Example.first", "Example.last"}
    assert records["Example.first"]["proof_source"] == "by trivial"
    assert "Other.later" not in records["Example.first"]["proof_source"]
    attributed = model_module._theorem_sources(
        "namespace Example\n@[a_theorem_attribute] theorem first : True := by trivial\nend Example\n",
        "attribute.lean",
    )
    assert attributed["Example.first"]["statement"] == "theorem first : True"
    actual = inspect_theorem(
        packaged, "FEP.GaussianPrecisionConditioning.internalConditionalKernel_variance"
    )
    assert actual["line_coordinate_kind"] == "formal_resource_file"
    fisher = analyze_topic(packaged, "fep-038")["primary"]
    assert fisher["line_coordinate_kind"] == "canonical_topic_body_literal"
    directives = [
        record["preceding_scope_directives"]
        for record in packaged.as_dict()["theorem_analysis"]["declarations"].values()
        if record["source_owner"].endswith("decision_risk.lean")
    ]
    assert "include h" in records["Example.first"]["source_context"]
    assert any(
        any(row["directive"] == "omit" for row in values) for values in directives
    )


def test_classical_mds_exact_distances_rank_zero_and_repeated_eigenspaces():
    two = classical_mds([[0, 0], [1, 1]])
    assert two["distances"][0][1] == math.sqrt(2)
    assert two["positive_rank"] == 1
    assert two["normalized_stress"] < 1e-14
    assert math.dist(*two["coordinates"]) == pytest.approx(math.sqrt(2), abs=1e-14)
    assert all(row[1] == 0 for row in two["coordinates"])
    for vectors in ([[1, 0]], [[1, 0], [1, 0], [1, 0]]):
        result = classical_mds(vectors)
        assert result["positive_rank"] == 0
        assert result["coordinates"] == [[0.0, 0.0]] * len(vectors)
        assert result["normalized_stress"] == 0
        assert result["explained_positive_inertia"] == 0
    triangle = classical_mds([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
    assert triangle == classical_mds([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
    assert triangle["positive_rank"] == 2
    assert triangle["eigenambiguity"][0]["multiplicity"] == 2
    assert triangle["normalized_stress"] < 1e-14
    assert sum(point[0] for point in triangle["coordinates"]) == pytest.approx(
        0, abs=1e-14
    )
    assert triangle["coordinates"][0][0] > 0
    from decimal import ROUND_UP, localcontext

    with localcontext() as ambient:
        ambient.prec = 4
        ambient.rounding = ROUND_UP
        ambient.Emin, ambient.Emax = -5, 5
        assert triangle == classical_mds([[1, 0, 0], [0, 1, 0], [0, 0, 1]])


@pytest.mark.parametrize(
    "vectors", [[], [[]], [[0], [0, 1]], [[True]], [[2]], [[float("nan")]], [[0.0]]]
)
def test_classical_mds_refuses_empty_malformed_or_nonbinary_carriers(vectors):
    with pytest.raises(BoundaryProbeError):
        classical_mds(vectors)


@pytest.fixture(scope="module")
def packaged():
    return build_mathematical_positioning()


def test_cross_corpus_assignments_keep_exact_features_source_passports_and_boundaries(
    packaged,
):
    from decimal import Decimal

    data = packaged.as_dict()
    cross = cross_corpus_embedding(packaged)
    assert len(cross["rows"]) == 34
    assert len(cross["coordinates"]) == 30
    assert [row["family"] for row in cross["rows"][:22]] == [
        row["family"] for row in data["family_positions"]
    ]
    assert all(
        row["evidence_status"] == "reviewed_source_statement_uncompiled"
        for row in cross["rows"][22:]
    )
    assert (
        cross["input_sha256"]["positioning.yaml"]
        == data["source_sha256"]["inputs/positioning.yaml"]
    )
    vectors = cross["vectors"]
    for i, row in enumerate(vectors):
        for j, other in enumerate(vectors):
            assert cross["projection"]["squared_distances"][i][j] == sum(
                a != b for a, b in zip(row, other, strict=True)
            )
    solver = cross["projection"]["eigensolver"]
    assert solver["converged"]
    assert Decimal(solver["offdiagonal_residual"]) <= Decimal(solver["residual_limit"])
    assert cross["projection"]["positive_rank"] > 2
    assert 0 < cross["projection"]["normalized_stress"] < 1
    assert "not assigned" in cross["assignment_boundary"]
    assert "no relation edge" in cross["relation_boundary"]
    untouched = data["authored_relations"]
    cross["rows"].clear()
    assert len(cross_corpus_embedding(packaged)["rows"]) == 34
    assert packaged.as_dict()["authored_relations"] == untouched
    policy = model_module.load_yaml(ROOT / "specs/openai-math-methods/positioning.yaml")
    policy.pop("cross_corpus")
    assert model_module._cross_corpus_model(policy, {}) is None


@pytest.mark.parametrize(
    "case",
    [
        "coordinate-duplicate",
        "coordinate-unknown",
        "family-missing",
        "family-duplicate",
        "family-domain-drift",
        "result-duplicate",
        "result-empty",
        "source-hash",
        "source-url",
        "source-escape",
        "pin",
        "status",
        "schema-bool",
    ],
)
def test_cross_corpus_refuses_malformed_rosters_and_false_source_identities(case):
    policy = copy.deepcopy(
        model_module.load_yaml(ROOT / "specs/openai-math-methods/positioning.yaml")
    )
    table = policy["cross_corpus"]
    if case == "coordinate-duplicate":
        table["coordinates"].append(table["coordinates"][0])
    elif case == "coordinate-unknown":
        table["upstream_results"][0]["features"].append("domain:unknown")
    elif case == "family-missing":
        table["fep_family_features"].pop()
    elif case == "family-duplicate":
        table["fep_family_features"].append(table["fep_family_features"][0])
    elif case == "family-domain-drift":
        table["fep_family_features"][0]["features"].remove("domain:analysis")
    elif case == "result-duplicate":
        table["upstream_results"].append(table["upstream_results"][0])
    elif case == "result-empty":
        table["upstream_results"].clear()
    elif case == "source-hash":
        table["upstream_results"][0]["source_sha256"] = "not-a-hash"
    elif case == "source-url":
        table["upstream_results"][0]["source_url"] = (
            "https://github.com/openai/math/blob/main/source.tex"
        )
    elif case == "source-escape":
        table["upstream_results"][0]["source_path"] = "../source.tex"
    elif case == "pin":
        table["upstream_pin"]["commit"] = "main"
    elif case == "status":
        table["upstream_results"][0]["status"] = "locally_verified"
    else:
        table["schema_version"] = True
    with pytest.raises(PositioningError):
        model_module._validate_cross_corpus(table, policy)


def test_repository_source_paths_are_posix_identities_on_every_host(monkeypatch):
    policy = model_module.load_yaml(ROOT / "specs/openai-math-methods/positioning.yaml")
    table = policy["cross_corpus"]
    path = table["upstream_results"][0]["source_path"]
    assert str(PureWindowsPath(path)) != path
    monkeypatch.setattr(model_module, "Path", PureWindowsPath)
    model_module._validate_cross_corpus(table, policy)
    for invalid in (
        path.replace("/", "\\"),
        "/" + path,
        "../" + path,
        "./" + path,
        "C:/" + path,
        "C:" + path,
    ):
        altered = copy.deepcopy(table)
        altered["upstream_results"][0]["source_path"] = invalid
        altered["upstream_results"][0]["source_url"] = (
            table["upstream_pin"]["repository_url"]
            + "/blob/"
            + table["upstream_pin"]["commit"]
            + "/"
            + invalid
        )
        with pytest.raises(PositioningError, match="source URL/path"):
            model_module._validate_cross_corpus(altered, policy)


def test_installed_and_checkout_models_preserve_canonical_values_and_explicit_origins(
    packaged,
):
    checkout = build_mathematical_positioning(ROOT)
    package_data, checkout_data = packaged.as_dict(), checkout.as_dict()
    assert packaged.origin is SourceOrigin.INSTALLED_PACKAGE
    assert checkout.origin is SourceOrigin.CHECKOUT
    for field in (
        "topics",
        "authored_relations",
        "family_positions",
        "continuous_scope",
        "feature_embedding",
    ):
        assert package_data[field] == checkout_data[field]
    package_hashes, checkout_hashes = (
        package_data["source_sha256"],
        checkout_data["source_sha256"],
    )
    assert set(package_hashes) - set(checkout_hashes) == {"data/topics.yaml"}
    assert {key: package_hashes[key] for key in checkout_hashes} == checkout_hashes
    assert package_data["counts"]["topics"] == len(packaged.metadata.topic_ids) == 168
    assert package_data["package_version"] == __version__
    assert package_data["counts"]["families"] == 22
    assert any(edge.kind is EdgeKind.FORMAL_PAIRING for edge in packaged.graph.edges)
    assert package_data["authored_relations"] == yaml.safe_load(
        (ROOT / "config/formalism_relations.yaml").read_text()
    )
    assert [row["semantic_review"] for row in package_data["topics"]] == yaml.safe_load(
        (ROOT / "config/theorem_maturity.yaml").read_text()
    )["topics"]
    assert all(not Path(name).is_absolute() for name in package_data["source_sha256"])


@pytest.mark.parametrize(
    "owner", ["catalogue/registry.py", "catalogue/schema.py", "formal/manifest.py"]
)
def test_foreign_checkout_refuses_changed_source_defining_python(tmp_path, owner):
    """Hashing a foreign owner never licenses applying different imported code."""
    for source in model_module._source_paths(
        ROOT, model_module._input_paths(ROOT)
    ).values():
        target = tmp_path / source.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
    assert build_mathematical_positioning(tmp_path).origin is SourceOrigin.CHECKOUT
    changed = tmp_path / "src/fep_lean" / owner
    # If accidentally executed, this is a real failure, not a harmless comment.
    changed.write_bytes(
        changed.read_bytes() + b"\nraise RuntimeError('foreign owner executed')\n"
    )
    with pytest.raises(PositioningError, match="disagree with imported runtime"):
        build_mathematical_positioning(tmp_path)


def test_previously_imported_validator_cannot_be_rebound_to_changed_owner_bytes(
    tmp_path,
):
    """Use a real copied package, cached import, and subsequent executable mutation."""
    source_root = tmp_path / "isolated-source"
    copied = source_root / "fep_lean"
    shutil.copytree(
        ROOT / "src/fep_lean",
        copied,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    probe = f"""
import pathlib, sys
sys.path.insert(0, {str(source_root)!r})
import fep_lean.catalogue.semantics
owner = pathlib.Path({str(copied / "catalogue/semantics.py")!r})
owner.write_bytes(owner.read_bytes() + b"\\nraise RuntimeError('changed validator executed')\\n")
from fep_lean.methods import PositioningError, build_mathematical_positioning
try:
    build_mathematical_positioning()
except PositioningError as error:
    assert 'catalogue/semantics.py' in str(error)
    assert 'disagree with imported runtime' in str(error)
else:
    raise AssertionError('cached validator was labeled with changed owner bytes')
"""
    subprocess.run(
        [sys.executable, "-I", "-c", probe],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )


def test_detached_views_and_exact_queries_do_not_mutate_retained_model(packaged):
    data = packaged.as_dict()
    data["topics"].clear()
    assert len(packaged.as_dict()["topics"]) == 168
    topic = inspect_topic(packaged, "fep-038")
    assert topic["primary_theorem_qualified"].startswith("fep_fep038.FEP038.")
    assert (
        topic["mathematical_context"]["classification_scope"]
        == "inherited_family_context"
    )
    family = inspect_family(packaged, "core-information-geometry")
    assert "fep-038" in family["topic_ids"]
    assert positioning_neighbors(packaged, family["family"], 2)
    for operation, identity in (
        (inspect_topic, "fep-999"),
        (inspect_family, "unknown"),
        (positioning_neighbors, "unknown"),
    ):
        with pytest.raises(PositioningError):
            operation(packaged, identity)


@pytest.mark.parametrize(
    "failure",
    [
        "duplicate_key",
        "invalid_yaml",
        "unknown_family",
        "unknown_domain",
        "unknown_topic",
        "missing_topic",
        "dangling_witness",
        "maturity_drift",
        "bool_schema",
    ],
)
def test_package_resources_refuse_malformed_or_drifting_inputs(
    tmp_path, monkeypatch, failure
):
    paths = {}
    for name, source in model_module._input_paths(None).items():
        target = tmp_path / name
        target.write_bytes(source.read_bytes())
        paths[name] = target
    policy_path = paths["positioning.yaml"]
    if failure == "duplicate_key":
        policy_path.write_text("schema_version: 1\nschema_version: 1\n")
    elif failure == "invalid_yaml":
        policy_path.write_text("families: [unterminated\n")
    elif failure in {"unknown_family", "unknown_domain", "bool_schema"}:
        document = yaml.safe_load(policy_path.read_text())
        if failure == "unknown_family":
            document["families"][0]["family"] = "unknown-family"
        elif failure == "unknown_domain":
            document["families"][0]["domains"].append("unreviewed-domain")
        else:
            document["schema_version"] = True
        policy_path.write_text(yaml.safe_dump(document))
    elif failure in {"unknown_topic", "missing_topic"}:
        path = paths["catalogue_metadata.yaml"]
        document = yaml.safe_load(path.read_text())
        if failure == "unknown_topic":
            document["topics"][0]["id"] = "fep-999"
        else:
            document["topics"].pop()
        path.write_text(yaml.safe_dump(document))
    elif failure == "dangling_witness":
        path = paths["formalism_relations.yaml"]
        document = yaml.safe_load(path.read_text())
        document["edges"][0]["witness"] = "Imagined.Native.theorem"
        path.write_text(yaml.safe_dump(document))
    else:
        path = paths["theorem_maturity.yaml"]
        document = yaml.safe_load(path.read_text())
        document["topics"][0]["invariant"] = (
            "Changed interpretation without catalogue refresh."
        )
        path.write_text(yaml.safe_dump(document))
    monkeypatch.setattr(model_module, "_input_paths", lambda _root: paths)
    with pytest.raises(ValueError):
        build_mathematical_positioning()


def test_four_package_copies_have_exact_read_only_canonical_parity(tmp_path):
    assert package_resource_drift(ROOT) == ()
    for name, owner in model_module.RESOURCE_OWNERS.items():
        source, generated = tmp_path / owner, tmp_path / "src/fep_lean/data" / name
        source.parent.mkdir(parents=True, exist_ok=True)
        generated.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes((ROOT / owner).read_bytes())
        generated.write_bytes(source.read_bytes())
    assert package_resource_drift(tmp_path) == ()
    target = tmp_path / "src/fep_lean/data/positioning.yaml"
    target.write_bytes(target.read_bytes() + b"\n")
    before = (target.stat().st_mtime_ns, target.read_bytes())
    assert package_resource_drift(tmp_path) == (target,)
    assert (target.stat().st_mtime_ns, target.read_bytes()) == before


def test_full_export_and_exact_freshness_refuse_byte_drift_without_repair(
    packaged, tmp_path
):
    output = tmp_path / "analysis"
    paths = export_mathematical_positioning(packaged, output)
    assert {
        "positioning.json",
        "positioning.md",
        "visual-model.json",
        "mathematical-map.html",
    } <= {path.name for path in paths}
    assert len([path for path in paths if path.suffix == ".svg"]) == 13
    assert mathematical_positioning_drift(packaged, output) == ()
    html = output / "mathematical-map.html"
    data = html.read_bytes()
    html.write_bytes(data + b" ")
    before = html.stat().st_mtime_ns
    assert html in mathematical_positioning_drift(packaged, output)
    assert html.read_bytes() == data + b" " and html.stat().st_mtime_ns == before
    assert "installed_package" in (output / "positioning.md").read_text()
    missing = tmp_path / "absent"
    assert mathematical_positioning_drift(packaged, missing)
    assert not missing.exists()


def test_representation_is_deterministic_and_contains_all_contracts(packaged):
    products = mathematical_positioning_bytes(packaged)
    assert products == mathematical_positioning_bytes(packaged)
    markdown = products[Path("positioning.md")].decode()
    for topic in packaged.as_dict()["topics"]:
        review = topic["semantic_review"]
        for field in (
            "invariant",
            "assumption_review",
            "non_vacuity",
            "acceptance_probe",
        ):
            assert review[field] in markdown


def test_markdown_fences_exact_namespace_context_and_rejects_raw_brackets(
    packaged, tmp_path
):
    import importlib.util

    from fep_lean.methods.projection import render_markdown

    spec = importlib.util.spec_from_file_location(
        "methods_markdown_hygiene", ROOT / "docs/md_hygiene.py"
    )
    assert spec is not None and spec.loader is not None
    hygiene = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(hygiene)
    data = packaged.as_dict()
    markdown = render_markdown(data)
    contexts = [
        data["theorem_analysis"]["declarations"][topic["primary_theorem_qualified"]][
            "namespace_variable_context"
        ]
        for topic in data["topics"]
    ]
    context = next(values for values in contexts if "[" in "\n".join(values))
    exact_context = "\n".join(context)
    fenced = f"Namespace variable context:\n\n```lean\n{exact_context}\n```"
    assert fenced in markdown
    assert "Source-grounded semantic analysis: Source-grounded" not in markdown
    path = tmp_path / "positioning.md"
    path.write_text(markdown, encoding="utf-8")
    assert hygiene.lint_file(path, max_line=None, strict=True) == []
    path.write_text(
        markdown.replace(fenced, "Namespace variable context: " + exact_context, 1),
        encoding="utf-8",
    )
    assert any(
        "orphan bracket" in issue
        for issue in hygiene.lint_file(path, max_line=None, strict=True)
    )


def test_boundary_probes_preserve_support_and_float_range_failures():
    assert bernoulli_fisher(0.5) == 4
    for parameter in (0.0, 1.0, math.nan, 1e-320):
        with pytest.raises(BoundaryProbeError):
            bernoulli_fisher(parameter)
    assert finite_kl_totalized((1, 0), (0, 1)) == 1
    assert extended_kl((1, 0), (0, 1)) == math.inf
    expected = -math.log(1e-320)
    assert finite_kl_totalized((1, 0), (1e-320, 1)) == pytest.approx(expected)
    assert extended_kl((1, 0), (1e-320, 1)) == pytest.approx(expected)


def test_cli_methods_branch_is_portable_and_explicit_roots_fail_closed(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.delenv("FEP_LEAN_PROJECT_ROOT", raising=False)
    monkeypatch.setattr(cli, "project_root", lambda: tmp_path)
    assert cli.main(["methods", "inspect", "--topic", "fep-038"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["source_origin"] == "installed_package"
    assert payload["package_version"] == __version__
    assert payload["result"]["id"] == "fep-038"
    assert cli.main(["methods", "analyze", "fep-038"]) == 0
    analysis = json.loads(capsys.readouterr().out)["result"]
    assert analysis["primary"]["binders"][1]["type_source"] == "0 < p"
    assert cli.main(["methods", "theorem", analysis["primary"]["qualified_name"]]) == 0
    assert json.loads(capsys.readouterr().out)["result"] == analysis["primary"]
    assert cli.main(["methods", "embedding"]) == 0
    assert len(json.loads(capsys.readouterr().out)["result"]["rows"]) == 34
    assert cli.main(["methods", "neighbors", "unknown"]) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "error"
    assert cli.main(["--project-root", str(tmp_path), "methods", "inspect"]) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "error"
    assert "FEP_LEAN_PROJECT_ROOT" not in os.environ


def test_installed_wheel_methods_run_without_checkout_or_sibling_imports(tmp_path):
    """Build real wheel bytes and exercise public API/CLI in an isolated interpreter."""
    uv = shutil.which("uv")
    assert uv is not None
    dist = tmp_path / "dist"
    subprocess.run(
        [uv, "build", "--out-dir", str(dist)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    wheel = next(dist.glob("fep_lean-*.whl"))
    environment = tmp_path / "venv"
    clean_env = {
        key: value
        for key, value in os.environ.items()
        if key not in {"PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV"}
        and not key.startswith("FEP_LEAN_")
    }
    subprocess.run(
        [uv, "venv", "--python", sys.executable, str(environment)],
        cwd=tmp_path,
        env=clean_env,
        check=True,
        capture_output=True,
        text=True,
    )
    scripts = environment / ("Scripts" if os.name == "nt" else "bin")
    python = scripts / ("python.exe" if os.name == "nt" else "python")
    subprocess.run(
        [uv, "pip", "install", "--python", str(python), str(wheel)],
        cwd=tmp_path,
        env=clean_env,
        check=True,
        capture_output=True,
        text=True,
    )
    output = tmp_path / "installed-analysis"
    probe = f"""
import json, pathlib, sys, fep_lean
from fep_lean.methods import build_mathematical_positioning, inspect_topic, export_mathematical_positioning, mathematical_positioning_drift
assert pathlib.Path(fep_lean.__file__).is_relative_to(pathlib.Path({str(environment)!r}))
assert not any(p and pathlib.Path(p).is_relative_to(pathlib.Path({str(ROOT)!r})) for p in sys.path)
model = build_mathematical_positioning()
assert model.origin.value == 'installed_package'
assert len(model.metadata.topic_ids) == 168
assert inspect_topic(model, 'fep-038')['primary_theorem_qualified'].startswith('fep_fep038.FEP038.')
root = pathlib.Path({str(output)!r})
paths = export_mathematical_positioning(model, root)
assert mathematical_positioning_drift(model, root) == ()
print(json.dumps({{'topics':len(model.metadata.topic_ids), 'artifacts':len(paths)}}))
"""
    subprocess.run(
        [str(python), "-I", "-c", probe],
        cwd=tmp_path,
        env=clean_env,
        check=True,
        capture_output=True,
        text=True,
    )
    console = scripts / ("fep-lean.exe" if os.name == "nt" else "fep-lean")
    result = subprocess.run(
        [str(console), "methods", "inspect", "--family", "core-information-geometry"],
        cwd=tmp_path,
        env=clean_env,
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(result.stdout)["source_origin"] == "installed_package"
    before = {
        path.relative_to(output): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in output.rglob("*")
        if path.is_file()
    }
    subprocess.run(
        [str(console), "methods", "check", "--output-root", str(output)],
        cwd=tmp_path,
        env=clean_env,
        check=True,
        capture_output=True,
        text=True,
    )
    after = {
        path.relative_to(output): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in output.rglob("*")
        if path.is_file()
    }
    assert before == after
