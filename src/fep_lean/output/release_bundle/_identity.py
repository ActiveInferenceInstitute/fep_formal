"""Publication identity, licensing, and owner classification checks."""

import re
from collections import Counter
from functools import lru_cache
from pathlib import (
    Path,
    PurePosixPath,
)

import yaml

from fep_lean.catalogue.relations import EdgeKind
from fep_lean.catalogue.theorem_maturity_projection import (
    render_markdown,
    validate_audit,
)
from fep_lean.catalogue.topics import FEPTopicCatalogue
from fep_lean.output import release_bundle as bundle
from fep_lean.output.browser_capture import (
    CANONICAL_BROWSER_SCREENSHOTS as _CANONICAL_BROWSER_SCREENSHOTS,
)
from fep_lean.output.formalism_presentation import FormalismPresentation
from fep_lean.output.publication_metadata import (
    PublicationMetadataError,
    load_publication_author,
)
from fep_lean.output.release_bundle._constants import (
    _CANONICAL_LICENSE,
    _CANONICAL_PUBLICATION_DOI,
    _CANONICAL_PUBLICATION_JOURNAL,
    _CANONICAL_RELEASE_DATE,
    _CANONICAL_RELEASE_VERSION,
    _CANONICAL_REPOSITORY_URL,
    _MANUSCRIPT_FIGURE_REFERENCES,
    _MINIMUM_SPDX_SETUPTOOLS_REQUIREMENT,
    NUMERICAL_RECEIPT,
    PUBLICATION_PDF,
    PYTHON_ACCEPTANCE_RECEIPT,
)
from fep_lean.output.release_bundle._core import (
    ReleaseBundleError,
    _relative_file_bytes,
)
from fep_lean.output.release_bundle._manuscript import (
    _manuscript_variables,
)


@lru_cache(maxsize=1)
def _canonical_owner_names() -> tuple[frozenset[str], frozenset[str]]:
    synthetic_root = Path("/__fep_lean_release_root__")
    source_names = frozenset(
        path.relative_to(synthetic_root).as_posix()
        for path in bundle.source_owner_paths(synthetic_root)
    )
    config_names = frozenset(
        path.relative_to(synthetic_root).as_posix()
        for path in bundle.config_owner_paths(synthetic_root)
    )
    return source_names, config_names


def _expected_evidence_class(name: str) -> str | None:
    """Return the sole allowed evidence class for a recognized bundle path."""
    source_names, config_names = _canonical_owner_names()
    if name in source_names:
        return "manifested_lean_source" if name.endswith(".lean") else "source_owner"
    if name in config_names:
        return "configuration_snapshot"
    static_classes = dict(bundle._REQUIRED_STATIC_MEMBERS)
    if name in static_classes:
        return static_classes[name]
    if name == NUMERICAL_RECEIPT.as_posix():
        return "numerical_non_proof_receipt"
    if name == PYTHON_ACCEPTANCE_RECEIPT.as_posix():
        return "python_acceptance_receipt"
    if name in _CANONICAL_BROWSER_SCREENSHOTS.values():
        return "browser_screenshot"
    if name in _MANUSCRIPT_FIGURE_REFERENCES.values():
        return "rendered_manuscript_figure"
    if name == PUBLICATION_PDF.as_posix():
        return "rendered_manuscript_pdf"
    rendered_asset_names = {
        (Path("output/manuscript") / destination).as_posix()
        for _source, destination in bundle.MANUSCRIPT_ASSETS.values()
    }
    if name in rendered_asset_names:
        return "rendered_manuscript_asset"
    path = PurePosixPath(name)
    if path.parent == PurePosixPath("output/manuscript") and path.suffix == ".md":
        return "rendered_manuscript"
    return None


def _theorem_maturity_projection_errors(project_root: Path) -> tuple[str, ...]:
    root = Path(project_root).resolve()
    try:
        expected = render_markdown(validate_audit(root))
        actual = (root / "docs" / "theorem-maturity-audit.md").read_text(
            encoding="utf-8"
        )
    except (KeyError, OSError, TypeError, ValueError) as exc:
        return (f"theorem-maturity projection cannot be validated: {exc}",)
    return () if actual == expected else ("theorem-maturity projection is stale",)


def _license_metadata_errors(project_root: Path) -> tuple[str, ...]:
    """Require one publication identity across every bundled metadata plane."""
    root = Path(project_root).resolve()
    errors: list[str] = []
    try:
        canonical_author = load_publication_author(root)
    except PublicationMetadataError as exc:
        canonical_author = None
        errors.append(f"CITATION.cff author metadata cannot be read: {exc}")
    try:
        license_text = _relative_file_bytes(root, "LICENSE").decode("utf-8")
    except (ReleaseBundleError, UnicodeDecodeError) as exc:
        errors.append(f"canonical license text cannot be read: {exc}")
    else:
        if "Creative Commons Attribution 4.0 International (CC BY 4.0)" not in (
            license_text
        ):
            errors.append(f"LICENSE does not declare {_CANONICAL_LICENSE}")
        if f"https://doi.org/{_CANONICAL_PUBLICATION_DOI}" not in license_text:
            errors.append(f"LICENSE does not declare DOI {_CANONICAL_PUBLICATION_DOI}")
        if re.search(r"\bcopyleft\b", license_text, re.IGNORECASE) is not None:
            errors.append("LICENSE must not describe CC-BY-4.0 as copyleft")

    try:
        citation = yaml.safe_load(
            _relative_file_bytes(root, "CITATION.cff").decode("utf-8")
        )
    except (ReleaseBundleError, UnicodeDecodeError, yaml.YAMLError) as exc:
        errors.append(f"CITATION.cff license cannot be read: {exc}")
    else:
        if not isinstance(citation, dict) or citation.get("license") != (
            _CANONICAL_LICENSE
        ):
            errors.append(f"CITATION.cff license must be {_CANONICAL_LICENSE}")
        if not isinstance(citation, dict) or citation.get("version") != (
            _CANONICAL_RELEASE_VERSION
        ):
            errors.append(f"CITATION.cff version must be {_CANONICAL_RELEASE_VERSION}")
        if not isinstance(citation, dict) or citation.get("date-released") != (
            _CANONICAL_RELEASE_DATE
        ):
            errors.append(
                f"CITATION.cff date-released must be {_CANONICAL_RELEASE_DATE}"
            )
        if not isinstance(citation, dict) or citation.get("repository-code") != (
            _CANONICAL_REPOSITORY_URL
        ):
            errors.append(
                f"CITATION.cff repository-code must be {_CANONICAL_REPOSITORY_URL}"
            )
        if not isinstance(citation, dict) or citation.get("url") != (
            _CANONICAL_REPOSITORY_URL
        ):
            errors.append(f"CITATION.cff URL must be {_CANONICAL_REPOSITORY_URL}")
        preferred = (
            citation.get("preferred-citation") if isinstance(citation, dict) else None
        )
        if not isinstance(preferred, dict) or preferred.get("doi") != (
            _CANONICAL_PUBLICATION_DOI
        ):
            errors.append(
                "CITATION.cff preferred-citation DOI must be "
                f"{_CANONICAL_PUBLICATION_DOI}"
            )
        if not isinstance(preferred, dict) or preferred.get("journal") != (
            _CANONICAL_PUBLICATION_JOURNAL
        ):
            errors.append(
                "CITATION.cff preferred-citation journal must be "
                f"{_CANONICAL_PUBLICATION_JOURNAL}"
            )

    try:
        manuscript = yaml.safe_load(
            _relative_file_bytes(root, "manuscript/config.yaml").decode("utf-8")
        )
    except (ReleaseBundleError, UnicodeDecodeError, yaml.YAMLError) as exc:
        errors.append(f"manuscript license metadata cannot be read: {exc}")
    else:
        publication = (
            manuscript.get("publication") if isinstance(manuscript, dict) else None
        )
        if not isinstance(publication, dict) or publication.get("doi") != (
            _CANONICAL_PUBLICATION_DOI
        ):
            errors.append(
                f"manuscript publication DOI must be {_CANONICAL_PUBLICATION_DOI}"
            )
        if not isinstance(publication, dict) or publication.get("journal") != (
            _CANONICAL_PUBLICATION_JOURNAL
        ):
            errors.append(
                "manuscript publication journal must be "
                f"{_CANONICAL_PUBLICATION_JOURNAL}"
            )
        metadata = manuscript.get("metadata") if isinstance(manuscript, dict) else None
        if not isinstance(metadata, dict) or metadata.get("license") != (
            _CANONICAL_LICENSE
        ):
            errors.append(f"manuscript metadata license must be {_CANONICAL_LICENSE}")
        paper = manuscript.get("paper") if isinstance(manuscript, dict) else None
        if not isinstance(paper, dict) or paper.get("version") != (
            _CANONICAL_RELEASE_VERSION
        ):
            errors.append(
                f"manuscript paper version must be {_CANONICAL_RELEASE_VERSION}"
            )
        if not isinstance(paper, dict) or paper.get("date") != (
            _CANONICAL_RELEASE_DATE
        ):
            errors.append(f"manuscript paper date must be {_CANONICAL_RELEASE_DATE}")

    try:
        pyproject = _relative_file_bytes(root, "pyproject.toml").decode("utf-8")
    except (ReleaseBundleError, UnicodeDecodeError) as exc:
        errors.append(f"Python package license metadata cannot be read: {exc}")
    else:
        build_section = re.search(
            r"(?ms)^\[build-system\]\s*(.*?)(?=^\[[^\n]+\]|\Z)", pyproject
        )
        build_requires = (
            re.search(
                rf'(?m)^requires\s*=\s*\[[^\]]*"{re.escape(_MINIMUM_SPDX_SETUPTOOLS_REQUIREMENT)}"[^\]]*\]\s*$',
                build_section.group(1),
            )
            if build_section is not None
            else None
        )
        if build_requires is None:
            errors.append(
                "Python build system must require "
                f"{_MINIMUM_SPDX_SETUPTOOLS_REQUIREMENT}"
            )
        project_section = re.search(
            r"(?ms)^\[project\]\s*(.*?)(?=^\[[^\n]+\]|\Z)", pyproject
        )
        package_license = (
            re.search(r'(?m)^license\s*=\s*"([^"]+)"\s*$', project_section.group(1))
            if project_section is not None
            else None
        )
        if package_license is None or package_license.group(1) != _CANONICAL_LICENSE:
            errors.append(f"Python package license must be {_CANONICAL_LICENSE}")
        package_versions = (
            re.findall(r'(?m)^version\s*=\s*"([^"]+)"\s*$', project_section.group(1))
            if project_section is not None
            else []
        )
        if package_versions != [_CANONICAL_RELEASE_VERSION]:
            errors.append(
                f"Python package version must be {_CANONICAL_RELEASE_VERSION}"
            )
        package_readme = (
            re.search(r'(?m)^readme\s*=\s*"([^"]+)"\s*$', project_section.group(1))
            if project_section is not None
            else None
        )
        if package_readme is None or package_readme.group(1) != "README.md":
            errors.append("Python package readme must be README.md")
        package_authors = (
            re.search(r"(?ms)^authors\s*=\s*\[(.*?)\]", project_section.group(1))
            if project_section is not None
            else None
        )
        authors_text = package_authors.group(1) if package_authors is not None else ""
        package_author_records = re.findall(
            r'\{\s*name\s*=\s*"([^"]+)"\s*,\s*email\s*=\s*"([^"]+)"\s*,?\s*\}',
            authors_text,
        )
        if canonical_author is not None and package_author_records != [
            (canonical_author.name, canonical_author.email)
        ]:
            errors.append(
                "Python package authors must match CITATION.cff canonical author "
                f"{canonical_author.name} <{canonical_author.email}>"
            )
        urls_section = re.search(
            r"(?ms)^\[project\.urls\]\s*(.*?)(?=^\[[^\n]+\]|\Z)", pyproject
        )
        urls_text = urls_section.group(1) if urls_section is not None else ""
        expected_urls = {
            "Repository": _CANONICAL_REPOSITORY_URL,
            "Changelog": f"{_CANONICAL_REPOSITORY_URL}/blob/main/CHANGELOG.md",
            "Concept DOI": f"https://doi.org/{_CANONICAL_PUBLICATION_DOI}",
        }
        for label, expected_url in expected_urls.items():
            quoted_label = re.escape(f'"{label}"' if " " in label else label)
            match = re.search(rf'(?m)^{quoted_label}\s*=\s*"([^"]+)"\s*$', urls_text)
            if match is None or match.group(1) != expected_url:
                errors.append(f"Python package {label} URL must be {expected_url}")

    try:
        package_init = _relative_file_bytes(root, "src/fep_lean/__init__.py").decode(
            "utf-8"
        )
    except (ReleaseBundleError, UnicodeDecodeError) as exc:
        errors.append(f"Python runtime version cannot be read: {exc}")
    else:
        runtime_versions = re.findall(
            r'(?m)^__version__\s*=\s*"([^"]+)"\s*$', package_init
        )
        if runtime_versions != [_CANONICAL_RELEASE_VERSION]:
            errors.append(
                f"Python runtime version must be {_CANONICAL_RELEASE_VERSION}"
            )

    try:
        settings = yaml.safe_load(
            _relative_file_bytes(root, "config/settings.yaml").decode("utf-8")
        )
    except (ReleaseBundleError, UnicodeDecodeError, yaml.YAMLError) as exc:
        errors.append(f"runtime settings version cannot be read: {exc}")
    else:
        project = settings.get("project") if isinstance(settings, dict) else None
        if not isinstance(project, dict) or project.get("version") != (
            _CANONICAL_RELEASE_VERSION
        ):
            errors.append(
                f"runtime settings version must be {_CANONICAL_RELEASE_VERSION}"
            )

    try:
        sidecar = yaml.safe_load(
            _relative_file_bytes(root, ".aii/config.yaml").decode("utf-8")
        )
    except (ReleaseBundleError, UnicodeDecodeError, yaml.YAMLError) as exc:
        errors.append(f"InstituteOS sidecar metadata cannot be read: {exc}")
    else:
        meta = sidecar.get("meta") if isinstance(sidecar, dict) else None
        if not isinstance(meta, dict) or meta.get("updated") != (
            _CANONICAL_RELEASE_DATE
        ):
            errors.append(
                f"InstituteOS sidecar update date must be {_CANONICAL_RELEASE_DATE}"
            )
        repo = sidecar.get("repo") if isinstance(sidecar, dict) else None
        description = str(repo.get("description", "")) if isinstance(repo, dict) else ""
        if f"Release v{_CANONICAL_RELEASE_VERSION}" not in description:
            errors.append(
                "InstituteOS sidecar description must identify release "
                f"v{_CANONICAL_RELEASE_VERSION}"
            )
        if _CANONICAL_RELEASE_DATE not in description:
            errors.append(
                "InstituteOS sidecar description must identify release date "
                f"{_CANONICAL_RELEASE_DATE}"
            )
        if _CANONICAL_PUBLICATION_DOI not in description:
            errors.append(
                "InstituteOS sidecar description must identify concept DOI "
                f"{_CANONICAL_PUBLICATION_DOI}"
            )
        if not isinstance(repo, dict) or repo.get("full_name") != (
            "ActiveInferenceInstitute/fep_formal"
        ):
            errors.append(
                "InstituteOS sidecar repository must be "
                "ActiveInferenceInstitute/fep_formal"
            )
        ecosystem = sidecar.get("ecosystem") if isinstance(sidecar, dict) else None
        links = ecosystem.get("links") if isinstance(ecosystem, dict) else None
        if not isinstance(links, dict) or links.get("github") != (
            _CANONICAL_REPOSITORY_URL
        ):
            errors.append(
                f"InstituteOS sidecar GitHub URL must be {_CANONICAL_REPOSITORY_URL}"
            )
        provenance = sidecar.get("provenance") if isinstance(sidecar, dict) else None
        if not isinstance(provenance, dict) or provenance.get("license") != (
            _CANONICAL_LICENSE
        ):
            errors.append(f"InstituteOS sidecar license must be {_CANONICAL_LICENSE}")
        sidecar_citation = (
            provenance.get("citation") if isinstance(provenance, dict) else None
        )
        if not isinstance(sidecar_citation, dict) or sidecar_citation.get("doi") != (
            _CANONICAL_PUBLICATION_DOI
        ):
            errors.append(
                f"InstituteOS sidecar citation DOI must be {_CANONICAL_PUBLICATION_DOI}"
            )
    return tuple(errors)


def _bounded_manuscript_projection_errors(
    project_root: Path,
    *,
    presentation: FormalismPresentation | None = None,
) -> tuple[str, ...]:
    """Validate canonical manuscript variables without launching test collection."""
    root = Path(project_root).resolve()
    try:
        variables = _manuscript_variables(root)
        catalogue = FEPTopicCatalogue.from_yaml(root / "config" / "topics.yaml")
        summary = catalogue.summary()
        if presentation is None:
            presentation = bundle.build_formalism_presentation(root)
    except (OSError, TypeError, ValueError) as exc:
        return (f"manuscript variables cannot be validated: {exc}",)
    errors: list[str] = []
    for key in (
        "total_topics",
        "families",
        "maturity",
        "area_maturity",
        "semantic_dispositions",
        "area_semantic_dispositions",
    ):
        if variables.get(key) != summary[key]:
            errors.append(f"manuscript variable is stale: {key}")
    expected_areas = {
        area: {"count": count} for area, count in summary["areas"].items()
    }
    if variables.get("areas") != expected_areas:
        errors.append("manuscript variable is stale: areas")
    if variables.get("total_areas") != len(expected_areas):
        errors.append("manuscript variable is stale: total_areas")
    topic_ids = [topic.id for topic in catalogue.topics]
    if variables.get("topic_ids") != topic_ids:
        errors.append("manuscript variable is stale: topic_ids")
    topic_variables = variables.get("topics")
    if not isinstance(topic_variables, dict) or tuple(topic_variables) != tuple(
        topic_ids
    ):
        errors.append("manuscript topic-variable roster is stale")
    else:
        for topic in catalogue.topics:
            row = topic_variables.get(topic.id)
            expected = {
                "title": topic.title,
                "area": topic.area,
                "maturity": topic.mathlib_status,
                "mathlib_status": topic.mathlib_status,
                "primary_theorem": topic.primary_theorem,
                "semantic_disposition": topic.semantic_disposition,
                "assumption_review": topic.assumption_review,
                "non_vacuity": topic.non_vacuity,
                "acceptance_probe": topic.acceptance_probe,
                "lean_chars": topic.lean_chars,
                "nl_statement": topic.nl,
                "lean_sketch": topic.lean_sketch,
                "latex_equations": list(topic.latex_equations),
            }
            if not isinstance(row, dict) or any(
                row.get(key) != value for key, value in expected.items()
            ):
                errors.append(f"manuscript topic variables are stale: {topic.id}")

    formalism = variables.get("formalism")
    observed_relation_counts = Counter(row.kind for row in presentation.relations)
    relation_counts = {
        kind.value: observed_relation_counts.get(kind.value, 0) for kind in EdgeKind
    }
    capability_counts = dict(Counter(row.status for row in presentation.capabilities))
    if not isinstance(formalism, dict):
        errors.append("manuscript formalism variables are missing")
    else:
        if formalism.get("metrics") != dict(presentation.metrics):
            errors.append("manuscript formalism metrics are stale")
        if formalism.get("relation_counts") != relation_counts:
            errors.append("manuscript formalism relation counts are stale")
        if formalism.get("capability_status_counts") != {
            status: capability_counts.get(status, 0)
            for status in ("satisfied", "partial", "open")
        }:
            errors.append("manuscript capability counts are stale")
    try:
        drift = bundle.manuscript_projection_drift(
            root,
            catalogue,
            expected_variables=variables,
        )
    except (OSError, TypeError, ValueError) as exc:
        errors.append(f"manuscript appendix cannot be validated: {exc}")
    else:
        errors.extend(
            f"manuscript projection is stale: {path.relative_to(root)}"
            for path in drift
        )
    return tuple(dict.fromkeys(errors))
