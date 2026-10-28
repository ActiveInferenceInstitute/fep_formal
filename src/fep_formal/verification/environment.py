"""Read-only capability probes and explicit locked workspace acquisition.

Only setup_workspace acquires dependencies; run_validation_checks remains read-only.
"""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
import sys
import time
from collections import Counter
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, TextIO

from fep_formal._paths import project_root as default_project_root
from fep_formal._paths import resolve_environment, resolve_output_root
from fep_formal.gauss.cli import check_gauss_cli
from fep_formal.gauss.client import resolve_gauss_home
from fep_formal.verification._subprocess import run_process_group
from fep_formal.verification._toolchain import (
    find_executable,
    find_toolchain_bin,
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
_VERSION_TIMEOUT_S = 5.0


def _lean_subprocess_env() -> dict[str, str]:
    return subprocess_env()


def _find_toolchain_lean(lean_dir: Path | None = None) -> str | None:
    toolchain = find_toolchain_bin(lean_dir)
    candidate = toolchain / "lean" if toolchain else None
    return str(candidate) if candidate and candidate.is_file() else None


def _version_line(exe: str, cwd: Path | None = None) -> tuple[bool, str]:
    try:
        proc = run_process_group(
            [exe, "--version"],
            cwd=cwd if cwd is not None else Path.cwd(),
            env=_lean_subprocess_env(),
            timeout=_VERSION_TIMEOUT_S,
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
    explicit = resolve_environment("FEP_FORMAL_LEAN_EXE", "")
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
        from fep_formal.catalogue.topics import FEPTopicCatalogue

        catalogue = FEPTopicCatalogue.from_yaml(project_root / "config" / "topics.yaml")
    except Exception as exc:
        return False, str(exc)
    return True, f"topics.yaml validated ({len(catalogue.topics)} topics)"


def _check_dirs(project_root: Path) -> tuple[bool, str]:
    required = ("manuscript", "config", "src", "lean", "scripts", "tests")
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


def _check_output_writable(
    project_root: Path, output_root: Path | None = None
) -> tuple[bool, str]:
    output = resolve_output_root(project_root, output_root)
    parent = output
    while not parent.exists():
        if parent.is_symlink():
            return False, f"output path has a dangling symlink: {parent}"
        if parent.parent == parent:
            return False, f"output path has no existing ancestor: {output}"
        parent = parent.parent
    if not parent.is_dir():
        return False, f"output path is blocked by a non-directory: {parent}"
    if not os.access(parent, os.W_OK | os.X_OK):
        return False, f"output directory is not writable/searchable: {parent}"
    return True, f"output directory {output} writable (checked {parent})"


def _check_file(project_root: Path, relative: str) -> tuple[bool, str]:
    path = project_root / relative
    return (
        path.is_file(),
        f"{relative} present" if path.is_file() else f"{relative} missing",
    )


def _check_references_bib(project_root: Path) -> tuple[bool, str]:
    path = project_root / "manuscript" / "references.bib"
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
    duplicates = sorted(key for key, count in Counter(keys).items() if count > 1)
    if duplicates:
        return False, "duplicate bibliography keys: " + ", ".join(duplicates)
    entry_lines = [line for line in text.splitlines() if line.lstrip().startswith("@")]
    if len(entry_lines) != len(matches):
        return False, "manuscript/references.bib has a malformed entry header"
    return True, f"references.bib validated ({len(keys)} unique entries)"


def _check_hermes_credentials(project_root: Path) -> tuple[bool, str]:
    from fep_formal.llm.hermes import HermesConfig

    config = HermesConfig.from_settings(project_root, hydrate_environment=False)
    if not config.api_key:
        return (
            False,
            "Hermes requires a provider key in the environment or OpenGauss dotenv",
        )
    if not config.enabled:
        return (
            False,
            "Hermes is disabled or the credential/endpoint configuration is incompatible",
        )
    try:
        config.runtime_policy()
    except ValueError:
        return False, "Hermes endpoint configuration is invalid"
    return True, "Hermes credentials configured (authentication not checked)"


# Focused check functions remain available for direct unit coverage. The
# pipeline itself uses the mode-aware dispatcher below.
def _check_catalogue_import(project_root: Path) -> tuple[bool, str]:
    return _check_topics_yaml(project_root)


def run_validation_checks(
    project_root: Path, *, mode: str = "full", output_root: Path | None = None
) -> dict[str, Any]:
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
        (
            "output_writable",
            lambda: _check_output_writable(project_root, output_root),
        ),
        (
            "manuscript_config",
            lambda: _check_file(project_root, "manuscript/config.yaml"),
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
            ("hermes_credentials", lambda: _check_hermes_credentials(project_root)),
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


def setup_workspace(
    root: Path,
    *,
    failure_emitter: Callable[..., int] | None = None,
    progress_stream: TextIO | None = None,
) -> int:
    """Acquire the checked-in workspace without resolving new dependency pins.

    Direct callers retain the existing text and exit codes. CLI adapters may
    provide a failure emitter and progress stream; the final success line stays
    on stdout, while command diagnostics can go to stderr without interception.
    """
    import re
    import shutil

    from fep_formal.verification._toolchain import (
        lean_version_matches_pin,
        pinned_lean_semver,
        read_mathlib_tag,
        read_toolchain_pin,
        resolved_mathlib_revision,
    )

    def failed(message: str, *, exit_code: int = 1) -> int:
        if failure_emitter is not None:
            return failure_emitter(message, command="setup", exit_code=exit_code)
        print(message, flush=True)
        return exit_code

    lean_dir = Path(resolve_environment("FEP_FORMAL_DIR", str(root / "lean"))).resolve()
    repair = (
        "Inspect git diff -- lean/lean-toolchain lean/lakefile.lean "
        "lean/lake-manifest.json uv.lock; preserve intentional edits, then restore "
        "these files together from the intended reviewed commit and rerun setup. "
        "Do not run lake update to repair ordinary setup."
    )
    try:
        timeout = int(resolve_environment("FEP_FORMAL_SETUP_TIMEOUT_SEC", "1800"))
    except ValueError:
        return failed("setup failed: FEP_FORMAL_SETUP_TIMEOUT_SEC must be an integer")
    if timeout < 1:
        return failed("setup failed: FEP_FORMAL_SETUP_TIMEOUT_SEC must be positive")
    deadline = time.monotonic() + timeout
    pins = [
        lean_dir / name
        for name in ("lean-toolchain", "lakefile.lean", "lake-manifest.json")
    ] + [root / "uv.lock"]
    try:
        snapshot = {path: path.read_bytes() for path in pins}
        toolchain = read_toolchain_pin(lean_dir)
        tag = read_mathlib_tag(lean_dir)
        manifest = json.loads(snapshot[lean_dir / "lake-manifest.json"])
        packages = manifest.get("packages") if isinstance(manifest, dict) else None
        if (
            not toolchain
            or tag != "v" + str(pinned_lean_semver(toolchain))
            or not isinstance(packages, list)
            or not packages
            or manifest.get("packagesDir") != ".lake/packages"
            or any(
                not isinstance(package, dict)
                or package.get("type") != "git"
                or not re.fullmatch(r"[0-9a-f]{40}", str(package.get("rev", "")))
                for package in packages
            )
        ):
            raise ValueError("invalid or mismatched toolchain/Mathlib/manifest pins")
        mathlib = [package for package in packages if package.get("name") == "mathlib"]
        if len(mathlib) != 1 or mathlib[0].get("inputRev") != tag:
            raise ValueError(
                "manifest Mathlib inputRev does not match lakefile/toolchain"
            )
        revision = resolved_mathlib_revision(lean_dir)
    except (OSError, ValueError) as exc:
        return failed(f"setup failed: {exc}. {repair}")

    def check_pins() -> None:
        for path, original in snapshot.items():
            if not path.is_file() or path.read_bytes() != original:
                raise ValueError(f"setup pin drift: {path}. {repair}")

    env = subprocess_env(lean_dir)
    # Setup deliberately installs into the requested (or ordinary) elan home,
    # unlike read-only verification's temporary writable-home fallback.
    elan_home = Path(os.environ.get("ELAN_HOME", str(Path.home() / ".elan")))
    env["ELAN_HOME"] = str(elan_home)
    for name in ("XDG_CACHE_HOME", "MATHLIB_CACHE_DIR"):
        if name in os.environ:
            env[name] = os.environ[name]

    def run(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
        check_pins()
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise subprocess.TimeoutExpired(list(command), timeout)
        print(
            f"[fep_formal setup] {' '.join(command)}", flush=True, file=progress_stream
        )
        try:
            result = run_process_group(
                command, cwd=lean_dir, env=env, timeout=remaining, check=False
            )
            if result.stdout:
                print(result.stdout, end="", flush=True, file=progress_stream)
            if result.stderr:
                print(result.stderr, end="", flush=True, file=progress_stream)
        finally:
            check_pins()
        if result.returncode:
            raise subprocess.CalledProcessError(result.returncode, list(command))
        return result

    try:
        lake = find_executable("lake", lean_dir)
        if not lake:
            elan = resolve_environment("FEP_FORMAL_ELAN_EXE") or shutil.which("elan")
            if not elan and (elan_home / "bin" / "elan").is_file():
                elan = str(elan_home / "bin" / "elan")
            if not elan:
                raise ValueError(
                    "elan is unavailable; install elan or set FEP_FORMAL_ELAN_EXE"
                )
            run([elan, "toolchain", "install", toolchain])
            toolchain_bin = (
                elan_home
                / "toolchains"
                / toolchain.replace("/", "--").replace(":", "---")
                / "bin"
            )
            lake = str(toolchain_bin / "lake")
        # Newly acquired toolchains must be visible to nested cache processes,
        # including Cache.IO's `lean --print-prefix` lookup.
        env["PATH"] = str(Path(lake).parent) + os.pathsep + env.get("PATH", "")
        lake_version = run([lake, "--version"]).stdout
        if f"(Lean version {pinned_lean_semver(toolchain)})" not in lake_version:
            raise ValueError(
                f"Lake does not report {toolchain}; install that toolchain with elan "
                "and remove a mismatched FEP_FORMAL_LAKE_EXE override"
            )
        # With a validated manifest, ordinary Lake loading materializes its
        # exact revisions. --wfail rejects out-of-date dependency warnings.
        actual_lean = run([lake, "--wfail", "env", "lean", "--version"]).stdout
        if not lean_version_matches_pin(actual_lean, toolchain):
            raise ValueError(f"actual Lean does not match {toolchain}")
        actual_revision = run(
            ["git", "-C", str(lean_dir / ".lake/packages/mathlib"), "rev-parse", "HEAD"]
        ).stdout.strip()
        if actual_revision != revision:
            raise ValueError(
                "materialized Mathlib revision does not match the manifest"
            )
        cache = run([lake, "--wfail", "exe", "cache", "get"])
        # The pinned Mathlib cache CLI returns zero for HTTP 404 misses.
        # Its explicit warning must not authorize a full source rebuild.
        if "some files were not found in the cache" in cache.stdout + cache.stderr:
            raise ValueError(
                "the pinned Mathlib cache is incomplete; retain this log and retry "
                "when the upstream cache is available; no source build was started"
            )
        run([lake, "--wfail", "build", "FepSketches"])
        print(
            f"[fep_formal setup] OK | lean: {actual_lean.strip()} | mathlib: {revision}",
            flush=True,
        )
        return 0
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        return failed(
            f"setup failed: {exc}. For pin/manifest errors: {repair}",
            exit_code=exc.returncode
            if isinstance(exc, subprocess.CalledProcessError)
            else 1,
        )


def _configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
