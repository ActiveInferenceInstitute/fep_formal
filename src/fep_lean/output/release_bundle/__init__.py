"""Deterministic, fail-closed publication evidence bundles.

The archive is a transport for already validated evidence, never a new proof
plane.  Every member is a regular file with normalized metadata; the manifest
and checksum table describe the exact payload without a recursive self-hash.
"""

from __future__ import (
    annotations as annotations,
)

import gzip as gzip
import hashlib as hashlib
import importlib.metadata as importlib  # noqa: F401
import io as io
import json as json
import math as math
import os as os
import re as re
import shlex as shlex
import shutil as shutil
import struct as struct
import subprocess as subprocess
import sys as sys
import tarfile as tarfile
import tempfile as tempfile
import xml.etree.ElementTree as ET  # noqa: F401
import zlib as zlib
from collections import (
    Counter as Counter,
)
from collections.abc import (
    Mapping as Mapping,
)
from collections.abc import (
    Sequence as Sequence,
)
from dataclasses import (
    dataclass as dataclass,
)
from functools import (
    lru_cache as lru_cache,
)
from pathlib import (
    Path as Path,
)
from pathlib import (
    PurePosixPath as PurePosixPath,
)
from typing import (
    Any as Any,
)

import yaml as yaml

from fep_lean.catalogue.coverage import (
    formalism_coverage_drift as formalism_coverage_drift,
)
from fep_lean.catalogue.relations import (
    EdgeKind as EdgeKind,
)
from fep_lean.catalogue.theorem_maturity_projection import (
    render_markdown as render_markdown,
)
from fep_lean.catalogue.theorem_maturity_projection import (
    validate_audit as validate_audit,
)
from fep_lean.catalogue.topics import (
    FEPTopicCatalogue as FEPTopicCatalogue,
)
from fep_lean.output.browser_capture import (
    BROWSER_ASSET_ROOT as BROWSER_ASSET_ROOT,
)
from fep_lean.output.browser_capture import (
    BROWSER_RECEIPT as BROWSER_RECEIPT,
)
from fep_lean.output.browser_capture import (
    CANONICAL_BROWSER_PROJECTIONS as _CANONICAL_BROWSER_PROJECTIONS,  # noqa: F401
)
from fep_lean.output.browser_capture import (
    CANONICAL_BROWSER_SCREENSHOTS as _CANONICAL_BROWSER_SCREENSHOTS,  # noqa: F401
)
from fep_lean.output.browser_capture import (
    REQUIRED_BROWSER_INTERACTIONS as _REQUIRED_BROWSER_INTERACTIONS,  # noqa: F401
)
from fep_lean.output.browser_capture import (
    BrowserCaptureError as BrowserCaptureError,
)
from fep_lean.output.browser_capture import (
    canonical_browser_capture_provenance as canonical_browser_capture_provenance,
)
from fep_lean.output.browser_capture import (
    canonical_browser_observations as canonical_browser_observations,
)
from fep_lean.output.browser_capture import (
    canonical_browser_render_configuration as canonical_browser_render_configuration,
)
from fep_lean.output.browser_capture import (
    replay_browser_acceptance as replay_browser_acceptance,
)
from fep_lean.output.browser_capture import (
    resolve_browser_executable as resolve_browser_executable,
)
from fep_lean.output.evidence import (
    validate_native_lean_receipt as validate_native_lean_receipt,
)
from fep_lean.output.formal_kernel_dashboard import (
    formal_kernel_dashboard_drift as formal_kernel_dashboard_drift,
)
from fep_lean.output.formalism_atlas import (
    atlas_projection_drift as atlas_projection_drift,
)
from fep_lean.output.formalism_presentation import (
    RELEASE_CAPABILITIES as RELEASE_CAPABILITIES,
)
from fep_lean.output.formalism_presentation import (
    RELEASE_FAMILIES as RELEASE_FAMILIES,
)
from fep_lean.output.formalism_presentation import (
    RELEASE_RELATIONS as RELEASE_RELATIONS,
)
from fep_lean.output.formalism_presentation import (
    RELEASE_SEAL as RELEASE_SEAL,
)
from fep_lean.output.formalism_presentation import (
    RELEASE_TOPICS as RELEASE_TOPICS,
)
from fep_lean.output.formalism_presentation import (
    RELEASE_WITNESSES as RELEASE_WITNESSES,
)
from fep_lean.output.formalism_presentation import (
    FormalismPresentation as FormalismPresentation,
)
from fep_lean.output.formalism_presentation import (
    build_formalism_presentation as build_formalism_presentation,
)
from fep_lean.output.fsutil import (
    atomic_write_bytes as atomic_write_bytes,
)
from fep_lean.output.fsutil import (
    sha256_bytes as sha256_bytes,
)
from fep_lean.output.fsutil import (
    sha256_file as sha256_file,
)
from fep_lean.output.manuscript import (
    collection_runtime_identity as collection_runtime_identity,
)
from fep_lean.output.manuscript import (
    manuscript_projection_drift as manuscript_projection_drift,
)
from fep_lean.output.manuscript import (
    parse_pytest_collection_stdout as parse_pytest_collection_stdout,
)
from fep_lean.output.manuscript import (
    pytest_collection_command as pytest_collection_command,
)
from fep_lean.output.manuscript import (
    pytest_collection_environment as pytest_collection_environment,
)
from fep_lean.output.provenance import (
    config_owner_paths as config_owner_paths,
)
from fep_lean.output.provenance import (
    report_config_digest as report_config_digest,
)
from fep_lean.output.provenance import (
    report_owner_errors as report_owner_errors,
)
from fep_lean.output.provenance import (
    report_source_digest as report_source_digest,
)
from fep_lean.output.provenance import (
    source_owner_paths as source_owner_paths,
)
from fep_lean.output.publication_metadata import (
    GraphicalAbstractAsset as GraphicalAbstractAsset,
)
from fep_lean.output.publication_metadata import (
    PublicationMetadataError as PublicationMetadataError,
)
from fep_lean.output.publication_metadata import (
    load_graphical_abstract as load_graphical_abstract,
)
from fep_lean.output.publication_metadata import (
    load_publication_author as load_publication_author,
)
from fep_lean.output.release_bundle._acceptance import (
    _canonical_coverage_path as _canonical_coverage_path,
)
from fep_lean.output.release_bundle._acceptance import (
    _canonical_python_source_records as _canonical_python_source_records,
)
from fep_lean.output.release_bundle._acceptance import (
    _collect_python_node_ids as _collect_python_node_ids,
)
from fep_lean.output.release_bundle._acceptance import (
    _controlled_python_acceptance_path as _controlled_python_acceptance_path,
)
from fep_lean.output.release_bundle._acceptance import (
    _distribution_fingerprint as _distribution_fingerprint,
)
from fep_lean.output.release_bundle._acceptance import (
    _junit_identity_from_node_id as _junit_identity_from_node_id,
)
from fep_lean.output.release_bundle._acceptance import (
    _normalized_python_acceptance_command as _normalized_python_acceptance_command,
)
from fep_lean.output.release_bundle._acceptance import (
    _pytest_receipt_errors as _pytest_receipt_errors,
)
from fep_lean.output.release_bundle._acceptance import (
    _python_acceptance_command as _python_acceptance_command,
)
from fep_lean.output.release_bundle._acceptance import (
    _python_acceptance_environment as _python_acceptance_environment,
)
from fep_lean.output.release_bundle._acceptance import (
    _python_acceptance_external_executable as _python_acceptance_external_executable,
)
from fep_lean.output.release_bundle._acceptance import (
    _python_acceptance_home_font_mirrors as _python_acceptance_home_font_mirrors,
)
from fep_lean.output.release_bundle._acceptance import (
    _python_acceptance_receipt_errors as _python_acceptance_receipt_errors,
)
from fep_lean.output.release_bundle._acceptance import (
    _python_acceptance_runtime_identity as _python_acceptance_runtime_identity,
)
from fep_lean.output.release_bundle._acceptance import (
    _python_acceptance_tool_bin as _python_acceptance_tool_bin,
)
from fep_lean.output.release_bundle._acceptance import (
    _python_acceptance_tool_identity as _python_acceptance_tool_identity,
)
from fep_lean.output.release_bundle._acceptance import (
    _python_evidence_summary as _python_evidence_summary,
)
from fep_lean.output.release_bundle._acceptance import (
    _python_input_snapshot as _python_input_snapshot,
)
from fep_lean.output.release_bundle._acceptance import (
    _python_test_records as _python_test_records,
)
from fep_lean.output.release_bundle._acceptance import (
    _restore_python_acceptance_files as _restore_python_acceptance_files,
)
from fep_lean.output.release_bundle._acceptance import (
    build_numerical_witness_receipt as build_numerical_witness_receipt,
)
from fep_lean.output.release_bundle._acceptance import (
    build_python_acceptance_receipt as build_python_acceptance_receipt,
)
from fep_lean.output.release_bundle._acceptance import (
    run_python_acceptance as run_python_acceptance,
)
from fep_lean.output.release_bundle._acceptance import (
    write_numerical_witnesses as write_numerical_witnesses,
)
from fep_lean.output.release_bundle._assemble import (
    _add_member as _add_member,
)
from fep_lean.output.release_bundle._assemble import (
    _archive_contents as _archive_contents,
)
from fep_lean.output.release_bundle._assemble import (
    _build_manifest as _build_manifest,
)
from fep_lean.output.release_bundle._assemble import (
    _digest_snapshot_classes as _digest_snapshot_classes,
)
from fep_lean.output.release_bundle._assemble import (
    _live_snapshot_fingerprint as _live_snapshot_fingerprint,
)
from fep_lean.output.release_bundle._assemble import (
    _member_by_path as _member_by_path,
)
from fep_lean.output.release_bundle._assemble import (
    _project_members as _project_members,
)
from fep_lean.output.release_bundle._assemble import (
    _snapshot_fingerprint as _snapshot_fingerprint,
)
from fep_lean.output.release_bundle._assemble import (
    _supplemental_snapshot_records as _supplemental_snapshot_records,
)
from fep_lean.output.release_bundle._assemble import (
    _toolchain_identity as _toolchain_identity,
)
from fep_lean.output.release_bundle._assemble import (
    _toolchain_identity_from_members as _toolchain_identity_from_members,
)
from fep_lean.output.release_bundle._assemble import (
    _write_archive as _write_archive,
)
from fep_lean.output.release_bundle._assemble import (
    build_release_bundle as build_release_bundle,
)
from fep_lean.output.release_bundle._browser import (
    _browser_receipt_errors as _browser_receipt_errors,
)
from fep_lean.output.release_bundle._browser import (
    _browser_screenshot_paths as _browser_screenshot_paths,
)
from fep_lean.output.release_bundle._browser import (
    _live_browser_identity as _live_browser_identity,
)
from fep_lean.output.release_bundle._browser import (
    _png_dimensions as _png_dimensions,
)
from fep_lean.output.release_bundle._constants import (
    _CANONICAL_LICENSE as _CANONICAL_LICENSE,
)
from fep_lean.output.release_bundle._constants import (
    _CANONICAL_PUBLICATION_DOI as _CANONICAL_PUBLICATION_DOI,
)
from fep_lean.output.release_bundle._constants import (
    _CANONICAL_PUBLICATION_JOURNAL as _CANONICAL_PUBLICATION_JOURNAL,
)
from fep_lean.output.release_bundle._constants import (
    _CANONICAL_RELEASE_DATE as _CANONICAL_RELEASE_DATE,
)
from fep_lean.output.release_bundle._constants import (
    _CANONICAL_RELEASE_VERSION as _CANONICAL_RELEASE_VERSION,
)
from fep_lean.output.release_bundle._constants import (
    _CANONICAL_REPOSITORY_URL as _CANONICAL_REPOSITORY_URL,
)
from fep_lean.output.release_bundle._constants import (
    _CHECKSUM_LINE_RE as _CHECKSUM_LINE_RE,
)
from fep_lean.output.release_bundle._constants import (
    _GIT_SHA_RE as _GIT_SHA_RE,
)
from fep_lean.output.release_bundle._constants import (
    _MANUSCRIPT_FIGURE_REFERENCES as _MANUSCRIPT_FIGURE_REFERENCES,
)
from fep_lean.output.release_bundle._constants import (
    _MARKDOWN_IMAGE_RE as _MARKDOWN_IMAGE_RE,
)
from fep_lean.output.release_bundle._constants import (
    _MAX_ARCHIVE_BYTES as _MAX_ARCHIVE_BYTES,
)
from fep_lean.output.release_bundle._constants import (
    _MAX_ARCHIVE_MEMBERS as _MAX_ARCHIVE_MEMBERS,
)
from fep_lean.output.release_bundle._constants import (
    _MAX_MEMBER_BYTES as _MAX_MEMBER_BYTES,
)
from fep_lean.output.release_bundle._constants import (
    _MAX_TOTAL_MEMBER_BYTES as _MAX_TOTAL_MEMBER_BYTES,
)
from fep_lean.output.release_bundle._constants import (
    _MINIMUM_SPDX_SETUPTOOLS_REQUIREMENT as _MINIMUM_SPDX_SETUPTOOLS_REQUIREMENT,
)
from fep_lean.output.release_bundle._constants import (
    _PANDOC_TIMEOUT_SECONDS as _PANDOC_TIMEOUT_SECONDS,
)
from fep_lean.output.release_bundle._constants import (
    _PDF_ID_RE as _PDF_ID_RE,
)
from fep_lean.output.release_bundle._constants import (
    _PDF_TIMEOUT_SECONDS as _PDF_TIMEOUT_SECONDS,
)
from fep_lean.output.release_bundle._constants import (
    _PROVIDER_MEMBER_PREFIXES as _PROVIDER_MEMBER_PREFIXES,
)
from fep_lean.output.release_bundle._constants import (
    _PYTHON_ACCEPTANCE_ARGUMENTS as _PYTHON_ACCEPTANCE_ARGUMENTS,
)
from fep_lean.output.release_bundle._constants import (
    _PYTHON_ACCEPTANCE_DISTRIBUTIONS as _PYTHON_ACCEPTANCE_DISTRIBUTIONS,
)
from fep_lean.output.release_bundle._constants import (
    _PYTHON_ACCEPTANCE_EXPLICIT_PLUGINS as _PYTHON_ACCEPTANCE_EXPLICIT_PLUGINS,
)
from fep_lean.output.release_bundle._constants import (
    _PYTHON_ACCEPTANCE_EXTERNAL_TOOLS as _PYTHON_ACCEPTANCE_EXTERNAL_TOOLS,
)
from fep_lean.output.release_bundle._constants import (
    _PYTHON_ACCEPTANCE_TIMEOUT_SECONDS as _PYTHON_ACCEPTANCE_TIMEOUT_SECONDS,
)
from fep_lean.output.release_bundle._constants import (
    _PYTHON_ACCEPTANCE_USER_FONT_DIRECTORIES as _PYTHON_ACCEPTANCE_USER_FONT_DIRECTORIES,
)
from fep_lean.output.release_bundle._constants import (
    _REQUIRED_STATIC_MEMBERS as _REQUIRED_STATIC_MEMBERS,
)
from fep_lean.output.release_bundle._constants import (
    _RESOURCE_MARKUP_RE as _RESOURCE_MARKUP_RE,
)
from fep_lean.output.release_bundle._constants import (
    _SHA256_RE as _SHA256_RE,
)
from fep_lean.output.release_bundle._constants import (
    _STATIC_REQUIRED_BUNDLE_PATHS as _STATIC_REQUIRED_BUNDLE_PATHS,
)
from fep_lean.output.release_bundle._constants import (
    CHECKSUMS_NAME as CHECKSUMS_NAME,
)
from fep_lean.output.release_bundle._constants import (
    MANIFEST_NAME as MANIFEST_NAME,
)
from fep_lean.output.release_bundle._constants import (
    NUMERICAL_RECEIPT as NUMERICAL_RECEIPT,
)
from fep_lean.output.release_bundle._constants import (
    PUBLICATION_HTML as PUBLICATION_HTML,
)
from fep_lean.output.release_bundle._constants import (
    PUBLICATION_PDF as PUBLICATION_PDF,
)
from fep_lean.output.release_bundle._constants import (
    PYTEST_RECEIPT as PYTEST_RECEIPT,
)
from fep_lean.output.release_bundle._constants import (
    PYTHON_ACCEPTANCE_RECEIPT as PYTHON_ACCEPTANCE_RECEIPT,
)
from fep_lean.output.release_bundle._constants import (
    PYTHON_COVERAGE_RECEIPT as PYTHON_COVERAGE_RECEIPT,
)
from fep_lean.output.release_bundle._constants import (
    RELEASE_BUNDLE_SCHEMA_VERSION as RELEASE_BUNDLE_SCHEMA_VERSION,
)
from fep_lean.output.release_bundle._constants import (
    RENDERER_PROVENANCE as RENDERER_PROVENANCE,
)
from fep_lean.output.release_bundle._core import (
    PublicationManuscript as PublicationManuscript,
)
from fep_lean.output.release_bundle._core import (
    ReleaseBundleError as ReleaseBundleError,
)
from fep_lean.output.release_bundle._core import (
    ReleaseBundleValidation as ReleaseBundleValidation,
)
from fep_lean.output.release_bundle._core import (
    _BundleMember as _BundleMember,
)
from fep_lean.output.release_bundle._core import (
    _canonical_json as _canonical_json,
)
from fep_lean.output.release_bundle._core import (
    _digest_named_bytes as _digest_named_bytes,
)
from fep_lean.output.release_bundle._core import (
    _is_provider_member as _is_provider_member,
)
from fep_lean.output.release_bundle._core import (
    _json_object as _json_object,
)
from fep_lean.output.release_bundle._core import (
    _relative_file_bytes as _relative_file_bytes,
)
from fep_lean.output.release_bundle._core import (
    _safe_member_name as _safe_member_name,
)
from fep_lean.output.release_bundle._core import (
    _source_date_epoch as _source_date_epoch,
)
from fep_lean.output.release_bundle._identity import (
    _bounded_manuscript_projection_errors as _bounded_manuscript_projection_errors,
)
from fep_lean.output.release_bundle._identity import (
    _canonical_owner_names as _canonical_owner_names,
)
from fep_lean.output.release_bundle._identity import (
    _expected_evidence_class as _expected_evidence_class,
)
from fep_lean.output.release_bundle._identity import (
    _license_metadata_errors as _license_metadata_errors,
)
from fep_lean.output.release_bundle._identity import (
    _theorem_maturity_projection_errors as _theorem_maturity_projection_errors,
)
from fep_lean.output.release_bundle._manuscript import (
    _canonical_pdf_identifier as _canonical_pdf_identifier,
)
from fep_lean.output.release_bundle._manuscript import (
    _canonical_renderer_input_records as _canonical_renderer_input_records,
)
from fep_lean.output.release_bundle._manuscript import (
    _controlled_renderer_path as _controlled_renderer_path,
)
from fep_lean.output.release_bundle._manuscript import (
    _latex_preamble as _latex_preamble,
)
from fep_lean.output.release_bundle._manuscript import (
    _manuscript_inputs as _manuscript_inputs,
)
from fep_lean.output.release_bundle._manuscript import (
    _manuscript_source_records as _manuscript_source_records,
)
from fep_lean.output.release_bundle._manuscript import (
    _manuscript_variables as _manuscript_variables,
)
from fep_lean.output.release_bundle._manuscript import (
    _normalized_renderer_environment as _normalized_renderer_environment,
)
from fep_lean.output.release_bundle._manuscript import (
    _pandoc_base_command as _pandoc_base_command,
)
from fep_lean.output.release_bundle._manuscript import (
    _publication_resource_records as _publication_resource_records,
)
from fep_lean.output.release_bundle._manuscript import (
    _render_twice as _render_twice,
)
from fep_lean.output.release_bundle._manuscript import (
    _rendered_manuscript_errors as _rendered_manuscript_errors,
)
from fep_lean.output.release_bundle._manuscript import (
    _renderer_environment as _renderer_environment,
)
from fep_lean.output.release_bundle._manuscript import (
    _replace_publication_set as _replace_publication_set,
)
from fep_lean.output.release_bundle._manuscript import (
    _required_graphical_abstract as _required_graphical_abstract,
)
from fep_lean.output.release_bundle._manuscript import (
    _run_renderer as _run_renderer,
)
from fep_lean.output.release_bundle._manuscript import (
    _tool_identity as _tool_identity,
)
from fep_lean.output.release_bundle._manuscript import (
    publication_manuscript_errors as publication_manuscript_errors,
)
from fep_lean.output.release_bundle._manuscript import (
    render_publication_manuscript as render_publication_manuscript,
)
from fep_lean.output.release_bundle._manuscript import (
    write_publication_manuscript as write_publication_manuscript,
)
from fep_lean.output.release_bundle._prerequisites import (
    _base_prerequisite_errors as _base_prerequisite_errors,
)
from fep_lean.output.release_bundle._prerequisites import (
    release_bundle_prerequisite_errors as release_bundle_prerequisite_errors,
)
from fep_lean.output.release_bundle._validate import (
    _parse_checksums as _parse_checksums,
)
from fep_lean.output.release_bundle._validate import (
    _parse_manifest as _parse_manifest,
)
from fep_lean.output.release_bundle._validate import (
    _read_archive as _read_archive,
)
from fep_lean.output.release_bundle._validate import (
    validate_release_bundle as validate_release_bundle,
)
from fep_lean.output.rendering import (
    MANUSCRIPT_ASSETS as MANUSCRIPT_ASSETS,
)
from fep_lean.output.rendering import (
    manuscript_source_files as manuscript_source_files,
)
from fep_lean.output.rendering import (
    render_manuscript as render_manuscript,
)
from fep_lean.verification.formalism_audit import (
    validate_formalism_audit_receipt as validate_formalism_audit_receipt,
)
from fep_lean.verification.numerical_witnesses import (
    NON_PROOF_EVIDENCE as NON_PROOF_EVIDENCE,
)
from fep_lean.verification.numerical_witnesses import (
    evaluate_numerical_witnesses as evaluate_numerical_witnesses,
)

__all__ = [
    "CHECKSUMS_NAME",
    "MANIFEST_NAME",
    "PUBLICATION_HTML",
    "PUBLICATION_PDF",
    "RELEASE_BUNDLE_SCHEMA_VERSION",
    "RENDERER_PROVENANCE",
    "PublicationManuscript",
    "ReleaseBundleError",
    "ReleaseBundleValidation",
    "build_numerical_witness_receipt",
    "build_python_acceptance_receipt",
    "build_release_bundle",
    "publication_manuscript_errors",
    "release_bundle_prerequisite_errors",
    "render_publication_manuscript",
    "run_python_acceptance",
    "validate_release_bundle",
    "write_numerical_witnesses",
    "write_publication_manuscript",
]
