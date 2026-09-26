"""H2.5d-R0 fixed Fin4 native Gaussian-conditioning spike contracts."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest

from fep_lean.formal import formal_projection_pairs
from fep_lean.formal.manifest import FORMAL_MODULES
from fep_lean.lean_source import lean_code_without_comments
from tests._support.lake import lake_executable
from tests._support.lean_runner import run_lean_compile_probe, run_lean_probe

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEAN_ROOT = PROJECT_ROOT / "lean"
SPIKE = (
    PROJECT_ROOT
    / "specs"
    / "done"
    / "horizon-2-smooth-stochastic"
    / "spikes"
    / "05d_gaussian_conditioning.lean"
)
REPAIR = (
    PROJECT_ROOT
    / "specs"
    / "done"
    / "horizon-2-smooth-stochastic"
    / "readiness"
    / "repairs"
    / "05d-gaussian-conditioning.json"
)
MAINTAINED_OWNER = (
    PROJECT_ROOT
    / "src"
    / "fep_lean"
    / "formal"
    / "gaussian_precision_conditioning.lean"
)
SOURCE_BOUND_PATHS = (
    "lean/lean-toolchain",
    "lean/lakefile.lean",
    "lean/lake-manifest.json",
    "specs/done/horizon-2-smooth-stochastic/readiness/acceptance.json",
    "specs/done/horizon-2-smooth-stochastic/readiness/matrix.yaml",
    "specs/done/horizon-2-smooth-stochastic/readiness/probes/08_gaussian_conditioning.lean",
    "src/fep_lean/formal/fin4_gaussian_semigroup.lean",
    "specs/done/horizon-2-smooth-stochastic/slices/05d-r0-gaussian-conditioning.md",
    "specs/done/horizon-2-smooth-stochastic/spikes/05d_gaussian_conditioning.lean",
    "tests/test_horizon2_gaussian_conditioning_readiness.py",
)

EXACT_IMPORTS = (
    "FepSketches.fin4_gaussian_semigroup",
    "Mathlib.Probability.Distributions.Gaussian.HasGaussianLaw.Independence",
    "Mathlib.Probability.Independence.Conditional",
)
PUBLIC_ABBREVIATIONS = ("Blanket", "Endpoints")
PUBLIC_DEFINITIONS = (
    "blanketCoordinates",
    "endpointCoordinates",
    "partitionCoordinates",
    "blanketLaw",
    "conditionalOffset",
    "externalConditionalKernel",
    "internalConditionalKernel",
    "endpointConditionalKernel",
)
PUBLIC_THEOREMS = (
    "measurable_blanketCoordinates",
    "measurable_endpointCoordinates",
    "measurable_partitionCoordinates",
    "externalConditionalKernel_apply",
    "internalConditionalKernel_apply",
    "endpointConditionalKernel_apply",
    "stationaryPartition_eq_compProd",
    "endpointCondDistrib_ae_eq_product",
    "externalCondDistrib_ae_eq",
    "internalCondDistrib_ae_eq",
    "external_condIndep_internal_given_blanket",
    "fixed_precisionZero_covarianceNonzero_condIndep",
)
PUBLIC_ENVIRONMENT_DECLARATIONS = frozenset(
    (*PUBLIC_ABBREVIATIONS, *PUBLIC_DEFINITIONS, *PUBLIC_THEOREMS)
)
ALLOWED_AXIOMS = frozenset({"propext", "Classical.choice", "Quot.sound"})

pytestmark = pytest.mark.serial_lean


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _parse_axiom_names(block: str) -> set[str]:
    return {
        token.strip().strip("'")
        for token in block.split(",")
        if token.strip().strip("'")
    }


def _parse_namespace_declaration_names(output: str) -> frozenset[str]:
    qualified_prefix = re.escape("FEPProbe.H2_5dGaussianConditioning.")
    return frozenset(
        re.findall(
            rf"'{qualified_prefix}"
            r"([A-Za-z_][A-Za-z0-9_']*(?:\.[A-Za-z_][A-Za-z0-9_']*)*)' "
            r"(?:depends on axioms: \[.*?\]|does not depend on any axioms)",
            output,
            re.DOTALL,
        )
    )


def test_h2_5d_r0_is_spike_only_and_not_projected() -> None:
    assert SPIKE.is_file()
    if not REPAIR.exists():
        assert not MAINTAINED_OWNER.exists()
    assert all(module.resource != SPIKE.name for module in FORMAL_MODULES)
    projected_sources = {
        source.resolve() for source, _ in formal_projection_pairs(PROJECT_ROOT)
    }
    assert SPIKE.resolve() not in projected_sources


def test_h2_5d_r0_reuses_only_the_fixed_h2_5c_carrier() -> None:
    raw_source = SPIKE.read_text(encoding="utf-8")
    source = lean_code_without_comments(raw_source)

    assert tuple(re.findall(r"(?m)^import (\S+)$", raw_source)) == EXACT_IMPORTS
    assert "namespace FEPProbe.H2_5dGaussianConditioning\n" in raw_source
    assert raw_source.rstrip().endswith("end FEPProbe.H2_5dGaussianConditioning")
    assert "open FEP.Fin4GaussianSemigroup\n" in raw_source
    assert "open FEP.Fin4GaussianSemigroup.Axis\n" in raw_source
    assert not re.search(
        r"(?m)^(?:inductive|structure|class|abbrev|def|noncomputable def)\s+"
        r"(?:Axis|StandardizedState|K|Sigma|stationaryLaw|multivariateGaussian)\b",
        source,
    )
    assert "stationaryLaw (0 : StandardizedState)" in source
    assert "stationaryLaw_eq_gaussian 0" in source
    assert "K_external_internal" in source
    assert "Sigma_external_internal" in source
    assert "Sigma_external_internal_ne_zero" in source


def test_h2_5d_r0_coordinates_and_gaussian_rows_are_exact() -> None:
    source = lean_code_without_comments(SPIKE.read_text(encoding="utf-8"))

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
        r"def partitionCoordinates \(state : StandardizedState\) : "
        r"Blanket × Endpoints :=\s*"
        r"\(blanketCoordinates state, endpointCoordinates state\)",
        source,
    )
    assert re.search(
        r"noncomputable def blanketLaw : Measure Blanket :=\s*"
        r"\(stationaryLaw \(0 : StandardizedState\)\)\.map blanketCoordinates",
        source,
    )
    assert re.search(
        r"def conditionalOffset \(blanket : Blanket\) : ℝ :=\s*"
        r"\(blanket\.1 \+ blanket\.2\) / 4",
        source,
    )
    assert source.count("gaussianReal (conditionalOffset blanket) (1 / 4)") >= 4
    assert re.search(
        r"noncomputable def endpointConditionalKernel : Kernel Blanket "
        r"Endpoints :=\s*"
        r"externalConditionalKernel ×ₖ internalConditionalKernel",
        source,
    )
    assert re.search(
        r"theorem endpointConditionalKernel_apply \(blanket : Blanket\) :\s*"
        r"endpointConditionalKernel blanket =\s*"
        r"\(gaussianReal \(\(blanket\.1 \+ blanket\.2\) / 4\) \(1 / 4\)\)"
        r"\.prod\s*"
        r"\(gaussianReal \(\(blanket\.1 \+ blanket\.2\) / 4\) \(1 / 4\)\)",
        source,
    )


def test_h2_5d_r0_native_factorization_and_conditional_surface_are_exact() -> None:
    source = lean_code_without_comments(SPIKE.read_text(encoding="utf-8"))

    assert re.search(
        r"theorem stationaryPartition_eq_compProd\s*:\s*"
        r"\(stationaryLaw \(0 : StandardizedState\)\)\.map "
        r"partitionCoordinates =\s*blanketLaw ⊗ₘ endpointConditionalKernel",
        source,
    )
    assert re.search(
        r"theorem endpointCondDistrib_ae_eq_product\s*:\s*"
        r"condDistrib endpointCoordinates blanketCoordinates\s*"
        r"\(stationaryLaw \(0 : StandardizedState\)\) "
        r"=ᵐ\[blanketLaw\]\s*endpointConditionalKernel",
        source,
    )
    assert re.search(
        r"theorem externalCondDistrib_ae_eq\s*:\s*"
        r"condDistrib \(fun state : StandardizedState => state external\)\s*"
        r"blanketCoordinates \(stationaryLaw \(0 : StandardizedState\)\) "
        r"=ᵐ\[blanketLaw\]\s*externalConditionalKernel",
        source,
    )
    assert re.search(
        r"theorem internalCondDistrib_ae_eq\s*:\s*"
        r"condDistrib \(fun state : StandardizedState => state internal\)\s*"
        r"blanketCoordinates \(stationaryLaw \(0 : StandardizedState\)\) "
        r"=ᵐ\[blanketLaw\]\s*internalConditionalKernel",
        source,
    )
    assert "condDistrib_ae_eq_of_measure_eq_compProd_of_measurable" in source
    assert "condDistrib_comp" in source
    assert "condIndepFun_iff_map_prod_eq_prod_condDistrib_prod_condDistrib" in source
    assert "Measure.compProd_congr" in source
    assert re.search(
        r"theorem external_condIndep_internal_given_blanket\s*:\s*"
        r"\(fun state : StandardizedState => state external\) ⟂ᵢ\[\s*"
        r"blanketCoordinates, measurable_blanketCoordinates;\s*"
        r"stationaryLaw \(0 : StandardizedState\)\]\s*"
        r"\(fun state => state internal\)",
        source,
    )


def test_h2_5d_r0_combined_boundary_is_typed_and_nonvacuous() -> None:
    source = lean_code_without_comments(SPIKE.read_text(encoding="utf-8"))

    assert re.search(
        r"theorem fixed_precisionZero_covarianceNonzero_condIndep\s*:\s*"
        r"K external internal = 0 ∧\s*"
        r"cov\[fun state : StandardizedState => state external,\s*"
        r"fun state => state internal; "
        r"stationaryLaw \(0 : StandardizedState\)\] =\s*"
        r"1 / 24 ∧\s*"
        r"cov\[fun state : StandardizedState => state external,\s*"
        r"fun state => state internal; "
        r"stationaryLaw \(0 : StandardizedState\)\] ≠\s*"
        r"0 ∧\s*"
        r"\(\(fun state : StandardizedState => state external\) ⟂ᵢ\[",
        source,
    )
    assert source.count("rw [covariance_coordinate]") >= 2
    assert "exact Sigma_external_internal\n" in source
    assert "exact Sigma_external_internal_ne_zero\n" in source
    assert "exact ⟨K_external_internal, hCovariance, hCovarianceNonzero," in source


def test_h2_5d_r0_public_surface_is_exact_and_fail_closed() -> None:
    source = lean_code_without_comments(SPIKE.read_text(encoding="utf-8"))

    assert tuple(re.findall(r"(?m)^abbrev (\w+)\b", source)) == (PUBLIC_ABBREVIATIONS)
    assert (
        tuple(re.findall(r"(?m)^(?:noncomputable )?def (\w+)\b", source))
        == PUBLIC_DEFINITIONS
    )
    assert tuple(re.findall(r"(?m)^theorem (\w+)\b", source)) == PUBLIC_THEOREMS
    assert not re.search(r"(?m)^(?:noncomputable )?instance\b", source)
    assert not re.search(
        r"\b(?:sorry|admit|axiom|opaque)\b|unsafe\s+(?:def|theorem)|:\s*True\b",
        source,
    )
    assert not re.search(
        r"\b(?:PDF|SchurComplement|posterior|certificate|Certificate|"
        r"witness|Witness|transition|arbitraryCenter|H2_6a|H2_7|H3|"
        r"causal|intervention|reversibility|thermodynamic|SDE|Ito|Itô|"
        r"FokkerPlanck|Girsanov|Brownian)\b",
        source,
    )
    assert not re.search(r"\(center\s*:\s*StandardizedState\)", source)
    assert not re.search(r"Matrix\.SchurComplement|Kernel\.Posterior", source)


def test_h2_5d_r0_spike_compiles_warning_free(tmp_path: Path) -> None:
    probe = tmp_path / "H2_5dGaussianConditioningSpike.lean"
    probe.write_text(SPIKE.read_text(encoding="utf-8"), encoding="utf-8")
    result = run_lean_probe(
        probe,
        import_root=PROJECT_ROOT / "src" / "fep_lean" / "formal",
        cwd=LEAN_ROOT,
        timeout_s=1800,
    )

    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "warning:" not in output.lower()


def test_h2_5d_r0_public_axioms_census_and_typed_consumers(tmp_path: Path) -> None:
    probe = tmp_path / "H2_5dGaussianConditioningAudit.lean"
    source = SPIKE.read_text(encoding="utf-8")
    # v4.34 migration: Lean core rejects `#print prefix`, so emit one
    # `#print axioms` per roster member; a missing declaration fails its own
    # report so the roster stays fail-closed, and reports quote full names.
    prints = "\n".join(
        f"#print axioms FEPProbe.H2_5dGaussianConditioning.{name}"
        for name in sorted(PUBLIC_ENVIRONMENT_DECLARATIONS)
    )
    consumers = r"""
open MeasureTheory ProbabilityTheory
open scoped ENNReal MeasureTheory NNReal ProbabilityTheory
open FEP.Fin4GaussianSemigroup
open FEP.Fin4GaussianSemigroup.Axis
open FEPProbe.H2_5dGaussianConditioning

example : IsMarkovKernel endpointConditionalKernel := inferInstance

example :
    (stationaryLaw (0 : StandardizedState)).map partitionCoordinates =
      blanketLaw ⊗ₘ endpointConditionalKernel :=
  stationaryPartition_eq_compProd

example :
    condDistrib endpointCoordinates blanketCoordinates
        (stationaryLaw (0 : StandardizedState)) =ᵐ[blanketLaw]
      endpointConditionalKernel :=
  endpointCondDistrib_ae_eq_product

example :
    condDistrib (fun state : StandardizedState => state external)
        blanketCoordinates (stationaryLaw (0 : StandardizedState)) =ᵐ[blanketLaw]
      externalConditionalKernel :=
  externalCondDistrib_ae_eq

example :
    condDistrib (fun state : StandardizedState => state internal)
        blanketCoordinates (stationaryLaw (0 : StandardizedState)) =ᵐ[blanketLaw]
      internalConditionalKernel :=
  internalCondDistrib_ae_eq

example :
    (fun state : StandardizedState => state external) ⟂ᵢ[
      blanketCoordinates, measurable_blanketCoordinates;
      stationaryLaw (0 : StandardizedState)]
      (fun state => state internal) :=
  external_condIndep_internal_given_blanket

example :
    K external internal = 0 ∧
      cov[fun state : StandardizedState => state external,
        fun state => state internal; stationaryLaw (0 : StandardizedState)] =
          1 / 24 ∧
      cov[fun state : StandardizedState => state external,
        fun state => state internal; stationaryLaw (0 : StandardizedState)] ≠
          0 ∧
      ((fun state : StandardizedState => state external) ⟂ᵢ[
        blanketCoordinates, measurable_blanketCoordinates;
        stationaryLaw (0 : StandardizedState)]
        (fun state => state internal)) :=
  fixed_precisionZero_covarianceNonzero_condIndep
"""
    probe.write_text(
        f"{source}\n{prints}\n{consumers}\n",
        encoding="utf-8",
    )
    result = run_lean_compile_probe(
        probe,
        cwd=LEAN_ROOT,
        timeout_s=300,
        executable=lake_executable(
            missing="raise",
            context="H2.5d-R0 native validation",
        ),
    )

    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "sorryAx" not in output
    assert "warning:" not in output.lower()
    actual_declarations = _parse_namespace_declaration_names(output)
    missing = sorted(PUBLIC_ENVIRONMENT_DECLARATIONS - actual_declarations)
    extra = sorted(actual_declarations - PUBLIC_ENVIRONMENT_DECLARATIONS)
    assert not missing and not extra, f"missing={missing}; extra={extra}"
    reports_seen = 0
    nonempty_reports = 0
    for name in PUBLIC_THEOREMS:
        full_name = f"FEPProbe.H2_5dGaussianConditioning.{name}"
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


def test_h2_5d_r0_repair_is_source_bound_append_only_go() -> None:
    assert REPAIR.is_file()
    repair = json.loads(REPAIR.read_text(encoding="utf-8"))

    assert repair["schema_version"] == 1
    assert repair["gate"] == "H2.5d-R0"
    assert repair["decision"] == "go"
    assert repair["decision_scope"] == "open_H2.5d_implementation_only"
    assert repair["historical_boundary"] == {
        "acceptance_mutated": False,
        "addendum_only": True,
        "matrix_mutated": False,
        "row_id": "gaussian_conditioning_precision",
        "row_status_at_decision": "blocking_no_go",
    }
    assert repair["compiler"] == {
        "lean_commit": "819816b2e0a3bf405af45ae5c7af2491d8f5bee6",
        "lean_version": "4.33.1",
        "mathlib_revision": "0df444a360eaa60ab8c11dca51a86af692955474",
        "mathlib_tag": "v4.33.1",
    }
    assert repair["imports"] == list(EXACT_IMPORTS)
    assert repair["declarations"] == {
        "abbreviations": list(PUBLIC_ABBREVIATIONS),
        "definitions": list(PUBLIC_DEFINITIONS),
        "theorems": list(PUBLIC_THEOREMS),
    }
    assert repair["coordinate_order"] == {
        "blanket": ["sensory", "active"],
        "endpoints": ["external", "internal"],
        "partition": ["blanket", "endpoints"],
    }
    assert repair["conditional_formulas"] == {
        "common_mean": "(sensory + active) / 4",
        "external_variance": "1 / 4",
        "internal_variance": "1 / 4",
        "endpoint_row": ("externalConditionalKernel ×ₖ internalConditionalKernel"),
    }
    assert repair["proof_route"] == {
        "center": "0",
        "condDistrib_scope": "blanketLaw_almost_everywhere",
        "conditional_independence": "native_CondIndepFun",
        "joint_factorization_orientation": "stationary_map_equals_compProd",
        "marginal_covariance": "cov[external, internal; stationaryLaw 0] = 1 / 24",
        "pointwise_condDistrib_claim": False,
        "scope_substitution_used": False,
        "stationary_law": True,
    }
    assert repair["evidence"]["compiler_exit_code"] == 0
    assert repair["evidence"]["warning_count"] == 0
    assert repair["evidence"]["warning_sha256"] == hashlib.sha256(b"").hexdigest()
    assert repair["evidence"]["standard_axiom_audit"] is True
    assert repair["evidence"]["public_theorem_count"] == len(PUBLIC_THEOREMS)
    assert repair["evidence"]["allowed_axioms"] == [
        "propext",
        "Classical.choice",
        "Quot.sound",
    ]
    assert repair["evidence"]["sorry_axiom_present"] is False
    assert repair["review"] == {
        "independent_claim": "approved_scope_exact",
        "independent_gaussian_graphical_model": ("approved_no_mathematical_blocker"),
        "independent_lean_probability": "approved_no_mathematical_blocker",
    }
    assert repair["downstream"] == {
        "opened": ["H2.5d implementation"],
        "remains_closed": [
            "H2.7 terminal filter/control clauses",
            "continuous H3 eligibility",
        ],
    }
    required_no_go_claims = {
        "arbitrary-center conditioning",
        "generic precision conditional-independence equivalence",
        "pointwise regular conditional distribution",
        "unconditional endpoint independence",
        "transition-row conditioning",
        "converse",
        "causal separation",
        "physical Markov blanket",
        "continuous-path result",
        "H2.7 result",
        "H3 result",
    }
    assert required_no_go_claims <= set(repair["reviewed_no_go_claims"])
    assert repair["source_sha256"] == {
        relative: _sha256(PROJECT_ROOT / relative) for relative in SOURCE_BOUND_PATHS
    }
