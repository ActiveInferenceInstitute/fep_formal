#!/usr/bin/env python3
"""Generate or drift-check formalism breadth/depth projections."""

from __future__ import annotations

import argparse
from pathlib import Path

from fep_formal.catalogue.coverage import (
    formalism_coverage_drift,
    write_formalism_coverage,
)
from fep_formal.catalogue.generation import check_or_write


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    return check_or_write(
        root,
        formalism_coverage_drift,
        write_formalism_coverage,
        "formalism coverage projections are current",
        check=args.check,
    )


if __name__ == "__main__":
    raise SystemExit(main())
