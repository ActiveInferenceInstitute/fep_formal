#!/usr/bin/env python3
"""Reject a manuscript render whose LaTeX log records errors or dropped glyphs.

The shared rendering template's own success test only looks for four fatal
markers, so ``! `` errors and ``Missing character:`` notes pass as a successful
render (see ``fep_lean.output.render_log``).  This wrapper is the project-side
fail-closed acceptance for a combined PDF build and must be run after
``stage_03_render.py``.

A hosted CI runner has neither XeLaTeX, pandoc, the mermaid CLI, a browser
for the two captured figures, nor the two fonts this document selects, so it
cannot re-run this acceptance.  ``--receipt`` writes what the acceptance found
into a committed file and ``--verify-receipt`` re-reads it, which is how the
gate reaches CI: a chapter edited without a fresh render leaves the receipt
naming a digest the checkout no longer has.

Usage:
    uv run python scripts/check_render_log.py
    uv run python scripts/check_render_log.py --pdf-dir output/pdf
    uv run python scripts/check_render_log.py --receipt docs/render-acceptance.json
    uv run python scripts/check_render_log.py --verify-receipt docs/render-acceptance.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# A direct acceptance invocation must not update checkout-local bytecode.
if __name__ == "__main__":
    sys.dont_write_bytecode = True

import yaml

from fep_lean.output.render_log import (
    build_acceptance_receipt,
    contents_number_overflow_defects,
    mermaid_fallback_defects,
    receipt_defects,
    render_log_defects,
    stale_render_defects,
    uncaptioned_table_defects,
)

DEFAULT_RECEIPT = Path("docs") / "render-acceptance.json"


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
    parser.add_argument(
        "--manuscript-dir",
        type=Path,
        default=None,
        help="authored manuscript sources to compare the render against "
        "(default: manuscript)",
    )
    parser.add_argument(
        "--receipt",
        type=Path,
        default=None,
        help=f"write the acceptance receipt here (default: {DEFAULT_RECEIPT})",
        nargs="?",
        const=DEFAULT_RECEIPT,
    )
    parser.add_argument(
        "--verify-receipt",
        type=Path,
        default=None,
        help="verify a committed receipt against these sources and do nothing "
        "else; this is the half a runner without a LaTeX toolchain can run",
        nargs="?",
        const=DEFAULT_RECEIPT,
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    project_root = Path(__file__).resolve().parents[1]
    if args.verify_receipt is not None:
        return verify_receipt(project_root, args)
    pdf_dir = (
        args.pdf_dir if args.pdf_dir is not None else project_root / "output" / "pdf"
    )
    manuscript_dir = (
        args.manuscript_dir
        if args.manuscript_dir is not None
        else project_root / "manuscript"
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
    vars_path = manuscript_dir / "manuscript_vars.yaml"
    if vars_path.is_file():
        variables = yaml.safe_load(vars_path.read_text(encoding="utf-8"))
    stale = stale_render_defects(manuscript_dir, pdf_dir, variables=variables)
    for line in stale:
        print(f"FAIL: {line}")
    if not stale:
        print("OK: every manuscript source is typeset in the combined render")
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
    status = 1 if failed or fallbacks or stale or uncaptioned or overflowed else 0
    if args.receipt is not None:
        counts = {
            "tex_errors": sum(len(defects.tex_errors) for defects in results),
            "missing_characters": sum(
                len(defects.missing_characters) for defects in results
            ),
            "mermaid_fallbacks": len(fallbacks),
            "stale_sources": len(stale),
            "uncaptioned_tables": len(uncaptioned),
            "contents_number_overflows": len(overflowed),
        }
        receipt = build_acceptance_receipt(manuscript_dir, pdf_dir, counts=counts)
        # A rejected render must not leave a receipt behind claiming otherwise,
        # and must not leave the previous render's receipt in place either --
        # that one describes a tree nobody is shipping any more.
        if not receipt["accepted"]:
            print(
                f"FAIL: not writing {args.receipt}; this render was rejected, "
                f"so no receipt may claim these sources were accepted"
            )
            return 1
        path = (
            args.receipt if args.receipt.is_absolute() else project_root / args.receipt
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(f"OK: wrote the acceptance receipt to {path}")
    return status


def verify_receipt(project_root: Path, args: argparse.Namespace) -> int:
    """Report whether the committed receipt covers this checkout's sources."""

    receipt = (
        args.verify_receipt
        if args.verify_receipt.is_absolute()
        else project_root / args.verify_receipt
    )
    manuscript_dir = (
        args.manuscript_dir
        if args.manuscript_dir is not None
        else project_root / "manuscript"
    )
    defects = receipt_defects(receipt, manuscript_dir)
    for line in defects:
        print(f"FAIL: {line}")
    if defects:
        return 1
    print(
        f"OK: {receipt} records a clean acceptance of exactly these manuscript sources"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
