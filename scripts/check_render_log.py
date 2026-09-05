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

from fep_lean.output.render_log import render_log_defects


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
    pdf_dir = args.pdf_dir if args.pdf_dir is not None else project_root / "output" / "pdf"
    results = render_log_defects(pdf_dir)
    failed = False
    for defects in results:
        for line in defects.report():
            print(line)
        failed = failed or not defects.clean
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
