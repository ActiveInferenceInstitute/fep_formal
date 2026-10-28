"""Q7 static extraction, exact-number, input-gauge, and custody regressions.

These tests neither import the generated runner nor launch Lean. Native proof
acceptance is a separate serial gate owned by the shared receipt engine.
"""

from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import json
import shutil
import sys
import types
from fractions import Fraction
from pathlib import Path

import pytest

from fep_formal.verification import gnn_continuous_artifact_proof as q7
from fep_formal.verification.gnn_continuous_artifact_proof import (
    EPSILON,
    ContinuousArtifactError,
    canonical_json,
    canonical_scaffold_bytes,
    exact_coefficient_intervals,
    extract_continuous_artifact,
    read_json_object,
    render_lean_probe,
    scaffold_digest,
    validate_expected,
    validate_input_document,
    validate_render_provenance,
)

ROOT = Path(__file__).resolve().parents[1]
SLICE = ROOT / "specs/gnn-bridge-q7-continuous-ou-proof"
RUNNER = SLICE / "fixtures/continuous_ou_jax.py"
SOURCE = SLICE / "fixtures/FepLeanContinuousOU.md"


@pytest.fixture
def expected():
    return json.loads((SLICE / "expected.json").read_text())


@pytest.fixture
def runner():
    return RUNNER.read_text()


def test_decimal_lexeme_and_binary64_are_distinct_exact_numbers(runner, expected):
    artifact = extract_continuous_artifact(runner, expected)
    f = artifact.numbers["F_RAW"]
    q = artifact.numbers["Q_RAW"]
    assert f.decimal == Fraction(36787944117144233, 10**17)
    assert f.binary64 == Fraction(828390857088487, 2251799813685248)
    assert q.binary64 == Fraction(7788207392432013, 9007199254740992)
    assert f.binary64 != f.decimal
    assert q.binary64 != q.decimal
    assert f.binary64_hex == "0x1.78b56362cef38p-2"
    validate_input_document(SOURCE.read_text(), artifact)


def test_intervals_certify_error_without_an_exp_float_oracle(runner, expected):
    artifact = extract_continuous_artifact(runner, expected)
    for name, (lower, upper) in exact_coefficient_intervals().items():
        assert 0 < lower < upper < 1
        actual = artifact.numbers[name].binary64
        assert max(abs(actual - lower), abs(actual - upper)) < EPSILON


@pytest.mark.parametrize(
    "old,new,reason",
    [
        ("F_RAW = [[0.36787944117144233]]", "F_RAW = [[1.0]]", "coefficient_bound"),
        ("Q_RAW = [[0.8646647167633873]]", "Q_RAW = [[0.0]]", "coefficient_bound"),
        ("H_RAW = [[1.0]]", "H_RAW = [[2.0]]", "gauge"),
        ("R_RAW = [[1.0]]", "R_RAW = [[0.0]]", "gauge"),
        ("PRIOR_MEAN_RAW = [0.0]", "PRIOR_MEAN_RAW = [1.0]", "gauge"),
        ("PRIOR_COV_RAW = [[1.0]]", "PRIOR_COV_RAW = [[2.0]]", "gauge"),
        ("F_RAW = [[0.36787944117144233]]", "F_RAW = [[1e999]]", "nonfinite"),
        ("H_RAW = [[1.0]]", "H_RAW = [[True]]", "literal"),
        ("H_RAW = [[1.0]]", "H_RAW = [[-1.0]]", "literal"),
        ("H_RAW = [[1.0]]", "H_RAW = [[float('nan')]]", "literal"),
        ("H_RAW = [[1.0]]", "H_RAW = [[1/1]]", "literal"),
        ("H_RAW = [[1.0]]", "H_RAW = [[0x1]]", "literal"),
        ("H_RAW = [[1.0]]", "H_RAW = [1.0]", "shape"),
        ("H_RAW = [[1.0]]", "H_RAW = [[1.0, 1.0]]", "shape"),
        ("H_RAW = [[1.0]]", "H_RAW = ((1.0,),)", "shape"),
        ("H_RAW = [[1.0]]", "H_RAW = [[]]", "shape"),
        ("DT = 1.0", "DT = 0.5", "metadata"),
        ("DT = 1.0", "DT = 1", "metadata"),
        ("NUM_TIMESTEPS = 1", "NUM_TIMESTEPS = 2", "metadata"),
        ("NUM_TIMESTEPS = 1", "NUM_TIMESTEPS = True", "metadata"),
        ("GOAL_MEAN_RAW = None", "GOAL_MEAN_RAW = [0.0]", "metadata"),
        ("CONTROL_GAIN = None", "CONTROL_GAIN = 0.0", "metadata"),
        ("OUTPUT_ENV = 'GNN_OUTPUT_DIR'", "OUTPUT_ENV = 'OTHER'", "metadata"),
        ("H_RAW = [[1.0]]", "", "missing_assignment"),
        ("H_RAW = [[1.0]]", "H_RAW = [[1.0]]\nH_RAW = [[1.0]]", "duplicate_assignment"),
        ("H_RAW = [[1.0]]", "H_RAW = alias = [[1.0]]", "ambiguous_assignment"),
        ("H_RAW = [[1.0]]", "if True:\n    H_RAW = [[1.0]]", "ambiguous_assignment"),
    ],
)
def test_rejects_parameter_and_time_contract_changes(
    runner, expected, old, new, reason
):
    assert old in runner
    with pytest.raises(ContinuousArtifactError) as error:
        extract_continuous_artifact(runner.replace(old, new), expected)
    assert error.value.reason == reason


@pytest.mark.parametrize(
    "extra",
    [
        "alias = F_RAW\nalias[0][0] = 0.0",
        "F_RAW[0][0] = 0.0",
        "F_RAW.append([0.0])",
        "globals()['F_RAW'] = [[0.0]]",
        "def hidden(F_RAW):\n    return F_RAW",
        "from elsewhere import F_RAW",
        "def F_RAW():\n    return [[0.0]]",
        "def arr(x):\n    return x * 0",
        "def no_op():\n    return None",
    ],
)
def test_frozen_scaffold_rejects_alias_mutation_shadowing_and_unreviewed_code(
    runner, expected, extra
):
    with pytest.raises(ContinuousArtifactError, match="scaffold"):
        extract_continuous_artifact(runner + "\n" + extra, expected)


@pytest.mark.parametrize("extra", ["del F_RAW", "F_RAW += [[0.0]]", "(F_RAW := None)"])
def test_rebinding_cannot_hide_behind_a_single_initial_assignment(
    runner, expected, extra
):
    with pytest.raises(ContinuousArtifactError, match="ambiguous_assignment"):
        extract_continuous_artifact(runner + "\n" + extra, expected)


def test_comment_does_not_execute_but_changes_source_custody(
    runner, expected, tmp_path
):
    marker = tmp_path / "never-written"
    changed = runner + f"\n# open({str(marker)!r}, 'w').write('bad')\n"
    original = extract_continuous_artifact(runner, expected)
    artifact = extract_continuous_artifact(changed, expected)
    assert artifact.scaffold_sha256 == original.scaffold_sha256
    assert artifact.source_sha256 != original.source_sha256
    assert not marker.exists()


@pytest.mark.parametrize(
    "field,value",
    [
        ("epsilon_ratio", [1, 10]),
        ("schema_version", True),
        ("model", "general continuous dynamics"),
        ("runner_ast_sha256", "bad"),
        ("formulas", {"F": "1"}),
        ("gauge", {}),
    ],
)
def test_expected_contract_cannot_relax_the_model_or_tolerance(expected, field, value):
    expected[field] = value
    with pytest.raises(ContinuousArtifactError, match="expected_contract"):
        validate_expected(expected)


@pytest.mark.parametrize(
    "old,new",
    [
        ("step_duration: 1", "step_duration: 2"),
        ("ou_rate: 1", "ou_rate: 2"),
        ("num_timesteps: 1", "num_timesteps: 2"),
        ("prior_mean[1,1,type=float]", "prior_mean[1,type=float]"),
        ("ModelTimeHorizon=1", "ModelTimeHorizon=2"),
        ("((0.36787944117144233))", "((0.3678794411714423))"),
        ("## Footer", "## ModelParameters"),
        ("## Equations", "goal_mean={(0.0)}\n\n## Equations"),
    ],
)
def test_input_gauge_shape_time_and_parameter_custody(runner, expected, old, new):
    source = SOURCE.read_text()
    assert old in source
    with pytest.raises(ContinuousArtifactError, match="input_contract"):
        validate_input_document(
            source.replace(old, new), extract_continuous_artifact(runner, expected)
        )


def test_native_template_uses_dyadic_values_and_no_decimal_identity(runner, expected):
    artifact = extract_continuous_artifact(runner, expected)
    probe = render_lean_probe(artifact, (SLICE / "probe.template.lean").read_text())
    assert "828390857088487 / 2251799813685248" in probe
    assert "7788207392432013 / 9007199254740992" in probe
    assert "Real.exp_one_near_20" in probe
    assert "@@" not in probe
    assert "sorry" not in probe


@pytest.mark.parametrize(
    "template", ["@@F@@", "@@F@@ @@Q@@ @@UNKNOWN@@", "@@F@@ @@F@@ @@Q@@"]
)
def test_unknown_or_duplicate_template_slots_rejected(runner, expected, template):
    with pytest.raises(ContinuousArtifactError, match="template"):
        render_lean_probe(extract_continuous_artifact(runner, expected), template)


def _provenance():
    return json.loads((SLICE / "render_provenance.json").read_text())


def _validate(record, owners=None):
    validate_render_provenance(
        record,
        input_bytes=SOURCE.read_bytes(),
        artifact_bytes=RUNNER.read_bytes(),
        owners=record["owners_before"] if owners is None else owners,
    )


def test_actual_render_record_is_internally_consistent():
    _validate(_provenance())


@pytest.mark.parametrize(
    "key,value",
    [
        ("returncode", True),
        ("returncode", 1),
        ("schema_version", True),
        ("stdout", ""),
        ("stderr", None),
        ("command", []),
        ("render_route", ["invented renderer"]),
        ("owners_after", {}),
        ("input", {}),
        ("output", {}),
        ("source_pin_sha256", "bad"),
        ("native_claim_ready", True),
    ],
)
def test_render_provenance_rejects_fabricated_or_incomplete_evidence(key, value):
    record = _provenance()
    record[key] = value
    with pytest.raises(ContinuousArtifactError, match="render_custody"):
        _validate(record)


def test_render_provenance_rejects_current_source_owner_drift():
    record = _provenance()
    current = copy.deepcopy(record["owners_before"])
    first = next(iter(current["gnn"]))
    current["gnn"][first] = "0" * 64
    with pytest.raises(ContinuousArtifactError, match="render_custody"):
        _validate(record, current)


@pytest.mark.parametrize(
    "source",
    [
        '{"schema_version": 1, "schema_version": 1}',
        '{"nested": {"F": 1, "F": 2}}',
        '{"F": NaN}',
        '{"F": Infinity}',
        "[]",
        "null",
        "{unfinished",
        b"\xff",
    ],
)
def test_json_custody_rejects_ambiguous_and_nonstandard_records(source):
    with pytest.raises(ContinuousArtifactError, match="json"):
        read_json_object(source)


def test_checked_extractor_buffer_rejects_replacement_before_execution(tmp_path):
    spec = importlib.util.spec_from_file_location(
        "q7_generator_race", SLICE / "generate_probe.py"
    )
    assert spec is not None and spec.loader is not None
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    relative = "src/fep_formal/verification/gnn_continuous_artifact_proof.py"
    path = tmp_path / relative
    path.parent.mkdir(parents=True)
    good = (ROOT / relative).read_bytes()
    import hashlib

    generator._VERIFIED_ARTIFACT_DIGESTS = {relative: hashlib.sha256(good).hexdigest()}
    marker = tmp_path / "must-not-execute"
    path.write_text(
        f"from pathlib import Path\nPath({str(marker)!r}).write_text('bad')\n"
    )
    with pytest.raises(ValueError, match="extractor changed"):
        generator._extractor(tmp_path)
    assert not marker.exists()


def _synthetic_current_profile(
    root: Path, generator: types.ModuleType, extra=()
) -> None:
    """Construct test-only bookkeeping; this does not observe any runtime."""
    for name in {
        *generator.PORTABILITY_INPUTS,
        *generator.EXTRA_FILES,
        generator.PROVENANCE,
        *extra,
    }:
        destination = root / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, destination)
    path = root / generator.PORTABILITY_EVIDENCE
    evidence = json.loads(path.read_text())
    evidence["test_fixture"] = (
        "synthetic current bindings; no runtime or native acceptance"
    )
    evidence["inputs"] = {
        name: hashlib.sha256((root / name).read_bytes()).hexdigest()
        for name in generator.PORTABILITY_INPUTS
    }
    path.write_text(json.dumps(evidence))


def test_generator_is_read_only_and_manifest_does_not_claim_native_evidence(
    tmp_path: Path,
):
    spec = importlib.util.spec_from_file_location(
        "q7_generator_test", SLICE / "generate_probe.py"
    )
    assert spec is not None and spec.loader is not None
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    watched = [
        path
        for path in SLICE.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    ]
    before = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in watched}
    _synthetic_current_profile(tmp_path / "source", generator)
    texts, manifest = generator.regenerate(tmp_path / "source")
    output = tmp_path / "fresh"
    args = ["--source-root", str(tmp_path / "source"), "--output-root", str(output)]
    assert generator.main(args) == 0
    assert generator.main(["--check", *args]) == 0
    with pytest.raises(SystemExit):
        generator.main(args)
    with pytest.raises(SystemExit):
        generator.main([])
    probe = output / "generated/probe.lean"
    probe.write_text(probe.read_text() + "\n-- tampered\n")
    with pytest.raises(ValueError, match="generated artifacts differ"):
        generator.main(["--check", *args])
    assert set(texts) == {
        "generated/probe.lean",
        "generated/artifact_proof_manifest.json",
    }
    assert "required separately" in manifest["native_evidence"]
    assert manifest["receipt_contract"]["canonical_variant"] == "ou"
    assert canonical_json(manifest) == texts["generated/artifact_proof_manifest.json"]
    assert {
        path: (path.read_bytes(), path.stat().st_mtime_ns) for path in watched
    } == before
    assert (
        scaffold_digest(RUNNER.read_text())
        == json.loads((SLICE / "expected.json").read_text())["runner_ast_sha256"]
    )


def test_native_contract_binds_portability_artifacts_and_json_reader(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """The native snapshot must bind the actual retained serialization inputs."""
    spec = importlib.util.spec_from_file_location(
        "q7_native_contract_test", SLICE / "verify_native.py"
    )
    assert spec is not None and spec.loader is not None
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    prefix = SLICE.relative_to(ROOT).as_posix()
    required = {
        f"{prefix}/scaffold-serialization.md",
        f"{prefix}/generated/scaffold-canonical.json",
        f"{prefix}/generated/scaffold-runtime-parity.json",
        "src/fep_formal/verification/_jsonutil.py",
        "src/fep_formal/_paths.py",
    }
    assert required <= set(adapter.CONTRACT.extra_files)
    assert required <= adapter.VERIFICATION._artifact_files()
    spec = importlib.util.spec_from_file_location(
        "q7_native_profile", SLICE / "generate_probe.py"
    )
    assert spec is not None and spec.loader is not None
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    original_files = adapter.VERIFICATION._artifact_files()
    _synthetic_current_profile(tmp_path, generator, original_files)
    outputs, _ = generator.regenerate(tmp_path)
    for name, text in outputs.items():
        destination = tmp_path / generator.PREFIX / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(text)
    adapter.VERIFICATION.root = tmp_path
    authority = {
        name: q7.digest((tmp_path / name).read_bytes())
        for name in adapter.VERIFICATION._artifact_files()
    }
    poisoned = types.ModuleType("fep_formal.verification._jsonutil")

    def reject_cached_reader(*_args, **_kwargs):
        raise AssertionError("ambient cached JSON reader was executed")

    poisoned.load_strict_json = reject_cached_reader
    monkeypatch.setitem(sys.modules, poisoned.__name__, poisoned)
    # Native regeneration must execute the bound reader bytes through the
    # private checked-import authority, even when canonical imports are poisoned.
    adapter.VERIFICATION._regenerate(authority[adapter.CONTRACT.generator], authority)


def test_frozen_scaffold_digest_reproduces_the_pinned_interpreter_contract(
    monkeypatch: pytest.MonkeyPatch,
):
    """The accepted Q7 scaffold validates under exactly the pinned interpreter.

    Candidate canonical bytes have a separate portability contract. Actual
    scaffold/extraction validation keeps the pinned CPython 3.14 guard and
    refuses before parsing under an unsupported interpreter.
    """
    pinned = (ROOT / ".python-version").read_text().strip()
    assert pinned == "3.14"
    assert ".".join(str(part) for part in sys.version_info[:2]) == pinned
    monkeypatch.setattr(
        sys, "implementation", types.SimpleNamespace(name="pypy"), raising=True
    )
    monkeypatch.setattr(sys, "version_info", (3, 12, 9, "final", 0), raising=True)
    with pytest.raises(ContinuousArtifactError) as refused:
        scaffold_digest("invalid syntax !!!")
    assert refused.value.reason == "interpreter"
    assert "cpython 3.14" in str(refused.value)
    assert "pypy 3.12" in str(refused.value)
    monkeypatch.setattr(
        sys, "implementation", types.SimpleNamespace(name="cpython"), raising=True
    )
    monkeypatch.setattr(sys, "version_info", (3, 14, 2, "final", 0), raising=True)
    accepted_digest = scaffold_digest(RUNNER.read_text())
    monkeypatch.undo()
    assert (
        accepted_digest
        == scaffold_digest(RUNNER.read_text())
        == json.loads((SLICE / "expected.json").read_text())["runner_ast_sha256"]
    )


@pytest.mark.parametrize(
    "old,new",
    [
        ("def solve(a, b):", "def solve(b, a):"),
        ("def arr(x):", "def arr(x: int) -> float:"),
        ("def eye(n):", "@arr\ndef eye(n):"),
        ("RANDOM_SEED = 42", "RANDOM_SEED = 43"),
        ("DT = 1.0", "DT = 1"),
        ("jax_enable_x64', True", "jax_enable_x64', 1"),
        ("gain * (goal - mu)", "gain * (mu - goal)"),
        ("parents=True, exist_ok=True", "exist_ok=True, parents=True"),
        ("{FRAMEWORK} continuous", "{FRAMEWORK!r} continuous"),
        ("MODEL_NAME = 'FepLean", "MODEL_NAME = 'Other FepLean"),
        ("RANDOM_SEED = 42", "RANDOM_SEED = 42  # type: int"),
        ("def arr(x):", "def arr(x=1):"),
    ],
)
def test_canonical_scaffold_retains_semantic_fields_types_and_order(
    runner: str, old: str, new: str
) -> None:
    assert old in runner
    assert canonical_scaffold_bytes(runner.replace(old, new)) != (
        canonical_scaffold_bytes(runner)
    )


def test_canonical_scaffold_ignores_only_locations_comments_and_six_values(
    runner: str,
) -> None:
    source = runner
    for old, new in (
        ("F_RAW = [[0.36787944117144233]]", "F_RAW = [[0.123]]"),
        ("H_RAW = [[1.0]]", "H_RAW = [[2.0]]"),
        ("Q_RAW = [[0.8646647167633873]]", "Q_RAW = [[0.234]]"),
        ("R_RAW = [[1.0]]", "R_RAW = [[3.0]]"),
        ("PRIOR_MEAN_RAW = [0.0]", "PRIOR_MEAN_RAW = [4.0]"),
        ("PRIOR_COV_RAW = [[1.0]]", "PRIOR_COV_RAW = [[5.0]]"),
    ):
        assert old in source
        source = source.replace(old, new)
    assert canonical_scaffold_bytes("\n\n" + source + "\n# harmless comment\n") == (
        canonical_scaffold_bytes(runner)
    )


def test_canonical_scaffold_normalizes_only_absent_empty_function_type_params(
    runner: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    tree = ast.parse(runner, type_comments=True)
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef))
    expected_node = q7._canonical_scaffold_value(function)
    absent = copy.deepcopy(function)
    del absent.type_params
    fields = ast.FunctionDef._fields
    monkeypatch.setattr(ast.FunctionDef, "_fields", fields[:-1])
    assert q7._canonical_scaffold_value(absent) == expected_node
    absent.type_params = [ast.Name(id="T", ctx=ast.Load())]
    with pytest.raises(
        ContinuousArtifactError, match="type_params must be absent or empty"
    ):
        q7._canonical_scaffold_value(absent)


@pytest.mark.parametrize(
    "defect", ["unknown_field", "field_order", "attribute", "missing"]
)
def test_canonical_scaffold_rejects_unreviewed_field_schema(
    monkeypatch: pytest.MonkeyPatch, defect: str
) -> None:
    node = ast.Name(id="x", ctx=ast.Load())
    if defect == "unknown_field":
        monkeypatch.setattr(ast.Name, "_fields", (*ast.Name._fields, "future_semantic"))
    elif defect == "field_order":
        monkeypatch.setattr(ast.Name, "_fields", tuple(reversed(ast.Name._fields)))
    elif defect == "attribute":
        node.future_semantic = "unreviewed"
    else:
        del node.id
    with pytest.raises(ContinuousArtifactError) as error:
        q7._canonical_scaffold_value(node)
    assert error.value.reason == "scaffold_schema"


@pytest.mark.parametrize(
    "extra", ["class Unreviewed: pass", "def generator():\n    yield 1"]
)
def test_canonical_scaffold_rejects_unreviewed_nodes(runner: str, extra: str) -> None:
    with pytest.raises(ContinuousArtifactError) as error:
        canonical_scaffold_bytes(runner + "\n" + extra)
    assert error.value.reason == "scaffold_schema"


@pytest.mark.parametrize(
    "value", [float("inf"), float("nan"), 1j, b"new literal", (1, 2)]
)
def test_canonical_scaffold_rejects_unreviewed_or_nonfinite_scalars(
    value: object,
) -> None:
    with pytest.raises(ContinuousArtifactError) as error:
        q7._canonical_scaffold_value(ast.Constant(value=value))
    assert error.value.reason == "scaffold_schema"


def test_canonical_candidate_interpreter_guard_runs_before_parse(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "version_info", (3, 15, 0, "final", 0))
    with pytest.raises(ContinuousArtifactError) as error:
        canonical_scaffold_bytes("invalid syntax !!!")
    assert error.value.reason == "interpreter"


@pytest.mark.parametrize(
    "defect",
    [
        None,
        "owner",
        "canonical_bytes",
        "schema_bool",
        "missing_runtime",
        "false_control",
        "numeric_control",
        "wrong_minor",
        "unknown_fields",
        "missing_present_node",
        "absent_allowed_node",
        "extra_absent_node",
    ],
)
def test_synthetic_portability_schema_refuses_stale_or_rejecting_inputs(
    tmp_path: Path, defect: str | None
) -> None:
    spec = importlib.util.spec_from_file_location(
        "q7_parity_check_test", SLICE / "generate_probe.py"
    )
    assert spec is not None and spec.loader is not None
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    api = generator._extractor(ROOT)
    _synthetic_current_profile(tmp_path, generator)
    evidence_path = tmp_path / generator.PORTABILITY_EVIDENCE
    evidence = json.loads(evidence_path.read_text())
    source = RUNNER.read_text()
    if defect in {"absent_allowed_node", "extra_absent_node"}:
        # Artificial parser fixture, never a renderer/native/scientific result:
        # remove one allowed class and keep the other schema fields intact.
        class WithoutPow(ast.NodeTransformer):
            def visit_BinOp(self, node: ast.BinOp) -> ast.expr:
                rewritten = self.generic_visit(node)
                assert isinstance(rewritten, ast.BinOp)
                if isinstance(rewritten.op, ast.Pow):
                    return ast.copy_location(ast.Constant(value=0), rewritten)
                return rewritten

        source = ast.unparse(WithoutPow().visit(ast.parse(source)))
        assert not any(
            isinstance(node, ast.Pow) for node in ast.walk(ast.parse(source))
        )
        fixture = generator.FIXTURES["ou"]
        (tmp_path / fixture).write_text(source)
        encoded = api.canonical_scaffold_bytes(source)
        (tmp_path / generator.CANONICAL_SCAFFOLD).write_bytes(encoded)
        evidence["inputs"][fixture] = hashlib.sha256(source.encode()).hexdigest()
        evidence["canonical_bytes"] = len(encoded)
        evidence["canonical_sha256"] = hashlib.sha256(encoded).hexdigest()
        for record in evidence["runtimes"]:
            record["canonical_sha256"] = evidence["canonical_sha256"]
            record["observed_fields"].pop("Pow")
            if defect == "extra_absent_node":
                record["observed_fields"]["Pow"] = []
    if defect == "owner":
        (tmp_path / generator.EXTRACTOR).write_text("# changed extractor\n")
    elif defect == "canonical_bytes":
        (tmp_path / generator.CANONICAL_SCAFFOLD).write_bytes(b"[]\n")
    elif defect == "schema_bool":
        evidence["schema_version"] = True
    elif defect == "missing_runtime":
        evidence["runtimes"].pop()
    elif defect == "false_control":
        evidence["runtimes"][0]["controls"]["unknown_field"] = False
    elif defect == "numeric_control":
        evidence["runtimes"][0]["controls"]["unknown_field"] = 1
    elif defect == "wrong_minor":
        evidence["runtimes"][0]["version_info"] = [3, 14, 4]
    elif defect == "unknown_fields":
        evidence["runtimes"][0]["observed_fields"]["FunctionDef"].append("future")
    elif defect == "missing_present_node":
        evidence["runtimes"][0]["observed_fields"].pop("Call")
    evidence_path.write_text(json.dumps(evidence))
    watched = [path for path in tmp_path.rglob("*") if path.is_file()]
    before = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in watched}
    if defect not in {None, "absent_allowed_node"}:
        with pytest.raises(ValueError, match="Q7.*(parity|runtime observation)"):
            generator.validate_scaffold_portability(tmp_path, api, source)
    else:
        generator.validate_scaffold_portability(tmp_path, api, source)
    assert before == {
        path: (path.read_bytes(), path.stat().st_mtime_ns) for path in watched
    }


def test_q7_stale_parity_is_rejected_without_repair(tmp_path):
    spec = importlib.util.spec_from_file_location(
        "q7_stale_profile", SLICE / "generate_probe.py"
    )
    assert spec is not None and spec.loader is not None
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    _synthetic_current_profile(tmp_path, generator)
    path = tmp_path / generator.PORTABILITY_EVIDENCE
    evidence = json.loads(path.read_text())
    evidence["inputs"][generator.EXTRACTOR] = "0" * 64
    path.write_text(json.dumps(evidence))
    before = path.read_bytes(), path.stat().st_mtime_ns
    with pytest.raises(ValueError, match="parity evidence is stale"):
        generator.validate_scaffold_portability(
            tmp_path, generator._extractor(tmp_path), RUNNER.read_text()
        )
    with pytest.raises(ValueError, match="parity evidence is stale"):
        generator.main(["--check", "--source-root", str(tmp_path)])
    assert (path.read_bytes(), path.stat().st_mtime_ns) == before


@pytest.mark.parametrize("scaffold", [True, False])
@pytest.mark.parametrize(
    "defect",
    [
        None,
        "partial",
        "unknown",
        "tamper",
        "source_drift",
        "symlink",
        "directory",
        "alias",
        "duplicate_json",
        "hardlink",
        "parent_symlink",
        "unknown_field",
    ],
)
def test_publication_synthetic_schema_controls(tmp_path, scaffold, defect):
    """Synthetic bookkeeping exercises publication only, never runtime evidence."""
    spec = importlib.util.spec_from_file_location(
        "q7_publish_test", SLICE / "generate_probe.py"
    )
    assert spec is not None and spec.loader is not None
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    root = tmp_path / "source"
    _synthetic_current_profile(
        root, generator, [generator.MANIFEST, generator.PROBES["ou"]]
    )
    evidence_path = root / generator.PORTABILITY_EVIDENCE
    evidence = json.loads(evidence_path.read_text())
    evidence.pop("test_fixture")
    evidence_path.write_text(json.dumps(evidence))
    incoming = tmp_path / "incoming"
    generated = incoming / "generated"
    generated.mkdir(parents=True)
    if scaffold:
        for name in (generator.CANONICAL_SCAFFOLD, generator.PORTABILITY_EVIDENCE):
            shutil.copyfile(root / name, generated / Path(name).name)
    else:
        outputs, _ = generator.regenerate(root)
        for name, data in outputs.items():
            (incoming / name).write_text(data)
    chosen = generated / (
        "scaffold-runtime-parity.json" if scaffold else "artifact_proof_manifest.json"
    )
    if defect == "partial":
        chosen.unlink()
    elif defect == "unknown":
        (generated / "extra").write_text("unknown")
    elif defect == "tamper":
        chosen.write_text("{}")
    elif defect == "source_drift":
        with (root / generator.SERIALIZATION_PROTOCOL).open("a") as stream:
            stream.write("\nChanged owner\n")
    elif defect == "symlink":
        data = chosen.read_bytes()
        chosen.unlink()
        target = tmp_path / "linked"
        target.write_bytes(data)
        chosen.symlink_to(target)
    elif defect == "directory":
        chosen.unlink()
        chosen.mkdir()
    elif defect == "alias":
        incoming = root / generator.PREFIX
    elif defect == "duplicate_json":
        chosen.write_text(
            chosen.read_text().replace(
                '"schema_version": 1', '"schema_version": 1, "schema_version": 1'
            )
        )
    elif defect == "hardlink":
        (tmp_path / "hardlink").hardlink_to(chosen)
    elif defect == "parent_symlink":
        link = tmp_path / "incoming-link"
        link.symlink_to(incoming, target_is_directory=True)
        incoming = link
    elif defect == "unknown_field":
        document = json.loads(chosen.read_text())
        document["unknown"] = True
        chosen.write_text(json.dumps(document))
    destination = root / generator.PREFIX / "generated"
    before = {p.name: p.read_bytes() for p in destination.iterdir()}
    args = [
        "--source-root",
        str(root),
        "--publish-scaffold-from" if scaffold else "--publish-generated-from",
        str(incoming),
    ]
    if defect is not None:
        with pytest.raises(ValueError):
            generator.main(args)
        assert before == {p.name: p.read_bytes() for p in destination.iterdir()}
        assert not list(destination.parent.glob(".generated-*"))
    else:
        expected_bytes = {p.name: p.read_bytes() for p in generated.iterdir()}
        assert generator.main(args) == 0
        assert before | expected_bytes == {
            p.name: p.read_bytes() for p in destination.iterdir()
        }
        backups = list(destination.parent.glob(".generated-before-*"))
        assert len(backups) == 1
        assert before == {p.name: p.read_bytes() for p in backups[0].iterdir()}
        assert not list(destination.parent.glob(".generated-publish-*"))


def test_publication_install_failure_restores_real_directory(tmp_path):
    spec = importlib.util.spec_from_file_location(
        "q7_publish_rollback", SLICE / "generate_probe.py"
    )
    assert spec is not None and spec.loader is not None
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    destination = tmp_path / "generated"
    destination.mkdir()
    (destination / "preimage").write_bytes(b"unchanged")
    backup = tmp_path / "backup"
    with pytest.raises(FileNotFoundError):
        generator._install_publication(tmp_path / "missing-stage", destination, backup)
    assert (destination / "preimage").read_bytes() == b"unchanged"
    assert not backup.exists()


@pytest.mark.parametrize("mutation", ["owner", "candidate"])
@pytest.mark.parametrize("scaffold", [True, False])
def test_publication_rejects_real_post_staging_drift(tmp_path, mutation, scaffold):
    """Mutate actual files after a real fsync; synthetic parity is not a capture."""
    spec = importlib.util.spec_from_file_location(
        "q7_publish_drift", SLICE / "generate_probe.py"
    )
    assert spec is not None and spec.loader is not None
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    root = tmp_path / "source"
    _synthetic_current_profile(
        root, generator, [generator.MANIFEST, generator.PROBES["ou"]]
    )
    evidence_path = root / generator.PORTABILITY_EVIDENCE
    evidence = json.loads(evidence_path.read_text())
    evidence.pop("test_fixture")
    evidence_path.write_text(json.dumps(evidence))
    incoming = tmp_path / "incoming"
    generated = incoming / "generated"
    generated.mkdir(parents=True)
    if scaffold:
        for name in (generator.CANONICAL_SCAFFOLD, generator.PORTABILITY_EVIDENCE):
            shutil.copyfile(root / name, generated / Path(name).name)
    else:
        outputs, _ = generator.regenerate(root)
        for name, data in outputs.items():
            (incoming / name).write_text(data)
    changed_path = (
        root / generator.SERIALIZATION_PROTOCOL
        if mutation == "owner"
        else generated / ("scaffold-canonical.json" if scaffold else "probe.lean")
    )
    changed_before = changed_path.read_bytes()
    destination = root / generator.PREFIX / "generated"
    before = {p.name: p.read_bytes() for p in destination.iterdir()}
    original_fsync = generator.os.fsync
    mutations = []

    def fsync_then_mutate(fd):
        original_fsync(fd)
        if not mutations:
            changed_path.write_bytes(changed_before + b"\nchanged during staging\n")
            mutations.append(changed_path)

    generator.os.fsync = fsync_then_mutate
    try:
        with pytest.raises(ValueError, match="inputs changed before installation"):
            generator.publish(root, incoming, scaffold=scaffold)
    finally:
        generator.os.fsync = original_fsync
    assert mutations == [changed_path]
    assert changed_path.read_bytes() != changed_before
    assert before == {p.name: p.read_bytes() for p in destination.iterdir()}
    assert not list(destination.parent.glob(".generated-*"))


@pytest.mark.parametrize("recipe", [None, 1, "", " \n\t"])
def test_publication_rejects_malformed_stored_recipe(tmp_path, recipe):
    spec = importlib.util.spec_from_file_location(
        "q7_publish_recipe", SLICE / "generate_probe.py"
    )
    assert spec is not None and spec.loader is not None
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    root = tmp_path / "source"
    _synthetic_current_profile(
        root, generator, [generator.MANIFEST, generator.PROBES["ou"]]
    )
    incoming = tmp_path / "incoming"
    generated = incoming / "generated"
    generated.mkdir(parents=True)
    shutil.copyfile(
        root / generator.CANONICAL_SCAFFOLD, generated / "scaffold-canonical.json"
    )
    evidence = json.loads((root / generator.PORTABILITY_EVIDENCE).read_text())
    evidence.pop("test_fixture")
    evidence["probe_command"] = recipe
    (generated / "scaffold-runtime-parity.json").write_text(json.dumps(evidence))
    destination = root / generator.PREFIX / "generated"
    before = {p.name: p.read_bytes() for p in destination.iterdir()}
    with pytest.raises(ValueError, match="probe_command must be a nonempty recipe"):
        generator.publish(root, incoming, scaffold=True)
    assert before == {p.name: p.read_bytes() for p in destination.iterdir()}
    assert not list(destination.parent.glob(".generated-*"))
