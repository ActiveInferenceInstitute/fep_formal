"""Source and opt-in native boundaries for Slice 05 formalisms."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import pytest

from fep_lean.catalogue.bodies.geometric_optimization import (
    BODIES as GEOMETRY_BODIES,
)
from fep_lean.catalogue.bodies.path_thermodynamics import BODIES as THERMO_BODIES
from tests._support.lake import lake_executable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEAN_ROOT = PROJECT_ROOT / "lean"
FORMAL_ROOT = PROJECT_ROOT / "src" / "fep_lean" / "formal"

THERMO_IDS = tuple(f"fep-{number:03d}" for number in range(93, 100))
GEOMETRY_IDS = tuple(f"fep-{number:03d}" for number in range(100, 107))
RUN_NATIVE = os.environ.get("FEP_LEAN_SLICE05_COMPILE_TEST") == "1"

THERMO_TITLES = (
    "Forward and Reverse Finite Path-Law Ratio",
    "Entropy Production as Path KL",
    "Detailed Fluctuation Symmetry",
    "Integral Fluctuation Theorem",
    "Finite Jarzynski Equality",
    "Local Detailed Balance and Current Cancellation",
    "Reversible-Chain One-Step KL Dissipation",
)
GEOMETRY_TITLES = (
    "Categorical Fisher Positivity on Simplex Tangents",
    "Fisher Pullback under Reparameterization",
    "Unbiased Scalar Cramér–Rao Bound under Score Regularity",
    "Natural-Gradient Equivariance under an Invertible Full-Rank Chart",
    "Mirror-Descent Three-Point Identity",
    "Bregman Pythagorean Law for an Affine Information Projection",
    "Replicator–Natural-Gradient Equivalence",
)

pytestmark = pytest.mark.serial_lean


def _compile(source: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [lake_executable(), "env", "lean", str(source)],
        cwd=LEAN_ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=300,
    )


def _topic_closure(tmp_path: Path, topic_id: str, body: str) -> Path:
    """Materialize one topic with its source foundation, without projections."""
    if topic_id in THERMO_IDS:
        resource = "path_thermodynamics.lean"
    else:
        resource = "geometric_optimization.lean"
    import_line = f"import FepSketches.{resource.removesuffix('.lean')}\n"
    assert body.startswith(import_line)
    source = tmp_path / f"{topic_id}.lean"
    source.write_text(
        (FORMAL_ROOT / resource).read_text(encoding="utf-8")
        + "\n"
        + body.removeprefix(import_line),
        encoding="utf-8",
    )
    return source


def test_slice05_body_modules_own_exact_ordered_rosters() -> None:
    assert tuple(THERMO_BODIES) == THERMO_IDS
    assert tuple(GEOMETRY_BODIES) == GEOMETRY_IDS
    assert not (set(THERMO_BODIES) & set(GEOMETRY_BODIES))
    assert len(THERMO_TITLES) == len(THERMO_IDS)
    assert len(GEOMETRY_TITLES) == len(GEOMETRY_IDS)


@pytest.mark.parametrize(
    ("topic_id", "body"), (*THERMO_BODIES.items(), *GEOMETRY_BODIES.items())
)
def test_slice05_bodies_are_standalone_scoped_sources(topic_id: str, body: str) -> None:
    digits = topic_id.removeprefix("fep-")
    assert body.startswith("import FepSketches.")
    assert f"namespace FEP{digits}\n" in body
    assert body.rstrip().endswith(f"end FEP{digits}")
    assert re.search(rf"\btheorem fep{digits}_[A-Za-z0-9_]+", body)
    assert not re.search(r"(?m)^\s*(?:axiom|opaque)\b", body)
    assert not re.search(r"\b(?:sorry|admit)\b", body)


@pytest.mark.parametrize(
    ("resource", "declarations"),
    (
        (
            "path_thermodynamics.lean",
            (
                "pathLaw_normalization",
                "reverse_reverse",
                "entropyProduction_eq_expected_logRatio",
                "detailedFluctuation_identity",
                "integralFluctuation_eq_one",
                "finiteJarzynski_eq",
                "localDetailedBalance_current_zero",
                "isInvariant_of_isReversible",
                "reversibleKL_oneStep_dissipation",
                "identityKernel_KL_equality",
                "irreversibleBool_entropyProduction_pos",
            ),
        ),
        (
            "geometric_optimization.lean",
            (
                "categoricalFisher_pos",
                "fairBernoulli_fullRank_example",
                "twoCategorical_simplexMetric_fullRank",
                "twoCategorical_nonzeroTangent_metric",
                "twoCategoricalTangent_spans",
                "duplicatedScore_nullDirection_example",
                "fisherPullback_comp",
                "naturalGradient_equivariant",
                "weightedCauchySchwarz_of_right_pos",
                "scalarCramerRao",
                "mirrorDescent_threePoint_identity",
                "affineProjection_bregmanPythagorean",
                "affineProjection_minimizes",
                "replicator_naturalGradient_equivalence",
                "twoCategorical_replicator_nonzero_witness",
            ),
        ),
    ),
)
def test_slice05_foundations_expose_exact_witness_contracts(
    resource: str, declarations: tuple[str, ...]
) -> None:
    source = (FORMAL_ROOT / resource).read_text(encoding="utf-8")
    for declaration in declarations:
        assert re.search(rf"(?m)^theorem {declaration}\b", source), declaration
    assert "fep_all" not in source
    assert not re.search(r"(?m)^\s*(?:axiom|opaque)\b", source)
    assert not re.search(r"\b(?:sorry|admit)\b", source)


def test_path_thermodynamics_keeps_support_and_rate_boundaries_visible() -> None:
    source = (FORMAL_ROOT / "path_thermodynamics.lean").read_text(encoding="utf-8")
    assert "hForward : ∀ path, 0 < protocol.forward path" in source
    assert "hReverse : ∀ path, 0 < protocol.reverseAligned path" in source
    assert "pathRatio_zero_reverse_boundary" in source
    assert "localAffinity_zero_reverseRate_boundary" in source
    assert "HasJarzynskiNormalization" in source
    assert "IsReversible stationary kernel" in source
    assert "finiteChannel_dataProcessing" in source


def test_geometric_optimization_extends_the_existing_fisher_carrier() -> None:
    source = (FORMAL_ROOT / "geometric_optimization.lean").read_text(encoding="utf-8")
    assert source.startswith("import FepSketches.information_geometry\n")
    assert "model : ScoreModel (Fin d) d" in source
    assert "fisherMetric model tangent tangent" in source
    assert "lowerTangent model tangent" in source
    assert "unbiased :" in source
    assert "scoreRegularity :" in source
    assert "fisher_pos :" in source
    assert "[Invertible (fisherMatrix model)]" in source


def test_two_categorical_geometry_has_concrete_interior_and_boundary_witnesses() -> (
    None
):
    source = (FORMAL_ROOT / "geometric_optimization.lean").read_text(encoding="utf-8")
    fep100 = GEOMETRY_BODIES["fep-100"]
    fep106 = GEOMETRY_BODIES["fep-106"]

    assert "twoCategoricalFisherCarrier : CategoricalFisherCarrier 2" in source
    assert "twoCategoricalTangent : Fin 2 → ℝ" in source
    assert "twoCategorical_simplexMetric_fullRank" in fep100
    assert "twoCategoricalTangent_spans" in fep100
    assert "twoCategorical_nonzeroTangent_metric" in fep100
    assert "duplicatedScore_nullDirection_example" in fep100
    assert "twoCategoricalFitness : Fin 2 → ℝ" in source
    assert "twoCategorical_replicator_nonzero_witness" in fep106
    assert "replicatorVector twoCategoricalLaw twoCategoricalFitness ≠ 0" in fep106


def test_slice05_go_no_go_bodies_are_substantive() -> None:
    fep099 = THERMO_BODIES["fep-099"]
    assert "reversibleKL_oneStep_dissipation" in fep099
    assert "IsReversible stationary kernel" in fep099
    assert "fep099_irreversiblePositiveProduction_witness" in fep099

    fep103 = GEOMETRY_BODIES["fep-103"]
    assert "naturalGradient_equivariant" in fep103
    assert "weightedCauchySchwarz_of_right_pos" in fep103
    assert "hRight : 0 <" in fep103


@pytest.mark.skipif(
    not RUN_NATIVE,
    reason="set FEP_LEAN_SLICE05_COMPILE_TEST=1 for serialized native checks",
)
@pytest.mark.parametrize("topic_id", ("fep-099", "fep-102", "fep-103"))
def test_slice05_gate_topics_compile_warning_free(
    tmp_path: Path, topic_id: str
) -> None:
    bodies = THERMO_BODIES if topic_id in THERMO_BODIES else GEOMETRY_BODIES
    result = _compile(_topic_closure(tmp_path, topic_id, bodies[topic_id]))
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "warning:" not in output.lower()


@pytest.mark.skipif(
    not RUN_NATIVE,
    reason="set FEP_LEAN_SLICE05_COMPILE_TEST=1 for serialized native checks",
)
@pytest.mark.parametrize(
    "resource", ("path_thermodynamics.lean", "geometric_optimization.lean")
)
def test_slice05_foundations_compile_warning_free(resource: str) -> None:
    result = _compile(FORMAL_ROOT / resource)
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "warning:" not in output.lower()


@pytest.mark.skipif(
    not RUN_NATIVE,
    reason="set FEP_LEAN_SLICE05_COMPILE_TEST=1 for serialized native checks",
)
@pytest.mark.parametrize(
    ("topic_id", "body"), (*THERMO_BODIES.items(), *GEOMETRY_BODIES.items())
)
def test_slice05_topic_bodies_compile_warning_free(
    tmp_path: Path, topic_id: str, body: str
) -> None:
    result = _compile(_topic_closure(tmp_path, topic_id, body))
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "warning:" not in output.lower()
