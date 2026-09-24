"""H3.6S feasibility spike: exact fixture round-trip and synthetic recovery.

Slice-local executable consumer of the exported typed Fin4 carrier parameters
(mirrored from accepted H2 Lean declarations; no model registry). Every
tolerance, seed, and sample size below was frozen before the first recovery
run (preregistration discipline):

- exact rational fixture round-trip bound to theorem-owned values;
- two identifiable synthetic recovery settings with frozen tolerances;
- mandatory rejections: reordered parameters, missing units, stale digests;
- one misspecified-covariance negative control.

This spike is NOT the H3.6S acceptance owner. Promotion into
`src/fep_lean/verification/h3_reference_study.py` with the
`tests/test_h3_reference_study.py` contract remains an orchestrator-owned
H3.6S step; no acceptance or exit-gate verdict is issued here.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from fractions import Fraction
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------------------
# Frozen protocol constants (preregistered before the first recovery run).
# ---------------------------------------------------------------------------

BASE_SEED = 20260911
N_PAIRS = 200_000
SETTING_A_DELTA = 0.25
SETTING_B_DELTA = 0.5
RATE_REL_TOL = 0.05
K_MAX_ENTRY_TOL = 0.2
DIFFUSION_ABS_TOL = 0.25
COEF_ABS_TOL = 0.02
RESIDUAL_ABS_TOL = 0.03
INTERCEPT_ABS_TOL = 0.02
FLOAT_TOL = 1e-12
MISSPECIFICATION_DETECT_MIN = 0.005

AXES = ("external", "sensory", "active", "internal")

# Digest pins at research/h3-case-study base b992032: the accepted H2 carrier
# sources (src and lean projections are byte-identical) and the H2.7 terminal
# receipt. A mismatch rejects the run (stale theorem/source digests).
PINNED_SOURCES: dict[str, str] = {
    "src/fep_lean/formal/fin4_gaussian_semigroup.lean": (
        "a7c14d2fdeb44c61ffa4012d6eccc8d00051be916ab536e2658f4ef3652d260c"
    ),
    "src/fep_lean/formal/gaussian_precision_conditioning.lean": (
        "64afcf45cf2ef44b78db7e5b2fb2de02bd3af80cefda888523baae1043b37c38"
    ),
    "src/fep_lean/formal/compositions/smooth_reference_kernel.lean": (
        "156464de9e7c33e16fa22bd6939fa64938b03ee4f5554fb3ecd48fbfaed6d397"
    ),
    "src/fep_lean/formal/compositions/gaussian_filter.lean": (
        "2b0ec699ab07e19800fb978157721e82420b650478479368aa3c4a7878ea156e"
    ),
    "src/fep_lean/formal/compositions/gaussian_control.lean": (
        "76b2e36f840682df5adac654456d2d94c81c636778fbcd1efa39bc3cbfe3d3f0"
    ),
    "specs/horizon-2-smooth-stochastic/readiness/terminal-acceptance.json": (
        "dac2dac5dacef74d48657fed2e5f6e297635d8345e84fc9b62be02bfbbf05b45"
    ),
}

# Exact Fin4 precision, axis order external, sensory, active, internal.
# Mirror of `FEP.Fin4GaussianSemigroup.K` (fin4_gaussian_semigroup.lean:85-117)
# and the accepted witness raw matrix (_horizon_numerical_witnesses.py:195).
EXACT_K: tuple[tuple[Fraction, ...], ...] = (
    (Fraction(4), Fraction(-1), Fraction(-1), Fraction(0)),
    (Fraction(-1), Fraction(4), Fraction(0), Fraction(-1)),
    (Fraction(-1), Fraction(0), Fraction(4), Fraction(-1)),
    (Fraction(0), Fraction(-1), Fraction(-1), Fraction(4)),
)

# Named derived covariance entries. Mirror of
# `FEP.Fin4GaussianSemigroup.Sigma_eq_entries` (fin4_gaussian_semigroup.lean:257-274).
EXACT_SIGMA: tuple[tuple[Fraction, ...], ...] = (
    (Fraction(7, 24), Fraction(1, 12), Fraction(1, 12), Fraction(1, 24)),
    (Fraction(1, 12), Fraction(7, 24), Fraction(1, 24), Fraction(1, 12)),
    (Fraction(1, 12), Fraction(1, 24), Fraction(7, 24), Fraction(1, 12)),
    (Fraction(1, 24), Fraction(1, 12), Fraction(1, 12), Fraction(7, 24)),
)

# Exact eigenmodes and precision rates. Mirror of `K_eigenmode_two`,
# `K_eigenmode_four_external`, `K_eigenmode_four_sensory`, `K_eigenmode_six`
# (fin4_gaussian_semigroup.lean:172/179/187/195) and the accepted witness
# (_horizon_numerical_witnesses.py:212-213).
EXACT_MODES: tuple[tuple[int, ...], ...] = (
    (1, 1, 1, 1),
    (1, 0, 0, -1),
    (0, 1, -1, 0),
    (1, -1, -1, 1),
)
EXACT_RATES: tuple[int, ...] = (2, 4, 4, 6)

# Exact seam values with sources:
# `K_external_internal` = 0 (fin4_gaussian_semigroup.lean:313);
# `Sigma_external_internal` = 1/24 (:317);
# `externalConditionalKernel_variance` = 1/4
# (gaussian_precision_conditioning.lean:215-217);
# `perturbedEndpoint_external_internal_covariance` = -1/15 (:959-961).
SEAM_EXTERNAL_INTERNAL_PRECISION = Fraction(0)
SEAM_MARGINAL_COVARIANCE = Fraction(1, 24)
SEAM_CONDITIONAL_VARIANCE = Fraction(1, 4)
SEAM_PERTURBED_COVARIANCE = Fraction(-1, 15)


class SpikeRejection(RuntimeError):
    """Raised when the executable must reject its inputs."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest_guard(root: Path) -> dict[str, str]:
    """Reject stale theorem/source digests (frozen-rejection boundary R3)."""
    observed = {
        relative: _sha256(root / relative)
        for relative in PINNED_SOURCES
        if (root / relative).is_file()
    }
    if set(observed) != set(PINNED_SOURCES):
        missing = sorted(set(PINNED_SOURCES) - set(observed))
        raise SpikeRejection(f"pinned source missing: {missing}")
    for relative, expected in PINNED_SOURCES.items():
        if observed[relative] != expected:
            raise SpikeRejection(f"stale source digest: {relative}")
    return observed


def _exact_inverse(
    matrix: tuple[tuple[Fraction, ...], ...],
) -> tuple[tuple[Fraction, ...], ...]:
    n = len(matrix)
    rows = [
        list(row) + [Fraction(i == j) for j in range(n)] for i, row in enumerate(matrix)
    ]
    for col in range(n):
        pivot = next((r for r in range(col, n) if rows[r][col] != 0), None)
        if pivot is None:
            raise ValueError("singular matrix")
        rows[col], rows[pivot] = rows[pivot], rows[col]
        factor = rows[col][col]
        rows[col] = [value / factor for value in rows[col]]
        for r in range(n):
            if r != col and rows[r][col] != 0:
                scale = rows[r][col]
                rows[r] = [a - scale * b for a, b in zip(rows[r], rows[col])]
    return tuple(tuple(row[n:]) for row in rows)


def validate_typed_parameters() -> dict[str, bool]:
    """Reordered/axis-permuted parameters must be rejected (boundary R1)."""
    outcomes: dict[str, bool] = {}
    # R1a: pairing the all-ones eigenmode with the rate-6 entry of a reordered
    # rate list must fail the eigenmode relation (K * ones = 2 * ones).
    ones = EXACT_MODES[0]
    product = tuple(sum(EXACT_K[i][j] * ones[j] for j in range(4)) for i in range(4))
    outcomes["reordered_rate_pairing_rejected"] = product != tuple(
        6 * coordinate for coordinate in ones
    )
    # R1b: transposing the external and sensory axes is not the accepted
    # carrier: the named covariance changes and the external/internal
    # precision seam breaks.
    order = (1, 0, 2, 3)
    permuted = tuple(
        tuple(EXACT_K[order[i]][order[j]] for j in range(4)) for i in range(4)
    )
    sigma_permuted = _exact_inverse(permuted)
    outcomes["axis_permutation_rejected"] = sigma_permuted != EXACT_SIGMA and permuted[
        0
    ][3] != Fraction(0)
    return outcomes


def raw_unit_calibration(
    raw: Fraction, offset: Fraction | None, scale: Fraction | None
) -> Fraction:
    """Positive affine raw-unit bridge; missing or nonpositive units reject (R2)."""
    if offset is None or scale is None:
        raise SpikeRejection("missing unit calibration")
    if scale <= 0:
        raise SpikeRejection("nonpositive raw scale")
    standardized = (raw - offset) / scale
    if offset + scale * standardized != raw:
        raise SpikeRejection("raw-unit round trip failed")
    return standardized


def validate_raw_units() -> dict[str, bool]:
    outcomes: dict[str, bool] = {}
    standardized = raw_unit_calibration(Fraction(13, 7), Fraction(-3), Fraction(2))
    outcomes["round_trip_exact"] = Fraction(-3) + Fraction(
        2
    ) * standardized == Fraction(13, 7)
    for offset, scale, label in (
        (None, Fraction(2), "missing_offset"),
        (Fraction(0), None, "missing_scale"),
        (Fraction(0), Fraction(0), "zero_scale"),
        (Fraction(0), Fraction(-1), "negative_scale"),
    ):
        try:
            raw_unit_calibration(Fraction(1), offset, scale)
        except SpikeRejection:
            outcomes[f"reject_{label}"] = True
        else:
            outcomes[f"reject_{label}"] = False
    return outcomes


def fixture_roundtrip() -> dict[str, object]:
    """Exact rational fixture round-trip plus theorem-mirroring numerics."""
    exact_inverse = _exact_inverse(EXACT_K)
    identity_ok = all(
        sum(EXACT_K[i][k] * exact_inverse[k][j] for k in range(4)) == Fraction(i == j)
        for i in range(4)
        for j in range(4)
    )
    eigenmode_ok = all(
        sum(EXACT_K[i][j] * mode[j] for j in range(4)) == rate * mode[i]
        for mode, rate in zip(EXACT_MODES, EXACT_RATES, strict=True)
        for i in range(4)
    )
    endpoint_precision = (
        (EXACT_K[0][0], EXACT_K[0][3]),
        (EXACT_K[3][0], EXACT_K[3][3]),
    )
    endpoint_covariance = _exact_inverse(endpoint_precision)
    perturbed = _exact_inverse(((Fraction(4), Fraction(1)), (Fraction(1), Fraction(4))))
    exact_checks: dict[str, bool] = {
        "sigma_exact_inverse_matches_named": exact_inverse == EXACT_SIGMA,
        "K_mul_Sigma_identity": identity_ok,
        "K_eigenmode_exactness": eigenmode_ok,
        "K_external_internal_zero": EXACT_K[0][3] == SEAM_EXTERNAL_INTERNAL_PRECISION,
        "Sigma_external_internal_one_over_24": (
            EXACT_SIGMA[0][3] == SEAM_MARGINAL_COVARIANCE
        ),
        "conditional_covariance_zero": endpoint_covariance[0][1] == Fraction(0),
        "conditional_variance_one_quarter": (
            endpoint_covariance[0][0] == SEAM_CONDITIONAL_VARIANCE
        ),
        "perturbed_covariance_minus_one_fifteenth": (
            perturbed[0][1] == SEAM_PERTURBED_COVARIANCE
        ),
    }

    # Exact reconstruction from the theorem-owned eigenmodes: each mode v has
    # squared norm (4, 2, 2, 4), so
    # Sigma = sum_m (1/lambda_m) * v_m v_m^T / |v_m|^2 holds exactly in
    # rational arithmetic (witness lines 212-213 + Sigma_eq_entries).
    mode_norms_squared = (4, 2, 2, 4)
    exact_checks["eigenmodes_orthogonal_exact"] = all(
        sum(EXACT_MODES[a][k] * EXACT_MODES[b][k] for k in range(4)) == 0
        for a in range(4)
        for b in range(4)
        if a != b
    )
    stationary_from_rates = tuple(
        tuple(
            sum(
                Fraction(1, EXACT_RATES[m])
                * Fraction(EXACT_MODES[m][i] * EXACT_MODES[m][j], mode_norms_squared[m])
                for m in range(4)
            )
            for j in range(4)
        )
        for i in range(4)
    )
    exact_checks["stationary_covariance_from_rates"] = (
        stationary_from_rates == EXACT_SIGMA
    )

    u = np.array(
        [
            [float(Fraction(x, 1)) / math.sqrt(float(norm)) for x in mode]
            for mode, norm in zip(EXACT_MODES, (4, 2, 2, 4), strict=True)
        ],
        dtype=float,
    )
    rates = np.array([float(rate) for rate in EXACT_RATES], dtype=float)
    sigma = np.array(
        [[float(value) for value in row] for row in EXACT_SIGMA], dtype=float
    )

    def transition(time: float) -> np.ndarray:
        return np.asarray(u.T @ np.diag(np.exp(-rates * time)) @ u)

    def noise(time: float) -> np.ndarray:
        return np.asarray(
            u.T @ np.diag((1.0 - np.exp(-2.0 * rates * time)) / rates) @ u
        )

    semigroup_error = max(
        float(np.max(np.abs(transition(left) @ transition(right) - transition(total))))
        for left, right, total in ((0.5, 0.75, 1.25), (0.25, 4.0, 4.25))
    )
    stationarity_error = max(
        float(
            np.max(
                np.abs(
                    transition(time) @ sigma @ transition(time).T + noise(time) - sigma
                )
            )
        )
        for time in (0.25, 1.0, 4.0)
    )
    ones_full = np.ones(4)
    projected_error = max(
        abs(
            float(ones_full @ noise(time) @ ones_full) / 4.0
            - 0.5 * (1.0 - math.exp(-4.0 * time))
        )
        for time in (0.25, 1.0, 4.0)
    )

    return {
        **exact_checks,
        "semigroup_composition_error": semigroup_error,
        "stationary_covariance_error": stationarity_error,
        "scalar_projection_error": projected_error,
        "semigroup_within_tolerance": semigroup_error <= FLOAT_TOL,
        "stationarity_within_tolerance": stationarity_error <= FLOAT_TOL,
        "scalar_projection_within_tolerance": projected_error <= FLOAT_TOL,
    }


def _simulate_pairs(
    rng: np.random.Generator, count: int, delta: float
) -> tuple[np.ndarray, np.ndarray]:
    """I.i.d. stationary pairs (x_t, x_{t+delta}) under the exact model."""
    sigma = np.array([[float(value) for value in row] for row in EXACT_SIGMA])
    u = np.array(
        [
            [float(x) / math.sqrt(float(norm)) for x in mode]
            for mode, norm in zip(EXACT_MODES, (4, 2, 2, 4), strict=True)
        ]
    )
    rates = np.array([float(rate) for rate in EXACT_RATES])
    decay = u.T @ np.diag(np.exp(-rates * delta)) @ u
    noise_cov = u.T @ np.diag((1.0 - np.exp(-2.0 * rates * delta)) / rates) @ u
    chol = np.linalg.cholesky(noise_cov)
    x = rng.multivariate_normal(np.zeros(4), sigma, size=count)
    x_next = x @ decay.T + rng.standard_normal((count, 4)) @ chol.T
    return x, x_next


def recover_rates_and_diffusion(
    x: np.ndarray, x_next: np.ndarray, delta: float
) -> dict[str, object]:
    """Recover the four eigenmode rates and the shared diffusion rate.

    Mirrors the theorem-owned transition: E[x_{t+d} x_t^T] = e^{-K d} Sigma
    (`transition_mean`/`transition_covariance`), so Gamma1 Gamma0^{-1}
    estimates e^{-K d} and its eigendecomposition recovers the exact
    eigenmode rates; Var(x_{t+d} - A x_t) = Sigma - A Sigma A^T recovers the
    per-mode noise variances (1 - e^{-2 lambda d}) / lambda, i.e. diffusion
    variance rate 2 (`scalarParameters_exact`,
    fin4_gaussian_semigroup.lean:680-683).
    """
    gamma1 = (x_next.T @ x) / len(x)
    gamma0 = (x.T @ x) / len(x)
    m_hat = (gamma1 + gamma1.T) / 2.0 @ np.linalg.inv(gamma0)
    values, vectors = np.linalg.eigh(m_hat)
    values = np.maximum(values, 1e-12)
    rates_hat = -np.log(values) / delta
    k_hat = vectors @ np.diag(rates_hat) @ vectors.T
    q_hat = gamma0 - m_hat @ gamma0 @ m_hat.T
    mode_variances = np.einsum("mi,ij,mj->m", vectors.T, q_hat, vectors.T)
    diffusion_hat = (
        2.0 * rates_hat * mode_variances / (1.0 - np.exp(-2.0 * rates_hat * delta))
    )
    rates_observed = sorted(float(value) for value in rates_hat)
    rates_exact = sorted(float(rate) for rate in EXACT_RATES)
    rate_errors = [
        abs(observed - exact) / exact
        for observed, exact in zip(rates_observed, rates_exact, strict=True)
    ]
    k_error = float(
        np.max(
            np.abs(
                k_hat - np.array([[float(value) for value in row] for row in EXACT_K])
            )
        )
    )
    return {
        "rates_hat": rates_observed,
        "rate_relative_errors": rate_errors,
        "rate_within_tolerance": all(error <= RATE_REL_TOL for error in rate_errors),
        "k_max_entry_error": k_error,
        "k_within_tolerance": k_error <= K_MAX_ENTRY_TOL,
        "diffusion_estimates": [float(value) for value in diffusion_hat],
        "diffusion_within_tolerance": all(
            abs(value - 2.0) <= DIFFUSION_ABS_TOL for value in diffusion_hat
        ),
    }


def recover_recognition(
    x: np.ndarray, observed: tuple[int, ...], target: int
) -> dict[str, float | tuple[float, ...]]:
    """Least-squares recovery of the exact Gaussian conditional-mean map."""
    design = np.column_stack((np.ones(len(x)), x[:, list(observed)]))
    outcome = x[:, target]
    coefficients, _, _, _ = np.linalg.lstsq(design, outcome, rcond=None)
    residual = outcome - design @ coefficients
    return {
        "intercept": float(coefficients[0]),
        "coefficients": tuple(float(value) for value in coefficients[1:]),
        "residual_variance": float(np.var(residual)),
    }


def recognition_gates(
    estimate: dict[str, float | tuple[float, ...]],
    expected_coefficients: tuple[float, ...],
    expected_residual: float,
) -> dict[str, bool]:
    coefficients = estimate["coefficients"]
    intercept = estimate["intercept"]
    residual_variance = estimate["residual_variance"]
    assert isinstance(coefficients, tuple)
    assert isinstance(intercept, float)
    assert isinstance(residual_variance, float)
    return {
        "coefficients_within_tolerance": all(
            abs(observed - expected) <= COEF_ABS_TOL
            for observed, expected in zip(
                coefficients, expected_coefficients, strict=True
            )
        ),
        "intercept_within_tolerance": abs(intercept) <= INTERCEPT_ABS_TOL,
        "residual_within_tolerance": (
            abs(residual_variance - expected_residual) <= RESIDUAL_ABS_TOL
        ),
    }


def negative_control(x: np.ndarray) -> dict[str, float]:
    """Precision-zero does not imply covariance-zero (the rejected substitute).

    The marginal external/internal covariance is exactly 1/24
    (`stationary_external_internal_covariance`,
    gaussian_precision_conditioning.lean:902-904) while the
    blanket-conditional covariance is exactly zero. A recognizer of internal
    from external that assumes the covariance is zero because the precision
    entry is zero loses exactly that signal: its MSE exceeds the optimal
    regression MSE (2/7, coefficient 1/7) by exactly 1/168.
    """
    design = np.column_stack((np.ones(len(x)), x[:, 0]))
    outcome = x[:, 3]
    coefficients, _, _, _ = np.linalg.lstsq(design, outcome, rcond=None)
    residual = outcome - design @ coefficients
    mse_fit = float(np.var(residual))
    mse_zero = float(np.var(outcome))
    return {
        "optimal_coefficient": float(coefficients[1]),
        "expected_coefficient": 1.0 / 7.0,
        "optimal_mse": mse_fit,
        "exact_optimal_mse": float(Fraction(2, 7)),
        "zero_covariance_mse": mse_zero,
        "exact_zero_mse": float(Fraction(7, 24)),
        "detectable_excess": mse_zero - mse_fit,
    }


def _run_setting(
    rng: np.random.Generator, delta: float
) -> tuple[dict[str, object], dict[str, float | tuple[float, ...]], dict[str, bool]]:
    x, x_next = _simulate_pairs(rng, N_PAIRS, delta)
    rates = recover_rates_and_diffusion(x, x_next, delta)
    if delta == SETTING_A_DELTA:
        # Setting A observes both interface axes (sensory, active).
        recognition = recover_recognition(x, (1, 2), 0)
        gates = recognition_gates(recognition, (0.25, 0.25), float(Fraction(1, 4)))
    else:
        # Setting B observes only the sensory axis.
        recognition = recover_recognition(x, (1,), 0)
        gates = recognition_gates(recognition, (2.0 / 7.0,), float(Fraction(15, 56)))
    return rates, recognition, gates


def run_spike(root: Path) -> dict[str, object]:
    digests = digest_guard(root)
    rejections = validate_typed_parameters()
    units = validate_raw_units()
    fixture = fixture_roundtrip()

    rng = np.random.default_rng(BASE_SEED)
    rates_a, recognition_a, gates_a = _run_setting(rng, SETTING_A_DELTA)
    rates_b, recognition_b, gates_b = _run_setting(rng, SETTING_B_DELTA)
    control_x, _ = _simulate_pairs(rng, N_PAIRS, SETTING_A_DELTA)
    control = negative_control(control_x)

    fixture_ok = all(value for value in fixture.values() if isinstance(value, bool))
    settings_ok = (
        bool(rates_a["rate_within_tolerance"])
        and bool(rates_a["diffusion_within_tolerance"])
        and bool(rates_a["k_within_tolerance"])
        and all(gates_a.values())
        and bool(rates_b["rate_within_tolerance"])
        and bool(rates_b["diffusion_within_tolerance"])
        and bool(rates_b["k_within_tolerance"])
        and all(gates_b.values())
    )
    rejections_ok = all(rejections.values()) and all(units.values())
    control_ok = control["detectable_excess"] >= MISSPECIFICATION_DETECT_MIN
    decision = (
        "pass"
        if fixture_ok and settings_ok and rejections_ok and control_ok
        else "fail"
    )
    return {
        "schema_version": 1,
        "gate": "H3.6S-feasibility-spike",
        "branch": "continuous",
        "base_seed": BASE_SEED,
        "n_pairs_per_setting": N_PAIRS,
        "frozen_tolerances": {
            "rate_relative": RATE_REL_TOL,
            "k_max_entry": K_MAX_ENTRY_TOL,
            "diffusion_absolute": DIFFUSION_ABS_TOL,
            "coefficient_absolute": COEF_ABS_TOL,
            "residual_absolute": RESIDUAL_ABS_TOL,
            "intercept_absolute": INTERCEPT_ABS_TOL,
            "float_semigroup_and_stationarity": FLOAT_TOL,
            "misspecification_detect_min": MISSPECIFICATION_DETECT_MIN,
        },
        "digests": digests,
        "fixture": fixture,
        "rejection_boundaries": {
            "reordered_parameters": rejections,
            "raw_units": units,
        },
        "setting_a": {
            "delta": SETTING_A_DELTA,
            "observed_axes": ["sensory", "active"],
            "rates": rates_a,
            "recognition": recognition_a,
            "gates": gates_a,
        },
        "setting_b": {
            "delta": SETTING_B_DELTA,
            "observed_axes": ["sensory"],
            "rates": rates_b,
            "recognition": recognition_b,
            "gates": gates_b,
        },
        "negative_control": control,
        "gate_results": {
            "fixture": fixture_ok,
            "settings": settings_ok,
            "rejections": rejections_ok,
            "negative_control_detected": control_ok,
        },
        "decision": decision,
        "claim_boundary": (
            "Feasibility evidence only: non-proof numerical evidence under the "
            "H2 witness discipline. Not an H3.6S acceptance verdict, not "
            "observed-data calibration, and not an empirical claim."
        ),
    }


def main(argv: list[str]) -> int:
    root = Path(argv[1]) if len(argv) > 1 else Path.cwd()
    payload = run_spike(root)
    print(json.dumps(payload, indent=2, sort_keys=True, default=str))
    return 0 if payload["decision"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
