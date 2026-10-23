"""Conservative Lean source-text normalization for structural validators."""

from __future__ import annotations

import re
from collections.abc import Iterator
from functools import lru_cache

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
    rf"^\s*{LEAN_ATTRIBUTE_PREFIX}(?:public\s+)?(?:theorem|lemma)\s+([A-Za-z][A-Za-z0-9_]*)(?=$|\s|[:({{\[])",
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
        if current == "'" and (
            index == 0 or not (source[index - 1].isalnum() or source[index - 1] in "_'")
        ):
            literal = re.match(
                r"'(?:\\(?:u\{[0-9a-fA-F]+\}|.)|[^'\\\n])'", source[index:]
            )
            if literal is not None:
                output.extend(" " * len(literal[0]))
                index += len(literal[0])
                continue
        if current == "«":
            quoted_end = source.find("»", index + 1)
            if quoted_end >= 0:
                output.extend(source[index : quoted_end + 1])
                index = quoted_end + 1
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


# Content identity, never filesystem identity. Bound both entry count and each
# retained source length; cache only the immutable mask, not comment boundaries.
_MASK_CACHE_MAX_ENTRIES = 32
_MASK_CACHE_MAX_SOURCE_CHARS = 16_384


@lru_cache(maxsize=_MASK_CACHE_MAX_ENTRIES)
def _cached_lean_code_without_comments(source: str) -> str:
    return _lean_source_mask(source)[0]


def lean_code_without_comments(source: str) -> str:
    """Blank nested comments and strings while preserving source offsets.

    Lean permits nested block comments.  Regex-based structural checks must not
    accept declarations or dependencies that occur only in comments or string
    literals, while source-block extraction still needs exact byte offsets.
    Every removed non-newline character is therefore replaced with one space.
    """
    if type(source) is str and len(source) <= _MASK_CACHE_MAX_SOURCE_CHARS:
        return _cached_lean_code_without_comments(source)
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
    """Return the complete supported theorem/lemma result before its proof."""
    match = LEAN_THEOREM_RE.search(lean_code_without_comments(source))
    if match is None:
        raise ValueError("Lean declaration has no theorem or lemma header")
    colon, proof = lean_theorem_header_delimiters(source, match.end())
    conclusion = lean_code_without_comments(source)[colon + 1 : proof].strip()
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


def lean_syntax_mask(source: str) -> str:
    """Mask comments and literals while preserving every source offset."""
    code = lean_code_without_comments(source)
    # Character literals and quoted identifiers must not contribute syntax.
    literals = re.compile(r"«[^»]*»|'(?:\\(?:u\{[0-9a-fA-F]+\}|.)|[^'\\\n])'")
    code = literals.sub(
        lambda match: "".join("\n" if c == "\n" else " " for c in match[0]), code
    )
    if "«" in code or "»" in code:
        raise ValueError("unsupported or unterminated Lean quoted identifier")
    return code


def lean_theorem_header_delimiters(source: str, start: int) -> tuple[int, int]:
    """Locate the goal colon and proof assignment in supported source headers.

    This is a conservative lexical extractor, not Lean elaboration. Balanced
    binders and parenthesized expressions are supported. Top-level simple
    ``let``/``letI`` initializers consume their own assignment; unparenthesized
    tactic/binder constructs in such initializers are refused rather than
    returning a truncated proposition. Returned offsets address original text.
    """
    code = lean_syntax_mask(source)
    command = re.compile(
        r"(?m)^[ \t]*(?:@\[[^\]\r\n]*\][ \t]*)*"
        r"(?:(?:public|private|protected|noncomputable|unsafe|partial)\s+)*"
        r"(?:theorem|lemma|def|abbrev|structure|instance|opaque|inductive|class|"
        r"axiom|constant|example|namespace|section|end)\b"
    )
    declaration_line = code.rfind("\n", 0, start) + 1
    declaration_indent = len(code[declaration_line:start]) - len(
        code[declaration_line:start].lstrip()
    )
    boundaries = (
        match
        for match in command.finditer(code, start)
        if len(match[0]) - len(match[0].lstrip()) <= declaration_indent
    )
    before_declaration = code[:declaration_line].rstrip()
    if re.search(
        r"\b(?:private|protected|noncomputable|unsafe|partial)\s*$", before_declaration
    ):
        raise ValueError("unsupported multiline Lean declaration modifier")
    boundary = next(boundaries, None)
    stop = boundary.start() if boundary else len(code)
    stack: list[str] = []
    pairs = {")": "(", "}": "{", "]": "["}
    goal: int | None = None
    pending_let = False
    saw_let_initializer = False
    saw_result_function = False
    unsupported = {
        "by",
        "do",
        "have",
        "haveI",
        "haveI'",
        "letI'",
        "suffices",
        "show",
        "match",
        "calc",
    }
    index = start
    while index < stop:
        char = code[index]
        if not stack and char == "|" and goal is not None:
            line_start = code.rfind("\n", 0, index) + 1
            line_stop = code.find("\n", index)
            line_stop = stop if line_stop < 0 else line_stop
            clause = code[index + 1 : line_stop]
            if not code[line_start:index].strip() and "=>" in clause:
                pattern = clause.split("=>", 1)[0]
                if (
                    "|" not in pattern
                    and not saw_let_initializer
                    and not pending_let
                    and not saw_result_function
                ):
                    return goal, index
        if not stack and code[index : index + 2] == ":=":
            if goal is None:
                raise ValueError("Lean theorem header has no goal colon")
            if pending_let:
                pending_let = False
                saw_let_initializer = True
                index += 2
                continue
            return goal, index
        if char in "({[":
            stack.append(char)
        elif char in ")}]":
            if not stack or stack.pop() != pairs[char]:
                raise ValueError("unbalanced Lean theorem header")
        elif char == ":" and not stack and goal is None:
            goal = index
        elif not stack and (char.isalpha() or char == "_"):
            match = re.match(r"[\w'.]+", code[index:])
            assert match is not None
            token = match[0]
            if goal is not None:
                if token == "where":
                    return goal, index
                if token == "fun":
                    saw_result_function = True
                if token in {"let", "letI"}:
                    tail = code[index + len(token) : stop].lstrip()
                    if (
                        pending_let
                        or tail.startswith(("(", "⟨"))
                        or re.match(r"(?:rec|mut)\b", tail)
                    ):
                        raise ValueError("unsupported top-level Lean let binding")
                    pending_let = True
                elif token in unsupported:
                    raise ValueError(
                        "unsupported unparenthesized Lean result expression"
                    )
            index += len(token)
            continue
        index += 1
    raise ValueError("Lean theorem header has no supported proof delimiter")
