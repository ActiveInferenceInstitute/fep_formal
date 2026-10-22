"""Mutation controls for the exact finite two-state limit review extension."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest
import yaml

from tests._support.fast_relaxation_review import (
    fast_relaxation_review,
    fast_relaxation_theorem_extension,
    reverse_fast_relaxation_raw,
    reverse_fast_relaxation_rows,
)
from tests._support.lean_module_contract import reverse_primary_alignment_raw

ROOT = Path(__file__).resolve().parents[1]


def test_fast_relaxation_fixture_rejects_modified_bytes(tmp_path):
    source = ROOT / "tests/fixtures/fast_relaxation_review_20261020.json"
    target = tmp_path / "tests/fixtures/fast_relaxation_review_20261020.json"
    target.parent.mkdir(parents=True)
    target.write_bytes(source.read_bytes() + b" ")
    with pytest.raises(AssertionError):
        fast_relaxation_review(tmp_path)


@pytest.mark.parametrize("capability", [False, True])
def test_fast_relaxation_inverse_restores_only_reviewed_row(capability):
    change = fast_relaxation_review(ROOT)["capability" if capability else "maturity"]
    unrelated = {"id": "unrelated", "evidence": ["retained"]}
    rows = [copy.deepcopy(unrelated), copy.deepcopy(change["after"])]
    original = copy.deepcopy(rows)
    assert reverse_fast_relaxation_rows(rows, ROOT, capability=capability) == [
        unrelated,
        change["before"],
    ]
    assert rows == original


@pytest.mark.parametrize("capability", [False, True])
@pytest.mark.parametrize("mutation", ["missing", "duplicate", "field"])
def test_fast_relaxation_inverse_rejects_changed_roster_or_field(capability, mutation):
    change = fast_relaxation_review(ROOT)["capability" if capability else "maturity"]
    fields = list(change["after"]) if mutation == "field" else [None]
    for field in fields:
        rows = [copy.deepcopy(change["after"])]
        if mutation == "missing":
            rows.clear()
        elif mutation == "duplicate":
            rows.append(copy.deepcopy(rows[0]))
        else:
            rows[0][field] = "unreviewed"
        with pytest.raises(AssertionError):
            reverse_fast_relaxation_rows(rows, ROOT, capability=capability)


def test_fast_relaxation_raw_inverse_retains_historical_bytes():
    raw = reverse_primary_alignment_raw(
        (ROOT / "config/theorem_maturity.yaml").read_bytes(), ROOT
    )
    before = reverse_fast_relaxation_raw(raw, ROOT)
    review = fast_relaxation_review(ROOT)["maturity"]
    assert yaml.safe_load(before)["topics"][158] == review["before"]


@pytest.mark.parametrize("mutation", ["outside", "inside", "missing", "duplicate"])
def test_fast_relaxation_raw_inverse_rejects_changed_bytes(mutation):
    raw = reverse_primary_alignment_raw(
        (ROOT / "config/theorem_maturity.yaml").read_bytes(), ROOT
    )
    block = fast_relaxation_review(ROOT)["maturity"]["after_raw_block"].encode()
    if mutation == "outside":
        raw += b"# unreviewed\n"
    elif mutation == "inside":
        raw = raw.replace(block, block.replace(b"formalized", b"unreviewed"), 1)
    elif mutation == "missing":
        raw = raw.replace(block, b"", 1)
    else:
        raw += block
    with pytest.raises(AssertionError):
        reverse_fast_relaxation_raw(raw, ROOT)


@pytest.mark.parametrize("mutation", ["missing", "owner"])
def test_fast_relaxation_extension_rejects_missing_or_moved_theorems(mutation):
    owners = fast_relaxation_review(ROOT)["new_theorem_owners"]
    for name in owners:
        declarations = {key: {"source_owner": owner} for key, owner in owners.items()}
        if mutation == "missing":
            del declarations[name]
        else:
            declarations[name]["source_owner"] = "unreviewed.lean"
        with pytest.raises(AssertionError):
            fast_relaxation_theorem_extension(declarations, ROOT)


def test_fast_relaxation_extension_excludes_exactly_four_names():
    owners = fast_relaxation_review(ROOT)["new_theorem_owners"]
    declarations = {key: {"source_owner": owner} for key, owner in owners.items()}
    declarations["unreviewed.fifth"] = {"source_owner": "unreviewed.lean"}
    extension = fast_relaxation_theorem_extension(declarations, ROOT)
    assert extension == set(owners)
    assert len(extension) == 4
    assert declarations.keys() - extension == {"unreviewed.fifth"}
