"""Pytest configuration for fep_formal tests.

Setup:
- Adds ``src/`` to ``sys.path`` so test imports resolve without installation.
- Sets ``MPLBACKEND=Agg`` for headless matplotlib.
- Probes for ``gauss``, ``lake``, ``lean`` on PATH (or ``~/.elan/bin``).
- Sets ``FEP_FORMAL_TOOLS_MISSING`` env var (comma-separated) when tools are absent.

Coverage notes:
    Remaining branches include live Lean and provider paths. Provider calls run
    only under explicit live-test selection with configured credentials.
"""

import os
import shutil
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

from fep_formal._paths import resolve_environment

# Several test modules import this fixture owner before registering its
# pytest plugin. Mark it for rewriting before that first ordinary import.
pytest.register_assert_rewrite("tests._support.catalogue_project")

os.environ.setdefault("MPLBACKEND", "Agg")

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


_LIVE_CHROME_NODE_IDS = frozenset(
    {
        (
            "tests/test_browser_capture.py::"
            "test_live_chrome_blocks_and_records_a_delayed_outbound_request"
        ),
        (
            "tests/test_browser_capture.py::"
            "test_live_chrome_replay_terminates_every_profile_writer"
        ),
    }
)


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Group shared Lean probes and the two live Chrome cases under loadgroup.

    The Lean probe files compile against the shared ``lean/.lake`` tree and
    must never run in parallel with each other; this makes the documented
    marker enforce that constraint instead of relying on serial-only runs.
    Chrome grouping is a contention hypothesis for CUR-01, not a diagnosed
    startup fix. Run before xdist derives its loadgroup node IDs.
    """
    # ``xdist_group`` is registered by pytest-xdist, which the hermetic
    # Python-acceptance environment deliberately does not autoload (its
    # plugin policy is pytest + pytest-timeout only). Pinning to a group is
    # only meaningful when xdist is actually driving the run, so skip it
    # there instead of failing collection with an unregistered marker.
    if config.pluginmanager.hasplugin("xdist"):
        for item in items:
            if item.get_closest_marker("serial_lean") is not None:
                item.add_marker(pytest.mark.xdist_group("lean"))
            if item.nodeid in _LIVE_CHROME_NODE_IDS:
                item.add_marker(pytest.mark.xdist_group("live_chrome"))


def pytest_configure(config: pytest.Config) -> None:
    """Warn (not hard-exit) when gauss / lake / lean are not on PATH.

    Missing-tool handling is deliberately two-stance, not uniform: boundary
    probes use ``pytest.skip`` (see ``tests/_support/lake.py::
    lake_executable(missing="skip", ...)``), while acceptance probes raise
    ``RuntimeError`` and fail closed. Both stances are intentional.
    Sets FEP_FORMAL_TOOLS_MISSING env var listing any absent tools.
    """
    missing = [name for name in ("gauss", "lake", "lean") if not shutil.which(name)]
    # Also probe ~/.elan/bin (elan-managed lean may not be on PATH in sandboxed shells)
    elan_bin = Path.home() / ".elan" / "bin"
    still_missing = [m for m in missing if not (elan_bin / m).is_file()]
    if still_missing:
        # Don't hard-exit — let tests that gracefully handle missing tools still run.
        os.environ["FEP_FORMAL_TOOLS_MISSING"] = ",".join(still_missing)
    else:
        os.environ.setdefault("FEP_FORMAL_REQUIRE_GAUSS", "1")


@pytest.fixture(autouse=True, scope="session")
def _hermetic_gauss_home(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Path]:
    """Point ``GAUSS_HOME`` at an empty scratch dir for the whole session.

    ``HermesConfig.from_settings`` step 0 (``_load_gauss_dotenv``) reads
    ``$GAUSS_HOME/.env`` — defaulting to the *real* host ``~/.gauss/.env`` when
    ``GAUSS_HOME`` is unset — and writes allowlisted keys into ``os.environ``
    (``hermes.py:240-241``). Left un-stubbed, tests inherit whatever the host
    keeps in ``~/.gauss``, making full-order runs order-dependent on ambient
    host state (TestsScout item-14 seam evidence (d)). The session-scoped
    redirect closes that seam at the conftest level.

    Deliberately host-only: tool-availability probes (``gauss``/``lake``/
    ``lean`` on PATH) are untouched, so their skip semantics still hold, and
    live-test runs (``FEP_FORMAL_LIVE_TESTS=1``) opt back into real host state.
    """
    live_var = resolve_environment("FEP_FORMAL_LIVE_TESTS", "").lower()
    if live_var in ("1", "true", "yes"):
        yield Path(os.environ.get("GAUSS_HOME", str(Path.home() / ".gauss")))
        return
    scratch = tmp_path_factory.mktemp("gauss-home")
    saved = os.environ.get("GAUSS_HOME")
    os.environ["GAUSS_HOME"] = str(scratch)
    try:
        yield scratch
    finally:
        if saved is None:
            os.environ.pop("GAUSS_HOME", None)
        else:
            os.environ["GAUSS_HOME"] = saved


# The H2.7-R0 custody record (and its validator and readiness test module) are
# hash-bound to the recorded 1.4.0 release token. These tests validate a copy of
# the custody inputs in which an approved later release version is mapped back
# to that token; every other byte must still match. See
# tests/_support/release_lineage.py.
_RECORDED_RELEASE_TESTS = {
    "test_horizon2_gaussian_vfe_readiness.py": frozenset(
        {
            "test_h2_7_r0_repair_is_source_bound_append_only_go",
            "test_h2_7_r0_custody_rejects_tampering",
            "test_h2_7_h3_custody_addendum_rejects_tampering",
        }
    ),
    "test_horizon2_smooth_reference_kernel.py": frozenset(
        {"test_h2_7_consumes_only_an_accepted_source_bound_r0_decision"}
    ),
}


@pytest.fixture(autouse=True)
def _recorded_release_lineage(
    request: pytest.FixtureRequest,
    tmp_path_factory: pytest.TempPathFactory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    names = _RECORDED_RELEASE_TESTS.get(request.node.path.name, frozenset())
    if getattr(request.node, "originalname", request.node.name) not in names:
        return
    from tests._support.release_lineage import custody_root

    root = custody_root(ROOT, tmp_path_factory.mktemp("recorded-release"))
    monkeypatch.setattr(request.module, "PROJECT_ROOT", root)
    # Module-level custody file constants follow the copied root.
    for name, value in vars(request.module).copy().items():
        if isinstance(value, Path) and value.is_relative_to(ROOT):
            copied = root / value.relative_to(ROOT)
            if copied.is_file():
                monkeypatch.setattr(request.module, name, copied)
