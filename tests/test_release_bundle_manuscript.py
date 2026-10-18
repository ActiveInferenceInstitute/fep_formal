"""Manuscript release/publication boundary contracts."""

from __future__ import annotations

import ast
import errno
import hashlib
import json
import os
import re
import shlex
import shutil
import stat
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from fep_lean.output import release_bundle as bundle_module
from fep_lean.output.release_bundle import (
    publication_manuscript_errors,
    render_publication_manuscript,
    write_publication_manuscript,
)
from tests._support.release_bundle import (
    _fixture_renderer_tools,
    _minimal_manuscript,
    _png_bytes,
)

PROJ = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("phase", ["initial", "fallback", "final"])
def test_renderer_identity_cannot_dispatch_or_accept_after_shared_deadline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, phase: str
) -> None:
    from fep_lean.output.release_bundle import _manuscript
    from fep_lean.verification import _subprocess

    clock = [100.0]
    reads: list[str] = []
    calls: list[float] = []
    monkeypatch.setattr(
        _manuscript, "time", SimpleNamespace(monotonic=lambda: clock[0])
    )

    def binary(executable: str) -> tuple[Path, str]:
        reads.append(executable)
        if (
            phase == "initial"
            and len(reads) == 1
            or phase == "final"
            and len(reads) == 2
        ):
            clock[0] += 2.0
        return tmp_path / "tool", "1" * 64

    def probe(command: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(float(kwargs["timeout"]))
        if phase == "fallback":
            clock[0] += 1.0
            return subprocess.CompletedProcess(command, 1, "", "")
        return subprocess.CompletedProcess(command, 0, "fixture tool\n", "")

    monkeypatch.setattr(_manuscript, "_renderer_binary_state", binary)
    monkeypatch.setattr(_subprocess, "run_process_group", probe)
    with pytest.raises(bundle_module.ReleaseBundleError, match="deterministic budget"):
        _manuscript._tool_identity(str(tmp_path / "tool"), timeout=1)
    assert len(calls) == (0 if phase == "initial" else 1)
    assert len(reads) == (2 if phase == "final" else 1)


def test_renderer_identity_fallback_receives_only_remaining_budget(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from fep_lean.output.release_bundle import _manuscript
    from fep_lean.verification import _subprocess

    clock = [100.0]
    calls: list[float] = []
    monkeypatch.setattr(
        _manuscript, "time", SimpleNamespace(monotonic=lambda: clock[0])
    )
    monkeypatch.setattr(
        _manuscript, "_renderer_binary_state", lambda _: (tmp_path / "tool", "1" * 64)
    )

    def probe(command: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(float(kwargs["timeout"]))
        clock[0] += 0.4
        return subprocess.CompletedProcess(
            command,
            1 if len(calls) == 1 else 0,
            "" if len(calls) == 1 else "fixture tool\n",
            "",
        )

    monkeypatch.setattr(_subprocess, "run_process_group", probe)
    assert (
        _manuscript._tool_identity(str(tmp_path / "tool"), timeout=1)["version"]
        == "fixture tool"
    )
    assert calls == pytest.approx([1.0, 0.6])


def test_renderer_preparation_cannot_launch_after_consuming_budget(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from fep_lean.output.release_bundle import _manuscript
    from fep_lean.verification import _subprocess

    clock = [100.0]
    monkeypatch.setattr(
        _manuscript, "time", SimpleNamespace(monotonic=lambda: clock[0])
    )

    def environment(*args: object, **kwargs: object) -> dict[str, str]:
        clock[0] += 1.0
        return {}

    def unexpected(*args: object, **kwargs: object) -> None:
        pytest.fail("expired preparation launched a child")

    monkeypatch.setattr(_manuscript, "_renderer_environment", environment)
    monkeypatch.setattr(_subprocess, "run_process_group", unexpected)
    with pytest.raises(bundle_module.ReleaseBundleError, match="deterministic budget"):
        _manuscript._run_renderer(
            ["unused"],
            project_root=tmp_path,
            environment_root=tmp_path,
            epoch=0,
            timeout=1,
        )


def test_standalone_renderer_refuses_late_supervised_completion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from fep_lean.output.release_bundle import _manuscript
    from fep_lean.verification import _subprocess

    clock = [100.0]
    monkeypatch.setattr(
        _manuscript, "time", SimpleNamespace(monotonic=lambda: clock[0])
    )
    monkeypatch.setattr(
        _manuscript, "_renderer_environment", lambda *args, **kwargs: {}
    )

    def late_completion(
        command: object, **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        clock[0] += 2.0
        return subprocess.CompletedProcess(command, 0, "complete", "")

    monkeypatch.setattr(_subprocess, "run_process_group", late_completion)
    with pytest.raises(bundle_module.ReleaseBundleError, match="deterministic budget"):
        _manuscript._run_renderer(
            ["unused"],
            project_root=tmp_path,
            environment_root=tmp_path,
            epoch=0,
            timeout=1,
        )


@pytest.mark.parametrize("replace_parent", [False, True])
def test_template_gitlink_brackets_the_descriptor_relative_leaf(
    tmp_path: Path, replace_parent: bool
) -> None:
    from fep_lean.output.release_bundle import _core
    from tests.test_distribution import _workflow_python

    template = tmp_path.resolve() / "render-template"
    name = "infrastructure/steganography/kmyth"
    commit = "cb23c6d94423cbe4f5ef0caf23594d1095ddde79"
    path = template / name
    path.mkdir(parents=True)
    script = _workflow_python(
        "Stage accepted render evidence with exact source and tool provenance", "render"
    )
    wanted = {"uninitialized_gitlink", "template_identity"}
    nodes = [
        node
        for node in ast.parse(script).body
        if isinstance(node, ast.FunctionDef) and node.name in wanted
    ]
    assert {node.name for node in nodes} == wanted
    captured: list[int] = []

    def parent_fd(leaf: Path) -> int:
        fd = _core._capture_parent_fd(leaf)
        captured.append(fd)
        if replace_parent:
            leaf.parent.rename(leaf.parent.with_name("retained-original-parent"))
            leaf.mkdir(parents=True)
        return fd

    scope: dict[str, object] = {
        "template": template,
        "allowed_gitlink": (name, commit),
        "os": os,
        "stat": stat,
        "_capture_parent_fd": parent_fd,
    }
    # Execute only allowlisted functions from the held local workflow AST.
    exec(  # noqa: S102
        compile(
            ast.Module(body=nodes, type_ignores=[]),
            "actual held workflow gitlink",
            "exec",
        ),
        scope,
    )
    if os.name != "posix":
        with pytest.raises(bundle_module.ReleaseBundleError, match="POSIX descriptor"):
            scope["uninitialized_gitlink"](name, "160000", commit)
    elif replace_parent:
        with pytest.raises(SystemExit, match="canonical empty directory"):
            scope["uninitialized_gitlink"](name, "160000", commit)
    else:
        result = scope["uninitialized_gitlink"](name, "160000", commit)
        assert result["mode"] == "160000" and result["git_commit"] == commit
        assert result["empty"] is True and len(result["identity"]) == 6
    assert len(captured) == (1 if os.name == "posix" else 0)
    for fd in captured:
        with pytest.raises(OSError) as failure:
            os.fstat(fd)
        assert failure.value.errno == errno.EBADF


@pytest.mark.parametrize("phase", ["artifact", "normalized"])
@pytest.mark.parametrize("mutation", ["symlink", "fifo"])
def test_renderer_artifact_replacement_after_regular_check_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, phase: str, mutation: str
) -> None:
    from fep_lean.output.release_bundle import _manuscript

    changed: list[Path] = []
    original_is_file = Path.is_file
    pdf = b"%PDF-1.4\n<< /ID [<" + b"0" * 32 + b"> <" + b"F" * 32 + b">] >>\n"

    def complete(command: tuple[str, ...], **kwargs: object) -> object:
        output = (
            command[-1]
            if command[0] == "mutool"
            else next(
                item.split("=", 1)[1]
                for item in command
                if item.startswith("--output=")
            )
        )
        Path(output).write_bytes(pdf)
        return SimpleNamespace(returncode=0)

    def replace_after_check(path: Path) -> bool:
        regular = original_is_file(path)
        wanted = path.name == (
            "render-0.pdf" if phase == "artifact" else "normalized.pdf"
        )
        if os.name == "posix" and regular and wanted and not changed:
            path.unlink()
            if mutation == "fifo":
                os.mkfifo(path)
            else:
                target = path.parent / "forbidden.pdf"
                target.write_bytes(pdf)
                path.symlink_to(target.name)
            changed.append(path)
        return regular

    monkeypatch.setattr(bundle_module, "_run_renderer", complete)
    monkeypatch.setattr(Path, "is_file", replace_after_check)
    started = time.monotonic()
    with pytest.raises((bundle_module.ReleaseBundleError, OSError)) as failure:
        _manuscript._render_twice(
            ("pandoc",),
            project_root=tmp_path,
            epoch=0,
            suffix=".pdf",
            extra_args=(),
            timeout=5,
            pdf_normalizer="mutool" if phase == "normalized" else None,
        )
    assert time.monotonic() - started < 3
    if os.name == "posix":
        assert len(changed) == 1
        if isinstance(failure.value, OSError):
            assert failure.value.errno == errno.ELOOP
        else:
            assert "capture" in str(failure.value)
    else:
        assert "POSIX descriptor" in str(failure.value)


@pytest.mark.parametrize(
    "control", ["regular", "executable", "hidden_mode", "read_mode", "read_replacement"]
)
def test_template_manifest_checks_physical_mode_and_read_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, control: str
) -> None:
    from fep_lean.output.release_bundle import _core
    from tests.test_distribution import _workflow_python

    root = tmp_path.resolve()
    template = root / "render-template"
    template.mkdir()
    owner = template / "owner.txt"
    owner.write_bytes(b"tracked template bytes\n")
    (template / ".gitignore").write_text("projects/active/fep_lean\n")
    if control == "executable":
        owner.chmod(0o755)
    for args in (
        ["init", "-q"],
        ["config", "core.fsmonitor", "false"],
        ["config", "user.name", "Fixture"],
        ["config", "user.email", "fixture@example.invalid"],
        ["add", "."],
        ["commit", "-qm", "fixture"],
        ["config", "core.filemode", "false"],
    ):
        subprocess.run(
            ["git", "-c", "core.fsmonitor=false", *args],
            cwd=template,
            check=True,
            capture_output=True,
            timeout=5,
        )
    if os.name == "posix":
        registration = template / "projects/active/fep_lean"
        registration.parent.mkdir(parents=True)
        registration.symlink_to(str(root), target_is_directory=True)
    if control == "hidden_mode":
        owner.chmod(0o755)
    script = _workflow_python(
        "Stage accepted render evidence with exact source and tool provenance", "render"
    )
    wanted = {
        "require_clean_template",
        "template_blob",
        "uninitialized_gitlink",
        "template_identity",
        "template_manifest",
    }
    nodes = [
        node
        for node in ast.parse(script).body
        if isinstance(node, ast.FunctionDef) and node.name in wanted
    ]
    assert {node.name for node in nodes} == wanted
    scope: dict[str, object] = {
        "root": root,
        "template": template,
        "Path": Path,
        "hashlib": hashlib,
        "os": os,
        "stat": stat,
        "subprocess": subprocess,
        "allowed_gitlink": (
            "infrastructure/steganography/kmyth",
            "cb23c6d94423cbe4f5ef0caf23594d1095ddde79",
        ),
    }
    scope["template_sha"] = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=template, text=True, timeout=5
    ).strip()
    scope["template_object_format"] = subprocess.check_output(
        ["git", "rev-parse", "--show-object-format"], cwd=template, text=True, timeout=5
    ).strip()
    for name in (
        "_capture_directory_paths",
        "_capture_link_bytes",
        "_capture_parent_fd",
        "_capture_regular_file",
        "_capture_resource_link_target",
        "_capture_template_links",
    ):
        scope[name] = getattr(_core, name)
    # Execute only allowlisted functions from the held local workflow AST.
    exec(  # noqa: S102
        compile(
            ast.Module(body=nodes, type_ignores=[]),
            "actual held workflow manifest",
            "exec",
        ),
        scope,
    )
    changed: list[Path] = []

    def capture(path: Path) -> bytes:
        data = _core._capture_regular_file(path)
        if (
            path == owner
            and control in {"read_mode", "read_replacement"}
            and not changed
        ):
            if control == "read_mode":
                path.chmod(0o755)
            else:
                replacement = path.with_name("replacement")
                replacement.write_bytes(data)
                replacement.replace(path)
            changed.append(path)
        return data

    scope["_capture_regular_file"] = capture
    if os.name != "posix":
        with pytest.raises(bundle_module.ReleaseBundleError, match="POSIX descriptor"):
            scope["template_manifest"]()
    elif control in {"hidden_mode", "read_mode", "read_replacement"}:
        message = (
            "physical mode differs"
            if control == "hidden_mode"
            else "changed while reading"
        )
        with pytest.raises(SystemExit, match=message):
            scope["template_manifest"]()
        assert (
            subprocess.check_output(
                ["git", "diff", "--name-only", "HEAD", "-z"], cwd=template, timeout=5
            )
            == b""
        )
    else:
        result = scope["template_manifest"]()
        assert result["sources"]["owner.txt"]["mode"] == (
            "100755" if control == "executable" else "100644"
        )
        assert (
            result["sources"]["owner.txt"]["sha256"]
            == hashlib.sha256(owner.read_bytes()).hexdigest()
        )
    assert not (root / "output/render-evidence").exists()


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
    if any(
        shutil.which(name) is None
        for name in ("pandoc", "xelatex", "xdvipdfmx", "mutool")
    ):
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

    from fep_lean.output.release_bundle import _manuscript

    original_read = _manuscript._capture_regular_file

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
    monkeypatch.setattr(_manuscript, "_capture_regular_file", delayed_artifact_read)
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
