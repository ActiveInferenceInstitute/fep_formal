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

from check_render_log import main as accept_render
from render_manuscript import main as render_sources

from fep_lean.output.render_fonts import (
    FontProbeError,
    font_coverage_defects,
)

PROJECT_NAME = "fep_lean"
RENDER_STAGE = Path("scripts/pipeline/stage_03_render.py")
TEMPLATE_ENVIRONMENT_VARIABLE = "FEP_LEAN_TEMPLATE_DIR"
# One template checkout serves several projects, and two concurrent renders
# share its output tree. The lock is a directory because ``mkdir`` is atomic.
LOCK_ENVIRONMENT_VARIABLE = "DOCXOLOGY_RENDER_LOCK"
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


def acquire_lock(lock: Path, timeout_s: float) -> bool:
    """Take the shared render lock, waiting up to ``timeout_s``."""

    deadline = time.monotonic() + timeout_s
    while True:
        try:
            lock.mkdir()
            return True
        except FileExistsError:
            if time.monotonic() >= deadline:
                return False
            time.sleep(5)


def render_publication(
    project_root: Path,
    template: Path,
    *,
    runner: Runner = default_runner,
    hydrator: Hydrator | None = None,
    project: str = PROJECT_NAME,
    skip_probe: bool = False,
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
    hydration = (hydrator or (lambda: render_sources([])))()
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
    acceptance = accept_render(
        [
            "--pdf-dir",
            str(project_root / "output" / "pdf"),
            "--manuscript-dir",
            str(project_root / "manuscript"),
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
            project_root, template, skip_probe=args.skip_font_probe
        )
    finally:
        lock.rmdir()


if __name__ == "__main__":
    raise SystemExit(main())
