"""Hard-cutover contracts for the modular catalogue body registry."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType, ModuleType
from typing import Final

import pytest
import yaml

from fep_lean.catalogue.generation import hoisted_sketch_imports, strip_sketch_imports
from fep_lean.catalogue.latex import build_theorem_latex, build_topic_latex_equations
from fep_lean.catalogue.registry import (
    BODIES,
    BODY_MODULE_MANIFEST,
    LATEX_EQUATIONS,
    THEOREM_LATEX,
    BodyModule,
    RegistryValidationError,
    build_body_registry,
    validate_body_family_ownership,
    validate_body_roster,
)
from fep_lean.catalogue.schema import load_catalogue_metadata
from fep_lean.catalogue.semantics import SemanticValidationError
from fep_lean.lean_source import (
    lean_code_without_comments,
    lean_declaration_conclusion,
)

PROJ = Path(__file__).resolve().parent.parent
BASELINE = (
    PROJ
    / "specs"
    / "done"
    / "formalism-catalogue-120"
    / "assets"
    / "slice-01-original-body-sha256.json"
)
EXPECTED_EXPANSION_TITLES = (
    "Likelihood-Ratio Reconstruction under Absolute Continuity",
    "Posterior Density as a Likelihood Tilt",
    "Kernel Bayesian-Inversion Reconstruction",
    "Bayes Involution for Finite Joint Laws",
    "Composite-Kernel Bayesian Inversion",
    "Standard-Borel Conditional-Kernel Reconstruction",
    "Conditional-Expectation Tower through a Kernel",
    "Finite Gibbs Variational Principle",
    "Finite Donsker–Varadhan Equality with a Full-Support Gibbs Optimizer",
    "Coordinate ELBO Decomposition",
    "Mean-Field Coordinate Free-Energy Optimum",
    "Fixed-Sample Importance-Weighted Jensen Bound",
    "Finite-Channel KL Data-Processing Inequality",
    "Rate–Distortion Lagrangian Weak Duality",
    "Controlled-Kernel Normalization",
    "Action-Conditioned Bayesian Belief Update",
    "Reachable Finite-Belief POMDP Reduction",
    "Soft Bellman Recursion",
    "KL-Control Desirability Recursion",
    "Control-as-Inference Policy Posterior",
    "Sophisticated Expected-Free-Energy Backward Induction",
    "Hidden-Markov Forward Filtering Recursion",
    "Backward Information-Message Recursion",
    "Forward–Backward Smoothing Factorization",
    "Smoothing-Marginal Normalization",
    "One-Step Normalized Variational State Update",
    "Two-Level Hierarchical Predictive Factorization",
    "Bayesian Model-Averaging Predictive Law",
    "Blanket Factorization and Conditional-Mutual-Information Equivalence",
    "Shared-Conditional Mixture Preservation",
    "Coupled-Subsystem Blanket Composition",
    "Finite Intervention-Kernel Normalization",
    "Non-Descendant Intervention Invariance",
    "Ordered Finite Causal Factorization",
    "Local Markov Property from Ordered Factorization",
    "Precision-Weighted Prediction-Error Energy",
    "Hierarchical Predictive-Coding Energy Decomposition",
    "Prediction-Error Gradient Identity",
    "Finite Generalized-Coordinate Shift Semigroup",
    "Finite-Jet Generalized-Filtering Correction Equation",
    "Precision Modulation of Prediction Error",
    "Quadratic Predictive-Coding Convergence",
    "Forward and Reverse Finite Path-Law Ratio",
    "Entropy Production as Path KL",
    "Detailed Fluctuation Symmetry",
    "Integral Fluctuation Theorem",
    "Finite Jarzynski Equality",
    "Local Detailed Balance and Current Cancellation",
    "Reversible-Chain One-Step KL Dissipation",
    "Categorical Fisher Positivity on Simplex Tangents",
    "Fisher Pullback under Reparameterization",
    "Unbiased Scalar Cramér–Rao Bound under Score Regularity",
    "Natural-Gradient Equivariance under an Invertible Full-Rank Chart",
    "Mirror-Descent Three-Point Identity",
    "Bregman Pythagorean Law for an Affine Information Projection",
    "Replicator–Natural-Gradient Equivalence",
    "Product-Agent Generative Law",
    "Additive Collective Variational Free Energy",
    "Independent-Agent Expected-Free-Energy Additivity",
    "Unit-Weight Product-of-Experts Pool Normalization",
    "Consensus Mass Conservation",
    "Contractive Belief-Consensus Convergence",
    "Coupled-Agent Potential Descent",
    "Sub-Gaussian Empirical-Mean Tail Bound",
    "Simultaneous Finite-Alphabet Frequency Bound",
    "Finite-Hypothesis PAC-Bayes Loss-Gap Bound",
    "Posterior-Odds Multiplicative Recursion",
    "Exponential Posterior Concentration from a Likelihood Gap",
    "Bayesian-Mixture Log-Loss Regret Bound",
    "Bayes-Factor Multiplicativity and Model-Evidence Update",
    "Laplace-Smoothing Error Identity",
    "Laplace-Smoothing Bias Bound",
    "Absolute-Error Transfer through Laplace Smoothing",
    "Squared-Risk Transfer through Laplace Smoothing",
    "Bernoulli Brier Excess-Risk Identity",
    "Finite-Law Laplace Brier-Risk Bound",
    "Concentration-Event Transfer through Smoothing",
    "Observation-Contingent Policy-Tree Recursion",
    "Finite Policy-Tree Bellman Minimum",
    "Optimal Finite Policy-Tree Existence",
    "Open-Loop Plan Embedding into Policy Trees",
    "Closed-Loop Policy-Tree Dominance over Open Loop",
    "Treewise Expected-Free-Energy Decomposition",
    "Strict Boolean Feedback Advantage",
    "Finite-Law Measure Embedding",
    "Finite-Law Embedding Injectivity and Expectation Transfer",
    "Embedded Finite-Kernel Composition",
    "Markov-Blanket Rectangle Factorization",
    "Native Markov-Blanket Conditional Independence",
    "Conditional Independence under Measurable Coarsening",
    "Native Blanket-Transition Closure",
    "Finite Exponential-Family Normalization and Support",
    "Affine Exponential-Family Log-Density Ratio",
    "Finite Log-Partition Gradient",
    "Centered Exponential-Family Score Identity",
    "Log-Partition Hessian–Variance–Fisher Identity",
    "Exponential-Family KL–Bregman Identity",
    "Natural-to-Mean Coordinate Injectivity",
    "Two-State Continuous-Time Markov Kernel",
    "Continuous-Time Identity at Zero",
    "Two-State Chapman–Kolmogorov Semigroup",
    "Two-State Continuous-Time Master Equation",
    "Continuous-Time Stationarity and Detailed Balance",
    "Exact Two-State Exponential Relaxation",
    "Exact Two-State Quadratic Lyapunov Decay",
)


def _module(name: str, bodies: dict[str, str]) -> ModuleType:
    module = ModuleType(name)
    module.__dict__["BODIES"] = bodies
    return module


def _body(topic_number: int, declarations: str) -> str:
    digits = f"{topic_number:03d}"
    return f"namespace FEP{digits}\n{declarations}\nend FEP{digits}\n"


def test_metadata_roster_seal_exactly_joins_modular_body_registry() -> None:
    """The metadata interval, rows, and body modules form one ordered roster."""
    metadata = load_catalogue_metadata(PROJ / "config" / "catalogue_metadata.yaml")

    assert metadata.schema_version == 2
    assert metadata.topic_ids == tuple(BODIES)
    assert tuple(record.id for record in metadata.records) == metadata.topic_ids
    assert metadata.roster.first_id == metadata.topic_ids[0]
    assert metadata.roster.last_id == metadata.topic_ids[-1]
    assert tuple(record.title for record in metadata.records[50:]) == (
        EXPECTED_EXPANSION_TITLES
    )
    assert (
        tuple(module.family for module in BODY_MODULE_MANIFEST)
        == metadata.families[: len(BODY_MODULE_MANIFEST)]
    )
    validate_body_family_ownership(
        {record.id: record.family for record in metadata.records}
    )


def test_registry_rejects_a_topic_body_owned_by_the_wrong_family_module() -> None:
    metadata = load_catalogue_metadata(PROJ / "config" / "catalogue_metadata.yaml")
    first = BODY_MODULE_MANIFEST[0]
    wrong_manifest = (
        BodyModule("not-the-metadata-family", first.module),
        *BODY_MODULE_MANIFEST[1:],
    )

    with pytest.raises(RegistryValidationError, match="family owner mismatch"):
        validate_body_family_ownership(
            {record.id: record.family for record in metadata.records},
            manifest=wrong_manifest,
        )


def test_historical_pre_cutover_body_ledger_remains_complete() -> None:
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    expected = baseline["topics"]

    assert tuple(expected) == tuple(f"fep-{index:03d}" for index in range(1, 51))
    assert all(
        isinstance(digest, str)
        and len(digest) == 64
        and set(digest) <= set("0123456789abcdef")
        for digest in expected.values()
    )
    assert tuple(BODIES)[: len(expected)] == tuple(expected)
    assert tuple(BODIES)[len(expected) :] == tuple(
        f"fep-{index:03d}" for index in range(51, 156)
    )


def test_registry_rejects_duplicate_topic_ids_across_modules() -> None:
    body = _body(1, "theorem fep001_ok : True := by trivial")
    modules = (
        BodyModule("one", _module("fixtures.one", {"fep-001": body})),
        BodyModule("two", _module("fixtures.two", {"fep-001": body})),
    )

    with pytest.raises(RegistryValidationError, match="duplicate topic ID"):
        build_body_registry(modules)


@pytest.mark.parametrize("topic_id", ["fep-1", "FEP-001", "fep-0001", "other-001"])
def test_registry_rejects_malformed_topic_ids(topic_id: str) -> None:
    module = BodyModule(
        "malformed",
        _module(
            "fixtures.malformed",
            {topic_id: _body(1, "theorem fep001_ok : True := by trivial")},
        ),
    )

    with pytest.raises(RegistryValidationError, match="malformed topic ID"):
        build_body_registry((module,))


def test_registry_rejects_wrong_namespace_and_duplicate_declarations() -> None:
    wrong_namespace = BodyModule(
        "namespace",
        _module(
            "fixtures.namespace",
            {
                "fep-002": _body(
                    1, "theorem fep002_wrong_namespace : True := by trivial"
                )
            },
        ),
    )
    duplicate_declaration = BodyModule(
        "declaration",
        _module(
            "fixtures.declaration",
            {
                "fep-001": _body(
                    1,
                    "theorem fep001_duplicate : True := by trivial\n"
                    "theorem fep001_duplicate : True := by trivial",
                )
            },
        ),
    )

    with pytest.raises(RegistryValidationError, match="namespaces must be exactly"):
        build_body_registry((wrong_namespace,))
    with pytest.raises(RegistryValidationError, match="duplicate declarations"):
        build_body_registry((duplicate_declaration,))


def test_registry_ignores_comment_and_string_only_lean_commands() -> None:
    valid = _body(
        1,
        "/- namespace Fake\n"
        "lemma fep001_commentOnly : True := by trivial\n"
        "end Fake -/\n"
        'def message := "theorem fep001_stringOnly : True"\n'
        "lemma fep001_live : True := by trivial",
    )
    registry = build_body_registry(
        (BodyModule("comments", _module("fixtures.comments", {"fep-001": valid})),)
    )
    equations = build_theorem_latex(registry)

    assert tuple(registry) == ("fep-001",)
    assert tuple(equations) == (("fep-001", "fep001_live"),)
    assert build_topic_latex_equations(registry, equations)["fep-001"] == [
        equations[("fep-001", "fep001_live")]
    ]

    comment_only = BodyModule(
        "comments",
        _module(
            "fixtures.comments_only",
            {
                "fep-001": (
                    "/- namespace FEP001\n"
                    "theorem fep001_commentOnly : True := by trivial\n"
                    "end FEP001 -/\n"
                )
            },
        ),
    )
    with pytest.raises(RegistryValidationError, match="namespaces must be exactly"):
        build_body_registry((comment_only,))


def test_theorem_latex_renders_lean_type_star_as_a_math_superscript() -> None:
    body = _body(
        1,
        "variable {α : Type*}\ntheorem fep001_identity (value : α) : α := value",
    )
    registry = build_body_registry(
        (BodyModule("type_star", _module("fixtures.type_star", {"fep-001": body})),)
    )

    equation = build_theorem_latex(registry)[("fep-001", "fep001_identity")]

    assert r"\mathsf{Type}^{*}" in equation
    assert r"\mathsf{Type}^\*" not in equation


def test_theorem_latex_normalizes_lean_unicode_to_portable_ascii() -> None:
    body = _body(
        1,
        "variable {Ω 𝓧 𝓒 : Type*} [MeasurableSpace Ω]\n"
        "theorem fep001_unicode\n"
        "    (κ η : Kernel Ω Ω) (μ ν : Measure Ω)\n"
        "    (observable : Ω → ℝ≥0∞) (hαhalf : True) :\n"
        "    ¬hαhalf ∧ ((κ ∘ₖ η)†μ =ᵐ[ν] κ) ∧ μ ≪ ν ∧\n"
        "      (∫⁻ x, observable x ∂μ) ≤ ∞ ∧\n"
        "      (μ ⊗ₘ κ) = (μ ⊗ₘ η) ∧ κ ⁻¹' Set.univ = Set.univ := by trivial",
    )
    registry = build_body_registry(
        (BodyModule("unicode", _module("fixtures.unicode", {"fep-001": body})),)
    )

    equation = build_theorem_latex(registry)[("fep-001", "fep001_unicode")]

    assert equation.isascii()
    assert r"\mathcal{X}" in equation
    assert r"\mathcal{C}" in equation
    assert r"\mathbb{R}_{\ge 0}^{\infty}" in equation
    assert r"\mathbin{\circ_{k}}" in equation
    assert r"^{\dagger}" in equation
    assert r"\overset{\mathrm{a.e.}}{=}" in equation
    assert r"\ll" in equation
    assert r"\int^{-}" in equation
    assert r"\,\mathrm{d}\," in equation
    assert r"\mathbin{\otimes_{m}}" in equation
    assert r"\infty" in equation
    assert r"h\alpha{}half" in equation
    assert r"\alphahalf" not in equation
    assert r"\neg{}h\alpha{}half" in equation
    assert r"\negh" not in equation
    assert r"\kappa{} ^{-1} \Omega" in equation.replace(" \\\\\n&", " ")
    assert r"^{-1}'" not in equation


def test_catalogue_latex_contains_no_unconverted_unicode() -> None:
    assert all(
        equation.isascii()
        for equations in LATEX_EQUATIONS.values()
        for equation in equations
    )


def _flatten_row_joins(equation: str) -> str:
    """Join wrapped LaTeX rows the way the rendering-contract pins expect."""
    return equation.replace(" \\\\\n&", "")


# Golden data pinning the theorem LaTeX rendering contract: each entry is the
# pinned topic's rendered theorem LaTeX with the row-join flattening applied
# exactly once, byte-identical to the previously inlined exact-string pins.
THEOREM_LATEX_GOLDEN: Final[Mapping[str, str]] = MappingProxyType(
    {
        "fep155_twoStateLyapunov_exact": _flatten_row_joins(
            THEOREM_LATEX[("fep-155", "fep155_twoStateLyapunov_exact")]
        ),
        "fep131_openLoopEmbedding_value": _flatten_row_joins(
            THEOREM_LATEX[("fep-131", "fep131_openLoopEmbedding_value")]
        ),
        "fep131_openLoopEmbedding_leaf": _flatten_row_joins(
            THEOREM_LATEX[("fep-131", "fep131_openLoopEmbedding_leaf")]
        ),
        "fep038_bernoulliMass_hasDerivAt": _flatten_row_joins(
            THEOREM_LATEX[("fep-038", "fep038_bernoulliMass_hasDerivAt")]
        ),
        "fep001_variationalUpperBound_eq_iff": _flatten_row_joins(
            THEOREM_LATEX[("fep-001", "fep001_variationalUpperBound_eq_iff")]
        ),
    }
)


def test_catalogue_latex_preserves_application_spacing_and_bounded_rows() -> None:
    from fep_lean.catalogue.registry import THEOREM_LATEX

    lyapunov = THEOREM_LATEX[("fep-155", "fep155_twoStateLyapunov_exact")]
    flattened = THEOREM_LATEX_GOLDEN["fep155_twoStateLyapunov_exact"]

    assert r"\mathsf{rates.lyapunov}\,\mathsf{initial}\,\mathsf{time}" in flattened, (
        "fep155_twoStateLyapunov_exact"
    )
    assert r"\mathsf{rates.rho}" in lyapunov, "fep155_twoStateLyapunov_exact"
    assert r"\mathsf{time} ^ 2" in lyapunov, "fep155_twoStateLyapunov_exact"
    assert r"\cdot" in lyapunov, "fep155_twoStateLyapunov_exact"
    assert max(len(line) for line in lyapunov.splitlines()) <= 140
    assert all(
        max(len(line) for line in equation.splitlines()) <= 280
        for equation in THEOREM_LATEX.values()
    )


def test_theorem_latex_keeps_named_arguments_inside_the_statement() -> None:
    from fep_lean.catalogue.registry import THEOREM_LATEX

    value = THEOREM_LATEX[("fep-131", "fep131_openLoopEmbedding_value")]
    flat_value = THEOREM_LATEX_GOLDEN["fep131_openLoopEmbedding_value"]
    flat_leaf = THEOREM_LATEX_GOLDEN["fep131_openLoopEmbedding_leaf"]

    assert r"\mathsf{Observation} := \mathsf{Observation}" in flat_value, (
        "fep131_openLoopEmbedding_value"
    )
    assert r"\mathsf{openLoopValue}\,\mathsf{model}" in value, (
        "fep131_openLoopEmbedding_value"
    )
    assert r"\mathsf{plan}\,\mathsf{belief}" in value, "fep131_openLoopEmbedding_value"
    assert r"\mathsf{depth} := 0" in flat_leaf, "fep131_openLoopEmbedding_leaf"
    assert r"\mathsf{PUnit.unit}" in flat_leaf, "fep131_openLoopEmbedding_leaf"
    assert r"P\mathsf{Unit}" not in flat_leaf, "fep131_openLoopEmbedding_leaf"
    assert r"\mathsf{OpenLoopPlan}\,\mathsf{Action}\,0" in flat_leaf, (
        "fep131_openLoopEmbedding_leaf"
    )
    assert r"\mathsf{PolicyTree}" in flat_leaf, "fep131_openLoopEmbedding_leaf"
    assert r"\mathsf{Action}" in flat_leaf, "fep131_openLoopEmbedding_leaf"
    assert r"\mathsf{Observation}\,0" in flat_leaf, "fep131_openLoopEmbedding_leaf"


def test_theorem_latex_does_not_rewrite_identifier_suffixes() -> None:
    from fep_lean.catalogue.registry import THEOREM_LATEX

    affine = THEOREM_LATEX[("fep-105", "fep105_affineProjection_minimizes")]
    measurable = THEOREM_LATEX[("fep-140", "fep140_condIndepFun_measurableImages")]

    assert r"\mathsf{affineSet}" in affine
    assert r"affine\mathsf{Set}" not in affine
    assert r"\mathsf{internalMeasurable}" in measurable
    assert r"internal\mathsf{Measurable}" not in measurable


def test_theorem_latex_spaces_applications_after_grouped_arguments() -> None:
    flattened = THEOREM_LATEX_GOLDEN["fep038_bernoulliMass_hasDerivAt"]

    assert r"b)\,p" in flattened, "fep038_bernoulliMass_hasDerivAt"


def test_theorem_latex_renders_lean_identifiers_and_ascii_lambdas_unambiguously() -> (
    None
):
    from fep_lean.catalogue.registry import THEOREM_LATEX

    derivative = THEOREM_LATEX[("fep-038", "fep038_bernoulliMass_hasDerivAt")]
    wildcard = THEOREM_LATEX[("fep-069", "fep069_zeroCost_unitDesirability")]
    flat_variational = THEOREM_LATEX_GOLDEN["fep001_variationalUpperBound_eq_iff"]
    flat_derivative = THEOREM_LATEX_GOLDEN["fep038_bernoulliMass_hasDerivAt"]

    assert r"\mathsf{fep001\_variationalUpperBound}" in flat_variational, (
        "fep001_variationalUpperBound_eq_iff"
    )
    assert r"[\mathsf{IsFiniteMeasure}\,\mathsf{posterior}]" in flat_variational, (
        "fep001_variationalUpperBound_eq_iff"
    )
    assert any(
        r"\lambda\,q \mapsto \mathsf{fep038\_bernoulliMass}" in line
        for line in derivative.splitlines()
    ), "fep038_bernoulliMass_hasDerivAt"
    assert r"\mapsto" in flat_derivative, "fep038_bernoulliMass_hasDerivAt"
    assert "=>" not in flat_derivative, "fep038_bernoulliMass_hasDerivAt"
    assert r"\lambda\,\mathord{\_} \mapsto" in wildcard, (
        "fep069_zeroCost_unitDesirability"
    )


def test_catalogue_latex_keeps_short_binders_as_visual_units() -> None:
    from fep_lean.catalogue.registry import THEOREM_LATEX

    response = THEOREM_LATEX[("fep-037", "fep037_response_eq")]

    assert any(r"(n : \mathbb{N})" in line for line in response.splitlines())


def test_catalogue_latex_never_strands_an_operator_at_a_row_end() -> None:
    from fep_lean.catalogue.registry import THEOREM_LATEX

    unsafe_endings = (" +", " -", " *", " /", " =", " <=", " >=", " <", " >")
    assert all(
        not line.removesuffix(r" \\").rstrip().endswith(unsafe_endings)
        for equation in THEOREM_LATEX.values()
        for line in equation.splitlines()
    )


def test_theorem_latex_rejects_unknown_unicode_with_sorted_codepoints() -> None:
    body = _body(
        1,
        "theorem fep001_unknownUnicode (value : ☃ ↝ ☃) : True := by trivial",
    )
    registry = build_body_registry(
        (
            BodyModule(
                "unknown_unicode",
                _module("fixtures.unknown_unicode", {"fep-001": body}),
            ),
        )
    )

    with pytest.raises(ValueError, match=r"U\+219D, U\+2603"):
        build_theorem_latex(registry)


def test_lean_source_normalization_is_offset_preserving_and_import_safe() -> None:
    body = (
        "/- outer\n"
        "  /- import Fake.Nested -/\n"
        "  theorem commented : True := by trivial\n"
        "-/\n"
        'def label := "import Fake.String"\n'
        "import Mathlib.Probability.Notation\n"
        "namespace FEP001\n"
        "lemma fep001_live : True := by trivial\n"
        "end FEP001\n"
    )
    normalized = lean_code_without_comments(body)

    assert len(normalized) == len(body)
    assert normalized.count("\n") == body.count("\n")
    assert "Fake.Nested" not in normalized
    assert "Fake.String" not in normalized
    assert hoisted_sketch_imports({"fep-001": body}) == (
        "import Mathlib.Probability.Notation",
    )
    stripped = strip_sketch_imports(body)
    assert "import Fake.Nested" in stripped
    assert '"import Fake.String"' in stripped
    assert "import Mathlib.Probability.Notation" not in stripped
    assert (
        lean_declaration_conclusion(
            "theorem paired (h : True ∧ True) : True := by trivial"
        )
        == "True"
    )


def test_body_roster_join_rejects_missing_extra_and_reordered_ids() -> None:
    roster = ("fep-001", "fep-002")
    body = _body(1, "theorem fep001_ok : True := by trivial")

    for bodies in (
        {"fep-001": body},
        {"fep-001": body, "fep-002": body, "fep-003": body},
        {"fep-002": body, "fep-001": body},
    ):
        with pytest.raises(RegistryValidationError, match="sealed roster"):
            validate_body_roster(bodies, roster)


@pytest.mark.parametrize("mutation", ["missing", "extra", "reordered", "malformed"])
def test_metadata_roster_seal_rejects_row_drift(tmp_path: Path, mutation: str) -> None:
    source = yaml.safe_load(
        (PROJ / "config" / "catalogue_metadata.yaml").read_text(encoding="utf-8")
    )
    if mutation == "missing":
        source["topics"].pop()
    elif mutation == "extra":
        source["topics"].append(dict(source["topics"][-1]))
    elif mutation == "reordered":
        source["topics"][0], source["topics"][1] = (
            source["topics"][1],
            source["topics"][0],
        )
    else:
        source["roster"]["last_id"] = "fep-50"
    path = tmp_path / "catalogue_metadata.yaml"
    path.write_text(yaml.safe_dump(source, sort_keys=False), encoding="utf-8")

    with pytest.raises(SemanticValidationError):
        load_catalogue_metadata(path)


def test_latex_registry_is_qualified_complete_and_fully_consumed() -> None:
    assert all(isinstance(key, tuple) and len(key) == 2 for key in THEOREM_LATEX)
    assert tuple(LATEX_EQUATIONS) == tuple(BODIES)
    assert sum(len(rows) for rows in LATEX_EQUATIONS.values()) == len(THEOREM_LATEX)
