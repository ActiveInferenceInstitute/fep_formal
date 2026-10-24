"""Supplemental regression controls outside the fixed 80-item installed matrix."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from fep_lean.output.render_log import build_acceptance_receipt
from fep_lean.output.rendering import MANUSCRIPT_ASSETS
from tests.test_distribution import (
    _TEMPLATE_GITLINK,
    PROJECT_ROOT,
    _init_fixture_repository,
    _workflow_python,
)
from tests.test_distribution import (
    _TEMPLATE_SUCCESS_CASES as _ORIGINAL_TEMPLATE_SUCCESS_CASES,
)

_TEMPLATE_SUCCESS_CASES = _ORIGINAL_TEMPLATE_SUCCESS_CASES | {"executable_owner"}


def test_q7_scaffold_bytes_refuse_cp1252_codepage_substitution() -> None:
    """Wrong text decoding must not become accepted canonical AST evidence."""
    from fep_lean.verification.gnn_continuous_artifact_proof import (
        canonical_scaffold_bytes,
    )

    fixture_root = PROJECT_ROOT / "specs/gnn-bridge-q7-continuous-ou-proof"
    source = fixture_root / "fixtures/continuous_ou_jax.py"
    expected = json.loads((fixture_root / "expected.json").read_text(encoding="utf-8"))[
        "runner_ast_sha256"
    ]
    utf8 = source.read_text(encoding="utf-8")
    cp1252_decoded = source.read_text(encoding="cp1252")
    assert utf8 != cp1252_decoded, "control requires the actual UTF-8 scaffold text"
    assert hashlib.sha256(canonical_scaffold_bytes(utf8)).hexdigest() == expected
    assert (
        hashlib.sha256(canonical_scaffold_bytes(cp1252_decoded)).hexdigest() != expected
    )


def test_staging_detects_physical_template_mode_drift_hidden_from_git(
    tmp_path: Path,
) -> None:
    _exercise_render_artifact_staging(tmp_path, failure="during_template_mode_drift")


@pytest.mark.parametrize("template_case", ("executable_owner", "during_link_read"))
def test_staging_retains_executable_owners_and_rejects_link_read_races(
    tmp_path: Path, template_case: str
) -> None:
    _exercise_render_artifact_staging(tmp_path, template_case=template_case)


# Bounded PR45 helper snapshot: retain the original installed 80-case matrix
# and security assertions; both fixture producers follow receipt version 2.
def _exercise_render_artifact_staging(
    tmp_path: Path,
    *,
    failure: str | None = None,
    template_case: str | None = None,
    gitlink_case: str | None = None,
) -> None:
    staging_step = next(
        step
        for step in yaml.safe_load(
            (PROJECT_ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        )["jobs"]["render"]["steps"]
        if step.get("name")
        == "Stage accepted render evidence with exact source and tool provenance"
    )
    assert (
        staging_step["env"]["EXPECTED_TEMPLATE_SHA"]
        == "5b3c0f43940f0322fbc6205b3be4c2854f99329d"
    )
    # The operator context supplies this real fixture HEAD below. Git commands
    # and recorded entry OIDs stay real; the fixture is never called the pin.
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "01_abstract.md").write_text("A rendered statement.\n")
    (manuscript / "preamble.md").write_text("\\setmainfont{TestFont}\n")
    (manuscript / "09z_unified_formalism_catalogue.md").write_text("Appendix.\n")
    (manuscript / "manuscript_vars.yaml").write_text("{}\n")
    (manuscript / "config.yaml").write_text(
        "title: Fixture publication\npublication:\n  number_unlabeled_equations: true\n"
    )
    (manuscript / "references.bib").write_text(
        "@misc{fixture, title={Fixture source}}\n"
    )
    for source, _destination in MANUSCRIPT_ASSETS.values():
        path = tmp_path / source
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"fixture asset")
    pdf = tmp_path / "output/pdf"
    pdf.mkdir(parents=True)
    for name in (
        "_combined_manuscript.tex",
        "_combined_manuscript.md",
        "_latex_stdout.log",
    ):
        (pdf / name).write_text("fixture render\n")
    (pdf / "_combined_manuscript.tex").write_text(
        "\\begin{equation}\\label{eq:fixture}x=x\\end{equation}\n"
    )
    (pdf / "fep_lean_combined.pdf").write_bytes(b"%PDF-fixture")
    (pdf / "_combined_manuscript.log").write_text(
        "Output written on fep_lean_combined.pdf (1 page).\n"
    )
    for name in ("native-verification.json", "formalism-audit.json"):
        (tmp_path / "output" / name).write_text("{}\n")
    receipt = build_acceptance_receipt(
        manuscript,
        pdf,
        counts=dict.fromkeys(
            (
                "tex_errors",
                "missing_characters",
                "mermaid_fallbacks",
                "stale_sources",
                "uncaptioned_tables",
                "contents_number_overflows",
                "unresolved_references",
                "publication_cover",
                "unnumbered_equations",
            ),
            0,
        ),
    )
    receipt_path = tmp_path / "docs/render-acceptance.json"
    receipt_path.write_text(json.dumps(receipt))
    (tmp_path / "docs/render-fonts.json").write_text("{}\n")
    font = tmp_path / "font.ttf"
    font.write_bytes(b"fixture font bytes")
    selected_font = tmp_path.parent / f"{tmp_path.name}-selected-font.ttf"
    selected_font.write_bytes(b"fixture selected font bytes")
    (tmp_path / ".gitignore").write_text("output/\n")
    git_env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "Test",
        "GIT_AUTHOR_EMAIL": "test@example.invalid",
        "GIT_COMMITTER_NAME": "Test",
        "GIT_COMMITTER_EMAIL": "test@example.invalid",
    }
    _init_fixture_repository(tmp_path)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "-c", "commit.gpgsign=false", "commit", "-qm", "fixture"],
        cwd=tmp_path,
        env=git_env,
        check=True,
    )
    sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True
    ).strip()
    template = tmp_path / "output/render-template"
    template.mkdir()
    _init_fixture_repository(template)
    template_files = {"README.md": b"Pinned template source.\n"}
    template_links: dict[str, str] = {}
    template_gitlinks: dict[str, str] = {}
    template_ignore = "projects/active/fep_lean\n"
    registration = template / "projects/active/fep_lean"
    # Unsupported platforms refuse at the real artifact custody reader before
    # template discovery. Every parameter still executes that staging boundary.
    if os.name == "posix":
        gitlink_path = template / _TEMPLATE_GITLINK[0]
        gitlink_path.mkdir(parents=True)
        template_gitlinks[_TEMPLATE_GITLINK[0]] = _TEMPLATE_GITLINK[1]
        registration.parent.mkdir(parents=True)
        registration.symlink_to(tmp_path, target_is_directory=True)
        if template_case is not None:
            template_files.update(
                {
                    "resources/data.txt": b"First template resource.\n",
                    "resources/other.txt": b"Other template resource.\n",
                }
            )
            if template_case != "relative_directory":
                template_links["file-link"] = "resources/data.txt"
            if template_case not in {"relative_file", "absolute_internal_file"}:
                template_links["directory-link"] = "resources"
            if template_case == "absolute_internal_file":
                template_links["file-link"] = str(template / "resources/data.txt")
            elif template_case == "absolute_escape":
                template_links["file-link"] = str(font)
            elif template_case == "missing_target":
                template_links["file-link"] = "resources/missing.txt"
            elif template_case == "cyclic_target":
                template_links["file-link"] = "cycle-link"
                template_links["cycle-link"] = "file-link"
            elif template_case == "noncanonical_target":
                template_links["file-link"] = "resources/../README.md"
            elif template_case == "excluded_target":
                template_ignore += ".venv/\n"
                cache = template / ".venv/cache.txt"
                cache.parent.mkdir()
                cache.write_bytes(b"private fixture cache")
                template_links["file-link"] = ".venv/cache.txt"
            elif template_case == "regular_mode_as_link":
                template_files["mode-owner.txt"] = b"resources/data.txt"
            elif template_case == "executable_owner":
                template_files["tools/run.py"] = b"print('template executable')\n"
            elif template_case == "untracked_file_referent":
                template_links["file-link"] = "resources/ignored.txt"
            elif template_case == "empty_directory_referent":
                (template / "empty-resources").mkdir()
                template_links["directory-link"] = "empty-resources"
            elif template_case == "ignored_untracked_link":
                template_ignore += "ignored-link\n"
                template_links["ignored-link"] = "README.md"
            if template_case in {
                "untracked_file_referent",
                "untracked_directory_referent",
            }:
                template_ignore += "resources/ignored.txt\n"
                ignored = template / "resources/ignored.txt"
                ignored.parent.mkdir(exist_ok=True)
                ignored.write_bytes(b"untracked template referent")
            elif template_case == "directory_excluded_cache":
                template_ignore += "resources/__pycache__/\n"
                cache = template / "resources/__pycache__/ignored.pyc"
                cache.parent.mkdir(parents=True)
                cache.write_bytes(b"excluded fixture bytecode")
    template_files[".gitignore"] = template_ignore.encode("utf-8")
    for name, data in template_files.items():
        path = template / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        if os.name == "posix" and name == "tools/run.py":
            path.chmod(0o755)
    for name, target in template_links.items():
        (template / name).symlink_to(
            target, target_is_directory=name == "directory-link"
        )
    subprocess.run(["git", "add", "."], cwd=template, check=True)
    for name, commit in template_gitlinks.items():
        subprocess.run(
            ["git", "update-index", "--add", "--cacheinfo", f"160000,{commit},{name}"],
            cwd=template,
            check=True,
        )
    if os.name == "posix" and template_case == "tracked_registration":
        subprocess.run(
            ["git", "add", "-f", "--", "projects/active/fep_lean"],
            cwd=template,
            check=True,
        )
    subprocess.run(
        [
            "git",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "--allow-empty",
            "-qm",
            "template",
        ],
        cwd=template,
        env=git_env,
        check=True,
    )
    if os.name == "posix":
        hidden_owner = None
        if template_case == "link_mode_as_regular":
            owner = template / "file-link"
            owner.unlink()
            owner.write_bytes(b"resources/data.txt")
            hidden_owner = "file-link"
        elif template_case == "regular_mode_as_link":
            owner = template / "mode-owner.txt"
            owner.unlink()
            owner.symlink_to("resources/data.txt")
            hidden_owner = "mode-owner.txt"
        elif template_case in {
            "modified_referent",
            "modified_referent_hidden_from_git_diff",
        }:
            (template / "resources/data.txt").write_bytes(
                b"Changed template resource.\n"
            )
            if template_case == "modified_referent_hidden_from_git_diff":
                hidden_owner = "resources/data.txt"
        elif template_case == "wrong_internal_registration":
            registration.unlink()
            registration.symlink_to("../../README.md")
        elif template_case == "missing_registration":
            registration.unlink()
        elif template_case == "unsupported_git_mode":
            if gitlink_case in {"changed_mode_regular", "changed_mode_symlink"}:
                gitlink_path.rmdir()
                if gitlink_case == "changed_mode_regular":
                    gitlink_path.write_text("changed Git mode")
                else:
                    gitlink_path.symlink_to("../../README.md")
                subprocess.run(
                    [
                        "git",
                        "update-index",
                        "--force-remove",
                        "--",
                        _TEMPLATE_GITLINK[0],
                    ],
                    cwd=template,
                    check=True,
                )
                subprocess.run(
                    ["git", "add", "--", _TEMPLATE_GITLINK[0]], cwd=template, check=True
                )
                subprocess.run(
                    [
                        "git",
                        "-c",
                        "commit.gpgsign=false",
                        "commit",
                        "-qm",
                        "changed gitlink mode",
                    ],
                    cwd=template,
                    env=git_env,
                    check=True,
                )
            elif gitlink_case in {"unknown_path", "changed_commit"}:
                name = (
                    "gitlink"
                    if gitlink_case == "unknown_path"
                    else _TEMPLATE_GITLINK[0]
                )
                oid = subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], cwd=template, text=True
                ).strip()
                if gitlink_case == "unknown_path":
                    (template / name).mkdir()
                subprocess.run(
                    [
                        "git",
                        "update-index",
                        "--add",
                        "--cacheinfo",
                        f"160000,{oid},{name}",
                    ],
                    cwd=template,
                    check=True,
                )
                subprocess.run(
                    ["git", "-c", "commit.gpgsign=false", "commit", "-qm", "gitlink"],
                    cwd=template,
                    env=git_env,
                    check=True,
                )
            elif gitlink_case == "nonempty":
                (gitlink_path / "payload.txt").write_text("uninitialized content")
            elif gitlink_case == "initialized_gitfile":
                (gitlink_path / ".git").write_text(
                    "gitdir: /must-not-read-external-git-store\n"
                )
            elif gitlink_case == "initialized_gitdirectory":
                (gitlink_path / ".git").mkdir()
            elif gitlink_case in {"symlink", "regular_file", "missing"}:
                gitlink_path.rmdir()
                if gitlink_case == "symlink":
                    gitlink_path.symlink_to(template / "README.md")
                elif gitlink_case == "regular_file":
                    gitlink_path.write_text("gitlink must be a directory")
            elif gitlink_case == "parent_symlink":
                gitlink_path.rmdir()
                gitlink_path.parent.rmdir()
                redirected = template / "redirected-steganography"
                (redirected / "kmyth").mkdir(parents=True)
                gitlink_path.parent.symlink_to(redirected, target_is_directory=True)
        if hidden_owner is not None:
            # Exercise the manifest's real mode/blob checks independently of
            # Git's advisory worktree status; no Git command output is mocked.
            subprocess.run(
                ["git", "update-index", "--assume-unchanged", "--", hidden_owner],
                cwd=template,
                check=True,
            )
            assert not subprocess.check_output(
                ["git", "diff", "--name-only", "HEAD", "-z"], cwd=template
            )
    if failure == "stale_receipt":
        (manuscript / "01_abstract.md").write_text("Unaccepted change.\n")
    elif failure == "missing_pdf":
        (pdf / "fep_lean_combined.pdf").unlink()
    elif failure == "legacy_pdf_only":
        (pdf / "fep_lean_combined.pdf").rename(pdf / "_combined_manuscript.pdf")
    elif failure == "source_drift":
        font.write_bytes(b"changed tracked input")
    elif failure == "during_template_mode_drift":
        subprocess.run(
            ["git", "config", "core.filemode", "false"], cwd=template, check=True
        )
    elif failure == "untracked_chapter":
        (manuscript / "02_extra.md").write_text("An uncommitted accepted chapter.\n")
        receipt = build_acceptance_receipt(manuscript, pdf, counts=receipt["checks"])
        receipt_path.write_text(json.dumps(receipt))
    # Native/audit validation and renderer/font discovery are stubbed; git,
    # manuscript receipt validation, sources, staging and hashes remain real.
    # This verifies retention, not native compilation or a physical render.
    version_mutation = {
        "during_source_drift": "Path('manuscript/01_abstract.md').write_text('Changed during provenance discovery.\\n')",
        "during_chapter_addition": "Path('manuscript/02_extra.md').write_text('Added during provenance discovery.\\n')",
        "during_pdf_drift": "Path('output/pdf/fep_lean_combined.pdf').write_bytes(b'%PDF-unaccepted replacement')",
        "during_template_drift": "Path('output/render-template/README.md').write_text('Uncommitted template mutation.\\n')",
        "during_template_mode_drift": "Path('output/render-template/README.md').chmod(0o755); assert not _real_check_output(['git', '-C', 'output/render-template', 'diff', '--ignore-submodules=all', '--name-only', 'HEAD', '-z'])",
    }.get(failure, "pass")
    staged_mutation = {
        "while_staging_source_drift": "Path('manuscript/01_abstract.md').write_text('Changed while retaining evidence.\\n')",
        "while_staging_pdf_drift": "_real_write_bytes(Path('output/pdf/fep_lean_combined.pdf'), b'%PDF-changed while retaining evidence')",
        "retained_pdf_drift": "_real_write_bytes(path, b'%PDF-corrupted retained artifact')",
    }.get(failure, "pass")
    template_mutations = {
        "template_source": "Path('output/render-template/README.md').write_bytes(b'Changed template source.\\n')",
        "template_link": "Path('output/render-template/file-link').unlink(); Path('output/render-template/file-link').symlink_to('resources/other.txt')",
        "template_referent": "Path('output/render-template/resources/data.txt').write_bytes(b'Changed template referent.\\n')",
        "registration": "Path('output/render-template/projects/active/fep_lean').unlink(); Path('output/render-template/projects/active/fep_lean').symlink_to('../../README.md')",
    }
    gitlink_mutation = (
        f"Path('output/render-template/{_TEMPLATE_GITLINK[0]}/unexpected').write_text('changed gitlink')"
        if gitlink_case is not None and gitlink_case.endswith("nonempty")
        else f"_gitlink = Path('output/render-template/{_TEMPLATE_GITLINK[0]}'); _before = _gitlink.stat(); os.utime(_gitlink, ns=(_before.st_atime_ns, _before.st_mtime_ns + 1))"
    )
    if template_case is not None and template_case.startswith("discovery_"):
        version_mutation = template_mutations[template_case.removeprefix("discovery_")]
    elif template_case is not None and template_case.startswith("retention_"):
        staged_mutation = template_mutations[template_case.removeprefix("retention_")]
    if gitlink_case is not None and gitlink_case.startswith("discovery_"):
        version_mutation = gitlink_mutation
    elif gitlink_case is not None and gitlink_case.startswith("retention_"):
        staged_mutation = gitlink_mutation
    retained_read_mutation = {
        "retained_read_source_drift": "Path('manuscript/01_abstract.md').write_text('Changed while verifying retained bytes.\\n')",
        "retained_read_pdf_drift": "_real_write_bytes(Path('output/pdf/fep_lean_combined.pdf'), b'%PDF-changed during retained read')",
    }.get(failure, "pass")
    script = (
        "import os\n"
        "import subprocess\n"
        "from pathlib import Path\n"
        "_real_readlink = os.readlink\n"
        "_link_read_mutated = False\n"
        "def _mutating_readlink(path, **kwargs):\n"
        "    global _link_read_mutated\n"
        "    data = _real_readlink(path, **kwargs)\n"
        f"    if {template_case == 'during_link_read'!r} and kwargs.get('dir_fd') is not None and os.fsdecode(path) == 'file-link' and not _link_read_mutated:\n"
        "        owner = Path('output/render-template/file-link')\n"
        "        owner.unlink()\n"
        "        owner.symlink_to('resources/other.txt')\n"
        "        _link_read_mutated = True\n"
        "    return data\n"
        "os.readlink = _mutating_readlink\n"
        "import fep_lean.output.evidence as _native\n"
        "import fep_lean.verification.formalism_audit as _audit\n"
        f"_native.validate_native_lean_receipt = lambda *args, **kwargs: {{'native_claim_ready': {failure != 'native_stale'!r}}}\n"
        f"_audit.validate_formalism_audit_receipt = lambda *args, **kwargs: {('fixture audit is stale',) if failure == 'audit_stale' else ()!r}\n"
        "_real_check_output = subprocess.check_output\n"
        "def _version_probe(argv, **kwargs):\n"
        "    if argv[0] == 'fc-match':\n"
        f"        return {str(selected_font)!r} + '\\n'\n"
        "    if argv[0] in {'xelatex', 'pandoc', 'pandoc-crossref', 'rsvg-convert', 'mmdc'}:\n"
        "        if argv[0] == 'xelatex':\n"
        f"            {version_mutation}\n"
        "        return 'fixture version 1\\n'\n"
        "    if argv[1:] == ['--version']:\n"
        "        raise AssertionError(f'Unmodelled tool version probe: {argv[0]}')\n"
        "    return _real_check_output(argv, **kwargs)\n"
        "subprocess.check_output = _version_probe\n"
        "_real_write_bytes = Path.write_bytes\n"
        "def _staged_write(path, data):\n"
        "    result = _real_write_bytes(path, data)\n"
        "    if 'render-evidence' in path.parts and path.name == 'fep_lean_combined.pdf':\n"
        f"        {staged_mutation}\n"
        f"        if {failure == 'during_font_drift'!r}:\n"
        f"            _real_write_bytes(Path({str(selected_font)!r}), b'changed selected font bytes')\n"
        "    return result\n"
        "Path.write_bytes = _staged_write\n"
        "import fep_lean.output.release_bundle._core as _capture_owner\n"
        "_real_regular_read = _capture_owner._capture_regular_file\n"
        "_inventory_gitlink_mutated = False\n"
        "def _retained_read(path):\n"
        "    global _inventory_gitlink_mutated\n"
        "    data = _real_regular_read(path)\n"
        f"    if {gitlink_case is not None and gitlink_case.startswith('inventory_')!r} and path.name == 'README.md' and path.parent.name == 'render-template' and not _inventory_gitlink_mutated:\n"
        f"        {gitlink_mutation}\n"
        "        _inventory_gitlink_mutated = True\n"
        "    if 'render-evidence' in path.parts and path.name == 'fep_lean_combined.pdf':\n"
        f"        {retained_read_mutation}\n"
        "    return data\n"
        "_capture_owner._capture_regular_file = _retained_read\n"
        + _workflow_python(
            "Stage accepted render evidence with exact source and tool provenance",
            "render",
        )
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=tmp_path,
        env={
            **os.environ,
            "PYTHONPATH": str(PROJECT_ROOT / "src"),
            "EXPECTED_SHA": "0" * 40 if failure == "wrong_sha" else sha,
            "EXPECTED_TEMPLATE_SHA": "0" * 40
            if gitlink_case == "wrong_template_sha"
            else subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=template, text=True
            ).strip(),
            "WORKFLOW_RUN_ID": "fixture",
            "WORKFLOW_RUN_ATTEMPT": "1",
        },
        capture_output=True,
        text=True,
        check=False,
    )
    staged = tmp_path / "output/render-evidence"
    if os.name != "posix" and failure not in {
        "wrong_sha",
        "missing_pdf",
        "legacy_pdf_only",
    }:
        # The real custody reader refuses before source/receipt drift checks
        # on unsupported platforms. Execute the stage and assert that boundary.
        assert result.returncode != 0
        assert (
            "ReleaseBundleError: capture custody requires POSIX descriptor-relative reads"
            in result.stderr
        )
        assert not staged.exists()
        return
    if template_case is not None and template_case not in _TEMPLATE_SUCCESS_CASES:
        assert result.returncode != 0
        assert not staged.exists()
        expected_error = {
            "absolute_escape": "capture resource link escapes its owner",
            "missing_target": "capture resource link target is missing or cyclic",
            "cyclic_target": "capture resource link target is missing or cyclic",
            "noncanonical_target": "capture resource link target spelling is invalid",
            "excluded_target": "capture resource link targets an excluded subtree",
            "link_mode_as_regular": "template resource link membership differs from its recorded commit",
            "regular_mode_as_link": "template resource link membership differs from its recorded commit",
            "untracked_file_referent": "template link referent is not tracked at its recorded commit",
            "untracked_directory_referent": "template link referent is not tracked at its recorded commit",
            "empty_directory_referent": "template link referent is not tracked at its recorded commit",
            "modified_referent": "template authored inputs differ from its recorded commit",
            "modified_referent_hidden_from_git_diff": "template tracked resource differs from its recorded blob",
            "unsupported_git_mode": (
                "template checkout differs from the workflow template pin"
                if gitlink_case == "wrong_template_sha"
                else "template tracked resource mode is unsupported"
                if gitlink_case
                in {
                    "unknown_path",
                    "changed_commit",
                    "changed_mode_regular",
                    "changed_mode_symlink",
                }
                else "changed during evidence staging"
                if gitlink_case is not None and gitlink_case.endswith("empty_metadata")
                else "template allowed gitlink is not a canonical empty directory"
            ),
            "ignored_untracked_link": "template resource link membership differs from its recorded commit",
            "wrong_internal_registration": "template active-project registration differs from this checkout",
            "tracked_registration": "template active-project registration differs from this checkout",
            "missing_registration": "template resource link membership differs from its recorded commit",
            "during_link_read": "capture resource link changed",
        }.get(template_case, "changed during evidence staging")
        assert expected_error in result.stderr
    elif failure:
        assert result.returncode != 0
        assert not staged.exists()
        expected_error = {
            "wrong_sha": "differs from workflow SHA",
            "stale_receipt": "predates these sources",
            "missing_pdf": "accepted render evidence is missing",
            "legacy_pdf_only": "accepted render evidence is missing: output/pdf/fep_lean_combined.pdf",
            "source_drift": "tracked render inputs changed",
            "native_stale": "native evidence is not claim-ready",
            "audit_stale": "fixture audit is stale",
            "untracked_chapter": "authored manuscript source is not tracked",
            "during_source_drift": "changed during evidence staging",
            "during_chapter_addition": "changed during evidence staging",
            "during_pdf_drift": "changed during evidence staging",
            "during_template_drift": "changed during evidence staging",
            "during_template_mode_drift": "changed during evidence staging",
            "during_font_drift": "changed during evidence staging",
            "while_staging_source_drift": "changed during evidence staging",
            "while_staging_pdf_drift": "changed during evidence staging",
            "retained_pdf_drift": "changed during evidence staging",
            "retained_read_source_drift": "changed during evidence staging",
            "retained_read_pdf_drift": "changed during evidence staging",
        }[failure]
        assert expected_error in result.stderr
    else:
        assert result.returncode == 0, result.stderr or result.stdout
        manifest = json.loads((staged / "artifact-manifest.json").read_text())
        assert manifest["commit"] == sha
        assert "output/pdf/fep_lean_combined.pdf" in manifest["files"]
        assert "output/pdf/_combined_manuscript.pdf" not in manifest["files"]
        for relative, digest in manifest["files"].items():
            assert (
                hashlib.sha256((staged / relative).read_bytes()).hexdigest() == digest
            )
        sources = json.loads((staged / "source-manifest.json").read_text())
        assert sources["commit"] == sha
        assert (
            sources["sources"]["manuscript/01_abstract.md"]
            == hashlib.sha256((manuscript / "01_abstract.md").read_bytes()).hexdigest()
        )
        from fep_lean.output.release_bundle._core import _capture_link_bytes

        provenance = json.loads((staged / "renderer-provenance.json").read_text())
        for role, selected in provenance["fonts"].items():
            retained_font = selected["artifact_path"]
            assert retained_font == f"fonts/{role}/{selected_font.name}"
            assert (staged / retained_font).read_bytes() == selected_font.read_bytes()
            assert manifest["files"][retained_font] == selected["sha256"]
        template_sources = provenance["template_sources"]
        object_format = subprocess.check_output(
            ["git", "rev-parse", "--show-object-format"], cwd=template, text=True
        ).strip()
        known_bytes = {
            **template_files,
            **{name: os.fsencode(target) for name, target in template_links.items()},
        }
        expected_sources = {
            name: {
                "mode": "120000"
                if name in template_links
                else "100755"
                if name == "tools/run.py"
                else "100644",
                "git_blob": hashlib.new(
                    object_format,
                    b"blob " + str(len(data)).encode("ascii") + b"\0" + data,
                ).hexdigest(),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
            for name, data in known_bytes.items()
        }
        assert template_sources["sources"] == expected_sources
        assert set(template_sources["uninitialized_gitlinks"]) == set(template_gitlinks)
        for name, commit in template_gitlinks.items():
            gitlink_stat = (template / name).lstat()
            assert template_sources["uninitialized_gitlinks"][name] == {
                "mode": "160000",
                "git_commit": commit,
                "empty": True,
                "identity": [
                    gitlink_stat.st_dev,
                    gitlink_stat.st_ino,
                    gitlink_stat.st_mode,
                    gitlink_stat.st_size,
                    gitlink_stat.st_mtime_ns,
                    gitlink_stat.st_ctime_ns,
                ],
            }
            assert not list((template / name).iterdir())
        assert set(template_sources["links"]) == {
            *template_links,
            "projects/active/fep_lean",
        }
        for name, target in {
            **template_links,
            "projects/active/fep_lean": str(tmp_path),
        }.items():
            link = template_sources["links"][name]
            path = template / name
            resolved = path.resolve(strict=True)
            assert link["target"] == target
            assert (
                link["custody_sha256"]
                == hashlib.sha256(
                    _capture_link_bytes(path, target, template)
                ).hexdigest()
            )
            if name == "projects/active/fep_lean":
                assert link["resolved_target"] == str(tmp_path)
                assert link["referents"] == {}
            else:
                relative = resolved.relative_to(template).as_posix()
                assert link["resolved_target"] == relative
                names = (
                    {
                        item
                        for item in expected_sources
                        if item.startswith(relative + "/")
                    }
                    if resolved.is_dir()
                    else {relative}
                )
                assert link["referents"] == {
                    item: expected_sources[item] for item in names
                }


def test_python_acceptance_upload_retains_sealed_package_metadata() -> None:
    workflow = yaml.safe_load((PROJECT_ROOT / ".github/workflows/ci.yml").read_text())
    upload = next(
        step
        for step in workflow["jobs"]["python"]["steps"]
        if step.get("name") == "Retain actual Python acceptance results and coverage"
    )
    paths = set(upload["with"]["path"].splitlines())
    required = {
        "src/fep_lean.egg-info/" + name
        for name in (
            "PKG-INFO",
            "SOURCES.txt",
            "dependency_links.txt",
            "entry_points.txt",
            "requires.txt",
            "top_level.txt",
        )
    }
    assert required <= paths
    assert upload["with"]["if-no-files-found"] == "error"


@pytest.mark.parametrize(
    "failure", [None, "unsealed", "unexpected", "missing", "changed", "symlink"]
)
def test_python_metadata_upload_refuses_unsealed_or_changed_bytes(
    tmp_path: Path, failure: str | None
) -> None:
    names = (
        "PKG-INFO",
        "SOURCES.txt",
        "dependency_links.txt",
        "entry_points.txt",
        "requires.txt",
        "top_level.txt",
    )
    owner = tmp_path / "src/fep_lean.egg-info"
    owner.mkdir(parents=True)
    sealed = {}
    for name in names:
        payload = (name + " fixture bytes\n").encode()
        (owner / name).write_bytes(payload)
        sealed["src/fep_lean.egg-info/" + name] = hashlib.sha256(payload).hexdigest()
    selected = owner / "PKG-INFO"
    if failure == "unsealed":
        del sealed["src/fep_lean.egg-info/PKG-INFO"]
    elif failure == "unexpected":
        sealed["src/fep_lean.egg-info/unexpected"] = "0" * 64
    elif failure == "missing":
        selected.unlink()
    elif failure == "changed":
        selected.write_bytes(b"changed package metadata")
    elif failure == "symlink":
        target = tmp_path / "outside-metadata"
        target.write_bytes(selected.read_bytes())
        selected.unlink()
        selected.symlink_to(target)
    output = tmp_path / "output"
    output.mkdir()
    (output / "python-acceptance-collection.json").write_text(
        json.dumps({"source_sha256": sealed})
    )
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            _workflow_python(
                "Verify sealed Python package metadata before upload", "python"
            ),
        ],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(PROJECT_ROOT / "src")},
        capture_output=True,
        text=True,
        check=False,
    )
    assert (result.returncode == 0) is (failure is None), result.stderr
