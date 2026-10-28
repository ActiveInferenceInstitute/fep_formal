#!/usr/bin/env python3
"""Build or validate the deterministic FEP Lean evidence bundle."""

from __future__ import annotations

import argparse
from pathlib import Path

from fep_formal.output.release_bundle import (
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
    actions.add_argument(
        "--capture-journal",
        type=Path,
        help="explicit bounded publication capture journal outside the checkout",
    )
    actions.add_argument(
        "--plan-capture",
        action="store_true",
        help="print the capture stage policy without running tools",
    )
    parser.add_argument(
        "--resume", action="store_true", help="revalidate and resume --capture-journal"
    )
    parser.add_argument(
        "--template", type=Path, help="explicit capture rendering template"
    )
    parser.add_argument("--source-date-epoch", type=int, default=0)
    parser.add_argument("--timeout", type=float, default=21600)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    project_root = Path(__file__).resolve().parents[1]
    if args.capture_journal is not None or args.plan_capture:
        from fep_formal.cli import main as run_cli

        if args.output is not None:
            parser.error("--output cannot be combined with a capture action")
        if args.resume and args.capture_journal is None:
            parser.error("--resume requires --capture-journal")
        if args.template is None:
            parser.error("capture requires --template")
        arguments = [
            "--project-root",
            str(project_root),
            "publication-capture",
            "--template",
            str(args.template),
            "--source-date-epoch",
            str(args.source_date_epoch),
            "--timeout",
            str(args.timeout),
        ]
        if args.capture_journal is not None:
            arguments.extend(["--journal", str(args.capture_journal)])
        if args.plan_capture:
            arguments.append("--plan")
        if args.resume:
            arguments.append("--resume")
        return run_cli(arguments)
    if args.resume or args.template is not None:
        parser.error("--resume and --template require a capture action")
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
