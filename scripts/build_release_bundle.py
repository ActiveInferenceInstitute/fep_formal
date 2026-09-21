#!/usr/bin/env python3
"""Build or validate the deterministic FEP Lean evidence bundle."""

from __future__ import annotations

import argparse
from pathlib import Path

from fep_lean.output.release_bundle import (
    ReleaseBundleError,
    build_release_bundle,
    run_python_acceptance,
    validate_release_bundle,
    write_numerical_witnesses,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        help="destination .tar.gz archive",
    )
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument(
        "--check",
        action="store_true",
        help="rerender in temporary directories and validate an existing archive",
    )
    actions.add_argument(
        "--run-python-acceptance",
        action="store_true",
        help="run the exact full Python acceptance command and retain its receipts",
    )
    actions.add_argument(
        "--write-numerical-witnesses",
        action="store_true",
        help=(
            "build the numerical-witness receipt and write "
            "output/numerical-witnesses.json"
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    project_root = Path(__file__).resolve().parents[1]
    if (
        not args.run_python_acceptance
        and not args.write_numerical_witnesses
        and args.output is None
    ):
        parser.error(
            "--output is required unless --run-python-acceptance "
            "or --write-numerical-witnesses is used"
        )
    try:
        if args.run_python_acceptance:
            receipt = run_python_acceptance(project_root)
            print(f"Wrote {receipt}")
            return 0
        if args.write_numerical_witnesses:
            receipt = write_numerical_witnesses(project_root)
            print(f"Wrote {receipt}")
            return 0
        if args.check:
            validation = validate_release_bundle(
                args.output,
                project_root=project_root,
            )
            if not validation.claim_ready:
                print("ERROR: release bundle validation failed")
                for error in validation.errors:
                    print(f"  {error}")
                return 1
            print(
                "OK: current deterministic release bundle "
                f"{validation.archive_sha256} ({validation.member_count} members)"
            )
            return 0
        output = build_release_bundle(project_root, args.output)
    except ReleaseBundleError as exc:
        print(f"ERROR: {exc}")
        return 1
    validation = validate_release_bundle(output, project_root=project_root)
    if not validation.claim_ready:
        print("ERROR: written release bundle failed live-source validation")
        for error in validation.errors:
            print(f"  {error}")
        return 1
    print(
        f"Wrote {output} · sha256 {validation.archive_sha256} · "
        f"{validation.member_count} members"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
