"""Shared release fixtures; assertions remain in owner test modules."""

from __future__ import annotations

import gzip
import hashlib
import io
import json
import shutil
import struct
import sys
import tarfile
import zlib
from pathlib import Path

import pytest

from fep_lean.output import release_bundle as bundle_module

PROJ = Path(__file__).resolve().parents[2]


def _fixture_renderer_tools(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    names: tuple[str, ...] = ("pandoc",),
    *,
    actual_identity: bool = False,
) -> dict[str, Path]:
    """Keep real executable custody separate from mocked render output."""
    tools_root = tmp_path / "renderer-tools"
    tools_root.mkdir()
    tools = {name: tools_root / name for name in names}
    for name, path in tools.items():
        path.write_text(f"#!/bin/sh\nprintf '%s\\n' '{name} fixture'\n")
        path.chmod(0o700)
    monkeypatch.setattr(
        bundle_module.shutil,
        "which",
        lambda name: str(tools[name]) if name in tools else None,
    )
    if not actual_identity:
        monkeypatch.setattr(
            bundle_module,
            "_tool_identity",
            lambda executable: {
                "name": Path(executable).name,
                "version": f"{Path(executable).name} fixture",
                "binary_sha256": hashlib.sha256(
                    Path(executable).read_bytes()
                ).hexdigest(),
            },
        )
    return tools


def _write_raw_entries(
    path: Path, entries: tuple[tuple[tarfile.TarInfo, bytes | None], ...]
) -> None:
    payload = io.BytesIO()
    with tarfile.open(fileobj=payload, mode="w", format=tarfile.USTAR_FORMAT) as tar:
        for info, data in entries:
            info.size = len(data) if data is not None else 0
            tar.addfile(info, io.BytesIO(data) if data is not None else None)
    with (
        path.open("wb") as raw,
        gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0) as zipped,
    ):
        zipped.write(payload.getvalue())


def _write_raw_archive(path: Path, names: tuple[str, ...]) -> None:
    _write_raw_entries(
        path,
        tuple((tarfile.TarInfo(name), b"x") for name in names),
    )


def _png_bytes(width: int, height: int) -> bytes:
    def chunk(kind: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload))
            + kind
            + payload
            + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
        )

    rows = b"".join(b"\0" + b"\x80" * width for _ in range(height))
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(rows, level=9))
        + chunk(b"IEND", b"")
    )


def _valid_contents(payload: dict[str, bytes]) -> dict[str, bytes]:
    complete_payload = {
        path: f"fixture {path}\n".encode()
        for path in bundle_module._STATIC_REQUIRED_BUNDLE_PATHS
    }
    complete_payload["output/manuscript/01_chapter.md"] = b"# Chapter\n"
    complete_payload.update(payload)
    records = [
        {
            "path": name,
            "sha256": hashlib.sha256(data).hexdigest(),
            "size": len(data),
            "evidence_class": (
                bundle_module._expected_evidence_class(name) or "fixture"
            ),
        }
        for name, data in sorted(complete_payload.items())
    ]
    record_by_path = {record["path"]: record for record in records}
    manifest = {
        "schema_version": 1,
        "kind": "fep-lean-evidence-bundle",
        "source_date_epoch": 0,
        "catalogue": {
            "topics": 168,
            "families": 22,
            "areas": 5,
            "first_id": "fep-001",
            "last_id": "fep-168",
        },
        "formalism": {
            "relations": 146,
            "capabilities": 50,
            "formal_modules": 1,
            "numerical_witnesses": 17,
        },
        "toolchain": {
            "lean_toolchain": "leanprover/lean4:v4.33.1",
            "lean_version": "Lean (version 4.33.1, fixture, Release)",
            "mathlib_tag": "v4.33.1",
            "mathlib_revision": "0" * 40,
        },
        "source_sha256": "1" * 64,
        "config_sha256": "2" * 64,
        "manifested_lean_sources": sorted(
            name for name in complete_payload if name.endswith(".lean")
        ),
        "evidence": {
            "native_lean": {
                "current": True,
                "path": "output/native-verification.json",
                "sha256": record_by_path["output/native-verification.json"]["sha256"],
            },
            "declaration_axiom_audit": {
                "current": True,
                "path": "output/formalism-audit.json",
                "sha256": record_by_path["output/formalism-audit.json"]["sha256"],
            },
            "browser_interaction": {
                "current": True,
                "path": bundle_module.BROWSER_RECEIPT.as_posix(),
                "sha256": record_by_path[bundle_module.BROWSER_RECEIPT.as_posix()][
                    "sha256"
                ],
            },
            "numerical_witnesses": {
                "current": True,
                "path": bundle_module.NUMERICAL_RECEIPT.as_posix(),
                "sha256": record_by_path[bundle_module.NUMERICAL_RECEIPT.as_posix()][
                    "sha256"
                ],
                "evidence_kind": ("deterministic_numerical_witness_non_proof_evidence"),
            },
            "python_tests": {
                "current": True,
                "path": bundle_module.PYTEST_RECEIPT.as_posix(),
                "sha256": record_by_path[bundle_module.PYTEST_RECEIPT.as_posix()][
                    "sha256"
                ],
            },
            "python_coverage": {
                "current": True,
                "path": bundle_module.PYTHON_COVERAGE_RECEIPT.as_posix(),
                "sha256": record_by_path[
                    bundle_module.PYTHON_COVERAGE_RECEIPT.as_posix()
                ]["sha256"],
            },
            "python_acceptance": {
                "current": True,
                "path": bundle_module.PYTHON_ACCEPTANCE_RECEIPT.as_posix(),
                "sha256": record_by_path[
                    bundle_module.PYTHON_ACCEPTANCE_RECEIPT.as_posix()
                ]["sha256"],
            },
        },
        "external_full_mode": {
            "current": False,
            "authorized": False,
            "artifacts": [],
        },
        "members": records,
    }
    manifest_bytes = (
        json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode()
    with_manifest = {**complete_payload, "MANIFEST.json": manifest_bytes}
    checksums = "".join(
        f"{hashlib.sha256(with_manifest[name]).hexdigest()}  {name}\n"
        for name in sorted(with_manifest)
    ).encode()
    return {**with_manifest, "SHA256SUMS": checksums}


def _omit_manifested_member(contents: dict[str, bytes], omitted: str) -> None:
    contents.pop(omitted)
    manifest = json.loads(contents["MANIFEST.json"])
    manifest["members"] = [
        record for record in manifest["members"] if record["path"] != omitted
    ]
    manifest["manifested_lean_sources"] = [
        path for path in manifest["manifested_lean_sources"] if path != omitted
    ]
    contents["MANIFEST.json"] = (
        json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode()
    contents["SHA256SUMS"] = "".join(
        f"{hashlib.sha256(contents[name]).hexdigest()}  {name}\n"
        for name in sorted(contents)
        if name != "SHA256SUMS"
    ).encode()


def _minimal_manuscript(project_root: Path) -> None:
    manuscript = project_root / "manuscript"
    rendered = project_root / "output" / "manuscript"
    manuscript.mkdir(parents=True)
    rendered.mkdir(parents=True)
    shutil.copy2(PROJ / "manuscript/config.yaml", manuscript / "config.yaml")
    asset = (PROJ / "manuscript/assets/graphical-abstract.png").read_bytes()
    (manuscript / "assets").mkdir()
    (manuscript / "assets/graphical-abstract.png").write_bytes(asset)
    (rendered / "assets").mkdir()
    (rendered / "assets/graphical-abstract.png").write_bytes(asset)
    front_matter = (
        "---\n"
        "author:\n"
        "  - |\n"
        "    **Author information**  \n"
        "    Daniel Ari Friedman  \n"
        "    Active Inference Institute  \n"
        "    daniel@activeinference.institute · "
        "https://orcid.org/0000-0001-6232-9096\n"
        'abstract-title: "Graphical abstract"\n'
        "abstract: |\n"
        "  ![Graphical abstract fixture](assets/graphical-abstract.png){width=90%}\n"
        "---\n"
    )
    (manuscript / "00_front_matter.md").write_text(
        front_matter.replace(
            "assets/graphical-abstract.png",
            "{{publication.graphical_abstract.render_path}}",
        ),
        encoding="utf-8",
    )
    (rendered / "00_front_matter.md").write_text(front_matter, encoding="utf-8")
    (manuscript / "references.bib").write_text("", encoding="utf-8")
    (manuscript / "preamble.md").write_text(
        "```latex\n% deterministic fixture\n```\n", encoding="utf-8"
    )
    (manuscript / "01_chapter.md").write_text(
        "# Reproducible chapter\n\nThe finite result is checked.\n",
        encoding="utf-8",
    )
    (rendered / "01_chapter.md").write_text(
        "# Reproducible chapter\n\nThe finite result is checked.\n",
        encoding="utf-8",
    )
    (manuscript / "09z_unified_formalism_catalogue.md").write_text(
        "# Appendix\n\nA source-bound appendix.\n",
        encoding="utf-8",
    )


def _write_release_metadata_fixture(project_root: Path) -> None:
    (project_root / ".aii").mkdir(parents=True, exist_ok=True)
    (project_root / "manuscript").mkdir(parents=True, exist_ok=True)
    (project_root / "src/fep_lean").mkdir(parents=True, exist_ok=True)
    (project_root / "config").mkdir(parents=True, exist_ok=True)
    (project_root / "LICENSE").write_text(
        "Creative Commons Attribution 4.0 International (CC BY 4.0)\n"
        "Work-level concept DOI: https://doi.org/10.5281/zenodo.19699233\n",
        encoding="utf-8",
    )
    (project_root / "CITATION.cff").write_text(
        "cff-version: 1.2.0\n"
        "doi: 10.5281/zenodo.23196891\n"
        'version: "1.6.0"\n'
        'date-released: "2026-10-07"\n'
        "repository-code: https://github.com/ActiveInferenceInstitute/fep_formal\n"
        "url: https://github.com/ActiveInferenceInstitute/fep_formal\n"
        "license: CC-BY-4.0\n"
        "authors:\n"
        "  - &canonical-author\n"
        "    given-names: Daniel Ari\n"
        "    family-names: Friedman\n"
        "    email: daniel@activeinference.institute\n"
        "    orcid: https://orcid.org/0000-0001-6232-9096\n"
        "    affiliation: Active Inference Institute\n"
        "preferred-citation:\n"
        "  type: article\n"
        "  authors:\n"
        "    - *canonical-author\n"
        "  journal: Active Inference Journal\n"
        "  doi: 10.5281/zenodo.23220027\n"
        "  url: https://doi.org/10.5281/zenodo.23220027\n",
        encoding="utf-8",
    )
    (project_root / "manuscript/config.yaml").write_text(
        "paper:\n"
        '  version: "1.6.0"\n'
        '  date: "2026-10-07"\n'
        "publication:\n"
        "  doi: 10.5281/zenodo.23220027\n"
        "  journal: Active Inference Journal\n"
        "metadata:\n"
        "  license: CC-BY-4.0\n",
        encoding="utf-8",
    )
    (project_root / "pyproject.toml").write_text(
        '[build-system]\nrequires = ["setuptools>=77.0.3"]\n'
        'build-backend = "setuptools.build_meta"\n\n'
        '[project]\nname = "fixture"\nversion = "1.6.0"\n'
        'readme = "README.md"\n'
        'authors = [{ name = "Daniel Ari Friedman", email = "daniel@activeinference.institute" }]\n'
        'license = "CC-BY-4.0"\n',
        encoding="utf-8",
    )
    with (project_root / "pyproject.toml").open("a", encoding="utf-8") as handle:
        handle.write(
            "\n[project.urls]\n"
            'Repository = "https://github.com/ActiveInferenceInstitute/fep_formal"\n'
            'Changelog = "https://github.com/ActiveInferenceInstitute/fep_formal/blob/main/CHANGELOG.md"\n'
            '"Concept DOI" = "https://doi.org/10.5281/zenodo.19699233"\n'
        )
    (project_root / "src/fep_lean/__init__.py").write_text(
        '__version__ = "1.6.0"\n', encoding="utf-8"
    )
    (project_root / "config/settings.yaml").write_text(
        'project:\n  version: "1.6.0"\n', encoding="utf-8"
    )
    (project_root / ".aii/config.yaml").write_text(
        "meta:\n"
        "  updated: '2026-10-07'\n"
        "repo:\n"
        "  full_name: ActiveInferenceInstitute/fep_formal\n"
        "  description: 'Release v1.6.0 (2026-10-07); concept DOI 10.5281/zenodo.19699233'\n"
        "ecosystem:\n"
        "  links:\n"
        "    github: https://github.com/ActiveInferenceInstitute/fep_formal\n"
        "provenance:\n"
        "  license: CC-BY-4.0\n"
        "  citation:\n"
        "    doi: 10.5281/zenodo.19699233\n",
        encoding="utf-8",
    )


def _capture_stage(root: Path, name: str, dependencies: tuple[str, ...] = ()):
    from fep_lean.output.release_bundle._core import PublicationCaptureStage

    source, output = root / f"{name}.input", root / f"{name}.output"
    source.write_bytes(name.encode())
    producer = (
        "from pathlib import Path;import sys;"
        "data=Path(sys.argv[1]).read_bytes();"
        "Path(sys.argv[2]).write_bytes(data);print('produced');"
        "raise SystemExit(2 if data==b'reject' else 0)"
    )
    validator = (
        "from pathlib import Path;import sys;"
        "assert Path(sys.argv[1]).read_bytes()==Path(sys.argv[2]).read_bytes();"
        "print('checked')"
    )
    args = (str(source), str(output))
    return PublicationCaptureStage(
        name,
        dependencies,
        (str(source),),
        (str(output),),
        (sys.executable, "-c", producer, *args),
        (sys.executable, "-c", validator, *args),
        10,
    )


def _capture_plan(root: Path, stages):
    from fep_lean.output.release_bundle._core import PublicationCapturePlan

    return PublicationCapturePlan(str(root), tuple(stages), 30)


def _linked_capture_stage(tmp_path: Path):
    from dataclasses import replace

    root = tmp_path / "project"
    root.mkdir()
    owner = tmp_path / "resources"
    leaf = owner / "canonical/style.txt"
    leaf.parent.mkdir(parents=True)
    leaf.write_bytes(b"owned style")
    alias = owner / "links/style.txt"
    alias.parent.mkdir()
    alias.symlink_to("../canonical/style.txt")
    files = tuple(sorted((str(leaf), str(alias))))
    stage = _capture_stage(root, "a")
    stage = replace(
        stage,
        inputs=tuple(sorted((*stage.inputs, *files))),
        input_rosters=((str(owner), files),),
        resource_links=((str(alias), "../canonical/style.txt"),),
    )
    return root, owner, leaf, alias, stage
