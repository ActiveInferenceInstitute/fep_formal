"""The formalism atlas is a scalable projection of the shared presentation."""

from __future__ import annotations

import html as html_lib
import re
from dataclasses import replace
from pathlib import Path
from xml.etree import ElementTree

from fep_lean.output.formalism_atlas import (
    atlas_projection_drift,
    build_formalism_atlas,
    render_formalism_atlas_html,
    render_formalism_atlas_svg,
    write_formalism_atlas,
)
from fep_lean.output.formalism_presentation import (
    FormalismPresentation,
    PresentationRelation,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SVG_NAMESPACE = "http://www.w3.org/2000/svg"


def test_atlas_uses_the_shared_data_driven_presentation_model() -> None:
    atlas = build_formalism_atlas(PROJECT_ROOT)

    assert isinstance(atlas, FormalismPresentation)
    assert len(atlas.topics) == atlas.metrics["topics"]
    assert len(atlas.relations) == atlas.metrics["authored_relation_edges"]
    assert len(atlas.areas) == 5
    assert sum(len(area.topic_ids) for area in atlas.areas) == len(atlas.topics)
    assert sum(
        len(family.topic_ids) for family in atlas.families if family.area is not None
    ) == len(atlas.topics)


def test_static_svg_is_a_compact_area_family_relation_summary() -> None:
    atlas = build_formalism_atlas(PROJECT_ROOT)
    svg = render_formalism_atlas_svg(atlas)
    topic_families = [family for family in atlas.families if family.area is not None]
    relation_kinds = {relation.kind for relation in atlas.relations}

    assert svg.startswith(f'<svg xmlns="{SVG_NAMESPACE}"')
    assert 'role="img"' in svg
    assert svg.count('data-area-summary="') == len(atlas.areas)
    assert svg.count('data-family-summary="') == len(topic_families)
    assert svg.count('data-relation-kind="') == len(relation_kinds)
    assert 'class="topic-card"' not in svg
    assert 'data-topic-id="' not in svg
    assert f"{len(atlas.topics)} canonical topics" in svg
    assert "Authored scientific relations" in svg
    assert "Deterministic numerical witnesses" in svg
    assert "non-proof evidence" in svg
    assert "not Lean proof receipts or empirical validation" in svg
    assert "https://" not in svg
    assert "<image" not in svg and "<script" not in svg
    assert svg.replace(SVG_NAMESPACE, "").count("http://") == 0


def test_atlas_family_witness_summaries_distinguish_formal_alignment() -> None:
    atlas = build_formalism_atlas(PROJECT_ROOT)
    svg = render_formalism_atlas_svg(atlas)
    html = render_formalism_atlas_html(atlas)
    root = ElementTree.fromstring(svg)
    learning_family = next(
        family
        for family in atlas.families
        if family.id == "learning-concentration-and-model-evidence"
    )
    theorem_witness = next(
        witness
        for witness in atlas.witnesses
        if witness.formal_alignment == "theorem_instance"
    )
    structural_group = next(
        group
        for group in root.iter(f"{{{SVG_NAMESPACE}}}g")
        if group.attrib.get("data-family-summary") == learning_family.id
    )
    theorem_group = next(
        group
        for group in root.iter(f"{{{SVG_NAMESPACE}}}g")
        if group.attrib.get("data-family-summary") == theorem_witness.family
    )

    assert structural_group.attrib["data-formal-alignments"] == (
        "structural_analogue:1"
    )
    assert "1 structural analogue" in " ".join(structural_group.itertext())
    assert theorem_group.attrib["data-formal-alignments"] == "theorem_instance:1"
    assert "1 theorem instance" in " ".join(theorem_group.itertext())
    assert (
        f'data-mobile-family-summary="{learning_family.id}" '
        'data-formal-alignments="structural_analogue:1"'
    ) in html
    assert "15 theorem instances · 1 structural analogue" in html


def test_standalone_svg_uses_a_tight_page_geometry_without_capture_bands() -> None:
    svg = render_formalism_atlas_svg(build_formalism_atlas(PROJECT_ROOT))
    root = ElementTree.fromstring(svg)
    _, _, width, height = (float(value) for value in root.attrib["viewBox"].split())

    assert root.attrib["width"] == str(int(width))
    assert root.attrib["height"] == str(int(height))
    assert 1.2 <= width / height <= 1.5


def test_html_has_exact_accessible_tables_and_offline_interactions() -> None:
    atlas = build_formalism_atlas(PROJECT_ROOT)
    html = render_formalism_atlas_html(atlas)
    decoded_html = html_lib.unescape(html)
    dependency_count = sum(
        len(module.formal_dependencies) for module in atlas.formal_modules
    )

    assert html.startswith("<!doctype html>")
    assert 'id="atlas-search"' in html
    assert 'id="area-filter"' in html
    assert 'id="family-filter"' in html
    assert 'id="status-filter"' in html
    assert 'id="relation-filter"' in html
    assert 'id="atlas-viewport"' in html
    assert 'class="viewport" tabindex="0"' in html
    assert 'aria-keyshortcuts="/ Escape"' in html
    assert 'data-pan-direction="left"' in html
    assert 'data-pan-direction="right"' in html
    assert 'data-zoom="in"' in html
    assert 'data-zoom="out"' in html
    assert 'data-zoom="reset"' in html
    assert ".canvas{width:100%" in html
    assert ".viewport{overflow:auto;touch-action:none" in html
    assert ".viewport{overflow:auto;max-height" not in html
    assert ".table-wrap{overflow:auto;max-height" not in html
    assert "canvas.style.width=`${zoom*100}%`" in html
    assert html.count('data-topic-row="') == len(atlas.topics)
    assert html.count('data-relation-row="') == len(atlas.relations)
    assert html.count('data-capability-row="') == len(atlas.capabilities)
    assert html.count('data-module-row="') == len(atlas.formal_modules)
    assert html.count('data-dependency-row="') == dependency_count
    assert "Assumptions / scope" in html
    assert "Non-vacuity" in html
    assert "Exact authored relation table" in html
    assert "Code dependencies are not scientific relations" in html
    assert 'aria-live="polite"' in html
    assert 'addEventListener("keydown"' in html
    assert 'addEventListener("pointerdown"' in html
    assert "scrollBy" in html
    assert "@media (max-width: 760px)" in html
    assert "<script src=" not in html
    assert html.replace(SVG_NAMESPACE, "").count("http://") == 0
    assert "https://" not in html

    final_topic = atlas.topics[-1]
    assert final_topic.id in decoded_html
    assert final_topic.primary_theorem in decoded_html
    assert final_topic.invariant in decoded_html
    if atlas.relations:
        final_relation = atlas.relations[-1]
        assert final_relation.rationale in decoded_html
        if final_relation.witness is not None:
            assert final_relation.witness in decoded_html


def test_narrow_atlas_has_a_single_column_summary_with_all_five_areas() -> None:
    atlas = build_formalism_atlas(PROJECT_ROOT)
    html = render_formalism_atlas_html(atlas)

    assert html.count('data-mobile-area-summary="') == 5
    for area in atlas.areas:
        assert f'data-mobile-area-summary="{area.id}"' in html
    assert 'class="mobile-summary"' in html
    assert ".mobile-summary{display:none}" in html
    assert (
        "@media (max-width: 760px){.desktop-summary{display:none}"
        ".mobile-summary{display:block}"
    ) in html
    match = re.search(
        r'(<svg xmlns="http://www.w3.org/2000/svg"[^>]+data-layout="mobile".*?</svg>)',
        html,
        re.DOTALL,
    )
    assert match is not None
    mobile_root = ElementTree.fromstring(match.group(1))
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


def test_narrow_atlas_uses_reader_scale_type_and_wrapping_disposition_chips() -> None:
    atlas = build_formalism_atlas(PROJECT_ROOT)
    html = render_formalism_atlas_html(atlas)
    match = re.search(
        r'(<svg xmlns="http://www.w3.org/2000/svg"[^>]+data-layout="mobile".*?</svg>)',
        html,
        re.DOTALL,
    )
    assert match is not None
    mobile_svg = match.group(1)
    mobile_root = ElementTree.fromstring(mobile_svg)

    assert ".mobile-family-name{fill:#0f172a;font:700 16px" in mobile_svg
    for css_class in (
        "mobile-subtitle",
        "mobile-area-count",
        "mobile-family-count",
        "mobile-relation-count",
    ):
        assert re.search(rf"\.{css_class}{{[^}}]*font:[^;]*14px", mobile_svg)
    assert (
        f"Five areas · {len(atlas.families)} families · "
        f"{len(atlas.relations)} relations"
    ) in mobile_svg
    assert "vertically complete · no horizontal crop" in mobile_svg

    chip_groups = [
        group
        for group in mobile_root.iter(f"{{{SVG_NAMESPACE}}}g")
        if "data-disposition-chip" in group.attrib
    ]
    assert len(chip_groups) == sum(len(area.disposition_counts) for area in atlas.areas)
    assert any(group.attrib["data-chip-row"] == "1" for group in chip_groups)
    for group in chip_groups:
        rectangle = group.find(f"{{{SVG_NAMESPACE}}}rect")
        label = group.find(f"{{{SVG_NAMESPACE}}}text")
        assert rectangle is not None and label is not None
        assert float(rectangle.attrib["width"]) > 0
        assert "…" not in "".join(label.itertext())


def test_atlas_navigation_and_semantic_key_use_reader_facing_labels() -> None:
    atlas = build_formalism_atlas(PROJECT_ROOT)
    svg = render_formalism_atlas_svg(atlas)
    html = render_formalism_atlas_html(atlas)
    root = ElementTree.fromstring(svg)

    status_key = next(
        group
        for group in root.iter(f"{{{SVG_NAMESPACE}}}g")
        if group.attrib.get("data-semantic-status-key") == "true"
    )
    key_text = " ".join(text.strip() for text in status_key.itertext() if text.strip())
    for disposition in {topic.semantic_disposition for topic in atlas.topics}:
        assert disposition.replace("_", " ").title() in key_text

    for label in (
        "← Pan left",
        "Pan right →",
        "↑ Pan up",
        "Pan down ↓",
        "− Zoom out",
        "Reset view",
        "+ Zoom in",
    ):
        assert f">{label}</button>" in html
    assert f"{len(atlas.topics)} topics matched" in html
    assert "relations matched`" in html
    assert "relations visible`" not in html


def test_narrow_atlas_preserves_the_complete_numerical_evidence_boundary() -> None:
    atlas = build_formalism_atlas(PROJECT_ROOT)
    html = render_formalism_atlas_html(atlas)
    match = re.search(
        r'(<svg xmlns="http://www.w3.org/2000/svg"[^>]+data-layout="mobile".*?</svg>)',
        html,
        re.DOTALL,
    )
    assert match is not None
    mobile_root = ElementTree.fromstring(match.group(1))
    boundary_lines = [
        "".join(node.itertext())
        for node in mobile_root.iter(f"{{{SVG_NAMESPACE}}}text")
        if node.attrib.get("class") == "mobile-boundary-text"
    ]

    assert " ".join(boundary_lines) == atlas.numerical_evidence_boundary
    assert all("…" not in line for line in boundary_lines)


def test_narrow_relation_summary_wraps_new_data_driven_kinds_inside_viewbox() -> None:
    atlas = build_formalism_atlas(PROJECT_ROOT)
    expanded = replace(
        atlas,
        relations=(
            *atlas.relations,
            PresentationRelation(
                source="fep-001",
                target="fep-002",
                kind="formal_pairing",
                rationale="Synthetic renderer probe for a third authored kind.",
                witness="FEPComposed.synthetic_pairing_probe",
            ),
        ),
    )
    html = render_formalism_atlas_html(expanded)
    match = re.search(
        r'(<svg xmlns="http://www.w3.org/2000/svg"[^>]+data-layout="mobile".*?</svg>)',
        html,
        re.DOTALL,
    )
    assert match is not None
    mobile_root = ElementTree.fromstring(match.group(1))
    _, _, view_width, view_height = (
        float(value) for value in mobile_root.attrib["viewBox"].split()
    )
    relation_rectangles = [
        rectangle
        for rectangle in mobile_root.iter(f"{{{SVG_NAMESPACE}}}rect")
        if rectangle.attrib.get("class") == "mobile-relation"
    ]

    assert len(relation_rectangles) == 3
    for rectangle in relation_rectangles:
        assert (
            float(rectangle.attrib["x"]) + float(rectangle.attrib["width"])
            <= view_width
        )
        assert (
            float(rectangle.attrib["y"]) + float(rectangle.attrib["height"])
            <= view_height
        )


def test_narrow_topic_rows_become_readable_cards_and_other_tables_signal_scroll() -> (
    None
):
    atlas = build_formalism_atlas(PROJECT_ROOT)
    html = render_formalism_atlas_html(atlas)

    assert html.count('data-label="Area"') == len(atlas.topics)
    assert html.count('data-label="Primary theorem"') == len(atlas.topics)
    assert html.count('class="topic-review"') == len(atlas.topics) * 3
    assert re.search(
        r"#topic-table tbody tr,#relation-table tbody tr\{display:block", html
    )
    assert re.search(
        r"#topic-table td::before,#relation-table td::before"
        r"\{content:attr\(data-label\)",
        html,
    )
    assert "Swipe horizontally to inspect every column." in html


def test_narrow_relation_rows_are_complete_cards_without_offscreen_evidence() -> None:
    atlas = build_formalism_atlas(PROJECT_ROOT)
    rendered = render_formalism_atlas_html(atlas)
    decoded = html_lib.unescape(rendered)

    assert 'id="relation-table" data-mobile-layout="complete-cards"' in rendered
    assert re.search(r"#topic-table,#relation-table\{min-width:0}", rendered)
    assert re.search(
        r"#topic-table tbody tr,#relation-table tbody tr\{display:block", rendered
    )
    assert "Complete relation cards show rationale and exact witnesses." in rendered
    for index, relation in enumerate(atlas.relations):
        match = re.search(
            rf'<tr data-relation-row="{index}".*?</tr>', decoded, re.DOTALL
        )
        assert match is not None
        card = match.group(0)
        assert relation.source in card
        assert relation.target in card
        assert relation.rationale in card
        assert 'data-label="Rationale"' in card
        assert 'data-label="Exact witness"' in card
        if relation.witness is not None:
            assert relation.witness in card


def test_atlas_initial_page_is_compact_with_counted_section_navigation() -> None:
    atlas = build_formalism_atlas(PROJECT_ROOT)
    rendered = render_formalism_atlas_html(atlas)

    assert '<nav class="atlas-jumps" aria-label="Atlas sections">' in rendered
    assert f'href="#topic-records">{len(atlas.topics)} topics</a>' in rendered
    assert f'href="#relation-records">{len(atlas.relations)} relations</a>' in rendered
    assert (
        f'<details id="topic-records"><summary>Canonical topic table · '
        f"{len(atlas.topics)} topics</summary>"
    ) in rendered
    assert (
        f'<details id="relation-records"><summary>Exact authored relation table · '
        f"{len(atlas.relations)} relations</summary>"
    ) in rendered
    assert '<details open id="topic-records">' not in rendered
    assert '<details open id="relation-records">' not in rendered
    assert "topicSection.open=true" in rendered
    assert "relationSection.open=true" in rendered
    assert rendered.count('data-topic-row="') == len(atlas.topics)
    assert rendered.count('data-relation-row="') == len(atlas.relations)


def test_atlas_writer_and_drift_check_are_deterministic(tmp_path: Path) -> None:
    assert len(atlas_projection_drift(PROJECT_ROOT, output_root=tmp_path)) == 2
    svg_path, html_path = write_formalism_atlas(PROJECT_ROOT, output_root=tmp_path)
    assert svg_path.read_text(encoding="utf-8").startswith("<svg")
    assert html_path.read_text(encoding="utf-8").startswith("<!doctype html>")
    assert atlas_projection_drift(PROJECT_ROOT, output_root=tmp_path) == ()
    html_path.write_text("stale\n", encoding="utf-8")
    assert atlas_projection_drift(PROJECT_ROOT, output_root=tmp_path) == (html_path,)
