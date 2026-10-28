"""Thin argparse adapter for the H2.7 custody census, apply, and refresh.

``census`` composes a read-only drift report; ``apply`` walks the settled
14-phase order behind the verify gate and writes only into the explicit
``--output-dir`` staging tree; ``refresh`` composes census, the stop-gate,
apply, the read-only verify set, the pre-capture owner gate, and the
optional native capture in one sanctioned command, with mutually exclusive
orchestration modes: ``--plan`` (read-only planning pass journaling state
``planned``), ``--fixpoint`` (bounded staged fixpoint journaling state
``awaiting-commit``), and ``--resume <journal-dir>`` (phase 3; completes
the operation against a committed tip: journal/candidate validation, the
render-acceptance barrier, the full verify set, and the optional native
capture; terminal journal state ``captured``).
Exit codes follow the CLI contract: 0 when the requested report composed,
the apply landed, or the refresh completed (which now implies a claim-ready
native capture whenever ``--native`` was requested), 1 when a gate or a
fail-closed check refused.
Imports stay lazy so parser assembly stays cheap.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from fep_formal._paths import _emit_failure


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("operation", choices=("census", "apply", "refresh"))
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
            "explicit staging output for apply (required); never the live "
            "specs tree. For refresh, an explicit staging directory; the "
            "default is a fresh temporary directory. For fixpoint mode it "
            "is required and holds one fresh round directory per round"
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
    parser.add_argument(
        "--reason",
        default="",
        help="required non-empty for refresh: the audit-trail reason",
    )
    parser.add_argument(
        "--native",
        action="store_true",
        help=(
            "refresh only: after the verify set, run the native Lean capture "
            "(fep-formal verify --fail-on-warnings --receipt "
            "output/native-verification.json). Requires a committed clean "
            "tip: the receipt binds live source bytes, so the tree must "
            "stay frozen for the ~77-minute run"
        ),
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--plan",
        action="store_true",
        help=(
            "refresh plan mode: read-only pass over the fail-closed gates "
            "(reason, clean tip, owner inventory, census, verify gate, "
            "authorized roster, pin check); writes the plan journal and "
            "stops in state planned. Never runs test/audit subprocesses"
        ),
    )
    mode.add_argument(
        "--fixpoint",
        action="store_true",
        help=(
            "refresh fixpoint mode: bounded staged fixpoint over the "
            "settled 14-phase order with the directive chain carried "
            "between rounds; requires --output-dir; stops in state "
            "awaiting-commit (default bound 4 rounds, --max-rounds)"
        ),
    )
    mode.add_argument(
        "--resume",
        type=Path,
        default=None,
        metavar="JOURNAL-DIR",
        help=(
            "refresh resume mode: completes a plan/fixpoint journal "
            "against a committed tip — journal/candidate validation, the "
            "render-acceptance barrier, the full verify set, and the "
            "optional --native capture; terminal journal state captured"
        ),
    )
    parser.add_argument(
        "--max-rounds",
        type=int,
        default=4,
        help="fixpoint only: maximum number of rounds (>= 1; default 4)",
    )
    parser.add_argument(
        "--journal-dir",
        type=Path,
        default=None,
        help=(
            "override of the default journal parent "
            "output/custody-journal; the operation id is the last "
            "directory component"
        ),
    )


def _load_expectations(path: Path | None) -> Any:
    if path is None:
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError("expectations JSON must be an object")
    from fep_formal.custody.verify import Expectations

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
    from fep_formal.custody.census import census as census_from_tree

    report = census_from_tree(specs_dir, root)
    return {
        "status": "ok",
        "gated": report.is_gated(),
        "live_red": [record.path for record in report.live_red()],
        "stale": [record.path for record in report.stale()],
        "records": [asdict(record) for record in report.records],
    }


def _refresh_payload(report: Any) -> dict[str, Any]:
    """Serialize one refresh report under the CLI's JSON output convention.

    ``native_status`` is a derived taxonomy: ``not_requested`` when no
    capture was asked for, ``captured_claim_ready`` when the capture ran
    and its receipt validated against the live tree. Capture failures
    never reach this payload — they raise :class:`RefreshRefused` and the
    CLI reports exit 1 instead.
    """
    validation = report.native.get("validation") if report.native else None
    native_status = (
        "captured_claim_ready"
        if validation and validation["claim_ready"]
        else "not_requested"
    )
    return {
        "status": "ok",
        "operation": "refresh",
        "reason": report.reason,
        "authorized": list(report.authorized),
        "phases": list(report.apply.phases),
        "mutations": list(report.apply.mutations),
        "directives": [
            {
                "path": directive.path,
                "phase": directive.phase,
                "anchor": directive.anchor.decode("utf-8"),
                "replacement": directive.replacement.decode("utf-8"),
            }
            for directive in report.apply.directives
        ],
        "output_dir": report.apply.output_dir,
        "files_written": report.apply.files_written,
        "verify_set": report.verify_set,
        "warnings": list(report.warnings),
        "native": report.native,
        "native_status": native_status,
    }


def _plan_payload(journal: dict[str, Any]) -> dict[str, Any]:
    """Serialize one plan journal under the CLI's JSON output convention."""
    return {
        "status": "ok",
        "operation": "refresh",
        "mode": journal["mode"],
        "state": journal["state"],
        "journal_path": journal["journal_path"],
        "reason": journal["reason"],
        "authorized": journal["authorized"],
        "pre_commit_head": journal["pre_commit_head"],
        "census": journal["census"],
        "verify_gate": journal["verify_gate"],
        "pin_check": journal["pin_check"],
        "next_action": journal["next_action"],
        "owner_snapshot": journal["owner_snapshot"],
        "owner_errors": journal["owner_errors"],
    }


def _fixpoint_payload(journal: dict[str, Any]) -> dict[str, Any]:
    """Serialize one fixpoint journal under the CLI's JSON output convention."""
    return {
        "status": "ok",
        "operation": "refresh",
        "mode": journal["mode"],
        "state": journal["state"],
        "journal_path": journal["journal_path"],
        "reason": journal["reason"],
        "authorized": journal["authorized"],
        "pre_commit_head": journal["pre_commit_head"],
        "census": journal["census"],
        "verify_gate": journal["verify_gate"],
        "pin_check": journal["pin_check"],
        "phases": journal["phases"],
        "rounds_completed": journal["rounds_completed"],
        "staged_candidate": journal["staged_candidate"],
        "evidence_note": journal["evidence_note"],
        "next_action": journal["next_action"],
        "owner_snapshot": journal["owner_snapshot"],
        "owner_errors": journal["owner_errors"],
    }


def _resume_payload(journal: dict[str, Any]) -> dict[str, Any]:
    """Serialize one resumed journal under the CLI's JSON output convention.

    ``native_status`` mirrors :func:`_refresh_payload`'s taxonomy; the
    payload carries the recorded verify set and native summary rather than
    re-deriving them from a live report.
    """
    native = journal.get("native") or {}
    validation = native.get("validation")
    native_status = (
        "captured_claim_ready"
        if validation and validation["claim_ready"]
        else "not_requested"
    )
    return {
        "status": "ok",
        "operation": "refresh",
        "mode": journal["mode"],
        "state": journal["state"],
        "journal_path": journal["journal_path"],
        "reason": journal["reason"],
        "authorized": journal["authorized"],
        "resume_head": journal["resume_head"],
        "changed_paths": journal["changed_paths"],
        "verify_set": journal["verify_set"],
        "native": native,
        "native_status": native_status,
        "apply": journal["apply"],
        "render_barrier_paths": journal.get("render_barrier_paths", []),
    }


def run(root: Path, args: argparse.Namespace) -> int:
    from fep_formal.custody.apply import ApplyRefused, apply_refresh
    from fep_formal.custody.refresh import RefreshRefused

    try:
        specs_dir = (args.specs_dir or root / "specs").resolve()
        if args.operation == "census":
            print(
                json.dumps(_census_report(specs_dir, root), indent=2, allow_nan=False)
            )
            return 0
        if args.operation == "refresh":
            import tempfile

            from fep_formal.custody.refresh import fixpoint_refresh, plan_refresh

            authorized = tuple(args.authorized or ())
            if args.plan:
                journal = plan_refresh(
                    specs_dir,
                    root,
                    authorized,
                    args.reason,
                    journal_dir=args.journal_dir,
                )
                print(json.dumps(_plan_payload(journal), indent=2, allow_nan=False))
                return 0
            if args.fixpoint:
                if args.output_dir is None:
                    raise RefreshRefused("fixpoint mode requires --output-dir")
                journal = fixpoint_refresh(
                    specs_dir,
                    root,
                    args.output_dir.resolve(),
                    authorized,
                    args.reason,
                    max_rounds=args.max_rounds,
                    journal_dir=args.journal_dir,
                )
                print(json.dumps(_fixpoint_payload(journal), indent=2, allow_nan=False))
                return 0
            if args.resume is not None:
                from fep_formal.custody.refresh import resume_refresh

                if args.output_dir is None:
                    raise RefreshRefused("resume mode requires --output-dir")
                journal = resume_refresh(
                    specs_dir,
                    root,
                    args.output_dir.resolve(),
                    args.resume,
                    authorized,
                    args.reason,
                    run_native=args.native,
                )
                print(json.dumps(_resume_payload(journal), indent=2, allow_nan=False))
                return 0
            output_dir = (
                args.output_dir.resolve()
                if args.output_dir is not None
                else Path(tempfile.mkdtemp(prefix="fep-lean-custody-refresh-"))
            )
            from fep_formal.custody.refresh import refresh

            report = refresh(
                specs_dir,
                root,
                output_dir,
                authorized=authorized,
                reason=args.reason,
                run_native=args.native,
            )
            print(json.dumps(_refresh_payload(report), indent=2, allow_nan=False))
            return 0
        if args.output_dir is None:
            raise ValueError("custody apply requires --output-dir")
        apply_report = apply_refresh(
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
                    "phases": list(apply_report.phases),
                    "mutations": list(apply_report.mutations),
                    "directives": [
                        {
                            "path": directive.path,
                            "phase": directive.phase,
                            "anchor": directive.anchor.decode("utf-8"),
                            "replacement": directive.replacement.decode("utf-8"),
                        }
                        for directive in apply_report.directives
                    ],
                    "output_dir": apply_report.output_dir,
                    "files_written": apply_report.files_written,
                },
                indent=2,
                allow_nan=False,
            )
        )
        return 0
    except (
        ApplyRefused,
        RefreshRefused,
        OSError,
        ValueError,
        KeyError,
        TypeError,
    ) as exc:
        return _emit_failure(str(exc))
