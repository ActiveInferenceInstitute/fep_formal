"""Core release/publication boundary contracts."""

from __future__ import annotations

import hashlib
import io
import json
import os
import tarfile
from pathlib import Path

import pytest

from fep_formal.output import release_bundle as bundle_module
from fep_formal.output.release_bundle import (
    validate_release_bundle,
)
from tests._support.release_bundle import (
    _omit_manifested_member,
    _valid_contents,
    _write_raw_archive,
    _write_raw_entries,
)

PROJ = Path(__file__).resolve().parents[1]


def test_archive_validator_rejects_duplicate_members(tmp_path: Path) -> None:
    archive = tmp_path / "duplicate.tar.gz"
    _write_raw_archive(archive, ("MANIFEST.json", "MANIFEST.json"))

    validation = validate_release_bundle(archive)

    assert validation.valid is False
    assert "duplicate archive member: MANIFEST.json" in validation.errors


def test_deterministic_writer_normalizes_bytes_and_metadata(tmp_path: Path) -> None:
    contents = _valid_contents({})
    first = tmp_path / "first.tar.gz"
    second = tmp_path / "second.tar.gz"

    bundle_module._write_archive(first, contents, epoch=0)
    bundle_module._write_archive(second, contents, epoch=0)

    assert first.read_bytes() == second.read_bytes()
    assert (
        hashlib.sha256(first.read_bytes()).hexdigest()
        == hashlib.sha256(second.read_bytes()).hexdigest()
    )
    assert first.read_bytes()[3] == 0
    assert int.from_bytes(first.read_bytes()[4:8], "little") == 0
    validation = validate_release_bundle(first)
    assert validation.valid is True, validation.errors
    with tarfile.open(first, "r:gz") as archive:
        members = archive.getmembers()
    assert [member.name for member in members] == sorted(contents)
    assert all(member.mode == 0o644 for member in members)
    assert all(member.uid == member.gid == member.mtime == 0 for member in members)
    assert all(member.uname == member.gname == "" for member in members)


def test_deterministic_writer_syncs_the_complete_stream_before_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive = tmp_path / "release.tar.gz"
    synchronized_sizes: list[int] = []
    real_fsync = os.fsync

    def recording_fsync(file_descriptor: int) -> None:
        synchronized_sizes.append(os.fstat(file_descriptor).st_size)
        real_fsync(file_descriptor)

    monkeypatch.setattr(bundle_module.os, "fsync", recording_fsync)

    bundle_module._write_archive(
        archive,
        {"payload.bin": bytes(range(256)) * 64},
        epoch=0,
    )

    assert synchronized_sizes == [archive.stat().st_size]


def test_manifest_summary_is_derived_only_from_captured_member_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    coverage = {
        "topics": [{"id": f"fep-{index:03d}"} for index in range(1, 156)],
        "family_counts": {f"family-{index}": 1 for index in range(20)},
        "area_counts": {f"area-{index}": 1 for index in range(5)},
        "relations": [{} for _ in range(133)],
        "capabilities": [{} for _ in range(48)],
        "formal_modules": [{} for _ in range(34)],
    }
    native = {
        "lean_toolchain": "leanprover/lean4:v4.33.1",
        "lean_version": "Lean (version 4.33.1, fixture, Release)",
        "mathlib_tag": "v4.33.1",
        "mathlib_revision": "0" * 40,
    }
    payloads = {
        "docs/formalism-coverage.json": json.dumps(coverage).encode(),
        "output/native-verification.json": json.dumps(native).encode(),
        "output/formalism-audit.json": b"{}",
        bundle_module.BROWSER_RECEIPT.as_posix(): b"{}",
        bundle_module.PYTEST_RECEIPT.as_posix(): b"<testsuites/>",
        bundle_module.PYTHON_COVERAGE_RECEIPT.as_posix(): b"<coverage/>",
        bundle_module.NUMERICAL_RECEIPT.as_posix(): json.dumps(
            {"witness_count": 15}
        ).encode(),
        bundle_module.PYTHON_ACCEPTANCE_RECEIPT.as_posix(): b"{}",
    }
    source_record = bundle_module._BundleMember(
        "src/fep_formal/example.py", b"captured source\n", "source_owner"
    )
    config_record = bundle_module._BundleMember(
        "pyproject.toml", b"captured config\n", "configuration_snapshot"
    )
    members = (
        source_record,
        config_record,
        *(
            bundle_module._BundleMember(path, data, "fixture")
            for path, data in sorted(payloads.items())
        ),
    )
    monkeypatch.setattr(
        bundle_module,
        "source_owner_paths",
        lambda _root: pytest.fail("manifest re-read the live source roster"),
    )
    monkeypatch.setattr(
        bundle_module,
        "config_owner_paths",
        lambda _root: pytest.fail("manifest re-read the live config roster"),
    )

    manifest = bundle_module._build_manifest(tmp_path, members, epoch=0)

    assert manifest["catalogue"] == {
        "topics": 155,
        "families": 20,
        "areas": 5,
        "first_id": "fep-001",
        "last_id": "fep-155",
    }
    assert manifest["formalism"] == {
        "relations": 133,
        "capabilities": 48,
        "formal_modules": 34,
        "numerical_witnesses": 15,
    }
    assert manifest["source_sha256"] == bundle_module._digest_named_bytes(
        [(source_record.path, source_record.data)]
    )
    assert manifest["config_sha256"] == bundle_module._digest_named_bytes(
        [(config_record.path, config_record.data)]
    )


def test_archive_validator_rejects_traversal_and_symlinks(tmp_path: Path) -> None:
    traversal = tarfile.TarInfo("../escape")
    symlink = tarfile.TarInfo("docs/link")
    symlink.type = tarfile.SYMTYPE
    symlink.linkname = "/etc/passwd"
    archive = tmp_path / "unsafe.tar.gz"
    _write_raw_entries(
        archive,
        (
            (traversal, b"escape"),
            (symlink, None),
        ),
    )

    validation = validate_release_bundle(archive)

    assert validation.valid is False
    assert "unsafe archive member path: ../escape" in validation.errors
    assert "archive member is not a regular file: docs/link" in validation.errors


def test_archive_reader_does_not_decompress_an_over_limit_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive = tmp_path / "over-limit.tar.gz"
    bundle_module._write_archive(archive, _valid_contents({}), epoch=0)
    monkeypatch.setattr(bundle_module, "_MAX_ARCHIVE_BYTES", archive.stat().st_size - 1)

    def forbidden_open(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("over-limit archives must not be decompressed")

    monkeypatch.setattr(bundle_module.tarfile, "open", forbidden_open)

    contents, members, _epoch, errors = bundle_module._read_archive(archive)

    assert contents == {}
    assert members == ()
    assert errors == (
        f"compressed archive exceeds {bundle_module._MAX_ARCHIVE_BYTES} bytes",
    )


@pytest.mark.parametrize(
    ("limit_name", "limit", "expected_error"),
    [
        ("_MAX_ARCHIVE_MEMBERS", 1, "archive member count exceeds 1"),
        (
            "_MAX_TOTAL_MEMBER_BYTES",
            3,
            "aggregate archive payload exceeds 3 bytes",
        ),
    ],
)
def test_archive_reader_stops_before_extracting_payload_beyond_global_limits(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    limit_name: str,
    limit: int,
    expected_error: str,
) -> None:
    archive = tmp_path / f"{limit_name}.tar.gz"
    first = tarfile.TarInfo("a")
    second = tarfile.TarInfo("b")
    _write_raw_entries(archive, ((first, b"aa"), (second, b"bb")))
    monkeypatch.setattr(bundle_module, limit_name, limit)

    contents, members, _epoch, errors = bundle_module._read_archive(archive)

    assert contents["a"] == b"aa"
    assert "b" not in contents
    assert len(members) == 2
    assert expected_error in errors


@pytest.mark.parametrize(
    ("variant", "expected_error"),
    [
        ("missing", "cannot read release bundle:"),
        ("plain", "release bundle is not a gzip stream"),
    ],
)
def test_archive_validator_rejects_unreadable_and_nongzip_inputs(
    tmp_path: Path,
    variant: str,
    expected_error: str,
) -> None:
    archive = tmp_path / f"{variant}.tar.gz"
    if variant == "plain":
        archive.write_bytes(b"not a gzip stream")

    validation = validate_release_bundle(archive)

    assert validation.valid is False
    assert validation.member_count == 0
    assert any(error.startswith(expected_error) for error in validation.errors)
    assert validation.archive_sha256 == (
        "" if variant == "missing" else hashlib.sha256(archive.read_bytes()).hexdigest()
    )


def test_archive_reader_rejects_noncanonical_gzip_header_metadata(
    tmp_path: Path,
) -> None:
    archive = tmp_path / "header.tar.gz"
    _write_raw_archive(archive, ("payload.txt",))
    encoded = bytearray(archive.read_bytes())
    encoded[3] = 1
    encoded[8] = 0
    encoded[9] = 3
    archive.write_bytes(encoded)

    contents, members, _epoch, errors = bundle_module._read_archive(archive)

    assert contents == {"payload.txt": b"x"}
    assert [member.name for member in members] == ["payload.txt"]
    assert errors == (
        "gzip header flags must be zero",
        "gzip header must declare maximum compression",
        "gzip header operating-system byte must be 255",
    )


def test_archive_reader_stops_before_extracting_an_over_limit_member(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive = tmp_path / "large-member.tar.gz"
    info = tarfile.TarInfo("large.bin")
    _write_raw_entries(archive, ((info, b"four"),))
    monkeypatch.setattr(bundle_module, "_MAX_MEMBER_BYTES", 3)

    contents, members, _epoch, errors = bundle_module._read_archive(archive)

    assert contents == {}
    assert [member.name for member in members] == ["large.bin"]
    assert errors == ("archive member exceeds 3 bytes: large.bin",)


@pytest.mark.parametrize(
    ("extracted", "expected_error"),
    [
        (None, "cannot read archive member: payload.bin"),
        (b"short", "archive member size is inconsistent: payload.bin"),
    ],
)
def test_archive_reader_rejects_unreadable_or_short_member_streams(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    extracted: bytes | None,
    expected_error: str,
) -> None:
    archive = tmp_path / "unreadable-member.tar.gz"
    info = tarfile.TarInfo("payload.bin")
    _write_raw_entries(archive, ((info, b"complete"),))

    def broken_extractfile(
        _archive: tarfile.TarFile, _member: tarfile.TarInfo
    ) -> io.BytesIO | None:
        return None if extracted is None else io.BytesIO(extracted)

    monkeypatch.setattr(tarfile.TarFile, "extractfile", broken_extractfile)

    contents, members, _epoch, errors = bundle_module._read_archive(archive)

    assert contents == {}
    assert [member.name for member in members] == ["payload.bin"]
    assert errors == (expected_error,)


def test_archive_reader_reports_decompressor_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive = tmp_path / "corrupt.tar.gz"
    _write_raw_archive(archive, ("payload.txt",))

    def fail_to_open(*_args: object, **_kwargs: object) -> None:
        raise tarfile.ReadError("corrupt archive")

    monkeypatch.setattr(tarfile, "open", fail_to_open)

    contents, members, _epoch, errors = bundle_module._read_archive(archive)

    assert contents == {}
    assert members == ()
    assert errors == ("cannot parse release bundle: corrupt archive",)


@pytest.mark.parametrize(
    ("variant", "expected_error"),
    [
        ("missing_hash", "missing checksum: README.md"),
        ("unexpected", "unexpected archive member: extra.txt"),
        ("tampered", "checksum mismatch: README.md"),
        (
            "provider",
            "provider artifact is forbidden: output/reports/full-provider.json",
        ),
    ],
)
def test_archive_validator_rejects_missing_unexpected_and_tampered_members(
    tmp_path: Path,
    variant: str,
    expected_error: str,
) -> None:
    payload_path = (
        "output/reports/full-provider.json" if variant == "provider" else "README.md"
    )
    contents = _valid_contents({payload_path: b"checked\n"})
    if variant == "missing_hash":
        contents["SHA256SUMS"] = b""
    elif variant == "unexpected":
        contents["extra.txt"] = b"unmanifested\n"
    elif variant == "tampered":
        contents["README.md"] = b"changed\n"
    archive = tmp_path / f"{variant}.tar.gz"
    bundle_module._write_archive(archive, contents, epoch=0)

    validation = validate_release_bundle(archive)

    assert validation.valid is False
    assert expected_error in validation.errors


@pytest.mark.parametrize("name", ["config.yaml", "preamble.md", "references.bib"])
@pytest.mark.parametrize("mutation", ["omitted", "tampered"])
def test_archive_requires_exact_rendered_metadata_payloads(
    tmp_path: Path, name: str, mutation: str
) -> None:
    relative = f"output/manuscript/{name}"
    contents = _valid_contents({relative: b"exact metadata\r\n"})
    assert bundle_module._expected_evidence_class(relative) == (
        "rendered_manuscript_metadata"
    )
    if mutation == "omitted":
        _omit_manifested_member(contents, relative)
        error = f"required release payload is omitted: {relative}"
    else:
        contents[relative] = b"altered metadata\n"
        error = f"checksum mismatch: {relative}"
    archive = tmp_path / "metadata.tar.gz"
    bundle_module._write_archive(archive, contents, epoch=0)
    validation = validate_release_bundle(archive)
    assert not validation.valid
    assert error in validation.errors


def test_archive_validator_rejects_self_consistent_semantic_manifest_tampering(
    tmp_path: Path,
) -> None:
    contents = _valid_contents({})
    manifest = json.loads(contents[bundle_module.MANIFEST_NAME])
    manifest["catalogue"]["topics"] = 154
    manifest["formalism"]["relations"] = 132
    manifest["formalism"]["formal_modules"] = 0
    manifest["toolchain"].update(
        {
            "lean_version": "Lean (version 4.32.0, fixture, Release)",
            "mathlib_tag": "v4.31.0",
            "mathlib_revision": "A" * 40,
        }
    )
    manifest["source_sha256"] = "not-a-digest"
    manifest["manifested_lean_sources"].append("lean/FepSketches/missing.lean")
    manifest["manifested_lean_sources"].sort()
    manifest["evidence"]["native_lean"]["sha256"] = "0" * 64
    manifest["evidence"]["browser_interaction"]["current"] = False
    manifest["evidence"]["numerical_witnesses"]["evidence_kind"] = "proof"
    contents[bundle_module.MANIFEST_NAME] = bundle_module._canonical_json(manifest)
    contents[bundle_module.CHECKSUMS_NAME] = "".join(
        f"{hashlib.sha256(contents[name]).hexdigest()}  {name}\n"
        for name in sorted(contents)
        if name != bundle_module.CHECKSUMS_NAME
    ).encode()
    archive = tmp_path / "semantic-tampering.tar.gz"
    bundle_module._write_archive(archive, contents, epoch=0)

    validation = validate_release_bundle(archive)

    assert validation.valid is False
    expected_errors = {
        "manifest catalog does not match the 168-topic release seal",
        "manifest formalism.relations is stale",
        "manifest formalism.formal_modules must be positive",
        "manifest Lean version does not match its toolchain pin",
        "manifest Mathlib tag does not match the Lean pin",
        "manifest Mathlib revision is not a lowercase Git SHA",
        "manifest source_sha256 is invalid",
        "manifested Lean source is missing or invalid: lean/FepSketches/missing.lean",
        "manifest evidence record is invalid: browser_interaction",
        "manifest evidence hash is invalid: native_lean",
        "manifest numerical evidence boundary was weakened",
    }
    assert expected_errors <= set(validation.errors)


def test_archive_validator_rejects_ambiguous_checksum_tables(tmp_path: Path) -> None:
    contents = _valid_contents({})
    digest = "0" * 64
    contents[bundle_module.CHECKSUMS_NAME] = (
        f"{digest}  README.md\n"
        f"{digest}  README.md\n"
        f"{digest}  ../escape\n"
        "malformed checksum record\n"
        f"{digest}  CITATION.cff"
    ).encode()
    archive = tmp_path / "ambiguous-checksums.tar.gz"
    bundle_module._write_archive(archive, contents, epoch=0)

    validation = validate_release_bundle(archive)

    assert validation.valid is False
    assert {
        "SHA256SUMS must end with a newline",
        "duplicate checksum path: README.md",
        "unsafe checksum path: ../escape",
        "malformed checksum line: malformed checksum record",
        "SHA256SUMS paths must be lexically ordered",
    } <= set(validation.errors)


@pytest.mark.parametrize(
    ("variant", "expected_error"),
    [
        ("manifest_list", "MANIFEST.json must contain a JSON object"),
        ("non_utf8_checksums", "cannot decode SHA256SUMS:"),
    ],
)
def test_archive_validator_rejects_unparseable_control_records(
    tmp_path: Path,
    variant: str,
    expected_error: str,
) -> None:
    contents = _valid_contents({})
    if variant == "manifest_list":
        contents[bundle_module.MANIFEST_NAME] = b"[]\n"
        contents[bundle_module.CHECKSUMS_NAME] = "".join(
            f"{hashlib.sha256(contents[name]).hexdigest()}  {name}\n"
            for name in sorted(contents)
            if name != bundle_module.CHECKSUMS_NAME
        ).encode()
    else:
        contents[bundle_module.CHECKSUMS_NAME] = b"\xff"
    archive = tmp_path / f"{variant}.tar.gz"
    bundle_module._write_archive(archive, contents, epoch=0)

    validation = validate_release_bundle(archive)

    assert validation.valid is False
    assert any(error.startswith(expected_error) for error in validation.errors)


def test_archive_validator_rejects_ambiguous_manifest_member_records(
    tmp_path: Path,
) -> None:
    contents = _valid_contents({})
    manifest = json.loads(contents[bundle_module.MANIFEST_NAME])
    records = list(reversed(manifest["members"]))
    tampered_path = records[0]["path"]
    records[0] = {
        **records[0],
        "evidence_class": "",
        "invented_field": True,
    }
    records.extend(
        (
            "not an object",
            {
                "path": "../escape",
                "sha256": "0" * 64,
                "size": 0,
                "evidence_class": "fixture",
            },
            {
                "path": bundle_module.MANIFEST_NAME,
                "sha256": "0" * 64,
                "size": 0,
                "evidence_class": "fixture",
            },
            dict(records[-1]),
        )
    )
    manifest["members"] = records
    contents[bundle_module.MANIFEST_NAME] = bundle_module._canonical_json(manifest)
    contents[bundle_module.CHECKSUMS_NAME] = "".join(
        f"{hashlib.sha256(contents[name]).hexdigest()}  {name}\n"
        for name in sorted(contents)
        if name != bundle_module.CHECKSUMS_NAME
    ).encode()
    archive = tmp_path / "ambiguous-manifest-members.tar.gz"
    bundle_module._write_archive(archive, contents, epoch=0)

    validation = validate_release_bundle(archive)

    assert validation.valid is False
    assert {
        "manifest members must contain objects",
        "manifest member has unsafe path: ../escape",
        f"manifest payload cannot include {bundle_module.MANIFEST_NAME}",
        f"duplicate manifest member: {records[-1]['path']}",
        f"manifest member fields are invalid: {tampered_path}",
        f"manifest member evidence class is invalid: {tampered_path}",
        (f"manifest member evidence class is invalid for its path: {tampered_path}"),
        "manifest members must be lexically ordered",
    } <= set(validation.errors)


def test_archive_validator_rejects_unnormalized_metadata(tmp_path: Path) -> None:
    info = tarfile.TarInfo("MANIFEST.json")
    info.mode = 0o600
    info.uid = 1000
    info.gid = 1000
    info.uname = "builder"
    info.gname = "builder"
    info.mtime = 42
    archive = tmp_path / "metadata.tar.gz"
    _write_raw_entries(archive, ((info, b"{}"),))

    validation = validate_release_bundle(archive)

    assert validation.valid is False
    assert "archive member mode must be 0644: MANIFEST.json" in validation.errors
    assert "archive member uid/gid must be zero: MANIFEST.json" in validation.errors
    assert (
        "archive member owner names must be empty: MANIFEST.json" in validation.errors
    )
    assert (
        "archive member mtime differs from gzip mtime: MANIFEST.json"
        in validation.errors
    )


@pytest.mark.parametrize(
    "omitted",
    [
        "manuscript/references.bib",
        "manuscript/09z_unified_formalism_catalogue.md",
        "docs/formalism-coverage.json",
        "docs/formalism-atlas.svg",
        "docs/formal-kernel-dashboard.html",
        "output/native-verification.json",
        "output/formalism-audit.json",
        "output/pytest.xml",
        "output/coverage.xml",
        bundle_module.PYTHON_ACCEPTANCE_RECEIPT.as_posix(),
        bundle_module.BROWSER_RECEIPT.as_posix(),
        bundle_module.NUMERICAL_RECEIPT.as_posix(),
        "lean/FepSketches/fep_all.lean",
        bundle_module.PUBLICATION_HTML.as_posix(),
        bundle_module.RENDERER_PROVENANCE.as_posix(),
    ],
)
def test_required_release_payload_cannot_be_omitted(
    tmp_path: Path, omitted: str
) -> None:
    contents = _valid_contents({})
    _omit_manifested_member(contents, omitted)
    archive = tmp_path / "omitted.tar.gz"
    bundle_module._write_archive(archive, contents, epoch=0)

    validation = validate_release_bundle(archive)

    assert validation.valid is False
    assert f"required release payload is omitted: {omitted}" in validation.errors
