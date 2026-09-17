"""Deterministic builder for the canonical graphical-abstract asset.

``manuscript/assets/graphical-abstract.png`` is an authored image asset whose
exact bytes are pinned by the ``sha256`` recorded in ``manuscript/config.yaml``
and validated by ``fep_lean.output.publication_metadata.load_graphical_abstract``
on every manuscript render.  This module is that asset's producer: the art is
regenerated from a checkout instead of hand-edited pixels, so the pinned bytes
always have a source.

The rendered PNG is written as an 8-bit, non-interlaced RGB file -- the exact
canonical form ``load_graphical_abstract`` requires -- using a standard-library
PNG encoder.  Matplotlib's own writer emits RGBA and would need an additional
dependency to re-encode; the encoder below keeps the producer dependency-free
and byte-deterministic.  No timestamps, host metrics, or wall-clock values
enter the canvas.
"""

from __future__ import annotations

import struct
import zlib
from pathlib import Path
from typing import cast

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle

from fep_lean.output.fsutil import atomic_write_bytes

__all__ = [
    "GRAPHICAL_ABSTRACT_RELATIVE",
    "HEIGHT_PX",
    "WIDTH_PX",
    "render_graphical_abstract",
]

GRAPHICAL_ABSTRACT_RELATIVE = Path("manuscript/assets/graphical-abstract.png")

# The canonical asset dimensions ``manuscript/config.yaml`` declares.  The
# canvas is sized so ``figure`` pixels are exactly these: a mismatch is a hard
# error, never a rescale.
WIDTH_PX = 1536
HEIGHT_PX = 1024
# Inch-space canvas the layout is drawn in; WIDTH_PX / 200 by HEIGHT_PX / 200.
CANVAS_W = 7.68
CANVAS_H = 5.12

# The catalogue figure palette (fep_lean.output.figures), reused so the
# abstract shares the manuscript's visual language.
_BLUE = "#315f8c"
_GREEN = "#2f855a"
_AMBER = "#d69e2e"
_ACCENT = "#3182ce"
_GRAY = "#9aa5b1"
_INK = "#2d3748"
_BAND = "#f4f4f1"


def _encode_png_rgb(width: int, height: int, rgba: bytes) -> bytes:
    """Encode raw RGBA canvas bytes as a canonical 8-bit RGB PNG."""

    canvas = np.frombuffer(rgba, dtype=np.uint8).reshape(height, width, 4)
    # One filter-type-0 byte per scanline, then the RGB triplets.
    raw = np.zeros((height, 1 + width * 3), dtype=np.uint8)
    raw[:, 0] = 0
    raw[:, 1:] = canvas[:, :, :3].reshape(height, width * 3)
    compressed = zlib.compress(raw.tobytes(), 9)

    def chunk(tag: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload))
            + tag
            + payload
            + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF)
        )

    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", compressed)
        + chunk(b"IEND", b"")
    )


def _stage_box(
    ax: Axes,
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    title: str,
    lines: list[str],
    edge: str,
    face: str,
    dashed: bool = False,
) -> None:
    """Draw one pipeline stage box with a bold title and bullet lines.

    Coordinates are inches on the 7.68 x 5.12 canvas; font sizes are points.
    Every bullet line is kept short enough for a 2.18-inch box at 8 pt.
    """

    ax.add_patch(
        Rectangle(
            (x, y),
            w,
            h,
            facecolor=face,
            edgecolor=edge,
            linewidth=1.4,
            linestyle=(0, (4, 3)) if dashed else "solid",
            zorder=2,
        )
    )
    ax.text(
        x + w / 2,
        y + h - 0.16,
        title,
        ha="center",
        va="top",
        fontsize=9.8,
        fontweight="bold",
        color=edge if not dashed else _INK,
        zorder=3,
    )
    body = "\n".join(f"• {line}" for line in lines)
    ax.text(
        x + w / 2,
        y + h - 0.36,
        body,
        ha="center",
        va="top",
        fontsize=7.6,
        color=_INK,
        linespacing=1.5,
        zorder=3,
    )


def _arrow(
    ax: Axes,
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    color: str = _BLUE,
    dashed: bool = False,
) -> None:
    """Draw one directed arrow, optionally dashed."""

    ax.annotate(
        "",
        xy=end,
        xytext=start,
        arrowprops={
            "arrowstyle": "-|>",
            "color": color,
            "linewidth": 1.6,
            "linestyle": (0, (4, 3)) if dashed else "solid",
            "mutation_scale": 13,
            "shrinkA": 1,
            "shrinkB": 1,
        },
        zorder=4,
    )


def _draw(fig: Figure) -> None:
    """Compose the whole abstract on ``fig`` in inch coordinates."""

    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(0, CANVAS_W)
    ax.set_ylim(0, CANVAS_H)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    ax.text(
        0.22,
        CANVAS_H - 0.24,
        "Towards Lean 4 Formalization of the Free Energy Principle",
        ha="left",
        va="center",
        fontsize=15,
        fontweight="bold",
        color=_INK,
    )
    ax.text(
        0.22,
        CANVAS_H - 0.42,
        "AI-driven theorem sketching and verification for active inference and Bayesian mechanics",
        ha="left",
        va="center",
        fontsize=9,
        color="#5a6472",
    )

    # Row 1: authoring inputs -> generated catalogue -> pinned compile.
    box_w, gutter = 2.18, 0.35
    row1_y, row1_h = 2.86, 1.44
    x1, x2, x3 = 0.22, 0.22 + box_w + gutter, 0.22 + 2 * (box_w + gutter)
    _stage_box(
        ax,
        x1,
        row1_y,
        box_w,
        row1_h,
        title="GNN-typed authoring inputs",
        lines=[
            "catalogue metadata · maturity",
            "novelty + typed relations",
            "family-owned Lean bodies",
            "joined by stable topic ID",
        ],
        edge=_ACCENT,
        face="#eaf1f9",
    )
    _stage_box(
        ax,
        x2,
        row1_y,
        box_w,
        row1_h,
        title="Generated catalogue",
        lines=[
            "155 topics · 20 families",
            "regeneration-identical",
            "YAML / Lean / docs projections",
            "reviewed dispositions: formalized,",
            "conditional, structural",
        ],
        edge=_BLUE,
        face="#e9eef4",
    )
    _stage_box(
        ax,
        x3,
        row1_y,
        box_w,
        row1_h,
        title="Pinned Lean 4 + Mathlib",
        lines=[
            "lake build FepSketches",
            "zero warnings · zero sorry",
            "Mathlib KL + contraction lemmas",
            "reused, not restated",
        ],
        edge=_GREEN,
        face="#e9f4ee",
    )
    _arrow(ax, (x1 + box_w, row1_y + row1_h / 2), (x2, row1_y + row1_h / 2))
    _arrow(ax, (x2 + box_w, row1_y + row1_h / 2), (x3, row1_y + row1_h / 2))

    # Row 2: receipt -> fail-closed projection, with the optional full mode.
    row2_y, row2_h = 0.92, 1.44
    _stage_box(
        ax,
        x3,
        row2_y,
        box_w,
        row2_h,
        title="Native evidence receipt",
        lines=[
            "source-digest-bound",
            "claim-ready vs the live roster",
            "independent validator",
            "no green build invents evidence",
        ],
        edge=_AMBER,
        face="#faf3e0",
    )
    _stage_box(
        ax,
        x2,
        row2_y,
        box_w,
        row2_h,
        title="Fail-closed manuscript",
        lines=[
            "placeholder + reference audits",
            "render-acceptance receipt",
            "sources never auto-edited",
            "stale evidence blocks render",
        ],
        edge=_BLUE,
        face="#e9eef4",
    )
    _stage_box(
        ax,
        x1,
        row2_y,
        box_w,
        row2_h,
        title="Optional full mode",
        lines=[
            "Hermes + OpenGauss credentials",
            "full-run receipt, validated",
            "separate, optional contract",
            "historical reports stay historical",
        ],
        edge=_GRAY,
        face="#f4f4f2",
        dashed=True,
    )
    _arrow(ax, (x3 + box_w / 2, row1_y), (x3 + box_w / 2, row2_y + row2_h))
    _arrow(ax, (x3, row2_y + row2_h / 2), (x2 + box_w, row2_y + row2_h / 2))
    _arrow(
        ax,
        (x1 + box_w, row2_y + row2_h / 2),
        (x2, row2_y + row2_h / 2),
        color=_GRAY,
        dashed=True,
    )

    # Honesty band: the boundary the whole pipeline enforces.
    ax.add_patch(
        Rectangle(
            (0.22, 0.16),
            CANVAS_W - 0.44,
            0.5,
            facecolor=_BAND,
            edgecolor=_GRAY,
            linewidth=0.9,
            zorder=2,
        )
    )
    ax.text(
        CANVAS_W / 2,
        0.41,
        "A green build proves the sketch compiles — reviewed semantic dispositions "
        "(formalized, conditional, structural)\nare evidence in their own right; "
        "compilation never promotes a weaker row.",
        ha="center",
        va="center",
        fontsize=8.2,
        style="italic",
        color=_INK,
        zorder=3,
    )


def render_graphical_abstract(project_root: Path) -> Path:
    """Render the canonical graphical abstract and return its path.

    The output is byte-deterministic for a fixed toolchain: the canvas is
    drawn without dates or host metrics and encoded by the standard-library
    PNG writer above.  The write is atomic so a crash cannot leave a torn
    asset for the sha256-pinned validator.
    """

    project_root = Path(project_root)
    fig = plt.figure(figsize=(CANVAS_W, CANVAS_H), dpi=200)
    try:
        _draw(fig)
        fig.canvas.draw()
        rgba = cast(FigureCanvasAgg, fig.canvas).buffer_rgba()  # type: ignore[no-untyped-call]
        png = _encode_png_rgb(WIDTH_PX, HEIGHT_PX, bytes(rgba))
    finally:
        plt.close(fig)

    header_ok = png[:8] == b"\x89PNG\r\n\x1a\n" and png[12:16] == b"IHDR"
    if not header_ok:
        raise RuntimeError("graphical abstract encoder produced a non-PNG payload")
    width, height = struct.unpack(">II", png[16:24])
    if (width, height) != (WIDTH_PX, HEIGHT_PX):
        raise RuntimeError(
            "graphical abstract dimensions drifted: "
            f"expected {WIDTH_PX}x{HEIGHT_PX}, encoded {width}x{height}"
        )
    if png[24:29] != bytes((8, 2, 0, 0, 0)):
        raise RuntimeError("graphical abstract must be 8-bit non-interlaced RGB")

    target = project_root / GRAPHICAL_ABSTRACT_RELATIVE
    atomic_write_bytes(target, png)
    return target
