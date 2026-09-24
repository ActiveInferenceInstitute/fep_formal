"""H2.7-R0 continuous Gaussian VFE and natural-gradient proof gate."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from fep_lean.formal.manifest import FORMAL_MODULES
from fep_lean.lean_source import lean_code_without_comments
from tests._support.h2_r0_custody import (
    MANIFEST_PATH,
    PRIOR_PATH,
    SUCCESSOR_PATH,
    VALIDATOR_PATH,
    validate_h2_r0_custody,
)
from tests._support.lake import lake_executable
from tests._support.lean_runner import (
    run_lake_lean_probe,
    run_lean_compile_probe,
    run_lean_probe,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEAN_ROOT = PROJECT_ROOT / "lean"
SPIKE = (
    PROJECT_ROOT
    / "specs"
    / "horizon-2-smooth-stochastic"
    / "spikes"
    / "07_gaussian_vfe_natural_gradient.lean"
)
SLICE = (
    PROJECT_ROOT
    / "specs"
    / "horizon-2-smooth-stochastic"
    / "slices"
    / "07-r0-gaussian-vfe-natural-gradient.md"
)
REPAIR = (
    PROJECT_ROOT
    / "specs"
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
    "specs/horizon-2-smooth-stochastic/readiness/acceptance.json",
    "specs/horizon-2-smooth-stochastic/readiness/matrix.yaml",
    "src/fep_lean/formal/manifest.py",
    "src/fep_lean/formal/gaussian_information_geometry.lean",
    "lean/FepSketches/gaussian_information_geometry.lean",
    "src/fep_lean/formal/smooth_information_geometry.lean",
    "lean/FepSketches/smooth_information_geometry.lean",
    "src/fep_lean/formal/compositions/gaussian_filter.lean",
    "lean/FepSketches/compositions/gaussian_filter.lean",
    "specs/horizon-2-smooth-stochastic/slices/07-r0-gaussian-vfe-natural-gradient.md",
    "specs/horizon-2-smooth-stochastic/spikes/07_gaussian_vfe_natural_gradient.lean",
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


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _parse_axiom_names(block: str) -> frozenset[str]:
    return frozenset(
        token.strip().strip("'")
        for token in block.replace("\n", " ").split(",")
        if token.strip().strip("'")
    )


def _axiom_reports(output: str) -> dict[str, frozenset[str]]:
    reports: dict[str, frozenset[str]] = {}
    for name in PUBLIC_THEOREMS:
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


def _namespace_names(output: str) -> frozenset[str]:
    prefix = re.escape(f"{NAMESPACE}.")
    return frozenset(re.findall(rf"(?m)^{prefix}([A-Za-z_][A-Za-z0-9_']*)\b", output))


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
    assert (LEAN_ROOT / "lean-toolchain").read_text(encoding="utf-8").strip() == (
        "leanprover/lean4:v4.34.0"
    )
    manifest = json.loads((LEAN_ROOT / "lake-manifest.json").read_text("utf-8"))
    mathlib = next(
        package for package in manifest["packages"] if package["name"] == "mathlib"
    )
    assert mathlib["rev"] == "5ed2965256430c3649e86755f9576b54eca72435"
    assert mathlib["inputRev"] == "v4.34.0"
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
    assert version_line.startswith("Lean (version 4.34.0, "), version_line
    assert "commit 293d5d0c0c3f3dded4688b3ccd6a33939ac5102b, Release)" in version_line


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
        r"(?P<body>.*?)(?=\n\nnoncomputable def meanNaturalGradient\b)",
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
        r"(?=\n\ntheorem evidenceLaw_eq_volume_withDensity\b)",
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
    suffix += "\n".join(f"#print axioms {NAMESPACE}.{name}" for name in PUBLIC_THEOREMS)
    suffix += f"\n#print prefix {NAMESPACE}\n"
    result = _run_lean(SPIKE.read_text(encoding="utf-8") + suffix)
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "warning:" not in output
    assert "sorryAx" not in output
    reports = _axiom_reports(output)
    assert set(reports) == set(PUBLIC_THEOREMS)
    assert all(axioms <= ALLOWED_AXIOMS for axioms in reports.values())
    actual = _namespace_names(output)
    assert actual == PUBLIC_ENVIRONMENT, (
        f"missing={sorted(PUBLIC_ENVIRONMENT - actual)}; "
        f"extra={sorted(actual - PUBLIC_ENVIRONMENT)}"
    )


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
    successor = validate_h2_r0_custody(PROJECT_ROOT)
    assert REPAIR.is_file()
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
            "../specs/horizon-2-smooth-stochastic/spikes/"
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
    assert successor["source_sha256"] == {
        relative: _sha256(PROJECT_ROOT / relative)
        for relative in (*SOURCE_BOUND_PATHS, VALIDATOR_PATH)
    }


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
    for relative in (*SOURCE_BOUND_PATHS, VALIDATOR_PATH, PRIOR_PATH, SUCCESSOR_PATH):
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(PROJECT_ROOT / relative, destination)
    successor_path = tmp_path / SUCCESSOR_PATH
    successor = json.loads(successor_path.read_text(encoding="utf-8"))
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
    successor_path.write_text(json.dumps(successor), encoding="utf-8")
    with pytest.raises(ValueError):
        validate_h2_r0_custody(tmp_path)
