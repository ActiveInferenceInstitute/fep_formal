"""Read-only capability preflight."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from fep_lean._paths import _emit_failure, project_root
from fep_lean.verification.environment import run_validation_checks


def run_preflight(*, root: Path | None = None) -> int:
    """Inspect every required full-mode capability without changing the environment."""
    result = run_validation_checks(
        project_root() if root is None else root, mode="full"
    )
    if result["status"] != "ok":
        return _emit_failure("full-mode capabilities unavailable", result=result)
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "ok" else 1


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Validate every capability required by full fep_lean execution"
    )
    parser.parse_args(argv)
    raise SystemExit(run_preflight())


if __name__ == "__main__":
    main()
