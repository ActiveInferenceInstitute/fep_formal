"""H1.1 implication boundaries and finite countermodel contracts."""

from __future__ import annotations

import re
from pathlib import Path

from fep_lean.lean_source import lean_code_without_comments

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE = (
    PROJECT_ROOT
    / "src"
    / "fep_lean"
    / "formal"
    / "compositions"
    / "finite_scientific_implications.lean"
)

DIRECT_IMPORTS = (
    "FepSketches.finite_probability",
    "FepSketches.causal_dynamics",
    "FepSketches.finite_markov_dynamics",
    "FepSketches.active_inference",
    "FepSketches.information_geometry",
)

TARGET_DECLARATIONS = (
    "factorizedProduct_invariant_under_pairedKernel",
    "rowwiseBlanket_doesNotImply_stationaryBlanket",
    "sparseCoupling_doesNotImply_condIndep",
    "stationaryBlanket_doesNotImply_freeEnergyDescent",
    "blanketPosterior_and_flowAlignment_imply_localDescent",
    "observationalBlanket_doesNotIdentify_causalBlanket",
)

CROSS_CARRIER_PREDICATES = (
    "RecognitionMatchesPosterior",
    "LocalFreeEnergyDescent",
)

INTRINSIC_OWNER_VOCABULARY = (
    "ConditionallyIndependent",
    "RowwiseTransitionFactorization",
    "StationaryLaw",
    "StationaryBlanket",
    "SparseCoupling",
    "ObservationalBlanketsEquivalent",
    "CausalBlanketsEquivalent",
)




def _declaration(source: str, name: str) -> str:
    uncommented = lean_code_without_comments(source)
    match = re.search(
        rf"(?m)^(?:private\s+)?(?:theorem|def|noncomputable def)\s+"
        rf"{re.escape(name)}\b(?P<body>.*?)"
        rf"(?=^(?:private\s+)?(?:theorem|def|noncomputable def)\s+|^end\b|\Z)",
        uncommented,
        flags=re.DOTALL | re.MULTILINE,
    )
    assert match is not None, f"missing declaration {name}"
    return match.group(0)


def _statement(source: str, name: str) -> str:
    declaration = _declaration(source, name)
    statement, separator, _proof = declaration.partition(":= by")
    assert separator, f"{name} must have a checked proof body"
    return statement


def test_h11_source_owns_exact_imports_and_namespace() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    imports = tuple(
        line.removeprefix("import ")
        for line in source.splitlines()
        if line.startswith("import ")
    )

    assert imports == DIRECT_IMPORTS
    assert "namespace FEPComposed.FiniteScientificImplications\n" in source
    assert source.rstrip().endswith("end FEPComposed.FiniteScientificImplications")


def test_h11_exposes_the_five_implication_boundaries_without_placeholders() -> None:
    source = SOURCE.read_text(encoding="utf-8")

    assert tuple(re.findall(r"(?m)^theorem\s+([A-Za-z0-9_]+)", source)) == (
        TARGET_DECLARATIONS
    )
    assert not re.search(r"(?m)^\s*(?:axiom|opaque|unsafe\s+(?:def|theorem))\b", source)
    assert not re.search(r"\b(?:sorry|admit)\b|:\s*True\b", source)


def test_h11_owns_only_cross_carrier_recognition_and_descent_predicates() -> None:
    source = SOURCE.read_text(encoding="utf-8")

    for name in CROSS_CARRIER_PREDICATES:
        assert _declaration(source, name)

    uncommented = lean_code_without_comments(source)
    assert "HasRecognitionMap" not in uncommented
    for name in INTRINSIC_OWNER_VOCABULARY:
        assert not re.search(
            rf"(?m)^(?:private\s+)?(?:theorem|def|noncomputable def)\s+"
            rf"{re.escape(name)}\b",
            uncommented,
        )

    recognition = _declaration(source, "RecognitionMatchesPosterior")
    descent = _declaration(source, "LocalFreeEnergyDescent")

    assert "posteriorState model" in recognition
    assert "∃ derivative" in descent
    assert "HasDerivAt objective derivative point ∧ derivative < 0" in descent


def test_rejected_implications_ship_rational_nonvacuous_countermodels() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    rowwise = _statement(source, "rowwiseBlanket_doesNotImply_stationaryBlanket")
    sparse = _statement(source, "sparseCoupling_doesNotImply_condIndep")
    stationary = _statement(source, "stationaryBlanket_doesNotImply_freeEnergyDescent")
    causal = _statement(source, "observationalBlanket_doesNotIdentify_causalBlanket")
    stationary_contract = " ".join(stationary.split())

    assert "∀ current" in rowwise and "kernel.row current" in rowwise
    assert "FEP.FiniteMarkovDynamics.IsInvariant law kernel" in rowwise
    assert "∃ blanketModel : ConditionalBlanketModel Unit Bool Bool" in rowwise
    assert "blanketModel.conditional () = law" in rowwise
    assert "FEP.CausalDynamics.Factorizes blanketModel" in rowwise
    assert "blanketModel.blanketLaw () = 1" in rowwise
    assert rowwise.count("= 1 / 2") == 2

    assert "∃ internalKernel : FiniteKernel Bool Bool" in sparse
    assert "kernel = pairedKernel internalKernel externalKernel" in sparse
    assert "FEP.FiniteMarkovDynamics.IsInvariant law kernel" in sparse
    assert "blanketModel.conditional () = law" in sparse
    assert "¬FEP.CausalDynamics.Factorizes blanketModel" in sparse
    assert "blanketModel.blanketLaw () = 1" in sparse
    assert sparse.count("= 1 / 2") == 2

    assert (
        "FEP.FiniteMarkovDynamics.IsInvariant independentFairBlanket "
        "pairIdentityKernel" in stationary_contract
    )
    assert (
        "FEP.CausalDynamics.Factorizes independentStationaryBlanketModel"
        in stationary_contract
    )
    assert (
        "independentStationaryBlanketModel.conditional () = independentFairBlanket"
        in stationary_contract
    )
    assert "independentStationaryBlanketModel.blanketLaw () = 1" in stationary_contract
    assert "¬LocalFreeEnergyDescent stationaryPosteriorFreeEnergy 0" in stationary
    assert stationary.count("= 1 / 4") == 2
    assert "variationalFreeEnergy" in _declaration(
        source, "stationaryPosteriorFreeEnergy"
    )
    assert "posteriorState" in _declaration(source, "stationaryPosteriorFreeEnergy")
    assert (
        "independentFairBlanket.fstMarginal = "
        "predictedState (symmetricBoolModel fairBoolLaw) false" in stationary_contract
    )
    assert (
        "posteriorState (symmetricBoolModel fairBoolLaw) false false "
        "symmetricFalseEvidence = independentFairBlanket.fstMarginal"
        in stationary_contract
    )

    for statement in (rowwise, sparse, stationary):
        assert "law.fstMarginal.product law.sndMarginal" not in statement

    assert "mediatorMarginal (orderedJoint observationalCopyModel) =" in causal
    assert "mediatorMarginal (orderedJoint observationalIndependentModel)" in causal
    assert "¬(∀ root" in causal
    assert "interventionalJoint observationalCopyModel root" in causal
    assert "interventionalJoint observationalIndependentModel root" in causal
    assert "= 1 / 2" in causal and "= 1" in causal


def test_positive_recovery_exposes_rank_alignment_and_derivative_premises() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    theorem = _declaration(
        source, "blanketPosterior_and_flowAlignment_imply_localDescent"
    )
    statement = _statement(
        source, "blanketPosterior_and_flowAlignment_imply_localDescent"
    )

    for required in (
        "hPosterior : RecognitionMatchesPosterior",
        "hPosteriorSupport : ∀ state",
        "hIdentifiable : Identifiable scoreModel",
        "hTangent : tangent ≠ 0",
        "hNatural : IsNaturalGradient scoreModel covector tangent",
        "hDerivative : HasDerivAt objective derivative point",
        "hDerivativeIdentity :",
        "derivative = -(∑ coordinate, tangent coordinate * covector coordinate)",
    ):
        assert required in statement

    assert "derivative < 0" not in statement
    assert "HasRecognitionMap" not in theorem
    assert "fisherMetric_pos" in theorem
    assert "fisherMetric_eq_dot_lowerTangent" in theorem
    assert "LocalFreeEnergyDescent objective point" in statement
    for overclaim in ("global", "converges", "physical", "dissipation"):
        assert overclaim not in statement.lower()


def test_interior_bernoulli_instantiates_the_recovery_theorem() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    witness = _declaration(source, "interiorBernoulli_localDescent_nonvacuous")
    probability = _declaration(source, "scaledLogisticProbability")
    model = _declaration(source, "bernoulliEvidenceModel")
    objective = _declaration(source, "bernoulliEvidenceFreeEnergy")
    direction = _declaration(source, "bernoulliDirectionalVFE")
    vfe_binding = _declaration(
        source, "bernoulliEvidenceFreeEnergy_eq_variationalFreeEnergy"
    )
    score_binding = _declaration(source, "parameterizedBernoulli_score_eq_logDeriv")
    alignment = _declaration(source, "bernoulliNatural_alignment")
    directional_derivative = _declaration(source, "bernoulliDirectionalVFE_hasDerivAt")

    assert witness.startswith("private theorem")
    assert "fairBernoulliScoreModel" in witness
    assert "bernoulliEvidenceModel 0" in witness
    assert "RecognitionMatchesPosterior" in witness
    assert "bernoulliScoreModel_identifiable" in witness
    assert "bernoulliNaturalTangent_ne_zero" in witness
    assert "bernoulliNatural_alignment" in witness
    assert "bernoulliDirectionalVFE_hasDerivAt" in witness
    assert "blanketPosterior_and_flowAlignment_imply_localDescent" in witness
    assert "fun parameter : ℝ => -4 * parameter" not in witness

    assert "Real.exp (4 * parameter)" in probability
    assert "GenerativeModel Unit Bool Bool" in model
    assert "scaledLogisticLaw parameter" in model
    assert "outcomeSurprisal (bernoulliEvidenceModel parameter) () true" in objective
    assert (
        "bernoulliEvidenceFreeEnergy (-step * bernoulliNaturalTangent 0)" in direction
    )
    assert "variationalFreeEnergy (bernoulliEvidenceModel parameter)" in vfe_binding
    assert "posteriorState (bernoulliEvidenceModel parameter)" in vfe_binding
    assert "fairBernoulliScoreModel.score outcome 0" in score_binding
    assert "HasDerivAt" in score_binding and "Real.log" in score_binding
    assert (
        "IsNaturalGradient fairBernoulliScoreModel bernoulliEvidenceCovector"
        in alignment
    )
    assert "bernoulliNaturalTangent" in alignment
    assert "HasDerivAt bernoulliDirectionalVFE (-1) 0" in directional_derivative
