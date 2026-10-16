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
LEAN_ATTRIBUTE_PREFIX = r"(?:@\[[^\]\r\n]*\][ \t]*)*"
LEAN_THEOREM_RE = re.compile(
    rf"^\s*{LEAN_ATTRIBUTE_PREFIX}(?:theorem|lemma)\s+([A-Za-z][A-Za-z0-9_]*)",
    re.MULTILINE,
)
# Canonical bodies use one simple module name per import line. Horizontal
# whitespace keeps an incomplete `import` from consuming the next command.
LEAN_IMPORT_RE = re.compile(
    rf"^[ \t]*(?P<public>public[ \t]+)?(?P<meta>meta[ \t]+)?"
    rf"import[ \t]+{_LEAN_QUALIFIED_NAME}[ \t]*\r?$",
    re.MULTILINE,
)
# User sketches can use Unicode or quoted module components. Conversion only
# needs the command prefix; canonical import hoisting uses the stricter form.
_LEAN_IMPORT_PREFIX_RE = re.compile(
    r"^[ \t]*(?P<public>public[ \t]+)?(?P<meta>meta[ \t]+)?"
    r"import[ \t]+(?=[^ \t\r\n])"
)


def _lean_source_mask(source: str) -> tuple[str, list[tuple[int, int | None]]]:
    """Mask comments/strings and locate outer block-comment boundaries."""
    output: list[str] = []
    block_comments: list[tuple[int, int | None]] = []
    block_start = 0
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
                if not block_depth:
                    block_comments.append((block_start, index + 2))
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
            block_start = index
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
    if block_depth:
        block_comments.append((block_start, None))
    return "".join(output), block_comments


def lean_code_without_comments(source: str) -> str:
    """Blank nested comments and strings while preserving source offsets.

    Lean permits nested block comments.  Regex-based structural checks must not
    accept declarations or dependencies that occur only in comments or string
    literals, while source-block extraction still needs exact byte offsets.
    Every removed non-newline character is therefore replaced with one space.
    """
    return _lean_source_mask(source)[0]


def is_lean_qualified_name(value: str) -> bool:
    """Return whether ``value`` is a simple or dot-qualified Lean name."""
    return re.fullmatch(_LEAN_QUALIFIED_NAME, value) is not None


def lean_module_source(source: str) -> str:
    """Preserve a legacy source's public surface under Lean's module system.

    Only command lines outside comments and strings are rewritten. Existing
    modules retain their declared visibility; theorem statements and proofs are
    left byte-for-byte intact.
    """
    code, block_comments = _lean_source_mask(source)
    if re.match(r"\s*module(?:\s|$)", code):
        return source
    lines = source.splitlines(keepends=True)
    commands = code.splitlines(keepends=True)
    imports = [
        (index, match)
        for index, line in enumerate(commands)
        if (match := _LEAN_IMPORT_PREFIX_RE.match(line)) is not None
    ]
    end = imports[-1][0] + 1 if imports else 0
    insertion = sum(len(line) for line in lines[:end])
    for start, stop in block_comments:
        if start < insertion and (stop is None or insertion < stop):
            if stop is None:
                # Preserve malformed input for Lean to reject; never hide the
                # visibility marker inside an unterminated trailing comment.
                return source
            insertion = stop
            break
    promoted = 0
    for index, match in imports:
        if match.group("public") is None:
            offset = (
                match.start("meta")
                if match.group("meta") is not None
                else commands[index].index("import")
            )
            lines[index] = lines[index][:offset] + "public " + lines[index][offset:]
            promoted += 1
    insertion += len("public ") * promoted
    converted = "".join(lines)
    section = "\n@[expose] public section\n"
    if insertion and converted[insertion - 1] != "\n":
        section = "\n" + section
    return "module\n" + converted[:insertion] + section + converted[insertion:]


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
    "LEAN_ATTRIBUTE_PREFIX",
    "LEAN_IMPORT_RE",
    "LEAN_THEOREM_RE",
    "is_lean_qualified_name",
    "iter_lean_namespace_scopes",
    "lean_code_without_comments",
    "lean_declaration_conclusion",
    "lean_outer_namespaces",
]
