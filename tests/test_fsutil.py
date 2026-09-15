"""Gates for the shared output-plane filesystem primitives (fsutil)."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pytest

from fep_lean.bridge.custody import write_text
from fep_lean.output.fsutil import (
    SHA256_HEX_RE,
    atomic_write_bytes,
    atomic_write_text,
    sha256_bytes,
    sha256_file,
    write_json,
)


def test_atomic_write_bytes_round_trips(tmp_path: Path) -> None:
    target = tmp_path / "blob.bin"
    atomic_write_bytes(target, b"\x00\xffpayload")
    assert target.read_bytes() == b"\x00\xffpayload"


def test_atomic_write_text_encodes_utf8(tmp_path: Path) -> None:
    target = tmp_path / "note.txt"
    atomic_write_text(target, "café ☃\n")
    assert target.read_text(encoding="utf-8") == "café ☃\n"


def test_atomic_write_creates_missing_parent_dirs(tmp_path: Path) -> None:
    target = tmp_path / "a" / "b" / "c.txt"
    atomic_write_text(target, "nested\n")
    assert target.read_text(encoding="utf-8") == "nested\n"


def test_failed_replace_leaves_target_untouched(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "keep.txt"
    atomic_write_text(target, "original\n")
    before = target.read_text(encoding="utf-8")

    def boom(src: object, dst: object) -> None:
        raise OSError("replace exploded")

    monkeypatch.setattr(os, "replace", boom)
    with pytest.raises(OSError, match="replace exploded"):
        atomic_write_text(target, "replacement\n")

    assert target.read_text(encoding="utf-8") == before
    # The failed temp file is cleaned up, not left as litter.
    assert [p.name for p in tmp_path.iterdir()] == ["keep.txt"]


def test_failed_write_body_leaves_target_untouched(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "keep.bin"
    atomic_write_bytes(target, b"original")

    def explode(handle: object) -> None:
        raise OSError("write exploded")

    real_fdopen = os.fdopen

    def exploding_fdopen(fd: int, *args: object, **kwargs: object) -> object:
        handle = real_fdopen(fd, "wb")
        handle.write = explode  # type: ignore[assignment]
        return handle

    monkeypatch.setattr(os, "fdopen", exploding_fdopen)
    with pytest.raises(OSError, match="write exploded"):
        atomic_write_bytes(target, b"replacement")

    assert target.read_bytes() == b"original"
    assert [p.name for p in tmp_path.iterdir()] == ["keep.bin"]


def test_write_json_is_canonical_and_sorted(tmp_path: Path) -> None:
    target = tmp_path / "data.json"
    write_json(target, {"b": 1, "a": [2, 3]})
    assert (
        target.read_text(encoding="utf-8")
        == '{\n  "a": [\n    2,\n    3\n  ],\n  "b": 1\n}\n'
    )


def test_write_json_rejects_nan(tmp_path: Path) -> None:
    target = tmp_path / "data.json"
    with pytest.raises(ValueError, match="Out of range"):
        write_json(target, {"x": float("nan")})
    assert not target.exists()


def test_write_json_rejects_inf(tmp_path: Path) -> None:
    target = tmp_path / "data.json"
    with pytest.raises(ValueError, match="Out of range"):
        write_json(target, [float("inf")])
    assert not target.exists()


def test_custody_write_text_short_circuits_unchanged_content(
    tmp_path: Path,
) -> None:
    """The load-bearing guard: unchanged bytes keep the on-disk mtime."""
    target = tmp_path / "out.txt"
    write_text(target, "same\n")
    os.utime(target, ns=(1_000_000_000, 1_000_000_000))

    write_text(target, "same\n")

    assert os.stat(target).st_mtime_ns == 1_000_000_000


def test_custody_write_text_replaces_changed_content(tmp_path: Path) -> None:
    target = tmp_path / "out.txt"
    write_text(target, "before\n")
    os.utime(target, ns=(1_000_000_000, 1_000_000_000))

    write_text(target, "after\n")

    assert target.read_text(encoding="utf-8") == "after\n"
    assert os.stat(target).st_mtime_ns != 1_000_000_000


def test_custody_write_text_refuses_symlink(tmp_path: Path) -> None:
    real = tmp_path / "real.txt"
    real.write_text("real\n", encoding="utf-8")
    link = tmp_path / "link.txt"
    link.symlink_to(real)

    with pytest.raises(ValueError, match="symlink"):
        write_text(link, "overwrite\n")

    assert real.read_text(encoding="utf-8") == "real\n"


def test_sha256_bytes_matches_reference() -> None:
    digest = sha256_bytes(b"fep_lean")
    assert SHA256_HEX_RE.fullmatch(digest) is not None
    assert digest == hashlib.sha256(b"fep_lean").hexdigest()


def test_sha256_file_digests_and_reports_absent_as_empty(tmp_path: Path) -> None:
    target = tmp_path / "blob.bin"
    target.write_bytes(b"fep_lean")
    assert sha256_file(target) == sha256_bytes(b"fep_lean")
    assert sha256_file(tmp_path / "absent.bin") == ""
