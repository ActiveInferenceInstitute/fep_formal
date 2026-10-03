"""Deterministic adversarial H3 implementation controls; no study seeds are drawn."""

from __future__ import annotations

import copy
import importlib.util
import io
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from fractions import Fraction
from itertools import pairwise
from pathlib import Path
from types import ModuleType, SimpleNamespace

import numpy as np
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def study() -> ModuleType:
    name = "h3_frozen_synthetic_executor"
    spec = importlib.util.spec_from_file_location(
        name, ROOT / "specs/h3-reference-study/run_synthetic.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def exporter(study: ModuleType, monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """Load the slice-local producer beside the already-loaded executor."""
    monkeypatch.setitem(sys.modules, "run_synthetic", study)
    name = "h3_native_export_producer"
    spec = importlib.util.spec_from_file_location(
        name, ROOT / "specs/h3-reference-study/export_native.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, name, module)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def protocol() -> dict:
    return yaml.safe_load(
        (ROOT / "specs/h3-reference-study/preregistration.yaml").read_bytes()
    )


@pytest.fixture
def toy_export(study: ModuleType, protocol: dict) -> dict:
    """Handwritten validation fixture, never represented as a native export."""

    def rat(value: object) -> dict:
        number = Fraction(str(value))
        return {"numerator": number.numerator, "denominator": number.denominator}

    k = protocol["carrier"]["precision"]
    # Exact inverse for this toy validation fixture.
    sigma = [
        [rat(v) for v in row]
        for row in [
            ["7/24", "1/12", "1/12", "1/24"],
            ["1/12", "7/24", "1/24", "1/12"],
            ["1/12", "1/24", "7/24", "1/12"],
            ["1/24", "1/12", "1/12", "7/24"],
        ]
    ]
    return {
        "schema_version": 1,
        "protocol_sha256": study.PROTOCOL_SHA256,
        "axes": list(study.AXES),
        "axis_fin_order": [0, 1, 2, 3],
        "raw_units": protocol["carrier"]["raw_unit_bridge"]["units"],
        "settings": [
            {
                "id": row["id"],
                **{
                    key: rat(row[key])
                    for key in ("center", "observation_noise_variance", "delta")
                },
            }
            for row in protocol["synthetic_acceptance"]["settings"]
        ],
        "precision": [[rat(v) for v in row] for row in k],
        "covariance": sigma,
        "mode_columns": [
            [rat(v) for v in row]
            for row in [[1, 1, 0, 1], [1, 0, 1, -1], [1, 0, -1, -1], [1, -1, 0, 1]]
        ],
        "rates": [rat(v) for v in (2, 4, 4, 6)],
        "mode_squared_norms": [rat(v) for v in (4, 2, 2, 4)],
        "scales": [rat(v) for v in (1, 2, 3, 4)],
        "offsets": [rat(v) for v in (0, 1, -1, 2)],
        "rate": rat(2),
        "diffusion_variance_rate": rat(2),
        "recognition_coefficients": [rat("1/4"), rat("1/4")],
        "recognition_variance": rat("1/4"),
        "recognition_boundary": "precision_block_algebra_only_native_conditioning_owned_by_composition",
        "witnesses": sorted(study.PARAMETER_WITNESSES),
    }


def _toy_native_stdout(study: ModuleType, value: dict) -> str:
    return (
        "H3_PARAMETERS="
        + json.dumps(value)
        + "\n"
        + "\n".join(
            f"'{name}' depends on axioms: [propext, Classical.choice, Quot.sound]"
            for name in sorted(study.PARAMETER_WITNESSES)
        )
        + "\n"
    )


def test_native_export_parser_requires_actual_value_and_equality_evidence(
    study: ModuleType,
    exporter: ModuleType,
    toy_export: dict,
) -> None:
    stdout = _toy_native_stdout(study, toy_export)
    assert exporter.parse_native_output(stdout, "", 0) == toy_export
    malformed = (
        (stdout, "", True),
        (stdout, "warning: rejected\n", 0),
        (stdout.replace("Quot.sound", "sorryAx"), "", 0),
        (stdout + "H3_PARAMETERS={}\n", "", 0),
        (stdout + "'unrequested' does not depend on any axioms\n", "", 0),
        (stdout.replace("Classical.choice", "Invented.resultAx"), "", 0),
        (
            stdout
            + f"'{min(study.PARAMETER_WITNESSES)}' does not depend on any axioms\n",
            "",
            0,
        ),
        ("\n".join(stdout.splitlines()[:-1]), "", 0),
        (
            stdout.replace(
                '"schema_version": 1', '"schema_version": 1, "schema_version": 1'
            ),
            "",
            0,
        ),
    )
    for candidate, stderr, code in malformed:
        with pytest.raises(ValueError):
            exporter.parse_native_output(candidate, stderr, code)


@pytest.mark.skipif(
    os.name != "posix", reason="native exporter descriptor custody is POSIX-only"
)
@pytest.mark.parametrize(
    "failure", [None, "source-race", "timeout", "deadline-final-check", "deadline-seal"]
)
def test_export_attempt_retains_real_child_failure_and_rejects_source_race(
    study: ModuleType,
    exporter: ModuleType,
    toy_export: dict,
    protocol: dict,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: str | None,
) -> None:
    """Explicit fake compiler fixture tests custody, never native mathematics."""
    from fep_lean.verification._subprocess import run_process_group

    root = tmp_path.resolve() / "toy-project"
    producer = root / study.BASE / "export_native.py"
    producer.parent.mkdir(parents=True)
    producer.write_text("# explicitly fake producer fixture\n")
    (root / study.BASE / "run_synthetic.py").write_text("# fake executor fixture\n")
    foundation = root / exporter.FOUNDATION
    foundation.parent.mkdir(parents=True)
    foundation.write_text("namespace FEP.H3ReferenceModel\nend FEP.H3ReferenceModel\n")
    (root / "lean").mkdir()
    (root / "lean/lean-toolchain").write_text("leanprover/lean4:v4.34.1\n")
    (root / "lean/lake-manifest.json").write_text(
        json.dumps(
            {
                "packages": [
                    {
                        "name": "mathlib",
                        "rev": "d13f23b723b8a846827a245b89c10fc7d3f11612",
                    }
                ]
            }
        )
    )
    monkeypatch.setattr(exporter, "__file__", str(producer))
    monkeypatch.setattr(exporter, "frozen_protocol", lambda _inputs: protocol)
    monkeypatch.setattr(exporter, "report_owner_errors", lambda _root: ())
    monkeypatch.setattr(exporter, "source_owner_paths", lambda _root: (foundation,))
    monkeypatch.setattr(exporter, "config_owner_paths", lambda _root: ())
    monkeypatch.setattr(exporter, "find_executable", lambda *_args: "FAKE-LAKE")
    monkeypatch.setattr(
        exporter, "read_toolchain_pin", lambda _root: "leanprover/lean4:v4.34.1"
    )
    revision = "d13f23b723b8a846827a245b89c10fc7d3f11612"
    monkeypatch.setattr(exporter, "resolved_mathlib_revision", lambda _root: revision)
    observed_budgets: list[float] = []
    clock_offset = [0.0]
    monkeypatch.setattr(
        exporter,
        "time",
        SimpleNamespace(monotonic=lambda: time.monotonic() + clock_offset[0]),
    )
    if failure == "deadline-final-check":
        original_inventory = study.AttemptFiles.inventory
        inventory_calls = [0]

        def delayed_inventory(self: object, *, strict: bool = True) -> object:
            inventory_calls[0] += 1
            if inventory_calls[0] == 2:
                clock_offset[0] += 21.0
            return original_inventory(self, strict=strict)

        monkeypatch.setattr(study.AttemptFiles, "inventory", delayed_inventory)
    if failure == "deadline-seal":
        original_receipt = study.AttemptFiles.receipt
        receipt_calls = [0]

        def delayed_receipt(self: object, raw: bytes) -> None:
            original_receipt(self, raw)
            receipt_calls[0] += 1
            if receipt_calls[0] == 1:
                clock_offset[0] += 21.0

        monkeypatch.setattr(study.AttemptFiles, "receipt", delayed_receipt)

    def fake_compiler(
        command: list[str], *, cwd: Path, env: dict, timeout: float
    ) -> subprocess.CompletedProcess[str]:
        observed_budgets.append(timeout)
        if failure == "timeout":
            code = "import time; print('retained child output', flush=True); time.sleep(10)"
        else:
            if command[-1] == "--version":
                stdout = (
                    "Lean (version 4.34.1, arm64-apple-darwin, commit fake, Release)\n"
                )
            elif command[0] == "git":
                stdout = revision + "\n"
            elif command[1] == "build":
                stdout = "FAKE BUILD FIXTURE ONLY\n"
            else:
                stdout = _toy_native_stdout(study, toy_export)
            code = "import sys; sys.stdout.write(" + repr(stdout) + ")"
        result = run_process_group(
            [sys.executable, "-I", "-S", "-c", code], cwd=cwd, env=env, timeout=timeout
        )
        if failure == "source-race" and command[-1].endswith("H3NativeExport.lean"):
            original = foundation.stat()
            foundation.write_text(
                foundation.read_text() + "-- changed during compiler\n"
            )
            os.utime(foundation, ns=(original.st_atime_ns, original.st_mtime_ns))
        return result

    monkeypatch.setattr(exporter, "run_process_group", fake_compiler)
    output = root / study.BASE / "attempt"
    started = time.monotonic()
    if failure is None:
        result = exporter.export_native(root, output, 20.0)
        assert result["accepted"] is True
        exported = json.loads((output / "export.json").read_bytes())
        assert exported["parameters"] == toy_export
        assert set(exported["source_after"]) == {
            *study.STUDY_SOURCE_FILES,
            exporter.FOUNDATION,
        }
        assert len(observed_budgets) == 6
        assert all(right < left for left, right in pairwise(observed_budgets))
        assert set(result["artifact_sha256"]) == {
            *exported["native_artifacts"],
            study.BASE + "attempt/export.json",
        }
        # Inspect attempt gates in isolation. This deliberately fake compiler
        # cannot pass a real native audit or open any scientific generator.
        monkeypatch.setattr(
            study, "source_owner_paths", lambda _root: (_root / exporter.FOUNDATION,)
        )
        monkeypatch.setattr(study, "config_owner_paths", lambda _root: ())
        audit = root / "audit.json"
        audit.write_text("{}\n")

        def audit_boundary(*_args: object) -> None:
            raise RuntimeError("independent native audit still required")

        monkeypatch.setattr(study, "validate_formalism_audit_receipt", audit_boundary)
        export_name = study.BASE + "attempt/export.json"
        with pytest.raises(RuntimeError, match="independent native audit"):
            study.load_export(
                study.Inputs(root),
                export_name,
                "audit.json",
                "absent-proof-review.json",
            )

        original_export = (output / "export.json").read_bytes()
        original_acceptance = (output / "acceptance.json").read_bytes()
        relocated = tmp_path / "fresh extracted project"
        shutil.copytree(root, relocated)
        with pytest.raises(RuntimeError, match="independent native audit"):
            study.load_export(
                study.Inputs(relocated),
                export_name,
                "audit.json",
                "absent-proof-review.json",
            )
        controls = []
        for captured_root in (None, True, "/", "/a/../b", "/a//b", "/changed"):
            changed_root = copy.deepcopy(exported)
            changed_root["captured_project_root"] = captured_root
            controls.append((changed_root, result))
        missing_transcript = copy.deepcopy(exported)
        missing_transcript["native_artifacts"].pop(
            study.BASE + "attempt/native-build.stderr"
        )
        controls.append((missing_transcript, result))
        wrong_parameters = copy.deepcopy(exported)
        wrong_parameters["parameters"]["rates"][0]["numerator"] = 99
        controls.append((wrong_parameters, result))
        absent_source_digest = copy.deepcopy(exported)
        absent_source_digest["source_after"][exporter.FOUNDATION] = None
        absent_source_digest["source_before"][exporter.FOUNDATION] = None
        controls.append((absent_source_digest, result))
        rejected_attempt = copy.deepcopy(result)
        rejected_attempt["accepted"] = False
        controls.append((exported, rejected_attempt))
        for candidate_export, candidate_acceptance in controls:
            export_bytes = (json.dumps(candidate_export) + "\n").encode()
            acceptance = copy.deepcopy(candidate_acceptance)
            # Bind the changed export exactly: rejection must arise from the
            # substantive transcript/schema/acceptance gate, not stale hash.
            acceptance["artifact_sha256"][export_name] = study.hashlib.sha256(
                export_bytes
            ).hexdigest()
            (output / "export.json").write_bytes(export_bytes)
            (output / "acceptance.json").write_text(json.dumps(acceptance) + "\n")
            with pytest.raises(study.StudyRejection):
                study.load_export(
                    study.Inputs(root),
                    export_name,
                    "audit.json",
                    "absent-proof-review.json",
                )
        # Rebind every affected digest so semantic replay supplies the refusal.
        rebound_transcripts = (
            ("H3NativeExport.lean", b'#eval IO.println "forged parameter body"\n'),
            (
                "native-export.stdout",
                (
                    _toy_native_stdout(study, toy_export) + "warning: forged pass\n"
                ).encode(),
            ),
            (
                "native-export.stdout",
                _toy_native_stdout(study, toy_export)
                .replace("Quot.sound", "sorryAx")
                .encode(),
            ),
            (
                "native-export.stdout",
                "\n".join(
                    _toy_native_stdout(study, toy_export).splitlines()[:-1]
                ).encode(),
            ),
            ("compiler-version-final.stdout", b"Lean (version 4.33.1, Release)\n"),
            (
                "mathlib-head-final.stdout",
                b"0000000000000000000000000000000000000000\n",
            ),
        )
        for filename, raw in rebound_transcripts:
            target = output / filename
            previous = target.read_bytes()
            target.write_bytes(raw)
            candidate_export = copy.deepcopy(exported)
            candidate_acceptance = copy.deepcopy(result)
            path = study.BASE + "attempt/" + filename
            digest = study.hashlib.sha256(raw).hexdigest()
            candidate_export["native_artifacts"][path] = digest
            candidate_acceptance["artifact_sha256"][path] = digest
            export_bytes = (json.dumps(candidate_export) + "\n").encode()
            candidate_acceptance["artifact_sha256"][export_name] = study.hashlib.sha256(
                export_bytes
            ).hexdigest()
            (output / "export.json").write_bytes(export_bytes)
            (output / "acceptance.json").write_text(
                json.dumps(candidate_acceptance) + "\n"
            )
            with pytest.raises(study.StudyRejection):
                study.load_export(
                    study.Inputs(root),
                    export_name,
                    "audit.json",
                    "absent-proof-review.json",
                )
            target.write_bytes(previous)
        (output / "export.json").write_bytes(original_export)
        for stage_change in (True, 1, "trust-flag", "renewed-budget"):
            altered = copy.deepcopy(result)
            if stage_change == "trust-flag":
                altered["stages"][3]["command"].append("--trust=1")
            elif stage_change == "renewed-budget":
                altered["stages"][1]["budget_seconds"] = altered["stages"][0][
                    "budget_seconds"
                ]
            else:
                altered["stages"][3]["returncode"] = stage_change
            (output / "acceptance.json").write_text(json.dumps(altered) + "\n")
            with pytest.raises(study.StudyRejection):
                study.load_export(
                    study.Inputs(root),
                    export_name,
                    "audit.json",
                    "absent-proof-review.json",
                )
        (output / "export.json").write_bytes(original_export)
        (output / "acceptance.json").write_bytes(original_acceptance)
        (output / "native-export.stdout").write_text("H3_PARAMETERS={}\n")
        with pytest.raises(study.StudyRejection, match="stale input"):
            study.load_export(
                study.Inputs(root),
                export_name,
                "audit.json",
                "absent-proof-review.json",
            )
    elif failure in ("deadline-final-check", "deadline-seal"):
        result = exporter.export_native(root, output, 20.0)
        record = json.loads((output / "acceptance.json").read_bytes())
        assert result["accepted"] is False
        assert record["accepted"] is False
        assert "deadline" in record["failure"]["reason"]
        assert (output / "export.json").is_file()
        assert record["artifact_sha256"]
    else:
        with pytest.raises((study.StudyRejection, subprocess.TimeoutExpired)):
            exporter.export_native(root, output, 2.0 if failure == "timeout" else 20.0)
        assert not (output / "export.json").exists()
        record = json.loads((output / "acceptance.json").read_bytes())
        assert record["accepted"] is False
        assert record["failure"]["type"] in {"StudyRejection", "TimeoutExpired"}
        if failure == "timeout":
            assert (
                output / "compiler-version.stdout"
            ).read_bytes() == b"retained child output\n"
            assert time.monotonic() - started < 6
        else:
            assert (
                (output / "native-export.stdout")
                .read_text()
                .startswith("H3_PARAMETERS=")
            )


def test_native_export_rejects_dot_dot_before_any_write_or_process(
    exporter: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path.resolve() / "project"
    root.mkdir()
    calls = []

    def forbidden(*args: object, **kwargs: object) -> None:
        calls.append((args, kwargs))
        raise AssertionError("preflight/process started for escaping output")

    monkeypatch.setattr(exporter, "frozen_protocol", forbidden)
    monkeypatch.setattr(exporter, "run_process_group", forbidden)
    with pytest.raises(ValueError, match="noncanonical"):
        exporter.export_native(root, root / ".." / "outside-attempt", 20.0)
    assert calls == []
    assert not (tmp_path / "outside-attempt").exists()


def test_frozen_inputs_and_missing_export_reject_before_any_generator(
    study: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = []

    def forbidden_generator(*args: object, **kwargs: object) -> None:
        calls.append((args, kwargs))
        raise AssertionError("scientific generator opened before native gates")

    monkeypatch.setattr(study.np.random, "Generator", forbidden_generator)
    with pytest.raises(study.StudyRejection, match="missing input"):
        study.run_study(
            ROOT,
            tmp_path.resolve() / "attempt",
            "specs/h3-reference-study/output/missing-export.json",
            "output/formalism-audit.json",
            "specs/h3-reference-study/output/missing-review.json",
        )
    assert calls == []
    assert not (tmp_path / "attempt").exists()


def test_parameter_binding_and_locked_input_negatives(
    study: ModuleType, protocol: dict, toy_export: dict
) -> None:
    p = study.parameters(toy_export, protocol)
    assert np.max(np.abs(p["u"].T @ p["u"] - np.eye(4))) < 1e-12
    controls = study.parameter_negative_controls(toy_export, protocol)
    assert len(controls["rejected"]) == 9
    assert controls["null_point_density_accepted"]
    wrong_mode = copy.deepcopy(toy_export)
    wrong_mode["mode_columns"][0][1]["numerator"] = -1
    with pytest.raises(study.StudyRejection, match="mode"):
        study.parameters(wrong_mode, protocol)
    wrong_setting = copy.deepcopy(toy_export)
    wrong_setting["settings"][1]["delta"]["numerator"] = 3
    with pytest.raises(study.StudyRejection, match="setting parameter"):
        study.parameters(wrong_setting, protocol)


@pytest.mark.parametrize(
    "value",
    [
        True,
        {"numerator": True, "denominator": 1},
        {"numerator": 1, "denominator": 0},
        {"numerator": 1, "denominator": -1},
        {"numerator": 1, "denominator": 1, "extra": 0},
    ],
)
def test_rational_export_rejects_boolean_zero_denominator_and_extra_fields(
    study: ModuleType, value: object
) -> None:
    with pytest.raises(study.StudyRejection):
        study.fraction(value)


def test_centered_asymmetric_transition_uses_declared_matrix_orientation(
    study: ModuleType,
) -> None:
    x = np.asarray(
        [[1 if n & (1 << i) else -1 for i in range(4)] for n in range(16)], dtype=float
    )
    a = np.asarray(
        [[0.2, 0.1, 0, 0], [0, 0.3, 0.1, 0], [0, 0, 0.4, 0.1], [0.1, 0, 0, 0.5]]
    )
    observed = study.estimates(
        x + [2, 3, 4, 5], x @ a.T + [-3, 4, -5, 6], 0.25, {"u": np.eye(4)}
    )
    assert np.allclose(observed["precision"], np.eye(4))
    assert np.allclose(observed["transition"], a)
    assert observed["recognition_residual_variance"] == pytest.approx(1)
    with pytest.raises(study.StudyRejection, match="singular"):
        study.estimates(np.ones((16, 4)), np.ones((16, 4)), 0.25, {"u": np.eye(4)})
    with pytest.raises(study.StudyRejection, match="slope"):
        study.estimates(x, 2 * x, 0.25, {"u": np.eye(4)})


def test_sbc_tie_rank_normalization_and_shape_failures(study: ModuleType) -> None:
    z = np.zeros(2)
    metrics, means = study.sbc_metrics(
        z, z, 0, 0.125, np.zeros((2, 31)), np.asarray([0, 0.999])
    )
    assert metrics["rank_histogram"] == [1] + [0] * 30 + [1]
    assert metrics["normalized_rank_mean"] == 0.5
    assert sum(metrics["rank_frequencies"]) == 1
    assert np.array_equal(means, z)
    with pytest.raises(study.StudyRejection, match="shapes"):
        study.sbc_metrics(z, z, 0, 0.125, np.zeros((2, 30)), np.zeros(2))
    with pytest.raises(study.StudyRejection, match="tie uniforms"):
        study.sbc_metrics(z, z, 0, 0.125, np.zeros((2, 31)), np.ones(2))


def test_source_race_including_restored_mtime_and_symlink_reject(
    study: ModuleType, tmp_path: Path
) -> None:
    source = tmp_path / "source.json"
    source.write_bytes(b"{}")
    inputs = study.Inputs(tmp_path)
    inputs.read("source.json")
    before = source.stat()
    source.write_bytes(b"[]")
    os.utime(source, ns=(before.st_atime_ns, before.st_mtime_ns))
    with pytest.raises(study.StudyRejection, match="changed during read"):
        inputs.stable()
    (tmp_path / "redirect").symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(study.StudyRejection, match="symlink"):
        study.Inputs(tmp_path).read("redirect/source.json")


def test_output_cannot_overwrite_sources_or_follow_symlinks(
    study: ModuleType, tmp_path: Path
) -> None:
    root = tmp_path.resolve()
    with pytest.raises(study.StudyRejection, match="H3 output"):
        study.new_output(root, root / "new-source")
    parent = root / "specs/h3-reference-study/output"
    parent.mkdir(parents=True)
    assert study.new_output(root, parent / "attempt") == parent / "attempt"
    (root / "redirect").symlink_to(parent, target_is_directory=True)
    with pytest.raises(study.StudyRejection, match="symlink"):
        study.new_output(root, root / "redirect/attempt")


def test_exact_fixture_scope_and_uncapped_zero_observation_tail(
    study: ModuleType, protocol: dict, toy_export: dict
) -> None:
    controls = study.exact_controls(protocol, study.parameters(toy_export, protocol))
    assert controls["accepted"]
    row = controls["fixed_latent_consistency"]["A"][0]
    assert {
        name: row[name]
        for name in (
            "n",
            "variance",
            "mean",
            "native_joint_mse",
            "markov_tail_bound_epsilon_half",
        )
    } == {
        "n": 0,
        "variance": "1/2",
        "mean": "0",
        "native_joint_mse": "1/2",
        "markov_tail_bound_epsilon_half": "2",
    }
    assert controls["fixed_latent_consistency"]["B"][0]["mean"] == "3/4"
    assert controls["singular_grid"]["status"].startswith("requires separately")


def test_atime_only_read_changes_do_not_reject(
    study: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source.json"
    source.write_bytes(b"{}")
    original = os.fstat
    calls = []

    def access_only(fd: int) -> SimpleNamespace:
        value = original(fd)
        calls.append(fd)
        fields = {
            name: getattr(value, name)
            for name in (
                "st_dev",
                "st_ino",
                "st_mode",
                "st_size",
                "st_mtime_ns",
                "st_ctime_ns",
            )
        }
        return SimpleNamespace(**fields, st_atime_ns=len(calls))

    monkeypatch.setattr(study.os, "fstat", access_only)
    inputs = study.Inputs(tmp_path)
    assert inputs.read("source.json") == b"{}"
    inputs.stable()
    assert len(calls) == 4


@pytest.mark.parametrize(
    "field, value, message",
    [
        ("schema_version", True, "native export schema"),
        ("returncode", False, "export compiler"),
    ],
)
def test_boolean_native_metadata_is_rejected_before_audit(
    study: ModuleType, tmp_path: Path, field: str, value: bool, message: str
) -> None:
    payload = {
        "schema_version": 1,
        "kind": "h3-native-rational-export",
        "protocol_sha256": study.PROTOCOL_SHA256,
        "returncode": 0,
        "warnings": [],
        "source_before": {},
        "source_after": {},
    }
    payload[field] = value
    (tmp_path / "export.json").write_text(json.dumps(payload))
    with pytest.raises(study.StudyRejection, match=message):
        study.load_export(
            study.Inputs(tmp_path),
            "export.json",
            "missing-audit.json",
            "missing-review.json",
        )


def test_corrupted_sequential_posterior_fails_independent_exact_gates(
    study: ModuleType, protocol: dict, toy_export: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    p = study.parameters(toy_export, protocol)
    original = study.posterior

    def corrupted(*args: object, **kwargs: object) -> tuple:
        mean, variance = original(*args, **kwargs)
        return mean + 0.125, variance * 0.9

    monkeypatch.setattr(study, "posterior", corrupted)
    result = study.exact_controls(protocol, p)
    assert not result["accepted"]
    assert not result["gates"]["fixed_latent_consistency"]
    assert not result["gates"]["wrong_prior_exact_bias"]
    assert not result["gates"]["shifted_correct_mean_and_variance"]


def test_retained_array_manifest_detects_mutation_and_undeclared_outputs(
    study: ModuleType, tmp_path: Path
) -> None:
    reference = study.save_array(tmp_path, "posterior_means", np.asarray([0.0, 1.0]))
    declared = study.array_references(
        {"control": {"posterior_mean_arrays": {"false": reference}}}
    )
    assert declared == study.output_artifacts(tmp_path)
    path = tmp_path / reference["path"]
    path.write_bytes(path.read_bytes() + b"changed")
    assert declared != study.output_artifacts(tmp_path)
    (tmp_path / "unexpected.txt").write_text("partial failure must be retained")
    with pytest.raises(study.StudyRejection, match="unexpected output"):
        study.output_artifacts(tmp_path)
    assert "unexpected.txt" in study.output_artifacts(tmp_path, strict=False)


def test_rejected_attempt_retains_completed_setting_and_nonfollowing_issues(
    study: ModuleType,
    protocol: dict,
    toy_export: dict,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Failure-retention fixture bypasses native gates; no scientific RNG runs."""
    protocol = copy.deepcopy(protocol)
    environment = protocol["synthetic_acceptance"]["execution_environment"]
    environment.update(python=study.platform.python_version(), numpy=np.__version__)
    monkeypatch.setattr(study, "frozen_protocol", lambda *args: protocol)
    monkeypatch.setattr(study, "load_export", lambda *args: toy_export)
    outside = tmp_path / "outside.txt"
    outside.write_text("untouched")
    output = tmp_path.resolve() / "attempt"

    calibration_calls: list[str] = []

    def failed_setting(
        setting: dict, sbc: dict, protocol: dict, p: dict, files: object
    ) -> dict:
        calibration_calls.append(setting["id"])
        if setting["id"] == "A":
            ref = study.save_array(files, "toy_setting_a", np.asarray([0.0]))
            return {
                "setting_id": "A",
                "fixture": "deterministic failure retention only",
                "array": ref,
            }
        (output / "unexpected_directory").mkdir()
        (output / "unexpected_link").symlink_to(outside)
        raise study.StudyRejection("original second-setting failure")

    monkeypatch.setattr(study, "calibrate", failed_setting)
    for runtime in ("python", "numpy"):
        actual = environment[runtime]
        environment[runtime] = "0.0.0"
        with pytest.raises(
            study.StudyRejection, match="frozen execution runtime mismatch"
        ):
            study.run_study(ROOT, output, "unused", "unused", "unused")
        assert not output.exists()
        assert calibration_calls == []
        environment[runtime] = actual
    with pytest.raises(study.StudyRejection, match="original second-setting failure"):
        study.run_study(ROOT, output, "unused", "unused", "unused")
    assert calibration_calls == ["A", "B"]
    receipt = json.loads((output / "acceptance.json").read_bytes())
    assert receipt["accepted"] is False
    assert receipt["failure"]["reason"] == "original second-setting failure"
    assert receipt["calibration"][0]["setting_id"] == "A"
    assert set(receipt["retained_artifact_sha256"]) == {"toy_setting_a.npy"}
    assert {row["path"] for row in receipt["retained_output_issues"]} == {
        "unexpected_directory",
        "unexpected_link",
    }
    assert outside.read_text() == "untouched"


def test_attempt_descriptor_does_not_write_through_redirected_path(
    study: ModuleType, tmp_path: Path
) -> None:
    original = tmp_path.resolve() / "attempt"
    original.mkdir()
    displaced = original.with_name("displaced")
    target = original.with_name("protected")
    target.mkdir()
    files = study.AttemptFiles(original)
    try:
        original.rename(displaced)
        original.symlink_to(target, target_is_directory=True)
        reference = study.save_array(files, "toy", np.asarray([1.0]))
        hashes, issues = files.inventory()
        assert hashes == {reference["path"]: reference["sha256"]}
        assert issues == [{"path": ".", "reason": "attempt directory redirected"}]
        files.receipt(b'{"accepted":false}\n')
        assert (displaced / "acceptance.json").read_bytes() == b'{"accepted":false}\n'
        assert list(target.iterdir()) == []
    finally:
        files.close()


@pytest.mark.skipif(os.name != "posix", reason="POSIX descriptor custody contract")
@pytest.mark.parametrize("owner", ["input", "output"])
def test_regular_file_swapped_to_fifo_cannot_block_read(
    study: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, owner: str
) -> None:
    filename = "source.json" if owner == "input" else "array.npy"
    source = tmp_path / filename
    source.write_bytes(b"{}")
    original_open = os.open
    swapped = []

    def swap_open(path: object, flags: int, *args: object, **kwargs: object) -> int:
        if path == filename and not swapped:
            swapped.append(True)
            source.unlink()
            os.mkfifo(source)
        return original_open(path, flags, *args, **kwargs)

    original_handler = signal.getsignal(signal.SIGALRM)

    def blocked(_signum: int, _frame: object) -> None:
        raise AssertionError("FIFO swap blocked custody before fstat")

    files = study.AttemptFiles(tmp_path.resolve()) if owner == "output" else None
    monkeypatch.setattr(study.os, "open", swap_open)
    signal.signal(signal.SIGALRM, blocked)
    signal.setitimer(signal.ITIMER_REAL, 2)
    try:
        if owner == "input":
            with pytest.raises(study.StudyRejection, match="nonregular"):
                study.Inputs(tmp_path).read(filename)
        else:
            hashes, issues = files.inventory()
            assert hashes == {}
            assert "nonregular" in issues[0]["reason"]
        assert swapped == [True]
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, original_handler)
        if files is not None:
            files.close()


def test_ancestor_swapped_during_creation_cannot_create_in_outside_target(
    study: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path.resolve()
    parent, displaced, outside = (
        root / name for name in ("parent", "displaced", "outside")
    )
    parent.mkdir()
    outside.mkdir()
    original_mkdir = os.mkdir

    def swap_mkdir(path: object, *args: object, **kwargs: object) -> None:
        parent.rename(displaced)
        parent.symlink_to(outside, target_is_directory=True)
        original_mkdir(path, *args, **kwargs)

    monkeypatch.setattr(study.os, "mkdir", swap_mkdir)
    files = study.AttemptFiles(parent / "attempt", create=True)
    try:
        assert list(outside.iterdir()) == []
        assert (displaced / "attempt").is_dir()
        _, issues = files.inventory()
        assert issues == [{"path": ".", "reason": "attempt directory path unavailable"}]
    finally:
        files.close()


def test_project_root_ancestor_swap_cannot_return_outside_bytes(
    study: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path.resolve()
    parent, displaced, outside = (
        root / name for name in ("parent", "displaced", "outside")
    )
    project = parent / "project"
    project.mkdir(parents=True)
    (outside / "project").mkdir(parents=True)
    (project / "input.json").write_bytes(b'{"inside":true}')
    (outside / "project/input.json").write_bytes(b'{"outside":true}')
    inputs = study.Inputs(project)
    original = os.open
    swapped = []

    def swap_before_root_open(
        path: object, flags: int, *args: object, **kwargs: object
    ) -> int:
        if not swapped:
            swapped.append(True)
            parent.rename(displaced)
            parent.symlink_to(outside, target_is_directory=True)
        return original(path, flags, *args, **kwargs)

    monkeypatch.setattr(study.os, "open", swap_before_root_open)
    with pytest.raises(OSError):
        inputs.read("input.json")
    assert inputs.states == {}
    assert (outside / "project/input.json").read_bytes() == b'{"outside":true}'


def _small_deterministic_replay_fixture(
    study: ModuleType,
    protocol: dict,
    toy_export: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[dict, dict, dict[str, bytes]]:
    """Toy analysis buffers only; no seed, study draw or primary outcome is produced."""
    protocol = copy.deepcopy(protocol)
    spec = protocol["synthetic_acceptance"]
    n = 32
    spec["pairs_per_setting"] = n
    spec["simulation_based_calibration"]["replications_per_setting"] = n
    spec["control_evaluation"] = n
    p = study.parameters(toy_export, protocol)
    grid = np.repeat(
        np.asarray(
            [
                [1 if row & (1 << axis) else -1 for axis in range(4)]
                for row in range(16)
            ],
            dtype=np.float64,
        ),
        2,
        axis=0,
    )
    modes = grid / np.sqrt(p["rates"])
    buffers: dict[str, bytes] = {}

    class ToyArraySink:
        def write_new(self, name: str, data: bytes) -> None:
            assert name not in buffers
            buffers[name] = data

    def small_descriptive_jackknife_fixture(
        x0: np.ndarray, xt: np.ndarray, *_args: object
    ) -> dict:
        assert x0.shape == xt.shape == (n, 4)
        return {
            "available": False,
            "failures": [
                {"group": 0, "reason": "small deterministic descriptive fixture"}
            ],
            "boundary": "Failed groups retained; no interval fabricated.",
        }

    monkeypatch.setattr(study, "jackknife", small_descriptive_jackknife_fixture)
    sink = ToyArraySink()
    calibrations, recoveries = [], []
    for setting, sbc in zip(
        spec["settings"], spec["simulation_based_calibration"]["settings"], strict=True
    ):
        center = study.fraction(setting["center"])
        noise = study.fraction(setting["observation_noise_variance"])
        delta = study.fraction(setting["delta"])
        x0 = modes @ p["u"].T + center * p["u"][:, 0]
        xt = (modes * np.exp(-delta * p["rates"])) @ p["u"].T + center * p["u"][:, 0]
        y = xt @ p["u"][:, 0] + np.sqrt(noise) * (np.arange(n) % 3 - 1)
        eta = np.tile(np.linspace(-2.0, 2.0, 31), (n, 1))
        ties = np.arange(n, dtype=np.float64) / n
        calibrations.append(
            study.analyze_calibration(
                setting, sbc, protocol, p, x0, xt, y, eta, ties, sink
            )
        )
        recoveries.append(study.analyze_recovery(setting, protocol, p, x0, xt, y, sink))
    control = study.analyze_control(
        protocol,
        p,
        modes @ p["u"].T,
        grid * 0.1,
        np.linspace(-1.0, 1.0, n),
        np.roll(grid, 1, axis=0) * 0.2,
        sink,
    )
    accepted = (
        all(row["accepted"] for row in calibrations + recoveries)
        and control["accepted"]
    )
    assert (
        accepted is False
    )  # A toy zero-innovation recovery fails the frozen diffusion gate.
    record = study.json_primitives(
        {
            "schema_version": 1,
            "gate": "H3.6S",
            "study_id": protocol["study_id"],
            "protocol_sha256": study.PROTOCOL_SHA256,
            "source_before": {"handwritten_toy_fixture": "0" * 64},
            "source_after": {"handwritten_toy_fixture": "0" * 64},
            "execution_environment": spec["execution_environment"],
            "empirical_gate": "governed_no_go",
            "input_negative_controls": study.parameter_negative_controls(
                toy_export, protocol
            ),
            "exact_controls": study.exact_controls(protocol, p),
            "calibration": calibrations,
            "recovery": recoveries,
            "control": control,
            "accepted": accepted,
            "decision": "accepted" if accepted else "rejected",
            "retained_output_issues": [],
        }
    )
    record["artifact_sha256"] = study.array_references(record)
    record["retained_artifact_sha256"] = dict(record["artifact_sha256"])
    assert len(buffers) == len(record["artifact_sha256"]) == 42
    return protocol, record, buffers


def _forbid_scientific_randomness(
    study: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    def forbidden(*_args: object, **_kwargs: object) -> None:
        pytest.fail("pure replay opened a scientific generator or seed")

    monkeypatch.setattr(study.np.random, "Generator", forbidden)
    monkeypatch.setattr(study.np.random, "PCG64", forbidden)


def test_pure_synthetic_replay_keeps_complete_threshold_failure_failed(
    study: ModuleType, protocol: dict, toy_export: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    protocol, record, buffers = _small_deterministic_replay_fixture(
        study, protocol, toy_export, monkeypatch
    )
    _forbid_scientific_randomness(study, monkeypatch)
    result = study.replay_synthetic_attempt(
        protocol, toy_export, record, buffers.__getitem__
    )
    assert result["accepted"] is False
    assert result["decision"] == "rejected"
    assert result["calibration"] == record["calibration"]
    assert result["recovery"] == record["recovery"]
    assert result["control"] == record["control"]
    for recovery in record["recovery"]:
        state_ref = recovery["arrays"]["states_delta"]["path"]
        raw_ref = recovery["arrays"]["raw_states_delta"]["path"]
        p = study.parameters(toy_export, protocol)
        np.testing.assert_array_equal(
            np.load(io.BytesIO(buffers[raw_ref]), allow_pickle=False),
            p["offsets"]
            + p["scales"] * np.load(io.BytesIO(buffers[state_ref]), allow_pickle=False),
        )
    for calibration in record["calibration"]:
        assert calibration[
            "wrong_noise_nominal_gates"
        ] == study.calibration_nominal_gates(
            calibration["wrong_noise"],
            protocol["synthetic_acceptance"]["simulation_based_calibration"][
                "conjunctive_thresholds_each_setting"
            ],
        )
        assert calibration["wrong_noise_nominal_accepted"] == all(
            calibration["wrong_noise_nominal_gates"].values()
        )
    assert set(record["calibration"][0]["arrays"]) == {
        "latent",
        "observations",
        "posterior_means",
        "wrong_noise_means",
        "states0",
        "states_delta",
        "posterior_standard_normals",
        "tie_uniforms",
    }


@pytest.mark.parametrize(
    "mutation",
    [
        "partial",
        "unknown_gate",
        "missing_gate",
        "trimmed_metrics",
        "missing_control",
        "trimmed_exact",
        "missing_negative_control",
        "unknown_metric",
        "boolean_measurement",
        "wrong_decision",
        "trimmed_histogram",
        "missing_array",
    ],
)
def test_pure_synthetic_replay_rejects_incomplete_or_altered_results(
    study: ModuleType,
    protocol: dict,
    toy_export: dict,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    protocol, record, buffers = _small_deterministic_replay_fixture(
        study, protocol, toy_export, monkeypatch
    )
    _forbid_scientific_randomness(study, monkeypatch)
    if mutation == "partial":
        record.pop("recovery")
    elif mutation == "unknown_gate":
        record["calibration"][0]["gates"]["arbitrary_success"] = True
    elif mutation == "missing_gate":
        record["calibration"][0]["gates"].pop("rank_frequency")
    elif mutation == "trimmed_metrics":
        record["recovery"][0]["metrics"].pop("precision_max_entry_absolute_error")
    elif mutation == "missing_control":
        record.pop("control")
    elif mutation == "trimmed_exact":
        record["exact_controls"].pop("calibration_fixtures")
    elif mutation == "missing_negative_control":
        record["input_negative_controls"]["rejected"].pop("axis_labels")
    elif mutation == "unknown_metric":
        record["recovery"][0]["metrics"]["arbitrary_measurement"] = 0.0
    elif mutation == "boolean_measurement":
        record["recovery"][0]["metrics"]["precision_max_entry_absolute_error"] = False
    elif mutation == "wrong_decision":
        record["accepted"], record["decision"] = True, "accepted"
    elif mutation == "trimmed_histogram":
        record["calibration"][0]["nominal"]["rank_histogram"].pop()
    else:
        record["calibration"][0]["arrays"].pop("tie_uniforms")
    with pytest.raises(study.StudyRejection):
        study.replay_synthetic_attempt(
            protocol, toy_export, record, buffers.__getitem__
        )


@pytest.mark.parametrize(
    "mutation",
    [
        "shape",
        "dtype",
        "derived",
        "trailing_bytes",
        "extra_array",
        "fortran",
        "huge_header",
    ],
)
def test_pure_synthetic_replay_rejects_rehashed_array_changes(
    study: ModuleType,
    protocol: dict,
    toy_export: dict,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    protocol, record, buffers = _small_deterministic_replay_fixture(
        study, protocol, toy_export, monkeypatch
    )
    _forbid_scientific_randomness(study, monkeypatch)
    name = "sbc_A_states0.npy"
    if mutation == "shape":
        values = np.zeros((32, 3), dtype="<f8")
    elif mutation == "dtype":
        values = np.zeros((32, 4), dtype="<f4")
    elif mutation == "derived":
        name = "sbc_A_posterior_means.npy"
        values = np.load(io.BytesIO(buffers[name]), allow_pickle=False) + 1.0
    elif mutation == "extra_array":
        name = "unregistered_extra.npy"
        values = np.zeros(1, dtype="<f8")
    elif mutation == "fortran":
        values = np.asfortranarray(np.zeros((32, 4), dtype="<f8"))
    elif mutation == "huge_header":
        encoded = io.BytesIO()
        np.lib.format.write_array_header_1_0(
            encoded, {"descr": "<f8", "fortran_order": False, "shape": (10**9, 4)}
        )
        buffers[name] = encoded.getvalue()
        values = None

        def forbidden_load(*_args: object, **_kwargs: object) -> None:
            pytest.fail("invalid declared shape reached NumPy allocation")

        monkeypatch.setattr(study.np, "load", forbidden_load)
    else:
        values = None
    if values is not None:
        encoded = io.BytesIO()
        np.save(encoded, values, allow_pickle=False)
        buffers[name] = encoded.getvalue()
    elif mutation != "huge_header":
        buffers[name] += b"trailing bytes"
    digest = study.hashlib.sha256(buffers[name]).hexdigest()
    for roster in ("artifact_sha256", "retained_artifact_sha256"):
        record[roster][name] = digest

    def update_reference(value: object) -> None:
        if type(value) is dict:
            if value.get("path") == name:
                value["sha256"] = digest
            for child in value.values():
                update_reference(child)
        elif type(value) is list:
            for child in value:
                update_reference(child)

    update_reference(record)
    if mutation == "extra_array":
        record["control"]["shared_arrays"]["unregistered_extra"] = {
            "path": name,
            "sha256": digest,
        }
    with pytest.raises(study.StudyRejection):
        study.replay_synthetic_attempt(
            protocol, toy_export, record, buffers.__getitem__
        )


def test_real_jackknife_rejects_small_unfrozen_count_before_estimation(
    study: ModuleType, protocol: dict, toy_export: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    p = study.parameters(toy_export, protocol)
    _forbid_scientific_randomness(study, monkeypatch)
    with pytest.raises(study.StudyRejection, match="frozen jackknife count mismatch"):
        study.jackknife(np.zeros((16, 4)), np.zeros((16, 4)), 0.25, p, {})


def test_pure_replay_rejects_abbreviated_arbitrary_complete_fixture(
    study: ModuleType, protocol: dict, toy_export: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    _forbid_scientific_randomness(study, monkeypatch)
    encoded = io.BytesIO()
    np.save(encoded, np.zeros(1, dtype="<f8"), allow_pickle=False)
    data = encoded.getvalue()
    digest = study.hashlib.sha256(data).hexdigest()
    spec = protocol["synthetic_acceptance"]
    record = {
        "schema_version": 1,
        "gate": "H3.6S",
        "study_id": protocol["study_id"],
        "protocol_sha256": study.PROTOCOL_SHA256,
        "source_before": {"toy": "0" * 64},
        "source_after": {"toy": "0" * 64},
        "execution_environment": spec["execution_environment"],
        "empirical_gate": "governed_no_go",
        "calibration": [
            {
                "setting_id": setting["id"],
                "seed": sbc["seed"],
                "accepted": True,
                "gates": {"arbitrary": True},
            }
            for setting, sbc in zip(
                spec["settings"],
                spec["simulation_based_calibration"]["settings"],
                strict=True,
            )
        ],
        "recovery": [
            {"setting": setting, "accepted": True, "gates": {"arbitrary": True}}
            for setting in spec["settings"]
        ],
        "exact_controls": {"accepted": True},
        "control": {
            "accepted": True,
            "seed": spec["controls_seed"],
            "results": {
                setting["id"]: {"gates": {"arbitrary": True}}
                for setting in spec["settings"]
            },
            "array": {"path": "arbitrary.npy", "sha256": digest},
        },
        "artifact_sha256": {"arbitrary.npy": digest},
        "retained_artifact_sha256": {"arbitrary.npy": digest},
        "retained_output_issues": [],
        "accepted": True,
        "decision": "accepted",
    }
    with pytest.raises(
        study.StudyRejection, match="missing retained array: sbc_A_states0.npy"
    ):
        study.replay_synthetic_attempt(protocol, toy_export, record, lambda _name: data)


def test_generator_wrappers_keep_exact_draw_order_without_real_generators(
    study: ModuleType, protocol: dict, toy_export: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    p = study.parameters(toy_export, protocol)
    calls: list[tuple] = []

    class FixedGenerator:
        def __init__(self, seed: int):
            calls.append(("seed", seed))

        def standard_normal(
            self, shape: int | tuple[int, ...], *, dtype: object
        ) -> np.ndarray:
            calls.append(("normal", shape, dtype))
            fixture_shape = (16, *shape[1:]) if type(shape) is tuple else (16,)
            return np.zeros(fixture_shape, dtype=np.float64)

        def random(self, n: int) -> np.ndarray:
            calls.append(("ties", n))
            return np.zeros(16, dtype=np.float64)

    monkeypatch.setattr(study.np.random, "PCG64", lambda seed: seed)
    monkeypatch.setattr(study.np.random, "Generator", FixedGenerator)
    for name in ("analyze_recovery", "analyze_calibration", "analyze_control"):
        monkeypatch.setattr(study, name, lambda *_args: {"fixture": "draw-order-only"})
    setting = protocol["synthetic_acceptance"]["settings"][0]
    sbc = protocol["synthetic_acceptance"]["simulation_based_calibration"]["settings"][
        0
    ]
    study.recover(setting, protocol, p, object())
    assert calls == [
        ("seed", setting["seed"]),
        ("normal", (200000, 4), np.float64),
        ("normal", (200000, 4), np.float64),
        ("normal", 200000, np.float64),
    ]
    calls.clear()
    study.calibrate(setting, sbc, protocol, p, object())
    assert calls == [
        ("seed", sbc["seed"]),
        ("normal", (20000, 4), np.float64),
        ("normal", (20000, 4), np.float64),
        ("normal", 20000, np.float64),
        ("normal", (20000, 31), np.float64),
        ("ties", 20000),
    ]
    calls.clear()
    study.control_simulation(protocol, p, object())
    assert calls == [
        ("seed", protocol["synthetic_acceptance"]["controls_seed"]),
        ("normal", (200000, 4), np.float64),
        ("normal", (200000, 4), np.float64),
        ("normal", 200000, np.float64),
        ("normal", (200000, 4), np.float64),
    ]
