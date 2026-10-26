"""H2.7-R0 continuous Gaussian VFE and natural-gradient proof gate."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

import pytest

from fep_lean import __version__
from fep_lean.formal.manifest import FORMAL_MODULES
from fep_lean.lean_source import lean_code_without_comments
from tests._support.h2_r0_custody import (
    H3_ADDED_OWNERS,
    H3_ADDENDUM_PATH,
    H3_OWNER_SOURCE_PATHS,
    MANIFEST_PATH,
    PRIOR_PATH,
    RELEASE_METADATA_REPLACEMENTS,
    SUCCESSOR_PATH,
    VALIDATOR_PATH,
    W4_CODE_CONSOLIDATION,
    validate_h2_r0_custody,
)
from tests._support.lake import lake_executable
from tests._support.lean435_migration import (
    HISTORICAL_CUSTODY_ARCHIVE,
    HISTORICAL_MANIFEST_ARCHIVE,
    HISTORICAL_MANIFEST_ARCHIVE_SHA256,
    HISTORICAL_METADATA_ARCHIVE,
    HISTORICAL_METADATA_ARCHIVE_SHA256,
    bridge_dev_lock_predecessor,
    bridge_dev_metadata_predecessor,
    historical_carrier_bytes,
    historical_custody_root,
    historical_custody_sources,
    historical_manifest_bytes,
    historical_metadata_bytes,
    historical_toolchain_files,
)
from tests._support.lean_runner import (
    run_lake_lean_probe,
    run_lean_compile_probe,
    run_lean_probe,
)
from tests._support.release_lineage import LATER_RELEASE_VERSIONS, custody_paths

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEAN_ROOT = PROJECT_ROOT / "lean"
SPIKE = (
    PROJECT_ROOT
    / "specs"
    / "done"
    / "horizon-2-smooth-stochastic"
    / "spikes"
    / "07_gaussian_vfe_natural_gradient.lean"
)
SLICE = (
    PROJECT_ROOT
    / "specs"
    / "done"
    / "horizon-2-smooth-stochastic"
    / "slices"
    / "07-r0-gaussian-vfe-natural-gradient.md"
)
REPAIR = (
    PROJECT_ROOT
    / "specs"
    / "done"
    / "horizon-2-smooth-stochastic"
    / "readiness"
    / "repairs"
    / "07-gaussian-vfe-natural-gradient.json"
)

SOURCE_BOUND_PATHS = (
    "lean/lean-toolchain",
    "lean/lakefile.lean",
    "lean/lake-manifest.json",
    "pyproject.toml",
    "uv.lock",
    "specs/done/horizon-2-smooth-stochastic/readiness/acceptance.json",
    "specs/done/horizon-2-smooth-stochastic/readiness/matrix.yaml",
    "src/fep_lean/formal/manifest.py",
    "src/fep_lean/formal/gaussian_information_geometry.lean",
    "lean/FepSketches/gaussian_information_geometry.lean",
    "src/fep_lean/formal/smooth_information_geometry.lean",
    "lean/FepSketches/smooth_information_geometry.lean",
    "src/fep_lean/formal/compositions/gaussian_filter.lean",
    "lean/FepSketches/compositions/gaussian_filter.lean",
    "specs/done/horizon-2-smooth-stochastic/slices/07-r0-gaussian-vfe-natural-gradient.md",
    "specs/done/horizon-2-smooth-stochastic/spikes/07_gaussian_vfe_natural_gradient.lean",
    "tests/test_horizon2_gaussian_vfe_readiness.py",
)
OWNER_BINDINGS = {
    "FepSketches.gaussian_information_geometry": (
        "gaussian_information_geometry.lean",
        "FEP.GaussianInformationGeometry",
    ),
    "FepSketches.smooth_information_geometry": (
        "smooth_information_geometry.lean",
        "FEP.SmoothInformationGeometry",
    ),
    "FepSketches.compositions.gaussian_filter": (
        "compositions/gaussian_filter.lean",
        "FEPComposed.GaussianFilter",
    ),
}

pytestmark = pytest.mark.serial_lean

EXACT_IMPORTS = (
    "FepSketches.gaussian_information_geometry",
    "FepSketches.smooth_information_geometry",
    "FepSketches.compositions.gaussian_filter",
)
PUBLIC_DEFINITIONS = (
    "evidenceSurprisal",
    "gaussianVariationalFreeEnergy",
    "meanNaturalGradient",
    "naturalGradientFlow",
)
PUBLIC_THEOREMS = (
    "evidenceLaw_eq_volume_withDensity",
    "evidenceDensity_ne_top",
    "gaussianVariationalFreeEnergy_eq_meanSquare_add_surprisal",
    "gaussianVariationalFreeEnergy_sub_surprisal_eq_nativeKL",
    "gaussianVariationalFreeEnergy_eq_surprisal_iff",
    "gaussianVariationalFreeEnergy_hasDerivAt",
    "meanNaturalGradient_eq_displacement",
    "meanNaturalGradient_metric_dual",
    "naturalGradientFlow_zero",
    "gaussianVariationalFreeEnergy_naturalGradientFlow_hasDerivAt",
    "gaussianVariationalFreeEnergy_naturalGradientFlow_deriv_neg",
    "continuousGaussianVFE_naturalGradient",
)
PUBLIC_ENVIRONMENT = frozenset((*PUBLIC_DEFINITIONS, *PUBLIC_THEOREMS))
ALLOWED_AXIOMS = frozenset({"propext", "Classical.choice", "Quot.sound"})
NAMESPACE = "FEPProbe.H2_7GaussianVFE"

H3_TAMPER_ERRORS = {
    "missing_h3_owner": "H3 owner missing, duplicated, or changed",
    "unlisted_h3_owner": "H3 owner subtraction does not recover the historical custody manifest",
    "duplicate_h3_owner": "duplicate manifest resource",
    "reordered_h3_owner": "H3 owner bytes, role, or insertion order changed",
    "changed_h3_role": "H3 owner missing, duplicated, or changed",
    "changed_h3_namespace": "H3 owner missing, duplicated, or changed",
    "manifest_code": "H3 owner subtraction does not recover the historical custody manifest",
    "h3_owner_source": "stale H3 addendum source digest",
    "addendum_prior": "H3 custody addendum does not bind the immutable successor",
    "addendum_boolean_schema": "H3 custody addendum does not bind the immutable successor",
    "addendum_modules": "H3 manifest transition does not match the exact append-only owners",
    "addendum_sources": "stale H3 addendum source digest",
    "addendum_historical_support": "historical custody support digests changed",
    "addendum_support_allowance": "unreviewed H3 custody support-change allowance",
    "addendum_downstream": "H3 custody addendum expanded the historical decision or downstream scope",
    "addendum_native": "H3 custody addendum cannot claim fresh or reused native execution",
    "addendum_numeric_native_flag": "H3 custody addendum cannot claim fresh or reused native execution",
    "release_dependency_drift": "release metadata has unlisted changes beyond the root version: pyproject.toml",
    "release_lock_dependency_drift": "release metadata has unlisted changes beyond the root version: uv.lock",
    "release_lock_schema_drift": "release metadata has unlisted changes beyond the root version: uv.lock",
    "release_version_drift": "release metadata must contain exactly the approved root version: pyproject.toml",
    "release_duplicate_root": "release metadata must contain exactly the approved root version: pyproject.toml",
    "release_missing_transition": "H3 custody addendum fields changed",
    "release_transition_digest": "release metadata transition does not match the exact root-version delta",
    "release_transition_allowance": "release metadata transition does not match the exact root-version delta",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _production_custody_snapshot() -> dict[str, bytes]:
    """Observe every retained custody input without changing its epoch."""
    # The autouse release-lineage fixture redirects PROJECT_ROOT for custody
    # checks. This snapshot deliberately observes the real repository.
    root = Path(__file__).resolve().parents[1]
    records = (PRIOR_PATH, SUCCESSOR_PATH, H3_ADDENDUM_PATH)
    paths = {
        VALIDATOR_PATH,
        *records,
        HISTORICAL_CUSTODY_ARCHIVE,
        HISTORICAL_MANIFEST_ARCHIVE,
        HISTORICAL_METADATA_ARCHIVE,
        "tests/fixtures/custody_toolchain_4_34_1.json",
    }
    for relative in records:
        paths.update(json.loads((root / relative).read_bytes())["source_sha256"])
    return {relative: (root / relative).read_bytes() for relative in paths}


def _copy_historical_custody_inputs(source: Path, destination: Path) -> None:
    """Copy only bound inputs and authenticated archives for a static control."""
    import shutil

    for relative in {
        *custody_paths(source),
        HISTORICAL_CUSTODY_ARCHIVE,
        HISTORICAL_MANIFEST_ARCHIVE,
        HISTORICAL_METADATA_ARCHIVE,
        "tests/fixtures/custody_toolchain_4_34_1.json",
        "tests/fixtures/source_epoch_20261026.json",
        "src/fep_lean/formal/compositions/h3_case_study_model_control.lean",
        "src/fep_lean/formal/compositions/h3_case_study_path_information.lean",
        "src/fep_lean/formal/compositions/h3_case_study_cost_feedback.lean",
    }:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / relative, target)


def _parse_axiom_names(block: str) -> frozenset[str]:
    return frozenset(
        token.strip().strip("'")
        for token in block.replace("\n", " ").split(",")
        if token.strip().strip("'")
    )


def _axiom_reports(output: str) -> dict[str, frozenset[str]]:
    reports: dict[str, frozenset[str]] = {}
    for name in sorted(PUBLIC_ENVIRONMENT):
        qualified = f"{NAMESPACE}.{name}"
        report = re.search(
            rf"'{re.escape(qualified)}' "
            r"(?:depends on axioms: \[(?P<axioms>.*?)\]"
            r"|does not depend on any axioms)",
            output,
            re.DOTALL,
        )
        assert report is not None, f"missing axiom report for {qualified}\n{output}"
        if report.group("axioms") is None:
            reports[name] = frozenset()
        else:
            parsed = _parse_axiom_names(report.group("axioms"))
            assert parsed, f"empty axiom report for {qualified}"
            reports[name] = parsed
    return reports


def _run_lean(source_text: str) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory(prefix="lean_probe_") as temp_dir:
        probe = Path(temp_dir) / "LeanProbe.lean"
        probe.write_text(source_text, encoding="utf-8")
        return run_lean_probe(
            probe,
            import_root=PROJECT_ROOT / "src" / "fep_lean" / "formal",
            cwd=LEAN_ROOT,
            timeout_s=1800,
        )


def _typed_consumers() -> str:
    return r"""
open MeasureTheory ProbabilityTheory InformationTheory
open FEP.GaussianInformationGeometry
open FEP.SmoothInformationGeometry
open FEPComposed.GaussianFilter
open FEPProbe.H2_7GaussianVFE

example (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation : ℝ) :
    evidenceSurprisal model prior observation =
      -Real.log (evidenceDensity model prior observation).toReal := rfl

example (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation recognitionMean : ℝ) :
    gaussianVariationalFreeEnergy model prior observation recognitionMean =
      (klDiv ((posteriorFamily model prior).law recognitionMean)
        ((posteriorBelief model prior observation).law)).toReal +
          evidenceSurprisal model prior observation := rfl

example (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation recognitionMean : ℝ) :
    meanNaturalGradient model prior observation recognitionMean =
      ((posteriorFamily model prior).meanFisher recognitionMean)⁻¹ *
        ((recognitionMean - posteriorMean model prior observation) /
          (posteriorVariance model prior : ℝ)) := rfl

example (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation recognitionMean time : ℝ) :
    naturalGradientFlow model prior observation recognitionMean time =
      recognitionMean - time *
        meanNaturalGradient model prior observation recognitionMean := rfl

example (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief) :
    evidenceLaw model prior = volume.withDensity (evidenceDensity model prior) :=
  evidenceLaw_eq_volume_withDensity model prior

example (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation : ℝ) : evidenceDensity model prior observation ≠ ⊤ :=
  evidenceDensity_ne_top model prior observation

example (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation recognitionMean : ℝ) :
    gaussianVariationalFreeEnergy model prior observation recognitionMean =
      (recognitionMean - posteriorMean model prior observation) ^ 2 /
          (2 * (posteriorVariance model prior : ℝ)) +
        evidenceSurprisal model prior observation :=
  gaussianVariationalFreeEnergy_eq_meanSquare_add_surprisal
    model prior observation recognitionMean

example (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation recognitionMean : ℝ) :
    gaussianVariationalFreeEnergy model prior observation recognitionMean -
        evidenceSurprisal model prior observation =
      (klDiv ((posteriorFamily model prior).law recognitionMean)
        ((posteriorBelief model prior observation).law)).toReal :=
  gaussianVariationalFreeEnergy_sub_surprisal_eq_nativeKL
    model prior observation recognitionMean

example (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation recognitionMean : ℝ) :
    gaussianVariationalFreeEnergy model prior observation recognitionMean =
        evidenceSurprisal model prior observation ↔
      recognitionMean = posteriorMean model prior observation :=
  gaussianVariationalFreeEnergy_eq_surprisal_iff
    model prior observation recognitionMean

example (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation recognitionMean : ℝ) :
    HasDerivAt (gaussianVariationalFreeEnergy model prior observation)
      ((recognitionMean - posteriorMean model prior observation) /
        (posteriorVariance model prior : ℝ)) recognitionMean :=
  gaussianVariationalFreeEnergy_hasDerivAt model prior observation recognitionMean

example (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation recognitionMean : ℝ) :
    meanNaturalGradient model prior observation recognitionMean =
      recognitionMean - posteriorMean model prior observation :=
  meanNaturalGradient_eq_displacement model prior observation recognitionMean

example (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation recognitionMean tangent : ℝ) :
    meanMetricPairing (posteriorFamily model prior) recognitionMean
        (meanNaturalGradient model prior observation recognitionMean) tangent =
      ((recognitionMean - posteriorMean model prior observation) /
          (posteriorVariance model prior : ℝ)) * tangent :=
  meanNaturalGradient_metric_dual model prior observation recognitionMean tangent

example (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation recognitionMean : ℝ) :
    naturalGradientFlow model prior observation recognitionMean 0 = recognitionMean :=
  naturalGradientFlow_zero model prior observation recognitionMean

example (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation recognitionMean : ℝ) :
    HasDerivAt
      (fun time => gaussianVariationalFreeEnergy model prior observation
        (naturalGradientFlow model prior observation recognitionMean time))
      (-((recognitionMean - posteriorMean model prior observation) ^ 2 /
        (posteriorVariance model prior : ℝ))) 0 :=
  gaussianVariationalFreeEnergy_naturalGradientFlow_hasDerivAt
    model prior observation recognitionMean

example (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation recognitionMean : ℝ)
    (h : recognitionMean ≠ posteriorMean model prior observation) :
    -((recognitionMean - posteriorMean model prior observation) ^ 2 /
        (posteriorVariance model prior : ℝ)) < 0 :=
  gaussianVariationalFreeEnergy_naturalGradientFlow_deriv_neg
    model prior observation recognitionMean h

example (model : ScalarGaussianFilterModel) (prior : ScalarGaussianBelief)
    (observation recognitionMean tangent : ℝ)
    (h : recognitionMean ≠ posteriorMean model prior observation) :
    evidenceLaw model prior = volume.withDensity (evidenceDensity model prior) ∧
      0 < evidenceDensity model prior observation ∧
      evidenceDensity model prior observation ≠ ⊤ ∧
      gaussianVariationalFreeEnergy model prior observation recognitionMean -
          evidenceSurprisal model prior observation =
        (klDiv ((posteriorFamily model prior).law recognitionMean)
          ((posteriorBelief model prior observation).law)).toReal ∧
      (gaussianVariationalFreeEnergy model prior observation recognitionMean =
          evidenceSurprisal model prior observation ↔
        recognitionMean = posteriorMean model prior observation) ∧
      meanNaturalGradient model prior observation recognitionMean =
        recognitionMean - posteriorMean model prior observation ∧
      meanMetricPairing (posteriorFamily model prior) recognitionMean
          (meanNaturalGradient model prior observation recognitionMean) tangent =
        ((recognitionMean - posteriorMean model prior observation) /
            (posteriorVariance model prior : ℝ)) * tangent ∧
      HasDerivAt
        (fun time => gaussianVariationalFreeEnergy model prior observation
          (naturalGradientFlow model prior observation recognitionMean time))
        (-((recognitionMean - posteriorMean model prior observation) ^ 2 /
          (posteriorVariance model prior : ℝ))) 0 ∧
      -((recognitionMean - posteriorMean model prior observation) ^ 2 /
          (posteriorVariance model prior : ℝ)) < 0 :=
  continuousGaussianVFE_naturalGradient
    model prior observation recognitionMean tangent h
"""


def test_h2_7_r0_is_source_bound_and_reuses_exact_owners() -> None:
    assert SPIKE.is_file()
    assert SLICE.is_file()
    assert all(Path(module.resource).name != SPIKE.name for module in FORMAL_MODULES)
    source = SPIKE.read_text(encoding="utf-8")
    assert tuple(re.findall(r"(?m)^import (\S+)$", source)) == EXACT_IMPORTS
    assert f"namespace {NAMESPACE}\n" in source
    assert source.rstrip().endswith(f"end {NAMESPACE}")
    modules = {module.lean_module: module for module in FORMAL_MODULES}
    for lean_module, (resource, namespace) in OWNER_BINDINGS.items():
        owner = modules[lean_module]
        assert owner.resource == resource
        assert owner.declaration_namespace == namespace
        canonical = PROJECT_ROOT / "src" / "fep_lean" / "formal" / resource
        projection = LEAN_ROOT / "FepSketches" / resource
        assert projection.read_bytes() == canonical.read_bytes()


def test_h2_7_r0_uses_the_pinned_lean_mathlib_environment() -> None:
    historical_pins = historical_toolchain_files(Path(__file__).resolve().parents[1])
    assert historical_pins["lean/lean-toolchain"] == b"leanprover/lean4:v4.34.1\n"
    # Frozen acceptance retains that earlier epoch; these native probes must
    # use the actual current compiler, without reissuing the old decision.
    assert (LEAN_ROOT / "lean-toolchain").read_text(encoding="utf-8").strip() == (
        "leanprover/lean4:v4.35.0"
    )
    manifest = json.loads((LEAN_ROOT / "lake-manifest.json").read_text("utf-8"))
    mathlib = next(
        package for package in manifest["packages"] if package["name"] == "mathlib"
    )
    assert mathlib["rev"] == "56a005855ea17e0b0958f73ec801ae140b0a1679"
    assert mathlib["inputRev"] == "v4.35.0"
    result = run_lake_lean_probe(
        ["env", "lean", "--version"],
        cwd=LEAN_ROOT,
        timeout_s=30,
        executable=lake_executable(
            missing="raise",
            context="H2.7-R0 native validation",
        ),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stderr == ""
    # Pin the toolchain version + exact build commit; the platform triple varies
    # by host (the CI runner is x86_64-linux, local hosts may be aarch64-darwin)
    # and is not part of the source-bound environment claim the receipt records.
    version_line = result.stdout.strip()
    assert version_line.startswith("Lean (version 4.35.0, "), version_line
    assert "commit eb6cafb7290e8bd5f2937522d8d804f58f02bafc, Release)" in version_line


def test_h2_7_r0_surface_and_orientation_are_exact_and_fail_closed() -> None:
    source = lean_code_without_comments(SPIKE.read_text(encoding="utf-8"))
    definitions = tuple(
        re.findall(r"(?m)^(?:noncomputable )?def ([A-Za-z_][A-Za-z0-9_']*)\b", source)
    )
    theorems = tuple(re.findall(r"(?m)^theorem ([A-Za-z_][A-Za-z0-9_']*)\b", source))
    assert definitions == PUBLIC_DEFINITIONS
    assert theorems == PUBLIC_THEOREMS
    assert not re.search(
        r"(?m)^(?:private|protected)\s+|^(?:structure|class|abbrev|lemma|instance)\b",
        source,
    )
    assert re.search(
        r"noncomputable def evidenceSurprisal.*?: ℝ :=\s*"
        r"-Real\.log \(evidenceDensity model prior observation\)\.toReal",
        source,
        re.DOTALL,
    )
    vfe_definition = re.search(
        r"noncomputable def gaussianVariationalFreeEnergy\b"
        r"(?P<body>.*?)(?=\n\s*noncomputable def meanNaturalGradient\b)",
        source,
        re.DOTALL,
    )
    assert vfe_definition is not None
    assert re.search(
        r"klDiv\s+\(\(posteriorFamily model prior\)\.law recognitionMean\)\s+"
        r"\(\(posteriorBelief model prior observation\)\.law\)",
        vfe_definition["body"],
    )
    assert not re.search(
        r"klDiv\s+\(\(posteriorBelief model prior observation\)\.law\)\s+"
        r"\(\(posteriorFamily model prior\)\.law recognitionMean\)",
        vfe_definition["body"],
    )
    flow_definition = re.search(
        r"noncomputable def naturalGradientFlow\b(?P<body>.*?)"
        r"(?=\n\s*theorem evidenceLaw_eq_volume_withDensity\b)",
        source,
        re.DOTALL,
    )
    assert flow_definition is not None
    assert re.search(
        r"recognitionMean - time \*\s*"
        r"meanNaturalGradient model prior observation recognitionMean",
        flow_definition["body"],
    )
    assert "volume.withDensity (evidenceDensity model prior)" in source
    assert "evidenceDensity_pos model prior observation" in source
    assert "meanFisher_eq_inv_variance" in source
    assert "meanMetricPairing_eq_invVariance" in source
    assert "posteriorVariance_pos model prior" in source
    assert not re.search(
        r"\b(?:GenerativeModel|FiniteLaw|pointMass|expectedFreeEnergy|"
        r"epistemicValue|reward|HamiltonJacobi|FokkerPlanck|Girsanov|SDE)\b",
        source,
    )
    assert not re.search(
        r"\b(?:sorry|admit|axiom|opaque)\b|unsafe\s+(?:def|theorem)|:\s*True\b",
        source,
    )
    assert "Set.singleton" not in source
    assert not re.search(r"evidenceLaw\b.*\{observation\}", source, re.DOTALL)


def test_h2_7_r0_compiles_warning_free() -> None:
    result = run_lean_compile_probe(
        SPIKE,
        cwd=LEAN_ROOT,
        timeout_s=300,
        executable=lake_executable(
            missing="raise",
            context="H2.7-R0 native validation",
        ),
    )
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert output == ""


def test_h2_7_r0_exact_types_environment_and_axioms() -> None:
    suffix = "\n" + _typed_consumers() + "\n"
    # Lean v4.34.0 core no longer accepts `#print prefix <namespace>`; the
    # roster check emits one `#print axioms` per PUBLIC_ENVIRONMENT member.
    # A missing declaration fails its own report, so the roster stays
    # fail-closed; the axiom-report format quotes fully qualified names
    # regardless of the consumers' `open` statements.
    suffix += (
        "\n"
        + "\n".join(
            f"#print axioms {NAMESPACE}.{name}" for name in sorted(PUBLIC_ENVIRONMENT)
        )
        + "\n"
    )
    result = _run_lean(SPIKE.read_text(encoding="utf-8") + suffix)
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "warning:" not in output
    assert "sorryAx" not in output
    reports = _axiom_reports(output)
    assert set(reports) == set(PUBLIC_ENVIRONMENT)
    assert all(axioms <= ALLOWED_AXIOMS for axioms in reports.values())


def test_h2_7_r0_typed_consumer_rejects_reversed_kl() -> None:
    mutated = _typed_consumers().replace(
        "(klDiv ((posteriorFamily model prior).law recognitionMean)\n"
        "        ((posteriorBelief model prior observation).law)).toReal",
        "(klDiv ((posteriorBelief model prior observation).law)\n"
        "        ((posteriorFamily model prior).law recognitionMean)).toReal",
        1,
    )
    assert mutated != _typed_consumers()
    result = _run_lean(SPIKE.read_text(encoding="utf-8") + "\n" + mutated)
    assert result.returncode != 0
    output = result.stdout + result.stderr
    assert "expected to have type" in output or "type mismatch" in output.lower()


def test_h2_7_r0_repair_is_source_bound_append_only_go() -> None:
    before = _production_custody_snapshot()
    # The category owner is outside the frozen manifest transition. Its earlier
    # refusal must not be mistaken for failure of the current native theorem.
    with pytest.raises(
        ValueError,
        match=r"^H3 owner subtraction does not recover the historical custody manifest$",
    ):
        validate_h2_r0_custody(PROJECT_ROOT)
    assert _sha256(PROJECT_ROOT / VALIDATOR_PATH) == (
        "46c45d3eb5a19c8a6c9814d660ff9e6f8f0ddaeff6b4cd17ff14520fded27b53"
    )
    assert _sha256(PROJECT_ROOT / SUCCESSOR_PATH) == (
        "6311a998b1a66bb31949e194eb9e36a2e361dfbfb0f0e7d715b3a17e3e396bae"
    )
    assert _sha256(PROJECT_ROOT / H3_ADDENDUM_PATH) == (
        "69279a2c2641a81799c272dca277d4c255a46eaa48c94cb86c1072aa0fa936c6"
    )
    # Read sealed historical decisions rather than presenting them as a new
    # successful custody validation for the migrated source tree.
    successor = {
        **json.loads((PROJECT_ROOT / H3_ADDENDUM_PATH).read_bytes()),
        "historical_custody": json.loads((PROJECT_ROOT / SUCCESSOR_PATH).read_bytes()),
    }
    assert REPAIR.is_file()
    assert _sha256(REPAIR) == (
        "06fa2f40cec8cc0174eb4583e1e86436ba6bb081db494ff1e2b5086e196d289a"
    )
    repair = json.loads(REPAIR.read_text(encoding="utf-8"))

    assert repair["schema_version"] == 1
    assert repair["gate"] == "H2.7-R0"
    assert repair["decision"] == "go"
    assert repair["decision_scope"] == "open_H2.7_implementation_only"
    assert repair["historical_boundary"] == {
        "acceptance_mutated": False,
        "addendum_only": True,
        "matrix_mutated": False,
        "h2_0_row_statuses_mutated": False,
    }
    assert repair["compiler"] == {
        "lean_commit": "819816b2e0a3bf405af45ae5c7af2491d8f5bee6",
        "lean_version": "4.33.1",
        "mathlib_revision": "0df444a360eaa60ab8c11dca51a86af692955474",
        "mathlib_tag": "v4.33.1",
    }
    assert repair["imports"] == list(EXACT_IMPORTS)
    assert repair["declarations"] == {
        "definitions": list(PUBLIC_DEFINITIONS),
        "theorems": list(PUBLIC_THEOREMS),
    }
    assert repair["proof_route"] == {
        "evidence_reference": "Lebesgue density of the actual H2.6a evidence law",
        "recognition_family": "fixed posterior variance with free mean",
        "native_kl_orientation": "recognition_to_posterior",
        "mean_fisher_coordinate": "inverse posterior variance",
        "natural_gradient": "Fisher inverse applied to the VFE mean differential",
        "descent_scope": "time-zero derivative along the local negative-natural-gradient line",
        "scope_substitution_used": False,
        "stored_derivative_or_strictness_certificate": False,
    }
    assert repair["evidence"] == {
        "compile_command": (
            "cd lean && lake env lean "
            "../specs/done/horizon-2-smooth-stochastic/spikes/"
            "07_gaussian_vfe_natural_gradient.lean"
        ),
        "compiler_exit_code": 0,
        "compiler_output": "",
        "compiler_output_sha256": hashlib.sha256(b"").hexdigest(),
        "warning_count": 0,
        "typed_consumer_audit": True,
        "standard_axiom_audit": True,
        "axiom_audited_declarations": list(PUBLIC_THEOREMS),
        "allowed_axioms": ["propext", "Classical.choice", "Quot.sound"],
        "sorry_axiom_present": False,
        "public_definition_count": len(PUBLIC_DEFINITIONS),
        "public_theorem_count": len(PUBLIC_THEOREMS),
        "owner_projection_parity": True,
        "focused_test_command": (
            "uv run pytest -q tests/test_horizon2_gaussian_vfe_readiness.py --no-cov"
        ),
        "focused_test_count": 7,
    }
    assert repair["review"]["independent_lean_api"] == (
        "approved_no_api_or_proof_blocker"
    )
    assert repair["review"]["independent_information_geometry"] == (
        "approved_no_scientific_blocker"
    )
    assert repair["review"]["independent_skeptical_claim_scope"] == (
        "approved_fail_closed_source_bound_contract"
    )
    assert repair["review"]["reviewed_spike_sha256"] == _sha256(SPIKE)
    assert (
        repair["review"]["reviewed_pre_receipt_test_sha256"]
        == repair["source_sha256"]["tests/test_horizon2_gaussian_vfe_readiness.py"]
    )
    assert repair["downstream"] == {
        "opened": ["H2.7 maintained implementation"],
        "remains_closed": [
            "H3.G0 pending accepted H2.7 terminal certificate",
            "all H3 implementation",
        ],
    }
    assert repair["reviewed_no_go_claims"] == [
        "singleton-event surprisal",
        "finite H1 VFE as a continuous-density substitute",
        "expected free energy, reward, or policy optimality",
        "arbitrary recognition covariance or recognition family",
        "global natural-gradient flow or ODE convergence",
        "physical energy, thermodynamic work, or dimensional identification",
        "unqualified Fisher-equals-covariance claim",
        "continuous H3 eligibility before accepted H2.7",
    ]
    assert (
        successor["historical_custody"]["manifest_transition"]["code_consolidation"]
        == W4_CODE_CONSOLIDATION
    )
    assert set(successor["source_sha256"]) == {
        *SOURCE_BOUND_PATHS,
        VALIDATOR_PATH,
        *H3_OWNER_SOURCE_PATHS,
    }
    historical_pins = historical_toolchain_files(Path(__file__).resolve().parents[1])
    historical_manifest = historical_manifest_bytes(
        Path(__file__).resolve().parents[1], (PROJECT_ROOT / MANIFEST_PATH).read_bytes()
    )
    historical_metadata = historical_metadata_bytes(
        Path(__file__).resolve().parents[1],
        (PROJECT_ROOT / "pyproject.toml").read_bytes(),
    )
    migrated_sources = {
        "src/fep_lean/formal/gaussian_information_geometry.lean",
        "lean/FepSketches/gaussian_information_geometry.lean",
        "src/fep_lean/formal/smooth_information_geometry.lean",
        "lean/FepSketches/smooth_information_geometry.lean",
        "src/fep_lean/formal/compositions/gaussian_filter.lean",
        "lean/FepSketches/compositions/gaussian_filter.lean",
    }
    historical_only = {
        "tests/test_horizon2_gaussian_vfe_readiness.py",
        *H3_OWNER_SOURCE_PATHS,
    }
    for relative, digest in successor["source_sha256"].items():
        live = (PROJECT_ROOT / relative).read_bytes()
        if relative in historical_pins:
            historical = historical_pins[relative]
        elif relative == MANIFEST_PATH:
            historical = historical_manifest
        elif relative == "pyproject.toml":
            historical = historical_metadata
        elif relative == "uv.lock":
            historical = bridge_dev_lock_predecessor(live)
        elif relative in migrated_sources:
            canonical = relative.replace("lean/FepSketches/", "src/fep_lean/formal/", 1)
            historical = historical_carrier_bytes(canonical, live)
        elif relative in historical_only:
            # The immutable addendum above seals these historical hashes.
            # Current bytes deliberately differ and cannot reuse that evidence.
            assert hashlib.sha256(live).hexdigest() != digest, relative
            continue
        else:
            historical = live
        assert hashlib.sha256(historical).hexdigest() == digest, relative
    assert {
        relative
        for relative, digest in successor["source_sha256"].items()
        if _sha256(PROJECT_ROOT / relative) != digest
    } == set(historical_pins) | migrated_sources | historical_only | {
        MANIFEST_PATH,
        "pyproject.toml",
        "uv.lock",
    }
    assert successor["historical_custody"] == json.loads(
        (PROJECT_ROOT / SUCCESSOR_PATH).read_text(encoding="utf-8")
    )
    assert (
        successor["source_sha256"] != successor["historical_custody"]["source_sha256"]
    )
    assert successor["native_evidence"] == {
        "status": "not_executed",
        "historical_evidence_reused": False,
        "probes": [],
    }
    assert before == _production_custody_snapshot()


def test_historical_custody_control_is_positive_and_explicitly_non_native(
    tmp_path: Path,
) -> None:
    root = Path(__file__).resolve().parents[1]
    before = _production_custody_snapshot()
    originals = historical_custody_sources(root)
    restored = historical_custody_root(root, tmp_path)
    result = validate_h2_r0_custody(restored)
    assert result["decision"] == "preserve_accepted_R0"
    assert len(result["source_sha256"]) == 22
    for relative, digest in result["source_sha256"].items():
        assert _sha256(restored / relative) == digest
    assert result["native_evidence"] == {
        "status": "not_executed",
        "historical_evidence_reused": False,
        "probes": [],
    }
    for relative, data in originals.items():
        assert (restored / relative).read_bytes() == data
        assert (root / relative).read_bytes() != data
    manifest = (restored / MANIFEST_PATH).read_bytes()
    assert historical_manifest_bytes(root, manifest) == manifest
    assert (
        historical_manifest_bytes(root, (root / MANIFEST_PATH).read_bytes()) == manifest
    )
    marker = json.loads(
        (restored / "output/historical-custody-unit-control.json").read_bytes()
    )
    assert marker["source_commit"] == "5e1cc9095b5f0590772c739d27558c2c711f9a44"
    assert marker["restored_source_paths"] == sorted(result["source_sha256"])
    assert marker["manifest_archive_sha256"] == HISTORICAL_MANIFEST_ARCHIVE_SHA256
    assert marker["observed_manifest_sha256"] == _sha256(root / MANIFEST_PATH)
    assert marker["restored_manifest_sha256"] == _sha256(restored / MANIFEST_PATH)
    assert marker["observed_manifest_sha256"] != marker["restored_manifest_sha256"]
    assert marker["metadata_archive_sha256"] == HISTORICAL_METADATA_ARCHIVE_SHA256
    assert marker["observed_pyproject_sha256"] == _sha256(root / "pyproject.toml")
    assert marker["restored_pyproject_sha256"] == _sha256(restored / "pyproject.toml")
    assert marker["current_native_or_scientific_acceptance"] is False
    assert marker["archived_source_execution"] is False
    assert before == _production_custody_snapshot()

    # Exact proof-refactor replay is a static historical control, not H3 acceptance.
    from tests._support import lean435_migration as migration

    scalar = (root / "src/fep_lean/formal/scalar_gaussian_semigroup.lean").read_bytes()
    archived = (root / migration._HISTORICAL_SCALAR_REPLAY).read_bytes()
    assert (
        migration.historical_scalar_static_replay_source(scalar, archived) == archived
    )
    with pytest.raises(AssertionError, match="unrecognized live scalar"):
        migration.historical_scalar_static_replay_source(scalar + b"\n", archived)
    with pytest.raises(AssertionError, match="archive identity changed"):
        migration.historical_scalar_static_replay_source(scalar, archived + b"\n")
    changed_statement = scalar.replace(
        b"model.ouNativeSemigroup model.stationaryLaw := by",
        b"model.ouNativeSemigroup (0 : Measure Real) := by",
        1,
    )
    assert changed_statement != scalar
    with pytest.raises(AssertionError, match="unrecognized live scalar"):
        migration.historical_scalar_static_replay_source(changed_statement, archived)


@pytest.mark.parametrize("tamper", ("append", "metadata", "payload"))
def test_historical_custody_archive_tampering_is_rejected_before_decode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, tamper: str
) -> None:
    from tests._support import lean435_migration as migration

    root = Path(__file__).resolve().parents[1]
    before = _production_custody_snapshot()
    raw = (root / migration.HISTORICAL_CUSTODY_ARCHIVE).read_bytes()
    if tamper == "append":
        changed = raw + b"\n"
    else:
        payload = json.loads(raw)
        if tamper == "metadata":
            payload["source_commit"] = "0" * 40
        else:
            relative = next(iter(payload["files"]))
            payload["files"][relative]["data"] = "not-archived-source"
        changed = json.dumps(payload).encode()
    resource = tmp_path / migration.HISTORICAL_CUSTODY_ARCHIVE
    resource.parent.mkdir(parents=True)
    resource.write_bytes(changed)

    def forbidden_decode() -> None:
        pytest.fail("a changed archive must fail its identity check before decoding")

    monkeypatch.setattr(migration.zlib, "decompressobj", forbidden_decode)
    with pytest.raises(
        AssertionError, match="historical custody archive identity changed"
    ):
        historical_custody_sources(tmp_path)
    assert before == _production_custody_snapshot()


@pytest.mark.parametrize("tamper", ("append", "metadata", "payload"))
def test_historical_manifest_companion_tampering_refuses_before_decode_and_writing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, tamper: str
) -> None:
    from tests._support import lean435_migration as migration

    root = Path(__file__).resolve().parents[1]
    before = _production_custody_snapshot()
    source = tmp_path / "changed-input"
    destination = tmp_path / "historical-control"
    destination.mkdir()
    _copy_historical_custody_inputs(root, source)
    resource = source / HISTORICAL_MANIFEST_ARCHIVE
    raw = resource.read_bytes()
    if tamper == "append":
        changed = raw + b"\n"
    else:
        payload = json.loads(raw)
        if tamper == "metadata":
            payload["source_commit"] = "0" * 40
        else:
            payload["files"][MANIFEST_PATH]["data"] = "not-archived-source"
        changed = json.dumps(payload).encode()
    resource.write_bytes(changed)

    def forbidden_decode() -> None:
        pytest.fail("a changed companion must fail before any source decoding")

    monkeypatch.setattr(migration.zlib, "decompressobj", forbidden_decode)
    with pytest.raises(
        AssertionError, match="historical custody manifest archive identity changed"
    ):
        historical_custody_root(source, destination)
    assert not any(destination.iterdir())
    assert before == _production_custody_snapshot()


@pytest.mark.parametrize("profile", ("predecessor", "T01", "P09", "P08", "P08_P09"))
@pytest.mark.parametrize("version", ("1.4.0", *LATER_RELEASE_VERSIONS))
def test_historical_metadata_preserves_only_explicit_release_profiles(
    profile: str, version: str
) -> None:
    root = Path(__file__).resolve().parents[1]
    before = _production_custody_snapshot()
    live = (root / "pyproject.toml").read_bytes()
    historical = historical_metadata_bytes(root, live)
    live = bridge_dev_metadata_predecessor(live)
    recorded_token = RELEASE_METADATA_REPLACEMENTS["pyproject.toml"][1].encode()
    current_token = recorded_token.replace(b'"1.4.0"', b'"1.6.0"')
    # Keep these exact historical profile digests in their recorded 1.6.0 epoch.
    live_token = recorded_token.replace(b'"1.4.0"', f'"{__version__}"'.encode())
    assert live.count(live_token) == 1
    live = live.replace(live_token, current_token, 1)
    if profile == "predecessor":
        uv_pin = b'\n[tool.uv]\nrequired-version = "==0.13.0"\n'
        assert historical.count(b"\n[project]\n") == 1
        data = historical.replace(b"\n[project]\n", uv_pin + b"\n[project]\n", 1)
        assert hashlib.sha256(
            data.replace(recorded_token, current_token, 1)
        ).hexdigest() == (
            "5ad8bcdd8d2cd55629a0f7c91d7133cbec42081ee893e325f43e18140ab0eb79"
        )
    else:
        assert (
            hashlib.sha256(live).hexdigest()
            == "7b3109accc06616e9cb2fffe50babbe4216ddfc9a8bc154a0a0be09376084e2c"
        )
        if profile in {"T01", "P08"}:
            reviewed_note = (
                b"# Aggregate line coverage only; branch arcs are not enabled or gated here.\n"
                b"# docs/coverage-floors.json owns additional measured package line floors.\n"
            )
            assert live.count(reviewed_note) == 1
            live = live.replace(
                reviewed_note,
                b"# Line coverage ~91%; combined line+branch ~89.6% with current Hermes/network branches.\n",
                1,
            )
        if profile in {"T01", "P09"}:
            marker = b'timeout_method = "thread"\n'
            filters = (
                b"filterwarnings = [\n"
                b'    "ignore::UserWarning",\n'
                b'    "ignore::pytest.PytestWarning",\n'
                b'    "ignore::DeprecationWarning",\n'
                b"]\n"
            )
            assert live.count(marker) == 1
            live = live.replace(marker, marker + filters, 1)
        expected_live_digest = {
            "T01": "ab94d6fa723dbb547e3e73f70d826060ab63e873e812922cbb30ef090d7d3d3e",
            "P09": "bd0c17f95d13206cee7f55b7bdaa45745da0a7aa0ae0d9a8d9bfe3ae717eafae",
            "P08": "7cddff7d00c626e1838f955480c425f187ea04d10b049708ee22366828cc7282",
            "P08_P09": "7b3109accc06616e9cb2fffe50babbe4216ddfc9a8bc154a0a0be09376084e2c",
        }[profile]
        assert hashlib.sha256(live).hexdigest() == expected_live_digest
        assert live.count(current_token) == 1
        data = live.replace(current_token, recorded_token, 1)
    token = recorded_token.replace(b'"1.4.0"', f'"{version}"'.encode())
    assert (
        historical_metadata_bytes(root, data.replace(recorded_token, token, 1))
        == historical
    )
    assert before == _production_custody_snapshot()


@pytest.mark.parametrize("tamper", ("append", "metadata", "payload"))
def test_metadata_companion_tampering_refuses_before_parse_decode_and_writing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, tamper: str
) -> None:
    from tests._support import lean435_migration as migration

    root = Path(__file__).resolve().parents[1]
    before = _production_custody_snapshot()
    source = tmp_path / "changed-input"
    destination = tmp_path / "historical-control"
    destination.mkdir()
    _copy_historical_custody_inputs(root, source)
    resource = source / HISTORICAL_METADATA_ARCHIVE
    raw = resource.read_bytes()
    if tamper == "append":
        changed = raw + b"\n"
    else:
        payload = json.loads(raw)
        if tamper == "metadata":
            payload["source_commit"] = "0" * 40
        else:
            payload["files"]["pyproject.toml"]["data"] = "not-archived-source"
        changed = json.dumps(payload).encode()
    resource.write_bytes(changed)
    original_loads = migration.json.loads

    def refuse_companion_parse(data: bytes, *args: object, **kwargs: object) -> object:
        assert data != changed, "changed companion was parsed before authentication"
        return original_loads(data, *args, **kwargs)

    def forbidden_decode() -> None:
        pytest.fail("changed companion must fail before any source decoding")

    monkeypatch.setattr(migration.json, "loads", refuse_companion_parse)
    monkeypatch.setattr(migration.zlib, "decompressobj", forbidden_decode)
    with pytest.raises(
        AssertionError, match="historical custody metadata archive identity changed"
    ):
        historical_custody_root(source, destination)
    assert not any(destination.iterdir())
    assert before == _production_custody_snapshot()


@pytest.mark.parametrize(
    "tamper",
    (
        "spike",
        "owner",
        "manifest",
        "category_role",
        "metadata_dependency",
        "metadata_unknown_release",
        "metadata_duplicate_root",
        "metadata_uv_pin",
    ),
)
def test_historical_custody_control_refuses_source_drift_before_writing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, tamper: str
) -> None:
    root = Path(__file__).resolve().parents[1]
    before = _production_custody_snapshot()
    source = tmp_path / "changed-input"
    destination = tmp_path / "historical-control"
    destination.mkdir()
    _copy_historical_custody_inputs(root, source)
    relative = {
        "spike": "specs/done/horizon-2-smooth-stochastic/spikes/07_gaussian_vfe_natural_gradient.lean",
        "owner": "src/fep_lean/formal/gaussian_information_geometry.lean",
        "manifest": MANIFEST_PATH,
        "category_role": MANIFEST_PATH,
    }.get(tamper, "pyproject.toml")
    changed = source / relative
    data = changed.read_bytes()
    if tamper == "category_role":
        owner = (
            b'        resource="compositions/finite_kernel_category.lean",\n'
            b'        lean_module="FepSketches.compositions.finite_kernel_category",\n'
            b"        role=FormalModuleRole.COMPOSITION,\n"
        )
        assert data.count(owner) == 1
        data = data.replace(owner, owner.replace(b"COMPOSITION", b"FOUNDATION"), 1)
    elif tamper.startswith("metadata_"):
        from tests._support import lean435_migration as migration

        def forbidden_decode() -> None:
            pytest.fail("unknown live metadata must fail before source decoding")

        monkeypatch.setattr(migration.zlib, "decompressobj", forbidden_decode)
        if tamper == "metadata_dependency":
            data = data.replace(b'"numpy>=1.24.0"', b'"numpy>=1.25.0"', 1)
        elif tamper == "metadata_unknown_release":
            current = f'version = "{__version__}"'.encode()
            assert data.count(current) == 1
            data = data.replace(current, b'version = "9.9.9"', 1)
        elif tamper == "metadata_duplicate_root":
            data += (
                f'\n[project]\nname = "fep_lean"\nversion = "{__version__}"\n'.encode()
            )
        else:
            data = data.replace(
                b'required-version = "==0.13.0"', b'required-version = "==0.13.1"', 1
            )
        assert data != changed.read_bytes()
    else:
        data += b"\n-- unreviewed source change\n"
    changed.write_bytes(data)
    with pytest.raises(AssertionError, match=re.escape(relative)):
        historical_custody_root(source, destination)
    assert not any(destination.iterdir())
    assert before == _production_custody_snapshot()


@pytest.mark.parametrize(
    "tamper",
    (
        "prior",
        "unlisted_owner",
        "duplicate_owner",
        "missing_owner",
        "changed_owner_role",
        "stale_source",
        "expanded_downstream",
        "expanded_allowance",
        "native_claim_without_probes",
    ),
)
def test_h2_7_r0_custody_rejects_tampering(tmp_path: Path, tamper: str) -> None:
    before = _production_custody_snapshot()
    # Exact original bound bytes, not a rebased current epoch: the unchanged
    # validator must accept this historical static control before mutation.
    historical_custody_root(Path(__file__).resolve().parents[1], tmp_path)
    successor_path = tmp_path / SUCCESSOR_PATH
    successor_bytes = successor_path.read_bytes()
    successor = json.loads(successor_bytes)
    manifest_path = tmp_path / MANIFEST_PATH
    manifest = manifest_path.read_text(encoding="utf-8")
    owner = (
        "    FormalModule(\n"
        '        resource="gnn_document.lean",\n'
        '        lean_module="FepSketches.gnn_document",\n'
        "        role=FormalModuleRole.FOUNDATION,\n"
        '        declaration_namespace="FEP.GnnDocument",\n'
        "    ),\n"
    )
    assert manifest.count(owner) == 1
    if tamper == "prior":
        path = tmp_path / PRIOR_PATH
        path.write_bytes(path.read_bytes() + b"\n")
    elif tamper == "unlisted_owner":
        manifest = manifest.replace(
            owner,
            owner
            + owner.replace("gnn_document", "unreviewed").replace(
                "GnnDocument", "Unreviewed"
            ),
            1,
        )
    elif tamper == "duplicate_owner":
        manifest = manifest.replace(owner, owner + owner, 1)
    elif tamper == "missing_owner":
        manifest = manifest.replace(owner, "", 1)
    elif tamper == "changed_owner_role":
        manifest = manifest.replace(
            'lean_module="FepSketches.gaussian_information_geometry",\n'
            "        role=FormalModuleRole.FOUNDATION,",
            'lean_module="FepSketches.gaussian_information_geometry",\n'
            "        role=FormalModuleRole.COMPOSITION,",
            1,
        )
    elif tamper == "stale_source":
        path = tmp_path / SPIKE.relative_to(PROJECT_ROOT)
        path.write_bytes(path.read_bytes() + b"\n")
    elif tamper == "expanded_downstream":
        successor["downstream"]["opened"].append("H3 implementation")
    elif tamper == "expanded_allowance":
        successor["allowed_prior_source_changes"].append(
            str(SPIKE.relative_to(PROJECT_ROOT))
        )
    else:
        successor["native_evidence"] = {
            "status": "verified",
            "historical_evidence_reused": False,
            "probes": [],
        }
    if "owner" in tamper:
        assert manifest != manifest_path.read_text(encoding="utf-8")
        manifest_path.write_text(manifest, encoding="utf-8")
        # Even rebinding the live manifest hash must not authorize owner drift.
        digest = _sha256(manifest_path)
        successor["source_sha256"][MANIFEST_PATH] = digest
        successor["manifest_transition"]["current_sha256"] = digest
    # A semantically unchanged successor keeps its original sealed bytes,
    # allowing source-only tampering to reach its own source-digest guard.
    if successor != json.loads(successor_bytes):
        successor_path.write_text(json.dumps(successor), encoding="utf-8")
    expected = {
        "prior": "immutable R0 prior changed",
        "stale_source": "stale historical custody source digest",
    }.get(tamper, "immutable R0 custody successor changed")
    with pytest.raises(ValueError, match=f"^{re.escape(expected)}$"):
        validate_h2_r0_custody(tmp_path)
    assert before == _production_custody_snapshot()


@pytest.mark.parametrize(
    "tamper",
    (
        "missing_h3_owner",
        "unlisted_h3_owner",
        "duplicate_h3_owner",
        "reordered_h3_owner",
        "changed_h3_role",
        "changed_h3_namespace",
        "manifest_code",
        "h3_owner_source",
        "addendum_prior",
        "addendum_boolean_schema",
        "addendum_modules",
        "addendum_sources",
        "addendum_historical_support",
        "addendum_support_allowance",
        "addendum_downstream",
        "addendum_native",
        "addendum_numeric_native_flag",
        "release_dependency_drift",
        "release_lock_dependency_drift",
        "release_lock_schema_drift",
        "release_version_drift",
        "release_duplicate_root",
        "release_missing_transition",
        "release_transition_digest",
        "release_transition_allowance",
    ),
)
def test_h2_7_h3_custody_addendum_rejects_tampering(
    tmp_path: Path, tamper: str
) -> None:
    before = _production_custody_snapshot()
    # Exact original bound bytes, not a rebased current epoch: the unchanged
    # validator must accept this historical static control before mutation.
    historical_custody_root(Path(__file__).resolve().parents[1], tmp_path)
    addendum_path = tmp_path / H3_ADDENDUM_PATH
    addendum = json.loads(addendum_path.read_text(encoding="utf-8"))
    manifest_path = tmp_path / MANIFEST_PATH
    manifest = manifest_path.read_text(encoding="utf-8")
    block = (
        "    FormalModule(\n"
        '        resource="h3_reference_model.lean",\n'
        '        lean_module="FepSketches.h3_reference_model",\n'
        "        role=FormalModuleRole.FOUNDATION,\n"
        '        declaration_namespace="FEP.H3ReferenceModel",\n'
        "    ),\n"
    )
    assert manifest.count(block) == 1
    if tamper == "missing_h3_owner":
        manifest = manifest.replace(block, "", 1)
    elif tamper == "unlisted_h3_owner":
        manifest = manifest.replace(
            block,
            block
            + block.replace("h3_reference_model", "unreviewed_h3_model").replace(
                "H3ReferenceModel", "UnreviewedH3Model"
            ),
            1,
        )
    elif tamper == "duplicate_h3_owner":
        manifest = manifest.replace(block, block + block, 1)
    elif tamper == "reordered_h3_owner":
        manifest = manifest.replace(block, "", 1).replace(
            "FORMAL_MODULES: tuple[FormalModule, ...] = (\n",
            "FORMAL_MODULES: tuple[FormalModule, ...] = (\n" + block,
            1,
        )
    elif tamper == "changed_h3_role":
        manifest = manifest.replace(
            block, block.replace("FOUNDATION", "COMPOSITION"), 1
        )
    elif tamper == "changed_h3_namespace":
        manifest = manifest.replace(
            block, block.replace("FEP.H3ReferenceModel", "FEP.OtherH3Model"), 1
        )
    elif tamper == "manifest_code":
        manifest = manifest.replace(
            "Single explicit roster", "Tampered explicit roster", 1
        )
    elif tamper == "h3_owner_source":
        path = tmp_path / H3_OWNER_SOURCE_PATHS[0]
        path.write_bytes(path.read_bytes() + b"\n")
    elif tamper in {
        "release_dependency_drift",
        "release_lock_dependency_drift",
        "release_lock_schema_drift",
        "release_version_drift",
        "release_duplicate_root",
    }:
        relative = (
            "uv.lock"
            if tamper in {"release_lock_dependency_drift", "release_lock_schema_drift"}
            else "pyproject.toml"
        )
        path = tmp_path / relative
        contents = path.read_text(encoding="utf-8")
        if tamper == "release_dependency_drift":
            altered = contents.replace("numpy>=1.24.0", "numpy>=1.25.0", 1)
        elif tamper == "release_lock_dependency_drift":
            altered = contents.replace('version = "2.5.1"', 'version = "2.5.2"', 1)
        elif tamper == "release_lock_schema_drift":
            altered = contents.replace("revision = 3\n", "revision = 5\n", 1)
        elif tamper == "release_version_drift":
            altered = contents.replace('version = "1.4.0"', 'version = "1.5.0"', 1)
        else:
            altered = contents + '\n[project]\nname = "fep_lean"\nversion = "1.4.0"\n'
        assert altered != contents
        path.write_text(altered, encoding="utf-8")
        # Coherently rebinding the new bytes never authorizes another delta.
        digest = _sha256(path)
        addendum["source_sha256"][relative] = digest
        addendum["release_metadata_transition"]["sources"][relative][
            "current_sha256"
        ] = digest
    elif tamper == "release_missing_transition":
        del addendum["release_metadata_transition"]
    elif tamper == "release_transition_digest":
        addendum["release_metadata_transition"]["sources"]["pyproject.toml"][
            "historical_sha256"
        ] = "0" * 64
    elif tamper == "release_transition_allowance":
        addendum["release_metadata_transition"]["sources"]["config/settings.yaml"] = {}
    elif tamper == "addendum_prior":
        addendum["prior_custody"]["sha256"] = "0" * 64
    elif tamper == "addendum_boolean_schema":
        addendum["schema_version"] = True
    elif tamper == "addendum_modules":
        addendum["manifest_transition"]["added_modules"] = [
            dict(owner) for owner in reversed(H3_ADDED_OWNERS)
        ]
    elif tamper == "addendum_sources":
        addendum["source_sha256"][VALIDATOR_PATH] = "0" * 64
    elif tamper == "addendum_historical_support":
        addendum["historical_support_source_sha256"][VALIDATOR_PATH] = "0" * 64
    elif tamper == "addendum_support_allowance":
        addendum["approved_custody_support_changes"].append("pyproject.toml")
    elif tamper == "addendum_downstream":
        addendum["downstream"]["opened"].append("H3 implementation")
    elif tamper == "addendum_numeric_native_flag":
        addendum["native_evidence"]["historical_evidence_reused"] = 0
    else:
        addendum["native_evidence"]["status"] = "verified"
    if (
        tamper.endswith("h3_owner")
        or tamper.startswith("changed_h3_")
        or tamper == "manifest_code"
    ):
        assert manifest != manifest_path.read_text(encoding="utf-8")
        manifest_path.write_text(manifest, encoding="utf-8")
        # A matching current digest cannot authorize different owner bytes,
        # order, roles, or changes to any reconstructed historical code.
        digest = _sha256(manifest_path)
        addendum["source_sha256"][MANIFEST_PATH] = digest
        addendum["manifest_transition"]["current_sha256"] = digest
    addendum_path.write_text(json.dumps(addendum), encoding="utf-8")
    expected = H3_TAMPER_ERRORS[tamper]
    with pytest.raises(ValueError, match=f"^{re.escape(expected)}$"):
        validate_h2_r0_custody(tmp_path)
    assert before == _production_custody_snapshot()
