"""Conservative Lean source-text normalization for structural validators."""

from __future__ import annotations

import re
from collections.abc import Iterator

_LEAN_QUALIFIED_NAME = r"[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)*"
_LEAN_NAMESPACE_RE = re.compile(rf"^\s*namespace\s+({_LEAN_QUALIFIED_NAME})\s*$")
_LEAN_SECTION_RE = re.compile(
    rf"^\s*(?:noncomputable\s+)?section(?:\s+({_LEAN_QUALIFIED_NAME}))?\s*$"
)
_LEAN_END_RE = re.compile(rf"^\s*end(?:\s+({_LEAN_QUALIFIED_NAME}))?\s*$")

# Canonical theorem/lemma header regex for every catalogue/registry/coverage
# consumer. Identifiers start with a letter (Lean's own rule for the names
# these bodies use); one definition, imported everywhere a theorem roster is
# parsed.
LEAN_THEOREM_RE = re.compile(
    r"^\s*(?:theorem|lemma)\s+([A-Za-z][A-Za-z0-9_]*)", re.MULTILINE
)


def lean_code_without_comments(source: str) -> str:
    """Blank nested comments and strings while preserving source offsets.

    Lean permits nested block comments.  Regex-based structural checks must not
    accept declarations or dependencies that occur only in comments or string
    literals, while source-block extraction still needs exact byte offsets.
    Every removed non-newline character is therefore replaced with one space.
    """
    output: list[str] = []
    index = 0
    block_depth = 0
    in_line_comment = False
    in_string = False
    escaped = False
    while index < len(source):
        current = source[index]
        following = source[index : index + 2]
        if in_line_comment:
            if current == "\n":
                in_line_comment = False
                output.append(current)
            else:
                output.append(" ")
            index += 1
            continue
        if block_depth:
            if following == "/-":
                block_depth += 1
                output.extend((" ", " "))
                index += 2
                continue
            if following == "-/":
                block_depth -= 1
                output.extend((" ", " "))
                index += 2
                continue
            output.append(current if current == "\n" else " ")
            index += 1
            continue
        if in_string:
            output.append(current if current == "\n" else " ")
            if escaped:
                escaped = False
            elif current == "\\":
                escaped = True
            elif current == '"':
                in_string = False
            index += 1
            continue
        if following == "--":
            in_line_comment = True
            output.extend((" ", " "))
            index += 2
            continue
        if following == "/-":
            block_depth = 1
            output.extend((" ", " "))
            index += 2
            continue
        if current == '"':
            in_string = True
            output.append(" ")
            index += 1
            continue
        output.append(current)
        index += 1
    return "".join(output)


def is_lean_qualified_name(value: str) -> bool:
    """Return whether ``value`` is a simple or dot-qualified Lean name."""
    return re.fullmatch(_LEAN_QUALIFIED_NAME, value) is not None


def iter_lean_namespace_scopes(
    source: str,
) -> Iterator[tuple[str, tuple[str, ...], str | None]]:
    """Yield comment-free lines with their active and newly opened namespaces."""
    blocks: list[tuple[str, str | None]] = []
    for line in lean_code_without_comments(source).splitlines():
        opened_namespace: str | None = None
        if match := _LEAN_NAMESPACE_RE.match(line):
            opened_namespace = match.group(1)
            blocks.append(("namespace", opened_namespace))
        elif match := _LEAN_SECTION_RE.match(line):
            blocks.append(("section", match.group(1)))
        elif match := _LEAN_END_RE.match(line):
            name = match.group(1)
            if name is None:
                if blocks:
                    blocks.pop()
            else:
                for index in range(len(blocks) - 1, -1, -1):
                    block_name = blocks[index][1]
                    if block_name == name or (
                        block_name is not None and block_name.rsplit(".", 1)[-1] == name
                    ):
                        del blocks[index:]
                        break
        namespaces = tuple(
            name for kind, name in blocks if kind == "namespace" and name is not None
        )
        yield line, namespaces, opened_namespace


def lean_outer_namespaces(source: str) -> tuple[str, ...]:
    """Return every namespace opened outside another namespace block."""
    return tuple(
        opened_namespace
        for _line, namespaces, opened_namespace in iter_lean_namespace_scopes(source)
        if opened_namespace is not None and len(namespaces) == 1
    )


def lean_declaration_conclusion(source: str) -> str:
    """Return a theorem/lemma result after its final top-level header colon."""
    code = lean_code_without_comments(source)
    proof_start = re.search(r":=\s*by\b", code)
    if proof_start is None:
        raise ValueError("Lean declaration has no `:= by` proof boundary")
    header = code[: proof_start.start()]
    paren = brace = bracket = 0
    conclusion_colon: int | None = None
    for index, character in enumerate(header):
        if character == "(":
            paren += 1
        elif character == ")":
            paren = max(0, paren - 1)
        elif character == "{":
            brace += 1
        elif character == "}":
            brace = max(0, brace - 1)
        elif character == "[":
            bracket += 1
        elif character == "]":
            bracket = max(0, bracket - 1)
        elif character == ":" and paren == brace == bracket == 0:
            conclusion_colon = index
    if conclusion_colon is None:
        raise ValueError("Lean declaration has no top-level conclusion colon")
    conclusion = header[conclusion_colon + 1 :].strip()
    if not conclusion:
        raise ValueError("Lean declaration conclusion is empty")
    return conclusion


__all__ = [
    "LEAN_THEOREM_RE",
    "is_lean_qualified_name",
    "iter_lean_namespace_scopes",
    "lean_code_without_comments",
    "lean_declaration_conclusion",
    "lean_outer_namespaces",
]
