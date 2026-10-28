"""Retain a bounded, source-bound native H3 parameter export; no study draws."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, cast

from run_synthetic import (
    BASE,
    NATIVE_EXPORT_FOUNDATION,
    PROTOCOL_SHA256,
    STUDY_SOURCE_FILES,
    AttemptFiles,
    Inputs,
    StudyRejection,
    frozen_protocol,
    native_probe,
    parameters,
    parse_native_output,
    replay_native_attempt,
    require,
)

from fep_formal.lean_source import lean_code_without_comments
from fep_formal.output.provenance import (
    config_owner_paths,
    report_owner_errors,
    source_owner_paths,
)
from fep_formal.verification._subprocess import run_process_group
from fep_formal.verification._toolchain import (
    find_executable,
    lean_version_matches_pin,
    read_toolchain_pin,
    resolved_mathlib_revision,
    subprocess_env,
)

FOUNDATION = NATIVE_EXPORT_FOUNDATION


def export_native(root: Path, output: Path, timeout: float) -> dict[str, Any]:
    """Build current imports, compile retained canonical text and seal all evidence."""
    require(os.name == "posix", "native export requires POSIX descriptor custody")
    require(sys.version_info[:2] == (3, 14), "native export requires Python 3.14")
    require(
        math.isfinite(timeout) and timeout > 0, "positive finite export budget required"
    )
    inputs = Inputs(root)
    root = inputs.root
    require(output.is_absolute(), "absolute native attempt path required")
    require(".." not in output.parts, "noncanonical native attempt path")
    require(output.is_relative_to(root), "native attempt must remain inside project")
    relative = output.relative_to(root).as_posix()
    require(
        Path(__file__).resolve() == root / BASE / "export_native.py",
        "export producer does not belong to declared project",
    )
    protocol = frozen_protocol(inputs)
    owner_errors = report_owner_errors(root)
    require(
        not owner_errors, "current owner/projection errors: " + "; ".join(owner_errors)
    )
    names = sorted(
        {
            path.relative_to(root).as_posix()
            for path in (*source_owner_paths(root), *config_owner_paths(root))
        }
        | set(STUDY_SOURCE_FILES)
    )
    for name in names:
        inputs.read(name)
    before = {name: inputs.states[name].sha256 for name in names}
    source = inputs.states[FOUNDATION].bytes.decode()
    require(
        not re.search(
            r"\b(?:sorry|admit|axiom|opaque)\b|unsafe\s+",
            lean_code_without_comments(source),
        ),
        "native foundation has a placeholder or unsafe declaration",
    )
    probe = native_probe(source)
    files = AttemptFiles(output, create=True)
    start = time.monotonic()
    deadline = start + timeout
    stages: list[dict[str, Any]] = []
    record: dict[str, Any] = {
        "schema_version": 1,
        "kind": "h3-native-export-attempt",
        "protocol_sha256": PROTOCOL_SHA256,
        "captured_project_root": str(root),
        "accepted": False,
        "capture_budget_seconds": timeout,
        "source_before": before,
        "stages": stages,
        "boundary": "Native parameter/equality evidence only; complete composition audit, independent proof reviews and synthetic execution remain separate.",
    }
    expected_files: dict[str, str] = {}

    def retain(name: str, raw: bytes) -> None:
        files.write_new(name, raw)
        expected_files[name] = hashlib.sha256(raw).hexdigest()

    def stage(name: str, command: list[str]) -> subprocess.CompletedProcess[str]:
        environment = subprocess_env(root / "lean")
        remaining = deadline - time.monotonic()
        require(remaining > 0, "native export deadline expired")
        started = time.monotonic()
        item: dict[str, Any] = {
            "name": name,
            "command": command,
            "budget_seconds": remaining,
        }
        stages.append(item)
        try:
            result = run_process_group(
                command,
                cwd=root / "lean",
                env=environment,
                timeout=remaining,
            )
        except subprocess.TimeoutExpired as error:
            item["timed_out"] = True
            for suffix, raw in (("stdout", error.output), ("stderr", error.stderr)):
                if raw is not None:
                    retain(
                        f"{name}.{suffix}",
                        raw if isinstance(raw, bytes) else raw.encode(),
                    )
            raise
        else:
            item["returncode"] = result.returncode
            retain(f"{name}.stdout", result.stdout.encode())
            retain(f"{name}.stderr", result.stderr.encode())
            return result
        finally:
            inputs.stable()
            item["duration_seconds"] = time.monotonic() - started

    try:
        lake = find_executable("lake", root / "lean")
        require(lake is not None, "pinned Lake unavailable")
        lake = cast(str, lake)
        version = stage("compiler-version", [lake, "env", "lean", "--version"])
        require(version.returncode == 0, "compiler version process failed")
        pin = read_toolchain_pin(root / "lean")
        require(
            pin is not None and lean_version_matches_pin(version.stdout, pin),
            "actual compiler differs from pin",
        )
        revision = resolved_mathlib_revision(root / "lean")
        require(bool(revision), "Mathlib manifest revision unavailable")
        head = stage(
            "mathlib-head",
            [
                "git",
                "-C",
                str(root / "lean/.lake/packages/mathlib"),
                "rev-parse",
                "HEAD",
            ],
        )
        require(
            head.returncode == 0 and head.stdout.strip() == revision,
            "actual Mathlib checkout differs from pin",
        )
        build = stage(
            "native-build",
            [
                lake,
                "build",
                "FepSketches.h3_reference_model",
                "FepSketches.compositions.h3_case_study",
            ],
        )
        require(build.returncode == 0, "current native targets failed")
        require(
            not re.search(
                r"\b(?:warning|error):|\bsorryAx\b",
                build.stdout + build.stderr,
                re.IGNORECASE,
            ),
            "current native build warned or failed",
        )
        retain("H3NativeExport.lean", probe.encode())
        inputs.read(
            relative + "/H3NativeExport.lean",
            expected=expected_files["H3NativeExport.lean"],
        )
        compiler = stage(
            "native-export",
            [
                lake,
                "env",
                "lean",
                "--threads=1",
                "-R",
                str(output),
                str(output / "H3NativeExport.lean"),
            ],
        )
        value = parse_native_output(
            compiler.stdout, compiler.stderr, compiler.returncode
        )
        parameters(value, protocol)
        final_head = stage(
            "mathlib-head-final",
            [
                "git",
                "-C",
                str(root / "lean/.lake/packages/mathlib"),
                "rev-parse",
                "HEAD",
            ],
        )
        require(
            final_head.returncode == 0 and final_head.stdout.strip() == revision,
            "actual Mathlib revision changed during native export",
        )
        final_version = stage(
            "compiler-version-final", [lake, "env", "lean", "--version"]
        )
        require(
            final_version.returncode == 0 and final_version.stdout == version.stdout,
            "actual compiler identity changed during native export",
        )
        inputs.stable()
        artifacts = {
            relative + "/" + name: digest
            for name, digest in sorted(expected_files.items())
        }
        exported = {
            "schema_version": 1,
            "kind": "h3-native-rational-export",
            "protocol_sha256": PROTOCOL_SHA256,
            "captured_project_root": str(root),
            "returncode": compiler.returncode,
            "warnings": [],
            "lean_version": version.stdout.strip(),
            "mathlib_revision": revision,
            "source_before": before,
            "source_after": {name: inputs.states[name].sha256 for name in names},
            "parameters": value,
            "native_acceptance": relative + "/acceptance.json",
            "native_artifacts": artifacts,
        }
        retain(
            "export.json",
            (
                json.dumps(exported, indent=2, sort_keys=True, allow_nan=False) + "\n"
            ).encode(),
        )
        retained, issues = files.inventory(strict=False)
        require(
            not issues and retained == expected_files, "native export artifacts changed"
        )
        inputs.stable()
        record["duration_seconds"] = time.monotonic() - start
        # Replay the same substantive evidence gates the numerical consumer
        # enforces, rather than trusting this producer's metadata flags.
        for name, digest in artifacts.items():
            inputs.read(name, expected=digest)
        replay_native_attempt(inputs, relative + "/export.json", exported, record)
        require(time.monotonic() < deadline, "native export capture deadline expired")
        record["accepted"] = True
    except BaseException as error:
        record["failure"] = {"type": type(error).__name__, "reason": str(error)}
        raise
    finally:
        record["source_after"] = {name: inputs.states[name].sha256 for name in names}
        record["input_sha256"] = inputs.hashes()
        retained, issues = files.inventory(strict=False)
        record["artifact_sha256"] = {
            relative + "/" + name: digest for name, digest in sorted(retained.items())
        }
        record["retained_output_issues"] = issues
        record["duration_seconds"] = time.monotonic() - start
        if record["accepted"] and (issues or retained != expected_files):
            record["accepted"] = False
            record["failure"] = {
                "type": "StudyRejection",
                "reason": "native artifacts changed during final seal",
            }
        if record["accepted"] and time.monotonic() >= deadline:
            record["accepted"] = False
            record["failure"] = {
                "type": "StudyRejection",
                "reason": "native export capture deadline expired",
            }
        try:
            files.receipt(
                (
                    json.dumps(record, indent=2, sort_keys=True, allow_nan=False) + "\n"
                ).encode()
            )
            if record["accepted"] and time.monotonic() >= deadline:
                record["accepted"] = False
                record["duration_seconds"] = time.monotonic() - start
                record["failure"] = {
                    "type": "StudyRejection",
                    "reason": "native export deadline expired during seal",
                }
                files.receipt(
                    (
                        json.dumps(record, indent=2, sort_keys=True, allow_nan=False)
                        + "\n"
                    ).encode()
                )
        finally:
            files.close()
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-root", type=Path, default=Path(__file__).resolve().parents[2]
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=1800.0)
    args = parser.parse_args()
    try:
        record = export_native(args.project_root, args.output, args.timeout)
    except (StudyRejection, subprocess.TimeoutExpired, OSError, ValueError) as error:
        print(json.dumps({"accepted": False, "error": str(error)}))
        return 1
    print(json.dumps({"accepted": record["accepted"], "attempt": str(args.output)}))
    return 0 if record["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
