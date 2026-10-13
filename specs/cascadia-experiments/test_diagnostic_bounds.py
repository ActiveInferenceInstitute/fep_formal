"""Receipt type, strict parsing, stale-input and create-only boundary checks."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

SCRIPT = Path(__file__).with_name("verify_diagnostic_bounds.py")


@pytest.fixture(scope="module")
def bounds() -> ModuleType:
    sys.path.insert(0, str(SCRIPT.parent))
    spec = importlib.util.spec_from_file_location("cascadia_diagnostic_bounds", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_compiler_exit_status_cannot_be_boolean(bounds: ModuleType) -> None:
    with pytest.raises(ValueError, match="field types"):
        bounds.CompilerRecord(True, "", "")


def test_receipt_parser_rejects_duplicate_exit_status(
    tmp_path: Path, bounds: ModuleType
) -> None:
    path = tmp_path / "compiler.json"
    path.write_text(
        '{"return_code":1,"return_code":0,"stdout":"","stderr":""}', encoding="utf-8"
    )
    with pytest.raises(ValueError, match="duplicate key"):
        bounds._load_record(path)


def test_stale_inputs_fail_before_any_native_dependency(bounds: ModuleType) -> None:
    compiler = bounds.CompilerRecord(0, "", "")
    record = bounds.BoundsReceipt({}, {}, "", compiler, compiler, {}, True)
    with pytest.raises(ValueError, match="inputs have changed"):
        bounds.check_evidence(record)


def test_compilation_refuses_existing_attempt(
    tmp_path: Path, bounds: ModuleType
) -> None:
    marker = tmp_path / "failed-attempt.json"
    marker.write_bytes(b"retained failure")
    with pytest.raises(FileExistsError):
        bounds.compile_bounds(tmp_path)
    assert marker.read_bytes() == b"retained failure"


def test_cli_explicitly_selects_compile_or_check() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode != 0 and "required" in result.stderr
