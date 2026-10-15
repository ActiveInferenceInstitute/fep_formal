"""Static contracts for the fep-051--092 cross-topic composition layer."""

from __future__ import annotations

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
COMPOSITIONS_ROOT = PROJECT_ROOT / "src" / "fep_lean" / "formal" / "compositions"

BRIDGES = {
    51: (
        "measure_variational.lean",
        "fep051_rn_reconstruction_refines_fep017",
        "fep_fep051.FEP051.fep051_likelihoodRatio_reconstruction",
        "fep_fep017.FEP017.fep017_posterior_joint_reconstruction",
    ),
    52: (
        "measure_variational.lean",
        "fep052_posterior_tilt_is_fep017_posterior",
        "fep_fep052.FEP052.fep052_countable_posterior_density_tilt",
        "fep_fep017.FEP017.fep017_posterior_bayes_density",
    ),
    53: (
        "measure_variational.lean",
        "fep053_joint_reconstruction_extends_fep017",
        "fep_fep053.FEP053.fep053_kernelBayes_joint_reconstruction",
        "fep_fep017.FEP017.fep017_posterior_joint_reconstruction",
    ),
    54: (
        "measure_variational.lean",
        "fep054_involution_of_fep017_posterior",
        "fep_fep054.FEP054.fep054_bayes_involution",
        "fep_fep017.FEP017.fep017_posterior_recovers_prior",
    ),
    55: (
        "measure_variational.lean",
        "fep055_composite_inversion_uses_fep019",
        "fep_fep055.FEP055.fep055_compositeKernel_bayesInversion",
        "fep_fep019.FEP019.fep019_priorPredictive_assoc",
    ),
    56: (
        "measure_variational.lean",
        "fep056_disintegration_supplies_fep017",
        "fep_fep056.FEP056.fep056_standardBorel_condKernel_reconstruction",
        "fep_fep017.FEP017.fep017_posterior_joint_reconstruction",
    ),
    57: (
        "measure_variational.lean",
        "fep057_tower_integrates_fep015",
        "fep_fep057.FEP057.fep057_conditionalExpectation_tower",
        "fep_fep015.FEP015.fep015_variationalIntegrand_measurable",
    ),
    58: (
        "measure_variational.lean",
        "fep058_gibbs_gap_is_fep001_kl",
        "fep_fep058.FEP058.fep058_gibbsVariational_lower_bound",
        "fep_fep001.FEP001.fep001_variationalUpperBound_ge",
    ),
    59: (
        "measure_variational.lean",
        "fep059_dv_equality_is_fep001_exactness",
        "fep_fep059.FEP059.fep059_donskerVaradhan_equality_iff",
        "fep_fep001.FEP001.fep001_variationalGap_eq_zero_iff",
    ),
    60: (
        "measure_variational.lean",
        "fep060_coordinate_elbo_refines_fep002",
        "fep_fep060.FEP060.fep060_coordinateELBO_decomposition",
        "fep_fep002.FEP002.fep002_elbo_bound",
    ),
    61: (
        "measure_variational.lean",
        "fep061_meanField_gap_is_fep014_kl",
        "fep_fep061.FEP061.fep061_meanFieldCoordinate_optimum_iff",
        "fep_fep014.FEP014.fep014_kl_eq_zero_iff",
    ),
    62: (
        "measure_variational.lean",
        "fep062_iwae_jensen_uses_fep035",
        "fep_fep062.FEP062.fep062_fixedSample_importanceJensen",
        "fep_fep035.FEP035.fep035_log_jensen_two_strict",
    ),
    63: (
        "measure_variational.lean",
        "fep063_channel_dpi_bounds_fep014",
        "fep_fep063.FEP063.fep063_finiteChannel_klDataProcessing",
        "fep_fep014.FEP014.fep014_kl_nonneg",
    ),
    64: (
        "measure_variational.lean",
        "fep064_rateDistortion_uses_fep041_mutualInformation",
        "fep_fep064.FEP064.fep064_rateDistortion_weakDuality",
        "fep_fep041.FEP041.fep041_informationGain_nonneg",
    ),
    65: (
        "control_temporal.lean",
        "fep065_controlledKernel_extends_fep023_normalization",
        "fep_fep065.FEP065.fep065_controlledKernel_normalization",
        "fep_fep023.FEP023.fep023_reachable_normalized",
    ),
    66: (
        "control_temporal.lean",
        "fep066_action_update_refines_fep034_filter",
        "fep_fep066.FEP066.fep066_actionConditioned_bayes_reconstruction",
        "fep_fep034.FEP034.fep034_filter_joint_reconstruction",
    ),
    67: (
        "control_temporal.lean",
        "fep067_reachableBelief_refines_fep023",
        "fep_fep067.FEP067.fep067_reachableBelief_policyValue_equivalence",
        "fep_fep023.FEP023.fep023_policy_reachable",
    ),
    68: (
        "control_temporal.lean",
        "fep068_softBellman_extends_fep033",
        "fep_fep068.FEP068.fep068_softBellman_recursion",
        "fep_fep033.FEP033.fep033_bellman",
    ),
    69: (
        "control_temporal.lean",
        "fep069_desirability_combines_fep031_weights",
        "fep_fep069.FEP069.fep069_desirability_recursion",
        "fep_fep031.FEP031.fep031_gibbs_weight_pos",
    ),
    70: (
        "control_temporal.lean",
        "fep070_controlPosterior_refines_fep028_softmax",
        "fep_fep070.FEP070.fep070_controlPosterior_normalized",
        "fep_fep028.FEP028.fep028_softmax_probs_sum_one",
    ),
    71: (
        "control_temporal.lean",
        "fep071_sophisticatedEFE_extends_fep033",
        "fep_fep071.FEP071.fep071_sophisticatedEFE_backward_step",
        "fep_fep033.FEP033.fep033_bellman",
    ),
    72: (
        "control_temporal.lean",
        "fep072_forward_filter_refines_fep034",
        "fep_fep072.FEP072.fep072_forward_filtering_recursion",
        "fep_fep034.FEP034.fep034_filter_joint_reconstruction",
    ),
    73: (
        "control_temporal.lean",
        "fep073_backward_message_composes_fep047",
        "fep_fep073.FEP073.fep073_backward_message_recursion",
        "fep_fep047.FEP047.fep047_forward_compose",
    ),
    74: (
        "control_temporal.lean",
        "fep074_smoothing_reconstructs_fep034_filter",
        "fep_fep074.FEP074.fep074_forwardBackward_smoothing_factorization",
        "fep_fep034.FEP034.fep034_filter_joint_reconstruction",
    ),
    75: (
        "control_temporal.lean",
        "fep075_smoothing_normalization_extends_fep034",
        "fep_fep075.FEP075.fep075_smoothing_marginal_normalization",
        "fep_fep034.FEP034.fep034_filter_mass_one",
    ),
    76: (
        "control_temporal.lean",
        "fep076_variational_update_refines_fep028_softmax",
        "fep_fep076.FEP076.fep076_variational_state_update_normalized",
        "fep_fep028.FEP028.fep028_softmax_probs_sum_one",
    ),
    77: (
        "control_temporal.lean",
        "fep077_hierarchical_predictive_extends_fep027",
        "fep_fep077.FEP077.fep077_hierarchical_predictive_factorization",
        "fep_fep027.FEP027.fep027_hierarchical_assoc",
    ),
    78: (
        "control_temporal.lean",
        "fep078_model_average_composes_fep019",
        "fep_fep078.FEP078.fep078_modelAverage_predictive_law",
        "fep_fep019.FEP019.fep019_priorPredictive_assoc",
    ),
    79: (
        "causal_predictive.lean",
        "fep079_blanket_cmi_refines_fep009",
        "fep_fep079.FEP079.fep079_blanketFactorization_iff_conditionalMutualInformation_zero",
        "fep_fep009.FEP009.fep009_joint_product_nonneg",
    ),
    80: (
        "causal_predictive.lean",
        "fep080_shared_mixture_preserves_fep019_prediction",
        "fep_fep080.FEP080.fep080_sharedConditional_mixture_preservation",
        "fep_fep019.FEP019.fep019_priorPredictive_assoc",
    ),
    81: (
        "causal_predictive.lean",
        "fep081_coupled_blanket_composes_fep009",
        "fep_fep081.FEP081.fep081_coupledSubsystem_blanketComposition",
        "fep_fep009.FEP009.fep009_joint_product_nonneg",
    ),
    82: (
        "causal_predictive.lean",
        "fep082_intervention_normalization_extends_fep023",
        "fep_fep082.FEP082.fep082_interventionKernel_normalization",
        "fep_fep023.FEP023.fep023_reachable_normalized",
    ),
    83: (
        "causal_predictive.lean",
        "fep083_intervention_invariance_refines_fep009",
        "fep_fep083.FEP083.fep083_nonDescendant_intervention_invariance",
        "fep_fep009.FEP009.fep009_likelihood_mono",
    ),
    84: (
        "causal_predictive.lean",
        "fep084_ordered_factorization_extends_fep027",
        "fep_fep084.FEP084.fep084_orderedFiniteCausal_factorization",
        "fep_fep027.FEP027.fep027_hierarchical_assoc",
    ),
    85: (
        "causal_predictive.lean",
        "fep085_local_markov_refines_fep009",
        "fep_fep085.FEP085.fep085_localMarkov_mutualInformation_zero",
        "fep_fep009.FEP009.fep009_condIndep_bot_right",
    ),
    86: (
        "causal_predictive.lean",
        "fep086_precision_energy_refines_fep016",
        "fep_fep086.FEP086.fep086_precisionWeighted_predictionError_nonnegative",
        "fep_fep016.FEP016.fep016_precision_weighted",
    ),
    87: (
        "causal_predictive.lean",
        "fep087_hierarchical_energy_extends_fep039",
        "fep_fep087.FEP087.fep087_hierarchicalPredictiveCoding_decomposition",
        "fep_fep039.FEP039.fep039_global_add",
    ),
    88: (
        "causal_predictive.lean",
        "fep088_prediction_gradient_extends_fep043",
        "fep_fep088.FEP088.fep088_predictionError_gradient_identity",
        "fep_fep043.FEP043.fep043_quadratic_hasDerivAt",
    ),
    89: (
        "causal_predictive.lean",
        "fep089_finite_jet_shift_specializes_fep006",
        "fep_fep089.FEP089.fep089_finiteJet_shift_semigroup",
        "fep_fep006.FEP006.fep006_iterateFlow_add",
    ),
    90: (
        "causal_predictive.lean",
        "fep090_generalized_correction_combines_fep043",
        "fep_fep090.FEP090.fep090_finiteJet_generalizedFiltering_correctionEquation",
        "fep_fep043.FEP043.fep043_quadratic_hasDerivAt",
    ),
    91: (
        "causal_predictive.lean",
        "fep091_precision_modulation_refines_fep016",
        "fep_fep091.FEP091.fep091_precisionModulation_energy_mono",
        "fep_fep016.FEP016.fep016_precision_weighted",
    ),
    92: (
        "causal_predictive.lean",
        "fep092_quadratic_convergence_specializes_fep032",
        "fep_fep092.FEP092.fep092_quadraticPredictiveCoding_error_tendsto_zero",
        "fep_fep032.FEP032.fep032_quadraticUpdate_tendsto",
    ),
    93: (
        "thermo_geometry.lean",
        "fep093_path_ratio_extends_fep010_reversal",
        "fep_fep093.FEP093.fep093_forward_reverse_pathLaw_ratio",
        "fep_fep010.FEP010.fep010_identity_reversible",
    ),
    94: (
        "thermo_geometry.lean",
        "fep094_path_kl_refines_fep049_entropy_production",
        "fep_fep094.FEP094.fep094_entropyProduction_as_pathKL",
        "fep_fep049.FEP049.fep049_entropyProduction_nonneg",
    ),
    95: (
        "thermo_geometry.lean",
        "fep095_fluctuation_symmetry_extends_fep010_reversibility",
        "fep_fep095.FEP095.fep095_detailedFluctuation_symmetry",
        "fep_fep010.FEP010.fep010_reversible_invariant",
    ),
    96: (
        "thermo_geometry.lean",
        "fep096_integral_fluctuation_refines_fep049",
        "fep_fep096.FEP096.fep096_integralFluctuation_theorem",
        "fep_fep049.FEP049.fep049_flux_force_identity",
    ),
    97: (
        "thermo_geometry.lean",
        "fep097_jarzynski_extends_fep013_helmholtz",
        "fep_fep097.FEP097.fep097_finiteJarzynski_equality",
        "fep_fep013.FEP013.fep013_delta_F",
    ),
    98: (
        "thermo_geometry.lean",
        "fep098_local_current_refines_fep025",
        "fep_fep098.FEP098.fep098_localDetailedBalance_currentCancellation",
        "fep_fep025.FEP025.fep025_probabilityCurrent_antisymm",
    ),
    99: (
        "thermo_geometry.lean",
        "fep099_reversible_kl_dissipation_links_fep010_fep014",
        "fep_fep099.FEP099.fep099_reversibleChain_oneStep_KL_dissipation",
        "fep_fep014.FEP014.fep014_kl_nonneg",
    ),
    100: (
        "thermo_geometry.lean",
        "fep100_categorical_fisher_refines_fep004",
        "fep_fep100.FEP100.fep100_categoricalFisher_simplexTangent_positivity",
        "fep_fep004.FEP004.fep004_fisherMetric_nonneg",
    ),
    101: (
        "thermo_geometry.lean",
        "fep101_fisher_pullback_extends_fep038",
        "fep_fep101.FEP101.fep101_fisherPullback_reparameterization",
        "fep_fep038.FEP038.fep038_fisherMetric_pullback",
    ),
    102: (
        "thermo_geometry.lean",
        "fep102_cramer_rao_uses_fep038_score_geometry",
        "fep_fep102.FEP102.fep102_unbiasedScalar_cramerRao",
        "fep_fep038.FEP038.fep038_expectedScore_zero",
    ),
    103: (
        "thermo_geometry.lean",
        "fep103_natural_gradient_extends_fep038",
        "fep_fep103.FEP103.fep103_naturalGradient_equivariance",
        "fep_fep038.FEP038.fep038_naturalGradient_duality",
    ),
    104: (
        "thermo_geometry.lean",
        "fep104_mirror_descent_refines_fep024",
        "fep_fep104.FEP104.fep104_mirrorDescent_threePoint_identity",
        "fep_fep024.FEP024.fep024_klRegularizedObjective_ge",
    ),
    105: (
        "thermo_geometry.lean",
        "fep105_bregman_projection_extends_fep044",
        "fep_fep105.FEP105.fep105_affineProjection_bregmanPythagorean",
        "fep_fep044.FEP044.fep044_hellingerSq_nonneg",
    ),
    106: (
        "thermo_geometry.lean",
        "fep106_replicator_links_fep028_fep038",
        "fep_fep106.FEP106.fep106_replicator_naturalGradient_equivalence",
        "fep_fep038.FEP038.fep038_naturalGradient_duality",
    ),
    107: (
        "collective_learning.lean",
        "fep107_product_agent_extends_fep027_hierarchy",
        "fep_fep107.FEP107.fep107_productAgent_generative_mass",
        "fep_fep027.FEP027.fep027_hierarchical_mass_one",
    ),
    108: (
        "collective_learning.lean",
        "fep108_collective_vfe_extends_fep039_additivity",
        "fep_fep108.FEP108.fep108_collectiveVFE_additive",
        "fep_fep039.FEP039.fep039_global_add",
    ),
    109: (
        "collective_learning.lean",
        "fep109_independent_efe_extends_fep021",
        "fep_fep109.FEP109.fep109_independentEFE_additive",
        "fep_fep021.FEP021.fep021_efe_epistemic_balance",
    ),
    110: (
        "collective_learning.lean",
        "fep110_product_of_experts_refines_fep028_normalization",
        "fep_fep110.FEP110.fep110_unitWeightProductOfExpertsPool_normalized",
        "fep_fep028.FEP028.fep028_softmax_probs_sum_one",
    ),
    111: (
        "collective_learning.lean",
        "fep111_consensus_mass_extends_fep025_conservation",
        "fep_fep111.FEP111.fep111_consensus_pointwise_mass_conserved",
        "fep_fep025.FEP025.fep025_total_divergence_zero",
    ),
    112: (
        "collective_learning.lean",
        "fep112_consensus_convergence_extends_fep048_contraction",
        "fep_fep112.FEP112.fep112_consensus_converges",
        "fep_fep048.FEP048.fep048_halfUpdate_iterates_converge",
    ),
    113: (
        "collective_learning.lean",
        "fep113_coupled_potential_refines_fep032_descent",
        "fep_fep113.FEP113.fep113_coupledPotential_strict_descent",
        "fep_fep032.FEP032.fep032_quadraticEnergy_descent",
    ),
    114: (
        "collective_learning.lean",
        "fep114_subgaussian_tail_refines_fep036_empirical_rate",
        "fep_fep114.FEP114.fep114_subGaussian_empiricalMean_tail",
        "fep_fep036.FEP036.fep036_smoothedRate_pos",
    ),
    115: (
        "collective_learning.lean",
        "fep115_frequency_union_bound_extends_fep042_counts",
        "fep_fep115.FEP115.fep115_simultaneous_frequency_bound",
        "fep_fep042.FEP042.fep042_likelihood_factorizes",
    ),
    116: (
        "collective_learning.lean",
        "fep116_pac_bayes_refines_fep001_variational_bound",
        "fep_fep116.FEP116.fep116_finitePACBayes_with_confidence",
        "fep_fep001.FEP001.fep001_variationalUpperBound_ge",
    ),
    117: (
        "collective_learning.lean",
        "fep117_posterior_odds_extends_fep017_bayes",
        "fep_fep117.FEP117.fep117_posteriorOdds_recursion",
        "fep_fep017.FEP017.fep017_posterior_joint_reconstruction",
    ),
    118: (
        "collective_learning.lean",
        "fep118_posterior_concentration_extends_fep045_update",
        "fep_fep118.FEP118.fep118_posteriorGap_concentration",
        "fep_fep045.FEP045.fep045_posterior_mass_one",
    ),
    119: (
        "collective_learning.lean",
        "fep119_mixture_log_loss_refines_fep026_complexity",
        "fep_fep119.FEP119.fep119_mixtureLogLoss_regret",
        "fep_fep026.FEP026.fep026_complexity_additive",
    ),
    120: (
        "collective_learning.lean",
        "fep120_bayes_factor_update_extends_fep019_prediction",
        "fep_fep120.FEP120.fep120_bayesFactor_multiplicative_update",
        "fep_fep019.FEP019.fep019_priorPredictive_assoc",
    ),
}

DECLARATION_RE = re.compile(
    r"(?m)^(?:theorem|def|abbrev|structure|class|instance|axiom|opaque)\s+"
    r"([A-Za-z][A-Za-z0-9_]*)"
)
THEOREM_RE = re.compile(r"(?m)^theorem\s+(fep\d{3}_[A-Za-z0-9_]+)")


def _sources() -> dict[str, str]:
    return {
        filename: (COMPOSITIONS_ROOT / filename).read_text(encoding="utf-8")
        for filename in sorted({bridge[0] for bridge in BRIDGES.values()})
    }


def _theorem_block(source: str, theorem_name: str) -> str:
    start_match = re.search(rf"(?m)^theorem {re.escape(theorem_name)}\b", source)
    assert start_match is not None, theorem_name
    next_match = re.search(r"(?m)^theorem\s+", source[start_match.end() :])
    end = len(source) if next_match is None else start_match.end() + next_match.start()
    return source[start_match.start() : end]


def test_expansion_compositions_pin_exact_ids_names_and_file_ownership() -> None:
    assert tuple(BRIDGES) == tuple(range(51, 121))
    sources = _sources()
    assert tuple(sources) == (
        "causal_predictive.lean",
        "collective_learning.lean",
        "control_temporal.lean",
        "measure_variational.lean",
        "thermo_geometry.lean",
    )

    actual = {
        int(name[3:6]): (filename, name)
        for filename, source in sources.items()
        for name in THEOREM_RE.findall(source)
    }
    expected = {
        topic_id: (filename, theorem_name)
        for topic_id, (filename, theorem_name, _, _) in BRIDGES.items()
    }
    assert actual == expected
    assert sum(len(THEOREM_RE.findall(source)) for source in sources.values()) == 70


def test_every_bridge_consumes_endpoint_and_pre051_declarations() -> None:
    sources = _sources()
    for topic_id, (filename, theorem_name, endpoint, prior) in BRIDGES.items():
        block = _theorem_block(sources[filename], theorem_name)
        assert endpoint in block, topic_id
        assert prior in block, topic_id
        prior_match = re.fullmatch(r"fep_fep(\d{3})\.FEP\d{3}\..+", prior)
        assert prior_match is not None
        assert int(prior_match.group(1)) < 51


def test_composition_sources_have_only_proved_topic_theorems() -> None:
    forbidden = re.compile(r"\b(?:sorry|admit)\b|:\s*True\b")
    for filename, source in _sources().items():
        assert source.startswith("module\npublic import FepSketches.fep_all\n"), (
            filename
        )
        assert "namespace FEPComposed\n" in source
        assert source.rstrip().endswith("end FEPComposed")
        assert forbidden.search(source) is None
        declarations = DECLARATION_RE.findall(source)
        assert declarations == THEOREM_RE.findall(source)
