#!/usr/bin/env python3
"""Run the pinned Lean declaration/axiom audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from fep_formal.verification.formalism_audit import (
    run_formalism_audit,
    write_formalism_audit_receipt,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--timeout", type=int, default=300)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    result = run_formalism_audit(root, timeout=args.timeout)
    if args.receipt is not None:
        destination = args.receipt
        if not destination.is_absolute():
            destination = root / destination
        write_formalism_audit_receipt(destination, result)
    print(json.dumps(result.as_dict(), indent=2, sort_keys=True))
    return 0 if result.complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
