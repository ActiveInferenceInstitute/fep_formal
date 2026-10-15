"""Integration contracts for the connected Horizon 1 formal surface."""

from __future__ import annotations

from pathlib import Path

from fep_lean.formal import (
    FORMAL_MODULES,
    FormalModuleRole,
    formal_module_imports,
    formal_projection_drift,
    formal_projection_pairs,
    formal_resource_manifest_drift,
    formal_theorem_modules,
    render_formal_aggregate,
)
from fep_lean.formal.declarations import composed_theorem_declarations

PROJECT_ROOT = Path(__file__).resolve().parents[1]

H11_DECLARATIONS = frozenset(
    {
        "factorizedProduct_invariant_under_pairedKernel",
        "rowwiseBlanket_doesNotImply_stationaryBlanket",
        "sparseCoupling_doesNotImply_condIndep",
        "stationaryBlanket_doesNotImply_freeEnergyDescent",
        "blanketPosterior_and_flowAlignment_imply_localDescent",
        "observationalBlanket_doesNotIdentify_causalBlanket",
    }
)

H11_IMPORTS = (
    "FepSketches.finite_probability",
    "FepSketches.causal_dynamics",
    "FepSketches.finite_markov_dynamics",
    "FepSketches.active_inference",
    "FepSketches.information_geometry",
)

H12_THEOREMS = frozenset(
    {
        "embeddedLaw_withDensity_ratio",
        "weightedDirac_klDiv_eq_finiteKL_of_fullSupport",
        "weightedDirac_klDiv_eq_top_of_not_absolutelyContinuous",
        "boolPointMass_klDiv_eq_top",
        "properLogScore_excessRisk_eq_finiteKL_truth_report",
        "finiteKL_asymmetric_bool",
        "mutualInformation_mono_under_observationGarbling",
        "bayesRisk_mono_under_observationGarbling",
        "boolZeroOneLoss_measurable",
        "boolPrior_zeroOneRisk",
        "revealingBoolArgminEstimator",
        "revealingBool_isBayesEstimator",
        "revealingBool_bayesRisk_eq_zero",
        "garbledBool_bayesRisk_eq_half",
        "revealingBool_bayesRisk_lt_garbled",
    }
)

H13_IMPORTS = (
    "FepSketches.learning_theory",
    "FepSketches.statistical_convergence",
    "FepSketches.native_blanket",
    "FepSketches.decision_risk",
    "Mathlib.Probability.Independence.InfinitePi",
)

H13_THEOREMS = frozenset(
    {
        "trajectoryCoordinates_iIndep",
        "trajectoryCoordinate_map",
        "centeredLogLikelihoodRatio_hasSubgaussianMGF",
        "finiteSampleBadGap_probability_le",
        "selectedLikelihood_pos",
        "selectedPredictive_pos",
        "posteriorBadMass_contraction_of_not_badGap",
        "posteriorBadMass_failure_probability_le",
        "posteriorAfter_two_true_witness",
        "posteriorAfter_zeroPrior",
        "nonidentifiablePosteriorAfter_eq_prior",
        "empiricalLogLikelihoodRatio_strongLaw",
        "posteriorBadMass_eventually_contracts",
    }
)

H14_IMPORTS = (
    "FepSketches.policy_tree",
    "FepSketches.active_inference",
    "FepSketches.controlled_markov",
    "FepSketches.decision_risk",
    "FepSketches.finite_posterior_learning",
)

H14_THEOREMS = frozenset(
    {
        "vfeGap_eq_finiteKL_recognition_posterior",
        "finiteTreeGibbsPosterior_sum_one",
        "selectedBeliefInterpret_learned_exact",
        "selectedBeliefInterpret_learned_nonDirac",
        "selectedBeliefUpdate_commutes_posteriorUpdate",
        "selectedPosteriorDecisionRisk_prefers_observation",
        "selectedPosteriorFeedback_continuation_optimal",
        "selectedPosteriorFeedback_changes_action",
        "selectedPosteriorFeedback_value",
        "selectedPosteriorOpenLoop_value",
        "selectedPosteriorFeedback_strictlyBetter",
        "boolFeedback_observation_changes_emittedAction",
    }
)


def test_first_horizon_wave_has_exact_manifest_owners() -> None:
    owners = {
        module.resource: (
            module.lean_module,
            module.role,
            module.declaration_namespace,
        )
        for module in FORMAL_MODULES
    }

    assert owners["decision_risk.lean"] == (
        "FepSketches.decision_risk",
        FormalModuleRole.FOUNDATION,
        "FEP.DecisionRisk",
    )
    assert owners["finite_posterior_learning.lean"] == (
        "FepSketches.finite_posterior_learning",
        FormalModuleRole.FOUNDATION,
        "FEP.FinitePosteriorLearning",
    )
    assert owners["compositions/finite_scientific_implications.lean"] == (
        "FepSketches.compositions.finite_scientific_implications",
        FormalModuleRole.COMPOSITION,
        "FEPComposed.FiniteScientificImplications",
    )
    assert owners["compositions/finite_policy_action.lean"] == (
        "FepSketches.compositions.finite_policy_action",
        FormalModuleRole.COMPOSITION,
        "FEPComposed.FinitePolicyAction",
    )
    assert owners["compositions/finite_reference_agent.lean"] == (
        "FepSketches.compositions.finite_reference_agent",
        FormalModuleRole.COMPOSITION,
        "FEPComposed.FiniteReferenceAgent",
    )


def test_h11_projection_and_public_aggregate_are_byte_current() -> None:
    source, projection = next(
        pair
        for module, pair in zip(
            FORMAL_MODULES,
            formal_projection_pairs(PROJECT_ROOT),
            strict=True,
        )
        if module.resource == "compositions/finite_scientific_implications.lean"
    )
    assert projection == (
        PROJECT_ROOT
        / "lean"
        / "FepSketches"
        / "compositions"
        / "finite_scientific_implications.lean"
    )
    assert projection.read_bytes() == source.read_bytes()
    assert (
        tuple(
            line.removeprefix("public import ")
            for line in source.read_text(encoding="utf-8").splitlines()
            if line.startswith("public import ")
        )
        == H11_IMPORTS
    )

    aggregate = render_formal_aggregate()
    new_import = "import FepSketches.compositions.finite_scientific_implications"
    assert aggregate.count(new_import) == 1
    for foundation in H11_IMPORTS:
        assert f"import {foundation}\n" not in aggregate
    assert (PROJECT_ROOT / "src" / "fep_lean" / "formal" / "composed.lean").read_text(
        encoding="utf-8"
    ) == aggregate


def test_h11_public_declaration_boundary_is_exact() -> None:
    prefix = "FEPComposed.FiniteScientificImplications."
    declarations = {
        declaration.removeprefix(prefix)
        for declaration in composed_theorem_declarations(PROJECT_ROOT)
        if declaration.startswith(prefix)
    }

    # Exposed support is part of the public module API, not a new implication.
    exposed_support = {
        "symmetricFalseEvidence",
        "scaledLogisticProbability_pos",
        "scaledLogisticProbability_lt_one",
    }
    assert declarations == H11_DECLARATIONS | exposed_support


def test_h12_foundation_projection_and_import_order_are_exact() -> None:
    source, projection = next(
        pair
        for module, pair in zip(
            FORMAL_MODULES,
            formal_projection_pairs(PROJECT_ROOT),
            strict=True,
        )
        if module.resource == "decision_risk.lean"
    )
    assert projection == PROJECT_ROOT / "lean" / "FepSketches" / "decision_risk.lean"
    assert projection.read_bytes() == source.read_bytes()

    imports = formal_module_imports()
    assert imports.count("FepSketches.decision_risk") == 1
    assert imports.index("FepSketches.decision_risk") < imports.index(
        "FepSketches.compositions.core"
    )
    assert imports[-1] == "FepSketches.composed"
    assert "import FepSketches.decision_risk\n" not in render_formal_aggregate()


def test_h12_public_theorem_owner_boundary_is_exact() -> None:
    prefix = "FEP.DecisionRisk."
    owners = formal_theorem_modules(PROJECT_ROOT)
    declarations = {
        declaration.removeprefix(prefix)
        for declaration, module in owners.items()
        if declaration.startswith(prefix) and module == "FepSketches.decision_risk"
    }

    relative_support_extension = {
        "embeddedLaw_withDensity_ratio_of_relativeSupport",
        "weightedDirac_klDiv_eq_finiteKL_of_relativeSupport",
        "finiteKL_mono_under_channel_of_relativeSupport",
        "predictive_relativeSupport",
        "joint_relativeSupport_productMarginals",
        "embeddedLaw_product",
        "nativeChannelMutualInformation_eq_finite",
        "channelJoint_fstMarginal",
        "embeddedJoint_klDiv_eq_mutualInformation",
        "finiteMutualInformation_mono_under_observationGarbling",
    }
    assert declarations == H12_THEOREMS | relative_support_extension


def test_h13_foundation_projection_and_import_order_are_exact() -> None:
    source, projection = next(
        pair
        for module, pair in zip(
            FORMAL_MODULES,
            formal_projection_pairs(PROJECT_ROOT),
            strict=True,
        )
        if module.resource == "finite_posterior_learning.lean"
    )
    assert projection == (
        PROJECT_ROOT / "lean" / "FepSketches" / "finite_posterior_learning.lean"
    )
    assert projection.read_bytes() == source.read_bytes()
    assert (
        tuple(
            line.removeprefix("public import ")
            for line in source.read_text(encoding="utf-8").splitlines()
            if line.startswith("public import ")
        )
        == H13_IMPORTS
    )

    imports = formal_module_imports()
    assert imports.count("FepSketches.finite_posterior_learning") == 1
    assert imports.index("FepSketches.decision_risk") < imports.index(
        "FepSketches.finite_posterior_learning"
    )
    assert imports.index("FepSketches.finite_posterior_learning") < imports.index(
        "FepSketches.compositions.core"
    )
    assert "import FepSketches.finite_posterior_learning\n" not in (
        render_formal_aggregate()
    )


def test_h13_public_theorem_owner_boundary_is_exact() -> None:
    prefix = "FEP.FinitePosteriorLearning."
    owners = formal_theorem_modules(PROJECT_ROOT)
    declarations = {
        declaration.removeprefix(prefix)
        for declaration, module in owners.items()
        if declaration.startswith(prefix)
        and module == "FepSketches.finite_posterior_learning"
    }

    # The exported posterior definition depends on this positivity proof.
    assert declarations == H13_THEOREMS | {"nonidentifiablePredictive_pos"}


def test_h14_projection_aggregate_and_import_boundary_are_exact() -> None:
    source, projection = next(
        pair
        for module, pair in zip(
            FORMAL_MODULES,
            formal_projection_pairs(PROJECT_ROOT),
            strict=True,
        )
        if module.resource == "compositions/finite_policy_action.lean"
    )
    assert projection == (
        PROJECT_ROOT
        / "lean"
        / "FepSketches"
        / "compositions"
        / "finite_policy_action.lean"
    )
    assert projection.read_bytes() == source.read_bytes()
    assert (
        tuple(
            line.removeprefix("public import ")
            for line in source.read_text(encoding="utf-8").splitlines()
            if line.startswith("public import ")
        )
        == H14_IMPORTS
    )

    aggregate = render_formal_aggregate()
    new_import = "import FepSketches.compositions.finite_policy_action"
    assert aggregate.count(new_import) == 1
    for foundation in H14_IMPORTS:
        assert f"import {foundation}\n" not in aggregate


def test_h14_public_theorem_owner_boundary_is_exact() -> None:
    prefix = "FEPComposed.FinitePolicyAction."
    declarations = {
        declaration.removeprefix(prefix)
        for declaration in composed_theorem_declarations(PROJECT_ROOT)
        if declaration.startswith(prefix)
    }

    assert declarations == H14_THEOREMS


def test_first_horizon_wave_manifest_and_workspace_have_no_drift() -> None:
    assert formal_resource_manifest_drift(PROJECT_ROOT) == ()
    assert formal_projection_drift(PROJECT_ROOT) == ()
