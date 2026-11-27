"""Reject unsafe or inconsistent cover inputs through the public metadata API."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
import yaml
from PIL import Image

from fep_formal.output.publication_metadata import (
    PublicationMetadataError,
    load_graphical_abstract,
    load_repository_url,
    project_cover_author,
)


def _asset_project(root: Path) -> tuple[dict[str, object], bytes]:
    (root / "docs" / "manuscript").mkdir()
    image = root / "cover.png"
    Image.new("RGB", (2, 2), (10, 20, 30)).save(image)
    data = image.read_bytes()
    metadata: dict[str, object] = {
        "path": "cover.png",
        "media_type": "image/png",
        "width_px": 2,
        "height_px": 2,
        "sha256": hashlib.sha256(data).hexdigest(),
        "alt_text": "A small valid cover fixture.",
    }
    _write_asset_metadata(root, metadata)
    return metadata, data


def _write_asset_metadata(root: Path, value: object) -> None:
    (root / "docs/manuscript/config.yaml").write_text(
        yaml.safe_dump({"publication": {"graphical_abstract": value}}), encoding="utf-8"
    )


def test_cover_asset_valid_bytes_and_public_projection(tmp_path: Path) -> None:
    metadata, data = _asset_project(tmp_path)
    asset = load_graphical_abstract(tmp_path)
    assert asset.data == data
    assert asset.manuscript_variables() == {
        "source_path": "cover.png",
        "render_path": "assets/cover.png",
        **{key: value for key, value in metadata.items() if key != "path"},
    }


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("path", "../cover.png", "unsafe graphical abstract asset path"),
        ("path", "assets//cover.png", "unsafe graphical abstract asset path"),
        ("path", "absent.png", "required graphical abstract asset is missing"),
        ("media_type", "image/jpeg", "must be an image/png"),
        ("sha256", "not-a-digest", "64 lowercase hex"),
        ("sha256", "0" * 64, "sha256 does not match"),
        ("width_px", 3, "dimensions do not match"),
        ("height_px", True, "positive integer"),
        ("alt_text", "  ", "non-empty string"),
    ],
)
def test_cover_asset_rejects_invalid_metadata(
    tmp_path: Path, field: str, value: object, reason: str
) -> None:
    metadata, before = _asset_project(tmp_path)
    metadata[field] = value
    _write_asset_metadata(tmp_path, metadata)
    with pytest.raises(PublicationMetadataError, match=reason):
        load_graphical_abstract(tmp_path)
    assert (tmp_path / "cover.png").read_bytes() == before


@pytest.mark.parametrize("kind", ("symlink", "file_parent", "root_symlink"))
def test_cover_asset_rejects_filesystem_aliases(tmp_path: Path, kind: str) -> None:
    project = tmp_path / "project"
    project.mkdir()
    metadata, before = _asset_project(project)
    if kind == "symlink":
        (project / "alias.png").symlink_to(project / "cover.png")
        metadata["path"] = "alias.png"
        reason = "traverses a symlink"
    elif kind == "file_parent":
        (project / "blocker").write_text("ordinary file")
        metadata["path"] = "blocker/cover.png"
        reason = "ancestor is not a directory"
    else:
        alias = tmp_path / "alias"
        alias.symlink_to(project, target_is_directory=True)
        project = alias
        reason = "project root traverses a symlink"
    _write_asset_metadata(project, metadata)
    with pytest.raises(PublicationMetadataError, match=reason):
        load_graphical_abstract(project)
    assert (project / "cover.png").read_bytes() == before


@pytest.mark.parametrize("kind", ("bad_header", "rgba"))
def test_cover_asset_rejects_invalid_png_after_digest_match(
    tmp_path: Path, kind: str
) -> None:
    metadata, data = _asset_project(tmp_path)
    if kind == "bad_header":
        data = b"not a PNG even though the digest matches"
        reason = "not a canonical PNG"
    else:
        Image.new("RGBA", (2, 2), (10, 20, 30, 255)).save(tmp_path / "cover.png")
        data = (tmp_path / "cover.png").read_bytes()
        reason = "8-bit non-interlaced RGB PNG"
    (tmp_path / "cover.png").write_bytes(data)
    metadata["sha256"] = hashlib.sha256(data).hexdigest()
    _write_asset_metadata(tmp_path, metadata)
    with pytest.raises(PublicationMetadataError, match=reason):
        load_graphical_abstract(tmp_path)


@pytest.mark.parametrize("payload", (b"[unterminated", b"\xff"))
def test_repository_owner_rejects_unreadable_yaml(
    tmp_path: Path, payload: bytes
) -> None:
    (tmp_path / "CITATION.cff").write_bytes(payload)
    with pytest.raises(PublicationMetadataError, match="cannot read CITATION.cff"):
        load_repository_url(tmp_path)


def test_repository_owner_rejects_insecure_url_and_nonmapping(tmp_path: Path) -> None:
    owner = tmp_path / "CITATION.cff"
    owner.write_text("repository-code: http://example.invalid/repo\n")
    with pytest.raises(PublicationMetadataError, match="must be an https URL"):
        load_repository_url(tmp_path)
    owner.write_text("- not a mapping\n")
    with pytest.raises(PublicationMetadataError, match="must be a mapping"):
        load_repository_url(tmp_path)


@pytest.mark.parametrize("payload", (b"[unterminated", b"\xff"))
def test_cover_projection_rejects_invalid_yaml_before_owner_lookup(
    tmp_path: Path, payload: bytes
) -> None:
    with pytest.raises(
        PublicationMetadataError, match="invalid manuscript cover config"
    ):
        project_cover_author(payload, tmp_path)
