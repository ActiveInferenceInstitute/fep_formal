"""Regenerate ``lean/FepSketches/fep_all.lean`` from the body registry.

The aggregate Lake file is the whole-workspace compilation target used by
``lake build FepSketches`` and the CI proof-quality gate. It is tracked so a
fresh clone contains the same canonical Lean input used by the tests.

This script is the single regenerator. It reads the canonical bodies from
:mod:`fep_lean.catalogue.registry` (the same source the catalogue YAML is built
from) and emits one file:

* ``lean/FepSketches/fep_all.lean`` — every topic wrapped in
  ``namespace fep_fepNNN ... end fep_fepNNN``. Per-sketch ``import Mathlib.*``
  lines are deduplicated and hoisted verbatim, preserving the exact dependency
  surface used by standalone verification and the coverage projection.

The aggregate's outer ``namespace fep_fepNNN`` (lowercase, ``fep_`` prefix)
differs deliberately from each sketch's inner ``namespace FEPNNN``: the outer
wrapper exists only to namespace-isolate identically-named helpers across
topics during a single batch compile, while the inner namespaces preserve the
per-topic theorem qualified names used in the manuscript and tests.

Usage
-----
::

    uv run python scripts/_maint_build_fep_all_lean.py

Exit code 0 on success, non-zero if the body registry is empty or the Lean output
directory cannot be created.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from fep_lean.catalogue.generation import (
    check_or_write,
    fep_all_projection_path,
    render_fep_all_lean,
)
from fep_lean.catalogue.registry import BODIES

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LEAN_OUT_DIR = PROJECT_ROOT / "lean" / "FepSketches"
FEP_ALL_PATH = fep_all_projection_path(PROJECT_ROOT)


def write_aggregate(out_dir: Path | None = None) -> tuple[Path, int]:
    """Write ``fep_all.lean`` under *out_dir* and return its topic count."""
    out_dir = out_dir or LEAN_OUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    bodies = dict(BODIES)
    text = render_fep_all_lean(bodies)

    fep_all_path = out_dir / "fep_all.lean"
    fep_all_path.write_text(text, encoding="utf-8")
    return fep_all_path, len(bodies)


def aggregate_is_current(path: Path = FEP_ALL_PATH) -> bool:
    """Return whether *path* exactly matches the canonical sketch projection."""
    expected = render_fep_all_lean(BODIES)
    try:
        return path.read_text(encoding="utf-8") == expected
    except OSError:
        return False


def _aggregate_drift(_root: Path) -> tuple[Path, ...]:
    return () if aggregate_is_current() else (FEP_ALL_PATH,)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail without writing when the tracked aggregate is stale",
    )
    args = parser.parse_args(argv)
    try:
        if args.check:
            return check_or_write(
                PROJECT_ROOT,
                _aggregate_drift,
                None,
                f"{FEP_ALL_PATH.relative_to(PROJECT_ROOT)} is current",
                check=True,
            )
        fep_all_path, n = write_aggregate()
    except (ValueError, OSError) as exc:
        print(f"_maint_build_fep_all_lean: failed: {exc}", file=sys.stderr)
        return 1
    print(f"wrote {n} topic namespaces to {fep_all_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
