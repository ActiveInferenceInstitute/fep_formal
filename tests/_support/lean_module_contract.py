"""Exact current Lean module headers and source-only closure extraction."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path

from fep_lean.lean_source import lean_code_without_comments


def _header(imports: tuple[str, ...]) -> str:
    return (
        "module\n"
        + "".join(f"public import {dependency}\n" for dependency in imports)
        + "\n@[expose] public section\n"
    )


def assert_exposed_module_header(source: str, imports: tuple[str, ...]) -> None:
    """Pin the module boundary, exact ordered public imports and exposed scope."""
    assert source.startswith(_header(imports))
    code = lean_code_without_comments(source)
    assert tuple(re.findall(r"(?m)^public import (\S+)$", code)) == imports
    assert not re.search(r"(?m)^import\s", code)
    assert len(re.findall(r"(?m)^module$", code)) == 1


def exposed_module_body(source: str, imports: tuple[str, ...]) -> str:
    """Extract a verified dependency body for inlining in one outer module.

    The caller retains the outer module's imports and exposed public section.
    Topic bodies use legacy imports and are deliberately outside this helper.
    """
    assert_exposed_module_header(source, imports)
    return source.removeprefix(_header(imports))


def topic_projection_sources(aggregate: Path) -> tuple[tuple[Path, str], ...]:
    """Read topic-bearing files named by actual imports, without generator metadata."""
    text = aggregate.read_text(encoding="utf-8")
    names = re.findall(
        r"(?m)^public import FepSketches\.families\.([a-z][a-z0-9_]*)$",
        lean_code_without_comments(text),
    )
    if not names:
        return ((aggregate, text),)
    assert len(names) == len(set(names)), "duplicate family imports"
    return tuple(
        (path, path.read_text(encoding="utf-8"))
        for name in names
        for path in [aggregate.parent / "families" / (name + ".lean")]
    )


def topic_projection_text(aggregate: Path) -> str:
    """Read the actual imported topic sources as one source-only inspection view."""
    return "\n".join(text for _, text in topic_projection_sources(aggregate))


def topic_namespace_owner_modules(aggregate: Path) -> dict[str, str]:
    """Resolve namespace owners from actual generated files, not registry metadata."""
    owners: dict[str, str] = {}
    for path, text in topic_projection_sources(aggregate):
        module = "FepSketches." + ".".join(
            path.relative_to(aggregate.parent).with_suffix("").parts
        )
        for namespace in re.findall(
            r"(?m)^namespace (fep_fep\d+)\s*$", lean_code_without_comments(text)
        ):
            assert namespace not in owners, f"duplicate topic owner: {namespace}"
            owners[namespace] = module
    return owners


_EXACT_INFORMATION_REVIEW_SHA256 = (
    "e6f5c12d6843b04d1ae85f8b7157bc7da55b2c6de7227b24158227882f069d6c"
)


def exact_information_review(project_root: Path) -> dict:
    """Authenticate the new review without changing historical seal fixtures."""
    path = project_root / "tests/fixtures/exact_information_review_20261020.json"
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == _EXACT_INFORMATION_REVIEW_SHA256
    review = json.loads(raw)
    assert review["schema_version"] == 1
    assert review["topic_roster_count"] == 168
    assert review["formal_module_count"] == 72
    assert review["semantic_dispositions_changed"] is False
    assert len(review["edge_changes"]) == 7
    assert len(review["capability_changes"]) == 2
    assert len(review["new_theorem_owners"]) == 35
    return review


def reverse_information_entries(
    entries: list[dict[str, object]], project_root: Path, *, capabilities: bool = False
) -> list[dict[str, object]]:
    """Reverse only exact reviewed complete rows before applying older seals."""
    review = exact_information_review(project_root)
    changes = review["capability_changes" if capabilities else "edge_changes"]

    def key(row: dict) -> object:
        return row["id"] if capabilities else (row["source"], row["target"])

    expected = {key(change["reviewed"]): change for change in changes}
    assert len(expected) == len(changes)
    seen = set()
    restored = []
    for row in entries:
        identity = key(row)
        if identity in expected:
            assert identity not in seen
            seen.add(identity)
            change = expected[identity]
            assert row == change["reviewed"]
            restored.append(dict(change["released"]))
        else:
            restored.append(dict(row))
    assert seen == set(expected)
    return restored


def restore_information_owner(source: str, owner: str, project_root: Path) -> str:
    """Require every current byte, remove approved additions, and hash its preimage."""
    if owner == "src/fep_lean/formal/variational_duality.lean":
        source = restore_finite_rate_distortion_owner(source, project_root)
    if owner == "src/fep_lean/formal/compositions/core.lean":
        source = restore_obligation_core(source, project_root)
    change = exact_information_review(project_root)["owner_changes"][owner]
    assert hashlib.sha256(source.encode()).hexdigest() == change["reviewed_sha256"]
    for addition in [*change["added_imports"], change["added_block"]]:
        assert source.count(addition) == 1
        source = source.replace(addition, "", 1)
    assert hashlib.sha256(source.encode()).hexdigest() == change["released_sha256"]
    return source


_FINITE_RATE_DISTORTION_REVIEW_SHA256 = (
    "72203e995cfa96d7726b244d950f8a1bebb34a2879754d67a59170d948cc0a22"
)


def finite_rate_distortion_review(project_root: Path) -> dict:
    raw = (
        project_root / "tests/fixtures/finite_rate_distortion_review_20261022.json"
    ).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == _FINITE_RATE_DISTORTION_REVIEW_SHA256
    review = json.loads(raw)
    assert review["schema_version"] == 1
    assert len(review["new_theorem_owners"]) == 39
    assert len(review["capability_changes"]) == 1
    return review


def reverse_finite_rate_distortion_capabilities(
    rows: list[dict], project_root: Path
) -> list[dict]:
    changes = finite_rate_distortion_review(project_root)["capability_changes"]
    restored = [dict(row) for row in rows]
    for change in changes:
        indices = [i for i, row in enumerate(restored) if row.get("id") == change["id"]]
        assert len(indices) == 1
        index = indices[0]
        assert restored[index] == change["after"]
        restored[index] = dict(change["before"])
    return restored


def restore_finite_rate_distortion_owner(source: str, project_root: Path) -> str:
    review = finite_rate_distortion_review(project_root)
    for addition in [review["added_import"], review["added_block"]]:
        assert source.count(addition) == 1
        source = source.replace(addition, "", 1)
    assert hashlib.sha256(source.encode()).hexdigest() == review["prior_owner_sha256"]
    return source


def finite_rate_distortion_theorem_extension(
    declarations: dict, project_root: Path
) -> set[str]:
    owners = finite_rate_distortion_review(project_root)["new_theorem_owners"]
    assert owners.keys() <= declarations.keys()
    assert {name: declarations[name]["source_owner"] for name in owners} == owners
    return set(owners)


_OBLIGATION_REVIEW_SHA256 = (
    "7f5f85fde16ed8e62aee4b4ac39ad492949f703c5599246a068ec01055aa2719"
)


def obligation_review(project_root: Path) -> dict:
    raw = (
        project_root / "tests/fixtures/conceptual_obligations_review_20261022.json"
    ).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == _OBLIGATION_REVIEW_SHA256
    review = json.loads(raw)
    assert review["schema_version"] == 1
    assert len(review["edge_changes"]) == 7
    assert (
        len(
            {
                (c["before"]["source"], c["before"]["target"])
                for c in review["edge_changes"]
            }
        )
        == 7
    )
    return review


def reverse_obligation_edges(edges: list[dict], project_root: Path) -> list[dict]:
    restored = copy.deepcopy(edges)
    for change in obligation_review(project_root)["edge_changes"]:
        key = (change["after"]["source"], change["after"]["target"])
        positions = [
            i
            for i, edge in enumerate(restored)
            if (edge["source"], edge["target"]) == key
        ]
        assert len(positions) == 1
        position = positions[0]
        assert restored[position] == change["after"]
        restored[position] = copy.deepcopy(change["before"])
    return restored


def reverse_obligation_model(model: dict, project_root: Path) -> dict:
    assert type(model["schema_version"]) is int and model["schema_version"] == 3
    restored = copy.deepcopy(model)
    restored["schema_version"] = 2
    restored["edges"] = reverse_obligation_edges(model["edges"], project_root)
    return restored


def restore_obligation_core(source: str, project_root: Path) -> str:
    review = obligation_review(project_root)
    block = review["added_core_block"]
    assert source.count(block) == 1
    restored = source.replace(block, "", 1)
    assert hashlib.sha256(restored.encode()).hexdigest() == review["base_core_sha256"]
    return restored


def obligation_theorem_extension(declarations: dict, project_root: Path) -> set[str]:
    owners = obligation_review(project_root)["new_theorem_owners"]
    assert owners.keys() <= declarations.keys()
    assert {name: declarations[name]["source_owner"] for name in owners} == owners
    return set(owners)


_PRIMARY_ALIGNMENT_REVIEW_SHA256 = (
    "d8111a50ec6ded5d5b0a7657408314c01b1b7bab9b9969392d29dc7dd17dd311"
)


def primary_alignment_review(project_root: Path) -> dict:
    raw = (
        project_root / "tests/fixtures/primary_alignment_review_20261022.json"
    ).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == _PRIMARY_ALIGNMENT_REVIEW_SHA256
    review = json.loads(raw)
    assert review["schema_version"] == 1
    assert [x["id"] for x in review["body_changes"]] == ["fep-063"]
    assert [x["id"] for x in review["maturity_changes"]] == ["fep-063", "fep-064"]
    assert len(review["old_declaration_statement_sha256"]) == 2326
    assert set(review["old_declaration_statement_sha256"]) == set(
        review["old_declaration_owners"]
    )
    assert len(review["new_theorem_owners"]) == 1
    return review


def restore_primary_alignment_bodies(bodies: dict, project_root: Path) -> dict:
    restored = dict(bodies)
    for change in primary_alignment_review(project_root)["body_changes"]:
        assert restored[change["id"]] == change["after"]
        restored[change["id"]] = change["before"]
    return restored


def reverse_primary_alignment_rows(rows: list[dict], project_root: Path) -> list[dict]:
    restored = copy.deepcopy(rows)
    for change in primary_alignment_review(project_root)["maturity_changes"]:
        positions = [i for i, row in enumerate(restored) if row["id"] == change["id"]]
        assert len(positions) == 1
        assert restored[positions[0]] == change["after"]
        restored[positions[0]] = copy.deepcopy(change["before"])
    return restored


def reverse_primary_alignment_raw(raw: bytes, project_root: Path) -> bytes:
    review = primary_alignment_review(project_root)
    assert hashlib.sha256(raw).hexdigest() == review["reviewed_maturity_sha256"]
    for change in review["maturity_changes"]:
        current = change["raw_after"].encode()
        assert raw.count(current) == 1
        raw = raw.replace(current, change["raw_before"].encode(), 1)
    assert hashlib.sha256(raw).hexdigest() == review["prior_maturity_sha256"]
    return raw


def restore_primary_alignment_owner(source: str, project_root: Path) -> str:
    review = primary_alignment_review(project_root)
    assert source == review["owner_after"]
    restored = review["owner_before"]
    assert hashlib.sha256(restored.encode()).hexdigest() == review["prior_owner_sha256"]
    return restored


def primary_alignment_theorem_extension(
    declarations: dict, project_root: Path
) -> set[str]:
    review = primary_alignment_review(project_root)
    for name, digest in review["old_declaration_statement_sha256"].items():
        assert name in declarations
        assert (
            hashlib.sha256(declarations[name]["statement"].encode()).hexdigest()
            == digest
        )
        assert (
            declarations[name]["source_owner"] == review["old_declaration_owners"][name]
        )
    owners = review["new_theorem_owners"]
    assert owners.keys() <= declarations.keys()
    for name, digest in review["new_declaration_statement_sha256"].items():
        assert (
            hashlib.sha256(declarations[name]["statement"].encode()).hexdigest()
            == digest
        )
    assert {name: declarations[name]["source_owner"] for name in owners} == owners
    return set(owners)
