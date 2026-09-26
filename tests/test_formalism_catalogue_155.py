"""Expansion-VII roster, ownership, and byte-preservation contracts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml

from fep_lean.catalogue import BODIES, BODY_MODULE_MANIFEST, load_catalogue_metadata
from fep_lean.catalogue.semantics import load_theorem_maturity
from fep_lean.formal.manifest import FORMAL_MODULES, FormalModuleRole

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = (
    PROJECT_ROOT
    / "specs"
    / "done"
    / "formalism-catalogue-155"
    / "assets"
    / "baseline-120-sha256.json"
)

NEW_FAMILY_RANGES = {
    "finite-sample-risk-and-calibration": range(121, 128),
    "closed-loop-policy-trees-and-efe": range(128, 135),
    "finite-to-native-blanket-transfer": range(135, 142),
    "finite-exponential-family-dual-geometry": range(142, 149),
    "two-state-continuous-time-thermodynamics": range(149, 156),
}
NEW_FAMILY_AREAS = {
    "finite-sample-risk-and-calibration": "FEP",
    "closed-loop-policy-trees-and-efe": "ActiveInference",
    "finite-to-native-blanket-transfer": "BayesianMechanics",
    "finite-exponential-family-dual-geometry": "InfoGeometry",
    "two-state-continuous-time-thermodynamics": "Thermodynamics",
    "standalone-efe-formalizations": "ActiveInference",
}
NEW_CAPABILITY_IDS = {
    "cap-closed-loop-policy-trees",
    "cap-continuous-time-thermodynamics",
    "cap-finite-exponential-family-geometry",
    "cap-finite-sample-risk-calibration",
    "cap-native-blanket-transfer",
}
H1_0_FEP014_ASSUMPTION = (
    "Self-divergence uses SigmaFinite; zero-characterization and the chain rule use "
    "finite measures; the chain rule additionally requires Markov kernels. The pin "
    "separately exposes native measure-KL data processing under a Markov kernel as "
    "InformationTheory.klDiv_comp_right_le; fep-014 does not include that theorem in "
    "its maintained theorem surface."
)
RELEASED_FEP014_ASSUMPTION = (
    "Self-divergence uses SigmaFinite; zero-characterization and the chain rule use "
    "finite measures; the chain rule additionally requires Markov kernels. No "
    "data-processing theorem is claimed because the pinned Mathlib revision does not "
    "expose one."
)


def _canonical(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def _length_prefixed_sha256(rows: list[str]) -> str:
    digest = hashlib.sha256()
    for row in rows:
        encoded = row.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return digest.hexdigest()


def _yaml(name: str) -> dict[str, object]:
    value = yaml.safe_load((PROJECT_ROOT / "config" / name).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_expansion_vii_has_exact_roster_family_and_area_ownership() -> None:
    metadata = load_catalogue_metadata(
        PROJECT_ROOT / "config" / "catalogue_metadata.yaml"
    )
    expected_ids = tuple(f"fep-{index:03d}" for index in range(1, 160))

    assert metadata.topic_ids == expected_ids
    assert tuple(BODIES) == expected_ids
    assert len(metadata.families) == 21
    assert set(NEW_FAMILY_RANGES) <= set(metadata.families)

    records = metadata.by_topic_id
    for family, indices in NEW_FAMILY_RANGES.items():
        ids = tuple(f"fep-{index:03d}" for index in indices)
        assert tuple(record.id for record in metadata if record.family == family) == ids
        assert {records[topic_id].area for topic_id in ids} == {
            NEW_FAMILY_AREAS[family]
        }

    area_counts: dict[str, int] = {}
    for record in metadata:
        area_counts[record.area] = area_counts.get(record.area, 0) + 1
    assert area_counts == {
        "FEP": 41,
        "ActiveInference": 35,
        "BayesianMechanics": 41,
        "InfoGeometry": 21,
        "Thermodynamics": 21,
    }


def test_expansion_vii_registers_one_body_and_foundation_owner_per_family() -> None:
    body_families = tuple(entry.family for entry in BODY_MODULE_MANIFEST)
    assert len(body_families) == len(set(body_families)) == 21
    assert set(NEW_FAMILY_RANGES) <= set(body_families)

    foundations = {
        module.resource
        for module in FORMAL_MODULES
        if module.role is FormalModuleRole.FOUNDATION
    }
    assert {
        "empirical_risk.lean",
        "policy_tree.lean",
        "native_blanket.lean",
        "exponential_family.lean",
        "continuous_time_markov.lean",
    } <= foundations

    compositions = {
        module.resource
        for module in FORMAL_MODULES
        if module.role is FormalModuleRole.COMPOSITION
    }
    assert {
        "compositions/risk_calibration.lean",
        "compositions/policy_trees.lean",
        "compositions/native_blanket_transfer.lean",
        "compositions/exponential_family.lean",
        "compositions/continuous_time.lean",
    } <= compositions


def test_expansion_vii_semantic_roster_is_complete_and_formalized() -> None:
    maturity = load_theorem_maturity(PROJECT_ROOT / "config" / "theorem_maturity.yaml")
    expected_ids = tuple(f"fep-{index:03d}" for index in range(1, 160))

    assert tuple(record.id for record in maturity.records) == expected_ids
    assert all(
        maturity.by_topic_id[f"fep-{index:03d}"].disposition.value == "formalized"
        for index in range(121, 156)
    )


def test_expansion_vii_preserves_released_rows_except_h1_0_pin_correction() -> None:
    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    metadata = _yaml("catalogue_metadata.yaml")
    maturity = _yaml("theorem_maturity.yaml")
    novelty = _yaml("formalism_novelty.yaml")
    relations = _yaml("formalism_relations.yaml")

    assert (
        _length_prefixed_sha256(
            [f"{topic_id}\0{BODIES[topic_id]}" for topic_id in tuple(BODIES)[:120]]
        )
        == baseline["body_digest"]
    )
    assert (
        _length_prefixed_sha256([_canonical(row) for row in metadata["topics"][:120]])
        == baseline["metadata_rows_digest"]
    )
    maturity_rows = [dict(row) for row in maturity["topics"][:120]]
    assert maturity_rows[13]["id"] == "fep-014"
    assert maturity_rows[13]["assumption_review"] == H1_0_FEP014_ASSUMPTION
    maturity_rows[13]["assumption_review"] = RELEASED_FEP014_ASSUMPTION
    assert (
        _length_prefixed_sha256([_canonical(row) for row in maturity_rows])
        == baseline["maturity_rows_digest"]
    )
    assert (
        _length_prefixed_sha256([_canonical(row) for row in novelty["topics"][:70]])
        == baseline["novelty_rows_digest"]
    )
    assert (
        _length_prefixed_sha256(
            [
                _canonical(row)
                for row in relations["capabilities"]
                if row["id"] not in NEW_CAPABILITY_IDS
            ]
        )
        == baseline["capabilities_digest"]
    )
    assert (
        _length_prefixed_sha256([_canonical(row) for row in relations["edges"][:98]])
        == baseline["edges_digest"]
    )
