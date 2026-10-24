"""Identity release/publication boundary contracts."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from fep_lean.output import release_bundle as bundle_module
from tests._support.release_bundle import (
    _write_release_metadata_fixture,
)

PROJ = Path(__file__).resolve().parents[1]


def test_bounded_manuscript_projection_accepts_zero_count_relation_kinds() -> None:
    project_root = Path(__file__).resolve().parents[1]

    assert "manuscript formalism relation counts are stale" not in (
        bundle_module._bounded_manuscript_projection_errors(project_root)
    )


def test_release_metadata_rejects_a_stale_institute_sidecar(tmp_path: Path) -> None:
    _write_release_metadata_fixture(tmp_path)
    sidecar = tmp_path / ".aii/config.yaml"
    sidecar.write_text(
        sidecar.read_text(encoding="utf-8").replace("v2.0.1", "v1.0.0"),
        encoding="utf-8",
    )

    assert bundle_module._license_metadata_errors(tmp_path) == (
        "InstituteOS sidecar description must identify release v2.0.1",
    )


def test_release_metadata_rejects_a_misdirected_repository_url(tmp_path: Path) -> None:
    _write_release_metadata_fixture(tmp_path)
    citation = tmp_path / "CITATION.cff"
    citation.write_text(
        citation.read_text(encoding="utf-8").replace(
            "repository-code: https://github.com/ActiveInferenceInstitute/fep_formal",
            "repository-code: https://github.com/example/wrong",
        ),
        encoding="utf-8",
    )

    assert bundle_module._license_metadata_errors(tmp_path) == (
        "CITATION.cff repository-code must be https://github.com/ActiveInferenceInstitute/fep_formal",
    )


def test_release_metadata_rejects_a_misdirected_package_url(tmp_path: Path) -> None:
    _write_release_metadata_fixture(tmp_path)
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        pyproject.read_text(encoding="utf-8").replace(
            'Repository = "https://github.com/ActiveInferenceInstitute/fep_formal"',
            'Repository = "https://github.com/example/wrong"',
        ),
        encoding="utf-8",
    )

    assert bundle_module._license_metadata_errors(tmp_path) == (
        "Python package Repository URL must be https://github.com/ActiveInferenceInstitute/fep_formal",
    )


def test_release_metadata_rejects_package_author_drift_from_citation(
    tmp_path: Path,
) -> None:
    _write_release_metadata_fixture(tmp_path)
    citation_path = tmp_path / "CITATION.cff"
    citation = yaml.safe_load(citation_path.read_text(encoding="utf-8"))
    citation["authors"][0]["given-names"] = "Ada"
    citation["authors"][0]["family-names"] = "Example"
    citation["authors"][0]["email"] = "ada@example.org"
    citation["preferred-citation"]["authors"] = citation["authors"]
    citation_path.write_text(
        yaml.safe_dump(citation, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )

    assert bundle_module._license_metadata_errors(tmp_path) == (
        (
            "Python package authors must match CITATION.cff canonical author "
            "Ada Example <ada@example.org>"
        ),
    )


def test_release_metadata_is_consistent_and_fail_closed(tmp_path: Path) -> None:
    _write_release_metadata_fixture(tmp_path)

    assert bundle_module._license_metadata_errors(tmp_path) == ()

    (tmp_path / "LICENSE").write_text(
        "Creative Commons Attribution 4.0 International (CC BY 4.0)\n",
        encoding="utf-8",
    )
    assert bundle_module._license_metadata_errors(tmp_path) == (
        "LICENSE does not declare DOI 10.5281/zenodo.19699233",
    )
    (tmp_path / "LICENSE").write_text(
        "Creative Commons Attribution 4.0 International (CC BY 4.0)\n"
        "Work-level concept DOI: https://doi.org/10.5281/zenodo.19699233\n",
        encoding="utf-8",
    )
    (tmp_path / "LICENSE").write_text(
        (tmp_path / "LICENSE").read_text(encoding="utf-8") + "Copyleft fixture\n",
        encoding="utf-8",
    )
    assert bundle_module._license_metadata_errors(tmp_path) == (
        "LICENSE must not describe CC-BY-4.0 as copyleft",
    )
    _write_release_metadata_fixture(tmp_path)

    (tmp_path / "manuscript/config.yaml").write_text(
        "paper:\n"
        '  version: "2.0.1"\n'
        '  date: "2026-10-24"\n'
        "publication:\n"
        "  doi: 10.0000/wrong\n"
        "  journal: Active Inference Journal\n"
        "metadata:\n"
        "  license: CC-BY-4.0\n",
        encoding="utf-8",
    )
    assert bundle_module._license_metadata_errors(tmp_path) == (
        "manuscript publication DOI must be 10.5281/zenodo.23607007",
    )

    (tmp_path / "manuscript/config.yaml").write_text(
        "paper:\n"
        '  version: "2.0.1"\n'
        '  date: "2026-10-24"\n'
        "publication:\n"
        "  doi: 10.5281/zenodo.23607007\n"
        "  journal: Other Journal\n"
        "metadata:\n"
        "  license: Apache-2.0\n",
        encoding="utf-8",
    )
    assert bundle_module._license_metadata_errors(tmp_path) == (
        "manuscript publication journal must be Active Inference Journal",
        "manuscript metadata license must be CC-BY-4.0",
    )

    (tmp_path / "manuscript/config.yaml").write_text(
        "paper:\n"
        '  version: "2.0.1"\n'
        '  date: "2026-10-24"\n'
        "publication:\n"
        "  doi: 10.5281/zenodo.23607007\n"
        "  journal: Active Inference Journal\n"
        "metadata:\n"
        "  license: CC-BY-4.0\n",
        encoding="utf-8",
    )
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "fixture"\nreadme = "README.md"\n'
        'authors = [{ name = "Daniel Ari Friedman", email = "daniel@activeinference.institute" }]\n\n'
        '[project.urls]\nRepository = "https://github.com/ActiveInferenceInstitute/fep_formal"\n'
        'Changelog = "https://github.com/ActiveInferenceInstitute/fep_formal/blob/main/CHANGELOG.md"\n'
        '"Concept DOI" = "https://doi.org/10.5281/zenodo.19699233"\n',
        encoding="utf-8",
    )
    assert bundle_module._license_metadata_errors(tmp_path) == (
        "Python build system must require setuptools>=77.0.3",
        "Python package license must be CC-BY-4.0",
        "Python package version must be 2.0.1",
    )

    _write_release_metadata_fixture(tmp_path)
    citation_path = tmp_path / "CITATION.cff"
    citation_path.write_text(
        citation_path.read_text(encoding="utf-8").replace(
            "doi: 10.5281/zenodo.23607007", "doi: 10.0000/wrong"
        ),
        encoding="utf-8",
    )
    assert bundle_module._license_metadata_errors(tmp_path) == (
        "CITATION.cff preferred-citation DOI must be 10.5281/zenodo.23607007",
    )

    _write_release_metadata_fixture(tmp_path)
    citation_path.write_text(
        citation_path.read_text(encoding="utf-8").replace(
            "journal: Active Inference Journal", "journal: Other Journal"
        ),
        encoding="utf-8",
    )
    assert bundle_module._license_metadata_errors(tmp_path) == (
        "CITATION.cff preferred-citation journal must be Active Inference Journal",
    )


@pytest.mark.parametrize(
    ("plane", "replacement"),
    [
        ("software", None),
        ("software", "10.5281/zenodo.19699233"),
        ("software", "10.5281/zenodo.23220027"),
        ("software", "10.5281/zenodo.23607007"),
        ("software", "10.5281/zenodo.23196892"),
        ("preferred", None),
        ("preferred", "10.5281/zenodo.19699233"),
        ("preferred", "10.5281/zenodo.23220027"),
        ("preferred", "10.5281/zenodo.23196891"),
        ("preferred", "10.5281/zenodo.22072956"),
        ("preferred_url", None),
        ("preferred_url", "https://doi.org/10.5281/zenodo.19699233"),
        ("preferred_url", "https://doi.org/10.5281/zenodo.23220027"),
        ("preferred_url", "https://doi.org/10.5281/zenodo.23196891"),
        ("preferred_url", "https://doi.org/10.5281/zenodo.22072956"),
        ("preferred_url", "http://doi.org/10.5281/zenodo.23607007"),
        ("manuscript", None),
        ("manuscript", "10.5281/zenodo.19699233"),
        ("manuscript", "10.5281/zenodo.23220027"),
        ("manuscript", "10.5281/zenodo.23196891"),
        ("manuscript", "10.5281/zenodo.22072956"),
    ],
)
def test_release_metadata_rejects_swapped_or_absent_doi_identity(
    tmp_path: Path, plane: str, replacement: str | None
) -> None:
    _write_release_metadata_fixture(tmp_path)
    relative = "manuscript/config.yaml" if plane == "manuscript" else "CITATION.cff"
    path = tmp_path / relative
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    if plane == "software":
        record, field = document, "doi"
        error = "CITATION.cff software concept DOI must be 10.5281/zenodo.23196891"
    elif plane == "manuscript":
        record, field = document["publication"], "doi"
        error = "manuscript publication DOI must be 10.5281/zenodo.23607007"
    else:
        record = document["preferred-citation"]
        field = "url" if plane == "preferred_url" else "doi"
        error = (
            "CITATION.cff preferred-citation URL must be "
            "https://doi.org/10.5281/zenodo.23607007"
            if field == "url"
            else "CITATION.cff preferred-citation DOI must be 10.5281/zenodo.23607007"
        )
    if replacement is None:
        record.pop(field)
    else:
        record[field] = replacement
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")

    assert bundle_module._license_metadata_errors(tmp_path) == (error,)


@pytest.mark.parametrize(
    "wrong_version_doi",
    [
        "10.5281/zenodo.19699233",
        "10.5281/zenodo.23196891",
        "10.5281/zenodo.22072956",
        "10.5281/zenodo.23220027",
        "10.5281/zenodo.23220028",
    ],
)
def test_release_metadata_rejects_matching_but_wrong_manuscript_version(
    tmp_path: Path, wrong_version_doi: str
) -> None:
    """Agreement between authored owners cannot replace the fixed release ID."""
    _write_release_metadata_fixture(tmp_path)
    citation_path = tmp_path / "CITATION.cff"
    citation = yaml.safe_load(citation_path.read_text(encoding="utf-8"))
    citation["preferred-citation"]["doi"] = wrong_version_doi
    citation["preferred-citation"]["url"] = f"https://doi.org/{wrong_version_doi}"
    citation_path.write_text(
        yaml.safe_dump(citation, sort_keys=False), encoding="utf-8"
    )
    manuscript_path = tmp_path / "manuscript/config.yaml"
    manuscript = yaml.safe_load(manuscript_path.read_text(encoding="utf-8"))
    manuscript["publication"]["doi"] = wrong_version_doi
    manuscript_path.write_text(
        yaml.safe_dump(manuscript, sort_keys=False), encoding="utf-8"
    )

    assert bundle_module._license_metadata_errors(tmp_path) == (
        "CITATION.cff preferred-citation DOI must be 10.5281/zenodo.23607007",
        "CITATION.cff preferred-citation URL must be https://doi.org/10.5281/zenodo.23607007",
        "manuscript publication DOI must be 10.5281/zenodo.23607007",
    )


@pytest.mark.parametrize(
    ("relative", "old", "new", "expected_error"),
    [
        (
            "LICENSE",
            "https://doi.org/10.5281/zenodo.19699233",
            "https://doi.org/10.5281/zenodo.23196891",
            "LICENSE does not declare DOI 10.5281/zenodo.19699233",
        ),
        (
            "pyproject.toml",
            '"Concept DOI" = "https://doi.org/10.5281/zenodo.19699233"',
            '"Concept DOI" = "https://doi.org/10.5281/zenodo.23220027"',
            "Python package Concept DOI URL must be https://doi.org/10.5281/zenodo.19699233",
        ),
        (
            ".aii/config.yaml",
            "concept DOI 10.5281/zenodo.19699233",
            "concept DOI 10.5281/zenodo.23220027",
            "InstituteOS sidecar description must identify concept DOI 10.5281/zenodo.19699233",
        ),
        (
            ".aii/config.yaml",
            "    doi: 10.5281/zenodo.19699233",
            "    doi: 10.5281/zenodo.23220027",
            "InstituteOS sidecar citation DOI must be 10.5281/zenodo.19699233",
        ),
    ],
)
def test_release_metadata_retains_each_scholarly_concept_guard(
    tmp_path: Path, relative: str, old: str, new: str, expected_error: str
) -> None:
    _write_release_metadata_fixture(tmp_path)
    path = tmp_path / relative
    before = path.read_text(encoding="utf-8")
    assert before.count(old) == 1
    path.write_text(before.replace(old, new), encoding="utf-8")

    assert bundle_module._license_metadata_errors(tmp_path) == (expected_error,)


@pytest.mark.parametrize(
    ("relative", "old", "new", "expected_error"),
    [
        (
            "CITATION.cff",
            'version: "2.0.1"',
            'version: "1.2.0"',
            "CITATION.cff version must be 2.0.1",
        ),
        (
            "CITATION.cff",
            'date-released: "2026-10-24"',
            'date-released: "2026-09-16"',
            "CITATION.cff date-released must be 2026-10-24",
        ),
        (
            "manuscript/config.yaml",
            'version: "2.0.1"',
            'version: "1.2.0"',
            "manuscript paper version must be 2.0.1",
        ),
        (
            "manuscript/config.yaml",
            'date: "2026-10-24"',
            'date: "2026-09-16"',
            "manuscript paper date must be 2026-10-24",
        ),
        (
            "pyproject.toml",
            'version = "2.0.1"',
            'version = "1.2.0"',
            "Python package version must be 2.0.1",
        ),
        (
            "src/fep_lean/__init__.py",
            '__version__ = "2.0.1"',
            '__version__ = "1.2.0"',
            "Python runtime version must be 2.0.1",
        ),
        (
            "config/settings.yaml",
            'version: "2.0.1"',
            'version: "1.2.0"',
            "runtime settings version must be 2.0.1",
        ),
    ],
)
def test_release_metadata_rejects_each_version_and_date_plane_independently(
    tmp_path: Path,
    relative: str,
    old: str,
    new: str,
    expected_error: str,
) -> None:
    _write_release_metadata_fixture(tmp_path)
    path = tmp_path / relative
    path.write_text(
        path.read_text(encoding="utf-8").replace(old, new), encoding="utf-8"
    )

    assert bundle_module._license_metadata_errors(tmp_path) == (expected_error,)


@pytest.mark.parametrize(
    ("relative", "duplicate", "expected_error"),
    [
        (
            "pyproject.toml",
            'version = "1.2.0"\n',
            "Python package version must be 2.0.1",
        ),
        (
            "src/fep_lean/__init__.py",
            '__version__ = "1.2.0"\n',
            "Python runtime version must be 2.0.1",
        ),
    ],
)
def test_release_metadata_rejects_ambiguous_duplicate_runtime_versions(
    tmp_path: Path,
    relative: str,
    duplicate: str,
    expected_error: str,
) -> None:
    _write_release_metadata_fixture(tmp_path)
    path = tmp_path / relative
    contents = path.read_text(encoding="utf-8")
    if relative == "pyproject.toml":
        contents = contents.replace(
            'version = "2.0.1"\n',
            'version = "2.0.1"\n' + duplicate,
            1,
        )
    else:
        contents += duplicate
    path.write_text(
        contents,
        encoding="utf-8",
    )

    assert bundle_module._license_metadata_errors(tmp_path) == (expected_error,)


def test_live_release_metadata_planes_are_consistent() -> None:
    project_root = Path(__file__).resolve().parents[1]

    assert bundle_module._license_metadata_errors(project_root) == ()
