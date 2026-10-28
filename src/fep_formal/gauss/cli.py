"""Integration with [math-inc/OpenGauss](https://github.com/math-inc/OpenGauss) ``gauss`` CLI."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

_CLI_TIMEOUT_S = 120.0

from fep_formal._paths import resolve_environment


def _require_gauss_from_env() -> bool:
    v = resolve_environment("FEP_FORMAL_REQUIRE_GAUSS", "").strip().lower()
    return v in ("1", "true", "yes", "on")


def check_gauss_cli(
    project_root: Path | None, *, require: bool | None = None
) -> tuple[bool, str]:
    """Check local CLI availability without probing account credentials.

    If ``gauss`` is missing: fails only when ``require`` is True or the
    explicit ``FEP_FORMAL_REQUIRE_GAUSS`` setting is truthy.
    """
    # verification's public API imports this probe; resolve its shared runner
    # at invocation time to avoid a package-initialization cycle.
    from fep_formal.verification._subprocess import run_process_group

    if require is None:
        require = _require_gauss_from_env()

    exe = shutil.which("gauss")
    if not exe:
        return (
            (False, "gauss: executable is unavailable")
            if require
            else (True, "gauss: not configured")
        )

    try:
        with tempfile.TemporaryDirectory(prefix="fep-formal-gauss-probe-") as home:
            probe_home = Path(home).resolve()
            env = os.environ.copy()
            env["GAUSS_HOME"] = str(probe_home)
            env["GAUSS_SKIP_UPDATE_CHECK"] = "1"
            env["PYTHON_DOTENV_DISABLED"] = "1"
            proc = run_process_group(
                [exe, "--version"],
                cwd=probe_home,
                timeout=_CLI_TIMEOUT_S,
                check=False,
                env=env,
            )
    except (OSError, subprocess.TimeoutExpired) as e:
        msg = f"gauss version: failed ({e})"
        return (False, msg) if require else (True, msg)

    out = (proc.stdout or "").strip()
    err = (proc.stderr or "").strip()
    if proc.returncode != 0:
        snippet = (err or out)[:400]
        msg = f"gauss version: exit {proc.returncode} — {snippet}"
        return (False, msg) if require else (True, msg)

    line = out.splitlines()[0] if out else ""
    if not re.fullmatch(
        r"Gauss v\d+\.\d+\.\d+(?:[-+][\w.-]+)?(?: \([^\r\n]+\))?", line
    ):
        msg = "gauss version: unrecognized or empty version output"
        return (False, msg) if require else (True, msg)
    return (
        True,
        f"gauss CLI: available ({line[:120]}); provider/session checks are separate",
    )
