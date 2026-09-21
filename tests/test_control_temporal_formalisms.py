"""Native boundaries for controlled-Markov and temporal-inference families."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

from fep_lean.catalogue.bodies.controlled_markov import BODIES as CONTROL_BODIES
from fep_lean.catalogue.bodies.temporal_inference import BODIES as TEMPORAL_BODIES
from tests._support.lake import lake_executable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEAN_ROOT = PROJECT_ROOT / "lean"
FORMAL_ROOT = PROJECT_ROOT / "src" / "fep_lean" / "formal"

CONTROL_IDS = tuple(f"fep-{number:03d}" for number in range(65, 72))
TEMPORAL_IDS = tuple(f"fep-{number:03d}" for number in range(72, 79))

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


def _foundation_closure(tmp_path: Path, resource: str) -> Path:
    """Materialize a source-only closure without mutating shared projections."""
    source = FORMAL_ROOT / resource
    if resource == "controlled_markov.lean":
        return source
    import_line = "import FepSketches.controlled_markov\n"
    temporal = source.read_text(encoding="utf-8")
    assert temporal.startswith(import_line)
    closure = tmp_path / resource
    closure.write_text(
        (FORMAL_ROOT / "controlled_markov.lean").read_text(encoding="utf-8")
        + "\n"
        + temporal.removeprefix(import_line),
        encoding="utf-8",
    )
    return closure


def _topic_closure(tmp_path: Path, topic_id: str, body: str) -> Path:
    """Materialize one topic with its canonical family foundation closure."""
    if topic_id in CONTROL_IDS:
        foundation = (FORMAL_ROOT / "controlled_markov.lean").read_text(
            encoding="utf-8"
        )
        import_line = "import FepSketches.controlled_markov\n"
    else:
        controlled = (FORMAL_ROOT / "controlled_markov.lean").read_text(
            encoding="utf-8"
        )
        temporal_import = "import FepSketches.controlled_markov\n"
        temporal = (FORMAL_ROOT / "temporal_inference.lean").read_text(encoding="utf-8")
        assert temporal.startswith(temporal_import)
        foundation = controlled + "\n" + temporal.removeprefix(temporal_import)
        import_line = "import FepSketches.temporal_inference\n"
    assert body.startswith(import_line)
    source = tmp_path / f"{topic_id}.lean"
    source.write_text(
        foundation + "\n" + body.removeprefix(import_line), encoding="utf-8"
    )
    return source


def test_slice03_body_modules_own_one_exact_ordered_roster() -> None:
    assert tuple(CONTROL_BODIES) == CONTROL_IDS
    assert tuple(TEMPORAL_BODIES) == TEMPORAL_IDS
    assert not (set(CONTROL_BODIES) & set(TEMPORAL_BODIES))


@pytest.mark.parametrize(
    ("topic_id", "body"),
    (*CONTROL_BODIES.items(), *TEMPORAL_BODIES.items()),
)
def test_slice03_bodies_are_standalone_scoped_sources(topic_id: str, body: str) -> None:
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
            "controlled_markov.lean",
            (
                "controlledKernel_sum_one",
                "actionBeliefUpdate_reconstruction",
                "reachableBelief_policyValue_eq",
                "softBellmanPartition_pos",
                "softBellmanValue_succ",
                "softBellmanValue_le_actionEnergy",
                "desirabilityStep_nonneg",
                "controlPosterior_sum_one",
                "sophisticatedEFEValue_succ",
                "boolReachablePOMDP_update_sound",
                "twoStageFeedback_changes_action",
                "twoStageFeedback_beats_openLoop",
            ),
        ),
        (
            "temporal_inference.lean",
            (
                "forwardFilter_reconstruction",
                "backwardMessage_nonneg",
                "forwardBackwardSmoothing_factorization",
                "forwardBackwardSmoothing_sum_one",
                "variationalStateUpdate_sum_one",
                "hierarchicalPredictive_eq",
                "modelAverage_sum_one",
                "forward_backward_evidence_agree",
                "boolForwardFilter_true_mass",
                "boolSmoothing_sum_one",
            ),
        ),
    ),
)
def test_slice03_foundations_expose_exact_witness_contracts(
    resource: str, declarations: tuple[str, ...]
) -> None:
    source = (FORMAL_ROOT / resource).read_text(encoding="utf-8")
    for declaration in declarations:
        assert re.search(rf"(?m)^theorem {declaration}\b", source), declaration
    assert not re.search(r"(?m)^\s*(?:axiom|opaque)\b", source)
    assert not re.search(r"\b(?:sorry|admit)\b", source)


def test_soft_bellman_topic_requires_nonempty_actions_and_uses_temperature() -> None:
    foundation = (FORMAL_ROOT / "controlled_markov.lean").read_text(encoding="utf-8")
    body = CONTROL_BODIES["fep-068"]

    assert "[Nonempty Action]" in body
    assert "softBellmanValue_partition_pos" in body
    assert "softBellmanValue_le_actionEnergy" in body
    assert "hTemperature" in body
    assert "∀ action" in body
    assert "softBellmanValue_le_actionEnergy" in foundation


@pytest.mark.parametrize(
    "resource", ("controlled_markov.lean", "temporal_inference.lean")
)
def test_slice03_foundations_compile_warning_free(
    tmp_path: Path, resource: str
) -> None:
    result = _compile(_foundation_closure(tmp_path, resource))

    assert result.returncode == 0, result.stdout + result.stderr
    assert "warning:" not in (result.stdout + result.stderr).lower()


@pytest.mark.parametrize(
    ("topic_id", "body"),
    (*CONTROL_BODIES.items(), *TEMPORAL_BODIES.items()),
)
def test_slice03_topic_bodies_compile_warning_free(
    tmp_path: Path, topic_id: str, body: str
) -> None:
    result = _compile(_topic_closure(tmp_path, topic_id, body))

    assert result.returncode == 0, result.stdout + result.stderr
    assert "warning:" not in (result.stdout + result.stderr).lower()
