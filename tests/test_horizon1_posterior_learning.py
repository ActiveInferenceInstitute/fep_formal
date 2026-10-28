"""H1.3 selected-model posterior-learning source contracts."""

from __future__ import annotations

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FOUNDATION = (
    PROJECT_ROOT / "src" / "fep_formal" / "formal" / "finite_posterior_learning.lean"
)

EXACT_IMPORTS = (
    "FepSketches.learning_theory",
    "FepSketches.statistical_convergence",
    "FepSketches.native_blanket",
    "FepSketches.decision_risk",
    "Mathlib.Probability.Independence.InfinitePi",
)

PUBLIC_DECLARATIONS = (
    "Hypothesis",
    "Observation",
    "Trajectory",
    "truthHypothesis",
    "selectedLikelihood",
    "selectedPrior",
    "truthObservationLaw",
    "truthObservationMeasure",
    "trajectoryLaw",
    "trajectoryLaw_isProbabilityMeasure",
    "trajectoryCoordinates_iIndep",
    "trajectoryCoordinate_map",
    "logLikelihoodRatio",
    # Exposed numeric bounds are support for the public subgaussian proof.
    "logLikelihoodRatioLower",
    "logLikelihoodRatioUpper",
    "identificationGap",
    "logLikelihoodRatioProxy",
    "centeredLogLikelihoodRatio",
    "centeredLogLikelihoodRatio_hasSubgaussianMGF",
    "finiteSampleBadGap",
    "finiteSampleBadGap_probability_le",
    "selectedLikelihood_pos",
    "selectedPredictive_pos",
    "posteriorUpdate",
    "posteriorAfter",
    "priorBadOdds",
    "posteriorBadMass_contraction_of_not_badGap",
    "posteriorBadMassFailure",
    "posteriorBadMass_failure_probability_le",
    "posteriorAfter_two_true_witness",
    "posteriorAfter_zeroPrior",
    "nonidentifiableLikelihood",
    # Existing support for the exposed posterior recursion.
    "nonidentifiablePredictive_pos",
    "nonidentifiablePosteriorUpdate",
    "nonidentifiablePosteriorAfter",
    "nonidentifiablePosteriorAfter_eq_prior",
    "trajectoryObservation",
    "empiricalLogLikelihoodRatio_strongLaw",
    "posteriorBadMass_eventually_contracts",
)


def _declaration(source: str, name: str) -> str:
    match = re.search(
        rf"(?m)^(?:private\s+)?(?:noncomputable\s+)?"
        rf"(?:theorem|lemma|abbrev|def|instance)\s+{re.escape(name)}\b"
        rf"(?P<body>.*?)(?=\n(?:private\s+)?(?:noncomputable\s+)?"
        rf"(?:theorem|lemma|abbrev|def|instance|end)\b|\Z)",
        source,
        flags=re.DOTALL,
    )
    assert match is not None, f"missing declaration {name}"
    return match.group(0)


def test_posterior_learning_owns_exact_import_and_namespace_contract() -> None:
    source = FOUNDATION.read_text(encoding="utf-8")
    assert source.startswith("module\n")
    assert "\n@[expose] public section\n" in source

    assert tuple(re.findall(r"(?m)^public import (\S+)$", source)) == EXACT_IMPORTS
    assert "namespace FEP.FinitePosteriorLearning\n" in source
    assert source.rstrip().endswith("end FEP.FinitePosteriorLearning")
    assert (
        tuple(
            re.findall(
                r"(?m)^(?!private\s)(?:noncomputable\s+)?"
                r"(?:theorem|lemma|abbrev|def|instance)\s+(\w+)",
                source,
            )
        )
        == PUBLIC_DECLARATIONS
    )
    assert not re.search(
        r"\b(?:sorry|admit|axiom|opaque)\b|unsafe\s+(?:def|theorem)|:\s*True\b",
        source,
    )


def test_selected_bool_model_constructs_iid_trajectory_without_abstract_premise() -> (
    None
):
    source = FOUNDATION.read_text(encoding="utf-8")
    likelihood = _declaration(source, "selectedLikelihood")
    prior = _declaration(source, "selectedPrior")
    truth_measure = _declaration(source, "truthObservationMeasure")
    trajectory = _declaration(source, "trajectoryLaw")
    independence = _declaration(source, "trajectoryCoordinates_iIndep")
    marginal = _declaration(source, "trajectoryCoordinate_map")

    assert "abbrev Hypothesis := Bool" in source
    assert "abbrev Observation := Bool" in source
    assert "abbrev Trajectory := ℕ → Observation" in source
    assert "FiniteKernel Hypothesis Observation" in likelihood
    assert "if hypothesis = observation then 3 / 4 else 1 / 4" in likelihood
    assert "FEP.DecisionRisk.boolFairLaw" in prior
    assert "Measure.infinitePi" in trajectory
    assert "FEP.NativeBlanket.embeddedLaw truthObservationLaw" in truth_measure
    assert "truthObservationMeasure" in trajectory
    assert "iIndepFun_infinitePi" in independence
    assert "infinitePi_map_eval" in marginal
    assert not re.search(r"\((?:independent|iid)\s*:\s*iIndepFun", source)


def test_bounded_centered_llr_derives_the_finite_sample_bad_gap_bound() -> None:
    source = FOUNDATION.read_text(encoding="utf-8")
    llr = _declaration(source, "logLikelihoodRatio")
    bounded = _declaration(source, "logLikelihoodRatio_mem_Icc")
    centered = _declaration(source, "centeredLogLikelihoodRatio_hasSubgaussianMGF")
    independent_observables = _declaration(source, "centeredObservables_iIndep")
    coordinate_subgaussian = _declaration(
        source, "centeredObservable_hasSubgaussianMGF"
    )
    bad_gap = _declaration(source, "finiteSampleBadGap")
    tail = _declaration(source, "finiteSampleBadGap_probability_le")

    assert "selectedLikelihood false observation /" in llr
    assert "selectedLikelihood truthHypothesis observation" in llr
    assert "Set.Icc logLikelihoodRatioLower logLikelihoodRatioUpper" in bounded
    assert "hasSubgaussianMGF_of_mem_Icc" in centered
    assert "FEP.LearningTheory.subGaussian_empiricalMean_tail" in tail
    assert "sampleCountPositive : 0 < sampleCount" in tail
    assert "deviationPositive : 0 < deviation" in tail
    assert "(sampleCount : ℝ) * deviation ≤" in bad_gap
    assert "trajectoryCoordinates_iIndep" in independent_observables
    assert "trajectoryCoordinate_map" in coordinate_subgaussian
    assert not re.search(r"\((?:tailBound|subGaussian|concentrationBound)\s*:", tail)


def test_bad_gap_bound_contracts_the_recursively_updated_posterior_mass() -> None:
    source = FOUNDATION.read_text(encoding="utf-8")
    update = _declaration(source, "posteriorUpdate")
    repeated = _declaration(source, "posteriorAfter")
    one_step_odds = _declaration(source, "posteriorUpdate_badOdds")
    odds = _declaration(source, "posteriorAfter_badOdds")
    pathwise = _declaration(source, "posteriorBadMass_contraction_of_not_badGap")
    probability = _declaration(source, "posteriorBadMass_failure_probability_le")

    assert "FiniteLaw Hypothesis" in update
    assert "selectedLikelihood.posterior" in update
    assert "posteriorUpdate (posteriorAfter prior path sampleCount)" in repeated
    assert "FEP.LearningTheory.posteriorOdds_recursion" in one_step_odds
    assert "posteriorUpdate_badOdds" in odds
    assert "finiteSampleBadGap sampleCount deviation" in pathwise
    assert "sampleCountPositive : 0 < sampleCount" in pathwise
    assert "deviationPositive : 0 < deviation" in pathwise
    assert "deviationBelowGap : deviation < identificationGap" in pathwise
    assert "0 < (sampleCount : ℝ) * (identificationGap - deviation) ∧" in pathwise
    assert "posteriorAfter prior path sampleCount false" in pathwise
    assert "priorBadOdds prior *" in pathwise
    assert "finiteSampleBadGap_probability_le" in probability
    assert "measureReal_mono" in probability
    assert "sampleCountPositive : 0 < sampleCount" in probability
    assert "deviationPositive : 0 < deviation" in probability
    assert "deviationBelowGap : deviation < identificationGap" in probability
    assert probability.index("posteriorBadMass_contraction_of_not_badGap") < (
        probability.index("finiteSampleBadGap_probability_le")
    )
    assert not re.search(r"\((?:posteriorBound|badMassBound)\s*:", probability)


def test_repeated_update_is_nonconstant_and_retains_identification_boundaries() -> None:
    source = FOUNDATION.read_text(encoding="utf-8")
    witness = _declaration(source, "posteriorAfter_two_true_witness")
    zero_prior = _declaration(source, "posteriorAfter_zeroPrior")
    nonidentifiable_update = _declaration(source, "nonidentifiablePosteriorUpdate")
    nonidentifiable = _declaration(source, "nonidentifiablePosteriorAfter_eq_prior")

    assert "posteriorAfter selectedPrior (fun _ => true) 2 false = 1 / 10" in witness
    assert "posteriorAfter selectedPrior (fun _ => true) 2 true = 9 / 10" in witness
    assert "posteriorAfter selectedPrior (fun _ => true) 2 ≠ selectedPrior" in witness
    assert "FEP.LearningTheory.posterior_zero_of_prior_zero" in zero_prior
    assert "nonidentifiableLikelihood.posterior" in nonidentifiable_update
    assert "nonidentifiablePosteriorAfter prior path sampleCount = prior" in (
        nonidentifiable
    )
    for excluded in (
        "betaMeasure",
        "binomial",
        "conjugatePosterior",
        "FEP.EmpiricalRisk",
    ):
        assert excluded not in source


def test_almost_sure_contraction_separately_consumes_finite_alphabet_strong_law() -> (
    None
):
    source = FOUNDATION.read_text(encoding="utf-8")
    pairwise = _declaration(source, "trajectoryAtomIndicators_pairwiseIndep")
    identically_distributed = _declaration(
        source, "trajectoryAtomIndicators_identDistrib"
    )
    strong_law = _declaration(source, "empiricalLogLikelihoodRatio_strongLaw")
    eventual = _declaration(source, "posteriorBadMass_eventually_contracts")

    assert "trajectoryCoordinates_iIndep" in pairwise
    assert "trajectoryCoordinate_hasLaw" in identically_distributed
    assert "FEP.StatisticalConvergence.empiricalExpectation_strongLaw" in strong_law
    assert "∀ᵐ path ∂trajectoryLaw" in eventual
    assert "∀ᶠ sampleCount in atTop" in eventual
    assert "posteriorAfter prior path sampleCount false" in eventual
    assert "empiricalLogLikelihoodRatio_strongLaw" in eventual
    assert "posteriorBadMass_contraction_of_not_badGap" in eventual
    assert "finiteSampleBadGap_probability_le" not in eventual
