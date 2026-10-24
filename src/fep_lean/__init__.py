"""Public fep_lean API.

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

from fep_lean._paths import FepLeanError, project_root, project_root_context

if TYPE_CHECKING:
    from fep_lean.catalogue import (
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
    from fep_lean.gauss.cli import check_gauss_cli
    from fep_lean.gauss.client import OpenGaussClient, SessionRecord
    from fep_lean.gauss.runner import GaussRunner, TopicRunResult
    from fep_lean.llm.hermes import (
        HermesAPIError,
        HermesConfig,
        HermesExplainer,
        HermesResult,
    )
    from fep_lean.output.evidence import (
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
    from fep_lean.output.figures import write_all_catalogue_figures
    from fep_lean.output.formal_kernel_dashboard import (
        FormalKernelDashboard,
        build_formal_kernel_dashboard,
        formal_kernel_dashboard_drift,
        render_formal_kernel_dashboard_html,
        render_formal_kernel_dashboard_svg,
        write_formal_kernel_dashboard,
    )
    from fep_lean.output.formalism_atlas import (
        FormalismAtlas,
        atlas_projection_drift,
        build_formalism_atlas,
        render_formalism_atlas_html,
        render_formalism_atlas_svg,
        write_formalism_atlas,
    )
    from fep_lean.output.manuscript import (
        build_manuscript_vars,
        build_unified_formalism_appendix_markdown,
        manuscript_projection_drift,
        write_manuscript_vars,
        write_unified_formalism_appendix_markdown,
    )
    from fep_lean.output.rendering import (
        ManuscriptRenderError,
        render_manuscript,
        unresolved_placeholders,
    )
    from fep_lean.output.reporter import Reporter, ReportPaths, validate_report_receipt
    from fep_lean.pipeline.core import FEPPipeline, PipelineResult, StepResult
    from fep_lean.pipeline.orchestrator import run_pipeline, run_single_topic
    from fep_lean.verification.environment import run_validation_checks
    from fep_lean.verification.formalism_audit import (
        FormalismAuditResult,
        FormalismEvidenceRecord,
        build_formalism_probe,
        run_formalism_audit,
        validate_formalism_audit_receipt,
        write_formalism_audit_receipt,
    )
    from fep_lean.verification.lean_verifier import LeanVerifier, VerifyResult

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
    "PublicationReadinessReport": "fep_lean.output.evidence",
    "SectionReport": "fep_lean.output.evidence",
    "StatusReport": "fep_lean.output.evidence",
    "build_status_report": "fep_lean.output.evidence",
    "report_to_json": "fep_lean.output.evidence",
    "CapabilityNode": "fep_lean.catalogue",
    "CapabilityStatus": "fep_lean.catalogue",
    "CatalogueMetadata": "fep_lean.catalogue",
    "CatalogueValidationError": "fep_lean.catalogue",
    "EdgeKind": "fep_lean.catalogue",
    "FEPPipeline": "fep_lean.pipeline.core",
    "FEPTopicCatalogue": "fep_lean.catalogue",
    "FormalKernelDashboard": "fep_lean.output.formal_kernel_dashboard",
    "FormalismAtlas": "fep_lean.output.formalism_atlas",
    "FormalismAuditResult": "fep_lean.verification.formalism_audit",
    "FormalismEdge": "fep_lean.catalogue",
    "FormalismEvidenceRecord": "fep_lean.verification.formalism_audit",
    "FormalismGraph": "fep_lean.catalogue",
    "GaussRunner": "fep_lean.gauss.runner",
    "HermesAPIError": "fep_lean.llm.hermes",
    "HermesConfig": "fep_lean.llm.hermes",
    "HermesExplainer": "fep_lean.llm.hermes",
    "HermesResult": "fep_lean.llm.hermes",
    "LeanVerifier": "fep_lean.verification.lean_verifier",
    "ManuscriptRenderError": "fep_lean.output.rendering",
    "OpenGaussClient": "fep_lean.gauss.client",
    "PipelineResult": "fep_lean.pipeline.core",
    "ReportPaths": "fep_lean.output.reporter",
    "Reporter": "fep_lean.output.reporter",
    "SemanticDisposition": "fep_lean.catalogue",
    "SemanticValidationError": "fep_lean.catalogue",
    "SessionRecord": "fep_lean.gauss.client",
    "StepResult": "fep_lean.pipeline.core",
    "TheoremMaturityAudit": "fep_lean.catalogue",
    "TheoremMaturityRecord": "fep_lean.catalogue",
    "TopicEntry": "fep_lean.catalogue",
    "TopicRunResult": "fep_lean.gauss.runner",
    "VerifyResult": "fep_lean.verification.lean_verifier",
    "atlas_projection_drift": "fep_lean.output.formalism_atlas",
    "build_formal_kernel_dashboard": "fep_lean.output.formal_kernel_dashboard",
    "build_formalism_atlas": "fep_lean.output.formalism_atlas",
    "build_formalism_probe": "fep_lean.verification.formalism_audit",
    "build_manuscript_vars": "fep_lean.output.manuscript",
    "build_native_lean_receipt": "fep_lean.output.evidence",
    "build_unified_formalism_appendix_markdown": "fep_lean.output.manuscript",
    "check_gauss_cli": "fep_lean.gauss.cli",
    "formal_kernel_dashboard_drift": "fep_lean.output.formal_kernel_dashboard",
    "latest_claim_ready_full_report": "fep_lean.output.evidence",
    "load_catalogue_metadata": "fep_lean.catalogue",
    "load_formalism_graph": "fep_lean.catalogue",
    "load_formalism_novelty": "fep_lean.catalogue",
    "load_theorem_maturity": "fep_lean.catalogue",
    "manuscript_projection_drift": "fep_lean.output.manuscript",
    "render_formal_kernel_dashboard_html": "fep_lean.output.formal_kernel_dashboard",
    "render_formal_kernel_dashboard_svg": "fep_lean.output.formal_kernel_dashboard",
    "render_formalism_atlas_html": "fep_lean.output.formalism_atlas",
    "render_formalism_atlas_svg": "fep_lean.output.formalism_atlas",
    "render_manuscript": "fep_lean.output.rendering",
    "run_formalism_audit": "fep_lean.verification.formalism_audit",
    "run_pipeline": "fep_lean.pipeline.orchestrator",
    "run_single_topic": "fep_lean.pipeline.orchestrator",
    "run_validation_checks": "fep_lean.verification.environment",
    "unresolved_placeholders": "fep_lean.output.rendering",
    "validate_formalism_audit_receipt": "fep_lean.verification.formalism_audit",
    "validate_native_lean_receipt": "fep_lean.output.evidence",
    "validate_report_receipt": "fep_lean.output.reporter",
    "write_all_catalogue_figures": "fep_lean.output.figures",
    "write_formal_kernel_dashboard": "fep_lean.output.formal_kernel_dashboard",
    "write_formalism_atlas": "fep_lean.output.formalism_atlas",
    "write_formalism_audit_receipt": "fep_lean.verification.formalism_audit",
    "write_manuscript_vars": "fep_lean.output.manuscript",
    "write_native_lean_receipt": "fep_lean.output.evidence",
    "write_unified_formalism_appendix_markdown": "fep_lean.output.manuscript",
}

__all__ = [
    "CapabilityNode",
    "CapabilityStatus",
    "CatalogueMetadata",
    "CatalogueValidationError",
    "EdgeKind",
    "FEPPipeline",
    "FEPTopicCatalogue",
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

    ``import fep_lean`` stays cheap; ``fep_lean.<Name>`` imports the owning
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
