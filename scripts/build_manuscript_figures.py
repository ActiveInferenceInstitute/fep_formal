#!/usr/bin/env python3
"""Produce the manuscript figure PNGs that no other generator writes.

``fep-lean catalogue`` writes the matplotlib figures and ``fep-lean atlas`` /
``fep-lean dashboard`` write the SVG projections, but two chapters cite those
projections as PNGs. This wrapper rasterizes them (see
``fep_lean.output.svg_raster``) so a publication render on a clean checkout has
every figure it references.

Run it after ``fep-lean atlas`` and ``fep-lean dashboard`` and before
``stage_03_render.py``.

Usage:
    uv run python scripts/build_manuscript_figures.py
    uv run python scripts/build_manuscript_figures.py --check
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# A direct build/check invocation must not update checkout-local bytecode.
if __name__ == "__main__":
    sys.dont_write_bytecode = True

from fep_lean.catalogue.generation import check_or_write
from fep_lean.output.svg_raster import (
    SvgRasterError,
    manuscript_png_drift,
    write_manuscript_figure_pngs,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="rasterize the SVG projections the manuscript cites as PNGs"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if a cited PNG is missing or older than its SVG projection",
    )
    return parser


def _drift(project_root: Path) -> tuple[Path, ...]:
    # manuscript_png_drift reports human-readable defect lines; the shared
    # shell prefixes each with "STALE: ".
    return tuple(Path(item) for item in manuscript_png_drift(project_root))


def _write(project_root: Path) -> tuple[Path, ...]:
    produced = write_manuscript_figure_pngs(project_root)
    return tuple(figure.png_path for figure in produced)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    project_root = Path(__file__).resolve().parents[1]
    try:
        return check_or_write(
            project_root,
            _drift,
            _write,
            "every cited manuscript figure PNG is current",
            check=args.check,
        )
    except SvgRasterError as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
