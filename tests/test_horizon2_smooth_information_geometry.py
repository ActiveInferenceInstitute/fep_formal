"""H2.2a scalar-chart duality, flatness, and rank-boundary contracts."""

from __future__ import annotations

import re
import tempfile
from pathlib import Path

import pytest

from fep_lean.formal.manifest import FORMAL_MODULES, FormalModuleRole
from fep_lean.formal.projection import formal_projection_drift
from fep_lean.lean_source import lean_code_without_comments
from tests._support.lake import lake_executable
from tests._support.lean_runner import run_lean_compile_probe

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEAN_ROOT = PROJECT_ROOT / "lean"
FOUNDATION = (
    PROJECT_ROOT / "src" / "fep_lean" / "formal" / "smooth_information_geometry.lean"
)
PROJECTION = LEAN_ROOT / "FepSketches" / "smooth_information_geometry.lean"

pytestmark = pytest.mark.serial_lean

EXACT_IMPORTS = (
    "FepSketches.gaussian_information_geometry",
    "Mathlib.Analysis.Calculus.Deriv.Mul",
    "Mathlib.Analysis.Calculus.FDeriv.Pi",
)
PUBLIC_DEFINITIONS = (
    "naturalMetricPairing",
    "meanMetricPairing",
    "naturalAffinePath",
    "duplicatedMeanJacobian",
    "duplicatedMeanMap",
    "duplicatedMeanPullbackMetric",
    "duplicatedNullTangent",
)
PUBLIC_THEOREMS = (
    "duplicatedMeanMap_hasFDerivAt",
    "naturalMetricPairing_eq_variance",
    "meanMetricPairing_eq_invVariance",
    "meanMetricPairing_eq_naturalPullback",
    "naturalMean_coordinateBasis_dual",
    "flatNaturalMean_duality_hasDerivAt",
    "naturalMetricComponent_hasDerivAt_zero",
    "meanMetricComponent_hasDerivAt_zero",
    "naturalAffinePath_hasDerivAt",
    "naturalAffinePathVelocity_hasDerivAt_zero",
    "naturalToMean_naturalAffinePath",
    "klDiv_meanCoordinates_eq_naturalBregman",
    "duplicatedMeanJacobian_nullTangent",
    "duplicatedNullTangent_ne_zero",
    "duplicatedMeanPullbackMetric_null",
    "duplicatedMeanPullback_not_positiveDefinite",
)

SCIENTIFIC_CONTRACTS = r"""
open MeasureTheory ProbabilityTheory
open scoped ENNReal MeasureTheory NNReal ProbabilityTheory

example (family : FEP.GaussianInformationGeometry.FixedVarianceGaussian)
    (mean left right : ℝ) :
    FEP.SmoothInformationGeometry.meanMetricPairing family mean left right =
      FEP.SmoothInformationGeometry.naturalMetricPairing family
        (family.meanToNatural mean)
        ((family.variance : ℝ)⁻¹ * left)
        ((family.variance : ℝ)⁻¹ * right) :=
  FEP.SmoothInformationGeometry.meanMetricPairing_eq_naturalPullback
    family mean left right

example (family : FEP.GaussianInformationGeometry.FixedVarianceGaussian)
    (time : ℝ) (exponentialField mixtureField : ℝ → ℝ)
    (exponentialDerivative mixtureDerivative : ℝ)
    (hExponential : HasDerivAt exponentialField exponentialDerivative time)
    (hMixture : HasDerivAt mixtureField mixtureDerivative time) :
    HasDerivAt
      (fun candidate =>
        FEP.SmoothInformationGeometry.naturalMetricPairing family candidate
          (exponentialField candidate)
          ((family.variance : ℝ)⁻¹ * mixtureField candidate))
      (FEP.SmoothInformationGeometry.naturalMetricPairing family time
          exponentialDerivative
          ((family.variance : ℝ)⁻¹ * mixtureField time) +
        FEP.SmoothInformationGeometry.naturalMetricPairing family time
          (exponentialField time)
          ((family.variance : ℝ)⁻¹ * mixtureDerivative)) time :=
  FEP.SmoothInformationGeometry.flatNaturalMean_duality_hasDerivAt
    family time exponentialField mixtureField exponentialDerivative
    mixtureDerivative hExponential hMixture

example (family : FEP.GaussianInformationGeometry.FixedVarianceGaussian)
    (sourceMean referenceMean : ℝ) :
    InformationTheory.klDiv
        (family.law sourceMean) (family.law referenceMean) =
      ENNReal.ofReal
        (family.naturalBregman
          (family.meanToNatural sourceMean)
          (family.meanToNatural referenceMean)) :=
  FEP.SmoothInformationGeometry.klDiv_meanCoordinates_eq_naturalBregman
    family sourceMean referenceMean

example (parameter : Fin 2 → ℝ) :
    HasFDerivAt FEP.SmoothInformationGeometry.duplicatedMeanMap
      FEP.SmoothInformationGeometry.duplicatedMeanJacobian parameter :=
  FEP.SmoothInformationGeometry.duplicatedMeanMap_hasFDerivAt parameter

example (family : FEP.GaussianInformationGeometry.FixedVarianceGaussian)
    (parameter left right : Fin 2 → ℝ) :
    FEP.SmoothInformationGeometry.duplicatedMeanPullbackMetric
        family parameter left right =
      FEP.SmoothInformationGeometry.meanMetricPairing family
        (FEP.SmoothInformationGeometry.duplicatedMeanMap parameter)
        (FEP.SmoothInformationGeometry.duplicatedMeanJacobian left)
        (FEP.SmoothInformationGeometry.duplicatedMeanJacobian right) := rfl

example :
    FEP.SmoothInformationGeometry.duplicatedMeanJacobian
        FEP.SmoothInformationGeometry.duplicatedNullTangent = 0 :=
  FEP.SmoothInformationGeometry.duplicatedMeanJacobian_nullTangent

example : FEP.SmoothInformationGeometry.duplicatedNullTangent ≠ 0 :=
  FEP.SmoothInformationGeometry.duplicatedNullTangent_ne_zero

example (family : FEP.GaussianInformationGeometry.FixedVarianceGaussian)
    (parameter : Fin 2 → ℝ) :
    ¬ ∀ tangent : Fin 2 → ℝ, tangent ≠ 0 →
      0 < FEP.SmoothInformationGeometry.duplicatedMeanPullbackMetric
        family parameter tangent tangent :=
  FEP.SmoothInformationGeometry.duplicatedMeanPullback_not_positiveDefinite
    family parameter
"""


def test_h2_2a_has_one_exact_foundation_owner() -> None:
    assert FOUNDATION.is_file()
    source = FOUNDATION.read_text(encoding="utf-8")
    owners = [
        module
        for module in FORMAL_MODULES
        if module.resource == "smooth_information_geometry.lean"
    ]

    assert len(owners) == 1
    owner = owners[0]
    assert owner.lean_module == "FepSketches.smooth_information_geometry"
    assert owner.role is FormalModuleRole.FOUNDATION
    assert owner.declaration_namespace == "FEP.SmoothInformationGeometry"
    assert tuple(re.findall(r"(?m)^import (\S+)$", source)) == EXACT_IMPORTS
    assert "namespace FEP.SmoothInformationGeometry\n" in source
    assert source.rstrip().endswith("end FEP.SmoothInformationGeometry")


def test_h2_2a_public_surface_is_exact_and_has_no_parallel_geometry_hierarchy() -> None:
    source = lean_code_without_comments(FOUNDATION.read_text(encoding="utf-8"))

    assert (
        tuple(re.findall(r"(?m)^noncomputable def (\w+)\b", source))
        == PUBLIC_DEFINITIONS
    )
    assert tuple(re.findall(r"(?m)^theorem (\w+)\b", source)) == PUBLIC_THEOREMS
    assert not re.search(r"(?m)^(?:structure|class|inductive|abbrev)\s", source)
    assert not re.search(
        r"\b(?:Riemannian|Christoffel|Curvature|CovariantDerivative)\b", source
    )
    assert not re.search(
        r"\b(?:sorry|admit|axiom|opaque)\b|unsafe\s+(?:def|theorem)|:\s*True\b",
        source,
    )


def test_h2_2a_metric_duality_and_rank_boundary_are_theorem_visible() -> None:
    source = lean_code_without_comments(FOUNDATION.read_text(encoding="utf-8"))

    assert "family.naturalFisher natural" in source
    assert "family.meanFisher mean" in source
    assert "family.meanToNatural mean" in source
    assert "naturalMetricPairing family natural" in source
    assert "HasDerivAt exponentialField" in source
    assert "HasDerivAt mixtureField" in source
    assert "family.naturalBregman" in source
    assert "InformationTheory.klDiv" in source
    assert "duplicatedNullTangent ≠ 0" in source
    assert "HasFDerivAt duplicatedMeanMap duplicatedMeanJacobian" in source
    assert "duplicatedMeanMap parameter" in source
    assert "duplicatedMeanPullbackMetric" in source
    assert "= 0" in source


def test_h2_2a_projection_and_manifest_are_current() -> None:
    assert PROJECTION.read_bytes() == FOUNDATION.read_bytes()
    assert formal_projection_drift(PROJECT_ROOT) == ()


def test_h2_2a_foundation_compiles_warning_free() -> None:
    with tempfile.TemporaryDirectory(prefix="fep-h2-2a-") as output_dir:
        output_path = Path(output_dir) / "smooth_information_geometry.olean"
        result = run_lean_compile_probe(
            FOUNDATION,
            cwd=LEAN_ROOT,
            import_root=PROJECT_ROOT / "src" / "fep_lean" / "formal",
            output_path=output_path,
            timeout_s=300,
            executable=lake_executable(
                missing="raise",
                context="H2.2a native acceptance",
            ),
        )
        assert output_path.is_file(), result.stdout + result.stderr

    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "warning:" not in output.lower()


def test_h2_2a_public_theorems_use_only_standard_axioms(tmp_path: Path) -> None:
    probe = tmp_path / "SmoothInformationGeometryAxioms.lean"
    source = FOUNDATION.read_text(encoding="utf-8")
    prints = "\n".join(
        f"#print axioms FEP.SmoothInformationGeometry.{name}"
        for name in PUBLIC_THEOREMS
    )
    probe.write_text(f"{source}\n{prints}\n{SCIENTIFIC_CONTRACTS}\n", encoding="utf-8")
    result = run_lean_compile_probe(
        probe,
        cwd=LEAN_ROOT,
        import_root=PROJECT_ROOT / "src" / "fep_lean" / "formal",
        timeout_s=300,
        executable=lake_executable(
            missing="raise",
            context="H2.2a native acceptance",
        ),
    )

    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "sorryAx" not in output
    assert "warning:" not in output.lower()
    axiom_blocks = re.findall(r"depends on axioms: \[(.*?)\]", output, flags=re.DOTALL)
    assert len(axiom_blocks) == len(PUBLIC_THEOREMS), output
    for block in axiom_blocks:
        axioms = set(re.findall(r"'([^']+)'", block))
        assert axioms <= {"propext", "Classical.choice", "Quot.sound"}
