"""Acceptance for the fail-closed LaTeX-log gate.

Regression cover for FEP-LEAN-R2: a render that wrote ``Output written on``
while dropping 162 characters and logging two TeX errors was reported as
successful.
"""

from __future__ import annotations

from pathlib import Path

from fep_lean.output.render_log import (
    RenderLogDefects,
    render_log_defects,
    scan_render_log,
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


def test_output_written_does_not_excuse_errors_or_dropped_glyphs(tmp_path: Path) -> None:
    """The exact fail-open shape: a PDF was written, yet the log is defective."""

    log = _write(tmp_path, "_combined_manuscript.log", DEFECTIVE_LOG)
    assert "Output written on" in log.read_text(encoding="utf-8")
    defects = scan_render_log(log)
    assert not defects.clean
    assert len(defects.tex_errors) == 2
    assert len(defects.missing_characters) == 3


def test_missing_glyphs_are_grouped_by_codepoint(tmp_path: Path) -> None:
    defects = scan_render_log(_write(tmp_path, "_combined_manuscript.log", DEFECTIVE_LOG))
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
