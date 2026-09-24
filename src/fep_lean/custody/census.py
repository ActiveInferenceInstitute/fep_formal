"""Read-only census of the H2.7 terminal-acceptance custody surface.

Hashes the recorded custody values — the terminal receipt and its native
capture, the ``PREDECESSORS`` pins, and the 07-gaussian-vfe-natural-gradient
R0 successor custody — against the live tree and classifies each surface
(:mod:`fep_lean.custody.model`). Pure and read-only: bytes are hashed, no
receipt or source file is ever written, no validator or compiler is invoked.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from fep_lean.custody.model import INTACT, LIVE_RED, STALE, Census, CensusRecord
from fep_lean.verification import horizon_acceptance as acceptance
from fep_lean.verification._jsonutil import load_strict_json
from fep_lean.verification.horizon_acceptance import (
    CURRENT_FILES,
    R0_SUCCESSOR,
    TERMINAL_RECEIPT,
    native_source_paths,
    source_snapshot,
)

# The one permanent prior-drift pair: identical to the validator's only-two
# exemption inside horizon_acceptance._predecessors and to
# tests/_support/h2_r0_custody.ALLOWED_PRIOR_CHANGES. src cannot import
# tests, so the reviewed pair is restated here; the fixture tests pin it
# against both of those sources.
AUTHORIZED_PRIOR_DRIFT = (
    "src/fep_lean/formal/manifest.py",
    "tests/test_horizon2_gaussian_vfe_readiness.py",
)

# The PREDECESSORS constant is owned by the validator module; the census
# reports its no-drift fact against that module's repo-relative path.
VALIDATOR_PATH = next(
    path
    for path in CURRENT_FILES
    if path.endswith("verification/horizon_acceptance.py")
)

_SPEC_PREFIX = "specs/"
_PRIOR_07_SUFFIX = "/07-gaussian-vfe-natural-gradient.json"


def _record(path: str, status: str, detail: str) -> CensusRecord:
    return CensusRecord(path=path, status=status, detail=detail)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _receipt_disk_path(specs_dir: Path, repo_relative: str) -> Path:
    """Map a repo-relative ``specs/...`` receipt key onto the specs root."""
    if not repo_relative.startswith(_SPEC_PREFIX):
        raise ValueError(f"receipt key outside specs/: {repo_relative}")
    return specs_dir / repo_relative[len(_SPEC_PREFIX) :]


def _read_receipt(disk_path: Path) -> bytes:
    """Read receipt bytes, failing closed with the precise reason."""
    try:
        return disk_path.read_bytes()
    except OSError as exc:
        raise ValueError(f"missing/unreadable ({exc})") from exc


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _parse_receipt(data: bytes) -> dict[str, Any]:
    """Parse strict JSON receipt bytes, failing closed with the reason."""
    receipt: dict[str, Any] = load_strict_json(data)
    _require(isinstance(receipt, dict), "receipt JSON root must be an object")
    return receipt


def _receipt_source_map(receipt: dict[str, Any]) -> dict[str, Any]:
    sources: dict[str, Any] = receipt.get("source_sha256", {})
    _require(isinstance(sources, dict), "source_sha256 map malformed")
    return sources


def _live_digests(repo_root: Path, names: list[str]) -> dict[str, str | None]:
    """Hash each live file, recording ``None`` for missing/unreadable paths."""
    live: dict[str, str | None] = {}
    try:
        snapshot = source_snapshot(repo_root, sorted(names))
    except (OSError, ValueError):
        snapshot = None
    if snapshot is not None:
        for name, digest in snapshot.items():
            live[name] = digest
        return live
    for name in sorted(names):
        try:
            live[name] = source_snapshot(repo_root, [name])[name]
        except (OSError, ValueError):
            live[name] = None
    return live


def _terminal_receipt(
    specs_dir: Path, repo_root: Path
) -> tuple[CensusRecord, list[CensusRecord]]:
    """Classify the terminal receipt, then each captured native file."""
    try:
        data = _read_receipt(_receipt_disk_path(specs_dir, TERMINAL_RECEIPT))
        receipt = _parse_receipt(data)
    except ValueError as exc:
        return _record(TERMINAL_RECEIPT, LIVE_RED, f"terminal receipt {exc}"), []
    structural = _receipt_structural_problems(receipt)
    if structural:
        return (
            _record(TERMINAL_RECEIPT, LIVE_RED, "; ".join(structural)),
            [],
        )
    evidence = receipt["native_evidence"]
    before = evidence["source_before"]
    after = evidence["source_after"]
    if before != after:
        return (
            _record(
                TERMINAL_RECEIPT,
                LIVE_RED,
                "native capture inconsistent: source_before != source_after "
                "(horizon_acceptance.py:592)",
            ),
            [],
        )
    try:
        plane = native_source_paths(repo_root)
    except (OSError, ValueError) as exc:
        return (
            _record(TERMINAL_RECEIPT, LIVE_RED, f"native plane unavailable: {exc}"),
            [],
        )
    if set(before) != set(plane):
        return (
            _record(
                TERMINAL_RECEIPT,
                LIVE_RED,
                "native capture roster differs from the live native plane",
            ),
            [],
        )
    live = _live_digests(repo_root, sorted(before))
    records: list[CensusRecord] = []
    stale: list[str] = []
    unreadable: list[str] = []
    for name in sorted(before):
        recorded = before[name]
        live_digest = live.get(name)
        if live_digest is None:
            unreadable.append(name)
            records.append(
                _record(
                    name,
                    LIVE_RED,
                    "captured file missing/unreadable on the live tree",
                )
            )
        elif live_digest != recorded:
            stale.append(name)
            records.append(
                _record(
                    name,
                    STALE,
                    f"capture digest {recorded[:12]} predates live {live_digest[:12]}",
                )
            )
        else:
            records.append(_record(name, INTACT, "capture entry matches live tree"))
    if unreadable:
        return (
            _record(
                TERMINAL_RECEIPT,
                LIVE_RED,
                "native capture cannot be compared: " + ", ".join(sorted(unreadable)),
            ),
            records,
        )
    if stale:
        return (
            _record(
                TERMINAL_RECEIPT,
                STALE,
                "native source capture stale or changed "
                f"(horizon_acceptance.py:592): {len(stale)} captured file(s) "
                "differ from the live tree",
            ),
            records,
        )
    return (
        _record(
            TERMINAL_RECEIPT,
            INTACT,
            "terminal receipt accepted; native capture matches the live "
            f"native plane ({len(before)} files)",
        ),
        records,
    )


def _receipt_structural_problems(receipt: dict[str, Any]) -> list[str]:
    """Gate fields and the predecessor binding the census requires intact."""
    problems: list[str] = []
    if type(receipt.get("schema_version")) is not int or receipt["schema_version"] != 1:
        problems.append("acceptance schema is not version 1")
    if receipt.get("gate") != "H2.7":
        problems.append("terminal is not the H2.7 gate receipt")
    if receipt.get("decision") != "accepted":
        problems.append("terminal is not accepted")
    if receipt.get("predecessors") != acceptance.PREDECESSORS:
        problems.append("predecessor chain differs from reviewed whitelist")
    evidence = receipt.get("native_evidence")
    if not isinstance(evidence, dict):
        problems.append("native_evidence missing/malformed")
    else:
        for label in ("source_before", "source_after"):
            capture = evidence.get(label)
            if not isinstance(capture, dict) or not all(
                isinstance(key, str) and isinstance(value, str)
                for key, value in capture.items()
            ):
                problems.append(f"native capture map {label} malformed")
    return problems


def _predecessor_chain(specs_dir: Path, repo_root: Path) -> list[CensusRecord]:
    """Classify the PREDECESSORS constant, then each pinned receipt.

    The constant is read from the imported module object, not a copy, so a
    chore's PREDECESSORS patch to the validator file is honored without a
    re-import.
    """
    predecessors = acceptance.PREDECESSORS
    records: list[CensusRecord] = []
    drifted: list[str] = []
    for path, pin in sorted(predecessors.items()):
        try:
            live = _sha256(_read_receipt(_receipt_disk_path(specs_dir, path)))
        except ValueError as exc:
            drifted.append(f"{path} (pin {pin[:12]}, live {exc})")
            continue
        if live != pin:
            drifted.append(f"{path} (pin {pin[:12]}, live {live[:12]})")
    if drifted:
        records.append(
            _record(
                VALIDATOR_PATH,
                LIVE_RED,
                "PREDECESSORS constant no-drift violated: " + "; ".join(drifted),
            )
        )
    else:
        records.append(
            _record(
                VALIDATOR_PATH,
                INTACT,
                "PREDECESSORS constant matches every live predecessor receipt "
                f"({len(predecessors)} pins)",
            )
        )
    for path, pin in sorted(predecessors.items()):
        records.append(_predecessor_receipt(specs_dir, repo_root, path, pin))
    return records


def _predecessor_receipt(
    specs_dir: Path, repo_root: Path, path: str, pin: str
) -> CensusRecord:
    """Classify one pinned receipt: pin, source map, and successor custody."""
    try:
        data = _read_receipt(_receipt_disk_path(specs_dir, path))
        receipt = _parse_receipt(data)
    except ValueError as exc:
        return _record(path, LIVE_RED, f"predecessor receipt {exc}")
    problems: list[str] = []
    digest = _sha256(data)
    if digest != pin:
        problems.append(
            f"receipt digest drift from PREDECESSORS pin ({pin[:12]} -> {digest[:12]})"
        )
    if path == R0_SUCCESSOR:
        problems.extend(_successor_custody_problems(receipt, repo_root))
    else:
        problems.extend(_source_map_problems(receipt, repo_root, path))
    if problems:
        return _record(path, LIVE_RED, "; ".join(problems))
    return _record(path, INTACT, "predecessor receipt matches its pin and live source")


def _source_map_problems(
    receipt: dict[str, Any], repo_root: Path, path: str
) -> list[str]:
    """Compare a pinned receipt's source map to the live tree."""
    try:
        sources = _receipt_source_map(receipt)
    except ValueError as exc:
        return [str(exc)]
    problems: list[str] = []
    exempt = path.endswith(_PRIOR_07_SUFFIX)
    for name in sorted(sources):
        if exempt and name in AUTHORIZED_PRIOR_DRIFT:
            continue
        live = _live_digests(repo_root, [name]).get(name)
        if live is None:
            problems.append(f"stale predecessor source: {name} missing/unreadable")
        elif live != sources[name]:
            problems.append(f"stale predecessor source: {name}")
    return problems


def _successor_custody_problems(receipt: dict[str, Any], repo_root: Path) -> list[str]:
    """The R0 successor binds current digests and three identical probe maps."""
    problems: list[str] = []
    sources = receipt.get("source_sha256")
    if not isinstance(sources, dict):
        problems.append("R0 successor source_sha256 map missing/malformed")
        sources = None
    else:
        for name in sorted(sources):
            live = _live_digests(repo_root, [name]).get(name)
            if live is None:
                problems.append(
                    f"R0 successor custody digest drift: {name} missing/unreadable"
                )
            elif live != sources[name]:
                problems.append(f"R0 successor custody digest drift: {name}")
    evidence = receipt.get("native_evidence")
    if not isinstance(evidence, dict):
        problems.append("R0 successor native_evidence missing/malformed")
        return problems
    if evidence.get("status") != "verified":
        problems.append("R0 current native evidence pending")
    if evidence.get("historical_evidence_reused") is not False:
        problems.append("R0 historical execution reused")
    probes = evidence.get("probes")
    if not isinstance(probes, list):
        problems.append("R0 successor probes malformed")
        return problems
    for index, probe in enumerate(probes):
        if not isinstance(probe, dict):
            problems.append(f"R0 probe {index} malformed")
        elif (
            probe.get("source_sha256") != sources or probe.get("pytest_exit_code") != 0
        ):
            problems.append(f"R0 probe {index} source mismatch")
    return problems


def census(specs_dir: Path, repo_root: Path) -> Census:
    """Enumerate the H2.7 custody surface against the live tree.

    ``specs_dir`` locates the receipt chain (normally ``repo_root / "specs"``);
    ``repo_root`` locates every hashed source file. Both are injectable so
    tests drive the census through isolated evidence fixtures instead of the
    live tree.
    """
    terminal, capture = _terminal_receipt(specs_dir, repo_root)
    return Census(
        (
            terminal,
            *_predecessor_chain(specs_dir, repo_root),
            *capture,
        )
    )
