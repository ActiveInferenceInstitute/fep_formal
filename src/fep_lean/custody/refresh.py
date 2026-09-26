"""The one sanctioned custody-refresh command, composing the settled phases.

``refresh`` composes the already-verified custody machinery in its
dependency-safe order and adds nothing new:

1. :func:`fep_lean.custody.census.census` — the read-only drift census.
2. :func:`fep_lean.custody.verify.verify` — the strict stop-gate against
   ``GATE_EXPECTATIONS``. A ``live-red`` record is never authorized; stale
   surfaces outside ``authorized_changes`` fail; a required surface missing
   from the census fails.
3. :func:`fep_lean.custody.apply.apply_refresh` — the settled 14-phase walk,
   writing only into the explicit staging tree.
4. The read-only verify set: the readiness matrix contract, the R0 custody
   successor validator, the terminal-acceptance validator, the diagnostics
   byte-equality probe, the custody test suites, the formalism audit
   receipt, and the pin audit.
5. The pre-capture owner gate: :func:`fep_lean.output.provenance.report_owner_errors`
   must return zero errors before any native capture runs.
6. Optionally, the native Lean capture — refused away from a committed clean
   tip, because the receipt binds live source bytes.

The known post-apply bridge cascade (source_binding FAILED naming an
authorized owner, freshness STALE) is reported as a warning with the
post-fold pin-cycle direction; it is never a failure and never remedied
here — pin cycles are coordinator-side.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from fep_lean.custody.apply import (
    DIAGNOSTICS,
    ApplyReport,
    apply_refresh,
    dump_json_bytes,
)
from fep_lean.custody.census import census as census_from_tree
from fep_lean.custody.verify import GATE_EXPECTATIONS
from fep_lean.custody.verify import verify as verify_gate
from fep_lean.output.provenance import report_owner_errors

#: Receipt path for the optional native capture (cwd-relative convention).
NATIVE_RECEIPT = "output/native-verification.json"
#: Receipt path for the read-only bridge pin probe.
BRIDGE_PIN = "specs/gnn-bridge-w2-source-custody/source-pin.json"
#: Targeted custody suites (never the full battery).
CUSTODY_TEST_FILES = (
    "tests/test_horizon_acceptance.py",
    "tests/test_h3_preregistration.py",
)


class RefreshRefused(RuntimeError):
    """A stop-gate, verify-set, or pre-capture check refused the refresh."""


@dataclass(frozen=True)
class RefreshReport:
    """Outcome of one composed refresh, reported phase by phase."""

    reason: str
    authorized: tuple[str, ...]
    apply: ApplyReport
    verify_set: dict[str, Any]
    warnings: tuple[str, ...] = ()
    native: dict[str, Any] = field(default_factory=dict)


def _run(*command: str, root: Path) -> dict[str, Any]:
    """Run one fixed project command; never a mutation of custody surfaces."""
    result = subprocess.run(
        command,
        cwd=str(root),
        check=False,
        capture_output=True,
        text=True,
    )
    tail = "\n".join(((result.stdout or "") + (result.stderr or "")).splitlines()[-20:])
    return {"command": list(command), "exit_code": result.returncode, "tail": tail}


def _load_module(root: Path, relative: str, name: str) -> Any:
    """Load a standalone validator module by path, without package coupling."""
    path = root / relative
    if not path.is_file():
        raise RefreshRefused(f"validator module missing: {relative}")
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RefreshRefused(f"validator module unloadable: {relative}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _validate_terminal(root: Path) -> dict[str, Any]:
    from fep_lean.verification.horizon_acceptance import validate_terminal_acceptance

    accepted = validate_terminal_acceptance(root)
    return {
        "receipt_sha256": accepted.receipt_sha256,
        "mandatory_nodeids": len(accepted.mandatory_nodeids),
        "source_files": len(accepted.source_sha256),
    }


def _diagnostics_byte_equality(root: Path, specs_dir: Path) -> dict[str, Any]:
    """Recompute the diagnostics record; compare bytes against the live tree."""
    from fep_lean.verification.horizon_acceptance import diagnostic_record

    serialized = dump_json_bytes(diagnostic_record(root), relative=DIAGNOSTICS)
    live = (specs_dir / DIAGNOSTICS[len("specs/") :]).read_bytes()
    equal = serialized == live
    return {
        "path": DIAGNOSTICS,
        "byte_equal": equal,
        "detail": (
            "diagnostics.json byte-equals the recomputed diagnostic record"
            if equal
            else "diagnostics.json drifted from the recomputed diagnostic record"
        ),
    }


def _bridge_warning(root: Path) -> str | None:
    """Detect the known post-apply bridge cascade; read-only, never a failure.

    Without a GNN checkout the authoritative ``bridge status`` cannot run, so
    this probes the fep_lean half of the signature: live owner bytes vs the
    pin's recorded digests. Any mismatch is the authorized-edit cascade the
    coordinator's post-fold bridge pin cycle remedies.
    """
    pin_path = root / BRIDGE_PIN
    if not pin_path.is_file():
        return None
    try:
        pin = json.loads(pin_path.read_text(encoding="utf-8"))
        owners: dict[str, str] = pin["fep_lean"]["owners"]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return f"bridge pin unreadable ({BRIDGE_PIN}): {exc}"
    drifted = sorted(
        owner
        for owner, digest in owners.items()
        if not isinstance(digest, str)
        or not (root / owner).is_file()
        or hashlib.sha256((root / owner).read_bytes()).hexdigest() != digest
    )
    if not drifted:
        return None
    return (
        "bridge source binding is stale on: "
        + ", ".join(drifted)
        + " (freshness STALE cascade expected); run the post-fold bridge pin "
        "cycle (coordinator-side; this command never pins)"
    )


def refresh(
    specs_dir: Path,
    root: Path,
    output_dir: Path,
    authorized: tuple[str, ...] = (),
    reason: str = "",
    *,
    run_native: bool = False,
) -> RefreshReport:
    """Compose census → stop-gate → apply → verify set → optional native capture."""
    if not reason.strip():
        raise RefreshRefused("a non-empty --reason is required for the audit trail")
    if not specs_dir.is_dir():
        raise RefreshRefused(f"specs dir not found: {specs_dir}")
    if not root.is_dir():
        raise RefreshRefused(f"repo root not found: {root}")

    census = census_from_tree(specs_dir, root)
    ok, problems = verify_gate(census, GATE_EXPECTATIONS)
    if not ok:
        raise RefreshRefused("custody verify gate refused: " + "; ".join(problems))

    report = apply_refresh(
        specs_dir,
        root,
        output_dir,
        GATE_EXPECTATIONS,
        census=census,
        authorized_changes=authorized,
    )

    readiness = _load_module(
        root,
        "specs/done/horizon-2-smooth-stochastic/readiness/validate.py",
        "fep_lean_custody_readiness_validate",
    )
    h2_r0 = _load_module(
        root, "tests/_support/h2_r0_custody.py", "fep_lean_h2_r0_probe"
    )
    verify_set: dict[str, Any] = {
        "readiness": readiness.readiness_errors(root),
        "h2_r0_custody": h2_r0.validate_h2_r0_custody(root)["native_evidence"][
            "status"
        ],
        "terminal_acceptance": _validate_terminal(root),
        "diagnostics": _diagnostics_byte_equality(root, specs_dir),
        "pytest_custody": _run(
            "uv",
            "run",
            "--frozen",
            "--extra",
            "dev",
            "pytest",
            *CUSTODY_TEST_FILES,
            "-q",
            "--no-cov",
            root=root,
        ),
        "formalism_audit": _run(
            "uv",
            "run",
            "--frozen",
            "python",
            "scripts/audit_formalisms.py",
            "--receipt",
            "output/formalism-audit.json",
            root=root,
        ),
        "pin_audit": _run(
            "uv",
            "run",
            "--frozen",
            "python",
            "docs/pin_audit.py",
            "--check-latest",
            root=root,
        ),
    }
    failures = _verify_failures(verify_set)
    if failures:
        raise RefreshRefused("verify set failed: " + "; ".join(failures))

    warnings: list[str] = []
    bridge = _bridge_warning(root)
    if bridge is not None:
        warnings.append(bridge)

    native: dict[str, Any] = {}
    if run_native:
        owner_errors = report_owner_errors(root)
        if owner_errors:
            raise RefreshRefused(
                "pre-capture owner gate refused: " + "; ".join(owner_errors)
            )
        dirty = _git_dirty(root)
        if dirty:
            raise RefreshRefused(
                "native capture requires a committed clean tip; dirty: "
                + ", ".join(dirty)
            )
        native = _run(
            "uv",
            "run",
            "fep-lean",
            "verify",
            "--fail-on-warnings",
            "--receipt",
            NATIVE_RECEIPT,
            root=root,
        )
    return RefreshReport(
        reason=reason,
        authorized=authorized,
        apply=report,
        verify_set=verify_set,
        warnings=tuple(warnings),
        native=native,
    )


def _verify_failures(verify_set: dict[str, Any]) -> list[str]:
    """Collect dict-shaped verify-set failures; validator raises fail closed."""
    failures: list[str] = []
    readiness = verify_set["readiness"]
    if readiness:
        failures.append("readiness errors: " + "; ".join(readiness))
    diagnostics = verify_set["diagnostics"]
    if not diagnostics["byte_equal"]:
        failures.append(str(diagnostics["detail"]))
    for key in ("pytest_custody", "formalism_audit", "pin_audit"):
        run = verify_set[key]
        if run["exit_code"] != 0:
            failures.append(f"{key} exit {run['exit_code']}: {run['tail']}")
    return failures


def _git_dirty(root: Path) -> list[str]:
    """The porcelain dirty list; the native receipt binds live source bytes."""
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(root),
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return [f"git status failed: {result.stderr.strip()[:200]}"]
    return result.stdout.splitlines()
