"""Typed receipts and live-source admission for generic Cascadia score bounds."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from fep_formal.verification._jsonutil import load_strict_json

SLICE: Final = Path(__file__).resolve().parent
ROOT: Final = SLICE.parents[1]
THEOREMS: Final = (
    "brier_nonneg",
    "probability_le_one",
    "sum_squares_le_one",
    "brier_identity",
    "brier_le_two",
    "wrong_point_mass_score",
)
ALLOWED_AXIOMS: Final = {"propext", "Classical.choice", "Quot.sound"}


@dataclass(frozen=True, slots=True)
class CompilerRecord:
    return_code: int
    stdout: str
    stderr: str

    def __post_init__(self) -> None:
        if (
            type(self.return_code) is not int
            or type(self.stdout) is not str
            or type(self.stderr) is not str
        ):
            message = "invalid compiler record field types"
            raise ValueError(message)


@dataclass(frozen=True, slots=True)
class BoundsReceipt:
    """Evidence for the named real-number theorems, not a simulation instance."""

    inputs: dict[str, str]
    files: dict[str, str]
    mathlib_revision: str
    compiler: CompilerRecord
    positive: CompilerRecord
    controls: dict[str, CompilerRecord]
    diagnostic_theorems_verified: bool
    native_claim_ready: bool = False

    def __post_init__(self) -> None:
        if (
            type(self.diagnostic_theorems_verified) is not bool
            or type(self.native_claim_ready) is not bool
        ):
            message = "invalid diagnostic receipt flag types"
            raise ValueError(message)


def _load_record(path: Path) -> CompilerRecord:
    return CompilerRecord(**load_strict_json(path.read_bytes()))


def _load_receipt(path: Path) -> BoundsReceipt:
    data = load_strict_json(path.read_bytes())
    data["compiler"] = CompilerRecord(**data["compiler"])
    data["positive"] = CompilerRecord(**data["positive"])
    data["controls"] = {
        name: CompilerRecord(**row) for name, row in data["controls"].items()
    }
    return BoundsReceipt(**data)


def fingerprints() -> dict[str, str]:
    """Bind theorem/tool bytes and the maintained Lean/Mathlib pin files."""
    paths = (
        SLICE / "DiagnosticBounds.lean",
        Path(__file__),
        SLICE / "verify_diagnostic_bounds.py",
        ROOT / "lean/lean-toolchain",
        ROOT / "lean/lakefile.lean",
        ROOT / "lean/lake-manifest.json",
        ROOT / "src/fep_formal/verification/_jsonutil.py",
        ROOT / "src/fep_formal/verification/_subprocess.py",
    )
    return {
        path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in paths
    }


def check_evidence(record: BoundsReceipt) -> None:
    """Refuse stale inputs, warnings, unlisted axioms or non-failing controls."""
    if record.inputs != fingerprints():
        message = "diagnostic proof inputs have changed"
        raise ValueError(message)
    manifest = json.loads((ROOT / "lean/lake-manifest.json").read_bytes())
    expected_revision = next(
        p["rev"] for p in manifest["packages"] if p["name"] == "mathlib"
    )
    actual_revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT / "lean/.lake/packages/mathlib",
        text=True,
        timeout=30,
    ).strip()
    if (
        record.mathlib_revision != expected_revision
        or actual_revision != expected_revision
    ):
        message = "Mathlib checkout does not match the maintained pin"
        raise ValueError(message)
    pin = (
        (ROOT / "lean/lean-toolchain")
        .read_text(encoding="utf-8")
        .strip()
        .rsplit(":v", 1)[1]
    )
    if record.compiler.return_code != 0 or not re.search(
        rf"version {re.escape(pin)}[,)]", record.compiler.stdout
    ):
        message = "compiler does not match the maintained pin"
        raise ValueError(message)
    output = record.positive.stdout + record.positive.stderr
    if record.positive.return_code != 0 or re.search(
        r"\b(error|warning|sorry)\b", output
    ):
        message = "positive diagnostic proof compilation failed"
        raise ValueError(message)
    reports = re.findall(
        r"'CascadiaDiagnostics\.(\w+)' depends on axioms: \[([^]]*)\]", output
    )
    if len(reports) != len(THEOREMS) or {name for name, _ in reports} != set(THEOREMS):
        message = "diagnostic theorem axiom roster is incomplete"
        raise ValueError(message)
    if any(
        set(filter(None, axioms.split(", "))) - ALLOWED_AXIOMS for _, axioms in reports
    ):
        message = "diagnostic theorem depends on an unapproved axiom"
        raise ValueError(message)
    if set(record.controls) != {"bound_one", "wrong_binary_score"} or any(
        row.return_code != 1 or "error:" not in row.stdout + row.stderr
        for row in record.controls.values()
    ):
        message = "false diagnostic controls did not fail"
        raise ValueError(message)
    if not record.diagnostic_theorems_verified or record.native_claim_ready:
        message = "invalid diagnostic evidence flags"
        raise ValueError(message)
