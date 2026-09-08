#!/usr/bin/env python3
"""Validate internal Markdown links and optional anchors under ``docs/``.

Features
--------
- Recognises ``[text](path)``, ``[text](path#anchor)``, and ``<url>`` inline links.
- Resolves relative links against the source file's directory; checks existence.
- Skips ``http://``, ``https://``, ``mailto:``, standalone ``#anchors``, and
  protocol-relative ``//`` links (same as before, but with clearer rules).
- **New**: ``--strict`` validates that a ``#anchor`` actually exists in the
  target markdown (heading slugs and explicit HTML ``id="..."`` attributes).
- **New**: exits with code ``1`` if any issue is found (suitable for CI).
- ``--include-root`` also scans repository-root documents (``README.md``,
  ``AGENTS.md``, ``SPEC.md``, ``PAI.md``) to catch link rot at the project level.

After editing anchors in cross-link hubs such as ``pipeline.md`` or ``configuration.md``,
run ``--strict`` so new ``#heading`` fragments resolve.

Usage
-----

.. code-block:: bash

    uv run python check_links.py                 # docs/ only, no anchors
    uv run python check_links.py --strict        # docs/ + anchor validation
    uv run python check_links.py --include-root  # also scan project-level docs
    uv run python check_links.py --strict -v     # verbose: print every file scanned
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

DOCS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = DOCS_DIR.parent

# Inline links:  [text](path)  or  [text](path#anchor "title")
_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(\s*([^)\s]+)(?:\s+\"[^\"]*\")?\s*\)")
# Auto-links: <https://…>
_AUTOLINK = re.compile(r"<(https?://[^>]+)>")
# Heading for slug generation: #, ##, ###, etc.
_HEADING = re.compile(r"^(#+)\s+(.*?)\s*$")
# Explicit {#anchor} attribute after a heading (pandoc-style)
_EXPLICIT_ANCHOR = re.compile(r"\{#([A-Za-z0-9_-]+)\}")
# HTML id attribute (inline anchors)
_HTML_ID = re.compile(r'\bid=["\']([A-Za-z0-9_-]+)["\']')


def slugify(heading_text: str) -> str:
    """Approximate GitHub/pandoc slug: lowercase, spaces → ``-``, strip punctuation."""
    text = heading_text.strip().lower()
    # Strip explicit {#id} attributes before slugifying
    text = _EXPLICIT_ANCHOR.sub("", text).strip()
    # Remove anything that isn't alnum, whitespace, or hyphen
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    text = re.sub(r"[\s_]+", "-", text, flags=re.UNICODE)
    return text.strip("-")


def collect_anchors(md_text: str) -> set[str]:
    """Return the set of anchor strings that a ``#anchor`` link can legitimately target."""
    anchors: set[str] = set()
    for line in md_text.splitlines():
        m = _HEADING.match(line)
        if m:
            heading = m.group(2)
            # Slug form
            anchors.add(slugify(heading))
            # Explicit {#id}
            explicit = _EXPLICIT_ANCHOR.search(heading)
            if explicit:
                anchors.add(explicit.group(1))
        for html in _HTML_ID.findall(line):
            anchors.add(html)
    return anchors


def is_external(url: str) -> bool:
    url = url.strip()
    return url.startswith(
        ("http://", "https://", "mailto:", "ftp://", "//", "#", "tel:")
    )


def check_file(
    filepath: Path,
    *,
    strict: bool,
    anchor_cache: dict[Path, set[str]],
) -> list[str]:
    """Return a list of human-readable issues found in ``filepath``."""
    issues: list[str] = []
    try:
        content = filepath.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"cannot read {filepath}: {exc}"]

    links: list[tuple[int, str]] = []
    for lineno, line in enumerate(content.splitlines(), 1):
        for _, url in _LINK_PATTERN.findall(line):
            links.append((lineno, url))
        for url in _AUTOLINK.findall(line):
            links.append((lineno, url))

    for lineno, url in links:
        # Skip externals and standalone in-page anchors
        if url.startswith("#"):
            if strict:
                anchors = collect_anchors(content)
                target = url.lstrip("#")
                if target and target not in anchors:
                    issues.append(
                        f"{filepath.name}:{lineno}: in-page anchor '#{target}' "
                        f"not found in same file"
                    )
            continue
        if is_external(url):
            continue

        # Split off #anchor fragment (if any)
        path_part, _, anchor = url.partition("#")
        if not path_part:
            continue

        target_path = (filepath.parent / path_part).resolve()

        if not target_path.exists():
            issues.append(
                f"{filepath.name}:{lineno}: broken link → {url}  "
                f"(resolved to {target_path})"
            )
            continue

        # Anchor validation for cross-file links (--strict only)
        if strict and anchor and target_path.suffix.lower() == ".md":
            anchors = anchor_cache.get(target_path)
            if anchors is None:
                try:
                    anchors = collect_anchors(target_path.read_text(encoding="utf-8"))
                except OSError:
                    anchors = set()
                anchor_cache[target_path] = anchors
            if anchor not in anchors:
                issues.append(
                    f"{filepath.name}:{lineno}: anchor '#{anchor}' not found in "
                    f"{target_path.name} (known: {len(anchors)} headings)"
                )

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Also validate #anchor references against target-file headings.",
    )
    parser.add_argument(
        "--include-root",
        action="store_true",
        help="Also scan sibling files (../README.md, ../AGENTS.md, ../SPEC.md, ../PAI.md).",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print every file scanned, not just the summary.",
    )
    args = parser.parse_args()

    # The manuscript subdirectory is gated by docs/xref_audit.py, which
    # understands the render-time template placeholders and pipeline-relative
    # figure paths the chapters use; the plain link audit skips it.
    files: list[Path] = sorted(
        path
        for path in DOCS_DIR.glob("**/*.md")
        if DOCS_DIR / "manuscript" not in path.parents
    )
    if args.include_root:
        for name in ("README.md", "AGENTS.md", "SPEC.md", "PAI.md"):
            p = PROJECT_ROOT / name
            if p.exists():
                files.append(p)

    anchor_cache: dict[Path, set[str]] = {}
    total_issues = 0
    scanned = 0

    for file in files:
        issues = check_file(file, strict=args.strict, anchor_cache=anchor_cache)
        scanned += 1
        if issues:
            for msg in issues:
                print(msg)
            total_issues += len(issues)
        elif args.verbose:
            print(f"OK  {file.relative_to(PROJECT_ROOT)}")

    if total_issues:
        print(
            f"\nFAIL: {total_issues} issue(s) across {scanned} file(s)"
            f"{' (strict)' if args.strict else ''}"
        )
        return 1

    print(
        f"OK: {scanned} file(s) scanned"
        f"{' (strict; anchors validated)' if args.strict else ''}"
        f" — no broken links."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
# Integrated into validation via `infrastructure.validation.cli` and the fep_lean pipeline.
