"""Manuscript projections and deterministic generated appendices."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from fep_lean.catalogue.coverage import build_formalism_coverage
from fep_lean.catalogue.relations import EdgeKind
from fep_lean.catalogue.topics import FEPTopicCatalogue
from fep_lean.output.evidence import (
    latest_claim_ready_full_report,
    validate_native_lean_receipt,
)
from fep_lean.output.provenance import config_owner_paths, source_owner_paths
from fep_lean.output.publication_metadata import (
    load_graphical_abstract,
    load_repository_url,
    load_publication_author,
)

UNIFIED_FORMALISM_CATALOGUE_FILENAME = "09z_unified_formalism_catalogue.md"
# ``source`` carries the checkout identity and the wall-clock render date, so
# it is run-bound by construction and must not participate in drift equality.
_RUN_BOUND_MANUSCRIPT_KEYS = frozenset(
    {"compile_rate", "full", "hermes", "source", "verify"}
)
_TEST_COLLECTION_CACHE_SCHEMA_VERSION = 4
_TEST_COLLECTION_PLUGIN_DISTRIBUTIONS = ("pytest", "pytest-timeout")
_TEST_COLLECTION_EXPLICIT_PLUGINS = ("pytest_timeout",)
_TEST_COLLECTION_ENVIRONMENT_POLICY = {
    "FEP_LEAN_LIVE_TESTS": "0",
    "LANG": "C.UTF-8",
    "LC_ALL": "C.UTF-8",
    "MPLBACKEND": "Agg",
    "PATH": os.defpath,
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONHASHSEED": "0",
    "PYTHONNOUSERSITE": "1",
    "PYTEST_ADDOPTS": "",
    "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
    "TZ": "UTC",
}
_TEST_COLLECTION_TEMP_ENVIRONMENT_POLICY = {
    "HOME": "home",
    "MPLCONFIGDIR": "matplotlib",
    "TMPDIR": ".",
    "XDG_CACHE_HOME": "xdg-cache",
}


def _git_output(project_root: Path, arguments: list[str]) -> str:
    """Return trimmed ``git`` stdout, or the empty string when git cannot answer."""

    try:
        completed = subprocess.run(  # nosec B603 B607 - fixed argv, shell=False
            ["git", "-C", str(project_root), *arguments],
            capture_output=True,
            check=False,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def _source_stamp_vars(project_root: Path) -> dict[str, str]:
    """Return the checkout identity this render describes.

    The title page carries an authored ``paper.version``/``paper.date`` from
    ``manuscript/config.yaml``, which a reader uses to fetch the sources behind
    the numbers.  When the checkout has moved past the stamped tag, those two
    fields silently describe a different tree: the audited v1.1.0 stamp sat on
    a paper whose live-token counts came from a tree 15,033 Lean lines newer,
    and no reader could reproduce a single headline count from the tag.

    These variables are the reproducible complement -- the exact commit the
    numbers were computed from, whether that checkout was clean, and when the
    render happened.  Every value is computed; none is authored.
    """

    root = Path(project_root)
    commit = _git_output(root, ["rev-parse", "HEAD"])
    short_commit = _git_output(root, ["rev-parse", "--short=12", "HEAD"])
    describe = _git_output(root, ["describe", "--tags", "--always", "--dirty"])
    exact_tag = _git_output(root, ["describe", "--exact-match", "--tags", "HEAD"])
    porcelain = _git_output(root, ["status", "--porcelain"])
    commit_date = _git_output(root, ["log", "-1", "--format=%cI"])
    dirty = bool(porcelain)
    stamp = short_commit or "unknown"
    if dirty:
        stamp = f"{stamp} (uncommitted changes present)"
    return {
        "commit": commit or "unknown",
        "short_commit": short_commit or "unknown",
        "describe": describe or "unknown",
        "exact_tag": exact_tag or "none",
        "commit_date": commit_date or "unknown",
        "dirty": "true" if dirty else "false",
        "render_date": datetime.now(UTC).date().isoformat(),
        # One ready-to-typeset line for the title page.
        "stamp": (
            f"source snapshot {stamp}, rendered "
            f"{datetime.now(UTC).date().isoformat()}"
        ),
    }


def _read_toolchain_vars(project_root: Path) -> dict[str, str]:
    lean_dir = Path(project_root) / "lean"
    toolchain = (
        (lean_dir / "lean-toolchain").read_text(encoding="utf-8").strip()
        if (lean_dir / "lean-toolchain").is_file()
        else ""
    )
    lean_version = toolchain.rsplit(":", 1)[-1].removeprefix("v") if toolchain else ""
    mathlib_tag = ""
    lakefile = lean_dir / "lakefile.lean"
    if lakefile.is_file():
        text = lakefile.read_text(encoding="utf-8")
        match = re.search(r'@\s*"([^"]+)"', text)
        if match:
            mathlib_tag = match.group(1)
    manifest = lean_dir / "lake-manifest.json"
    if not mathlib_tag and manifest.is_file():
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
            for package in data.get("packages", []):
                if package.get("name") == "mathlib":
                    mathlib_tag = str(package.get("inputRev", ""))
                    break
        except (OSError, ValueError, TypeError):
            pass
    return {
        "lean_toolchain": toolchain,
        "lean_version": lean_version,
        "mathlib_tag": mathlib_tag,
    }


def _get_latest_verification_manifest(
    project_root: Path, output_root: Path | None = None
) -> Path | None:
    report_root = latest_claim_ready_full_report(
        project_root,
        output_root=output_root,
    )
    return report_root / "verification_manifest.json" if report_root else None


def _verify_block_from_manifest(path: Path | None) -> dict[str, Any]:
    base: dict[str, Any] = {
        "manifest_present": False,
        "evidence_kind": "unavailable",
        "claim_ready": False,
        "run_id": "not available",
        "verify_lean_ran": False,
        "topics_with_result": 0,
        "compiles_true": 0,
        "compiles_false": 0,
        "sorry_count": 0,
        "sorry_topics": 0,
        "sorry_occurrences": 0,
        "warning_count": 0,
        "duration_seconds": 0.0,
        "duration_min": 0.0,
        "mean_topic_s": 0.0,
        "failed_topic_ids": "none",
        "not_clean_topic_ids": "none",
        "failed_compile_topic_ids": "none",
        "clean_topic_ids": [],
    }
    if path is None or not path.is_file():
        return base
    base["manifest_present"] = True
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return base
    results = data.get("results") if isinstance(data, dict) else []
    if not isinstance(results, list):
        results = []
    base["verify_lean_ran"] = bool(data.get("verify_lean_ran", False))
    base["evidence_kind"] = "full-pipeline"
    base["run_id"] = path.parent.name
    base["topics_with_result"] = (
        int(data.get("topics_with_result", len(results)))
        if str(data.get("topics_with_result", len(results))).isdigit()
        else len(results)
    )
    base["compiles_true"] = int(
        data.get(
            "compiles_true",
            sum(bool(r.get("compiles")) for r in results if isinstance(r, dict)),
        )
    )
    base["compiles_false"] = int(
        data.get("compiles_false", max(0, len(results) - base["compiles_true"]))
    )
    durations = [
        float(row.get("duration_s", 0.0) or 0.0)
        for row in results
        if isinstance(row, dict)
    ]
    # Two different questions, two different numbers. ``sorry_topics`` counts
    # topics that admit anything; ``sorry_occurrences`` counts admitted proofs.
    # Prose that says "uses of ``sorry``" wants the second. ``sorry_count`` is
    # retained as the historical alias of ``sorry_topics``.
    sorry_topics = sum(
        bool(row.get("has_sorry", row.get("lean_has_sorry", False)))
        for row in results
        if isinstance(row, dict)
    )
    sorry_occurrences = sum(
        int(row["sorry_occurrences"])
        if isinstance(row.get("sorry_occurrences"), int)
        and not isinstance(row.get("sorry_occurrences"), bool)
        else bool(row.get("has_sorry", row.get("lean_has_sorry", False)))
        for row in results
        if isinstance(row, dict)
    )
    warning_count = sum(
        len(row.get("warnings", []))
        for row in results
        if isinstance(row, dict) and isinstance(row.get("warnings", []), list)
    )
    clean_ids = [
        str(row.get("topic_id", ""))
        for row in results
        if isinstance(row, dict)
        and bool(row.get("compiles", False))
        and not bool(row.get("has_sorry", row.get("lean_has_sorry", False)))
        and not row.get("warnings", [])
    ]
    # ``clean`` means compiled, unadmitted and warning-free, so its complement
    # includes topics that compiled cleanly but emitted a warning. Printing
    # that complement under the label "failed" is wrong; name both sets.
    not_clean_ids = [
        str(row.get("topic_id", ""))
        for row in results
        if isinstance(row, dict) and str(row.get("topic_id", "")) not in clean_ids
    ]
    failed_compile_ids = [
        str(row.get("topic_id", ""))
        for row in results
        if isinstance(row, dict) and not bool(row.get("compiles", False))
    ]
    duration_seconds = sum(durations)
    base.update(
        {
            "sorry_count": sorry_topics,
            "sorry_topics": sorry_topics,
            "sorry_occurrences": sorry_occurrences,
            "warning_count": warning_count,
            "duration_seconds": round(duration_seconds, 3),
            "duration_min": round(duration_seconds / 60, 2),
            "mean_topic_s": round(duration_seconds / len(durations), 3)
            if durations
            else 0.0,
            "failed_topic_ids": ", ".join(not_clean_ids) or "none",
            "not_clean_topic_ids": ", ".join(not_clean_ids) or "none",
            "failed_compile_topic_ids": ", ".join(failed_compile_ids) or "none",
            "clean_topic_ids": clean_ids,
        }
    )
    return base


def _verify_block_from_native_receipt(
    path: Path | None, project_root: Path
) -> dict[str, Any]:
    """Project a validated native receipt into manuscript-safe variables."""
    base = _verify_block_from_manifest(None)
    if path is None or not path.is_file():
        return base
    validation = validate_native_lean_receipt(path, project_root=project_root)
    base["manifest_present"] = True
    base["evidence_kind"] = "native-lean"
    base["claim_ready"] = bool(validation.get("native_claim_ready", False))
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return base
    rows = payload.get("results", []) if isinstance(payload, dict) else []
    rows = rows if isinstance(rows, list) else []
    clean_ids = [
        str(row.get("topic_id", ""))
        for row in rows
        if isinstance(row, dict)
        and bool(row.get("compiles", False))
        and not bool(row.get("has_sorry", False))
        and not row.get("warnings", [])
    ]
    not_clean_ids = [
        str(row.get("topic_id", ""))
        for row in rows
        if isinstance(row, dict) and str(row.get("topic_id", "")) not in clean_ids
    ]
    failed_compile_ids = [
        str(row.get("topic_id", ""))
        for row in rows
        if isinstance(row, dict) and not bool(row.get("compiles", False))
    ]
    duration_seconds = float(payload.get("duration_s", 0.0) or 0.0)
    catalogue_digest = str(payload.get("catalogue_sha256", ""))
    base.update(
        {
            "run_id": f"native-{catalogue_digest[:12]}"
            if catalogue_digest
            else "native-unidentified",
            "verify_lean_ran": bool(rows),
            "topics_with_result": len(rows),
            "compiles_true": sum(
                bool(row.get("compiles", False))
                for row in rows
                if isinstance(row, dict)
            ),
            "compiles_false": sum(
                not bool(row.get("compiles", False))
                for row in rows
                if isinstance(row, dict)
            ),
            "sorry_count": int(validation.get("sorry_count", 0)),
            "sorry_topics": int(validation.get("sorry_count", 0)),
            "sorry_occurrences": int(
                validation.get("sorry_occurrences", validation.get("sorry_count", 0))
            ),
            "warning_count": int(validation.get("warning_count", 0)),
            "duration_seconds": round(duration_seconds, 3),
            "duration_min": round(duration_seconds / 60, 2),
            "mean_topic_s": round(duration_seconds / len(rows), 3) if rows else 0.0,
            "failed_topic_ids": ", ".join(not_clean_ids) or "none",
            "not_clean_topic_ids": ", ".join(not_clean_ids) or "none",
            "failed_compile_topic_ids": ", ".join(failed_compile_ids) or "none",
            "clean_topic_ids": clean_ids,
        }
    )
    return base


def _hermes_block_from_summary(path: Path | None) -> dict[str, Any]:
    keys: dict[str, Any] = {
        "summary_present": False,
        "run_id": "",
        "processed": 0,
        "success_count": 0,
        "cache_hits": 0,
        "mean_topic_s": 0.0,
        "tokens_total": 0,
        "tokens_mean": 0,
        "hermes_lean_compiles_count": 0,
        "primary_model": "",
        "models_used": "",
        "model_fallback_count": 0,
        "network_retry_count": 0,
        "chain_advance_reasons": {},
        "chain_advance_reasons_summary": "none",
    }
    if path is None or not path.is_file():
        return keys
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return keys
    rows = data.get("topics", []) if isinstance(data, dict) else []
    rows = rows if isinstance(rows, list) else []
    models = [
        str(r.get("hermes_model", ""))
        for r in rows
        if isinstance(r, dict) and r.get("hermes_model")
    ]
    reasons: dict[str, int] = {}
    primary_models: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        model = str(row.get("hermes_model", ""))
        reason = str(row.get("chain_advance_reason", ""))
        if reason:
            reasons[reason] = reasons.get(reason, 0) + 1
        elif model:
            primary_models.add(model)
    tokens = [
        int(r.get("tokens_used", 0) or 0)
        for r in rows
        if isinstance(r, dict) and int(r.get("tokens_used", 0) or 0) > 0
    ]
    durations = [
        float(r.get("duration_s", 0.0) or 0.0)
        for r in rows
        if isinstance(r, dict) and float(r.get("duration_s", 0.0) or 0.0) > 0
    ]
    run_id = str(data.get("run_id", ""))
    if run_id and not run_id.startswith("run_"):
        run_id = "run_" + run_id
    primary_model = next(iter(primary_models)) if len(primary_models) == 1 else ""
    keys.update(
        {
            "summary_present": True,
            "run_id": run_id,
            "processed": len(rows),
            "success_count": sum(
                bool(r.get("hermes_success")) for r in rows if isinstance(r, dict)
            ),
            "cache_hits": sum(
                bool(r.get("cache_hit")) for r in rows if isinstance(r, dict)
            ),
            "mean_topic_s": round(sum(durations) / len(durations), 3)
            if durations
            else 0.0,
            "tokens_total": sum(tokens),
            "tokens_mean": sum(tokens) // len(tokens) if tokens else 0,
            "hermes_lean_compiles_count": sum(
                bool(r.get("hermes_lean_compiles")) for r in rows if isinstance(r, dict)
            ),
            "primary_model": primary_model,
            "models_used": ", ".join(sorted(set(models))),
            "model_fallback_count": sum(reasons.values()),
            "network_retry_count": sum(
                int(r.get("network_retries", 0) or 0)
                for r in rows
                if isinstance(r, dict)
            ),
            "chain_advance_reasons": reasons,
        }
    )
    keys["chain_advance_reasons_summary"] = (
        ", ".join(
            f"{n}× {reason}"
            for reason, n in sorted(
                reasons.items(), key=lambda item: (-item[1], item[0])
            )
        )
        or "none"
    )
    return keys


def _safe_project_path(project_root: Path, path: Path, *, label: str) -> Path:
    """Return a lexical in-root path after rejecting every symlink component."""
    root = Path(os.path.abspath(project_root))
    candidate = Path(os.path.abspath(path))
    for component in (*reversed(root.parents), root):
        if component.is_symlink():
            raise ValueError(
                f"unsafe {label}: project root ancestor is a symlink: {component}"
            )
        if component.exists() and not component.is_dir():
            raise ValueError(
                f"unsafe {label}: project root ancestor is not a directory: {component}"
            )
    try:
        relative = candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"unsafe {label}: path escapes project root: {path}") from exc
    current = root
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            raise ValueError(f"unsafe {label}: symlink path component: {current}")
        if current != candidate and current.exists() and not current.is_dir():
            raise ValueError(f"unsafe {label}: non-directory path component: {current}")
    return candidate


def _test_collection_input_paths(project_root: Path) -> tuple[Path, ...]:
    """Return every file whose bytes can affect pytest collection.

    Collection-time parametrization imports the maintained catalogue and formal
    manifests, so test files and ``pyproject.toml`` alone are not a closed
    cache key.  Reuse the source/config receipt owners and add every Python
    test; missing owners remain part of the fingerprint rather than silently
    shrinking it.
    """
    root = Path(os.path.abspath(project_root))
    tests_root = _safe_project_path(root, root / "tests", label="test collection input")
    paths = {*source_owner_paths(root), *config_owner_paths(root)}
    if tests_root.exists():
        if not tests_root.is_dir():
            raise ValueError("unsafe test collection input: tests is not a directory")
        for directory, dirnames, filenames in os.walk(tests_root, followlinks=False):
            current = Path(directory)
            for name in (*dirnames, *filenames):
                child = _safe_project_path(
                    root, current / name, label="test collection input"
                )
                if child.suffix == ".py" and name in filenames:
                    paths.add(child)
    validated: set[Path] = set()
    for path in paths:
        safe = _safe_project_path(root, path, label="test/source/config input")
        if safe.exists() and not safe.is_file():
            raise ValueError(f"unsafe test/source/config input: not a file: {safe}")
        validated.add(safe)
    return tuple(sorted(validated, key=lambda path: path.as_posix()))


def _collection_runtime_identity() -> dict[str, Any]:
    """Return the interpreter, plugin, and hermetic-policy collection identity."""
    executable = Path(sys.executable).resolve()
    if not executable.is_file():
        raise ValueError(f"pytest collection interpreter is not a file: {executable}")
    plugins: dict[str, str] = {}
    for distribution in _TEST_COLLECTION_PLUGIN_DISTRIBUTIONS:
        try:
            plugins[distribution] = importlib.metadata.version(distribution)
        except importlib.metadata.PackageNotFoundError as exc:
            raise ValueError(
                f"required pytest collection distribution is missing: {distribution}"
            ) from exc
    return {
        "environment": {
            **_TEST_COLLECTION_ENVIRONMENT_POLICY,
            **{
                name: f"<temporary>/{relative}" if relative != "." else "<temporary>"
                for name, relative in _TEST_COLLECTION_TEMP_ENVIRONMENT_POLICY.items()
            },
        },
        "explicit_plugins": list(_TEST_COLLECTION_EXPLICIT_PLUGINS),
        "interpreter": {
            "cache_tag": sys.implementation.cache_tag,
            "executable": executable.as_posix(),
            "executable_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
            "implementation": sys.implementation.name,
            "version": sys.version,
        },
        "plugin_distributions": plugins,
        "pytest_arguments": [
            "tests",
            "--collect-only",
            "-q",
            "--color=no",
            *(
                argument
                for plugin in _TEST_COLLECTION_EXPLICIT_PLUGINS
                for argument in ("-p", plugin)
            ),
            "-o",
            "cache_dir=<temporary>",
            "-o",
            "addopts=",
        ],
    }


def _test_collection_fingerprint(
    project_root: Path, *, identity: dict[str, Any] | None = None
) -> str:
    root = Path(project_root)
    digest = hashlib.sha256()
    digest.update(
        json.dumps(
            identity if identity is not None else _collection_runtime_identity(),
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )
    digest.update(b"\0")
    for path in _test_collection_input_paths(root):
        try:
            relative = path.relative_to(root).as_posix()
        except ValueError:
            relative = path.as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes() if path.is_file() else b"<missing>")
        digest.update(b"\0")
    return digest.hexdigest()


def _pytest_collection_command(cache_dir: Path) -> list[str]:
    """Return the exact quiet collection command used by evidence builders."""
    return [
        sys.executable,
        "-m",
        "pytest",
        "tests",
        "--collect-only",
        "-q",
        "--color=no",
        *(
            argument
            for plugin in _TEST_COLLECTION_EXPLICIT_PLUGINS
            for argument in ("-p", plugin)
        ),
        "-o",
        f"cache_dir={cache_dir}",
        "-o",
        "addopts=",
    ]


def _pytest_collection_environment(temporary_root: Path) -> dict[str, str]:
    """Return the hermetic environment used for collection evidence."""
    return {
        **_TEST_COLLECTION_ENVIRONMENT_POLICY,
        **{
            name: str(temporary_root / relative)
            if relative != "."
            else str(temporary_root)
            for name, relative in _TEST_COLLECTION_TEMP_ENVIRONMENT_POLICY.items()
        },
    }


def _parse_pytest_collection_stdout(stdout: str) -> tuple[str, ...]:
    """Parse the exact ordered node-id roster from quiet pytest output."""
    summary_pattern = re.compile(
        r"(?:=+\s+)?([1-9]\d*) tests? collected in "
        r"[0-9]+(?:\.[0-9]+)?s(?:\s+=+)?"
    )
    stdout_lines = [line for line in stdout.splitlines() if line.strip()]
    matches = [
        match
        for line in stdout_lines
        if (match := summary_pattern.fullmatch(line)) is not None
    ]
    if len(matches) != 1:
        raw_excerpt = " ".join(stdout.split())[-400:]
        excerpt = raw_excerpt.encode("unicode_escape").decode("ascii") or "<empty>"
        raise ValueError(
            "pytest collection did not report exactly one anchored positive "
            f"summary; found {len(matches)}; stdout tail: {excerpt}"
        )
    if not stdout_lines or summary_pattern.fullmatch(stdout_lines[-1]) is None:
        raise ValueError("pytest collection summary was not the final stdout line")
    count = int(matches[0].group(1))
    node_ids = tuple(stdout_lines[:-1])
    if (
        len(node_ids) != count
        or len(set(node_ids)) != len(node_ids)
        or any(
            not node_id.startswith("tests/") or "::" not in node_id or "\x00" in node_id
            for node_id in node_ids
        )
    ):
        raise ValueError(
            "pytest collection node-id roster is missing, duplicated, malformed, "
            "or disagrees with the final summary"
        )
    return node_ids


def _stage_bytes(path: Path, content: bytes) -> Path:
    """Durably stage bytes beside ``path`` without altering the destination."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        return temporary
    except BaseException:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        raise


def _atomic_write_bytes(path: Path, content: bytes) -> None:
    temporary = _stage_bytes(path, content)
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _atomic_write_text(path: Path, content: str) -> None:
    """Replace ``path`` only after a complete same-filesystem write."""
    _atomic_write_bytes(path, content.encode("utf-8"))


def _transactional_write_texts(writes: tuple[tuple[Path, str], ...]) -> None:
    """Install a text projection set or restore its exact prior state."""
    if len({path for path, _content in writes}) != len(writes):
        raise ValueError("transactional projection destinations must be unique")
    snapshots: dict[Path, bytes | None] = {}
    staged: list[tuple[Path, Path]] = []
    install_started = False
    for path, _content in writes:
        if path.exists() and not path.is_file():
            raise ValueError(f"projection destination is not a regular file: {path}")
        snapshots[path] = path.read_bytes() if path.is_file() else None
    try:
        for path, content in writes:
            staged.append((_stage_bytes(path, content.encode("utf-8")), path))
        install_started = True
        for temporary, destination in staged:
            os.replace(temporary, destination)
    except BaseException as exc:
        rollback_errors: list[str] = []
        destinations = (
            reversed([path for path, _content in writes]) if install_started else ()
        )
        for destination in destinations:
            try:
                previous = snapshots[destination]
                if previous is None:
                    destination.unlink(missing_ok=True)
                else:
                    _atomic_write_bytes(destination, previous)
            except BaseException as rollback_exc:
                rollback_errors.append(f"{destination}: {rollback_exc}")
        if rollback_errors:
            raise OSError(
                "manuscript projection rollback failed: " + "; ".join(rollback_errors)
            ) from exc
        raise
    finally:
        for temporary, _destination in staged:
            temporary.unlink(missing_ok=True)


def _count_test_cases(project_root: Path, *, write_cache: bool = True) -> int:
    """Collect and cache in generation mode; validate cached evidence in check mode."""
    root = Path(os.path.abspath(project_root))
    cache = _safe_project_path(
        root,
        root / "output" / ".cache" / "tests_collected.json",
        label="test collection cache",
    )
    inputs = _test_collection_input_paths(root)
    tests_root = root / "tests"
    tests = [
        path
        for path in inputs
        if path.name.startswith("test_")
        and path.suffix == ".py"
        and path.is_relative_to(tests_root)
    ]
    identity = _collection_runtime_identity()
    fingerprint = _test_collection_fingerprint(root, identity=identity)
    if cache.is_file() and tests:
        try:
            payload = json.loads(cache.read_text(encoding="utf-8"))
            collected = payload.get("collected")
            node_ids = payload.get("node_ids")
            if (
                payload.get("schema_version") == _TEST_COLLECTION_CACHE_SCHEMA_VERSION
                and payload.get("input_sha256") == fingerprint
                and payload.get("collection_identity") == identity
                and payload.get("test_files") == len(tests)
                and type(collected) is int
                and collected > 0
                and isinstance(node_ids, list)
                and all(isinstance(node_id, str) for node_id in node_ids)
                and len(node_ids) == collected
                and len(set(node_ids)) == collected
                and all(
                    node_id.startswith("tests/")
                    and "::" in node_id
                    and "\x00" not in node_id
                    for node_id in node_ids
                )
            ):
                return collected
        except (OSError, ValueError, TypeError):
            pass
    if not write_cache:
        state = "stale or invalid" if cache.exists() else "missing"
        raise ValueError(
            f"test collection cache is {state}; run manuscript generation first"
        )
    try:
        with tempfile.TemporaryDirectory(prefix="fep-lean-pytest-collection-") as raw:
            temporary_root = Path(raw)
            cache_dir = temporary_root / "cache"
            home_dir = temporary_root / "home"
            cache_dir.mkdir()
            home_dir.mkdir()
            environment = _pytest_collection_environment(temporary_root)
            command = _pytest_collection_command(cache_dir)
            proc = subprocess.run(
                command,
                cwd=root,
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
                env=environment,
            )
    except subprocess.TimeoutExpired as exc:
        raise ValueError("pytest collection timed out after 120 seconds") from exc
    except (OSError, subprocess.SubprocessError) as exc:
        raise ValueError(f"pytest collection could not run: {exc}") from exc
    if proc.returncode != 0:
        raise ValueError(f"pytest collection failed with exit code {proc.returncode}")
    if proc.stderr.strip():
        raw_excerpt = " ".join(proc.stderr.split())[-400:]
        excerpt = raw_excerpt.encode("unicode_escape").decode("ascii") or "<empty>"
        raise ValueError(
            f"pytest collection wrote unexpected stderr; output tail: {excerpt}"
        )
    node_ids = _parse_pytest_collection_stdout(proc.stdout)
    count = len(node_ids)
    post_identity = _collection_runtime_identity()
    post_fingerprint = _test_collection_fingerprint(root, identity=post_identity)
    if post_identity != identity or post_fingerprint != fingerprint:
        raise ValueError("test collection inputs or runtime changed during collection")
    if write_cache:
        _atomic_write_text(
            cache,
            json.dumps(
                {
                    "schema_version": _TEST_COLLECTION_CACHE_SCHEMA_VERSION,
                    "collected": count,
                    "collection_identity": identity,
                    "input_sha256": fingerprint,
                    "node_ids": list(node_ids),
                    "test_files": len(tests),
                },
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n",
        )
    return count


_SMALL_NUMBER_WORDS = {
    0: "Zero",
    1: "One",
    2: "Two",
    3: "Three",
    4: "Four",
    5: "Five",
    6: "Six",
    7: "Seven",
    8: "Eight",
    9: "Nine",
    10: "Ten",
    11: "Eleven",
    12: "Twelve",
    13: "Thirteen",
    14: "Fourteen",
    15: "Fifteen",
    16: "Sixteen",
    17: "Seventeen",
    18: "Eighteen",
    19: "Nineteen",
    20: "Twenty",
}


def _rate_text(clean: int, total: int) -> str:
    if total <= 0:
        return "not verified"
    return f"{clean}/{total} ({100 * clean / total:.1f}%)"


def build_manuscript_vars(
    catalogue: FEPTopicCatalogue,
    project_root: Path,
    *,
    output_root: Path | None = None,
    cache_test_count: bool = True,
) -> dict[str, Any]:
    summary = catalogue.summary()
    topics: dict[str, dict[str, Any]] = {}
    icons = {"real": "✅", "partial": "◐", "aspirational": "○"}
    for topic in catalogue.topics:
        topics[topic.id] = {
            "title": topic.title,
            "area": topic.area,
            "maturity": topic.mathlib_status,
            "maturity_icon": icons.get(topic.mathlib_status, "?"),
            "mathlib_status": topic.mathlib_status,
            "primary_theorem": topic.primary_theorem,
            "semantic_disposition": topic.semantic_disposition,
            "assumption_review": topic.assumption_review,
            "non_vacuity": topic.non_vacuity,
            "acceptance_probe": topic.acceptance_probe,
            "lean_chars": topic.lean_chars,
            "nl_statement": topic.nl,
            "lean_sketch": topic.lean_sketch,
            "latex_equations": list(topic.latex_equations),
        }
    root = Path(project_root)
    evidence_root = Path(output_root) if output_root is not None else root / "output"
    native_receipt = evidence_root / "native-verification.json"
    verify = _verify_block_from_native_receipt(native_receipt, root)
    manifest = _get_latest_verification_manifest(root, output_root)
    if not verify["claim_ready"] and manifest is not None:
        verify = _verify_block_from_manifest(manifest)
        verify["claim_ready"] = True
    summary_path = manifest.parent / "summary.json" if manifest else None
    clean_topic_ids = set(verify.pop("clean_topic_ids", []))
    area_counts = summary["areas"]
    area_vars = {area: {"count": count} for area, count in area_counts.items()}
    if verify["claim_ready"]:
        compile_rate = {
            "total": _rate_text(len(clean_topic_ids), len(catalogue.topics)),
            "by_area": {
                area: _rate_text(
                    sum(
                        topic.id in clean_topic_ids
                        for topic in catalogue.topics
                        if topic.area == area
                    ),
                    count,
                )
                for area, count in area_counts.items()
            },
        }
    else:
        compile_rate = {
            "total": "not verified",
            "by_area": {area: "not verified" for area in area_counts},
        }
    combined_info_bayes = area_counts.get("InfoGeometry", 0) + area_counts.get(
        "BayesianMechanics", 0
    )
    coverage = build_formalism_coverage(root)
    relation_counts = {
        kind.value: int(coverage["relation_counts"].get(kind.value, 0))
        for kind in EdgeKind
    }
    capability_status_counts = {
        status: int(coverage["capability_status_counts"].get(status, 0))
        for status in ("satisfied", "partial", "open")
    }
    test_count = (
        _count_test_cases(project_root)
        if cache_test_count
        else _count_test_cases(project_root, write_cache=False)
    )
    publication_author = load_publication_author(root)
    graphical_abstract = load_graphical_abstract(root)
    source_stamp = _source_stamp_vars(project_root)
    repository_url = load_repository_url(root)
    return {
        **summary,
        "areas": area_vars,
        "total_areas": len(summary["areas"]),
        "topic_ids": [topic.id for topic in catalogue.topics],
        "topics": topics,
        "combined_info_bayes_count": combined_info_bayes,
        "combined_info_bayes_count_caps": _SMALL_NUMBER_WORDS.get(
            combined_info_bayes, str(combined_info_bayes)
        ),
        "formalism": {
            "metrics": coverage["metrics"],
            "relation_counts": relation_counts,
            "capability_status_counts": capability_status_counts,
        },
        "compile_rate": compile_rate,
        **_read_toolchain_vars(project_root),
        "source": source_stamp,
        "verify": verify,
        "full": {
            "claim_ready": manifest is not None,
            "report_root": str(manifest.parent) if manifest is not None else "",
        },
        "hermes": _hermes_block_from_summary(summary_path),
        "tests": {"collected": test_count},
        "publication": {
            "author": publication_author.manuscript_variables(),
            "graphical_abstract": graphical_abstract.manuscript_variables(),
            "repository_url": repository_url,
        },
    }


def _dump_manuscript_vars(variables: dict[str, Any]) -> str:
    return yaml.safe_dump(
        variables,
        sort_keys=False,
        allow_unicode=True,
    )


def _mapping_shape(value: Any) -> Any:
    """Return a value-independent schema for run-bound projection blocks."""
    if isinstance(value, dict):
        return {key: _mapping_shape(item) for key, item in value.items()}
    if isinstance(value, list):
        return ["item"]
    return "value"


def _stable_manuscript_vars(variables: dict[str, Any]) -> dict[str, Any]:
    """Remove local receipt/provider values while retaining canonical data."""
    return {
        key: value
        for key, value in variables.items()
        if key not in _RUN_BOUND_MANUSCRIPT_KEYS
    }


def manuscript_projection_drift(
    project_root: Path,
    catalogue: FEPTopicCatalogue | None = None,
    *,
    output_root: Path | None = None,
    expected_variables: dict[str, Any] | None = None,
) -> tuple[Path, ...]:
    """Return stale generated manuscript projections without trusting run-local data.

    Topic, formalism, toolchain, and test-census values must match canonical
    sources exactly. Receipt and provider values are intentionally local, so
    their values are excluded while their typed mapping shapes remain pinned.
    """
    root = Path(project_root)
    cat = catalogue or FEPTopicCatalogue.from_yaml(root / "config" / "topics.yaml")
    expected_vars = (
        expected_variables
        if expected_variables is not None
        else build_manuscript_vars(cat, root, output_root=output_root)
    )
    vars_path = root / "manuscript" / "manuscript_vars.yaml"
    appendix_path = root / "manuscript" / UNIFIED_FORMALISM_CATALOGUE_FILENAME
    drift: list[Path] = []

    try:
        actual_vars = yaml.safe_load(vars_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        actual_vars = None
    if not isinstance(actual_vars, dict):
        drift.append(vars_path)
    else:
        stable_matches = _stable_manuscript_vars(
            actual_vars
        ) == _stable_manuscript_vars(expected_vars)
        top_level_schema_matches = set(actual_vars) == set(expected_vars)
        run_bound_shapes_match = all(
            _mapping_shape(actual_vars.get(key))
            == _mapping_shape(expected_vars.get(key))
            for key in _RUN_BOUND_MANUSCRIPT_KEYS
        )
        if not (stable_matches and top_level_schema_matches and run_bound_shapes_match):
            drift.append(vars_path)

    expected_appendix = build_unified_formalism_appendix_markdown(cat, root)
    try:
        appendix_matches = (
            appendix_path.read_text(encoding="utf-8") == expected_appendix
        )
    except OSError:
        appendix_matches = False
    if not appendix_matches:
        drift.append(appendix_path)
    return tuple(drift)


def build_lean_catalogue_markdown(catalogue: FEPTopicCatalogue) -> str:
    lines = [
        "# Appendix B: Full Lean Catalogue {#sec:appendix_b_full_topic_lean_catalogue}",
        "",
    ]
    last_topic_id = catalogue.topics[-1].id
    for topic in catalogue.topics:
        if topic.id == last_topic_id:
            lines.extend([r"\newpage", ""])
        lines.extend(
            [
                f"## {topic.id} — {topic.title} {{#sec:catalogue-{topic.id}}}",
                "",
                topic.nl.strip(),
                "",
                "### Lean sketch",
                "",
                "```lean",
                topic.lean_sketch.rstrip(),
                "```",
                "",
                "### Typeset statement signatures",
                "",
            ]
        )
        for equation in topic.latex_equations:
            lines.extend(["$$", equation, "$$", ""])
    return "\n".join(lines).rstrip() + "\n"


def build_typeset_equations_markdown(
    catalogue: FEPTopicCatalogue, project_root: Path | None = None
) -> str:
    lines = [
        r"\newpage",
        "",
        "# Appendix C: Typeset Equations {#sec:appendix_c_latex_equations}",
        "",
    ]
    last_topic_id = catalogue.topics[-1].id
    for topic in catalogue.topics:
        if topic.id == last_topic_id:
            lines.extend([r"\newpage", ""])
        lines.extend(
            [
                f"## {topic.id} — {topic.title} {{#sec:eqs-{topic.id}}}",
                "",
            ]
        )
        for index, equation in enumerate(topic.latex_equations, 1):
            # pandoc-crossref only numbers the ``$$ ... $$ {#eq:x}`` form. A
            # ``\label`` inside ``$$`` renders as an unnumbered display and is
            # invisible to the filter, so every reference to it would dangle.
            lines.extend(["$$", equation, f"$$ {{#eq:{topic.id}-{index}}}", ""])
    return "\n".join(lines).rstrip() + "\n"


def build_unified_formalism_appendix_markdown(
    catalogue: FEPTopicCatalogue, project_root: Path | None = None
) -> str:
    return (
        "<!-- AUTO-GENERATED by src/fep_lean/output/manuscript.py -->\n\n"
        + build_lean_catalogue_markdown(catalogue)
        + "\n"
        + build_typeset_equations_markdown(catalogue, project_root)
    )


def write_manuscript_vars(
    project_root: Path,
    catalogue: FEPTopicCatalogue | None = None,
    *,
    output_root: Path | None = None,
) -> Path:
    """Transactionally write the variable projection and its paired appendix."""
    root = Path(os.path.abspath(project_root))
    cat = catalogue or FEPTopicCatalogue.from_yaml(root / "config" / "topics.yaml")
    out = _safe_project_path(
        root,
        root / "manuscript" / "manuscript_vars.yaml",
        label="manuscript projection",
    )
    appendix = _safe_project_path(
        root,
        root / "manuscript" / UNIFIED_FORMALISM_CATALOGUE_FILENAME,
        label="manuscript projection",
    )
    variables = _dump_manuscript_vars(
        build_manuscript_vars(cat, root, output_root=output_root)
    )
    appendix_markdown = build_unified_formalism_appendix_markdown(cat, root)
    _transactional_write_texts(
        (
            (out, variables),
            (appendix, appendix_markdown),
        )
    )
    return out


def write_unified_formalism_appendix_markdown(
    project_root: Path, catalogue: FEPTopicCatalogue | None = None
) -> Path:
    """Atomically refresh only the generated unified-formalism appendix."""
    root = Path(os.path.abspath(project_root))
    cat = catalogue or FEPTopicCatalogue.from_yaml(root / "config" / "topics.yaml")
    out = _safe_project_path(
        root,
        root / "manuscript" / UNIFIED_FORMALISM_CATALOGUE_FILENAME,
        label="manuscript projection",
    )
    _atomic_write_text(out, build_unified_formalism_appendix_markdown(cat, root))
    return out
