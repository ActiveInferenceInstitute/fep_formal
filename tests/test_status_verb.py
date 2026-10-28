"""The status verb composes existing checks and states its boundaries."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from fep_formal import cli
from fep_formal.catalogue import generation as catalogue_generation
from fep_formal.catalogue.generation import render_topics_yaml
from fep_formal.cli import (
    RENDER_RECEIPT,
    SOURCE_PIN,
    bridge_pin_section,
    build_status_report,
    catalogue_products_section,
    render_receipt_section,
)
from fep_formal.output import evidence, render_log
from fep_formal.output import manuscript as manuscript_module
from fep_formal.output.browser_capture import CANONICAL_BROWSER_SCREENSHOTS
from fep_formal.output.render_log import RECEIPT_VERSION, manuscript_source_digest


def _projection_owner(name: str):
    return {
        "catalogue_projection_drift": catalogue_generation,
        "fep_all_projection_drift": catalogue_generation,
        "build_manuscript_vars": manuscript_module,
        "manuscript_projection_drift": manuscript_module,
    }[name]


SECTION_NAMES = (
    "catalogue_build_products",
    "render_receipt_freshness",
    "bridge_source_pin",
    "native_verification_receipt",
)


def accepted_receipt_payload(manuscript_dir: Path) -> dict[str, object]:
    """Build the smallest render-acceptance receipt covering *manuscript_dir*."""
    return {
        "receipt_version": RECEIPT_VERSION,
        "accepted": True,
        "pages": 1,
        "checks": {
            "tex_errors": [],
            "missing_characters": [],
            "mermaid_fallbacks": [],
            "stale_sources": [],
            "uncaptioned_tables": [],
            "contents_number_overflows": [],
            "unresolved_references": [],
            "publication_cover": [],
            "unnumbered_equations": [],
        },
        "manuscript_source_digest": manuscript_source_digest(manuscript_dir),
        "source_digests": {},
    }


def manuscript_tree(root: Path) -> Path:
    """Stage a minimal typeset manuscript, including the generated appendix
    the render receipt covers and fails closed without, under *root*."""
    manuscript = root / "manuscript"
    manuscript.mkdir()
    (manuscript / "01_chapter.md").write_text("# Chapter\n\nText.\n")
    (manuscript / "preamble.md").write_text("\\usepackage{fontspec}\n")
    (manuscript / "09z_unified_formalism_catalogue.md").write_text(
        "Generated appendix.\n"
    )
    return manuscript


def test_report_has_all_sections_and_boundaries(tmp_path: Path) -> None:
    report = build_status_report(tmp_path)
    payload = report.as_dict()
    assert [section["name"] for section in payload["sections"]] == list(SECTION_NAMES)
    assert payload["status"] == "ok"
    assert payload["native_claim_ready"] is False
    for section in payload["sections"]:
        assert section["boundary"].strip()
        assert section["composes"], section["name"]


def test_top_level_native_claim_ready_tracks_section_state(tmp_path: Path) -> None:
    """The top-level flag must agree with the native section's state.

    VI-7: ``as_dict`` hardcoded ``native_claim_ready: False``, so a
    claim_ready section (fresh 155/155 receipt) surfaced as False at the
    top level with an empty errors list -- a silent contradiction of the
    section authority.
    """
    from fep_formal.cli import SectionReport, StatusReport

    composes = ("fep_formal.output.evidence.validate_native_lean_receipt",)
    claim_ready = SectionReport(
        name="native_verification_receipt",
        state="claim_ready",
        findings=("native_claim_ready: True",),
        composes=composes,
        boundary="probe",
    )
    not_ready = SectionReport(
        name="native_verification_receipt",
        state="not_claim_ready",
        findings=("native_claim_ready: False",),
        composes=composes,
        boundary="probe",
    )
    filler = SectionReport(
        name="catalogue_build_products",
        state="current",
        findings=(),
        composes=composes,
        boundary="probe",
    )
    assert StatusReport((filler, claim_ready)).as_dict()["native_claim_ready"] is True
    assert StatusReport((filler, not_ready)).as_dict()["native_claim_ready"] is False


def test_report_json_round_trips(tmp_path: Path) -> None:
    payload = json.loads(json.dumps(build_status_report(tmp_path).as_dict()))
    assert payload["schema_version"] == 1
    assert payload["status"] == "ok"
    assert [section["name"] for section in payload["sections"]] == list(SECTION_NAMES)
    for section in payload["sections"]:
        assert isinstance(section["findings"], list)
        assert isinstance(section["composes"], list)


def test_missing_build_product_is_reported_stale(tmp_path: Path) -> None:
    # The tracked aggregate Lean projection is absent from this checkout.
    expected_dir = tmp_path / "lean" / "FepSketches"
    expected_dir.mkdir(parents=True)
    (expected_dir / "fep_all.lean").write_text("# stale content\n")
    section = catalogue_products_section(tmp_path)
    assert section.state == "stale"
    assert any(
        finding.startswith("stale or missing: lean/FepSketches/fep_all.lean")
        for finding in section.findings
    )


def test_render_receipt_missing_then_current_then_stale(tmp_path: Path) -> None:
    manuscript = manuscript_tree(tmp_path)
    receipt = tmp_path / RENDER_RECEIPT

    missing = render_receipt_section(tmp_path)
    assert missing.state == "missing"
    assert any("no acceptance receipt" in finding for finding in missing.findings)

    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps(accepted_receipt_payload(manuscript)))
    current = render_receipt_section(tmp_path)
    assert current.state == "current"
    assert current.findings == ()

    (manuscript / "01_chapter.md").write_text("# Chapter\n\nEdited.\n")
    stale = render_receipt_section(tmp_path)
    assert stale.state == "stale"
    assert any("covers manuscript sources" in finding for finding in stale.findings)


def test_bridge_pin_absent_reports_not_pinned(tmp_path: Path) -> None:
    section = bridge_pin_section(tmp_path)
    assert section.state == "not_pinned"
    assert any("not pinned" in finding for finding in section.findings)
    assert "explicitly named GNN checkout" in section.boundary


def test_bridge_pin_detects_fep_lean_owner_drift(tmp_path: Path) -> None:
    pin_path = tmp_path / SOURCE_PIN
    pin_path.parent.mkdir(parents=True)
    pin_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "fep_lean": {"commit": "0" * 40, "owners": {}},
                "gnn": {"commit": "0" * 40, "owners": {}},
            }
        )
    )
    section = bridge_pin_section(tmp_path)
    assert section.state == "stale"
    assert any("owner roster mismatch" in finding for finding in section.findings)


@pytest.mark.parametrize("named_gnn", [False, True])
@pytest.mark.parametrize("owner_drift", [False, True])
def test_bridge_currency_agrees_on_both_status_surfaces(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    named_gnn: bool,
    owner_drift: bool,
) -> None:
    root, gnn = tmp_path / "fep", tmp_path / "gnn"
    root.mkdir()
    gnn.mkdir()
    for checkout in (root, gnn):
        (checkout / "owner.txt").write_bytes(b"pinned owner\n")
    owners = {"owner.txt": hashlib.sha256(b"pinned owner\n").hexdigest()}
    pin = root / SOURCE_PIN
    pin.parent.mkdir(parents=True)
    pin.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "fep_lean": {"commit": "0" * 40, "owners": owners},
                "gnn": {"commit": "1" * 40, "owners": owners},
            }
        )
    )
    monkeypatch.setattr(cli.operations, "owner_roster", lambda *_args: ("owner.txt",))
    if owner_drift:
        ((gnn if named_gnn else root) / "owner.txt").write_bytes(b"changed owner\n")

    def forbid_process(*_args: object, **_kwargs: object) -> None:
        pytest.fail("bridge currency check started a process")

    monkeypatch.setattr(subprocess, "run", forbid_process)
    monkeypatch.setattr(subprocess, "Popen", forbid_process)
    before = {
        path.relative_to(tmp_path): (path.read_bytes(), path.stat().st_mtime_ns)
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    payload = build_status_report(root, gnn if named_gnn else None).as_dict()
    expected = "stale" if owner_drift else "current" if named_gnn else "unverified"
    for sections in (
        payload["sections"],
        payload["publication_readiness"]["sections"],
    ):
        bridge = next(row for row in sections if row["name"] == "bridge_source_pin")
        assert bridge["state"] == expected
        if not named_gnn:
            assert any("not compared" in item for item in bridge["findings"])
    after = {
        path.relative_to(tmp_path): (path.read_bytes(), path.stat().st_mtime_ns)
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    assert before == after


def test_malformed_receipts_fail_closed_without_exceptions(tmp_path: Path) -> None:
    receipt = tmp_path / RENDER_RECEIPT
    receipt.parent.mkdir(parents=True)
    receipt.write_text("{not json")
    section = render_receipt_section(tmp_path)
    assert section.state == "stale"
    assert any(
        "unreadable acceptance receipt" in finding for finding in section.findings
    )


@pytest.fixture
def matching_projection_checks(monkeypatch: pytest.MonkeyPatch) -> None:
    """Start with successful checks, then fail one actual comparison boundary."""
    catalogue = object()  # Passed through to mocked generators; never inspected.
    for name in (
        "catalogue_projection_drift",
        "fep_all_projection_drift",
        "manuscript_projection_drift",
    ):
        monkeypatch.setattr(_projection_owner(name), name, lambda *_args, **_kwargs: ())
    monkeypatch.setattr(
        manuscript_module, "build_manuscript_vars", lambda *_args, **_kwargs: {}
    )
    monkeypatch.setattr(cli.FEPTopicCatalogue, "from_yaml", lambda _path: catalogue)


@pytest.mark.parametrize(
    "failed_check,error",
    [
        ("catalogue_projection_drift", OSError("catalogue unreadable")),
        ("fep_all_projection_drift", ValueError("invalid aggregate owner")),
        ("build_manuscript_vars", ValueError("test collection cache is missing")),
        ("build_manuscript_vars", ValueError("test collection cache is stale")),
        ("manuscript_projection_drift", TypeError("malformed manuscript variables")),
    ],
)
def test_unavailable_comparison_never_reports_current(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    matching_projection_checks: None,
    failed_check: str,
    error: Exception,
) -> None:
    def unavailable(*_args: object, **_kwargs: object) -> tuple[Path, ...]:
        raise error

    monkeypatch.setattr(_projection_owner(failed_check), failed_check, unavailable)
    section = catalogue_products_section(tmp_path)
    assert section.state == "unverified"
    assert any(str(error) in finding for finding in section.findings)


def test_actual_drift_remains_stale_with_an_unavailable_comparison(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    matching_projection_checks: None,
) -> None:
    monkeypatch.setattr(
        catalogue_generation,
        "fep_all_projection_drift",
        lambda _root: (tmp_path / "aggregate.lean",),
    )

    def missing_census(*_args: object, **_kwargs: object) -> dict[str, object]:
        raise ValueError("test collection cache is missing")

    monkeypatch.setattr(manuscript_module, "build_manuscript_vars", missing_census)
    section = catalogue_products_section(tmp_path)
    assert section.state == "stale"
    assert any("aggregate.lean" in finding for finding in section.findings)
    assert any("not compared" in finding for finding in section.findings)


def test_completed_matching_comparisons_report_current(
    tmp_path: Path, matching_projection_checks: None
) -> None:
    section = catalogue_products_section(tmp_path)
    assert section.state == "current"
    assert not section.findings


def test_status_is_process_free_and_preserves_file_bytes_and_mtimes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manuscript_tree(tmp_path)
    output = tmp_path / "output"
    output.mkdir()
    for relative in (
        cli.NATIVE_RECEIPT,
        Path("output/formalism-audit.json"),
        cli.release_bundle.PYTHON_ACCEPTANCE_RECEIPT,
        cli.release_bundle.BROWSER_RECEIPT,
    ):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('{"malformed": true}\n')
    (output / "pytest.xml").write_text("malformed JUnit")
    (output / "coverage.xml").write_text("malformed coverage")
    (tmp_path / "manuscript/manuscript_vars.yaml").write_text("malformed: true\n")

    def forbid_execution(*_args: object, **_kwargs: object) -> None:
        pytest.fail("status attempted process execution or test collection")

    monkeypatch.setattr(subprocess, "run", forbid_execution)
    monkeypatch.setattr(subprocess, "Popen", forbid_execution)
    monkeypatch.setattr(
        cli.release_bundle, "_collect_python_node_ids", forbid_execution
    )
    monkeypatch.setattr(
        cli.release_bundle, "replay_browser_acceptance", forbid_execution
    )
    monkeypatch.setattr(
        cli.release_bundle, "render_publication_manuscript", forbid_execution
    )
    before = {
        path.relative_to(tmp_path): (path.read_bytes(), path.stat().st_mtime_ns)
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    payload = build_status_report(tmp_path).as_dict()
    after = {
        path.relative_to(tmp_path): (path.read_bytes(), path.stat().st_mtime_ns)
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    assert before == after
    assert payload["status"] == "ok"
    readiness = payload["publication_readiness"]
    assert readiness["state"] == "blocked"
    assert readiness["claim_ready"] is False
    assert readiness["runtime_checks_performed"] is False
    assert readiness["bundle_parity_verified"] is False
    assert readiness["deferred_checks"]
    states = {section["name"]: section["state"] for section in readiness["sections"]}
    assert states["formalism_audit_receipt"] == "stale"
    assert states["python_acceptance_receipt"] == "stale"
    assert states["browser_acceptance_receipt"] == "stale"


def test_valid_census_reaches_real_manuscript_builder_without_processes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A valid cache must not expose the live Git stamping branch in status."""
    project = Path(__file__).resolve().parent.parent
    for relative in ("config", "src/fep_formal/formal", "manuscript/assets"):
        shutil.copytree(project / relative, tmp_path / relative)
    (tmp_path / "config/topics.yaml").write_text(render_topics_yaml(tmp_path))
    for relative in (
        "CITATION.cff",
        "manuscript/config.yaml",
        "lean/lean-toolchain",
        "lean/lakefile.lean",
    ):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(project / relative, path)
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_sample.py").write_text("def test_sample(): pass\n")
    identity = manuscript_module.collection_runtime_identity()
    cache = tmp_path / "output/.cache/tests_collected.json"
    cache.parent.mkdir(parents=True)
    cache.write_text(
        json.dumps(
            {
                "schema_version": manuscript_module._TEST_COLLECTION_CACHE_SCHEMA_VERSION,
                "input_sha256": manuscript_module._test_collection_fingerprint(
                    tmp_path, identity=identity
                ),
                "collection_identity": identity,
                "test_files": 1,
                "collected": 1,
                "node_ids": ["tests/test_sample.py::test_sample"],
            }
        )
    )
    assert manuscript_module._count_test_cases(tmp_path, write_cache=False) == 1
    captured: list[dict[str, object]] = []
    actual_builder = manuscript_module.build_manuscript_vars

    def capture_builder(*args: object, **kwargs: object) -> dict[str, object]:
        values = actual_builder(*args, **kwargs)
        captured.append(values)
        return values

    def forbid_process(*_args: object, **_kwargs: object) -> None:
        pytest.fail("valid-census status started a subprocess")

    monkeypatch.setattr(manuscript_module, "build_manuscript_vars", capture_builder)
    monkeypatch.setattr(subprocess, "run", forbid_process)
    monkeypatch.setattr(subprocess, "Popen", forbid_process)
    before = {
        path.relative_to(tmp_path): (path.read_bytes(), path.stat().st_mtime_ns)
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    payload = build_status_report(tmp_path).as_dict()
    after = {
        path.relative_to(tmp_path): (path.read_bytes(), path.stat().st_mtime_ns)
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    assert before == after
    assert len(captured) == 1
    assert captured[0]["tests"] == {"collected": 1}
    source = captured[0]["source"]
    assert isinstance(source, dict)
    assert set(source.values()) == {"unverified"}
    assert "No checkout stamp is captured" in payload["sections"][0]["boundary"]


def test_manuscript_builder_keeps_live_stamping_as_its_default(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = Path(__file__).resolve().parent.parent
    stamps: list[Path] = []
    actual_stamp = manuscript_module._source_stamp_vars(project)

    def capture_stamp(root: Path) -> dict[str, str]:
        stamps.append(root)
        return actual_stamp

    monkeypatch.setattr(manuscript_module, "_source_stamp_vars", capture_stamp)
    monkeypatch.setattr(
        manuscript_module, "_count_test_cases", lambda *_args, **_kwargs: 1
    )
    topics = tmp_path / "topics.yaml"
    topics.write_text(render_topics_yaml(project))
    catalogue = cli.FEPTopicCatalogue.from_yaml(topics)
    strict = manuscript_module.build_manuscript_vars(catalogue, project)
    static = manuscript_module.build_manuscript_vars(
        catalogue, project, capture_source_stamp=False
    )
    assert stamps == [project]
    assert strict["source"] == actual_stamp
    assert set(static["source"]) == set(actual_stamp)
    assert manuscript_module._mapping_shape(static["source"]) == (
        manuscript_module._mapping_shape(strict["source"])
    )


def test_source_changes_during_status_block_readiness(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    snapshot_calls = 0

    def changed_source(
        _root: Path, _gnn: Path | None
    ) -> tuple[dict[str, str], tuple[str, ...]]:
        nonlocal snapshot_calls
        snapshot_calls += 1
        return {"source": "before" if snapshot_calls == 1 else "after"}, ()

    monkeypatch.setattr(evidence, "_readiness_input_snapshot", changed_source)
    readiness = build_status_report(tmp_path).as_dict()["publication_readiness"]
    stability = readiness["sections"][-1]
    assert stability["name"] == "input_stability"
    assert stability["state"] == "error"
    assert "changed during status" in stability["findings"][0]
    assert readiness["claim_ready"] is False


@pytest.mark.parametrize(
    "relative",
    [
        next(iter(CANONICAL_BROWSER_SCREENSHOTS.values())),
        "output/.cache/tests_collected.json",
        "output/manuscript/01_chapter.md",
        next(iter(cli.release_bundle._MANUSCRIPT_FIGURE_REFERENCES.values())),
    ],
)
def test_consumed_screenshot_and_census_mutations_block_input_stability(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, relative: str
) -> None:
    receipt = tmp_path / cli.release_bundle.BROWSER_RECEIPT
    receipt.parent.mkdir(parents=True)
    receipt.write_text("{}\n")
    if relative == "output/manuscript/01_chapter.md":
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "01_chapter.md").write_text("A consumed chapter.\n")
    observed = tmp_path / relative
    observed.parent.mkdir(parents=True, exist_ok=True)
    observed.write_bytes(b"before validation")

    def mutate_input(_root: Path, *, check_runtime: bool) -> tuple[str, ...]:
        assert check_runtime is False
        observed.write_bytes(b"after validation")
        return ()

    monkeypatch.setattr(cli.release_bundle, "_browser_receipt_errors", mutate_input)
    readiness = build_status_report(tmp_path).as_dict()["publication_readiness"]
    stability = readiness["sections"][-1]
    assert stability["state"] == "error"
    assert "changed during status" in stability["findings"][0]
    assert readiness["claim_ready"] is False


def test_statically_matching_planes_still_require_runtime_and_bundle_gates() -> None:
    sections = tuple(
        cli.SectionReport(name, "current", (), ("existing.owner",), "static boundary")
        for name in (
            "catalogue_build_products",
            "render_receipt_freshness",
            "bridge_source_pin",
            "native_verification_receipt",
            "formalism_audit_receipt",
            "python_acceptance_receipt",
            "browser_acceptance_receipt",
            "publication_inputs",
            "publication_bundle",
            "input_stability",
        )
    )
    readiness = cli.PublicationReadinessReport(sections)
    assert readiness.state == "unverified"
    assert readiness.claim_ready is False
    assert (
        cli.PublicationReadinessReport(
            sections, runtime_checks_performed=True, bundle_parity_verified=True
        ).claim_ready
        is True
    )
    assert (
        cli.PublicationReadinessReport(
            sections[:-1], runtime_checks_performed=True, bundle_parity_verified=True
        ).claim_ready
        is False
    )


@pytest.mark.parametrize(
    "failed_validator,section_index",
    [("receipt_defects", 1), ("validate_native_lean_receipt", 3)],
)
def test_unavailable_receipt_comparison_keeps_report_composed_and_blocks_readiness(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failed_validator: str,
    section_index: int,
) -> None:
    native = tmp_path / cli.NATIVE_RECEIPT
    native.parent.mkdir()
    native.write_text("{}\n")

    def unreadable(*_args: object, **_kwargs: object) -> tuple[str, ...]:
        raise OSError("source bytes became unreadable")

    monkeypatch.setattr(
        (
            {"receipt_defects": render_log, "validate_native_lean_receipt": evidence}[
                failed_validator
            ]
        ),
        failed_validator,
        unreadable,
    )
    payload = build_status_report(tmp_path).as_dict()
    section = payload["sections"][section_index]
    assert payload["status"] == "ok"
    assert section["state"] == "error"
    assert "source bytes became unreadable" in section["findings"][0]
    assert payload["publication_readiness"]["claim_ready"] is False


def test_public_readiness_types_retain_cli_identity_and_projection() -> None:
    from dataclasses import FrozenInstanceError

    from fep_formal import (
        PublicationReadinessReport,
        SectionReport,
        StatusReport,
        output,
    )
    from fep_formal.output import evidence

    assert cli.SectionReport is evidence.SectionReport is SectionReport
    assert cli.PublicationReadinessReport is PublicationReadinessReport
    assert cli.StatusReport is output.StatusReport is StatusReport
    section = SectionReport("example", "current", (), (), "fixture boundary")
    report = StatusReport((section,))
    assert (
        cli.report_to_json(report)
        == '{\n  "schema_version": 1,\n  "status": "error",\n  "evidence_plane": "evidence currency and provenance",\n  "boundary": "status composes existing read-only checks; exit 0 means the report composed, never that the evidence is current. Each section\'s state and boundary are the authority. Nothing here compiles Lean, runs Hermes or OpenGauss, executes the test suite, writes bytes, or repairs drift.",\n  "native_claim_ready": false,\n  "sections": [\n    {\n      "name": "example",\n      "state": "current",\n      "findings": [],\n      "composes": [],\n      "boundary": "fixture boundary"\n    }\n  ]\n}'
    )
    with pytest.raises(FrozenInstanceError):
        report.sections = ()
    unknown = PublicationReadinessReport((section,), True, True)
    assert unknown.state == "blocked" and not unknown.claim_ready
    assert not PublicationReadinessReport(()).claim_ready


def test_public_inspection_rejects_unknown_plane_before_reading(tmp_path: Path) -> None:
    from fep_formal.output import release_bundle

    with pytest.raises(ValueError, match="unknown stored publication evidence plane"):
        release_bundle.inspect_stored_publication_evidence(
            tmp_path / "absent", "unknown"
        )
    assert not list(tmp_path.iterdir())


def test_caller_root_context_nests_and_explicitly_projects_child_environment(
    tmp_path: Path,
) -> None:
    import os

    from fep_formal._paths import (
        project_child_environment,
        project_root,
        project_root_context,
    )

    original = dict(os.environ)
    base = {"FEP_FORMAL_PROJECT_ROOT": "caller-base", "SENTINEL": "unchanged"}
    before = dict(base)
    with project_root_context(tmp_path / "one"):
        assert project_root() == (tmp_path / "one").resolve()
        assert project_child_environment(base)["FEP_FORMAL_PROJECT_ROOT"] == str(
            project_root()
        )
        with project_root_context(tmp_path / "two"):
            assert project_root() == (tmp_path / "two").resolve()
        assert project_root() == (tmp_path / "one").resolve()
    assert base == before
    assert project_child_environment(base) == base
    assert dict(os.environ) == original


def test_caller_root_context_isolated_between_contexts(tmp_path: Path) -> None:
    from contextvars import copy_context

    from fep_formal._paths import project_root, project_root_context

    outer = project_root()

    def inspect() -> Path:
        with project_root_context(tmp_path):
            return project_root()

    assert copy_context().run(inspect) == tmp_path.resolve()
    assert project_root() == outer


def test_caller_root_context_restores_after_error(tmp_path: Path) -> None:
    from fep_formal._paths import project_root, project_root_context

    previous = project_root()
    with pytest.raises(RuntimeError, match="control"), project_root_context(tmp_path):
        raise RuntimeError("control")
    assert project_root() == previous


def test_caller_roots_do_not_cross_independent_contexts(tmp_path: Path) -> None:
    from contextvars import copy_context

    from fep_formal._paths import project_root, project_root_context

    first, second = copy_context(), copy_context()
    with project_root_context(tmp_path / "outer"):

        def enter(root: Path) -> Path:
            with project_root_context(root):
                return project_root()

        assert first.run(enter, tmp_path / "first") == (tmp_path / "first").resolve()
        assert second.run(enter, tmp_path / "second") == (tmp_path / "second").resolve()
        assert project_root() == (tmp_path / "outer").resolve()


def test_public_snapshot_builder_has_one_owner_and_starts_no_tools(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import os

    from fep_formal import build_status_report as public_builder
    from fep_formal import output

    assert public_builder is output.build_status_report is evidence.build_status_report
    assert cli.build_status_report is public_builder

    def forbidden(*_args: object, **_kwargs: object) -> None:
        pytest.fail("a static readiness snapshot must not start a tool")

    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    environment = dict(os.environ)
    files = sorted(tmp_path.rglob("*"))
    report = public_builder(tmp_path)
    assert isinstance(report, evidence.StatusReport)
    assert report.publication_readiness is not None
    assert report.publication_readiness.claim_ready is False
    assert dict(os.environ) == environment
    assert sorted(tmp_path.rglob("*")) == files
