"""Tests for fep_formal.gauss.cli sad paths using genuine filesystem and environment mutation."""

from __future__ import annotations

from pathlib import Path

import pytest

from fep_formal.gauss.cli import _require_gauss_from_env, check_gauss_cli

PROJ = Path(__file__).resolve().parent.parent


def test_require_gauss_from_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("FEP_FORMAL_REQUIRE_GAUSS", "1")
    assert _require_gauss_from_env() is True
    monkeypatch.setenv("FEP_FORMAL_REQUIRE_GAUSS", "false")
    assert _require_gauss_from_env() is False


def test_check_gauss_cli_missing_not_required(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    # Ensure gauss is not on path
    monkeypatch.setenv("PATH", str(tmp_path))
    ok, msg = check_gauss_cli(PROJ, require=False)
    assert ok is True
    assert "not configured" in msg


def test_check_gauss_cli_missing_required(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    monkeypatch.setenv("PATH", str(tmp_path))
    ok, msg = check_gauss_cli(PROJ, require=True)
    assert ok is False
    assert "unavailable" in msg


def test_check_gauss_cli_exit_error(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    # Create a temporary gauss binary that exits with error
    temporary_gauss = tmp_path / "gauss"
    temporary_gauss.write_text("#!/bin/sh\necho 'version failed' >&2\nexit 1\n")
    temporary_gauss.chmod(0o755)

    monkeypatch.setenv("PATH", str(tmp_path))

    ok, msg = check_gauss_cli(PROJ, require=True)
    assert ok is False
    assert "version failed" in msg

    ok, msg = check_gauss_cli(PROJ, require=False)
    assert ok is True
    assert "version: exit 1" in msg


def test_check_gauss_cli_ok(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    temporary_gauss = tmp_path / "gauss"
    temporary_gauss.write_text("#!/bin/sh\necho 'Gauss v0.2.2 (2026-09-30)'\nexit 0\n")
    temporary_gauss.chmod(0o755)

    monkeypatch.setenv("PATH", str(tmp_path))

    root = tmp_path / "proj"
    root.mkdir()

    ok, msg = check_gauss_cli(root, require=True)
    assert ok is True
    assert "Gauss v0.2.2" in msg


@pytest.mark.parametrize("output", ["", "everything is fine", "Gauss vbroken"])
@pytest.mark.parametrize("require", [True, False])
def test_check_gauss_cli_rejects_nonversion(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, output: str, require: bool
):
    temporary_gauss = tmp_path / "gauss"
    temporary_gauss.write_text(f"#!/bin/sh\necho '{output}'\n")
    temporary_gauss.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path))
    ok, msg = check_gauss_cli(PROJ, require=require)
    assert ok is (not require)
    assert "unrecognized or empty" in msg


def test_check_gauss_cli_uses_isolated_version_only(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    import sys

    original_home = tmp_path / "account-home"
    original_home.mkdir()
    sentinel = original_home / "auth.json"
    sentinel.write_text("unchanged-account-record")
    temporary_gauss = tmp_path / "gauss"
    temporary_gauss.write_text(
        f"#!{sys.executable}\n"
        "import os,sys\nfrom pathlib import Path\n"
        "assert sys.argv[1:] == ['--version']\n"
        "assert os.environ['GAUSS_SKIP_UPDATE_CHECK'] == '1'\n"
        "assert os.environ['PYTHON_DOTENV_DISABLED'] == '1'\n"
        f"assert Path(os.environ['GAUSS_HOME']) != Path({str(original_home)!r})\n"
        "assert Path.cwd() == Path(os.environ['GAUSS_HOME'])\n"
        "assert not list(Path.cwd().iterdir())\n"
        "print('Gauss v0.2.2')\n"
    )
    temporary_gauss.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path))
    monkeypatch.setenv("GAUSS_HOME", str(original_home))
    monkeypatch.setenv("GAUSS_SKIP_UPDATE_CHECK", "0")
    monkeypatch.setenv("PYTHON_DOTENV_DISABLED", "0")
    assert check_gauss_cli(PROJ, require=True)[0]
    assert sentinel.read_text() == "unchanged-account-record"
    assert list(original_home.iterdir()) == [sentinel]
