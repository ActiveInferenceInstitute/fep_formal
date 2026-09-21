#!/usr/bin/env python3
"""Generate or drift-check the deterministic formal-kernel dashboard."""

from __future__ import annotations

import argparse
from pathlib import Path

from fep_lean.catalogue.generation import check_or_write
from fep_lean.output.formal_kernel_dashboard import (
    formal_kernel_dashboard_drift,
    write_formal_kernel_dashboard,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    return check_or_write(
        root,
        formal_kernel_dashboard_drift,
        write_formal_kernel_dashboard,
        "formal-kernel dashboard projections are current",
        check=args.check,
    )


if __name__ == "__main__":
    raise SystemExit(main())
