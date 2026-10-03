"""Deterministic release bundles fail closed at the archive boundary."""

from __future__ import annotations

import gzip
import hashlib
import io
import json
import os
import re
import runpy
import shlex
import shutil
import struct
import subprocess
import sys
import tarfile
import time
import zlib
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from fep_lean.output import release_bundle as bundle_module
from fep_lean.output.release_bundle import (
    build_numerical_witness_receipt,
    build_release_bundle,
    publication_manuscript_errors,
    render_publication_manuscript,
    validate_release_bundle,
    write_publication_manuscript,
)

PROJ = Path(__file__).resolve().parents[1]


def _fixture_renderer_tools(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    names: tuple[str, ...] = ("pandoc",),
    *,
    actual_identity: bool = False,
) -> dict[str, Path]:
    """Keep real executable custody separate from mocked render output."""
    tools_root = tmp_path / "renderer-tools"
    tools_root.mkdir()
    tools = {name: tools_root / name for name in names}
    for name, path in tools.items():
        path.write_text(f"#!/bin/sh\nprintf '%s\\n' '{name} fixture'\n")
        path.chmod(0o700)
    monkeypatch.setattr(
        bundle_module.shutil,
        "which",
        lambda name: str(tools[name]) if name in tools else None,
    )
    if not actual_identity:
        monkeypatch.setattr(
            bundle_module,
            "_tool_identity",
            lambda executable: {
                "name": Path(executable).name,
                "version": f"{Path(executable).name} fixture",
                "binary_sha256": hashlib.sha256(
                    Path(executable).read_bytes()
                ).hexdigest(),
            },
        )
    return tools


def test_bounded_manuscript_projection_accepts_zero_count_relation_kinds() -> None:
    project_root = Path(__file__).resolve().parents[1]

    assert "manuscript formalism relation counts are stale" not in (
        bundle_module._bounded_manuscript_projection_errors(project_root)
    )


def _write_raw_entries(
    path: Path, entries: tuple[tuple[tarfile.TarInfo, bytes | None], ...]
) -> None:
    payload = io.BytesIO()
    with tarfile.open(fileobj=payload, mode="w", format=tarfile.USTAR_FORMAT) as tar:
        for info, data in entries:
            info.size = len(data) if data is not None else 0
            tar.addfile(info, io.BytesIO(data) if data is not None else None)
    with (
        path.open("wb") as raw,
        gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0) as zipped,
    ):
        zipped.write(payload.getvalue())


def _write_raw_archive(path: Path, names: tuple[str, ...]) -> None:
    _write_raw_entries(
        path,
        tuple((tarfile.TarInfo(name), b"x") for name in names),
    )


def _png_bytes(width: int, height: int) -> bytes:
    def chunk(kind: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload))
            + kind
            + payload
            + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
        )

    rows = b"".join(b"\0" + b"\x80" * width for _ in range(height))
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(rows, level=9))
        + chunk(b"IEND", b"")
    )


def _valid_contents(payload: dict[str, bytes]) -> dict[str, bytes]:
    complete_payload = {
        path: f"fixture {path}\n".encode()
        for path in bundle_module._STATIC_REQUIRED_BUNDLE_PATHS
    }
    complete_payload["output/manuscript/01_chapter.md"] = b"# Chapter\n"
    complete_payload.update(payload)
    records = [
        {
            "path": name,
            "sha256": hashlib.sha256(data).hexdigest(),
            "size": len(data),
            "evidence_class": (
                bundle_module._expected_evidence_class(name) or "fixture"
            ),
        }
        for name, data in sorted(complete_payload.items())
    ]
    record_by_path = {record["path"]: record for record in records}
    manifest = {
        "schema_version": 1,
        "kind": "fep-lean-evidence-bundle",
        "source_date_epoch": 0,
        "catalogue": {
            "topics": 168,
            "families": 22,
            "areas": 5,
            "first_id": "fep-001",
            "last_id": "fep-168",
        },
        "formalism": {
            "relations": 146,
            "capabilities": 50,
            "formal_modules": 1,
            "numerical_witnesses": 17,
        },
        "toolchain": {
            "lean_toolchain": "leanprover/lean4:v4.33.1",
            "lean_version": "Lean (version 4.33.1, fixture, Release)",
            "mathlib_tag": "v4.33.1",
            "mathlib_revision": "0" * 40,
        },
        "source_sha256": "1" * 64,
        "config_sha256": "2" * 64,
        "manifested_lean_sources": sorted(
            name for name in complete_payload if name.endswith(".lean")
        ),
        "evidence": {
            "native_lean": {
                "current": True,
                "path": "output/native-verification.json",
                "sha256": record_by_path["output/native-verification.json"]["sha256"],
            },
            "declaration_axiom_audit": {
                "current": True,
                "path": "output/formalism-audit.json",
                "sha256": record_by_path["output/formalism-audit.json"]["sha256"],
            },
            "browser_interaction": {
                "current": True,
                "path": bundle_module.BROWSER_RECEIPT.as_posix(),
                "sha256": record_by_path[bundle_module.BROWSER_RECEIPT.as_posix()][
                    "sha256"
                ],
            },
            "numerical_witnesses": {
                "current": True,
                "path": bundle_module.NUMERICAL_RECEIPT.as_posix(),
                "sha256": record_by_path[bundle_module.NUMERICAL_RECEIPT.as_posix()][
                    "sha256"
                ],
                "evidence_kind": ("deterministic_numerical_witness_non_proof_evidence"),
            },
            "python_tests": {
                "current": True,
                "path": bundle_module.PYTEST_RECEIPT.as_posix(),
                "sha256": record_by_path[bundle_module.PYTEST_RECEIPT.as_posix()][
                    "sha256"
                ],
            },
            "python_coverage": {
                "current": True,
                "path": bundle_module.PYTHON_COVERAGE_RECEIPT.as_posix(),
                "sha256": record_by_path[
                    bundle_module.PYTHON_COVERAGE_RECEIPT.as_posix()
                ]["sha256"],
            },
            "python_acceptance": {
                "current": True,
                "path": bundle_module.PYTHON_ACCEPTANCE_RECEIPT.as_posix(),
                "sha256": record_by_path[
                    bundle_module.PYTHON_ACCEPTANCE_RECEIPT.as_posix()
                ]["sha256"],
            },
        },
        "external_full_mode": {
            "current": False,
            "authorized": False,
            "artifacts": [],
        },
        "members": records,
    }
    manifest_bytes = (
        json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode()
    with_manifest = {**complete_payload, "MANIFEST.json": manifest_bytes}
    checksums = "".join(
        f"{hashlib.sha256(with_manifest[name]).hexdigest()}  {name}\n"
        for name in sorted(with_manifest)
    ).encode()
    return {**with_manifest, "SHA256SUMS": checksums}


def _omit_manifested_member(contents: dict[str, bytes], omitted: str) -> None:
    contents.pop(omitted)
    manifest = json.loads(contents["MANIFEST.json"])
    manifest["members"] = [
        record for record in manifest["members"] if record["path"] != omitted
    ]
    manifest["manifested_lean_sources"] = [
        path for path in manifest["manifested_lean_sources"] if path != omitted
    ]
    contents["MANIFEST.json"] = (
        json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode()
    contents["SHA256SUMS"] = "".join(
        f"{hashlib.sha256(contents[name]).hexdigest()}  {name}\n"
        for name in sorted(contents)
        if name != "SHA256SUMS"
    ).encode()


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
        "src/fep_lean/example.py", b"captured source\n", "source_owner"
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


def test_project_snapshot_captures_each_release_owned_evidence_plane(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture_bytes = {
        "src/fep_lean/example.py": b"value = 1\n",
        "lean/FepSketches/example.lean": b"theorem example : True := by trivial\n",
        "pyproject.toml": b"[project]\nname = 'fixture'\n",
        "README.md": b"# Fixture\n",
        bundle_module.RENDERER_PROVENANCE.as_posix(): (b'{"pdf":{"current":true}}\n'),
        "manuscript/01_chapter.md": b"# Source chapter\n",
        "output/manuscript/01_chapter.md": b"# Rendered chapter\n",
        "output/manuscript/config.yaml": b"title: raw {{metadata}}\r\n",
        "output/manuscript/preamble.md": b"% raw {{metadata}}\r\n",
        "output/manuscript/references.bib": b"@article{raw}\r\n",
        "output/manuscript/assets/atlas.svg": b"<svg/>\n",
        bundle_module.PUBLICATION_PDF.as_posix(): b"%PDF fixture\n",
        "output/browser/atlas.png": b"PNG fixture\n",
    }
    for relative, data in fixture_bytes.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    monkeypatch.setattr(
        bundle_module,
        "source_owner_paths",
        lambda root: (
            root / "src/fep_lean/example.py",
            root / "lean/FepSketches/example.lean",
        ),
    )
    monkeypatch.setattr(
        bundle_module,
        "config_owner_paths",
        lambda root: (root / "pyproject.toml",),
    )
    monkeypatch.setattr(
        bundle_module,
        "_REQUIRED_STATIC_MEMBERS",
        (
            ("README.md", "project_documentation"),
            (
                bundle_module.RENDERER_PROVENANCE.as_posix(),
                "renderer_provenance",
            ),
            *(
                row
                for row in bundle_module._REQUIRED_STATIC_MEMBERS
                if row[1] == "rendered_manuscript_metadata"
            ),
        ),
    )
    monkeypatch.setattr(
        bundle_module,
        "manuscript_source_files",
        lambda root: (root / "01_chapter.md",),
    )
    monkeypatch.setattr(
        bundle_module,
        "MANUSCRIPT_ASSETS",
        {
            "../docs/atlas.svg": (
                Path("docs/atlas.svg"),
                Path("assets/atlas.svg"),
            )
        },
    )
    monkeypatch.setattr(
        bundle_module,
        "_publication_resource_records",
        lambda _root: (("output/figures/status.png", b"plot fixture\n"),),
    )
    monkeypatch.setattr(
        bundle_module,
        "_browser_screenshot_paths",
        lambda _root: ("output/browser/atlas.png",),
    )
    monkeypatch.setattr(
        bundle_module,
        "build_numerical_witness_receipt",
        lambda _root: b"numerical receipt\n",
    )
    monkeypatch.setattr(
        bundle_module,
        "build_python_acceptance_receipt",
        lambda _root: b"python acceptance receipt\n",
    )

    members = bundle_module._project_members(tmp_path)
    observed = {member.path: (member.evidence_class, member.data) for member in members}

    assert [member.path for member in members] == sorted(observed)
    assert observed == {
        "README.md": ("project_documentation", b"# Fixture\n"),
        "lean/FepSketches/example.lean": (
            "manifested_lean_source",
            b"theorem example : True := by trivial\n",
        ),
        "output/browser/atlas.png": ("browser_screenshot", b"PNG fixture\n"),
        "output/figures/status.png": (
            "rendered_manuscript_figure",
            b"plot fixture\n",
        ),
        "output/manuscript/01_chapter.md": (
            "rendered_manuscript",
            b"# Rendered chapter\n",
        ),
        "output/manuscript/config.yaml": (
            "rendered_manuscript_metadata",
            b"title: raw {{metadata}}\r\n",
        ),
        "output/manuscript/preamble.md": (
            "rendered_manuscript_metadata",
            b"% raw {{metadata}}\r\n",
        ),
        "output/manuscript/references.bib": (
            "rendered_manuscript_metadata",
            b"@article{raw}\r\n",
        ),
        "output/manuscript/assets/atlas.svg": (
            "rendered_manuscript_asset",
            b"<svg/>\n",
        ),
        bundle_module.PUBLICATION_PDF.as_posix(): (
            "rendered_manuscript_pdf",
            b"%PDF fixture\n",
        ),
        bundle_module.RENDERER_PROVENANCE.as_posix(): (
            "renderer_provenance",
            b'{"pdf":{"current":true}}\n',
        ),
        bundle_module.NUMERICAL_RECEIPT.as_posix(): (
            "numerical_non_proof_receipt",
            b"numerical receipt\n",
        ),
        bundle_module.PYTHON_ACCEPTANCE_RECEIPT.as_posix(): (
            "python_acceptance_receipt",
            b"python acceptance receipt\n",
        ),
        "pyproject.toml": (
            "configuration_snapshot",
            b"[project]\nname = 'fixture'\n",
        ),
        "src/fep_lean/example.py": ("source_owner", b"value = 1\n"),
    }


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
        "manifest catalogue does not match the 168-topic release seal",
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


def _minimal_manuscript(project_root: Path) -> None:
    manuscript = project_root / "manuscript"
    rendered = project_root / "output" / "manuscript"
    manuscript.mkdir(parents=True)
    rendered.mkdir(parents=True)
    shutil.copy2(PROJ / "manuscript/config.yaml", manuscript / "config.yaml")
    asset = (PROJ / "manuscript/assets/graphical-abstract.png").read_bytes()
    (manuscript / "assets").mkdir()
    (manuscript / "assets/graphical-abstract.png").write_bytes(asset)
    (rendered / "assets").mkdir()
    (rendered / "assets/graphical-abstract.png").write_bytes(asset)
    front_matter = (
        "---\n"
        "author:\n"
        "  - |\n"
        "    **Author information**  \n"
        "    Daniel Ari Friedman  \n"
        "    Active Inference Institute  \n"
        "    daniel@activeinference.institute · "
        "https://orcid.org/0000-0001-6232-9096\n"
        'abstract-title: "Graphical abstract"\n'
        "abstract: |\n"
        "  ![Graphical abstract fixture](assets/graphical-abstract.png){width=90%}\n"
        "---\n"
    )
    (manuscript / "00_front_matter.md").write_text(
        front_matter.replace(
            "assets/graphical-abstract.png",
            "{{publication.graphical_abstract.render_path}}",
        ),
        encoding="utf-8",
    )
    (rendered / "00_front_matter.md").write_text(front_matter, encoding="utf-8")
    (manuscript / "references.bib").write_text("", encoding="utf-8")
    (manuscript / "preamble.md").write_text(
        "```latex\n% deterministic fixture\n```\n", encoding="utf-8"
    )
    (manuscript / "01_chapter.md").write_text(
        "# Reproducible chapter\n\nThe finite result is checked.\n",
        encoding="utf-8",
    )
    (rendered / "01_chapter.md").write_text(
        "# Reproducible chapter\n\nThe finite result is checked.\n",
        encoding="utf-8",
    )
    (manuscript / "09z_unified_formalism_catalogue.md").write_text(
        "# Appendix\n\nA source-bound appendix.\n",
        encoding="utf-8",
    )


def test_publication_html_shows_author_and_embeds_graphical_abstract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pandoc = shutil.which("pandoc")
    if pandoc is None:
        pytest.skip("pandoc is unavailable")
    _minimal_manuscript(tmp_path)
    monkeypatch.setattr(
        bundle_module.shutil,
        "which",
        lambda name: pandoc if name == "pandoc" else None,
    )

    rendered = render_publication_manuscript(tmp_path, source_date_epoch=0)

    assert b"Author information" in rendered.html
    assert b"Daniel Ari Friedman" in rendered.html
    assert b"Active Inference Institute" in rendered.html
    assert b"daniel@activeinference.institute" in rendered.html
    assert b"0000-0001-6232-9096" in rendered.html
    assert b"data:image/png;base64," in rendered.html
    provenance = json.loads(rendered.provenance)
    inputs = {record["path"]: record for record in provenance["inputs"]}
    assert inputs["manuscript/assets/graphical-abstract.png"]["sha256"] == (
        "68b7819e8c799348b9d958cee41c5c4fdb5b716690749e0e586ef0e90086a904"
    )


def test_publication_pdf_shows_author_and_embeds_graphical_abstract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    required = {
        name: shutil.which(name)
        for name in (
            "pandoc",
            "xelatex",
            "xdvipdfmx",
            "mutool",
            "pdftotext",
            "pdfimages",
        )
    }
    if any(executable is None for executable in required.values()):
        pytest.skip("complete PDF inspection toolchain is unavailable")
    _minimal_manuscript(tmp_path)
    scratch = tmp_path / "render scratch"
    scratch.mkdir()
    monkeypatch.setattr(bundle_module.tempfile, "tempdir", str(scratch))

    rendered = render_publication_manuscript(tmp_path, source_date_epoch=0)

    assert rendered.pdf is not None
    provenance = json.loads(rendered.provenance)
    assert provenance["pdf"]["status"] == "reproducible"
    assert (
        provenance["renderers"]["xdvipdfmx"]["binary_sha256"]
        == hashlib.sha256(
            Path(str(required["xdvipdfmx"])).resolve().read_bytes()
        ).hexdigest()
    )
    assert provenance["commands"]["pdf_driver"] == [
        "xdvipdfmx",
        "-q",
        "-E",
        "-o",
        "-",
        "<XDV_STDIN>",
    ]
    repeated = render_publication_manuscript(tmp_path, source_date_epoch=0)
    assert repeated.pdf == rendered.pdf
    assert repeated.html == rendered.html
    assert repeated.provenance == rendered.provenance
    (tmp_path / "publication-repeated.pdf").write_bytes(repeated.pdf)
    (tmp_path / "publication-provenance.json").write_bytes(rendered.provenance)
    pdf = tmp_path / "publication.pdf"
    pdf.write_bytes(rendered.pdf)
    text_result = subprocess.run(
        [str(required["pdftotext"]), "-f", "1", "-l", "1", "-layout", str(pdf), "-"],
        check=False,
        capture_output=True,
        text=True,
    )
    images_result = subprocess.run(
        [str(required["pdfimages"]), "-f", "1", "-l", "1", "-list", str(pdf)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert text_result.returncode == 0
    assert "Author information" in text_result.stdout
    assert "Daniel Ari Friedman" in text_result.stdout
    assert "Active Inference Institute" in text_result.stdout
    assert "daniel@activeinference.institute" in text_result.stdout
    assert "0000-0001-6232-9096" in text_result.stdout
    assert images_result.returncode == 0
    assert re.search(r"\b1536\s+1024\b", images_result.stdout)


def test_native_pdf_driver_keeps_changed_content_nonreproducible(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    required = {
        name: shutil.which(name)
        for name in ("pandoc", "xelatex", "xdvipdfmx", "mutool", "pdftotext")
    }
    if any(executable is None for executable in required.values()):
        pytest.skip("complete native PDF rendering toolchain is unavailable")
    _minimal_manuscript(tmp_path)
    real_renderer = bundle_module._run_renderer
    pdf_calls = 0
    normalized_pdfs: list[Path] = []

    def changed_second_render(
        command: list[str], **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        nonlocal pdf_calls
        if command[0] == required["pandoc"]:
            pdf_calls += 1
            if pdf_calls == 2:
                (tmp_path / "output/manuscript/01_chapter.md").write_text(
                    "# Reproducible chapter\n\nA different scientific statement.\n",
                    encoding="utf-8",
                )
        result = real_renderer(command, **kwargs)  # type: ignore[arg-type]
        if command[0] == required["mutool"] and result.returncode == 0:
            retained = tmp_path / f"changed-content-{len(normalized_pdfs)}.pdf"
            retained.write_bytes(Path(command[-1]).read_bytes())
            normalized_pdfs.append(retained)
        return result

    monkeypatch.setattr(bundle_module, "_run_renderer", changed_second_render)
    pdf, status = bundle_module._render_twice(
        bundle_module._pandoc_base_command(tmp_path, str(required["pandoc"])),
        project_root=tmp_path,
        epoch=0,
        suffix=".pdf",
        extra_args=(),
        include_header=bundle_module._latex_preamble(tmp_path),
        timeout=120,
        auxiliary_executables=tuple(str(path) for path in required.values()),
        pdf_normalizer=str(required["mutool"]),
        pdf_engine=str(required["xelatex"]),
        pdf_driver=str(required["xdvipdfmx"]),
    )

    assert pdf_calls == 2
    assert pdf is None
    assert status == "renderer_output_not_reproducible"
    assert len(normalized_pdfs) == 2
    texts = [
        subprocess.check_output([str(required["pdftotext"]), str(path), "-"], text=True)
        for path in normalized_pdfs
    ]
    assert "The finite result is checked" in texts[0]
    assert "A different scientific statement" in texts[1]


def test_publication_resources_require_graphical_abstract_contract(
    tmp_path: Path,
) -> None:
    _minimal_manuscript(tmp_path)
    config_path = tmp_path / "manuscript/config.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    del config["publication"]["graphical_abstract"]
    config_path.write_text(
        yaml.safe_dump(config, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )

    with pytest.raises(
        bundle_module.ReleaseBundleError,
        match="manuscript graphical abstract metadata",
    ):
        bundle_module._publication_resource_records(tmp_path)


def test_publication_html_is_two_render_reproducible_and_checkable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pandoc = shutil.which("pandoc")
    if pandoc is None:
        pytest.skip("pandoc is unavailable")
    _minimal_manuscript(tmp_path)
    real_which = shutil.which
    monkeypatch.setattr(
        bundle_module.shutil,
        "which",
        lambda name: pandoc if name == "pandoc" else None,
    )

    rendered = render_publication_manuscript(tmp_path, source_date_epoch=0)
    written = write_publication_manuscript(tmp_path, source_date_epoch=0)

    assert b"Reproducible chapter" in rendered.html
    assert rendered.pdf is None
    provenance = json.loads(rendered.provenance)
    assert provenance["html"]["status"] == "reproducible"
    assert provenance["pdf"]["status"] == "xelatex_unavailable"
    assert "manuscript/preamble.md" in {
        record["path"] for record in provenance["inputs"]
    }
    assert set(provenance["normalized_environment"]) == {
        "PATH",
        "HOME",
        "XDG_CACHE_HOME",
        "TEXMFVAR",
        "TEXMFCONFIG",
        "SOURCE_DATE_EPOCH",
        "FORCE_SOURCE_DATE",
        "TZ",
        "LANG",
        "LC_ALL",
    }
    assert (
        provenance["renderers"]["pandoc"]["binary_sha256"]
        == hashlib.sha256(Path(pandoc).resolve().read_bytes()).hexdigest()
    )
    assert [path.name for path in written] == [
        "fep-lean-manuscript.html",
        "renderer-provenance.json",
    ]
    assert publication_manuscript_errors(tmp_path, source_date_epoch=0) == ()

    (tmp_path / "output/manuscript/fep-lean-manuscript.html").write_bytes(b"stale")
    assert publication_manuscript_errors(tmp_path, source_date_epoch=0) == (
        (
            "publication manuscript member is stale: "
            "output/manuscript/fep-lean-manuscript.html"
        ),
    )
    assert real_which("pandoc") == pandoc


@pytest.mark.parametrize("name", ["config.yaml", "preamble.md", "references.bib"])
@pytest.mark.parametrize("mutation", ["missing", "stale", "symlink"])
def test_rendered_metadata_validates_canonical_bytes_and_rejects_extra_members(
    tmp_path: Path, name: str, mutation: str
) -> None:
    from fep_lean.output.publication_metadata import load_graphical_abstract

    _minimal_manuscript(tmp_path)
    for source, _destination in bundle_module.MANUSCRIPT_ASSETS.values():
        asset = tmp_path / source
        asset.parent.mkdir(parents=True, exist_ok=True)
        asset.write_bytes(b"fixture asset\n")
    variables = {
        "publication": {
            "graphical_abstract": load_graphical_abstract(
                tmp_path
            ).manuscript_variables(),
        },
    }
    (tmp_path / "manuscript/manuscript_vars.yaml").write_text(
        yaml.safe_dump(variables), encoding="utf-8"
    )
    rendered = tmp_path / "output/manuscript"
    bundle_module.render_manuscript(tmp_path / "manuscript", rendered, variables)
    assert bundle_module._rendered_manuscript_errors(tmp_path) == ()
    actual = rendered / name
    if mutation == "missing":
        actual.unlink()
    elif mutation == "symlink":
        actual.unlink()
        actual.symlink_to(tmp_path / "manuscript" / name)
    else:
        actual.write_bytes(actual.read_bytes() + b"changed\n")
    expected = "stale" if mutation == "stale" else "missing"
    assert bundle_module._rendered_manuscript_errors(tmp_path) == (
        f"rendered manuscript member is {expected}: {name}",
    )
    shutil.copyfile(tmp_path / "manuscript" / name, rendered / "restored-copy")
    actual.unlink(missing_ok=True)
    (rendered / "restored-copy").rename(actual)
    (rendered / "unowned.bib").write_bytes(b"unknown metadata\n")
    assert bundle_module._rendered_manuscript_errors(tmp_path) == (
        "unexpected rendered manuscript member: unowned.bib",
    )


def test_release_rejects_manuscript_sources_that_escape_through_symlinks(
    tmp_path: Path,
) -> None:
    project_root = tmp_path / "checkout"
    manuscript = project_root / "manuscript"
    rendered = project_root / "output" / "manuscript"
    manuscript.mkdir(parents=True)
    outside = tmp_path / "outside.md"
    outside.write_text("# Outside-root content\n", encoding="utf-8")
    (manuscript / "01_chapter.md").symlink_to(outside)
    (manuscript / "manuscript_vars.yaml").write_text("{}\n", encoding="utf-8")
    for source_relative, _destination in bundle_module.MANUSCRIPT_ASSETS.values():
        roster_source = project_root / source_relative
        roster_source.parent.mkdir(parents=True, exist_ok=True)
        roster_source.write_bytes(b"<fixture/>\n")
    bundle_module.render_manuscript(manuscript, rendered, {})

    errors = bundle_module._rendered_manuscript_errors(project_root)

    assert errors == (
        "manuscript source is not a canonical regular file: manuscript/01_chapter.md",
    )


@pytest.mark.parametrize(
    ("relative", "expected_error"),
    [
        ("manuscript/config.yaml", "path traverses a symlink"),
        ("manuscript/references.bib", "required regular file is missing"),
        (
            "manuscript/09z_unified_formalism_catalogue.md",
            "required regular file is missing",
        ),
        (
            "output/manuscript/assets/formalism-atlas.svg",
            "required file traverses a symlink",
        ),
        (
            "docs/formalism-atlas.svg",
            "required file traverses a symlink",
        ),
    ],
)
def test_publication_renderer_rejects_symlinked_metadata_appendix_and_resources(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    relative: str,
    expected_error: str,
) -> None:
    _minimal_manuscript(tmp_path)
    canonical = tmp_path / relative
    if relative.startswith(("output/manuscript/assets/", "docs/")):
        source = tmp_path / "manuscript/01_chapter.md"
        rendered = tmp_path / "output/manuscript/01_chapter.md"
        source.write_text("![Atlas](../docs/formalism-atlas.svg)\n", encoding="utf-8")
        rendered.write_text("![Atlas](assets/formalism-atlas.svg)\n", encoding="utf-8")
        outside = tmp_path / "outside-assets"
        outside.mkdir()
        (outside / canonical.name).write_text("<svg/>", encoding="utf-8")
        if relative.startswith("output/manuscript/assets/"):
            docs = tmp_path / "docs"
            docs.mkdir()
            (docs / "formalism-atlas.svg").write_text("<svg/>", encoding="utf-8")
            (outside / "graphical-abstract.png").write_bytes(
                (PROJ / "manuscript/assets/graphical-abstract.png").read_bytes()
            )
        if canonical.parent.exists():
            shutil.rmtree(canonical.parent)
        canonical.parent.symlink_to(outside, target_is_directory=True)
    else:
        outside = tmp_path / f"outside-{canonical.name}"
        outside.write_bytes(canonical.read_bytes())
        canonical.unlink()
        canonical.symlink_to(outside)
    monkeypatch.setattr(
        bundle_module.shutil,
        "which",
        lambda name: "/fixed/bin/pandoc" if name == "pandoc" else None,
    )
    monkeypatch.setattr(
        bundle_module,
        "_tool_identity",
        lambda _executable: {
            "name": "pandoc",
            "version": "pandoc fixture",
            "binary_sha256": "1" * 64,
        },
    )
    monkeypatch.setattr(
        bundle_module,
        "_render_twice",
        lambda _command, **_kwargs: (
            b"<html><body>fixture</body></html>",
            "reproducible",
        ),
    )

    with pytest.raises(bundle_module.ReleaseBundleError, match=expected_error):
        render_publication_manuscript(tmp_path, source_date_epoch=0)


def test_nonreproducible_pdf_is_disclosed_and_excluded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_manuscript(tmp_path)
    _fixture_renderer_tools(
        tmp_path,
        monkeypatch,
        ("pandoc", "xelatex", "xdvipdfmx", "rsvg-convert", "mutool"),
    )
    monkeypatch.setattr(
        bundle_module,
        "_render_twice",
        lambda _command, **kwargs: (
            (b"<html><body>checked</body></html>", "reproducible")
            if kwargs["suffix"] == ".html"
            else (None, "renderer_output_not_reproducible")
        ),
    )

    rendered = render_publication_manuscript(tmp_path, source_date_epoch=0)
    provenance = json.loads(rendered.provenance)

    assert rendered.pdf is None
    assert provenance["pdf"] == {
        "current": False,
        "path": "",
        "sha256": "",
        "size": 0,
        "status": "renderer_output_not_reproducible",
    }
    assert provenance["renderers"]["xelatex"]["version"] == "xelatex fixture"
    assert provenance["renderers"]["rsvg-convert"]["version"] == (
        "rsvg-convert fixture"
    )
    assert provenance["renderers"]["mutool"]["version"] == "mutool fixture"
    assert provenance["commands"]["pdf_normalization"] == [
        "mutool",
        "clean",
        "<OUTPUT.pdf>",
        "<NORMALIZED.pdf>",
        "<CANONICAL_CONTENT_DERIVED_TRAILER_ID>",
    ]


def test_controlled_renderer_path_includes_pdf_asset_converter() -> None:
    controlled = bundle_module._controlled_renderer_path(
        ("/render/bin/pandoc", "--pdf-engine=/tex/bin/xelatex"),
        auxiliary_executables=("/svg/bin/rsvg-convert", "/pdf/bin/mutool"),
    ).split(os.pathsep)

    assert controlled[:4] == [
        "/render/bin",
        "/tex/bin",
        "/svg/bin",
        "/pdf/bin",
    ]


@pytest.mark.skipif(os.name != "posix", reason="renderer group cleanup requires POSIX")
@pytest.mark.parametrize("operation", ["render", "identity"])
def test_renderer_timeout_cleans_real_child_and_grandchild(
    tmp_path: Path, operation: str
) -> None:
    ready = tmp_path / "renderer-ready.json"
    grandchild = "import time;time.sleep(8)"
    child = (
        "import json,os,subprocess,sys,time\nfrom pathlib import Path\n"
        f"process=subprocess.Popen([sys.executable,'-S','-c',{grandchild!r}])\n"
        f"path=Path({str(ready)!r})\n"
        "stage=path.with_suffix('.stage')\n"
        "stage.write_text(json.dumps([os.getpid(),process.pid]))\n"
        "stage.rename(path)\n"
        "print('render descendants ready',flush=True)\ntime.sleep(8)\n"
    )
    parent = (
        "import subprocess,sys,time\n"
        f"subprocess.Popen([sys.executable,'-S','-c',{child!r}])\n"
        "time.sleep(8)\n"
    )
    started = time.monotonic()
    expected_error = (
        "renderer exceeded its 2-second deterministic budget"
        if operation == "render"
        else "cannot identify renderer"
    )
    with pytest.raises(
        bundle_module.ReleaseBundleError,
        match=expected_error,
    ) as failure:
        if operation == "render":
            bundle_module._run_renderer(
                [sys.executable, "-S", "-c", parent],
                project_root=tmp_path,
                environment_root=tmp_path / "environment",
                epoch=0,
                timeout=2,
            )
        else:
            tool = tmp_path / "fake-render-version"
            tool.write_text(f"#!{sys.executable} -S\n{parent}")
            tool.chmod(0o700)
            bundle_module._tool_identity(str(tool), timeout=2)

    assert time.monotonic() - started < 4
    assert isinstance(failure.value.__cause__, subprocess.TimeoutExpired)
    assert b"render descendants ready" in failure.value.__cause__.stdout
    descendants = json.loads(ready.read_text())
    assert len(descendants) == 2

    def exited(pid: int) -> bool:
        result = subprocess.run(
            ["ps", "-o", "stat=", "-p", str(pid)],
            capture_output=True,
            text=True,
            check=False,
            timeout=2,
        )
        return result.returncode != 0 or result.stdout.lstrip().startswith("Z")

    cleanup_deadline = time.monotonic() + 1
    while not all(exited(pid) for pid in descendants):
        if time.monotonic() >= cleanup_deadline:
            pytest.fail("timed-out renderer descendants remain alive")
        time.sleep(0.02)


def test_pdf_renderer_uses_two_xelatex_passes_per_isolated_render(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    wrappers: list[str] = []
    drivers: list[str] = []

    def fake_renderer(
        command: object,
        *,
        project_root: Path,
        environment_root: Path,
        epoch: int,
        timeout: int,
        auxiliary_executables: object = (),
    ) -> subprocess.CompletedProcess[str]:
        del project_root, environment_root, epoch, timeout, auxiliary_executables
        argv = list(command)  # type: ignore[arg-type]
        output_arg = next(arg for arg in argv if str(arg).startswith("--output="))
        output = Path(str(output_arg).split("=", 1)[1])
        engine_arg = next(arg for arg in argv if str(arg).startswith("--pdf-engine="))
        wrapper = Path(str(engine_arg).split("=", 1)[1])
        wrapper_text = wrapper.read_text(encoding="utf-8")
        wrappers.append(wrapper_text)
        engine_command = shlex.split(wrapper_text.splitlines()[2])
        driver_argument = next(
            argument
            for argument in engine_command
            if argument.startswith("-output-driver=")
        )
        driver_command = shlex.split(driver_argument.removeprefix("-output-driver="))
        assert driver_command[0] == "/bin/sh"
        driver = Path(driver_command[1])
        drivers.append(driver.read_text(encoding="utf-8"))
        refused_output = tmp_path / "refused.pdf"
        refused = subprocess.run(
            [str(driver), "-o", str(refused_output), "unexpected"],
            capture_output=True,
            check=False,
            timeout=5,
        )
        assert refused.returncode == 64
        assert not refused_output.exists()
        output.write_bytes(
            b"%PDF-1.5\ntrailer<</ID[<"
            + b"A" * 32
            + b"><"
            + b"B" * 32
            + b">]>>\n%%EOF\n"
        )
        return subprocess.CompletedProcess(argv, 0, "", "")

    monkeypatch.setattr(bundle_module, "_run_renderer", fake_renderer)

    rendered, status = bundle_module._render_twice(
        ("/render/bin/pandoc",),
        project_root=tmp_path,
        epoch=0,
        suffix=".pdf",
        extra_args=(),
        timeout=30,
        pdf_engine="/tex/bin/xelatex",
        pdf_driver="/driver path/bin/xdvipdfmx",
    )

    assert status == "reproducible"
    assert rendered is not None
    assert len(wrappers) == 2
    assert all(wrapper.count("/tex/bin/xelatex") == 2 for wrapper in wrappers)
    assert len(drivers) == 2
    assert all("'/driver path/bin/xdvipdfmx' -q -E -o -" in body for body in drivers)


def test_native_publication_pdf_is_reproducible_across_concurrent_private_jobs(
    tmp_path: Path,
) -> None:
    if any(shutil.which(name) is None for name in ("pandoc", "xelatex", "mutool")):
        pytest.skip("complete PDF renderer toolchain is unavailable")
    _minimal_manuscript(tmp_path)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(render_publication_manuscript, tmp_path, source_date_epoch=0)
            for _ in range(2)
        ]
        results = [future.result(timeout=180) for future in futures]
    assert results[0].pdf is not None
    assert results[0].pdf == results[1].pdf
    assert results[0].provenance == results[1].provenance
    assert all(
        json.loads(result.provenance)["pdf"]["status"] == "reproducible"
        for result in results
    )


@pytest.mark.parametrize("timeout", [0, -1, float("inf"), float("nan"), True])
def test_render_budget_rejects_malformed_values_before_dispatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, timeout: float
) -> None:
    def unexpected_dispatch(*args: object, **kwargs: object) -> None:
        pytest.fail("invalid budget reached renderer dispatch")

    monkeypatch.setattr(bundle_module, "_run_renderer", unexpected_dispatch)
    with pytest.raises(bundle_module.ReleaseBundleError, match="finite and positive"):
        bundle_module._render_twice(
            ("unused",),
            project_root=tmp_path,
            epoch=0,
            suffix=".pdf",
            extra_args=(),
            timeout=timeout,
        )


@pytest.mark.skipif(os.name != "posix", reason="process groups require POSIX")
def test_renderer_timeout_reaps_parent_and_stops_pipe_holding_grandchild(
    tmp_path: Path,
) -> None:
    pid_file = tmp_path / "owned-child.pid"
    script = (
        "import subprocess, sys, time\n"
        "from pathlib import Path\n"
        "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])\n"
        "Path(sys.argv[1]).write_text(str(child.pid))\n"
        "time.sleep(60)\n"
    )
    started = time.monotonic()
    with pytest.raises(bundle_module.ReleaseBundleError, match="deterministic budget"):
        bundle_module._run_renderer(
            (sys.executable, "-c", script, str(pid_file)),
            project_root=tmp_path,
            environment_root=tmp_path / "environment",
            epoch=0,
            timeout=0.5,
        )
    assert time.monotonic() - started < 5
    assert pid_file.is_file()
    status = subprocess.run(
        ("ps", "-o", "stat=", "-p", pid_file.read_text()),
        check=False,
        capture_output=True,
        text=True,
        timeout=3,
    )
    assert not status.stdout.strip() or status.stdout.lstrip().startswith("Z")


@pytest.mark.parametrize("normalize_pdf", [False, True])
def test_two_render_passes_and_normalizer_share_one_deadline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, normalize_pdf: bool
) -> None:
    clock = [100.0]
    dispatched: list[tuple[str, ...]] = []
    monkeypatch.setattr(
        "fep_lean.output.release_bundle._manuscript.time",
        SimpleNamespace(monotonic=lambda: clock[0]),
    )

    def consume_budget(command: tuple[str, ...], **kwargs: object) -> object:
        dispatched.append(tuple(command))
        output = next(
            item.split("=", 1)[1] for item in command if item.startswith("--output=")
        )
        Path(output).write_bytes(b"complete first render")
        clock[0] += 1.0
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(bundle_module, "_run_renderer", consume_budget)
    with pytest.raises(bundle_module.ReleaseBundleError, match="deterministic budget"):
        bundle_module._render_twice(
            ("pandoc",),
            project_root=tmp_path,
            epoch=0,
            suffix=".pdf",
            extra_args=(),
            timeout=1,
            pdf_normalizer="mutool" if normalize_pdf else None,
        )
    assert len(dispatched) == 1
    assert dispatched[0][0] == "pandoc"


@pytest.mark.parametrize("late_phase", ["artifact", "normalizer", "cleanup"])
def test_completed_renderer_cannot_publish_after_artifact_or_cleanup_deadline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, late_phase: str
) -> None:
    clock = [100.0]
    monkeypatch.setattr(
        "fep_lean.output.release_bundle._manuscript.time",
        SimpleNamespace(monotonic=lambda: clock[0]),
    )
    pdf = b"%PDF-1.4\n<< /ID [<" + b"0" * 32 + b"> <" + b"F" * 32 + b">] >>\n"

    def complete_renderer(command: tuple[str, ...], **kwargs: object) -> object:
        if command[0] == "mutool":
            output = command[-1]
        else:
            output = next(
                item.split("=", 1)[1]
                for item in command
                if item.startswith("--output=")
            )
        Path(output).write_bytes(pdf)
        return SimpleNamespace(returncode=0)

    original_read = Path.read_bytes

    def delayed_artifact_read(path: Path) -> bytes:
        data = original_read(path)
        if (
            late_phase == "artifact"
            and path.name == "render-1.pdf"
            or late_phase == "normalizer"
            and path.name == "normalized.pdf"
            and path.parent.name == "environment-1"
        ):
            clock[0] += 2.0
        return data

    directory_type = bundle_module.tempfile.TemporaryDirectory

    class BudgetedDirectory(directory_type):
        def __exit__(self, *args: object) -> None:
            super().__exit__(*args)
            if late_phase == "cleanup":
                clock[0] += 2.0

    monkeypatch.setattr(
        "fep_lean.output.release_bundle._manuscript.tempfile",
        SimpleNamespace(TemporaryDirectory=BudgetedDirectory),
    )
    monkeypatch.setattr(Path, "read_bytes", delayed_artifact_read)
    monkeypatch.setattr(bundle_module, "_run_renderer", complete_renderer)
    with pytest.raises(bundle_module.ReleaseBundleError, match="deterministic budget"):
        bundle_module._render_twice(
            ("pandoc",),
            project_root=tmp_path,
            epoch=0,
            suffix=".pdf",
            extra_args=(),
            timeout=1,
            pdf_normalizer="mutool" if late_phase == "normalizer" else None,
        )


def test_publication_renderer_numbers_sections_for_resolvable_references(
    tmp_path: Path,
) -> None:
    _minimal_manuscript(tmp_path)

    command = bundle_module._pandoc_base_command(tmp_path, "/render/bin/pandoc")

    assert "--number-sections" in command


def test_pdf_identifier_normalization_removes_only_random_trailer_ids() -> None:
    prefix = b"%PDF-1.5\n1 0 obj<</Type/Catalog>>endobj\ntrailer<</Size 2/ID[<"
    suffix = b">]>>\nstartxref\n0\n%%EOF\n"
    first = prefix + b"A" * 32 + b"><" + b"B" * 32 + suffix
    second = prefix + b"C" * 32 + b"><" + b"D" * 32 + suffix

    normalized_first = bundle_module._canonical_pdf_identifier(first)
    normalized_second = bundle_module._canonical_pdf_identifier(second)

    assert normalized_first == normalized_second
    assert len(normalized_first) == len(first)
    assert b"A" * 32 not in normalized_first
    assert b"B" * 32 not in normalized_first


def test_renderer_provenance_ignores_irrelevant_ambient_path_tails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_manuscript(tmp_path)
    _fixture_renderer_tools(tmp_path, monkeypatch)
    monkeypatch.setattr(
        bundle_module,
        "_render_twice",
        lambda _command, **_kwargs: (
            b"<html><body>identical</body></html>",
            "reproducible",
        ),
    )
    monkeypatch.setenv("PATH", "/fixed/bin:/usr/bin")
    first = render_publication_manuscript(tmp_path, source_date_epoch=0)
    monkeypatch.setenv("PATH", "/fixed/bin:/usr/bin:/irrelevant-tail")
    second = render_publication_manuscript(tmp_path, source_date_epoch=0)

    assert first.html == second.html
    assert first.provenance == second.provenance


@pytest.mark.skipif(os.name != "posix", reason="actual fixture tools require POSIX")
@pytest.mark.parametrize(
    "name", ["pandoc", "xelatex", "xdvipdfmx", "rsvg-convert", "mutool"]
)
@pytest.mark.parametrize("mutation", ["bytes", "symlink_target", "disappearance"])
def test_publication_renderer_rejects_binary_changed_during_rendering(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    mutation: str,
) -> None:
    """Use actual version children; render bytes alone are a custody fixture."""
    _minimal_manuscript(tmp_path)
    tools = _fixture_renderer_tools(
        tmp_path,
        monkeypatch,
        ("pandoc", "xelatex", "xdvipdfmx", "rsvg-convert", "mutool"),
        actual_identity=True,
    )
    executable = tools[name]
    selected_target = executable
    replacement = executable.with_name(f"{name}-replacement")
    if mutation == "symlink_target":
        selected_target = executable.with_name(f"{name}-original")
        executable.rename(selected_target)
        replacement.write_bytes(selected_target.read_bytes())
        replacement.chmod(0o700)
        executable.symlink_to(selected_target.name)
        assert hashlib.sha256(selected_target.read_bytes()).digest() == (
            hashlib.sha256(replacement.read_bytes()).digest()
        )

    def mutate_binary(_command: object, **kwargs: object) -> tuple[bytes, str]:
        if kwargs["suffix"] == ".pdf":
            if mutation == "bytes":
                selected_target.write_bytes(
                    selected_target.read_bytes() + b"# persistent edit\n"
                )
            elif mutation == "symlink_target":
                executable.unlink()
                executable.symlink_to(replacement.name)
            else:
                executable.unlink()
        return b"fixture render bytes", "reproducible"

    monkeypatch.setattr(bundle_module, "_render_twice", mutate_binary)
    with pytest.raises(
        bundle_module.ReleaseBundleError,
        match="renderer binary changed during rendering",
    ):
        render_publication_manuscript(tmp_path, source_date_epoch=0)


def test_renderer_identity_missing_binary_keeps_typed_diagnostic(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from fep_lean.verification import _subprocess

    def forbidden_child(*_args: object, **_kwargs: object) -> None:
        pytest.fail("a missing binary must fail before a process launch")

    monkeypatch.setattr(_subprocess, "run_process_group", forbidden_child)
    with pytest.raises(
        bundle_module.ReleaseBundleError, match="cannot identify renderer"
    ):
        bundle_module._tool_identity(str(tmp_path / "vanished-renderer"), timeout=2)


@pytest.mark.skipif(os.name != "posix", reason="actual version fixture requires POSIX")
def test_renderer_identity_rejects_binary_removed_by_actual_version_child(
    tmp_path: Path,
) -> None:
    executable = tmp_path / "removed-renderer"
    executable.write_text(
        "#!/bin/sh\n/bin/rm -- \"$0\"\nprintf '%s\\n' 'fixture version'\n"
    )
    executable.chmod(0o700)
    with pytest.raises(
        bundle_module.ReleaseBundleError,
        match="renderer binary changed during identification",
    ):
        bundle_module._tool_identity(str(executable), timeout=2)
    assert not executable.exists()


@pytest.mark.skipif(os.name != "posix", reason="actual FIFO control requires POSIX")
def test_renderer_binary_final_read_rejects_fifo_swap_without_blocking(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_manuscript(tmp_path)
    tools = _fixture_renderer_tools(tmp_path, monkeypatch)
    executable = tools["pandoc"]
    final_read = False
    swapped = False
    real_open = os.open

    def mutate_at_open(
        path: object, flags: int, *args: object, **kwargs: object
    ) -> int:
        nonlocal swapped
        if final_read and path == executable.name and "dir_fd" in kwargs:
            executable.unlink()
            os.mkfifo(executable)
            swapped = True
        return real_open(path, flags, *args, **kwargs)  # type: ignore[arg-type]

    def finish_render(_command: object, **_kwargs: object) -> tuple[bytes, str]:
        nonlocal final_read
        final_read = True
        return b"fixture HTML", "reproducible"

    monkeypatch.setattr(os, "open", mutate_at_open)
    monkeypatch.setattr(bundle_module, "_render_twice", finish_render)
    started = time.monotonic()
    with pytest.raises(
        bundle_module.ReleaseBundleError,
        match="renderer binary changed during rendering",
    ):
        render_publication_manuscript(tmp_path, source_date_epoch=0)
    assert swapped
    assert time.monotonic() - started < 2


def test_renderer_provenance_binds_referenced_local_manuscript_figures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_manuscript(tmp_path)
    reference = "![Status](../output/figures/status_distribution.png)\n"
    (tmp_path / "manuscript/01_chapter.md").write_text(reference, encoding="utf-8")
    (tmp_path / "output/manuscript/01_chapter.md").write_text(
        reference, encoding="utf-8"
    )
    figure = tmp_path / "output/figures/status_distribution.png"
    figure.parent.mkdir(parents=True)
    figure.write_bytes(_png_bytes(8, 8))
    _fixture_renderer_tools(tmp_path, monkeypatch)
    monkeypatch.setattr(
        bundle_module,
        "_render_twice",
        lambda _command, **_kwargs: (
            b"<html><body>embedded</body></html>",
            "reproducible",
        ),
    )

    provenance = json.loads(
        render_publication_manuscript(tmp_path, source_date_epoch=0).provenance
    )

    inputs = {record["path"]: record for record in provenance["inputs"]}
    assert inputs["output/figures/status_distribution.png"]["sha256"] == (
        hashlib.sha256(figure.read_bytes()).hexdigest()
    )


def test_publication_renderer_rejects_a_resource_changed_during_rendering(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_manuscript(tmp_path)
    reference = "![Status](../output/figures/status_distribution.png)\n"
    (tmp_path / "manuscript/01_chapter.md").write_text(reference, encoding="utf-8")
    (tmp_path / "output/manuscript/01_chapter.md").write_text(
        reference, encoding="utf-8"
    )
    figure = tmp_path / "output/figures/status_distribution.png"
    figure.parent.mkdir(parents=True)
    figure.write_bytes(_png_bytes(8, 8))
    _fixture_renderer_tools(tmp_path, monkeypatch)

    def mutate_resource(_command: object, **_kwargs: object) -> tuple[bytes, str]:
        figure.write_bytes(_png_bytes(9, 8))
        return b"<html><body>embedded</body></html>", "reproducible"

    monkeypatch.setattr(bundle_module, "_render_twice", mutate_resource)

    with pytest.raises(
        bundle_module.ReleaseBundleError,
        match="manuscript renderer inputs changed during rendering",
    ):
        render_publication_manuscript(tmp_path, source_date_epoch=0)


@pytest.mark.parametrize(
    ("reference", "error"),
    [
        (
            "![Provider](../output/reports/provider-plot.png)\n",
            (
                "manuscript image reference is not release-owned: "
                "../output/reports/provider-plot.png"
            ),
        ),
        (
            "![Provider][plot]\n\n[plot]: ../output/reports/provider-plot.png\n",
            "manuscript image syntax is not release-owned",
        ),
        (
            '<img src="../output/reports/provider-plot.png">\n',
            "manuscript contains unsupported resource-bearing markup",
        ),
    ],
)
def test_renderer_rejects_unowned_or_provider_manuscript_image_targets(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    reference: str,
    error: str,
) -> None:
    _minimal_manuscript(tmp_path)
    (tmp_path / "manuscript/01_chapter.md").write_text(reference, encoding="utf-8")
    (tmp_path / "output/manuscript/01_chapter.md").write_text(
        reference, encoding="utf-8"
    )
    provider = tmp_path / "output/reports/provider-plot.png"
    provider.parent.mkdir(parents=True)
    provider.write_bytes(_png_bytes(8, 8))
    monkeypatch.setattr(
        bundle_module.shutil,
        "which",
        lambda name: "/fixed/bin/pandoc" if name == "pandoc" else None,
    )
    monkeypatch.setattr(
        bundle_module,
        "_tool_identity",
        lambda _executable: {
            "name": "pandoc",
            "version": "pandoc fixed",
            "binary_sha256": "0" * 63 + "1",
        },
    )
    monkeypatch.setattr(
        bundle_module,
        "_render_twice",
        lambda _command, **_kwargs: (
            b"<html><body>provider bytes embedded</body></html>",
            "reproducible",
        ),
    )

    with pytest.raises(bundle_module.ReleaseBundleError, match=error):
        render_publication_manuscript(tmp_path, source_date_epoch=0)


def test_browser_receipt_is_bound_to_canonical_projections_and_screenshots(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    chrome = tmp_path / "google-chrome"
    chrome.write_bytes(b"canonical Chrome fixture\n")
    chrome_digest = hashlib.sha256(chrome.read_bytes()).hexdigest()
    decoy = tmp_path / "google-chrome-decoy"
    decoy.write_bytes(b"different Chrome fixture\n")
    monkeypatch.setattr(
        bundle_module.shutil,
        "which",
        lambda name: str(decoy) if name == "google-chrome" else None,
    )
    monkeypatch.setattr(
        bundle_module.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(
            returncode=0,
            stdout="Google Chrome 151.0.7922.169\n",
            stderr="",
        ),
    )
    projection_records: dict[str, dict[str, str]] = {}
    for key, relative in bundle_module._CANONICAL_BROWSER_PROJECTIONS.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"{key}\n", encoding="utf-8")
        projection_records[key] = {
            "path": relative,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
    screenshot_records: list[dict[str, object]] = []
    for (
        role,
        screenshot_relative,
    ) in bundle_module._CANONICAL_BROWSER_SCREENSHOTS.items():
        if role.endswith("_mobile"):
            width, height = 390, 844
        elif role.endswith("_desktop"):
            width, height = 1440, 900
        else:
            width, height = 1600, 1000
        screenshot = tmp_path / screenshot_relative
        screenshot.parent.mkdir(parents=True, exist_ok=True)
        screenshot.write_bytes(_png_bytes(width, height))
        screenshot_records.append(
            {
                "role": role,
                "path": screenshot_relative,
                "sha256": hashlib.sha256(screenshot.read_bytes()).hexdigest(),
                "width": width,
                "height": height,
            }
        )
    expected = {
        "topics": 168,
        "families": 22,
        "witnesses": 17,
        "relations": 146,
        "capabilities": 50,
        "external_requests": [],
        "atlas": {
            "areas": 5,
            "bodyFitsViewport": True,
            "detailSections": 4,
            "detailsInitiallyOpen": 0,
            "escapeCleared": True,
            "families": 22,
            "fepVisible": 41,
            "pairingVisible": 118,
            "relationCards": 146,
            "relations": 146,
            "searchVisible": 1,
            "slashFocused": True,
            "topics": 168,
        },
        "atlas_mobile": {
            "areas": 5,
            "bodyFitsViewport": True,
            "desktopSummaryHidden": True,
            "detailSections": 4,
            "detailsInitiallyOpen": 0,
            "families": 22,
            "mobileSummaryVisible": True,
            "relationCards": 146,
            "topics": 168,
        },
        "dashboard": {
            "acceptedVisible": 17,
            "accessibleTables": 17,
            "bodyFitsViewport": True,
            "detailJumps": 17,
            "detailRecords": 17,
            "detailsInitiallyOpen": 0,
            "escapeCleared": True,
            "exactScrollRegions": 51,
            "familyVisible": 1,
            "filterOpened": 1,
            "jumpFocused": True,
            "jumpOpened": True,
            "overviewHiddenByFilter": True,
            "searchVisible": 1,
            "slashFocused": True,
            "structuralAnalogues": 1,
            "theoremInstances": 16,
            "witnesses": 17,
        },
        "dashboard_mobile": {
            "bodyFitsViewport": True,
            "compactDefaultHeight": True,
            "desktopOverviewHidden": True,
            "detailJumps": 17,
            "detailRecords": 17,
            "detailsInitiallyOpen": 0,
            "exactScrollRegions": 51,
            "filterOpened": 1,
            "jumpFocused": True,
            "jumpOpened": True,
            "mobileOverviewInitiallyOpen": False,
            "mobileOverviewDisclosureVisible": True,
            "overviewHiddenByFilter": True,
            "plotSummaries": 17,
            "recordCollectionInitiallyOpen": False,
            "witnesses": 17,
        },
    }
    capture_provenance = {
        "command": "uv run python scripts/capture_browser_acceptance.py",
        "owner": "src/fep_lean/output/browser_capture.py",
        "owner_sha256": "b" * 64,
        "protocol": "Chrome DevTools Protocol",
        "wrapper": "scripts/capture_browser_acceptance.py",
        "wrapper_sha256": "c" * 64,
    }
    render_configuration = bundle_module.canonical_browser_render_configuration()
    render_environment = {
        "browser_locale": "en-US",
        "device_pixel_ratio": "1",
        "platform": "Linux x86_64",
        "timezone": "UTC",
        "webgl_renderer": "SwiftShader fixture",
        "webgl_vendor": "Google Inc. fixture",
    }
    receipt = {
        "schema_version": 4,
        "kind": "browser-interaction",
        "accepted": True,
        "browser": {
            "name": "Google Chrome",
            "version": "151.0.7922.169",
            "executable_path": str(chrome.resolve()),
            "executable_sha256": chrome_digest,
        },
        "render_configuration": dict(render_configuration),
        "render_environment": dict(render_environment),
        "capture": dict(capture_provenance),
        "projections": projection_records,
        "screenshots": screenshot_records,
        "interactions": {
            key: True for key in bundle_module._REQUIRED_BROWSER_INTERACTIONS
        },
        "observed": expected,
        "expected": expected,
    }
    receipt_path = tmp_path / bundle_module.BROWSER_RECEIPT
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    monkeypatch.setattr(
        bundle_module,
        "build_formalism_presentation",
        lambda _root: SimpleNamespace(
            topics=(None,) * 168,
            families=(None,) * 22,
            witnesses=(None,) * 17,
            relations=(None,) * 146,
            capabilities=(None,) * 50,
        ),
    )
    captured_screenshots = {
        record["role"]: (tmp_path / str(record["path"])).read_bytes()
        for record in screenshot_records
    }
    replay = SimpleNamespace(
        browser=receipt["browser"],
        render_configuration=render_configuration,
        render_environment=render_environment,
        observations=expected,
        interactions=receipt["interactions"],
        screenshot_bytes=captured_screenshots,
    )
    replay_calls: list[tuple[Path, str | None, Path | None]] = []

    def replay_exact_browser(
        project_root: Path,
        *,
        browser_name: str | None = None,
        executable: Path | None = None,
    ) -> SimpleNamespace:
        replay_calls.append((project_root, browser_name, executable))
        return replay

    monkeypatch.setattr(
        bundle_module, "replay_browser_acceptance", replay_exact_browser
    )
    monkeypatch.setattr(
        bundle_module,
        "canonical_browser_capture_provenance",
        lambda _root: capture_provenance,
    )

    static_snapshot = {
        path: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in tmp_path.rglob("*")
        if path.is_file()
    }

    def forbidden_browser_execution(*_args: object, **_kwargs: object) -> None:
        pytest.fail("static browser validation started a browser process")

    with monkeypatch.context() as static_patch:
        static_patch.setattr(subprocess, "run", forbidden_browser_execution)
        static_patch.setattr(
            bundle_module, "replay_browser_acceptance", forbidden_browser_execution
        )
        assert (
            bundle_module._browser_receipt_errors(tmp_path, check_runtime=False) == ()
        )
    assert replay_calls == []
    assert static_snapshot == {
        path: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in tmp_path.rglob("*")
        if path.is_file()
    }

    assert bundle_module._browser_receipt_errors(tmp_path) == ()
    assert replay_calls[-1] == (tmp_path.resolve(), "Google Chrome", chrome.resolve())

    receipt["browser"]["executable_path"] = str(decoy.resolve())
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    assert "browser executable hash differs from the live browser binary" in (
        bundle_module._browser_receipt_errors(tmp_path)
    )
    receipt["browser"]["executable_path"] = str(chrome.resolve())
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

    replay.render_configuration = {
        **render_configuration,
        "gpu": "enabled",
    }
    assert "browser render configuration differs from live Chrome replay" in (
        bundle_module._browser_receipt_errors(tmp_path)
    )
    replay.render_configuration = render_configuration

    receipt["capture"]["owner_sha256"] = "0" * 64
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    assert "browser capture provenance is not canonical" in (
        bundle_module._browser_receipt_errors(tmp_path)
    )
    receipt["capture"]["owner_sha256"] = "b" * 64
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

    replay.browser = {**receipt["browser"], "version": "151.0.7922.170"}
    assert "browser receipt identity differs from live Chrome replay" in (
        bundle_module._browser_receipt_errors(tmp_path)
    )
    replay.browser = receipt["browser"]

    receipt["render_environment"]["timezone"] = "America/Los_Angeles"
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    assert "browser render environment is not canonical" in (
        bundle_module._browser_receipt_errors(tmp_path)
    )
    receipt["render_environment"] = dict(render_environment)
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

    replay.render_environment = {**render_environment, "gpu": "enabled"}
    assert "browser render environment differs from live Chrome replay" in (
        bundle_module._browser_receipt_errors(tmp_path)
    )
    replay.render_environment = render_environment

    replay.observations = {
        **expected,
        "external_requests": ["https://unexpected.invalid/asset.css"],
    }
    assert "browser receipt observations differ from live Chrome replay" in (
        bundle_module._browser_receipt_errors(tmp_path)
    )
    replay.observations = expected

    replay.screenshot_bytes = {
        **captured_screenshots,
        "atlas_desktop": b"different live Chrome pixels",
    }
    assert (
        "browser screenshot differs from live Chrome capture: "
        "specs/done/formalism-catalogue-155/assets/atlas-155-desktop.png"
        in bundle_module._browser_receipt_errors(tmp_path)
    )
    replay.screenshot_bytes = captured_screenshots

    del expected["atlas"]["slashFocused"]
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    assert "browser receipt detailed DOM observations are not canonical" in (
        bundle_module._browser_receipt_errors(tmp_path)
    )
    expected["atlas"]["slashFocused"] = True
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

    receipt["browser"]["executable_sha256"] = "0" * 64
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    assert "browser executable hash cannot be the all-zero sentinel" in (
        bundle_module._browser_receipt_errors(tmp_path)
    )
    receipt["browser"]["executable_sha256"] = chrome_digest
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

    first = receipt["screenshots"][0]
    invalid_png = tmp_path / str(first["path"])
    invalid_png.write_bytes(b"not a png")
    first["sha256"] = hashlib.sha256(invalid_png.read_bytes()).hexdigest()
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    assert "browser screenshot is not a PNG stream" in (
        bundle_module._browser_receipt_errors(tmp_path)
    )

    (tmp_path / "docs/formalism-atlas.html").write_text("tampered\n", encoding="utf-8")
    assert (
        "browser receipt projection hash is stale: atlas_html"
        in bundle_module._browser_receipt_errors(tmp_path)
    )


def test_release_rejects_an_unsupported_receipt_browser_product(tmp_path: Path) -> None:
    executable = tmp_path / "brave-like"
    executable.write_text(
        '#!/bin/sh\nprintf "Brave Browser 123.4.5.6\\n"\n',
        encoding="utf-8",
    )
    executable.chmod(0o755)

    with pytest.raises(
        bundle_module.ReleaseBundleError,
        match="supported Chrome or Chromium product",
    ):
        bundle_module._live_browser_identity("Chromium", executable)


def test_numerical_receipt_preserves_every_typed_check_and_evidence_boundary() -> None:
    project_root = Path(__file__).resolve().parents[1]

    payload = json.loads(build_numerical_witness_receipt(project_root))

    assert payload["kind"] == "numerical-witness-receipt"
    assert payload["complete"] is True
    assert payload["witness_count"] == 17
    assert payload["check_count"] == sum(
        len(witness["checks"]) for witness in payload["witnesses"]
    )
    assert all(witness["accepted"] is True for witness in payload["witnesses"])
    assert all(
        check["accepted"] is True
        for witness in payload["witnesses"]
        for check in witness["checks"]
    )
    assert all(
        witness["evidence_kind"] == payload["evidence_kind"]
        for witness in payload["witnesses"]
    )
    assert len(payload["source_sha256"]) == len(payload["config_sha256"]) == 64


def test_python_receipts_bind_full_roster_and_coverage_floor(tmp_path: Path) -> None:
    output = tmp_path / "output"
    manuscript = tmp_path / "manuscript"
    output.mkdir()
    manuscript.mkdir()
    test_root = tmp_path / "tests"
    test_root.mkdir()
    source = tmp_path / "src/fep_lean"
    source.mkdir(parents=True)
    (source / "a.py").write_text(
        "\n".join(f"value_{index} = {index}" for index in range(1, 11)) + "\n",
        encoding="utf-8",
    )
    (test_root / "test_fixture.py").write_text(
        "def test_fixture():\n    assert True\n", encoding="utf-8"
    )
    (manuscript / "manuscript_vars.yaml").write_text(
        "tests:\n  collected: 3\n", encoding="utf-8"
    )

    def junit_xml(*, tests: int, skipped: int) -> str:
        cases = []
        for index in range(tests):
            outcome = '<skipped message="fixture"/>' if index < skipped else ""
            cases.append(
                f'<testcase classname="tests.test_fixture" name="test_{index}" '
                f'time="0">{outcome}</testcase>'
            )
        return (
            f'<testsuites><testsuite tests="{tests}" failures="0" errors="0" '
            f'skipped="{skipped}" time="0">{"".join(cases)}'
            "</testsuite></testsuites>\n"
        )

    def coverage_xml(*, covered: int) -> str:
        lines = "".join(
            f'<line number="{number}" hits="{int(number <= covered)}"/>'
            for number in range(1, 11)
        )
        return (
            f'<coverage line-rate="{covered / 10:.4f}" lines-valid="10" '
            f'lines-covered="{covered}"><packages><package><classes>'
            '<class filename="fep_lean/a.py"><lines>'
            f"{lines}</lines></class></classes></package></packages></coverage>\n"
        )

    (output / "pytest.xml").write_text(
        junit_xml(tests=3, skipped=1),
        encoding="utf-8",
    )
    coverage = output / "coverage.xml"
    coverage.write_text(coverage_xml(covered=9), encoding="utf-8")

    assert bundle_module._pytest_receipt_errors(tmp_path) == ()

    coverage.write_text(coverage_xml(covered=8), encoding="utf-8")
    assert "Python coverage line-rate 0.8000 is below 0.8900" in (
        bundle_module._pytest_receipt_errors(tmp_path)
    )

    coverage.write_text(coverage_xml(covered=9), encoding="utf-8")
    (output / "pytest.xml").write_text(
        junit_xml(tests=2, skipped=0),
        encoding="utf-8",
    )
    assert (
        "Python test receipt count differs from the canonical test roster: "
        "receipt=2, canonical=3" in bundle_module._pytest_receipt_errors(tmp_path)
    )

    (output / "pytest.xml").write_text(
        junit_xml(tests=3, skipped=3),
        encoding="utf-8",
    )
    assert "Python test receipt contains no executed tests" in (
        bundle_module._pytest_receipt_errors(tmp_path)
    )


def test_python_receipts_require_actual_testcase_and_coverage_line_records(
    tmp_path: Path,
) -> None:
    output = tmp_path / "output"
    manuscript = tmp_path / "manuscript"
    output.mkdir()
    manuscript.mkdir()
    (manuscript / "manuscript_vars.yaml").write_text(
        "tests:\n  collected: 1\n", encoding="utf-8"
    )
    (output / "pytest.xml").write_text(
        '<testsuites><testsuite tests="1" failures="0" errors="0" '
        'skipped="0" time="0"/></testsuites>\n',
        encoding="utf-8",
    )
    (output / "coverage.xml").write_text(
        '<coverage line-rate="0.9" lines-valid="10" lines-covered="9"/>\n',
        encoding="utf-8",
    )

    errors = bundle_module._pytest_receipt_errors(tmp_path)

    assert "Python test receipt testcase records disagree with suite counters" in errors
    assert "Python coverage receipt contains no executable line records" in errors


def test_python_receipts_aggregate_invalid_junit_and_coverage_records(
    tmp_path: Path,
) -> None:
    output = tmp_path / "output"
    manuscript = tmp_path / "manuscript"
    output.mkdir()
    manuscript.mkdir()
    (manuscript / "manuscript_vars.yaml").write_text(
        "tests:\n  collected: 0\n", encoding="utf-8"
    )
    (output / "pytest.xml").write_text(
        '<testsuite tests="1" failures="1" errors="1" skipped="1" time="0">'
        '<testcase time="not-a-number"><failure/><error/></testcase>'
        "</testsuite>\n",
        encoding="utf-8",
    )
    (output / "coverage.xml").write_text(
        '<notcoverage line-rate="nan" lines-valid="1" lines-covered="2">'
        '<class filename="../escape.py"><line number="bad" hits="bad"/></class>'
        "</notcoverage>\n",
        encoding="utf-8",
    )

    errors = bundle_module._pytest_receipt_errors(tmp_path)

    assert {
        "Python test receipt is not green: failures=1, errors=1",
        "Python test receipt testcase records disagree with suite counters",
        "Python test receipt contains an invalid testcase",
        "canonical collected-test count must be positive",
        "Python coverage receipt root must be coverage",
        "Python coverage line-rate must be finite in [0, 1]",
        "Python coverage line counters are invalid",
        "Python coverage receipt contains an invalid line record",
        "canonical Python source tree is missing or a symlink",
    } <= set(errors)


def test_python_receipts_bind_the_exact_collected_node_id_roster(
    tmp_path: Path,
) -> None:
    output = tmp_path / "output"
    manuscript = tmp_path / "manuscript"
    source = tmp_path / "src/fep_lean"
    output.mkdir()
    manuscript.mkdir()
    source.mkdir(parents=True)
    (source / "a.py").write_text("value = 1\n", encoding="utf-8")
    (manuscript / "manuscript_vars.yaml").write_text(
        "tests:\n  collected: 1\n", encoding="utf-8"
    )
    (output / "pytest.xml").write_text(
        '<testsuite tests="1" failures="0" errors="0" skipped="0" time="0">'
        '<testcase classname="tests.test_fixture" name="test_invented" time="0"/>'
        "</testsuite>\n",
        encoding="utf-8",
    )
    (output / "coverage.xml").write_text(
        '<coverage line-rate="1" lines-valid="1" lines-covered="1">'
        '<packages><package><classes><class filename="fep_lean/a.py">'
        '<lines><line number="1" hits="1"/></lines></class></classes>'
        "</package></packages></coverage>\n",
        encoding="utf-8",
    )

    errors = bundle_module._pytest_receipt_errors(
        tmp_path,
        expected_node_ids=("tests/test_fixture.py::test_fixture",),
    )

    assert (
        "Python test receipt testcase roster differs from collected node IDs" in errors
    )


def test_junit_identity_preserves_scope_delimiters_inside_parameter_ids() -> None:
    node_id = (
        "tests/test_topic.py::TestCatalogue::test_body"
        "[fep-073-theorem x : xs = y :: ys]"
    )

    assert bundle_module._junit_identity_from_node_id(node_id) == (
        "tests.test_topic.TestCatalogue",
        "test_body[fep-073-theorem x : xs = y :: ys]",
    )


def test_python_receipts_reject_noncanonical_coverage_source_records(
    tmp_path: Path,
) -> None:
    output = tmp_path / "output"
    manuscript = tmp_path / "manuscript"
    source = tmp_path / "src/fep_lean"
    output.mkdir()
    manuscript.mkdir()
    source.mkdir(parents=True)
    (source / "real.py").write_text("value = 1\n", encoding="utf-8")
    (manuscript / "manuscript_vars.yaml").write_text(
        "tests:\n  collected: 1\n", encoding="utf-8"
    )
    (output / "pytest.xml").write_text(
        '<testsuite tests="1" failures="0" errors="0" skipped="0" time="0">'
        '<testcase classname="tests.test_fixture" name="test_fixture" time="0"/>'
        "</testsuite>\n",
        encoding="utf-8",
    )
    (output / "coverage.xml").write_text(
        '<coverage line-rate="1" lines-valid="1" lines-covered="1">'
        '<packages><package><classes><class filename="fep_lean/invented.py">'
        '<lines><line number="1" hits="1"/></lines></class></classes>'
        "</package></packages></coverage>\n",
        encoding="utf-8",
    )

    errors = bundle_module._pytest_receipt_errors(tmp_path)

    assert (
        "Python coverage source roster differs from canonical Python sources" in errors
    )


def test_python_coverage_floor_uses_exact_line_counters_not_rounded_rate(
    tmp_path: Path,
) -> None:
    output = tmp_path / "output"
    manuscript = tmp_path / "manuscript"
    output.mkdir()
    manuscript.mkdir()
    (manuscript / "manuscript_vars.yaml").write_text(
        "tests:\n  collected: 1\n", encoding="utf-8"
    )
    (output / "pytest.xml").write_text(
        '<testsuite tests="1" failures="0" errors="0" skipped="0" time="0">'
        '<testcase classname="tests.test_fixture" name="test_fixture" time="0"/>'
        "</testsuite>\n",
        encoding="utf-8",
    )
    lines_valid = 10_001
    lines_covered = 8_900
    lines = "".join(
        f'<line number="{number}" hits="{int(number <= lines_covered)}"/>'
        for number in range(1, lines_valid + 1)
    )
    (output / "coverage.xml").write_text(
        '<coverage line-rate="0.8900" lines-valid="10001" '
        'lines-covered="8900"><packages><package><classes>'
        '<class filename="fep_lean/a.py"><lines>'
        f"{lines}</lines></class></classes></package></packages></coverage>\n",
        encoding="utf-8",
    )

    errors = bundle_module._pytest_receipt_errors(tmp_path)

    assert "Python coverage counter-derived line-rate is below 0.8900" in errors


def test_python_acceptance_is_emitted_only_by_the_exact_stable_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "output"
    manuscript = tmp_path / "manuscript"
    tests = tmp_path / "tests"
    output.mkdir()
    manuscript.mkdir()
    tests.mkdir()
    source = tmp_path / "src/fep_lean"
    source.mkdir(parents=True)
    (source / "a.py").write_text("value = 1\n", encoding="utf-8")
    test_source = tests / "test_fixture.py"
    test_source.write_text("def test_fixture():\n    assert True\n", encoding="utf-8")
    (manuscript / "manuscript_vars.yaml").write_text(
        "tests:\n  collected: 1\n", encoding="utf-8"
    )
    monkeypatch.setattr(bundle_module, "report_source_digest", lambda _root: "1" * 64)
    monkeypatch.setattr(bundle_module, "report_config_digest", lambda _root: "2" * 64)
    observed_runs: list[tuple[list[str], Mapping[str, str]]] = []
    tool_bin_links: list[str] = []

    def completed_run(command: list[str], **kwargs: object) -> SimpleNamespace:
        environment = kwargs["env"]
        assert isinstance(environment, dict)
        assert all(
            isinstance(key, str) and isinstance(value, str)
            for key, value in environment.items()
        )
        observed_runs.append((command, environment))
        if "--collect-only" in command:
            return SimpleNamespace(
                returncode=0,
                stdout=(
                    "tests/test_fixture.py::test_fixture\n1 test collected in 0.01s\n"
                ),
                stderr="",
            )
        run_root = Path(environment["COVERAGE_FILE"]).parent
        tool_bin_links.extend(
            link.name for link in (run_root / "acceptance-tool-bin").iterdir()
        )
        (output / "pytest.xml").write_text(
            '<testsuites><testsuite tests="1" failures="0" errors="0" '
            'skipped="0" time="0.1"><testcase classname="tests.test_fixture" '
            'name="test_fixture" time="0.1"/></testsuite></testsuites>\n',
            encoding="utf-8",
        )
        (output / "coverage.xml").write_text(
            '<coverage line-rate="1" lines-valid="1" lines-covered="1">'
            '<packages><package><classes><class filename="fep_lean/a.py">'
            '<lines><line number="1" hits="1"/></lines></class></classes>'
            "</package></packages></coverage>\n",
            encoding="utf-8",
        )
        return SimpleNamespace(returncode=0, stdout="passed", stderr="")

    monkeypatch.setattr(subprocess, "run", completed_run)

    receipt_path = bundle_module.run_python_acceptance(tmp_path)
    receipt = json.loads(receipt_path.read_bytes())

    assert len(observed_runs) == 3
    assert "--collect-only" in observed_runs[0][0]
    assert "--collect-only" not in observed_runs[1][0]
    assert "--collect-only" in observed_runs[2][0]
    assert all(
        environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] == "1"
        for _command, environment in observed_runs
    )
    assert receipt["schema_version"] == 3
    assert receipt["collection"]["node_ids"] == ["tests/test_fixture.py::test_fixture"]
    assert len(receipt["executor"]["interpreter"]["executable_sha256"]) == 64
    assert "pytest-cov" in receipt["executor"]["plugin_distributions"]
    assert len(receipt["executor"]["external_executables"]["uv"]["sha256"]) == 64
    assert sorted(tool_bin_links) == ["fc-list", "git"]
    tool_bin = Path(observed_runs[1][1]["COVERAGE_FILE"]).parent / (
        "acceptance-tool-bin"
    )
    for _command, environment in observed_runs:
        if "--collect-only" in _command:
            continue
        assert environment["PATH"] == receipt["executor"]["environment"][
            "PATH"
        ].replace("<temporary>", str(tool_bin.parent))
        assert environment["PATH"].split(os.pathsep)[2] == str(tool_bin)
    assert set(receipt["executor"]["external_executables"]) == {
        "fc-list",
        "git",
        "uv",
    }
    assert receipt["coverage"]["source_records"] == [
        {
            "lines": [{"hits": 1, "number": 1}],
            "path": "src/fep_lean/a.py",
            "source_sha256": hashlib.sha256(b"value = 1\n").hexdigest(),
        }
    ]
    assert receipt["inputs"]["before"] == receipt["inputs"]["after"]
    assert receipt["inputs"]["stable"] is True
    assert receipt["tests"]["passed"] == 1
    assert receipt["coverage"]["line_rate"] == 1.0
    assert bundle_module.build_python_acceptance_receipt(tmp_path) == (
        receipt_path.read_bytes()
    )

    static_snapshot = {
        path: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in tmp_path.rglob("*")
        if path.is_file()
    }

    def forbidden_collection(*_args: object, **_kwargs: object) -> None:
        pytest.fail("static Python validation started collection")

    with monkeypatch.context() as static_patch:
        static_patch.setattr(subprocess, "run", forbidden_collection)
        static_patch.setattr(
            bundle_module, "_collect_python_node_ids", forbidden_collection
        )
        assert (
            bundle_module._python_acceptance_receipt_errors(
                tmp_path, check_runtime=False
            )
            == ()
        )
        receipt["collection"]["node_ids"] = [
            "tests/test_fixture.py::test_fixture",
            "tests/test_fixture.py::test_fixture",
        ]
        receipt_path.write_bytes(bundle_module._canonical_json(receipt))
        assert "Python acceptance receipt collected node IDs are invalid" in (
            bundle_module._python_acceptance_receipt_errors(
                tmp_path, check_runtime=False
            )
        )
        receipt["collection"]["node_ids"] = ["tests/test_fixture.py::test_invented"]
        receipt_path.write_bytes(bundle_module._canonical_json(receipt))
        assert (
            "Python test receipt testcase roster differs from collected node IDs"
            in bundle_module._python_acceptance_receipt_errors(
                tmp_path, check_runtime=False
            )
        )
    receipt["collection"]["node_ids"] = ["tests/test_fixture.py::test_fixture"]
    receipt_path.write_bytes(bundle_module._canonical_json(receipt))
    # The deliberately mutated receipt is restored; all other inputs and evidence
    # must retain the exact bytes and mtimes across both static checks.
    assert {
        path: state for path, state in static_snapshot.items() if path != receipt_path
    } == {
        path: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in tmp_path.rglob("*")
        if path.is_file() and path != receipt_path
    }

    receipt["collection"]["node_ids"] = ["tests/test_fixture.py::test_invented"]
    receipt_path.write_bytes(bundle_module._canonical_json(receipt))
    with pytest.raises(
        bundle_module.ReleaseBundleError,
        match="Python acceptance receipt collected node IDs are stale",
    ):
        bundle_module.build_python_acceptance_receipt(tmp_path)
    receipt["collection"]["node_ids"] = ["tests/test_fixture.py::test_fixture"]
    receipt_path.write_bytes(bundle_module._canonical_json(receipt))

    test_source.write_text("def test_fixture():\n    assert False\n", encoding="utf-8")
    with pytest.raises(
        bundle_module.ReleaseBundleError,
        match="Python acceptance receipt input snapshot is stale",
    ):
        bundle_module.build_python_acceptance_receipt(tmp_path)


@pytest.mark.parametrize("mutation", ["test_tree", "test_count_owner", "executor"])
def test_python_acceptance_rolls_back_when_inputs_or_executor_change_during_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    output = tmp_path / "output"
    manuscript = tmp_path / "manuscript"
    tests = tmp_path / "tests"
    output.mkdir()
    manuscript.mkdir()
    tests.mkdir()
    source = tmp_path / "src/fep_lean"
    source.mkdir(parents=True)
    (source / "a.py").write_text("value = 1\n", encoding="utf-8")
    test_source = tests / "test_fixture.py"
    test_source.write_text("def test_fixture():\n    assert True\n", encoding="utf-8")
    test_count_owner = manuscript / "manuscript_vars.yaml"
    test_count_owner.write_text(
        f"tests:\n  collected: {2 if mutation == 'test_count_owner' else 1}\n",
        encoding="utf-8",
    )
    prior = {
        output / "pytest.xml": b"prior junit\n",
        output / "coverage.xml": b"prior coverage\n",
        output / "python-acceptance.json": b"prior acceptance\n",
    }
    for path, data in prior.items():
        path.write_bytes(data)
    monkeypatch.setattr(bundle_module, "report_source_digest", lambda _root: "1" * 64)
    monkeypatch.setattr(bundle_module, "report_config_digest", lambda _root: "2" * 64)
    if mutation == "executor":
        executor_calls = 0
        stable_executor = bundle_module._python_acceptance_runtime_identity()

        def changing_executor() -> dict[str, object]:
            nonlocal executor_calls
            executor_calls += 1
            return {
                **stable_executor,
                "fingerprint_sha256": ("1" * 64 if executor_calls == 1 else "2" * 64),
            }

        monkeypatch.setattr(
            bundle_module,
            "_python_acceptance_runtime_identity",
            changing_executor,
        )

    def changing_run(command: list[str], **_kwargs: object) -> SimpleNamespace:
        if "--collect-only" in command:
            return SimpleNamespace(
                returncode=0,
                stdout=(
                    "tests/test_fixture.py::test_fixture\n1 test collected in 0.01s\n"
                ),
                stderr="",
            )
        (output / "pytest.xml").write_text(
            '<testsuite tests="1" failures="0" errors="0" skipped="0" '
            'time="0"><testcase classname="tests.test_fixture" '
            'name="test_fixture" time="0"/></testsuite>\n',
            encoding="utf-8",
        )
        (output / "coverage.xml").write_text(
            '<coverage line-rate="1" lines-valid="1" lines-covered="1">'
            '<packages><package><classes><class filename="fep_lean/a.py">'
            '<lines><line number="1" hits="1"/></lines></class></classes>'
            "</package></packages></coverage>\n",
            encoding="utf-8",
        )
        if mutation == "test_tree":
            test_source.write_text(
                "def test_fixture():\n    assert False\n", encoding="utf-8"
            )
        elif mutation == "test_count_owner":
            test_count_owner.write_text("tests:\n  collected: 1\n", encoding="utf-8")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", changing_run)

    with pytest.raises(
        bundle_module.ReleaseBundleError,
        match=(
            "executor changed during acceptance"
            if mutation == "executor"
            else "changed during acceptance"
        ),
    ):
        bundle_module.run_python_acceptance(tmp_path)

    assert {path: path.read_bytes() for path in prior} == prior


def test_python_acceptance_rolls_back_after_an_interrupted_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "output"
    manuscript = tmp_path / "manuscript"
    tests = tmp_path / "tests"
    output.mkdir()
    manuscript.mkdir()
    tests.mkdir()
    (tests / "test_fixture.py").write_text(
        "def test_fixture():\n    assert True\n", encoding="utf-8"
    )
    (manuscript / "manuscript_vars.yaml").write_text(
        "tests:\n  collected: 1\n", encoding="utf-8"
    )
    prior = {
        output / "pytest.xml": b"prior junit\n",
        output / "coverage.xml": b"prior coverage\n",
        output / "python-acceptance.json": b"prior acceptance\n",
    }
    for path, data in prior.items():
        path.write_bytes(data)
    monkeypatch.setattr(bundle_module, "report_source_digest", lambda _root: "1" * 64)
    monkeypatch.setattr(bundle_module, "report_config_digest", lambda _root: "2" * 64)

    def interrupted_run(command: list[str], **_kwargs: object) -> SimpleNamespace:
        if "--collect-only" in command:
            return SimpleNamespace(
                returncode=0,
                stdout=(
                    "tests/test_fixture.py::test_fixture\n1 test collected in 0.01s\n"
                ),
                stderr="",
            )
        (output / "pytest.xml").write_bytes(b"partial junit\n")
        (output / "coverage.xml").write_bytes(b"partial coverage\n")
        raise KeyboardInterrupt

    monkeypatch.setattr(subprocess, "run", interrupted_run)

    with pytest.raises(KeyboardInterrupt):
        bundle_module.run_python_acceptance(tmp_path)

    assert {path: path.read_bytes() for path in prior} == prior


def test_python_acceptance_failure_removes_partial_new_receipts_and_restores_prior(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "output"
    manuscript = tmp_path / "manuscript"
    tests = tmp_path / "tests"
    output.mkdir()
    manuscript.mkdir()
    tests.mkdir()
    (tests / "test_fixture.py").write_text(
        "def test_fixture():\n    assert True\n", encoding="utf-8"
    )
    (manuscript / "manuscript_vars.yaml").write_text(
        "tests:\n  collected: 1\n", encoding="utf-8"
    )
    acceptance = output / bundle_module.PYTHON_ACCEPTANCE_RECEIPT.name
    acceptance.write_bytes(b"prior acceptance\n")
    junit = output / bundle_module.PYTEST_RECEIPT.name
    coverage = output / bundle_module.PYTHON_COVERAGE_RECEIPT.name
    monkeypatch.setattr(bundle_module, "report_source_digest", lambda _root: "1" * 64)
    monkeypatch.setattr(bundle_module, "report_config_digest", lambda _root: "2" * 64)
    monkeypatch.setattr(
        bundle_module,
        "_python_acceptance_runtime_identity",
        lambda: {"fingerprint_sha256": "3" * 64},
    )
    monkeypatch.setattr(
        bundle_module,
        "collection_runtime_identity",
        lambda: {"pytest_arguments": []},
    )
    monkeypatch.setattr(
        bundle_module,
        "_python_acceptance_environment",
        lambda _temporary_root: {},
    )

    def failed_run(command: list[str], **_kwargs: object) -> SimpleNamespace:
        if "--collect-only" in command:
            return SimpleNamespace(
                returncode=0,
                stdout="tests/test_fixture.py::test_fixture\n1 test collected in 0.01s\n",
                stderr="",
            )
        junit.write_bytes(b"partial junit\n")
        coverage.write_bytes(b"partial coverage\n")
        return SimpleNamespace(returncode=3, stdout="", stderr="suite failed")

    monkeypatch.setattr(subprocess, "run", failed_run)

    with pytest.raises(
        bundle_module.ReleaseBundleError,
        match="canonical Python acceptance command failed: suite failed",
    ):
        bundle_module.run_python_acceptance(tmp_path)

    assert not junit.exists()
    assert not coverage.exists()
    assert acceptance.read_bytes() == b"prior acceptance\n"


def test_python_acceptance_validator_aggregates_stale_noncanonical_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "output"
    output.mkdir()
    receipt = {
        "schema_version": 2,
        "kind": "invented-receipt",
        "complete": False,
        "returncode": 1,
        "command": ["invented-command"],
        "executor": {"fingerprint_sha256": "stale"},
        "collection": {
            "command": ["invented-collection"],
            "node_ids": ["tests/test_fixture.py::test_invented"],
        },
        "inputs": {
            "before": {"fingerprint_sha256": "before"},
            "after": {"fingerprint_sha256": "stale"},
            "stable": False,
        },
        "tests": {"collected": 0},
        "coverage": {"line_rate": 0.0},
    }
    (tmp_path / bundle_module.PYTHON_ACCEPTANCE_RECEIPT).write_text(
        json.dumps(receipt, indent=2), encoding="utf-8"
    )
    monkeypatch.setattr(
        bundle_module,
        "_collect_python_node_ids",
        lambda _root, _temporary_root: ("tests/test_fixture.py::test_fixture",),
    )
    monkeypatch.setattr(
        bundle_module,
        "collection_runtime_identity",
        lambda: {"pytest_arguments": ["--collect-only"]},
    )
    executor_calls = 0

    def changing_executor() -> dict[str, str]:
        nonlocal executor_calls
        executor_calls += 1
        return {"fingerprint_sha256": "current" if executor_calls == 1 else "changed"}

    input_calls = 0

    def changing_inputs(_root: Path) -> dict[str, str]:
        nonlocal input_calls
        input_calls += 1
        return {"fingerprint_sha256": "current" if input_calls == 1 else "changed"}

    monkeypatch.setattr(
        bundle_module, "_python_acceptance_runtime_identity", changing_executor
    )
    monkeypatch.setattr(bundle_module, "_python_input_snapshot", changing_inputs)
    monkeypatch.setattr(
        bundle_module,
        "_python_evidence_summary",
        lambda _root: {
            "tests": {"collected": 1},
            "coverage": {"line_rate": 1.0},
        },
    )
    monkeypatch.setattr(
        bundle_module,
        "_pytest_receipt_errors",
        lambda _root, **_kwargs: ("underlying Python evidence is invalid",),
    )

    errors = bundle_module._python_acceptance_receipt_errors(tmp_path)

    assert {
        "underlying Python evidence is invalid",
        "Python acceptance receipt is not canonical sorted JSON",
        "Python acceptance receipt schema_version must be 3",
        "Python acceptance receipt kind is invalid",
        "Python acceptance receipt is not complete and green",
        "Python acceptance receipt command is not canonical",
        "Python acceptance receipt executor identity is stale",
        "Python acceptance receipt collection command is not canonical",
        "Python acceptance receipt collected node IDs are stale",
        "Python acceptance receipt input snapshots are not stable",
        "Python acceptance receipt input snapshot is stale",
        "Python acceptance receipt JUnit summary or hash is stale",
        "Python acceptance receipt coverage summary or hash is stale",
        "Python acceptance inputs changed during validation",
        "Python acceptance executor changed during validation",
    } <= set(errors)


def test_prerequisite_gate_reports_stale_projection_native_formal_and_browser_planes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        bundle_module,
        "report_owner_errors",
        lambda _root: ("canonical projection is stale",),
    )
    for name in (
        "formalism_coverage_drift",
        "atlas_projection_drift",
        "formal_kernel_dashboard_drift",
        "manuscript_projection_drift",
    ):
        monkeypatch.setattr(bundle_module, name, lambda _root: ())
    monkeypatch.setattr(
        bundle_module, "_theorem_maturity_projection_errors", lambda _root: ()
    )
    monkeypatch.setattr(bundle_module, "_rendered_manuscript_errors", lambda _root: ())
    monkeypatch.setattr(
        bundle_module,
        "validate_native_lean_receipt",
        lambda *_args, **_kwargs: {
            "valid": False,
            "source_bound": False,
            "native_claim_ready": False,
            "errors": ["source digest drifted"],
        },
    )
    monkeypatch.setattr(
        bundle_module,
        "validate_formalism_audit_receipt",
        lambda *_args: ("declaration closure drifted",),
    )
    monkeypatch.setattr(
        bundle_module,
        "_browser_receipt_errors",
        lambda _root, *, presentation=None: ("browser projection hash drifted",),
    )
    monkeypatch.setattr(bundle_module, "_pytest_receipt_errors", lambda _root: ())

    errors = bundle_module._base_prerequisite_errors(tmp_path)

    assert "canonical projection is stale" in errors
    assert (
        "native Lean receipt is not current and claim-ready: source digest drifted"
        in errors
    )
    assert "formalism audit receipt is stale: declaration closure drifted" in errors
    assert "browser projection hash drifted" in errors


def _write_release_metadata_fixture(project_root: Path) -> None:
    (project_root / ".aii").mkdir(parents=True, exist_ok=True)
    (project_root / "manuscript").mkdir(parents=True, exist_ok=True)
    (project_root / "src/fep_lean").mkdir(parents=True, exist_ok=True)
    (project_root / "config").mkdir(parents=True, exist_ok=True)
    (project_root / "LICENSE").write_text(
        "Creative Commons Attribution 4.0 International (CC BY 4.0)\n"
        "Work-level concept DOI: https://doi.org/10.5281/zenodo.19699233\n",
        encoding="utf-8",
    )
    (project_root / "CITATION.cff").write_text(
        "cff-version: 1.2.0\n"
        'version: "1.3.0"\n'
        'date-released: "2026-09-26"\n'
        "repository-code: https://github.com/ActiveInferenceInstitute/fep_formal\n"
        "url: https://github.com/ActiveInferenceInstitute/fep_formal\n"
        "license: CC-BY-4.0\n"
        "authors:\n"
        "  - &canonical-author\n"
        "    given-names: Daniel Ari\n"
        "    family-names: Friedman\n"
        "    email: daniel@activeinference.institute\n"
        "    orcid: https://orcid.org/0000-0001-6232-9096\n"
        "    affiliation: Active Inference Institute\n"
        "preferred-citation:\n"
        "  type: article\n"
        "  authors:\n"
        "    - *canonical-author\n"
        "  journal: Active Inference Journal\n"
        "  doi: 10.5281/zenodo.19699233\n",
        encoding="utf-8",
    )
    (project_root / "manuscript/config.yaml").write_text(
        "paper:\n"
        '  version: "1.3.0"\n'
        '  date: "2026-09-26"\n'
        "publication:\n"
        "  doi: 10.5281/zenodo.19699233\n"
        "  journal: Active Inference Journal\n"
        "metadata:\n"
        "  license: CC-BY-4.0\n",
        encoding="utf-8",
    )
    (project_root / "pyproject.toml").write_text(
        '[build-system]\nrequires = ["setuptools>=77.0.3"]\n'
        'build-backend = "setuptools.build_meta"\n\n'
        '[project]\nname = "fixture"\nversion = "1.3.0"\n'
        'readme = "README.md"\n'
        'authors = [{ name = "Daniel Ari Friedman", email = "daniel@activeinference.institute" }]\n'
        'license = "CC-BY-4.0"\n',
        encoding="utf-8",
    )
    with (project_root / "pyproject.toml").open("a", encoding="utf-8") as handle:
        handle.write(
            "\n[project.urls]\n"
            'Repository = "https://github.com/ActiveInferenceInstitute/fep_formal"\n'
            'Changelog = "https://github.com/ActiveInferenceInstitute/fep_formal/blob/main/CHANGELOG.md"\n'
            '"Concept DOI" = "https://doi.org/10.5281/zenodo.19699233"\n'
        )
    (project_root / "src/fep_lean/__init__.py").write_text(
        '__version__ = "1.3.0"\n', encoding="utf-8"
    )
    (project_root / "config/settings.yaml").write_text(
        'project:\n  version: "1.3.0"\n', encoding="utf-8"
    )
    (project_root / ".aii/config.yaml").write_text(
        "meta:\n"
        "  updated: '2026-09-26'\n"
        "repo:\n"
        "  full_name: ActiveInferenceInstitute/fep_formal\n"
        "  description: 'Release v1.3.0 (2026-09-26); concept DOI 10.5281/zenodo.19699233'\n"
        "ecosystem:\n"
        "  links:\n"
        "    github: https://github.com/ActiveInferenceInstitute/fep_formal\n"
        "provenance:\n"
        "  license: CC-BY-4.0\n"
        "  citation:\n"
        "    doi: 10.5281/zenodo.19699233\n",
        encoding="utf-8",
    )


def test_release_metadata_rejects_a_stale_institute_sidecar(tmp_path: Path) -> None:
    _write_release_metadata_fixture(tmp_path)
    sidecar = tmp_path / ".aii/config.yaml"
    sidecar.write_text(
        sidecar.read_text(encoding="utf-8").replace("v1.3.0", "v1.0.0"),
        encoding="utf-8",
    )

    assert bundle_module._license_metadata_errors(tmp_path) == (
        "InstituteOS sidecar description must identify release v1.3.0",
    )


def test_release_metadata_rejects_a_misdirected_repository_url(tmp_path: Path) -> None:
    _write_release_metadata_fixture(tmp_path)
    citation = tmp_path / "CITATION.cff"
    citation.write_text(
        citation.read_text(encoding="utf-8").replace(
            "repository-code: https://github.com/ActiveInferenceInstitute/fep_formal",
            "repository-code: https://github.com/example/wrong",
        ),
        encoding="utf-8",
    )

    assert bundle_module._license_metadata_errors(tmp_path) == (
        "CITATION.cff repository-code must be https://github.com/ActiveInferenceInstitute/fep_formal",
    )


def test_release_metadata_rejects_a_misdirected_package_url(tmp_path: Path) -> None:
    _write_release_metadata_fixture(tmp_path)
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        pyproject.read_text(encoding="utf-8").replace(
            'Repository = "https://github.com/ActiveInferenceInstitute/fep_formal"',
            'Repository = "https://github.com/example/wrong"',
        ),
        encoding="utf-8",
    )

    assert bundle_module._license_metadata_errors(tmp_path) == (
        "Python package Repository URL must be https://github.com/ActiveInferenceInstitute/fep_formal",
    )


def test_release_metadata_rejects_package_author_drift_from_citation(
    tmp_path: Path,
) -> None:
    _write_release_metadata_fixture(tmp_path)
    citation_path = tmp_path / "CITATION.cff"
    citation = yaml.safe_load(citation_path.read_text(encoding="utf-8"))
    citation["authors"][0]["given-names"] = "Ada"
    citation["authors"][0]["family-names"] = "Example"
    citation["authors"][0]["email"] = "ada@example.org"
    citation["preferred-citation"]["authors"] = citation["authors"]
    citation_path.write_text(
        yaml.safe_dump(citation, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )

    assert bundle_module._license_metadata_errors(tmp_path) == (
        (
            "Python package authors must match CITATION.cff canonical author "
            "Ada Example <ada@example.org>"
        ),
    )


def test_release_metadata_is_consistent_and_fail_closed(tmp_path: Path) -> None:
    _write_release_metadata_fixture(tmp_path)

    assert bundle_module._license_metadata_errors(tmp_path) == ()

    (tmp_path / "LICENSE").write_text(
        "Creative Commons Attribution 4.0 International (CC BY 4.0)\n",
        encoding="utf-8",
    )
    assert bundle_module._license_metadata_errors(tmp_path) == (
        "LICENSE does not declare DOI 10.5281/zenodo.19699233",
    )
    (tmp_path / "LICENSE").write_text(
        "Creative Commons Attribution 4.0 International (CC BY 4.0)\n"
        "Work-level concept DOI: https://doi.org/10.5281/zenodo.19699233\n",
        encoding="utf-8",
    )
    (tmp_path / "LICENSE").write_text(
        (tmp_path / "LICENSE").read_text(encoding="utf-8") + "Copyleft fixture\n",
        encoding="utf-8",
    )
    assert bundle_module._license_metadata_errors(tmp_path) == (
        "LICENSE must not describe CC-BY-4.0 as copyleft",
    )
    _write_release_metadata_fixture(tmp_path)

    (tmp_path / "manuscript/config.yaml").write_text(
        "paper:\n"
        '  version: "1.3.0"\n'
        '  date: "2026-09-26"\n'
        "publication:\n"
        "  doi: 10.0000/wrong\n"
        "  journal: Active Inference Journal\n"
        "metadata:\n"
        "  license: CC-BY-4.0\n",
        encoding="utf-8",
    )
    assert bundle_module._license_metadata_errors(tmp_path) == (
        "manuscript publication DOI must be 10.5281/zenodo.19699233",
    )

    (tmp_path / "manuscript/config.yaml").write_text(
        "paper:\n"
        '  version: "1.3.0"\n'
        '  date: "2026-09-26"\n'
        "publication:\n"
        "  doi: 10.5281/zenodo.19699233\n"
        "  journal: Other Journal\n"
        "metadata:\n"
        "  license: Apache-2.0\n",
        encoding="utf-8",
    )
    assert bundle_module._license_metadata_errors(tmp_path) == (
        "manuscript publication journal must be Active Inference Journal",
        "manuscript metadata license must be CC-BY-4.0",
    )

    (tmp_path / "manuscript/config.yaml").write_text(
        "paper:\n"
        '  version: "1.3.0"\n'
        '  date: "2026-09-26"\n'
        "publication:\n"
        "  doi: 10.5281/zenodo.19699233\n"
        "  journal: Active Inference Journal\n"
        "metadata:\n"
        "  license: CC-BY-4.0\n",
        encoding="utf-8",
    )
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "fixture"\nreadme = "README.md"\n'
        'authors = [{ name = "Daniel Ari Friedman", email = "daniel@activeinference.institute" }]\n\n'
        '[project.urls]\nRepository = "https://github.com/ActiveInferenceInstitute/fep_formal"\n'
        'Changelog = "https://github.com/ActiveInferenceInstitute/fep_formal/blob/main/CHANGELOG.md"\n'
        '"Concept DOI" = "https://doi.org/10.5281/zenodo.19699233"\n',
        encoding="utf-8",
    )
    assert bundle_module._license_metadata_errors(tmp_path) == (
        "Python build system must require setuptools>=77.0.3",
        "Python package license must be CC-BY-4.0",
        "Python package version must be 1.3.0",
    )

    _write_release_metadata_fixture(tmp_path)
    citation_path = tmp_path / "CITATION.cff"
    citation_path.write_text(
        citation_path.read_text(encoding="utf-8").replace(
            "doi: 10.5281/zenodo.19699233", "doi: 10.0000/wrong"
        ),
        encoding="utf-8",
    )
    assert bundle_module._license_metadata_errors(tmp_path) == (
        "CITATION.cff preferred-citation DOI must be 10.5281/zenodo.19699233",
    )

    _write_release_metadata_fixture(tmp_path)
    citation_path.write_text(
        citation_path.read_text(encoding="utf-8").replace(
            "journal: Active Inference Journal", "journal: Other Journal"
        ),
        encoding="utf-8",
    )
    assert bundle_module._license_metadata_errors(tmp_path) == (
        "CITATION.cff preferred-citation journal must be Active Inference Journal",
    )


@pytest.mark.parametrize(
    ("relative", "old", "new", "expected_error"),
    [
        (
            "CITATION.cff",
            'version: "1.3.0"',
            'version: "1.2.0"',
            "CITATION.cff version must be 1.3.0",
        ),
        (
            "CITATION.cff",
            'date-released: "2026-09-26"',
            'date-released: "2026-09-16"',
            "CITATION.cff date-released must be 2026-09-26",
        ),
        (
            "manuscript/config.yaml",
            'version: "1.3.0"',
            'version: "1.2.0"',
            "manuscript paper version must be 1.3.0",
        ),
        (
            "manuscript/config.yaml",
            'date: "2026-09-26"',
            'date: "2026-09-16"',
            "manuscript paper date must be 2026-09-26",
        ),
        (
            "pyproject.toml",
            'version = "1.3.0"',
            'version = "1.2.0"',
            "Python package version must be 1.3.0",
        ),
        (
            "src/fep_lean/__init__.py",
            '__version__ = "1.3.0"',
            '__version__ = "1.2.0"',
            "Python runtime version must be 1.3.0",
        ),
        (
            "config/settings.yaml",
            'version: "1.3.0"',
            'version: "1.2.0"',
            "runtime settings version must be 1.3.0",
        ),
    ],
)
def test_release_metadata_rejects_each_version_and_date_plane_independently(
    tmp_path: Path,
    relative: str,
    old: str,
    new: str,
    expected_error: str,
) -> None:
    _write_release_metadata_fixture(tmp_path)
    path = tmp_path / relative
    path.write_text(
        path.read_text(encoding="utf-8").replace(old, new), encoding="utf-8"
    )

    assert bundle_module._license_metadata_errors(tmp_path) == (expected_error,)


@pytest.mark.parametrize(
    ("relative", "duplicate", "expected_error"),
    [
        (
            "pyproject.toml",
            'version = "1.2.0"\n',
            "Python package version must be 1.3.0",
        ),
        (
            "src/fep_lean/__init__.py",
            '__version__ = "1.2.0"\n',
            "Python runtime version must be 1.3.0",
        ),
    ],
)
def test_release_metadata_rejects_ambiguous_duplicate_runtime_versions(
    tmp_path: Path,
    relative: str,
    duplicate: str,
    expected_error: str,
) -> None:
    _write_release_metadata_fixture(tmp_path)
    path = tmp_path / relative
    contents = path.read_text(encoding="utf-8")
    if relative == "pyproject.toml":
        contents = contents.replace(
            'version = "1.3.0"\n',
            'version = "1.3.0"\n' + duplicate,
            1,
        )
    else:
        contents += duplicate
    path.write_text(
        contents,
        encoding="utf-8",
    )

    assert bundle_module._license_metadata_errors(tmp_path) == (expected_error,)


def test_live_release_metadata_planes_are_consistent() -> None:
    project_root = Path(__file__).resolve().parents[1]

    assert bundle_module._license_metadata_errors(project_root) == ()


def test_release_bundle_cli_exposes_output_and_nonmutating_check(
    tmp_path: Path,
) -> None:
    project_root = Path(__file__).resolve().parents[1]
    script = project_root / "scripts" / "build_release_bundle.py"
    help_result = subprocess.run(
        ["uv", "run", "python", str(script), "--help"],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
    )
    missing = tmp_path / "missing.tar.gz"
    check_result = subprocess.run(
        [
            "uv",
            "run",
            "python",
            str(script),
            "--check",
            "--output",
            str(missing),
        ],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert help_result.returncode == 0
    assert "--output" in help_result.stdout
    assert "--check" in help_result.stdout
    assert "--run-python-acceptance" in help_result.stdout
    assert check_result.returncode == 1
    assert "release bundle validation failed" in check_result.stdout
    assert not missing.exists()


def test_public_builder_atomically_produces_identical_archives(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project_root = tmp_path / "checkout"
    project_root.mkdir()
    monkeypatch.setattr(bundle_module, "_base_prerequisite_errors", lambda _root: ())
    monkeypatch.setattr(
        bundle_module, "write_publication_manuscript", lambda *_args, **_kwargs: ()
    )
    monkeypatch.setattr(
        bundle_module, "publication_manuscript_errors", lambda *_args, **_kwargs: ()
    )
    monkeypatch.setattr(bundle_module, "_project_members", lambda _root: ())
    contents = _valid_contents({})
    monkeypatch.setattr(
        bundle_module,
        "_archive_contents",
        lambda _root, _members, *, epoch: contents,
    )
    first = tmp_path / "first.tar.gz"
    second = tmp_path / "second.tar.gz"

    build_release_bundle(project_root, first, source_date_epoch=0)
    build_release_bundle(project_root, second, source_date_epoch=0)

    assert first.read_bytes() == second.read_bytes()
    assert validate_release_bundle(first).valid is True
    assert not tuple(tmp_path.glob(".*.stage-*"))


def test_public_builder_rejects_project_input_destination(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project_root = tmp_path / "checkout"
    project_root.mkdir()
    destination = project_root / "release.tar.gz"
    monkeypatch.setattr(bundle_module, "_base_prerequisite_errors", lambda _root: ())

    with pytest.raises(
        bundle_module.ReleaseBundleError,
        match="destination must be outside the project root",
    ):
        build_release_bundle(project_root, destination, source_date_epoch=0)

    assert not destination.exists()


def test_public_builder_rejects_a_symlinked_destination(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project_root = tmp_path / "checkout"
    project_root.mkdir()
    target = tmp_path / "target.tar.gz"
    target.write_bytes(b"prior release\n")
    destination = tmp_path / "release.tar.gz"
    destination.symlink_to(target)
    monkeypatch.setattr(
        bundle_module,
        "_base_prerequisite_errors",
        lambda _root: ("must not reach prerequisites",),
    )

    with pytest.raises(
        bundle_module.ReleaseBundleError,
        match="release bundle destination is a symlink",
    ):
        build_release_bundle(project_root, destination, source_date_epoch=0)

    assert destination.is_symlink()
    assert target.read_bytes() == b"prior release\n"


def test_public_builder_rejects_a_concurrently_changed_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project_root = tmp_path / "checkout"
    project_root.mkdir()
    readme = project_root / "README.md"
    readme.write_text("snapshot A\n", encoding="utf-8")
    member = bundle_module._BundleMember(
        "README.md", readme.read_bytes(), "project_documentation"
    )
    monkeypatch.setattr(bundle_module, "_base_prerequisite_errors", lambda _root: ())
    monkeypatch.setattr(
        bundle_module, "write_publication_manuscript", lambda *_args, **_kwargs: ()
    )
    monkeypatch.setattr(
        bundle_module, "publication_manuscript_errors", lambda *_args, **_kwargs: ()
    )
    monkeypatch.setattr(bundle_module, "_project_members", lambda _root: (member,))

    def mutate_during_manifest(
        _root: Path,
        _members: tuple[object, ...],
        *,
        epoch: int,
    ) -> dict[str, bytes]:
        assert epoch == 0
        readme.write_text("snapshot B\n", encoding="utf-8")
        return _valid_contents({})

    monkeypatch.setattr(bundle_module, "_archive_contents", mutate_during_manifest)

    with pytest.raises(
        bundle_module.ReleaseBundleError,
        match="release inputs changed while the immutable snapshot was assembled",
    ):
        build_release_bundle(
            project_root, tmp_path / "release.tar.gz", source_date_epoch=0
        )


def test_public_builder_preserves_destination_when_inputs_change_after_staging(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project_root = tmp_path / "checkout"
    project_root.mkdir()
    readme = project_root / "README.md"
    readme.write_text("snapshot A\n", encoding="utf-8")
    member = bundle_module._BundleMember(
        "README.md", readme.read_bytes(), "project_documentation"
    )
    monkeypatch.setattr(bundle_module, "_base_prerequisite_errors", lambda _root: ())
    monkeypatch.setattr(
        bundle_module, "write_publication_manuscript", lambda *_args, **_kwargs: ()
    )
    monkeypatch.setattr(
        bundle_module, "publication_manuscript_errors", lambda *_args, **_kwargs: ()
    )
    monkeypatch.setattr(bundle_module, "_project_members", lambda _root: (member,))
    contents = _valid_contents({"README.md": b"snapshot A\n"})
    monkeypatch.setattr(
        bundle_module,
        "_archive_contents",
        lambda _root, _members, *, epoch: contents,
    )
    real_write = bundle_module._write_archive
    mutated = False

    def mutate_after_staging(
        path: Path, payload: dict[str, bytes], *, epoch: int
    ) -> None:
        nonlocal mutated
        real_write(path, payload, epoch=epoch)
        if not mutated:
            readme.write_text("snapshot B\n", encoding="utf-8")
            mutated = True

    monkeypatch.setattr(bundle_module, "_write_archive", mutate_after_staging)
    destination = tmp_path / "release.tar.gz"
    destination.write_bytes(b"prior release\n")

    with pytest.raises(
        bundle_module.ReleaseBundleError,
        match="live release inputs changed during validation|"
        "release inputs changed before the staged archive could be committed",
    ):
        build_release_bundle(project_root, destination, source_date_epoch=0)

    assert destination.read_bytes() == b"prior release\n"


def test_public_builder_fingerprints_unbundled_manuscript_sources(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project_root = tmp_path / "checkout"
    manuscript = project_root / "manuscript"
    manuscript.mkdir(parents=True)
    source = manuscript / "01_chapter.md"
    source.write_text("source A\n", encoding="utf-8")
    (project_root / "README.md").write_text("snapshot\n", encoding="utf-8")
    member = bundle_module._BundleMember(
        "README.md", b"snapshot\n", "project_documentation"
    )
    monkeypatch.setattr(bundle_module, "_base_prerequisite_errors", lambda _root: ())
    monkeypatch.setattr(
        bundle_module, "write_publication_manuscript", lambda *_args, **_kwargs: ()
    )
    monkeypatch.setattr(
        bundle_module, "publication_manuscript_errors", lambda *_args, **_kwargs: ()
    )
    monkeypatch.setattr(bundle_module, "_project_members", lambda _root: (member,))
    contents = _valid_contents({"README.md": b"snapshot\n"})
    monkeypatch.setattr(
        bundle_module,
        "_archive_contents",
        lambda _root, _members, *, epoch: contents,
    )
    real_write = bundle_module._write_archive
    mutated = False

    def mutate_source_after_staging(
        path: Path, payload: dict[str, bytes], *, epoch: int
    ) -> None:
        nonlocal mutated
        real_write(path, payload, epoch=epoch)
        if not mutated:
            source.write_text("source B\n", encoding="utf-8")
            mutated = True

    monkeypatch.setattr(bundle_module, "_write_archive", mutate_source_after_staging)

    with pytest.raises(
        bundle_module.ReleaseBundleError,
        match="release inputs changed before the staged archive could be committed",
    ):
        build_release_bundle(
            project_root, tmp_path / "release.tar.gz", source_date_epoch=0
        )


def test_publication_set_rolls_back_every_member_after_install_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "output" / "manuscript"
    output.mkdir(parents=True)
    html = tmp_path / bundle_module.PUBLICATION_HTML
    provenance = tmp_path / bundle_module.RENDERER_PROVENANCE
    html.write_bytes(b"old html")
    provenance.write_bytes(b"old provenance")
    monkeypatch.setattr(
        bundle_module,
        "render_publication_manuscript",
        lambda *_args, **_kwargs: bundle_module.PublicationManuscript(
            html=b"new html",
            pdf=None,
            provenance=b"new provenance",
            source_digest="0" * 64,
        ),
    )
    real_replace = bundle_module.os.replace

    def fail_second_install(source: object, destination: object) -> None:
        source_path = Path(source)  # type: ignore[arg-type]
        if (
            source_path.parent.name == "new"
            and source_path.name == bundle_module.RENDERER_PROVENANCE.name
        ):
            raise OSError("injected install failure")
        real_replace(source, destination)

    monkeypatch.setattr(bundle_module.os, "replace", fail_second_install)

    with pytest.raises(
        bundle_module.ReleaseBundleError,
        match="cannot transactionally replace publication set",
    ):
        write_publication_manuscript(tmp_path, source_date_epoch=0)

    assert html.read_bytes() == b"old html"
    assert provenance.read_bytes() == b"old provenance"


@pytest.mark.parametrize("symlink_level", ["manuscript", "output"])
def test_publication_set_rejects_a_symlinked_destination_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, symlink_level: str
) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    output = tmp_path / "output"
    if symlink_level == "manuscript":
        output.mkdir()
        (output / "manuscript").symlink_to(outside, target_is_directory=True)
        error = "publication destination directory is a symlink"
    else:
        output.symlink_to(outside, target_is_directory=True)
        error = "publication destination directory traverses a symlink"
    monkeypatch.setattr(
        bundle_module,
        "render_publication_manuscript",
        lambda *_args, **_kwargs: bundle_module.PublicationManuscript(
            html=b"new html",
            pdf=None,
            provenance=b"new provenance",
            source_digest="0" * 64,
        ),
    )

    with pytest.raises(
        bundle_module.ReleaseBundleError,
        match=error,
    ):
        write_publication_manuscript(tmp_path, source_date_epoch=0)

    assert not tuple(outside.iterdir())


def test_publication_set_rolls_back_after_an_interrupted_install(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "output" / "manuscript"
    output.mkdir(parents=True)
    html = tmp_path / bundle_module.PUBLICATION_HTML
    provenance = tmp_path / bundle_module.RENDERER_PROVENANCE
    html.write_bytes(b"old html")
    provenance.write_bytes(b"old provenance")
    monkeypatch.setattr(
        bundle_module,
        "render_publication_manuscript",
        lambda *_args, **_kwargs: bundle_module.PublicationManuscript(
            html=b"new html",
            pdf=None,
            provenance=b"new provenance",
            source_digest="0" * 64,
        ),
    )
    real_replace = bundle_module.os.replace

    def interrupt_second_install(source: object, destination: object) -> None:
        source_path = Path(source)  # type: ignore[arg-type]
        if (
            source_path.parent.name == "new"
            and source_path.name == bundle_module.RENDERER_PROVENANCE.name
        ):
            raise KeyboardInterrupt
        real_replace(source, destination)

    monkeypatch.setattr(bundle_module.os, "replace", interrupt_second_install)

    with pytest.raises(KeyboardInterrupt):
        write_publication_manuscript(tmp_path, source_date_epoch=0)

    assert html.read_bytes() == b"old html"
    assert provenance.read_bytes() == b"old provenance"


@pytest.mark.parametrize("interrupt_after", range(8))
def test_publication_set_restores_old_and_absent_members_after_each_atomic_move(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    interrupt_after: int,
) -> None:
    output = tmp_path / "output" / "manuscript"
    output.mkdir(parents=True)
    html = tmp_path / bundle_module.PUBLICATION_HTML
    pdf = tmp_path / bundle_module.PUBLICATION_PDF
    provenance = tmp_path / bundle_module.RENDERER_PROVENANCE
    html.write_bytes(b"old html")
    provenance.write_bytes(b"old provenance")
    desired = {
        bundle_module.PUBLICATION_HTML: b"new html",
        bundle_module.PUBLICATION_PDF: b"new pdf",
        bundle_module.RENDERER_PROVENANCE: b"new provenance",
    }
    real_replace = bundle_module.os.replace
    transaction_moves = 0

    def interrupt_after_atomic_move(source: object, destination: object) -> None:
        nonlocal transaction_moves
        source_path = Path(source)  # type: ignore[arg-type]
        destination_path = Path(destination)  # type: ignore[arg-type]
        is_stage = destination_path.parent.name == "new"
        is_backup = destination_path.parent.name == "backup"
        is_install = (
            source_path.parent.name == "new" and destination_path.parent == output
        )
        real_replace(source, destination)
        if is_stage or is_backup or is_install:
            current_move = transaction_moves
            transaction_moves += 1
            if current_move == interrupt_after:
                raise KeyboardInterrupt

    monkeypatch.setattr(bundle_module.os, "replace", interrupt_after_atomic_move)

    with pytest.raises(KeyboardInterrupt):
        bundle_module._replace_publication_set(tmp_path, desired)

    assert html.read_bytes() == b"old html"
    assert provenance.read_bytes() == b"old provenance"
    assert not pdf.exists()


@pytest.mark.parametrize(
    ("rollback_failure", "expected_detail", "preserved_name"),
    [
        (
            "unlink",
            "unlink output/manuscript/fep-lean-manuscript.html",
            "fep-lean-manuscript.html",
        ),
        (
            "restore",
            "restore output/manuscript/renderer-provenance.json",
            "renderer-provenance.json",
        ),
    ],
)
def test_publication_set_reports_rollback_failures_and_preserves_recovery_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    rollback_failure: str,
    expected_detail: str,
    preserved_name: str,
) -> None:
    output = tmp_path / "output" / "manuscript"
    output.mkdir(parents=True)
    html = tmp_path / bundle_module.PUBLICATION_HTML
    provenance = tmp_path / bundle_module.RENDERER_PROVENANCE
    html.write_bytes(b"old html")
    provenance.write_bytes(b"old provenance")
    desired = {
        bundle_module.PUBLICATION_HTML: b"new html",
        bundle_module.RENDERER_PROVENANCE: b"new provenance",
    }
    real_replace = bundle_module.os.replace
    real_unlink = Path.unlink

    def fail_install_or_restore(source: object, destination: object) -> None:
        source_path = Path(source)  # type: ignore[arg-type]
        if (
            source_path.parent.name == "new"
            and source_path.name == bundle_module.RENDERER_PROVENANCE.name
        ):
            raise OSError("injected install failure")
        if (
            rollback_failure == "restore"
            and source_path.parent.name == "backup"
            and source_path.name == bundle_module.RENDERER_PROVENANCE.name
        ):
            raise OSError("injected restore failure")
        real_replace(source, destination)

    def fail_rollback_unlink(
        path: Path, missing_ok: bool = False
    ) -> None:  # pragma: no cover - signature parity
        if rollback_failure == "unlink" and path == html:
            raise OSError("injected unlink failure")
        real_unlink(path, missing_ok=missing_ok)

    monkeypatch.setattr(bundle_module.os, "replace", fail_install_or_restore)
    monkeypatch.setattr(Path, "unlink", fail_rollback_unlink)

    with pytest.raises(
        bundle_module.ReleaseBundleError,
        match="cannot transactionally replace publication set",
    ) as captured:
        bundle_module._replace_publication_set(tmp_path, desired)

    assert expected_detail in str(captured.value)
    recovery_roots = tuple(output.glob(".publication-set-*/backup"))
    assert len(recovery_roots) == 1
    assert (recovery_roots[0] / preserved_name).read_bytes().startswith(b"old ")


def test_structural_validation_without_live_root_is_not_claim_ready(
    tmp_path: Path,
) -> None:
    archive = tmp_path / "structural.tar.gz"
    bundle_module._write_archive(archive, _valid_contents({}), epoch=0)

    validation = validate_release_bundle(archive)

    assert validation.valid is True
    assert validation.source_bound is False
    assert validation.claim_ready is False


def test_live_validation_rejects_inputs_that_change_during_comparison(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "checkout"
    root.mkdir()
    readme = root / "README.md"
    readme.write_text("snapshot A\n", encoding="utf-8")
    member = bundle_module._BundleMember(
        "README.md", readme.read_bytes(), "project_documentation"
    )
    contents = _valid_contents({"README.md": b"snapshot A\n"})
    archive = tmp_path / "release.tar.gz"
    bundle_module._write_archive(archive, contents, epoch=0)
    monkeypatch.setattr(bundle_module, "_base_prerequisite_errors", lambda _root: ())
    monkeypatch.setattr(
        bundle_module, "publication_manuscript_errors", lambda *_args, **_kwargs: ()
    )
    monkeypatch.setattr(bundle_module, "_project_members", lambda _root: (member,))

    def mutate_during_expected_archive(
        _root: Path,
        _members: tuple[object, ...],
        *,
        epoch: int,
    ) -> dict[str, bytes]:
        assert epoch == 0
        readme.write_text("snapshot B\n", encoding="utf-8")
        return contents

    monkeypatch.setattr(
        bundle_module, "_archive_contents", mutate_during_expected_archive
    )

    validation = validate_release_bundle(archive, project_root=root)

    assert validation.claim_ready is False
    assert "live release inputs changed during validation" in validation.errors


def test_structural_validator_rejects_unowned_manifest_paths(tmp_path: Path) -> None:
    archive = tmp_path / "unowned.tar.gz"
    bundle_module._write_archive(
        archive,
        _valid_contents({"docs/unowned.txt": b"self-consistent fiction\n"}),
        epoch=0,
    )

    validation = validate_release_bundle(archive)

    assert validation.valid is False
    assert "manifest member path is not release-owned: docs/unowned.txt" in (
        validation.errors
    )


def _capture_stage(root: Path, name: str, dependencies: tuple[str, ...] = ()):
    from fep_lean.output.release_bundle._core import PublicationCaptureStage

    source, output = root / f"{name}.input", root / f"{name}.output"
    source.write_bytes(name.encode())
    producer = (
        "from pathlib import Path;import sys;"
        "data=Path(sys.argv[1]).read_bytes();"
        "Path(sys.argv[2]).write_bytes(data);print('produced');"
        "raise SystemExit(2 if data==b'reject' else 0)"
    )
    validator = (
        "from pathlib import Path;import sys;"
        "assert Path(sys.argv[1]).read_bytes()==Path(sys.argv[2]).read_bytes();"
        "print('checked')"
    )
    args = (str(source), str(output))
    return PublicationCaptureStage(
        name,
        dependencies,
        (str(source),),
        (str(output),),
        (sys.executable, "-c", producer, *args),
        (sys.executable, "-c", validator, *args),
        10,
    )


def _capture_plan(root: Path, stages):
    from fep_lean.output.release_bundle._core import PublicationCapturePlan

    return PublicationCapturePlan(str(root), tuple(stages), 30)


def test_publication_capture_plan_is_process_free(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from fep_lean.output.release_bundle._core import plan_publication_capture

    template = tmp_path / "template"
    renderer = template / "scripts/pipeline/stage_03_render.py"
    renderer.parent.mkdir(parents=True)
    renderer.write_text("# explicit fixture template owner\n")

    def forbid(*_args, **_kwargs):
        pytest.fail("planning launched a process")

    monkeypatch.setattr(subprocess, "Popen", forbid)
    plan = plan_publication_capture(PROJ, template_root=template)
    assert tuple(s.name for s in plan.stages) == (
        "native",
        "formalism-audit",
        "python",
        "render",
        "numerical",
        "browser",
        "bundle",
    )
    assert plan.stages[-1].outputs == (
        "{attempt}/release-a.tar.gz",
        "{attempt}/release-b.tar.gz",
    )
    assert not (tmp_path / "journal").exists()


def test_publication_capture_reuses_unchanged_stages_and_invalidates_descendants(
    tmp_path: Path,
) -> None:
    from fep_lean.output.release_bundle._core import run_publication_capture

    root = tmp_path / "project"
    root.mkdir()
    a, b, child = (
        _capture_stage(root, "a"),
        _capture_stage(root, "b"),
        _capture_stage(root, "child", ("a",)),
    )
    plan = _capture_plan(root, (a, b, child))
    journal = tmp_path / "journal"
    assert run_publication_capture(plan, journal).complete
    original = {p: p.read_bytes() for p in journal.rglob("*") if p.is_file()}
    resumed = run_publication_capture(plan, journal, resume=True)
    assert resumed.complete and resumed.reused_stages == ("a", "b", "child")
    assert all(p.read_bytes() == data for p, data in original.items())
    # Repeated resume retains the original producer artifact origin.
    assert run_publication_capture(plan, journal, resume=True).reused_stages == (
        "a",
        "b",
        "child",
    )
    (root / "a.input").write_bytes(b"new source")
    changed = run_publication_capture(plan, journal, resume=True)
    assert changed.complete and changed.reused_stages == ("b",)
    records = [
        json.loads(p.read_text())
        for p in sorted(journal.glob("attempts/*/result.json"))
    ][-3:]
    assert [r["mode"] for r in records] == ["capture", "reuse", "capture"]
    assert (root / "a.output").read_bytes() == b"new source"


def test_publication_capture_failed_stage_resume_preserves_partial_and_prior_bytes(
    tmp_path: Path,
) -> None:
    from fep_lean.output.release_bundle._core import run_publication_capture

    root = tmp_path / "project"
    root.mkdir()
    a, b = _capture_stage(root, "a"), _capture_stage(root, "b")
    (root / "b.output").write_bytes(b"prior accepted bytes")
    (root / "b.input").write_bytes(b"reject")
    plan, journal = _capture_plan(root, (a, b)), tmp_path / "journal"
    rejected = run_publication_capture(plan, journal)
    assert not rejected.complete and rejected.failed_stage == "b"
    attempt = journal / "attempts/000002-b"
    assert (attempt / "prior/0000.bin").read_bytes() == b"prior accepted bytes"
    assert (attempt / "artifacts/0000.bin").read_bytes() == b"reject"
    retained = {p: p.read_bytes() for p in attempt.rglob("*") if p.is_file()}
    (root / "b.input").write_bytes(b"repaired independent input")
    recovered = run_publication_capture(plan, journal, resume=True)
    assert recovered.complete and recovered.reused_stages == ("a",)
    assert all(p.read_bytes() == data for p, data in retained.items())


@pytest.mark.parametrize(
    "tamper", ["policy", "artifact", "stream", "acceptance", "extra", "symlink"]
)
def test_publication_capture_rejects_tampered_history_before_process(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, tamper: str
) -> None:
    from fep_lean.output.release_bundle._core import run_publication_capture

    root = tmp_path / "project"
    root.mkdir()
    plan, journal = (
        _capture_plan(root, (_capture_stage(root, "a"),)),
        tmp_path / "journal",
    )
    assert run_publication_capture(plan, journal).complete
    attempt = journal / "attempts/000001-a"
    target = {
        "policy": journal / "journal.json",
        "artifact": attempt / "artifacts/0000.bin",
        "stream": attempt / "stdout.log",
        "acceptance": attempt / "result.json",
        "extra": attempt / "unexpected",
        "symlink": attempt / "artifacts/0000.bin",
    }[tamper]
    if tamper == "symlink":
        target.unlink()
        target.symlink_to(root / "a.output")
    elif tamper == "acceptance":
        payload = json.loads(target.read_text())
        payload["check_returncode"] = True
        target.chmod(0o644)
        target.write_text(json.dumps(payload))
    else:
        if target.exists():
            target.chmod(0o644)
        target.write_bytes(b"tampered")

    def forbid(*_args, **_kwargs):
        pytest.fail("tampered history launched a process")

    monkeypatch.setattr(subprocess, "Popen", forbid)
    with pytest.raises(bundle_module.ReleaseBundleError):
        run_publication_capture(plan, journal, resume=True)


def test_publication_capture_rejects_source_mutation_and_missing_artifacts(
    tmp_path: Path,
) -> None:
    from dataclasses import replace

    from fep_lean.output.release_bundle._core import run_publication_capture

    root = tmp_path / "project"
    root.mkdir()
    stage = _capture_stage(root, "a")
    code = "from pathlib import Path;import sys;Path(sys.argv[1]).write_bytes(b'mutated');Path(sys.argv[2]).write_bytes(b'mutated')"
    stage = replace(
        stage, command=(sys.executable, "-c", code, stage.inputs[0], stage.outputs[0])
    )
    rejected = run_publication_capture(
        _capture_plan(root, (stage,)), tmp_path / "mutation"
    )
    assert not rejected.complete and any("inputs changed" in e for e in rejected.errors)
    (root / "a.output").unlink()
    stage = replace(
        stage,
        command=(sys.executable, "-c", "pass"),
        check_command=(sys.executable, "-c", "pass"),
    )
    missing = run_publication_capture(
        _capture_plan(root, (stage,)), tmp_path / "missing"
    )
    assert not missing.complete and any("missing" in e for e in missing.errors)


def test_publication_capture_owns_only_its_external_journal_and_declared_outputs(
    tmp_path: Path,
) -> None:
    from dataclasses import replace

    from fep_lean.output.release_bundle._core import run_publication_capture

    root = tmp_path / "project"
    root.mkdir()
    stage = _capture_stage(root, "a")
    with pytest.raises(bundle_module.ReleaseBundleError, match="outside"):
        run_publication_capture(_capture_plan(root, (stage,)), root / "journal")
    outside = tmp_path / "outside"
    outside.write_bytes(b"keep")
    linked = root / "link.output"
    linked.symlink_to(outside)
    stage = replace(stage, outputs=(str(linked),))
    with pytest.raises(bundle_module.ReleaseBundleError, match="canonical"):
        run_publication_capture(_capture_plan(root, (stage,)), tmp_path / "journal")
    assert outside.read_bytes() == b"keep"


def test_publication_capture_two_archive_worker_requires_independent_strict_acceptance_and_parity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from fep_lean.output.release_bundle._core import _publication_capture_worker

    archives = [tmp_path / name for name in ("release-a.tar.gz", "release-b.tar.gz")]
    for archive in archives:
        bundle_module._write_archive(archive, _valid_contents({}), epoch=0)
    calls = []

    def accepted(path, *, project_root):
        calls.append(path)
        return SimpleNamespace(errors=(), claim_ready=True)

    monkeypatch.setattr(bundle_module, "validate_release_bundle", accepted)
    assert (
        _publication_capture_worker(
            "bundle", "check", str(tmp_path), str(tmp_path), str(tmp_path), "0"
        )
        == 0
    )
    assert calls == archives
    archives[1].write_bytes(archives[1].read_bytes() + b"divergence")
    assert (
        _publication_capture_worker(
            "bundle", "check", str(tmp_path), str(tmp_path), str(tmp_path), "0"
        )
        == 1
    )
    monkeypatch.setattr(
        bundle_module,
        "validate_release_bundle",
        lambda *_args, **_kwargs: SimpleNamespace(
            errors=("strict owner rejected",), claim_ready=False
        ),
    )
    assert (
        _publication_capture_worker(
            "bundle", "check", str(tmp_path), str(tmp_path), str(tmp_path), "0"
        )
        == 1
    )


def test_publication_capture_runs_real_numerical_owner_in_disposable_project(
    tmp_path: Path,
) -> None:
    from fep_lean.output.release_bundle._core import (
        _PUBLICATION_CAPTURE_WORKER,
        PublicationCaptureStage,
        run_publication_capture,
    )

    root = tmp_path / "project"
    root.mkdir()
    for name in ("src", "config"):
        shutil.copytree(
            PROJ / name,
            root / name,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
    inputs = tuple(str(p) for p in sorted(root.rglob("*")) if p.is_file())
    command = (sys.executable, "-c", _PUBLICATION_CAPTURE_WORKER, "numerical")
    stage = PublicationCaptureStage(
        "numerical",
        (),
        inputs,
        (str(root / "output/numerical-witnesses.json"),),
        (*command, "produce", str(root), "{attempt}", str(root), "0"),
        (*command, "check", str(root), "{artifact_attempt}", str(root), "0"),
        30,
    )
    result = run_publication_capture(
        _capture_plan(root, (stage,)), tmp_path / "journal"
    )
    assert result.complete
    receipt = json.loads((root / "output/numerical-witnesses.json").read_text())
    assert (
        receipt["complete"] is True
        and receipt["evidence_kind"]
        == "deterministic_numerical_witness_non_proof_evidence"
    )
    assert run_publication_capture(
        _capture_plan(root, (stage,)), tmp_path / "journal", resume=True
    ).reused_stages == ("numerical",)


@pytest.mark.skipif(os.name != "posix", reason="POSIX process-group capture contract")
def test_publication_capture_deadline_reaps_real_child_and_grandchild(
    tmp_path: Path,
) -> None:
    from dataclasses import replace

    from fep_lean.output.release_bundle._core import run_publication_capture

    root = tmp_path / "project"
    root.mkdir()
    stage = _capture_stage(root, "a")
    pidfile = root / "processes.json"
    code = (
        "import os,subprocess,sys,time,json;from pathlib import Path;"
        "child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(120)']);"
        "Path(sys.argv[1]).write_text(json.dumps([os.getpid(),child.pid]));"
        "print('capture started',flush=True);time.sleep(120)"
    )
    stage = replace(
        stage,
        command=(sys.executable, "-c", code, str(pidfile)),
        outputs=(str(pidfile),),
        timeout_s=1,
    )
    started = time.monotonic()
    outcome = run_publication_capture(
        _capture_plan(root, (stage,)), tmp_path / "journal"
    )
    assert time.monotonic() - started < 4
    assert not outcome.complete and "deadline" in outcome.errors[0]
    for pid in json.loads(pidfile.read_text()):
        state = subprocess.run(
            ["ps", "-o", "stat=", "-p", str(pid)],
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()
        assert not state or state.startswith("Z"), (
            f"owned descendant still running: {pid} {state}"
        )
    attempt = tmp_path / "journal/attempts/000001-a"
    assert "capture started" in (attempt / "stdout.log").read_text()
    assert json.loads((attempt / "result.json").read_text())["timed_out"] is True


def test_publication_capture_cli_plan_is_additive_and_process_free(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from fep_lean.cli import main

    template = tmp_path / "template"
    renderer = template / "scripts/pipeline/stage_03_render.py"
    renderer.parent.mkdir(parents=True)
    renderer.write_text("# planning-only fixture\n")

    def forbid(*_args, **_kwargs):
        pytest.fail("CLI planning launched a process")

    monkeypatch.setattr(subprocess, "Popen", forbid)
    assert (
        main(
            [
                "--project-root",
                str(PROJ),
                "publication-capture",
                "--template",
                str(template),
                "--plan",
            ]
        )
        == 0
    )
    policy = json.loads(capsys.readouterr().out)
    assert policy["kind"] == "strict-local-publication-capture"
    assert policy["stages"][-1]["name"] == "bundle"


@pytest.mark.parametrize(
    "arguments",
    [
        ["--plan-capture", "--check"],
        ["--plan-capture", "--run-python-acceptance"],
        ["--plan-capture", "--write-numerical-witnesses"],
        ["--plan-capture", "--capture-journal", "/unused"],
        ["--plan-capture", "--resume"],
        ["--capture-journal", "/unused", "--output", "/unused.tar.gz"],
        ["--resume"],
    ],
)
def test_publication_capture_wrapper_rejects_ambiguous_actions_without_execution(
    arguments: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    namespace = runpy.run_path(str(PROJ / "scripts/build_release_bundle.py"))

    def forbid(*_args, **_kwargs):
        pytest.fail("invalid capture arguments launched a process")

    monkeypatch.setattr(subprocess, "Popen", forbid)
    with pytest.raises(SystemExit) as rejected:
        namespace["main"](arguments)
    assert rejected.value.code == 2


def test_publication_capture_template_seals_all_resource_types(
    tmp_path: Path,
) -> None:
    from fep_lean.output.release_bundle._core import plan_publication_capture

    template = tmp_path / "template"
    renderer = template / "scripts/pipeline/stage_03_render.py"
    renderer.parent.mkdir(parents=True)
    renderer.write_text("# explicit fixture\n")
    for name in (
        "theme.sty",
        "article.cls",
        "refs.bib",
        "page.css",
        "page.js",
        "logo.png",
        "scripts.py",
        "config-wizard.md",
    ):
        (template / name).write_bytes(b"retained resource")
    nested = template / "config/README.md"
    nested.parent.mkdir()
    nested.write_bytes(b"retained nested resource")
    cache = template / ".venv/ignored-resource.sty"
    cache.parent.mkdir()
    cache.write_bytes(b"excluded environment")
    plan = plan_publication_capture(PROJ, template_root=template)
    for stage_name in ("render", "bundle"):
        stage = next(s for s in plan.stages if s.name == stage_name)
        expected = tuple(
            sorted(str(p) for p in template.rglob("*") if p.is_file() and p != cache)
        )
        assert (str(template), expected) in stage.input_rosters
        assert set(expected) <= set(stage.inputs)
        assert str(cache) not in stage.inputs


def _linked_capture_stage(tmp_path: Path):
    from dataclasses import replace

    root = tmp_path / "project"
    root.mkdir()
    owner = tmp_path / "resources"
    leaf = owner / "canonical/style.txt"
    leaf.parent.mkdir(parents=True)
    leaf.write_bytes(b"owned style")
    alias = owner / "links/style.txt"
    alias.parent.mkdir()
    alias.symlink_to("../canonical/style.txt")
    files = tuple(sorted((str(leaf), str(alias))))
    stage = _capture_stage(root, "a")
    stage = replace(
        stage,
        inputs=tuple(sorted((*stage.inputs, *files))),
        input_rosters=((str(owner), files),),
        resource_links=((str(alias), "../canonical/style.txt"),),
    )
    return root, owner, leaf, alias, stage


@pytest.mark.skipif(os.name != "posix", reason="POSIX descriptor link ownership")
def test_publication_capture_declared_internal_link_and_resume(tmp_path: Path) -> None:
    from fep_lean.output.release_bundle._core import run_publication_capture

    root, _owner, leaf, alias, stage = _linked_capture_stage(tmp_path)
    plan = _capture_plan(root, (stage,))
    journal = tmp_path / "journal"
    outcome = run_publication_capture(plan, journal)
    assert outcome.complete
    policy = json.loads((journal / "journal.json").read_text())["policy"]
    assert policy["stages"][0]["resource_links"] == [
        {"path": str(alias), "target": "../canonical/style.txt"}
    ]
    assert alias.read_bytes() == leaf.read_bytes() == b"owned style"
    assert run_publication_capture(plan, journal, resume=True).reused_stages == ("a",)


@pytest.mark.skipif(os.name != "posix", reason="POSIX descriptor link ownership")
def test_publication_capture_real_template_registration_is_process_free(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from fep_lean.output.release_bundle._core import plan_publication_capture

    template = tmp_path / "template"
    entry = template / "scripts/pipeline/stage_03_render.py"
    entry.parent.mkdir(parents=True)
    entry.write_text("# fixed fixture pipeline\n")
    target = template / "styles/base.sty"
    target.parent.mkdir()
    target.write_text("owned resource\n")
    alias = template / "alias.sty"
    alias.symlink_to("styles/base.sty")
    same_stem = template / "scripts.py"
    same_stem.symlink_to("styles/base.sty")
    nested_alias = template / "scripts/alias.sty"
    nested_alias.symlink_to("../styles/base.sty")
    registration = template / "projects/active/fep_lean"
    registration.parent.mkdir(parents=True)
    registration.symlink_to(PROJ, target_is_directory=True)
    monkeypatch.setattr(
        subprocess,
        "Popen",
        lambda *_args, **_kwargs: pytest.fail("planning launched a process"),
    )
    plan = plan_publication_capture(PROJ, template_root=template)
    expected = tuple(
        sorted(
            (
                (str(alias), "styles/base.sty"),
                (str(same_stem), "styles/base.sty"),
                (str(nested_alias), "../styles/base.sty"),
                (str(registration), str(PROJ)),
            )
        )
    )
    for stage in plan.stages:
        if stage.name in {"render", "bundle"}:
            assert stage.resource_links == expected
            assert {str(entry), str(target), str(alias), str(registration)} <= set(
                stage.inputs
            )
        else:
            assert stage.resource_links == ()


@pytest.mark.skipif(os.name != "posix", reason="POSIX descriptor link ownership")
@pytest.mark.parametrize(
    "case",
    [
        "external",
        "external-chain",
        "broken",
        "cyclic",
        "unsealed",
        "wrong-owner",
        "duplicate",
        "output",
        "wrong-registration",
        "excluded-target",
        "excluded-case-target",
        "excluded-bytecode-target",
    ],
)
def test_publication_capture_link_policy_rejects_forged_custom_plans(
    tmp_path: Path, case: str
) -> None:
    from dataclasses import replace

    from fep_lean.output.release_bundle._core import run_publication_capture

    root, owner, leaf, alias, stage = _linked_capture_stage(tmp_path)
    raw = "../canonical/style.txt"
    if case in {"external", "external-chain", "broken", "cyclic", "wrong-registration"}:
        alias.unlink()
        if case == "external":
            outside = tmp_path / "private.txt"
            outside.write_bytes(b"outside")
            raw = str(outside)
        elif case == "external-chain":
            outside = tmp_path / "outside"
            outside.mkdir()
            (outside / "back").symlink_to(leaf.parent, target_is_directory=True)
            raw = str(outside / "back/style.txt")
        elif case == "broken":
            raw = "../canonical/missing.txt"
        elif case == "cyclic":
            raw = "style.txt"
        else:
            wrong = tmp_path / "other-project"
            wrong.mkdir()
            registration = owner / "projects/active/fep_lean"
            registration.parent.mkdir(parents=True)
            alias = registration
            raw = str(wrong)
            files = tuple(sorted((str(leaf), str(alias))))
            stage = replace(
                stage,
                inputs=tuple(sorted((*stage.inputs[:1], *files))),
                input_rosters=((str(owner), files),),
            )
        alias.symlink_to(raw)
        stage = replace(stage, resource_links=((str(alias), raw),))
    elif case in {
        "excluded-target",
        "excluded-case-target",
        "excluded-bytecode-target",
    }:
        alias.unlink()
        leaf.unlink()
        cached = (
            owner / "canonical/bytecode.PYC"
            if case == "excluded-bytecode-target"
            else owner / ".venv/styles/base.sty"
        )
        cached.parent.mkdir(parents=True, exist_ok=True)
        cached.write_bytes(b"excluded resource")
        raw = {
            "excluded-target": "../.venv/styles",
            "excluded-case-target": "../.VeNv/styles",
            "excluded-bytecode-target": "../canonical/bytecode.PYC",
        }[case]
        alias.symlink_to(raw, target_is_directory=True)
        stage = replace(
            stage,
            inputs=tuple(sorted((str(root / "a.input"), str(alias), str(cached)))),
            input_rosters=((str(owner), (str(alias),)),),
            resource_links=((str(alias), raw),),
        )
    elif case == "unsealed":
        files = (str(alias),)
        stage = replace(
            stage,
            inputs=(str(root / "a.input"), str(alias)),
            input_rosters=((str(owner), files),),
        )
    elif case == "duplicate":
        stage = replace(stage, resource_links=stage.resource_links * 2)
    elif case == "wrong-owner":
        stage = replace(stage, input_rosters=((str(root), (str(alias),)),))
    elif case == "output":
        stage = replace(stage, outputs=(str(alias),))
    with pytest.raises(bundle_module.ReleaseBundleError):
        run_publication_capture(_capture_plan(root, (stage,)), tmp_path / "journal")
    assert not (tmp_path / "journal").exists()


@pytest.mark.skipif(os.name != "posix", reason="POSIX descriptor link ownership")
@pytest.mark.parametrize(
    "case",
    [
        "cancelled-missing",
        "cancelled-file",
        "owner-escape-reentry",
        "empty-component",
        "dot-component",
        "trailing-separator",
        "absolute-empty-component",
    ],
)
def test_publication_capture_link_rejects_ambiguous_raw_target_spelling(
    tmp_path: Path, case: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    from dataclasses import replace

    from fep_lean.output.release_bundle._core import run_publication_capture

    root, owner, leaf, alias, stage = _linked_capture_stage(tmp_path)
    raw = {
        "cancelled-missing": "../canonical/missing/../style.txt",
        "cancelled-file": "../canonical/style.txt/../style.txt",
        "owner-escape-reentry": f"../../{owner.name}/canonical/style.txt",
        "empty-component": "../canonical//style.txt",
        "dot-component": "../canonical/./style.txt",
        "trailing-separator": "../canonical/style.txt/",
        "absolute-empty-component": f"{leaf.parent}//{leaf.name}",
    }[case]
    alias.unlink()
    alias.symlink_to(raw)
    stage = replace(stage, resource_links=((str(alias), raw),))
    monkeypatch.setattr(
        subprocess,
        "Popen",
        lambda *_args, **_kwargs: pytest.fail("invalid link launched a producer"),
    )
    with pytest.raises(bundle_module.ReleaseBundleError, match="spelling is invalid"):
        run_publication_capture(_capture_plan(root, (stage,)), tmp_path / "journal")
    assert not (tmp_path / "journal").exists()


@pytest.mark.skipif(os.name != "posix", reason="POSIX descriptor link ownership")
def test_publication_capture_rejects_byte_identical_referent_replacement(
    tmp_path: Path,
) -> None:
    from dataclasses import replace

    from fep_lean.output.release_bundle._core import run_publication_capture

    root, _owner, leaf, alias, stage = _linked_capture_stage(tmp_path)
    original_link = alias.lstat()
    original_leaf = leaf.stat()
    code = (
        "from pathlib import Path;import sys;"
        "leaf=Path(sys.argv[1]);output=Path(sys.argv[2]);"
        "replacement=leaf.with_name('replacement.txt');"
        "replacement.write_bytes(leaf.read_bytes());replacement.replace(leaf);"
        "output.write_bytes(b'a')"
    )
    stage = replace(
        stage, command=(sys.executable, "-c", code, str(leaf), str(root / "a.output"))
    )
    outcome = run_publication_capture(
        _capture_plan(root, (stage,)), tmp_path / "journal"
    )
    assert not outcome.complete
    assert alias.lstat() == original_link
    assert leaf.stat().st_ino != original_leaf.st_ino
    assert alias.read_bytes() == leaf.read_bytes() == b"owned style"
    record = json.loads(
        (tmp_path / "journal/attempts/000001-a/result.json").read_text()
    )
    assert record["inputs_before"][str(leaf)] == record["inputs_after"][str(leaf)]
    assert record["inputs_before"][str(alias)] != record["inputs_after"][str(alias)]
    assert any("changed" in error for error in outcome.errors)


@pytest.mark.skipif(os.name != "posix", reason="POSIX descriptor link ownership")
@pytest.mark.parametrize("mutation", ["link", "ancestor"])
def test_publication_capture_rejects_restored_link_or_owned_ancestor(
    tmp_path: Path, mutation: str
) -> None:
    from dataclasses import replace

    from fep_lean.output.release_bundle._core import run_publication_capture

    root, _owner, leaf, alias, stage = _linked_capture_stage(tmp_path)
    original = alias.lstat()
    code = (
        "from pathlib import Path;import os,sys,time;"
        "alias=Path(sys.argv[1]);output=Path(sys.argv[2]);"
    )
    if mutation == "link":
        code += (
            "saved=alias.parent/'saved';alias.rename(saved);"
            "alias.symlink_to('../canonical/style.txt');assert alias.read_bytes()==b'owned style';"
            "alias.unlink();saved.rename(alias);"
        )
    else:
        code += (
            "parent=alias.parent;saved=parent.with_name('saved');parent.rename(saved);"
            "parent.mkdir();(parent/'style.txt').symlink_to('../canonical/style.txt');"
            "assert (parent/'style.txt').read_bytes()==b'owned style';"
            "(parent/'style.txt').unlink();parent.rmdir();saved.rename(parent);"
        )
    code += "output.write_bytes(b'a')"
    stage = replace(
        stage, command=(sys.executable, "-c", code, str(alias), str(root / "a.output"))
    )
    outcome = run_publication_capture(
        _capture_plan(root, (stage,)), tmp_path / "journal"
    )
    assert not outcome.complete
    assert (
        alias.lstat().st_ino == original.st_ino
        and alias.read_bytes() == leaf.read_bytes()
    )
    record = json.loads(
        (tmp_path / "journal/attempts/000001-a/result.json").read_text()
    )
    assert (
        record["accepted"] is False
        and record["inputs_before"] != record["inputs_after"]
    )
    assert any("changed" in error for error in outcome.errors)


@pytest.mark.skipif(os.name != "posix", reason="POSIX descriptor link ownership")
def test_publication_capture_existing_cache_contents_preserve_link_snapshot(
    tmp_path: Path,
) -> None:
    from fep_lean.output.release_bundle._core import _capture_stage_snapshot

    _root, owner, _leaf, _alias, stage = _linked_capture_stage(tmp_path)
    cache = owner / ".venv/data"
    cache.parent.mkdir()
    cache.write_bytes(b"before")
    before = _capture_stage_snapshot(stage)
    cache.write_bytes(b"after")
    assert _capture_stage_snapshot(stage) == before


def test_publication_capture_resource_edits_invalidate_and_added_membership_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from dataclasses import replace

    from fep_lean.output.release_bundle._core import run_publication_capture

    root = tmp_path / "project"
    root.mkdir()
    stage = _capture_stage(root, "a")
    resources = root / "resources"
    resources.mkdir()
    style = resources / "theme.sty"
    style.write_text("original style")
    stage = replace(
        stage,
        inputs=(*stage.inputs, str(style)),
        input_rosters=((str(resources), (str(style),)),),
    )
    plan = _capture_plan(root, (stage,))
    journal = tmp_path / "journal"
    assert run_publication_capture(plan, journal).complete
    style.write_text("changed style")
    result = run_publication_capture(plan, journal, resume=True)
    assert result.complete and result.reused_stages == ()
    (resources / "new.bib").write_text("new bibliography")

    def forbid(*_args, **_kwargs):
        pytest.fail("expanded frozen roster launched a process")

    monkeypatch.setattr(subprocess, "Popen", forbid)
    with pytest.raises(bundle_module.ReleaseBundleError, match="membership changed"):
        run_publication_capture(plan, journal, resume=True)


def test_publication_capture_rejects_membership_expansion_during_producer(
    tmp_path: Path,
) -> None:
    from dataclasses import replace

    from fep_lean.output.release_bundle._core import run_publication_capture

    root = tmp_path / "project"
    root.mkdir()
    stage = _capture_stage(root, "a")
    resources = root / "resources"
    resources.mkdir()
    stage = replace(
        stage,
        input_rosters=((str(resources), ()),),
        command=(
            sys.executable,
            "-c",
            (
                "from pathlib import Path;import sys;"
                "Path(sys.argv[1]).write_bytes(Path(sys.argv[2]).read_bytes());"
                "Path(sys.argv[3]).write_text('newly consumed chapter')"
            ),
            stage.outputs[0],
            stage.inputs[0],
            str(resources / "new.md"),
        ),
    )
    result = run_publication_capture(
        _capture_plan(root, (stage,)), tmp_path / "journal"
    )
    assert not result.complete
    assert "capture input directory membership changed" in result.errors
    record = json.loads(
        (tmp_path / "journal/attempts/000001-a/result.json").read_text()
    )
    assert record["accepted"] is False and record["outputs"]


def test_publication_capture_failed_reuse_and_recapture_share_one_stage_budget(
    tmp_path: Path,
) -> None:
    from dataclasses import replace

    from fep_lean.output.release_bundle._core import run_publication_capture

    root = tmp_path / "project"
    root.mkdir()
    stage = _capture_stage(root, "a")
    stage = replace(
        stage,
        timeout_s=1.2,
        command=(
            sys.executable,
            "-c",
            (
                "from pathlib import Path;import sys,time;"
                "time.sleep(.8 if Path(sys.argv[3]).name.startswith('000003-') else 0);"
                "Path(sys.argv[2]).write_bytes(Path(sys.argv[1]).read_bytes())"
            ),
            stage.inputs[0],
            stage.outputs[0],
            "{attempt}",
        ),
        check_command=(
            sys.executable,
            "-c",
            (
                "from pathlib import Path;import sys,time;"
                "reuse=Path(sys.argv[1]).name.startswith('000002-');"
                "time.sleep(.8 if reuse else 0);raise SystemExit(2 if reuse else 0)"
            ),
            "{attempt}",
        ),
    )
    plan = _capture_plan(root, (stage,))
    journal = tmp_path / "journal"
    assert run_publication_capture(plan, journal).complete
    started = time.monotonic()
    rejected = run_publication_capture(plan, journal, resume=True)
    elapsed = time.monotonic() - started
    assert not rejected.complete and rejected.failed_stage == "a"
    assert elapsed < 1.55, "recapture reset the stage's finite budget"
    retained = [
        json.loads(p.read_text())
        for p in sorted(journal.glob("attempts/*/result.json"))
    ]
    assert retained[-2]["mode"] == "reuse" and not retained[-2]["accepted"]
    assert retained[-1]["mode"] == "capture" and retained[-1]["timed_out"]


def test_publication_capture_unowned_attempt_file_never_receives_acceptance(
    tmp_path: Path,
) -> None:
    from dataclasses import replace

    from fep_lean.output.release_bundle._core import run_publication_capture

    root = tmp_path / "project"
    root.mkdir()
    stage = _capture_stage(root, "a")
    stage = replace(
        stage,
        command=(
            sys.executable,
            "-c",
            (
                "from pathlib import Path;import sys;"
                "Path(sys.argv[2]).write_bytes(Path(sys.argv[1]).read_bytes());"
                "(Path(sys.argv[3])/'undeclared.txt').write_text('unowned')"
            ),
            stage.inputs[0],
            stage.outputs[0],
            "{attempt}",
        ),
    )
    result = run_publication_capture(
        _capture_plan(root, (stage,)), tmp_path / "journal"
    )
    assert not result.complete
    assert "capture attempt has unexpected files or symlinks" in result.errors


def test_publication_capture_reuse_check_mutation_cannot_rewrite_accepted_history(
    tmp_path: Path,
) -> None:
    from dataclasses import replace

    from fep_lean.output.release_bundle._core import run_publication_capture

    root = tmp_path / "project"
    root.mkdir()
    stage = _capture_stage(root, "a")
    stage = replace(
        stage,
        check_command=(
            sys.executable,
            "-c",
            (
                "from pathlib import Path;import sys;"
                "output=Path(sys.argv[2]);"
                "output.write_bytes(b'mutated') if Path(sys.argv[1]).name.startswith('000002-') else None"
            ),
            "{attempt}",
            stage.outputs[0],
        ),
    )
    plan = _capture_plan(root, (stage,))
    journal = tmp_path / "journal"
    assert run_publication_capture(plan, journal).complete
    prior = (journal / "attempts/000001-a/artifacts/0000.bin").read_bytes()
    recaptured = run_publication_capture(plan, journal, resume=True)
    assert recaptured.complete and recaptured.reused_stages == ()
    record = json.loads((journal / "attempts/000002-a/result.json").read_text())
    assert record["accepted"] is False
    assert (
        "capture reuse check changed previously accepted artifacts" in record["errors"]
    )
    assert (journal / "attempts/000001-a/artifacts/0000.bin").read_bytes() == prior
    assert Path(stage.outputs[0]).read_bytes() == prior


def test_publication_capture_timeout_journal_preserves_raw_partial_streams(
    tmp_path: Path,
) -> None:
    from dataclasses import replace

    from fep_lean.output.release_bundle._core import run_publication_capture

    root = tmp_path / "project"
    root.mkdir()
    stage = _capture_stage(root, "a")
    stdout, stderr = b"raw\r\n\xe2", b"error\r\n\xff"
    stage = replace(
        stage,
        timeout_s=0.7,
        command=(
            sys.executable,
            "-c",
            f"import os,time;os.write(1,{stdout!r});os.write(2,{stderr!r});time.sleep(30)",
        ),
    )
    journal = tmp_path / "journal"
    result = run_publication_capture(_capture_plan(root, (stage,)), journal)
    assert not result.complete
    attempt = journal / "attempts/000001-a"
    assert (attempt / "stdout.log").read_bytes() == stdout
    assert (attempt / "stderr.log").read_bytes() == stderr
    record = json.loads((attempt / "result.json").read_text())
    assert record["timed_out"] is True and record["accepted"] is False
    assert record["streams"] == {
        "stdout.log": hashlib.sha256(stdout).hexdigest(),
        "stderr.log": hashlib.sha256(stderr).hexdigest(),
    }


@pytest.mark.parametrize("mutation", ["add", "remove"])
def test_publication_capture_final_snapshot_rechecks_directory_membership_after_reads(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    from dataclasses import replace

    from fep_lean.output.release_bundle import _core

    root = tmp_path / "project"
    root.mkdir()
    stage = _capture_stage(root, "a")
    resources = root / "resources"
    resources.mkdir()
    style = resources / "theme.sty"
    style.write_bytes(b"consumed style")
    stage = replace(
        stage,
        inputs=(*stage.inputs, str(style)),
        input_rosters=((str(resources), (str(style),)),),
    )
    original = _core._capture_regular_file
    reads = 0

    def race(path: Path) -> bytes:
        nonlocal reads
        data = original(path)
        if path == style:
            reads += 1
            if reads == 3:
                if mutation == "add":
                    (resources / "late-added.css").write_text("expanded roster")
                else:
                    style.unlink()
        return data

    monkeypatch.setattr(_core, "_capture_regular_file", race)
    journal = tmp_path / "journal"
    result = _core.run_publication_capture(_capture_plan(root, (stage,)), journal)
    assert reads == 3 and not result.complete
    assert "capture inputs could not be rechecked after the attempt" in result.errors
    record = json.loads((journal / "attempts/000001-a/result.json").read_text())
    assert record["accepted"] is False


def test_publication_capture_plan_owns_every_render_asset_and_generated_collection_cache(
    tmp_path: Path,
) -> None:
    from fep_lean.output.release_bundle._core import plan_publication_capture
    from fep_lean.output.rendering import MANUSCRIPT_ASSETS

    template = tmp_path / "template"
    renderer = template / "scripts/pipeline/stage_03_render.py"
    renderer.parent.mkdir(parents=True)
    renderer.write_text("# explicit template\n")
    plan = plan_publication_capture(PROJ, template_root=template)
    render = next(s for s in plan.stages if s.name == "render")
    bundle = next(s for s in plan.stages if s.name == "bundle")
    for source, destination in MANUSCRIPT_ASSETS.values():
        assert str(PROJ / source) in render.inputs
        resolved = str(PROJ / "output/manuscript" / destination)
        assert resolved in render.outputs and resolved in bundle.inputs
    for name in ("config.yaml", "preamble.md", "references.bib"):
        assert str(PROJ / "manuscript" / name) in render.inputs
        resolved = str(PROJ / "output/manuscript" / name)
        assert resolved in render.outputs and resolved in bundle.inputs
    cache = str(PROJ / "output/.cache/tests_collected.json")
    assert cache in render.outputs and cache not in render.inputs
    assert cache in bundle.inputs


def test_publication_capture_real_renderer_asset_source_mutation_rejects(
    tmp_path: Path,
) -> None:
    from fep_lean.output.release_bundle._core import (
        PublicationCaptureStage,
        run_publication_capture,
    )
    from fep_lean.output.rendering import MANUSCRIPT_ASSETS

    root = tmp_path / "project"
    manuscript = root / "manuscript"
    manuscript.mkdir(parents=True)
    chapter = manuscript / "01_chapter.md"
    chapter.write_text("A disposable chapter.\n")
    origins = []
    destinations = [str(root / "output/manuscript/01_chapter.md")]
    for source, destination in MANUSCRIPT_ASSETS.values():
        origin = root / source
        origin.parent.mkdir(parents=True, exist_ok=True)
        origin.write_bytes(b"owned fixture asset")
        origins.append(str(origin))
        destinations.append(str(root / "output/manuscript" / destination))
    program = (
        "from pathlib import Path;import sys;"
        "from fep_lean.output.rendering import render_manuscript;"
        "root=Path(sys.argv[1]);render_manuscript(root/'manuscript',root/'output/manuscript',{});"
        "Path(sys.argv[2]).write_bytes(b'asset changed during render')"
    )
    stage = PublicationCaptureStage(
        "render",
        (),
        (str(chapter), *origins),
        tuple(destinations),
        (sys.executable, "-c", program, str(root), origins[-1]),
        (sys.executable, "-c", "pass"),
        # This successful producer imports the real package and renderer;
        # deadline/cleanup controls have separate, deliberately short bounds.
        30,
    )
    result = run_publication_capture(
        _capture_plan(root, (stage,)), tmp_path / "journal"
    )
    assert not result.complete
    assert "capture inputs changed during execution or validation" in result.errors


def test_publication_capture_first_run_generated_cache_is_an_output_then_consumed_input(
    tmp_path: Path,
) -> None:
    from dataclasses import replace

    from fep_lean.output.release_bundle._core import run_publication_capture

    root = tmp_path / "project"
    root.mkdir()
    render = _capture_stage(root, "render")
    bundle = _capture_stage(root, "bundle", ("render",))
    cache = root / "output/.cache/tests_collected.json"
    render = replace(
        render,
        outputs=(*render.outputs, str(cache)),
        command=(
            sys.executable,
            "-c",
            (
                "from pathlib import Path;import sys;"
                "Path(sys.argv[2]).write_bytes(Path(sys.argv[1]).read_bytes());"
                "cache=Path(sys.argv[3]);cache.parent.mkdir(parents=True,exist_ok=True);"
                "cache.write_bytes(b'generated cache fixture')"
            ),
            render.inputs[0],
            render.outputs[0],
            str(cache),
        ),
    )
    bundle = replace(bundle, inputs=(*bundle.inputs, str(cache)))
    assert not cache.exists()
    plan = _capture_plan(root, (render, bundle))
    journal = tmp_path / "journal"
    assert run_publication_capture(plan, journal).complete
    first = json.loads((journal / "attempts/000001-render/result.json").read_text())
    assert str(cache) not in first["prior_outputs"]
    assert str(cache) in first["outputs"]
    consumed = json.loads((journal / "attempts/000002-bundle/result.json").read_text())
    assert str(cache) in consumed["inputs_before"]
    assert run_publication_capture(plan, journal, resume=True).reused_stages == (
        "render",
        "bundle",
    )
    cache.write_bytes(b"changed generated cache")
    assert run_publication_capture(plan, journal, resume=True).reused_stages == ()


@pytest.mark.parametrize("swap", ["final-file", "ancestor"])
def test_publication_capture_descriptor_reads_refuse_real_symlink_swaps(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, swap: str
) -> None:
    from fep_lean.output.release_bundle import _core

    directory = tmp_path / "declared"
    directory.mkdir()
    source = directory / "source.txt"
    source.write_bytes(b"declared bytes")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "source.txt").write_bytes(b"synthetic outside")
    original_open = os.open
    swapped = False

    def race(path, flags, *args, **kwargs):
        nonlocal swapped
        if not swapped and path == (
            "source.txt" if swap == "final-file" else "declared"
        ):
            swapped = True
            if swap == "final-file":
                source.rename(directory / "retained-source.txt")
                source.symlink_to(outside / "source.txt")
            else:
                directory.rename(tmp_path / "retained-directory")
                directory.symlink_to(outside, target_is_directory=True)
        return original_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", race)
    with pytest.raises(OSError):
        _core._capture_regular_file(source)
    assert swapped
    assert (outside / "source.txt").read_bytes() == b"synthetic outside"


def test_publication_capture_descriptor_writes_refuse_ancestor_swap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from fep_lean.output.release_bundle import _core

    parent = tmp_path / "journal"
    parent.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    original_open = os.open
    swapped = False

    def race(path, flags, *args, **kwargs):
        nonlocal swapped
        if path == "journal" and not swapped:
            swapped = True
            parent.rename(tmp_path / "retained-journal")
            parent.symlink_to(outside, target_is_directory=True)
        return original_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", race)
    with pytest.raises(OSError):
        _core._capture_new_file(parent / "receipt.json", b"retained evidence")
    assert swapped and not tuple(outside.iterdir())


def test_publication_capture_descriptor_read_refuses_fifo_swap_before_blocking(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from fep_lean.output.release_bundle import _core

    source = tmp_path / "source.txt"
    source.write_bytes(b"regular source")
    original_open = os.open
    swapped = False

    def race(path, flags, *args, **kwargs):
        nonlocal swapped
        if path == "source.txt" and not swapped:
            swapped = True
            source.rename(tmp_path / "retained-source.txt")
            os.mkfifo(source)
            # Failure here avoids an unbounded test hang while still opening
            # the real swapped FIFO under the product's actual descriptor flags.
            assert flags & os.O_NONBLOCK
        return original_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", race)
    with pytest.raises(bundle_module.ReleaseBundleError, match="regular file"):
        _core._capture_regular_file(source)
    assert swapped


def test_publication_capture_unsupported_platform_refuses_before_journal_or_process(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from fep_lean.output.release_bundle import _core

    root = tmp_path / "project"
    root.mkdir()
    plan = _capture_plan(root, (_capture_stage(root, "a"),))
    monkeypatch.setattr(_core, "os", SimpleNamespace(name="nt"))

    def forbid(*_args, **_kwargs):
        pytest.fail("unsupported capture platform launched a process")

    monkeypatch.setattr(subprocess, "Popen", forbid)
    journal = tmp_path / "journal"
    with pytest.raises(bundle_module.ReleaseBundleError, match="requires POSIX"):
        _core.run_publication_capture(plan, journal)
    assert not journal.exists()
