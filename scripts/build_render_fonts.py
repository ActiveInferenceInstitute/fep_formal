#!/usr/bin/env python3
"""Generate, drift-check, or probe the manuscript's font requirement.

The requirement is derived from the sources: every non-ASCII codepoint the
manuscript typesets, split by the face that carries it. ``--check`` fails when
the document starts using a glyph the committed record does not list, which is
the moment a maintainer must confirm the render host's font covers it.
``--probe`` asks the host's own fontconfig whether the selected families cover
the whole set, and is the preflight ``scripts/render_publication.py`` runs.

Usage:
    uv run python scripts/build_render_fonts.py
    uv run python scripts/build_render_fonts.py --check
    uv run python scripts/build_render_fonts.py --probe
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# A direct check invocation must not update checkout-local bytecode.
if __name__ == "__main__":
    sys.dont_write_bytecode = True

from fep_lean.catalogue.generation import check_or_write
from fep_lean.output.render_fonts import (
    FontProbeError,
    font_coverage_defects,
    render_font_projection,
)

PROJECTION = Path("docs/render-fonts.json")


def _rendered(project_root: Path) -> str:
    return json.dumps(render_font_projection(project_root), indent=2) + "\n"


def _drift(project_root: Path) -> tuple[Path, ...]:
    target = project_root / PROJECTION
    current = target.read_text(encoding="utf-8") if target.is_file() else ""
    return () if current == _rendered(project_root) else (target,)


def _write(project_root: Path) -> tuple[Path, ...]:
    target = project_root / PROJECTION
    target.write_text(_rendered(project_root), encoding="utf-8")
    return (target,)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="manuscript font requirement projection and host probe"
    )
    parser.add_argument("--check", action="store_true")
    parser.add_argument(
        "--probe",
        action="store_true",
        help="ask the host's fontconfig whether the selected faces cover the set",
    )
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    if args.probe:
        try:
            defects = font_coverage_defects(root)
        except FontProbeError as error:
            print(f"FAIL: {error}")
            return 1
        for line in defects:
            print(f"FAIL: {line}")
        if defects:
            return 1
        print("OK: every typeset codepoint is covered by an installed font")
        return 0
    try:
        return check_or_write(
            root,
            _drift,
            _write,
            "the manuscript font requirement is current",
            check=args.check,
        )
    except FontProbeError as error:
        print(f"FAIL: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
