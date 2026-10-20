"""Read-only capability preflight."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from fep_lean._paths import project_root
from fep_lean.verification.environment import run_validation_checks


def _run_version(cmd: list[str], cwd: Path | None = None) -> tuple[int, str]:
    """Run a bounded version probe for direct command diagnostics."""
    import subprocess

    try:
        proc = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=5, check=False
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 1, str(exc)
    output = (proc.stdout or proc.stderr or "").strip().splitlines()
    return proc.returncode, output[0] if output else "no output"


def run_preflight(*, require_gauss: bool | None = None) -> int:
    """Inspect full capabilities; the compatibility argument never relaxes them.

    Full mode always requires OpenGauss. Keep the legacy keyword accepted,
    without changing process-global environment state during inspection.
    """
    result = run_validation_checks(project_root(), mode="full")
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "ok" else 1


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Validate every capability required by full fep_lean execution"
    )
    parser.add_argument(
        "--require-gauss",
        action="store_true",
        help="retained for explicitness; full mode always requires OpenGauss",
    )
    parser.parse_args(argv)
    raise SystemExit(run_preflight(require_gauss=True))


if __name__ == "__main__":
    main()
