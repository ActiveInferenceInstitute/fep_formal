"""Real receipt-validation controls around the single mocked compile boundary.

These tests do not claim native execution; a hosted shadow run must compare
actual compiler outcomes before the duplicate gate can be removed.
"""

from __future__ import annotations

import copy
import json
import subprocess
from types import SimpleNamespace

import pytest

from fep_lean.output.evidence import (
    build_native_lean_receipt,
    write_native_lean_receipt,
)
from fep_lean.verification.lean_verifier import CatalogueVerification, VerifyResult
from tests._support import native_catalogue_gate as gate
from tests.test_native_evidence import (
    LEAN_VERSION,
    _copy_complete_owner_tree,
    _topic_ids,
)


@pytest.fixture
def producer(tmp_path, monkeypatch):
    root = tmp_path / "checkout"
    _copy_complete_owner_tree(root)
    ids = _topic_ids(root)
    results = [
        VerifyResult(
            topic_id=name, compiles=True, has_sorry=False, lean_version=LEAN_VERSION
        )
        for name in ids
    ]
    payload = build_native_lean_receipt(root, ids, results)
    calls = []
    state = SimpleNamespace(
        root=root, payload=payload, calls=calls, exit_code=0, mutate_source=False
    )

    def compile_once(at, topic_ids, area, *, receipt_path, fail_on_warnings):
        calls.append((at, topic_ids, area, receipt_path, fail_on_warnings))
        write_native_lean_receipt(receipt_path, copy.deepcopy(payload))
        if state.mutate_source:
            owner = root / "src/fep_lean/lean_source.py"
            owner.write_text(owner.read_text() + "\n# source drift\n")
        return CatalogueVerification(
            {"complete": state.exit_code == 0}, state.exit_code, 2
        )

    monkeypatch.setattr(gate, "verify_catalogue", compile_once)
    return state


def test_single_strict_unfiltered_call_and_real_receipt_validation(producer):
    result = gate.produce_native_catalogue_receipt(producer.root, "1")
    assert producer.calls == [
        (
            producer.root,
            None,
            None,
            producer.root / "output/native-verification.json",
            True,
        )
    ]
    assert result["validation"]["native_claim_ready"] is True
    assert result["topic_ids"] == _topic_ids(producer.root)
    assert result["validation"]["verified_topics"] == 168


@pytest.mark.parametrize("flag", ["", "0", "true", "yes"])
def test_explicit_invalid_mode_never_compiles_or_skips(producer, flag):
    with pytest.raises(ValueError, match="flag"):
        gate.produce_native_catalogue_receipt(producer.root, flag)
    assert not producer.calls


@pytest.mark.parametrize(
    "name",
    [
        "native-verification.json",
        "native-catalogue-producer.intent.json",
        "native-catalogue-producer.json",
    ],
)
def test_preexisting_evidence_or_claim_refuses_before_compile(producer, name):
    output = producer.root / "output"
    output.mkdir()
    (output / name).write_text("historical")
    with pytest.raises(FileExistsError, match="fresh"):
        gate.produce_native_catalogue_receipt(producer.root, "1")
    assert not producer.calls


@pytest.mark.parametrize(
    "field,value",
    [
        ("compiles", False),
        ("has_sorry", True),
        ("warnings", ["warning"]),
        ("errors", ["error"]),
        ("sorry_occurrences", 1),
        ("lean_version", "Lean version 4.34.0"),
    ],
)
def test_real_validator_refuses_adverse_compiler_rows(producer, field, value):
    producer.payload["results"][0][field] = value
    with pytest.raises(RuntimeError, match="claim-ready|compiler"):
        gate.produce_native_catalogue_receipt(producer.root, "1")
    assert len(producer.calls) == 1


@pytest.mark.parametrize("mutation", ["subset", "duplicate", "reordered", "extra"])
def test_real_validator_refuses_wrong_roster(producer, mutation):
    rows = producer.payload["results"]
    if mutation == "subset":
        rows.pop()
    elif mutation == "duplicate":
        rows[1] = copy.deepcopy(rows[0])
    elif mutation == "reordered":
        rows.reverse()
    else:
        rows.append(copy.deepcopy(rows[0]))
    with pytest.raises(RuntimeError, match="claim-ready|roster"):
        gate.produce_native_catalogue_receipt(producer.root, "1")


def test_source_mutation_during_compile_is_refused(producer):
    producer.mutate_source = True
    with pytest.raises(RuntimeError, match="source changed"):
        gate.produce_native_catalogue_receipt(producer.root, "1")


def test_failed_producer_cannot_be_retried_in_same_job_root(producer):
    producer.exit_code = 1
    with pytest.raises(RuntimeError, match="producer failed"):
        gate.produce_native_catalogue_receipt(producer.root, "1")
    with pytest.raises(FileExistsError, match="fresh"):
        gate.produce_native_catalogue_receipt(producer.root, "1")
    assert len(producer.calls) == 1
    assert (producer.root / "output/native-catalogue-producer.json").is_file()


def test_timeout_preserves_claim_and_refuses_unrecorded_retry(producer, monkeypatch):
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(
            "native compile", 1, output="partial compiler output"
        )

    monkeypatch.setattr(gate, "verify_catalogue", timeout)
    with pytest.raises(subprocess.TimeoutExpired):
        gate.produce_native_catalogue_receipt(producer.root, "1")
    assert (producer.root / "output/native-catalogue-producer.intent.json").is_file()
    assert not (producer.root / "output/native-verification.json").exists()
    with pytest.raises(FileExistsError):
        gate.produce_native_catalogue_receipt(producer.root, "1")


def test_symlink_output_is_refused_before_compile(producer, tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (producer.root / "output").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        gate.produce_native_catalogue_receipt(producer.root, "1")
    assert not producer.calls
    assert not list(outside.iterdir())


def test_dangling_receipt_symlink_is_refused(producer, tmp_path):
    (producer.root / "output").mkdir()
    (producer.root / "output/native-verification.json").symlink_to(tmp_path / "absent")
    with pytest.raises(FileExistsError):
        gate.produce_native_catalogue_receipt(producer.root, "1")
    assert not producer.calls


def test_exclusive_intent_allows_only_one_concurrent_producer(producer, monkeypatch):
    import threading
    from concurrent.futures import ThreadPoolExecutor
    from pathlib import Path

    barrier = threading.Barrier(2)
    original_open = Path.open

    def synchronized_open(path, mode="r", *args, **kwargs):
        if path.name == "native-catalogue-producer.intent.json" and mode == "x":
            barrier.wait(timeout=10)
        return original_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", synchronized_open)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(gate.produce_native_catalogue_receipt, producer.root, "1")
            for _ in range(2)
        ]
        outcomes = []
        for future in futures:
            try:
                outcomes.append(future.result(timeout=30))
            except FileExistsError:
                outcomes.append("refused")
    assert sum(isinstance(value, dict) for value in outcomes) == 1
    assert outcomes.count("refused") == 1
    assert len(producer.calls) == 1


def test_actual_missing_mathlib_path_fails_ci_mode_without_skip(producer, monkeypatch):
    from fep_lean.verification.lean_verifier import LeanVerifier, verify_catalogue

    monkeypatch.setattr(gate, "verify_catalogue", verify_catalogue)
    monkeypatch.setattr(
        LeanVerifier,
        "check_mathlib_built",
        lambda self: (False, "cache absent control"),
    )

    def forbidden(*args, **kwargs):
        raise AssertionError("missing Mathlib must not start compilation")

    monkeypatch.setattr(LeanVerifier, "verify_batch", forbidden)
    with pytest.raises(RuntimeError, match="producer failed"):
        gate.produce_native_catalogue_receipt(producer.root, "1")
    assert not (producer.root / "output/native-verification.json").exists()
    assert (
        "cache absent control"
        in (producer.root / "output/native-catalogue-producer.json").read_text()
    )


@pytest.fixture
def consumer(producer):
    """Synthetic compiler boundary, real native receipt construction/validation."""
    gate.produce_native_catalogue_receipt(producer.root, "1")
    output = producer.root / "output"
    native = json.loads((output / "native-verification.json").read_text())
    invocation = {
        "status": "ok",
        "mode": "lean-only",
        "complete": True,
        "catalogue_topics": 168,
        "verified_topics": 168,
        "compiled_without_sorry_topics": 168,
        "warning_count": 0,
        "sorry_count": 0,
        "mathlib": "Mathlib built (`Mathlib.olean` and required leaves present)",
        "receipt": str(output / "native-verification.json"),
        "native_claim_ready": True,
        "results": [
            VerifyResult(
                topic_id=row["topic_id"],
                compiles=row["compiles"],
                has_sorry=row["has_sorry"],
                sorry_occurrences=row["sorry_occurrences"],
                errors=row["errors"],
                warnings=row["warnings"],
                duration_s=row["duration_s"],
                lean_version=row["lean_version"],
            ).as_dict()
            for row in native["results"]
        ],
    }
    (output / "native-catalogue-producer.json").write_text(json.dumps(invocation))
    junit = output / "serial-lean-acceptance.xml"
    junit.write_text(
        '<testsuite><testcase classname="tests.test_catalogue_bodies_compile" '
        'name="test_all_catalogue_bodies_compile"/></testsuite>'
    )
    producer.junit = junit
    return producer


def test_consumer_validates_actual_records_without_second_compile(consumer):
    result = gate.validate_native_catalogue_producer(
        consumer.root, junit=consumer.junit
    )
    assert result["validation"]["native_claim_ready"]
    assert result["producer_node_passed_exactly_once"]
    assert len(consumer.calls) == 1


@pytest.mark.parametrize(
    "name",
    [
        "native-verification.json",
        "native-catalogue-producer.intent.json",
        "native-catalogue-producer.json",
        "serial-lean-acceptance.xml",
    ],
)
@pytest.mark.parametrize("mutation", ["missing", "symlink", "malformed"])
def test_consumer_refuses_unavailable_or_nonregular_records(consumer, name, mutation):
    path = consumer.root / "output" / name
    if mutation == "missing":
        path.unlink()
    elif mutation == "symlink":
        target = path.with_suffix(".retained")
        path.rename(target)
        path.symlink_to(target)
    else:
        path.write_text("malformed")
    with pytest.raises((ValueError, RuntimeError)):
        gate.validate_native_catalogue_producer(consumer.root, junit=consumer.junit)
    assert len(consumer.calls) == 1


@pytest.mark.parametrize(
    "field,value",
    [
        ("complete", False),
        ("status", "error"),
        ("verified_topics", 167),
        ("warning_count", 1),
        ("native_claim_ready", False),
    ],
)
def test_consumer_refuses_incomplete_or_non_strict_api(consumer, field, value):
    path = consumer.root / "output/native-catalogue-producer.json"
    data = json.loads(path.read_text())
    data[field] = value
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="API"):
        gate.validate_native_catalogue_producer(consumer.root, junit=consumer.junit)


@pytest.mark.parametrize(
    "mutation", ["reordered", "duplicate", "missing", "duration", "extra-field"]
)
def test_consumer_refuses_api_receipt_mismatch(consumer, mutation):
    path = consumer.root / "output/native-catalogue-producer.json"
    data = json.loads(path.read_text())
    if mutation == "reordered":
        data["results"].reverse()
    elif mutation == "duplicate":
        data["results"][1] = copy.deepcopy(data["results"][0])
    elif mutation == "missing":
        data["results"].pop()
    elif mutation == "duration":
        data["results"][0]["duration_s"] += 1
    else:
        data["unknown"] = True
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="API"):
        gate.validate_native_catalogue_producer(consumer.root, junit=consumer.junit)


@pytest.mark.parametrize("mutation", ["strict", "filter", "extra"])
def test_consumer_refuses_changed_producer_intent(consumer, mutation):
    path = consumer.root / "output/native-catalogue-producer.intent.json"
    data = json.loads(path.read_text())
    if mutation == "strict":
        data["fail_on_warnings"] = False
    elif mutation == "filter":
        data["topic_ids"] = ["fep-001"]
    else:
        data["unknown"] = True
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="intent"):
        gate.validate_native_catalogue_producer(consumer.root, junit=consumer.junit)


@pytest.mark.parametrize(
    "mutation", ["missing", "duplicate", "skipped", "failure", "error"]
)
def test_consumer_requires_once_passing_serial_producer(consumer, mutation):
    import xml.etree.ElementTree as ET

    tree = ET.parse(consumer.junit)
    suite = tree.getroot()
    node = suite[0]
    if mutation == "missing":
        suite.remove(node)
    elif mutation == "duplicate":
        suite.append(copy.deepcopy(node))
    else:
        ET.SubElement(node, mutation)
    tree.write(consumer.junit)
    with pytest.raises(ValueError, match="passing producer"):
        gate.validate_native_catalogue_producer(consumer.root, junit=consumer.junit)


def test_consumer_refuses_stale_source_without_recompile(consumer):
    owner = consumer.root / "src/fep_lean/lean_source.py"
    owner.write_text(owner.read_text() + "\n# stale source\n")
    with pytest.raises(ValueError, match="source-bound"):
        gate.validate_native_catalogue_producer(consumer.root, junit=consumer.junit)
    assert len(consumer.calls) == 1


def test_consumer_refuses_input_replacement_during_validation(consumer, monkeypatch):
    original = gate.validate_native_lean_receipt

    def replace_after_validation(*args, **kwargs):
        result = original(*args, **kwargs)
        path = consumer.root / "output/native-catalogue-producer.intent.json"
        path.write_text("{}")
        return result

    monkeypatch.setattr(gate, "validate_native_lean_receipt", replace_after_validation)
    with pytest.raises(ValueError, match="changed during consumption"):
        gate.validate_native_catalogue_producer(consumer.root, junit=consumer.junit)


@pytest.mark.parametrize(
    "field,value",
    [
        ("unexpected", True),
        ("compiles", 1),
        ("has_sorry", 0),
        ("sorry_occurrences", False),
        ("duration_s", False),
        ("status", "compile_error"),
        ("skip_reason", "invented"),
        ("failure_kind", "timeout"),
        ("lean_file", "/foreign.lean"),
        ("retries", True),
        ("retries", 0),
        ("retries", 2),
    ],
)
def test_consumer_rejects_noncanonical_typed_api_result(consumer, field, value):
    path = consumer.root / "output/native-catalogue-producer.json"
    data = json.loads(path.read_text())
    data["results"][0][field] = value
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="API"):
        gate.validate_native_catalogue_producer(consumer.root, junit=consumer.junit)


@pytest.mark.parametrize("value", [False, "fixture", "Mathlib not built", ""])
def test_consumer_rejects_wrong_mathlib_projection(consumer, value):
    path = consumer.root / "output/native-catalogue-producer.json"
    data = json.loads(path.read_text())
    data["mathlib"] = value
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="API"):
        gate.validate_native_catalogue_producer(consumer.root, junit=consumer.junit)


@pytest.mark.parametrize("mode", ["foreign", "relative", "parent-hop", "symlink"])
def test_consumer_requires_exact_current_receipt_target(consumer, mode):
    output = consumer.root / "output"
    path = output / "native-catalogue-producer.json"
    data = json.loads(path.read_text())
    if mode == "foreign":
        data["receipt"] = "/foreign/native-verification.json"
    elif mode == "relative":
        data["receipt"] = "output/native-verification.json"
    elif mode == "parent-hop":
        data["receipt"] = str(output / ".." / "output" / "native-verification.json")
    else:
        alias = output / "alias"
        alias.symlink_to(output, target_is_directory=True)
        data["receipt"] = str(alias / "native-verification.json")
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="API"):
        gate.validate_native_catalogue_producer(consumer.root, junit=consumer.junit)


def test_consumer_accepts_real_retry_once_projection(consumer):
    path = consumer.root / "output/native-catalogue-producer.json"
    data = json.loads(path.read_text())
    data["results"][0]["retries"] = 1
    path.write_text(json.dumps(data))
    assert gate.validate_native_catalogue_producer(consumer.root, junit=consumer.junit)[
        "producer_node_passed_exactly_once"
    ]
