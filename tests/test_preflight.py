"""Tests for fep_lean.verification.preflight — real subprocesses, no direct execution."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from fep_lean.verification.environment import _version_line
from fep_lean.verification.preflight import run_preflight

PROJ = Path(__file__).resolve().parent.parent


def test_version_line_missing_binary() -> None:
    ok, line = _version_line("/nonexistent/fep_lean_preflight_binary")
    assert ok is False
    assert isinstance(line, str)
    assert len(line) > 0


def test_run_preflight_returns_zero_or_one() -> None:
    c = run_preflight()
    assert c in (0, 1)


def test_run_preflight_require_gauss_when_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Cover the gauss-missing path by hiding gauss from PATH."""
    monkeypatch.setenv("PATH", str(tmp_path))
    monkeypatch.setenv("FEP_LEAN_SKIP_FALLBACKS", "1")
    assert run_preflight() == 1


def test_version_line_with_real_binary() -> None:
    """Cover the canonical version probe with a real binary."""
    ok, line = _version_line(sys.executable)
    assert ok is True
    assert "Python" in line or "python" in line.lower()


def test_run_preflight_gauss_required_missing_with_env(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Cover the gauss-fail early return in run_preflight with isolated PATH."""
    monkeypatch.setenv("PATH", str(tmp_path))
    monkeypatch.setenv("FEP_LEAN_SKIP_FALLBACKS", "1")
    assert run_preflight() == 1


def test_preflight_main_cli_smoke() -> None:
    """Exercise ``main()`` (argparse + sys.exit) without directing."""
    code = (
        "import sys\n"
        "sys.path.insert(0, 'src')\n"
        "sys.argv = ['fep-lean preflight']\n"
        "from fep_lean.verification.preflight import main\n"
        "main()\n"
    )
    r = subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(PROJ),
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    assert r.returncode in (0, 1)


def test_preflight_main_rejects_removed_flag(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The removed no-op option must be rejected rather than silently accepted."""
    monkeypatch.setenv("PATH", str(tmp_path))
    monkeypatch.setenv("FEP_LEAN_SKIP_FALLBACKS", "1")
    monkeypatch.setattr(sys, "argv", ["fep-lean preflight", "--require-gauss"])
    from fep_lean.verification.preflight import main

    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 2


def test_run_preflight_happy_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A partial tree remains a strict full-mode failure."""
    from fep_lean.verification import preflight

    monkeypatch.setattr(preflight, "project_root", lambda: tmp_path / "proj")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    monkeypatch.setenv("PATH", str(bin_dir))
    status = preflight.run_preflight()
    assert status == 1


def test_preflight_full_checks_preserve_environment(monkeypatch, capsys, tmp_path):
    from fep_lean.verification import preflight

    monkeypatch.setenv("FEP_LEAN_REQUIRE_GAUSS", "preserved-sentinel")
    monkeypatch.setattr(preflight, "project_root", lambda: tmp_path)
    calls = []
    payload = {"status": "error", "mode": "full", "checks": [], "failed_count": 1}

    def inspect(root, *, mode):
        calls.append((root, mode))
        return payload

    monkeypatch.setattr(preflight, "run_validation_checks", inspect)
    before = dict(os.environ)
    assert preflight.run_preflight() == 1
    assert calls == [(tmp_path, "full")]
    record = json.loads(capsys.readouterr().out)
    assert record["status"] == "error"
    assert record["details"]["result"] == payload
    assert dict(os.environ) == before
