"""H2.6a exact scalar Gaussian filter source contracts."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from fep_lean.formal import formal_projection_pairs, render_formal_aggregate
from fep_lean.formal.manifest import FORMAL_MODULES, FormalModuleRole
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
    / "gaussian_filter.lean"
)

EXACT_IMPORTS = (
    "FepSketches.gaussian_information_geometry",
    "FepSketches.scalar_gaussian_semigroup",
    "Mathlib.Probability.Distributions.Gaussian.Real",
    "Mathlib.Probability.Kernel.Posterior",
)

PUBLIC_DEFINITIONS = (
    "law",
    "predictionVariance",
    "predictionBelief",
    "observationKernel",
    "innovationVariance",
    "gain",
    "posteriorMean",
    "posteriorVariance",
    "posteriorFamily",
    "posteriorBelief",
    "closedFormPosteriorKernel",
    "evidenceFamily",
    "evidenceLaw",
    "evidenceDensity",
    "filterRecursion",
)

PUBLIC_THEOREMS = (
    "predictionVariance_pos",
    "predictionBelief_law_eq_ouTransition",
    "observationKernel_apply",
    "innovationVariance_pos",
    "posteriorVariance_pos",
    "gaussianPDF_factorization",
    "gaussianEvidence_compProd_closedForm_eq_map_swap",
    "evidenceLaw_eq_gaussian",
    "closedFormPosterior_compProd_eq_map_swap",
    "closedFormPosterior_ae_eq_native",
    "evidenceDensity_pos",
    "evidenceDensity_ne_zero",
    "evidenceLaw_singleton_eq_zero",
    "closedFormPosterior_univ",
    "filterRecursion_nil",
    "filterRecursion_cons",
)

pytestmark = pytest.mark.serial_lean






def test_h2_6a_has_one_exact_maintained_source_owner() -> None:
    assert SOURCE.is_file()
    source = SOURCE.read_text(encoding="utf-8")
    uncommented = lean_code_without_comments(source)

    assert tuple(re.findall(r"(?m)^import (\S+)$", source)) == EXACT_IMPORTS
    assert "namespace FEPComposed.GaussianFilter\n" in source
    assert source.rstrip().endswith("end FEPComposed.GaussianFilter")
    assert "namespace FEPProbe" not in uncommented


def test_h2_6a_is_manifested_projected_and_aggregated_once() -> None:
    modules = tuple(
        module
        for module in FORMAL_MODULES
        if module.resource == "compositions/gaussian_filter.lean"
    )

    assert len(modules) == 1
    assert modules[0].lean_module == "FepSketches.compositions.gaussian_filter"
    assert modules[0].role is FormalModuleRole.COMPOSITION
    assert modules[0].declaration_namespace == "FEPComposed.GaussianFilter"

    projection_pairs = dict(formal_projection_pairs(PROJECT_ROOT))
    projection = PROJECT_ROOT / "lean" / "FepSketches" / modules[0].resource
    assert projection_pairs[SOURCE] == projection
    assert projection.read_bytes() == SOURCE.read_bytes()

    aggregate = render_formal_aggregate()
    assert aggregate.count("import FepSketches.compositions.gaussian_filter\n") == 1


def test_h2_6a_reuses_exact_scalar_owners_and_stores_only_raw_inputs() -> None:
    source = lean_code_without_comments(SOURCE.read_text(encoding="utf-8"))
    belief = re.search(
        r"structure ScalarGaussianBelief where\n(?P<body>.*?)(?=\n\n)",
        source,
        re.DOTALL,
    )
    model = re.search(
        r"structure ScalarGaussianFilterModel where\n(?P<body>.*?)(?=\n\n)",
        source,
        re.DOTALL,
    )

    assert tuple(re.findall(r"(?m)^structure (\w+) where$", source)) == (
        "ScalarGaussianBelief",
        "ScalarGaussianFilterModel",
    )
    assert belief is not None
    assert tuple(re.findall(r"(?m)^  (\w+)\s*:", belief["body"])) == (
        "mean",
        "family",
    )
    assert "family : FixedVarianceGaussian" in belief["body"]
    assert model is not None
    assert tuple(re.findall(r"(?m)^  (\w+)\s*:", model["body"])) == (
        "dynamics",
        "stepDuration",
        "observationNoise",
    )
    assert "dynamics : ScalarOUParameters" in model["body"]
    assert "stepDuration : ℝ≥0" in model["body"]
    assert "observationNoise : FixedVarianceGaussian" in model["body"]
    assert "structure ScalarOUParameters" not in source
    assert "structure FixedVarianceGaussian" not in source
    assert not re.search(
        r"(?m)^(?:private )?(?:noncomputable )?def "
        r"(?:ouTransition|transitionKernel|gaussianLocation|observationLaw)\b",
        source,
    )


def test_h2_6a_public_surface_is_exact_and_fail_closed() -> None:
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
        r"\b(?:KalmanBucy|Kalman--Bucy|nonlinearFilter|SDE|Ito|Itô|"
        r"parameterConsistency|Multivariate)\b",
        source,
    )
    assert not re.search(
        r"model\.observationNoise\.variance\s*=\s*0|"
        r"if\s+innovationVariance\b.*=\s*0",
        source,
        re.DOTALL,
    )


def test_h2_6a_prediction_observation_and_closed_parameters_are_exact() -> None:
    source = lean_code_without_comments(SOURCE.read_text(encoding="utf-8"))

    assert "NNReal.mk (model.dynamics.decay model.stepDuration ^ 2)" in source
    assert "model.dynamics.transitionVariance model.stepDuration" in source
    assert "model.dynamics.ouTransition model.stepDuration ∘ₘ prior.law" in source
    assert "ouTransition_comp_gaussian" in source
    assert "toFun state := model.observationNoise.law state" in source
    assert "observationKernel model state = model.observationNoise.law state" in source
    assert "predicted.family.variance + model.observationNoise.variance" in source
    assert "(predicted.family.variance : ℝ) /" in source
    assert (
        "predicted.mean + gain model prior * (observation - predicted.mean)" in source
    )
    assert (
        "predicted.family.variance * model.observationNoise.variance /\n"
        "    innovationVariance model prior"
    ) in source
    assert "0 < innovationVariance model prior" in source
    assert "0 < posteriorVariance model prior" in source


def test_h2_6a_closed_form_is_connected_to_the_native_posterior() -> None:
    source = lean_code_without_comments(SOURCE.read_text(encoding="utf-8"))

    assert re.search(
        r"gaussianPDF predicted\.mean predicted\.family\.variance state \*\s*"
        r"gaussianPDF state model\.observationNoise\.variance observation =\s*"
        r"evidenceDensity model prior observation \*",
        source,
    )
    assert re.search(
        r"\(evidenceFamily model prior\)\.law predicted\.mean ⊗ₘ\s*"
        r"closedFormPosteriorKernel model prior =\s*"
        r"\(\(predictionBelief model prior\)\.law ⊗ₘ observationKernel model\)\.map\s*"
        r"Prod\.swap",
        source,
    )
    assert re.search(
        r"evidenceLaw model prior ⊗ₘ closedFormPosteriorKernel model prior =\s*"
        r"\(\(predictionBelief model prior\)\.law ⊗ₘ observationKernel model\)\.map\s*"
        r"Prod\.swap",
        source,
    )
    assert "congrArg Measure.fst" in source
    assert "ProbabilityTheory.ae_eq_posterior_of_compProd_eq" in source
    assert re.search(
        r"closedFormPosteriorKernel model prior\s*=ᵐ\[evidenceLaw model prior\]\s*"
        r"ProbabilityTheory\.posterior",
        source,
    )
    assert not re.search(
        r"closedFormPosteriorKernel model prior\s*=\s*"
        r"ProbabilityTheory\.posterior",
        source,
    )
    assert "0 < evidenceDensity model prior observation" in source
    assert "evidenceDensity model prior observation ≠ 0" in source
    assert "evidenceLaw model prior {observation} = 0" in source
    assert "closedFormPosteriorKernel model prior observation Set.univ = 1" in source


def test_h2_6a_finite_recursion_reuses_the_proved_one_step_update() -> None:
    source = lean_code_without_comments(SOURCE.read_text(encoding="utf-8"))
    model = re.search(
        r"structure ScalarGaussianFilterModel where\n(?P<body>.*?)(?=\n\n)",
        source,
        re.DOTALL,
    )

    assert re.search(
        r"def filterRecursion\s*"
        r"\(model : ScalarGaussianFilterModel\)\s*:\s*"
        r"ScalarGaussianBelief → List ℝ → ScalarGaussianBelief\s*"
        r"\| prior, \[\] => prior\s*"
        r"\| prior, observation :: observations =>\s*"
        r"filterRecursion model\s*"
        r"\(posteriorBelief model prior observation\) observations",
        source,
    )
    assert "filterRecursion model prior [] = prior" in source
    assert re.search(
        r"filterRecursion model prior \(observation :: observations\) =\s*"
        r"filterRecursion model\s*"
        r"\(posteriorBelief model prior observation\) observations",
        source,
    )
    assert model is not None
    assert "filterRecursion" not in model["body"]


def test_h2_6a_compiles_warning_free(tmp_path: Path) -> None:
    output_path = tmp_path / "gaussian_filter.olean"
    lake = lake_executable(missing="raise", context="H2.6a native acceptance")
    result = run_lean_compile_probe(
        SOURCE,
        cwd=LEAN_ROOT,
        import_root=PROJECT_ROOT / "src" / "fep_lean" / "formal",
        output_path=output_path,
        timeout_s=300,
        executable=lake,
    )

    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert output_path.is_file(), output
    assert "warning:" not in output.lower()


def test_h2_6a_public_theorems_use_only_standard_axioms(tmp_path: Path) -> None:
    probe = tmp_path / "GaussianFilterAxioms.lean"
    source = SOURCE.read_text(encoding="utf-8")
    prints = "\n".join(
        f"#print axioms FEPComposed.GaussianFilter.{name}" for name in PUBLIC_THEOREMS
    )
    probe.write_text(f"{source}\n{prints}\n", encoding="utf-8")
    lake = lake_executable(missing="raise", context="H2.6a native acceptance")
    result = run_lean_compile_probe(
        probe,
        cwd=LEAN_ROOT,
        import_root=PROJECT_ROOT / "src" / "fep_lean" / "formal",
        timeout_s=300,
        executable=lake,
    )

    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "sorryAx" not in output
    assert "warning:" not in output.lower()
    for name in PUBLIC_THEOREMS:
        qualified = f"FEPComposed.GaussianFilter.{name}"
        match = re.search(
            rf"'{re.escape(qualified)}' depends on axioms: \[(.*?)\]",
            output,
            re.DOTALL,
        )
        if match is None:
            assert f"'{qualified}' does not depend on any axioms" in output
            continue
        axioms = {
            name.strip().strip("'")
            for name in match[1].replace("\n", " ").split(",")
            if name.strip()
        }
        assert axioms
        assert axioms <= {"propext", "Classical.choice", "Quot.sound"}
