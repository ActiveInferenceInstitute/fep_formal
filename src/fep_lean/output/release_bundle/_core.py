"""Shared models, errors, and canonical helpers for the release bundle."""

import hashlib
import json
import os
from collections.abc import (
    Mapping,
    Sequence,
)
from dataclasses import dataclass
from pathlib import (
    Path,
    PurePosixPath,
)
from typing import Any

from fep_lean.output.release_bundle._constants import (
    _PROVIDER_MEMBER_PREFIXES,
)


@dataclass(frozen=True)
class ReleaseBundleValidation:
    """Independent validation result for one release archive."""

    valid: bool
    source_bound: bool
    claim_ready: bool
    errors: tuple[str, ...]
    archive_sha256: str
    member_count: int
    manifest: dict[str, Any] | None


class ReleaseBundleError(ValueError):
    """Raised before replacing an archive when publication inputs are invalid."""


@dataclass(frozen=True)
class PublicationManuscript:
    """Fresh deterministic manuscript outputs and renderer provenance."""

    html: bytes
    pdf: bytes | None
    provenance: bytes
    source_digest: str


@dataclass(frozen=True)
class _BundleMember:
    path: str
    data: bytes
    evidence_class: str


def _canonical_json(payload: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(
            dict(payload),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        + "\n"
    ).encode("utf-8")


def _source_date_epoch(value: int | None = None) -> int:
    raw: str | int = (
        os.environ.get("SOURCE_DATE_EPOCH", "0") if value is None else value
    )
    if isinstance(raw, bool):
        raise ReleaseBundleError("SOURCE_DATE_EPOCH must be an integer")
    try:
        epoch = int(raw)
    except (TypeError, ValueError) as exc:
        raise ReleaseBundleError("SOURCE_DATE_EPOCH must be an integer") from exc
    if epoch < 0 or epoch > 0xFFFFFFFF:
        raise ReleaseBundleError("SOURCE_DATE_EPOCH must be between 0 and 4294967295")
    return epoch


def _relative_file_bytes(project_root: Path, relative: str) -> bytes:
    root = Path(project_root).resolve()
    if not _safe_member_name(relative):
        raise ReleaseBundleError(f"required file path is unsafe: {relative}")
    path = root / relative
    if path.is_symlink() or not path.is_file():
        raise ReleaseBundleError(f"required regular file is missing: {relative}")
    resolved = path.resolve()
    if not resolved.is_relative_to(root):
        raise ReleaseBundleError(f"required file escapes the project root: {relative}")
    parent = path.parent
    while parent != root:
        if parent.is_symlink():
            raise ReleaseBundleError(f"required file traverses a symlink: {relative}")
        parent = parent.parent
    return path.read_bytes()


def _digest_named_bytes(records: Sequence[tuple[str, bytes]]) -> str:
    digest = hashlib.sha256()
    for name, data in sorted(records):
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(data)
        digest.update(b"\0")
    return digest.hexdigest()


def _safe_member_name(name: str) -> bool:
    if not name or "\\" in name or name.startswith("/") or name.endswith("/"):
        return False
    path = PurePosixPath(name)
    return path.as_posix() == name and all(
        part not in {"", ".", ".."} for part in path.parts
    )


def _is_provider_member(name: str) -> bool:
    lowered = name.lower()
    if lowered.startswith(_PROVIDER_MEMBER_PREFIXES):
        return True
    if not lowered.startswith("output/"):
        return False
    basename = PurePosixPath(lowered).name
    return basename.startswith(
        ("provider", "hermes", "opengauss", "external-full", "full-mode")
    )


def _json_object(path: Path, label: str) -> tuple[dict[str, Any] | None, str | None]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return None, f"cannot read {label}: {exc}"
    if not isinstance(payload, dict):
        return None, f"{label} must contain a JSON object"
    return payload, None
