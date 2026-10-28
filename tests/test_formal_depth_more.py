"""Deep information-theory and Fisher-geometry contracts stay projected."""

from __future__ import annotations

from pathlib import Path

from fep_formal.formal import formal_projection_drift
from fep_formal.formal.declarations import formal_theorem_modules

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_finite_information_chain_rules_are_declared_and_projected() -> None:
    owners = formal_theorem_modules(PROJECT_ROOT)
    expected = {
        "FEP.FiniteInformation.conditionalKL_nonneg",
        "FEP.FiniteInformation.conditionalKL_eq_zero_iff",
        "FEP.FiniteInformation.finiteKL_joint_chain_rule",
        "FEP.FiniteInformation.finiteKL_prior_le_joint",
        "FEP.FiniteInformation.finiteKL_product",
        "FEP.FiniteInformation.mutualInformation_eq_zero_iff",
        "FEP.FiniteInformation.mutualInformation_le_predictive_entropy",
    }

    assert {name: owners.get(name) for name in expected} == {
        name: "FepSketches.finite_information" for name in expected
    }
    assert formal_projection_drift(PROJECT_ROOT) == ()


def test_fisher_lowering_and_pullback_laws_are_declared_and_projected() -> None:
    owners = formal_theorem_modules(PROJECT_ROOT)
    expected = {
        "FEP.InformationGeometry.bernoulliScoreModel_fullSupport",
        "FEP.InformationGeometry.bernoulliScoreModel_identifiable",
        "FEP.InformationGeometry.bernoulli_fisherMatrix_entry",
        "FEP.InformationGeometry.bernoulli_fisherMatrix_isUnit",
        "FEP.InformationGeometry.bernoulli_fisherMetric_eq",
        "FEP.InformationGeometry.bernoulli_fisherMetric_pos",
        "FEP.InformationGeometry.bernoulli_naturalGradient_eq",
        "FEP.InformationGeometry.duplicatedFairBernoulli_fisherMatrix_entry",
        "FEP.InformationGeometry.duplicatedFairBernoulli_not_identifiable",
        "FEP.InformationGeometry.duplicatedScoreNullTangent_ne_zero",
        "FEP.InformationGeometry.duplicatedScoreNullTangent_pairing_zero",
        "FEP.InformationGeometry.duplicatedScore_fisherMetric_eq_zero",
        "FEP.InformationGeometry.fairBernoulliScoreModel_scores",
        "FEP.InformationGeometry.fairBernoulli_fisherMatrix_entry",
        "FEP.InformationGeometry.fisherMetric_eq_dot_lowerTangent",
        "FEP.InformationGeometry.fisherMetric_add_left",
        "FEP.InformationGeometry.fisherMetric_smul_left",
        "FEP.InformationGeometry.naturalGradient_metric_duality",
        "FEP.InformationGeometry.naturalGradient_energy_identity",
        "FEP.InformationGeometry.pullbackMetric_comp",
    }

    assert {name: owners.get(name) for name in expected} == {
        name: "FepSketches.information_geometry" for name in expected
    }
    assert formal_projection_drift(PROJECT_ROOT) == ()
