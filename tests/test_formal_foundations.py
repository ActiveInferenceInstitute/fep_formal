"""The maintained FEP/active-inference kernel stays deep, explicit, and closed."""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from fep_lean.catalogue.coverage import build_formalism_coverage
from fep_lean.catalogue.relations import load_formalism_graph
from fep_lean.formal.declarations import formal_theorem_modules
from fep_lean.formal.manifest import (
    FORMAL_MODULES,
    FormalModuleRole,
    formal_resource_paths,
)
from fep_lean.lean_source import lean_code_without_comments

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_formal_kernel_has_exact_manifested_declaration_closure() -> None:
    owners = formal_theorem_modules(PROJECT_ROOT)
    # Eight existing support proofs are exported for exposed module definitions.
    # Pin their identities as well as the per-owner declaration counts below.
    exposed_support = {
        "FEP.LinearGaussianSemigroup.LinearGaussianParameters.finOneState_measurable": "FepSketches.linear_gaussian_semigroup",
        "FEP.ScalarGaussianSemigroup.ScalarOUParameters.stationaryVariance_pos": "FepSketches.scalar_gaussian_semigroup",
        "FEP.PosteriorConvergence.observation_stronglyMeasurable": "FepSketches.posterior_convergence",
        "FEP.ContinuousTimeMarkov.boolBlanketRefreshTime_pos": "FepSketches.continuous_time_markov",
        "FEP.FinitePosteriorLearning.nonidentifiablePredictive_pos": "FepSketches.finite_posterior_learning",
        "FEPComposed.FiniteScientificImplications.scaledLogisticProbability_lt_one": "FepSketches.compositions.finite_scientific_implications",
        "FEPComposed.FiniteScientificImplications.scaledLogisticProbability_pos": "FepSketches.compositions.finite_scientific_implications",
        "FEPComposed.FiniteScientificImplications.symmetricFalseEvidence": "FepSketches.compositions.finite_scientific_implications",
    }
    assert {name: owners[name] for name in exposed_support} == exposed_support
    native_entropy_support = {
        "FEP.VariationalDuality.nativeKL_tilted_gap": "FepSketches.variational_duality",
        "FEP.VariationalDuality.nativeEntropy_le_klDiv": "FepSketches.variational_duality",
        "FEP.VariationalDuality.nativeCgf_le_klDiv": "FepSketches.variational_duality",
    }
    assert {
        name: owners[name] for name in native_entropy_support
    } == native_entropy_support
    modules_by_role = {
        role: tuple(module for module in FORMAL_MODULES if module.role is role)
        for role in FormalModuleRole
    }
    manifested_resources = tuple(module.resource for module in FORMAL_MODULES)
    actual_resources = tuple(
        sorted(
            path.relative_to(PROJECT_ROOT / "src" / "fep_lean" / "formal").as_posix()
            for path in (PROJECT_ROOT / "src" / "fep_lean" / "formal").rglob("*.lean")
        )
    )
    resolved_resources = tuple(
        path.relative_to(PROJECT_ROOT / "src" / "fep_lean" / "formal").as_posix()
        for path in formal_resource_paths(project_root=PROJECT_ROOT)
    )

    assert manifested_resources == resolved_resources
    assert set(manifested_resources) == set(actual_resources)
    assert all(modules_by_role.values())
    assert tuple(
        module.lean_module for module in modules_by_role[FormalModuleRole.AGGREGATE]
    ) == ("FepSketches.composed",)
    # Preserve the original per-owner inventory after excluding only the seven
    # independently reviewed scalar bridges; unrelated additions still fail.
    scalar_bridges = {
        "FEPComposed.fep031_energyGibbs_is_topicProbability",
        "FEPComposed.fep030_fep031_finite_maxEntropy",
        "FEPComposed.fep030_fin2_entropy_eq_binEntropy",
        "FEPComposed.fep030_finite_binary_entropy_bound",
        "FEPComposed.fep030_fep031_binary_maxEntropy",
        "FEPComposed.fep018_coordinate_derivative_is_fep038",
        "FEPComposed.fep018_fep038_actual_metric_pullback",
    }
    assert {name: owners[name] for name in scalar_bridges} == {
        name: "FepSketches.compositions.core" for name in scalar_bridges
    }
    assert Counter(
        owner for name, owner in owners.items() if name not in scalar_bridges
    ) == {
        "FepSketches.finite_probability": 19,
        "FepSketches.finite_information": 31,
        "FepSketches.active_inference": 44,
        "FepSketches.gnn_denotation": 7,
        "FepSketches.gnn_denotation_continuous": 9,
        "FepSketches.gnn_render_statements": 7,
        "FepSketches.markov_blanket": 9,
        "FepSketches.information_geometry": 33,
        "FepSketches.statistical_convergence": 7,
        "FepSketches.measure_bayes": 12,
        "FepSketches.variational_duality": 85,
        "FepSketches.controlled_markov": 33,
        "FepSketches.temporal_inference": 52,
        "FepSketches.finite_markov_dynamics": 17,
        "FepSketches.causal_dynamics": 34,
        "FepSketches.predictive_coding": 47,
        "FepSketches.ness_flow": 25,
        "FepSketches.path_thermodynamics": 81,
        "FepSketches.geometric_optimization": 25,
        "FepSketches.collective_inference": 41,
        "FepSketches.learning_theory": 12,
        "FepSketches.empirical_risk": 38,
        "FepSketches.policy_tree": 13,
        "FepSketches.native_blanket": 26,
        "FepSketches.exponential_family": 23,
        "FepSketches.gaussian_information_geometry": 31,
        "FepSketches.smooth_information_geometry": 16,
        "FepSketches.continuous_time_markov": 98,
        "FepSketches.markov_semigroup": 10,
        "FepSketches.scalar_gaussian_semigroup": 16,
        "FepSketches.linear_gaussian_semigroup": 26,
        "FepSketches.fin4_gaussian_semigroup": 42,
        "FepSketches.gaussian_precision_conditioning": 25,
        "FepSketches.decision_risk": 25,
        "FepSketches.finite_posterior_learning": 14,
        "FepSketches.posterior_convergence": 27,
        "FepSketches.compositions.core": 26,
        "FepSketches.compositions.measure_variational": 14,
        "FepSketches.compositions.control_temporal": 14,
        "FepSketches.compositions.causal_predictive": 14,
        "FepSketches.compositions.thermo_geometry": 15,
        "FepSketches.compositions.collective_learning": 14,
        "FepSketches.compositions.risk_calibration": 7,
        "FepSketches.compositions.policy_trees": 7,
        "FepSketches.compositions.native_blanket_transfer": 20,
        "FepSketches.compositions.exponential_family": 7,
        "FepSketches.compositions.continuous_time": 7,
        "FepSketches.compositions.finite_scientific_implications": 9,
        "FepSketches.compositions.finite_policy_action": 12,
        "FepSketches.compositions.finite_reference_agent": 5,
        "FepSketches.compositions.gaussian_filter": 16,
        "FepSketches.compositions.gaussian_control": 19,
        "FepSketches.compositions.gaussian_grid_path": 11,
        "FepSketches.compositions.smooth_reference_kernel": 30,
        "FepSketches.compositions.finite_kernel_category": 8,
        "FepSketches.efe_policy_selection": 25,
        "FepSketches.perception_action_loop": 40,
        "FepSketches.bayesian_model_reduction": 10,
        "FepSketches.efe_time_scale_separation": 37,
        "FepSketches.compositions.efe_policy_selection": 1,
        "FepSketches.compositions.perception_action_loop": 1,
        "FepSketches.compositions.bayesian_model_reduction": 1,
        "FepSketches.compositions.efe_time_scale_separation": 1,
        "FepSketches.helmholtz_ao_ness": 22,
        "FepSketches.geometric_mechanics": 37,
        "FepSketches.compositions.helmholtz_ao_ness": 2,
        "FepSketches.compositions.geometric_mechanics": 7,
        "FepSketches.law_weighted_split": 7,
        "FepSketches.h3_reference_model": 53,
        "FepSketches.compositions.h3_case_study": 93,
    }


def test_foundations_pin_the_claims_that_make_the_kernel_substantive() -> None:
    owners = formal_theorem_modules(PROJECT_ROOT)
    expected = {
        "FEP.StatisticalConvergence.sum_indicator_eq_successCount": (
            "FepSketches.statistical_convergence"
        ),
        "FEP.FiniteKernel.comp_assoc": "FepSketches.finite_probability",
        "FEP.FiniteKernel.predictive_comp": "FepSketches.finite_probability",
        "FEP.FiniteInformation.finiteKL_eq_zero_iff": (
            "FepSketches.finite_information"
        ),
        "FEP.FiniteInformation.mutualInformation_product_eq_zero": (
            "FepSketches.finite_information"
        ),
        "FEP.FiniteInformation.finiteKL_joint_chain_rule": (
            "FepSketches.finite_information"
        ),
        "FEP.FiniteInformation.finiteKL_disjoint_pointMass_totalized": (
            "FepSketches.finite_information"
        ),
        "FEP.ActiveInference.variationalFreeEnergy_eq_surprisal_iff": (
            "FepSketches.active_inference"
        ),
        "FEP.ActiveInference.expectedFreeEnergy_eq_risk_add_ambiguity": (
            "FepSketches.active_inference"
        ),
        "FEP.ActiveInference.rolloutKernel_append": ("FepSketches.active_inference"),
        "FEP.ActiveInference.cumulativeExpectedFreeEnergyFrom_append": (
            "FepSketches.active_inference"
        ),
        "FEP.ActiveInference.inferSelectActJoint_factorization": (
            "FepSketches.active_inference"
        ),
        "FEP.ActiveInference.inferSelectActActionMarginal_eq_actionLaw": (
            "FepSketches.active_inference"
        ),
        "FEP.ActiveInference.not_fullSupport_of_preference_eq_zero": (
            "FepSketches.active_inference"
        ),
        "FEP.ActiveInference.symmetricBoolModel_expectedFreeEnergy": (
            "FepSketches.active_inference"
        ),
        "FEP.ActiveInference.symmetricBoolModel_policyPrior_changes_posterior": (
            "FepSketches.active_inference"
        ),
        "FEP.MarkovBlanket.conditional_mutualInformation_zero": (
            "FepSketches.markov_blanket"
        ),
        "FEP.MarkovBlanket.transition_factorization": ("FepSketches.markov_blanket"),
        "FEP.MarkovBlanket.transition_row_conditional_factorization": (
            "FepSketches.markov_blanket"
        ),
        "FEP.InformationGeometry.naturalGradient_unique": (
            "FepSketches.information_geometry"
        ),
        "FEP.InformationGeometry.naturalGradient_metric_duality": (
            "FepSketches.information_geometry"
        ),
        "FEP.InformationGeometry.pullbackMetric_pos": (
            "FepSketches.information_geometry"
        ),
        "FEP.InformationGeometry.duplicatedScore_fisherMetric_eq_zero": (
            "FepSketches.information_geometry"
        ),
        "FEP.StatisticalConvergence.empiricalL1Error_strongLaw": (
            "FepSketches.statistical_convergence"
        ),
        "FEP.StatisticalConvergence.empiricalExpectation_strongLaw": (
            "FepSketches.statistical_convergence"
        ),
        "FEP.MeasureBayes.likelihoodRatio_reconstruction_iff": (
            "FepSketches.measure_bayes"
        ),
        "FEP.MeasureBayes.conditionalKernel_reconstruction": (
            "FepSketches.measure_bayes"
        ),
        "FEP.VariationalDuality.dvObjective_optimizer": (
            "FepSketches.variational_duality"
        ),
        "FEP.VariationalDuality.finiteChannel_dataProcessing": (
            "FepSketches.variational_duality"
        ),
        "FEP.ControlledMarkov.softBellmanValue_succ": ("FepSketches.controlled_markov"),
        "FEP.ControlledMarkov.softBellmanValue_partition_pos": (
            "FepSketches.controlled_markov"
        ),
        "FEP.ControlledMarkov.softBellmanValue_le_actionEnergy": (
            "FepSketches.controlled_markov"
        ),
        "FEP.ControlledMarkov.twoStageFeedback_beats_openLoop": (
            "FepSketches.controlled_markov"
        ),
        "FEP.TemporalInference.forward_backward_evidence_agree": (
            "FepSketches.temporal_inference"
        ),
        "FEP.FiniteMarkovDynamics.hasDobrushinBound_comp": (
            "FepSketches.finite_markov_dynamics"
        ),
        "FEP.CausalDynamics.nonDescendant_intervention_invariant": (
            "FepSketches.causal_dynamics"
        ),
        "FEP.PredictiveCoding.generalizedFilteringStep_equation": (
            "FepSketches.predictive_coding"
        ),
        "FEP.PathThermodynamics.integralFluctuation_eq_one": (
            "FepSketches.path_thermodynamics"
        ),
        "FEP.GeometricOptimization.scalarCramerRao": (
            "FepSketches.geometric_optimization"
        ),
        "FEP.GeometricOptimization.twoCategorical_simplexMetric_fullRank": (
            "FepSketches.geometric_optimization"
        ),
        "FEP.GeometricOptimization.twoCategorical_nonzeroTangent_metric": (
            "FepSketches.geometric_optimization"
        ),
        "FEP.GeometricOptimization.twoCategorical_replicator_nonzero_witness": (
            "FepSketches.geometric_optimization"
        ),
        "FEP.CollectiveInference.consensus_gap_tendsto_zero": (
            "FepSketches.collective_inference"
        ),
        "FEP.LearningTheory.finitePACBayes_changeOfMeasure_with_confidence": (
            "FepSketches.learning_theory"
        ),
        "FEP.EmpiricalRisk.laplaceBrierRisk_le": "FepSketches.empirical_risk",
        "FEP.EmpiricalRisk.laplaceBias_nonzero_witness": ("FepSketches.empirical_risk"),
        "FEP.PolicyTrees.exists_optimalPolicyTree": "FepSketches.policy_tree",
        "FEP.PolicyTrees.boolFeedbackTree_strictlyBetter": ("FepSketches.policy_tree"),
        "FEP.NativeBlanket.staticJoint_condIndepFun": ("FepSketches.native_blanket"),
        "FEP.NativeBlanket.correlatedBlanket_nonvacuous": (
            "FepSketches.native_blanket"
        ),
        "FEP.ExponentialFamily.ScalarExponentialFamily.finiteKL_eq_logPartitionBregman": (
            "FepSketches.exponential_family"
        ),
        "FEP.ExponentialFamily.ScalarExponentialFamily.threeState_variance_zero_pos": (
            "FepSketches.exponential_family"
        ),
        "FEP.ContinuousTimeMarkov.TwoStateRates.transition_masterEquation": (
            "FepSketches.continuous_time_markov"
        ),
        "FEP.ContinuousTimeMarkov.TwoStateRates.benchmarkLyapunov_deriv_zero_neg": (
            "FepSketches.continuous_time_markov"
        ),
        "FEPComposed.activeInference_expectedFreeEnergy_to_fep021": (
            "FepSketches.compositions.core"
        ),
        "FEPComposed.fep036_smoothedRate_strongLaw": ("FepSketches.compositions.core"),
        "FEPComposed.fep126_laplaceBrierRisk_combines_fep022_fep036": (
            "FepSketches.compositions.risk_calibration"
        ),
        "FEPComposed.fep134_feedbackWitness_extends_fep071": (
            "FepSketches.compositions.policy_trees"
        ),
        "FEPComposed.fep139_nativeCondIndep_connects_fep009_fep079": (
            "FepSketches.compositions.native_blanket_transfer"
        ),
        "FEPComposed.fep147_KLBregman_connects_fep014_fep104": (
            "FepSketches.compositions.exponential_family"
        ),
        "FEPComposed.fep155_lyapunovDecay_extends_fep032": (
            "FepSketches.compositions.continuous_time"
        ),
    }
    assert {name: owners.get(name) for name in expected} == expected


def test_formal_resources_contain_no_proof_placeholders() -> None:
    placeholder = re.compile(r"\b(?:sorry|admit)\b")
    for path in formal_resource_paths(project_root=PROJECT_ROOT):
        body = lean_code_without_comments(path.read_text(encoding="utf-8"))
        assert placeholder.search(body) is None, path.name
        assert "set_option autoImplicit false" not in body or "theorem" in body


def test_foundation_modules_do_not_import_the_generated_topic_aggregate() -> None:
    for path in formal_resource_paths(
        FormalModuleRole.FOUNDATION, project_root=PROJECT_ROOT
    ):
        assert "import FepSketches.fep_all" not in path.read_text(encoding="utf-8")


def test_new_capabilities_are_closed_by_exact_declarations() -> None:
    graph = load_formalism_graph(PROJECT_ROOT / "config" / "formalism_relations.yaml")
    owners = formal_theorem_modules(PROJECT_ROOT)
    capability_evidence = {node.id: set(node.evidence) for node in graph.capabilities}
    expected_ids = {
        "cap-active-inference-generative-model",
        "cap-cumulative-expected-free-energy",
        "cap-evidence-lower-bound",
        "cap-expected-free-energy-decomposition",
        "cap-finite-information-theory",
        "cap-finite-kernel-algebra",
        "cap-finite-kl-chain-rules",
        "cap-finite-observable-consistency",
        "cap-markov-blanket-dynamics",
        "cap-multidimensional-information-geometry",
        "cap-open-loop-policy-rollout",
        "cap-policy-posterior-action",
        "cap-strong-law-consistency",
    }
    assert expected_ids <= capability_evidence.keys()
    for capability_id in expected_ids:
        assert capability_evidence[capability_id]
        assert capability_evidence[capability_id] <= owners.keys()


def test_formal_module_dependency_projection_is_acyclic_and_separate() -> None:
    coverage = build_formalism_coverage(PROJECT_ROOT)
    graph = load_formalism_graph(PROJECT_ROOT / "config" / "formalism_relations.yaml")
    modules = {row["lean_module"]: row for row in coverage["formal_modules"]}
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(module: str) -> None:
        assert module not in visiting, f"formal module dependency cycle at {module}"
        if module in visited:
            return
        visiting.add(module)
        for dependency in modules[module]["formal_dependencies"]:
            assert dependency in modules
            visit(dependency)
        visiting.remove(module)
        visited.add(module)

    for module in modules:
        visit(module)
    assert len(visited) == len(modules) == len(FORMAL_MODULES)
    assert coverage["metrics"]["authored_relation_edges"] == len(graph.edges)
    assert coverage["relation_counts"] == dict(
        sorted(Counter(edge.kind.value for edge in graph.edges).items())
    )
