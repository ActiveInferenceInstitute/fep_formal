"""Shared filesystem primitives for the output plane.

One atomic-write pair, one sha256 pair, and one hex-digest pattern replace the
five near-copies that drift began to accumulate across (SC-14): rendering,
reporter, release_bundle, manuscript, evidence, and browser_capture now import
from here. Public names only — the private cross-module imports SC-16 flagged
(``_atomic_text``) are retired.
"""

from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path

__all__ = [
    "SHA256_HEX_RE",
    "atomic_write_bytes",
    "atomic_write_text",
    "sha256_bytes",
    "sha256_file",
]

import re

SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")


def sha256_bytes(data: bytes) -> str:
    """Return the hex sha256 digest of ``data``."""
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    """Return the hex sha256 digest of a file, or the empty string if absent."""
    return sha256_bytes(path.read_bytes()) if Path(path).is_file() else ""


def atomic_write_bytes(path: Path, data: bytes) -> None:
    """Write ``data`` to ``path`` atomically (tempfile + fsync + rename)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, raw_path = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(raw_path, path)
    finally:
        if os.path.exists(raw_path):
            os.unlink(raw_path)


def atomic_write_text(path: Path, text: str) -> None:
    """Write ``text`` to ``path`` atomically (tempfile + fsync + rename)."""
    atomic_write_bytes(path, text.encode("utf-8"))
