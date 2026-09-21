"""Acceptance for the fail-closed LaTeX-log gate.

Regression cover for FEP-LEAN-R2: a render that wrote ``Output written on``
while dropping 162 characters and logging two TeX errors was reported as
successful.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest

from fep_lean.output.render_log import (
    RECEIPT_VERSION,
    RenderLogDefects,
    build_acceptance_receipt,
    contents_number_overflow_defects,
    manuscript_source_digest,
    manuscript_source_digests,
    mermaid_fallback_defects,
    receipt_defects,
    render_log_defects,
    rendered_manuscript_sources,
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


def test_a_per_render_source_stamp_line_is_not_drift(tmp_path: Path) -> None:
    """The stamp names this render's commit; no projection can agree with it.

    ``manuscript_vars.yaml`` records the commit it was generated at, so one
    commit later the file and the render disagree by construction. Comparing
    that line would report every render as stale.
    """
    chapter = (
        "That checkout is `{{source.short_commit}}`, rendered "
        "{{source.render_date}}, and the counts come from it alone.\n"
    )
    manuscript, pdf = _stale_tree(
        tmp_path,
        chapter,
        "That checkout is `abc123def456`, rendered 2026-09-06, and the counts "
        "come from it alone.\n",
    )

    assert (
        stale_render_defects(
            manuscript, pdf, variables={"source": {"short_commit": "stale000"}}
        )
        == ()
    )


def test_a_drifted_line_beside_a_stamp_line_is_still_drift(tmp_path: Path) -> None:
    """Only the stamp line is exempt, not the file that carries it."""
    chapter = (
        "That checkout is `{{source.short_commit}}`, rendered "
        "{{source.render_date}}, and the counts come from it alone.\n\n"
        "The table below reports the present catalogue's scope across every "
        "maintained area of the formalization.\n"
    )
    manuscript, pdf = _stale_tree(
        tmp_path,
        chapter,
        "That checkout is `abc123def456`, rendered 2026-09-06, and the counts "
        "come from it alone.\n\n"
        "Table 1 reports the present catalogue's scope across every "
        "maintained area of the formalization.\n",
    )

    defects = stale_render_defects(
        manuscript, pdf, variables={"source": {"short_commit": "stale000"}}
    )

    assert len(defects) == 1
    assert "The table below reports" in defects[0]


def test_a_caption_line_the_renderer_consumes_is_not_drift(tmp_path: Path) -> None:
    """The italic line under a diagram fence becomes the figure's caption.

    Its words survive into ``\\caption{...}`` and the figure's ``alt`` text, so
    the line is gone while the sentence is not.
    """
    caption = (
        "The Hermes topic run: a canonical topic entry reaches a Lean block "
        "only through a session and a compiler."
    )
    manuscript, pdf = _stale_tree(
        tmp_path,
        f"*{caption}*\n",
        "\\begin{figure}[htbp]\n"
        f"\\includegraphics[alt={{{caption}}}]{{figures/diagram.png}}\n"
        f"\\caption{{{caption}}}\n"
        "\\end{figure}\n",
    )

    assert stale_render_defects(manuscript, pdf) == ()


def test_a_drifted_caption_is_still_drift(tmp_path: Path) -> None:
    """Only the markup is forgiven; changed words are not a substring either."""
    manuscript, pdf = _stale_tree(
        tmp_path,
        "*The Hermes topic run: a canonical topic entry reaches a Lean block "
        "only through a session and a compiler.*\n",
        "\\caption{The Hermes topic run: a canonical topic entry reaches a Lean "
        "block only through a retry.}\n",
    )

    defects = stale_render_defects(manuscript, pdf)

    assert len(defects) == 1
    assert "The Hermes topic run" in defects[0]


# ── acceptance receipt ────────────────────────────────────────────────────
# A hosted runner cannot re-run the acceptance above, so the gate that reaches
# CI is this receipt: written only by a clean acceptance, committed, and bound
# to the manuscript sources it covered.
CLEAN_COUNTS = {
    "tex_errors": 0,
    "missing_characters": 0,
    "mermaid_fallbacks": 0,
    "stale_sources": 0,
    "uncaptioned_tables": 0,
    "contents_number_overflows": 0,
}


def _manuscript(tmp_path: Path) -> Path:
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "01_abstract.md").write_text("An abstract.\n", encoding="utf-8")
    (manuscript / "preamble.md").write_text(
        "\\setmonofont{JuliaMono}\n", encoding="utf-8"
    )
    (manuscript / "09z_unified_formalism_catalogue.md").write_text(
        "# Unified formalism catalogue\n\n155 topic-scoped Lean bodies.\n",
        encoding="utf-8",
    )
    (manuscript / "AGENTS.md").write_text("Contributor notes.\n", encoding="utf-8")
    return manuscript


def _pdf_dir(tmp_path: Path) -> Path:
    pdf_dir = tmp_path / "pdf"
    pdf_dir.mkdir()
    _write(pdf_dir, "_combined_manuscript.log", CLEAN_LOG)
    return pdf_dir


def test_contributor_documentation_is_not_a_typeset_source(tmp_path: Path) -> None:
    """The digest covers what the template typesets, not what lives beside it."""
    names = [path.name for path in rendered_manuscript_sources(_manuscript(tmp_path))]
    assert names == ["01_abstract.md", "09z_unified_formalism_catalogue.md"]


def test_the_preamble_is_part_of_the_digest(tmp_path: Path) -> None:
    """Changing the font selection must invalidate a receipt.

    ``preamble.md`` is never typeset as prose, so it is not a rendered source
    -- but selecting a face without the document's glyphs is exactly the change
    that shipped a false theorem, and a digest that ignored it would accept
    that change silently.
    """
    manuscript = _manuscript(tmp_path)
    before = manuscript_source_digest(manuscript)
    (manuscript / "preamble.md").write_text(
        "\\setmonofont{FreeMono}\n", encoding="utf-8"
    )
    assert manuscript_source_digest(manuscript) != before


def test_every_covered_file_carries_its_own_digest(tmp_path: Path) -> None:
    manuscript = _manuscript(tmp_path)
    digests = manuscript_source_digests(manuscript)
    assert sorted(digests) == [
        "01_abstract.md",
        "09z_unified_formalism_catalogue.md",
        "preamble.md",
    ]


def test_a_clean_acceptance_receipt_covers_this_checkout(tmp_path: Path) -> None:
    manuscript = _manuscript(tmp_path)
    receipt = build_acceptance_receipt(
        manuscript, _pdf_dir(tmp_path), counts=CLEAN_COUNTS
    )
    assert receipt["accepted"] is True
    assert receipt["receipt_version"] == RECEIPT_VERSION
    assert receipt["pages"] == 346
    path = tmp_path / "render-acceptance.json"
    path.write_text(json.dumps(receipt), encoding="utf-8")
    assert receipt_defects(path, manuscript) == ()


def test_a_receipt_never_claims_acceptance_for_a_defective_render(
    tmp_path: Path,
) -> None:
    receipt = build_acceptance_receipt(
        _manuscript(tmp_path),
        _pdf_dir(tmp_path),
        counts={**CLEAN_COUNTS, "missing_characters": 3},
    )
    assert receipt["accepted"] is False


def test_a_receipt_recording_a_defect_is_rejected(tmp_path: Path) -> None:
    """Even hand-edited to ``accepted``, a recorded defect fails the gate."""
    manuscript = _manuscript(tmp_path)
    receipt = build_acceptance_receipt(
        manuscript, _pdf_dir(tmp_path), counts={**CLEAN_COUNTS, "tex_errors": 2}
    )
    receipt["accepted"] = True
    path = tmp_path / "render-acceptance.json"
    path.write_text(json.dumps(receipt), encoding="utf-8")
    defects = receipt_defects(path, manuscript)
    assert any("reported 2 tex_errors" in line for line in defects)


def test_an_edited_chapter_leaves_the_receipt_stale(tmp_path: Path) -> None:
    """The defect this gate exists for: sources shipped without a re-render."""
    manuscript = _manuscript(tmp_path)
    path = tmp_path / "render-acceptance.json"
    path.write_text(
        json.dumps(
            build_acceptance_receipt(
                manuscript, _pdf_dir(tmp_path), counts=CLEAN_COUNTS
            )
        ),
        encoding="utf-8",
    )
    assert receipt_defects(path, manuscript) == ()
    (manuscript / "01_abstract.md").write_text(
        "An abstract, revised after the render.\n", encoding="utf-8"
    )
    defects = receipt_defects(path, manuscript)
    assert any("predates these sources" in line for line in defects)
    # The mismatch names the file, so a reader does not bisect thirty of them.
    assert any("changed since that render: 01_abstract.md" in line for line in defects)


def test_an_absent_receipt_is_a_defect_not_a_pass(tmp_path: Path) -> None:
    defects = receipt_defects(tmp_path / "nothing.json", _manuscript(tmp_path))
    assert len(defects) == 1
    assert "no acceptance receipt" in defects[0]


def test_an_unreadable_receipt_is_a_defect(tmp_path: Path) -> None:
    path = tmp_path / "render-acceptance.json"
    path.write_text("{not json", encoding="utf-8")
    defects = receipt_defects(path, _manuscript(tmp_path))
    assert len(defects) == 1
    assert "unreadable acceptance receipt" in defects[0]


def test_a_receipt_from_a_future_schema_is_a_defect(tmp_path: Path) -> None:
    manuscript = _manuscript(tmp_path)
    receipt = build_acceptance_receipt(
        manuscript, _pdf_dir(tmp_path), counts=CLEAN_COUNTS
    )
    receipt["receipt_version"] = RECEIPT_VERSION + 1
    path = tmp_path / "render-acceptance.json"
    path.write_text(json.dumps(receipt), encoding="utf-8")
    assert any("receipt_version" in line for line in receipt_defects(path, manuscript))


def test_a_receipt_missing_a_check_is_not_accepted(tmp_path: Path) -> None:
    """A receipt written by an older acceptance cannot vouch for a newer one."""
    manuscript = _manuscript(tmp_path)
    receipt = build_acceptance_receipt(
        manuscript, _pdf_dir(tmp_path), counts=CLEAN_COUNTS
    )
    del receipt["checks"]["mermaid_fallbacks"]
    path = tmp_path / "render-acceptance.json"
    path.write_text(json.dumps(receipt), encoding="utf-8")
    assert any(
        "does not record mermaid_fallbacks" in line
        for line in receipt_defects(path, manuscript)
    )


def test_building_a_receipt_without_every_check_is_refused(tmp_path: Path) -> None:
    """The builder cannot silently omit a check the verifier will demand."""
    with pytest.raises(ValueError, match="missing checks"):
        build_acceptance_receipt(
            _manuscript(tmp_path),
            _pdf_dir(tmp_path),
            counts={"tex_errors": 0},
        )


# ── receipt classification + fail-closed gaps (W2 regressions) ───────────


def test_a_moved_generated_appendix_names_the_catalogue_remediation(
    tmp_path: Path,
) -> None:
    """A build product's move names its regeneration command, not a re-render."""
    manuscript = _manuscript(tmp_path)
    receipt = build_acceptance_receipt(
        manuscript, _pdf_dir(tmp_path), counts=dict(CLEAN_COUNTS)
    )
    path = _write(tmp_path, "render-acceptance.json", json.dumps(receipt))
    (manuscript / "09z_unified_formalism_catalogue.md").write_text(
        "# Unified formalism catalogue, regenerated.\n", encoding="utf-8"
    )
    defects = receipt_defects(path, manuscript)
    stale = [line for line in defects if "predates these sources" in line]
    assert len(stale) == 1
    assert "regenerate the build product with `uv run fep-lean catalogue`" in stale[0]
    assert "re-run scripts/render_publication.py" not in stale[0]
    assert "09z_unified_formalism_catalogue.md (generated appendix)" in stale[0]


def test_a_moved_authored_chapter_keeps_the_render_remediation(
    tmp_path: Path,
) -> None:
    """An authored chapter's move still names the render, not the catalogue."""
    manuscript = _manuscript(tmp_path)
    receipt = build_acceptance_receipt(
        manuscript, _pdf_dir(tmp_path), counts=dict(CLEAN_COUNTS)
    )
    path = _write(tmp_path, "render-acceptance.json", json.dumps(receipt))
    (manuscript / "01_abstract.md").write_text(
        "An abstract, revised after the render.\n", encoding="utf-8"
    )
    defects = receipt_defects(path, manuscript)
    stale = [line for line in defects if "predates these sources" in line]
    assert len(stale) == 1
    assert "re-run scripts/render_publication.py" in stale[0]
    assert "fep-lean catalogue" not in stale[0]
    assert "changed since that render: 01_abstract.md" in stale[0]


def test_mixed_moves_name_both_remediations(tmp_path: Path) -> None:
    """Authored chapters keep the render remediation; appendices name theirs."""
    manuscript = _manuscript(tmp_path)
    receipt = build_acceptance_receipt(
        manuscript, _pdf_dir(tmp_path), counts=dict(CLEAN_COUNTS)
    )
    path = _write(tmp_path, "render-acceptance.json", json.dumps(receipt))
    (manuscript / "01_abstract.md").write_text(
        "An abstract, revised after the render.\n", encoding="utf-8"
    )
    (manuscript / "09z_unified_formalism_catalogue.md").write_text(
        "# Unified formalism catalogue, regenerated.\n", encoding="utf-8"
    )
    defects = receipt_defects(path, manuscript)
    stale = [line for line in defects if "predates these sources" in line]
    assert len(stale) == 1
    assert "re-run scripts/render_publication.py" in stale[0]
    assert "changed since that render: 01_abstract.md" in stale[0]
    assert "09z_unified_formalism_catalogue.md (generated appendix)" in stale[0]
    appendix = [line for line in defects if "generated appendix 09z_" in line]
    assert len(appendix) == 1
    assert "regenerate it with `uv run fep-lean catalogue`" in appendix[0]


def test_a_missing_generated_appendix_is_a_defect_even_when_the_digest_matches(
    tmp_path: Path,
) -> None:
    """A receipt built over an unhydrated checkout cannot vouch for one."""
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "01_abstract.md").write_text("An abstract.\n", encoding="utf-8")
    (manuscript / "preamble.md").write_text(
        "\\setmonofont{JuliaMono}\n", encoding="utf-8"
    )
    receipt = build_acceptance_receipt(
        manuscript, _pdf_dir(tmp_path), counts=dict(CLEAN_COUNTS)
    )
    path = _write(tmp_path, "render-acceptance.json", json.dumps(receipt))
    defects = receipt_defects(path, manuscript)
    assert any(
        "09z_unified_formalism_catalogue.md" in line
        and "uv run fep-lean catalogue" in line
        for line in defects
    )
    assert not any("predates these sources" in line for line in defects)


def test_a_receipt_covering_a_now_absent_appendix_names_regeneration(
    tmp_path: Path,
) -> None:
    """Deleting the build product stales the receipt and is its own defect."""
    manuscript = _manuscript(tmp_path)
    receipt = build_acceptance_receipt(
        manuscript, _pdf_dir(tmp_path), counts=dict(CLEAN_COUNTS)
    )
    path = _write(tmp_path, "render-acceptance.json", json.dumps(receipt))
    (manuscript / "09z_unified_formalism_catalogue.md").unlink()
    defects = receipt_defects(path, manuscript)
    assert any("predates these sources" in line for line in defects)
    assert any(
        "09z_unified_formalism_catalogue.md is missing" in line
        and "uv run fep-lean catalogue" in line
        for line in defects
    )


# ── log-coverage gaps (W2 regressions) ──────────────────────────────────


def test_contents_overflow_scans_the_stdout_log_when_the_combined_log_is_absent(
    tmp_path: Path,
) -> None:
    """A stdout-only render is judged from the stdout log, and the gap is named."""
    _write(tmp_path, "_latex_stdout.log", CONTENTS_OVERFLOW_LOG)
    defects = contents_number_overflow_defects(tmp_path)
    assert len(defects) == 2
    assert "_combined_manuscript.log" in defects[0]
    assert "expected log is absent" in defects[0]
    assert "_latex_stdout.log exists" in defects[0]
    assert "contents number 15.100" in defects[1]


def test_render_log_defects_reports_a_missing_expected_log_when_a_sibling_exists(
    tmp_path: Path,
) -> None:
    """Half the compiler evidence must not read as a clean render."""
    _write(tmp_path, "_latex_stdout.log", CLEAN_LOG)
    results = render_log_defects(tmp_path)
    assert len(results) == 2
    assert results[0].log_path.name == "_combined_manuscript.log"
    assert not results[0].clean
    assert "compiler log not found" in results[0].tex_errors[0]
    assert results[1].log_path.name == "_latex_stdout.log"
    assert results[1].clean


# ── acceptance script degraded mode (W2 regressions) ────────────────────


def _check_render_log_module() -> Any:
    """Load the acceptance script the way test_render_publication loads its driver."""
    import importlib.util
    import sys

    scripts = Path(__file__).resolve().parent.parent / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    spec = importlib.util.spec_from_file_location(
        "check_render_log_w2", scripts / "check_render_log.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_absent_manuscript_vars_prints_a_degraded_staleness_line(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Without the variables projection the OK line would overstate coverage."""
    manuscript = tmp_path / "manuscript"
    pdf = tmp_path / "pdf"
    manuscript.mkdir()
    pdf.mkdir()
    _write(pdf, "_combined_manuscript.log", CLEAN_LOG)
    _write(pdf, "_latex_stdout.log", CLEAN_LOG)
    (manuscript / "01_abstract.md").write_text("An abstract.\n", encoding="utf-8")
    _write(pdf, "_combined_manuscript.md", "An abstract.\n")
    module = _check_render_log_module()
    status = module.main(
        ["--pdf-dir", str(pdf), "--manuscript-dir", str(manuscript)]
    )
    out = capsys.readouterr().out
    assert (
        "WARN: manuscript_vars.yaml absent; placeholder-carrying lines "
        "skipped from the staleness comparison" in out
    )
    assert "OK: every manuscript source is typeset in the combined render" not in out
    assert status == 0


def test_present_manuscript_vars_keeps_the_unconditional_ok_line(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """With the projection present the comparison is complete and says so."""
    manuscript = tmp_path / "manuscript"
    pdf = tmp_path / "pdf"
    manuscript.mkdir()
    pdf.mkdir()
    _write(pdf, "_combined_manuscript.log", CLEAN_LOG)
    _write(pdf, "_latex_stdout.log", CLEAN_LOG)
    (manuscript / "01_abstract.md").write_text("An abstract.\n", encoding="utf-8")
    _write(pdf, "_combined_manuscript.md", "An abstract.\n")
    (manuscript / "manuscript_vars.yaml").write_text(
        "topic_count: 155\n", encoding="utf-8"
    )
    module = _check_render_log_module()
    module.main(["--pdf-dir", str(pdf), "--manuscript-dir", str(manuscript)])
    out = capsys.readouterr().out
    assert "OK: every manuscript source is typeset in the combined render" in out
    assert "WARN: manuscript_vars.yaml absent" not in out
