#!/usr/bin/env python3
"""Read-only checks for the recorded GNN bridge source pin.

The pin at ``specs/gnn-bridge-w2-source-custody/source-pin.json`` records a
descriptive commit reference and owner SHA-256 digests for both sides of the
pair. This script never writes the pin, the emitted documents, or either
repository. It is standard-library only and needs no network access.

Modes:
  --check-shape   validate the pin JSON shape only (cheap, always available).
  --verify PATH   verify a GNN checkout at the recorded commit and confirm every
                  recorded owner digest on both sides. The GNN checkout must be
                  the recorded commit; the FEP owners are read from this
                  working tree because the pin records actual owner bytes.

Exit codes:
  0  valid
  1  invalid shape or owner/commit mismatch
  2  the requested check cannot be completed (missing checkout or git)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

PIN = "specs/gnn-bridge-w2-source-custody/source-pin.json"
HEX40 = set("0123456789abcdef")


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate key in source pin: {key}")
        result[key] = value
    return result


def read_pin(root: Path) -> dict[str, Any]:
    path = root / PIN
    try:
        payload = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"cannot read {PIN}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{PIN} root must be a JSON object")
    return payload


def _is_sha(value: Any, length: int) -> bool:
    return (
        isinstance(value, str)
        and len(value) == length
        and set(value.lower()) <= HEX40
        and value == value.lower()
    )


def _is_relative_path(value: Any) -> bool:
    if not isinstance(value, str) or not value or "\\" in value:
        return False
    path = Path(value)
    return not path.is_absolute() and ".." not in path.parts


def shape_errors(pin: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if pin.get("schema_version") != 1:
        errors.append("unsupported source pin schema")
    for key in ("fep_lean", "gnn"):
        entry = pin.get(key)
        if not isinstance(entry, dict):
            errors.append(f"missing or malformed {key} source binding")
            continue
        if not _is_sha(entry.get("commit"), 40):
            errors.append(f"{key} commit is not a 40-character lowercase hex SHA")
        owners = entry.get("owners")
        if not isinstance(owners, dict) or not owners:
            errors.append(f"{key} owners must be a non-empty object")
            continue
        for name, digest in owners.items():
            if not _is_relative_path(name):
                errors.append(f"{key} owner path is not repository-relative: {name!r}")
            if not _is_sha(digest, 64):
                errors.append(
                    f"{key} owner digest is not a 64-character lowercase hex SHA: {name}"
                )
    if set(pin) != {"schema_version", "fep_lean", "gnn"}:
        errors.append(
            "source pin keys must be exactly schema_version, fep_lean and gnn"
        )
    return errors


def _run_git(args: list[str]) -> str:
    return subprocess.run(
        args,
        check=True,
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
    ).stdout.strip()


def _blob_digest(checkout: Path, commit: str, name: str) -> str | None:
    try:
        blob = subprocess.run(
            ["git", "-C", str(checkout), "cat-file", "-p", f"{commit}:{name}"],
            check=True,
            capture_output=True,
            stdin=subprocess.DEVNULL,
        ).stdout
    except subprocess.CalledProcessError:
        return None
    return hashlib.sha256(blob).hexdigest()


def verify(root: Path, gnn: Path, pin: dict[str, Any]) -> tuple[list[str], str | None]:
    errors = shape_errors(pin)
    if errors:
        return errors, None
    try:
        head = _run_git(["git", "-C", str(gnn), "rev-parse", "HEAD"])
    except (OSError, subprocess.CalledProcessError) as exc:
        return [f"cannot read the GNN checkout HEAD: {exc}"], None
    gnn_commit = pin["gnn"]["commit"]
    if head != gnn_commit:
        errors.append(
            f"GNN checkout HEAD {head} does not equal the recorded pin {gnn_commit}"
        )
    for name, expected in pin["gnn"]["owners"].items():
        actual = _blob_digest(gnn, gnn_commit, name)
        if actual is None:
            errors.append(f"GNN owner is absent at {gnn_commit}: {name}")
        elif actual != expected:
            errors.append(f"GNN owner digest changed: {name}")
    fep_commit = pin["fep_lean"]["commit"]
    try:
        _run_git(["git", "-C", str(root), "cat-file", "-e", f"{fep_commit}^{{commit}}"])
    except (OSError, subprocess.CalledProcessError):
        errors.append(f"FEP commit is not resolvable in this checkout: {fep_commit}")
    for name, expected in pin["fep_lean"]["owners"].items():
        path = root / name
        if not path.is_file():
            errors.append(f"FEP owner is absent: {name}")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            errors.append(f"FEP owner digest changed: {name}")
    return errors, gnn_commit


def _write_github_output(pin: dict[str, Any]) -> None:
    target = os.environ.get("GITHUB_OUTPUT")
    if not target:
        return
    with Path(target).open("a", encoding="utf-8") as handle:
        handle.write(f"gnn_sha={pin['gnn']['commit']}\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check-shape",
        action="store_true",
        help="validate only the pin JSON shape",
    )
    parser.add_argument(
        "--verify",
        type=Path,
        metavar="GNN_CHECKOUT",
        help="verify a GNN checkout at the recorded commit and both owner sets",
    )
    parser.add_argument(
        "--github-output",
        action="store_true",
        help="append the recorded GNN commit to GITHUB_OUTPUT",
    )
    parser.add_argument(
        "--pin-root",
        type=Path,
        default=None,
        help="repository root holding the pin (defaults to this checkout)",
    )
    args = parser.parse_args(argv)
    root = (args.pin_root or Path(__file__).resolve().parents[2]).resolve()

    try:
        pin = read_pin(root)
    except ValueError as exc:
        print(json.dumps({"status": "error", "errors": [str(exc)]}, indent=2))
        return 1

    errors = shape_errors(pin)
    if args.check_shape and not args.verify:
        print(
            json.dumps(
                {
                    "status": "ok" if not errors else "error",
                    "errors": errors,
                    "gnn_commit": pin.get("gnn", {}).get("commit"),
                    "owner_counts": {
                        key: len(pin.get(key, {}).get("owners", {}))
                        for key in ("fep_lean", "gnn")
                    },
                },
                indent=2,
            )
        )
        if errors:
            return 1
        if args.github_output:
            _write_github_output(pin)
        return 0

    if args.verify is None:
        parser.error("one of --check-shape or --verify is required")
    if errors:
        print(json.dumps({"status": "error", "errors": errors}, indent=2))
        return 1
    gnn = args.verify.resolve()
    if not (gnn / ".git").exists():
        print(
            json.dumps(
                {
                    "status": "unavailable",
                    "errors": [
                        f"GNN checkout is missing or not a git repository: {gnn}"
                    ],
                },
                indent=2,
            )
        )
        return 2
    verify_errors, gnn_commit = verify(root, gnn, pin)
    print(
        json.dumps(
            {
                "status": "ok" if not verify_errors else "error",
                "errors": verify_errors,
                "gnn_commit": gnn_commit,
            },
            indent=2,
        )
    )
    return 0 if not verify_errors else 1


if __name__ == "__main__":
    sys.exit(main())
