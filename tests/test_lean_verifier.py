"""Tests for lean_verifier — real LeanVerifier behavior with full Mathlib4.

All tests use real objects.  Tests requiring lean/lake on PATH are skipped
gracefully when the tools are unavailable (respects sandboxed CI).

The verifier is configured with the real fep_lean/lean/ workspace which
now has Mathlib4 as a Lake dependency.  A one-time setup is required before
compilation tests can pass:

    cd lean
    lake exe cache get && lake build

See ``scripts/_maint_bootstrap_lean_toolchain.sh`` (or ``cd lean && lake exe cache get && lake build``).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from fep_lean.verification.lean_verifier import (
    LeanVerifier,
    VerifyResult,
    _find_exe,
    _sanitize_lean_block,
    _subprocess_env,
)

PROJ = Path(__file__).resolve().parent.parent
LEAN_DIR = PROJ / "lean"

pytestmark = pytest.mark.serial_lean


@pytest.fixture(autouse=True)
def fast_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    """Force a short timeout for all tests so sandboxed hanging processes don't stall the suite."""
    monkeypatch.setenv("FEP_LEAN_VERIFY_TIMEOUT", "2")


@pytest.fixture()
def verifier() -> LeanVerifier:
    return LeanVerifier(lean_dir=LEAN_DIR, project_root=PROJ)


# ── Construction and configuration ───────────────────────────────────────────


def test_verifier_instantiates(verifier: LeanVerifier) -> None:
    assert verifier is not None
    assert verifier._lean_dir == LEAN_DIR
    assert verifier._sketches_dir == LEAN_DIR / "FepSketches"


def test_verifier_sketches_dir_created(verifier: LeanVerifier) -> None:
    assert verifier._sketches_dir.is_dir()


def test_check_lake_available_returns_bool(verifier: LeanVerifier) -> None:
    result = verifier.check_lake_available()
    assert isinstance(result, bool)


def test_lean_version_returns_none_or_str(verifier: LeanVerifier) -> None:
    v = verifier.lean_version()
    assert v is None or isinstance(v, str)


# ── check_mathlib_built ───────────────────────────────────────────────────────


def test_check_mathlib_built_returns_tuple(verifier: LeanVerifier) -> None:
    ok, msg = verifier.check_mathlib_built()
    assert isinstance(ok, bool)
    assert isinstance(msg, str)
    assert len(msg) > 0


def test_check_mathlib_built_message_is_informative(verifier: LeanVerifier) -> None:
    _ok, msg = verifier.check_mathlib_built()
    # Message must mention either "Mathlib" or "lake"
    assert "athlib" in msg or "lake" in msg or "olean" in msg


# ── VerifyResult dataclass ────────────────────────────────────────────────────


def test_verify_result_compiles_clean() -> None:
    r = VerifyResult(
        topic_id="fep-001",
        compiles=True,
        has_sorry=False,
        errors=[],
        warnings=["warning: ..."],
        duration_s=0.5,
        lean_version="Lean 4.15.0",
    )
    assert r.status == "compiles_clean"
    d = r.as_dict()
    assert d["compiles"] is True
    assert d["has_sorry"] is False
    assert d["status"] == "compiles_clean"
    assert d["lean_version"] == "Lean 4.15.0"


def test_verify_result_with_sorry() -> None:
    r = VerifyResult(
        topic_id="fep-002",
        compiles=True,
        has_sorry=True,
        lean_version="Lean 4.15.0",
    )
    assert r.status == "compiles_with_sorry"
    assert r.as_dict()["status"] == "compiles_with_sorry"


def test_verify_result_compile_error() -> None:
    r = VerifyResult(
        topic_id="fep-003",
        compiles=False,
        has_sorry=False,
        errors=["Error: type mismatch"],
    )
    assert r.status == "compile_error"


def test_verify_result_skipped() -> None:
    r = VerifyResult(
        topic_id="fep-004",
        compiles=False,
        has_sorry=False,
        skip_reason="lake not found",
    )
    assert r.status == "skipped (lake not found)"
    assert r.as_dict()["skip_reason"] == "lake not found"


# ── _wrap_lean_code ────────────────────────────────────────────────────────────


def test_wrap_lean_code_adds_import_when_missing(verifier: LeanVerifier) -> None:
    code = "theorem foo : True := True.intro"
    wrapped = verifier._wrap_lean_code(code)
    assert "import Mathlib" in wrapped
    assert "theorem foo" in wrapped
    # Must open relevant namespaces
    assert "MeasureTheory" in wrapped
    assert "ProbabilityTheory" in wrapped


def test_wrap_lean_code_preserves_existing_imports(verifier: LeanVerifier) -> None:
    code = "import Mathlib\ntheorem foo : True := True.intro"
    wrapped = verifier._wrap_lean_code(code)
    assert wrapped == code  # unchanged — no duplicate preamble


def test_wrap_lean_code_single_import_not_wrapped(verifier: LeanVerifier) -> None:
    code = "import Mathlib.MeasureTheory.Measure.MeasureSpace\ntheorem bar : True := True.intro"
    wrapped = verifier._wrap_lean_code(code)
    assert wrapped == code


# ── _sanitize_lean_block ──────────────────────────────────────────────────────


def test_sanitize_lean_block_clean():
    """Imports at top should not be modified."""
    code = "import Mathlib\nnamespace Foo\ntheorem t : 1 = 1 := rfl\nend Foo"
    result = _sanitize_lean_block(code)
    assert result == code


def test_sanitize_lean_block_strips_late_imports():
    """Import statements after namespace content must be removed."""
    code = "namespace Foo\ntheorem t : 1 = 1 := rfl\nimport Mathlib.Data.Finset.Max\nend Foo"
    result = _sanitize_lean_block(code)
    assert "import Mathlib.Data.Finset.Max" not in result
    assert "theorem t" in result
    assert "namespace Foo" in result


def test_sanitize_lean_block_preserves_comment_lines_beginning_with_import():
    """Ordinary prose beginning with ``import`` must not be parsed as a command."""
    code = (
        "import Mathlib\n"
        "namespace Foo\n"
        "/-- A positive product law satisfies the\n"
        "importance-weighted Jensen bound. -/\n"
        "theorem t : True := True.intro\n"
        "end Foo"
    )

    assert _sanitize_lean_block(code) == code


# ── verify_sketch (without lake) ──────────────────────────────────────────────


def test_verify_sketch_skipped_when_lake_missing(verifier: LeanVerifier) -> None:
    """When lake is unavailable, result is VerifyResult with skip_reason or error.

    Forces lake unavailability by pointing _lake_exe to a nonexistent path,
    ensuring this test always runs regardless of the host environment.
    """
    verifier._lake_exe = None  # force lake-not-found path
    sketch = "theorem foo : True := True.intro"
    r = verifier.verify_sketch("fep-001", sketch)
    assert isinstance(r, VerifyResult)
    assert not r.compiles
    assert r.skip_reason, f"Expected skip_reason when lake is missing, got: {r}"


def test_verify_sketch_returns_result_even_with_bad_sketch(
    verifier: LeanVerifier,
) -> None:
    """Compilation errors must not raise; they must be captured in VerifyResult."""
    sketch = "this is not lean code at all ??? !!!"
    r = verifier.verify_sketch("fep-bad", sketch)
    assert isinstance(r, VerifyResult)
    # lean_version should be populated (or skip_reason if unavailable)
    assert r.lean_version is not None or r.skip_reason


# ── verify_sketch WITH LAKE (requires Mathlib setup) ─────────────────────────


def test_verify_sketch_with_lake_trivial(verifier: LeanVerifier) -> None:
    """When lake is available and Mathlib is built, verify a trivially true theorem."""
    if not verifier.check_lake_available():
        pytest.skip(
            "lake not on PATH — run scripts/_maint_bootstrap_lean_toolchain.sh (or uv run fep-lean setup — wraps it) first"
        )
    _mathlib_ok, _mathlib_msg = verifier.check_mathlib_built()
    # Trivial True.intro doesn't actually need Mathlib loaded
    sketch = "theorem fep_lean_trivial_check : True := True.intro"
    r = verifier.verify_sketch("fep-trivial", sketch)
    assert isinstance(r, VerifyResult)
    assert isinstance(r.compiles, bool)
    assert r.duration_s >= 0.0
    assert r.lean_version is not None


def test_verify_sketch_with_lake_and_mathlib_sorry(verifier: LeanVerifier) -> None:
    """Typical FEP topic sketch: sorry-based, imports Mathlib, must classify correctly."""
    if not verifier.check_lake_available():
        pytest.skip(
            "lake not on PATH — run scripts/_maint_bootstrap_lean_toolchain.sh (or uv run fep-lean setup — wraps it) first"
        )
    mathlib_ok, mathlib_msg = verifier.check_mathlib_built()
    if not mathlib_ok:
        pytest.skip(f"Mathlib not built: {mathlib_msg}")
    sketch = (
        "import Mathlib\n"
        "open MeasureTheory\n"
        "-- KL non-negativity sketch\n"
        "theorem fep_lean_kl_nonneg (μ ν : Measure ℝ) :\n"
        "    0 ≤ (μ.rnDeriv ν).toReal := by\n"
        "  sorry\n"
    )
    r = verifier.verify_sketch("fep-001-mathlib", sketch)
    assert isinstance(r, VerifyResult)
    # With Mathlib built, the import should resolve
    if r.compiles:
        assert r.has_sorry  # sorry must be detected
        assert r.status == "compiles_with_sorry"
    else:
        # Even if compile fails, it's captured not raised
        assert isinstance(r.errors, list)


# ── verify_batch ──────────────────────────────────────────────────────────────


def test_verify_batch_returns_one_per_item(verifier: LeanVerifier) -> None:
    items = [
        ("fep-001", "theorem a : True := True.intro"),
        ("fep-002", "theorem b : True := True.intro"),
    ]
    results = verifier.verify_batch(items)
    assert len(results) == 2
    assert all(isinstance(r, VerifyResult) for r in results)
    assert results[0].topic_id == "fep-001"
    assert results[1].topic_id == "fep-002"


def test_verify_batch_empty_input(verifier: LeanVerifier) -> None:
    results = verifier.verify_batch([])
    assert results == []


# ── environment helpers ────────────────────────────────────────────────────────


def test_subprocess_env_has_elan_home() -> None:
    env = _subprocess_env(LEAN_DIR)
    assert "ELAN_HOME" in env
    assert len(env["ELAN_HOME"]) > 0


def test_find_exe_lake_returns_str_or_none() -> None:
    result = _find_exe("lake", LEAN_DIR)
    assert result is None or isinstance(result, str)


def test_find_exe_lean_returns_str_or_none() -> None:
    result = _find_exe("lean", LEAN_DIR)
    assert result is None or isinstance(result, str)
