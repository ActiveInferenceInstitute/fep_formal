"""H2 diagnostics retain catalogue closure and scientific counterexamples."""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction

import pytest

from fep_lean.verification._horizon_numerical_witnesses import _inverse
from fep_lean.verification.numerical_witnesses import (
    evaluate_numerical_witnesses,
    numerical_witness_by_id,
)


def test_horizons_preserve_exact_catalogue_closure() -> None:
    witnesses = evaluate_numerical_witnesses()
    assert len([w for w in witnesses if w.scope == "catalogue"]) == 16
    assert {w.id for w in witnesses if w.scope == "horizon2"} == {
        "h2-scalar-terminal",
        "h2-fin4-blanket",
    }
    assert all(w.accepted for w in witnesses)


def test_local_gradient_line_is_not_an_exponential_flow() -> None:
    witness = numerical_witness_by_id()["h2-scalar-terminal"]
    assert [row.values[1] for row in witness.rows] == [1.5, 1.125, 0.75, 0.0]
    checks = {check.id: check for check in witness.checks}
    assert checks["local-vfe-derivative"].rhs == -4.5
    assert checks["posterior-variance"].lhs == 0.5
    parameters = dict(witness.parameters)
    assert parameters["base_risk"] < parameters["alternative_risk"]
    changed = replace(checks["posterior-variance"], lhs=1.0)
    rejected = replace(witness, checks=(changed,))
    assert not rejected.accepted


def test_precision_blanket_does_not_mean_marginal_independence() -> None:
    witness = numerical_witness_by_id()["h2-fin4-blanket"]
    parameters = dict(witness.parameters)
    assert parameters["marginal_endpoint_covariance"] == 1 / 24
    assert parameters["conditional_endpoint_covariance"] == 0
    assert parameters["perturbed_conditional_covariance"] == -1 / 15
    assert witness.rows[0].values == (0.0, 0.0, 0.0, 0.0)
    assert all(row.values[3] > 0 for row in witness.rows[1:])


def test_singular_witness_inverse_rejects() -> None:
    with pytest.raises(ValueError, match="singular"):
        _inverse(((Fraction(1), Fraction(1)), (Fraction(1), Fraction(1))))


def test_exact_inverse_pivots_when_diagonal_is_zero() -> None:
    matrix = ((Fraction(0), Fraction(1)), (Fraction(1), Fraction(0)))
    assert _inverse(matrix) == matrix


def test_unknown_witness_scope_rejects() -> None:
    with pytest.raises(ValueError, match="scope"):
        replace(numerical_witness_by_id()["h2-scalar-terminal"], scope="unbound")  # type: ignore[arg-type]


def test_scope_selection_uses_same_registry() -> None:
    all_witnesses = evaluate_numerical_witnesses()
    for scope in ("catalogue", "horizon2"):
        assert evaluate_numerical_witnesses(scope=scope) == tuple(
            w for w in all_witnesses if w.scope == scope
        )
    with pytest.raises(ValueError, match="scope"):
        evaluate_numerical_witnesses(scope="unbound")  # type: ignore[arg-type]


def test_stationary_check_detects_wrong_transverse_decay(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from fep_lean.verification import _horizon_numerical_witnesses as horizon

    original = horizon._fin4_transition

    def wrong_decay(
        time: float, modes: tuple[tuple[int, ...], ...], eigenvalues: tuple[int, ...]
    ) -> horizon.Matrix:
        # The all-ones rate stays correct and the altered flow remains a semigroup.
        return original(
            time, modes, tuple(5 if rate == 4 else rate for rate in eigenvalues)
        )

    monkeypatch.setattr(horizon, "_fin4_transition", wrong_decay)
    witness = horizon.fin4_blanket_witness()
    checks = {check.id: check for check in witness.checks}
    assert checks["semigroup-composition"].accepted
    assert checks["all-ones-scalar-projection"].accepted
    assert checks["positive-time-noise"].accepted
    assert not checks["stationary-covariance"].accepted
    assert not witness.accepted
