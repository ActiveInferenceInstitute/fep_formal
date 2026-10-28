"""Deterministic catalog projections from the maintained authoring sources."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from pathlib import Path
from typing import Any

import yaml

from fep_formal.lean_source import (
    LEAN_IMPORT_RE,
    lean_code_without_comments,
    lean_module_source,
)

from . import registry as _registry
from .novelty import load_formalism_novelty
from .registry import assert_roster, validate_body_family_ownership
from .schema import load_catalogue_metadata
from .semantics import load_theorem_maturity, render_proxy_statement


def _display_path(root: Path, path: Path) -> str:
    """Render *path* for display, relative to *root* when possible."""
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def check_or_write(
    root: Path,
    drift_fn: Callable[[Path], Iterable[Path]],
    write_fn: Callable[[Path], Iterable[Path]] | None,
    label: str,
    *,
    check: bool,
    failure_emitter: Callable[..., int] | None = None,
) -> int:
    """Shared fail-closed ``--check``/write shell for generated projections.

    With *check* set, print one ``STALE: <relative path>`` line per drifted
    path and return 1, or ``OK: <label>`` and return 0 when current; *write_fn*
    stays unused. A CLI failure callback can instead emit its structured
    refusal without changing the direct-call default. Otherwise call *write_fn* and print one
    ``Wrote <relative path>`` line per written path, returning 0.
    """
    if check:
        drift = list(drift_fn(root))
        if drift and failure_emitter is not None:
            return failure_emitter(
                "generated projections are stale",
                paths=[_display_path(root, path) for path in drift],
            )
        for path in drift:
            print(f"STALE: {_display_path(root, path)}")
        if drift:
            return 1
        print(f"OK: {label}")
        return 0
    if write_fn is None:
        raise ValueError("write_fn is required when check is False")
    for path in write_fn(root):
        print(f"Wrote {_display_path(root, path)}")
    return 0


def topics_header(topic_count: int) -> str:
    """Return the generated projection header without a fixed roster constant."""
    return (
        f"# FEP / Active Inference / Bayesian Mechanics — {topic_count}-topic Lean4 catalog\n"
        "# Each topic maps to one OpenGauss session when workflows are enabled.\n"
        "# Regenerate: uv run python scripts/_maint_build_topics_catalogue.py\n"
        "# Fields include compile maturity and a separately reviewed semantic disposition.\n"
        "# `latex_equations` is generated from fep_formal.catalogue.registry; do not edit it here.\n"
        "# Manuscript rendering consumes those same generated equation signatures.\n\n"
    )


def strip_sketch_imports(body: str) -> str:
    """Remove imports that the aggregate projection hoists to its header."""
    code = lean_code_without_comments(body)
    lines: list[str] = []
    for raw_line, code_line in zip(
        body.splitlines(keepends=True), code.splitlines(keepends=True), strict=True
    ):
        if LEAN_IMPORT_RE.match(code_line) is None:
            lines.append(raw_line)
        elif raw_line != code_line:
            # Keep comment delimiters even when an import shares their line.
            # Dropping that whole line could open or close a different block.
            lines.append(
                "".join(
                    raw
                    for raw, clean in zip(raw_line, code_line, strict=True)
                    if clean.isspace()
                )
            )
    return "".join(lines).lstrip("\n")


def hoisted_sketch_imports(sketches: Mapping[str, str]) -> tuple[str, ...]:
    """Return the exact distinct sketch imports in deterministic order."""
    return tuple(
        sorted(
            {
                " ".join(match.group().split())
                for body in sketches.values()
                for match in LEAN_IMPORT_RE.finditer(lean_code_without_comments(body))
            }
        )
    )


def topic_id_to_namespace(topic_id: str) -> str:
    """Convert ``fep-NNN`` to the aggregate's ``fep_fepNNN`` namespace."""
    if not topic_id.startswith("fep-"):
        raise ValueError(f"unexpected topic id format: {topic_id!r}")
    suffix = topic_id.removeprefix("fep-")
    if not suffix.isdigit():
        raise ValueError(f"non-numeric topic suffix: {topic_id!r}")
    return f"fep_fep{suffix}"


def render_fep_all_lean(sketches: Mapping[str, str] | None = None) -> str:
    """Render namespace-wrapped topic text with its exact hoisted import union.

    Family shards use this body renderer; the tracked compatibility aggregate
    is rendered by ``fep_all_projection_sources``. Custom source rendering
    retains its existing namespace and import behavior.
    """
    source = dict(_registry.BODIES) if sketches is None else dict(sketches)
    if not source:
        raise ValueError(
            "body registry is empty — refusing to write a degenerate aggregate"
        )

    parts = [
        "-- AUTO-GENERATED by scripts/_maint_build_fep_all_lean.py",
        "-- Source of truth: src/fep_formal/catalogue/bodies/*.py via catalogue.registry",
        "-- Do not edit by hand; regenerate after any canonical body change.",
        "--",
        "-- Each topic body is wrapped in `namespace fep_fepNNN ... end fep_fepNNN`",
        "-- so identically-named helpers across topics never collide during the",
        "-- whole-catalog `lake build FepSketches`. Inner `namespace FEPNNN`",
        "-- blocks are preserved so per-topic qualified names stay stable.",
        *hoisted_sketch_imports(source),
        "",
    ]
    for topic_id in sorted(source):
        namespace = topic_id_to_namespace(topic_id)
        body = strip_sketch_imports(source[topic_id]).rstrip()
        parts.extend((f"namespace {namespace}", "", body, "", f"end {namespace}", ""))
    return lean_module_source("\n".join(parts).rstrip() + "\n")


def fep_all_projection_sources(
    sketches: Mapping[str, str] | None = None,
) -> dict[Path, str]:
    """Render the import-only aggregate and its manifest-owned family shards.

    Paths are relative to ``lean/FepSketches``. The source manifest fixes the
    output universe; filesystem discovery cannot silently shrink it.
    """
    source = dict(_registry.BODIES) if sketches is None else dict(sketches)
    if not source:
        raise ValueError("body registry is empty — refusing empty family projections")
    known = {
        topic for entry in _registry.BODY_MODULE_MANIFEST for topic in entry.bodies
    }
    unknown = set(source) - known
    if unknown:
        raise ValueError(f"topics have no manifested family owner: {sorted(unknown)}")
    shards: dict[Path, str] = {}
    imports: list[str] = []
    for entry in _registry.BODY_MODULE_MANIFEST:
        owned = {topic: source[topic] for topic in entry.bodies if topic in source}
        if not owned:
            continue
        path = Path(entry.lean_projection_relative_path).relative_to("lean/FepSketches")
        shards[path] = render_fep_all_lean(owned)
        module = "FepSketches." + ".".join(path.with_suffix("").parts)
        imports.append(f"import {module}")
    aggregate = lean_module_source(
        "-- AUTO-GENERATED by scripts/_maint_build_fep_all_lean.py\n"
        "-- Import-only compatibility aggregate; topic bodies live in family shards.\n"
        + "\n".join(imports)
        + "\n"
    )
    return {Path("fep_all.lean"): aggregate, **shards}


def fep_all_projection_path(project_root: Path) -> Path:
    """Return the tracked whole-catalog Lean import aggregate path."""
    return Path(project_root) / "lean" / "FepSketches" / "fep_all.lean"


def fep_all_output_drift(output_dir: Path) -> tuple[Path, ...]:
    """Check every expected family output, including missing or tampered shards."""
    drift: list[Path] = []
    sources = fep_all_projection_sources()
    expected_paths = {output_dir / relative for relative in sources}
    for relative, expected in sources.items():
        path = output_dir / relative
        if path.is_symlink() or path.parent.is_symlink():
            drift.append(path)
            continue
        try:
            current = path.read_text(encoding="utf-8")
        except OSError:
            drift.append(path)
            continue
        if current != expected:
            drift.append(path)
    family_dir = output_dir / "families"
    if not family_dir.is_symlink():
        drift.extend(sorted(set(family_dir.rglob("*.lean")) - expected_paths))
    return tuple(drift)


def fep_all_projection_drift(project_root: Path) -> tuple[Path, ...]:
    """Return stale aggregate or family paths from the fixed source manifest."""
    return fep_all_output_drift(fep_all_projection_path(project_root).parent)


def build_topics_data(project_root: Path) -> dict[str, Any]:
    """Join metadata, semantic review, Lean bodies, and equation signatures."""
    root = Path(project_root)
    metadata = load_catalogue_metadata(root / "config" / "catalogue_metadata.yaml")
    assert_roster(metadata.topic_ids)
    validate_body_family_ownership(
        {record.id: record.family for record in metadata.records}
    )
    audit = load_theorem_maturity(
        root / "config" / "theorem_maturity.yaml",
        roster_ids=metadata.topic_ids,
    )
    reviews = audit.by_topic_id
    if [row.id for row in metadata.records] != [record.id for record in audit.records]:
        raise ValueError("catalog metadata and theorem maturity rosters differ")
    from fep_formal.formal.declarations import composed_theorem_sources

    load_formalism_novelty(
        root / "config" / "formalism_novelty.yaml",
        metadata.topic_ids,
        composed_sources=composed_theorem_sources(root),
    )

    rows: list[dict[str, Any]] = []
    for meta in metadata.records:
        review = reviews[meta.id]
        rows.append(
            {
                "id": meta.id,
                "title": meta.title,
                "area": meta.area,
                "family": meta.family,
                "mathlib_modules": list(meta.mathlib_modules),
                "mathlib_status": meta.mathlib_status,
                "primary_theorem": review.primary_theorem,
                "supporting_theorems": list(review.supporting_theorems),
                "boundary_theorems": list(review.boundary_theorems),
                "semantic_disposition": review.disposition.value,
                "nl": render_proxy_statement(review),
                "assumption_review": review.assumption_review,
                "non_vacuity": review.non_vacuity,
                "acceptance_probe": review.acceptance_probe,
                "lean_sketch": _registry.BODIES[meta.id],
                "latex_equations": list(_registry.LATEX_EQUATIONS[meta.id]),
            }
        )
    return {
        "schema_version": 2,
        "roster": {
            "first_id": metadata.roster.first_id,
            "last_id": metadata.roster.last_id,
        },
        "families": list(metadata.families),
        "topics": rows,
    }


def render_topics_yaml(project_root: Path) -> str:
    """Render the checkout and wheel catalog bytes."""
    data = build_topics_data(project_root)
    rows = data["topics"]
    return topics_header(len(rows)) + yaml.safe_dump(
        data,
        sort_keys=False,
        allow_unicode=True,
        width=120,
    )


def catalogue_projection_paths(project_root: Path) -> tuple[Path, Path]:
    """Return checkout and package-data destinations in stable order."""
    root = Path(project_root)
    return (
        root / "config" / "topics.yaml",
        root / "src" / "fep_formal" / "data" / "topics.yaml",
    )


def write_topics_catalogues(project_root: Path) -> tuple[Path, Path]:
    """Write both generated projections from one rendered byte sequence."""
    rendered = render_topics_yaml(project_root)
    paths = catalogue_projection_paths(project_root)
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered, encoding="utf-8")
    return paths


def catalogue_projection_drift(project_root: Path) -> list[Path]:
    """Return generated paths whose current bytes differ from canonical output."""
    expected = render_topics_yaml(project_root)
    return [
        path
        for path in catalogue_projection_paths(project_root)
        if not path.is_file() or path.read_text(encoding="utf-8") != expected
    ]
