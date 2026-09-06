"""Canonical owner sets for full-run source and configuration receipts.

The report digest deliberately follows maintained source owners rather than a
recursive checkout snapshot. Python bytecode, editable-install metadata,
provider caches, reports, and other runtime products therefore cannot change a
claim's source identity, while every manifested formal Lean resource and its
workspace projection remains explicitly bound.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from pathlib import Path

from fep_lean.catalogue.registry import body_source_relative_paths
from fep_lean.formal.manifest import FORMAL_MODULES, formal_resource_relative_paths

OWNER_MANIFEST_VERSION = 15

# Globs are discovery rules only. They must never define the digest roster:
# deleting a source file would otherwise silently delete it from the claimed
# source universe. Any addition to these namespaces must be reviewed and added
# to this versioned roster before report or native receipts can source-bind.
SOURCE_OWNER_GLOBS: tuple[str, ...] = (
    "src/fep_lean/**/*.py",
    "scripts/*.py",
)

SOURCE_OWNER_ROSTER: tuple[str, ...] = (
    "scripts/01_fep_catalogue_and_figures.py",
    "scripts/02_run_single_topic.py",
    "scripts/03_lean_verify_only.py",
    "scripts/04_generate_reports.py",
    "scripts/_maint_build_fep_all_lean.py",
    "scripts/_maint_build_formal_modules.py",
    "scripts/_maint_build_lean_landscape.py",
    "scripts/_maint_build_topics_catalogue.py",
    "scripts/audit_formalisms.py",
    "scripts/build_formal_kernel_dashboard.py",
    "scripts/build_formalism_atlas.py",
    "scripts/build_formalism_coverage.py",
    "scripts/build_manuscript_figures.py",
    "scripts/build_release_bundle.py",
    "scripts/capture_browser_acceptance.py",
    "scripts/check_render_log.py",
    "scripts/render_manuscript.py",
    "scripts/theorem_maturity_audit.py",
    "scripts/verify_report_receipt.py",
    "src/fep_lean/__init__.py",
    "src/fep_lean/_paths.py",
    "src/fep_lean/lean_source.py",
    "src/fep_lean/catalogue/__init__.py",
    "src/fep_lean/catalogue/bodies/__init__.py",
    "src/fep_lean/catalogue/coverage.py",
    "src/fep_lean/catalogue/generation.py",
    "src/fep_lean/catalogue/latex.py",
    "src/fep_lean/catalogue/novelty.py",
    "src/fep_lean/catalogue/references.py",
    "src/fep_lean/catalogue/relations.py",
    "src/fep_lean/catalogue/registry.py",
    "src/fep_lean/catalogue/schema.py",
    "src/fep_lean/catalogue/semantics.py",
    "src/fep_lean/catalogue/topics.py",
    "src/fep_lean/bridge/__init__.py",
    "src/fep_lean/bridge/certificates.py",
    "src/fep_lean/bridge/cli.py",
    "src/fep_lean/bridge/custody.py",
    "src/fep_lean/bridge/operations.py",
    "src/fep_lean/cli.py",
    "src/fep_lean/data/__init__.py",
    "src/fep_lean/formal/__init__.py",
    "src/fep_lean/formal/declarations.py",
    "src/fep_lean/formal/manifest.py",
    "src/fep_lean/formal/projection.py",
    "src/fep_lean/gauss/__init__.py",
    "src/fep_lean/gauss/cli.py",
    "src/fep_lean/gauss/client.py",
    "src/fep_lean/gauss/runner.py",
    "src/fep_lean/llm/__init__.py",
    "src/fep_lean/llm/hermes.py",
    "src/fep_lean/output/__init__.py",
    "src/fep_lean/output/browser_capture.py",
    "src/fep_lean/output/evidence.py",
    "src/fep_lean/output/figures.py",
    "src/fep_lean/output/formal_kernel_dashboard.py",
    "src/fep_lean/output/formalism_atlas.py",
    "src/fep_lean/output/formalism_presentation.py",
    "src/fep_lean/output/manuscript.py",
    "src/fep_lean/output/provenance.py",
    "src/fep_lean/output/publication_metadata.py",
    "src/fep_lean/output/rendering.py",
    "src/fep_lean/output/release_bundle.py",
    "src/fep_lean/output/render_log.py",
    "src/fep_lean/output/reporter.py",
    "src/fep_lean/output/svg_raster.py",
    "src/fep_lean/pipeline/__init__.py",
    "src/fep_lean/pipeline/core.py",
    "src/fep_lean/pipeline/orchestrator.py",
    "src/fep_lean/verification/__init__.py",
    "src/fep_lean/verification/_horizon_numerical_witnesses.py",
    "src/fep_lean/verification/_toolchain.py",
    "src/fep_lean/verification/_subprocess.py",
    "src/fep_lean/verification/environment.py",
    "src/fep_lean/verification/formalism_audit.py",
    "src/fep_lean/verification/gnn_artifact_proof.py",
    "src/fep_lean/verification/gnn_artifact_receipt.py",
    "src/fep_lean/verification/gnn_continuous_artifact_proof.py",
    "src/fep_lean/verification/gnn_julia_artifact_proof.py",
    "src/fep_lean/verification/horizon_acceptance.py",
    "src/fep_lean/verification/lean_verifier.py",
    "src/fep_lean/verification/numerical_witnesses.py",
    "src/fep_lean/verification/preflight.py",
    *body_source_relative_paths(),
)

SOURCE_OWNER_FILES: tuple[str, ...] = (
    *SOURCE_OWNER_ROSTER,
    "lean/FepSketches/fep_all.lean",
)

CONFIG_OWNER_FILES: tuple[str, ...] = (
    "pyproject.toml",
    "uv.lock",
    "config/catalogue_metadata.yaml",
    "config/formalism_novelty.yaml",
    "config/formalism_relations.yaml",
    "config/settings.yaml",
    "config/theorem_maturity.yaml",
    "config/topics.yaml",
    "src/fep_lean/data/topics.yaml",
    "manuscript/config.yaml",
    "lean/lean-toolchain",
    "lean/lakefile.lean",
    "lean/lake-manifest.json",
)

CATALOGUE_SOURCE_FILES: tuple[str, ...] = (
    "config/catalogue_metadata.yaml",
    "config/formalism_novelty.yaml",
    "config/theorem_maturity.yaml",
    "src/fep_lean/catalogue/registry.py",
    *body_source_relative_paths(),
)


def _deduplicated(paths: Iterable[Path]) -> tuple[Path, ...]:
    """Return paths once in deterministic lexical order."""
    return tuple(sorted(set(paths), key=lambda path: path.as_posix()))


def source_owner_paths(project_root: Path) -> tuple[Path, ...]:
    """Return every maintained executable/formal source owner for reports."""
    root = Path(project_root)
    paths = [root / relative for relative in SOURCE_OWNER_FILES]
    paths.extend(root / relative for relative in formal_resource_relative_paths())
    paths.extend(
        root / "lean" / "FepSketches" / module.resource for module in FORMAL_MODULES
    )
    return _deduplicated(paths)


def config_owner_paths(project_root: Path) -> tuple[Path, ...]:
    """Return every maintained configuration/toolchain owner for reports."""
    root = Path(project_root)
    return _deduplicated(root / relative for relative in CONFIG_OWNER_FILES)


def digest_owner_paths(project_root: Path, paths: Iterable[Path]) -> str:
    """Hash owner paths and bytes, retaining missing owners in the identity."""
    root = Path(project_root)
    digest = hashlib.sha256()
    for path in _deduplicated(Path(path) for path in paths):
        relative = path.relative_to(root).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes() if path.is_file() else b"<missing>")
        digest.update(b"\0")
    return digest.hexdigest()


def report_source_digest(project_root: Path) -> str:
    """Return the canonical executable/formal source digest."""
    root = Path(project_root)
    return digest_owner_paths(root, source_owner_paths(root))


def report_config_digest(project_root: Path) -> str:
    """Return the canonical catalogue/configuration/toolchain digest."""
    root = Path(project_root)
    return digest_owner_paths(root, config_owner_paths(root))


def catalogue_source_paths(project_root: Path) -> tuple[Path, ...]:
    """Return maintained catalogue sources with body paths derived from the registry."""
    root = Path(project_root)
    return _deduplicated(root / relative for relative in CATALOGUE_SOURCE_FILES)


def catalogue_sources_digest(project_root: Path) -> str:
    """Return the exact maintained catalogue-source digest."""
    root = Path(project_root)
    return digest_owner_paths(root, catalogue_source_paths(root))


def report_owner_errors(project_root: Path) -> tuple[str, ...]:
    """Return fail-closed live-owner/projection errors for report validation."""
    root = Path(project_root)
    errors: list[str] = []
    if not root.is_dir():
        return (f"project root is missing: {root}",)

    discovered_source_owners = {
        path.relative_to(root).as_posix()
        for pattern in SOURCE_OWNER_GLOBS
        for path in root.glob(pattern)
        if path.is_file()
    }
    rostered_source_owners = set(SOURCE_OWNER_ROSTER)
    for relative in sorted(discovered_source_owners - rostered_source_owners):
        errors.append(
            f"source owner is absent from manifest v{OWNER_MANIFEST_VERSION}: {relative}"
        )
    for path in (*source_owner_paths(root), *config_owner_paths(root)):
        if not path.is_file():
            errors.append(
                f"canonical report owner is missing: {path.relative_to(root)}"
            )

    try:
        from fep_lean.catalogue.generation import (
            catalogue_projection_drift,
            fep_all_projection_drift,
        )
        from fep_lean.catalogue.topics import FEPTopicCatalogue
        from fep_lean.formal import formal_aggregate_drift, formal_projection_drift

        FEPTopicCatalogue.from_yaml(root / "config" / "topics.yaml")
        drift = (
            *catalogue_projection_drift(root),
            *fep_all_projection_drift(root),
            *formal_aggregate_drift(root),
            *formal_projection_drift(root),
        )
        errors.extend(
            f"canonical projection is stale: {path.relative_to(root)}" for path in drift
        )
    except (OSError, TypeError, ValueError) as exc:
        errors.append(f"canonical report owners cannot be loaded: {exc}")
    return tuple(dict.fromkeys(errors))
