"""Independent comparison of two actual strict native executions in one CI job."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from fep_lean.output import validate_native_lean_receipt


def compare_native_catalogue_receipts(
    root: Path, producer: Path, cli: Path, *, run_id: str, attempt: str, commit: str
) -> dict[str, Any]:
    """Compare all receipt fields except measured compiler durations."""
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("exact commit required")
    if any(not re.fullmatch(r"[1-9][0-9]*", value) for value in (run_id, attempt)):
        raise ValueError("actual workflow run and attempt required")
    if (
        subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True
        ).strip()
        != commit
    ):
        raise ValueError("workflow commit differs from actual checkout")
    if producer.resolve() == cli.resolve():
        raise ValueError("distinct receipt identities required")
    payloads = []
    hashes = []
    validations = []
    for path in (producer, cli):
        if path.is_symlink() or not path.is_file():
            raise ValueError("regular native receipt required")
        raw = path.read_bytes()
        with tempfile.TemporaryDirectory(prefix="fep-native-shadow-") as directory:
            snapshot = Path(directory) / "native.json"
            snapshot.write_bytes(raw)
            validation = validate_native_lean_receipt(snapshot, project_root=root)
        if path.is_symlink() or path.read_bytes() != raw:
            raise ValueError("receipt changed during comparison")
        if not all(
            validation.get(k) is True
            for k in ("valid", "source_bound", "native_claim_ready")
        ):
            raise ValueError("both actual executions must independently qualify")
        payloads.append(json.loads(raw))
        hashes.append(hashlib.sha256(raw).hexdigest())
        validations.append(validation)

    def semantic(payload: dict[str, Any]) -> dict[str, Any]:
        return {
            key: (
                [{k: v for k, v in row.items() if k != "duration_s"} for row in value]
                if key == "results"
                else value
            )
            for key, value in payload.items()
            if key != "duration_s"
        }

    if semantic(payloads[0]) != semantic(payloads[1]):
        raise ValueError("strict native outcomes/source/toolchain differ")
    return {
        "schema_version": 1,
        "head": commit,
        "run_id": run_id,
        "attempt": attempt,
        "passed": True,
        "receipt_sha256": hashes,
        "validation": validations,
        "producer_duration_s": payloads[0]["duration_s"],
        "cli_duration_s": payloads[1]["duration_s"],
        "topic_ids": payloads[0]["requested_topic_ids"],
        "boundary": "Two actual strict executions compared. Durations may differ; no gate removed and no steady-state speedup established.",
    }
