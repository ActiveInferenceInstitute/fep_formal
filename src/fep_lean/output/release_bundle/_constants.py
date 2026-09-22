"""Canonical release-bundle constants, regexes, and receipt paths."""

import re
from collections.abc import Mapping
from pathlib import Path

from fep_lean.output.browser_capture import BROWSER_RECEIPT

RELEASE_BUNDLE_SCHEMA_VERSION = 1

MANIFEST_NAME = "MANIFEST.json"

CHECKSUMS_NAME = "SHA256SUMS"

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

_GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")

_CHECKSUM_LINE_RE = re.compile(r"^([0-9a-f]{64})  ([^\r\n]+)$")

_PDF_ID_RE = re.compile(rb"/ID\s*\[\s*<([0-9A-Fa-f]{32})>\s*<([0-9A-Fa-f]{32})>\s*\]")

_MARKDOWN_IMAGE_RE = re.compile(r"!\[[^\]\r\n]*\]\(\s*(?:<([^>\r\n]+)>|([^\s)\r\n]+))")

_RESOURCE_MARKUP_RE = re.compile(
    r"<\s*(?:audio|embed|iframe|image|img|link|object|script|source|track|video)\b"
    r"|\burl\s*\(|@import\b",
    re.IGNORECASE,
)

_CANONICAL_LICENSE = "CC-BY-4.0"

_CANONICAL_PUBLICATION_DOI = "10.5281/zenodo.19699233"

_CANONICAL_PUBLICATION_JOURNAL = "Active Inference Journal"

_CANONICAL_REPOSITORY_URL = "https://github.com/ActiveInferenceInstitute/fep_formal"

_CANONICAL_RELEASE_VERSION = "1.2.0"

_CANONICAL_RELEASE_DATE = "2026-09-17"

_MINIMUM_SPDX_SETUPTOOLS_REQUIREMENT = "setuptools>=77.0.3"

_MAX_ARCHIVE_MEMBERS = 20_000

_MAX_MEMBER_BYTES = 512 * 1024 * 1024

_MAX_ARCHIVE_BYTES = 1024 * 1024 * 1024

_MAX_TOTAL_MEMBER_BYTES = 2 * 1024 * 1024 * 1024

_PANDOC_TIMEOUT_SECONDS = 600

_PDF_TIMEOUT_SECONDS = 1_200

_PYTHON_ACCEPTANCE_TIMEOUT_SECONDS = 7_200

PUBLICATION_HTML = Path("output/manuscript/fep-lean-manuscript.html")

PUBLICATION_PDF = Path("output/manuscript/fep-lean-manuscript.pdf")

RENDERER_PROVENANCE = Path("output/manuscript/renderer-provenance.json")

NUMERICAL_RECEIPT = Path("output/numerical-witnesses.json")

PYTEST_RECEIPT = Path("output/pytest.xml")

PYTHON_COVERAGE_RECEIPT = Path("output/coverage.xml")

PYTHON_ACCEPTANCE_RECEIPT = Path("output/python-acceptance.json")

_PYTHON_ACCEPTANCE_EXPLICIT_PLUGINS = (
    "pytest_cov.plugin",
    "pytest_httpserver.pytest_plugin",
    "pytest_timeout",
)

_PYTHON_ACCEPTANCE_DISTRIBUTIONS = (
    "coverage",
    "pluggy",
    "pytest",
    "pytest-cov",
    "pytest-httpserver",
    "pytest-timeout",
)

_PYTHON_ACCEPTANCE_EXTERNAL_TOOLS: tuple[str, ...] = (
    # The two host mechanisms the suite's tool-dependent lanes need beyond the
    # interpreter and uv directories: `git` (the bridge custody/pin lanes build
    # throwaway sibling checkouts) and fontconfig (`fc-list`, the face-coverage
    # probe the render-font lanes and the render preflight run). The
    # PATH-controlled acceptance environment carries exactly these executables
    # and nothing broader.
    "git",
    "fc-list",
)

_PYTHON_ACCEPTANCE_USER_FONT_DIRECTORIES: tuple[str, ...] = (
    # The standard user font directories fontconfig resolves under $HOME. The
    # acceptance environment redirects HOME into the temporary root, which
    # would hide every user-installed face exactly when the font lanes must
    # ask whether this host covers the manuscript; each present directory is
    # mirrored as a symlink so the redirected HOME sees the same inventory.
    ".fonts",
    ".local/share/fonts",
    "Library/Fonts",
)

_PYTHON_ACCEPTANCE_ARGUMENTS: tuple[str, ...] = (
    "tests",
    "-q",
    "--color=no",
    "--strict-markers",
    "--tb=short",
    # The serial_lean lane needs lake/lean on PATH (plus the pinned Mathlib
    # tree); the hermetic acceptance environment deliberately strips PATH, so
    # those probes cannot run there. The documented canonical command (CI and
    # the AGENTS.md required checks) deselects them with the same marker.
    "-m",
    "not serial_lean",
    "--cov=src",
    "--cov-fail-under=89",
    "--cov-report=term",
    "--cov-report=xml:output/coverage.xml",
    "--junitxml=output/pytest.xml",
    "-o",
    "junit_family=xunit2",
    "-o",
    "addopts=",
)

_MANUSCRIPT_FIGURE_REFERENCES: Mapping[str, str] = {
    "../output/figures/status_distribution.png": (
        "output/figures/status_distribution.png"
    ),
}

_REQUIRED_STATIC_MEMBERS: tuple[tuple[str, str], ...] = (
    (".aii/config.yaml", "institute_metadata"),
    ("README.md", "project_documentation"),
    ("LICENSE", "legal_metadata"),
    ("CITATION.cff", "citation_metadata"),
    ("manuscript/config.yaml", "manuscript_metadata"),
    ("manuscript/assets/graphical-abstract.png", "graphical_abstract"),
    ("manuscript/manuscript_vars.yaml", "manuscript_metadata"),
    ("manuscript/preamble.md", "manuscript_source"),
    ("manuscript/references.bib", "bibliography"),
    (
        "manuscript/09z_unified_formalism_catalogue.md",
        "generated_formalism_appendix",
    ),
    ("docs/formalism-coverage.json", "formalism_coverage"),
    ("docs/formalism-coverage.md", "formalism_coverage"),
    ("docs/theorem-maturity-audit.md", "theorem_maturity"),
    ("docs/formalism-atlas.svg", "formalism_visualization"),
    ("docs/formalism-atlas.html", "formalism_visualization"),
    ("docs/formal-kernel-dashboard.svg", "numerical_visualization"),
    ("docs/formal-kernel-dashboard.html", "numerical_visualization"),
    ("output/native-verification.json", "native_lean_receipt"),
    ("output/formalism-audit.json", "declaration_axiom_receipt"),
    (PYTEST_RECEIPT.as_posix(), "python_test_receipt"),
    (PYTHON_COVERAGE_RECEIPT.as_posix(), "python_coverage_receipt"),
    (BROWSER_RECEIPT.as_posix(), "browser_receipt"),
    (PUBLICATION_HTML.as_posix(), "rendered_manuscript"),
    (
        "output/manuscript/assets/graphical-abstract.png",
        "rendered_manuscript_asset",
    ),
    (RENDERER_PROVENANCE.as_posix(), "renderer_provenance"),
)

_PROVIDER_MEMBER_PREFIXES = (
    "output/reports/",
    "provider/",
    "external-full-mode/",
)

_STATIC_REQUIRED_BUNDLE_PATHS = frozenset(
    {
        *(path for path, _evidence_class in _REQUIRED_STATIC_MEMBERS),
        NUMERICAL_RECEIPT.as_posix(),
        PYTHON_ACCEPTANCE_RECEIPT.as_posix(),
        "lean/FepSketches/fep_all.lean",
    }
)
