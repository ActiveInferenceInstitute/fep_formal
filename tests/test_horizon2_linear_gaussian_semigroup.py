"""H2.5b symmetric-precision linear Gaussian semigroup contracts."""

from __future__ import annotations

import re
import tempfile
from pathlib import Path

import pytest

from fep_lean.formal import formal_projection_pairs
from fep_lean.formal.manifest import FORMAL_MODULES, FormalModuleRole
from fep_lean.lean_source import lean_code_without_comments
from tests._support.lake import lake_executable
from tests._support.lean_runner import run_lean_compile_probe

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEAN_ROOT = PROJECT_ROOT / "lean"
FOUNDATION = (
    PROJECT_ROOT / "src" / "fep_lean" / "formal" / "linear_gaussian_semigroup.lean"
)

pytestmark = pytest.mark.serial_lean

EXACT_IMPORTS = (
    "FepSketches.markov_semigroup",
    "FepSketches.scalar_gaussian_semigroup",
    "Mathlib.Analysis.Matrix.PosDef",
    "Mathlib.Analysis.Normed.Algebra.MatrixExponential",
    "Mathlib.Analysis.SpecialFunctions.Exponential",
    "Mathlib.MeasureTheory.Measure.LevyConvergence",
    "Mathlib.MeasureTheory.Measure.ProbabilityMeasure",
    "Mathlib.Order.Filter.AtTopBot.CountablyGenerated",
    "Mathlib.Probability.Distributions.Gaussian.Multivariate",
    "Mathlib.Probability.Kernel.Composition.Comp",
    "Mathlib.Probability.Kernel.Composition.CompProd",
    "Mathlib.Probability.Kernel.Composition.MapComap",
    "Mathlib.Tactic.NoncommRing",
    "Mathlib.Topology.Instances.NNReal.Lemmas",
)
PUBLIC_DEFINITIONS = (
    "covariance",
    "evolution",
    "transitionMean",
    "transitionCovariance",
    "transition",
    "nativeSemigroup",
    "stationaryLaw",
    "transitionProbability",
    "stationaryProbability",
    "finOneState",
    "finOneParameters",
    "finOneScalarParameters",
    "finOneTransition",
)
PUBLIC_THEOREMS = (
    "precision_mul_covariance",
    "covariance_mul_precision",
    "covariance_posDef",
    "evolution_zero",
    "evolution_add",
    "evolution_transpose",
    "transitionMean_zero",
    "transitionMean_add",
    "transitionCovariance_zero",
    "transitionCovariance_posSemidef",
    "transitionCovariance_posDef",
    "transitionCovariance_add",
    "transition_apply",
    "transition_univ",
    "transition_zero",
    "transition_comp_multivariateGaussian",
    "transition_add",
    "stationaryLaw_invariant",
    "transition_mean",
    "transition_covariance",
    "transitionProbability_tendsto_invariant",
    "integral_transition_tendsto_invariant",
    "finOne_transitionMean",
    "finOne_transitionCovariance",
    "finOneTransition_eq_scalarOU",
)
ALLOWED_AXIOMS = frozenset({"propext", "Classical.choice", "Quot.sound"})


def _parse_axiom_names(block: str) -> set[str]:
    return {
        token.strip().strip("'")
        for token in block.split(",")
        if token.strip().strip("'")
    }


def test_axiom_parser_accepts_lean_4_33_unquoted_names() -> None:
    assert _parse_axiom_names("propext, Classical.choice, Quot.sound") == {
        "propext",
        "Classical.choice",
        "Quot.sound",
    }
    assert _parse_axiom_names("'propext', 'Classical.choice'") == {
        "propext",
        "Classical.choice",
    }






def test_h2_5b_has_exact_owner_imports_and_generic_axis() -> None:
    assert FOUNDATION.is_file()
    source = FOUNDATION.read_text(encoding="utf-8")

    assert tuple(re.findall(r"(?m)^import (\S+)$", source)) == EXACT_IMPORTS
    assert "namespace FEP.LinearGaussianSemigroup\n" in source
    assert source.rstrip().endswith("end FEP.LinearGaussianSemigroup")
    assert "{Axis : Type*} [Fintype Axis] [DecidableEq Axis]" in source
    assert "abbrev State (Axis : Type*) := EuclideanSpace ℝ Axis" in source


def test_h2_5b_is_manifested_and_projected_as_one_foundation() -> None:
    modules = tuple(
        module
        for module in FORMAL_MODULES
        if module.resource == "linear_gaussian_semigroup.lean"
    )

    assert len(modules) == 1
    assert modules[0].lean_module == "FepSketches.linear_gaussian_semigroup"
    assert modules[0].role is FormalModuleRole.FOUNDATION
    assert modules[0].declaration_namespace == "FEP.LinearGaussianSemigroup"

    projection_pairs = dict(formal_projection_pairs(PROJECT_ROOT))
    projection = PROJECT_ROOT / "lean" / "FepSketches" / modules[0].resource
    assert projection_pairs[FOUNDATION] == projection
    assert projection.read_bytes() == FOUNDATION.read_bytes()


def test_h2_5b_stores_only_raw_precision_and_center() -> None:
    source = lean_code_without_comments(FOUNDATION.read_text(encoding="utf-8"))
    carrier = re.search(
        r"structure LinearGaussianParameters \(Axis : Type\*\) where\n"
        r"(?P<body>.*?)(?=\n\n)",
        source,
        re.DOTALL,
    )
    assert carrier is not None
    assert tuple(re.findall(r"(?m)^  (\w+)\s*:", carrier["body"])) == (
        "precision",
        "precision_posDef",
        "center",
    )
    assert not re.search(
        r"covariance|semigroup|invariant|markov|measur|posSemidef|transition",
        carrier["body"],
        re.IGNORECASE,
    )


def test_h2_5b_public_surface_is_exact_and_fail_closed() -> None:
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
        r"\b(?:SDE|Ito|Itô|FokkerPlanck|Brownian|Hurwitz|Lyapunov|"
        r"generator|Generator)\b",
        source,
    )
    assert not re.search(
        r"\b(?:Fin4Axis|eigenmodeTwo|eigenmodeFour|eigenmodeSix)\b", source
    )


def test_h2_5b_derives_inverse_and_dynamic_covariance() -> None:
    source = lean_code_without_comments(FOUNDATION.read_text(encoding="utf-8"))

    assert "model.precision⁻¹" in source
    assert "model.precision * model.covariance = 1" in source
    assert "model.covariance * model.precision = 1" in source
    assert "model.covariance.PosDef" in source
    assert "NormedSpace.exp ((-(time : ℝ)) • model.precision)" in source
    assert "model.covariance -" in source
    assert "model.evolution time * model.covariance * (model.evolution time)ᵀ" in source
    assert "(model.transitionCovariance time).PosSemidef" in source
    assert "(model.transitionCovariance time).PosDef" in source
    assert "(hTime : 0 < time)" in source
    assert "model.transitionCovariance (left + right) =" in source
    assert "model.evolution right * model.transitionCovariance left" in source
    assert "model.transitionCovariance right" in source
    assert "Commute" in source


def test_h2_5b_owns_a_measurable_markov_kernel_and_chronological_semigroup() -> None:
    source = lean_code_without_comments(FOUNDATION.read_text(encoding="utf-8"))
    transition = re.search(
        r"noncomputable def transition\b(?P<body>.*?)(?=\n\n)",
        source,
        re.DOTALL,
    )
    assert transition is not None

    assert ": Kernel (State Axis) (State Axis)" in transition["body"]
    assert "Kernel.compProd" in transition["body"]
    assert "Kernel.const" in transition["body"]
    assert "Kernel.map" in transition["body"]
    assert (
        "multivariateGaussian 0 (model.transitionCovariance time)" in transition["body"]
    )
    assert "transition_isMarkovKernel" in source
    assert "model.transition time state =" in source
    assert "multivariateGaussian" in source
    assert "model.transition 0 = Kernel.id" in source
    assert "model.transition (left + right) =" in source
    assert "model.transition right ∘ₖ model.transition left" in source
    assert "FEP.MarkovSemigroup.NativeKernelSemigroup" in source
    assert "kernel_add := model.transition_add" in source


def test_h2_5b_invariance_moments_and_full_time_weak_limit_are_explicit() -> None:
    source = lean_code_without_comments(FOUNDATION.read_text(encoding="utf-8"))

    assert "FEP.MarkovSemigroup.InvariantLaw" in source
    assert "integral_id_multivariateGaussian" in source
    assert "covariance_eval_multivariateGaussian" in source
    assert "Filter.tendsto_of_seq_tendsto" in source
    assert "ProbabilityMeasure.tendsto_iff_tendsto_charFun" in source
    assert "charFun_multivariateGaussian" in source
    assert "ProbabilityMeasure.tendsto_iff_forall_integral_tendsto" in source
    assert "(f : State Axis →ᵇ ℝ)" in source


def test_h2_5b_fin_one_specialization_names_exact_h2_5a_parameters() -> None:
    source = lean_code_without_comments(FOUNDATION.read_text(encoding="utf-8"))

    assert "LinearGaussianParameters (Fin 1)" in source
    assert "diffusionVarianceRate := 2" in source
    assert "FEP.ScalarGaussianSemigroup.ScalarOUParameters" in source
    assert "(finOneParameters rate hRate center).finOneTransition time =" in source
    assert "Kernel.comap" in source
    assert "Kernel.map" in source
    assert "(finOneParameters rate hRate center).finOneTransition time" in source
    assert "(finOneScalarParameters rate hRate center).ouTransition time" in source


def test_h2_5b_compiles_warning_free() -> None:
    with tempfile.TemporaryDirectory(prefix="fep-h2-5b-") as output_dir:
        output_path = Path(output_dir) / "linear_gaussian_semigroup.olean"
        result = run_lean_compile_probe(
            FOUNDATION,
            cwd=LEAN_ROOT,
            import_root=PROJECT_ROOT / "src" / "fep_lean" / "formal",
            output_path=output_path,
            timeout_s=300,
            executable=lake_executable(
                missing="raise",
                context="H2.5b native acceptance",
            ),
        )
        assert output_path.is_file(), result.stdout + result.stderr

    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "warning:" not in output.lower()


def test_h2_5b_public_theorems_use_only_standard_axioms(tmp_path: Path) -> None:
    probe = tmp_path / "LinearGaussianSemigroupAxioms.lean"
    source = FOUNDATION.read_text(encoding="utf-8")
    prints = "\n".join(
        f"#print axioms FEP.LinearGaussianSemigroup.LinearGaussianParameters.{name}"
        for name in PUBLIC_THEOREMS
    )
    chronological_and_scalar_consumers = """
open MeasureTheory ProbabilityTheory
open scoped ProbabilityTheory

example {Axis : Type*} [Fintype Axis] [DecidableEq Axis]
    (model : FEP.LinearGaussianSemigroup.LinearGaussianParameters Axis)
    (left right : ℝ≥0) :
    model.transition (left + right) =
      model.transition right ∘ₖ model.transition left :=
  model.nativeSemigroup.kernel_add left right

example (rate center : ℝ) (hRate : 0 < rate) (time : ℝ≥0) :
    (FEP.LinearGaussianSemigroup.LinearGaussianParameters.finOneParameters
      rate hRate center).finOneTransition time =
      (FEP.LinearGaussianSemigroup.LinearGaussianParameters.finOneScalarParameters
        rate hRate center).ouTransition time :=
  FEP.LinearGaussianSemigroup.LinearGaussianParameters.finOneTransition_eq_scalarOU
    rate hRate center time
"""
    probe.write_text(
        f"{source}\n{prints}\n{chronological_and_scalar_consumers}\n",
        encoding="utf-8",
    )
    result = run_lean_compile_probe(
        probe,
        cwd=LEAN_ROOT,
        import_root=PROJECT_ROOT / "src" / "fep_lean" / "formal",
        timeout_s=300,
        executable=lake_executable(
            missing="raise",
            context="H2.5b native acceptance",
        ),
    )

    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "sorryAx" not in output
    assert "warning:" not in output.lower()
    axiom_blocks = re.findall(r"depends on axioms: \[(.*?)\]", output, re.DOTALL)
    assert len(axiom_blocks) == len(PUBLIC_THEOREMS), output
    for block in axiom_blocks:
        axioms = _parse_axiom_names(block)
        assert axioms, f"vacuous axiom block: {block!r}\n{output}"
        assert axioms <= ALLOWED_AXIOMS, axioms
