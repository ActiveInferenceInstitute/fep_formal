"""Single explicit roster for maintained formal Lean resources."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path, PurePosixPath

from fep_lean.lean_source import is_lean_qualified_name, lean_outer_namespaces

_RELEASED_SHARED_DECLARATION_NAMESPACE = "FEPComposed"


class FormalModuleRole(str, Enum):
    """How a maintained Lean module participates in formal evidence."""

    FOUNDATION = "foundation"
    COMPOSITION = "composition"
    AGGREGATE = "aggregate"


@dataclass(frozen=True)
class FormalModule:
    """One packaged Lean resource and its declaration ownership."""

    resource: str
    lean_module: str
    role: FormalModuleRole
    declaration_namespace: str | None

    def __post_init__(self) -> None:
        resource = PurePosixPath(self.resource)
        if (
            not self.resource
            or "\\" in self.resource
            or resource.is_absolute()
            or resource.suffix != ".lean"
            or any(part in {"", ".", ".."} for part in resource.parts)
        ):
            raise ValueError(
                "formal resource must be a safe relative POSIX path ending in .lean: "
                f"{self.resource!r}"
            )
        expected_module = "FepSketches." + ".".join(resource.with_suffix("").parts)
        if self.lean_module != expected_module:
            raise ValueError(
                "formal Lean module must exactly match its resource path: "
                f"expected {expected_module!r}, got {self.lean_module!r}"
            )
        if self.role is FormalModuleRole.AGGREGATE:
            if self.declaration_namespace is not None:
                raise ValueError(
                    "aggregate formal module must not own a declaration namespace"
                )
        elif self.declaration_namespace is None or not is_lean_qualified_name(
            self.declaration_namespace
        ):
            raise ValueError(
                "foundation and composition modules require a qualified "
                f"declaration namespace: {self.declaration_namespace!r}"
            )


FORMAL_MODULES: tuple[FormalModule, ...] = (
    FormalModule(
        resource="finite_probability.lean",
        lean_module="FepSketches.finite_probability",
        role=FormalModuleRole.FOUNDATION,
        declaration_namespace="FEP",
    ),
    FormalModule(
        resource="finite_information.lean",
        lean_module="FepSketches.finite_information",
        role=FormalModuleRole.FOUNDATION,
        declaration_namespace="FEP.FiniteInformation",
    ),
    FormalModule(
        resource="active_inference.lean",
        lean_module="FepSketches.active_inference",
        role=FormalModuleRole.FOUNDATION,
        declaration_namespace="FEP.ActiveInference",
    ),
    FormalModule(
        resource="markov_blanket.lean",
        lean_module="FepSketches.markov_blanket",
        role=FormalModuleRole.FOUNDATION,
        declaration_namespace="FEP.MarkovBlanket",
    ),
    FormalModule(
        resource="information_geometry.lean",
        lean_module="FepSketches.information_geometry",
        role=FormalModuleRole.FOUNDATION,
        declaration_namespace="FEP.InformationGeometry",
    ),
    FormalModule(
        resource="statistical_convergence.lean",
        lean_module="FepSketches.statistical_convergence",
        role=FormalModuleRole.FOUNDATION,
        declaration_namespace="FEP.StatisticalConvergence",
    ),
    FormalModule(
        resource="measure_bayes.lean",
        lean_module="FepSketches.measure_bayes",
        role=FormalModuleRole.FOUNDATION,
        declaration_namespace="FEP.MeasureBayes",
    ),
    FormalModule(
        resource="variational_duality.lean",
        lean_module="FepSketches.variational_duality",
        role=FormalModuleRole.FOUNDATION,
        declaration_namespace="FEP.VariationalDuality",
    ),
    FormalModule(
        resource="controlled_markov.lean",
        lean_module="FepSketches.controlled_markov",
        role=FormalModuleRole.FOUNDATION,
        declaration_namespace="FEP.ControlledMarkov",
    ),
    FormalModule(
        resource="temporal_inference.lean",
        lean_module="FepSketches.temporal_inference",
        role=FormalModuleRole.FOUNDATION,
        declaration_namespace="FEP.TemporalInference",
    ),
    FormalModule(
        resource="finite_markov_dynamics.lean",
        lean_module="FepSketches.finite_markov_dynamics",
        role=FormalModuleRole.FOUNDATION,
        declaration_namespace="FEP.FiniteMarkovDynamics",
    ),
    FormalModule(
        resource="causal_dynamics.lean",
        lean_module="FepSketches.causal_dynamics",
        role=FormalModuleRole.FOUNDATION,
        declaration_namespace="FEP.CausalDynamics",
    ),
    FormalModule(
        resource="predictive_coding.lean",
        lean_module="FepSketches.predictive_coding",
        role=FormalModuleRole.FOUNDATION,
        declaration_namespace="FEP.PredictiveCoding",
    ),
    FormalModule(
        resource="ness_flow.lean",
        lean_module="FepSketches.ness_flow",
        role=FormalModuleRole.FOUNDATION,
        declaration_namespace="FEP.NessFlow",
    ),
    FormalModule(
        resource="path_thermodynamics.lean",
        lean_module="FepSketches.path_thermodynamics",
        role=FormalModuleRole.FOUNDATION,
        declaration_namespace="FEP.PathThermodynamics",
    ),
    FormalModule(
        resource="geometric_optimization.lean",
        lean_module="FepSketches.geometric_optimization",
        role=FormalModuleRole.FOUNDATION,
        declaration_namespace="FEP.GeometricOptimization",
    ),
    FormalModule(
        resource="collective_inference.lean",
        lean_module="FepSketches.collective_inference",
        role=FormalModuleRole.FOUNDATION,
        declaration_namespace="FEP.CollectiveInference",
    ),
    FormalModule(
        resource="learning_theory.lean",
        lean_module="FepSketches.learning_theory",
        role=FormalModuleRole.FOUNDATION,
        declaration_namespace="FEP.LearningTheory",
    ),
    FormalModule(
        resource="empirical_risk.lean",
        lean_module="FepSketches.empirical_risk",
        role=FormalModuleRole.FOUNDATION,
        declaration_namespace="FEP.EmpiricalRisk",
    ),
    FormalModule(
        resource="policy_tree.lean",
        lean_module="FepSketches.policy_tree",
        role=FormalModuleRole.FOUNDATION,
        declaration_namespace="FEP.PolicyTrees",
    ),
    FormalModule(
        resource="native_blanket.lean",
        lean_module="FepSketches.native_blanket",
        role=FormalModuleRole.FOUNDATION,
        declaration_namespace="FEP.NativeBlanket",
    ),
    FormalModule(
        resource="exponential_family.lean",
        lean_module="FepSketches.exponential_family",
        role=FormalModuleRole.FOUNDATION,
        declaration_namespace="FEP.ExponentialFamily",
    ),
    FormalModule(
        resource="gaussian_information_geometry.lean",
        lean_module="FepSketches.gaussian_information_geometry",
        role=FormalModuleRole.FOUNDATION,
        declaration_namespace="FEP.GaussianInformationGeometry",
    ),
    FormalModule(
        resource="smooth_information_geometry.lean",
        lean_module="FepSketches.smooth_information_geometry",
        role=FormalModuleRole.FOUNDATION,
        declaration_namespace="FEP.SmoothInformationGeometry",
    ),
    FormalModule(
        resource="continuous_time_markov.lean",
        lean_module="FepSketches.continuous_time_markov",
        role=FormalModuleRole.FOUNDATION,
        declaration_namespace="FEP.ContinuousTimeMarkov",
    ),
    FormalModule(
        resource="markov_semigroup.lean",
        lean_module="FepSketches.markov_semigroup",
        role=FormalModuleRole.FOUNDATION,
        declaration_namespace="FEP.MarkovSemigroup",
    ),
    FormalModule(
        resource="scalar_gaussian_semigroup.lean",
        lean_module="FepSketches.scalar_gaussian_semigroup",
        role=FormalModuleRole.FOUNDATION,
        declaration_namespace="FEP.ScalarGaussianSemigroup",
    ),
    FormalModule(
        resource="linear_gaussian_semigroup.lean",
        lean_module="FepSketches.linear_gaussian_semigroup",
        role=FormalModuleRole.FOUNDATION,
        declaration_namespace="FEP.LinearGaussianSemigroup",
    ),
    FormalModule(
        resource="fin4_gaussian_semigroup.lean",
        lean_module="FepSketches.fin4_gaussian_semigroup",
        role=FormalModuleRole.FOUNDATION,
        declaration_namespace="FEP.Fin4GaussianSemigroup",
    ),
    FormalModule(
        resource="gaussian_precision_conditioning.lean",
        lean_module="FepSketches.gaussian_precision_conditioning",
        role=FormalModuleRole.FOUNDATION,
        declaration_namespace="FEP.GaussianPrecisionConditioning",
    ),
    FormalModule(
        resource="decision_risk.lean",
        lean_module="FepSketches.decision_risk",
        role=FormalModuleRole.FOUNDATION,
        declaration_namespace="FEP.DecisionRisk",
    ),
    FormalModule(
        resource="finite_posterior_learning.lean",
        lean_module="FepSketches.finite_posterior_learning",
        role=FormalModuleRole.FOUNDATION,
        declaration_namespace="FEP.FinitePosteriorLearning",
    ),
    FormalModule(
        resource="posterior_convergence.lean",
        lean_module="FepSketches.posterior_convergence",
        role=FormalModuleRole.FOUNDATION,
        declaration_namespace="FEP.PosteriorConvergence",
    ),
    FormalModule(
        resource="gnn_document.lean",
        lean_module="FepSketches.gnn_document",
        role=FormalModuleRole.FOUNDATION,
        declaration_namespace="FEP.GnnDocument",
    ),
    FormalModule(
        resource="gnn_denotation.lean",
        lean_module="FepSketches.gnn_denotation",
        role=FormalModuleRole.FOUNDATION,
        declaration_namespace="FEP.GnnDenotation",
    ),
    FormalModule(
        resource="gnn_denotation_continuous.lean",
        lean_module="FepSketches.gnn_denotation_continuous",
        role=FormalModuleRole.FOUNDATION,
        declaration_namespace="FEP.GnnContinuous",
    ),
    FormalModule(
        resource="gnn_render_statements.lean",
        lean_module="FepSketches.gnn_render_statements",
        role=FormalModuleRole.FOUNDATION,
        declaration_namespace="FEP.GnnRenderStatements",
    ),
    FormalModule(
        resource="efe_policy_selection.lean",
        lean_module="FepSketches.efe_policy_selection",
        role=FormalModuleRole.FOUNDATION,
        declaration_namespace="FEP.EFEPolicy",
    ),
    FormalModule(
        resource="perception_action_loop.lean",
        lean_module="FepSketches.perception_action_loop",
        role=FormalModuleRole.FOUNDATION,
        declaration_namespace="FEP.PerceptionActionLoop",
    ),
    FormalModule(
        resource="bayesian_model_reduction.lean",
        lean_module="FepSketches.bayesian_model_reduction",
        role=FormalModuleRole.FOUNDATION,
        declaration_namespace="FEP.BayesianModelReduction",
    ),
    FormalModule(
        resource="efe_time_scale_separation.lean",
        lean_module="FepSketches.efe_time_scale_separation",
        role=FormalModuleRole.FOUNDATION,
        declaration_namespace="FEP.TimeScaleEFE",
    ),
    FormalModule(
        resource="compositions/core.lean",
        lean_module="FepSketches.compositions.core",
        role=FormalModuleRole.COMPOSITION,
        declaration_namespace="FEPComposed",
    ),
    FormalModule(
        resource="compositions/measure_variational.lean",
        lean_module="FepSketches.compositions.measure_variational",
        role=FormalModuleRole.COMPOSITION,
        declaration_namespace="FEPComposed",
    ),
    FormalModule(
        resource="compositions/control_temporal.lean",
        lean_module="FepSketches.compositions.control_temporal",
        role=FormalModuleRole.COMPOSITION,
        declaration_namespace="FEPComposed",
    ),
    FormalModule(
        resource="compositions/causal_predictive.lean",
        lean_module="FepSketches.compositions.causal_predictive",
        role=FormalModuleRole.COMPOSITION,
        declaration_namespace="FEPComposed",
    ),
    FormalModule(
        resource="compositions/thermo_geometry.lean",
        lean_module="FepSketches.compositions.thermo_geometry",
        role=FormalModuleRole.COMPOSITION,
        declaration_namespace="FEPComposed",
    ),
    FormalModule(
        resource="compositions/collective_learning.lean",
        lean_module="FepSketches.compositions.collective_learning",
        role=FormalModuleRole.COMPOSITION,
        declaration_namespace="FEPComposed",
    ),
    FormalModule(
        resource="compositions/risk_calibration.lean",
        lean_module="FepSketches.compositions.risk_calibration",
        role=FormalModuleRole.COMPOSITION,
        declaration_namespace="FEPComposed",
    ),
    FormalModule(
        resource="compositions/policy_trees.lean",
        lean_module="FepSketches.compositions.policy_trees",
        role=FormalModuleRole.COMPOSITION,
        declaration_namespace="FEPComposed",
    ),
    FormalModule(
        resource="compositions/native_blanket_transfer.lean",
        lean_module="FepSketches.compositions.native_blanket_transfer",
        role=FormalModuleRole.COMPOSITION,
        declaration_namespace="FEPComposed",
    ),
    FormalModule(
        resource="compositions/exponential_family.lean",
        lean_module="FepSketches.compositions.exponential_family",
        role=FormalModuleRole.COMPOSITION,
        declaration_namespace="FEPComposed",
    ),
    FormalModule(
        resource="compositions/continuous_time.lean",
        lean_module="FepSketches.compositions.continuous_time",
        role=FormalModuleRole.COMPOSITION,
        declaration_namespace="FEPComposed",
    ),
    FormalModule(
        resource="compositions/finite_scientific_implications.lean",
        lean_module="FepSketches.compositions.finite_scientific_implications",
        role=FormalModuleRole.COMPOSITION,
        declaration_namespace="FEPComposed.FiniteScientificImplications",
    ),
    FormalModule(
        resource="compositions/finite_policy_action.lean",
        lean_module="FepSketches.compositions.finite_policy_action",
        role=FormalModuleRole.COMPOSITION,
        declaration_namespace="FEPComposed.FinitePolicyAction",
    ),
    FormalModule(
        resource="compositions/finite_reference_agent.lean",
        lean_module="FepSketches.compositions.finite_reference_agent",
        role=FormalModuleRole.COMPOSITION,
        declaration_namespace="FEPComposed.FiniteReferenceAgent",
    ),
    FormalModule(
        resource="compositions/gaussian_filter.lean",
        lean_module="FepSketches.compositions.gaussian_filter",
        role=FormalModuleRole.COMPOSITION,
        declaration_namespace="FEPComposed.GaussianFilter",
    ),
    FormalModule(
        resource="compositions/gaussian_control.lean",
        lean_module="FepSketches.compositions.gaussian_control",
        role=FormalModuleRole.COMPOSITION,
        declaration_namespace="FEPComposed.GaussianControl",
    ),
    FormalModule(
        resource="compositions/gaussian_grid_path.lean",
        lean_module="FepSketches.compositions.gaussian_grid_path",
        role=FormalModuleRole.COMPOSITION,
        declaration_namespace="FEPComposed.GaussianGridPath",
    ),
    FormalModule(
        resource="compositions/smooth_reference_kernel.lean",
        lean_module="FepSketches.compositions.smooth_reference_kernel",
        role=FormalModuleRole.COMPOSITION,
        declaration_namespace="FEPComposed.SmoothReferenceKernel",
    ),
    FormalModule(
        resource="compositions/efe_policy_selection.lean",
        lean_module="FepSketches.compositions.efe_policy_selection",
        role=FormalModuleRole.COMPOSITION,
        declaration_namespace="FEPComposed",
    ),
    FormalModule(
        resource="compositions/perception_action_loop.lean",
        lean_module="FepSketches.compositions.perception_action_loop",
        role=FormalModuleRole.COMPOSITION,
        declaration_namespace="FEPComposed",
    ),
    FormalModule(
        resource="compositions/bayesian_model_reduction.lean",
        lean_module="FepSketches.compositions.bayesian_model_reduction",
        role=FormalModuleRole.COMPOSITION,
        declaration_namespace="FEPComposed",
    ),
    FormalModule(
        resource="compositions/efe_time_scale_separation.lean",
        lean_module="FepSketches.compositions.efe_time_scale_separation",
        role=FormalModuleRole.COMPOSITION,
        declaration_namespace="FEPComposed",
    ),
    FormalModule(
        resource="composed.lean",
        lean_module="FepSketches.composed",
        role=FormalModuleRole.AGGREGATE,
        declaration_namespace=None,
    ),
)

_RELEASED_SHARED_DECLARATION_NAMESPACE_RESOURCES = frozenset(
    module.resource
    for module in FORMAL_MODULES
    if module.role is FormalModuleRole.COMPOSITION
    and module.declaration_namespace == _RELEASED_SHARED_DECLARATION_NAMESPACE
)


def _selected(role: FormalModuleRole | None) -> tuple[FormalModule, ...]:
    modules = (
        FORMAL_MODULES
        if role is None
        else tuple(module for module in FORMAL_MODULES if module.role is role)
    )
    resources = tuple(module.resource for module in modules)
    lean_modules = tuple(module.lean_module for module in modules)
    unauthorized_shared_namespace_owners = tuple(
        module.resource
        for module in modules
        if module.declaration_namespace == _RELEASED_SHARED_DECLARATION_NAMESPACE
        and (
            module.role is not FormalModuleRole.COMPOSITION
            or module.resource not in _RELEASED_SHARED_DECLARATION_NAMESPACE_RESOURCES
        )
    )
    declaration_namespaces = tuple(
        module.declaration_namespace
        for module in modules
        if module.declaration_namespace is not None
        and module.declaration_namespace != _RELEASED_SHARED_DECLARATION_NAMESPACE
    )
    if len(set(resources)) != len(resources):
        raise ValueError("formal resource manifest contains duplicate resources")
    if len(set(lean_modules)) != len(lean_modules):
        raise ValueError("formal resource manifest contains duplicate Lean modules")
    if unauthorized_shared_namespace_owners:
        raise ValueError(
            "formal resource manifest assigns the released compatibility namespace "
            f"to unrecognized resources: {unauthorized_shared_namespace_owners!r}"
        )
    if len(set(declaration_namespaces)) != len(declaration_namespaces):
        raise ValueError(
            "formal resource manifest contains duplicate declaration namespaces"
        )
    return modules


def formal_resource_paths(
    role: FormalModuleRole | None = None,
    *,
    project_root: Path | None = None,
) -> tuple[Path, ...]:
    """Return canonical resources from an explicit package or checkout origin.

    Omitting ``project_root`` discovers installed package data. Checkout-bound
    generation and audits pass it explicitly so a wheel cannot silently
    substitute its own formal bytes for the checkout being validated.
    """
    resource_dir = (
        Path(project_root) / "src" / "fep_lean" / "formal"
        if project_root is not None
        else Path(__file__).resolve().parent
    )
    return tuple(resource_dir / module.resource for module in _selected(role))


def formal_resource_relative_paths(
    role: FormalModuleRole | None = None,
) -> tuple[Path, ...]:
    """Return repository-relative canonical resource paths in manifest order."""
    base = Path("src") / "fep_lean" / "formal"
    return tuple(base / module.resource for module in _selected(role))


def formal_resource_manifest_drift(project_root: Path) -> tuple[Path, ...]:
    """Return resource-roster or declaration-namespace drift."""
    modules = _selected(None)
    resource_dir = Path(project_root) / "src" / "fep_lean" / "formal"
    manifested = {resource_dir / module.resource for module in modules}
    present = set(resource_dir.rglob("*.lean")) if resource_dir.is_dir() else set()
    drift = manifested ^ present
    for module in modules:
        path = resource_dir / module.resource
        if path not in present:
            continue
        namespaces = lean_outer_namespaces(path.read_text(encoding="utf-8"))
        if module.declaration_namespace is None:
            if namespaces:
                drift.add(path)
        elif not namespaces or any(
            namespace != module.declaration_namespace for namespace in namespaces
        ):
            drift.add(path)
    return tuple(sorted(drift, key=lambda path: path.as_posix()))


def formal_module_imports(
    role: FormalModuleRole | None = None,
) -> tuple[str, ...]:
    """Return workspace Lean imports in manifest order."""
    return tuple(module.lean_module for module in _selected(role))
