"""The timeout backstop kills live probes and cancels after normal completion."""

from __future__ import annotations

import contextlib
import json
import os
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from fep_formal.verification import _subprocess
from tests._support import lean_runner


@pytest.mark.parametrize("route", ["broker", "lease", "direct"])
@pytest.mark.parametrize(
    "timeout",
    [0, -1, True, False, float("inf"), float("-inf"), float("nan"), "1", 10**400],
)
def test_invalid_process_timeout_refuses_allocation_and_dispatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, route: str, timeout: Any
) -> None:
    environment = (
        {
            _subprocess._SOCKET_ENV: "synthetic-socket",
            _subprocess._TOKEN_ENV: "synthetic-token",
        }
        if route == "lease"
        else {}
    )
    monkeypatch.setattr(
        _subprocess,
        "os",
        SimpleNamespace(
            name="nt" if route == "direct" else "posix", environ=environment
        ),
    )

    def unexpected(*args: Any, **kwargs: Any) -> Any:
        pytest.fail("malformed timeout allocated a broker, channel or process")

    monkeypatch.setattr(_subprocess, "_Broker", unexpected)
    monkeypatch.setattr(_subprocess, "_remote", unexpected)
    monkeypatch.setattr(_subprocess.subprocess, "Popen", unexpected)
    with pytest.raises(ValueError, match="None or finite and positive"):
        _subprocess.run_process_group(
            ["must-not-launch"], cwd=tmp_path, timeout=timeout
        )


@pytest.mark.parametrize("route", ["broker", "lease", "direct"])
@pytest.mark.parametrize("timeout", [None, 0.5, 2])
def test_valid_process_timeout_preserves_each_dispatch_contract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, route: str, timeout: float | None
) -> None:
    environment = (
        {
            _subprocess._SOCKET_ENV: "synthetic-socket",
            _subprocess._TOKEN_ENV: "synthetic-token",
        }
        if route == "lease"
        else {}
    )
    monkeypatch.setattr(
        _subprocess,
        "os",
        SimpleNamespace(
            name="nt" if route == "direct" else "posix", environ=environment
        ),
    )
    calls: list[tuple[str, float | None]] = []

    def completed(*args: Any, **kwargs: Any) -> Any:
        calls.append(("lease", kwargs["timeout"]))
        return subprocess.CompletedProcess(["accepted"], 0, "accepted", "")

    class Broker:
        def run(self, *args: Any, **kwargs: Any) -> Any:
            calls.append(("broker", kwargs["timeout"]))
            return subprocess.CompletedProcess(["accepted"], 0, "accepted", "")

        def close(self) -> None:
            pass

    class Process:
        returncode = 0
        stdout = stderr = None

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def communicate(self, *, timeout: float | None) -> tuple[str, str]:
            calls.append(("direct", timeout))
            return "accepted", ""

    monkeypatch.setattr(_subprocess, "_Broker", Broker)
    monkeypatch.setattr(_subprocess, "_remote", completed)
    monkeypatch.setattr(_subprocess.subprocess, "Popen", Process)
    assert (
        _subprocess.run_process_group(
            ["accepted"], cwd=tmp_path, timeout=timeout
        ).stdout
        == "accepted"
    )
    assert calls == [(route, timeout)]


@pytest.mark.parametrize("timeout", [0, -1, True, 10**400])
def test_authenticated_broker_rejects_invalid_timeout_before_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, timeout: Any
) -> None:
    import threading

    class Connection:
        def settimeout(self, timeout: float) -> None:
            pass

        def close(self) -> None:
            pass

    connection = Connection()
    descriptor = os.open(os.devnull, os.O_RDONLY)
    broker = object.__new__(_subprocess._Broker)
    broker.token = "synthetic-authenticated-token"
    broker.lock = threading.Lock()
    broker.connections = {connection}
    broker.workers = set()
    request = {
        "token": broker.token,
        "command": ["must-not-launch"],
        "cwd": str(tmp_path),
        "env": {},
        "timeout": timeout,
        "capture": True,
    }
    responses: list[dict[str, Any]] = []

    def unexpected(*args: Any, **kwargs: Any) -> Any:
        pytest.fail("authenticated invalid budget reached broker.run")

    monkeypatch.setattr(broker, "run", unexpected)
    monkeypatch.setattr(
        _subprocess.socket,
        "recv_fds",
        lambda *args: (b"", [descriptor], 0, None),
        raising=False,
    )
    monkeypatch.setattr(_subprocess, "_read_frame", lambda *args: request)
    monkeypatch.setattr(
        _subprocess, "_send_frame", lambda channel, value: responses.append(value)
    )
    broker._request(connection)
    assert responses == [
        {"kind": "error", "error": "invalid process supervision request"}
    ]
    assert not broker.connections


def _synthetic_scope_broker() -> tuple[Any, Any]:
    class Channel:
        closed = False

        def shutdown(self, how: int) -> None:
            pass

        def close(self) -> None:
            self.closed = True

    broker = object.__new__(_subprocess._Broker)
    broker.token = "a" * 64
    broker.lock = threading.RLock()
    broker.closed = False
    parent = _subprocess._Group(
        SimpleNamespace(pid=12345),
        Channel(),
        scope_token="b" * 64,
        parent=None,
    )
    broker.groups = {parent}
    broker.scopes = {parent.scope_token: parent}
    broker.issued_tokens = {broker.token, parent.scope_token, "c" * 64}
    return broker, parent


@pytest.mark.parametrize(
    "scope", ["active", "broker-wide", "unknown", "revoked", "replayed", "late"]
)
def test_broker_authenticates_only_a_live_scope_before_child_allocation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, scope: str
) -> None:
    class Connection:
        closed = False

        def settimeout(self, timeout: float) -> None:
            pass

        def close(self) -> None:
            self.closed = True

    broker, parent = _synthetic_scope_broker()
    token = parent.scope_token
    if scope == "broker-wide":
        token = broker.token
    elif scope == "unknown":
        token = "d" * 64
    elif scope == "revoked":
        broker.groups.remove(parent)
    elif scope == "replayed":
        broker.groups.remove(parent)
        broker.scopes.clear()
    connection = Connection()
    broker.connections = {connection}
    broker.workers = set()
    descriptor = os.open(os.devnull, os.O_RDONLY)
    request = {
        "token": token,
        "command": ["must-not-launch"],
        "cwd": str(tmp_path),
        "env": {},
        "timeout": 1,
        "capture": True,
    }
    responses: list[dict[str, Any]] = []
    calls: list[Any] = []

    def unexpected(*args: Any, **kwargs: Any) -> Any:
        pytest.fail("inactive scope allocated a child channel or process")

    def run(command: Any, **kwargs: Any) -> Any:
        assert kwargs["root"] is False and kwargs["parent"] is parent
        calls.append(parent)
        if scope == "late":
            # Interpose at the actual authentication/registration boundary.
            broker.groups.remove(parent)
            broker.scopes.clear()
            return _subprocess._Broker.run(broker, command, **kwargs)
        assert scope == "active"
        return subprocess.CompletedProcess(command, 0, b"", b"")

    monkeypatch.setattr(broker, "run", run)
    monkeypatch.setattr(_subprocess.socket, "socketpair", unexpected)
    monkeypatch.setattr(_subprocess.subprocess, "Popen", unexpected)
    monkeypatch.setattr(
        _subprocess.socket,
        "recv_fds",
        lambda *args: (b"", [descriptor], 0, None),
        raising=False,
    )
    monkeypatch.setattr(_subprocess, "_read_frame", lambda *args: request)
    monkeypatch.setattr(
        _subprocess, "_send_frame", lambda channel, value: responses.append(value)
    )
    broker._request(connection)
    if scope == "active":
        assert responses == [
            {"kind": "completed", "returncode": 0, "stdout_bytes": 0, "stderr_bytes": 0}
        ]
    else:
        assert responses == [
            {"kind": "error", "error": "inactive process supervision scope"}
        ]
    assert calls == ([parent] if scope in {"active", "late"} else [])
    assert connection.closed and not broker.connections
    with pytest.raises(OSError):
        os.fstat(descriptor)


@pytest.mark.parametrize("token", ["a" * 64, "b" * 64, "c" * 64])
def test_scope_capabilities_are_never_reissued_before_allocation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, token: str
) -> None:
    broker, parent = _synthetic_scope_broker()

    def unexpected(*args: Any, **kwargs: Any) -> Any:
        pytest.fail("reissued scope allocated a child channel or process")

    monkeypatch.setattr(_subprocess.secrets, "token_hex", lambda count: token)
    monkeypatch.setattr(_subprocess.socket, "socketpair", unexpected)
    monkeypatch.setattr(_subprocess.subprocess, "Popen", unexpected)
    with pytest.raises(OSError, match="scope capability collision"):
        broker.run(
            ["must-not-launch"],
            cwd=tmp_path,
            env={},
            timeout=1,
            capture=True,
            root=False,
            parent=parent,
        )
    assert broker.groups == {parent} and broker.scopes == {parent.scope_token: parent}


@pytest.mark.parametrize("cancelled", [False, True])
def test_scope_release_is_iterative_revokes_before_signals_and_preserves_siblings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, cancelled: bool
) -> None:
    broker, caller = _synthetic_scope_broker()
    channel_type = type(caller.channel)

    def add(parent: Any, index: int) -> Any:
        group = _subprocess._Group(
            SimpleNamespace(pid=20000 + index),
            channel_type(),
            scope_token=f"synthetic-{index}",
            parent=parent,
        )
        broker.groups.add(group)
        broker.scopes[group.scope_token] = group
        parent.children.add(group)
        return group

    sibling = add(caller, 0)
    ancestor = add(caller, 1)
    subtree = [ancestor]
    for index in range(2, 1102):
        subtree.append(add(subtree[-1], index))
    signals: list[int] = []

    def unexpected(*args: Any, **kwargs: Any) -> Any:
        pytest.fail("revoked descendant allocated a child channel or process")

    def signal_owned(pid: int, sig: int) -> None:
        assert broker.groups == {caller, sibling}
        assert set(broker.scopes) == {caller.scope_token, sibling.scope_token}
        with pytest.raises(ValueError, match="inactive process supervision scope"):
            broker.run(
                ["must-not-launch"],
                cwd=tmp_path,
                env={},
                timeout=1,
                capture=True,
                root=False,
                parent=subtree[-1],
            )
        signals.append(pid)

    # These are synthetic registered guards, never real or census-derived PIDs.
    monkeypatch.setattr(_subprocess, "os", SimpleNamespace(killpg=signal_owned))
    monkeypatch.setattr(_subprocess, "signal", SimpleNamespace(SIGKILL=9))
    monkeypatch.setattr(_subprocess.socket, "socketpair", unexpected)
    monkeypatch.setattr(_subprocess.subprocess, "Popen", unexpected)
    broker.release(ancestor, cancelled=cancelled)
    assert signals == [group.process.pid for group in reversed(subtree)]
    assert caller.children == {sibling, ancestor}
    assert not caller.cancel.is_set() and not sibling.cancel.is_set()
    assert not caller.channel.closed and not sibling.channel.closed
    for group in subtree:
        assert group.cancel.is_set() and group.channel.closed
        assert not group.cleanup_done.is_set()
        assert group.expired.is_set() == (cancelled or group is not ancestor)
        with pytest.raises(ValueError, match="inactive process supervision scope"):
            broker._scope(group.scope_token)


@pytest.mark.parametrize("owner", [lean_runner])
@pytest.mark.parametrize("deadline_first", [False, True])
def test_watchdog_cancellation_and_deadline(
    owner: Any, deadline_first: bool, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    callbacks: list[Any] = []
    kills: list[tuple[int, int]] = []

    class Thread:
        def __init__(self, *, target: Any, daemon: bool) -> None:
            self.target = target

        def start(self) -> None:
            if deadline_first:
                self.target()
            else:
                callbacks.append(self.target)

        def join(self) -> None:
            for callback in callbacks:
                callback()
            callbacks.clear()

    class Process:
        pid = 456
        returncode = 0

        def communicate(self, **kwargs: Any) -> tuple[str, str]:
            if deadline_first:
                assert kills == [(456, owner.signal.SIGKILL)]
            return "compiled", ""

    monkeypatch.setattr(owner.threading, "Thread", Thread)
    monkeypatch.setattr(owner.subprocess, "Popen", lambda *a, **kw: Process())
    monkeypatch.setattr(owner.os, "getpgid", lambda pid: pid)
    monkeypatch.setattr(owner.os, "killpg", lambda pid, sig: kills.append((pid, sig)))

    def run() -> Any:
        if owner is _subprocess:
            return owner.run_process_group(["fake"], cwd=tmp_path, timeout=0)
        return owner.run_lean_probe(
            tmp_path / "Probe.lean", import_root=tmp_path, cwd=tmp_path, timeout_s=0
        )

    if deadline_first:
        with pytest.raises(owner.subprocess.TimeoutExpired):
            run()
    else:
        assert run().stdout == "compiled"
    for callback in callbacks:
        callback()
    if not deadline_first:
        assert kills == [], "normal completion must cancel the group-kill backstop"


@pytest.mark.parametrize("check", [False, True])
def test_deadline_before_communicate_is_still_a_timeout(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, check: bool
) -> None:
    import subprocess
    import sys
    import time

    start = _subprocess.threading.Thread.start

    def delayed_start(thread: Any) -> None:
        start(thread)
        time.sleep(0.2)

    monkeypatch.setattr(_subprocess.threading.Thread, "start", delayed_start)
    with pytest.raises(subprocess.TimeoutExpired):
        _subprocess.run_process_group(
            [sys.executable, "-S", "-c", "import time; time.sleep(2)"],
            cwd=tmp_path,
            timeout=0.05,
            check=check,
        )


_SHARED_OWNER = Path(_subprocess.__file__).resolve()


def _load_shared() -> str:
    return (
        "import importlib.util\n"
        f"spec=importlib.util.spec_from_file_location('owned_process_helper',{str(_SHARED_OWNER)!r})\n"
        "helper=importlib.util.module_from_spec(spec)\nspec.loader.exec_module(helper)\n"
    )


@pytest.mark.skipif(os.name != "posix", reason="private guard requires POSIX")
def test_private_guard_excludes_site_without_changing_target_startup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        _subprocess,
        "_GUARD_PROGRAM",
        "import sys;assert 'site' not in sys.modules\n" + _subprocess._GUARD_PROGRAM,
    )
    result = _subprocess.run_process_group(
        [sys.executable, "-c", "import sys;print('site' in sys.modules)"],
        cwd=tmp_path,
        timeout=3,
        check=True,
    )
    assert result.stdout == "True\n"


def _status(pid: int) -> str:
    return subprocess.run(
        ["/bin/ps", "-o", "stat=", "-p", str(pid)],
        capture_output=True,
        text=True,
        check=False,
        timeout=1,
    ).stdout.strip()


def _sleeper_tree(tmp_path: Path) -> tuple[str, Path, Path]:
    child = tmp_path / "tool.json"
    grand = tmp_path / "grandchild.json"
    grand_program = (
        "import os,time,json;from pathlib import Path;"
        f"Path({str(grand)!r}).write_text(json.dumps([os.getpid(),os.getpgid(0)]));"
        "time.sleep(30)"
    )
    # Print before the grandchild marker exists: callers that crash once the
    # marker appears must not race the broker's forward of this output, which
    # the barrier rightly treats as an undelivered obligation.
    program = (
        "import os,sys,subprocess,time,json\nfrom pathlib import Path\n"
        f"Path({str(child)!r}).write_text(json.dumps([os.getpid(),os.getpgid(0)]))\n"
        "print('nested tool started',flush=True)\n"
        f"subprocess.Popen([sys.executable,'-S','-c',{grand_program!r}])\n"
        f"while not Path({str(grand)!r}).exists(): time.sleep(.005)\n"
        "time.sleep(30)\n"
    )
    return program, child, grand


def _registered_sleeper_tree(tmp_path: Path) -> tuple[str, tuple[Path, ...]]:
    program, child, grand = _sleeper_tree(tmp_path)
    intermediate = tmp_path / "intermediate.json"
    nested = (
        _load_shared()
        + "import os,sys,json\nfrom pathlib import Path\n"
        + f"Path({str(intermediate)!r}).write_text(json.dumps([os.getpid(),os.getpgid(0)]))\n"
        + "print('intermediate registered',flush=True)\n"
        + f"helper.run_process_group([sys.executable,'-S','-c',{program!r}],cwd={str(tmp_path)!r},timeout=None)\n"
    )
    return nested, (intermediate, child, grand)


@pytest.mark.skipif(os.name != "posix", reason="cooperative ownership is POSIX")
@pytest.mark.parametrize("returncode", [0, 7])
def test_three_registered_levels_release_on_parent_completion_and_crash(
    tmp_path: Path, returncode: int
) -> None:
    program, records = _registered_sleeper_tree(tmp_path)
    outer = (
        _load_shared()
        + "import os,sys,threading,time\nfrom pathlib import Path\n"
        + f"def inner():\n helper.run_process_group([sys.executable,'-S','-c',{program!r}],cwd={str(tmp_path)!r},timeout=None)\n"
        + "threading.Thread(target=inner,daemon=True).start()\n"
        + f"deadline=time.monotonic()+3\nwhile not Path({str(records[-1])!r}).exists() and time.monotonic()<deadline: time.sleep(.01)\n"
        + f"assert Path({str(records[-1])!r}).exists(),'registered descendants never reached readiness'\n"
        + "print('three registered levels started',flush=True)\n"
        + ("os._exit(7)\n" if returncode else "")
    )
    result = _subprocess.run_process_group(
        [sys.executable, "-S", "-c", outer], cwd=tmp_path, timeout=5
    )
    assert result.returncode == returncode, result.stderr
    assert result.stdout == "three registered levels started\n"
    for record in records:
        assert record.is_file(), "registered descendant never reached readiness"
        pid, pgid = json.loads(record.read_text())
        assert pgid != os.getpgrp()
        state = _status(pid)
        assert not state or state.startswith("Z"), (
            f"registered descendant still live: {pid}"
        )


@pytest.mark.skipif(os.name != "posix", reason="cooperative ownership is POSIX")
def test_three_level_inner_deadline_preserves_live_caller_and_sibling(
    tmp_path: Path,
) -> None:
    program, records = _registered_sleeper_tree(tmp_path)
    ready, release = tmp_path / "sibling-ready", tmp_path / "release-sibling"
    sibling = (
        "import time\nfrom pathlib import Path\n"
        + f"Path({str(ready)!r}).write_text('ready')\n"
        + f"deadline=time.monotonic()+6\nwhile not Path({str(release)!r}).exists() and time.monotonic()<deadline: time.sleep(.01)\n"
        + f"assert Path({str(release)!r}).exists(),'sibling was never released'\n"
        + "print('sibling completed',flush=True)\n"
    )
    outer = (
        _load_shared()
        + "import sys,subprocess,threading,time,json\nfrom pathlib import Path\n"
        + "results=[]\nerrors=[]\n"
        + "def independent():\n try:\n"
        + f"  results.append(helper.run_process_group([sys.executable,'-S','-c',{sibling!r}],cwd={str(tmp_path)!r},timeout=8,check=True))\n"
        + " except BaseException as error: errors.append(error)\n"
        + "worker=threading.Thread(target=independent,daemon=True)\nworker.start()\n"
        + f"deadline=time.monotonic()+3\nwhile not Path({str(ready)!r}).exists() and time.monotonic()<deadline: time.sleep(.01)\n"
        + f"assert Path({str(ready)!r}).exists(),'sibling never reached readiness'\n"
        + f"try:\n helper.run_process_group([sys.executable,'-S','-c',{program!r}],cwd={str(tmp_path)!r},timeout=2)\n"
        + "except subprocess.TimeoutExpired as error:\n"
        + " assert error.timeout==2 and b'intermediate registered' in error.output\n"
        + "else: raise AssertionError('inner deadline did not expire')\n"
        + f"for name in {[str(record) for record in records]!r}:\n"
        + " pid,_=json.loads(Path(name).read_text())\n"
        + " state=subprocess.run(['/bin/ps','-o','stat=','-p',str(pid)],capture_output=True,text=True,check=False,timeout=1).stdout.strip()\n"
        + " assert not state or state.startswith('Z'),'owned inner descendant still live'\n"
        + "assert worker.is_alive() and not results and not errors,'inner cleanup cancelled its sibling'\n"
        + f"Path({str(release)!r}).write_text('release')\n"
        + "worker.join(timeout=3)\n"
        + "assert not worker.is_alive() and not errors\n"
        + "assert len(results)==1 and results[0].stdout=='sibling completed\\n'\n"
        + "print('outer caller and sibling survived',flush=True)\n"
    )
    result = _subprocess.run_process_group(
        [sys.executable, "-S", "-c", outer], cwd=tmp_path, timeout=12, check=True
    )
    assert result.stdout == "outer caller and sibling survived\n"


@pytest.mark.skipif(os.name != "posix", reason="cooperative ownership is POSIX")
@pytest.mark.parametrize("crash", [False, True])
def test_cooperative_outer_deadline_and_crash_stop_nested_groups(
    tmp_path: Path, crash: bool
) -> None:
    program, child, grand = _sleeper_tree(tmp_path)
    outer = (
        _load_shared()
        + "import os,sys,threading,time\nfrom pathlib import Path\n"
        + f"def inner():\n helper.run_process_group([sys.executable,'-S','-c',{program!r}],cwd={str(tmp_path)!r},timeout=None)\n"
    )
    if crash:
        outer += (
            "threading.Thread(target=inner,daemon=True).start()\n"
            f"deadline=time.monotonic()+3\nwhile not Path({str(grand)!r}).exists() and time.monotonic()<deadline: time.sleep(.01)\n"
            f"assert Path({str(grand)!r}).exists(),'owned grandchildren never reached readiness'\n"
            "os._exit(7)\n"
        )
    else:
        outer += "inner()\n"
    unrelated = subprocess.Popen(
        [sys.executable, "-S", "-c", "import time;time.sleep(30)"],
        start_new_session=True,
    )
    try:
        started = time.monotonic()
        if crash:
            result = _subprocess.run_process_group(
                [sys.executable, "-S", "-c", outer], cwd=tmp_path, timeout=4
            )
            assert result.returncode == 7
        else:
            with pytest.raises(subprocess.TimeoutExpired):
                _subprocess.run_process_group(
                    [sys.executable, "-S", "-c", outer], cwd=tmp_path, timeout=3
                )
        call_budget = 4 if crash else 3
        assert time.monotonic() - started < call_budget + 2, (
            "nested pipes outlived bounded cleanup allowance"
        )
        for record in (child, grand):
            assert record.is_file(), "owned descendant never reached readiness"
            pid, pgid = json.loads(record.read_text())
            assert pgid != os.getpgrp(), "tool entered the calling test's group"
            state = _status(pid)
            assert not state or state.startswith("Z"), (
                f"owned descendant still live: {pid}"
            )
        assert unrelated.poll() is None, "cleanup touched an unrelated session"
    finally:
        unrelated.kill()
        unrelated.wait(timeout=2)


@pytest.mark.skipif(os.name != "posix", reason="cooperative ownership is POSIX")
def test_inner_deadline_preserves_outer_caller_and_partial_streams(
    tmp_path: Path,
) -> None:
    program, child, grand = _sleeper_tree(tmp_path)
    outer = (
        _load_shared()
        + "import sys,subprocess\n"
        + f"try:\n helper.run_process_group([sys.executable,'-S','-c',{program!r}],cwd={str(tmp_path)!r},timeout=2.5)\n"
        + "except subprocess.TimeoutExpired as error:\n"
        + " assert error.timeout==2.5\n"
        + " assert b'nested tool started' in error.output\n"
        + " print('outer caller survived',flush=True)\n"
    )
    result = _subprocess.run_process_group(
        [sys.executable, "-S", "-c", outer], cwd=tmp_path, timeout=6, check=True
    )
    assert result.stdout == "outer caller survived\n"
    for record in (child, grand):
        assert record.is_file(), "owned descendant never reached readiness"
        pid, _ = json.loads(record.read_text())
        state = _status(pid)
        assert not state or state.startswith("Z")


@pytest.mark.skipif(os.name != "posix", reason="cooperative ownership is POSIX")
@pytest.mark.parametrize("capture", [False, True])
def test_nested_normal_completion_preserves_output_and_check(
    tmp_path: Path, capture: bool
) -> None:
    outer = (
        _load_shared()
        + "import sys,subprocess\n"
        + f"result=helper.run_process_group([sys.executable,'-S','-c','print(\"inner complete\")'],cwd={str(tmp_path)!r},timeout=3,capture={capture!r},check=True)\n"
        + (
            "assert result.stdout=='inner complete\\n'\nprint(result.stdout,end='')\n"
            if capture
            else "assert result.stdout is None\n"
        )
        + f"try:\n helper.run_process_group([sys.executable,'-S','-c','import sys;print(\"failed output\");sys.exit(6)'],cwd={str(tmp_path)!r},timeout=3,check=True)\n"
        + "except subprocess.CalledProcessError as error:\n"
        + " assert error.returncode==6 and error.stdout=='failed output\\n'\n"
        + " print('check preserved')\n"
    )
    result = _subprocess.run_process_group(
        [sys.executable, "-S", "-c", outer], cwd=tmp_path, timeout=8, check=True
    )
    assert result.stdout == "inner complete\ncheck preserved\n"


@pytest.mark.skipif(os.name != "posix", reason="cooperative ownership is POSIX")
def test_nested_timeout_preserves_raw_incomplete_utf8_and_crlf(tmp_path: Path) -> None:
    stdout = b"raw\r\n\xe2"
    stderr = b"error\r\n\xff"
    tool = (
        f"import os,time;os.write(1,{stdout!r});os.write(2,{stderr!r});time.sleep(30)"
    )
    outer = (
        _load_shared()
        + "import sys,subprocess\n"
        + f"try:\n helper.run_process_group([sys.executable,'-S','-c',{tool!r}],cwd={str(tmp_path)!r},timeout=2)\n"
        + "except subprocess.TimeoutExpired as error:\n"
        + " assert error.timeout==2\n"
        + f" assert error.output=={stdout!r} and error.stderr=={stderr!r}\n"
        + " print('raw timeout preserved')\n"
        + "else: raise AssertionError('missing timeout')\n"
    )
    result = _subprocess.run_process_group(
        [sys.executable, "-S", "-c", outer], cwd=tmp_path, timeout=5, check=True
    )
    assert result.stdout == "raw timeout preserved\n"


@pytest.mark.skipif(os.name != "posix", reason="cooperative ownership is POSIX")
def test_nested_capture_larger_than_frame_bound(tmp_path: Path) -> None:
    size = 33 * 1024 * 1024
    tool = (
        "import os\nchunk=b'a'*65536\n"
        f"for _ in range({size // 65536}):\n"
        " data=chunk\n while data:\n  data=data[os.write(1,data):]\n"
    )
    outer = (
        _load_shared()
        + "import sys\n"
        + f"result=helper.run_process_group([sys.executable,'-S','-c',{tool!r}],cwd={str(tmp_path)!r},timeout=10,check=True)\n"
        + f"assert result.stdout=='a'*{size} and result.stderr==''\n"
        + "print('large capture preserved')\n"
    )
    result = _subprocess.run_process_group(
        [sys.executable, "-S", "-c", outer], cwd=tmp_path, timeout=15
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "large capture preserved\n"


@pytest.mark.skipif(os.name != "posix", reason="descriptor inheritance is POSIX")
def test_nested_command_inherits_callers_stdin(tmp_path: Path) -> None:
    tool = "import sys;print(sys.stdin.read(),end='')"
    outer = (
        _load_shared()
        + "import os,sys\n"
        + "original=os.dup(0)\nreader,writer=os.pipe()\n"
        + "os.write(writer,b'caller input\\r\\n');os.close(writer)\n"
        + "os.dup2(reader,0);os.close(reader)\ntry:\n"
        + f" result=helper.run_process_group([sys.executable,'-S','-c',{tool!r}],cwd={str(tmp_path)!r},timeout=3,check=True)\n"
        + " assert result.stdout=='caller input\\n'\n"
        + "finally:\n os.dup2(original,0);os.close(original)\n"
        + "print('caller stdin preserved')\n"
    )
    result = _subprocess.run_process_group(
        [sys.executable, "-S", "-c", outer], cwd=tmp_path, timeout=6, check=True
    )
    assert result.stdout == "caller stdin preserved\n"


@pytest.mark.skipif(os.name != "posix", reason="descriptor inheritance is POSIX")
def test_nested_uncaptured_output_uses_callers_live_descriptor(tmp_path: Path) -> None:
    output, signal = tmp_path / "caller-output", tmp_path / "continue"
    tool = (
        "import time\nfrom pathlib import Path\nprint('live progress',flush=True)\n"
        + f"deadline=time.monotonic()+2\nwhile not Path({str(signal)!r}).exists() and time.monotonic()<deadline: time.sleep(.01)\n"
        + f"assert Path({str(signal)!r}).exists(),'output was deferred or misdirected'\n"
        + "print('finished',flush=True)\n"
    )
    outer = (
        _load_shared()
        + "import os,sys,threading,time\nfrom pathlib import Path\n"
        + "original=os.dup(1)\n"
        + f"sink=os.open({str(output)!r},os.O_CREAT|os.O_WRONLY,0o600)\nos.dup2(sink,1);os.close(sink)\n"
        + "def observe():\n deadline=time.monotonic()+2\n"
        + f" while 'live progress' not in Path({str(output)!r}).read_text() and time.monotonic()<deadline: time.sleep(.01)\n"
        + f" if 'live progress' in Path({str(output)!r}).read_text(): Path({str(signal)!r}).touch()\n"
        + "observer=threading.Thread(target=observe);observer.start()\ntry:\n"
        + f" result=helper.run_process_group([sys.executable,'-S','-c',{tool!r}],cwd={str(tmp_path)!r},timeout=3,capture=False,check=True)\n"
        + " assert result.stdout is None and result.stderr is None\n"
        + "finally:\n os.dup2(original,1);os.close(original);observer.join()\n"
        + f"assert Path({str(output)!r}).read_text()=='live progress\\nfinished\\n'\n"
        + "print('live caller output preserved')\n"
    )
    result = _subprocess.run_process_group(
        [sys.executable, "-S", "-c", outer], cwd=tmp_path, timeout=6, check=True
    )
    assert result.stdout == "live caller output preserved\n"


@pytest.mark.skipif(os.name != "posix", reason="private broker requires POSIX")
@pytest.mark.parametrize("lease", ["partial", "stale"])
def test_invalid_lease_refuses_fallback_launch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, lease: str
) -> None:
    marker = tmp_path / "must-not-launch"
    monkeypatch.setenv(_subprocess._SOCKET_ENV, str(tmp_path / "missing.sock"))
    if lease == "partial":
        monkeypatch.delenv(_subprocess._TOKEN_ENV, raising=False)
    else:
        monkeypatch.setenv(_subprocess._TOKEN_ENV, "synthetic-invalid-capability")
    with pytest.raises(OSError):
        _subprocess.run_process_group(
            [
                sys.executable,
                "-c",
                f"from pathlib import Path;Path({str(marker)!r}).touch()",
            ],
            cwd=tmp_path,
            timeout=1,
        )
    assert not marker.exists()


@pytest.mark.skipif(os.name != "posix", reason="private broker requires POSIX")
def test_broker_rejects_unauthenticated_and_pid_requests(tmp_path: Path) -> None:
    marker = tmp_path / "must-not-launch"
    broker = _subprocess._Broker()
    try:
        for forged_pid in (False, True):
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as channel:
                channel.connect(broker.address)
                request = {
                    "token": broker.token if forged_pid else "synthetic-wrong-token",
                    "command": [
                        sys.executable,
                        "-c",
                        f"from pathlib import Path;Path({str(marker)!r}).touch()",
                    ],
                    "cwd": str(tmp_path),
                    "env": {},
                    "timeout": 1,
                    "capture": True,
                }
                if forged_pid:
                    request["pid"] = os.getpid()
                _subprocess._send_frame(channel, request)
                assert _subprocess._read_frame(channel)["kind"] == "error"
        assert not marker.exists() and not broker.groups
    finally:
        broker.close()


@pytest.mark.skipif(os.name != "posix", reason="detached sessions require POSIX")
def test_unregistered_detached_pipe_has_bounded_drain(tmp_path: Path) -> None:
    # This raw detached child is explicitly outside cooperative cleanup. It has
    # its own short lifetime; the test never kills a PID learned from a census.
    record = tmp_path / "raw.json"
    detached = (
        "import os,time,json;from pathlib import Path;"
        f"Path({str(record)!r}).write_text(json.dumps([os.getpid(),os.getpgid(0)]));"
        "time.sleep(5)"
    )
    outer = (
        "import subprocess,sys,time\n"
        f"subprocess.Popen([sys.executable,'-S','-c',{detached!r}],start_new_session=True)\n"
        f"while not __import__('pathlib').Path({str(record)!r}).exists(): time.sleep(.005)\n"
        "print('partial raw output',flush=True)\ntime.sleep(30)\n"
    )
    started = time.monotonic()
    with pytest.raises(subprocess.TimeoutExpired) as error:
        _subprocess.run_process_group(
            [sys.executable, "-S", "-c", outer], cwd=tmp_path, timeout=2
        )
    assert time.monotonic() - started < 4
    assert error.value.timeout == 2
    assert b"partial raw output" in error.value.output
    assert record.is_file(), "detached pipe holder never reached readiness"
    pid, _ = json.loads(record.read_text())
    assert _status(pid) and not _status(pid).startswith("Z"), (
        "raw escape was falsely claimed killed"
    )
    deadline = time.monotonic() + 6
    while time.monotonic() < deadline:
        state = _status(pid)
        if not state or state.startswith("Z"):
            break
        time.sleep(0.02)
    else:
        pytest.fail("test-owned short detached child did not finish")


@pytest.mark.parametrize("blocked", [False, True])
def test_closing_subtree_shares_deadline_and_retains_failure(
    monkeypatch: pytest.MonkeyPatch, blocked: bool
) -> None:
    broker, parent = _synthetic_scope_broker()
    sibling = _subprocess._Group(
        SimpleNamespace(pid=12346),
        parent.channel.__class__(),
        scope_token="sibling",
        parent=None,
    )
    broker.groups.add(sibling)
    broker.scopes[sibling.scope_token] = sibling
    nodes = []
    for index in range(24):
        ancestor = parent if index % 2 == 0 else nodes[-1]
        child = _subprocess._Group(
            SimpleNamespace(pid=12400 + index),
            parent.channel.__class__(),
            scope_token=f"child-{index}",
            parent=ancestor,
        )
        ancestor.children.add(child)
        broker.groups.add(child)
        broker.scopes[child.scope_token] = child
        nodes.append(child)
    signals = []
    monkeypatch.setattr(
        _subprocess, "os", SimpleNamespace(killpg=lambda pid, sig: signals.append(pid))
    )
    # Model a forward-error release before the ancestor sees its outcome.
    broker.release(nodes[0])
    assert nodes[0] in parent.children
    broker.release(parent)
    assert len(signals) == 25 and len(set(signals)) == 25
    broker.release(parent, cancelled=True)
    assert len(signals) == 25
    assert broker._scope(sibling.scope_token) is sibling
    for group in [parent, *nodes]:
        with pytest.raises(ValueError, match="inactive"):
            broker._scope(group.scope_token)
    assert all(n.cleanup_deadline <= parent.cleanup_deadline for n in nodes)
    entered, unblock = threading.Event(), threading.Event()

    def complete() -> None:
        entered.set()
        assert unblock.wait(2)
        for child in reversed(nodes):
            child.cleanup_settled = True
            broker._complete_cleanup(child)

    worker = threading.Thread(target=complete)
    worker.start()
    assert entered.wait(1)
    started = time.monotonic()
    try:
        if blocked:
            with pytest.raises(OSError, match="subtree cleanup incomplete"):
                broker._await_children(parent)
            assert time.monotonic() - started < _subprocess._REAP_TIMEOUT_S + 0.2
        else:
            unblock.set()
            broker._await_children(parent)
        assert not parent.cleanup_done.is_set()
    finally:
        unblock.set()
        worker.join(timeout=1)
    assert not worker.is_alive() and not parent.children
    failed = nodes[0]
    failed.parent = parent
    parent.children.add(failed)
    failed.cleanup_error = OSError("controlled failure")
    with pytest.raises(
        OSError, match="subtree cleanup failed|subtree cleanup incomplete"
    ):
        broker._await_children(parent)


@pytest.mark.skipif(os.name != "posix", reason="private broker requires POSIX")
@pytest.mark.parametrize("forward_failure", [False, True])
@pytest.mark.parametrize("blocked", [False, True])
def test_real_ancestor_response_waits_for_closing_child(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    forward_failure: bool,
    blocked: bool,
) -> None:
    broker = _subprocess._Broker()
    entered, unblock, barrier = threading.Event(), threading.Event(), threading.Event()
    forward_hook = threading.Event()
    request_exit = threading.Event()
    request = broker._request
    complete = broker._complete_cleanup
    await_children = broker._await_children
    send = _subprocess._send_frame
    children = []

    def hold(group: Any) -> None:
        if group.parent is not None:
            children.append(group)
            entered.set()
            assert unblock.wait(2), "cleanup control was not released"
        complete(group)

    def await_control(group: Any) -> None:
        if group.parent is None:
            barrier.set()
        await_children(group)

    def forward(channel: Any, value: Any) -> None:
        if isinstance(value, dict) and value.get("kind") == "stream":
            # Let the caller crash only after the child's guard reported, so
            # the early-closing classification is deterministic.
            with broker.lock:
                closing = [g for g in broker.groups if g.parent is not None]
            deadline = time.monotonic() + 2
            while (
                any(g.outcome is None for g in closing) and time.monotonic() < deadline
            ):
                time.sleep(0.005)
            marker.touch()
            if forward_failure:
                forward_hook.set()
                raise BrokenPipeError("controlled caller transport failure")
        send(channel, value)

    def request_control(connection: Any) -> None:
        try:
            request(connection)
        finally:
            request_exit.set()

    monkeypatch.setattr(broker, "_request", request_control)
    monkeypatch.setattr(broker, "_complete_cleanup", hold)
    monkeypatch.setattr(broker, "_await_children", await_control)
    monkeypatch.setattr(_subprocess, "_send_frame", forward)
    marker = tmp_path / "ready"
    tool = "print('child output',flush=True)"
    outer = (
        _load_shared()
        + "import sys,threading,time,os\nfrom pathlib import Path\n"
        + f"def inner():\n helper.run_process_group([sys.executable,'-S','-c',{tool!r}],cwd={str(tmp_path)!r},timeout=None)\n"
        + "threading.Thread(target=inner,daemon=True).start()\n"
        + f"deadline=time.monotonic()+2\nwhile not Path({str(marker)!r}).exists() and time.monotonic()<deadline: time.sleep(.005)\n"
        + f"assert Path({str(marker)!r}).exists()\n"
        + "os._exit(7)\n"
    )
    results, errors = [], []

    def run() -> None:
        try:
            results.append(
                broker.run(
                    [sys.executable, "-S", "-c", outer],
                    cwd=tmp_path,
                    env=dict(os.environ),
                    timeout=4,
                    capture=True,
                    root=True,
                )
            )
        except BaseException as error:
            errors.append(error)

    worker = threading.Thread(target=run)
    worker.start()
    try:
        assert entered.wait(3), "child cleanup hook did not activate"
        assert barrier.wait(1), "ancestor barrier hook did not activate"
        if forward_failure:
            assert forward_hook.is_set(), "forward-error hook did not activate"
        assert worker.is_alive() and not results and not errors
        if not blocked:
            unblock.set()
        worker.join(timeout=1)
        assert not worker.is_alive(), "ancestor exceeded original cleanup cap"
        # The caller crashed before this early-closing request could deliver
        # its terminal response. Even the unblocked, EOF-clean branch retains
        # that unacknowledged obligation. Live commands canceled by an ancestor
        # remain the original crash test's distinct clean-cancellation case.
        assert not results and len(errors) == 1
        assert isinstance(errors[0], OSError)
        assert ("cleanup incomplete" if blocked else "cleanup failed") in str(errors[0])
        if not blocked and not forward_failure:
            assert children[0].request_done.is_set()
            assert not children[0].delivery_done.is_set()
            assert any(
                "terminal response unacknowledged" in str(error)
                for error in children[0].cleanup_errors
            )
    finally:
        # Test-only teardown of the deliberately held worker, after the
        # production barrier's expected failure; never reset that deadline.
        unblock.set()
        worker.join(timeout=1)
        assert request_exit.wait(1), "held request did not exit during teardown"
        broker.close()
    assert children and all(child.cleanup_done.is_set() for child in children)
    assert not broker.workers and not broker.groups


def test_outcome_and_watchdog_release_race_is_idempotent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    broker, group = _synthetic_scope_broker()
    start = threading.Barrier(3)
    signals = []
    monkeypatch.setattr(
        _subprocess, "os", SimpleNamespace(killpg=lambda pid, sig: signals.append(pid))
    )

    def release(cancelled: bool) -> None:
        start.wait(timeout=1)
        broker.release(group, cancelled=cancelled)

    workers = [
        threading.Thread(target=release, args=(value,)) for value in (False, True)
    ]
    for worker in workers:
        worker.start()
    start.wait(timeout=1)
    for worker in workers:
        worker.join(timeout=1)
    assert all(not worker.is_alive() for worker in workers)
    assert signals == [group.process.pid]
    assert group.cancel.is_set() and not group.cleanup_done.is_set()
    with pytest.raises(ValueError, match="inactive"):
        broker._scope(group.scope_token)


@pytest.mark.parametrize(
    "state",
    [
        "accepted",
        "send-only",
        "incomplete",
        "wrong-token",
        "wrong-receipt",
        "revoked",
        "expired",
    ],
)
def test_terminal_acceptance_only_discharges_settled_authenticated_error(
    monkeypatch: pytest.MonkeyPatch, state: str
) -> None:
    broker, parent = _synthetic_scope_broker()
    child = _subprocess._Group(
        SimpleNamespace(pid=12346),
        type(parent.channel)(),
        scope_token="child",
        parent=parent,
    )
    parent.children.add(child)
    child.cleanup_error = OSError("nonEOF capture")
    child.cleanup_errors.append(child.cleanup_error)
    child.cleanup_settled = state != "incomplete"
    child.request_done.set()
    child.terminal_receipt = "d" * 64
    broker._complete_cleanup(child)
    assert child in parent.children and child.cleanup_done.is_set()
    token = "sibling" if state == "wrong-token" else parent.scope_token
    receipt = "e" * 64 if state == "wrong-receipt" else child.terminal_receipt
    if state == "revoked":
        broker.groups.remove(parent)
        broker.scopes.clear()
    if state == "expired":
        parent.expired.set()
    if state != "send-only":
        broker._acknowledge(child, token, receipt)
    assert child.delivery_done.is_set() == (state == "accepted")
    assert (child not in parent.children) == (state == "accepted")
    assert child.cleanup_error is not None and child.cleanup_errors
    # Acceptance cannot reactivate an expired child or signal a supplied PID.
    with pytest.raises(ValueError, match="inactive"):
        broker._scope(child.scope_token)
    parent.cleanup_deadline = time.monotonic()
    if state == "accepted":
        broker._await_children(parent)
    else:
        with pytest.raises(
            OSError, match="subtree cleanup failed|subtree cleanup incomplete"
        ):
            broker._await_children(parent)


@pytest.mark.parametrize("depth", [1, 40])
def test_completion_tree_has_one_budget_even_with_terminal_errors(
    monkeypatch: pytest.MonkeyPatch, depth: int
) -> None:
    broker, parent = _synthetic_scope_broker()
    nodes = [parent]
    for index in range(40):
        ancestor = nodes[-1] if depth == 40 else parent
        child = _subprocess._Group(
            SimpleNamespace(pid=13000 + index),
            type(parent.channel)(),
            scope_token=f"tree-{index}",
            parent=ancestor,
        )
        ancestor.children.add(child)
        broker.groups.add(child)
        broker.scopes[child.scope_token] = child
        nodes.append(child)
    signals = []
    monkeypatch.setattr(
        _subprocess, "os", SimpleNamespace(killpg=lambda pid, sig: signals.append(pid))
    )
    started = time.monotonic()
    broker.release(parent)
    deadline = parent.cleanup_deadline
    assert all(node.cleanup_deadline == deadline for node in nodes)
    # This is a synthetic completion tree, not a claim of 40 live guard reaps.
    for node in reversed(nodes[1:]):
        with (
            pytest.raises(
                OSError, match="subtree cleanup incomplete|subtree cleanup failed"
            )
            if node.children
            else contextlib.nullcontext()
        ):
            broker._await_children(node)
        node.cleanup_error = OSError("controlled incomplete descendant")
        node.cleanup_settled = False
        broker._complete_cleanup(node)
    with pytest.raises(
        OSError, match="subtree cleanup failed|subtree cleanup incomplete"
    ):
        broker._await_children(parent)
    assert time.monotonic() - started < _subprocess._REAP_TIMEOUT_S + 0.2
    broker.release(parent)
    assert parent.cleanup_deadline == deadline and len(signals) == 41


@pytest.mark.parametrize(
    "case",
    [
        "completed",
        "timeout",
        "oserror",
        "length",
        "returncode",
        "timeout-type",
        "timeout-mismatch",
        "error-type",
        "bad-kind",
        "bad-text",
        "ack-send-failure",
        "close-primary-failure",
    ],
)
def test_remote_validates_terminal_response_before_acknowledgment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, case: str
) -> None:
    import base64
    import hashlib

    class Channel:
        def __enter__(self) -> Any:
            return self

        def close(self) -> None:
            if case == "close-primary-failure":
                raise OSError("controlled remote close failure")

        def settimeout(self, value: Any) -> None:
            pass

        def connect(self, address: str) -> None:
            assert address == "synthetic-address"

        def sendall(self, data: bytes) -> None:
            pass

        def recv(self, count: int) -> bytes:
            return b""

    response: dict[str, Any] = {
        "kind": "completed",
        "returncode": 0,
        "receipt": "d" * 64,
        "diagnostics": ["controlled cleanup diagnostic"],
        "stdout_bytes": 4,
        "stderr_bytes": 0,
    }
    data = b"ok\r\n"
    if case in {
        "timeout",
        "timeout-type",
        "timeout-mismatch",
        "ack-send-failure",
        "close-primary-failure",
    }:
        response.pop("returncode")
        response.update(
            kind="timeout",
            timeout=True
            if case == "timeout-type"
            else 3
            if case == "timeout-mismatch"
            else 2,
        )
        data = b"\xe2\r\nx"
    if case in {"oserror", "error-type"}:
        response.pop("returncode")
        response.update(
            kind="oserror",
            error=[None, 4 if case == "error-type" else "controlled error"],
        )
    if case == "length":
        response["stderr_bytes"] = 1
    if case == "returncode":
        response["returncode"] = True
    if case == "bad-kind":
        response["kind"] = []
    if case == "bad-text":
        data = b"\xffabc"
    frames = iter(
        [
            {
                "kind": "stream",
                "pipe": "stdout",
                "data": base64.b64encode(data).decode(),
            },
            response,
        ]
    )
    sent = []

    def send(channel: Any, value: Any) -> None:
        sent.append(value)
        if case == "ack-send-failure":
            raise BrokenPipeError("controlled acknowledgment loss")

    monkeypatch.setattr(
        _subprocess,
        "os",
        SimpleNamespace(
            environ={
                _subprocess._TOKEN_ENV: "authenticated-parent",
                _subprocess._SOCKET_ENV: "synthetic-address",
            },
            fspath=os.fspath,
        ),
    )
    monkeypatch.setattr(
        _subprocess,
        "socket",
        SimpleNamespace(
            AF_UNIX=1,
            SOCK_STREAM=1,
            socket=lambda *args: Channel(),
            send_fds=lambda channel, frames, fds: len(frames[0]),
        ),
    )
    monkeypatch.setattr(_subprocess, "_read_frame", lambda channel: next(frames))
    monkeypatch.setattr(_subprocess, "_send_frame", send)
    if case == "completed":
        result = _subprocess._remote(
            ["accepted"], cwd=tmp_path, env={}, timeout=2, capture=True
        )
        assert result.stdout == "ok\n"
    elif case in {"timeout", "ack-send-failure", "close-primary-failure"}:
        with pytest.raises(subprocess.TimeoutExpired) as caught:
            _subprocess._remote(
                ["accepted"], cwd=tmp_path, env={}, timeout=2, capture=True
            )
        assert caught.value.output == b"\xe2\r\nx" and caught.value.stderr == b""
        assert caught.value.__notes__
    else:
        with pytest.raises((OSError, UnicodeDecodeError)):
            _subprocess._remote(
                ["accepted"], cwd=tmp_path, env={}, timeout=2, capture=True
            )
    valid = case in {
        "completed",
        "timeout",
        "oserror",
        "ack-send-failure",
        "close-primary-failure",
    }
    assert len(sent) == int(valid), "invalid response must never be acknowledged"
    if valid:
        assert sent[0] == {
            "kind": "ack",
            "token": "authenticated-parent",
            "receipt": hashlib.sha256(_subprocess._frame_bytes(response)).hexdigest(),
        }


@pytest.mark.skipif(os.name != "posix", reason="owned POSIX guard")
@pytest.mark.parametrize(
    "fault", ["wait-reaped", "wait-unreaped", "join-done", "close-done", "close-open"]
)
@pytest.mark.parametrize("capture", [False, True])
def test_cleanup_faults_publish_terminal_diagnostics_and_physical_settlement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fault: str, capture: bool
) -> None:
    if not capture and fault.startswith("close"):
        pytest.skip("uncaptured guard has no capture stream to fault")
    broker = _subprocess._Broker()
    processes = []
    groups = []
    allocate = _subprocess.subprocess.Popen
    group_type = _subprocess._Group
    join = threading.Thread.join

    class Stream:
        def __init__(self, stream: Any) -> None:
            self.stream = stream

        def fileno(self) -> int:
            return self.stream.fileno()

        @property
        def closed(self) -> bool:
            return bool(self.stream.closed)

        def close(self) -> None:
            if fault == "close-done":
                self.stream.close()
            raise OSError("controlled capture close fault")

    def popen(*args: Any, **kwargs: Any) -> Any:
        process = allocate(*args, **kwargs)
        processes.append(process)
        wait = process.wait
        process.real_wait = wait
        if fault.startswith("wait"):

            def wait_fault(*args: Any, **kwargs: Any) -> Any:
                if fault == "wait-reaped":
                    wait(*args, **kwargs)
                raise OSError(f"controlled {fault} fault")

            process.wait = wait_fault
        if capture and fault.startswith("close"):
            process.stdout = Stream(process.stdout)
            process.stderr = Stream(process.stderr)
        return process

    class Group(group_type):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            groups.append(self)

    def join_fault(thread: Any, timeout: Any = None) -> None:
        join(thread, timeout=timeout)
        if thread is not broker.server:
            raise OSError("controlled join fault after real thread exit")

    monkeypatch.setattr(_subprocess.subprocess, "Popen", popen)
    monkeypatch.setattr(_subprocess, "_Group", Group)
    if fault == "join-done":
        monkeypatch.setattr(threading.Thread, "join", join_fault)
    try:
        with pytest.raises(OSError, match="controlled"):
            broker.run(
                [sys.executable, "-S", "-c", "pass"],
                cwd=tmp_path,
                env=dict(os.environ),
                timeout=2,
                capture=capture,
                root=True,
            )
        group = groups[0]
        assert group.cleanup_done.is_set() and group.cleanup_error is not None
        assert group.cleanup_errors and group.cleanup_error.__notes__
        assert group.cleanup_settled == (fault not in {"wait-unreaped", "close-open"})
        assert group.process.returncode is not None or fault == "wait-unreaped"
        if capture and fault != "close-open":
            assert all(
                stream.closed for stream in (group.process.stdout, group.process.stderr)
            )
    finally:
        # Explicit test-only settlement of an intentionally unreaped guard/open
        # stream; production observed failure is retained, never relabeled EOF.
        monkeypatch.setattr(threading.Thread, "join", join)
        for process in processes:
            process.real_wait(timeout=1)
            for stream in (process.stdout, process.stderr):
                if stream is not None:
                    (stream.stream if isinstance(stream, Stream) else stream).close()
        broker.close()
    assert not broker.groups and not broker.workers


def test_broker_close_error_preserves_primary_timeout_and_exact_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    primary = subprocess.TimeoutExpired(
        ["command"], 1, output=b"\xe2\r\n", stderr=b"\xff"
    )

    class Broker:
        def run(self, *args: Any, **kwargs: Any) -> Any:
            raise primary

        def close(self) -> None:
            raise OSError("controlled broker close failure")

    monkeypatch.setattr(_subprocess, "os", SimpleNamespace(name="posix", environ={}))
    monkeypatch.setattr(_subprocess, "_Broker", Broker)
    with pytest.raises(subprocess.TimeoutExpired) as caught:
        _subprocess.run_process_group(["command"], cwd=tmp_path, timeout=1)
    assert (
        caught.value is primary
        and caught.value.output == b"\xe2\r\n"
        and caught.value.stderr == b"\xff"
    )
    assert "controlled broker close failure" in caught.value.__notes__[0]


@pytest.mark.skipif(os.name != "posix", reason="SCM_RIGHTS request protocol")
@pytest.mark.parametrize(
    "mode",
    [
        "ack",
        "send-only",
        "lost-response",
        "send-fault",
        "wrong-token",
        "revoked",
        "incomplete",
        "clean-lost-response",
        "clean-revoked-response",
        "cancelled-clean-response",
    ],
)
def test_request_handoff_requires_actual_authenticated_terminal_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    import hashlib

    broker, parent = _synthetic_scope_broker()
    child = _subprocess._Group(
        SimpleNamespace(pid=12346),
        type(parent.channel)(),
        scope_token="child",
        parent=parent,
    )
    child.cleanup_error = (
        None
        if mode
        in {"clean-lost-response", "clean-revoked-response", "cancelled-clean-response"}
        else OSError("controlled nonEOF capture failure")
    )
    child.ancestor_cancelled = mode == "cancelled-clean-response"
    if child.ancestor_cancelled:
        child.expired.set()
    child.cleanup_settled = mode != "incomplete"
    child.cleanup_done.set()
    parent.children.add(child)
    local, client = socket.socketpair()
    local.settimeout(1)
    client.settimeout(1)
    broker.connections = {local}
    broker.workers = set()
    exited = threading.Event()
    sent = threading.Event()
    send_frame = _subprocess._send_frame

    def send(channel: Any, value: Any) -> None:
        if isinstance(value, dict) and "receipt" in value:
            sent.set()
            if mode == "send-fault":
                raise BrokenPipeError("controlled terminal response send fault")
        send_frame(channel, value)

    def run(command: Any, **kwargs: Any) -> Any:
        kwargs["registered"](child)
        raise subprocess.TimeoutExpired(command, 1, output=b"", stderr=b"")

    def request() -> None:
        try:
            broker._request(local)
        finally:
            exited.set()

    monkeypatch.setattr(broker, "run", run)
    monkeypatch.setattr(_subprocess, "_send_frame", send)
    worker = threading.Thread(target=request)
    worker.start()
    descriptor = os.open(os.devnull, os.O_RDONLY)
    try:
        frame = _subprocess._frame_bytes(
            {
                "token": parent.scope_token,
                "command": ["controlled"],
                "cwd": str(tmp_path),
                "env": {},
                "timeout": 1,
                "capture": True,
            }
        )
        count = socket.send_fds(client, [frame], [descriptor])
        if count < len(frame):
            client.sendall(frame[count:])
        assert sent.wait(1), "terminal send control did not activate"
        if mode not in {"lost-response", "send-fault"}:
            response = _subprocess._read_frame(client)
            assert response["kind"] == "timeout" and response["stdout_bytes"] == 0
            if mode in {
                "revoked",
                "clean-revoked-response",
                "cancelled-clean-response",
            }:
                with broker.lock:
                    broker.groups.remove(parent)
                    broker.scopes.clear()
            if mode not in {
                "send-only",
                "clean-lost-response",
                "clean-revoked-response",
                "cancelled-clean-response",
            }:
                send_frame(
                    client,
                    {
                        "kind": "ack",
                        "token": "sibling"
                        if mode == "wrong-token"
                        else parent.scope_token,
                        "receipt": hashlib.sha256(
                            _subprocess._frame_bytes(response)
                        ).hexdigest(),
                    },
                )
        client.close()
        assert exited.wait(1), "request worker did not finish bounded fixture teardown"
        worker.join(timeout=1)
        assert (
            child.request_done.is_set()
            and not broker.connections
            and not broker.workers
        )
        assert child.delivery_done.is_set() == (mode == "ack")
        assert (child not in parent.children) == (
            mode in {"ack", "cancelled-clean-response"}
        )
        assert (child.cleanup_error is None) == (mode == "cancelled-clean-response")
        parent.cleanup_deadline = time.monotonic()
        if mode in {"ack", "cancelled-clean-response"}:
            broker._await_children(parent)
        else:
            with pytest.raises(
                OSError, match="subtree cleanup failed|subtree cleanup incomplete"
            ):
                broker._await_children(parent)
    finally:
        os.close(descriptor)
        client.close()
        local.close()
        worker.join(timeout=1)
    assert not worker.is_alive()


@pytest.mark.skipif(os.name != "posix", reason="owned POSIX guard")
@pytest.mark.parametrize("capture", [False, True])
def test_live_owned_guard_cannot_be_discharged_by_delivered_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capture: bool
) -> None:
    # A failed authorized signal leaves the real owned tool blocked on our
    # socket. Test teardown releases it through that socket, without any new
    # PID/PGID authority or a signal after reap.
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    listener.listen()
    listener.settimeout(2)
    ready, release = threading.Event(), threading.Event()
    exited = threading.Event()
    control_errors = []

    def controller() -> None:
        try:
            with listener.accept()[0] as channel:
                channel.settimeout(3)
                assert channel.recv(1) == b"H"
                ready.set()
                assert release.wait(2)
                channel.sendall(b"R")
                assert channel.recv(1) == b""
        except BaseException as error:
            control_errors.append(error)
        finally:
            exited.set()

    control = threading.Thread(target=controller)
    control.start()
    broker = _subprocess._Broker()
    groups = []
    group_type = _subprocess._Group

    class Group(group_type):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            groups.append(self)

    signal_entered = threading.Event()

    def fail_signal(pid: int, sig: int) -> None:
        signal_entered.set()
        raise OSError("controlled owned signal failure")

    # A command with no detached descendants. The cooperative guard remains
    # genuinely live until the controller releases its direct tool.
    tool = (
        "import socket,os\ns=socket.socket();s.settimeout(3)\n"
        f"s.connect({listener.getsockname()!r});s.sendall(b'H')\n"
        "assert s.recv(1)==b'R';s.close()\n"
    )
    monkeypatch.setattr(_subprocess, "_Group", Group)
    monkeypatch.setattr(_subprocess.os, "killpg", fail_signal)
    result_errors = []

    def run() -> None:
        try:
            broker.run(
                [sys.executable, "-S", "-c", tool],
                cwd=tmp_path,
                env=dict(os.environ),
                timeout=0.15,
                capture=capture,
                root=True,
            )
        except BaseException as error:
            result_errors.append(error)

    worker = threading.Thread(target=run)
    started = time.monotonic()
    worker.start()
    try:
        assert ready.wait(1), "real held tool never reached its socket barrier"
        worker.join(timeout=1)
        assert not worker.is_alive() and signal_entered.is_set()
        assert time.monotonic() - started < 0.15 + _subprocess._REAP_TIMEOUT_S + 0.3
        assert len(result_errors) == 1 and isinstance(
            result_errors[0], (OSError, subprocess.TimeoutExpired)
        )
        group = groups[0]
        assert group.cleanup_done.is_set() and not group.cleanup_settled
        assert group.process.returncode is None, (
            "negative control did not keep the guard unreaped"
        )
        assert any(
            "guard cleanup incomplete" in str(error) for error in group.cleanup_errors
        )
        parent = group_type(
            SimpleNamespace(pid=-1),
            group.channel,
            scope_token="synthetic-active-parent",
            parent=None,
        )
        group.parent = parent
        parent.children.add(group)
        broker.groups.add(parent)
        broker.scopes[parent.scope_token] = parent
        group.request_done.set()
        group.terminal_receipt = "d" * 64
        broker.closed = False
        broker._acknowledge(group, parent.scope_token, group.terminal_receipt)
        assert group in parent.children and not group.delivery_done.is_set()
        broker.groups.remove(parent)
        broker.scopes.clear()
    finally:
        release.set()
        assert exited.wait(1), "socket controller did not finish teardown"
        control.join(timeout=1)
        worker.join(timeout=1)
        broker.close()
        for group in groups:
            group.process.wait(timeout=1)
        listener.close()
    assert not control_errors and not control.is_alive()
