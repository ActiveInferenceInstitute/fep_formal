"""Prospective H3 archive/custody controls; no scientific seeds are drawn."""

from __future__ import annotations

import gzip
import importlib.util
import io
import json
import os
import subprocess
import sys
import tarfile
import tempfile
from copy import deepcopy
from pathlib import Path
from types import ModuleType

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def bundle() -> ModuleType:
    for name, filename in (
        ("run_synthetic", "run_synthetic.py"),
        ("h3_prospective_bundle", "bundle_study.py"),
    ):
        spec = importlib.util.spec_from_file_location(
            name, ROOT / "specs/h3-reference-study" / filename
        )
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return module


def toy_archive(bundle: ModuleType) -> tuple[bytes, dict, dict]:
    """This is a wrapper encoding fixture, not a valid package/science archive."""
    payload = {
        bundle.PACKAGE: b"explicitly invalid package fixture",
        "study/specs/h3-reference-study/toy.json": b"{}\n",
    }
    metadata = {
        "descriptor": {
            "path": "specs/h3-reference-study/toy.json",
            "sha256": bundle.digest(b"{}\n"),
        },
        "package_project_path": "output/toy.tar.gz",
        "protocol_sha256": bundle.PROTOCOL_SHA256,
        "source_sha256": {},
    }
    return bundle.archive_bytes(payload, metadata), payload, metadata


def rewrite_archive(bundle: ModuleType, raw: bytes, change: object) -> bytes:
    output = io.BytesIO()
    with (
        gzip.GzipFile(
            fileobj=output, mode="wb", filename="", mtime=0, compresslevel=9
        ) as zipped,
        tarfile.open(fileobj=zipped, mode="w|", format=tarfile.USTAR_FORMAT) as target,
        tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as source,
    ):
        for member in source:
            stream = source.extractfile(member)
            assert stream is not None
            data = stream.read()
            member, data = change(member, data)
            member.size = len(data)
            target.addfile(member, io.BytesIO(data))
    return output.getvalue()


def test_archive_encoding_is_byte_identical_without_scientific_acceptance(
    bundle: ModuleType,
) -> None:
    raw, payload, metadata = toy_archive(bundle)
    assert raw == bundle.archive_bytes(dict(reversed(tuple(payload.items()))), metadata)
    observed, manifest = bundle.read_study_archive(raw)
    assert observed == payload
    assert manifest["source_date_epoch"] == 0
    with pytest.raises(bundle.StudyRejection, match="contained package rejected"):
        bundle.validate(raw)


@pytest.mark.parametrize(
    "name", ["", "/absolute", "a/../b", "a/./b", "a//b", "a/", "a\\b", "a\x00b"]
)
def test_reference_names_reject_traversal_and_noncanonical_paths(
    bundle: ModuleType, name: str
) -> None:
    with pytest.raises(bundle.StudyRejection):
        bundle.safe_name(name)


@pytest.mark.parametrize("sha", [None, True, 1, "a" * 63, "A" * 64, "z" * 64])
def test_reference_digests_are_typed(bundle: ModuleType, sha: object) -> None:
    with pytest.raises(bundle.StudyRejection):
        bundle.reference({"path": "safe", "sha256": sha})


@pytest.mark.parametrize(
    "failure",
    [
        "hash",
        "bool-size",
        "uid",
        "mode",
        "link",
        "traversal",
        "undeclared",
        "duplicate",
        "extra-manifest",
    ],
)
def test_archive_metadata_and_coherently_rebound_member_controls(
    bundle: ModuleType, failure: str
) -> None:
    raw, _, _ = toy_archive(bundle)

    def change(member: tarfile.TarInfo, data: bytes) -> tuple[tarfile.TarInfo, bytes]:
        if member.name == bundle.MANIFEST and failure in (
            "hash",
            "bool-size",
            "extra-manifest",
        ):
            manifest = json.loads(data)
            if failure == "extra-manifest":
                manifest["undeclared"] = "not a reviewed closure field"
            elif failure == "hash":
                manifest["members"][0]["sha256"] = "0" * 64
            else:
                manifest["members"][0]["size"] = True
            data = bundle.canonical(manifest)
        if member.name == bundle.PACKAGE:
            if failure == "uid":
                member.uid = 1
            elif failure == "mode":
                member.mode = 0o755
            elif failure == "link":
                member.type = tarfile.SYMTYPE
                member.linkname = "/outside"
            elif failure == "traversal":
                member.name = "../outside"
            elif failure == "undeclared":
                member.name = "private/provider.toml"
            elif failure == "duplicate":
                member.name = bundle.MANIFEST
        return member, data

    with pytest.raises(bundle.StudyRejection):
        bundle.read_study_archive(rewrite_archive(bundle, raw, change))


@pytest.mark.parametrize("kind", ["symlink", "fifo", "oversize"])
def test_descriptor_archive_reads_never_follow_or_block(
    bundle: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    original = tmp_path / "original"
    original.write_bytes(b"outside bytes remain untouched")
    path = tmp_path / "archive"
    if kind == "symlink":
        path.symlink_to(original)
    elif kind == "fifo":
        os.mkfifo(path)
    else:
        path.write_bytes(b"12345")
        monkeypatch.setattr(bundle, "MAX_ARCHIVE_BYTES", 4)
    with pytest.raises((bundle.StudyRejection, ValueError)):
        bundle.archive_buffer(path)
    assert original.read_bytes() == b"outside bytes remain untouched"


def test_failed_assembly_retains_frozen_source_rejection_before_any_draw(
    bundle: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        pytest.fail(
            "no scientific generator or child may start for an absent descriptor"
        )

    monkeypatch.setattr(np.random, "Generator", forbidden)
    monkeypatch.setattr(bundle, "run_process_group", forbidden)
    output = tmp_path / "failed-assembly"
    with pytest.raises(
        bundle.StudyRejection,
        match=r"^stale input: src/fep_lean/formal/fin4_gaussian_semigroup\.lean$",
    ):
        bundle.assemble(
            ROOT, "specs/h3-reference-study/output/absent-descriptor.json", output
        )
    record = json.loads((output / "acceptance.json").read_bytes())
    assert record["accepted"] is False
    assert record["failure"]["type"] == "StudyRejection"
    assert not (output / "study.tar.gz").exists()


def test_claim_boundary_preserves_failed_primary_and_governed_no_go(
    bundle: ModuleType,
) -> None:
    protocol = {
        "claim_matrix": {
            "proved": "exact statements only",
            "numerical": "frozen measurements only",
            "empirical": "unavailable",
            "causal": "imposed synthetic interventions only",
            "physical_thermodynamics": "unidentifiable_without_constitutive_measurements",
            "excluded": "universal FEP",
        }
    }
    claims = bundle.expected_claims(
        protocol,
        {"native_witnesses": {"toy": "toy"}},
        {"accepted": False, "decision": "rejected"},
    )
    assert claims["numerical"]["accepted"] is False
    assert claims["empirical"] == "unavailable"
    assert (
        claims["physical_thermodynamics"]
        == "unidentifiable_without_constitutive_measurements"
    )


def test_reproduction_refuses_invalid_package_before_install_or_rng(
    bundle: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    raw, _, _ = toy_archive(bundle)

    def forbidden(*args: object, **kwargs: object) -> None:
        pytest.fail("invalid archive must not invoke a child or scientific generator")

    monkeypatch.setattr(bundle, "run_process_group", forbidden)
    monkeypatch.setattr(np.random, "Generator", forbidden)
    output = tmp_path / "not-created"
    with pytest.raises(bundle.StudyRejection, match="contained package rejected"):
        bundle.reproduce(raw, output, reviewer_id="explicit fixture reviewer")
    assert not output.exists()


@pytest.mark.parametrize(
    "failure",
    [
        None,
        "promoted-primary",
        "changed-array",
        "undeclared-array",
        "different-seed",
        "duplicate-setting",
        "untyped-gate",
        "execution-failure",
    ],
)
def test_abbreviated_attempt_cannot_claim_complete_scientific_results(
    bundle: ModuleType, tmp_path: Path, failure: str | None
) -> None:
    """Minimal receipt fixture tests validation; it is never a native result."""
    source = tmp_path / "owned.txt"
    source.write_bytes(b"owned fixture source")
    expected = {"owned.txt": bundle.digest(source.read_bytes())}
    protocol = {
        "study_id": "explicit toy receipt fixture",
        "synthetic_acceptance": {
            "execution_environment": {"fixture": True},
            "settings": [{"id": "A", "seed": 101}, {"id": "B", "seed": 102}],
            "simulation_based_calibration": {
                "settings": [{"seed": 103}, {"seed": 104}]
            },
            "controls_seed": 105,
        },
    }
    array = io.BytesIO()
    np.save(array, np.asarray([1.0, 2.0], dtype="<f8"), allow_pickle=False)
    array_bytes = array.getvalue()
    sha = bundle.digest(array_bytes)
    (tmp_path / "fixture.npy").write_bytes(array_bytes)
    spec = protocol["synthetic_acceptance"]
    record = {
        "schema_version": 1,
        "gate": "H3.6S",
        "protocol_sha256": bundle.PROTOCOL_SHA256,
        "study_id": protocol["study_id"],
        "source_before": expected,
        "source_after": expected,
        "execution_environment": spec["execution_environment"],
        "empirical_gate": "governed_no_go",
        "accepted": False,
        "decision": "rejected",
        "exact_controls": {"accepted": True},
        "calibration": [
            {
                "setting_id": setting["id"],
                "seed": sbc["seed"],
                "accepted": True,
                "gates": {"toy": True},
            }
            for setting, sbc in zip(
                spec["settings"],
                spec["simulation_based_calibration"]["settings"],
                strict=True,
            )
        ],
        "recovery": [
            {"setting": setting, "accepted": False, "gates": {"toy": False}}
            for setting in spec["settings"]
        ],
        "control": {
            "accepted": True,
            "seed": 105,
            "results": {"A": {"gates": {"toy": True}}, "B": {"gates": {"toy": True}}},
        },
        "arrays": [{"path": "fixture.npy", "sha256": sha}],
        "artifact_sha256": {"fixture.npy": sha},
        "retained_artifact_sha256": {"fixture.npy": sha},
        "retained_output_issues": [],
    }
    record = deepcopy(record)
    if failure == "promoted-primary":
        record["accepted"], record["decision"] = True, "accepted"
    elif failure == "changed-array":
        (tmp_path / "fixture.npy").write_bytes(array_bytes + b"changed")
    elif failure == "undeclared-array":
        record["retained_artifact_sha256"]["undeclared.npy"] = "0" * 64
    elif failure == "different-seed":
        record["calibration"][0]["seed"] = 999
    elif failure == "duplicate-setting":
        record["recovery"][1]["setting"] = record["recovery"][0]["setting"]
    elif failure == "untyped-gate":
        record["control"]["results"]["A"]["gates"]["toy"] = 1
    elif failure == "execution-failure":
        record["failure"] = {"type": "ValueError", "reason": "retained failure"}
    (tmp_path / "acceptance.json").write_bytes(bundle.canonical(record))
    with pytest.raises(bundle.StudyRejection):
        bundle.synthetic_attempt(
            bundle.Inputs(tmp_path), "acceptance.json", expected, protocol, {}
        )


def test_reproduction_timeout_retains_real_child_raw_streams_and_failed_record(
    bundle: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Explicit child fixture tests retention, not installation or scientific execution."""
    from fep_lean.verification._subprocess import run_process_group

    raw, _, _ = toy_archive(bundle)
    monkeypatch.setattr(
        bundle,
        "validate",
        lambda _raw: {"valid": True, "claim_ready": False, "fixture_only": True},
    )

    def fixture_hydration(payload: dict, metadata: dict, directory: Path) -> None:
        directory.mkdir()
        descriptor = directory / metadata["descriptor"]["path"]
        descriptor.parent.mkdir(parents=True)
        descriptor.write_bytes(
            bundle.canonical({"synthetic_attempt": {"path": "fixture-attempt.json"}})
        )
        (directory / "fixture-attempt.json").write_bytes(
            bundle.canonical({"accepted": False})
        )

    monkeypatch.setattr(bundle, "hydrate", fixture_hydration)
    calls = []

    def actual_timeout(
        command: list[str], *, cwd: Path, env: dict, timeout: float
    ) -> object:
        calls.append(command)
        assert command[1] == "sync" and "--locked" in command
        code = "import sys,time; sys.stdout.buffer.write(b'fixture \\xff\\r\\n'); sys.stdout.flush(); time.sleep(10)"
        return run_process_group(
            [sys.executable, "-I", "-S", "-c", code], cwd=cwd, env=env, timeout=timeout
        )

    monkeypatch.setattr(bundle, "run_process_group", actual_timeout)

    def forbidden_generator(*args: object, **kwargs: object) -> None:
        pytest.fail("the failed child cannot open a scientific stream")

    monkeypatch.setattr(np.random, "Generator", forbidden_generator)
    output = tmp_path / "failed-reproduction"
    with pytest.raises(subprocess.TimeoutExpired):
        bundle.reproduce(
            raw, output, reviewer_id="explicit timeout fixture", timeout=2.0
        )
    assert len(calls) == 1
    assert (output / "locked-install.stdout").read_bytes() == b"fixture \xff\r\n"
    record = json.loads((output / "acceptance.json").read_bytes())
    assert record["accepted"] is False
    assert record["failure"]["type"] == "TimeoutExpired"
    assert record["stages"][0]["timed_out"] is True
    assert record["retained_stream_sha256"]["locked-install.stdout"] == bundle.digest(
        b"fixture \xff\r\n"
    )


def test_frozen_h2_packet_is_retained_as_history_without_rebinding_current_source(
    bundle: ModuleType,
) -> None:
    inputs = bundle.Inputs(ROOT)
    bundle.frozen_history(inputs)
    freeze = inputs.json(bundle.BASE + "freeze.json")
    assert (
        inputs.states[bundle.H2_TERMINAL].sha256
        == freeze["h2_terminal_at_freeze_sha256"]
    )
    assert any(name.endswith("junit.xml") for name in inputs.states)
    assert any(name.endswith("collection.json") for name in inputs.states)
    assert any(
        "review" in name and name.startswith(bundle.H2_PACKET) for name in inputs.states
    )
    assert not any(name.startswith("src/") for name in inputs.states)


@pytest.mark.parametrize(
    "failure", ["raw-trailer", "gzip-member", "empty-gzip-member", "crc", "tar-trailer"]
)
def test_complete_archive_envelope_is_validated(
    bundle: ModuleType, failure: str
) -> None:
    raw, _, _ = toy_archive(bundle)
    if failure == "raw-trailer":
        raw += b"undeclared trailer"
    elif failure in ("gzip-member", "empty-gzip-member"):
        raw += gzip.compress(
            b"undeclared second payload" if failure == "gzip-member" else b"", mtime=0
        )
    elif failure == "crc":
        corrupted = bytearray(raw)
        corrupted[-8] ^= 1
        raw = bytes(corrupted)
    else:
        expanded = bytearray(gzip.decompress(raw))
        expanded[-1] = 1
        raw = gzip.compress(bytes(expanded), mtime=0)
    with pytest.raises(bundle.StudyRejection):
        bundle.read_study_archive(raw)


def test_hydration_uses_canonical_private_system_temp_path(
    bundle: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        bundle, "retained_package", lambda *args, **kwargs: {"fixture.txt": b"fixture"}
    )
    with tempfile.TemporaryDirectory(prefix="h3-system-temp-control-") as temporary:
        directory = Path(temporary).resolve() / "project"
        bundle.hydrate(
            {bundle.PACKAGE: b"invalid fixture package"},
            {"package_project_path": "output/toy.tar.gz"},
            directory,
        )
        assert (directory / "fixture.txt").read_bytes() == b"fixture"


@pytest.mark.parametrize("trimmed", [False, True])
def test_bundle_replays_complete_toy_analysis_without_promoting_failed_primary(
    bundle: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    trimmed: bool,
) -> None:
    from tests import test_h3_reference_study as support

    study = sys.modules["run_synthetic"]
    protocol = support.protocol.__wrapped__()
    native_fixture = support.toy_export.__wrapped__(study, protocol)
    protocol, record, arrays = support._small_deterministic_replay_fixture(
        study, protocol, native_fixture, monkeypatch
    )
    support._forbid_scientific_randomness(study, monkeypatch)
    source = tmp_path / "source.txt"
    source.write_bytes(b"explicit toy integration source")
    expected = {"source.txt": bundle.digest(source.read_bytes())}
    record["source_before"] = record["source_after"] = expected
    for name, data in arrays.items():
        (tmp_path / name).write_bytes(data)
    if trimmed:
        del record["calibration"][0]["wrong_noise_nominal_gates"]["coverage"]
    (tmp_path / "acceptance.json").write_bytes(bundle.canonical(record))
    if trimmed:
        with pytest.raises(bundle.StudyRejection, match="synthetic replay mismatch"):
            bundle.synthetic_attempt(
                bundle.Inputs(tmp_path),
                "acceptance.json",
                expected,
                protocol,
                native_fixture,
            )
    else:
        observed = bundle.synthetic_attempt(
            bundle.Inputs(tmp_path),
            "acceptance.json",
            expected,
            protocol,
            native_fixture,
        )
        assert observed["accepted"] is False
        assert observed["decision"] == "rejected"
        assert len(observed["artifact_sha256"]) == 42


@pytest.mark.parametrize(
    "failure", [None, "archive", "receipt", "source", "package", "ancestor"]
)
def test_assembly_checks_source_archive_and_receipt_after_final_seal(
    bundle: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: str | None,
) -> None:
    """Assembly custody fixture has no package/native/science acceptance."""
    root = tmp_path / "project"
    root.mkdir()
    source, package = root / "source.txt", root / "output/fixture.tar.gz"
    source.write_bytes(b"fixture source")
    package.parent.mkdir()
    package.write_bytes(b"fixture package")
    sources = {"source.txt": bundle.digest(source.read_bytes())}
    payload = {bundle.PACKAGE: package.read_bytes()}
    metadata = {
        "descriptor": {"path": bundle.BASE + "output/fixture.json", "sha256": "0" * 64},
        "package_project_path": "output/fixture.tar.gz",
        "protocol_sha256": bundle.PROTOCOL_SHA256,
        "source_sha256": sources,
    }
    monkeypatch.setattr(bundle, "collect", lambda *_args: (payload, metadata, sources))
    monkeypatch.setattr(
        bundle,
        "validate",
        lambda *_args, **_kwargs: {"valid": True, "fixture_only": True},
    )
    parent = tmp_path / "attempt-parent"
    parent.mkdir()
    output = parent / "assembly"
    moved = tmp_path / "original-parent"
    outside = tmp_path / "outside"
    outside.mkdir()
    original_receipt = bundle.AttemptFiles.receipt
    changed = False

    def mutate_during_seal(files: object, data: bytes) -> None:
        nonlocal changed
        original_receipt(files, data)
        if changed or not json.loads(data)["accepted"]:
            return
        changed = True
        if failure == "archive":
            (output / "study.tar.gz").write_bytes(b"altered archive")
        elif failure == "receipt":
            (output / "acceptance.json").write_bytes(
                b'{"accepted":true,"forged":true}\n'
            )
        elif failure in {"source", "package"}:
            path = source if failure == "source" else package
            before = path.stat()
            path.write_bytes(path.read_bytes() + b"changed")
            os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
        elif failure == "ancestor":
            parent.rename(moved)
            parent.symlink_to(outside, target_is_directory=True)

    monkeypatch.setattr(bundle.AttemptFiles, "receipt", mutate_during_seal)
    result = bundle.assemble(root, metadata["descriptor"]["path"], output)
    assert result["accepted"] is (failure is None)
    retained = moved / "assembly" if failure == "ancestor" else output
    assert json.loads((retained / "acceptance.json").read_bytes())["accepted"] is (
        failure is None
    )
    assert list(outside.iterdir()) == []


@pytest.mark.parametrize(
    "failure",
    [
        None,
        "extracted-source",
        "installed-source",
        "installed-import-transient",
        "stream-seal",
        "ancestor-seal",
        "synthetic-seal",
        "receipt-seal",
    ],
)
def test_reproduction_parent_snapshots_and_final_seal_fail_closed(
    bundle: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: str | None,
) -> None:
    """Real stdlib children test custody; installation/native/science are explicit fixtures."""
    from fep_lean.verification._subprocess import run_process_group

    array = io.BytesIO()
    np.save(array, np.asarray([2.0], dtype="<f8"), allow_pickle=False)
    array_raw = array.getvalue()
    original = {
        "accepted": False,
        "execution_environment": {"python": "3.14.4", "numpy": "2.5.1"},
        "artifact_sha256": {"fixture.npy": bundle.digest(array_raw)},
    }
    producer = b"""import argparse,pathlib,sys
p=argparse.ArgumentParser()
p.add_argument('--output',type=pathlib.Path,required=True)
p.add_argument('--check-inputs',action='store_true')
a,_=p.parse_known_args()
if a.check_inputs:
    print('explicit stdlib input fixture')
    sys.exit(0)
a.output.mkdir()
for name in ('acceptance.json','fixture.npy'):
    (a.output/name).write_bytes((pathlib.Path(__file__).parent/'output/reference'/name).read_bytes())
sys.exit(1)
"""
    fixture_sources = {
        bundle.BASE + "run_synthetic.py": producer,
        "src/fep_lean/__init__.py": b"# explicit installed source fixture\n",
    }
    descriptor_path = bundle.BASE + "output/descriptor.json"
    descriptor = {
        "export": {"path": "fixture-export.json"},
        "audit": {"path": "fixture-audit.json"},
        "proof_review": {"path": "fixture-review.json"},
        "synthetic_attempt": {"path": bundle.BASE + "output/reference/acceptance.json"},
    }
    payload = {
        bundle.PACKAGE: b"invalid package; replaced only by an explicit validation fixture",
        **{"study/" + name: value for name, value in fixture_sources.items()},
        "study/" + descriptor_path: bundle.canonical(descriptor),
    }
    metadata = {
        "descriptor": {
            "path": descriptor_path,
            "sha256": bundle.digest(bundle.canonical(descriptor)),
        },
        "package_project_path": "output/fixture.tar.gz",
        "protocol_sha256": bundle.PROTOCOL_SHA256,
        "source_sha256": {
            name: bundle.digest(value) for name, value in fixture_sources.items()
        },
    }
    raw = bundle.archive_bytes(payload, metadata)
    monkeypatch.setattr(
        bundle,
        "validate",
        lambda _raw: {"valid": True, "claim_ready": False, "fixture_only": True},
    )

    def fixture_hydration(_payload: dict, _metadata: dict, directory: Path) -> None:
        directory.mkdir()
        for name, value in fixture_sources.items():
            path = directory / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(value)
        path = directory / descriptor_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(bundle.canonical(descriptor))
        reference = directory / bundle.BASE / "output/reference"
        reference.mkdir()
        (reference / "acceptance.json").write_bytes(bundle.canonical(original))
        (reference / "fixture.npy").write_bytes(array_raw)

    monkeypatch.setattr(bundle, "hydrate", fixture_hydration)
    calls: list[str] = []
    installed_file: Path | None = None

    def change_with_restored_mtime(path: Path) -> None:
        before = path.stat()
        path.write_bytes(path.read_bytes() + b"# changed\n")
        os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))

    def fixture_child(
        command: list[str], *, cwd: Path, env: dict, timeout: float
    ) -> object:
        nonlocal installed_file
        if command[1] == "sync":
            name = "locked-install"
            assert "--locked" in command and "--no-editable" in command
            installed_file = (
                Path(env["UV_PROJECT_ENVIRONMENT"]) / "lib/fep_lean/__init__.py"
            )
            installed_file.parent.mkdir(parents=True)
            installed_file.write_bytes(fixture_sources["src/fep_lean/__init__.py"])
            actual_command = [
                sys.executable,
                "-I",
                "-S",
                "-c",
                "print('explicit install fixture')",
            ]
        elif command[2] == "-S":
            name = "installed-location"
            assert installed_file is not None
            location = {
                "python": "3.14.4",
                "purelib": str(installed_file.parent.parent),
            }
            actual_command = [
                sys.executable,
                "-I",
                "-S",
                "-c",
                "print(" + repr(json.dumps(location)) + ")",
            ]
        elif command[2] == "-c":
            name = "installed-runtime"
            assert installed_file is not None
            runtime = {
                "python": "3.14.4",
                "numpy": "2.5.1",
                "package": str(installed_file),
                "source_sha256": {
                    "src/fep_lean/__init__.py": bundle.digest(
                        installed_file.read_bytes()
                    )
                },
            }
            actual_command = [
                sys.executable,
                "-I",
                "-S",
                "-c",
                "print(" + repr(json.dumps(runtime)) + ")",
            ]
        else:
            name = "frozen-inputs" if "--check-inputs" in command else "synthetic"
            actual_command = [sys.executable, "-I", "-S", *command[2:]]
        calls.append(name)
        retained_bytes = retained_stat = None
        if failure == "installed-import-transient" and name == "installed-runtime":
            assert installed_file is not None
            retained_bytes, retained_stat = (
                installed_file.read_bytes(),
                installed_file.stat(),
            )
            installed_file.write_bytes(
                retained_bytes + b"# temporarily altered before import\n"
            )
            # The actual stdlib child observes changed bytes; the fake runtime
            # metadata alone cannot establish this mutation was unseen.
            actual_command[-1] = (
                "import pathlib; assert b'temporarily altered' in pathlib.Path("
                + repr(str(installed_file))
                + ").read_bytes(); "
                + actual_command[-1]
            )
        completed = run_process_group(actual_command, cwd=cwd, env=env, timeout=timeout)
        if retained_bytes is not None:
            assert installed_file is not None and retained_stat is not None
            installed_file.write_bytes(retained_bytes)
            os.utime(
                installed_file,
                ns=(retained_stat.st_atime_ns, retained_stat.st_mtime_ns),
            )
        if failure == "extracted-source" and name == "installed-runtime":
            change_with_restored_mtime(cwd / bundle.BASE / "run_synthetic.py")
        if failure == "installed-source" and name == "frozen-inputs":
            assert installed_file is not None
            change_with_restored_mtime(installed_file)
        return completed

    monkeypatch.setattr(bundle, "run_process_group", fixture_child)
    parent = tmp_path / "attempt-parent"
    parent.mkdir()
    output = parent / "reproduction"
    moved_parent = tmp_path / "retained-original-parent"
    outside = tmp_path / "outside"
    outside.mkdir()
    original_receipt = bundle.AttemptFiles.receipt
    mutated = False

    def seal_with_mutation(files: object, data: bytes) -> None:
        nonlocal mutated
        original_receipt(files, data)
        if mutated or not json.loads(data)["accepted"]:
            return
        if failure == "stream-seal":
            mutated = True
            (output / "locked-install.stdout").write_bytes(b"unowned changed stream")
        elif failure == "ancestor-seal":
            mutated = True
            parent.rename(moved_parent)
            parent.symlink_to(outside, target_is_directory=True)
        elif failure == "synthetic-seal":
            mutated = True
            (output / "synthetic").rename(output / "retained-synthetic")
            (output / "synthetic").symlink_to(outside, target_is_directory=True)
        elif failure == "receipt-seal":
            mutated = True
            (output / "acceptance.json").write_bytes(
                b'{"accepted":true,"forged":true}\n'
            )

    monkeypatch.setattr(bundle.AttemptFiles, "receipt", seal_with_mutation)
    if failure in {
        "extracted-source",
        "installed-source",
        "installed-import-transient",
    }:
        with pytest.raises(bundle.StudyRejection, match="input changed|stale input"):
            bundle.reproduce(raw, output, reviewer_id="explicit custody fixture")
        assert "synthetic" not in calls
    else:
        result = bundle.reproduce(raw, output, reviewer_id="explicit custody fixture")
        assert result["accepted"] is (failure is None)
    retained_output = (
        moved_parent / "reproduction" if failure == "ancestor-seal" else output
    )
    record = json.loads((retained_output / "acceptance.json").read_bytes())
    assert record["accepted"] is (failure is None)
    assert list(outside.iterdir()) == []
    if failure is None:
        assert calls == [
            "locked-install",
            "installed-location",
            "installed-runtime",
            "frozen-inputs",
            "synthetic",
        ]
        assert (output / "synthetic/fixture.npy").read_bytes() == array_raw
