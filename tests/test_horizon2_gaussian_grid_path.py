"""H2.6c native finite-grid OU path-law contracts."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from fep_lean.formal.manifest import FORMAL_MODULES, FormalModuleRole
from fep_lean.formal.projection import formal_projection_drift
from fep_lean.lean_source import lean_code_without_comments
from tests._support.lake import lake_executable
from tests._support.lean_runner import run_lean_compile_probe

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEAN_ROOT = PROJECT_ROOT / "lean"
SOURCE = (
    PROJECT_ROOT
    / "src"
    / "fep_lean"
    / "formal"
    / "compositions"
    / "gaussian_grid_path.lean"
)
PROJECTION = LEAN_ROOT / "FepSketches" / "compositions" / "gaussian_grid_path.lean"

pytestmark = pytest.mark.serial_lean

EXACT_IMPORTS = (
    "FepSketches.scalar_gaussian_semigroup",
    "Mathlib.InformationTheory.KullbackLeibler.Basic",
    "Mathlib.MeasureTheory.Integral.Bochner.Basic",
    "Mathlib.MeasureTheory.Measure.Decomposition.RadonNikodym",
    "Mathlib.Probability.Kernel.IonescuTulcea.PartialTraj",
)
PUBLIC_DEFINITIONS = (
    "ouGridStep",
    "ouPartialTraj",
    "initialGridLaw",
    "forwardGridLaw",
    "reverseGridPath",
    "reverseAlignedGridLaw",
    "gridPathKL",
)
PUBLIC_THEOREMS = (
    "ouPartialTraj_comp",
    "forwardGridLaw_normalized",
    "reverseGridPath_measurable",
    "reverseGridPath_involutive",
    "reverseAlignedGridLaw_normalized",
    "integral_reverseAlignedGridLaw",
    "rnDeriv_forward_reverseAligned_eq_ratio",
    "gridPathKL_eq_expectedLogRatio",
    "expectedLogRatio_nonneg",
    "gridPathKL_eq_top_of_not_ac",
    "gridPathKL_eq_top_of_not_integrable",
)






def test_h2_6c_has_one_exact_composition_owner() -> None:
    assert SOURCE.is_file()
    source = SOURCE.read_text(encoding="utf-8")
    owners = [
        module
        for module in FORMAL_MODULES
        if module.resource == "compositions/gaussian_grid_path.lean"
    ]

    assert len(owners) == 1
    owner = owners[0]
    assert owner.lean_module == "FepSketches.compositions.gaussian_grid_path"
    assert owner.role is FormalModuleRole.COMPOSITION
    assert owner.declaration_namespace == "FEPComposed.GaussianGridPath"
    assert tuple(re.findall(r"(?m)^import (\S+)$", source)) == EXACT_IMPORTS


def test_h2_6c_reuses_native_ou_and_partial_trajectory_carriers() -> None:
    source = lean_code_without_comments(SOURCE.read_text(encoding="utf-8"))

    assert re.search(
        r"structure TimeGrid where\s+time : ℕ → ℝ≥0\s+monotone_time : Monotone time",
        source,
    )
    assert "abbrev GaussianGridState : ℕ → Type := fun _ => ℝ" in source
    assert "abbrev GridPath (n : ℕ) :=" in source
    assert "model.ouTransition (grid.time (n + 1) - grid.time n)" in source
    assert "Kernel.partialTraj (ouGridStep model grid)" in source
    assert "(times : ℕ → ℝ≥0)" not in source
    assert "model.stationaryLaw.map" in source
    assert "FiniteLaw" not in source
    assert "FEP.PathThermodynamics" not in source
    assert "FepSketches.path_thermodynamics" not in source


def test_h2_6c_public_surface_is_exact_and_fail_closed() -> None:
    source = lean_code_without_comments(SOURCE.read_text(encoding="utf-8"))

    assert (
        tuple(re.findall(r"(?m)^(?:noncomputable )?def (\w+)\b", source))
        == PUBLIC_DEFINITIONS
    )
    assert tuple(re.findall(r"(?m)^theorem (\w+)\b", source)) == PUBLIC_THEOREMS
    assert not re.search(
        r"\b(?:sorry|admit|axiom|opaque)\b|unsafe\s+(?:def|theorem)|:\s*True\b",
        source,
    )
    assert not re.search(
        r"\b(?:SDE|Ito|Itô|Girsanov|FokkerPlanck|ContinuousPath|ReverseOU)\b",
        source,
    )
    assert not re.search(r"0\s*≤\s*gridPathKL\b", source)


def test_h2_6c_grid_order_reversal_and_normalization_are_explicit() -> None:
    source = lean_code_without_comments(SOURCE.read_text(encoding="utf-8"))

    assert re.search(
        r"ouPartialTraj model grid b c ∘ₖ ouPartialTraj model grid a b\s*=\s*"
        r"ouPartialTraj model grid a c",
        source,
    )
    assert "Kernel.partialTraj_comp_partialTraj hab hbc" in source
    assert "forwardGridLaw model grid n Set.univ = 1" in source
    assert "Function.Involutive (reverseGridPath n)" in source
    assert "Measure.map" in source
    assert "reverseAlignedGridLaw model grid n Set.univ = 1" in source
    assert "(f : GridPath n →ᵇ ℝ)" in source


def test_h2_6c_kl_is_oriented_supported_and_nonvacuous() -> None:
    source = lean_code_without_comments(SOURCE.read_text(encoding="utf-8"))

    assert re.search(
        r"InformationTheory\.klDiv\s+\(forwardGridLaw model grid n\)\s+"
        r"\(reverseAlignedGridLaw model grid n\)",
        source,
    )
    assert re.search(
        r"\(forwardGridLaw model grid n\)\.rnDeriv\s+"
        r"\(reverseAlignedGridLaw model grid n\)\s*=ᵐ"
        r"\[reverseAlignedGridLaw model grid n\]",
        source,
    )
    assert "Measure.rnDeriv_eq_div" in source
    assert "InformationTheory.klDiv_of_ac_of_integrable" in source
    assert "InformationTheory.integral_llr_add_sub_measure_univ_nonneg" in source
    assert "InformationTheory.klDiv_of_not_ac" in source
    assert "InformationTheory.klDiv_of_not_integrable" in source
    assert "Integrable\n      (MeasureTheory.llr" in source


def test_h2_6c_projection_is_current() -> None:
    assert PROJECTION.is_file()
    assert PROJECTION.read_bytes() == SOURCE.read_bytes()
    assert formal_projection_drift(PROJECT_ROOT) == ()


def test_h2_6c_compiles_warning_free() -> None:
    result = run_lean_compile_probe(
        SOURCE,
        cwd=LEAN_ROOT,
        import_root=PROJECT_ROOT / "src" / "fep_lean" / "formal",
        timeout_s=300,
        executable=lake_executable(
            missing="raise",
            context="H2.6c native acceptance",
        ),
    )

    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "warning:" not in output.lower()


def test_h2_6c_public_theorems_use_only_standard_axioms(tmp_path: Path) -> None:
    probe = tmp_path / "GaussianGridPathAxioms.lean"
    source = SOURCE.read_text(encoding="utf-8")
    prints = "\n".join(
        f"#print axioms FEPComposed.GaussianGridPath.{name}" for name in PUBLIC_THEOREMS
    )
    probe.write_text(f"{source}\n{prints}\n", encoding="utf-8")
    result = run_lean_compile_probe(
        probe,
        cwd=LEAN_ROOT,
        import_root=PROJECT_ROOT / "src" / "fep_lean" / "formal",
        timeout_s=300,
        executable=lake_executable(
            missing="raise",
            context="H2.6c native acceptance",
        ),
    )

    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "sorryAx" not in output
    assert "warning:" not in output.lower()
    axiom_blocks = re.findall(r"depends on axioms: \[(.*?)\]", output, re.DOTALL)
    assert len(axiom_blocks) == len(PUBLIC_THEOREMS), output
    for block in axiom_blocks:
        axioms = set(re.findall(r"'([^']+)'", block))
        assert axioms <= {"propext", "Classical.choice", "Quot.sound"}
