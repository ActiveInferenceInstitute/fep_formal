"""Bibliography and manuscript citation contracts."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _audit_module():
    spec = importlib.util.spec_from_file_location(
        "citation_audit", PROJECT_ROOT / "docs" / "citation_audit.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_bibliography_and_authored_citations_are_bijective() -> None:
    audit = _audit_module()

    assert audit.audit_citations(PROJECT_ROOT) == ()


def test_verified_efe_records_remain_pinned() -> None:
    audit = _audit_module()
    entries = {
        entry.key: entry
        for entry in audit.parse_bibliography(
            PROJECT_ROOT / "docs" / "manuscript" / "references.bib"
        )
    }

    assert entries["champion2026reframing"].fields["doi"] == "10.1162/NECO.a.1491"
    assert entries["millidge2021whence"].fields["doi"] == "10.1162/neco_a_01354"
