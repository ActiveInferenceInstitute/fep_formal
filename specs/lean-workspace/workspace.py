#!/usr/bin/env python3
"""Coordinate independent Lean packages without combining their namespaces."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import tomllib

TOOLCHAIN = "leanprover/lean4:v4.35.0"
MATHLIB_REV = "56a005855ea17e0b0958f73ec801ae140b0a1679"


def execute(args: list[str], cwd: Path, timeout: int = 30) -> str:
    return subprocess.check_output(
        args, cwd=cwd, text=True, timeout=timeout, stderr=subprocess.PIPE
    ).strip()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def project_lock(repo: dict, config: Path) -> dict:
    root = Path(repo["path"])
    directory = root / config.parent
    pin = directory / "lean-toolchain"
    manifest = directory / "lake-manifest.json"
    dependencies = []
    if manifest.is_file():
        dependencies = json.loads(manifest.read_text()).get("packages", [])
    mathlib = next((p for p in dependencies if p.get("name") == "mathlib"), None)
    return {
        "id": repo["nameWithOwner"] + ":" + config.parent.as_posix(),
        "repository": repo["nameWithOwner"],
        "repository_path": str(root),
        "directory": str(directory),
        "mode": repo["mode"],
        "head": execute(["git", "rev-parse", "HEAD"], root),
        "configuration": config.name,
        "configuration_sha256": digest(directory / config.name),
        "toolchain": pin.read_text().strip() if pin.is_file() else None,
        "manifest_sha256": digest(manifest) if manifest.is_file() else None,
        "mathlib_revision": mathlib.get("rev") if mathlib else None,
        "dependencies": dependencies,
        "sources": {
            p: digest(root / p)
            for p in execute(
                ["git", "ls-files", "-z", "--", str(config.parent)], root
            ).split("\0")
            if p.endswith(".lean") and (root / p).is_file()
        },
    }


def inventory(vault: Path) -> dict:
    scope = json.loads(
        execute(
            [
                str(vault / "_tools/vault"),
                "repos",
                "--limit",
                "1000",
                "--format",
                "json",
            ],
            vault,
            120,
        )
    )
    next_offset = scope.get("next_offset")
    while next_offset is not None:
        page = json.loads(
            execute(
                [
                    str(vault / "_tools/vault"),
                    "repos",
                    "--offset",
                    str(next_offset),
                    "--limit",
                    "1000",
                    "--format",
                    "json",
                ],
                vault,
                120,
            )
        )
        if page["manifest_generated"] != scope["manifest_generated"]:
            raise ValueError(
                "GitVault scope changed during pagination; retry inventory"
            )
        scope["repos"].extend(page["repos"])
        next_offset = page.get("next_offset")
    rows = []
    for repo in scope["repos"]:
        root = Path(repo["path"])
        row = {k: repo[k] for k in ("nameWithOwner", "path", "mode", "visibility")}
        if not (root / ".git").exists():
            rows.append({**row, "state": "missing", "projects": []})
            continue
        try:
            files = execute(["git", "ls-files", "-z"], root).split("\0")
            configs = [
                Path(p)
                for p in files
                if Path(p).name in {"lakefile.lean", "lakefile.toml"}
            ]
            row.update(
                state="scanned",
                projects=[project_lock(repo, p) for p in configs],
                lean_sources=[p for p in files if p.endswith(".lean")],
                toolchain_files=[p for p in files if Path(p).name == "lean-toolchain"],
            )
            rows.append(row)
        except (OSError, subprocess.SubprocessError, ValueError) as exc:
            rows.append(
                {
                    **row,
                    "state": "unavailable",
                    "error": type(exc).__name__,
                    "projects": [],
                }
            )
    return {
        "schema_version": 1,
        "observed": time.time(),
        "manifest_generated": scope["manifest_generated"],
        "required_toolchain": TOOLCHAIN,
        "required_mathlib_revision": MATHLIB_REV,
        "collection_complete": False,
        "scope": "Tracked sources in the current GitVault manifest; missing/unavailable repositories remain explicit.",
        "repositories": rows,
    }


def check_project(project: dict) -> dict:
    directory = Path(project["directory"])
    root = Path(project["repository_path"])
    problems = []
    try:
        if execute(["git", "rev-parse", "HEAD"], root) != project["head"]:
            problems.append("repository head changed; refresh inventory")
        if (
            digest(directory / project["configuration"])
            != project["configuration_sha256"]
        ):
            problems.append("package configuration changed; refresh inventory")
        pin = directory / "lean-toolchain"
        if not pin.is_file() or pin.read_text().strip() != TOOLCHAIN:
            problems.append("toolchain is not exact 4.35.0")
        manifest = directory / "lake-manifest.json"
        if project["manifest_sha256"] != (
            digest(manifest) if manifest.is_file() else None
        ):
            problems.append("dependency manifest changed; refresh inventory")
        configuration = (directory / project["configuration"]).read_text()
        if project["configuration"].endswith(".toml"):
            requirements = tomllib.loads(configuration).get("require", [])
            requirement = next(
                (r for r in requirements if r.get("name") == "mathlib"), None
            )
            requires_mathlib = requirement is not None
            pinned = not requires_mathlib or requirement.get("rev") in {
                "v4.35.0",
                MATHLIB_REV,
            }
        else:
            requirement = re.search(
                r'^\s*require[ \t]+(?:mathlib|"leanprover-community"[ \t]*/[ \t]*"mathlib")[ \t]+([\s\S]*?)(?=\n\S|\Z)',
                configuration,
                re.MULTILINE,
            )
            requires_mathlib = requirement is not None
            pinned = not requires_mathlib or bool(
                re.search(
                    r'@[ \t\r\n]*(?:git[ \t\r\n]+)?"(?:v4\.35\.0|'
                    + MATHLIB_REV
                    + r')"',
                    requirement.group(),
                )
            )
        if requires_mathlib and (
            project["mathlib_revision"] != MATHLIB_REV or not pinned
        ):
            problems.append(
                "Mathlib requires both the stable declaration and exact resolved revision"
            )
        relative_directory = directory.relative_to(root)
        current_sources = {
            relative
            for relative in execute(
                [
                    "git",
                    "ls-files",
                    "--cached",
                    "--others",
                    "--exclude-standard",
                    "-z",
                    "--",
                    str(relative_directory),
                ],
                root,
            ).split("\0")
            if relative.endswith(".lean")
        }
        if current_sources != set(project.get("sources", {})):
            problems.append("tracked Lean source membership changed; refresh inventory")
        for relative, expected in project.get("sources", {}).items():
            source = root / relative
            if not source.is_file() or digest(source) != expected:
                problems.append("Lean source changed: " + relative)
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        problems.append(type(exc).__name__)
    return {
        "id": project["id"],
        "state": (
            "reference-only"
            if project["mode"] != "account"
            else "aligned"
            if not problems
            else "not-aligned"
        ),
        "alignment": "aligned" if not problems else "not-aligned",
        "problems": problems,
    }


def create_workspace(data: dict, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    folders = [
        {"name": p["id"], "path": p["directory"]}
        for r in data["repositories"]
        for p in r["projects"]
        if p["mode"] == "account"
    ]
    folders.extend(
        {"name": r["nameWithOwner"] + ":unpackaged Lean", "path": r["path"]}
        for r in data["repositories"]
        if r.get("mode") == "account"
        and not r["projects"]
        and (r.get("lean_sources") or r.get("toolchain_files"))
    )
    workspace = {
        "folders": folders,
        "extensions": {"recommendations": ["leanprover.lean4"]},
        "settings": {
            "files.watcherExclude": {"**/.lake/**": True, "**/.git/objects/**": True}
        },
    }
    (destination / "Lean.code-workspace").write_text(
        json.dumps(workspace, indent=2) + "\n"
    )
    (destination / "lean-workspace.lock.json").write_text(
        json.dumps(data, indent=2) + "\n"
    )
    (destination / "lean-toolchain").write_text(TOOLCHAIN + "\n")


def build_project(project: dict, log_dir: Path, elan: str, timeout: int) -> dict:
    result = check_project(project)
    if result["state"] != "aligned":
        return result
    if project["mode"] != "account":
        return {"id": project["id"], "state": "reference-only"}
    logfile = log_dir / (
        hashlib.sha256(project["id"].encode()).hexdigest()[:20] + ".log"
    )
    before = time.monotonic()
    try:
        with logfile.open("w") as output:
            run = subprocess.run(
                [
                    elan,
                    "run",
                    TOOLCHAIN,
                    "lake",
                    "--keep-toolchain",
                    "--wfail",
                    "build",
                ],
                check=False,
                cwd=project["directory"],
                stdout=output,
                stderr=subprocess.STDOUT,
                env={**os.environ, "ELAN_TOOLCHAIN": TOOLCHAIN},
                timeout=timeout,
            )
        # A build may discover or update dependencies. Recheck against the lock.
        after = check_project(project)
        state = (
            "passed"
            if run.returncode == 0 and after["state"] == "aligned"
            else "failed"
        )
        return {
            "id": project["id"],
            "state": state,
            "returncode": run.returncode,
            "post_build": after,
            "seconds": round(time.monotonic() - before, 3),
            "log": str(logfile),
            "log_sha256": digest(logfile),
        }
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "id": project["id"],
            "state": "unavailable",
            "error": type(exc).__name__,
            "log": str(logfile),
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["inventory", "workspace", "check", "build"])
    parser.add_argument("--vault", type=Path)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--elan", default="elan")
    parser.add_argument("--timeout", type=int, default=1800)
    args = parser.parse_args()
    if args.action == "inventory":
        if args.vault is None:
            parser.error("--vault is required for inventory")
        data = inventory(args.vault.resolve())
        args.output.write_text(json.dumps(data, indent=2) + "\n")
        return int(any(r["state"] != "scanned" for r in data["repositories"]))
    if args.input is None:
        parser.error("--input is required")
    data = json.loads(args.input.read_text())
    if args.action == "workspace":
        create_workspace(data, args.output)
        return 0
    projects = [p for r in data["repositories"] for p in r["projects"]]
    if args.action == "check":
        results = [check_project(p) for p in projects]
    else:
        # Serialize packages: nested packages can share dependency/build trees.
        args.output.parent.mkdir(parents=True, exist_ok=True)
        log_dir = args.output.parent / "build-logs"
        log_dir.mkdir(exist_ok=True)
        if args.vault is None:
            parser.error("--vault is required for guarded builds")
        sys.path.insert(0, str(args.vault.resolve() / "_tools"))
        from vaultlib import configuration, operation

        cfg = configuration(args.vault.resolve() / "vault.toml")
        with operation(cfg, "lean-workspace-build", repository_writes=True):
            results = [
                build_project(p, log_dir, args.elan, args.timeout) for p in projects
            ]
    missing = [
        r["nameWithOwner"] for r in data["repositories"] if r["state"] != "scanned"
    ]
    passed = not missing and all(
        r["state"] in {"aligned", "passed", "reference-only"} for r in results
    )
    args.output.write_text(
        json.dumps(
            {"passed": passed, "unavailable_repositories": missing, "results": results},
            indent=2,
        )
        + "\n"
    )
    return int(not passed)


if __name__ == "__main__":
    raise SystemExit(main())
