"""The publication entry point refuses a render the template calls successful.

Regression cover for FEP-LEAN-R2. The shared template compiles with
``-interaction=nonstopmode`` and tests its log for four fatal markers, so a
``! `` error and every ``Missing character:`` note exit zero with a PDF
written. The project cannot change the template, so its entry point must not
accept the template's verdict.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from collections.abc import Sequence
from pathlib import Path

import pytest
import yaml

from fep_lean.output.render_log import manuscript_source_digest, receipt_defects

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DIRTY_LOG = """This is XeTeX, Version 3.141592653
Missing character: There is no ᶜ (U+1D9C) in font FreeMono/OT:script=latn;
! Argument of \\TU\\' has an extra }.
Output written on _combined_manuscript.pdf (346 pages).
"""

CLEAN_LOG = """This is XeTeX, Version 3.141592653
Output written on _combined_manuscript.pdf (350 pages).
"""


def _driver():
    scripts = PROJECT_ROOT / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    spec = importlib.util.spec_from_file_location(
        "render_publication", scripts / "render_publication.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _project(tmp_path: Path, log: str) -> Path:
    """A project tree holding one rendered chapter and one compiler log."""
    manuscript = tmp_path / "manuscript"
    pdf = tmp_path / "output" / "pdf"
    manuscript.mkdir(parents=True)
    pdf.mkdir(parents=True)
    (pdf / "_combined_manuscript.log").write_text(log, encoding="utf-8")
    (pdf / "_combined_manuscript.md").write_text(
        "The catalogue holds 155 topic-scoped Lean bodies across every "
        "maintained area of the formalization.\n",
        encoding="utf-8",
    )
    (manuscript / "02b_background.md").write_text(
        "The catalogue holds 155 topic-scoped Lean bodies across every "
        "maintained area of the formalization.\n",
        encoding="utf-8",
    )
    return tmp_path


def _successful_template(_command: Sequence[str], _cwd: Path) -> int:
    """The template's own verdict on every render audited so far: success."""
    return 0


def _hydrated() -> int:
    """A successful authored-source render."""
    return 0


def test_a_successful_template_render_over_a_dirty_log_is_rejected(
    tmp_path: Path,
) -> None:
    driver = _driver()
    project = _project(tmp_path, DIRTY_LOG)

    status = driver.render_publication(
        project,
        tmp_path / "template",
        runner=_successful_template,
        hydrator=_hydrated,
        skip_probe=True,
    )

    assert status == 1


def test_a_clean_render_is_accepted(tmp_path: Path) -> None:
    driver = _driver()
    project = _project(tmp_path, CLEAN_LOG)

    status = driver.render_publication(
        project,
        tmp_path / "template",
        runner=_successful_template,
        hydrator=_hydrated,
        skip_probe=True,
    )

    assert status == 0


def test_a_failed_template_render_is_never_accepted(tmp_path: Path) -> None:
    driver = _driver()
    project = _project(tmp_path, CLEAN_LOG)

    status = driver.render_publication(
        project,
        tmp_path / "template",
        runner=lambda _command, _cwd: 1,
        hydrator=_hydrated,
        skip_probe=True,
    )

    assert status == 1


def test_acceptance_runs_even_when_the_template_failed(tmp_path: Path) -> None:
    """The acceptance is the record of what was wrong, not a second opinion."""
    driver = _driver()
    project = _project(tmp_path, DIRTY_LOG)
    calls: list[str] = []

    def runner(_command: Sequence[str], _cwd: Path) -> int:
        calls.append("rendered")
        return 1

    assert (
        driver.render_publication(
            project,
            tmp_path / "template",
            runner=runner,
            hydrator=_hydrated,
            skip_probe=True,
        )
        == 1
    )
    assert calls == ["rendered"]


def test_the_render_command_is_the_documented_template_stage(tmp_path: Path) -> None:
    driver = _driver()
    project = _project(tmp_path, CLEAN_LOG)
    seen: list[Sequence[str]] = []

    def runner(command: Sequence[str], cwd: Path) -> int:
        seen.append(command)
        assert cwd == tmp_path / "template"
        return 0

    driver.render_publication(
        project,
        tmp_path / "template",
        runner=runner,
        hydrator=_hydrated,
        skip_probe=True,
    )

    assert seen == [
        [
            "uv",
            "run",
            "--frozen",
            "python",
            "scripts/pipeline/stage_03_render.py",
            "--project",
            "fep_lean",
        ]
    ]


def test_a_missing_template_names_what_it_tried(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    driver = _driver()
    monkeypatch.delenv(driver.TEMPLATE_ENVIRONMENT_VARIABLE, raising=False)
    with pytest.raises(FileNotFoundError) as error:
        driver.resolve_template(tmp_path / "absent")
    assert "stage_03_render.py" in str(error.value)
    assert str(tmp_path / "absent") in str(error.value)


def test_a_template_is_resolved_from_the_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    driver = _driver()
    stage = tmp_path / "template" / driver.RENDER_STAGE
    stage.parent.mkdir(parents=True)
    stage.write_text("", encoding="utf-8")
    monkeypatch.setenv(driver.TEMPLATE_ENVIRONMENT_VARIABLE, str(tmp_path / "template"))

    assert driver.resolve_template(None) == (tmp_path / "template").resolve()


def test_the_shared_render_lock_is_exclusive(tmp_path: Path) -> None:
    driver = _driver()
    lock = tmp_path / "render.lock"

    assert driver.acquire_lock(lock, timeout_s=0) is True
    assert driver.acquire_lock(lock, timeout_s=0) is False
    lock.rmdir()
    assert driver.acquire_lock(lock, timeout_s=0) is True


def test_sources_that_will_not_render_stop_the_publication(tmp_path: Path) -> None:
    """The template typesets output/manuscript, so unhydrated sources ship stale.

    The template renders from the project's own rendered tree when it exists
    and its hydration hook does not fire for this project, so a render run
    without a successful source render reproduces whatever was typeset last.
    """
    driver = _driver()
    project = _project(tmp_path, CLEAN_LOG)
    rendered: list[str] = []

    def runner(_command: Sequence[str], _cwd: Path) -> int:
        rendered.append("template ran")
        return 0

    status = driver.render_publication(
        project,
        tmp_path / "template",
        runner=runner,
        hydrator=lambda: 1,
        skip_probe=True,
    )

    assert status == 1
    assert rendered == []


def test_the_sources_are_hydrated_before_the_template_runs(tmp_path: Path) -> None:
    driver = _driver()
    project = _project(tmp_path, CLEAN_LOG)
    order: list[str] = []

    def runner(_command: Sequence[str], _cwd: Path) -> int:
        order.append("template")
        return 0

    def hydrator() -> int:
        order.append("hydrate")
        return 0

    driver.render_publication(
        project,
        tmp_path / "template",
        runner=runner,
        hydrator=hydrator,
        skip_probe=True,
    )

    assert order == ["hydrate", "template"]


def test_a_clean_render_writes_the_committed_receipt(tmp_path: Path) -> None:
    """A hosted runner reads this file because it cannot run the acceptance."""
    driver = _driver()
    project = _project(tmp_path, CLEAN_LOG)

    status = driver.render_publication(
        project,
        tmp_path / "template",
        runner=_successful_template,
        hydrator=_hydrated,
        skip_probe=True,
    )

    assert status == 0
    receipt = json.loads((project / driver.RECEIPT_PATH).read_text(encoding="utf-8"))
    assert receipt["accepted"] is True
    assert receipt["pages"] == 350
    assert receipt["manuscript_source_digest"] == manuscript_source_digest(
        project / "manuscript"
    )
    assert sorted(receipt["source_digests"]) == ["02b_background.md", "preamble.md"]


def test_a_rejected_render_leaves_no_receipt(tmp_path: Path) -> None:
    """A receipt is a claim of acceptance; a rejected render may not make one."""
    driver = _driver()
    project = _project(tmp_path, DIRTY_LOG)

    status = driver.render_publication(
        project,
        tmp_path / "template",
        runner=_successful_template,
        hydrator=_hydrated,
        skip_probe=True,
    )

    assert status == 1
    assert not (project / driver.RECEIPT_PATH).exists()


def test_a_rejected_render_withdraws_the_standing_receipt(tmp_path: Path) -> None:
    """A stale receipt is a live claim, and this run disproves it.

    Sources can drift out of a render without changing: a count that moves
    under ``src/`` leaves every chapter byte-identical, so the digest cannot
    catch it and the previous receipt would keep vouching for a render that no
    longer passes.
    """
    driver = _driver()
    project = _project(tmp_path, CLEAN_LOG)
    assert (
        driver.render_publication(
            project,
            tmp_path / "template",
            runner=_successful_template,
            hydrator=_hydrated,
            skip_probe=True,
        )
        == 0
    )
    receipt = project / driver.RECEIPT_PATH
    assert receipt.is_file()

    (project / "output" / "pdf" / "_combined_manuscript.log").write_text(
        DIRTY_LOG, encoding="utf-8"
    )
    status = driver.render_publication(
        project,
        tmp_path / "template",
        runner=_successful_template,
        hydrator=_hydrated,
        skip_probe=True,
    )

    assert status == 1
    assert not receipt.exists()


def test_continuous_integration_invokes_the_acceptance() -> None:
    """The audited state: a real, tested acceptance that nothing ran.

    ``grep -rn check_render_log --include="*.yml" .github/`` returned no match,
    so every defect this gate catches could reach ``main`` unopposed. This pins
    the wiring, not the wording: some step of the workflow must run the
    acceptance script.
    """
    workflow = yaml.safe_load(
        (PROJECT_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    )
    commands = [
        step.get("run", "")
        for job in workflow["jobs"].values()
        for step in job["steps"]
    ]
    assert any("scripts/check_render_log.py" in command for command in commands)


def test_the_committed_receipt_covers_the_committed_manuscript() -> None:
    """The gate's verdict on this checkout, run as a test rather than in CI."""
    assert (
        receipt_defects(
            PROJECT_ROOT / "docs" / "render-acceptance.json",
            PROJECT_ROOT / "manuscript",
        )
        == ()
    )
