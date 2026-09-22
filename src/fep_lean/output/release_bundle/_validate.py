"""Release-archive reader and live-checkout validation."""

import gzip
import json
import re
import tarfile
import tempfile
from pathlib import Path
from typing import Any

from fep_lean.output import release_bundle as bundle
from fep_lean.output.browser_capture import BROWSER_RECEIPT
from fep_lean.output.formalism_presentation import (
    RELEASE_SEAL,
    FormalismPresentation,
)
from fep_lean.output.fsutil import (
    sha256_bytes,
    sha256_file,
)
from fep_lean.output.release_bundle._assemble import (
    _live_snapshot_fingerprint,
    _snapshot_fingerprint,
)
from fep_lean.output.release_bundle._constants import (
    _CHECKSUM_LINE_RE,
    _GIT_SHA_RE,
    _SHA256_RE,
    _STATIC_REQUIRED_BUNDLE_PATHS,
    CHECKSUMS_NAME,
    MANIFEST_NAME,
    NUMERICAL_RECEIPT,
    PYTEST_RECEIPT,
    PYTHON_ACCEPTANCE_RECEIPT,
    PYTHON_COVERAGE_RECEIPT,
    RELEASE_BUNDLE_SCHEMA_VERSION,
)
from fep_lean.output.release_bundle._core import (
    ReleaseBundleValidation,
    _is_provider_member,
    _safe_member_name,
)
from fep_lean.output.release_bundle._identity import (
    _expected_evidence_class,
)
from fep_lean.output.release_bundle._prerequisites import (
    release_bundle_prerequisite_errors,
)
from fep_lean.verification.numerical_witnesses import NON_PROOF_EVIDENCE


def _read_archive(
    archive: Path,
) -> tuple[dict[str, bytes], tuple[tarfile.TarInfo, ...], int, tuple[str, ...]]:
    errors: list[str] = []
    try:
        archive_size = archive.stat().st_size
        with archive.open("rb") as handle:
            header = handle.read(10)
    except OSError as exc:
        return {}, (), 0, (f"cannot read release bundle: {exc}",)
    if archive_size > bundle._MAX_ARCHIVE_BYTES:
        return (
            {},
            (),
            0,
            (f"compressed archive exceeds {bundle._MAX_ARCHIVE_BYTES} bytes",),
        )
    if len(header) < 10 or header[:3] != b"\x1f\x8b\x08":
        return {}, (), 0, ("release bundle is not a gzip stream",)
    flags = header[3]
    epoch = int.from_bytes(header[4:8], "little")
    if flags != 0:
        errors.append("gzip header flags must be zero")
    if header[8] != 2:
        errors.append("gzip header must declare maximum compression")
    if header[9] != 255:
        errors.append("gzip header operating-system byte must be 255")
    members: list[tarfile.TarInfo] = []
    contents: dict[str, bytes] = {}
    names_seen: set[str] = set()
    total_member_bytes = 0
    try:
        with tarfile.open(archive, mode="r|gz") as tar:
            for member in tar:
                members.append(member)
                if len(members) > bundle._MAX_ARCHIVE_MEMBERS:
                    errors.append(
                        f"archive member count exceeds {bundle._MAX_ARCHIVE_MEMBERS}"
                    )
                    break
                if member.name in names_seen:
                    errors.append(f"duplicate archive member: {member.name}")
                names_seen.add(member.name)
                if not _safe_member_name(member.name):
                    errors.append(f"unsafe archive member path: {member.name}")
                if not member.isreg():
                    errors.append(
                        f"archive member is not a regular file: {member.name}"
                    )
                    continue
                if member.size > bundle._MAX_MEMBER_BYTES:
                    errors.append(
                        f"archive member exceeds {bundle._MAX_MEMBER_BYTES} bytes: {member.name}"
                    )
                    break
                total_member_bytes += member.size
                if total_member_bytes > bundle._MAX_TOTAL_MEMBER_BYTES:
                    errors.append(
                        "aggregate archive payload exceeds "
                        f"{bundle._MAX_TOTAL_MEMBER_BYTES} bytes"
                    )
                    break
                extracted = tar.extractfile(member)
                if extracted is None:
                    errors.append(f"cannot read archive member: {member.name}")
                    continue
                data = extracted.read(member.size + 1)
                if len(data) != member.size:
                    errors.append(f"archive member size is inconsistent: {member.name}")
                    continue
                contents.setdefault(member.name, data)
    except (gzip.BadGzipFile, OSError, tarfile.TarError, EOFError) as exc:
        errors.append(f"cannot parse release bundle: {exc}")
    return contents, tuple(members), epoch, tuple(errors)


def _parse_manifest(
    contents: dict[str, bytes], errors: list[str]
) -> dict[str, Any] | None:
    raw = contents.get(MANIFEST_NAME)
    if raw is None:
        errors.append(f"missing required archive member: {MANIFEST_NAME}")
        return None
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"cannot parse {MANIFEST_NAME}: {exc}")
        return None
    if not isinstance(payload, dict):
        errors.append(f"{MANIFEST_NAME} must contain a JSON object")
        return None
    canonical = (
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode()
    if raw != canonical:
        errors.append(f"{MANIFEST_NAME} is not canonical sorted JSON")
    if payload.get("schema_version") != RELEASE_BUNDLE_SCHEMA_VERSION:
        errors.append(
            f"manifest schema_version must be {RELEASE_BUNDLE_SCHEMA_VERSION}"
        )
    if payload.get("kind") != "fep-lean-evidence-bundle":
        errors.append("manifest kind must be fep-lean-evidence-bundle")
    return payload


def _parse_checksums(contents: dict[str, bytes], errors: list[str]) -> dict[str, str]:
    raw = contents.get(CHECKSUMS_NAME)
    if raw is None:
        errors.append(f"missing required archive member: {CHECKSUMS_NAME}")
        return {}
    try:
        text = raw.decode("utf-8")
    except UnicodeError as exc:
        errors.append(f"cannot decode {CHECKSUMS_NAME}: {exc}")
        return {}
    if text and not text.endswith("\n"):
        errors.append(f"{CHECKSUMS_NAME} must end with a newline")
    parsed: dict[str, str] = {}
    for line in text.splitlines():
        match = _CHECKSUM_LINE_RE.fullmatch(line)
        if match is None:
            errors.append(f"malformed checksum line: {line}")
            continue
        digest, name = match.groups()
        if name in parsed:
            errors.append(f"duplicate checksum path: {name}")
            continue
        if not _safe_member_name(name) or name == CHECKSUMS_NAME:
            errors.append(f"unsafe checksum path: {name}")
            continue
        parsed[name] = digest
    if tuple(parsed) != tuple(sorted(parsed)):
        errors.append(f"{CHECKSUMS_NAME} paths must be lexically ordered")
    return parsed


def validate_release_bundle(
    archive_path: Path,
    *,
    project_root: Path | None = None,
    presentation: FormalismPresentation | None = None,
) -> ReleaseBundleValidation:
    """Validate archive structure, bytes, and optionally the live checkout.

    Validation never extracts archive members.  Supplying ``project_root``
    additionally binds the archive to the current release inputs; that live
    comparison is implemented by the high-level builder below.  Supplying
    ``presentation`` reuses an already-built formalism join so a builder that
    validates twice against one root does not rebuild it per pass.
    """
    archive = Path(archive_path)
    contents, members, epoch, read_errors = _read_archive(archive)
    errors = list(read_errors)
    names = tuple(member.name for member in members)
    if names != tuple(sorted(names)):
        errors.append("archive members must be lexically ordered")
    for member in members:
        if member.mode != 0o644:
            errors.append(f"archive member mode must be 0644: {member.name}")
        if member.uid != 0 or member.gid != 0:
            errors.append(f"archive member uid/gid must be zero: {member.name}")
        if member.uname or member.gname:
            errors.append(f"archive member owner names must be empty: {member.name}")
        if member.mtime != epoch:
            errors.append(
                f"archive member mtime differs from gzip mtime: {member.name}"
            )
        if member.pax_headers:
            errors.append(f"archive member carries PAX metadata: {member.name}")

    manifest = _parse_manifest(contents, errors)
    checksums = _parse_checksums(contents, errors)
    manifest_members: dict[str, dict[str, Any]] = {}
    if manifest is not None:
        if manifest.get("source_date_epoch") != epoch:
            errors.append("manifest source_date_epoch differs from gzip mtime")
        if manifest.get("external_full_mode") != {
            "artifacts": [],
            "authorized": False,
            "current": False,
        }:
            errors.append("manifest external_full_mode must be explicitly unavailable")
        raw_members = manifest.get("members")
        if not isinstance(raw_members, list):
            errors.append("manifest members must be a list")
        else:
            for record in raw_members:
                if not isinstance(record, dict):
                    errors.append("manifest members must contain objects")
                    continue
                name = record.get("path")
                if not isinstance(name, str) or not _safe_member_name(name):
                    errors.append(f"manifest member has unsafe path: {name}")
                    continue
                if name in {MANIFEST_NAME, CHECKSUMS_NAME}:
                    errors.append(f"manifest payload cannot include {name}")
                    continue
                if name in manifest_members:
                    errors.append(f"duplicate manifest member: {name}")
                    continue
                if set(record) != {"path", "sha256", "size", "evidence_class"}:
                    errors.append(f"manifest member fields are invalid: {name}")
                evidence_class = record.get("evidence_class")
                if not isinstance(evidence_class, str) or not evidence_class:
                    errors.append(f"manifest member evidence class is invalid: {name}")
                expected_class = _expected_evidence_class(name)
                if expected_class is None:
                    errors.append(f"manifest member path is not release-owned: {name}")
                elif evidence_class != expected_class:
                    errors.append(
                        "manifest member evidence class is invalid for its path: "
                        f"{name}"
                    )
                if _is_provider_member(name):
                    errors.append(f"provider artifact is forbidden: {name}")
                manifest_members[name] = record
            if tuple(manifest_members) != tuple(sorted(manifest_members)):
                errors.append("manifest members must be lexically ordered")

        if manifest.get("catalogue") != {
            "areas": RELEASE_SEAL["areas"],
            "families": RELEASE_SEAL["families"],
            "first_id": RELEASE_SEAL["first_id"],
            "last_id": RELEASE_SEAL["last_id"],
            "topics": RELEASE_SEAL["topics"],
        }:
            errors.append(
                "manifest catalogue does not match the 155-topic release seal"
            )
        formalism = manifest.get("formalism")
        if not isinstance(formalism, dict):
            errors.append("manifest formalism summary must be an object")
        else:
            for key, expected in (
                ("relations", RELEASE_SEAL["relations"]),
                ("capabilities", RELEASE_SEAL["capabilities"]),
                ("numerical_witnesses", RELEASE_SEAL["witnesses"]),
            ):
                if formalism.get(key) != expected:
                    errors.append(f"manifest formalism.{key} is stale")
            formal_modules = formalism.get("formal_modules")
            if type(formal_modules) is not int or formal_modules <= 0:
                errors.append("manifest formalism.formal_modules must be positive")
        toolchain = manifest.get("toolchain")
        if not isinstance(toolchain, dict):
            errors.append("manifest toolchain identity must be an object")
        else:
            lean_toolchain = toolchain.get("lean_toolchain")
            lean_version = toolchain.get("lean_version")
            mathlib_tag = toolchain.get("mathlib_tag")
            mathlib_revision = toolchain.get("mathlib_revision")
            toolchain_match = (
                re.fullmatch(r"leanprover/lean4:v(\d+\.\d+\.\d+)", lean_toolchain)
                if isinstance(lean_toolchain, str)
                else None
            )
            version_match = (
                re.match(r"Lean \(version (\d+\.\d+\.\d+)(?:,|\))", lean_version)
                if isinstance(lean_version, str)
                else None
            )
            mathlib_match = (
                re.fullmatch(r"v(\d+\.\d+\.\d+)", mathlib_tag)
                if isinstance(mathlib_tag, str)
                else None
            )
            if toolchain_match is None:
                errors.append("manifest Lean toolchain is not a stable semantic pin")
            if version_match is None:
                errors.append("manifest Lean version is not actual compiler output")
            if mathlib_match is None:
                errors.append("manifest Mathlib tag is not a stable semantic pin")
            if (
                toolchain_match is not None
                and version_match is not None
                and toolchain_match.group(1) != version_match.group(1)
            ):
                errors.append("manifest Lean version does not match its toolchain pin")
            if (
                toolchain_match is not None
                and mathlib_match is not None
                and toolchain_match.group(1) != mathlib_match.group(1)
            ):
                errors.append("manifest Mathlib tag does not match the Lean pin")
            if (
                not isinstance(mathlib_revision, str)
                or _GIT_SHA_RE.fullmatch(mathlib_revision) is None
            ):
                errors.append("manifest Mathlib revision is not a lowercase Git SHA")
        for digest_name in ("source_sha256", "config_sha256"):
            digest = manifest.get(digest_name)
            if not isinstance(digest, str) or _SHA256_RE.fullmatch(digest) is None:
                errors.append(f"manifest {digest_name} is invalid")
        lean_sources = manifest.get("manifested_lean_sources")
        if (
            not isinstance(lean_sources, list)
            or not lean_sources
            or any(not isinstance(name, str) for name in lean_sources)
            or lean_sources != sorted(set(lean_sources))
        ):
            errors.append("manifested Lean source roster is invalid")
            lean_sources = []
        for name in lean_sources:
            if name not in manifest_members or not name.endswith(".lean"):
                errors.append(f"manifested Lean source is missing or invalid: {name}")

        for required in sorted(_STATIC_REQUIRED_BUNDLE_PATHS - set(manifest_members)):
            errors.append(f"required release payload is omitted: {required}")
        if not any(
            name.startswith("output/manuscript/") and name.endswith(".md")
            for name in manifest_members
        ):
            errors.append("rendered manuscript Markdown tree is omitted")

        evidence = manifest.get("evidence")
        expected_evidence = {
            "native_lean": "output/native-verification.json",
            "declaration_axiom_audit": "output/formalism-audit.json",
            "browser_interaction": BROWSER_RECEIPT.as_posix(),
            "numerical_witnesses": NUMERICAL_RECEIPT.as_posix(),
            "python_tests": PYTEST_RECEIPT.as_posix(),
            "python_coverage": PYTHON_COVERAGE_RECEIPT.as_posix(),
            "python_acceptance": PYTHON_ACCEPTANCE_RECEIPT.as_posix(),
        }
        if not isinstance(evidence, dict) or set(evidence) != set(expected_evidence):
            errors.append("manifest evidence roster is not canonical")
        else:
            for key, expected_path in expected_evidence.items():
                record = evidence.get(key)
                if (
                    not isinstance(record, dict)
                    or record.get("current") is not True
                    or record.get("path") != expected_path
                ):
                    errors.append(f"manifest evidence record is invalid: {key}")
                    continue
                digest = record.get("sha256")
                manifest_member_record = manifest_members.get(expected_path)
                if (
                    not isinstance(digest, str)
                    or manifest_member_record is None
                    or digest != manifest_member_record.get("sha256")
                ):
                    errors.append(f"manifest evidence hash is invalid: {key}")
            numerical_record = evidence.get("numerical_witnesses")
            if (
                isinstance(numerical_record, dict)
                and numerical_record.get("evidence_kind") != NON_PROOF_EVIDENCE
            ):
                errors.append("manifest numerical evidence boundary was weakened")

    expected_names = set(manifest_members) | {MANIFEST_NAME, CHECKSUMS_NAME}
    actual_names = set(contents)
    for name in sorted(expected_names - actual_names):
        errors.append(f"missing required archive member: {name}")
    for name in sorted(actual_names - expected_names):
        errors.append(f"unexpected archive member: {name}")
    for name in sorted(actual_names):
        if _is_provider_member(name):
            errors.append(f"provider artifact is forbidden: {name}")
    expected_checksum_names = set(manifest_members) | {MANIFEST_NAME}
    for name in sorted(expected_checksum_names - set(checksums)):
        errors.append(f"missing checksum: {name}")
    for name in sorted(set(checksums) - expected_checksum_names):
        errors.append(f"unexpected checksum: {name}")
    for name in sorted(expected_checksum_names & set(checksums) & set(contents)):
        if checksums[name] != sha256_bytes(contents[name]):
            errors.append(f"checksum mismatch: {name}")
    for name, record in manifest_members.items():
        digest = record.get("sha256")
        size = record.get("size")
        if not isinstance(digest, str) or _SHA256_RE.fullmatch(digest) is None:
            errors.append(f"manifest member has invalid sha256: {name}")
        elif name in contents and digest != sha256_bytes(contents[name]):
            errors.append(f"manifest hash mismatch: {name}")
        if type(size) is not int or size < 0:
            errors.append(f"manifest member has invalid size: {name}")
        elif name in contents and size != len(contents[name]):
            errors.append(f"manifest size mismatch: {name}")

    if not errors:
        try:
            with tempfile.TemporaryDirectory(prefix="fep-lean-archive-check-") as raw:
                normalized = Path(raw) / "normalized.tar.gz"
                bundle._write_archive(normalized, contents, epoch=epoch)
                if normalized.read_bytes() != archive.read_bytes():
                    errors.append(
                        "archive bytes are not the canonical normalized USTAR/gzip encoding"
                    )
        except (OSError, ValueError) as exc:
            errors.append(f"cannot reproduce normalized archive bytes: {exc}")

    if project_root is not None and manifest is not None:
        root = Path(project_root).resolve()
        errors.extend(
            release_bundle_prerequisite_errors(
                root,
                source_date_epoch=epoch,
                include_publication=True,
                presentation=presentation,
            )
        )
        try:
            expected_members = bundle._project_members(root)
            expected_fingerprint = _snapshot_fingerprint(root, expected_members)
            expected_contents = bundle._archive_contents(
                root, expected_members, epoch=epoch
            )
        except (OSError, TypeError, ValueError) as exc:
            errors.append(f"live release inputs cannot be loaded: {exc}")
        else:
            for name in sorted(set(expected_contents) - set(contents)):
                errors.append(f"archive is missing a current project member: {name}")
            for name in sorted(set(contents) - set(expected_contents)):
                errors.append(f"archive contains a non-current project member: {name}")
            for name in sorted(set(contents) & set(expected_contents)):
                if contents[name] != expected_contents[name]:
                    errors.append(
                        f"archive member differs from the live project: {name}"
                    )
            try:
                current_fingerprint = _live_snapshot_fingerprint(root, expected_members)
            except (OSError, TypeError, ValueError) as exc:
                errors.append(f"live release inputs cannot be rechecked: {exc}")
            else:
                if current_fingerprint != expected_fingerprint:
                    errors.append("live release inputs changed during validation")
    unique_errors = tuple(dict.fromkeys(errors))
    try:
        archive_digest = (
            sha256_file(archive)
            if archive.stat().st_size <= bundle._MAX_ARCHIVE_BYTES
            else ""
        )
    except OSError:
        archive_digest = ""
    return ReleaseBundleValidation(
        valid=not unique_errors,
        source_bound=project_root is not None and not unique_errors,
        claim_ready=project_root is not None and not unique_errors,
        errors=unique_errors,
        archive_sha256=archive_digest,
        member_count=len(members),
        manifest=manifest,
    )
