"""lean_verifier — Lean 4 / Lake compilation checker for fep_lean.

Verifies Lean 4 theorem sketches by writing them to a temporary file inside
the project's ``lean/FepSketches/`` directory and running ``lake env lean`` on
them.  The verifier correctly classifies ``sorry``-containing sketches as
"compiles with warnings" rather than "fails".

macOS sandbox note
------------------
``elan`` (the Lean version manager) may fail to write ``~/.elan/settings.toml``
in sandboxed environments.  The verifier works around this by:

1. Trying ``lake`` / ``lean`` on ``PATH`` first (respects ``PATH`` overrides).
2. Falling back to the raw toolchain binary at
   ``~/.elan/toolchains/{name}/bin/lake`` (bypasses the elan proxy).
3. Optionally overriding via ``FEP_LEAN_LAKE_EXE`` / ``FEP_LEAN_LEAN_EXE``
   environment variables.
4. Setting ``ELAN_HOME=/tmp/fep_lean_elan`` so the elan proxy can write its
   settings even in restricted environments.

Toolchain resolution order (for direct-path fallback):
  1. ``FEP_LEAN_LAKE_EXE`` env var
  2. ``lake`` on PATH (may be elan proxy — handled gracefully)
  3. ``~/.elan/toolchains/<toolchain>/bin/lake`` matching ``lean-toolchain``
  4. All other toolchains in ``~/.elan/toolchains/``, newest first

Public API
----------
    LeanVerifier(lean_dir, project_root)
    .verify_sketch(topic_id, lean_code)  → VerifyResult
    .verify_batch(items)                  → list[VerifyResult]
    .check_lake_available()               → bool
    .lean_version()                       → str | None

VerifyResult fields
-------------------
    compiles: bool          — True if ``lake env lean`` exits 0
    has_sorry: bool         — True if the sketch contains ``sorry``
    errors: list[str]       — compiler error lines
    warnings: list[str]     — compiler warning lines
    stdout: str             — full combined output
    duration_s: float       — elapsed seconds
    lean_version: str       — lean --version string (cached)
    topic_id: str
    lean_file: Path | None  — temp file path used
"""

from __future__ import annotations

import contextlib
import logging
import math
import os
import re
import statistics
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from fep_lean.verification._subprocess import run_process_group
from fep_lean.verification._toolchain import (
    ensure_writable_elan_home as _ensure_elan_home,
)
from fep_lean.verification._toolchain import find_executable as _shared_find_executable
from fep_lean.verification._toolchain import (
    find_toolchain_bin as _shared_find_toolchain_bin,
)
from fep_lean.verification._toolchain import get_elan_home as _get_elan_home
from fep_lean.verification._toolchain import (
    get_writable_elan_home as _get_elan_home_override,
)
from fep_lean.verification._toolchain import (
    lake_version_matches_pin as _lake_version_matches_pin,
)
from fep_lean.verification._toolchain import read_toolchain_name as _read_toolchain_name
from fep_lean.verification._toolchain import subprocess_env as _shared_subprocess_env

log = logging.getLogger(__name__)

FailureKind = Literal[
    "missing_import",
    "renamed_identifier",
    "tactic_failure",
    "arity_mismatch",
    "timeout",
    "other",
]

_LEAN_VERSION_CACHE: dict[str, str] = {}

# Error and warning patterns from `lake env lean` output
_RE_ERROR = re.compile(r"^.+ error:.*(?:\n\s+.*)*", re.MULTILINE)
_RE_WARNING = re.compile(r"^.+ warning:.*(?:\n\s+.*)*", re.MULTILINE)
_RE_SORRY = re.compile(r"\bsorry\b")
_RE_IMPORT_COMMAND = re.compile(r"^import(?:\s+|$)")


def _strip_lean_comments(code: str) -> str:
    """Remove Lean block and line comments so a commented ``sorry`` is not counted."""
    without_blocks = re.sub(r"/-.*?-/?", "", code, flags=re.DOTALL)
    return re.sub(r"--[^\n]*", "", without_blocks)


def _has_sorry(code: str) -> bool:
    """Detect proof placeholders while ignoring Lean line and block comments."""
    return bool(_RE_SORRY.search(_strip_lean_comments(code)))


def _count_sorry(code: str) -> int:
    """Count proof placeholders, ignoring Lean line and block comments.

    ``has_sorry`` answers "does this topic admit anything"; the manuscript also
    prints a figure it calls "uses of ``sorry``", which is an occurrence count.
    Summing the boolean gave the number of *topics*, so a topic with three
    admitted proofs contributed one. Count the occurrences here so the two
    questions have two answers.
    """
    return len(_RE_SORRY.findall(_strip_lean_comments(code)))


_RE_FAIL_KIND_TIMEOUT = re.compile(r"timeout|timed out", re.IGNORECASE)
_RE_FAIL_KIND_TACTIC = re.compile(
    r"unknown tactic|tactic .* failed|unsolved goals", re.IGNORECASE
)
_RE_FAIL_KIND_ARITY = re.compile(
    r"type mismatch|Application type mismatch|number of fields|wrong number of",
    re.IGNORECASE,
)

_LAKE_TIMEOUT_S = int(os.environ.get("FEP_LEAN_VERIFY_TIMEOUT", "1800"))
_VERIFICATION_TIMEOUT = _LAKE_TIMEOUT_S


def _get_timeout() -> int:
    """Read timeout from env at call time so tests can override without reimport."""
    return int(os.environ.get("FEP_LEAN_VERIFY_TIMEOUT", str(_VERIFICATION_TIMEOUT)))


def classify_failure_kind(stderr_out: str, *, timed_out: bool = False) -> FailureKind:
    """Lightweight advisory classification from Lean stderr/stdout (regex)."""
    if timed_out:
        return "timeout"
    s = stderr_out or ""
    if _RE_FAIL_KIND_TIMEOUT.search(s):
        return "timeout"
    if _RE_FAIL_KIND_TACTIC.search(s):
        return "tactic_failure"
    if _RE_FAIL_KIND_ARITY.search(s):
        return "arity_mismatch"
    if re.search(r"could not resolve import|unknown module", s, re.IGNORECASE):
        return "missing_import"
    if re.search(r"unknownIdentifier|Unknown constant", s):
        return "renamed_identifier"
    if "import" in s and "error" in s.lower():
        return "missing_import"
    return "other"


def _get_elan_bin() -> Path:
    return _get_elan_home() / "bin"


def _subprocess_env(lean_dir: Path | None = None) -> dict[str, str]:
    """Build an environment dict for lean/lake sub-processes.

    Delegates to ``fep_lean.verification._toolchain.subprocess_env``; callers
    must thread the instance's ``_lean_dir`` so the direct toolchain ``bin/``
    is prepended to ``PATH`` (matching the pinned lake at argv head).
    """
    return _shared_subprocess_env(lean_dir)


def _direct_toolchain_bin(lean_dir: Path | None = None) -> Path | None:
    """Return the ``bin/`` directory of the matching (or newest) toolchain."""
    return _shared_find_toolchain_bin(lean_dir)


def _find_exe(name: str, lean_dir: Path | None = None) -> str | None:
    """Resolve an executable via the shared toolchain resolution order."""
    return _shared_find_executable(name, lean_dir)


def _sanitize_lean_block(code: str) -> str:
    """Drop import lines appearing after the first non-import/non-comment line.

    Lean 4 requires all imports at file top. Hermes sometimes emits import
    statements after namespace declarations; this strips them to prevent
    'invalid import command' errors.
    """
    lines = code.split("\n")
    first_non_import = len(lines)
    for i, ln in enumerate(lines):
        s = ln.strip()
        if (
            s
            and _RE_IMPORT_COMMAND.match(s) is None
            and not s.startswith("--")
            and not s.startswith("/-")
            and not s.startswith("-/")
        ):
            first_non_import = i
            break
    cleaned = [
        ln
        for i, ln in enumerate(lines)
        if not (
            _RE_IMPORT_COMMAND.match(ln.strip()) is not None and i > first_non_import
        )
    ]
    return "\n".join(cleaned)


@dataclass
class VerifyResult:
    """Outcome of compiling one Lean sketch with full Mathlib4 context."""

    topic_id: str
    compiles: bool
    has_sorry: bool
    sorry_occurrences: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    stdout: str = ""
    stderr: str = ""
    duration_s: float = 0.0
    lean_version: str = "unknown"
    lean_file: Path | None = None
    skip_reason: str = ""  # non-empty when verification was skipped
    failure_kind: FailureKind = "other"

    @property
    def status(self) -> str:
        """Human-readable status for reporting."""
        if self.skip_reason:
            return f"skipped ({self.skip_reason})"
        if not self.compiles:
            return "compile_error"
        if self.has_sorry:
            return "compiles_with_sorry"
        return "compiles_clean"

    def as_dict(self) -> dict[str, object]:
        """Return serializable dict for reports and JSONL export."""
        return {
            "topic_id": self.topic_id,
            "compiles": self.compiles,
            "has_sorry": self.has_sorry,
            "sorry_occurrences": self.sorry_occurrences,
            "status": self.status,
            "errors": self.errors,
            "warnings": self.warnings,
            "duration_s": round(self.duration_s, 3),
            "lean_version": self.lean_version,
            "lean_file": str(self.lean_file) if self.lean_file else None,
            "skip_reason": self.skip_reason,
            "failure_kind": self.failure_kind,
        }


class LeanVerifier:
    """Verify Lean 4 sketches via ``lake env lean <file>`` in the project workspace.

    Parameters
    ----------
    lean_dir:
        Path to the Lean / Lake project root (must contain ``lakefile.lean``
        and ``lean-toolchain``).  The workspace must have Mathlib4 as a
        dependency (see ``lean/lakefile.lean``) so that ``import Mathlib.*``
        resolves correctly.
    project_root:
        Parent project root (used for resolving relative paths if lean_dir is
        relative).

    Mathlib setup
    -------------
    Before the first run, execute in a **non-sandboxed terminal**::

        cd lean
        lake exe cache get   # downloads prebuilt Mathlib .olean cache (~3 GB)
        lake build           # compiles FepSketches against Mathlib

    The verifier then calls ``lake env lean <sketch.lean>`` which inherits the
    full Mathlib environment from the built workspace.
    """

    def __init__(
        self,
        lean_dir: Path | str | None = None,
        project_root: Path | str | None = None,
    ) -> None:
        if project_root is not None:
            self._project_root = Path(project_root).resolve()
        else:
            self._project_root = Path.cwd()

        if lean_dir is not None:
            self._lean_dir = Path(lean_dir).resolve()
        else:
            self._lean_dir = (self._project_root / "lean").resolve()

        _ensure_elan_home()
        self._lake_exe: str | None = _find_exe("lake", self._lean_dir)
        self._lean_exe: str | None = _find_exe("lean", self._lean_dir)
        self._sketches_dir = self._lean_dir / "FepSketches"
        self._lake_probe: tuple[str | None, bool] | None = None
        self._sketches_dir.mkdir(parents=True, exist_ok=True)

        log.debug(
            "LeanVerifier: lean_dir=%s lake=%s lean=%s elan_home=%s",
            self._lean_dir,
            self._lake_exe,
            self._lean_exe,
            _get_elan_home_override(),
        )

    # ── Public ────────────────────────────────────────────────────────────────

    def check_lake_available(self) -> bool:
        """Return ``True`` if the pinned ``lake`` toolchain is usable.

        Uses a short timeout to detect hanging elan proxy processes
        (common in macOS sandboxed environments where settings.toml is blocked).
        """
        if not self._lake_exe:
            return False
        cache_key = self._lake_exe
        if self._lake_probe is not None and self._lake_probe[0] == cache_key:
            return self._lake_probe[1]
        try:
            r = subprocess.run(
                [self._lake_exe, "--version"],
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
                env=_subprocess_env(self._lean_dir),
            )
            output = (r.stdout or "") + (r.stderr or "")
            pinned = _read_toolchain_name(self._lean_dir)
            available = r.returncode == 0 and (
                not pinned or _lake_version_matches_pin(output, pinned)
            )
        except (OSError, subprocess.TimeoutExpired):
            available = False
        self._lake_probe = (cache_key, available)
        return available

    def lean_version(self) -> str | None:
        """Return the cached ``lean --version`` string, or None if unavailable."""
        if not self._lean_exe:
            return None
        if self._lean_exe in _LEAN_VERSION_CACHE:
            return _LEAN_VERSION_CACHE[self._lean_exe]
        try:
            r = subprocess.run(
                [self._lean_exe, "--version"],
                capture_output=True,
                text=True,
                timeout=20,
                check=False,
                env=_subprocess_env(self._lean_dir),
            )
            stdout = (r.stdout or "").strip()
            stderr = (r.stderr or "").strip()
            combined_err = (stderr + stdout).lower()
            # elan sandbox issue: settings.toml write is blocked or isolated ELAN_HOME
            # causes 'no default toolchain'. Both are proxy sandbox issues.
            if r.returncode != 0:
                if (
                    "settings.toml" in combined_err
                    and "operation not permitted" in combined_err
                ) or "no default toolchain configured" in combined_err:
                    version = (
                        f"lean (sandbox proxy restriction; binary at {self._lean_exe})"
                    )
                else:
                    version = f"lean (exit {r.returncode})"
            elif r.returncode == 0:
                version = stdout.splitlines()[0] if stdout else "lean"
            _LEAN_VERSION_CACHE[self._lean_exe] = version
            return version
        except (OSError, subprocess.TimeoutExpired):
            return None

    def check_mathlib_built(self) -> tuple[bool, str]:
        """Return ``(True, msg)`` if the Mathlib .olean cache is present in the
        workspace's ``.lake/packages/mathlib/`` directory.

        This is a fast filesystem check — it does NOT invoke lake or lean. The
        check probes both the root ``Mathlib.olean`` and a small set of leaf
        modules that are imported by virtually every catalogue sketch
        (``Mathlib.Data.Real.Basic`` for ``LE ℝ`` / ``OfNat ℝ`` instances and
        ``Mathlib.Algebra.Order.Ring.Basic`` for ordered-ring arithmetic). A
        partial cache that contains the root artifact but is missing these
        leaves produces confusing per-topic ``failed to synthesize`` errors at
        compile time, so we treat it as "not built" rather than letting the
        downstream batch run against a broken environment.
        """
        mathlib_pkg = self._lean_dir / ".lake" / "packages" / "mathlib"
        if not mathlib_pkg.is_dir():
            return (
                False,
                "Mathlib not yet downloaded — run: cd lean && lake exe cache get",
            )
        # Lake's dependency cache is built inside Mathlib's own package
        # workspace; the project workspace only contains FepSketches oleans.
        mathlib_build = mathlib_pkg / ".lake" / "build" / "lib" / "lean"
        mathlib_root_olean = mathlib_build / "Mathlib.olean"
        if not mathlib_root_olean.is_file():
            return (
                False,
                (
                    "Mathlib not yet downloaded or built — missing build artifact: "
                    f"{mathlib_root_olean}"
                ),
            )
        # Probe a small, stable set of leaf .olean files that the catalogue
        # sketches universally depend on. If any is missing, the cache is
        # partial / corrupted and a full-catalogue batch will fail opaquely.
        required_leaves = (
            mathlib_build / "Mathlib" / "Data" / "Real" / "Basic.olean",
            mathlib_build / "Mathlib" / "Algebra" / "Order" / "Ring" / "Basic.olean",
            mathlib_build
            / "Mathlib"
            / "MeasureTheory"
            / "Measure"
            / "MeasureSpace.olean",
        )
        missing = [
            str(p.relative_to(mathlib_build))
            for p in required_leaves
            if not p.is_file()
        ]
        if missing:
            return (
                False,
                (
                    "Mathlib build is incomplete; required leaf .olean files missing: "
                    f"{missing}"
                ),
            )
        return (
            True,
            f"Mathlib built (`{mathlib_root_olean.name}` and required leaves present)",
        )

    def verify_sketch(self, topic_id: str, lean_code: str) -> VerifyResult:
        """Compile ``lean_code`` inside the Lean workspace using full Mathlib4.

        The code is written to a temporary file in ``lean/FepSketches/`` so
        that Lake's module resolution picks up both FepSketches and Mathlib.
        The temp file is removed after compilation regardless of outcome.

        Returns
        -------
        VerifyResult
        """
        lv = self.lean_version() or "unknown"

        if not self._lake_exe:
            return VerifyResult(
                topic_id=topic_id,
                compiles=False,
                has_sorry=_has_sorry(lean_code),
                sorry_occurrences=_count_sorry(lean_code),
                lean_version=lv,
                skip_reason="lake not found — install elan/lean or set FEP_LEAN_LAKE_EXE",
            )
        if not self._lean_dir.is_dir():
            return VerifyResult(
                topic_id=topic_id,
                compiles=False,
                has_sorry=_has_sorry(lean_code),
                sorry_occurrences=_count_sorry(lean_code),
                lean_version=lv,
                skip_reason=f"lean_dir not found: {self._lean_dir}",
            )
        if not (self._lean_dir / "lakefile.lean").exists():
            return VerifyResult(
                topic_id=topic_id,
                compiles=False,
                has_sorry=_has_sorry(lean_code),
                sorry_occurrences=_count_sorry(lean_code),
                lean_version=lv,
                skip_reason="lakefile.lean not found",
            )

        # Wrap bare theorem declarations in the required import preamble
        full_code = self._wrap_lean_code(lean_code)
        has_sorry = _has_sorry(full_code)
        sorry_occurrences = _count_sorry(full_code)

        tmp_file: Path | None = None
        try:
            # Write to a temp .lean file inside FepSketches/
            fd, tmp_path_str = tempfile.mkstemp(
                prefix=f"_verify_{topic_id}_",
                suffix=".lean",
                dir=str(self._sketches_dir),
            )
            tmp_file = Path(tmp_path_str)
            os.close(fd)
            full_code = _sanitize_lean_block(full_code)
            tmp_file.write_text(full_code, encoding="utf-8")

            t0 = time.monotonic()
            # Use `lake env lean <file>` — inherits Mathlib env from built workspace
            result = self._run_lake_lean(tmp_file)
            elapsed = time.monotonic() - t0

            combined = (result.stdout or "") + (result.stderr or "")
            errors = _RE_ERROR.findall(combined)
            warnings = _RE_WARNING.findall(combined)
            compiles = result.returncode == 0

            log.info(
                "verify_sketch %s: compiles=%s sorry=%s errors=%d (%.2fs)",
                topic_id,
                compiles,
                has_sorry,
                len(errors),
                elapsed,
            )
            if len(combined) > 8000:
                log.warning(
                    "verify_sketch %s: output truncated from %d → 8000 chars; "
                    "full stderr may be missing from stored result",
                    topic_id,
                    len(combined),
                )
            fk: FailureKind = "other"
            if not compiles:
                fk = classify_failure_kind(combined)
            return VerifyResult(
                topic_id=topic_id,
                compiles=compiles,
                has_sorry=has_sorry,
                sorry_occurrences=sorry_occurrences,
                errors=errors,
                warnings=warnings,
                stdout=combined[:8000],
                duration_s=elapsed,
                lean_version=lv,
                lean_file=tmp_file,
                failure_kind=fk,
            )
        except subprocess.TimeoutExpired as exc:
            t_used = _get_timeout()
            log.warning("verify_sketch %s: timeout after %ss", topic_id, t_used)
            return VerifyResult(
                topic_id=topic_id,
                compiles=False,
                has_sorry=has_sorry,
                sorry_occurrences=sorry_occurrences,
                lean_version=lv,
                lean_file=tmp_file,
                duration_s=float(t_used),
                skip_reason=f"timeout after {t_used}s",
                stderr=str(exc),
                failure_kind="timeout",
            )
        except OSError as exc:
            log.error("verify_sketch %s: OSError %s", topic_id, exc)
            return VerifyResult(
                topic_id=topic_id,
                compiles=False,
                has_sorry=_has_sorry(lean_code),
                sorry_occurrences=_count_sorry(lean_code),
                lean_version=lv,
                skip_reason=str(exc),
            )
        finally:
            if tmp_file and tmp_file.exists():
                with contextlib.suppress(OSError):
                    tmp_file.unlink()

    def verify_batch(self, items: list[tuple[str, str]]) -> list[VerifyResult]:
        """Verify multiple ``(topic_id, lean_code)`` pairs sequentially
        (max_workers=1 to avoid .olean race conditions)."""
        results: list[VerifyResult] = []
        # Intentionally serialized: concurrent `lake env lean` calls share the
        # same .lake/build/ workspace and can race on .olean files, causing
        # spurious "invalid .olean file" errors.
        log.info(
            "Verifying %d Lean sketches sequentially (serialized for .olean safety)...",
            len(items),
        )
        for topic_id, lean_code in items:
            results.append(self.verify_sketch(topic_id, lean_code))
        assert all(r.topic_id for r in results), (
            "VerifyResult missing topic_id — cannot sort batch"
        )
        # Re-sort results by topic_id to maintain consistency
        results.sort(key=lambda r: r.topic_id)
        return results

    @staticmethod
    def summarize_batch_durations(
        results: list[VerifyResult],
    ) -> dict[str, float | int]:
        """Min / median / p95 of ``duration_s`` for non-skipped rows (metrics / §04e)."""
        vals = sorted(
            r.duration_s for r in results if not r.skip_reason and r.duration_s >= 0
        )
        if not vals:
            return {"count": 0, "min_s": 0.0, "median_s": 0.0, "p95_s": 0.0}
        n = len(vals)
        p95_i = min(n - 1, max(0, math.ceil(0.95 * n) - 1))
        return {
            "count": n,
            "min_s": round(vals[0], 4),
            "median_s": round(statistics.median(vals), 4),
            "p95_s": round(vals[p95_i], 4),
        }

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _wrap_lean_code(self, lean_code: str) -> str:
        """Prepend Mathlib import preamble if not already present.

        The preamble imports the core Mathlib modules used by the FEP
        catalogue, covering:
        - MeasureTheory (measures, integration, KL divergence)
        - Probability (kernels, conditional expectations, KL)
        - Analysis (special functions, inner products, derivatives)
        - Topology, LinearAlgebra, Geometry (manifolds, tangent bundles)
        """
        if lean_code.strip().startswith("import "):
            return lean_code
        preamble = (
            "import Mathlib\n"
            "-- Core Mathlib4 modules for FEP formalization\n"
            "open MeasureTheory ProbabilityTheory Real Nat Finset Set\n"
            "open scoped BigOperators\n\n"
        )
        return preamble + lean_code

    def _run_lake_lean(self, lean_file: Path) -> subprocess.CompletedProcess[str]:
        """Run ``lake env lean <file>`` in the lakefile directory.

        Uses ``_subprocess_env()`` which sets ``ELAN_HOME`` to a writable
        temp directory and injects the direct toolchain bin into PATH,
        bypassing the elan proxy's settings.toml write requirement.

        Runs through :func:`run_process_group` so a deadline kills the whole
        ``lake`` → ``lean`` process group; bare ``subprocess.run`` kills only
        the direct child and lets the ``lean`` grandchild hold the pipes and
        the ``.olean`` lock region past the advertised timeout.
        """
        env = _subprocess_env(self._lean_dir)
        if self._lake_exe is None:
            raise RuntimeError("lake executable is unavailable")
        return run_process_group(
            [self._lake_exe, "env", "lean", str(lean_file)],
            cwd=str(self._lean_dir),
            env=env,
            timeout=_get_timeout(),
            check=False,
        )
