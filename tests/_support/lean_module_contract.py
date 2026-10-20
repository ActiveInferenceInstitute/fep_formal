"""Exact current Lean module headers and source-only closure extraction."""

from __future__ import annotations

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
    change = exact_information_review(project_root)["owner_changes"][owner]
    assert hashlib.sha256(source.encode()).hexdigest() == change["reviewed_sha256"]
    for addition in [*change["added_imports"], change["added_block"]]:
        assert source.count(addition) == 1
        source = source.replace(addition, "", 1)
    assert hashlib.sha256(source.encode()).hexdigest() == change["released_sha256"]
    return source
