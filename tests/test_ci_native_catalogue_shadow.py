"""Comparison controls use real receipt validation, never simulated acceptance."""

from __future__ import annotations

import copy
import json

import pytest

from fep_lean.output.evidence import build_native_lean_receipt
from fep_lean.verification.lean_verifier import VerifyResult
from tests._support import native_catalogue_shadow as shadow
from tests.test_native_evidence import (
    LEAN_VERSION,
    _copy_complete_owner_tree,
    _topic_ids,
)


@pytest.mark.parametrize(
    "mode",
    [
        "pass",
        "warning",
        "source",
        "roster",
        "same",
        "commit",
        "run",
        "symlink",
        "version",
    ],
)
def test_compare_two_receipts_with_real_validator(tmp_path, monkeypatch, mode):
    root = tmp_path / "checkout"
    _copy_complete_owner_tree(root)
    ids = _topic_ids(root)
    payload = build_native_lean_receipt(
        root,
        ids,
        [
            VerifyResult(
                topic_id=n, compiles=True, has_sorry=False, lean_version=LEAN_VERSION
            )
            for n in ids
        ],
    )
    first = root / "first.json"
    second = root / "second.json"
    first.write_text(json.dumps(payload))
    other = copy.deepcopy(payload)
    other["duration_s"] = 1
    other["results"][0]["duration_s"] = 1
    if mode == "warning":
        other["results"][0]["warnings"] = ["warning: control"]
    if mode == "source":
        other["source_digest"] = "0" * 64
    if mode == "roster":
        other["requested_topic_ids"].reverse()
    if mode == "version":
        other["results"][0]["lean_version"] = "different"
    second.write_text(json.dumps(other))
    if mode == "symlink":
        target = root / "target.json"
        second.rename(target)
        second.symlink_to(target)
    monkeypatch.setattr(
        shadow.subprocess, "check_output", lambda *a, **k: "a" * 40 + "\n"
    )
    kwargs = {
        "run_id": "123" if mode != "run" else "",
        "attempt": "1",
        "commit": "a" * 40 if mode != "commit" else "b" * 40,
    }
    if mode == "pass":
        result = shadow.compare_native_catalogue_receipts(root, first, second, **kwargs)
        assert (
            result["passed"]
            and result["topic_ids"] == ids
            and result["producer_duration_s"] != result["cli_duration_s"]
        )
    else:
        with pytest.raises(ValueError):
            shadow.compare_native_catalogue_receipts(
                root, first, first if mode == "same" else second, **kwargs
            )
