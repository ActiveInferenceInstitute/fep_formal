"""Shared lake executable resolution for native formalism boundary tests."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest


def lake_executable() -> str:
    lake = shutil.which("lake")
    if lake is None:
        candidate = Path.home() / ".elan" / "bin" / "lake"
        if candidate.is_file():
            lake = str(candidate)
    if lake is None:
        pytest.skip("lake is required for native formalism boundary tests")
    return lake
