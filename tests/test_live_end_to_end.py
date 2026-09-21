"""Opt-in credential-gated end-to-end test of the full fep_lean pipeline.

Set ``FEP_LEAN_LIVE_TESTS=1`` **and** provide ``OPENROUTER_API_KEY`` (or
``ANTHROPIC_API_KEY``) to run.  Requires the Lean workspace to be built
(``uv run fep-lean setup``) and a healthy ``gauss`` CLI on PATH.  Skipped
otherwise so offline developer machines and CI stay green.

This is the pipeline-level counterpart to
``test_gauss_runner.py::test_run_topic_with_real_hermes`` (component-level):
it exercises ``run_single_topic`` — catalogue load, environment validation,
Hermes HTTP, ``lake env lean`` verification, SQLite persistence, manuscript
artifacts, and the report — in one shot.

This remains opt-in because it crosses the external provider boundary; the
offline acceptance suite never treats a skipped live call as provider evidence.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from fep_lean.pipeline.core import PipelineResult
from fep_lean.pipeline.orchestrator import run_single_topic

PROJ = Path(__file__).resolve().parent.parent

_HAS_API_KEY = bool(
    os.environ.get("OPENROUTER_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
)
_LIVE_VAR = os.environ.get("FEP_LEAN_LIVE_TESTS", "").lower()
_LIVE_ENABLED = _LIVE_VAR in ("1", "true", "yes")


def _lean_workspace_ready() -> bool:
    mathlib_root = (
        PROJ
        / "lean"
        / ".lake"
        / "packages"
        / "mathlib"
        / ".lake"
        / "build"
        / "lib"
        / "lean"
        / "Mathlib.olean"
    )
    return mathlib_root.is_file()


@pytest.mark.skipif(
    not (_HAS_API_KEY and _LIVE_ENABLED),
    reason="Requires FEP_LEAN_LIVE_TESTS=1 and OPENROUTER_API_KEY/ANTHROPIC_API_KEY",
)
@pytest.mark.skipif(
    not _lean_workspace_ready(),
    reason="Lean workspace not built — run `uv run fep-lean setup` first",
)
def test_run_single_topic_full_mode_end_to_end(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Live full-mode run of fep-001 through the complete pipeline.

    Asserts structural properties of the result rather than ``complete``
    (rate limits and free-tier model availability make ``success``
    non-deterministic): the run must return a well-formed ``PipelineResult``
    with a populated topic result carrying Hermes and Lean outcome fields,
    and must not crash in any pipeline stage.
    """
    monkeypatch.setenv("FEP_LEAN_OUTPUT_ROOT", str(tmp_path / "output"))
    result = run_single_topic("fep-001", mode="full")

    assert isinstance(result, PipelineResult)
    assert result.mode == "full"
    assert result.catalogue_topics == 1
    # Stage trail: catalogue load + validation + gauss must all be recorded.
    stage_names = [s.name for s in result.stages]
    assert "Load Catalogue" in stage_names
    assert "Environment Validation" in stage_names
    assert "Gauss Sessions" in stage_names
    # A topic row must exist with the Hermes/Lean outcome fields populated.
    assert len(result.topic_results) == 1
    row = result.topic_results[0]
    assert row.topic_id == "fep-001"
    assert row.session_id  # SQLite session persisted
    assert row.hermes_model  # a real model responded (or chain label recorded)
    assert isinstance(row.lean_compiles, bool)
    assert isinstance(row.duration_s, float) and row.duration_s > 0
