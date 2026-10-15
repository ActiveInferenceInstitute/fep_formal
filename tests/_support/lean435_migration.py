"""Compare frozen H3 carrier bytes across the enumerated Lean 4.35 migration."""

from __future__ import annotations

import base64
import hashlib
import json
import re
import zlib
from collections.abc import Mapping, Sequence
from pathlib import Path

_CARRIER_IMPORT_ADDITIONS = {
    "src/fep_lean/formal/markov_semigroup.lean": (),
    "src/fep_lean/formal/gaussian_information_geometry.lean": (),
    "src/fep_lean/formal/smooth_information_geometry.lean": (),
    "src/fep_lean/formal/h3_reference_model.lean": (),
    "src/fep_lean/formal/fin4_gaussian_semigroup.lean": (
        "Mathlib.Probability.Distributions.Gaussian.Fernique",
    ),
    "src/fep_lean/formal/gaussian_precision_conditioning.lean": (
        "Mathlib.Probability.Distributions.Gaussian.HasGaussianLaw.Basic",
    ),
    "src/fep_lean/formal/scalar_gaussian_semigroup.lean": (),
    "src/fep_lean/formal/compositions/smooth_reference_kernel.lean": (),
    "src/fep_lean/formal/compositions/gaussian_filter.lean": (
        "Mathlib.Probability.Kernel.Composition.WithDensity",
    ),
    "src/fep_lean/formal/compositions/gaussian_control.lean": (),
}

_CARRIER_EXPORTED_SUPPORT = {
    "src/fep_lean/formal/scalar_gaussian_semigroup.lean": (
        "noncomputable def rateDenominator",
        "theorem stationaryVariance_pos",
    ),
    "src/fep_lean/formal/compositions/gaussian_control.lean": (
        "noncomputable instance actionKernelFamily_isMarkovKernel",
        "noncomputable def boolDynamics",
    ),
}


def historical_carrier_bytes(relative: str, live: bytes) -> bytes:
    """Reverse only known carrier migration edits, never update frozen evidence.

    Callers must compare the returned bytes with the immutable historical
    digest. Any other statement, proof, carrier, or import change survives
    this reversal and therefore invalidates that comparison.
    """
    additions = _CARRIER_IMPORT_ADDITIONS[relative]
    migrated = live.decode("utf-8")
    assert migrated.startswith("module\n"), relative
    assert migrated.count("\n@[expose] public section\n") == 1, relative
    historical = migrated.removeprefix("module\n").replace(
        "\n@[expose] public section\n", "", 1
    )
    for dependency in additions:
        extra_import = f"public import {dependency}\n"
        assert historical.count(extra_import) == 1, relative
        historical = historical.replace(extra_import, "", 1)
    historical = re.sub(r"(?m)^public import ", "import ", historical)
    for support in _CARRIER_EXPORTED_SUPPORT.get(relative, ()):
        # Declarations may continue on the next line; retain that exact suffix.
        pattern = rf"(?m)^{re.escape(support)}(?=\s)"
        assert len(re.findall(pattern, historical)) == 1, relative
        historical = re.sub(pattern, f"private {support}", historical, count=1)
    return historical.encode("utf-8")


def historical_toolchain_files(project_root: Path) -> dict[str, bytes]:
    """Read the existing sealed 4.34.1 inputs without changing any live pin.

    These are historical bytes, not a claim that the installed compiler uses
    them. They cannot make a changed historical test source pass custody.
    """
    resource = project_root / "tests/fixtures/custody_toolchain_4_34_1.json"
    raw = resource.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == (
        "9916471b29cec86a3a77b2983f854207be112b8b87d233c202bfbcd160f4158c"
    )
    fixture = json.loads(raw)
    assert fixture["kind"] == "historical-custody-unit-fixture"
    assert fixture["source_commit"] == "5e1cc9095b5f0590772c739d27558c2c711f9a44"
    assert set(fixture["files"]) == {
        "lean/lean-toolchain",
        "lean/lakefile.lean",
        "lean/lake-manifest.json",
    }
    return {
        relative: text.encode("utf-8") for relative, text in fixture["files"].items()
    }


def assert_historical_repair_bindings(
    project_root: Path,
    repair_path: Path,
    receipt_sha256: str,
    source_paths: Sequence[str],
    *,
    historical_tests: Mapping[str, str],
) -> None:
    """Keep an immutable repair bound to history and reject live substitution.

    Every unchanged resource still binds its exact live bytes. Only enumerated
    Lean migration edits are inverted, and the result must match the immutable
    recorded digest. Historical tests retain their recorded digests in the
    sealed receipt; updated tests are deliberately not execution evidence for
    that old epoch. No receipt or source file is rewritten by this check.
    """
    receipt_bytes = repair_path.read_bytes()
    assert hashlib.sha256(receipt_bytes).hexdigest() == receipt_sha256
    recorded = json.loads(receipt_bytes)["source_sha256"]
    assert set(recorded) == set(source_paths)
    pins = historical_toolchain_files(project_root)
    migrated = set(pins) | set(historical_tests)
    for relative in source_paths:
        live = (project_root / relative).read_bytes()
        if relative in pins:
            historical = pins[relative]
        elif relative in historical_tests:
            assert recorded[relative] == historical_tests[relative]
            assert hashlib.sha256(live).hexdigest() != recorded[relative]
            continue
        elif relative.startswith("src/fep_lean/formal/"):
            historical = historical_carrier_bytes(relative, live)
            migrated.add(relative)
        else:
            historical = live
        assert hashlib.sha256(historical).hexdigest() == recorded[relative], relative
    # An exact mismatch roster prevents unrelated source drift from being
    # excused as a generic migration or promoted to current acceptance.
    assert {
        relative
        for relative in source_paths
        if hashlib.sha256((project_root / relative).read_bytes()).hexdigest()
        != recorded[relative]
    } == migrated


HISTORICAL_CUSTODY_ARCHIVE = "tests/fixtures/historical_h3_custody_sources.json"
HISTORICAL_CUSTODY_ARCHIVE_SHA256 = (
    "2e279ffd13826b1eb2a07a5652d8e07e52ce5e0e3590b041418ab46d8a126eb1"
)
HISTORICAL_MANIFEST_ARCHIVE = "tests/fixtures/historical_h3_custody_manifest.json"
HISTORICAL_MANIFEST_ARCHIVE_SHA256 = (
    "5d44c38f15ae28b3bf7732ebe60edbcf2c6e27050dfb28fd6a466ebcdf890b18"
)
_HISTORICAL_MANIFEST_SHA256 = (
    "c1dff5c5753162d1cf91fb27c5cb08777d385db4c606bd65a136d2c93acf07ce"
)
_CATEGORY_MANIFEST_SHA256 = (
    "e99bc2bb55d88872d04a851430fae6ca9978bc9aea12de493e923c3d8b9f4157"
)
_CATEGORY_OWNER_BLOCK = (
    b"    FormalModule(\n"
    b'        resource="compositions/finite_kernel_category.lean",\n'
    b'        lean_module="FepSketches.compositions.finite_kernel_category",\n'
    b"        role=FormalModuleRole.COMPOSITION,\n"
    b'        declaration_namespace="FEPComposed.FiniteKernelCategory",\n'
    b"    ),\n"
)
_CATEGORY_OWNER_ANCHOR = (
    b"    FormalModule(\n"
    b'        resource="compositions/smooth_reference_kernel.lean",\n'
    b'        lean_module="FepSketches.compositions.smooth_reference_kernel",\n'
    b"        role=FormalModuleRole.COMPOSITION,\n"
    b'        declaration_namespace="FEPComposed.SmoothReferenceKernel",\n'
    b"    ),\n"
)
_HISTORICAL_CUSTODY_ORIGINALS = {
    "src/fep_lean/formal/compositions/h3_case_study.lean": (
        "7a8ba9346dc9ab700ac6276c26421b46c0437eabaab7cd448a2bc05998318849",
        252275,
        60488,
    ),
    "tests/test_horizon2_gaussian_vfe_readiness.py": (
        "b36f3a1b9e80f7e83705178c31d7483b8a334e8c2d905508f39154e13fcb2455",
        34650,
        10244,
    ),
}
_HISTORICAL_CUSTODY_SOURCE_PATHS = frozenset(
    (
        "lean/lake-manifest.json",
        "lean/lakefile.lean",
        "lean/lean-toolchain",
        "pyproject.toml",
        "uv.lock",
        "src/fep_lean/formal/manifest.py",
        "src/fep_lean/formal/gaussian_information_geometry.lean",
        "lean/FepSketches/gaussian_information_geometry.lean",
        "src/fep_lean/formal/smooth_information_geometry.lean",
        "lean/FepSketches/smooth_information_geometry.lean",
        "src/fep_lean/formal/compositions/gaussian_filter.lean",
        "lean/FepSketches/compositions/gaussian_filter.lean",
        "src/fep_lean/formal/h3_reference_model.lean",
        "lean/FepSketches/h3_reference_model.lean",
        "src/fep_lean/formal/compositions/h3_case_study.lean",
        "lean/FepSketches/compositions/h3_case_study.lean",
        "specs/done/horizon-2-smooth-stochastic/readiness/acceptance.json",
        "specs/done/horizon-2-smooth-stochastic/readiness/matrix.yaml",
        "specs/done/horizon-2-smooth-stochastic/slices/07-r0-gaussian-vfe-natural-gradient.md",
        "specs/done/horizon-2-smooth-stochastic/spikes/07_gaussian_vfe_natural_gradient.lean",
        "tests/test_horizon2_gaussian_vfe_readiness.py",
        "tests/_support/h2_r0_custody.py",
    )
)


def historical_manifest_bytes(project_root: Path, live: bytes) -> bytes:
    """Recover authenticated history only from the two exact recognized inputs.

    Recognizing the prospective category manifest is a static input transition,
    not approval of its mathematical API or execution. Unknown live changes
    fail before decoding, and a changed companion fails before decoding too.
    The historical validator and every existing archive remain unchanged.
    """
    live_digest = hashlib.sha256(live).hexdigest()
    assert live_digest in {_HISTORICAL_MANIFEST_SHA256, _CATEGORY_MANIFEST_SHA256}, (
        "unreviewed live custody manifest: src/fep_lean/formal/manifest.py"
    )
    predecessor = live
    if live_digest == _CATEGORY_MANIFEST_SHA256:
        assert live.count(_CATEGORY_OWNER_BLOCK) == 1
        assert live.count(_CATEGORY_OWNER_ANCHOR + _CATEGORY_OWNER_BLOCK) == 1
        predecessor = live.replace(_CATEGORY_OWNER_BLOCK, b"", 1)

    raw = (project_root / HISTORICAL_MANIFEST_ARCHIVE).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == HISTORICAL_MANIFEST_ARCHIVE_SHA256, (
        "historical custody manifest archive identity changed"
    )
    payload = json.loads(raw)
    assert set(payload) == {
        "schema_version",
        "kind",
        "source_commit",
        "encoding",
        "evidence_boundary",
        "files",
    }
    assert type(payload["schema_version"]) is int and payload["schema_version"] == 1
    assert payload["kind"] == "historical-h3-custody-manifest-companion"
    assert payload["source_commit"] == "5e1cc9095b5f0590772c739d27558c2c711f9a44"
    assert payload["encoding"] == "zlib+base64"
    assert payload["evidence_boundary"] == (
        "Original public manifest bytes for offline historical custody unit controls. "
        "No Lean/test execution, current native acceptance, or renewed scientific approval."
    )
    relative = "src/fep_lean/formal/manifest.py"
    assert set(payload["files"]) == {relative}
    entry = payload["files"][relative]
    assert set(entry) == {"sha256", "size", "data"}
    assert entry["sha256"] == _HISTORICAL_MANIFEST_SHA256
    assert type(entry["size"]) is int and entry["size"] == 22567
    assert isinstance(entry["data"], str) and len(entry["data"]) == 4456
    compressed = base64.b64decode(entry["data"], validate=True)
    decoder = zlib.decompressobj()
    data = decoder.decompress(compressed, entry["size"] + 1)
    assert decoder.eof and not decoder.unused_data and not decoder.unconsumed_tail
    assert len(data) == entry["size"]
    assert hashlib.sha256(data).hexdigest() == _HISTORICAL_MANIFEST_SHA256
    assert predecessor == data, "category owner subtraction changed historical bytes"
    return data


def historical_custody_sources(project_root: Path) -> dict[str, bytes]:
    """Decode only the two sealed original resources, never execute either.

    Check the archive identity, metadata, expected sizes and recorded source
    digests before decoding; check each decoded digest again before returning
    any bytes. Normal CI does not need old Git objects or network access.
    """
    raw = (project_root / HISTORICAL_CUSTODY_ARCHIVE).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == HISTORICAL_CUSTODY_ARCHIVE_SHA256, (
        "historical custody archive identity changed"
    )
    payload = json.loads(raw)
    assert set(payload) == {
        "schema_version",
        "kind",
        "source_commit",
        "encoding",
        "evidence_boundary",
        "files",
    }
    assert type(payload["schema_version"]) is int and payload["schema_version"] == 1
    assert payload["kind"] == "historical-h3-custody-unit-sources"
    assert payload["source_commit"] == "5e1cc9095b5f0590772c739d27558c2c711f9a44"
    assert payload["encoding"] == "zlib+base64"
    assert payload["evidence_boundary"] == (
        "Original public source bytes for offline historical custody unit controls. "
        "No Lean/test execution, current native acceptance, or renewed scientific approval."
    )
    assert set(payload["files"]) == set(_HISTORICAL_CUSTODY_ORIGINALS)
    sources = {}
    for relative, (digest, size, encoded_size) in _HISTORICAL_CUSTODY_ORIGINALS.items():
        entry = payload["files"][relative]
        assert set(entry) == {"sha256", "size", "data"}
        assert entry["sha256"] == digest, relative
        assert type(entry["size"]) is int and entry["size"] == size, relative
        assert isinstance(entry["data"], str) and len(entry["data"]) == encoded_size
        compressed = base64.b64decode(entry["data"], validate=True)
        decoder = zlib.decompressobj()
        data = decoder.decompress(compressed, size + 1)
        assert decoder.eof and not decoder.unused_data and not decoder.unconsumed_tail
        assert len(data) == size, relative
        assert hashlib.sha256(data).hexdigest() == digest, relative
        sources[relative] = data
    return sources


def historical_custody_root(project_root: Path, destination: Path) -> Path:
    """Restore an authentic historical custody control into an empty temp root.

    The unchanged validator must accept all 22 original bound inputs before a
    negative control mutates them. This is historical replay of static custody
    only: archived Lean/test sources are never executed and no native/scientific
    evidence is renewed. Every production file remains read-only.
    """
    from tests._support.h2_r0_custody import (
        H3_ADDENDUM_PATH,
        MANIFEST_PATH,
        PRIOR_PATH,
        SUCCESSOR_PATH,
        VALIDATOR_PATH,
        validate_h2_r0_custody,
    )

    assert destination.is_dir() and not destination.is_symlink()
    assert not any(destination.iterdir()), "historical custody root must be empty"
    assert destination.resolve() != project_root.resolve()
    records = {
        PRIOR_PATH: "06fa2f40cec8cc0174eb4583e1e86436ba6bb081db494ff1e2b5086e196d289a",
        SUCCESSOR_PATH: "6311a998b1a66bb31949e194eb9e36a2e361dfbfb0f0e7d715b3a17e3e396bae",
        H3_ADDENDUM_PATH: "69279a2c2641a81799c272dca277d4c255a46eaa48c94cb86c1072aa0fa936c6",
    }
    prepared = {}
    for relative, digest in records.items():
        data = (project_root / relative).read_bytes()
        assert hashlib.sha256(data).hexdigest() == digest, relative
        prepared[relative] = data
    recorded_sources = json.loads(prepared[H3_ADDENDUM_PATH])["source_sha256"]
    assert set(recorded_sources) == _HISTORICAL_CUSTODY_SOURCE_PATHS
    assert recorded_sources[VALIDATOR_PATH] == (
        "46c45d3eb5a19c8a6c9814d660ff9e6f8f0ddaeff6b4cd17ff14520fded27b53"
    )
    live_manifest = (project_root / MANIFEST_PATH).read_bytes()
    historical_manifest = historical_manifest_bytes(project_root, live_manifest)
    archived = historical_custody_sources(project_root)
    pins = historical_toolchain_files(project_root)
    for relative, digest in recorded_sources.items():
        canonical = relative.replace("lean/FepSketches/", "src/fep_lean/formal/", 1)
        if relative == MANIFEST_PATH:
            data = historical_manifest
        elif canonical in archived:
            data = archived[canonical]
        elif relative in pins:
            data = pins[relative]
        else:
            data = (project_root / relative).read_bytes()
            if relative == "pyproject.toml":
                uv_pin = b'\n[tool.uv]\nrequired-version = "==0.13.0"\n'
                assert data.count(uv_pin) == 1
                data = data.replace(uv_pin, b"", 1)
                current = b'[project]\nname = "fep_lean"\nversion = "1.6.0"\n'
                historical = current.replace(b'"1.6.0"', b'"1.4.0"')
                assert data.count(current) == 1
                data = data.replace(current, historical, 1)
            elif relative == "uv.lock":
                current = b'[[package]]\nname = "fep-lean"\nversion = "1.6.0"\n'
                historical = current.replace(b'"1.6.0"', b'"1.4.0"')
                assert data.count(current) == 1
                data = data.replace(current, historical, 1)
            elif canonical in _CARRIER_IMPORT_ADDITIONS:
                data = historical_carrier_bytes(canonical, data)
        assert hashlib.sha256(data).hexdigest() == digest, relative
        prepared[relative] = data
    # Nothing is written until every exact original source and record checks.
    for relative, data in prepared.items():
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    provenance = {
        "kind": "historical-static-custody-unit-control",
        "source_commit": "5e1cc9095b5f0590772c739d27558c2c711f9a44",
        "archive_sha256": HISTORICAL_CUSTODY_ARCHIVE_SHA256,
        "manifest_archive_sha256": HISTORICAL_MANIFEST_ARCHIVE_SHA256,
        "observed_manifest_sha256": hashlib.sha256(live_manifest).hexdigest(),
        "restored_manifest_sha256": _HISTORICAL_MANIFEST_SHA256,
        "restored_source_paths": sorted(recorded_sources),
        "current_native_or_scientific_acceptance": False,
        "archived_source_execution": False,
    }
    marker = destination / "output/historical-custody-unit-control.json"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(json.dumps(provenance, sort_keys=True) + "\n", encoding="utf-8")
    accepted = validate_h2_r0_custody(destination)
    assert accepted["decision"] == "preserve_accepted_R0"
    assert accepted["native_evidence"] == {
        "status": "not_executed",
        "historical_evidence_reused": False,
        "probes": [],
    }
    return destination
