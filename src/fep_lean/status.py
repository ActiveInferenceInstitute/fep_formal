"""Read-only evidence-currency report composing existing fep_lean checks.

``fep-lean status`` does not invent heuristics: every section delegates to the
same fail-closed functions the regeneration, render, and bridge gates already
use, then states exactly what the composed evidence does and does not prove.
A green local command is only meaningful when its capability boundary and
evidence are explicit, so every section carries its boundary in the report.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fep_lean.bridge import operations
from fep_lean.bridge.custody import validate_binding
from fep_lean.catalogue.generation import (
    catalogue_projection_drift,
    fep_all_projection_drift,
)
from fep_lean.catalogue.topics import FEPTopicCatalogue
from fep_lean.output.evidence import validate_native_lean_receipt
from fep_lean.output.manuscript import (
    build_manuscript_vars,
    manuscript_projection_drift,
)
from fep_lean.output.render_log import receipt_defects

RENDER_RECEIPT = Path("docs") / "render-acceptance.json"
NATIVE_RECEIPT = Path("output") / "native-verification.json"
SOURCE_PIN = Path(operations.PIN)

_STATUS_BOUNDARY = (
    "status composes existing read-only checks; exit 0 means the report "
    "composed, never that the evidence is current. Each section's state and "
    "boundary are the authority. Nothing here compiles Lean, runs Hermes or "
    "OpenGauss, executes the test suite, writes bytes, or repairs drift."
)


@dataclass(frozen=True)
class SectionReport:
    """One evidence-currency section with its explicit capability boundary."""

    name: str
    state: str
    findings: tuple[str, ...]
    composes: tuple[str, ...]
    boundary: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "state": self.state,
            "findings": list(self.findings),
            "composes": list(self.composes),
            "boundary": self.boundary,
        }


@dataclass(frozen=True)
class StatusReport:
    """Typed ``fep-lean status`` payload: sections, never proof claims."""

    sections: tuple[SectionReport, ...]

    @property
    def status(self) -> str:
        """``ok`` when the report composed; section states carry currency."""
        return "ok" if len(self.sections) == 4 else "error"

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "status": self.status,
            "evidence_plane": "evidence currency and provenance",
            "boundary": _STATUS_BOUNDARY,
            "native_claim_ready": False,
            "sections": [section.as_dict() for section in self.sections],
        }


def catalogue_products_section(
    root: Path, catalogue: FEPTopicCatalogue | None = None
) -> SectionReport:
    """Compare offline catalogue build products against their generators."""
    composes = (
        "fep_lean.catalogue.generation.catalogue_projection_drift",
        "fep_lean.catalogue.generation.fep_all_projection_drift",
        "fep_lean.output.manuscript.manuscript_projection_drift",
    )
    boundary = (
        "Compares generated projections byte-for-byte against their canonical "
        "generators. It does not compile Lean, run Hermes or OpenGauss, "
        "execute the test suite, or prove any theorem: current means only "
        "that generators and products agree on bytes."
    )
    stale: list[Path] = []
    findings: list[str] = []
    try:
        stale.extend(catalogue_projection_drift(root))
    except (OSError, ValueError) as exc:
        findings.append(f"topic catalogue projections unreadable: {exc}")
    try:
        stale.extend(fep_all_projection_drift(root))
    except (OSError, ValueError) as exc:
        findings.append(f"aggregate Lean projection unreadable: {exc}")
    try:
        cat = catalogue or FEPTopicCatalogue.from_yaml(root / "config" / "topics.yaml")
        expected_vars = build_manuscript_vars(
            cat,
            root,
            output_root=root / "output",
            cache_test_count=False,
        )
        stale.extend(
            manuscript_projection_drift(
                root,
                catalogue=cat,
                output_root=root / "output",
                expected_variables=expected_vars,
            )
        )
    except (OSError, ValueError) as exc:
        # The test census refuses to run a collection here; a missing cache is
        # the census boundary, not a drift verdict on the manuscript.
        findings.append(
            "manuscript projections not compared: test-collection census "
            f"cache missing or stale ({exc})"
        )
    if stale:
        findings.extend(
            f"stale or missing: {path.relative_to(root).as_posix() if path.is_relative_to(root) else path.as_posix()}"
            for path in stale
        )
    state = "stale" if stale else "current"
    return SectionReport(
        name="catalogue_build_products",
        state=state,
        findings=tuple(findings),
        composes=composes,
        boundary=boundary,
    )


def render_receipt_section(
    root: Path,
    *,
    receipt_path: Path | None = None,
    manuscript_dir: Path | None = None,
) -> SectionReport:
    receipt = receipt_path or root / RENDER_RECEIPT
    manuscript = manuscript_dir or root / "manuscript"
    composes = (
        "fep_lean.output.render_log.receipt_defects",
        "fep_lean.output.render_log.manuscript_source_digests",
    )
    boundary = (
        "The receipt binds an accepted render to the authored manuscript text "
        "and LaTeX preamble as of that render. It does not re-run the render, "
        "does not cover values a {{token}} resolves to (manuscript projection "
        "drift owns that surface), and says nothing about Lean, Hermes, or "
        "OpenGauss evidence."
    )
    defects = receipt_defects(receipt, manuscript)
    if not receipt.is_file():
        state = "missing"
    elif defects:
        state = "stale"
    else:
        state = "current"
    return SectionReport(
        name="render_receipt_freshness",
        state=state,
        findings=defects,
        composes=composes,
        boundary=boundary,
    )


def bridge_pin_section(root: Path, gnn_root: Path | None = None) -> SectionReport:
    """Report GNN bridge source-pin presence and, when possible, staleness."""
    composes = (
        "fep_lean.bridge.operations.check_sources",
        "fep_lean.bridge.custody.validate_binding",
    )
    pin = root / SOURCE_PIN
    if not pin.is_file():
        return SectionReport(
            name="bridge_source_pin",
            state="not_pinned",
            findings=("specs/gnn-bridge-w2-source-custody/source-pin.json: not pinned",),
            composes=composes,
            boundary=(
                "No source pin exists, so no bridge evidence is bound to owner "
                "bytes. Pin presence alone establishes nothing about the "
                "current sibling tree: comparing working-tree bytes requires "
                "the explicitly named GNN checkout, and a fresh pin is not "
                "evidence of correctness or of native proof."
            ),
        )
    try:
        data = operations.read_object(pin)
        findings = [
            f"fep_lean commit recorded: {data['fep_lean'].get('commit', '?')}",
            f"gnn commit recorded: {data['gnn'].get('commit', '?')}",
        ]
        errors: list[str]
        if gnn_root is not None:
            errors = operations.check_sources(root, gnn_root, data)
        else:
            fep_entry = data.get("fep_lean")
            owners = fep_entry.get("owners") if isinstance(fep_entry, dict) else None
            if not isinstance(owners, dict):
                errors = ["malformed fep_lean source binding"]
            else:
                errors = validate_binding(
                    root, owners, operations.owner_roster(root, "fep_lean")
                )
                errors = [f"fep_lean: {error}" for error in errors]
            findings.append(
                "gnn owner bytes not compared: pass --gnn-root with the "
                "explicit GNN checkout to validate both sides"
            )
    except (OSError, KeyError, TypeError, ValueError) as exc:
        return SectionReport(
            name="bridge_source_pin",
            state="error",
            findings=(f"unreadable or malformed source pin: {exc}",),
            composes=composes,
            boundary=(
                "A malformed pin is a custody failure, not a stale-but-trusted "
                "reference; re-pin explicitly after reviewing owner changes."
            ),
        )
    findings.extend(errors)
    state = "current" if not errors else "stale"
    return SectionReport(
        name="bridge_source_pin",
        state=state,
        findings=tuple(findings),
        composes=composes,
        boundary=(
            "Custody binds owner bytes, not a perpetually refreshed HEAD. "
            "Currency here means the pinned working trees still match; it is "
            "not native proof, not semantic review, and not proof that an "
            "older execution artifact was produced by these sources."
        ),
    )


def native_receipt_section(
    root: Path, *, receipt_path: Path | None = None
) -> SectionReport:
    """Read the native verification receipt with its claim boundary."""
    receipt = receipt_path or root / NATIVE_RECEIPT
    composes = ("fep_lean.output.evidence.validate_native_lean_receipt",)
    if not receipt.is_file():
        return SectionReport(
            name="native_verification_receipt",
            state="missing",
            findings=("output/native-verification.json: absent",),
            composes=composes,
            boundary=(
                "No native receipt exists, so no Lean compilation claim is "
                "bound to current sources. Catalogue-mode output must never "
                "be read as Lean evidence."
            ),
        )
    validation = validate_native_lean_receipt(receipt, project_root=root)
    findings = [
        f"valid: {validation.get('valid', False)}",
        f"native_claim_ready: {validation.get('native_claim_ready', False)}",
        f"selected topics: {validation.get('selected_topics', 0)}",
        f"verified topics: {validation.get('verified_topics', 0)}",
        f"warnings: {validation.get('warning_count', 0)}",
        f"sorry: {validation.get('sorry_count', 0)}",
    ]
    findings.extend(str(error) for error in validation.get("errors", []))
    state = "claim_ready" if validation.get("native_claim_ready") else "not_claim_ready"
    return SectionReport(
        name="native_verification_receipt",
        state=state,
        findings=tuple(findings),
        composes=composes,
        boundary=(
            "Claim readiness covers exact-source native compilation of the "
            "selected roster at the recorded digests, with zero errors, "
            "warnings, and sorry. It is not a Hermes/OpenGauss full run, not "
            "semantic review of a theorem proxy, and not a proof of the FEP; "
            "compilation of a Lean body never promotes its disposition."
        ),
    )


def build_status_report(root: Path, gnn_root: Path | None = None) -> StatusReport:
    """Compose the four evidence-currency sections for *root*."""
    return StatusReport(
        sections=(
            catalogue_products_section(root),
            render_receipt_section(root),
            bridge_pin_section(root, gnn_root),
            native_receipt_section(root),
        )
    )


def report_to_json(report: StatusReport) -> str:
    """Serialize the report for the CLI's JSON output convention."""
    return json.dumps(report.as_dict(), indent=2, default=str)
