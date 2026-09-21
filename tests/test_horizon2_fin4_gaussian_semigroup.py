"""H2.5c exact named-axis four-coordinate Gaussian carrier contracts."""

from __future__ import annotations

import re
import tempfile
from fractions import Fraction
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
    PROJECT_ROOT / "src" / "fep_lean" / "formal" / "fin4_gaussian_semigroup.lean"
)

pytestmark = pytest.mark.serial_lean

EXACT_IMPORTS = ("FepSketches.linear_gaussian_semigroup",)
PUBLIC_DEFINITIONS = (
    "axisFin",
    "K",
    "Sigma",
    "eigenmodeTwo",
    "eigenmodeFourExternal",
    "eigenmodeFourSensory",
    "eigenmodeSix",
    "parameters",
    "transition",
    "nativeSemigroup",
    "stationaryLaw",
    "transitionProbability",
    "stationaryProbability",
    "normalizedAllOnes",
    "allOnesProjection",
    "allOnesEmbedding",
    "scalarParameters",
    "projectedTransition",
)
PUBLIC_THEOREMS = (
    "axisFin_order",
    "axis_cardinality",
    "axis_pairwise_ne",
    "K_isSymm",
    "K_isHermitian",
    "K_posDef",
    "K_eigenmode_two",
    "K_eigenmode_four_external",
    "K_eigenmode_four_sensory",
    "K_eigenmode_six",
    "eigenmodes_nonzero",
    "eigenmodes_independent",
    "K_mul_Sigma",
    "Sigma_mul_K",
    "Sigma_eq_entries",
    "Sigma_isSymm",
    "Sigma_posDef",
    "K_external_internal",
    "Sigma_external_internal",
    "Sigma_external_internal_ne_zero",
    "parameters_covariance",
    "transitionCovariance_posSemidef",
    "transitionCovariance_posDef",
    "transition_apply",
    "transition_univ",
    "transition_zero",
    "transition_add",
    "stationaryLaw_eq_gaussian",
    "stationaryLaw_invariant",
    "transition_mean",
    "transition_covariance",
    "transitionProbability_tendsto_invariant",
    "integral_transition_tendsto_invariant",
    "normalizedAllOnes_unit",
    "allOnesProjection_embedding",
    "allOnes_projection_nontrivial",
    "K_normalizedAllOnes",
    "Sigma_normalizedAllOnes",
    "evolution_normalizedAllOnes",
    "scalarParameters_exact",
    "projectedTransition_eq_scalarOU",
    "exactFin4Carrier",
)
PUBLIC_INSTANCES = (
    "instDecidableEqAxis",
    "instFintypeAxis",
    "transition_isMarkovKernel",
    "stationaryLaw_isProbabilityMeasure",
)
AXIS_GENERATED_DECLARATIONS = (
    "Axis.active",
    "Axis.active.elim",
    "Axis.active.sizeOf_spec",
    "Axis.casesOn",
    "Axis.ctorElim",
    "Axis.ctorElimType",
    "Axis.ctorIdx",
    "Axis.external",
    "Axis.external.elim",
    "Axis.external.sizeOf_spec",
    "Axis.internal",
    "Axis.internal.elim",
    "Axis.internal.sizeOf_spec",
    "Axis.noConfusion",
    "Axis.noConfusionType",
    "Axis.ofNat",
    "Axis.ofNat_ctorIdx",
    "Axis.rec",
    "Axis.recOn",
    "Axis.sensory",
    "Axis.sensory.elim",
    "Axis.sensory.sizeOf_spec",
    "Axis.toCtorIdx",
)
PUBLIC_ENVIRONMENT_DECLARATIONS = frozenset(
    (
        "Axis",
        "StandardizedState",
        *AXIS_GENERATED_DECLARATIONS,
        *PUBLIC_DEFINITIONS,
        *PUBLIC_THEOREMS,
        *PUBLIC_INSTANCES,
    )
)
ALLOWED_AXIOMS = frozenset({"propext", "Classical.choice", "Quot.sound"})
EXACT_FIN4_CARRIER_PROPOSITION = r"""
    Fintype.card Axis = 4 ∧
      (axisFin external = 0 ∧ axisFin sensory = 1 ∧
        axisFin active = 2 ∧ axisFin internal = 3) ∧
      (external ≠ sensory ∧ external ≠ active ∧ external ≠ internal ∧
        sensory ≠ active ∧ sensory ≠ internal ∧ active ≠ internal) ∧
      K.IsSymm ∧ K.PosDef ∧
      K * FEP.Fin4GaussianSemigroup.Sigma = 1 ∧
      FEP.Fin4GaussianSemigroup.Sigma * K = 1 ∧
      FEP.Fin4GaussianSemigroup.Sigma.IsSymm ∧
      FEP.Fin4GaussianSemigroup.Sigma.PosDef ∧
      (FEP.Fin4GaussianSemigroup.Sigma = fun
        | external, external => 7 / 24
        | external, sensory => 1 / 12
        | external, active => 1 / 12
        | external, internal => 1 / 24
        | sensory, external => 1 / 12
        | sensory, sensory => 7 / 24
        | sensory, active => 1 / 24
        | sensory, internal => 1 / 12
        | active, external => 1 / 12
        | active, sensory => 1 / 24
        | active, active => 7 / 24
        | active, internal => 1 / 12
        | internal, external => 1 / 24
        | internal, sensory => 1 / 12
        | internal, active => 1 / 12
        | internal, internal => 7 / 24) ∧
      K *ᵥ eigenmodeTwo = 2 • eigenmodeTwo ∧
      K *ᵥ eigenmodeFourExternal = 4 • eigenmodeFourExternal ∧
      K *ᵥ eigenmodeFourSensory = 4 • eigenmodeFourSensory ∧
      K *ᵥ eigenmodeSix = 6 • eigenmodeSix ∧
      (eigenmodeTwo ≠ 0 ∧ eigenmodeFourExternal ≠ 0 ∧
        eigenmodeFourSensory ≠ 0 ∧ eigenmodeSix ≠ 0) ∧
      (∀ two fourExternal fourSensory six : ℝ,
        (∀ axis,
          two * eigenmodeTwo axis +
              fourExternal * eigenmodeFourExternal axis +
              fourSensory * eigenmodeFourSensory axis +
              six * eigenmodeSix axis = 0) →
          two = 0 ∧ fourExternal = 0 ∧ fourSensory = 0 ∧ six = 0) ∧
      K external internal = 0 ∧
      FEP.Fin4GaussianSemigroup.Sigma external internal = 1 / 24 ∧
      FEP.Fin4GaussianSemigroup.Sigma external internal ≠ 0 ∧
      (∀ (time : ℝ≥0),
        (FEP.Fin4GaussianSemigroup.Sigma -
          NormedSpace.exp ((-(time : ℝ)) • K) *
              FEP.Fin4GaussianSemigroup.Sigma *
            (NormedSpace.exp ((-(time : ℝ)) • K))ᵀ).PosSemidef) ∧
      (∀ (time : ℝ≥0), 0 < time →
        (FEP.Fin4GaussianSemigroup.Sigma -
          NormedSpace.exp ((-(time : ℝ)) • K) *
              FEP.Fin4GaussianSemigroup.Sigma *
            (NormedSpace.exp ((-(time : ℝ)) • K))ᵀ).PosDef) ∧
      (∀ (center : StandardizedState) (time : ℝ≥0)
          (state : StandardizedState),
        transition center time state =
          multivariateGaussian
            (center + Matrix.toEuclideanCLM (𝕜 := ℝ)
              (NormedSpace.exp ((-(time : ℝ)) • K)) (state - center))
            (FEP.Fin4GaussianSemigroup.Sigma -
              NormedSpace.exp ((-(time : ℝ)) • K) *
                  FEP.Fin4GaussianSemigroup.Sigma *
                (NormedSpace.exp ((-(time : ℝ)) • K))ᵀ)) ∧
      (∀ (center : StandardizedState) (left right : ℝ≥0),
        transition center (left + right) =
          transition center right ∘ₖ transition center left) ∧
      (∀ center : StandardizedState,
        stationaryLaw center =
          multivariateGaussian center FEP.Fin4GaussianSemigroup.Sigma) ∧
      (∀ center : StandardizedState,
        FEP.MarkovSemigroup.InvariantLaw
          (nativeSemigroup center) (stationaryLaw center)) ∧
      (∀ center state : StandardizedState,
        Tendsto (fun time : ℝ≥0 => transitionProbability center time state)
          atTop (nhds (stationaryProbability center))) ∧
      ⟪normalizedAllOnes, normalizedAllOnes⟫ = 1 ∧
      K *ᵥ normalizedAllOnes = 2 • normalizedAllOnes ∧
      FEP.Fin4GaussianSemigroup.Sigma *ᵥ normalizedAllOnes =
        (1 / 2 : ℝ) • normalizedAllOnes ∧
      (∀ center : ℝ, (scalarParameters center).rate = 2 ∧
        (scalarParameters center).diffusionVarianceRate = 2) ∧
      (∀ (center : ℝ) (time : ℝ≥0),
        projectedTransition center time =
          (scalarParameters center).ouTransition time)
"""

K_STAR = (
    (Fraction(4), Fraction(-1), Fraction(-1), Fraction(0)),
    (Fraction(-1), Fraction(4), Fraction(0), Fraction(-1)),
    (Fraction(-1), Fraction(0), Fraction(4), Fraction(-1)),
    (Fraction(0), Fraction(-1), Fraction(-1), Fraction(4)),
)
SIGMA_STAR = (
    (Fraction(7, 24), Fraction(1, 12), Fraction(1, 12), Fraction(1, 24)),
    (Fraction(1, 12), Fraction(7, 24), Fraction(1, 24), Fraction(1, 12)),
    (Fraction(1, 12), Fraction(1, 24), Fraction(7, 24), Fraction(1, 12)),
    (Fraction(1, 24), Fraction(1, 12), Fraction(1, 12), Fraction(7, 24)),
)


def _matmul(
    left: tuple[tuple[Fraction, ...], ...],
    right: tuple[tuple[Fraction, ...], ...],
) -> tuple[tuple[Fraction, ...], ...]:
    return tuple(
        tuple(
            sum(
                (left[row][inner] * right[inner][column] for inner in range(4)),
                start=Fraction(0),
            )
            for column in range(4)
        )
        for row in range(4)
    )


def _matvec(
    matrix: tuple[tuple[Fraction, ...], ...],
    vector: tuple[Fraction, ...],
) -> tuple[Fraction, ...]:
    return tuple(
        sum(
            (matrix[row][column] * vector[column] for column in range(4)),
            start=Fraction(0),
        )
        for row in range(4)
    )


def _determinant(matrix: tuple[tuple[Fraction, ...], ...]) -> Fraction:
    if len(matrix) == 1:
        return matrix[0][0]
    return sum(
        (
            (-1 if column % 2 else 1)
            * matrix[0][column]
            * _determinant(
                tuple(
                    tuple(value for index, value in enumerate(row) if index != column)
                    for row in matrix[1:]
                )
            )
            for column in range(len(matrix))
        ),
        start=Fraction(0),
    )






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


def test_h2_5c_environment_census_rejects_every_public_declaration_form(
    tmp_path: Path,
) -> None:
    probe = tmp_path / "Fin4GaussianSemigroupCensusMutations.lean"
    probe.write_text(
        """import FepSketches.linear_gaussian_semigroup

namespace FEP.Fin4GaussianCensusMutation

lemma publicLemma : (0 : Nat) = 0 := rfl

protected theorem protectedTheorem : (1 : Nat) = 1 := rfl

@[simp]
theorem attributedTheorem (value : Nat) : value + 0 = value := by simp

@[simp] theorem sameLineTheorem (value : Nat) : 0 + value = value := by simp

end FEP.Fin4GaussianCensusMutation

#print prefix FEP.Fin4GaussianCensusMutation
""",
        encoding="utf-8",
    )
    result = run_lean_compile_probe(
        probe,
        cwd=LEAN_ROOT,
        import_root=PROJECT_ROOT / "src" / "fep_lean" / "formal",
        timeout_s=300,
        executable=lake_executable(
            missing="raise",
            context="H2.5c native acceptance",
        ),
    )
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    escaped_declarations = frozenset(
        {
            "publicLemma",
            "protectedTheorem",
            "attributedTheorem",
            "sameLineTheorem",
        }
    )
    assert (
        _parse_namespace_declaration_names(output, "FEP.Fin4GaussianCensusMutation")
        == escaped_declarations
    )
    with pytest.raises(AssertionError) as rejected:
        _assert_exact_namespace_declarations(
            output, "FEP.Fin4GaussianCensusMutation", frozenset()
        )
    for name in escaped_declarations:
        assert name in str(rejected.value)


def test_h2_5c_owns_the_named_axis_in_the_preregistered_order() -> None:
    assert FOUNDATION.is_file()
    source = FOUNDATION.read_text(encoding="utf-8")

    assert tuple(re.findall(r"(?m)^import (\S+)$", source)) == EXACT_IMPORTS
    assert "namespace FEP.Fin4GaussianSemigroup\n" in source
    assert source.rstrip().endswith("end FEP.Fin4GaussianSemigroup")
    assert re.search(
        r"inductive Axis\n"
        r"  \| external\n"
        r"  \| sensory\n"
        r"  \| active\n"
        r"  \| internal\n",
        source,
    )
    assert "def axisFin : Axis ≃ Fin 4" in source
    assert "axisFin external = 0" in source
    assert "axisFin sensory = 1" in source
    assert "axisFin active = 2" in source
    assert "axisFin internal = 3" in source
    assert "abbrev StandardizedState :=" in source
    assert "EuclideanSpace ℝ Axis" in source
    assert "Fin4Axis" not in source


def test_h2_5c_is_manifested_and_projected_as_one_foundation() -> None:
    modules = tuple(
        module
        for module in FORMAL_MODULES
        if module.resource == "fin4_gaussian_semigroup.lean"
    )

    assert len(modules) == 1
    assert modules[0].lean_module == "FepSketches.fin4_gaussian_semigroup"
    assert modules[0].role is FormalModuleRole.FOUNDATION
    assert modules[0].declaration_namespace == "FEP.Fin4GaussianSemigroup"

    projection_pairs = dict(formal_projection_pairs(PROJECT_ROOT))
    projection = PROJECT_ROOT / "lean" / "FepSketches" / modules[0].resource
    assert projection_pairs[FOUNDATION] == projection
    assert projection.read_bytes() == FOUNDATION.read_bytes()


def test_h2_5c_derives_the_exact_precision_and_covariance() -> None:
    source = lean_code_without_comments(FOUNDATION.read_text(encoding="utf-8"))

    assert "def K : Matrix Axis Axis ℝ" in source
    for literal in (
        "| external, external => 4",
        "| external, sensory => -1",
        "| external, active => -1",
        "| external, internal => 0",
        "| sensory, external => -1",
        "| sensory, sensory => 4",
        "| sensory, active => 0",
        "| sensory, internal => -1",
        "| active, external => -1",
        "| active, sensory => 0",
        "| active, active => 4",
        "| active, internal => -1",
        "| internal, external => 0",
        "| internal, sensory => -1",
        "| internal, active => -1",
        "| internal, internal => 4",
    ):
        assert literal in source
    assert re.search(
        r"noncomputable def Sigma : Matrix Axis Axis ℝ :=\n  K⁻¹",
        source,
    )
    assert "theorem K_isSymm" in source
    assert "theorem K_posDef" in source
    assert "theorem Sigma_eq_entries" in source
    assert "theorem K_mul_Sigma : K * Sigma = 1" in source
    assert "theorem Sigma_mul_K : Sigma * K = 1" in source
    assert "theorem Sigma_posDef : Sigma.PosDef" in source
    assert "theorem K_external_internal : K external internal = 0" in source
    assert (
        "theorem Sigma_external_internal : Sigma external internal = 1 / 24" in source
    )
    assert "theorem Sigma_external_internal_ne_zero" in source
    assert "Matrix.PosDef.of_dotProduct_mulVec_pos" in source

    identity = tuple(
        tuple(Fraction(row == column) for column in range(4)) for row in range(4)
    )
    assert _matmul(K_STAR, SIGMA_STAR) == identity
    assert _matmul(SIGMA_STAR, K_STAR) == identity
    assert tuple(
        _determinant(tuple(row[:size] for row in K_STAR[:size])) for size in range(1, 5)
    ) == (Fraction(4), Fraction(15), Fraction(56), Fraction(192))
    assert K_STAR[0][3] == 0
    assert SIGMA_STAR[0][3] == Fraction(1, 24)


def test_h2_5c_proves_four_nonvacuous_independent_eigenmodes() -> None:
    source = lean_code_without_comments(FOUNDATION.read_text(encoding="utf-8"))

    for name in (
        "eigenmodeTwo",
        "eigenmodeFourExternal",
        "eigenmodeFourSensory",
        "eigenmodeSix",
    ):
        assert f"def {name} : Axis → ℝ" in source
    assert "theorem K_eigenmode_two" in source
    assert "K *ᵥ eigenmodeTwo = 2 • eigenmodeTwo" in source
    assert "theorem K_eigenmode_four_external" in source
    assert "K *ᵥ eigenmodeFourExternal = 4 • eigenmodeFourExternal" in source
    assert "theorem K_eigenmode_four_sensory" in source
    assert "K *ᵥ eigenmodeFourSensory = 4 • eigenmodeFourSensory" in source
    assert "theorem K_eigenmode_six" in source
    assert "K *ᵥ eigenmodeSix = 6 • eigenmodeSix" in source
    assert "theorem eigenmodes_nonzero" in source
    assert "theorem eigenmodes_independent" in source

    modes = (
        ((Fraction(1), Fraction(1), Fraction(1), Fraction(1)), Fraction(2)),
        ((Fraction(1), Fraction(0), Fraction(0), Fraction(-1)), Fraction(4)),
        ((Fraction(0), Fraction(1), Fraction(-1), Fraction(0)), Fraction(4)),
        ((Fraction(1), Fraction(-1), Fraction(-1), Fraction(1)), Fraction(6)),
    )
    for vector, eigenvalue in modes:
        assert vector != (Fraction(0),) * 4
        assert _matvec(K_STAR, vector) == tuple(eigenvalue * x for x in vector)
    mode_matrix = tuple(tuple(mode[0][row] for mode in modes) for row in range(4))
    assert _determinant(mode_matrix) != 0


def test_h2_5c_specializes_the_accepted_linear_gaussian_owner() -> None:
    source = lean_code_without_comments(FOUNDATION.read_text(encoding="utf-8"))

    assert "noncomputable def parameters (center : StandardizedState)" in source
    assert "FEP.LinearGaussianSemigroup.LinearGaussianParameters Axis" in source
    assert "precision := K" in source
    assert "precision_posDef := K_posDef" in source
    assert "center := center" in source
    assert "theorem parameters_covariance" in source
    assert "(parameters center).covariance = Sigma" in source
    assert "noncomputable def transition" in source
    assert "(parameters center).transition time" in source
    assert "noncomputable def nativeSemigroup" in source
    assert "kernel_zero := transition_zero center" in source
    assert "kernel_add := transition_add center" in source
    assert "noncomputable def stationaryLaw" in source
    assert "(parameters center).stationaryLaw" in source
    assert "stationaryLaw center = multivariateGaussian center Sigma" in source
    assert "noncomputable def transitionProbability" in source
    assert "noncomputable def stationaryProbability" in source

    for theorem in (
        "transitionCovariance_posDef",
        "transition_apply",
        "transition_univ",
        "transition_zero",
        "transition_add",
        "stationaryLaw_eq_gaussian",
        "stationaryLaw_invariant",
        "transition_mean",
        "transition_covariance",
        "transitionProbability_tendsto_invariant",
        "integral_transition_tendsto_invariant",
    ):
        assert f"theorem {theorem}" in source
    assert "NormedSpace.exp ((-(time : ℝ)) • K)" in source
    assert "Sigma -" in source
    assert "multivariateGaussian" in source
    assert "transition center (left + right) =" in source
    assert "transition center right ∘ₖ transition center left" in source
    assert "FEP.MarkovSemigroup.InvariantLaw" in source
    assert "ProbabilityMeasure" in source
    assert "Tendsto" in source

    assert "Kernel.compProd" not in source
    assert ".bind" not in source


def test_h2_5c_projects_the_normalized_all_ones_mode_to_h2_5a() -> None:
    source = lean_code_without_comments(FOUNDATION.read_text(encoding="utf-8"))

    assert "noncomputable def normalizedAllOnes : StandardizedState" in source
    assert "WithLp.toLp 2 (fun _ => (1 / 2 : ℝ))" in source
    assert "noncomputable def allOnesProjection : StandardizedState →L[ℝ] ℝ" in source
    assert "innerSL ℝ normalizedAllOnes" in source
    assert "noncomputable def allOnesEmbedding : ℝ →L[ℝ] StandardizedState" in source
    assert "ContinuousLinearMap.toSpanSingleton ℝ normalizedAllOnes" in source
    assert "theorem normalizedAllOnes_unit" in source
    assert "⟪normalizedAllOnes, normalizedAllOnes⟫ = 1" in source
    assert "theorem allOnesProjection_embedding" in source
    assert "allOnesProjection (allOnesEmbedding value) = value" in source
    assert "theorem allOnes_projection_nontrivial" in source
    assert "allOnesProjection normalizedAllOnes = 1" in source

    assert "theorem K_normalizedAllOnes" in source
    assert "K *ᵥ normalizedAllOnes = 2 • normalizedAllOnes" in source
    assert "theorem Sigma_normalizedAllOnes" in source
    assert "Sigma *ᵥ normalizedAllOnes = (1 / 2 : ℝ) • normalizedAllOnes" in source
    assert "theorem evolution_normalizedAllOnes" in source
    assert "NormedSpace.exp ((-(time : ℝ)) • K) *ᵥ normalizedAllOnes" in source
    assert "Real.exp (-2 * (time : ℝ)) • normalizedAllOnes" in source

    assert "noncomputable def scalarParameters (center : ℝ)" in source
    assert re.search(
        r"finOneScalarParameters 2\s+\(by norm_num\) center",
        source,
    )
    assert "theorem scalarParameters_exact" in source
    assert "(scalarParameters center).rate = 2" in source
    assert "(scalarParameters center).diffusionVarianceRate = 2" in source
    assert "noncomputable def projectedTransition" in source
    assert "Kernel.comap (transition (allOnesEmbedding center) time)" in source
    assert "Kernel.map" in source
    assert "theorem projectedTransition_eq_scalarOU" in source
    assert "projectedTransition center time =" in source
    assert "(scalarParameters center).ouTransition time" in source

    normalized = (Fraction(1, 2),) * 4
    assert sum(value * value for value in normalized) == 1
    assert _matvec(K_STAR, normalized) == tuple(2 * value for value in normalized)
    assert _matvec(SIGMA_STAR, normalized) == tuple(
        Fraction(1, 2) * value for value in normalized
    )


def test_h2_5c_public_surface_is_exact_nonvacuous_and_fail_closed() -> None:
    source = lean_code_without_comments(FOUNDATION.read_text(encoding="utf-8"))

    assert len(PUBLIC_DEFINITIONS) == 18
    assert len(PUBLIC_THEOREMS) == 42
    assert "theorem axis_cardinality : Fintype.card Axis = 4" in source
    assert "theorem axis_pairwise_ne" in source
    assert "external ≠ sensory" in source
    assert "external ≠ internal" in source
    assert "active ≠ internal" in source
    assert "theorem Sigma_isSymm : Sigma.IsSymm" in source
    assert "theorem transitionCovariance_posSemidef" in source

    assert not re.search(
        r"\b(?:sorry|admit|axiom|opaque)\b|unsafe\s+(?:def|theorem)|:\s*True\b",
        source,
    )
    assert not re.search(
        r"\b(?:SDE|Ito|Itô|FokkerPlanck|Brownian|generator|Generator|"
        r"reversible|Reversible|detailedBalance|conditioning|"
        r"conditionalIndependence|PrecisionCI|H3Eligibility)\b",
        source,
    )
    assert not re.search(r"\b(?:Fin4Axis|Fin4State)\b", source)
    assert not re.search(r"(?:K|Sigma)\s*:=.*?Fin\s+4", source, re.DOTALL)
    assert not re.search(r"structure\s+\w*(?:Certificate|Witness)", source)


def test_h2_5c_compiles_warning_free() -> None:
    with tempfile.TemporaryDirectory(prefix="fep-h2-5c-") as output_dir:
        output_path = Path(output_dir) / "fin4_gaussian_semigroup.olean"
        result = run_lean_compile_probe(
            FOUNDATION,
            cwd=LEAN_ROOT,
            import_root=PROJECT_ROOT / "src" / "fep_lean" / "formal",
            output_path=output_path,
            timeout_s=300,
            executable=lake_executable(
                missing="raise",
                context="H2.5c native acceptance",
            ),
        )
        assert output_path.is_file(), result.stdout + result.stderr

    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "warning:" not in output.lower()


def test_h2_5c_public_surface_axioms_and_terminal_export(tmp_path: Path) -> None:
    probe = tmp_path / "Fin4GaussianSemigroupAxioms.lean"
    source = FOUNDATION.read_text(encoding="utf-8")
    prints = "\n".join(
        f"#print axioms FEP.Fin4GaussianSemigroup.{name}" for name in PUBLIC_THEOREMS
    )
    consumers = f"""
open Filter MeasureTheory ProbabilityTheory
open scoped ProbabilityTheory Topology
open FEP.Fin4GaussianSemigroup
open FEP.Fin4GaussianSemigroup.Axis

example :
    axisFin external = 0 ∧ axisFin sensory = 1 ∧
      axisFin active = 2 ∧ axisFin internal = 3 :=
  axisFin_order

example (center : StandardizedState) (left right : ℝ≥0) :
    transition center (left + right) =
      transition center right ∘ₖ transition center left :=
  (nativeSemigroup center).kernel_add left right

example (center : ℝ) (time : ℝ≥0) :
    projectedTransition center time =
      (scalarParameters center).ouTransition time :=
  projectedTransition_eq_scalarOU center time

example (center : StandardizedState) :
    stationaryLaw center =
      multivariateGaussian center FEP.Fin4GaussianSemigroup.Sigma :=
  stationaryLaw_eq_gaussian center

example :
    K * FEP.Fin4GaussianSemigroup.Sigma = 1 ∧
      FEP.Fin4GaussianSemigroup.Sigma * K = 1 ∧
      K external internal = 0 ∧
      FEP.Fin4GaussianSemigroup.Sigma external internal = 1 / 24 ∧
      FEP.Fin4GaussianSemigroup.Sigma external internal ≠ 0 :=
  ⟨K_mul_Sigma, Sigma_mul_K, K_external_internal,
    Sigma_external_internal, Sigma_external_internal_ne_zero⟩

example :
{EXACT_FIN4_CARRIER_PROPOSITION} :=
  exactFin4Carrier
"""
    probe.write_text(
        f"{source}\n{prints}\n#print prefix FEP.Fin4GaussianSemigroup\n{consumers}\n",
        encoding="utf-8",
    )
    result = run_lean_compile_probe(
        probe,
        cwd=LEAN_ROOT,
        import_root=PROJECT_ROOT / "src" / "fep_lean" / "formal",
        timeout_s=300,
        executable=lake_executable(
            missing="raise",
            context="H2.5c native acceptance",
        ),
    )

    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "sorryAx" not in output
    assert "warning:" not in output.lower()
    _assert_exact_namespace_declarations(
        output,
        "FEP.Fin4GaussianSemigroup",
        PUBLIC_ENVIRONMENT_DECLARATIONS,
    )
    reports_seen = 0
    for name in PUBLIC_THEOREMS:
        full_name = f"FEP.Fin4GaussianSemigroup.{name}"
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
            assert axioms <= ALLOWED_AXIOMS, (full_name, axioms)
    assert reports_seen == len(PUBLIC_THEOREMS) == 42
