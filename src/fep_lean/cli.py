"""Single canonical command-line interface for fep_lean."""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from fep_lean._paths import project_root, project_root_errors
from fep_lean.catalogue.topics import FEPTopicCatalogue
from fep_lean.output.evidence import (
    build_native_lean_receipt,
    validate_native_lean_receipt,
    write_native_lean_receipt,
)
from fep_lean.output.formal_kernel_dashboard import (
    formal_kernel_dashboard_drift,
    write_formal_kernel_dashboard,
)
from fep_lean.output.formalism_atlas import (
    atlas_projection_drift,
    write_formalism_atlas,
)
from fep_lean.pipeline.orchestrator import run_pipeline, run_single_topic
from fep_lean.verification._subprocess import run_process_group
from fep_lean.verification._toolchain import find_executable, subprocess_env
from fep_lean.verification.environment import run_validation_checks
from fep_lean.verification.lean_verifier import LeanVerifier


def _configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def _setup(root: Path) -> int:
    lean_dir = root / "lean"
    try:
        timeout = int(os.environ.get("FEP_LEAN_SETUP_TIMEOUT_SEC", "1800"))
    except ValueError:
        print("setup failed: FEP_LEAN_SETUP_TIMEOUT_SEC must be an integer", flush=True)
        return 1
    if timeout < 1:
        print("setup failed: FEP_LEAN_SETUP_TIMEOUT_SEC must be positive", flush=True)
        return 1

    lake = find_executable("lake", lean_dir)
    deadline = time.monotonic() + timeout
    if not lake:
        bootstrap = root / "scripts" / "_maint_bootstrap_lean_toolchain.sh"
        if not bootstrap.is_file():
            print(
                "lake executable is unavailable and the bootstrap script is missing",
                flush=True,
            )
            return 1
        bootstrap_env = dict(os.environ)
        elan_home = bootstrap_env.get("ELAN_HOME", str(Path.home() / ".elan"))
        bootstrap_env["ELAN_HOME"] = elan_home
        bootstrap_env["PATH"] = (
            str(Path(elan_home) / "bin") + ":" + bootstrap_env.get("PATH", "")
        )
        bootstrap_result: subprocess.CompletedProcess[None]
        try:
            bootstrap_result = run_process_group(
                ["bash", str(bootstrap)],
                cwd=root,
                env=bootstrap_env,
                timeout=max(1, int(deadline - time.monotonic())),
                check=False,
                capture=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            print(f"setup failed: {exc}", flush=True)
            return 1
        if bootstrap_result.returncode:
            print(
                f"setup failed with exit code {bootstrap_result.returncode}: {bootstrap}",
                flush=True,
            )
            return bootstrap_result.returncode
        return 0

    env = subprocess_env(lean_dir)
    for command in ((lake, "update"), (lake, "exe", "cache", "get"), (lake, "build")):
        try:
            remaining = max(1, int(deadline - time.monotonic()))
            lake_result = run_process_group(
                command, cwd=lean_dir, env=env, timeout=remaining, check=False
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            print(f"setup failed: {exc}", flush=True)
            return 1
        if lake_result.returncode:
            print(
                f"setup failed with exit code {lake_result.returncode}: {' '.join(command)}",
                flush=True,
            )
            return lake_result.returncode
    return 0


def _print_result(result: object) -> int:
    payload = result.as_dict() if hasattr(result, "as_dict") else result
    print(json.dumps(payload, indent=2, default=str))
    return 0 if getattr(result, "complete", False) else 1


def _atlas(root: Path, *, check: bool) -> int:
    """Write or fail-closed drift-check the formalism atlas projection."""
    if check:
        drift = atlas_projection_drift(root)
        if drift:
            for path in drift:
                try:
                    rendered = path.relative_to(root)
                except ValueError:
                    rendered = path
                print(f"STALE: {rendered}")
            return 1
        print("OK: formalism atlas projections are current")
        return 0
    for path in write_formalism_atlas(root):
        try:
            rendered = path.relative_to(root)
        except ValueError:
            rendered = path
        print(f"Wrote {rendered}")
    return 0


def _dashboard(root: Path, *, check: bool) -> int:
    """Write or fail-closed drift-check the formal-kernel dashboard."""
    if check:
        drift = formal_kernel_dashboard_drift(root)
        if drift:
            for path in drift:
                try:
                    rendered = path.relative_to(root)
                except ValueError:
                    rendered = path
                print(f"STALE: {rendered}")
            return 1
        print("OK: formal-kernel dashboard projections are current")
        return 0
    for path in write_formal_kernel_dashboard(root):
        try:
            rendered = path.relative_to(root)
        except ValueError:
            rendered = path
        print(f"Wrote {rendered}")
    return 0


def _verify(
    root: Path,
    topic_ids: list[str] | None,
    area: str | None,
    *,
    receipt_path: Path | None = None,
    fail_on_warnings: bool = False,
) -> int:
    """Compile catalogue sketches with Lean only, without Hermes or Gauss."""
    try:
        catalogue = FEPTopicCatalogue.from_yaml(root / "config" / "topics.yaml")
        topics = catalogue.topics
        if topic_ids:
            known = {topic.id for topic in topics}
            unknown = sorted(set(topic_ids) - known)
            if unknown:
                raise ValueError(f"unknown topic ids: {', '.join(unknown)}")
            topics = [topic for topic in topics if topic.id in topic_ids]
        if area:
            topics = [topic for topic in topics if topic.area == area]
        if not topics:
            raise ValueError("no catalogue topics matched the requested filters")
    except Exception as exc:
        print(
            json.dumps(
                {
                    "status": "error",
                    "mode": "lean-only",
                    "complete": False,
                    "failure_reason": str(exc),
                }
            )
        )
        return 1

    verifier = LeanVerifier(lean_dir=root / "lean", project_root=root)
    mathlib_ok, mathlib_message = verifier.check_mathlib_built()
    if not mathlib_ok:
        print(
            json.dumps(
                {
                    "status": "error",
                    "mode": "lean-only",
                    "complete": False,
                    "catalogue_topics": len(topics),
                    "verified_topics": 0,
                    "mathlib": mathlib_message,
                    "results": [],
                },
                indent=2,
            )
        )
        return 1

    results = verifier.verify_batch([(topic.id, topic.lean_sketch) for topic in topics])
    result_payload = []
    for result in results:
        row = result.as_dict()
        # The verifier removes its temporary source file before returning;
        # do not publish a path that is already stale in the CLI receipt.
        row["lean_file"] = None
        result_payload.append(row)
    compiled_without_sorry = sum(
        result.compiles and not result.has_sorry for result in results
    )
    warning_count = sum(len(getattr(result, "warnings", [])) for result in results)
    verified = sum(
        result.compiles and not result.has_sorry and not getattr(result, "warnings", [])
        for result in results
    )
    sorry_count = sum(result.has_sorry for result in results)
    complete = (
        len(results) == len(topics)
        and compiled_without_sorry == len(topics)
        and (not fail_on_warnings or warning_count == 0)
    )
    receipt_validation: dict[str, Any] | None = None
    if receipt_path is not None:
        receipt = write_native_lean_receipt(
            receipt_path,
            build_native_lean_receipt(root, [topic.id for topic in topics], results),
        )
        receipt_validation = validate_native_lean_receipt(receipt, project_root=root)
        complete = complete and bool(receipt_validation.get("valid", False))
    print(
        json.dumps(
            {
                "status": "ok" if complete else "error",
                "mode": "lean-only",
                "complete": complete,
                "catalogue_topics": len(topics),
                "verified_topics": verified,
                "compiled_without_sorry_topics": compiled_without_sorry,
                "warning_count": warning_count,
                "sorry_count": sorry_count,
                "mathlib": mathlib_message,
                "receipt": str(receipt_path) if receipt_path is not None else None,
                "native_claim_ready": (
                    receipt_validation.get("native_claim_ready", False)
                    if receipt_validation is not None
                    else False
                ),
                "results": result_payload,
            },
            indent=2,
            default=str,
        )
    )
    return 0 if complete else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fep-lean",
        description="Strict FEP Lean catalogue and verification pipeline",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=None,
        help="source checkout containing config/, lean/, manuscript/, and src/",
    )
    parser.add_argument("--verbose", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)
    from fep_lean.bridge.cli import add_arguments

    add_arguments(sub.add_parser("bridge", help="source-bound GNN bridge operations"))
    sub.add_parser("setup", help="explicitly acquire/build the pinned Lean workspace")
    sub.add_parser("preflight", help="run read-only full-mode capability checks")
    verify = sub.add_parser("verify", help="compile catalogue sketches with Lean only")
    verify.add_argument("--area")
    verify.add_argument("--topic", action="append", dest="topics")
    verify.add_argument(
        "--receipt",
        type=Path,
        help="atomically write a typed native-Lean verification receipt",
    )
    verify.add_argument(
        "--fail-on-warnings",
        action="store_true",
        help="treat any Lean warning as a verification failure",
    )
    catalogue = sub.add_parser(
        "catalogue", help="generate deterministic offline catalogue artifacts"
    )
    catalogue.add_argument("--area")
    catalogue.add_argument("--topic", action="append", dest="topics")
    atlas = sub.add_parser(
        "atlas", help="generate the offline formalism composition atlas"
    )
    atlas.add_argument(
        "--check", action="store_true", help="fail if atlas projections are stale"
    )
    dashboard = sub.add_parser(
        "dashboard", help="generate the offline formal-kernel validation dashboard"
    )
    dashboard.add_argument(
        "--check", action="store_true", help="fail if dashboard projections are stale"
    )
    run = sub.add_parser("run", help="run full Hermes, Lean, and SQLite verification")
    run.add_argument("--area")
    run.add_argument("--topic", action="append", dest="topics")
    run.add_argument(
        "--workflow", choices=("verify", "draft", "prove", "review"), default="verify"
    )
    topic = sub.add_parser("topic", help="verify one exact topic")
    topic.add_argument("topic_id")
    topic.add_argument(
        "--workflow", choices=("verify", "draft", "prove", "review"), default="verify"
    )
    sub.add_parser("report", help="run catalogue mode and emit a complete report")
    status = sub.add_parser(
        "status",
        help=(
            "read-only evidence-currency report composing existing checks; "
            "exit 0 means the report composed, not that evidence is current"
        ),
    )
    status.add_argument(
        "--gnn-root",
        type=Path,
        default=None,
        help=(
            "explicit GNN checkout for full source-pin comparison; omit to "
            "report pin presence and the fep_lean side only"
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    _configure_logging(args.verbose or os.environ.get("FEP_LEAN_VERIFY_VERBOSE") == "1")
    previous_project_dir = os.environ.get("FEP_LEAN_PROJECT_ROOT")
    if args.project_root is not None:
        os.environ["FEP_LEAN_PROJECT_ROOT"] = str(args.project_root.resolve())
    try:
        root = project_root()
        missing = project_root_errors(root)
        if missing:
            print(
                json.dumps(
                    {
                        "status": "error",
                        "complete": False,
                        "project_root": str(root),
                        "failure_reason": (
                            "substantive fep-lean commands require a source checkout; "
                            "pass --project-root /path/to/fep_lean. Missing: "
                            + ", ".join(missing)
                        ),
                    },
                    indent=2,
                )
            )
            return 1
        if args.command == "setup":
            return _setup(root)
        if args.command == "bridge":
            from fep_lean.bridge.cli import run as run_bridge

            return run_bridge(root, args)
        if args.command == "preflight":
            result = run_validation_checks(root, mode="full")
            print(json.dumps(result, indent=2))
            return 0 if result["status"] == "ok" else 1
        if args.command == "verify":
            return _verify(
                root,
                args.topics,
                args.area,
                receipt_path=args.receipt,
                fail_on_warnings=args.fail_on_warnings,
            )
        if args.command == "catalogue":
            return _print_result(
                run_pipeline(
                    mode="catalogue", area_filter=args.area, topic_filter=args.topics
                )
            )
        if args.command == "atlas":
            return _atlas(root, check=args.check)
        if args.command == "dashboard":
            return _dashboard(root, check=args.check)
        if args.command == "run":
            return _print_result(
                run_pipeline(
                    mode="full",
                    area_filter=args.area,
                    topic_filter=args.topics,
                    workflow=args.workflow,
                )
            )
        if args.command == "topic":
            return _print_result(
                run_single_topic(args.topic_id, mode="full", workflow=args.workflow)
            )
        if args.command == "report":
            return _print_result(run_pipeline(mode="catalogue"))
        if args.command == "status":
            from fep_lean.status import build_status_report, report_to_json

            print(report_to_json(build_status_report(root, args.gnn_root)))
            return 0
        parser.error(f"unsupported command: {args.command}")
        return 2
    finally:
        if args.project_root is not None:
            if previous_project_dir is None:
                os.environ.pop("FEP_LEAN_PROJECT_ROOT", None)
            else:
                os.environ["FEP_LEAN_PROJECT_ROOT"] = previous_project_dir


if __name__ == "__main__":
    raise SystemExit(main())
