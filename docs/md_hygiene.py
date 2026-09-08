#!/usr/bin/env python3
"""Lint Markdown hygiene under this checkout's ``docs/`` directory.

Checks (in order)
-----------------
1. **Trailing newline** — every file must end with ``\\n``.
2. **Header spacing** — ``##Title`` → ``## Title``.
3. **List marker spacing** — ``-item`` / ``*item`` / ``+item`` → ``- item`` etc.
   (``*`` followed by another ``*`` is treated as bold/italic, not a list.)
4. **Line length** *(--max-line N)* — warns on lines longer than ``N`` chars.
   Disabled by default to avoid noisy warnings on wide tables (prefer a short table
   plus a pointer to ``configuration.md`` for large env-var matrices).
5. **Duplicate H1** — warns when a file has more than one ``# Title`` heading.
6. **Orphan bracket** *(--strict)* — flags ``[text]`` not followed by ``(...)`` or ``[...]``
   (likely a broken reference link).
7. **Trailing whitespace** *(--strict)* — flags lines ending in one or more spaces.
8. **Tab characters** *(--strict)* — flags tabs outside of code blocks.

Exit codes
----------

- ``0`` — no issues.
- ``1`` — at least one issue found (CI-friendly).

Usage
-----

.. code-block:: bash

    uv run python md_hygiene.py                      # default checks
    uv run python md_hygiene.py --max-line 120       # also warn on lines >120 chars
    uv run python md_hygiene.py --strict             # include orphan brackets, trailing WS, tabs
    uv run python md_hygiene.py --include-root       # also lint ../README.md, ../AGENTS.md, ../SPEC.md
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

DOCS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = DOCS_DIR.parent

# Fenced-code boundaries (```lang  …  ```)
_FENCE = re.compile(r"^\s*```")
# H1 headings (for duplicate-H1 detection)
_H1 = re.compile(r"^#\s+\S")
# Any heading 1–6
_HEADING = re.compile(r"^(#{1,6})([^ #]|\s*$)")
# List markers: '-', '+', or '*' not followed by '*' (bold/italic)
_LIST_BAD = re.compile(r"^(\s*)([-+]|\*(?!\*))[^ \n\-\*]")
# Orphan reference bracket: [text] not followed by ( or [
_ORPHAN_BRACKET = re.compile(r"\[[^\]\n]+\](?![\(\[:])")
# Trailing whitespace
_TRAILING_WS = re.compile(r"[ \t]+$")
# Inline code span (single or double backtick). We strip these before running
# the orphan-bracket check so code-like tokens such as `[tool.pytest]` don't fire.
_INLINE_CODE = re.compile(r"`{1,2}[^`\n]+?`{1,2}")
# Table-row heuristic: line starts with '|' (possibly after leading whitespace)
_TABLE_ROW = re.compile(r"^\s*\|")


def lint_file(
    path: Path,
    *,
    max_line: int | None,
    strict: bool,
) -> list[str]:
    """Return a list of human-readable issues in ``path``."""
    issues: list[str] = []
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"cannot read {path}: {exc}"]

    if not content.endswith("\n"):
        issues.append(f"{path.name}: file does not end with a newline")

    lines = content.splitlines()
    h1_count = 0
    in_code = False

    for i, line in enumerate(lines, start=1):
        if _FENCE.match(line):
            in_code = not in_code
            continue

        # --- checks that DO run inside code blocks ---
        # (none currently; reserved for future backtick-balance checks)

        if in_code:
            continue

        # --- checks that skip code blocks ---
        if _H1.match(line):
            h1_count += 1

        # Header spacing
        m = _HEADING.match(line)
        if m:
            rest = line[len(m.group(1)) :]
            if rest and not rest.startswith(" ") and not rest.startswith("#"):
                issues.append(
                    f"{path.name}:{i}: header missing space after '{m.group(1)}': {line.rstrip()}"
                )

        # List marker spacing (skip HTML comments)
        if "<!--" not in line and _LIST_BAD.match(line):
            issues.append(
                f"{path.name}:{i}: list marker missing trailing space: {line.rstrip()}"
            )

        # Line length — tolerant of table rows (pipe tables have long rows
        # by design) and of lines that are essentially one long link.
        if max_line is not None and len(line) > max_line and not _TABLE_ROW.match(line):
            issues.append(f"{path.name}:{i}: line length {len(line)} > {max_line}")

        if strict:
            # Orphan reference brackets (likely broken link). Strip inline
            # code spans first so tokens like `[tool.pytest]` or `["src"]`
            # inside backticks don't register as orphans.
            line_no_code = _INLINE_CODE.sub("", line)
            for m in _ORPHAN_BRACKET.finditer(line_no_code):
                token = m.group(0)
                inner = token[1:-1]
                # Skip footnotes like [^1] and task-list [x]/[ ]
                if token.startswith("[^") or token in ("[x]", "[ ]", "[X]"):
                    continue
                # Skip GitHub-flavored admonitions: [!NOTE], [!WARNING], etc.
                if inner.startswith("!") and inner[1:].isupper():
                    continue
                # Skip obvious label tokens (single uppercase word)
                if re.fullmatch(r"[A-Z][A-Z0-9_]{1,10}", inner):
                    continue
                # Skip math-like notation: pipes (KL divergence), function
                # calls, integrals, partial derivatives, etc.
                if any(ch in inner for ch in "|·∫∑∂∇∞∈≤≥≠⟨⟩∀∃"):
                    continue
                if "(" in inner and ")" in inner:
                    # Looks like a function expression: log p(o), x(t), etc.
                    continue
                # Skip math tuples / function arguments: [q,p], [x, y, z]
                if "," in inner and not any(c in inner for c in ".:/"):
                    continue
                issues.append(
                    f"{path.name}:{i}: orphan bracket (likely broken link): {token}"
                )

            # Trailing whitespace
            if _TRAILING_WS.search(line):
                issues.append(f"{path.name}:{i}: trailing whitespace")

            # Tabs outside code blocks
            if "\t" in line:
                issues.append(f"{path.name}:{i}: tab character (use spaces)")

    if h1_count > 1:
        issues.append(f"{path.name}: {h1_count} top-level '# …' headings (expected 1)")

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    parser.add_argument(
        "--max-line",
        type=int,
        default=None,
        metavar="N",
        help="Warn on lines longer than N characters (default: disabled).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Also check for orphan brackets, trailing whitespace, and tabs.",
    )
    parser.add_argument(
        "--include-root",
        action="store_true",
        help="Also lint sibling files (../README.md, ../AGENTS.md, ../SPEC.md, ../PAI.md).",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print every file scanned.",
    )
    args = parser.parse_args()

    # The manuscript subdirectory is gated by docs/xref_audit.py; its pandoc
    # citations and render-time placeholders are not plain-markdown issues.
    files = sorted(
        path
        for path in DOCS_DIR.glob("**/*.md")
        if DOCS_DIR / "manuscript" not in path.parents
    )
    if args.include_root:
        for name in ("README.md", "AGENTS.md", "SPEC.md", "PAI.md"):
            p = PROJECT_ROOT / name
            if p.exists():
                files.append(p)

    total = 0
    scanned = 0
    for path in files:
        issues = lint_file(path, max_line=args.max_line, strict=args.strict)
        scanned += 1
        if issues:
            for msg in issues:
                print(msg)
            total += len(issues)
        elif args.verbose:
            print(f"OK  {path.relative_to(PROJECT_ROOT)}")

    if total:
        print(f"\nFAIL: {total} issue(s) across {scanned} file(s)")
        return 1
    print(f"OK: {scanned} file(s) scanned — no hygiene issues.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
