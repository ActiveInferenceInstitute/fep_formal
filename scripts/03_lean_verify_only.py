#!/usr/bin/env python3
"""Thin wrapper: 1:1 alias of `fep-lean verify` (Lean only; no Hermes/Gauss).

Exists for auto-discovery environments that enumerate scripts/*.py; the
public surface is the `fep-lean verify` verb itself.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from fep_lean.cli import main

if __name__ == "__main__":
    raise SystemExit(main(["verify", *sys.argv[1:]]))
