"""Q6 extraction/generation contracts. No Julia/Lean/runtime evidence is fabricated."""

from __future__ import annotations

import base64
import copy
import hashlib
import importlib.util
import itertools
import json
from fractions import Fraction
from pathlib import Path
from types import ModuleType

import pytest

from fep_lean.verification import gnn_julia_artifact_proof as q6
from fep_lean.verification.gnn_artifact_proof import ArtifactProofError

ROOT = Path(q6.__file__).resolve().parents[3]
SLICE = ROOT / q6.SLICE
SKELETON = (ROOT / q6.SKELETON_PATH).read_bytes().decode("utf-8")

# Independent test oracle, not read from generated files or extracted fixtures.
EXPECTED_ASYM = {
    "A_data": (Fraction(1, 4), Fraction(1, 2), Fraction(3, 4), Fraction(1, 2)),
    "B_data": tuple(
        Fraction(v) for v in ("1/4", "1/2", "3/4", "1/8", "3/4", "1/2", "1/4", "7/8")
    ),
    "C_data": (Fraction(1, 4), Fraction(3, 4)),
    "D_data": (Fraction(5, 8), Fraction(3, 8)),
    "E_data": (Fraction(3, 8), Fraction(5, 8)),
}


def _source(variant: str = "asymmetric") -> str:
    return (
        (SLICE / "fixtures" / f"activeinference_{variant}_runner.jl")
        .read_bytes()
        .decode()
    )


def _document() -> dict[str, object]:
    prefix, suffix = SKELETON.split(q6.SLOT)
    source = _source()
    encoded = source[len(prefix) : len(source) - len(suffix)]
    return json.loads(base64.b64decode(encoded, validate=True))


def _wrap(text: str | bytes) -> str:
    raw = text.encode() if isinstance(text, str) else text
    return SKELETON.replace(q6.SLOT, base64.b64encode(raw).decode())


def _extract_document(document: dict[str, object]):  # type: ignore[no-untyped-def]
    return q6.extract_julia_embedded_tables(
        _wrap(json.dumps(document)), skeleton_text=SKELETON
    )


def _generator() -> ModuleType:
    path = SLICE / "generate_probe.py"
    spec = importlib.util.spec_from_file_location("q6_draft_generator", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_actual_canonical_runner_and_asymmetric_oracle() -> None:
    assert hashlib.sha256(SKELETON.encode()).hexdigest() == q6.SKELETON_SHA256
    tables = q6.extract_julia_embedded_tables(_source(), skeleton_text=SKELETON)
    assert tables.source_sha256 == hashlib.sha256(_source().encode()).hexdigest()
    assert {
        name: table.values for name, table in tables.tables.items()
    } == EXPECTED_ASYM
    assert tables.table("B_data").get((0, 1, 1)) == Fraction(1, 8)
    assert "C_pref = softmax(C)" in _source()
    assert "init_aif(" not in _source()
    for key in ("C_data", "D_data", "E_data"):
        values = tables.table(key).values
        assert values != tuple(reversed(values))
    assert len({tables.table(k).values for k in ("C_data", "D_data", "E_data")}) == 3


def test_symmetric_matches_independent_q2_values() -> None:
    tables = q6.extract_julia_embedded_tables(
        _source("symmetric"), skeleton_text=SKELETON
    )
    for name in ("A_data", "B_data", "C_data", "D_data"):
        assert set(tables.table(name).values) == {Fraction(1, 2)}
    assert tables.table("E_data").values == (Fraction(1, 4), Fraction(3, 4))


@pytest.mark.parametrize(
    "change",
    (
        lambda s: s + "\nGNN_SPEC = Dict()\n",
        lambda s: s.replace("C_pref = softmax(C)", "C_pref = C"),
        lambda s: s.replace(
            "tensor[next_state, previous_state, action]",
            "tensor[previous_state, next_state, action]",
        ),
        lambda s: s.replace("function run_simulation()", "function alternate()"),
        lambda s: s.replace(
            "const GNN_SPEC =", 'const GNN_SPEC_JSON_B64 = "e30="\nconst GNN_SPEC ='
        ),
        lambda s: s.replace("using JSON", 'using JSON\neval(Meta.parse("1"))'),
        lambda s: s.replace("\n", "\r\n"),
    ),
)
def test_rejects_every_nonpayload_change(change) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(ArtifactProofError, match="skeleton_mismatch|invalid_base64"):
        q6.extract_julia_embedded_tables(change(_source()), skeleton_text=SKELETON)


def test_rejects_caller_supplied_changed_skeleton() -> None:
    with pytest.raises(ArtifactProofError, match="unapproved_skeleton"):
        q6.extract_julia_embedded_tables(_source(), skeleton_text=SKELETON + "\n")


@pytest.mark.parametrize(
    "encoded", ("", "!", "Zg=", "Zg===", "Zh==", "e30=\n", 'e30="; error("bad")')
)
def test_invalid_or_noncanonical_base64(encoded: str) -> None:
    with pytest.raises(ArtifactProofError, match="invalid_base64"):
        q6.extract_julia_embedded_tables(
            SKELETON.replace(q6.SLOT, encoded), skeleton_text=SKELETON
        )


@pytest.mark.parametrize(
    "payload",
    (b"\xff", b"[]", b"{} trailing", b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":Infinity}'),
)
def test_invalid_json_and_duplicate_keys(payload: bytes) -> None:
    with pytest.raises(ArtifactProofError):
        q6.extract_julia_embedded_tables(_wrap(payload), skeleton_text=SKELETON)


@pytest.mark.parametrize(
    "bad", (True, False, None, "0.5", -0.5, 1.5, 0.1, 0.000001, 1e100, [])
)
def test_rejects_invalid_numeric_leaf(bad: object) -> None:
    document = _document()
    document["initialparameterization"]["A"][0][0] = bad  # type: ignore[index]
    with pytest.raises(ArtifactProofError):
        _extract_document(document)


@pytest.mark.parametrize(
    "tamper",
    (
        "missing_e",
        "extra_table",
        "ragged",
        "dimension",
        "boolean_dimension",
        "axis",
        "provenance",
        "schema",
        "unnormalized",
    ),
)
def test_document_and_table_contract(tamper: str) -> None:
    document = _document()
    initial = document["initialparameterization"]
    params = document["model_parameters"]
    if tamper == "missing_e":
        del initial["E"]  # type: ignore[attr-defined]
    elif tamper == "extra_table":
        initial["F"] = [0.5, 0.5]  # type: ignore[index]
    elif tamper == "ragged":
        initial["B"][0][0].pop()  # type: ignore[index]
    elif tamper in ("dimension", "boolean_dimension"):
        params["num_hidden_states"] = 3 if tamper == "dimension" else True  # type: ignore[index]
    elif tamper == "axis":
        params["b_tensor_order"] = "action_previous_next"  # type: ignore[index]
    elif tamper == "provenance":
        document["matrix_provenance"]["B"]["canonical_order"] = "wrong"  # type: ignore[index]
    elif tamper == "schema":
        document["canonical_pomdp_schema"] = "future"
    else:
        initial["D"] = [0.5, 0.75]  # type: ignore[index]
    with pytest.raises(ArtifactProofError):
        _extract_document(document)


@pytest.mark.parametrize("order", list(itertools.permutations(range(3)))[1:])
def test_all_five_b_axis_permutations_change_independent_oracle(
    order: tuple[int, ...],
) -> None:
    document = _document()
    original = document["initialparameterization"]["B"]  # type: ignore[index]
    mutated = copy.deepcopy(original)
    for indices in itertools.product(range(2), repeat=3):
        i, j, k = indices
        a, b, c = (indices[position] for position in order)
        mutated[i][j][k] = original[a][b][c]
    document["initialparameterization"]["B"] = mutated  # type: ignore[index]
    try:
        tables = _extract_document(document)
    except ArtifactProofError as error:
        assert error.reason == "normalization_violation"
    else:
        assert tables.table("B_data").values != EXPECTED_ASYM["B_data"]
        probe = q6.render_julia_input_probe(tables, variant="asymmetric")
        assert q6.ASYMMETRIC_ORACLE_LEAN in probe
        assert probe != q6.render_julia_input_probe(
            q6.extract_julia_embedded_tables(_source(), skeleton_text=SKELETON),
            variant="asymmetric",
        )


def test_previous_action_exchange_stays_normalized_but_changes_oracle() -> None:
    document = _document()
    original = document["initialparameterization"]["B"]  # type: ignore[index]
    document["initialparameterization"]["B"] = [  # type: ignore[index]
        [[original[i][k][j] for k in range(2)] for j in range(2)] for i in range(2)
    ]
    tables = _extract_document(document)
    assert tables.table("B_data").values != EXPECTED_ASYM["B_data"]


def test_generator_is_deterministic_readonly_and_scope_explicit() -> None:
    generator = _generator()
    texts, manifest = generator.regenerate()
    assert generator.regenerate() == (texts, manifest)
    before = {
        p: (p.read_bytes(), p.stat().st_mtime_ns)
        for p in (SLICE / "generated").iterdir()
    }
    assert generator.main(["--check"]) == 0
    assert {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in before} == before
    assert manifest["native_verification"] == "not_established_by_generation"
    assert (
        manifest["backend_contract"]["consumed_c_identical_to_embedded_input"] is False
    )
    assert set(texts) == {
        "generated/probe_symmetric.lean",
        "generated/probe_asymmetric.lean",
        "generated/artifact_proof_manifest.json",
    }
    for variant in q6.VARIANTS:
        probe = texts[f"generated/probe_{variant}.lean"]
        for name in q6.THEOREMS[variant]:
            assert f"theorem {name}" in probe
        assert "not runtime-consumed C" in probe
        assert "sorry" not in probe
        assert "axiom " not in probe


def test_contract_returns_fresh_metadata() -> None:
    contract = q6.backend_contract()
    contract["scope"] = "wrong"
    assert q6.backend_contract()["scope"] == q6.SCOPE


def test_size_bound_and_unknown_probe_variant() -> None:
    with pytest.raises(ArtifactProofError, match="source_too_large"):
        q6.extract_julia_embedded_tables(
            "x" * (q6.MAX_SOURCE_BYTES + 1), skeleton_text=SKELETON
        )
    tables = q6.extract_julia_embedded_tables(_source(), skeleton_text=SKELETON)
    with pytest.raises(ArtifactProofError, match="unknown_variant"):
        q6.render_julia_input_probe(tables, variant="unknown")


@pytest.mark.serial_lean
@pytest.mark.parametrize("variant", q6.VARIANTS)
def test_native_embedded_input_probe_and_axioms(tmp_path: Path, variant: str) -> None:
    """Native-only acceptance; the draft Python run explicitly deselects this."""
    from fep_lean.verification.formalism_audit import parse_axiom_output
    from tests._support.lean_runner import run_lean_probe

    expected = tuple(f"{q6.NAMESPACES[variant]}.{n}" for n in q6.THEOREMS[variant])
    probe = tmp_path / f"q6_{variant}.lean"
    source = (SLICE / "generated" / f"probe_{variant}.lean").read_text()
    source += "\n" + "\n".join(f"#print axioms {name}" for name in expected) + "\n"
    probe.write_text(source)
    result = run_lean_probe(
        probe,
        import_root=ROOT / "src/fep_lean/formal",
        cwd=ROOT / "lean",
        timeout_s=1800,
    )
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "warning:" not in output and "sorry" not in output
    reports, errors = parse_axiom_output(output, expected=expected)
    assert not errors, errors
    assert set(reports) == set(expected)
    assert all(
        set(axioms) <= {"propext", "Classical.choice", "Quot.sound"}
        for axioms in reports.values()
    )


@pytest.mark.serial_lean
def test_native_normalized_previous_action_swap_is_rejected(tmp_path: Path) -> None:
    """Reject an axis error that passes all probability normalization checks."""
    from tests._support.lean_runner import run_lean_probe

    document = _document()
    original = document["initialparameterization"]["B"]  # type: ignore[index]
    document["initialparameterization"]["B"] = [  # type: ignore[index]
        [[original[i][k][j] for k in range(2)] for j in range(2)] for i in range(2)
    ]
    tables = _extract_document(document)
    source = q6.render_julia_input_probe(tables, variant="asymmetric")
    assert q6.ASYMMETRIC_ORACLE_LEAN in source
    probe = tmp_path / "q6_wrong_axes.lean"
    probe.write_text(source)
    result = run_lean_probe(
        probe,
        import_root=ROOT / "src/fep_lean/formal",
        cwd=ROOT / "lean",
        timeout_s=1800,
    )
    output = result.stdout + result.stderr
    assert result.returncode != 0
    assert "unsolved goals" in output or "type mismatch" in output.lower(), output
