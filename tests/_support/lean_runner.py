"""Shared process-group-safe runner for Lake/Lean compile probes.

Each readiness test file historically defined its own ``_run_lean`` using
``subprocess.run(..., timeout=N)``. On timeout, ``subprocess.run`` kills only
the direct child (``lake``); the grandchild ``lean`` process survives, holds
memory and the .olean lock region, and accumulates across a suite run until
the machine thrashes. Running through a new process group and killing the whole
group on timeout closes that leak (fep-tests HANDOFF, 2026-08-28/29).

Executable resolution lives in ``tests/_support/lake.py`` (``lake_executable``)
with the two deliberate missing-tool stances; see ``tests/conftest.py``.
"""

from __future__ import annotations

import contextlib
import os
import signal
import subprocess
import threading
from collections.abc import Sequence
from pathlib import Path

__all__ = [
    "run_lake_lean_probe",
    "run_lean_compile_probe",
    "run_lean_probe",
]


def run_lake_lean_probe(
    arguments: Sequence[str],
    *,
    cwd: Path,
    timeout_s: int = int(os.environ.get("FEP_LEAN_PROBE_TIMEOUT", "1800")),
    executable: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run ``lake <arguments>`` (e.g. ``["env", "lean", "--version"]``) in its own process group."""
    command = [
        executable if executable is not None else os.environ.get("FEP_LAKE_BIN", "lake"),
        *arguments,
    ]
    return _run_process_group(command, cwd=cwd, timeout_s=timeout_s)


def run_lean_compile_probe(
    source_path: Path,
    *,
    cwd: Path,
    import_root: Path | None = None,
    output_path: Path | None = None,
    timeout_s: int = int(os.environ.get("FEP_LEAN_PROBE_TIMEOUT", "1800")),
    executable: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Compile ``source_path`` via ``lake env lean [-R import_root] [-o output_path]`` in its own process group."""
    arguments = ["env", "lean"]
    if import_root is not None:
        arguments += ["-R", str(import_root)]
    if output_path is not None:
        arguments += ["-o", str(output_path)]
    arguments.append(str(source_path))
    return run_lake_lean_probe(
        arguments, cwd=cwd, timeout_s=timeout_s, executable=executable
    )


def run_lean_probe(
    probe_path: Path,
    *,
    import_root: Path,
    cwd: Path,
    timeout_s: int = int(os.environ.get("FEP_LEAN_PROBE_TIMEOUT", "1800")),
    executable: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Compile ``probe_path`` via ``lake env lean -R import_root`` in its own process group."""
    return run_lean_compile_probe(
        probe_path,
        cwd=cwd,
        import_root=import_root,
        timeout_s=timeout_s,
        executable=executable,
    )


def _run_process_group(
    command: list[str], *, cwd: Path, timeout_s: int
) -> subprocess.CompletedProcess[str]:
    process = subprocess.Popen(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    # Backstop watchdog: kill the whole process group if ``timeout_s`` elapses,
    # even when the caller dies first (e.g. pytest-timeout terminates the test
    # thread without running our ``except`` block). Without this, timed-out
    # lean grandchildren survive as PPID=1 orphans, hold gigabytes, and wedge
    # every later compile on the machine.
    timed_out = threading.Event()
    deadline_expired = threading.Event()

    def _watchdog() -> None:
        if timed_out.wait(timeout_s):
            return
        deadline_expired.set()
        with contextlib.suppress(ProcessLookupError):
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)

    watchdog = threading.Thread(target=_watchdog, daemon=True)
    watchdog.start()
    try:
        stdout, stderr = process.communicate(timeout=timeout_s + 60)
    except subprocess.TimeoutExpired:
        timed_out.set()
        with contextlib.suppress(ProcessLookupError):
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        with contextlib.suppress(Exception):
            process.communicate(timeout=30)
        raise
    finally:
        timed_out.set()
        watchdog.join()
    if deadline_expired.is_set():
        raise subprocess.TimeoutExpired(
            command, timeout_s, output=stdout, stderr=stderr
        )
    return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)
