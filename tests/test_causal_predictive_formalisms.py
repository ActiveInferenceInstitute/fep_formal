"""Native boundaries for causal-dynamics and predictive-coding families."""

from __future__ import annotations

import re
import runpy
import subprocess
from pathlib import Path

import pytest

from fep_lean.catalogue.bodies.causal_blankets_interventions import (
    BODIES as CAUSAL_BODIES,
)
from fep_lean.catalogue.bodies.predictive_coding_generalized import (
    BODIES as PREDICTIVE_BODIES,
)
from tests._support.lake import lake_executable
from tests._support.lean_runner import run_lean_compile_probe

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEAN_ROOT = PROJECT_ROOT / "lean"
FORMAL_ROOT = PROJECT_ROOT / "src" / "fep_lean" / "formal"

CAUSAL_IDS = tuple(f"fep-{number:03d}" for number in range(79, 86))
PREDICTIVE_IDS = tuple(f"fep-{number:03d}" for number in range(86, 93))

pytestmark = pytest.mark.serial_lean


def _compile(source: Path) -> subprocess.CompletedProcess[str]:
    return run_lean_compile_probe(
        source,
        cwd=LEAN_ROOT,
        timeout_s=300,
        executable=lake_executable(),
    )


def _compile_topic_closure(
    tmp_path: Path, *, topic_id: str, foundation: str, body: str
) -> subprocess.CompletedProcess[str]:
    import_line = f"import FepSketches.{foundation}\n"
    assert body.startswith(import_line)
    source = tmp_path / f"{topic_id}.lean"
    source.write_text(
        (FORMAL_ROOT / f"{foundation}.lean").read_text(encoding="utf-8")
        + "\n"
        + body.removeprefix(import_line),
        encoding="utf-8",
    )
    return _compile(source)


def test_slice04_body_modules_own_one_exact_ordered_roster() -> None:
    assert tuple(CAUSAL_BODIES) == CAUSAL_IDS
    assert tuple(PREDICTIVE_BODIES) == PREDICTIVE_IDS
    assert not (set(CAUSAL_BODIES) & set(PREDICTIVE_BODIES))


@pytest.mark.parametrize(
    "module_name",
    ("causal_blankets_interventions", "predictive_coding_generalized"),
)
def test_slice04_body_module_has_no_competing_mapping_alias(module_name: str) -> None:
    namespace = runpy.run_path(
        PROJECT_ROOT / "src" / "fep_lean" / "catalogue" / "bodies" / f"{module_name}.py"
    )
    public_mappings = tuple(
        name
        for name, value in namespace.items()
        if not name.startswith("__") and isinstance(value, dict)
    )

    assert public_mappings == ("BODIES",)


@pytest.mark.parametrize(
    ("topic_id", "body"),
    (*CAUSAL_BODIES.items(), *PREDICTIVE_BODIES.items()),
)
def test_slice04_bodies_are_standalone_scoped_sources(topic_id: str, body: str) -> None:
    digits = topic_id.removeprefix("fep-")
    assert body.startswith("import FepSketches.")
    assert f"namespace FEP{digits}\n" in body
    assert body.rstrip().endswith(f"end FEP{digits}")
    assert re.search(rf"\btheorem fep{digits}_[A-Za-z0-9_]+", body)
    assert not re.search(r"(?m)^\s*(?:axiom|opaque)\b", body)
    assert not re.search(r"\b(?:sorry|admit)\b", body)
    assert not re.search(r":\s*True\b", body)


@pytest.mark.parametrize(
    ("resource", "declarations"),
    (
        (
            "causal_dynamics.lean",
            (
                "conditionalMutualInformation_eq_zero_iff_factorizes",
                "sharedConditional_mixture_preserves_joint",
                "coupledBlanket_conditionalMutualInformation_zero",
                "interventionKernel_sum_one",
                "orderedJoint_factorization",
                "nonDescendant_intervention_invariant",
                "boolIntervention_false_mediator_true_zero",
                "boolIntervention_true_mediator_true_one",
                "localMarkov_factorization_from_ordered",
                "localMarkov_mutualInformation_zero",
                "localMarkov_zeroEvidence_boundary",
                "boolMediatorEvidence_true",
            ),
        ),
        (
            "predictive_coding.lean",
            (
                "precisionEnergy_nonneg",
                "precisionEnergy_eq_zero_iff",
                "precisionEnergy_hasDerivAt",
                "hierarchicalEnergy_succ",
                "shift_add",
                "shift_top_zero",
                "generalizedFilteringStep_equation",
                "generalizedCoordinateEnergy_hasDerivAt",
                "generalizedFlow_top_boundary",
                "precisionEnergy_mono",
                "predictionEnergy_contraction",
                "predictionEnergy_strictDecrease",
                "iteratePredictionError_tendsto_zero",
                "iteratePredictionEnergy_tendsto_zero",
                "halfStep_energy_witness",
            ),
        ),
    ),
)
def test_slice04_foundations_expose_exact_witness_contracts(
    resource: str, declarations: tuple[str, ...]
) -> None:
    source = (FORMAL_ROOT / resource).read_text(encoding="utf-8")
    for declaration in declarations:
        assert re.search(rf"(?m)^theorem {declaration}\b", source), declaration
    assert not re.search(r"(?m)^\s*(?:axiom|opaque)\b", source)
    assert not re.search(r"\b(?:sorry|admit)\b", source)
    assert not re.search(r":\s*True\b", source)


def test_local_markov_topic_keeps_scope_and_boundary_visible() -> None:
    source = (FORMAL_ROOT / "causal_dynamics.lean").read_text(encoding="utf-8")
    body = CAUSAL_BODIES["fep-085"]

    assert "OrderedFourNodeModel" in source
    assert "hEvidence : 0 < mediatorEvidence model mediator" in body
    assert "fep085_zeroEvidence_boundary" in body
    assert "not general d-separation" in body


def test_four_node_intervention_witness_changes_only_named_descendant_claim() -> None:
    body = CAUSAL_BODIES["fep-083"]

    assert "boolIntervention_false_mediator_true_zero" in body
    assert "boolIntervention_true_mediator_true_one" in body
    assert "boolIntervention_preserves_named_nonDescendant" in body


def test_finite_jet_topic_exposes_derivative_shift_and_truncation() -> None:
    source = (FORMAL_ROOT / "predictive_coding.lean").read_text(encoding="utf-8")
    body = PREDICTIVE_BODIES["fep-090"]

    assert "structure FiniteJet" in source
    assert "truncated : ∀ degree, order < degree" in source
    assert "HasDerivAt" in body
    assert "shift 1 estimate" in body
    assert "fep090_finiteJet_truncation_visible" in body
    assert "fep090_firstOrder_correction_nonvacuity" in body


def test_quadratic_convergence_keeps_exact_stability_interval_visible() -> None:
    body = PREDICTIVE_BODIES["fep-092"]

    assert "hStepPositive : 0 < stepSize" in body
    assert "hStepBelowTwo : stepSize < 2" in body
    assert "Tendsto" in body
    assert "fep092_halfStep_decrease_nonvacuity" in body


@pytest.mark.parametrize("resource", ("causal_dynamics.lean", "predictive_coding.lean"))
def test_slice04_foundations_compile_warning_free(resource: str) -> None:
    result = _compile(FORMAL_ROOT / resource)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "warning:" not in (result.stdout + result.stderr).lower()


@pytest.mark.parametrize(
    ("topic_id", "body"),
    (*CAUSAL_BODIES.items(), *PREDICTIVE_BODIES.items()),
)
def test_slice04_topic_bodies_compile_warning_free(
    tmp_path: Path, topic_id: str, body: str
) -> None:
    foundation = "causal_dynamics" if topic_id in CAUSAL_BODIES else "predictive_coding"
    result = _compile_topic_closure(
        tmp_path, topic_id=topic_id, foundation=foundation, body=body
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "warning:" not in (result.stdout + result.stderr).lower()
