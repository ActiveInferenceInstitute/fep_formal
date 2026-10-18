"""Exact current Lean module headers and source-only closure extraction."""

from __future__ import annotations

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
