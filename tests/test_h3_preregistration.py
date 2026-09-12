"""H3.G0 preregistration matrix: acceptance-record schema and source pins.

Validates the H3.G0 acceptance record (`specs/h3-case-study/
pre-outcome-metadata.json`) against the protocol's required G0 field set
(`src/fep_lean/verification/horizon_acceptance.py:706-731`) and re-binds the
six source-hash pins captured in the frozen feasibility-spike receipt
(`specs/h3-case-study/spike-receipt.json`) to the live tree — the
protocol-matrix artifact the H3.G0 row requires.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType

PROJECT_ROOT = Path(__file__).resolve().parents[1]
H3_DIR = PROJECT_ROOT / "specs" / "h3-case-study"

# H3.G0 required field set and constraints, mirroring
# `validate_continuous_eligibility` (horizon_acceptance.py:706-731).
REQUIRED_G0_FIELDS = {
    "schema_version",
    "branch",
    "outcomes_accessed",
    "pre_outcome_basis",
    "finite_branch_considered",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_spike() -> ModuleType:
    path = H3_DIR / "h3_reference_study_spike.py"
    spec = importlib.util.spec_from_file_location("h3_reference_study_spike", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_g0_metadata_matches_required_schema() -> None:
    metadata = json.loads((H3_DIR / "pre-outcome-metadata.json").read_text())
    receipt = json.loads((H3_DIR / "spike-receipt.json").read_text())
    assert set(metadata) == REQUIRED_G0_FIELDS
    assert type(metadata["schema_version"]) is int
    assert metadata["schema_version"] == 1
    assert metadata["branch"] == "continuous"
    assert metadata["outcomes_accessed"] is False
    assert metadata["finite_branch_considered"] is False
    assert isinstance(metadata["pre_outcome_basis"], str)
    assert metadata["pre_outcome_basis"].strip()
    # The receipt and the acceptance record must name the same branch.
    assert receipt["branch"] == metadata["branch"]


def test_six_source_hash_pins_bind_the_live_tree() -> None:
    receipt = json.loads((H3_DIR / "spike-receipt.json").read_text())
    spike = _load_spike()
    assert len(spike.PINNED_SOURCES) == 6
    assert set(receipt["digests"]) == set(spike.PINNED_SOURCES)
    for relative, digest in spike.PINNED_SOURCES.items():
        assert _sha256(PROJECT_ROOT / relative) == digest, relative
        assert receipt["digests"][relative] == digest, relative
