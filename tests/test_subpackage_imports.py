"""Test the installed ``fep_lean`` package surface."""

from __future__ import annotations

from pathlib import Path

import tomllib

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_root_package_init_importable():
    """The distribution name is also the one importable root package."""
    import fep_lean

    assert fep_lean.__version__
    assert hasattr(fep_lean, "FEPTopicCatalogue")
    assert hasattr(fep_lean, "LeanVerifier")
    assert hasattr(fep_lean, "HermesExplainer")
    assert hasattr(fep_lean, "FEPPipeline")
    assert hasattr(fep_lean, "Reporter")
    assert hasattr(fep_lean, "SemanticDisposition")
    assert hasattr(fep_lean, "TheoremMaturityAudit")
    assert hasattr(fep_lean, "validate_native_lean_receipt")
    assert hasattr(fep_lean, "render_manuscript")
    assert hasattr(fep_lean, "manuscript_projection_drift")
    assert hasattr(fep_lean, "build_formalism_atlas")
    assert hasattr(fep_lean, "build_formal_kernel_dashboard")
    assert hasattr(fep_lean, "run_formalism_audit")
    assert len(fep_lean.__all__) > 10


def test_runtime_version_matches_distribution_metadata() -> None:
    """The public runtime version must not drift from the wheel metadata."""
    import fep_lean

    metadata = tomllib.loads(
        (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    assert fep_lean.__version__ == metadata["project"]["version"]


def test_catalogue_imports():
    from fep_lean.catalogue import (
        FEPTopicCatalogue,
        SemanticDisposition,
        TheoremMaturityAudit,
    )

    assert FEPTopicCatalogue is not None
    assert SemanticDisposition.FORMALIZED.value == "formalized"
    assert TheoremMaturityAudit is not None


def test_verification_imports():
    from fep_lean.verification.lean_verifier import LeanVerifier

    assert LeanVerifier is not None


def test_mathematical_methods_public_import_surface():
    from fep_lean import methods

    expected = {
        "BoundaryProbeError",
        "MathematicalPositioning",
        "PositioningError",
        "SourceOrigin",
        "analyze_topic",
        "bernoulli_fisher",
        "build_mathematical_positioning",
        "classical_mds",
        "cross_corpus_embedding",
        "evaluate_boundary_probes",
        "exponential_tilt",
        "export_mathematical_positioning",
        "extended_kl",
        "finite_expectation",
        "finite_kl_totalized",
        "gibbs_duality_diagnostics",
        "inspect_family",
        "inspect_topic",
        "log_partition",
        "inspect_theorem",
        "mathematical_positioning_bytes",
        "mathematical_positioning_drift",
        "package_resource_drift",
        "positioning_neighbors",
    }
    assert set(methods.__all__) == expected
    assert all(callable(getattr(methods, name)) for name in expected)


def test_gauss_imports():
    from fep_lean.gauss.client import OpenGaussClient

    assert OpenGaussClient is not None


def test_llm_imports():
    from fep_lean.llm.hermes import HermesExplainer

    assert HermesExplainer is not None


def test_output_imports():
    from fep_lean.output import (
        ManuscriptRenderError,
        ReleaseBundleError,
        build_formal_kernel_dashboard,
        build_formalism_atlas,
        build_manuscript_vars,
        build_numerical_witness_receipt,
        build_python_acceptance_receipt,
        build_release_bundle,
        build_typeset_equations_markdown,
        build_unified_formalism_appendix_markdown,
        manuscript_projection_drift,
        render_manuscript,
        render_publication_manuscript,
        validate_native_lean_receipt,
        validate_release_bundle,
        write_formal_kernel_dashboard,
        write_formalism_atlas,
        write_manuscript_vars,
        write_unified_formalism_appendix_markdown,
    )

    assert callable(build_manuscript_vars)
    assert callable(build_formalism_atlas)
    assert callable(build_formal_kernel_dashboard)
    assert callable(write_manuscript_vars)
    assert callable(write_unified_formalism_appendix_markdown)
    assert callable(build_typeset_equations_markdown)
    assert callable(build_unified_formalism_appendix_markdown)
    assert callable(manuscript_projection_drift)
    assert callable(write_unified_formalism_appendix_markdown)
    assert callable(render_manuscript)
    assert callable(render_publication_manuscript)
    assert callable(validate_native_lean_receipt)
    assert callable(build_numerical_witness_receipt)
    assert callable(build_python_acceptance_receipt)
    assert callable(build_release_bundle)
    assert callable(validate_release_bundle)
    assert callable(write_formalism_atlas)
    assert callable(write_formal_kernel_dashboard)
    assert issubclass(ManuscriptRenderError, ValueError)
    assert issubclass(ReleaseBundleError, ValueError)
    from fep_lean.output.reporter import Reporter

    assert Reporter is not None


def test_pipeline_imports():
    from fep_lean.pipeline.core import FEPPipeline

    assert FEPPipeline is not None
