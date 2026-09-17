#!/usr/bin/env python3
"""Render the canonical graphical-abstract asset for the manuscript.

The abstract is an authored image asset whose bytes are pinned by the
``sha256`` in ``manuscript/config.yaml``; this wrapper is its producer (see
``fep_lean.output.graphical_abstract``).  Run it whenever the art changes,
then record the new digest in ``manuscript/config.yaml`` -- the validator
fails closed on any mismatch, so a stale pin cannot ship.  The copy pass in
``scripts/build_manuscript_figures.py`` then republishes the asset under
``output/figures/`` for the combined render.

Usage:
    uv run python scripts/build_graphical_abstract.py
    uv run python scripts/build_graphical_abstract.py --check
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# A direct build/check invocation must not update checkout-local bytecode.
if __name__ == "__main__":
    sys.dont_write_bytecode = True

from fep_lean.output.graphical_abstract import (
    GRAPHICAL_ABSTRACT_RELATIVE,
    render_graphical_abstract,
)
from fep_lean.output.publication_metadata import (
    PublicationMetadataError,
    load_graphical_abstract,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="render the canonical graphical-abstract asset"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate the committed asset against its config pin without writing",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    project_root = Path(__file__).resolve().parents[1]
    if args.check:
        try:
            asset = load_graphical_abstract(project_root)
        except PublicationMetadataError as exc:
            print(f"ERROR: {exc}")
            return 1
        print(
            f"OK: {GRAPHICAL_ABSTRACT_RELATIVE} matches its config pin "
            f"({asset.width_px}x{asset.height_px}, sha256 {asset.sha256[:12]}...)"
        )
        return 0
    target = render_graphical_abstract(project_root)
    print(f"Wrote {target.relative_to(project_root)} ({target.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
