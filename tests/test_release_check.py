"""Release gate: version/date agreement, changelog section and hosted CI."""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from pathlib import Path
from types import ModuleType

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SOURCES = (
    "pyproject.toml",
    "src/fep_lean/__init__.py",
    "src/fep_lean/output/release_bundle/_constants.py",
    "CITATION.cff",
    "manuscript/config.yaml",
    "config/settings.yaml",
    ".aii/config.yaml",
    "uv.lock",
    "CHANGELOG.md",
)


def _module() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "release_check", PROJECT_ROOT / "docs" / "release_check.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _copy_sources(root: Path) -> Path:
    for relative in _SOURCES:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(PROJECT_ROOT / relative, target)
    return root


def test_repository_metadata_agrees_on_one_release() -> None:
    check = _module()
    release = check.read_release(PROJECT_ROOT)
    assert check.metadata_errors(PROJECT_ROOT) == ()
    assert release.version == check.read_versions(PROJECT_ROOT)["pyproject.toml"]
    assert release.date == check.read_dates(PROJECT_ROOT)["CITATION.cff"]


@pytest.mark.parametrize(
    ("relative", "old", "new", "message"),
    [
        (
            "pyproject.toml",
            '\nversion = "',
            '\nversion = "9.9.9" #',
            "pyproject.toml",
        ),
        (
            "src/fep_lean/__init__.py",
            '__version__ = "',
            '__version__ = "0.',
            "__init__",
        ),
        ("CITATION.cff", "date-released: ", "date-released: 1999-01-01 #", "CITATION"),
        ("manuscript/config.yaml", "  version: ", "  version: 0.0.1 #", "manuscript"),
        ("config/settings.yaml", "  version: ", "  version: 0.0.1 #", "settings"),
        (".aii/config.yaml", "Release v", "Release v0.0.", ".aii"),
        (".aii/config.yaml", "updated: '", "updated: '1999-01-01' #", ".aii"),
    ],
)
def test_any_metadata_drift_is_reported(
    tmp_path: Path, relative: str, old: str, new: str, message: str
) -> None:
    check = _module()
    root = _copy_sources(tmp_path)
    path = root / relative
    text = path.read_text(encoding="utf-8")
    assert old in text
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    errors = check.metadata_errors(root)
    assert errors and any(message in error for error in errors)


def test_missing_changelog_section_is_reported(tmp_path: Path) -> None:
    check = _module()
    root = _copy_sources(tmp_path)
    release = check.read_release(root)
    changelog = root / "CHANGELOG.md"
    changelog.write_text(
        changelog.read_text(encoding="utf-8").replace(
            f"## {release.version} — {release.date}", "## Unreleased", 1
        ),
        encoding="utf-8",
    )
    assert any("CHANGELOG" in error for error in check.metadata_errors(root))


def test_hosted_ci_requires_successful_run_on_exact_commit() -> None:
    check = _module()
    sha = "a" * 40
    ok = [{"headSha": sha, "status": "completed", "conclusion": "success"}]
    assert check.hosted_errors(sha, ok) == ()
    assert check.hosted_errors(sha, []) != ()
    pending = [{"headSha": sha, "status": "in_progress", "conclusion": ""}]
    assert any("not completed" in e for e in check.hosted_errors(sha, pending))
    failed = [{"headSha": sha, "status": "completed", "conclusion": "failure"}]
    assert any("failure" in e for e in check.hosted_errors(sha, failed))
    other = [{"headSha": "b" * 40, "status": "completed", "conclusion": "success"}]
    assert check.hosted_errors(sha, other) != ()
    # The newest run on the commit decides; an older success does not mask it.
    assert check.hosted_errors(sha, failed + ok) != ()


def _jobs(**overrides: str) -> list[dict[str, str]]:
    names = ["changes", "python", "static", "lean", "render-deps", "render"] + [
        f"distribution ({os}, 3.{minor})"
        for os in ("ubuntu-latest", "macos-latest", "windows-latest")
        for minor in range(10, 15)
    ]
    jobs = [{"name": name, "conclusion": "success"} for name in names]
    jobs.append({"name": "documentation", "conclusion": "skipped"})
    for job in jobs:
        job["conclusion"] = overrides.get(job["name"], job["conclusion"])
    return jobs


def test_hosted_jobs_require_every_promised_lane_to_succeed() -> None:
    check = _module()
    assert check.job_errors(_jobs()) == ()
    # A dispatch run can skip Lean and render yet conclude success.
    skipped = check.job_errors(_jobs(lean="skipped", render="skipped"))
    assert any("'lean': skipped" in e for e in skipped)
    assert any("'render': skipped" in e for e in skipped)
    failed_cell = check.job_errors(
        _jobs(**{"distribution (windows-latest, 3.10)": "failure"})
    )
    assert any("windows-latest, 3.10" in e for e in failed_cell)
    # A reduced pull-request matrix is not release evidence.
    reduced = [
        job for job in _jobs() if not job["name"].endswith((", 3.11)", ", 3.13)"))
    ]
    missing = check.job_errors(reduced)
    assert any("'distribution (macos-latest, 3.11)': missing" in e for e in missing)
    assert len(missing) == 6
    only_python = [{"name": "python", "conclusion": "success"}]
    errors = check.job_errors(only_python)
    assert any("'lean': missing" in e for e in errors)
    assert any("no distribution matrix" in e for e in errors)


def test_release_notes_extract_only_the_version_section(tmp_path: Path) -> None:
    check = _module()
    root = _copy_sources(tmp_path)
    release = check.read_release(root)
    notes = check.release_notes(root, release)
    assert notes.startswith(f"## {release.version} — {release.date}")
    assert "\n## " not in notes[3:]


def test_cli_reports_json_and_exit_status(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    check = _module()
    assert check.main(["--root", str(PROJECT_ROOT), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["errors"] == [] and payload["version"]
    root = _copy_sources(tmp_path)
    (root / "CITATION.cff").write_text("version: 0\n", encoding="utf-8")
    assert check.main(["--root", str(root)]) == 1


def test_bump_rewrites_every_gated_file_and_leaves_only_expected_gaps(
    tmp_path: Path,
) -> None:
    check = _module()
    root = _copy_sources(tmp_path)
    changed = check.bump(root, "9.8.7", "2031-02-03")
    assert ".aii/config.yaml" in changed and "pyproject.toml" in changed
    versions, dates = check.read_versions(root), check.read_dates(root)
    assert {k: v for k, v in versions.items() if k != "uv.lock"} == {
        k: "9.8.7" for k in versions if k != "uv.lock"
    }
    assert set(dates.values()) == {"2031-02-03"}
    errors = check.metadata_errors(root)
    # Only the maintainer-owned steps remain: uv.lock and the changelog section.
    assert len(errors) == 2
    assert any(e.startswith("uv.lock version") for e in errors)
    assert any("CHANGELOG.md lacks" in e and "9.8.7" in e for e in errors)


def test_bump_is_idempotent_and_closes_the_gate_given_lock_and_changelog(
    tmp_path: Path,
) -> None:
    check = _module()
    root = _copy_sources(tmp_path)
    old = check.read_release(root)
    check.bump(root, "9.8.7", "2031-02-03")
    first = {r: (root / r).read_text(encoding="utf-8") for r in _SOURCES}
    check.bump(root, "9.8.7", "2031-02-03")
    assert first == {r: (root / r).read_text(encoding="utf-8") for r in _SOURCES}
    lock = root / "uv.lock"
    lock.write_text(
        lock.read_text(encoding="utf-8").replace(
            f'version = "{old.version}"', 'version = "9.8.7"', 1
        ),
        encoding="utf-8",
    )
    changelog = root / "CHANGELOG.md"
    changelog.write_text(
        "## 9.8.7 — 2031-02-03 — test\n\n" + changelog.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    assert check.metadata_errors(root) == ()


@pytest.mark.parametrize(
    ("version", "date"), [("1.7", "2031-02-03"), ("1.7.0", "03/02/2031")]
)
def test_bump_rejects_malformed_arguments_without_touching_files(
    tmp_path: Path, version: str, date: str
) -> None:
    check = _module()
    root = _copy_sources(tmp_path)
    before = {r: (root / r).read_text(encoding="utf-8") for r in _SOURCES}
    with pytest.raises(ValueError):
        check.bump(root, version, date)
    assert before == {r: (root / r).read_text(encoding="utf-8") for r in _SOURCES}


def test_cli_bump_prints_uv_lock_and_requires_both_flags(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    check = _module()
    root = _copy_sources(tmp_path)
    assert (
        check.main(["--root", str(root), "--bump", "9.8.7", "--date", "2031-02-03"])
        == 0
    )
    assert "uv lock" in capsys.readouterr().out
    assert check.read_release(root).version == "9.8.7"
    with pytest.raises(SystemExit):
        check.main(["--root", str(root), "--bump", "9.8.8"])
