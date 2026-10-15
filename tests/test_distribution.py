"""Installed-distribution contracts for the public package boundary."""

from __future__ import annotations

import hashlib
import json
import os
import re
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


def _init_fixture_repository(root: Path) -> None:
    # A user's fsmonitor setting must not launch detached daemons for these
    # disposable repositories. Override only this fixture's local config.
    subprocess.run(
        ["git", "-c", "core.fsmonitor=false", "init", "-q", str(root)], check=True
    )
    subprocess.run(
        ["git", "-C", str(root), "config", "--local", "core.fsmonitor", "false"],
        check=True,
    )


def _package_namespace_digests(project_root: Path) -> dict[str, str]:
    root = project_root / "src" / "fep_lean"
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file()
        and (path.suffix in {".py", ".lean", ".yaml"} or path.name == "py.typed")
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
    # PEP 561: the typed-package marker ships (empty) in the built wheel.
    assert expected_resources["py.typed"] == hashlib.sha256(b"").hexdigest()
    assert "py.typed" in _wheel_namespace_digests(wheel)

    environment = tmp_path / "venv"
    target_python = os.environ.get("FEP_DISTRIBUTION_PYTHON", sys.executable)
    clean_env = {
        key: value
        for key, value in os.environ.items()
        if key not in {"PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV"}
        and not key.startswith(("FEP_LEAN_", "MYPY"))
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
                "for path in installed_root.rglob('*') if path.is_file() and (path.suffix in {'.py', '.lean', '.yaml'} or path.name == 'py.typed')}; "
                "assert installed == expected, 'installed namespace roster or bytes differ'; "
                "from fep_lean.verification.gnn_continuous_artifact_proof import ContinuousArtifactError, scaffold_digest, canonical_scaffold_bytes; "
                f"q7_source = pathlib.Path({str(PROJECT_ROOT / 'specs/gnn-bridge-q7-continuous-ou-proof/fixtures/continuous_ou_jax.py')!r}).read_text(encoding='utf-8'); "
                f"q7_expected = {json.loads((PROJECT_ROOT / 'specs/gnn-bridge-q7-continuous-ou-proof/expected.json').read_text(encoding='utf-8'))['runner_ast_sha256']!r}; "
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
                "print('distribution-python=' + '.'.join(map(str, sys.version_info[:2])))\n"
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

    # Run the locked validator's checker against the existing target environment.
    # The checker is a development tool, never a runtime dependency of the wheel.
    typing_config = tmp_path / "installed-typing.ini"
    typing_config.write_text("[mypy]\n", encoding="utf-8")
    valid_typing = tmp_path / "installed_typing_valid.py"
    consumer = (
        "from pathlib import Path\n"
        "from typing_extensions import assert_type\n"
        "from fep_lean import FEPPipeline, PipelineResult\n"
        "\n"
        "pipeline = FEPPipeline(Path('.'))\n"
        "assert_type(pipeline, FEPPipeline)\n"
        "result = pipeline.run(mode='catalogue')\n"
        "assert_type(result, PipelineResult)\n"
        "assert_type(result.catalogue_topics, int)\n"
    )
    valid_typing.write_text(consumer, encoding="utf-8")
    target_versions = [
        line.removeprefix("distribution-python=")
        for line in probe.stdout.splitlines()
        if line.startswith("distribution-python=")
    ]
    assert len(target_versions) == 1, probe.stdout
    checker = [
        sys.executable,
        "-I",
        "-m",
        "mypy",
        "--config-file",
        str(typing_config),
        "--python-executable",
        str(python),
        "--python-version",
        target_versions[0],
        "--strict",
        "--disallow-any-expr",
        "--disallow-any-unimported",
        "--no-incremental",
        "--cache-dir",
        os.devnull,
        "--no-pretty",
        "--show-error-codes",
        "--no-error-summary",
        "--verbose",
    ]
    typed = subprocess.run(
        [*checker, str(valid_typing)],
        cwd=tmp_path,
        env=clean_env,
        timeout=120,
        check=False,
        capture_output=True,
        text=True,
    )
    assert typed.returncode == 0, typed.stdout + typed.stderr
    resolved_modules = [
        (module, Path(path).resolve())
        for path, module in re.findall(
            r"^LOG:\s+Parsing (.+) \((fep_lean(?:\.[A-Za-z_][A-Za-z_0-9]*)*)\)$",
            typed.stderr,
            re.MULTILINE,
        )
    ]
    assert "fep_lean" in {module for module, _ in resolved_modules}, typed.stderr
    assert "fep_lean.pipeline.core" in {module for module, _ in resolved_modules}, (
        typed.stderr
    )
    assert all(
        path.is_relative_to(environment.resolve()) for _, path in resolved_modules
    ), resolved_modules

    invalid_typing = tmp_path / "installed_typing_invalid.py"
    invalid_typing.write_text(
        consumer + "pipeline.run(mode='invalid-mode')\n", encoding="utf-8"
    )
    rejected = subprocess.run(
        [*checker, str(invalid_typing)],
        cwd=tmp_path,
        env=clean_env,
        timeout=120,
        check=False,
        capture_output=True,
        text=True,
    )
    assert rejected.returncode == 1, rejected.stdout + rejected.stderr
    errors = [line for line in rejected.stdout.splitlines() if ": error:" in line]
    assert len(errors) == 1, rejected.stdout + rejected.stderr
    assert all(
        expected in errors[0]
        for expected in (
            invalid_typing.name,
            'Argument "mode"',
            '"FEPPipeline"',
            "incompatible type",
            "invalid-mode",
            "[arg-type]",
        )
    ), errors[0]
    print("installed wheel typing: valid API accepted; invalid mode rejected")

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
    _init_fixture_repository(tmp_path)
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
    _init_fixture_repository(tmp_path)
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
        "during_template_mode_drift",
        "during_font_drift",
        "while_staging_source_drift",
        "while_staging_pdf_drift",
        "retained_pdf_drift",
        "retained_read_source_drift",
        "retained_read_pdf_drift",
    ],
)
def test_render_artifact_staging_refuses_unaccepted_or_unbound_inputs(
    tmp_path: Path, failure: str | None
) -> None:
    """Execute CI staging; valid output hashes bind, plausible failures refuse."""
    _exercise_render_artifact_staging(tmp_path, failure=failure)


_TEMPLATE_SUCCESS_CASES = frozenset(
    {
        "relative_file",
        "relative_directory",
        "relative_file_and_directory",
        "absolute_internal_file",
        "directory_excluded_cache",
        "executable_owner",
    }
)
_TEMPLATE_GITLINK = (
    "infrastructure/steganography/kmyth",
    "cb23c6d94423cbe4f5ef0caf23594d1095ddde79",
)

_TEMPLATE_LINK_CASES = (
    "relative_file",
    "relative_directory",
    "relative_file_and_directory",
    "absolute_internal_file",
    "directory_excluded_cache",
    "executable_owner",
    "during_link_read",
    "absolute_escape",
    "missing_target",
    "cyclic_target",
    "noncanonical_target",
    "excluded_target",
    "link_mode_as_regular",
    "regular_mode_as_link",
    "untracked_file_referent",
    "untracked_directory_referent",
    "empty_directory_referent",
    "modified_referent",
    "modified_referent_hidden_from_git_diff",
    "unsupported_git_mode",
    "ignored_untracked_link",
    "wrong_internal_registration",
    "tracked_registration",
    "missing_registration",
    "discovery_template_source",
    "discovery_template_link",
    "discovery_template_referent",
    "discovery_registration",
    "retention_template_source",
    "retention_template_link",
    "retention_template_referent",
    "retention_registration",
)


@pytest.mark.parametrize("template_case", _TEMPLATE_LINK_CASES)
def test_render_artifact_staging_binds_template_links(
    tmp_path: Path, template_case: str
) -> None:
    """Run the actual workflow against committed link and referent controls."""
    if template_case == "unsupported_git_mode":
        # Exercise each real gitlink rejection in its own independent
        # repository and staging path.
        for variant in (
            "unknown_path",
            "changed_commit",
            "changed_mode_regular",
            "changed_mode_symlink",
            "wrong_template_sha",
            "nonempty",
            "initialized_gitfile",
            "initialized_gitdirectory",
            "symlink",
            "regular_file",
            "missing",
            "parent_symlink",
            "inventory_nonempty",
            "inventory_empty_metadata",
            "discovery_nonempty",
            "discovery_empty_metadata",
            "retention_nonempty",
            "retention_empty_metadata",
        ):
            child = tmp_path / variant
            child.mkdir()
            _exercise_render_artifact_staging(
                child, template_case=template_case, gitlink_case=variant
            )
        return
    _exercise_render_artifact_staging(tmp_path, template_case=template_case)


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
