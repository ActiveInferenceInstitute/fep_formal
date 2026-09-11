"""Q7 static extraction, exact-number, input-gauge, and custody regressions.

These tests neither import the generated runner nor launch Lean. Native proof
acceptance is a separate serial gate owned by the shared receipt engine.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from fractions import Fraction
from pathlib import Path

import pytest

from fep_lean.verification.gnn_continuous_artifact_proof import (
    EPSILON,
    ContinuousArtifactError,
    canonical_json,
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
    relative = "src/fep_lean/verification/gnn_continuous_artifact_proof.py"
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


def test_generator_is_read_only_and_manifest_does_not_claim_native_evidence():
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
    texts, manifest = generator.regenerate()
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


def test_frozen_scaffold_digest_reproduces_the_pinned_interpreter_contract():
    """The accepted Q7 scaffold validates under exactly the pinned interpreter.

    ``scaffold_digest`` freezes ``ast.dump`` output, which is CPython
    minor-version-sensitive. The reviewed ``expected.json`` digest is pinned
    under CPython 3.14 (the ``.python-version`` pin) and must be re-validated
    on the same minor version; until FEP-SCAFFOLD-PORTABILITY records a
    version-stable serialization with a new reviewed scaffold, no other
    interpreter is accepted to reproduce ``runner_ast_sha256``.
    """
    pinned = (ROOT / ".python-version").read_text().strip()
    assert pinned == "3.14"
    assert ".".join(str(part) for part in sys.version_info[:2]) == pinned
    assert (
        scaffold_digest(RUNNER.read_text())
        == json.loads((SLICE / "expected.json").read_text())["runner_ast_sha256"]
    )
