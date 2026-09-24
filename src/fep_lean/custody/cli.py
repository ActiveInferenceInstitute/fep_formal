"""Thin argparse adapter for the H2.7 custody census and apply operations.

``census`` composes a read-only drift report; ``apply`` walks the settled
14-phase order behind the verify gate and writes only into the explicit
``--output-dir`` staging tree. Exit codes follow the CLI contract: 0 when the
requested report composed or the apply landed, 1 when the gate or a fail-closed
check refused. Imports stay lazy so parser assembly stays cheap.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("operation", choices=("census", "apply"))
    parser.add_argument(
        "--specs-dir",
        type=Path,
        default=None,
        help="explicit specs tree; defaults to <project-root>/specs",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help=(
            "explicit staging output for apply (required); never the live specs tree"
        ),
    )
    parser.add_argument(
        "--expectations",
        type=Path,
        default=None,
        help=(
            "optional JSON with the verify-gate expectations "
            "(required_intact/allowed_stale); default is GATE_EXPECTATIONS"
        ),
    )
    parser.add_argument(
        "--authorized",
        action="append",
        metavar="PATH",
        help="authorized forced-change path (repo-relative); repeatable",
    )


def _load_expectations(path: Path | None) -> Any:
    if path is None:
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError("expectations JSON must be an object")
    from fep_lean.custody.verify import Expectations

    required = data.get("required_intact", ())
    allowed = data.get("allowed_stale", ())
    if not isinstance(required, list) or not isinstance(allowed, list):
        raise TypeError("expectations fields must be arrays")
    if not all(isinstance(item, str) for item in (*required, *allowed)):
        raise ValueError("expectations entries must be strings")
    return Expectations(
        required_intact=tuple(required), allowed_stale=frozenset(allowed)
    )


def _census_report(specs_dir: Path, root: Path) -> dict[str, Any]:
    from fep_lean.custody.census import census as census_from_tree

    report = census_from_tree(specs_dir, root)
    return {
        "status": "ok",
        "gated": report.is_gated(),
        "live_red": [record.path for record in report.live_red()],
        "stale": [record.path for record in report.stale()],
        "records": [asdict(record) for record in report.records],
    }


def run(root: Path, args: argparse.Namespace) -> int:
    from fep_lean.custody.apply import ApplyRefused, apply_refresh

    try:
        specs_dir = (args.specs_dir or root / "specs").resolve()
        if args.operation == "census":
            print(
                json.dumps(_census_report(specs_dir, root), indent=2, allow_nan=False)
            )
            return 0
        if args.output_dir is None:
            raise ValueError("custody apply requires --output-dir")
        report = apply_refresh(
            specs_dir,
            root,
            args.output_dir.resolve(),
            _load_expectations(args.expectations),
            census=None,
            authorized_changes=tuple(args.authorized or ()),
        )
        print(
            json.dumps(
                {
                    "status": "ok",
                    "phases": list(report.phases),
                    "mutations": list(report.mutations),
                    "directives": [
                        {
                            "path": directive.path,
                            "phase": directive.phase,
                            "anchor": directive.anchor.decode("utf-8"),
                            "replacement": directive.replacement.decode("utf-8"),
                        }
                        for directive in report.directives
                    ],
                    "output_dir": report.output_dir,
                    "files_written": report.files_written,
                },
                indent=2,
                allow_nan=False,
            )
        )
        return 0
    except (ApplyRefused, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        return 1
