"""Hermetic project-fixture knobs for the custody apply tests.

Every drift injection in this module lands on ``tmp_path`` copies. The
fixture root assembles a byte-identical projection of every repo file the
H2.7 custody surface hashes (the native plane roster, ``PIN_FILES``,
``MANDATORY_TEST_FILES``, and the non-specs ``CURRENT_FILES`` members) plus a
full ``specs/`` copy, following the evidence-fixture pattern in
``tests/test_custody_census.py`` (``_evidence_tree``). Census and apply then
run entirely against the fixture — the live repo tree is never a write
target, and gate verdicts derive from ``census``/``verify`` over the same
fixture tree instead of being keyed to live custody state.

Drift markers are appended to Python surfaces only: mutating a
``lean/FepSketches`` mirror without its ``src/fep_lean/formal`` twin trips
the validator's formal-projection drift check, which would classify the
whole native plane as broken rather than stale. Receipt JSON is drifted with
whitespace only, so the recorded digest drifts while the payload stays
parseable.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from fep_lean.verification.horizon_acceptance import (
    CURRENT_FILES,
    MANDATORY_TEST_FILES,
    PIN_FILES,
    native_source_paths,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

PY_DRIFT_MARKER = b"\n# custody fixture drift\n"

JSON_WHITESPACE_DRIFT = b"\n"

# The fep-lean CLI validates its project root against these checkout-bound
# markers (src/fep_lean/_paths.py); the fixture root carries copies so the
# custody CLI subcommands dispatch instead of refusing the checkout check.
_CHECKOUT_ONLY_FILES = (
    "config/topics.yaml",
    "config/settings.yaml",
    "manuscript/config.yaml",
    "src/fep_lean/__init__.py",
)


def fixture_root(tmp_path: Path) -> Path:
    """Assemble the isolated project root under ``tmp_path``.

    The returned root contains ``specs/`` (staged wholesale) and byte-identical
    copies of every non-specs surface the custody chain reads, so
    ``apply_refresh(specs_dir, root, ...)`` and ``census(root/"specs", root)``
    behave exactly as they do against the live repo while remaining writable.
    """
    root = tmp_path / "project"
    shutil.copytree(REPO_ROOT / "src/fep_lean/formal", root / "src/fep_lean/formal")
    shutil.copytree(REPO_ROOT / "lean/FepSketches", root / "lean/FepSketches")
    paths = (
        set(PIN_FILES)
        | set(MANDATORY_TEST_FILES)
        | set(CURRENT_FILES)
        | set(_CHECKOUT_ONLY_FILES)
        | set(native_source_paths(REPO_ROOT))
        | {"pyproject.toml", "uv.lock"}
    )
    for relative in sorted(paths):
        if relative.startswith("specs/"):
            continue  # staged wholesale below; resolves via root/"specs"
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / relative, destination)
    shutil.copytree(REPO_ROOT / "specs", root / "specs")
    return root


def spec_path(root: Path, relative: str) -> Path:
    """Map a ``specs/...`` repo-relative path onto the fixture's staged copy."""
    assert relative.startswith("specs/")
    return root / "specs" / relative[len("specs/") :]


def drift_file(path: Path, marker: bytes = PY_DRIFT_MARKER) -> None:
    """Append ``marker`` to one fixture file; tmp copies only, never live."""
    path.write_bytes(path.read_bytes() + marker)
