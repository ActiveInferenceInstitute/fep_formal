"""Retain and check the explicit H3 closure around an accepted package archive.

Archive validation is read-only. Scientific reproduction has its own command
and cannot start before the native, frozen-protocol and final-review gates pass.
"""

from __future__ import annotations

import argparse
import contextlib
import gzip
import hashlib
import io
import json
import math
import os
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
import zlib
from pathlib import Path, PurePosixPath
from typing import Any, cast

from run_synthetic import (
    BASE,
    PROTOCOL_SHA256,
    STUDY_SOURCE_FILES,
    AttemptFiles,
    Inputs,
    StudyRejection,
    frozen_protocol,
    load_export,
    parameters,
    replay_synthetic_attempt,
    require,
)

from fep_formal.output.release_bundle import validate_release_bundle
from fep_formal.output.release_bundle._core import _capture_parent_fd
from fep_formal.output.release_bundle._validate import _read_archive
from fep_formal.verification._jsonutil import load_strict_json
from fep_formal.verification._subprocess import run_process_group

PRODUCERS = (*STUDY_SOURCE_FILES, BASE + "bundle_study.py")
MAX_ARCHIVE_BYTES = 512 * 1024 * 1024
MAX_TOTAL_BYTES = 2 * 1024 * 1024 * 1024
MANIFEST = "H3-MANIFEST.json"
PACKAGE = "package.tar.gz"
REVIEW_ROLES = {"lean", "domain", "statistical"}
METADATA_FIELDS = {
    "descriptor",
    "package_project_path",
    "protocol_sha256",
    "source_sha256",
}
H2_TERMINAL = (
    "specs/done/horizon-2-smooth-stochastic/readiness/terminal-acceptance.json"
)
H2_PACKET = "specs/comprehensive-science-improvement/evidence/h2-capture-20260930-r2/"


def canonical(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode()


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def check_output_owner(files: AttemptFiles) -> None:
    """Reopen every lexical directory without following links and match our owner."""
    try:
        current = AttemptFiles(files.directory)
    except OSError as error:
        raise StudyRejection(
            "owned output ancestor redirected or unavailable"
        ) from error
    try:
        require(
            (current.identity.st_dev, current.identity.st_ino)
            == (files.identity.st_dev, files.identity.st_ino),
            "owned output directory replaced",
        )
    finally:
        current.close()


def safe_name(name: Any) -> str:
    require(
        type(name) is str
        and bool(name)
        and "\\" not in name
        and "\x00" not in name
        and not name.startswith("/")
        and all(part not in ("", ".", "..") for part in name.split("/")),
        "unsafe archive/reference path",
    )
    return cast(str, name)


def reference(value: Any) -> tuple[str, str]:
    require(
        type(value) is dict and set(value) == {"path", "sha256"},
        "typed reference required",
    )
    name = safe_name(value["path"])
    sha = value["sha256"]
    require(
        type(sha) is str
        and len(sha) == 64
        and all(c in "0123456789abcdef" for c in sha),
        "reference digest must be SHA-256",
    )
    return name, sha


def file_identity(value: os.stat_result) -> tuple[int, ...]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def archive_buffer(path: Path) -> tuple[bytes, tuple[int, ...]]:
    """Bound a regular descriptor before reading; never follow a FIFO or link."""
    require(
        path.is_absolute() and ".." not in path.parts,
        "absolute canonical archive required",
    )
    require(not any(p.is_symlink() for p in (path, *path.parents)), "symlink archive")
    directory = _capture_parent_fd(path)
    fd = None
    try:
        fd = os.open(
            path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory
        )
        before = os.fstat(fd)
        require(
            stat.S_ISREG(before.st_mode) and before.st_size <= MAX_ARCHIVE_BYTES,
            "nonregular or oversized archive",
        )
        with os.fdopen(fd, "rb") as stream:
            fd = None
            raw = stream.read(MAX_ARCHIVE_BYTES + 1)
            after = os.fstat(stream.fileno())
        require(
            file_identity(before) == file_identity(after)
            and len(raw) == before.st_size,
            "archive changed while reading",
        )
        lexical = os.stat(path.name, dir_fd=directory, follow_symlinks=False)
        require(
            file_identity(lexical) == file_identity(after), "archive path redirected"
        )
        return raw, file_identity(before)
    finally:
        if fd is not None:
            os.close(fd)
        os.close(directory)


def retained_package(raw: bytes, *, root: Path | None) -> dict[str, bytes]:
    """Validate a captured buffer, so a live path cannot redirect validation."""
    with tempfile.TemporaryDirectory(prefix="h3-package-check-") as temporary:
        path = Path(temporary).resolve() / PACKAGE
        path.write_bytes(raw)
        result = validate_release_bundle(path, project_root=root)
        require(
            result.claim_ready if root is not None else result.valid,
            "contained package rejected: " + "; ".join(result.errors),
        )
        contents, _, _, errors = _read_archive(path)
        require(not errors, "contained package could not be read")
        return contents


def synthetic_attempt(
    inputs: Inputs,
    name: str,
    expected_sources: dict[str, str],
    protocol: dict[str, Any],
    native_parameters_raw: dict[str, Any],
) -> dict[str, Any]:
    record = inputs.json(name)
    require(
        type(record.get("schema_version")) is int
        and record["schema_version"] == 1
        and record.get("gate") == "H3.6S"
        and record.get("protocol_sha256") == PROTOCOL_SHA256
        and record.get("study_id") == protocol["study_id"]
        and record.get("source_before") == expected_sources
        and record.get("source_after") == expected_sources
        and record.get("execution_environment")
        == protocol["synthetic_acceptance"]["execution_environment"]
        and record.get("empirical_gate") == "governed_no_go",
        "synthetic attempt is incomplete, stale or outside the frozen scope",
    )
    require(
        type(record.get("accepted")) is bool and record.get("failure") is None,
        "execution failure is retained but cannot be promoted to a reproduced primary result",
    )
    require(
        set(record) - {"failure"}
        == {
            "schema_version",
            "gate",
            "study_id",
            "protocol_sha256",
            "source_before",
            "source_after",
            "execution_environment",
            "empirical_gate",
            "input_negative_controls",
            "exact_controls",
            "calibration",
            "recovery",
            "control",
            "accepted",
            "decision",
            "artifact_sha256",
            "retained_artifact_sha256",
            "retained_output_issues",
        },
        "synthetic result field roster incomplete or unknown",
    )
    parent = PurePosixPath(name).parent

    def retained_array(relative: str) -> bytes:
        return inputs.read((parent / safe_name(relative)).as_posix())

    replay_synthetic_attempt(protocol, native_parameters_raw, record, retained_array)
    return record


def expected_claims(
    protocol: dict[str, Any], proof: dict[str, Any], attempt: dict[str, Any]
) -> dict[str, Any]:
    scope = protocol["claim_matrix"]
    return {
        "proved": {
            "scope": scope["proved"],
            "native_witnesses": proof["native_witnesses"],
        },
        "numerical": {
            "scope": scope["numerical"],
            "accepted": attempt["accepted"],
            "decision": attempt["decision"],
        },
        **{
            key: scope[key]
            for key in ("empirical", "causal", "physical_thermodynamics", "excluded")
        },
    }


def frozen_history(inputs: Inputs) -> None:
    """Retain the immutable prerequisite observation, without rebinding its epoch."""
    freeze = inputs.json(BASE + "freeze.json")
    terminal = inputs.json(H2_TERMINAL, expected=freeze["h2_terminal_at_freeze_sha256"])
    require(
        terminal.get("decision") == "accepted",
        "frozen H2 prerequisite was not accepted",
    )
    seen: set[str] = set()

    def walk(value: Any, depth: int = 0) -> None:
        require(
            depth <= 32 and len(seen) <= 1024, "historical reference closure too large"
        )
        if type(value) is dict:
            if set(value) == {"path", "sha256"}:
                name, sha = reference(value)
                if name.startswith(H2_PACKET):
                    raw = inputs.read(name, expected=sha)
                    if name not in seen and name.endswith(".json"):
                        seen.add(name)
                        walk(load_strict_json(raw.decode()), depth + 1)
            else:
                for child in value.values():
                    walk(child, depth + 1)
        elif type(value) is list:
            for child in value:
                walk(child, depth + 1)

    walk(terminal)


def collect(
    root: Path, descriptor_name: str, *, live_package: bool = True
) -> tuple[dict[str, bytes], dict[str, Any], dict[str, str]]:
    """Traverse only declared references after all substantive acceptance gates."""
    require(sys.version_info[:2] == (3, 14), "Python 3.14 validator required")
    inputs = Inputs(root)
    root = inputs.root
    protocol = frozen_protocol(inputs)
    descriptor_name = safe_name(descriptor_name)
    # Read descriptor in a separate reader until the execution source map has
    # been replayed; it was not a synthetic producer input.
    descriptor_inputs = Inputs(root)
    descriptor = descriptor_inputs.json(descriptor_name)
    require(
        type(descriptor.get("schema_version")) is int
        and descriptor["schema_version"] == 1
        and descriptor.get("kind") == "h3-study-bundle-inputs"
        and set(descriptor)
        == {
            "schema_version",
            "kind",
            "package",
            "export",
            "audit",
            "proof_review",
            "synthetic_attempt",
            "claim_matrix",
            "final_reviews",
        },
        "study bundle descriptor schema/roster",
    )
    refs = {
        key: reference(descriptor[key])
        for key in (
            "package",
            "export",
            "audit",
            "proof_review",
            "synthetic_attempt",
            "claim_matrix",
        )
    }
    require(
        len({name for name, _ in refs.values()}) == len(refs),
        "duplicate input references",
    )
    for key in ("export", "proof_review", "synthetic_attempt", "claim_matrix"):
        require(
            refs[key][0].startswith(BASE + "output/"),
            "study evidence must belong to the H3 output roster",
        )
    require(
        refs["package"][0].startswith("output/"),
        "package archive must belong to project output",
    )
    # Load these hashes before the export gate; the original executor's source
    # map did not contain an extra descriptor or package archive.
    for key in ("export", "audit", "proof_review"):
        name, sha = refs[key]
        descriptor_inputs.read(name, expected=sha)
    raw_parameters = load_export(
        inputs, refs["export"][0], refs["audit"][0], refs["proof_review"][0]
    )
    parameters(raw_parameters, protocol)
    expected_sources = inputs.hashes()
    attempt_name, attempt_sha = refs["synthetic_attempt"]
    attempt = synthetic_attempt(
        inputs, attempt_name, expected_sources, protocol, raw_parameters
    )
    require(
        inputs.states[attempt_name].sha256 == attempt_sha,
        "synthetic receipt descriptor mismatch",
    )
    # All subsequent reads are closure inputs, not historical execution inputs.
    frozen_history(inputs)
    inputs.read(
        descriptor_name, expected=descriptor_inputs.states[descriptor_name].sha256
    )
    producers = {name: digest(inputs.read(name)) for name in PRODUCERS}
    package_name, package_sha = refs["package"]
    package_raw, package_identity = archive_buffer(root / package_name)
    require(digest(package_raw) == package_sha, "package archive descriptor mismatch")
    package_contents = retained_package(
        package_raw, root=root if live_package else None
    )
    proof = inputs.json(refs["proof_review"][0])
    claims_name, claims_sha = refs["claim_matrix"]
    claims = inputs.json(claims_name, expected=claims_sha)
    native_export = inputs.json(refs["export"][0])
    bindings = {
        "protocol_sha256": PROTOCOL_SHA256,
        "export_sha256": refs["export"][1],
        "audit_sha256": refs["audit"][1],
        "proof_review_sha256": refs["proof_review"][1],
        "synthetic_attempt_sha256": attempt_sha,
        "package_sha256": package_sha,
        "producer_sha256": producers,
        "source_sha256": native_export["source_after"],
    }
    require(
        type(claims.get("schema_version")) is int
        and claims["schema_version"] == 1
        and claims.get("kind") == "h3-final-claim-matrix"
        and all(claims.get(key) == value for key, value in bindings.items())
        and claims.get("claims") == expected_claims(protocol, proof, attempt),
        "final claim matrix changed or exceeds proved/synthetic scope",
    )
    reviews = descriptor["final_reviews"]
    require(
        type(reviews) is list and len(reviews) == 3,
        "three final claim reviews required",
    )
    identities, roles, paths = set(), set(), set()
    for ref in reviews:
        name, sha = reference(ref)
        require(
            name.startswith(BASE + "output/") and name not in paths,
            "unowned or duplicate final review",
        )
        paths.add(name)
        review = inputs.json(name, expected=sha)
        require(
            type(review.get("schema_version")) is int
            and review["schema_version"] == 1
            and review.get("decision") == "approve"
            and review.get("independent_of_authorship") is True
            and review.get("claim_matrix_sha256") == claims_sha
            and all(review.get(key) == value for key, value in bindings.items())
            and type(review.get("reviewer_id")) is str
            and bool(review["reviewer_id"])
            and type(review.get("role")) is str,
            "final claim review absent or stale",
        )
        identities.add(review["reviewer_id"])
        roles.add(review["role"])
    require(
        len(identities) == 3 and roles == REVIEW_ROLES,
        "independent final claim reviewer roster",
    )
    inputs.stable()
    descriptor_inputs.stable()
    require(
        archive_buffer(root / package_name) == (package_raw, package_identity),
        "package archive changed",
    )
    supplement: dict[str, bytes] = {}
    for name, state in inputs.states.items():
        if name in package_contents:
            require(
                package_contents[name] == state.bytes,
                "contradictory package/study overlap: " + name,
            )
        else:
            require(
                name == H2_TERMINAL
                or name.startswith(
                    (BASE, "specs/comprehensive-science-improvement/evidence/")
                ),
                "required current evidence is absent from accepted package: " + name,
            )
            supplement[name] = state.bytes
    payload = {
        PACKAGE: package_raw,
        **{"study/" + name: raw for name, raw in supplement.items()},
    }
    return (
        payload,
        {
            "descriptor": {
                "path": descriptor_name,
                "sha256": digest(inputs.states[descriptor_name].bytes),
            },
            "package_project_path": package_name,
            "protocol_sha256": PROTOCOL_SHA256,
            "source_sha256": inputs.hashes(),
        },
        inputs.hashes(),
    )


def archive_bytes(
    payload: dict[str, bytes], metadata: dict[str, Any], *, epoch: int = 0
) -> bytes:
    require(type(epoch) is int and 0 <= epoch <= 0xFFFFFFFF, "invalid archive epoch")
    require(set(metadata) == METADATA_FIELDS, "archive metadata roster")
    require(
        MANIFEST not in payload and PACKAGE in payload,
        "reserved or missing package archive member",
    )
    require(
        sum(len(raw) for raw in payload.values()) <= MAX_TOTAL_BYTES,
        "oversized archive payload",
    )
    require(len(payload) <= 20_000, "too many archive members")
    manifest = {
        "schema_version": 1,
        "kind": "h3-study-evidence-bundle",
        "source_date_epoch": epoch,
        **metadata,
        "members": [
            {"path": safe_name(name), "sha256": digest(raw), "size": len(raw)}
            for name, raw in sorted(payload.items())
        ],
    }
    contents = {**payload, MANIFEST: canonical(manifest)}
    output = io.BytesIO()
    with (
        gzip.GzipFile(
            fileobj=output, mode="wb", filename="", compresslevel=9, mtime=epoch
        ) as zipped,
        tarfile.open(fileobj=zipped, mode="w|", format=tarfile.USTAR_FORMAT) as archive,
    ):
        for name, raw in sorted(contents.items()):
            info = tarfile.TarInfo(safe_name(name))
            info.mode, info.uid, info.gid = 0o644, 0, 0
            info.uname = info.gname = ""
            info.mtime, info.size = epoch, len(raw)
            archive.addfile(info, io.BytesIO(raw))
    result = output.getvalue()
    require(len(result) <= MAX_ARCHIVE_BYTES, "oversized compressed archive")
    return result


def read_study_archive(raw: bytes) -> tuple[dict[str, bytes], dict[str, Any]]:
    require(len(raw) <= MAX_ARCHIVE_BYTES, "oversized compressed archive")
    with tempfile.TemporaryDirectory(prefix="h3-archive-check-") as temporary:
        workspace = Path(temporary).resolve()
        expanded = workspace / "payload.tar"
        decoder = zlib.decompressobj(16 + zlib.MAX_WBITS)
        total = 0
        try:
            with expanded.open("xb") as stream:
                for start in range(0, len(raw), 65536):
                    segment = raw[start : start + 65536]
                    while segment:
                        data = decoder.decompress(segment, 1024 * 1024)
                        segment = decoder.unconsumed_tail
                        total += len(data)
                        require(
                            total <= MAX_TOTAL_BYTES + 20_000 * 1024 + 10240,
                            "oversized decompressed archive",
                        )
                        stream.write(data)
                        if decoder.eof:
                            require(
                                not decoder.unused_data
                                and not segment
                                and start + 65536 >= len(raw),
                                "trailing bytes or concatenated gzip member",
                            )
                            break
                require(decoder.eof, "truncated gzip stream")
        except zlib.error as error:
            raise StudyRejection("invalid gzip CRC or stream: " + str(error)) from error
        path = workspace / "study.tar.gz"
        path.write_bytes(raw)
        contents, members, epoch, errors = _read_archive(path)
        require(
            not errors and bool(members), "study archive rejected: " + "; ".join(errors)
        )
        last = members[-1]
        payload_end = last.offset_data + ((last.size + 511) // 512) * 512
        expected_size = ((payload_end + 1024 + 10239) // 10240) * 10240
        require(total == expected_size, "undeclared tar trailer payload")
        with expanded.open("rb") as stream:
            stream.seek(payload_end)
            require(not any(stream.read()), "nonzero tar trailer payload")
    require(not errors, "study archive rejected: " + "; ".join(errors))
    require(
        tuple(m.name for m in members) == tuple(sorted(contents)),
        "unordered or duplicate study archive",
    )
    for member in members:
        safe_name(member.name)
        require(
            member.mode == 0o644
            and member.uid == member.gid == 0
            and member.uname == member.gname == ""
            and member.mtime == epoch
            and not member.pax_headers
            and not member.linkname,
            "nondeterministic archive member metadata",
        )
    require(MANIFEST in contents, "study manifest absent")
    manifest = load_strict_json(contents[MANIFEST].decode())
    require(
        type(manifest) is dict
        and canonical(manifest) == contents[MANIFEST]
        and type(manifest.get("schema_version")) is int
        and manifest["schema_version"] == 1
        and manifest.get("kind") == "h3-study-evidence-bundle"
        and type(manifest.get("source_date_epoch")) is int
        and manifest.get("source_date_epoch") == epoch,
        "study manifest schema/canonical encoding",
    )
    records = manifest.get("members")
    require(
        set(manifest)
        == METADATA_FIELDS | {"schema_version", "kind", "source_date_epoch", "members"},
        "manifest field roster",
    )
    require(
        type(records) is list
        and all(
            type(row) is dict
            and set(row) == {"path", "sha256", "size"}
            and type(row.get("size")) is int
            for row in records
        ),
        "typed manifest member roster",
    )
    expected = []
    for name, data in sorted(contents.items()):
        if name != MANIFEST:
            require(
                name == PACKAGE or name.startswith("study/"),
                "undeclared outer namespace",
            )
            expected.append({"path": name, "sha256": digest(data), "size": len(data)})
    require(
        records == expected and PACKAGE in contents,
        "study manifest hash/size/roster mismatch",
    )
    return {name: data for name, data in contents.items() if name != MANIFEST}, cast(
        dict[str, Any], manifest
    )


def hydrate(
    payload: dict[str, bytes], metadata: dict[str, Any], directory: Path
) -> None:
    package = retained_package(payload[PACKAGE], root=None)
    project: dict[str, bytes] = dict(package)
    for name, raw in payload.items():
        if name != PACKAGE:
            relative = safe_name(name.removeprefix("study/"))
            require(
                relative not in project or project[relative] == raw,
                "contradictory extracted overlap",
            )
            project[relative] = raw
    package_name = safe_name(metadata["package_project_path"])
    require(package_name not in project, "package archive overlaps extracted source")
    project[package_name] = payload[PACKAGE]
    files = AttemptFiles(directory, create=True)
    try:
        for name, raw in sorted(project.items()):
            parts = PurePosixPath(safe_name(name)).parts
            parent = os.dup(files.fd)
            try:
                for part in parts[:-1]:
                    with contextlib.suppress(FileExistsError):
                        os.mkdir(part, mode=0o700, dir_fd=parent)
                    child = os.open(
                        part,
                        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                        dir_fd=parent,
                    )
                    os.close(parent)
                    parent = child
                fd = os.open(
                    parts[-1],
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                    0o600,
                    dir_fd=parent,
                )
                with os.fdopen(fd, "wb") as stream:
                    stream.write(raw)
                    stream.flush()
                    os.fsync(stream.fileno())
            finally:
                os.close(parent)
        for name, raw in project.items():
            require(
                archive_buffer(directory / name)[0] == raw,
                "extracted source changed: " + name,
            )
    finally:
        files.close()


def validate(raw: bytes, *, project_root: Path | None = None) -> dict[str, Any]:
    payload, metadata = read_study_archive(raw)
    with tempfile.TemporaryDirectory(prefix="h3-contained-source-") as temporary:
        root = Path(temporary).resolve() / "project"
        hydrate(payload, metadata, root)
        descriptor, _ = reference(metadata["descriptor"])
        expected_payload, expected_metadata, _ = collect(
            root, descriptor, live_package=False
        )
        require(
            payload == expected_payload
            and all(
                metadata.get(key) == value for key, value in expected_metadata.items()
            ),
            "archive is not exactly the typed evidence closure",
        )
    if project_root is not None:
        current, live_metadata, _ = collect(project_root, descriptor)
        require(
            payload == current
            and all(metadata.get(key) == value for key, value in live_metadata.items()),
            "archive differs from final source",
        )
    return {
        "schema_version": 1,
        "kind": "h3-study-bundle-validation",
        "valid": True,
        "source_bound": project_root is not None,
        "claim_ready": False,
        "archive_sha256": digest(raw),
        "protocol_sha256": PROTOCOL_SHA256,
        "boundary": "Contained native/review/synthetic evidence checked; fresh reproduction and publication remain separate.",
    }


def assemble(
    root: Path, descriptor: str, output: Path, *, timeout: float = 600
) -> dict[str, Any]:
    require(os.name == "posix", "POSIX descriptor custody required")
    require(
        type(timeout) in (int, float) and math.isfinite(timeout) and timeout > 0,
        "finite positive assembly budget",
    )
    require(
        output.is_absolute() and ".." not in output.parts,
        "absolute canonical attempt path",
    )
    files = AttemptFiles(output, create=True)
    start = time.monotonic()
    result: dict[str, Any] = {
        "schema_version": 1,
        "kind": "h3-study-bundle-attempt",
        "accepted": False,
    }
    source_guard: Inputs | None = None
    package_identity: tuple[bytes, tuple[int, ...]] | None = None
    try:
        payload, metadata, sources = collect(root, descriptor)
        source_guard = Inputs(root)
        for name, sha in sources.items():
            source_guard.read(name, expected=sha)
        package_identity = archive_buffer(root / metadata["package_project_path"])
        require(
            package_identity[0] == payload[PACKAGE], "package changed before assembly"
        )
        raw = archive_bytes(payload, metadata)
        files.write_new("study.tar.gz", raw)
        validation = validate(raw, project_root=root)
        require(
            archive_buffer(output / "study.tar.gz")[0] == raw,
            "retained archive changed",
        )
        require(time.monotonic() - start < timeout, "study assembly deadline expired")
        result.update(
            {
                "accepted": True,
                "archive_sha256": digest(raw),
                "source_sha256": sources,
                "validation": validation,
            }
        )
    except BaseException as error:
        result["failure"] = {"type": type(error).__name__, "reason": str(error)}
        raise
    finally:
        result["duration_seconds"] = time.monotonic() - start
        try:
            if result["accepted"] and time.monotonic() - start >= timeout:
                result["accepted"] = False
                result["failure"] = {
                    "type": "StudyRejection",
                    "reason": "assembly deadline expired before seal",
                }
            sealed_bytes = canonical(result)
            files.receipt(sealed_bytes)
            if result["accepted"]:
                try:
                    check_output_owner(files)
                    require(
                        set(os.listdir(files.fd))
                        == {"study.tar.gz", "acceptance.json"},
                        "assembly output roster changed during seal",
                    )
                    require(
                        archive_buffer(output / "study.tar.gz")[0] == raw,
                        "owned archive changed during seal",
                    )
                    require(
                        archive_buffer(output / "acceptance.json")[0] == sealed_bytes,
                        "owned acceptance changed during seal",
                    )
                    require(source_guard is not None, "assembly source snapshot absent")
                    cast(Inputs, source_guard).stable()
                    require(
                        archive_buffer(root / metadata["package_project_path"])
                        == package_identity,
                        "package changed during seal",
                    )
                except (StudyRejection, OSError) as error:
                    result["accepted"] = False
                    result["failure"] = {
                        "type": type(error).__name__,
                        "reason": str(error),
                    }
                    files.receipt(canonical(result))
            if result["accepted"] and time.monotonic() - start >= timeout:
                result["accepted"] = False
                result["failure"] = {
                    "type": "StudyRejection",
                    "reason": "assembly deadline expired during seal",
                }
                files.receipt(canonical(result))
        finally:
            files.close()
    return result


def reproduce(
    raw: bytes, output: Path, *, reviewer_id: str, uv: str = "uv", timeout: float = 1800
) -> dict[str, Any]:
    """Install the contained lock outside its source and reproduce all frozen draws."""
    require(
        os.name == "posix" and output.is_absolute() and ".." not in output.parts,
        "POSIX absolute canonical reproduction attempt required",
    )
    require(
        type(timeout) in (int, float) and math.isfinite(timeout) and timeout > 0,
        "finite positive reproduction budget",
    )
    require(type(uv) is str and bool(uv), "uv executable required")
    require(
        type(reviewer_id) is str and bool(reviewer_id),
        "actual reproduction reviewer identity required",
    )
    # This check performs no simulation or dependency acquisition.
    validation = validate(raw)
    payload, metadata = read_study_archive(raw)
    files = AttemptFiles(output, create=True)
    start = time.monotonic()
    result: dict[str, Any] = {
        "schema_version": 1,
        "kind": "h3-study-reproduction",
        "accepted": False,
        "archive_sha256": digest(raw),
        "reviewer_id": reviewer_id,
        "validation": validation,
        "stages": [],
    }
    expected_streams: dict[str, str] = {}
    fresh_outputs: Inputs | None = None
    source_guard: Inputs | None = None
    installed_guard: Inputs | None = None
    temporary_owner: tempfile.TemporaryDirectory[str] | None = None
    try:
        temporary_owner = tempfile.TemporaryDirectory(prefix="h3-fresh-reproduction-")
        with contextlib.nullcontext(temporary_owner.name) as temporary:
            workspace = Path(temporary).resolve()
            root, environment = workspace / "project", workspace / "validator"
            hydrate(payload, metadata, root)
            source_guard = Inputs(root)
            for name, sha in metadata["source_sha256"].items():
                source_guard.read(name, expected=sha)
            descriptor = source_guard.json(metadata["descriptor"]["path"])
            original = source_guard.json(descriptor["synthetic_attempt"]["path"])
            env = {
                key: value
                for key, value in os.environ.items()
                if key
                in {
                    "PATH",
                    "SYSTEMROOT",
                    "TMPDIR",
                    "TEMP",
                    "LANG",
                    "LC_ALL",
                    "SSL_CERT_FILE",
                    "SSL_CERT_DIR",
                }
            }
            env["UV_PROJECT_ENVIRONMENT"] = str(environment)
            env["PYTHONNOUSERSITE"] = "1"
            env["UV_NO_CONFIG"] = "1"
            env["UV_KEYRING_PROVIDER"] = "disabled"

            def stage(
                name: str, command: list[str], *, allowed: tuple[int, ...] = (0,)
            ) -> subprocess.CompletedProcess[str]:
                source_guard.stable()
                if installed_guard is not None:
                    installed_guard.stable()
                remaining = timeout - (time.monotonic() - start)
                require(remaining > 0, "reproduction deadline expired")
                row: dict[str, Any] = {
                    "name": name,
                    "command": command,
                    "budget_seconds": remaining,
                }
                result["stages"].append(row)
                begun = time.monotonic()
                try:
                    completed = run_process_group(
                        command, cwd=root, env=env, timeout=remaining
                    )
                    row["returncode"] = completed.returncode
                    for stream, value in (
                        ("stdout", completed.stdout),
                        ("stderr", completed.stderr),
                    ):
                        filename, data = name + "." + stream, value.encode()
                        files.write_new(filename, data)
                        expected_streams[filename] = digest(data)
                    require(
                        completed.returncode in allowed,
                        "reproduction child failed: " + name,
                    )
                except subprocess.TimeoutExpired as error:
                    row["timed_out"] = True
                    for stream, partial in (
                        ("stdout", error.output),
                        ("stderr", error.stderr),
                    ):
                        if partial is not None:
                            filename = name + "." + stream
                            data = (
                                partial
                                if isinstance(partial, bytes)
                                else partial.encode()
                            )
                            files.write_new(filename, data)
                            expected_streams[filename] = digest(data)
                    raise
                finally:
                    row["duration_seconds"] = time.monotonic() - begun
                    source_guard.stable()
                    if installed_guard is not None:
                        installed_guard.stable()
                return completed

            stage(
                "locked-install",
                [
                    uv,
                    "sync",
                    "--locked",
                    "--no-dev",
                    "--all-extras",
                    "--no-editable",
                    "--python",
                    "3.14.4",
                ],
            )
            python = str(environment / "bin/python")
            installed_sources = {
                name: sha
                for name, sha in metadata["source_sha256"].items()
                if name.startswith(("src/fep_formal/", "src/fep_lean/"))
                and name.endswith((".py", ".pyi", ".lean", ".yaml", "/py.typed"))
            }
            require(bool(installed_sources), "installed package source roster absent")
            location_code = (
                "import json,pathlib,platform,sysconfig; "
                "print(json.dumps({'python':platform.python_version(),"
                "'purelib':str(pathlib.Path(sysconfig.get_paths()['purelib']).resolve())},sort_keys=True))"
            )
            location = load_strict_json(
                stage(
                    "installed-location", [python, "-I", "-S", "-c", location_code]
                ).stdout
            )
            require(
                type(location) is dict
                and set(location) == {"python", "purelib"}
                and location["python"] == original["execution_environment"]["python"]
                and type(location["purelib"]) is str,
                "stdlib installed-location evidence mismatch",
            )
            # Bind physical installed owners, including the compatibility shim,
            # without rewriting original source keys in a historical bundle.
            package_root, namespace = (
                Path(location["purelib"]),
                "fep_formal" if "src/fep_formal/__init__.py" in installed_sources else "fep_lean",
            )
            require(
                package_root.is_relative_to(environment)
                and package_root.resolve() == package_root,
                "installed package root redirected",
            )
            installed_guard = Inputs(package_root)
            for name, sha in installed_sources.items():
                installed_guard.read(name.removeprefix("src/"), expected=sha)
            runtime_code = (
                "import importlib,json,platform,pathlib,hashlib,numpy; "
                f"package=importlib.import_module({namespace!r}); "
                "p=pathlib.Path(package.__file__).resolve(); "
                f"purelib=pathlib.Path({str(package_root)!r}); "
                f"assert p == purelib / {namespace!r} / '__init__.py'; "
                f"assert p.is_relative_to(pathlib.Path({str(environment)!r})); "
                f"assert not p.is_relative_to(pathlib.Path({str(root)!r})); "
                f"expected={installed_sources!r}; "
                "observed={name:hashlib.sha256((purelib/name.removeprefix('src/')).read_bytes()).hexdigest() for name in expected}; "
                "assert observed==expected; "
                "print(json.dumps({'python':platform.python_version(),'numpy':numpy.__version__,'package':str(p),'source_sha256':observed},sort_keys=True))"
            )
            runtime = load_strict_json(
                stage("installed-runtime", [python, "-I", "-c", runtime_code]).stdout
            )
            require(
                type(runtime) is dict
                and set(runtime) == {"python", "numpy", "package", "source_sha256"}
                and runtime.get("source_sha256") == installed_sources
                and type(runtime.get("package")) is str
                and bool(runtime["package"])
                and runtime.get("python") == original["execution_environment"]["python"]
                and runtime.get("numpy") == original["execution_environment"]["numpy"]
                and runtime.get("package") == str(package_root / namespace / "__init__.py"),
                "installed runtime source evidence mismatch",
            )
            simulated = output / "synthetic"
            arguments = [
                python,
                "-I",
                str(root / BASE / "run_synthetic.py"),
                "--project-root",
                str(root),
                "--output",
                str(simulated),
                "--export",
                descriptor["export"]["path"],
                "--audit",
                descriptor["audit"]["path"],
                "--proof-review",
                descriptor["proof_review"]["path"],
            ]
            stage("frozen-inputs", [*arguments, "--check-inputs"])
            stage(
                "synthetic", arguments, allowed=(0,) if original["accepted"] else (1,)
            )
            require(
                simulated.resolve() == simulated
                and not any(p.is_symlink() for p in (simulated, *simulated.parents)),
                "reproduction output redirected",
            )
            fresh_outputs = Inputs(simulated)
            actual = fresh_outputs.json("acceptance.json")
            require(
                actual == original, "fresh fixture/settings/control receipt differs"
            )
            for name, sha in original["artifact_sha256"].items():
                data = fresh_outputs.read(safe_name(name), expected=sha)
                require(digest(data) == sha, "fresh array differs: " + name)
            result["reproduced_array_sha256"] = original["artifact_sha256"]
            result["synthetic_accepted"] = original["accepted"]
            result["execution_environment"] = original["execution_environment"]
            result["retained_synthetic_attempt"] = {
                "path": "synthetic/acceptance.json",
                "sha256": fresh_outputs.states["acceptance.json"].sha256,
            }
            require(
                time.monotonic() - start < timeout,
                "reproduction final deadline expired",
            )
            result["accepted"] = True
    except BaseException as error:
        result["failure"] = {"type": type(error).__name__, "reason": str(error)}
        raise
    finally:
        result["duration_seconds"] = time.monotonic() - start
        retained, issues = files.inventory(strict=False)
        result["retained_stream_sha256"] = retained
        result["retained_output_issues"] = [
            issue
            for issue in issues
            if issue
            != {"path": "synthetic", "reason": "nonregular artifact; target never read"}
        ]
        if result["accepted"] and fresh_outputs is not None:
            try:
                require(
                    (output / "synthetic").resolve() == output / "synthetic",
                    "reproduction directory redirected",
                )
                fresh_outputs.stable()
                require(
                    set(os.listdir(output / "synthetic"))
                    == {"acceptance.json", *result["reproduced_array_sha256"]},
                    "reproduction output roster changed",
                )
            except (StudyRejection, OSError) as error:
                result["accepted"] = False
                result["failure"] = {"type": type(error).__name__, "reason": str(error)}
        if result["accepted"] and (
            result["retained_output_issues"] or retained != expected_streams
        ):
            result["accepted"] = False
            result["failure"] = {
                "type": "StudyRejection",
                "reason": "reproduction streams changed",
            }
        try:
            if result["accepted"] and time.monotonic() - start >= timeout:
                result["accepted"] = False
                result["failure"] = {
                    "type": "StudyRejection",
                    "reason": "reproduction deadline expired before seal",
                }
            sealed_bytes = canonical(result)
            files.receipt(sealed_bytes)
            if result["accepted"]:
                try:
                    check_output_owner(files)
                    post_hashes, post_issues = files.inventory(strict=False)
                    require(
                        post_hashes.pop("acceptance.json", None)
                        == digest(sealed_bytes),
                        "owned acceptance changed during seal",
                    )
                    require(
                        post_hashes == expected_streams
                        and all(
                            issue
                            == {
                                "path": "synthetic",
                                "reason": "nonregular artifact; target never read",
                            }
                            for issue in post_issues
                        ),
                        "owned streams changed during seal",
                    )
                    require(
                        fresh_outputs is not None
                        and source_guard is not None
                        and installed_guard is not None,
                        "reproduction custody snapshots absent",
                    )
                    cast(Inputs, fresh_outputs).stable()
                    require(
                        (output / "synthetic").resolve() == output / "synthetic"
                        and not any(
                            p.is_symlink()
                            for p in (
                                output / "synthetic",
                                *(output / "synthetic").parents,
                            )
                        ),
                        "synthetic output redirected during seal",
                    )
                    require(
                        set(os.listdir(output / "synthetic"))
                        == {"acceptance.json", *result["reproduced_array_sha256"]},
                        "synthetic output roster changed during seal",
                    )
                    cast(Inputs, source_guard).stable()
                    cast(Inputs, installed_guard).stable()
                except (StudyRejection, OSError) as error:
                    result["accepted"] = False
                    result["failure"] = {
                        "type": type(error).__name__,
                        "reason": str(error),
                    }
                    files.receipt(canonical(result))
            if result["accepted"] and time.monotonic() - start >= timeout:
                result["accepted"] = False
                result["failure"] = {
                    "type": "StudyRejection",
                    "reason": "reproduction deadline expired during seal",
                }
                files.receipt(canonical(result))
        finally:
            files.close()
            if temporary_owner is not None:
                temporary_owner.cleanup()
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="operation", required=True)
    build = sub.add_parser("assemble")
    build.add_argument(
        "--project-root", type=Path, default=Path(__file__).resolve().parents[2]
    )
    build.add_argument("--descriptor", required=True)
    build.add_argument("--output", required=True, type=Path)
    build.add_argument("--timeout", type=float, default=600)
    check = sub.add_parser("check")
    check.add_argument("--archive", required=True, type=Path)
    check.add_argument("--project-root", type=Path)
    replay = sub.add_parser("reproduce")
    replay.add_argument("--archive", required=True, type=Path)
    replay.add_argument("--output", required=True, type=Path)
    replay.add_argument("--timeout", type=float, default=1800)
    replay.add_argument("--reviewer-id", required=True)
    args = parser.parse_args()
    try:
        if args.operation == "assemble":
            result = assemble(
                args.project_root, args.descriptor, args.output, timeout=args.timeout
            )
        elif args.operation == "check":
            result = validate(
                archive_buffer(args.archive)[0], project_root=args.project_root
            )
        else:
            result = reproduce(
                archive_buffer(args.archive)[0],
                args.output,
                reviewer_id=args.reviewer_id,
                timeout=args.timeout,
            )
    except (StudyRejection, OSError, ValueError, subprocess.TimeoutExpired) as error:
        print(
            canonical(
                {
                    "accepted": False,
                    "failure": {"type": type(error).__name__, "reason": str(error)},
                }
            ).decode(),
            end="",
        )
        return 2
    print(canonical(result).decode(), end="")
    return 0 if result.get("accepted", result.get("valid", False)) else 2


if __name__ == "__main__":
    raise SystemExit(main())
