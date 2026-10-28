# /// script
# requires-python = ">=3.14"
# dependencies = []
# ///
# How to run: uv run python specs/cascadia-experiments/verify_diagnostic_bounds.py --compile OUTPUT
"""Compile generic score bounds and false controls; check retained evidence read-only."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path
from typing import assert_never

from cascadia_diagnostic_evidence import (
    ROOT,
    SLICE,
    BoundsReceipt,
    CompilerRecord,
    _load_receipt,
    _load_record,
    check_evidence,
    fingerprints,
)

from fep_formal.verification._subprocess import run_process_group


def _timeout_text(value: str | bytes | None) -> str:
    match value:
        case None:
            return ""
        case bytes():
            return value.decode("utf-8", errors="replace")
        case str():
            return value
        case unreachable:
            assert_never(unreachable)


def _run(arguments: Sequence[str], destination: Path) -> CompilerRecord:
    try:
        result = run_process_group(
            ["lake", "env", "lean", *arguments],
            cwd=ROOT / "lean",
            capture=True,
            timeout=300,
            check=False,
        )
        record = CompilerRecord(
            return_code=result.returncode, stdout=result.stdout, stderr=result.stderr
        )
    except subprocess.TimeoutExpired as error:
        record = CompilerRecord(
            return_code=124,
            stdout=_timeout_text(error.stdout),
            stderr=_timeout_text(error.stderr) + "\ncompiler timeout after 300 seconds",
        )
    with destination.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(asdict(record), indent=2, sort_keys=True) + "\n")
    return record


def compile_bounds(output: Path) -> Path:
    """Preserve a new attempt before compiling; readiness requires both controls."""
    output = output.absolute()
    output.mkdir(parents=True, exist_ok=False)
    inputs = fingerprints()
    source = (SLICE / "DiagnosticBounds.lean").read_text(encoding="utf-8")
    variants = {
        "positive": source,
        "bound_one": source.replace(
            "brier p truth ≤ 2 := by", "brier p truth ≤ 1 := by"
        ),
        "wrong_binary_score": source.replace(
            "else 1) 0 = 2 := by", "else 1) 0 = 1 := by"
        ),
    }
    compiler = _run(("--version",), output / "compiler.json")
    records = {}
    for name, content in variants.items():
        if name != "positive" and content == source:
            message = "diagnostic mutation did not change its target"
            raise ValueError(message)
        path = output / f"{name}.lean"
        with path.open("x", encoding="utf-8") as stream:
            stream.write(content)
        records[name] = _run(
            ("-DwarningAsError=true", str(path)), output / f"{name}.json"
        )
    files = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in output.iterdir()
    }
    mathlib_revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT / "lean/.lake/packages/mathlib",
        text=True,
        timeout=30,
    ).strip()
    record = BoundsReceipt(
        inputs=inputs,
        files=files,
        mathlib_revision=mathlib_revision,
        compiler=compiler,
        positive=records["positive"],
        controls={name: records[name] for name in ("bound_one", "wrong_binary_score")},
        diagnostic_theorems_verified=True,
    )
    check_evidence(record)
    receipt = output / "receipt.json"
    with receipt.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(asdict(record), indent=2, sort_keys=True) + "\n")
    return receipt


def check_bounds(output: Path) -> None:
    """Recheck exact input and output bytes without launching Lean or repairing."""
    record = _load_receipt(output / "receipt.json")
    if {p.name for p in output.iterdir()} != set(record.files) | {"receipt.json"}:
        message = "diagnostic proof output roster differs"
        raise ValueError(message)
    for name, digest in record.files.items():
        if (
            Path(name).name != name
            or (output / name).is_symlink()
            or hashlib.sha256((output / name).read_bytes()).hexdigest() != digest
        ):
            message = "diagnostic proof output digest differs"
            raise ValueError(message)
    for name, expected in (
        ("compiler", record.compiler),
        ("positive", record.positive),
        *record.controls.items(),
    ):
        if _load_record(output / f"{name}.json") != expected:
            message = "diagnostic compiler transcript differs from receipt"
            raise ValueError(message)
    source = (SLICE / "DiagnosticBounds.lean").read_text(encoding="utf-8")
    variants = {
        "positive": source,
        "bound_one": source.replace(
            "brier p truth ≤ 2 := by", "brier p truth ≤ 1 := by"
        ),
        "wrong_binary_score": source.replace(
            "else 1) 0 = 2 := by", "else 1) 0 = 1 := by"
        ),
    }
    if any(
        (output / f"{name}.lean").read_text(encoding="utf-8") != content
        for name, content in variants.items()
    ):
        message = "diagnostic compiled source differs from its specified instance"
        raise ValueError(message)
    check_evidence(record)


def main(argv: Sequence[str] | None = None) -> int:
    """Select actual compilation or a read-only evidence recheck explicitly."""
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--compile", type=Path)
    mode.add_argument("--check", type=Path)
    args = parser.parse_args(argv)
    if args.compile is not None:
        print(compile_bounds(args.compile))
    else:
        check_bounds(args.check)
        print("diagnostic theorem evidence matches current inputs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
