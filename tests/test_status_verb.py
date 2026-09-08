"""The status verb composes existing checks and states its boundaries."""

from __future__ import annotations

import json
from pathlib import Path

from fep_lean.output.render_log import manuscript_source_digest
from fep_lean.status import (
    RENDER_RECEIPT,
    SOURCE_PIN,
    bridge_pin_section,
    build_status_report,
    catalogue_products_section,
    render_receipt_section,
)

SECTION_NAMES = (
    "catalogue_build_products",
    "render_receipt_freshness",
    "bridge_source_pin",
    "native_verification_receipt",
)


def accepted_receipt_payload(manuscript_dir: Path) -> dict[str, object]:
    """Build the smallest render-acceptance receipt covering *manuscript_dir*."""
    return {
        "receipt_version": 1,
        "accepted": True,
        "pages": 1,
        "checks": {
            "tex_errors": [],
            "missing_characters": [],
            "mermaid_fallbacks": [],
            "stale_sources": [],
            "uncaptioned_tables": [],
            "contents_number_overflows": [],
        },
        "manuscript_source_digest": manuscript_source_digest(manuscript_dir),
        "source_digests": {},
    }


def manuscript_tree(root: Path) -> Path:
    """Stage a minimal typeset manuscript under *root*."""
    manuscript = root / "manuscript"
    manuscript.mkdir()
    (manuscript / "01_chapter.md").write_text("# Chapter\n\nText.\n")
    (manuscript / "preamble.md").write_text("\\usepackage{fontspec}\n")
    return manuscript


def test_report_has_all_sections_and_boundaries(tmp_path: Path) -> None:
    report = build_status_report(tmp_path)
    payload = report.as_dict()
    assert [section["name"] for section in payload["sections"]] == list(SECTION_NAMES)
    assert payload["status"] == "ok"
    assert payload["native_claim_ready"] is False
    for section in payload["sections"]:
        assert section["boundary"].strip()
        assert section["composes"], section["name"]


def test_report_json_round_trips(tmp_path: Path) -> None:
    payload = json.loads(json.dumps(build_status_report(tmp_path).as_dict()))
    assert payload["schema_version"] == 1
    assert payload["status"] == "ok"
    assert [section["name"] for section in payload["sections"]] == list(SECTION_NAMES)
    for section in payload["sections"]:
        assert isinstance(section["findings"], list)
        assert isinstance(section["composes"], list)


def test_missing_build_product_is_reported_stale(tmp_path: Path) -> None:
    # The tracked aggregate Lean projection is absent from this checkout.
    expected_dir = tmp_path / "lean" / "FepSketches"
    expected_dir.mkdir(parents=True)
    (expected_dir / "fep_all.lean").write_text("# stale content\n")
    section = catalogue_products_section(tmp_path)
    assert section.state == "stale"
    assert any(
        finding.startswith("stale or missing: lean/FepSketches/fep_all.lean")
        for finding in section.findings
    )


def test_render_receipt_missing_then_current_then_stale(tmp_path: Path) -> None:
    manuscript = manuscript_tree(tmp_path)
    receipt = tmp_path / RENDER_RECEIPT

    missing = render_receipt_section(tmp_path)
    assert missing.state == "missing"
    assert any("no acceptance receipt" in finding for finding in missing.findings)

    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps(accepted_receipt_payload(manuscript)))
    current = render_receipt_section(tmp_path)
    assert current.state == "current"
    assert current.findings == ()

    (manuscript / "01_chapter.md").write_text("# Chapter\n\nEdited.\n")
    stale = render_receipt_section(tmp_path)
    assert stale.state == "stale"
    assert any("covers manuscript sources" in finding for finding in stale.findings)


def test_bridge_pin_absent_reports_not_pinned(tmp_path: Path) -> None:
    section = bridge_pin_section(tmp_path)
    assert section.state == "not_pinned"
    assert any("not pinned" in finding for finding in section.findings)
    assert "explicitly named GNN checkout" in section.boundary


def test_bridge_pin_detects_fep_lean_owner_drift(tmp_path: Path) -> None:
    pin_path = tmp_path / SOURCE_PIN
    pin_path.parent.mkdir(parents=True)
    pin_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "fep_lean": {"commit": "0" * 40, "owners": {}},
                "gnn": {"commit": "0" * 40, "owners": {}},
            }
        )
    )
    section = bridge_pin_section(tmp_path)
    assert section.state == "stale"
    assert any("owner roster mismatch" in finding for finding in section.findings)


def test_malformed_receipts_fail_closed_without_exceptions(tmp_path: Path) -> None:
    receipt = tmp_path / RENDER_RECEIPT
    receipt.parent.mkdir(parents=True)
    receipt.write_text("{not json")
    section = render_receipt_section(tmp_path)
    assert section.state == "stale"
    assert any(
        "unreadable acceptance receipt" in finding for finding in section.findings
    )
