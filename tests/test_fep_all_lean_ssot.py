"""Verify the actual aggregate import closure owns every catalogue topic once.

The compatibility root contains imports; its family shards contain topic
namespaces. Inspect the actual files, independently of the generator's output
map, so missing/duplicated topic definitions cannot hide behind metadata.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from tests._support.lean_module_contract import (
    topic_projection_sources,
    topic_projection_text,
)

PROJ = Path(__file__).resolve().parent.parent
FEP_ALL = PROJ / "lean" / "FepSketches" / "fep_all.lean"
TOPICS_YAML = PROJ / "config" / "topics.yaml"

_NS_RE = re.compile(r"^namespace fep_fep(\d+)", re.MULTILINE)


def _extract_lean_topic_ids(text: str) -> set[str]:
    """Extract topic IDs from namespace declarations in fep_all.lean."""
    return {f"fep-{m.group(1)}" for m in _NS_RE.finditer(text)}


def _load_yaml_topic_ids() -> set[str]:
    """Load topic IDs from topics.yaml."""
    with open(TOPICS_YAML, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return {t["id"] for t in data["topics"]}


def test_fep_all_lean_covers_all_yaml_topics() -> None:
    """Every topic in topics.yaml has a corresponding namespace in fep_all.lean."""
    lean_ids = _extract_lean_topic_ids(topic_projection_text(FEP_ALL))
    yaml_ids = _load_yaml_topic_ids()

    missing_from_lean = yaml_ids - lean_ids
    extra_in_lean = lean_ids - yaml_ids

    errors: list[str] = []
    if missing_from_lean:
        errors.append(
            f"In topics.yaml but not in fep_all.lean: {sorted(missing_from_lean)}"
        )
    if extra_in_lean:
        errors.append(
            f"In fep_all.lean but not in topics.yaml: {sorted(extra_in_lean)}"
        )

    assert not errors, "\n".join(errors)


def test_fep_all_lean_has_the_sealed_topic_count() -> None:
    """The aggregate must contain exactly the generated catalogue namespaces."""
    lean_ids = _extract_lean_topic_ids(topic_projection_text(FEP_ALL))
    expected_ids = _load_yaml_topic_ids()
    assert len(lean_ids) == len(expected_ids), (
        f"Expected {len(expected_ids)} topics, found {len(lean_ids)}: {sorted(lean_ids)}"
    )


def test_fep_all_lean_has_no_sorry() -> None:
    """fep_all.lean must not contain any non-comment sorry."""
    text = topic_projection_text(FEP_ALL)
    sorry_lines = []
    for i, line in enumerate(text.splitlines(), 1):
        stripped = line.lstrip()
        if stripped.startswith("--"):
            continue
        if re.search(r"\bsorry\b", line):
            sorry_lines.append(f"  line {i}: {line.rstrip()}")

    assert not sorry_lines, "sorry found in fep_all.lean:\n" + "\n".join(sorry_lines)


def test_imported_family_topic_membership_is_bijective() -> None:
    """The real import closure owns every topic once, with no aggregate duplication."""
    aggregate = FEP_ALL.read_text(encoding="utf-8")
    assert not _NS_RE.search(aggregate)
    sources = topic_projection_sources(FEP_ALL)
    assert all(path.parent.name == "families" for path, _ in sources)
    ids = [
        f"fep-{match.group(1)}"
        for _, text in sources
        for match in _NS_RE.finditer(text)
    ]
    assert set(ids) == _load_yaml_topic_ids()
    assert len(ids) == len(set(ids))
