"""Regression checks for the maintained semantic theorem audit."""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

from fep_lean.catalogue.schema import load_catalogue_metadata

PROJ = Path(__file__).resolve().parent.parent
SCRIPTS = PROJ / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def test_theorem_maturity_audit_covers_native_source() -> None:
    from theorem_maturity_audit import validate_audit

    data = validate_audit(PROJ)
    topic_ids = load_catalogue_metadata(
        PROJ / "config" / "catalogue_metadata.yaml"
    ).topic_ids

    assert tuple(row["id"] for row in data["topics"]) == topic_ids
    assert all(
        "native Lean compile" in row["acceptance_probe"] for row in data["topics"]
    )
    assert Counter(row["disposition"] for row in data["topics"]) == {
        "conditional_proxy": 13,
        "formalized": 140,
        "structural_proxy": 6,
    }
    assert (
        next(row for row in data["topics"] if row["id"] == "fep-036")["disposition"]
        == "formalized"
    )
    assert not any(row["disposition"] == "assumption_gap" for row in data["topics"])


def test_generated_theorem_maturity_projection_is_current() -> None:
    from theorem_maturity_audit import OUTPUT_PATH, render_markdown, validate_audit

    data = validate_audit(PROJ)
    topic_ids = load_catalogue_metadata(
        PROJ / "config" / "catalogue_metadata.yaml"
    ).topic_ids

    assert OUTPUT_PATH.is_file()
    assert OUTPUT_PATH.read_text(encoding="utf-8") == render_markdown(data)
    text = OUTPUT_PATH.read_text(encoding="utf-8")
    assert "AUTO-GENERATED" in text
    assert text.count("| fep-") == len(topic_ids)
