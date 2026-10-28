"""Validate historical runner evidence offline; never execute a runner or Lean."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

sys.dont_write_bytecode = True
MANIFEST_SHA256 = "06de871541eaf39c0a032ac5f20f1cf768e21e8bb4ebee8bea47c9e53029df4d"
FEP_COMMIT = "cc2cd1699350530e2bfdec195e8dc9f28a6d4fcb"
GNN_COMMIT = "9a94853e9fceb568dea3b91d11336c4ede6dcf7b"
VERSIONS = {
    "jax": "0.9.2",
    "jaxlib": "0.9.2",
    "numpy": "2.4.4",
    "scipy": "1.17.1",
    "ml_dtypes": "0.5.4",
    "opt_einsum": "3.4.0",
}


def require(condition: object, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def strict(path: Path) -> Any:
    def nonfinite(_: str) -> None:
        raise ValueError("nonfinite JSON constant")

    return json.loads(
        path.read_text(), object_pairs_hook=unique, parse_constant=nonfinite
    )


def member(name: str) -> str:
    path = PurePosixPath(name)
    require(
        bool(name)
        and not path.is_absolute()
        and ".." not in path.parts
        and str(path) == name,
        "unsafe evidence member",
    )
    require(
        "\\" not in name and not any(ord(c) < 32 for c in name),
        "unsafe evidence member characters",
    )
    return name


def validate_manifest(root: Path) -> dict[str, Any]:
    require(
        root.is_dir() and not root.is_symlink(),
        "evidence root must be a real directory",
    )
    require(
        not any(p.is_symlink() for p in root.rglob("*")),
        "retained evidence must not contain symlinks",
    )
    require(
        sha(root / "manifest.json") == MANIFEST_SHA256, "unreviewed evidence manifest"
    )
    manifest = strict(root / "manifest.json")
    require(manifest["schema_version"] == 1, "unknown manifest schema")
    expected = manifest["files_sha256"]
    files = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}
    require(
        files == set(expected) | {"manifest.json"}, "missing or extra evidence member"
    )
    for name, digest in expected.items():
        require(sha(root / member(name)) == digest, "changed evidence member: " + name)
    require(
        manifest["FEP_commit"] == FEP_COMMIT and manifest["GNN_commit"] == GNN_COMMIT,
        "wrong historical pair",
    )
    return manifest


def checker(root: Path) -> dict[str, Any]:
    source = root / "actual/validate_output.py"
    # Only the manifest-authenticated frozen module is loaded. Bytecode writes
    # are disabled above; its __main__ branch is never entered.
    spec = importlib.util.spec_from_file_location("fep61_frozen_checker", source)
    if spec is None or spec.loader is None:
        raise ValueError("checker loader unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return vars(module)


def validate_actual(root: Path, check: dict[str, Any]) -> dict[str, Any]:
    actual = root / "actual"
    protocol = strict(actual / "protocol-v2.json")
    require(
        sha(actual / "protocol-v2.json")
        == (actual / "protocol-v2.sha256").read_text().strip(),
        "protocol seal mismatch",
    )
    require(
        sha(actual / "protocol.json")
        == protocol["prior_protocol_sha256"]
        == (actual / "protocol.sha256").read_text().strip(),
        "predecessor protocol mismatch",
    )
    bindings = {
        "capture.py": "capture_adapter_sha256",
        "validate_output.py": "checker_sha256",
        "candidate/runner.py": "runner_sha256",
        "requirements.txt": "requirements_sha256",
        "checker-controls.json": "checker_controls_sha256",
        "runtime-inventory.json": "runtime_inventory_sha256",
        "runtime_inventory_program.py.txt": "runtime_inventory_program_sha256",
    }
    for name, key in bindings.items():
        require(
            sha(actual / name) == protocol[key],
            "protocol input binding mismatch: " + name,
        )
    require(
        protocol["FEP_candidate_head"] == FEP_COMMIT
        and protocol["GNN_head"] == GNN_COMMIT,
        "actual pair mismatch",
    )
    require(
        {key: len(value) for key, value in protocol["owners"].items()}
        == {"fep_lean": 197, "gnn": 771},
        "source-owner roster mismatch",
    )
    runtime = strict(actual / "runtime-inventory.json")
    require(
        {key: value["version"] for key, value in runtime["packages"].items()}
        == VERSIONS,
        "historical tool version mismatch",
    )
    require(
        runtime["python"].startswith("3.11.17 ") and runtime["machine"] == "arm64",
        "historical runtime identity mismatch",
    )
    require(
        sum(len(value["files"]) for value in runtime["packages"].values()) == 3270,
        "runtime member roster mismatch",
    )
    journal = strict(actual / "execution.json")
    require(
        journal["complete"] is True
        and journal["passed"] is True
        and journal["failure_reason"] is None,
        "historical execution incomplete",
    )
    require(
        journal["protocol_sha256"] == sha(actual / "protocol-v2.json")
        and journal["capture_adapter_sha256"] == protocol["capture_adapter_sha256"],
        "execution protocol mismatch",
    )
    require(
        journal["FEP_candidate_head"] == FEP_COMMIT
        and journal["GNN_head"] == GNN_COMMIT,
        "execution pair mismatch",
    )
    require(
        protocol["invocations"] == len(journal["checks"]) == 2
        and protocol["deadline_seconds_per_invocation"] == 180,
        "execution cardinality/deadline mismatch",
    )
    stable: bytes | None = None
    for index, row in enumerate(journal["checks"], 1):
        home = actual / f"invocation-{index}"
        require(
            row["invocation"] == index
            and row["returncode"] == 0
            and row["source_runtime_before_after_unchanged"] is True,
            "unsuccessful historical invocation",
        )
        require(
            row["command"] == protocol["command"]
            and 0 <= row["elapsed_seconds"] <= 180,
            "invocation command/deadline mismatch",
        )
        for filename, field in [
            ("stdout.txt", "stdout_sha256"),
            ("stderr.txt", "stderr_sha256"),
            ("output/simulation_results.json", "output_sha256"),
        ]:
            require(
                sha(home / filename) == row[field], "captured stream/output mismatch"
            )
        require(
            not (home / "stderr.txt").read_bytes(), "historical invocation has stderr"
        )
        output = strict(home / "output/simulation_results.json")
        require(
            check["validate"](output, jax_version=VERSIONS["jax"]) == row["comparison"],
            "numerical comparison mismatch",
        )
        del output["execution_time_seconds"]
        encoded = json.dumps(output, sort_keys=True, allow_nan=False).encode()
        require(
            hashlib.sha256(encoded).hexdigest() == row["stable_payload_sha256"],
            "stable payload binding mismatch",
        )
        require(
            stable is None or encoded == stable, "historical numerical replay differs"
        )
        stable = encoded
    return protocol


def validate_synthetic(root: Path, protocol: dict[str, Any]) -> None:
    home = root / "synthetic"
    qualification = strict(home / "qualification.json")
    review = strict(root / "reviews/synthetic-postexecution-review.json")
    require(
        review["decision"] == "approve_actual_synthetic_capture_adapter_controls"
        and review["all22_cases_verified"] is True
        and not review["blocking_findings"],
        "synthetic review not approved",
    )
    require(
        sha(home / "qualification.json") == review["qualification_sha256"],
        "synthetic qualification seal mismatch",
    )
    execution = strict(home / "execution-receipt.json")
    require(
        sha(home / "execution-receipt.json") == review["execution_receipt_sha256"]
        and execution["returncode"] == 0,
        "synthetic execution receipt mismatch",
    )
    require(
        execution["supervisor_sha256_before_and_after"]
        == review["actual_supervisor_sha256"]
        == protocol["owners"]["fep_lean"]["src/fep_lean/verification/_subprocess.py"],
        "actual and synthetic supervisors differ",
    )
    require(
        sha(home / "control_harness.py")
        == qualification["script_sha256"]
        == review["reviewed_script_sha256"],
        "synthetic harness binding mismatch",
    )
    require(
        qualification["complete"] is True
        and qualification["passed"] is True
        and len(qualification["checks"]) == 22,
        "synthetic controls incomplete",
    )
    require(
        qualification["adapter_sha256"]
        == protocol["capture_adapter_sha256"]
        == review["adapter_sha256"],
        "synthetic adapter differs from actual adapter",
    )
    for name, digest in review[
        "artifact_hashes_excluding_Git_internals_and_symlink_targets"
    ].items():
        require(
            sha(home / member(name)) == digest, "reviewed synthetic artifact changed"
        )
    reviewed = {row["case"]: row for row in review["cases"]}
    require(
        len(reviewed) == 22
        and {row["case"] for row in qualification["checks"]} == set(reviewed),
        "synthetic case roster mismatch",
    )
    layout = strict(root / "synthetic-layout-observations.json")
    for row in qualification["checks"]:
        case = row["case"]
        record = reviewed[case]
        current = home / member(case)
        require(
            row["passed"] is True
            and record["branch_evidence_independently_verified"] is True,
            "unqualified synthetic case",
        )
        require(
            sha(current / "stdout.bin") == row["stdout_sha256"]
            and sha(current / "stderr.bin") == row["stderr_sha256"],
            "synthetic streams changed",
        )
        stored = current / "fep61-runtime-proposal/execution.json"
        require(
            (strict(stored) if stored.exists() else None) == row["journal"],
            "synthetic journal differs",
        )
        require(
            row["expected_failure_marker"] == record["traceback_marker"],
            "synthetic rejection branch differs",
        )
        if case == "positive":
            require(
                row["returncode"] == 0
                and row["journal"]["complete"] is True
                and row["journal"]["passed"] is True,
                "synthetic positive failed",
            )
        else:
            require(
                row["returncode"] != 0
                and row["expected_failure_marker"]
                in (current / "stderr.bin").read_text(),
                "synthetic refusal lacks intended branch",
            )
        if row["journal"] is None:
            require(
                record["captured_rows"] is None,
                "absent journal/count mismatch: " + case,
            )
        elif case == "preexisting-journal":
            require(
                record["captured_rows"] == 0
                and row["journal"] == {"existing": "preserve"}
                and row["original_journal_preserved"] is True,
                "preexisting journal was not preserved",
            )
        else:
            require(
                len(row["journal"]["checks"]) == record["captured_rows"],
                "synthetic invocation count mismatch: " + case,
            )
        if case == "symlink-output":
            require(
                "fep61-runtime-proposal/invocation-1/output/simulation_results.json"
                in layout[case]["symlink_observations_not_materialized"],
                "missing historical symlink observation",
            )
        if case == "deadline":
            require(
                "Timeout" in row["journal"]["failure_reason"]
                and record["captured_rows"] == 0,
                "deadline refusal not observed",
            )
        if case == "second-output-mismatch":
            require(
                row["journal"]["failure_reason"]
                == "AssertionError: numerical replay changed",
                "wrong replay refusal",
            )


def validate_source_blobs(protocol: dict[str, Any], fep: Path, gnn: Path) -> None:
    for key, commit, repository in [
        ("fep_lean", FEP_COMMIT, fep),
        ("gnn", GNN_COMMIT, gnn),
    ]:
        owners = protocol["owners"][key]
        queries = [commit + ":" + member(name) for name in owners]
        # Regular files avoid duplex-pipe backpressure while Git consumes the
        # complete historical owner batch and emits its captured responses.
        with (
            tempfile.TemporaryFile() as batch_input,
            tempfile.TemporaryFile() as batch_stdout,
            tempfile.TemporaryFile() as batch_stderr,
        ):
            batch_input.write(("\n".join(queries) + "\n").encode())
            batch_input.seek(0)
            try:
                subprocess.run(
                    [
                        "git",
                        "--no-optional-locks",
                        "--no-replace-objects",
                        "-C",
                        str(repository),
                        "cat-file",
                        "--batch",
                    ],
                    env={
                        **os.environ,
                        "GIT_NO_LAZY_FETCH": "1",
                        "GIT_NO_REPLACE_OBJECTS": "1",
                        "GIT_OPTIONAL_LOCKS": "0",
                    },
                    stdin=batch_input,
                    stdout=batch_stdout,
                    stderr=batch_stderr,
                    check=True,
                    timeout=30,
                )
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
                batch_stdout.seek(0)
                batch_stderr.seek(0)
                error.output = batch_stdout.read()
                error.stderr = batch_stderr.read()
                raise
            batch_stdout.seek(0)
            data = batch_stdout.read()
        offset = 0
        for name, digest in owners.items():
            end = data.find(b"\n", offset)
            require(end >= 0, "truncated Git batch header")
            header = data[offset:end].split()
            require(
                len(header) == 3 and header[1] == b"blob",
                "missing historical source blob",
            )
            size = int(header[2])
            offset = end + 1
            require(
                hashlib.sha256(data[offset : offset + size]).hexdigest() == digest,
                "historical owner differs: " + name,
            )
            require(
                data[offset + size : offset + size + 1] == b"\n",
                "truncated Git batch blob",
            )
            offset += size + 1
        require(offset == len(data), "unexpected Git batch output")


def validate(
    root: Path, *, fep_git: Path | None = None, gnn_git: Path | None = None
) -> dict[str, Any]:
    manifest = validate_manifest(root)
    frozen = checker(root)
    protocol = validate_actual(root, frozen)
    validate_synthetic(root, protocol)
    require(
        (fep_git is None) == (gnn_git is None),
        "supply both historical Git repositories or neither",
    )
    if fep_git is not None and gnn_git is not None:
        validate_source_blobs(protocol, fep_git, gnn_git)
    return {
        "status": "passed",
        "historical_FEP_commit": FEP_COMMIT,
        "historical_GNN_commit": GNN_COMMIT,
        "retained_files": len(manifest["files_sha256"]),
        "actual_historical_invocations": 2,
        "synthetic_adapter_controls": 22,
        "historical_source_blobs_checked": fep_git is not None,
        "runner_executed_by_validator": False,
        "native_verified_by_validator": False,
        "OU_prediction_or_dynamics_exercised": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--evidence-root",
        type=Path,
        default=Path(__file__).resolve().parent / "evidence/observations-20261020",
    )
    parser.add_argument("--fep-git", type=Path)
    parser.add_argument("--gnn-git", type=Path)
    args = parser.parse_args()
    try:
        result = validate(
            args.evidence_root, fep_git=args.fep_git, gnn_git=args.gnn_git
        )
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        print(
            json.dumps(
                {"status": "error", "failure_reason": str(error), "details": None}
            )
        )
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
