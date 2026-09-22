"""Deterministic manuscript rendering and publication-set replacement."""

import hashlib
import os
import re
import shlex
import shutil
import subprocess
import tempfile
from collections.abc import (
    Mapping,
    Sequence,
)
from pathlib import Path
from typing import Any

import yaml

from fep_lean.output import release_bundle as bundle
from fep_lean.output.fsutil import (
    atomic_write_bytes,
    sha256_bytes,
    sha256_file,
)
from fep_lean.output.publication_metadata import (
    GraphicalAbstractAsset,
    PublicationMetadataError,
    load_graphical_abstract,
)
from fep_lean.output.release_bundle._constants import (
    _MANUSCRIPT_FIGURE_REFERENCES,
    _MARKDOWN_IMAGE_RE,
    _PANDOC_TIMEOUT_SECONDS,
    _PDF_ID_RE,
    _PDF_TIMEOUT_SECONDS,
    _RESOURCE_MARKUP_RE,
    PUBLICATION_HTML,
    PUBLICATION_PDF,
    RENDERER_PROVENANCE,
)
from fep_lean.output.release_bundle._core import (
    PublicationManuscript,
    ReleaseBundleError,
    _canonical_json,
    _digest_named_bytes,
    _relative_file_bytes,
    _source_date_epoch,
)
from fep_lean.output.rendering import render_manuscript


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
        "binary_sha256": sha256_file(resolved),
    }


def _manuscript_inputs(project_root: Path) -> tuple[Path, ...]:
    root = Path(project_root)
    rendered_root = root / "output" / "manuscript"
    rendered = tuple(
        rendered_root / source.name
        for source in bundle.manuscript_source_files(root / "manuscript")
    )
    return (*rendered, root / "manuscript" / "09z_unified_formalism_catalogue.md")


def _manuscript_source_records(
    project_root: Path,
) -> tuple[tuple[str, bytes], ...]:
    """Capture authored manuscript inputs through the canonical file boundary."""
    root = Path(project_root).resolve()
    records: list[tuple[str, bytes]] = []
    for path in bundle.manuscript_source_files(root / "manuscript"):
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
        set(bundle.MANUSCRIPT_ASSETS)
        | {
            destination.as_posix()
            for _source, destination in bundle.MANUSCRIPT_ASSETS.values()
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
    ) in bundle.MANUSCRIPT_ASSETS.items():
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
    for _source, destination in bundle.MANUSCRIPT_ASSETS.values():
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
            completed = bundle._run_renderer(
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
                normalizer_result = bundle._run_renderer(
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
        bundle._publication_resource_records(root)
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
    resource_records = bundle._publication_resource_records(root)
    input_records = _canonical_renderer_input_records(root, resource_records)
    pandoc = shutil.which("pandoc")
    if pandoc is None:
        raise ReleaseBundleError("pandoc is required for the self-contained HTML")
    pandoc_identity = bundle._tool_identity(pandoc)
    base_command = _pandoc_base_command(root, pandoc)
    html, html_status = bundle._render_twice(
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
    pdf_renderer = bundle._tool_identity(xelatex) if xelatex is not None else None
    rsvg_renderer = (
        bundle._tool_identity(rsvg_convert) if rsvg_convert is not None else None
    )
    mutool_renderer = bundle._tool_identity(mutool) if mutool is not None else None
    if xelatex is not None and mutool is None:
        pdf_status = "mutool_unavailable"
    elif xelatex is not None:
        preamble = _latex_preamble(root)
        pdf, pdf_status = bundle._render_twice(
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

    final_resource_records = bundle._publication_resource_records(root)
    if _canonical_renderer_input_records(root, final_resource_records) != input_records:
        raise ReleaseBundleError("manuscript renderer inputs changed during rendering")
    source_digest = _digest_named_bytes(input_records)
    provenance: dict[str, Any] = {
        "schema_version": 1,
        "kind": "deterministic-manuscript-render",
        "source_date_epoch": epoch,
        "source_sha256": source_digest,
        "inputs": [
            {"path": path, "sha256": sha256_bytes(data), "size": len(data)}
            for path, data in sorted(input_records)
        ],
        "html": {
            "current": True,
            "path": PUBLICATION_HTML.as_posix(),
            "sha256": sha256_bytes(html),
            "size": len(html),
            "status": html_status,
        },
        "pdf": {
            "current": pdf is not None,
            "path": PUBLICATION_PDF.as_posix() if pdf is not None else "",
            "sha256": sha256_bytes(pdf) if pdf is not None else "",
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
    rendered = bundle.render_publication_manuscript(
        root, source_date_epoch=source_date_epoch
    )
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
            atomic_write_bytes(new_root / relative.name, data)

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
        expected = bundle.render_publication_manuscript(
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
