"""Packaged cross-topic Lean has one owner and deterministic projections."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from fep_lean.formal import (
    FORMAL_MODULES,
    FormalModule,
    FormalModuleRole,
    formal_aggregate_drift,
    formal_projection_drift,
    formal_projection_pairs,
    formal_resource_manifest_drift,
    formal_resource_paths,
    render_formal_aggregate,
    write_formal_aggregate,
    write_formal_projections,
)
from fep_lean.formal import manifest as formal_manifest
from tests._support.h2_r0_custody import validate_h2_r0_custody
from tests._support.lake import lake_executable
from tests._support.lean_runner import run_lake_lean_probe, run_lean_probe

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_formal_module_accepts_safe_nested_resources_with_exact_module_path() -> None:
    module = FormalModule(
        resource="compositions/measure_variational.lean",
        lean_module="FepSketches.compositions.measure_variational",
        role=FormalModuleRole.COMPOSITION,
        declaration_namespace="FEPComposed",
    )

    assert module.resource == "compositions/measure_variational.lean"
    assert module.declaration_namespace == "FEPComposed"


@pytest.mark.parametrize(
    ("resource", "lean_module"),
    [
        ("../escape.lean", "FepSketches.escape"),
        ("/tmp/escape.lean", "FepSketches.escape"),
        ("compositions/family.lean", "FepSketches.wrong.family"),
    ],
)
def test_formal_module_rejects_unsafe_or_mismatched_resource_paths(
    resource: str, lean_module: str
) -> None:
    with pytest.raises(ValueError):
        FormalModule(
            resource=resource,
            lean_module=lean_module,
            role=FormalModuleRole.COMPOSITION,
            declaration_namespace="FEPComposed",
        )


@pytest.mark.parametrize(
    ("role", "declaration_namespace"),
    [
        (FormalModuleRole.FOUNDATION, None),
        (FormalModuleRole.COMPOSITION, "not a Lean namespace"),
        (FormalModuleRole.AGGREGATE, "FEPComposed"),
    ],
)
def test_formal_module_rejects_namespace_values_that_disagree_with_role(
    role: FormalModuleRole, declaration_namespace: str | None
) -> None:
    with pytest.raises(ValueError, match="declaration namespace"):
        FormalModule(
            resource="module.lean",
            lean_module="FepSketches.module",
            role=role,
            declaration_namespace=declaration_namespace,
        )


def test_formal_module_manifest_is_the_single_explicit_resource_roster() -> None:
    foundation_resources = (
        "finite_probability.lean",
        "finite_information.lean",
        "active_inference.lean",
        "markov_blanket.lean",
        "information_geometry.lean",
        "statistical_convergence.lean",
        "measure_bayes.lean",
        "variational_duality.lean",
        "controlled_markov.lean",
        "temporal_inference.lean",
        "finite_markov_dynamics.lean",
        "causal_dynamics.lean",
        "predictive_coding.lean",
        "ness_flow.lean",
        "path_thermodynamics.lean",
        "geometric_optimization.lean",
        "collective_inference.lean",
        "learning_theory.lean",
        "empirical_risk.lean",
        "policy_tree.lean",
        "native_blanket.lean",
        "exponential_family.lean",
        "gaussian_information_geometry.lean",
        "smooth_information_geometry.lean",
        "continuous_time_markov.lean",
        "markov_semigroup.lean",
        "scalar_gaussian_semigroup.lean",
        "linear_gaussian_semigroup.lean",
        "fin4_gaussian_semigroup.lean",
        "gaussian_precision_conditioning.lean",
        "decision_risk.lean",
        "finite_posterior_learning.lean",
        "posterior_convergence.lean",
        "gnn_document.lean",
        "gnn_denotation.lean",
        "gnn_denotation_continuous.lean",
        "gnn_render_statements.lean",
        "efe_policy_selection.lean",
        "perception_action_loop.lean",
        "bayesian_model_reduction.lean",
        "efe_time_scale_separation.lean",
        "helmholtz_ao_ness.lean",
        "geometric_mechanics.lean",
        "law_weighted_split.lean",
        "h3_reference_model.lean",
    )
    released_composition_resources = (
        "compositions/core.lean",
        "compositions/measure_variational.lean",
        "compositions/control_temporal.lean",
        "compositions/causal_predictive.lean",
        "compositions/thermo_geometry.lean",
        "compositions/collective_learning.lean",
        "compositions/risk_calibration.lean",
        "compositions/policy_trees.lean",
        "compositions/native_blanket_transfer.lean",
        "compositions/exponential_family.lean",
        "compositions/continuous_time.lean",
    )
    composition_resources = (
        *released_composition_resources,
        "compositions/finite_scientific_implications.lean",
        "compositions/finite_policy_action.lean",
        "compositions/finite_reference_agent.lean",
        "compositions/gaussian_filter.lean",
        "compositions/gaussian_control.lean",
        "compositions/gaussian_grid_path.lean",
        "compositions/smooth_reference_kernel.lean",
        "compositions/finite_kernel_category.lean",
        "compositions/efe_policy_selection.lean",
        "compositions/perception_action_loop.lean",
        "compositions/bayesian_model_reduction.lean",
        "compositions/efe_time_scale_separation.lean",
        "compositions/helmholtz_ao_ness.lean",
        "compositions/geometric_mechanics.lean",
        "compositions/h3_case_study.lean",
    )
    aggregate_resources = ("composed.lean",)
    resources = (
        *foundation_resources,
        *composition_resources,
        *aggregate_resources,
    )
    modules = tuple(
        "FepSketches." + resource.removesuffix(".lean").replace("/", ".")
        for resource in resources
    )
    assert tuple(module.resource for module in FORMAL_MODULES) == resources
    assert tuple(module.lean_module for module in FORMAL_MODULES) == modules
    assert tuple(module.declaration_namespace for module in FORMAL_MODULES) == (
        "FEP",
        "FEP.FiniteInformation",
        "FEP.ActiveInference",
        "FEP.MarkovBlanket",
        "FEP.InformationGeometry",
        "FEP.StatisticalConvergence",
        "FEP.MeasureBayes",
        "FEP.VariationalDuality",
        "FEP.ControlledMarkov",
        "FEP.TemporalInference",
        "FEP.FiniteMarkovDynamics",
        "FEP.CausalDynamics",
        "FEP.PredictiveCoding",
        "FEP.NessFlow",
        "FEP.PathThermodynamics",
        "FEP.GeometricOptimization",
        "FEP.CollectiveInference",
        "FEP.LearningTheory",
        "FEP.EmpiricalRisk",
        "FEP.PolicyTrees",
        "FEP.NativeBlanket",
        "FEP.ExponentialFamily",
        "FEP.GaussianInformationGeometry",
        "FEP.SmoothInformationGeometry",
        "FEP.ContinuousTimeMarkov",
        "FEP.MarkovSemigroup",
        "FEP.ScalarGaussianSemigroup",
        "FEP.LinearGaussianSemigroup",
        "FEP.Fin4GaussianSemigroup",
        "FEP.GaussianPrecisionConditioning",
        "FEP.DecisionRisk",
        "FEP.FinitePosteriorLearning",
        "FEP.PosteriorConvergence",
        "FEP.GnnDocument",
        "FEP.GnnDenotation",
        "FEP.GnnContinuous",
        "FEP.GnnRenderStatements",
        "FEP.EFEPolicy",
        "FEP.PerceptionActionLoop",
        "FEP.BayesianModelReduction",
        "FEP.TimeScaleEFE",
        "FEP.HelmholtzAoNess",
        "FEP.GeometricMechanics",
        "FEP.LawWeightedSplit",
        "FEP.H3ReferenceModel",
        *("FEPComposed",) * len(released_composition_resources),
        "FEPComposed.FiniteScientificImplications",
        "FEPComposed.FinitePolicyAction",
        "FEPComposed.FiniteReferenceAgent",
        "FEPComposed.GaussianFilter",
        "FEPComposed.GaussianControl",
        "FEPComposed.GaussianGridPath",
        "FEPComposed.SmoothReferenceKernel",
        "FEPComposed.FiniteKernelCategory",
        "FEPComposed",
        "FEPComposed",
        "FEPComposed",
        "FEPComposed",
        "FEPComposed",
        "FEPComposed",
        "FEPComposed.H3CaseStudy",
        None,
    )
    expected_resources_by_role = {
        FormalModuleRole.FOUNDATION: foundation_resources,
        FormalModuleRole.COMPOSITION: composition_resources,
        FormalModuleRole.AGGREGATE: aggregate_resources,
    }
    assert {
        role: tuple(module.resource for module in FORMAL_MODULES if module.role is role)
        for role in FormalModuleRole
    } == expected_resources_by_role
    assert formal_resource_paths() == tuple(
        PROJECT_ROOT / "src" / "fep_lean" / "formal" / resource
        for resource in resources
    )
    assert formal_resource_paths(project_root=PROJECT_ROOT) == tuple(
        PROJECT_ROOT / "src" / "fep_lean" / "formal" / resource
        for resource in resources
    )


def test_checkout_resource_origin_is_explicit_and_not_site_package_derived(
    tmp_path: Path,
) -> None:
    assert formal_resource_paths(project_root=tmp_path) == tuple(
        tmp_path / "src" / "fep_lean" / "formal" / module.resource
        for module in FORMAL_MODULES
    )


def test_formal_resource_manifest_rejects_missing_and_unlisted_lean_files(
    tmp_path: Path,
) -> None:
    formal_root = tmp_path / "src" / "fep_lean" / "formal"
    for module in FORMAL_MODULES:
        path = formal_root / module.resource
        path.parent.mkdir(parents=True, exist_ok=True)
        namespace = module.declaration_namespace
        source = (
            "/- declaration-free aggregate -/\n"
            if namespace is None
            else f"namespace {namespace}\nend {namespace}\n"
        )
        path.write_text(source, encoding="utf-8")

    rogue = formal_root / "unmanifested.lean"
    rogue.write_text("theorem escapedAudit : True := by trivial\n", encoding="utf-8")
    assert formal_resource_manifest_drift(tmp_path) == (rogue,)

    rogue.unlink()
    missing = formal_root / FORMAL_MODULES[0].resource
    missing.unlink()
    assert formal_resource_manifest_drift(tmp_path) == (missing,)


def test_formal_resource_manifest_validates_comment_stripped_namespace_owner(
    tmp_path: Path,
) -> None:
    formal_root = tmp_path / "src" / "fep_lean" / "formal"
    for module in FORMAL_MODULES:
        path = formal_root / module.resource
        path.parent.mkdir(parents=True, exist_ok=True)
        if module.declaration_namespace is None:
            path.write_text("/- declaration-free aggregate -/\n", encoding="utf-8")
        else:
            path.write_text(
                f"namespace {module.declaration_namespace}\n"
                "theorem fixture : True := by trivial\n"
                f"end {module.declaration_namespace}\n",
                encoding="utf-8",
            )

    assert formal_resource_manifest_drift(tmp_path) == ()
    target = formal_root / FORMAL_MODULES[0].resource
    target.write_text(
        f"/- namespace {FORMAL_MODULES[0].declaration_namespace} -/\n"
        "namespace Wrong.Owner\n"
        "theorem fixture : True := by trivial\n"
        "end Wrong.Owner\n",
        encoding="utf-8",
    )

    assert formal_resource_manifest_drift(tmp_path) == (target,)

    target.write_text(
        f"namespace {FORMAL_MODULES[0].declaration_namespace}\n"
        "namespace Nested\n"
        "theorem fixture : True := by trivial\n"
        "end Nested\n"
        f"end {FORMAL_MODULES[0].declaration_namespace}\n"
        "namespace Wrong.Owner\n"
        "theorem secondFixture : True := by trivial\n"
        "end Wrong.Owner\n",
        encoding="utf-8",
    )

    assert formal_resource_manifest_drift(tmp_path) == (target,)


def test_formal_manifest_rejects_duplicate_leaf_specific_namespace_owners(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    duplicate_namespace = "FEPComposed.FiniteReferenceAgent"
    monkeypatch.setattr(
        formal_manifest,
        "FORMAL_MODULES",
        (
            FormalModule(
                resource="compositions/first.lean",
                lean_module="FepSketches.compositions.first",
                role=FormalModuleRole.COMPOSITION,
                declaration_namespace=duplicate_namespace,
            ),
            FormalModule(
                resource="compositions/second.lean",
                lean_module="FepSketches.compositions.second",
                role=FormalModuleRole.COMPOSITION,
                declaration_namespace=duplicate_namespace,
            ),
        ),
    )

    with pytest.raises(ValueError, match="duplicate declaration namespaces"):
        formal_manifest.formal_module_imports()


def test_formal_manifest_rejects_new_owner_of_released_shared_namespace(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        formal_manifest,
        "FORMAL_MODULES",
        (
            FormalModule(
                resource="compositions/future.lean",
                lean_module="FepSketches.compositions.future",
                role=FormalModuleRole.COMPOSITION,
                declaration_namespace="FEPComposed",
            ),
        ),
    )

    with pytest.raises(ValueError, match="released compatibility namespace"):
        formal_manifest.formal_resource_manifest_drift(tmp_path)


def test_core_composition_leaf_names_cross_topic_witnesses() -> None:
    source, projection = next(
        pair
        for module, pair in zip(
            FORMAL_MODULES,
            formal_projection_pairs(PROJECT_ROOT),
            strict=True,
        )
        if module.resource == "compositions/core.lean"
    )
    text = source.read_text(encoding="utf-8")
    assert "theorem fep002_vfe_compProd_chain_rule" in text
    assert "theorem fep031_zeroBeta_binary_maxEntropy" in text
    assert "theorem fep034_filter_is_fep017_posterior" in text
    assert "theorem fep027_priorPredictive_is_fep019" in text
    assert "theorem fep022_predictive_is_hierarchical_marginal" in text
    assert "theorem fep036_empiricalPosterior_closed" in text
    assert "theorem fep038_fisherRao_separation" in text
    assert "theorem fep041_informationGain_is_fep014_kl" in text
    assert "theorem fep025_current_dissipation_nonneg" in text
    assert "theorem fep037_autocorrelation_tracks_fep020" in text
    assert "theorem fep021_informationGain_balance" in text
    assert "theorem fep003_pragmaticCost_efe_balance" in text
    assert "theorem fep024_regularizer_is_fep014_kl" in text
    assert "zero inverse temperature" in text
    assert "zero temperature" not in text.lower()
    assert "sorry" not in text
    assert projection == (
        PROJECT_ROOT / "lean" / "FepSketches" / "compositions" / "core.lean"
    )


def test_formal_projection_writer_and_drift_are_byte_exact(tmp_path: Path) -> None:
    assert formal_projection_drift(tmp_path)
    for module in FORMAL_MODULES:
        canonical = tmp_path / "src" / "fep_lean" / "formal" / module.resource
        canonical.parent.mkdir(parents=True, exist_ok=True)
        canonical.write_bytes(
            (
                PROJECT_ROOT / "src" / "fep_lean" / "formal" / module.resource
            ).read_bytes()
        )
    written = write_formal_projections(tmp_path)
    assert written == tuple(
        tmp_path / "lean" / "FepSketches" / module.resource for module in FORMAL_MODULES
    )
    assert formal_projection_drift(tmp_path) == ()

    canonical = tmp_path / "src" / "fep_lean" / "formal" / FORMAL_MODULES[0].resource
    original = canonical.read_bytes()
    canonical.write_text(
        "namespace Wrong.Owner\nend Wrong.Owner\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="formal resource manifest is incomplete"):
        write_formal_projections(tmp_path)
    assert canonical in formal_projection_drift(tmp_path)
    canonical.write_bytes(original)
    assert formal_projection_drift(tmp_path) == ()

    written[0].write_text("tampered\n", encoding="utf-8")
    assert formal_projection_drift(tmp_path) == (written[0],)


def test_public_composition_aggregate_is_manifest_generated(tmp_path: Path) -> None:
    aggregate = tmp_path / "src" / "fep_lean" / "formal" / "composed.lean"
    assert formal_aggregate_drift(tmp_path) == (aggregate,)
    assert write_formal_aggregate(tmp_path) == aggregate
    assert aggregate.read_text(encoding="utf-8") == render_formal_aggregate()
    assert "theorem " not in aggregate.read_text(encoding="utf-8")
    assert formal_aggregate_drift(tmp_path) == ()

    aggregate.write_text("import FepSketches.compositions.core\n", encoding="utf-8")
    assert formal_aggregate_drift(tmp_path) == (aggregate,)


def test_checkout_formal_projection_is_current() -> None:
    assert formal_aggregate_drift(PROJECT_ROOT) == ()
    assert formal_projection_drift(PROJECT_ROOT) == ()


def test_category_roster_growth_is_rejected_by_historical_custody() -> None:
    # A current category resource cannot be presented as unchanged H2/H3 history.
    # Keep this refusal when separately reviewing a prospective successor epoch.
    with pytest.raises(
        ValueError,
        match="H3 owner subtraction does not recover the historical custody manifest",
    ):
        validate_h2_r0_custody(PROJECT_ROOT)


@pytest.mark.serial_lean
def test_finite_kernel_category_public_consumer_and_axioms(tmp_path: Path) -> None:
    namespace = "FEPComposed.FiniteKernelCategory"
    targets = (
        "finiteKernelCategory",
        "finKernCat_id_comp",
        "finKernCat_comp_id",
        "finKernCat_assoc",
        "predictiveFunctor",
        "bool_predictive_identity",
        "bool_flip_true",
        "bool_flip_false",
        "bool_predictive_composition",
        "bool_predictive_flip_twice",
    )
    consumer = tmp_path / "FiniteKernelCategoryConsumer.lean"
    consumer.write_text(
        """module
public import FepSketches.compositions.finite_kernel_category

@[expose] public section

open CategoryTheory FEP FEPComposed.FiniteKernelCategory

example (X Y : FinKernCat) (kernel : FiniteKernel X.α Y.α) : X ⟶ Y := kernel

example (X Y : FinKernCat) (kernel : X ⟶ Y) : 𝟙 X ≫ kernel = kernel :=
  finKernCat_id_comp X Y kernel

example (X Y : FinKernCat) (kernel : X ⟶ Y) : kernel ≫ 𝟙 Y = kernel :=
  finKernCat_comp_id X Y kernel

example (W X Y Z : FinKernCat) (f : W ⟶ X) (g : X ⟶ Y) (h : Y ⟶ Z) :
    (f ≫ g) ≫ h = f ≫ (g ≫ h) :=
  finKernCat_assoc W X Y Z f g h

example : predictiveFunctor.obj boolObject = FiniteLaw Bool := rfl

example (X Y : FinKernCat) (kernel : X ⟶ Y) (prior : FiniteLaw X.α) :
    predictiveFunctor.map kernel prior = FiniteKernel.predictive prior kernel := rfl

example : predictiveFunctor.map (𝟙 boolObject) (FiniteLaw.pointMass true) =
    FiniteLaw.pointMass true := bool_predictive_identity

example : predictiveFunctor.map boolFlip (FiniteLaw.pointMass true) =
    FiniteLaw.pointMass false := bool_flip_true

example : predictiveFunctor.map boolFlip (FiniteLaw.pointMass false) =
    FiniteLaw.pointMass true := bool_flip_false

example : predictiveFunctor.map (boolFlip ≫ boolFlip) (FiniteLaw.pointMass true) =
    predictiveFunctor.map boolFlip
      (predictiveFunctor.map boolFlip (FiniteLaw.pointMass true)) :=
  bool_predictive_composition

example : predictiveFunctor.map (boolFlip ≫ boolFlip) (FiniteLaw.pointMass true) =
    FiniteLaw.pointMass true := bool_predictive_flip_twice

"""
        + "\n".join(f"#print axioms {namespace}.{target}" for target in targets)
        + "\n",
        encoding="utf-8",
    )
    result = run_lean_probe(
        consumer,
        import_root=tmp_path,
        cwd=PROJECT_ROOT / "lean",
        timeout_s=300,
        executable=lake_executable(
            missing="raise", context="finite-kernel category acceptance"
        ),
    )
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "warning:" not in output.lower(), output
    for target in targets:
        reports = re.findall(
            rf"'{re.escape(namespace)}\.{target}' depends on axioms: \[(.*?)\]",
            output,
            re.DOTALL,
        )
        assert len(reports) == 1, (
            f"missing or duplicate axiom report: {target}\n{output}"
        )
        assert {name.strip() for name in reports[0].split(",")} == {
            "propext",
            "Classical.choice",
            "Quot.sound",
        }, f"unexpected axioms: {target}\n{output}"


@pytest.mark.serial_lean
def test_scalar_bridge_public_consumer_and_axioms(tmp_path: Path) -> None:
    source = (
        PROJECT_ROOT
        / "specs/comprehensive-next-steps/spikes/scalar-bridges-20261019/positive-consumer.lean"
    )
    probe = tmp_path / "ScalarBridgeConsumer.lean"
    probe.write_bytes(source.read_bytes())
    result = run_lean_probe(
        probe,
        import_root=tmp_path,
        cwd=PROJECT_ROOT / "lean",
        timeout_s=300,
        executable=lake_executable(missing="raise", context="scalar bridge acceptance"),
    )
    output = result.stdout + result.stderr
    assert result.returncode == 0 and "warning:" not in output.lower(), output
    reports = re.findall(r"depends on axioms: \[(.*?)\]", output, re.DOTALL)
    assert len(reports) == 9, output
    assert all(
        {a.strip() for a in report.split(",")}
        == {"propext", "Classical.choice", "Quot.sound"}
        for report in reports
    ), output


@pytest.mark.serial_lean
@pytest.mark.parametrize(
    "case", ["reject-zero-endpoint", "reject-omitted-energy-match"]
)
def test_scalar_bridge_imported_consumers_refuse_missing_premises(
    tmp_path: Path, case: str
) -> None:
    source = (
        PROJECT_ROOT
        / f"specs/comprehensive-next-steps/spikes/scalar-bridges-20261019/{case}.lean"
    )
    probe = tmp_path / "RejectedScalarConsumer.lean"
    probe.write_bytes(source.read_bytes())
    result = run_lean_probe(
        probe,
        import_root=tmp_path,
        cwd=PROJECT_ROOT / "lean",
        timeout_s=300,
        executable=lake_executable(
            missing="raise", context="scalar bridge refusal control"
        ),
    )
    output = result.stdout + result.stderr
    assert (
        result.returncode != 0
        and "error:" in output
        and "unknown" not in output.lower()
    ), output
    if case == "reject-zero-endpoint":
        assert "unsolved goals" in output and "⊢ False" in output, output
    else:
        assert (
            "projection" in output.lower()
            and "function" in output.lower()
            and "fep030_fep031_finite_maxEntropy" in output
        ), output


@pytest.mark.serial_lean
@pytest.mark.parametrize(
    ("case", "reports", "reject"),
    [
        ("fair-boolean-consumer", 11, False),
        ("native-nonzero-consumer", 3, False),
        ("endpoint-countermodels", 4, False),
        ("endpoint-positive-consumer", 4, False),
        ("helmholtz-positive-consumer", 5, False),
        ("helmholtz-zero-countermodel", 1, False),
        ("reject-fair-boolean-zero-multiplier", 0, True),
        ("reject-fisher-endpoint", 0, True),
        ("reject-zero-step", 0, True),
        ("reject-zero-temperature", 0, True),
        ("reject-negative-temperature", 0, True),
    ],
)
def test_exact_information_imported_consumers_and_boundary_controls(
    tmp_path: Path, case: str, reports: int, reject: bool
) -> None:
    source = (
        PROJECT_ROOT
        / "specs/comprehensive-next-steps/spikes/exact-information-20261020"
        / (case + ".lean")
    )
    probe = tmp_path / "ExactInformationConsumer.lean"
    probe.write_bytes(source.read_bytes())
    result = run_lean_probe(
        probe,
        import_root=tmp_path,
        cwd=PROJECT_ROOT / "lean",
        timeout_s=180,
        executable=lake_executable(
            missing="raise", context="exact information imported consumer"
        ),
    )
    output = result.stdout + result.stderr
    assert "warning:" not in output.lower() and "sorryAx" not in output, output
    axioms = re.findall(
        r"'([^']+)' depends on axioms:\s*\[([^]]*)\]", output, re.DOTALL
    )
    assert len(axioms) == reports and len({name for name, _ in axioms}) == reports, (
        output
    )
    assert all(
        {a.strip() for a in row.split(",")}
        == {"propext", "Classical.choice", "Quot.sound"}
        for _, row in axioms
    ), output
    if reject:
        assert result.returncode == 1 and output.count("error:") == 1, output
        assert (
            "unsolved goals" in output
            and "⊢ False" in output
            and "unknown" not in output.lower()
        ), output
    else:
        assert result.returncode == 0 and "error:" not in output, output


@pytest.mark.serial_lean
@pytest.mark.parametrize(
    ("case", "reports", "reject"),
    [
        ("CountLevelConsumers", 8, False),
        ("AvailableAPIs", 5, False),
        ("RejectZeroShape", 0, True),
    ],
)
def test_dirichlet_count_component_and_library_boundary(
    tmp_path: Path, case: str, reports: int, reject: bool
) -> None:
    source = (
        PROJECT_ROOT
        / "specs/comprehensive-next-steps/spikes/dirichlet-counts-20261020"
        / (case + ".lean")
    )
    probe = tmp_path / "DirichletCountConsumer.lean"
    probe.write_bytes(source.read_bytes())
    result = run_lake_lean_probe(
        ["env", "lean", "-E", "warning", "-R", str(tmp_path), str(probe)],
        cwd=PROJECT_ROOT / "lean",
        timeout_s=180,
        executable=lake_executable(
            missing="raise", context="count-learning and pinned-library acceptance"
        ),
    )
    output = result.stdout + result.stderr
    assert "warning:" not in output.lower() and "sorryAx" not in output, output
    axioms = re.findall(r"'([^']+)' depends on axioms:\s*\[([^]]*)\]", output)
    assert len(axioms) == reports and len({name for name, _ in axioms}) == reports, (
        output
    )
    assert all(
        {a.strip() for a in row.split(",")}
        == {"propext", "Classical.choice", "Quot.sound"}
        for _, row in axioms
    ), output
    if reject:
        assert result.returncode == 1 and output.count("error:") == 1, output
        assert (
            "unsolved goals" in output
            and "case hα" in output
            and "⊢ False" in output
            and "unknown" not in output.lower()
        ), output
    else:
        assert result.returncode == 0 and "error:" not in output, output
