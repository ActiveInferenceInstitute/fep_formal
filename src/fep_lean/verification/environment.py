"""Read-only capability validation for the standalone fep_lean project."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from fep_lean._paths import project_root as default_project_root
from fep_lean.gauss.cli import check_gauss_cli
from fep_lean.gauss.client import resolve_gauss_home
from fep_lean.verification._toolchain import (
    find_executable,
    find_toolchain_bin,
    get_writable_elan_home,
    lean_version_matches_pin,
    pinned_lean_semver,
    read_mathlib_tag,
    read_toolchain_pin,
    subprocess_env,
)

_BIB_ENTRY_RE = re.compile(
    r"(?m)^\s*@(?P<kind>[A-Za-z]+)\s*\{\s*(?P<key>[^,\s{}]+)\s*,"
)
CATALOGUE_VALIDATION_CHECK_NAMES: tuple[str, ...] = (
    "topics_yaml",
    "project_layout",
    "python_scientific_stack",
    "output_writable",
    "manuscript_config",
    "catalogue_loader",
    "references_bib",
)
FULL_VALIDATION_CHECK_NAMES: tuple[str, ...] = (
    *CATALOGUE_VALIDATION_CHECK_NAMES,
    "gauss_cli",
    "gauss_state",
    "toolchain_pin",
    "lean_cli",
    "lake_cli",
    "lean_workspace",
    "mathlib_built",
    "hermes_credentials",
)


def _get_elan_home() -> str:
    return get_writable_elan_home()


def _lean_subprocess_env() -> dict[str, str]:
    return subprocess_env()


def _find_toolchain_lean(lean_dir: Path | None = None) -> str | None:
    toolchain = find_toolchain_bin(lean_dir)
    candidate = toolchain / "lean" if toolchain else None
    return str(candidate) if candidate and candidate.is_file() else None


def _version_line(exe: str, cwd: Path | None = None) -> tuple[bool, str]:
    try:
        proc = subprocess.run(
            [exe, "--version"],
            cwd=cwd,
            env=_lean_subprocess_env(),
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)
    output = (proc.stdout or proc.stderr or "").strip().splitlines()
    return proc.returncode == 0, output[0] if output else f"{exe}: no version output"


def _check_lean_cli(project_root: Path | None = None) -> tuple[bool, str]:
    root = project_root if project_root is not None else default_project_root()
    lean_dir = root / "lean"
    toolchain = read_toolchain_pin(lean_dir)
    if toolchain is None:
        return False, "lean/lean-toolchain is missing or malformed"
    explicit = os.environ.get("FEP_LEAN_LEAN_EXE", "")
    lean = (
        explicit
        if explicit and Path(explicit).is_file()
        else _find_toolchain_lean(lean_dir) or shutil.which("lean")
    )
    if not lean:
        return False, "lean executable is unavailable"
    ok, line = _version_line(lean, lean_dir)
    if not ok:
        return False, f"lean invocation failed: {line}"
    if not lean_version_matches_pin(line, toolchain):
        expected = pinned_lean_semver(toolchain)
        return False, f"wrong Lean version: {line}; expected {expected}"
    return True, line


def _check_toolchain_pin(project_root: Path) -> tuple[bool, str]:
    lean_dir = project_root / "lean"
    toolchain = read_toolchain_pin(lean_dir)
    if toolchain is None:
        return False, "lean/lean-toolchain is missing or malformed"
    mathlib_tag = read_mathlib_tag(lean_dir)
    if mathlib_tag is None:
        return False, "lean/lakefile.lean has no unique stable Mathlib release pin"
    lean_version = pinned_lean_semver(toolchain)
    if lean_version != mathlib_tag.removeprefix("v"):
        return (
            False,
            f"Lean {toolchain} and Mathlib {mathlib_tag} do not share a release",
        )
    return True, f"Lean {toolchain}; Mathlib {mathlib_tag}"


def _check_mathlib_built(project_root: Path) -> tuple[bool, str]:
    """Check the existing Mathlib build without downloading or compiling."""
    lean_root = project_root / "lean"
    build_roots = [
        lean_root / ".lake" / "build" / "lib" / "lean",
        # ``lake exe cache get`` materializes Mathlib's oleans in the
        # dependency workspace, while the project workspace contains the
        # FepSketches oleans that consume them.
        lean_root
        / ".lake"
        / "packages"
        / "mathlib"
        / ".lake"
        / "build"
        / "lib"
        / "lean",
    ]
    for build_root in build_roots:
        root_olean = build_root / "Mathlib.olean"
        required = (
            build_root / "Mathlib" / "MeasureTheory" / "Measure" / "MeasureSpace.olean"
        )
        if root_olean.is_file() and required.is_file():
            return True, f"Mathlib build present ({root_olean})"
    expected = build_roots[-1] / "Mathlib.olean"
    return False, f"Mathlib build artifact missing: {expected}"


def _check_lake(project_root: Path) -> tuple[bool, str]:
    lake_dir = project_root / "lean"
    toolchain = read_toolchain_pin(lake_dir)
    if toolchain is None:
        return False, "lean/lean-toolchain is missing or malformed"
    lake = find_executable("lake", lake_dir)
    if not lake:
        return False, "lake executable is unavailable"
    ok, line = _version_line(lake, lake_dir)
    if not ok:
        return False, f"lake invocation failed: {line}"
    expected = pinned_lean_semver(toolchain)
    if f"Lean version {expected}" not in line:
        return False, f"wrong Lake toolchain: {line}; expected Lean {expected}"
    return True, line


def _check_gauss_config(project_root: Path) -> tuple[bool, str]:
    configured = resolve_gauss_home(project_root)
    path = Path(configured).expanduser() if configured else Path.home() / ".gauss"
    parent = path if path.is_dir() else path.parent
    if not parent.is_dir():
        return False, f"OpenGauss state directory parent is missing: {parent}"
    if not os.access(parent, os.W_OK):
        return False, f"OpenGauss state directory is not writable: {path}"
    return True, f"OpenGauss state directory available: {path}"


def _check_topics_yaml(project_root: Path) -> tuple[bool, str]:
    try:
        from fep_lean.catalogue.topics import FEPTopicCatalogue

        catalogue = FEPTopicCatalogue.from_yaml(project_root / "config" / "topics.yaml")
    except Exception as exc:
        return False, str(exc)
    return True, f"topics.yaml validated ({len(catalogue.topics)} topics)"


def _check_dirs(project_root: Path) -> tuple[bool, str]:
    required = ("config", "docs", "src", "lean", "scripts", "tests")
    missing = [rel for rel in required if not (project_root / rel).is_dir()]
    return (
        not missing,
        f"missing {', '.join(missing)}" if missing else "project layout present",
    )


def _check_lean_workspace(project_root: Path) -> tuple[bool, str]:
    lean = project_root / "lean"
    if not (lean / "lakefile.lean").is_file():
        return False, "lean/lakefile.lean is missing"
    aggregate = lean / "FepSketches" / "fep_all.lean"
    if not aggregate.is_file():
        return False, "lean/FepSketches/fep_all.lean is missing"
    return True, "Lean workspace and canonical aggregate present"


def _check_python_stack() -> tuple[bool, str]:
    try:
        import matplotlib

        matplotlib.use("Agg")
    except Exception as exc:
        return False, str(exc)
    return (
        True,
        f"Python {sys.version_info.major}.{sys.version_info.minor}; scientific stack present",
    )


def _check_output_writable(project_root: Path) -> tuple[bool, str]:
    output = project_root / "output"
    parent = output if output.is_dir() else output.parent
    if not parent.is_dir():
        return False, f"output/ parent is missing: {parent}"
    if not os.access(parent, os.W_OK):
        return False, "output/ is not writable"
    return True, "output/ writable"


def _check_file(project_root: Path, relative: str) -> tuple[bool, str]:
    path = project_root / relative
    return (
        path.is_file(),
        f"{relative} present" if path.is_file() else f"{relative} missing",
    )


def _check_references_bib(project_root: Path) -> tuple[bool, str]:
    path = project_root / "docs" / "manuscript" / "references.bib"
    if not path.is_file():
        return False, "manuscript/references.bib is missing"
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return False, f"cannot read manuscript/references.bib: {exc}"
    if not text.strip():
        return False, "manuscript/references.bib is empty"

    # BibTeX permits nested braced values, so a mere entry-header match is not
    # enough: fail closed on any unmatched unescaped brace as well.
    depth = 0
    escaped = False
    for character in text:
        if escaped:
            escaped = False
            continue
        if character == "\\":
            escaped = True
        elif character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth < 0:
                return False, "manuscript/references.bib has an unmatched closing brace"
    if depth:
        return False, "manuscript/references.bib has an unmatched opening brace"

    matches = list(_BIB_ENTRY_RE.finditer(text))
    keys = [match.group("key") for match in matches]
    if not keys:
        return False, "manuscript/references.bib has no parseable BibTeX entries"
    duplicates = sorted({key for key in keys if keys.count(key) > 1})
    if duplicates:
        return False, "duplicate bibliography keys: " + ", ".join(duplicates)
    entry_lines = [line for line in text.splitlines() if line.lstrip().startswith("@")]
    if len(entry_lines) != len(matches):
        return False, "manuscript/references.bib has a malformed entry header"
    return True, f"references.bib validated ({len(keys)} unique entries)"


def _check_hermes_credentials() -> tuple[bool, str]:
    if not os.environ.get("OPENROUTER_API_KEY") and not os.environ.get(
        "ANTHROPIC_API_KEY"
    ):
        return (
            False,
            "OPENROUTER_API_KEY or ANTHROPIC_API_KEY is required for full mode",
        )
    return True, "Hermes credentials configured"


# Focused check functions remain available for direct unit coverage. The
# pipeline itself uses the mode-aware dispatcher below.
def _check_catalogue_import(project_root: Path) -> tuple[bool, str]:
    return _check_topics_yaml(project_root)


def _check_dot_gauss_writable(project_root: Path | None = None) -> tuple[bool, str]:
    return _check_gauss_config(project_root or Path.cwd())


def _check_python_numpy_matplotlib() -> tuple[bool, str]:
    return _check_python_stack()


def _check_manuscript_config(project_root: Path) -> tuple[bool, str]:
    return _check_file(project_root, "docs/manuscript/config.yaml")


def _check_scripts_tests(project_root: Path) -> tuple[bool, str]:
    return _check_dirs(project_root)


def run_validation_checks(project_root: Path, *, mode: str = "full") -> dict[str, Any]:
    """Run bounded, read-only checks for ``full`` or ``catalogue`` mode."""
    if mode not in {"full", "catalogue"}:
        raise ValueError(f"unsupported validation mode: {mode}")
    checks: list[dict[str, Any]] = []

    def run(name: str, fn: Callable[[], tuple[bool, str]]) -> None:
        started = time.perf_counter()
        try:
            ok, message = fn()
        except Exception as exc:
            ok, message = False, f"{type(exc).__name__}: {exc}"
        checks.append(
            {
                "name": name,
                "ok": ok,
                "message": message,
                "duration_s": round(time.perf_counter() - started, 4),
            }
        )

    catalogue_checks: tuple[tuple[str, Callable[[], tuple[bool, str]]], ...] = (
        ("topics_yaml", lambda: _check_topics_yaml(project_root)),
        ("project_layout", lambda: _check_dirs(project_root)),
        ("python_scientific_stack", _check_python_stack),
        ("output_writable", lambda: _check_output_writable(project_root)),
        (
            "manuscript_config",
            lambda: _check_file(project_root, "docs/manuscript/config.yaml"),
        ),
        ("catalogue_loader", lambda: _check_topics_yaml(project_root)),
        ("references_bib", lambda: _check_references_bib(project_root)),
    )
    assert tuple(name for name, _ in catalogue_checks) == (
        CATALOGUE_VALIDATION_CHECK_NAMES
    )
    for name, check in catalogue_checks:
        run(name, check)
    if mode == "full":
        full_only_checks: tuple[tuple[str, Callable[[], tuple[bool, str]]], ...] = (
            ("gauss_cli", lambda: check_gauss_cli(project_root, require=True)),
            ("gauss_state", lambda: _check_gauss_config(project_root)),
            ("toolchain_pin", lambda: _check_toolchain_pin(project_root)),
            ("lean_cli", lambda: _check_lean_cli(project_root)),
            ("lake_cli", lambda: _check_lake(project_root)),
            ("lean_workspace", lambda: _check_lean_workspace(project_root)),
            ("mathlib_built", lambda: _check_mathlib_built(project_root)),
            ("hermes_credentials", _check_hermes_credentials),
        )
        assert (
            tuple(name for name, _ in full_only_checks)
            == (FULL_VALIDATION_CHECK_NAMES[len(CATALOGUE_VALIDATION_CHECK_NAMES) :])
        )
        for name, check in full_only_checks:
            run(name, check)
    failed = [check for check in checks if not check["ok"]]
    return {
        "status": "ok" if not failed else "error",
        "mode": mode,
        "checks": checks,
        "failed_count": len(failed),
    }
