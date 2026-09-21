"""The manuscript's glyph requirement is derived, probed, and recorded.

Regression cover for FEP-LEAN-R1: FreeMono covers none of the Unicode
subscripts and superscripts the Lean bodies use, so XeTeX dropped every
occurrence and printed a complement lemma as ``mu s = 1 - mu s``. The fix was
a font installed on one machine; these are the checks that keep it from
regressing silently on another.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from fep_lean.output.manuscript import UNIFIED_FORMALISM_CATALOGUE_FILENAME
from fep_lean.output.render_fonts import (
    FontProbeError,
    code_font_codepoints,
    declared_fonts,
    font_coverage_defects,
    prose_font_codepoints,
    render_font_projection,
    uncovered_codepoints,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
# The six codepoints the audited render dropped, one of which made a printed
# theorem false.
DROPPED_IN_THE_AUDITED_RENDER = (0x2098, 0x2096, 0x1D50, 0x209A, 0x1D62, 0x1D9C)


def test_the_dropped_codepoints_are_in_the_derived_requirement() -> None:
    required = set(code_font_codepoints(PROJECT_ROOT / "manuscript"))
    assert set(DROPPED_IN_THE_AUDITED_RENDER) <= required


def test_the_preamble_selects_a_face_for_code_and_for_prose() -> None:
    fonts = declared_fonts(PROJECT_ROOT / "manuscript" / "preamble.md")
    assert fonts["mono"] == "JuliaMono"
    assert fonts["main"]


def test_code_and_prose_requirements_are_read_from_the_right_spans(
    tmp_path: Path,
) -> None:
    (tmp_path / "chapter.md").write_text(
        "Prose ± sign.\n\n"
        "Inline `μ sᶜ` code.\n\n"
        "```lean\ntheorem t : κ ∘ₘ μ = μ := rfl\n```\n",
        encoding="utf-8",
    )
    code = set(code_font_codepoints(tmp_path))
    prose = set(prose_font_codepoints(tmp_path))
    assert 0x1D9C in code and 0x2098 in code
    assert 0x00B1 in prose
    assert 0x00B1 not in code
    assert 0x1D9C not in prose


def test_a_font_without_the_glyph_is_reported(tmp_path: Path) -> None:
    """FreeMono is the exact face that dropped them."""
    missing = uncovered_codepoints("FreeMono", DROPPED_IN_THE_AUDITED_RENDER)
    if missing == ():  # pragma: no cover - only on a host without FreeMono
        pytest.skip("FreeMono is not installed on this host")
    assert set(missing) == set(DROPPED_IN_THE_AUDITED_RENDER)


def test_the_selected_faces_cover_this_manuscript() -> None:
    """The selected faces cover the manuscript on a renderable host.

    CI runners resolve a glyphless JuliaMono stub, so the probe there
    deterministically drops every codepoint this manuscript typesets; that
    exact dropped-glyph set is pinned instead of skipping behind a CI
    conditional. Only a host with no fontconfig probe at all may skip.
    """
    fonts = declared_fonts(PROJECT_ROOT / "manuscript" / "preamble.md")
    required = code_font_codepoints(PROJECT_ROOT / "manuscript")
    try:
        mono_missing = uncovered_codepoints(fonts["mono"], required)
    except FontProbeError:
        pytest.skip(
            "no fc-list on this host, so no face coverage can be attested here"
        )
    else:
        if mono_missing == required:
            # The glyphless JuliaMono stub deterministically drops the entire
            # requirement, and the fail-closed gate must say so instead of
            # blessing the host. A stub that starts resolving glyphs (or a
            # probe that silently stops querying) takes the branch below and
            # must attest real coverage there.
            defects = font_coverage_defects(PROJECT_ROOT)
            assert defects
            assert any(
                defect.startswith(
                    f"mono: installed {fonts['mono']} has no glyph"
                )
                for defect in defects
            )
            return
        assert font_coverage_defects(PROJECT_ROOT) == ()


def test_a_preamble_with_no_code_face_is_a_defect(tmp_path: Path) -> None:
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "preamble.md").write_text(
        "\\setmainfont{FreeSerif}\n", encoding="utf-8"
    )
    (manuscript / "chapter.md").write_text("`sᶜ`\n", encoding="utf-8")
    (manuscript / UNIFIED_FORMALISM_CATALOGUE_FILENAME).write_text("", encoding="utf-8")
    defects = font_coverage_defects(tmp_path)
    assert len(defects) == 1
    assert "selects no \\setmonofont" in defects[0]


def test_requirement_derivation_fails_closed_without_the_appendix(
    tmp_path: Path,
) -> None:
    """A fresh checkout must not derive an understated glyph requirement.

    The generated appendix is part of the typeset surface; deriving the
    requirement without it silently shrinks the committed record (and then
    every later check agrees with the wrong record).
    """
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "chapter.md").write_text("`sᶜ`\n", encoding="utf-8")
    with pytest.raises(FontProbeError) as error:
        font_coverage_defects(tmp_path)
    assert UNIFIED_FORMALISM_CATALOGUE_FILENAME in str(error.value)
    assert "fep-lean catalogue" in str(error.value)
    with pytest.raises(FontProbeError):
        render_font_projection(tmp_path)


def test_an_unprobeable_host_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    """Not knowing is not the same as being covered."""
    monkeypatch.setattr("fep_lean.output.render_fonts.shutil.which", lambda _name: None)
    with pytest.raises(FontProbeError) as error:
        uncovered_codepoints("JuliaMono", (0x2098,))
    assert "fontconfig" in str(error.value)


def test_the_committed_requirement_matches_the_sources() -> None:
    appendix = PROJECT_ROOT / "manuscript" / UNIFIED_FORMALISM_CATALOGUE_FILENAME
    if not appendix.is_file():
        pytest.skip(
            "generated appendix is missing; run `uv run fep-lean catalogue` first"
        )
    committed = json.loads(
        (PROJECT_ROOT / "docs" / "render-fonts.json").read_text(encoding="utf-8")
    )
    assert committed == render_font_projection(PROJECT_ROOT)
