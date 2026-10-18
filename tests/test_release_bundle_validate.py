"""Validate release/publication boundary contracts."""

from __future__ import annotations

from pathlib import Path

import pytest

from fep_lean.output import release_bundle as bundle_module
from fep_lean.output.release_bundle import (
    validate_release_bundle,
)
from tests._support.release_bundle import (
    _valid_contents,
)

PROJ = Path(__file__).resolve().parents[1]


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
