"""The conftest session keeps Hermes dotenv hydration off the real host.

Regression pin for the ambient-hang seam map (TestsScout item-14 evidence (d)):
``HermesConfig._load_gauss_dotenv`` reads ``$GAUSS_HOME/.env`` — defaulting to
the real ``~/.gauss/.env`` when ``GAUSS_HOME`` is unset — and writes
allowlisted keys into ``os.environ``. ``tests/conftest.py`` redirects
``GAUSS_HOME`` to an empty scratch dir for the whole session; these tests fail
if that redirect is removed.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

_REAL_GAUSS_HOME = (Path.home() / ".gauss").resolve()


def test_gauss_home_defaults_to_hermetic_scratch() -> None:
    """The session fixture points GAUSS_HOME at an empty scratch dir."""
    gauss_home = os.environ.get("GAUSS_HOME")
    assert gauss_home is not None, "conftest session fixture did not set GAUSS_HOME"
    resolved = Path(gauss_home).resolve()
    assert resolved != _REAL_GAUSS_HOME
    assert not (resolved / ".env").is_file(), (
        "the hermetic GAUSS_HOME scratch dir must hold no dotenv"
    )


def test_fixture_plugin_is_rewritten_before_ordinary_test_import(
    tmp_path: Path,
) -> None:
    tests = tmp_path / "tests"
    support = tests / "_support"
    support.mkdir(parents=True)
    (tests / "__init__.py").touch()
    (support / "__init__.py").touch()
    shutil.copy2(Path(__file__).with_name("conftest.py"), tests / "conftest.py")
    (tmp_path / "pytest.ini").write_text("[pytest]\n")
    (support / "catalogue_project.py").write_text(
        "def compare():\n    left, right = 1, 2\n    assert left == right\n"
    )
    (tests / "test_import_order.py").write_text(
        "import pytest\n"
        "from tests._support.catalogue_project import compare\n"
        "pytest_plugins = ['tests._support.catalogue_project']\n"
        "def test_rewritten_assertion():\n"
        "    with pytest.raises(AssertionError, match='assert 1 == 2'):\n"
        "        compare()\n"
    )
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-W",
            "error::pytest.PytestAssertRewriteWarning",
        ],
        cwd=tmp_path,
        env={**os.environ, "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"},
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "1 passed" in result.stdout
