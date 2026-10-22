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
from fep_lean.verification.lean_verifier import VerifyResult, verify_catalogue

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


def validate_native_catalogue_producer(root: Path, *, junit: Path) -> dict[str, Any]:
    """Consume this job's producer evidence without compiling or writing receipts.

    GitHub job/artifact provenance is authenticated independently at publication.
    The claimed intent alone is not completion: the actual API, strict native
    receipt and once-passing serial node must agree here.
    """
    import xml.etree.ElementTree as ET

    root = root.resolve(strict=True)
    output = root / "output"
    if output.is_symlink():
        raise ValueError("native consumer output must not be a symlink")
    paths = {
        "receipt": output / "native-verification.json",
        "intent": output / "native-catalogue-producer.intent.json",
        "invocation": output / "native-catalogue-producer.json",
        "junit": junit,
    }
    if junit.parent != output:
        raise ValueError("native consumer requires this checkout's serial JUnit")
    captured = {}
    for name, path in paths.items():
        if path.is_symlink() or not path.is_file():
            raise ValueError("regular current producer evidence required: " + name)
        captured[name] = path.read_bytes()
    before = _source_snapshot(root)
    with tempfile.TemporaryDirectory(prefix="fep-native-consumer-") as directory:
        frozen = Path(directory) / "native-verification.json"
        frozen.write_bytes(captured["receipt"])
        validation = validate_native_lean_receipt(frozen, project_root=root)
    if not all(
        validation.get(k) is True
        for k in ("valid", "source_bound", "native_claim_ready")
    ):
        raise ValueError("producer native receipt is not source-bound and claim-ready")
    payload = json.loads(captured["receipt"])
    expected = list(
        FEPTopicCatalogue.from_yaml(root / "config/topics.yaml").roster.topic_ids
    )
    if (
        payload["requested_topic_ids"] != expected
        or [r["topic_id"] for r in payload["results"]] != expected
    ):
        raise ValueError("producer must cover the exact ordered sealed roster")
    if json.loads(captured["intent"]) != {
        "state": "claimed",
        "operation": "verify_catalogue",
        "topic_ids": None,
        "area": None,
        "fail_on_warnings": True,
    }:
        raise ValueError("strict unfiltered producer intent required")
    invocation = json.loads(captured["invocation"])
    fields = {
        "status",
        "mode",
        "complete",
        "catalogue_topics",
        "verified_topics",
        "compiled_without_sorry_topics",
        "warning_count",
        "sorry_count",
        "mathlib",
        "receipt",
        "native_claim_ready",
        "results",
    }
    if not isinstance(invocation, dict) or set(invocation) != fields:
        raise ValueError("closed producer API record required")
    count = len(expected)
    if (
        invocation["status"] != "ok"
        or invocation["mode"] != "lean-only"
        or invocation["complete"] is not True
        or invocation["native_claim_ready"] is not True
        or any(
            type(invocation[k]) is not int or invocation[k] != count
            for k in (
                "catalogue_topics",
                "verified_topics",
                "compiled_without_sorry_topics",
            )
        )
        or any(
            type(invocation[k]) is not int or invocation[k] != 0
            for k in ("warning_count", "sorry_count")
        )
        or type(invocation["mathlib"]) is not str
        or invocation["mathlib"]
        != "Mathlib built (`Mathlib.olean` and required leaves present)"
        or type(invocation["receipt"]) is not str
        or not Path(invocation["receipt"]).is_absolute()
        or ".." in Path(invocation["receipt"]).parts
        or invocation["receipt"] != str(paths["receipt"])
        or Path(invocation["receipt"]).resolve(strict=True)
        != paths["receipt"].resolve(strict=True)
        or not isinstance(invocation["results"], list)
        or len(invocation["results"]) != count
    ):
        raise ValueError("producer API did not complete the strict full roster")

    def same_typed_json(left: Any, right: Any) -> bool:
        if type(left) is not type(right):
            return False
        if isinstance(right, dict):
            return set(left) == set(right) and all(
                same_typed_json(left[k], v) for k, v in right.items()
            )
        if isinstance(right, list):
            return len(left) == len(right) and all(
                same_typed_json(a, b) for a, b in zip(left, right, strict=True)
            )
        return left == right

    for api_row, native_row in zip(
        invocation["results"], payload["results"], strict=True
    ):
        # Use the real VerifyResult projection, including status/skip/failure fields.
        # Its optional retries field is emitted only for the documented retry-once result.
        if not isinstance(api_row, dict):
            raise TypeError("closed producer API result required")
        retries = api_row.get("retries", 0)
        if "retries" in api_row and (type(retries) is not int or retries != 1):
            raise ValueError(
                "producer API retry projection differs from typed contract"
            )
        projected = VerifyResult(
            topic_id=native_row["topic_id"],
            compiles=native_row["compiles"],
            has_sorry=native_row["has_sorry"],
            sorry_occurrences=native_row["sorry_occurrences"],
            errors=native_row["errors"],
            warnings=native_row["warnings"],
            duration_s=native_row["duration_s"],
            lean_version=native_row["lean_version"],
            retries=retries,
        ).as_dict()
        if not same_typed_json(api_row, projected):
            raise ValueError(
                "producer API outcomes differ from actual typed native projection"
            )
    try:
        cases = list(ET.fromstring(captured["junit"]).iter("testcase"))
    except ET.ParseError as error:
        raise ValueError("malformed serial JUnit") from error
    selected = [
        c
        for c in cases
        if c.attrib.get("classname") == "tests.test_catalogue_bodies_compile"
        and c.attrib.get("name") == "test_all_catalogue_bodies_compile"
    ]
    if (
        len(selected) != 1
        or any(
            selected[0].find(tag) is not None for tag in ("skipped", "failure", "error")
        )
        or any(
            c.find("failure") is not None or c.find("error") is not None for c in cases
        )
    ):
        raise ValueError(
            "exactly one passing producer in a successful serial lane required"
        )
    if _source_snapshot(root) != before:
        raise ValueError("producer source changed during consumption")
    for name, path in paths.items():
        if path.is_symlink() or path.read_bytes() != captured[name]:
            raise ValueError("producer evidence changed during consumption")
    return {
        "validation": validation,
        "topic_ids": expected,
        "evidence_sha256": {
            name: hashlib.sha256(raw).hexdigest() for name, raw in captured.items()
        },
        "producer_node_passed_exactly_once": True,
    }
