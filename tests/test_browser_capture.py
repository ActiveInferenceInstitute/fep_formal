"""Canonical Chrome/CDP browser acceptance owns its emitted evidence."""

from __future__ import annotations

import hashlib
import json
import os
import stat
import struct
import subprocess
import sys
import tempfile
import zlib
from collections.abc import Iterator
from contextlib import contextmanager, suppress
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import BinaryIO

import pytest

from fep_lean.output import browser_capture as capture_module


def _startup_stderr_tail(stream: BinaryIO) -> str:
    """Read at most 8 KiB without a pipe that can block Chrome startup."""
    size = stream.seek(0, os.SEEK_END)
    stream.seek(max(0, size - 8192))
    tail = stream.read(8192).decode("utf-8", errors="replace")
    return f"stderr_bytes={size}; tail (max 8192 bytes):\n{tail}"


def _startup_port_state(command: list[str]) -> dict[str, object]:
    """Selected port-file metadata only, never its UUID or unbounded contents."""
    profile = next(
        arg.split("=", 1)[1] for arg in command if arg.startswith("--user-data-dir=")
    )
    port_file = Path(profile) / "DevToolsActivePort"
    flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(port_file, flags)
    except FileNotFoundError:
        return {"exists": False, "size": None, "parse_valid": False}
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise ValueError("diagnostic port path is not a regular file")
        size = metadata.st_size
        raw = os.read(descriptor, 4097)
    finally:
        os.close(descriptor)
    lines = raw.decode("utf-8", errors="replace").splitlines()
    valid = False
    if len(raw) <= 4096 and len(lines) >= 2:
        with suppress(ValueError):
            valid = 0 < int(lines[0]) < 65536 and bool(lines[1])
    return {"exists": True, "size": size, "parse_valid": valid}


@pytest.fixture(autouse=True)
def _live_chrome_startup_diagnostics(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Retain per-launch diagnostics for exactly the two live Chrome probes.

    The production context still owns the deadline, errors and process cleanup.
    Anonymous temporary stderr files avoid pipe backpressure and are closed on
    both success and failure. Only a bounded tail enters pytest failure reports.
    """
    if request.node.name not in {
        "test_live_chrome_blocks_and_records_a_delayed_outbound_request",
        "test_live_chrome_replay_terminates_every_profile_writer",
    }:
        return
    original_client = capture_module._chrome_client
    original_subprocess = capture_module.subprocess
    original_os = capture_module.os
    original_resolver = capture_module.resolve_browser_executable
    identities = []
    diagnostic_errors = []

    def diagnostic_resolver(*args, **kwargs):
        result = original_resolver(*args, **kwargs)
        try:
            name, executable, version, digest = result
            identities.append(
                {
                    "name": name,
                    "path": str(executable),
                    "version": version,
                    "sha256": digest,
                }
            )
        except Exception as exc:
            diagnostic_errors.append(repr(exc))
        return result

    monkeypatch.setattr(
        capture_module, "resolve_browser_executable", diagnostic_resolver
    )
    launch = 0

    @contextmanager
    def diagnostic_client(
        executable: Path,
    ) -> Iterator[tuple[capture_module._CdpClient, str]]:
        nonlocal launch
        launch += 1
        processes = []
        launch_records = []
        signal_observations = []
        with tempfile.TemporaryFile() as stderr:

            def diagnostic_popen(*args, **kwargs):
                kwargs["stderr"] = stderr
                process = original_subprocess.Popen(*args, **kwargs)
                processes.append(process)
                try:
                    launch_records.append(
                        (process, args[0], capture_module.time.monotonic())
                    )
                except Exception as exc:
                    diagnostic_errors.append(repr(exc))
                return process

            def diagnostic_killpg(pgid, sig):
                try:
                    for process, command, started in launch_records:
                        if process.pid == pgid:
                            signal_observations.append(
                                {
                                    "pid": process.pid,
                                    "signal": int(sig),
                                    "returncode_before_signal": process.poll(),
                                    "elapsed_since_Popen_return_seconds": capture_module.time.monotonic()
                                    - started,
                                    "startup_deadline_seconds": capture_module._CDP_START_TIMEOUT_SECONDS,
                                    "resolver_matches": [
                                        row
                                        for row in identities
                                        if row["path"] == str(executable)
                                    ],
                                    "port": _startup_port_state(command),
                                }
                            )
                except Exception as exc:
                    diagnostic_errors.append(repr(exc))
                return original_os.killpg(pgid, sig)

            # Patch only this owner's module reference, never global Popen.
            proxy = SimpleNamespace(
                **{**vars(original_subprocess), "Popen": diagnostic_popen}
            )
            with monkeypatch.context() as patch:
                patch.setattr(capture_module, "subprocess", proxy)
                patch.setattr(
                    capture_module,
                    "os",
                    SimpleNamespace(
                        **{**vars(original_os), "killpg": diagnostic_killpg}
                    ),
                )
                try:
                    with original_client(executable) as client:
                        yield client
                finally:
                    try:
                        states = [(p.pid, p.poll()) for p in processes]
                        request.node.add_report_section(
                            "call",
                            f"Chrome startup {launch}",
                            f"worker={os.environ.get('PYTEST_XDIST_WORKER', 'main')}; "
                            f"pid/returncode_after_cleanup={states!r}\n"
                            + json.dumps(
                                {
                                    "resolver_observations": identities,
                                    "pre_signal_observations": signal_observations,
                                    "diagnostic_errors": diagnostic_errors,
                                }
                            )
                            + "\n"
                            + _startup_stderr_tail(stderr),
                        )
                    except Exception as exc:
                        # Reporting itself must never replace the primary outcome.
                        diagnostic_errors.append(repr(exc))

    monkeypatch.setattr(capture_module, "_chrome_client", diagnostic_client)


def _controlled_chrome_startup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    partial_at: float | None = None,
    valid_at: float | None = None,
    exit_at: float | None = None,
) -> SimpleNamespace:
    """Exercise the real startup/cleanup owner with no process, socket or sleep."""
    state = SimpleNamespace(
        now=0.0,
        launches=0,
        connects=[],
        calls=[],
        signals=[],
        waits=[],
        returncode=None,
        closes=0,
        profile=tmp_path / "controlled-profile",
    )
    port_file = state.profile / "DevToolsActivePort"

    def publish_port() -> None:
        if valid_at is not None and state.now >= valid_at:
            port_file.write_text("9222\n/devtools/browser/control\n", encoding="utf-8")
        elif partial_at is not None and state.now >= partial_at:
            port_file.write_text("", encoding="utf-8")

    def make_profile(**kwargs) -> str:
        state.profile.mkdir()
        publish_port()
        return str(state.profile)

    def sleep(seconds: float) -> None:
        state.now = round(state.now + seconds, 6)
        publish_port()

    def poll():
        if exit_at is not None and state.now >= exit_at:
            state.returncode = 17
        return state.returncode

    def wait(*, timeout: float):
        state.waits.append(timeout)
        assert state.returncode is not None
        return state.returncode

    def popen(command, **kwargs):
        state.launches += 1
        assert kwargs["start_new_session"] is True
        return SimpleNamespace(pid=4242, poll=poll, wait=wait)

    def killpg(pid: int, sig: int) -> None:
        state.signals.append((pid, sig))
        assert pid == 4242
        state.returncode = -int(sig)

    def connect(host: str, port: int, path: str):
        state.connects.append((host, port, path))
        return object()

    def call(method: str, params=None, *, session_id=None):
        state.calls.append((method, params, session_id))
        return {
            "Target.createTarget": {"targetId": "target"},
            "Target.attachToTarget": {"sessionId": "session"},
        }.get(method, {})

    def close() -> None:
        state.closes += 1

    state.client = SimpleNamespace(call=call, close=close)
    monkeypatch.setattr(
        capture_module,
        "time",
        SimpleNamespace(
            monotonic=lambda: state.now,
            sleep=sleep,
        ),
    )
    monkeypatch.setattr(
        capture_module, "tempfile", SimpleNamespace(mkdtemp=make_profile)
    )
    monkeypatch.setattr(
        capture_module,
        "subprocess",
        SimpleNamespace(
            **{**vars(capture_module.subprocess), "Popen": popen},
        ),
    )
    monkeypatch.setattr(
        capture_module,
        "os",
        SimpleNamespace(
            **{**vars(capture_module.os), "killpg": killpg},
        ),
    )
    monkeypatch.setattr(capture_module._WebSocket, "connect", connect)
    monkeypatch.setattr(capture_module, "_CdpClient", lambda websocket: state.client)
    return state


@pytest.mark.parametrize("partial_at", [None, 10.0])
def test_startup_budget_admits_a_valid_port_after_twenty_seconds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, partial_at: float | None
) -> None:
    state = _controlled_chrome_startup(
        tmp_path,
        monkeypatch,
        partial_at=partial_at,
        valid_at=20.0,
    )
    with capture_module._chrome_client(tmp_path / "fake-chrome") as (client, session):
        assert (client, session) == (state.client, "session")
        assert state.now == 20.0
        assert state.connects == [("127.0.0.1", 9222, "/devtools/browser/control")]
    assert state.launches == 1
    assert state.closes == 1
    assert state.signals == [(4242, capture_module.signal.SIGTERM)]
    assert state.waits == [5]
    assert not state.profile.exists()


@pytest.mark.parametrize("partial_at", [None, 0.0, "late"])
def test_startup_expiry_uses_one_deadline_and_cleans_up(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, partial_at: float | str | None
) -> None:
    budget = capture_module._CDP_START_TIMEOUT_SECONDS
    partial_when = budget - 10.0 if partial_at == "late" else partial_at
    state = _controlled_chrome_startup(tmp_path, monkeypatch, partial_at=partial_when)
    with (
        pytest.raises(
            capture_module.BrowserCaptureError,
            match="Chrome did not publish a usable CDP port",
        ),
        capture_module._chrome_client(tmp_path / "fake-chrome"),
    ):
        pytest.fail("an absent or incomplete port must not provide a CDP client")
    assert state.now == budget
    assert state.launches == 1
    assert state.connects == state.calls == []
    assert state.closes == 0
    assert state.signals == [(4242, capture_module.signal.SIGTERM)]
    assert state.waits == [5]
    assert not state.profile.exists()


def test_startup_process_exit_fails_promptly_without_a_client_and_cleans_up(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = _controlled_chrome_startup(tmp_path, monkeypatch, exit_at=3.0)
    with (
        pytest.raises(
            capture_module.BrowserCaptureError,
            match="Chrome exited before CDP became available",
        ),
        capture_module._chrome_client(tmp_path / "fake-chrome"),
    ):
        pytest.fail("an exited process must not provide a CDP client")
    assert state.now == 3.0
    assert state.returncode == 17
    assert state.launches == 1
    assert state.connects == state.calls == state.signals == state.waits == []
    assert state.closes == 0
    assert not state.profile.exists()


def test_startup_stderr_diagnostics_bound_and_decode_tail() -> None:
    with tempfile.TemporaryFile() as stream:
        stream.write(b"discarded-prefix" + b"x" * 8191 + b"\xff")
        result = _startup_stderr_tail(stream)
    assert "discarded-prefix" not in result
    assert result.endswith("x" * 8191 + "\ufffd")
    assert "stderr_bytes=8208" in result


def test_startup_diagnostics_retain_stderr_without_hiding_launch_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    executable = tmp_path / "exiting-chrome"
    executable.write_text(
        "#!/bin/sh\nprintf 'startup failure control' >&2\nexit 17\n",
        encoding="utf-8",
    )
    executable.chmod(0o700)
    sections = []
    request = SimpleNamespace(
        node=SimpleNamespace(
            name="test_live_chrome_blocks_and_records_a_delayed_outbound_request",
            add_report_section=lambda *section: sections.append(section),
        )
    )
    original_popen = subprocess.Popen
    _live_chrome_startup_diagnostics.__wrapped__(request, monkeypatch)
    with (
        pytest.raises(
            capture_module.BrowserCaptureError,
            match="Chrome exited before CDP became available",
        ),
        capture_module._chrome_client(executable),
    ):
        pytest.fail("an exited process must not provide a CDP client")
    assert subprocess.Popen is original_popen
    assert capture_module._CDP_START_TIMEOUT_SECONDS == 30
    assert len(sections) == 1
    when, title, details = sections[0]
    assert (when, title) == ("call", "Chrome startup 1")
    assert ", 17)]" in details
    assert "stderr_bytes=23" in details
    assert details.endswith("startup failure control")


@pytest.mark.parametrize("xdist_present", [False, True])
def test_live_chrome_grouping_requires_xdist_and_exact_node_ids(
    tmp_path: Path, xdist_present: bool
) -> None:
    """Exercise real collection with strict markers and isolated plugin loading."""
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "conftest.py").write_bytes(
        Path(__file__).with_name("conftest.py").read_bytes()
    )
    names = (
        "test_live_chrome_blocks_and_records_a_delayed_outbound_request",
        "test_live_chrome_replay_terminates_every_profile_writer",
    )
    cases = "import pytest\n" + "\n".join(
        f"def {name}(): pass\n" for name in (*names, names[0] + "_unrelated")
    )
    cases += "\n@pytest.mark.serial_lean\ndef test_lean_probe(): pass\n"
    (tests / "test_browser_capture.py").write_text(cases, encoding="utf-8")
    (tests / "test_other.py").write_text(cases, encoding="utf-8")
    (tmp_path / "pytest.ini").write_text(
        "[pytest]\nmarkers =\n    serial_lean: shared Lean workspace\n",
        encoding="utf-8",
    )
    (tmp_path / "conftest.py").write_text(
        "import json\n"
        "def pytest_collection_finish(session):\n"
        "    rows = {item.nodeid: [mark.args[0] for mark in "
        "item.iter_markers('xdist_group')] for item in session.items}\n"
        "    (session.config.rootpath / 'groups.json').write_text(json.dumps(rows))\n",
        encoding="utf-8",
    )
    command = [sys.executable, "-m", "pytest", "--collect-only", "--strict-markers"]
    if xdist_present:
        command += ["-p", "xdist"]
    environment = {
        key: value
        for key, value in os.environ.items()
        if key not in {"PYTEST_ADDOPTS", "PYTEST_PLUGINS"}
    }
    environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    result = subprocess.run(
        command,
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    groups = json.loads((tmp_path / "groups.json").read_text(encoding="utf-8"))
    expected = {
        f"tests/{filename}::{name}": (
            ["lean"]
            if xdist_present and name == "test_lean_probe"
            else ["live_chrome"]
            if xdist_present and filename == "test_browser_capture.py" and name in names
            else []
        )
        for filename in ("test_browser_capture.py", "test_other.py")
        for name in (*names, names[0] + "_unrelated", "test_lean_probe")
    }
    assert groups == expected


@pytest.mark.parametrize("remove_tryfirst", [False, True])
def test_loadgroup_workers_require_grouping_before_xdist_node_ids(
    tmp_path: Path, remove_tryfirst: bool
) -> None:
    """Real workers accept the hook and reject its ordering mutation.

    Collection alone sees marks even when xdist has already consumed them.
    These controls assert worker node IDs and placement under loadgroup.
    """
    tests = tmp_path / "tests"
    tests.mkdir()
    hook = Path(__file__).with_name("conftest.py").read_text(encoding="utf-8")
    if remove_tryfirst:
        decorator = "@pytest.hookimpl(tryfirst=True)\n"
        assert hook.count(decorator) == 1
        hook = hook.replace(decorator, "")
    (tests / "conftest.py").write_text(hook, encoding="utf-8")
    names = (
        "test_live_chrome_blocks_and_records_a_delayed_outbound_request",
        "test_live_chrome_replay_terminates_every_profile_writer",
    )
    expected = {}
    for filename in ("test_browser_capture.py", "test_other.py"):
        cases = "import pytest\n"
        for name in (*names, names[0] + "_unrelated", "test_lean_probe"):
            group = (
                "lean"
                if name == "test_lean_probe"
                else "live_chrome"
                if filename == "test_browser_capture.py" and name in names
                else ""
            )
            node_id = f"tests/{filename}::{name}"
            expected[node_id] = group
            if group == "lean":
                cases += "@pytest.mark.serial_lean\n"
            runtime_id = node_id + (f"@{group}" if group else "")
            cases += (
                f"def {name}(request):\n"
                f"    assert request.node.nodeid == {runtime_id!r}\n"
            )
        (tests / filename).write_text(cases, encoding="utf-8")
    (tmp_path / "pytest.ini").write_text(
        "[pytest]\nmarkers =\n    serial_lean: shared Lean workspace\n",
        encoding="utf-8",
    )
    (tmp_path / "conftest.py").write_text(
        "import json\n"
        "from pathlib import Path\n"
        "def pytest_runtest_logreport(report):\n"
        "    if report.when == 'call' and hasattr(report, 'worker_id'):\n"
        "        with Path('workers.jsonl').open('a') as stream:\n"
        "            stream.write(json.dumps({'nodeid': report.nodeid, "
        "'worker': report.worker_id, 'outcome': report.outcome}) + '\\n')\n",
        encoding="utf-8",
    )
    environment = {
        key: value
        for key, value in os.environ.items()
        if key not in {"PYTEST_ADDOPTS", "PYTEST_PLUGINS"}
    }
    environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-p",
            "xdist",
            "-n",
            "2",
            "--dist",
            "loadgroup",
            "--strict-markers",
            "-q",
        ],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == int(remove_tryfirst), result.stdout + result.stderr
    rows = [
        json.loads(line)
        for line in (tmp_path / "workers.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert len(rows) == len(expected) == 8
    actual = {row["nodeid"]: row for row in rows}
    for node_id, group in expected.items():
        runtime_id = node_id + (f"@{group}" if group and not remove_tryfirst else "")
        assert actual[runtime_id]["outcome"] == (
            "failed" if group and remove_tryfirst else "passed"
        )
    if not remove_tryfirst:
        for group in ("live_chrome", "lean"):
            grouped = [row for row in rows if row["nodeid"].endswith(f"@{group}")]
            assert len(grouped) == 2
            assert len({row["worker"] for row in grouped}) == 1


def _png_bytes(width: int, height: int, fill: int) -> bytes:
    def chunk(kind: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload))
            + kind
            + payload
            + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
        )

    rows = b"".join(b"\0" + bytes((fill,)) * width for _ in range(height))
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(rows, level=9))
        + chunk(b"IEND", b"")
    )


def test_canonical_render_configuration_names_every_normalized_pixel_input() -> None:
    assert capture_module.canonical_browser_render_configuration() == {
        "browser_locale": "en-US",
        "color_profile": "srgb",
        "device_scale_factor": "1",
        "font_render_hinting": "none",
        "gpu": "disabled",
        "process_locale": "C.UTF-8",
        "timezone": "UTC",
    }


def _stubbed_capture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> capture_module.BrowserReplay:
    source_root = Path(__file__).resolve().parents[1]
    for relative in (
        "src/fep_lean/output/browser_capture.py",
        "scripts/capture_browser_acceptance.py",
    ):
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((source_root / relative).read_bytes())
    counts = {
        "topics": 155,
        "families": 20,
        "witnesses": 15,
        "relations": 133,
        "capabilities": 48,
    }
    for key, relative in capture_module.CANONICAL_BROWSER_PROJECTIONS.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"{key}\n", encoding="utf-8")
    screenshots = {
        role: _png_bytes(
            390 if role.endswith("_mobile") else 1440,
            844 if role.endswith("_mobile") else 900,
            index + 1,
        )
        for index, role in enumerate(capture_module.CANONICAL_BROWSER_SCREENSHOTS)
    }
    browser_executable = tmp_path / "fixture-chrome"
    browser_executable.write_bytes(b"fixture Chrome binary\n")
    replay = capture_module.BrowserReplay(
        browser={
            "name": "Google Chrome",
            "version": "151.0.7922.169",
            "executable_path": str(browser_executable.resolve()),
            "executable_sha256": hashlib.sha256(
                browser_executable.read_bytes()
            ).hexdigest(),
        },
        render_configuration=capture_module.canonical_browser_render_configuration(),
        render_environment={
            "browser_locale": "en-US",
            "device_pixel_ratio": "1",
            "platform": "Linux x86_64",
            "timezone": "UTC",
            "webgl_renderer": "WebKit WebGL",
            "webgl_vendor": "WebKit",
        },
        observations=capture_module.canonical_browser_observations(counts),
        interactions={
            key: True for key in capture_module.REQUIRED_BROWSER_INTERACTIONS
        },
        screenshot_bytes=screenshots,
    )
    monkeypatch.setattr(capture_module, "_project_counts", lambda _root: counts)
    monkeypatch.setattr(
        capture_module,
        "replay_browser_acceptance",
        lambda *_args, **_kwargs: replay,
    )
    return replay


def test_canonical_dom_passes_the_interaction_summary() -> None:
    root = Path(__file__).resolve().parents[1]
    counts = capture_module._project_counts(root)
    observations = capture_module.canonical_browser_observations(counts)
    presentation = capture_module.build_formalism_presentation(root)
    assert observations["atlas"]["pairingVisible"] == sum(
        relation.kind == "formal_pairing" for relation in presentation.relations
    )
    assert observations["atlas"]["pairingVisible"] == 118
    assert all(capture_module._interactions(observations).values())
    stale = deepcopy(observations)
    stale["atlas"]["pairingVisible"] = 119
    assert not capture_module._interactions(stale)["search_and_filter"]


@pytest.mark.parametrize("pairings", [0, 105, 117, 118, 120, 146])
def test_interactions_reject_incorrect_pairing_counts(
    pairings: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Preserve these six historical 119-contract refusals and their exact IDs.
    # The canonical test above separately pins current 118 and refuses stale 119.
    monkeypatch.setattr(capture_module, "REVIEWED_ATLAS_PAIRINGS", 119)
    root = Path(__file__).resolve().parents[1]
    observations = capture_module.canonical_browser_observations(
        capture_module._project_counts(root)
    )
    observations["atlas"]["pairingVisible"] = pairings
    assert not capture_module._interactions(observations)["search_and_filter"]


@pytest.mark.parametrize(
    ("section", "field", "value"),
    [
        ("atlas", "pairingVisible", 105),
        ("atlas", "escapePreservedFilters", False),
        ("atlas", "outsideEscapePreservedFilters", False),
        ("atlas", "clearAllResetFilters", False),
        ("dashboard", "escapePreservedFilters", False),
        ("dashboard", "outsideEscapePreservedFilters", False),
        ("dashboard", "clearAllResetFilters", False),
        ("dashboard_mobile", "compactDefaultHeight", False),
        ("dashboard_mobile", "clearAllResetFilters", False),
        ("dashboard_mobile", "escapeCleared", False),
        ("dashboard_mobile", "escapePreservedFilters", False),
        ("dashboard_mobile", "outsideEscapePreservedFilters", False),
        ("dashboard_mobile", "recordCollectionInitiallyOpen", True),
    ],
)
def test_capture_rejects_noncanonical_dom_without_replacing_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    section: str,
    field: str,
    value: int | bool,
) -> None:
    replay = _stubbed_capture(tmp_path, monkeypatch)
    # Even an all-accepted interaction summary cannot override the exact DOM gate.
    replay.observations[section][field] = value
    paths = [
        tmp_path / capture_module.BROWSER_RECEIPT,
        *(tmp_path / p for p in capture_module.CANONICAL_BROWSER_SCREENSHOTS.values()),
    ]
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"historical evidence\n")
    before = {path: path.read_bytes() for path in paths}
    with pytest.raises(
        capture_module.BrowserCaptureError, match="DOM observations are not canonical"
    ) as failure:
        capture_module.capture_browser_acceptance(tmp_path)
    assert f"{section}.{field}: expected " in str(failure.value)
    assert f"observed {value!r}" in str(failure.value)
    assert {path: path.read_bytes() for path in paths} == before


def test_dom_rejection_identifies_missing_fields_without_logging_page_content(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    replay = _stubbed_capture(tmp_path, monkeypatch)
    del replay.observations["atlas"]["topics"]
    replay.observations["external_requests"] = ["https://example.test/private-token"]
    replay.observations["private-page-text"] = "private value"
    with pytest.raises(capture_module.BrowserCaptureError) as failure:
        capture_module.build_browser_receipt(tmp_path, replay)
    message = str(failure.value)
    assert "atlas.topics: missing (expected 155)" in message
    assert (
        "external_requests: expected list(length=0), observed list(length=1)" in message
    )
    assert "root: 1 unexpected field(s)" in message
    assert "private" not in message
    assert not (tmp_path / capture_module.BROWSER_RECEIPT).exists()


def test_dom_rejection_bounds_the_difference_inventory() -> None:
    expected = {f"field{index:02}": True for index in range(20)}
    observed = dict.fromkeys(expected, False)
    message = capture_module._dom_difference_summary(expected, observed)
    assert "field00: expected True, observed False" in message
    assert "field15: expected True, observed False" in message
    assert "field16" not in message
    assert message.endswith("4 additional difference(s)")


def test_capture_command_emits_source_bound_receipt_and_exact_screenshot_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    replay = _stubbed_capture(tmp_path, monkeypatch)

    receipt_path = capture_module.capture_browser_acceptance(tmp_path)
    payload = json.loads(receipt_path.read_text(encoding="utf-8"))

    owner = tmp_path / "src/fep_lean/output/browser_capture.py"
    wrapper = tmp_path / "scripts/capture_browser_acceptance.py"
    assert payload["capture"] == {
        "command": "uv run python scripts/capture_browser_acceptance.py",
        "owner": owner.relative_to(tmp_path).as_posix(),
        "owner_sha256": hashlib.sha256(owner.read_bytes()).hexdigest(),
        "protocol": "Chrome DevTools Protocol",
        "wrapper": wrapper.relative_to(tmp_path).as_posix(),
        "wrapper_sha256": hashlib.sha256(wrapper.read_bytes()).hexdigest(),
    }
    assert payload["schema_version"] == 4
    assert payload["browser"]["executable_path"] == str(
        (tmp_path / "fixture-chrome").resolve()
    )
    assert payload["render_configuration"] == (
        capture_module.canonical_browser_render_configuration()
    )
    assert payload["render_environment"] == replay.render_environment
    for role, relative in capture_module.CANONICAL_BROWSER_SCREENSHOTS.items():
        assert (tmp_path / relative).read_bytes() == replay.screenshot_bytes[role]


@pytest.mark.parametrize(
    "interruption",
    [
        OSError("injected browser install failure"),
        KeyboardInterrupt("injected browser install interruption"),
    ],
)
def test_capture_install_rolls_back_existing_and_absent_destinations(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    interruption: BaseException,
) -> None:
    _stubbed_capture(tmp_path, monkeypatch)
    destinations = [
        *(
            tmp_path / relative
            for relative in capture_module.CANONICAL_BROWSER_SCREENSHOTS.values()
        ),
        tmp_path / capture_module.BROWSER_RECEIPT,
    ]
    before: dict[Path, bytes | None] = {}
    for index, destination in enumerate(destinations):
        if index % 2 == 0:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(f"old-{index}".encode())
            before[destination] = destination.read_bytes()
        else:
            before[destination] = None
    real_replace = os.replace
    call_count = 0
    fail_at = sum(value is not None for value in before.values()) + 3

    def fail_once(source: Path, destination: Path) -> None:
        nonlocal call_count
        call_count += 1
        if call_count == fail_at:
            raise interruption
        real_replace(source, destination)

    monkeypatch.setattr(capture_module.os, "replace", fail_once)

    with pytest.raises(type(interruption), match="injected browser install"):
        capture_module.capture_browser_acceptance(tmp_path)

    for destination, expected in before.items():
        if expected is None:
            assert not destination.exists()
        else:
            assert destination.read_bytes() == expected


def test_capture_preserves_and_reports_backups_after_incomplete_rollback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stubbed_capture(tmp_path, monkeypatch)
    destinations = [
        *(
            tmp_path / relative
            for relative in capture_module.CANONICAL_BROWSER_SCREENSHOTS.values()
        ),
        tmp_path / capture_module.BROWSER_RECEIPT,
    ]
    for index, destination in enumerate(destinations):
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(f"old-{index}".encode())
    real_replace = capture_module.os.replace

    def fail_install_and_restore(source: Path, destination: Path) -> None:
        source_path = Path(source)
        if (
            source_path.name == "atlas-155-mobile.png"
            and source_path.parent.name.startswith(".browser-capture-")
        ):
            raise OSError("injected browser install failure")
        if source_path.parent.name == "backups" and source_path.name.startswith("01-"):
            raise OSError("injected browser restore failure")
        real_replace(source, destination)

    monkeypatch.setattr(os, "replace", fail_install_and_restore)

    with pytest.raises(
        capture_module.BrowserCaptureError,
        match="recovery files retained at",
    ) as captured:
        capture_module.capture_browser_acceptance(tmp_path)

    recovery = Path(str(captured.value).rsplit("recovery files retained at ", 1)[1])
    assert recovery.is_dir()
    assert (recovery / "backups" / "01-atlas-155-mobile.png").read_bytes() == b"old-1"


def test_replay_rejects_a_symlinked_projection_parent_before_browser_launch(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    project = tmp_path_factory.mktemp("browser-project")
    external_docs = tmp_path_factory.mktemp("external-docs")
    (external_docs / "formalism-atlas.html").write_text("external\n", encoding="utf-8")
    (project / "docs").symlink_to(external_docs, target_is_directory=True)

    with pytest.raises(
        capture_module.BrowserCaptureError,
        match="projection path traverses a symlink",
    ):
        capture_module.replay_browser_acceptance(project)


def test_replay_rejects_a_projection_path_that_lexically_escapes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        capture_module,
        "CANONICAL_BROWSER_PROJECTIONS",
        {"atlas_html": "../external/formalism-atlas.html"},
    )

    with pytest.raises(
        capture_module.BrowserCaptureError,
        match="projection path escapes the project root",
    ):
        capture_module.replay_browser_acceptance(tmp_path)


def test_capture_rejects_a_symlinked_specs_ancestor_without_external_writes(
    tmp_path_factory: pytest.TempPathFactory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = tmp_path_factory.mktemp("capture-project")
    external_specs = tmp_path_factory.mktemp("external-specs")
    _stubbed_capture(project, monkeypatch)
    (project / "specs").mkdir()
    (project / "specs/done").symlink_to(external_specs, target_is_directory=True)

    with pytest.raises(
        capture_module.BrowserCaptureError,
        match="asset path traverses a symlink",
    ):
        capture_module.capture_browser_acceptance(project)

    assert list(external_specs.iterdir()) == []


@pytest.mark.parametrize(
    "relative",
    (capture_module.CAPTURE_OWNER, capture_module.CAPTURE_WRAPPER),
)
def test_capture_rejects_symlinked_capture_provenance_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    relative: str,
) -> None:
    _stubbed_capture(tmp_path, monkeypatch)
    external = tmp_path / "external-capture-owner.py"
    external.write_text("external owner\n", encoding="utf-8")
    path = tmp_path / relative
    path.unlink()
    path.symlink_to(external)

    with pytest.raises(
        capture_module.BrowserCaptureError,
        match="capture provenance path traverses a symlink",
    ):
        capture_module.capture_browser_acceptance(tmp_path)


def test_receipt_rejects_a_long_delay_network_api_even_with_a_stubbed_replay(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _stubbed_capture(tmp_path, monkeypatch)
    (tmp_path / "docs/formalism-atlas.html").write_text(
        "<script>setTimeout(() => fetch('https://example.invalid'), 60000)</script>",
        encoding="utf-8",
    )

    with pytest.raises(
        capture_module.BrowserCaptureError,
        match="network-capable browser API",
    ):
        capture_module.capture_browser_acceptance(tmp_path)


def test_receipt_rejects_a_noncanonical_declared_render_configuration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    replay = _stubbed_capture(tmp_path, monkeypatch)
    tampered = replace(
        replay,
        render_configuration={**replay.render_configuration, "gpu": "enabled"},
    )

    with pytest.raises(
        capture_module.BrowserCaptureError,
        match="render configuration is not canonical",
    ):
        capture_module.build_browser_receipt(tmp_path, tampered)


def test_receipt_rejects_an_incomplete_observed_render_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    replay = _stubbed_capture(tmp_path, monkeypatch)
    tampered = replace(
        replay,
        render_environment={
            key: value
            for key, value in replay.render_environment.items()
            if key != "platform"
        },
    )

    with pytest.raises(
        capture_module.BrowserCaptureError,
        match="render environment is incomplete",
    ):
        capture_module.build_browser_receipt(tmp_path, tampered)


@pytest.mark.parametrize(
    "version_output",
    ("Brave Browser 123.4.5.6", "Chromium 123.4.5.6 Brave"),
)
def test_browser_resolution_rejects_an_unsupported_product(
    tmp_path: Path, version_output: str
) -> None:
    executable = tmp_path / "brave-like"
    executable.write_text(
        f'#!/bin/sh\nprintf "{version_output}\\n"\n',
        encoding="utf-8",
    )
    executable.chmod(0o755)

    with pytest.raises(
        capture_module.BrowserCaptureError,
        match="supported Chrome or Chromium product",
    ):
        capture_module.resolve_browser_executable(executable=executable)


def test_cdp_product_must_corroborate_the_resolved_browser_version() -> None:
    class FakeClient:
        def call(self, method: str) -> dict[str, str]:
            assert method == "Browser.getVersion"
            return {"product": "Chrome/124.0.0.1"}

    with pytest.raises(
        capture_module.BrowserCaptureError,
        match="CDP product version differs",
    ):
        capture_module._validate_cdp_browser_identity(
            FakeClient(),
            browser_name="Google Chrome",
            version="123.0.0.1",
        )


def _resolvable_browser() -> bool:
    """True when the capture module resolves a supported browser itself."""
    try:
        capture_module.resolve_browser_executable()
    except capture_module.BrowserCaptureError:
        return False
    return True


_BROWSER_RESOLVABLE = _resolvable_browser()


@pytest.mark.skipif(
    not _BROWSER_RESOLVABLE,
    reason=(
        "capture_module.resolve_browser_executable() cannot resolve a "
        "supported Chrome/Chromium executable on this host"
    ),
)
def test_live_chrome_blocks_and_records_a_delayed_outbound_request(
    tmp_path: Path,
) -> None:
    page = tmp_path / "delayed-network.html"
    page.write_text(
        "<script>setTimeout(() => fetch("
        "'https://example.invalid/delayed-resource'), 1000)</script>",
        encoding="utf-8",
    )
    executable = capture_module.resolve_browser_executable()[1]

    with (
        capture_module._chrome_client(executable) as (client, session_id),
        pytest.raises(
            capture_module.BrowserCaptureError,
            match="network-capable browser API",
        ),
    ):
        capture_module._navigate(client, session_id, page)


@pytest.mark.skipif(
    not _BROWSER_RESOLVABLE,
    reason=(
        "capture_module.resolve_browser_executable() cannot resolve a "
        "supported Chrome/Chromium executable on this host"
    ),
)
def test_live_chrome_replay_terminates_every_profile_writer(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch
) -> None:
    project_root = Path(__file__).resolve().parents[1]
    original = capture_module._dashboard_observations
    mobile_layouts = []

    def measured_dashboard(client, session_id, *, mobile):
        if mobile:
            layout = capture_module._evaluate(
                client,
                session_id,
                """(() => ({
                  viewport:[innerWidth,innerHeight],
                  scrollHeight:document.documentElement.scrollHeight,
                  summaryHeights:[...document.querySelectorAll(
                    '.mobile-plot-group>summary')].map(
                      summary=>summary.getBoundingClientRect().height)
                }))()""",
            )
            mobile_layouts.append(layout)
            request.node.add_report_section(
                "call", "Mobile default layout", json.dumps(layout, sort_keys=True)
            )
        return original(client, session_id, mobile=mobile)

    monkeypatch.setattr(capture_module, "_dashboard_observations", measured_dashboard)

    first = capture_module.replay_browser_acceptance(project_root)
    second = capture_module.replay_browser_acceptance(project_root)

    browser_path = Path(first.browser["executable_path"])
    assert browser_path.is_absolute()
    assert browser_path.is_file()
    assert (
        hashlib.sha256(browser_path.read_bytes()).hexdigest()
        == first.browser["executable_sha256"]
    )
    assert first.render_configuration == (
        capture_module.canonical_browser_render_configuration()
    )
    assert first.render_environment == second.render_environment
    assert first.render_environment["browser_locale"] == "en-US"
    assert first.render_environment["timezone"] == "UTC"
    assert first.render_environment["device_pixel_ratio"] == "1"
    assert first.render_environment["platform"]
    assert first.render_environment["webgl_renderer"]
    assert first.render_environment["webgl_vendor"]
    assert first.observations == second.observations
    expected = capture_module.canonical_browser_observations(
        capture_module._project_counts(project_root)
    )
    assert first.observations == expected
    assert all(first.interactions.values())
    assert first.interactions == second.interactions
    # Validate the actual replay without publishing a production capture.
    assert capture_module.build_browser_receipt(project_root, first)
    assert capture_module.build_browser_receipt(project_root, second)
    assert len(mobile_layouts) == 2
    for layout in mobile_layouts:
        assert layout["viewport"] == [390, 844]
        assert layout["scrollHeight"] <= 2 * layout["viewport"][1]
        assert len(layout["summaryHeights"]) == 8
        assert min(layout["summaryHeights"]) >= 44
    assert (
        first.observations["dashboard_mobile"]["mobileOverviewInitiallyOpen"] is False
    )
    assert (
        first.observations["dashboard_mobile"]["mobileOverviewDisclosureVisible"]
        is True
    )
    assert first.screenshot_bytes == second.screenshot_bytes


def _keyboard_policy_states():
    filters = [{"id": "family", "value": "chosen"}, {"id": "status", "value": ""}]
    before = {"text": "keyboard-scope-control", "focused": "clear", "filters": filters}
    after = {"text": "", "focused": "search", "filters": deepcopy(filters)}
    reset = {
        "text": "",
        "focused": "clear",
        "filters": [{"id": "family", "value": ""}, {"id": "status", "value": ""}],
    }
    return [deepcopy(before), deepcopy(before), after, reset]


def _run_keyboard_policy(monkeypatch, states):
    snapshots = iter(states)
    keys = []

    def evaluate(_client, _session, expression):
        return next(snapshots) if "filters:" in expression else True

    monkeypatch.setattr(capture_module, "_evaluate", evaluate)
    monkeypatch.setattr(
        capture_module, "_press_key", lambda _c, _s, key: keys.append(key)
    )
    result = capture_module._explorer_keyboard_reset_observations(
        object(),
        "session",
        search_id="search",
        clear_id="clear",
        filter_ids=("family", "status"),
    )
    assert keys == ["Escape", "Escape"]
    return result


def test_keyboard_policy_observes_preservation_focus_and_explicit_reset(monkeypatch):
    assert _run_keyboard_policy(monkeypatch, _keyboard_policy_states()) == {
        "escapeCleared": True,
        "escapePreservedFilters": True,
        "outsideEscapePreservedFilters": True,
        "clearAllResetFilters": True,
    }


@pytest.mark.parametrize("stage", [0, 1, 2, 3])
def test_keyboard_policy_rejects_missing_snapshot_at_every_stage(monkeypatch, stage):
    states = _keyboard_policy_states()
    states[stage] = {}
    with pytest.raises(capture_module.BrowserCaptureError, match="snapshot shape"):
        _run_keyboard_policy(monkeypatch, states)


@pytest.mark.parametrize(
    "corruption",
    ["empty", "missing", "reordered", "extra", "nonstring-value", "nonstring-text"],
)
def test_keyboard_policy_rejects_malformed_or_missing_controls(monkeypatch, corruption):
    states = _keyboard_policy_states()
    before = states[0]
    if corruption == "empty":
        before["filters"] = []
    elif corruption == "missing":
        before["filters"].pop()
    elif corruption == "reordered":
        before["filters"].reverse()
    elif corruption == "extra":
        before["filters"].append({"id": "extra", "value": ""})
    elif corruption == "nonstring-value":
        before["filters"][0]["value"] = 0
    else:
        before["text"] = None
    with pytest.raises(
        capture_module.BrowserCaptureError, match="cardinality|types|identities|values"
    ):
        _run_keyboard_policy(monkeypatch, states)


@pytest.mark.parametrize(
    ("stage", "field"),
    [
        (1, "outsideEscapePreservedFilters"),
        (2, "escapeCleared"),
        (3, "clearAllResetFilters"),
    ],
)
def test_keyboard_policy_rejects_focus_theft(monkeypatch, stage, field):
    states = _keyboard_policy_states()
    states[stage]["focused"] = "unrelated"
    assert _run_keyboard_policy(monkeypatch, states)[field] is False


def test_keyboard_policy_rejects_noop_clear(monkeypatch):
    states = _keyboard_policy_states()
    states[3]["filters"][0]["value"] = "chosen"
    assert _run_keyboard_policy(monkeypatch, states)["clearAllResetFilters"] is False
