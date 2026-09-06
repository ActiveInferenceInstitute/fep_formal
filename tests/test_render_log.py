"""Acceptance for the fail-closed LaTeX-log gate.

Regression cover for FEP-LEAN-R2: a render that wrote ``Output written on``
while dropping 162 characters and logging two TeX errors was reported as
successful.
"""

from __future__ import annotations

import os
from pathlib import Path

from fep_lean.output.render_log import (
    RenderLogDefects,
    contents_number_overflow_defects,
    mermaid_fallback_defects,
    render_log_defects,
    scan_render_log,
    stale_render_defects,
    uncaptioned_table_defects,
)

CLEAN_LOG = """This is XeTeX, Version 3.141592653
(./_combined_manuscript.tex
Output written on _combined_manuscript.pdf (346 pages).
"""

DEFECTIVE_LOG = """This is XeTeX, Version 3.141592653
Missing character: There is no ₘ (U+2098) in font FreeMono/OT:script=latn;
Missing character: There is no ₘ (U+2098) in font FreeMono/OT:script=latn;
Missing character: There is no ᶜ (U+1D9C) in font FreeMono/OT:script=latn;
! Argument of \\TU\\' has an extra }.
! Paragraph ended before \\TU\\' was complete.
Output written on _combined_manuscript.pdf (346 pages).
"""


def _write(tmp_path: Path, name: str, content: str) -> Path:
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path


def test_clean_log_is_accepted(tmp_path: Path) -> None:
    defects = scan_render_log(_write(tmp_path, "_combined_manuscript.log", CLEAN_LOG))
    assert defects.clean
    assert defects.tex_errors == ()
    assert defects.missing_characters == ()
    assert defects.summary().startswith("OK:")


def test_output_written_does_not_excuse_errors_or_dropped_glyphs(
    tmp_path: Path,
) -> None:
    """The exact fail-open shape: a PDF was written, yet the log is defective."""

    log = _write(tmp_path, "_combined_manuscript.log", DEFECTIVE_LOG)
    assert "Output written on" in log.read_text(encoding="utf-8")
    defects = scan_render_log(log)
    assert not defects.clean
    assert len(defects.tex_errors) == 2
    assert len(defects.missing_characters) == 3


def test_missing_glyphs_are_grouped_by_codepoint(tmp_path: Path) -> None:
    defects = scan_render_log(
        _write(tmp_path, "_combined_manuscript.log", DEFECTIVE_LOG)
    )
    grouped = dict(defects.missing_by_codepoint)
    assert sum(grouped.values()) == 3
    assert any("U+2098" in key and count == 2 for key, count in grouped.items())
    assert any("U+1D9C" in key and count == 1 for key, count in grouped.items())


def test_report_caps_detail_lines(tmp_path: Path) -> None:
    body = "".join(
        f"Missing character: There is no x (U+{index:04X}) in font FreeMono/OT:script=latn;\n"
        for index in range(0x2090, 0x2090 + 20)
    )
    defects = scan_render_log(_write(tmp_path, "_combined_manuscript.log", body))
    report = defects.report(max_lines=3)
    assert report[0].startswith("FAIL:")
    assert any("further dropped codepoint(s)" in line for line in report)


def test_absent_log_is_a_defect_not_a_pass(tmp_path: Path) -> None:
    defects = scan_render_log(tmp_path / "never_written.log")
    assert not defects.clean
    assert defects.tex_errors and "compiler log not found" in defects.tex_errors[0]


def test_render_log_defects_never_returns_empty(tmp_path: Path) -> None:
    """An unrendered output directory must not read as a clean render."""

    results = render_log_defects(tmp_path)
    assert results
    assert all(isinstance(item, RenderLogDefects) for item in results)
    assert not results[0].clean


def test_render_log_defects_scans_every_present_log(tmp_path: Path) -> None:
    _write(tmp_path, "_combined_manuscript.log", CLEAN_LOG)
    _write(tmp_path, "_latex_stdout.log", DEFECTIVE_LOG)
    results = render_log_defects(tmp_path)
    assert len(results) == 2
    assert [defects.clean for defects in results] == [True, False]


CAPTIONED_TABLE = r"""\begin{longtable}[]{@{}ll@{}}
\caption{Topic count and native receipt rate for each catalogue area.}\tabularnewline
\toprule\noalign{}
A & B \\
\midrule\noalign{}
\endfirsthead
\bottomrule\noalign{}
\endlastfoot
1 & 2 \\
\end{longtable}
"""

UNCAPTIONED_TABLE = r"""\begin{longtable}[]{@{}ll@{}}
\toprule\noalign{}
A & B \\
\midrule\noalign{}
\endfirsthead
\bottomrule\noalign{}
\endlastfoot
1 & 2 \\
\end{longtable}
"""

# The exact shape TeX writes when a contents number is wider than its box.
CONTENTS_OVERFLOW_LOG = """This is XeTeX, Version 3.141592653
Overfull \\hbox (4.49997pt too wide) detected at line 578
\\TU/FreeSerif(0)/m/n/10 15.100
 []

Overfull \\hbox (12.0pt too wide) in paragraph at lines 900--901
\\TU/FreeSerif(0)/m/n/10 ordinary prose that is simply too wide
 []
Output written on _combined_manuscript.pdf (347 pages).
"""


def test_captioned_table_is_accepted(tmp_path: Path) -> None:
    _write(tmp_path, "_combined_manuscript.tex", CAPTIONED_TABLE)
    assert uncaptioned_table_defects(tmp_path) == ()


def test_uncaptioned_table_is_reported(tmp_path: Path) -> None:
    _write(tmp_path, "_combined_manuscript.tex", UNCAPTIONED_TABLE + CAPTIONED_TABLE)
    defects = uncaptioned_table_defects(tmp_path)
    assert len(defects) == 1
    assert defects[0].endswith("no prose can refer to it")
    assert ":1:" in defects[0]


def test_contents_number_overflow_is_separated_from_prose_overflow(
    tmp_path: Path,
) -> None:
    """Only the bare-number overflow is a contents defect; wide prose is not."""
    _write(tmp_path, "_combined_manuscript.log", CONTENTS_OVERFLOW_LOG)
    defects = contents_number_overflow_defects(tmp_path)
    assert len(defects) == 1
    assert "contents number 15.100" in defects[0]
    assert "4.49997pt" in defects[0]


def test_absent_render_artifacts_report_nothing(tmp_path: Path) -> None:
    """Both audits read build output, so an unbuilt tree has nothing to judge."""
    assert uncaptioned_table_defects(tmp_path) == ()
    assert contents_number_overflow_defects(tmp_path) == ()


# ── mermaid fallback ──────────────────────────────────────────────────────
# The audited PDF shipped its only diagram as a page of ``flowchart LR`` source
# captioned "Figure 3: Mermaid diagram", because the renderer logs a warning
# and falls back when it cannot find a browser. This is the shape it emits.
MERMAID_FALLBACK = r"""\begin{figure}[htbp]
\centering
\begin{verbatim}
flowchart LR
  source[canonical TopicEntry] --> session[SQLite session]
\end{verbatim}
\caption{Mermaid diagram}
\end{figure}
"""

RASTERIZED_FIGURE = r"""\begin{figure}[htbp]
\centering
\includegraphics{figures/mermaid_inline/diagram-1.png}
\caption{The Hermes topic run}
\end{figure}
"""

# A verbatim figure that is not a diagram: a code listing shown as a figure.
VERBATIM_LISTING = r"""\begin{figure}[htbp]
\centering
\begin{verbatim}
theorem fep001_union_bound : True := trivial
\end{verbatim}
\caption{A Lean listing}
\end{figure}
"""


def test_rasterized_diagram_is_accepted(tmp_path: Path) -> None:
    _write(tmp_path, "_combined_manuscript.tex", RASTERIZED_FIGURE)
    assert mermaid_fallback_defects(tmp_path) == ()


def test_mermaid_source_shipped_as_verbatim_is_reported(tmp_path: Path) -> None:
    """The exact artifact defect: diagram source typeset as the figure."""
    _write(tmp_path, "_combined_manuscript.tex", RASTERIZED_FIGURE + MERMAID_FALLBACK)
    defects = mermaid_fallback_defects(tmp_path)
    assert len(defects) == 1
    assert "mermaid diagram shipped as verbatim source" in defects[0]
    assert "'flowchart LR'" in defects[0]
    assert "'Mermaid diagram'" in defects[0]


def test_a_verbatim_figure_that_is_not_a_diagram_is_not_reported(
    tmp_path: Path,
) -> None:
    """A code listing in a figure is legitimate; only diagram source is not."""
    _write(tmp_path, "_combined_manuscript.tex", VERBATIM_LISTING)
    assert mermaid_fallback_defects(tmp_path) == ()


def test_mermaid_audit_reads_the_caption_not_the_alt_text(tmp_path: Path) -> None:
    """A fallback with an authored caption is still a fallback."""
    _write(
        tmp_path,
        "_combined_manuscript.tex",
        MERMAID_FALLBACK.replace("Mermaid diagram", "The Hermes topic run"),
    )
    defects = mermaid_fallback_defects(tmp_path)
    assert len(defects) == 1
    assert "'The Hermes topic run'" in defects[0]


# ── staleness ─────────────────────────────────────────────────────────────
CHAPTER = (
    "# Background\n\n"
    "The table below reports the present catalogue's scope across every "
    "maintained area of the formalization.\n"
)
RENDERED = (
    "# Background\n\n"
    "The table below reports the present catalogue's scope across every "
    "maintained area of the formalization.\n"
)


def _stale_tree(tmp_path: Path, chapter: str, rendered: str) -> tuple[Path, Path]:
    manuscript = tmp_path / "manuscript"
    pdf = tmp_path / "pdf"
    manuscript.mkdir()
    pdf.mkdir()
    (pdf / "_combined_manuscript.md").write_text(rendered, encoding="utf-8")
    os.utime(pdf / "_combined_manuscript.md", (1_000, 1_000))
    (manuscript / "02b_background.md").write_text(chapter, encoding="utf-8")
    os.utime(manuscript / "02b_background.md", (2_000, 2_000))
    return manuscript, pdf


def test_a_newer_source_with_identical_content_is_not_stale(tmp_path: Path) -> None:
    """The false positive that failed the delivered artifact.

    Regenerating a chapter to byte-identical content moves its mtime. The first
    version of this guard compared mtimes and rejected a render that described
    exactly that tree.
    """
    manuscript, pdf = _stale_tree(tmp_path, CHAPTER, RENDERED)
    assert stale_render_defects(manuscript, pdf) == ()


def test_a_drifted_prose_line_is_stale(tmp_path: Path) -> None:
    """The real drift: 02b says "The table below", the render says "Table 1"."""
    manuscript, pdf = _stale_tree(
        tmp_path,
        CHAPTER,
        RENDERED.replace("The table below reports", "Table 1 reports"),
    )
    defects = stale_render_defects(manuscript, pdf)
    assert len(defects) == 1
    assert "1 line(s) absent" in defects[0]
    assert "The table below reports" in defects[0]


def test_a_render_newer_than_every_source_can_still_be_stale(tmp_path: Path) -> None:
    """The second failure this guard exists for.

    The shared template renders from the project's own rendered tree, so a
    render whose inputs were never regenerated is newer than every authored
    source and still typesets the drift. Mtime cannot see that; content can.
    """
    manuscript, pdf = _stale_tree(
        tmp_path,
        CHAPTER,
        RENDERED.replace("The table below reports", "Table 1 reports"),
    )
    os.utime(manuscript / "02b_background.md", (500, 500))

    defects = stale_render_defects(manuscript, pdf)

    assert len(defects) == 1
    assert "The table below reports" in defects[0]


def test_placeholder_lines_are_compared_through_the_render_variables(
    tmp_path: Path,
) -> None:
    """A token line matches the value it rendered to, and only that value."""
    chapter = (
        "The catalogue holds {{total_topics}} topic-scoped Lean bodies across "
        "every maintained area of the formalization.\n"
    )
    manuscript, pdf = _stale_tree(
        tmp_path,
        chapter,
        "The catalogue holds 155 topic-scoped Lean bodies across every "
        "maintained area of the formalization.\n",
    )
    assert stale_render_defects(manuscript, pdf, variables={"total_topics": 155}) == ()
    defects = stale_render_defects(manuscript, pdf, variables={"total_topics": 162})
    assert len(defects) == 1
    assert "162 topic-scoped" in defects[0]


def test_a_changed_variable_file_drifts_a_chapter_nobody_edited(
    tmp_path: Path,
) -> None:
    """A count can drift a chapter no one touched, so no source is skipped."""
    chapter = (
        "The catalogue holds {{total_topics}} topic-scoped Lean bodies across "
        "every maintained area of the formalization.\n"
    )
    manuscript, pdf = _stale_tree(
        tmp_path,
        chapter,
        "The catalogue holds 155 topic-scoped Lean bodies across every "
        "maintained area of the formalization.\n",
    )
    os.utime(manuscript / "02b_background.md", (500, 500))

    defects = stale_render_defects(manuscript, pdf, variables={"total_topics": 162})

    assert len(defects) == 1
    assert "162 topic-scoped" in defects[0]


def test_image_lines_are_not_drift(tmp_path: Path) -> None:
    """The renderer rewrites image paths; that is not a stale chapter."""
    chapter = (
        "![A generated figure showing the area distribution of the catalogue]"
        "(../output/figures/topics_by_area.png)\n"
    )
    manuscript, pdf = _stale_tree(
        tmp_path,
        chapter,
        "![A generated figure showing the area distribution of the catalogue]"
        "(figures/topics_by_area.png)\n",
    )
    assert stale_render_defects(manuscript, pdf) == ()


def test_an_absent_combined_render_is_a_defect(tmp_path: Path) -> None:
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    defects = stale_render_defects(manuscript, tmp_path / "pdf")
    assert len(defects) == 1
    assert "combined render is absent" in defects[0]


def test_preamble_is_not_compared_against_the_combined_document(
    tmp_path: Path,
) -> None:
    """``preamble.md`` becomes the LaTeX header, never combined prose."""
    manuscript, pdf = _stale_tree(tmp_path, CHAPTER, RENDERED)
    (manuscript / "preamble.md").write_text(
        "\\usepackage[margin=1cm, top=1.2cm, bottom=1.2cm, heightrounded]{geometry}\n",
        encoding="utf-8",
    )
    os.utime(manuscript / "preamble.md", (2_000, 2_000))
    assert stale_render_defects(manuscript, pdf) == ()
