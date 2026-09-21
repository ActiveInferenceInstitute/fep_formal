"""H2.5d maintained Gaussian precision-conditioning contracts."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

import pytest

from fep_lean.formal import formal_projection_pairs, render_formal_aggregate
from fep_lean.formal.manifest import FORMAL_MODULES, FormalModuleRole
from fep_lean.lean_source import lean_code_without_comments
from tests._support.lake import lake_executable
from tests._support.lean_runner import run_lean_compile_probe, run_lean_probe

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEAN_ROOT = PROJECT_ROOT / "lean"
SOURCE = (
    PROJECT_ROOT
    / "src"
    / "fep_lean"
    / "formal"
    / "gaussian_precision_conditioning.lean"
)
PROJECTION = PROJECT_ROOT / "lean" / "FepSketches" / SOURCE.name
H2_5C_SOURCE = (
    PROJECT_ROOT / "src" / "fep_lean" / "formal" / "fin4_gaussian_semigroup.lean"
)
R0_SPIKE = (
    PROJECT_ROOT
    / "specs"
    / "horizon-2-smooth-stochastic"
    / "spikes"
    / "05d_gaussian_conditioning.lean"
)
R0_TEST = PROJECT_ROOT / "tests" / "test_horizon2_gaussian_conditioning_readiness.py"
R0_REPAIR = (
    PROJECT_ROOT
    / "specs"
    / "horizon-2-smooth-stochastic"
    / "readiness"
    / "repairs"
    / "05d-gaussian-conditioning.json"
)
R0_LIFECYCLE = R0_REPAIR.with_name("05d-gaussian-conditioning-lifecycle.json")
READINESS_VALIDATOR = (
    PROJECT_ROOT / "specs" / "horizon-2-smooth-stochastic" / "readiness" / "validate.py"
)

EXACT_IMPORTS = (
    "FepSketches.fin4_gaussian_semigroup",
    "Mathlib.LinearAlgebra.Matrix.Notation",
    "Mathlib.Probability.Distributions.Gaussian.HasGaussianLaw.Independence",
    "Mathlib.Probability.Independence.Conditional",
)
PUBLIC_ABBREVIATIONS = ("Blanket", "Endpoints", "PerturbedEndpoints")
PUBLIC_DEFINITIONS = (
    "blanketCoordinates",
    "endpointCoordinates",
    "partitionCoordinates",
    "blanketLaw",
    "conditionalOffset",
    "externalConditionalMean",
    "internalConditionalMean",
    "externalConditionalKernel",
    "internalConditionalKernel",
    "endpointConditionalKernel",
    "perturbedExternal",
    "perturbedInternal",
    "perturbedEndpointPrecision",
    "perturbedEndpointCovariance",
    "perturbedEndpointLaw",
)
PUBLIC_INSTANCES = (
    "blanketLaw_isProbabilityMeasure",
    "externalConditionalKernel_isMarkovKernel",
    "internalConditionalKernel_isMarkovKernel",
    "endpointConditionalKernel_isMarkovKernel",
    "perturbedEndpointLaw_isProbabilityMeasure",
)
PUBLIC_THEOREMS = (
    "measurable_blanketCoordinates",
    "measurable_endpointCoordinates",
    "measurable_partitionCoordinates",
    "externalConditionalKernel_apply",
    "internalConditionalKernel_apply",
    "endpointConditionalKernel_apply",
    "externalConditionalKernel_mean",
    "externalConditionalKernel_variance",
    "internalConditionalKernel_mean",
    "internalConditionalKernel_variance",
    "stationaryPartition_eq_compProd",
    "endpointCondDistrib_ae_eq_product",
    "externalCondDistrib_ae_eq",
    "internalCondDistrib_ae_eq",
    "external_condIndep_internal_given_blanket",
    "stationary_external_internal_covariance",
    "stationary_external_internal_covariance_ne_zero",
    "precisionZero_covarianceNonzero_condIndep",
    "perturbedEndpointPrecision_posDef",
    "perturbedEndpointCovariance_eq_entries",
    "perturbedEndpointCovariance_posDef",
    "perturbedEndpointPrecision_external_internal",
    "perturbedEndpointCovariance_external_internal",
    "perturbedEndpoint_external_internal_covariance",
    "perturbedEndpoint_external_not_indep_internal",
)
PUBLIC_ENVIRONMENT_DECLARATIONS = frozenset(
    (
        *PUBLIC_ABBREVIATIONS,
        *PUBLIC_DEFINITIONS,
        *PUBLIC_INSTANCES,
        *PUBLIC_THEOREMS,
    )
)
ALLOWED_AXIOMS = frozenset({"propext", "Classical.choice", "Quot.sound"})
R0_REPAIR_SHA256 = "a7092b45672616fbb88144683ab99c0d29d29819459825c8f1740b4360573d5f"
R0_LIFECYCLE_SHA256 = "64e5abcfe7cbcaf5f5164378e65a230e8dd13904c3f1462aa4b73678338270d6"
ORIGINAL_R0_TEST_SHA256 = (
    "0e7606ed93161751c945f459cd33aeed90a4829c4f886ba04461a909e9b8326f"
)
PRESERVED_HASHES = {
    H2_5C_SOURCE: "d8d15d0abdfe6eb53c9e1b94d6f1e90a076e97c9507a3532021aea090deb630b",
    R0_SPIKE: "551bcf412f037f0a1f4a5ca180b244074c3df910a6c502d8eaef8eed402a6df8",
    R0_TEST: "16562762a0c0a8fc06bde2858b26a5b0526164fcfe91c3d56ae39b4fe7b42ade",
}

pytestmark = pytest.mark.serial_lean




def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()




def _parse_axiom_names(block: str) -> set[str]:
    return {
        token.strip().strip("'")
        for token in block.split(",")
        if token.strip().strip("'")
    }


def _parse_namespace_declaration_names(output: str, namespace: str) -> frozenset[str]:
    qualified_prefix = re.escape(f"{namespace}.")
    return frozenset(
        re.findall(
            rf"(?m)^{qualified_prefix}"
            r"([A-Za-z_][A-Za-z0-9_']*(?:\.[A-Za-z_][A-Za-z0-9_']*)*)",
            output,
        )
    )


def _assert_exact_namespace_declarations(
    output: str, namespace: str, expected: frozenset[str]
) -> None:
    actual = _parse_namespace_declaration_names(output, namespace)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    assert not missing and not extra, f"missing={missing}; extra={extra}"


def _run_lean(path: Path, *, timeout: int = 300) -> subprocess.CompletedProcess[str]:
    return run_lean_probe(
        path,
        import_root=PROJECT_ROOT / "src" / "fep_lean" / "formal",
        cwd=LEAN_ROOT,
        timeout_s=timeout,
    )


def test_h2_5d_owner_imports_namespace_and_h2_5c_reuse_are_exact() -> None:
    assert SOURCE.is_file()
    raw_source = SOURCE.read_text(encoding="utf-8")
    source = lean_code_without_comments(raw_source)

    assert tuple(re.findall(r"(?m)^import (\S+)$", raw_source)) == EXACT_IMPORTS
    assert "namespace FEP.GaussianPrecisionConditioning\n" in raw_source
    assert raw_source.rstrip().endswith("end FEP.GaussianPrecisionConditioning")
    assert "FEPProbe" not in raw_source
    assert "open FEP.Fin4GaussianSemigroup\n" in raw_source
    assert "open FEP.Fin4GaussianSemigroup.Axis\n" in raw_source
    assert not re.search(
        r"(?m)^(?:inductive|structure|class|abbrev|def|noncomputable def)\s+"
        r"(?:Axis|StandardizedState|K|Sigma|stationaryLaw|multivariateGaussian)\b",
        source,
    )
    assert "stationaryLaw center" in source
    assert "stationaryLaw_eq_gaussian center" in source
    assert "K_external_internal" in source
    assert "Sigma_external_internal" in source
    assert not re.search(
        r"\b(?:sorry|admit|axiom|opaque)\b|unsafe\s+(?:def|theorem)|:\s*True\b",
        source,
    )
    assert "Kernel.Posterior" not in source
    assert "Matrix.SchurComplement" not in source
    assert "05d_gaussian_conditioning" not in source
    assert not re.search(
        r"\b(?:causal|intervention|H2_7|H3|SDE|Ito|Itô|FokkerPlanck|"
        r"Girsanov|reversibility|thermodynamic|conditionallyIndependent|"
        r"Certificate|certificate)\b",
        source,
    )


def test_h2_5d_is_one_manifested_projected_foundation_not_an_aggregate_leaf() -> None:
    modules = tuple(
        module
        for module in FORMAL_MODULES
        if module.resource == "gaussian_precision_conditioning.lean"
    )
    resources = tuple(module.resource for module in FORMAL_MODULES)

    assert len(modules) == 1
    assert modules[0].lean_module == "FepSketches.gaussian_precision_conditioning"
    assert modules[0].role is FormalModuleRole.FOUNDATION
    assert modules[0].declaration_namespace == "FEP.GaussianPrecisionConditioning"
    assert resources.index("gaussian_precision_conditioning.lean") == (
        resources.index("fin4_gaussian_semigroup.lean") + 1
    )

    projection_pairs = dict(formal_projection_pairs(PROJECT_ROOT))
    assert projection_pairs[SOURCE] == PROJECTION
    assert PROJECTION.read_bytes() == SOURCE.read_bytes()

    aggregate = render_formal_aggregate()
    assert "import FepSketches.gaussian_precision_conditioning\n" not in aggregate


def test_h2_5d_projected_module_imports_with_native_instances_and_boundary(
    tmp_path: Path,
) -> None:
    olean = (
        LEAN_ROOT
        / ".lake"
        / "build"
        / "lib"
        / "lean"
        / "FepSketches"
        / "gaussian_precision_conditioning.olean"
    )
    olean.parent.mkdir(parents=True, exist_ok=True)
    emit = run_lean_compile_probe(
        PROJECTION,
        cwd=LEAN_ROOT,
        output_path=olean,
        timeout_s=300,
        executable=lake_executable(
            missing="raise",
            context="H2.5d native validation",
        ),
    )
    emit_output = emit.stdout + emit.stderr
    assert emit.returncode == 0, emit_output
    assert olean.is_file() and olean.stat().st_size > 0
    assert "warning:" not in emit_output.lower()

    probe = tmp_path / "GaussianPrecisionConditioningProjectedConsumer.lean"
    probe.write_text(
        r"""import FepSketches.gaussian_precision_conditioning

open ProbabilityTheory
open FEP.Fin4GaussianSemigroup
open FEP.Fin4GaussianSemigroup.Axis
open FEP.GaussianPrecisionConditioning

example (center : StandardizedState) :
    IsMarkovKernel (endpointConditionalKernel center) := by infer_instance

example (center : StandardizedState) :
    K external internal = 0 ∧
      cov[fun state : StandardizedState => state external,
        fun state => state internal; stationaryLaw center] = 1 / 24 ∧
      cov[fun state : StandardizedState => state external,
        fun state => state internal; stationaryLaw center] ≠ 0 ∧
      ((fun state : StandardizedState => state external) ⟂ᵢ[
        blanketCoordinates, measurable_blanketCoordinates; stationaryLaw center]
        (fun state => state internal)) :=
  precisionZero_covarianceNonzero_condIndep center

example : ¬ IndepFun perturbedExternal perturbedInternal perturbedEndpointLaw :=
  perturbedEndpoint_external_not_indep_internal
""",
        encoding="utf-8",
    )
    result = _run_lean(probe)
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "warning:" not in output.lower()


def test_h2_5d_public_source_roster_and_fixed_formulas_are_exact() -> None:
    source = lean_code_without_comments(SOURCE.read_text(encoding="utf-8"))

    assert tuple(re.findall(r"(?m)^abbrev (\w+)\b", source)) == PUBLIC_ABBREVIATIONS
    assert (
        tuple(re.findall(r"(?m)^(?!private\b)(?:noncomputable )?def (\w+)\b", source))
        == PUBLIC_DEFINITIONS
    )
    assert (
        tuple(
            re.findall(r"(?m)^(?!private\b)(?:noncomputable )?instance (\w+)\b", source)
        )
        == PUBLIC_INSTANCES
    )
    assert (
        tuple(re.findall(r"(?m)^(?!private\b)theorem (\w+)\b", source))
        == PUBLIC_THEOREMS
    )

    assert re.search(
        r"def blanketCoordinates \(state : StandardizedState\) : Blanket :=\s*"
        r"\(state sensory, state active\)",
        source,
    )
    assert re.search(
        r"def endpointCoordinates \(state : StandardizedState\) : Endpoints :=\s*"
        r"\(state external, state internal\)",
        source,
    )
    assert re.search(
        r"def conditionalOffset \(center : StandardizedState\) "
        r"\(blanket : Blanket\) : ℝ :=\s*"
        r"\(\(blanket\.1 - center sensory\) \+ "
        r"\(blanket\.2 - center active\)\) / 4",
        source,
    )
    assert "center external + conditionalOffset center blanket" in source
    assert "center internal + conditionalOffset center blanket" in source
    assert re.search(
        r"noncomputable def perturbedEndpointCovariance[^:]*:\s*"
        r"Matrix \(Fin 2\) \(Fin 2\) ℝ :=\s*"
        r"perturbedEndpointPrecision⁻¹",
        source,
    )
    assert source.count("!![4, 1; 1, 4]") == 1
    assert "multivariateGaussian 0 perturbedEndpointCovariance" in source
    assert re.search(
        r"def perturbedExternal \(state : PerturbedEndpoints\) : ℝ :=\s*state 0",
        source,
    )
    assert re.search(
        r"def perturbedInternal \(state : PerturbedEndpoints\) : ℝ :=\s*state 1",
        source,
    )


def test_h2_5d_environment_census_rejects_hidden_declaration_forms(
    tmp_path: Path,
) -> None:
    probe = tmp_path / "GaussianPrecisionConditioningCensusMutations.lean"
    probe.write_text(
        """import FepSketches.fin4_gaussian_semigroup

namespace FEP.GaussianPrecisionConditioningCensusMutation

lemma publicLemma : (0 : Nat) = 0 := rfl

protected theorem protectedTheorem : (1 : Nat) = 1 := rfl

@[simp]
theorem attributedTheorem (value : Nat) : value + 0 = value := by simp

@[simp] theorem sameLineTheorem (value : Nat) : 0 + value = value := by simp

end FEP.GaussianPrecisionConditioningCensusMutation

#print prefix FEP.GaussianPrecisionConditioningCensusMutation
""",
        encoding="utf-8",
    )
    result = _run_lean(probe)
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    mutations = frozenset(
        {
            "publicLemma",
            "protectedTheorem",
            "attributedTheorem",
            "sameLineTheorem",
        }
    )
    assert (
        _parse_namespace_declaration_names(
            output, "FEP.GaussianPrecisionConditioningCensusMutation"
        )
        == mutations
    )
    with pytest.raises(AssertionError) as rejected:
        _assert_exact_namespace_declarations(
            output, "FEP.GaussianPrecisionConditioningCensusMutation", frozenset()
        )
    for name in mutations:
        assert name in str(rejected.value)


def test_h2_5d_canonical_source_compiles_warning_free() -> None:
    result = _run_lean(SOURCE)
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "warning:" not in output.lower()


def test_h2_5d_public_axioms_census_and_typed_consumers(tmp_path: Path) -> None:
    probe = tmp_path / "GaussianPrecisionConditioningAudit.lean"
    source = SOURCE.read_text(encoding="utf-8")
    prints = "\n".join(
        f"#print axioms FEP.GaussianPrecisionConditioning.{name}"
        for name in PUBLIC_THEOREMS
    )
    consumers = r"""
open MeasureTheory ProbabilityTheory
open scoped ENNReal MeasureTheory NNReal ProbabilityTheory
open FEP.Fin4GaussianSemigroup
open FEP.Fin4GaussianSemigroup.Axis
open FEP.GaussianPrecisionConditioning

variable (center : StandardizedState) (blanket : Blanket)

example : IsProbabilityMeasure (blanketLaw center) := inferInstance
example : IsMarkovKernel (externalConditionalKernel center) := inferInstance
example : IsMarkovKernel (internalConditionalKernel center) := inferInstance
example : IsMarkovKernel (endpointConditionalKernel center) := inferInstance
example : IsProbabilityMeasure perturbedEndpointLaw := inferInstance

example :
    externalConditionalMean center blanket =
      center external +
        ((blanket.1 - center sensory) + (blanket.2 - center active)) / 4 :=
  rfl

example :
    internalConditionalMean center blanket =
      center internal +
        ((blanket.1 - center sensory) + (blanket.2 - center active)) / 4 :=
  rfl

example :
    ∫ value, value ∂externalConditionalKernel center blanket =
      externalConditionalMean center blanket :=
  externalConditionalKernel_mean center blanket

example : Var[id; externalConditionalKernel center blanket] = 1 / 4 :=
  externalConditionalKernel_variance center blanket

example :
    ∫ value, value ∂internalConditionalKernel center blanket =
      internalConditionalMean center blanket :=
  internalConditionalKernel_mean center blanket

example : Var[id; internalConditionalKernel center blanket] = 1 / 4 :=
  internalConditionalKernel_variance center blanket

example :
    (stationaryLaw center).map partitionCoordinates =
      blanketLaw center ⊗ₘ endpointConditionalKernel center :=
  stationaryPartition_eq_compProd center

example :
    condDistrib endpointCoordinates blanketCoordinates (stationaryLaw center)
      =ᵐ[blanketLaw center] endpointConditionalKernel center :=
  endpointCondDistrib_ae_eq_product center

example :
    condDistrib (fun state : StandardizedState => state external)
        blanketCoordinates (stationaryLaw center) =ᵐ[blanketLaw center]
      externalConditionalKernel center :=
  externalCondDistrib_ae_eq center

example :
    condDistrib (fun state : StandardizedState => state internal)
        blanketCoordinates (stationaryLaw center) =ᵐ[blanketLaw center]
      internalConditionalKernel center :=
  internalCondDistrib_ae_eq center

example :
    (fun state : StandardizedState => state external) ⟂ᵢ[
      blanketCoordinates, measurable_blanketCoordinates; stationaryLaw center]
      (fun state => state internal) :=
  external_condIndep_internal_given_blanket center

example (sensoryValue activeValue : ℝ) :
    externalConditionalMean (0 : StandardizedState)
        (sensoryValue, activeValue) = (sensoryValue + activeValue) / 4 := by
  simp [externalConditionalMean, conditionalOffset]

example (sensoryValue activeValue : ℝ) :
    internalConditionalMean (0 : StandardizedState)
        (sensoryValue, activeValue) = (sensoryValue + activeValue) / 4 := by
  simp [internalConditionalMean, conditionalOffset]

example :
    cov[fun state : StandardizedState => state external,
      fun state => state internal; stationaryLaw center] = 1 / 24 :=
  stationary_external_internal_covariance center

example :
    K external internal = 0 ∧
      cov[fun state : StandardizedState => state external,
        fun state => state internal; stationaryLaw center] = 1 / 24 ∧
      cov[fun state : StandardizedState => state external,
        fun state => state internal; stationaryLaw center] ≠ 0 ∧
      ((fun state : StandardizedState => state external) ⟂ᵢ[
        blanketCoordinates, measurable_blanketCoordinates; stationaryLaw center]
        (fun state => state internal)) :=
  precisionZero_covarianceNonzero_condIndep center

example : perturbedEndpointPrecision.PosDef :=
  perturbedEndpointPrecision_posDef
example : perturbedEndpointCovariance.PosDef :=
  perturbedEndpointCovariance_posDef
example :
    perturbedEndpointCovariance = !![4 / 15, -1 / 15; -1 / 15, 4 / 15] :=
  perturbedEndpointCovariance_eq_entries

example : perturbedEndpointPrecision 0 0 = 4 := rfl
example : perturbedEndpointPrecision 0 1 = 1 :=
  perturbedEndpointPrecision_external_internal
example : perturbedEndpointPrecision 1 0 = 1 := rfl
example : perturbedEndpointPrecision 1 1 = 4 := rfl

example : perturbedEndpointCovariance 0 0 = 4 / 15 := by
  rw [perturbedEndpointCovariance_eq_entries]
  norm_num
example : perturbedEndpointCovariance 0 1 = -1 / 15 :=
  perturbedEndpointCovariance_external_internal
example : perturbedEndpointCovariance 1 0 = -1 / 15 := by
  rw [perturbedEndpointCovariance_eq_entries]
  norm_num
example : perturbedEndpointCovariance 1 1 = 4 / 15 := by
  rw [perturbedEndpointCovariance_eq_entries]
  norm_num

example :
    cov[perturbedExternal, perturbedInternal; perturbedEndpointLaw] = -1 / 15 :=
  perturbedEndpoint_external_internal_covariance

example : ¬ IndepFun perturbedExternal perturbedInternal perturbedEndpointLaw :=
  perturbedEndpoint_external_not_indep_internal
"""
    probe.write_text(
        f"{source}\n{prints}\n#print prefix "
        f"FEP.GaussianPrecisionConditioning\n{consumers}\n",
        encoding="utf-8",
    )
    result = _run_lean(probe)
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "sorryAx" not in output
    assert "warning:" not in output.lower()
    _assert_exact_namespace_declarations(
        output, "FEP.GaussianPrecisionConditioning", PUBLIC_ENVIRONMENT_DECLARATIONS
    )

    reports_seen = 0
    nonempty_reports = 0
    for name in PUBLIC_THEOREMS:
        full_name = f"FEP.GaussianPrecisionConditioning.{name}"
        report = re.search(
            rf"'{re.escape(full_name)}' "
            r"(?:depends on axioms: \[(?P<axioms>.*?)\]"
            r"|does not depend on any axioms)",
            output,
            re.DOTALL,
        )
        assert report is not None, full_name
        reports_seen += 1
        if (block := report.group("axioms")) is not None:
            axioms = _parse_axiom_names(block)
            nonempty_reports += bool(axioms)
            assert axioms <= ALLOWED_AXIOMS, (full_name, axioms)
    assert reports_seen == len(PUBLIC_THEOREMS)
    assert nonempty_reports > 0


def test_h2_5d_preserves_h2_5c_r0_hashes_and_readiness_validation() -> None:
    for path, expected in PRESERVED_HASHES.items():
        assert path.is_file()
        assert _sha256(path) == expected

    assert _sha256(R0_REPAIR) == R0_REPAIR_SHA256
    repair = json.loads(R0_REPAIR.read_text(encoding="utf-8"))
    assert repair["decision"] == "go"
    for path, expected in PRESERVED_HASHES.items():
        relative = path.relative_to(PROJECT_ROOT).as_posix()
        assert repair["source_sha256"][relative] == expected

    assert _sha256(R0_LIFECYCLE) == R0_LIFECYCLE_SHA256
    lifecycle = json.loads(R0_LIFECYCLE.read_text(encoding="utf-8"))
    assert lifecycle["gate"] == "H2.5d-R0-lifecycle"
    assert lifecycle["decision"] == "provenance_correction"
    assert lifecycle["decision_scope"] == "record_test_lifecycle_correction_only"
    assert lifecycle["historical_artifact"] == {
        "guard": "assert not MAINTAINED_OWNER.exists()",
        "test_sha256": ORIGINAL_R0_TEST_SHA256,
    }
    assert lifecycle["corrected_artifact"] == {
        "guard": "if not REPAIR.exists(): assert not MAINTAINED_OWNER.exists()",
        "repair_sha256": R0_REPAIR_SHA256,
        "test_sha256": PRESERVED_HASHES[R0_TEST],
    }
    assert lifecycle["preserved_boundary"]["scientific_claim_mutated"] is False
    assert (
        lifecycle["preserved_boundary"]["r0_spike_sha256"]
        == (PRESERVED_HASHES[R0_SPIKE])
    )
    assert lifecycle["supersession"] == {
        "further_in_place_receipt_mutation_allowed": False,
        "historical_test_digest_retained": True,
        "supersedes_only_owner_absence_lifecycle_assertion": True,
    }

    result = subprocess.run(
        [
            "uv",
            "run",
            "python",
            str(READINESS_VALIDATOR.relative_to(PROJECT_ROOT)),
            "--check",
            "--project-root",
            str(PROJECT_ROOT),
        ],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert output.strip() == "H2.0 readiness matrix: valid"
