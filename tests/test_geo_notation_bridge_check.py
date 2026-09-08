"""The GEO-INFER notation bridge checker fails closed on every drift class."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SLICE = REPO_ROOT / "specs" / "geo-infer-notation-bridge"
if str(SLICE) not in sys.path:
    sys.path.insert(0, str(SLICE))

from check_geo_notation_bridge import validate_map

MATURITY = "config/theorem_maturity.yaml"
MAP = "specs/geo-infer-notation-bridge/data/notation-map.yaml"
VALID_ANCHOR = (
    "GEO-INFER-ACT/src/geo_infer_act/core/free_energy.py::FreeEnergyCalculator"
)


def entry(topic_id: str = "fep-002", symbol: str = "fep002_vfe_ge_surprisal") -> dict:
    return {
        "concept": "variational free energy",
        "fep_lean": {"topic_id": topic_id, "symbol": symbol},
        "geo_anchor": VALID_ANCHOR,
        "correspondence": "Correspondence of the bound construct; not a proof claim.",
        "reference": "Friston (2010), Nature Reviews Neuroscience 11(7)",
    }


def maturity_payload() -> dict:
    return {
        "schema_version": 2,
        "topics": [
            {
                "id": "fep-002",
                "primary_theorem": "fep002_vfe_ge_surprisal",
                "supporting_theorems": ["fep002_prob_measure_univ"],
                "boundary_theorems": [],
            },
            {
                "id": "fep-021",
                "primary_theorem": "fep021_efe_epistemic_balance",
                "supporting_theorems": [],
                "boundary_theorems": [],
            },
        ],
    }


def stage(root: Path, entries: list) -> Path:
    """Stage a minimal checkout with a map and maturity file under *root*."""
    (root / "specs" / "geo-infer-notation-bridge" / "data").mkdir(
        parents=True, exist_ok=True
    )
    (root / "config").mkdir(exist_ok=True)
    (root / MATURITY).write_text(yaml.safe_dump(maturity_payload()), encoding="utf-8")
    (root / MAP).write_text(
        yaml.safe_dump({"schema_version": 1, "entries": entries}, sort_keys=False),
        encoding="utf-8",
    )
    return root


def test_repository_map_validates_clean() -> None:
    assert validate_map(REPO_ROOT) == []


def test_unknown_topic_id_is_drift(tmp_path: Path) -> None:
    defects = validate_map(stage(tmp_path, [entry(topic_id="fep-999")]))
    assert any(
        "topic id not present in config/theorem_maturity.yaml" in defect
        for defect in defects
    )


def test_symbol_absent_from_maturity_surface_is_drift(tmp_path: Path) -> None:
    defects = validate_map(stage(tmp_path, [entry(symbol="fep999_madeUpTheorem")]))
    assert any(
        "does not appear in the maturity surface" in defect for defect in defects
    )


def test_supporting_theorem_symbols_are_accepted(tmp_path: Path) -> None:
    defects = validate_map(stage(tmp_path, [entry(symbol="fep002_prob_measure_univ")]))
    assert defects == []


@pytest.mark.parametrize(
    "anchor",
    [
        "GEO-INFER-ACT/src/geo_infer_act/core/free_energy.py",  # no ::Symbol
        "GEO-INFER-ACT/src/geo_infer_act/core/free_energy.py::free energy",  # space
        "GEO-INFER-ACT/src/geo_infer_act/core/free_energy.py::9Calc",  # bad symbol
        "GEO-INFER-act/src/geo_infer_act/core/free_energy.py::FreeEnergyCalculator",  # lowercase module
        "GEO-INFER-ACT/src/geo_infer_act/core/free_energy.txt::Calc",  # not .py
        "docs/gnn/gnn_syntax.md::GNNSection",  # wrong repo grammar
    ],
)
def test_anchor_grammar_violations_are_drift(tmp_path: Path, anchor: str) -> None:
    bad = entry()
    bad["geo_anchor"] = anchor
    defects = validate_map(stage(tmp_path, [bad]))
    assert any("does not match" in defect for defect in defects), anchor


def test_schema_version_drift_is_reported(tmp_path: Path) -> None:
    root = stage(tmp_path, [entry()])
    text = (root / MAP).read_text(encoding="utf-8")
    text = text.replace("schema_version: 1", "schema_version: 2")
    (root / MAP).write_text(text, encoding="utf-8")
    defects = validate_map(root)
    assert any("schema_version" in defect for defect in defects)


def test_missing_entry_key_is_drift(tmp_path: Path) -> None:
    bad = entry()
    del bad["reference"]
    defects = validate_map(stage(tmp_path, [bad]))
    assert any("keys" in defect for defect in defects)


def test_duplicate_topic_id_is_drift(tmp_path: Path) -> None:
    defects = validate_map(stage(tmp_path, [entry(), entry()]))
    assert any("duplicate topic id" in defect for defect in defects)


def test_unsorted_entries_are_drift(tmp_path: Path) -> None:
    defects = validate_map(
        stage(
            tmp_path,
            [
                entry(topic_id="fep-021", symbol="fep021_efe_epistemic_balance"),
                entry(),
            ],
        )
    )
    assert any("sorted by topic_id" in defect for defect in defects)


def test_unreadable_map_fails_closed(tmp_path: Path) -> None:
    root = stage(tmp_path, [entry()])
    (root / MAP).write_text("{a: [b: c}", encoding="utf-8")
    defects = validate_map(root)
    assert any("unreadable notation map" in defect for defect in defects)


def test_unreadable_maturity_fails_closed(tmp_path: Path) -> None:
    root = stage(tmp_path, [entry()])
    (root / MATURITY).write_text("{a: [b: c}", encoding="utf-8")
    defects = validate_map(root)
    assert any("theorem_maturity.yaml: unreadable" in defect for defect in defects)


def test_checker_output_is_deterministic(tmp_path: Path) -> None:
    stage(tmp_path, [entry()])
    assert validate_map(tmp_path) == validate_map(tmp_path) == []
