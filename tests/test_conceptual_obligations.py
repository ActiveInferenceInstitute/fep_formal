"""Closed relation obligations and exact historical extension controls."""

from __future__ import annotations

import copy
from dataclasses import FrozenInstanceError
from html.parser import HTMLParser
from pathlib import Path

import pytest
import yaml

from fep_lean.catalogue.relations import EdgeKind, FormalismEdge, load_formalism_graph
from fep_lean.catalogue.semantics import SemanticValidationError
from fep_lean.output.formalism_atlas import _obligation_markup
from tests._support.lean_module_contract import (
    obligation_review,
    obligation_theorem_extension,
    restore_obligation_core,
    reverse_obligation_edges,
    reverse_obligation_model,
)

ROOT = Path(__file__).resolve().parents[1]


def _payload(version=3, obligation="issue:93"):
    row = {
        "source": "fep-001",
        "target": "fep-002",
        "kind": "conceptual",
        "rationale": "An explicit missing carrier bridge.",
    }
    if version == 3:
        row["blocked_by"] = obligation
    return {"schema_version": version, "capabilities": [], "edges": [row]}


def _load(payload, tmp_path):
    path = tmp_path / "relations.yaml"
    path.write_text(yaml.safe_dump(payload))
    return load_formalism_graph(path, roster_ids=("fep-001", "fep-002"))


@pytest.mark.parametrize(
    "token", ["issue:93", "lemma:FEPComposed.missing_carrier_bridge"]
)
def test_schema_three_preserves_obligation_and_immutability(token, tmp_path):
    edge = _load(_payload(obligation=token), tmp_path).edges[0]
    assert edge.blocked_by == token and edge.witness is None
    with pytest.raises(FrozenInstanceError):
        edge.blocked_by = "unreviewed"


def test_explicit_legacy_schema_two_and_old_constructor(tmp_path):
    assert _load(_payload(version=2), tmp_path).edges[0].blocked_by is None
    assert (
        FormalismEdge(
            "fep-001", "fep-002", EdgeKind.CONCEPTUAL, "legacy", None
        ).blocked_by
        is None
    )
    payload = _payload(version=2)
    payload["edges"][0]["blocked_by"] = "issue:93"
    with pytest.raises(SemanticValidationError, match="unknown"):
        _load(payload, tmp_path)


@pytest.mark.parametrize(
    "token",
    [
        None,
        True,
        93,
        [],
        {},
        "",
        " ",
        " issue:93",
        "issue:93 ",
        "issue:0",
        "issue:01",
        "issue:-1",
        "issue:+1",
        "issue:1.0",
        "issue:١",
        "url:https://example.com",
        "lemma:unqualified",
        "lemma:FEPComposed.bad name",
        "lemma:<script>",
    ],
)
def test_obligation_requires_exact_canonical_string(token, tmp_path):
    with pytest.raises(SemanticValidationError):
        _load(_payload(obligation=token), tmp_path)


def test_schema_three_requires_field_without_default(tmp_path):
    payload = _payload()
    del payload["edges"][0]["blocked_by"]
    with pytest.raises(SemanticValidationError, match="missing blocked_by"):
        _load(payload, tmp_path)


@pytest.mark.parametrize("kind", ["formal", "formal_pairing", "blocked_by"])
def test_field_is_forbidden_on_other_kinds(kind, tmp_path):
    payload = _payload()
    payload["edges"][0]["kind"] = kind
    if kind != "blocked_by":
        payload["edges"][0]["witness"] = "FEPComposed.fake_witness"
    with pytest.raises(SemanticValidationError, match="unknown blocked_by"):
        _load(payload, tmp_path)


def test_capability_blocker_kind_remains_distinct(tmp_path):
    payload = _payload()
    payload["capabilities"] = [
        {
            "id": "cap-example",
            "title": "Missing capability",
            "description": "Separate capability node.",
            "status": "open",
        }
    ]
    payload["edges"] = [
        {
            "source": "fep-001",
            "target": "cap-example",
            "kind": "blocked_by",
            "rationale": "Requires capability.",
        }
    ]
    edge = _load(payload, tmp_path).edges[0]
    assert edge.kind is EdgeKind.BLOCKED_BY and edge.blocked_by is None


@pytest.mark.parametrize("version", [True, 2.0, 3.0, 1, 4, "3"])
def test_versions_are_explicit_integer_discriminators(version, tmp_path):
    payload = _payload()
    payload["schema_version"] = version
    with pytest.raises(SemanticValidationError, match="schema_version"):
        _load(payload, tmp_path)


def test_all_current_conceptual_rows_expose_obligations():
    graph = load_formalism_graph(ROOT / "config/formalism_relations.yaml")
    rows = [edge for edge in graph.edges if edge.kind is EdgeKind.CONCEPTUAL]
    assert len(rows) == 6 and all(edge.blocked_by and not edge.witness for edge in rows)
    pair = next(
        edge
        for edge in graph.edges
        if (edge.source, edge.target) == ("fep-016", "fep-032")
    )
    assert pair.kind is EdgeKind.FORMAL_PAIRING and pair.blocked_by is None
    assert pair.witness == "FEPComposed.fep016_quadratic_pairs_fep032_descent"


class _Tags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


@pytest.mark.parametrize(
    "token",
    [
        "lemma:<script>alert(1)</script>",
        'issue:93" onclick="bad',
        "issue:١",
        "javascript:alert(1)",
        "lemma:FEPComposed.missing",
    ],
)
def test_renderer_escapes_tokens_without_links(token):
    parsed = _Tags()
    parsed.feed(_obligation_markup(token))
    assert parsed.tags == [("code", {})]


def test_renderer_keeps_canonical_issue_literal_and_offline():
    parsed = _Tags()
    markup = _obligation_markup("issue:93")
    parsed.feed(markup)
    assert parsed.tags == [("code", {})]
    assert "issue:93" in markup and "https://" not in markup


def test_inverse_restores_exact_rows_without_mutating_input():
    review = obligation_review(ROOT)
    rows = [copy.deepcopy(change["after"]) for change in review["edge_changes"]]
    original = copy.deepcopy(rows)
    assert reverse_obligation_edges(rows, ROOT) == [
        c["before"] for c in review["edge_changes"]
    ]
    assert rows == original


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "field"])
def test_inverse_rejects_each_bad_row(mutation):
    changes = obligation_review(ROOT)["edge_changes"]
    for index, change in enumerate(changes):
        for field in list(change["after"]) if mutation == "field" else [None]:
            rows = [copy.deepcopy(c["after"]) for c in changes]
            if mutation == "missing":
                del rows[index]
            elif mutation == "duplicate":
                rows.append(copy.deepcopy(rows[index]))
            else:
                rows[index][field] = "unreviewed"
            with pytest.raises(AssertionError):
                reverse_obligation_edges(rows, ROOT)


def test_model_inverse_requires_exact_version():
    model = yaml.safe_load((ROOT / "config/formalism_relations.yaml").read_text())
    assert reverse_obligation_model(model, ROOT)["schema_version"] == 2
    for version in [2, 3.0, True, 4]:
        candidate = copy.deepcopy(model)
        candidate["schema_version"] = version
        with pytest.raises(AssertionError):
            reverse_obligation_model(candidate, ROOT)


def test_fixture_authenticates_exact_bytes(tmp_path):
    source = ROOT / "tests/fixtures/conceptual_obligations_review_20261022.json"
    target = tmp_path / "tests/fixtures/conceptual_obligations_review_20261022.json"
    target.parent.mkdir(parents=True)
    target.write_bytes(source.read_bytes() + b" ")
    with pytest.raises(AssertionError):
        obligation_review(tmp_path)


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "old_proof"])
def test_core_inverse_seals_all_old_proofs(mutation):
    review = obligation_review(ROOT)
    source = (ROOT / review["core_owner"]).read_text()
    block = review["added_core_block"]
    if mutation == "missing":
        source = source.replace(block, "", 1)
    elif mutation == "duplicate":
        source += block
    else:
        source = source.replace("namespace FEPComposed", "namespace Tampered", 1)
    with pytest.raises(AssertionError):
        restore_obligation_core(source, ROOT)


@pytest.mark.parametrize("mutation", ["missing", "owner"])
def test_extension_rejects_missing_or_moved_theorem(mutation):
    owners = obligation_review(ROOT)["new_theorem_owners"]
    declarations = {name: {"source_owner": owner} for name, owner in owners.items()}
    name = next(iter(owners))
    if mutation == "missing":
        del declarations[name]
    else:
        declarations[name]["source_owner"] = "unreviewed.lean"
    with pytest.raises(AssertionError):
        obligation_theorem_extension(declarations, ROOT)


def test_extension_does_not_hide_extra_theorem():
    owners = obligation_review(ROOT)["new_theorem_owners"]
    declarations = {name: {"source_owner": owner} for name, owner in owners.items()}
    declarations["FEPComposed.unreviewed_extra"] = {"source_owner": "unreviewed.lean"}
    extension = obligation_theorem_extension(declarations, ROOT)
    assert len(extension) == 1
    assert declarations.keys() - extension == {"FEPComposed.unreviewed_extra"}


_PAIRING_CONTROLS = """module
public import FepSketches.compositions.core
public import Mathlib.Tactic.NormNum

@[expose] public section

namespace FEP105RouteControls

theorem positive :
    0 ≤ (2 : ℝ) * (2 - 0) ^ 2 ∧
    (fep_fep032.FEP032.fep032_quadraticUpdate (1/2) 0 2 - 0) ^ 2 ≤ (2 - 0) ^ 2 := by
  exact FEPComposed.fep016_quadratic_pairs_fep032_descent 2 (1/2) 0 2
    (by norm_num) (by norm_num) (by norm_num)

theorem zero_precision :
    0 ≤ (0 : ℝ) * (2 - 0) ^ 2 ∧
    (fep_fep032.FEP032.fep032_quadraticUpdate 1 0 2 - 0) ^ 2 ≤ (2 - 0) ^ 2 := by
  exact FEPComposed.fep016_quadratic_pairs_fep032_descent 0 1 0 2
    (by norm_num) (by norm_num) (by norm_num)

theorem step_zero :
    0 ≤ (2 : ℝ) * (2 - 0) ^ 2 ∧
    (fep_fep032.FEP032.fep032_quadraticUpdate 0 0 2 - 0) ^ 2 ≤ (2 - 0) ^ 2 := by
  exact FEPComposed.fep016_quadratic_pairs_fep032_descent 2 0 0 2
    (by norm_num) (by norm_num) (by norm_num)

theorem step_two :
    0 ≤ (2 : ℝ) * (2 - 0) ^ 2 ∧
    (fep_fep032.FEP032.fep032_quadraticUpdate 2 0 2 - 0) ^ 2 ≤ (2 - 0) ^ 2 := by
  exact FEPComposed.fep016_quadratic_pairs_fep032_descent 2 2 0 2
    (by norm_num) (by norm_num) (by norm_num)

theorem fixed_center :
    0 ≤ (2 : ℝ) * (3 - 3) ^ 2 ∧
    (fep_fep032.FEP032.fep032_quadraticUpdate 1 3 3 - 3) ^ 2 ≤ (3 - 3) ^ 2 := by
  exact FEPComposed.fep016_quadratic_pairs_fep032_descent 2 1 3 3
    (by norm_num) (by norm_num) (by norm_num)

theorem interior_strict_numeric :
    (fep_fep032.FEP032.fep032_quadraticUpdate (1/2) 0 2 - 0) ^ 2 = (1 : ℝ) ∧
    (1 : ℝ) < (2 - 0) ^ 2 := by
  norm_num [fep_fep032.FEP032.fep032_quadraticUpdate]

theorem endpoint_energy_equality :
    (fep_fep032.FEP032.fep032_quadraticUpdate 0 0 2 - 0) ^ 2 = (2 - 0 : ℝ) ^ 2 ∧
    (fep_fep032.FEP032.fep032_quadraticUpdate 2 0 2 - 0) ^ 2 = (2 - 0 : ℝ) ^ 2 := by
  norm_num [fep_fep032.FEP032.fep032_quadraticUpdate]

theorem negative_precision : ¬ 0 ≤ (-1 : ℝ) * (2 - 0) ^ 2 := by norm_num

theorem negative_step :
    ¬ (fep_fep032.FEP032.fep032_quadraticUpdate (-1) 0 2 - 0) ^ 2 ≤ (2 - 0 : ℝ) ^ 2 := by
  norm_num [fep_fep032.FEP032.fep032_quadraticUpdate]

theorem oversized_step :
    ¬ (fep_fep032.FEP032.fep032_quadraticUpdate 3 0 2 - 0) ^ 2 ≤ (2 - 0 : ℝ) ^ 2 := by
  norm_num [fep_fep032.FEP032.fep032_quadraticUpdate]

end FEP105RouteControls

#print axioms FEPComposed.fep016_quadratic_pairs_fep032_descent
#print axioms FEP105RouteControls.positive
#print axioms FEP105RouteControls.zero_precision
#print axioms FEP105RouteControls.step_zero
#print axioms FEP105RouteControls.step_two
#print axioms FEP105RouteControls.fixed_center
#print axioms FEP105RouteControls.interior_strict_numeric
#print axioms FEP105RouteControls.endpoint_energy_equality
#print axioms FEP105RouteControls.negative_precision
#print axioms FEP105RouteControls.negative_step
#print axioms FEP105RouteControls.oversized_step
"""


@pytest.mark.serial_lean
def test_supporting_pairing_native_boundary_controls(tmp_path):
    from tests._support.lake import lake_executable
    from tests._support.lean_runner import run_lake_lean_probe

    source = tmp_path / "PairingControls.lean"
    source.write_text(_PAIRING_CONTROLS)
    result = run_lake_lean_probe(
        ["env", "lean", "-DwarningAsError=true", str(source)],
        cwd=ROOT / "lean",
        executable=lake_executable(
            missing="raise", context="conceptual pairing acceptance"
        ),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert not result.stderr
    from fep_lean.verification.formalism_audit import parse_axiom_output

    expected = ("FEPComposed.fep016_quadratic_pairs_fep032_descent",) + tuple(
        "FEP105RouteControls." + name
        for name in (
            "positive",
            "zero_precision",
            "step_zero",
            "step_two",
            "fixed_center",
            "interior_strict_numeric",
            "endpoint_energy_equality",
            "negative_precision",
            "negative_step",
            "oversized_step",
        )
    )
    axioms, errors = parse_axiom_output(result.stdout, expected=expected)
    assert not errors
    assert set(axioms) == set(expected)
    assert all(
        set(values) <= {"propext", "Classical.choice", "Quot.sound"}
        for values in axioms.values()
    )
