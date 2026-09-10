"""Shared Lean toolchain path resolution helpers.

Both ``lean_verifier.py`` and ``environment.py`` need to locate the Lean/Lake
binaries and set up a writable ELAN_HOME for sandboxed environments.  This
module provides the common primitives so the resolution logic is defined once.
"""

from __future__ import annotations

import contextlib
import json
import os
import re
import shutil
import tempfile
from pathlib import Path

_PINNED_LEAN_VERSION_RE = re.compile(r"^leanprover/lean4:v(?P<version>\d+\.\d+\.\d+)$")
_ACTUAL_LEAN_VERSION_RE = re.compile(
    r"^Lean(?:\s+\(|\s+)version\s+(?P<version>\d+\.\d+\.\d+)(?:[,)]|$)"
)
_MATHLIB_TAG_RE = re.compile(r"^v(?P<version>\d+\.\d+\.\d+)$")
_MATHLIB_DEPENDENCY_RE = re.compile(r'mathlib4\.git"\s*@\s*"(?P<tag>v\d+\.\d+\.\d+)"')


def pinned_lean_semver(toolchain: str) -> str | None:
    """Extract the semantic version from a canonical Lean toolchain name."""
    match = _PINNED_LEAN_VERSION_RE.fullmatch(toolchain.strip())
    return match.group("version") if match else None


def actual_lean_semver(version_output: str) -> str | None:
    """Extract the semantic version from the first ``lean --version`` line."""
    first_line = (
        version_output.strip().splitlines()[0] if version_output.strip() else ""
    )
    match = _ACTUAL_LEAN_VERSION_RE.match(first_line)
    return match.group("version") if match else None


def lean_version_matches_pin(version_output: str, toolchain: str) -> bool:
    """Return whether recorded compiler output identifies the pinned version."""
    pinned = pinned_lean_semver(toolchain)
    actual = actual_lean_semver(version_output)
    return pinned is not None and actual == pinned


def read_toolchain_pin(lean_dir: Path) -> str | None:
    """Return the validated canonical toolchain pin from a Lean workspace."""
    try:
        raw = (Path(lean_dir) / "lean-toolchain").read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError):
        return None
    return raw if pinned_lean_semver(raw) is not None else None


def read_mathlib_tag(lean_dir: Path) -> str | None:
    """Return the validated Mathlib release tag from ``lakefile.lean``."""
    try:
        source = (Path(lean_dir) / "lakefile.lean").read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    matches = [match.group("tag") for match in _MATHLIB_DEPENDENCY_RE.finditer(source)]
    if len(matches) != 1 or _MATHLIB_TAG_RE.fullmatch(matches[0]) is None:
        return None
    return matches[0]


def resolved_mathlib_revision(lean_dir: Path) -> str:
    """Return the exact Mathlib Git revision recorded by Lake."""
    path = Path(lean_dir) / "lake-manifest.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return ""
    packages = payload.get("packages", []) if isinstance(payload, dict) else []
    if not isinstance(packages, list):
        return ""
    revisions = [
        package.get("rev")
        for package in packages
        if isinstance(package, dict) and package.get("name") == "mathlib"
    ]
    if len(revisions) != 1 or not isinstance(revisions[0], str):
        return ""
    revision = revisions[0]
    return revision if re.fullmatch(r"[0-9a-f]{40}", revision) else ""


def get_elan_home() -> Path:
    """Return the ELAN_HOME directory, respecting environment overrides."""
    return Path(os.environ.get("ELAN_HOME", str(Path.home() / ".elan")))


def get_elan_toolchains() -> Path:
    """Return ``<ELAN_HOME>/toolchains``."""
    return get_elan_home() / "toolchains"


def get_writable_elan_home() -> str:
    """Return a writable ELAN_HOME for sandboxed sub-processes.

    If ``ELAN_HOME`` is already set, returns that value. Otherwise falls back
    to a temp directory so the elan proxy can initialize without writing to
    ``~/.elan/settings.toml``.
    """
    if env := os.environ.get("ELAN_HOME"):
        return env
    return str(Path(tempfile.gettempdir()) / "fep_lean_elan")


def ensure_writable_elan_home() -> None:
    """Create the writable ELAN_HOME directory if it doesn't exist."""
    with contextlib.suppress(OSError):
        Path(get_writable_elan_home()).mkdir(parents=True, exist_ok=True)


def read_toolchain_name(lean_dir: Path) -> str | None:
    """Read ``lean-toolchain`` and return the elan-style toolchain name.

    E.g. ``leanprover/lean4:v4.33.1`` → ``leanprover--lean4---v4.33.1``.
    Returns ``None`` if the file is missing or malformed.
    """
    raw = read_toolchain_pin(lean_dir)
    if raw is None:
        return None
    return raw.replace("/", "--").replace(":", "---")


def find_toolchain_bin(lean_dir: Path | None = None) -> Path | None:
    """Return the ``bin/`` directory of the matching (or newest) toolchain.

    Resolution order:
      1. Match the name in ``lean-toolchain`` if *lean_dir* is given.
      2. Fall back to the newest toolchain in ``~/.elan/toolchains/``.

    All filesystem access is wrapped in try/except to handle macOS sandbox
    ``PermissionError`` when the agent shell cannot stat ``~/.elan``.
    """
    toolchains = get_elan_toolchains()
    try:
        if not toolchains.is_dir():
            return None
    except (OSError, PermissionError):
        return None

    if lean_dir:
        tc_name = read_toolchain_name(lean_dir)
        if tc_name:
            try:
                candidate = toolchains / tc_name / "bin"
                if candidate.is_dir():
                    return candidate
            except (OSError, PermissionError):
                pass

    try:
        candidates = sorted(
            (d / "bin" for d in toolchains.iterdir() if (d / "bin").is_dir()),
            key=lambda p: p.parent.stat().st_mtime,
            reverse=True,
        )
        return candidates[0] if candidates else None
    except (OSError, PermissionError):
        return None


def find_executable(name: str, lean_dir: Path | None = None) -> str | None:
    """Resolve a Lean/Lake executable using the pinned project toolchain.

    The elan proxy is not guaranteed to be on ``PATH`` in a fresh checkout,
    and the proxy may also try to write elan state before it can run.  Prefer
    the direct binary from the project's pinned toolchain, then honor the
    normal PATH and finally the elan proxy location.
    """
    explicit = os.environ.get(f"FEP_LEAN_{name.upper()}_EXE", "").strip()
    if explicit:
        return explicit if Path(explicit).is_file() else None

    toolchain_bin = find_toolchain_bin(lean_dir)
    if toolchain_bin:
        direct = toolchain_bin / name
        if direct.is_file():
            return str(direct)

    found = shutil.which(name)
    if found:
        return found

    elan_proxy = get_elan_home() / "bin" / name
    return str(elan_proxy) if elan_proxy.is_file() else None


def lake_version_matches_pin(version_output: str, toolchain: str) -> bool:
    """Return whether a ``lake --version`` line carries the pinned Lean version."""
    match = _ACTUAL_LEAN_VERSION_RE.match(version_output.strip().splitlines()[0] if version_output.strip() else "")
    return match is not None and f"v{match.group('version')}" in toolchain


def subprocess_env(lean_dir: Path | None = None) -> dict[str, str]:
    """Build an environment dict for lean/lake sub-processes.

    Sets ``ELAN_HOME`` to a writable location and optionally prepends the
    direct toolchain ``bin/`` to ``PATH``.
    """
    env = dict(os.environ)
    env["ELAN_HOME"] = get_writable_elan_home()
    ensure_writable_elan_home()

    tc_bin = find_toolchain_bin(lean_dir)
    if tc_bin:
        env["PATH"] = str(tc_bin) + ":" + env.get("PATH", "")

    return env
