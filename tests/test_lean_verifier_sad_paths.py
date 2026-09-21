"""Sad path tests for fep_lean.verification.lean_verifier using real process boundaries."""

from __future__ import annotations

from pathlib import Path

import pytest

from fep_lean.verification.lean_verifier import (
    LeanVerifier,
    _direct_toolchain_bin,
    _ensure_elan_home,
    _find_exe,
)

PROJ = Path(__file__).resolve().parent.parent

pytestmark = pytest.mark.serial_lean


def test_ensure_elan_home_oserror(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    elan_home = tmp_path / "elan"
    elan_home.mkdir()
    elan_home.chmod(0o555)  # un-writable
    monkeypatch.setenv("ELAN_HOME", str(elan_home / "nested"))

    # Should catch OSError and pass silently
    _ensure_elan_home()

    elan_home.chmod(0o755)


def test_direct_toolchain_bin_oserrors(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    temporary_proj = tmp_path / "temporary_proj"

    # Isolate from real ~/.elan
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("ELAN_HOME", str(tmp_path / "elan"))

    # 1. Missing directory
    assert _direct_toolchain_bin(temporary_proj) is None

    # 2. Cannot read lean-toolchain file
    temporary_proj.mkdir()
    lean_dir = temporary_proj / "lean"
    lean_dir.mkdir()
    (
        lean_dir / "lean-toolchain"
    ).mkdir()  # directory instead of file will cause read_text error
    assert _direct_toolchain_bin(temporary_proj) is None


def test_find_exe_explicit_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    custom_lean = tmp_path / "custom_lean"
    custom_lean.write_text("temporary binary")
    monkeypatch.setenv("FEP_LEAN_LEAN_EXE", str(custom_lean))

    # find_exe uses FEP_LEAN_{NAME_UPPER}_EXE
    assert _find_exe("lean") == str(custom_lean)


def test_find_exe_elan_proxy(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    # Set ELAN_HOME to tmp_path and provide a proxy
    proxy_bin = tmp_path / "bin"
    proxy_bin.mkdir()
    (proxy_bin / "lean").write_text("")

    monkeypatch.setenv("PATH", str(tmp_path))
    monkeypatch.setenv("LEAN_EXE", "")
    monkeypatch.setenv("ELAN_HOME", str(tmp_path))

    res = _find_exe("lean")
    assert str(res).endswith("lean")


def test_lean_verifier_init_defaults(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    lv = LeanVerifier(lean_dir=None, project_root=None)
    assert str(lv._project_root) == str(tmp_path)
    assert lv._lean_dir.name == "lean"


def test_check_lake_available_oserror(tmp_path: Path):
    lv = LeanVerifier(PROJ / "lean", PROJ)
    # A directory instead of an executable will throw PermissionError/OSError when run
    lake_dir = tmp_path / "lake_dir"
    lake_dir.mkdir()
    lv._lake_exe = str(lake_dir)
    assert lv.check_lake_available() is False


def test_lean_version_not_found(tmp_path: Path):
    lv = LeanVerifier(PROJ / "lean", PROJ)
    lv._lean_exe = None
    assert lv.lean_version() is None


def test_lean_version_sandbox_errors(tmp_path: Path):
    lv = LeanVerifier(PROJ / "lean", PROJ)

    temporary_lean = tmp_path / "lean"
    temporary_lean.write_text(
        "#!/bin/sh\necho 'settings.toml: operation not permitted' >&2\nexit 1\n"
    )
    temporary_lean.chmod(0o755)
    lv._lean_exe = str(temporary_lean)

    import fep_lean.verification.lean_verifier

    fep_lean.verification.lean_verifier._LEAN_VERSION_CACHE.clear()

    v = lv.lean_version()
    assert v is not None
    assert v.startswith("lean (")

    temporary_lean2 = tmp_path / "lean2"
    temporary_lean2.write_text("#!/bin/sh\necho 'segmentation fault' >&2\nexit 1\n")
    temporary_lean2.chmod(0o755)
    lv._lean_exe = str(temporary_lean2)

    fep_lean.verification.lean_verifier._LEAN_VERSION_CACHE.clear()

    v = lv.lean_version()
    assert v is not None
    assert "exit 1" in v


def test_lean_version_oserror(tmp_path: Path):
    lv = LeanVerifier(PROJ / "lean", PROJ)
    lake_dir = tmp_path / "lake_dir"
    lake_dir.mkdir()
    lv._lean_exe = str(lake_dir)
    import fep_lean.verification.lean_verifier

    fep_lean.verification.lean_verifier._LEAN_VERSION_CACHE.clear()
    assert lv.lean_version() is None


def test_check_mathlib_built_sad_paths(tmp_path: Path):
    lv = LeanVerifier(tmp_path / "lean", tmp_path)
    ok, msg = lv.check_mathlib_built()
    assert ok is False
    assert "Mathlib" in msg


def test_verify_sketch_lake_not_found():
    lv = LeanVerifier(PROJ / "lean", PROJ)
    lv._lake_exe = None
    res = lv.verify_sketch("topic-1", "sorry")
    assert res.compiles is False
    assert "lake not found" in res.skip_reason


def test_verify_sketch_lean_dir_not_found(tmp_path: Path):
    lv = LeanVerifier(tmp_path / "missing_lean", tmp_path)
    lv._lake_exe = "/temporary/lake"
    res = lv.verify_sketch("topic-1", "sorry")
    assert res.compiles is False
    assert res.skip_reason
    assert "lakefile" in res.skip_reason or "lean_dir" in res.skip_reason


def test_verify_sketch_lakefile_not_found(tmp_path: Path):
    lean_dir = tmp_path / "lean"
    lean_dir.mkdir()
    lv = LeanVerifier(lean_dir, tmp_path)
    lv._lake_exe = "/temporary/lake"
    res = lv.verify_sketch("topic-1", "sorry")
    assert res.compiles is False
    assert "lakefile.lean not found" in res.skip_reason


def test_verify_sketch_subprocess_timeout(tmp_path: Path):
    lean_dir = tmp_path / "lean"
    lean_dir.mkdir()
    (lean_dir / "lakefile.lean").write_text("")
    (lean_dir / "FepSketches").mkdir()

    lv = LeanVerifier(lean_dir, tmp_path)

    temporary_lake = tmp_path / "lake"
    temporary_lake.write_text("#!/bin/sh\nsleep 10\n")
    temporary_lake.chmod(0o755)

    lv._lake_exe = str(temporary_lake)
    import fep_lean.verification.lean_verifier

    original_timeout = fep_lean.verification.lean_verifier._VERIFICATION_TIMEOUT
    fep_lean.verification.lean_verifier._VERIFICATION_TIMEOUT = 1

    try:
        res = lv.verify_sketch("topic-1", "sorry")
        assert res.compiles is False
        assert "timeout after" in res.skip_reason
    finally:
        fep_lean.verification.lean_verifier._VERIFICATION_TIMEOUT = original_timeout


def test_verify_sketch_oserror(tmp_path: Path):
    lean_dir = tmp_path / "lean"
    lean_dir.mkdir()
    (lean_dir / "lakefile.lean").write_text("")
    (lean_dir / "FepSketches").mkdir()

    lv = LeanVerifier(lean_dir, tmp_path)

    lake_dir = tmp_path / "lake_dir_temporary"
    lake_dir.mkdir()
    lv._lake_exe = str(lake_dir)
    res = lv.verify_sketch("topic-1", "sorry")
    assert res.compiles is False
    assert (
        "Permission denied" in res.skip_reason
        or "Is a directory" in res.skip_reason
        or "Errno 13" in res.skip_reason
    )
