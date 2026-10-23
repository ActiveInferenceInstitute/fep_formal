#!/usr/bin/env python3
"""Generate deterministic offline catalog artifacts."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from fep_lean.cli import main

if __name__ == "__main__":
    raise SystemExit(main(["catalogue", *sys.argv[1:]]))
