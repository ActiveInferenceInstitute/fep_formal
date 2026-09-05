"""Fail-closed acceptance for the LaTeX compiler log of a manuscript render.

The shared rendering template compiles with ``-interaction=nonstopmode`` and
declares the render successful whenever the compiler writes ``Output written
on ...``.  Two classes of defect survive that test:

``! <message>``
    A genuine TeX error.  ``nonstopmode`` logs it and keeps going, so the
    compiler still emits a PDF.

``Missing character: There is no <c> (U+XXXX) in font <face>``
    The selected font has no glyph for a codepoint that appears in typeset
    source.  XeTeX drops the character and records a note.

The second class is the dangerous one for a formalization paper, because the
dropped character is deleted from the *statement*, not merely from its
rendering.  A run of this manuscript typeset the complement lemma

    theorem ... : mu s^c = 1 - mu s

with the Unicode superscript ``c`` (U+1D9C) absent from the mono font, so the
published page read ``mu s = 1 - mu s`` -- a false claim, shipped by a render
the pipeline called successful.

This module reduces a compiler log to those two diagnostic classes so a render
can be rejected on them.  It reads a log; it never invokes a compiler.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

__all__ = [
    "RenderLogDefects",
    "scan_render_log",
    "render_log_defects",
]

_TEX_ERROR_PREFIX = "! "
_MISSING_GLYPH_MARKER = "Missing character:"
# ``Missing character: There is no ᶜ (U+1D9C) in font FreeMono/OT:script=latn``
_MISSING_GLYPH_RE = re.compile(
    r"Missing character: There is no (?P<char>.+?) \((?P<codepoint>U\+[0-9A-Fa-f]+)\)"
    r" in font (?P<font>[^\s]+)"
)
# The compiler logs are the canonical evidence for a combined render.
DEFAULT_LOG_NAMES = ("_combined_manuscript.log", "_latex_stdout.log")


@dataclass(frozen=True)
class RenderLogDefects:
    """TeX errors and dropped glyphs recorded in one compiler log."""

    log_path: Path
    tex_errors: tuple[str, ...] = ()
    missing_characters: tuple[str, ...] = ()
    missing_by_codepoint: tuple[tuple[str, int], ...] = field(default=())

    @property
    def clean(self) -> bool:
        """True when the log records neither a TeX error nor a dropped glyph."""

        return not self.tex_errors and not self.missing_characters

    def summary(self) -> str:
        """One-line verdict naming the counts, suitable for a gate transcript."""

        if self.clean:
            return f"OK: {self.log_path} records 0 TeX errors and 0 missing characters"
        parts = [
            f"{len(self.tex_errors)} TeX error(s)",
            f"{len(self.missing_characters)} missing character(s)"
            f" across {len(self.missing_by_codepoint)} distinct codepoint(s)",
        ]
        return f"FAIL: {self.log_path} records " + " and ".join(parts)

    def report(self, max_lines: int = 10) -> list[str]:
        """Human-readable detail lines, capped so a 162-hit log stays readable."""

        lines: list[str] = [self.summary()]
        for error in self.tex_errors[:max_lines]:
            lines.append(f"  error: {error}")
        if len(self.tex_errors) > max_lines:
            lines.append(f"  ... {len(self.tex_errors) - max_lines} further TeX error(s)")
        for codepoint, count in self.missing_by_codepoint[:max_lines]:
            lines.append(f"  dropped: {count:>4}x {codepoint}")
        if len(self.missing_by_codepoint) > max_lines:
            remaining = len(self.missing_by_codepoint) - max_lines
            lines.append(f"  ... {remaining} further dropped codepoint(s)")
        return lines


def scan_render_log(log_path: Path) -> RenderLogDefects:
    """Scan one LaTeX log for TeX errors and dropped characters.

    A missing log is itself a defect -- a render that produced no compiler log
    cannot be accepted -- and is reported as a single TeX error line rather
    than silently passing.
    """

    log_path = Path(log_path)
    if not log_path.exists():
        return RenderLogDefects(
            log_path=log_path,
            tex_errors=(f"! compiler log not found: {log_path}",),
        )
    content = log_path.read_text(encoding="utf-8", errors="replace")
    errors: list[str] = []
    missing: list[str] = []
    codepoints: Counter[str] = Counter()
    for line in content.splitlines():
        if line.startswith(_TEX_ERROR_PREFIX):
            errors.append(line.strip())
            continue
        if _MISSING_GLYPH_MARKER not in line:
            continue
        missing.append(line.strip())
        match = _MISSING_GLYPH_RE.search(line)
        if match:
            codepoints[f"{match['char']} ({match['codepoint']}) in font {match['font']}"] += 1
        else:
            codepoints[line.strip()] += 1
    return RenderLogDefects(
        log_path=log_path,
        tex_errors=tuple(errors),
        missing_characters=tuple(missing),
        missing_by_codepoint=tuple(sorted(codepoints.items(), key=lambda item: (-item[1], item[0]))),
    )


def render_log_defects(
    pdf_dir: Path,
    log_names: tuple[str, ...] = DEFAULT_LOG_NAMES,
) -> list[RenderLogDefects]:
    """Scan every known compiler log under ``pdf_dir``.

    Logs that were not written are skipped, except that an empty result set is
    impossible to accept: the caller receives a defect for the first expected
    name so a missing render cannot pass as clean.
    """

    pdf_dir = Path(pdf_dir)
    present = [pdf_dir / name for name in log_names if (pdf_dir / name).exists()]
    if not present:
        return [scan_render_log(pdf_dir / log_names[0])]
    return [scan_render_log(path) for path in present]
