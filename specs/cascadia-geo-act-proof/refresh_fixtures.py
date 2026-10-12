#!/usr/bin/env python3
"""Copy the Cascadia river-homing fixtures from an explicitly named GEO-INFER checkout.

The fixtures are GEO-INFER-ACT's committed outputs: the GNN v1 source it
rendered, the ``gnn-geo-infer/1`` artifact GNN's strict exporter produced from
that source, the typed-network sidecar, and GNN's export provenance record.
This tool copies those bytes verbatim and records where they came from. It
never edits, regenerates or reinterprets them; a stale copy is replaced only
by running this tool again against a named checkout.

    uv run python specs/cascadia-geo-act-proof/refresh_fixtures.py \\
        --geo-infer-root /path/to/GEO_INFER
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

SLICE = Path(__file__).resolve().parent
FIXTURES = SLICE / "fixtures"
SOURCE_DIR = Path("GEO-INFER-ACT/examples/cascadia/data")
NAMES = (
    "smith_river_homing.gnn.md",
    "smith_river_homing.geo-infer.json",
    "smith_river_homing.domain.json",
    "smith_river_homing.export.json",
)


def sha256_file(path: Path) -> str:
    """Return the lowercase SHA-256 of a file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    """Copy fixtures and write ``fixtures/provenance.json``."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--geo-infer-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.geo_infer_root.resolve(strict=True)
    source = root / SOURCE_DIR
    missing = [name for name in NAMES if not (source / name).is_file()]
    if missing:
        print(f"missing GEO-INFER fixtures: {missing}", file=sys.stderr)
        return 1

    def git(*arguments: str) -> str:
        return subprocess.check_output(
            ["git", *arguments], cwd=root, text=True, timeout=60
        ).strip()

    FIXTURES.mkdir(parents=True, exist_ok=True)
    for name in NAMES:
        shutil.copyfile(source / name, FIXTURES / name)
    record = {
        "schema_version": "fep-lean/cascadia-fixtures/1",
        "geo_infer_revision": git("rev-parse", "HEAD"),
        "geo_infer_branch": git("rev-parse", "--abbrev-ref", "HEAD"),
        "geo_infer_fixtures_dirty": bool(
            git("status", "--porcelain", "--", str(SOURCE_DIR))
        ),
        "source_directory": SOURCE_DIR.as_posix(),
        "files": {name: sha256_file(FIXTURES / name) for name in NAMES},
    }
    (FIXTURES / "provenance.json").write_text(
        json.dumps(record, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(record, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
