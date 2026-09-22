"""Fail-closed prerequisite aggregation for release-bundle entry points."""

from pathlib import Path

from fep_lean.output import release_bundle as bundle
from fep_lean.output.formalism_presentation import (
    RELEASE_SEAL,
    FormalismPresentation,
)
from fep_lean.output.release_bundle._acceptance import (
    _python_acceptance_receipt_errors,
)
from fep_lean.output.release_bundle._constants import (
    PUBLICATION_HTML,
    RENDERER_PROVENANCE,
)
from fep_lean.output.release_bundle._core import (
    ReleaseBundleError,
    _relative_file_bytes,
)
from fep_lean.output.release_bundle._identity import (
    _bounded_manuscript_projection_errors,
    _license_metadata_errors,
)


def _base_prerequisite_errors(
    project_root: Path,
    *,
    presentation: FormalismPresentation | None = None,
) -> tuple[str, ...]:
    root = Path(project_root).resolve()
    errors: list[str] = []
    if not root.is_dir():
        return (f"project root is missing: {root}",)
    errors.extend(_license_metadata_errors(root))
    try:
        errors.extend(bundle.report_owner_errors(root))
        errors.extend(
            f"formalism coverage projection is stale: {path.relative_to(root)}"
            for path in bundle.formalism_coverage_drift(root)
        )
        if presentation is None:
            presentation = bundle.build_formalism_presentation(root)
        errors.extend(
            f"formalism atlas projection is stale: {path.relative_to(root)}"
            for path in bundle.atlas_projection_drift(root, presentation=presentation)
        )
        errors.extend(
            f"formal-kernel dashboard projection is stale: {path.relative_to(root)}"
            for path in bundle.formal_kernel_dashboard_drift(
                root, presentation=presentation
            )
        )
    except (OSError, TypeError, ValueError) as exc:
        errors.append(f"canonical projections cannot be validated: {exc}")
    errors.extend(
        _bounded_manuscript_projection_errors(root, presentation=presentation)
    )
    errors.extend(bundle._theorem_maturity_projection_errors(root))
    errors.extend(bundle._rendered_manuscript_errors(root))

    native = bundle.validate_native_lean_receipt(
        root / "output" / "native-verification.json", project_root=root
    )
    if not (
        native.get("valid") is True
        and native.get("source_bound") is True
        and native.get("native_claim_ready") is True
        and native.get("live_catalogue_topics") == RELEASE_SEAL["topics"]
        and native.get("selected_topics") == RELEASE_SEAL["topics"]
        and native.get("verified_topics") == RELEASE_SEAL["topics"]
    ):
        native_errors = native.get("errors")
        detail = "; ".join(native_errors) if isinstance(native_errors, list) else ""
        errors.append(f"native Lean receipt is not current and claim-ready: {detail}")
    errors.extend(
        f"formalism audit receipt is stale: {error}"
        for error in bundle.validate_formalism_audit_receipt(
            root / "output" / "formalism-audit.json", root
        )
    )
    errors.extend(bundle._browser_receipt_errors(root, presentation=presentation))
    errors.extend(_python_acceptance_receipt_errors(root))
    for relative, _evidence_class in bundle._REQUIRED_STATIC_MEMBERS:
        if relative in {PUBLICATION_HTML.as_posix(), RENDERER_PROVENANCE.as_posix()}:
            continue
        try:
            _relative_file_bytes(root, relative)
        except ReleaseBundleError as exc:
            errors.append(str(exc))
    return tuple(dict.fromkeys(errors))


def release_bundle_prerequisite_errors(
    project_root: Path,
    *,
    source_date_epoch: int | None = None,
    include_publication: bool = True,
    presentation: FormalismPresentation | None = None,
) -> tuple[str, ...]:
    """Return every current-source prerequisite failure without writing.

    ``presentation`` optionally carries an already-built formalism join from
    an earlier pass over the same root so repeated prerequisite validation
    reuses one immutable snapshot instead of rebuilding it.
    """
    if presentation is None:
        errors = list(bundle._base_prerequisite_errors(Path(project_root)))
    else:
        errors = list(
            bundle._base_prerequisite_errors(
                Path(project_root), presentation=presentation
            )
        )
    if include_publication:
        errors.extend(
            bundle.publication_manuscript_errors(
                project_root, source_date_epoch=source_date_epoch
            )
        )
    return tuple(dict.fromkeys(errors))
