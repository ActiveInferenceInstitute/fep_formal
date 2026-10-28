#!/usr/bin/env python3
"""Capture canonical Chrome/CDP browser acceptance evidence."""

from __future__ import annotations

import argparse
from pathlib import Path

from fep_formal.output.browser_capture import (
    BrowserCaptureError,
    capture_browser_acceptance,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--browser",
        type=Path,
        help="explicit local Chrome/Chromium executable",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    project_root = Path(__file__).resolve().parents[1]
    try:
        receipt = capture_browser_acceptance(
            project_root,
            executable=args.browser,
        )
    except BrowserCaptureError as exc:
        print(f"ERROR: {exc}")
        return 1
    print(f"Wrote {receipt.relative_to(project_root)} and six bound screenshots")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
