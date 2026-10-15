"""Expansion-VII roster, ownership, and byte-preservation contracts."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from pathlib import Path

import pytest
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
REVIEWED_DELTAS_PATH = (
    PROJECT_ROOT / "tests" / "fixtures" / "formalism_catalogue_155_reviewed_deltas.json"
)
REVIEWED_MATURITY_FIELDS = {
    "fep-063": {
        "supporting_theorems",
        "boundary_theorems",
        "non_vacuity",
        "acceptance_probe",
    },
    "fep-064": {
        "supporting_theorems",
        "boundary_theorems",
        "invariant",
        "assumption_review",
        "non_vacuity",
        "acceptance_probe",
    },
}

NEW_FAMILY_RANGES = {
    "finite-sample-risk-and-calibration": range(121, 128),
    "closed-loop-policy-trees-and-efe": range(128, 135),
    "finite-to-native-blanket-transfer": range(135, 142),
    "finite-exponential-family-dual-geometry": range(142, 149),
    "two-state-continuous-time-thermodynamics": range(149, 156),
    # fep-166 lands in standalone-efe-formalizations, so the geometric-
    # mechanics family is no longer a contiguous roster interval.
    "geometric-mechanics-notation": (161, 162, 163, 164, 165, 167, 168),
}
NEW_FAMILY_AREAS = {
    "finite-sample-risk-and-calibration": "FEP",
    "closed-loop-policy-trees-and-efe": "ActiveInference",
    "finite-to-native-blanket-transfer": "BayesianMechanics",
    "finite-exponential-family-dual-geometry": "InfoGeometry",
    "two-state-continuous-time-thermodynamics": "Thermodynamics",
    "standalone-efe-formalizations": "ActiveInference",
    "geometric-mechanics-notation": "Thermodynamics",
}
NEW_CAPABILITY_IDS = {
    "cap-closed-loop-policy-trees",
    "cap-continuous-time-thermodynamics",
    "cap-finite-exponential-family-geometry",
    "cap-finite-sample-risk-calibration",
    "cap-native-blanket-transfer",
    "cap-standalone-efe-theorems",
    "cap-geometric-mechanics-solenoidal",
}
# Reviewed derivational edges added after the 1.5 release (LEAN-8, issue 106).
# Edges are kept sorted by source, so a new edge from a released core topic
# lands inside the released prefix; excluding exactly these keys keeps every
# released edge row byte-identical under the historical digest.
NEW_EDGE_KEYS = {
    ("fep-007", "formal", "fep-028"),
    ("fep-029", "formal", "fep-104"),
    ("fep-046", "formal", "fep-045"),
    ("fep-050", "formal", "fep-049"),
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


def _assert_released_body_and_maturity(
    bodies: Mapping[str, str], maturity_rows: list[dict[str, object]]
) -> None:
    """Reverse only reviewed deltas, retaining both historical digest gates."""
    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    deltas = json.loads(REVIEWED_DELTAS_PATH.read_text(encoding="utf-8"))
    assert deltas["schema_version"] == 1
    assert set(deltas["body_changes"]) == set(REVIEWED_MATURITY_FIELDS)
    assert set(deltas["maturity_changes"]) == set(REVIEWED_MATURITY_FIELDS)
    assert baseline["topic_count"] == 120

    released_bodies = dict(bodies)
    migration = json.loads(
        (
            PROJECT_ROOT / "tests/fixtures/lean435_catalogue_proof_migration.json"
        ).read_text()
    )
    assert set(migration["topics"]) == {"fep-013", "fep-038", "fep-040", "fep-043"}
    for topic_id, change in migration["topics"].items():
        current_body = bodies[topic_id]
        assert (
            hashlib.sha256(current_body.encode()).hexdigest()
            == change["migrated_sha256"]
        )
        restored, count = re.subn(
            r"(?m)^( +)first\n( +)\| rfl$",
            lambda match: (
                match[1]
                + "first\n"
                + match[2]
                + "| exact AddCommGroup.ext rfl\n"
                + match[2]
                + "| exact Module.ext rfl\n"
                + match[2]
                + "| rfl"
            ),
            current_body,
        )
        assert count == change["removed_pairs"]
        assert (
            hashlib.sha256(restored.encode()).hexdigest() == change["historical_sha256"]
        )
        released_bodies[topic_id] = restored
    for topic_id, change in deltas["body_changes"].items():
        released = change["released_body"]
        namespace_end = f"end FEP{topic_id[-3:]}\n"
        assert released.endswith(namespace_end)
        expected = (
            released[: -len(namespace_end)]
            + change["added_before_namespace_end"]
            + namespace_end
        )
        # Exact additive reconstruction protects the released primary statements
        # and the approved new theorems; an arbitrary replacement is rejected.
        assert bodies[topic_id] == expected, topic_id
        released_bodies[topic_id] = released
    assert (
        _length_prefixed_sha256(
            [
                f"{topic_id}\0{released_bodies[topic_id]}"
                for topic_id in tuple(bodies)[:120]
            ]
        )
        == baseline["body_digest"]
    )

    released_maturity = [dict(row) for row in maturity_rows[:120]]
    for topic_id, fields in deltas["maturity_changes"].items():
        assert set(fields) == REVIEWED_MATURITY_FIELDS[topic_id]
        row = released_maturity[int(topic_id[-3:]) - 1]
        assert row["id"] == topic_id
        for field, change in fields.items():
            assert row[field] == change["reviewed"], (topic_id, field)
            row[field] = change["released"]
    assert released_maturity[13]["id"] == "fep-014"
    assert released_maturity[13]["assumption_review"] == H1_0_FEP014_ASSUMPTION
    released_maturity[13]["assumption_review"] = RELEASED_FEP014_ASSUMPTION
    assert (
        _length_prefixed_sha256([_canonical(row) for row in released_maturity])
        == baseline["maturity_rows_digest"]
    )


def test_expansion_vii_has_exact_roster_family_and_area_ownership() -> None:
    metadata = load_catalogue_metadata(
        PROJECT_ROOT / "config" / "catalogue_metadata.yaml"
    )
    expected_ids = tuple(f"fep-{index:03d}" for index in range(1, 169))

    assert metadata.topic_ids == expected_ids
    assert tuple(BODIES) == expected_ids
    assert len(metadata.families) == 22
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
        "ActiveInference": 37,
        "BayesianMechanics": 41,
        "InfoGeometry": 21,
        "Thermodynamics": 28,
    }


def test_expansion_vii_registers_one_body_and_foundation_owner_per_family() -> None:
    body_families = tuple(entry.family for entry in BODY_MODULE_MANIFEST)
    assert len(body_families) == len(set(body_families)) == 22
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
    expected_ids = tuple(f"fep-{index:03d}" for index in range(1, 169))

    assert tuple(record.id for record in maturity.records) == expected_ids
    assert all(
        maturity.by_topic_id[f"fep-{index:03d}"].disposition.value == "formalized"
        for index in range(121, 169)
    )


def test_expansion_vii_preserves_released_rows_except_reviewed_deltas() -> None:
    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    metadata = _yaml("catalogue_metadata.yaml")
    maturity = _yaml("theorem_maturity.yaml")
    novelty = _yaml("formalism_novelty.yaml")
    relations = _yaml("formalism_relations.yaml")

    _assert_released_body_and_maturity(
        BODIES, [dict(row) for row in maturity["topics"][:120]]
    )
    assert (
        _length_prefixed_sha256([_canonical(row) for row in metadata["topics"][:120]])
        == baseline["metadata_rows_digest"]
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
        _length_prefixed_sha256(
            [
                _canonical(row)
                for row in [
                    edge
                    for edge in relations["edges"]
                    if (edge["source"], edge["kind"], edge["target"])
                    not in NEW_EDGE_KEYS
                ][:98]
            ]
        )
        == baseline["edges_digest"]
    )


@pytest.mark.parametrize(
    "mutation",
    [
        "released_primary_body",
        "reviewed_identity_body",
        "reviewed_attainment_body",
        "unreviewed_body",
        "released_primary_metadata",
        "reviewed_metadata",
        "unreviewed_metadata",
    ],
)
def test_reviewed_deltas_reject_unapproved_changes(mutation: str) -> None:
    bodies = dict(BODIES)
    maturity = [dict(row) for row in _yaml("theorem_maturity.yaml")["topics"][:120]]
    if mutation == "released_primary_body":
        bodies["fep-063"] = bodies["fep-063"].replace(
            "theorem fep063_finiteChannel_klDataProcessing",
            "theorem changed_primary",
            1,
        )
    elif mutation == "reviewed_identity_body":
        bodies["fep-063"] = bodies["fep-063"].replace(
            "theorem fep063_identityChannel_preservesKL", "theorem changed_identity", 1
        )
    elif mutation == "reviewed_attainment_body":
        bodies["fep-064"] = bodies["fep-064"].replace(
            "theorem fep064_rateDistortion_exists_minimizer",
            "theorem changed_attainment",
            1,
        )
    elif mutation == "unreviewed_body":
        bodies["fep-062"] += "\n-- unreviewed change\n"
    elif mutation == "released_primary_metadata":
        maturity[63]["primary_theorem"] = "changed_primary"
    elif mutation == "reviewed_metadata":
        maturity[62]["acceptance_probe"] = "changed acceptance"
    else:
        maturity[61]["invariant"] = "changed invariant"
    with pytest.raises(AssertionError):
        _assert_released_body_and_maturity(bodies, maturity)
