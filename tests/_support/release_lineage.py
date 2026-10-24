"""Present the live tree to the frozen H2.7-R0 custody validator.

The H3 custody addendum records the release-metadata transition 1.3.0 -> 1.4.0,
and its validator (hash-bound, never edited) requires the recorded 1.4.0 root
token. Later releases change only that token. This helper copies the custody
inputs and maps an approved later root version back to the recorded token, so
the validator still proves every other byte is unchanged. Any other version or
a duplicated root is left as-is and fails the validator.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from tests._support.h2_r0_custody import (
    H3_ADDENDUM_PATH,
    PRIOR_PATH,
    RELEASE_METADATA_REPLACEMENTS,
    SUCCESSOR_PATH,
    VALIDATOR_PATH,
)

LATER_RELEASE_VERSIONS = ("1.5.0", "1.6.0", "2.0.0")


def record_release_metadata(root: Path) -> None:
    """Rewrite an approved later root version to the recorded 1.4.0 token."""
    for relative, (_, recorded) in RELEASE_METADATA_REPLACEMENTS.items():
        path = root / relative
        data = path.read_text(encoding="utf-8")
        if recorded in data:
            continue
        for version in LATER_RELEASE_VERSIONS:
            live = recorded.replace('"1.4.0"', f'"{version}"')
            if data.count(live) == 1:
                path.write_text(data.replace(live, recorded, 1), encoding="utf-8")
                break


def custody_paths(source: Path) -> tuple[str, ...]:
    """Every file the custody validator binds, read from the custody records."""
    paths = {PRIOR_PATH, SUCCESSOR_PATH, H3_ADDENDUM_PATH, VALIDATOR_PATH}
    for record in (PRIOR_PATH, SUCCESSOR_PATH, H3_ADDENDUM_PATH):
        data = json.loads((source / record).read_text(encoding="utf-8"))
        paths.update(data.get("source_sha256", {}))
    return tuple(sorted(paths))


def custody_root(source: Path, destination: Path) -> Path:
    """Copy custody inputs from ``source`` and record their release metadata."""
    for relative in custody_paths(source):
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / relative, target)
    record_release_metadata(destination)
    return destination
