#!/usr/bin/env python3
"""Compatibility entry point for read-only W2 bridge custody checks.

Default: no writes. --refresh-digests is guarded Signature-only emission.
The source pin is changed only by `fep-formal bridge pin --gnn-root PATH`.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

# Retain the historical compatibility alias for existing import consumers.
from fep_formal.bridge.custody import classify_document as _classify_diff  # noqa: F401
from fep_formal.bridge.operations import emit, status

FEP_LEAN_ROOT = Path(__file__).resolve().parents[2]
GNN_ROOT = FEP_LEAN_ROOT.parent / "GeneralizedNotationNotation"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gnn-root", type=Path, default=GNN_ROOT)
    parser.add_argument("--refresh-digests", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.refresh_digests:
            for model in ("finite", "continuous"):
                emit(FEP_LEAN_ROOT, args.gnn_root, model, refresh=True)
        result = status(FEP_LEAN_ROOT, args.gnn_root)
        print(json.dumps(result, indent=2))
        return 0 if result["status"] == "ok" else 1
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
