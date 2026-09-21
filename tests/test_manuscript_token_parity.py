"""Manuscript token-parity regression test.

Guards the contract that every ``{{token}}`` referenced by the shipped
manuscript chapters is produced by ``build_manuscript_vars``. Regression
coverage for the 2026-08-18 pass, where ``areas.<X>.count``,
``compile_rate.by_area.<X>``, ``combined_info_bayes_count(_caps)``,
``verify.sorry_count/run_id/mean_topic_s/duration_min`` and
``compile_rate.total`` were referenced in prose without a producer.
Regression coverage for the 2026-09-21 pass: the expansion-family counts
(``base_topic_count``, ``expansion_families``, ``expansion_family_topics``,
``expansion_family_size``, ``expansion_first_families``,
``expansion_second_families``, ``expansion_second_topics``,
``topics_before_second_expansion``) are derived from the canonical roster
instead of hand-typed prose.
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
        (PROJ / "manuscript" / "manuscript_vars.yaml").read_text(encoding="utf-8")
    )
    fresh_keys = set(_flatten(fresh))
    committed_keys = set(_flatten(committed))
    assert fresh_keys == committed_keys, (
        f"manuscript_vars.yaml out of sync: missing={fresh_keys - committed_keys}, "
        f"extra={committed_keys - fresh_keys} — run `uv run fep-lean catalogue`"
    )


def test_expansion_family_vars_derive_from_canonical_roster(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Expansion-family prose tokens must recompute from roster and ledger."""
    monkeypatch.setattr(manuscript_module, "_count_test_cases", lambda *a, **k: 0)
    catalogue = FEPTopicCatalogue.from_yaml(PROJ / "config" / "topics.yaml")
    variables = build_manuscript_vars(catalogue, PROJ)
    family_ids: dict[str, set[int]] = {}
    for topic in catalogue.topics:
        family_ids.setdefault(topic.family, set()).add(int(topic.id.split("-", 1)[1]))
    ledger = yaml.safe_load(
        (PROJ / "config" / "formalism_novelty.yaml").read_text(encoding="utf-8")
    )
    baseline = int(ledger["baseline_last_id"].split("-", 1)[1])
    boundary = int(manuscript_module._SECOND_EXPANSION_FIRST_ID.split("-", 1)[1])
    base = {f: ids for f, ids in family_ids.items() if max(ids) <= baseline}
    expansion = {f: ids for f, ids in family_ids.items() if min(ids) > baseline}
    sizes = {len(ids) for ids in expansion.values()}
    assert len(sizes) == 1, f"expansion families are not uniformly sized: {sizes}"
    first = [f for f, ids in expansion.items() if max(ids) < boundary]
    second = [f for f, ids in expansion.items() if min(ids) >= boundary]
    assert len(first) + len(second) == len(expansion), "boundary splits a family"
    assert variables["base_topic_count"] == sum(len(ids) for ids in base.values())
    assert variables["expansion_families"] == len(first) + len(second)
    assert variables["expansion_family_topics"] == sum(
        len(ids) for ids in expansion.values()
    )
    assert variables["expansion_family_size"] == next(iter(sizes))
    assert variables["expansion_first_families"] == len(first)
    assert variables["expansion_second_families"] == len(second)
    assert variables["expansion_second_topics"] == sum(
        len(ids) for f, ids in expansion.items() if min(ids) >= boundary
    )
    assert variables["topics_before_second_expansion"] == (
        variables["base_topic_count"] + len(first) * next(iter(sizes))
    )
    # Calibrated structural pins for the sealed 155-topic roster (04h/04i):
    # a 50-topic core, ten first-wave and five second-wave families of seven
    # topics each, and a second expansion running from 120 to 155.
    assert variables["base_topic_count"] == 50
    assert variables["expansion_families"] == 15
    assert variables["expansion_family_topics"] == 105
    assert variables["expansion_family_size"] == 7
    assert variables["expansion_first_families"] == 10
    assert variables["expansion_second_families"] == 5
    assert variables["expansion_second_topics"] == 35
    assert variables["topics_before_second_expansion"] == 120
