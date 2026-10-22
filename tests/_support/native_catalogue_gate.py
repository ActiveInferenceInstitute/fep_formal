"""One explicit strict producer inside the existing serial catalogue test.

The CI job executes this node once and archives its JUnit and ordinary native
receipt. Build caches never select a receipt. This helper adds no public API.
"""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any

from fep_lean.catalogue.topics import FEPTopicCatalogue
from fep_lean.output.evidence import _source_snapshot, validate_native_lean_receipt
from fep_lean.verification.lean_verifier import verify_catalogue

CI_NATIVE_RECEIPT_ENV = "FEP_LEAN_CI_NATIVE_RECEIPT"


def produce_native_catalogue_receipt(root: Path, flag: str) -> dict[str, Any]:
    """Execute one unfiltered strict producer; refusal never falls back or skips."""
    if flag != "1":
        raise ValueError("explicit CI native receipt flag must equal 1")
    root = root.resolve(strict=True)
    output = root / "output"
    if output.is_symlink():
        raise ValueError("native producer output directory must not be a symlink")
    output.mkdir(exist_ok=True)
    receipt = output / "native-verification.json"
    intent = output / "native-catalogue-producer.intent.json"
    invocation = output / "native-catalogue-producer.json"
    for path in (receipt, intent, invocation):
        if path.exists() or path.is_symlink():
            raise FileExistsError("native producer requires fresh output: " + path.name)
    # Exclusive creation prevents simultaneous or failed-then-repeated producers.
    # The serial job owns this checkout; no historical receipt is ever selected.
    with intent.open("x") as stream:
        stream.write(
            json.dumps(
                {
                    "state": "claimed",
                    "operation": "verify_catalogue",
                    "topic_ids": None,
                    "area": None,
                    "fail_on_warnings": True,
                }
            )
            + "\n"
        )
    before = _source_snapshot(root)
    result = verify_catalogue(
        root, None, None, receipt_path=receipt, fail_on_warnings=True
    )
    with invocation.open("x") as stream:
        stream.write(result.to_json() + "\n")
    if result.exit_code != 0:
        raise RuntimeError(
            "strict native catalogue producer failed; actual output retained"
        )
    if _source_snapshot(root) != before:
        raise RuntimeError("native catalogue source changed during execution")
    if receipt.is_symlink() or not receipt.is_file():
        raise ValueError("native producer receipt must be a regular file")
    raw = receipt.read_bytes()
    # The validator consumes the exact captured bytes, independent of later
    # pathname replacement. Source validation still targets the live checkout.
    with tempfile.TemporaryDirectory(
        prefix="fep-native-receipt-snapshot-"
    ) as directory:
        snapshot = Path(directory) / "native-verification.json"
        snapshot.write_bytes(raw)
        validation = validate_native_lean_receipt(snapshot, project_root=root)
    if receipt.is_symlink() or receipt.read_bytes() != raw:
        raise RuntimeError("native receipt changed during independent validation")
    if not all(
        validation.get(key) is True
        for key in ("valid", "source_bound", "native_claim_ready")
    ):
        raise RuntimeError("strict native receipt is not independently claim-ready")
    payload = json.loads(raw)
    expected = list(
        FEPTopicCatalogue.from_yaml(root / "config/topics.yaml").roster.topic_ids
    )
    if (
        payload["requested_topic_ids"] != expected
        or [row["topic_id"] for row in payload["results"]] != expected
    ):
        raise RuntimeError(
            "native producer must compile the exact ordered sealed roster"
        )
    if any(
        not row["compiles"]
        or row["has_sorry"]
        or row["warnings"]
        or row["errors"]
        or row["sorry_occurrences"] != 0
        for row in payload["results"]
    ):
        raise RuntimeError(
            "native producer contains compiler failures, warnings or admitted proofs"
        )
    return {
        "source": before,
        "receipt_sha256": hashlib.sha256(raw).hexdigest(),
        "topic_ids": expected,
        "validation": validation,
    }
