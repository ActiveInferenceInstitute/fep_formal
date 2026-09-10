"""Scalable offline atlas projections of the shared formalism presentation."""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from typing import TypeAlias

from fep_lean.output.formalism_presentation import (
    FormalismPresentation,
    PresentationFamily,
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

ATLAS_SVG = Path("docs/formalism-atlas.svg")
ATLAS_HTML = Path("docs/formalism-atlas.html")

FormalismAtlas: TypeAlias = FormalismPresentation

_AREA_PALETTE = (
    ("#0f766e", "#ccfbf1"),
    ("#1d4ed8", "#dbeafe"),
    ("#7c3aed", "#ede9fe"),
    ("#b45309", "#fef3c7"),
    ("#be123c", "#ffe4e6"),
)
_STATUS_COLORS = ("#0f766e", "#2563eb", "#7c3aed", "#d97706", "#be123c")


def build_formalism_atlas(project_root: Path) -> FormalismAtlas:
    """Return the shared immutable presentation used by both atlas projections."""
    return build_formalism_presentation(Path(project_root))








def _status_summary(counts: Mapping[str, int]) -> str:
    return " · ".join(f"{humanize_identifier(str(key))} {value}" for key, value in counts.items())


def _formal_alignment_summary(counts: Mapping[str, int]) -> str:
    if not counts:
        return "0 numerical witnesses"
    ordered = sorted(counts, key=lambda key: (key == "structural_analogue", key))
    return " · ".join(
        f"{counts[key]} {humanize_identifier(key).lower()}{'s' if counts[key] != 1 else ''}"
        for key in ordered
    )


def _formal_alignment_data(counts: Mapping[str, int]) -> str:
    if not counts:
        return "none"
    return ",".join(f"{key}:{counts[key]}" for key in sorted(counts))


def _disposition_chip_layout(
    counts: Mapping[str, int], *, available_width: float
) -> tuple[tuple[str, str, int, float, float], ...]:
    """Lay out complete disposition labels in wrapping rows without truncation."""
    gap = 7.0
    row = 0
    cursor = 0.0
    layout: list[tuple[str, str, int, float, float]] = []
    for disposition, count in sorted(counts.items()):
        label = f"{humanize_identifier(disposition)} · {count}"
        chip_width = min(available_width, max(92.0, 24.0 + len(label) * 7.2))
        if cursor and cursor + chip_width > available_width:
            row += 1
            cursor = 0.0
        layout.append((disposition, label, row, cursor, chip_width))
        cursor += chip_width + gap
    return tuple(layout)


def _family_by_area(
    atlas: FormalismAtlas,
) -> dict[str, tuple[PresentationFamily, ...]]:
    return {
        area.id: tuple(family for family in atlas.families if family.area == area.id)
        for area in atlas.areas
    }




def render_formalism_atlas_svg(atlas: FormalismAtlas) -> str:
    """Render a compact area/family/relation summary, never a topic-card sheet."""
    families_by_area = _family_by_area(atlas)
    width = 1600
    area_columns = 3
    area_width = 493
    area_gap = 20
    family_step = 66
    area_positions: dict[str, tuple[int, int]] = {}
    area_y = 142
    for row_start in range(0, len(atlas.areas), area_columns):
        row = atlas.areas[row_start : row_start + area_columns]
        row_width = len(row) * area_width + (len(row) - 1) * area_gap
        row_x = (width - row_width) // 2
        row_families = max((len(families_by_area[area.id]) for area in row), default=0)
        for column, area in enumerate(row):
            area_positions[area.id] = (
                row_x + column * (area_width + area_gap),
                area_y,
            )
        area_y += 136 + row_families * family_step + 24
    relation_y = area_y + 8
    height = relation_y + 228
    relation_counts = Counter(relation.kind for relation in atlas.relations)
    alignment_counts: Counter[str] = Counter(
        witness.formal_alignment for witness in atlas.witnesses
    )
    dispositions = sorted({topic.semantic_disposition for topic in atlas.topics})
    metadata = {
        "schema_version": atlas.schema_version,
        "review_date": atlas.review_date,
        "topic_count": len(atlas.topics),
        "area_ids": [area.id for area in atlas.areas],
        "family_ids": [
            family.id for family in atlas.families if family.area is not None
        ],
        "relation_counts": dict(sorted(relation_counts.items())),
        "witness_count": len(atlas.witnesses),
        "formal_alignment_counts": dict(sorted(alignment_counts.items())),
        "evidence_kind": "deterministic_numerical_witness_non_proof_evidence",
    }
    lines = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" '
            'role="img" aria-labelledby="atlas-title atlas-description">'
        ),
        '<title id="atlas-title">Formalism composition atlas summary</title>',
        (
            '<desc id="atlas-description">Five broad areas summarize canonical '
            "topic families and semantic dispositions. Authored relation counts are "
            "reported separately from formal-module code dependencies. "
            f"{escape_svg_text(atlas.structural_evidence_boundary)} "
            f"{escape_svg_text(atlas.numerical_evidence_boundary)}</desc>"
        ),
        f"<metadata>{escape_svg_text(json.dumps(metadata, sort_keys=True, separators=(',', ':')))}</metadata>",
        """<style>
            .background{fill:#f8fafc}.title{fill:#0f172a;font:800 34px system-ui,sans-serif}
            .subtitle{fill:#475569;font:500 16px system-ui,sans-serif}.area-card{fill:#fff;stroke-width:2}
            .area-name{font:800 19px system-ui,sans-serif}.area-count{fill:#334155;font:650 14px system-ui,sans-serif}
            .family-card{fill:#fff;stroke:#cbd5e1;stroke-width:1}.family-name{fill:#0f172a;font:700 13px system-ui,sans-serif}
            .family-count{fill:#475569;font:550 12px system-ui,sans-serif}.section{fill:#0f172a;font:800 19px system-ui,sans-serif}
            .relation-card{fill:#fff;stroke:#cbd5e1;stroke-width:1.5}.relation-kind{fill:#0f172a;font:800 15px system-ui,sans-serif}
            .relation-count{fill:#334155;font:600 13px system-ui,sans-serif}.boundary{fill:#fff7ed;stroke:#fb923c;stroke-width:1.5}
            .boundary-title{fill:#9a3412;font:800 14px system-ui,sans-serif}.boundary-text{fill:#7c2d12;font:500 12px system-ui,sans-serif}
            .status-key{fill:#f8fafc;stroke:#cbd5e1;stroke-width:1.5}.status-key-title{fill:#0f172a;font:800 13px system-ui,sans-serif}
            .status-label{fill:#475569;font:650 12px system-ui,sans-serif}.footer{fill:#64748b;font:550 12px system-ui,sans-serif}
        </style>""",
        f'<rect class="background" width="{width}" height="{height}"/>',
        '<text class="title" x="40" y="55">Formalism composition atlas</text>',
        (
            f'<text class="subtitle" x="40" y="84">{len(atlas.topics)} canonical topics · '
            f"{len(atlas.families)} joined families · {len(atlas.relations)} authored relations · "
            f"{len(atlas.formal_modules)} maintained modules</text>"
        ),
        (
            '<text class="subtitle" x="40" y="108">Data-driven family layout; '
            "full topic, relation, capability, and module records remain available "
            "in the companion accessible HTML tables.</text>"
        ),
    ]

    for area_index, area in enumerate(atlas.areas):
        x, area_top = area_positions[area.id]
        stroke, tint = _AREA_PALETTE[area_index % len(_AREA_PALETTE)]
        families = families_by_area[area.id]
        lines.extend(
            [
                (
                    f'<g data-area-summary="{escape_svg_text(area.id)}" role="group" '
                    f'aria-label="{escape_svg_text(area.id)}, {len(area.topic_ids)} topics">'
                ),
                (
                    f'<rect class="area-card" x="{x}" y="{area_top}" '
                    f'width="{area_width}" height="122" rx="14" '
                    f'style="stroke:{stroke};fill:{tint}"/>'
                ),
                (
                    f'<text class="area-name" x="{x + 18}" y="{area_top + 34}" '
                    f'style="fill:{stroke}">{escape_svg_text(humanize_identifier(area.id))}</text>'
                ),
                (
                    f'<text class="area-count" x="{x + 18}" y="{area_top + 62}">'
                    f"{len(area.topic_ids)} topics · {len(families)} families</text>"
                ),
            ]
        )
        lines.extend(
            svg_text_lines(
                wrap_text(_status_summary(area.disposition_counts), 58, lines=2),
                x=x + 18,
                y=area_top + 88,
                css_class="area-count",
                step=19,
            )
        )
        lines.append("</g>")
        for family_index, family in enumerate(families):
            y = area_top + 136 + family_index * family_step
            lines.extend(
                [
                    (
                        f'<g data-family-summary="{escape_svg_text(family.id)}" role="group" '
                        f'data-formal-alignments="{escape_svg_text(_formal_alignment_data(family.formal_alignment_counts))}" '
                        f'aria-label="{escape_svg_text(family.id)}, {len(family.topic_ids)} topics">'
                    ),
                    (
                        f'<rect class="family-card" x="{x}" y="{y}" '
                        f'width="{area_width}" height="56" rx="9"/>'
                    ),
                ]
            )
            lines.extend(
                svg_text_lines(
                    wrap_text(humanize_identifier(family.id), 56),
                    x=x + 13,
                    y=y + 20,
                    css_class="family-name",
                    step=15,
                )
            )
            lines.append(
                f'<text class="family-count" x="{x + 13}" y="{y + 50}">'
                f"{len(family.topic_ids)} topics · "
                f"{escape_svg_text(_formal_alignment_summary(family.formal_alignment_counts))}</text>"
            )
            lines.append("</g>")

    lines.append(
        f'<text class="section" x="40" y="{relation_y}">Authored scientific relations</text>'
    )
    relation_card_y = relation_y + 20
    relation_kinds = sorted(relation_counts)
    relation_card_width = 235
    for index, kind in enumerate(relation_kinds):
        x = 40 + index * (relation_card_width + 14)
        count = relation_counts[kind]
        witnessed = sum(
            relation.kind == kind and relation.witness is not None
            for relation in atlas.relations
        )
        lines.extend(
            [
                (
                    f'<g data-relation-kind="{escape_svg_text(kind)}" role="group" '
                    f'aria-label="{escape_svg_text(kind)}, {count} relations">'
                ),
                (
                    f'<rect class="relation-card" x="{x}" y="{relation_card_y}" '
                    f'width="{relation_card_width}" height="72" rx="10"/>'
                ),
                (
                    f'<text class="relation-kind" x="{x + 14}" y="{relation_card_y + 27}">'
                    f"{escape_svg_text(humanize_identifier(kind))}</text>"
                ),
                (
                    f'<text class="relation-count" x="{x + 14}" y="{relation_card_y + 52}">'
                    f"{count} edges · {witnessed} named witnesses</text>"
                ),
                "</g>",
            ]
        )

    status_x = 40 + max(1, len(relation_kinds)) * (relation_card_width + 14) + 16
    status_width = width - status_x - 40
    lines.extend(
        [
            (
                '<g data-semantic-status-key="true" role="group" '
                'aria-label="Semantic status key">'
            ),
            (
                f'<rect class="status-key" x="{status_x}" y="{relation_card_y}" '
                f'width="{status_width}" height="72" rx="10"/>'
            ),
            (
                f'<text class="status-key-title" x="{status_x + 14}" '
                f'y="{relation_card_y + 22}">Semantic status key</text>'
            ),
        ]
    )
    status_slot = (status_width - 28) / max(1, len(dispositions))
    for index, disposition in enumerate(dispositions):
        count = sum(topic.semantic_disposition == disposition for topic in atlas.topics)
        item_x = status_x + 14 + index * status_slot
        y = relation_card_y + 51
        color = _STATUS_COLORS[index % len(_STATUS_COLORS)]
        lines.extend(
            [
                f'<circle cx="{item_x + 5}" cy="{y - 4}" r="5" fill="{color}"/>',
                (
                    f'<text class="status-label" x="{item_x + 18}" y="{y}">'
                    f"{escape_svg_text(humanize_identifier(disposition))} · {count}</text>"
                ),
            ]
        )
    lines.append("</g>")

    boundary_y = height - 104
    lines.extend(
        [
            (
                f'<rect class="boundary" x="40" y="{boundary_y}" width="1520" '
                'height="66" rx="10"/>'
            ),
            (
                f'<text class="boundary-title" x="58" y="{boundary_y + 25}">'
                "Numerical alignment · "
                f"{escape_svg_text(_formal_alignment_summary(alignment_counts))}</text>"
            ),
            (
                f'<text class="boundary-text" x="58" y="{boundary_y + 48}">'
                "Deterministic diagnostics only—not Lean proof receipts or empirical "
                f"validation; {len(atlas.witnesses)} typed witnesses provide exact workbench values.</text>"
            ),
            (
                f'<text class="footer" x="40" y="{height - 14}">Reviewed '
                f"{escape_svg_text(atlas.review_date)} · Module-import dependencies are code structure, "
                "not authored scientific relations.</text>"
            ),
            "</svg>",
        ]
    )
    return "\n".join(lines) + "\n"


def _render_formalism_atlas_mobile_svg(atlas: FormalismAtlas) -> str:
    """Render all five areas as a readable narrow, vertically flowing summary."""
    families_by_area = _family_by_area(atlas)
    width = 390
    margin = 12
    card_width = width - 2 * margin
    family_height = 72
    area_gap = 14
    area_chip_layouts = {
        area.id: _disposition_chip_layout(
            area.disposition_counts, available_width=card_width - 28
        )
        for area in atlas.areas
    }
    area_header_heights = {
        area.id: 74
        + (max((item[2] for item in area_chip_layouts[area.id]), default=0) + 1) * 30
        for area in atlas.areas
    }
    area_heights = tuple(
        area_header_heights[area.id]
        + len(families_by_area[area.id]) * family_height
        + area_gap
        for area in atlas.areas
    )
    relation_counts = Counter(relation.kind for relation in atlas.relations)
    alignment_counts: Counter[str] = Counter(
        witness.formal_alignment for witness in atlas.witnesses
    )
    relation_items = tuple(sorted(relation_counts.items()))
    relation_columns = 1
    relation_rows = (len(relation_items) + relation_columns - 1) // relation_columns
    relation_card_height = 76
    relation_card_gap = 10
    relation_cards_height = (
        relation_rows * relation_card_height
        + max(0, relation_rows - 1) * relation_card_gap
    )
    status_counts = dict(
        sorted(Counter(topic.semantic_disposition for topic in atlas.topics).items())
    )
    status_chip_layout = _disposition_chip_layout(
        status_counts, available_width=card_width
    )
    status_rows = max((item[2] for item in status_chip_layout), default=0) + 1
    relation_height = 42 + relation_cards_height + 34 + status_rows * 30 + 24
    header_height = 128
    boundary_lines = wrap_text(
        atlas.numerical_evidence_boundary,
        44,
        lines=None,
    )
    boundary_card_height = 72 + len(boundary_lines) * 18
    boundary_height = boundary_card_height + 28
    height = header_height + sum(area_heights) + relation_height + boundary_height
    lines = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
            'data-layout="mobile" role="img" '
            'aria-labelledby="mobile-atlas-title mobile-atlas-description">'
        ),
        '<title id="mobile-atlas-title">Five-area formalism atlas</title>',
        (
            '<desc id="mobile-atlas-description">All five broad areas and all '
            f"{len(atlas.families)} families in a single readable vertical flow.</desc>"
        ),
        """<style>
            .mobile-bg{fill:#f8fafc}.mobile-title{fill:#0f172a;font:800 24px system-ui,sans-serif}
            .mobile-subtitle{fill:#475569;font:600 14px system-ui,sans-serif}.mobile-area{stroke-width:2}
            .mobile-area-name{font:800 19px system-ui,sans-serif}.mobile-area-count{fill:#334155;font:650 14px system-ui,sans-serif}
            .mobile-disposition{fill:#fff;stroke-width:1.5}.mobile-disposition-text{font:700 14px system-ui,sans-serif}
            .mobile-family{fill:#fff;stroke:#cbd5e1;stroke-width:1}.mobile-family-name{fill:#0f172a;font:700 16px system-ui,sans-serif}
            .mobile-family-count{fill:#475569;font:600 14px system-ui,sans-serif}.mobile-section{fill:#0f172a;font:800 18px system-ui,sans-serif}
            .mobile-relation{fill:#fff;stroke:#cbd5e1;stroke-width:1.5}.mobile-relation-kind{fill:#0f172a;font:800 14px system-ui,sans-serif}
            .mobile-relation-count{fill:#334155;font:600 14px system-ui,sans-serif}.mobile-status-key-title{fill:#0f172a;font:800 14px system-ui,sans-serif}
            .mobile-boundary{fill:#fff7ed;stroke:#fb923c;stroke-width:1.5}.mobile-boundary-title{fill:#9a3412;font:800 14px system-ui,sans-serif}
            .mobile-alignment-text{fill:#9a3412;font:700 14px system-ui,sans-serif}.mobile-boundary-text{fill:#7c2d12;font:550 14px system-ui,sans-serif}
        </style>""",
        f'<rect class="mobile-bg" width="{width}" height="{height}"/>',
        '<text class="mobile-title" x="12" y="34">Formalism composition atlas</text>',
        (
            f'<text class="mobile-subtitle" x="12" y="58">Five areas · '
            f"{len(atlas.families)} families · {len(atlas.relations)} relations</text>"
        ),
        (
            f'<text class="mobile-subtitle" x="12" y="82" '
            f'data-explanatory-subtitle="{len(atlas.topics)} canonical topics · '
            'vertically complete · no horizontal crop">'
            f'<tspan x="12" y="82">{len(atlas.topics)} canonical topics · '
            'vertically complete</tspan><tspan x="12" y="102">no horizontal crop</tspan>'
            "</text>"
        ),
    ]
    y = header_height
    for area_index, area in enumerate(atlas.areas):
        families = families_by_area[area.id]
        area_header_height = area_header_heights[area.id]
        stroke, tint = _AREA_PALETTE[area_index % len(_AREA_PALETTE)]
        lines.extend(
            [
                (
                    f'<g data-mobile-area-summary="{escape_svg_text(area.id)}" role="group" '
                    f'aria-label="{escape_svg_text(area.id)}, {len(area.topic_ids)} topics">'
                ),
                (
                    f'<rect class="mobile-area" x="{margin}" y="{y}" '
                    f'width="{card_width}" height="{area_header_height - 2}" rx="12" '
                    f'style="stroke:{stroke};fill:{tint}"/>'
                ),
                (
                    f'<text class="mobile-area-name" x="{margin + 14}" y="{y + 29}" '
                    f'style="fill:{stroke}">{escape_svg_text(humanize_identifier(area.id))}</text>'
                ),
                (
                    f'<text class="mobile-area-count" x="{margin + 14}" y="{y + 56}">'
                    f"{len(area.topic_ids)} topics · {len(families)} families</text>"
                ),
            ]
        )
        for disposition, label, chip_row, chip_x, chip_width in area_chip_layouts[
            area.id
        ]:
            color = _STATUS_COLORS[
                sorted(status_counts).index(disposition) % len(_STATUS_COLORS)
            ]
            chip_y = y + 72 + chip_row * 30
            lines.extend(
                [
                    (
                        f'<g data-disposition-chip="{escape_svg_text(disposition)}" '
                        f'data-chip-row="{chip_row}" role="group">'
                    ),
                    (
                        f'<rect class="mobile-disposition" x="{margin + 14 + chip_x:.1f}" '
                        f'y="{chip_y}" width="{chip_width:.1f}" height="24" rx="12" '
                        f'style="stroke:{color}"/>'
                    ),
                    (
                        f'<text class="mobile-disposition-text" x="{margin + 25 + chip_x:.1f}" '
                        f'y="{chip_y + 17}" style="fill:{color}">{escape_svg_text(label)}</text>'
                    ),
                    "</g>",
                ]
            )
        family_y = y + area_header_height
        for family in families:
            lines.extend(
                [
                    (
                        f'<g data-mobile-family-summary="{escape_svg_text(family.id)}" '
                        f'data-formal-alignments="{escape_svg_text(_formal_alignment_data(family.formal_alignment_counts))}" '
                        'role="group">'
                    ),
                    (
                        f'<rect class="mobile-family" x="{margin}" y="{family_y}" '
                        f'width="{card_width}" height="{family_height - 7}" rx="8"/>'
                    ),
                ]
            )
            lines.extend(
                svg_text_lines(
                    wrap_text(humanize_identifier(family.id), 39),
                    x=margin + 12,
                    y=family_y + 22,
                    css_class="mobile-family-name",
                    step=18,
                )
            )
            lines.append(
                f'<text class="mobile-family-count" x="{margin + 12}" y="{family_y + 62}">'
                f"{len(family.topic_ids)} topics · "
                f"{escape_svg_text(_formal_alignment_summary(family.formal_alignment_counts))}</text>"
            )
            lines.append("</g>")
            family_y += family_height
        lines.append("</g>")
        y += area_header_height + len(families) * family_height + area_gap

    lines.append(
        f'<text class="mobile-section" x="{margin}" y="{y + 24}">Authored scientific relations</text>'
    )
    relation_y = y + 42
    relation_card_width = (
        card_width - relation_card_gap * (relation_columns - 1)
    ) / relation_columns
    for index, (kind, count) in enumerate(relation_items):
        column = index % relation_columns
        row = index // relation_columns
        x = margin + column * (relation_card_width + relation_card_gap)
        card_y = relation_y + row * (relation_card_height + relation_card_gap)
        witnessed = sum(
            relation.kind == kind and relation.witness is not None
            for relation in atlas.relations
        )
        lines.extend(
            [
                (
                    f'<rect class="mobile-relation" x="{x:.1f}" y="{card_y}" '
                    f'width="{relation_card_width:.1f}" height="{relation_card_height}" rx="9"/>'
                ),
                (
                    f'<text class="mobile-relation-kind" x="{x + 12:.1f}" y="{card_y + 27}">'
                    f"{escape_svg_text(humanize_identifier(kind))}</text>"
                ),
                (
                    f'<text class="mobile-relation-count" x="{x + 12:.1f}" y="{card_y + 52}">'
                    f"{count} edges · {witnessed} witnessed</text>"
                ),
            ]
        )
    status_y = relation_y + relation_cards_height + 28
    lines.append(
        f'<g data-mobile-semantic-status-key="true" role="group" '
        f'aria-label="Semantic status key"><text class="mobile-status-key-title" '
        f'x="{margin}" y="{status_y}">Semantic status key</text>'
    )
    for disposition, label, chip_row, chip_x, chip_width in status_chip_layout:
        color = _STATUS_COLORS[
            sorted(status_counts).index(disposition) % len(_STATUS_COLORS)
        ]
        chip_y = status_y + 12 + chip_row * 30
        lines.extend(
            [
                (
                    f'<g data-status-key-chip="{escape_svg_text(disposition)}" '
                    f'data-chip-row="{chip_row}">'
                ),
                (
                    f'<rect class="mobile-disposition" x="{margin + chip_x:.1f}" '
                    f'y="{chip_y}" width="{chip_width:.1f}" height="24" rx="12" '
                    f'style="stroke:{color}"/>'
                ),
                (
                    f'<text class="mobile-disposition-text" x="{margin + 11 + chip_x:.1f}" '
                    f'y="{chip_y + 17}" style="fill:{color}">{escape_svg_text(label)}</text>'
                ),
                "</g>",
            ]
        )
    lines.append("</g>")
    boundary_y = height - boundary_height + 8
    lines.extend(
        [
            (
                f'<rect class="mobile-boundary" x="{margin}" y="{boundary_y}" '
                f'width="{card_width}" height="{boundary_card_height}" rx="9"/>'
            ),
            (
                f'<text class="mobile-boundary-title" x="{margin + 12}" y="{boundary_y + 24}">'
                "Numerical evidence boundary</text>"
            ),
            (
                f'<text class="mobile-alignment-text" x="{margin + 12}" y="{boundary_y + 44}">'
                f"{escape_svg_text(_formal_alignment_summary(alignment_counts))}</text>"
            ),
        ]
    )
    lines.extend(
        svg_text_lines(
            boundary_lines,
            x=margin + 12,
            y=boundary_y + 62,
            css_class="mobile-boundary-text",
            step=18,
        )
    )
    lines.append("</svg>")
    return "\n".join(lines) + "\n"




def _topic_table(atlas: FormalismAtlas) -> str:
    rows: list[str] = []
    for topic in atlas.topics:
        search = (
            f"{topic.id} {topic.title} {topic.area} {topic.family} "
            f"{topic.semantic_disposition} {topic.primary_theorem} "
            f"{topic.invariant} {topic.assumption_review} {topic.non_vacuity}"
        ).lower()
        rows.append(
            f'<tr data-topic-row="{escape_svg_text(topic.id)}" data-area="{escape_svg_text(topic.area)}" '
            f'data-family="{escape_svg_text(topic.family)}" '
            f'data-status="{escape_svg_text(topic.semantic_disposition)}" '
            f'data-search="{escape_svg_text(search)}">'
            f'<th scope="row"><code>{escape_svg_text(topic.id)}</code><span>{escape_svg_text(topic.title)}</span></th>'
            f'<td data-label="Area">{escape_svg_text(humanize_identifier(topic.area))}</td>'
            f'<td data-label="Family">{escape_svg_text(humanize_identifier(topic.family))}</td>'
            f'<td data-label="Status"><span class="status">{escape_svg_text(humanize_identifier(topic.semantic_disposition))}</span></td>'
            f'<td data-label="Primary theorem"><code>{escape_svg_text(topic.primary_theorem)}</code></td>'
            f'<td data-label="Invariant"><details class="topic-review"><summary>Read invariant</summary><p>{escape_svg_text(topic.invariant)}</p></details></td>'
            f'<td data-label="Assumptions / scope"><details class="topic-review"><summary>Read assumptions</summary><p>{escape_svg_text(topic.assumption_review)}</p></details></td>'
            f'<td data-label="Non-vacuity"><details class="topic-review"><summary>Read non-vacuity review</summary><p>{escape_svg_text(topic.non_vacuity)}</p></details></td>'
            f'<td data-label="Counts">{topic.theorem_count} / {topic.definition_count} / {len(topic.imports)}</td>'
            "</tr>"
        )
    return "".join(rows)


def _relation_table(atlas: FormalismAtlas) -> str:
    return "".join(
        f'<tr data-relation-row="{index}" data-kind="{escape_svg_text(relation.kind)}">'
        f'<th scope="row"><code>{escape_svg_text(relation.source)}</code></th>'
        f'<td data-label="Relation kind"><span class="status">{escape_svg_text(humanize_identifier(relation.kind))}</span></td>'
        f'<td data-label="Paired topic"><code>{escape_svg_text(relation.target)}</code></td>'
        f'<td data-label="Rationale">{escape_svg_text(relation.rationale)}</td>'
        f'<td data-label="Exact witness">'
        f"{f'<code>{escape_svg_text(relation.witness)}</code>' if relation.witness else '—'}</td>"
        "</tr>"
        for index, relation in enumerate(atlas.relations)
    )


def _capability_table(atlas: FormalismAtlas) -> str:
    return "".join(
        f'<tr data-capability-row="{escape_svg_text(capability.id)}">'
        f'<th scope="row"><code>{escape_svg_text(capability.id)}</code><span>{escape_svg_text(capability.title)}</span></th>'
        f"<td>{escape_svg_text(humanize_identifier(capability.status))}</td>"
        f"<td>{escape_svg_text(capability.description)}</td>"
        f"<td>{', '.join(f'<code>{escape_svg_text(item)}</code>' for item in capability.evidence) or '—'}</td>"
        f"<td>{', '.join(escape_svg_text(item) for item in capability.blocked_topics) or '—'}</td>"
        "</tr>"
        for capability in atlas.capabilities
    )


def _module_table(atlas: FormalismAtlas) -> str:
    return "".join(
        f'<tr data-module-row="{escape_svg_text(module.id)}">'
        f'<th scope="row"><code>{escape_svg_text(module.lean_module)}</code></th>'
        f"<td>{escape_svg_text(humanize_identifier(module.role))}</td>"
        f"<td>{module.theorem_count}</td><td>{module.definition_count}</td>"
        f"<td>{module.structure_count}</td>"
        f"<td>{', '.join(f'<code>{escape_svg_text(item)}</code>' for item in module.formal_dependencies) or '—'}</td>"
        "</tr>"
        for module in atlas.formal_modules
    )


def _dependency_table(atlas: FormalismAtlas) -> str:
    rows: list[str] = []
    index = 0
    for module in atlas.formal_modules:
        for dependency in module.formal_dependencies:
            rows.append(
                f'<tr data-dependency-row="{index}"><th scope="row"><code>'
                f'{escape_svg_text(module.lean_module)}</code></th><td aria-label="depends on">→</td>'
                f"<td><code>{escape_svg_text(dependency)}</code></td></tr>"
            )
            index += 1
    return "".join(rows)


def render_formalism_atlas_html(atlas: FormalismAtlas) -> str:
    """Render the offline searchable atlas with complete accessible data tables."""
    svg = render_formalism_atlas_svg(atlas).rstrip()
    mobile_svg = _render_formalism_atlas_mobile_svg(atlas).rstrip()
    topic_families = sorted(
        family.id for family in atlas.families if family.area is not None
    )
    statuses = sorted({topic.semantic_disposition for topic in atlas.topics})
    relation_kinds = sorted({relation.kind for relation in atlas.relations})
    title_summary = (
        f"{len(atlas.topics)} topics · {len(topic_families)} topic families · "
        f"{len(atlas.relations)} authored relations"
    )
    head = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Formalism composition atlas</title>
<style>
:root{color-scheme:light;--ink:#0f172a;--muted:#475569;--line:#cbd5e1;--paper:#f8fafc;--accent:#0f766e}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.5 system-ui,sans-serif}
a{color:#0f5e59}.skip{position:absolute;left:-9999px}.skip:focus{left:12px;top:12px;background:white;padding:10px;z-index:20}
header,main{max-width:1700px;margin:auto;padding:24px}header{padding-bottom:8px}h1{margin:.1rem 0;font-size:clamp(2rem,5vw,3.4rem)}
.lede{max-width:85ch;color:var(--muted)}.boundary{border-left:5px solid #f97316;background:#fff7ed;padding:12px 16px;max-width:110ch}
.controls{display:grid;grid-template-columns:minmax(220px,2fr) repeat(4,minmax(150px,1fr));gap:12px;position:sticky;top:0;z-index:8;background:rgba(248,250,252,.96);padding:12px 0}
label{font-weight:700}input,select,button{font:inherit;border:1px solid #94a3b8;border-radius:8px;background:white;padding:9px;color:var(--ink);width:100%}
.field{display:grid;gap:4px}.result{grid-column:1/-1;color:var(--muted);min-height:1.5em}.summary-shell{border:1px solid var(--line);border-radius:14px;background:white;overflow:hidden}
.atlas-jumps{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0 18px}.atlas-jumps a{display:inline-block;border:1px solid var(--line);border-radius:999px;background:white;padding:7px 11px;font-weight:750;text-decoration:none}details[id]{scroll-margin-top:140px}
.summary-tools{display:flex;flex-wrap:wrap;gap:8px;padding:10px;border-bottom:1px solid var(--line)}.summary-tools button{width:auto;min-width:44px}
.viewport{overflow:auto;touch-action:none;cursor:grab;scrollbar-color:#94a3b8 #e2e8f0}.viewport.is-dragging{cursor:grabbing}
.desktop-summary{display:block}.mobile-summary{display:none}.canvas{width:100%;transform-origin:top left}.canvas svg,.mobile-summary svg{display:block;width:100%;height:auto}.hint{padding:8px 12px;color:var(--muted);font-size:.9rem}
details{margin:22px 0;border:1px solid var(--line);border-radius:12px;background:white}summary{cursor:pointer;font-size:1.2rem;font-weight:800;padding:15px}
.table-wrap{overflow:auto;border-top:1px solid var(--line);scrollbar-color:#64748b #e2e8f0;overscroll-behavior-inline:contain}.scroll-hint,.relation-card-hint{display:none;margin:0;padding:8px 12px;background:#eff6ff;color:#1e3a8a;font-weight:750}table{border-collapse:collapse;width:100%;min-width:1050px}caption{text-align:left;font-weight:700;padding:12px}
th,td{padding:10px;border-bottom:1px solid #e2e8f0;text-align:left;vertical-align:top}thead th{position:sticky;top:0;background:#e2e8f0;z-index:2}
tbody th{min-width:170px}tbody th span{display:block;font-weight:500;margin-top:4px}.status{display:inline-block;background:#e2e8f0;border-radius:999px;padding:2px 8px;white-space:nowrap}
.topic-review{margin:0;border:0;border-radius:0;background:transparent}.topic-review summary{padding:2px 0;color:#0f5e59;font-size:.88rem}.topic-review p{min-width:250px;margin:7px 0 2px}code{font-size:.86em;overflow-wrap:anywhere}[hidden]{display:none!important}.empty{padding:16px;color:var(--muted)}
@media (max-width: 1100px){.controls{grid-template-columns:1fr 1fr}.controls .search{grid-column:1/-1}}
@media (max-width: 760px){.desktop-summary{display:none}.mobile-summary{display:block}header,main{padding:14px}.controls{position:static;grid-template-columns:1fr}.controls .search{grid-column:auto}h1{font-size:2rem}.topic-table-wrap,.relation-table-wrap{max-height:none;overflow:visible}#topic-table,#relation-table{min-width:0}#topic-table thead,#relation-table thead{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}#topic-table tbody,#relation-table tbody{display:block}#topic-table tbody tr,#relation-table tbody tr{display:block;margin:10px;border:1px solid var(--line);border-radius:10px;overflow:hidden}#topic-table tbody th,#relation-table tbody th{display:block;min-width:0;padding:10px 12px;background:#f1f5f9}#topic-table td,#relation-table td{display:grid;grid-template-columns:7.5rem minmax(0,1fr);gap:8px;padding:6px 12px}#topic-table td::before,#relation-table td::before{content:attr(data-label);font-weight:800;color:var(--muted)}#topic-table .topic-review,#topic-table .topic-review p{min-width:0}.scroll-hint,.relation-card-hint{display:block}}
@media (prefers-reduced-motion: reduce){*{scroll-behavior:auto!important}}
</style>
</head>
<body>
<a class="skip" href="#topic-table">Skip to topic table</a>
<header><p>FEP Lean · deterministic generated projection</p><h1>Formalism composition atlas</h1>"""
    controls = (
        f'<p class="lede">{escape_svg_text(title_summary)}. The compact SVG summarizes five broad '
        "areas and their data-driven families; the tables below preserve every canonical "
        f"record without turning the static figure into a {len(atlas.topics)}-card "
        "print sheet.</p>"
        f'<p class="boundary"><strong>Evidence boundary.</strong> {escape_svg_text(atlas.structural_evidence_boundary)} '
        f"{escape_svg_text(atlas.numerical_evidence_boundary)}</p></header><main>"
        '<section class="controls" aria-label="Atlas filters">'
        '<div class="field search"><label for="atlas-search">Search topics</label>'
        '<input id="atlas-search" type="search" aria-keyshortcuts="/ Escape" '
        'placeholder="ID, title, theorem, invariant, assumption…"></div>'
        '<div class="field"><label for="area-filter">Area</label><select id="area-filter">'
        f"{options_fragment([area.id for area in atlas.areas], all_label='areas')}</select></div>"
        '<div class="field"><label for="family-filter">Family</label><select id="family-filter">'
        f"{options_fragment(topic_families, all_label='families')}</select></div>"
        '<div class="field"><label for="status-filter">Semantic status</label><select id="status-filter">'
        f"{options_fragment(statuses, all_label='statuses')}</select></div>"
        '<div class="field"><label for="relation-filter">Relation kind</label><select id="relation-filter">'
        f"{options_fragment(relation_kinds, all_label='relation kinds')}</select></div>"
        f'<div id="atlas-result-count" class="result" role="status" aria-live="polite">{len(atlas.topics)} topics matched</div>'
        "</section>"
    )
    summary = (
        '<nav class="atlas-jumps" aria-label="Atlas sections">'
        '<a href="#summary-title">Visual summary</a>'
        f'<a href="#topic-records">{len(atlas.topics)} topics</a>'
        f'<a href="#relation-records">{len(atlas.relations)} relations</a>'
        f'<a href="#capability-records">{len(atlas.capabilities)} capabilities</a>'
        f'<a href="#module-records">{len(atlas.formal_modules)} formal modules</a></nav>'
        '<section aria-labelledby="summary-title"><h2 id="summary-title">Area, family, and relation summary</h2>'
        '<div class="summary-shell"><div class="desktop-summary"><div class="summary-tools" aria-label="Summary navigation">'
        '<button type="button" data-pan-direction="left" aria-label="Pan left">← Pan left</button>'
        '<button type="button" data-pan-direction="right" aria-label="Pan right">Pan right →</button>'
        '<button type="button" data-pan-direction="up" aria-label="Pan up">↑ Pan up</button>'
        '<button type="button" data-pan-direction="down" aria-label="Pan down">Pan down ↓</button>'
        '<button type="button" data-zoom="out" aria-label="Zoom out">− Zoom out</button>'
        '<button type="button" data-zoom="reset">Reset view</button>'
        '<button type="button" data-zoom="in" aria-label="Zoom in">+ Zoom in</button></div>'
        '<div id="atlas-viewport" class="viewport" tabindex="0" aria-label="Scrollable atlas summary; arrow keys pan, plus and minus zoom">'
        f'<div id="atlas-canvas" class="canvas">{svg}</div></div>'
        '<p class="hint">Drag or use arrow buttons/keys to pan. Use +/− to zoom. Press / to search and Escape to clear filters.</p>'
        f'</div><div class="mobile-summary">{mobile_svg}</div></div></section>'
    )
    tables = (
        f'<details id="topic-records"><summary>Canonical topic table · {len(atlas.topics)} topics</summary>'
        '<div class="table-wrap topic-table-wrap">'
        f'<table id="topic-table"><caption>All {len(atlas.topics)} canonical topics; filters hide rows without deleting evidence.</caption>'
        '<thead><tr><th scope="col">Topic</th><th scope="col">Area</th><th scope="col">Family</th><th scope="col">Status</th>'
        '<th scope="col">Primary theorem</th><th scope="col">Invariant</th><th scope="col">Assumptions / scope</th>'
        '<th scope="col">Non-vacuity</th><th scope="col">Theorems / definitions / imports</th></tr></thead>'
        f"<tbody>{_topic_table(atlas)}</tbody></table></div></details>"
        f'<details id="relation-records"><summary>Exact authored relation table · {len(atlas.relations)} relations</summary>'
        '<div class="table-wrap relation-table-wrap">'
        '<p class="relation-card-hint">Complete relation cards show rationale and exact witnesses.</p>'
        f'<table id="relation-table" data-mobile-layout="complete-cards"><caption>All {len(atlas.relations)} authored scientific relations; relation kind filtering applies here.</caption>'
        '<thead><tr><th scope="col">Source</th><th scope="col">Kind</th><th scope="col">Target</th><th scope="col">Rationale</th><th scope="col">Exact witness</th></tr></thead>'
        f"<tbody>{_relation_table(atlas)}</tbody></table></div></details>"
        f'<details id="capability-records"><summary>Retained capability table · {len(atlas.capabilities)} records</summary><div class="table-wrap">'
        '<p class="scroll-hint">Swipe horizontally to inspect every column.</p>'
        f"<table><caption>{len(atlas.capabilities)} retained capability records preserve resolved and open history.</caption>"
        '<thead><tr><th scope="col">Capability</th><th scope="col">Status</th><th scope="col">Required surface</th><th scope="col">Declaration evidence</th><th scope="col">Blocked topics</th></tr></thead>'
        f"<tbody>{_capability_table(atlas)}</tbody></table></div></details>"
        f'<details id="module-records"><summary>Maintained formal-module table · {len(atlas.formal_modules)} modules</summary><div class="table-wrap">'
        '<p class="scroll-hint">Swipe horizontally to inspect every column.</p>'
        f"<table><caption>{len(atlas.formal_modules)} maintained modules. Code dependencies are not scientific relations.</caption>"
        '<thead><tr><th scope="col">Lean module</th><th scope="col">Role</th><th scope="col">Theorems</th><th scope="col">Definitions</th><th scope="col">Structures</th><th scope="col">Internal dependencies</th></tr></thead>'
        f"<tbody>{_module_table(atlas)}</tbody></table></div>"
        '<div class="table-wrap"><table><caption>Exact internal module-dependency edges</caption>'
        '<thead><tr><th scope="col">Module</th><th scope="col">Direction</th><th scope="col">Imported maintained module</th></tr></thead>'
        f"<tbody>{_dependency_table(atlas)}</tbody></table></div></details>"
    )
    script = """</main>
<script>
"use strict";
const search=document.getElementById("atlas-search");
const area=document.getElementById("area-filter");
const family=document.getElementById("family-filter");
const status=document.getElementById("status-filter");
const relation=document.getElementById("relation-filter");
const result=document.getElementById("atlas-result-count");
const topicSection=document.getElementById("topic-records");
const relationSection=document.getElementById("relation-records");
const topicRows=[...document.querySelectorAll("[data-topic-row]")];
const relationRows=[...document.querySelectorAll("[data-relation-row]")];
function applyFilters(){
  const query=search.value.trim().toLowerCase();let matched=0;let matchedRelations=0;
  topicRows.forEach(row=>{const show=(!query||row.dataset.search.includes(query))&&(!area.value||row.dataset.area===area.value)&&(!family.value||row.dataset.family===family.value)&&(!status.value||row.dataset.status===status.value);row.hidden=!show;if(show)matched+=1;});
  relationRows.forEach(row=>{const show=!relation.value||row.dataset.kind===relation.value;row.hidden=!show;if(show)matchedRelations+=1;});
  if(query||area.value||family.value||status.value)topicSection.open=true;
  if(relation.value)relationSection.open=true;
  result.textContent=`${matched} of ${topicRows.length} topics · ${matchedRelations} of ${relationRows.length} relations matched`;
}
[search,area,family,status,relation].forEach(control=>control.addEventListener("input",applyFilters));
document.addEventListener("keydown",event=>{
  const editing=["INPUT","SELECT","TEXTAREA"].includes(document.activeElement.tagName);
  if(event.key==="/"&&!editing){event.preventDefault();search.focus();}
  if(event.key==="Escape"){search.value="";area.value="";family.value="";status.value="";relation.value="";applyFilters();search.focus();}
});
const viewport=document.getElementById("atlas-viewport");const canvas=document.getElementById("atlas-canvas");let zoom=1;
function setZoom(next){zoom=Math.max(.55,Math.min(1.8,next));canvas.style.width=`${zoom*100}%`;}
document.querySelectorAll("[data-zoom]").forEach(button=>button.addEventListener("click",()=>{const mode=button.dataset.zoom;setZoom(mode==="in"?zoom+.15:mode==="out"?zoom-.15:1);}));
const deltas={left:[-260,0],right:[260,0],up:[0,-220],down:[0,220]};
function pan(direction){const delta=deltas[direction];viewport.scrollBy({left:delta[0],top:delta[1],behavior:"smooth"});}
document.querySelectorAll("[data-pan-direction]").forEach(button=>button.addEventListener("click",()=>pan(button.dataset.panDirection)));
viewport.addEventListener("keydown",event=>{const direction={ArrowLeft:"left",ArrowRight:"right",ArrowUp:"up",ArrowDown:"down"}[event.key];if(direction){event.preventDefault();pan(direction);}if(event.key==="+"||event.key==="="){setZoom(zoom+.15);}if(event.key==="-"){setZoom(zoom-.15);}});
let drag=null;viewport.addEventListener("pointerdown",event=>{drag={x:event.clientX,y:event.clientY,left:viewport.scrollLeft,top:viewport.scrollTop};viewport.classList.add("is-dragging");viewport.setPointerCapture(event.pointerId);});
viewport.addEventListener("pointermove",event=>{if(!drag)return;viewport.scrollLeft=drag.left-(event.clientX-drag.x);viewport.scrollTop=drag.top-(event.clientY-drag.y);});
function stopDrag(){drag=null;viewport.classList.remove("is-dragging");}viewport.addEventListener("pointerup",stopDrag);viewport.addEventListener("pointercancel",stopDrag);
applyFilters();
</script>
</body>
</html>
"""
    return head + controls + summary + tables + script


def atlas_projection_paths(
    project_root: Path, *, output_root: Path | None = None
) -> tuple[Path, Path]:
    """Return atlas destinations, optionally rooted in a temporary directory."""
    root = Path(output_root) if output_root is not None else Path(project_root)
    return root / ATLAS_SVG, root / ATLAS_HTML


def write_formalism_atlas(
    project_root: Path, *, output_root: Path | None = None
) -> tuple[Path, Path]:
    """Write deterministic SVG and interactive HTML atlas projections."""
    atlas = build_formalism_atlas(Path(project_root))
    svg_path, html_path = atlas_projection_paths(project_root, output_root=output_root)
    atomic_write_text(svg_path, render_formalism_atlas_svg(atlas))
    atomic_write_text(html_path, render_formalism_atlas_html(atlas))
    return svg_path, html_path


def atlas_projection_drift(
    project_root: Path,
    *,
    output_root: Path | None = None,
    presentation: FormalismPresentation | None = None,
) -> tuple[Path, ...]:
    """Return missing or stale atlas projection paths in stable order.

    ``presentation`` optionally supplies the already-built shared join so a
    caller that validated several planes against one snapshot can thread it
    through without rebuilding it per call (SC-20). No output bytes change.
    """
    atlas = build_formalism_atlas(Path(project_root)) if presentation is None else presentation
    svg_path, html_path = atlas_projection_paths(project_root, output_root=output_root)
    expected = {
        svg_path: render_formalism_atlas_svg(atlas),
        html_path: render_formalism_atlas_html(atlas),
    }
    return tuple(
        path
        for path, content in expected.items()
        if not path.is_file() or path.read_text(encoding="utf-8") != content
    )


__all__ = [
    "FormalismAtlas",
    "atlas_projection_drift",
    "atlas_projection_paths",
    "build_formalism_atlas",
    "render_formalism_atlas_html",
    "render_formalism_atlas_svg",
    "write_formalism_atlas",
]
