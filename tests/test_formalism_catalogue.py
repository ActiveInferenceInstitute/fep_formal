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
from tests._support.fast_relaxation_review import (
    reverse_fast_relaxation_raw,
    reverse_fast_relaxation_rows,
)
from tests._support.lean_module_contract import (
    exact_information_review,
    restore_information_owner,
    reverse_information_entries,
)

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
# Exact old/new import prefixes for the 21 L01 topic bodies. Reversing only
# these reviewed prefixes leaves every declaration/proof byte subject to the
# original immutable historical digest gates below.
REVIEWED_IMPORT_HEADERS: dict[str, tuple[str, str]] = {
    "fep-004": (
        "import Mathlib.Algebra.Order.BigOperators.Group.Finset\nimport Mathlib.Tactic\n\n",
        "import Mathlib.Algebra.Order.BigOperators.Group.Finset\nimport Mathlib.Basic.Real.Basic\nimport Mathlib.Tactic.Ring\n\n",
    ),
    "fep-013": (
        "import Mathlib.Analysis.Calculus.Deriv.Add\nimport Mathlib.Analysis.Calculus.Deriv.Mul\nimport Mathlib.Tactic\n\n",
        "import Mathlib.Analysis.Calculus.Deriv.Add\nimport Mathlib.Analysis.Calculus.Deriv.Mul\nimport Mathlib.Tactic.Convert\nimport Mathlib.Tactic.Linarith\nimport Mathlib.Tactic.Ring\n\n",
    ),
    "fep-018": (
        "import Mathlib.Analysis.SpecialFunctions.Trigonometric.Inverse\nimport Mathlib.Analysis.Real.Sqrt\nimport Mathlib.Tactic\n\n",
        "import Mathlib.Analysis.SpecialFunctions.Trigonometric.Inverse\nimport Mathlib.Analysis.Real.Sqrt\nimport Mathlib.Tactic.Linarith\nimport Mathlib.Tactic.Ring\n\n",
    ),
    "fep-020": (
        "import Mathlib.Analysis.SpecificLimits.Normed\nimport Mathlib.Algebra.BigOperators.Group.Finset.Basic\nimport Mathlib.Data.Bool.Basic\nimport Mathlib.Tactic\n\n",
        "import Mathlib.Analysis.SpecificLimits.Normed\nimport Mathlib.Algebra.BigOperators.Group.Finset.Basic\nimport Mathlib.Data.Bool.Basic\nimport Mathlib.Tactic.Linarith\nimport Mathlib.Tactic.Ring\n\n",
    ),
    "fep-022": (
        "import Mathlib.Probability.Kernel.Composition.MeasureComp\nimport Mathlib.Tactic\n\n",
        "import Mathlib.Probability.Kernel.Composition.MeasureComp\nimport Mathlib.Tactic.Linarith\nimport Mathlib.Tactic.Ring\n\n",
    ),
    "fep-025": (
        "import Mathlib.Algebra.BigOperators.Group.Finset.Basic\nimport Mathlib.LinearAlgebra.Matrix.Notation\nimport Mathlib.Tactic\n\n",
        "import Mathlib.Algebra.BigOperators.Group.Finset.Basic\nimport Mathlib.LinearAlgebra.Matrix.Notation\nimport Mathlib.Basic.Real.Basic\nimport Mathlib.Tactic.FinCases\nimport Mathlib.Tactic.Linarith\nimport Mathlib.Tactic.NormNum\nimport Mathlib.Tactic.Ring\n\n",
    ),
    "fep-029": (
        "import Mathlib.Analysis.Convex.Basic\nimport Mathlib.Tactic\n\n",
        "import Mathlib.Analysis.Convex.Basic\nimport Mathlib.Basic.Real.Basic\nimport Mathlib.Tactic.Linarith\nimport Mathlib.Tactic.Ring\n\n",
    ),
    "fep-030": (
        "import Mathlib.Analysis.SpecialFunctions.BinaryEntropy\nimport Mathlib.Algebra.BigOperators.Ring.Finset\nimport Mathlib.Basic.Real.Basic\nimport Mathlib.Tactic\n\n",
        "import Mathlib.Analysis.SpecialFunctions.BinaryEntropy\nimport Mathlib.Algebra.BigOperators.Ring.Finset\nimport Mathlib.Basic.Real.Basic\nimport Mathlib.Tactic.FieldSimp\nimport Mathlib.Tactic.Ring\nmeta import Lean.Meta.Tactic.NormCast\n\n",
    ),
    "fep-032": (
        "import Mathlib.Analysis.SpecificLimits.Normed\nimport Mathlib.Tactic\n\n",
        "import Mathlib.Analysis.SpecificLimits.Normed\nimport Mathlib.Tactic.Linarith\nimport Mathlib.Tactic.Ring\n\n",
    ),
    "fep-036": (
        "import Mathlib.Analysis.SpecificLimits.Basic\nimport Mathlib.Data.Nat.Cast.Field\nimport Mathlib.Probability.Distributions.Binomial\nimport Mathlib.Tactic\n\n",
        "import Mathlib.Analysis.SpecificLimits.Basic\nimport Mathlib.Data.Nat.Cast.Field\nimport Mathlib.Probability.Distributions.Binomial\nimport Mathlib.Tactic.FieldSimp\nimport Mathlib.Tactic.GCongr\nimport Mathlib.Tactic.Positivity\nmeta import Lean.Meta.Tactic.NormCast\nmeta import Lean.Elab.Tactic.Omega\n\n",
    ),
    "fep-037": (
        "import Mathlib.Analysis.SpecificLimits.Normed\nimport Mathlib.Tactic\n\n",
        "import Mathlib.Analysis.SpecificLimits.Normed\nimport Mathlib.Tactic.Linarith\nimport Mathlib.Tactic.Positivity\nimport Mathlib.Tactic.Ring\n\n",
    ),
    "fep-038": (
        "import Mathlib.Analysis.Calculus.Deriv.Add\nimport Mathlib.Algebra.BigOperators.Group.Finset.Basic\nimport Mathlib.Data.Bool.Basic\nimport Mathlib.Analysis.Real.Sqrt\nimport Mathlib.Tactic\n\n",
        "import Mathlib.Analysis.Calculus.Deriv.Add\nimport Mathlib.Algebra.BigOperators.Group.Finset.Basic\nimport Mathlib.Data.Bool.Basic\nimport Mathlib.Analysis.Real.Sqrt\nimport Mathlib.Tactic.Convert\nimport Mathlib.Tactic.FieldSimp\nimport Mathlib.Tactic.Linarith\nimport Mathlib.Tactic.NormNum\nimport Mathlib.Tactic.Ring\n\n",
    ),
    "fep-040": (
        "import Mathlib.Analysis.SpecialFunctions.Log.Deriv\nimport Mathlib.Probability.Distributions.Gaussian.Real\nimport Mathlib.Tactic\n\n",
        "import Mathlib.Analysis.SpecialFunctions.Log.Deriv\nimport Mathlib.Probability.Distributions.Gaussian.Real\nimport Mathlib.Tactic.Convert\nimport Mathlib.Tactic.FieldSimp\nimport Mathlib.Tactic.GCongr\nimport Mathlib.Tactic.Positivity\n\n",
    ),
    "fep-042": (
        "import Mathlib.Data.List.Count\nimport Mathlib.Tactic\n\n",
        "import Mathlib.Data.List.Count\nimport Mathlib.Basic.Real.Basic\nimport Mathlib.Tactic.Ring\n\n",
    ),
    "fep-043": (
        "import Mathlib.Analysis.Calculus.Deriv.Mul\nimport Mathlib.Analysis.Calculus.Deriv.Pow\nimport Mathlib.Analysis.Calculus.LocalExtr.Basic\nimport Mathlib.Tactic\n\n",
        "import Mathlib.Analysis.Calculus.Deriv.Mul\nimport Mathlib.Analysis.Calculus.Deriv.Pow\nimport Mathlib.Analysis.Calculus.LocalExtr.Basic\nimport Mathlib.Tactic.Convert\nimport Mathlib.Tactic.Linarith\nimport Mathlib.Tactic.Positivity\nimport Mathlib.Tactic.Ring\n\n",
    ),
    "fep-044": (
        "import Mathlib.Analysis.Real.Sqrt\nimport Mathlib.Tactic\n\n",
        "import Mathlib.Analysis.Real.Sqrt\nimport Mathlib.Tactic.Linarith\nimport Mathlib.Tactic.Positivity\nimport Mathlib.Tactic.Ring\n\n",
    ),
    "fep-045": (
        "import Mathlib.Algebra.BigOperators.Group.Finset.Basic\nimport Mathlib.Tactic\n\n",
        "import Mathlib.Algebra.BigOperators.Group.Finset.Basic\nimport Mathlib.Basic.Real.Basic\nimport Mathlib.Data.Fintype.Basic\nimport Mathlib.Tactic.FieldSimp\nimport Mathlib.Tactic.Ring\n\n",
    ),
    "fep-046": (
        "import Mathlib.Algebra.BigOperators.Ring.List\nimport Mathlib.Tactic\n\n",
        "import Mathlib.Algebra.BigOperators.Ring.List\nimport Mathlib.Basic.Real.Basic\nimport Mathlib.Tactic.Linarith\nimport Mathlib.Tactic.Ring\n\n",
    ),
    "fep-048": (
        "import Mathlib.Order.Monotone.Basic\nimport Mathlib.Topology.MetricSpace.Contracting\nimport Mathlib.Tactic\n\n",
        "import Mathlib.Order.Monotone.Basic\nimport Mathlib.Topology.MetricSpace.Contracting\nimport Mathlib.Tactic.NormNum\n\n",
    ),
    "fep-049": (
        "import Mathlib.Algebra.Order.BigOperators.Group.Finset\nimport Mathlib.Analysis.SpecialFunctions.Log.Basic\nimport Mathlib.Tactic\n\n",
        "import Mathlib.Algebra.Order.BigOperators.Group.Finset\nimport Mathlib.Analysis.SpecialFunctions.Log.Basic\nimport Mathlib.Tactic.Linarith\nimport Mathlib.Tactic.Ring\n\n",
    ),
    "fep-050": (
        "import Mathlib.Analysis.SpecialFunctions.BinaryEntropy\nimport Mathlib.Tactic\n\n",
        "import Mathlib.Analysis.SpecialFunctions.BinaryEntropy\nimport Mathlib.Tactic.Linarith\nimport Mathlib.Tactic.NormNum\n\n",
    ),
}

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


_PROXY_REVIEW_PATH = PROJECT_ROOT / "tests/fixtures/theorem_proxy_review_20261019.json"
_PROXY_REVIEW_SHA256 = (
    "f9b3e16457fb75416e81ff46c905f9e0ca38f01ca0d64f5b89f83a26abb7345d"
)


def _proxy_review() -> dict[str, object]:
    raw = _PROXY_REVIEW_PATH.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == _PROXY_REVIEW_SHA256
    review = json.loads(raw)
    assert review["schema_version"] == 1
    assert len(review["changes"]) == 52
    assert len({(c["id"], c["field"]) for c in review["changes"]}) == 52
    assert len(review["top_level_changes"]) == 1
    assert {c["id"] for c in review["body_changes"]} == {"fep-009", "fep-029"}
    return review


def _reverse_proxy_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    restored = [dict(row) for row in rows]
    by_id = {row["id"]: row for row in restored}
    for change in _proxy_review()["changes"]:
        if change["id"] in by_id:
            row = by_id[change["id"]]
            assert row[change["field"]] == change["reviewed"]
            row[change["field"]] = change["released"]
    return restored


def _assert_proxy_metadata_preimage(metadata: dict[str, object]) -> None:
    review = _proxy_review()
    restored = dict(metadata)
    restored["topics"] = _reverse_proxy_rows(
        reverse_fast_relaxation_rows(metadata["topics"], PROJECT_ROOT)
    )
    for change in review["top_level_changes"]:
        assert restored[change["field"]] == change["reviewed"]
        restored[change["field"]] = change["released"]
    assert (
        hashlib.sha256(_canonical(restored).encode()).hexdigest()
        == review["released_metadata_canonical_sha256"]
    )


def test_complete_proxy_review_reverses_only_exact_approved_metadata() -> None:
    review = _proxy_review()
    assert (
        hashlib.sha256(
            reverse_fast_relaxation_raw(
                (PROJECT_ROOT / "config/theorem_maturity.yaml").read_bytes(),
                PROJECT_ROOT,
            )
        ).hexdigest()
        == review["reviewed_metadata_sha256"]
    )
    _assert_proxy_metadata_preimage(_yaml("theorem_maturity.yaml"))


@pytest.mark.parametrize("mutation", ["reviewed", "unreviewed", "date"])
def test_proxy_review_rejects_unapproved_metadata(mutation: str) -> None:
    metadata = _yaml("theorem_maturity.yaml")
    if mutation == "reviewed":
        metadata["topics"][156]["invariant"] = "changed claim"
    elif mutation == "unreviewed":
        metadata["topics"][1]["primary_theorem"] = "unapproved theorem"
    else:
        metadata["review_date"] = "1900-01-01"
    with pytest.raises(AssertionError):
        _assert_proxy_metadata_preimage(metadata)


def test_proxy_review_rejects_modified_fixture(tmp_path: Path, monkeypatch) -> None:
    original = _PROXY_REVIEW_PATH.read_bytes()
    tampered = tmp_path / "tampered.json"
    tampered.write_bytes(original + b" ")
    monkeypatch.setattr(
        __import__(__name__, fromlist=["unused"]), "_PROXY_REVIEW_PATH", tampered
    )
    with pytest.raises(AssertionError):
        _proxy_review()


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
    for change in _proxy_review()["body_changes"]:
        topic = change["id"]
        assert released_bodies[topic].count(change["reviewed"]) == 1
        released_bodies[topic] = released_bodies[topic].replace(
            change["reviewed"], change["released"]
        )
    for topic_id, (released_header, reviewed_header) in REVIEWED_IMPORT_HEADERS.items():
        current = released_bodies[topic_id]
        assert current.startswith(reviewed_header), topic_id
        released_bodies[topic_id] = released_header + current[len(reviewed_header) :]
    migration = json.loads(
        (
            PROJECT_ROOT / "tests/fixtures/lean435_catalogue_proof_migration.json"
        ).read_text()
    )
    assert set(migration["topics"]) == {"fep-013", "fep-038", "fep-040", "fep-043"}
    for topic_id, change in migration["topics"].items():
        current_body = released_bodies[topic_id]
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
        assert released_bodies[topic_id] == expected, topic_id
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

    released_maturity = _reverse_proxy_rows(maturity_rows[:120])
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


_RELATION_RATIONALE_REVIEW_PATH = (
    PROJECT_ROOT / "tests" / "fixtures" / "relation_rationale_review_20261019.json"
)
_RELATION_RATIONALE_REVIEW_SHA256 = (
    "97fe4ef6a2621d62adf1300c1ea12e006e5d5cad53d5d85090777ad1c472048f"
)


_SCALAR_REVIEW_PATH = (
    PROJECT_ROOT / "tests/fixtures/scalar_bridges_review_20261019.json"
)
_SCALAR_REVIEW_SHA256 = (
    "728214c856f86560a8ff1d3a91e8f1b141bc98dbd57c34cb0f00713b99e7355a"
)


def _scalar_review() -> dict[str, object]:
    raw = _SCALAR_REVIEW_PATH.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == _SCALAR_REVIEW_SHA256
    review = json.loads(raw)
    assert review["schema_version"] == 1 and review["new_theorems"] == 7
    return review


_CONJUGACY_RATIONALE_REVIEW_PATH = (
    PROJECT_ROOT / "tests/fixtures/conjugacy_rationale_review_20261020.json"
)
_CONJUGACY_RATIONALE_REVIEW_SHA256 = (
    "de38efa3965146e47bb6d89f1bd5b81d9e41f2284714adae9d113752de3e5dfa"
)


def _restore_reviewed_conjugacy_rationale(
    edges: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Undo only the exact independently reviewed prose before historical seals."""
    raw = _CONJUGACY_RATIONALE_REVIEW_PATH.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == _CONJUGACY_RATIONALE_REVIEW_SHA256
    review = json.loads(raw)
    assert review["schema_version"] == 1
    result = []
    seen = 0
    for edge in edges:
        if (edge["source"], edge["target"]) == ("fep-017", "fep-045"):
            assert edge == review["reviewed"]
            result.append(dict(review["released"]))
            seen += 1
        else:
            result.append(dict(edge))
    assert seen == 1
    return result


_NATIVE_CONDITIONAL_REVIEW_PATH = (
    PROJECT_ROOT / "tests/fixtures/native_conditional_independence_review_20261020.json"
)
_NATIVE_CONDITIONAL_REVIEW_SHA256 = (
    "746cbe88175a1ea64314786623e1346f9c499cc849f04ce393658302aed28d82"
)


def _restore_reviewed_native_conditional_capability(
    caps: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Undo only the exact reviewed finite/native wording and existing witness."""
    raw = _NATIVE_CONDITIONAL_REVIEW_PATH.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == _NATIVE_CONDITIONAL_REVIEW_SHA256
    review = json.loads(raw)
    assert review["schema_version"] == 1
    result = []
    seen = 0
    for cap in caps:
        if cap["id"] == review["reviewed"]["id"]:
            assert cap == review["reviewed"]
            result.append(dict(review["released"]))
            seen += 1
        else:
            result.append(dict(cap))
    assert seen == 1
    return result


@pytest.mark.parametrize(
    "mutation",
    ["description", "evidence", "status", "unrelated", "missing", "duplicate"],
)
def test_native_conditional_capability_review_rejects_unapproved_changes(
    mutation: str,
) -> None:
    model = _yaml("formalism_relations.yaml")
    caps = model["capabilities"]
    row = next(cap for cap in caps if cap["id"] == "cap-conditional-independence")
    if mutation == "description":
        row["description"] = "Unreviewed general transport claim."
    elif mutation == "evidence":
        row["evidence"] = ["FEP.NativeBlanket.unreviewed_witness"]
    elif mutation == "status":
        row["status"] = "open"
    elif mutation == "unrelated":
        other = next(cap for cap in caps if cap["id"] != row["id"])
        other["description"] = "Unreviewed unrelated capability."
    elif mutation == "missing":
        caps.remove(row)
    else:
        caps.append(dict(row))
    with pytest.raises(AssertionError):
        _assert_scalar_model_preimage(model)


def test_native_conditional_capability_review_authenticates_fixture_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    replacement = tmp_path / "changed-native-review.json"
    replacement.write_bytes(_NATIVE_CONDITIONAL_REVIEW_PATH.read_bytes() + b" ")
    monkeypatch.setitem(globals(), "_NATIVE_CONDITIONAL_REVIEW_PATH", replacement)
    with pytest.raises(AssertionError):
        _assert_scalar_model_preimage(_yaml("formalism_relations.yaml"))


def _reverse_scalar_edges(edges: list[dict[str, object]]) -> list[dict[str, object]]:
    edges = _restore_reviewed_conjugacy_rationale(edges)
    edges = reverse_information_entries(edges, PROJECT_ROOT)
    change = _scalar_review()["edge_change"]
    result = []
    seen = 0
    for edge in edges:
        if (edge["source"], edge["target"]) == ("fep-030", "fep-031"):
            assert edge == change["reviewed"]
            result.append(dict(change["released"]))
            seen += 1
        else:
            result.append(dict(edge))
    assert seen == 1
    return result


def _reverse_scalar_capabilities(
    caps: list[dict[str, object]],
) -> list[dict[str, object]]:
    caps = reverse_fast_relaxation_rows(caps, PROJECT_ROOT, capability=True)
    caps = _restore_reviewed_native_conditional_capability(caps)
    caps = reverse_information_entries(caps, PROJECT_ROOT, capabilities=True)
    change = _scalar_review()["capability_change"]
    result = []
    seen = 0
    for cap in caps:
        if cap["id"] == change["reviewed"]["id"]:
            assert cap == change["reviewed"]
            result.append(dict(change["released"]))
            seen += 1
        else:
            result.append(dict(cap))
    assert seen == 1
    return result


def _assert_scalar_model_preimage(model: dict[str, object]) -> None:
    restored = dict(model)
    restored["edges"] = _reverse_scalar_edges(model["edges"])
    restored["capabilities"] = _reverse_scalar_capabilities(model["capabilities"])
    assert (
        hashlib.sha256(_canonical(restored).encode()).hexdigest()
        == _scalar_review()["released_model_canonical_sha256"]
    )


def _assert_scalar_core_preimage(source: str) -> None:
    source = restore_information_owner(
        source, "src/fep_lean/formal/compositions/core.lean", PROJECT_ROOT
    )
    review = _scalar_review()
    for key in ["added_public_imports", "added_core_block"]:
        assert source.count(review[key]) == 1
        source = source.replace(review[key], "")
    assert hashlib.sha256(source.encode()).hexdigest() == review["released_core_sha256"]


def test_scalar_bridges_preserve_exact_existing_proofs_and_relation_model() -> None:
    _assert_scalar_model_preimage(_yaml("formalism_relations.yaml"))
    _assert_scalar_core_preimage(
        (PROJECT_ROOT / "src/fep_lean/formal/compositions/core.lean").read_text()
    )


@pytest.mark.parametrize(
    "mutation",
    ["kind", "witness", "capability", "other_edge", "old_proof", "new_proof"],
)
def test_scalar_bridge_review_rejects_unapproved_changes(mutation: str) -> None:
    if mutation in {"old_proof", "new_proof"}:
        source = (
            PROJECT_ROOT / "src/fep_lean/formal/compositions/core.lean"
        ).read_text()
        old = (
            "namespace FEPComposed"
            if mutation == "old_proof"
            else "theorem fep018_coordinate_derivative_is_fep038"
        )
        assert old in source
        with pytest.raises(AssertionError):
            _assert_scalar_core_preimage(source.replace(old, "unreviewed", 1))
        return
    model = _yaml("formalism_relations.yaml")
    edge = next(
        e
        for e in model["edges"]
        if (e["source"], e["target"]) == ("fep-030", "fep-031")
    )
    if mutation == "kind":
        edge["kind"] = "formal"
    elif mutation == "witness":
        edge["witness"] = "FEPComposed.unreviewed"
    elif mutation == "capability":
        next(
            c
            for c in model["capabilities"]
            if c["id"] == "cap-multidimensional-information-geometry"
        )["evidence"][0] = "unreviewed"
    else:
        model["edges"][0]["rationale"] = "unreviewed"
    with pytest.raises(AssertionError):
        _assert_scalar_model_preimage(model)


def test_scalar_bridge_review_rejects_modified_fixture(
    tmp_path: Path, monkeypatch
) -> None:
    tampered = tmp_path / "tampered.json"
    tampered.write_bytes(_SCALAR_REVIEW_PATH.read_bytes() + b" ")
    monkeypatch.setattr(
        __import__(__name__, fromlist=["unused"]), "_SCALAR_REVIEW_PATH", tampered
    )
    with pytest.raises(AssertionError):
        _scalar_review()


def _assert_released_relation_rows(edges: list[dict[str, object]]) -> None:
    """Reverse only the exact reviewed prose delta before the immutable seal."""
    edges = _reverse_scalar_edges(edges)
    raw = _RELATION_RATIONALE_REVIEW_PATH.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == _RELATION_RATIONALE_REVIEW_SHA256
    review = json.loads(raw)
    assert review["schema_version"] == 1
    deltas = review["deltas"]
    assert len(deltas) == 29
    keyed = {(r["source"], r["kind"], r["target"]): r for r in deltas}
    assert len(keyed) == len(deltas)
    seen = set()
    normalized = []
    for edge in edges:
        row = dict(edge)
        key = (row["source"], row["kind"], row["target"])
        if key in keyed:
            delta = keyed[key]
            assert row["witness"] == delta["witness"]
            assert row["rationale"] == delta["reviewed_rationale"]
            row["rationale"] = delta["released_rationale"]
            assert key not in seen
            seen.add(key)
        normalized.append(row)
    assert seen == set(keyed)
    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    released = [
        edge
        for edge in normalized
        if (edge["source"], edge["kind"], edge["target"]) not in NEW_EDGE_KEYS
    ][:98]
    assert (
        _length_prefixed_sha256([_canonical(row) for row in released])
        == baseline["edges_digest"]
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
                for row in _reverse_scalar_capabilities(relations["capabilities"])
                if row["id"] not in NEW_CAPABILITY_IDS
            ]
        )
        == baseline["capabilities_digest"]
    )
    _assert_released_relation_rows(relations["edges"])


@pytest.mark.parametrize(
    "mutation",
    [
        "released_primary_body",
        "narrowed_import_changed",
        "narrowed_import_added",
        "narrowed_proof_changed",
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
    if mutation == "narrowed_import_changed":
        bodies["fep-013"] = bodies["fep-013"].replace(
            "Mathlib.Tactic.Convert", "Mathlib.Tactic", 1
        )
    elif mutation == "narrowed_import_added":
        bodies["fep-013"] = "import Mathlib.Tactic\n" + bodies["fep-013"]
    elif mutation == "narrowed_proof_changed":
        bodies["fep-013"] = bodies["fep-013"].replace(
            "namespace FEP013", "namespace Unreviewed", 1
        )
    elif mutation == "released_primary_body":
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


@pytest.mark.parametrize(
    "mutation",
    ["reviewed_text", "reviewed_kind", "reviewed_witness", "unreviewed_text"],
)
def test_relation_rationale_review_rejects_unapproved_changes(mutation: str) -> None:
    edges = [dict(edge) for edge in _yaml("formalism_relations.yaml")["edges"]]
    review = json.loads(_RELATION_RATIONALE_REVIEW_PATH.read_text(encoding="utf-8"))
    keys = {(r["source"], r["kind"], r["target"]) for r in review["deltas"]}
    if mutation == "unreviewed_text":
        released = [
            edge
            for edge in edges
            if (edge["source"], edge["kind"], edge["target"]) not in NEW_EDGE_KEYS
        ][:98]
        row = next(
            edge
            for edge in released
            if (edge["source"], edge["kind"], edge["target"]) not in keys
        )
        row["rationale"] = "An unreviewed replacement."
    else:
        row = next(
            edge
            for edge in edges
            if (edge["source"], edge["kind"], edge["target"]) in keys
        )
        field, value = {
            "reviewed_text": ("rationale", "An unreviewed replacement."),
            "reviewed_kind": ("kind", "conceptual"),
            "reviewed_witness": ("witness", "FEPComposed.unreviewed_witness"),
        }[mutation]
        row[field] = value
    with pytest.raises(AssertionError):
        _assert_released_relation_rows(edges)


def test_relation_rationale_review_authenticates_fixture_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    replacement = tmp_path / "changed-review.json"
    replacement.write_bytes(_RELATION_RATIONALE_REVIEW_PATH.read_bytes() + b" ")
    monkeypatch.setitem(globals(), "_RELATION_RATIONALE_REVIEW_PATH", replacement)
    with pytest.raises(AssertionError):
        _assert_released_relation_rows(_yaml("formalism_relations.yaml")["edges"])


def test_exact_information_review_preserves_complete_prior_model_and_owner_bytes():
    review = exact_information_review(PROJECT_ROOT)
    model = _yaml("formalism_relations.yaml")
    model["edges"] = _restore_reviewed_conjugacy_rationale(model["edges"])
    model["capabilities"] = _restore_reviewed_native_conditional_capability(
        reverse_fast_relaxation_rows(
            model["capabilities"], PROJECT_ROOT, capability=True
        )
    )
    assert (
        hashlib.sha256(_canonical(model).encode()).hexdigest()
        == review["reviewed_model_canonical_sha256"]
    )
    restored = dict(model)
    restored["edges"] = reverse_information_entries(model["edges"], PROJECT_ROOT)
    restored["capabilities"] = reverse_information_entries(
        model["capabilities"], PROJECT_ROOT, capabilities=True
    )
    assert (
        hashlib.sha256(_canonical(restored).encode()).hexdigest()
        == review["released_model_canonical_sha256"]
    )
    for owner in review["owner_changes"]:
        restore_information_owner(
            (PROJECT_ROOT / owner).read_text(), owner, PROJECT_ROOT
        )


@pytest.mark.parametrize(
    "mutation",
    ["old_proof", "new_proof", "witness", "rationale", "capability", "other_edge"],
)
def test_exact_information_review_rejects_unapproved_changes(mutation):
    review = exact_information_review(PROJECT_ROOT)
    if mutation in {"old_proof", "new_proof"}:
        owner = "src/fep_lean/formal/compositions/core.lean"
        source = (PROJECT_ROOT / owner).read_text()
        name = (
            "namespace FEPComposed"
            if mutation == "old_proof"
            else "theorem fep013_finite_helmholtz_decomposition"
        )
        assert name in source
        with pytest.raises(AssertionError):
            restore_information_owner(
                source.replace(name, "unreviewed", 1), owner, PROJECT_ROOT
            )
        return
    model = _yaml("formalism_relations.yaml")
    model["edges"] = _restore_reviewed_conjugacy_rationale(model["edges"])
    model["capabilities"] = _restore_reviewed_native_conditional_capability(
        reverse_fast_relaxation_rows(
            model["capabilities"], PROJECT_ROOT, capability=True
        )
    )
    if mutation == "capability":
        identity = review["capability_changes"][0]["reviewed"]["id"]
        next(row for row in model["capabilities"] if row["id"] == identity)["evidence"][
            0
        ] = "unreviewed"
    elif mutation == "other_edge":
        model["edges"][0]["rationale"] = "unreviewed"
    else:
        identity = review["edge_changes"][0]["reviewed"]
        row = next(
            row
            for row in model["edges"]
            if (row["source"], row["target"])
            == (identity["source"], identity["target"])
        )
        row[mutation] = "unreviewed"
    with pytest.raises(AssertionError):
        restored = dict(model)
        restored["edges"] = reverse_information_entries(model["edges"], PROJECT_ROOT)
        restored["capabilities"] = reverse_information_entries(
            model["capabilities"], PROJECT_ROOT, capabilities=True
        )
        assert (
            hashlib.sha256(_canonical(restored).encode()).hexdigest()
            == review["released_model_canonical_sha256"]
        )


def test_exact_information_review_rejects_modified_fixture(tmp_path):
    target = tmp_path / "tests/fixtures/exact_information_review_20261020.json"
    target.parent.mkdir(parents=True)
    target.write_bytes(
        (
            PROJECT_ROOT / "tests/fixtures/exact_information_review_20261020.json"
        ).read_bytes()
        + b" "
    )
    with pytest.raises(AssertionError):
        exact_information_review(tmp_path)


@pytest.mark.parametrize(
    "mutation", ["rationale", "kind", "witness", "missing", "duplicate"]
)
def test_conjugacy_rationale_review_refuses_changes_beyond_exact_prose(mutation):
    edges = [dict(edge) for edge in _yaml("formalism_relations.yaml")["edges"]]
    row = next(
        edge
        for edge in edges
        if (edge["source"], edge["target"]) == ("fep-017", "fep-045")
    )
    if mutation == "missing":
        edges.remove(row)
    elif mutation == "duplicate":
        edges.append(dict(row))
    else:
        row[mutation] = {
            "rationale": "unreviewed",
            "kind": "formal",
            "witness": "FEPComposed.unreviewed",
        }[mutation]
    with pytest.raises(AssertionError):
        _restore_reviewed_conjugacy_rationale(edges)


def test_conjugacy_rationale_review_authenticates_exact_fixture(tmp_path, monkeypatch):
    changed = tmp_path / "changed-review.json"
    changed.write_bytes(_CONJUGACY_RATIONALE_REVIEW_PATH.read_bytes() + b" ")
    monkeypatch.setitem(globals(), "_CONJUGACY_RATIONALE_REVIEW_PATH", changed)
    with pytest.raises(AssertionError):
        _restore_reviewed_conjugacy_rationale(
            _yaml("formalism_relations.yaml")["edges"]
        )
