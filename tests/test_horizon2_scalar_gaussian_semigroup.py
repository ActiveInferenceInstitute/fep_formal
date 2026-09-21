"""H2.5a scalar Gaussian Ornstein--Uhlenbeck semigroup contracts."""

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
    PROJECT_ROOT / "src" / "fep_lean" / "formal" / "scalar_gaussian_semigroup.lean"
)
PROJECTION = LEAN_ROOT / "FepSketches" / "scalar_gaussian_semigroup.lean"

pytestmark = pytest.mark.serial_lean

EXACT_IMPORTS = (
    "FepSketches.gaussian_information_geometry",
    "FepSketches.markov_semigroup",
    "Mathlib.Analysis.SpecialFunctions.Exp",
    "Mathlib.MeasureTheory.Measure.LevyConvergence",
    "Mathlib.MeasureTheory.Measure.ProbabilityMeasure",
    "Mathlib.Order.Filter.AtTopBot.CountablyGenerated",
    "Mathlib.Probability.Distributions.Gaussian.Real",
    "Mathlib.Probability.Kernel.Composition.Comp",
    "Mathlib.Topology.Instances.NNReal.Lemmas",
)
PUBLIC_DEFINITIONS = (
    "decay",
    "stationaryVariance",
    "transitionMean",
    "transitionVariance",
    "positiveTimeGaussian",
    "ouTransition",
    "ouNativeSemigroup",
    "stationaryGaussian",
    "stationaryLaw",
    "ouTransitionProbability",
    "stationaryProbability",
)
PUBLIC_THEOREMS = (
    "stationaryVariance_eq",
    "transitionMean_zero",
    "transitionVariance_zero",
    "transitionVariance_pos",
    "ouTransition_univ",
    "ouTransition_zero",
    "ouTransition_add",
    "ouTransition_comp_gaussian",
    "ouTransition_eq_gaussianLocation",
    "stationaryLaw_invariant",
    "ouTransition_mean",
    "ouTransition_variance",
    "ouTransitionProbability_tendsto_invariant",
    "integral_ouTransition_tendsto_invariant",
    "ouKL_to_stationary_nonincrease",
)


def test_h2_5a_has_one_exact_foundation_owner() -> None:
    assert FOUNDATION.is_file()
    source = FOUNDATION.read_text(encoding="utf-8")
    owners = [module for module in FORMAL_MODULES if module.resource == FOUNDATION.name]

    assert len(owners) == 1
    owner = owners[0]
    assert owner.lean_module == "FepSketches.scalar_gaussian_semigroup"
    assert owner.role is FormalModuleRole.FOUNDATION
    assert owner.declaration_namespace == "FEP.ScalarGaussianSemigroup"
    assert tuple(re.findall(r"(?m)^import (\S+)$", source)) == EXACT_IMPORTS
    assert "namespace FEP.ScalarGaussianSemigroup\n" in source
    assert source.rstrip().endswith("end FEP.ScalarGaussianSemigroup")


def test_h2_5a_stores_only_raw_positive_parameters() -> None:
    source = lean_code_without_comments(FOUNDATION.read_text(encoding="utf-8"))
    carrier = re.search(
        r"structure ScalarOUParameters where\n(?P<body>.*?)(?=\n\n)",
        source,
        re.DOTALL,
    )
    assert carrier is not None
    assert tuple(re.findall(r"(?m)^  (\w+)\s*:", carrier["body"])) == (
        "rate",
        "rate_pos",
        "center",
        "diffusionVarianceRate",
        "diffusionVarianceRate_pos",
    )
    assert "stationaryVariance" not in carrier["body"]
    assert "invariant" not in carrier["body"].lower()
    assert "semigroup" not in carrier["body"].lower()


def test_h2_5a_public_surface_is_exact_and_fail_closed() -> None:
    source = lean_code_without_comments(FOUNDATION.read_text(encoding="utf-8"))

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
        r"\b(?:SDE|Ito|Itô|FokkerPlanck|Fokker--Planck|generator|Generator)\b",
        source,
    )


def test_h2_5a_zero_positive_and_h2_1_branches_are_explicit() -> None:
    source = lean_code_without_comments(FOUNDATION.read_text(encoding="utf-8"))

    assert (
        "(model.stationaryVariance : ℝ) =\n"
        "      (model.diffusionVarianceRate : ℝ) / (2 * model.rate)"
    ) in source
    assert "model.transitionVariance 0 = 0" in source
    assert "(hTime : 0 < time)" in source
    assert "0 < model.transitionVariance time" in source
    assert "model.ouTransition 0 = Kernel.id" in source
    assert "gaussianReal_zero_var" in source
    assert "FEP.GaussianInformationGeometry.FixedVarianceGaussian" in source
    assert "model.positiveTimeGaussian time hTime" in source
    assert "model.ouTransition time state =" in source


def test_h2_5a_chapman_kolmogorov_is_chronological_and_consumes_h2_4() -> None:
    source = lean_code_without_comments(FOUNDATION.read_text(encoding="utf-8"))

    assert "model.ouTransition (left + right) =" in source
    assert "model.ouTransition right ∘ₖ model.ouTransition left" in source
    assert ".bind" in source
    assert "Measure.lintegral_conv" in source
    assert "gaussianReal_map_const_mul" in source
    assert "gaussianReal_map_add_const" in source
    assert "gaussianReal_conv_gaussianReal" in source
    assert "FEP.MarkovSemigroup.NativeKernelSemigroup" in source
    assert "kernel_add := model.ouTransition_add" in source
    assert "model.ouTransition time ∘ₘ gaussianReal sourceMean sourceVariance" in source
    assert "gaussian_bind_affine" in source


def test_h2_5a_invariance_moments_weak_limit_and_kl_are_explicit() -> None:
    source = lean_code_without_comments(FOUNDATION.read_text(encoding="utf-8"))

    assert "FEP.MarkovSemigroup.InvariantLaw" in source
    assert "integral_id_gaussianReal" in source
    assert "variance_id_gaussianReal" in source
    assert "Filter.tendsto_of_seq_tendsto" in source
    assert "ProbabilityMeasure.tendsto_iff_tendsto_charFun" in source
    assert "charFun_gaussianReal" in source
    assert "ProbabilityMeasure.tendsto_iff_forall_integral_tendsto" in source
    assert "(f : ℝ →ᵇ ℝ)" in source
    assert "nativeKL_to_invariant_nonincrease" in source
    assert "kernel (earlier + increment)" not in source


def test_h2_5a_projection_is_current() -> None:
    assert PROJECTION.read_bytes() == FOUNDATION.read_bytes()
    assert formal_projection_drift(PROJECT_ROOT) == ()


def test_h2_5a_compiles_warning_free() -> None:
    with tempfile.TemporaryDirectory(prefix="fep-h2-5a-") as output_dir:
        output_path = Path(output_dir) / "scalar_gaussian_semigroup.olean"
        result = run_lean_compile_probe(
            FOUNDATION,
            cwd=LEAN_ROOT,
            import_root=PROJECT_ROOT / "src" / "fep_lean" / "formal",
            output_path=output_path,
            timeout_s=300,
            executable=lake_executable(
                missing="raise",
                context="H2.5a native acceptance",
            ),
        )
        assert output_path.is_file(), result.stdout + result.stderr

    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "warning:" not in output.lower()


def test_h2_5a_public_theorems_use_only_standard_axioms(tmp_path: Path) -> None:
    probe = tmp_path / "ScalarGaussianSemigroupAxioms.lean"
    source = FOUNDATION.read_text(encoding="utf-8")
    prints = "\n".join(
        f"#print axioms FEP.ScalarGaussianSemigroup.ScalarOUParameters.{name}"
        for name in PUBLIC_THEOREMS
    )
    chronological_consumer = """
open MeasureTheory ProbabilityTheory
open scoped ProbabilityTheory

example
    (model : FEP.ScalarGaussianSemigroup.ScalarOUParameters)
    (left right : ℝ≥0) :
    model.ouTransition (left + right) =
      model.ouTransition right ∘ₖ model.ouTransition left :=
  (model.ouNativeSemigroup).kernel_add left right
"""
    probe.write_text(
        f"{source}\n{prints}\n{chronological_consumer}\n", encoding="utf-8"
    )
    result = run_lean_compile_probe(
        probe,
        cwd=LEAN_ROOT,
        import_root=PROJECT_ROOT / "src" / "fep_lean" / "formal",
        timeout_s=300,
        executable=lake_executable(
            missing="raise",
            context="H2.5a native acceptance",
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
