"""Public fep_lean API.

Subpackages
-----------
    catalogue/     — Data model and topics YAML
    verification/  — Lean 4 checker and environment validation
    gauss/         — OpenGauss API client, sessions, orchestrator
    llm/           — LLM backend wrapper (Hermes explainer)
    output/        — Artifact generators (figures, manuscript vars, reports)
    pipeline/      — 4-stage core DAG (Load Catalogue, Environment Validation,
                     Gauss Sessions, Manuscript Artifacts) and entry scripts
    bridge/        — cross-repo GNN custody + verification operations
    data/          — generated package data (topics.yaml)
    formal/        — Lean 4 sources mirrored/generated under lean/
"""

from __future__ import annotations

__version__ = "1.2.0"

from fep_lean._paths import project_root
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
    build_native_lean_receipt,
    latest_claim_ready_full_report,
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

__all__ = [
    "CapabilityNode",
    "CapabilityStatus",
    "CatalogueMetadata",
    "CatalogueValidationError",
    "EdgeKind",
    "FEPPipeline",
    "FEPTopicCatalogue",
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
    "ReportPaths",
    "Reporter",
    "SemanticDisposition",
    "SemanticValidationError",
    "SessionRecord",
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
    "render_formal_kernel_dashboard_html",
    "render_formal_kernel_dashboard_svg",
    "render_formalism_atlas_html",
    "render_formalism_atlas_svg",
    "render_manuscript",
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
