"""The formal-kernel dashboard renders every typed numerical witness."""

from __future__ import annotations

import html as html_lib
import math
import re
from itertools import pairwise
from pathlib import Path
from xml.etree import ElementTree

from fep_lean.output.formal_kernel_dashboard import (
    build_formal_kernel_dashboard,
    formal_kernel_dashboard_drift,
    render_formal_kernel_dashboard_html,
    render_formal_kernel_dashboard_svg,
    write_formal_kernel_dashboard,
)
from fep_lean.output.formalism_presentation import FormalismPresentation
from fep_lean.verification.numerical_witnesses import NON_PROOF_EVIDENCE

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SVG_NAMESPACE = "http://www.w3.org/2000/svg"
MOBILE_SVG_PATTERN = re.compile(
    r'(<svg xmlns="http://www.w3.org/2000/svg"[^>]+data-layout="mobile".*?</svg>)',
    re.DOTALL,
)


def _mobile_svg_roots(rendered: str) -> list[ElementTree.Element]:
    return [
        ElementTree.fromstring(match) for match in MOBILE_SVG_PATTERN.findall(rendered)
    ]


def _mobile_root_for(rendered: str, witness_id: str) -> ElementTree.Element:
    return next(
        root
        for root in _mobile_svg_roots(rendered)
        if any(
            element.attrib.get("data-mobile-witness-summary") == witness_id
            for element in root.iter()
        )
    )


def _mobile_summaries(rendered: str) -> list[ElementTree.Element]:
    return [
        element
        for root in _mobile_svg_roots(rendered)
        for element in root.iter(f"{{{SVG_NAMESPACE}}}g")
        if "data-mobile-witness-summary" in element.attrib
    ]


def test_dashboard_uses_all_typed_witnesses_from_the_shared_join() -> None:
    dashboard = build_formal_kernel_dashboard(PROJECT_ROOT)

    assert isinstance(dashboard, FormalismPresentation)
    assert len(dashboard.witnesses) == 16
    assert len({witness.id for witness in dashboard.witnesses}) == 16
    assert len({witness.family for witness in dashboard.witnesses}) == 16
    assert all(witness.accepted for witness in dashboard.witnesses)
    assert all(
        witness.evidence_kind == NON_PROOF_EVIDENCE for witness in dashboard.witnesses
    )


def test_dashboard_explicitly_distinguishes_witness_formal_alignment() -> None:
    dashboard = build_formal_kernel_dashboard(PROJECT_ROOT)
    svg = render_formal_kernel_dashboard_svg(dashboard)
    html = render_formal_kernel_dashboard_html(dashboard)
    root = ElementTree.fromstring(svg)
    subgaussian = next(
        group
        for group in root.iter(f"{{{SVG_NAMESPACE}}}g")
        if group.attrib.get("data-witness-summary") == "subgaussian-envelope"
    )
    theorem_instance = next(
        group
        for group in root.iter(f"{{{SVG_NAMESPACE}}}g")
        if group.attrib.get("data-witness-summary") == "measure-bayes-reconstruction"
    )
    subgaussian_html = re.search(
        r'<article[^>]+data-witness-id="subgaussian-envelope".*?</article>',
        html,
        re.DOTALL,
    )
    assert subgaussian_html is not None

    assert subgaussian.attrib["data-formal-alignment"] == "structural_analogue"
    assert "Formal alignment · Structural Analogue" in " ".join(
        text.strip() for text in subgaussian.itertext() if text.strip()
    )
    assert theorem_instance.attrib["data-formal-alignment"] == "theorem_instance"
    assert "Formal alignment · Theorem Instance" in " ".join(
        text.strip() for text in theorem_instance.itertext() if text.strip()
    )
    assert "<code>structural_analogue</code>" in subgaussian_html.group(0)
    assert "does not discharge all formal premises" in subgaussian_html.group(0)
    assert html.count('data-formal-alignment="structural_analogue"') == 3
    assert html.count('data-formal-alignment="theorem_instance"') == 45
    assert ".overview-viewport{overflow:auto;max-height" not in html


def test_svg_summarizes_every_witness_without_external_assets() -> None:
    dashboard = build_formal_kernel_dashboard(PROJECT_ROOT)
    svg = render_formal_kernel_dashboard_svg(dashboard)

    assert svg.startswith(f'<svg xmlns="{SVG_NAMESPACE}"')
    assert 'role="img"' in svg
    assert svg.count('data-witness-summary="') == len(dashboard.witnesses)
    assert svg.count('data-witness-status="accepted"') == len(dashboard.witnesses)
    assert svg.count('data-boundary-observed="true"') == len(dashboard.witnesses)
    assert svg.count('class="banner-line"') == 2
    assert '<text class="banner-label" x="58" y="123">Evidence boundary</text>' in svg
    assert "typed checks" in svg
    assert "Boundary observed" in svg
    assert "explanatory non-proof evidence" in svg
    for witness in dashboard.witnesses:
        assert witness.id in svg
        assert witness.title in svg
        assert witness.family in svg
        assert witness.boundary_behavior in html_lib.unescape(svg)
        for theorem in witness.theorem_mirrors:
            assert theorem in html_lib.unescape(svg)
        for check in witness.checks:
            assert check.id in html_lib.unescape(svg)
    assert "https://" not in svg
    assert "<image" not in svg and "<script" not in svg
    assert svg.replace(SVG_NAMESPACE, "").count("http://") == 0


def test_standalone_dashboard_uses_full_canvas_in_three_readable_columns() -> None:
    dashboard = build_formal_kernel_dashboard(PROJECT_ROOT)
    rendered = render_formal_kernel_dashboard_svg(dashboard)
    root = ElementTree.fromstring(rendered)
    _, _, view_width, view_height = (
        float(value) for value in root.attrib["viewBox"].split()
    )
    cards = [
        rectangle
        for rectangle in root.iter(f"{{{SVG_NAMESPACE}}}rect")
        if rectangle.attrib.get("class") == "card"
    ]

    assert root.attrib["width"] == str(int(view_width))
    assert root.attrib["height"] == str(int(view_height))
    assert root.attrib["data-column-count"] == "3"
    assert view_width / view_height >= 0.45
    assert len(cards) == len(dashboard.witnesses)
    assert len({rectangle.attrib["x"] for rectangle in cards}) == 3
    assert len({rectangle.attrib["y"] for rectangle in cards}) == 6
    assert min(float(rectangle.attrib["x"]) for rectangle in cards) <= 20
    assert (
        max(
            float(rectangle.attrib["x"]) + float(rectangle.attrib["width"])
            for rectangle in cards
        )
        >= view_width - 20
    )
    for rectangle in cards:
        assert (
            float(rectangle.attrib["x"]) + float(rectangle.attrib["width"])
            <= view_width
        )
        assert (
            float(rectangle.attrib["y"]) + float(rectangle.attrib["height"])
            <= view_height
        )
    assert ".card-title{fill:#0f172a;font:800 19px" in rendered
    assert ".axis-label{fill:#334155;font:750 16px" in rendered
    assert re.search(r"\.legend,[^\n]+font:650 15px", rendered)
    assert ".check-passed{fill:#047857;font:800 14px" in rendered


def test_bar_plots_use_and_disclose_a_zero_baseline() -> None:
    dashboard = build_formal_kernel_dashboard(PROJECT_ROOT)
    svg = render_formal_kernel_dashboard_svg(dashboard)
    bar_witnesses = [
        witness for witness in dashboard.witnesses if witness.plot.kind == "bar"
    ]

    assert svg.count('data-zero-baseline="true"') == len(bar_witnesses)
    for witness in bar_witnesses:
        assert (
            f'data-plot-for="{witness.id}" data-zero-baseline="true" data-y-min="0.0"'
        ) in svg
    assert svg.count('class="scale-zero"') == len(bar_witnesses)


def test_exact_zero_bars_are_explicitly_distinct_from_missing_values() -> None:
    dashboard = build_formal_kernel_dashboard(PROJECT_ROOT)
    rendered = render_formal_kernel_dashboard_html(dashboard)
    root = _mobile_root_for(rendered, "categorical-fisher-rank")
    fisher = next(
        group
        for group in root.iter(f"{{{SVG_NAMESPACE}}}g")
        if group.attrib.get("data-plot-for") == "categorical-fisher-rank"
    )
    zero_bars = [
        bar
        for bar in fisher.iter(f"{{{SVG_NAMESPACE}}}rect")
        if bar.attrib.get("data-zero-value") == "true"
    ]
    zero_markers = [
        marker
        for marker in fisher.iter(f"{{{SVG_NAMESPACE}}}circle")
        if marker.attrib.get("class") == "zero-value-marker"
    ]
    zero_key = next(
        text
        for text in fisher.iter(f"{{{SVG_NAMESPACE}}}text")
        if text.attrib.get("class") == "exact-zero-key"
    )

    assert len(zero_bars) == 1
    assert zero_bars[0].attrib["data-category-index"] == "4"
    assert zero_bars[0].attrib["data-series-key"] == "observed"
    assert zero_bars[0].attrib["data-value"] == "0.0"
    assert len(zero_markers) == 1
    assert zero_markers[0].attrib["data-category-index"] == "4"
    assert zero_markers[0].attrib["data-series-key"] == "observed"
    assert "exact zero" in " ".join(zero_key.itertext()).lower()
    assert "not missing" in " ".join(zero_key.itertext()).lower()


def test_grouped_exact_zero_markers_remain_distinct_for_each_series() -> None:
    dashboard = build_formal_kernel_dashboard(PROJECT_ROOT)
    rendered = render_formal_kernel_dashboard_html(dashboard)
    root = _mobile_root_for(rendered, "native-blanket-transfer")
    blanket = next(
        group
        for group in root.iter(f"{{{SVG_NAMESPACE}}}g")
        if group.attrib.get("data-plot-for") == "native-blanket-transfer"
    )
    zero_bars = [
        bar
        for bar in blanket.iter(f"{{{SVG_NAMESPACE}}}rect")
        if bar.attrib.get("data-category-index") == "2"
        and bar.attrib.get("data-zero-value") == "true"
    ]
    zero_markers = [
        marker
        for marker in blanket.iter(f"{{{SVG_NAMESPACE}}}circle")
        if marker.attrib.get("class") == "zero-value-marker"
        and marker.attrib.get("data-category-index") == "2"
    ]

    assert len(zero_bars) == len(zero_markers) == 2
    assert len({marker.attrib["cx"] for marker in zero_markers}) == 2
    bar_centers = {
        bar.attrib["data-series-key"]: (
            float(bar.attrib["x"]) + float(bar.attrib["width"]) / 2
        )
        for bar in zero_bars
    }
    marker_centers = {
        marker.attrib["data-series-key"]: float(marker.attrib["cx"])
        for marker in zero_markers
    }
    zero_key = next(
        text
        for text in blanket.iter(f"{{{SVG_NAMESPACE}}}text")
        if text.attrib.get("class") == "exact-zero-key"
    )
    assert marker_centers.keys() == bar_centers.keys()
    assert all(
        math.isclose(marker_centers[key], bar_centers[key], abs_tol=0.01)
        for key in marker_centers
    )
    assert "marker per series" in " ".join(zero_key.itertext()).lower()
    assert not any(
        text.attrib.get("class") == "coincident-series-key"
        for text in blanket.iter(f"{{{SVG_NAMESPACE}}}text")
    )


def test_coincident_line_series_use_a_shared_exact_rail_and_distinct_markers() -> None:
    dashboard = build_formal_kernel_dashboard(PROJECT_ROOT)
    rendered = render_formal_kernel_dashboard_html(dashboard)
    root = _mobile_root_for(rendered, "belief-consensus-contraction")
    consensus = next(
        group
        for group in root.iter(f"{{{SVG_NAMESPACE}}}g")
        if group.attrib.get("data-plot-for") == "belief-consensus-contraction"
    )
    rails = [
        path
        for path in consensus.iter(f"{{{SVG_NAMESPACE}}}path")
        if path.attrib.get("class") == "coincident-value-rail"
    ]
    markers = [
        element
        for element in consensus.iter()
        if element.attrib.get("class") == "coincident-series-marker"
    ]
    markers_by_point: dict[str, list[ElementTree.Element]] = {}
    for marker in markers:
        markers_by_point.setdefault(marker.attrib["data-point-index"], []).append(
            marker
        )

    assert len(rails) == 1
    assert rails[0].attrib["data-series-keys"] == "gap | predicted_gap"
    assert rails[0].attrib["data-visual-offset"] == "0"
    assert rails[0].attrib["stroke"] == "#334155"
    assert set(markers_by_point) == {str(index) for index in range(9)}
    for point_markers in markers_by_point.values():
        assert {marker.attrib["data-series-key"] for marker in point_markers} == {
            "gap",
            "predicted_gap",
        }
        assert {marker.attrib["data-marker-shape"] for marker in point_markers} == {
            "ring",
            "diamond",
        }
        assert {marker.attrib["data-center-x"] for marker in point_markers} == {
            point_markers[0].attrib["data-center-x"]
        }
        assert {marker.attrib["data-center-y"] for marker in point_markers} == {
            point_markers[0].attrib["data-center-y"]
        }
        assert {marker.attrib["data-visual-offset"] for marker in point_markers} == {
            "0"
        }
    ring = next(
        marker for marker in markers if marker.attrib["data-marker-shape"] == "ring"
    )
    diamond = next(
        marker for marker in markers if marker.attrib["data-marker-shape"] == "diamond"
    )
    assert ring.tag == f"{{{SVG_NAMESPACE}}}circle"
    assert float(ring.attrib["r"]) >= 5
    assert float(ring.attrib["stroke-width"]) >= 2.5
    assert diamond.tag == f"{{{SVG_NAMESPACE}}}rect"
    assert float(diamond.attrib["width"]) >= 7
    legend_markers = [
        element
        for element in consensus.iter()
        if element.attrib.get("class") == "coincident-legend-marker"
    ]
    assert {marker.attrib["data-marker-shape"] for marker in legend_markers} == {
        "ring",
        "diamond",
    }
    overlap_key = next(
        text
        for text in consensus.iter(f"{{{SVG_NAMESPACE}}}text")
        if text.attrib.get("class") == "coincident-series-key"
    )
    overlap_text = " ".join(overlap_key.itertext()).lower()
    assert "identical values" in overlap_text
    assert "shared rail" in overlap_text
    assert "no value offset" in overlap_text


def test_long_series_legend_is_fully_visible_without_ellipsis() -> None:
    svg = render_formal_kernel_dashboard_svg(
        build_formal_kernel_dashboard(PROJECT_ROOT)
    )
    root = ElementTree.fromstring(svg)
    weighted_legend = next(
        text
        for text in root.iter(f"{{{SVG_NAMESPACE}}}text")
        if text.attrib.get("class") == "legend"
        and (title := text.find(f"{{{SVG_NAMESPACE}}}title")) is not None
        and title.text == "weighted_exponential"
    )
    visible_lines = [
        child.text or ""
        for child in weighted_legend
        if child.tag == f"{{{SVG_NAMESPACE}}}tspan"
    ]

    assert weighted_legend.attrib["data-series-key"] == "weighted_exponential"
    assert " ".join(visible_lines) == "Forward-weighted exponential"
    assert all("…" not in line for line in visible_lines)


def test_desktop_legend_lines_fit_inside_each_summary_card() -> None:
    root = ElementTree.fromstring(
        render_formal_kernel_dashboard_svg(build_formal_kernel_dashboard(PROJECT_ROOT))
    )
    groups = [
        group
        for group in root.iter(f"{{{SVG_NAMESPACE}}}g")
        if "data-witness-summary" in group.attrib
    ]

    assert len(groups) == 16
    for group in groups:
        card = next(
            rectangle
            for rectangle in group.iter(f"{{{SVG_NAMESPACE}}}rect")
            if rectangle.attrib.get("class") == "card"
        )
        card_right = float(card.attrib["x"]) + float(card.attrib["width"])
        card_bottom = float(card.attrib["y"]) + float(card.attrib["height"])
        for legend in (
            text
            for text in group.iter(f"{{{SVG_NAMESPACE}}}text")
            if text.attrib.get("class") == "legend"
        ):
            for line in legend.findall(f"{{{SVG_NAMESPACE}}}tspan"):
                # Seven pixels per character is conservative for the declared
                # 13 px system font and catches labels that overrun the card.
                assert float(line.attrib["x"]) + 7 * len(line.text or "") <= (
                    card_right - 8
                )
                assert float(line.attrib["y"]) + 13 <= card_bottom - 8


def test_every_plot_discloses_axis_quantities_units_domain_and_y_extrema() -> None:
    dashboard = build_formal_kernel_dashboard(PROJECT_ROOT)
    root = ElementTree.fromstring(render_formal_kernel_dashboard_svg(dashboard))
    plot_groups = {
        group.attrib["data-plot-for"]: group
        for group in root.iter(f"{{{SVG_NAMESPACE}}}g")
        if "data-plot-for" in group.attrib
    }

    assert set(plot_groups) == {witness.id for witness in dashboard.witnesses}
    for witness in dashboard.witnesses:
        group = plot_groups[witness.id]
        texts = list(group.iter(f"{{{SVG_NAMESPACE}}}text"))
        domain = next(text for text in texts if text.attrib.get("class") == "x-domain")
        x_axis = next(
            text
            for text in texts
            if "axis-x-label" in text.attrib.get("class", "").split()
        )
        y_axis = next(
            text
            for text in texts
            if "axis-y-label" in text.attrib.get("class", "").split()
        )
        visible_domain = " ".join(
            text.strip() for text in domain.itertext() if text.strip()
        )
        declared_domain = domain.attrib["data-x-domain"]
        x_index = next(
            index
            for index, column in enumerate(witness.columns)
            if column.key == witness.plot.x_key
        )
        x_label = witness.columns[x_index].label
        first_x = str(witness.rows[0].values[x_index])
        last_x = str(witness.rows[-1].values[x_index])
        y_labels = [
            next(column.label for column in witness.columns if column.key == key)
            for key in witness.plot.y_keys
        ]

        assert x_label in declared_domain
        assert first_x in declared_domain
        assert last_x in declared_domain
        if group.attrib["data-x-unit"] == "categorical":
            category_keys = [
                text
                for text in texts
                if text.attrib.get("class") == "category-key-item"
            ]
            assert len(category_keys) == len(witness.rows)
            assert "full labels in exact HTML table" in visible_domain
        else:
            assert x_label in visible_domain
            assert first_x in visible_domain
            assert last_x in visible_domain
        assert x_label in " ".join(x_axis.itertext())
        assert group.attrib["data-x-quantity"] == x_label
        assert group.attrib["data-x-unit"] in {"categorical", "dimensionless"}
        assert "unit:" in " ".join(x_axis.itertext())
        assert group.attrib["data-y-quantities"] == " | ".join(y_labels)
        assert group.attrib["data-y-unit"] == "dimensionless"
        assert all(label in " ".join(y_axis.itertext()) for label in y_labels)
        assert "unit: dimensionless" in " ".join(y_axis.itertext())
        assert any(text.attrib.get("class") == "scale-maximum" for text in texts)
        minimum_class = "scale-zero" if witness.plot.kind == "bar" else "scale-minimum"
        assert any(text.attrib.get("class") == minimum_class for text in texts)

    soft_bellman = plot_groups["soft-bellman-temperature"]
    assert float(soft_bellman.attrib["data-y-min"]) < 0
    assert any(
        "-0.811" in " ".join(text.itertext())
        for text in soft_bellman.iter(f"{{{SVG_NAMESPACE}}}text")
        if text.attrib.get("class") == "scale-minimum"
    )


def test_categorical_bars_have_an_aligned_key_before_the_footer_band() -> None:
    dashboard = build_formal_kernel_dashboard(PROJECT_ROOT)
    witness = next(
        item for item in dashboard.witnesses if item.id == "categorical-fisher-rank"
    )
    root = ElementTree.fromstring(render_formal_kernel_dashboard_svg(dashboard))
    summary = next(
        group
        for group in root.iter(f"{{{SVG_NAMESPACE}}}g")
        if group.attrib.get("data-witness-summary") == witness.id
    )
    plot = next(
        group
        for group in summary.iter(f"{{{SVG_NAMESPACE}}}g")
        if group.attrib.get("data-plot-for") == witness.id
    )
    ticks = [
        text
        for text in plot.iter(f"{{{SVG_NAMESPACE}}}text")
        if text.attrib.get("class") == "category-tick"
    ]
    keys = [
        text
        for text in plot.iter(f"{{{SVG_NAMESPACE}}}text")
        if text.attrib.get("class") == "category-key-item"
    ]
    bars = [
        rectangle
        for rectangle in plot.iter(f"{{{SVG_NAMESPACE}}}rect")
        if "data-category-index" in rectangle.attrib
    ]
    x_index = next(
        index
        for index, column in enumerate(witness.columns)
        if column.key == witness.plot.x_key
    )
    categories = [str(row.values[x_index]) for row in witness.rows]

    assert plot.attrib["data-category-count"] == str(len(categories))
    assert [text.text for text in ticks] == [
        f"C{index}" for index in range(1, len(categories) + 1)
    ]
    assert [text.attrib["data-category-value"] for text in keys] == categories
    assert [text.attrib["data-category-label"] for text in keys] == [
        f"C{index}" for index in range(1, len(categories) + 1)
    ]
    assert len(bars) == len(categories)
    for tick, bar in zip(ticks, bars, strict=True):
        bar_center = float(bar.attrib["x"]) + float(bar.attrib["width"]) / 2
        assert math.isclose(float(tick.attrib["x"]), bar_center, abs_tol=0.01)

    annotation_bottom = float(plot.attrib["data-annotation-band-bottom"])
    footer_top = float(summary.attrib["data-footer-band-top"])
    assert annotation_bottom + 6 <= footer_top
    card = next(
        rectangle
        for rectangle in summary.iter(f"{{{SVG_NAMESPACE}}}rect")
        if rectangle.attrib.get("class") == "card"
    )
    card_right = float(card.attrib["x"]) + float(card.attrib["width"])
    for key in keys:
        assert float(key.attrib["x"]) + 7 * len(key.text or "") <= card_right - 8
        assert float(key.attrib["y"]) + 12 <= footer_top - 6
    footer_text = [
        text
        for text in summary.iter(f"{{{SVG_NAMESPACE}}}text")
        if text.attrib.get("class") == "alignment"
    ]
    assert len(footer_text) == 2
    assert min(float(text.attrib["y"]) for text in footer_text) >= footer_top + 18


def test_mobile_categorical_axis_and_key_have_card_relative_spacing() -> None:
    dashboard = build_formal_kernel_dashboard(PROJECT_ROOT)
    rendered = render_formal_kernel_dashboard_html(dashboard)
    root = _mobile_root_for(rendered, "categorical-fisher-rank")
    summary = next(
        group
        for group in root.iter(f"{{{SVG_NAMESPACE}}}g")
        if group.attrib.get("data-mobile-witness-summary") == "categorical-fisher-rank"
    )
    plot = next(
        group
        for group in summary.iter(f"{{{SVG_NAMESPACE}}}g")
        if group.attrib.get("data-plot-for") == "categorical-fisher-rank"
    )
    card = next(
        rectangle
        for rectangle in summary.iter(f"{{{SVG_NAMESPACE}}}rect")
        if rectangle.attrib.get("class") == "mobile-card"
    )
    card_right = float(card.attrib["x"]) + float(card.attrib["width"])
    x_axis = next(
        text
        for text in plot.iter(f"{{{SVG_NAMESPACE}}}text")
        if "axis-x-label" in text.attrib.get("class", "").split()
    )
    keys = [
        text
        for text in plot.iter(f"{{{SVG_NAMESPACE}}}text")
        if text.attrib.get("class") == "category-key-item"
    ]

    assert plot.attrib["data-category-key-columns"] == "1"
    for line in x_axis.findall(f"{{{SVG_NAMESPACE}}}tspan"):
        assert float(line.attrib["x"]) + 7 * len(line.text or "") <= card_right - 10
    rows: dict[float, list[ElementTree.Element]] = {}
    for key in keys:
        rows.setdefault(float(key.attrib["y"]), []).append(key)
    assert len(rows) == 5
    assert all(len(row) == 1 for row in rows.values())
    assert all(right - left >= 20 for left, right in pairwise(sorted(rows)))
    for row in rows.values():
        ordered = sorted(row, key=lambda item: float(item.attrib["x"]))
        for left, right in pairwise(ordered):
            left_edge = float(left.attrib["x"]) + 7 * len(left.text or "")
            assert left_edge + 12 <= float(right.attrib["x"])


def test_narrow_workbench_has_a_single_column_summary_with_every_witness() -> None:
    dashboard = build_formal_kernel_dashboard(PROJECT_ROOT)
    html = render_formal_kernel_dashboard_html(dashboard)

    assert html.count('data-mobile-witness-summary="') == len(dashboard.witnesses)
    for witness in dashboard.witnesses:
        assert f'data-mobile-witness-summary="{witness.id}"' in html
    assert 'class="mobile-overview"' in html
    assert ".mobile-overview{display:none}" in html
    assert (
        "@media (max-width: 760px){.desktop-overview{display:none}"
        ".mobile-overview{display:block}"
    ) in html
    mobile_roots = _mobile_svg_roots(html)
    assert len(mobile_roots) == 6
    for mobile_root in mobile_roots:
        _, _, view_width, view_height = (
            float(value) for value in mobile_root.attrib["viewBox"].split()
        )
        assert view_width == 390
        for rectangle in mobile_root.iter(f"{{{SVG_NAMESPACE}}}rect"):
            assert (
                float(rectangle.attrib.get("x", 0)) + float(rectangle.attrib["width"])
                <= view_width
            )
            assert (
                float(rectangle.attrib.get("y", 0)) + float(rectangle.attrib["height"])
                <= view_height
            )


def test_mobile_defaults_keep_counted_plot_groups_and_exact_records_collapsed() -> None:
    dashboard = build_formal_kernel_dashboard(PROJECT_ROOT)
    rendered = render_formal_kernel_dashboard_html(dashboard)

    assert (
        f'<div class="mobile-overview" data-summary-count="{len(dashboard.witnesses)}" '
        'data-group-count="6">' in rendered
    )
    assert rendered.count('class="mobile-plot-group" open') == 0
    assert "Groups start collapsed; use the index to open any group." in rendered
    assert (
        f'<details id="witnesses" class="record-collection" '
        f'data-detail-count="{len(dashboard.witnesses)}">' in rendered
    )
    assert '<details id="witnesses" class="record-collection" open' not in rendered
    assert f"Exact evaluated witness records · {len(dashboard.witnesses)}" in rendered
    assert rendered.count('data-mobile-witness-summary="') == len(dashboard.witnesses)
    assert rendered.count('<details class="witness-detail"') == len(dashboard.witnesses)
    assert "recordCollection.open=filtering" in rendered
    assert "recordCollection.open=true" in rendered
    collection_start = rendered.index('<details id="witnesses"')
    index_start = rendered.index('<nav class="detail-navigation"')
    records_start = rendered.index('<section class="record-list"')
    assert collection_start < index_start < records_start


def test_mobile_overview_uses_counted_three_plot_groups_with_direct_navigation() -> (
    None
):
    dashboard = build_formal_kernel_dashboard(PROJECT_ROOT)
    rendered = render_formal_kernel_dashboard_html(dashboard)
    groups = re.findall(
        r'(<svg xmlns="http://www.w3.org/2000/svg"[^>]+data-layout="mobile".*?</svg>)',
        rendered,
        re.DOTALL,
    )

    assert (
        f'<div class="mobile-overview" data-summary-count="{len(dashboard.witnesses)}" '
        'data-group-count="6">' in rendered
    )
    assert '<details class="mobile-overview"' not in rendered
    assert rendered.count('class="mobile-plot-group"') == 6
    assert rendered.count('class="mobile-plot-viewport"') == 6
    assert rendered.count('data-scroll-axis="vertical"') == 6
    assert rendered.count('data-mobile-group-jump="') == 6
    assert rendered.count('class="mobile-plot-group" open') == 0
    assert "16 plots in 6 groups · at most 3 plots per group" in rendered
    assert "Scroll inside an open group for its three complete plots." in rendered
    assert (
        ".mobile-plot-viewport{max-height:min(52vh,560px);overflow-y:auto;"
        "overflow-x:hidden" in rendered
    )
    assert len(groups) == 6
    assert rendered.count('data-mobile-witness-summary="') == len(dashboard.witnesses)
    group_sizes = []
    for group_index, group in enumerate(groups, 1):
        root = ElementTree.fromstring(group)
        _, _, width, height = (float(value) for value in root.attrib["viewBox"].split())
        assert width == 390
        assert height < 2600
        assert root.attrib["data-mobile-group"] == str(group_index)
        assert root.attrib["data-mobile-group-count"] == "6"
        group_sizes.append(
            sum(
                "data-mobile-witness-summary" in element.attrib
                for element in root.iter()
            )
        )
    assert group_sizes == [3, 3, 3, 3, 3, 1]
    assert "mobilePlotGroups.forEach(group=>group.open=group===target)" in rendered
    assert 'target.querySelector("summary").focus()' in rendered


def test_mobile_group_index_exposes_every_group_without_horizontal_discovery() -> None:
    rendered = render_formal_kernel_dashboard_html(
        build_formal_kernel_dashboard(PROJECT_ROOT)
    )
    index = re.search(r'<nav class="mobile-group-index".*?</nav>', rendered, re.DOTALL)

    assert index is not None
    expected_jumps = (
        ("Plots 1 through 3, 3 plots", "Plots 1–3"),
        ("Plots 4 through 6, 3 plots", "Plots 4–6"),
        ("Plots 7 through 9, 3 plots", "Plots 7–9"),
        ("Plots 10 through 12, 3 plots", "Plots 10–12"),
        ("Plots 13 through 15, 3 plots", "Plots 13–15"),
        ("Plots 16 through 16, 1 plots", "Plots 16–16"),
    )
    for group_index, (aria_label, link_text) in enumerate(expected_jumps, 1):
        assert (
            f'data-mobile-group-jump="{group_index}" '
            f'aria-label="{aria_label}">{link_text}</a>'
        ) in index.group(0)
    assert (
        ".mobile-group-index{display:grid;"
        "grid-template-columns:repeat(3,minmax(0,1fr))" in rendered
    )
    assert ".mobile-group-index{display:flex" not in rendered
    assert '.mobile-plot-group>summary::before{content:"▸"' in rendered
    assert '.mobile-plot-group[open]>summary::before{content:"▾"' in rendered


def test_mobile_groups_keep_a_persistent_vertical_scroll_affordance() -> None:
    rendered = render_formal_kernel_dashboard_html(
        build_formal_kernel_dashboard(PROJECT_ROOT)
    )

    assert rendered.count('class="mobile-plot-scroll-cue"') == 6
    assert rendered.count("Scroll within this group · 3 complete plots") == 5
    assert rendered.count("Scroll within this group · 1 complete plots") == 1
    assert ".mobile-plot-viewport{max-height:min(52vh,560px);" in rendered
    assert "scrollbar-gutter:stable" in rendered
    assert "box-shadow:inset 0 18px 14px -20px #1e3a8a" in rendered


def test_mobile_group_footer_copy_is_complete_and_fitted_to_two_lines() -> None:
    rendered = render_formal_kernel_dashboard_html(
        build_formal_kernel_dashboard(PROJECT_ROOT)
    )

    for group_index, root in enumerate(_mobile_svg_roots(rendered), 1):
        footer_lines = [
            " ".join(text.itertext())
            for text in root.iter(f"{{{SVG_NAMESPACE}}}text")
            if text.attrib.get("class") == "mobile-footer"
        ]
        assert footer_lines == [
            f"Group {group_index} · {3 if group_index <= 5 else 1} witnesses shown",
            "Exact values continue in accessible tables.",
        ]
        assert all("…" not in line for line in footer_lines)


def test_expanded_mobile_overview_uses_content_fitted_cards_without_dead_bands() -> (
    None
):
    dashboard = build_formal_kernel_dashboard(PROJECT_ROOT)
    rendered = render_formal_kernel_dashboard_html(dashboard)
    roots = _mobile_svg_roots(rendered)
    summaries = _mobile_summaries(rendered)
    card_heights: set[float] = set()

    assert len(summaries) == len(dashboard.witnesses)
    assert all(float(root.attrib["viewBox"].split()[-1]) < 2600 for root in roots)
    for summary in summaries:
        card = next(
            rectangle
            for rectangle in summary.iter(f"{{{SVG_NAMESPACE}}}rect")
            if rectangle.attrib.get("class") == "mobile-card"
        )
        plot = next(
            group
            for group in summary.iter(f"{{{SVG_NAMESPACE}}}g")
            if "data-plot-for" in group.attrib
        )
        boundary = next(
            text
            for text in summary.iter(f"{{{SVG_NAMESPACE}}}text")
            if text.attrib.get("class") == "mobile-boundary"
        )
        plot_y_values = [
            float(element.attrib[attribute])
            for element in plot.iter()
            for attribute in ("y", "cy", "y1", "y2")
            if attribute in element.attrib
        ]
        card_bottom = float(card.attrib["y"]) + float(card.attrib["height"])
        boundary_y = float(boundary.attrib["y"])
        card_heights.add(float(card.attrib["height"]))

        assert 16 <= boundary_y - max(plot_y_values) <= 40
        assert math.isclose(card_bottom - boundary_y, 18, abs_tol=0.01)
    assert len(card_heights) >= 4


def test_narrow_status_badges_have_a_separate_row_from_titles() -> None:
    dashboard = build_formal_kernel_dashboard(PROJECT_ROOT)
    html = render_formal_kernel_dashboard_html(dashboard)
    groups = _mobile_summaries(html)

    assert len(groups) == len(dashboard.witnesses)
    for group in groups:
        texts = list(group.iter(f"{{{SVG_NAMESPACE}}}text"))
        badges = [
            text
            for text in texts
            if text.attrib.get("class")
            in {"mobile-check-passed", "mobile-check-failed", "mobile-non-proof"}
        ]
        title_lines = [
            text for text in texts if text.attrib.get("class") == "mobile-card-title"
        ]
        assert len(badges) == 2
        assert max(float(badge.attrib["y"]) for badge in badges) + 16 <= min(
            float(text.attrib["y"]) for text in title_lines
        )


def test_narrow_cards_preserve_every_complete_witness_title() -> None:
    dashboard = build_formal_kernel_dashboard(PROJECT_ROOT)
    html = render_formal_kernel_dashboard_html(dashboard)
    groups = _mobile_summaries(html)

    assert len(groups) == len(dashboard.witnesses)
    for group, witness in zip(groups, dashboard.witnesses, strict=True):
        title = " ".join(
            text.text or ""
            for text in group.iter(f"{{{SVG_NAMESPACE}}}text")
            if text.attrib.get("class") == "mobile-card-title"
        )
        assert title == witness.title
        assert "…" not in title


def test_narrow_dashboard_heading_wraps_without_clipping_reader_title() -> None:
    dashboard = build_formal_kernel_dashboard(PROJECT_ROOT)
    rendered = render_formal_kernel_dashboard_html(dashboard)
    headings = [
        text
        for root in _mobile_svg_roots(rendered)
        for text in root.iter(f"{{{SVG_NAMESPACE}}}text")
        if text.attrib.get("class") == "mobile-title"
    ]

    assert len(headings) == 6
    for heading in headings:
        lines = [
            child.text or ""
            for child in heading
            if child.tag == f"{{{SVG_NAMESPACE}}}tspan"
        ]
        assert heading.attrib["data-reader-title"] == (
            "Formalism numerical witness workbench"
        )
        assert lines == ["Formalism numerical", "witness workbench"]
        assert " ".join(lines) == heading.attrib["data-reader-title"]
        assert all("…" not in line for line in lines)


def test_narrow_plots_keep_x_domains_and_negative_y_floors_visible() -> None:
    dashboard = build_formal_kernel_dashboard(PROJECT_ROOT)
    html = render_formal_kernel_dashboard_html(dashboard)
    x_domains = [
        text
        for root in _mobile_svg_roots(html)
        for text in root.iter(f"{{{SVG_NAMESPACE}}}text")
        if text.attrib.get("class") == "x-domain"
    ]
    line_minima = [
        text
        for root in _mobile_svg_roots(html)
        for text in root.iter(f"{{{SVG_NAMESPACE}}}text")
        if text.attrib.get("class") == "scale-minimum"
    ]

    assert len(x_domains) == len(dashboard.witnesses)
    assert len(line_minima) == sum(
        witness.plot.kind != "bar" for witness in dashboard.witnesses
    )
    assert any("-0.811" in " ".join(text.itertext()) for text in line_minima)
    assert (
        ".mobile-dashboard-svg .legend,.mobile-dashboard-svg .plot-note,"
        ".mobile-dashboard-svg .x-domain,.mobile-dashboard-svg .scale-zero,"
        ".mobile-dashboard-svg .scale-minimum,.mobile-dashboard-svg .scale-maximum"
        in html
    )


def test_plot_geometry_uses_readable_type_native_mobile_height_and_direct_legends() -> (
    None
):
    dashboard = build_formal_kernel_dashboard(PROJECT_ROOT)
    standalone = render_formal_kernel_dashboard_svg(dashboard)
    html = render_formal_kernel_dashboard_html(dashboard)
    mobile = MOBILE_SVG_PATTERN.findall(html)[0]
    mobile_roots = _mobile_svg_roots(html)
    standalone_root = ElementTree.fromstring(standalone)

    assert ".axis-label{fill:#334155;font:750 16px" in standalone
    assert re.search(r"\.legend,[^\n]+font:650 15px", standalone)
    assert ".axis-label{fill:#334155;font:750 15px" in mobile
    assert re.search(r"\.legend,[^\n]+font:650 14px", mobile)
    desktop_plots = [
        group
        for group in standalone_root.iter(f"{{{SVG_NAMESPACE}}}g")
        if "data-plot-for" in group.attrib
    ]
    mobile_plots = [
        group
        for mobile_root in mobile_roots
        for group in mobile_root.iter(f"{{{SVG_NAMESPACE}}}g")
        if "data-plot-for" in group.attrib
    ]
    assert len(desktop_plots) == len(mobile_plots) == len(dashboard.witnesses)
    assert all(
        group.attrib["data-legend-layout"] == "direct" for group in desktop_plots
    )
    assert all(
        group.attrib["data-legend-layout"] == "stacked" for group in mobile_plots
    )
    assert all(
        float(group.attrib["data-native-plot-height"]) >= 170 for group in mobile_plots
    )


def test_publication_scale_metadata_and_boolean_category_keys_use_large_type() -> None:
    dashboard = build_formal_kernel_dashboard(PROJECT_ROOT)
    standalone = render_formal_kernel_dashboard_svg(dashboard)
    html = render_formal_kernel_dashboard_html(dashboard)
    mobile = MOBILE_SVG_PATTERN.findall(html)[0]
    mobile_root = _mobile_root_for(html, "causal-intervention-invariance")

    assert ".family{fill:#475569;font:650 15px" in standalone
    assert ".metric{fill:#334155;font:700 15px" in standalone
    assert ".axis-label{fill:#334155;font:750 16px" in standalone
    assert re.search(r"\.legend,[^\n]+font:650 15px", standalone)
    assert ".category-tick{fill:#334155;font:800 15px" in standalone
    assert ".category-key-item{fill:#334155;font:700 15px" in standalone
    assert ".mobile-family{fill:#475569;font:650 14px" in mobile
    assert ".mobile-metric{fill:#334155;font:700 14px" in mobile
    assert ".axis-label{fill:#334155;font:750 15px" in mobile
    assert re.search(r"\.legend,[^\n]+font:650 14px", mobile)
    assert ".category-tick{fill:#334155;font:800 15px" in mobile
    assert ".category-key-item{fill:#334155;font:700 15px" in mobile

    boolean_root = next(
        group
        for group in mobile_root.iter(f"{{{SVG_NAMESPACE}}}g")
        if group.attrib.get("data-plot-for") == "causal-intervention-invariance"
    )
    keys = [
        text
        for text in boolean_root.iter(f"{{{SVG_NAMESPACE}}}text")
        if text.attrib.get("class") == "category-key-item"
    ]
    assert boolean_root.attrib["data-category-key-columns"] == "1"
    assert [key.attrib["data-category-label"] for key in keys] == ["C1", "C2"]
    assert [key.attrib["data-category-value"] for key in keys] == [
        "do(root=false)",
        "do(root=true)",
    ]
    assert len({key.attrib["x"] for key in keys}) == 1
    assert float(keys[1].attrib["y"]) - float(keys[0].attrib["y"]) >= 20


def test_embedded_desktop_and_mobile_svg_typography_is_scoped_per_layout() -> None:
    rendered = render_formal_kernel_dashboard_html(
        build_formal_kernel_dashboard(PROJECT_ROOT)
    )

    assert 'class="dashboard-svg"' in rendered
    assert rendered.count('class="mobile-dashboard-svg"') == 6
    assert ".dashboard-svg .axis-label{fill:#334155;font:750 16px" in rendered
    assert ".dashboard-svg .legend,.dashboard-svg .plot-note" in rendered
    assert ".mobile-dashboard-svg .axis-label{fill:#334155;font:750 15px" in rendered
    assert ".mobile-dashboard-svg .legend,.mobile-dashboard-svg .plot-note" in rendered
    assert "}.axis-label{" not in rendered
    assert "}.legend,.plot-note" not in rendered


def test_long_desktop_y_axis_labels_wrap_inside_their_card() -> None:
    dashboard = build_formal_kernel_dashboard(PROJECT_ROOT)
    root = ElementTree.fromstring(render_formal_kernel_dashboard_svg(dashboard))
    witness = next(
        witness
        for witness in dashboard.witnesses
        if witness.id == "causal-intervention-invariance"
    )
    summary = next(
        group
        for group in root.iter(f"{{{SVG_NAMESPACE}}}g")
        if group.attrib.get("data-witness-summary") == witness.id
    )
    card = next(
        rectangle
        for rectangle in summary.iter(f"{{{SVG_NAMESPACE}}}rect")
        if rectangle.attrib.get("class") == "card"
    )
    y_axis = next(
        text
        for text in summary.iter(f"{{{SVG_NAMESPACE}}}text")
        if "axis-y-label" in text.attrib.get("class", "")
    )
    visible_lines = [
        child.text or "" for child in y_axis if child.tag == f"{{{SVG_NAMESPACE}}}tspan"
    ]
    columns = {column.key: column for column in witness.columns}
    expected = (
        "y · "
        + " / ".join(columns[key].label for key in witness.plot.y_keys)
        + " · unit: dimensionless"
    )
    card_right = float(card.attrib["x"]) + float(card.attrib["width"])

    assert " ".join(visible_lines) == expected
    assert all("…" not in line for line in visible_lines)
    assert all(
        float(tspan.attrib["x"]) + len(tspan.text or "") * 8 <= card_right - 12
        for tspan in y_axis
        if tspan.tag == f"{{{SVG_NAMESPACE}}}tspan"
    )


def test_dashboard_status_boundary_residuals_and_title_are_reader_facing() -> None:
    dashboard = build_formal_kernel_dashboard(PROJECT_ROOT)
    svg = render_formal_kernel_dashboard_svg(dashboard)
    html = render_formal_kernel_dashboard_html(dashboard)
    reader_title = "Formalism numerical witness workbench"

    assert svg.count("TYPED CHECKS PASSED") == len(dashboard.witnesses)
    assert svg.count("NON-PROOF WITNESS") >= len(dashboard.witnesses)
    assert html.count("TYPED CHECKS PASSED") >= len(dashboard.witnesses) * 3
    assert html.count(dashboard.numerical_evidence_boundary) == 1
    assert "NON-PROOF WITNESS · explanatory typed checks only" in html
    assert f'<title id="dashboard-title">{reader_title}</title>' in svg
    assert f'<text class="title" x="40" y="52">{reader_title}</text>' in svg
    assert f"<title>{reader_title}</title>" in html
    assert f"<h1>{reader_title}</h1>" in html

    nonzero = next(
        witness
        for witness in dashboard.witnesses
        if 0 < max(check.residual for check in witness.checks) < 1e-3
    )
    exact_residual = repr(max(check.residual for check in nonzero.checks))
    summary = re.search(
        rf'<g class="witness-summary"[^>]+data-witness-id="{nonzero.id}".*?</g>',
        svg,
        re.DOTALL,
    )
    assert summary is not None
    assert re.search(r"max residual [1-9]\.[0-9]{2}e-\d+", summary.group(0))
    assert exact_residual in summary.group(0)


def test_narrow_details_wrap_identifiers_and_signal_wide_data_tables() -> None:
    dashboard = build_formal_kernel_dashboard(PROJECT_ROOT)
    html = render_formal_kernel_dashboard_html(dashboard)

    assert html.count('class="table-scroll-hint"') == 3 * len(dashboard.witnesses)
    assert "Swipe horizontally for all evaluated columns" in html
    assert ".parameter-table{min-width:max(420px,100%);table-layout:auto}" in html
    assert "word-break:break-word" in html
    assert "overflow-wrap:anywhere" in html


def test_narrow_exact_tables_scroll_without_breaking_identifiers_or_numbers() -> None:
    dashboard = build_formal_kernel_dashboard(PROJECT_ROOT)
    rendered = render_formal_kernel_dashboard_html(dashboard)

    assert rendered.count('class="table-wrap exact-scroll"') == (
        3 * len(dashboard.witnesses)
    )
    assert rendered.count('data-scroll-axis="horizontal"') == (
        3 * len(dashboard.witnesses)
    )
    assert rendered.count('class="table-scroll-hint"') == (3 * len(dashboard.witnesses))
    assert "← Swipe horizontally for exact parameters →" in rendered
    assert "← Swipe horizontally for every typed numerical check →" in rendered
    assert "← Swipe horizontally for all evaluated columns →" in rendered
    assert rendered.count("exact-table") >= 3 * len(dashboard.witnesses)
    assert (
        ".witness-workbench .exact-table th,.witness-workbench .exact-table td,"
        ".witness-workbench .exact-table code{white-space:nowrap;"
        "overflow-wrap:normal;word-break:normal" in rendered
    )
    assert (
        ".parameter-table th,.parameter-table td{width:50%;word-break:break-word}"
        not in rendered
    )
    for witness in dashboard.witnesses:
        for key, value in witness.parameters:
            assert f"<code>{key}</code>" in rendered
            expected = str(value).lower() if isinstance(value, bool) else repr(value)
            assert f"<td>{expected}</td>" in rendered


def test_narrow_workbench_contains_table_min_content_without_hiding_overflow() -> None:
    dashboard = build_formal_kernel_dashboard(PROJECT_ROOT)
    rendered = render_formal_kernel_dashboard_html(dashboard)

    assert ".workbench-grid>*{min-width:0;max-width:100%}" in rendered
    assert ".exact-scroll{min-width:0;max-width:100%;overflow-x:auto}" in rendered
    assert ".theorem-group{min-width:0;max-width:100%;overflow-x:auto}" in rendered
    assert ".witness-detail,.witness-detail>*{min-width:0;max-width:100%}" in rendered
    assert rendered.count('class="theorem-group"') == len(dashboard.witnesses)
    assert "body{overflow-x:hidden}" not in rendered
    assert "html{overflow-x:hidden}" not in rendered


def test_narrow_filter_controls_are_constrained_to_the_mobile_viewport() -> None:
    html = render_formal_kernel_dashboard_html(
        build_formal_kernel_dashboard(PROJECT_ROOT)
    )

    assert ".field{display:grid;gap:4px;min-width:0}" in html
    assert "width:100%;min-width:0;max-width:100%" in html


def test_detail_records_are_counted_collapsed_and_opened_by_navigation_or_filter() -> (
    None
):
    dashboard = build_formal_kernel_dashboard(PROJECT_ROOT)
    rendered = render_formal_kernel_dashboard_html(dashboard)

    assert rendered.count('<details class="witness-detail"') == len(dashboard.witnesses)
    assert '<details class="witness-detail" open' not in rendered
    assert rendered.count('class="witness-detail-summary"') == len(dashboard.witnesses)
    assert (
        f'<details class="detail-index" data-detail-count="{len(dashboard.witnesses)}">'
        in rendered
    )
    assert (
        f"Browse {len(dashboard.witnesses)} collapsed numerical witness records"
        in rendered
    )
    assert rendered.count('data-detail-jump="') == len(dashboard.witnesses)
    for witness in dashboard.witnesses:
        assert f'href="#witness-detail-{witness.id}"' in rendered

    assert (
        'const records=[...document.querySelectorAll(".witness-detail")];' in rendered
    )
    assert "record.open=filtering&&show" in rendered
    assert "overview.hidden=filtering" in rendered
    assert "target.open=true" in rendered
    assert 'target.querySelector("summary").focus()' in rendered
    assert "matching detail records expanded below" in rendered


def test_html_is_a_filtered_exact_family_numerical_workbench() -> None:
    dashboard = build_formal_kernel_dashboard(PROJECT_ROOT)
    html = render_formal_kernel_dashboard_html(dashboard)
    decoded_html = html_lib.unescape(html)
    row_count = sum(len(witness.rows) for witness in dashboard.witnesses)
    mirror_count = sum(len(witness.theorem_mirrors) for witness in dashboard.witnesses)

    assert html.startswith("<!doctype html>")
    assert 'id="witness-search"' in html
    assert 'id="witness-family-filter"' in html
    assert 'id="witness-status-filter"' in html
    assert 'aria-keyshortcuts="/ Escape"' in html
    assert html.count('class="witness-workbench"') == len(dashboard.witnesses)
    assert html.count('data-witness-id="') == len(dashboard.witnesses) * 2
    assert html.count('data-witness-row="') == row_count
    assert html.count('data-theorem-mirror="') == mirror_count
    assert html.count('class="witness-data exact-table"') == len(dashboard.witnesses)
    assert html.count('class="parameter-table exact-table"') == len(dashboard.witnesses)
    check_count = sum(len(witness.checks) for witness in dashboard.witnesses)
    assert html.count('data-numerical-check="') == check_count
    assert html.count("Numerical checks") >= len(dashboard.witnesses)
    assert html.count("Boundary observed") >= len(dashboard.witnesses)
    assert "Theorem mirrors" in html
    assert "Exact evaluated data" in html
    assert "Lean proof receipts" in html
    assert "empirical validation" in html
    assert 'aria-live="polite"' in html
    assert 'addEventListener("keydown"' in html
    assert "@media (max-width: 760px)" in html
    assert "<script src=" not in html
    assert html.replace(SVG_NAMESPACE, "").count("http://") == 0
    assert "https://" not in html

    for witness in dashboard.witnesses:
        assert witness.invariant in decoded_html
        assert witness.boundary_behavior in decoded_html
        for check in witness.checks:
            assert check.id in decoded_html
            assert check.relation in decoded_html
            assert repr(check.lhs).lower() in decoded_html.lower()
            assert repr(check.rhs).lower() in decoded_html.lower()
            assert repr(check.tolerance) in decoded_html
            assert repr(check.residual) in decoded_html
        for theorem in witness.theorem_mirrors:
            assert theorem in decoded_html
        for row in witness.rows:
            for value in row.values:
                expected = (
                    str(value).lower() if isinstance(value, bool) else repr(value)
                )
                assert expected in decoded_html


def test_dashboard_writer_and_drift_check_are_deterministic(tmp_path: Path) -> None:
    assert len(formal_kernel_dashboard_drift(PROJECT_ROOT, output_root=tmp_path)) == 2
    svg_path, html_path = write_formal_kernel_dashboard(
        PROJECT_ROOT, output_root=tmp_path
    )
    assert svg_path.read_text(encoding="utf-8").startswith("<svg")
    assert html_path.read_text(encoding="utf-8").startswith("<!doctype html>")
    assert formal_kernel_dashboard_drift(PROJECT_ROOT, output_root=tmp_path) == ()
    html_path.write_text("stale\n", encoding="utf-8")
    assert formal_kernel_dashboard_drift(PROJECT_ROOT, output_root=tmp_path) == (
        html_path,
    )
