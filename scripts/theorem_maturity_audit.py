#!/usr/bin/env python3
"""Validate and render the maintained semantic theorem-maturity audit."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
AUDIT_PATH = ROOT / "config" / "theorem_maturity.yaml"
OUTPUT_PATH = ROOT / "docs" / "theorem-maturity-audit.md"


# SC-18: the audit data model and Markdown renderer are promoted to an
# importable module so the release-bundle validator no longer executes this
# script's namespace with runpy. These re-exports keep the wrapper's public
# behavior identical.
from fep_lean.catalogue.theorem_maturity_projection import (
    render_markdown,
    validate_audit,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write", action="store_true", help="write the generated Markdown projection"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail without writing when the generated projection is stale",
    )
    args = parser.parse_args(argv)
    data = validate_audit()
    if args.write and args.check:
        parser.error("--write and --check are mutually exclusive")
    if args.write:
        OUTPUT_PATH.write_text(render_markdown(data), encoding="utf-8")
        print(f"Wrote {OUTPUT_PATH}")
    elif args.check:
        expected = render_markdown(data)
        try:
            current = OUTPUT_PATH.read_text(encoding="utf-8")
        except OSError:
            current = ""
        if current != expected:
            print(f"STALE: {OUTPUT_PATH.relative_to(ROOT)}", file=sys.stderr)
            return 1
        print("OK: theorem maturity projection is current")
    else:
        print(f"OK: {len(data['topics'])} theorem-maturity rows validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
