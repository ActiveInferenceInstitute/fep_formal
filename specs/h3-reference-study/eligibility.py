"""Evaluate continuous H3.G0 from accepted H2 evidence without changing carriers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from fep_formal.verification.horizon_acceptance import (
    TERMINAL_RECEIPT,
    validate_continuous_eligibility,
    write_explicit_output,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument(
        "--metadata", required=True, help="project-relative pre-outcome metadata"
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    root = args.project_root.resolve()
    try:
        payload = validate_continuous_eligibility(root, args.metadata)
        if args.output is not None:
            write_explicit_output(
                root,
                args.output,
                payload,
                inputs=(root / TERMINAL_RECEIPT, root / args.metadata),
            )
        print(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False))
        return 0
    except (OSError, ValueError, TypeError, KeyError, RecursionError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
