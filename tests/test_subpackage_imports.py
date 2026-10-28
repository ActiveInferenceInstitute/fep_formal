"""Test the installed ``fep_formal`` package surface."""

from __future__ import annotations

from pathlib import Path

import tomllib

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_root_package_init_importable():
    """The distribution name is also the one importable root package."""
    import fep_formal

    assert fep_formal.__version__
    assert hasattr(fep_formal, "FEPTopicCatalogue")
    assert hasattr(fep_formal, "LeanVerifier")
    assert hasattr(fep_formal, "HermesExplainer")
    assert hasattr(fep_formal, "FEPPipeline")
    assert hasattr(fep_formal, "Reporter")
    assert hasattr(fep_formal, "SemanticDisposition")
    assert hasattr(fep_formal, "TheoremMaturityAudit")
    assert hasattr(fep_formal, "validate_native_lean_receipt")
    assert hasattr(fep_formal, "render_manuscript")
    assert hasattr(fep_formal, "manuscript_projection_drift")
    assert hasattr(fep_formal, "build_formalism_atlas")
    assert hasattr(fep_formal, "build_formal_kernel_dashboard")
    assert hasattr(fep_formal, "run_formalism_audit")
    assert len(fep_formal.__all__) > 10


def test_runtime_version_matches_distribution_metadata() -> None:
    """The public runtime version must not drift from the wheel metadata."""
    import fep_formal

    metadata = tomllib.loads(
        (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    assert fep_formal.__version__ == metadata["project"]["version"]


def test_catalogue_imports():
    from fep_formal.catalogue import (
        FEPTopicCatalogue,
        SemanticDisposition,
        TheoremMaturityAudit,
    )

    assert FEPTopicCatalogue is not None
    assert SemanticDisposition.FORMALIZED.value == "formalized"
    assert TheoremMaturityAudit is not None


def test_verification_imports():
    from fep_formal.verification.lean_verifier import LeanVerifier

    assert LeanVerifier is not None


def test_mathematical_methods_public_import_surface():
    from fep_formal import methods

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
        "load_packaged_formalism_query",
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
    from fep_formal.gauss.client import OpenGaussClient

    assert OpenGaussClient is not None


def test_llm_imports():
    from fep_formal.llm.hermes import HermesExplainer

    assert HermesExplainer is not None


def test_output_imports():
    from fep_formal.output import (
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
    from fep_formal.output.reporter import Reporter

    assert Reporter is not None


def test_pipeline_imports():
    from fep_formal.pipeline.core import FEPPipeline

    assert FEPPipeline is not None


def _layer_import_violations(source: str, *, release_owner: bool = False) -> list[str]:
    import ast

    tree = ast.parse(source)
    violations = []
    bundle_aliases = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module == "fep_formal.cli" or (
                module in {"fep_formal", "fep_lean"}
                and any(alias.name == "cli" for alias in node.names)
            ):
                violations.append("CLI dependency")
            if not release_owner and (
                module.startswith("fep_formal.output.release_bundle._")
                or (
                    module == "fep_formal.output.release_bundle"
                    and any(alias.name.startswith("_") for alias in node.names)
                )
            ):
                violations.append("private release import")
            if module == "fep_formal.output":
                bundle_aliases.update(
                    alias.asname or alias.name
                    for alias in node.names
                    if alias.name == "release_bundle"
                )
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "fep_formal.cli":
                    violations.append("CLI dependency")
                if not release_owner and alias.name.startswith(
                    "fep_formal.output.release_bundle._"
                ):
                    violations.append("private release import")
                if alias.name == "fep_formal.output.release_bundle" and alias.asname:
                    bundle_aliases.add(alias.asname)
    if not release_owner:
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Attribute)
                and (
                    ast.unparse(node.value) in bundle_aliases
                    or ast.unparse(node.value) == "fep_formal.output.release_bundle"
                )
                and node.attr.startswith("_")
            ):
                violations.append("private release attribute")
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "getattr"
                and len(node.args) >= 2
            ):
                owner, attribute = node.args[:2]
                if (
                    (
                        ast.unparse(owner) in bundle_aliases
                        or ast.unparse(owner) == "fep_formal.output.release_bundle"
                    )
                    and isinstance(attribute, ast.Constant)
                    and isinstance(attribute.value, str)
                    and attribute.value.startswith("_")
                ):
                    violations.append("private release getattr")
    return violations


def test_production_layers_do_not_import_cli_or_private_release_owners() -> None:
    package = PROJECT_ROOT / "src/fep_formal"
    violations = {}
    for path in package.rglob("*.py"):
        relative = path.relative_to(package)
        if relative.as_posix() == "__main__.py":
            # This exact executable adapter is the sole package-level caller
            # of the CLI. Operational layers retain the import-direction gate.
            import ast

            tree = ast.parse(path.read_text(encoding="utf-8"))
            assert len(tree.body) == 3
            assert isinstance(tree.body[1], ast.ImportFrom)
            assert tree.body[1].module == "fep_formal.cli"
            assert [alias.name for alias in tree.body[1].names] == ["main"]
            continue
        found = _layer_import_violations(
            path.read_text(encoding="utf-8"),
            release_owner=relative.parts[:2] == ("output", "release_bundle"),
        )
        if found:
            violations[str(relative)] = found
    assert not violations


def test_import_direction_guard_rejects_local_alias_and_private_access() -> None:
    candidates = [
        "def worker():\n from fep_formal.cli import main",
        "from fep_formal import cli as console",
        "import fep_formal.cli as console",
        "from fep_formal.output.release_bundle._core import private",
        "from fep_formal.output.release_bundle import _native_receipt_errors",
        "from fep_formal.output import release_bundle as rb\nrb._native_receipt_errors()",
        "import fep_formal.output.release_bundle as rb\ngetattr(rb, '_secret')()",
        "import fep_formal.output.release_bundle\nfep_formal.output.release_bundle._secret()",
    ]
    assert all(_layer_import_violations(source) for source in candidates)
    assert not _layer_import_violations(
        "from fep_formal.output.release_bundle import publication_input_snapshot"
    )
    assert not _layer_import_violations(
        "from fep_formal.output.release_bundle._core import private", release_owner=True
    )


def test_verification_subpackage_exports_canonical_operations() -> None:
    from fep_formal import verification
    from fep_formal.verification import environment, lean_verifier

    assert verification.setup_workspace is environment.setup_workspace
    assert verification.verify_catalogue is lean_verifier.verify_catalogue
    assert verification.CatalogueVerification is lean_verifier.CatalogueVerification


def test_explorer_keyboard_policy_has_one_public_owner() -> None:
    from fep_formal.output import (
        formal_kernel_dashboard,
        formalism_atlas,
        svg_presentation,
    )

    assert "EXPLORER_KEYBOARD_SCRIPT" in svg_presentation.__all__
    assert (
        formalism_atlas.EXPLORER_KEYBOARD_SCRIPT
        is svg_presentation.EXPLORER_KEYBOARD_SCRIPT
    )
    assert (
        formal_kernel_dashboard.EXPLORER_KEYBOARD_SCRIPT
        is svg_presentation.EXPLORER_KEYBOARD_SCRIPT
    )
