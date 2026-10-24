#!/usr/bin/env python3
"""Check the release gate: one version/date, a changelog section, green hosted CI.

The gate is deliberately short (see release.md). Hosted acceptance includes
every required installed-wheel matrix cell. Research and evidence lanes
(H3 study, capture custody, optional provider runs) retain their own acceptance
probes and are reported in release notes.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import tomllib
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = "ci.yml"
#: Jobs whose success the release table in release.md promises. A dispatch
#: run may skip Lean or render and still conclude ``success``, so the run
#: conclusion alone is not enough.
REQUIRED_JOBS = ("python", "static", "lean", "render-deps", "render")
DISTRIBUTION_PREFIX = "distribution ("
# Automatic code PRs, main pushes and manual full runs use the full matrix.
# The release gate requires every operating system and interpreter cell.
DISTRIBUTION_CELLS = tuple(
    f"distribution ({os}, {python})"
    for os in ("ubuntu-latest", "macos-latest", "windows-latest")
    for python in ("3.10", "3.11", "3.12", "3.13", "3.14")
)
#: InstituteOS sidecar: ``repo.description`` names ``Release vX.Y.Z`` and the
#: date; ``meta.updated`` carries the release date.
SIDECAR = ".aii/config.yaml"


@dataclass(frozen=True)
class Release:
    version: str
    date: str

    @property
    def tag(self) -> str:
        return f"v{self.version}"


def _text(root: Path, relative: str) -> str:
    return (root / relative).read_text(encoding="utf-8")


def _assignment(root: Path, relative: str, name: str) -> str | None:
    match = re.search(rf'(?m)^{name}\s*=\s*"([^"]+)"\s*$', _text(root, relative))
    return match.group(1) if match else None


def _yaml(root: Path, relative: str) -> dict[str, Any]:
    data = yaml.safe_load(_text(root, relative))
    return data if isinstance(data, dict) else {}


def _nested(data: dict[str, Any], *keys: str) -> str | None:
    value: Any = data
    for key in keys:
        value = value.get(key) if isinstance(value, dict) else None
    return None if value is None else str(value)


def _lock_version(root: Path) -> str | None:
    packages = tomllib.loads(_text(root, "uv.lock")).get("package", [])
    versions = [p.get("version") for p in packages if p.get("name") == "fep-lean"]
    return versions[0] if len(versions) == 1 else None


def _sidecar_release(root: Path) -> str | None:
    """The release version the InstituteOS sidecar description names."""
    repo = _yaml(root, SIDECAR).get("repo")
    description = str(repo.get("description", "")) if isinstance(repo, dict) else ""
    match = re.search(r"Release v(\d+\.\d+\.\d+\S*)", description)
    return match.group(1) if match else None


def read_versions(root: Path) -> dict[str, str | None]:
    """Every version-bearing source, keyed by the file a maintainer edits."""
    pyproject = tomllib.loads(_text(root, "pyproject.toml"))
    return {
        "pyproject.toml": pyproject.get("project", {}).get("version"),
        "src/fep_lean/__init__.py": _assignment(
            root, "src/fep_lean/__init__.py", "__version__"
        ),
        "release_bundle/_constants.py": _assignment(
            root,
            "src/fep_lean/output/release_bundle/_constants.py",
            "_CANONICAL_RELEASE_VERSION",
        ),
        "CITATION.cff": _nested(_yaml(root, "CITATION.cff"), "version"),
        "manuscript/config.yaml": _nested(
            _yaml(root, "manuscript/config.yaml"), "paper", "version"
        ),
        "config/settings.yaml": _nested(
            _yaml(root, "config/settings.yaml"), "project", "version"
        ),
        SIDECAR: _sidecar_release(root),
        "uv.lock": _lock_version(root),
    }


def read_dates(root: Path) -> dict[str, str | None]:
    return {
        "CITATION.cff": _nested(_yaml(root, "CITATION.cff"), "date-released"),
        "manuscript/config.yaml": _nested(
            _yaml(root, "manuscript/config.yaml"), "paper", "date"
        ),
        "release_bundle/_constants.py": _assignment(
            root,
            "src/fep_lean/output/release_bundle/_constants.py",
            "_CANONICAL_RELEASE_DATE",
        ),
        SIDECAR: _nested(_yaml(root, SIDECAR), "meta", "updated"),
    }


def read_release(root: Path) -> Release:
    versions, dates = read_versions(root), read_dates(root)
    return Release(
        version=versions["pyproject.toml"] or "", date=dates["CITATION.cff"] or ""
    )


_VERSION_RE = re.compile(r"\d+\.\d+\.\d+")
_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
_CONSTANTS = "src/fep_lean/output/release_bundle/_constants.py"


def _sub_once(text: str, pattern: str, replacement: str) -> str:
    new, count = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE)
    if count != 1:
        raise ValueError(f"pattern not found: {pattern}")
    return new


def bump(root: Path, version: str, date: str) -> tuple[str, ...]:
    """Rewrite the version and date in every file the gate reads.

    Edits are line-local regex substitutions so quoting and comments survive.
    ``uv.lock`` and ``CHANGELOG.md`` are deliberately left to the maintainer
    (``uv lock``; a dated section); returns the files rewritten.
    """
    if not _VERSION_RE.fullmatch(version):
        raise ValueError(f"version must look like X.Y.Z, got {version!r}")
    if not _DATE_RE.fullmatch(date):
        raise ValueError(f"date must look like YYYY-MM-DD, got {date!r}")
    qv, qd = f'"{version}"', f'"{date}"'
    edits: dict[str, list[tuple[str, str]]] = {
        "pyproject.toml": [(r'^version\s*=\s*"[^"]+"', f"version = {qv}")],
        "src/fep_lean/__init__.py": [
            (r'^__version__\s*=\s*"[^"]+"', f"__version__ = {qv}")
        ],
        _CONSTANTS: [
            (
                r'^_CANONICAL_RELEASE_VERSION\s*=\s*"[^"]+"',
                f"_CANONICAL_RELEASE_VERSION = {qv}",
            ),
            (
                r'^_CANONICAL_RELEASE_DATE\s*=\s*"[^"]+"',
                f"_CANONICAL_RELEASE_DATE = {qd}",
            ),
        ],
        "CITATION.cff": [
            (r"^version:.*$", f"version: {qv}"),
            (r"^date-released:.*$", f"date-released: {qd}"),
        ],
        "manuscript/config.yaml": [
            (r"^(  version:\s*).*$", rf"\g<1>{qv}"),
            (r"^(  date:\s*).*$", rf"\g<1>{qd}"),
        ],
        "config/settings.yaml": [(r"^(  version:\s*).*$", rf"\g<1>{qv}")],
        SIDECAR: [
            (r"Release v\d+\.\d+\.\d+\S*", f"Release v{version}"),
            (r"(?<=\()\d{4}-\d{2}-\d{2}", date),
            (r"^(  updated:\s*).*$", rf"\g<1>'{date}'"),
        ],
    }
    # Compute everything first so a failed pattern leaves the tree untouched.
    rewritten: dict[str, str] = {}
    for relative, subs in edits.items():
        text = _text(root, relative)
        for pattern, replacement in subs:
            text = _sub_once(text, pattern, replacement)
        rewritten[relative] = text
    for relative, text in rewritten.items():
        (root / relative).write_text(text, encoding="utf-8")
    return tuple(rewritten)


def _heading(release: Release) -> str:
    return f"## {release.version} — {release.date}"


def metadata_errors(root: Path) -> tuple[str, ...]:
    release = read_release(root)
    errors = [
        f"{source} version {value!r} != pyproject.toml {release.version!r}"
        for source, value in read_versions(root).items()
        if value != release.version
    ]
    errors += [
        f"{source} date {value!r} != CITATION.cff {release.date!r}"
        for source, value in read_dates(root).items()
        if value != release.date
    ]
    headings = re.findall(r"(?m)^## .*$", _text(root, "CHANGELOG.md"))
    if not any(h.startswith(_heading(release)) for h in headings):
        errors.append(f"CHANGELOG.md lacks a '{_heading(release)}' section")
    return tuple(errors)


def release_notes(root: Path, release: Release) -> str:
    lines = _text(root, "CHANGELOG.md").splitlines()
    start = next(
        i for i, line in enumerate(lines) if line.startswith(_heading(release))
    )
    end = next(
        (i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")),
        len(lines),
    )
    return "\n".join(lines[start:end]).strip() + "\n"


def hosted_errors(sha: str, runs: list[dict[str, Any]]) -> tuple[str, ...]:
    """The newest hosted CI run on the exact commit must have succeeded."""
    exact = [run for run in runs if run.get("headSha") == sha]
    if not exact:
        return (f"no hosted {WORKFLOW} run for {sha}",)
    newest = exact[0]
    if newest.get("status") != "completed":
        return (f"hosted {WORKFLOW} run for {sha} not completed",)
    if newest.get("conclusion") != "success":
        return (f"hosted {WORKFLOW} run for {sha}: {newest.get('conclusion')}",)
    return ()


def job_errors(jobs: list[dict[str, Any]]) -> tuple[str, ...]:
    """Every promised job must have run and succeeded, none skipped."""
    conclusions = {str(job.get("name")): job.get("conclusion") for job in jobs}
    errors = [
        f"hosted {WORKFLOW} job {name!r}: {conclusions.get(name) or 'missing'}"
        for name in REQUIRED_JOBS
        if conclusions.get(name) != "success"
    ]
    cells = {n: c for n, c in conclusions.items() if n.startswith(DISTRIBUTION_PREFIX)}
    if not cells:
        errors.append(f"hosted {WORKFLOW} run has no distribution matrix jobs")
    else:
        errors += [
            f"hosted {WORKFLOW} job {name!r}: missing"
            for name in DISTRIBUTION_CELLS
            if name not in cells
        ]
    errors += [
        f"hosted {WORKFLOW} job {name!r}: {conclusion}"
        for name, conclusion in sorted(cells.items())
        if conclusion != "success"
    ]
    return tuple(errors)


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()


def repository_errors(root: Path) -> tuple[str, ...]:
    errors = []
    if _git(root, "status", "--porcelain"):
        errors.append("working tree is not clean")
    _git(root, "fetch", "--quiet", "origin", "main")
    if _git(root, "rev-parse", "HEAD") != _git(root, "rev-parse", "origin/main"):
        errors.append("HEAD is not origin/main")
    return tuple(errors)


def fetch_runs(root: Path, sha: str) -> list[dict[str, Any]]:
    output = subprocess.run(
        [
            "gh", "run", "list", "--workflow", WORKFLOW, "--commit", sha,
            "--json", "headSha,status,conclusion,databaseId", "--limit", "20",
        ],
        cwd=root, check=True, capture_output=True, text=True,
    ).stdout  # fmt: skip
    runs = json.loads(output)
    return runs if isinstance(runs, list) else []


def fetch_jobs(root: Path, run_id: int) -> list[dict[str, Any]]:
    output = subprocess.run(
        ["gh", "run", "view", str(run_id), "--json", "jobs"],
        cwd=root, check=True, capture_output=True, text=True,
    ).stdout  # fmt: skip
    payload = json.loads(output)
    jobs = payload.get("jobs") if isinstance(payload, dict) else None
    return jobs if isinstance(jobs, list) else []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT)
    parser.add_argument(
        "--hosted",
        action="store_true",
        help="also require a clean HEAD equal to origin/main with green hosted CI",
    )
    parser.add_argument(
        "--bump",
        metavar="X.Y.Z",
        help="rewrite the version in every gated file (requires --date), then exit",
    )
    parser.add_argument("--date", metavar="YYYY-MM-DD", help="release date for --bump")
    parser.add_argument("--notes", type=Path, help="write the release notes here")
    parser.add_argument("--json", action="store_true", help="print a JSON report")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if args.bump or args.date:
        if not (args.bump and args.date):
            parser.error("--bump and --date must be given together")
        try:
            changed = bump(root, args.bump, args.date)
        except ValueError as exc:
            print(f"FAIL: {exc}", file=sys.stderr)
            return 1
        print(f"Bumped {len(changed)} files to {args.bump} ({args.date}):")
        for relative in changed:
            print(f"  {relative}")
        print("Remaining manual steps:")
        print(
            f"  1. add a '## {args.bump} — {args.date} — title' section to CHANGELOG.md"
        )
        print("  2. uv lock   # refreshes the fep-lean entry in uv.lock")
        print("  3. uv run python docs/release_check.py")
        return 0
    release = read_release(root)
    errors = list(metadata_errors(root))
    if args.hosted:
        errors += repository_errors(root)
        sha = _git(root, "rev-parse", "HEAD")
        runs = fetch_runs(root, sha)
        run_errors = hosted_errors(sha, runs)
        errors += run_errors
        if not run_errors:
            newest = next(run for run in runs if run.get("headSha") == sha)
            errors += job_errors(fetch_jobs(root, int(newest["databaseId"])))
    if args.notes and not errors:
        args.notes.write_text(release_notes(root, release), encoding="utf-8")
    if args.json:
        report = {"version": release.version, "date": release.date, "errors": errors}
        print(json.dumps(report, indent=2))
    else:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        if not errors:
            print(f"OK: release {release.tag} ({release.date}) gate passes")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
