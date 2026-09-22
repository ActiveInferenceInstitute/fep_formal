#!/usr/bin/env python3
"""Render the publication and refuse to call a defective render successful.

The shared rendering template compiles with ``-interaction=nonstopmode`` and
tests the log for four fatal markers only, so a ``! `` error and every
``Missing character:`` note still exit zero with a PDF written. That is the
mechanism that shipped 162 dropped glyphs and one false printed theorem
(FEP-LEAN-R1/R2). The template is a separate repository shared with other
projects, so this repository cannot change that test -- but it can decline to
accept its verdict.

This is the project's publication entry point. It runs the template's render
stage and then the project's own acceptance, and its exit code is the
conjunction: a render whose log records a TeX error or a dropped glyph, whose
diagram fell back to raw source, whose tables lost their captions, or that no
longer describes its own sources, fails here even though the template reported
success.

Usage:
    uv run python scripts/render_publication.py --template <path to template>
    FEP_LEAN_TEMPLATE_DIR=<path> uv run python scripts/render_publication.py
    uv run python scripts/render_publication.py --accept-only
"""

from __future__ import annotations

import argparse
import contextlib
import importlib
import os
import subprocess  # nosec B404 - fixed argv, shell=False
import sys
import tempfile
import time
from collections.abc import Callable, Sequence
from pathlib import Path

# A direct render/acceptance invocation must not update checkout-local bytecode.
if __name__ == "__main__":
    sys.dont_write_bytecode = True

# The acceptance lives in a sibling script; make it importable however this
# file was loaded, so a test can drive the composition without a subprocess.
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Sibling scripts resolve through the sys.path bootstrap above at runtime;
# mypy does not follow sys.path mutations, so bind the two entry points to
# their concrete signatures instead of importing untyped top-level names.
accept_render: Callable[[list[str] | None], int] = (
    importlib.import_module("check_render_log").main
)
render_sources: Callable[[list[str] | None], int] = (
    importlib.import_module("render_manuscript").main
)

from fep_lean.output.render_fonts import (
    FontProbeError,
    font_coverage_defects,
)

PROJECT_NAME = "fep_lean"
RENDER_STAGE = Path("scripts/pipeline/stage_03_render.py")
# The committed record of what the acceptance found. CI does not render this
# manuscript -- that needs a checkout of the shared template, XeLaTeX, pandoc,
# ``rsvg-convert``, the mermaid CLI and the two faces the preamble selects --
# so it verifies this instead, and a chapter edited without a fresh render
# leaves it naming a digest the checkout no longer has.
RECEIPT_PATH = Path("docs") / "render-acceptance.json"
TEMPLATE_ENVIRONMENT_VARIABLE = "FEP_LEAN_TEMPLATE_DIR"
# One template checkout serves several projects, and two concurrent renders
# share its output tree. The lock is a directory because ``mkdir`` is atomic.
LOCK_ENVIRONMENT_VARIABLE = "DOCXOLOGY_RENDER_LOCK"
HOLDER_PID_FILE = "holder.pid"
Runner = Callable[[Sequence[str], Path], int]
Hydrator = Callable[[], int]


def default_runner(command: Sequence[str], cwd: Path) -> int:
    """Run the template's render stage and return its exit code."""

    completed = subprocess.run(  # nosec B603 - fixed argv, shell=False
        list(command), cwd=str(cwd), check=False
    )
    return completed.returncode


def resolve_template(explicit: Path | None) -> Path:
    """Return the template checkout, or raise with what was tried."""

    candidates = [explicit] if explicit is not None else []
    from_environment = os.environ.get(TEMPLATE_ENVIRONMENT_VARIABLE, "").strip()
    if from_environment:
        candidates.append(Path(from_environment))
    for candidate in candidates:
        resolved = Path(candidate).expanduser().resolve()
        if (resolved / RENDER_STAGE).is_file():
            return resolved
    tried = ", ".join(str(candidate) for candidate in candidates) or "(nothing)"
    raise FileNotFoundError(
        f"no rendering template holding {RENDER_STAGE} was found; tried {tried}. "
        f"Pass --template or set {TEMPLATE_ENVIRONMENT_VARIABLE}"
    )


def _recorded_holder_pid(lock: Path) -> int | None:
    """The pid the lock's holder recorded, when that file is present and valid."""

    try:
        return int((lock / HOLDER_PID_FILE).read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None


def _process_is_alive(pid: int) -> bool:
    """``os.kill(pid, 0)`` probes existence without delivering a signal."""

    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # the process exists but is not ours to signal
    except OSError:
        return False
    return True


def acquire_lock(lock: Path, timeout_s: float) -> bool:
    """Take the shared render lock, waiting up to ``timeout_s``.

    The winner records its pid in ``HOLDER_PID_FILE`` so a waiter can tell a
    live contender from a lock a crashed render left behind.
    """

    deadline = time.monotonic() + timeout_s
    stale_warned = False
    while True:
        try:
            lock.mkdir()
        except FileExistsError:
            holder = _recorded_holder_pid(lock)
            if (
                holder is not None
                and not stale_warned
                and not _process_is_alive(holder)
            ):
                print(
                    f"WARNING: the holder of the shared render lock {lock} "
                    f"(pid {holder}) appears dead; the lock looks stale, but "
                    "the wait continues as configured"
                )
                stale_warned = True
            if time.monotonic() >= deadline:
                return False
            time.sleep(5)
        else:
            (lock / HOLDER_PID_FILE).write_text(str(os.getpid()), encoding="utf-8")
            return True


def release_lock(lock: Path) -> None:
    """Release the shared render lock without masking the render's verdict.

    ``HOLDER_PID_FILE`` is ours to remove; anything else in the directory was
    left by another process, so it is reported -- naming the override
    environment variable -- instead of raised over. A release never raises:
    the render ran to a verdict, and that verdict is the exit code.
    """

    # The marker is advisory; rmdir below reports real leftovers.
    with contextlib.suppress(OSError):
        (lock / HOLDER_PID_FILE).unlink()
    try:
        lock.rmdir()
    except FileNotFoundError:
        pass
    except OSError:
        print(
            f"WARNING: the shared render lock {lock} looks stale; it still "
            "holds files left by another process and they were left in place. "
            f"Set {LOCK_ENVIRONMENT_VARIABLE} to a private path to point the "
            "render at a different lock."
        )


def render_publication(
    project_root: Path,
    template: Path,
    *,
    runner: Runner = default_runner,
    hydrator: Hydrator | None = None,
    project: str = PROJECT_NAME,
    skip_probe: bool = False,
    require_release_stamp: bool = False,
) -> int:
    """Hydrate the sources, render through the template, then accept or reject.

    The hydration step is neither optional nor the template's job. The template
    renders from ``output/manuscript`` whenever that directory exists
    (``infrastructure/rendering/_manuscript_source.resolve_manuscript_dir``)
    and refreshes only ``config.yaml`` and ``preamble.md`` inside it; its own
    hydration hook looks for a ``scripts/z_generate_manuscript_variables.py``
    this project does not have, and silently does nothing. A render run without
    this step therefore typesets whatever the project's renderer last wrote
    there -- which is how a render made after two chapters were fixed
    reproduced their drift exactly.

    The template's exit code is reported but never sufficient: the acceptance
    runs whatever it was, because the failure this guards against is exactly a
    zero exit over a defective log.
    """

    if not skip_probe:
        try:
            font_defects = font_coverage_defects(project_root)
        except FontProbeError as error:
            print(f"FAIL: {error}")
            return 1
        for line in font_defects:
            print(f"FAIL: {line}")
        if font_defects:
            print(
                "Refusing to render: the host would drop these glyphs silently, "
                "which is how a printed theorem became false (FEP-LEAN-R1)."
            )
            return 1
        print("OK: every typeset codepoint is covered by an installed font")
    hydration_argv = ["--require-release-stamp"] if require_release_stamp else []
    hydration = (hydrator or (lambda: render_sources(hydration_argv)))()
    if hydration != 0:
        print(
            "FAIL: the authored sources did not render; refusing to typeset "
            "whatever output/manuscript happens to hold"
        )
        return 1
    command = [
        "uv",
        "run",
        "--frozen",
        "python",
        str(RENDER_STAGE),
        "--project",
        project,
    ]
    render_status = runner(command, template)
    print(f"Template render exit={render_status}")
    # ``--receipt`` records the verdict where a runner without a LaTeX
    # toolchain can read it. It is written only when nothing was found, so a
    # rejected render leaves no receipt claiming these sources were accepted.
    acceptance = accept_render(
        [
            "--pdf-dir",
            str(project_root / "output" / "pdf"),
            "--manuscript-dir",
            str(project_root / "manuscript"),
            "--receipt",
            str(project_root / RECEIPT_PATH),
        ]
    )
    if render_status != 0:
        print("FAIL: the template's render stage reported failure")
    if acceptance != 0:
        print(
            "FAIL: the render is not publishable; the template reported "
            f"exit={render_status} for it"
        )
    return 1 if render_status or acceptance else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="render the publication and accept it fail-closed"
    )
    parser.add_argument(
        "--template",
        type=Path,
        default=None,
        help=f"rendering template checkout (default: ${TEMPLATE_ENVIRONMENT_VARIABLE})",
    )
    parser.add_argument(
        "--accept-only",
        action="store_true",
        help="skip the render and only accept the artifacts already in output/pdf",
    )
    parser.add_argument(
        "--skip-font-probe",
        action="store_true",
        help="skip the installed-font preflight (for a host without fontconfig)",
    )
    parser.add_argument(
        "--require-release-stamp",
        action="store_true",
        help="pass --require-release-stamp to the authored-source render, "
        "making a checkout that moved past its stamped tag a hydration failure",
    )
    parser.add_argument(
        "--lock-timeout",
        type=float,
        default=1800.0,
        help="seconds to wait for the shared template render lock",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    project_root = Path(__file__).resolve().parents[1]
    if args.accept_only:
        return accept_render(
            [
                "--pdf-dir",
                str(project_root / "output" / "pdf"),
                "--manuscript-dir",
                str(project_root / "manuscript"),
                "--receipt",
                str(project_root / RECEIPT_PATH),
            ]
        )
    try:
        template = resolve_template(args.template)
    except FileNotFoundError as error:
        print(f"ERROR: {error}")
        return 1
    lock = Path(
        os.environ.get(LOCK_ENVIRONMENT_VARIABLE)
        or Path(tempfile.gettempdir()) / "docxology-render.lock"
    )
    if not acquire_lock(lock, args.lock_timeout):
        print(f"ERROR: another render holds {lock}; waited {args.lock_timeout}s")
        return 1
    try:
        return render_publication(
            project_root,
            template,
            require_release_stamp=args.require_release_stamp,
            skip_probe=args.skip_font_probe,
        )
    finally:
        release_lock(lock)


if __name__ == "__main__":
    raise SystemExit(main())
