"""Bounded capture with private, cooperative, root-owned POSIX groups.

Only groups created by the private broker can be signalled. Raw unregistered
detached sessions are outside descendant cleanup, but cannot hold capture open
indefinitely after cancellation. Other platforms receive direct-child cleanup.
"""

from __future__ import annotations

import base64
import contextlib
import hashlib
import json
import locale
import math
import os
import secrets
import selectors
import signal
import socket
import struct
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Callable, Iterator, Mapping, Sequence
from pathlib import Path
from typing import Any, Final, Literal, overload

__all__ = ["run_process_group"]
_REAP_TIMEOUT_S: Final = 0.5
_CHANNEL_TIMEOUT_S: Final = 5.0
_MAX_FRAME_BYTES: Final = 32 * 1024 * 1024
_SOCKET_ENV: Final = "FEP_LEAN_PROCESS_OWNER_SOCKET"
_TOKEN_ENV: Final = "FEP_LEAN_PROCESS_OWNER_TOKEN"

# The actual tool inherits this new group. Its leader stays alive (or unreaped
# on external death) until the root kills/deregisters it. No client supplies a
# PID, signal, executable code or import path to this guard.
_GUARD_PROGRAM = r"""
import json, os, socket, struct, subprocess, sys
channel = socket.socket(fileno=int(sys.argv[1]))
os.set_inheritable(channel.fileno(), False)
def receive(n):
    parts = []
    while n:
        part = channel.recv(n)
        if not part:
            raise EOFError('launch channel closed')
        parts.append(part)
        n -= len(part)
    return b''.join(parts)
size = struct.unpack('!I', receive(4))[0]
if not 0 < size <= 33554432:
    raise ValueError('invalid launch frame')
command = json.loads(receive(size))
try:
    result = {'returncode': subprocess.Popen(command).wait()}
except OSError as error:
    result = {'oserror': [error.errno, error.strerror, error.filename]}
data = json.dumps(result, allow_nan=False).encode('utf-8')
channel.sendall(struct.pack('!I', len(data)) + data)
channel.recv(1)
"""


def _valid_timeout(timeout: object) -> bool:
    """Keep None unbounded; refuse malformed budgets before any allocation."""
    if timeout is None:
        return True
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)):
        return False
    try:
        # The remote capture channel adds the existing drain allowance before
        # socket.settimeout. Stay within Python's exposed wait representation.
        return (
            timeout > 0
            and math.isfinite(timeout)
            and timeout + 2 * _REAP_TIMEOUT_S <= threading.TIMEOUT_MAX
        )
    except OverflowError:
        return False


def _frame_bytes(value: Any) -> bytes:
    data = json.dumps(value, allow_nan=False).encode("utf-8")
    if not 0 < len(data) <= _MAX_FRAME_BYTES:
        raise ValueError("process supervision frame exceeds its bound")
    return struct.pack("!I", len(data)) + data


def _send_frame(channel: socket.socket, value: Any) -> None:
    channel.sendall(_frame_bytes(value))


def _read_frame(channel: socket.socket, header: bytes = b"") -> Any:
    def receive(count: int) -> bytes:
        parts = []
        while count:
            part = channel.recv(count)
            if not part:
                raise OSError("process supervision channel closed")
            parts.append(part)
            count -= len(part)
        return b"".join(parts)

    if len(header) > 4:
        raise ValueError("invalid process supervision frame header")
    count = struct.unpack("!I", header + receive(4 - len(header)))[0]
    if not 0 < count <= _MAX_FRAME_BYTES:
        raise ValueError("invalid process supervision frame length")
    return json.loads(receive(count))


def _text(data: bytes) -> str:
    return (
        data.decode(locale.getpreferredencoding(False))
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )


def _note(error: BaseException, message: str) -> None:
    # Validator execution uses 3.14; retain the package's 3.10 exception API.
    notes = getattr(error, "__notes__", [])
    error.__notes__ = [*notes, message]


@contextlib.contextmanager
def _remote_channel() -> Iterator[socket.socket]:
    channel = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        yield channel
    finally:
        primary = sys.exc_info()[1]
        try:
            channel.close()
        except OSError as error:
            if primary is None:
                raise
            _note(primary, f"remote channel close: {error}")


class _Group:
    def __init__(
        self,
        process: subprocess.Popen[bytes],
        channel: socket.socket,
        *,
        scope_token: str,
        parent: _Group | None,
    ):
        self.process = process
        self.channel = channel
        self.scope_token = scope_token
        self.parent = parent
        self.children: set[_Group] = set()
        self.finished = threading.Event()
        self.cleanup_done = threading.Event()
        self.cleanup_error: OSError | None = None
        self.cleanup_errors: list[BaseException] = []
        self.cleanup_settled = False
        self.delivery_done = threading.Event()
        self.request_done = threading.Event()
        self.request_owned = False
        self.terminal_receipt: str | None = None
        self.request_deadline: float | None = None
        self.stream_sizes = {"stdout_bytes": 0, "stderr_bytes": 0}
        self.cleanup_deadline: float | None = None
        self.expired = threading.Event()
        self.ancestor_cancelled = False
        self.cancel = threading.Event()
        self.outcome: dict[str, Any] | None = None
        self.error: BaseException | None = None
        self.command_error: BaseException | None = None


class _Broker:
    def __init__(self) -> None:
        self.directory = tempfile.TemporaryDirectory(prefix="fep-pg-", dir="/tmp")
        self.address = str(Path(self.directory.name) / "owner.sock")
        # Retained for compatibility with rejection controls, never allocation.
        self.token = secrets.token_hex(32)
        self.lock = threading.RLock()
        self.groups: set[_Group] = set()
        self.scopes: dict[str, _Group] = {}
        self.issued_tokens = {self.token}
        self.connections: set[socket.socket] = set()
        self.workers: set[threading.Thread] = set()
        self.closed = False
        self.cleanup_deadline: float | None = None
        self.listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.listener.bind(self.address)
        self.listener.listen()
        self.listener.settimeout(0.05)
        self.server = threading.Thread(target=self._serve, daemon=True)
        self.server.start()

    def release(self, group: _Group, *, cancelled: bool = False) -> None:
        with self.lock:
            pending, subtree = [group], []
            deadline = group.cleanup_deadline or time.monotonic() + _REAP_TIMEOUT_S
            if group.parent is None:
                self.cleanup_deadline = deadline
            while pending:
                current = pending.pop()
                subtree.append(current)
                pending.extend(current.children)
                current.cleanup_deadline = min(
                    current.cleanup_deadline or deadline, deadline
                )
            subtree = [current for current in subtree if current in self.groups]
            # Revoke the entire registered subtree before another request can
            # acquire the lock. Only fresh groups created here grant authority.
            for current in subtree:
                self.groups.remove(current)
                self.scopes.pop(current.scope_token)
            for current in reversed(subtree):
                # Only a command still running is canceled by its ancestor. One
                # whose guard already reported keeps its delivery obligation,
                # whichever release wins the lock.
                if (
                    current.parent is not None
                    and (current is not group or self.closed)
                    and current.outcome is None
                ):
                    current.ancestor_cancelled = True
                if cancelled or current is not group:
                    current.expired.set()
                # Closing children remain linked until their run has completed
                # drain, reap and thread cleanup. Revocation grants no new authority.
                # The unreaped guard reserves its original group identity;
                # neither a supplied PID nor a process census grants authority.
                try:
                    os.killpg(current.process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                except OSError as error:
                    current.cleanup_errors.append(error)
                current.cancel.set()
                with contextlib.suppress(OSError):
                    current.channel.shutdown(socket.SHUT_RDWR)
                try:
                    current.channel.close()
                except OSError as error:
                    current.cleanup_errors.append(error)

    def _await_children(self, group: _Group) -> None:
        # Release has atomically denied further allocation in this subtree.
        # Never hold the broker lock across waits or join shared request workers.
        with self.lock:
            children = tuple(group.children)
        assert group.cleanup_deadline is not None
        for child in children:
            if not child.cleanup_done.wait(
                max(0, group.cleanup_deadline - time.monotonic())
            ):
                raise OSError("process supervision subtree cleanup incomplete")
            if child.request_owned and not child.request_done.wait(
                max(0, group.cleanup_deadline - time.monotonic())
            ):
                raise OSError("process supervision request cleanup incomplete")
            if not child.cleanup_settled:
                raise OSError(
                    "process supervision subtree cleanup incomplete"
                ) from child.cleanup_error
            if child.cleanup_error is not None:
                if child.cleanup_settled:
                    child.delivery_done.wait(
                        max(0, group.cleanup_deadline - time.monotonic())
                    )
                with self.lock:
                    if child not in group.children:
                        continue
                raise OSError(
                    "process supervision subtree cleanup failed"
                ) from child.cleanup_error

    def _complete_cleanup(self, group: _Group) -> None:
        with self.lock:
            group.cleanup_done.set()
            # Retain failures for the ancestor to observe, including failures
            # that finished before its snapshot. Successful children may detach.
            if (
                group.cleanup_settled
                and group.cleanup_error is None
                and group.parent is not None
                and not group.request_owned
            ):
                group.parent.children.discard(group)

    def _acknowledge(self, group: _Group, token: str, receipt: str) -> None:
        # The same authenticated connection carries an exact terminal-frame
        # digest. This grants no allocation or signal authority. Revocation and
        # acceptance are ordered under the allocation lock; waits stay outside.
        with self.lock:
            parent = group.parent
            if (
                parent is not None
                and not self.closed
                and parent in self.groups
                and self.scopes.get(token) is parent
                and not parent.expired.is_set()
                and group.terminal_receipt is not None
                and receipt == group.terminal_receipt
                and group.cleanup_done.is_set()
                and group.cleanup_settled
                and group.request_done.is_set()
            ):
                parent.children.discard(group)
                group.delivery_done.set()

    def _scope(self, token: str) -> _Group:
        with self.lock:
            group = self.scopes.get(token)
            if self.closed or group is None or group not in self.groups:
                raise ValueError("inactive process supervision scope")
            return group

    def abort(self) -> None:
        with self.lock:
            self.closed = True
            for group in tuple(self.groups):
                self.release(group, cancelled=True)

    def close(self) -> None:
        self.abort()
        failures: list[BaseException] = []
        try:
            self.listener.close()
        except OSError as error:
            failures.append(error)
        with self.lock:
            for connection in tuple(self.connections):
                with contextlib.suppress(OSError):
                    connection.shutdown(socket.SHUT_RDWR)
                try:
                    connection.close()
                except OSError as error:
                    failures.append(error)
        deadline = self.cleanup_deadline or time.monotonic() + _REAP_TIMEOUT_S
        with self.lock:
            workers = tuple(self.workers)
        for worker in (self.server, *workers):
            try:
                worker.join(timeout=max(0, deadline - time.monotonic()))
            except (OSError, RuntimeError) as error:
                failures.append(error)
        if self.server.is_alive() or any(worker.is_alive() for worker in workers):
            failures.append(
                OSError("process supervision workers did not finish bounded cleanup")
            )
        else:
            try:
                self.directory.cleanup()
            except OSError as error:
                failures.append(error)
        if failures:
            failure = OSError(str(failures[0]))
            for diagnostic in failures:
                _note(failure, f"{type(diagnostic).__name__}: {diagnostic}")
            raise failure from failures[0]

    def _serve(self) -> None:
        while not self.closed:
            try:
                connection, _ = self.listener.accept()
            except TimeoutError:
                continue
            except OSError:
                return
            with self.lock:
                if self.closed:
                    connection.close()
                    return
                self.connections.add(connection)
            worker = threading.Thread(
                target=lambda c=connection: self._request(c), daemon=True
            )
            with self.lock:
                self.workers.add(worker)
            worker.start()

    def _request(self, connection: socket.socket) -> None:
        descriptors: list[int] = []
        group: _Group | None = None
        acknowledgment: Any = None

        def registered(value: _Group) -> None:
            nonlocal group
            group = value
            group.request_owned = True

        try:
            connection.settimeout(_CHANNEL_TIMEOUT_S)
            header, descriptors, flags, _ = socket.recv_fds(connection, 4, 3)
            for descriptor in descriptors:
                os.set_inheritable(descriptor, False)
            if flags & socket.MSG_CTRUNC:
                raise ValueError("truncated process supervision descriptors")
            request = _read_frame(connection, header)
            if (
                not isinstance(request, dict)
                or set(request)
                != {"token", "command", "cwd", "env", "timeout", "capture"}
                or not isinstance(request["token"], str)
                or not isinstance(request["command"], list)
                or not request["command"]
                or any(type(v) is not str for v in request["command"])
                or type(request["cwd"]) is not str
                or not isinstance(request["env"], dict)
                or any(
                    type(k) is not str or type(v) is not str
                    for k, v in request["env"].items()
                )
                or type(request["capture"]) is not bool
                or not _valid_timeout(request["timeout"])
            ):
                raise ValueError("invalid process supervision request")
            if len(descriptors) != (1 if request["capture"] else 3):
                raise ValueError("invalid process supervision descriptors")
            parent = self._scope(request["token"])
            connection.settimeout(_REAP_TIMEOUT_S)

            def forward(name: str, data: bytes) -> None:
                _send_frame(
                    connection,
                    {
                        "kind": "stream",
                        "pipe": name,
                        "data": base64.b64encode(data).decode("ascii"),
                    },
                )

            # Inherited descriptors belong to the requesting caller. Captured
            # streams travel as bounded raw-byte frames, never one giant result.
            result = self.run(
                request["command"],
                cwd=request["cwd"],
                env=request["env"],
                timeout=request["timeout"],
                capture=request["capture"],
                root=False,
                parent=parent,
                forward=forward if request["capture"] else None,
                stdin=descriptors[0],
                output_fds=None
                if request["capture"]
                else (descriptors[1], descriptors[2]),
                registered=registered,
            )
            response = {
                "kind": "completed",
                "returncode": result.returncode,
                "stdout_bytes": len(result.stdout) if request["capture"] else 0,
                "stderr_bytes": len(result.stderr) if request["capture"] else 0,
            }
        except subprocess.TimeoutExpired as error:
            response = {
                "kind": "timeout",
                "timeout": error.timeout,
                "stdout_bytes": len(error.output) if error.output else 0,
                "stderr_bytes": len(error.stderr) if error.stderr else 0,
            }
        except OSError as error:
            response = {"kind": "oserror", "error": [error.errno, str(error)]}
        except (ValueError, TypeError, KeyError, RecursionError) as error:
            response = {"kind": "error", "error": str(error)}
        try:
            # A one-use challenge and digest bind receipt to this connection's
            # exact request and terminal response, including partial lengths.
            if group is not None:
                response.update(group.stream_sizes)
                response["diagnostics"] = [
                    f"{type(error).__name__}: {error}" for error in group.cleanup_errors
                ]
                response["receipt"] = secrets.token_hex(32)
                group.terminal_receipt = hashlib.sha256(
                    _frame_bytes(response)
                ).hexdigest()
                ack_parent = group.parent
                assert ack_parent is not None
                # An active caller may acknowledge during its operation. There
                # is no new cleanup allowance: close interrupts this read and
                # the ancestor barrier uses its original shared deadline.
                deadline = ack_parent.cleanup_deadline
                if deadline is None and ack_parent.request_deadline is not None:
                    deadline = ack_parent.request_deadline + _REAP_TIMEOUT_S
                connection.settimeout(
                    None if deadline is None else max(0, deadline - time.monotonic())
                )
            _send_frame(connection, response)
            if group is not None:
                acknowledgment = _read_frame(connection)
        except (OSError, ValueError, TypeError, RecursionError) as error:
            if group is not None:
                group.cleanup_errors.append(error)
        finally:
            for descriptor in descriptors:
                try:
                    os.close(descriptor)
                except OSError as error:
                    if group is not None:
                        group.cleanup_settled = False
                        group.cleanup_errors.append(error)
                        group.cleanup_error = group.cleanup_error or error
            with self.lock:
                # Closing a socket is not a wait. Peer EOF and the subsequent
                # acknowledgment decision share the revocation critical section:
                # the caller can finish only after request resources finalize,
                # and its ancestor cannot revoke between close and acceptance.
                try:
                    connection.close()
                except OSError as error:
                    if group is not None:
                        group.cleanup_settled = False
                        group.cleanup_errors.append(error)
                        group.cleanup_error = group.cleanup_error or error
                self.connections.discard(connection)
                self.workers.discard(threading.current_thread())
                if group is not None:
                    group.request_done.set()
                    valid_ack = (
                        isinstance(acknowledgment, dict)
                        and set(acknowledgment) == {"kind", "token", "receipt"}
                        and acknowledgment["kind"] == "ack"
                        and acknowledgment["token"] == request["token"]
                        and acknowledgment["receipt"] == group.terminal_receipt
                    )
                    if valid_ack:
                        self._acknowledge(
                            group, request["token"], acknowledgment["receipt"]
                        )
                    if not group.delivery_done.is_set() and not (
                        group.ancestor_cancelled
                        and group.expired.is_set()
                        and acknowledgment is None
                    ):
                        unacknowledged = OSError(
                            "process supervision terminal response unacknowledged"
                        )
                        group.cleanup_errors.append(unacknowledged)
                        group.cleanup_error = group.cleanup_error or unacknowledged
                    # Clean ancestor-induced cancellation needs no command
                    # acknowledgment from a dead caller. Settled errors always
                    # remain obligations unless authenticated acceptance won
                    # the race with revocation above.
                    if group.cleanup_settled and group.cleanup_error is None:
                        assert group.parent is not None
                        group.parent.children.discard(group)

    def run(
        self,
        command: Sequence[str],
        *,
        cwd: str | os.PathLike[str],
        env: Mapping[str, str],
        timeout: float | None,
        capture: bool,
        root: bool,
        parent: _Group | None = None,
        forward: Callable[[str, bytes], None] | None = None,
        stdin: int | None = None,
        output_fds: tuple[int, int] | None = None,
        registered: Callable[[_Group], None] | None = None,
    ) -> subprocess.CompletedProcess[Any]:
        deadline = None if timeout is None else time.monotonic() + timeout
        with self.lock:
            if self.closed:
                raise subprocess.TimeoutExpired(
                    list(command),
                    timeout if timeout is not None else _REAP_TIMEOUT_S,
                )
            if (root and parent is not None) or (
                not root
                and (
                    parent is None
                    or parent not in self.groups
                    or self.scopes.get(parent.scope_token) is not parent
                )
            ):
                raise ValueError("inactive process supervision scope")
            scope_token = secrets.token_hex(32)
            if scope_token in self.issued_tokens:
                raise OSError("process supervision scope capability collision")
            self.issued_tokens.add(scope_token)
            local, child = socket.socketpair()
            child_environment = {
                **env,
                _SOCKET_ENV: self.address,
                _TOKEN_ENV: scope_token,
            }
            try:
                process = subprocess.Popen(
                    [
                        sys.executable,
                        "-I",
                        "-S",
                        "-c",
                        _GUARD_PROGRAM,
                        str(child.fileno()),
                    ],
                    cwd=str(cwd),
                    env=child_environment,
                    stdin=stdin,
                    stdout=subprocess.PIPE
                    if capture
                    else (output_fds[0] if output_fds else None),
                    stderr=subprocess.PIPE
                    if capture
                    else (output_fds[1] if output_fds else None),
                    start_new_session=True,
                    pass_fds=(child.fileno(),),
                )
                group = _Group(process, local, scope_token=scope_token, parent=parent)
                group.request_deadline = deadline
                self.groups.add(group)
                self.scopes[scope_token] = group
                if parent is not None:
                    parent.children.add(group)
                if registered is not None:
                    registered(group)
            except BaseException:
                local.close()
                child.close()
                raise
        child.close()

        def outcome() -> None:
            try:
                payload = _read_frame(local)
                if not isinstance(payload, dict) or set(payload) not in (
                    {"returncode"},
                    {"oserror"},
                ):
                    raise ValueError("invalid process guard outcome")
                group.outcome = payload
            except (OSError, ValueError, TypeError, RecursionError) as error:
                group.error = error
            finally:
                self.release(group)
                group.finished.set()
                if root:
                    self.abort()

        def watchdog() -> None:
            remaining = (
                None if deadline is None else max(0, deadline - time.monotonic())
            )
            if group.cancel.wait(remaining):
                return
            group.expired.set()
            if root:
                self.abort()
            else:
                self.release(group, cancelled=True)

        guard_reader = threading.Thread(target=outcome, daemon=True)
        timer = threading.Thread(target=watchdog, daemon=True)
        reader_started = False
        buffers = {"stdout": bytearray(), "stderr": bytearray()}
        streams = [p for p in (process.stdout, process.stderr) if p is not None]
        forward_error: OSError | None = None
        capture_complete = not capture
        timer_started = False
        try:
            timer.start()
            timer_started = True
            _send_frame(local, list(command))  # Register before actual tool launch.
            guard_reader.start()
            reader_started = True
            with selectors.DefaultSelector() as selector:
                for name, pipe in (
                    ("stdout", process.stdout),
                    ("stderr", process.stderr),
                ):
                    if pipe is not None:
                        os.set_blocking(pipe.fileno(), False)
                        selector.register(pipe, selectors.EVENT_READ, name)
                while True:
                    now = time.monotonic()
                    if (
                        deadline is not None
                        and now >= deadline
                        and not group.cancel.is_set()
                    ):
                        group.expired.set()
                        if root:
                            self.abort()
                        else:
                            self.release(group, cancelled=True)
                    if group.finished.is_set() and not selector.get_map():
                        capture_complete = True
                        break
                    if (
                        group.cleanup_deadline is not None
                        and now >= group.cleanup_deadline
                    ):
                        group.expired.set()  # Reject incomplete held-pipe capture.
                        break
                    if not selector.get_map():
                        group.finished.wait(0.01)
                        continue
                    for key, _ in selector.select(0.01):
                        chunk = os.read(key.fd, 65536)
                        if chunk:
                            buffers[key.data].extend(chunk)
                            if forward is not None:
                                try:
                                    forward(key.data, chunk)
                                except OSError as error:
                                    forward_error = error
                                    forward = None
                                    self.release(group)
                                    # Continue reading broker-owned pipes to EOF;
                                    # failed caller transport is not drain evidence.
                        else:
                            selector.unregister(key.fileobj)
            self.release(group)
            if forward_error is not None:
                raise forward_error
            if group.expired.is_set():
                raise subprocess.TimeoutExpired(
                    list(command),
                    timeout if timeout is not None else _REAP_TIMEOUT_S,
                    output=bytes(buffers["stdout"]),
                    stderr=bytes(buffers["stderr"]),
                )
            if group.error is not None:
                raise OSError(
                    "process guard closed without a complete outcome"
                ) from group.error
            assert group.outcome is not None
            if "oserror" in group.outcome:
                number, message, filename = group.outcome["oserror"]
                raise OSError(number, message, filename)
            return subprocess.CompletedProcess(
                list(command),
                group.outcome["returncode"],
                (
                    bytes(buffers["stdout"])
                    if forward
                    else _text(bytes(buffers["stdout"]))
                )
                if capture
                else None,
                (
                    bytes(buffers["stderr"])
                    if forward
                    else _text(bytes(buffers["stderr"]))
                )
                if capture
                else None,
            )
        except OSError:
            if group.expired.is_set():
                raise subprocess.TimeoutExpired(
                    list(command),
                    timeout if timeout is not None else _REAP_TIMEOUT_S,
                    output=bytes(buffers["stdout"]) if capture else None,
                    stderr=bytes(buffers["stderr"]) if capture else None,
                ) from None
            raise
        finally:
            primary = sys.exc_info()[1]
            self.release(group)
            assert group.cleanup_deadline is not None

            def remaining() -> float:
                assert group.cleanup_deadline is not None
                return max(0, group.cleanup_deadline - time.monotonic())

            failures = group.cleanup_errors
            try:
                process.wait(timeout=remaining())
            except (OSError, subprocess.TimeoutExpired) as error:
                failures.append(error)
            settled = process.returncode is not None
            if not settled:
                failures.append(OSError("process supervision guard cleanup incomplete"))
            if local.fileno() != -1:
                settled = False
                failures.append(
                    OSError("process supervision guard channel cleanup incomplete")
                )
            group.cancel.set()
            for thread, started, name in (
                (timer, timer_started, "timer"),
                (guard_reader, reader_started, "reader"),
            ):
                if started:
                    try:
                        thread.join(timeout=remaining())
                    except (OSError, RuntimeError) as error:
                        failures.append(error)
                    if thread.is_alive():
                        settled = False
                        failures.append(
                            OSError(f"process supervision {name} cleanup incomplete")
                        )
            if not capture_complete:
                failures.append(
                    OSError("process supervision capture cleanup incomplete")
                )
            if forward_error is not None:
                failures.append(forward_error)
            try:
                self._await_children(group)
            except OSError as error:
                settled = False
                failures.append(error)
            for stream in streams:
                try:
                    stream.close()
                except OSError as error:
                    failures.append(error)
                if not stream.closed:
                    settled = False
                    failures.append(
                        OSError("process supervision stream cleanup incomplete")
                    )
            group.cleanup_settled = settled
            group.stream_sizes = {
                f"{name}_bytes": len(data) for name, data in buffers.items()
            }
            failure = OSError(str(failures[0])) if failures else None
            if failure is not None:
                for diagnostic in failures:
                    _note(failure, f"{type(diagnostic).__name__}: {diagnostic}")
                failure.__cause__ = failures[0]
            group.cleanup_error = failure
            group.command_error = primary or failure
            self._complete_cleanup(group)
            if failure is not None:
                if primary is not None:
                    for diagnostic in failures:
                        _note(
                            primary,
                            f"cleanup: {type(diagnostic).__name__}: {diagnostic}",
                        )
                else:
                    raise failure


def _remote(
    command: Sequence[str],
    *,
    cwd: str | os.PathLike[str],
    env: Mapping[str, str],
    timeout: float | None,
    capture: bool,
) -> subprocess.CompletedProcess[Any]:
    with _remote_channel() as channel:
        channel.settimeout(_CHANNEL_TIMEOUT_S)
        channel.connect(os.environ[_SOCKET_ENV])
        frame = _frame_bytes(
            {
                "token": os.environ[_TOKEN_ENV],
                "command": list(command),
                "cwd": os.fspath(cwd),
                "env": dict(env),
                "timeout": timeout,
                "capture": capture,
            },
        )
        # SCM_RIGHTS duplicates only the caller's inherited standard streams;
        # it grants no PID or signal authority to the broker client.
        sent = socket.send_fds(channel, [frame], [0] if capture else [0, 1, 2])
        if sent < len(frame):  # An empty send to a rejecting peer raises EPIPE.
            channel.sendall(frame[sent:])
        channel.settimeout(
            None if timeout is None else max(0.001, timeout) + 2 * _REAP_TIMEOUT_S
        )
        buffers = {"stdout": bytearray(), "stderr": bytearray()}
        try:
            while True:
                result = _read_frame(channel)
                if not isinstance(result, dict) or result.get("kind") != "stream":
                    break
                if (
                    not capture
                    or set(result) != {"kind", "pipe", "data"}
                    or type(result["pipe"]) is not str
                    or result["pipe"] not in buffers
                    or type(result["data"]) is not str
                ):
                    raise OSError("invalid process supervision stream")
                name = result["pipe"]
                try:
                    buffers[name].extend(
                        base64.b64decode(result["data"], validate=True)
                    )
                except ValueError as error:
                    raise OSError("invalid process supervision stream bytes") from error
        except TimeoutError:
            raise subprocess.TimeoutExpired(
                list(command),
                timeout if timeout is not None else _REAP_TIMEOUT_S,
                output=bytes(buffers["stdout"]) if capture else None,
                stderr=bytes(buffers["stderr"]) if capture else None,
            ) from None
        if not isinstance(result, dict):
            raise OSError("invalid process supervision response")
        kind = result.get("kind")
        receipt = result.get("receipt")
        sizes = {"stdout_bytes", "stderr_bytes"}
        fields = {
            "completed": {"returncode"},
            "timeout": {"timeout"},
            "oserror": {"error"},
            "error": {"error"},
        }
        if type(kind) is not str or kind not in fields:
            raise OSError("invalid process supervision response")
        # Rejections before allocation carry no receipt and cannot acknowledge
        # a child. Every allocated terminal result includes exact stream sizes.
        if kind == "error" and receipt is None:
            if set(result) != {"kind", "error"} or type(result["error"]) is not str:
                raise OSError("invalid process supervision rejection")
            raise OSError("process supervision request rejected")
        if (
            type(receipt) is not str
            or len(receipt) != 64
            or any(c not in "0123456789abcdef" for c in receipt)
            or set(result) != {"kind", "receipt", "diagnostics"} | sizes | fields[kind]
            or not isinstance(result["diagnostics"], list)
            or any(type(note) is not str for note in result["diagnostics"])
        ):
            raise OSError("invalid process supervision response")
        _check_stream_sizes(result, buffers)
        if kind == "completed":
            if type(result["returncode"]) is not int:
                raise OSError("invalid process supervision return code")
            # Decode before acknowledging; invalid text is not validated receipt.
            completed = subprocess.CompletedProcess(
                list(command),
                result["returncode"],
                _text(bytes(buffers["stdout"])) if capture else None,
                _text(bytes(buffers["stderr"])) if capture else None,
            )
            terminal_error: BaseException | None = None
        elif kind == "timeout":
            if result["timeout"] is None or not _valid_timeout(result["timeout"]):
                raise OSError("invalid process supervision timeout")
            if result["timeout"] != (
                timeout if timeout is not None else _REAP_TIMEOUT_S
            ):
                raise OSError("process supervision timeout does not match request")
            terminal_error = subprocess.TimeoutExpired(
                list(command),
                result["timeout"],
                output=bytes(buffers["stdout"]) if capture else None,
                stderr=bytes(buffers["stderr"]) if capture else None,
            )
        elif kind == "oserror":
            remote_error = result["error"]
            if (
                not isinstance(remote_error, list)
                or len(remote_error) != 2
                or (remote_error[0] is not None and type(remote_error[0]) is not int)
                or type(remote_error[1]) is not str
            ):
                raise OSError("invalid process supervision error")
            terminal_error = OSError(*remote_error)
        else:
            if type(result["error"]) is not str:
                raise OSError("invalid process supervision error")
            terminal_error = OSError("process supervision request rejected")
        if terminal_error is not None:
            for note in result["diagnostics"]:
                _note(terminal_error, f"cleanup: {note}")
        try:
            _send_frame(
                channel,
                {
                    "kind": "ack",
                    "token": os.environ[_TOKEN_ENV],
                    "receipt": hashlib.sha256(_frame_bytes(result)).hexdigest(),
                },
            )
            if channel.recv(1) != b"":
                raise OSError("invalid process supervision acknowledgment completion")
        except OSError as error:
            if terminal_error is None:
                raise
            _note(terminal_error, f"terminal acknowledgment: {error}")
        if terminal_error is not None:
            raise terminal_error
        return completed


def _check_stream_sizes(
    result: Mapping[str, Any], buffers: Mapping[str, bytearray]
) -> None:
    for name in ("stdout", "stderr"):
        size = result.get(f"{name}_bytes")
        if type(size) is not int or size != len(buffers[name]):
            raise OSError("incomplete process supervision stream")


@overload
def run_process_group(
    command: Sequence[str],
    *,
    cwd: str | os.PathLike[str],
    env: Mapping[str, str] | None = ...,
    timeout: float | None,
    check: bool = ...,
    capture: Literal[True] = ...,
) -> subprocess.CompletedProcess[str]: ...


@overload
def run_process_group(
    command: Sequence[str],
    *,
    cwd: str | os.PathLike[str],
    env: Mapping[str, str] | None = ...,
    timeout: float | None,
    check: bool = ...,
    capture: Literal[False],
) -> subprocess.CompletedProcess[None]: ...


def run_process_group(
    command: Sequence[str],
    *,
    cwd: str | os.PathLike[str],
    env: Mapping[str, str] | None = None,
    timeout: float | None,
    check: bool = False,
    capture: bool = True,
) -> subprocess.CompletedProcess[str] | subprocess.CompletedProcess[None]:
    """Run an owned command and preserve text, check and typed timeout semantics.

    Cooperative nested helpers receive bounded subtree cleanup. Capture EOF
    and trusted guards do not prove arbitrary descendants' kernel death.
    Unregistered detached sessions and non-POSIX descendants are not claimed.
    """
    if not _valid_timeout(timeout):
        raise ValueError("process timeout must be None or finite and positive")
    environment = dict(os.environ if env is None else env)
    lease = (_SOCKET_ENV in os.environ, _TOKEN_ENV in os.environ)
    if any(lease):
        if not all(lease) or os.name != "posix":
            raise OSError("incomplete or unsupported process supervision lease")
        result = _remote(
            command, cwd=cwd, env=environment, timeout=timeout, capture=capture
        )
    elif os.name == "posix":
        broker = _Broker()
        try:
            result = broker.run(
                command,
                cwd=cwd,
                env=environment,
                timeout=timeout,
                capture=capture,
                root=True,
            )
        finally:
            primary = sys.exc_info()[1]
            try:
                broker.close()
            except OSError as error:
                if primary is None:
                    raise
                _note(primary, f"broker close: {type(error).__name__}: {error}")
    else:
        # Direct-child only; no POSIX/cooperative-descendant guarantee.
        process = subprocess.Popen(
            list(command),
            cwd=str(cwd),
            env=environment,
            text=True,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.PIPE if capture else None,
        )
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            with contextlib.suppress(subprocess.TimeoutExpired):
                process.communicate(timeout=_REAP_TIMEOUT_S)
            raise
        finally:
            if process.stdout is not None:
                process.stdout.close()
            if process.stderr is not None:
                process.stderr.close()
        result = subprocess.CompletedProcess(
            list(command), process.returncode, stdout, stderr
        )
    if check and result.returncode:
        raise subprocess.CalledProcessError(
            result.returncode, list(command), output=result.stdout, stderr=result.stderr
        )
    return result
