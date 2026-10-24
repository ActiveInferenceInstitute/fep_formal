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


@pytest.fixture
def supplement_contract():
    """Import the exact slice helper; no process, network or actual CI fixture."""
    import importlib.util
    from pathlib import Path

    path = (
        Path(__file__).resolve().parents[1]
        / "specs/publication-browser-acceptance/native_supplement.py"
    )
    spec = importlib.util.spec_from_file_location("native_supplement_controls", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert Path(module.__file__).resolve() == path
    return module


def _supplement_join_fixture(module):
    candidate, base, checkout, tree = (letter * 40 for letter in "abcd")
    reference = {
        "schema_version": 1,
        "profile": module.PROFILE,
        "candidate": candidate,
        "base": base,
        "tree": tree,
        "automatic_checkout": checkout,
        "workflow_sha256": "e" * 64,
        "automatic_run_id": 101,
        "automatic_run_attempt": 2,
        "pr_number": 7,
        "supplement_run_id": 202,
        "supplement_run_attempt": 1,
    }
    run = {
        "repository": {"full_name": module.REPOSITORY, "id": module.REPOSITORY_ID},
        "workflow_id": module.WORKFLOW_ID,
        "path": module.WORKFLOW_PATH,
        "id": 101,
        "run_attempt": 2,
        "event": "pull_request",
        "head_sha": candidate,
        "pull_requests": [
            {
                "number": 7,
                "head": {"sha": candidate, "repo": {"id": module.REPOSITORY_ID}},
                "base": {"sha": base, "repo": {"id": module.REPOSITORY_ID}},
            }
        ],
        "status": "completed",
        "conclusion": "success",
    }
    validation = {
        "supplement_join_schema": "full-automatic-source-projection-v1",
        "profile": "pull_request",
        "run_id": 101,
        "run_attempt": 2,
        "state": "FULL_PROFILE_AND_ACTUAL_CAPTURED_CONSUMER_VALIDATED_PDF_ACCEPTANCE_PENDING",
        "head": candidate,
        "artifact_commit": checkout,
        "captured_checkout_commit": checkout,
        "synthetic_parents": [base, candidate],
        "source_tree": tree,
        "workflow_sha256": reference["workflow_sha256"],
        "artifact_roster": {"total_count": 5, "artifacts": list(range(5))},
        "jobs": [
            {
                "name": name,
                "status": "completed",
                "conclusion": "skipped" if name == "documentation" else "success",
            }
            for name in sorted(module.ROLE_NAMES)
        ],
        "audit_defects": [],
        "render_defects": [],
        "native_validation": {"native_claim_ready": True, "verified_topics": 168},
    }
    supplement = {
        "passed": True,
        "complete": True,
        "profile": module.PROFILE,
        "head": candidate,
        "run_id": 202,
        "run_attempt": 1,
        "reference": reference,
        "producer_cases": 1,
        "api_topics": 168,
        "cli_topics": 168,
        "nonduration_equal": True,
        "original_zip_verified": True,
        "production_api_source_bound": True,
        "production_cli_source_bound": True,
        "runtime_unchanged": True,
    }
    return reference, run, validation, supplement


@pytest.mark.parametrize(
    "mode",
    [
        "pass",
        "wrong-repository",
        "wrong-workflow",
        "wrong-event",
        "wrong-auto-attempt",
        "wrong-pr",
        "foreign-pr",
        "automatic-active",
        "automatic-failed",
        "wrong-synthetic",
        "reversed-parents",
        "wrong-tree",
        "wrong-workflow-bytes",
        "missing-wheel",
        "failed-job",
        "missing-original-artifact",
        "wrong-supplement-attempt",
        "fake-full-serial",
        "stale-api",
        "stale-cli",
        "runtime-drift",
        "missing-pdf",
        "stale-automatic-review",
        "stale-supplement-review",
    ],
)
def test_versioned_native_supplement_release_join(supplement_contract, mode):
    module = supplement_contract
    reference, run, validation, supplement = _supplement_join_fixture(module)
    if mode == "wrong-repository":
        run["repository"]["full_name"] = "other/fep_formal"
    elif mode == "wrong-workflow":
        run["workflow_id"] += 1
    elif mode == "wrong-event":
        run["event"] = "workflow_dispatch"
    elif mode == "wrong-auto-attempt":
        run["run_attempt"] += 1
    elif mode == "wrong-pr":
        run["pull_requests"][0]["number"] += 1
    elif mode == "foreign-pr":
        run["pull_requests"][0]["head"]["repo"]["id"] += 1
    elif mode == "automatic-active":
        run.update(status="in_progress", conclusion=None)
    elif mode == "automatic-failed":
        run["conclusion"] = "failure"
    elif mode == "wrong-synthetic":
        validation["artifact_commit"] = reference["candidate"]
    elif mode == "reversed-parents":
        validation["synthetic_parents"].reverse()
    elif mode == "wrong-tree":
        validation["source_tree"] = "f" * 40
    elif mode == "wrong-workflow-bytes":
        validation["workflow_sha256"] = "f" * 64
    elif mode == "missing-wheel":
        validation["jobs"].pop()
    elif mode == "failed-job":
        next(row for row in validation["jobs"] if row["name"] == "lean")[
            "conclusion"
        ] = "failure"
    elif mode == "missing-original-artifact":
        validation["artifact_roster"]["artifacts"].pop()
    elif mode == "wrong-supplement-attempt":
        supplement["run_attempt"] += 1
    elif mode == "fake-full-serial":
        supplement["producer_cases"] = 640
    elif mode == "stale-api":
        supplement["production_api_source_bound"] = False
    elif mode == "stale-cli":
        supplement["production_cli_source_bound"] = False
    elif mode == "runtime-drift":
        supplement["runtime_unchanged"] = False
    encode = lambda obj: json.dumps(obj, sort_keys=True).encode()
    v_raw, s_raw = encode(validation), encode(supplement)
    acceptance = {
        "passed": True,
        "complete": True,
        "head": reference["candidate"],
        "run_id": 101,
        "run_attempt": 2,
        "validation_sha256": module.sha(v_raw),
        "PDF_scoped_acceptance": mode != "missing-pdf",
    }
    a_raw = encode(acceptance)
    review = {
        "passed": True,
        "complete": True,
        "head": reference["candidate"],
        "acceptance_sha256": module.sha(a_raw)
        if mode != "stale-automatic-review"
        else "0" * 64,
    }
    s_review = {
        "passed": True,
        "complete": True,
        "head": reference["candidate"],
        "qualification_sha256": module.sha(s_raw)
        if mode != "stale-supplement-review"
        else "0" * 64,
    }
    if mode == "pass":
        result = module.join_release(
            reference, run, v_raw, a_raw, encode(review), s_raw, encode(s_review)
        )
        assert result["passed"] and result["automatic_checkout"] != result["head"]
    else:
        with pytest.raises(ValueError):
            module.join_release(
                reference, run, v_raw, a_raw, encode(review), s_raw, encode(s_review)
            )


def test_active_automatic_reference_is_identity_only(
    supplement_contract, tmp_path, monkeypatch
):
    import io
    import sys
    from pathlib import Path
    from types import SimpleNamespace

    module = supplement_contract
    for invalid in (True, 0, -1, "1"):
        with pytest.raises(ValueError, match="positive integer"):
            module.positive(invalid)
    assert module.positive(1) == 1
    for invalid in (None, "A" * 40, 123):
        with pytest.raises(ValueError, match="exact commit"):
            module.commit(invalid)
    assert module.commit("a" * 40) == "a" * 40
    monkeypatch.setenv("GITHUB_REPOSITORY", module.REPOSITORY)
    monkeypatch.setenv("GITHUB_API_URL", "https://api.github.com")
    monkeypatch.setenv("GH_TOKEN", "synthetic-control-token")
    for index, payload in enumerate(([], None, True, {"id": 1})):
        raw = json.dumps(payload).encode()
        with monkeypatch.context() as local:
            local.setattr(
                module.urllib.request,
                "urlopen",
                lambda request, timeout, data=raw: io.BytesIO(data),
            )
            dest = tmp_path / f"api-{index}.json"
            if isinstance(payload, dict):
                assert module.api("/actions/runs/1", dest) == payload
            else:
                with pytest.raises(ValueError, match="metadata object"):
                    module.api("/actions/runs/1", dest)
            assert dest.read_bytes() == raw
    root = Path(module.__file__).resolve().parents[2]
    names = (
        "tests/__init__.py",
        "tests/_support/__init__.py",
        "tests/_support/native_catalogue_gate.py",
        "tests/_support/native_catalogue_shadow.py",
    )
    source_before = {
        name: {"sha256": module.sha((root / name).read_bytes())} for name in names
    }
    with monkeypatch.context() as local:
        local.setitem(sys.modules, "tests", SimpleNamespace(__file__=None))
        with pytest.raises(ValueError, match="module file missing"):
            module.native_validators(root, source_before)
    with monkeypatch.context() as local:
        local.setattr(
            module.importlib,
            "import_module",
            lambda name: SimpleNamespace(__file__=None),
        )
        with pytest.raises(ValueError, match="validator import origin"):
            module.native_validators(root, source_before)
    reference, run, _, _ = _supplement_join_fixture(module)
    run.update(status="in_progress", conclusion=None)
    kwargs = {
        "run_id": 101,
        "attempt": 2,
        "pr_number": 7,
        "candidate": reference["candidate"],
        "base": reference["base"],
    }
    module.automatic_identity(run, **kwargs)
    with pytest.raises(ValueError, match="not terminal"):
        module.automatic_identity(run, terminal=True, **kwargs)


@pytest.mark.parametrize("mode", ["pass", "skip", "twice", "wrong-node"])
def test_native_supplement_is_exactly_one_producer(supplement_contract, mode):
    module = supplement_contract
    node = '<testcase classname="tests.test_catalogue_bodies_compile" name="test_all_catalogue_bodies_compile">{}</testcase>'
    raw = node.format("<skipped/>" if mode == "skip" else "")
    if mode == "twice":
        raw += raw
    if mode == "wrong-node":
        raw = raw.replace("test_all_catalogue_bodies_compile", "unrelated")
    raw = ("<testsuite>" + raw + "</testsuite>").encode()
    if mode == "pass":
        module.producer_case(raw)
    else:
        with pytest.raises(ValueError):
            module.producer_case(raw)
