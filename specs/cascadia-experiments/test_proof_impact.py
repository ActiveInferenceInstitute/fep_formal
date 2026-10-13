"""Exact-table change detection and fail-closed sidecar controls."""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from pathlib import Path
from types import ModuleType

import pytest


@pytest.fixture(scope="module")
def impact() -> ModuleType:
    path = Path(__file__).with_name("proof_impact.py")
    spec = importlib.util.spec_from_file_location("proof_impact", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_reference_is_identical_but_worksheet_is_not_proof(impact: ModuleType) -> None:
    result = impact.assess(impact.REFERENCE / "fixtures")
    assert result.changed_components == result.required_reviews == ()
    assert result.reference_bytes_match and result.native_claim_ready is False


def test_exact_habit_change_reopens_its_witnesses(
    tmp_path: Path, impact: ModuleType
) -> None:
    shutil.copytree(impact.REFERENCE / "fixtures", tmp_path / "variant")
    folder = tmp_path / "variant"
    artifact = folder / "smith_river_homing.geo-infer.json"
    domain = folder / "smith_river_homing.domain.json"
    data = json.loads(artifact.read_bytes())
    data["matrices"]["E"] = [0.25] * 4
    artifact.write_text(json.dumps(data), encoding="utf-8")
    sidecar = json.loads(domain.read_bytes())
    sidecar["exact"]["E"] = ["1/4"] * 4
    domain.write_text(json.dumps(sidecar), encoding="utf-8")
    result = impact.assess(folder)
    assert result.changed_components == ("E",)
    assert "policy-posterior bridge instance" in result.required_reviews
    assert not result.reference_bytes_match and not result.native_claim_ready
    sidecar["exact"]["E"][0] = "1/8"
    domain.write_text(json.dumps(sidecar), encoding="utf-8")
    with pytest.raises(ValueError, match="sidecar E differs"):
        impact.assess(folder)


def test_clock_change_does_not_inherit_physical_time_proof(
    tmp_path: Path, impact: ModuleType
) -> None:
    shutil.copytree(impact.REFERENCE / "fixtures", tmp_path / "variant")
    artifact = tmp_path / "variant/smith_river_homing.geo-infer.json"
    data = json.loads(artifact.read_bytes())
    data["time"]["step_seconds"] = 60
    artifact.write_text(json.dumps(data), encoding="utf-8")
    result = impact.assess(artifact.parent)
    assert result.changed_components == ("clock",)
    assert "step-count proof alone" in result.required_reviews[0]


def test_non_dyadic_and_stale_source_are_rejected(
    tmp_path: Path, impact: ModuleType
) -> None:
    shutil.copytree(impact.REFERENCE / "fixtures", tmp_path / "variant")
    artifact = tmp_path / "variant/smith_river_homing.geo-infer.json"
    original = json.loads(artifact.read_bytes())
    original["matrices"]["D"][0] = 0.1
    artifact.write_text(json.dumps(original), encoding="utf-8")
    with pytest.raises(ValueError, match="power of two|dyadic"):
        impact.assess(artifact.parent)
    source = artifact.with_name("smith_river_homing.gnn.md")
    source.write_text(
        source.read_text(encoding="utf-8") + "\nchanged\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="source digest"):
        impact.assess(artifact.parent)
