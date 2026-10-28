"""Regenerate the import-only Lean topic aggregate and its family shards.

Canonical bodies live in ``src/fep_formal/catalogue/bodies``. The explicit body
manifest fixes one generated ``lean/FepSketches/families/*.lean`` file per
family. Each shard preserves topic namespaces and hoists exactly its own
body imports; ``fep_all.lean`` publicly imports those shards for compatibility.
Compositions import only the families whose topic namespaces they reference.

``--check`` checks the aggregate and every manifested shard, rejecting missing,
tampered, unexpected or symlinked family outputs without writing. Write mode
refuses foreign or symlinked outputs rather than overwriting them.

Run ``uv run python scripts/_maint_build_fep_all_lean.py`` to regenerate.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from fep_formal.catalogue.generation import (
    check_or_write,
    fep_all_output_drift,
    fep_all_projection_path,
    fep_all_projection_sources,
)
from fep_formal.catalogue.registry import BODIES

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LEAN_OUT_DIR = PROJECT_ROOT / "lean" / "FepSketches"
FEP_ALL_PATH = fep_all_projection_path(PROJECT_ROOT)


def write_aggregate(out_dir: Path | None = None) -> tuple[Path, int]:
    """Write aggregate and family shards; return compatibility path and topic count."""
    out_dir = out_dir or LEAN_OUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    bodies = dict(BODIES)
    sources = fep_all_projection_sources(bodies)
    expected = {out_dir / relative for relative in sources}
    for path in expected:
        if path.is_symlink() or path.parent.is_symlink():
            raise ValueError(f"refusing symlinked projection: {path}")
    unexpected = set((out_dir / "families").rglob("*.lean")) - expected
    if unexpected:
        raise ValueError(f"unmanifested family projections: {sorted(unexpected)}")
    for relative, text in sources.items():
        path = out_dir / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    fep_all_path = out_dir / "fep_all.lean"
    return fep_all_path, len(bodies)


def aggregate_is_current(path: Path = FEP_ALL_PATH) -> bool:
    """Return whether *path* exactly matches the canonical sketch projection."""
    return path.name == "fep_all.lean" and not fep_all_output_drift(path.parent)


def _aggregate_drift(_root: Path) -> tuple[Path, ...]:
    return fep_all_output_drift(FEP_ALL_PATH.parent)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail without writing when the aggregate or any family shard is stale",
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
    print(f"wrote {n} topic namespaces to family shards imported by {fep_all_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
