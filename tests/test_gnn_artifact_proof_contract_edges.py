"""Malformed runner and custody inputs must fail before artifact proof generation.

These tests parse synthetic Python, inspect generated text, and alter isolated
artifact copies. They never import a runner or invoke Lean or the GNN renderer.
"""

from __future__ import annotations

import json
import shutil
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest

from fep_lean.verification import gnn_artifact_proof as proof

ROOT = Path(__file__).resolve().parents[1]
SLICE = Path("specs/gnn-bridge-q5-artifact-proof")
EXTRACTOR = Path("src/fep_lean/verification/gnn_artifact_proof.py")
MANIFEST = Path("generated/artifact_proof_manifest.json")
LITERALS = {
    "A_data": "[[0.5, 0.5], [0.5, 0.5]]",
    "B_data": "[[[0.5, 0.5], [0.5, 0.5]], [[0.5, 0.5], [0.5, 0.5]]]",
    "C_data": "[0.5, 0.5]",
    "D_data": "[0.5, 0.5]",
    "E_data": "[0.25, 0.75]",
}


def _runner(*, replace: dict[str, str] | None = None, extra: str = "") -> str:
    statements = {name: f"{name} = {literal}" for name, literal in LITERALS.items()}
    statements.update(replace or {})
    body = "\n".join(statements.values()) + "\n" + extra
    return (
        "def main():\n" + "\n".join("    " + line for line in body.splitlines()) + "\n"
    )


def _reject(source: str, reason: str) -> proof.ArtifactProofError:
    with pytest.raises(proof.ArtifactProofError) as caught:
        proof.extract_pymdp_tables(source, source_name="rejected-runner.py")
    assert caught.value.reason == reason
    return caught.value


@pytest.mark.parametrize("literal", ["[True, False]", "[None, 1]", "['0.25', 0.75]"])
def test_non_numeric_literal_cannot_enter_probability_tables(literal: str) -> None:
    _reject(
        _runner(replace={"E_data": f"E_data = {literal}"}), "unsupported_expression"
    )


@pytest.mark.parametrize("literal", ["[]", "[[], []]"])
def test_empty_tables_are_rejected_before_shape_or_normalization(literal: str) -> None:
    error = _reject(_runner(replace={"A_data": f"A_data = {literal}"}), "ragged_table")
    assert "empty table row" in error.detail


@pytest.mark.parametrize(
    "statement,reason",
    [
        ("alias = A_data = [[0.5, 0.5], [0.5, 0.5]]", "unsupported_expression"),
        ("[*A_data] = [[0.5, 0.5], [0.5, 0.5]]", "reassignment"),
        ("A_data.values = [[0.5, 0.5], [0.5, 0.5]]", "reassignment"),
        ("A_data[0]: list = [0.5, 0.5]", "reassignment"),
    ],
)
def test_alternative_assignment_targets_do_not_establish_frozen_tables(
    statement: str,
    reason: str,
) -> None:
    _reject(_runner(replace={"A_data": statement}), reason)


def test_annotations_preserve_literal_values_without_evaluating_annotation() -> None:
    annotated = _runner(
        replace={
            "A_data": "A_data: do_not_execute() = " + LITERALS["A_data"],
            "E_data": "E_data: list\nE_data = " + LITERALS["E_data"],
        }
    )
    ordinary = proof.extract_pymdp_tables(_runner())
    tables = proof.extract_pymdp_tables(annotated)
    assert tables.tables == ordinary.tables
    assert tables.source_sha256 != ordinary.source_sha256


def test_annotation_without_value_cannot_replace_missing_table() -> None:
    error = _reject(_runner(replace={"E_data": "E_data: list"}), "missing_assignment")
    assert "E_data" in error.detail


def test_deleted_table_is_not_a_retained_literal() -> None:
    _reject(_runner(extra="del E_data"), "reassignment")


def test_context_manager_binding_cannot_overwrite_a_table_name() -> None:
    _reject(_runner(extra="with manager() as E_data:\n    pass"), "ambiguous_dataflow")


@pytest.mark.parametrize(
    "statement,detail",
    [
        ("class Holder:\n    E_data = [0.25, 0.75]", "ClassDef"),
        ("def nested():\n    E_data = [0.25, 0.75]", "nested function"),
    ],
)
def test_class_or_nested_function_tables_cannot_satisfy_main_contract(
    statement: str,
    detail: str,
) -> None:
    error = _reject(_runner(replace={"E_data": statement}), "ambiguous_dataflow")
    assert detail in error.detail


def test_table_in_a_different_top_level_function_is_not_owned_by_main() -> None:
    source = _runner(replace={"E_data": "pass"})
    source += "\ndef helper():\n    E_data = [0.25, 0.75]\n"
    error = _reject(source, "ambiguous_dataflow")
    assert "found scope helper" in error.detail


@pytest.mark.parametrize(
    "extra",
    [
        "import math as E_data",
        "match value:\n    case [*E_data]:\n        pass",
        "match value:\n    case {'key': item, **E_data}:\n        pass",
        "global E_data",
        "nonlocal E_data",
    ],
)
def test_binding_forms_that_shadow_tables_are_rejected(extra: str) -> None:
    _reject(_runner(extra=extra), "shadowed_name")


def test_syntax_error_preserves_source_identity_in_rejection() -> None:
    error = _reject("def main():\n    E_data = [", "syntax_error")
    assert "rejected-runner.py" in error.detail


def test_omitted_shape_declaration_is_not_inferred_from_the_literal() -> None:
    shapes = {
        name: shape
        for name, shape in proof.DISCRETE_BOOL_SHAPES.items()
        if name != "E_data"
    }
    with pytest.raises(proof.ArtifactProofError) as caught:
        proof.extract_pymdp_tables(_runner(), shapes=shapes)
    assert caught.value.reason == "shape_mismatch"
    assert "no declared shape for E_data" in caught.value.detail


def test_transition_normalization_is_checked_per_previous_state_and_policy() -> None:
    literal = "[[[0.5, 0.5], [0.5, 0.25]], [[0.5, 0.5], [0.5, 0.5]]]"
    error = _reject(
        _runner(replace={"B_data": f"B_data = {literal}"}), "normalization_violation"
    )
    assert "policy 1, previous 1" in error.detail
    assert "3/4" in error.detail


@pytest.mark.parametrize("name", ["C_data", "D_data", "E_data"])
def test_each_vector_requires_its_own_unit_mass(name: str) -> None:
    error = _reject(
        _runner(replace={name: f"{name} = [0.25, 0.5]"}), "normalization_violation"
    )
    assert name in error.detail and "3/4" in error.detail


@pytest.mark.parametrize(
    "indices", [(), (0,), (0, 0, 0), (-1, 0), (0, -1), (2, 0), (0, 2)]
)
def test_table_access_refuses_wrong_arity_and_python_negative_indexing(
    indices: tuple[int, ...],
) -> None:
    table = proof.extract_pymdp_tables(_runner()).table("A_data")
    with pytest.raises(proof.ArtifactProofError) as caught:
        table.get(indices)
    assert caught.value.reason == "internal_error"


def test_deterministic_probabilities_render_as_exact_integer_literals() -> None:
    tables = proof.extract_pymdp_tables(
        _runner(
            replace={
                "A_data": "A_data = ((1, 0), (0, 1))",
                "E_data": "E_data = (0, 1)",
            }
        )
    )
    assert tables.table("A_data").get((0, 0)) == Fraction(1)
    assert tables.table("E_data").values == (Fraction(0), Fraction(1))
    source = proof.render_lean_probe(
        tables,
        variant="symmetric",
        fixture_name="deterministic-control.py",
        fixture_sha256=tables.source_sha256,
    )
    assert "(0 : ℝ)" in source and "(1 : ℝ)" in source
    # Rendering a new candidate never replaces the independent proof reference.
    assert "DiscreteTargetFaithful symArtifactTables symBoolPayload" in source


def test_unknown_probe_variant_does_not_silently_select_an_expected_model() -> None:
    tables = proof.extract_pymdp_tables(_runner())
    with pytest.raises(proof.ArtifactProofError) as caught:
        proof.render_lean_probe(
            tables,
            variant="Symmetric",
            fixture_name="candidate.py",
            fixture_sha256=tables.source_sha256,
        )
    assert caught.value.reason == "internal_error"
    assert "unknown variant" in caught.value.detail


@pytest.fixture
def artifact_copy(tmp_path: Path) -> tuple[Path, Path, dict[str, Any]]:
    root = tmp_path / "repo"
    local = root / SLICE
    for relative in [
        SLICE / "fixtures/pymdp_symmetric_runner.py",
        SLICE / "fixtures/pymdp_asymmetric_runner.py",
        SLICE / "generated/probe_symmetric.lean",
        SLICE / "generated/probe_asymmetric.lean",
        SLICE / MANIFEST,
        EXTRACTOR,
    ]:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    manifest = json.loads((local / MANIFEST).read_text())
    assert (
        proof.manifest_mismatches(
            json.dumps(manifest), repo_root=root, slice_root=local
        )
        == []
    )
    return root, local, manifest


@pytest.mark.parametrize("value", [None, [], "manifest", 1])
def test_manifest_requires_an_object_not_a_json_scalar_or_array(value: Any) -> None:
    problems = proof.manifest_mismatches(
        json.dumps(value), repo_root=ROOT, slice_root=ROOT / SLICE
    )
    assert problems == ["manifest: expected a JSON object"]


@pytest.mark.parametrize(
    "change",
    [
        "missing_metadata",
        "unexpected_verdict",
        "fixtures_array",
        "generated_null",
        "missing_probe",
        "extra_fixture",
    ],
)
def test_manifest_schema_cannot_omit_evidence_or_add_unapproved_fields(
    artifact_copy: tuple[Path, Path, dict[str, Any]],
    change: str,
) -> None:
    root, local, manifest = artifact_copy
    expected: str
    if change == "missing_metadata":
        del manifest["expected_payload"]
        expected = "manifest: missing key expected_payload"
    elif change == "unexpected_verdict":
        manifest["native_claim_ready"] = True
        expected = "manifest: unexpected key native_claim_ready"
    elif change == "fixtures_array":
        manifest["fixtures"] = []
        expected = "manifest: fixtures/generated must be JSON objects"
    elif change == "generated_null":
        manifest["generated"] = None
        expected = "manifest: fixtures/generated must be JSON objects"
    elif change == "missing_probe":
        del manifest["generated"]["generated/probe_asymmetric.lean"]
        expected = "generated: missing key generated/probe_asymmetric.lean"
    else:
        manifest["fixtures"]["../../outside.py"] = "0" * 64
        expected = "fixtures: unexpected key ../../outside.py"
    problems = proof.manifest_mismatches(
        json.dumps(manifest), repo_root=root, slice_root=local
    )
    assert expected in problems


@pytest.mark.parametrize(
    "artifact,mode",
    [
        ("fixture", "deleted"),
        ("fixture", "symlink"),
        ("probe", "deleted"),
        ("probe", "symlink"),
        ("extractor", "deleted"),
        ("extractor", "symlink"),
    ],
)
def test_missing_or_aliased_proof_inputs_cannot_satisfy_manifest_custody(
    artifact_copy: tuple[Path, Path, dict[str, Any]],
    artifact: str,
    mode: str,
) -> None:
    root, local, manifest = artifact_copy
    path = {
        "fixture": local / "fixtures/pymdp_symmetric_runner.py",
        "probe": local / "generated/probe_symmetric.lean",
        "extractor": root / EXTRACTOR,
    }[artifact]
    data = path.read_bytes()
    path.unlink()
    if mode == "symlink":
        external = root.parent / path.name
        external.write_bytes(data)
        path.symlink_to(external)
    problems = proof.manifest_mismatches(
        json.dumps(manifest), repo_root=root, slice_root=local
    )
    assert any("missing or unsafe" in problem for problem in problems)
    if artifact == "fixture":
        assert any(
            "symmetric: cannot verify payload" in problem for problem in problems
        )


def test_generator_disagreement_is_rejected_even_when_stored_hash_matches_disk(
    artifact_copy: tuple[Path, Path, dict[str, Any]],
) -> None:
    root, local, manifest = artifact_copy
    key = "generated/probe_symmetric.lean"
    wrong = "0" * 64
    assert manifest["generated"][key] != wrong
    problems = proof.manifest_mismatches(
        json.dumps(manifest),
        repo_root=root,
        slice_root=local,
        regenerate={key: wrong},
    )
    assert len(problems) == 1 and problems[0].startswith(f"{key}: regenerated ")


def test_rehashing_an_unparseable_fixture_cannot_bless_payload_evidence(
    artifact_copy: tuple[Path, Path, dict[str, Any]],
) -> None:
    root, local, manifest = artifact_copy
    path = local / "fixtures/pymdp_symmetric_runner.py"
    path.write_text("def main():\n    A_data = [")
    manifest["fixtures"][path.name] = proof.sha256_file_strict(path)
    problems = proof.manifest_mismatches(
        json.dumps(manifest), repo_root=root, slice_root=local
    )
    assert any(
        "symmetric: cannot verify payload (syntax_error:" in problem
        for problem in problems
    )
    assert "manifest: expected_payload differs from exact extracted tables" in problems
