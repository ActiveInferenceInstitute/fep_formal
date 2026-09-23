#!/usr/bin/env python3
"""Command-line client for the Prove2me Lean-formalization platform.

Thin argparse wrapper over ``fep_lean.prove2me``: identify the authenticated
agent, search theorems, list missions, draft a mission proposal, submit a Lean
proof for verification, and poll a submission until a terminal verdict.  The
API key is resolved by ``Prove2meConfig.load`` (environment or credentials
file) and is never printed; the only output is a single JSON object on stdout
(``{"ok": true, "result": ...}`` on success, ``{"ok": false, "error": ...}``
on failure), so the script is safe to pipe into ``jq``.

Usage:
    uv run python scripts/prove2me.py whoami
    uv run python scripts/prove2me.py search --q "group" --tags algebra,order-theory
    uv run python scripts/prove2me.py mission-list --limit 50
    uv run python scripts/prove2me.py proposal-create --name "My mission" --field-id UUID
    uv run python scripts/prove2me.py submit --theorem-id ID --file solution.lean
    uv run python scripts/prove2me.py poll --submission-id ID --timeout-s 600
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# A direct CLI invocation must not update checkout-local bytecode.
if __name__ == "__main__":
    sys.dont_write_bytecode = True

from fep_lean.prove2me.client import Prove2meClient

from fep_lean.prove2me.config import Prove2meConfig, Prove2meError
from fep_lean.prove2me.missions import wait_for_verdict

CLIENT_TIMEOUT_S = 30.0
POLL_TIMEOUT_S = 600.0
POLL_INTERVAL_S = 5.0


def _add_common(parser: argparse.ArgumentParser, *, with_timeout: bool = True) -> None:
    """Add the flags shared by every subcommand.

    ``with_timeout`` is off for ``poll`` only because that subcommand reuses
    ``--timeout-s`` as its own wait deadline.
    """
    parser.add_argument(
        "--base-url",
        default=None,
        help="API base URL override (default: from configuration)",
    )
    if with_timeout:
        parser.add_argument(
            "--timeout-s",
            type=float,
            default=CLIENT_TIMEOUT_S,
            help=(
                f"per-request transport timeout in seconds "
                f"(default: {CLIENT_TIMEOUT_S})"
            ),
        )


def build_parser() -> argparse.ArgumentParser:
    """Build the argparse parser with one subcommand per endpoint."""
    parser = argparse.ArgumentParser(
        prog="prove2me.py",
        description="Interact with the Prove2me Lean-formalization platform API.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    whoami = subparsers.add_parser(
        "whoami", help="identify the authenticated agent (GET /me)"
    )
    _add_common(whoami)

    search = subparsers.add_parser("search", help="search theorems (GET /theorems)")
    search.add_argument("--q", required=True, help="free-text query")
    search.add_argument("--status", default=None, help="filter by theorem status")
    search.add_argument("--sort", default=None, help="sort order")
    search.add_argument("--tags", default=None, help="comma-separated tags")
    _add_common(search)

    mission_list = subparsers.add_parser(
        "mission-list", help="list missions (GET /missions)"
    )
    mission_list.add_argument(
        "--limit", type=int, default=20, help="page size (default: 20)"
    )
    mission_list.add_argument(
        "--offset", type=int, default=0, help="page offset (default: 0)"
    )
    _add_common(mission_list)

    proposal_create = subparsers.add_parser(
        "proposal-create",
        help="draft a mission proposal (POST /mission-proposals)",
    )
    proposal_create.add_argument("--name", required=True, help="proposal name")
    proposal_create.add_argument(
        "--description", default=None, help="proposal description"
    )
    proposal_create.add_argument(
        "--mission-type",
        default="OpenProblem",
        help="mission type (default: OpenProblem)",
    )
    proposal_create.add_argument(
        "--field-id",
        action="append",
        default=None,
        dest="field_ids",
        metavar="UUID",
        help="field to link (repeatable)",
    )
    proposal_create.add_argument(
        "--env", default=None, help="environment for the mission"
    )
    _add_common(proposal_create)

    submit = subparsers.add_parser(
        "submit", help="submit a Lean proof for verification (POST /verify)"
    )
    submit.add_argument("--theorem-id", required=True, help="theorem to verify against")
    submit.add_argument(
        "--file",
        required=True,
        help="path to the Lean solution file (UTF-8)",
    )
    submit.add_argument(
        "--proof-type", default="prove", help="proof type (default: prove)"
    )
    submit.add_argument(
        "--explanation", default=None, help="optional explanation of the proof"
    )
    _add_common(submit)

    poll = subparsers.add_parser(
        "poll", help="wait for a submission verdict (GET /verify)"
    )
    poll.add_argument("--submission-id", required=True, help="submission id to poll")
    poll.add_argument(
        "--timeout-s",
        type=float,
        default=POLL_TIMEOUT_S,
        help=f"seconds to wait for a terminal verdict (default: {POLL_TIMEOUT_S})",
    )
    poll.add_argument(
        "--poll-s",
        type=float,
        default=POLL_INTERVAL_S,
        help=f"seconds between polls (default: {POLL_INTERVAL_S})",
    )
    _add_common(poll, with_timeout=False)

    return parser


def _split_tags(raw: str | None) -> list[str] | None:
    """Split a comma-separated ``--tags`` value; ``None`` stays ``None``."""
    if raw is None:
        return None
    return [tag for tag in (part.strip() for part in raw.split(",")) if tag]


def _dispatch(client: Prove2meClient, args: argparse.Namespace) -> dict[str, Any]:
    """Run the selected subcommand against the client."""
    if args.command == "whoami":
        return client.whoami()
    if args.command == "search":
        return client.search_theorems(
            q=args.q,
            status=args.status,
            sort=args.sort,
            tags=_split_tags(args.tags),
        )
    if args.command == "mission-list":
        return client.list_missions(limit=args.limit, offset=args.offset)
    if args.command == "proposal-create":
        return client.create_proposal(
            args.name,
            description=args.description,
            mission_type=args.mission_type,
            field_ids=args.field_ids,
            env=args.env,
        )
    if args.command == "submit":
        solution_lean = Path(args.file).read_text(encoding="utf-8")
        return client.submit_proof(
            args.theorem_id,
            solution_lean,
            proof_type=args.proof_type,
            explanation=args.explanation,
        )
    return wait_for_verdict(
        client,
        args.submission_id,
        timeout_s=args.timeout_s,
        poll_s=args.poll_s,
    )


def main(argv: list[str] | None = None) -> int:
    """Parse arguments, run one subcommand, and print a JSON envelope."""
    args = build_parser().parse_args(argv)
    try:
        config = Prove2meConfig.load(base_url=args.base_url)
        if args.command == "poll":
            # On poll, --timeout-s is the verdict wait deadline, not the
            # per-request transport timeout; the client keeps its default.
            client = Prove2meClient(config)
        else:
            client = Prove2meClient(config, timeout_s=args.timeout_s)
        result = _dispatch(client, args)
    except Prove2meError as exc:
        print(
            json.dumps({"ok": False, "error": str(exc), "status_code": exc.status_code})
        )
        return 1
    except OSError as exc:
        print(json.dumps({"ok": False, "error": str(exc), "status_code": None}))
        return 1
    print(json.dumps({"ok": True, "result": result}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
