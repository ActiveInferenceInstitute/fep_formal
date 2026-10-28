"""gauss_cli helpers — isolated real local version probe only."""

from __future__ import annotations

import pytest

import fep_formal.gauss.cli as gauss_cli
from fep_formal._paths import resolve_environment

pytestmark = pytest.mark.timeout(180)


@pytest.mark.skipif(
    "gauss" in resolve_environment("FEP_FORMAL_TOOLS_MISSING", ""),
    reason="gauss CLI missing",
)
def test_gauss_version_real_without_project_root() -> None:
    ok, msg = gauss_cli.check_gauss_cli(None, require=True)
    assert ok is True
    assert "gauss" in msg.lower()
