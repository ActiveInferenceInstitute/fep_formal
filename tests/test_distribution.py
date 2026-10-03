"""Installed-distribution contracts for the public package boundary."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile
from email import policy
from email.parser import Parser
from importlib.metadata import distribution
from pathlib import Path

import pytest
import yaml

from fep_lean.output.render_log import build_acceptance_receipt
from fep_lean.output.rendering import MANUSCRIPT_ASSETS

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _assert_wheel_metadata_headers(metadata_text: str) -> None:
    metadata = Parser(policy=policy.strict).parsestr(metadata_text, headersonly=True)
    assert not metadata.defects
    expected = {
        "License-Expression": ["CC-BY-4.0"],
        "License-File": ["LICENSE"],
        "Author-email": ["Daniel Ari Friedman <daniel@activeinference.institute>"],
        "Description-Content-Type": ["text/markdown"],
        "Project-URL": [
            "Repository, https://github.com/ActiveInferenceInstitute/fep_formal",
            "Changelog, https://github.com/ActiveInferenceInstitute/fep_formal/blob/main/CHANGELOG.md",
            "Concept DOI, https://doi.org/10.5281/zenodo.19699233",
        ],
    }
    for header, values in expected.items():
        # Header order is irrelevant; complete values and multiplicity are exact.
        assert sorted(metadata.get_all(header, [])) == sorted(values), header


def _wheel_metadata_fixture() -> str:
    return (
        "Metadata-Version: 2.4\n"
        "Name: fep_lean\n"
        "License-Expression: CC-BY-4.0\n"
        "License-File: LICENSE\n"
        "Author-email: Daniel Ari Friedman <daniel@activeinference.institute>\n"
        "Description-Content-Type: text/markdown\n"
        "Project-URL: Repository, https://github.com/ActiveInferenceInstitute/fep_formal\n"
        "Project-URL: Changelog, https://github.com/ActiveInferenceInstitute/fep_formal/blob/main/CHANGELOG.md\n"
        "Project-URL: Concept DOI, https://doi.org/10.5281/zenodo.19699233\n"
        "\nA package description.\n"
    )


@pytest.mark.parametrize("line_ending", ["\n", "\r\n"], ids=["LF", "CRLF"])
def test_wheel_metadata_headers_accept_standard_line_endings(line_ending: str) -> None:
    _assert_wheel_metadata_headers(_wheel_metadata_fixture().replace("\n", line_ending))


@pytest.mark.parametrize("line_ending", ["\n", "\r\n"], ids=["LF", "CRLF"])
@pytest.mark.parametrize(
    "duplicate",
    [
        "License-Expression: CC-BY-4.0",
        "License-File: LICENSE",
        "Author-email: Daniel Ari Friedman <daniel@activeinference.institute>",
        "Description-Content-Type: text/markdown",
        "Project-URL: Concept DOI, https://doi.org/10.5281/zenodo.19699233",
    ],
)
def test_wheel_metadata_headers_refuse_duplicate_values(
    line_ending: str, duplicate: str
) -> None:
    metadata = _wheel_metadata_fixture().replace("\n\n", f"\n{duplicate}\n\n", 1)
    with pytest.raises(AssertionError, match=duplicate.split(":", 1)[0]):
        _assert_wheel_metadata_headers(metadata.replace("\n", line_ending))


@pytest.mark.parametrize("line_ending", ["\n", "\r\n"], ids=["LF", "CRLF"])
@pytest.mark.parametrize("failure", ["body_only_license", "wrong_project_url"])
def test_wheel_metadata_headers_refuse_body_spoof_and_wrong_url(
    line_ending: str, failure: str
) -> None:
    metadata = _wheel_metadata_fixture()
    if failure == "body_only_license":
        metadata = metadata.replace("License-Expression: CC-BY-4.0\n", "", 1)
        metadata += "License-Expression: CC-BY-4.0\n"
        header = "License-Expression"
    else:
        metadata = metadata.replace(
            "Project-URL: Concept DOI, https://doi.org/10.5281/zenodo.19699233",
            "Project-URL: Concept DOI, https://doi.org/10.5281/zenodo.1",
        )
        header = "Project-URL"
    with pytest.raises(AssertionError, match=header):
        _assert_wheel_metadata_headers(metadata.replace("\n", line_ending))


def _package_namespace_digests(project_root: Path) -> dict[str, str]:
    root = project_root / "src" / "fep_lean"
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file() and path.suffix in {".py", ".lean", ".yaml"}
    }


def _wheel_namespace_digests(wheel: Path) -> dict[str, str]:
    with zipfile.ZipFile(wheel) as archive:
        members = [
            entry.filename
            for entry in archive.infolist()
            if entry.filename.startswith("fep_lean/") and not entry.is_dir()
        ]
        assert len(members) == len(set(members)), "duplicate wheel namespace member"
        return {
            name.removeprefix("fep_lean/"): hashlib.sha256(
                archive.read(name)
            ).hexdigest()
            for name in members
        }


def test_distribution_exports_one_root_package_and_console_script() -> None:
    """Wheel metadata must match the documented import and CLI surfaces."""
    dist = distribution("fep_lean")

    top_level = (dist.read_text("top_level.txt") or "").split()
    assert top_level == ["fep_lean"]

    scripts = {
        entry.name: entry.value
        for entry in dist.entry_points
        if entry.group == "console_scripts"
    }
    assert scripts == {"fep-lean": "fep_lean.cli:main"}


def test_q7_scaffold_bytes_refuse_legacy_codepage_substitution() -> None:
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
    legacy = source.read_text(encoding="cp1252")
    assert utf8 != legacy, "control requires the actual UTF-8 scaffold text"
    assert hashlib.sha256(canonical_scaffold_bytes(utf8)).hexdigest() == expected
    assert hashlib.sha256(canonical_scaffold_bytes(legacy)).hexdigest() != expected


def test_built_wheel_imports_in_isolated_namespace(tmp_path: Path) -> None:
    """Exercise the built bytes outside the checkout's import path."""
    uv = shutil.which("uv")
    assert uv is not None, "the project test contract requires uv"
    dist_dir = tmp_path / "dist"
    # uv's default builds an sdist and then its wheel in a fresh extracted tree.
    # --wheel builds directly from source and can retain stale build/lib owners.
    subprocess.run(
        [uv, "build", "--out-dir", str(dist_dir)],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    wheel = next(dist_dir.glob("fep_lean-*.whl"))
    expected_resources = _package_namespace_digests(PROJECT_ROOT)
    assert _wheel_namespace_digests(wheel) == expected_resources
    with zipfile.ZipFile(wheel) as archive:
        metadata_name = next(
            name for name in archive.namelist() if name.endswith(".dist-info/METADATA")
        )
        wheel_metadata = archive.read(metadata_name).decode("utf-8")
    _assert_wheel_metadata_headers(wheel_metadata)

    environment = tmp_path / "venv"
    target_python = os.environ.get("FEP_DISTRIBUTION_PYTHON", sys.executable)
    clean_env = {
        key: value
        for key, value in os.environ.items()
        if key not in {"PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV"}
        and not key.startswith("FEP_LEAN_")
    }
    subprocess.run(
        [uv, "venv", "--python", target_python, str(environment)],
        cwd=tmp_path,
        env=clean_env,
        check=True,
        capture_output=True,
        text=True,
    )
    scripts = environment / ("Scripts" if os.name == "nt" else "bin")
    python = scripts / ("python.exe" if os.name == "nt" else "python")
    subprocess.run(
        [
            uv,
            "pip",
            "install",
            "--python",
            str(python),
            str(wheel),
        ],
        cwd=tmp_path,
        env=clean_env,
        check=True,
        capture_output=True,
        text=True,
    )
    # Resolve the declared runtime dependencies for the target interpreter in
    # its own environment. Neither editable-install .pth files nor the parent
    # validator's site-packages are a compatibility substitute.
    probe = subprocess.run(
        [
            str(python),
            "-I",
            "-c",
            (
                "import hashlib, importlib.resources, importlib.util, pathlib, sys, fep_lean; "
                "from fep_lean.bridge.custody import classify_document; "
                "from fep_lean.bridge.certificates import compare; "
                "assert callable(classify_document) and callable(compare); "
                "from fep_lean.catalogue import BODIES, FEPTopicCatalogue; "
                f"assert pathlib.Path(fep_lean.__file__).is_relative_to(pathlib.Path({str(environment)!r})); "
                f"assert not any(path and pathlib.Path(path).is_relative_to(pathlib.Path({str(PROJECT_ROOT)!r})) for path in sys.path); "
                "assert len(FEPTopicCatalogue.default().topics) == len(BODIES); "
                "assert callable(fep_lean.build_formal_kernel_dashboard); "
                "formal = importlib.resources.files('fep_lean.formal').joinpath('composed.lean'); "
                "core = importlib.resources.files('fep_lean.formal').joinpath('compositions/core.lean'); "
                "assert 'import FepSketches.compositions.core' in formal.read_text(encoding='utf-8'); "
                "assert 'fep002_vfe_compProd_chain_rule' in core.read_text(encoding='utf-8'); "
                f"expected = {expected_resources!r}; "
                "root = importlib.resources.files('fep_lean'); "
                "assert all(hashlib.sha256(root.joinpath(name).read_bytes()).hexdigest() == value for name, value in expected.items()); "
                "installed_root = pathlib.Path(fep_lean.__file__).parent; "
                "installed = {path.relative_to(installed_root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() "
                "for path in installed_root.rglob('*') if path.is_file() and path.suffix in {'.py', '.lean', '.yaml'}}; "
                "assert installed == expected, 'installed namespace roster or bytes differ'; "
                "from fep_lean.verification.gnn_continuous_artifact_proof import ContinuousArtifactError, scaffold_digest, canonical_scaffold_bytes; "
                f"q7_source = pathlib.Path({str(PROJECT_ROOT / 'specs/gnn-bridge-q7-continuous-ou-proof/fixtures/continuous_ou_jax.py')!r}).read_text(encoding='utf-8'); "
                f"q7_expected = {json.loads((PROJECT_ROOT / 'specs/gnn-bridge-q7-continuous-ou-proof/expected.json').read_text())['runner_ast_sha256']!r}; "
                "assert hashlib.sha256(canonical_scaffold_bytes(q7_source)).hexdigest() == q7_expected; "
                "accepted = sys.implementation.name == 'cpython' and sys.version_info[:2] == (3, 14); "
                "\nif not accepted:\n"
                "    try:\n"
                "        scaffold_digest('invalid syntax !!!')\n"
                "    except ContinuousArtifactError as exc:\n"
                "        assert exc.reason == 'interpreter', str(exc)\n"
                "    else:\n"
                "        raise AssertionError('unsupported Q7 interpreter accepted')\n"
                "assert importlib.util.find_spec('catalogue') is None\n"
                "print(sys.version, sys.platform)\n"
            ),
        ],
        cwd=tmp_path,
        env=clean_env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert probe.returncode == 0, probe.stderr or probe.stdout
    print("installed wheel runtime:", probe.stdout.strip())
    capture_probe = subprocess.run(
        [
            str(python),
            "-I",
            "-c",
            """
from pathlib import Path
import os, sys
from fep_lean.output.release_bundle import (
    PublicationCapturePlan, PublicationCaptureStage, ReleaseBundleError, run_publication_capture,
)
root = Path.cwd() / 'capture-project'
root.mkdir()
source, output = root / 'source.txt', root / 'artifact.txt'
source.write_text('first')
producer = (
    'from pathlib import Path;import sys;'
    'Path(sys.argv[2]).write_bytes(Path(sys.argv[1]).read_bytes());'
    "print('installed nested producer')"
)
nested = (
    'import sys;print("installed nested worker started",flush=True);'
    'from fep_lean.verification._subprocess import run_process_group;'
    'r=run_process_group([sys.executable,"-S","-c",sys.argv[1],sys.argv[2],sys.argv[3]],'
    'cwd=sys.argv[4],timeout=10,check=True);print(r.stdout,end="")'
)
validator = (
    'from pathlib import Path;import sys;'
    'assert Path(sys.argv[1]).read_bytes()==Path(sys.argv[2]).read_bytes()'
)
stage = PublicationCaptureStage(
    'installed', (), (str(source),), (str(output),),
    (sys.executable, '-c', nested, producer, str(source), str(output), str(root)),
    (sys.executable, '-S', '-c', validator, str(source), str(output)), 60,
)
plan = PublicationCapturePlan(str(root), (stage,), 180)
journal = Path.cwd() / 'capture-journal'
if os.name != 'posix':
    try:
        run_publication_capture(plan, journal)
    except ReleaseBundleError as error:
        assert 'requires POSIX' in str(error)
    else:
        raise AssertionError('unsupported custody platform executed capture')
    assert not journal.exists()
    print(sys.version, sys.platform, 'unsupported capture custody refused before journal')
    raise SystemExit(0)
captured = run_publication_capture(plan, journal)
assert captured.complete, captured
reused = run_publication_capture(plan, journal, resume=True)
assert reused.reused_stages == ('installed',), reused
source.write_text('changed')
changed = run_publication_capture(plan, journal, resume=True)
assert changed.complete and not changed.reused_stages, changed
assert output.read_text() == 'changed'
print(sys.version, sys.platform, 'installed capture and nested helper accepted')
""",
        ],
        cwd=tmp_path,
        env=clean_env,
        timeout=240,
        check=False,
        capture_output=True,
        text=True,
    )
    assert capture_probe.returncode == 0, capture_probe.stderr or capture_probe.stdout
    print("installed capture runtime:", capture_probe.stdout.strip())
    cli = subprocess.run(
        [str(scripts / ("fep-lean.exe" if os.name == "nt" else "fep-lean")), "--help"],
        cwd=tmp_path,
        env=clean_env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert cli.returncode == 0, cli.stderr or cli.stdout
    assert "Strict FEP Lean catalogue" in cli.stdout
    outside_checkout = subprocess.run(
        [
            str(scripts / ("fep-lean.exe" if os.name == "nt" else "fep-lean")),
            "catalogue",
        ],
        cwd=tmp_path,
        env=clean_env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert outside_checkout.returncode == 1
    assert "--project-root" in outside_checkout.stdout
    # Explicit-root CLI behavior belongs to wheel acceptance; freshness of
    # repository projections has its own gate. Generate and check a disposable
    # checkout so concurrent projection updates cannot contaminate this probe.
    checkout = tmp_path / "checkout"
    shutil.copytree(PROJECT_ROOT / "config", checkout / "config")
    shutil.copytree(
        PROJECT_ROOT / "src/fep_lean/formal", checkout / "src/fep_lean/formal"
    )
    for relative in (
        "src/fep_lean/__init__.py",
        "lean/lean-toolchain",
        "lean/lakefile.lean",
        "manuscript/config.yaml",
    ):
        target = checkout / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(PROJECT_ROOT / relative, target)
    for command in ("atlas", "dashboard"):
        built = subprocess.run(
            [
                str(scripts / ("fep-lean.exe" if os.name == "nt" else "fep-lean")),
                "--project-root",
                str(checkout),
                command,
            ],
            cwd=tmp_path,
            env=clean_env,
            check=False,
            capture_output=True,
            text=True,
        )
        assert built.returncode == 0, built.stderr or built.stdout
    live_check = subprocess.run(
        [
            str(scripts / ("fep-lean.exe" if os.name == "nt" else "fep-lean")),
            "--project-root",
            str(checkout),
            "atlas",
            "--check",
        ],
        cwd=tmp_path,
        env=clean_env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert live_check.returncode == 0, live_check.stderr or live_check.stdout
    assert "projections are current" in live_check.stdout
    dashboard_check = subprocess.run(
        [
            str(scripts / ("fep-lean.exe" if os.name == "nt" else "fep-lean")),
            "--project-root",
            str(checkout),
            "dashboard",
            "--check",
        ],
        cwd=tmp_path,
        env=clean_env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert dashboard_check.returncode == 0, (
        dashboard_check.stderr or dashboard_check.stdout
    )
    assert "dashboard projections are current" in dashboard_check.stdout


def test_default_build_excludes_stale_cache_without_deleting_it(tmp_path: Path) -> None:
    """Reproduce dirty direct builds and require exact fresh-sdist wheel bytes."""
    uv = shutil.which("uv")
    assert uv is not None, "the project test contract requires uv"
    project = tmp_path / "project"
    project.mkdir()
    for name in ("pyproject.toml", "README.md", "LICENSE", ".python-version"):
        shutil.copyfile(PROJECT_ROOT / name, project / name)
    shutil.copytree(
        PROJECT_ROOT / "src/fep_lean",
        project / "src/fep_lean",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    expected = _package_namespace_digests(project)
    # These are the actual five orphan names found in the retained failing
    # wheels. Controlled marker bytes seed only this private project's cache;
    # no repository source or existing build/lib file is changed or removed.
    orphans = {
        "output/release_bundle.py": b"LEGACY_CACHE_ONLY = True\n",
        **{
            f"formal/compositions/{name}.lean": b"-- controlled orphaned build resource\n"
            for name in (
                "concentration_bridges",
                "decision_bridges",
                "fluctuation_bridges",
                "graph_consensus",
            )
        },
    }
    cache = project / "build/lib/fep_lean"
    for relative, contents in orphans.items():
        assert relative not in expected
        path = cache / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(contents)
    direct_dist, fresh_dist = tmp_path / "direct-dist", tmp_path / "fresh-dist"
    subprocess.run(
        [uv, "build", "--wheel", "--out-dir", str(direct_dist)],
        cwd=project,
        check=True,
        capture_output=True,
        text=True,
    )
    direct = _wheel_namespace_digests(next(direct_dist.glob("fep_lean-*.whl")))
    orphan_digests = {
        relative: hashlib.sha256(contents).hexdigest()
        for relative, contents in orphans.items()
    }
    assert direct == {**expected, **orphan_digests}
    subprocess.run(
        [uv, "build", "--out-dir", str(fresh_dist)],
        cwd=project,
        check=True,
        capture_output=True,
        text=True,
    )
    assert len(tuple(fresh_dist.glob("fep_lean-*.tar.gz"))) == 1
    assert _wheel_namespace_digests(next(fresh_dist.glob("fep_lean-*.whl"))) == expected
    assert {name: (cache / name).read_bytes() for name in orphans} == orphans
    assert _package_namespace_digests(project) == expected
    print("controlled stale-cache carryover reproduced; fresh-sdist namespace exact")


def _workflow_python(step_name: str, job: str) -> str:
    workflow = yaml.safe_load(
        (PROJECT_ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    )
    step = next(
        step for step in workflow["jobs"][job]["steps"] if step.get("name") == step_name
    )
    return step["run"].split("<<'PY'\n", 1)[1].rsplit("\nPY", 1)[0]


@pytest.mark.parametrize(
    ("changed_path", "docs_only"),
    [
        ("README.md", True),
        ("docs/development.md", True),
        ("docs/formalism-coverage.md", False),
        ("docs/theorem-maturity-audit.md", False),
        ("docs/lean-landscape.md", False),
        ("docs/render-acceptance.json", False),
        ("docs/render-fonts.json", False),
        ("docs/formalism-atlas.svg", False),
        ("manuscript/01_abstract.md", False),
        ("src/fep_lean/catalogue/bodies/free_energy.py", False),
        (".github/workflows/ci.yml", False),
    ],
)
def test_documentation_classifier_keeps_publication_inputs_on_full_gates(
    tmp_path: Path, changed_path: str, docs_only: bool
) -> None:
    """Exercise the actual CI classifier against a real git difference."""
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    git_env = dict(os.environ)
    git_env.update(
        GIT_AUTHOR_NAME="Test",
        GIT_AUTHOR_EMAIL="test@example.invalid",
        GIT_COMMITTER_NAME="Test",
        GIT_COMMITTER_EMAIL="test@example.invalid",
    )
    subprocess.run(
        ["git", "commit", "--allow-empty", "-qm", "baseline"],
        cwd=tmp_path,
        env=git_env,
        check=True,
    )
    base = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True
    ).strip()
    path = tmp_path / changed_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("change\n", encoding="utf-8")
    subprocess.run(["git", "add", "--", changed_path], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "commit", "-qm", "change"],
        cwd=tmp_path,
        env=git_env,
        check=True,
    )
    output = tmp_path / "job-output"
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            _workflow_python("Classify documentation-only pull requests", "changes"),
        ],
        cwd=tmp_path,
        env={
            **os.environ,
            "EVENT_NAME": "pull_request",
            "BASE_SHA": base,
            "GITHUB_OUTPUT": str(output),
        },
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert output.read_text().strip() == f"docs_only={str(docs_only).lower()}"


def test_documentation_classifier_rejects_source_rename_into_prose(
    tmp_path: Path,
) -> None:
    """A 100-percent rename must preserve the removed owner's full gates."""
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    source = tmp_path / "src/owner.py"
    source.parent.mkdir()
    source.write_text("A file renamed without any content change.\n")
    git_env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "Test",
        "GIT_AUTHOR_EMAIL": "test@example.invalid",
        "GIT_COMMITTER_NAME": "Test",
        "GIT_COMMITTER_EMAIL": "test@example.invalid",
    }
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "-c", "commit.gpgsign=false", "commit", "-qm", "source"],
        cwd=tmp_path,
        env=git_env,
        check=True,
    )
    base = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True
    ).strip()
    docs = tmp_path / "docs"
    docs.mkdir()
    source.rename(docs / "renamed.md")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "-c", "commit.gpgsign=false", "commit", "-qm", "rename"],
        cwd=tmp_path,
        env=git_env,
        check=True,
    )
    output = tmp_path / "job-output"
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            _workflow_python("Classify documentation-only pull requests", "changes"),
        ],
        cwd=tmp_path,
        env={
            **os.environ,
            "EVENT_NAME": "pull_request",
            "BASE_SHA": base,
            "GITHUB_OUTPUT": str(output),
        },
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert output.read_text().strip() == "docs_only=false"


@pytest.mark.parametrize(
    "failure",
    [
        None,
        "wrong_sha",
        "stale_receipt",
        "missing_pdf",
        "legacy_pdf_only",
        "source_drift",
        "native_stale",
        "audit_stale",
        "untracked_chapter",
        "during_source_drift",
        "during_chapter_addition",
        "during_pdf_drift",
        "during_template_drift",
        "during_font_drift",
        "while_staging_source_drift",
        "while_staging_pdf_drift",
        "retained_pdf_drift",
        "retained_read_source_drift",
        "retained_read_pdf_drift",
        "template_symlink_replaced",
        "template_symlink_retargeted",
        "template_gitlink_populated",
        "template_gitlink_replaced",
        "during_template_symlink_drift",
        "while_staging_template_symlink_drift",
        "while_staging_template_gitlink_drift",
        "template_gitlink_missing",
        "template_gitlink_retargeted",
        "during_template_link_read",
        "during_template_mode_drift",
    ],
)
def test_render_artifact_staging_refuses_unaccepted_or_unbound_inputs(
    tmp_path: Path, failure: str | None
) -> None:
    """Execute CI staging; valid output hashes bind, plausible failures refuse."""
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "01_abstract.md").write_text("A rendered statement.\n")
    (manuscript / "preamble.md").write_text("\\setmainfont{TestFont}\n")
    (manuscript / "09z_unified_formalism_catalogue.md").write_text("Appendix.\n")
    (manuscript / "manuscript_vars.yaml").write_text("{}\n")
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
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
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
    template = tmp_path / "render-template"
    template.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=template, check=True)
    (template / "README.md").write_text("Pinned template source.\n")
    template_link = template / "pointer.py"
    external_target = tmp_path.parent / f"{tmp_path.name}-private-target.py"
    external_target.write_bytes(b"private target bytes are not renderer inputs\n")
    link_target = os.path.relpath(external_target, template)
    if os.name == "posix":
        template_link.symlink_to(link_target)
    gitlink = template / "unused-submodule"
    gitlink.mkdir()
    subprocess.run(["git", "add", "."], cwd=template, check=True)
    subprocess.run(
        [
            "git",
            "update-index",
            "--add",
            "--cacheinfo",
            f"160000,{sha},unused-submodule",
        ],
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
    if failure == "template_gitlink_missing":
        gitlink.rmdir()
    elif failure == "template_gitlink_retargeted":
        subprocess.run(
            [
                "git",
                "update-index",
                "--cacheinfo",
                f"160000,{'1' * 40},unused-submodule",
            ],
            cwd=template,
            check=True,
        )
    elif failure == "during_template_mode_drift":
        subprocess.run(
            ["git", "config", "core.filemode", "false"], cwd=template, check=True
        )
    elif failure == "stale_receipt":
        (manuscript / "01_abstract.md").write_text("Unaccepted change.\n")
    elif failure == "missing_pdf":
        (pdf / "fep_lean_combined.pdf").unlink()
    elif failure == "legacy_pdf_only":
        (pdf / "fep_lean_combined.pdf").rename(pdf / "_combined_manuscript.pdf")
    elif failure == "source_drift":
        font.write_bytes(b"changed tracked input")
    elif failure == "template_symlink_replaced" and os.name == "posix":
        template_link.unlink()
        template_link.write_text(link_target)
    elif failure == "template_symlink_retargeted" and os.name == "posix":
        template_link.unlink()
        template_link.symlink_to("unaccepted-target")
    elif failure == "template_gitlink_populated":
        (gitlink / "unbound-owner.py").write_text("unbound source\n")
    elif failure == "template_gitlink_replaced":
        gitlink.rmdir()
        gitlink.write_text("unbound replacement\n")
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
        "during_template_drift": "Path('render-template/README.md').write_text('Uncommitted template mutation.\\n')",
        "during_template_symlink_drift": "Path('render-template/pointer.py').unlink(); Path('render-template/pointer.py').symlink_to('unaccepted-target')",
        "during_template_mode_drift": "Path('render-template/README.md').chmod(0o755)",
    }.get(failure, "pass")
    staged_mutation = {
        "while_staging_source_drift": "Path('manuscript/01_abstract.md').write_text('Changed while retaining evidence.\\n')",
        "while_staging_pdf_drift": "_real_write_bytes(Path('output/pdf/fep_lean_combined.pdf'), b'%PDF-changed while retaining evidence')",
        "retained_pdf_drift": "_real_write_bytes(path, b'%PDF-corrupted retained artifact')",
        "while_staging_template_symlink_drift": "Path('render-template/pointer.py').unlink(); Path('render-template/pointer.py').symlink_to('unaccepted-target')",
        "while_staging_template_gitlink_drift": "Path('render-template/unused-submodule/unbound-owner.py').write_text('unbound source\\n')",
    }.get(failure, "pass")
    retained_read_mutation = {
        "retained_read_source_drift": "Path('manuscript/01_abstract.md').write_text('Changed while verifying retained bytes.\\n')",
        "retained_read_pdf_drift": "_real_write_bytes(Path('output/pdf/fep_lean_combined.pdf'), b'%PDF-changed during retained read')",
    }.get(failure, "pass")
    script = (
        "import os\n"
        "import subprocess\n"
        "from pathlib import Path\n"
        "_real_readlink = os.readlink\n"
        "def _pointer_read(path, **kwargs):\n"
        "    data = _real_readlink(path, **kwargs)\n"
        f"    if {failure == 'during_template_link_read'!r} and path == b'pointer.py':\n"
        "        Path('render-template/pointer.py').unlink()\n"
        "        Path('render-template/pointer.py').symlink_to('unaccepted-target')\n"
        "    return data\n"
        "os.readlink = _pointer_read\n"
        "import fep_lean.output.evidence as _native\n"
        "import fep_lean.verification.formalism_audit as _audit\n"
        f"_native.validate_native_lean_receipt = lambda *args, **kwargs: {{'native_claim_ready': {failure != 'native_stale'!r}}}\n"
        f"_audit.validate_formalism_audit_receipt = lambda *args, **kwargs: {('fixture audit is stale',) if failure == 'audit_stale' else ()!r}\n"
        "_real_check_output = subprocess.check_output\n"
        "def _version_probe(argv, **kwargs):\n"
        "    if argv[0] == 'fc-match':\n"
        f"        return {str(selected_font)!r} + '\\n'\n"
        "    if argv[0] in {'xelatex', 'pandoc', 'rsvg-convert', 'mmdc'}:\n"
        "        if argv[0] == 'xelatex':\n"
        f"            {version_mutation}\n"
        "        return 'fixture version 1\\n'\n"
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
        "def _retained_read(path):\n"
        f"    if path == Path({str(external_target)!r}):\n"
        "        raise AssertionError('template symlink target must never be read')\n"
        "    data = _real_regular_read(path)\n"
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
            "WORKFLOW_RUN_ID": "fixture",
            "WORKFLOW_RUN_ATTEMPT": "1",
        },
        capture_output=True,
        text=True,
        check=False,
    )
    staged = tmp_path / "output/render-evidence"
    if os.name != "posix" and (
        "capture custody requires POSIX descriptor-relative reads" in result.stderr
    ):
        # Publication capture runs on Linux. This platform certifies the
        # explicit custody refusal before the later POSIX mutation controls.
        assert result.returncode != 0
        assert not staged.exists()
        return
    if failure:
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
            "during_font_drift": "changed during evidence staging",
            "while_staging_source_drift": "changed during evidence staging",
            "while_staging_pdf_drift": "changed during evidence staging",
            "retained_pdf_drift": "changed during evidence staging",
            "retained_read_source_drift": "changed during evidence staging",
            "retained_read_pdf_drift": "changed during evidence staging",
            "template_symlink_replaced": "template authored inputs differ",
            "template_symlink_retargeted": "template authored inputs differ",
            "template_gitlink_populated": "gitlink has unbound checkout content",
            "template_gitlink_replaced": "template authored inputs differ",
            "during_template_symlink_drift": "changed during evidence staging",
            "while_staging_template_symlink_drift": "changed during evidence staging",
            "while_staging_template_gitlink_drift": "changed during evidence staging",
            "template_gitlink_retargeted": "template authored inputs differ",
            "template_gitlink_missing": "template authored inputs differ",
            "during_template_link_read": "symlink changed while reading",
            "during_template_mode_drift": "changed during evidence staging",
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
        provenance = json.loads((staged / "renderer-provenance.json").read_text())
        template_tree = provenance["template_tree"]
        assert template_tree["README.md"]["mode"] == "100644"
        assert template_tree["README.md"]["type"] == "blob"
        assert template_tree["unused-submodule"] == {
            "mode": "160000",
            "type": "commit",
            "git_oid": sha,
            "checkout_state": "uninitialized-empty",
        }
        if os.name == "posix":
            pointer = template_tree["pointer.py"]
            assert pointer["mode"] == "120000"
            assert pointer["type"] == "blob"
            assert bytes.fromhex(pointer["target_hex"]) == os.fsencode(link_target)
            assert (
                pointer["git_oid"]
                == subprocess.check_output(
                    ["git", "hash-object", "--stdin"],
                    cwd=template,
                    input=os.fsencode(link_target),
                )
                .decode()
                .strip()
            )
            assert "pointer.py" not in provenance["template_sources"]
        assert (
            external_target.read_bytes()
            == b"private target bytes are not renderer inputs\n"
        )
        assert (
            b"private target bytes are not renderer inputs"
            not in (staged / "renderer-provenance.json").read_bytes()
        )
        assert (
            sources["sources"]["manuscript/01_abstract.md"]
            == hashlib.sha256((manuscript / "01_abstract.md").read_bytes()).hexdigest()
        )
