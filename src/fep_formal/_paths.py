"""Shared path resolution for the fep_formal project.

Provides ``project_root()`` so that any subpackage can locate the
project directory without depending on the pipeline layer.
"""

from __future__ import annotations

import json
import os
import warnings
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import overload


@overload
def resolve_environment(name: str, default: str) -> str: ...


@overload
def resolve_environment(name: str, default: None = None) -> str | None: ...


def resolve_environment(name: str, default: str | None = None) -> str | None:
    """Resolve public settings at call time without exposing values or mutation."""
    if not name.startswith("FEP_FORMAL_"):
        raise ValueError("expected a canonical FEP_FORMAL_ environment name")
    legacy = "FEP_LEAN_" + name.removeprefix("FEP_FORMAL_")
    if name in os.environ:
        if legacy in os.environ and os.environ[legacy] != os.environ[name]:
            warnings.warn(
                f"{legacy} is deprecated and conflicts with {name}; {name} takes precedence",
                FutureWarning,
                stacklevel=2,
            )
        return os.environ[name]
    if legacy in os.environ:
        warnings.warn(
            f"{legacy} is deprecated; use {name}", FutureWarning, stacklevel=2
        )
        return os.environ[legacy]
    return default


class FepFormalError(Exception):
    """Common base of every package-defined exception.

    Package errors keep their historical built-in base (``ValueError``,
    ``RuntimeError``, ...) alongside this one, so existing ``except`` clauses
    are unaffected while callers can catch ``FepFormalError`` for any of them.
    Lives in ``_paths`` because every layer can already import it cycle-free.
    """


# Deprecated compatibility alias; both names identify the same exception class.
FepLeanError = FepFormalError


_PACKAGE_DIR = Path(__file__).resolve().parent  # src/fep_formal/
_CHECKOUT_MARKERS = (
    "config/topics.yaml",
    "config/settings.yaml",
    "lean/lean-toolchain",
    "lean/lakefile.lean",
    "manuscript/config.yaml",
    "src/fep_formal/__init__.py",
)


_CALLER_PROJECT_ROOT: ContextVar[Path | None] = ContextVar(
    "fep_lean_caller_project_root", default=None
)


@contextmanager
def project_root_context(root: Path) -> Iterator[Path]:
    """Bind an explicit caller root without mutating process environment."""
    selected = Path(root).resolve()
    token = _CALLER_PROJECT_ROOT.set(selected)
    try:
        yield selected
    finally:
        _CALLER_PROJECT_ROOT.reset(token)


def project_child_environment(base: Mapping[str, str]) -> dict[str, str]:
    """Copy a child environment and propagate only an explicit caller root.

    ContextVars do not propagate to OS children. Do not infer credentials,
    mutate base, or override its root when no caller context is active.
    """
    result = dict(base)
    selected = _CALLER_PROJECT_ROOT.get()
    if selected is not None:
        result["FEP_FORMAL_PROJECT_ROOT"] = str(selected)
    return result


def project_root() -> Path:
    """Return the project root directory.

    In a source checkout this resolves to the directory containing ``src/``,
    ``config/``, and ``lean/``. In an installed wheel it resolves only to the
    distribution ancestor; substantive CLI callers must validate it with
    :func:`project_root_errors` or supply ``FEP_FORMAL_PROJECT_ROOT`` /
    ``--project-root``.
    The environment override is also useful for isolated test fixtures.
    """
    return explicit_project_root() or _PACKAGE_DIR.parent.parent


def explicit_project_root() -> Path | None:
    """Return caller-context then environment root, without checkout fallback."""
    if selected := _CALLER_PROJECT_ROOT.get():
        return selected
    if env_dir := resolve_environment("FEP_FORMAL_PROJECT_ROOT"):
        return Path(env_dir).resolve()
    return None


def resolve_output_root(root: Path, explicit: Path | None = None) -> Path:
    """Resolve explicit, environment, settings, then default output paths.

    Explicit and environment paths retain their caller-working-directory
    semantics. A relative settings path belongs to the project checkout.
    Only the selected configuration is read; this function writes nothing.
    """
    if explicit is not None:
        return Path(explicit)
    override = resolve_environment("FEP_FORMAL_OUTPUT_ROOT", "")
    if override.strip():
        return Path(override)
    root = Path(root)
    settings_path = root / "config" / "settings.yaml"
    if not settings_path.is_file():
        return root / "output"

    import yaml

    try:
        settings = yaml.safe_load(settings_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise ValueError(
            f"unreadable output settings file {settings_path}: {type(exc).__name__}"
        ) from exc
    if settings is None:
        settings = {}
    if not isinstance(settings, dict):
        raise ValueError(f"output settings file {settings_path} must be a mapping")  # noqa: TRY004 -- invalid configuration, not an argument type
    output = settings.get("output")
    if output is None:
        output = {}
    if not isinstance(output, dict):
        raise ValueError(f"output in {settings_path} must be a mapping")  # noqa: TRY004 -- invalid configuration, not an argument type
    configured = output.get("root")
    if configured is None or configured == "":
        return root / "output"
    if not isinstance(configured, str) or not configured.strip():
        raise ValueError(f"output.root in {settings_path} must be a nonblank path")
    return (root / configured).resolve()


def project_root_errors(root: Path) -> tuple[str, ...]:
    """Return missing checkout assets required by substantive CLI workflows.

    The wheel contains the importable catalog and formal resources, but the
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


def _emit_failure(reason: str, *, indent: int | None = None, **extra: object) -> int:
    """Emit one operational-failure envelope and return the CLI failure status.

    Context always lives in details; success serializers remain independent.
    """
    payload = {"status": "error", "failure_reason": reason, "details": extra}
    print(json.dumps(payload, indent=indent, default=str, allow_nan=False))
    return 1


def _display(root: Path, path: Path) -> str:
    """Render *path* for display, relative to *root* when possible."""
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)
