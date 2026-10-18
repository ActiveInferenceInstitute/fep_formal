"""Capture release/publication boundary contracts."""

from __future__ import annotations

import hashlib
import json
import os
import runpy
import shutil
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from fep_lean.output import release_bundle as bundle_module
from tests._support.release_bundle import (
    _capture_plan,
    _capture_stage,
    _linked_capture_stage,
    _valid_contents,
)

PROJ = Path(__file__).resolve().parents[1]


def test_publication_capture_plan_is_process_free(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from fep_lean.output.release_bundle._core import plan_publication_capture

    template = tmp_path / "template"
    renderer = template / "scripts/pipeline/stage_03_render.py"
    renderer.parent.mkdir(parents=True)
    renderer.write_text("# explicit fixture template owner\n")

    def forbid(*_args, **_kwargs):
        pytest.fail("planning launched a process")

    monkeypatch.setattr(subprocess, "Popen", forbid)
    plan = plan_publication_capture(PROJ, template_root=template)
    assert tuple(s.name for s in plan.stages) == (
        "native",
        "formalism-audit",
        "render",
        "python",
        "numerical",
        "browser",
        "bundle",
    )
    assert plan.stages[-1].outputs == (
        "{attempt}/release-a.tar.gz",
        "{attempt}/release-b.tar.gz",
    )
    assert not (tmp_path / "journal").exists()
    native, render, python = (
        next(s for s in plan.stages if s.name == name)
        for name in ("native", "render", "python")
    )
    assert render.dependencies == ("native", "formalism-audit")
    assert python.dependencies == ("render",)
    variables = str(PROJ / "manuscript/manuscript_vars.yaml")
    appendix = str(PROJ / "manuscript/09z_unified_formalism_catalogue.md")
    cache = str(PROJ / "output/.cache/tests_collected.json")
    assert {variables, appendix, cache} <= set(native.outputs)
    assert not {variables, appendix, cache} & set(native.inputs)
    assert {variables, appendix, cache} <= set(render.inputs) & set(python.inputs)
    assert not set(python.outputs) & set(render.inputs)
    assert str(PROJ / "CITATION.cff") in native.inputs
    assert str(PROJ / "manuscript/assets/graphical-abstract.png") in native.inputs
    assert str(PROJ / "docs/render-acceptance.json") in python.inputs
    assert str(PROJ / "docs/render-fonts.json") in python.inputs


@pytest.mark.parametrize(
    "missing", ["manuscript_vars.yaml", "09z_unified_formalism_catalogue.md"]
)
def test_publication_capture_missing_projection_pair_rejects_before_tools(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, missing: str
) -> None:
    from fep_lean.output.release_bundle._core import plan_publication_capture

    root = tmp_path / "project"
    manuscript = root / "manuscript"
    manuscript.mkdir(parents=True)
    for name in ("manuscript_vars.yaml", "09z_unified_formalism_catalogue.md"):
        if name != missing:
            (manuscript / name).write_text("preserve existing member\n")

    def forbid(*_args, **_kwargs):
        pytest.fail("missing projection preparation launched a process")

    monkeypatch.setattr(subprocess, "Popen", forbid)
    with pytest.raises(
        bundle_module.ReleaseBundleError, match="catalogue before planning"
    ):
        plan_publication_capture(root, template_root=tmp_path / "template")
    assert {p.name for p in manuscript.iterdir()} == {
        "manuscript_vars.yaml",
        "09z_unified_formalism_catalogue.md",
    } - {missing}


@pytest.mark.parametrize("boundary", ["exit", "invalid", "unbound", "unready", "alias"])
def test_publication_capture_native_rejection_preserves_projection_pair(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, boundary: str
) -> None:
    from fep_lean import cli
    from fep_lean.output import evidence, manuscript
    from fep_lean.output.release_bundle._core import _publication_capture_worker

    directory = tmp_path / "manuscript"
    directory.mkdir()
    originals = {
        name: b"preserved projection\n"
        for name in ("manuscript_vars.yaml", "09z_unified_formalism_catalogue.md")
    }
    for name, data in originals.items():
        (directory / name).write_bytes(data)
    validation = {"valid": True, "source_bound": True, "native_claim_ready": True}
    if boundary != "exit":
        key = {
            "invalid": "valid",
            "unbound": "source_bound",
            "unready": "native_claim_ready",
            "alias": "valid",
        }[boundary]
        validation[key] = 1 if boundary == "alias" else False
    monkeypatch.setattr(cli, "main", lambda _args: 7 if boundary == "exit" else 0)
    monkeypatch.setattr(
        evidence, "validate_native_lean_receipt", lambda *_args, **_kwargs: validation
    )

    def forbid(*_args, **_kwargs):
        pytest.fail("rejected native evidence refreshed manuscript projections")

    monkeypatch.setattr(manuscript, "write_manuscript_vars", forbid)
    assert _publication_capture_worker(
        "native", "produce", str(tmp_path), str(tmp_path), str(tmp_path), "0"
    ) == (7 if boundary == "exit" else 1)
    assert {name: (directory / name).read_bytes() for name in originals} == originals


@pytest.mark.parametrize(
    "mutation",
    ["none", "duration", "compile_rate", "appendix", "source_date", "source_shape"],
)
def test_publication_capture_projects_final_native_values_and_rejects_stale_values(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    from fep_lean import cli
    from fep_lean.catalogue.topics import FEPTopicCatalogue
    from fep_lean.output import evidence, manuscript
    from fep_lean.output.release_bundle._core import _publication_capture_worker

    (tmp_path / "manuscript").mkdir()
    (tmp_path / "output/.cache").mkdir(parents=True)
    receipt = tmp_path / "output/native-verification.json"
    receipt.write_text(json.dumps({"duration_s": 1.125}))
    monkeypatch.setattr(
        FEPTopicCatalogue,
        "from_yaml",
        lambda _path: SimpleNamespace(marker="canonical appendix\n"),
    )
    monkeypatch.setattr(
        manuscript,
        "build_unified_formalism_appendix_markdown",
        lambda cat, _root: cat.marker,
    )
    monkeypatch.setattr(
        evidence,
        "validate_native_lean_receipt",
        lambda *_args, **_kwargs: {
            "valid": True,
            "source_bound": True,
            "native_claim_ready": True,
        },
    )

    def variables(_cat, root, *, output_root=None, cache_test_count=True):
        assert root == tmp_path and output_root is None
        cache = root / "output/.cache/tests_collected.json"
        if cache_test_count:
            cache.write_text(json.dumps({"collected": 1}))
        assert json.loads(cache.read_text()) == {"collected": 1}
        return {
            "verify": {
                "duration_seconds": json.loads(receipt.read_text())["duration_s"],
                "claim_ready": True,
            },
            "compile_rate": {"total": "100%"},
            "source": {"render_date": "2026-10-02", "stamp": "captured source stamp"},
        }

    monkeypatch.setattr(manuscript, "build_manuscript_vars", variables)
    # Use the real transactional pair writer, serializer and drift validator.
    manuscript.write_manuscript_vars(tmp_path)
    old = (tmp_path / "manuscript/manuscript_vars.yaml").read_bytes()

    def final_native(_args):
        receipt.write_text(json.dumps({"duration_s": 17.875}))
        return 0

    monkeypatch.setattr(cli, "main", final_native)
    assert (
        _publication_capture_worker(
            "native", "produce", str(tmp_path), str(tmp_path), str(tmp_path), "0"
        )
        == 0
    )
    projection = tmp_path / "manuscript/manuscript_vars.yaml"
    current = yaml.safe_load(projection.read_text())
    assert current["verify"]["duration_seconds"] == 17.875
    assert projection.read_bytes() != old
    if mutation == "duration":
        current["verify"]["duration_seconds"] = 1.125
    elif mutation == "compile_rate":
        current["compile_rate"]["total"] = "0%"
    elif mutation == "appendix":
        (tmp_path / "manuscript/09z_unified_formalism_catalogue.md").write_text(
            "stale appendix\n"
        )
    elif mutation == "source_date":
        # A later check may run after UTC midnight; native values stay fixed.
        current["source"]["render_date"] = "2026-10-01"
        current["source"]["stamp"] = "previous captured source stamp"
    elif mutation == "source_shape":
        current["source"]["render_date"] = 20261002
    if mutation in {"duration", "compile_rate", "source_date", "source_shape"}:
        projection.write_text(manuscript._dump_manuscript_vars(current))
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    assert _publication_capture_worker(
        "native", "check", str(tmp_path), str(tmp_path), str(tmp_path), "0"
    ) == (0 if mutation in {"none", "source_date"} else 1)
    assert {p: p.read_bytes() for p in before} == before


def test_publication_capture_projection_failure_is_fatal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from fep_lean import cli
    from fep_lean.output import evidence, manuscript
    from fep_lean.output.release_bundle._core import _publication_capture_worker

    monkeypatch.setattr(cli, "main", lambda _args: 0)
    monkeypatch.setattr(
        evidence,
        "validate_native_lean_receipt",
        lambda *_args, **_kwargs: {
            "valid": True,
            "source_bound": True,
            "native_claim_ready": True,
        },
    )

    def reject(*_args, **_kwargs):
        raise OSError("projection transaction failed")

    monkeypatch.setattr(manuscript, "write_manuscript_vars", reject)
    with pytest.raises(OSError, match="projection transaction failed"):
        _publication_capture_worker(
            "native", "produce", str(tmp_path), str(tmp_path), str(tmp_path), "0"
        )


def test_publication_capture_reuses_unchanged_stages_and_invalidates_descendants(
    tmp_path: Path,
) -> None:
    from fep_lean.output.release_bundle._core import run_publication_capture

    root = tmp_path / "project"
    root.mkdir()
    a, b, child = (
        _capture_stage(root, "a"),
        _capture_stage(root, "b"),
        _capture_stage(root, "child", ("a",)),
    )
    plan = _capture_plan(root, (a, b, child))
    journal = tmp_path / "journal"
    assert run_publication_capture(plan, journal).complete
    original = {p: p.read_bytes() for p in journal.rglob("*") if p.is_file()}
    resumed = run_publication_capture(plan, journal, resume=True)
    assert resumed.complete and resumed.reused_stages == ("a", "b", "child")
    assert all(p.read_bytes() == data for p, data in original.items())
    # Repeated resume retains the original producer artifact origin.
    assert run_publication_capture(plan, journal, resume=True).reused_stages == (
        "a",
        "b",
        "child",
    )
    (root / "a.input").write_bytes(b"new source")
    changed = run_publication_capture(plan, journal, resume=True)
    assert changed.complete and changed.reused_stages == ("b",)
    records = [
        json.loads(p.read_text())
        for p in sorted(journal.glob("attempts/*/result.json"))
    ][-3:]
    assert [r["mode"] for r in records] == ["capture", "reuse", "capture"]
    assert (root / "a.output").read_bytes() == b"new source"


def test_publication_capture_failed_stage_resume_preserves_partial_and_prior_bytes(
    tmp_path: Path,
) -> None:
    from fep_lean.output.release_bundle._core import run_publication_capture

    root = tmp_path / "project"
    root.mkdir()
    a, b = _capture_stage(root, "a"), _capture_stage(root, "b")
    (root / "b.output").write_bytes(b"prior accepted bytes")
    (root / "b.input").write_bytes(b"reject")
    plan, journal = _capture_plan(root, (a, b)), tmp_path / "journal"
    rejected = run_publication_capture(plan, journal)
    assert not rejected.complete and rejected.failed_stage == "b"
    attempt = journal / "attempts/000002-b"
    assert (attempt / "prior/0000.bin").read_bytes() == b"prior accepted bytes"
    assert (attempt / "artifacts/0000.bin").read_bytes() == b"reject"
    retained = {p: p.read_bytes() for p in attempt.rglob("*") if p.is_file()}
    (root / "b.input").write_bytes(b"repaired independent input")
    recovered = run_publication_capture(plan, journal, resume=True)
    assert recovered.complete and recovered.reused_stages == ("a",)
    assert all(p.read_bytes() == data for p, data in retained.items())


@pytest.mark.parametrize(
    "tamper", ["policy", "artifact", "stream", "acceptance", "extra", "symlink"]
)
def test_publication_capture_rejects_tampered_history_before_process(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, tamper: str
) -> None:
    from fep_lean.output.release_bundle._core import run_publication_capture

    root = tmp_path / "project"
    root.mkdir()
    plan, journal = (
        _capture_plan(root, (_capture_stage(root, "a"),)),
        tmp_path / "journal",
    )
    assert run_publication_capture(plan, journal).complete
    attempt = journal / "attempts/000001-a"
    target = {
        "policy": journal / "journal.json",
        "artifact": attempt / "artifacts/0000.bin",
        "stream": attempt / "stdout.log",
        "acceptance": attempt / "result.json",
        "extra": attempt / "unexpected",
        "symlink": attempt / "artifacts/0000.bin",
    }[tamper]
    if tamper == "symlink":
        target.unlink()
        target.symlink_to(root / "a.output")
    elif tamper == "acceptance":
        payload = json.loads(target.read_text())
        payload["check_returncode"] = True
        target.chmod(0o644)
        target.write_text(json.dumps(payload))
    else:
        if target.exists():
            target.chmod(0o644)
        target.write_bytes(b"tampered")

    def forbid(*_args, **_kwargs):
        pytest.fail("tampered history launched a process")

    monkeypatch.setattr(subprocess, "Popen", forbid)
    with pytest.raises(bundle_module.ReleaseBundleError):
        run_publication_capture(plan, journal, resume=True)


def test_publication_capture_rejects_source_mutation_and_missing_artifacts(
    tmp_path: Path,
) -> None:
    from dataclasses import replace

    from fep_lean.output.release_bundle._core import run_publication_capture

    root = tmp_path / "project"
    root.mkdir()
    stage = _capture_stage(root, "a")
    code = "from pathlib import Path;import sys;Path(sys.argv[1]).write_bytes(b'mutated');Path(sys.argv[2]).write_bytes(b'mutated')"
    stage = replace(
        stage, command=(sys.executable, "-c", code, stage.inputs[0], stage.outputs[0])
    )
    rejected = run_publication_capture(
        _capture_plan(root, (stage,)), tmp_path / "mutation"
    )
    assert not rejected.complete and any("inputs changed" in e for e in rejected.errors)
    (root / "a.output").unlink()
    stage = replace(
        stage,
        command=(sys.executable, "-c", "pass"),
        check_command=(sys.executable, "-c", "pass"),
    )
    missing = run_publication_capture(
        _capture_plan(root, (stage,)), tmp_path / "missing"
    )
    assert not missing.complete and any("missing" in e for e in missing.errors)


def test_publication_capture_owns_only_its_external_journal_and_declared_outputs(
    tmp_path: Path,
) -> None:
    from dataclasses import replace

    from fep_lean.output.release_bundle._core import run_publication_capture

    root = tmp_path / "project"
    root.mkdir()
    stage = _capture_stage(root, "a")
    with pytest.raises(bundle_module.ReleaseBundleError, match="outside"):
        run_publication_capture(_capture_plan(root, (stage,)), root / "journal")
    outside = tmp_path / "outside"
    outside.write_bytes(b"keep")
    linked = root / "link.output"
    linked.symlink_to(outside)
    stage = replace(stage, outputs=(str(linked),))
    with pytest.raises(bundle_module.ReleaseBundleError, match="canonical"):
        run_publication_capture(_capture_plan(root, (stage,)), tmp_path / "journal")
    assert outside.read_bytes() == b"keep"


def test_publication_capture_two_archive_worker_requires_independent_strict_acceptance_and_parity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from fep_lean.output.release_bundle._core import _publication_capture_worker

    archives = [tmp_path / name for name in ("release-a.tar.gz", "release-b.tar.gz")]
    for archive in archives:
        bundle_module._write_archive(archive, _valid_contents({}), epoch=0)
    calls = []

    def accepted(path, *, project_root):
        calls.append(path)
        return SimpleNamespace(errors=(), claim_ready=True)

    monkeypatch.setattr(bundle_module, "validate_release_bundle", accepted)
    assert (
        _publication_capture_worker(
            "bundle", "check", str(tmp_path), str(tmp_path), str(tmp_path), "0"
        )
        == 0
    )
    assert calls == archives
    archives[1].write_bytes(archives[1].read_bytes() + b"divergence")
    assert (
        _publication_capture_worker(
            "bundle", "check", str(tmp_path), str(tmp_path), str(tmp_path), "0"
        )
        == 1
    )
    monkeypatch.setattr(
        bundle_module,
        "validate_release_bundle",
        lambda *_args, **_kwargs: SimpleNamespace(
            errors=("strict owner rejected",), claim_ready=False
        ),
    )
    assert (
        _publication_capture_worker(
            "bundle", "check", str(tmp_path), str(tmp_path), str(tmp_path), "0"
        )
        == 1
    )


def test_publication_capture_runs_real_numerical_owner_in_disposable_project(
    tmp_path: Path,
) -> None:
    from fep_lean.output.release_bundle._core import (
        _PUBLICATION_CAPTURE_WORKER,
        PublicationCaptureStage,
        run_publication_capture,
    )

    root = tmp_path / "project"
    root.mkdir()
    for name in ("src", "config"):
        shutil.copytree(
            PROJ / name,
            root / name,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
    inputs = tuple(str(p) for p in sorted(root.rglob("*")) if p.is_file())
    command = (sys.executable, "-c", _PUBLICATION_CAPTURE_WORKER, "numerical")
    stage = PublicationCaptureStage(
        "numerical",
        (),
        inputs,
        (str(root / "output/numerical-witnesses.json"),),
        (*command, "produce", str(root), "{attempt}", str(root), "0"),
        (*command, "check", str(root), "{artifact_attempt}", str(root), "0"),
        # Functional budget only: a cold numerical owner can exceed 30 s under
        # xdist load. Deadline reaping is covered by the dedicated test below.
        180,
    )
    result = run_publication_capture(
        _capture_plan(root, (stage,)), tmp_path / "journal"
    )
    assert result.complete
    receipt = json.loads((root / "output/numerical-witnesses.json").read_text())
    assert (
        receipt["complete"] is True
        and receipt["evidence_kind"]
        == "deterministic_numerical_witness_non_proof_evidence"
    )
    assert run_publication_capture(
        _capture_plan(root, (stage,)), tmp_path / "journal", resume=True
    ).reused_stages == ("numerical",)


@pytest.mark.skipif(os.name != "posix", reason="POSIX process-group capture contract")
def test_publication_capture_deadline_reaps_real_child_and_grandchild(
    tmp_path: Path,
) -> None:
    from dataclasses import replace

    from fep_lean.output.release_bundle._core import run_publication_capture

    root = tmp_path / "project"
    root.mkdir()
    stage = _capture_stage(root, "a")
    pidfile = root / "processes.json"
    code = (
        "import os,subprocess,sys,time,json;from pathlib import Path;"
        "child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(120)']);"
        "Path(sys.argv[1]).write_text(json.dumps([os.getpid(),child.pid]));"
        "print('capture started',flush=True);time.sleep(120)"
    )
    stage = replace(
        stage,
        command=(sys.executable, "-c", code, str(pidfile)),
        outputs=(str(pidfile),),
        timeout_s=1,
    )
    started = time.monotonic()
    outcome = run_publication_capture(
        _capture_plan(root, (stage,)), tmp_path / "journal"
    )
    assert time.monotonic() - started < 4
    assert not outcome.complete and "deadline" in outcome.errors[0]
    for pid in json.loads(pidfile.read_text()):
        state = subprocess.run(
            ["ps", "-o", "stat=", "-p", str(pid)],
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()
        assert not state or state.startswith("Z"), (
            f"owned descendant still running: {pid} {state}"
        )
    attempt = tmp_path / "journal/attempts/000001-a"
    assert "capture started" in (attempt / "stdout.log").read_text()
    assert json.loads((attempt / "result.json").read_text())["timed_out"] is True


def test_publication_capture_cli_plan_is_additive_and_process_free(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from fep_lean.cli import main

    template = tmp_path / "template"
    renderer = template / "scripts/pipeline/stage_03_render.py"
    renderer.parent.mkdir(parents=True)
    renderer.write_text("# planning-only fixture\n")

    def forbid(*_args, **_kwargs):
        pytest.fail("CLI planning launched a process")

    monkeypatch.setattr(subprocess, "Popen", forbid)
    assert (
        main(
            [
                "--project-root",
                str(PROJ),
                "publication-capture",
                "--template",
                str(template),
                "--plan",
            ]
        )
        == 0
    )
    policy = json.loads(capsys.readouterr().out)
    assert policy["kind"] == "strict-local-publication-capture"
    assert policy["stages"][-1]["name"] == "bundle"


@pytest.mark.parametrize(
    "arguments",
    [
        ["--plan-capture", "--check"],
        ["--plan-capture", "--run-python-acceptance"],
        ["--plan-capture", "--write-numerical-witnesses"],
        ["--plan-capture", "--capture-journal", "/unused"],
        ["--plan-capture", "--resume"],
        ["--capture-journal", "/unused", "--output", "/unused.tar.gz"],
        ["--resume"],
    ],
)
def test_publication_capture_wrapper_rejects_ambiguous_actions_without_execution(
    arguments: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    namespace = runpy.run_path(str(PROJ / "scripts/build_release_bundle.py"))

    def forbid(*_args, **_kwargs):
        pytest.fail("invalid capture arguments launched a process")

    monkeypatch.setattr(subprocess, "Popen", forbid)
    with pytest.raises(SystemExit) as rejected:
        namespace["main"](arguments)
    assert rejected.value.code == 2


def test_publication_capture_template_seals_all_resource_types(
    tmp_path: Path,
) -> None:
    from fep_lean.output.release_bundle._core import plan_publication_capture

    template = tmp_path / "template"
    renderer = template / "scripts/pipeline/stage_03_render.py"
    renderer.parent.mkdir(parents=True)
    renderer.write_text("# explicit fixture\n")
    for name in (
        "theme.sty",
        "article.cls",
        "refs.bib",
        "page.css",
        "page.js",
        "logo.png",
        "scripts.py",
        "config-wizard.md",
    ):
        (template / name).write_bytes(b"retained resource")
    nested = template / "config/README.md"
    nested.parent.mkdir()
    nested.write_bytes(b"retained nested resource")
    cache = template / ".venv/ignored-resource.sty"
    cache.parent.mkdir()
    cache.write_bytes(b"excluded environment")
    plan = plan_publication_capture(PROJ, template_root=template)
    for stage_name in ("render", "bundle"):
        stage = next(s for s in plan.stages if s.name == stage_name)
        expected = tuple(
            sorted(str(p) for p in template.rglob("*") if p.is_file() and p != cache)
        )
        assert (str(template), expected) in stage.input_rosters
        assert set(expected) <= set(stage.inputs)
        assert str(cache) not in stage.inputs


@pytest.mark.skipif(os.name != "posix", reason="POSIX descriptor link ownership")
def test_publication_capture_declared_internal_link_and_resume(tmp_path: Path) -> None:
    from fep_lean.output.release_bundle._core import run_publication_capture

    root, _owner, leaf, alias, stage = _linked_capture_stage(tmp_path)
    plan = _capture_plan(root, (stage,))
    journal = tmp_path / "journal"
    outcome = run_publication_capture(plan, journal)
    assert outcome.complete
    policy = json.loads((journal / "journal.json").read_text())["policy"]
    assert policy["stages"][0]["resource_links"] == [
        {"path": str(alias), "target": "../canonical/style.txt"}
    ]
    assert alias.read_bytes() == leaf.read_bytes() == b"owned style"
    assert run_publication_capture(plan, journal, resume=True).reused_stages == ("a",)


@pytest.mark.skipif(os.name != "posix", reason="POSIX descriptor link ownership")
def test_publication_capture_real_template_registration_is_process_free(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from fep_lean.output.release_bundle._core import plan_publication_capture

    template = tmp_path / "template"
    entry = template / "scripts/pipeline/stage_03_render.py"
    entry.parent.mkdir(parents=True)
    entry.write_text("# fixed fixture pipeline\n")
    target = template / "styles/base.sty"
    target.parent.mkdir()
    target.write_text("owned resource\n")
    alias = template / "alias.sty"
    alias.symlink_to("styles/base.sty")
    same_stem = template / "scripts.py"
    same_stem.symlink_to("styles/base.sty")
    nested_alias = template / "scripts/alias.sty"
    nested_alias.symlink_to("../styles/base.sty")
    registration = template / "projects/active/fep_lean"
    registration.parent.mkdir(parents=True)
    registration.symlink_to(PROJ, target_is_directory=True)
    monkeypatch.setattr(
        subprocess,
        "Popen",
        lambda *_args, **_kwargs: pytest.fail("planning launched a process"),
    )
    plan = plan_publication_capture(PROJ, template_root=template)
    expected = tuple(
        sorted(
            (
                (str(alias), "styles/base.sty"),
                (str(same_stem), "styles/base.sty"),
                (str(nested_alias), "../styles/base.sty"),
                (str(registration), str(PROJ)),
            )
        )
    )
    for stage in plan.stages:
        if stage.name in {"render", "bundle"}:
            assert stage.resource_links == expected
            assert {str(entry), str(target), str(alias), str(registration)} <= set(
                stage.inputs
            )
        else:
            assert stage.resource_links == ()


@pytest.mark.skipif(os.name != "posix", reason="POSIX descriptor link ownership")
@pytest.mark.parametrize(
    "case",
    [
        "external",
        "external-chain",
        "broken",
        "cyclic",
        "unsealed",
        "wrong-owner",
        "duplicate",
        "output",
        "wrong-registration",
        "excluded-target",
        "excluded-case-target",
        "excluded-bytecode-target",
    ],
)
def test_publication_capture_link_policy_rejects_forged_custom_plans(
    tmp_path: Path, case: str
) -> None:
    from dataclasses import replace

    from fep_lean.output.release_bundle._core import run_publication_capture

    root, owner, leaf, alias, stage = _linked_capture_stage(tmp_path)
    raw = "../canonical/style.txt"
    if case in {"external", "external-chain", "broken", "cyclic", "wrong-registration"}:
        alias.unlink()
        if case == "external":
            outside = tmp_path / "private.txt"
            outside.write_bytes(b"outside")
            raw = str(outside)
        elif case == "external-chain":
            outside = tmp_path / "outside"
            outside.mkdir()
            (outside / "back").symlink_to(leaf.parent, target_is_directory=True)
            raw = str(outside / "back/style.txt")
        elif case == "broken":
            raw = "../canonical/missing.txt"
        elif case == "cyclic":
            raw = "style.txt"
        else:
            wrong = tmp_path / "other-project"
            wrong.mkdir()
            registration = owner / "projects/active/fep_lean"
            registration.parent.mkdir(parents=True)
            alias = registration
            raw = str(wrong)
            files = tuple(sorted((str(leaf), str(alias))))
            stage = replace(
                stage,
                inputs=tuple(sorted((*stage.inputs[:1], *files))),
                input_rosters=((str(owner), files),),
            )
        alias.symlink_to(raw)
        stage = replace(stage, resource_links=((str(alias), raw),))
    elif case in {
        "excluded-target",
        "excluded-case-target",
        "excluded-bytecode-target",
    }:
        alias.unlink()
        leaf.unlink()
        cached = (
            owner / "canonical/bytecode.PYC"
            if case == "excluded-bytecode-target"
            else owner / ".venv/styles/base.sty"
        )
        cached.parent.mkdir(parents=True, exist_ok=True)
        cached.write_bytes(b"excluded resource")
        raw = {
            "excluded-target": "../.venv/styles",
            "excluded-case-target": "../.VeNv/styles",
            "excluded-bytecode-target": "../canonical/bytecode.PYC",
        }[case]
        alias.symlink_to(raw, target_is_directory=True)
        stage = replace(
            stage,
            inputs=tuple(sorted((str(root / "a.input"), str(alias), str(cached)))),
            input_rosters=((str(owner), (str(alias),)),),
            resource_links=((str(alias), raw),),
        )
    elif case == "unsealed":
        files = (str(alias),)
        stage = replace(
            stage,
            inputs=(str(root / "a.input"), str(alias)),
            input_rosters=((str(owner), files),),
        )
    elif case == "duplicate":
        stage = replace(stage, resource_links=stage.resource_links * 2)
    elif case == "wrong-owner":
        stage = replace(stage, input_rosters=((str(root), (str(alias),)),))
    elif case == "output":
        stage = replace(stage, outputs=(str(alias),))
    with pytest.raises(bundle_module.ReleaseBundleError):
        run_publication_capture(_capture_plan(root, (stage,)), tmp_path / "journal")
    assert not (tmp_path / "journal").exists()


@pytest.mark.skipif(os.name != "posix", reason="POSIX descriptor link ownership")
@pytest.mark.parametrize(
    "case",
    [
        "cancelled-missing",
        "cancelled-file",
        "owner-escape-reentry",
        "empty-component",
        "dot-component",
        "trailing-separator",
        "absolute-empty-component",
    ],
)
def test_publication_capture_link_rejects_ambiguous_raw_target_spelling(
    tmp_path: Path, case: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    from dataclasses import replace

    from fep_lean.output.release_bundle._core import run_publication_capture

    root, owner, leaf, alias, stage = _linked_capture_stage(tmp_path)
    raw = {
        "cancelled-missing": "../canonical/missing/../style.txt",
        "cancelled-file": "../canonical/style.txt/../style.txt",
        "owner-escape-reentry": f"../../{owner.name}/canonical/style.txt",
        "empty-component": "../canonical//style.txt",
        "dot-component": "../canonical/./style.txt",
        "trailing-separator": "../canonical/style.txt/",
        "absolute-empty-component": f"{leaf.parent}//{leaf.name}",
    }[case]
    alias.unlink()
    alias.symlink_to(raw)
    stage = replace(stage, resource_links=((str(alias), raw),))
    monkeypatch.setattr(
        subprocess,
        "Popen",
        lambda *_args, **_kwargs: pytest.fail("invalid link launched a producer"),
    )
    with pytest.raises(bundle_module.ReleaseBundleError, match="spelling is invalid"):
        run_publication_capture(_capture_plan(root, (stage,)), tmp_path / "journal")
    assert not (tmp_path / "journal").exists()


@pytest.mark.skipif(os.name != "posix", reason="POSIX descriptor link ownership")
def test_publication_capture_rejects_byte_identical_referent_replacement(
    tmp_path: Path,
) -> None:
    from dataclasses import replace

    from fep_lean.output.release_bundle._core import run_publication_capture

    root, _owner, leaf, alias, stage = _linked_capture_stage(tmp_path)
    original_link = alias.lstat()
    original_leaf = leaf.stat()
    code = (
        "from pathlib import Path;import sys;"
        "leaf=Path(sys.argv[1]);output=Path(sys.argv[2]);"
        "replacement=leaf.with_name('replacement.txt');"
        "replacement.write_bytes(leaf.read_bytes());replacement.replace(leaf);"
        "output.write_bytes(b'a')"
    )
    stage = replace(
        stage, command=(sys.executable, "-c", code, str(leaf), str(root / "a.output"))
    )
    outcome = run_publication_capture(
        _capture_plan(root, (stage,)), tmp_path / "journal"
    )
    assert not outcome.complete
    assert alias.lstat() == original_link
    assert leaf.stat().st_ino != original_leaf.st_ino
    assert alias.read_bytes() == leaf.read_bytes() == b"owned style"
    record = json.loads(
        (tmp_path / "journal/attempts/000001-a/result.json").read_text()
    )
    assert record["inputs_before"][str(leaf)] == record["inputs_after"][str(leaf)]
    assert record["inputs_before"][str(alias)] != record["inputs_after"][str(alias)]
    assert any("changed" in error for error in outcome.errors)


@pytest.mark.skipif(os.name != "posix", reason="POSIX descriptor link ownership")
@pytest.mark.parametrize("mutation", ["link", "ancestor"])
def test_publication_capture_rejects_restored_link_or_owned_ancestor(
    tmp_path: Path, mutation: str
) -> None:
    from dataclasses import replace

    from fep_lean.output.release_bundle._core import run_publication_capture

    root, _owner, leaf, alias, stage = _linked_capture_stage(tmp_path)
    original = alias.lstat()
    code = (
        "from pathlib import Path;import os,sys,time;"
        "alias=Path(sys.argv[1]);output=Path(sys.argv[2]);"
    )
    if mutation == "link":
        code += (
            "saved=alias.parent/'saved';alias.rename(saved);"
            "alias.symlink_to('../canonical/style.txt');assert alias.read_bytes()==b'owned style';"
            "alias.unlink();saved.rename(alias);"
        )
    else:
        code += (
            "parent=alias.parent;saved=parent.with_name('saved');parent.rename(saved);"
            "parent.mkdir();(parent/'style.txt').symlink_to('../canonical/style.txt');"
            "assert (parent/'style.txt').read_bytes()==b'owned style';"
            "(parent/'style.txt').unlink();parent.rmdir();saved.rename(parent);"
        )
    code += "output.write_bytes(b'a')"
    stage = replace(
        stage, command=(sys.executable, "-c", code, str(alias), str(root / "a.output"))
    )
    outcome = run_publication_capture(
        _capture_plan(root, (stage,)), tmp_path / "journal"
    )
    assert not outcome.complete
    assert (
        alias.lstat().st_ino == original.st_ino
        and alias.read_bytes() == leaf.read_bytes()
    )
    record = json.loads(
        (tmp_path / "journal/attempts/000001-a/result.json").read_text()
    )
    assert (
        record["accepted"] is False
        and record["inputs_before"] != record["inputs_after"]
    )
    assert any("changed" in error for error in outcome.errors)


@pytest.mark.skipif(os.name != "posix", reason="POSIX descriptor link ownership")
def test_publication_capture_existing_cache_contents_preserve_link_snapshot(
    tmp_path: Path,
) -> None:
    from fep_lean.output.release_bundle._core import _capture_stage_snapshot

    _root, owner, _leaf, _alias, stage = _linked_capture_stage(tmp_path)
    cache = owner / ".venv/data"
    cache.parent.mkdir()
    cache.write_bytes(b"before")
    before = _capture_stage_snapshot(stage)
    cache.write_bytes(b"after")
    assert _capture_stage_snapshot(stage) == before


def test_publication_capture_resource_edits_invalidate_and_added_membership_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from dataclasses import replace

    from fep_lean.output.release_bundle._core import run_publication_capture

    root = tmp_path / "project"
    root.mkdir()
    stage = _capture_stage(root, "a")
    resources = root / "resources"
    resources.mkdir()
    style = resources / "theme.sty"
    style.write_text("original style")
    stage = replace(
        stage,
        inputs=(*stage.inputs, str(style)),
        input_rosters=((str(resources), (str(style),)),),
    )
    plan = _capture_plan(root, (stage,))
    journal = tmp_path / "journal"
    assert run_publication_capture(plan, journal).complete
    style.write_text("changed style")
    result = run_publication_capture(plan, journal, resume=True)
    assert result.complete and result.reused_stages == ()
    (resources / "new.bib").write_text("new bibliography")

    def forbid(*_args, **_kwargs):
        pytest.fail("expanded frozen roster launched a process")

    monkeypatch.setattr(subprocess, "Popen", forbid)
    with pytest.raises(bundle_module.ReleaseBundleError, match="membership changed"):
        run_publication_capture(plan, journal, resume=True)


def test_publication_capture_rejects_membership_expansion_during_producer(
    tmp_path: Path,
) -> None:
    from dataclasses import replace

    from fep_lean.output.release_bundle._core import run_publication_capture

    root = tmp_path / "project"
    root.mkdir()
    stage = _capture_stage(root, "a")
    resources = root / "resources"
    resources.mkdir()
    stage = replace(
        stage,
        input_rosters=((str(resources), ()),),
        command=(
            sys.executable,
            "-c",
            (
                "from pathlib import Path;import sys;"
                "Path(sys.argv[1]).write_bytes(Path(sys.argv[2]).read_bytes());"
                "Path(sys.argv[3]).write_text('newly consumed chapter')"
            ),
            stage.outputs[0],
            stage.inputs[0],
            str(resources / "new.md"),
        ),
    )
    result = run_publication_capture(
        _capture_plan(root, (stage,)), tmp_path / "journal"
    )
    assert not result.complete
    assert "capture input directory membership changed" in result.errors
    record = json.loads(
        (tmp_path / "journal/attempts/000001-a/result.json").read_text()
    )
    assert record["accepted"] is False and record["outputs"]


def test_publication_capture_failed_reuse_and_recapture_share_one_stage_budget(
    tmp_path: Path,
) -> None:
    from dataclasses import replace

    from fep_lean.output.release_bundle._core import run_publication_capture

    root = tmp_path / "project"
    root.mkdir()
    stage = _capture_stage(root, "a")
    stage = replace(
        stage,
        timeout_s=1.2,
        command=(
            sys.executable,
            "-c",
            (
                "from pathlib import Path;import sys,time;"
                "time.sleep(.8 if Path(sys.argv[3]).name.startswith('000003-') else 0);"
                "Path(sys.argv[2]).write_bytes(Path(sys.argv[1]).read_bytes())"
            ),
            stage.inputs[0],
            stage.outputs[0],
            "{attempt}",
        ),
        check_command=(
            sys.executable,
            "-c",
            (
                "from pathlib import Path;import sys,time;"
                "reuse=Path(sys.argv[1]).name.startswith('000002-');"
                "time.sleep(.8 if reuse else 0);raise SystemExit(2 if reuse else 0)"
            ),
            "{attempt}",
        ),
    )
    plan = _capture_plan(root, (stage,))
    journal = tmp_path / "journal"
    assert run_publication_capture(plan, journal).complete
    started = time.monotonic()
    rejected = run_publication_capture(plan, journal, resume=True)
    elapsed = time.monotonic() - started
    assert not rejected.complete and rejected.failed_stage == "a"
    assert elapsed < 1.55, "recapture reset the stage's finite budget"
    retained = [
        json.loads(p.read_text())
        for p in sorted(journal.glob("attempts/*/result.json"))
    ]
    assert retained[-2]["mode"] == "reuse" and not retained[-2]["accepted"]
    assert retained[-1]["mode"] == "capture" and retained[-1]["timed_out"]


def test_publication_capture_unowned_attempt_file_never_receives_acceptance(
    tmp_path: Path,
) -> None:
    from dataclasses import replace

    from fep_lean.output.release_bundle._core import run_publication_capture

    root = tmp_path / "project"
    root.mkdir()
    stage = _capture_stage(root, "a")
    stage = replace(
        stage,
        command=(
            sys.executable,
            "-c",
            (
                "from pathlib import Path;import sys;"
                "Path(sys.argv[2]).write_bytes(Path(sys.argv[1]).read_bytes());"
                "(Path(sys.argv[3])/'undeclared.txt').write_text('unowned')"
            ),
            stage.inputs[0],
            stage.outputs[0],
            "{attempt}",
        ),
    )
    result = run_publication_capture(
        _capture_plan(root, (stage,)), tmp_path / "journal"
    )
    assert not result.complete
    assert "capture attempt has unexpected files or symlinks" in result.errors


def test_publication_capture_reuse_check_mutation_cannot_rewrite_accepted_history(
    tmp_path: Path,
) -> None:
    from dataclasses import replace

    from fep_lean.output.release_bundle._core import run_publication_capture

    root = tmp_path / "project"
    root.mkdir()
    stage = _capture_stage(root, "a")
    stage = replace(
        stage,
        check_command=(
            sys.executable,
            "-c",
            (
                "from pathlib import Path;import sys;"
                "output=Path(sys.argv[2]);"
                "output.write_bytes(b'mutated') if Path(sys.argv[1]).name.startswith('000002-') else None"
            ),
            "{attempt}",
            stage.outputs[0],
        ),
    )
    plan = _capture_plan(root, (stage,))
    journal = tmp_path / "journal"
    assert run_publication_capture(plan, journal).complete
    prior = (journal / "attempts/000001-a/artifacts/0000.bin").read_bytes()
    recaptured = run_publication_capture(plan, journal, resume=True)
    assert recaptured.complete and recaptured.reused_stages == ()
    record = json.loads((journal / "attempts/000002-a/result.json").read_text())
    assert record["accepted"] is False
    assert (
        "capture reuse check changed previously accepted artifacts" in record["errors"]
    )
    assert (journal / "attempts/000001-a/artifacts/0000.bin").read_bytes() == prior
    assert Path(stage.outputs[0]).read_bytes() == prior


def test_publication_capture_timeout_journal_preserves_raw_partial_streams(
    tmp_path: Path,
) -> None:
    from dataclasses import replace

    from fep_lean.output.release_bundle._core import run_publication_capture

    root = tmp_path / "project"
    root.mkdir()
    stage = _capture_stage(root, "a")
    stdout, stderr = b"raw\r\n\xe2", b"error\r\n\xff"
    stage = replace(
        stage,
        timeout_s=0.7,
        command=(
            sys.executable,
            "-c",
            f"import os,time;os.write(1,{stdout!r});os.write(2,{stderr!r});time.sleep(30)",
        ),
    )
    journal = tmp_path / "journal"
    result = run_publication_capture(_capture_plan(root, (stage,)), journal)
    assert not result.complete
    attempt = journal / "attempts/000001-a"
    assert (attempt / "stdout.log").read_bytes() == stdout
    assert (attempt / "stderr.log").read_bytes() == stderr
    record = json.loads((attempt / "result.json").read_text())
    assert record["timed_out"] is True and record["accepted"] is False
    assert record["streams"] == {
        "stdout.log": hashlib.sha256(stdout).hexdigest(),
        "stderr.log": hashlib.sha256(stderr).hexdigest(),
    }


@pytest.mark.parametrize("mutation", ["add", "remove"])
def test_publication_capture_final_snapshot_rechecks_directory_membership_after_reads(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    from dataclasses import replace

    from fep_lean.output.release_bundle import _core

    root = tmp_path / "project"
    root.mkdir()
    stage = _capture_stage(root, "a")
    resources = root / "resources"
    resources.mkdir()
    style = resources / "theme.sty"
    style.write_bytes(b"consumed style")
    stage = replace(
        stage,
        inputs=(*stage.inputs, str(style)),
        input_rosters=((str(resources), (str(style),)),),
    )
    original = _core._capture_regular_file
    reads = 0

    def race(path: Path) -> bytes:
        nonlocal reads
        data = original(path)
        if path == style:
            reads += 1
            if reads == 3:
                if mutation == "add":
                    (resources / "late-added.css").write_text("expanded roster")
                else:
                    style.unlink()
        return data

    monkeypatch.setattr(_core, "_capture_regular_file", race)
    journal = tmp_path / "journal"
    result = _core.run_publication_capture(_capture_plan(root, (stage,)), journal)
    assert reads == 3 and not result.complete
    assert "capture inputs could not be rechecked after the attempt" in result.errors
    record = json.loads((journal / "attempts/000001-a/result.json").read_text())
    assert record["accepted"] is False


def test_publication_capture_plan_owns_every_render_asset_and_generated_collection_cache(
    tmp_path: Path,
) -> None:
    from fep_lean.output.release_bundle._core import plan_publication_capture
    from fep_lean.output.rendering import MANUSCRIPT_ASSETS

    template = tmp_path / "template"
    renderer = template / "scripts/pipeline/stage_03_render.py"
    renderer.parent.mkdir(parents=True)
    renderer.write_text("# explicit template\n")
    plan = plan_publication_capture(PROJ, template_root=template)
    render = next(s for s in plan.stages if s.name == "render")
    bundle = next(s for s in plan.stages if s.name == "bundle")
    for source, destination in MANUSCRIPT_ASSETS.values():
        assert str(PROJ / source) in render.inputs
        resolved = str(PROJ / "output/manuscript" / destination)
        assert resolved in render.outputs and resolved in bundle.inputs
    for name in ("config.yaml", "preamble.md", "references.bib"):
        assert str(PROJ / "manuscript" / name) in render.inputs
        resolved = str(PROJ / "output/manuscript" / name)
        assert resolved in render.outputs and resolved in bundle.inputs
    cache = str(PROJ / "output/.cache/tests_collected.json")
    native = next(s for s in plan.stages if s.name == "native")
    assert cache in native.outputs and cache in render.inputs
    assert cache not in render.outputs
    assert cache in bundle.inputs


def test_publication_capture_real_renderer_asset_source_mutation_rejects(
    tmp_path: Path,
) -> None:
    from fep_lean.output.release_bundle._core import (
        PublicationCaptureStage,
        run_publication_capture,
    )
    from fep_lean.output.rendering import MANUSCRIPT_ASSETS

    root = tmp_path / "project"
    manuscript = root / "manuscript"
    manuscript.mkdir(parents=True)
    chapter = manuscript / "01_chapter.md"
    chapter.write_text("A disposable chapter.\n")
    origins = []
    destinations = [str(root / "output/manuscript/01_chapter.md")]
    for source, destination in MANUSCRIPT_ASSETS.values():
        origin = root / source
        origin.parent.mkdir(parents=True, exist_ok=True)
        origin.write_bytes(b"owned fixture asset")
        origins.append(str(origin))
        destinations.append(str(root / "output/manuscript" / destination))
    program = (
        "from pathlib import Path;import sys;"
        "from fep_lean.output.rendering import render_manuscript;"
        "root=Path(sys.argv[1]);render_manuscript(root/'manuscript',root/'output/manuscript',{});"
        "Path(sys.argv[2]).write_bytes(b'asset changed during render')"
    )
    stage = PublicationCaptureStage(
        "render",
        (),
        (str(chapter), *origins),
        tuple(destinations),
        (sys.executable, "-c", program, str(root), origins[-1]),
        (sys.executable, "-c", "pass"),
        # This successful producer imports the real package and renderer;
        # deadline/cleanup controls have separate, deliberately short bounds.
        30,
    )
    result = run_publication_capture(
        _capture_plan(root, (stage,)), tmp_path / "journal"
    )
    assert not result.complete
    assert "capture inputs changed during execution or validation" in result.errors


def test_publication_capture_first_run_generated_cache_is_an_output_then_consumed_input(
    tmp_path: Path,
) -> None:
    from dataclasses import replace

    from fep_lean.output.release_bundle._core import run_publication_capture

    root = tmp_path / "project"
    root.mkdir()
    render = _capture_stage(root, "render")
    bundle = _capture_stage(root, "bundle", ("render",))
    cache = root / "output/.cache/tests_collected.json"
    render = replace(
        render,
        outputs=(*render.outputs, str(cache)),
        command=(
            sys.executable,
            "-c",
            (
                "from pathlib import Path;import sys;"
                "Path(sys.argv[2]).write_bytes(Path(sys.argv[1]).read_bytes());"
                "cache=Path(sys.argv[3]);cache.parent.mkdir(parents=True,exist_ok=True);"
                "cache.write_bytes(b'generated cache fixture')"
            ),
            render.inputs[0],
            render.outputs[0],
            str(cache),
        ),
    )
    bundle = replace(bundle, inputs=(*bundle.inputs, str(cache)))
    assert not cache.exists()
    plan = _capture_plan(root, (render, bundle))
    journal = tmp_path / "journal"
    assert run_publication_capture(plan, journal).complete
    first = json.loads((journal / "attempts/000001-render/result.json").read_text())
    assert str(cache) not in first["prior_outputs"]
    assert str(cache) in first["outputs"]
    consumed = json.loads((journal / "attempts/000002-bundle/result.json").read_text())
    assert str(cache) in consumed["inputs_before"]
    assert run_publication_capture(plan, journal, resume=True).reused_stages == (
        "render",
        "bundle",
    )
    cache.write_bytes(b"changed generated cache")
    assert run_publication_capture(plan, journal, resume=True).reused_stages == ()


@pytest.mark.parametrize("swap", ["final-file", "ancestor"])
def test_publication_capture_descriptor_reads_refuse_real_symlink_swaps(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, swap: str
) -> None:
    from fep_lean.output.release_bundle import _core

    directory = tmp_path / "declared"
    directory.mkdir()
    source = directory / "source.txt"
    source.write_bytes(b"declared bytes")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "source.txt").write_bytes(b"synthetic outside")
    original_open = os.open
    swapped = False

    def race(path, flags, *args, **kwargs):
        nonlocal swapped
        if not swapped and path == (
            "source.txt" if swap == "final-file" else "declared"
        ):
            swapped = True
            if swap == "final-file":
                source.rename(directory / "retained-source.txt")
                source.symlink_to(outside / "source.txt")
            else:
                directory.rename(tmp_path / "retained-directory")
                directory.symlink_to(outside, target_is_directory=True)
        return original_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", race)
    with pytest.raises(OSError):
        _core._capture_regular_file(source)
    assert swapped
    assert (outside / "source.txt").read_bytes() == b"synthetic outside"


def test_publication_capture_descriptor_writes_refuse_ancestor_swap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from fep_lean.output.release_bundle import _core

    parent = tmp_path / "journal"
    parent.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    original_open = os.open
    swapped = False

    def race(path, flags, *args, **kwargs):
        nonlocal swapped
        if path == "journal" and not swapped:
            swapped = True
            parent.rename(tmp_path / "retained-journal")
            parent.symlink_to(outside, target_is_directory=True)
        return original_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", race)
    with pytest.raises(OSError):
        _core._capture_new_file(parent / "receipt.json", b"retained evidence")
    assert swapped and not tuple(outside.iterdir())


def test_publication_capture_descriptor_read_refuses_fifo_swap_before_blocking(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from fep_lean.output.release_bundle import _core

    source = tmp_path / "source.txt"
    source.write_bytes(b"regular source")
    original_open = os.open
    swapped = False

    def race(path, flags, *args, **kwargs):
        nonlocal swapped
        if path == "source.txt" and not swapped:
            swapped = True
            source.rename(tmp_path / "retained-source.txt")
            os.mkfifo(source)
            # Failure here avoids an unbounded test hang while still opening
            # the real swapped FIFO under the product's actual descriptor flags.
            assert flags & os.O_NONBLOCK
        return original_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", race)
    with pytest.raises(bundle_module.ReleaseBundleError, match="regular file"):
        _core._capture_regular_file(source)
    assert swapped


def test_publication_capture_unsupported_platform_refuses_before_journal_or_process(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from fep_lean.output.release_bundle import _core

    root = tmp_path / "project"
    root.mkdir()
    plan = _capture_plan(root, (_capture_stage(root, "a"),))
    monkeypatch.setattr(_core, "os", SimpleNamespace(name="nt"))

    def forbid(*_args, **_kwargs):
        pytest.fail("unsupported capture platform launched a process")

    monkeypatch.setattr(subprocess, "Popen", forbid)
    journal = tmp_path / "journal"
    with pytest.raises(bundle_module.ReleaseBundleError, match="requires POSIX"):
        _core.run_publication_capture(plan, journal)
    assert not journal.exists()
