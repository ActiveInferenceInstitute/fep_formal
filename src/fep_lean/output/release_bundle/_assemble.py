"""Release-bundle member assembly, manifest construction, and archive write."""

import gzip
import io
import json
import os
import re
import tarfile
import tempfile
from collections.abc import (
    Mapping,
    Sequence,
)
from pathlib import Path
from typing import Any

from fep_lean.output import release_bundle as bundle
from fep_lean.output.browser_capture import BROWSER_RECEIPT
from fep_lean.output.formalism_presentation import FormalismPresentation
from fep_lean.output.fsutil import sha256_bytes
from fep_lean.output.release_bundle._acceptance import (
    _python_test_records,
)
from fep_lean.output.release_bundle._constants import (
    CHECKSUMS_NAME,
    MANIFEST_NAME,
    NUMERICAL_RECEIPT,
    PUBLICATION_PDF,
    PYTEST_RECEIPT,
    PYTHON_ACCEPTANCE_RECEIPT,
    PYTHON_COVERAGE_RECEIPT,
    RELEASE_BUNDLE_SCHEMA_VERSION,
    RENDERER_PROVENANCE,
)
from fep_lean.output.release_bundle._core import (
    ReleaseBundleError,
    _BundleMember,
    _canonical_json,
    _digest_named_bytes,
    _is_provider_member,
    _json_object,
    _relative_file_bytes,
    _safe_member_name,
    _source_date_epoch,
)
from fep_lean.output.release_bundle._manuscript import (
    _manuscript_source_records,
)
from fep_lean.output.release_bundle._prerequisites import (
    release_bundle_prerequisite_errors,
)
from fep_lean.verification.numerical_witnesses import NON_PROOF_EVIDENCE


def _add_member(
    members: dict[str, _BundleMember],
    *,
    path: str,
    data: bytes,
    evidence_class: str,
) -> None:
    if not _safe_member_name(path) or path in {MANIFEST_NAME, CHECKSUMS_NAME}:
        raise ReleaseBundleError(f"unsafe bundle member path: {path}")
    if path in members:
        raise ReleaseBundleError(f"duplicate bundle member path: {path}")
    if _is_provider_member(path):
        raise ReleaseBundleError(f"provider artifact is forbidden: {path}")
    members[path] = _BundleMember(path, data, evidence_class)


def _project_members(project_root: Path) -> tuple[_BundleMember, ...]:
    root = Path(project_root).resolve()
    members: dict[str, _BundleMember] = {}
    source_paths = bundle.source_owner_paths(root)
    for path in source_paths:
        relative = path.relative_to(root).as_posix()
        _add_member(
            members,
            path=relative,
            data=_relative_file_bytes(root, relative),
            evidence_class=(
                "manifested_lean_source"
                if relative.endswith(".lean")
                else "source_owner"
            ),
        )
    for path in bundle.config_owner_paths(root):
        relative = path.relative_to(root).as_posix()
        if relative not in members:
            _add_member(
                members,
                path=relative,
                data=_relative_file_bytes(root, relative),
                evidence_class="configuration_snapshot",
            )
    for relative, evidence_class in bundle._REQUIRED_STATIC_MEMBERS:
        if relative not in members:
            _add_member(
                members,
                path=relative,
                data=_relative_file_bytes(root, relative),
                evidence_class=evidence_class,
            )
    for source in bundle.manuscript_source_files(root / "manuscript"):
        relative = f"output/manuscript/{source.name}"
        if relative not in members:
            _add_member(
                members,
                path=relative,
                data=_relative_file_bytes(root, relative),
                evidence_class="rendered_manuscript",
            )
    for _source, destination in bundle.MANUSCRIPT_ASSETS.values():
        relative = (Path("output/manuscript") / destination).as_posix()
        if relative not in members:
            _add_member(
                members,
                path=relative,
                data=_relative_file_bytes(root, relative),
                evidence_class="rendered_manuscript_asset",
            )
    for relative, data in bundle._publication_resource_records(root):
        if relative not in members:
            _add_member(
                members,
                path=relative,
                data=data,
                evidence_class="rendered_manuscript_figure",
            )
    provenance, error = _json_object(root / RENDERER_PROVENANCE, "renderer provenance")
    if provenance is None:
        raise ReleaseBundleError(error or "renderer provenance is invalid")
    pdf = provenance.get("pdf")
    if isinstance(pdf, dict) and pdf.get("current") is True:
        _add_member(
            members,
            path=PUBLICATION_PDF.as_posix(),
            data=_relative_file_bytes(root, PUBLICATION_PDF.as_posix()),
            evidence_class="rendered_manuscript_pdf",
        )
    for relative in bundle._browser_screenshot_paths(root):
        _add_member(
            members,
            path=relative,
            data=_relative_file_bytes(root, relative),
            evidence_class="browser_screenshot",
        )
    _add_member(
        members,
        path=NUMERICAL_RECEIPT.as_posix(),
        data=bundle.build_numerical_witness_receipt(root),
        evidence_class="numerical_non_proof_receipt",
    )
    _add_member(
        members,
        path=PYTHON_ACCEPTANCE_RECEIPT.as_posix(),
        data=bundle.build_python_acceptance_receipt(root),
        evidence_class="python_acceptance_receipt",
    )
    return tuple(members[path] for path in sorted(members))


def _toolchain_identity(project_root: Path) -> dict[str, str]:
    root = Path(project_root)
    native, error = _json_object(
        root / "output" / "native-verification.json", "native Lean receipt"
    )
    if native is None:
        raise ReleaseBundleError(error or "native Lean receipt is invalid")
    identity = {
        "lean_toolchain": str(native.get("lean_toolchain", "")),
        "lean_version": str(native.get("lean_version", "")),
        "mathlib_tag": str(native.get("mathlib_tag", "")),
        "mathlib_revision": str(native.get("mathlib_revision", "")),
    }
    if (
        not identity["lean_toolchain"]
        or not identity["lean_version"]
        or not re.fullmatch(r"v\d+\.\d+\.\d+", identity["mathlib_tag"])
        or not re.fullmatch(r"[0-9a-f]{40}", identity["mathlib_revision"])
    ):
        raise ReleaseBundleError("native receipt lacks a complete toolchain identity")
    return identity


def _member_by_path(members: Sequence[_BundleMember], path: str) -> _BundleMember:
    matches = [member for member in members if member.path == path]
    if len(matches) != 1:
        raise ReleaseBundleError(f"release snapshot lacks exactly one member: {path}")
    return matches[0]


def _toolchain_identity_from_members(
    members: Sequence[_BundleMember],
) -> dict[str, str]:
    native_member = _member_by_path(members, "output/native-verification.json")
    try:
        native = json.loads(native_member.data.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ReleaseBundleError("native receipt snapshot is invalid JSON") from exc
    if not isinstance(native, dict):
        raise ReleaseBundleError("native receipt snapshot must be a JSON object")
    identity = {
        "lean_toolchain": str(native.get("lean_toolchain", "")),
        "lean_version": str(native.get("lean_version", "")),
        "mathlib_tag": str(native.get("mathlib_tag", "")),
        "mathlib_revision": str(native.get("mathlib_revision", "")),
    }
    if (
        not identity["lean_toolchain"]
        or not identity["lean_version"]
        or not re.fullmatch(r"v\d+\.\d+\.\d+", identity["mathlib_tag"])
        or not re.fullmatch(r"[0-9a-f]{40}", identity["mathlib_revision"])
    ):
        raise ReleaseBundleError("native receipt lacks a complete toolchain identity")
    return identity


def _digest_snapshot_classes(
    members: Sequence[_BundleMember],
    evidence_classes: frozenset[str],
) -> str:
    records = [
        (member.path, member.data)
        for member in members
        if member.evidence_class in evidence_classes
    ]
    if not records:
        raise ReleaseBundleError("release snapshot contains no canonical owners")
    return _digest_named_bytes(records)


def _supplemental_snapshot_records(
    project_root: Path,
) -> tuple[tuple[str, bytes], ...]:
    """Capture release inputs that are validated but intentionally not bundled."""
    root = Path(project_root).resolve()
    records: list[tuple[str, bytes]] = []
    if (root / "manuscript").is_dir():
        records.extend(_manuscript_source_records(root))
    if (root / "tests").is_dir():
        records.extend(_python_test_records(root))
    return tuple(records)


def _snapshot_fingerprint(project_root: Path, members: Sequence[_BundleMember]) -> str:
    records = [(member.path, member.data) for member in members]
    records.extend(_supplemental_snapshot_records(project_root))
    return _digest_named_bytes(records)


def _live_snapshot_fingerprint(
    project_root: Path, members: Sequence[_BundleMember]
) -> str:
    root = Path(project_root).resolve()
    records: list[tuple[str, bytes]] = []
    for member in members:
        if member.path == NUMERICAL_RECEIPT.as_posix():
            data = bundle.build_numerical_witness_receipt(root)
        elif member.path == PYTHON_ACCEPTANCE_RECEIPT.as_posix():
            data = bundle.build_python_acceptance_receipt(root)
        else:
            data = _relative_file_bytes(root, member.path)
        records.append((member.path, data))
    records.extend(_supplemental_snapshot_records(root))
    return _digest_named_bytes(records)


def _build_manifest(
    project_root: Path,
    members: Sequence[_BundleMember],
    *,
    epoch: int,
) -> dict[str, Any]:
    try:
        coverage_snapshot = json.loads(
            _member_by_path(members, "docs/formalism-coverage.json").data.decode(
                "utf-8"
            )
        )
        numerical_snapshot = json.loads(
            _member_by_path(members, NUMERICAL_RECEIPT.as_posix()).data.decode("utf-8")
        )
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ReleaseBundleError("release summary snapshot is invalid JSON") from exc
    if not isinstance(coverage_snapshot, dict) or not isinstance(
        numerical_snapshot, dict
    ):
        raise ReleaseBundleError("release summary snapshot must contain JSON objects")
    topics = coverage_snapshot.get("topics")
    family_counts = coverage_snapshot.get("family_counts")
    area_counts = coverage_snapshot.get("area_counts")
    relations = coverage_snapshot.get("relations")
    capabilities = coverage_snapshot.get("capabilities")
    formal_modules = coverage_snapshot.get("formal_modules")
    if (
        not isinstance(topics, list)
        or not topics
        or not all(isinstance(topic, dict) for topic in topics)
        or not isinstance(family_counts, dict)
        or not isinstance(area_counts, dict)
        or not isinstance(relations, list)
        or not isinstance(capabilities, list)
        or not isinstance(formal_modules, list)
        or type(numerical_snapshot.get("witness_count")) is not int
    ):
        raise ReleaseBundleError("release summary snapshot has an invalid shape")
    first_id = topics[0].get("id")
    last_id = topics[-1].get("id")
    if not isinstance(first_id, str) or not isinstance(last_id, str):
        raise ReleaseBundleError("release summary snapshot lacks topic boundary IDs")
    browser = _member_by_path(members, BROWSER_RECEIPT.as_posix()).data
    native = _member_by_path(members, "output/native-verification.json").data
    formal = _member_by_path(members, "output/formalism-audit.json").data
    pytest_receipt = _member_by_path(members, PYTEST_RECEIPT.as_posix()).data
    coverage_receipt = _member_by_path(members, PYTHON_COVERAGE_RECEIPT.as_posix()).data
    numerical = _member_by_path(members, NUMERICAL_RECEIPT.as_posix()).data
    python_acceptance = _member_by_path(
        members, PYTHON_ACCEPTANCE_RECEIPT.as_posix()
    ).data
    return {
        "schema_version": RELEASE_BUNDLE_SCHEMA_VERSION,
        "kind": "fep-lean-evidence-bundle",
        "source_date_epoch": epoch,
        "catalogue": {
            "topics": len(topics),
            "families": len(family_counts),
            "areas": len(area_counts),
            "first_id": first_id,
            "last_id": last_id,
        },
        "formalism": {
            "relations": len(relations),
            "capabilities": len(capabilities),
            "formal_modules": len(formal_modules),
            "numerical_witnesses": numerical_snapshot["witness_count"],
        },
        "toolchain": _toolchain_identity_from_members(members),
        "evidence": {
            "native_lean": {
                "current": True,
                "path": "output/native-verification.json",
                "sha256": sha256_bytes(native),
            },
            "declaration_axiom_audit": {
                "current": True,
                "path": "output/formalism-audit.json",
                "sha256": sha256_bytes(formal),
            },
            "browser_interaction": {
                "current": True,
                "path": BROWSER_RECEIPT.as_posix(),
                "sha256": sha256_bytes(browser),
            },
            "numerical_witnesses": {
                "current": True,
                "path": NUMERICAL_RECEIPT.as_posix(),
                "sha256": sha256_bytes(numerical),
                "evidence_kind": NON_PROOF_EVIDENCE,
            },
            "python_tests": {
                "current": True,
                "path": PYTEST_RECEIPT.as_posix(),
                "sha256": sha256_bytes(pytest_receipt),
            },
            "python_coverage": {
                "current": True,
                "path": PYTHON_COVERAGE_RECEIPT.as_posix(),
                "sha256": sha256_bytes(coverage_receipt),
            },
            "python_acceptance": {
                "current": True,
                "path": PYTHON_ACCEPTANCE_RECEIPT.as_posix(),
                "sha256": sha256_bytes(python_acceptance),
            },
        },
        "external_full_mode": {
            "current": False,
            "authorized": False,
            "artifacts": [],
        },
        "source_sha256": _digest_snapshot_classes(
            members, frozenset({"manifested_lean_source", "source_owner"})
        ),
        "config_sha256": _digest_snapshot_classes(
            members, frozenset({"configuration_snapshot"})
        ),
        "manifested_lean_sources": [
            member.path
            for member in members
            if member.evidence_class == "manifested_lean_source"
        ],
        "members": [
            {
                "path": member.path,
                "sha256": sha256_bytes(member.data),
                "size": len(member.data),
                "evidence_class": member.evidence_class,
            }
            for member in members
        ],
    }


def _archive_contents(
    project_root: Path,
    members: Sequence[_BundleMember],
    *,
    epoch: int,
) -> dict[str, bytes]:
    manifest_bytes = _canonical_json(
        _build_manifest(project_root, members, epoch=epoch)
    )
    contents = {member.path: member.data for member in members}
    contents[MANIFEST_NAME] = manifest_bytes
    checksums = "".join(
        f"{sha256_bytes(contents[name])}  {name}\n" for name in sorted(contents)
    ).encode("utf-8")
    contents[CHECKSUMS_NAME] = checksums
    return contents


def _write_archive(path: Path, contents: Mapping[str, bytes], *, epoch: int) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, raw_path = tempfile.mkstemp(
        prefix=f".{destination.name}.", dir=destination.parent
    )
    try:
        with os.fdopen(fd, "wb") as raw:
            with (
                gzip.GzipFile(
                    fileobj=raw,
                    mode="wb",
                    filename="",
                    compresslevel=9,
                    mtime=epoch,
                ) as zipped,
                tarfile.open(
                    fileobj=zipped,
                    mode="w|",
                    format=tarfile.USTAR_FORMAT,
                ) as tar,
            ):
                for name in sorted(contents):
                    if not _safe_member_name(name):
                        raise ReleaseBundleError(f"unsafe bundle member path: {name}")
                    data = contents[name]
                    info = tarfile.TarInfo(name)
                    info.mode = 0o644
                    info.uid = 0
                    info.gid = 0
                    info.uname = ""
                    info.gname = ""
                    info.mtime = epoch
                    info.size = len(data)
                    tar.addfile(info, io.BytesIO(data))
            raw.flush()
            os.fsync(raw.fileno())
        os.replace(raw_path, destination)
    except (OSError, tarfile.TarError, ValueError) as exc:
        raise ReleaseBundleError(f"cannot build deterministic archive: {exc}") from exc
    finally:
        if os.path.exists(raw_path):
            os.unlink(raw_path)


def build_release_bundle(
    project_root: Path,
    output_path: Path,
    *,
    source_date_epoch: int | None = None,
) -> Path:
    """Validate, render, stage, validate, and atomically replace one bundle."""
    root = Path(project_root).resolve()
    requested_destination = Path(output_path)
    if requested_destination.is_symlink():
        raise ReleaseBundleError("release bundle destination is a symlink")
    lexical_destination = requested_destination.absolute()
    destination = requested_destination.resolve()
    if not destination.name.endswith(".tar.gz"):
        raise ReleaseBundleError("release bundle destination must end in .tar.gz")
    if lexical_destination.is_relative_to(root) or destination.is_relative_to(root):
        raise ReleaseBundleError(
            "release bundle destination must be outside the project root"
        )
    epoch = _source_date_epoch(source_date_epoch)
    presentation: FormalismPresentation | None = None
    try:
        presentation = bundle.build_formalism_presentation(root)
    except (OSError, TypeError, ValueError):
        presentation = None
    prerequisite_errors = release_bundle_prerequisite_errors(
        root,
        source_date_epoch=epoch,
        include_publication=False,
        presentation=presentation,
    )
    if prerequisite_errors:
        raise ReleaseBundleError(
            "release prerequisites failed:\n" + "\n".join(prerequisite_errors)
        )
    bundle.write_publication_manuscript(root, source_date_epoch=epoch)
    publication_errors = bundle.publication_manuscript_errors(
        root, source_date_epoch=epoch
    )
    if publication_errors:
        raise ReleaseBundleError(
            "publication manuscript is stale:\n" + "\n".join(publication_errors)
        )
    members = bundle._project_members(root)
    snapshot_fingerprint = _snapshot_fingerprint(root, members)
    contents = bundle._archive_contents(root, members, epoch=epoch)
    if _live_snapshot_fingerprint(root, members) != snapshot_fingerprint:
        raise ReleaseBundleError(
            "release inputs changed while the immutable snapshot was assembled"
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=f".{destination.name}.stage-", dir=destination.parent
    ) as raw_stage:
        staged = Path(raw_stage) / destination.name
        bundle._write_archive(staged, contents, epoch=epoch)
        validation = bundle.validate_release_bundle(
            staged, project_root=root, presentation=presentation
        )
        if not validation.claim_ready:
            raise ReleaseBundleError(
                "staged release bundle is not live claim-ready:\n"
                + "\n".join(validation.errors)
            )
        if _live_snapshot_fingerprint(root, members) != snapshot_fingerprint:
            raise ReleaseBundleError(
                "release inputs changed before the staged archive could be committed"
            )
        os.replace(staged, destination)
    return destination
