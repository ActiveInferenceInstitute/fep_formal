"""Exercise the actual import-safe stdlib barrier with fake HTTP/time only."""

import contextlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import tempfile
import textwrap
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


@pytest.mark.parametrize(
    "update_code,install_code,expected_code,expected_calls",
    [(0, 0, 0, 2), (42, 0, 42, 1), (0, 43, 43, 2)],
    ids=[
        "apt_success_exact_argv",
        "apt_update_failure_stops",
        "apt_install_failure_propagates",
    ],
)
@pytest.mark.parametrize(
    "mirror",
    [
        "azure",
        "official",
        "unknown",
        "mixed",
        "missing",
        "wrong_key",
        "uri_continuation",
        "suite_continuation",
        "duplicate_key",
    ],
)
def test_render_apt_network_prefix(
    tmp_path, update_code, install_code, expected_code, expected_calls, mirror
):
    """Execute only the real workflow APT prefix with Bash builtin stubs."""
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    title = "      - name: Install the XeLaTeX toolchain, Pandoc, pandoc-crossref, and the SVG rasterizer\n"
    assert workflow.count(title) == 1
    step = workflow.split(title, 1)[1].split("      - name:", 1)[0]
    assert "        timeout-minutes: 12\n" in step
    script = textwrap.dedent(step.split("        run: |\n", 1)[1])
    lines = script.splitlines()
    ends = [
        i
        for i, line in enumerate(lines)
        if line.startswith("printf 'FEP_RENDER_INSTALL_PHASE phase=apt_install ")
    ]
    assert len(ends) == 1
    prefix = "\n".join(lines[: ends[0] + 1]) + "\n"
    assert "curl " not in prefix and "dpkg " not in prefix
    bash = shutil.which("bash")
    assert bash is not None, "These workflow contract controls require Bash"
    # Parse the entire unchanged download/install suffix without executing it.
    syntax = subprocess.run(
        [bash, "-n"],
        input=script,
        text=True,
        capture_output=True,
        stdin=None,
        timeout=5,
        check=False,
    )
    assert syntax.returncode == 0, syntax.stdout + syntax.stderr
    sources = tmp_path / "ubuntu.sources"
    azure = (
        "Types: deb\nURIs: https://azure.archive.ubuntu.com/ubuntu/\n"
        "Suites: noble noble-updates noble-backports\nComponents: main universe\n"
        "Signed-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg\n\n"
        "Types: deb\nURIs: http://azure.archive.ubuntu.com/ubuntu/\n"
        "Suites: noble-security\nComponents: main universe\n"
        "Signed-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg\n"
    )
    official = azure.replace(
        "https://azure.archive.ubuntu.com/", "https://archive.ubuntu.com/"
    ).replace("http://azure.archive.ubuntu.com/", "http://security.ubuntu.com/")
    original = {
        "azure": azure,
        "official": official,
        "unknown": azure.replace("azure.archive.ubuntu.com", "unexpected.invalid"),
        "mixed": azure.replace(
            "Suites: noble-security", "Suites: noble noble-security"
        ),
        "missing": "# no Ubuntu source configured\n",
        "wrong_key": azure.replace("ubuntu-archive-keyring.gpg", "unexpected.gpg"),
        "uri_continuation": azure.replace(
            "/ubuntu/\n", "/ubuntu/\n https://unexpected.invalid/ubuntu/\n", 1
        ),
        "suite_continuation": azure.replace(
            "Suites: noble-security", "Suites: noble-security\n noble"
        ),
        "duplicate_key": azure.replace(
            "Types: deb", "Signed-By: /unexpected.gpg\nTypes: deb", 1
        ),
    }[mirror]
    sources.write_text(original)
    literal = "Path('/etc/apt/sources.list.d/ubuntu.sources')"
    assert prefix.count(literal) == 1
    prefix = prefix.replace(literal, f"Path({str(sources)!r})")
    argv_log = tmp_path / "apt-argv.nul"
    stub = r"""
sudo() {
  if [[ "$1" == python3 ]]; then command "$@"; return; fi
  printf '%s\0' "$@" >> "$APT_ARGV_LOG"
  printf '\0' >> "$APT_ARGV_LOG"
  [[ "$1" == apt-get ]] || return 99
  local argument
  for argument in "$@"; do
    if [[ "$argument" == update ]]; then return "$APT_UPDATE_RC"; fi
    if [[ "$argument" == install ]]; then return "$APT_INSTALL_RC"; fi
  done
  return 98
}
"""
    result = subprocess.run(
        [bash, "-e", "-u", "-o", "pipefail", "-c", stub + "\n" + prefix],
        env={
            "PATH": os.environ.get("PATH", ""),
            "APT_ARGV_LOG": str(argv_log),
            "APT_UPDATE_RC": str(update_code),
            "APT_INSTALL_RC": str(install_code),
        },
        stdin=subprocess.DEVNULL,
        text=True,
        capture_output=True,
        timeout=5,
        check=False,
    )
    if mirror not in {"azure", "official"}:
        assert result.returncode != 0
        assert not argv_log.exists()
        assert sources.read_text() == original
        assert "FEP_RENDER_INSTALL_PHASE" not in result.stdout
        return
    assert sources.read_text() == official
    assert result.returncode == expected_code, result.stdout + result.stderr
    raw = argv_log.read_bytes()
    assert raw.endswith(b"\0\0")
    calls = [
        [word.decode("utf-8") for word in call.split(b"\0")]
        for call in raw[:-2].split(b"\0\0")
    ]
    options = [
        "apt-get",
        "-o",
        "Acquire::http::Timeout=30",
        "-o",
        "Acquire::https::Timeout=30",
        "-o",
        "Acquire::Retries=1",
    ]
    expected = [options + ["update", "--error-on=any"]]
    if expected_calls == 2:
        expected.append(
            options
            + [
                "install",
                "-y",
                "--no-install-recommends",
                "texlive-xetex",
                "texlive-latex-recommended",
                "texlive-latex-extra",
                "texlive-fonts-recommended",
                "lmodern",
                "fontconfig",
                "librsvg2-bin",
            ]
        )
    assert calls == expected
    assert (
        "FEP_RENDER_INSTALL_PHASE phase=apt_update " in result.stdout
        if update_code == 0
        else "FEP_RENDER_INSTALL_PHASE" not in result.stdout
    )
    assert ("FEP_RENDER_INSTALL_PHASE phase=apt_install " in result.stdout) == (
        expected_code == 0
    )
