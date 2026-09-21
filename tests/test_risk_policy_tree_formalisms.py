"""Static and native contracts for finite risk and closed-loop policy trees."""

from __future__ import annotations

import re
import runpy
import subprocess
from pathlib import Path
from typing import TypedDict, cast

import pytest

from tests._support.lake import lake_executable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEAN_ROOT = PROJECT_ROOT / "lean"
FORMAL_ROOT = PROJECT_ROOT / "src" / "fep_lean" / "formal"
BODIES_ROOT = PROJECT_ROOT / "src" / "fep_lean" / "catalogue" / "bodies"
COMPOSITIONS_ROOT = FORMAL_ROOT / "compositions"
SPIKE_ROOT = PROJECT_ROOT / "specs" / "done" / "formalism-catalogue-155" / "spikes"

pytestmark = pytest.mark.serial_lean


class TopicContract(TypedDict):
    title: str
    primary: str


class FamilyContract(TypedDict):
    foundation_import: str
    topics: dict[str, TopicContract]


FAMILIES: dict[str, FamilyContract] = {
    "finite_sample_risk_calibration": {
        "foundation_import": "FepSketches.empirical_risk",
        "topics": {
            "fep-121": {
                "title": "Laplace-Smoothing Error Identity",
                "primary": "fep121_laplaceError_identity",
            },
            "fep-122": {
                "title": "Laplace-Smoothing Bias Bound",
                "primary": "fep122_laplaceBias_abs_le",
            },
            "fep-123": {
                "title": "Absolute-Error Transfer",
                "primary": "fep123_laplaceAbsoluteError_le",
            },
            "fep-124": {
                "title": "Squared-Risk Transfer",
                "primary": "fep124_laplaceSquaredError_le",
            },
            "fep-125": {
                "title": "Bernoulli Brier Excess-Risk Identity",
                "primary": "fep125_brierExcess_eq_sqError",
            },
            "fep-126": {
                "title": "Laplace Brier-Risk Bound",
                "primary": "fep126_laplaceBrierRisk_le",
            },
            "fep-127": {
                "title": "Concentration-Event Transfer Through Smoothing",
                "primary": "fep127_laplaceBadEvent_subset",
            },
        },
    },
    "closed_loop_policy_trees": {
        "foundation_import": "FepSketches.policy_tree",
        "topics": {
            "fep-128": {
                "title": "Observation-Contingent Policy-Tree Recursion",
                "primary": "fep128_policyTreeValue_node",
            },
            "fep-129": {
                "title": "Finite Policy-Tree Bellman Minimum",
                "primary": "fep129_optimalTreeValue_eq_min",
            },
            "fep-130": {
                "title": "Optimal Finite Policy-Tree Existence",
                "primary": "fep130_exists_optimalPolicyTree",
            },
            "fep-131": {
                "title": "Open-Loop Plan Embedding",
                "primary": "fep131_openLoopEmbedding_value",
            },
            "fep-132": {
                "title": "Closed-Loop Dominance over Open Loop",
                "primary": "fep132_optimalTree_le_openLoop",
            },
            "fep-133": {
                "title": "Treewise EFE Decomposition",
                "primary": "fep133_policyTree_efe_eq_risk_add_ambiguity",
            },
            "fep-134": {
                "title": "Strict Boolean Feedback Advantage",
                "primary": "fep134_boolFeedback_strictlyBetter",
            },
        },
    },
}

COMPOSITION_BRIDGES: dict[str, dict[str, tuple[str, str]]] = {
    "risk_calibration.lean": {
        "fep121_laplaceError_extends_fep036": (
            "fep_fep121.FEP121.fep121_laplaceError_identity",
            "fep_fep036.FEP036.fep036_smoothedRate_eq_shrunkEmpirical",
        ),
        "fep122_laplaceBias_extends_fep036": (
            "fep_fep122.FEP122.fep122_laplaceBias_abs_le",
            "fep_fep036.FEP036.fep036_smoothedRate_mem_Ioo",
        ),
        "fep123_laplaceAbsoluteError_extends_fep036": (
            "fep_fep123.FEP123.fep123_laplaceAbsoluteError_le",
            "fep_fep036.FEP036.fep036_smoothedRate_eq_shrunkEmpirical",
        ),
        "fep124_laplaceSquaredRisk_combines_fep036_fep114": (
            "fep_fep124.FEP124.fep124_laplaceSquaredError_le",
            "fep_fep114.FEP114.fep114_subGaussian_empiricalMean_tail",
        ),
        "fep125_brierExcess_refines_fep022": (
            "fep_fep125.FEP125.fep125_brierExcess_eq_sqError",
            "fep_fep022.FEP022.fep022_brier_decomposition",
        ),
        "fep126_laplaceBrierRisk_combines_fep022_fep036": (
            "fep_fep126.FEP126.fep126_laplaceBrierRisk_le",
            "fep_fep022.FEP022.fep022_brier_decomposition",
        ),
        "fep127_laplaceConcentration_combines_fep036_fep114": (
            "fep_fep127.FEP127.fep127_laplaceBadEvent_subset",
            "fep_fep114.FEP114.fep114_subGaussian_empiricalMean_tail",
        ),
    },
    "policy_trees.lean": {
        "fep128_policyTreeRecursion_extends_fep071": (
            "fep_fep128.FEP128.fep128_policyTreeValue_node",
            "fep_fep071.FEP071.fep071_sophisticatedEFE_backward_step",
        ),
        "fep129_policyTreeBellman_extends_fep033": (
            "fep_fep129.FEP129.fep129_optimalTreeValue_eq_min",
            "fep_fep033.FEP033.fep033_bellman",
        ),
        "fep130_optimalPolicyTree_extends_fep008": (
            "fep_fep130.FEP130.fep130_exists_optimalPolicyTree",
            "fep_fep008.FEP008.fep008_exists_minG",
        ),
        "fep131_openLoopEmbedding_extends_fep033": (
            "fep_fep131.FEP131.fep131_openLoopEmbedding_value",
            "fep_fep033.FEP033.fep033_bellman",
        ),
        "fep132_closedLoopDominance_extends_fep071": (
            "fep_fep132.FEP132.fep132_optimalTree_le_openLoop",
            "fep_fep071.FEP071.fep071_twoStage_feedback_strictly_better",
        ),
        "fep133_treewiseEFE_extends_fep021": (
            "fep_fep133.FEP133.fep133_policyTree_efe_eq_risk_add_ambiguity",
            "fep_fep021.FEP021.fep021_efe_epistemic_balance",
        ),
        "fep134_feedbackWitness_extends_fep071": (
            "fep_fep134.FEP134.fep134_boolFeedback_strictlyBetter",
            "fep_fep071.FEP071.fep071_twoStage_feedback_strictly_better",
        ),
    },
}

AXIOM_PROBES: dict[str, tuple[str, ...]] = {
    "empirical_risk.lean": (
        "FEP.EmpiricalRisk.laplaceError_identity",
        "FEP.EmpiricalRisk.laplaceSquaredRisk_le",
        "FEP.EmpiricalRisk.brierExcess_eq_sqError",
        "FEP.EmpiricalRisk.laplaceBadEvent_probability_le",
        "FEP.EmpiricalRisk.laplaceBias_nonzero_witness",
    ),
    "policy_tree.lean": (
        "FEP.PolicyTrees.policyTreeValue_node",
        "FEP.PolicyTrees.exists_optimalPolicyTree",
        "FEP.PolicyTrees.openLoopEmbedding_value",
        "FEP.PolicyTrees.policyTree_efe_eq_risk_add_ambiguity",
        "FEP.PolicyTrees.boolFeedbackTree_strictlyBetter",
    ),
}

ALLOWED_AXIOMS = frozenset({"Classical.choice", "Quot.sound", "propext"})

FORBIDDEN_FORMAL_TOKENS = re.compile(
    r"\b(?:sorry|admit|axiom|opaque)\b|:\s*True\b|FepSketches\.fep_all"
)


def _load_body_module(module_name: str) -> dict[str, object]:
    return runpy.run_path(str(BODIES_ROOT / f"{module_name}.py"))


def _bodies(module_name: str) -> dict[str, str]:
    bodies = _load_body_module(module_name)["BODIES"]
    assert isinstance(bodies, dict)
    return cast(dict[str, str], bodies)


def _compile(source: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [lake_executable(), "env", "lean", str(source)],
        cwd=LEAN_ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=300,
    )


def _compile_topic(
    tmp_path: Path, *, module_name: str, topic_id: str
) -> subprocess.CompletedProcess[str]:
    import_line = f"import FepSketches.{FAMILIES[module_name]['foundation_import'].split('.')[-1]}\n"
    body = _bodies(module_name)[topic_id]
    assert body.startswith(import_line)
    closure = tmp_path / f"{topic_id}.lean"
    closure.write_text(
        (
            FORMAL_ROOT
            / f"{FAMILIES[module_name]['foundation_import'].split('.')[-1]}.lean"
        ).read_text(encoding="utf-8")
        + "\n"
        + body.removeprefix(import_line),
        encoding="utf-8",
    )
    return _compile(closure)


def _axiom_probe_closure(tmp_path: Path, resource: str) -> Path:
    foundation = (FORMAL_ROOT / resource).read_text(encoding="utf-8")
    spike = (SPIKE_ROOT / resource).read_text(encoding="utf-8")
    import_line = f"import FepSketches.{resource.removesuffix('.lean')}\n"
    assert spike.startswith(import_line)
    closure = tmp_path / f"axioms-{resource}"
    closure.write_text(
        foundation + "\n" + spike.removeprefix(import_line), encoding="utf-8"
    )
    return closure


def test_owned_foundation_and_body_files_exist() -> None:
    for module_name, contract in FAMILIES.items():
        foundation_name = contract["foundation_import"].split(".")[-1]
        assert (FORMAL_ROOT / f"{foundation_name}.lean").is_file()
        assert (BODIES_ROOT / f"{module_name}.py").is_file()


@pytest.mark.parametrize("module_name", tuple(FAMILIES))
def test_family_modules_export_only_exact_ordered_bodies(module_name: str) -> None:
    namespace = _load_body_module(module_name)
    assert "BODIES" in namespace
    assert "TOPIC_BODIES" not in namespace

    contract = FAMILIES[module_name]
    bodies = _bodies(module_name)
    assert tuple(bodies) == tuple(contract["topics"])

    for topic_id, topic in contract["topics"].items():
        digits = topic_id.removeprefix("fep-")
        body = bodies[topic_id]
        assert body.startswith(f"import {contract['foundation_import']}\n")
        assert f"/-! # {topic['title']} -/" in body
        assert f"namespace FEP{digits}\n" in body
        assert re.search(rf"(?m)^theorem {topic['primary']}\b", body)
        assert body.rstrip().endswith(f"end FEP{digits}")
        assert FORBIDDEN_FORMAL_TOKENS.search(body) is None


def test_foundations_pin_finite_carriers_and_reuse_existing_owners() -> None:
    risk = (FORMAL_ROOT / "empirical_risk.lean").read_text(encoding="utf-8")
    policy = (FORMAL_ROOT / "policy_tree.lean").read_text(encoding="utf-8")

    assert risk.startswith("import FepSketches.learning_theory\n")
    assert "FiniteLaw" in risk
    assert "VariationalDuality.expectation" in risk
    assert "def empiricalRate" in risk
    assert "def laplaceEstimate" in risk
    assert "def bernoulliBrierScore" in risk
    assert "def finiteEventProbability" in risk

    assert policy.startswith("import FepSketches.controlled_markov\n")
    assert "def PolicyTree" in policy
    assert "structure PolicyTreeModel" in policy
    assert "FiniteLaw" in policy
    assert "finiteArgmin" in policy
    assert "expectedFreeEnergy_eq_risk_add_ambiguity" in policy

    assert FORBIDDEN_FORMAL_TOKENS.search(risk) is None
    assert FORBIDDEN_FORMAL_TOKENS.search(policy) is None


def test_risk_foundation_pins_brier_identity_and_nonzero_bias() -> None:
    source = (FORMAL_ROOT / "empirical_risk.lean").read_text(encoding="utf-8")

    assert re.search(r"(?m)^theorem brierExcess_eq_sqError\b", source)
    assert re.search(r"(?m)^theorem laplaceSquaredRisk_le\b", source)
    assert re.search(r"(?m)^theorem laplaceBrierRisk_le\b", source)
    assert re.search(r"(?m)^theorem laplaceBias_nonzero_witness\b", source)
    assert "laplaceBias 2 0 = 1 / 4" in source
    assert "laplaceBias 2 0 ≠ 0" in source


def test_policy_foundation_pins_exact_boolean_feedback_boundaries() -> None:
    source = (FORMAL_ROOT / "policy_tree.lean").read_text(encoding="utf-8")

    assert re.search(r"(?m)^theorem boolFeedbackTree_value_zero\b", source)
    assert re.search(r"(?m)^theorem boolOpenLoop_value_half\b", source)
    assert "policyTreeValue boolFeedbackModel boolFeedbackTree false = 0" in source
    assert (
        "openLoopValue boolFeedbackModel (boolOpenLoopPlan action) false = 1 / 2"
        in source
    )
    assert re.search(r"(?m)^theorem boolFeedbackTree_strictlyBetter\b", source)


@pytest.mark.parametrize("resource", tuple(AXIOM_PROBES))
def test_promoted_spikes_print_exact_keystone_axioms(resource: str) -> None:
    source = (SPIKE_ROOT / resource).read_text(encoding="utf-8")
    assert source.startswith(f"import FepSketches.{resource.removesuffix('.lean')}\n")
    assert (
        tuple(re.findall(r"(?m)^#print axioms ([A-Za-z0-9_.']+)$", source))
        == (AXIOM_PROBES[resource])
    )
    assert FORBIDDEN_FORMAL_TOKENS.search(source) is None


@pytest.mark.parametrize("resource", tuple(COMPOSITION_BRIDGES))
def test_composition_leaves_pin_exact_bridge_names_and_imports(resource: str) -> None:
    source = (COMPOSITIONS_ROOT / resource).read_text(encoding="utf-8")
    foundation = resource.removesuffix("s.lean")
    if resource == "risk_calibration.lean":
        foundation = "empirical_risk"

    assert source.startswith(
        f"import FepSketches.fep_all\nimport FepSketches.{foundation}\n"
    )
    assert tuple(re.findall(r"(?m)^theorem ([A-Za-z0-9_']+)", source)) == tuple(
        COMPOSITION_BRIDGES[resource]
    )
    source_without_required_aggregate = source.replace(
        "import FepSketches.fep_all\n", "", 1
    )
    assert FORBIDDEN_FORMAL_TOKENS.search(source_without_required_aggregate) is None


@pytest.mark.parametrize(
    ("resource", "bridge", "new_topic_ref", "target_topic_ref"),
    tuple(
        (resource, bridge, references[0], references[1])
        for resource, bridges in COMPOSITION_BRIDGES.items()
        for bridge, references in bridges.items()
    ),
)
def test_composition_bridge_proofs_consume_new_and_target_topics(
    resource: str, bridge: str, new_topic_ref: str, target_topic_ref: str
) -> None:
    source = (COMPOSITIONS_ROOT / resource).read_text(encoding="utf-8")
    start = source.index(f"theorem {bridge}")
    next_theorem = source.find("\ntheorem ", start + len(bridge))
    end = (
        next_theorem if next_theorem >= 0 else source.index("\nend FEPComposed", start)
    )
    theorem_block = source[start:end]
    signature, proof = theorem_block.split(":= by", maxsplit=1)

    assert "∧" in signature
    assert new_topic_ref in proof
    assert target_topic_ref in proof


@pytest.mark.parametrize(
    ("module_name", "topic_id", "primary"),
    tuple(
        (module_name, topic_id, topic["primary"])
        for module_name, contract in FAMILIES.items()
        for topic_id, topic in contract["topics"].items()
    ),
)
def test_topic_inventory_names_each_primary_declaration(
    module_name: str, topic_id: str, primary: str
) -> None:
    assert primary in _bodies(module_name)[topic_id]


@pytest.mark.parametrize("foundation_name", ("empirical_risk", "policy_tree"))
def test_foundation_compiles_warning_free(foundation_name: str) -> None:
    result = _compile(FORMAL_ROOT / f"{foundation_name}.lean")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "warning:" not in (result.stdout + result.stderr).lower()


@pytest.mark.parametrize(
    ("module_name", "topic_id"),
    tuple(
        (module_name, topic_id)
        for module_name, contract in FAMILIES.items()
        for topic_id in contract["topics"]
    ),
)
def test_topic_body_closure_compiles_warning_free(
    tmp_path: Path, module_name: str, topic_id: str
) -> None:
    result = _compile_topic(tmp_path, module_name=module_name, topic_id=topic_id)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "warning:" not in (result.stdout + result.stderr).lower()


@pytest.mark.parametrize("resource", tuple(COMPOSITION_BRIDGES))
def test_composition_leaf_closure_compiles_warning_free(resource: str) -> None:
    result = _compile(COMPOSITIONS_ROOT / resource)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "warning:" not in (result.stdout + result.stderr).lower()


@pytest.mark.parametrize("resource", tuple(AXIOM_PROBES))
def test_keystone_axiom_probe_accepts_only_trusted_set(
    tmp_path: Path, resource: str
) -> None:
    result = _compile(_axiom_probe_closure(tmp_path, resource))
    output = result.stdout + result.stderr

    assert result.returncode == 0, output
    assert "warning:" not in output.lower()
    assert "sorryAx" not in output
    for declaration in AXIOM_PROBES[resource]:
        assert f"'{declaration}'" in output
    for axiom_blob in re.findall(r"depends on axioms: \[([^]]*)]", output):
        observed = {item.strip() for item in axiom_blob.split(",") if item.strip()}
        assert observed <= ALLOWED_AXIOMS
