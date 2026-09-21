#!/usr/bin/env python3
"""Project packaged cross-topic Lean modules into the Lake workspace."""

from __future__ import annotations

import argparse
from pathlib import Path

from fep_lean.catalogue.generation import check_or_write
from fep_lean.formal import (
    formal_aggregate_drift,
    formal_projection_drift,
    write_formal_aggregate,
    write_formal_projections,
)


def _drift(root: Path) -> tuple[Path, ...]:
    return (*formal_aggregate_drift(root), *formal_projection_drift(root))


def _write(root: Path) -> tuple[Path, ...]:
    return (write_formal_aggregate(root), *write_formal_projections(root))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    return check_or_write(
        root,
        _drift,
        _write,
        "formal Lean workspace projections are current",
        check=args.check,
    )


if __name__ == "__main__":
    raise SystemExit(main())
