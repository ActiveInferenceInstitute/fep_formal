"""Exercise the actual import-safe stdlib barrier with fake HTTP/time only."""

import contextlib
import importlib.util
import io
import json
import os
import tempfile
import time
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load_barrier():
    path = ROOT / "specs/publication-browser-acceptance/wait_render_dependencies.py"
    spec = importlib.util.spec_from_file_location(
        "tested_render_dependency_barrier", path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert Path(module.__file__).resolve() == path.resolve()
    return module


def _run_case(name, mutate=None, event="pull_request", expected="pass", sequence=None):
    barrier = _load_barrier()
    orig_env = dict(os.environ)
    orig_url = urllib.request.urlopen
    orig_mono, orig_sleep = time.monotonic, time.sleep
    sourcehead = "a" * 40
    checkout = "b" * 40
    apihead = sourcehead if event == "pull_request" else checkout
    metadata = {
        "id": 71,
        "run_attempt": 2,
        "event": event,
        "head_sha": apihead,
        "repository": {"full_name": "owner/repo"},
    }
    job = {
        "name": "render-deps",
        "id": 88,
        "run_id": 71,
        "run_attempt": 2,
        "head_sha": apihead,
        "status": "completed",
        "conclusion": "success",
    }
    artifact = {
        "id": 99,
        "name": "render-figures-71-2",
        "expired": False,
        "size_in_bytes": 100,
        "workflow_run": {"id": 71, "head_sha": apihead},
    }
    data = {
        "metadata": metadata,
        "jobs": {"total_count": 1, "jobs": [job]},
        "artifacts": {"total_count": 1, "artifacts": [artifact]},
    }
    if mutate:
        mutate(data)
    clock = [0.0]
    calls = []
    sleeps = []
    jobcalls = [0]

    class Response:
        def __init__(self, raw):
            self.raw = raw

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self, limit):
            assert limit == 4_000_001
            return self.raw[:limit]

    def fake_url(req, timeout):
        assert timeout == 20 and req.full_url.startswith(
            "https://api.invalid/repos/owner/repo/actions/runs/71"
        )
        assert req.get_header("Authorization") == "Bearer test-only-not-secret"
        calls.append(req.full_url)
        if name == "api_error":
            raise OSError("synthetic API refusal")
        if name == "oversize":
            return Response(b" " * 4_000_001)
        if name == "malformed_json":
            return Response(b"{")
        if "/jobs?" in req.full_url:
            assert "/attempts/2/jobs?" in req.full_url
            n = jobcalls[0]
            jobcalls[0] += 1
            value = sequence[min(n, len(sequence) - 1)] if sequence else data["jobs"]
        elif "/artifacts?" in req.full_url:
            value = data["artifacts"]
        else:
            value = data["metadata"]
        return Response(json.dumps(value).encode())

    def sleep(seconds):
        assert 0 <= seconds <= 10
        sleeps.append(seconds)
        clock[0] += seconds

    with tempfile.TemporaryDirectory(prefix="fep-barrier-pure-") as temp:
        root = Path(temp)
        eventfile = root / "event.json"
        output = root / "output"
        eventfile.write_text(
            json.dumps({"pull_request": {"head": {"sha": sourcehead}}})
        )
        os.environ.clear()
        os.environ.update(
            {
                "GITHUB_REPOSITORY": "owner/repo",
                "GITHUB_RUN_ID": "71",
                "GITHUB_RUN_ATTEMPT": "2",
                "GITHUB_SHA": checkout,
                "GITHUB_EVENT_NAME": event,
                "GITHUB_EVENT_PATH": str(eventfile),
                "GITHUB_API_URL": "https://api.invalid",
                "GH_TOKEN": "test-only-not-secret",
                "GITHUB_OUTPUT": str(output),
            }
        )
        urllib.request.urlopen = fake_url
        time.monotonic = lambda: clock[0]
        time.sleep = sleep
        captured = io.StringIO()
        error = None
        try:
            with contextlib.redirect_stdout(captured):
                barrier.main()
        except (Exception, SystemExit) as exc:
            error = type(exc).__name__ + ": " + str(exc)
        finally:
            urllib.request.urlopen = orig_url
            time.monotonic = orig_mono
            time.sleep = orig_sleep
            os.environ.clear()
            os.environ.update(orig_env)
        text = output.read_text() if output.exists() else ""
        if expected == "pass":
            assert error is None and text == "artifact_id=99\n", (name, error, text)
        else:
            assert error is not None and text == "", (name, error, text)
            if expected == "deadline":
                assert clock[0] == 1200 and error.startswith("SystemExit: Timed out"), (
                    name,
                    error,
                    clock,
                )
        assert "test-only-not-secret" not in captured.getvalue()
        return {
            "name": name,
            "passed": True,
            "expected": expected,
            "actual_error": error,
            "clock_seconds": clock[0],
            "api_calls": len(calls),
            "job_polls": jobcalls[0],
            "immutable_id_output": text,
            "stdout": captured.getvalue(),
        }


def _scenarios():
    rows = []

    def case(name, mutate=None, event="pull_request", expected="pass", sequence=None):
        rows.append(pytest.param(name, mutate, event, expected, sequence, id=name))

    case("PR source distinct from synthetic checkout")
    case("main", event="push")
    case("manual", event="workflow_dispatch")
    basejob = {
        "name": "render-deps",
        "id": 88,
        "run_id": 71,
        "run_attempt": 2,
        "head_sha": "a" * 40,
        "status": "completed",
        "conclusion": "success",
    }
    case(
        "nojob_pending_success",
        sequence=[
            {"total_count": 0, "jobs": []},
            {
                "total_count": 1,
                "jobs": [dict(basejob, status="in_progress", conclusion=None)],
            },
            {"total_count": 1, "jobs": [basejob]},
        ],
    )
    for conclusion in [
        "failure",
        "cancelled",
        "skipped",
        "timed_out",
        "action_required",
    ]:
        case(
            "producer_" + conclusion,
            lambda d, c=conclusion: d["jobs"]["jobs"][0].update(conclusion=c),
            expected="refuse",
        )
    for field, value in [("run_id", 72), ("run_attempt", 1), ("head_sha", "b" * 40)]:
        case(
            "wrong_job_" + field,
            lambda d, f=field, v=value: d["jobs"]["jobs"][0].update({f: v}),
            expected="refuse",
        )
    for field, value in [
        ("id", 72),
        ("run_attempt", 1),
        ("head_sha", "b" * 40),
        ("event", "push"),
    ]:
        case(
            "wrong_run_" + field,
            lambda d, f=field, v=value: d["metadata"].update({f: v}),
            expected="refuse",
        )
    case(
        "wrong_repository",
        lambda d: d["metadata"]["repository"].update(full_name="other/repo"),
        expected="refuse",
    )
    case(
        "duplicate_jobs",
        lambda d: d["jobs"].update(total_count=2, jobs=d["jobs"]["jobs"] * 2),
        expected="refuse",
    )
    case(
        "duplicate_artifacts",
        lambda d: d["artifacts"].update(
            total_count=2, artifacts=d["artifacts"]["artifacts"] * 2
        ),
        expected="refuse",
    )
    for name, mutate in [
        (
            "missing_artifact",
            lambda d: d["artifacts"].update(total_count=0, artifacts=[]),
        ),
        (
            "expired_artifact",
            lambda d: d["artifacts"]["artifacts"][0].update(expired=True),
        ),
        (
            "stale_attempt_name",
            lambda d: d["artifacts"]["artifacts"][0].update(name="render-figures-71-1"),
        ),
        (
            "wrong_run_name",
            lambda d: d["artifacts"]["artifacts"][0].update(name="render-figures-70-2"),
        ),
        (
            "legacy_name",
            lambda d: d["artifacts"]["artifacts"][0].update(name="render-figures"),
        ),
        ("no_job_deadline", lambda d: d["jobs"].update(total_count=0, jobs=[])),
    ]:
        case(name, mutate, expected="deadline")
    for field, value in [("id", 72), ("head_sha", "c" * 40)]:
        case(
            "wrong_artifact_" + field,
            lambda d, f=field, v=value: d["artifacts"]["artifacts"][0][
                "workflow_run"
            ].update({f: v}),
            expected="refuse",
        )
    case(
        "empty_artifact",
        lambda d: d["artifacts"]["artifacts"][0].update(size_in_bytes=0),
        expected="refuse",
    )
    for key in ["jobs", "artifacts"]:
        case(
            key + "_pagination",
            lambda d, k=key: d[k].update(total_count=101),
            expected="refuse",
        )
        case(
            key + "_truncated",
            lambda d, k=key: d[k].update(total_count=2),
            expected="refuse",
        )
    for name in ["api_error", "oversize", "malformed_json"]:
        case(name, expected="refuse")
    return rows


@pytest.mark.parametrize("name,mutate,event,expected,sequence", _scenarios())
def test_render_dependency_barrier(name, mutate, event, expected, sequence):
    result = _run_case(name, mutate, event, expected, sequence)
    assert result["passed"] is True


def test_import_does_not_require_environment_or_access_network(monkeypatch):
    monkeypatch.setattr(os, "environ", {})

    def forbidden(*args, **kwargs):
        raise AssertionError("Import must not access HTTP")

    monkeypatch.setattr(urllib.request, "urlopen", forbidden)
    assert callable(_load_barrier().main)
