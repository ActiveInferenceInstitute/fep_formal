"""Static contracts for the collective-inference and learning-theory families."""

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

pytestmark = pytest.mark.serial_lean


class FamilyContract(TypedDict):
    foundation_import: str
    topics: dict[str, str]


FAMILIES: dict[str, FamilyContract] = {
    "collective_inference": {
        "foundation_import": "FepSketches.collective_inference",
        "topics": {
            "fep-107": "Product-Agent Generative Law",
            "fep-108": "Additive Collective Variational Free Energy",
            "fep-109": "Independent-Agent Expected-Free-Energy Additivity",
            "fep-110": "Unit-Weight Product-of-Experts Pool Normalization",
            "fep-111": "Consensus Mass Conservation",
            "fep-112": "Contractive Belief-Consensus Convergence",
            "fep-113": "Coupled-Agent Potential Descent",
        },
    },
    "learning_theory": {
        "foundation_import": "FepSketches.learning_theory",
        "topics": {
            "fep-114": "Sub-Gaussian Empirical-Mean Tail Bound",
            "fep-115": "Simultaneous Finite-Alphabet Frequency Bound",
            "fep-116": "Finite-Hypothesis PAC-Bayes Loss-Gap Bound",
            "fep-117": "Posterior-Odds Multiplicative Recursion",
            "fep-118": "Exponential Posterior Concentration from a Likelihood Gap",
            "fep-119": "Bayesian-Mixture Log-Loss Regret Bound",
            "fep-120": "Bayes-Factor Multiplicativity and Model-Evidence Update",
        },
    },
}

EXPECTED_FOUNDATION_THEOREMS = {
    "collective_inference": (
        "productKernel_sum_one",
        "productAgent_joint_mass",
        "productExpectedCost_additive",
        "collectiveVFE_additive",
        "independentEFE_additive",
        "unitWeightProductOfExpertsPool_sum_one",
        "consensusMass_conserved",
        "consensus_gap_contracts",
        "consensusIterate_gap",
        "consensus_gap_tendsto_zero",
        "boolConsensus_nonzero_strict_witness",
        "coupledPotential_contracts",
        "coupledPotential_strict_descent",
    ),
    "learning_theory": (
        "subGaussian_empiricalMean_tail",
        "simultaneous_frequency_bound",
        "finitePACBayes_changeOfMeasure_with_confidence",
        "posteriorOdds_recursion",
        "posterior_zero_of_prior_zero",
        "posteriorGap_concentration",
        "twoHypothesis_posterior_witness",
        "mixtureEvidence_lower_bound",
        "mixtureLogLoss_regret",
        "bayesFactor_multiplicative",
        "bayesFactor_twoHypothesis_witness",
        "bayesFactor_zero_denominator_boundary",
    ),
}

FORBIDDEN_FORMAL_TOKENS = re.compile(
    r"\b(?:sorry|admit|axiom|opaque)\b|FepSketches\.fep_all"
)


def _load_body_module(module_name: str) -> dict[str, object]:
    return runpy.run_path(str(BODIES_ROOT / f"{module_name}.py"))


def _bodies(module_name: str) -> dict[str, str]:
    namespace = _load_body_module(module_name)
    bodies = namespace["BODIES"]
    assert isinstance(bodies, dict)
    return cast(dict[str, str], bodies)


def _theorem_names(source: str) -> tuple[str, ...]:
    return tuple(re.findall(r"^theorem\s+([A-Za-z0-9_']+)", source, re.MULTILINE))


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
    import_line = f"import FepSketches.{module_name}\n"
    body = _bodies(module_name)[topic_id]
    assert body.startswith(import_line)
    combined = tmp_path / f"{topic_id}.lean"
    combined.write_text(
        (FORMAL_ROOT / f"{module_name}.lean").read_text(encoding="utf-8")
        + "\n"
        + body.removeprefix(import_line),
        encoding="utf-8",
    )
    return _compile(combined)


def test_family_modules_export_only_ordered_bodies_with_exact_titles() -> None:
    for module_name, contract in FAMILIES.items():
        namespace = _load_body_module(module_name)
        assert "BODIES" in namespace
        assert "TOPIC_BODIES" not in namespace

        bodies = _bodies(module_name)
        topics = contract["topics"]
        assert tuple(bodies) == tuple(topics)
        for topic_id, title in topics.items():
            number = topic_id.removeprefix("fep-")
            body = bodies[topic_id]
            assert isinstance(body, str)
            assert body.startswith(f"import {contract['foundation_import']}\n")
            assert f"/-! # {title} -/" in body
            assert f"namespace FEP{number}\n" in body
            assert f"theorem fep{number}_" in body
            assert f"end FEP{number}\n" in body
            assert FORBIDDEN_FORMAL_TOKENS.search(body) is None


def test_foundations_have_the_exact_required_theorem_inventory() -> None:
    for module_name, theorem_names in EXPECTED_FOUNDATION_THEOREMS.items():
        source = (FORMAL_ROOT / f"{module_name}.lean").read_text(encoding="utf-8")
        actual = _theorem_names(source)
        assert actual == theorem_names
        assert FORBIDDEN_FORMAL_TOKENS.search(source) is None


def test_collective_foundation_exposes_independence_and_coupling_boundaries() -> None:
    source = (FORMAL_ROOT / "collective_inference.lean").read_text(encoding="utf-8")

    assert source.startswith("import FepSketches.finite_information\n")
    assert "FiniteLaw.product" in source
    assert "FiniteInformation.finiteKL_product" in source
    assert "def productOfExpertsNormalizer" in source
    assert "def unitWeightProductOfExpertsPool" in source
    assert "logOpinionPool" not in source
    assert "equal-log-weight" not in source
    assert "def consensusStep" in source
    assert "def consensusIterate" in source
    assert "Tendsto" in source
    assert "Bool" in source
    assert "FiniteLaw.pointMass true" in source
    assert "FiniteLaw.pointMass false" in source
    assert "0 < beliefGap" in source
    assert "def coupledPotential" in source
    for overclaim in (
        "emergent agency",
        "collective intelligence",
        "group-level blanket",
        "social optimality",
    ):
        assert overclaim not in source.lower()


def test_learning_foundation_exposes_probability_support_and_sample_assumptions() -> (
    None
):
    source = (FORMAL_ROOT / "learning_theory.lean").read_text(encoding="utf-8")

    assert source.startswith("import FepSketches.variational_duality\n")
    assert "Mathlib.Probability.Moments.SubGaussian" in source
    assert "measure_sum_ge_le_of_iIndepFun" in source
    assert "measureReal_iUnion_fintype_le" in source
    assert "potentialIsLossGap" in source
    assert "logMGFBound" in source
    assert "empiricalLoss" in source
    assert "populationLoss" in source
    assert "inverseTemperaturePositive" in source
    assert "0 < confidence" in source
    assert "confidence < 1" in source
    assert "FiniteInformation.finiteKL" in source
    assert "VariationalDuality.expectation" in source
    assert "likelihoodGap" in source
    assert "sampleCount" in source
    assert "FiniteLaw Bool" in source


def test_hard_consensus_topic_has_strict_nonzero_bool_witness() -> None:
    foundation = (FORMAL_ROOT / "collective_inference.lean").read_text(encoding="utf-8")
    body = _bodies("collective_inference")["fep-112"]

    assert "theorem boolConsensus_nonzero_strict_witness" in foundation
    assert "0 < beliefGap" in foundation
    assert "beliefGap" in foundation and "< beliefGap" in foundation
    assert "theorem fep112_bool_nonzero_strict_witness" in body
    assert "theorem fep112_consensus_converges" in body


def test_hard_pac_bayes_topic_has_probability_prior_and_support_contract() -> None:
    foundation = (FORMAL_ROOT / "learning_theory.lean").read_text(encoding="utf-8")
    body = _bodies("learning_theory")["fep-116"]

    signature_start = foundation.index(
        "theorem finitePACBayes_changeOfMeasure_with_confidence"
    )
    signature_end = foundation.index(" := by", signature_start)
    signature = foundation[signature_start:signature_end]
    assert "FiniteLaw Hypothesis" in signature
    assert "GibbsCertificate Hypothesis" in signature
    assert "empiricalLoss" in signature
    assert "populationLoss" in signature
    assert "inverseTemperaturePositive" in signature
    assert "potentialIsLossGap" in signature
    assert "logMGFBound" in signature
    assert "confidencePositive" in signature
    assert "confidenceBelowOne" in signature
    assert "expectation posterior populationLoss" in signature
    assert "expectation posterior empiricalLoss" in signature
    assert "finiteKL posterior prior" in signature
    assert "μ.real" not in signature
    assert "bad :" not in signature
    assert "theorem fep116_finitePACBayes_with_confidence" in body
    assert "potentialIsLossGap" in body
    assert "logMGFBound" in body


def test_unit_weight_product_of_experts_names_replace_opinion_pool_names() -> None:
    foundation = (FORMAL_ROOT / "collective_inference.lean").read_text(encoding="utf-8")
    body = _bodies("collective_inference")["fep-110"]
    composition = (FORMAL_ROOT / "compositions" / "collective_learning.lean").read_text(
        encoding="utf-8"
    )

    for source in (foundation, body, composition):
        assert "unitWeightProductOfExpertsPool" in source
        assert "logOpinionPool" not in source
        assert "opinion pool" not in source.lower()
    assert "fep110_product_of_experts_refines_fep028_normalization" in composition
    assert "fep110_opinion_pool_refines_fep028_normalization" not in composition


def test_learning_family_pins_two_hypothesis_witnesses_and_zero_support() -> None:
    source = (FORMAL_ROOT / "learning_theory.lean").read_text(encoding="utf-8")
    bodies = _bodies("learning_theory")

    assert "twoHypothesis_posterior_witness" in source
    assert "bayesFactor_twoHypothesis_witness" in source
    assert "posterior_zero_of_prior_zero" in source
    assert "bayesFactor_zero_denominator_boundary" in source
    assert "fep117_zero_prior_boundary" in bodies["fep-117"]
    assert "fep118_twoHypothesis_witness" in bodies["fep-118"]
    assert "fep120_zero_evidence_boundary" in bodies["fep-120"]


@pytest.mark.parametrize("module_name", tuple(FAMILIES))
def test_family_foundation_compiles_warning_free(module_name: str) -> None:
    result = _compile(FORMAL_ROOT / f"{module_name}.lean")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "warning:" not in (result.stdout + result.stderr).lower()


@pytest.mark.parametrize(
    ("module_name", "topic_id"),
    [
        ("collective_inference", "fep-112"),
        ("learning_theory", "fep-116"),
    ],
)
def test_hard_topic_spike_compiles_warning_free(
    tmp_path: Path, module_name: str, topic_id: str
) -> None:
    result = _compile_topic(tmp_path, module_name=module_name, topic_id=topic_id)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "warning:" not in (result.stdout + result.stderr).lower()


NON_SPIKE_TOPICS = tuple(
    (module_name, topic_id)
    for module_name, contract in FAMILIES.items()
    for topic_id in contract["topics"]
    if topic_id not in {"fep-112", "fep-116"}
)


@pytest.mark.parametrize(("module_name", "topic_id"), NON_SPIKE_TOPICS)
def test_each_remaining_topic_compiles_warning_free(
    tmp_path: Path, module_name: str, topic_id: str
) -> None:
    result = _compile_topic(tmp_path, module_name=module_name, topic_id=topic_id)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "warning:" not in (result.stdout + result.stderr).lower()


@pytest.mark.parametrize("module_name", tuple(FAMILIES))
def test_family_body_closure_compiles_warning_free(
    tmp_path: Path, module_name: str
) -> None:
    import_line = f"import FepSketches.{module_name}\n"
    combined = tmp_path / f"{module_name}_family.lean"
    combined.write_text(
        (FORMAL_ROOT / f"{module_name}.lean").read_text(encoding="utf-8")
        + "\n"
        + "\n".join(
            body.removeprefix(import_line) for body in _bodies(module_name).values()
        ),
        encoding="utf-8",
    )

    result = _compile(combined)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "warning:" not in (result.stdout + result.stderr).lower()
