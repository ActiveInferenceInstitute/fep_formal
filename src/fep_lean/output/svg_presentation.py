"""Shared SVG presentation kernel for the atlas and dashboard projections.

The escape/humanize/wrap/text-line helpers were duplicated verbatim across
``formalism_atlas`` and ``formal_kernel_dashboard`` (SC-15); both now import
this single implementation. Escape behavior is byte-identical to the retired
copies (``html.escape(..., quote=True)``); ``wrap`` retains the
ellipsis-terminated final-line truncation.
"""

from __future__ import annotations

import html
from collections.abc import Callable

from fep_lean.output.formalism_presentation import humanize_formalism_identifier

__all__ = [
    "escape_svg_text",
    "humanize_identifier",
    "options_fragment",
    "svg_text_lines",
    "wrap_text",
]


def escape_svg_text(value: object) -> str:
    """Escape ``value`` for use inside SVG/HTML text and attribute contexts."""
    return html.escape(str(value), quote=True)


def humanize_identifier(value: str) -> str:
    """Render a formalism identifier as its presentation-facing label."""
    return humanize_formalism_identifier(value)


def wrap_text(value: str, width: int, *, lines: int | None = 2) -> tuple[str, ...]:
    """Word-wrap ``value`` to ``width`` columns, truncating past ``lines``."""
    words = value.split()
    wrapped: list[str] = []
    current: list[str] = []
    for word in words:
        candidate = " ".join((*current, word))
        if current and len(candidate) > width:
            wrapped.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        wrapped.append(" ".join(current))
    if lines is None or len(wrapped) <= lines:
        return tuple(wrapped)
    retained = wrapped[:lines]
    retained[-1] = retained[-1].rstrip("…") + "…"
    return tuple(retained)


def svg_text_lines(
    lines: tuple[str, ...],
    *,
    x: float,
    y: float,
    css_class: str,
    step: int = 18,
) -> list[str]:
    """Project wrapped lines as SVG ``<text>`` rows at a fixed leading."""
    return [
        f'<text class="{css_class}" x="{x:.1f}" y="{y + index * step:.1f}">'
        f"{escape_svg_text(line)}</text>"
        for index, line in enumerate(lines)
    ]


def options_fragment(
    values: list[str],
    *,
    all_label: str,
    humanize: Callable[[str], str] = humanize_identifier,
) -> str:
    """Build a ``<select>`` option fragment with an 'All' default row."""
    rows = [f'<option value="">All {escape_svg_text(all_label)}</option>']
    rows.extend(
        f'<option value="{escape_svg_text(value)}">'
        f"{escape_svg_text(humanize(value))}</option>"
        for value in values
    )
    return "".join(rows)
