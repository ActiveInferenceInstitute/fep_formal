"""Content-addressed custody without self-referential commit refreshes."""

from __future__ import annotations

import hashlib
import json
import os  # noqa: F401 -- tests patch custody.os.replace; custody and fsutil share
import re  #        -- the os module, so the patch reaches the delegated write.
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from fep_lean.output.fsutil import atomic_write_text

FRESH = "FRESH"
STALE_CUSTODY = "STALE-CUSTODY (digest-only)"
CONTENT_DRIFT = "CONTENT-DRIFT"
SIGNATURE_FIELDS = frozenset(
    {
        "source_commit",
        "pipeline_commit",
        "source_owners_sha256",
        "pipeline_owners_sha256",
    }
)


def contained_file(root: Path, relative: str) -> Path:
    """Resolve a readable owner without accepting escapes or symlink aliases."""
    root = root.resolve()
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts or not rel.parts:
        raise ValueError(f"invalid owner path: {relative}")
    path = root / rel
    if any(
        parent.is_symlink()
        for parent in [path, *path.parents]
        if parent != root and root in parent.parents
    ):
        raise ValueError(f"symlinked owner: {relative}")
    if not path.is_file() or not path.resolve().is_relative_to(root):
        raise ValueError(f"missing or uncontained owner: {relative}")
    return path


def fingerprint(root: Path, paths: Iterable[str]) -> dict[str, str]:
    """Hash an explicit owner roster; absent owners are errors, not omissions."""
    return {
        name: hashlib.sha256(contained_file(root, name).read_bytes()).hexdigest()
        for name in sorted(set(paths))
    }


def binding_digest(binding: Mapping[str, str]) -> str:
    return hashlib.sha256(
        json.dumps(dict(binding), sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def validate_binding(
    root: Path, binding: Mapping[str, str], expected: Iterable[str]
) -> list[str]:
    """Validate both roster membership and every byte digest, without writes."""
    expected_set = set(expected)
    errors = []
    if set(binding) != expected_set:
        errors.append("owner roster mismatch")
    for relative in sorted(expected_set):
        try:
            actual = fingerprint(root, [relative])[relative]
            if binding.get(relative) != actual:
                errors.append(f"owner content changed: {relative}")
        except (ValueError, OSError) as exc:
            errors.append(str(exc))
    return errors


def _without_custody(document: str) -> str:
    lines = document.splitlines(keepends=True)
    headers = [i for i, line in enumerate(lines) if line.strip() == "## Signature"]
    if len(headers) != 1:
        raise ValueError("exactly one Signature section is required")
    start = headers[0] + 1
    end = next(
        (i for i in range(start, len(lines)) if lines[i].startswith("## ")), len(lines)
    )
    seen: set[str] = set()
    keep = lines[:start]
    for line in lines[start:end]:
        key, sep, value = line.partition(":")
        if key in SIGNATURE_FIELDS and sep:
            if key in seen or not value.strip():
                raise ValueError("duplicate or empty custody field")
            seen.add(key)
        else:
            keep.append(line)
    if not {"source_commit", "pipeline_commit"} <= seen:
        raise ValueError("missing custody commits")
    return "".join(keep + lines[end:])


def classify_document(on_disk: str, regenerated: str) -> str:
    """Only allowed Signature fields may differ; order and multiplicity matter."""
    try:
        if _without_custody(on_disk) != _without_custody(regenerated):
            return CONTENT_DRIFT
    except ValueError:
        return CONTENT_DRIFT
    return FRESH if on_disk == regenerated else STALE_CUSTODY


def write_text(path: Path, content: str) -> None:
    """Atomically emit changed bytes; unchanged output retains its mtime."""
    if path.is_symlink():
        raise ValueError("refusing to overwrite a symlink")
    if path.is_file() and path.read_text(encoding="utf-8") == content:
        return
    atomic_write_text(path, content)


def write_json(path: Path, payload: Any) -> None:
    write_text(
        path, json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )


def refresh_signature(path: Path, regenerated: str) -> None:
    if (
        not path.is_file()
        or classify_document(path.read_text(encoding="utf-8"), regenerated)
        == CONTENT_DRIFT
    ):
        raise ValueError(
            "content drift requires deliberate re-emission; refresh refused"
        )
    write_text(path, regenerated)


def valid_commit(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}", value) is not None
