#!/usr/bin/env python3
"""Generate or drift-check the deterministic formalism atlas."""

from __future__ import annotations

import argparse
from pathlib import Path

from fep_lean.catalogue.generation import check_or_write
from fep_lean.output.formalism_atlas import (
    atlas_projection_drift,
    write_formalism_atlas,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    return check_or_write(
        root,
        atlas_projection_drift,
        write_formalism_atlas,
        "formalism atlas projections are current",
        check=args.check,
    )


if __name__ == "__main__":
    raise SystemExit(main())
