"""Public semantic-audit contracts for the formalism catalogue."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from fep_lean.catalogue.generation import build_topics_data
from fep_lean.catalogue.schema import load_catalogue_metadata
from fep_lean.catalogue.semantics import load_theorem_maturity, theorem_names

PROJ = Path(__file__).resolve().parent.parent
SEALED_IDS = load_catalogue_metadata(
    PROJ / "config" / "catalogue_metadata.yaml"
).topic_ids

EXPECTED_BELOW_FORMALIZED = {
    "fep-052": "conditional_proxy",
    "fep-054": "conditional_proxy",
    "fep-055": "conditional_proxy",
    "fep-063": "conditional_proxy",
    "fep-064": "structural_proxy",
    "fep-067": "structural_proxy",
    "fep-069": "structural_proxy",
    "fep-070": "structural_proxy",
    "fep-071": "conditional_proxy",
    "fep-079": "conditional_proxy",
    "fep-081": "structural_proxy",
    "fep-083": "conditional_proxy",
    "fep-085": "conditional_proxy",
    "fep-094": "structural_proxy",
    "fep-095": "conditional_proxy",
    "fep-097": "conditional_proxy",
    "fep-100": "conditional_proxy",
    "fep-105": "conditional_proxy",
    "fep-106": "conditional_proxy",
}


def test_theorem_role_parser_ignores_comments_and_accepts_lemmas() -> None:
    body = (
        "/- theorem commented : True := by trivial -/\n"
        'def label := "theorem stringOnly : True"\n'
        "lemma liveLemma : True := by trivial\n"
        "theorem liveTheorem : True := by trivial\n"
    )

    assert theorem_names(body) == {"liveLemma", "liveTheorem"}


def test_semantic_audit_has_complete_ordered_roster_and_conserved_counts() -> None:
    audit = load_theorem_maturity(PROJ / "config" / "theorem_maturity.yaml")

    assert [record.id for record in audit.records] == list(SEALED_IDS)
    assert audit.disposition_counts == {
        "conditional_proxy": 13,
        "formalized": 140,
        "structural_proxy": 6,
    }
    assert {
        record.id: record.disposition.value
        for record in audit.records
        if record.disposition.value != "formalized"
    } == EXPECTED_BELOW_FORMALIZED
    assert sum(audit.disposition_counts.values()) == len(SEALED_IDS)


def test_static_metadata_roster_matches_semantic_roster() -> None:
    metadata = load_catalogue_metadata(PROJ / "config" / "catalogue_metadata.yaml")
    audit = load_theorem_maturity(PROJ / "config" / "theorem_maturity.yaml")

    assert [record.id for record in metadata] == [record.id for record in audit.records]
    assert {record.area for record in metadata} == {
        "FEP",
        "ActiveInference",
        "BayesianMechanics",
        "InfoGeometry",
        "Thermodynamics",
    }
    assert Counter(record.area for record in metadata) == {
        "FEP": 41,
        "ActiveInference": 35,
        "BayesianMechanics": 41,
        "InfoGeometry": 21,
        "Thermodynamics": 21,
    }


def test_generated_natural_language_is_semantic_not_generic() -> None:
    rows = build_topics_data(PROJ)["topics"]

    assert len(rows) == len(SEALED_IDS)
    assert all("Catalogue row" not in row["nl"] for row in rows)
    assert all("Natural-language anchor" not in row["nl"] for row in rows)
    assert all(row["semantic_disposition"] in row["nl"] for row in rows)
    assert rows[0]["nl"].startswith(
        "Surprisal plus Mathlib's native measure KL upper-bounds surprisal"
    )
