"""Project packaged formal Lean resources into the checkout Lake workspace."""

from __future__ import annotations

from pathlib import Path

from fep_formal.lean_source import lean_module_source

from .manifest import (
    FORMAL_MODULES,
    FormalModuleRole,
    formal_module_imports,
    formal_resource_manifest_drift,
    formal_resource_paths,
)

_AGGREGATE_NOTE = """/-!
This file is generated from the formal module manifest. Scientific cross-topic
witnesses live in family-owned composition leaves; this aggregate intentionally
declares no theorems.
-/
"""


def render_formal_aggregate() -> str:
    """Render the import-only public composition aggregate."""
    imports = "\n".join(
        f"import {module}"
        for module in formal_module_imports(FormalModuleRole.COMPOSITION)
    )
    return lean_module_source(f"{imports}\n\n{_AGGREGATE_NOTE}")


def _aggregate_path(project_root: Path) -> Path:
    paths = formal_resource_paths(
        FormalModuleRole.AGGREGATE,
        project_root=project_root,
    )
    if len(paths) != 1:
        raise ValueError("formal manifest must contain exactly one aggregate module")
    return paths[0]


def formal_aggregate_drift(project_root: Path) -> tuple[Path, ...]:
    """Return the canonical aggregate when it differs from its manifest."""
    path = _aggregate_path(Path(project_root))
    expected = render_formal_aggregate().encode("utf-8")
    return () if path.is_file() and path.read_bytes() == expected else (path,)


def write_formal_aggregate(project_root: Path) -> Path:
    """Materialize the canonical aggregate from the composition-leaf roster."""
    path = _aggregate_path(Path(project_root))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_formal_aggregate(), encoding="utf-8")
    return path


def formal_projection_pairs(project_root: Path) -> tuple[tuple[Path, Path], ...]:
    """Return canonical-resource/workspace-projection pairs in stable order."""
    root = Path(project_root)
    workspace = root / "lean" / "FepSketches"
    return tuple(
        (source, workspace / module.resource)
        for module, source in zip(
            FORMAL_MODULES,
            formal_resource_paths(project_root=root),
            strict=True,
        )
    )


def write_formal_projections(project_root: Path) -> tuple[Path, ...]:
    """Materialize exact resource bytes into the Lake workspace."""
    drift = formal_resource_manifest_drift(project_root)
    if drift:
        rendered = ", ".join(path.as_posix() for path in drift)
        raise ValueError(f"formal resource manifest is incomplete: {rendered}")
    written: list[Path] = []
    for source, target in formal_projection_pairs(project_root):
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
        written.append(target)
    return tuple(written)


def formal_projection_drift(project_root: Path) -> tuple[Path, ...]:
    """Return missing or byte-stale workspace projections."""
    root = Path(project_root)
    manifest_drift = formal_resource_manifest_drift(root)
    projection_drift = tuple(
        target
        for source, target in formal_projection_pairs(root)
        if source.is_file()
        and (not target.is_file() or target.read_bytes() != source.read_bytes())
    )
    return (*manifest_drift, *projection_drift)
