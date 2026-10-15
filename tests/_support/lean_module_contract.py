"""Exact current Lean module headers and source-only closure extraction."""

from __future__ import annotations

import re

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
