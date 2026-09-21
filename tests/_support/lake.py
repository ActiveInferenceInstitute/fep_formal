"""Shared lake executable resolution with the two deliberate missing-tool stances."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Literal

import pytest


def lake_executable(
    *,
    missing: Literal["skip", "raise"] = "skip",
    context: str = "native formalism boundary tests",
) -> str:
    """Resolve ``lake`` from PATH or ``~/.elan/bin``.

    Missing-tool stance is deliberate per test file (see ``tests/conftest.py``):
    ``missing="skip"`` for boundary probes, ``missing="raise"`` (RuntimeError,
    fail closed) for acceptance probes. ``context`` completes the historical
    per-file message ``lake is required for <context>``; the defaults reproduce
    the original boundary-probe behavior verbatim.
    """
    lake = shutil.which("lake")
    if lake is None:
        candidate = Path.home() / ".elan" / "bin" / "lake"
        if candidate.is_file():
            lake = str(candidate)
    if lake is None:
        if missing == "skip":
            pytest.skip(f"lake is required for {context}")
        raise RuntimeError(f"lake is required for {context}")
    return lake
