"""Deterministic mathematical boundary probes; explanatory non-proof evidence."""

from __future__ import annotations

import math
from collections.abc import Sequence
from decimal import (
    ROUND_HALF_EVEN,
    Context,
    Decimal,
    DivisionByZero,
    InvalidOperation,
    Overflow,
    localcontext,
)
from fractions import Fraction
from numbers import Real
from typing import Any

from fep_formal._paths import FepFormalError


class BoundaryProbeError(ValueError, FepFormalError):
    """A probability, support, or floating-point range contract failed."""


def _finite_vector(values: Sequence[float], label: str) -> tuple[float, ...]:
    if not isinstance(values, Sequence) or not values:
        raise BoundaryProbeError(
            f"{label} needs a nonempty sequence of finite real numbers"
        )
    converted: list[float] = []
    for value in values:
        if isinstance(value, bool) or not isinstance(value, Real):
            raise BoundaryProbeError(
                f"{label} needs finite real numbers, excluding bool"
            )
        try:
            number = float(value)
        except (ValueError, OverflowError) as exc:
            raise BoundaryProbeError(f"{label} exceeds the finite float range") from exc
        if not math.isfinite(number):
            raise BoundaryProbeError(f"{label} needs finite real numbers")
        converted.append(number)
    return tuple(converted)


def _finite_law(values: Sequence[float], label: str) -> tuple[float, ...]:
    law = _finite_vector(values, label)
    if any(mass < 0 or mass > 1 + 1e-12 for mass in law) or not math.isclose(
        math.fsum(law), 1, rel_tol=0, abs_tol=1e-12
    ):
        raise BoundaryProbeError(f"{label} must be normalized and nonnegative")
    return law


def _law_potential(
    law: Sequence[float], potential: Sequence[float], label: str
) -> tuple[tuple[float, ...], tuple[float, ...]]:
    masses = _finite_law(law, label)
    values = _finite_vector(potential, "potential")
    if len(masses) != len(values):
        raise BoundaryProbeError("law and potential need equal nonempty supports")
    return masses, values


def _finite_float(value: Fraction | Decimal, label: str) -> float:
    try:
        result = float(value)
    except (ValueError, OverflowError) as exc:
        raise BoundaryProbeError(f"{label} exceeds the finite float range") from exc
    if not math.isfinite(result):
        raise BoundaryProbeError(f"{label} exceeds the finite float range")
    return result


def _decimal_fraction(value: Fraction) -> Decimal:
    return Decimal(value.numerator) / Decimal(value.denominator)


def _gibbs_context() -> Context:
    # Binary64 inputs span about 632 decimal orders when a subnormal mass
    # weights an extreme potential. Near-one logarithms also need the small
    # mass tail retained before cancellation. 700 digits cover both; 80 would
    # silently erase representable partition/KL values at those boundaries.
    return Context(
        prec=700,
        rounding=ROUND_HALF_EVEN,
        Emin=-999999,
        Emax=999999,
        traps=[InvalidOperation, DivisionByZero, Overflow],
    )


def _fraction_expectation(
    masses: Sequence[Fraction], values: Sequence[Fraction]
) -> Fraction:
    return sum(
        (mass * value for mass, value in zip(masses, values, strict=True)), Fraction(0)
    )


def finite_expectation(law: Sequence[float], potential: Sequence[float]) -> float:
    """Sum supplied binary-float masses times potentials, rounding only the result.

    Laws must sum to one within ``1e-12``; accepted masses are used literally.
    Exact rational accumulation preserves subnormal products and cancellation.
    An unrepresentable final result raises :class:`BoundaryProbeError`.
    """
    masses, values = _law_potential(law, potential, "law")
    return _finite_float(
        _fraction_expectation(
            tuple(map(Fraction.from_float, masses)),
            tuple(map(Fraction.from_float, values)),
        ),
        "finite expectation",
    )


def _log_tilt(
    reference: Sequence[Fraction], potential: Sequence[Fraction]
) -> tuple[Fraction, Decimal, tuple[Decimal | None, ...], tuple[float, ...]]:
    """Center before adding log masses; callers supply the Decimal context."""
    center = max(
        value for mass, value in zip(reference, potential, strict=True) if mass
    )
    weights = tuple(
        _decimal_fraction(mass).ln() + _decimal_fraction(value - center)
        if mass
        else None
        for mass, value in zip(reference, potential, strict=True)
    )
    weight_center = max(value for value in weights if value is not None)
    partition = sum(
        ((value - weight_center).exp() for value in weights if value is not None),
        Decimal(0),
    )
    centered_log_partition = weight_center + partition.ln()
    log_tilt = tuple(
        value - centered_log_partition if value is not None else None
        for value in weights
    )
    optimizer = tuple(
        float(value.exp()) if value is not None else 0.0 for value in log_tilt
    )
    return center, centered_log_partition, log_tilt, optimizer


def log_partition(reference: Sequence[float], potential: Sequence[float]) -> float:
    """Evaluate ``log(sum(q_i * exp(v_i)))`` stably on positive reference support.

    Accepted reference masses are used literally. Zero-reference potentials
    cannot determine the numerical center. The result is numerical, not proof.
    """
    masses, values = _law_potential(reference, potential, "reference")
    with localcontext(_gibbs_context()):
        center, centered, _, _ = _log_tilt(
            tuple(map(Fraction.from_float, masses)),
            tuple(map(Fraction.from_float, values)),
        )
        return _finite_float(_decimal_fraction(center) + centered, "log partition")


def exponential_tilt(
    reference: Sequence[float], potential: Sequence[float]
) -> tuple[float, ...]:
    """Return normalized Gibbs weights, with true zero reference atoms preserved.

    A positive mathematical weight can round to zero. Use
    :func:`gibbs_duality_diagnostics` to distinguish that underflow from a true
    support boundary; KL against the rounded weights can be misleading.
    """
    masses, values = _law_potential(reference, potential, "reference")
    with localcontext(_gibbs_context()):
        return _log_tilt(
            tuple(map(Fraction.from_float, masses)),
            tuple(map(Fraction.from_float, values)),
        )[3]


def gibbs_duality_diagnostics(
    candidate: Sequence[float],
    reference: Sequence[float],
    potential: Sequence[float],
) -> dict[str, Any]:
    """Compare finite Gibbs duality quantities with explicit numerical boundaries.

    Accepted candidate/reference laws are normalized by their exact binary
    rational mass sums. Original sums and residuals are reported. The gap is
    evaluated with centered 700-digit arithmetic; its KL comparison uses analytic
    log weights, never the underflow-truncated optimizer. True support failure
    uses JSON-safe infinity strings and leaves identity comparisons unset.
    Finite outputs outside binary64 range raise :class:`BoundaryProbeError`.
    Neither the residual nor its roundoff allowance certifies a Lean theorem.
    """
    reference_values, values = _law_potential(reference, potential, "reference")
    candidate_values = _finite_law(candidate, "candidate")
    if len(candidate_values) != len(reference_values):
        raise BoundaryProbeError("candidate and reference need equal nonempty supports")
    p_raw = tuple(map(Fraction.from_float, candidate_values))
    q_raw = tuple(map(Fraction.from_float, reference_values))
    p_sum, q_sum = sum(p_raw), sum(q_raw)
    p = tuple(mass / p_sum for mass in p_raw)
    q = tuple(mass / q_sum for mass in q_raw)
    v = tuple(map(Fraction.from_float, values))
    zeros = [index for index, mass in enumerate(q) if not mass]
    outside = [index for index in zeros if p[index]]
    sums = {
        "candidate": math.fsum(candidate_values),
        "reference": math.fsum(reference_values),
    }
    with localcontext(_gibbs_context()):
        center, centered_partition, log_tilt, optimizer = _log_tilt(q, v)
        expectation = _fraction_expectation(p, v)
        centered_expectation = _fraction_expectation(
            p, tuple(value - center for value in v)
        )
        report: dict[str, Any] = {
            "evidence_boundary": "Numerical non-proof diagnostics; no native or scientific acceptance.",
            "input_mass_sums": sums,
            "input_mass_residuals": {name: mass - 1.0 for name, mass in sums.items()},
            "normalization_convention": (
                "Diagnostics normalize accepted candidate/reference masses by their exact "
                "binary rational sums; scalar helpers use supplied masses literally."
            ),
            "reference_zero_indices": zeros,
            "candidate_outside_reference_indices": outside,
            "tilt_underflow_indices": [
                index for index, mass in enumerate(q) if mass and optimizer[index] == 0
            ],
            "optimizer": list(optimizer),
            "log_partition": _finite_float(
                _decimal_fraction(center) + centered_partition, "log partition"
            ),
            "expected_potential": _finite_float(expectation, "expected potential"),
            "centered_log_partition": _finite_float(
                centered_partition, "centered log partition"
            ),
            "centered_expected_potential": _finite_float(
                centered_expectation, "centered expected potential"
            ),
        }
        if outside:
            report.update(
                kl_candidate_reference="infinity",
                dv_objective="-infinity",
                duality_gap="infinity",
                kl_candidate_log_tilt="infinity",
                identity_residual=None,
                roundoff_allowance=None,
                identity_within_roundoff=None,
            )
            return report
        kl = Decimal(0)
        kl_tilt = Decimal(0)
        for index, mass in enumerate(p):
            if mass:
                weight = _decimal_fraction(mass)
                log_mass = weight.ln()
                kl += weight * (log_mass - _decimal_fraction(q[index]).ln())
                log_optimizer = log_tilt[index]
                assert log_optimizer is not None  # positive p has positive q above
                kl_tilt += weight * (log_mass - log_optimizer)
        gap = centered_partition - _decimal_fraction(centered_expectation) + kl
        residual = gap - kl_tilt
        report.update(
            kl_candidate_reference=_finite_float(kl, "candidate/reference KL"),
            dv_objective=_finite_float(
                _decimal_fraction(expectation) - kl, "DV objective"
            ),
            duality_gap=_finite_float(gap, "duality gap"),
            kl_candidate_log_tilt=_finite_float(kl_tilt, "candidate/log-tilt KL"),
            identity_residual=_finite_float(residual, "identity residual"),
        )
        allowance = 8 * math.fsum(
            math.ulp(report[key])
            for key in (
                "centered_log_partition",
                "centered_expected_potential",
                "kl_candidate_reference",
                "duality_gap",
                "kl_candidate_log_tilt",
            )
        )
        report.update(
            roundoff_allowance=allowance,
            identity_within_roundoff=abs(report["identity_residual"]) <= allowance,
        )
        return report


def bernoulli_fisher(parameter: float) -> float:
    """Evaluate the regular interior Bernoulli Fisher weight; reject singular endpoints."""
    if not math.isfinite(parameter) or not 0 < parameter < 1:
        raise BoundaryProbeError("Bernoulli Fisher needs 0 < p < 1")
    information = 1 / (parameter * (1 - parameter))
    if not math.isfinite(information):
        raise BoundaryProbeError(
            "interior Bernoulli Fisher exceeds the representable float range"
        )
    return information


def _law_pair(p: Sequence[float], q: Sequence[float]) -> None:
    if not p or len(p) != len(q):
        raise BoundaryProbeError("law comparison needs equal nonempty supports")
    for law in (p, q):
        if any(not math.isfinite(x) or x < 0 for x in law) or not math.isclose(
            math.fsum(law), 1, rel_tol=0, abs_tol=1e-12
        ):
            raise BoundaryProbeError("numeric law must be normalized and nonnegative")


def finite_kl_totalized(p: Sequence[float], q: Sequence[float]) -> float:
    """Mirror q*klFun(p/q), with totalized division, for an explanatory probe."""
    _law_pair(p, q)
    terms = []
    for source, reference in zip(p, q, strict=True):
        if reference == 0:
            terms.append(0.0)
        elif source == 0:
            terms.append(reference)
        else:
            # Algebraically the same supported integrand without ratio overflow.
            log_ratio = math.log(source) - math.log(reference)
            terms.append(math.fsum((source * log_ratio, -source, reference)))
    return math.fsum(terms)


def extended_kl(p: Sequence[float], q: Sequence[float]) -> float:
    """Conventional extended-real discrete KL with its support-failure boundary."""
    _law_pair(p, q)
    if any(
        source > 0 and reference == 0 for source, reference in zip(p, q, strict=True)
    ):
        return math.inf
    return math.fsum(
        source * (math.log(source) - math.log(reference))
        for source, reference in zip(p, q, strict=True)
        if source > 0
    )


def evaluate_boundary_probes() -> list[dict[str, Any]]:
    """Expose four finite diagnostic examples without claiming native verification."""
    extended_boundary = extended_kl((1.0, 0.0), (0.0, 1.0))
    law = [1 / 3, 1 / 3, 1 / 3]
    tangent = [1, -1, 0]
    return [
        {
            "id": "bernoulli-interior",
            "parameters": [0.5, 0.25, 0.01],
            "fisher": [bernoulli_fisher(p) for p in (0.5, 0.25, 0.01)],
            "boundary": "p=0 and p=1 rejected; no regular Fisher endpoint is inferred",
            "reading_anchor": "fep_fep038.FEP038.fep038_fisherMetric",
        },
        {
            "id": "kl-support-boundary",
            "source": [1.0, 0.0],
            "reference": [0.0, 1.0],
            "totalized_finite_kl": finite_kl_totalized((1.0, 0.0), (0.0, 1.0)),
            "extended_discrete_kl": "infinity"
            if math.isinf(extended_boundary)
            else extended_boundary,
            "interpretation": "Finite totalized KL cannot be substituted for native KL at disjoint support.",
            "reading_anchor": "FEP.FiniteInformation.finiteKL_disjoint_pointMass_totalized",
        },
        {
            "id": "fisher-chart-degeneracy",
            "law": law,
            "redundant_logit_information": [
                [2 / 9 if i == j else -1 / 9 for j in range(3)] for i in range(3)
            ],
            "logit_null_direction": [1, 1, 1],
            "simplex_tangent": tangent,
            "law_coordinate_tangent_norm_squared": sum(
                v * v / p for v, p in zip(tangent, law, strict=True)
            ),
            "interpretation": (
                "The redundant common-logit offset is null; the law-coordinate "
                "metric sum(v_i^2/p_i) is positive on this nonzero mass-zero tangent. "
                "These are different coordinate representations of the same family."
            ),
            "reading_anchor": "src/fep_formal/formal/geometric_optimization.lean",
        },
        {
            "id": "descent-does-not-identify",
            "objective": "f(x,y)=x^2",
            "update": "(x,y) -> (x/2,y)",
            "initial_states": [[1, 0], [1, 9]],
            "energy_sequence": [4.0 ** (-step) for step in range(6)],
            "distinct_limit_states": [[0, 0], [0, 9]],
            "interpretation": (
                "Both trajectories decrease the same objective but retain distinct "
                "unobserved coordinates. Descent alone does not establish "
                "identifiability or a unique state."
            ),
            "reading_anchor": "fep-032 exact scalar convergence versus additional latent coordinates",
        },
    ]


def classical_mds(vectors: Sequence[Sequence[int]]) -> dict[str, Any]:
    """Deterministic two-dimensional classical MDS of binary feature assignments.

    Integer squared distances are authoritative. All derived arithmetic uses an
    80-digit Decimal context, a fixed largest-pivot Jacobi algorithm, and an
    explicit residual gate. Publication values are quantized to 24 decimal
    places with half-even rounding. Neither LAPACK nor platform libm determines
    these artifact bytes. Repeated axes remain interpretation-ambiguous.
    """
    if not vectors or not vectors[0]:
        raise BoundaryProbeError("MDS requires nonempty rows and coordinates")
    width = len(vectors[0])
    if any(
        len(row) != width
        or any(type(value) is not int or value not in (0, 1) for value in row)
        for row in vectors
    ):
        raise BoundaryProbeError("MDS needs equal-width binary integer vectors")
    count = len(vectors)
    squared = [
        [sum(a != b for a, b in zip(left, right, strict=True)) for right in vectors]
        for left in vectors
    ]
    arithmetic = Context(
        prec=80,
        rounding=ROUND_HALF_EVEN,
        Emin=-999999,
        Emax=999999,
        capitals=1,
        clamp=0,
        traps=[InvalidOperation, DivisionByZero, Overflow],
    )
    with localcontext(arithmetic):
        zero, one = Decimal(0), Decimal(1)
        divisor = Decimal(count)
        means = [
            sum((Decimal(value) for value in row), zero) / divisor for row in squared
        ]
        grand_mean = sum(means, zero) / divisor
        gram = [
            [
                -(Decimal(squared[i][j]) - means[i] - means[j] + grand_mean) / 2
                for j in range(count)
            ]
            for i in range(count)
        ]
        norm_bound = max(sum((abs(value) for value in row), zero) for row in gram)
        residual_limit = Decimal("1e-60") * max(norm_bound, one)
        matrix = [row[:] for row in gram]
        basis = [[one if i == j else zero for j in range(count)] for i in range(count)]
        iteration_limit = max(1, 100 * count * count)
        residual = zero
        iterations = 0
        for iteration in range(iteration_limit):
            candidates = [
                (abs(matrix[i][j]), i, j)
                for i in range(count)
                for j in range(i + 1, count)
            ]
            residual, p, q = (
                max(candidates, key=lambda item: (item[0], -item[1], -item[2]))
                if candidates
                else (zero, 0, 0)
            )
            if residual <= residual_limit:
                iterations = iteration
                break
            off = matrix[p][q]
            theta = (matrix[q][q] - matrix[p][p]) / (2 * off)
            tangent = (one if theta >= 0 else -one) / (
                abs(theta) + (one + theta * theta).sqrt()
            )
            cosine = one / (one + tangent * tangent).sqrt()
            sine = tangent * cosine
            matrix[p][p] -= tangent * off
            matrix[q][q] += tangent * off
            matrix[p][q] = matrix[q][p] = zero
            for row in range(count):
                if row not in (p, q):
                    left, right = matrix[row][p], matrix[row][q]
                    matrix[row][p] = matrix[p][row] = cosine * left - sine * right
                    matrix[row][q] = matrix[q][row] = sine * left + cosine * right
                left, right = basis[row][p], basis[row][q]
                basis[row][p] = cosine * left - sine * right
                basis[row][q] = sine * left + cosine * right
        else:
            raise BoundaryProbeError(
                "deterministic MDS Jacobi residual did not converge within its fixed cap"
            )
        order = sorted(range(count), key=lambda index: (-matrix[index][index], index))
        values = [matrix[index][index] for index in order]
        basis = [[row[index] for index in order] for row in basis]
        # A symmetric residual with every off-diagonal <= r has spectral norm
        # <= (n-1)*r. This conservative diagnostic adds an explicit factor64;
        # it classifies numerical zero/repetition, never scientific acceptance.
        threshold = 64 * count * residual_limit
        if any(value < -threshold for value in values):
            raise BoundaryProbeError(
                "binary Euclidean MDS has a materially negative eigenvalue"
            )
        positive = [index for index, value in enumerate(values) if value > threshold]
        clusters: list[list[int]] = []
        for index in positive:
            if clusters and abs(values[index] - values[clusters[-1][0]]) <= threshold:
                clusters[-1].append(index)
            else:
                clusters.append([index])
        oriented: list[tuple[Decimal, list[Decimal]]] = []
        ambiguity = []
        orientation_threshold = 64 * count * Decimal("1e-60")
        quantum = Decimal("1e-24")

        def serialized(value: Decimal) -> float:
            rounded = value.quantize(quantum)
            return float(rounded) if rounded else 0.0

        for cluster in clusters:
            projector = [
                [
                    sum((basis[i][axis] * basis[j][axis] for axis in cluster), zero)
                    for j in range(count)
                ]
                for i in range(count)
            ]
            canonical: list[list[Decimal]] = []
            for row_index in range(count):
                candidate = [projector[row][row_index] for row in range(count)]
                for _pass in range(2):
                    for previous in canonical:
                        dot = sum(
                            (
                                left_value * right_value
                                for left_value, right_value in zip(
                                    previous, candidate, strict=True
                                )
                            ),
                            zero,
                        )
                        candidate = [
                            value - dot * previous_value
                            for value, previous_value in zip(
                                candidate, previous, strict=True
                            )
                        ]
                norm = sum((value * value for value in candidate), zero).sqrt()
                if norm <= orientation_threshold:
                    continue
                candidate = [value / norm for value in candidate]
                pivot = max(
                    range(count), key=lambda index: (abs(candidate[index]), -index)
                )
                if candidate[pivot] < 0:
                    candidate = [-value for value in candidate]
                canonical.append(candidate)
                if len(canonical) == len(cluster):
                    break
            if len(canonical) != len(cluster):
                raise BoundaryProbeError(
                    "cannot orient the MDS eigenspace at numeric precision"
                )
            representative = sum((values[index] for index in cluster), zero) / len(
                cluster
            )
            oriented.extend((representative, vector) for vector in canonical)
            if len(cluster) > 1:
                ambiguity.append(
                    {
                        "axis_indices": [index + 1 for index in cluster],
                        "multiplicity": len(cluster),
                        "eigenvalue_representative": serialized(representative),
                        "interpretation": "Rotationally ambiguous eigenspace; row-order projector basis is a display convention.",
                    }
                )
        points = [[zero, zero] for _row in vectors]
        for axis, (value, vector) in enumerate(oriented[:2]):
            for index in range(count):
                points[index][axis] = vector[index] * value.sqrt()
        residuals: list[Decimal] = []
        total: list[int] = []
        for left_index in range(count):
            for right_index in range(left_index + 1, count):
                distance = Decimal(squared[left_index][right_index]).sqrt()
                projected = sum(
                    (
                        (points[left_index][axis] - points[right_index][axis]) ** 2
                        for axis in range(2)
                    ),
                    zero,
                ).sqrt()
                residuals.append((distance - projected) ** 2)
                total.append(squared[left_index][right_index])
        denominator = sum(total)
        stress = (sum(residuals, zero) / denominator).sqrt() if denominator else zero
        positive_sum = sum((value for value, _vector in oriented), zero)
        return {
            "method": "classical MDS on explicit binary feature Euclidean distances",
            "distance_formula": "d(i,j)^2 = sum_k (z_ik - z_jk)^2 = Hamming mismatch count",
            "gram_formula": "B = -H D^2 H / 2; H = I - 11^T/n",
            "squared_distances": squared,
            "coordinates": [[serialized(value) for value in row] for row in points],
            "distances": [
                [serialized(Decimal(value).sqrt()) for value in row] for row in squared
            ],
            "eigenvalues": [serialized(value) for value in values],
            "eigenvalues_decimal": [format(value, ".60E") for value in values],
            "positive_rank": len(positive),
            "display_axis_eigenvalues": [
                serialized(value) for value, _vector in oriented[:2]
            ]
            + [0.0] * max(0, 2 - len(oriented)),
            "explained_positive_inertia": serialized(
                sum((value for value, _vector in oriented[:2]), zero) / positive_sum
            )
            if positive_sum
            else 0.0,
            "normalized_stress": serialized(stress),
            "stress_formula": "sqrt(sum_{i<j}(d_ij-dhat_ij)^2 / sum_{i<j}d_ij^2); zero denominator => 0",
            "numerical_zero_threshold": format(threshold, ".60E"),
            "threshold_scope": "64*n*Jacobi residual limit; spectral residual bound <=(n-1)*limit. Numerical rank/repetition diagnostic, not scientific/proof acceptance.",
            "eigensolver": {
                "algorithm": "80-digit Decimal largest-offdiagonal-pivot Jacobi; first row/column break exact ties",
                "iterations": iterations,
                "iteration_limit": iteration_limit,
                "offdiagonal_residual": format(residual, ".60E"),
                "residual_limit": format(residual_limit, ".60E"),
                "gram_norm_upper_bound": format(norm_bound, ".60E"),
                "converged": residual <= residual_limit,
            },
            "numerical_serialization": "Derived publication values: Decimal quantization to 24 decimal places, ROUND_HALF_EVEN, then IEEE float/JSON; full 60-decimal-exponent eigenspectrum retained separately. Exact binary vectors and integer squared distances are authoritative.",
            "eigenambiguity": ambiguity,
            "axis_convention": "Repeated-eigenspace projector columns, retained row order, reorthogonalized; greatest-absolute coordinate positive. Signs/orientations have no semantic meaning.",
            "zero_axis_policy": "Missing positive axes are identically zero; identical rows coincide. No fabricated spread or jitter.",
            "interpretation": "Distances compare authored feature assignments. They do not establish theorem equivalence, proof transfer, empirical similarity, or learned semantic embedding.",
        }
