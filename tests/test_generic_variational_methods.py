"""Independent numerical contracts for reusable finite Gibbs methods.

These tests compare floating-point diagnostics with arithmetic oracles. They
do not elaborate Lean or create a native/scientific acceptance receipt.
"""

from __future__ import annotations

import json
import math
import sys
from decimal import ROUND_DOWN, Decimal, Inexact, localcontext
from fractions import Fraction

import pytest

from fep_formal import cli
from fep_formal.methods import (
    BoundaryProbeError,
    exponential_tilt,
    extended_kl,
    finite_expectation,
    gibbs_duality_diagnostics,
    log_partition,
)


def _decimal_oracle(reference, potential, candidate=None, *, precision=120):
    """Use direct high-precision exponentials independently of float scaling."""
    with localcontext() as context:
        context.prec = precision
        q = tuple(Decimal.from_float(float(value)) for value in reference)
        v = tuple(Decimal.from_float(float(value)) for value in potential)
        if candidate is not None:
            q = tuple(value / sum(q) for value in q)
        weights = tuple(mass * value.exp() for mass, value in zip(q, v, strict=True))
        partition = sum(weights)
        optimizer = tuple(weight / partition for weight in weights)
        result = {
            "log_partition": float(partition.ln()),
            "optimizer": tuple(float(mass) for mass in optimizer),
        }
        if candidate is not None:
            p = tuple(Decimal.from_float(float(value)) for value in candidate)
            p = tuple(value / sum(p) for value in p)
            expected = sum(mass * value for mass, value in zip(p, v, strict=True))
            kl = sum(
                mass * (mass.ln() - base.ln())
                for mass, base in zip(p, q, strict=True)
                if mass
            )
            gap = partition.ln() - expected + kl
            result.update(
                expected_potential=float(expected),
                kl_candidate_reference=float(kl),
                dv_objective=float(expected - kl),
                duality_gap=float(gap),
            )
        return result


def test_finite_gibbs_matches_independent_direct_exponential_oracle():
    reference = (0.2, 0.3, 0.5)
    potential = (-0.4, 0.2, 0.8)
    candidate = (0.1, 0.7, 0.2)
    oracle = _decimal_oracle(reference, potential)
    assert log_partition(reference, potential) == pytest.approx(
        oracle["log_partition"], rel=1e-13, abs=1e-14
    )
    assert exponential_tilt(reference, potential) == pytest.approx(
        oracle["optimizer"], rel=1e-13, abs=1e-14
    )
    report = gibbs_duality_diagnostics(candidate, reference, potential)
    expected = _decimal_oracle(reference, potential, candidate)
    for key in (
        "log_partition",
        "expected_potential",
        "kl_candidate_reference",
        "dv_objective",
        "duality_gap",
    ):
        assert report[key] == pytest.approx(expected[key], rel=1e-12, abs=2e-14)
    assert report["kl_candidate_log_tilt"] == pytest.approx(
        expected["duality_gap"], rel=1e-12, abs=2e-14
    )
    assert report["identity_within_roundoff"] is True
    assert abs(report["identity_residual"]) <= report["roundoff_allowance"]
    assert report["reference_zero_indices"] == []
    assert report["candidate_outside_reference_indices"] == []
    assert report["tilt_underflow_indices"] == []
    assert isinstance(report["evidence_boundary"], str)
    assert "proof" in report["evidence_boundary"].lower()
    assert "claim_ready" not in report
    assert "native_verified" not in report
    json.dumps(report, allow_nan=False)


def test_explicit_gibbs_optimizer_attains_zero_gap_within_roundoff():
    reference = (0.2, 0.3, 0.5)
    potential = (-0.4, 0.2, 0.8)
    optimizer = exponential_tilt(reference, potential)
    report = gibbs_duality_diagnostics(optimizer, reference, potential)
    assert report["duality_gap"] == pytest.approx(0.0, abs=2e-13)
    assert report["kl_candidate_log_tilt"] == pytest.approx(0.0, abs=2e-13)
    assert report["dv_objective"] == pytest.approx(report["log_partition"], abs=2e-13)


def test_generic_methods_do_not_inherit_ambient_decimal_rounding_or_traps():
    reference = (0.2, 0.3, 0.5)
    candidate = (0.1, 0.7, 0.2)
    potential = (-0.4, 0.2, 0.8)
    expected_partition = log_partition(reference, potential)
    expected_tilt = exponential_tilt(reference, potential)
    expected_report = gibbs_duality_diagnostics(candidate, reference, potential)
    with localcontext() as context:
        context.prec = 3
        context.rounding = ROUND_DOWN
        context.traps[Inexact] = True
        assert log_partition(reference, potential) == expected_partition
        assert exponential_tilt(reference, potential) == expected_tilt
        assert (
            gibbs_duality_diagnostics(candidate, reference, potential)
            == expected_report
        )


@pytest.mark.parametrize("offset", (0.0, 900.0, -900.0, 1e308, -1e308))
def test_constant_potential_preserves_nonuniform_reference(offset):
    reference = (0.125, 0.25, 0.625)
    potential = (offset,) * len(reference)
    assert log_partition(reference, potential) == pytest.approx(offset, abs=2e-14)
    assert exponential_tilt(reference, potential) == pytest.approx(
        reference, rel=1e-13, abs=1e-14
    )


def test_gibbs_is_equivariant_under_permutation_and_constant_shift():
    reference = (0.2, 0.0, 0.3, 0.5)
    candidate = (0.6, 0.0, 0.1, 0.3)
    potential = (-0.5, 7.0, 0.3, 0.8)
    order = (3, 1, 0, 2)
    permuted = lambda values: tuple(values[index] for index in order)
    original = exponential_tilt(reference, potential)
    assert exponential_tilt(permuted(reference), permuted(potential)) == pytest.approx(
        permuted(original), rel=1e-13, abs=1e-14
    )
    shifted = tuple(value + 512.0 for value in potential)
    assert exponential_tilt(reference, shifted) == pytest.approx(
        original, rel=1e-12, abs=1e-13
    )
    assert log_partition(reference, shifted) - 512.0 == pytest.approx(
        log_partition(reference, potential), abs=1e-13
    )
    before = gibbs_duality_diagnostics(candidate, reference, potential)
    after = gibbs_duality_diagnostics(candidate, reference, shifted)
    assert after["duality_gap"] == pytest.approx(before["duality_gap"], abs=1e-13)


def test_zero_reference_atoms_do_not_set_the_center_or_gain_mass():
    reference = (0.0, 1.0)
    potential = (1e308, -1e308)
    assert log_partition(reference, potential) == -1e308
    assert exponential_tilt(reference, potential) == (0.0, 1.0)
    assert exponential_tilt(reference, (-1e308, -1e308)) == (0.0, 1.0)


def test_subnormal_reference_is_not_multiplied_before_log_scaling():
    smallest = math.ulp(0.0)
    reference = (smallest, 1.0)
    potential = (0.0, -745.0)
    oracle = _decimal_oracle(reference, potential)
    actual = exponential_tilt(reference, potential)
    assert actual == pytest.approx(oracle["optimizer"], rel=2e-13, abs=1e-14)
    assert 0.63 < actual[0] < 0.64
    assert log_partition(reference, potential) == pytest.approx(
        oracle["log_partition"], abs=2e-12
    )


@pytest.mark.parametrize(
    ("law", "potential"),
    (
        ((0.5, 0.5), (math.ulp(0.0), math.ulp(0.0))),
        ((0.5, 0.25, 0.25), (1e308, -1e308, math.nextafter(-1e308, 0.0))),
        ((0.1, 0.2, 0.7), (1e308, -1e308, 0.0)),
        ((0.5, 0.5), (sys.float_info.max, -sys.float_info.max)),
    ),
)
def test_expectation_matches_exact_binary_rational_weighted_sum(law, potential):
    expected = float(
        sum(
            (
                Fraction.from_float(mass) * Fraction.from_float(value)
                for mass, value in zip(law, potential, strict=True)
            ),
            Fraction(0),
        )
    )
    assert finite_expectation(law, potential) == expected


def test_literal_mass_scalar_contract_and_explicit_normalized_diagnostics():
    reference = (0.3, 0.7 + 4e-13)
    candidate = (0.2, 0.8 + 5e-13)
    potential = (-1.0, 2.0)
    raw_sum = math.fsum(reference)
    assert log_partition(reference, (0.0, 0.0)) == pytest.approx(
        math.log(raw_sum), abs=1e-15
    )
    assert finite_expectation(candidate, (1.0, 1.0)) == math.fsum(candidate)
    report = gibbs_duality_diagnostics(candidate, reference, potential)
    assert report["input_mass_sums"] == {
        "candidate": math.fsum(candidate),
        "reference": raw_sum,
    }
    assert report["input_mass_residuals"]["candidate"] == pytest.approx(
        math.fsum(candidate) - 1.0, abs=1e-16
    )
    assert isinstance(report["normalization_convention"], str)
    assert "normaliz" in report["normalization_convention"].lower()
    oracle = _decimal_oracle(reference, potential, candidate)
    assert report["expected_potential"] == pytest.approx(
        oracle["expected_potential"], abs=2e-14
    )
    assert report["duality_gap"] == pytest.approx(oracle["duality_gap"], abs=2e-14)


@pytest.mark.parametrize("tail", (1e-90, 1e-200, math.ulp(0.0)))
def test_literal_log_partition_retains_normalization_tails_below_float_one(tail):
    reference = (1.0, tail)
    potential = (0.0, 0.0)
    # The accepted law's binary64 sum rounds to one; its literal mathematical
    # sum is larger. The scalar API must retain that distinction through log.
    assert math.fsum(reference) == 1.0
    expected = _decimal_oracle(reference, potential, precision=1100)["log_partition"]
    assert expected > 0.0
    assert expected == math.log1p(tail)
    actual = log_partition(reference, potential)
    assert actual > 0.0
    assert actual == pytest.approx(expected, rel=1e-13, abs=0.0)


@pytest.mark.parametrize(
    ("candidate_tail", "reference_tail"),
    ((1e-200, 1e-90), (math.ulp(0.0), 1e-200)),
)
def test_normalized_kl_and_gibbs_gap_retain_positive_reference_tail(
    candidate_tail, reference_tail
):
    candidate = (1.0, candidate_tail)
    reference = (1.0, reference_tail)
    potential = (0.0, 0.0)
    # A low-precision normalization loses the dominant atom's positive KL
    # contribution and leaves only a spurious negative tail contribution.
    oracle = _decimal_oracle(reference, potential, candidate, precision=1100)
    expected = oracle["kl_candidate_reference"]
    assert expected > 0.99 * reference_tail
    report = gibbs_duality_diagnostics(candidate, reference, potential)
    for key in ("kl_candidate_reference", "duality_gap", "kl_candidate_log_tilt"):
        assert report[key] > 0.0
        assert report[key] == pytest.approx(expected, rel=1e-13, abs=0.0)
    assert report["duality_gap"] == pytest.approx(
        oracle["duality_gap"], rel=1e-13, abs=0.0
    )
    assert report["candidate_outside_reference_indices"] == []
    assert report["tilt_underflow_indices"] == []


def test_supported_tilt_underflow_keeps_a_finite_log_domain_gap():
    candidate = reference = (0.5, 0.5)
    report = gibbs_duality_diagnostics(candidate, reference, (0.0, -1000.0))
    assert report["optimizer"] == [1.0, 0.0]
    assert report["tilt_underflow_indices"] == [1]
    assert report["reference_zero_indices"] == []
    assert report["candidate_outside_reference_indices"] == []
    expected = 500.0 - math.log(2.0)
    assert report["duality_gap"] == pytest.approx(expected, abs=1e-12)
    assert report["kl_candidate_log_tilt"] == pytest.approx(expected, abs=1e-12)
    assert extended_kl(candidate, report["optimizer"]) == math.inf
    assert report["identity_within_roundoff"] is True
    json.dumps(report, allow_nan=False)


def test_extreme_potential_difference_can_have_a_representable_weighted_gap():
    report = gibbs_duality_diagnostics((0.5, 0.5), (0.5, 0.5), (1e308, -1e308))
    assert report["expected_potential"] == 0.0
    assert report["duality_gap"] == pytest.approx(1e308, rel=1e-14)
    assert report["kl_candidate_log_tilt"] == pytest.approx(1e308, rel=1e-14)
    assert report["tilt_underflow_indices"] == [1]
    assert math.isfinite(report["roundoff_allowance"])
    json.dumps(report, allow_nan=False)


def test_true_support_failure_is_explicit_and_json_safe():
    report = gibbs_duality_diagnostics((0.5, 0.5), (0.0, 1.0), (1.0, -1.0))
    assert report["reference_zero_indices"] == [0]
    assert report["candidate_outside_reference_indices"] == [0]
    assert report["tilt_underflow_indices"] == []
    assert report["kl_candidate_reference"] == "infinity"
    assert report["duality_gap"] == "infinity"
    assert report["kl_candidate_log_tilt"] == "infinity"
    assert report["dv_objective"] == "-infinity"
    for key in ("identity_residual", "roundoff_allowance", "identity_within_roundoff"):
        assert report[key] is None
    json.dumps(report, allow_nan=False)


@pytest.mark.parametrize(
    ("law", "potential"),
    (
        ((), ()),
        ((1.0,), (0.0, 1.0)),
        ((0.5, -0.5), (0.0, 0.0)),
        ((0.4, 0.4), (0.0, 0.0)),
        ((1e308, 1e308), (0.0, 0.0)),
        ((math.nan, 1.0), (0.0, 0.0)),
        ((math.inf, 0.0), (0.0, 0.0)),
        ((True, 0.0), (0.0, 0.0)),
        (("1", 0.0), (0.0, 0.0)),
        ((1.0, 0.0), (math.nan, 0.0)),
        ((1.0, 0.0), (0.0, math.nan)),
        ((1.0, 0.0), (math.inf, 0.0)),
        ((1.0, 0.0), (0.0, True)),
        ((1.0, 0.0), (0.0, "0")),
        ((1.0, 0.0), (0.0, 1j)),
    ),
)
def test_generic_scalar_methods_reject_invalid_law_or_potential(law, potential):
    for operation in (finite_expectation, log_partition, exponential_tilt):
        with pytest.raises(BoundaryProbeError):
            operation(law, potential)


@pytest.mark.parametrize("candidate", ((), (1.0,), (0.2, 0.2), (False, 1.0)))
def test_diagnostics_validate_candidate_independently(candidate):
    with pytest.raises(BoundaryProbeError):
        gibbs_duality_diagnostics(candidate, (0.5, 0.5), (0.0, 1.0))


def test_unrepresentable_final_expectation_and_gap_fail_explicitly():
    # Law sums remain inside the accepted tolerance; the literal weighted
    # expectation nevertheless exceeds binary64's largest finite value.
    with pytest.raises(BoundaryProbeError):
        finite_expectation((1.0 + 5e-13,), (sys.float_info.max,))
    with pytest.raises(BoundaryProbeError):
        gibbs_duality_diagnostics((0.0, 1.0), (0.5, 0.5), (1e308, -1e308))


def test_gibbs_cli_emits_explicit_nonproof_report_and_domain_error(capsys):
    arguments = [
        "methods",
        "gibbs",
        "--reference",
        "[0.2, 0.3, 0.5]",
        "--potential",
        "[-0.4, 0.2, 0.8]",
        "--candidate",
        "[0.1, 0.7, 0.2]",
    ]
    assert cli.main(arguments) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "ok"
    assert payload["result"]["duality_gap"] > 0.0
    assert "proof" in payload["result"]["evidence_boundary"].lower()
    bad = arguments.copy()
    bad[bad.index("--candidate") + 1] = "[0.1, 0.1, 0.1]"
    assert cli.main(bad) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "error"


def test_gibbs_cli_requires_candidate_and_rejects_malformed_json(capsys):
    with pytest.raises(SystemExit) as missing:
        cli.main(["methods", "gibbs", "--reference", "[1]", "--potential", "[0]"])
    assert missing.value.code == 2
    capsys.readouterr()
    assert (
        cli.main(
            [
                "methods",
                "gibbs",
                "--reference",
                "{bad json}",
                "--potential",
                "[0]",
                "--candidate",
                "[1]",
            ]
        )
        == 1
    )
    assert json.loads(capsys.readouterr().out)["status"] == "error"
