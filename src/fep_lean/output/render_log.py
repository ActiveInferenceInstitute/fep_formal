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

import hashlib
import json
import re
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from fep_lean.output.rendering import (
    SOURCE_EXCLUDES,
    VERBATIM_SOURCES,
    substitute_placeholders,
)

__all__ = [
    "RECEIPT_VERSION",
    "RenderLogDefects",
    "build_acceptance_receipt",
    "contents_number_overflow_defects",
    "manuscript_source_digest",
    "manuscript_source_digests",
    "mermaid_fallback_defects",
    "receipt_defects",
    "render_log_defects",
    "rendered_manuscript_sources",
    "scan_render_log",
    "stale_render_defects",
    "uncaptioned_table_defects",
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
            (
                f"{len(self.missing_characters)} missing character(s)"
                f" across {len(self.missing_by_codepoint)} distinct codepoint(s)"
            ),
        ]
        return f"FAIL: {self.log_path} records " + " and ".join(parts)

    def report(self, max_lines: int = 10) -> list[str]:
        """Human-readable detail lines, capped so a 162-hit log stays readable."""

        lines: list[str] = [self.summary()]
        for error in self.tex_errors[:max_lines]:
            lines.append(f"  error: {error}")
        if len(self.tex_errors) > max_lines:
            lines.append(
                f"  ... {len(self.tex_errors) - max_lines} further TeX error(s)"
            )
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
            codepoints[
                f"{match['char']} ({match['codepoint']}) in font {match['font']}"
            ] += 1
        else:
            codepoints[line.strip()] += 1
    return RenderLogDefects(
        log_path=log_path,
        tex_errors=tuple(errors),
        missing_characters=tuple(missing),
        missing_by_codepoint=tuple(
            sorted(codepoints.items(), key=lambda item: (-item[1], item[0]))
        ),
    )


def render_log_defects(
    pdf_dir: Path,
    log_names: tuple[str, ...] = DEFAULT_LOG_NAMES,
) -> list[RenderLogDefects]:
    """Scan every known compiler log under ``pdf_dir``.

    A log that was not written is itself a defect once any expected log
    exists: the acceptance cannot judge a render half of whose compiler
    evidence is missing, so the absent name is scanned too and reported as
    not found (:func:`scan_render_log`). A directory where no expected log
    exists still yields a defect for the first expected name, so a render
    that never ran cannot pass as clean.
    """

    pdf_dir = Path(pdf_dir)
    present = [pdf_dir / name for name in log_names if (pdf_dir / name).exists()]
    if not present:
        return [scan_render_log(pdf_dir / log_names[0])]
    return [scan_render_log(pdf_dir / name) for name in log_names]


# A ``mermaid`` fence the renderer could not rasterize is replaced by a
# ``verbatim`` block holding the diagram's own source, captioned with the
# fence's alt text or the literal fallback ``Mermaid diagram``. The template
# logs that at WARNING and keeps going, so the manuscript's only diagram
# shipped as a page of ``flowchart LR`` source captioned "Figure 3: Mermaid
# diagram". The missing-``mmdc`` branch of the same function raises, so the
# two failure modes disagree; this is the project-side half that makes both
# fail closed.
_MERMAID_FALLBACK_RE = re.compile(
    r"\\begin\{figure\}\[htbp\]\s*\n\\centering\s*\n\\begin\{verbatim\}\n"
    r"(?P<body>.*?)\n\\end\{verbatim\}\s*\n\\caption\{(?P<caption>[^}]*)\}",
    re.DOTALL,
)
# ``flowchart``/``graph``/``sequenceDiagram``/... opening a verbatim figure is
# mermaid source, whatever the caption says.
_MERMAID_SOURCE_RE = re.compile(
    r"^\s*(?:%%\{.*?\}%%\s*)?"
    r"(flowchart|graph|sequenceDiagram|classDiagram|stateDiagram(?:-v2)?|erDiagram"
    r"|journey|gantt|pie|gitGraph|mindmap|timeline|quadrantChart|C4Context)\b",
    re.IGNORECASE,
)
DEFAULT_TEX_NAME = "_combined_manuscript.tex"


def mermaid_fallback_defects(
    pdf_dir: Path, tex_name: str = DEFAULT_TEX_NAME
) -> tuple[str, ...]:
    """Return one line per mermaid diagram that shipped as raw source.

    The rendered LaTeX is the evidence: a rasterized diagram is an
    ``\\includegraphics`` of a PNG under ``figures/mermaid_inline/``, while a
    failed one is a ``verbatim`` block containing the fence's own source.
    """

    tex_path = Path(pdf_dir) / tex_name
    if not tex_path.is_file():
        return ()
    content = tex_path.read_text(encoding="utf-8", errors="replace")
    failures: list[str] = []
    for match in _MERMAID_FALLBACK_RE.finditer(content):
        body = match.group("body")
        caption = match.group("caption").strip()
        if not _MERMAID_SOURCE_RE.match(body):
            continue
        line_number = content.count("\n", 0, match.start()) + 1
        first_line = body.strip().splitlines()[0].strip()
        failures.append(
            f"{tex_path}:{line_number}: mermaid diagram shipped as verbatim source "
            f"(caption {caption!r}, first line {first_line!r}) -- the renderer fell "
            f"back instead of rasterizing it"
        )
    return tuple(failures)


DEFAULT_COMBINED_MARKDOWN = "_combined_manuscript.md"
# Files that live beside the chapters but never reach the combined document:
# contributor documentation, and ``preamble.md``, which the template copies
# into the LaTeX header instead. The renderer owns that list, so it is read
# from the renderer rather than restated here -- restating it made the guard
# report 107 lines of LaTeX preamble as prose drift. Generated appendices are
# excluded from *substitution* but are typeset verbatim, so they stay in.
_NON_RENDERED_MANUSCRIPT_FILES = frozenset(SOURCE_EXCLUDES) - frozenset(
    VERBATIM_SOURCES
)


def _significant_lines(text: str) -> list[str]:
    """Return the lines of a manuscript source that must survive a render.

    Short lines (headings, table rules, list bullets) repeat across chapters and
    would match anywhere, so they carry no evidence. Image lines are excluded
    because the renderer legitimately rewrites their paths -- an audit that
    counted those reported drift on two lines that had not drifted.
    """

    lines: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if len(line) <= 60 or line.startswith("!["):
            continue
        lines.append(line)
    return lines


# The source stamp names the commit the render was computed from and the date
# it ran. Both are unique to a render by construction, so a committed variable
# projection can never agree with them and a line carrying one cannot be
# compared -- checking it would report every render as stale one commit later.
_PER_RENDER_TOKEN = "{{source."


def _comparable(raw_line: str, variables: Mapping[str, Any] | None) -> bool:
    """True when a source line can be matched against the rendered document."""

    if _PER_RENDER_TOKEN in raw_line:
        return False
    return variables is not None or "{{" not in raw_line


# Markdown emphasis is markup the renderer may consume rather than carry: the
# italic line under a diagram fence becomes that figure's ``\caption{...}`` and
# its ``alt`` text, so its words survive while the line does not. Comparing the
# emphasized text as a substring of the rendered document keeps that case out
# of the report without weakening it -- drift changes the words, and changed
# words are not a substring either.
_EMPHASIS = "*_ "


def _is_rendered(line: str, rendered_lines: set[str], rendered_text: str) -> bool:
    """True when a source line survives into the render, as a line or in one."""

    if line in rendered_lines:
        return True
    core = line.strip(_EMPHASIS)
    return bool(core) and core in rendered_text


def stale_render_defects(
    manuscript_dir: Path,
    pdf_dir: Path,
    combined_name: str = DEFAULT_COMBINED_MARKDOWN,
    variables: Mapping[str, Any] | None = None,
    max_lines: int = 3,
) -> tuple[str, ...]:
    """Return every authored source whose text is not in the combined render.

    Two failures produced the same artifact, and both are checked here by the
    same test. The audited PDF predated two of its own chapters and one prose
    line had genuinely drifted -- 02b said "The table below reports ..." while
    the render still said "Table 1 reports ...". Then a later render, run after
    those chapters were fixed, reproduced the drift exactly: the shared
    template renders from ``output/manuscript`` when that directory exists, so
    a render whose *inputs* were never regenerated is newer than every authored
    source and still describes an older tree.

    Modification time cannot see the second case and got the first one wrong
    too: regenerating two files to byte-identical content moved their mtimes
    and failed the render they describe exactly. So no source is skipped and no
    mtime is read. A source is stale when a line of it, substituted the way the
    renderer substitutes it, is not a line of the combined document.

    ``variables`` is the render's own variable mapping. Without it, lines
    carrying ``{{placeholder}}`` tokens cannot be compared and are skipped, so
    pass it wherever it is available.
    """

    combined = Path(pdf_dir) / combined_name
    if not combined.is_file():
        return (f"{combined}: combined render is absent; nothing to compare against",)
    rendered_text = combined.read_text(encoding="utf-8", errors="replace")
    rendered_lines = {line.strip() for line in rendered_text.splitlines()}
    manuscript = Path(manuscript_dir)
    stale: list[str] = []
    for source in sorted(manuscript.glob("*.md")):
        if source.name in _NON_RENDERED_MANUSCRIPT_FILES:
            continue
        text = source.read_text(encoding="utf-8", errors="replace")
        authored = {
            authored_line.strip(): raw_line.strip()
            for authored_line, raw_line in zip(
                _significant_lines(
                    substitute_placeholders(text, variables, strict=False)
                    if variables is not None
                    else text
                ),
                _significant_lines(text),
                strict=False,
            )
        }
        missing = [
            line
            for line, raw in authored.items()
            if _comparable(raw, variables)
            and not _is_rendered(line, rendered_lines, rendered_text)
        ]
        if not missing:
            continue
        detail = "; ".join(f"{line[:80]!r}" for line in missing[:max_lines])
        if len(missing) > max_lines:
            detail += f"; ... {len(missing) - max_lines} further line(s)"
        stale.append(
            f"{source}: {len(missing)} line(s) absent from {combined.name}; "
            f"the render describes an older tree: {detail}"
        )
    return tuple(stale)


# Pandoc emits one ``longtable`` per authored pipe table and, when the table has
# a caption, a ``\caption`` before the running head that ``\endfirsthead``
# closes. The audited PDF held 36 longtables and 6 ``\caption`` calls, all six
# on figures, so no table in the document carried a number a reader could cite.
_LONGTABLE_RE = re.compile(r"\\begin\{longtable\}")
_LONGTABLE_HEAD_END = r"\endfirsthead"


def uncaptioned_table_defects(
    pdf_dir: Path, tex_name: str = DEFAULT_TEX_NAME
) -> tuple[str, ...]:
    """Return one line per rendered table that carries no caption."""

    tex_path = Path(pdf_dir) / tex_name
    if not tex_path.is_file():
        return ()
    content = tex_path.read_text(encoding="utf-8", errors="replace")
    failures: list[str] = []
    for match in _LONGTABLE_RE.finditer(content):
        head_end = content.find(_LONGTABLE_HEAD_END, match.end())
        head = content[match.end() : head_end if head_end != -1 else match.end() + 800]
        if r"\caption{" in head:
            continue
        line_number = content.count("\n", 0, match.start()) + 1
        failures.append(
            f"{tex_path}:{line_number}: longtable has no \\caption, so it is "
            f"unnumbered and no prose can refer to it"
        )
    return tuple(failures)


# A contents line whose section number is wider than its number box overflows
# into the entry title: ``15.100fep-100 --- ...``. TeX reports that as an
# overfull \hbox whose next log line holds the number alone, which is what
# separates this class from ordinary overfull prose.
_OVERFULL_RE = re.compile(r"^Overfull \\hbox \(([0-9.]+)pt too wide\)")
_BARE_NUMBER_RE = re.compile(r"^\\[^ ]+ (?P<number>\d+(?:\.\d+)*)\s*$")


def _contents_overflow_lines(log_path: Path) -> tuple[str, ...]:
    """Return the overflow lines recorded in one compiler log."""

    lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    failures: list[str] = []
    for index, line in enumerate(lines):
        overfull = _OVERFULL_RE.match(line)
        if overfull is None or index + 1 >= len(lines):
            continue
        number = _BARE_NUMBER_RE.match(lines[index + 1])
        if number is None:
            continue
        failures.append(
            f"{log_path}:{index + 1}: contents number {number['number']} overflows "
            f"its number box by {overfull.group(1)}pt and collides with the entry "
            f"title; widen the matching \\@dottedtocline number width"
        )
    return tuple(failures)


def contents_number_overflow_defects(
    pdf_dir: Path, log_name: str = "_combined_manuscript.log"
) -> tuple[str, ...]:
    """Return one line per contents entry whose number overflowed its box.

    The named log is scanned when present. When it is absent while a sibling
    expected log (:data:`DEFAULT_LOG_NAMES`) exists, the sibling is scanned
    and the absence is reported: half the compiler evidence cannot stand in
    for the combined log, and silence would accept the render. A directory
    where no expected log exists still has nothing to judge.
    """

    pdf_dir = Path(pdf_dir)
    log_path = pdf_dir / log_name
    if log_path.is_file():
        return _contents_overflow_lines(log_path)
    siblings = [
        pdf_dir / name
        for name in DEFAULT_LOG_NAMES
        if name != log_name and (pdf_dir / name).is_file()
    ]
    if not siblings:
        return ()
    absent = tuple(
        f"{log_path}: expected log is absent while {sibling.name} exists; the "
        f"contents-number acceptance cannot judge the combined document "
        f"without it -- re-run scripts/render_publication.py"
        for sibling in siblings
    )
    scanned = tuple(
        line for sibling in siblings for line in _contents_overflow_lines(sibling)
    )
    return absent + scanned


# The acceptance above needs a real render to judge, and continuous
# integration does not produce one: a render needs a checkout of the shared
# template -- a separate repository this project does not pin -- plus XeLaTeX,
# pandoc, ``rsvg-convert``, the mermaid CLI and the two faces
# ``manuscript/preamble.md`` selects. So CI cannot re-run the acceptance. What
# it can do is refuse to merge sources the acceptance has never seen.
#
# That is what this receipt is for. It is written only by an acceptance that
# found nothing, it is committed, and it names the exact manuscript sources it
# covered. A chapter edited without a fresh render leaves the receipt naming a
# digest the checkout no longer has, and the verification below fails.
#
# Its boundary is stated rather than implied: it binds the acceptance to the
# authored manuscript text, the LaTeX preamble, and the byte-exact generated
# appendix (``09z_unified_formalism_catalogue.md``). A change under ``src/``
# that moves a computed count regenerates that appendix via
# ``uv run fep-lean catalogue`` and moves its digest, so the receipt goes
# stale and a fresh render is required. Only the values a chapter's
# ``{{token}}`` resolves to inside the authored text stay outside the digest:
# :func:`stale_render_defects` compares those against the render variables on
# the render path, and ``manuscript_projection_drift`` owns the generated
# projections against the catalogue.
RECEIPT_VERSION = 1
# Every check whose defect list must be empty for a render to be publishable.
_RECEIPT_CHECKS = (
    "tex_errors",
    "missing_characters",
    "mermaid_fallbacks",
    "stale_sources",
    "uncaptioned_tables",
    "contents_number_overflows",
)
_PAGES_RE = re.compile(r"Output written on \S+ \((?P<pages>\d+) pages?")


def rendered_manuscript_sources(manuscript_dir: Path) -> tuple[Path, ...]:
    """Return the manuscript files the template typesets, in render order."""

    return tuple(
        path
        for path in sorted(Path(manuscript_dir).glob("*.md"))
        if path.name not in _NON_RENDERED_MANUSCRIPT_FILES
    )


def manuscript_source_digests(manuscript_dir: Path) -> dict[str, str]:
    """Return one digest per file the acceptance covers, keyed by name.

    ``preamble.md`` is not typeset as prose -- the template copies it into the
    LaTeX header -- but it selects the fonts, and choosing a face without the
    document's glyphs is the defect that shipped a false theorem. A record that
    ignored it would accept that change silently.

    The digests are per file rather than one blob so that a mismatch can name
    what moved. A reader who is told only that two hashes differ has to bisect
    thirty files; a reader told ``09z_unified_formalism_catalogue.md`` knows
    immediately that the generated appendix, not a chapter, is what changed.
    """

    manuscript = Path(manuscript_dir)
    return {
        path.name: hashlib.sha256(
            path.read_bytes() if path.is_file() else b""
        ).hexdigest()
        for path in (
            *rendered_manuscript_sources(manuscript),
            manuscript / "preamble.md",
        )
    }


def _missing_generated_sources(manuscript_dir: Path) -> tuple[str, ...]:
    """Return the generated sources that have not been materialized.

    The generated appendices are build products of ``uv run fep-lean
    catalogue``. A checkout that has not run it is missing required
    manuscript inputs, and a digest that silently covered fewer files would
    accept a render of an incomplete paper.
    """

    manuscript = Path(manuscript_dir)
    return tuple(
        name for name in VERBATIM_SOURCES if not (manuscript / name).is_file()
    )


def manuscript_source_digest(manuscript_dir: Path) -> str:
    """Return one digest over every typeset source and the LaTeX preamble."""

    digest = hashlib.sha256()
    for name, file_digest in sorted(manuscript_source_digests(manuscript_dir).items()):
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_digest.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def rendered_page_count(
    pdf_dir: Path, log_name: str = "_combined_manuscript.log"
) -> int:
    """Return the page count the compiler recorded, or ``0`` when it did not."""

    log_path = Path(pdf_dir) / log_name
    if not log_path.is_file():
        return 0
    match = _PAGES_RE.search(log_path.read_text(encoding="utf-8", errors="replace"))
    return int(match["pages"]) if match else 0


def build_acceptance_receipt(
    manuscript_dir: Path,
    pdf_dir: Path,
    *,
    counts: Mapping[str, int],
) -> dict[str, Any]:
    """Return the receipt recording that this render passed this acceptance.

    ``counts`` is the number of defects each check reported, keyed by
    :data:`_RECEIPT_CHECKS`; the caller has already run them, so recomputing
    here would let the receipt disagree with the report it accompanies.
    """

    missing = [name for name in _RECEIPT_CHECKS if name not in counts]
    if missing:
        raise ValueError(f"acceptance receipt is missing checks: {sorted(missing)}")
    checks = {name: int(counts[name]) for name in _RECEIPT_CHECKS}
    return {
        "receipt_version": RECEIPT_VERSION,
        "accepted": not any(checks.values()),
        "manuscript_source_digest": manuscript_source_digest(manuscript_dir),
        "source_digests": manuscript_source_digests(manuscript_dir),
        "pages": rendered_page_count(pdf_dir),
        "checks": checks,
    }


def receipt_defects(receipt_path: Path, manuscript_dir: Path) -> tuple[str, ...]:
    """Return why the committed acceptance receipt does not cover this checkout.

    An absent, unreadable, rejecting or stale receipt is a defect. Not knowing
    whether the shipped render was accepted is the state this whole module
    exists to reject, so it is never treated as an absence of evidence.
    """

    path = Path(receipt_path)
    if not path.is_file():
        absent = (
            f"{path}: no acceptance receipt, so no render of these sources is "
            f"known to have passed the acceptance; run "
            f"scripts/render_publication.py"
        )
        return (absent,)
    try:
        receipt = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        return (f"{path}: unreadable acceptance receipt ({error})",)
    if not isinstance(receipt, dict):
        return (f"{path}: acceptance receipt is not a JSON object",)
    failures: list[str] = []
    version = receipt.get("receipt_version")
    if version != RECEIPT_VERSION:
        failures.append(
            f"{path}: receipt_version is {version!r}, expected {RECEIPT_VERSION}"
        )
    checks = receipt.get("checks")
    if not isinstance(checks, dict):
        failures.append(f"{path}: receipt records no checks")
    else:
        for name in _RECEIPT_CHECKS:
            if name not in checks:
                failures.append(f"{path}: receipt does not record {name}")
            elif checks[name]:
                failures.append(
                    f"{path}: the accepted render reported {checks[name]} {name}"
                )
    if receipt.get("accepted") is not True:
        failures.append(
            f"{path}: records accepted={receipt.get('accepted')!r}; the render "
            f"it describes was rejected"
        )
    expected = manuscript_source_digest(manuscript_dir)
    recorded = receipt.get("manuscript_source_digest")
    if recorded != expected:
        moved = _moved_source_names(receipt.get("source_digests"), manuscript_dir)
        generated = [name for name in moved if name in VERBATIM_SOURCES]
        authored = [name for name in moved if name not in VERBATIM_SOURCES]
        if authored or not moved:
            remediation = "re-run scripts/render_publication.py"
        else:
            remediation = (
                "regenerate the build product with `uv run fep-lean catalogue`"
            )
        failures.append(
            f"{path}: covers manuscript sources {recorded!r} but this checkout "
            f"is {expected!r}; the shipped render predates these sources -- "
            f"{remediation}"
            + _moved_sources(receipt.get("source_digests"), manuscript_dir)
        )
        if generated and authored:
            failures.append(
                f"{path}: generated appendix {', '.join(generated)} changed "
                f"since that render; regenerate it with `uv run fep-lean catalogue`"
            )
    for name in _missing_generated_sources(manuscript_dir):
        failures.append(
            f"{path}: generated appendix {name} is missing under "
            f"{manuscript_dir}; the acceptance digest covers the generated "
            f"appendix, so run `uv run fep-lean catalogue` first"
        )
    return tuple(failures)


def _moved_source_names(recorded: Any, manuscript_dir: Path) -> list[str]:
    """Return the names whose digests differ between receipt and checkout."""

    if not isinstance(recorded, dict):
        return []
    live = manuscript_source_digests(manuscript_dir)
    return sorted(
        {
            name
            for name in set(recorded) | set(live)
            if recorded.get(name) != live.get(name)
        }
    )


def _moved_sources(recorded: Any, manuscript_dir: Path, limit: int = 5) -> str:
    """Return the names that differ, so a stale receipt says what changed.

    Generated appendices (:data:`VERBATIM_SOURCES`) are build products, so
    they are labeled as such: their remediation is regeneration, not a
    re-render.
    """

    moved = _moved_source_names(recorded, manuscript_dir)
    if not moved:
        return ""
    shown = ", ".join(
        f"{name} (generated appendix)" if name in VERBATIM_SOURCES else name
        for name in moved[:limit]
    )
    if len(moved) > limit:
        shown += f", and {len(moved) - limit} more"
    return f"; changed since that render: {shown}"
