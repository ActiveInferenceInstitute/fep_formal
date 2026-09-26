"""Numerical witnesses pin family diagnostics without claiming proof evidence."""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import MISSING, fields, replace
from itertools import pairwise
from typing import Any, cast

import pytest

from fep_lean.formal.declarations import all_formal_theorem_declarations
from fep_lean.verification import numerical_witnesses as witness_module
from fep_lean.verification.numerical_witnesses import (
    NON_PROOF_EVIDENCE,
    NumericalCheck,
    NumericalWitness,
    WitnessColumn,
    WitnessPlot,
    WitnessRow,
    evaluate_numerical_witnesses,
    numerical_witness_by_id,
)

EXPECTED_IDS = (
    "measure-bayes-reconstruction",
    "gibbs-duality-gap",
    "soft-bellman-temperature",
    "bool-forward-backward",
    "causal-intervention-invariance",
    "finite-jet-error-descent",
    "path-fluctuation-identity",
    "categorical-fisher-rank",
    "belief-consensus-contraction",
    "subgaussian-envelope",
    "laplace-brier-risk",
    "policy-tree-feedback",
    "native-blanket-transfer",
    "exponential-family-duality",
    "two-state-master-equation",
    "boltzmann-efe-affinity-gap",
    "h2-scalar-terminal",
    "h2-fin4-blanket",
)


def test_every_expanded_family_has_one_accepted_numerical_witness() -> None:
    witnesses = evaluate_numerical_witnesses()

    assert tuple(witness.id for witness in witnesses) == EXPECTED_IDS
    assert len({witness.family for witness in witnesses}) == len(EXPECTED_IDS)
    assert all(witness.accepted for witness in witnesses)
    assert all(witness.checks for witness in witnesses)
    assert all(check.accepted for witness in witnesses for check in witness.checks)
    assert all(
        math.isfinite(check.residual)
        for witness in witnesses
        for check in witness.checks
    )


def test_numerical_check_is_the_sole_typed_assertion_surface() -> None:
    witness_fields = {field.name for field in fields(NumericalWitness)}
    assert "checks" in witness_fields
    assert "residual" not in witness_fields
    assert "tolerance" not in witness_fields

    assert NumericalCheck("eq", "eq", 1.0, 1.0, 0.0).accepted
    assert NumericalCheck("le", "le", 1.0, 2.0, 0.0).accepted
    assert NumericalCheck("ge", "ge", 2.0, 1.0, 0.0).accepted
    assert NumericalCheck("predicate", "predicate", True, True, 0.0).accepted


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        (
            {
                "id": "Bad ID",
                "relation": "eq",
                "lhs": 0.0,
                "rhs": 0.0,
                "tolerance": 0.0,
            },
            "malformed",
        ),
        (
            {
                "id": "bad",
                "relation": "invalid",
                "lhs": 0.0,
                "rhs": 0.0,
                "tolerance": 0.0,
            },
            "relation",
        ),
        (
            {
                "id": "bad",
                "relation": "eq",
                "lhs": math.nan,
                "rhs": 0.0,
                "tolerance": 0.0,
            },
            "finite",
        ),
        (
            {
                "id": "bad",
                "relation": "eq",
                "lhs": 0.0,
                "rhs": math.inf,
                "tolerance": 0.0,
            },
            "finite",
        ),
        (
            {"id": "bad", "relation": "eq", "lhs": 0.0, "rhs": 0.0, "tolerance": -1.0},
            "tolerance",
        ),
        (
            {
                "id": "bad",
                "relation": "predicate",
                "lhs": 1,
                "rhs": True,
                "tolerance": 0.0,
            },
            "boolean",
        ),
    ],
)
def test_numerical_check_rejects_malformed_contracts(
    kwargs: dict[str, object], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        NumericalCheck(**cast(Any, kwargs))


def test_strong_theorem_alignment_must_be_explicitly_declared() -> None:
    alignment = next(
        field for field in fields(NumericalWitness) if field.name == "formal_alignment"
    )
    assert alignment.default is MISSING


def test_witness_registry_rejects_family_substitution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = witness_module._measure_bayes_reconstruction()
    monkeypatch.setattr(
        witness_module,
        "_measure_bayes_reconstruction",
        lambda: replace(original, family="core-free-energy"),
    )

    with pytest.raises(ValueError, match="family closure"):
        evaluate_numerical_witnesses()


@pytest.mark.parametrize("bad_value", [float("nan"), "not-numeric"])
def test_plot_series_reject_nonfinite_or_nonnumeric_cells(
    bad_value: str | float,
) -> None:
    witness = witness_module._categorical_fisher_rank()
    observed_index = next(
        index
        for index, column in enumerate(witness.columns)
        if column.key == "observed"
    )
    values = list(witness.rows[0].values)
    values[observed_index] = bad_value
    rows = (WitnessRow(tuple(values)), *witness.rows[1:])

    with pytest.raises(ValueError, match=r"finite (?:numeric|scalar) values"):
        replace(witness, rows=rows)


@pytest.mark.parametrize("bad_value", [float("nan"), "not-numeric"])
def test_line_plot_rejects_nonfinite_or_nonnumeric_x_cells(
    bad_value: str | float,
) -> None:
    witness = witness_module._soft_bellman_temperature()
    x_index = next(
        index
        for index, column in enumerate(witness.columns)
        if column.key == witness.plot.x_key
    )
    values = list(witness.rows[0].values)
    values[x_index] = bad_value
    rows = (WitnessRow(tuple(values)), *witness.rows[1:])

    with pytest.raises(
        ValueError, match=r"finite (?:scalar|numeric)|line and scatter x columns"
    ):
        replace(witness, rows=rows)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda witness: replace(witness, boundary_behavior=""), "boundary behavior"),
        (
            lambda witness: replace(witness, boundary_observed=cast(Any, "yes")),
            "boundary_observed",
        ),
        (
            lambda witness: replace(
                witness,
                plot=WitnessPlot(
                    cast(Any, "heatmap"), witness.plot.x_key, witness.plot.y_keys
                ),
            ),
            "plot kind",
        ),
        (
            lambda witness: replace(
                witness,
                columns=(
                    WitnessColumn(witness.columns[0].key, ""),
                    *witness.columns[1:],
                ),
            ),
            "column keys and labels",
        ),
        (
            lambda witness: replace(
                witness, parameters=(*witness.parameters, ("nonfinite", math.inf))
            ),
            "parameter values",
        ),
    ],
)
def test_witness_schema_rejects_fail_open_runtime_values(
    mutation: Callable[[NumericalWitness], NumericalWitness], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        mutation(witness_module._categorical_fisher_rank())


def test_witnesses_are_accessible_and_keep_the_evidence_boundary() -> None:
    for witness in evaluate_numerical_witnesses():
        keys = tuple(column.key for column in witness.columns)
        assert witness.evidence_kind == NON_PROOF_EVIDENCE
        assert witness.theorem_mirrors
        assert witness.rows
        assert all(len(row.values) == len(keys) for row in witness.rows)
        assert witness.plot.x_key in keys
        assert set(witness.plot.y_keys) <= set(keys)
        assert witness.boundary_behavior
        assert witness.boundary_observed
        assert len({check.id for check in witness.checks}) == len(witness.checks)


def test_every_theorem_mirror_resolves_in_the_canonical_inventory() -> None:
    known = all_formal_theorem_declarations()
    unresolved = {
        witness.id: tuple(
            declaration
            for declaration in witness.theorem_mirrors
            if declaration not in known
        )
        for witness in evaluate_numerical_witnesses()
        if any(declaration not in known for declaration in witness.theorem_mirrors)
    }

    assert unresolved == {}


def test_witness_evaluation_fails_closed_on_unresolved_theorem_mirror(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        witness_module,
        "all_formal_theorem_declarations",
        lambda _project_root=None: frozenset(),
        raising=False,
    )

    with pytest.raises(ValueError, match="unresolved numerical witness declarations"):
        evaluate_numerical_witnesses()


def test_family_witnesses_exercise_nontrivial_boundaries() -> None:
    witnesses = numerical_witness_by_id()

    temporal = witnesses["bool-forward-backward"]
    assert temporal.parameters[1][1] == pytest.approx(23 / 40)
    assert temporal.rows[1].values[3] == pytest.approx(20 / 23)
    assert temporal.rows[1].values[5] == pytest.approx(39 / 46)

    causal = witnesses["causal-intervention-invariance"]
    assert causal.parameters == (
        ("root_law", "uniform"),
        ("nondescendant_law", "uniform"),
        ("mediator_kernel", "copy-root"),
        ("outcome_kernel", "xor"),
    )
    assert tuple(row.values[0] for row in causal.rows) == (
        "do(root=false)",
        "do(root=true)",
    )
    assert causal.rows[0].values[1] == causal.rows[1].values[1] == 0.5
    assert causal.rows[0].values[2] == 0.0
    assert causal.rows[1].values[2] == 1.0
    assert causal.rows[0].values[3] == causal.rows[1].values[3] == 0.5

    predictive = witnesses["finite-jet-error-descent"]
    assert predictive.parameters == (
        ("precision", 3.0),
        ("target", 0.25),
        ("step_size", 0.2),
        ("contraction", 0.8),
    )
    assert predictive.rows[0].values[2] == pytest.approx(-1.75)
    assert predictive.rows[1].values[2] == pytest.approx(-1.4)
    energies = tuple(float(row.values[3]) for row in predictive.rows)
    assert all(later < earlier for earlier, later in pairwise(energies))

    soft_bellman = witnesses["soft-bellman-temperature"]
    assert {
        "FEP.ControlledMarkov.softBellmanValue_succ",
        "FEP.ControlledMarkov.softBellmanValue_partition_pos",
        "FEP.ControlledMarkov.softBellmanValue_le_actionEnergy",
        "fep_fep068.FEP068.fep068_softBellman_recursion",
    } <= set(soft_bellman.theorem_mirrors)
    assert all(float(row.values[1]) > 0.0 for row in soft_bellman.rows)
    assert all(float(row.values[4]) >= 0.0 for row in soft_bellman.rows)
    assert all(float(row.values[5]) >= 0.0 for row in soft_bellman.rows)

    fisher = witnesses["categorical-fisher-rank"]
    assert fisher.parameters == (
        ("categories", 2),
        ("categorical_law", "(1/2, 1/2)"),
        ("categorical_tangent", "(1, -1)"),
        ("duplicated_score_gram", "[[4, 4], [4, 4]]"),
    )
    assert {
        "FEP.GeometricOptimization.twoCategorical_nonzeroTangent_metric",
        "FEP.GeometricOptimization.twoCategorical_simplexMetric_fullRank",
        "FEP.InformationGeometry.duplicatedFairBernoulli_fisherMatrix_entry",
        "FEP.InformationGeometry.duplicatedFairBernoulli_not_identifiable",
    } <= set(fisher.theorem_mirrors)
    assert tuple(row.values[2] for row in fisher.rows) == (4.0, 4.0, 4.0, 4.0, 0.0)
    assert all(row.values[3] == 0.0 for row in fisher.rows)

    consensus = witnesses["belief-consensus-contraction"]
    gaps = tuple(float(row.values[3]) for row in consensus.rows)
    assert gaps == tuple(sorted(gaps, reverse=True))
    assert gaps[-1] < gaps[0]

    concentration = witnesses["subgaussian-envelope"]
    assert concentration.formal_alignment == "structural_analogue"
    assert all(
        float(row.values[1]) <= float(row.values[2]) for row in concentration.rows
    )

    risk = witnesses["laplace-brier-risk"]
    assert risk.family == "finite-sample-risk-and-calibration"
    assert risk.parameters[:2] == (("sample_count", 8), ("target", 0.3))
    assert any(check.id == "nonzero-bias-quarter" for check in risk.checks)

    policy = witnesses["policy-tree-feedback"]
    assert policy.family == "closed-loop-policy-trees-and-efe"
    assert any(check.id == "feedback-value-zero" for check in policy.checks)
    assert any(check.id == "open-loop-value-half" for check in policy.checks)

    blanket = witnesses["native-blanket-transfer"]
    assert blanket.family == "finite-to-native-blanket-transfer"
    assert tuple(row.values[1] for row in blanket.rows) == (0.5, 0.5, 0.0)

    geometry = witnesses["exponential-family-duality"]
    assert geometry.family == "finite-exponential-family-dual-geometry"
    assert any(
        check.id == "three-state-variance-two-thirds" for check in geometry.checks
    )

    continuous = witnesses["two-state-master-equation"]
    assert continuous.family == "two-state-continuous-time-thermodynamics"
    assert continuous.parameters[:2] == (("forward_rate", 0.7), ("backward_rate", 0.3))
    assert any(
        check.id == "lyapunov-derivative-negative" for check in continuous.checks
    )
