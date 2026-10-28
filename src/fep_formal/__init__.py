"""Public fep_formal API.

Subpackages
-----------
    catalogue/     — Data model and topics YAML
    verification/  — Lean 4 checker and environment validation
    gauss/         — OpenGauss API client, sessions, orchestrator
    llm/           — LLM backend wrapper (Hermes explainer)
    output/        — Artifact generators (figures, manuscript vars, reports)
    pipeline/      — 4-stage core DAG (Load Catalog, Environment Validation,
                     Gauss Sessions, Manuscript Artifacts) and entry scripts
    bridge/        — cross-repo GNN custody + verification operations
    data/          — generated package data (topics.yaml)
    formal/        — Lean 4 sources mirrored/generated under lean/
"""

from __future__ import annotations

__version__ = "2.1.0"

# Capture the installed/source package before importing any subpackage. The
# mathematical methods use this immutable identity to reject edited sources
# behind already cached Python modules. This is an import-consistency check;
# the explicit report/native owner roster and custody policy remain separate.
import hashlib as _runtime_hashlib
from pathlib import Path as _RuntimePath
from types import MappingProxyType as _RuntimeMappingProxyType

_runtime_package_root = _RuntimePath(__file__).resolve().parent
_SOURCE_RUNTIME_SHA256 = _RuntimeMappingProxyType(
    {
        path.relative_to(_runtime_package_root).as_posix(): _runtime_hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in sorted(_runtime_package_root.rglob("*.py"))
        if path.is_file()
    }
)

import importlib as _importlib
from typing import TYPE_CHECKING

from fep_formal._paths import (
    FepFormalError,
    FepLeanError,
    project_root,
    project_root_context,
)

if TYPE_CHECKING:
    from fep_formal.catalogue import (
        CapabilityNode,
        CapabilityStatus,
        CatalogueMetadata,
        CatalogueValidationError,
        EdgeKind,
        FEPTopicCatalogue,
        FormalismEdge,
        FormalismGraph,
        SemanticDisposition,
        SemanticValidationError,
        TheoremMaturityAudit,
        TheoremMaturityRecord,
        TopicEntry,
        load_catalogue_metadata,
        load_formalism_graph,
        load_formalism_novelty,
        load_theorem_maturity,
    )
    from fep_formal.gauss.cli import check_gauss_cli
    from fep_formal.gauss.client import OpenGaussClient, SessionRecord
    from fep_formal.gauss.runner import GaussRunner, TopicRunResult
    from fep_formal.llm.hermes import (
        HermesAPIError,
        HermesConfig,
        HermesExplainer,
        HermesResult,
    )
    from fep_formal.output.evidence import (
        PublicationReadinessReport,
        SectionReport,
        StatusReport,
        build_native_lean_receipt,
        build_status_report,
        latest_claim_ready_full_report,
        report_to_json,
        validate_native_lean_receipt,
        write_native_lean_receipt,
    )
    from fep_formal.output.figures import write_all_catalogue_figures
    from fep_formal.output.formal_kernel_dashboard import (
        FormalKernelDashboard,
        build_formal_kernel_dashboard,
        formal_kernel_dashboard_drift,
        render_formal_kernel_dashboard_html,
        render_formal_kernel_dashboard_svg,
        write_formal_kernel_dashboard,
    )
    from fep_formal.output.formalism_atlas import (
        FormalismAtlas,
        atlas_projection_drift,
        build_formalism_atlas,
        render_formalism_atlas_html,
        render_formalism_atlas_svg,
        write_formalism_atlas,
    )
    from fep_formal.output.manuscript import (
        build_manuscript_vars,
        build_unified_formalism_appendix_markdown,
        manuscript_projection_drift,
        write_manuscript_vars,
        write_unified_formalism_appendix_markdown,
    )
    from fep_formal.output.rendering import (
        ManuscriptRenderError,
        render_manuscript,
        unresolved_placeholders,
    )
    from fep_formal.output.reporter import (
        Reporter,
        ReportPaths,
        validate_report_receipt,
    )
    from fep_formal.pipeline.core import FEPPipeline, PipelineResult, StepResult
    from fep_formal.pipeline.orchestrator import run_pipeline, run_single_topic
    from fep_formal.verification.environment import run_validation_checks
    from fep_formal.verification.formalism_audit import (
        FormalismAuditResult,
        FormalismEvidenceRecord,
        build_formalism_probe,
        run_formalism_audit,
        validate_formalism_audit_receipt,
        write_formalism_audit_receipt,
    )
    from fep_formal.verification.lean_verifier import LeanVerifier, VerifyResult

# Subpackages the eager imports used to bind as attributes; kept in dir().
_SUBPACKAGES = (
    "catalogue",
    "formal",
    "gauss",
    "lean_source",
    "llm",
    "output",
    "pipeline",
    "verification",
)

_LAZY_EXPORTS = {
    "PublicationReadinessReport": "fep_formal.output.evidence",
    "SectionReport": "fep_formal.output.evidence",
    "StatusReport": "fep_formal.output.evidence",
    "build_status_report": "fep_formal.output.evidence",
    "report_to_json": "fep_formal.output.evidence",
    "CapabilityNode": "fep_formal.catalogue",
    "CapabilityStatus": "fep_formal.catalogue",
    "CatalogueMetadata": "fep_formal.catalogue",
    "CatalogueValidationError": "fep_formal.catalogue",
    "EdgeKind": "fep_formal.catalogue",
    "FEPPipeline": "fep_formal.pipeline.core",
    "FEPTopicCatalogue": "fep_formal.catalogue",
    "FormalKernelDashboard": "fep_formal.output.formal_kernel_dashboard",
    "FormalismAtlas": "fep_formal.output.formalism_atlas",
    "FormalismAuditResult": "fep_formal.verification.formalism_audit",
    "FormalismEdge": "fep_formal.catalogue",
    "FormalismEvidenceRecord": "fep_formal.verification.formalism_audit",
    "FormalismGraph": "fep_formal.catalogue",
    "GaussRunner": "fep_formal.gauss.runner",
    "HermesAPIError": "fep_formal.llm.hermes",
    "HermesConfig": "fep_formal.llm.hermes",
    "HermesExplainer": "fep_formal.llm.hermes",
    "HermesResult": "fep_formal.llm.hermes",
    "LeanVerifier": "fep_formal.verification.lean_verifier",
    "ManuscriptRenderError": "fep_formal.output.rendering",
    "OpenGaussClient": "fep_formal.gauss.client",
    "PipelineResult": "fep_formal.pipeline.core",
    "ReportPaths": "fep_formal.output.reporter",
    "Reporter": "fep_formal.output.reporter",
    "SemanticDisposition": "fep_formal.catalogue",
    "SemanticValidationError": "fep_formal.catalogue",
    "SessionRecord": "fep_formal.gauss.client",
    "StepResult": "fep_formal.pipeline.core",
    "TheoremMaturityAudit": "fep_formal.catalogue",
    "TheoremMaturityRecord": "fep_formal.catalogue",
    "TopicEntry": "fep_formal.catalogue",
    "TopicRunResult": "fep_formal.gauss.runner",
    "VerifyResult": "fep_formal.verification.lean_verifier",
    "atlas_projection_drift": "fep_formal.output.formalism_atlas",
    "build_formal_kernel_dashboard": "fep_formal.output.formal_kernel_dashboard",
    "build_formalism_atlas": "fep_formal.output.formalism_atlas",
    "build_formalism_probe": "fep_formal.verification.formalism_audit",
    "build_manuscript_vars": "fep_formal.output.manuscript",
    "build_native_lean_receipt": "fep_formal.output.evidence",
    "build_unified_formalism_appendix_markdown": "fep_formal.output.manuscript",
    "check_gauss_cli": "fep_formal.gauss.cli",
    "formal_kernel_dashboard_drift": "fep_formal.output.formal_kernel_dashboard",
    "latest_claim_ready_full_report": "fep_formal.output.evidence",
    "load_catalogue_metadata": "fep_formal.catalogue",
    "load_formalism_graph": "fep_formal.catalogue",
    "load_formalism_novelty": "fep_formal.catalogue",
    "load_theorem_maturity": "fep_formal.catalogue",
    "manuscript_projection_drift": "fep_formal.output.manuscript",
    "render_formal_kernel_dashboard_html": "fep_formal.output.formal_kernel_dashboard",
    "render_formal_kernel_dashboard_svg": "fep_formal.output.formal_kernel_dashboard",
    "render_formalism_atlas_html": "fep_formal.output.formalism_atlas",
    "render_formalism_atlas_svg": "fep_formal.output.formalism_atlas",
    "render_manuscript": "fep_formal.output.rendering",
    "run_formalism_audit": "fep_formal.verification.formalism_audit",
    "run_pipeline": "fep_formal.pipeline.orchestrator",
    "run_single_topic": "fep_formal.pipeline.orchestrator",
    "run_validation_checks": "fep_formal.verification.environment",
    "unresolved_placeholders": "fep_formal.output.rendering",
    "validate_formalism_audit_receipt": "fep_formal.verification.formalism_audit",
    "validate_native_lean_receipt": "fep_formal.output.evidence",
    "validate_report_receipt": "fep_formal.output.reporter",
    "write_all_catalogue_figures": "fep_formal.output.figures",
    "write_formal_kernel_dashboard": "fep_formal.output.formal_kernel_dashboard",
    "write_formalism_atlas": "fep_formal.output.formalism_atlas",
    "write_formalism_audit_receipt": "fep_formal.verification.formalism_audit",
    "write_manuscript_vars": "fep_formal.output.manuscript",
    "write_native_lean_receipt": "fep_formal.output.evidence",
    "write_unified_formalism_appendix_markdown": "fep_formal.output.manuscript",
}

__all__ = [
    "CapabilityNode",
    "CapabilityStatus",
    "CatalogueMetadata",
    "CatalogueValidationError",
    "EdgeKind",
    "FEPPipeline",
    "FEPTopicCatalogue",
    "FepFormalError",
    "FepLeanError",
    "FormalKernelDashboard",
    "FormalismAtlas",
    "FormalismAuditResult",
    "FormalismEdge",
    "FormalismEvidenceRecord",
    "FormalismGraph",
    "GaussRunner",
    "HermesAPIError",
    "HermesConfig",
    "HermesExplainer",
    "HermesResult",
    "LeanVerifier",
    "ManuscriptRenderError",
    "OpenGaussClient",
    "PipelineResult",
    "PublicationReadinessReport",
    "ReportPaths",
    "Reporter",
    "SectionReport",
    "SemanticDisposition",
    "SemanticValidationError",
    "SessionRecord",
    "StatusReport",
    "StepResult",
    "TheoremMaturityAudit",
    "TheoremMaturityRecord",
    "TopicEntry",
    "TopicRunResult",
    "VerifyResult",
    "atlas_projection_drift",
    "build_formal_kernel_dashboard",
    "build_formalism_atlas",
    "build_formalism_probe",
    "build_manuscript_vars",
    "build_native_lean_receipt",
    "build_status_report",
    "build_unified_formalism_appendix_markdown",
    "check_gauss_cli",
    "formal_kernel_dashboard_drift",
    "latest_claim_ready_full_report",
    "load_catalogue_metadata",
    "load_formalism_graph",
    "load_formalism_novelty",
    "load_theorem_maturity",
    "manuscript_projection_drift",
    "project_root",
    "project_root_context",
    "render_formal_kernel_dashboard_html",
    "render_formal_kernel_dashboard_svg",
    "render_formalism_atlas_html",
    "render_formalism_atlas_svg",
    "render_manuscript",
    "report_to_json",
    "run_formalism_audit",
    "run_pipeline",
    "run_single_topic",
    "run_validation_checks",
    "unresolved_placeholders",
    "validate_formalism_audit_receipt",
    "validate_native_lean_receipt",
    "validate_report_receipt",
    "write_all_catalogue_figures",
    "write_formal_kernel_dashboard",
    "write_formalism_atlas",
    "write_formalism_audit_receipt",
    "write_manuscript_vars",
    "write_native_lean_receipt",
    "write_unified_formalism_appendix_markdown",
]


def __getattr__(name: str) -> object:
    """Resolve heavy public re-exports on first access (PEP 562).

    ``import fep_formal`` stays cheap; ``fep_formal.<Name>`` imports the owning
    subpackage once and caches the attribute on this module.
    """
    if name in _SUBPACKAGES:
        return _importlib.import_module(f"{__name__}.{name}")
    module_name = _LAZY_EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(_importlib.import_module(module_name), name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    hidden = {"_importlib", "_LAZY_EXPORTS", "_SUBPACKAGES", "__getattr__", "__dir__"}
    return sorted({*globals(), *__all__, *_SUBPACKAGES} - hidden)
