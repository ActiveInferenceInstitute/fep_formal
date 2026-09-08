#!/usr/bin/env python3
"""Audit cross-reference integrity against the pandoc-crossref standard.

Scope
-----

The audit runs over **exactly the files the renderer emits** --
``fep_lean.output.rendering.manuscript_source_files`` -- rather than re-globbing
``manuscript/*.md``. A gate that measures a different file set than the artifact
reports "all resolve" while references dangle in every produced PDF, which is
what a wider glob did here: the excluded ``09z_unified_formalism_catalogue.md``
supplied 27 anchor definitions that no rendered section can see.

Standard enforced
-----------------

Definitions are pandoc anchors carrying a prefix -- ``{#sec:x}``, ``{#eq:x}``,
``{#fig:x width=80%}``, ``{#tbl:x}``. References are the pandoc-crossref bracket
form ``[@sec:x]`` / ``[@eq:x]`` / ``[@fig:x]`` / ``[@tbl:x]``.

Four failure classes, each reported with ``file:line``:

1. ``raw-ref`` -- ``\\ref``/``\\eqref``/``\\cref``/``\\Cref``/``\\autoref``/
   ``\\nameref`` in Markdown. These survive the LaTeX path but pandoc deletes
   them from HTML, so they are not portable across output formats.
2. ``raw-equation`` -- ``\\begin{equation}`` or a ``$$\\label{...}`` line.
   pandoc parses the former as a RawBlock that ``pandoc-crossref`` cannot see
   and renders the latter as an unnumbered display, so neither can ever carry a
   resolvable equation number. The crossref form is ``$$ ... $$ {#eq:x}``.
3. ``hand-number`` -- a hand-typed ``Figure 3`` / ``Table 1`` / ``Section 2``.
   Numbering is the filter's to assign; a typed literal silently goes stale.
4. ``unresolved`` -- a ``[@prefix:id]`` reference whose anchor is defined in no
   rendered file.

Exit codes
----------

- ``0`` -- every reference resolves and no forbidden construct is present.
- ``1`` -- at least one finding (CI-friendly).

Usage
-----

.. code-block:: bash

    uv run python docs/xref_audit.py            # default
    uv run python docs/xref_audit.py --verbose  # list every defined anchor
    uv run python docs/xref_audit.py --root path/to/docs/manuscript
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

DOCS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = DOCS_DIR.parent
DEFAULT_ROOT = PROJECT_ROOT / "docs" / "manuscript"

if str(PROJECT_ROOT / "src") not in sys.path:  # pragma: no cover - import shim
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from fep_lean.output.rendering import manuscript_source_files

#: Anchor definition. Tolerates trailing attributes (``{#fig:x width=100%}``).
_RE_ANCHOR = re.compile(r"\{#([A-Za-z]+:[\w:.-]+)(?=[\s}])")
#: pandoc-crossref reference, including ``[@a:x; @a:y]`` continuations.
_RE_BRACKET_REF = re.compile(r"[\[;]\s*@([A-Za-z]+:[\w:.-]+)")
_RE_RAW_REF = re.compile(r"\\(?:ref|eqref|cref|Cref|autoref|nameref)\{([\w:.-]+)\}")
_RE_RAW_EQUATION = re.compile(r"\\begin\{equation\*?\}|^\$\$\\label\{")
_RE_HAND_NUMBER = re.compile(r"\b(?:Figure|Table|Section|Equation|Appendix)\s+\d+\b")

#: Prefixes pandoc-crossref owns. Other anchors (plain ids) are not audited.
_CROSSREF_PREFIXES = ("sec", "eq", "fig", "tbl", "lst")


class Finding(tuple[str, Path, int, str]):
    """``(kind, path, line, detail)`` -- a tuple subclass for stable sorting."""

    __slots__ = ()


def _iter_prose_lines(text: str) -> list[tuple[int, str]]:
    """Yield ``(lineno, line)`` outside fenced code blocks."""
    out: list[tuple[int, str]] = []
    in_fence = False
    for number, line in enumerate(text.splitlines(), start=1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        out.append((number, line))
    return out


def audit(
    files: tuple[Path, ...],
    definition_files: tuple[Path, ...] | None = None,
) -> tuple[list[Finding], set[str], set[str]]:
    """Return findings plus the defined-anchor and referenced-id sets.

    Definitions are collected from ``definition_files`` when given, falling
    back to ``files``. Generated appendix projections are excluded from the
    renderable source list but still define anchors that chapters reference,
    so callers pass the full manuscript glob as ``definition_files``.
    """
    defined: set[str] = set()
    for path in definition_files if definition_files is not None else files:
        for _, line in _iter_prose_lines(path.read_text(encoding="utf-8")):
            defined |= set(_RE_ANCHOR.findall(line))
    referenced: set[str] = set()
    ref_origin: dict[str, list[tuple[Path, int]]] = defaultdict(list)
    findings: list[Finding] = []

    parsed: list[tuple[Path, list[tuple[int, str]]]] = []
    for path in files:
        lines = _iter_prose_lines(path.read_text(encoding="utf-8"))
        parsed.append((path, lines))

    for path, lines in parsed:
        for number, line in lines:
            for match in _RE_RAW_REF.finditer(line):
                findings.append(
                    Finding(("raw-ref", path, number, f"\\ref{{{match.group(1)}}}"))
                )
            if _RE_RAW_EQUATION.search(line):
                findings.append(
                    Finding(("raw-equation", path, number, line.strip()[:60]))
                )
            for match in _RE_HAND_NUMBER.finditer(line):
                findings.append(Finding(("hand-number", path, number, match.group(0))))
            for match in _RE_BRACKET_REF.finditer(line):
                ref_id = match.group(1)
                if ref_id.split(":", 1)[0] not in _CROSSREF_PREFIXES:
                    continue  # a bibliography key such as [@friston2010], not a xref
                referenced.add(ref_id)
                ref_origin[ref_id].append((path, number))

    for ref_id in sorted(referenced - defined):
        for path, number in ref_origin[ref_id]:
            findings.append(Finding(("unresolved", path, number, f"[@{ref_id}]")))

    findings.sort(key=lambda f: (f[0], str(f[1]), f[2]))
    return findings, defined, referenced


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_ROOT,
        help="Manuscript directory to scan (default: checkout manuscript/).",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Also list every anchor definition found.",
    )
    args = parser.parse_args(argv)

    root: Path = args.root.resolve()
    if not root.exists():
        print(f"FAIL: manuscript root does not exist: {root}")
        return 1

    files = manuscript_source_files(root)
    if not files:
        print(f"FAIL: no renderable *.md files under {root}")
        return 1

    findings, defined, referenced = audit(files, tuple(sorted(root.glob("*.md"))))

    if findings:
        for kind, path, number, detail in findings:
            try:
                rel = path.relative_to(PROJECT_ROOT)
            except ValueError:
                rel = path
            print(f"{rel}:{number}: {kind}: {detail}")
        print()
        counts: dict[str, int] = defaultdict(int)
        for kind, _, _, _ in findings:
            counts[kind] += 1
        breakdown = ", ".join(f"{kind}={counts[kind]}" for kind in sorted(counts))
        print(
            f"FAIL: {len(findings)} finding(s) over {len(files)} rendered file(s) "
            f"[{breakdown}]; {len(defined)} anchors defined, "
            f"{len(referenced)} crossref reference(s)."
        )
        return 1

    if args.verbose:
        print(f"Anchors ({len(defined)}):")
        for anchor in sorted(defined):
            print(f"  {anchor}")

    print(
        f"OK: {len(files)} rendered file(s), {len(defined)} anchor(s) defined, "
        f"{len(referenced)} crossref reference(s) — all resolve, "
        "no forbidden construct."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
