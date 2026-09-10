"""Offline numerical workbench for every typed formal-family witness."""

from __future__ import annotations

import html
import math
from pathlib import Path
from typing import Literal, TypeAlias

from fep_lean.output.formalism_presentation import (
    FormalismPresentation,
    build_formalism_presentation,
)
from fep_lean.output.fsutil import atomic_write_text
from fep_lean.output.svg_presentation import (
    escape_svg_text,
    humanize_identifier,
    options_fragment,
    svg_text_lines,
    wrap_text,
)
from fep_lean.verification.numerical_witnesses import NumericalWitness, Scalar

DASHBOARD_SVG = Path("docs/formal-kernel-dashboard.svg")
DASHBOARD_HTML = Path("docs/formal-kernel-dashboard.html")

FormalKernelDashboard: TypeAlias = FormalismPresentation
_MobilePlotGroup: TypeAlias = tuple[int, int, tuple[NumericalWitness, ...]]

_SERIES_COLORS = (
    "#0f766e",
    "#2563eb",
    "#7c3aed",
    "#d97706",
    "#be123c",
    "#0891b2",
)
_DASHBOARD_READER_TITLE = "Formalism numerical witness workbench"
_COMPACT_BOUNDARY_BADGE = "NON-PROOF WITNESS · explanatory typed checks only"
_MOBILE_PLOTS_PER_GROUP = 3


def build_formal_kernel_dashboard(project_root: Path) -> FormalKernelDashboard:
    """Return the same immutable presentation join used by the atlas."""
    return build_formalism_presentation(Path(project_root))




def _text(value: object) -> str:
    return html.escape(str(value), quote=False)


def _scalar_text(value: Scalar) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    return repr(value)




def _formal_alignment_explanation(witness: NumericalWitness) -> str:
    if witness.formal_alignment == "theorem_instance":
        return (
            "The evaluated witness is aligned as a finite instance of its named "
            "theorem mirrors."
        )
    return (
        "The witness illustrates the same structural pattern but does not discharge "
        "all formal premises."
    )


def _check_summary(witness: NumericalWitness) -> str:
    """Return an accessible exact summary of every typed numerical check."""
    return "; ".join(
        f"{check.id}: {check.relation}({check.lhs!r}, {check.rhs!r}), "
        f"tolerance {check.tolerance!r}, residual {check.residual!r}, "
        f"{'accepted' if check.accepted else 'rejected'}"
        for check in witness.checks
    )


def _maximum_check_residual(witness: NumericalWitness) -> float:
    """Return the largest relation-aware residual for a nonempty check set."""
    return max(check.residual for check in witness.checks)


def _compact_number(value: float) -> str:
    """Format a summary value compactly while exact values remain in tables."""
    if value == 0:
        return "0"
    magnitude = abs(value)
    if magnitude < 1e-3 or magnitude >= 1e4:
        return f"{value:.2e}"
    return f"{value:.4g}"






def _numeric(value: Scalar) -> float | None:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        number = float(value)
        return number if math.isfinite(number) else None
    return None


def _plot_coordinates(
    witness: NumericalWitness,
) -> tuple[
    tuple[Scalar, ...],
    tuple[float, ...],
    tuple[tuple[str, tuple[float, ...]], ...],
]:
    indexes = {column.key: index for index, column in enumerate(witness.columns)}
    raw_x = tuple(row.values[indexes[witness.plot.x_key]] for row in witness.rows)
    numeric_x = tuple(_numeric(value) for value in raw_x)
    if all(value is not None for value in numeric_x):
        x_values = tuple(float(value) for value in numeric_x if value is not None)
    else:
        x_values = tuple(float(index) for index in range(len(raw_x)))
    series: list[tuple[str, tuple[float, ...]]] = []
    for key in witness.plot.y_keys:
        values = tuple(_numeric(row.values[indexes[key]]) for row in witness.rows)
        if all(value is not None for value in values):
            series.append(
                (key, tuple(float(value) for value in values if value is not None))
            )
    return raw_x, x_values, tuple(series)


def _plot_scalar_text(value: Scalar) -> str:
    if isinstance(value, str):
        return value
    return _scalar_text(value)


def _x_domain_caption(witness: NumericalWitness, raw_x: tuple[Scalar, ...]) -> str:
    x_column = next(
        column for column in witness.columns if column.key == witness.plot.x_key
    )
    values = tuple(_plot_scalar_text(value) for value in raw_x)
    if len(values) <= 5:
        domain = " · ".join(values)
    else:
        domain = f"{values[0]} … {values[-1]} · {len(values)} rows"
    return f"{x_column.label}: {domain}"


def _compact_category_label(value: Scalar) -> str:
    """Keep SVG category keys concise while exact values remain in tables."""
    label = _plot_scalar_text(value)
    words = label.split()
    if len(label) <= 18 or len(words) <= 2:
        return label
    return " ".join(words[-2:])


def _scaled(
    value: float, minimum: float, maximum: float, start: float, span: float
) -> float:
    if math.isclose(minimum, maximum):
        return start + span / 2
    return start + (value - minimum) * span / (maximum - minimum)


def _coincident_marker_svg(
    *,
    css_class: str,
    series_key: str,
    color: str,
    shape: Literal["ring", "diamond"],
    center_x: float,
    center_y: float,
    point_index: int | None,
) -> str:
    """Render a centered identity glyph without perturbing its data coordinate."""
    point = f' data-point-index="{point_index}"' if point_index is not None else ""
    common = (
        f'class="{css_class}" data-series-key="{escape_svg_text(series_key)}" '
        f'data-marker-shape="{shape}" data-center-x="{center_x:.2f}" '
        f'data-center-y="{center_y:.2f}" data-visual-offset="0"{point}'
    )
    title = f"<title>{escape_svg_text(series_key)} · identical shared-rail value</title>"
    if shape == "ring":
        return (
            f'<circle {common} cx="{center_x:.2f}" cy="{center_y:.2f}" r="6" '
            f'fill="white" stroke="{color}" stroke-width="3">{title}</circle>'
        )
    size = 7.0
    return (
        f'<rect {common} x="{center_x - size / 2:.2f}" '
        f'y="{center_y - size / 2:.2f}" width="{size:.1f}" height="{size:.1f}" '
        f'fill="{color}" stroke="white" stroke-width="1.2" '
        f'transform="rotate(45 {center_x:.2f} {center_y:.2f})">{title}</rect>'
    )


def _plot_elements(
    witness: NumericalWitness,
    *,
    x: int,
    y: int,
    width: int,
    native_plot_height: int,
    stacked_legend: bool,
) -> tuple[list[str], float]:
    raw_x, x_values, series = _plot_coordinates(witness)
    if not x_values or not series:
        return (
            [
                (
                    f'<text class="plot-note" x="{x + 8}" '
                    f'y="{y + native_plot_height // 2}">'
                    "No plottable numeric series</text>"
                )
            ],
            float(y + native_plot_height),
        )
    x_min, x_max = min(x_values), max(x_values)
    all_y = tuple(value for _, values in series for value in values)
    y_min, y_max = min(all_y), max(all_y)
    zero_baseline = witness.plot.kind == "bar"
    if zero_baseline:
        y_min = min(0.0, y_min)
        y_max = max(0.0, y_max)
    if math.isclose(y_min, y_max) and zero_baseline:
        y_max = y_min + 1.0
    elif math.isclose(y_min, y_max):
        padding = max(abs(y_min) * 0.1, 1.0)
        y_min -= padding
        y_max += padding
    columns = {column.key: column for column in witness.columns}
    x_label = columns[witness.plot.x_key].label
    y_labels = tuple(columns[key].label for key, _values in series)
    x_unit = (
        "dimensionless"
        if all(
            isinstance(value, (int, float)) and not isinstance(value, bool)
            for value in raw_x
        )
        else "categorical"
    )
    y_unit = "dimensionless"
    y_axis = f"y · {' / '.join(y_labels)} · unit: {y_unit}"
    x_axis = f"x · {x_label} · unit: {x_unit}"
    axis_text_width = max(28, int((width - 32) / 8))
    y_axis_lines = wrap_text(y_axis, axis_text_width, lines=None)
    x_axis_lines = wrap_text(x_axis, axis_text_width, lines=None)
    x_domain = _x_domain_caption(witness, raw_x)
    domain_lines = wrap_text(x_domain, axis_text_width, lines=None)
    categorical = x_unit == "categorical"
    category_labels = tuple(f"C{index + 1}" for index in range(len(raw_x)))
    category_key_columns = 1 if stacked_legend else 2
    legend_layout = "stacked" if stacked_legend else "direct"
    legend_width = 0 if stacked_legend else max(162, int(width * 0.34))
    scale_gutter = 82
    legend_gap = 14 if not stacked_legend else 0
    axis_line_step = 19
    annotation_line_step = 18
    category_key_step = 21
    plot_left = x + 8 + scale_gutter
    plot_top = y + len(y_axis_lines) * axis_line_step + 8
    plot_width = width - 16 - scale_gutter - legend_width - legend_gap
    plot_bottom = plot_top + native_plot_height
    x_axis_left = x + 8 if categorical else plot_left
    category_tick_y = plot_bottom + 15
    x_axis_y = plot_bottom + (33 if categorical else 22)
    domain_y = x_axis_y + len(x_axis_lines) * annotation_line_step + 2
    category_key_y = domain_y + 21
    if categorical:
        category_rows = math.ceil(len(raw_x) / category_key_columns)
        annotation_bottom = (
            category_key_y + (category_rows - 1) * category_key_step + 15
        )
    else:
        annotation_bottom = (
            domain_y + (len(domain_lines) - 1) * annotation_line_step + 16
        )
    legend_limit = max(
        24 if stacked_legend else 10,
        int(((width - 42) if stacked_legend else (legend_width - 18)) / 7),
    )
    legend_lines = tuple(
        wrap_text(columns[key].label, legend_limit, lines=None) for key, _values in series
    )
    coincident_with: list[str | None] = []
    for series_index, (_key, values) in enumerate(series):
        match = next(
            (
                prior_key
                for prior_key, prior_values in series[:series_index]
                if all(
                    math.isclose(left, right, rel_tol=1e-12, abs_tol=1e-15)
                    for left, right in zip(values, prior_values, strict=True)
                )
            ),
            None,
        )
        coincident_with.append(match)
    coincident_roots = {
        prior_key for prior_key in coincident_with if prior_key is not None
    }
    coincident_groups = {
        key: [key] for key, _values in series if key in coincident_roots
    }
    for (key, _values), root in zip(series, coincident_with, strict=True):
        if root is not None:
            coincident_groups[root].append(key)
    coincident_root_by_key = {
        key: root for root, keys in coincident_groups.items() for key in keys
    }
    has_exact_zero = zero_baseline and any(
        value == 0.0 for _key, values in series for value in values
    )
    lines = [
        (
            f'<g class="plot" data-plot-for="{escape_svg_text(witness.id)}" '
            f'data-zero-baseline="{str(zero_baseline).lower()}" '
            f'data-y-min="{y_min!r}" data-y-max="{y_max!r}" '
            f'data-x-quantity="{escape_svg_text(x_label)}" data-x-unit="{x_unit}" '
            f'data-y-quantities="{escape_svg_text(" | ".join(y_labels))}" '
            f'data-y-unit="{y_unit}" data-legend-layout="{legend_layout}" '
            f'data-native-plot-height="{native_plot_height}" '
            f'data-category-count="{len(raw_x) if categorical else 0}" '
            f'data-category-key-columns="{category_key_columns if categorical else 0}" '
            f'data-annotation-band-bottom="{annotation_bottom:.2f}">'
        ),
        (
            f'<text class="axis-label axis-y-label" x="{x + 8}" y="{y + 13}">'
            + "".join(
                f'<tspan x="{x + 8}" y="{y + 13 + index * axis_line_step}">{escape_svg_text(line)}</tspan>'
                for index, line in enumerate(y_axis_lines)
            )
            + "</text>"
        ),
        (
            f'<line class="axis" x1="{plot_left}" y1="{plot_top + native_plot_height}" '
            f'x2="{plot_left + plot_width}" y2="{plot_top + native_plot_height}"/>'
        ),
        (
            f'<line class="axis" x1="{plot_left}" y1="{plot_top}" '
            f'x2="{plot_left}" y2="{plot_top + native_plot_height}"/>'
        ),
    ]
    minimum_class = "scale-zero" if zero_baseline else "scale-minimum"
    minimum_label = "0" if zero_baseline and y_min == 0.0 else f"{y_min:.3g}"
    lines.extend(
        [
            (
                f'<text class="{minimum_class}" x="{x + 8}" '
                f'y="{plot_top + native_plot_height - 5}">y min {minimum_label}</text>'
            ),
            (
                f'<text class="scale-maximum" x="{x + 8}" '
                f'y="{plot_top + 13}">y max {y_max:.3g}</text>'
            ),
        ]
    )
    for series_index, (key, values) in enumerate(series):
        color = _SERIES_COLORS[series_index % len(_SERIES_COLORS)]
        coincident_root = coincident_root_by_key.get(key)
        overlap_role = "coincident-member" if coincident_root else "independent"
        points = tuple(
            (
                _scaled(value_x, x_min, x_max, plot_left, plot_width),
                plot_top
                + native_plot_height
                - _scaled(value_y, y_min, y_max, 0, native_plot_height),
            )
            for value_x, value_y in zip(x_values, values, strict=True)
        )
        if witness.plot.kind == "bar":
            group_width = plot_width / max(1, len(x_values))
            bar_width = max(2.0, group_width * 0.7 / len(series))
            baseline = min(
                native_plot_height,
                max(
                    0.0,
                    _scaled(0.0, y_min, y_max, 0, native_plot_height),
                ),
            )
            baseline_y = plot_top + native_plot_height - baseline
            for point_index, (_, point_y) in enumerate(points):
                value = values[point_index]
                is_zero = value == 0.0
                center_x = plot_left + (point_index + 0.5) * group_width
                bar_x = (
                    center_x - len(series) * bar_width / 2 + series_index * bar_width
                )
                lines.append(
                    f'<rect class="plot-bar" data-category-index="{point_index}" '
                    f'data-series-key="{escape_svg_text(key)}" data-value="{value!r}" '
                    f'data-zero-value="{str(is_zero).lower()}" '
                    f'x="{bar_x:.2f}" y="{min(point_y, baseline_y):.2f}" '
                    f'width="{bar_width:.2f}" height="{max(1.0, abs(baseline_y - point_y)):.2f}" '
                    f'fill="{color}" opacity="0.82"><title>{escape_svg_text(key)}</title></rect>'
                )
                if is_zero:
                    marker_x = bar_x + bar_width / 2
                    lines.append(
                        f'<circle class="zero-value-marker" '
                        f'data-category-index="{point_index}" '
                        f'data-series-key="{escape_svg_text(key)}" '
                        f'cx="{marker_x:.2f}" cy="{baseline_y:.2f}" r="4" '
                        f'fill="white" stroke="{color}" stroke-width="2">'
                        f"<title>{escape_svg_text(key)}: exact zero, not missing</title></circle>"
                    )
        else:
            if witness.plot.kind == "line":
                path = " ".join(
                    f"{'M' if index == 0 else 'L'} {point_x:.2f} {point_y:.2f}"
                    for index, (point_x, point_y) in enumerate(points)
                )
                if coincident_root is None:
                    lines.append(
                        f'<path data-series-key="{escape_svg_text(key)}" '
                        f'data-overlap-role="{overlap_role}" d="{path}" '
                        f'fill="none" stroke="{color}" stroke-width="2.8" '
                        'vector-effect="non-scaling-stroke"/>'
                    )
                elif key == coincident_root:
                    shared_keys = " | ".join(coincident_groups[coincident_root])
                    lines.append(
                        f'<path class="coincident-value-rail" '
                        f'data-series-keys="{escape_svg_text(shared_keys)}" '
                        'data-visual-offset="0" d="'
                        f'{path}" fill="none" stroke="#334155" stroke-width="3.4" '
                        'stroke-linecap="round" vector-effect="non-scaling-stroke"/>'
                    )
            for point_index, (point_x, point_y) in enumerate(points):
                if coincident_root is not None:
                    member_index = coincident_groups[coincident_root].index(key)
                    lines.append(
                        _coincident_marker_svg(
                            css_class="coincident-series-marker",
                            series_key=key,
                            color=color,
                            shape="ring" if member_index == 0 else "diamond",
                            center_x=point_x,
                            center_y=point_y,
                            point_index=point_index,
                        )
                    )
                else:
                    lines.append(
                        f'<circle data-series-key="{escape_svg_text(key)}" '
                        f'data-overlap-role="{overlap_role}" cx="{point_x:.2f}" '
                        f'cy="{point_y:.2f}" r="3.4" '
                        f'fill="{color}"><title>{escape_svg_text(key)}</title></circle>'
                    )
    if categorical:
        group_width = plot_width / max(1, len(x_values))
        for category_index, (category_label, category_value) in enumerate(
            zip(category_labels, raw_x, strict=True)
        ):
            center_x = plot_left + (category_index + 0.5) * group_width
            lines.append(
                f'<text class="category-tick" data-category-index="{category_index}" '
                f'data-category-value="{escape_svg_text(_plot_scalar_text(category_value))}" '
                f'x="{center_x:.2f}" y="{category_tick_y:.2f}" '
                f'text-anchor="middle">{category_label}</text>'
            )
    x_axis_tspans = "".join(
        f'<tspan x="{x_axis_left}" y="{x_axis_y + line_index * annotation_line_step}">{escape_svg_text(line)}</tspan>'
        for line_index, line in enumerate(x_axis_lines)
    )
    lines.append(
        f'<text class="axis-label axis-x-label" x="{x_axis_left}" y="{x_axis_y}">'
        f"{x_axis_tspans}</text>"
    )
    if categorical:
        lines.append(
            f'<text class="x-domain" data-x-domain="{escape_svg_text(x_domain)}" '
            f'x="{x + 8}" y="{domain_y}">Category key · full labels in exact HTML table</text>'
        )
        key_width = (width - 16) / category_key_columns
        for category_index, (category_label, category_value) in enumerate(
            zip(category_labels, raw_x, strict=True)
        ):
            key_column = category_index % category_key_columns
            key_row = category_index // category_key_columns
            key_x = x + 8 + key_column * key_width
            key_y = category_key_y + key_row * category_key_step
            compact_label = _compact_category_label(category_value)
            lines.append(
                f'<text class="category-key-item" data-category-index="{category_index}" '
                f'data-category-label="{category_label}" '
                f'data-category-value="{escape_svg_text(_plot_scalar_text(category_value))}" '
                f'x="{key_x:.2f}" y="{key_y:.2f}">{category_label} · '
                f"{escape_svg_text(compact_label)}<title>{escape_svg_text(_plot_scalar_text(category_value))}</title></text>"
            )
    else:
        domain_tspans = "".join(
            f'<tspan x="{plot_left}" y="{domain_y + line_index * annotation_line_step:.2f}">'
            f"{escape_svg_text(line)}</tspan>"
            for line_index, line in enumerate(domain_lines)
        )
        lines.append(
            f'<text class="x-domain" data-x-domain="{escape_svg_text(x_domain)}" '
            f'x="{plot_left}" y="{domain_y}">{domain_tspans}</text>'
        )
    if stacked_legend:
        legend_x = x + 16
        legend_y = annotation_bottom + 12
    else:
        legend_x = plot_left + plot_width + 18
        legend_y = plot_top + 13
    for series_index, ((key, _values), wrapped_label) in enumerate(
        zip(series, legend_lines, strict=True)
    ):
        color = _SERIES_COLORS[series_index % len(_SERIES_COLORS)]
        coincident_root = coincident_root_by_key.get(key)
        overlap_role = "coincident-member" if coincident_root else "independent"
        tspans = "".join(
            f'<tspan x="{legend_x + 20:.2f}" y="{legend_y + line_index * annotation_line_step:.2f}">'
            f"{escape_svg_text(line)}</tspan>"
            for line_index, line in enumerate(wrapped_label)
        )
        if witness.plot.kind == "line":
            if coincident_root is not None:
                member_index = coincident_groups[coincident_root].index(key)
                lines.append(
                    _coincident_marker_svg(
                        css_class="coincident-legend-marker",
                        series_key=key,
                        color=color,
                        shape="ring" if member_index == 0 else "diamond",
                        center_x=legend_x + 5,
                        center_y=legend_y - 4,
                        point_index=None,
                    )
                )
            else:
                lines.append(
                    f'<line class="legend-swatch" data-series-key="{escape_svg_text(key)}" '
                    f'data-overlap-role="{overlap_role}" x1="{legend_x}" '
                    f'y1="{legend_y - 4}" x2="{legend_x + 10}" y2="{legend_y - 4}" '
                    f'stroke="{color}" stroke-width="2.8"/>'
                )
        else:
            lines.append(
                f'<circle cx="{legend_x + 5}" cy="{legend_y - 4}" r="4" '
                f'fill="{color}"/>'
            )
        lines.append(
            f'<text class="legend" data-series-key="{escape_svg_text(key)}" '
            f'x="{legend_x + 20:.2f}" y="{legend_y}">'
            f"<title>{escape_svg_text(key)}</title>{tspans}</text>"
        )
        legend_y += len(wrapped_label) * annotation_line_step + 9
    if witness.plot.kind == "line" and coincident_roots:
        overlap_lines = wrap_text(
            "Identical values · shared rail + ring/diamond identities · no value offset",
            legend_limit,
            lines=None,
        )
        tspans = "".join(
            f'<tspan x="{legend_x:.2f}" y="{legend_y + index * annotation_line_step:.2f}">'
            f"{escape_svg_text(line)}</tspan>"
            for index, line in enumerate(overlap_lines)
        )
        lines.append(
            f'<text class="coincident-series-key" x="{legend_x:.2f}" '
            f'y="{legend_y}">{tspans}</text>'
        )
        legend_y += len(overlap_lines) * annotation_line_step + 9
    if has_exact_zero:
        zero_key_lines = wrap_text(
            "Hollow marker per series · exact zero, not missing",
            legend_limit,
            lines=None,
        )
        tspans = "".join(
            f'<tspan x="{legend_x + 20:.2f}" y="{legend_y + index * annotation_line_step:.2f}">'
            f"{escape_svg_text(line)}</tspan>"
            for index, line in enumerate(zero_key_lines)
        )
        lines.extend(
            [
                (
                    f'<circle class="zero-value-key-marker" cx="{legend_x + 5}" '
                    f'cy="{legend_y - 4}" r="4" fill="white" stroke="#475569" '
                    'stroke-width="2"/>'
                ),
                (
                    f'<text class="exact-zero-key" x="{legend_x + 20:.2f}" '
                    f'y="{legend_y}">{tspans}</text>'
                ),
            ]
        )
        legend_y += len(zero_key_lines) * annotation_line_step + 9
    lines.append("</g>")
    return lines, max(annotation_bottom, legend_y - 7)


def _render_formal_kernel_dashboard_desktop_svg(
    dashboard: FormalKernelDashboard, *, full_boundary: bool
) -> str:
    """Render the wide dashboard with either full or compact evidence context."""
    columns = 3
    card_width = 510
    gap_x = 18
    gap_y = 12
    left = 17
    top = 186 if full_boundary else 154
    rows = math.ceil(len(dashboard.witnesses) / columns)
    relative_plot_bottoms = tuple(
        _plot_elements(
            witness,
            x=0,
            y=148,
            width=card_width - 24,
            native_plot_height=145,
            stacked_legend=False,
        )[1]
        for witness in dashboard.witnesses
    )
    witness_card_heights = tuple(
        max(460, math.ceil(plot_bottom) + 60) for plot_bottom in relative_plot_bottoms
    )
    row_heights = tuple(
        max(witness_card_heights[index : index + columns])
        for index in range(0, len(witness_card_heights), columns)
    )
    row_tops: list[int] = []
    next_row_top = top
    for row_height in row_heights:
        row_tops.append(next_row_top)
        next_row_top += row_height + gap_y
    width = 1600
    height = top + sum(row_heights) + max(0, rows - 1) * gap_y + 92
    lines = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" class="dashboard-svg" '
            f'data-column-count="{columns}" '
            'role="img" aria-labelledby="dashboard-title dashboard-description">'
        ),
        f'<title id="dashboard-title">{_DASHBOARD_READER_TITLE}</title>',
        (
            '<desc id="dashboard-description">All typed deterministic numerical '
            "witnesses are plotted from their declared schemas with residual, "
            "tolerance, theorem-mirror, unit, and boundary summaries. The visible "
            "boundary label identifies these diagnostics as non-proof evidence.</desc>"
        ),
        """<style>
            .dashboard-svg .background{fill:#f8fafc}.dashboard-svg .title{fill:#0f172a;font:800 34px system-ui,sans-serif}
            .dashboard-svg .subtitle{fill:#475569;font:500 16px system-ui,sans-serif}.dashboard-svg .banner{fill:#fff7ed;stroke:#fb923c;stroke-width:1.5}
            .dashboard-svg .banner-label{fill:#9a3412;font:800 14px system-ui,sans-serif}.dashboard-svg .banner-line{fill:#7c2d12;font:650 13px system-ui,sans-serif}.dashboard-svg .card{fill:#fff;stroke:#cbd5e1;stroke-width:1.4}
            .dashboard-svg .card-title{fill:#0f172a;font:800 19px system-ui,sans-serif}.dashboard-svg .family{fill:#475569;font:650 15px system-ui,sans-serif}
            .dashboard-svg .metric{fill:#334155;font:700 15px ui-monospace,monospace}.dashboard-svg .check-passed{fill:#047857;font:800 14px system-ui,sans-serif}
            .dashboard-svg .check-failed{fill:#be123c;font:800 14px system-ui,sans-serif}.dashboard-svg .non-proof{fill:#9a3412;font:800 14px system-ui,sans-serif}.dashboard-svg .axis{stroke:#94a3b8;stroke-width:1}
            .dashboard-svg .axis-label{fill:#334155;font:750 16px system-ui,sans-serif}.dashboard-svg .legend,.dashboard-svg .plot-note,.dashboard-svg .x-domain,.dashboard-svg .scale-zero,.dashboard-svg .scale-minimum,.dashboard-svg .scale-maximum{fill:#334155;font:650 15px system-ui,sans-serif}.dashboard-svg .exact-zero-key,.dashboard-svg .coincident-series-key{fill:#334155;font:700 14px system-ui,sans-serif}.dashboard-svg .category-tick{fill:#334155;font:800 15px system-ui,sans-serif}.dashboard-svg .category-key-item{fill:#334155;font:700 15px system-ui,sans-serif}.dashboard-svg .card-footer-rule{stroke:#e2e8f0;stroke-width:1}.dashboard-svg .alignment{fill:#334155;font:650 14px system-ui,sans-serif}
            .dashboard-svg .footer{fill:#475569;font:600 14px system-ui,sans-serif}
        </style>""",
        f'<rect class="background" width="{width}" height="{height}"/>',
        f'<text class="title" x="40" y="52">{_DASHBOARD_READER_TITLE}</text>',
        (
            f'<text class="subtitle" x="40" y="81">{len(dashboard.witnesses)} typed witnesses · '
            f"{len({witness.family for witness in dashboard.witnesses})} formal families · "
            "exact evaluated schemas</text>"
        ),
    ]
    if full_boundary:
        lines.extend(
            [
                '<rect class="banner" x="40" y="101" width="1520" height="68" rx="9"/>',
                '<text class="banner-label" x="58" y="123">Evidence boundary</text>',
                *svg_text_lines(
                    wrap_text(dashboard.numerical_evidence_boundary, 132, lines=2),
                    x=58,
                    y=143,
                    css_class="banner-line",
                    step=16,
                ),
            ]
        )
    else:
        lines.extend(
            [
                '<rect class="banner" x="40" y="101" width="1520" height="36" rx="18"/>',
                (
                    '<text class="banner-label" x="58" y="124">'
                    f"{_COMPACT_BOUNDARY_BADGE}</text>"
                ),
            ]
        )
    lines.append('<g role="list" aria-label="Typed numerical witnesses">')
    for index, witness in enumerate(dashboard.witnesses):
        column = index % columns
        row = index // columns
        x = left + column * (card_width + gap_x)
        y = row_tops[row]
        card_height = row_heights[row]
        footer_top = y + card_height - 54
        status = "accepted" if witness.accepted else "rejected"
        check_class = "check-passed" if witness.accepted else "check-failed"
        check_label = (
            "TYPED CHECKS PASSED" if witness.accepted else "TYPED CHECKS FAILED"
        )
        lines.extend(
            [
                (
                    f'<g class="witness-summary" data-witness-summary="{escape_svg_text(witness.id)}" '
                    f'data-witness-id="{escape_svg_text(witness.id)}" data-family="{escape_svg_text(witness.family)}" '
                    f'data-witness-status="{status}" data-check-count="{len(witness.checks)}" '
                    f'data-max-check-residual="{_maximum_check_residual(witness)!r}" '
                    f'data-formal-alignment="{escape_svg_text(witness.formal_alignment)}" '
                    f'data-boundary-observed="{str(witness.boundary_observed).lower()}" '
                    f'data-footer-band-top="{footer_top}" '
                    f'role="listitem" tabindex="0" '
                    f'aria-label="{escape_svg_text(witness.title)}, {status}, '
                    f'{escape_svg_text(humanize_identifier(witness.formal_alignment))}">'
                ),
                f"<title>{escape_svg_text(witness.title)} · {witness.id} · {witness.family}</title>",
                (
                    f"<desc>{escape_svg_text(witness.invariant)} Boundary: "
                    f"{escape_svg_text(witness.boundary_behavior)} Theorem mirrors: "
                    f"{escape_svg_text(', '.join(witness.theorem_mirrors))} Formal alignment: "
                    f"{escape_svg_text(witness.formal_alignment)}. Typed checks: "
                    f"{escape_svg_text(_check_summary(witness))}.</desc>"
                ),
                f'<rect class="card" x="{x}" y="{y}" width="{card_width}" height="{card_height}" rx="13"/>',
            ]
        )
        lines.extend(
            f'<text class="card-title" x="{x + 18}" y="{y + 73 + line_index * 21}">{escape_svg_text(line)}</text>'
            for line_index, line in enumerate(wrap_text(witness.title, 46))
        )
        lines.extend(
            [
                f'<text class="family" x="{x + 18}" y="{y + 115}">{escape_svg_text(witness.family)} · {len(witness.rows)} rows · {witness.plot.kind}</text>',
                (
                    f'<text class="metric" x="{x + 18}" y="{y + 135}">'
                    f"{len(witness.checks)} typed checks · max residual "
                    f"{_compact_number(_maximum_check_residual(witness))}</text>"
                ),
                (
                    f'<text class="{check_class}" x="{x + 18}" y="{y + 25}">'
                    f"{check_label}</text>"
                ),
                (
                    f'<text class="non-proof" x="{x + 18}" y="{y + 45}">'
                    "NON-PROOF WITNESS</text>"
                ),
                (
                    f'<line class="card-footer-rule" x1="{x + 18}" y1="{footer_top}" '
                    f'x2="{x + card_width - 18}" y2="{footer_top}"/>'
                ),
                (
                    f'<text class="alignment" x="{x + 18}" y="{footer_top + 18}">Formal alignment · '
                    f"{escape_svg_text(humanize_identifier(witness.formal_alignment))}</text>"
                ),
                (
                    f'<text class="alignment" x="{x + 18}" y="{footer_top + 36}">Boundary observed · '
                    f"{'yes' if witness.boundary_observed else 'no'} · "
                    f"{len(witness.theorem_mirrors)} theorem mirrors</text>"
                ),
            ]
        )
        plot_lines, _plot_bottom = _plot_elements(
            witness,
            x=x + 12,
            y=y + 148,
            width=card_width - 24,
            native_plot_height=145,
            stacked_legend=False,
        )
        lines.extend(plot_lines)
        lines.append("</g>")
    lines.extend(
        [
            "</g>",
            (
                f'<text class="footer" x="40" y="{height - 30}">Exact tables, theorem '
                "mirrors, parameters, typed checks, and boundary statements "
                "are preserved in the companion accessible HTML workbench.</text>"
            ),
            "</svg>",
        ]
    )
    return "\n".join(lines) + "\n"


def render_formal_kernel_dashboard_svg(dashboard: FormalKernelDashboard) -> str:
    """Render every typed witness with a complete visible evidence warning."""
    return _render_formal_kernel_dashboard_desktop_svg(dashboard, full_boundary=True)


def _render_formal_kernel_dashboard_mobile_svg(
    dashboard: FormalKernelDashboard,
    *,
    witnesses: tuple[NumericalWitness, ...],
    group_index: int,
    group_count: int,
    start_index: int,
) -> str:
    """Render one bounded group of witness plots in a narrow vertical flow."""
    width = 390
    margin = 10
    card_width = width - 2 * margin
    card_gap = 10
    top = 144
    card_layouts: list[tuple[int, int, int, list[str]]] = []
    next_y = top
    for witness in witnesses:
        plot_lines, plot_bottom = _plot_elements(
            witness,
            x=margin + 6,
            y=next_y + 182,
            width=card_width - 12,
            native_plot_height=170,
            stacked_legend=True,
        )
        boundary_y = math.ceil(plot_bottom) + 20
        card_height = boundary_y - next_y + 18
        card_layouts.append((next_y, card_height, boundary_y, plot_lines))
        next_y += card_height + card_gap
    height = next_y + 60
    lines = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
            f'class="mobile-dashboard-svg" data-layout="mobile" '
            f'data-mobile-group="{group_index}" '
            f'data-mobile-group-count="{group_count}" '
            f'data-witness-start="{start_index}" '
            f'data-witness-end="{start_index + len(witnesses) - 1}" role="img" '
            f'aria-labelledby="mobile-dashboard-title-{group_index} '
            f'mobile-dashboard-description-{group_index}">'
        ),
        (
            f'<title id="mobile-dashboard-title-{group_index}">'
            f"{_DASHBOARD_READER_TITLE} · plot group {group_index} of {group_count}</title>"
        ),
        (
            f'<desc id="mobile-dashboard-description-{group_index}">This bounded '
            f"mobile group contains witnesses {start_index} through "
            f"{start_index + len(witnesses) - 1} of {len(dashboard.witnesses)}, "
            "each once in a readable vertical column with native-height plots and "
            "a compact non-proof boundary badge.</desc>"
        ),
        """<style>
            .mobile-dashboard-svg .mobile-bg{fill:#f8fafc}.mobile-dashboard-svg .mobile-title{fill:#0f172a;font:800 22px system-ui,sans-serif}
            .mobile-dashboard-svg .mobile-subtitle{fill:#475569;font:650 14px system-ui,sans-serif}.mobile-dashboard-svg .mobile-banner{fill:#fff7ed;stroke:#fb923c;stroke-width:1.5}
            .mobile-dashboard-svg .mobile-banner-label{fill:#9a3412;font:800 13px system-ui,sans-serif}
            .mobile-dashboard-svg .mobile-card{fill:#fff;stroke:#cbd5e1;stroke-width:1.4}.mobile-dashboard-svg .mobile-card-title{fill:#0f172a;font:800 17px system-ui,sans-serif}
            .mobile-dashboard-svg .mobile-family{fill:#475569;font:650 14px system-ui,sans-serif}.mobile-dashboard-svg .mobile-metric{fill:#334155;font:700 14px ui-monospace,monospace}
            .mobile-dashboard-svg .mobile-check-passed{fill:#047857;font:800 14px system-ui,sans-serif}.mobile-dashboard-svg .mobile-check-failed{fill:#be123c;font:800 14px system-ui,sans-serif}
            .mobile-dashboard-svg .mobile-non-proof{fill:#9a3412;font:800 14px system-ui,sans-serif}.mobile-dashboard-svg .axis{stroke:#94a3b8;stroke-width:1}
            .mobile-dashboard-svg .axis-label{fill:#334155;font:750 15px system-ui,sans-serif}.mobile-dashboard-svg .legend,.mobile-dashboard-svg .plot-note,.mobile-dashboard-svg .x-domain,.mobile-dashboard-svg .scale-zero,.mobile-dashboard-svg .scale-minimum,.mobile-dashboard-svg .scale-maximum{fill:#334155;font:650 14px system-ui,sans-serif}.mobile-dashboard-svg .exact-zero-key,.mobile-dashboard-svg .coincident-series-key{fill:#334155;font:700 14px system-ui,sans-serif}.mobile-dashboard-svg .category-tick{fill:#334155;font:800 15px system-ui,sans-serif}.mobile-dashboard-svg .category-key-item{fill:#334155;font:700 15px system-ui,sans-serif}
            .mobile-dashboard-svg .mobile-alignment{fill:#334155;font:700 13px system-ui,sans-serif}.mobile-dashboard-svg .mobile-boundary{fill:#334155;font:650 13px system-ui,sans-serif}.mobile-dashboard-svg .mobile-footer{fill:#475569;font:650 13px system-ui,sans-serif}
        </style>""",
        f'<rect class="mobile-bg" width="{width}" height="{height}"/>',
        (
            f'<text class="mobile-title" data-reader-title="{_DASHBOARD_READER_TITLE}" '
            'x="10" y="29"><tspan x="10" y="29">Formalism numerical</tspan>'
            '<tspan x="10" y="52">witness workbench</tspan></text>'
        ),
        (
            f'<text class="mobile-subtitle" x="10" y="76">Plots {start_index}–'
            f"{start_index + len(witnesses) - 1} of {len(dashboard.witnesses)} · "
            f"group {group_index} of {group_count}</text>"
        ),
        '<rect class="mobile-banner" x="10" y="92" width="370" height="36" rx="18"/>',
        f'<text class="mobile-banner-label" x="22" y="115">{_COMPACT_BOUNDARY_BADGE}</text>',
    ]
    lines.append(
        f'<g role="list" aria-label="Typed numerical witnesses, group {group_index} '
        f'of {group_count}">'
    )
    for witness, (y, card_height, boundary_y, plot_lines) in zip(
        witnesses, card_layouts, strict=True
    ):
        status = "accepted" if witness.accepted else "rejected"
        check_class = (
            "mobile-check-passed" if witness.accepted else "mobile-check-failed"
        )
        check_label = (
            "TYPED CHECKS PASSED" if witness.accepted else "TYPED CHECKS FAILED"
        )
        lines.extend(
            [
                (
                    f'<g data-mobile-witness-summary="{escape_svg_text(witness.id)}" '
                    f'data-family="{escape_svg_text(witness.family)}" '
                    f'data-formal-alignment="{escape_svg_text(witness.formal_alignment)}" '
                    f'role="listitem" aria-label="{escape_svg_text(witness.title)}, {status}, '
                    f'{escape_svg_text(humanize_identifier(witness.formal_alignment))}">'
                ),
                f"<title>{escape_svg_text(witness.title)} · {witness.id}</title>",
                f"<desc>Typed checks: {escape_svg_text(_check_summary(witness))}.</desc>",
                (
                    f'<rect class="mobile-card" x="{margin}" y="{y}" '
                    f'width="{card_width}" height="{card_height}" rx="11"/>'
                ),
            ]
        )
        lines.extend(
            f'<text class="mobile-card-title" x="{margin + 12}" '
            f'y="{y + 70 + line_index * 17}">{escape_svg_text(line)}</text>'
            for line_index, line in enumerate(wrap_text(witness.title, 39, lines=3))
        )
        lines.extend(
            svg_text_lines(
                wrap_text(witness.family, 52, lines=2),
                x=margin + 12,
                y=y + 122,
                css_class="mobile-family",
                step=15,
            )
        )
        lines.extend(
            [
                (
                    f'<text class="mobile-alignment" x="{margin + 12}" y="{y + 154}">'
                    f"Formal alignment · {escape_svg_text(humanize_identifier(witness.formal_alignment))}</text>"
                ),
                (
                    f'<text class="mobile-metric" x="{margin + 12}" y="{y + 172}">'
                    f"{len(witness.checks)} typed checks · max residual "
                    f"{_compact_number(_maximum_check_residual(witness))}</text>"
                ),
                (
                    f'<text class="{check_class}" x="{margin + 12}" '
                    f'y="{y + 23}">{check_label}</text>'
                ),
                (
                    f'<text class="mobile-non-proof" x="{margin + 12}" '
                    f'y="{y + 42}">NON-PROOF WITNESS</text>'
                ),
            ]
        )
        lines.extend(plot_lines)
        lines.append(
            f'<text class="mobile-boundary" x="{margin + 12}" y="{boundary_y}">'
            f"Boundary observed · {'yes' if witness.boundary_observed else 'no'} · "
            f"{len(witness.theorem_mirrors)} theorem mirrors</text>"
        )
        lines.append("</g>")
    lines.extend(
        [
            "</g>",
            (
                f'<text class="mobile-footer" x="10" y="{height - 38}">'
                f"Group {group_index} · {len(witnesses)} witnesses shown</text>"
            ),
            (
                f'<text class="mobile-footer" x="10" y="{height - 19}">'
                "Exact values continue in accessible tables.</text>"
            ),
            "</svg>",
        ]
    )
    return "\n".join(lines) + "\n"


def _parameter_table(witness: NumericalWitness) -> str:
    rows = "".join(
        f'<tr><th scope="row"><code>{escape_svg_text(key)}</code></th>'
        f"<td>{_text(_scalar_text(value))}</td></tr>"
        for key, value in witness.parameters
    )
    return (
        '<table class="parameter-table exact-table"><caption>Exact evaluated parameters</caption>'
        f"<tbody>{rows}</tbody></table>"
    )


def _data_table(witness: NumericalWitness) -> str:
    headings = "".join(
        f'<th scope="col" data-column-key="{escape_svg_text(column.key)}">{escape_svg_text(column.label)}</th>'
        for column in witness.columns
    )
    rows = "".join(
        f'<tr data-witness-row="{row_index}">'
        + "".join(f"<td>{_text(_scalar_text(value))}</td>" for value in row.values)
        + "</tr>"
        for row_index, row in enumerate(witness.rows)
    )
    return (
        '<table class="witness-data exact-table"><caption>Exact evaluated data</caption>'
        f"<thead><tr>{headings}</tr></thead><tbody>{rows}</tbody></table>"
    )


def _check_table(witness: NumericalWitness) -> str:
    rows = "".join(
        f'<tr data-numerical-check="{escape_svg_text(check.id)}">'
        f'<th scope="row"><code>{escape_svg_text(check.id)}</code></th>'
        f"<td><code>{escape_svg_text(check.relation)}</code></td>"
        f"<td>{_text(_scalar_text(check.lhs))}</td>"
        f"<td>{_text(_scalar_text(check.rhs))}</td>"
        f"<td>{check.tolerance!r}</td><td>{check.residual!r}</td>"
        f"<td>{str(check.accepted).lower()}</td></tr>"
        for check in witness.checks
    )
    return (
        '<table class="check-table exact-table"><caption>Typed numerical checks</caption>'
        '<thead><tr><th scope="col">Check</th><th scope="col">Relation</th>'
        '<th scope="col">Left</th><th scope="col">Right</th>'
        '<th scope="col">Tolerance</th><th scope="col">Residual</th>'
        f'<th scope="col">Accepted</th></tr></thead><tbody>{rows}</tbody></table>'
    )


def _exact_scroll_region(*, hint: str, label: str, table: str) -> str:
    """Expose one exact table as a keyboard-focusable horizontal region."""
    return (
        f'<p class="table-scroll-hint">{escape_svg_text(hint)}</p>'
        f'<div class="table-wrap exact-scroll" role="region" tabindex="0" '
        f'aria-label="{escape_svg_text(label)}" data-scroll-axis="horizontal">{table}</div>'
    )


def _witness_detail(witness: NumericalWitness) -> str:
    status = "accepted" if witness.accepted else "rejected"
    check_label = "TYPED CHECKS PASSED" if witness.accepted else "TYPED CHECKS FAILED"
    alignment_label = humanize_identifier(witness.formal_alignment)
    search = (
        f"{witness.id} {witness.family} {witness.title} {witness.invariant} "
        f"{' '.join(witness.theorem_mirrors)} {witness.boundary_behavior} "
        f"{witness.formal_alignment} {alignment_label} {_check_summary(witness)}"
    ).lower()
    mirrors = "".join(
        f'<li data-theorem-mirror="{index}"><code>{escape_svg_text(theorem)}</code></li>'
        for index, theorem in enumerate(witness.theorem_mirrors)
    )
    plot_series = ", ".join(
        f"<code>{escape_svg_text(key)}</code>" for key in witness.plot.y_keys
    )
    detail_id = f"witness-detail-{witness.id}"
    return (
        '<details class="witness-detail">'
        f'<summary class="witness-detail-summary" id="{escape_svg_text(detail_id)}">'
        f'<span class="summary-title">{escape_svg_text(witness.title)}</span>'
        f'<span class="summary-meta"><code>{escape_svg_text(witness.id)}</code> · '
        f"{escape_svg_text(humanize_identifier(witness.family))} · {check_label}</span></summary>"
        f'<article class="witness-workbench" data-witness-id="{escape_svg_text(witness.id)}" '
        f'data-family="{escape_svg_text(witness.family)}" data-status="{status}" '
        f'data-formal-alignment="{escape_svg_text(witness.formal_alignment)}" '
        f'data-search="{escape_svg_text(search)}">'
        f'<header><div><p class="eyebrow">{escape_svg_text(witness.family)}</p><h2>{escape_svg_text(witness.title)}</h2>'
        f'<p><code>{escape_svg_text(witness.id)}</code></p></div><div class="badges">'
        f'<span class="badge {status}">{check_label}</span>'
        '<span class="badge non-proof">NON-PROOF WITNESS</span></div></header>'
        f'<p class="invariant"><strong>Invariant.</strong> {escape_svg_text(witness.invariant)}</p>'
        '<dl class="diagnostics">'
        f"<div><dt>Numerical checks</dt><dd><code>{len(witness.checks)}</code></dd></div>"
        f"<div><dt>Maximum residual</dt><dd><code>{_compact_number(_maximum_check_residual(witness))}</code></dd></div>"
        f"<div><dt>Boundary observed</dt><dd>{str(witness.boundary_observed).lower()}</dd></div>"
        f"<div><dt>Evidence kind</dt><dd><code>{escape_svg_text(witness.evidence_kind)}</code></dd></div>"
        f"<div><dt>Formal alignment</dt><dd><code>{escape_svg_text(witness.formal_alignment)}</code>"
        f'<span class="alignment-note">{escape_svg_text(alignment_label)} — '
        f"{escape_svg_text(_formal_alignment_explanation(witness))}</span></dd></div>"
        "</dl>"
        f"<p><strong>Boundary behavior.</strong> {escape_svg_text(witness.boundary_behavior)}</p>"
        f"<p><strong>Plot contract.</strong> {escape_svg_text(witness.plot.kind)} · x <code>{escape_svg_text(witness.plot.x_key)}</code> · y {plot_series}</p>"
        '<div class="workbench-grid"><div>'
        f"{_exact_scroll_region(hint='← Swipe horizontally for exact parameters →', label=f'{witness.title} exact parameters', table=_parameter_table(witness))}"
        f'</div><div class="theorem-group"><h3>Theorem mirrors</h3><ul>{mirrors}</ul></div></div>'
        f"{_exact_scroll_region(hint='← Swipe horizontally for every typed numerical check →', label=f'{witness.title} typed numerical checks', table=_check_table(witness))}"
        f"{_exact_scroll_region(hint='← Swipe horizontally for all evaluated columns →', label=f'{witness.title} exact evaluated data', table=_data_table(witness))}"
        "</article></details>"
    )


def _detail_index(witnesses: tuple[NumericalWitness, ...]) -> str:
    items = "".join(
        f'<li><a data-detail-jump="{escape_svg_text(witness.id)}" '
        f'href="#witness-detail-{escape_svg_text(witness.id)}">'
        f"<code>{escape_svg_text(witness.id)}</code> · {escape_svg_text(witness.title)}</a></li>"
        for witness in witnesses
    )
    return (
        '<nav class="detail-navigation" aria-label="Numerical witness detail index">'
        f'<details class="detail-index" data-detail-count="{len(witnesses)}">'
        f"<summary>Browse {len(witnesses)} collapsed numerical witness records</summary>"
        "<p>Choose a record to open it directly. Search and filters expand every "
        "matching record automatically.</p>"
        f"<ol>{items}</ol></details></nav>"
    )




def _mobile_plot_groups(
    witnesses: tuple[NumericalWitness, ...],
) -> tuple[_MobilePlotGroup, ...]:
    """Partition the mobile overview into stable, countable three-plot groups."""
    return tuple(
        (
            offset + 1,
            min(offset + _MOBILE_PLOTS_PER_GROUP, len(witnesses)),
            witnesses[offset : offset + _MOBILE_PLOTS_PER_GROUP],
        )
        for offset in range(0, len(witnesses), _MOBILE_PLOTS_PER_GROUP)
    )


def render_formal_kernel_dashboard_html(dashboard: FormalKernelDashboard) -> str:
    """Render all witnesses as an offline filterable numerical workbench."""
    svg = _render_formal_kernel_dashboard_desktop_svg(
        dashboard, full_boundary=False
    ).rstrip()
    mobile_groups = _mobile_plot_groups(dashboard.witnesses)
    mobile_group_count = len(mobile_groups)
    mobile_group_svgs = tuple(
        _render_formal_kernel_dashboard_mobile_svg(
            dashboard,
            witnesses=witnesses,
            group_index=group_index,
            group_count=mobile_group_count,
            start_index=start_index,
        ).rstrip()
        for group_index, (start_index, _end_index, witnesses) in enumerate(
            mobile_groups, 1
        )
    )
    mobile_group_index = "".join(
        f'<a href="#mobile-plot-group-{group_index}" '
        f'data-mobile-group-jump="{group_index}" '
        f'aria-label="Plots {start_index} through {end_index}, '
        f'{len(witnesses)} plots">Plots {start_index}–{end_index}</a>'
        for group_index, (start_index, end_index, witnesses) in enumerate(
            mobile_groups, 1
        )
    )
    mobile_group_sections = "".join(
        f'<details id="mobile-plot-group-{group_index}" class="mobile-plot-group"'
        f' data-summary-count="{len(witnesses)}" data-first-index="{start_index}" '
        f'data-last-index="{end_index}"><summary><span>Plots {start_index}–'
        f"{end_index} of {len(dashboard.witnesses)}</span>"
        f"<small>{len(witnesses)} witnesses · open one group at a time</small></summary>"
        f'<p class="mobile-plot-scroll-cue">↕ Scroll within this group · '
        f"{len(witnesses)} complete plots</p>"
        f'<div class="mobile-plot-viewport" role="region" tabindex="0" '
        f'data-scroll-axis="vertical" aria-label="Scrollable plots {start_index} '
        f'through {end_index}">{mobile_svg}</div></details>'
        for group_index, ((start_index, end_index, witnesses), mobile_svg) in enumerate(
            zip(mobile_groups, mobile_group_svgs, strict=True), 1
        )
    )
    mobile_overview = (
        f'<div class="mobile-overview" data-summary-count="{len(dashboard.witnesses)}" '
        f'data-group-count="{mobile_group_count}">'
        f'<p class="mobile-overview-intro">{len(dashboard.witnesses)} plots in '
        f"{mobile_group_count} groups · at most {_MOBILE_PLOTS_PER_GROUP} plots per group. Groups start "
        "collapsed; use the index to open any group. Scroll inside an open "
        "group for its three complete plots.</p>"
        '<nav class="mobile-group-index" aria-label="Mobile plot groups">'
        f"{mobile_group_index}</nav>{mobile_group_sections}</div>"
    )
    families = sorted({witness.family for witness in dashboard.witnesses})
    records = "".join(_witness_detail(witness) for witness in dashboard.witnesses)
    detail_index = _detail_index(dashboard.witnesses)
    return (
        """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>"""
        + _DASHBOARD_READER_TITLE
        + """</title>
<style>
:root{color-scheme:light;--ink:#0f172a;--muted:#475569;--line:#cbd5e1;--paper:#f8fafc;--accent:#0f766e}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.5 system-ui,sans-serif}
.skip{position:absolute;left:-9999px}.skip:focus{left:12px;top:12px;background:white;padding:10px;z-index:20}
body>header,main{max-width:1650px;margin:auto;padding:24px}body>header{padding-bottom:10px}h1{margin:.1rem 0;font-size:clamp(2rem,5vw,3.4rem)}
.lede{max-width:90ch;color:var(--muted)}.boundary{border-left:5px solid #f97316;background:#fff7ed;padding:12px 16px;max-width:115ch}
.controls{display:grid;grid-template-columns:minmax(260px,2fr) minmax(220px,1fr) minmax(170px,1fr);gap:12px;position:sticky;top:0;z-index:8;background:rgba(248,250,252,.96);padding:12px 0}
.field{display:grid;gap:4px;min-width:0}label{font-weight:700}input,select{font:inherit;border:1px solid #94a3b8;border-radius:8px;background:white;padding:9px;color:var(--ink);width:100%;min-width:0;max-width:100%}
.result{grid-column:1/-1;color:var(--muted);min-height:1.5em}.overview{border:1px solid var(--line);border-radius:14px;background:white;overflow:hidden}
.desktop-overview{display:block}.mobile-overview{display:none}.overview-viewport{overflow:auto;scrollbar-color:#94a3b8 #e2e8f0}.desktop-overview svg{display:block;min-width:1100px;width:100%;height:auto}.mobile-overview-intro{margin:0;padding:14px 16px 10px;color:var(--muted)}.mobile-group-index{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:7px;padding:0 14px 12px}.mobile-group-index a{min-width:0;border:1px solid #94a3b8;border-radius:10px;padding:8px 5px;color:#0f4c81;font-size:.92rem;font-weight:800;text-align:center;text-decoration:none;white-space:nowrap}.mobile-plot-group{border-top:1px solid var(--line);scroll-margin-top:12px}.mobile-plot-group>summary{display:grid;grid-template-columns:auto 1fr;column-gap:9px;row-gap:2px;cursor:pointer;font-weight:800;list-style:none;padding:14px 16px}.mobile-plot-group>summary::-webkit-details-marker{display:none}.mobile-plot-group>summary::before{content:"▸";grid-row:1/3;align-self:center;color:#0f4c81;font-size:1.15rem}.mobile-plot-group[open]>summary::before{content:"▾"}.mobile-plot-group>summary span,.mobile-plot-group>summary small{grid-column:2}.mobile-plot-group>summary small{color:var(--muted);font-weight:650}.mobile-plot-scroll-cue{margin:0;padding:7px 16px;border-top:1px solid #bfdbfe;background:#eff6ff;color:#1e3a8a;font-weight:750}.mobile-plot-viewport{max-height:min(52vh,560px);overflow-y:auto;overflow-x:hidden;scrollbar-gutter:stable;scrollbar-color:#64748b #e2e8f0;overscroll-behavior-block:contain;border-top:1px solid #e2e8f0;box-shadow:inset 0 18px 14px -20px #1e3a8a,inset 0 -18px 14px -20px #1e3a8a}.mobile-plot-group svg{display:block;width:100%;height:auto}
.hint{padding:8px 12px;color:var(--muted)}.detail-navigation{margin:10px 0 18px}.detail-index,.record-collection,.witness-detail{border:1px solid var(--line);border-radius:14px;background:white}.detail-index>summary,.record-collection>summary,.witness-detail>summary{cursor:pointer;font-weight:800;padding:14px 16px}.detail-index>p{margin:0;padding:0 16px 10px;color:var(--muted)}.detail-index ol{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:6px 24px;margin:0;padding:0 16px 18px 44px}.detail-index a{overflow-wrap:anywhere}.record-collection{margin:18px 0;scroll-margin-top:150px}.record-list{padding:0 14px 1px}.witness-detail{margin:16px 0;scroll-margin-top:150px;overflow:clip}.witness-detail,.witness-detail>*{min-width:0;max-width:100%}.witness-detail[open]>summary{border-bottom:1px solid var(--line)}.witness-detail-summary{display:flex;justify-content:space-between;gap:18px;align-items:start}.summary-title{font-size:1.05rem}.summary-meta{color:var(--muted);font-weight:650;text-align:right}.witness-workbench{margin:0;border:0;background:white;padding:20px}
.witness-workbench>header{display:flex;justify-content:space-between;gap:18px;align-items:start}.witness-workbench>header>div:first-child{min-width:0}.witness-workbench h2{margin:.15rem 0}.eyebrow{margin:0;color:var(--accent);font-weight:800;text-transform:uppercase;letter-spacing:.04em;font-size:.78rem}
.badges{display:flex;flex:0 0 auto;flex-direction:column;align-items:flex-end;gap:6px}.badge{border-radius:999px;padding:5px 10px;font-weight:800;text-transform:uppercase;white-space:nowrap}.badge.accepted{background:#d1fae5;color:#065f46}.badge.rejected{background:#ffe4e6;color:#9f1239}.badge.non-proof{background:#fff7ed;color:#9a3412}
.invariant{font-size:1.04rem}.diagnostics{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}.diagnostics div{background:#f1f5f9;border-radius:9px;padding:10px}
dt{color:var(--muted);font-weight:700}dd{margin:3px 0 0;overflow-wrap:anywhere}.workbench-grid{display:grid;grid-template-columns:minmax(320px,1fr) minmax(320px,1fr);gap:18px;min-width:0;max-width:100%}.workbench-grid>*{min-width:0;max-width:100%}.theorem-group{min-width:0;max-width:100%;overflow-x:auto}
.alignment-note{display:block;margin-top:4px;color:var(--muted);font-size:.9rem}
.table-scroll-hint{display:none;margin:14px 0 0;padding:8px 10px;background:#eff6ff;color:#1e3a8a;font-weight:750;border-radius:8px}.table-wrap{overflow:auto;border:1px solid var(--line);border-radius:10px;margin-top:8px;scrollbar-color:#64748b #e2e8f0;scrollbar-gutter:stable;overscroll-behavior-inline:contain;box-shadow:inset -16px 0 12px -18px #1e3a8a}.exact-scroll{min-width:0;max-width:100%;overflow-x:auto}table{border-collapse:collapse;width:100%;min-width:620px}.parameter-table{min-width:max(420px,100%);table-layout:auto}caption{text-align:left;padding:10px;font-weight:800}
th,td{padding:9px;border-top:1px solid #e2e8f0;text-align:left;vertical-align:top;overflow-wrap:anywhere}thead th{background:#e2e8f0}.witness-workbench,.witness-workbench>*{min-width:0;max-width:100%}.witness-workbench code{font-size:.87em;overflow-wrap:anywhere;word-break:break-word}.witness-workbench li{overflow-wrap:anywhere;word-break:break-word}[hidden]{display:none!important}
.witness-workbench .exact-table th,.witness-workbench .exact-table td,.witness-workbench .exact-table code{white-space:nowrap;overflow-wrap:normal;word-break:normal;font-variant-numeric:tabular-nums}
@media (max-width: 900px){.controls{grid-template-columns:1fr 1fr}.controls .search{grid-column:1/-1}.diagnostics{grid-template-columns:1fr 1fr}.workbench-grid{grid-template-columns:1fr}}
@media (max-width: 760px){.desktop-overview{display:none}.mobile-overview{display:block}body>header,main{padding:14px}.controls{position:static;grid-template-columns:1fr}.controls .search{grid-column:auto}.detail-index ol{grid-template-columns:1fr;padding-left:36px}.witness-detail-summary{display:block}.summary-meta{display:block;margin-top:5px;text-align:left}.diagnostics{grid-template-columns:1fr}.witness-workbench{padding:14px}.witness-workbench>header{display:block}.badges{align-items:flex-start;margin-top:10px}.badge{display:inline-block;white-space:normal}.table-scroll-hint{display:block}.exact-scroll{border-color:#60a5fa;box-shadow:inset -20px 0 16px -20px #1e3a8a}}
@media (prefers-reduced-motion: reduce){*{scroll-behavior:auto!important}}
</style>
</head>
<body>
<a class="skip" href="#witnesses">Skip to numerical witnesses</a>
<header><p>FEP Lean · deterministic generated projection</p><h1>"""
        + _DASHBOARD_READER_TITLE
        + """</h1>"""
        f'<p class="lede">All {len(dashboard.witnesses)} typed witnesses are rendered from '
        "their evaluated table and plot schemas. Nothing here is recomputed in the "
        "presentation layer.</p>"
        f'<p class="boundary"><strong>Evidence boundary.</strong> {escape_svg_text(dashboard.numerical_evidence_boundary)}'
        "</p></header><main>"
        '<section class="controls" aria-label="Numerical witness filters">'
        '<div class="field search"><label for="witness-search">Search workbench</label>'
        '<input id="witness-search" type="search" aria-keyshortcuts="/ Escape" placeholder="Family, ID, theorem, invariant, boundary…"></div>'
        '<div class="field"><label for="witness-family-filter">Family</label><select id="witness-family-filter">'
        f"{options_fragment(families, all_label='families')}</select></div>"
        '<div class="field"><label for="witness-status-filter">Evaluation status</label><select id="witness-status-filter">'
        '<option value="">All statuses</option><option value="accepted">Typed checks passed</option><option value="rejected">Typed checks failed</option></select></div>'
        f'<div id="witness-result-count" class="result" role="status" aria-live="polite">{len(dashboard.witnesses)} witnesses matched</div>'
        "</section>"
        '<section id="witness-overview" aria-labelledby="overview-title"><h2 id="overview-title">All-family visual summary</h2>'
        '<div class="overview"><div class="desktop-overview"><div class="overview-viewport" tabindex="0" aria-label="Scrollable numerical witness summary">'
        f"{svg}</div></div>{mobile_overview}"
        '<p class="hint">The exact tables below are authoritative for displayed values; plots are compact visual encodings of the same rows.</p></div></section>'
        f'<details id="witnesses" class="record-collection" data-detail-count="{len(dashboard.witnesses)}">'
        f"<summary>Exact evaluated witness records · {len(dashboard.witnesses)}</summary>"
        f"{detail_index}"
        f'<section class="record-list" aria-label="Accessible numerical witness data">{records}</section></details>'
        """</main>
<script>
"use strict";
const search=document.getElementById("witness-search");
const family=document.getElementById("witness-family-filter");
const status=document.getElementById("witness-status-filter");
const result=document.getElementById("witness-result-count");
const overview=document.getElementById("witness-overview");
const recordCollection=document.getElementById("witnesses");
const records=[...document.querySelectorAll(".witness-detail")];
const mobilePlotGroups=[...document.querySelectorAll(".mobile-plot-group")];
const recordById=new Map(records.map(record=>{const card=record.querySelector(".witness-workbench");return[card.dataset.witnessId,record];}));
function applyFilters(){const query=search.value.trim().toLowerCase();const filtering=Boolean(query||family.value||status.value);let matched=0;records.forEach(record=>{const card=record.querySelector(".witness-workbench");const show=(!query||card.dataset.search.includes(query))&&(!family.value||card.dataset.family===family.value)&&(!status.value||card.dataset.status===status.value);record.hidden=!show;record.open=filtering&&show;if(show)matched+=1;});overview.hidden=filtering;recordCollection.open=filtering;result.textContent=filtering?`${matched} of ${records.length} witnesses matched; matching detail records expanded below`:`${records.length} witness records available; details collapsed below`;}
[search,family,status].forEach(control=>control.addEventListener("input",applyFilters));
document.querySelectorAll("[data-detail-jump]").forEach(link=>link.addEventListener("click",()=>{search.value="";family.value="";status.value="";applyFilters();const target=recordById.get(link.dataset.detailJump);recordCollection.open=true;target.hidden=false;target.open=true;target.querySelector("summary").focus();}));
document.querySelectorAll("[data-mobile-group-jump]").forEach(link=>link.addEventListener("click",()=>{const target=document.getElementById(`mobile-plot-group-${link.dataset.mobileGroupJump}`);mobilePlotGroups.forEach(group=>group.open=group===target);target.querySelector("summary").focus();}));
document.addEventListener("keydown",event=>{const editing=["INPUT","SELECT","TEXTAREA"].includes(document.activeElement.tagName);if(event.key==="/"&&!editing){event.preventDefault();search.focus();}if(event.key==="Escape"){search.value="";family.value="";status.value="";applyFilters();search.focus();}});
applyFilters();
</script>
</body>
</html>
"""
    )


def dashboard_projection_paths(
    project_root: Path, *, output_root: Path | None = None
) -> tuple[Path, Path]:
    """Return dashboard destinations, optionally under a temporary root."""
    root = Path(output_root) if output_root is not None else Path(project_root)
    return root / DASHBOARD_SVG, root / DASHBOARD_HTML


def write_formal_kernel_dashboard(
    project_root: Path, *, output_root: Path | None = None
) -> tuple[Path, Path]:
    """Write deterministic SVG and HTML numerical-workbench projections."""
    dashboard = build_formal_kernel_dashboard(Path(project_root))
    svg_path, html_path = dashboard_projection_paths(
        project_root, output_root=output_root
    )
    atomic_write_text(svg_path, render_formal_kernel_dashboard_svg(dashboard))
    atomic_write_text(html_path, render_formal_kernel_dashboard_html(dashboard))
    return svg_path, html_path


def formal_kernel_dashboard_drift(
    project_root: Path,
    *,
    output_root: Path | None = None,
    presentation: FormalismPresentation | None = None,
) -> tuple[Path, ...]:
    """Return missing or stale dashboard projection paths in stable order.

    ``presentation`` optionally supplies the already-built shared join (SC-20).
    """
    dashboard = (
        build_formal_kernel_dashboard(Path(project_root))
        if presentation is None
        else presentation
    )
    svg_path, html_path = dashboard_projection_paths(
        project_root, output_root=output_root
    )
    expected = {
        svg_path: render_formal_kernel_dashboard_svg(dashboard),
        html_path: render_formal_kernel_dashboard_html(dashboard),
    }
    return tuple(
        path
        for path, content in expected.items()
        if not path.is_file() or path.read_text(encoding="utf-8") != content
    )


__all__ = [
    "FormalKernelDashboard",
    "build_formal_kernel_dashboard",
    "dashboard_projection_paths",
    "formal_kernel_dashboard_drift",
    "render_formal_kernel_dashboard_html",
    "render_formal_kernel_dashboard_svg",
    "write_formal_kernel_dashboard",
]
