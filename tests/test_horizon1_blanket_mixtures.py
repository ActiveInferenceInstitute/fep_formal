"""H1.6 blanket-mixture, invariance, and causal-identification contracts."""

from __future__ import annotations

import re
from pathlib import Path

from fep_formal.lean_source import lean_code_without_comments

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FORMAL_ROOT = PROJECT_ROOT / "src" / "fep_formal" / "formal"
CAUSAL_SOURCE = FORMAL_ROOT / "causal_dynamics.lean"
COMPOSITION_SOURCE = (
    FORMAL_ROOT / "compositions" / "finite_scientific_implications.lean"
)

CAUSAL_THEOREMS = (
    "mixture_product_shared_right",
    "mixture_product_shared_left",
    "mixture_factorizes_of_shared_right",
    "boolFactorizedMixture_eq_correlatedBlanket",
    "boolFactorizedMixture_not_factorized",
    "interventionalMediatorMarginal_mass",
    "interventionalMediator_eq_of_mediatorKernel_eq",
)

COMPOSITION_THEOREM = "factorizedProduct_invariant_under_pairedKernel"


def _declaration(source: str, name: str) -> str:
    code = lean_code_without_comments(source)
    match = re.search(
        rf"(?m)^(?:private\s+)?(?:theorem|def|noncomputable def)\s+"
        rf"{re.escape(name)}\b(?P<body>.*?)"
        rf"(?=^(?:private\s+)?(?:theorem|def|noncomputable def)\s+|^end\b|\Z)",
        code,
        flags=re.DOTALL | re.MULTILINE,
    )
    assert match is not None, f"missing declaration {name}"
    return match.group(0)


def _statement(source: str, name: str) -> str:
    statement, separator, _proof = _declaration(source, name).partition(":= by")
    assert separator, f"{name} must have a checked proof"
    return " ".join(statement.split())


def test_h16_intrinsic_owner_exposes_shared_marginal_and_breaking_mixtures() -> None:
    source = CAUSAL_SOURCE.read_text(encoding="utf-8")

    for theorem in CAUSAL_THEOREMS:
        assert _declaration(source, theorem)

    shared_right = _statement(source, "mixture_product_shared_right")
    shared_left = _statement(source, "mixture_product_shared_left")
    factorizes = _statement(source, "mixture_factorizes_of_shared_right")
    breaking = _statement(source, "boolFactorizedMixture_not_factorized")

    assert "mixLaw weight" in shared_right
    assert "left.product shared" in shared_right
    assert "right.product shared" in shared_right
    assert "(mixLaw weight" in shared_right and ").product shared" in shared_right

    assert "shared.product left" in shared_left
    assert "shared.product right" in shared_left
    assert "shared.product (mixLaw weight" in shared_left

    assert "left = leftInternal.product shared" in factorizes
    assert "right = rightInternal.product shared" in factorizes
    assert "mixture = mixture.fstMarginal.product mixture.sndMarginal" in factorizes

    assert "mixLaw (1 / 2 : ℝ)" in breaking
    assert "(FiniteLaw.pointMass false).product" in breaking
    assert "(FiniteLaw.pointMass true).product" in breaking
    assert ".fstMarginal.product" in breaking
    assert ".sndMarginal" in breaking


def test_h16_factorized_mixture_counterexample_is_explicitly_nonvacuous() -> None:
    source = CAUSAL_SOURCE.read_text(encoding="utf-8")
    equality = _declaration(source, "boolFactorizedMixture_eq_correlatedBlanket")
    breaking = _declaration(source, "boolFactorizedMixture_not_factorized")

    assert "correlatedBoolBlanket" in equality
    assert "1 / 2" in equality
    assert "correlatedBoolBlanket_not_factorized" in breaking
    assert "FiniteLaw.pointMass false" in breaking
    assert "FiniteLaw.pointMass true" in breaking


def test_h16_structural_identification_requires_the_named_causal_kernel() -> None:
    source = CAUSAL_SOURCE.read_text(encoding="utf-8")
    theorem = _statement(source, "interventionalMediator_eq_of_mediatorKernel_eq")

    assert "left.mediatorGivenRoot = right.mediatorGivenRoot" in theorem
    assert "mediatorMarginal (interventionalJoint left root)" in theorem
    assert "mediatorMarginal (interventionalJoint right root)" in theorem
    for unsupported in ("faithful", "dSeparated", "identifiedFromObservation"):
        assert unsupported not in theorem


def test_h16_cross_owner_theorem_preserves_factorized_stationary_product() -> None:
    source = COMPOSITION_SOURCE.read_text(encoding="utf-8")
    theorem = _statement(source, COMPOSITION_THEOREM)

    assert "FEP.FiniteMarkovDynamics.IsInvariant internalLaw internalKernel" in theorem
    assert "FEP.FiniteMarkovDynamics.IsInvariant externalLaw externalKernel" in theorem
    assert "FEP.FiniteMarkovDynamics.IsInvariant" in theorem
    assert "internalLaw.product externalLaw" in theorem
    assert "pairedKernel internalKernel externalKernel" in theorem
    assert "ConditionalBlanketModel Unit Internal External" in theorem
    assert "FEP.CausalDynamics.Factorizes blanketModel" in theorem
    assert "blanketModel.conditional () = internalLaw.product externalLaw" in theorem
    assert "blanketModel.blanketLaw () = 1" in theorem


def test_h16_sources_remain_placeholder_free() -> None:
    for path in (CAUSAL_SOURCE, COMPOSITION_SOURCE):
        source = lean_code_without_comments(path.read_text(encoding="utf-8"))
        assert not re.search(r"(?m)^\s*(?:axiom|opaque)\b", source)
        assert not re.search(r"\b(?:sorry|admit)\b|:\s*True\b", source)
