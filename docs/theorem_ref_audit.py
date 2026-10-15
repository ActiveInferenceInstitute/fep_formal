#!/usr/bin/env python3
"""Audit canonical declaration references and current root catalogue counts.

Current overview/contract sections are compared with the generated coverage
projection. Release histories and dated evidence receipts have their own source
epochs; their topic and test totals are deliberately not rebound to live counts.
This is a reference audit, not native, runtime or scientific acceptance.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

from fep_lean.catalogue.coverage import COVERAGE_JSON
from fep_lean.catalogue.references import unresolved_manuscript_references
from fep_lean.formal.declarations import composed_theorem_declarations

# Scope follows the current overview/contract sections, not every number in
# every root document. In particular README's Release section and HANDOFF's
# dated receipts are historical. Runtime/test counts have no coverage-JSON
# counterpart and are never compared with catalogue or declaration counts.
_CURRENT_COUNT_SECTIONS = {
    "README.md": frozenset({"", "Contract", "Formal depth"}),
    "AGENTS.md": frozenset({"Purpose"}),
    "SPEC.md": frozenset({"Scope"}),
    "HANDOFF.md": frozenset({"Current formal breadth and depth"}),
}
_SMALL_COUNTS = {
    word: value
    for value, word in enumerate(
        (
            "zero",
            "one",
            "two",
            "three",
            "four",
            "five",
            "six",
            "seven",
            "eight",
            "nine",
            "ten",
        )
    )
}
_NUMBER = r"(?P<count>\d+(?:,\d{3})*|" + "|".join(_SMALL_COUNTS) + r")\b"
_COUNT_REFERENCES = (
    ("topics", re.compile(r"\bcatalogue\s+of\s+" + _NUMBER, re.IGNORECASE)),
    ("topics", re.compile(r"\b" + _NUMBER + r"(?:-|\s+)topics?\b", re.IGNORECASE)),
    (
        "families",
        re.compile(r"\b" + _NUMBER + r"\s+(?:reviewed\s+)?families\b", re.IGNORECASE),
    ),
    ("areas", re.compile(r"\b" + _NUMBER + r"\s+areas\b", re.IGNORECASE)),
)


def _blank(text: str) -> str:
    """Mask non-prose without changing source line numbers."""
    return "".join("\n" if character == "\n" else " " for character in text)


def _current_count_prose(text: str, sections: frozenset[str]) -> str:
    text = re.sub(r"<!--.*?-->", lambda match: _blank(match[0]), text, flags=re.DOTALL)
    section = ""
    fence: str | None = None
    prose: list[str] = []
    for line in text.splitlines(keepends=True):
        marker = re.match(r"^\s*(`{3,}|~{3,})(.*)$", line)
        if fence is not None:
            if (
                marker is not None
                and marker[1][0] == fence[0]
                and len(marker[1]) >= len(fence)
                and not marker[2].strip()
            ):
                fence = None
            prose.append(_blank(line))
            continue
        if marker is not None:
            fence = marker[1]
            prose.append(_blank(line))
            continue
        heading = re.match(r"^##\s+(.+?)\s*#*\s*$", line)
        if heading is not None:
            section = heading[1]
        prose.append(line if section in sections else _blank(line))
    # Link targets are addresses, not catalogue quantity claims.
    return re.sub(r"\]\([^\n)]*\)", lambda match: _blank(match[0]), "".join(prose))


def root_count_reference_failures(root: Path) -> tuple[str, ...]:
    """Compare current topic/family/area claims with the existing coverage join.

    The coverage generator's own freshness gate validates its source binding.
    Here the topic rows and area projection must also conserve the topic total;
    a missing or malformed reference cannot silently disable the audit.
    """
    try:
        coverage = json.loads((root / COVERAGE_JSON).read_text(encoding="utf-8"))
        if not isinstance(coverage, dict):
            raise TypeError("expected an object")
        metrics = coverage.get("metrics")
        rows = coverage.get("topics")
        area_counts = coverage.get("area_counts")
        if not isinstance(metrics, dict) or not isinstance(rows, list):
            raise TypeError("expected metrics and topic rows")
        topic_count = metrics.get("topics")
        if type(topic_count) is not int or topic_count <= 0 or len(rows) != topic_count:
            raise ValueError("topic total does not match the topic rows")
        if not isinstance(area_counts, dict) or not area_counts:
            raise ValueError("expected nonempty area counts")
        if any(type(count) is not int or count <= 0 for count in area_counts.values()):
            raise ValueError("area counts must be positive integers")
        families: set[str] = set()
        areas: Counter[str] = Counter()
        for row in rows:
            if not isinstance(row, dict):
                raise TypeError("expected topic row objects")
            family, area = row.get("family"), row.get("area")
            if (
                not isinstance(family, str)
                or not family
                or not isinstance(area, str)
                or not area
            ):
                raise ValueError("topic rows must name their family and area")
            families.add(family)
            areas[area] += 1
        if areas != area_counts:
            raise ValueError("area counts do not match the topic rows")
        expected = {
            "topics": topic_count,
            "families": len(families),
            "areas": len(areas),
        }
    except (OSError, UnicodeError, ValueError, TypeError) as exc:
        return (f"{COVERAGE_JSON}: cannot validate catalogue count references: {exc}",)

    failures: list[str] = []
    for relative, sections in _CURRENT_COUNT_SECTIONS.items():
        try:
            prose = _current_count_prose(
                (root / relative).read_text(encoding="utf-8"), sections
            )
        except (OSError, UnicodeError) as exc:
            failures.append(f"{relative}: cannot read current count claims: {exc}")
            continue
        for unit, pattern in _COUNT_REFERENCES:
            for match in pattern.finditer(prose):
                literal = match["count"].lower()
                found = (
                    _SMALL_COUNTS[literal]
                    if literal in _SMALL_COUNTS
                    else int(literal.replace(",", ""))
                )
                if found != expected[unit]:
                    line = prose.count("\n", 0, match.start()) + 1
                    failures.append(
                        f"{relative}:{line}: current catalogue {unit} count "
                        f"{literal!r} disagrees with {COVERAGE_JSON} ({expected[unit]})"
                    )
    return tuple(failures)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    composed = {
        declaration.rsplit(".", 1)[-1]
        for declaration in composed_theorem_declarations()
    }
    failures = tuple(
        f"manuscript/{failure}"
        for failure in unresolved_manuscript_references(
            root / "manuscript", additional_declarations=composed
        )
    ) + root_count_reference_failures(root)
    if failures:
        for failure in failures:
            print(failure)
        print(f"FAIL: {len(failures)} canonical declaration/count reference failure(s)")
        return 1
    print(
        "OK: all manuscript topic and composed declaration references resolve; "
        "current root catalogue counts match coverage"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
