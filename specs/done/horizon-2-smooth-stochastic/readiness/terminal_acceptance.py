"""Read-only H2 acceptance and explicit deterministic diagnostic output."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from fep_lean.verification.horizon_acceptance import (
    CURRENT_FILES,
    TERMINAL_RECEIPT,
    diagnostic_record,
    validate_terminal_acceptance,
    write_explicit_output,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("validate", "diagnostics"))
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    root = args.project_root.resolve()
    try:
        payload = (
            asdict(validate_terminal_acceptance(root))
            if args.operation == "validate"
            else diagnostic_record(root)
        )
        if args.output is not None:
            write_explicit_output(
                root,
                args.output,
                payload,
                inputs=tuple(root / p for p in (*CURRENT_FILES, TERMINAL_RECEIPT)),
            )
        print(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False))
        return 0
    except (OSError, ValueError, TypeError, KeyError, RecursionError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
