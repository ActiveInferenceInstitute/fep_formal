"""Rasterize the canonical SVG projections into the PNGs the manuscript cites.

``manuscript/04f_semantic_closure_and_validation.md`` and
``manuscript/04g_finite_active_inference_kernel.md`` include
``../output/figures/formalism-atlas.png`` and
``../output/figures/formal-kernel-dashboard.png``.  Until this module existed no
producer wrote either file: they had been rasterized by hand, so a publication
render on a clean checkout aborted with

    ! Unable to load picture or PDF file '../figures/formalism-atlas.png'.

and every downstream figure number shifted.  A figure a chapter depends on must
have a producer, and that producer must derive it from the same projection the
SVG comes from -- never from a stored copy.

The rasterizer is an external binary (``rsvg-convert``, from librsvg).  Its
absence is a hard failure, not a skipped step: silently omitting a cited figure
is what shipped the defect in the first place.
"""

from __future__ import annotations

import shutil
import subprocess  # nosec B404 - fixed argv, no shell, resolved absolute binary
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

__all__ = [
    "MANUSCRIPT_COPIED_FIGURES",
    "MANUSCRIPT_SVG_FIGURES",
    "SvgRasterError",
    "RasterizedFigure",
    "manuscript_png_drift",
    "rasterize_svg",
    "resolve_rasterizer",
    "write_manuscript_figure_pngs",
]

# Every SVG projection a manuscript chapter cites as a PNG, keyed by the PNG
# name written under ``output/figures/``.  Adding a chapter figure means adding
# a row here, not adding a file by hand.
MANUSCRIPT_SVG_FIGURES: Mapping[str, str] = {
    "formalism-atlas.png": "docs/formalism-atlas.svg",
    "formal-kernel-dashboard.png": "docs/formal-kernel-dashboard.svg",
}
# Authored image assets a chapter cites that must also be published under
# ``output/figures/``. The combined renderer flattens an ``assets/<name>``
# reference to ``../figures/<name>`` relative to ``output/pdf/``, so an asset
# that lives only in ``manuscript/assets/`` renders as a missing figure.
MANUSCRIPT_COPIED_FIGURES: Mapping[str, str] = {
    "graphical-abstract.png": "manuscript/assets/graphical-abstract.png",
}
# Width in pixels of the rasterized output. Fixed so two runs on the same SVG
# produce the same bytes regardless of the host's display metrics.
RASTER_WIDTH_PX = 2000
RASTERIZER = "rsvg-convert"


class SvgRasterError(RuntimeError):
    """A cited figure could not be produced from its SVG projection."""


@dataclass(frozen=True)
class RasterizedFigure:
    """One PNG written from an SVG projection."""

    png_path: Path
    svg_path: Path
    byte_size: int


def resolve_rasterizer() -> Path:
    """Return the SVG rasterizer executable, or fail with an install pointer."""

    found = shutil.which(RASTERIZER)
    if found is None:
        raise SvgRasterError(
            f"{RASTERIZER} is required to produce the manuscript figure PNGs "
            f"({', '.join(sorted(MANUSCRIPT_SVG_FIGURES))}); install librsvg "
            "(macOS: brew install librsvg; Debian: apt-get install librsvg2-bin)"
        )
    return Path(found).resolve()


def rasterize_svg(svg_path: Path, png_path: Path, *, width_px: int = RASTER_WIDTH_PX) -> RasterizedFigure:
    """Rasterize one SVG to PNG at a fixed width.

    Raises:
        SvgRasterError: when the source is missing, the rasterizer is absent,
            or the rasterizer produced no output.
    """

    svg_path = Path(svg_path)
    png_path = Path(png_path)
    if not svg_path.is_file():
        raise SvgRasterError(f"SVG projection not found: {svg_path}")
    executable = resolve_rasterizer()
    png_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        str(executable),
        "--format=png",
        f"--width={width_px}",
        "--keep-aspect-ratio",
        "--background-color=white",
        "--output",
        str(png_path),
        str(svg_path),
    ]
    try:
        completed = subprocess.run(  # nosec B603 - fixed argv, shell=False
            command,
            capture_output=True,
            check=False,
            text=True,
            timeout=120,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise SvgRasterError(f"{RASTERIZER} failed to run for {svg_path}") from exc
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()[:500]
        raise SvgRasterError(f"{RASTERIZER} failed for {svg_path}: {detail}")
    if not png_path.is_file() or png_path.stat().st_size == 0:
        raise SvgRasterError(f"{RASTERIZER} wrote no output for {svg_path}")
    return RasterizedFigure(
        png_path=png_path,
        svg_path=svg_path,
        byte_size=png_path.stat().st_size,
    )


def write_manuscript_figure_pngs(project_root: Path) -> tuple[RasterizedFigure, ...]:
    """Publish every PNG a manuscript chapter cites into ``output/figures/``.

    Rasterizes the SVG projections and copies the authored image assets, so a
    clean checkout has each cited figure at the path the combined renderer
    resolves.
    """

    project_root = Path(project_root)
    figures_dir = project_root / "output" / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    produced: list[RasterizedFigure] = []
    for png_name, svg_relative in sorted(MANUSCRIPT_SVG_FIGURES.items()):
        produced.append(
            rasterize_svg(project_root / svg_relative, figures_dir / png_name)
        )
    for png_name, source_relative in sorted(MANUSCRIPT_COPIED_FIGURES.items()):
        source_path = project_root / source_relative
        if not source_path.is_file():
            raise SvgRasterError(f"authored figure asset not found: {source_relative}")
        destination = figures_dir / png_name
        destination.write_bytes(source_path.read_bytes())
        produced.append(
            RasterizedFigure(
                png_path=destination,
                svg_path=source_path,
                byte_size=destination.stat().st_size,
            )
        )
    return tuple(produced)


def manuscript_png_drift(project_root: Path) -> list[str]:
    """Return the cited PNGs that are absent or older than their SVG source.

    A PNG that predates its SVG is stale by construction: the projection has
    been regenerated since the raster was taken.
    """

    project_root = Path(project_root)
    figures_dir = project_root / "output" / "figures"
    stale: list[str] = []
    for png_name, svg_relative in sorted(
        {**MANUSCRIPT_SVG_FIGURES, **MANUSCRIPT_COPIED_FIGURES}.items()
    ):
        png_path = figures_dir / png_name
        svg_path = project_root / svg_relative
        if not svg_path.is_file():
            stale.append(f"{svg_relative}: figure source missing")
            continue
        if not png_path.is_file():
            stale.append(
                f"output/figures/{png_name}: not produced from {svg_relative}"
            )
            continue
        if png_path.stat().st_mtime < svg_path.stat().st_mtime:
            stale.append(f"output/figures/{png_name}: older than {svg_relative}")
    return stale
