"""Assemble release/publication boundary contracts."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from fep_lean.output import release_bundle as bundle_module
from fep_lean.output.release_bundle import (
    build_release_bundle,
    validate_release_bundle,
    write_publication_manuscript,
)
from tests._support.release_bundle import (
    _valid_contents,
)

PROJ = Path(__file__).resolve().parents[1]


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
