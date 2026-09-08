"""Shared path resolution for the fep_lean project.

Provides ``project_root()`` so that any subpackage can locate the
project directory without depending on the pipeline layer.
"""

from __future__ import annotations

import os
from pathlib import Path

_PACKAGE_DIR = Path(__file__).resolve().parent  # src/fep_lean/
_CHECKOUT_MARKERS = (
    "config/topics.yaml",
    "config/settings.yaml",
    "lean/lean-toolchain",
    "lean/lakefile.lean",
    "docs/manuscript/config.yaml",
    "src/fep_lean/__init__.py",
)


def project_root() -> Path:
    """Return the project root directory.

    In a source checkout this resolves to the directory containing ``src/``,
    ``config/``, and ``lean/``. In an installed wheel it resolves only to the
    distribution ancestor; substantive CLI callers must validate it with
    :func:`project_root_errors` or supply ``FEP_LEAN_PROJECT_ROOT`` /
    ``--project-root``.
    The environment override is also useful for isolated test fixtures.
    """
    if env_dir := os.environ.get("FEP_LEAN_PROJECT_ROOT"):
        return Path(env_dir).resolve()
    return _PACKAGE_DIR.parent.parent


def project_root_errors(root: Path) -> tuple[str, ...]:
    """Return missing checkout assets required by substantive CLI workflows.

    The wheel contains the importable catalogue and formal resources, but the
    Lean workspace, authored configuration, manuscript, and generated-output
    owners intentionally remain checkout-bound.  Detecting that boundary up
    front prevents an installed console script from accidentally treating a
    ``site-packages`` ancestor as a project checkout.
    """
    candidate = Path(root).resolve()
    return tuple(
        relative
        for relative in _CHECKOUT_MARKERS
        if not (candidate / relative).is_file()
    )
