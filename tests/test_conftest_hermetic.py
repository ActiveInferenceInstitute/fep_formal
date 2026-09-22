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