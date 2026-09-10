"""Deterministic, fail-closed publication evidence bundles.

The archive is a transport for already validated evidence, never a new proof
plane.  Every member is a regular file with normalized metadata; the manifest
and checksum table describe the exact payload without a recursive self-hash.
"""

from __future__ import annotations

import gzip
import hashlib
import importlib.metadata
import io
import json
import math
import os
import re
import shlex
import shutil
import struct
import subprocess
import sys
import tarfile
import tempfile
import xml.etree.ElementTree as ET
import zlib
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

from fep_lean.catalogue.coverage import formalism_coverage_drift
from fep_lean.catalogue.relations import EdgeKind
from fep_lean.catalogue.theorem_maturity_projection import (
    render_markdown,
    validate_audit,
)
from fep_lean.catalogue.topics import FEPTopicCatalogue
from fep_lean.output.browser_capture import (
    BROWSER_ASSET_ROOT,
    BROWSER_RECEIPT,
    BrowserCaptureError,
    canonical_browser_capture_provenance,
    canonical_browser_observations,
    canonical_browser_render_configuration,
    replay_browser_acceptance,
    resolve_browser_executable,
)
from fep_lean.output.browser_capture import (
    CANONICAL_BROWSER_PROJECTIONS as _CANONICAL_BROWSER_PROJECTIONS,
)
from fep_lean.output.browser_capture import (
    CANONICAL_BROWSER_SCREENSHOTS as _CANONICAL_BROWSER_SCREENSHOTS,
)
from fep_lean.output.browser_capture import (
    REQUIRED_BROWSER_INTERACTIONS as _REQUIRED_BROWSER_INTERACTIONS,
)
from fep_lean.output.evidence import validate_native_lean_receipt
from fep_lean.output.formal_kernel_dashboard import formal_kernel_dashboard_drift
from fep_lean.output.formalism_atlas import atlas_projection_drift
from fep_lean.output.formalism_presentation import (
    RELEASE_CAPABILITIES,
    RELEASE_FAMILIES,
    RELEASE_RELATIONS,
    RELEASE_SEAL,
    RELEASE_TOPICS,
    RELEASE_WITNESSES,
    build_formalism_presentation,
)
from fep_lean.output.fsutil import atomic_write_bytes, sha256_bytes
from fep_lean.output.manuscript import (
    collection_runtime_identity,
    manuscript_projection_drift,
    parse_pytest_collection_stdout,
    pytest_collection_command,
    pytest_collection_environment,
)
from fep_lean.output.provenance import (
    config_owner_paths,
    report_config_digest,
    report_owner_errors,
    report_source_digest,
    source_owner_paths,
)
from fep_lean.output.publication_metadata import (
    GraphicalAbstractAsset,
    PublicationMetadataError,
    load_graphical_abstract,
    load_publication_author,
)
from fep_lean.output.rendering import (
    MANUSCRIPT_ASSETS,
    manuscript_source_files,
    render_manuscript,
)
from fep_lean.verification.formalism_audit import (
    validate_formalism_audit_receipt,
)
from fep_lean.verification.numerical_witnesses import (
    NON_PROOF_EVIDENCE,
    evaluate_numerical_witnesses,
)

RELEASE_BUNDLE_SCHEMA_VERSION = 1
MANIFEST_NAME = "MANIFEST.json"
CHECKSUMS_NAME = "SHA256SUMS"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_CHECKSUM_LINE_RE = re.compile(r"^([0-9a-f]{64})  ([^\r\n]+)$")
_PDF_ID_RE = re.compile(rb"/ID\s*\[\s*<([0-9A-Fa-f]{32})>\s*<([0-9A-Fa-f]{32})>\s*\]")
_MARKDOWN_IMAGE_RE = re.compile(r"!\[[^\]\r\n]*\]\(\s*(?:<([^>\r\n]+)>|([^\s)\r\n]+))")
_RESOURCE_MARKUP_RE = re.compile(
    r"<\s*(?:audio|embed|iframe|image|img|link|object|script|source|track|video)\b"
    r"|\burl\s*\(|@import\b",
    re.IGNORECASE,
)
_CANONICAL_LICENSE = "CC-BY-4.0"
_CANONICAL_PUBLICATION_DOI = "10.5281/zenodo.19699233"
_CANONICAL_PUBLICATION_JOURNAL = "Active Inference Journal"
_CANONICAL_REPOSITORY_URL = "https://github.com/ActiveInferenceInstitute/fep_lean"
_CANONICAL_RELEASE_VERSION = "1.1.0"
_CANONICAL_RELEASE_DATE = "2026-08-23"
_MINIMUM_SPDX_SETUPTOOLS_REQUIREMENT = "setuptools>=77.0.3"
_MAX_ARCHIVE_MEMBERS = 20_000
_MAX_MEMBER_BYTES = 512 * 1024 * 1024
_MAX_ARCHIVE_BYTES = 1024 * 1024 * 1024
_MAX_TOTAL_MEMBER_BYTES = 2 * 1024 * 1024 * 1024
_PANDOC_TIMEOUT_SECONDS = 600
_PDF_TIMEOUT_SECONDS = 1_200
_PYTHON_ACCEPTANCE_TIMEOUT_SECONDS = 7_200

PUBLICATION_HTML = Path("output/manuscript/fep-lean-manuscript.html")
PUBLICATION_PDF = Path("output/manuscript/fep-lean-manuscript.pdf")
RENDERER_PROVENANCE = Path("output/manuscript/renderer-provenance.json")
NUMERICAL_RECEIPT = Path("output/numerical-witnesses.json")
PYTEST_RECEIPT = Path("output/pytest.xml")
PYTHON_COVERAGE_RECEIPT = Path("output/coverage.xml")
PYTHON_ACCEPTANCE_RECEIPT = Path("output/python-acceptance.json")
_PYTHON_ACCEPTANCE_EXPLICIT_PLUGINS = (
    "pytest_cov.plugin",
    "pytest_httpserver.pytest_plugin",
    "pytest_timeout",
)
_PYTHON_ACCEPTANCE_DISTRIBUTIONS = (
    "coverage",
    "pluggy",
    "pytest",
    "pytest-cov",
    "pytest-httpserver",
    "pytest-timeout",
)
_PYTHON_ACCEPTANCE_ARGUMENTS: tuple[str, ...] = (
    "tests",
    "-q",
    "--color=no",
    "--strict-markers",
    "--tb=short",
    "--cov=src",
    "--cov-fail-under=89",
    "--cov-report=term",
    "--cov-report=xml:output/coverage.xml",
    "--junitxml=output/pytest.xml",
    "-o",
    "junit_family=xunit2",
    "-o",
    "addopts=",
)

_MANUSCRIPT_FIGURE_REFERENCES: Mapping[str, str] = {
    "../output/figures/status_distribution.png": (
        "output/figures/status_distribution.png"
    ),
}
_REQUIRED_STATIC_MEMBERS: tuple[tuple[str, str], ...] = (
    (".aii/config.yaml", "institute_metadata"),
    ("README.md", "project_documentation"),
    ("LICENSE", "legal_metadata"),
    ("CITATION.cff", "citation_metadata"),
    ("manuscript/config.yaml", "manuscript_metadata"),
    ("manuscript/assets/graphical-abstract.png", "graphical_abstract"),
    ("manuscript/manuscript_vars.yaml", "manuscript_metadata"),
    ("manuscript/preamble.md", "manuscript_source"),
    ("manuscript/references.bib", "bibliography"),
    (
        "manuscript/09z_unified_formalism_catalogue.md",
        "generated_formalism_appendix",
    ),
    ("docs/formalism-coverage.json", "formalism_coverage"),
    ("docs/formalism-coverage.md", "formalism_coverage"),
    ("docs/theorem-maturity-audit.md", "theorem_maturity"),
    ("docs/formalism-atlas.svg", "formalism_visualization"),
    ("docs/formalism-atlas.html", "formalism_visualization"),
    ("docs/formal-kernel-dashboard.svg", "numerical_visualization"),
    ("docs/formal-kernel-dashboard.html", "numerical_visualization"),
    ("output/native-verification.json", "native_lean_receipt"),
    ("output/formalism-audit.json", "declaration_axiom_receipt"),
    (PYTEST_RECEIPT.as_posix(), "python_test_receipt"),
    (PYTHON_COVERAGE_RECEIPT.as_posix(), "python_coverage_receipt"),
    (BROWSER_RECEIPT.as_posix(), "browser_receipt"),
    (PUBLICATION_HTML.as_posix(), "rendered_manuscript"),
    (
        "output/manuscript/assets/graphical-abstract.png",
        "rendered_manuscript_asset",
    ),
    (RENDERER_PROVENANCE.as_posix(), "renderer_provenance"),
)
_PROVIDER_MEMBER_PREFIXES = (
    "output/reports/",
    "provider/",
    "external-full-mode/",
)
_STATIC_REQUIRED_BUNDLE_PATHS = frozenset(
    {
        *(path for path, _evidence_class in _REQUIRED_STATIC_MEMBERS),
        NUMERICAL_RECEIPT.as_posix(),
        PYTHON_ACCEPTANCE_RECEIPT.as_posix(),
        "lean/FepSketches/fep_all.lean",
    }
)


@dataclass(frozen=True)
class ReleaseBundleValidation:
    """Independent validation result for one release archive."""

    valid: bool
    source_bound: bool
    claim_ready: bool
    errors: tuple[str, ...]
    archive_sha256: str
    member_count: int
    manifest: dict[str, Any] | None


class ReleaseBundleError(ValueError):
    """Raised before replacing an archive when publication inputs are invalid."""


@dataclass(frozen=True)
class PublicationManuscript:
    """Fresh deterministic manuscript outputs and renderer provenance."""

    html: bytes
    pdf: bytes | None
    provenance: bytes
    source_digest: str


@dataclass(frozen=True)
class _BundleMember:
    path: str
    data: bytes
    evidence_class: str


def _sha256(data: bytes) -> str:
    """Deprecated alias; shared implementation lives in ``output.fsutil``."""
    return sha256_bytes(data)


def _canonical_json(payload: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(
            dict(payload),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        + "\n"
    ).encode("utf-8")


def _source_date_epoch(value: int | None = None) -> int:
    raw: str | int = (
        os.environ.get("SOURCE_DATE_EPOCH", "0") if value is None else value
    )
    if isinstance(raw, bool):
        raise ReleaseBundleError("SOURCE_DATE_EPOCH must be an integer")
    try:
        epoch = int(raw)
    except (TypeError, ValueError) as exc:
        raise ReleaseBundleError("SOURCE_DATE_EPOCH must be an integer") from exc
    if epoch < 0 or epoch > 0xFFFFFFFF:
        raise ReleaseBundleError("SOURCE_DATE_EPOCH must be between 0 and 4294967295")
    return epoch


def _atomic_bytes(path: Path, data: bytes) -> None:
    """Deprecated alias; shared implementation lives in ``output.fsutil``."""
    atomic_write_bytes(path, data)


def _relative_file_bytes(project_root: Path, relative: str) -> bytes:
    root = Path(project_root).resolve()
    if not _safe_member_name(relative):
        raise ReleaseBundleError(f"required file path is unsafe: {relative}")
    path = root / relative
    if path.is_symlink() or not path.is_file():
        raise ReleaseBundleError(f"required regular file is missing: {relative}")
    resolved = path.resolve()
    if not resolved.is_relative_to(root):
        raise ReleaseBundleError(f"required file escapes the project root: {relative}")
    parent = path.parent
    while parent != root:
        if parent.is_symlink():
            raise ReleaseBundleError(f"required file traverses a symlink: {relative}")
        parent = parent.parent
    return path.read_bytes()


def _digest_named_bytes(records: Sequence[tuple[str, bytes]]) -> str:
    digest = hashlib.sha256()
    for name, data in sorted(records):
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(data)
        digest.update(b"\0")
    return digest.hexdigest()


def _tool_identity(executable: str, *, timeout: int = 30) -> dict[str, str]:
    resolved = Path(executable).resolve()
    first_line: list[str] = []
    for version_flag in ("--version", "-v"):
        try:
            completed = subprocess.run(
                [executable, version_flag],
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise ReleaseBundleError(
                f"cannot identify renderer {executable}: {exc}"
            ) from exc
        first_line = (completed.stdout or completed.stderr).splitlines()
        if completed.returncode == 0 and first_line:
            break
    else:
        raise ReleaseBundleError(f"cannot identify renderer {executable}")
    return {
        "name": Path(executable).name,
        "version": first_line[0].strip(),
        "binary_sha256": _sha256(resolved.read_bytes()),
    }


def _manuscript_inputs(project_root: Path) -> tuple[Path, ...]:
    root = Path(project_root)
    rendered_root = root / "output" / "manuscript"
    rendered = tuple(
        rendered_root / source.name
        for source in manuscript_source_files(root / "manuscript")
    )
    return (*rendered, root / "manuscript" / "09z_unified_formalism_catalogue.md")


def _manuscript_source_records(
    project_root: Path,
) -> tuple[tuple[str, bytes], ...]:
    """Capture authored manuscript inputs through the canonical file boundary."""
    root = Path(project_root).resolve()
    records: list[tuple[str, bytes]] = []
    for path in manuscript_source_files(root / "manuscript"):
        relative = path.relative_to(root).as_posix()
        try:
            data = _relative_file_bytes(root, relative)
        except ReleaseBundleError as exc:
            raise ReleaseBundleError(
                f"manuscript source is not a canonical regular file: {relative}"
            ) from exc
        records.append((relative, data))
    if not records:
        raise ReleaseBundleError("canonical manuscript source tree is empty")
    return tuple(records)


def _required_graphical_abstract(project_root: Path) -> GraphicalAbstractAsset:
    """Return the cover only when its complete publication contract validates."""
    root = Path(project_root).resolve()
    try:
        return load_graphical_abstract(root)
    except PublicationMetadataError as exc:
        raise ReleaseBundleError(str(exc)) from exc


def _publication_resource_records(
    project_root: Path,
) -> tuple[tuple[str, bytes], ...]:
    """Capture the narrow roster of local files embedded by the manuscript."""
    root = Path(project_root).resolve()
    source_records = _manuscript_source_records(root)
    graphical_abstract = _required_graphical_abstract(root)
    rendered_records: list[tuple[str, bytes]] = []
    for name, _data in source_records:
        relative = f"output/manuscript/{Path(name).name}"
        path = root / relative
        if path.exists() or path.is_symlink():
            rendered_records.append((relative, _relative_file_bytes(root, relative)))
    allowed_references = (
        set(MANUSCRIPT_ASSETS)
        | {
            destination.as_posix()
            for _source, destination in MANUSCRIPT_ASSETS.values()
        }
        | set(_MANUSCRIPT_FIGURE_REFERENCES)
    )
    graphical_abstract_placeholder = "{{publication.graphical_abstract.render_path}}"
    allowed_references.update(
        {graphical_abstract_placeholder, graphical_abstract.render_path}
    )
    observed_references: set[str] = set()
    for _name, data in (*source_records, *rendered_records):
        try:
            text = data.decode("utf-8")
        except UnicodeError as exc:
            raise ReleaseBundleError("manuscript source is not UTF-8") from exc
        matches = tuple(_MARKDOWN_IMAGE_RE.finditer(text))
        matched_starts = {match.start() for match in matches}
        if any(
            match.start() not in matched_starts for match in re.finditer(r"!\[", text)
        ):
            raise ReleaseBundleError("manuscript image syntax is not release-owned")
        if _RESOURCE_MARKUP_RE.search(text) is not None:
            raise ReleaseBundleError(
                "manuscript contains unsupported resource-bearing markup"
            )
        for match in matches:
            reference = match.group(1) or match.group(2)
            if reference not in allowed_references:
                raise ReleaseBundleError(
                    f"manuscript image reference is not release-owned: {reference}"
                )
            observed_references.add(reference)
    if not {
        graphical_abstract_placeholder,
        graphical_abstract.render_path,
    }.issubset(observed_references):
        raise ReleaseBundleError(
            "configured graphical abstract is not consumed by source and rendered front matter"
        )
    referenced = {
        relative
        for reference, relative in _MANUSCRIPT_FIGURE_REFERENCES.items()
        if reference in observed_references
    }
    for reference, (
        source_relative,
        destination_relative,
    ) in MANUSCRIPT_ASSETS.items():
        if (
            reference in observed_references
            or destination_relative.as_posix() in observed_references
        ):
            _relative_file_bytes(root, source_relative.as_posix())
    records = [
        (relative, _relative_file_bytes(root, relative))
        for relative in sorted(referenced)
    ]
    rendered_path = (
        Path("output/manuscript") / graphical_abstract.render_path
    ).as_posix()
    rendered_data = _relative_file_bytes(root, rendered_path)
    if rendered_data != graphical_abstract.data:
        raise ReleaseBundleError("rendered graphical abstract asset is stale")
    records.extend(
        (
            (graphical_abstract.source_path, graphical_abstract.data),
            (rendered_path, rendered_data),
        )
    )
    return tuple(records)


def _canonical_renderer_input_records(
    project_root: Path,
    resource_records: Sequence[tuple[str, bytes]],
) -> tuple[tuple[str, bytes], ...]:
    """Snapshot every local Pandoc input through one containment boundary."""
    root = Path(project_root).resolve()
    relative_names = {
        path.relative_to(root).as_posix()
        for path in (
            *_manuscript_inputs(root),
            root / "manuscript" / "references.bib",
            root / "manuscript" / "config.yaml",
            root / "manuscript" / "preamble.md",
        )
    }
    for _source, destination in MANUSCRIPT_ASSETS.values():
        relative = (Path("output/manuscript") / destination).as_posix()
        candidate = root / relative
        if candidate.exists() or candidate.is_symlink():
            relative_names.add(relative)
    records = {
        relative: _relative_file_bytes(root, relative)
        for relative in sorted(relative_names)
    }
    for relative, data in resource_records:
        existing = records.setdefault(relative, data)
        if existing != data:
            raise ReleaseBundleError(
                f"manuscript renderer input changed while captured: {relative}"
            )
    return tuple(sorted(records.items()))


def _controlled_renderer_path(
    command: Sequence[str], *, auxiliary_executables: Sequence[str] = ()
) -> str:
    directories: list[str] = []
    executables = [command[0]]
    executables.extend(
        argument.removeprefix("--pdf-engine=")
        for argument in command
        if argument.startswith("--pdf-engine=")
    )
    executables.extend(auxiliary_executables)
    for executable in executables:
        candidate = Path(executable)
        if candidate.is_absolute():
            directory = str(candidate.resolve().parent)
            if directory not in directories:
                directories.append(directory)
    for directory in os.defpath.split(os.pathsep):
        if directory and directory not in directories:
            directories.append(directory)
    return os.pathsep.join(directories)


def _renderer_environment(
    epoch: int,
    environment_root: Path,
    command: Sequence[str],
    *,
    auxiliary_executables: Sequence[str] = (),
) -> dict[str, str]:
    """Return the complete, controlled environment seen by local renderers."""
    root = Path(environment_root)
    home = root / "home"
    cache = root / "cache"
    texmf_var = root / "texmf-var"
    texmf_config = root / "texmf-config"
    for path in (home, cache, texmf_var, texmf_config):
        path.mkdir(parents=True, exist_ok=True)
    return {
        "PATH": _controlled_renderer_path(
            command, auxiliary_executables=auxiliary_executables
        ),
        "HOME": str(home),
        "XDG_CACHE_HOME": str(cache),
        "TEXMFVAR": str(texmf_var),
        "TEXMFCONFIG": str(texmf_config),
        "SOURCE_DATE_EPOCH": str(epoch),
        "FORCE_SOURCE_DATE": "1",
        "TZ": "UTC",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
    }


def _normalized_renderer_environment(epoch: int) -> dict[str, str]:
    """Describe the effective renderer environment without temporary paths."""
    return {
        "PATH": "<CONTROLLED_RENDERER_PATH>",
        "HOME": "<RENDER_TEMP>/home",
        "XDG_CACHE_HOME": "<RENDER_TEMP>/cache",
        "TEXMFVAR": "<RENDER_TEMP>/texmf-var",
        "TEXMFCONFIG": "<RENDER_TEMP>/texmf-config",
        "SOURCE_DATE_EPOCH": str(epoch),
        "FORCE_SOURCE_DATE": "1",
        "TZ": "UTC",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
    }


def _latex_preamble(project_root: Path) -> bytes:
    """Extract the single fenced LaTeX preamble used by the PDF renderer."""
    raw = _relative_file_bytes(project_root, "manuscript/preamble.md")
    try:
        text = raw.decode("utf-8")
    except UnicodeError as exc:
        raise ReleaseBundleError("manuscript preamble is not UTF-8") from exc
    lines = text.splitlines()
    if len(lines) < 3 or lines[0].strip() != "```latex" or lines[-1].strip() != "```":
        raise ReleaseBundleError("manuscript preamble must be one fenced latex block")
    body = "\n".join(lines[1:-1]).strip()
    if not body:
        raise ReleaseBundleError("manuscript preamble is empty")
    return (body + "\n").encode("utf-8")


def _pandoc_base_command(project_root: Path, pandoc: str) -> list[str]:
    root = Path(project_root).resolve()
    try:
        config_text = _relative_file_bytes(root, "manuscript/config.yaml").decode(
            "utf-8"
        )
        config = yaml.safe_load(config_text)
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        raise ReleaseBundleError("manuscript/config.yaml is invalid") from exc
    if not isinstance(config, dict) or not isinstance(config.get("paper"), dict):
        raise ReleaseBundleError("manuscript/config.yaml lacks paper metadata")
    paper = config["paper"]
    title = paper.get("title")
    date = paper.get("date")
    if not isinstance(title, str) or not title.strip():
        raise ReleaseBundleError("manuscript title is missing")
    if not isinstance(date, str) or not date.strip():
        raise ReleaseBundleError("manuscript date is missing")
    command = [
        pandoc,
        "--standalone",
        "--citeproc",
        "--toc",
        "--number-sections",
        f"--metadata=title:{title}",
        f"--metadata=date:{date}",
        "--bibliography=manuscript/references.bib",
        "--resource-path=output/manuscript:output/manuscript/assets:manuscript:docs",
    ]
    command.extend(
        path.relative_to(root).as_posix() for path in _manuscript_inputs(root)
    )
    return command


def _run_renderer(
    command: Sequence[str],
    *,
    project_root: Path,
    environment_root: Path,
    epoch: int,
    timeout: int,
    auxiliary_executables: Sequence[str] = (),
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            list(command),
            cwd=project_root,
            env=_renderer_environment(
                epoch,
                environment_root,
                command,
                auxiliary_executables=auxiliary_executables,
            ),
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise ReleaseBundleError(
            f"renderer exceeded its {timeout}-second deterministic budget"
        ) from exc
    except OSError as exc:
        raise ReleaseBundleError(f"cannot execute manuscript renderer: {exc}") from exc


def _canonical_pdf_identifier(data: bytes) -> bytes:
    """Replace one random PDF trailer ID with a content-derived stable ID."""
    matches = tuple(_PDF_ID_RE.finditer(data))
    if len(matches) != 1:
        raise ReleaseBundleError(
            "normalized PDF must contain exactly one two-part trailer ID"
        )
    match = matches[0]
    zeroed = bytearray(data)
    for group in (1, 2):
        start, end = match.span(group)
        zeroed[start:end] = b"0" * (end - start)
    identifier = hashlib.sha256(zeroed).hexdigest()[:32].upper().encode("ascii")
    canonical = bytearray(data)
    for group in (1, 2):
        start, end = match.span(group)
        canonical[start:end] = identifier
    return bytes(canonical)


def _render_twice(
    base_command: Sequence[str],
    *,
    project_root: Path,
    epoch: int,
    suffix: str,
    extra_args: Sequence[str],
    include_header: bytes | None = None,
    timeout: int,
    auxiliary_executables: Sequence[str] = (),
    pdf_normalizer: str | None = None,
    pdf_engine: str | None = None,
) -> tuple[bytes | None, str]:
    outputs: list[bytes] = []
    with tempfile.TemporaryDirectory(prefix="fep-lean-render-") as raw_directory:
        directory = Path(raw_directory)
        for index in range(2):
            run_root = directory / f"environment-{index}"
            run_root.mkdir()
            output = directory / f"render-{index}{suffix}"
            command = [*base_command, *extra_args]
            if pdf_engine is not None:
                wrapper_directory = run_root / "bin"
                wrapper_directory.mkdir()
                wrapper = wrapper_directory / "xelatex"
                quoted_engine = shlex.quote(pdf_engine)
                wrapper.write_text(
                    "#!/bin/sh\n"
                    "set -eu\n"
                    f'{quoted_engine} "$@"\n'
                    f'exec {quoted_engine} "$@"\n',
                    encoding="utf-8",
                )
                wrapper.chmod(0o755)
                command.append(f"--pdf-engine={wrapper}")
            if include_header is not None:
                header = run_root / "preamble.tex"
                header.write_bytes(include_header)
                command.append(f"--include-in-header={header}")
            completed = _run_renderer(
                [*command, f"--output={output}"],
                project_root=project_root,
                environment_root=run_root,
                epoch=epoch,
                timeout=timeout,
                auxiliary_executables=auxiliary_executables,
            )
            if completed.returncode != 0 or not output.is_file():
                return None, f"renderer_failed_returncode_{completed.returncode}"
            rendered_bytes = output.read_bytes()
            if pdf_normalizer is not None:
                normalized = run_root / "normalized.pdf"
                normalizer_result = _run_renderer(
                    [pdf_normalizer, "clean", str(output), str(normalized)],
                    project_root=project_root,
                    environment_root=run_root,
                    epoch=epoch,
                    timeout=timeout,
                    auxiliary_executables=auxiliary_executables,
                )
                if normalizer_result.returncode != 0 or not normalized.is_file():
                    return (
                        None,
                        f"pdf_normalizer_failed_returncode_{normalizer_result.returncode}",
                    )
                try:
                    rendered_bytes = _canonical_pdf_identifier(normalized.read_bytes())
                except ReleaseBundleError:
                    return None, "pdf_identifier_not_canonicalizable"
            outputs.append(rendered_bytes)
    if outputs[0] != outputs[1]:
        return None, "renderer_output_not_reproducible"
    return outputs[0], "reproducible"


def _rendered_manuscript_errors(project_root: Path) -> tuple[str, ...]:
    root = Path(project_root)
    destination = root / "output" / "manuscript"
    errors: list[str] = []
    try:
        _publication_resource_records(root)
    except ReleaseBundleError as exc:
        return (str(exc),)
    with tempfile.TemporaryDirectory(prefix="fep-lean-manuscript-check-") as raw:
        expected_root = Path(raw) / "manuscript"
        try:
            render_manuscript(
                root / "manuscript", expected_root, _manuscript_variables(root)
            )
        except (OSError, TypeError, ValueError) as exc:
            return (f"rendered manuscript cannot be reproduced: {exc}",)
        expected_files = tuple(
            sorted(path for path in expected_root.rglob("*") if path.is_file())
        )
        for expected in expected_files:
            relative = expected.relative_to(expected_root)
            actual = destination / relative
            if actual.is_symlink() or not actual.is_file():
                errors.append(f"rendered manuscript member is missing: {relative}")
            else:
                actual_relative = actual.relative_to(root).as_posix()
                try:
                    actual_data = _relative_file_bytes(root, actual_relative)
                except ReleaseBundleError as exc:
                    errors.append(str(exc))
                else:
                    if actual_data != expected.read_bytes():
                        errors.append(
                            f"rendered manuscript member is stale: {relative}"
                        )
        allowed = {path.relative_to(expected_root) for path in expected_files}
        allowed.update(
            {
                Path(PUBLICATION_HTML.name),
                Path(PUBLICATION_PDF.name),
                Path(RENDERER_PROVENANCE.name),
            }
        )
        if destination.is_dir():
            for actual in sorted(
                path for path in destination.rglob("*") if path.is_file()
            ):
                relative = actual.relative_to(destination)
                if relative not in allowed:
                    errors.append(f"unexpected rendered manuscript member: {relative}")
    return tuple(errors)


def _manuscript_variables(project_root: Path) -> dict[str, Any]:
    root = Path(project_root).resolve()
    try:
        raw = _relative_file_bytes(root, "manuscript/manuscript_vars.yaml")
        payload = yaml.safe_load(raw.decode("utf-8"))
    except (ReleaseBundleError, UnicodeDecodeError, yaml.YAMLError) as exc:
        raise ReleaseBundleError(f"cannot read manuscript variables: {exc}") from exc
    if not isinstance(payload, dict):
        raise ReleaseBundleError("manuscript variables must be a mapping")
    return payload


def render_publication_manuscript(
    project_root: Path,
    *,
    source_date_epoch: int | None = None,
) -> PublicationManuscript:
    """Render HTML twice and include PDF only when two local renders agree."""
    root = Path(project_root).resolve()
    epoch = _source_date_epoch(source_date_epoch)
    resource_records = _publication_resource_records(root)
    input_records = _canonical_renderer_input_records(root, resource_records)
    pandoc = shutil.which("pandoc")
    if pandoc is None:
        raise ReleaseBundleError("pandoc is required for the self-contained HTML")
    pandoc_identity = _tool_identity(pandoc)
    base_command = _pandoc_base_command(root, pandoc)
    html, html_status = _render_twice(
        base_command,
        project_root=root,
        epoch=epoch,
        suffix=".html",
        extra_args=("--embed-resources", "--mathml"),
        timeout=_PANDOC_TIMEOUT_SECONDS,
    )
    if html is None:
        raise ReleaseBundleError(f"deterministic HTML rendering failed: {html_status}")
    lowered_html = html.lower()
    if (
        b'src="http://' in lowered_html
        or b'src="https://' in lowered_html
        or b"src='http://" in lowered_html
        or b"src='https://" in lowered_html
        or b"file://" in lowered_html
    ):
        raise ReleaseBundleError("rendered manuscript HTML contains external assets")

    xelatex = shutil.which("xelatex")
    rsvg_convert = shutil.which("rsvg-convert")
    mutool = shutil.which("mutool")
    pdf: bytes | None = None
    pdf_status = "xelatex_unavailable"
    pdf_renderer = _tool_identity(xelatex) if xelatex is not None else None
    rsvg_renderer = _tool_identity(rsvg_convert) if rsvg_convert is not None else None
    mutool_renderer = _tool_identity(mutool) if mutool is not None else None
    if xelatex is not None and mutool is None:
        pdf_status = "mutool_unavailable"
    elif xelatex is not None:
        preamble = _latex_preamble(root)
        pdf, pdf_status = _render_twice(
            base_command,
            project_root=root,
            epoch=epoch,
            suffix=".pdf",
            extra_args=(),
            include_header=preamble,
            timeout=_PDF_TIMEOUT_SECONDS,
            auxiliary_executables=tuple(
                executable
                for executable in (xelatex, rsvg_convert, mutool)
                if executable is not None
            ),
            pdf_normalizer=mutool,
            pdf_engine=xelatex,
        )

    final_resource_records = _publication_resource_records(root)
    if _canonical_renderer_input_records(root, final_resource_records) != input_records:
        raise ReleaseBundleError("manuscript renderer inputs changed during rendering")
    source_digest = _digest_named_bytes(input_records)
    provenance: dict[str, Any] = {
        "schema_version": 1,
        "kind": "deterministic-manuscript-render",
        "source_date_epoch": epoch,
        "source_sha256": source_digest,
        "inputs": [
            {"path": path, "sha256": _sha256(data), "size": len(data)}
            for path, data in sorted(input_records)
        ],
        "html": {
            "current": True,
            "path": PUBLICATION_HTML.as_posix(),
            "sha256": _sha256(html),
            "size": len(html),
            "status": html_status,
        },
        "pdf": {
            "current": pdf is not None,
            "path": PUBLICATION_PDF.as_posix() if pdf is not None else "",
            "sha256": _sha256(pdf) if pdf is not None else "",
            "size": len(pdf) if pdf is not None else 0,
            "status": pdf_status,
        },
        "renderers": {
            "pandoc": pandoc_identity,
            "xelatex": pdf_renderer,
            "rsvg-convert": rsvg_renderer,
            "mutool": mutool_renderer,
        },
        "commands": {
            "html": [
                "pandoc",
                *base_command[1:],
                "--embed-resources",
                "--mathml",
                "--output=<OUTPUT.html>",
            ],
            "pdf": (
                [
                    "pandoc",
                    *base_command[1:],
                    "--pdf-engine=<TWO_PASS_XELATEX_WRAPPER>",
                    "--include-in-header=<RENDER_TEMP>/preamble.tex",
                    "--output=<OUTPUT.pdf>",
                ]
                if pdf_renderer is not None
                else []
            ),
            "pdf_engine_passes": 2 if pdf_renderer is not None else 0,
            "pdf_normalization": (
                [
                    "mutool",
                    "clean",
                    "<OUTPUT.pdf>",
                    "<NORMALIZED.pdf>",
                    "<CANONICAL_CONTENT_DERIVED_TRAILER_ID>",
                ]
                if mutool_renderer is not None
                else []
            ),
        },
        "normalized_environment": _normalized_renderer_environment(epoch),
    }
    return PublicationManuscript(
        html=html,
        pdf=pdf,
        provenance=_canonical_json(provenance),
        source_digest=source_digest,
    )


def write_publication_manuscript(
    project_root: Path,
    *,
    source_date_epoch: int | None = None,
) -> tuple[Path, ...]:
    """Atomically replace the current reproducible manuscript projections."""
    root = Path(project_root).resolve()
    rendered = render_publication_manuscript(root, source_date_epoch=source_date_epoch)
    if rendered.pdf is None and (root / PUBLICATION_PDF).exists():
        raise ReleaseBundleError(
            "a stale PDF exists but the current local renderer is not reproducible"
        )
    desired: dict[Path, bytes] = {PUBLICATION_HTML: rendered.html}
    if rendered.pdf is not None:
        desired[PUBLICATION_PDF] = rendered.pdf
    desired[RENDERER_PROVENANCE] = rendered.provenance
    _replace_publication_set(root, desired)
    return tuple(root / relative for relative in desired)


def _replace_publication_set(project_root: Path, desired: Mapping[Path, bytes]) -> None:
    """Install the complete publication set or restore every prior member."""
    root = Path(project_root).resolve()
    destination_root = root / PUBLICATION_HTML.parent
    if destination_root.is_symlink():
        raise ReleaseBundleError("publication destination directory is a symlink")
    parent = destination_root.parent
    while parent != root:
        if parent.is_symlink():
            raise ReleaseBundleError(
                "publication destination directory traverses a symlink"
            )
        parent = parent.parent
    if destination_root.exists() and not destination_root.is_dir():
        raise ReleaseBundleError("publication destination is not a directory")
    destination_root.mkdir(parents=True, exist_ok=True)
    if not destination_root.resolve().is_relative_to(root):
        raise ReleaseBundleError("publication destination escapes the project root")
    stage = Path(tempfile.mkdtemp(prefix=".publication-set-", dir=destination_root))
    preserve_stage = False
    try:
        new_root = stage / "new"
        backup_root = stage / "backup"
        new_root.mkdir()
        backup_root.mkdir()
        desired_records = tuple(desired.items())
        for relative, data in desired_records:
            if relative.parent != PUBLICATION_HTML.parent:
                raise ReleaseBundleError(
                    f"publication member has an invalid owner directory: {relative}"
                )
            _atomic_bytes(new_root / relative.name, data)

        transaction: list[tuple[Path, Path, Path, Path, bool]] = []
        for relative, _data in desired_records:
            destination = root / relative
            if destination.is_symlink():
                raise ReleaseBundleError(
                    f"publication destination is a symlink: {relative}"
                )
            existed = destination.exists()
            if existed and not destination.is_file():
                raise ReleaseBundleError(
                    f"publication destination is not a file: {relative}"
                )
            transaction.append(
                (
                    relative,
                    destination,
                    new_root / relative.name,
                    backup_root / relative.name,
                    existed,
                )
            )

        try:
            for _relative, destination, _staged, backup, existed in transaction:
                if existed:
                    os.replace(destination, backup)
            for _relative, destination, staged, _backup, _existed in transaction:
                os.replace(staged, destination)
        except BaseException as exc:
            rollback_errors: list[str] = []
            for (
                relative,
                destination,
                staged,
                backup,
                existed,
            ) in reversed(transaction):
                if backup.exists():
                    if destination.exists() or destination.is_symlink():
                        try:
                            if destination.is_symlink() or not destination.is_file():
                                raise OSError("destination is not a regular file")
                            destination.unlink()
                        except BaseException as rollback_exc:
                            rollback_errors.append(f"unlink {relative}: {rollback_exc}")
                            continue
                    try:
                        os.replace(backup, destination)
                    except BaseException as rollback_exc:
                        rollback_errors.append(f"restore {relative}: {rollback_exc}")
                elif existed:
                    if not staged.exists():
                        rollback_errors.append(
                            f"restore {relative}: prior backup is unavailable"
                        )
                    elif destination.is_symlink() or not destination.is_file():
                        rollback_errors.append(
                            f"restore {relative}: prior member is unavailable"
                        )
                elif destination.exists() or destination.is_symlink():
                    if staged.exists():
                        rollback_errors.append(
                            f"unlink {relative}: unexpected concurrent member appeared"
                        )
                    else:
                        try:
                            if destination.is_symlink() or not destination.is_file():
                                raise OSError("destination is not a regular file")
                            destination.unlink()
                        except BaseException as rollback_exc:
                            rollback_errors.append(f"unlink {relative}: {rollback_exc}")
            detail = (
                f"; rollback errors: {'; '.join(rollback_errors)}"
                f"; recovery files retained at {stage}"
                if rollback_errors
                else ""
            )
            preserve_stage = bool(rollback_errors)
            if isinstance(exc, (OSError, ReleaseBundleError)) or rollback_errors:
                raise ReleaseBundleError(
                    f"cannot transactionally replace publication set: {exc}{detail}"
                ) from exc
            raise
    finally:
        if stage.exists() and not preserve_stage:
            shutil.rmtree(stage)


def publication_manuscript_errors(
    project_root: Path,
    *,
    source_date_epoch: int | None = None,
) -> tuple[str, ...]:
    """Rerender in temporary directories and report projection drift."""
    root = Path(project_root).resolve()
    try:
        expected = render_publication_manuscript(
            root, source_date_epoch=source_date_epoch
        )
    except (OSError, TypeError, ValueError) as exc:
        return (f"publication manuscript cannot be reproduced: {exc}",)
    expected_files: dict[Path, bytes] = {
        PUBLICATION_HTML: expected.html,
        RENDERER_PROVENANCE: expected.provenance,
    }
    if expected.pdf is not None:
        expected_files[PUBLICATION_PDF] = expected.pdf
    elif (root / PUBLICATION_PDF).exists():
        return ("stale PDF exists without a reproducible current renderer",)
    errors: list[str] = []
    for relative, data in expected_files.items():
        path = root / relative
        if path.is_symlink() or not path.is_file():
            errors.append(f"publication manuscript member is missing: {relative}")
        elif path.read_bytes() != data:
            errors.append(f"publication manuscript member is stale: {relative}")
    return tuple(errors)


def _safe_member_name(name: str) -> bool:
    if not name or "\\" in name or name.startswith("/") or name.endswith("/"):
        return False
    path = PurePosixPath(name)
    return path.as_posix() == name and all(
        part not in {"", ".", ".."} for part in path.parts
    )


def _is_provider_member(name: str) -> bool:
    lowered = name.lower()
    if lowered.startswith(_PROVIDER_MEMBER_PREFIXES):
        return True
    if not lowered.startswith("output/"):
        return False
    basename = PurePosixPath(lowered).name
    return basename.startswith(
        ("provider", "hermes", "opengauss", "external-full", "full-mode")
    )


@lru_cache(maxsize=1)
def _canonical_owner_names() -> tuple[frozenset[str], frozenset[str]]:
    synthetic_root = Path("/__fep_lean_release_root__")
    source_names = frozenset(
        path.relative_to(synthetic_root).as_posix()
        for path in source_owner_paths(synthetic_root)
    )
    config_names = frozenset(
        path.relative_to(synthetic_root).as_posix()
        for path in config_owner_paths(synthetic_root)
    )
    return source_names, config_names


def _expected_evidence_class(name: str) -> str | None:
    """Return the sole allowed evidence class for a recognized bundle path."""
    source_names, config_names = _canonical_owner_names()
    if name in source_names:
        return "manifested_lean_source" if name.endswith(".lean") else "source_owner"
    if name in config_names:
        return "configuration_snapshot"
    static_classes = dict(_REQUIRED_STATIC_MEMBERS)
    if name in static_classes:
        return static_classes[name]
    if name == NUMERICAL_RECEIPT.as_posix():
        return "numerical_non_proof_receipt"
    if name == PYTHON_ACCEPTANCE_RECEIPT.as_posix():
        return "python_acceptance_receipt"
    if name in _CANONICAL_BROWSER_SCREENSHOTS.values():
        return "browser_screenshot"
    if name in _MANUSCRIPT_FIGURE_REFERENCES.values():
        return "rendered_manuscript_figure"
    if name == PUBLICATION_PDF.as_posix():
        return "rendered_manuscript_pdf"
    rendered_asset_names = {
        (Path("output/manuscript") / destination).as_posix()
        for _source, destination in MANUSCRIPT_ASSETS.values()
    }
    if name in rendered_asset_names:
        return "rendered_manuscript_asset"
    path = PurePosixPath(name)
    if path.parent == PurePosixPath("output/manuscript") and path.suffix == ".md":
        return "rendered_manuscript"
    return None


def _json_object(path: Path, label: str) -> tuple[dict[str, Any] | None, str | None]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return None, f"cannot read {label}: {exc}"
    if not isinstance(payload, dict):
        return None, f"{label} must contain a JSON object"
    return payload, None


def _png_dimensions(data: bytes) -> tuple[int, int]:
    """Validate a complete PNG chunk stream and return its IHDR dimensions."""
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ReleaseBundleError("browser screenshot is not a PNG stream")
    offset = 8
    dimensions: tuple[int, int] | None = None
    saw_image_data = False
    saw_end = False
    while offset < len(data):
        if offset + 12 > len(data):
            raise ReleaseBundleError("browser screenshot has a truncated PNG chunk")
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        payload_end = offset + 8 + length
        crc_end = payload_end + 4
        if crc_end > len(data):
            raise ReleaseBundleError("browser screenshot has a truncated PNG payload")
        payload = data[offset + 8 : payload_end]
        recorded_crc = struct.unpack(">I", data[payload_end:crc_end])[0]
        actual_crc = zlib.crc32(chunk_type + payload) & 0xFFFFFFFF
        if recorded_crc != actual_crc:
            raise ReleaseBundleError("browser screenshot has an invalid PNG checksum")
        if chunk_type == b"IHDR":
            if dimensions is not None or length != 13 or offset != 8:
                raise ReleaseBundleError("browser screenshot has an invalid PNG header")
            width, height = struct.unpack(">II", payload[:8])
            if width <= 0 or height <= 0:
                raise ReleaseBundleError(
                    "browser screenshot dimensions must be positive"
                )
            dimensions = (width, height)
        elif chunk_type == b"IDAT":
            saw_image_data = True
        elif chunk_type == b"IEND":
            if length != 0:
                raise ReleaseBundleError(
                    "browser screenshot has an invalid PNG terminator"
                )
            saw_end = True
            offset = crc_end
            break
        offset = crc_end
    if dimensions is None or not saw_image_data or not saw_end or offset != len(data):
        raise ReleaseBundleError("browser screenshot PNG stream is incomplete")
    return dimensions


def _live_browser_identity(name: str, executable: Path) -> tuple[str, str]:
    """Identify the exact receipt-recorded browser, never a PATH substitute."""
    resolved_path = Path(executable)
    try:
        replayable = (
            resolved_path.is_absolute()
            and not resolved_path.is_symlink()
            and resolved_path.is_file()
            and resolved_path.resolve() == resolved_path
        )
    except OSError as exc:
        raise ReleaseBundleError(
            f"browser receipt executable path is not replayable: {resolved_path}"
        ) from exc
    if not replayable:
        raise ReleaseBundleError(
            f"browser receipt executable path is not replayable: {resolved_path}"
        )
    try:
        _detected_name, _path, version, digest = resolve_browser_executable(
            browser_name=name,
            executable=resolved_path,
        )
    except BrowserCaptureError as exc:
        raise ReleaseBundleError(str(exc)) from exc
    return version, digest


def _browser_receipt_errors(project_root: Path) -> tuple[str, ...]:
    root = Path(project_root).resolve()
    path = root / BROWSER_RECEIPT
    payload, error = _json_object(path, "browser receipt")
    if payload is None:
        return (error or "browser receipt is invalid",)
    errors: list[str] = []
    if payload.get("schema_version") != 4:
        errors.append("browser receipt schema_version must be 4")
    if payload.get("kind") != "browser-interaction":
        errors.append("browser receipt kind must be browser-interaction")
    if payload.get("accepted") is not True:
        errors.append("browser receipt must be accepted")
    browser = payload.get("browser")
    browser_name: str | None = None
    browser_executable: Path | None = None
    if not isinstance(browser, dict) or set(browser) != {
        "name",
        "version",
        "executable_path",
        "executable_sha256",
    }:
        errors.append("browser receipt identity is incomplete")
    else:
        name = browser.get("name")
        version = browser.get("version")
        executable_path = browser.get("executable_path")
        executable_sha256 = browser.get("executable_sha256")
        if name not in {"Google Chrome", "Chromium"}:
            errors.append("browser receipt name must identify Chrome or Chromium")
        if (
            not isinstance(version, str)
            or re.fullmatch(r"\d+\.\d+\.\d+\.\d+", version) is None
        ):
            errors.append("browser receipt version is invalid")
        if (
            not isinstance(executable_sha256, str)
            or _SHA256_RE.fullmatch(executable_sha256) is None
        ):
            errors.append("browser executable hash is invalid")
        elif executable_sha256 == "0" * 64:
            errors.append("browser executable hash cannot be the all-zero sentinel")
        if not isinstance(executable_path, str) or not executable_path:
            errors.append("browser executable path is invalid")
        elif not Path(executable_path).is_absolute():
            errors.append("browser executable path must be absolute")
        else:
            browser_executable = Path(executable_path)
        if (
            isinstance(name, str)
            and name in {"Google Chrome", "Chromium"}
            and browser_executable is not None
        ):
            browser_name = name
            try:
                live_version, live_digest = _live_browser_identity(
                    name, browser_executable
                )
            except ReleaseBundleError as exc:
                errors.append(str(exc))
            else:
                if version != live_version:
                    errors.append(
                        "browser receipt version differs from the live browser"
                    )
                if executable_sha256 != live_digest:
                    errors.append(
                        "browser executable hash differs from the live browser binary"
                    )
    render_configuration = payload.get("render_configuration")
    if render_configuration != canonical_browser_render_configuration():
        errors.append("browser render configuration is not canonical")
    render_environment = payload.get("render_environment")
    render_environment_keys = {
        "browser_locale",
        "device_pixel_ratio",
        "platform",
        "timezone",
        "webgl_renderer",
        "webgl_vendor",
    }
    if (
        not isinstance(render_environment, dict)
        or set(render_environment) != render_environment_keys
        or not all(
            isinstance(value, str) and value for value in render_environment.values()
        )
        or render_environment.get("browser_locale") != "en-US"
        or render_environment.get("device_pixel_ratio") != "1"
        or render_environment.get("timezone") != "UTC"
    ):
        errors.append("browser render environment is not canonical")
    capture = payload.get("capture")
    try:
        canonical_capture = canonical_browser_capture_provenance(root)
    except BrowserCaptureError as exc:
        errors.append(str(exc))
    else:
        if capture != canonical_capture:
            errors.append("browser capture provenance is not canonical")
    interactions = payload.get("interactions")
    if not isinstance(interactions, dict) or set(interactions) != set(
        _REQUIRED_BROWSER_INTERACTIONS
    ):
        errors.append("browser interaction roster is not canonical")
    elif any(interactions[key] is not True for key in _REQUIRED_BROWSER_INTERACTIONS):
        errors.append("browser interaction checks must all be true")
    expected = payload.get("expected")
    observed = payload.get("observed")
    if not isinstance(expected, dict) or observed != expected:
        errors.append("browser receipt observed and expected values must match exactly")
    try:
        presentation = build_formalism_presentation(root)
        required_counts = {
            "topics": len(presentation.topics),
            "families": len(presentation.families),
            "witnesses": len(presentation.witnesses),
            "relations": len(presentation.relations),
            "capabilities": len(presentation.capabilities),
        }
    except (OSError, TypeError, ValueError) as exc:
        errors.append(f"live browser presentation cannot be loaded: {exc}")
        required_counts = {
            "topics": RELEASE_TOPICS,
            "families": RELEASE_FAMILIES,
            "witnesses": RELEASE_WITNESSES,
            "relations": RELEASE_RELATIONS,
            "capabilities": RELEASE_CAPABILITIES,
        }
    if required_counts != {
        "topics": RELEASE_TOPICS,
        "families": RELEASE_FAMILIES,
        "witnesses": RELEASE_WITNESSES,
        "relations": RELEASE_RELATIONS,
        "capabilities": RELEASE_CAPABILITIES,
    }:
        errors.append("live presentation does not match the 155-topic release seal")
    if isinstance(expected, dict):
        for key, value in required_counts.items():
            if expected.get(key) != value:
                errors.append(f"browser receipt expected.{key} is stale")
    canonical_observations = canonical_browser_observations(required_counts)
    if expected != canonical_observations or observed != canonical_observations:
        errors.append("browser receipt detailed DOM observations are not canonical")

    projections = payload.get("projections")
    if not isinstance(projections, dict) or set(projections) != set(
        _CANONICAL_BROWSER_PROJECTIONS
    ):
        errors.append("browser receipt projection roster is not canonical")
        projections = {}
    for key, canonical_path in _CANONICAL_BROWSER_PROJECTIONS.items():
        record = projections.get(key)
        if not isinstance(record, dict) or record.get("path") != canonical_path:
            errors.append(f"browser receipt projection path is invalid: {key}")
            continue
        digest = record.get("sha256")
        if not isinstance(digest, str) or _SHA256_RE.fullmatch(digest) is None:
            errors.append(f"browser receipt projection hash is invalid: {key}")
            continue
        try:
            actual = _sha256(_relative_file_bytes(root, canonical_path))
        except ReleaseBundleError as exc:
            errors.append(str(exc))
            continue
        if digest != actual:
            errors.append(f"browser receipt projection hash is stale: {key}")

    screenshots = payload.get("screenshots")
    if not isinstance(screenshots, list) or len(screenshots) != len(
        _CANONICAL_BROWSER_SCREENSHOTS
    ):
        errors.append("browser receipt screenshot roster is not canonical")
        screenshots = []
    screenshot_paths: list[str] = []
    screenshot_roles: list[str] = []
    screenshot_data_by_role: dict[str, bytes] = {}
    for index, record in enumerate(screenshots):
        if not isinstance(record, dict):
            errors.append(f"browser screenshot record {index} must be an object")
            continue
        if set(record) != {"role", "path", "sha256", "width", "height"}:
            errors.append(f"browser screenshot record fields are invalid: {index}")
        role = record.get("role")
        relative = record.get("path")
        digest = record.get("sha256")
        width = record.get("width")
        height = record.get("height")
        if (
            not isinstance(role, str)
            or role not in _CANONICAL_BROWSER_SCREENSHOTS
            or relative != _CANONICAL_BROWSER_SCREENSHOTS.get(role)
        ):
            errors.append(f"browser screenshot role/path is invalid: {role}")
            continue
        if role in screenshot_roles:
            errors.append(f"duplicate browser screenshot role: {role}")
            continue
        screenshot_roles.append(role)
        if (
            not isinstance(relative, str)
            or not relative.startswith(f"{BROWSER_ASSET_ROOT.as_posix()}/")
            or not _safe_member_name(relative)
        ):
            errors.append(f"browser screenshot path is invalid: {relative}")
            continue
        if relative in screenshot_paths:
            errors.append(f"duplicate browser screenshot path: {relative}")
            continue
        screenshot_paths.append(relative)
        if not isinstance(digest, str) or _SHA256_RE.fullmatch(digest) is None:
            errors.append(f"browser screenshot hash is invalid: {relative}")
            continue
        try:
            screenshot_data = _relative_file_bytes(root, relative)
            actual = _sha256(screenshot_data)
            actual_width, actual_height = _png_dimensions(screenshot_data)
        except ReleaseBundleError as exc:
            errors.append(str(exc))
            continue
        screenshot_data_by_role[role] = screenshot_data
        if digest != actual:
            errors.append(f"browser screenshot hash is stale: {relative}")
        if type(width) is not int or type(height) is not int:
            errors.append(f"browser screenshot dimensions are invalid: {relative}")
        elif (width, height) != (actual_width, actual_height):
            errors.append(f"browser screenshot dimensions are stale: {relative}")
        elif role.endswith("_mobile") and (width != 390 or height < 844):
            errors.append(f"browser mobile screenshot viewport is invalid: {relative}")
        elif role.endswith("_desktop") and (width < 1200 or height < 800):
            errors.append(f"browser desktop screenshot viewport is invalid: {relative}")
        elif role.endswith("_standalone") and (width < 1200 or height < 800):
            errors.append(
                f"browser standalone screenshot viewport is invalid: {relative}"
            )
    if screenshot_paths != sorted(screenshot_paths):
        errors.append("browser screenshot paths must be lexically ordered")
    if set(screenshot_roles) != set(_CANONICAL_BROWSER_SCREENSHOTS):
        errors.append("browser receipt screenshot roles are incomplete")
    if not errors and browser_name is not None and browser_executable is not None:
        try:
            replay = replay_browser_acceptance(
                root,
                browser_name=browser_name,
                executable=browser_executable,
            )
        except BrowserCaptureError as exc:
            errors.append(f"live Chrome browser replay failed: {exc}")
        else:
            if replay.browser != browser:
                errors.append(
                    "browser receipt identity differs from live Chrome replay"
                )
            if replay.render_configuration != render_configuration:
                errors.append(
                    "browser render configuration differs from live Chrome replay"
                )
            if replay.render_environment != render_environment:
                errors.append(
                    "browser render environment differs from live Chrome replay"
                )
            if replay.observations != observed:
                errors.append(
                    "browser receipt observations differ from live Chrome replay"
                )
            if replay.interactions != interactions:
                errors.append(
                    "browser receipt interactions differ from live Chrome replay"
                )
            for role, relative in _CANONICAL_BROWSER_SCREENSHOTS.items():
                if replay.screenshot_bytes.get(role) != screenshot_data_by_role.get(
                    role
                ):
                    errors.append(
                        f"browser screenshot differs from live Chrome capture: {relative}"
                    )
    return tuple(dict.fromkeys(errors))


def _browser_screenshot_paths(project_root: Path) -> tuple[str, ...]:
    payload, error = _json_object(
        Path(project_root) / BROWSER_RECEIPT, "browser receipt"
    )
    if payload is None:
        raise ReleaseBundleError(error or "browser receipt is invalid")
    screenshots = payload.get("screenshots")
    if not isinstance(screenshots, list):
        raise ReleaseBundleError("browser receipt screenshots must be a list")
    paths: list[str] = []
    for record in screenshots:
        if not isinstance(record, dict):
            raise ReleaseBundleError("browser receipt screenshot paths are invalid")
        relative = record.get("path")
        if not isinstance(relative, str):
            raise ReleaseBundleError("browser receipt screenshot paths are invalid")
        paths.append(relative)
    return tuple(paths)


def _theorem_maturity_projection_errors(project_root: Path) -> tuple[str, ...]:
    root = Path(project_root).resolve()
    try:
        expected = render_markdown(validate_audit(root))
        actual = (root / "docs" / "theorem-maturity-audit.md").read_text(
            encoding="utf-8"
        )
    except (KeyError, OSError, TypeError, ValueError) as exc:
        return (f"theorem-maturity projection cannot be validated: {exc}",)
    return () if actual == expected else ("theorem-maturity projection is stale",)


def _license_metadata_errors(project_root: Path) -> tuple[str, ...]:
    """Require one publication identity across every bundled metadata plane."""
    root = Path(project_root).resolve()
    errors: list[str] = []
    try:
        canonical_author = load_publication_author(root)
    except PublicationMetadataError as exc:
        canonical_author = None
        errors.append(f"CITATION.cff author metadata cannot be read: {exc}")
    try:
        license_text = _relative_file_bytes(root, "LICENSE").decode("utf-8")
    except (ReleaseBundleError, UnicodeDecodeError) as exc:
        errors.append(f"canonical license text cannot be read: {exc}")
    else:
        if "Creative Commons Attribution 4.0 International (CC BY 4.0)" not in (
            license_text
        ):
            errors.append(f"LICENSE does not declare {_CANONICAL_LICENSE}")
        if f"https://doi.org/{_CANONICAL_PUBLICATION_DOI}" not in license_text:
            errors.append(f"LICENSE does not declare DOI {_CANONICAL_PUBLICATION_DOI}")
        if re.search(r"\bcopyleft\b", license_text, re.IGNORECASE) is not None:
            errors.append("LICENSE must not describe CC-BY-4.0 as copyleft")

    try:
        citation = yaml.safe_load(
            _relative_file_bytes(root, "CITATION.cff").decode("utf-8")
        )
    except (ReleaseBundleError, UnicodeDecodeError, yaml.YAMLError) as exc:
        errors.append(f"CITATION.cff license cannot be read: {exc}")
    else:
        if not isinstance(citation, dict) or citation.get("license") != (
            _CANONICAL_LICENSE
        ):
            errors.append(f"CITATION.cff license must be {_CANONICAL_LICENSE}")
        if not isinstance(citation, dict) or citation.get("version") != (
            _CANONICAL_RELEASE_VERSION
        ):
            errors.append(f"CITATION.cff version must be {_CANONICAL_RELEASE_VERSION}")
        if not isinstance(citation, dict) or citation.get("date-released") != (
            _CANONICAL_RELEASE_DATE
        ):
            errors.append(
                f"CITATION.cff date-released must be {_CANONICAL_RELEASE_DATE}"
            )
        if not isinstance(citation, dict) or citation.get("repository-code") != (
            _CANONICAL_REPOSITORY_URL
        ):
            errors.append(
                f"CITATION.cff repository-code must be {_CANONICAL_REPOSITORY_URL}"
            )
        if not isinstance(citation, dict) or citation.get("url") != (
            _CANONICAL_REPOSITORY_URL
        ):
            errors.append(f"CITATION.cff URL must be {_CANONICAL_REPOSITORY_URL}")
        preferred = (
            citation.get("preferred-citation") if isinstance(citation, dict) else None
        )
        if not isinstance(preferred, dict) or preferred.get("doi") != (
            _CANONICAL_PUBLICATION_DOI
        ):
            errors.append(
                "CITATION.cff preferred-citation DOI must be "
                f"{_CANONICAL_PUBLICATION_DOI}"
            )
        if not isinstance(preferred, dict) or preferred.get("journal") != (
            _CANONICAL_PUBLICATION_JOURNAL
        ):
            errors.append(
                "CITATION.cff preferred-citation journal must be "
                f"{_CANONICAL_PUBLICATION_JOURNAL}"
            )

    try:
        manuscript = yaml.safe_load(
            _relative_file_bytes(root, "manuscript/config.yaml").decode("utf-8")
        )
    except (ReleaseBundleError, UnicodeDecodeError, yaml.YAMLError) as exc:
        errors.append(f"manuscript license metadata cannot be read: {exc}")
    else:
        publication = (
            manuscript.get("publication") if isinstance(manuscript, dict) else None
        )
        if not isinstance(publication, dict) or publication.get("doi") != (
            _CANONICAL_PUBLICATION_DOI
        ):
            errors.append(
                f"manuscript publication DOI must be {_CANONICAL_PUBLICATION_DOI}"
            )
        if not isinstance(publication, dict) or publication.get("journal") != (
            _CANONICAL_PUBLICATION_JOURNAL
        ):
            errors.append(
                "manuscript publication journal must be "
                f"{_CANONICAL_PUBLICATION_JOURNAL}"
            )
        metadata = manuscript.get("metadata") if isinstance(manuscript, dict) else None
        if not isinstance(metadata, dict) or metadata.get("license") != (
            _CANONICAL_LICENSE
        ):
            errors.append(f"manuscript metadata license must be {_CANONICAL_LICENSE}")
        paper = manuscript.get("paper") if isinstance(manuscript, dict) else None
        if not isinstance(paper, dict) or paper.get("version") != (
            _CANONICAL_RELEASE_VERSION
        ):
            errors.append(
                f"manuscript paper version must be {_CANONICAL_RELEASE_VERSION}"
            )
        if not isinstance(paper, dict) or paper.get("date") != (
            _CANONICAL_RELEASE_DATE
        ):
            errors.append(f"manuscript paper date must be {_CANONICAL_RELEASE_DATE}")

    try:
        pyproject = _relative_file_bytes(root, "pyproject.toml").decode("utf-8")
    except (ReleaseBundleError, UnicodeDecodeError) as exc:
        errors.append(f"Python package license metadata cannot be read: {exc}")
    else:
        build_section = re.search(
            r"(?ms)^\[build-system\]\s*(.*?)(?=^\[[^\n]+\]|\Z)", pyproject
        )
        build_requires = (
            re.search(
                rf'(?m)^requires\s*=\s*\[[^\]]*"{re.escape(_MINIMUM_SPDX_SETUPTOOLS_REQUIREMENT)}"[^\]]*\]\s*$',
                build_section.group(1),
            )
            if build_section is not None
            else None
        )
        if build_requires is None:
            errors.append(
                "Python build system must require "
                f"{_MINIMUM_SPDX_SETUPTOOLS_REQUIREMENT}"
            )
        project_section = re.search(
            r"(?ms)^\[project\]\s*(.*?)(?=^\[[^\n]+\]|\Z)", pyproject
        )
        package_license = (
            re.search(r'(?m)^license\s*=\s*"([^"]+)"\s*$', project_section.group(1))
            if project_section is not None
            else None
        )
        if package_license is None or package_license.group(1) != _CANONICAL_LICENSE:
            errors.append(f"Python package license must be {_CANONICAL_LICENSE}")
        package_versions = (
            re.findall(r'(?m)^version\s*=\s*"([^"]+)"\s*$', project_section.group(1))
            if project_section is not None
            else []
        )
        if package_versions != [_CANONICAL_RELEASE_VERSION]:
            errors.append(
                f"Python package version must be {_CANONICAL_RELEASE_VERSION}"
            )
        package_readme = (
            re.search(r'(?m)^readme\s*=\s*"([^"]+)"\s*$', project_section.group(1))
            if project_section is not None
            else None
        )
        if package_readme is None or package_readme.group(1) != "README.md":
            errors.append("Python package readme must be README.md")
        package_authors = (
            re.search(r"(?ms)^authors\s*=\s*\[(.*?)\]", project_section.group(1))
            if project_section is not None
            else None
        )
        authors_text = package_authors.group(1) if package_authors is not None else ""
        package_author_records = re.findall(
            r'\{\s*name\s*=\s*"([^"]+)"\s*,\s*email\s*=\s*"([^"]+)"\s*,?\s*\}',
            authors_text,
        )
        if canonical_author is not None and package_author_records != [
            (canonical_author.name, canonical_author.email)
        ]:
            errors.append(
                "Python package authors must match CITATION.cff canonical author "
                f"{canonical_author.name} <{canonical_author.email}>"
            )
        urls_section = re.search(
            r"(?ms)^\[project\.urls\]\s*(.*?)(?=^\[[^\n]+\]|\Z)", pyproject
        )
        urls_text = urls_section.group(1) if urls_section is not None else ""
        expected_urls = {
            "Repository": _CANONICAL_REPOSITORY_URL,
            "Changelog": f"{_CANONICAL_REPOSITORY_URL}/blob/main/CHANGELOG.md",
            "Concept DOI": f"https://doi.org/{_CANONICAL_PUBLICATION_DOI}",
        }
        for label, expected_url in expected_urls.items():
            quoted_label = re.escape(f'"{label}"' if " " in label else label)
            match = re.search(rf'(?m)^{quoted_label}\s*=\s*"([^"]+)"\s*$', urls_text)
            if match is None or match.group(1) != expected_url:
                errors.append(f"Python package {label} URL must be {expected_url}")

    try:
        package_init = _relative_file_bytes(root, "src/fep_lean/__init__.py").decode(
            "utf-8"
        )
    except (ReleaseBundleError, UnicodeDecodeError) as exc:
        errors.append(f"Python runtime version cannot be read: {exc}")
    else:
        runtime_versions = re.findall(
            r'(?m)^__version__\s*=\s*"([^"]+)"\s*$', package_init
        )
        if runtime_versions != [_CANONICAL_RELEASE_VERSION]:
            errors.append(
                f"Python runtime version must be {_CANONICAL_RELEASE_VERSION}"
            )

    try:
        settings = yaml.safe_load(
            _relative_file_bytes(root, "config/settings.yaml").decode("utf-8")
        )
    except (ReleaseBundleError, UnicodeDecodeError, yaml.YAMLError) as exc:
        errors.append(f"runtime settings version cannot be read: {exc}")
    else:
        project = settings.get("project") if isinstance(settings, dict) else None
        if not isinstance(project, dict) or project.get("version") != (
            _CANONICAL_RELEASE_VERSION
        ):
            errors.append(
                f"runtime settings version must be {_CANONICAL_RELEASE_VERSION}"
            )

    try:
        sidecar = yaml.safe_load(
            _relative_file_bytes(root, ".aii/config.yaml").decode("utf-8")
        )
    except (ReleaseBundleError, UnicodeDecodeError, yaml.YAMLError) as exc:
        errors.append(f"InstituteOS sidecar metadata cannot be read: {exc}")
    else:
        meta = sidecar.get("meta") if isinstance(sidecar, dict) else None
        if not isinstance(meta, dict) or meta.get("updated") != (
            _CANONICAL_RELEASE_DATE
        ):
            errors.append(
                f"InstituteOS sidecar update date must be {_CANONICAL_RELEASE_DATE}"
            )
        repo = sidecar.get("repo") if isinstance(sidecar, dict) else None
        description = str(repo.get("description", "")) if isinstance(repo, dict) else ""
        if f"Release v{_CANONICAL_RELEASE_VERSION}" not in description:
            errors.append(
                "InstituteOS sidecar description must identify release "
                f"v{_CANONICAL_RELEASE_VERSION}"
            )
        if _CANONICAL_RELEASE_DATE not in description:
            errors.append(
                "InstituteOS sidecar description must identify release date "
                f"{_CANONICAL_RELEASE_DATE}"
            )
        if _CANONICAL_PUBLICATION_DOI not in description:
            errors.append(
                "InstituteOS sidecar description must identify concept DOI "
                f"{_CANONICAL_PUBLICATION_DOI}"
            )
        if not isinstance(repo, dict) or repo.get("full_name") != (
            "ActiveInferenceInstitute/fep_lean"
        ):
            errors.append(
                "InstituteOS sidecar repository must be "
                "ActiveInferenceInstitute/fep_lean"
            )
        ecosystem = sidecar.get("ecosystem") if isinstance(sidecar, dict) else None
        links = ecosystem.get("links") if isinstance(ecosystem, dict) else None
        if not isinstance(links, dict) or links.get("github") != (
            _CANONICAL_REPOSITORY_URL
        ):
            errors.append(
                f"InstituteOS sidecar GitHub URL must be {_CANONICAL_REPOSITORY_URL}"
            )
        provenance = sidecar.get("provenance") if isinstance(sidecar, dict) else None
        if not isinstance(provenance, dict) or provenance.get("license") != (
            _CANONICAL_LICENSE
        ):
            errors.append(f"InstituteOS sidecar license must be {_CANONICAL_LICENSE}")
        sidecar_citation = (
            provenance.get("citation") if isinstance(provenance, dict) else None
        )
        if not isinstance(sidecar_citation, dict) or sidecar_citation.get("doi") != (
            _CANONICAL_PUBLICATION_DOI
        ):
            errors.append(
                f"InstituteOS sidecar citation DOI must be {_CANONICAL_PUBLICATION_DOI}"
            )
    return tuple(errors)


def _bounded_manuscript_projection_errors(project_root: Path) -> tuple[str, ...]:
    """Validate canonical manuscript variables without launching test collection."""
    root = Path(project_root).resolve()
    try:
        variables = _manuscript_variables(root)
        catalogue = FEPTopicCatalogue.from_yaml(root / "config" / "topics.yaml")
        summary = catalogue.summary()
        presentation = build_formalism_presentation(root)
    except (OSError, TypeError, ValueError) as exc:
        return (f"manuscript variables cannot be validated: {exc}",)
    errors: list[str] = []
    for key in (
        "total_topics",
        "families",
        "maturity",
        "area_maturity",
        "semantic_dispositions",
        "area_semantic_dispositions",
    ):
        if variables.get(key) != summary[key]:
            errors.append(f"manuscript variable is stale: {key}")
    expected_areas = {
        area: {"count": count} for area, count in summary["areas"].items()
    }
    if variables.get("areas") != expected_areas:
        errors.append("manuscript variable is stale: areas")
    if variables.get("total_areas") != len(expected_areas):
        errors.append("manuscript variable is stale: total_areas")
    topic_ids = [topic.id for topic in catalogue.topics]
    if variables.get("topic_ids") != topic_ids:
        errors.append("manuscript variable is stale: topic_ids")
    topic_variables = variables.get("topics")
    if not isinstance(topic_variables, dict) or tuple(topic_variables) != tuple(
        topic_ids
    ):
        errors.append("manuscript topic-variable roster is stale")
    else:
        for topic in catalogue.topics:
            row = topic_variables.get(topic.id)
            expected = {
                "title": topic.title,
                "area": topic.area,
                "maturity": topic.mathlib_status,
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
            if not isinstance(row, dict) or any(
                row.get(key) != value for key, value in expected.items()
            ):
                errors.append(f"manuscript topic variables are stale: {topic.id}")

    formalism = variables.get("formalism")
    observed_relation_counts = Counter(row.kind for row in presentation.relations)
    relation_counts = {
        kind.value: observed_relation_counts.get(kind.value, 0) for kind in EdgeKind
    }
    capability_counts = dict(Counter(row.status for row in presentation.capabilities))
    if not isinstance(formalism, dict):
        errors.append("manuscript formalism variables are missing")
    else:
        if formalism.get("metrics") != dict(presentation.metrics):
            errors.append("manuscript formalism metrics are stale")
        if formalism.get("relation_counts") != relation_counts:
            errors.append("manuscript formalism relation counts are stale")
        if formalism.get("capability_status_counts") != {
            status: capability_counts.get(status, 0)
            for status in ("satisfied", "partial", "open")
        }:
            errors.append("manuscript capability counts are stale")
    try:
        drift = manuscript_projection_drift(
            root,
            catalogue,
            expected_variables=variables,
        )
    except (OSError, TypeError, ValueError) as exc:
        errors.append(f"manuscript appendix cannot be validated: {exc}")
    else:
        errors.extend(
            f"manuscript projection is stale: {path.relative_to(root)}"
            for path in drift
        )
    return tuple(dict.fromkeys(errors))


def _junit_identity_from_node_id(node_id: str) -> tuple[str, str]:
    address, parameter_open, parameters = node_id.partition("[")
    path, *scopes = address.split("::")
    names = [
        PurePosixPath(path).with_suffix("").as_posix().replace("/", "."),
        *scopes,
    ]
    names[-1] += parameter_open + parameters
    return ".".join(names[:-1]), names[-1]


def _canonical_python_source_records(
    project_root: Path,
) -> tuple[tuple[str, bytes], ...]:
    root = Path(project_root).resolve()
    source_root = root / "src"
    if source_root.is_symlink() or not source_root.is_dir():
        raise ReleaseBundleError("canonical Python source tree is missing or a symlink")
    records: list[tuple[str, bytes]] = []
    for path in sorted(source_root.rglob("*.py")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink() or not path.is_file():
            raise ReleaseBundleError(
                f"canonical Python source is not a regular file: {relative}"
            )
        records.append((relative, _relative_file_bytes(root, relative)))
    if not records:
        raise ReleaseBundleError("canonical Python source tree is empty")
    return tuple(records)


def _canonical_coverage_path(filename: str) -> str | None:
    if "\\" in filename:
        return None
    path = PurePosixPath(filename)
    if path.is_absolute() or not path.parts or ".." in path.parts:
        return None
    if path.parts[0] != "src":
        path = PurePosixPath("src") / path
    return path.as_posix()


def _pytest_receipt_errors(
    project_root: Path,
    *,
    expected_node_ids: Sequence[str] | None = None,
) -> tuple[str, ...]:
    root_path = Path(project_root)
    path = root_path / PYTEST_RECEIPT
    try:
        junit_root = ET.fromstring(path.read_bytes())
    except (OSError, ET.ParseError) as exc:
        return (f"cannot read Python test receipt: {exc}",)
    suites = (
        [junit_root]
        if junit_root.tag == "testsuite"
        else list(junit_root.findall("testsuite"))
    )
    if not suites:
        return ("Python test receipt contains no test suites",)
    try:
        tests = sum(int(suite.get("tests", "0")) for suite in suites)
        failures = sum(int(suite.get("failures", "0")) for suite in suites)
        errors = sum(int(suite.get("errors", "0")) for suite in suites)
        skipped = sum(int(suite.get("skipped", "0")) for suite in suites)
    except ValueError:
        return ("Python test receipt contains non-integer counters",)
    receipt_errors: list[str] = []
    if tests <= 0:
        receipt_errors.append("Python test receipt contains no tests")
    if failures or errors:
        receipt_errors.append(
            f"Python test receipt is not green: failures={failures}, errors={errors}",
        )
    if skipped >= tests:
        receipt_errors.append("Python test receipt contains no executed tests")
    testcases = list(junit_root.iter("testcase"))
    testcase_failures = sum(
        testcase.find("failure") is not None for testcase in testcases
    )
    testcase_errors = sum(testcase.find("error") is not None for testcase in testcases)
    testcase_skipped = sum(
        testcase.find("skipped") is not None for testcase in testcases
    )
    if (
        len(testcases),
        testcase_failures,
        testcase_errors,
        testcase_skipped,
    ) != (tests, failures, errors, skipped):
        receipt_errors.append(
            "Python test receipt testcase records disagree with suite counters"
        )
    for testcase in testcases:
        classname = testcase.get("classname")
        name = testcase.get("name")
        try:
            duration = float(testcase.get("time", "nan"))
        except ValueError:
            duration = math.nan
        if (
            not isinstance(classname, str)
            or not classname
            or not isinstance(name, str)
            or not name
            or not math.isfinite(duration)
            or duration < 0
        ):
            receipt_errors.append("Python test receipt contains an invalid testcase")
            break
    if expected_node_ids is not None:
        expected_testcases = Counter(
            _junit_identity_from_node_id(node_id) for node_id in expected_node_ids
        )
        observed_testcases = Counter(
            (testcase.get("classname", ""), testcase.get("name", ""))
            for testcase in testcases
        )
        if observed_testcases != expected_testcases:
            receipt_errors.append(
                "Python test receipt testcase roster differs from live collection"
            )
    try:
        manuscript_vars = yaml.safe_load(
            (root_path / "manuscript" / "manuscript_vars.yaml").read_text(
                encoding="utf-8"
            )
        )
        expected_tests = manuscript_vars["tests"]["collected"]
    except (KeyError, OSError, TypeError, yaml.YAMLError):
        receipt_errors.append("cannot resolve the canonical collected-test count")
    else:
        if type(expected_tests) is not int or expected_tests <= 0:
            receipt_errors.append("canonical collected-test count must be positive")
        elif tests != expected_tests:
            receipt_errors.append(
                "Python test receipt count differs from the canonical test roster: "
                f"receipt={tests}, canonical={expected_tests}"
            )

    coverage_path = root_path / PYTHON_COVERAGE_RECEIPT
    try:
        coverage = ET.fromstring(coverage_path.read_bytes())
        line_rate = float(coverage.get("line-rate", "nan"))
        lines_valid = int(coverage.get("lines-valid", "0"))
        lines_covered = int(coverage.get("lines-covered", "0"))
    except (OSError, ET.ParseError, TypeError, ValueError) as exc:
        receipt_errors.append(f"cannot read Python coverage receipt: {exc}")
    else:
        if coverage.tag != "coverage":
            receipt_errors.append("Python coverage receipt root must be coverage")
        if not (0.0 <= line_rate <= 1.0):
            receipt_errors.append("Python coverage line-rate must be finite in [0, 1]")
        elif line_rate < 0.89:
            receipt_errors.append(
                f"Python coverage line-rate {line_rate:.4f} is below 0.8900"
            )
        if lines_valid <= 0 or lines_covered < 0 or lines_covered > lines_valid:
            receipt_errors.append("Python coverage line counters are invalid")
        else:
            counter_rate = lines_covered / lines_valid
            if counter_rate < 0.89:
                receipt_errors.append(
                    "Python coverage counter-derived line-rate is below 0.8900"
                )
            if abs(counter_rate - line_rate) > 0.0001:
                receipt_errors.append(
                    "Python coverage line-rate disagrees with its line counters"
                )
        coverage_classes = list(coverage.iter("class"))
        coverage_lines = list(coverage.iter("line"))
        if not coverage_classes or not coverage_lines:
            receipt_errors.append(
                "Python coverage receipt contains no executable line records"
            )
        else:
            try:
                observed_lines = len(coverage_lines)
                observed_covered = sum(
                    int(line.get("hits", "-1")) > 0 for line in coverage_lines
                )
                invalid_lines = any(
                    int(line.get("number", "0")) <= 0 or int(line.get("hits", "-1")) < 0
                    for line in coverage_lines
                )
            except ValueError:
                invalid_lines = True
                observed_lines = -1
                observed_covered = -1
            if invalid_lines:
                receipt_errors.append(
                    "Python coverage receipt contains an invalid line record"
                )
            elif (observed_lines, observed_covered) != (
                lines_valid,
                lines_covered,
            ):
                receipt_errors.append(
                    "Python coverage line records disagree with aggregate counters"
                )
        try:
            source_records = _canonical_python_source_records(root_path)
        except ReleaseBundleError as exc:
            receipt_errors.append(str(exc))
        else:
            expected_sources = {name for name, _data in source_records}
            observed_sources = [
                _canonical_coverage_path(node.get("filename", ""))
                for node in coverage_classes
            ]
            if (
                None in observed_sources
                or len(observed_sources) != len(set(observed_sources))
                or set(observed_sources) != expected_sources
            ):
                receipt_errors.append(
                    "Python coverage source roster differs from canonical Python sources"
                )
            source_by_name = dict(source_records)
            for node, relative in zip(coverage_classes, observed_sources, strict=True):
                if relative not in source_by_name:
                    continue
                line_count = len(source_by_name[relative].splitlines())
                try:
                    line_numbers = [
                        int(line.get("number", "0")) for line in node.iter("line")
                    ]
                except ValueError:
                    continue
                if len(line_numbers) != len(set(line_numbers)) or any(
                    number > line_count for number in line_numbers
                ):
                    receipt_errors.append(
                        "Python coverage line records do not belong to canonical sources"
                    )
                    break
    return tuple(receipt_errors)


def _base_prerequisite_errors(project_root: Path) -> tuple[str, ...]:
    root = Path(project_root).resolve()
    errors: list[str] = []
    if not root.is_dir():
        return (f"project root is missing: {root}",)
    errors.extend(_license_metadata_errors(root))
    try:
        errors.extend(report_owner_errors(root))
        errors.extend(
            f"formalism coverage projection is stale: {path.relative_to(root)}"
            for path in formalism_coverage_drift(root)
        )
        presentation = build_formalism_presentation(root)
        errors.extend(
            f"formalism atlas projection is stale: {path.relative_to(root)}"
            for path in atlas_projection_drift(root, presentation=presentation)
        )
        errors.extend(
            f"formal-kernel dashboard projection is stale: {path.relative_to(root)}"
            for path in formal_kernel_dashboard_drift(root, presentation=presentation)
        )
    except (OSError, TypeError, ValueError) as exc:
        errors.append(f"canonical projections cannot be validated: {exc}")
    errors.extend(_bounded_manuscript_projection_errors(root))
    errors.extend(_theorem_maturity_projection_errors(root))
    errors.extend(_rendered_manuscript_errors(root))

    native = validate_native_lean_receipt(
        root / "output" / "native-verification.json", project_root=root
    )
    if not (
        native.get("valid") is True
        and native.get("source_bound") is True
        and native.get("native_claim_ready") is True
        and native.get("live_catalogue_topics") == RELEASE_SEAL["topics"]
        and native.get("selected_topics") == RELEASE_SEAL["topics"]
        and native.get("verified_topics") == RELEASE_SEAL["topics"]
    ):
        native_errors = native.get("errors")
        detail = "; ".join(native_errors) if isinstance(native_errors, list) else ""
        errors.append(f"native Lean receipt is not current and claim-ready: {detail}")
    errors.extend(
        f"formalism audit receipt is stale: {error}"
        for error in validate_formalism_audit_receipt(
            root / "output" / "formalism-audit.json", root
        )
    )
    errors.extend(_browser_receipt_errors(root))
    errors.extend(_python_acceptance_receipt_errors(root))
    for relative, _evidence_class in _REQUIRED_STATIC_MEMBERS:
        if relative in {PUBLICATION_HTML.as_posix(), RENDERER_PROVENANCE.as_posix()}:
            continue
        try:
            _relative_file_bytes(root, relative)
        except ReleaseBundleError as exc:
            errors.append(str(exc))
    return tuple(dict.fromkeys(errors))


def release_bundle_prerequisite_errors(
    project_root: Path,
    *,
    source_date_epoch: int | None = None,
    include_publication: bool = True,
) -> tuple[str, ...]:
    """Return every current-source prerequisite failure without writing."""
    errors = list(_base_prerequisite_errors(Path(project_root)))
    if include_publication:
        errors.extend(
            publication_manuscript_errors(
                project_root, source_date_epoch=source_date_epoch
            )
        )
    return tuple(dict.fromkeys(errors))


def build_numerical_witness_receipt(project_root: Path) -> bytes:
    """Serialize the live typed numerical checks as explanatory evidence."""
    root = Path(project_root).resolve()
    witnesses = evaluate_numerical_witnesses(project_root=root, scope="catalogue")
    records: list[dict[str, Any]] = []
    for witness in witnesses:
        records.append(
            {
                "id": witness.id,
                "family": witness.family,
                "title": witness.title,
                "theorem_mirrors": list(witness.theorem_mirrors),
                "invariant": witness.invariant,
                "parameters": [
                    {"name": name, "value": value} for name, value in witness.parameters
                ],
                "columns": [
                    {"key": column.key, "label": column.label}
                    for column in witness.columns
                ],
                "rows": [list(row.values) for row in witness.rows],
                "checks": [
                    {
                        "id": check.id,
                        "relation": check.relation,
                        "lhs": check.lhs,
                        "rhs": check.rhs,
                        "tolerance": check.tolerance,
                        "residual": check.residual,
                        "accepted": check.accepted,
                    }
                    for check in witness.checks
                ],
                "boundary_behavior": witness.boundary_behavior,
                "boundary_observed": witness.boundary_observed,
                "plot": {
                    "kind": witness.plot.kind,
                    "x_key": witness.plot.x_key,
                    "y_keys": list(witness.plot.y_keys),
                },
                "formal_alignment": witness.formal_alignment,
                "evidence_kind": witness.evidence_kind,
                "accepted": witness.accepted,
            }
        )
    payload = {
        "schema_version": 1,
        "kind": "numerical-witness-receipt",
        "evidence_kind": NON_PROOF_EVIDENCE,
        "complete": bool(records) and all(record["accepted"] for record in records),
        "witness_count": len(records),
        "check_count": sum(len(record["checks"]) for record in records),
        "source_sha256": report_source_digest(root),
        "config_sha256": report_config_digest(root),
        "witnesses": records,
    }
    if payload["witness_count"] != RELEASE_SEAL["witnesses"] or payload["complete"] is not True:
        raise ReleaseBundleError(
            "the live numerical witness closure is not the accepted 15-witness release"
        )
    return _canonical_json(payload)


def _python_test_records(project_root: Path) -> tuple[tuple[str, bytes], ...]:
    """Capture the complete maintained test tree without generated caches."""
    root = Path(project_root).resolve()
    test_root = root / "tests"
    if test_root.is_symlink() or not test_root.is_dir():
        raise ReleaseBundleError("canonical Python test tree is missing or a symlink")
    records: list[tuple[str, bytes]] = []
    for path in sorted(test_root.rglob("*")):
        relative = path.relative_to(root)
        if path.is_symlink():
            raise ReleaseBundleError(
                f"canonical Python test tree contains a symlink: {relative.as_posix()}"
            )
        if "__pycache__" in relative.parts or path.suffix in {".pyc", ".pyo"}:
            continue
        if path.is_file():
            name = relative.as_posix()
            records.append((name, _relative_file_bytes(root, name)))
    if not records:
        raise ReleaseBundleError("canonical Python test tree is empty")
    return tuple(records)


def _distribution_fingerprint(distribution_name: str) -> dict[str, str]:
    try:
        distribution = importlib.metadata.distribution(distribution_name)
    except importlib.metadata.PackageNotFoundError as exc:
        raise ReleaseBundleError(
            f"required Python acceptance distribution is missing: {distribution_name}"
        ) from exc
    selected: list[tuple[str, bytes]] = []
    for relative in distribution.files or ():
        relative_path = PurePosixPath(str(relative))
        if relative_path.suffix not in {
            ".py",
            ".so",
            ".pyd",
        } and relative_path.name not in {
            "METADATA",
            "entry_points.txt",
        }:
            continue
        path = Path(str(distribution.locate_file(relative)))
        if not path.is_file():
            raise ReleaseBundleError(
                "Python acceptance distribution file is missing: "
                f"{distribution_name}:{relative_path.as_posix()}"
            )
        selected.append((relative_path.as_posix(), path.read_bytes()))
    if not selected:
        raise ReleaseBundleError(
            f"Python acceptance distribution has no fingerprinted files: {distribution_name}"
        )
    return {
        "version": distribution.version,
        "files_sha256": _digest_named_bytes(selected),
    }


def _normalized_python_acceptance_command() -> list[str]:
    return [
        sys.executable,
        "-m",
        "pytest",
        *(
            argument
            for plugin in _PYTHON_ACCEPTANCE_EXPLICIT_PLUGINS
            for argument in ("-p", plugin)
        ),
        "-o",
        "cache_dir=<temporary>",
        *_PYTHON_ACCEPTANCE_ARGUMENTS,
    ]


def _python_acceptance_command(cache_dir: Path) -> list[str]:
    command = _normalized_python_acceptance_command()
    command[command.index("cache_dir=<temporary>")] = f"cache_dir={cache_dir}"
    return command


def _python_acceptance_external_executable(name: str) -> dict[str, str]:
    found = shutil.which(name)
    if found is None:
        raise ReleaseBundleError(
            f"required Python acceptance executable is missing: {name}"
        )
    path = Path(found).resolve()
    if not path.is_file():
        raise ReleaseBundleError(
            f"Python acceptance executable is not a regular file: {name}"
        )
    return {"path": path.as_posix(), "sha256": _sha256(path.read_bytes())}


def _controlled_python_acceptance_path(uv_path: str) -> str:
    directories = [Path(sys.executable).resolve().parent.as_posix()]
    directories.append(Path(uv_path).parent.as_posix())
    directories.extend(os.defpath.split(os.pathsep))
    return os.pathsep.join(dict.fromkeys(path for path in directories if path))


def _python_acceptance_environment(temporary_root: Path) -> dict[str, str]:
    environment = pytest_collection_environment(temporary_root)
    environment["COVERAGE_FILE"] = str(temporary_root / ".coverage")
    uv_identity = _python_acceptance_external_executable("uv")
    environment["PATH"] = _controlled_python_acceptance_path(uv_identity["path"])
    return environment


def _python_acceptance_runtime_identity() -> dict[str, Any]:
    collection_identity = collection_runtime_identity()
    uv_identity = _python_acceptance_external_executable("uv")
    identity: dict[str, Any] = {
        "environment": {
            **collection_identity["environment"],
            "COVERAGE_FILE": "<temporary>/.coverage",
            "PATH": _controlled_python_acceptance_path(uv_identity["path"]),
        },
        "external_executables": {"uv": uv_identity},
        "explicit_plugins": list(_PYTHON_ACCEPTANCE_EXPLICIT_PLUGINS),
        "interpreter": collection_identity["interpreter"],
        "plugin_distributions": {
            name: _distribution_fingerprint(name)
            for name in _PYTHON_ACCEPTANCE_DISTRIBUTIONS
        },
        "pytest_arguments": _normalized_python_acceptance_command()[3:],
    }
    identity["fingerprint_sha256"] = _sha256(_canonical_json(identity))
    return identity


def _collect_python_node_ids(
    project_root: Path, temporary_root: Path
) -> tuple[str, ...]:
    command = pytest_collection_command(temporary_root / "pytest-cache")
    try:
        completed = subprocess.run(
            command,
            cwd=project_root,
            env=pytest_collection_environment(temporary_root),
            check=False,
            capture_output=True,
            text=True,
            timeout=_PYTHON_ACCEPTANCE_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ReleaseBundleError(
            f"cannot collect canonical Python tests: {exc}"
        ) from exc
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise ReleaseBundleError(
            "canonical Python test collection failed"
            + (f": {detail}" if detail else "")
        )
    try:
        return parse_pytest_collection_stdout(completed.stdout)
    except ValueError as exc:
        raise ReleaseBundleError(
            f"canonical Python test collection is invalid: {exc}"
        ) from exc


def _python_input_snapshot(project_root: Path) -> dict[str, Any]:
    root = Path(project_root).resolve()
    test_records = _python_test_records(root)
    test_count_owner = _relative_file_bytes(root, "manuscript/manuscript_vars.yaml")
    snapshot: dict[str, Any] = {
        "source_sha256": report_source_digest(root),
        "config_sha256": report_config_digest(root),
        "test_tree_sha256": _digest_named_bytes(test_records),
        "test_file_count": len(test_records),
        "test_count_owner_sha256": _sha256(test_count_owner),
    }
    snapshot["fingerprint_sha256"] = _sha256(_canonical_json(snapshot))
    return snapshot


def _python_evidence_summary(project_root: Path) -> dict[str, Any]:
    """Summarize already validated JUnit and Cobertura evidence."""
    root = Path(project_root).resolve()
    junit_data = _relative_file_bytes(root, PYTEST_RECEIPT.as_posix())
    coverage_data = _relative_file_bytes(root, PYTHON_COVERAGE_RECEIPT.as_posix())
    junit_root = ET.fromstring(junit_data)
    suites = (
        [junit_root]
        if junit_root.tag == "testsuite"
        else list(junit_root.findall("testsuite"))
    )
    tests = sum(int(suite.get("tests", "0")) for suite in suites)
    failures = sum(int(suite.get("failures", "0")) for suite in suites)
    receipt_errors = sum(int(suite.get("errors", "0")) for suite in suites)
    skipped = sum(int(suite.get("skipped", "0")) for suite in suites)
    duration = sum(float(suite.get("time", "0")) for suite in suites)
    coverage = ET.fromstring(coverage_data)
    source_by_name = dict(_canonical_python_source_records(root))
    coverage_records: list[dict[str, Any]] = []
    for node in coverage.iter("class"):
        relative = _canonical_coverage_path(node.get("filename", ""))
        if relative not in source_by_name:
            raise ReleaseBundleError(
                "Python coverage source roster differs from canonical Python sources"
            )
        coverage_records.append(
            {
                "path": relative,
                "source_sha256": _sha256(source_by_name[relative]),
                "lines": [
                    {
                        "number": int(line.get("number", "0")),
                        "hits": int(line.get("hits", "-1")),
                    }
                    for line in node.iter("line")
                ],
            }
        )
    coverage_records.sort(key=lambda record: str(record["path"]))
    return {
        "tests": {
            "collected": tests,
            "passed": tests - failures - receipt_errors - skipped,
            "skipped": skipped,
            "failures": failures,
            "errors": receipt_errors,
            "duration_seconds": duration,
            "junit_path": PYTEST_RECEIPT.as_posix(),
            "junit_sha256": _sha256(junit_data),
        },
        "coverage": {
            "line_rate": float(coverage.get("line-rate", "nan")),
            "floor": 0.89,
            "lines_valid": int(coverage.get("lines-valid", "0")),
            "lines_covered": int(coverage.get("lines-covered", "0")),
            "path": PYTHON_COVERAGE_RECEIPT.as_posix(),
            "sha256": _sha256(coverage_data),
            "source_records": coverage_records,
        },
    }


def _python_acceptance_receipt_errors(project_root: Path) -> tuple[str, ...]:
    root = Path(project_root).resolve()
    errors: list[str] = []
    live_node_ids: tuple[str, ...] | None = None
    current_collection: dict[str, Any] | None = None
    current_executor: dict[str, Any] | None = None
    try:
        with tempfile.TemporaryDirectory(
            prefix="fep-lean-pytest-check-"
        ) as raw_directory:
            live_node_ids = _collect_python_node_ids(root, Path(raw_directory))
        current_collection = collection_runtime_identity()
        current_executor = _python_acceptance_runtime_identity()
    except (OSError, TypeError, ValueError, ReleaseBundleError) as exc:
        errors.append(f"Python acceptance runtime cannot be validated: {exc}")
    errors.extend(
        _pytest_receipt_errors(root, expected_node_ids=live_node_ids)
        if live_node_ids is not None
        else _pytest_receipt_errors(root)
    )
    path = root / PYTHON_ACCEPTANCE_RECEIPT
    payload, error = _json_object(path, "Python acceptance receipt")
    if payload is None:
        errors.append(error or "Python acceptance receipt is invalid")
        return tuple(dict.fromkeys(errors))
    try:
        receipt_data = _relative_file_bytes(root, PYTHON_ACCEPTANCE_RECEIPT.as_posix())
        current_inputs = _python_input_snapshot(root)
        summary = _python_evidence_summary(root)
    except (OSError, TypeError, ValueError, ET.ParseError) as exc:
        errors.append(f"Python acceptance receipt cannot be validated: {exc}")
        return tuple(dict.fromkeys(errors))
    if receipt_data != _canonical_json(payload):
        errors.append("Python acceptance receipt is not canonical sorted JSON")
    if payload.get("schema_version") != 3:
        errors.append("Python acceptance receipt schema_version must be 3")
    if payload.get("kind") != "python-acceptance-receipt":
        errors.append("Python acceptance receipt kind is invalid")
    if payload.get("complete") is not True or payload.get("returncode") != 0:
        errors.append("Python acceptance receipt is not complete and green")
    if payload.get("command") != _normalized_python_acceptance_command():
        errors.append("Python acceptance receipt command is not canonical")
    if current_executor is not None and payload.get("executor") != current_executor:
        errors.append("Python acceptance receipt executor identity is stale")
    collection = payload.get("collection")
    if not isinstance(collection, dict):
        errors.append("Python acceptance receipt collection evidence is invalid")
    else:
        if current_collection is not None and collection.get("command") != [
            sys.executable,
            "-m",
            "pytest",
            *current_collection["pytest_arguments"],
        ]:
            errors.append(
                "Python acceptance receipt collection command is not canonical"
            )
        if live_node_ids is not None and collection.get("node_ids") != list(
            live_node_ids
        ):
            errors.append("Python acceptance receipt collected node IDs are stale")
    inputs = payload.get("inputs")
    if not isinstance(inputs, dict) or set(inputs) != {"before", "after", "stable"}:
        errors.append("Python acceptance receipt input snapshots are invalid")
    else:
        before = inputs.get("before")
        after = inputs.get("after")
        if inputs.get("stable") is not True or before != after:
            errors.append("Python acceptance receipt input snapshots are not stable")
        if after != current_inputs:
            errors.append("Python acceptance receipt input snapshot is stale")
    if payload.get("tests") != summary["tests"]:
        errors.append("Python acceptance receipt JUnit summary or hash is stale")
    if payload.get("coverage") != summary["coverage"]:
        errors.append("Python acceptance receipt coverage summary or hash is stale")
    try:
        if current_inputs != _python_input_snapshot(root):
            errors.append("Python acceptance inputs changed during validation")
        if current_executor != _python_acceptance_runtime_identity():
            errors.append("Python acceptance executor changed during validation")
    except (OSError, TypeError, ValueError, ReleaseBundleError) as exc:
        errors.append(f"Python acceptance runtime cannot be revalidated: {exc}")
    return tuple(dict.fromkeys(errors))


def build_python_acceptance_receipt(project_root: Path) -> bytes:
    """Return the current receipt created by :func:`run_python_acceptance`."""
    root = Path(project_root).resolve()
    errors = _python_acceptance_receipt_errors(root)
    if errors:
        raise ReleaseBundleError(
            "Python acceptance receipts are not claim-ready:\n" + "\n".join(errors)
        )
    return _relative_file_bytes(root, PYTHON_ACCEPTANCE_RECEIPT.as_posix())


def _restore_python_acceptance_files(
    prior: Mapping[Path, bytes | None],
) -> tuple[str, ...]:
    errors: list[str] = []
    for path, data in prior.items():
        try:
            if data is None:
                path.unlink(missing_ok=True)
            else:
                _atomic_bytes(path, data)
        except OSError as exc:
            errors.append(f"{path}: {exc}")
    return tuple(errors)


def run_python_acceptance(project_root: Path) -> Path:
    """Run the canonical suite once and atomically retain its bound receipts."""
    root = Path(project_root).resolve()
    output_root = root / "output"
    if output_root.is_symlink():
        raise ReleaseBundleError("Python acceptance output directory is a symlink")
    output_root.mkdir(parents=True, exist_ok=True)
    if not output_root.resolve().is_relative_to(root):
        raise ReleaseBundleError(
            "Python acceptance output directory escapes project root"
        )
    owned_paths = tuple(
        root / relative
        for relative in (
            PYTEST_RECEIPT,
            PYTHON_COVERAGE_RECEIPT,
            PYTHON_ACCEPTANCE_RECEIPT,
        )
    )
    for path in owned_paths:
        if path.is_symlink() or (path.exists() and not path.is_file()):
            raise ReleaseBundleError(
                "Python acceptance destination is not a regular file: "
                f"{path.relative_to(root).as_posix()}"
            )
    prior = {
        path: path.read_bytes() if path.is_file() else None for path in owned_paths
    }
    before = _python_input_snapshot(root)
    try:
        executor_before = _python_acceptance_runtime_identity()
        collection_identity = collection_runtime_identity()
        with tempfile.TemporaryDirectory(prefix="fep-lean-pytest-") as raw:
            temporary_root = Path(raw)
            node_ids = _collect_python_node_ids(root, temporary_root)
            command = _python_acceptance_command(temporary_root / "pytest-cache")
            completed = subprocess.run(
                command,
                cwd=root,
                env=_python_acceptance_environment(temporary_root),
                check=False,
                capture_output=True,
                text=True,
                timeout=_PYTHON_ACCEPTANCE_TIMEOUT_SECONDS,
            )
            if completed.returncode != 0:
                detail = (completed.stderr or completed.stdout).strip()
                raise ReleaseBundleError(
                    "canonical Python acceptance command failed"
                    + (f": {detail}" if detail else "")
                )
        receipt_errors = _pytest_receipt_errors(root, expected_node_ids=node_ids)
        if receipt_errors:
            raise ReleaseBundleError(
                "canonical Python acceptance evidence is invalid:\n"
                + "\n".join(receipt_errors)
            )
        after = _python_input_snapshot(root)
        if before != after:
            raise ReleaseBundleError(
                "Python source, configuration, or tests changed during acceptance"
            )
        executor_after = _python_acceptance_runtime_identity()
        if executor_before != executor_after:
            raise ReleaseBundleError(
                "Python acceptance executor changed during acceptance"
            )
        summary = _python_evidence_summary(root)
        payload = {
            "schema_version": 3,
            "kind": "python-acceptance-receipt",
            "complete": True,
            "returncode": completed.returncode,
            "command": _normalized_python_acceptance_command(),
            "collection": {
                "command": [
                    sys.executable,
                    "-m",
                    "pytest",
                    *collection_identity["pytest_arguments"],
                ],
                "node_ids": list(node_ids),
            },
            "executor": executor_after,
            "inputs": {"before": before, "after": after, "stable": True},
            **summary,
        }
        _atomic_bytes(root / PYTHON_ACCEPTANCE_RECEIPT, _canonical_json(payload))
        validation_errors = _python_acceptance_receipt_errors(root)
        if validation_errors:
            raise ReleaseBundleError(
                "generated Python acceptance receipt is invalid:\n"
                + "\n".join(validation_errors)
            )
    except BaseException as exc:
        rollback_errors = _restore_python_acceptance_files(prior)
        if rollback_errors:
            raise ReleaseBundleError(
                "cannot restore Python acceptance receipts: "
                + "; ".join(rollback_errors)
            ) from exc
        if isinstance(exc, ReleaseBundleError):
            raise
        if isinstance(exc, (OSError, subprocess.SubprocessError)):
            raise ReleaseBundleError(f"cannot run Python acceptance: {exc}") from exc
        raise
    return root / PYTHON_ACCEPTANCE_RECEIPT


def _add_member(
    members: dict[str, _BundleMember],
    *,
    path: str,
    data: bytes,
    evidence_class: str,
) -> None:
    if not _safe_member_name(path) or path in {MANIFEST_NAME, CHECKSUMS_NAME}:
        raise ReleaseBundleError(f"unsafe bundle member path: {path}")
    if path in members:
        raise ReleaseBundleError(f"duplicate bundle member path: {path}")
    if _is_provider_member(path):
        raise ReleaseBundleError(f"provider artifact is forbidden: {path}")
    members[path] = _BundleMember(path, data, evidence_class)


def _project_members(project_root: Path) -> tuple[_BundleMember, ...]:
    root = Path(project_root).resolve()
    members: dict[str, _BundleMember] = {}
    source_paths = source_owner_paths(root)
    for path in source_paths:
        relative = path.relative_to(root).as_posix()
        _add_member(
            members,
            path=relative,
            data=_relative_file_bytes(root, relative),
            evidence_class=(
                "manifested_lean_source"
                if relative.endswith(".lean")
                else "source_owner"
            ),
        )
    for path in config_owner_paths(root):
        relative = path.relative_to(root).as_posix()
        if relative not in members:
            _add_member(
                members,
                path=relative,
                data=_relative_file_bytes(root, relative),
                evidence_class="configuration_snapshot",
            )
    for relative, evidence_class in _REQUIRED_STATIC_MEMBERS:
        if relative not in members:
            _add_member(
                members,
                path=relative,
                data=_relative_file_bytes(root, relative),
                evidence_class=evidence_class,
            )
    for source in manuscript_source_files(root / "manuscript"):
        relative = f"output/manuscript/{source.name}"
        if relative not in members:
            _add_member(
                members,
                path=relative,
                data=_relative_file_bytes(root, relative),
                evidence_class="rendered_manuscript",
            )
    for _source, destination in MANUSCRIPT_ASSETS.values():
        relative = (Path("output/manuscript") / destination).as_posix()
        if relative not in members:
            _add_member(
                members,
                path=relative,
                data=_relative_file_bytes(root, relative),
                evidence_class="rendered_manuscript_asset",
            )
    for relative, data in _publication_resource_records(root):
        if relative not in members:
            _add_member(
                members,
                path=relative,
                data=data,
                evidence_class="rendered_manuscript_figure",
            )
    provenance, error = _json_object(root / RENDERER_PROVENANCE, "renderer provenance")
    if provenance is None:
        raise ReleaseBundleError(error or "renderer provenance is invalid")
    pdf = provenance.get("pdf")
    if isinstance(pdf, dict) and pdf.get("current") is True:
        _add_member(
            members,
            path=PUBLICATION_PDF.as_posix(),
            data=_relative_file_bytes(root, PUBLICATION_PDF.as_posix()),
            evidence_class="rendered_manuscript_pdf",
        )
    for relative in _browser_screenshot_paths(root):
        _add_member(
            members,
            path=relative,
            data=_relative_file_bytes(root, relative),
            evidence_class="browser_screenshot",
        )
    _add_member(
        members,
        path=NUMERICAL_RECEIPT.as_posix(),
        data=build_numerical_witness_receipt(root),
        evidence_class="numerical_non_proof_receipt",
    )
    _add_member(
        members,
        path=PYTHON_ACCEPTANCE_RECEIPT.as_posix(),
        data=build_python_acceptance_receipt(root),
        evidence_class="python_acceptance_receipt",
    )
    return tuple(members[path] for path in sorted(members))


def _toolchain_identity(project_root: Path) -> dict[str, str]:
    root = Path(project_root)
    native, error = _json_object(
        root / "output" / "native-verification.json", "native Lean receipt"
    )
    if native is None:
        raise ReleaseBundleError(error or "native Lean receipt is invalid")
    identity = {
        "lean_toolchain": str(native.get("lean_toolchain", "")),
        "lean_version": str(native.get("lean_version", "")),
        "mathlib_tag": str(native.get("mathlib_tag", "")),
        "mathlib_revision": str(native.get("mathlib_revision", "")),
    }
    if (
        not identity["lean_toolchain"]
        or not identity["lean_version"]
        or not re.fullmatch(r"v\d+\.\d+\.\d+", identity["mathlib_tag"])
        or not re.fullmatch(r"[0-9a-f]{40}", identity["mathlib_revision"])
    ):
        raise ReleaseBundleError("native receipt lacks a complete toolchain identity")
    return identity


def _member_by_path(members: Sequence[_BundleMember], path: str) -> _BundleMember:
    matches = [member for member in members if member.path == path]
    if len(matches) != 1:
        raise ReleaseBundleError(f"release snapshot lacks exactly one member: {path}")
    return matches[0]


def _toolchain_identity_from_members(
    members: Sequence[_BundleMember],
) -> dict[str, str]:
    native_member = _member_by_path(members, "output/native-verification.json")
    try:
        native = json.loads(native_member.data.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ReleaseBundleError("native receipt snapshot is invalid JSON") from exc
    if not isinstance(native, dict):
        raise ReleaseBundleError("native receipt snapshot must be a JSON object")
    identity = {
        "lean_toolchain": str(native.get("lean_toolchain", "")),
        "lean_version": str(native.get("lean_version", "")),
        "mathlib_tag": str(native.get("mathlib_tag", "")),
        "mathlib_revision": str(native.get("mathlib_revision", "")),
    }
    if (
        not identity["lean_toolchain"]
        or not identity["lean_version"]
        or not re.fullmatch(r"v\d+\.\d+\.\d+", identity["mathlib_tag"])
        or not re.fullmatch(r"[0-9a-f]{40}", identity["mathlib_revision"])
    ):
        raise ReleaseBundleError("native receipt lacks a complete toolchain identity")
    return identity


def _digest_snapshot_classes(
    members: Sequence[_BundleMember],
    evidence_classes: frozenset[str],
) -> str:
    records = [
        (member.path, member.data)
        for member in members
        if member.evidence_class in evidence_classes
    ]
    if not records:
        raise ReleaseBundleError("release snapshot contains no canonical owners")
    return _digest_named_bytes(records)


def _supplemental_snapshot_records(
    project_root: Path,
) -> tuple[tuple[str, bytes], ...]:
    """Capture release inputs that are validated but intentionally not bundled."""
    root = Path(project_root).resolve()
    records: list[tuple[str, bytes]] = []
    if (root / "manuscript").is_dir():
        records.extend(_manuscript_source_records(root))
    if (root / "tests").is_dir():
        records.extend(_python_test_records(root))
    return tuple(records)


def _snapshot_fingerprint(project_root: Path, members: Sequence[_BundleMember]) -> str:
    records = [(member.path, member.data) for member in members]
    records.extend(_supplemental_snapshot_records(project_root))
    return _digest_named_bytes(records)


def _live_snapshot_fingerprint(
    project_root: Path, members: Sequence[_BundleMember]
) -> str:
    root = Path(project_root).resolve()
    records: list[tuple[str, bytes]] = []
    for member in members:
        if member.path == NUMERICAL_RECEIPT.as_posix():
            data = build_numerical_witness_receipt(root)
        elif member.path == PYTHON_ACCEPTANCE_RECEIPT.as_posix():
            data = build_python_acceptance_receipt(root)
        else:
            data = _relative_file_bytes(root, member.path)
        records.append((member.path, data))
    records.extend(_supplemental_snapshot_records(root))
    return _digest_named_bytes(records)


def _build_manifest(
    project_root: Path,
    members: Sequence[_BundleMember],
    *,
    epoch: int,
) -> dict[str, Any]:
    try:
        coverage_snapshot = json.loads(
            _member_by_path(members, "docs/formalism-coverage.json").data.decode(
                "utf-8"
            )
        )
        numerical_snapshot = json.loads(
            _member_by_path(members, NUMERICAL_RECEIPT.as_posix()).data.decode("utf-8")
        )
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ReleaseBundleError("release summary snapshot is invalid JSON") from exc
    if not isinstance(coverage_snapshot, dict) or not isinstance(
        numerical_snapshot, dict
    ):
        raise ReleaseBundleError("release summary snapshot must contain JSON objects")
    topics = coverage_snapshot.get("topics")
    family_counts = coverage_snapshot.get("family_counts")
    area_counts = coverage_snapshot.get("area_counts")
    relations = coverage_snapshot.get("relations")
    capabilities = coverage_snapshot.get("capabilities")
    formal_modules = coverage_snapshot.get("formal_modules")
    if (
        not isinstance(topics, list)
        or not topics
        or not all(isinstance(topic, dict) for topic in topics)
        or not isinstance(family_counts, dict)
        or not isinstance(area_counts, dict)
        or not isinstance(relations, list)
        or not isinstance(capabilities, list)
        or not isinstance(formal_modules, list)
        or type(numerical_snapshot.get("witness_count")) is not int
    ):
        raise ReleaseBundleError("release summary snapshot has an invalid shape")
    first_id = topics[0].get("id")
    last_id = topics[-1].get("id")
    if not isinstance(first_id, str) or not isinstance(last_id, str):
        raise ReleaseBundleError("release summary snapshot lacks topic boundary IDs")
    browser = _member_by_path(members, BROWSER_RECEIPT.as_posix()).data
    native = _member_by_path(members, "output/native-verification.json").data
    formal = _member_by_path(members, "output/formalism-audit.json").data
    pytest_receipt = _member_by_path(members, PYTEST_RECEIPT.as_posix()).data
    coverage_receipt = _member_by_path(members, PYTHON_COVERAGE_RECEIPT.as_posix()).data
    numerical = _member_by_path(members, NUMERICAL_RECEIPT.as_posix()).data
    python_acceptance = _member_by_path(
        members, PYTHON_ACCEPTANCE_RECEIPT.as_posix()
    ).data
    return {
        "schema_version": RELEASE_BUNDLE_SCHEMA_VERSION,
        "kind": "fep-lean-evidence-bundle",
        "source_date_epoch": epoch,
        "catalogue": {
            "topics": len(topics),
            "families": len(family_counts),
            "areas": len(area_counts),
            "first_id": first_id,
            "last_id": last_id,
        },
        "formalism": {
            "relations": len(relations),
            "capabilities": len(capabilities),
            "formal_modules": len(formal_modules),
            "numerical_witnesses": numerical_snapshot["witness_count"],
        },
        "toolchain": _toolchain_identity_from_members(members),
        "evidence": {
            "native_lean": {
                "current": True,
                "path": "output/native-verification.json",
                "sha256": _sha256(native),
            },
            "declaration_axiom_audit": {
                "current": True,
                "path": "output/formalism-audit.json",
                "sha256": _sha256(formal),
            },
            "browser_interaction": {
                "current": True,
                "path": BROWSER_RECEIPT.as_posix(),
                "sha256": _sha256(browser),
            },
            "numerical_witnesses": {
                "current": True,
                "path": NUMERICAL_RECEIPT.as_posix(),
                "sha256": _sha256(numerical),
                "evidence_kind": NON_PROOF_EVIDENCE,
            },
            "python_tests": {
                "current": True,
                "path": PYTEST_RECEIPT.as_posix(),
                "sha256": _sha256(pytest_receipt),
            },
            "python_coverage": {
                "current": True,
                "path": PYTHON_COVERAGE_RECEIPT.as_posix(),
                "sha256": _sha256(coverage_receipt),
            },
            "python_acceptance": {
                "current": True,
                "path": PYTHON_ACCEPTANCE_RECEIPT.as_posix(),
                "sha256": _sha256(python_acceptance),
            },
        },
        "external_full_mode": {
            "current": False,
            "authorized": False,
            "artifacts": [],
        },
        "source_sha256": _digest_snapshot_classes(
            members, frozenset({"manifested_lean_source", "source_owner"})
        ),
        "config_sha256": _digest_snapshot_classes(
            members, frozenset({"configuration_snapshot"})
        ),
        "manifested_lean_sources": [
            member.path
            for member in members
            if member.evidence_class == "manifested_lean_source"
        ],
        "members": [
            {
                "path": member.path,
                "sha256": _sha256(member.data),
                "size": len(member.data),
                "evidence_class": member.evidence_class,
            }
            for member in members
        ],
    }


def _archive_contents(
    project_root: Path,
    members: Sequence[_BundleMember],
    *,
    epoch: int,
) -> dict[str, bytes]:
    manifest_bytes = _canonical_json(
        _build_manifest(project_root, members, epoch=epoch)
    )
    contents = {member.path: member.data for member in members}
    contents[MANIFEST_NAME] = manifest_bytes
    checksums = "".join(
        f"{_sha256(contents[name])}  {name}\n" for name in sorted(contents)
    ).encode("utf-8")
    contents[CHECKSUMS_NAME] = checksums
    return contents


def _write_archive(path: Path, contents: Mapping[str, bytes], *, epoch: int) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, raw_path = tempfile.mkstemp(
        prefix=f".{destination.name}.", dir=destination.parent
    )
    try:
        with os.fdopen(fd, "wb") as raw:
            with (
                gzip.GzipFile(
                    fileobj=raw,
                    mode="wb",
                    filename="",
                    compresslevel=9,
                    mtime=epoch,
                ) as zipped,
                tarfile.open(
                    fileobj=zipped,
                    mode="w|",
                    format=tarfile.USTAR_FORMAT,
                ) as tar,
            ):
                for name in sorted(contents):
                    if not _safe_member_name(name):
                        raise ReleaseBundleError(f"unsafe bundle member path: {name}")
                    data = contents[name]
                    info = tarfile.TarInfo(name)
                    info.mode = 0o644
                    info.uid = 0
                    info.gid = 0
                    info.uname = ""
                    info.gname = ""
                    info.mtime = epoch
                    info.size = len(data)
                    tar.addfile(info, io.BytesIO(data))
            raw.flush()
            os.fsync(raw.fileno())
        os.replace(raw_path, destination)
    except (OSError, tarfile.TarError, ValueError) as exc:
        raise ReleaseBundleError(f"cannot build deterministic archive: {exc}") from exc
    finally:
        if os.path.exists(raw_path):
            os.unlink(raw_path)


def build_release_bundle(
    project_root: Path,
    output_path: Path,
    *,
    source_date_epoch: int | None = None,
) -> Path:
    """Validate, render, stage, validate, and atomically replace one bundle."""
    root = Path(project_root).resolve()
    requested_destination = Path(output_path)
    if requested_destination.is_symlink():
        raise ReleaseBundleError("release bundle destination is a symlink")
    lexical_destination = requested_destination.absolute()
    destination = requested_destination.resolve()
    if not destination.name.endswith(".tar.gz"):
        raise ReleaseBundleError("release bundle destination must end in .tar.gz")
    if lexical_destination.is_relative_to(root) or destination.is_relative_to(root):
        raise ReleaseBundleError(
            "release bundle destination must be outside the project root"
        )
    epoch = _source_date_epoch(source_date_epoch)
    prerequisite_errors = release_bundle_prerequisite_errors(
        root, source_date_epoch=epoch, include_publication=False
    )
    if prerequisite_errors:
        raise ReleaseBundleError(
            "release prerequisites failed:\n" + "\n".join(prerequisite_errors)
        )
    write_publication_manuscript(root, source_date_epoch=epoch)
    publication_errors = publication_manuscript_errors(root, source_date_epoch=epoch)
    if publication_errors:
        raise ReleaseBundleError(
            "publication manuscript is stale:\n" + "\n".join(publication_errors)
        )
    members = _project_members(root)
    snapshot_fingerprint = _snapshot_fingerprint(root, members)
    contents = _archive_contents(root, members, epoch=epoch)
    if _live_snapshot_fingerprint(root, members) != snapshot_fingerprint:
        raise ReleaseBundleError(
            "release inputs changed while the immutable snapshot was assembled"
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=f".{destination.name}.stage-", dir=destination.parent
    ) as raw_stage:
        staged = Path(raw_stage) / destination.name
        _write_archive(staged, contents, epoch=epoch)
        validation = validate_release_bundle(staged, project_root=root)
        if not validation.claim_ready:
            raise ReleaseBundleError(
                "staged release bundle is not live claim-ready:\n"
                + "\n".join(validation.errors)
            )
        if _live_snapshot_fingerprint(root, members) != snapshot_fingerprint:
            raise ReleaseBundleError(
                "release inputs changed before the staged archive could be committed"
            )
        os.replace(staged, destination)
    return destination


def _read_archive(
    archive: Path,
) -> tuple[dict[str, bytes], tuple[tarfile.TarInfo, ...], int, tuple[str, ...]]:
    errors: list[str] = []
    try:
        archive_size = archive.stat().st_size
        with archive.open("rb") as handle:
            header = handle.read(10)
    except OSError as exc:
        return {}, (), 0, (f"cannot read release bundle: {exc}",)
    if archive_size > _MAX_ARCHIVE_BYTES:
        return (
            {},
            (),
            0,
            (f"compressed archive exceeds {_MAX_ARCHIVE_BYTES} bytes",),
        )
    if len(header) < 10 or header[:3] != b"\x1f\x8b\x08":
        return {}, (), 0, ("release bundle is not a gzip stream",)
    flags = header[3]
    epoch = int.from_bytes(header[4:8], "little")
    if flags != 0:
        errors.append("gzip header flags must be zero")
    if header[8] != 2:
        errors.append("gzip header must declare maximum compression")
    if header[9] != 255:
        errors.append("gzip header operating-system byte must be 255")
    members: list[tarfile.TarInfo] = []
    contents: dict[str, bytes] = {}
    names_seen: set[str] = set()
    total_member_bytes = 0
    try:
        with tarfile.open(archive, mode="r|gz") as tar:
            for member in tar:
                members.append(member)
                if len(members) > _MAX_ARCHIVE_MEMBERS:
                    errors.append(
                        f"archive member count exceeds {_MAX_ARCHIVE_MEMBERS}"
                    )
                    break
                if member.name in names_seen:
                    errors.append(f"duplicate archive member: {member.name}")
                names_seen.add(member.name)
                if not _safe_member_name(member.name):
                    errors.append(f"unsafe archive member path: {member.name}")
                if not member.isreg():
                    errors.append(
                        f"archive member is not a regular file: {member.name}"
                    )
                    continue
                if member.size > _MAX_MEMBER_BYTES:
                    errors.append(
                        f"archive member exceeds {_MAX_MEMBER_BYTES} bytes: {member.name}"
                    )
                    break
                total_member_bytes += member.size
                if total_member_bytes > _MAX_TOTAL_MEMBER_BYTES:
                    errors.append(
                        "aggregate archive payload exceeds "
                        f"{_MAX_TOTAL_MEMBER_BYTES} bytes"
                    )
                    break
                extracted = tar.extractfile(member)
                if extracted is None:
                    errors.append(f"cannot read archive member: {member.name}")
                    continue
                data = extracted.read(member.size + 1)
                if len(data) != member.size:
                    errors.append(f"archive member size is inconsistent: {member.name}")
                    continue
                contents.setdefault(member.name, data)
    except (gzip.BadGzipFile, OSError, tarfile.TarError, EOFError) as exc:
        errors.append(f"cannot parse release bundle: {exc}")
    return contents, tuple(members), epoch, tuple(errors)


def _parse_manifest(
    contents: dict[str, bytes], errors: list[str]
) -> dict[str, Any] | None:
    raw = contents.get(MANIFEST_NAME)
    if raw is None:
        errors.append(f"missing required archive member: {MANIFEST_NAME}")
        return None
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"cannot parse {MANIFEST_NAME}: {exc}")
        return None
    if not isinstance(payload, dict):
        errors.append(f"{MANIFEST_NAME} must contain a JSON object")
        return None
    canonical = (
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode()
    if raw != canonical:
        errors.append(f"{MANIFEST_NAME} is not canonical sorted JSON")
    if payload.get("schema_version") != RELEASE_BUNDLE_SCHEMA_VERSION:
        errors.append(
            f"manifest schema_version must be {RELEASE_BUNDLE_SCHEMA_VERSION}"
        )
    if payload.get("kind") != "fep-lean-evidence-bundle":
        errors.append("manifest kind must be fep-lean-evidence-bundle")
    return payload


def _parse_checksums(contents: dict[str, bytes], errors: list[str]) -> dict[str, str]:
    raw = contents.get(CHECKSUMS_NAME)
    if raw is None:
        errors.append(f"missing required archive member: {CHECKSUMS_NAME}")
        return {}
    try:
        text = raw.decode("utf-8")
    except UnicodeError as exc:
        errors.append(f"cannot decode {CHECKSUMS_NAME}: {exc}")
        return {}
    if text and not text.endswith("\n"):
        errors.append(f"{CHECKSUMS_NAME} must end with a newline")
    parsed: dict[str, str] = {}
    for line in text.splitlines():
        match = _CHECKSUM_LINE_RE.fullmatch(line)
        if match is None:
            errors.append(f"malformed checksum line: {line}")
            continue
        digest, name = match.groups()
        if name in parsed:
            errors.append(f"duplicate checksum path: {name}")
            continue
        if not _safe_member_name(name) or name == CHECKSUMS_NAME:
            errors.append(f"unsafe checksum path: {name}")
            continue
        parsed[name] = digest
    if tuple(parsed) != tuple(sorted(parsed)):
        errors.append(f"{CHECKSUMS_NAME} paths must be lexically ordered")
    return parsed


def validate_release_bundle(
    archive_path: Path,
    *,
    project_root: Path | None = None,
) -> ReleaseBundleValidation:
    """Validate archive structure, bytes, and optionally the live checkout.

    Validation never extracts archive members.  Supplying ``project_root``
    additionally binds the archive to the current release inputs; that live
    comparison is implemented by the high-level builder below.
    """
    archive = Path(archive_path)
    contents, members, epoch, read_errors = _read_archive(archive)
    errors = list(read_errors)
    names = tuple(member.name for member in members)
    if names != tuple(sorted(names)):
        errors.append("archive members must be lexically ordered")
    for member in members:
        if member.mode != 0o644:
            errors.append(f"archive member mode must be 0644: {member.name}")
        if member.uid != 0 or member.gid != 0:
            errors.append(f"archive member uid/gid must be zero: {member.name}")
        if member.uname or member.gname:
            errors.append(f"archive member owner names must be empty: {member.name}")
        if member.mtime != epoch:
            errors.append(
                f"archive member mtime differs from gzip mtime: {member.name}"
            )
        if member.pax_headers:
            errors.append(f"archive member carries PAX metadata: {member.name}")

    manifest = _parse_manifest(contents, errors)
    checksums = _parse_checksums(contents, errors)
    manifest_members: dict[str, dict[str, Any]] = {}
    if manifest is not None:
        if manifest.get("source_date_epoch") != epoch:
            errors.append("manifest source_date_epoch differs from gzip mtime")
        if manifest.get("external_full_mode") != {
            "artifacts": [],
            "authorized": False,
            "current": False,
        }:
            errors.append("manifest external_full_mode must be explicitly unavailable")
        raw_members = manifest.get("members")
        if not isinstance(raw_members, list):
            errors.append("manifest members must be a list")
        else:
            for record in raw_members:
                if not isinstance(record, dict):
                    errors.append("manifest members must contain objects")
                    continue
                name = record.get("path")
                if not isinstance(name, str) or not _safe_member_name(name):
                    errors.append(f"manifest member has unsafe path: {name}")
                    continue
                if name in {MANIFEST_NAME, CHECKSUMS_NAME}:
                    errors.append(f"manifest payload cannot include {name}")
                    continue
                if name in manifest_members:
                    errors.append(f"duplicate manifest member: {name}")
                    continue
                if set(record) != {"path", "sha256", "size", "evidence_class"}:
                    errors.append(f"manifest member fields are invalid: {name}")
                evidence_class = record.get("evidence_class")
                if not isinstance(evidence_class, str) or not evidence_class:
                    errors.append(f"manifest member evidence class is invalid: {name}")
                expected_class = _expected_evidence_class(name)
                if expected_class is None:
                    errors.append(f"manifest member path is not release-owned: {name}")
                elif evidence_class != expected_class:
                    errors.append(
                        "manifest member evidence class is invalid for its path: "
                        f"{name}"
                    )
                if _is_provider_member(name):
                    errors.append(f"provider artifact is forbidden: {name}")
                manifest_members[name] = record
            if tuple(manifest_members) != tuple(sorted(manifest_members)):
                errors.append("manifest members must be lexically ordered")

        if manifest.get("catalogue") != {
            "areas": RELEASE_SEAL["areas"],
            "families": RELEASE_SEAL["families"],
            "first_id": RELEASE_SEAL["first_id"],
            "last_id": RELEASE_SEAL["last_id"],
            "topics": RELEASE_SEAL["topics"],
        }:
            errors.append(
                "manifest catalogue does not match the 155-topic release seal"
            )
        formalism = manifest.get("formalism")
        if not isinstance(formalism, dict):
            errors.append("manifest formalism summary must be an object")
        else:
            for key, expected in (
                ("relations", RELEASE_SEAL["relations"]),
                ("capabilities", RELEASE_SEAL["capabilities"]),
                ("numerical_witnesses", RELEASE_SEAL["witnesses"]),
            ):
                if formalism.get(key) != expected:
                    errors.append(f"manifest formalism.{key} is stale")
            formal_modules = formalism.get("formal_modules")
            if type(formal_modules) is not int or formal_modules <= 0:
                errors.append("manifest formalism.formal_modules must be positive")
        toolchain = manifest.get("toolchain")
        if not isinstance(toolchain, dict):
            errors.append("manifest toolchain identity must be an object")
        else:
            lean_toolchain = toolchain.get("lean_toolchain")
            lean_version = toolchain.get("lean_version")
            mathlib_tag = toolchain.get("mathlib_tag")
            mathlib_revision = toolchain.get("mathlib_revision")
            toolchain_match = (
                re.fullmatch(r"leanprover/lean4:v(\d+\.\d+\.\d+)", lean_toolchain)
                if isinstance(lean_toolchain, str)
                else None
            )
            version_match = (
                re.match(r"Lean \(version (\d+\.\d+\.\d+)(?:,|\))", lean_version)
                if isinstance(lean_version, str)
                else None
            )
            mathlib_match = (
                re.fullmatch(r"v(\d+\.\d+\.\d+)", mathlib_tag)
                if isinstance(mathlib_tag, str)
                else None
            )
            if toolchain_match is None:
                errors.append("manifest Lean toolchain is not a stable semantic pin")
            if version_match is None:
                errors.append("manifest Lean version is not actual compiler output")
            if mathlib_match is None:
                errors.append("manifest Mathlib tag is not a stable semantic pin")
            if (
                toolchain_match is not None
                and version_match is not None
                and toolchain_match.group(1) != version_match.group(1)
            ):
                errors.append("manifest Lean version does not match its toolchain pin")
            if (
                toolchain_match is not None
                and mathlib_match is not None
                and toolchain_match.group(1) != mathlib_match.group(1)
            ):
                errors.append("manifest Mathlib tag does not match the Lean pin")
            if (
                not isinstance(mathlib_revision, str)
                or _GIT_SHA_RE.fullmatch(mathlib_revision) is None
            ):
                errors.append("manifest Mathlib revision is not a lowercase Git SHA")
        for digest_name in ("source_sha256", "config_sha256"):
            digest = manifest.get(digest_name)
            if not isinstance(digest, str) or _SHA256_RE.fullmatch(digest) is None:
                errors.append(f"manifest {digest_name} is invalid")
        lean_sources = manifest.get("manifested_lean_sources")
        if (
            not isinstance(lean_sources, list)
            or not lean_sources
            or any(not isinstance(name, str) for name in lean_sources)
            or lean_sources != sorted(set(lean_sources))
        ):
            errors.append("manifested Lean source roster is invalid")
            lean_sources = []
        for name in lean_sources:
            if name not in manifest_members or not name.endswith(".lean"):
                errors.append(f"manifested Lean source is missing or invalid: {name}")

        for required in sorted(_STATIC_REQUIRED_BUNDLE_PATHS - set(manifest_members)):
            errors.append(f"required release payload is omitted: {required}")
        if not any(
            name.startswith("output/manuscript/") and name.endswith(".md")
            for name in manifest_members
        ):
            errors.append("rendered manuscript Markdown tree is omitted")

        evidence = manifest.get("evidence")
        expected_evidence = {
            "native_lean": "output/native-verification.json",
            "declaration_axiom_audit": "output/formalism-audit.json",
            "browser_interaction": BROWSER_RECEIPT.as_posix(),
            "numerical_witnesses": NUMERICAL_RECEIPT.as_posix(),
            "python_tests": PYTEST_RECEIPT.as_posix(),
            "python_coverage": PYTHON_COVERAGE_RECEIPT.as_posix(),
            "python_acceptance": PYTHON_ACCEPTANCE_RECEIPT.as_posix(),
        }
        if not isinstance(evidence, dict) or set(evidence) != set(expected_evidence):
            errors.append("manifest evidence roster is not canonical")
        else:
            for key, expected_path in expected_evidence.items():
                record = evidence.get(key)
                if (
                    not isinstance(record, dict)
                    or record.get("current") is not True
                    or record.get("path") != expected_path
                ):
                    errors.append(f"manifest evidence record is invalid: {key}")
                    continue
                digest = record.get("sha256")
                manifest_member_record = manifest_members.get(expected_path)
                if (
                    not isinstance(digest, str)
                    or manifest_member_record is None
                    or digest != manifest_member_record.get("sha256")
                ):
                    errors.append(f"manifest evidence hash is invalid: {key}")
            numerical_record = evidence.get("numerical_witnesses")
            if (
                isinstance(numerical_record, dict)
                and numerical_record.get("evidence_kind") != NON_PROOF_EVIDENCE
            ):
                errors.append("manifest numerical evidence boundary was weakened")

    expected_names = set(manifest_members) | {MANIFEST_NAME, CHECKSUMS_NAME}
    actual_names = set(contents)
    for name in sorted(expected_names - actual_names):
        errors.append(f"missing required archive member: {name}")
    for name in sorted(actual_names - expected_names):
        errors.append(f"unexpected archive member: {name}")
    for name in sorted(actual_names):
        if _is_provider_member(name):
            errors.append(f"provider artifact is forbidden: {name}")
    expected_checksum_names = set(manifest_members) | {MANIFEST_NAME}
    for name in sorted(expected_checksum_names - set(checksums)):
        errors.append(f"missing checksum: {name}")
    for name in sorted(set(checksums) - expected_checksum_names):
        errors.append(f"unexpected checksum: {name}")
    for name in sorted(expected_checksum_names & set(checksums) & set(contents)):
        if checksums[name] != _sha256(contents[name]):
            errors.append(f"checksum mismatch: {name}")
    for name, record in manifest_members.items():
        digest = record.get("sha256")
        size = record.get("size")
        if not isinstance(digest, str) or _SHA256_RE.fullmatch(digest) is None:
            errors.append(f"manifest member has invalid sha256: {name}")
        elif name in contents and digest != _sha256(contents[name]):
            errors.append(f"manifest hash mismatch: {name}")
        if type(size) is not int or size < 0:
            errors.append(f"manifest member has invalid size: {name}")
        elif name in contents and size != len(contents[name]):
            errors.append(f"manifest size mismatch: {name}")

    if not errors:
        try:
            with tempfile.TemporaryDirectory(prefix="fep-lean-archive-check-") as raw:
                normalized = Path(raw) / "normalized.tar.gz"
                _write_archive(normalized, contents, epoch=epoch)
                if normalized.read_bytes() != archive.read_bytes():
                    errors.append(
                        "archive bytes are not the canonical normalized USTAR/gzip encoding"
                    )
        except (OSError, ValueError) as exc:
            errors.append(f"cannot reproduce normalized archive bytes: {exc}")

    if project_root is not None and manifest is not None:
        root = Path(project_root).resolve()
        errors.extend(
            release_bundle_prerequisite_errors(
                root,
                source_date_epoch=epoch,
                include_publication=True,
            )
        )
        try:
            expected_members = _project_members(root)
            expected_fingerprint = _snapshot_fingerprint(root, expected_members)
            expected_contents = _archive_contents(root, expected_members, epoch=epoch)
        except (OSError, TypeError, ValueError) as exc:
            errors.append(f"live release inputs cannot be loaded: {exc}")
        else:
            for name in sorted(set(expected_contents) - set(contents)):
                errors.append(f"archive is missing a current project member: {name}")
            for name in sorted(set(contents) - set(expected_contents)):
                errors.append(f"archive contains a non-current project member: {name}")
            for name in sorted(set(contents) & set(expected_contents)):
                if contents[name] != expected_contents[name]:
                    errors.append(
                        f"archive member differs from the live project: {name}"
                    )
            try:
                current_fingerprint = _live_snapshot_fingerprint(root, expected_members)
            except (OSError, TypeError, ValueError) as exc:
                errors.append(f"live release inputs cannot be rechecked: {exc}")
            else:
                if current_fingerprint != expected_fingerprint:
                    errors.append("live release inputs changed during validation")
    unique_errors = tuple(dict.fromkeys(errors))
    try:
        archive_digest = (
            _sha256(archive.read_bytes())
            if archive.stat().st_size <= _MAX_ARCHIVE_BYTES
            else ""
        )
    except OSError:
        archive_digest = ""
    return ReleaseBundleValidation(
        valid=not unique_errors,
        source_bound=project_root is not None and not unique_errors,
        claim_ready=project_root is not None and not unique_errors,
        errors=unique_errors,
        archive_sha256=archive_digest,
        member_count=len(members),
        manifest=manifest,
    )


__all__ = [
    "CHECKSUMS_NAME",
    "MANIFEST_NAME",
    "PUBLICATION_HTML",
    "PUBLICATION_PDF",
    "RELEASE_BUNDLE_SCHEMA_VERSION",
    "RENDERER_PROVENANCE",
    "PublicationManuscript",
    "ReleaseBundleError",
    "ReleaseBundleValidation",
    "build_numerical_witness_receipt",
    "build_python_acceptance_receipt",
    "build_release_bundle",
    "publication_manuscript_errors",
    "release_bundle_prerequisite_errors",
    "render_publication_manuscript",
    "run_python_acceptance",
    "validate_release_bundle",
    "write_publication_manuscript",
]
