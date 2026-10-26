"""Live finite-path contract and exact, nonpromoting historical comparisons."""

import ast
import copy
from pathlib import Path

import pytest
import yaml

from fep_lean.methods.model import _theorem_sources
from tests._support import landauer_epoch as epoch

ROOT = Path(__file__).resolve().parents[1]


def inputs():
    record = epoch.review()
    owners = {owner: (ROOT / owner).read_text() for owner in record["owners"]}
    owner = "src/fep_lean/catalogue/bodies/core_thermodynamics.py"
    tree = ast.parse(owners[owner])
    bodies = ast.literal_eval(
        next(
            node.value
            for node in tree.body
            if isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "BODIES"
        )
    )
    body = bodies["fep-050"]
    raw = (ROOT / "config/theorem_maturity.yaml").read_bytes()
    return {
        "owners": owners,
        "body": body,
        "maturity_raw": raw,
        "maturity_rows": yaml.safe_load(raw)["topics"],
        "edges": yaml.safe_load(
            (ROOT / "config/formalism_relations.yaml").read_bytes()
        )["edges"],
        "declarations": _theorem_sources(body, owner, prefix="fep_fep050"),
    }


def test_live_current_contract_and_copied_historical_view():
    data = inputs()
    original = copy.deepcopy(data)
    epoch.current_contract(**data)
    view = epoch.statement_view(data["declarations"])
    record = epoch.review()
    for name, change in record["changed_statements"].items():
        assert view[name]["statement"] == change["before"]["statement"]
        assert data["declarations"][name]["statement"] == change["after"]["statement"]
    assert data == original
    assert epoch.theorem_extension(data["declarations"]) == set(record["new_theorems"])
    assert (
        epoch.bodies_before({"fep-050": data["body"]})["fep-050"]
        == record["body"]["before"]
    )
    assert (
        epoch._sha(epoch.maturity_before(data["maturity_raw"]))
        == record["maturity_raw"]["before_sha256"]
    )
    for owner, change in record["owners"].items():
        assert epoch.source_before(data["owners"][owner], owner) == change["before"]


@pytest.mark.parametrize(
    "mutation",
    [
        "old_row",
        "old_edge",
        "duplicate_row",
        "duplicate_edge",
        "missing_row",
        "missing_edge",
        "units",
        "endpoint",
        "unrelated_maturity_byte",
        "proof_body",
        "old_owner",
        "missing_owner",
        "changed_body",
    ],
)
def test_live_current_contract_rejects_mutations(mutation):
    data = inputs()
    record = epoch.review()
    rows = data["maturity_rows"]
    edges = data["edges"]
    row = next(r for r in rows if r.get("id") == "fep-050")
    edge = next(
        r for r in edges if (r.get("source"), r.get("target")) == ("fep-050", "fep-049")
    )
    owner = next(iter(record["owners"]))
    if mutation == "old_row":
        rows[rows.index(row)] = record["maturity"]["before"]
    elif mutation == "old_edge":
        edges[edges.index(edge)] = record["edge"]["before"]
    elif mutation == "duplicate_row":
        rows.append(copy.deepcopy(row))
    elif mutation == "duplicate_edge":
        edges.append(copy.deepcopy(edge))
    elif mutation == "missing_row":
        rows.remove(row)
    elif mutation == "missing_edge":
        edges.remove(edge)
    elif mutation == "units":
        row["assumption_review"] += " Heat is dimensionless."
    elif mutation == "endpoint":
        edge["rationale"] += " Use the unconditional primary endpoint."
    elif mutation == "unrelated_maturity_byte":
        data["maturity_raw"] += b"\n"
    elif mutation == "proof_body":
        data["owners"][owner] += "\n# changed proof owner\n"
    elif mutation == "old_owner":
        data["owners"][owner] = record["owners"][owner]["before"]
    elif mutation == "missing_owner":
        del data["owners"][owner]
    elif mutation == "changed_body":
        data["body"] += "\n"
    with pytest.raises((AssertionError, KeyError)):
        epoch.current_contract(**data)


@pytest.mark.parametrize("mutation", ["missing", "owner", "statement", "cached_digest"])
def test_each_actual_successor_type_is_required(mutation):
    original = inputs()["declarations"]
    record = epoch.review()
    for name in [*record["changed_statements"], *record["new_theorems"]]:
        data = copy.deepcopy(original)
        if mutation == "missing":
            del data[name]
        else:
            field = {
                "owner": "source_owner",
                "statement": "statement",
                "cached_digest": "statement_sha256",
            }[mutation]
            data[name][field] = "unapproved"
        with pytest.raises(AssertionError):
            epoch.statement_view(data)


def test_record_hash_checked_before_json_decode(tmp_path, monkeypatch):
    path = tmp_path / "record.json"
    path.write_text("not JSON")
    monkeypatch.setattr(epoch, "RECORD", path)
    with pytest.raises(AssertionError, match="record changed"):
        epoch.review()


def test_unknown_changes_reach_historical_seals():
    data = inputs()
    altered = data["maturity_raw"] + b"\n"
    assert epoch.maturity_before(altered) == altered
    for owner, source in data["owners"].items():
        changed = source + "\n"
        assert epoch.source_before(changed, owner) == changed
    rows = copy.deepcopy(data["maturity_rows"])
    row = next(r for r in rows if r.get("id") == "fep-050")
    row["assumption_review"] += " unapproved"
    assert epoch.rows_before(rows, "topics") == rows
