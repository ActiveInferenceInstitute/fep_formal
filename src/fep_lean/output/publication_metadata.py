"""Canonical publication metadata projected from maintained owner files."""

from __future__ import annotations

import hashlib
import os
import re
import struct
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

import yaml


class PublicationMetadataError(ValueError):
    """Raised when publication metadata cannot be consumed unambiguously."""


@dataclass(frozen=True)
class PublicationAuthor:
    """One author identity projected from ``CITATION.cff``."""

    name: str
    affiliation: str
    email: str
    orcid: str

    def manuscript_variables(self) -> dict[str, str]:
        """Return the stable author-information block variables."""
        return {
            "name": self.name,
            "affiliation": self.affiliation,
            "email": self.email,
            "orcid": self.orcid,
        }


@dataclass(frozen=True)
class GraphicalAbstractAsset:
    """Validated canonical graphical-abstract bytes and publication metadata."""

    source_path: str
    render_path: str
    media_type: str
    width_px: int
    height_px: int
    sha256: str
    alt_text: str
    data: bytes

    def manuscript_variables(self) -> dict[str, str | int]:
        """Return stable variables safe to expose to authored front matter."""
        return {
            "source_path": self.source_path,
            "render_path": self.render_path,
            "media_type": self.media_type,
            "width_px": self.width_px,
            "height_px": self.height_px,
            "sha256": self.sha256,
            "alt_text": self.alt_text,
        }


def _mapping(value: Any, *, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PublicationMetadataError(f"{label} must be a mapping")
    return value


def _required_text(mapping: dict[str, Any], key: str, *, label: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise PublicationMetadataError(f"{label} {key} must be a non-empty string")
    return value.strip()


def _required_positive_int(mapping: dict[str, Any], key: str, *, label: str) -> int:
    value = mapping.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise PublicationMetadataError(f"{label} {key} must be a positive integer")
    return value


def _safe_project_file(project_root: Path, relative: str, *, label: str) -> Path:
    """Resolve one regular in-root file without following symlink components."""
    root = Path(os.path.abspath(project_root))
    posix = PurePosixPath(relative)
    if (
        not relative
        or "\\" in relative
        or posix.is_absolute()
        or posix.as_posix() != relative
        or any(part in {"", ".", ".."} for part in posix.parts)
    ):
        raise PublicationMetadataError(f"unsafe {label} path: {relative}")
    for ancestor in (*reversed(root.parents), root):
        if ancestor.is_symlink():
            raise PublicationMetadataError(
                f"unsafe {label}: project root traverses a symlink: {ancestor}"
            )
    candidate = root
    for index, part in enumerate(posix.parts):
        candidate /= part
        if candidate.is_symlink():
            raise PublicationMetadataError(
                f"unsafe {label}: path traverses a symlink: {relative}"
            )
        if (
            index < len(posix.parts) - 1
            and candidate.exists()
            and not candidate.is_dir()
        ):
            raise PublicationMetadataError(
                f"unsafe {label}: path ancestor is not a directory: {relative}"
            )
    if not candidate.is_file():
        raise PublicationMetadataError(f"required {label} is missing: {relative}")
    if not candidate.resolve().is_relative_to(root):
        raise PublicationMetadataError(f"unsafe {label}: path escapes project root")
    return candidate


def _load_yaml_owner(
    project_root: Path, relative: str, *, label: str
) -> dict[str, Any]:
    path = _safe_project_file(project_root, relative, label=label)
    try:
        return _mapping(
            yaml.safe_load(path.read_text(encoding="utf-8")),
            label=label,
        )
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise PublicationMetadataError(f"cannot read {label}: {exc}") from exc


def load_publication_author(project_root: Path) -> PublicationAuthor:
    """Load the single canonical author identity from ``CITATION.cff``."""
    citation = _load_yaml_owner(project_root, "CITATION.cff", label="CITATION.cff")
    authors = citation.get("authors")
    if not isinstance(authors, list) or len(authors) != 1:
        raise PublicationMetadataError(
            "CITATION.cff must declare exactly one canonical author"
        )
    author = _mapping(authors[0], label="CITATION.cff author")
    preferred = _mapping(
        citation.get("preferred-citation"), label="CITATION.cff preferred-citation"
    )
    preferred_authors = preferred.get("authors")
    if (
        not isinstance(preferred_authors, list)
        or len(preferred_authors) != 1
        or preferred_authors[0] is not author
    ):
        raise PublicationMetadataError(
            "CITATION.cff preferred-citation authors must reuse the canonical authors"
        )
    return PublicationAuthor(
        name=(
            f"{_required_text(author, 'given-names', label='CITATION.cff author')} "
            f"{_required_text(author, 'family-names', label='CITATION.cff author')}"
        ),
        affiliation=_required_text(author, "affiliation", label="CITATION.cff author"),
        email=_required_text(author, "email", label="CITATION.cff author"),
        orcid=_required_text(author, "orcid", label="CITATION.cff author"),
    )


def load_repository_url(project_root: Path) -> str:
    """Return the canonical repository URL declared by ``CITATION.cff``.

    Four manuscript hyperlinks previously pointed at ``../docs/...`` and
    ``../src/...``. Those resolve relative to the PDF's own directory, which is
    ``output/pdf/``, so every one of them was dead in the published artifact --
    including the coverage report the manuscript designates as the owner of the
    incidence table. Anchoring them to this URL plus the render's exact commit
    makes them resolvable from anywhere and pinned to the tree they describe.
    """

    citation = _load_yaml_owner(project_root, "CITATION.cff", label="CITATION.cff")
    url = _required_text(citation, "repository-code", label="CITATION.cff")
    if not url.startswith("https://"):
        raise PublicationMetadataError(
            "CITATION.cff repository-code must be an https URL"
        )
    return url.rstrip("/")


def load_graphical_abstract(project_root: Path) -> GraphicalAbstractAsset:
    """Load and validate the configured graphical-abstract cover asset."""
    config = _load_yaml_owner(
        project_root, "manuscript/config.yaml", label="manuscript/config.yaml"
    )
    publication = _mapping(
        config.get("publication"), label="manuscript publication metadata"
    )
    graphical_abstract = _mapping(
        publication.get("graphical_abstract"),
        label="manuscript graphical abstract metadata",
    )
    source_path = _required_text(
        graphical_abstract,
        "path",
        label="manuscript graphical abstract metadata",
    )
    media_type = _required_text(
        graphical_abstract,
        "media_type",
        label="manuscript graphical abstract metadata",
    )
    if media_type != "image/png" or not source_path.endswith(".png"):
        raise PublicationMetadataError(
            "manuscript graphical abstract must be an image/png .png file"
        )
    width_px = _required_positive_int(
        graphical_abstract,
        "width_px",
        label="manuscript graphical abstract metadata",
    )
    height_px = _required_positive_int(
        graphical_abstract,
        "height_px",
        label="manuscript graphical abstract metadata",
    )
    expected_sha256 = _required_text(
        graphical_abstract,
        "sha256",
        label="manuscript graphical abstract metadata",
    )
    if re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is None:
        raise PublicationMetadataError(
            "manuscript graphical abstract sha256 must be 64 lowercase hex characters"
        )
    alt_text = _required_text(
        graphical_abstract,
        "alt_text",
        label="manuscript graphical abstract metadata",
    )
    path = _safe_project_file(
        project_root, source_path, label="graphical abstract asset"
    )
    data = path.read_bytes()
    actual_sha256 = hashlib.sha256(data).hexdigest()
    if actual_sha256 != expected_sha256:
        raise PublicationMetadataError(
            "graphical abstract sha256 does not match manuscript/config.yaml"
        )
    if (
        len(data) < 33
        or data[:8] != b"\x89PNG\r\n\x1a\n"
        or data[8:16] != b"\x00\x00\x00\rIHDR"
    ):
        raise PublicationMetadataError("graphical abstract is not a canonical PNG")
    actual_width, actual_height = struct.unpack(">II", data[16:24])
    if (actual_width, actual_height) != (width_px, height_px):
        raise PublicationMetadataError(
            "graphical abstract dimensions do not match manuscript/config.yaml: "
            f"expected {width_px}x{height_px}, found {actual_width}x{actual_height}"
        )
    if data[24:29] != bytes((8, 2, 0, 0, 0)):
        raise PublicationMetadataError(
            "graphical abstract must be 8-bit non-interlaced RGB PNG"
        )
    return GraphicalAbstractAsset(
        source_path=source_path,
        render_path=f"assets/{PurePosixPath(source_path).name}",
        media_type=media_type,
        width_px=width_px,
        height_px=height_px,
        sha256=actual_sha256,
        alt_text=alt_text,
        data=data,
    )
