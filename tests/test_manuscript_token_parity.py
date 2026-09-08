"""Manuscript token-parity regression test.

Guards the contract that every ``{{token}}`` referenced by the shipped
manuscript chapters is produced by ``build_manuscript_vars``. Regression
coverage for the 2026-08-18 pass, where ``areas.<X>.count``,
``compile_rate.by_area.<X>``, ``combined_info_bayes_count(_caps)``,
``verify.sorry_count/run_id/mean_topic_s/duration_min`` and
``compile_rate.total`` were referenced in prose without a producer.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

import fep_lean.output.manuscript as manuscript_module
from fep_lean.catalogue.topics import FEPTopicCatalogue
from fep_lean.output.manuscript import build_manuscript_vars

PROJ = Path(__file__).resolve().parent.parent
SKIP = {
    "09z_unified_formalism_catalogue.md",
    "manuscript_vars.yaml",
    "AGENTS.md",
    "README.md",
    "preamble.md",
    "09z_appendix_b_lean_catalogue.md",
    "09zc_appendix_c_lean_equations.md",
}
# Wildcard tokens handled specially by scripts/_inject_manuscript_vars.py.
WILDCARDS = {"maturity.*", "verify.*"}


def _flatten(data: object, prefix: str = "") -> dict[str, str]:
    flat: dict[str, str] = {}
    if isinstance(data, dict):
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else str(key)
            if isinstance(value, dict):
                flat.update(_flatten(value, full_key))
            elif isinstance(value, list):
                flat[full_key] = ", ".join(str(x) for x in value)
            elif isinstance(value, bool):
                flat[full_key] = str(value).lower()
            elif value is None:
                flat[full_key] = ""
            else:
                flat[full_key] = str(value)
    return flat


def test_every_manuscript_token_has_a_producer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(manuscript_module, "_count_test_cases", lambda *a, **k: 0)
    catalogue = FEPTopicCatalogue.from_yaml(PROJ / "config" / "topics.yaml")
    variables = build_manuscript_vars(catalogue, PROJ)
    flat = _flatten(variables)
    assert flat, "manuscript_vars must be non-empty"

    referenced: set[str] = set()
    for md_file in (PROJ / "manuscript").glob("*.md"):
        if md_file.name in SKIP:
            continue
        for match in re.finditer(
            r"\{\{([^}]+)\}\}", md_file.read_text(encoding="utf-8")
        ):
            token = match.group(1).strip()
            if token not in WILDCARDS and token != "…":
                referenced.add(token)

    missing = sorted(token for token in referenced if token not in flat)
    assert not missing, f"Manuscript tokens without a producer: {missing}"


def test_manuscript_vars_yaml_is_current(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The generated manuscript_vars.yaml must contain the same tokens a
    fresh ``build_manuscript_vars`` produces (no stale generator output)."""
    monkeypatch.setattr(manuscript_module, "_count_test_cases", lambda *a, **k: 0)
    catalogue = FEPTopicCatalogue.from_yaml(PROJ / "config" / "topics.yaml")
    fresh = build_manuscript_vars(catalogue, PROJ)
    committed = yaml.safe_load(
        (PROJ / "docs" / "manuscript" / "manuscript_vars.yaml").read_text(
            encoding="utf-8"
        )
    )
    fresh_keys = set(_flatten(fresh))
    committed_keys = set(_flatten(committed))
    assert fresh_keys == committed_keys, (
        f"manuscript_vars.yaml out of sync: missing={fresh_keys - committed_keys}, "
        f"extra={committed_keys - fresh_keys} — run `uv run fep-lean catalogue`"
    )
