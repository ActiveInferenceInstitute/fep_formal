"""Fail-closed font coverage for the glyphs this manuscript typesets.

A render is only as trustworthy as the fonts on the host that ran it. The
audited PDF dropped 162 characters -- every Unicode subscript and superscript
in the Lean sources -- because ``manuscript/preamble.md`` selected FreeMono,
which has no glyph for any of them, and XeTeX logs a dropped character as a
note rather than an error. One printed theorem became false.

The face is now JuliaMono, but the fix lives in a font installed on one
machine: nothing in the checkout records which glyphs the document needs, and
a render on a host without that face would regress silently and identically.

This module makes both halves mechanical. The requirement is derived from the
sources -- every non-ASCII codepoint the manuscript typesets, split by the face
that will carry it -- and the check probes the host's installed fonts through
fontconfig. Neither half is hand-maintained, so neither can drift away from
the document.
"""

from __future__ import annotations

import re
import shutil
import subprocess  # nosec B404 - fixed argv, shell=False, fontconfig query only
from collections.abc import Iterable
from pathlib import Path
from typing import Any

__all__ = [
    "FontProbeError",
    "code_font_codepoints",
    "declared_fonts",
    "font_coverage_defects",
    "prose_font_codepoints",
    "render_font_projection",
    "uncovered_codepoints",
]

# ``\setmonofont{JuliaMono}[Scale=MatchLowercase]`` -- the option list is
# irrelevant to coverage, so only the family is captured.
_FONT_RE = re.compile(
    r"^\\(?P<command>setmainfont|setmonofont)\{(?P<family>[^}]+)\}", re.MULTILINE
)
_FENCE_RE = re.compile(r"^```.*?^```", re.DOTALL | re.MULTILINE)
_INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
_NON_RENDERED = frozenset({"AGENTS.md", "README.md", "preamble.md"})
# Role -> the LaTeX command that selects the face carrying it.
CODE_ROLE = "mono"
PROSE_ROLE = "main"
_ROLE_COMMANDS = {CODE_ROLE: "setmonofont", PROSE_ROLE: "setmainfont"}


class FontProbeError(RuntimeError):
    """Raised when host font coverage cannot be established at all.

    Not knowing is not the same as being covered: a render host without
    fontconfig cannot demonstrate that it will typeset the document, and the
    failure mode being guarded against is silent.
    """


def _manuscript_files(manuscript_dir: Path) -> tuple[Path, ...]:
    return tuple(
        path
        for path in sorted(Path(manuscript_dir).glob("*.md"))
        if path.name not in _NON_RENDERED
    )


def code_font_codepoints(manuscript_dir: Path) -> tuple[int, ...]:
    """Return every non-ASCII codepoint typeset in a code face.

    Fenced blocks are the Lean bodies; inline spans are the identifiers and
    module paths quoted throughout the prose. Both are set in the mono face.
    """

    found: set[int] = set()
    for path in _manuscript_files(manuscript_dir):
        text = path.read_text(encoding="utf-8")
        for fence in _FENCE_RE.finditer(text):
            found.update(ord(char) for char in fence.group(0) if ord(char) > 127)
        outside = _FENCE_RE.sub("", text)
        for span in _INLINE_CODE_RE.finditer(outside):
            found.update(ord(char) for char in span.group(0) if ord(char) > 127)
    return tuple(sorted(found))


def prose_font_codepoints(manuscript_dir: Path) -> tuple[int, ...]:
    """Return every non-ASCII codepoint typeset outside a code face."""

    found: set[int] = set()
    for path in _manuscript_files(manuscript_dir):
        text = _FENCE_RE.sub("", path.read_text(encoding="utf-8"))
        text = _INLINE_CODE_RE.sub("", text)
        found.update(ord(char) for char in text if ord(char) > 127)
    return tuple(sorted(found))


def declared_fonts(preamble_path: Path) -> dict[str, str]:
    """Return the font family the preamble selects for each role."""

    text = Path(preamble_path).read_text(encoding="utf-8")
    selected = {
        match.group("command"): match.group("family").strip()
        for match in _FONT_RE.finditer(text)
    }
    return {
        role: selected[command]
        for role, command in _ROLE_COMMANDS.items()
        if command in selected
    }


def uncovered_codepoints(family: str, codepoints: Iterable[int]) -> tuple[int, ...]:
    """Return the codepoints the installed ``family`` has no glyph for.

    ``fc-list ":charset=2098:family=JuliaMono"`` prints a line per matching
    face and nothing when the family is absent or lacks the glyph, which is
    the same query the preamble tells a maintainer to run by hand.
    """

    executable = shutil.which("fc-list")
    if executable is None:
        raise FontProbeError(
            "fc-list is not on PATH, so font coverage cannot be verified; "
            "install fontconfig on the render host"
        )
    missing: list[int] = []
    for codepoint in codepoints:
        query = f":charset={codepoint:04X}:family={family}"
        completed = subprocess.run(  # nosec B603 - fixed argv, shell=False
            [executable, query, "family"],
            capture_output=True,
            check=False,
            text=True,
            timeout=30,
        )
        if not completed.stdout.strip():
            missing.append(codepoint)
    return tuple(missing)


def _describe(codepoint: int) -> str:
    return f"U+{codepoint:04X} ({chr(codepoint)!r})"


def font_coverage_defects(project_root: Path) -> tuple[str, ...]:
    """Return one line per glyph the host's selected fonts would drop.

    This is the check that would have stopped the audited render: FreeMono
    covers none of U+2098 U+2096 U+1D50 U+209A U+1D62 U+1D9C, all six of which
    the catalogue typesets in Lean code.
    """

    root = Path(project_root)
    manuscript = root / "manuscript"
    fonts = declared_fonts(manuscript / "preamble.md")
    requirements = {
        CODE_ROLE: code_font_codepoints(manuscript),
        PROSE_ROLE: prose_font_codepoints(manuscript),
    }
    defects: list[str] = []
    for role, codepoints in requirements.items():
        family = fonts.get(role)
        if family is None:
            defects.append(
                f"{role}: manuscript/preamble.md selects no "
                f"\\{_ROLE_COMMANDS[role]}, so the face is TeX's default"
            )
            continue
        missing = uncovered_codepoints(family, codepoints)
        if not missing:
            continue
        shown = ", ".join(_describe(codepoint) for codepoint in missing[:8])
        if len(missing) > 8:
            shown += f", ... {len(missing) - 8} more"
        defects.append(
            f"{role}: installed {family} has no glyph for {len(missing)} of "
            f"{len(codepoints)} codepoint(s) this manuscript typesets: {shown}"
        )
    return tuple(defects)


def render_font_projection(project_root: Path) -> dict[str, Any]:
    """Return the committed record of what a render host must supply.

    Only derived values: the faces the preamble selects and the codepoints the
    sources need. A ``--check`` of this projection fails when the manuscript
    starts using a glyph nobody has confirmed a font for.
    """

    manuscript = Path(project_root) / "manuscript"
    fonts = declared_fonts(manuscript / "preamble.md")
    roles = {}
    for role, codepoints in (
        (CODE_ROLE, code_font_codepoints(manuscript)),
        (PROSE_ROLE, prose_font_codepoints(manuscript)),
    ):
        roles[role] = {
            "family": fonts.get(role, ""),
            "codepoint_count": len(codepoints),
            "codepoints": [f"U+{codepoint:04X}" for codepoint in codepoints],
        }
    return {
        "note": (
            "Generated by scripts/build_render_fonts.py. Every codepoint listed "
            "here is typeset by manuscript/*.md; a render host whose selected "
            "font lacks one drops it silently (see FEP-LEAN-R1)."
        ),
        "roles": roles,
    }
