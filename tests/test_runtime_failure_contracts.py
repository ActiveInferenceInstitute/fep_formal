"""Observable persistence and subprocess failures preserve their public contracts."""

from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
import threading
import time
from contextlib import closing
from pathlib import Path
from typing import Any

import pytest

from fep_formal.gauss import cli as gauss_cli
from fep_formal.gauss.client import OpenGaussClient, resolve_gauss_home
from fep_formal.verification import _subprocess, environment


def test_failed_artifact_registration_leaves_no_published_file(tmp_path: Path) -> None:
    home = tmp_path / "nested" / "gauss"
    with OpenGaussClient(gauss_home=home) as store:
        session = store.create_session("fep-001", "FEP")
        with closing(sqlite3.connect(home / "fep_lean_state.db")) as db, db:
            db.execute(
                "CREATE TRIGGER reject_artifact BEFORE INSERT ON artifacts "
                "BEGIN SELECT RAISE(FAIL, 'registration unavailable'); END"
            )
        with pytest.raises(sqlite3.IntegrityError, match="registration unavailable"):
            store.write_artifact(session, {"claim": "unregistered"})
        assert list((home / "fep_artifacts").iterdir()) == []
        with closing(sqlite3.connect(home / "fep_lean_state.db")) as db:
            assert db.execute("SELECT count(*) FROM artifacts").fetchone() == (0,)
        assert store.export_session(session)["topic_id"] == "fep-001"


@pytest.mark.parametrize("payload", ["[]", '"plain text"', "null", "42"])
def test_non_object_cache_entries_are_misses(tmp_path: Path, payload: str) -> None:
    with OpenGaussClient(gauss_home=tmp_path / "gauss") as store:
        store.set_cached_hermes("key", "fep-001", "explain", "local", payload, "hash")
        assert store.get_cached_hermes("key") is None
        store.set_cached_hermes(
            "key", "fep-001", "explain", "local", '{"ok":true}', "hash"
        )
        assert store.get_cached_hermes("key") == {"ok": True}


@pytest.mark.parametrize(
    "settings", ["{unterminated", "- unexpected", "gauss: [unexpected]"]
)
def test_malformed_home_configuration_cannot_override_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, settings: str
) -> None:
    monkeypatch.delenv("GAUSS_HOME", raising=False)
    config = tmp_path / "config"
    config.mkdir()
    (config / "settings.yaml").write_text(settings)
    assert resolve_gauss_home(tmp_path) is None


def test_unsafe_topic_id_does_not_create_session(tmp_path: Path) -> None:
    with OpenGaussClient(gauss_home=tmp_path / "gauss") as store:
        with pytest.raises(ValueError, match="unsafe characters"):
            store.create_session("../../outside", "FEP")
        assert store.export_all_sessions() == []


def test_communicate_deadline_kills_group_when_watchdog_is_delayed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The main timeout path must work even if its backstop cannot be scheduled."""
    # This probe instruments the local broker. An inherited cooperative lease
    # would route signals to the outer broker, outside these monkeypatches.
    monkeypatch.delenv(_subprocess._SOCKET_ENV, raising=False)
    monkeypatch.delenv(_subprocess._TOKEN_ENV, raising=False)
    callbacks: list[Any] = []
    kills: list[int] = []
    kill_group = _subprocess.os.killpg

    class DelayedThread:
        def __init__(self, *, target: Any, daemon: bool) -> None:
            callbacks.append(target)

        def start(self) -> None:
            pass

        def join(self, timeout: float | None = None) -> None:
            for callback in callbacks:
                callback()

        def is_alive(self) -> bool:
            return False

    def record_kill(group: int, sig: int) -> None:
        kills.append(group)
        kill_group(group, sig)

    monkeypatch.setattr(threading, "Thread", DelayedThread)
    monkeypatch.setattr(_subprocess.os, "killpg", record_kill)
    child = "import time; time.sleep(30)"
    parent = (
        "import subprocess,sys,time; "
        f"subprocess.Popen([sys.executable,'-c',{child!r}]); "
        "print('started',flush=True); time.sleep(30)"
    )
    started = time.monotonic()
    with pytest.raises(subprocess.TimeoutExpired) as error:
        _subprocess.run_process_group(
            [sys.executable, "-c", parent], cwd=tmp_path, timeout=0.5
        )
    assert error.value.timeout == 0.5
    assert len(kills) == 1
    assert time.monotonic() - started < 10, "descendants must not retain the pipes"


def test_nonzero_exit_preserves_command_and_return_code(tmp_path: Path) -> None:
    command = [sys.executable, "-c", "raise SystemExit(7)"]
    with pytest.raises(subprocess.CalledProcessError) as error:
        _subprocess.run_process_group(command, cwd=tmp_path, timeout=None, check=True)
    assert error.value.returncode == 7
    assert error.value.cmd == command


def test_uncaptured_unlimited_process_inherits_output(
    tmp_path: Path, capfd: pytest.CaptureFixture[str]
) -> None:
    result = _subprocess.run_process_group(
        [sys.executable, "-c", "print('probe finished')"],
        cwd=tmp_path,
        timeout=None,
        capture=False,
        check=True,
    )
    assert result.returncode == 0
    assert result.stdout is None and result.stderr is None
    assert capfd.readouterr().out == "probe finished\n"


@pytest.mark.skipif(os.name != "posix", reason="process-group probes require POSIX")
@pytest.mark.parametrize("probe", ["gauss_required", "gauss_optional", "version"])
def test_capability_probe_deadline_kills_real_child_and_grandchild(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, probe: str
) -> None:
    """Capability commands cannot leave descendants retaining pipes."""
    child_pid = tmp_path / "child.pid"
    parent_pid = tmp_path / "parent.pid"
    child = (
        "import os,time; from pathlib import Path; "
        f"Path({str(child_pid)!r}).write_text(str(os.getpid())); time.sleep(30)"
    )
    executable = tmp_path / "probe"
    executable.write_text(
        f"#!{sys.executable} -S\n"
        "import os,subprocess,sys,time\nfrom pathlib import Path\n"
        f"Path({str(parent_pid)!r}).write_text(str(os.getpid()))\n"
        f"subprocess.Popen([sys.executable, '-S', '-c', {child!r}])\n"
        "ready_deadline = time.monotonic() + 2\n"
        f"while not Path({str(child_pid)!r}).exists() and time.monotonic() < ready_deadline: time.sleep(.005)\n"
        f"if not Path({str(child_pid)!r}).exists(): raise RuntimeError('grandchild did not reach readiness')\n"
        "print('probe started', flush=True)\ntime.sleep(30)\n"
    )
    executable.chmod(0o755)
    # The product deadline remains call-relative. These stdlib-only fixtures
    # permit bounded real startup under concurrent native compilation before
    # testing cancellation; absent sentinels never count as stopped children.
    probe_budget = 3.0
    monkeypatch.setattr(gauss_cli, "_CLI_TIMEOUT_S", probe_budget)
    monkeypatch.setattr(environment, "_VERSION_TIMEOUT_S", probe_budget)
    monkeypatch.setattr(gauss_cli.shutil, "which", lambda _name: str(executable))

    def state(pid: int) -> str:
        return subprocess.run(
            ["/bin/ps", "-o", "stat=", "-p", str(pid)],
            capture_output=True,
            text=True,
            timeout=1,
            check=False,
        ).stdout.strip()

    try:
        started = time.monotonic()
        if probe == "version":
            ok, message = environment._version_line(str(executable), tmp_path)
        else:
            ok, message = gauss_cli.check_gauss_cli(
                tmp_path, require=probe == "gauss_required"
            )
        assert time.monotonic() - started < probe_budget + 2, (
            "descendants retained probe pipes beyond budget and bounded drain"
        )
        assert ok is (probe == "gauss_optional")
        assert "timed out" in message
        # Both real generations ran. A transient zombie counts as stopped;
        # init may reap it after the parent has been killed with its group.
        for path in (parent_pid, child_pid):
            assert path.exists(), f"{probe} never reached real readiness: {path.name}"
            pid = int(path.read_text())
            current = state(pid)
            assert not current or current.startswith("Z"), (
                f"{probe} left PID {pid} running: {current}"
            )
    finally:
        for path in (parent_pid, child_pid):
            if path.exists():
                pid = int(path.read_text())
                current = state(pid)
                if current and not current.startswith("Z"):
                    os.kill(pid, 9)
