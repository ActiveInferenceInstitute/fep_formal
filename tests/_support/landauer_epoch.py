"""Exact finite-path source successor views for immutable historical unit seals."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RECORD = ROOT / "tests/fixtures/landauer_epoch_20261026.json"
RECORD_SHA256 = "de8f57cff85a7622f7b637c56aeb0eb36a15706c11405836d45f887999d1bb9a"


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def review() -> dict:
    raw = RECORD.read_bytes()
    assert _sha(raw) == RECORD_SHA256, "Landauer static successor record changed"
    record = json.loads(raw)
    assert record["kind"] == "finite-path-landauer-static-transition"
    assert record["supplies_native_evidence"] is record["scientific_promotion"] is False
    return record


def historical_source_owner(owner: str) -> str:
    """Translate only package identity, retaining the complete relative owner."""
    prefix = "src/fep_formal/"
    if owner.startswith(prefix):
        relative = owner[len(prefix) :]
        parts = relative.split("/")
        if all(part not in {"", ".", ".."} for part in parts) and (
            relative.startswith("formal/")
            and relative.endswith(".lean")
            or relative.startswith("catalogue/bodies/")
            and relative.endswith(".py")
        ):
            return "src/fep_lean/" + relative
    return owner


def current_source_owner(owner: str) -> str:
    """Resolve an authenticated historical owner to its canonical physical path."""
    candidate = owner.replace("src/fep_lean/", "src/fep_formal/", 1)
    return candidate if historical_source_owner(candidate) == owner else owner


def identity_maturity_before(raw: bytes) -> bytes:
    """Invert one CLI label only when the whole result matches the sealed bytes."""
    digest = review()["maturity_raw"]["after_sha256"]
    current = b"native_evidence: A validated receipt from uv run fep-formal verify --fail-on-warnings\n"
    historical = b"native_evidence: A validated receipt from uv run fep-lean verify --fail-on-warnings\n"
    if raw.count(current) != 1:
        return raw
    candidate = raw.replace(current, historical, 1)
    return candidate if _sha(candidate) == digest else raw


def theorem_extension(declarations: dict) -> set[str]:
    """Validate actual successor types before any historical comparison view."""
    record = review()
    expected = {
        name: row["after"] for name, row in record["changed_statements"].items()
    }
    expected.update(record["new_theorems"])
    for name, row in expected.items():
        assert name in declarations
        assert (
            historical_source_owner(declarations[name]["source_owner"])
            == row["source_owner"]
        )
        assert _sha(declarations[name]["statement"].encode()) == row["statement_sha256"]
        assert declarations[name]["statement_sha256"] == row["statement_sha256"]
    return set(record["new_theorems"])


def statement_view(declarations: dict) -> dict:
    """Copy two old types for historical seals; live API results stay unchanged."""
    theorem_extension(declarations)
    result = dict(declarations)
    for name, change in review()["changed_statements"].items():
        result[name] = {**declarations[name], **change["before"]}
    return result


def bodies_before(bodies: dict) -> dict:
    result = dict(bodies)
    row = review()["body"]
    if _sha(result["fep-050"].encode()) == row["after_sha256"]:
        result["fep-050"] = row["before"]
    return result


def rows_before(rows: list[dict], section: str) -> list[dict]:
    if section not in {"topics", "edges"}:
        return copy.deepcopy(rows)
    change = review()["maturity" if section == "topics" else "edge"]
    return [
        copy.deepcopy(change["before"] if row == change["after"] else row)
        for row in rows
    ]


def maturity_before(raw: bytes) -> bytes:
    raw = identity_maturity_before(raw)
    change = review()["maturity_raw"]
    if _sha(raw) != change["after_sha256"]:
        return raw
    before, after = change["before"].encode(), change["after"].encode()
    assert raw.count(after) == 1
    restored = raw.replace(after, before, 1)
    assert _sha(restored) == change["before_sha256"]
    return restored


def source_before(source: str, owner: str) -> str:
    change = review()["owners"].get(historical_source_owner(owner))
    if change is None or _sha(source.encode()) != change["after_sha256"]:
        return source
    before = change["before"]
    assert _sha(before.encode()) == change["before_sha256"]
    return before


def current_contract(
    *,
    owners: dict[str, str],
    body: str,
    maturity_raw: bytes,
    maturity_rows: list[dict],
    edges: list[dict],
    declarations: dict,
) -> None:
    """Require live successor bytes and metadata; historical views are not validation."""
    record = review()
    for owner, change in record["owners"].items():
        assert (
            _sha(owners[current_source_owner(owner)].encode()) == change["after_sha256"]
        )
    assert _sha(body.encode()) == record["body"]["after_sha256"]
    assert (
        _sha(identity_maturity_before(maturity_raw))
        == record["maturity_raw"]["after_sha256"]
    )
    selected = [row for row in maturity_rows if row.get("id") == "fep-050"]
    assert selected == [record["maturity"]["after"]]
    selected_edges = [
        row
        for row in edges
        if (row.get("source"), row.get("target")) == ("fep-050", "fep-049")
    ]
    assert selected_edges == [record["edge"]["after"]]
    theorem_extension(declarations)
