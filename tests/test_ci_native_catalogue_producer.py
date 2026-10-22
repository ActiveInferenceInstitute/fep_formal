"""Real receipt-validation controls around the single mocked compile boundary.

These tests do not claim native execution; a hosted shadow run must compare
actual compiler outcomes before the duplicate gate can be removed.
"""

from __future__ import annotations

import copy
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
