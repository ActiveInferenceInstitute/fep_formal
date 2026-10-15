"""H3.G0 preregistration matrix: acceptance-record schema and source pins.

Validates the H3.G0 acceptance record (`specs/h3-case-study/
pre-outcome-metadata.json`) against the protocol's required G0 field set
(`src/fep_lean/verification/horizon_acceptance.py:706-731`) and re-binds the
six source-hash pins captured in the frozen feasibility-spike receipt
(`specs/h3-case-study/spike-receipt.json`) to its preserved source epoch.
The historical spike must reject a replaced live terminal seal.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest

from tests._support.lean435_migration import historical_carrier_bytes

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


def test_feasibility_pins_preserve_historical_terminal_epoch() -> None:
    receipt = json.loads((H3_DIR / "spike-receipt.json").read_text())
    spike = _load_spike()
    assert len(spike.PINNED_SOURCES) == 6
    assert set(receipt["digests"]) == set(spike.PINNED_SOURCES)
    for relative, digest in spike.PINNED_SOURCES.items():
        assert receipt["digests"][relative] == digest, relative
        current = PROJECT_ROOT / relative
        if relative.endswith("/terminal-acceptance.json"):
            historical = (
                PROJECT_ROOT
                / "specs/comprehensive-science-improvement/evidence"
                / "h2-predecessor-terminal"
                / f"{digest}.json"
            )
            assert _sha256(historical) == digest
            assert _sha256(current) != digest
        elif relative.startswith("src/fep_lean/formal/"):
            historical_bytes = historical_carrier_bytes(relative, current.read_bytes())
            assert hashlib.sha256(historical_bytes).hexdigest() == digest, relative
            assert _sha256(current) != digest, relative
        else:
            assert _sha256(current) == digest, relative
    with pytest.raises(spike.SpikeRejection, match="stale source digest"):
        spike.digest_guard(PROJECT_ROOT)


def test_canonical_protocol_binds_real_pre_outcome_freeze_and_reviews() -> None:
    import yaml

    directory = PROJECT_ROOT / "specs/h3-reference-study"
    freeze = json.loads((directory / "freeze.json").read_bytes())
    canonical = PROJECT_ROOT / freeze["protocol"]["path"]
    assert _sha256(canonical) == freeze["protocol"]["sha256"]
    protocol = yaml.safe_load(canonical.read_bytes())
    assert protocol["execution_authorized"] is True
    assert protocol["branch"] == "continuous"
    assert protocol["finite_branch_selected"] is False
    assert freeze["new_outcomes_accessed"] is False
    assert freeze["new_model_implementation_started"] is False
    assert freeze["empirical_gate"] == "governed_no_go"
    identities = set()
    for ref in freeze["reviews"].values():
        path = PROJECT_ROOT / ref["path"]
        assert _sha256(path) == ref["sha256"]
        review = json.loads(path.read_bytes())
        assert review["decision"] == "approve"
        assert review["protocol_sha256"] == _sha256(canonical)
        identities.add(review["reviewer_id"])
    assert len(identities) == 2
    for path, digest in freeze["carrier_sources"].items():
        live = (PROJECT_ROOT / path).read_bytes()
        assert (
            hashlib.sha256(historical_carrier_bytes(path, live)).hexdigest() == digest
        )
        assert hashlib.sha256(live).hexdigest() != digest
