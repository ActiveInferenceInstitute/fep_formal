"""Concrete H2 diagnostics consumed only by the existing witness registry.

All operands are evaluated here; these diagnostics are neither native proof
receipts nor simulations of a GNN backend.
"""

from __future__ import annotations

import math
from fractions import Fraction

from .numerical_witnesses import (
    NumericalCheck,
    NumericalWitness,
    WitnessColumn,
    WitnessPlot,
    WitnessRow,
)


def scalar_terminal_witness() -> NumericalWitness:
    """Evaluate the exact selected H2.7 scalar carrier and local gradient line."""
    decay = math.exp(-1.0)
    prior_mean, prior_variance, noise_variance = 0.0, 1.0, 1.0
    predicted_mean = decay * prior_mean
    predicted_variance = decay**2 * prior_variance + (1.0 - decay**2)
    gain = predicted_variance / (predicted_variance + noise_variance)
    posterior_mean = predicted_mean + gain * (0.0 - predicted_mean)
    posterior_variance = (
        1.0 - gain
    ) ** 2 * predicted_variance + gain**2 * noise_variance
    surprisal = 0.5 * math.log(2.0 * math.pi * (predicted_variance + noise_variance))
    recognition_mean = 1.5
    displacement = recognition_mean - posterior_mean
    fisher = 1.0 / posterior_variance
    differential = displacement / posterior_variance
    natural_gradient = differential / fisher

    def vfe(mean: float) -> float:
        return (mean - posterior_mean) ** 2 / (2.0 * posterior_variance) + surprisal

    times = (0.0, 0.25, 0.5, 1.0)
    means = tuple(recognition_mean - t * natural_gradient for t in times)
    rows = tuple(
        WitnessRow((t, mean, vfe(mean), vfe(mean) - surprisal))
        for t, mean in zip(times, means, strict=True)
    )
    step = 1e-5
    numerical_derivative = (
        vfe(recognition_mean - step * natural_gradient)
        - vfe(recognition_mean + step * natural_gradient)
    ) / (2.0 * step)
    false_risk = decay**2 * posterior_variance + (1.0 - decay**2)
    true_risk = decay**2 * posterior_variance + 2.0 * (1.0 - decay**2)
    namespace = "FEPComposed.SmoothReferenceKernel."
    return NumericalWitness(
        id="h2-scalar-terminal",
        family="horizon2-scalar-terminal",
        scope="horizon2",
        title="Selected scalar Gaussian posterior, VFE and one-step action risk",
        theorem_mirrors=tuple(
            namespace + name
            for name in (
                "selectedPredictionBelief_eq_prior",
                "selectedPosterior_mean",
                "selectedPosterior_variance",
                "meanNaturalGradient_eq_displacement",
                "gaussianVariationalFreeEnergy_naturalGradientFlow_hasDerivAt",
                "selectedControl_false_risk",
                "selectedControl_true_risk",
                "selectedControl_false_strictlyBetter",
            )
        ),
        invariant="The selected stationary prior updates to variance one half; its local natural-gradient line decreases VFE and base diffusion has lower one-step risk.",
        parameters=(
            ("rate", 1.0),
            ("diffusion_variance_rate", 2.0),
            ("duration", 1.0),
            ("observation", 0.0),
            ("posterior_mean", posterior_mean),
            ("posterior_variance", posterior_variance),
            ("evidence_surprisal", surprisal),
            ("base_risk", false_risk),
            ("alternative_risk", true_risk),
        ),
        columns=tuple(
            WitnessColumn(key, label)
            for key, label in (
                ("time", "Local line parameter"),
                ("mean", "Recognition mean"),
                ("vfe", "Variational free energy"),
                ("kl_gap", "Recognition-to-posterior KL"),
            )
        ),
        rows=rows,
        checks=(
            NumericalCheck(
                "stationary-prediction-mean", "eq", predicted_mean, 0.0, 0.0
            ),
            NumericalCheck(
                "stationary-prediction-variance", "eq", predicted_variance, 1.0, 1e-15
            ),
            NumericalCheck("posterior-mean", "eq", posterior_mean, 0.0, 0.0),
            NumericalCheck("posterior-variance", "eq", posterior_variance, 0.5, 1e-15),
            NumericalCheck(
                "natural-gradient", "eq", natural_gradient, displacement, 1e-15
            ),
            NumericalCheck(
                "local-vfe-derivative",
                "eq",
                numerical_derivative,
                -(displacement**2) / posterior_variance,
                1e-8,
            ),
            NumericalCheck(
                "posterior-vfe-gap", "eq", vfe(posterior_mean) - surprisal, 0.0, 0.0
            ),
            NumericalCheck(
                "base-risk-formula", "eq", false_risk, 1.0 - 0.5 * decay**2, 1e-15
            ),
            NumericalCheck(
                "alternative-risk-formula", "eq", true_risk, 2.0 - 1.5 * decay**2, 1e-15
            ),
            NumericalCheck(
                "base-action-strictly-better",
                "predicate",
                false_risk < true_risk,
                True,
                0.0,
            ),
        ),
        boundary_behavior="At the posterior mean the KL gap and natural gradient vanish. The plotted path is the theorem's local straight line, not a globally integrated gradient-flow ODE.",
        boundary_observed=means[-1] == posterior_mean and vfe(means[-1]) == surprisal,
        plot=WitnessPlot("line", "time", ("vfe", "kl_gap")),
        formal_alignment="theorem_instance",
    )


Matrix = tuple[tuple[float, ...], ...]
RationalMatrix = tuple[tuple[Fraction, ...], ...]


def _inverse(matrix: RationalMatrix) -> RationalMatrix:
    """Exact Gauss-Jordan inverse, with singular matrices rejected."""
    n = len(matrix)
    rows = [
        list(row) + [Fraction(i == j) for j in range(n)] for i, row in enumerate(matrix)
    ]
    for column in range(n):
        pivot = next((i for i in range(column, n) if rows[i][column]), None)
        if pivot is None:
            raise ValueError("singular witness matrix")
        rows[column], rows[pivot] = rows[pivot], rows[column]
        divisor = rows[column][column]
        rows[column] = [value / divisor for value in rows[column]]
        for i in range(n):
            if i != column:
                scale = rows[i][column]
                rows[i] = [
                    a - scale * b for a, b in zip(rows[i], rows[column], strict=True)
                ]
    return tuple(tuple(row[n:]) for row in rows)


def _multiply(left: Matrix, right: Matrix) -> Matrix:
    return tuple(
        tuple(
            sum(left[i][k] * right[k][j] for k in range(len(right)))
            for j in range(len(right[0]))
        )
        for i in range(len(left))
    )


def _fin4_transition(
    time: float, modes: tuple[tuple[int, ...], ...], eigenvalues: tuple[int, ...]
) -> Matrix:
    return tuple(
        tuple(
            sum(
                math.exp(-rate * time)
                * vector[i]
                * vector[j]
                / sum(x * x for x in vector)
                for vector, rate in zip(modes, eigenvalues, strict=True)
            )
            for j in range(4)
        )
        for i in range(4)
    )


def fin4_blanket_witness() -> NumericalWitness:
    """Evaluate the accepted precision, its inverse and actual eigenmode dynamics."""
    raw = ((4, -1, -1, 0), (-1, 4, 0, -1), (-1, 0, 4, -1), (0, -1, -1, 4))
    precision = tuple(tuple(Fraction(x) for x in row) for row in raw)
    covariance = _inverse(precision)
    identity = tuple(
        tuple(
            sum(precision[i][k] * covariance[k][j] for k in range(4)) for j in range(4)
        )
        for i in range(4)
    )
    exact_inverse = all(
        identity[i][j] == Fraction(i == j) for i in range(4) for j in range(4)
    )
    endpoint_precision = tuple(tuple(precision[i][j] for j in (0, 3)) for i in (0, 3))
    endpoint_covariance = _inverse(endpoint_precision)
    perturbed_covariance = _inverse(
        ((Fraction(4), Fraction(1)), (Fraction(1), Fraction(4)))
    )
    modes = ((1, 1, 1, 1), (1, 0, 0, -1), (0, 1, -1, 0), (1, -1, -1, 1))
    eigenvalues = (2, 4, 4, 6)
    eigenmode_exact = all(
        sum(precision[i][j] * vector[j] for j in range(4)) == rate * vector[i]
        for vector, rate in zip(modes, eigenvalues, strict=True)
        for i in range(4)
    )
    sigma = tuple(tuple(float(x) for x in row) for row in covariance)

    def evolution(time: float) -> Matrix:
        return _fin4_transition(time, modes, eigenvalues)

    left, right = evolution(0.25), evolution(0.75)
    composed, total = _multiply(left, right), evolution(1.0)
    semigroup_error = max(
        abs(composed[i][j] - total[i][j]) for i in range(4) for j in range(4)
    )
    rows = []
    stationarity_error = 0.0
    projection_error = 0.0
    minimum_positive_eigenvalue = 1.0
    for time in (0.0, 0.25, 1.0, 4.0):
        transition = evolution(time)
        evolved = _multiply(_multiply(transition, sigma), transition)
        # Integrate each diffusion mode independently of the computed transition.
        # Stationarity below can therefore expose incorrect transition rates.
        eigen_noise = tuple(
            -math.expm1(-2 * rate * time) / rate for rate in eigenvalues
        )
        noise = tuple(
            tuple(
                sum(
                    variance * vector[i] * vector[j] / sum(x * x for x in vector)
                    for vector, variance in zip(modes, eigen_noise, strict=True)
                )
                for j in range(4)
            )
            for i in range(4)
        )
        stationarity_error = max(
            stationarity_error,
            *(
                abs(evolved[i][j] + noise[i][j] - sigma[i][j])
                for i in range(4)
                for j in range(4)
            ),
        )
        projected_noise = sum(noise[i][j] / 4.0 for i in range(4) for j in range(4))
        projection_error = max(
            projection_error, abs(projected_noise - 0.5 * (1.0 - math.exp(-4 * time)))
        )
        if time > 0:
            minimum_positive_eigenvalue = min(minimum_positive_eigenvalue, *eigen_noise)
        rows.append(WitnessRow((time, noise[0][0], projected_noise, min(eigen_noise))))
    namespace = "FEP.Fin4GaussianSemigroup."
    return NumericalWitness(
        id="h2-fin4-blanket",
        family="horizon2-fin4-blanket",
        scope="horizon2",
        title="Exact Fin4 precision blanket and Gaussian semigroup diagnostics",
        theorem_mirrors=tuple(
            namespace + name
            for name in (
                "K_mul_Sigma",
                "Sigma_mul_K",
                "K_posDef",
                "Sigma_external_internal",
                "K_eigenmode_two",
                "K_eigenmode_four_external",
                "K_eigenmode_four_sensory",
                "K_eigenmode_six",
                "transition_add",
                "stationaryLaw_invariant",
                "projectedTransition_eq_scalarOU",
            )
        )
        + (
            "FEP.GaussianPrecisionConditioning.precisionZero_covarianceNonzero_condIndep",
            "FEP.GaussianPrecisionConditioning.perturbedEndpoint_external_internal_covariance",
        ),
        invariant="The exact precision has zero external/internal entry despite marginal covariance 1/24; conditioning removes that covariance and the eigenmode transition preserves the stationary Gaussian.",
        parameters=(
            ("axis_order", "external,sensory,active,internal"),
            ("marginal_endpoint_covariance", float(covariance[0][3])),
            ("conditional_endpoint_covariance", float(endpoint_covariance[0][1])),
            ("perturbed_conditional_covariance", float(perturbed_covariance[0][1])),
        ),
        columns=tuple(
            WitnessColumn(key, label)
            for key, label in (
                ("time", "Time"),
                ("external_noise_variance", "External transition variance"),
                ("projected_noise_variance", "All-ones projected transition variance"),
                (
                    "minimum_noise_eigenvalue",
                    "Minimum transition covariance eigenvalue",
                ),
            )
        ),
        rows=tuple(rows),
        checks=(
            NumericalCheck("exact-inverse", "predicate", exact_inverse, True, 0.0),
            NumericalCheck(
                "positive-precision-eigenvalues",
                "predicate",
                eigenmode_exact and min(eigenvalues) > 0,
                True,
                0.0,
            ),
            NumericalCheck(
                "marginal-covariance",
                "predicate",
                covariance[0][3] == Fraction(1, 24),
                True,
                0.0,
            ),
            NumericalCheck(
                "conditional-covariance-zero",
                "predicate",
                endpoint_covariance[0][1] == 0,
                True,
                0.0,
            ),
            NumericalCheck(
                "conditional-variance",
                "predicate",
                endpoint_covariance[0][0] == Fraction(1, 4),
                True,
                0.0,
            ),
            NumericalCheck(
                "perturbed-covariance",
                "predicate",
                perturbed_covariance[0][1] == Fraction(-1, 15),
                True,
                0.0,
            ),
            NumericalCheck("semigroup-composition", "eq", semigroup_error, 0.0, 1e-12),
            NumericalCheck(
                "stationary-covariance", "eq", stationarity_error, 0.0, 1e-12
            ),
            NumericalCheck(
                "all-ones-scalar-projection", "eq", projection_error, 0.0, 1e-12
            ),
            NumericalCheck(
                "positive-time-noise",
                "predicate",
                minimum_positive_eigenvalue > 0.0,
                True,
                0.0,
            ),
        ),
        boundary_behavior="At time zero the transition noise is exactly zero (not positive definite); at positive sampled times its eigenvalues are positive. A unit endpoint precision perturbation yields conditional covariance -1/15.",
        boundary_observed=all(value == 0.0 for value in rows[0].values[1:])
        and perturbed_covariance[0][1] != 0,
        plot=WitnessPlot(
            "line", "time", ("external_noise_variance", "projected_noise_variance")
        ),
        formal_alignment="theorem_instance",
    )
