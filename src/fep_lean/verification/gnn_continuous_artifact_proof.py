"""Q7 static scalar OU literals, exact dyadic decoding, and receipt hooks.

No runner code is imported or executed. A separately frozen canonical AST
scaffold excludes only the six literal parameter values; arbitrary dataflow or
consumer edits therefore require a new reviewed scaffold. Decimal lexemes and
binary64 rationals are retained separately. Native evidence belongs to the
parent receipt engine, not this boundary reader.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from math import isfinite
from typing import Any, NoReturn, cast

from fep_lean._paths import FepLeanError
from fep_lean.verification._jsonutil import load_strict_json

TABLE_SHAPES = {
    "F_RAW": (1, 1),
    "H_RAW": (1, 1),
    "Q_RAW": (1, 1),
    "R_RAW": (1, 1),
    "PRIOR_MEAN_RAW": (1,),
    "PRIOR_COV_RAW": (1, 1),
}
METADATA = {
    "NUM_TIMESTEPS": 1,
    "DT": 1.0,
    "GOAL_MEAN_RAW": None,
    "CONTROL_GAIN": None,
    "OUTPUT_ENV": "GNN_OUTPUT_DIR",
}
GAUGE = {
    "ou_rate": 1,
    "ou_center": 0,
    "diffusion_variance_rate": 2,
    "step_duration": 1,
    "observation_noise_variance": 1,
    "num_timesteps": 1,
}
FORMULAS = {
    "F": "Real.exp (-1)",
    "Q": "1 - (Real.exp (-1)) ^ 2",
    "H": "1",
    "R": "1",
    "prior_mean": "0",
    "prior_cov": "1",
}
EPSILON = Fraction(1, 10**15)
RENDER_ROUTE = [
    "gnn.extract.pomdp_extractor.extract_pomdp_from_file(strict_validation=True)",
    "gnn.render.pomdp_processor.POMDPRenderProcessor._pomdp_to_gnn_spec",
    "gnn.render.processor.render_gnn_spec(jax)",
]
THEOREMS = (
    "selected_decay",
    "selected_transitionVariance",
    "exact_row_eq_selected",
    "artifact_exact_parameters",
    "exact_noise_formula",
    "artifact_F_bound",
    "artifact_Q_bound",
    "artifact_prediction_mean_bound",
    "artifact_prediction_variance_bound",
    "artifact_stationary_defect_bound",
    "nonstationary_prediction_changes_mean",
    "scalar_joseph_identity",
)
NAMESPACE = "FEPProbe.Q7ContinuousOU"

# Canonical candidate bytes are portable across the reviewed CPython versions;
# actual extraction/receipt validation still accepts only the pinned validator.
ACCEPTED_SCAFFOLD_INTERPRETERS: tuple[tuple[str, tuple[int, int]], ...] = (
    ("cpython", (3, 14)),
)
CANONICAL_SCAFFOLD_INTERPRETERS: tuple[tuple[str, tuple[int, int]], ...] = tuple(
    ("cpython", (3, minor)) for minor in range(10, 15)
)
SCAFFOLD_AST_SCHEMA_VERSION = 1

# Frozen from the actual runner, never inferred from a new runtime's AST.
# Every field is serialized, including empty/None fields. The sole normalized
# schema difference is FunctionDef's absent/empty type_params in 3.10--3.14.
_SCAFFOLD_AST_FIELDS: dict[str, tuple[str, ...]] = {
    "Add": (),
    "Assign": ("targets", "value", "type_comment"),
    "Attribute": ("value", "attr", "ctx"),
    "BinOp": ("left", "op", "right"),
    "Call": ("func", "args", "keywords"),
    "Compare": ("left", "ops", "comparators"),
    "Constant": ("value", "kind"),
    "Dict": ("keys", "values"),
    "Div": (),
    "Eq": (),
    "ExceptHandler": ("type", "name", "body"),
    "Expr": ("value",),
    "For": ("target", "iter", "body", "orelse", "type_comment"),
    "FormattedValue": ("value", "conversion", "format_spec"),
    "FunctionDef": (
        "name",
        "args",
        "body",
        "decorator_list",
        "returns",
        "type_comment",
        "type_params",
    ),
    "GeneratorExp": ("elt", "generators"),
    "Gt": (),
    "If": ("test", "body", "orelse"),
    "IfExp": ("test", "body", "orelse"),
    "Import": ("names",),
    "ImportFrom": ("module", "names", "level"),
    "IsNot": (),
    "JoinedStr": ("values",),
    "List": ("elts", "ctx"),
    "Load": (),
    "MatMult": (),
    "Module": ("body", "type_ignores"),
    "Mult": (),
    "Name": ("id", "ctx"),
    "Pow": (),
    "Return": ("value",),
    "Store": (),
    "Sub": (),
    "Subscript": ("value", "slice", "ctx"),
    "Try": ("body", "handlers", "orelse", "finalbody"),
    "Tuple": ("elts", "ctx"),
    "USub": (),
    "UnaryOp": ("op", "operand"),
    "With": ("items", "body", "type_comment"),
    "alias": ("name", "asname"),
    "arg": ("arg", "annotation", "type_comment"),
    "arguments": (
        "posonlyargs",
        "args",
        "vararg",
        "kwonlyargs",
        "kw_defaults",
        "kwarg",
        "defaults",
    ),
    "comprehension": ("target", "iter", "ifs", "is_async"),
    "keyword": ("arg", "value"),
    "withitem": ("context_expr", "optional_vars"),
}
_SCAFFOLD_LOCATION_ATTRIBUTES = frozenset(
    {"lineno", "col_offset", "end_lineno", "end_col_offset"}
)


class ContinuousArtifactError(ValueError, FepLeanError):
    """A contract rejection with a stable machine-readable reason."""

    def __init__(self, reason: str, detail: str) -> None:
        super().__init__(f"{reason}: {detail}")
        self.reason = reason


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n"


def read_json_object(source: str | bytes) -> dict[str, Any]:
    """Reject ambiguous duplicate keys and nonstandard JSON constants."""
    try:
        result = load_strict_json(source, fail=_fail)
    except (ValueError, UnicodeDecodeError) as error:
        raise ContinuousArtifactError("json", str(error)) from error
    if not isinstance(result, dict):
        _fail("json", "root must be an object")
    return result


def _fail(reason: str, detail: str) -> NoReturn:
    raise ContinuousArtifactError(reason, detail)


def _is_digest(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


@dataclass(frozen=True)
class ScalarLiteral:
    """Two exact numbers: decimal source rational and decoded binary64 rational."""

    lexeme: str
    decimal: Fraction
    binary64: Fraction
    binary64_hex: str

    def to_dict(self) -> dict[str, object]:
        def ratio(value: Fraction) -> list[int]:
            return [value.numerator, value.denominator]

        return {
            "lexeme": self.lexeme,
            "decimal_ratio": ratio(self.decimal),
            "binary64_ratio": ratio(self.binary64),
            "binary64_hex": self.binary64_hex,
        }


@dataclass(frozen=True)
class ContinuousArtifact:
    source_sha256: str
    scaffold_sha256: str
    numbers: Mapping[str, ScalarLiteral]

    def to_dict(self) -> dict[str, object]:
        return {
            "source_sha256": self.source_sha256,
            "scaffold_sha256": self.scaffold_sha256,
            "numbers": {key: value.to_dict() for key, value in self.numbers.items()},
        }


def expected_contract(scaffold_sha256: str) -> dict[str, object]:
    """Independent exact-model expectations; no artifact F/Q value is copied."""
    if not _is_digest(scaffold_sha256):
        _fail("expected_contract", "invalid reviewed runner scaffold digest")
    return {
        "schema_version": 2,
        "model": "selected scalar OU, passive, unit step",
        "gauge": dict(GAUGE),
        "formulas": dict(FORMULAS),
        "epsilon_ratio": [EPSILON.numerator, EPSILON.denominator],
        "artifact_shapes": {key: list(value) for key, value in TABLE_SHAPES.items()},
        "runner_ast_sha256": scaffold_sha256,
        "runner_ast_serialization": {
            "format": "fep-q7-scaffold-ast",
            "schema_version": SCAFFOLD_AST_SCHEMA_VERSION,
        },
    }


def validate_expected(expected: Mapping[str, Any]) -> str:
    scaffold = expected.get("runner_ast_sha256")
    if not _is_digest(scaffold):
        _fail("expected_contract", "missing reviewed runner scaffold digest")
    if canonical_json(dict(expected)) != canonical_json(
        expected_contract(str(scaffold))
    ):
        _fail("expected_contract", "exact formulas, gauge, epsilon or schema changed")
    return str(scaffold)


def _parse(source: str, *, type_comments: bool = False) -> ast.Module:
    try:
        return ast.parse(source, type_comments=type_comments)
    except (SyntaxError, ValueError) as error:
        raise ContinuousArtifactError("syntax", str(error)) from error


def _assignments(tree: ast.Module) -> dict[str, ast.Assign]:
    tracked = set(TABLE_SHAPES) | set(METADATA)
    assignments: dict[str, ast.Assign] = {}
    allowed_targets: set[int] = set()
    for statement in tree.body:
        if not isinstance(statement, ast.Assign):
            continue
        names = [
            target.id for target in statement.targets if isinstance(target, ast.Name)
        ]
        if not tracked.intersection(names):
            continue
        if len(statement.targets) != 1 or len(names) != 1:
            _fail(
                "ambiguous_assignment", "tracked assignments must have one name target"
            )
        name = names[0]
        if name in assignments:
            _fail("duplicate_assignment", name)
        assignments[name] = statement
        allowed_targets.add(id(statement.targets[0]))
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Name)
            and node.id in tracked
            and isinstance(node.ctx, ast.Store | ast.Del)
            and id(node) not in allowed_targets
        ):
            _fail(
                "ambiguous_assignment",
                f"nested/rebound/deleted tracked name: {node.id}",
            )
    missing = tracked - assignments.keys()
    if missing:
        _fail("missing_assignment", ", ".join(sorted(missing)))
    return assignments


def _require_accepted_scaffold_interpreter() -> None:
    """Refuse scaffold digestion before parsing outside the accepted set."""
    running = (sys.implementation.name.lower(), sys.version_info[:2])
    if running in ACCEPTED_SCAFFOLD_INTERPRETERS:
        return
    accepted = ", ".join(
        f"{name} {major}.{minor}"
        for name, (major, minor) in ACCEPTED_SCAFFOLD_INTERPRETERS
    )
    _fail(
        "interpreter",
        f"scaffold_digest accepts only {accepted}; running "
        f"{sys.implementation.name} {sys.version_info[0]}.{sys.version_info[1]}",
    )


def _canonical_scaffold_value(value: object) -> list[Any]:
    """Serialize only the frozen AST schema, preserving types and field order."""
    if isinstance(value, ast.AST):
        name = type(value).__name__
        fields = _SCAFFOLD_AST_FIELDS.get(name)
        if fields is None or type(value) is not getattr(ast, name, None):
            _fail("scaffold_schema", f"unreviewed AST node: {name}")
        observed = tuple(value._fields)
        if observed != fields and not (
            name == "FunctionDef" and observed == fields[:-1]
        ):
            _fail("scaffold_schema", f"unreviewed AST fields/order: {name}.{observed}")
        unknown = set(vars(value)) - set(fields) - _SCAFFOLD_LOCATION_ATTRIBUTES
        if unknown:
            _fail(
                "scaffold_schema",
                f"unreviewed AST attributes: {name}.{sorted(unknown)}",
            )
        serialized = []
        for field in fields:
            if name == "FunctionDef" and field == "type_params":
                current = (
                    getattr(value, field, [])
                    if field not in observed
                    else getattr(value, field, None)
                )
                if type(current) is not list or current:
                    _fail(
                        "scaffold_schema",
                        "FunctionDef.type_params must be absent or empty",
                    )
            else:
                if not hasattr(value, field):
                    _fail("scaffold_schema", f"missing AST field: {name}.{field}")
                current = getattr(value, field)
            serialized.append([field, _canonical_scaffold_value(current)])
        return ["node", name, serialized]
    if type(value) is list:
        return ["list", [_canonical_scaffold_value(item) for item in value]]
    if value is None:
        return ["none"]
    if type(value) is bool:
        return ["bool", value]
    if type(value) is int:
        return ["int", str(value)]
    if type(value) is float and isfinite(value):
        return ["float", value.hex()]
    if type(value) is str:
        return ["str", value]
    _fail("scaffold_schema", f"unreviewed AST scalar: {type(value).__name__}")


def canonical_scaffold_bytes(source: str) -> bytes:
    """Portable candidate syntax bytes, never approval or runner execution.

    Schema 1 retains all reviewed AST fields; only absent/empty FunctionDef
    type_params is normalized. Extraction keeps its separate 3.14 validator
    guard. See the slice's scaffold-serialization.md for the frozen protocol.
    """
    running = (sys.implementation.name.lower(), sys.version_info[:2])
    if running not in CANONICAL_SCAFFOLD_INTERPRETERS:
        _fail(
            "interpreter",
            "canonical scaffold serialization accepts only CPython 3.10--3.14",
        )
    tree = _parse(source, type_comments=True)
    assignments = _assignments(tree)
    for name in TABLE_SHAPES:
        assignments[name].value = ast.Constant(value=f"Q7_LITERAL:{name}")
    payload = [
        "fep-q7-scaffold-ast",
        SCAFFOLD_AST_SCHEMA_VERSION,
        _canonical_scaffold_value(tree),
    ]
    return (
        json.dumps(payload, ensure_ascii=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    ).encode("ascii")


def scaffold_digest(source: str) -> str:
    """Candidate digest for explicit review/freezing under the pinned validator."""
    _require_accepted_scaffold_interpreter()
    return digest(canonical_scaffold_bytes(source))


def _literal(node: ast.expr, source: str) -> ScalarLiteral:
    if not isinstance(node, ast.Constant) or type(node.value) not in (int, float):
        _fail("literal", "only direct finite numeric literals are accepted")
    value = cast(int | float, node.value)
    try:
        floating = float(value)
    except (OverflowError, TypeError, ValueError) as error:
        raise ContinuousArtifactError(
            "nonfinite", "not representable in binary64"
        ) from error
    if not isfinite(floating):
        _fail("nonfinite", "nonfinite binary64 literal")
    lexeme = ast.get_source_segment(source, node)
    if lexeme is None:
        _fail("literal", "missing original numeric source segment")
    try:
        decimal = Fraction(Decimal(str(lexeme)))
    except (InvalidOperation, ValueError) as error:
        raise ContinuousArtifactError(
            "literal", "not a decimal numeric literal"
        ) from error
    return ScalarLiteral(
        str(lexeme), decimal, Fraction.from_float(floating), floating.hex()
    )


def _scalar_table(node: ast.expr, shape: tuple[int, ...], source: str) -> ScalarLiteral:
    for size in shape:
        if not isinstance(node, ast.List) or len(node.elts) != size:
            _fail("shape", f"expected literal list shape {shape}")
        node = node.elts[0]
    return _literal(node, source)


def exact_coefficient_intervals() -> dict[str, tuple[Fraction, Fraction]]:
    """Rational enclosure implied by Mathlib Real.exp_one_near_20.

    Python computes certificate data; the generated Lean proof independently
    discharges these bounds against the actual imported Mathlib theorem.
    """
    center, radius = Fraction(363916618873, 133877442384), Fraction(1, 10**20)
    lower, upper = 1 / (center + radius), 1 / (center - radius)
    return {"F_RAW": (lower, upper), "Q_RAW": (1 - upper**2, 1 - lower**2)}


def _check_coefficients(numbers: Mapping[str, ScalarLiteral]) -> None:
    for name, (lower, upper) in exact_coefficient_intervals().items():
        value = numbers[name].binary64
        if max(abs(value - lower), abs(value - upper)) > EPSILON:
            _fail("coefficient_bound", f"{name} exceeds the certified enclosure budget")
    for name, expected in {
        "H_RAW": 1,
        "R_RAW": 1,
        "PRIOR_MEAN_RAW": 0,
        "PRIOR_COV_RAW": 1,
    }.items():
        if numbers[name].binary64 != expected or numbers[name].decimal != expected:
            _fail("gauge", f"{name} must be exactly {expected}")


def extract_continuous_artifact(
    source: str, expected: Mapping[str, Any]
) -> ContinuousArtifact:
    """Read a reviewed scalar JAX artifact, never importing/executing its code."""
    expected_scaffold = validate_expected(expected)
    tree = _parse(source)
    assignments = _assignments(tree)
    for name, wanted in METADATA.items():
        node = assignments[name].value
        if (
            not isinstance(node, ast.Constant)
            or type(node.value) is not type(wanted)
            or node.value != wanted
        ):
            _fail("metadata", f"{name} must remain {wanted!r}")
    numbers = {
        name: _scalar_table(assignments[name].value, shape, source)
        for name, shape in TABLE_SHAPES.items()
    }
    scaffold = scaffold_digest(source)
    if scaffold != expected_scaffold:
        _fail("scaffold", "canonical AST changed outside the six parameter literals")
    _check_coefficients(numbers)
    return ContinuousArtifact(digest(source.encode()), scaffold, numbers)


def validate_input_document(source: str, artifact: ContinuousArtifact) -> None:
    """Freeze the actual scalar source gauge and its six declared parameters."""
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in source.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            if current in sections:
                _fail("input_contract", f"duplicate section {current}")
            sections[current] = []
        elif current is not None:
            sections[current].append(line.split("#", 1)[0].strip())

    def body(name: str) -> str:
        if name not in sections:
            _fail("input_contract", f"missing section {name}")
        return "\n".join(line for line in sections[name] if line)

    parameters: dict[str, str] = {}
    for line in body("ModelParameters").splitlines():
        parts = line.split(":", 1)
        if len(parts) != 2 or parts[0].strip() in parameters:
            _fail("input_contract", "ambiguous model parameters")
        parameters[parts[0].strip()] = parts[1].strip()
    if parameters != {key: str(value) for key, value in GAUGE.items()}:
        _fail("input_contract", "model parameter gauge or duration changed")
    declarations = body("StateSpaceBlock").splitlines()
    required = [
        f"{name}[1,1,type=float]"
        for name in ("x", "y", "F", "Q", "H", "R", "prior_mean", "prior_cov", "u")
    ]
    if declarations != required + ["t[1,type=int]"]:
        _fail("input_contract", "scalar declaration shapes/order changed")
    if body("Time") != "Time=t\nDynamic\nContinuous\nModelTimeHorizon=1":
        _fail("input_contract", "time indexing contract changed")
    initial = body("InitialParameterization")
    number = r"[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?"
    for field, table in (
        ("F", "F_RAW"),
        ("Q", "Q_RAW"),
        ("H", "H_RAW"),
        ("R", "R_RAW"),
        ("prior_mean", "PRIOR_MEAN_RAW"),
        ("prior_cov", "PRIOR_COV_RAW"),
    ):
        brackets = (
            (r"\(\s*", r"\s*\)") if field == "prior_mean" else (r"\(\(\s*", r"\s*\)\)")
        )
        pattern = rf"{field}\s*=\s*\{{\s*{brackets[0]}({number}){brackets[1]}\s*\}}"
        matches = list(re.finditer(pattern, initial))
        if len(matches) != 1:
            _fail("input_contract", f"missing/ambiguous literal {field}")
        lexeme = matches[0].group(1)
        literal = artifact.numbers[table]
        if (
            Fraction(Decimal(lexeme)) != literal.decimal
            or Fraction.from_float(float(lexeme)) != literal.binary64
        ):
            _fail("input_contract", f"rendered {field} differs from its exact input")
        initial = initial[: matches[0].start()] + initial[matches[0].end() :]
    if initial.strip():
        _fail("input_contract", "unexpected initial parameterization content")


def validate_render_provenance(
    provenance: Mapping[str, Any],
    *,
    input_bytes: bytes,
    artifact_bytes: bytes,
    owners: Mapping[str, Any],
) -> None:
    """Receipt hook: require an actual current, unchanged canonical render record."""
    keys = {
        "schema_version",
        "evidence_plane",
        "render_route",
        "source_pin_sha256",
        "input",
        "output",
        "owners_before",
        "owners_after",
        "returncode",
        "stdout",
        "stderr",
        "command",
    }
    if set(provenance) != keys or type(provenance.get("schema_version")) is not int:
        _fail("render_custody", "invalid render provenance schema")
    if (
        provenance["schema_version"] != 1
        or provenance["evidence_plane"] != "canonical GNN render (no runner execution)"
        or provenance["render_route"] != RENDER_ROUTE
        or type(provenance["returncode"]) is not int
        or provenance["returncode"] != 0
    ):
        _fail("render_custody", "missing successful canonical rendering evidence")
    if (
        provenance["input"]
        != {
            "path": "specs/gnn-bridge-p4b-continuous-emission/gnn-input/FepLeanContinuousOU.md",
            "sha256": digest(input_bytes),
        }
        or provenance["output"]
        != {
            "path": "specs/gnn-bridge-q7-continuous-ou-proof/fixtures/continuous_ou_jax.py",
            "sha256": digest(artifact_bytes),
        }
        or not _is_digest(provenance["source_pin_sha256"])
    ):
        _fail("render_custody", "input/artifact digest changed")
    if (
        set(owners) != {"fep_lean", "gnn"}
        or any(
            not isinstance(table, dict)
            or not table
            or any(
                not isinstance(path, str) or not _is_digest(sha)
                for path, sha in table.items()
            )
            for table in owners.values()
        )
        or provenance["owners_before"] != owners
        or provenance["owners_after"] != owners
    ):
        _fail("render_custody", "render owners missing, changed, or stale")
    if (
        not isinstance(provenance["stdout"], str)
        or not provenance["stdout"].strip()
        or not isinstance(provenance["stderr"], str)
        or not isinstance(provenance["command"], list)
        or len(provenance["command"]) < 3
        or any(not isinstance(item, str) or not item for item in provenance["command"])
    ):
        _fail("render_custody", "missing render process evidence")


def render_lean_probe(artifact: ContinuousArtifact, template: str) -> str:
    """Substitute only exact rational constants into the reviewed proof template."""
    for token, name in (
        ("@@F@@", "F_RAW"),
        ("@@Q@@", "Q_RAW"),
        ("@@H@@", "H_RAW"),
        ("@@R@@", "R_RAW"),
        ("@@MEAN@@", "PRIOR_MEAN_RAW"),
        ("@@COV@@", "PRIOR_COV_RAW"),
    ):
        if template.count(token) != 1:
            _fail("template", f"exactly one {token} placeholder required")
        value = artifact.numbers[name].binary64
        template = template.replace(
            token, f"({value.numerator} / {value.denominator} : ℝ)"
        )
    if "@@" in template:
        _fail("template", "unknown unsubstituted template token")
    return template
