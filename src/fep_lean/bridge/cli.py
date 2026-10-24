"""Thin argparse adapter for explicit bridge operations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from fep_lean._paths import _emit_failure
from fep_lean.bridge import operations
from fep_lean.bridge.custody import write_json


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "operation",
        choices=(
            "status",
            "pin",
            "emit",
            "certify",
            "verify-certificate",
            "verify-document",
            "audit-semantic",
        ),
    )
    parser.add_argument(
        "--gnn-root",
        type=Path,
        required=True,
        help="explicit GNN checkout; no sibling dependency for normal fep-lean commands",
    )
    parser.add_argument("--model", choices=("finite", "continuous"), default="finite")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument(
        "--check", action="store_true", help="check emitted bytes without writes"
    )
    modes.add_argument(
        "--refresh-digests",
        action="store_true",
        help="rewrite only permitted Signature custody fields",
    )
    parser.add_argument(
        "--results",
        type=Path,
        help="explicit result JSON; audit-semantic accepts a self-contained GNN v2 witness",
    )
    parser.add_argument(
        "--receipt",
        type=Path,
        help="explicit certificate output/input; omitted certify is read-only",
    )
    parser.add_argument(
        "--document",
        type=Path,
        help="emitted GNN document for verify-document (md or lean)",
    )
    parser.add_argument(
        "--fail-on-warnings",
        action="store_true",
        help="verify-document: treat warnings as failures (fail-closed)",
    )


def run(root: Path, args: argparse.Namespace) -> int:
    try:
        if args.operation != "emit" and (args.check or args.refresh_digests):
            raise ValueError("--check and --refresh-digests apply only to emit")
        gnn = args.gnn_root.resolve()
        if args.operation == "status":
            result = operations.status(root, gnn)
        elif args.operation == "pin":
            if args.check or args.refresh_digests:
                raise ValueError("pin is an explicit mutation; use status to check")
            operations.pin_sources(root, gnn)
            result = {
                "status": "ok",
                "pin": operations.PIN,
                "note": "source custody only; existing receipts are not promoted",
            }
        elif args.operation == "emit":
            ok = operations.emit(
                root, gnn, args.model, check=args.check, refresh=args.refresh_digests
            )
            result = {
                "status": "ok" if ok else "error",
                "model": args.model,
                "read_only": args.check,
            }
        elif args.operation == "certify":
            if args.results is None:
                raise ValueError("certify requires --results")
            receipt = operations.certificate_receipt(root, gnn, args.results)
            if args.receipt is not None:
                operations.emit_certificate(args.receipt, receipt)
            result = {
                "status": "ok" if receipt["all_certificates_pass"] else "error",
                "receipt": receipt,
            }
        elif args.operation == "verify-certificate":
            if args.receipt is None:
                raise ValueError("verify-certificate requires --receipt")
            errors = operations.validate_certificate(
                root, gnn, operations.read_object(args.receipt)
            )
            result = {"status": "error" if errors else "ok", "errors": errors}
        elif args.operation == "audit-semantic":
            if args.results is None:
                raise ValueError("audit-semantic requires --results")
            if args.receipt is not None and (
                args.receipt.resolve() == args.results.resolve()
                or (args.receipt.exists() and args.receipt.samefile(args.results))
            ):
                raise ValueError(
                    "audit receipt must not overwrite or alias its input witness"
                )
            receipt = operations.semantic_witness_audit(root, gnn, args.results)
            if args.receipt is not None:
                write_json(args.receipt, receipt)
            result = {
                "status": "ok" if receipt["status"] == "passed" else "error",
                "receipt": receipt,
            }
        else:
            if args.document is None:
                raise ValueError("verify-document requires --document")
            receipt = operations.verify_document(
                root,
                gnn,
                args.document,
                model=args.model,
                receipt=args.receipt,
                fail_on_warnings=args.fail_on_warnings,
            )
            result = {"status": receipt["status"], "receipt": receipt}
        if result["status"] != "ok":
            return _emit_failure("bridge operation refused", result=result)
        print(json.dumps(result, indent=2, allow_nan=False))
        return 0 if result["status"] == "ok" else 1
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        RecursionError,
        OverflowError,
    ) as exc:
        return _emit_failure(str(exc))
