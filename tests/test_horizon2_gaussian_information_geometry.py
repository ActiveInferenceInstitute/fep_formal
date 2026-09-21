"""H2.1a fixed-variance scalar Gaussian and native-KL contracts."""

from __future__ import annotations

import re
import tempfile
from pathlib import Path

import pytest

from fep_lean.formal.manifest import (
    FORMAL_MODULES,
    FormalModuleRole,
    formal_module_imports,
    formal_resource_manifest_drift,
)
from fep_lean.formal.projection import formal_projection_drift
from fep_lean.lean_source import lean_code_without_comments
from tests._support.lake import lake_executable
from tests._support.lean_runner import run_lean_compile_probe

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEAN_ROOT = PROJECT_ROOT / "lean"
FOUNDATION = (
    PROJECT_ROOT / "src" / "fep_lean" / "formal" / "gaussian_information_geometry.lean"
)
PROJECTION = LEAN_ROOT / "FepSketches" / "gaussian_information_geometry.lean"

pytestmark = pytest.mark.serial_lean

EXACT_IMPORTS = (
    "Mathlib.Analysis.Calculus.Deriv.Mul",
    "Mathlib.InformationTheory.KullbackLeibler.Basic",
    "Mathlib.Probability.Distributions.Gaussian.Real",
)
PUBLIC_THEOREMS = (
    "law_eq_gaussianReal",
    "density_support",
    "law_eq_withDensity",
    "density_lintegral_eq_one",
    "law_univ",
    "law_rnDeriv_volume",
    "law_mutuallyAbsolutelyContinuous",
    "klDiv_law_eq_meanSquare",
    "klDiv_law_self",
    "klDiv_law_pos_of_ne",
    "zero_variance_excluded",
)


def test_h2_1a_owner_is_manifested_once_with_exact_imports_and_namespace() -> None:
    source = FOUNDATION.read_text(encoding="utf-8")
    owners = [
        module
        for module in FORMAL_MODULES
        if module.resource == "gaussian_information_geometry.lean"
    ]

    assert len(owners) == 1
    owner = owners[0]
    assert owner.lean_module == "FepSketches.gaussian_information_geometry"
    assert owner.role is FormalModuleRole.FOUNDATION
    assert owner.declaration_namespace == "FEP.GaussianInformationGeometry"
    assert tuple(re.findall(r"(?m)^import (\S+)$", source)) == EXACT_IMPORTS
    assert "namespace FEP.GaussianInformationGeometry\n" in source
    assert source.rstrip().endswith("end FEP.GaussianInformationGeometry")
    assert formal_module_imports().count(owner.lean_module) == 1


def test_h2_1a_public_surface_is_exact_and_fail_closed() -> None:
    source = FOUNDATION.read_text(encoding="utf-8")
    uncommented = lean_code_without_comments(source)

    assert re.search(r"(?m)^structure FixedVarianceGaussian where$", uncommented)
    public_theorems = tuple(re.findall(r"(?m)^theorem (\w+)\b", uncommented))
    assert public_theorems[: len(PUBLIC_THEOREMS)] == PUBLIC_THEOREMS
    assert not re.search(
        r"\b(?:sorry|admit|axiom|opaque)\b|unsafe\s+(?:def|theorem)|:\s*True\b",
        uncommented,
    )
    for forbidden in (
        "finiteKL",
        "multivariateGaussian",
        "FokkerPlanck",
        "StochasticIntegral",
    ):
        assert forbidden not in uncommented


def test_h2_1a_kl_orientation_support_and_boundary_are_theorem_visible() -> None:
    source = lean_code_without_comments(FOUNDATION.read_text(encoding="utf-8"))

    assert "(sourceMean referenceMean : ℝ)" in source
    assert (
        "InformationTheory.klDiv\n        (family.law sourceMean)\n        (family.law referenceMean)"
        in source
    )
    assert "ENNReal.ofReal\n        ((sourceMean - referenceMean) ^ 2 /" in source
    assert "(hMeans : sourceMean ≠ referenceMean)" in source
    assert "0 < InformationTheory.klDiv" in source
    assert "¬ ∃ family : FixedVarianceGaussian, family.variance = 0" in source
    assert "family.variance_pos" in source


def test_h2_1a_projection_and_manifest_are_current() -> None:
    assert PROJECTION.read_bytes() == FOUNDATION.read_bytes()
    assert formal_resource_manifest_drift(PROJECT_ROOT) == ()
    assert formal_projection_drift(PROJECT_ROOT) == ()


def test_h2_1a_foundation_compiles_warning_free() -> None:
    with tempfile.TemporaryDirectory(prefix="fep-h2-1a-") as output_dir:
        output_path = Path(output_dir) / "gaussian_information_geometry.olean"
        result = run_lean_compile_probe(
            FOUNDATION,
            cwd=LEAN_ROOT,
            import_root=PROJECT_ROOT / "src" / "fep_lean" / "formal",
            output_path=output_path,
            timeout_s=300,
            executable=lake_executable(
                missing="raise",
                context="H2.1a native acceptance",
            ),
        )
        assert output_path.is_file(), result.stdout + result.stderr

    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "warning:" not in output.lower()


def test_h2_1a_public_theorems_use_only_standard_axioms(tmp_path: Path) -> None:
    probe = tmp_path / "GaussianInformationGeometryAxioms.lean"
    source = FOUNDATION.read_text(encoding="utf-8")
    prints = "\n".join(
        f"#print axioms FEP.GaussianInformationGeometry.FixedVarianceGaussian.{name}"
        for name in PUBLIC_THEOREMS
    )
    probe.write_text(f"{source}\n{prints}\n", encoding="utf-8")
    result = run_lean_compile_probe(
        probe,
        cwd=LEAN_ROOT,
        import_root=PROJECT_ROOT / "src" / "fep_lean" / "formal",
        timeout_s=300,
        executable=lake_executable(
            missing="raise",
            context="H2.1a native acceptance",
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
