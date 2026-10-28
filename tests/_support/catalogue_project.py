"""Private checkout inputs for real catalogue and reporting pipeline tests.

``output_root`` does not redirect the generated manuscript source projections.
Tests must therefore isolate the project root as well as its runtime output.
Only declared owners, test collection sources and authored manuscript inputs
are copied; Git state, receipts, dependency caches and scientific runs are not.
"""

from __future__ import annotations

import shutil
from hashlib import sha256
from os import stat_result
from pathlib import Path

import pytest

from fep_formal.output.provenance import config_owner_paths, source_owner_paths

REPO_ROOT = Path(__file__).resolve().parents[2]
_EXCLUDED_DIRECTORIES = frozenset(
    {"__pycache__", ".cache", ".pytest_cache", ".lake", ".git", "output"}
)
_GENERATED_MANUSCRIPT_FILES = frozenset(
    {"manuscript_vars.yaml", "09z_unified_formalism_catalogue.md"}
)
_COLLECTION_RESOURCE_FILES = (
    "specs/geo-infer-notation-bridge/check_geo_notation_bridge.py",
    "specs/gnn-bridge-q6-activeinference-artifact/skeleton/canonical_bool_runner.jl.in",
    "specs/lean-workspace/test_workspace.py",
    "specs/lean-workspace/workspace.py",
)


def copy_catalogue_project(source: Path, destination: Path) -> Path:
    """Copy a canonical source project into a fresh private test directory."""
    source = source.resolve()
    destination = destination.resolve()
    if destination == source or destination.is_relative_to(source):
        raise ValueError("catalogue fixture must be outside its source checkout")
    paths = {*source_owner_paths(source), *config_owner_paths(source)}
    paths.update(source / relative for relative in ("CITATION.cff", ".python-version"))
    # Tests load these authored inputs at collection time. Keep that
    # genuine full collection, without copying any bridge receipts or runs.
    paths.update(source / relative for relative in _COLLECTION_RESOURCE_FILES)
    paths.update(
        path
        for path in (source / "tests").rglob("*.py")
        if not (_EXCLUDED_DIRECTORIES & set(path.relative_to(source).parts))
    )
    # These are authored resources; generated projections are produced by the
    # real pipeline, with no pre-existing receipt or test-census cache to reuse.
    paths.update(
        path
        for path in (source / "manuscript").rglob("*")
        if path.is_file()
        and path.name not in _GENERATED_MANUSCRIPT_FILES
        and not (_EXCLUDED_DIRECTORIES & set(path.relative_to(source).parts))
    )
    destination.mkdir(parents=True, exist_ok=False)
    for path in sorted(paths):
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"canonical fixture input is not a regular file: {path}")
        target = destination / path.relative_to(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    return destination


def manuscript_owner_state(project: Path) -> dict[str, tuple[object, ...]]:
    """Observe live manuscript bytes and metadata, excluding read-only atime."""

    def identity(stat: stat_result) -> tuple[int, ...]:
        return (
            stat.st_dev,
            stat.st_ino,
            stat.st_mode,
            stat.st_size,
            stat.st_mtime_ns,
            stat.st_ctime_ns,
        )

    result: dict[str, tuple[object, ...]] = {}
    for path in sorted((project / "manuscript").rglob("*")):
        if path.is_file():
            before = path.stat()
            digest = sha256(path.read_bytes()).hexdigest()
            after = path.stat()
            assert identity(before) == identity(after), f"input changed: {path}"
            result[path.relative_to(project).as_posix()] = (digest, *identity(after))
    return result


@pytest.fixture
def catalogue_project(tmp_path: Path) -> Path:
    """Each test receives its own real, writable catalogue project inputs."""
    return copy_catalogue_project(REPO_ROOT, tmp_path / "catalogue-project")
