#!/usr/bin/env python3
"""Regenerate or check the checkout and packaged topic catalogues."""

from __future__ import annotations

import argparse
from pathlib import Path

from fep_lean.catalogue.generation import (
    build_topics_data,
    catalogue_projection_drift,
    check_or_write,
    write_topics_catalogues,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail when either generated catalogue projection is stale",
    )
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    if args.check:
        return check_or_write(
            root,
            catalogue_projection_drift,
            None,
            "checkout and package topic catalogues are current",
            check=True,
        )

    paths = write_topics_catalogues(root)
    topic_count = len(build_topics_data(root)["topics"])
    print(f"Wrote {topic_count} topics to {paths[0]} and {paths[1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
