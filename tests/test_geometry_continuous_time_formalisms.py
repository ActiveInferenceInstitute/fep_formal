"""Source and opt-in native boundaries for catalogue rows 142--155."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import pytest

from fep_lean.catalogue.bodies.continuous_time_thermodynamics import (
    BODIES as CONTINUOUS_TIME_BODIES,
)
from fep_lean.catalogue.bodies.exponential_family_geometry import (
    BODIES as EXPONENTIAL_FAMILY_BODIES,
)
from tests._support.lake import lake_executable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEAN_ROOT = PROJECT_ROOT / "lean"
FORMAL_ROOT = PROJECT_ROOT / "src" / "fep_lean" / "formal"
COMPOSITIONS_ROOT = FORMAL_ROOT / "compositions"
SPIKE_ROOT = PROJECT_ROOT / "specs" / "done" / "formalism-catalogue-155" / "spikes"
GEOMETRY_IDS = tuple(f"fep-{number:03d}" for number in range(142, 149))
CONTINUOUS_TIME_IDS = tuple(f"fep-{number:03d}" for number in range(149, 156))
RUN_NATIVE = os.environ.get("FEP_LEAN_SLICE04_COMPILE_TEST") == "1"

COMPOSITION_BRIDGES = {
    "exponential_family.lean": (
        (
            "fep142_exponentialNormalization_extends_fep031",
            "fep_fep142.FEP142.fep142_exponentialFamily_sum_one",
            "fep_fep031.FEP031.fep031_gibbsProbability_sum_one",
        ),
        (
            "fep143_logDensityRatio_extends_fep026",
            "fep_fep143.FEP143.fep143_logDensityRatio_eq",
            "fep_fep026.FEP026.fep026_log_div",
        ),
        (
            "fep144_logPartitionGradient_extends_fep040",
            "fep_fep144.FEP144.fep144_logPartition_hasDerivAt",
            "fep_fep040.FEP040.fep040_gaussianEntropy_hasDerivAt",
        ),
        (
            "fep145_centeredScore_extends_fep038",
            "fep_fep145.FEP145.fep145_score_eq_statistic_sub_mean",
            "fep_fep038.FEP038.fep038_expectedScore_zero",
        ),
        (
            "fep146_fisherVariance_extends_fep100",
            "fep_fep146.FEP146.fep146_fisher_eq_variance",
            "fep_fep100.FEP100.fep100_categoricalFisher_simplexTangent_positivity",
        ),
        (
            "fep147_KLBregman_connects_fep014_fep104",
            "fep_fep147.FEP147.fep147_exponentialFamily_KL_eq_bregman",
            "fep_fep014.FEP014.fep014_kl_nonneg",
        ),
        (
            "fep148_meanCoordinate_extends_fep103",
            "fep_fep148.FEP148.fep148_meanParameter_injective",
            "fep_fep103.FEP103.fep103_naturalGradient_equivariance",
        ),
    ),
    "continuous_time.lean": (
        (
            "fep149_continuousKernel_extends_fep020",
            "fep_fep149.FEP149.fep149_twoStateSemigroup_rowSum",
            "fep_fep020.FEP020.fep020_transition_sum_one",
        ),
        (
            "fep150_semigroupZero_extends_fep006",
            "fep_fep150.FEP150.fep150_twoStateSemigroup_zero",
            "fep_fep006.FEP006.fep006_iterateFlow_zero",
        ),
        (
            "fep151_semigroupAdd_extends_fep006",
            "fep_fep151.FEP151.fep151_twoStateSemigroup_add",
            "fep_fep006.FEP006.fep006_iterateFlow_add",
        ),
        (
            "fep152_masterEquation_extends_fep020",
            "fep_fep152.FEP152.fep152_twoStateSemigroup_hasDerivAt",
            "fep_fep020.FEP020.fep020_evolve_affine",
        ),
        (
            "fep153_continuousDetailedBalance_extends_fep010",
            "fep_fep153.FEP153.fep153_twoStateSemigroup_detailedBalance",
            "fep_fep010.FEP010.fep010_identity_reversible",
        ),
        (
            "fep154_continuousRelaxation_extends_fep020",
            "fep_fep154.FEP154.fep154_twoStateRelaxation_exact",
            "fep_fep020.FEP020.fep020_deviation_step",
        ),
        (
            "fep155_lyapunovDecay_extends_fep032",
            "fep_fep155.FEP155.fep155_twoStateLyapunov_hasDerivAt",
            "fep_fep032.FEP032.fep032_quadraticEnergy_descent",
        ),
    ),
}

FORBIDDEN_DECLARATIONS = re.compile(
    r"(?m)^\s*(?:axiom|opaque|unsafe\s+(?:def|theorem))\b"
)
FORBIDDEN_PROOFS = re.compile(r"\b(?:sorry|admit)\b|:\s*True\b")

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
    if topic_id in GEOMETRY_IDS:
        resource = "exponential_family.lean"
    else:
        resource = "continuous_time_markov.lean"
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


def test_slice04_foundation_sources_exist() -> None:
    assert (FORMAL_ROOT / "exponential_family.lean").is_file()
    assert (FORMAL_ROOT / "continuous_time_markov.lean").is_file()


@pytest.mark.parametrize(
    ("resource", "keystones"),
    (
        (
            "exponential_family.lean",
            (
                "logPartition_hasDerivAt",
                "mean_hasDerivAt",
                "finiteKL_eq_logPartitionBregman",
                "threeState_variance_zero_pos",
            ),
        ),
        (
            "continuous_time_markov.lean",
            (
                "transition_add",
                "transition_masterEquation",
                "lyapunov_hasDerivAt",
                "benchmarkLyapunov_deriv_zero_neg",
            ),
        ),
    ),
)
def test_slice01_promoted_spikes_print_keystone_axioms(
    resource: str, keystones: tuple[str, ...]
) -> None:
    source = (SPIKE_ROOT / resource).read_text(encoding="utf-8")
    assert source.startswith(f"import FepSketches.{resource.removesuffix('.lean')}\n")
    for theorem in keystones:
        assert re.search(rf"(?m)^#print axioms .*\.{theorem}$", source), theorem
    assert not FORBIDDEN_DECLARATIONS.search(source)
    assert not FORBIDDEN_PROOFS.search(source)


def test_slice04_body_modules_own_exact_ordered_rosters() -> None:
    assert tuple(EXPONENTIAL_FAMILY_BODIES) == GEOMETRY_IDS
    assert tuple(CONTINUOUS_TIME_BODIES) == CONTINUOUS_TIME_IDS
    assert not (set(EXPONENTIAL_FAMILY_BODIES) & set(CONTINUOUS_TIME_BODIES))


@pytest.mark.parametrize(
    ("topic_id", "body"),
    (*EXPONENTIAL_FAMILY_BODIES.items(), *CONTINUOUS_TIME_BODIES.items()),
)
def test_slice04_bodies_are_standalone_scoped_sources(topic_id: str, body: str) -> None:
    digits = topic_id.removeprefix("fep-")
    assert body.startswith("import FepSketches.")
    assert f"namespace FEP{digits}\n" in body
    assert body.rstrip().endswith(f"end FEP{digits}")
    assert re.search(rf"\btheorem fep{digits}_[A-Za-z0-9_]+", body)
    assert not FORBIDDEN_DECLARATIONS.search(body)
    assert not FORBIDDEN_PROOFS.search(body)


@pytest.mark.parametrize(
    ("resource", "declarations"),
    (
        (
            "exponential_family.lean",
            (
                "weight_pos",
                "partition_pos",
                "law_pos",
                "mean_eq_expectation",
                "score_eq_statistic_sub_mean",
                "mean_score_zero",
                "weightedMoment_hasDerivAt",
                "logPartition_hasDerivAt",
                "mean_hasDerivAt",
                "law_hasDerivAt",
                "logDensityRatio_eq",
                "finiteKL_eq_logPartitionBregman",
                "fisher_eq_variance",
                "meanParameter_strictMono",
                "meanParameter_injectiveOn",
                "threeState_variance_zero_pos",
                "constantStatistic_variance_zero",
            ),
        ),
        (
            "continuous_time_markov.lean",
            (
                "decayRate_pos",
                "stationary_sum_one",
                "rho_add",
                "transition_rowSum",
                "transition_nonneg",
                "transition_zero",
                "transition_add",
                "transition_hasDerivAt",
                "generator_mul_transition",
                "transition_mul_generator",
                "transition_masterEquation",
                "transition_stationary",
                "transition_detailedBalance",
                "relaxation_exact",
                "lyapunov_exact",
                "lyapunov_hasDerivAt",
                "benchmarkInitial_nonstationary",
                "benchmarkLyapunov_deriv_zero_neg",
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
    assert "namespace FEP1" not in source
    assert not FORBIDDEN_DECLARATIONS.search(source)
    assert not FORBIDDEN_PROOFS.search(source)


def test_exponential_family_keeps_finite_scalar_support_visible() -> None:
    source = (FORMAL_ROOT / "exponential_family.lean").read_text(encoding="utf-8")
    bodies = "\n".join(EXPONENTIAL_FAMILY_BODIES.values())

    assert "[Fintype Outcome] [Nonempty Outcome]" in source
    assert "base_pos : ∀ outcome, 0 < base outcome" in source
    assert "Real.exp (parameter * family.statistic outcome)" in source
    assert "threeStateStatistic : Fin 3 → ℝ := ![0, 1, 2]" in source
    assert "threeState_variance_zero : threeStateFamily.variance 0 = 2 / 3" in source
    assert "constantStatistic_variance_zero" in source
    assert "finiteKL (family.law left) (family.law right)" in bodies
    assert "Set.Icc lower upper" in bodies


def test_continuous_time_source_preserves_two_state_plot_ready_regression() -> None:
    source = (FORMAL_ROOT / "continuous_time_markov.lean").read_text(encoding="utf-8")
    bodies = "\n".join(CONTINUOUS_TIME_BODIES.values())

    assert "transition (rates : TwoStateRates)" in source
    assert "(source target : Bool)" in source
    assert "forward := 7 / 10" in source
    assert "backward := 3 / 10" in source
    assert "FiniteLaw.pointMass false" in source
    assert "transition_masterEquation" in bodies
    assert "transition_stationary" in bodies
    assert "transition_detailedBalance" in bodies
    assert "benchmarkLyapunov_deriv_zero_neg" in bodies


def test_h17_certified_semigroup_carriers_are_explicit() -> None:
    source = (FORMAL_ROOT / "continuous_time_markov.lean").read_text(encoding="utf-8")

    assert "import FepSketches.active_inference\n" in source
    assert "import FepSketches.controlled_markov\n" not in source
    assert "import FepSketches.markov_blanket\n" in source
    assert "import Mathlib.Analysis.Normed.Algebra.MatrixExponential\n" in source
    assert re.search(r"(?m)^structure FiniteRateGenerator\b", source)
    assert re.search(r"(?m)^structure FiniteMarkovSemigroup\b", source)
    assert "noncomputable def exponentialCandidate" in source
    assert "entrywise stochasticity is not inferred" in source


def test_h17_action_interface_samples_the_certified_semigroup_exactly() -> None:
    source = (FORMAL_ROOT / "continuous_time_markov.lean").read_text(encoding="utf-8")

    assert re.search(r"(?m)^structure ActionIndexedSemigroup\b", source)
    assert re.search(r"(?m)^noncomputable def sampledKernel\b", source)
    assert re.search(r"(?m)^noncomputable def toActionInterface\b", source)
    assert re.search(
        r"(?m)^theorem selectedActionTransition_eq_sampledSemigroup\b", source
    )
    assert "actionTransition := indexed.sampledKernel" in source
    assert "transition_consistent := transition_consistent" in source


def test_h17_action_semigroup_is_the_single_generative_transition_owner() -> None:
    source = (FORMAL_ROOT / "continuous_time_markov.lean").read_text(encoding="utf-8")

    assert re.search(r"(?m)^noncomputable def toGenerativeModel\b", source)
    assert (
        "transition policy := indexed.sampledKernel (policyToAction policy)" in source
    )
    assert re.search(r"(?m)^theorem toGenerativeModel_transition\b", source)
    assert re.search(
        r"(?m)^noncomputable def toGenerativeModelActionInterface\b", source
    )
    assert "indexed.toActionInterface" in source
    assert "fun _ => rfl" in source


def test_h17_native_kl_contraction_uses_mathlib_kernel_dpi() -> None:
    source = (FORMAL_ROOT / "continuous_time_markov.lean").read_text(encoding="utf-8")

    assert "import FepSketches.decision_risk\n" in source
    assert re.search(r"(?m)^theorem nativeKL_contraction\b", source)
    assert re.search(r"(?m)^theorem nativeKL_contraction_to_invariant\b", source)
    assert "InformationTheory.klDiv_comp_right_le" in source
    assert source.count("FEP.NativeBlanket.embeddedPredictive_eq_comp") >= 2


def test_h17_two_state_regression_instantiates_the_general_certificate() -> None:
    source = (FORMAL_ROOT / "continuous_time_markov.lean").read_text(encoding="utf-8")

    for declaration in (
        "rateGenerator",
        "certifiedSemigroup",
        "certifiedSemigroup_kernel_eq_kernel",
        "certifiedSemigroup_stationary",
        "certifiedSemigroup_detailedBalanced",
    ):
        assert re.search(
            rf"(?m)^(?:noncomputable def|def|theorem) {declaration}\b", source
        ), declaration


def test_h17_three_state_steady_cycle_has_nonzero_probability_current() -> None:
    source = (FORMAL_ROOT / "continuous_time_markov.lean").read_text(encoding="utf-8")

    assert "def IsStationary (generator : FiniteRateGenerator" in source
    assert "def IsDetailedBalanced (generator : FiniteRateGenerator" in source
    assert "def probabilityCurrent (generator : FiniteRateGenerator" in source
    assert re.search(r"(?m)^def threeCycleGenerator\b", source)
    assert re.search(r"(?m)^noncomputable def threeCycleStationaryLaw\b", source)
    assert re.search(r"(?m)^theorem threeCycle_stationary\b", source)
    assert re.search(r"(?m)^theorem threeCycle_not_detailedBalanced\b", source)
    assert re.search(r"(?m)^theorem threeCycle_current_zero_one_ne_zero\b", source)


def test_h17_exact_blanket_product_has_positive_refresh_semigroup() -> None:
    source = (FORMAL_ROOT / "continuous_time_markov.lean").read_text(encoding="utf-8")

    assert re.search(r"(?m)^noncomputable def refreshSemigroup\b", source)
    assert re.search(r"(?m)^theorem refreshTransition_pos\b", source)
    assert re.search(r"(?m)^noncomputable def blanketRefreshSemigroup\b", source)
    assert re.search(r"(?m)^theorem refreshSemigroup_uniform_stationary\b", source)
    assert "FEP.MarkovBlanket.DynamicState Internal Sensory Active External" in source
    assert "[Nontrivial Internal] [Nontrivial Sensory]" in source
    assert "[Nontrivial Active] [Nontrivial External]" in source
    assert re.search(r"(?m)^theorem blanketPointMass_ne_uniform\b", source)
    assert re.search(r"(?m)^def boolBlanketOrigin\b", source)
    assert re.search(r"(?m)^noncomputable def boolBlanketInitialLaw\b", source)
    assert re.search(r"(?m)^theorem boolBlanketInitial_ne_uniform\b", source)
    assert re.search(r"(?m)^theorem boolBlanketStationaryLaw_isStationary\b", source)


def test_h17_internal_law_and_likelihood_lift_share_the_exact_blanket_carrier() -> None:
    source = (FORMAL_ROOT / "continuous_time_markov.lean").read_text(encoding="utf-8")

    assert re.search(r"(?m)^abbrev BoolBlanketState\b", source)
    assert "FEP.MarkovBlanket.DynamicState Bool Bool Bool Bool" in source
    assert re.search(r"(?m)^noncomputable def liftInternalLaw\b", source)
    assert "internal.product" in source
    assert "FiniteLaw.uniform : FiniteLaw (Bool × (Bool × Bool))" in source
    assert re.search(r"(?m)^theorem liftInternalLaw_fstMarginal\b", source)
    assert re.search(r"(?m)^theorem liftInternalLaw_ne_uniform_of_ne_uniform\b", source)
    assert re.search(r"(?m)^def liftInternalLikelihood\b", source)
    assert "likelihood state.1 observation" in source
    assert re.search(
        r"(?m)^theorem liftInternalLikelihood_predictive_liftInternalLaw\b",
        source,
    )
    assert "(liftInternalLikelihood likelihood).predictive" in source
    assert "likelihood.predictive internal" in source
    assert re.search(
        r"(?m)^theorem liftInternalLikelihood_posterior_liftInternalLaw\b",
        source,
    )
    assert "likelihood.posterior internal observation hEvidence" in source


def test_h17_bool_blanket_carrier_has_exactly_sixteen_states() -> None:
    source = (FORMAL_ROOT / "continuous_time_markov.lean").read_text(encoding="utf-8")

    assert re.search(r"(?m)^theorem boolBlanketState_card\b", source)
    assert "Fintype.card BoolBlanketState = 16" in source


def test_h17_bool_blanket_actions_are_exact_hold_and_refresh_kernels() -> None:
    source = (FORMAL_ROOT / "continuous_time_markov.lean").read_text(encoding="utf-8")

    assert re.search(r"(?m)^noncomputable def boolBlanketActionSampleTime\b", source)
    assert "if action then boolBlanketRefreshTime else 0" in source
    assert re.search(r"(?m)^theorem boolBlanketActionSampleTime_nonneg\b", source)
    assert re.search(
        r"(?m)^noncomputable def boolBlanketActionIndexedSemigroup\b", source
    )
    assert "ActionIndexedSemigroup BoolBlanketState Bool" in source
    assert "semigroup _ :=" in source
    assert re.search(
        r"(?m)^theorem boolBlanketActionIndexedSemigroup_false_kernel\b", source
    )
    assert "FiniteKernel.identity" in source
    assert re.search(
        r"(?m)^theorem boolBlanketActionIndexedSemigroup_true_kernel\b", source
    )
    assert "boolBlanketRefreshKernel" in source
    assert re.search(
        r"(?m)^theorem boolBlanketActionIndexedSemigroup_kernels_ne\b", source
    )


def test_h17_bool_blanket_generative_model_reuses_the_action_semigroup() -> None:
    source = (FORMAL_ROOT / "continuous_time_markov.lean").read_text(encoding="utf-8")

    assert re.search(r"(?m)^noncomputable def boolBlanketGenerativeModel\b", source)
    assert "GenerativeModel Bool BoolBlanketState Bool" in source
    assert "boolBlanketActionIndexedSemigroup.toGenerativeModel id" in source
    assert re.search(r"(?m)^theorem boolBlanketGenerativeModel_transition\b", source)
    assert re.search(
        r"(?m)^noncomputable def boolBlanketGenerativeModelActionInterface\b",
        source,
    )
    assert "toGenerativeModelActionInterface" in source


def test_h17_hold_policy_preserves_the_lifted_internal_observation_law() -> None:
    source = (FORMAL_ROOT / "continuous_time_markov.lean").read_text(encoding="utf-8")

    assert re.search(
        r"(?m)^theorem boolBlanketGenerativeModel_false_predictedOutcome\b",
        source,
    )
    assert "predictedOutcome" in source
    assert "liftInternalLaw internal" in source
    assert "liftInternalLikelihood likelihood" in source
    assert "likelihood.predictive internal" in source
    assert "boolBlanketActionIndexedSemigroup_false_kernel" in source
    assert "liftInternalLikelihood_predictive_liftInternalLaw" in source
    assert re.search(
        r"(?m)^theorem boolBlanketGenerativeModel_false_posteriorState\b",
        source,
    )
    assert "posteriorState" in source
    assert "liftInternalLikelihood_posterior_liftInternalLaw" in source


def test_h17_bool_blanket_refresh_strictly_decreases_native_kl() -> None:
    source = (FORMAL_ROOT / "continuous_time_markov.lean").read_text(encoding="utf-8")

    assert re.search(r"(?m)^theorem refreshSemigroup_predictive_mass\b", source)
    assert re.search(
        r"(?m)^theorem refreshSemigroup_finiteKL_strict_decrease_of_ne_uniform\b",
        source,
    )
    assert re.search(
        r"(?m)^theorem refreshSemigroup_nativeKL_strict_decrease_of_ne_uniform\b",
        source,
    )
    assert re.search(r"(?m)^noncomputable def boolBlanketRefreshTime\b", source)
    assert re.search(r"(?m)^noncomputable def boolBlanketEvolvedLaw\b", source)
    assert re.search(r"(?m)^theorem boolBlanket_finiteKL_strict_decrease\b", source)
    assert re.search(r"(?m)^theorem boolBlanket_nativeKL_strict_decrease\b", source)
    noninvariance = re.search(
        r"(?ms)^theorem boolBlanketInitial_not_invariant\b(.*?)(?=^theorem |^end )",
        source,
    )
    assert noninvariance is not None
    assert "¬FEP.FiniteMarkovDynamics.IsInvariant" in "".join(
        noninvariance.group(1).split()
    )
    assert "boolBlanketInitialLaw boolBlanketRefreshKernel" in " ".join(
        noninvariance.group(1).split()
    )
    assert (
        source.count("FEP.DecisionRisk.weightedDirac_klDiv_eq_finiteKL_of_fullSupport")
        >= 2
    )
    assert "FEP.MarkovBlanket.DynamicState Bool Bool Bool Bool" in source


def test_slice04_theorem_names_do_not_overclaim_scope() -> None:
    theorem_names = re.findall(
        r"(?m)^theorem\s+([A-Za-z0-9_]+)",
        "\n".join(
            (
                (FORMAL_ROOT / "exponential_family.lean").read_text(encoding="utf-8"),
                (FORMAL_ROOT / "continuous_time_markov.lean").read_text(
                    encoding="utf-8"
                ),
                *EXPONENTIAL_FAMILY_BODIES.values(),
                *CONTINUOUS_TIME_BODIES.values(),
            )
        ),
    )
    forbidden_token = re.compile(
        r"(?:^|_)(?:manifold|curvature|sde|fokker|planck|pde)(?:_|$)", re.IGNORECASE
    )
    assert all(not forbidden_token.search(name) for name in theorem_names)


@pytest.mark.parametrize(
    ("resource", "foundation", "bridges"),
    (
        (
            "exponential_family.lean",
            "FepSketches.exponential_family",
            COMPOSITION_BRIDGES["exponential_family.lean"],
        ),
        (
            "continuous_time.lean",
            "FepSketches.continuous_time_markov",
            COMPOSITION_BRIDGES["continuous_time.lean"],
        ),
    ),
)
def test_slice04_composition_leaves_pin_exact_bridges_and_endpoint_proofs(
    resource: str,
    foundation: str,
    bridges: tuple[tuple[str, str, str], ...],
) -> None:
    source = (COMPOSITIONS_ROOT / resource).read_text(encoding="utf-8")
    assert source.startswith("import FepSketches.fep_all\n")
    assert f"import {foundation}\n" in source
    assert "namespace FEPComposed\n" in source
    assert source.rstrip().endswith("end FEPComposed")
    assert len(bridges) == 7
    assert tuple(re.findall(r"(?m)^theorem\s+([A-Za-z0-9_]+)", source)) == tuple(
        bridge[0] for bridge in bridges
    )

    for index, (name, new_ref, endpoint_ref) in enumerate(bridges):
        start = source.index(f"theorem {name}")
        end = (
            source.index(f"theorem {bridges[index + 1][0]}")
            if index + 1 < len(bridges)
            else source.index("end FEPComposed")
        )
        declaration = source[start:end]
        statement, proof = declaration.split(":= by", maxsplit=1)
        assert "∧" in statement, name
        assert new_ref in proof, name
        assert endpoint_ref in proof, name

    assert not FORBIDDEN_DECLARATIONS.search(source)
    assert not FORBIDDEN_PROOFS.search(source)


@pytest.mark.skipif(
    not RUN_NATIVE,
    reason="set FEP_LEAN_SLICE04_COMPILE_TEST=1 for serialized native checks",
)
@pytest.mark.parametrize(
    "resource", ("exponential_family.lean", "continuous_time_markov.lean")
)
def test_slice04_foundations_compile_warning_free(resource: str) -> None:
    result = _compile(FORMAL_ROOT / resource)
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "warning:" not in output.lower()


@pytest.mark.skipif(
    not RUN_NATIVE,
    reason="set FEP_LEAN_SLICE04_COMPILE_TEST=1 for serialized native checks",
)
@pytest.mark.parametrize(
    ("topic_id", "body"),
    (*EXPONENTIAL_FAMILY_BODIES.items(), *CONTINUOUS_TIME_BODIES.items()),
)
def test_slice04_topic_bodies_compile_warning_free(
    tmp_path: Path, topic_id: str, body: str
) -> None:
    result = _compile(_topic_closure(tmp_path, topic_id, body))
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "warning:" not in output.lower()
