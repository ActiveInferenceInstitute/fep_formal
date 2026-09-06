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


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    project_root = Path(__file__).resolve().parents[1]
    if args.check:
        drift = manuscript_png_drift(project_root)
        if drift:
            print("ERROR: stale or missing manuscript figure PNGs")
            for item in drift:
                print(f"  {item}")
            return 1
        print("OK: every cited manuscript figure PNG is current")
        return 0
    try:
        produced = write_manuscript_figure_pngs(project_root)
    except SvgRasterError as exc:
        print(f"ERROR: {exc}")
        return 1
    for figure in produced:
        relative = figure.png_path.relative_to(project_root)
        print(
            f"Wrote {relative} ({figure.byte_size} bytes) from {figure.svg_path.name}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
