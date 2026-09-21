"""Restricted static-AST extraction of PyMDP runner table literals (Q5 slice).

This module is the extraction boundary of the GNN bridge Q5 artifact-proof
slice (``specs/gnn-bridge-q5-artifact-proof``). It parses a rendered pymdp
runner with the stdlib ``ast`` module — no import, no execution — and reads
the five embedded table literals (``A_data``, ``B_data``, ``C_data``,
``D_data``, ``E_data``) under the frozen pymdp layout:

- ``A_data[outcome][state]`` (``(num_obs, num_states)``),
- ``B_data[next][previous][policy]`` (canonical pymdp shape; the P1 runner's
  embedded ``matrix_provenance["B"].source_order`` makes
  ``_b_order_from_provenance`` treat the tensor as already canonical),
- ``C_data``/``D_data``/``E_data`` over outcome/state/policy respectively.

The contract is fail-closed: any deviation from a single straight-line
literal assignment per table — duplicate assignment, reassignment,
conditional or nested dataflow, unsupported expressions, non-finite or
non-dyadic literals, ragged or wrongly shaped tables, negative entries, or a
normalization violation in exact arithmetic — raises :class:`ArtifactProofError`
with a machine-readable reason. Values convert to exact
:class:`fractions.Fraction`; nothing is ever rounded.

Scope discipline (slice README non-goals): this module proves nothing about
Python semantics, the pymdp runtime, or GNN pipeline behavior; it is a
boundary reader for one frozen artifact family.
"""

from __future__ import annotations

import ast
import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from math import isfinite
from pathlib import Path
from typing import Any, Final

from fep_lean.bridge.custody import contained_file
from fep_lean.verification._jsonutil import load_strict_json

__all__ = [
    "DISCRETE_BOOL_SHAPES",
    "PYMDP_TABLE_NAMES",
    "ArtifactProofError",
    "PymdpArtifactTables",
    "TableValue",
    "extract_pymdp_tables",
    "manifest_mismatches",
    "render_lean_probe",
    "render_manifest",
    "sha256_file_strict",
]

PYMDP_TABLE_NAMES: Final[tuple[str, ...]] = (
    "A_data",
    "B_data",
    "C_data",
    "D_data",
    "E_data",
)

#: Declared shapes of the concrete discrete Boolean artifact family (Q2/Q4
#: carriers: State = Outcome = Policy = Bool).
DISCRETE_BOOL_SHAPES: Final[Mapping[str, tuple[int, ...]]] = {
    "A_data": (2, 2),
    "B_data": (2, 2, 2),
    "C_data": (2,),
    "D_data": (2,),
    "E_data": (2,),
}

_AMBIGUOUS_ANCESTORS: Final[tuple[type[ast.stmt], ...]] = (
    ast.If,
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.Try,
    ast.TryStar,
    ast.With,
    ast.AsyncWith,
    ast.Match,
)


class ArtifactProofError(Exception):
    """A fail-closed extraction rejection, carrying a reason code."""

    def __init__(self, reason: str, detail: str) -> None:
        super().__init__(f"{reason}: {detail}")
        self.reason = reason
        self.detail = detail


@dataclass(frozen=True)
class TableValue:
    """A rectangular table of exact rationals, stored row-major."""

    shape: tuple[int, ...]
    values: tuple[Fraction, ...]

    def get(self, indices: Sequence[int]) -> Fraction:
        if len(indices) != len(self.shape):
            raise ArtifactProofError(
                "internal_error", f"index arity {len(indices)} != shape {self.shape}"
            )
        flat = 0
        for index, size in zip(indices, self.shape, strict=True):
            if not 0 <= index < size:
                raise ArtifactProofError(
                    "internal_error", f"index {index} out of range for {self.shape}"
                )
            flat = flat * size + index
        return self.values[flat]

    def entries(self) -> tuple[tuple[tuple[int, ...], Fraction], ...]:
        """All ``(indices, value)`` pairs in row-major order."""
        out: list[tuple[tuple[int, ...], Fraction]] = []
        cursor = [0] * len(self.shape)

        def walk(dimension: int) -> None:
            if dimension == len(self.shape):
                out.append(
                    (tuple(cursor), self.values[_flat_index(self.shape, cursor)])
                )
                return
            for index in range(self.shape[dimension]):
                cursor[dimension] = index
                walk(dimension + 1)

        walk(0)
        return tuple(out)


def _flat_index(shape: tuple[int, ...], indices: Sequence[int]) -> int:
    flat = 0
    for index, size in zip(indices, shape, strict=True):
        flat = flat * size + index
    return flat


@dataclass(frozen=True)
class PymdpArtifactTables:
    """The five extracted tables plus the digest of the source they came from."""

    source_sha256: str
    tables: Mapping[str, TableValue]

    def table(self, name: str) -> TableValue:
        return self.tables[name]


def sha256_file_strict(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _literal_fraction(node: ast.expr, source_text: str) -> Fraction:
    """Exact rational of a numeric literal node, rejecting non-dyadic values."""
    if not isinstance(node, ast.Constant) or type(node.value) not in (int, float):
        raise ArtifactProofError(
            "unsupported_expression",
            f"line {node.lineno}: table entries must be numeric literals",
        )
    if isinstance(node.value, float) and not isfinite(node.value):
        raise ArtifactProofError(
            "non_finite_value", f"line {node.lineno}: non-finite numeric literal"
        )
    segment = ast.get_source_segment(source_text, node) or ast.unparse(node)
    try:
        exact = Decimal(segment)
    except (
        InvalidOperation
    ) as error:  # pragma: no cover - unparse always yields a number
        raise ArtifactProofError(
            "unsupported_expression",
            f"line {node.lineno}: unparsable literal {segment!r}",
        ) from error
    fraction = Fraction(exact)
    if fraction.denominator & (fraction.denominator - 1) != 0:
        raise ArtifactProofError(
            "non_dyadic_value",
            f"line {node.lineno}: {segment} is not dyadic (denominator "
            f"{fraction.denominator} is not a power of two); refusing to round",
        )
    return fraction


def _literal_table(
    node: ast.expr, source_text: str
) -> tuple[tuple[int, ...], tuple[Fraction, ...]]:
    """Shape and row-major values of a literal nested list/tuple."""
    if isinstance(node, ast.Constant):
        return (), (_literal_fraction(node, source_text),)
    if not isinstance(node, ast.List | ast.Tuple):
        raise ArtifactProofError(
            "unsupported_expression",
            f"line {node.lineno}: table must be a literal list/tuple "
            f"(got {type(node).__name__})",
        )
    if not node.elts:
        raise ArtifactProofError("ragged_table", f"line {node.lineno}: empty table row")
    first_shape, _ = _literal_table(node.elts[0], source_text)
    shape = (len(node.elts), *first_shape)
    values: list[Fraction] = []
    for element in node.elts:
        element_shape, element_values = _literal_table(element, source_text)
        if element_shape != first_shape:
            raise ArtifactProofError(
                "ragged_table",
                f"line {node.lineno}: table rows have differing shapes",
            )
        values.extend(element_values)
    return shape, tuple(values)


def _target_names(target: ast.expr) -> list[str]:
    """Names bound by an assignment target, including subscript mutations."""
    if isinstance(target, ast.Name):
        return [target.id]
    if isinstance(target, ast.Starred):
        return _target_names(target.value)
    if isinstance(target, ast.Subscript):
        return _target_names(target.value)
    if isinstance(target, ast.Attribute):
        return _target_names(target.value)
    if isinstance(target, ast.List | ast.Tuple):
        names: list[str] = []
        for element in target.elts:
            names.extend(_target_names(element))
        return names
    return []


def _base_names(node: ast.expr) -> list[str]:
    """Names along an attribute/subscript base chain (``A_data[0].append``)."""
    if isinstance(node, ast.Name):
        return [node.id]
    if isinstance(node, ast.Attribute | ast.Subscript):
        return _base_names(node.value)
    return []


def _extract_single(
    tree: ast.Module,
    source_text: str,
    name: str,
    parents: Mapping[ast.AST, ast.AST],
) -> TableValue:
    """The single straight-line literal assignment of ``name``, fail-closed."""
    assignments: list[ast.Assign | ast.AnnAssign] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            matched = [
                target for target in node.targets if name in _target_names(target)
            ]
            if not matched:
                continue
            if len(node.targets) != 1:
                raise ArtifactProofError(
                    "unsupported_expression",
                    f"line {node.lineno}: multi-target assignment of {name}",
                )
            if not isinstance(matched[0], ast.Name):
                raise ArtifactProofError(
                    "reassignment",
                    f"line {node.lineno}: in-place subscript/attribute mutation "
                    f"of {name}",
                )
            assignments.append(node)
        elif isinstance(node, ast.AnnAssign) and name in _target_names(node.target):
            if node.value is None:
                continue
            if not isinstance(node.target, ast.Name):
                raise ArtifactProofError(
                    "reassignment",
                    f"line {node.lineno}: annotated subscript mutation of {name}",
                )
            assignments.append(node)
        elif isinstance(node, ast.AugAssign) and name in _target_names(node.target):
            raise ArtifactProofError(
                "reassignment", f"line {node.lineno}: augmented reassignment of {name}"
            )
        elif isinstance(node, ast.Delete) and any(
            name in _target_names(target) for target in node.targets
        ):
            raise ArtifactProofError(
                "reassignment", f"line {node.lineno}: {name} is deleted"
            )
        elif isinstance(node, ast.NamedExpr) and name in _target_names(node.target):
            raise ArtifactProofError(
                "ambiguous_dataflow",
                f"line {node.lineno}: {name} bound by a walrus expression",
            )
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and name in _base_names(node.func)
        ):
            raise ArtifactProofError(
                "unsupported_expression",
                f"line {node.lineno}: method call on {name} "
                f"(e.g. append/insert/copy) is not a frozen-literal dataflow",
            )
        elif isinstance(node, ast.For | ast.AsyncFor | ast.comprehension) and name in (
            _target_names(node.target)
        ):
            raise ArtifactProofError(
                "ambiguous_dataflow",
                f"{name} is bound by a loop/comprehension target",
            )
        elif (
            isinstance(node, ast.withitem)
            and node.optional_vars is not None
            and name in _target_names(node.optional_vars)
        ):
            raise ArtifactProofError(
                "ambiguous_dataflow", f"{name} is bound by a with target"
            )

    if not assignments:
        raise ArtifactProofError("missing_assignment", f"no assignment of {name} found")
    if len(assignments) > 1:
        lines = ", ".join(str(node.lineno) for node in assignments)
        raise ArtifactProofError(
            "duplicate_assignment", f"{name} assigned at lines {lines}"
        )

    assignment = assignments[0]
    for ancestor in _ancestors(assignment, parents):
        if isinstance(ancestor, _AMBIGUOUS_ANCESTORS):
            raise ArtifactProofError(
                "ambiguous_dataflow",
                f"line {assignment.lineno}: {name} assigned under "
                f"{type(ancestor).__name__}",
            )
        if isinstance(ancestor, ast.Lambda | ast.ClassDef):
            raise ArtifactProofError(
                "ambiguous_dataflow",
                f"line {assignment.lineno}: {name} assigned inside "
                f"{type(ancestor).__name__}",
            )
    functions = [
        ancestor
        for ancestor in _ancestors(assignment, parents)
        if isinstance(ancestor, ast.FunctionDef | ast.AsyncFunctionDef)
    ]
    if len(functions) > 1:
        raise ArtifactProofError(
            "ambiguous_dataflow",
            f"line {assignment.lineno}: {name} assigned in a nested function scope",
        )
    if len(functions) != 1 or functions[0].name != "main":
        scope = functions[0].name if functions else "<module>"
        raise ArtifactProofError(
            "ambiguous_dataflow",
            f"line {assignment.lineno}: {name} must be assigned exactly once "
            f"inside main() (found scope {scope})",
        )

    value = assignment.value
    assert value is not None  # both accepted assignment forms carry a value
    shape, values = _literal_table(value, source_text)
    return TableValue(shape=shape, values=values)


def _ancestors(node: ast.AST, parents: Mapping[ast.AST, ast.AST]) -> list[ast.AST]:
    chain: list[ast.AST] = []
    cursor: ast.AST | None = parents.get(node)
    while cursor is not None:
        chain.append(cursor)
        cursor = parents.get(cursor)
    return chain


def _reject_shadows(tree: ast.Module) -> None:
    """Reject any non-assignment binding of a tracked table name."""
    for node in ast.walk(tree):
        detail: str | None = None
        if (
            isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef)
            and node.name in PYMDP_TABLE_NAMES
        ):
            detail = f"line {node.lineno}: {type(node).__name__} shadows {node.name}"
        elif isinstance(node, ast.Import):
            for alias in node.names:
                bound = alias.asname or alias.name.split(".")[0]
                if bound in PYMDP_TABLE_NAMES:
                    detail = f"line {node.lineno}: import binds {bound}"
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                bound = alias.asname or alias.name
                if bound in PYMDP_TABLE_NAMES:
                    detail = f"line {node.lineno}: import binds {bound}"
        elif isinstance(node, ast.ExceptHandler) and node.name in PYMDP_TABLE_NAMES:
            detail = f"line {node.lineno}: except handler binds {node.name}"
        elif isinstance(node, ast.MatchAs) and node.name in PYMDP_TABLE_NAMES:
            detail = f"line {node.lineno}: match capture binds {node.name}"
        elif isinstance(node, ast.MatchStar) and node.name in PYMDP_TABLE_NAMES:
            detail = f"line {node.lineno}: match star binds {node.name}"
        elif isinstance(node, ast.MatchMapping) and node.rest in PYMDP_TABLE_NAMES:
            detail = f"line {node.lineno}: match mapping binds {node.rest}"
        elif isinstance(node, ast.Global | ast.Nonlocal) and any(
            declared in PYMDP_TABLE_NAMES for declared in node.names
        ):
            detail = f"line {node.lineno}: global/nonlocal declares a table name"
        if detail is not None:
            raise ArtifactProofError("shadowed_name", detail)


def _require_unique_main(tree: ast.Module) -> None:
    """All table assignments belong to one unique top-level non-async main()."""
    mains = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "main"
    ]
    async_mains = [
        node
        for node in tree.body
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "main"
    ]
    if len(mains) != 1 or async_mains:
        raise ArtifactProofError(
            "ambiguous_dataflow",
            "expected exactly one top-level non-async main() owning the "
            "table assignments "
            f"(found {len(mains)} main, {len(async_mains)} async main)",
        )


def extract_pymdp_tables(
    source_text: str,
    *,
    shapes: Mapping[str, tuple[int, ...]] = DISCRETE_BOOL_SHAPES,
    source_name: str = "<pymdp runner>",
) -> PymdpArtifactTables:
    """Extract the five frozen-layout tables from a pymdp runner, fail-closed."""
    try:
        tree = ast.parse(source_text, filename=source_name)
    except SyntaxError as error:
        raise ArtifactProofError("syntax_error", str(error)) from error
    _reject_shadows(tree)
    _require_unique_main(tree)
    parents: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent

    tables: dict[str, TableValue] = {}
    for name in PYMDP_TABLE_NAMES:
        value = _extract_single(tree, source_text, name, parents)
        expected = shapes.get(name)
        if expected is None:
            raise ArtifactProofError("shape_mismatch", f"no declared shape for {name}")
        if value.shape != expected:
            raise ArtifactProofError(
                "shape_mismatch",
                f"{name} has shape {value.shape}, declared {expected}",
            )
        tables[name] = value

    _require_normalized(tables)
    return PymdpArtifactTables(
        source_sha256=hashlib.sha256(source_text.encode("utf-8")).hexdigest(),
        tables=tables,
    )


def _require_normalized(tables: Mapping[str, TableValue]) -> None:
    """Exact-arithmetic normalization under the frozen pymdp layout."""
    for name, value in tables.items():
        for indices, entry in value.entries():
            if entry < 0:
                raise ArtifactProofError(
                    "negative_value",
                    f"{name}{indices} = {entry} is negative",
                )

    a = tables["A_data"]
    for state in range(a.shape[1]):
        column = sum(
            (a.get((outcome, state)) for outcome in range(a.shape[0])), Fraction(0)
        )
        if column != 1:
            raise ArtifactProofError(
                "normalization_violation",
                f"A column (state {state}) sums to {column}, not 1",
            )
    b = tables["B_data"]
    for policy in range(b.shape[2]):
        for previous in range(b.shape[1]):
            column = sum(
                (
                    b.get((next_state, previous, policy))
                    for next_state in range(b.shape[0])
                ),
                Fraction(0),
            )
            if column != 1:
                raise ArtifactProofError(
                    "normalization_violation",
                    f"B column (policy {policy}, previous {previous}) sums to "
                    f"{column}, not 1",
                )
    for name in ("C_data", "D_data", "E_data"):
        vector = tables[name]
        total = sum(vector.values, Fraction(0))
        if total != 1:
            raise ArtifactProofError(
                "normalization_violation",
                f"{name} sums to {total}, not 1",
            )


def _lean_real(value: Fraction) -> str:
    if value.denominator == 1:
        return f"({value.numerator} : ℝ)"
    return f"({value.numerator} / {value.denominator} : ℝ)"


def _lean_bool_function(shape: tuple[int, ...], value: TableValue) -> str:
    """A nested ``if`` function over Bool indices realizing ``value``."""
    names = [f"b{depth}" for depth in range(len(shape))]

    def emit(dimension: int, indices: list[int]) -> str:
        if dimension == len(shape):
            return _lean_real(value.get(indices))
        high = emit(dimension + 1, [*indices, 1])
        low = emit(dimension + 1, [*indices, 0])
        body = f"if {names[dimension]} then {high} else {low}"
        return f"({body})" if dimension + 1 < len(shape) else body

    return f"fun {' '.join(names)} => {emit(0, [])}"


def render_lean_probe(
    tables: PymdpArtifactTables,
    *,
    variant: str,
    fixture_name: str,
    fixture_sha256: str,
) -> str:
    """Render the deterministic slice-local Lean probe for one fixture.

    Only the ``DiscreteTargetTables`` record is generated from the
    extracted literals. Everything it is proved against is independently
    authored: the symmetric probe targets the Q2 ``symBoolPayload``
    (transcribed in the accepted Q2 module from the P1 document), the
    asymmetric probe targets the static ``asymExpectedPayload`` transcribed
    below by hand from the fixture source. The faithfulness proofs are
    therefore not circular in the extractor.
    """
    if variant not in ("symmetric", "asymmetric"):
        raise ArtifactProofError("internal_error", f"unknown variant {variant!r}")
    prefix = "sym" if variant == "symmetric" else "asym"
    namespace = (
        "FEPProbe.Q5ArtifactProof"
        if variant == "symmetric"
        else "FEPProbe.Q5ArtifactProofAsym"
    )
    a = tables.table("A_data")
    b = tables.table("B_data")
    c = tables.table("C_data")
    d = tables.table("D_data")
    e = tables.table("E_data")

    lines: list[str] = []
    lines.append("import FepSketches.gnn_denotation")
    lines.append("import FepSketches.gnn_render_statements")
    lines.append("")
    lines.append("/-!")
    lines.append("# Q5 concrete PyMDP artifact proof (generated)")
    lines.append("")
    lines.append("Generated by `specs/gnn-bridge-q5-artifact-proof/generate_probe.py`")
    lines.append(
        f"from fixture `{fixture_name}` (sha256 {fixture_sha256}); do not edit."
    )
    lines.append("")
    lines.append(
        "The tables below are the runner's `A_data`/`B_data`/`C_data`/`D_data`"
    )
    lines.append(
        "/`E_data` literals under the frozen pymdp layout (`A[outcome][state]`,"
    )
    lines.append("`B[next][previous][policy]`, vectors over outcome/state/policy,")
    lines.append("`Bool` enumerated `false, true`); every value is an exact dyadic")
    lines.append("rational. Compilation establishes only the concrete theorems stated")
    lines.append("here on the Boolean carriers (bridge-contract evidence firewall).")
    lines.append("-/")
    lines.append("")
    lines.append(f"namespace {namespace}")
    lines.append("")
    lines.append("open FEP.ActiveInference FEP.GnnDenotation FEP.GnnRenderStatements")
    lines.append("")

    lines.extend(
        [
            f"/-- The five `{fixture_name}` table literals under the frozen pymdp",
            "layout (see module docstring). -/",
            f"noncomputable def {prefix}ArtifactTables :",
            "    DiscreteTargetTables Bool Bool Bool where",
            f"  aMat := {_lean_bool_function(a.shape, a)}",
            f"  bMat := {_lean_bool_function(b.shape, b)}",
            f"  cVec := {_lean_bool_function(c.shape, c)}",
            f"  dVec := {_lean_bool_function(d.shape, d)}",
            f"  eVec := {_lean_bool_function(e.shape, e)}",
            "",
        ]
    )

    def case_proofs(proved_against: str) -> list[str]:
        """Five explicit forall-Bool case proofs of target faithfulness."""

        def one(arity: int) -> list[str]:
            variables = " ".join(f"v{i}" for i in range(arity))
            splitting = " <;> ".join(f"cases v{i}" for i in range(arity))
            return [
                f"  · intro {variables}",
                f"    {splitting} <;> simp [{prefix}ArtifactTables, {proved_against}]",
            ]

        return [*one(2), *one(3), *one(1), *one(1), *one(1)]

    if variant == "symmetric":
        lines.extend(
            [
                "/-- The runner tables are faithful to the independently authored Q2",
                "payload `symBoolPayload` under the frozen target layout: five",
                "explicit pointwise Bool case proofs. -/",
                "theorem symArtifactTables_faithful :",
                "    DiscreteTargetFaithful symArtifactTables symBoolPayload := by",
                "  refine ⟨?_, ?_, ?_, ?_, ?_⟩",
                *case_proofs("symBoolPayload"),
                "",
                "/-- The concrete Q4 pymdp statement instance for the actual",
                "artifact. -/",
                "theorem symArtifact_statement5Pymdp :",
                "    Statement5Pymdp symBoolDoc symBoolPayload symBoolConforms",
                "      symArtifactTables :=",
                "  statement5DiscreteMatrices_holds _ _ _ _",
                "",
                "/-- Applied consequence: the runner literals equal the carrier",
                "masses of the Q2 denotation, pointwise on the Boolean carriers.",
                "-/",
                "theorem symArtifact_carrierMasses :",
                "    (∀ state outcome : Bool, symArtifactTables.aMat outcome state =",
                "        (denoteDiscrete symBoolDoc symBoolPayload symBoolConforms).likelihood.mass state outcome) ∧",
                "      (∀ policy previous next : Bool,",
                "        symArtifactTables.bMat next previous policy =",
                "        ((denoteDiscrete symBoolDoc symBoolPayload symBoolConforms).transition policy).mass previous next) ∧",
                "      (∀ outcome : Bool, symArtifactTables.cVec outcome =",
                "        (denoteDiscrete symBoolDoc symBoolPayload symBoolConforms).preferences.mass outcome) ∧",
                "      (∀ state : Bool, symArtifactTables.dVec state =",
                "        (denoteDiscrete symBoolDoc symBoolPayload symBoolConforms).initialState.mass state) ∧",
                "      (∀ policy : Bool, symArtifactTables.eVec policy =",
                "        (denoteDiscrete symBoolDoc symBoolPayload symBoolConforms).policyPrior.mass policy) :=",
                "  statement5DiscreteMatrices_holds _ _ _ _ symArtifactTables_faithful",
                "",
                "/-- Composed chain: a runner literal recovers the original Lean",
                "model `symmetricBoolModel trueBiasedPolicyPrior` exactly, via",
                "the accepted `symBoolDoc_denotation`. -/",
                "theorem symArtifact_aMass_eq_original (state outcome : Bool) :",
                "    symArtifactTables.aMat outcome state =",
                "      (symmetricBoolModel trueBiasedPolicyPrior).likelihood.mass",
                "        state outcome :=",
                "  by rw [symArtifact_carrierMasses.1 state outcome, symBoolDoc_denotation]",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "/-- Independently authored expected payload for the asymmetric",
                "fixture, hand-transcribed from",
                "`fixtures/pymdp_asymmetric_runner.py`",
                "(A = [[1/4,1/2],[3/4,1/2]], B(false) = [[1/4,3/4],[3/4,1/4]],",
                "B(true) = [[1/2,1/8],[1/2,7/8]], C = [1/4,3/4], D = [1/2,1/2],",
                "E = [3/8,5/8]). This record never flows through the extractor.",
                "-/",
                "noncomputable def asymExpectedPayload : DiscretePayload Bool Bool Bool where",
                "  aLikelihood := fun outcome state =>",
                "    if outcome then (if state then (1 / 2 : ℝ) else (3 / 4 : ℝ))",
                "      else (if state then (1 / 2 : ℝ) else (1 / 4 : ℝ))",
                "  bTransition := fun next previous policy =>",
                "    if next then",
                "      (if previous then (if policy then (7 / 8 : ℝ) else (1 / 4 : ℝ))",
                "        else (if policy then (1 / 2 : ℝ) else (3 / 4 : ℝ)))",
                "    else",
                "      (if previous then (if policy then (1 / 8 : ℝ) else (3 / 4 : ℝ))",
                "        else (if policy then (1 / 2 : ℝ) else (1 / 4 : ℝ)))",
                "  cPreferences := fun outcome =>",
                "    if outcome then (3 / 4 : ℝ) else (1 / 4 : ℝ)",
                "  dInitialState := fun _ => (1 / 2 : ℝ)",
                "  eHabit := fun policy => if policy then (5 / 8 : ℝ) else (3 / 8 : ℝ)",
                "",
                "/-- The runner tables are faithful to the independently authored",
                "expected payload: five explicit pointwise Bool case proofs. -/",
                "theorem asymArtifactTables_faithful :",
                "    DiscreteTargetFaithful asymArtifactTables asymExpectedPayload := by",
                "  refine ⟨?_, ?_, ?_, ?_, ?_⟩",
                *case_proofs("asymExpectedPayload"),
                "",
                "/-- Non-vacuity: the asymmetric fixture differs from the Q2",
                "symmetric exemplar at named entries, so the fragment is not",
                "exemplar-bound. -/",
                "theorem asymExpected_ne_symBoolPayload :",
                "    symBoolPayload.aLikelihood false false ≠",
                "        asymExpectedPayload.aLikelihood false false ∧",
                "      symBoolPayload.bTransition false false false ≠",
                "        asymExpectedPayload.bTransition false false false :=",
                "  by",
                "    refine ⟨?_, ?_⟩",
                "    · intro hEq",
                "      have h1 : symBoolPayload.aLikelihood false false = (1 / 2 : ℝ) := rfl",
                "      have h2 : asymExpectedPayload.aLikelihood false false = (1 / 4 : ℝ) := rfl",
                "      rw [h1, h2] at hEq",
                "      norm_num at hEq",
                "    · intro hEq",
                "      have h1 : symBoolPayload.bTransition false false false = (1 / 2 : ℝ) := rfl",
                "      have h2 : asymExpectedPayload.bTransition false false false = (1 / 4 : ℝ) := rfl",
                "      rw [h1, h2] at hEq",
                "      norm_num at hEq",
                "",
            ]
        )

    lines.append(f"end {namespace}")
    lines.append("")
    return "\n".join(lines)


def render_manifest(
    *,
    fixture_digests: Mapping[str, str],
    extractor_sha256: str,
    generated: Mapping[str, str],
    expected_payload: Mapping[str, object],
) -> str:
    """Deterministic manifest JSON for the slice's integrity checks."""
    manifest = {
        "slice": "gnn-bridge-q5-artifact-proof",
        "fixtures": dict(sorted(fixture_digests.items())),
        "extractor_sha256": extractor_sha256,
        "generated": dict(sorted(generated.items())),
        "expected_payload": expected_payload,
    }
    return json.dumps(manifest, sort_keys=True, indent=2, ensure_ascii=True) + "\n"


_MANIFEST_TOP_KEYS: Final[frozenset[str]] = frozenset(
    {"slice", "fixtures", "extractor_sha256", "generated", "expected_payload"}
)
_MANIFEST_FIXTURE_KEYS: Final[frozenset[str]] = frozenset(
    {"pymdp_asymmetric_runner.py", "pymdp_symmetric_runner.py"}
)
_MANIFEST_GENERATED_KEYS: Final[frozenset[str]] = frozenset(
    {"generated/probe_asymmetric.lean", "generated/probe_symmetric.lean"}
)


def manifest_mismatches(
    manifest_text: str,
    *,
    repo_root: Path,
    slice_root: Path,
    regenerate: Mapping[str, str] | None = None,
) -> list[str]:
    """Digest and schema mismatches between the manifest and the current tree.

    The manifest schema is strict: exactly the two retained fixture keys and
    the two generated probe keys, no more and no fewer, so manifest keys can
    never traverse the filesystem. When ``regenerate`` is supplied, every
    generated artifact must match BOTH the regenerated digest and the
    stored digest — regeneration never bypasses the stored custody record.
    """
    problems: list[str] = []

    try:
        manifest = load_strict_json(manifest_text)
    except ValueError as error:
        return [f"manifest: malformed JSON ({error})"]
    if not isinstance(manifest, dict):
        return ["manifest: expected a JSON object"]
    for key in sorted(_MANIFEST_TOP_KEYS - set(manifest)):
        problems.append(f"manifest: missing key {key}")
    for key in sorted(set(manifest) - _MANIFEST_TOP_KEYS):
        problems.append(f"manifest: unexpected key {key}")
    if manifest.get("slice") != "gnn-bridge-q5-artifact-proof":
        problems.append("manifest: wrong slice")
    fixtures = manifest.get("fixtures")
    generated = manifest.get("generated")
    if not isinstance(fixtures, dict) or not isinstance(generated, dict):
        problems.append("manifest: fixtures/generated must be JSON objects")
        return problems
    for key in sorted(_MANIFEST_FIXTURE_KEYS - set(fixtures)):
        problems.append(f"fixtures: missing key {key}")
    for key in sorted(set(fixtures) - _MANIFEST_FIXTURE_KEYS):
        problems.append(f"fixtures: unexpected key {key}")
    for key in sorted(_MANIFEST_GENERATED_KEYS - set(generated)):
        problems.append(f"generated: missing key {key}")
    for key in sorted(set(generated) - _MANIFEST_GENERATED_KEYS):
        problems.append(f"generated: unexpected key {key}")

    def check(
        section: str,
        allowed: frozenset[str],
        base: Path,
        key: str,
        stored: object,
    ) -> None:
        if key not in allowed:
            return
        if (
            not isinstance(stored, str)
            or len(stored) != 64
            or any(char not in "0123456789abcdef" for char in stored)
        ):
            problems.append(f"{key}: invalid SHA-256 digest")
            return
        try:
            path = contained_file(base, key)
        except (ValueError, OSError) as error:
            problems.append(f"{key}: missing or unsafe artifact ({error})")
            return
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        recomputed = (regenerate or {}).get(key) if section == "generated" else None
        if recomputed is not None and actual != recomputed:
            problems.append(
                f"{key}: regenerated {recomputed[:12]} != on-disk {actual[:12]}"
            )
        if actual != stored:
            problems.append(
                f"{key}: on-disk {actual[:12]} != manifest {str(stored)[:12]}"
            )

    for key, stored in sorted(fixtures.items()):
        check("fixtures", _MANIFEST_FIXTURE_KEYS, slice_root / "fixtures", key, stored)
    for key, stored in sorted(generated.items()):
        check("generated", _MANIFEST_GENERATED_KEYS, slice_root, key, stored)
    extractor = manifest.get("extractor_sha256")
    try:
        extractor_path = contained_file(
            repo_root, "src/fep_lean/verification/gnn_artifact_proof.py"
        )
        extractor_digest = hashlib.sha256(extractor_path.read_bytes()).hexdigest()
        if extractor_digest != extractor:
            problems.append(
                "src/fep_lean/verification/gnn_artifact_proof.py: "
                f"{extractor_digest[:12]} != manifest {str(extractor)[:12]}"
            )
    except (ValueError, OSError) as error:
        problems.append(f"extractor: missing or unsafe source ({error})")
    expected_payload: dict[str, Any] = {}
    for variant in ("symmetric", "asymmetric"):
        try:
            fixture = contained_file(slice_root, f"fixtures/pymdp_{variant}_runner.py")
            tables = extract_pymdp_tables(fixture.read_text(encoding="utf-8"))
            expected_payload[variant] = {
                name: {
                    "shape": list(tables.table(name).shape),
                    "values": [str(value) for _, value in tables.table(name).entries()],
                }
                for name in PYMDP_TABLE_NAMES
            }
        except (ValueError, OSError, ArtifactProofError) as error:
            problems.append(f"{variant}: cannot verify payload ({error})")
    if manifest.get("expected_payload") != expected_payload:
        problems.append(
            "manifest: expected_payload differs from exact extracted tables"
        )
    return problems
