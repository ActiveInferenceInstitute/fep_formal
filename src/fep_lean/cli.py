"""Single canonical command-line interface for fep_lean."""

from __future__ import annotations

import argparse
import json
import logging
import os
from collections.abc import Callable, Sequence
from contextlib import nullcontext
from pathlib import Path
from typing import Any

from fep_lean._paths import (
    explicit_project_root,
    project_root,
    project_root_context,
    project_root_errors,
)
from fep_lean.bridge import operations
from fep_lean.catalogue.generation import (
    check_or_write,
)
from fep_lean.catalogue.topics import FEPTopicCatalogue
from fep_lean.output import release_bundle
from fep_lean.output.evidence import (
    NATIVE_RECEIPT,
    RENDER_RECEIPT,
    STATUS_BOUNDARY,
    PublicationReadinessReport,
    SectionReport,
    StatusReport,
    bridge_pin_section,
    build_status_report,
    catalogue_products_section,
    native_receipt_section,
    render_receipt_section,
    report_to_json,
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
from fep_lean.verification.environment import run_validation_checks
from fep_lean.verification.environment import setup_workspace as _setup
from fep_lean.verification.lean_verifier import LeanVerifier, verify_catalogue

__all__ = [
    "NATIVE_RECEIPT",
    "RENDER_RECEIPT",
    "SOURCE_PIN",
    "FEPTopicCatalogue",
    "LeanVerifier",
    "PublicationReadinessReport",
    "SectionReport",
    "StatusReport",
    "bridge_pin_section",
    "build_parser",
    "build_status_report",
    "catalogue_products_section",
    "main",
    "native_receipt_section",
    "render_receipt_section",
    "report_to_json",
]


def _configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def _print_result(result: object) -> int:
    payload = result.as_dict() if hasattr(result, "as_dict") else result
    print(json.dumps(payload, indent=2, default=str))
    return 0 if getattr(result, "complete", False) else 1


def _emit_failure(reason: str, *, indent: int | None = None, **extra: object) -> int:
    """Print the canonical error JSON and return exit status 1.

    Key order is ``status``, then *extra* in call order, then
    ``failure_reason``; every verb's failure path goes through here so the
    schema cannot drift between verbs.
    """
    payload = {"status": "error", **extra, "failure_reason": reason}
    print(json.dumps(payload, indent=indent))
    return 1


def _display(root: Path, path: Path) -> str:
    """Render *path* for display, relative to *root* when possible."""
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _atlas(root: Path, *, check: bool) -> int:
    """Write or fail-closed drift-check the formalism atlas projection."""
    return check_or_write(
        root,
        atlas_projection_drift,
        write_formalism_atlas,
        "formalism atlas projections are current",
        check=check,
    )


def _dashboard(root: Path, *, check: bool) -> int:
    """Write or fail-closed drift-check the formal-kernel dashboard."""
    return check_or_write(
        root,
        formal_kernel_dashboard_drift,
        write_formal_kernel_dashboard,
        "formal-kernel dashboard projections are current",
        check=check,
    )


def _verify(
    root: Path,
    topic_ids: list[str] | None,
    area: str | None,
    *,
    receipt_path: Path | None = None,
    fail_on_warnings: bool = False,
) -> int:
    outcome = verify_catalogue(
        root,
        topic_ids,
        area,
        receipt_path=receipt_path,
        fail_on_warnings=fail_on_warnings,
    )
    print(outcome.to_json())
    return outcome.exit_code


SOURCE_PIN = Path(operations.PIN)


# Legacy CLI imports remain the exact same type objects, now owned by evidence.
_STATUS_BOUNDARY = STATUS_BOUNDARY


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
    methods = sub.add_parser(
        "methods", help="portable offline mathematical positioning and visual analysis"
    )
    methods_sub = methods.add_subparsers(dest="methods_operation", required=True)
    inspect = methods_sub.add_parser(
        "inspect", help="read exact topic or authored family contracts"
    )
    selection = inspect.add_mutually_exclusive_group()
    selection.add_argument("--topic")
    selection.add_argument("--family")
    neighbors = methods_sub.add_parser(
        "neighbors", help="read editorial incidence comparison candidates"
    )
    neighbors.add_argument("family")
    neighbors.add_argument("--limit", type=int, default=3)
    probe = methods_sub.add_parser(
        "probe", help="evaluate deterministic non-proof boundary probes"
    )
    probe.add_argument("name", nargs="?")
    gibbs = methods_sub.add_parser(
        "gibbs", help="evaluate finite Gibbs duality with numerical support diagnostics"
    )
    gibbs.add_argument(
        "--candidate", required=True, help="candidate law as a JSON array"
    )
    gibbs.add_argument(
        "--reference", required=True, help="reference law as a JSON array"
    )
    gibbs.add_argument(
        "--potential", required=True, help="finite potential as a JSON array"
    )
    analysis = methods_sub.add_parser(
        "analyze", help="read source-grounded Lean statement and maintained prose"
    )
    analysis.add_argument("topic")
    theorem = methods_sub.add_parser(
        "theorem", help="inspect one exact qualified Lean declaration contract"
    )
    theorem.add_argument("qualified_name")
    methods_sub.add_parser(
        "embedding", help="inspect interpretable FEP/OpenAI corpus coordinates"
    )
    for operation in ("export", "check"):
        export = methods_sub.add_parser(
            operation,
            help="write visual methods artifacts"
            if operation == "export"
            else "read-only artifact and resource freshness check",
        )
        export.add_argument(
            "--output-root", type=Path, default=Path("output/mathematical-methods")
        )
    from fep_lean.bridge.cli import add_arguments

    add_arguments(sub.add_parser("bridge", help="source-bound GNN bridge operations"))

    from fep_lean.custody.cli import add_arguments

    add_arguments(
        sub.add_parser("custody", help="H2.7 evidence-custody census and apply")
    )
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
    capture = sub.add_parser(
        "publication-capture",
        help="explicit bounded local publication evidence capture and resume",
    )
    capture.add_argument("--template", type=Path, required=True)
    capture.add_argument("--journal", type=Path)
    capture.add_argument(
        "--plan",
        action="store_true",
        help="print the fixed stage policy without running tools",
    )
    capture.add_argument(
        "--resume",
        action="store_true",
        help="revalidate and resume an existing journal",
    )
    capture.add_argument("--source-date-epoch", type=int, default=0)
    capture.add_argument("--timeout", type=float, default=21600)
    return parser


def _methods(args: argparse.Namespace, root: Path | None) -> int:
    """Portable methods branch; no checkout is required for installed resources."""
    from fep_lean import __version__
    from fep_lean.methods import (
        analyze_topic,
        build_mathematical_positioning,
        cross_corpus_embedding,
        evaluate_boundary_probes,
        export_mathematical_positioning,
        gibbs_duality_diagnostics,
        inspect_family,
        inspect_theorem,
        inspect_topic,
        mathematical_positioning_drift,
        package_resource_drift,
        positioning_neighbors,
    )

    try:
        if args.methods_operation == "gibbs":
            diagnostic = gibbs_duality_diagnostics(
                json.loads(args.candidate),
                json.loads(args.reference),
                json.loads(args.potential),
            )
            print(
                json.dumps(
                    {
                        "status": "ok",
                        "package_version": __version__,
                        "source_origin": "numerical-input",
                        "evidence_boundary": diagnostic["evidence_boundary"],
                        "result": diagnostic,
                    },
                    indent=2,
                    allow_nan=False,
                )
            )
            return 0
        if root is not None and args.methods_operation == "check":
            resources = package_resource_drift(root)
            if resources:
                raise ValueError(
                    "generated methods resource drift: "
                    + ", ".join(_display(root, path) for path in resources)
                )
        model = build_mathematical_positioning(root)
        data = model.as_dict()
        payload: Any
        if args.methods_operation == "inspect":
            payload = (
                inspect_topic(model, args.topic)
                if args.topic
                else inspect_family(model, args.family)
                if args.family
                else data["counts"]
            )
        elif args.methods_operation == "neighbors":
            payload = positioning_neighbors(model, args.family, args.limit)
        elif args.methods_operation == "analyze":
            payload = analyze_topic(model, args.topic)
        elif args.methods_operation == "theorem":
            payload = inspect_theorem(model, args.qualified_name)
        elif args.methods_operation == "embedding":
            payload = cross_corpus_embedding(model)
        elif args.methods_operation == "probe":
            probes = evaluate_boundary_probes()
            payload = [
                probe
                for probe in probes
                if args.name is None or probe["id"] == args.name
            ]
            if not payload:
                raise ValueError(f"unknown numerical probe: {args.name}")
        elif args.methods_operation == "export":
            payload = {
                "artifacts": [
                    str(path)
                    for path in export_mathematical_positioning(model, args.output_root)
                ]
            }
        else:
            drift = mathematical_positioning_drift(model, args.output_root)
            if drift:
                raise ValueError(
                    "methods artifact drift: " + ", ".join(str(path) for path in drift)
                )
            payload = {"fresh": True}
        print(
            json.dumps(
                {
                    "status": "ok",
                    "package_version": data["package_version"],
                    "source_origin": model.origin.value,
                    "evidence_boundary": data["evidence_boundary"],
                    "result": payload,
                },
                indent=2,
                allow_nan=False,
            )
        )
        return 0
    except (OSError, ValueError) as exc:
        return _emit_failure(str(exc))


def _preflight(root: Path) -> int:
    result = run_validation_checks(root, mode="full")
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "ok" else 1


def _status(root: Path, gnn_root: Path | None) -> int:
    print(report_to_json(build_status_report(root, gnn_root)))
    return 0


def _publication_capture(
    args: argparse.Namespace, root: Path, parser: argparse.ArgumentParser
) -> int:
    if args.plan and args.resume:
        parser.error("--plan and --resume are mutually exclusive")
    if not args.plan and args.journal is None:
        parser.error("publication-capture requires --journal unless --plan is used")
    try:
        plan = release_bundle.plan_publication_capture(
            root,
            template_root=args.template,
            source_date_epoch=args.source_date_epoch,
            timeout_s=args.timeout,
        )
        if args.plan:
            print(json.dumps(plan.record(), indent=2))
            return 0
        capture_result = release_bundle.run_publication_capture(
            plan, args.journal, resume=args.resume
        )
    except (OSError, release_bundle.ReleaseBundleError) as exc:
        return _emit_failure(str(exc), complete=False)
    print(json.dumps(capture_result.as_dict(), indent=2))
    return 0 if capture_result.complete else 1


def _dispatch_command(
    args: argparse.Namespace, root: Path, parser: argparse.ArgumentParser
) -> int:
    from fep_lean.bridge.cli import run as run_bridge
    from fep_lean.custody.cli import run as run_custody

    handlers: dict[str, Callable[[], int]] = {
        "setup": lambda: _setup(root),
        "bridge": lambda: run_bridge(root, args),
        "custody": lambda: run_custody(root, args),
        "verify": lambda: _verify(
            root,
            args.topics,
            args.area,
            receipt_path=args.receipt,
            fail_on_warnings=args.fail_on_warnings,
        ),
        "catalogue": lambda: _print_result(
            run_pipeline(
                mode="catalogue", area_filter=args.area, topic_filter=args.topics
            )
        ),
        "atlas": lambda: _atlas(root, check=args.check),
        "dashboard": lambda: _dashboard(root, check=args.check),
        "run": lambda: _print_result(
            run_pipeline(
                mode="full",
                area_filter=args.area,
                topic_filter=args.topics,
                workflow=args.workflow,
            )
        ),
        "topic": lambda: _print_result(
            run_single_topic(args.topic_id, mode="full", workflow=args.workflow)
        ),
        "report": lambda: _print_result(run_pipeline(mode="catalogue")),
        "preflight": lambda: _preflight(root),
        "status": lambda: _status(root, args.gnn_root),
        "publication-capture": lambda: _publication_capture(args, root, parser),
    }
    handler = handlers.get(args.command)
    if handler is None:
        parser.error(f"unsupported command: {args.command}")
        return 2
    return handler()


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    _configure_logging(args.verbose or os.environ.get("FEP_LEAN_VERIFY_VERBOSE") == "1")
    with (
        project_root_context(args.project_root)
        if args.project_root is not None
        else nullcontext()
    ):
        root = project_root()
        explicit_root = explicit_project_root()
        if args.command == "methods":
            selected = (
                root
                if args.project_root is not None
                or explicit_root
                or (not project_root_errors(root))
                else None
            )
            return _methods(args, selected)
        missing = project_root_errors(root)
        if missing:
            return _emit_failure(
                "substantive fep-lean commands require a source checkout; pass --project-root /path/to/fep_lean. Missing: "
                + ", ".join(missing),
                indent=2,
                complete=False,
                project_root=str(root),
            )
        return _dispatch_command(args, root, parser)


if __name__ == "__main__":
    raise SystemExit(main())
