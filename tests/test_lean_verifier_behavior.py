"""No-toolchain behavioral tests for Lean verification result handling."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from fep_lean.verification import lean_verifier as verifier_module
from fep_lean.verification.lean_verifier import LeanVerifier, VerifyResult


@pytest.mark.parametrize(
    ("output", "timed_out", "expected", "returncode"),
    (
        ("", True, "timeout", 0),
        ("process timed out", False, "timeout", 0),
        ("unsolved goals", False, "tactic_failure", 0),
        ("application type mismatch", False, "arity_mismatch", 0),
        ("could not resolve import Mathlib", False, "missing_import", 0),
        ("unknownIdentifier `oldName`", False, "renamed_identifier", 0),
        ("import Mathlib produced ERROR", False, "missing_import", 0),
        ("unexpected compiler crash", False, "other", 0),
        ("", False, "killed", -9),
        ("unsolved goals", False, "killed", -9),
    ),
)
def test_failure_classification_preserves_distinct_diagnostics(
    output: str,
    timed_out: bool,
    expected: str,
    returncode: int,
) -> None:
    assert (
        verifier_module.classify_failure_kind(
            output,
            timed_out=timed_out,
            returncode=returncode,
        )
        == expected
    )


def test_duration_summary_ignores_skips_and_reports_deterministic_percentiles() -> None:
    results = [
        VerifyResult("fep-001", True, False, duration_s=0.1),
        VerifyResult("fep-002", True, False, duration_s=0.2),
        VerifyResult("fep-003", True, False, duration_s=0.3),
        VerifyResult(
            "fep-004",
            False,
            False,
            duration_s=99.0,
            skip_reason="toolchain unavailable",
        ),
    ]

    assert LeanVerifier.summarize_batch_durations(results) == {
        "count": 3,
        "min_s": 0.1,
        "median_s": 0.2,
        "p95_s": 0.3,
    }
    assert LeanVerifier.summarize_batch_durations(results[3:]) == {
        "count": 0,
        "min_s": 0.0,
        "median_s": 0.0,
        "p95_s": 0.0,
    }


def _isolated_verifier(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> LeanVerifier:
    lean_dir = tmp_path / "lean"
    lean_dir.mkdir()
    (lean_dir / "lakefile.lean").write_text("", encoding="utf-8")
    monkeypatch.setattr(verifier_module, "_ensure_elan_home", lambda: None)
    monkeypatch.setattr(verifier_module, "_find_exe", lambda *_a, **_k: None)
    verifier = LeanVerifier(lean_dir=lean_dir, project_root=tmp_path)
    verifier._lake_exe = "/virtual/lake"
    verifier._lean_exe = None
    return verifier


def test_verifier_preserves_bounded_failure_output_without_invoking_lake(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    verifier = _isolated_verifier(tmp_path, monkeypatch)
    compiler_output = (
        "fixture.lean:1:1: error: application type mismatch\n" + "x" * 9000
    )
    monkeypatch.setattr(
        verifier,
        "_run_lake_lean",
        lambda _path: subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout=compiler_output,
            stderr="",
        ),
    )

    result = verifier.verify_sketch("fep-001", "theorem fixture : True := by sorry")

    assert result.compiles is False
    assert result.has_sorry is True
    assert result.failure_kind == "arity_mismatch"
    assert len(result.stdout) == 8000
    assert result.errors and "type mismatch" in result.errors[0]
    assert list(verifier._sketches_dir.glob("_verify_*.lean")) == []


def _killed_run(calls: list[Path], returncodes: list[int]):
    def _run(path: Path) -> subprocess.CompletedProcess:
        calls.append(path)
        return subprocess.CompletedProcess(
            args=[],
            returncode=returncodes.pop(0),
            stdout="",
            stderr="",
        )

    return _run


def test_killed_sketch_runs_once_without_retry_knob(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    verifier = _isolated_verifier(tmp_path, monkeypatch)
    calls: list[Path] = []
    monkeypatch.setattr(verifier, "_run_lake_lean", _killed_run(calls, [-9]))
    monkeypatch.delenv("FEP_LEAN_VERIFY_RETRY_KILLED", raising=False)

    result = verifier.verify_sketch(
        "fep-killed-off",
        "theorem probe : True := by trivial",
    )

    assert len(calls) == 1
    assert result.compiles is False
    assert result.failure_kind == "killed"
    assert "retries" not in result.as_dict()


def test_killed_sketch_retries_once_and_reports_retries(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    verifier = _isolated_verifier(tmp_path, monkeypatch)
    calls: list[Path] = []
    monkeypatch.setattr(verifier, "_run_lake_lean", _killed_run(calls, [-9, -9]))
    monkeypatch.setenv("FEP_LEAN_VERIFY_RETRY_KILLED", "1")

    result = verifier.verify_sketch(
        "fep-killed-retry",
        "theorem probe : True := by trivial",
    )

    assert len(calls) == 2
    assert result.compiles is False
    assert result.failure_kind == "killed"
    assert result.retries == 1
    assert result.as_dict()["retries"] == 1


def test_retry_outcome_wins_when_second_attempt_compiles(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    verifier = _isolated_verifier(tmp_path, monkeypatch)
    calls: list[Path] = []
    monkeypatch.setattr(verifier, "_run_lake_lean", _killed_run(calls, [-9, 0]))
    monkeypatch.setenv("FEP_LEAN_VERIFY_RETRY_KILLED", "1")

    result = verifier.verify_sketch(
        "fep-killed-success",
        "theorem probe : True := by trivial",
    )

    assert len(calls) == 2
    assert result.compiles is True
    assert result.retries == 1


def test_non_killed_failure_never_retries_even_with_knob(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    verifier = _isolated_verifier(tmp_path, monkeypatch)

    def _run(_path: Path) -> subprocess.CompletedProcess:
        return subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout="probe.lean:1:1: error: application type mismatch",
            stderr="",
        )

    monkeypatch.setattr(verifier, "_run_lake_lean", _run)
    monkeypatch.setenv("FEP_LEAN_VERIFY_RETRY_KILLED", "1")

    result = verifier.verify_sketch("fep-nokill", "theorem probe : True := by trivial")

    assert result.compiles is False
    assert result.failure_kind == "arity_mismatch"
    assert result.retries == 0


def test_mathlib_probe_rejects_a_partial_leaf_cache_without_running_lake(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    verifier = _isolated_verifier(tmp_path, monkeypatch)
    build_root = verifier._lean_dir / ".lake/packages/mathlib/.lake/build/lib/lean"
    build_root.mkdir(parents=True)
    (build_root / "Mathlib.olean").write_bytes(b"root")

    ok, message = verifier.check_mathlib_built()

    assert ok is False
    assert "required leaf .olean files missing" in message
    assert "Mathlib/Data/Real/Basic.olean" in message


def test_mathlib_probe_reports_a_missing_root_olean_without_running_lake(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    verifier = _isolated_verifier(tmp_path, monkeypatch)
    (verifier._lean_dir / ".lake" / "packages" / "mathlib").mkdir(parents=True)
    build_root = verifier._lean_dir / ".lake/packages/mathlib/.lake/build/lib/lean"

    ok, message = verifier.check_mathlib_built()

    assert ok is False
    assert str(build_root / "Mathlib.olean") in message


def test_run_lake_lean_fails_closed_without_an_executable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    verifier = _isolated_verifier(tmp_path, monkeypatch)
    verifier._lake_exe = None

    with pytest.raises(RuntimeError, match="lake executable is unavailable"):
        verifier._run_lake_lean(tmp_path / "sketch.lean")
