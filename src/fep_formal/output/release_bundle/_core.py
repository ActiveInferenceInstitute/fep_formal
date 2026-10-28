"""Shared models, errors, and canonical helpers for the release bundle."""

from __future__ import annotations

import contextlib
import hashlib
import json
import math
import os
import re
import stat
import subprocess
import sys
import time
from collections.abc import (
    Mapping,
    Sequence,
)
from dataclasses import dataclass
from pathlib import (
    Path,
    PurePosixPath,
)
from typing import Any, Protocol

from fep_formal._paths import FepFormalError
from fep_formal.output.fsutil import sha256_bytes
from fep_formal.output.release_bundle._constants import (
    _PROVIDER_MEMBER_PREFIXES,
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


class ReleaseBundleError(ValueError, FepFormalError):
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


def _json_object(path: Path, label: str) -> tuple[dict[str, Any] | None, str | None]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return None, f"cannot read {label}: {exc}"
    if not isinstance(payload, dict):
        return None, f"{label} must contain a JSON object"
    return payload, None


@dataclass(frozen=True)
class PublicationCaptureStage:
    """One explicit producer/check pair and its exact consumed file roster.

    Paths are absolute, except output paths may start with ``{attempt}/``.
    Commands are argument arrays; only whole-argument attempt placeholders expand.
    A custom roster records its own checks and never becomes publication evidence
    merely because its processes exit successfully.
    """

    name: str
    dependencies: tuple[str, ...]
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    command: tuple[str, ...]
    check_command: tuple[str, ...]
    timeout_s: float
    input_rosters: tuple[tuple[str, tuple[str, ...]], ...] = ()
    resource_links: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class PublicationCapturePlan:
    """A process-free, immutable execution policy for an explicit capture."""

    project_root: str
    stages: tuple[PublicationCaptureStage, ...]
    timeout_s: float = 21600
    kind: str = "custom-evidence-capture"

    def record(self) -> dict[str, Any]:
        return {
            "project_root": self.project_root,
            "kind": self.kind,
            "execution_platform": "posix",
            "timeout_s": self.timeout_s,
            "stages": [
                {
                    "name": s.name,
                    "dependencies": list(s.dependencies),
                    "inputs": list(s.inputs),
                    "outputs": list(s.outputs),
                    "command": list(s.command),
                    "check_command": list(s.check_command),
                    "timeout_s": s.timeout_s,
                    "input_rosters": [
                        {"directory": directory, "files": list(files)}
                        for directory, files in s.input_rosters
                    ],
                    "resource_links": [
                        {"path": path, "target": target}
                        for path, target in s.resource_links
                    ],
                }
                for s in self.stages
            ],
        }


@dataclass(frozen=True)
class PublicationCaptureResult:
    """Local capture outcome; completion does not publish or certify a provider."""

    complete: bool
    journal: Path
    accepted_stages: tuple[str, ...]
    reused_stages: tuple[str, ...]
    failed_stage: str | None
    errors: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        """Canonical local-capture JSON fields; no publication acceptance."""
        return {
            "status": "ok" if self.complete else "error",
            "complete": self.complete,
            "journal": str(self.journal),
            "accepted_stages": self.accepted_stages,
            "reused_stages": self.reused_stages,
            "failed_stage": self.failed_stage,
            "errors": self.errors,
            "evidence_plane": "local capture; no provider, hosted CI or publication action",
        }


def _capture_parent_fd(path: Path, *, create: bool = False) -> int:
    if os.name != "posix":
        raise ReleaseBundleError(
            "capture custody requires POSIX descriptor-relative reads"
        )
    directory_fd = os.open(path.anchor, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in path.parts[1:-1]:
            try:
                next_fd = os.open(
                    part,
                    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                    dir_fd=directory_fd,
                )
            except FileNotFoundError:
                if not create:
                    raise
                with contextlib.suppress(FileExistsError):
                    os.mkdir(part, 0o700, dir_fd=directory_fd)
                next_fd = os.open(
                    part,
                    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                    dir_fd=directory_fd,
                )
            os.close(directory_fd)
            directory_fd = next_fd
        return directory_fd
    except BaseException:
        os.close(directory_fd)
        raise


def _capture_mkdir(path: Path, *, parents: bool = False) -> None:
    directory_fd = _capture_parent_fd(path, create=parents)
    try:
        os.mkdir(path.name, 0o700, dir_fd=directory_fd)
    finally:
        os.close(directory_fd)


def _capture_regular_file(path: Path) -> bytes:
    if not path.is_absolute() or path.resolve() != path:
        raise ReleaseBundleError("capture file path must be canonical and absolute")
    if any(parent.is_symlink() for parent in (path, *path.parents)):
        raise ReleaseBundleError(f"capture file traverses a symlink: {path}")
    if not path.is_file():
        raise ReleaseBundleError(f"capture input or artifact is missing: {path}")
    directory_fd = _capture_parent_fd(path)
    file_fd = None
    try:
        # A pathname can become a FIFO after the lexical checks. Refuse its
        # descriptor type before any potentially blocking read/open handshake.
        file_fd = os.open(
            path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory_fd
        )
        before = os.fstat(file_fd)
        if not stat.S_ISREG(before.st_mode):
            raise ReleaseBundleError("capture input or artifact must be a regular file")
        with os.fdopen(file_fd, "rb") as stream:
            file_fd = None
            data = stream.read(before.st_size + 1)
            after = os.fstat(stream.fileno())

        def identity(value: os.stat_result) -> tuple[int, ...]:
            return (
                value.st_dev,
                value.st_ino,
                value.st_mode,
                value.st_size,
                value.st_mtime_ns,
                value.st_ctime_ns,
            )

        if identity(before) != identity(after) or len(data) != before.st_size:
            raise ReleaseBundleError("capture file changed while reading")
        return data
    finally:
        if file_fd is not None:
            os.close(file_fd)
        os.close(directory_fd)


def _capture_snapshot(paths: Sequence[str]) -> dict[str, str]:
    return {name: sha256_bytes(_capture_regular_file(Path(name))) for name in paths}


_CAPTURE_EXCLUDED_DIRECTORIES = frozenset(
    {".git", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
)


def _capture_link_bytes(path: Path, target: str, owner: Path) -> bytes:
    """Bind a declared link, its resolved identity and owned ancestry.

    Runtime acquisition precedes sealing. Cache contents may change, but moving
    or adding directory entries at an owned ancestor invalidates this capture.
    Shared ancestors above the resource owner bind identity, not timestamps.
    """
    if os.name != "posix":
        raise ReleaseBundleError(
            "capture resource links require POSIX descriptor custody"
        )
    if (
        not path.is_absolute()
        or not path.is_relative_to(owner)
        or path == owner
        or not target
        or "\x00" in target
    ):
        raise ReleaseBundleError("capture resource link is invalid")
    descriptors = [os.open(path.anchor, os.O_RDONLY | os.O_DIRECTORY)]
    states: list[tuple[str, os.stat_result]] = [(path.anchor, os.fstat(descriptors[0]))]
    current = Path(path.anchor)
    try:
        for part in path.parts[1:-1]:
            child = os.open(
                part,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                dir_fd=descriptors[-1],
            )
            descriptors.append(child)
            current /= part
            states.append((str(current), os.fstat(child)))
        before = os.stat(path.name, dir_fd=descriptors[-1], follow_symlinks=False)
        raw = os.readlink(path.name, dir_fd=descriptors[-1])
        canonical = Path(os.path.normpath(str(path.parent / target)))
        target_parent = _capture_parent_fd(canonical)
        try:
            canonical_before = os.stat(
                canonical.name, dir_fd=target_parent, follow_symlinks=False
            )
            referent_before = os.stat(
                path.name, dir_fd=descriptors[-1], follow_symlinks=True
            )
            canonical_after = os.stat(
                canonical.name, dir_fd=target_parent, follow_symlinks=False
            )
            referent_after = os.stat(
                path.name, dir_fd=descriptors[-1], follow_symlinks=True
            )
        finally:
            os.close(target_parent)
        after = os.stat(path.name, dir_fd=descriptors[-1], follow_symlinks=False)

        def identity(value: os.stat_result) -> tuple[int, ...]:
            return (
                value.st_dev,
                value.st_ino,
                value.st_mode,
                value.st_size,
                value.st_mtime_ns,
                value.st_ctime_ns,
            )

        if (
            not stat.S_ISLNK(before.st_mode)
            or raw != target
            or identity(before) != identity(after)
        ):
            raise ReleaseBundleError("capture resource link changed")

        def referent_identity(value: os.stat_result) -> tuple[int, ...]:
            return (value.st_dev, value.st_ino, stat.S_IFMT(value.st_mode))

        referent = referent_identity(canonical_before)
        if not (
            stat.S_ISREG(canonical_before.st_mode)
            or stat.S_ISDIR(canonical_before.st_mode)
        ) or any(
            referent_identity(value) != referent
            for value in (canonical_after, referent_before, referent_after)
        ):
            raise ReleaseBundleError("capture resource link referent changed")
        ancestry = []
        for fd, (name, state) in zip(descriptors, states, strict=True):
            final = os.fstat(fd)
            owned = Path(name).is_relative_to(owner)
            initial_fields = (
                state.st_dev,
                state.st_ino,
                stat.S_IFMT(state.st_mode),
                *((state.st_mtime_ns, state.st_ctime_ns) if owned else ()),
            )
            final_fields = (
                final.st_dev,
                final.st_ino,
                stat.S_IFMT(final.st_mode),
                *((final.st_mtime_ns, final.st_ctime_ns) if owned else ()),
            )
            if initial_fields != final_fields:
                raise ReleaseBundleError("capture resource link ancestry changed")
            ancestry.append({"path": name, "identity": initial_fields})
        return _canonical_json(
            {
                "target": raw,
                "identity": identity(before),
                "referent_identity": referent,
                "ancestry": ancestry,
            }
        )
    except OSError as exc:
        raise ReleaseBundleError("cannot capture the declared resource link") from exc
    finally:
        for fd in reversed(descriptors):
            os.close(fd)


def _capture_directory_paths(
    directory: Path, *, resource_links: tuple[tuple[str, str], ...] = ()
) -> tuple[str, ...]:
    """Seal all regular resources, excluding only declared caches and bytecode."""
    if (
        not directory.is_absolute()
        or directory.resolve() != directory
        or not directory.is_dir()
    ):
        raise ReleaseBundleError("capture input directory must be canonical and exist")
    paths = []
    links = {
        name: target
        for name, target in resource_links
        if Path(name).is_relative_to(directory)
    }
    seen_links = set()
    for path in sorted(directory.rglob("*")):
        relative = path.relative_to(directory)
        if {
            part.casefold() for part in relative.parts
        } & _CAPTURE_EXCLUDED_DIRECTORIES or path.suffix.casefold() in {
            ".pyc",
            ".pyo",
        }:
            continue
        if path.is_symlink():
            if str(path) not in links:
                raise ReleaseBundleError(
                    "capture input directory contains an undeclared symlink"
                )
            _capture_link_bytes(path, links[str(path)], directory)
            paths.append(str(path))
            seen_links.add(str(path))
            continue
        if path.is_file():
            paths.append(str(path))
        elif not path.is_dir():
            raise ReleaseBundleError(
                "capture input directory contains a nonregular resource"
            )
    if seen_links != set(links):
        raise ReleaseBundleError("capture resource link membership changed")
    return tuple(sorted(paths))


def _capture_check_rosters(stage: PublicationCaptureStage) -> None:
    for directory, files in stage.input_rosters:
        if (
            _capture_directory_paths(
                Path(directory), resource_links=stage.resource_links
            )
            != files
        ):
            raise ReleaseBundleError("capture input directory membership changed")


def _capture_stage_snapshot(stage: PublicationCaptureStage) -> dict[str, str]:
    _capture_check_rosters(stage)
    links = dict(stage.resource_links)
    snapshot = _capture_snapshot(
        tuple(name for name in stage.inputs if name not in links)
    )
    for name, target in stage.resource_links:
        owners = [
            Path(directory) for directory, files in stage.input_rosters if name in files
        ]
        if len(owners) != 1:
            raise ReleaseBundleError("capture resource link needs one explicit owner")
        snapshot[name] = sha256_bytes(
            _capture_link_bytes(Path(name), target, owners[0])
        )
    _capture_check_rosters(stage)
    return snapshot


def _capture_resource_link_target(
    path: Path, raw_target: str, owner: Path, project_root: Path
) -> Path:
    """Permit direct internal owners and one exact active-project registration."""
    raw_parts = raw_target.split("/")
    if raw_target.startswith("/"):
        if Path(raw_target).as_posix() != raw_target or ".." in raw_parts:
            raise ReleaseBundleError("capture resource link target spelling is invalid")
    else:
        parents = 0
        while parents < len(raw_parts) and raw_parts[parents] == "..":
            parents += 1
        if parents > len(path.parent.relative_to(owner).parts) or any(
            part in {"", ".", ".."} for part in raw_parts[parents:]
        ):
            raise ReleaseBundleError("capture resource link target spelling is invalid")
    target = Path(os.path.normpath(str(path.parent / raw_target)))
    registered = (
        path == owner / "projects/active/fep_lean"
        and raw_target == str(project_root)
        and target == project_root
    )
    if not registered and not target.is_relative_to(owner):
        raise ReleaseBundleError("capture resource link escapes its owner")
    if not registered and (
        {part.casefold() for part in target.relative_to(owner).parts}
        & _CAPTURE_EXCLUDED_DIRECTORIES
        or target.suffix.casefold() in {".pyc", ".pyo"}
    ):
        raise ReleaseBundleError("capture resource link targets an excluded subtree")
    try:
        if (
            path.resolve(strict=True) != target
            or target.resolve(strict=True) != target
            or any(parent.is_symlink() for parent in (target, *target.parents))
        ):
            raise ReleaseBundleError(
                "capture resource link target must be a direct canonical owner"
            )
        if not target.is_file() and not target.is_dir():
            raise ReleaseBundleError("capture resource link target is nonregular")
    except (OSError, RuntimeError) as exc:
        raise ReleaseBundleError(
            "capture resource link target is missing or cyclic"
        ) from exc
    return target


def _capture_template_links(
    template: Path, project_root: Path
) -> tuple[tuple[str, str], ...]:
    links = []
    for path in sorted(template.rglob("*")):
        relative = path.relative_to(template)
        if {
            part.casefold() for part in relative.parts
        } & _CAPTURE_EXCLUDED_DIRECTORIES or path.suffix.casefold() in {".pyc", ".pyo"}:
            continue
        if path.is_symlink():
            raw = os.readlink(path)
            _capture_resource_link_target(path, raw, template, project_root)
            _capture_link_bytes(path, raw, template)
            links.append((str(path), raw))
    return tuple(sorted(links))


def _capture_validate_resource_links(
    stage: PublicationCaptureStage, project_root: Path
) -> None:
    if (
        type(stage.resource_links) is not tuple
        or any(
            type(entry) is not tuple
            or len(entry) != 2
            or any(
                type(value) is not str or not value or "\x00" in value
                for value in entry
            )
            for entry in stage.resource_links
        )
        or tuple(sorted(set(stage.resource_links))) != stage.resource_links
        or len({name for name, _target in stage.resource_links})
        != len(stage.resource_links)
    ):
        raise ReleaseBundleError("capture resource link roster is invalid")
    for name, raw in stage.resource_links:
        path = Path(name)
        owners = [
            Path(directory) for directory, files in stage.input_rosters if name in files
        ]
        if (
            not path.is_absolute()
            or ".." in path.parts
            or len(owners) != 1
            or name not in stage.inputs
            or name in stage.outputs
        ):
            raise ReleaseBundleError(
                "capture resource link needs one sealed input owner"
            )
        owner = owners[0]
        if not path.is_relative_to(owner) or path == owner:
            raise ReleaseBundleError(
                "capture resource link needs one containing input owner"
            )
        target = _capture_resource_link_target(path, raw, owner, project_root)
        _capture_link_bytes(path, raw, owner)
        if target == project_root and path == owner / "projects/active/fep_lean":
            continue
        target_files = (
            (str(target),) if target.is_file() else _capture_directory_paths(target)
        )
        if not set(target_files) <= set(stage.inputs):
            raise ReleaseBundleError(
                "capture resource link target owners are not sealed"
            )


def _capture_output_path(name: str, attempt: Path) -> Path:
    if name.startswith("{attempt}/"):
        relative = name.removeprefix("{attempt}/")
        if not _safe_member_name(relative):
            raise ReleaseBundleError("capture attempt artifact path is unsafe")
        return attempt / relative
    return Path(name)


def _capture_new_file(path: Path, data: bytes) -> None:
    if not path.is_absolute() or path.resolve() != path:
        raise ReleaseBundleError("capture journal path must be canonical and absolute")
    if any(parent.is_symlink() for parent in (path, *path.parents)):
        raise ReleaseBundleError("capture journal must not traverse a symlink")
    directory_fd = _capture_parent_fd(path, create=True)
    file_fd = None
    try:
        file_fd = os.open(
            path.name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600,
            dir_fd=directory_fd,
        )
        with os.fdopen(file_fd, "wb") as stream:
            file_fd = None
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
            os.fchmod(stream.fileno(), 0o444)
    finally:
        if file_fd is not None:
            os.close(file_fd)
        os.close(directory_fd)


def _capture_validate_plan(plan: PublicationCapturePlan) -> None:
    root = Path(plan.project_root)
    if not root.is_absolute() or root.resolve() != root or not root.is_dir():
        raise ReleaseBundleError("capture requires a canonical existing project root")
    seen: set[str] = set()
    if not plan.stages or len(plan.stages) > 32:
        raise ReleaseBundleError("capture requires between one and 32 stages")
    for bound in (plan.timeout_s, *(s.timeout_s for s in plan.stages)):
        if (
            type(bound) not in (int, float)
            or not math.isfinite(bound)
            or not 0 < bound <= 86400
        ):
            raise ReleaseBundleError("capture deadlines must be finite and bounded")
    for stage in plan.stages:
        if (
            not re.fullmatch(r"[a-z][a-z0-9-]{0,31}", stage.name)
            or stage.name in seen
            or len(set(stage.dependencies)) != len(stage.dependencies)
            or not set(stage.dependencies) <= seen
        ):
            raise ReleaseBundleError(
                "capture stage graph must be unique and topological"
            )
        seen.add(stage.name)
        if not stage.inputs or not stage.outputs:
            raise ReleaseBundleError(
                "capture stages require explicit inputs and artifacts"
            )
        _capture_validate_resource_links(stage, root)
        resource_link_names = {name for name, _target in stage.resource_links}
        for paths in (stage.inputs, stage.outputs):
            if len(set(paths)) != len(paths):
                raise ReleaseBundleError("capture paths must be unique")
            for name in paths:
                if name.startswith("{attempt}/") and paths is stage.outputs:
                    _capture_output_path(name, root)
                elif not Path(name).is_absolute() or (
                    Path(name).resolve() != Path(name)
                    and not (paths is stage.inputs and name in resource_link_names)
                ):
                    raise ReleaseBundleError(
                        "capture paths must be canonical and absolute"
                    )
        if set(stage.inputs) & set(stage.outputs):
            raise ReleaseBundleError(
                "capture source inputs cannot also be producer outputs"
            )
        if len({directory for directory, _ in stage.input_rosters}) != len(
            stage.input_rosters
        ):
            raise ReleaseBundleError("capture input directory rosters must be unique")
        for directory, files in stage.input_rosters:
            parent = Path(directory)
            if (
                not parent.is_absolute()
                or parent.resolve() != parent
                or tuple(sorted(set(files))) != files
                or not set(files) <= set(stage.inputs)
                or any(
                    not Path(name).is_relative_to(parent)
                    or (
                        Path(name).resolve() != Path(name)
                        and name not in resource_link_names
                    )
                    for name in files
                )
            ):
                raise ReleaseBundleError("capture input directory roster is invalid")
        for command in (stage.command, stage.check_command):
            if not command or any(
                type(arg) is not str or not arg or "\x00" in arg for arg in command
            ):
                raise ReleaseBundleError(
                    "capture commands require nonempty argument arrays"
                )


def _capture_read_json(path: Path) -> dict[str, Any]:
    from fep_formal.verification._jsonutil import load_strict_json

    try:
        value = load_strict_json(_capture_regular_file(path).decode())
    except (UnicodeError, ValueError) as exc:
        raise ReleaseBundleError("capture journal JSON is malformed") from exc
    if type(value) is not dict:
        raise ReleaseBundleError("capture journal record must be an object")
    return value


class _CaptureProcessRunner(Protocol):
    def __call__(
        self,
        command: Sequence[str],
        *,
        cwd: str | os.PathLike[str],
        env: Mapping[str, str],
        timeout: float,
    ) -> subprocess.CompletedProcess[str]: ...


@dataclass(frozen=True)
class _CaptureAttemptOutcome:
    before: dict[str, str]
    after: dict[str, str]
    errors: tuple[str, ...]
    timed_out: bool


def _capture_read_history(
    attempts: Path,
    stage_by_name: dict[str, PublicationCaptureStage],
    policy_digest: str,
) -> tuple[dict[str, tuple[Path, dict[str, Any]]], int]:
    """Validate every retained byte before offering accepted stages for reuse."""
    previous: dict[str, tuple[Path, dict[str, Any]]] = {}
    known_artifacts: dict[str, dict[str, Any]] = {}
    number = 0
    for attempt in sorted(attempts.iterdir()):
        match = re.fullmatch(r"([0-9]{6})-([a-z][a-z0-9-]{0,31})", attempt.name)
        if attempt.is_symlink() or not attempt.is_dir() or match is None:
            raise ReleaseBundleError("capture attempt path is invalid")
        ordinal, stage_name = int(match[1]), match[2]
        if ordinal != number + 1 or stage_name not in stage_by_name:
            raise ReleaseBundleError("capture attempt sequence or stage is invalid")
        number = ordinal
        intent = _capture_read_json(attempt / "intent.json")
        if type(intent.get("schema_version")) is not int or intent != {
            "schema_version": 1,
            "stage": stage_name,
            "policy_sha256": policy_digest,
        }:
            raise ReleaseBundleError("capture attempt intent differs from its policy")
        if not (attempt / "result.json").exists():
            # A killed parent leaves an immutable incomplete attempt, not approval.
            if any(p.is_symlink() for p in attempt.rglob("*")):
                raise ReleaseBundleError(
                    "incomplete capture attempt contains a symlink"
                )
            continue
        record = _capture_read_json(attempt / "result.json")
        fields = {
            "schema_version",
            "stage",
            "policy_sha256",
            "mode",
            "artifact_attempt",
            "accepted",
            "inputs_before",
            "inputs_after",
            "outputs",
            "prior_outputs",
            "streams",
            "returncode",
            "check_returncode",
            "timed_out",
            "errors",
        }
        if (
            set(record) != fields
            or record["schema_version"] != 1
            or type(record["schema_version"]) is not int
            or record["stage"] != stage_name
            or record["policy_sha256"] != policy_digest
            or record["mode"] not in {"capture", "reuse"}
            or type(record["artifact_attempt"]) is not str
            or type(record["accepted"]) is not bool
            or type(record["timed_out"]) is not bool
            or not isinstance(record["errors"], list)
            or any(type(e) is not str for e in record["errors"])
            or any(
                value is not None and type(value) is not int
                for value in (record["returncode"], record["check_returncode"])
            )
        ):
            raise ReleaseBundleError("capture attempt result schema is invalid")
        stage = stage_by_name[stage_name]
        origin = record["artifact_attempt"]
        if (record["mode"] == "capture" and origin != attempt.name) or (
            record["mode"] == "reuse"
            and (
                origin not in known_artifacts
                or known_artifacts[origin]["stage"] != stage_name
                or (
                    record["accepted"]
                    and known_artifacts[origin]["outputs"] != record["outputs"]
                )
            )
        ):
            raise ReleaseBundleError("capture artifact origin is invalid")
        for name in ("inputs_before", "inputs_after"):
            value = record[name]
            if (
                type(value) is not dict
                or not set(value) <= set(stage.inputs)
                or any(
                    not isinstance(v, str) or not re.fullmatch(r"[0-9a-f]{64}", v)
                    for v in value.values()
                )
            ):
                raise ReleaseBundleError("capture retained input map is invalid")
        expected_files = {"intent.json", "result.json"}
        for field, prefix in (("outputs", "artifacts"), ("prior_outputs", "prior")):
            values = record[field]
            if type(values) is not dict or not set(values) <= set(stage.outputs):
                raise ReleaseBundleError("capture retained artifact map is invalid")
            for name, digest in values.items():
                rel = f"{prefix}/{stage.outputs.index(name):04d}.bin"
                expected_files.add(rel)
                if sha256_bytes(_capture_regular_file(attempt / rel)) != digest:
                    raise ReleaseBundleError(
                        "capture retained artifact bytes were changed"
                    )
        if type(record["streams"]) is not dict or set(record["streams"]) != {
            "stdout.log",
            "stderr.log",
        }:
            raise ReleaseBundleError("capture retained stream map is invalid")
        for name, digest in record["streams"].items():
            expected_files.add(name)
            if sha256_bytes(_capture_regular_file(attempt / name)) != digest:
                raise ReleaseBundleError("capture retained streams were changed")
        live_files = {
            p.relative_to(attempt).as_posix() for p in attempt.rglob("*") if p.is_file()
        }
        # Attempt-local declared producer outputs are retained alongside copies.
        for name in stage.outputs:
            if (
                name.startswith("{attempt}/")
                and origin == attempt.name
                and name in record["outputs"]
                and not _capture_output_path(name, attempt).is_file()
            ):
                raise ReleaseBundleError(
                    "capture producer artifact is missing from history"
                )
            if (
                name.startswith("{attempt}/")
                and _capture_output_path(name, attempt).is_file()
            ):
                rel = (
                    _capture_output_path(name, attempt).relative_to(attempt).as_posix()
                )
                expected_files.add(rel)
                if (
                    name in record["outputs"]
                    and sha256_bytes(_capture_regular_file(attempt / rel))
                    != record["outputs"][name]
                ):
                    raise ReleaseBundleError("capture producer artifact was changed")
        if live_files != expected_files or any(
            p.is_symlink() for p in attempt.rglob("*")
        ):
            raise ReleaseBundleError("capture attempt has unexpected files or symlinks")
        if record["accepted"]:
            if (
                record["inputs_before"] != record["inputs_after"]
                or set(record["inputs_before"]) != set(stage.inputs)
                or set(record["outputs"]) != set(stage.outputs)
                or record["check_returncode"] != 0
                or type(record["check_returncode"]) is not int
                or (
                    record["mode"] == "capture"
                    and (
                        record["returncode"] != 0
                        or type(record["returncode"]) is not int
                    )
                )
                or record["timed_out"]
                or record["errors"]
            ):
                raise ReleaseBundleError(
                    "capture acceptance is inconsistent with retained outcomes"
                )
            previous[stage_name] = (attempt, record)
            known_artifacts[attempt.name] = record
    return previous, number


def _capture_run_attempt(
    plan: PublicationCapturePlan,
    stage: PublicationCaptureStage,
    attempt: Path,
    artifact_attempt: Path,
    *,
    stage_deadline: float,
    policy_digest: str,
    mode: str,
    candidate: tuple[Path, dict[str, Any]] | None,
    environment: dict[str, str],
    process_runner: _CaptureProcessRunner,
) -> _CaptureAttemptOutcome:
    """Execute and durably close one attempt under the caller's unchanged deadline."""
    before: dict[str, str] = {}
    after: dict[str, str] = {}
    outputs: dict[str, str] = {}
    prior: dict[str, str] = {}
    errors: list[str] = []
    stdout = b""
    stderr = b""
    returncode: int | None = None
    check_returncode: int | None = None
    timed_out = False

    def execute(
        command: tuple[str, ...],
        *,
        execution_deadline: float = stage_deadline,
        current_attempt: Path = attempt,
        current_artifact_attempt: Path = artifact_attempt,
    ) -> subprocess.CompletedProcess[str]:
        bound = execution_deadline - time.monotonic()
        if bound <= 0:
            raise subprocess.TimeoutExpired(list(command), 0)
        arguments = [
            str(current_attempt)
            if a == "{attempt}"
            else str(current_artifact_attempt)
            if a == "{artifact_attempt}"
            else a
            for a in command
        ]
        return process_runner(
            arguments, cwd=plan.project_root, env=environment, timeout=bound
        )

    try:
        before = _capture_stage_snapshot(stage)
        for index, name in enumerate(stage.outputs):
            path = _capture_output_path(name, artifact_attempt)
            if any(p.is_symlink() for p in (path, *path.parents)):
                raise ReleaseBundleError(
                    "capture producer destination traverses a symlink"
                )
            if path.exists():
                data = _capture_regular_file(path)
                prior[name] = sha256_bytes(data)
                _capture_new_file(attempt / f"prior/{index:04d}.bin", data)
        if mode == "capture":
            completed = execute(stage.command)
            returncode = completed.returncode
            stdout += completed.stdout.encode()
            stderr += completed.stderr.encode()
            if returncode:
                raise ReleaseBundleError(
                    "capture producer returned a rejecting exit code"
                )
        completed = execute(stage.check_command)
        check_returncode = completed.returncode
        stdout += completed.stdout.encode()
        stderr += completed.stderr.encode()
        if check_returncode:
            raise ReleaseBundleError(
                "capture strict owner check rejected its artifacts"
            )
        for index, name in enumerate(stage.outputs):
            data = _capture_regular_file(_capture_output_path(name, artifact_attempt))
            outputs[name] = sha256_bytes(data)
            _capture_new_file(attempt / f"artifacts/{index:04d}.bin", data)
        after = _capture_stage_snapshot(stage)
        if before != after:
            raise ReleaseBundleError(
                "capture inputs changed during execution or validation"
            )
        if any(
            sha256_bytes(
                _capture_regular_file(_capture_output_path(name, artifact_attempt))
            )
            != digest
            for name, digest in outputs.items()
        ):
            raise ReleaseBundleError(
                "capture artifacts changed while they were retained"
            )
        if mode == "reuse" and candidate and outputs != candidate[1]["outputs"]:
            raise ReleaseBundleError(
                "capture reuse check changed previously accepted artifacts"
            )
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        stdout += (
            exc.stdout if isinstance(exc.stdout, bytes) else (exc.stdout or "").encode()
        )
        stderr += (
            exc.stderr if isinstance(exc.stderr, bytes) else (exc.stderr or "").encode()
        )
        errors.append("capture stage exceeded its finite deadline")
    except (OSError, ValueError, TypeError) as exc:
        errors.append(str(exc))
    try:
        after = _capture_stage_snapshot(stage)
    except (OSError, ReleaseBundleError):
        errors.append("capture inputs could not be rechecked after the attempt")
    # Even a rejected producer may have emitted partial or unchanged
    # artifacts. Preserve their actual bytes without granting approval.
    for index, name in enumerate(stage.outputs):
        if (
            name not in outputs
            and _capture_output_path(name, artifact_attempt).exists()
        ):
            try:
                data = _capture_regular_file(
                    _capture_output_path(name, artifact_attempt)
                )
                outputs[name] = sha256_bytes(data)
                _capture_new_file(attempt / f"artifacts/{index:04d}.bin", data)
            except (OSError, ReleaseBundleError) as exc:
                errors.append(str(exc))
    streams = {"stdout.log": stdout, "stderr.log": stderr}
    for name, data in streams.items():
        _capture_new_file(attempt / name, data)
    expected_files = {
        "intent.json",
        *streams,
        *(f"artifacts/{stage.outputs.index(name):04d}.bin" for name in outputs),
        *(f"prior/{stage.outputs.index(name):04d}.bin" for name in prior),
        *(
            name.removeprefix("{attempt}/")
            for name in stage.outputs
            if name.startswith("{attempt}/")
            and artifact_attempt == attempt
            and name in outputs
        ),
    }
    if {
        p.relative_to(attempt).as_posix() for p in attempt.rglob("*") if p.is_file()
    } != expected_files or any(p.is_symlink() for p in attempt.rglob("*")):
        errors.append("capture attempt has unexpected files or symlinks")
    record = {
        "schema_version": 1,
        "stage": stage.name,
        "policy_sha256": policy_digest,
        "mode": mode,
        "artifact_attempt": artifact_attempt.name,
        "accepted": not errors,
        "inputs_before": before,
        "inputs_after": after,
        "outputs": outputs,
        "prior_outputs": prior,
        "streams": {name: sha256_bytes(data) for name, data in streams.items()},
        "returncode": returncode,
        "check_returncode": check_returncode,
        "timed_out": timed_out,
        "errors": errors,
    }
    _capture_new_file(attempt / "result.json", _canonical_json(record))
    return _CaptureAttemptOutcome(before, after, tuple(errors), timed_out)


def run_publication_capture(
    plan: PublicationCapturePlan,
    journal: Path,
    *,
    resume: bool = False,
) -> PublicationCaptureResult:
    """Execute or resume a fixed DAG with immutable, independently checked history.

    Only this explicit action starts processes. Existing producers own their
    declared project outputs; the manager writes only its chosen journal. A
    rejected stage stops the DAG, while earlier accepted output copies remain.
    Every reused stage runs its strict check again under the same finite bound.
    """
    from fep_formal.verification._subprocess import run_process_group

    _capture_validate_plan(plan)
    if os.name != "posix":
        raise ReleaseBundleError(
            "publication capture requires POSIX input custody and process supervision"
        )
    for stage in plan.stages:
        _capture_check_rosters(stage)
    journal = Path(journal).absolute()
    if journal.resolve() != journal:
        raise ReleaseBundleError("capture journal path must be canonical")
    if any(p.is_symlink() for p in (journal, *journal.parents)):
        raise ReleaseBundleError("capture journal must not traverse a symlink")
    if journal.resolve().is_relative_to(Path(plan.project_root)):
        raise ReleaseBundleError("capture journal must be outside the project root")
    policy = plan.record()
    policy_digest = sha256_bytes(_canonical_json(policy))
    header = {
        "schema_version": 1,
        "kind": "publication-capture-journal",
        "policy": policy,
        "policy_sha256": policy_digest,
    }
    if resume:
        retained_header = _capture_read_json(journal / "journal.json")
        if (
            type(retained_header.get("schema_version")) is not int
            or retained_header != header
        ):
            raise ReleaseBundleError(
                "capture resume policy differs from the retained journal"
            )
    else:
        _capture_mkdir(journal, parents=True)
        _capture_new_file(journal / "journal.json", _canonical_json(header))
        _capture_mkdir(journal / "attempts")
    attempts = journal / "attempts"
    if attempts.is_symlink() or not attempts.is_dir():
        raise ReleaseBundleError("capture attempt directory is missing or a symlink")
    if {p.name for p in journal.iterdir()} != {"journal.json", "attempts"}:
        raise ReleaseBundleError("capture journal has unexpected top-level files")
    stage_by_name = {s.name: s for s in plan.stages}
    previous, number = _capture_read_history(attempts, stage_by_name, policy_digest)
    deadline = time.monotonic() + plan.timeout_s
    accepted: list[str] = []
    reused: list[str] = []
    changed: set[str] = set()
    from fep_formal._paths import project_child_environment

    environment = project_child_environment(os.environ)
    environment.update(PYTHONDONTWRITEBYTECODE="1", FEP_FORMAL_LIVE_TESTS="0")
    if plan.kind == "strict-local-publication-capture":
        environment["SOURCE_DATE_EPOCH"] = plan.stages[0].command[-1]
    for stage in plan.stages:
        stage_deadline = min(deadline, time.monotonic() + stage.timeout_s)
        candidate = previous.get(stage.name)
        reusable = False
        if candidate and not set(stage.dependencies) & changed:
            _old_attempt, old = candidate
            try:
                reusable = _capture_stage_snapshot(stage) == old[
                    "inputs_before"
                ] and all(
                    sha256_bytes(
                        _capture_regular_file(
                            _capture_output_path(
                                name, attempts / old["artifact_attempt"]
                            )
                        )
                    )
                    == digest
                    for name, digest in old["outputs"].items()
                )
            except (OSError, ReleaseBundleError):
                reusable = False
        for mode in ("reuse", "capture") if reusable else ("capture",):
            number += 1
            if number > 999999:
                raise ReleaseBundleError("capture attempt sequence is exhausted")
            attempt = attempts / f"{number:06d}-{stage.name}"
            _capture_mkdir(attempt)
            _capture_new_file(
                attempt / "intent.json",
                _canonical_json(
                    {
                        "schema_version": 1,
                        "stage": stage.name,
                        "policy_sha256": policy_digest,
                    }
                ),
            )
            artifact_attempt = (
                attempts / candidate[1]["artifact_attempt"]
                if mode == "reuse" and candidate
                else attempt
            )
            outcome = _capture_run_attempt(
                plan,
                stage,
                attempt,
                artifact_attempt,
                stage_deadline=stage_deadline,
                policy_digest=policy_digest,
                mode=mode,
                candidate=candidate,
                environment=environment,
                process_runner=run_process_group,
            )
            if outcome.errors:
                if (
                    mode == "reuse"
                    and outcome.before == outcome.after
                    and not outcome.timed_out
                ):
                    continue
                return PublicationCaptureResult(
                    False,
                    journal,
                    tuple(accepted),
                    tuple(reused),
                    stage.name,
                    tuple(outcome.errors),
                )
            accepted.append(stage.name)
            if mode == "reuse":
                reused.append(stage.name)
            else:
                changed.add(stage.name)
            break
    return PublicationCaptureResult(
        True, journal, tuple(accepted), tuple(reused), None, ()
    )


_PUBLICATION_CAPTURE_STAGE_NAMES = (
    "native",
    "formalism-audit",
    "render",
    "python",
    "numerical",
    "browser",
    "bundle",
)
_PUBLICATION_CAPTURE_WORKER = (
    "from fep_formal.output.release_bundle._core import _publication_capture_worker;"
    "import sys;raise SystemExit(_publication_capture_worker(*sys.argv[1:]))"
)


def _capture_render_outputs(root: Path) -> tuple[str, ...]:
    """Enumerate the existing render owner's declared publication outputs."""
    from fep_formal.output.release_bundle._constants import (
        PUBLICATION_HTML,
        RENDERER_PROVENANCE,
    )
    from fep_formal.output.rendering import (
        _RENDER_METADATA_FILES,
        MANUSCRIPT_ASSETS,
        manuscript_source_files,
    )

    def paths(*names: str) -> tuple[str, ...]:
        return tuple(str(root / name) for name in names)

    return paths(
        "docs/render-acceptance.json",
        "output/pdf/fep_lean_combined.pdf",
        "output/pdf/_combined_manuscript.log",
        "output/pdf/_latex_stdout.log",
        "output/pdf/_combined_manuscript.tex",
        PUBLICATION_HTML.as_posix(),
        RENDERER_PROVENANCE.as_posix(),
        "output/manuscript/assets/graphical-abstract.png",
        *(f"output/manuscript/{name}" for name in _RENDER_METADATA_FILES),
        *(
            f"output/manuscript/{destination.as_posix()}"
            for _source, destination in MANUSCRIPT_ASSETS.values()
        ),
        *(
            f"output/manuscript/{p.name}"
            for p in manuscript_source_files(root / "manuscript")
        ),
    )


def plan_publication_capture(
    project_root: Path,
    *,
    template_root: Path,
    source_date_epoch: int = 0,
    timeout_s: float = 21600,
) -> PublicationCapturePlan:
    """Declare the strict publication DAG without running tools or repairing inputs.

    The rendering template is an explicit read-only resource. Each existing
    producer retains its established output ownership. The final two archives
    live in the external journal; provider/hosted/publication actions are absent.
    """
    from fep_formal.output.browser_capture import (
        BROWSER_RECEIPT,
        CANONICAL_BROWSER_SCREENSHOTS,
    )
    from fep_formal.output.manuscript import UNIFIED_FORMALISM_CATALOGUE_FILENAME
    from fep_formal.output.provenance import config_owner_paths, source_owner_paths
    from fep_formal.output.publication_metadata import load_graphical_abstract
    from fep_formal.output.release_bundle._constants import (
        _MANUSCRIPT_FIGURE_REFERENCES,
        _REQUIRED_STATIC_MEMBERS,
    )
    from fep_formal.output.rendering import (
        MANUSCRIPT_ASSETS,
    )

    root = Path(project_root).resolve()
    template = Path(template_root).resolve()
    epoch = _source_date_epoch(source_date_epoch)
    for name in ("manuscript_vars.yaml", UNIFIED_FORMALISM_CATALOGUE_FILENAME):
        if not (root / "manuscript" / name).is_file():
            raise ReleaseBundleError(
                "capture requires existing paired manuscript projections; "
                "run fep-formal catalogue before planning"
            )
        _capture_regular_file(root / "manuscript" / name)
    # Enumerating owned files is read-only. Missing inputs fail when their stage
    # consumes them, so upstream receipt producers can run in topological order.
    common = tuple(
        sorted(
            str(p.absolute())
            for p in (*source_owner_paths(root), *config_owner_paths(root))
        )
    )
    test_paths = _capture_directory_paths(root / "tests")
    manuscript_paths = _capture_directory_paths(root / "manuscript")
    template_links = _capture_template_links(template, root)
    template_paths = _capture_directory_paths(template, resource_links=template_links)
    if not (template / "scripts/pipeline/stage_03_render.py").is_file():
        raise ReleaseBundleError(
            "capture requires the explicit rendering template owner"
        )

    def paths(*names: str) -> tuple[str, ...]:
        return tuple(str(root / name) for name in names)

    def stage(
        name: str,
        dependencies: tuple[str, ...],
        inputs: Sequence[str],
        outputs: Sequence[str],
        bound: float,
        rosters: tuple[tuple[Path, tuple[str, ...]], ...] = (),
    ) -> PublicationCaptureStage:
        arguments = (sys.executable, "-c", _PUBLICATION_CAPTURE_WORKER, name)
        tail = (str(root), "{artifact_attempt}", str(template), str(epoch))
        return PublicationCaptureStage(
            name,
            dependencies,
            tuple(sorted(set(inputs))),
            tuple(outputs),
            (*arguments, "produce", str(root), "{attempt}", str(template), str(epoch)),
            (*arguments, "check", *tail),
            bound,
            tuple((str(directory), files) for directory, files in rosters),
            template_links if name in {"render", "bundle"} else (),
        )

    native = paths("output/native-verification.json")
    audit = paths("output/formalism-audit.json")
    python = paths(
        "output/python-acceptance.json", "output/pytest.xml", "output/coverage.xml"
    )
    asset_origins = paths(
        *(source.as_posix() for source, _destination in MANUSCRIPT_ASSETS.values()),
        *_MANUSCRIPT_FIGURE_REFERENCES.values(),
        load_graphical_abstract(root).source_path,
    )
    collection_cache = paths("output/.cache/tests_collected.json")
    manuscript_projections = paths(
        "manuscript/manuscript_vars.yaml",
        f"manuscript/{UNIFIED_FORMALISM_CATALOGUE_FILENAME}",
    )
    citation = paths("CITATION.cff")
    render = _capture_render_outputs(root)
    numerical = paths("output/numerical-witnesses.json")
    browser = paths(BROWSER_RECEIPT.as_posix(), *CANONICAL_BROWSER_SCREENSHOTS.values())
    projections = paths(
        *(
            p
            for p, _kind in _REQUIRED_STATIC_MEMBERS
            if not p.startswith("output/") and p != BROWSER_RECEIPT.as_posix()
        )
    )
    roster = (
        stage(
            "native",
            (),
            (*common, *test_paths, *citation, *asset_origins),
            (*native, *manuscript_projections, *collection_cache),
            10800,
            ((root / "tests", test_paths),),
        ),
        stage("formalism-audit", (), common, audit, 3600),
        stage(
            "render",
            ("native", "formalism-audit"),
            (
                *common,
                *manuscript_paths,
                *template_paths,
                *asset_origins,
                *projections,
                *native,
                *audit,
                *citation,
                *collection_cache,
            ),
            render,
            3600,
            ((root / "manuscript", manuscript_paths), (template, template_paths)),
        ),
        stage(
            "python",
            ("render",),
            (
                *common,
                *test_paths,
                *manuscript_paths,
                *projections,
                *citation,
                *asset_origins,
                *collection_cache,
                *paths("docs/render-acceptance.json", "docs/render-fonts.json"),
            ),
            python,
            10800,
            ((root / "tests", test_paths), (root / "manuscript", manuscript_paths)),
        ),
        stage("numerical", (), common, numerical, 120),
        stage(
            "browser",
            ("render", "numerical"),
            (
                *common,
                *projections,
                *paths(
                    "docs/formalism-atlas.html", "docs/formal-kernel-dashboard.html"
                ),
            ),
            browser,
            600,
        ),
        stage(
            "bundle",
            _PUBLICATION_CAPTURE_STAGE_NAMES[:-1],
            (
                *common,
                *test_paths,
                *manuscript_paths,
                *template_paths,
                *asset_origins,
                *projections,
                *native,
                *audit,
                *python,
                *render,
                *numerical,
                *browser,
                *collection_cache,
            ),
            ("{attempt}/release-a.tar.gz", "{attempt}/release-b.tar.gz"),
            3600,
            (
                (root / "tests", test_paths),
                (root / "manuscript", manuscript_paths),
                (template, template_paths),
            ),
        ),
    )
    plan = PublicationCapturePlan(
        str(root), roster, timeout_s, "strict-local-publication-capture"
    )
    _capture_validate_plan(plan)
    return plan


def _publication_capture_worker(
    stage: str,
    mode: str,
    project_root: str,
    attempt_root: str,
    template_root: str,
    epoch: str,
) -> int:
    """Bounded child entry point composing the existing strict evidence owners."""
    from fep_formal.output import release_bundle as bundle
    from fep_formal.output.browser_capture import capture_browser_acceptance
    from fep_formal.output.evidence import validate_native_lean_receipt
    from fep_formal.output.render_log import receipt_defects
    from fep_formal.verification.formalism_audit import (
        run_formalism_audit,
        validate_formalism_audit_receipt,
        write_formalism_audit_receipt,
    )

    if stage not in _PUBLICATION_CAPTURE_STAGE_NAMES or mode not in {
        "produce",
        "check",
    }:
        raise ReleaseBundleError("unknown publication capture worker action")
    root, attempt = Path(project_root), Path(attempt_root)
    source_epoch = _source_date_epoch(int(epoch))
    if mode == "produce":
        if stage == "native":
            from fep_formal.output.manuscript import write_manuscript_vars
            from fep_formal.verification.lean_verifier import verify_catalogue

            outcome = verify_catalogue(
                root,
                None,
                None,
                receipt_path=root / "output/native-verification.json",
                fail_on_warnings=True,
            )
            print(outcome.to_json())
            native_returncode = outcome.exit_code
            if native_returncode:
                return native_returncode
            validation = validate_native_lean_receipt(
                root / "output/native-verification.json", project_root=root
            )
            if not all(
                validation.get(name) is True
                for name in ("valid", "source_bound", "native_claim_ready")
            ):
                return 1
            # Native timings and evidence values become immutable render/Python
            # inputs only after their final source-bound receipt is accepted.
            write_manuscript_vars(root)
            return 0
        if stage == "formalism-audit":
            result = run_formalism_audit(root, timeout=300)
            write_formalism_audit_receipt(root / "output/formalism-audit.json", result)
            return 0 if result.complete else 1
        if stage == "python":
            bundle.run_python_acceptance(root)
        elif stage == "render":
            import runpy

            renderer = runpy.run_path(str(root / "scripts/render_publication.py"))
            if renderer["main"](["--template", template_root, "--lock-timeout", "120"]):
                return 1
            bundle.write_publication_manuscript(root, source_date_epoch=source_epoch)
        elif stage == "numerical":
            bundle.write_numerical_witnesses(root)
        elif stage == "browser":
            capture_browser_acceptance(root)
        elif stage == "bundle":
            for name in ("release-a.tar.gz", "release-b.tar.gz"):
                bundle.build_release_bundle(
                    root, attempt / name, source_date_epoch=source_epoch
                )
        return 0
    errors: Sequence[str] = ()
    if stage == "native":
        native_result = validate_native_lean_receipt(
            root / "output/native-verification.json", project_root=root
        )
        if not (
            native_result.get("valid") is True
            and native_result.get("source_bound") is True
            and native_result.get("native_claim_ready") is True
        ):
            errors = ("native receipt is not live-source-bound and claim-ready",)
        else:
            import yaml

            from fep_formal.catalogue.topics import FEPTopicCatalogue
            from fep_formal.output.manuscript import (
                build_manuscript_vars,
                manuscript_projection_drift,
            )

            variables = build_manuscript_vars(
                FEPTopicCatalogue.from_yaml(root / "config/topics.yaml"),
                root,
                cache_test_count=False,
            )
            errors = tuple(
                f"stale native manuscript projection: {path.relative_to(root)}"
                for path in manuscript_projection_drift(
                    root, expected_variables=variables
                )
            )
            actual_variables = yaml.safe_load(
                _capture_regular_file(root / "manuscript/manuscript_vars.yaml")
            )
            actual_source = (
                actual_variables.get("source")
                if type(actual_variables) is dict
                else None
            )
            if (
                type(actual_source) is not dict
                or set(actual_source) != set(variables["source"])
                or any(type(value) is not str for value in actual_source.values())
            ):
                errors = (*errors, "native manuscript source stamp schema is invalid")
            # The source block has the established run-bound string schema,
            # including the render date. All other values, including every
            # current native result and timing, must still match exactly.
            if type(actual_variables) is not dict or _canonical_json(
                {
                    key: value
                    for key, value in actual_variables.items()
                    if key != "source"
                }
            ) != _canonical_json(
                {key: value for key, value in variables.items() if key != "source"}
            ):
                errors = (*errors, "native manuscript evidence values are stale")
    elif stage == "formalism-audit":
        errors = validate_formalism_audit_receipt(
            root / "output/formalism-audit.json", root
        )
    elif stage == "python":
        errors = bundle._python_acceptance_receipt_errors(root)
    elif stage == "render":
        errors = (
            *receipt_defects(
                root / "docs/render-acceptance.json", manuscript_dir=root / "manuscript"
            ),
            *bundle._rendered_manuscript_errors(root),
            *bundle.publication_manuscript_errors(root, source_date_epoch=source_epoch),
        )
    elif stage == "numerical":
        if _capture_regular_file(
            root / "output/numerical-witnesses.json"
        ) != bundle.build_numerical_witness_receipt(root):
            errors = ("numerical witness receipt is stale",)
    elif stage == "browser":
        errors = bundle._browser_receipt_errors(root)
    elif stage == "bundle":
        archives = tuple(
            attempt / name for name in ("release-a.tar.gz", "release-b.tar.gz")
        )
        validations = tuple(
            bundle.validate_release_bundle(archive, project_root=root)
            for archive in archives
        )
        errors = tuple(
            error for validation in validations for error in validation.errors
        )
        if not all(validation.claim_ready for validation in validations):
            errors = (
                *errors,
                "both archives must independently pass strict live-source validation",
            )
        if _capture_regular_file(archives[0]) != _capture_regular_file(archives[1]):
            errors = (
                *errors,
                "independently built publication archives differ in bytes",
            )
    for error in errors:
        print(f"ERROR: {error}")
    return 1 if errors else 0
