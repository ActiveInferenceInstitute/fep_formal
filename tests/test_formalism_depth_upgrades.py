"""Native-Mathlib depth upgrades stay attached to their reviewed topic rows."""

from __future__ import annotations

from pathlib import Path

import pytest

from fep_formal.catalogue.registry import BODIES
from fep_formal.catalogue.relations import EdgeKind, load_formalism_graph
from fep_formal.catalogue.schema import load_catalogue_metadata
from fep_formal.catalogue.semantics import SemanticDisposition, load_theorem_maturity
from fep_formal.verification.formalism_audit import parse_axiom_output
from tests._support.lake import lake_executable
from tests._support.lean_runner import run_lean_compile_probe

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_native_formalism_upgrades_replace_named_proxies() -> None:
    expected_fragments = {
        "fep-009": "CondIndep",
        "fep-010": "Kernel.IsReversible",
        "fep-030": "Real.binEntropy_le_log_two",
        "fep-035": "strictConcaveOn_log_Ioi",
        "fep-048": "ContractingWith",
    }
    for topic_id, fragment in expected_fragments.items():
        assert fragment in BODIES[topic_id]

    assert "Real.exp" not in BODIES["fep-010"]
    assert "def IsContractionWith" not in BODIES["fep-048"]


def test_promoted_rows_name_the_exact_native_primary_theorems() -> None:
    audit = load_theorem_maturity(
        PROJECT_ROOT / "config" / "theorem_maturity.yaml"
    ).by_topic_id
    expected = {
        "fep-009": "fep009_condIndep_symm",
        "fep-010": "fep010_reversible_invariant",
        "fep-030": "fep030_binaryEntropy_max",
        "fep-035": "fep035_log_jensen_two_strict",
        "fep-048": "fep048_contraction_unique",
    }
    for topic_id, primary in expected.items():
        assert audit[topic_id].primary_theorem == primary
        assert audit[topic_id].disposition is SemanticDisposition.FORMALIZED


def test_topic_titles_describe_the_narrowed_formal_surface() -> None:
    metadata = {
        row.id: row
        for row in load_catalogue_metadata(
            PROJECT_ROOT / "config" / "catalogue_metadata.yaml"
        )
    }
    assert metadata["fep-009"].title == "Conditional Independence Laws"
    assert metadata["fep-010"].title == "Detailed Balance Implies Invariance"


def test_fep017_uses_native_posterior_reconstruction_and_normalization() -> None:
    body = BODIES["fep-017"]
    assert "Mathlib.Probability.Kernel.Posterior" in body
    assert "ProbabilityTheory.posterior" in body
    assert "fep017_posterior_mass_one" in body
    assert "fep017_posterior_joint_reconstruction" in body
    assert "fep017_posterior_recovers_prior" in body
    assert "fep017_posterior_bayes_density" in body
    assert "likelihood s * prior s" not in body

    audit = load_theorem_maturity(
        PROJECT_ROOT / "config" / "theorem_maturity.yaml"
    ).by_topic_id["fep-017"]
    assert audit.primary_theorem == "fep017_posterior_joint_reconstruction"
    assert audit.disposition is SemanticDisposition.FORMALIZED

    metadata = {
        row.id: row
        for row in load_catalogue_metadata(
            PROJECT_ROOT / "config" / "catalogue_metadata.yaml"
        )
    }
    assert metadata["fep-017"].title == "Posterior Kernel Reconstruction"

    graph = load_formalism_graph(PROJECT_ROOT / "config" / "formalism_relations.yaml")
    assert not any(
        edge.source == "fep-017" and edge.kind is EdgeKind.BLOCKED_BY
        for edge in graph.edges
    )


def test_fep034_is_a_normalized_transition_observation_filter() -> None:
    body = BODIES["fep-034"]
    assert "Mathlib.Probability.Kernel.Posterior" in body
    assert "fep034_predictivePrior" in body
    assert "fep034_predictive_mass" in body
    assert "fep034_filter_mass_one" in body
    assert "fep034_filter_joint_reconstruction" in body
    assert "fep034_filter_recovers_prediction" in body
    assert "like s * ∑" not in body

    audit = load_theorem_maturity(
        PROJECT_ROOT / "config" / "theorem_maturity.yaml"
    ).by_topic_id["fep-034"]
    assert audit.primary_theorem == "fep034_filter_joint_reconstruction"
    assert audit.disposition is SemanticDisposition.FORMALIZED

    metadata = {
        row.id: row
        for row in load_catalogue_metadata(
            PROJECT_ROOT / "config" / "catalogue_metadata.yaml"
        )
    }
    assert metadata["fep-034"].title == "Normalized Bayesian Filtering"

    graph = load_formalism_graph(PROJECT_ROOT / "config" / "formalism_relations.yaml")
    normalization = next(
        node
        for node in graph.capabilities
        if node.id == "cap-probability-normalization"
    )
    assert normalization.status.value == "satisfied"
    assert "fep_fep017.FEP017.fep017_posterior_mass_one" in normalization.evidence
    assert "fep_fep034.FEP034.fep034_filter_mass_one" in normalization.evidence


def test_predictive_and_hierarchical_topics_share_native_kernel_composition() -> None:
    expected = {
        "fep-019": (
            "fep019_priorPredictive_mass",
            "fep019_priorPredictive_assoc",
        ),
        "fep-022": (
            "fep022_posteriorPredictive_mass_one",
            "fep022_brier_decomposition",
            "fep022_brier_eq_optimum_iff",
        ),
        "fep-027": (
            "fep027_hierarchical_fst",
            "fep027_hierarchical_snd",
            "fep027_hierarchical_assoc",
        ),
    }
    for topic_id, declarations in expected.items():
        body = BODIES[topic_id]
        assert "Mathlib.Probability.Kernel" in body
        for declaration in declarations:
            assert declaration in body

    audit = load_theorem_maturity(
        PROJECT_ROOT / "config" / "theorem_maturity.yaml"
    ).by_topic_id
    assert audit["fep-019"].primary_theorem == "fep019_priorPredictive_assoc"
    assert audit["fep-022"].primary_theorem == "fep022_brier_eq_optimum_iff"
    assert audit["fep-027"].primary_theorem == "fep027_hierarchical_assoc"
    assert all(
        audit[topic_id].disposition is SemanticDisposition.FORMALIZED
        for topic_id in ("fep-019", "fep-022", "fep-027")
    )

    graph = load_formalism_graph(PROJECT_ROOT / "config" / "formalism_relations.yaml")
    posterior_predictive = next(
        node
        for node in graph.capabilities
        if node.id == "cap-posterior-predictive-model"
    )
    hierarchical = next(
        node
        for node in graph.capabilities
        if node.id == "cap-hierarchical-factorization"
    )
    assert posterior_predictive.status.value == "satisfied"
    assert hierarchical.status.value == "satisfied"


def test_bernoulli_statistics_close_sufficiency_and_finite_conjugacy() -> None:
    expected = {
        "fep-036": (
            "fep036_binomialModel",
            "fep036_binomialModel_apply",
            "fep036_empiricalPrior_mem_Ioo",
            "fep036_smoothedRate_pos",
            "fep036_smoothedRate_lt_one",
            "fep036_smoothedRate_eq_shrunkEmpirical",
            "fep036_smoothedRate_tendsto_of_empiricalRate",
        ),
        "fep-042": (
            "fep042_likelihood_factorizes",
            "fep042_likelihood_eq_of_stat_eq",
        ),
        "fep-045": (
            "fep045_posteriorParameter_mem_unit",
            "fep045_bernoulli_posterior_closed",
            "fep045_posterior_mass_one",
        ),
    }
    for topic_id, declarations in expected.items():
        body = BODIES[topic_id]
        for declaration in declarations:
            assert declaration in body

    audit = load_theorem_maturity(
        PROJECT_ROOT / "config" / "theorem_maturity.yaml"
    ).by_topic_id
    assert audit["fep-042"].primary_theorem == "fep042_likelihood_eq_of_stat_eq"
    assert audit["fep-045"].primary_theorem == "fep045_bernoulli_posterior_closed"
    assert (
        audit["fep-036"].primary_theorem
        == "fep036_smoothedRate_tendsto_of_empiricalRate"
    )
    assert audit["fep-036"].disposition is SemanticDisposition.FORMALIZED
    assert audit["fep-042"].disposition is SemanticDisposition.FORMALIZED
    assert audit["fep-045"].disposition is SemanticDisposition.FORMALIZED

    graph = load_formalism_graph(PROJECT_ROOT / "config" / "formalism_relations.yaml")
    statuses = {node.id: node.status.value for node in graph.capabilities}
    assert statuses["cap-sufficient-statistics"] == "satisfied"
    assert statuses["cap-conjugacy-laws"] == "satisfied"
    assert statuses["cap-empirical-bayes-model"] == "satisfied"


def test_information_geometry_uses_bernoulli_fisher_kl_and_hellinger_laws() -> None:
    expected = {
        "fep-018": (
            "fep018_fisherRaoDistance_triangle",
            "fep018_fisherRaoDistance_eq_zero_iff",
        ),
        "fep-038": (
            "fep038_bernoulliMass_hasDerivAt",
            "fep038_expectedScore_zero",
            "fep038_fisherInformation_eq",
            "fep038_naturalGradient_duality",
            "fep038_fisherMetric_coordinate",
        ),
        "fep-041": (
            "InformationTheory.klDiv",
            "fep041_informationGain_nonneg",
            "fep041_expectedInformationGain_zero",
        ),
        "fep-044": (
            "fep044_hellingerSq_nonneg",
            "fep044_hellingerSq_eq_zero_iff",
            "fep044_hellingerSq_symm",
        ),
    }
    for topic_id, declarations in expected.items():
        body = BODIES[topic_id]
        for declaration in declarations:
            assert declaration in body

    audit = load_theorem_maturity(
        PROJECT_ROOT / "config" / "theorem_maturity.yaml"
    ).by_topic_id
    assert audit["fep-018"].primary_theorem == "fep018_fisherRaoDistance_eq_zero_iff"
    assert audit["fep-038"].primary_theorem == "fep038_fisherInformation_eq"
    assert audit["fep-041"].primary_theorem == "fep041_expectedInformationGain_zero"
    assert audit["fep-044"].primary_theorem == "fep044_hellingerSq_eq_zero_iff"
    assert all(
        audit[topic_id].disposition is SemanticDisposition.FORMALIZED
        for topic_id in ("fep-018", "fep-038", "fep-041", "fep-044")
    )

    graph = load_formalism_graph(PROJECT_ROOT / "config" / "formalism_relations.yaml")
    statuses = {node.id: node.status.value for node in graph.capabilities}
    assert statuses["cap-statistical-manifold"] == "satisfied"
    assert statuses["cap-convex-information-functionals"] == "satisfied"


def test_two_state_markov_relaxation_has_transition_stationarity_and_limit() -> None:
    body = BODIES["fep-020"]
    for declaration in (
        "fep020_transition_nonneg",
        "fep020_transition_sum_one",
        "fep020_evolve_affine",
        "fep020_uniform_stationary",
        "fep020_iterate_deviation",
        "fep020_tendsto_uniform",
    ):
        assert declaration in body
    assert "langevinStep" not in body

    audit = load_theorem_maturity(
        PROJECT_ROOT / "config" / "theorem_maturity.yaml"
    ).by_topic_id["fep-020"]
    assert audit.primary_theorem == "fep020_tendsto_uniform"
    assert audit.disposition is SemanticDisposition.FORMALIZED

    graph = load_formalism_graph(PROJECT_ROOT / "config" / "formalism_relations.yaml")
    dynamics = next(
        node for node in graph.capabilities if node.id == "cap-stochastic-dynamics"
    )
    assert dynamics.status.value == "satisfied"


def test_probability_currents_and_constitutive_entropy_production_are_explicit() -> (
    None
):
    expected = {
        "fep-025": (
            "fep025_probabilityCurrent_antisymm",
            "fep025_total_divergence_zero",
            "fep025_transitionCurrent_stationary",
            "fep025_cycleCurrent_stationary",
            "fep025_cycleCurrent_nonzero",
        ),
        "fep-049": (
            "fep049_linearFlux",
            "fep049_flux_force_identity",
            "fep049_edgeProduction_nonneg",
            "fep049_edgeProduction_eq_zero_iff",
            "fep049_entropyProduction_nonneg",
            "fep049_entropyProduction_eq_zero_iff",
        ),
    }
    for topic_id, declarations in expected.items():
        for declaration in declarations:
            assert declaration in BODIES[topic_id]

    audit = load_theorem_maturity(
        PROJECT_ROOT / "config" / "theorem_maturity.yaml"
    ).by_topic_id
    assert audit["fep-025"].primary_theorem == "fep025_cycleCurrent_stationary"
    assert audit["fep-049"].primary_theorem == "fep049_entropyProduction_eq_zero_iff"
    assert audit["fep-025"].disposition is SemanticDisposition.FORMALIZED
    assert audit["fep-049"].disposition is SemanticDisposition.FORMALIZED


def test_landauer_bound_is_derived_from_finite_path_erasure_protocol() -> None:
    body = BODIES["fep-050"]
    for declaration in (
        "fep050_erasure_not_injective",
        "fep050_erasureEntropyLoss_eq",
        "fep050_landauer_heat_bound",
        "fep050_landauer_work_bound",
    ):
        assert declaration in body
    assert "(hW : fep050_landauer_bound" not in body
    path_bound = body.split("theorem fep050_generalized_landauer_heat_bound", 1)[1]
    path_bound = path_bound.split("/-- The Landauer threshold is positive", 1)[0]
    assert "hsecondLaw" not in path_bound
    assert "FEP.PathThermodynamics.erasure_landauer_reset model hReset" in path_bound
    assert "hBeta : model.beta = (kB * T)⁻¹" in path_bound
    assert "model.meanHeat ≤ W" in path_bound
    assert "(hReset : model.IsReset)" in path_bound
    assert "FEP.PathThermodynamics.ErasureModel Path" in path_bound

    audit = load_theorem_maturity(
        PROJECT_ROOT / "config" / "theorem_maturity.yaml"
    ).by_topic_id["fep-050"]
    assert audit.primary_theorem == "fep050_landauer_work_bound"
    assert audit.disposition is SemanticDisposition.FORMALIZED

    graph = load_formalism_graph(PROJECT_ROOT / "config" / "formalism_relations.yaml")
    erasure = next(
        node for node in graph.capabilities if node.id == "cap-physical-erasure-model"
    )
    assert erasure.status.value == "satisfied"


def test_native_gaussian_law_has_thermal_entropy_response() -> None:
    body = BODIES["fep-040"]
    for declaration in (
        "ProbabilityTheory.gaussianReal",
        "fep040_gaussian_mass_one",
        "fep040_gaussian_mean",
        "fep040_gaussian_variance",
        "fep040_gaussianEntropy_hasDerivAt",
        "fep040_thermalEntropy_hasDerivAt",
        "fep040_heatCapacity_eq_half",
    ):
        assert declaration in body

    audit = load_theorem_maturity(
        PROJECT_ROOT / "config" / "theorem_maturity.yaml"
    ).by_topic_id["fep-040"]
    assert audit.primary_theorem == "fep040_thermalEntropy_hasDerivAt"
    assert audit.disposition is SemanticDisposition.FORMALIZED

    graph = load_formalism_graph(PROJECT_ROOT / "config" / "formalism_relations.yaml")
    gaussian = next(
        node
        for node in graph.capabilities
        if node.id == "cap-gaussian-thermodynamic-model"
    )
    assert gaussian.status.value == "satisfied"


def test_two_state_fluctuation_response_has_decay_and_dynamics_witness() -> None:
    body = BODIES["fep-037"]
    for declaration in (
        "fep037_autocorrelation_recurrence",
        "fep037_autocorrelation_tendsto_zero",
        "fep037_response_eq",
        "fep037_response_nonneg",
        "fep037_response_tendsto_zero",
    ):
        assert declaration in body

    audit = load_theorem_maturity(
        PROJECT_ROOT / "config" / "theorem_maturity.yaml"
    ).by_topic_id["fep-037"]
    assert audit.primary_theorem == "fep037_response_eq"
    assert audit.disposition is SemanticDisposition.FORMALIZED


def test_efe_convention_uses_epistemic_value_with_explicit_sign() -> None:
    body = BODIES["fep-021"]
    for declaration in (
        "fep021_expectedFreeEnergy",
        "fep021_efe_epistemic_balance",
        "fep021_efe_mono_pragmatic",
        "fep021_efe_antitone_epistemic",
        "fep021_efe_eq_zero_iff",
    ):
        assert declaration in body
    assert "(h : risk + ambiguity = epistemic + pragmatic)" not in body

    audit = load_theorem_maturity(
        PROJECT_ROOT / "config" / "theorem_maturity.yaml"
    ).by_topic_id["fep-021"]
    assert audit.primary_theorem == "fep021_efe_epistemic_balance"
    assert audit.disposition is SemanticDisposition.FORMALIZED


def test_critical_point_topic_uses_fermat_and_exact_quadratic_curvature() -> None:
    body = BODIES["fep-043"]
    for declaration in (
        "IsLocalMin",
        "fep043_localMin_deriv_zero",
        "fep043_quadratic_hasDerivAt",
        "fep043_quadratic_unique_min",
        "fep043_quadratic_critical_iff",
        "fep043_quadraticGradient_hasDerivAt",
        "fep043_quadratic_hessian_pos",
    ):
        assert declaration in body

    audit = load_theorem_maturity(
        PROJECT_ROOT / "config" / "theorem_maturity.yaml"
    ).by_topic_id["fep-043"]
    assert audit.primary_theorem == "fep043_quadratic_critical_iff"
    assert audit.disposition is SemanticDisposition.FORMALIZED


def test_policy_cost_reachability_and_bellman_recursion_are_explicit() -> None:
    expected = {
        "fep-003": (
            "fep003_pragmaticCost_succ",
            "fep003_pragmaticCost_mono",
            "fep003_pragmaticCost_horizon_succ",
        ),
        "fep-023": (
            "fep023_reachableLaws",
            "fep023_reachable_normalized",
            "fep023_reachable_mono",
        ),
        "fep-033": (
            "fep033_bellman",
            "fep033_value_mono",
            "fep033_zeroCost",
            "fep033_zeroDiscount",
        ),
    }
    for topic_id, declarations in expected.items():
        for declaration in declarations:
            assert declaration in BODIES[topic_id]

    audit = load_theorem_maturity(
        PROJECT_ROOT / "config" / "theorem_maturity.yaml"
    ).by_topic_id
    assert all(
        audit[topic_id].disposition is SemanticDisposition.FORMALIZED
        for topic_id in ("fep-003", "fep-008", "fep-023", "fep-033")
    )


def test_vfe_bound_and_kl_regularizer_use_native_measure_divergence() -> None:
    expected = {
        "fep-001": (
            "InformationTheory.klDiv",
            "fep001_variationalUpperBound_ge",
            "fep001_variationalGap_eq_zero_iff",
            "fep001_variationalUpperBound_eq_iff",
        ),
        "fep-024": (
            "InformationTheory.klDiv",
            "fep024_klRegularizedObjective_ge",
            "fep024_klRegularizedObjective_zeroWeight",
            "fep024_klRegularizedObjective_exact",
        ),
    }
    for topic_id, declarations in expected.items():
        for declaration in declarations:
            assert declaration in BODIES[topic_id]

    audit = load_theorem_maturity(
        PROJECT_ROOT / "config" / "theorem_maturity.yaml"
    ).by_topic_id
    assert audit["fep-001"].disposition is SemanticDisposition.FORMALIZED
    assert audit["fep-024"].disposition is SemanticDisposition.FORMALIZED


def test_partition_and_measurable_flow_have_exact_structural_laws() -> None:
    assert "fep005_existsUnique_block" in BODIES["fep-005"]
    for declaration in (
        "fep006_iterateFlow_measurable",
        "fep006_iterateFlow_zero",
        "fep006_iterateFlow_add",
        "fep006_iterateFlow_fixed",
    ):
        assert declaration in BODIES["fep-006"]

    audit = load_theorem_maturity(
        PROJECT_ROOT / "config" / "theorem_maturity.yaml"
    ).by_topic_id
    assert audit["fep-005"].disposition is SemanticDisposition.FORMALIZED
    assert audit["fep-006"].disposition is SemanticDisposition.FORMALIZED


def test_remaining_exact_formalisms_replace_all_but_empirical_bayes_proxy() -> None:
    expected = {
        "fep-004": (
            "fep004_fisherMetric",
            "fep004_fisherMetric_eq_zero_iff",
        ),
        "fep-007": (
            "fep007_normalizedMessage",
            "fep007_normalizedMessage_sum_one",
        ),
        "fep-011": (
            "fep011_surprise",
            "fep011_surprise_eq_zero_iff",
            "fep011_surprise_strictAnti",
        ),
        "fep-012": (
            "fep012_policyEntropy",
            "fep012_entropyRegularizedCost_le_expectedCost",
        ),
        "fep-013": (
            "fep013_helmholtz_hasDerivAt",
            "fep013_helmholtz_derivative_eq_neg_entropy",
        ),
        "fep-015": (
            "fep015_variationalIntegrand",
            "fep015_variationalIntegrand_measurable",
        ),
        "fep-016": (
            "fep016_laplaceKernel",
            "fep016_laplaceKernel_integrable",
            "fep016_laplaceKernel_integral",
        ),
        "fep-026": (
            "fep026_priorComplexity",
            "fep026_priorComplexity_eq_zero_iff",
        ),
        "fep-028": (
            "fep028_softmax_support",
            "fep028_softmax_sum_univ",
        ),
        "fep-032": (
            "fep032_quadraticUpdate_iterate",
            "fep032_quadraticUpdate_tendsto",
        ),
        "fep-039": (
            "fep039_global_eq_zero_iff",
            "fep039_global_add",
        ),
        "fep-046": (
            "fep046_stickWeights",
            "fep046_mass_conservation",
        ),
        "fep-047": (
            "Matrix.mulVec",
            "fep047_forward_compose",
        ),
    }
    for topic_id, declarations in expected.items():
        for declaration in declarations:
            assert declaration in BODIES[topic_id]

    audit = load_theorem_maturity(PROJECT_ROOT / "config" / "theorem_maturity.yaml")
    expected_below_formalized = {
        "fep-052": SemanticDisposition.CONDITIONAL_PROXY,
        "fep-054": SemanticDisposition.CONDITIONAL_PROXY,
        "fep-055": SemanticDisposition.CONDITIONAL_PROXY,
        "fep-063": SemanticDisposition.CONDITIONAL_PROXY,
        "fep-064": SemanticDisposition.STRUCTURAL_PROXY,
        "fep-067": SemanticDisposition.STRUCTURAL_PROXY,
        "fep-069": SemanticDisposition.STRUCTURAL_PROXY,
        "fep-070": SemanticDisposition.STRUCTURAL_PROXY,
        "fep-071": SemanticDisposition.CONDITIONAL_PROXY,
        "fep-079": SemanticDisposition.CONDITIONAL_PROXY,
        "fep-081": SemanticDisposition.STRUCTURAL_PROXY,
        "fep-083": SemanticDisposition.CONDITIONAL_PROXY,
        "fep-085": SemanticDisposition.CONDITIONAL_PROXY,
        "fep-094": SemanticDisposition.STRUCTURAL_PROXY,
        "fep-095": SemanticDisposition.CONDITIONAL_PROXY,
        "fep-097": SemanticDisposition.CONDITIONAL_PROXY,
        "fep-100": SemanticDisposition.CONDITIONAL_PROXY,
        "fep-105": SemanticDisposition.CONDITIONAL_PROXY,
        "fep-106": SemanticDisposition.CONDITIONAL_PROXY,
    }
    assert {
        row.id: row.disposition
        for row in audit.records
        if row.disposition is not SemanticDisposition.FORMALIZED
    } == expected_below_formalized


@pytest.mark.serial_lean
def test_native_landauer_path_protocol_controls(tmp_path: Path) -> None:
    fixture = PROJECT_ROOT / "tests/fixtures/landauer_path_controls.lean"
    probe = tmp_path / "LandauerPathControls.lean"
    probe.write_bytes(fixture.read_bytes())
    result = run_lean_compile_probe(
        probe,
        cwd=PROJECT_ROOT / "lean",
        import_root=tmp_path,
        output_path=tmp_path / "LandauerPathControls.olean",
        timeout_s=300,
        executable=lake_executable(
            missing="raise", context="finite-path Landauer controls"
        ),
    )
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "warning:" not in output.lower(), output
    names = tuple(
        "fep_fep050.FEP050." + name
        for name in (
            "fep050_generalized_landauer_heat_bound",
            "fep050_landauer_heat_bound",
            "fep050_landauer_work_bound",
        )
    ) + tuple(
        "FEP050Controls." + name
        for name in (
            "heat_encoding",
            "fair_catalogue_bound",
            "fair_reversible_equality",
            "biased_catalogue_bound",
            "biased_strict_control",
            "fair_work_control",
        )
    )
    axioms, errors = parse_axiom_output(output, expected=names)
    assert not errors, errors
    assert set(axioms) == set(names)
    for dependencies in axioms.values():
        assert set(dependencies) <= {"propext", "Classical.choice", "Quot.sound"}
