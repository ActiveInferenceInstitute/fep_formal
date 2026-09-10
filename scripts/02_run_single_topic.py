#!/usr/bin/env python3
"""Verify one topic through the canonical command-line interface."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from fep_lean.cli import main

if __name__ == "__main__":
    arguments = sys.argv[1:]
    if not arguments or arguments[0].startswith("-"):
        print(
            "usage: 02_run_single_topic.py TOPIC_ID [fep-lean topic options...]\n"
            "       an explicit topic id is required (no magic default)"
        )
        raise SystemExit(2)
    raise SystemExit(main(["topic", *arguments]))
