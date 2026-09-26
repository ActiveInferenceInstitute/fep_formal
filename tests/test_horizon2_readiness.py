"""H2.0 source-bound pinned-library readiness contracts."""

from __future__ import annotations

import copy
import importlib.util
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import cast

import pytest
import yaml

from tests._support.lake import lake_executable
from tests._support.lean_runner import run_lean_compile_probe

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SPEC_ROOT = PROJECT_ROOT / "specs" / "done" / "horizon-2-smooth-stochastic"
MATRIX_PATH = SPEC_ROOT / "readiness" / "matrix.yaml"
VALIDATOR_PATH = SPEC_ROOT / "readiness" / "validate.py"
LEAN_ROOT = PROJECT_ROOT / "lean"

pytestmark = pytest.mark.serial_lean

EXPECTED_TOOLCHAIN = {
    "lean": "v4.34.0",
    "mathlib_tag": "v4.34.0",
    "mathlib_revision": "5ed2965256430c3649e86755f9576b54eca72435",
    "sources": {
        "lean_toolchain": "lean/lean-toolchain",
        "lakefile": "lean/lakefile.lean",
        "lake_manifest": "lean/lake-manifest.json",
    },
}

PROBE_ORDER = (
    "readiness/pin_evidence.json",
    "readiness/probes/01_api_surface.lean",
    "readiness/probes/01_calculus.lean",
    "readiness/probes/02_local_geometry.lean",
    "readiness/probes/03_weak_convergence.lean",
    "readiness/probes/04_posterior_martingale.lean",
    "readiness/probes/05_scalar_gaussian.lean",
    "readiness/probes/06_native_semigroup_bridge.lean",
    "readiness/probes/07_fin4_matrix_gaussian.lean",
    "readiness/probes/08_gaussian_conditioning.lean",
    "readiness/probes/09_finite_grid.lean",
    "readiness/probes/10_brownian_fdl.lean",
    "readiness/probes/11_unsupported_api_search.yaml",
)


def _matrix() -> dict[str, object]:
    payload = yaml.safe_load(MATRIX_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _validator() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "fep_h2_readiness_validator", VALIDATOR_PATH
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_canonical_acceptance_fails_closed_without_lake(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(shutil, "which", lambda _name: None)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    with pytest.raises(RuntimeError, match="lake is required"):
        lake_executable(missing="raise", context="canonical H2.0 readiness acceptance")


def _assert_probe_compiles_warning_free(relative_path: str) -> None:
    probe = SPEC_ROOT / relative_path
    with tempfile.TemporaryDirectory(prefix="fep-h2-probe-") as output_dir:
        output_path = Path(output_dir) / f"{probe.stem}.olean"
        result = run_lean_compile_probe(
            probe,
            cwd=LEAN_ROOT,
            import_root=PROJECT_ROOT,
            output_path=output_path,
            timeout_s=300,
            executable=lake_executable(
                missing="raise",
                context="canonical H2.0 readiness acceptance",
            ),
        )

        assert output_path.is_file(), result.stdout + result.stderr

    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "warning:" not in output.lower()


def test_readiness_pin_and_api_surface_probe_are_explicit() -> None:
    payload = _matrix()
    rows = payload["rows"]
    assert isinstance(rows, list)
    pin_row = next(row for row in rows if row["id"] == "pin_identity")
    pin_evidence_path = SPEC_ROOT / "readiness" / "pin_evidence.json"
    probe = SPEC_ROOT / "readiness" / "probes" / "01_api_surface.lean"

    assert payload["toolchain"] == EXPECTED_TOOLCHAIN
    assert pin_row["probe"] == {
        "kind": "metadata",
        "path": "readiness/pin_evidence.json",
        "anchor": "latest_stable",
    }
    pin_evidence = json.loads(pin_evidence_path.read_text(encoding="utf-8"))
    assert pin_evidence["schema_version"] == 1
    assert pin_evidence["stable_pair"] == {
        "lean_revision": "293d5d0c0c3f3dded4688b3ccd6a33939ac5102b",
        "mathlib_revision": EXPECTED_TOOLCHAIN["mathlib_revision"],
        "tag": "v4.34.0",
    }
    assert all(
        "refs/tags/v4.35.0" not in repo["refs"] for repo in pin_evidence["repositories"]
    )
    assert (PROJECT_ROOT / "lean" / "lean-toolchain").read_text(
        encoding="utf-8"
    ).strip() == "leanprover/lean4:v4.34.0"
    assert probe.is_file()
    source = probe.read_text(encoding="utf-8")
    assert re.search(r"(?m)^example\b", source)
    assert not re.search(r"\b(?:sorry|admit|axiom|opaque)\b", source)


def test_api_surface_probe_compiles_warning_free() -> None:
    _assert_probe_compiles_warning_free("readiness/probes/01_api_surface.lean")


def test_readiness_matrix_has_an_exact_atomic_row_and_probe_roster() -> None:
    payload = _matrix()
    rows = cast(list[dict[str, object]], payload["rows"])
    row_order = cast(list[str], payload["row_order"])
    criticality_values = cast(list[str], payload["criticality_values"])
    decision_values = cast(list[str], payload["decision_values"])

    assert payload["probe_order"] == list(PROBE_ORDER)
    assert payload["no_go_edge_semantics"] == (
        "row-to-slice readiness closures, not canonical scheduling DAG arcs"
    )
    assert len(row_order) == 42
    assert [row["id"] for row in rows] == row_order
    assert len(set(row_order)) == len(row_order)
    assert {row["criticality"] for row in rows} <= set(criticality_values)
    assert {row["status"] for row in rows} <= set(decision_values)


def test_calculus_probe_exercises_each_atomic_obligation() -> None:
    probe = SPEC_ROOT / "readiness" / "probes" / "01_calculus.lean"
    source = probe.read_text(encoding="utf-8")

    for row_id in (
        "finite_sum_derivatives",
        "real_exp_log_derivatives",
        "matrix_valued_frechet_derivative",
    ):
        assert re.search(rf"(?m)^-- H2-READINESS-ROW: {row_id}\nexample\b", source)
    assert "HasDerivAt.fun_sum" in source
    assert "Real.hasDerivAt_exp" in source
    assert "Real.hasDerivAt_log" in source
    assert "hasFDerivAt_pi" in source
    assert "Matrix (Fin 2) (Fin 2) ℝ" in source
    assert source.count("rw [hasFDerivAt_pi]") >= 2


def test_calculus_probe_compiles_warning_free() -> None:
    _assert_probe_compiles_warning_free("readiness/probes/01_calculus.lean")


def test_local_geometry_probe_separates_required_coordinates_from_optional_bundle() -> (
    None
):
    probe = SPEC_ROOT / "readiness" / "probes" / "02_local_geometry.lean"
    source = probe.read_text(encoding="utf-8")

    assert re.search(r"(?m)^-- H2-READINESS-ROW: coordinate_duality\nexample\b", source)
    for row_id in (
        "riemannian_vector_space",
        "covariant_derivative_api",
        "torsion_api",
        "metric_compatibility_api",
        "manifold_bundle_packaging",
    ):
        assert f"-- H2-READINESS-OPTIONAL: {row_id}" in source
    assert "#check IsRiemannianManifold" in source
    assert "#check IsCovariantDerivativeOn" in source
    assert "hvariance : 0 < variance" in source
    assert "naturalToMean" in source
    assert "meanToNatural" in source
    assert "variance * (mean / variance) = mean" in source


def test_local_geometry_probe_compiles_warning_free() -> None:
    _assert_probe_compiles_warning_free("readiness/probes/02_local_geometry.lean")


def test_weak_convergence_probe_keeps_bounded_and_characteristic_routes_distinct() -> (
    None
):
    probe = SPEC_ROOT / "readiness" / "probes" / "03_weak_convergence.lean"
    source = probe.read_text(encoding="utf-8")

    for row_id in ("weak_bounded_continuous", "weak_characteristic_function"):
        assert re.search(rf"(?m)^-- H2-READINESS-ROW: {row_id}\nexample\b", source)
    assert "ProbabilityMeasure.tendsto_iff_forall_integral_tendsto" in source
    assert "ProbabilityMeasure.tendsto_iff_tendsto_charFun" in source


def test_weak_convergence_probe_compiles_warning_free() -> None:
    _assert_probe_compiles_warning_free("readiness/probes/03_weak_convergence.lean")


def test_posterior_martingale_probe_separates_limit_from_identification() -> None:
    probe = SPEC_ROOT / "readiness" / "probes" / "04_posterior_martingale.lean"
    source = probe.read_text(encoding="utf-8")

    for row_id in (
        "posterior_kernel",
        "conditional_expectation",
        "martingale_convergence",
    ):
        assert re.search(rf"(?m)^-- H2-READINESS-ROW: {row_id}\nexample\b", source)
    assert "-- H2-READINESS-OPTIONAL: bayes_estimator" in source
    assert "posterior_consistency" not in source


def test_posterior_martingale_probe_compiles_warning_free() -> None:
    _assert_probe_compiles_warning_free("readiness/probes/04_posterior_martingale.lean")


def test_scalar_gaussian_probe_exercises_every_native_boundary() -> None:
    probe = SPEC_ROOT / "readiness" / "probes" / "05_scalar_gaussian.lean"
    source = probe.read_text(encoding="utf-8")

    for row_id in (
        "scalar_gaussian_density_ac",
        "scalar_gaussian_moments_ext",
        "scalar_gaussian_parameter_measurability",
        "scalar_gaussian_affine_convolution",
        "scalar_gaussian_native_kl",
    ):
        assert re.search(rf"(?m)^-- H2-READINESS-ROW: {row_id}\nexample\b", source)
    for declaration in (
        "gaussianReal_of_var_ne_zero",
        "lintegral_gaussianPDF_eq_one",
        "gaussianReal_absolutelyContinuous",
        "gaussianReal_absolutelyContinuous'",
        "rnDeriv_gaussianReal",
        "integral_id_gaussianReal",
        "variance_id_gaussianReal",
        "gaussianReal_ext_iff",
        "measurable_gaussianReal",
        "IsMarkovKernel kernel",
        "gaussianReal_map_const_mul",
        "gaussianReal_map_add_const",
        "gaussianReal_conv_gaussianReal",
        "Measure.map_map",
        "InformationTheory.klDiv",
        "InformationTheory.klDiv_of_ac_of_integrable",
        "InformationTheory.klDiv_ne_top",
        "gaussianReal_unitShift_llr_integrable",
    ):
        assert declaration in source
    assert "InformationTheory.klDiv_self" not in source
    assert "toReal_klDiv_eq_integral_klFun" not in source
    assert re.search(
        r"InformationTheory\.klDiv\s+\(gaussianReal 1 1\)\s+"
        r"\(gaussianReal 0 1\) =\s+ENNReal\.ofReal",
        source,
    )


def test_scalar_gaussian_probe_compiles_warning_free() -> None:
    _assert_probe_compiles_warning_free("readiness/probes/05_scalar_gaussian.lean")


def test_native_semigroup_probe_preserves_one_kernel_and_exact_h1_embedding() -> None:
    probe = SPEC_ROOT / "readiness" / "probes" / "06_native_semigroup_bridge.lean"
    source = probe.read_text(encoding="utf-8")

    for row_id in (
        "native_kernel_algebra",
        "native_invariance_kl_dpi",
        "exact_h1_embedded_lift",
    ):
        assert re.search(rf"(?m)^-- H2-READINESS-ROW: {row_id}\nexample\b", source)
    for declaration in (
        "Kernel.comp_assoc",
        "IsMarkovKernel.comp",
        "Kernel.Invariant",
        "InformationTheory.klDiv_comp_right_le",
        "FEP.NativeBlanket.embeddedKernel",
        "FiniteKernel.comp",
        "boolBlanketActionIndexedSemigroup",
        "ActionIndexedSemigroup.sampledKernel",
    ):
        assert declaration in source
    assert "structure NativeKernelSemigroup" not in source


def test_native_semigroup_probe_compiles_warning_free() -> None:
    _assert_probe_compiles_warning_free(
        "readiness/probes/06_native_semigroup_bridge.lean"
    )


def test_fin4_probe_uses_the_fixed_carrier_and_a_genuine_state_kernel() -> None:
    probe = SPEC_ROOT / "readiness" / "probes" / "07_fin4_matrix_gaussian.lean"
    source = probe.read_text(encoding="utf-8")

    for row_id in (
        "finite_dimensional_matrix_carrier",
        "positive_definite_inverse",
        "matrix_exponential_semigroup",
        "fin4_exact_precision_witness",
        "multivariate_gaussian_measure",
        "multivariate_gaussian_state_kernel",
    ):
        assert re.search(rf"(?m)^-- H2-READINESS-ROW: {row_id}\nexample\b", source)
    assert re.search(
        r"(?m)^-- H2-READINESS-UPSTREAM: fin4_scalar_specialization\nexample\b",
        source,
    )
    assert re.search(
        r"(?m)^-- H2-READINESS-BLOCKING: transition_covariance_psd\nexample\b",
        source,
    )
    for non_go_id in ("fin4_scalar_specialization", "transition_covariance_psd"):
        assert f"-- H2-READINESS-ROW: {non_go_id}" not in source
    for declaration in (
        "inductive Fin4Axis",
        "fin4AxisEquivFin",
        "fin4Precision_mul_covariance",
        "fin4Precision_posDef",
        "fin4Precision_external_internal",
        "fin4Covariance_external_internal",
        "fin4Precision_eigenvalue_two",
        "fin4Precision_eigenvalue_six",
        "Matrix.exp_add_of_commute",
        "Matrix.PosSemidef",
        "multivariateGaussian",
        "Kernel.compProd",
        "Kernel.map",
        "IsMarkovKernel fin4GaussianKernel",
    ):
        assert declaration in source
    assert "structure Fin4GaussianCertificate" not in source


def test_fin4_probe_compiles_warning_free() -> None:
    _assert_probe_compiles_warning_free("readiness/probes/07_fin4_matrix_gaussian.lean")


def test_conditioning_probe_fails_closed_at_the_probabilistic_seams() -> None:
    probe = SPEC_ROOT / "readiness" / "probes" / "08_gaussian_conditioning.lean"
    source = probe.read_text(encoding="utf-8")

    for row_id in ("gaussian_conditioning_precision", "native_filter_posterior"):
        assert re.search(rf"(?m)^-- H2-READINESS-BLOCKING: {row_id}\nexample\b", source)
        assert f"-- H2-READINESS-ROW: {row_id}" not in source
    for declaration in (
        "Matrix.PosDef.fromBlocks₁₁",
        "ProbabilityTheory.posterior",
        "compProd_posterior_eq_map_swap",
        "measurable_gaussianReal",
        "IsMarkovKernel (ProbabilityTheory.posterior observation prior)",
    ):
        assert declaration in source
    assert "def ConditionallyIndependent" not in source
    assert "structure GaussianConditioningCertificate" not in source


def test_conditioning_probe_compiles_warning_free() -> None:
    _assert_probe_compiles_warning_free(
        "readiness/probes/08_gaussian_conditioning.lean"
    )


def test_finite_grid_probe_builds_a_normalized_compositional_path_law() -> None:
    probe = SPEC_ROOT / "readiness" / "probes" / "09_finite_grid.lean"
    source = probe.read_text(encoding="utf-8")

    assert re.search(
        r"(?m)^-- H2-READINESS-ROW: finite_grid_trajectory\nexample\b",
        source,
    )
    for declaration in (
        "Kernel.partialTraj",
        "Kernel.partialTraj_comp_partialTraj",
        "IsMarkovKernel (Kernel.partialTraj readinessStepKernel 0 3)",
        "Set.univ = 1",
    ):
        assert declaration in source
    assert "Kernel.traj" not in source
    assert "continuousPath" not in source


def test_finite_grid_probe_compiles_warning_free() -> None:
    _assert_probe_compiles_warning_free("readiness/probes/09_finite_grid.lean")


def test_brownian_probe_is_finite_dimensional_only() -> None:
    probe = SPEC_ROOT / "readiness" / "probes" / "10_brownian_fdl.lean"
    source = probe.read_text(encoding="utf-8")

    assert re.search(
        r"(?m)^-- H2-READINESS-OPTIONAL: brownian_finite_dimensional\nexample\b",
        source,
    )
    for declaration in (
        "BrownianReal.projectiveFamily",
        "BrownianReal.covariance_eval_projectiveFamily",
        "BrownianReal.measurePreserving_eval_projectiveFamily",
        "BrownianReal.isProjectiveMeasureFamily_projectiveFamily",
    ):
        assert declaration in source
    assert "IsBrownian" not in source
    assert "continuous paths" not in source.lower()


def test_brownian_probe_compiles_warning_free() -> None:
    _assert_probe_compiles_warning_free("readiness/probes/10_brownian_fdl.lean")


def test_unsupported_api_search_is_bounded_replayable_and_fail_closed() -> None:
    search_path = SPEC_ROOT / "readiness" / "probes" / "11_unsupported_api_search.yaml"
    payload = yaml.safe_load(search_path.read_text(encoding="utf-8"))
    searches = payload["searches"]

    assert payload["schema_version"] == 1
    assert payload["mathlib_revision"] == EXPECTED_TOOLCHAIN["mathlib_revision"]
    assert [search["id"] for search in searches] == [
        "general_native_markov_semigroup",
        "stochastic_integral_ito",
        "sde_existence_uniqueness",
        "fokker_planck_solution",
        "girsanov_transform",
        "continuous_path_measure_density",
    ]
    root = PROJECT_ROOT / payload["root"]
    assert root.is_dir()
    lean_sources = tuple(sorted(root.rglob("*.lean")))
    assert lean_sources

    for search in searches:
        patterns = tuple(re.compile(pattern) for pattern in search["patterns"])
        assert patterns
        matches: list[str] = []
        for source_path in lean_sources:
            source = source_path.read_text(encoding="utf-8")
            for line_number, line in enumerate(source.splitlines(), start=1):
                if any(pattern.search(line) for pattern in patterns):
                    matches.append(
                        f"{source_path.relative_to(PROJECT_ROOT)}:{line_number}:{line}"
                    )
        assert search["status"] == "optional_no_go"
        assert search["result_count"] == len(matches)
        assert search["matches"] == matches
        assert search["no_go_action"]


def test_readiness_validator_accepts_only_the_source_bound_sealed_matrix() -> None:
    validator = _validator()
    payload = _matrix()

    assert validator.readiness_errors(PROJECT_ROOT) == ()
    assert payload["canonical_rows_sha256"] == validator.canonical_rows_sha256(
        payload["rows"]
    )
    receipt = json.loads(
        (SPEC_ROOT / "readiness" / "acceptance.json").read_text(encoding="utf-8")
    )
    assert receipt["canonical_rows_sha256"] == payload["canonical_rows_sha256"]


@pytest.mark.parametrize(
    ("mutation", "expected_error"),
    (
        (
            lambda payload: payload["rows"][0].__setitem__("status", "pending"),
            "row pin_identity status is not sealed: pending",
        ),
        (
            lambda payload: payload["rows"][1]["probe"].__setitem__(
                "path", "readiness/probes/missing.lean"
            ),
            "readiness probe is missing",
        ),
        (
            lambda payload: payload["acceptance_evidence"].__setitem__(
                "receipt_sha256", "0" * 64
            ),
            "acceptance receipt digest mismatch",
        ),
        (
            lambda payload: payload.__setitem__("canonical_rows_sha256", "0" * 64),
            "canonical row digest mismatch",
        ),
    ),
)
def test_readiness_validator_rejects_tampering(
    mutation: object, expected_error: str
) -> None:
    validator = _validator()
    payload = copy.deepcopy(_matrix())
    assert callable(mutation)
    mutation(payload)

    errors = validator.readiness_errors(
        PROJECT_ROOT,
        payload=payload,
        formal_resources=(),
    )

    assert any(expected_error in error for error in errors), errors


@pytest.mark.parametrize(
    "mutation",
    (
        lambda payload: payload["rows"][1].__setitem__(
            "obligation", "A recomputed but false scientific obligation."
        ),
        lambda payload: payload["rows"][1].__setitem__(
            "probe",
            {
                "kind": "metadata",
                "path": "readiness/pin_evidence.json",
                "anchor": "latest_stable",
            },
        ),
    ),
)
def test_readiness_validator_rejects_rehashed_semantic_tampering(
    mutation: object,
) -> None:
    validator = _validator()
    payload = copy.deepcopy(_matrix())
    assert callable(mutation)
    mutation(payload)
    payload["canonical_rows_sha256"] = validator.canonical_rows_sha256(payload["rows"])

    errors = validator.readiness_errors(
        PROJECT_ROOT,
        payload=payload,
        formal_resources=(),
    )

    assert "acceptance receipt canonical row digest mismatch" in errors


def test_readiness_validator_rejects_a_premature_h2_formal_resource() -> None:
    validator = _validator()
    payload = copy.deepcopy(_matrix())
    payload["status"] = "pending"

    errors = validator.readiness_errors(
        PROJECT_ROOT,
        payload=payload,
        formal_resources=("gaussian_information_geometry.lean",),
    )

    assert (
        "maintained H2 formal resources must remain absent during H2.0: "
        "gaussian_information_geometry.lean" in errors
    )


def test_completed_readiness_evidence_survives_the_first_h2_resource() -> None:
    validator = _validator()

    errors = validator.readiness_errors(
        PROJECT_ROOT,
        payload=_matrix(),
        formal_resources=("gaussian_information_geometry.lean",),
    )

    assert errors == ()
