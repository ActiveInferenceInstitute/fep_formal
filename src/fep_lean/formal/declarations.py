"""Resolve canonical topic and composed Lean declaration names."""

from __future__ import annotations

import re
from pathlib import Path

from fep_lean.catalogue.registry import BODIES
from fep_lean.lean_source import (
    LEAN_THEOREM_RE,
    iter_lean_namespace_scopes,
    lean_code_without_comments,
)

from .manifest import FORMAL_MODULES, FormalModuleRole, formal_resource_paths

_THEOREM_RE = LEAN_THEOREM_RE
_TOP_LEVEL_DECLARATION_RE = re.compile(
    r"^(?:noncomputable\s+)?(?:theorem|lemma|def|abbrev|structure)\s+"
    r"[A-Za-z][A-Za-z0-9_]*",
    re.MULTILINE,
)


def _qualified_theorems(source: str) -> tuple[str, ...]:
    """Parse theorem names while distinguishing namespaces from sections."""
    declarations: list[str] = []
    for line, namespaces, _opened_namespace in iter_lean_namespace_scopes(source):
        if match := _THEOREM_RE.match(line):
            declarations.append(".".join((*namespaces, match.group(1))))
    return tuple(declarations)


def topic_theorem_declarations() -> frozenset[str]:
    """Return qualified theorem declarations from generated aggregate namespaces."""
    declarations: set[str] = set()
    for topic_id, body in BODIES.items():
        digits = topic_id.removeprefix("fep-")
        prefix = f"fep_fep{digits}.FEP{digits}"
        code = lean_code_without_comments(body)
        declarations.update(f"{prefix}.{name}" for name in _THEOREM_RE.findall(code))
    return frozenset(declarations)


def composed_theorem_declarations(
    project_root: Path | None = None,
) -> frozenset[str]:
    """Parse qualified theorem names from canonical packaged formal resources."""
    declarations: set[str] = set()
    for path in formal_resource_paths(
        FormalModuleRole.COMPOSITION,
        project_root=project_root,
    ):
        declarations.update(_qualified_theorems(path.read_text(encoding="utf-8")))
    return frozenset(declarations)


def composed_theorem_sources(
    project_root: Path | None = None,
) -> dict[str, str]:
    """Map each composed theorem to its exact declaration-and-proof source block."""
    sources: dict[str, str] = {}
    for path in formal_resource_paths(
        FormalModuleRole.COMPOSITION,
        project_root=project_root,
    ):
        content = path.read_text(encoding="utf-8")
        code = lean_code_without_comments(content)
        namespace_match = re.search(r"^namespace\s+([^\s]+)\s*$", code, re.MULTILINE)
        if namespace_match is None:
            raise ValueError(f"composition resource has no namespace: {path}")
        namespace = namespace_match.group(1)
        starts = tuple(_TOP_LEVEL_DECLARATION_RE.finditer(code))
        for index, match in enumerate(starts):
            theorem_match = re.match(
                r"(?:theorem|lemma)\s+([A-Za-z][A-Za-z0-9_]*)", match.group(0)
            )
            if theorem_match is None:
                continue
            end = starts[index + 1].start() if index + 1 < len(starts) else len(content)
            declaration = f"{namespace}.{theorem_match.group(1)}"
            if declaration in sources:
                raise ValueError(f"duplicate composed theorem source: {declaration}")
            sources[declaration] = content[match.start() : end]
    return sources


def formal_theorem_modules(project_root: Path | None = None) -> dict[str, str]:
    """Map each manifested formal theorem declaration to its Lean module."""
    modules: dict[str, str] = {}
    for module, path in zip(
        FORMAL_MODULES,
        formal_resource_paths(project_root=project_root),
        strict=True,
    ):
        for declaration in _qualified_theorems(path.read_text(encoding="utf-8")):
            if declaration in modules:
                raise ValueError(f"duplicate formal theorem declaration: {declaration}")
            modules[declaration] = module.lean_module
    return modules


def all_formal_theorem_declarations(
    project_root: Path | None = None,
) -> frozenset[str]:
    """Return every topic or composed theorem addressable by semantic evidence."""
    return topic_theorem_declarations() | frozenset(
        formal_theorem_modules(project_root)
    )
