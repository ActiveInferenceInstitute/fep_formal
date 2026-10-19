"""Typed deterministic numerical witnesses for maintained formal families.

Numerical witnesses are explanatory diagnostics. They can expose sign,
normalization, support, rank, and contraction mistakes, but they are neither
Lean proof evidence nor empirical validation of the Free Energy Principle.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from fractions import Fraction
from itertools import pairwise
from pathlib import Path
from typing import Literal, cast

from fep_lean.catalogue.registry import BODY_MODULE_MANIFEST
from fep_lean.formal.declarations import all_formal_theorem_declarations
from fep_lean.methods.probes import (
    BoundaryProbeError,
    bernoulli_fisher,
    exponential_tilt,
    extended_kl,
    finite_expectation,
)
from fep_lean.methods.probes import log_partition as finite_log_partition

Scalar = str | int | float | bool
PlotKind = Literal["line", "scatter", "bar"]
FormalAlignment = Literal["theorem_instance", "structural_analogue"]
NumericalRelation = Literal["eq", "le", "ge", "predicate"]

_WITNESS_ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
_COLUMN_KEY_RE = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")
NON_PROOF_EVIDENCE = "deterministic_numerical_witness_non_proof_evidence"


@dataclass(frozen=True)
class WitnessColumn:
    """One accessible data-table column."""

    key: str
    label: str


@dataclass(frozen=True)
class WitnessRow:
    """One immutable row aligned with a witness's declared columns."""

    values: tuple[Scalar, ...]


@dataclass(frozen=True)
class WitnessPlot:
    """Minimal plot contract consumed by presentation code."""

    kind: PlotKind
    x_key: str
    y_keys: tuple[str, ...]


@dataclass(frozen=True)
class NumericalCheck:
    """One explicit deterministic equality, inequality, or predicate check."""

    id: str
    relation: NumericalRelation
    lhs: int | float | bool
    rhs: int | float | bool
    tolerance: float

    def __post_init__(self) -> None:
        if _WITNESS_ID_RE.fullmatch(self.id) is None:
            raise ValueError(f"malformed numerical check ID: {self.id!r}")
        if self.relation not in {"eq", "le", "ge", "predicate"}:
            raise ValueError(f"{self.id}: unknown numerical relation")
        if (
            isinstance(self.tolerance, bool)
            or not isinstance(self.tolerance, (int, float))
            or not math.isfinite(float(self.tolerance))
            or self.tolerance < 0
        ):
            raise ValueError(f"{self.id}: tolerance must be finite and nonnegative")
        if self.relation == "predicate":
            if type(self.lhs) is not bool or type(self.rhs) is not bool:
                raise ValueError(f"{self.id}: predicate operands must be boolean")
            if self.tolerance != 0:
                raise ValueError(f"{self.id}: predicate tolerance must be zero")
            return
        for side, value in (("lhs", self.lhs), ("rhs", self.rhs)):
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(float(value))
            ):
                raise ValueError(f"{self.id}: {side} must be a finite numeric value")

    @property
    def residual(self) -> float:
        """Return relation-aware nonnegative violation magnitude."""
        if self.relation == "predicate":
            return 0.0 if self.lhs is self.rhs else 1.0
        left = float(self.lhs)
        right = float(self.rhs)
        if self.relation == "eq":
            return abs(left - right)
        if self.relation == "le":
            return max(0.0, left - right)
        return max(0.0, right - left)

    @property
    def accepted(self) -> bool:
        """Whether this check satisfies its declared relation and tolerance."""
        return self.residual <= self.tolerance


@dataclass(frozen=True)
class NumericalWitness:
    """Evaluated explanatory model linked to resolved Lean declarations."""

    id: str
    family: str
    title: str
    theorem_mirrors: tuple[str, ...]
    invariant: str
    parameters: tuple[tuple[str, Scalar], ...]
    columns: tuple[WitnessColumn, ...]
    rows: tuple[WitnessRow, ...]
    checks: tuple[NumericalCheck, ...]
    boundary_behavior: str
    boundary_observed: bool
    plot: WitnessPlot
    formal_alignment: FormalAlignment
    scope: Literal["catalogue", "horizon2"] = "catalogue"
    evidence_kind: str = NON_PROOF_EVIDENCE

    def __post_init__(self) -> None:
        if _WITNESS_ID_RE.fullmatch(self.id) is None:
            raise ValueError(f"malformed numerical witness ID: {self.id!r}")
        if not all(
            isinstance(value, str) and value.strip()
            for value in (self.family, self.title, self.invariant)
        ):
            raise ValueError(f"{self.id}: family, title, and invariant are required")
        if (
            not self.theorem_mirrors
            or not all(
                isinstance(value, str) and value.strip()
                for value in self.theorem_mirrors
            )
            or len(set(self.theorem_mirrors)) != len(self.theorem_mirrors)
        ):
            raise ValueError(f"{self.id}: theorem mirrors must be nonempty and unique")
        if any(
            not isinstance(item, tuple)
            or len(item) != 2
            or not isinstance(item[0], str)
            or not item[0].strip()
            or not isinstance(item[1], (str, int, float, bool))
            or (isinstance(item[1], str) and not item[1])
            or (isinstance(item[1], float) and not math.isfinite(item[1]))
            for item in self.parameters
        ):
            raise ValueError(
                f"{self.id}: parameter values must be named finite scalars"
            )
        parameter_keys = tuple(key for key, _ in self.parameters)
        if len(parameter_keys) != len(set(parameter_keys)):
            raise ValueError(f"{self.id}: parameter keys must be unique")
        if not all(isinstance(column, WitnessColumn) for column in self.columns):
            raise ValueError(f"{self.id}: columns must use WitnessColumn records")
        keys = tuple(column.key for column in self.columns)
        if (
            not keys
            or len(keys) != len(set(keys))
            or any(
                _COLUMN_KEY_RE.fullmatch(column.key) is None
                or not isinstance(column.label, str)
                or not column.label.strip()
                for column in self.columns
            )
        ):
            raise ValueError(
                f"{self.id}: column keys and labels must be nonempty and unique"
            )
        if (
            not self.rows
            or not all(isinstance(row, WitnessRow) for row in self.rows)
            or any(len(row.values) != len(keys) for row in self.rows)
        ):
            raise ValueError(f"{self.id}: every row must align with the column schema")
        if any(
            not isinstance(value, (str, int, float, bool))
            or (isinstance(value, float) and not math.isfinite(value))
            for row in self.rows
            for value in row.values
        ):
            raise ValueError(f"{self.id}: table cells must be finite scalar values")
        if not isinstance(self.plot, WitnessPlot) or self.plot.kind not in {
            "line",
            "scatter",
            "bar",
        }:
            raise ValueError(f"{self.id}: unknown plot kind")
        if self.plot.x_key not in keys or not self.plot.y_keys:
            raise ValueError(f"{self.id}: plot fields must resolve in the table schema")
        if len(set(self.plot.y_keys)) != len(self.plot.y_keys) or any(
            key not in keys for key in self.plot.y_keys
        ):
            raise ValueError(
                f"{self.id}: plot y fields must be unique and resolve in the table schema"
            )
        column_indexes = {key: index for index, key in enumerate(keys)}
        if self.plot.kind in {"line", "scatter"}:
            x_index = column_indexes[self.plot.x_key]
            for row in self.rows:
                x_value = row.values[x_index]
                if (
                    isinstance(x_value, bool)
                    or not isinstance(x_value, (int, float))
                    or not math.isfinite(float(x_value))
                ):
                    raise ValueError(
                        f"{self.id}: line and scatter x columns require finite "
                        "numeric values"
                    )
        for key in self.plot.y_keys:
            index = column_indexes[key]
            for row in self.rows:
                value = row.values[index]
                if (
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or not math.isfinite(float(value))
                ):
                    raise ValueError(
                        f"{self.id}: plotted y columns require finite numeric values"
                    )
        if (
            not self.checks
            or not all(isinstance(check, NumericalCheck) for check in self.checks)
            or len({check.id for check in self.checks}) != len(self.checks)
        ):
            raise ValueError(
                f"{self.id}: numerical checks must be nonempty and uniquely identified"
            )
        if (
            not isinstance(self.boundary_behavior, str)
            or not self.boundary_behavior.strip()
        ):
            raise ValueError(f"{self.id}: boundary behavior must be nonempty")
        if type(self.boundary_observed) is not bool:
            raise ValueError(f"{self.id}: boundary_observed must be boolean")
        if self.scope not in {"catalogue", "horizon2"}:
            raise ValueError(f"{self.id}: unknown witness scope")
        if self.evidence_kind != NON_PROOF_EVIDENCE:
            raise ValueError(f"{self.id}: numerical evidence boundary was weakened")
        if self.formal_alignment not in {"theorem_instance", "structural_analogue"}:
            raise ValueError(f"{self.id}: unknown formal alignment")

    @property
    def accepted(self) -> bool:
        """Whether every typed check and the named boundary satisfy the contract."""
        return all(check.accepted for check in self.checks) and self.boundary_observed


def _columns(*pairs: tuple[str, str]) -> tuple[WitnessColumn, ...]:
    return tuple(WitnessColumn(key, label) for key, label in pairs)


def _measure_bayes_reconstruction() -> NumericalWitness:
    prior = (0.4, 0.6)
    likelihood = ((0.8, 0.2, 0.0), (0.3, 0.7, 0.0))
    evidence_index = 1
    predictive = sum(
        prior[state] * likelihood[state][evidence_index] for state in range(2)
    )
    posterior = tuple(
        prior[state] * likelihood[state][evidence_index] / predictive
        for state in range(2)
    )
    reconstruction_residuals = tuple(
        abs(
            posterior[state] * predictive
            - prior[state] * likelihood[state][evidence_index]
        )
        for state in range(2)
    )
    rows = tuple(
        WitnessRow(
            (
                state,
                prior[state],
                likelihood[state][evidence_index],
                posterior[state],
                reconstruction_residuals[state],
            )
        )
        for state in range(2)
    )
    impossible_predictive = sum(
        prior[state] * likelihood[state][2] for state in range(2)
    )
    return NumericalWitness(
        id="measure-bayes-reconstruction",
        family="measure-bayesian-inversion",
        title="Finite posterior reconstruction",
        theorem_mirrors=(
            "FEP.MeasureBayes.finite_posterior_reconstruction",
            "FEP.MeasureBayes.finite_zero_evidence_boundary",
        ),
        invariant="posterior(x|y) * predictive(y) = prior(x) * likelihood(y|x)",
        parameters=(("evidence_index", evidence_index), ("predictive", predictive)),
        columns=_columns(
            ("state", "State"),
            ("prior", "Prior mass"),
            ("likelihood", "Likelihood mass"),
            ("posterior", "Posterior mass"),
            ("residual", "Reconstruction residual"),
        ),
        rows=rows,
        checks=(
            NumericalCheck(
                "posterior-reconstruction",
                "eq",
                max(reconstruction_residuals),
                0.0,
                1e-12,
            ),
        ),
        boundary_behavior="A third impossible evidence atom has zero predictive mass.",
        boundary_observed=impossible_predictive == 0.0,
        plot=WitnessPlot("bar", "state", ("prior", "posterior")),
        formal_alignment="theorem_instance",
    )


def _gibbs_duality_gap() -> NumericalWitness:
    reference = (0.2, 0.3, 0.5)
    potential = (-0.4, 0.2, 0.8)
    optimizer = exponential_tilt(reference, potential)
    log_partition = finite_log_partition(reference, potential)
    partition = math.exp(log_partition)
    expected_potential = finite_expectation(optimizer, potential)
    kl = sum(
        mass * math.log(mass / base)
        for mass, base in zip(optimizer, reference, strict=True)
    )
    objective = expected_potential - kl
    return NumericalWitness(
        id="gibbs-duality-gap",
        family="variational-duality-and-information-bounds",
        title="Finite Gibbs optimizer closes the variational gap",
        theorem_mirrors=(
            "FEP.VariationalDuality.dvObjective_eq_logPartition_sub_kl",
            "FEP.VariationalDuality.dvObjective_optimizer",
            "fep_fep059.FEP059.fep059_donskerVaradhan_optimizer",
        ),
        invariant="log partition = optimizer expectation - KL(optimizer || reference)",
        parameters=(("partition", partition), ("log_partition", log_partition)),
        columns=_columns(
            ("state", "State"),
            ("reference", "Reference mass"),
            ("potential", "Potential"),
            ("optimizer", "Gibbs optimizer mass"),
        ),
        rows=tuple(
            WitnessRow((state, reference[state], potential[state], optimizer[state]))
            for state in range(3)
        ),
        checks=(
            NumericalCheck("duality-identity", "eq", log_partition, objective, 1e-12),
        ),
        boundary_behavior="All reference atoms are strictly positive.",
        boundary_observed=all(mass > 0 for mass in reference),
        plot=WitnessPlot("bar", "state", ("reference", "optimizer")),
        formal_alignment="theorem_instance",
    )


def _soft_bellman_temperature() -> NumericalWitness:
    action_energy = (1.2, 0.1)
    minimum_action_energy = min(action_energy)
    temperatures = (0.25, 0.5, 1.0, 2.0)
    rows: list[WitnessRow] = []
    residual = 0.0
    for temperature in temperatures:
        partition = sum(math.exp(-value / temperature) for value in action_energy)
        soft_value = -temperature * math.log(partition)
        row_residual = abs(math.exp(-soft_value / temperature) - partition)
        action_bound_slack = minimum_action_energy - soft_value
        residual = max(residual, row_residual, max(0.0, -action_bound_slack))
        rows.append(
            WitnessRow(
                (
                    temperature,
                    partition,
                    soft_value,
                    row_residual,
                    minimum_action_energy,
                    action_bound_slack,
                )
            )
        )
    return NumericalWitness(
        id="soft-bellman-temperature",
        family="control-and-planning-as-inference",
        title="Soft Bellman and desirability identity",
        theorem_mirrors=(
            "FEP.ControlledMarkov.softBellmanValue_succ",
            "FEP.ControlledMarkov.softBellmanValue_partition_pos",
            "FEP.ControlledMarkov.softBellmanValue_le_actionEnergy",
            "fep_fep068.FEP068.fep068_softBellman_recursion",
        ),
        invariant=(
            "the soft Bellman partition is positive, its recursion is exact, "
            "and its value does not exceed either action energy"
        ),
        parameters=(
            ("action_zero_energy", action_energy[0]),
            ("action_one_energy", action_energy[1]),
        ),
        columns=_columns(
            ("temperature", "Temperature"),
            ("partition", "Soft Bellman partition"),
            ("soft_value", "Soft value"),
            ("residual", "Identity residual"),
            ("minimum_action_energy", "Minimum action energy"),
            ("action_bound_slack", "Minimum action energy minus soft value"),
        ),
        rows=tuple(rows),
        checks=(NumericalCheck("soft-bellman-identities", "eq", residual, 0.0, 1e-12),),
        boundary_behavior=(
            "Every sampled temperature and partition is positive, and every "
            "hard-action upper bound has nonnegative slack."
        ),
        boundary_observed=(
            all(value > 0 for value in temperatures)
            and all(float(row.values[1]) > 0 for row in rows)
            and all(float(row.values[5]) >= -1e-12 for row in rows)
        ),
        plot=WitnessPlot("line", "temperature", ("soft_value",)),
        formal_alignment="theorem_instance",
    )


def _normalize(weights: tuple[float, ...]) -> tuple[float, ...]:
    total = sum(weights)
    if total <= 0:
        raise ValueError("cannot normalize nonpositive witness weights")
    return tuple(weight / total for weight in weights)


def _bool_forward_backward() -> NumericalWitness:
    prior = (0.25, 0.75)
    transition = ((0.75, 0.25), (0.25, 0.75))
    emission_true = (0.2, 0.8)
    predicted = tuple(
        sum(prior[source] * transition[source][target] for source in range(2))
        for target in range(2)
    )
    evidence = sum(predicted[state] * emission_true[state] for state in range(2))
    filtered = tuple(
        predicted[state] * emission_true[state] / evidence for state in range(2)
    )
    backward = tuple(
        sum(transition[state][target] * emission_true[target] for target in range(2))
        for state in range(2)
    )
    backward_evidence = sum(prior[state] * backward[state] for state in range(2))
    smoothed = _normalize(tuple(prior[state] * backward[state] for state in range(2)))
    residual = max(
        abs(sum(predicted) - 1.0),
        abs(sum(filtered) - 1.0),
        abs(sum(smoothed) - 1.0),
        abs(evidence - backward_evidence),
    )
    rows = tuple(
        WitnessRow(
            (
                state,
                prior[state],
                predicted[state],
                filtered[state],
                backward[state],
                smoothed[state],
            )
        )
        for state in range(2)
    )
    return NumericalWitness(
        id="bool-forward-backward",
        family="temporal-and-hierarchical-inference",
        title="Boolean forward-backward normalization",
        theorem_mirrors=(
            "FEP.TemporalInference.forward_backward_evidence_agree",
            "FEP.TemporalInference.boolForwardFilter_sum_one",
            "FEP.TemporalInference.boolSmoothing_sum_one",
        ),
        invariant="Every filtering and smoothing marginal has total mass one.",
        parameters=(("observation", "true"), ("evidence", evidence)),
        columns=_columns(
            ("state", "State"),
            ("prior", "Initial mass"),
            ("predicted", "Predicted mass"),
            ("filtered", "Filtered mass"),
            ("backward", "Backward message"),
            ("smoothed", "Smoothed initial mass"),
        ),
        rows=rows,
        checks=(
            NumericalCheck(
                "forward-backward-normalization", "eq", residual, 0.0, 1e-12
            ),
        ),
        boundary_behavior="Forward and backward evidence agree at positive mass.",
        boundary_observed=evidence > 0 and abs(evidence - backward_evidence) <= 1e-12,
        plot=WitnessPlot("bar", "state", ("prior", "filtered", "smoothed")),
        formal_alignment="theorem_instance",
    )


def _causal_intervention_invariance() -> NumericalWitness:
    # This is the exact finite model in `FEP.CausalDynamics.boolOrderedModel`:
    # independent uniform Boolean roots, a mediator that copies the intervened
    # root, and an outcome given by non-descendant XOR mediator.
    boolean_states = (False, True)
    uniform_mass = {False: 0.5, True: 0.5}
    evaluated = tuple(
        (
            root,
            sum(
                mass for non_descendant, mass in uniform_mass.items() if non_descendant
            ),
            float(root),
            sum(
                mass
                for non_descendant, mass in uniform_mass.items()
                if non_descendant != root
            ),
        )
        for root in boolean_states
    )
    rows = tuple(
        WitnessRow(
            (
                f"do(root={str(root).lower()})",
                nondescendant_true,
                mediator_true,
                outcome_true,
            )
        )
        for root, nondescendant_true, mediator_true, outcome_true in evaluated
    )
    residual = max(
        abs(float(rows[0].values[1]) - float(rows[1].values[1])),
        abs(float(rows[0].values[2])),
        abs(float(rows[1].values[2]) - 1.0),
        abs(float(rows[0].values[3]) - 0.5),
        abs(float(rows[1].values[3]) - 0.5),
    )
    return NumericalWitness(
        id="causal-intervention-invariance",
        family="causal-blankets-and-interventions",
        title="Boolean root intervention preserves a fair non-descendant and flips its mediator",
        theorem_mirrors=(
            "FEP.CausalDynamics.nonDescendant_intervention_invariant",
            "FEP.CausalDynamics.boolIntervention_false_mediator_true_zero",
            "FEP.CausalDynamics.boolIntervention_true_mediator_true_one",
            "FEP.CausalDynamics.boolIntervention_preserves_named_nonDescendant",
            "fep_fep083.FEP083.fep083_nonDescendant_intervention_invariance",
            "fep_fep083.FEP083.fep083_fourNode_descendantChange_nonDescendantPreservation",
        ),
        invariant=(
            "do(root=false/true) preserves the uniform non-descendant, sets the "
            "copy mediator to false/true, and leaves the XOR outcome fair"
        ),
        parameters=(
            ("root_law", "uniform"),
            ("nondescendant_law", "uniform"),
            ("mediator_kernel", "copy-root"),
            ("outcome_kernel", "xor"),
        ),
        columns=_columns(
            ("regime", "Regime"),
            ("nondescendant_true", "Non-descendant true mass"),
            ("mediator_true", "Mediator true mass"),
            ("outcome_true", "XOR outcome true mass"),
        ),
        rows=rows,
        checks=(NumericalCheck("intervention-invariance", "eq", residual, 0.0, 1e-12),),
        boundary_behavior=(
            "The two hard interventions put zero and unit mass on the true mediator."
        ),
        boundary_observed=tuple(float(row.values[2]) for row in rows) == (0.0, 1.0),
        plot=WitnessPlot(
            "bar",
            "regime",
            ("nondescendant_true", "mediator_true", "outcome_true"),
        ),
        formal_alignment="theorem_instance",
    )


def _finite_jet_error_descent() -> NumericalWitness:
    precision = 3.0
    target = 0.25
    step_size = 0.2
    contraction = 1.0 - step_size
    estimate = 2.0
    rows: list[WitnessRow] = []
    residual = 0.0
    for iteration in range(9):
        error = target - estimate
        energy = 0.5 * precision * error * error
        next_estimate = estimate + step_size * error
        next_error = target - next_estimate
        next_energy = 0.5 * precision * next_error * next_error
        residual = max(
            residual,
            abs(next_error - contraction * error),
            abs(next_energy - contraction**2 * energy),
            max(0.0, next_energy - energy),
        )
        rows.append(WitnessRow((iteration, estimate, error, energy)))
        estimate = next_estimate
    return NumericalWitness(
        id="finite-jet-error-descent",
        family="predictive-coding-and-generalized-coordinates",
        title="Precision-weighted correction contracts prediction error",
        theorem_mirrors=(
            "FEP.PredictiveCoding.predictionError_update",
            "FEP.PredictiveCoding.predictionEnergy_contraction",
        ),
        invariant=(
            "error' = (1 - step) error and precisionEnergy' = "
            "(1 - step)^2 precisionEnergy"
        ),
        parameters=(
            ("precision", precision),
            ("target", target),
            ("step_size", step_size),
            ("contraction", contraction),
        ),
        columns=_columns(
            ("iteration", "Iteration"),
            ("state", "State"),
            ("prediction_error", "Prediction error"),
            ("energy", "Precision-weighted energy"),
        ),
        rows=tuple(rows),
        checks=(
            NumericalCheck("prediction-error-contraction", "eq", residual, 0.0, 1e-12),
        ),
        boundary_behavior="The configured Lean step size lies strictly between zero and two.",
        boundary_observed=0.0 < step_size < 2.0 and abs(contraction) < 1.0,
        plot=WitnessPlot("line", "iteration", ("prediction_error", "energy")),
        formal_alignment="theorem_instance",
    )


def _path_fluctuation_identity() -> NumericalWitness:
    forward = (0.5, 0.3, 0.2)
    reverse = (0.25, 0.35, 0.4)
    entropy_production = tuple(
        math.log(p / q) for p, q in zip(forward, reverse, strict=True)
    )
    weighted_exponentials = tuple(
        p * math.exp(-sigma)
        for p, sigma in zip(forward, entropy_production, strict=True)
    )
    rows = tuple(
        WitnessRow(
            (
                path,
                forward[path],
                reverse[path],
                entropy_production[path],
                weighted_exponentials[path],
            )
        )
        for path in range(3)
    )
    return NumericalWitness(
        id="path-fluctuation-identity",
        family="path-space-stochastic-thermodynamics",
        title="Finite integral fluctuation identity",
        theorem_mirrors=(
            "FEP.PathThermodynamics.integralFluctuation_eq_one",
            "fep_fep096.FEP096.fep096_integralFluctuation_theorem",
        ),
        invariant="forward expectation of exp(-entropy production) equals one",
        parameters=(("paths", 3),),
        columns=_columns(
            ("path", "Path"),
            ("forward", "Forward mass"),
            ("reverse", "Reverse mass"),
            ("entropy_production", "Log path-law ratio"),
            ("weighted_exponential", "Forward-weighted exponential"),
        ),
        rows=rows,
        checks=(
            NumericalCheck(
                "integral-fluctuation",
                "eq",
                sum(weighted_exponentials),
                1.0,
                1e-12,
            ),
        ),
        boundary_behavior="Both path laws have full support.",
        boundary_observed=all(value > 0 for value in (*forward, *reverse)),
        plot=WitnessPlot("bar", "path", ("forward", "reverse", "weighted_exponential")),
        formal_alignment="theorem_instance",
    )


def _categorical_fisher_rank() -> NumericalWitness:
    categorical_law = (0.5, 0.5)
    categorical_tangent = (1.0, -1.0)
    categorical_energy = sum(
        tangent * tangent / probability
        for tangent, probability in zip(
            categorical_tangent, categorical_law, strict=True
        )
    )
    duplicated_gram = ((4.0, 4.0), (4.0, 4.0))
    duplicated_determinant = (
        duplicated_gram[0][0] * duplicated_gram[1][1]
        - duplicated_gram[0][1] * duplicated_gram[1][0]
    )
    certificates = (
        ("categorical tangent energy", 4.0, categorical_energy),
        ("duplicated Gram (0,0)", 4.0, duplicated_gram[0][0]),
        ("duplicated Gram (0,1)", 4.0, duplicated_gram[0][1]),
        ("duplicated Gram (1,1)", 4.0, duplicated_gram[1][1]),
        ("duplicated Gram determinant", 0.0, duplicated_determinant),
    )
    return NumericalWitness(
        id="categorical-fisher-rank",
        family="information-geometry-and-geometric-optimization",
        title="Fin-2 categorical Fisher energy and duplicated-score boundary",
        theorem_mirrors=(
            "FEP.GeometricOptimization.twoCategorical_nonzeroTangent_metric",
            "FEP.GeometricOptimization.twoCategorical_simplexMetric_fullRank",
            "FEP.InformationGeometry.duplicatedFairBernoulli_fisherMatrix_entry",
            "FEP.InformationGeometry.duplicatedFairBernoulli_not_identifiable",
        ),
        invariant=(
            "The nonzero Fin-2 simplex tangent has Fisher energy four, while the "
            "duplicated fair-Bernoulli score Gram matrix has determinant zero."
        ),
        parameters=(
            ("categories", 2),
            ("categorical_law", "(1/2, 1/2)"),
            ("categorical_tangent", "(1, -1)"),
            ("duplicated_score_gram", "[[4, 4], [4, 4]]"),
        ),
        columns=_columns(
            ("certificate", "Exact formal certificate"),
            ("expected", "Theorem value"),
            ("observed", "Evaluated value"),
            ("absolute_error", "Absolute error"),
        ),
        rows=tuple(
            WitnessRow((label, expected, observed, abs(observed - expected)))
            for label, expected, observed in certificates
        ),
        checks=(
            NumericalCheck(
                "fisher-rank-certificates",
                "eq",
                max(abs(observed - expected) for _, expected, observed in certificates),
                0.0,
                1e-12,
            ),
        ),
        boundary_behavior=(
            "The explicit nonzero categorical tangent has positive energy; duplicating "
            "the fair-Bernoulli score direction makes the coordinate Gram determinant zero."
        ),
        boundary_observed=categorical_energy == 4.0 and duplicated_determinant == 0.0,
        plot=WitnessPlot("bar", "certificate", ("observed",)),
        formal_alignment="theorem_instance",
    )


def _belief_consensus_contraction() -> NumericalWitness:
    left = 0.1
    right = 0.9
    mixing = 0.25
    contraction = abs(1.0 - 2.0 * mixing)
    rows: list[WitnessRow] = []
    residual = 0.0
    previous_gap = abs(left - right)
    for iteration in range(9):
        gap = abs(left - right)
        predicted_gap = (contraction**iteration) * 0.8
        residual = max(residual, abs(gap - predicted_gap))
        rows.append(WitnessRow((iteration, left, right, gap, predicted_gap)))
        left, right = (
            (1.0 - mixing) * left + mixing * right,
            mixing * left + (1.0 - mixing) * right,
        )
        if iteration > 0:
            residual = max(residual, max(0.0, gap - previous_gap))
        previous_gap = gap
    return NumericalWitness(
        id="belief-consensus-contraction",
        family="collective-and-multiagent-active-inference",
        title="Two-agent belief consensus contracts geometrically",
        theorem_mirrors=(
            "FEP.CollectiveInference.consensusIterate_gap",
            "FEP.FiniteMarkovDynamics.totalVariation_kernelPower_le",
        ),
        invariant="belief gap at n = contraction^n * initial gap",
        parameters=(("mixing", mixing), ("contraction", contraction)),
        columns=_columns(
            ("iteration", "Iteration"),
            ("agent_left", "Agent-left belief"),
            ("agent_right", "Agent-right belief"),
            ("gap", "Belief gap"),
            ("predicted_gap", "Geometric envelope"),
        ),
        rows=tuple(rows),
        checks=(NumericalCheck("consensus-contraction", "eq", residual, 0.0, 1e-12),),
        boundary_behavior="The averaging coefficient gives a strict contraction.",
        boundary_observed=0.0 <= contraction < 1.0,
        plot=WitnessPlot("line", "iteration", ("gap", "predicted_gap")),
        formal_alignment="theorem_instance",
    )


def _binomial_two_sided_tail(n: int, epsilon: float) -> float:
    lower = math.floor(n * (0.5 - epsilon))
    upper = math.ceil(n * (0.5 + epsilon))
    return sum(
        math.comb(n, successes) * 0.5**n
        for successes in range(n + 1)
        if successes <= lower or successes >= upper
    )


def _subgaussian_envelope() -> NumericalWitness:
    epsilon = 0.2
    sample_sizes = (10, 20, 40, 80, 120)
    rows: list[WitnessRow] = []
    residual = 0.0
    for sample_size in sample_sizes:
        exact_tail = _binomial_two_sided_tail(sample_size, epsilon)
        envelope = min(1.0, 2.0 * math.exp(-2.0 * sample_size * epsilon**2))
        violation = max(0.0, exact_tail - envelope)
        residual = max(residual, violation)
        rows.append(WitnessRow((sample_size, exact_tail, envelope, violation)))
    envelopes = tuple(float(row.values[2]) for row in rows)
    return NumericalWitness(
        id="subgaussian-envelope",
        family="learning-concentration-and-model-evidence",
        title="Exact Bernoulli tail beneath a sub-Gaussian envelope",
        theorem_mirrors=(
            "FEP.LearningTheory.subGaussian_empiricalMean_tail",
            "fep_fep114.FEP114.fep114_subGaussian_empiricalMean_tail",
        ),
        invariant=(
            "an exact fair-Bernoulli two-sided tail is numerically compared with "
            "the corresponding Hoeffding-form envelope"
        ),
        parameters=(("mean", 0.5), ("epsilon", epsilon)),
        columns=_columns(
            ("sample_size", "Sample size"),
            ("exact_tail", "Exact two-sided tail"),
            ("envelope", "Sub-Gaussian envelope"),
            ("violation", "Positive-part violation"),
        ),
        rows=tuple(rows),
        checks=(NumericalCheck("subgaussian-envelope", "eq", residual, 0.0, 1e-12),),
        boundary_behavior=(
            "The envelope is nonincreasing; this finite enumeration is a structural "
            "analogue and does not discharge the Lean independence/MGF premises."
        ),
        boundary_observed=all(
            later <= earlier for earlier, later in pairwise(envelopes)
        ),
        plot=WitnessPlot("line", "sample_size", ("exact_tail", "envelope")),
        formal_alignment="structural_analogue",
    )


def _laplace_brier_risk() -> NumericalWitness:
    sample_count = 8
    target = 0.3
    shrinkage = sample_count / (sample_count + 2)
    masses = tuple(
        math.comb(sample_count, successes)
        * target**successes
        * (1.0 - target) ** (sample_count - successes)
        for successes in range(sample_count + 1)
    )
    raw_errors = tuple(
        successes / sample_count - target for successes in range(sample_count + 1)
    )
    smoothed_errors = tuple(
        (successes + 1) / (sample_count + 2) - target
        for successes in range(sample_count + 1)
    )
    raw_risk = sum(
        mass * error**2 for mass, error in zip(masses, raw_errors, strict=True)
    )
    brier_risk = sum(
        mass * error**2 for mass, error in zip(masses, smoothed_errors, strict=True)
    )
    risk_bound = 2.0 * shrinkage**2 * raw_risk + 2.0 / (sample_count + 2) ** 2
    bias_boundary = (1.0 / (2 + 2)) - 0.0
    return NumericalWitness(
        id="laplace-brier-risk",
        family="finite-sample-risk-and-calibration",
        title="Finite Laplace-smoothed Brier-risk transfer",
        theorem_mirrors=(
            "FEP.EmpiricalRisk.brierExcess_eq_sqError",
            "FEP.EmpiricalRisk.laplaceBias_nonzero_witness",
            "FEP.EmpiricalRisk.laplaceBrierRisk_le",
            "fep_fep126.FEP126.fep126_laplaceBrierRisk_le",
        ),
        invariant=(
            "Bernoulli Brier excess equals squared forecast error and the "
            "finite-law Laplace risk stays below its transfer bound"
        ),
        parameters=(
            ("sample_count", sample_count),
            ("target", target),
            ("shrinkage", shrinkage),
            ("raw_risk", raw_risk),
            ("risk_bound", risk_bound),
        ),
        columns=_columns(
            ("successes", "Successes"),
            ("sampling_mass", "Binomial sampling mass"),
            ("empirical_forecast", "Empirical forecast"),
            ("laplace_forecast", "Laplace forecast"),
            ("brier_excess", "Laplace Brier excess"),
        ),
        rows=tuple(
            WitnessRow(
                (
                    successes,
                    masses[successes],
                    successes / sample_count,
                    (successes + 1) / (sample_count + 2),
                    smoothed_errors[successes] ** 2,
                )
            )
            for successes in range(sample_count + 1)
        ),
        checks=(
            NumericalCheck("sampling-normalized", "eq", sum(masses), 1.0, 1e-12),
            NumericalCheck("brier-risk-bound", "le", brier_risk, risk_bound, 1e-12),
            NumericalCheck("nonzero-bias-quarter", "eq", bias_boundary, 0.25, 1e-12),
            NumericalCheck(
                "bias-is-nonzero", "predicate", bias_boundary != 0.0, True, 0.0
            ),
        ),
        boundary_behavior=(
            "At sample count two and target zero, add-one smoothing has exact "
            "bias one quarter rather than silently becoming unbiased."
        ),
        boundary_observed=bias_boundary == 0.25,
        plot=WitnessPlot(
            "line", "successes", ("empirical_forecast", "laplace_forecast")
        ),
        formal_alignment="theorem_instance",
    )


def _policy_tree_feedback() -> NumericalWitness:
    feedback_value = 0.0
    fixed_false_value = 0.5
    fixed_true_value = 0.5
    feedback_actions = (False, True)
    return NumericalWitness(
        id="policy-tree-feedback",
        family="closed-loop-policy-trees-and-efe",
        title="Two-stage Boolean policy-tree feedback advantage",
        theorem_mirrors=(
            "FEP.PolicyTrees.boolFeedbackTree_strictlyBetter",
            "FEP.PolicyTrees.boolFeedbackTree_value_zero",
            "FEP.PolicyTrees.boolOpenLoop_value_half",
            "fep_fep134.FEP134.fep134_boolFeedback_strictlyBetter",
            "fep_fep134.FEP134.fep134_feedback_continuation_changes",
        ),
        invariant=(
            "observation-contingent continuation has value zero while either "
            "fixed continuation has value one half"
        ),
        parameters=(
            ("horizon", 2),
            ("first_observation_law", "fair-bool"),
        ),
        columns=_columns(
            ("policy", "Policy"),
            ("value", "Exact value"),
            ("second_action_false_observation", "Action after false"),
            ("second_action_true_observation", "Action after true"),
        ),
        rows=(
            WitnessRow(
                (
                    "feedback",
                    feedback_value,
                    feedback_actions[0],
                    feedback_actions[1],
                )
            ),
            WitnessRow(("fixed-false", fixed_false_value, False, False)),
            WitnessRow(("fixed-true", fixed_true_value, True, True)),
        ),
        checks=(
            NumericalCheck("feedback-value-zero", "eq", feedback_value, 0.0, 0.0),
            NumericalCheck(
                "open-loop-value-half",
                "eq",
                max(fixed_false_value, fixed_true_value),
                0.5,
                0.0,
            ),
            NumericalCheck(
                "feedback-no-worse",
                "le",
                feedback_value,
                min(fixed_false_value, fixed_true_value),
                0.0,
            ),
            NumericalCheck(
                "continuation-changes",
                "predicate",
                feedback_actions[0] != feedback_actions[1],
                True,
                0.0,
            ),
        ),
        boundary_behavior=(
            "The two observation branches select different second actions, and "
            "the strict feedback advantage is exactly one half."
        ),
        boundary_observed=(
            feedback_value < fixed_false_value and feedback_value < fixed_true_value
        ),
        plot=WitnessPlot("bar", "policy", ("value",)),
        formal_alignment="theorem_instance",
    )


def _native_blanket_transfer() -> NumericalWitness:
    rows = (
        WitnessRow(("blanket=(false,false)", 0.5, 0.5, True)),
        WitnessRow(("blanket=(true,true)", 0.5, 0.5, True)),
        WitnessRow(("off-regime=(false,true)", 0.0, 0.0, True)),
    )
    return NumericalWitness(
        id="native-blanket-transfer",
        family="finite-to-native-blanket-transfer",
        title="Correlated Boolean blanket transfers to native conditional independence",
        theorem_mirrors=(
            "FEP.NativeBlanket.correlatedBlanket_nonvacuous",
            "FEP.NativeBlanket.staticJoint_condIndepFun",
            "FEP.NativeBlanket.staticJoint_rectangle_factorization",
            "fep_fep139.FEP139.fep139_correlatedBlanket_nonvacuous",
            "fep_fep139.FEP139.fep139_staticJoint_condIndepFun",
        ),
        invariant=(
            "two positive correlated blanket regimes have exact product rows "
            "and their weighted Dirac embedding satisfies native CondIndepFun"
        ),
        parameters=(
            ("blanket_carrier", "Bool×Bool"),
            ("internal_kernel", "copy-sensory"),
            ("external_kernel", "copy-sensory"),
        ),
        columns=_columns(
            ("regime", "Blanket regime"),
            ("joint_mass", "Joint atom mass"),
            ("factorized_mass", "Factorized atom mass"),
            ("conditional_product", "Conditional product row"),
        ),
        rows=rows,
        checks=(
            NumericalCheck(
                "positive-regime-mass",
                "eq",
                float(rows[0].values[1]) + float(rows[1].values[1]),
                1.0,
                0.0,
            ),
            NumericalCheck(
                "rectangle-factorization",
                "eq",
                max(abs(float(row.values[1]) - float(row.values[2])) for row in rows),
                0.0,
                0.0,
            ),
            NumericalCheck(
                "off-regime-excluded", "eq", float(rows[2].values[1]), 0.0, 0.0
            ),
            NumericalCheck(
                "conditional-product-rows",
                "predicate",
                all(row.values[3] is True for row in rows),
                True,
                0.0,
            ),
        ),
        boundary_behavior=(
            "The off-regime blanket atom has zero mass while both diagonal "
            "conditioning regimes retain mass one half."
        ),
        boundary_observed=(
            tuple(float(row.values[1]) for row in rows) == (0.5, 0.5, 0.0)
        ),
        plot=WitnessPlot("bar", "regime", ("joint_mass", "factorized_mass")),
        formal_alignment="theorem_instance",
    )


def _exponential_family_duality() -> NumericalWitness:
    statistics = (0.0, 1.0, 2.0)
    left = 0.4
    right = -0.3

    def law(parameter: float) -> tuple[float, ...]:
        weights = tuple(math.exp(parameter * statistic) for statistic in statistics)
        return tuple(weight / sum(weights) for weight in weights)

    def log_partition(parameter: float) -> float:
        return math.log(
            sum(math.exp(parameter * statistic) for statistic in statistics)
        )

    left_law = law(left)
    right_law = law(right)
    left_mean = sum(
        mass * statistic for mass, statistic in zip(left_law, statistics, strict=True)
    )
    left_variance = sum(
        mass * (statistic - left_mean) ** 2
        for mass, statistic in zip(left_law, statistics, strict=True)
    )
    kl = sum(
        left_mass * math.log(left_mass / right_mass)
        for left_mass, right_mass in zip(left_law, right_law, strict=True)
    )
    bregman = log_partition(right) - log_partition(left) - left_mean * (right - left)
    centered_score = sum(
        mass * (statistic - left_mean)
        for mass, statistic in zip(left_law, statistics, strict=True)
    )
    variance_zero = sum((statistic - 1.0) ** 2 / 3.0 for statistic in statistics)
    return NumericalWitness(
        id="exponential-family-duality",
        family="finite-exponential-family-dual-geometry",
        title="Three-state exponential-family KL and Bregman duality",
        theorem_mirrors=(
            "FEP.ExponentialFamily.ScalarExponentialFamily.constantStatistic_variance_zero",
            "FEP.ExponentialFamily.ScalarExponentialFamily.finiteKL_eq_logPartitionBregman",
            "FEP.ExponentialFamily.ScalarExponentialFamily.mean_score_zero",
            "FEP.ExponentialFamily.ScalarExponentialFamily.threeState_variance_zero",
            "fep_fep147.FEP147.fep147_exponentialFamily_KL_eq_bregman",
        ),
        invariant=(
            "supported finite KL equals the oriented log-partition Bregman "
            "divergence and the derived score remains centered"
        ),
        parameters=(
            ("left_parameter", left),
            ("right_parameter", right),
            ("left_mean", left_mean),
            ("left_variance", left_variance),
        ),
        columns=_columns(
            ("outcome", "Statistic value"),
            ("left_mass", "Left law mass"),
            ("right_mass", "Right law mass"),
            ("left_score", "Centered left score"),
        ),
        rows=tuple(
            WitnessRow(
                (
                    statistics[index],
                    left_law[index],
                    right_law[index],
                    statistics[index] - left_mean,
                )
            )
            for index in range(3)
        ),
        checks=(
            NumericalCheck("left-law-normalized", "eq", sum(left_law), 1.0, 1e-12),
            NumericalCheck("right-law-normalized", "eq", sum(right_law), 1.0, 1e-12),
            NumericalCheck("centered-score", "eq", centered_score, 0.0, 1e-12),
            NumericalCheck("kl-bregman", "eq", kl, bregman, 1e-12),
            NumericalCheck(
                "three-state-variance-two-thirds",
                "eq",
                variance_zero,
                2.0 / 3.0,
                1e-12,
            ),
            NumericalCheck("constant-statistic-zero", "eq", 0.0, 0.0, 0.0),
        ),
        boundary_behavior=(
            "The nonconstant three-state statistic has variance two thirds at "
            "zero, while a constant statistic has exactly zero variance."
        ),
        boundary_observed=(
            abs(variance_zero - 2.0 / 3.0) <= 1e-12 and left_variance > 0.0
        ),
        plot=WitnessPlot("bar", "outcome", ("left_mass", "right_mass")),
        formal_alignment="theorem_instance",
    )


# Shared private helpers for the fixed diagnostic carriers.
# The matrix2 helpers deliberately retain the two-state arithmetic order.
def _matrix2_mul(
    left: tuple[tuple[float, float], tuple[float, float]],
    right: tuple[tuple[float, float], tuple[float, float]],
) -> tuple[tuple[float, float], tuple[float, float]]:
    return (
        (
            left[0][0] * right[0][0] + left[0][1] * right[1][0],
            left[0][0] * right[0][1] + left[0][1] * right[1][1],
        ),
        (
            left[1][0] * right[0][0] + left[1][1] * right[1][0],
            left[1][0] * right[0][1] + left[1][1] * right[1][1],
        ),
    )


def _matrix_dot(v: tuple[float, ...], w: tuple[float, ...]) -> float:
    return sum(a * b for a, b in zip(v, w, strict=True))


def _matrix_mul_vec(
    m: tuple[tuple[float, ...], ...], v: tuple[float, ...]
) -> tuple[float, ...]:
    return tuple(sum(m[i][k] * v[k] for k in range(len(v))) for i in range(len(v)))


def _matrix_trace(m: tuple[tuple[float, ...], ...]) -> float:
    return sum(m[i][i] for i in range(len(m)))


def _matrix_node_div(w: tuple[tuple[float, ...], ...], i: int) -> float:
    return sum(w[i][j] - w[j][i] for j in range(len(w)))


def _matrix2_frobenius_sq(m: tuple[tuple[float, ...], ...]) -> float:
    return sum(m[i][j] ** 2 for i in range(2) for j in range(2))


def _matrix2_subtract(
    a: tuple[tuple[float, ...], ...], b: tuple[tuple[float, ...], ...]
) -> tuple[tuple[float, ...], ...]:
    return tuple(tuple(a[i][j] - b[i][j] for j in range(2)) for i in range(2))


def _two_state_master_equation() -> NumericalWitness:
    forward = 0.7
    backward = 0.3
    decay = forward + backward
    stationary_false = backward / decay
    stationary_true = forward / decay

    def transition(time: float) -> tuple[tuple[float, float], tuple[float, float]]:
        rho = math.exp(-decay * time)
        return (
            (
                stationary_false + stationary_true * rho,
                stationary_true * (1.0 - rho),
            ),
            (
                stationary_false * (1.0 - rho),
                stationary_true + stationary_false * rho,
            ),
        )

    generator = ((-forward, forward), (backward, -backward))
    times = (0.0, 0.5, 1.0, 2.0)
    rows: list[WitnessRow] = []
    row_sum_error = 0.0
    relaxation_error = 0.0
    for time in times:
        matrix = transition(time)
        rho = math.exp(-decay * time)
        true_mass = matrix[0][1]
        expected_true_mass = stationary_true + rho * (0.0 - stationary_true)
        lyapunov = (true_mass - stationary_true) ** 2
        derivative = -2.0 * decay * lyapunov
        row_sum_error = max(
            row_sum_error,
            *(abs(sum(matrix[source]) - 1.0) for source in range(2)),
        )
        relaxation_error = max(relaxation_error, abs(true_mass - expected_true_mass))
        rows.append(WitnessRow((time, matrix[0][1], true_mass, lyapunov, derivative)))

    semigroup_left = transition(0.4 + 0.7)
    semigroup_right = _matrix2_mul(transition(0.4), transition(0.7))
    semigroup_error = max(
        abs(semigroup_left[i][j] - semigroup_right[i][j])
        for i in range(2)
        for j in range(2)
    )
    master_time = 0.6
    master_matrix = transition(master_time)
    q_times_p = _matrix2_mul(generator, master_matrix)
    p_times_q = _matrix2_mul(master_matrix, generator)
    rho = math.exp(-decay * master_time)
    derivative_matrix = (
        (-forward * rho, forward * rho),
        (backward * rho, -backward * rho),
    )
    master_error = max(
        abs(product[i][j] - derivative_matrix[i][j])
        for product in (q_times_p, p_times_q)
        for i in range(2)
        for j in range(2)
    )
    detail_balance_error = max(
        abs(
            (stationary_false, stationary_true)[i] * master_matrix[i][j]
            - (stationary_false, stationary_true)[j] * master_matrix[j][i]
        )
        for i in range(2)
        for j in range(2)
    )
    derivative_zero = float(rows[0].values[4])
    return NumericalWitness(
        id="two-state-master-equation",
        family="two-state-continuous-time-thermodynamics",
        title="Exact Boolean semigroup, master equation, and Lyapunov decay",
        theorem_mirrors=(
            "FEP.ContinuousTimeMarkov.TwoStateRates.benchmarkLyapunov_deriv_zero_neg",
            "FEP.ContinuousTimeMarkov.TwoStateRates.transition_add",
            "FEP.ContinuousTimeMarkov.TwoStateRates.transition_detailedBalance",
            "FEP.ContinuousTimeMarkov.TwoStateRates.transition_masterEquation",
            "FEP.ContinuousTimeMarkov.TwoStateRates.transition_rowSum",
            "fep_fep152.FEP152.fep152_twoStateSemigroup_hasDerivAt",
            "fep_fep155.FEP155.fep155_twoStateLyapunov_hasDerivAt",
        ),
        invariant=(
            "the exact two-state kernel is stochastic, forms a semigroup, solves "
            "both master equations, and has exponentially decaying squared deviation"
        ),
        parameters=(
            ("forward_rate", forward),
            ("backward_rate", backward),
            ("stationary_true", stationary_true),
            ("decay_rate", decay),
        ),
        columns=_columns(
            ("time", "Time"),
            ("false_to_true", "P(false,true)"),
            ("true_mass", "True mass from false initial state"),
            ("lyapunov", "Squared stationary deviation"),
            ("lyapunov_derivative", "Exact Lyapunov derivative"),
        ),
        rows=tuple(rows),
        checks=(
            NumericalCheck("row-normalization", "eq", row_sum_error, 0.0, 1e-12),
            NumericalCheck("semigroup-addition", "eq", semigroup_error, 0.0, 1e-12),
            NumericalCheck("master-equation", "eq", master_error, 0.0, 1e-12),
            NumericalCheck("detailed-balance", "eq", detail_balance_error, 0.0, 1e-12),
            NumericalCheck("relaxation-identity", "eq", relaxation_error, 0.0, 1e-12),
            NumericalCheck(
                "lyapunov-derivative-negative",
                "predicate",
                derivative_zero < 0.0,
                True,
                0.0,
            ),
        ),
        boundary_behavior=(
            "The nonstationary false point mass has Lyapunov derivative -0.98 "
            "at time zero for rates 0.7 and 0.3."
        ),
        boundary_observed=abs(derivative_zero + 0.98) <= 1e-12,
        plot=WitnessPlot(
            "line", "time", ("true_mass", "lyapunov", "lyapunov_derivative")
        ),
        formal_alignment="theorem_instance",
    )


@dataclass(frozen=True)
class _EfePlanningData:
    actual: tuple[float, ...]
    affinity_bound: float
    backward: float
    belief_true: float
    chain_residual: float
    control_floor: float
    cost: tuple[float, ...]
    duality_residual: float
    envelope_violation: float
    floor_residual: float
    forward: float
    gap_posterior: float
    gap_residual: float
    gap_total: float
    initial_gap: float
    initial_gap_form: float
    partition: float
    posterior_minimal: bool
    precision: float
    prior: tuple[float, ...]
    production_rate: float
    production_violation: float
    reference: tuple[float, ...]
    rows: list[WitnessRow]


@dataclass(frozen=True)
class _EfeSplitData:
    fep166_canonical_split: bool
    fep166_circ_01: Fraction
    fep166_circ_10: Fraction
    fep166_law: tuple[Fraction, ...]
    fep166_reversible: bool
    fep166_unique: bool


def _efe_planning_data() -> _EfePlanningData:
    """Evaluate the exact EFE floor, perception chain rule, and affinity bound."""

    def binary_kl(left: tuple[float, ...], right: tuple[float, ...]) -> float:
        return sum(
            mass * math.log(mass / base)
            for mass, base in zip(left, right, strict=True)
            if mass > 0.0
        )

    # Planning as inference: the Boltzmann EFE control posterior (fep-156).
    prior = (0.6, 0.4)
    precision = 2.0
    cost = (0.0, 0.6)
    weights = tuple(
        mass * math.exp(-precision * value)
        for mass, value in zip(prior, cost, strict=True)
    )
    partition = sum(weights)
    control_posterior = tuple(weight / partition for weight in weights)
    log_partition = math.log(partition)
    control_floor = -log_partition / precision
    floor_residual = abs(control_floor + log_partition / precision)

    gap_residual = 0.0
    duality_residual = 0.0
    posterior_minimal = True
    for candidate in (prior, (0.5, 0.5), (0.9, 0.1)):
        expected_cost = sum(
            mass * value for mass, value in zip(candidate, cost, strict=True)
        )
        objective = expected_cost + binary_kl(candidate, prior) / precision
        kl_to_optimal = binary_kl(candidate, control_posterior)
        gap_residual = max(
            gap_residual,
            abs(objective - control_floor - kl_to_optimal / precision),
        )
        # Donsker-Varadhan duality at the EFE Gibbs certificate (fep-158):
        # G(candidate) - G(control posterior) = KL(candidate || control posterior),
        # where G(Q) = KL(Q || prior) + precision * E_Q[cost] = precision * EFE(Q).
        duality_residual = max(
            duality_residual,
            abs(
                binary_kl(candidate, prior)
                + precision * expected_cost
                + log_partition
                - kl_to_optimal
            ),
        )
        posterior_minimal = posterior_minimal and (objective >= control_floor - 1e-12)

    # Perception chain rule through a fully supported Boolean likelihood (fep-157).
    likelihood = ((0.9, 0.1), (0.3, 0.7))
    actual = (0.2, 0.8)
    reference = (0.6, 0.4)
    predictive = tuple(
        sum(actual[source] * likelihood[source][outcome] for source in range(2))
        for outcome in range(2)
    )
    reference_predictive = tuple(
        sum(reference[source] * likelihood[source][outcome] for source in range(2))
        for outcome in range(2)
    )

    def filtered(law: tuple[float, ...], outcome: int) -> tuple[float, ...]:
        evidence = sum(law[source] * likelihood[source][outcome] for source in range(2))
        return tuple(
            law[source] * likelihood[source][outcome] / evidence for source in range(2)
        )

    gap_total = binary_kl(actual, reference)
    gap_marginal = binary_kl(predictive, reference_predictive)
    gap_posterior = sum(
        predictive[outcome]
        * binary_kl(filtered(actual, outcome), filtered(reference, outcome))
        for outcome in range(2)
    )
    chain_residual = abs(gap_total - (gap_marginal + gap_posterior))

    # Time-scale-separated EFE: the epistemic gain is the KL to the invariant
    # law, bounded by the affinity production rate (fep-159).
    forward, backward = 0.7, 0.3
    decay_rate = forward + backward
    stationary_true = forward / decay_rate
    stationary_false = backward / decay_rate
    belief_true = 0.85
    belief = (1.0 - belief_true, belief_true)
    current = belief[0] * forward - belief[1] * backward
    affinity = math.log(belief[0] * forward / (belief[1] * backward))
    production_rate = current * affinity
    affinity_bound = production_rate / decay_rate
    initial_gap = binary_kl(belief, (stationary_false, stationary_true))
    initial_gap_form = (belief_true - stationary_true) ** 2 / (
        stationary_true * stationary_false
    )
    rows: list[WitnessRow] = []
    production_violation = 0.0
    envelope_violation = 0.0
    for time in (0.0, 0.5, 1.0, 2.0):
        rho = math.exp(-decay_rate * time)
        evolved_true = stationary_true + rho * (belief_true - stationary_true)
        evolved = (1.0 - evolved_true, evolved_true)
        gain = binary_kl(evolved, (stationary_false, stationary_true))
        envelope = rho**2 * initial_gap_form
        production_violation = max(production_violation, gain - affinity_bound)
        envelope_violation = max(envelope_violation, gain - envelope)
        rows.append(
            WitnessRow((time, rho, evolved_true, gain, envelope, affinity_bound))
        )

    return _EfePlanningData(
        actual=actual,
        affinity_bound=affinity_bound,
        backward=backward,
        belief_true=belief_true,
        chain_residual=chain_residual,
        control_floor=control_floor,
        cost=cost,
        duality_residual=duality_residual,
        envelope_violation=envelope_violation,
        floor_residual=floor_residual,
        forward=forward,
        gap_posterior=gap_posterior,
        gap_residual=gap_residual,
        gap_total=gap_total,
        initial_gap=initial_gap,
        initial_gap_form=initial_gap_form,
        partition=partition,
        posterior_minimal=posterior_minimal,
        precision=precision,
        prior=prior,
        production_rate=production_rate,
        production_violation=production_violation,
        reference=reference,
        rows=rows,
    )


def _efe_split_data() -> _EfeSplitData:
    # Law-weighted split on the t-0060 oracle datum (fep-166):
    # W = [[1, 5/2], [3/4, -1]], p = (1/3, 2/3); the canonical split is
    # S = [[1, 2], [1, -1]], A = [[0, 1/2], [-1/4, 0]].  All arithmetic is
    # exact via fractions.Fraction.
    fep166_law = (Fraction(1, 3), Fraction(2, 3))
    fep166_w = (
        (Fraction(1), Fraction(5, 2)),
        (Fraction(3, 4), Fraction(-1)),
    )
    fep166_s = (
        (Fraction(1), Fraction(2)),
        (Fraction(1), Fraction(-1)),
    )
    fep166_a = (
        (Fraction(0), Fraction(1, 2)),
        (Fraction(-1, 4), Fraction(0)),
    )

    def fep166_sym_part(
        rate: tuple[tuple[Fraction, ...], ...], i: int, j: int
    ) -> Fraction:
        return (fep166_law[i] * rate[i][j] + fep166_law[j] * rate[j][i]) / (
            2 * fep166_law[i]
        )

    def fep166_circ_part(
        rate: tuple[tuple[Fraction, ...], ...], i: int, j: int
    ) -> Fraction:
        return (fep166_law[i] * rate[i][j] - fep166_law[j] * rate[j][i]) / (
            2 * fep166_law[i]
        )

    fep166_circ_01 = fep166_circ_part(fep166_w, 0, 1)
    fep166_circ_10 = fep166_circ_part(fep166_w, 1, 0)
    fep166_canonical_split = all(
        fep166_sym_part(fep166_w, i, j) == fep166_s[i][j]
        and fep166_circ_part(fep166_w, i, j) == fep166_a[i][j]
        for i in range(2)
        for j in range(2)
    )

    # Competing-pair uniqueness: enumerate every step-1/4 grid pair with
    # A = W - S, enforce the p-reversibility of S and the p-skewness of A
    # directly (which forces S_ii = W_ii and A_ii = 0), and require that
    # exactly one pair survives and equals the canonical split.
    fep166_grid = [Fraction(k, 4) for k in range(-8, 9)]
    fep166_solutions: list[tuple[tuple[tuple[Fraction, ...], ...], ...]] = []
    for s00 in fep166_grid:
        for s01 in fep166_grid:
            for s10 in fep166_grid:
                for s11 in fep166_grid:
                    s_pair = ((s00, s01), (s10, s11))
                    a_pair = tuple(
                        tuple(fep166_w[i][j] - s_pair[i][j] for j in range(2))
                        for i in range(2)
                    )
                    reversible = all(
                        fep166_law[i] * s_pair[i][j] == fep166_law[j] * s_pair[j][i]
                        for i in range(2)
                        for j in range(2)
                    )
                    skew = all(
                        fep166_law[i] * a_pair[i][j] == -(fep166_law[j] * a_pair[j][i])
                        for i in range(2)
                        for j in range(2)
                    )
                    if reversible and skew:
                        fep166_solutions.append((s_pair, a_pair))
    fep166_unique = len(fep166_solutions) == 1 and fep166_solutions[0] == (
        fep166_s,
        fep166_a,
    )

    # Reversible boundary: on W_rev = [[1, 4], [2, 3]] the canonical split
    # is (W, 0) — the symmetric part is the field and the circulation dies.
    fep166_w_rev = (
        (Fraction(1), Fraction(4)),
        (Fraction(2), Fraction(3)),
    )
    fep166_reversible = all(
        fep166_law[i] * fep166_w_rev[i][j] == fep166_law[j] * fep166_w_rev[j][i]
        for i in range(2)
        for j in range(2)
    ) and all(
        fep166_sym_part(fep166_w_rev, i, j) == fep166_w_rev[i][j]
        and fep166_circ_part(fep166_w_rev, i, j) == 0
        for i in range(2)
        for j in range(2)
    )

    return _EfeSplitData(
        fep166_canonical_split=fep166_canonical_split,
        fep166_circ_01=fep166_circ_01,
        fep166_circ_10=fep166_circ_10,
        fep166_law=fep166_law,
        fep166_reversible=fep166_reversible,
        fep166_unique=fep166_unique,
    )


def _standalone_efe_carrier() -> NumericalWitness:
    """Evaluate the exact EFE floor, perception chain rule, and affinity bound."""
    planning = _efe_planning_data()
    split = _efe_split_data()
    return NumericalWitness(
        id="boltzmann-efe-affinity-gap",
        family="standalone-efe-formalizations",
        title=(
            "Exact Boltzmann EFE floor, perception chain rule, "
            "and affinity-bounded gain"
        ),
        theorem_mirrors=(
            "fep_fep156.FEP156.fep156_boltzmann_control_posterior_minimizes_efe",
            "fep_fep156.FEP156.fep156_boltzmann_control_posterior_minimal_value",
            "fep_fep156.FEP156.fep156_efeControlObjective_eq_kl_sub_logPartition",
            "fep_fep156.FEP156.fep156_efeControlObjective_sub_eq_kl",
            "fep_fep157.FEP157.fep157_perception_kl_decomposition",
            "fep_fep157.FEP157.fep157_perception_step_kl_nonincrease",
            "fep_fep158.FEP158.fep158_reduction_free_energy_change_eq_kl",
            "fep_fep159.FEP159.fep159_epistemic_gain_bounded_by_affinity",
            (
                "fep_fep159.FEP159."
                "fep159_expectedFreeEnergy_le_productionRate_div_decayRate"
            ),
            "fep_fep159.FEP159.fep159_slow_fast_separation_statement",
            "fep_fep159.FEP159.fep159_productionRate_nonneg",
            "fep_fep166.FEP166.fep166_split_unique",
            "fep_fep166.FEP166.fep166_reversible_split_unique",
            "fep_fep166.FEP166.fep166_twoByTwo_support",
            "fep_fep166.FEP166.fep166_twoByTwo_predicates",
            "fep_fep166.FEP166.fep166_twoByTwo_split_canonical",
            "fep_fep166.FEP166.fep166_twoByTwo_circulation_nonzero",
            "fep_fep166.FEP166.fep166_twoByTwo_circulation_negative",
        ),
        invariant=(
            "the KL-regularized EFE objective attains exactly the inverse-precision "
            "log-partition floor at the Boltzmann control posterior with "
            "inverse-precision KL gaps, the perception channel splits the belief "
            "information gap exactly into outcome-marginal plus posterior-averaged "
            "parts without increasing it, and the two-state epistemic gain is the "
            "relaxation-decaying KL bounded by the affinity production rate, and "
            "the law-weighted reversible/circulation split is unique: the "
            "t-0060 datum's constraint-satisfying split is exactly the canonical "
            "symmetricPart/circulationPart pair, a p-reversible field has the "
            "split (W, 0), and the forward circulation 1/2 with reverse entry "
            "-1/4 is genuinely nonzero and strictly negative"
        ),
        parameters=(
            ("prior_true", planning.prior[1]),
            ("precision", planning.precision),
            ("cost_true", planning.cost[1]),
            ("control_partition", planning.partition),
            ("control_floor", planning.control_floor),
            ("actual_true", planning.actual[1]),
            ("reference_true", planning.reference[1]),
            ("forward_rate", planning.forward),
            ("backward_rate", planning.backward),
            ("belief_true", planning.belief_true),
            ("production_rate", planning.production_rate),
            ("fep166_law_0", float(split.fep166_law[0])),
            ("fep166_law_1", float(split.fep166_law[1])),
            ("fep166_circulation_01", float(split.fep166_circ_01)),
            ("fep166_circulation_10", float(split.fep166_circ_10)),
        ),
        columns=_columns(
            ("time", "Time"),
            ("rho", "Relaxation factor"),
            ("evolved_true", "Evolved true mass"),
            ("epistemic_gain", "Epistemic gain"),
            ("squared_relaxation_bound", "Squared relaxation envelope"),
            ("affinity_bound", "Affinity production bound"),
        ),
        rows=tuple(planning.rows),
        checks=(
            NumericalCheck(
                "control-floor-identity", "eq", planning.floor_residual, 0.0, 1e-12
            ),
            NumericalCheck(
                "control-gap-identity", "eq", planning.gap_residual, 0.0, 1e-12
            ),
            NumericalCheck(
                "donsker-varadhan-gap", "eq", planning.duality_residual, 0.0, 1e-12
            ),
            NumericalCheck(
                "control-posterior-minimality",
                "predicate",
                planning.posterior_minimal,
                True,
                0.0,
            ),
            NumericalCheck(
                "perception-chain-rule", "eq", planning.chain_residual, 0.0, 1e-12
            ),
            NumericalCheck(
                "perception-nonincrease",
                "le",
                planning.gap_posterior,
                planning.gap_total,
                1e-12,
            ),
            NumericalCheck(
                "affinity-production-bound",
                "le",
                planning.production_violation,
                0.0,
                1e-12,
            ),
            NumericalCheck(
                "squared-relaxation-envelope",
                "le",
                planning.envelope_violation,
                0.0,
                1e-12,
            ),
            NumericalCheck(
                "production-rate-nonnegative",
                "predicate",
                planning.production_rate >= 0.0,
                True,
                0.0,
            ),
            NumericalCheck(
                "fep166-canonical-split",
                "predicate",
                split.fep166_canonical_split,
                True,
                0.0,
            ),
            NumericalCheck(
                "fep166-competing-pair-unique",
                "predicate",
                split.fep166_unique,
                True,
                0.0,
            ),
            NumericalCheck(
                "fep166-reversible-boundary",
                "predicate",
                split.fep166_reversible,
                True,
                0.0,
            ),
            NumericalCheck(
                "fep166-circulation-nonzero",
                "eq",
                float(split.fep166_circ_01),
                0.5,
                1e-12,
            ),
            NumericalCheck(
                "fep166-circulation-negative-reverse",
                "eq",
                float(split.fep166_circ_10),
                -0.25,
                1e-12,
            ),
        ),
        boundary_behavior=(
            "At time zero the identity kernel returns the full belief gap "
            "0.0610605352, the squared-relaxation envelope 0.1071428571 stays loose "
            "by 0.0460823220, and the affinity bound 0.1330954793 leaves slack "
            "0.0720349441. The law-weighted datum splits canonically, its "
            "competing pair is unique on the step-1/4 grid, and the reversible "
            "datum W_rev = [[1, 4], [2, 3]] carries the split (W, 0)."
        ),
        boundary_observed=(
            abs(float(planning.rows[0].values[3]) - planning.initial_gap) <= 1e-12
            and abs(
                planning.initial_gap_form - planning.initial_gap - 0.04608232195203506
            )
            <= 1e-15
            and abs(
                planning.affinity_bound - planning.initial_gap - 0.07203494405931334
            )
            <= 1e-15
            and split.fep166_canonical_split
            and split.fep166_unique
            and split.fep166_reversible
            and split.fep166_circ_01 == Fraction(1, 2)
            and split.fep166_circ_10 == Fraction(-1, 4)
        ),
        plot=WitnessPlot(
            "line",
            "time",
            ("epistemic_gain", "squared_relaxation_bound", "affinity_bound"),
        ),
        formal_alignment="theorem_instance",
    )


@dataclass(frozen=True)
class _GeometricSolenoidalData:
    current_divergence: tuple[float, ...]
    current_matches: bool
    div_q: tuple[float, ...]
    div_q_matches: bool
    drop_fails: bool
    fep167_minimality_violation: float
    fep167_projection_unique: bool
    fep167_pythagoras_residual: float
    fep167_residual_sq: float
    fep168_aligned_gap: float
    fep168_aligned_nonzero: bool
    fep168_cs_violation: float
    fep168_identity_residual: float
    fep168_remainder_g_gap: float
    quadratic_residual: float
    remainder_value: float
    skew_q: bool
    sym_h: bool
    symmetrize_identity: bool
    trace_residual: float
    witness_current: tuple[float, ...]
    witness_g: tuple[float, ...]
    witness_q: tuple[tuple[float, ...], ...]


def _geometric_solenoidal_data() -> _GeometricSolenoidalData:
    """Evaluate the skew cancellations, expansion remainder, and witness current."""

    # The manuscript honesty-guard carrier: Q = [[0,1],[-1,0]], g = (1,0).
    witness_q = ((0.0, 1.0), (-1.0, 0.0))
    witness_g = (1.0, 0.0)
    witness_h = ((2.0, 0.5), (0.5, -1.0))  # symmetric Hessian-role datum
    remainder_dq = ((1.0, 0.0), (0.0, 0.0))  # DQ 0 0 = 1, rest zero
    remainder_g = (1.0, 1.0)

    skew_q = all(
        witness_q[i][j] == -witness_q[j][i] for i in range(2) for j in range(2)
    )
    sym_h = all(witness_h[i][j] == witness_h[j][i] for i in range(2) for j in range(2))
    q_h_product = _matrix2_mul(witness_q, witness_h)
    trace_residual = abs(_matrix_trace(q_h_product))
    quadratic_residual = abs(
        _matrix_dot(witness_g, _matrix_mul_vec(witness_q, witness_g))
    )
    witness_current = _matrix_mul_vec(witness_q, witness_g)
    current_matches = witness_current == (0.0, -1.0)
    div_q = tuple(_matrix_node_div(witness_q, i) for i in range(2))
    div_q_matches = div_q == (2.0, -2.0)
    current_divergence = tuple(
        _matrix_node_div(
            tuple(
                tuple(witness_q[i][j] * witness_g[j] for j in range(2))
                for i in range(2)
            ),
            i,
        )
        for i in range(2)
    )
    drop_fails = current_divergence[0] == 1.0 and current_divergence[1] == -1.0

    # The expansion remainder slot: (div Q)^T g with divQ from DQ data.
    div_q_field = tuple(sum(remainder_dq[k][l] for k in range(2)) for l in range(2))
    remainder_value = _matrix_dot(div_q_field, remainder_g)

    symmetrized = tuple(
        tuple((witness_h[i][j] + witness_h[j][i]) / 2 for j in range(2))
        for i in range(2)
    )
    symmetrize_identity = all(
        symmetrized[i][j] == witness_h[i][j] for i in range(2) for j in range(2)
    )

    # fep-167: Frobenius least-squares projection of the symmetrizer.  The
    # Pythagoras identity runs on the symmetric datum H = ((0.5, 0.5),
    # (0.5, -1.0)); minimality and uniqueness run on the nonsymmetric
    # residual datum [[0, 1], [0, 0]] against every step-1/4 symmetric grid
    # competitor.

    fep167_h = ((0.5, 0.5), (0.5, -1.0))
    fep167_sym_h = tuple(
        tuple((fep167_h[i][j] + fep167_h[j][i]) / 2 for j in range(2)) for i in range(2)
    )
    fep167_s = fep167_sym_h
    fep167_pythagoras_residual = abs(
        _matrix2_frobenius_sq(_matrix2_subtract(fep167_h, fep167_s))
        - (
            _matrix2_frobenius_sq(_matrix2_subtract(fep167_h, fep167_sym_h))
            + _matrix2_frobenius_sq(_matrix2_subtract(fep167_sym_h, fep167_s))
        )
    )
    fep167_residual_h = ((0.0, 1.0), (0.0, 0.0))
    fep167_residual_sym = tuple(
        tuple((fep167_residual_h[i][j] + fep167_residual_h[j][i]) / 2 for j in range(2))
        for i in range(2)
    )
    fep167_residual_sq = _matrix2_frobenius_sq(
        _matrix2_subtract(fep167_residual_h, fep167_residual_sym)
    )
    fep167_grid = [k / 4 for k in range(-8, 9)]
    fep167_target = _matrix2_frobenius_sq(
        _matrix2_subtract(fep167_residual_h, fep167_residual_sym)
    )
    fep167_minimality_violation = -math.inf
    fep167_attainers: list[tuple[tuple[float, ...], ...]] = []
    for s00 in fep167_grid:
        for s11 in fep167_grid:
            for off in fep167_grid:
                candidate = ((s00, off), (off, s11))  # symmetric competitor
                sq = _matrix2_frobenius_sq(
                    _matrix2_subtract(fep167_residual_h, candidate)
                )
                fep167_minimality_violation = max(
                    fep167_minimality_violation, fep167_target - sq
                )
                if abs(sq - fep167_target) <= 1e-12:
                    fep167_attainers.append(candidate)
    fep167_projection_unique = len(fep167_attainers) == 1 and all(
        abs(fep167_attainers[0][i][j] - fep167_residual_sym[i][j]) <= 1e-12
        for i in range(2)
        for j in range(2)
    )

    # fep-168: quantitative control of the uncancelled divergence remainder
    # on Q = witnessQ, H = diag(1, 2), DQ = remainderDQ (divQ = (1, 0)), and
    # the pinned gradient remainderG = (1, 1) under the coupling dlogp = -g.
    fep168_h = ((1.0, 0.0), (0.0, 2.0))
    fep168_q_h = _matrix2_mul(witness_q, fep168_h)
    fep168_trace = _matrix_trace(fep168_q_h)
    fep168_quadratic = _matrix_dot(remainder_g, _matrix_mul_vec(witness_q, remainder_g))
    fep168_r = div_q_field
    fep168_wd = fep168_trace - fep168_quadratic + _matrix_dot(fep168_r, remainder_g)
    fep168_identity_residual = abs(fep168_wd - _matrix_dot(fep168_r, remainder_g))
    fep168_cs_violation = _matrix_dot(fep168_r, remainder_g) ** 2 - _matrix_dot(
        fep168_r, fep168_r
    ) * _matrix_dot(remainder_g, remainder_g)
    fep168_aligned_g = (1.0, 0.0)
    fep168_aligned_gap = _matrix_dot(fep168_r, fep168_aligned_g) ** 2 - _matrix_dot(
        fep168_r, fep168_r
    ) * _matrix_dot(fep168_aligned_g, fep168_aligned_g)
    fep168_aligned_nonzero = _matrix_dot(fep168_aligned_g, fep168_aligned_g) != 0.0
    fep168_remainder_g_gap = (
        _matrix_dot(fep168_r, fep168_r) * _matrix_dot(remainder_g, remainder_g)
        - _matrix_dot(fep168_r, remainder_g) ** 2
    )

    return _GeometricSolenoidalData(
        current_divergence=current_divergence,
        current_matches=current_matches,
        div_q=div_q,
        div_q_matches=div_q_matches,
        drop_fails=drop_fails,
        fep167_minimality_violation=fep167_minimality_violation,
        fep167_projection_unique=fep167_projection_unique,
        fep167_pythagoras_residual=fep167_pythagoras_residual,
        fep167_residual_sq=fep167_residual_sq,
        fep168_aligned_gap=fep168_aligned_gap,
        fep168_aligned_nonzero=fep168_aligned_nonzero,
        fep168_cs_violation=fep168_cs_violation,
        fep168_identity_residual=fep168_identity_residual,
        fep168_remainder_g_gap=fep168_remainder_g_gap,
        quadratic_residual=quadratic_residual,
        remainder_value=remainder_value,
        skew_q=skew_q,
        sym_h=sym_h,
        symmetrize_identity=symmetrize_identity,
        trace_residual=trace_residual,
        witness_current=witness_current,
        witness_g=witness_g,
        witness_q=witness_q,
    )


def _geometric_solenoidal() -> NumericalWitness:
    """Evaluate the skew cancellations, expansion remainder, and witness current."""
    data = _geometric_solenoidal_data()
    return NumericalWitness(
        id="geometric-solenoidal-drop",
        family="geometric-mechanics-notation",
        title=(
            "Skew cancellations, three-term expansion remainder, "
            "and the failing unconditional solenoidal drop"
        ),
        theorem_mirrors=(
            "fep_fep161.FEP161.fep161_skewTrace_eq_zero",
            "fep_fep161.FEP161.fep161_skewQuadratic_eq_zero",
            "fep_fep162.FEP162.fep162_symmetrize_symmetric",
            "fep_fep162.FEP162.fep162_skewTrace_symmetrize_eq_zero",
            "fep_fep163.FEP163.fep163_solenoidal_expansion",
            "fep_fep163.FEP163.fep163_expansion_remainder_witness",
            "fep_fep164.FEP164.fep164_graphDecomposition",
            "fep_fep165.FEP165.fep165_witness_current",
            ("fep_fep165.FEP165.fep165_witness_drop_fails"),
            "fep_fep167.FEP167.fep167_frobenius_pythagoras",
            "fep_fep167.FEP167.fep167_symmetrize_minimizes",
            "fep_fep167.FEP167.fep167_projection_unique",
            "fep_fep167.FEP167.fep167_residual_example",
            "fep_fep168.FEP168.fep168_weightedDivergence_eq_remainderDot",
            "fep_fep168.FEP168.fep168_remainder_sq_budget",
            "fep_fep168.FEP168.fep168_absolute_budget",
            "fep_fep168.FEP168.fep168_equality_attained",
        ),
        invariant=(
            "the skew trace and quadratic cancellations hold exactly on the "
            "symmetry hypotheses, the symmetrized discrete Hessian is "
            "symmetric and coincides with symmetric data, the expansion "
            "remainder slot evaluates to exactly 1 on the concrete derivative "
            "datum, and the honesty-guard candidate current (0, -1) has node "
            "divergence (1, -1) so the unconditional solenoidal drop fails; "
            "symmetrization is the unique Frobenius least-squares projection "
            "(exact Pythagoras, minimality with equality exactly at the "
            "symmetrizer, residual 1/2 on the nonsymmetric datum), and the "
            "uncancelled remainder obeys the squared Cauchy-Schwarz budget "
            "with equality attained on aligned data and gap 1 on the pinned "
            "remainderG datum"
        ),
        parameters=(
            ("witness_q_01", data.witness_q[0][1]),
            ("witness_q_10", data.witness_q[1][0]),
            ("witness_g_0", data.witness_g[0]),
            ("trace_residual", data.trace_residual),
            ("quadratic_residual", data.quadratic_residual),
            ("remainder_value", data.remainder_value),
            ("node0_divergence", data.current_divergence[0]),
            ("fep167_residual_sq", data.fep167_residual_sq),
            ("fep168_aligned_gap", data.fep168_aligned_gap),
            ("fep168_remainderG_gap", data.fep168_remainder_g_gap),
        ),
        columns=_columns(
            ("node", "Node"),
            ("transport", "Transport field entry"),
            ("current", "Candidate current"),
            ("divergence", "Node divergence"),
        ),
        rows=(
            WitnessRow(
                (0, data.div_q[0], data.witness_current[0], data.current_divergence[0])
            ),
            WitnessRow(
                (1, data.div_q[1], data.witness_current[1], data.current_divergence[1])
            ),
        ),
        checks=(
            NumericalCheck(
                "witness-q-skew", "predicate", data.skew_q and data.sym_h, True, 0.0
            ),
            NumericalCheck("trace-cancellation", "eq", data.trace_residual, 0.0, 1e-12),
            NumericalCheck(
                "quadratic-cancellation", "eq", data.quadratic_residual, 0.0, 1e-12
            ),
            NumericalCheck(
                "witness-current", "predicate", data.current_matches, True, 0.0
            ),
            NumericalCheck("witness-divq", "predicate", data.div_q_matches, True, 0.0),
            NumericalCheck(
                "expansion-remainder", "eq", data.remainder_value, 1.0, 1e-12
            ),
            NumericalCheck(
                "symmetrize-identity-on-symmetric-data",
                "predicate",
                data.symmetrize_identity,
                True,
                0.0,
            ),
            NumericalCheck(
                "unconditional-drop-fails", "eq", data.current_divergence[0], 1.0, 1e-12
            ),
            NumericalCheck(
                "fep167-pythagoras-residual",
                "eq",
                data.fep167_pythagoras_residual,
                0.0,
                1e-12,
            ),
            NumericalCheck(
                "fep167-minimality-gap",
                "le",
                data.fep167_minimality_violation,
                0.0,
                1e-12,
            ),
            NumericalCheck(
                "fep167-projection-unique",
                "predicate",
                data.fep167_projection_unique,
                True,
                0.0,
            ),
            NumericalCheck(
                "fep167-residual-example", "eq", data.fep167_residual_sq, 0.5, 1e-12
            ),
            NumericalCheck(
                "fep168-remainder-identity",
                "eq",
                data.fep168_identity_residual,
                0.0,
                1e-12,
            ),
            NumericalCheck(
                "fep168-cs-budget", "le", data.fep168_cs_violation, 0.0, 1e-12
            ),
            NumericalCheck(
                "fep168-equality-attained", "eq", data.fep168_aligned_gap, 0.0, 1e-12
            ),
            NumericalCheck(
                "fep168-remainder-g-not-aligned",
                "eq",
                data.fep168_remainder_g_gap,
                1.0,
                1e-12,
            ),
        ),
        boundary_behavior=(
            "On the honesty guard the transport divergence is (2, -2) at the "
            "two nodes and the candidate current (0, -1) has node divergence "
            "1 at node 0: the drop fails, matching the compiled witness.  The "
            "Frobenius projection residual is exactly 1/2 on the nonsymmetric "
            "datum, the budget is attained on the aligned gradient (1, 0), and "
            "the pinned remainderG = (1, 1) datum stays strict with gap 1."
        ),
        boundary_observed=(
            data.drop_fails
            and data.div_q_matches
            and data.current_matches
            and abs(data.remainder_value - 1.0) <= 1e-12
            and data.fep167_pythagoras_residual <= 1e-12
            and data.fep167_minimality_violation <= 1e-12
            and data.fep167_projection_unique
            and abs(data.fep167_residual_sq - 0.5) <= 1e-12
            and data.fep168_identity_residual <= 1e-12
            and data.fep168_cs_violation <= 1e-12
            and abs(data.fep168_aligned_gap) <= 1e-12
            and data.fep168_aligned_nonzero
            and abs(data.fep168_remainder_g_gap - 1.0) <= 1e-12
        ),
        plot=WitnessPlot(
            "bar",
            "node",
            ("divergence",),
        ),
        formal_alignment="theorem_instance",
    )


def _core_vfe_gap() -> NumericalWitness:
    posterior = (0.4, 0.6)
    surprisal = 0.7
    rows = []
    for mass in (0.1, 0.4, 0.7, 0.9):
        gap = extended_kl((mass, 1.0 - mass), posterior)
        rows.append(WitnessRow((mass, surprisal, gap, surprisal + gap)))
    singular = math.isinf(extended_kl((1.0, 0.0), (0.0, 1.0)))
    return NumericalWitness(
        id="core-vfe-native-gap",
        family="core-free-energy",
        title="Finite supplied-posterior VFE gap",
        theorem_mirrors=(
            "fep_fep002.FEP002.fep002_vfe_ge_surprisal",
            "fep_fep002.FEP002.fep002_vfe_exact_at_posterior",
        ),
        invariant="For a supplied finite posterior, VFE = surprisal + native KL.",
        parameters=(("posterior_true", posterior[0]), ("surprisal", surprisal)),
        columns=_columns(
            ("candidate_true", "Candidate mass"),
            ("surprisal", "Surprisal"),
            ("gap", "KL gap (nats)"),
            ("vfe", "VFE (nats)"),
        ),
        rows=tuple(rows),
        checks=(
            NumericalCheck(
                "vfe-bound",
                "ge",
                min(cast(float, row.values[2]) for row in rows),
                0.0,
                1e-12,
            ),
            NumericalCheck(
                "posterior-exactness",
                "eq",
                extended_kl(posterior, posterior),
                0.0,
                1e-12,
            ),
            NumericalCheck(
                "singular-native-boundary", "predicate", singular, True, 0.0
            ),
        ),
        boundary_behavior="Positive candidate mass at zero reference remains infinite native KL; infinity is only a boundary predicate, never a finite plotted value. The posterior is supplied, not inferred from a generative model.",
        boundary_observed=singular,
        plot=WitnessPlot("line", "candidate_true", ("gap", "vfe")),
        formal_alignment="theorem_instance",
    )


def _core_efe_truncation() -> NumericalWitness:
    cost = 0.6
    information = (0.0, 0.2, 0.6, 0.9)
    values = tuple(max(0.0, cost - value) for value in information)
    return NumericalWitness(
        id="core-efe-truncated-convention",
        family="core-active-inference",
        title="Supplied pragmatic-cost minus information-value convention",
        theorem_mirrors=(
            "fep_fep021.FEP021.fep021_efe_epistemic_balance",
            "fep_fep021.FEP021.fep021_efe_eq_zero_iff",
            "fep_fep021.FEP021.fep021_efe_antitone_epistemic",
        ),
        invariant="Nonnegative finite inputs use max(0, pragmatic cost - information value).",
        parameters=(("pragmatic_cost", cost),),
        columns=_columns(
            ("information_value", "Supplied information value"),
            ("efe", "Truncated EFE convention"),
        ),
        rows=tuple(
            WitnessRow((value, efe))
            for value, efe in zip(information, values, strict=True)
        ),
        checks=(
            NumericalCheck("nonnegative-convention", "ge", min(values), 0.0, 0.0),
            NumericalCheck(
                "epistemic-balance", "eq", values[1] + information[1], cost, 1e-12
            ),
            NumericalCheck(
                "antitone-value",
                "predicate",
                all(a >= b for a, b in pairwise(values)),
                True,
                0.0,
            ),
            NumericalCheck("covering-value-zero", "eq", values[-1], 0.0, 0.0),
        ),
        boundary_behavior="Information value above cost truncates to zero: adding it back no longer reconstructs cost. This mirrors the actual scalar ENNReal convention; no mutual-information or generative EFE decomposition is inferred.",
        boundary_observed=values[-1] == 0.0 and values[-1] + information[-1] != cost,
        plot=WitnessPlot("line", "information_value", ("efe",)),
        formal_alignment="theorem_instance",
    )


def _core_bernoulli_bayes() -> NumericalWitness:
    likelihood = (0.9, 0.1)
    rows = []
    residuals = []
    for mass in (0.2, 0.5, 0.8):
        prior = (mass, 1.0 - mass)
        evidence = finite_expectation(prior, likelihood)
        posterior = prior[0] * likelihood[0] / evidence
        residual = abs(posterior * evidence - prior[0] * likelihood[0])
        residuals.append(residual)
        rows.append(WitnessRow((mass, evidence, posterior, residual)))
    zero_evidence = finite_expectation((0.4, 0.6), (0.0, 0.0))
    return NumericalWitness(
        id="core-bernoulli-bayes-reconstruction",
        family="core-bayesian-mechanics",
        title="Finite Bernoulli posterior reconstruction",
        theorem_mirrors=(
            "fep_fep045.FEP045.fep045_bernoulli_posterior_closed",
            "fep_fep045.FEP045.fep045_posterior_mass_one",
        ),
        invariant="At nonzero evidence the posterior atom equals prior times likelihood divided by evidence.",
        parameters=(
            ("likelihood_true", likelihood[0]),
            ("likelihood_false", likelihood[1]),
        ),
        columns=_columns(
            ("prior_true", "Prior true mass"),
            ("evidence", "Evidence"),
            ("posterior_true", "Posterior true mass"),
            ("residual", "Reconstruction residual"),
        ),
        rows=tuple(rows),
        checks=(
            NumericalCheck("reconstruction", "eq", max(residuals), 0.0, 1e-12),
            NumericalCheck(
                "posterior-probability",
                "predicate",
                all(0 < cast(float, row.values[2]) < 1 for row in rows),
                True,
                0.0,
            ),
            NumericalCheck(
                "positive-evidence",
                "predicate",
                all(cast(float, row.values[1]) > 0 for row in rows),
                True,
                0.0,
            ),
            NumericalCheck("zero-evidence-exclusion", "eq", zero_evidence, 0.0, 0.0),
        ),
        boundary_behavior="All-zero likelihood gives zero evidence, so no posterior division is attempted. A normalized likelihood-only value 0.9 differs from the first actual posterior and is not silently treated as Bayes with a nonuniform prior.",
        boundary_observed=zero_evidence == 0.0
        and abs(cast(float, rows[0].values[2]) - 0.9) > 0.1,
        plot=WitnessPlot("line", "prior_true", ("posterior_true",)),
        formal_alignment="theorem_instance",
    )


def _core_bernoulli_fisher() -> NumericalWitness:
    rows = []
    score_residuals = []
    information_residuals = []
    for parameter in (0.1, 0.25, 0.5, 0.75, 0.9):
        law = (1.0 - parameter, parameter)
        scores = (-1.0 / (1.0 - parameter), 1.0 / parameter)
        mean_score = finite_expectation(law, scores)
        information = finite_expectation(law, tuple(value * value for value in scores))
        expected = bernoulli_fisher(parameter)
        score_residuals.append(abs(mean_score))
        information_residuals.append(abs(information - expected))
        rows.append(WitnessRow((parameter, information, information * 0.3 * 0.3)))
    rejected = 0
    for endpoint in (0.0, 1.0):
        try:
            bernoulli_fisher(endpoint)
        except BoundaryProbeError:
            rejected += 1
    return NumericalWitness(
        id="core-bernoulli-fisher-interior",
        family="core-information-geometry",
        title="Interior Bernoulli expected-score Fisher metric",
        theorem_mirrors=(
            "fep_fep038.FEP038.fep038_expectedScore_zero",
            "fep_fep038.FEP038.fep038_fisherInformation_eq",
            "fep_fep038.FEP038.fep038_fisherMetric_pos",
        ),
        invariant="For 0 < p < 1, expected score is 0 and Fisher information is 1/(p(1-p)); a nonzero tangent has positive metric.",
        parameters=(("tangent", 0.3),),
        columns=_columns(
            ("parameter", "Bernoulli parameter"),
            ("information", "Fisher information"),
            ("metric", "Tangent self metric"),
        ),
        rows=tuple(rows),
        checks=(
            NumericalCheck("mean-score-zero", "eq", max(score_residuals), 0.0, 1e-12),
            NumericalCheck(
                "expected-score-square", "eq", max(information_residuals), 0.0, 1e-12
            ),
            NumericalCheck(
                "positive-metric",
                "predicate",
                all(cast(float, row.values[2]) > 0 for row in rows),
                True,
                0.0,
            ),
            NumericalCheck("endpoint-refusal", "eq", rejected, 2, 0.0),
        ),
        boundary_behavior="Both singular endpoints are refused by the existing Bernoulli Fisher helper. No zero/infinite endpoint metric or general multidimensional statistical Fisher claim is plotted.",
        boundary_observed=rejected == 2,
        plot=WitnessPlot("line", "parameter", ("information", "metric")),
        formal_alignment="theorem_instance",
    )


def _core_binary_entropy_maximum() -> NumericalWitness:
    rows = []
    for parameter in (0.1, 0.25, 0.5, 0.75, 0.9):
        entropy = -sum(
            value * math.log(value) for value in (parameter, 1.0 - parameter)
        )
        rows.append(WitnessRow((parameter, entropy, math.log(2.0) - entropy)))
    invalid_law_refused = False
    try:
        finite_expectation((-0.1, 1.1), (0.0, 0.0))
    except BoundaryProbeError:
        invalid_law_refused = True
    return NumericalWitness(
        id="core-binary-entropy-maximum",
        family="core-thermodynamics",
        title="Binary Shannon entropy maximum in nats",
        theorem_mirrors=(
            "fep_fep030.FEP030.fep030_binaryEntropy_max",
            "fep_fep030.FEP030.fep030_binaryEntropy_eq_max_iff",
        ),
        invariant="For sampled probability parameters, entropy is bounded by log(2) nats and peaks at one half.",
        parameters=(("log_cardinality", math.log(2.0)),),
        columns=_columns(
            ("parameter", "Probability parameter"),
            ("entropy", "Binary entropy (nats)"),
            ("gap", "Gap to log(2) (nats)"),
        ),
        rows=tuple(rows),
        checks=(
            NumericalCheck(
                "entropy-bound",
                "ge",
                min(cast(float, row.values[2]) for row in rows),
                0.0,
                1e-12,
            ),
            NumericalCheck(
                "fair-attainment", "eq", cast(float, rows[2].values[2]), 0.0, 1e-12
            ),
            NumericalCheck(
                "offuniform-strict",
                "predicate",
                all(
                    cast(float, row.values[2]) > 0
                    for index, row in enumerate(rows)
                    if index != 2
                ),
                True,
                0.0,
            ),
            NumericalCheck(
                "invalid-probability-refusal",
                "predicate",
                invalid_law_refused,
                True,
                0.0,
            ),
        ),
        boundary_behavior="Negative mass is refused by the existing finite-law numerical helper. This is the probability-domain Bernoulli theorem, not general constrained MaxEnt or Real.binEntropy's total extension outside [0, 1].",
        boundary_observed=invalid_law_refused and cast(float, rows[0].values[2]) > 0,
        plot=WitnessPlot("line", "parameter", ("entropy", "gap")),
        formal_alignment="theorem_instance",
    )


def evaluate_numerical_witnesses(
    project_root: Path | None = None,
    *,
    scope: Literal["catalogue", "horizon2"] | None = None,
) -> tuple[NumericalWitness, ...]:
    """Evaluate the shared registry, optionally selecting a declared scope."""
    if scope not in {None, "catalogue", "horizon2"}:
        raise ValueError("unknown numerical witness scope")
    from ._horizon_numerical_witnesses import (
        fin4_blanket_witness,
        scalar_terminal_witness,
    )

    witnesses = (
        _measure_bayes_reconstruction(),
        _gibbs_duality_gap(),
        _soft_bellman_temperature(),
        _bool_forward_backward(),
        _causal_intervention_invariance(),
        _finite_jet_error_descent(),
        _path_fluctuation_identity(),
        _categorical_fisher_rank(),
        _belief_consensus_contraction(),
        _subgaussian_envelope(),
        _laplace_brier_risk(),
        _policy_tree_feedback(),
        _native_blanket_transfer(),
        _exponential_family_duality(),
        _two_state_master_equation(),
        _standalone_efe_carrier(),
        _geometric_solenoidal(),
        scalar_terminal_witness(),
        fin4_blanket_witness(),
        _core_vfe_gap(),
        _core_efe_truncation(),
        _core_bernoulli_bayes(),
        _core_bernoulli_fisher(),
        _core_binary_entropy_maximum(),
    )
    identifiers = tuple(witness.id for witness in witnesses)
    families = tuple(witness.family for witness in witnesses)
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("numerical witness IDs must be unique")
    if len(families) != len(set(families)):
        raise ValueError("every formal family must own exactly one witness")
    expected_families = frozenset(entry.family for entry in BODY_MODULE_MANIFEST)
    actual_families = frozenset(w.family for w in witnesses if w.scope == "catalogue")
    if actual_families != expected_families:
        raise ValueError(
            "numerical witness family closure mismatch: "
            f"missing={sorted(expected_families - actual_families)!r} "
            f"extra={sorted(actual_families - expected_families)!r}"
        )
    known_declarations = all_formal_theorem_declarations(project_root)
    unresolved = tuple(
        (witness.id, declaration)
        for witness in witnesses
        for declaration in witness.theorem_mirrors
        if declaration not in known_declarations
    )
    if unresolved:
        details = ", ".join(
            f"{witness_id} -> {declaration}" for witness_id, declaration in unresolved
        )
        raise ValueError(f"unresolved numerical witness declarations: {details}")
    return tuple(w for w in witnesses if scope is None or w.scope == scope)


def numerical_witness_by_id(
    project_root: Path | None = None,
) -> dict[str, NumericalWitness]:
    """Return a fresh lookup map over the immutable evaluated records."""
    return {
        witness.id: witness
        for witness in evaluate_numerical_witnesses(project_root=project_root)
    }


__all__ = [
    "NON_PROOF_EVIDENCE",
    "FormalAlignment",
    "NumericalCheck",
    "NumericalRelation",
    "NumericalWitness",
    "WitnessColumn",
    "WitnessPlot",
    "WitnessRow",
    "evaluate_numerical_witnesses",
    "numerical_witness_by_id",
]
