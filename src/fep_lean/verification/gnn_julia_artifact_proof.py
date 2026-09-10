"""Q6 restricted Julia embedded-input extraction, never Julia execution.

The whole canonical Boolean runner skeleton is fixed. Only its sole base64
JSON literal varies. The extracted C is raw input, not runtime softmax(C).
Q4 is an abstract matrix implication, not a Julia program-semantics theorem.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import re
from decimal import Decimal
from fractions import Fraction
from types import MappingProxyType
from typing import Final

from fep_lean.verification._jsonutil import load_strict_json
from fep_lean.verification.gnn_artifact_proof import (
    ArtifactProofError,
    PymdpArtifactTables,
    TableValue,
    _lean_bool_function,
    _require_normalized,
)

SLICE: Final = "specs/gnn-bridge-q6-activeinference-artifact"
SKELETON_PATH: Final = f"{SLICE}/skeleton/canonical_bool_runner.jl.in"
SKELETON_SHA256: Final = (
    "e46d27f13cba5be938dd0b2e4f5717a076a6304c31d8c188851c4c7c2cb8fb52"
)
SLOT: Final = "@@GNN_SPEC_JSON_B64@@"
B_ORDER: Final = "next_state_previous_state_action"
MAX_SOURCE_BYTES: Final = 1_000_000
SHAPES: Final = MappingProxyType(
    {"A": (2, 2), "B": (2, 2, 2), "C": (2,), "D": (2,), "E": (2,)}
)
VARIANTS: Final = ("symmetric", "asymmetric")
NAMESPACES: Final = {
    "symmetric": "FEPProbe.Q6JuliaEmbeddedInput",
    "asymmetric": "FEPProbe.Q6JuliaEmbeddedInputAsym",
}
THEOREMS: Final = {
    "symmetric": (
        "symEmbeddedInput_eq_Q2",
        "symEmbeddedInput_Q4_conditional",
        "symEmbeddedInput_Q2_carrierMasses",
    ),
    "asymmetric": ("asymEmbeddedInput_eq_expected", "asymExpected_differs_from_Q2"),
}
SCOPE: Final = (
    "Q6 concrete embedded Boolean input tables; no consumed-C equality, "
    "Julia runtime, ActiveInference agent, EFE, physical, or H3 claim"
)

# This is independently authored Lean, never interpolated from parsed tables.
ASYMMETRIC_ORACLE_LEAN: Final = r"""
noncomputable def asymExpectedPayload : DiscretePayload Bool Bool Bool where
  aLikelihood := fun outcome state =>
    if outcome then (if state then (1 / 2 : ℝ) else (3 / 4 : ℝ))
      else (if state then (1 / 2 : ℝ) else (1 / 4 : ℝ))
  bTransition := fun next previous policy =>
    if next then
      (if previous then (if policy then (7 / 8 : ℝ) else (1 / 4 : ℝ))
        else (if policy then (1 / 2 : ℝ) else (3 / 4 : ℝ)))
    else
      (if previous then (if policy then (1 / 8 : ℝ) else (3 / 4 : ℝ))
        else (if policy then (1 / 2 : ℝ) else (1 / 4 : ℝ)))
  cPreferences := fun outcome => if outcome then (3 / 4 : ℝ) else (1 / 4 : ℝ)
  dInitialState := fun state => if state then (3 / 8 : ℝ) else (5 / 8 : ℝ)
  eHabit := fun policy => if policy then (5 / 8 : ℝ) else (3 / 8 : ℝ)
"""


def _reject(reason: str, detail: str) -> None:
    raise ArtifactProofError(reason, detail)


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            _reject("duplicate_json_key", key)
        result[key] = value
    return result


def _nonfinite(value: str) -> object:
    _reject("nonfinite_value", value)
    raise AssertionError("unreachable")


def _object(value: object, name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        _reject("invalid_document", f"{name} must be an object")
    assert isinstance(value, dict)
    return value


def _fraction(value: object) -> Fraction:
    if type(value) is int:
        number = Fraction(value)
    elif isinstance(value, Decimal):
        if not value.is_finite() or (value and abs(value.adjusted()) > 16):
            _reject("numeric_bound", "numeric literal exceeds the selected contract")
        number = Fraction(value)
    else:
        _reject("nonnumeric_value", "leaves must be non-Boolean JSON numbers")
        raise AssertionError("unreachable")
    if number < 0 or number > 1:
        _reject("probability_range", str(number))
    denominator = number.denominator
    if denominator & (denominator - 1):
        _reject("nondyadic_value", str(number))
    if denominator > 65536:
        _reject("numeric_bound", "dyadic denominator exceeds 65536")
    return number


def _table(value: object, shape: tuple[int, ...], name: str) -> TableValue:
    entries: list[Fraction] = []

    def visit(current: object, remaining: tuple[int, ...]) -> None:
        if not remaining:
            entries.append(_fraction(current))
            return
        if not isinstance(current, list) or len(current) != remaining[0]:
            _reject("shape_mismatch", f"{name} must have shape {shape}")
        assert isinstance(current, list)
        for child in current:
            visit(child, remaining[1:])

    visit(value, shape)
    return TableValue(shape, tuple(entries))


def extract_julia_embedded_tables(
    source_text: str, *, skeleton_text: str
) -> PymdpArtifactTables:
    """Read exact input tables from the sole approved whole-script skeleton.

    Q5's immutable table container and normalization checks are shared. Its
    ``*_data`` dictionary keys are internal adapter names, not Julia variables.
    No Julia lexer, macro expansion, eval, renderer, or subprocess is invoked.
    """
    source_bytes = source_text.encode("utf-8")
    if len(source_bytes) > MAX_SOURCE_BYTES:
        _reject("source_too_large", str(len(source_bytes)))
    if hashlib.sha256(skeleton_text.encode()).hexdigest() != SKELETON_SHA256:
        _reject("unapproved_skeleton", "whole-script skeleton digest differs")
    if skeleton_text.count(SLOT) != 1:
        _reject("invalid_skeleton", "exactly one payload slot required")
    prefix, suffix = skeleton_text.split(SLOT)
    if not source_text.startswith(prefix) or not source_text.endswith(suffix):
        _reject("skeleton_mismatch", "Julia outside the sole literal changed")
    encoded = source_text[len(prefix) : len(source_text) - len(suffix)]
    if not encoded or re.fullmatch(r"[A-Za-z0-9+/]*={0,2}", encoded) is None:
        _reject("invalid_base64", "payload is not one base64 literal")
    try:
        decoded = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error) as error:
        raise ArtifactProofError("invalid_base64", str(error)) from error
    if base64.b64encode(decoded).decode("ascii") != encoded:
        _reject("invalid_base64", "noncanonical base64 encoding")
    try:
        document = _object(
            load_strict_json(
                decoded.decode("utf-8"),
                fail=lambda reason, detail: _reject(
                    "duplicate_json_key" if "duplicate" in detail
                    else "nonfinite_value",
                    detail.split(": ", 1)[-1],
                ),
                parse_float=Decimal,
            ),
            "root",
        )
    except (UnicodeError, ValueError, RecursionError) as error:
        raise ArtifactProofError("invalid_json", str(error)) from error
    if document.get("canonical_pomdp_schema") != "canonical_pomdp_v1":
        _reject("invalid_document", "canonical_pomdp_v1 required")
    parameters = _object(document.get("model_parameters"), "model_parameters")
    for key in ("num_hidden_states", "num_obs", "num_actions"):
        if type(parameters.get(key)) is not int or parameters[key] != 2:
            _reject("shape_mismatch", f"{key} must equal integer 2")
    if parameters.get("b_tensor_order") != B_ORDER:
        _reject("axis_order", "noncanonical B order")
    provenance = _object(document.get("matrix_provenance"), "matrix_provenance")
    if _object(provenance.get("B"), "B provenance").get("canonical_order") != B_ORDER:
        _reject("axis_order", "B provenance disagrees with canonical order")
    initial = _object(
        document.get("initialparameterization"), "initialparameterization"
    )
    if set(initial) != set(SHAPES):
        _reject("table_roster", "exactly A/B/C/D/E are required; E has no fallback")
    tables = {
        f"{name}_data": _table(initial[name], shape, name)
        for name, shape in SHAPES.items()
    }
    _require_normalized(tables)
    return PymdpArtifactTables(
        hashlib.sha256(source_bytes).hexdigest(), MappingProxyType(tables)
    )


def backend_contract() -> dict[str, object]:
    """Fixed metadata for parent-owned native evidence tooling; no execution."""
    return {
        "backend": "activeinference_jl_embedded_input",
        "scope": SCOPE,
        "slice": SLICE,
        "extractor": "src/fep_lean/verification/gnn_julia_artifact_proof.py",
        "shared_table_owner": "src/fep_lean/verification/gnn_artifact_proof.py",
        "generator": f"{SLICE}/generate_probe.py",
        "skeleton": SKELETON_PATH,
        "skeleton_sha256": SKELETON_SHA256,
        "targets": ["FepSketches.gnn_denotation", "FepSketches.gnn_render_statements"],
        "fixtures": {
            v: f"{SLICE}/fixtures/activeinference_{v}_runner.jl" for v in VARIANTS
        },
        "probes": {v: f"{SLICE}/generated/probe_{v}.lean" for v in VARIANTS},
        "theorems": {
            v: [f"{NAMESPACES[v]}.{name}" for name in THEOREMS[v]] for v in VARIANTS
        },
        "runtime_execution_verified": False,
        "consumed_c_identical_to_embedded_input": False,
    }


def table_manifest(tables: PymdpArtifactTables) -> dict[str, object]:
    """Describe extraction results; this is not an independent oracle."""
    return {
        key: {"shape": list(value.shape), "values": [str(v) for v in value.values]}
        for key, value in tables.tables.items()
    }


def _cases(table_name: str, reference: str) -> list[str]:
    lines = ["  refine ⟨?_, ?_, ?_, ?_, ?_⟩"]
    for arity in (2, 3, 1, 1, 1):
        variables = [f"v{i}" for i in range(arity)]
        lines.append("  · intro " + " ".join(variables))
        lines.append(
            "    "
            + " <;> ".join(f"cases {v}" for v in variables)
            + f" <;> norm_num [{table_name}, {reference}]"
        )
    return lines


def render_julia_input_probe(tables: PymdpArtifactTables, *, variant: str) -> str:
    """Generate only embedded-input equalities and the explicitly conditional Q4 claim."""
    if variant not in VARIANTS:
        _reject("unknown_variant", variant)
    prefix = "sym" if variant == "symmetric" else "asym"
    name = f"{prefix}EmbeddedInput"
    namespace = NAMESPACES[variant]
    lines = [
        "import FepSketches.gnn_denotation",
        "import FepSketches.gnn_render_statements",
        "",
        "/-! Q6 concrete raw embedded input, not runtime-consumed C.",
        f"Source SHA256: {tables.source_sha256}.",
        "The actual Julia runner applies softmax(C). Q4 below is an abstract",
        "matrix implication; no Julia execution or EFE equivalence is established. -/",
        f"namespace {namespace}",
        "open FEP.GnnDenotation FEP.GnnRenderStatements",
        f"noncomputable def {name} : DiscreteTargetTables Bool Bool Bool where",
    ]
    for field, key in zip(
        ("aMat", "bMat", "cVec", "dVec", "eVec"), SHAPES, strict=True
    ):
        value = tables.table(f"{key}_data")
        lines.append(f"  {field} := {_lean_bool_function(value.shape, value)}")
    lines.append("")
    if variant == "asymmetric":
        lines.extend(
            [
                ASYMMETRIC_ORACLE_LEAN,
                "theorem asymEmbeddedInput_eq_expected :",
                f"    DiscreteTargetFaithful {name} asymExpectedPayload := by",
                *_cases(name, "asymExpectedPayload"),
                "",
                "theorem asymExpected_differs_from_Q2 :",
                "    asymExpectedPayload.dInitialState false ≠ symBoolPayload.dInitialState false ∧",
                "      asymExpectedPayload.aLikelihood false false ≠ symBoolPayload.aLikelihood false false := by",
                "  norm_num [asymExpectedPayload, symBoolPayload]",
            ]
        )
    else:
        lines.extend(
            [
                "theorem symEmbeddedInput_eq_Q2 :",
                f"    DiscreteTargetFaithful {name} symBoolPayload := by",
                *_cases(name, "symBoolPayload"),
                "",
                "/-- Abstract conditional matrix statement, not runtime C equality. -/",
                "theorem symEmbeddedInput_Q4_conditional :",
                "    Statement5ActiveInferenceJl symBoolDoc symBoolPayload symBoolConforms",
                f"      {name} := statement5DiscreteMatrices_holds _ _ _ _",
                "",
                "/-- The five raw inputs equal the Q2 carrier masses. -/",
                "theorem symEmbeddedInput_Q2_carrierMasses :",
                f"    (∀ state outcome : Bool, {name}.aMat outcome state =",
                "      (denoteDiscrete symBoolDoc symBoolPayload symBoolConforms).likelihood.mass state outcome) ∧",
                f"    (∀ policy previous next : Bool, {name}.bMat next previous policy =",
                "      ((denoteDiscrete symBoolDoc symBoolPayload symBoolConforms).transition policy).mass previous next) ∧",
                f"    (∀ outcome : Bool, {name}.cVec outcome =",
                "      (denoteDiscrete symBoolDoc symBoolPayload symBoolConforms).preferences.mass outcome) ∧",
                f"    (∀ state : Bool, {name}.dVec state =",
                "      (denoteDiscrete symBoolDoc symBoolPayload symBoolConforms).initialState.mass state) ∧",
                f"    (∀ policy : Bool, {name}.eVec policy =",
                "      (denoteDiscrete symBoolDoc symBoolPayload symBoolConforms).policyPrior.mass policy) :=",
                "  statement5DiscreteMatrices_holds _ _ _ _ symEmbeddedInput_eq_Q2",
            ]
        )
    return "\n".join([*lines, "", f"end {namespace}", ""])
