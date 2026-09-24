#!/usr/bin/env python3
"""Fail-closed compile gate for formal Lean modules outside fep_all's closure.

Scope
-----

CI's lean job builds the Lake workspace projection (``lake build
FepSketches`` with ``globs := #[.andSubmodules 'FepSketches]`` in
``lean/lakefile.lean``). Those are the projected bytes under
``lean/FepSketches/``. The canonical sources under ``src/fep_lean/formal/``
are never compiled as files by any CI step, and the serial_lean lane's
opt-in compile probes are topic-driven, not module-driven. Commit b5e6a9d
narrowed ``finite_probability``'s imports and broke the orphaned
``src/fep_lean/formal/posterior_convergence.lean`` without any gate
compiling it; b85cfe0 fixed the break and this gate closes the gap.

Orphan definition
-----------------

A canonical formal module is *orphaned* when it is absent from the
transitive ``import FepSketches.*`` closure of
``lean/FepSketches/fep_all.lean``. Import edges use the same parse rule as
``scripts/_maint_build_lean_landscape.py::_workspace_imports`` (first token
after ``import``; only ``FepSketches.*`` targets are followed), and dotted
names mirror to canonical resources the way
``src/fep_lean/formal/manifest.py`` validates, e.g.
``FepSketches.compositions.core`` -> ``compositions/core.lean``. An import
without a canonical mirror (the generated ``FepSketches.fep_all`` aggregate
itself) is a closure leaf.

Check
-----

Only the top level of ``src/fep_lean/formal/`` is enumerated; the
composition leaves under ``formal/compositions/`` are workspace build
targets reached through ``composed.lean``. Each orphan's canonical file is
compiled with ``lake env lean`` from the ``lean/`` directory: no olean is
written and no incremental build state is consulted, so errors and
``warning:`` lines surface on every run. Any failing module is listed and
the exit code is nonzero.

Exit codes
----------

- ``0`` -- every orphaned module compiled error- and warning-free.
- ``1`` -- at least one orphan failed, or the inputs are unusable.

Usage
-----

.. code-block:: bash

    uv run python docs/check_orphan_compiles.py             # repo root
    uv run python docs/check_orphan_compiles.py --root path/to/repo
    uv run python docs/check_orphan_compiles.py --dry-run   # enumerate only
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FORMAL_DIR = Path("src") / "fep_lean" / "formal"
FEP_ALL_PATH = Path("lean") / "FepSketches" / "fep_all.lean"
LEAN_DIR = Path("lean")
WORKSPACE_PREFIX = "FepSketches."


def _workspace_imports(path: Path) -> list[str]:
    """``FepSketches.*`` imports of a Lean file, with the prefix stripped.

    Same parse rule as ``scripts/_maint_build_lean_landscape.py``. Comments
    are not interpreted; that is safe for the generated aggregate and the
    canonical sources, whose imports are plain top-of-file lines.
    """
    deps: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("import "):
            target = stripped.split()[1]
            if target.startswith(WORKSPACE_PREFIX):
                deps.append(target.removeprefix(WORKSPACE_PREFIX))
    return deps


def _canonical_mirror(formal_dir: Path, module: str) -> Path | None:
    """Canonical resource for a dotted workspace module, or None if absent."""
    parts = module.split(".")
    if not parts or any(not part for part in parts):
        return None
    mirror = formal_dir.joinpath(*parts).with_suffix(".lean")
    return mirror if mirror.is_file() else None


def import_closure(fep_all_path: Path, formal_dir: Path) -> frozenset[str]:
    """Dotted workspace-module names reachable from ``fep_all``'s imports."""
    closure: set[str] = set()
    stack = _workspace_imports(fep_all_path)
    while stack:
        module = stack.pop()
        if module in closure:
            continue
        mirror = _canonical_mirror(formal_dir, module)
        if mirror is None:
            # Generated aggregates (fep_all itself) and unmirrored names have
            # no canonical source to traverse; they are closure leaves, the
            # same treatment the landscape generator applies to unmanifested
            # names.
            continue
        closure.add(module)
        stack.extend(_workspace_imports(mirror))
    return frozenset(closure)


def orphan_modules(project_root: Path) -> tuple[str, ...]:
    """Sorted orphan set over the canonical top-level formal modules."""
    formal_dir = project_root / FORMAL_DIR
    closure = import_closure(project_root / FEP_ALL_PATH, formal_dir)
    return tuple(
        source.stem
        for source in sorted(formal_dir.glob("*.lean"))
        if source.stem not in closure
    )


def _lake_env_lean(lean_dir: Path, source: Path) -> subprocess.CompletedProcess[str]:
    """Compile one canonical file from source; no olean is written."""
    return subprocess.run(
        ["lake", "env", "lean", str(source)],
        cwd=lean_dir,
        capture_output=True,
        text=True,
        check=False,
    )


def _module_failed(result: subprocess.CompletedProcess[str]) -> bool:
    output = "\n".join(part for part in (result.stdout, result.stderr) if part)
    return result.returncode != 0 or "warning:" in output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compile formal Lean modules outside fep_all's import closure.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=PROJECT_ROOT,
        help="repository root (default: the checkout this script lives in)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the orphan set without compiling anything",
    )
    args = parser.parse_args(argv)
    project_root = args.root.resolve()
    formal_dir = project_root / FORMAL_DIR
    fep_all = project_root / FEP_ALL_PATH
    if not formal_dir.is_dir():
        print(f"formal module directory not found: {formal_dir}", file=sys.stderr)
        return 1
    if not fep_all.is_file():
        print(f"fep_all aggregate not found: {fep_all}", file=sys.stderr)
        return 1

    orphans = orphan_modules(project_root)
    print(f"orphaned formal modules outside fep_all's import closure: {len(orphans)}")
    for module in orphans:
        resource = FORMAL_DIR / f"{module}.lean"
        print(f"  {WORKSPACE_PREFIX}{module} ({resource.as_posix()})")
    if args.dry_run:
        return 0
    if not orphans:
        print("no orphaned formal modules to compile")
        return 0

    lean_dir = project_root / LEAN_DIR
    failures: list[tuple[str, str]] = []
    for module in orphans:
        source = formal_dir / f"{module}.lean"
        result = _lake_env_lean(lean_dir, source)
        if _module_failed(result):
            output = "\n".join(part for part in (result.stdout, result.stderr) if part)
            failures.append((module, output.strip()))
            print(f"FAIL {WORKSPACE_PREFIX}{module}")
        else:
            print(f"ok   {WORKSPACE_PREFIX}{module}")

    if failures:
        print(
            f"{len(failures)} of {len(orphans)} orphaned formal module(s) failed "
            "to compile:"
        )
        for module, output in failures:
            print(f"--- {WORKSPACE_PREFIX}{module} ---")
            print(output)
        return 1
    print(f"all {len(orphans)} orphaned formal module(s) compiled warning-free")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
