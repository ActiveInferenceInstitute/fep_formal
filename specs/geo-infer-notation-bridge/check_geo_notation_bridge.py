#!/usr/bin/env python3
"""Validate the GEO-INFER notation bridge map against its fixed contracts.

The notation map under ``specs/geo-infer-notation-bridge/data/`` is
documentation-level data. This checker is its deterministic freshness gate:
strict YAML schema, every topic id and fep_lean symbol must exist in
``config/theorem_maturity.yaml``, and every GEO-INFER anchor must match the
strict ``GEO-INFER-<MOD>/<repo-relative path>::<Symbol>`` grammar.

The checker never opens the sibling GEO-INFER checkout, never writes bytes,
and never claims that a notation row proves anything. Drift is reported as a
diff-style listing on stderr with exit 1; a clean map exits 0.

Usage::

    uv run python specs/geo-infer-notation-bridge/check_geo_notation_bridge.py --check
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml

def _repo_root() -> Path:
    """Walk up to the checkout root: the directory holding pyproject.toml."""
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "pyproject.toml").is_file():
            return candidate
    raise SystemExit(
        "check_geo_notation_bridge.py: no pyproject.toml above "
        f"{Path(__file__).resolve().parent}; run it inside the fep_lean checkout"
    )


ROOT = _repo_root()
MAP_REL = Path("specs/geo-infer-notation-bridge/data/notation-map.yaml")
MATURITY_REL = Path("config/theorem_maturity.yaml")

MAP_SCHEMA_VERSION = 1
ENTRY_KEYS = frozenset(
    {"concept", "fep_lean", "geo_anchor", "correspondence", "reference"}
)
FEP_LEAN_KEYS = frozenset({"topic_id", "symbol"})

# GEO-INFER-<MOD>/<repo-relative path>::<Symbol>, inline code never a link.
ANCHOR_RE = re.compile(
    r"^GEO-INFER-[A-Z][A-Z0-9-]*/[A-Za-z0-9_./-]+\.py::[A-Za-z_][A-Za-z0-9_]*$"
)


def _nonempty_str(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _maturity_symbols(root: Path) -> dict[str, set[str]]:
    """Return ``topic_id -> accepted fep_lean symbols`` from the maturity file."""
    payload = yaml.safe_load((root / MATURITY_REL).read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("topics"), list):
        raise TypeError("config/theorem_maturity.yaml has no topics list")
    symbols: dict[str, set[str]] = {}
    for row in payload["topics"]:
        if not isinstance(row, dict) or not _nonempty_str(row.get("id")):
            raise ValueError("theorem maturity rows must carry a string id")
        accepted: set[str] = set()
        for field in ("primary_theorem", "supporting_theorems", "boundary_theorems"):
            values = row.get(field)
            if isinstance(values, str):
                accepted.add(values)
            elif isinstance(values, list):
                accepted.update(v for v in values if isinstance(v, str))
        symbols[str(row["id"])] = accepted
    return symbols


def _load_entries(root: Path) -> tuple[list[Any] | None, list[str]]:
    """Load the map's entries; return them with any structural defect lines."""
    try:
        payload = yaml.safe_load((root / MAP_REL).read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        return None, [f"{MAP_REL}: unreadable notation map ({exc})"]
    if not isinstance(payload, dict):
        return None, [f"{MAP_REL}: root must be a mapping"]
    if payload.get("schema_version") != MAP_SCHEMA_VERSION:
        return None, [
            f"schema_version must be {MAP_SCHEMA_VERSION}, got {payload.get('schema_version')!r}",
        ]
    entries = payload.get("entries")
    if not isinstance(entries, list) or not entries:
        return None, [f"{MAP_REL}: entries must be a nonempty list"]
    return entries, []


def validate_map(root: Path = ROOT) -> list[str]:
    """Return one defect line per schema, roster, symbol, or grammar drift."""
    entries, defects = _load_entries(root)
    if entries is None:
        return defects
    try:
        symbols = _maturity_symbols(root)
    except (OSError, ValueError, TypeError, yaml.YAMLError) as exc:
        return defects + [f"config/theorem_maturity.yaml: unreadable ({exc})"]

    seen_topics: set[str] = set()
    previous_topic: str | None = None
    for index, entry in enumerate(entries):
        label = f"entry {index + 1}"
        if not isinstance(entry, dict):
            defects.append(f"{label}: must be a mapping")
            continue
        if set(entry) != ENTRY_KEYS:
            defects.append(f"{label}: keys {sorted(entry)} != {sorted(ENTRY_KEYS)}")
            continue
        if not _nonempty_str(entry["concept"]):
            defects.append(f"{label}: concept must be a nonempty string")
        fep_lean = entry["fep_lean"]
        if not isinstance(fep_lean, dict) or set(fep_lean) != FEP_LEAN_KEYS:
            described = (
                sorted(fep_lean)
                if isinstance(fep_lean, dict)
                else type(fep_lean).__name__
            )
            defects.append(
                f"{label}: fep_lean keys {described} != {sorted(FEP_LEAN_KEYS)}"
            )
            fep_lean = None
        for field in ("geo_anchor", "correspondence", "reference"):
            if not _nonempty_str(entry[field]):
                defects.append(f"{label}: {field} must be a nonempty string")
        topic_id = fep_lean.get("topic_id") if fep_lean else None
        symbol = fep_lean.get("symbol") if fep_lean else None
        if topic_id is not None and symbol is not None:
            label = f"entry {index + 1} ({topic_id})"
            if topic_id in seen_topics:
                defects.append(f"{label}: duplicate topic id")
            seen_topics.add(topic_id)
            accepted = symbols.get(topic_id)
            if accepted is None:
                defects.append(
                    f"{label}: topic id not present in config/theorem_maturity.yaml"
                )
            elif symbol not in accepted:
                defects.append(
                    f"{label}: symbol {symbol!r} does not appear in the "
                    f"maturity surface for {topic_id}"
                )
            if previous_topic is not None and topic_id < previous_topic:
                defects.append(
                    f"{label}: entries must be sorted by topic_id "
                    f"({topic_id} follows {previous_topic})"
                )
            previous_topic = topic_id
        anchor = entry["geo_anchor"]
        if _nonempty_str(anchor) and not ANCHOR_RE.match(anchor):
            defects.append(
                f"{label}: geo_anchor {anchor!r} does not match "
                "GEO-INFER-<MOD>/<path>.py::<Symbol>"
            )
    return defects


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help=(
            "read-only freshness gate: validate the map and fail closed on "
            "any drift (the checker never writes in either mode)"
        ),
    )
    parser.parse_args(argv)
    defects = validate_map()
    if defects:
        for defect in defects:
            print(f"MISMATCH: {defect}", file=sys.stderr)
        print(
            f"STALE: {MAP_REL} ({len(defects)} drift defects)",
            file=sys.stderr,
        )
        return 1
    count = len(yaml.safe_load((ROOT / MAP_REL).read_text(encoding="utf-8"))["entries"])
    print(f"OK: {count} notation rows validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
