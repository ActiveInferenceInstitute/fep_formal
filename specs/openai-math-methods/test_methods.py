"""Slice-local behavior and refusal tests; no Lean or provider execution."""

from __future__ import annotations

import copy
import importlib.util
import json
import math
from pathlib import Path
from types import SimpleNamespace
from xml.etree import ElementTree

import pytest
import yaml

from fep_formal.catalogue.schema import load_catalogue_metadata
from fep_formal.catalogue.semantics import SemanticValidationError
from fep_formal.formal.declarations import all_formal_theorem_declarations
from fep_formal.formal.manifest import FORMAL_MODULES

METHOD_PATH = Path(__file__).with_name("methods.py")
SPEC = importlib.util.spec_from_file_location("positioning_methods", METHOD_PATH)
assert SPEC is not None and SPEC.loader is not None
methods = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(methods)


@pytest.fixture(scope="module")
def model():
    return methods.build_model()


@pytest.fixture
def policy():
    return methods.load_yaml(METHOD_PATH.with_name("positioning.yaml"))


def validate_policy(policy):
    metadata = load_catalogue_metadata(methods.ROOT / "config/catalogue_metadata.yaml")
    methods.validate_policy(
        policy, metadata.families, {m.resource for m in FORMAL_MODULES}
    )


def test_model_covers_exact_roster_semantics_relations_and_body_owners(model):
    root = methods.ROOT
    metadata = methods.load_yaml(root / "config/catalogue_metadata.yaml")
    semantics = methods.load_yaml(root / "config/theorem_maturity.yaml")
    relations = methods.load_yaml(root / "config/formalism_relations.yaml")
    assert [row["id"] for row in model["topics"]] == [
        row["id"] for row in metadata["topics"]
    ]
    assert [row["semantic_review"] for row in model["topics"]] == semantics["topics"]
    assert model["authored_relations"] == relations
    assert model["counts"]["topics"] == 168
    assert model["counts"]["families"] == 22
    for topic in model["topics"]:
        assert topic["body_source"] in model["source_sha256"]
        assert topic["canonical_namespace"] == "FEP" + topic["id"][-3:]
        assert (
            topic["mathematical_context"]["classification_scope"]
            == "inherited_family_context"
        )
        assert topic["primary_theorem_qualified"].startswith(
            topic["aggregate_namespace"] + "."
        )
    resources = {row["resource"] for row in model["continuous_scope"]}
    assert {"h3_reference_model.lean", "smooth_information_geometry.lean"} <= resources


def test_deterministic_projection_and_all_semantic_fields_in_markdown(model):
    expected = methods.projection_bytes(model)
    assert expected == methods.projection_bytes(copy.deepcopy(model))
    assert expected == methods.projection_bytes(
        json.loads(json.dumps(model, sort_keys=True))
    )
    markdown = expected[methods.OUTPUTS[1]].decode()
    for topic in model["topics"]:
        for key in (
            "invariant",
            "assumption_review",
            "non_vacuity",
            "acceptance_probe",
        ):
            assert topic["semantic_review"][key] in markdown
    assert "formal_pairing" in markdown and "no compiler" in markdown
    svg = ElementTree.fromstring(expected[methods.OUTPUTS[2]])
    assert svg.attrib["role"] == "img"
    assert "family-domains-desc" in svg.attrib["aria-labelledby"]
    text = " ".join(svg.itertext())
    assert "not per-topic proof classification" in text
    assert "<image " not in expected[methods.OUTPUTS[2]].decode()
    for family in model["family_positions"]:
        assert family["family"] in text
    for domain in model["domains"]:
        assert domain in text


@pytest.mark.parametrize(
    "mutation",
    [
        "duplicate",
        "missing",
        "unknown",
        "domain",
        "domain-duplicate",
        "empty-axis",
        "unmanifested",
    ],
)
def test_policy_refuses_unreviewed_or_incomplete_coordinates(policy, mutation):
    if mutation == "duplicate":
        policy["families"].append(copy.deepcopy(policy["families"][0]))
    elif mutation == "missing":
        policy["families"].pop()
    elif mutation == "unknown":
        policy["families"][0]["family"] = "made-up-family"
    elif mutation == "domain":
        policy["families"][0]["domains"].append("made-up-domain")
    elif mutation == "domain-duplicate":
        policy["families"][0]["domains"].append(policy["families"][0]["domains"][0])
    elif mutation == "empty-axis":
        policy["families"][0]["topology"] = ""
    else:
        policy["continuous_scope"][0]["resource"] = "imagined_manifold.lean"
    with pytest.raises(methods.PositioningError):
        validate_policy(policy)


def test_yaml_duplicate_key_is_rejected(tmp_path):
    path = tmp_path / "duplicate.yaml"
    path.write_text("domains:\n  analysis: first\n  analysis: silently overwritten\n")
    with pytest.raises(methods.PositioningError, match="duplicate YAML key"):
        methods.load_yaml(path)


def test_literal_body_snapshot_rejects_stale_imports_and_duplicate_source_keys(
    tmp_path,
):
    path = tmp_path / "owner.py"
    entry = SimpleNamespace(
        source_relative_path="owner.py", bodies={"fep-001": "expected"}
    )
    path.write_text("BODIES: dict[str, str] = {'fep-001': 'expected'}\n")
    methods.validate_body_sources(tmp_path, (entry,))
    path.write_text("BODIES: dict[str, str] = {'fep-001': 'changed'}\n")
    with pytest.raises(methods.PositioningError, match="imported bodies differ"):
        methods.validate_body_sources(tmp_path, (entry,))
    path.write_text(
        "BODIES: dict[str, str] = {'fep-001': 'expected', 'fep-001': 'expected'}\n"
    )
    with pytest.raises(methods.PositioningError, match="duplicate literal body key"):
        methods.validate_body_sources(tmp_path, (entry,))


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "unknown"])
def test_canonical_metadata_refuses_roster_drift(tmp_path, mutation):
    metadata = methods.load_yaml(methods.ROOT / "config/catalogue_metadata.yaml")
    if mutation == "missing":
        metadata["topics"].pop()
    elif mutation == "duplicate":
        metadata["topics"][1]["id"] = metadata["topics"][0]["id"]
    else:
        metadata["topics"][0]["id"] = "fep-999"
    path = tmp_path / "catalogue_metadata.yaml"
    path.write_text(yaml.safe_dump(metadata))
    with pytest.raises(SemanticValidationError):
        load_catalogue_metadata(path)


@pytest.mark.parametrize(
    "owner", ["primary", "supporting", "boundary", "edge", "capability"]
)
def test_all_theorem_reference_lanes_refuse_dangling_names(model, owner):
    reviews = copy.deepcopy([topic["semantic_review"] for topic in model["topics"]])
    relations = copy.deepcopy(model["authored_relations"])
    missing = "Imagined.Native.theorem"
    if owner == "primary":
        reviews[0]["primary_theorem"] = missing
    elif owner in {"supporting", "boundary"}:
        reviews[0][owner + "_theorems"].append(missing)
    elif owner == "edge":
        relations["edges"][0]["witness"] = missing
    else:
        relations["capabilities"][0]["evidence"].append(missing)
    with pytest.raises(methods.PositioningError, match="dangling theorem"):
        methods.validate_references(
            reviews, relations, all_formal_theorem_declarations(methods.ROOT)
        )


def test_check_detects_same_size_drift_and_missing_without_writing(tmp_path):
    one = Path("one.txt")
    two = Path("two.txt")
    path = tmp_path / one
    path.write_bytes(b"old")
    before = path.stat()
    assert methods.check_projections(tmp_path, {one: b"new", two: b"new"}) == [
        "one.txt",
        "two.txt",
    ]
    after = path.stat()
    assert path.read_bytes() == b"old"
    assert (before.st_mtime_ns, before.st_size) == (after.st_mtime_ns, after.st_size)
    assert not (tmp_path / two).exists()
    assert methods.check_projections(tmp_path, {one: b"old"}) == []


def test_embedding_has_explicit_equal_weights_and_never_changes_relations(model):
    embedding = methods.feature_embedding(
        [
            {"family": "a", "domains": ["x", "y"]},
            {"family": "b", "domains": ["y", "z"]},
            {"family": "c", "domains": ["x", "y"]},
        ],
        ["x", "y", "z"],
    )
    assert embedding["vectors"]["a"] == [1, 1, 0]
    result = methods.neighbors(embedding, "a", 2)
    assert result[0]["family"] == "c" and result[0]["jaccard"] == 1
    assert result[1] == {
        "family": "b",
        "shared_domains": 1,
        "union_domains": 3,
        "jaccard": 1 / 3,
    }
    before = copy.deepcopy(model["authored_relations"])
    methods.neighbors(model["feature_embedding"], "core-information-geometry")
    assert model["authored_relations"] == before
    for family, vector in model["feature_embedding"]["vectors"].items():
        assert all(value in {0, 1} for value in vector)
        assert family in {row["family"] for row in model["family_positions"]}
    with pytest.raises(methods.PositioningError):
        methods.neighbors(embedding, "unknown")


@pytest.mark.parametrize("parameter", [0, 1, -0.01, 1.01, math.inf, math.nan])
def test_fisher_refuses_noninterior_or_nonfinite_parameters(parameter):
    with pytest.raises(methods.PositioningError):
        methods.bernoulli_fisher(parameter)


def test_interior_fisher_rejects_unrepresentable_float_without_moving_parameter():
    parameter = 1e-320
    assert 0 < parameter < 1
    with pytest.raises(methods.PositioningError, match="representable float range"):
        methods.bernoulli_fisher(parameter)
    assert parameter == 1e-320


def test_numeric_boundaries_distinguish_regular_geometry_support_and_identification():
    assert methods.bernoulli_fisher(0.5) == 4
    assert methods.bernoulli_fisher(0.25) == pytest.approx(16 / 3)
    assert methods.finite_kl_totalized((1, 0), (0, 1)) == 1
    assert methods.extended_kl((1, 0), (0, 1)) == math.inf
    assert methods.finite_kl_totalized((0.75, 0.25), (0.5, 0.5)) == pytest.approx(
        0.75 * math.log(1.5) + 0.25 * math.log(0.5)
    )
    probes = {row["id"]: row for row in methods.numerical_probes()}
    geometry = probes["fisher-chart-degeneracy"]
    assert all(
        math.fsum(row) == pytest.approx(0)
        for row in geometry["redundant_logit_information"]
    )
    assert sum(geometry["simplex_tangent"]) == 0
    assert (
        sum(
            v * v / p
            for v, p in zip(geometry["simplex_tangent"], geometry["law"], strict=True)
        )
        == 6
    )
    descent = probes["descent-does-not-identify"]
    assert all(
        a > b
        for a, b in zip(descent["energy_sequence"], descent["energy_sequence"][1:])
    )
    assert descent["distinct_limit_states"][0] != descent["distinct_limit_states"][1]
    with pytest.raises(methods.PositioningError):
        methods.extended_kl((0.5, 0.4), (0.5, 0.5))


def test_extreme_supported_kl_is_finite_without_ratio_overflow_or_underflow():
    source = (1.0, 0.0)
    reference = (1e-320, 1.0)
    expected = -math.log(reference[0])
    assert math.isfinite(expected)
    assert methods.extended_kl(source, reference) == pytest.approx(expected)
    assert methods.finite_kl_totalized(source, reference) == pytest.approx(expected)
    # The converse supported ratio is tiny; computing logarithms separately
    # keeps its finite contribution and does not turn it into log(0).
    reverse = methods.extended_kl(reference, (0.5, 0.5))
    assert math.isfinite(reverse) and reverse == pytest.approx(math.log(2))
    assert math.isfinite(methods.finite_kl_totalized(reference, (0.5, 0.5)))


@pytest.mark.parametrize("mutation", [None, "hash", "commit", "url", "path"])
def test_package_generator_binds_reviewed_result_passports_to_exact_lock(
    tmp_path, mutation
):
    from fep_formal.methods import PositioningError

    spec = importlib.util.spec_from_file_location(
        "passport_generator", METHOD_PATH.with_name("generate_package_methods.py")
    )
    assert spec and spec.loader
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    source = METHOD_PATH.parent
    target = tmp_path / "specs/openai-math-methods"
    target.mkdir(parents=True)
    policy = yaml.safe_load((source / "positioning.yaml").read_text())
    (target / "upstream.lock.json").write_bytes(
        (source / "upstream.lock.json").read_bytes()
    )
    if mutation == "hash":
        policy["cross_corpus"]["upstream_results"][0]["source_sha256"] = "0" * 64
    elif mutation == "commit":
        policy["cross_corpus"]["upstream_pin"]["commit"] = "0" * 40
    elif mutation == "url":
        policy["cross_corpus"]["upstream_results"][0]["source_url"] += "?altered=true"
    elif mutation == "path":
        policy["cross_corpus"]["upstream_results"][0]["source_path"] = (
            "not-reviewed.tex"
        )
    (target / "positioning.yaml").write_text(yaml.safe_dump(policy))
    before = {
        path: (path.read_bytes(), path.stat().st_mtime_ns) for path in target.iterdir()
    }
    if mutation is None:
        generator.validate_upstream_passports(tmp_path)
    else:
        with pytest.raises(PositioningError, match="disagrees with reviewed lock"):
            generator.validate_upstream_passports(tmp_path)
    assert before == {
        path: (path.read_bytes(), path.stat().st_mtime_ns) for path in target.iterdir()
    }
