#!/usr/bin/env python3
"""Independently validate a generated fep_formal report bundle."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from fep_formal.output.reporter import validate_report_receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report_root", type=Path, help="path to output/reports/run_...")
    parser.add_argument(
        "--require-complete",
        action="store_true",
        help="require a complete, non-empty full-mode receipt suitable for a verification claim",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="live fep_formal checkout whose source/config digests must match",
    )
    args = parser.parse_args(argv)
    receipt = validate_report_receipt(
        args.report_root,
        require_complete=args.require_complete,
        project_root=args.project_root.resolve(),
    )
    print(json.dumps(receipt, indent=2))
    return 0 if receipt["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
