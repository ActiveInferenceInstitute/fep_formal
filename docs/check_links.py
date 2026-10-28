#!/usr/bin/env python3
"""Validate internal Markdown links and optional anchors under ``docs/``.

Features
--------
- Recognises Markdown links/images and reference definitions outside code literals.
- Resolves relative links against the source file's directory; checks existence.
- Skips ``http://``, ``https://``, ``mailto:``, standalone ``#anchors``, and
  protocol-relative ``//`` links (same as before, but with clearer rules).
- **New**: ``--strict`` validates that a ``#anchor`` actually exists in the
  target markdown (heading slugs and explicit HTML ``id="..."`` attributes).
- **New**: exits with code ``1`` if any issue is found (suitable for CI).
- ``--include-root`` widens the scan to the repository's authored Markdown: every
  root ``*.md``, every ``AGENTS.md`` / ``README.md`` under ``src/``, ``tests/``,
  ``config/``, ``scripts/``, ``lean/`` and ``manuscript/``, and the non-historical
  documents under ``specs/`` and ``.github/``. It also requires a fresh generated
  ``.github/README.md`` projection of the authoritative root ``README.md``.
  Historical trees (``specs/done/**``,
  ``specs/**/evidence/**``, ``gnn_output*``, ``gnn-input``, ``fixtures``) are
  explicitly excluded: they are retained receipts and are never rewritten.

After editing anchors in cross-link hubs such as ``pipeline.md`` or ``configuration.md``,
run ``--strict`` so new ``#heading`` fragments resolve.

Usage
-----

.. code-block:: bash

    uv run python check_links.py                 # docs/ only, no anchors
    uv run python check_links.py --strict        # docs/ + anchor validation
    uv run python check_links.py --include-root  # also scan project-level docs
    uv run python check_links.py --include-root --write-github-readme
    uv run python check_links.py --strict -v     # verbose: print every file scanned
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

DOCS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = DOCS_DIR.parent

# --- Scan scope (kept identical in ``check_links.py`` and ``md_hygiene.py``) ---
# ``--include-root`` widens the scan from ``docs/**`` to the whole repository's
# authored Markdown: every root ``*.md``, every ``AGENTS.md`` / ``README.md``
# under the subtrees below, and maintained ``specs/`` / ``.github/`` Markdown.
CONTRACT_SUBTREES = ("src", "tests", "config", "scripts", "lean", "manuscript")
CONTRACT_NAMES = frozenset({"AGENTS.md", "README.md"})
# Historical / retained trees: ``specs/done/**`` and per-spec ``evidence/**``
# are frozen receipts (their bytes may be hashed), and ``gnn_output*`` /
# ``gnn-input`` / ``fixtures`` are tool outputs or tool inputs. They are never
# scanned and never rewritten; a link broken there is annotated, not edited.
HISTORICAL_DIR_NAMES = frozenset({"done", "evidence", "gnn-input", "fixtures"})
HISTORICAL_DIR_PREFIXES = ("gnn_output",)
# Vendored / build directories that can hold third-party Markdown.
_SKIP_DIR_NAMES = frozenset({"node_modules", "build", "__pycache__", "site-packages"})


def _label(path: Path) -> str:
    """Repo-relative path for messages (falls back to the bare name outside the repo)."""
    try:
        return path.relative_to(DOCS_DIR.parent).as_posix()
    except ValueError:
        return path.name


def _skip_dir(name: str) -> bool:
    return name.startswith(".") or name in _SKIP_DIR_NAMES


def _is_historical(rel_parts: tuple[str, ...]) -> bool:
    return any(
        part in HISTORICAL_DIR_NAMES or part.startswith(HISTORICAL_DIR_PREFIXES)
        for part in rel_parts[:-1]
    )


def _walk_md(base: Path, *, names: frozenset[str] | None) -> list[Path]:
    found: list[Path] = []
    if not base.is_dir():
        return found
    for path in base.rglob("*.md"):
        rel = path.relative_to(base).parts
        if any(_skip_dir(p) for p in rel[:-1]):
            continue
        if names is not None and path.name not in names:
            continue
        found.append(path)
    return found


def discover_files(docs_dir: Path, *, include_root: bool) -> list[Path]:
    """Return the Markdown files in scope (``docs/**``, plus the repo with ``include_root``)."""
    files = sorted(docs_dir.glob("**/*.md"))
    if not include_root:
        return files
    root = docs_dir.parent
    extra: set[Path] = set(root.glob("*.md"))
    for sub in CONTRACT_SUBTREES:
        extra.update(_walk_md(root / sub, names=CONTRACT_NAMES))
    for subtree in (root / "specs", root / ".github"):
        for path in _walk_md(subtree, names=None):
            if not _is_historical(path.relative_to(subtree).parts):
                extra.add(path)
    return files + sorted(extra - set(files))


_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
_QUOTE_PREFIX = re.compile(r"^ {0,3}> ?")
_LIST_ITEM = re.compile(r"^( {0,3})(?:[-+*]|[0-9]{1,9}[.)])( +)(.*)$")
_THEMATIC_BREAK = re.compile(r"^ {0,3}(?:(?:\* *){3,}|(?:- *){3,}|(?:_ *){3,})$")
_BACKTICKS = re.compile(r"`+")
_URL_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
_LINK_SUFFIX = re.compile(
    r"\s*(?:\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'|\((?:\\.|[^)\\])*\))?\s*\)"
)
_GITHUB_README_HEADER = (
    "<!-- Generated from ../README.md by ../docs/check_links.py; "
    "edit the root README.md and regenerate. -->\n\n"
)
# Heading for slug generation: #, ##, ###, etc.
_HEADING = re.compile(r"^(#+)\s+(.*?)\s*$")
# Explicit {#anchor} attribute after a heading (pandoc-style)
_EXPLICIT_ANCHOR = re.compile(r"\{#([A-Za-z0-9_-]+)\}")
# HTML id attribute (inline anchors)
_HTML_ID = re.compile(r'\bid=["\']([A-Za-z0-9_-]+)["\']')


def _blank_literal(text: str) -> str:
    """Hide literal characters without moving source offsets or line numbers."""
    return "".join(char if char in "\r\n" else " " for char in text)


def _list_item_content(text: str) -> tuple[str, int] | None:
    """Return a list item's content and continuation indentation in columns."""
    match = _LIST_ITEM.match(text)
    if match is None or _THEMATIC_BREAK.fullmatch(text):
        return None
    # Five or more spaces after a marker leave an indented code body;
    # only one space belongs to the list marker in that case.
    width = match.start(3) if len(match[2]) <= 4 else match.start(2) + 1
    return text[width:], width


def _container_prose(
    text: str, containers: list[tuple[str, int]]
) -> tuple[str, list[tuple[str, int]], bool]:
    """Strip explicit quote/list containers, preserving their continuation widths."""
    retained: list[tuple[str, int]] = []
    new_block = False
    for kind, width in containers:
        if kind == "quote":
            match = _QUOTE_PREFIX.match(text)
            if match is None:
                break
            text = text[match.end() :]
            retained.append((kind, width))
        elif len(text) - len(text.lstrip(" ")) >= width:
            text = text[width:]
            retained.append((kind, width))
        else:
            item = _list_item_content(text)
            if item is not None:
                text, width = item
                retained.append(("list", width))
                new_block = True
            break
    while True:
        quote = _QUOTE_PREFIX.match(text)
        if quote is not None:
            text = text[quote.end() :]
            retained.append(("quote", 0))
        else:
            item = _list_item_content(text)
            if item is None:
                break
            text, width = item
            retained.append(("list", width))
        new_block = True
    return text, retained, new_block


def _continued_container_line(
    text: str, containers: tuple[tuple[str, int], ...]
) -> str | None:
    """Strip only an open fence's containers; its payload is never new prose."""
    for index, (kind, width) in enumerate(containers):
        if not text.strip():
            # A list may contain a bare blank line, but each quote prefix
            # must remain explicit inside a fenced block. Otherwise a new
            # later blockquote could be hidden by an earlier unclosed fence.
            return None if any(k == "quote" for k, _ in containers[index:]) else ""
        if kind == "quote":
            quote = _QUOTE_PREFIX.match(text)
            if quote is None:
                return None
            text = text[quote.end() :]
        elif len(text) - len(text.lstrip(" ")) >= width:
            text = text[width:]
        else:
            return None
    return text


def _mask_block_code(text: str) -> str:
    """Mask indented/fenced code, including explicit quote/list containers.

    Indentation is measured after container prefixes. Indented lines cannot
    interrupt an existing paragraph, so continuation prose remains auditable.
    This is a bounded block recognizer, not a complete CommonMark renderer.
    """
    marker = ""
    containers: list[tuple[str, int]] = []
    fence_containers: tuple[tuple[str, int], ...] = ()
    paragraph_open = False
    result: list[str] = []
    for line in text.splitlines(keepends=True):
        body = line.rstrip("\r\n").expandtabs(4)
        if marker:
            fenced_body = _continued_container_line(body, fence_containers)
            if fenced_body is not None:
                result.append(_blank_literal(line))
                if re.fullmatch(
                    rf" {{0,3}}{re.escape(marker[0])}{{{len(marker)},}} *", fenced_body
                ):
                    marker = ""
                paragraph_open = False
                continue
            # A contained fence ends when its explicit container ends, even
            # if it omitted a closing delimiter. Following prose stays live.
            marker = ""
            paragraph_open = False
        if not body.strip():
            result.append(line)
            paragraph_open = False
            continue
        body, containers, new_block = _container_prose(body, containers)
        if new_block:
            paragraph_open = False
        if body.startswith("    ") and not paragraph_open:
            result.append(_blank_literal(line))
            continue
        match = _FENCE.match(body)
        if match and not (match[1].startswith("`") and "`" in match[2]):
            marker = match[1]
            fence_containers = tuple(containers)
            result.append(_blank_literal(line))
            paragraph_open = False
        else:
            result.append(line)
            paragraph_open = bool(body.strip()) and not (
                re.match(r"^ {0,3}(?:#{1,6}(?: |$)|=+ *$|-+ *$)", body)
                or _THEMATIC_BREAK.fullmatch(body)
            )
    return "".join(result)


def _is_escaped(text: str, index: int) -> bool:
    preceding = index - 1
    while preceding >= 0 and text[preceding] == "\\":
        preceding -= 1
    return (index - preceding - 1) % 2 == 1


def _markdown_prose(text: str) -> str:
    """Mask block code and inline spans before interpreting destinations."""
    prose = _mask_block_code(text)
    runs = list(_BACKTICKS.finditer(prose))
    chars = list(prose)
    covered = 0
    for index, opening in enumerate(runs):
        if opening.start() < covered or _is_escaped(prose, opening.start()):
            continue
        for closing in runs[index + 1 :]:
            if re.search(r"\n[ \t]*\n", prose[opening.end() : closing.start()]):
                break
            if len(closing[0]) == len(opening[0]):
                covered = closing.end()
                chars[opening.start() : covered] = _blank_literal(
                    prose[opening.start() : covered]
                )
                break
    return "".join(chars)


def _closing_bracket(text: str, start: int) -> int | None:
    depth = 1
    cursor = start + 1
    while cursor < len(text):
        char = text[cursor]
        if char == "\\":
            cursor += 2
            continue
        if char == "\n" and re.match(r"[ \t]*\n", text[cursor + 1 :]):
            return None
        if char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if not depth:
                return cursor
        cursor += 1
    return None


def _destination_bounds(
    text: str, start: int, *, reference: bool
) -> tuple[int, int, int] | None:
    """Return destination and containing-link bounds, including nested URLs."""
    cursor = start
    if cursor >= len(text):
        return None
    if text[cursor] == "<":
        start = cursor = cursor + 1
        while cursor < len(text) and text[cursor] not in ">\r\n":
            cursor += 2 if text[cursor] == "\\" else 1
        if cursor >= len(text) or text[cursor] != ">":
            return None
        end, after = cursor, cursor + 1
    else:
        depth = 0
        while cursor < len(text):
            char = text[cursor]
            if char == "\\" and cursor + 1 < len(text):
                cursor += 2
                continue
            if char.isspace() or (char == ")" and not depth):
                break
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
            cursor += 1
        if depth:
            return None
        end = after = cursor
    if end == start:
        return None
    if reference:
        line_end = text.find("\n", after)
        return start, end, len(text) if line_end == -1 else line_end
    suffix = _LINK_SUFFIX.match(text, after)
    return None if suffix is None else (start, end, suffix.end())


def markdown_destinations(text: str) -> list[tuple[int, int]]:
    """Locate inline/image/reference URLs while preserving literal source bytes."""
    prose = _markdown_prose(text)
    destinations: list[tuple[int, int]] = []
    excluded: list[tuple[int, int]] = []
    for opening in re.finditer(r"\[", prose):
        start = opening.start()
        if _is_escaped(prose, start) or any(a <= start < b for a, b in excluded):
            continue
        closing = _closing_bracket(prose, start)
        if closing is None or closing + 1 >= len(prose):
            continue
        reference = prose[closing + 1] == ":"
        if reference:
            line_start = prose.rfind("\n", 0, start) + 1
            if prose[start + 1 : closing].startswith("^") or not re.fullmatch(
                r" {0,3}", prose[line_start:start]
            ):
                continue
        elif prose[closing + 1] != "(":
            continue
        cursor = closing + 2
        while cursor < len(prose) and prose[cursor].isspace():
            cursor += 1
        bounds = _destination_bounds(prose, cursor, reference=reference)
        if bounds is not None:
            first, last, link_end = bounds
            destinations.append((first, last))
            # Nested badge images in the label have their own destinations;
            # bracket-like examples inside the URL or title do not.
            excluded.append((closing + 1, link_end))
    return sorted(destinations)


def render_github_readme(source: str) -> str:
    """Project root README links to ``.github/`` without editing code examples."""
    result = source
    for start, end in reversed(markdown_destinations(source)):
        url = source[start:end]
        if not url.startswith(("/", "#", "?")) and not _URL_SCHEME.match(url):
            result = result[:start] + "../" + url + result[end:]
    return _GITHUB_README_HEADER + result


def github_readme_issues(root: Path, *, write: bool = False) -> list[str]:
    """Require or explicitly regenerate the mirror from its sole root owner."""
    source = root / "README.md"
    target = root / ".github" / "README.md"
    if source.is_symlink() or target.parent.is_symlink() or target.is_symlink():
        return [
            "README projection source, .github directory and target must not be symlinks"
        ]
    try:
        expected = render_github_readme(source.read_bytes().decode("utf-8")).encode(
            "utf-8"
        )
        if write:
            target.parent.mkdir(exist_ok=True)
            target.write_bytes(expected)
        elif not target.is_file() or target.read_bytes() != expected:
            return [
                (
                    ".github/README.md is missing or stale; regenerate from README.md with "
                    "uv run python docs/check_links.py --include-root --write-github-readme"
                )
            ]
    except (OSError, UnicodeError) as exc:
        return [f"cannot project README.md to .github/README.md: {exc}"]
    return []


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
    for line in _mask_block_code(md_text).splitlines():
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
    return bool(_URL_SCHEME.match(url)) or url.startswith(("//", "#"))


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

    links = [
        (content.count("\n", 0, start) + 1, content[start:end])
        for start, end in markdown_destinations(content)
    ]

    for lineno, url in links:
        # Skip externals and standalone in-page anchors
        if url.startswith("#"):
            if strict:
                anchors = collect_anchors(content)
                target = url.lstrip("#")
                if target and target not in anchors:
                    issues.append(
                        f"{_label(filepath)}:{lineno}: in-page anchor '#{target}' "
                        f"not found in same file"
                    )
            continue
        if is_external(url):
            continue

        # Split off #anchor fragment (if any)
        parsed = urlsplit(url)
        path_part = unquote(re.sub(r"\\([^\w\s])", r"\1", parsed.path))
        anchor = unquote(parsed.fragment)
        if not path_part:
            continue

        target_path = (filepath.parent / path_part).resolve()

        if not target_path.exists():
            issues.append(
                f"{_label(filepath)}:{lineno}: broken link → {url}  "
                f"(resolved to {target_path})"
            )
            continue

        # Anchor validation for cross-file links (--strict only)
        if strict and anchor and target_path.suffix.lower() == ".md":
            cached_anchors = anchor_cache.get(target_path)
            if cached_anchors is None:
                try:
                    cached_anchors = collect_anchors(
                        target_path.read_text(encoding="utf-8")
                    )
                except OSError:
                    cached_anchors = set()
                anchor_cache[target_path] = cached_anchors
            if anchor not in cached_anchors:
                issues.append(
                    f"{_label(filepath)}:{lineno}: anchor '#{anchor}' not found in "
                    f"{target_path.name} (known: {len(cached_anchors)} headings)"
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
        help="Also scan root/subtree contracts and maintained specs/.github Markdown; require a fresh .github/README.md projection.",
    )
    parser.add_argument(
        "--write-github-readme",
        action="store_true",
        help="Regenerate .github/README.md from root README.md; implies --include-root.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print every file scanned, not just the summary.",
    )
    args = parser.parse_args()

    include_root = args.include_root or args.write_github_readme
    if include_root:
        mirror_issues = github_readme_issues(
            DOCS_DIR.parent, write=args.write_github_readme
        )
        if mirror_issues:
            for issue in mirror_issues:
                print(issue)
            return 1
    files = discover_files(DOCS_DIR, include_root=include_root)

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
