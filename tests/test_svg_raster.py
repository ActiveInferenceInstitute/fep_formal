"""Coverage for the manuscript figure publication path (``svg_raster``).

The rasterizer binary is faked with a fixture executable so every contract is
exercised deterministically in both the workspace (where ``rsvg-convert`` is
installed for real renders) and the hermetic acceptance environment (where the
controlled PATH deliberately does not carry it). One real-binary test runs
wherever the rasterizer exists and is skipped elsewhere by capability.
"""

from __future__ import annotations

import os
import shutil
import textwrap
import time
from pathlib import Path

import pytest

from fep_lean.output.svg_raster import (
    MANUSCRIPT_COPIED_FIGURES,
    MANUSCRIPT_SVG_FIGURES,
    RASTER_WIDTH_PX,
    RasterizedFigure,
    SvgRasterError,
    manuscript_png_drift,
    rasterize_svg,
    resolve_rasterizer,
    write_manuscript_figure_pngs,
)

MINIMAL_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="80" height="40">'
    '<rect width="80" height="40" fill="#4a6"/></svg>\n'
)
FAKE_PNG = b"\x89PNG\r\n\x1a\nfake-png-bytes"

FAKE_RASTERIZER = textwrap.dedent(
    """\
    #!/bin/sh
    out=""
    prev=""
    for argument in "$@"; do
        if [ "$prev" = "--output" ]; then out="$argument"; fi
        prev="$argument"
    done
    case "${FAKE_RSVG_MODE:-ok}" in
        fail) echo "fake rsvg: cannot render" >&2; exit 1 ;;
        silent) exit 0 ;;
        *) printf '%b' '\\x89PNG\\r\\n\\x1a\\nfake-png-bytes' > "$out"; exit 0 ;;
    esac
    """
)


@pytest.fixture
def svg(tmp_path: Path) -> Path:
    path = tmp_path / "projection.svg"
    path.write_text(MINIMAL_SVG, encoding="utf-8")
    return path


@pytest.fixture
def fake_rasterizer(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    executable = tmp_path / "bin" / "rsvg-convert"
    executable.parent.mkdir(parents=True, exist_ok=True)
    executable.write_text(FAKE_RASTERIZER, encoding="utf-8")
    executable.chmod(0o755)
    monkeypatch.setattr(
        "fep_lean.output.svg_raster.resolve_rasterizer", lambda: executable
    )
    return executable


def test_rasterize_svg_writes_a_real_png(
    svg: Path, tmp_path: Path, fake_rasterizer: Path
) -> None:
    png = tmp_path / "out" / "figure.png"
    figure = rasterize_svg(svg, png)
    assert isinstance(figure, RasterizedFigure)
    assert figure.byte_size == len(FAKE_PNG)
    assert png.read_bytes() == FAKE_PNG


def test_rasterize_missing_svg_is_an_error(tmp_path: Path) -> None:
    with pytest.raises(SvgRasterError, match="SVG projection not found"):
        rasterize_svg(tmp_path / "absent.svg", tmp_path / "figure.png")


def test_rasterize_failure_is_reported_with_the_rasterizer_detail(
    svg: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake_rasterizer: Path
) -> None:
    del fake_rasterizer
    monkeypatch.setenv("FAKE_RSVG_MODE", "fail")
    with pytest.raises(SvgRasterError, match="failed for .*cannot render"):
        rasterize_svg(svg, tmp_path / "figure.png")


def test_rasterize_silent_no_output_is_reported(
    svg: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake_rasterizer: Path
) -> None:
    del fake_rasterizer
    monkeypatch.setenv("FAKE_RSVG_MODE", "silent")
    with pytest.raises(SvgRasterError, match="wrote no output"):
        rasterize_svg(svg, tmp_path / "figure.png")


def test_rasterize_fixed_width_is_stable(
    svg: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    executable = tmp_path / "width-recorder"
    script = (
        "#!/bin/sh\n"
        'out=""; prev=""\n'
        'for argument in "$@"; do\n'
        '    if [ "$prev" = "--output" ]; then out="$argument"; fi\n'
        '    prev="$argument"\n'
        "done\n"
        "printf '%b' '\\x89PNG\\r\\n\\x1a\\nfake-png-bytes' > \"$out\"\n"
    )
    executable.parent.mkdir(parents=True, exist_ok=True)
    executable.write_text(script, encoding="utf-8")
    executable.chmod(0o755)
    monkeypatch.setattr(
        "fep_lean.output.svg_raster.resolve_rasterizer", lambda: executable
    )
    first = tmp_path / "a.png"
    second = tmp_path / "b.png"
    figure_a = rasterize_svg(svg, first)
    figure_b = rasterize_svg(svg, second, width_px=RASTER_WIDTH_PX)
    assert first.read_bytes() == second.read_bytes()
    assert figure_a.byte_size == figure_b.byte_size == len(FAKE_PNG)


def test_write_and_drift_round_trip(tmp_path: Path, fake_rasterizer: Path) -> None:
    del fake_rasterizer
    project_root = tmp_path
    for svg_relative in MANUSCRIPT_SVG_FIGURES.values():
        target = project_root / svg_relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(MINIMAL_SVG, encoding="utf-8")
    for source_relative in MANUSCRIPT_COPIED_FIGURES.values():
        source = project_root / source_relative
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes(b"png-bytes")

    figures_dir = project_root / "output" / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    produced = write_manuscript_figure_pngs(project_root)
    assert len(produced) == len(MANUSCRIPT_SVG_FIGURES) + len(MANUSCRIPT_COPIED_FIGURES)
    assert all(figure.byte_size > 0 for figure in produced)
    assert manuscript_png_drift(project_root) == []

    # A missing authored asset is a named defect, not a silent pass.
    missing_asset = next(iter(MANUSCRIPT_COPIED_FIGURES.values()))
    (project_root / missing_asset).unlink()
    with pytest.raises(SvgRasterError, match="authored figure asset not found"):
        write_manuscript_figure_pngs(project_root)
    for source_relative in MANUSCRIPT_COPIED_FIGURES.values():
        source = project_root / source_relative
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes(b"png-bytes")

    # A PNG older than its SVG is stale by construction.
    past = time.time() - 120
    for png_name in MANUSCRIPT_SVG_FIGURES:
        os.utime(figures_dir / png_name, (past, past))
    drift = manuscript_png_drift(project_root)
    assert any("older than" in line for line in drift)

    # A missing source projection is a named defect, not a silent pass.
    stale_target = next(iter(MANUSCRIPT_SVG_FIGURES.values()))
    (project_root / stale_target).unlink()
    drift = manuscript_png_drift(project_root)
    assert any("figure source missing" in line for line in drift)


def test_resolve_rasterizer_prefers_the_named_binary_on_path() -> None:
    if shutil.which("rsvg-convert") is None:
        pytest.skip("rsvg-convert toolchain unavailable")
    assert resolve_rasterizer().name == "rsvg-convert"
