#!/usr/bin/env python3
"""Reject a manuscript render whose LaTeX log records errors or dropped glyphs.

The shared rendering template's own success test only looks for four fatal
markers, so ``! `` errors and ``Missing character:`` notes pass as a successful
render (see ``fep_lean.output.render_log``).  This wrapper is the project-side
fail-closed acceptance for a combined PDF build and must be run after
``stage_03_render.py``.

Usage:
    uv run python scripts/check_render_log.py
    uv run python scripts/check_render_log.py --pdf-dir output/pdf
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# A direct acceptance invocation must not update checkout-local bytecode.
if __name__ == "__main__":
    sys.dont_write_bytecode = True

import yaml

from fep_lean.output.render_log import (
    contents_number_overflow_defects,
    mermaid_fallback_defects,
    render_log_defects,
    stale_render_defects,
    uncaptioned_table_defects,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="fail-closed acceptance for a combined manuscript render"
    )
    parser.add_argument(
        "--pdf-dir",
        type=Path,
        default=None,
        help="directory holding the compiler logs (default: output/pdf)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    project_root = Path(__file__).resolve().parents[1]
    pdf_dir = (
        args.pdf_dir if args.pdf_dir is not None else project_root / "output" / "pdf"
    )
    results = render_log_defects(pdf_dir)
    failed = False
    for defects in results:
        for line in defects.report():
            print(line)
        failed = failed or not defects.clean
    fallbacks = mermaid_fallback_defects(pdf_dir)
    for line in fallbacks:
        print(f"FAIL: {line}")
    if not fallbacks:
        print("OK: no mermaid diagram fell back to verbatim source")
    # The renderer resolves ``{{placeholder}}`` tokens from this file, so the
    # staleness check needs it to compare a source line against the rendered
    # line it became. Reading the committed projection costs nothing and keeps
    # this acceptance script free of the catalogue build.
    variables = None
    vars_path = project_root / "manuscript" / "manuscript_vars.yaml"
    if vars_path.is_file():
        variables = yaml.safe_load(vars_path.read_text(encoding="utf-8"))
    stale = stale_render_defects(
        project_root / "manuscript", pdf_dir, variables=variables
    )
    for line in stale:
        print(f"FAIL: {line}")
    if not stale:
        print("OK: no manuscript source is newer than the combined render")
    uncaptioned = uncaptioned_table_defects(pdf_dir)
    for line in uncaptioned:
        print(f"FAIL: {line}")
    if not uncaptioned:
        print("OK: every rendered table carries a caption")
    overflowed = contents_number_overflow_defects(pdf_dir)
    for line in overflowed:
        print(f"FAIL: {line}")
    if not overflowed:
        print("OK: no contents number overflows its number box")
    return 1 if failed or fallbacks or stale or uncaptioned or overflowed else 0


if __name__ == "__main__":
    raise SystemExit(main())
