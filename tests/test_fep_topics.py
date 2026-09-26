"""Catalogue load and summary invariants."""

from __future__ import annotations

from pathlib import Path

import pytest

from fep_lean.catalogue.schema import load_catalogue_metadata
from fep_lean.catalogue.topics import CatalogueValidationError, FEPTopicCatalogue

PROJ = Path(__file__).resolve().parent.parent
TOPICS = PROJ / "config" / "topics.yaml"
SEALED_IDS = load_catalogue_metadata(
    PROJ / "config" / "catalogue_metadata.yaml"
).topic_ids

_EXPECTED_AREAS = {
    "FEP": 42,
    "ActiveInference": 33,
    "BayesianMechanics": 41,
    "InfoGeometry": 21,
    "Thermodynamics": 22,
}


def test_catalogue_loads_the_sealed_roster() -> None:
    c = FEPTopicCatalogue.from_yaml(TOPICS)
    assert len(c.topics) == len(SEALED_IDS)
    assert c.source_path == TOPICS
    ids = [t.id for t in c.topics]
    assert ids == list(SEALED_IDS)
    assert c.topics[0].primary_theorem == "fep001_variationalUpperBound_eq_iff"
    assert c.topics[0].semantic_disposition == "formalized"
    assert "Catalogue row" not in c.topics[0].nl


def test_summary_totals_match_manual_rollups() -> None:
    c = FEPTopicCatalogue.from_yaml(TOPICS)
    s = c.summary()
    assert s["total_topics"] == len(SEALED_IDS)
    assert sum(s["areas"].values()) == len(SEALED_IDS)
    assert s["areas"] == dict(sorted(_EXPECTED_AREAS.items(), key=lambda x: x[0]))
    mat = s["maturity"]
    assert mat["real"] + mat["partial"] + mat["aspirational"] == len(SEALED_IDS)
    assert mat["real"] == len(SEALED_IDS)
    assert mat["partial"] == 0
    assert mat["aspirational"] == 0
    for area, count in s["areas"].items():
        am = s["area_maturity"][area]
        assert am["real"] + am["partial"] + am["aspirational"] == count
        assert am["real"] == count
        assert am["partial"] == 0
        assert am["aspirational"] == 0


def test_topic_lean_chars_non_negative() -> None:
    c = FEPTopicCatalogue.from_yaml(TOPICS)
    for t in c.topics:
        assert t.lean_chars >= 0
        assert t.id.startswith("fep-")


def test_unknown_yaml_raises_or_empty() -> None:
    p = PROJ / "config" / "nonexistent_topics.yaml"
    with pytest.raises(CatalogueValidationError):
        FEPTopicCatalogue.from_yaml(p)


def test_from_yaml_default_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(PROJ)
    c = FEPTopicCatalogue.default()
    assert len(c.topics) == len(SEALED_IDS)
    assert c.source_path.name == "topics.yaml"


def test_all_topics_mathlib_real() -> None:
    c = FEPTopicCatalogue.from_yaml(TOPICS)
    assert all(t.mathlib_status == "real" for t in c.topics)
    assert {t.id for t in c.topics} == set(SEALED_IDS)
