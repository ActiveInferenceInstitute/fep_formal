"""Exact inverse for the reviewed finite two-state limit extension."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

FIXTURE_SHA = "76835362aceb98d23a06887e7ae2ccbe26e3c4326a76a7b6475cf57ff7dae40a"


def fast_relaxation_review(root: Path) -> dict:
    raw = (root / "tests/fixtures/fast_relaxation_review_20261020.json").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == FIXTURE_SHA
    review = json.loads(raw)
    assert review["schema_version"] == 1
    return review


def reverse_fast_relaxation_rows(
    rows: list[dict], root: Path, *, capability: bool = False
) -> list[dict]:
    change = fast_relaxation_review(root)["capability" if capability else "maturity"]
    restored = copy.deepcopy(rows)
    matches = [i for i, row in enumerate(restored) if row.get("id") == change["id"]]
    assert len(matches) == 1
    index = matches[0]
    assert restored[index] == change["after"]
    restored[index] = copy.deepcopy(change["before"])
    return restored


def reverse_fast_relaxation_raw(raw: bytes, root: Path) -> bytes:
    change = fast_relaxation_review(root)["maturity"]
    assert hashlib.sha256(raw).hexdigest() == change["after_raw_file_sha256"]
    after = change["after_raw_block"].encode()
    assert raw.count(after) == 1
    restored = raw.replace(after, change["before_raw_block"].encode(), 1)
    assert hashlib.sha256(restored).hexdigest() == change["before_raw_file_sha256"]
    return restored


def fast_relaxation_theorem_extension(declarations: dict, root: Path) -> set[str]:
    owners = fast_relaxation_review(root)["new_theorem_owners"]
    assert owners.keys() <= declarations.keys()
    assert {name: declarations[name]["source_owner"] for name in owners} == owners
    return set(owners)
