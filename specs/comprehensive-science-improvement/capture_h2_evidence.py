"""Capture the complete current H2 mandatory test roster and real outcomes.

This preparation tool never changes an acceptance receipt, frozen roster pin,
review or diagnostics. Its new output directory retains failures as evidence.
The coordinator must independently review and seal any successful capture.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pytest

from fep_formal.verification._subprocess import run_process_group
from fep_formal.verification.horizon_acceptance import (
    MANDATORY_TEST_FILES,
    native_source_paths,
    source_snapshot,
    validate_test_evidence,
)


def write_new(path: Path, payload: Any) -> None:
    data = (
        json.dumps(payload, sort_keys=True, indent=2, allow_nan=False) + "\n"
    ).encode()
    with path.open("xb") as stream:
        stream.write(data)


class CollectionCapture:
    def __init__(self, destination: Path):
        self.destination = destination

    def pytest_configure(self, config: pytest.Config) -> None:
        if config.option.keyword or config.option.markexpr:
            raise pytest.UsageError("H2 capture forbids keyword and marker filters")

    @pytest.hookimpl(trylast=True)
    def pytest_collection_finish(self, session: pytest.Session) -> None:
        write_new(
            self.destination,
            {
                "schema_version": 1,
                "nodeids": [item.nodeid for item in session.items],
                "markers": {
                    item.nodeid: sorted(marker.name for marker in item.iter_markers())
                    for item in session.items
                },
            },
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=3600)
    parser.add_argument("--child", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--collect", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if sys.implementation.name != "cpython" or sys.version_info[:2] != (3, 14):
        parser.error("H2 evidence capture requires CPython 3.14")
    root = Path(__file__).resolve().parents[2]
    output = args.output.resolve()
    if args.child:
        if (
            os.environ.get("PYTEST_DISABLE_PLUGIN_AUTOLOAD") != "1"
            or os.environ.get("PYTEST_ADDOPTS")
            or os.environ.get("PYTEST_PLUGINS")
        ):
            parser.error("child requires the sealed pytest environment policy")
        return int(
            pytest.main(
                [
                    *MANDATORY_TEST_FILES,
                    "-q",
                    "-p",
                    "pytest_timeout",
                    "-o",
                    "addopts=",
                    *(
                        ["--collect-only"]
                        if args.collect
                        else [f"--junitxml={output / 'junit.xml'}"]
                    ),
                ],
                plugins=[
                    CollectionCapture(
                        output
                        / ("collection.json" if args.collect else "run-collection.json")
                    )
                ],
            )
        )
    if not 0 < args.timeout <= 7200:
        parser.error("timeout must be positive and at most 7200 seconds")
    output.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ)
    for name in ("PYTEST_ADDOPTS", "PYTEST_PLUGINS", "PYTEST_CURRENT_TEST"):
        env.pop(name, None)
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    env["FEP_HEAVY_LEAN_PROBES"] = "1"
    env.pop("FEP_LEAN_LIVE_TESTS", None)
    env["FEP_FORMAL_LIVE_TESTS"] = "0"
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--child",
        "--output",
        str(output),
    ]
    result: dict[str, Any] = {
        "schema_version": 1,
        "scope": "complete current MANDATORY_TEST_FILES; no -k or marker filter",
        "command": command,
        "environment": {"FEP_HEAVY_LEAN_PROBES": "1"},
        "pytest_policy": {
            "autoload": False,
            "explicit_plugins": ["pytest_timeout", "CollectionCapture"],
            "selection_environment_cleared": [
                "PYTEST_ADDOPTS",
                "PYTEST_PLUGINS",
                "PYTEST_CURRENT_TEST",
            ],
            "live_provider_tests": False,
            "collection_frozen_before_run": True,
        },
        "timeout_seconds": args.timeout,
        "python": sys.version,
        "accepted": False,
    }
    before = None
    paths: tuple[str, ...] = ()
    deadline = time.monotonic() + args.timeout
    stage = "source-before"
    try:
        paths = native_source_paths(root)
        before = source_snapshot(root, list(paths))
        write_new(output / "source-before.json", before)
        for stage, argv in (
            ("collection", [*command, "--collect"]),
            ("pytest", command),
        ):
            completed = run_process_group(
                argv, cwd=root, env=env, timeout=max(0.001, deadline - time.monotonic())
            )
            (output / f"{stage}-stdout.log").write_text(completed.stdout)
            (output / f"{stage}-stderr.log").write_text(completed.stderr)
            result[f"{stage}_exit_code"] = completed.returncode
            if completed.returncode != 0:
                break
            if stage == "collection":
                result["frozen_collection_sha256"] = hashlib.sha256(
                    (output / "collection.json").read_bytes()
                ).hexdigest()
        stage = "source-after"
        after = source_snapshot(root, list(paths))
        write_new(output / "source-after.json", after)
        result["source_unchanged"] = before == after
        if result.get("pytest_exit_code") == 0 and before == after:
            stage = "validate"
            collection = (output / "collection.json").read_bytes()
            result["collection_unchanged"] = (
                collection == (output / "run-collection.json").read_bytes()
            )
            if not result["collection_unchanged"]:
                raise ValueError(
                    "execution collection differs from pre-run frozen roster"
                )
            nodes = validate_test_evidence(
                root, json.loads(collection), (output / "junit.xml").read_bytes()
            )
            result["mandatory_node_count"] = len(nodes)
            result["accepted"] = True
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        RecursionError,
        subprocess.TimeoutExpired,
    ) as exc:
        result["capture_error"] = {
            "stage": stage,
            "type": type(exc).__name__,
            "message": str(exc),
        }
        if isinstance(exc, subprocess.TimeoutExpired):
            for suffix, partial in (
                ("stdout.log", exc.stdout),
                ("stderr.log", exc.stderr),
            ):
                data = partial or b""
                (output / f"{stage}-{suffix}").write_bytes(
                    data.encode("utf-8") if isinstance(data, str) else data
                )
    finally:
        if before is not None and not (output / "source-after.json").exists():
            try:
                after = source_snapshot(root, list(paths))
                write_new(output / "source-after.json", after)
                result["source_unchanged"] = before == after
            except (OSError, ValueError, TypeError) as exc:
                result["source_after_error"] = str(exc)
        artifacts = {}
        for path in sorted(output.iterdir()):
            if path.is_file():
                try:
                    artifacts[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
                except OSError as exc:
                    result["accepted"] = False
                    result.setdefault("artifact_errors", {})[path.name] = str(exc)
        result["artifacts"] = artifacts
        write_new(output / "capture.json", result)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
