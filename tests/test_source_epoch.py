"""Static historical views authenticate current sources without renewing evidence."""

from __future__ import annotations

import copy
import json
import shutil
from pathlib import Path

import pytest

from fep_lean.methods.model import _theorem_sources
from tests._support import source_epoch

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def current(tmp_path):
    record = json.loads((ROOT / source_epoch.TRANSITION_PATH).read_text())
    paths = [
        source_epoch.TRANSITION_PATH,
        record["h3_partition"]["facade_path"],
        *record["pairs"],
        *(part["path"] for part in record["h3_partition"]["parts"]),
    ]
    for name in paths:
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    return tmp_path


def test_partition_and_exact_source_preimages_are_static_only(current):
    source_epoch.authenticate_h3_partition(current)
    record = source_epoch._transition(current)
    assert (
        record["native_execution"]
        is record["scientific_acceptance"]
        is record["historical_evidence_renewed"]
        is False
    )
    for name, pair in record["pairs"].items():
        before = source_epoch.predecessor_source(
            current, name, (current / name).read_bytes()
        )
        assert source_epoch._sha(before) == pair["before_sha256"]


@pytest.mark.parametrize(
    "leaf",
    [
        "h3_case_study",
        "h3_case_study_model_control",
        "h3_case_study_path_information",
        "h3_case_study_cost_feedback",
    ],
)
@pytest.mark.parametrize("change", ["body", "missing", "symlink"])
def test_changed_h3_source_cannot_be_hidden_by_historical_replay(current, leaf, change):
    path = current / "src/fep_lean/formal/compositions" / (leaf + ".lean")
    raw = path.read_bytes()
    if change == "body":
        path.write_bytes(raw + b"\n-- changed source\n")
    else:
        path.unlink()
        if change == "symlink":
            outside = current / "same-bytes.lean"
            outside.write_bytes(raw)
            path.symlink_to(outside)
    with pytest.raises((AssertionError, FileNotFoundError)):
        source_epoch.predecessor_source(
            current,
            source_epoch.MANIFEST,
            (current / source_epoch.MANIFEST).read_bytes(),
        )


def test_changed_transition_refuses_before_json_decode(current, monkeypatch):
    path = current / source_epoch.TRANSITION_PATH
    path.write_bytes(path.read_bytes() + b"\n")

    def forbidden(*args, **kwargs):
        raise RuntimeError("untrusted JSON was decoded")

    monkeypatch.setattr(source_epoch.json, "loads", forbidden)
    with pytest.raises(AssertionError, match="identity changed"):
        source_epoch.authenticate_h3_partition(current)


def _declarations(current):
    result = {}
    record = source_epoch._transition(current)
    for part in record["h3_partition"]["parts"]:
        result.update(
            _theorem_sources((current / part["path"]).read_text(), part["path"])
        )
    return result


def test_owner_view_preserves_current_objects_and_exact_statements(current):
    declarations = _declarations(current)
    before = copy.deepcopy(declarations)
    historical = source_epoch.historical_h3_owner_view(declarations, current)
    assert declarations == before
    assert len(historical) == 93
    for name in historical:
        assert historical[name]["statement"] == declarations[name]["statement"]
        assert (
            historical[name]["source_owner"]
            == "src/fep_lean/formal/compositions/h3_case_study.lean"
        )


@pytest.mark.parametrize("change", ["missing", "extra", "owner", "statement"])
def test_wrong_declaration_cannot_inherit_historical_owner(current, change):
    declarations = _declarations(current)
    name = next(iter(declarations))
    if change == "missing":
        del declarations[name]
    elif change == "extra":
        declarations["FEPComposed.H3CaseStudy.unreviewed"] = declarations[name]
    elif change == "owner":
        declarations[name]["source_owner"] = "unreviewed.lean"
    else:
        declarations[name]["statement"] += " "
    with pytest.raises(AssertionError):
        source_epoch.historical_h3_owner_view(declarations, current)
